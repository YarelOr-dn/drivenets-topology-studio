"""Glue layer between recipe verify-phase keys and :class:`InnerCommandRunner`.

Purpose
-------
The scenario runner already executes ``verify.show_commands`` against the
DNOS top-level CLI via the resilient :func:`shared.device_runner.run_show`
strategy. Inner-shell surfaces (vtysh, ``run start shell``, NCP shell,
xraycli, ``grep`` over trace files) need a *persistent* SSH session and
prompt-aware nesting -- the existing one-shot path cannot drive them.

This module adds **four optional verify-phase keys** to the recipe schema:

================  =====================================================
Key                Routes to
================  =====================================================
``vtysh_commands``    ``InnerCommandRunner.run_vtysh``
``ncc_shell_commands`` ``InnerCommandRunner.run_ncc_shell``
``ncp_shell_commands`` ``InnerCommandRunner.run_ncp_shell`` (list of
                       ``{"ncp_id": int, "commands": [...]}`` blocks
                       *or* a flat list -- ncp_id defaults to 0)
``xraycli``           ``InnerCommandRunner.run_xraycli`` (list of
                       ``{"ncp_id": int, "topics": [...]}`` blocks
                       *or* a flat ``[topic, ...]`` list -- ncp_id 0)
``trace_views``       ``InnerCommandRunner.run_trace_views`` (list of
                       view dicts with ``file``/``match``/...)
================  =====================================================

If a recipe declares **none** of these keys, this module is a strict
no-op -- back-compat for every existing recipe is preserved.

Recording into the observability collector
------------------------------------------
Each :class:`InnerResult` is appended to the active phase as a synthetic
command entry so the existing HTML / JSON reports surface the inner
output alongside top-level show commands. The synthetic command label is
``"[inner:<surface>] <cmd>"``; the full ``output`` field is preserved.

Verdict layer
-------------
The glue returns a single ``LayerResult`` named ``inner_commands`` that
is:

* ``PASS`` when no rejection markers were observed and no transport
  errors occurred (or when no inner blocks were declared at all).
* ``FAIL`` when any inner result has ``ok == False`` (rejection marker
  *or* transport error). The detail message names the first failing
  surface + command. Evidence is the JSON-serialized result list.

The caller appends the layer to ``ScenarioVerdict.layers`` exactly as it
already does for ``show_command_syntax``.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from .inner_command_runner import InnerCommandRunner, InnerResult
from .verdict_engine import LayerResult, VerdictStatus

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema normalization
# ---------------------------------------------------------------------------

def _has_inner_blocks(verify_phase: Optional[Dict[str, Any]]) -> bool:
    """Return True iff the verify phase declares any inner-command key."""
    if not isinstance(verify_phase, dict):
        return False
    return any(
        verify_phase.get(k)
        for k in ("vtysh_commands", "ncc_shell_commands",
                  "ncp_shell_commands", "xraycli", "trace_views")
    )


def _normalize_ncp_blocks(
    raw: Any,
    *,
    list_key: str,
) -> List[Dict[str, Any]]:
    """Normalize ``ncp_shell_commands`` / ``xraycli`` recipe shapes.

    Accepts either a flat list (``ncp_id`` defaults to 0) or a list of
    ``{"ncp_id": int, "<list_key>": [...]}``. Returns a list of
    normalized blocks: ``[{"ncp_id": int, "<list_key>": [...]}]``.
    Any other shape returns ``[]`` (caller skips).
    """
    if not raw:
        return []
    if isinstance(raw, list) and raw and isinstance(raw[0], str):
        # Flat list of strings
        return [{"ncp_id": 0, list_key: list(raw)}]
    if isinstance(raw, list):
        out: List[Dict[str, Any]] = []
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            cmds = entry.get(list_key) or entry.get("commands") or []
            if not isinstance(cmds, list) or not cmds:
                continue
            try:
                ncp_id = int(entry.get("ncp_id", 0))
            except (TypeError, ValueError):
                ncp_id = 0
            out.append({"ncp_id": ncp_id, list_key: cmds})
        return out
    return []


def _substitute_inner(
    items: List[Any],
    sub_params: Optional[Dict[str, str]],
    sub_fn: Optional[Callable[[str, Dict[str, str]], str]],
) -> List[Any]:
    """Apply ``$variable`` substitution to strings in *items*.

    Trace-view dicts get their ``match``/``file`` substituted; xraycli
    topic strings and shell commands are substituted whole. Non-string,
    non-dict entries pass through unchanged.
    """
    if not (sub_params and sub_fn):
        return items
    out: List[Any] = []
    for it in items:
        if isinstance(it, str):
            out.append(sub_fn(it, sub_params))
        elif isinstance(it, dict):
            new_d = dict(it)
            for k in ("file", "match"):
                if isinstance(new_d.get(k), str):
                    new_d[k] = sub_fn(new_d[k], sub_params)
            out.append(new_d)
        else:
            out.append(it)
    return out


# ---------------------------------------------------------------------------
# Observability recording
# ---------------------------------------------------------------------------

def _record_results(
    obs: Any,
    device: str,
    results: List[InnerResult],
) -> None:
    """Append each :class:`InnerResult` to the current observability phase.

    Uses the same shape ``run_and_record`` produces for top-level show
    commands so the HTML / JSON reports stay symmetric. We don't have a
    callable to wrap (the command already executed), so we synthesize the
    command record by calling a no-op ``run_show`` lambda that returns
    the captured output.
    """
    if obs is None or not results:
        return
    for res in results:
        # Build a label that survives report grouping. The square-bracket
        # prefix lets readers grep "[inner:" to find these.
        label = f"[inner:{res.surface}] {res.command}"
        try:
            obs.run_and_record(
                device, label,
                run_show=lambda _d, _c, _out=res.output: _out,
            )
        except Exception as exc:  # noqa: BLE001
            log.debug("obs.run_and_record failed for inner result: %s", exc)
        # Surface markers as anomalies so the timeline shows them.
        if res.markers:
            try:
                obs.record_anomaly(
                    f"inner:{res.surface} {res.command} -> markers={res.markers}"
                )
            except Exception:  # noqa: BLE001
                pass
        elif res.error:
            try:
                obs.record_anomaly(
                    f"inner:{res.surface} {res.command} -> error={res.error}"
                )
            except Exception:  # noqa: BLE001
                pass


# ---------------------------------------------------------------------------
# Verdict synthesis
# ---------------------------------------------------------------------------

def _synthesize_verdict(
    results: List[InnerResult],
    *,
    declared: bool,
) -> LayerResult:
    """Build the ``inner_commands`` LayerResult from a list of results.

    * ``declared=False`` -> SKIP (no inner blocks in recipe).
    * Any ``ok=False`` -> FAIL (rejection markers or transport error).
    * Otherwise -> PASS with a count of executed surfaces.
    """
    if not declared:
        return LayerResult(
            "inner_commands", VerdictStatus.SKIP,
            "no inner-command blocks declared",
        )
    if not results:
        return LayerResult(
            "inner_commands", VerdictStatus.SKIP,
            "inner-command blocks declared but none executed (session unavailable)",
        )
    failures = [r for r in results if not r.ok]
    if failures:
        first = failures[0]
        reason = (f"markers={first.markers}" if first.markers
                  else f"error={first.error}")
        return LayerResult(
            "inner_commands", VerdictStatus.FAIL,
            f"{len(failures)}/{len(results)} inner command(s) rejected; "
            f"first: [{first.surface}] {first.command} -> {reason}",
            evidence=json.dumps([r.to_dict() for r in failures[:5]],
                                indent=2),
        )
    surfaces = sorted({r.surface for r in results})
    return LayerResult(
        "inner_commands", VerdictStatus.PASS,
        f"{len(results)} inner command(s) ok across surfaces={surfaces}",
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def execute_inner_command_blocks(
    *,
    verify_phase: Optional[Dict[str, Any]],
    device: str,
    obs: Any,
    sub_params: Optional[Dict[str, str]] = None,
    substitute_fn: Optional[Callable[[str, Dict[str, str]], str]] = None,
    ssh_session: Optional[Any] = None,
    password: Optional[str] = None,
) -> Tuple[LayerResult, List[Dict[str, Any]]]:
    """Run all inner-command blocks declared in *verify_phase*.

    Args:
        verify_phase: The ``phases["verify"]`` dict from the recipe.
        device: Device label used for log lines + observability.
        obs: ``ObservabilityCollector`` (current phase already begun).
        sub_params: Optional mapping for ``$variable`` substitution.
        substitute_fn: ``substitute(cmd, params) -> cmd`` callable
            (matches the existing scenario_runner helper). Required iff
            ``sub_params`` is non-empty.
        ssh_session: Live :class:`scaler.dnos_session.DNOSSession`. When
            ``None`` and inner blocks are declared, a SKIP layer is
            returned with a clear reason so the scenario does not crash.
        password: Device login password (some builds re-prompt inside
            ``run start shell``). Pass-through to :class:`InnerCommandRunner`.

    Returns:
        Tuple ``(layer_result, raw_results)``:

        * ``layer_result`` -- single :class:`LayerResult` named
          ``inner_commands``, ready to append to
          ``ScenarioVerdict.layers``.
        * ``raw_results`` -- list of dicts (one per inner command), the
          same shape ``InnerResult.to_dict()`` produces. Useful for
          report aggregators that want fine-grained data.
    """
    if not _has_inner_blocks(verify_phase):
        return _synthesize_verdict([], declared=False), []

    if ssh_session is None:
        layer = LayerResult(
            "inner_commands", VerdictStatus.SKIP,
            "inner-command blocks declared but no SSH session available "
            f"for '{device}' (add to ~/SCALER/db/devices.json or export "
            "DNOS_SSH_IP/USER/PASS)",
        )
        return layer, []

    runner = InnerCommandRunner(
        ssh_session, password=password, device_label=device,
    )

    all_results: List[InnerResult] = []
    t0 = time.time()

    # vtysh -----------------------------------------------------------------
    vtysh_cmds = list(verify_phase.get("vtysh_commands") or [])
    vtysh_cmds = _substitute_inner(vtysh_cmds, sub_params, substitute_fn)
    if vtysh_cmds:
        try:
            res = runner.run_vtysh(vtysh_cmds)
        except Exception as exc:  # noqa: BLE001
            res = [InnerResult(
                surface="vtysh", command="<context>",
                ok=False, markers=[], elapsed_s=0.0,
                output="", error=f"{type(exc).__name__}: {exc}",
            )]
        all_results.extend(res)
        _record_results(obs, device, res)

    # NCC shell -------------------------------------------------------------
    ncc_cmds = list(verify_phase.get("ncc_shell_commands") or [])
    ncc_cmds = _substitute_inner(ncc_cmds, sub_params, substitute_fn)
    if ncc_cmds:
        try:
            res = runner.run_ncc_shell(ncc_cmds)
        except Exception as exc:  # noqa: BLE001
            res = [InnerResult(
                surface="ncc_shell", command="<context>",
                ok=False, markers=[], elapsed_s=0.0,
                output="", error=f"{type(exc).__name__}: {exc}",
            )]
        all_results.extend(res)
        _record_results(obs, device, res)

    # NCP shell -------------------------------------------------------------
    for block in _normalize_ncp_blocks(
        verify_phase.get("ncp_shell_commands"), list_key="commands",
    ):
        cmds = _substitute_inner(block["commands"], sub_params, substitute_fn)
        try:
            res = runner.run_ncp_shell(cmds, ncp_id=block["ncp_id"])
        except Exception as exc:  # noqa: BLE001
            res = [InnerResult(
                surface="ncp_shell",
                command=f"<context ncp={block['ncp_id']}>",
                ok=False, markers=[], elapsed_s=0.0,
                output="", error=f"{type(exc).__name__}: {exc}",
            )]
        all_results.extend(res)
        _record_results(obs, device, res)

    # xraycli ---------------------------------------------------------------
    for block in _normalize_ncp_blocks(
        verify_phase.get("xraycli"), list_key="topics",
    ):
        topics = _substitute_inner(block["topics"], sub_params, substitute_fn)
        try:
            res = runner.run_xraycli(topics, ncp_id=block["ncp_id"])
        except Exception as exc:  # noqa: BLE001
            res = [InnerResult(
                surface="xraycli",
                command=f"<context ncp={block['ncp_id']}>",
                ok=False, markers=[], elapsed_s=0.0,
                output="", error=f"{type(exc).__name__}: {exc}",
            )]
        all_results.extend(res)
        _record_results(obs, device, res)

    # trace views -----------------------------------------------------------
    views = list(verify_phase.get("trace_views") or [])
    views = _substitute_inner(views, sub_params, substitute_fn)
    if views:
        try:
            res = runner.run_trace_views(views)
        except Exception as exc:  # noqa: BLE001
            res = [InnerResult(
                surface="ncc_shell", command="<trace_views context>",
                ok=False, markers=[], elapsed_s=0.0,
                output="", error=f"{type(exc).__name__}: {exc}",
            )]
        all_results.extend(res)
        _record_results(obs, device, res)

    elapsed = time.time() - t0
    log.info(
        "inner_command_runner_glue: %s ran %d result(s) in %.2fs",
        device, len(all_results), elapsed,
    )

    layer = _synthesize_verdict(all_results, declared=True)
    return layer, [r.to_dict() for r in all_results]
