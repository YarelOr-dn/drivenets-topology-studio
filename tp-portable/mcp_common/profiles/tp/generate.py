"""TP generation orchestration with --agent sdk|cursor|none."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from mcp_common.profiles.tp.gates_runner import run_parity, run_refine, run_selfcheck
from mcp_common.profiles.tp.ingest import ingest_epic
from mcp_common.profiles.tp.knowledge import knowledge_gate
from mcp_common.profiles.tp.tp_env import resolve_epic_dir, resolve_tp_root


def _write_generation_brief(epic_dir: Path, epic: str, *, agent: str, categories: list[str] | None) -> Path:
    brief = {
        "epic": epic,
        "agent": agent,
        "categories": categories or [],
        "tp_root": str(resolve_tp_root()),
        "instructions": (
            "Follow tp-generator-command skill. Author full_result.json + manifest.json + "
            "test_plan markdown. Run tp selfcheck + tp parity before declaring done."
        ),
    }
    path = epic_dir / "generation_brief.json"
    path.write_text(json.dumps(brief, indent=2) + "\n", encoding="utf-8")
    return path


def _sdk_handoff(epic: str, *, categories: list[str] | None) -> dict[str, Any]:
    summary = f"/TP generate {epic}"
    steps = [
        f"Ingest and generate TP for {epic} including enabler epics",
        "Run Stage-7 refine loop (max 3 iterations)",
        "Run tp selfcheck + parity; fix until green",
    ]
    if categories:
        steps.insert(1, f"Categories: {', '.join(categories)}")
    try:
        from mcp_common.profiles.test.sdk_scheduler import sdk_continue

        out = sdk_continue(summary=summary, steps=steps, scope="nondestructive")
        return {"ok": bool(out.get("ok")), "agent": "sdk", **out}
    except Exception as exc:
        return {
            "ok": False,
            "agent": "sdk",
            "error": str(exc),
            "report_block": (
                "[ERROR] SDK handoff failed. Ensure user-test-mcp is bound and run:\n"
                "  python3 -m mcp_common.profiles.test.sdk_cli doctor\n"
                f"Detail: {exc}"
            ),
        }


def run_generate(
    epic: str,
    *,
    agent: str = "none",
    categories: list[str] | None = None,
    strict_knowledge: bool = False,
) -> dict[str, Any]:
    epic = epic.upper()
    gate = knowledge_gate(epic, strict=strict_knowledge)
    if not gate.get("ok"):
        return gate

    ingest = ingest_epic(epic)
    if not ingest.get("ok"):
        return ingest

    epic_dir = resolve_epic_dir(epic)

    if agent == "cursor":
        brief = _write_generation_brief(epic_dir, epic, agent=agent, categories=categories)
        return {
            "ok": True,
            "agent": "cursor",
            "brief_path": str(brief),
            "knowledge": gate,
            "message": "Generation brief written; continue in Cursor with /TP skill.",
        }

    if agent == "sdk":
        sdk = _sdk_handoff(epic, categories=categories)
        sdk["knowledge"] = gate
        return sdk

    # agent == none: deterministic pipeline only (ingest + gates if artifacts exist)
    fr = epic_dir / "full_result.json"
    if not fr.is_file():
        brief = _write_generation_brief(epic_dir, epic, agent="none", categories=categories)
        return {
            "ok": True,
            "agent": "none",
            "knowledge": gate,
            "brief_path": str(brief),
            "message": (
                "Ingest complete. No full_result.json yet — author TCs (agent) then re-run "
                "tp selfcheck / tp parity / tp refine."
            ),
        }

    rc_sc = run_selfcheck(epic)
    rc_ref = run_refine(epic) if rc_sc == 0 else 1
    rc_par = run_parity(epic) if rc_ref == 0 else 1
    ok = rc_sc == 0 and rc_ref == 0 and rc_par == 0
    return {
        "ok": ok,
        "agent": "none",
        "knowledge": gate,
        "selfcheck_rc": rc_sc,
        "refine_rc": rc_ref,
        "parity_rc": rc_par,
    }
