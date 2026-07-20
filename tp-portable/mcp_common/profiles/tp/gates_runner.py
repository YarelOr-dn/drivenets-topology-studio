"""Gate runner wrappers for tp CLI."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from mcp_common.profiles.tp.tp_env import resolve_tp_root


def _gates_dir() -> Path:
    return Path(__file__).resolve().parent / "gates"


def _run_gate(script: str, *args: str) -> int:
    cmd = [sys.executable, str(_gates_dir() / script), *args]
    env = dict(**{k: v for k, v in __import__("os").environ.items()})
    root = Path(__file__).resolve().parents[2]  # mcp_common
    env["PYTHONPATH"] = str(root) + ":" + str(_gates_dir()) + (
        ":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    p = subprocess.run(cmd, env=env)
    return int(p.returncode)


def run_selfcheck(epic: str, *, skip_mcp_validate: bool = False) -> int:
    args = ["--epic", epic, "--dir", str(resolve_tp_root())]
    if skip_mcp_validate:
        args.append("--skip-mcp-validate")
    return _run_gate("_tp_self_check.py", *args)


def run_parity(epic: str, *, strict: bool = False) -> int:
    args = ["--epic", epic, "--dir", str(resolve_tp_root())]
    if strict:
        args.append("--strict")
    return _run_gate("_tp_parity_gate.py", *args)


def run_refine(epic: str, *, max_iterations: int = 3) -> int:
    args = ["--epic", epic, "--dir", str(resolve_tp_root()), "--max-iterations", str(max_iterations)]
    return _run_gate("_tp_refine_loop.py", *args)


def run_review(
    epic: str,
    *,
    tc: str | None = None,
    category: str | None = None,
    list_all: bool = False,
    fmt: str = "chat",
) -> str:
    import subprocess

    args = ["--epic", epic, "--dir", str(resolve_tp_root()), "--format", fmt]
    if tc:
        args += ["--tc", tc]
    if category:
        args += ["--category", category]
    if list_all:
        args.append("--list")
    cmd = [sys.executable, str(_gates_dir() / "_tp_review.py"), *args]
    env = dict(**{k: v for k, v in __import__("os").environ.items()})
    root = Path(__file__).resolve().parents[2]
    env["PYTHONPATH"] = str(root) + ":" + str(_gates_dir())
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return (p.stdout or "") + (p.stderr or "")
