"""Jira push runner for tp CLI."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from mcp_common.profiles.tp.tp_env import resolve_epic_dir, resolve_tp_root


def _gates_dir() -> Path:
    return Path(__file__).resolve().parent / "gates"


def run_push(
    epic: str,
    *,
    category: str | None = None,
    tc: str | None = None,
    adf_config: bool = False,
    dry_run: bool = True,
) -> dict[str, Any]:
    epic = epic.upper()
    epic_dir = resolve_epic_dir(epic)
    if not (epic_dir / "manifest.json").is_file():
        return {"ok": False, "error": f"manifest missing: {epic_dir / 'manifest.json'}"}

    env = dict(**{k: v for k, v in __import__("os").environ.items()})
    root = Path(__file__).resolve().parents[2]
    env["PYTHONPATH"] = str(root) + ":" + str(_gates_dir())

    if tc and adf_config:
        args = ["--epic", epic, "--tc", tc, "--dry-run"]
        if not dry_run:
            args.append("--push")
        cmd = [sys.executable, str(_gates_dir() / "_tp_jira_push_adf.py"), *args]
        p = subprocess.run(cmd, capture_output=True, text=True, env=env)
        return {
            "ok": p.returncode == 0,
            "tool": "_tp_jira_push_adf.py",
            "dry_run": dry_run,
            "stdout": (p.stdout or "")[-4000:],
            "stderr": (p.stderr or "")[-2000:],
            "rc": p.returncode,
        }

    if category:
        args = ["--epic", epic, "--category", category, "--dir", str(resolve_tp_root())]
        if dry_run:
            args.append("--dry-run")
        cmd = [sys.executable, str(_gates_dir() / "_tp_push_category.py"), *args]
        p = subprocess.run(cmd, capture_output=True, text=True, env=env)
        return {
            "ok": p.returncode == 0,
            "tool": "_tp_push_category.py",
            "dry_run": dry_run,
            "stdout": (p.stdout or "")[-4000:],
            "stderr": (p.stderr or "")[-2000:],
            "rc": p.returncode,
        }

    # Fallback: create_jira_test_issues dry-run against test_plan markdown
    md = epic_dir / f"test_plan_{epic}.md"
    if not md.is_file():
        return {"ok": False, "error": "specify --category or --tc --adf-config; no test_plan markdown"}

    push_script = Path(__file__).resolve().parent / "push" / "create_jira_test_issues.py"
    args = [str(push_script), str(md), "--epic", epic, "--dry-run"]
    p = subprocess.run([sys.executable, *args], capture_output=True, text=True, env=env)
    return {
        "ok": p.returncode == 0,
        "tool": "create_jira_test_issues.py",
        "dry_run": True,
        "stdout": (p.stdout or "")[-4000:],
        "stderr": (p.stderr or "")[-2000:],
        "rc": p.returncode,
    }
