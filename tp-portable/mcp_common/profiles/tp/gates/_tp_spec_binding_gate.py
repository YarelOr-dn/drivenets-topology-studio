#!/usr/bin/env python3
"""Bind every TC command to spec or live syntax authority for /TP Stage 7.

Writes spec_binding_report.json; collect_findings() feeds refine_worklist.

Usage:
    python3 _tp_spec_binding_gate.py --epic SW-211037
    python3 _tp_spec_binding_gate.py --epic SW-211037 --strict   # exit 1 on UNBOUND*

Exit 0 = no UNBOUND / UNBOUND_LIVE (or non-strict report).
Exit 1 = (--strict) at least one UNBOUND or UNBOUND_LIVE.
Exit 2 = missing artifacts.
"""
from __future__ import annotations

from _tp_paths import default_data_dir
import argparse
import json
import sys
from pathlib import Path
from typing import Any

from _tp_syntax_common import (
    atomic_write_json,
    commands_match,
    extract_tc_commands,
    normalize_cmd,
)


def _load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _bind_spec(cmd: str, inventory: list[dict]) -> tuple[str | None, str | None]:
    tc_norm = normalize_cmd(cmd)
    if not tc_norm or tc_norm.startswith("(gnmi") or tc_norm.startswith("(netconf"):
        return None, None
    if tc_norm.startswith("configure no "):
        tc_norm = "configure " + tc_norm[len("configure no ") :]
    for ent in inventory:
        for key in ("norm",):
            spec_norm = ent.get(key) or ""
            if commands_match(tc_norm, spec_norm):
                return ent.get("source"), ent.get("cmd")
        level = ent.get("level") or ""
        syn = ent.get("syntax_only") or ent.get("raw") or ""
        if level and syn:
            combo = normalize_cmd(f"{level} {syn}")
            if commands_match(tc_norm, combo):
                return ent.get("source"), ent.get("cmd")
        syn_norm = ent.get("norm_syntax") or normalize_cmd(syn)
        if syn_norm and len(syn_norm) >= 6 and syn_norm in tc_norm:
            return ent.get("source"), ent.get("cmd")
        if syn_norm and syn_norm.startswith("show ") and tc_norm.startswith(syn_norm):
            return ent.get("source"), ent.get("cmd")
        if level:
            lvl_norm = normalize_cmd(level)
            if lvl_norm and lvl_norm in tc_norm and syn_norm and syn_norm in tc_norm:
                return ent.get("source"), ent.get("cmd")
    for ent in inventory:
        level = ent.get("level") or ""
        if not level:
            continue
        lvl_norm = normalize_cmd(level)
        if lvl_norm and len(lvl_norm) >= 24 and lvl_norm in tc_norm:
            return ent.get("source"), level
    return None, None


def _live_vs_spec_drift(live_text: str, spec_cmd: str) -> bool:
    return normalize_cmd(live_text) != normalize_cmd(spec_cmd)


