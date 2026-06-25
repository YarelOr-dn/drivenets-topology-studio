"""/SPIRENT <-> /TEST sync mandate.

Per user mandate 2026-04-20: any /TEST that needs Spirent devices, BGP, or
traffic MUST auto-invoke /SPIRENT before execution to (1) verify DNAAS fabric
path health through the `dnos_dnaas_*` MCP tools and (2) apply canonical
SPIRENT description tags on every Spirent-owned DNOS object.

This module owns the glue layer between the /TEST orchestrator and
``spirent_sync.run_full_sync``. It is deliberately isolated so the mandate
has a single readable home.

Public API:
    _requires_spirent(recipe, infra_required) -> bool
    _resolve_spirent_vlan(recipe, params) -> int
    _dev_ip(device) -> str
    auto_invoke_spirent_sync(*, device, recipe, infra_required,
                             params, auto_fix=True, dry_run=False) -> dict | None
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# spirent_sync import (optional -- if unavailable, auto_invoke_spirent_sync
# degrades to a no-op with a clear warning rather than breaking /TEST).
# ---------------------------------------------------------------------------
try:
    from spirent_sync import run_full_sync as _spirent_full_sync
except Exception as _ssx:  # noqa: BLE001
    _spirent_full_sync = None  # type: ignore[assignment]
    _spirent_sync_err: Optional[Exception] = _ssx
else:
    _spirent_sync_err = None


def _requires_spirent(recipe: Dict[str, Any], infra_required: str) -> bool:
    """True when this recipe needs /SPIRENT (devices, BGP, or traffic)."""
    if infra_required in ("spirent_vpls_cp", "mixed", "evpn_with_spirent"):
        return True
    for sc in recipe.get("scenarios", []) or []:
        method = str(sc.get("method") or "").lower()
        if method.startswith("spirent"):
            return True
        for key in ("expect", "phases"):
            blob = sc.get(key) or {}
            txt = json.dumps(blob) if isinstance(blob, (dict, list)) else ""
            if "spirent" in txt.lower() or "check_ha_traffic" in txt:
                return True
    return False


def _resolve_spirent_vlan(recipe: Dict[str, Any], params: Dict[str, Any]) -> Optional[int]:
    """Best-effort extraction of the fabric VLAN needed for dnaas-fix."""
    for key in ("fabric_vlan", "outer_vlan", "ac1_vlan", "vlan"):
        val = params.get(key) if isinstance(params, dict) else None
        if val:
            try:
                return int(str(val).strip())
            except Exception:
                continue
    for sc in recipe.get("scenarios", []) or []:
        blob = json.dumps(sc) if isinstance(sc, dict) else ""
        m = re.search(r'"(?:fabric_vlan|outer_vlan|vlan)"\s*:\s*(\d+)', blob)
        if m:
            return int(m.group(1))
    return 214  # current PE-1 EVPN default


def _dev_ip(device: str) -> str:
    """Resolve a device name/hostname to its mgmt IP from devices.json.

    Handles both list-shaped and dict-shaped device DBs, including the
    ``{"devices": [...], "settings": ...}`` format used in the live lab.
    """
    try:
        db_path = Path("/home/dn/SCALER/db/devices.json")
        if not db_path.exists():
            return ""
        with db_path.open() as fh:
            raw = json.load(fh)
        entries: List[Dict[str, Any]] = []
        if isinstance(raw, list):
            entries = [d for d in raw if isinstance(d, dict)]
        elif isinstance(raw, dict):
            if isinstance(raw.get("devices"), list):
                entries = [d for d in raw["devices"] if isinstance(d, dict)]
            else:
                for key, val in raw.items():
                    if isinstance(val, dict):
                        val.setdefault("name", key)
                        entries.append(val)
        for dev in entries:
            for field in ("name", "hostname", "alias"):
                if str(dev.get(field) or "").strip() == device:
                    for ipk in ("mgmt_ip", "ip", "address"):
                        ip = dev.get(ipk)
                        if ip:
                            return str(ip)
    except Exception:
        pass
    return ""


def auto_invoke_spirent_sync(
    *,
    device: str,
    recipe: Dict[str, Any],
    infra_required: str,
    params: Dict[str, Any],
    auto_fix: bool = True,
    dry_run: bool = False,
) -> Optional[Dict[str, Any]]:
    """Per user mandate 2026-04-20: any /TEST needing Spirent MUST call /SPIRENT sync.

    Runs MCP-backed fabric health and description tagging (mark-dnos) via
    ``spirent_sync.run_full_sync``. The DUT name is passed for DNAAS path
    correlation; the management IP is used only for description tagging.

    No-op for tests that do not require Spirent resources (returns None).
    Returns the structured status dict on success/failure.
    """
    if not _requires_spirent(recipe, infra_required):
        return None
    if _spirent_full_sync is None:
        print(
            f"[SPIRENT-SYNC] helper unavailable ({_spirent_sync_err!r}); skipping auto-sync",
            flush=True,
        )
        return None
    vlan = _resolve_spirent_vlan(recipe, params or {})
    dut_ip = _dev_ip(device) or device
    print(
        f"\n[SPIRENT-SYNC] /TEST <-> /SPIRENT mandate: vlan={vlan} dut={dut_ip} "
        f"auto_fix={auto_fix} dry_run={dry_run}",
        flush=True,
    )
    try:
        try:
            status = _spirent_full_sync(
                vlan=vlan,
                dut=device,
                dut_for_descriptions=(dut_ip or device),
                auto_fix=auto_fix,
                include_fabric_desc=True,
                dry_run=dry_run,
            )
        except TypeError:
            # Older helper signature. Keep the run visible, but the updated
            # helper should always be present in this catalog.
            status = _spirent_full_sync(
                vlan=vlan,
                dut=(dut_ip or device),
                auto_fix=auto_fix,
                include_fabric_desc=True,
                dry_run=dry_run,
            )
    except Exception as exc:  # noqa: BLE001
        print(f"[SPIRENT-SYNC] FAILED: {exc}", flush=True)
        return {"overall": "FAIL", "error": str(exc), "vlan": vlan, "dut": dut_ip}
    overall = status.get("overall", "UNKNOWN") if isinstance(status, dict) else "UNKNOWN"
    print(f"[SPIRENT-SYNC] overall={overall}", flush=True)
    if isinstance(status, dict):
        for step in status.get("steps", []) or []:
            tag = step.get("step", "?")
            st = step.get("status", "?")
            detail = step.get("detail", "")
            print(f"  [{tag}] {st} -- {detail}", flush=True)
    return status


__all__ = [
    "_requires_spirent",
    "_resolve_spirent_vlan",
    "_dev_ip",
    "auto_invoke_spirent_sync",
    "_spirent_full_sync",
    "_spirent_sync_err",
]
