"""TP environment resolver - portable /TP layer.

Precedence (highest first):
  TP_* env vars -> ~/.cursor/tp_config.json -> project mcp.json -> ~/.cursor/mcp.json -> bundled defaults
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

__version__ = "2026.07.19.1"

TP_CONFIG_PATH = Path.home() / ".cursor" / "tp_config.json"
DEFAULT_SCALER_ROOT = Path.home() / "SCALER"
DEFAULT_JIRA_BASE_URL = "https://drivenets.atlassian.net"
DEFAULT_CONFLUENCE_BASE_URL = "https://drivenets.atlassian.net/wiki"
DEFAULT_STRICT_KNOWLEDGE = False

_PROFILE_ROOT = Path(__file__).resolve().parent
_CONFIG_CACHE: dict[str, Any] | None = None


def profile_root() -> Path:
    return _PROFILE_ROOT


def _read_json(path: Path) -> dict[str, Any]:
    try:
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def load_tp_config() -> dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        _CONFIG_CACHE = _read_json(TP_CONFIG_PATH)
    return dict(_CONFIG_CACHE)


def _env_first(*keys: str, config_key: str | None = None, default: Any = None) -> Any:
    for k in keys:
        v = os.environ.get(k)
        if v is not None and str(v).strip() != "":
            return v
    if config_key:
        cfg = load_tp_config()
        if config_key in cfg and cfg[config_key] not in (None, ""):
            return cfg[config_key]
    return default


def resolve_scaler_root() -> Path:
    raw = _env_first("TP_SCALER_ROOT", "SCALER_ROOT", config_key="scaler_root",
                       default=str(DEFAULT_SCALER_ROOT))
    return Path(str(raw)).expanduser()


def resolve_tp_root() -> Path:
    raw = _env_first("TP_ROOT", config_key="tp_root", default=str(resolve_scaler_root() / "TEST" / "tp"))
    return Path(str(raw)).expanduser()


def resolve_reference_dir() -> Path:
    raw = _env_first("TP_REFERENCE_DIR", config_key="reference_dir",
                     default=str(profile_root() / "reference"))
    return Path(str(raw)).expanduser()


def resolve_knowledge_dir() -> Path:
    raw = _env_first("TP_KNOWLEDGE_DIR", config_key="knowledge_dir",
                     default=str(Path.home() / ".cursor" / "knowledge_base"))
    return Path(str(raw)).expanduser()


def resolve_knowledge_seed_dir() -> Path:
    return profile_root() / "knowledge_seed"


def resolve_cache_dir() -> Path:
    raw = _env_first("TP_CACHE_DIR", config_key="cache_dir",
                     default=str(Path.home() / ".cursor" / "tp_cache"))
    return Path(str(raw)).expanduser()


def resolve_cheetah_glob() -> str:
    return str(_env_first("TP_CHEETAH_GLOB", config_key="cheetah_glob",
                          default=str(Path.home() / "cheetah*")))


def resolve_mcp_root() -> Path:
    raw = _env_first("TP_MCP_ROOT", config_key="mcp_root",
                     default=str(profile_root() / "mcp" / "tp_agent_mcp"))
    return Path(str(raw)).expanduser()


def resolve_mcp_cli() -> Path:
    raw = _env_first("TP_MCP_CLI", config_key="mcp_cli",
                     default=str(Path.home() / "mcp_common" / "mcp_cli.py"))
    return Path(str(raw)).expanduser()


def resolve_jira_mode() -> str:
    return str(_env_first("TP_JIRA_MODE", config_key="jira_mode", default="auto")).lower()


def resolve_jira_base_url() -> str:
    return str(_env_first("JIRA_BASE_URL", config_key="jira_base_url",
                          default=DEFAULT_JIRA_BASE_URL)).rstrip("/")


def resolve_confluence_base_url() -> str:
    return str(_env_first("CONFLUENCE_BASE_URL", config_key="confluence_base_url",
                          default=DEFAULT_CONFLUENCE_BASE_URL)).rstrip("/")


def resolve_jira_credentials() -> dict[str, str]:
    cfg = load_tp_config()
    jira = cfg.get("jira") if isinstance(cfg.get("jira"), dict) else {}
    return {
        "base_url": resolve_jira_base_url(),
        "user_email": str(
            os.environ.get("JIRA_USER_EMAIL")
            or os.environ.get("JIRA_USERNAME")
            or jira.get("user_email")
            or jira.get("username")
            or ""
        ).strip(),
        "api_token": str(
            os.environ.get("JIRA_API_TOKEN")
            or jira.get("api_token")
            or ""
        ).strip(),
    }


def resolve_strict_knowledge() -> bool:
    raw = _env_first("TP_STRICT_KNOWLEDGE", config_key="strict_knowledge",
                     default="1" if DEFAULT_STRICT_KNOWLEDGE else "0")
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def resolve_epic_dir(epic: str) -> Path:
    return resolve_tp_root() / epic.upper()


def atomic_write_json(path: Path, obj: Any) -> None:
    import tempfile

    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o600 if "config" in path.name or "secret" in path.name else 0o644)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def portability_doctor() -> dict[str, Any]:
    """Portable environment report for tp doctor."""
    from mcp_common.profiles.tp.jira_client import doctor_backends

    scaler = resolve_scaler_root()
    tp_root = resolve_tp_root()
    reference = resolve_reference_dir()
    knowledge = resolve_knowledge_dir()
    creds = resolve_jira_credentials()
    mcp_root = resolve_mcp_root()

    remediation: list[str] = []
    if not reference.is_dir():
        remediation.append(f"reference dir missing: {reference} (run install-tp.sh)")
    if not (reference / "tp_checklist.json").is_file():
        remediation.append(f"tp_checklist.json missing under {reference}")
    if not tp_root.is_dir():
        remediation.append(f"create TP output root or set TP_ROOT (current: {tp_root})")
    if not creds["api_token"]:
        remediation.append("set JIRA_API_TOKEN + JIRA_USER_EMAIL or ~/.cursor/tp_config.json jira section")
    if not mcp_root.is_dir():
        remediation.append(f"tp-agent-mcp missing: {mcp_root}")

    jira_ok = bool(creds["api_token"] and creds["user_email"])
    jira_backends = doctor_backends()
    any_jira = any(b.get("available") for b in jira_backends)
    seed_count = 0
    seed_dir = resolve_knowledge_seed_dir()
    if seed_dir.is_dir():
        seed_count = sum(1 for p in seed_dir.iterdir() if p.is_dir() and not p.name.startswith("."))

    knowledge_count = 0
    if knowledge.is_dir():
        knowledge_count = sum(1 for p in knowledge.iterdir() if p.is_dir() and not p.name.startswith("."))

    go = (
        reference.is_dir()
        and (reference / "tp_checklist.json").is_file()
        and mcp_root.is_dir()
        and (jira_ok or any_jira or resolve_jira_mode() in ("plugin", "dn-mcp", "auto"))
    )

    return {
        "go": go,
        "profile_root": str(profile_root()),
        "profile_version": __version__,
        "scaler_root": str(scaler),
        "tp_root": str(tp_root),
        "reference_dir": str(reference),
        "knowledge_dir": str(knowledge),
        "knowledge_seed_count": seed_count,
        "knowledge_installed_count": knowledge_count,
        "cache_dir": str(resolve_cache_dir()),
        "mcp_root": str(mcp_root),
        "jira_mode": resolve_jira_mode(),
        "jira_base_url": resolve_jira_base_url(),
        "jira_credentials_present": jira_ok,
        "jira_backends": jira_backends,
        "strict_knowledge": resolve_strict_knowledge(),
        "tp_config_path": str(TP_CONFIG_PATH),
        "tp_config_present": TP_CONFIG_PATH.is_file(),
        "remediation": remediation,
    }


def tp_config_schema_doc() -> str:
    return json.dumps({
        "scaler_root": "/path/to/SCALER (optional)",
        "tp_root": "~/SCALER/TEST/tp (optional)",
        "reference_dir": "bundled reference path (optional)",
        "knowledge_dir": "~/.cursor/knowledge_base (optional)",
        "cache_dir": "~/.cursor/tp_cache (optional)",
        "jira_mode": "auto|rest|plugin|dn-mcp",
        "jira_base_url": "https://your.atlassian.net",
        "confluence_base_url": "https://your.atlassian.net/wiki",
        "strict_knowledge": False,
        "jira": {
            "user_email": "you@company.com",
            "api_token": "ATATT...",
        },
    }, indent=2)