def _bind_command(
    cmd: str,
    *,
    implementation_status: str,
    inventory: list[dict],
    device: str | None,
    has_blocker: bool = False,
) -> dict[str, Any]:
    spec_source, spec_cmd = _bind_spec(cmd, inventory)
    row: dict[str, Any] = {
        "command": cmd,
        "norm": normalize_cmd(cmd),
        "state": "UNBOUND",
        "spec_source": spec_source,
        "spec_cmd": spec_cmd,
        "live_source": None,
        "drift": False,
        "note": None,
    }

    low = cmd.strip().lower()
    if low.endswith("?") or " ?" in low:
        row["state"] = "PENDING_BUILD"
        row["note"] = "?-completion probe"
        if spec_source:
            row["state"] = spec_source if spec_source.startswith("SPEC_") else "PENDING_BUILD"
        return row
    if low.startswith("(gnmi") or low.startswith("(netconf"):
        row["state"] = "PENDING_BUILD"
        row["note"] = "non-CLI mutation surface"
        return row
    if low.startswith("(") or not low.startswith(
        ("show ", "configure", "clear ", "debug ", "rollback ", "load ")
    ):
        row["state"] = "PENDING_BUILD"
        row["note"] = "non-executable CLI fragment or scope note"
        return row

    if implementation_status == "shipped_in_lab" and device:
        try:
            from _tp_live_syntax_probe import probe_live_syntax  # noqa: WPS433

            live = probe_live_syntax(device, cmd)
            qm = live.get("question_mark")
            cs = live.get("cmd_search")
            if qm:
                row["live_source"] = "LIVE_QUESTION_MARK"
                row["state"] = "LIVE_QUESTION_MARK"
                live_text = qm if isinstance(qm, str) else json.dumps(qm)
                if spec_source and _live_vs_spec_drift(live_text, spec_cmd or cmd):
                    row["state"] = "DRIFT"
                    row["drift"] = True
                    row["note"] = "live ?-completion disagrees with SPEC"
                return row
            if cs:
                row["live_source"] = "LIVE_CMD_SEARCH"
                row["state"] = "LIVE_CMD_SEARCH"
                if spec_source:
                    row["state"] = "PENDING_BUILD" if not spec_source else row["state"]
                return row
            if spec_source:
                row["state"] = spec_source.split(":", 1)[0] if spec_source.startswith("SPEC_") else "SPEC"
                if spec_source.startswith("SPEC_USER_STORY"):
                    row["state"] = spec_source
                elif spec_source.startswith("SPEC_RST"):
                    row["state"] = spec_source
                return row
            row["state"] = "UNBOUND_LIVE"
            return row
        except Exception as exc:  # pragma: no cover
            row["note"] = f"live probe error: {exc}"

    if spec_source:
        if spec_source.startswith("SPEC_USER_STORY"):
            row["state"] = spec_source
        elif spec_source.startswith("SPEC_RST"):
            row["state"] = spec_source
        else:
            row["state"] = "PENDING_BUILD"
        if implementation_status == "pending_build":
            row["note"] = "pending_build; SPEC binding only"
        return row

    if has_blocker and implementation_status == "pending_build" and low.startswith(
        ("show ", "debug ", "configure", "clear ", "rollback", "load ")
    ):
        row["state"] = "PENDING_BUILD"
        row["note"] = "RST BLOCKER; binding deferred until cheetah worktree"
        return row

    row["state"] = "UNBOUND"
    return row


def bind_all(tp_dir: Path, epic: str, *, write: bool = True) -> dict[str, Any]:
    fr_path = tp_dir / "full_result.json"
    inv_path = tp_dir / "cli_spec_inventory.json"
    ver_path = tp_dir / "epic_version.json"
    if not fr_path.is_file():
        raise FileNotFoundError(f"Missing full_result.json: {fr_path}")

    fr = json.loads(fr_path.read_text(encoding="utf-8"))
    inventory_doc = _load_json(inv_path) or {"entries": []}
    ver = _load_json(ver_path) or {}
    inventory = inventory_doc.get("entries") or []
    impl = ver.get("implementation_status") or "pending_build"
    device = ver.get("lab_device")

    bindings: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in extract_tc_commands(fr):
        cmd = row["command"]
        key = f"{row['tc_id']}|{normalize_cmd(cmd)}"
        if key in seen:
            continue
        seen.add(key)
        bound = _bind_command(
            cmd,
            implementation_status=impl,
            inventory=inventory,
            device=device,
            has_blocker=bool(ver.get("blocker")),
        )
        bound["tc_id"] = row["tc_id"]
        bound["origin"] = row["origin"]
        bindings.append(bound)

    counts: dict[str, int] = {}
    for b in bindings:
        st = b.get("state") or "UNBOUND"
        base = st.split(":", 1)[0] if ":" in st else st
        counts[base] = counts.get(base, 0) + 1

    report = {
        "epic": epic,
        "fix_version": ver.get("fix_version"),
        "implementation_status": impl,
        "inventory_total": len(inventory),
        "command_count": len(bindings),
        "counts": counts,
        "blocker": ver.get("blocker"),
        "bindings": bindings,
    }
    if write:
        atomic_write_json(tp_dir / "spec_binding_report.json", report)
    return report


