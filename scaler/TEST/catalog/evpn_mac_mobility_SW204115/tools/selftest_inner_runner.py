#!/usr/bin/env python3
"""Live self-test for the inner-command runner wiring (Step 2).

Exercises ``shared.inner_command_runner_glue.execute_inner_command_blocks``
exactly the way ``orchestration.scenario_runner`` calls it, against a real
DNOS device, with no recipe edits committed and no test config applied.

What it proves (5 cases):

  1. Healthy block -- vtysh + ncc_shell + xraycli + trace_views all execute,
     each populates obs, and the synthesized layer verdict is PASS.
  2. Bad command -- a deliberately invalid vtysh command produces a FAIL
     layer with rejection markers attached to that result row.
  3. Empty block -- a verify phase with NO inner-command keys yields a SKIP
     layer (i.e. legacy show_commands-only recipes are unaffected).
  4. Substitution -- ``$KEY`` placeholders inside trace_views.file are
     replaced by ``sub_params`` via the same substitute_fn the runner uses.
  5. No-SSH path -- when ``ssh_session=None`` is passed but the recipe
     declares inner blocks, the glue degrades gracefully to a SKIP layer
     (never raises, never crashes the scenario).

The test is read-only on the device:

  * Only ``show`` / ``cat /.gitcommit`` style commands are run.
  * No commit, no rollback, no config-mode entry.
  * Persistent SSH sessions are cleaned up on exit.

Usage::

    cd ~/drivenets-topology-studio/scaler/TEST/catalog/evpn_mac_mobility_SW204115
    PYTHONPATH=. python3 tools/selftest_inner_runner.py            # PE-1 default
    PYTHONPATH=. python3 tools/selftest_inner_runner.py --device PE-4

Exit code: 0 if all 5 cases pass, 1 otherwise. Safe to wire into CI as a
smoke check before any recipe edits enable inner-command surfaces.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Make the suite importable when invoked from any cwd.
SUITE_ROOT = Path(__file__).resolve().parent.parent
if str(SUITE_ROOT) not in sys.path:
    sys.path.insert(0, str(SUITE_ROOT))

from shared.device_runner import (  # noqa: E402
    cleanup_all_sessions,
    get_persistent_ssh_session,
    get_session_credentials,
)
from shared.inner_command_runner_glue import execute_inner_command_blocks  # noqa: E402
from shared.observability import ObservabilityCollector  # noqa: E402
from shared.verdict_engine import VerdictStatus  # noqa: E402


def _substitute(cmd: str, params):
    """Mirror ``orchestration.scenario_runner.substitute`` -- ``$key`` => params[key]."""
    if not params:
        return cmd
    out = cmd
    for k, v in params.items():
        out = out.replace(f"${k}", str(v))
    return out


def _print_results(label, layer, raw):
    print(
        f"[INFO] {label} -> layer={layer.status} -- {layer.detail} "
        f"({len(raw)} result(s))",
        flush=True,
    )
    for r in raw:
        out_snip = (r.get("output", "") or "")[:80].replace("\n", " | ")
        print(
            f"  - [{r['surface']}] {r['command'][:50]:<50} "
            f"ok={r['ok']} markers={r['markers']} "
            f"out_len={len(r.get('output') or '')} '{out_snip}'",
            flush=True,
        )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Live self-test for inner-command runner wiring",
    )
    parser.add_argument(
        "--device",
        default="PE-1",
        help="DNOS device to run the read-only checks against (default: PE-1)",
    )
    args = parser.parse_args(argv)
    device = args.device

    print(f"[INFO] resolving credentials for {device}", flush=True)
    creds = get_session_credentials(device)
    if not creds:
        print(f"[FAIL] no credentials for {device}", flush=True)
        return 1
    print(
        f"[OK] creds: ip={creds['ip']} user={creds['username']}",
        flush=True,
    )

    print("[INFO] opening persistent SSH session", flush=True)
    ssh = get_persistent_ssh_session(device)
    if ssh is None:
        print("[FAIL] no SSH session", flush=True)
        return 1
    print("[OK] session alive", flush=True)

    obs = ObservabilityCollector(
        test_id="selftest_inner_runner",
        scenario_id="sc_inner",
        device=device,
    )
    obs.begin_phase("verify")

    # --- Test 1: healthy block ---------------------------------------------
    print(
        "\n[TEST 1] healthy block -- vtysh + ncc_shell + xraycli + trace_views",
        flush=True,
    )
    healthy_verify = {
        "vtysh_commands": [
            "show version",
        ],
        "ncc_shell_commands": [
            "cat /.gitcommit",
        ],
        "xraycli": [
            {"ncp_id": 0, "topics": ["/wb_agent/flowspec/info"]},
        ],
        "trace_views": [
            {
                "file": "routing_engine/bgpd_traces",
                "match": "Established",
                "context_before": 0,
                "context_after": 0,
                "max_lines": 5,
            },
        ],
    }
    t0 = time.time()
    layer, raw = execute_inner_command_blocks(
        verify_phase=healthy_verify,
        device=device,
        obs=obs,
        sub_params={},
        substitute_fn=_substitute,
        ssh_session=ssh,
        password=creds["password"],
    )
    elapsed = time.time() - t0
    print(f"[INFO] elapsed={elapsed:.2f}s", flush=True)
    _print_results("healthy", layer, raw)
    test1_pass = (
        layer.status == VerdictStatus.PASS
        and len(raw) >= 4
        and all(r["ok"] for r in raw)
    )
    print(f"[{'OK' if test1_pass else 'FAIL'}] Test 1: healthy=PASS", flush=True)

    # --- Test 2: deliberate bad command -> FAIL layer ----------------------
    print("\n[TEST 2] bad-command block -- vtysh receives nonsense", flush=True)
    bad_verify = {
        "vtysh_commands": [
            "show this-command-definitely-does-not-exist",
        ],
    }
    layer2, raw2 = execute_inner_command_blocks(
        verify_phase=bad_verify,
        device=device,
        obs=obs,
        sub_params=None,
        substitute_fn=None,
        ssh_session=ssh,
        password=creds["password"],
    )
    _print_results("bad-command", layer2, raw2)
    test2_pass = (
        layer2.status == VerdictStatus.FAIL
        and len(raw2) >= 1
        and any(r["markers"] for r in raw2)
    )
    print(f"[{'OK' if test2_pass else 'FAIL'}] Test 2: bad-command=FAIL", flush=True)

    # --- Test 3: empty inner block -> SKIP --------------------------------
    print("\n[TEST 3] empty verify (no inner keys) -- expect SKIP", flush=True)
    layer3, raw3 = execute_inner_command_blocks(
        verify_phase={"show_commands": ["show system | no-more"]},
        device=device,
        obs=obs,
        sub_params=None,
        substitute_fn=None,
        ssh_session=ssh,
        password=creds["password"],
    )
    test3_pass = layer3.status == VerdictStatus.SKIP and len(raw3) == 0
    print(f"[INFO] empty -> layer={layer3.status} -- {layer3.detail}", flush=True)
    print(f"[{'OK' if test3_pass else 'FAIL'}] Test 3: empty=SKIP", flush=True)

    # --- Test 4: substitution -----------------------------------------------
    print(
        "\n[TEST 4] substitution -- $TEST_FILE replaced in trace_views.file",
        flush=True,
    )
    subst_verify = {
        "trace_views": [
            {
                "file": "$TEST_FILE",
                "match": "Established",
                "context_before": 0,
                "context_after": 0,
                "max_lines": 3,
            },
        ],
    }
    layer4, raw4 = execute_inner_command_blocks(
        verify_phase=subst_verify,
        device=device,
        obs=obs,
        sub_params={"TEST_FILE": "routing_engine/bgpd_traces"},
        substitute_fn=_substitute,
        ssh_session=ssh,
        password=creds["password"],
    )
    cmd_text = raw4[0]["command"] if raw4 else ""
    test4_pass = (
        "routing_engine/bgpd_traces" in cmd_text and "$TEST_FILE" not in cmd_text
    )
    print(f"[INFO] substituted command: {cmd_text[:120]}", flush=True)
    print(f"[{'OK' if test4_pass else 'FAIL'}] Test 4: substitution", flush=True)

    # --- Test 5: ssh_session=None graceful SKIP ----------------------------
    print(
        "\n[TEST 5] no SSH session + declared blocks -- expect graceful SKIP",
        flush=True,
    )
    layer5, raw5 = execute_inner_command_blocks(
        verify_phase=healthy_verify,
        device=device,
        obs=obs,
        sub_params=None,
        substitute_fn=None,
        ssh_session=None,
        password=None,
    )
    test5_pass = layer5.status == VerdictStatus.SKIP and len(raw5) == 0
    print(f"[INFO] None-session -> layer={layer5.status} -- {layer5.detail}", flush=True)
    print(f"[{'OK' if test5_pass else 'FAIL'}] Test 5: None-session=SKIP", flush=True)

    obs.end_phase()
    cleanup_all_sessions()

    all_pass = test1_pass and test2_pass and test3_pass and test4_pass and test5_pass
    print()
    print("=" * 70)
    print(f"INNER-RUNNER SELF-TEST: {'ALL PASS' if all_pass else 'FAILURES'}")
    print(f"  Test 1 (healthy=PASS):      {'OK' if test1_pass else 'FAIL'}")
    print(f"  Test 2 (bad-command=FAIL):  {'OK' if test2_pass else 'FAIL'}")
    print(f"  Test 3 (empty=SKIP):        {'OK' if test3_pass else 'FAIL'}")
    print(f"  Test 4 (substitution):      {'OK' if test4_pass else 'FAIL'}")
    print(f"  Test 5 (None-session=SKIP): {'OK' if test5_pass else 'FAIL'}")
    print("=" * 70)
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
