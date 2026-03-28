#!/usr/bin/env python3
"""
Spirent pre-flight checks for EVPN test execution.

Verifies Spirent session is alive, port connectivity is healthy,
and DNAAS path is ready before starting traffic-dependent tests.
Returns structured results so the orchestrator can decide whether
to proceed with Spirent traffic, fall back to manual, or abort.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("spirent_preflight")

SPIRENT_TOOL_PATHS = [
    Path.home() / "SCALER" / "SPIRENT" / "spirent_tool.py",
    Path.home() / "drivenets-topology-studio" / "scaler" / "SPIRENT" / "spirent_tool.py",
]


def _find_spirent_tool() -> Optional[Path]:
    for p in SPIRENT_TOOL_PATHS:
        if p.exists():
            return p
    return None


def _run_spirent_cmd(
    tool_path: Path, args: List[str], timeout: int = 30,
) -> Dict[str, Any]:
    try:
        cmd = ["python3", str(tool_path)] + args
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode == 0:
            try:
                return json.loads(proc.stdout)
            except json.JSONDecodeError:
                return {"status": "ok", "raw": proc.stdout[:1000]}
        return {"status": "error", "stderr": proc.stderr[:500], "rc": proc.returncode}
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def check_spirent_session(
    tool_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Check if Spirent session is alive and ports are connected."""
    tool = tool_path or _find_spirent_tool()
    if not tool:
        return {
            "available": False,
            "reason": "spirent_tool.py not found",
            "searched": [str(p) for p in SPIRENT_TOOL_PATHS],
        }

    result = _run_spirent_cmd(tool, ["status", "--json"])
    if result.get("status") in ("timeout", "error"):
        detail = result.get("detail", result.get("stderr", "unknown"))
        return {
            "available": False,
            "reason": f"Spirent status check failed: {detail}",
            "tool_path": str(tool),
        }

    return {
        "available": True,
        "tool_path": str(tool),
        "session": result,
    }


def check_dnaas_path(
    vlan: int, tool_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Check if DNAAS bridge-domain path is ready for the specified VLAN."""
    tool = tool_path or _find_spirent_tool()
    if not tool:
        return {"ready": False, "reason": "spirent_tool.py not found"}

    result = _run_spirent_cmd(tool, ["dnaas", "check", "--vlan", str(vlan)])
    if result.get("status") in ("timeout", "error"):
        detail = result.get("detail", result.get("stderr", "unknown"))
        return {
            "ready": False,
            "reason": f"DNAAS check failed: {detail}",
            "vlan": vlan,
        }

    return {"ready": True, "vlan": vlan, "detail": result}


def run_preflight(
    vlans: Optional[List[int]] = None,
    require_spirent: bool = False,
) -> Dict[str, Any]:
    """Full Spirent pre-flight: session + DNAAS paths.

    Args:
        vlans: VLANs to check DNAAS path readiness for.
        require_spirent: If True, preflight fails when Spirent is unavailable.
                         If False, warnings are issued but tests can proceed
                         with TrafficMethod.MANUAL fallback.

    Returns:
        {
            "pass": bool,
            "spirent_available": bool,
            "spirent": {...session check...},
            "dnaas_paths": [...per-vlan results...],
            "warnings": [...],
            "traffic_method": "spirent" | "manual",
        }
    """
    result: Dict[str, Any] = {
        "pass": True,
        "spirent_available": False,
        "warnings": [],
        "traffic_method": "manual",
    }

    session = check_spirent_session()
    result["spirent"] = session
    result["spirent_available"] = session.get("available", False)

    if not session.get("available"):
        msg = f"Spirent unavailable: {session.get('reason')}"
        if require_spirent:
            result["pass"] = False
            result["warnings"].append(f"[FAIL] {msg}")
        else:
            result["warnings"].append(
                f"[WARN] {msg}; tests will use MANUAL traffic method"
            )
    else:
        result["traffic_method"] = "spirent"

    if vlans and session.get("available"):
        tool = Path(session["tool_path"])
        dnaas_results = []
        for vlan in vlans:
            dnaas = check_dnaas_path(vlan, tool)
            dnaas_results.append(dnaas)
            if not dnaas.get("ready"):
                result["warnings"].append(
                    f"[WARN] DNAAS path not ready for VLAN {vlan}: "
                    f"{dnaas.get('reason', 'unknown')}"
                )
        result["dnaas_paths"] = dnaas_results

    return result