def collect_findings(tp_dir: Path, epic: str) -> list[dict]:
    report_path = tp_dir / "spec_binding_report.json"
    if not report_path.is_file():
        return [{
            "kind": "spec-binding",
            "target_id": epic,
            "what_missing": "spec_binding_report.json (run harvester + gate)",
            "source_ref": "_tp_spec_binding_gate",
            "suggested_action": "Run _tp_epic_version.py, _tp_cli_spec_harvester.py, _tp_spec_binding_gate.py",
            "severity": "error",
        }]

    report = json.loads(report_path.read_text(encoding="utf-8"))
    out: list[dict] = []
    if report.get("blocker"):
        blk = report["blocker"]
        out.append({
            "kind": "spec-binding",
            "target_id": epic,
            "what_missing": blk.get("message", "cheetah version BLOCKER"),
            "source_ref": "epic_version.json",
            "suggested_action": blk.get("suggested_cmd", "Add matching cheetah worktree"),
            "severity": "warn",
        })

    for b in report.get("bindings") or []:
        st = b.get("state") or ""
        if st == "UNBOUND":
            out.append({
                "kind": "spec-binding",
                "target_id": b.get("tc_id") or epic,
                "what_missing": f"UNBOUND command: {b.get('command', '')[:120]}",
                "source_ref": "cli_spec_inventory.json",
                "suggested_action": "spec-binding-fixer: bind to story/RST or remove invented command",
                "severity": "error",
            })
        elif st == "UNBOUND_LIVE":
            out.append({
                "kind": "spec-binding",
                "target_id": b.get("tc_id") or epic,
                "what_missing": f"UNBOUND_LIVE: {b.get('command', '')[:120]}",
                "source_ref": "live probe",
                "suggested_action": "Run ?-completion via dnos-cli-completion-protocol; tell user if both null",
                "severity": "error",
            })
        elif st == "DRIFT" or b.get("drift"):
            out.append({
                "kind": "spec-binding",
                "target_id": b.get("tc_id") or epic,
                "what_missing": f"DRIFT live != SPEC: {b.get('command', '')[:120]}",
                "source_ref": b.get("spec_source") or "SPEC",
                "suggested_action": "File drift_report.json + Jira comment; do NOT mutate TP",
                "severity": "warn",
            })
    return out


def run_gate(tp_dir: Path, epic: str, *, strict: bool = False, write: bool = True) -> int:
    try:
        report = bind_all(tp_dir, epic, write=write)
    except FileNotFoundError as exc:
        print(f"[FAIL] {exc}")
        return 2

    unbound = sum(1 for b in report["bindings"] if b.get("state") == "UNBOUND")
    unbound_live = sum(1 for b in report["bindings"] if b.get("state") == "UNBOUND_LIVE")
    drift = sum(1 for b in report["bindings"] if b.get("state") == "DRIFT" or b.get("drift"))
    spec_hits = sum(
        1 for b in report["bindings"]
        if str(b.get("state", "")).startswith("SPEC_")
    )

    print(f"[OK] spec_binding_report.json commands={report['command_count']} "
          f"SPEC={spec_hits} UNBOUND={unbound} UNBOUND_LIVE={unbound_live} DRIFT={drift}")
    if report.get("blocker"):
        print(f"[WARN] {report['blocker'].get('message')}")

    if strict and (unbound or unbound_live):
        print(f"[FAIL] spec-binding strict: UNBOUND={unbound} UNBOUND_LIVE={unbound_live}")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="/TP spec-binding gate")
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    tp_dir = Path(args.dir).expanduser() / args.epic
    return run_gate(tp_dir, args.epic, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
