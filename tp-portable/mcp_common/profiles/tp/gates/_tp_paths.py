"""Shared path resolution for portable /TP gate scripts."""
from __future__ import annotations

from pathlib import Path

GATES_DIR = Path(__file__).resolve().parent


def default_data_dir() -> str:
    try:
        from mcp_common.profiles.tp.tp_env import resolve_tp_root

        return str(resolve_tp_root())
    except Exception:
        return str(Path.home() / "SCALER" / "TEST" / "tp")


def resolve_data_dir(arg: str | None = None) -> Path:
    if arg:
        return Path(arg).expanduser()
    return Path(default_data_dir())


def gates_script(name: str) -> Path:
    return GATES_DIR / name


def resolve_mcp_root() -> Path:
    try:
        from mcp_common.profiles.tp.tp_env import resolve_mcp_root as _rm

        return _rm()
    except Exception:
        return GATES_DIR.parent / "mcp" / "tp_agent_mcp"


def resolve_mcp_cli() -> Path:
    try:
        from mcp_common.profiles.tp.tp_env import resolve_mcp_cli as _rc

        return _rc()
    except Exception:
        return Path.home() / "mcp_common" / "mcp_cli.py"


def resolve_jira_base_url() -> str:
    try:
        from mcp_common.profiles.tp.tp_env import resolve_jira_base_url as _rj

        return _rj()
    except Exception:
        return "https://drivenets.atlassian.net"


def resolve_cache_dir() -> Path:
    try:
        from mcp_common.profiles.tp.tp_env import resolve_cache_dir as _rc

        return _rc()
    except Exception:
        return Path.home() / ".cursor" / "tp_cache"


def resolve_cheetah_glob() -> str:
    try:
        from mcp_common.profiles.tp.tp_env import resolve_cheetah_glob as _rg

        return _rg()
    except Exception:
        return str(Path.home() / "cheetah*")
