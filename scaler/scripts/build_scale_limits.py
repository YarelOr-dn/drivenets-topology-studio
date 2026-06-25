#!/usr/bin/env python3
"""build_scale_limits.py - reconcile the three DNOS scale-limit sources into one DB.

Today three sources disagree:
  * scaler/limits.json                       (live-verified, pool/ifindex authoritative)
  * scaler/scaler/validator.py    DNOS_LIMITS (GUI/wizard validation)
  * scaler/scaler/cli_rules_db.py DNOS_LIMITS ("from Release Notes")

Known disagreements (FXC 8000 vs 32000, BGP 2000 vs 1024, PWHE 4000 vs 8192,
flowspec-interfaces 8000 vs 1000) are NOT silently auto-picked.  This builder:

  1. Ingests all three + the per-NCP hardware mapping from limits.json.
  2. Maps each source key to a CANONICAL key, records every source's value, and
     flags ``disagreement: true`` when sources differ.
  3. Picks an authoritative ``value`` (live-verified limits.json wins; else the
     majority/first source) with a ``confidence`` + ``reconciliation_notes``.
  4. PRESERVES each consumer's CURRENT effective value under ``consumers`` so the
     loader can rebuild validator.py / cli_rules_db.py dicts BYTE-IDENTICAL today
     (zero behavior change) while making scale_limits.json the single SoT.
  5. Emits ``scale_limits.json`` (atomic) + ``scale_limits_compat_diff.json``
     listing every value that WOULD change if a consumer adopted the canonical
     value (so a human can decide, per the plan's "flag every changed value").

Run:  python3 scaler/scripts/build_scale_limits.py [--check]
  --check : do not write; exit non-zero if scale_limits.json is stale/missing
            (used by the golden-snapshot regression test).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_SCALER = Path(__file__).resolve().parents[1]          # .../scaler
LIMITS_JSON = REPO_SCALER / "limits.json"
OUT_DB = REPO_SCALER / "scale_limits.json"
OUT_DIFF = REPO_SCALER / "scale_limits_compat_diff.json"
SCHEMA_VERSION = "1.0"


def _atomic_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(obj, f, indent=2, sort_keys=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def _load_python_dnos_limits() -> tuple[dict[str, int], dict[str, int]]:
    """Import validator.py and cli_rules_db.py DNOS_LIMITS (scaler on sys.path)."""
    if str(REPO_SCALER) not in sys.path:
        sys.path.insert(0, str(REPO_SCALER))
    validator_limits: dict[str, int] = {}
    cli_limits: dict[str, int] = {}
    try:
        from scaler.validator import DNOS_LIMITS as _vl  # type: ignore
        validator_limits = dict(_vl)
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] could not import scaler.validator DNOS_LIMITS: {exc}", file=sys.stderr)
    try:
        from scaler.cli_rules_db import DNOS_LIMITS as _cl  # type: ignore
        cli_limits = dict(_cl)
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] could not import scaler.cli_rules_db DNOS_LIMITS: {exc}", file=sys.stderr)
    return validator_limits, cli_limits


# Canonical limit definitions: which source key feeds each canonical limit.
# (canonical_key, scope, limits_json_path, validator_key, cli_key, prefer)
# ``limits_json_path`` is a dotted path into limits.json dnos_platform_limits.
# ``prefer`` chooses the authoritative value: "limits_json" | "validator" | "cli".
_CANON = [
    # services
    ("max_fxc_instances", "per-system", "services.max_fxc_instances", "services_fxc", "max_fxc_instances", "limits_json"),
    ("max_evpn_instances", "per-system", "services.max_evpn_instances", "services_evpn", "max_evpn_vpls_instances", "limits_json"),
    ("max_vrf_instances", "per-system", None, "services_vrf", "max_l3vpn_instances", "validator"),
    ("max_vpws_instances", "per-system", None, "services_vpws", None, "validator"),
    ("max_bridge_domain_instances", "per-system", None, "services_bridge_domain", None, "validator"),
    # bgp
    ("max_bgp_peers", "per-system", "bgp.max_peers", "bgp_peers", "max_bgp_peers", "limits_json"),
    ("max_bgp_routes", "per-system", None, "bgp_routes", None, "validator"),
    # multihoming
    ("max_esi_interfaces", "per-system", "multihoming.max_esi_interfaces", "multihoming_esi", None, "limits_json"),
    # interfaces / pools
    ("max_pwhe_interfaces", "pool", "ifindex_pools.ph_pool.max_capacity", "interfaces_pwhe", "max_pwhe_interfaces", "limits_json"),
    ("max_qinq_stag", "pool", "ifindex_pools.stag_pool.max_capacity", "interfaces_pwhe_qinq", None, "limits_json"),
    ("max_vlan_subinterfaces", "pool", "ifindex_pools.vlan_pool.max_capacity", "vlan_subinterfaces", None, "limits_json"),
    ("max_irb_interfaces", "pool", "ifindex_pools.irb_pool.max_capacity", "interfaces_irb", "max_irb_interfaces", "limits_json"),
    ("max_datapath_interfaces", "per-system", None, "interfaces_total", None, "validator"),
    ("max_bundle_interfaces", "per-system", None, "interfaces_bundle", "max_bundle_interfaces", "validator"),
    ("max_bundle_subinterfaces", "per-system", None, None, "max_bundle_subinterfaces", "cli"),
    ("max_physical_interfaces", "per-system", None, "interfaces_physical", "max_physical_interfaces", "validator"),
    ("max_loopback_interfaces", "per-system", None, "interfaces_loopback", "max_loopback_interfaces", "validator"),
    # flowspec (per-NCP TCAM)
    ("max_flowspec_hw_ipv4_per_ncp", "per-NCP", "flowspec.hw_tcam_per_ncp.ipv4_capacity", None, "max_flowspec_hw_entries_ipv4", "limits_json"),
    ("max_flowspec_hw_ipv6_per_ncp", "per-NCP", "flowspec.hw_tcam_per_ncp.ipv6_capacity", None, "max_flowspec_hw_entries_ipv6", "limits_json"),
    ("max_flowspec_rules_total", "per-system", "flowspec.max_rules_total", None, "max_flowspec_rules_total", "limits_json"),
    ("max_flowspec_rules_per_vrf", "per-system", "flowspec.max_rules_per_vrf", None, "max_flowspec_rules_per_vrf", "limits_json"),
    ("max_flowspec_interfaces", "per-system", "flowspec.max_flowspec_interfaces", None, "max_flowspec_interfaces", "limits_json"),
    ("max_flowspec_local_policies", "per-system", "flowspec.max_local_policies", None, "max_flowspec_local_policies", "limits_json"),
    ("max_flowspec_vpn_peers", "per-system", "flowspec.max_flowspec_vpn_peers", None, None, "limits_json"),
]


def _dig(d: dict, dotted: str) -> Any:
    cur: Any = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    limits_json = json.loads(LIMITS_JSON.read_text())
    dpl = limits_json.get("dnos_platform_limits", {})
    validator_limits, cli_limits = _load_python_dnos_limits()

    limits: dict[str, Any] = {}
    diff_rows: list[dict[str, Any]] = []

    for canon, scope, lj_path, v_key, c_key, prefer in _CANON:
        lj_val = _dig(dpl, lj_path) if lj_path else None
        v_val = validator_limits.get(v_key) if v_key else None
        c_val = cli_limits.get(c_key) if c_key else None

        sources: dict[str, Any] = {}
        if lj_val is not None:
            sources["limits.json"] = lj_val
        if v_val is not None:
            sources["validator.py"] = v_val
        if c_val is not None:
            sources["cli_rules_db.py"] = c_val

        present = [x for x in (lj_val, v_val, c_val) if x is not None]
        disagreement = len(set(present)) > 1

        # authoritative value
        prefer_val = {"limits_json": lj_val, "validator": v_val, "cli": c_val}.get(prefer)
        value = prefer_val if prefer_val is not None else (present[0] if present else None)
        confidence = "high" if (prefer == "limits_json" and lj_val is not None and not disagreement) else (
            "medium" if not disagreement else "low")

        notes = ""
        if disagreement:
            notes = (
                f"sources disagree {sources}; authoritative={value} (prefer={prefer}); "
                f"resolve by live verification before raising any consumer's effective value"
            )

        # consumer-preserved effective values (so loaders stay byte-identical today)
        consumers: dict[str, Any] = {}
        if v_key is not None and v_val is not None:
            consumers["validator"] = {"key": v_key, "value": v_val}
        if c_key is not None and c_val is not None:
            consumers["cli_rules_db"] = {"key": c_key, "value": c_val}

        limits[canon] = {
            "value": value,
            "scope": scope,
            "source": prefer,
            "dnos_version": "25.4",
            "confidence": confidence,
            "sources": sources,
            "disagreement": disagreement,
            "reconciliation_notes": notes,
            "consumers": consumers,
        }

        # compat diff: would adopting canonical value change a consumer?
        for cons_name, info in consumers.items():
            if value is not None and info["value"] != value:
                diff_rows.append({
                    "canonical": canon,
                    "consumer": cons_name,
                    "consumer_key": info["key"],
                    "current_effective": info["value"],
                    "canonical_value": value,
                    "action": "PRESERVED (no change applied); adopt canonical only with explicit override",
                })

    db = {
        "schema_version": SCHEMA_VERSION,
        "generated_by": "scaler/scripts/build_scale_limits.py",
        "dnos_version_baseline": "25.4",
        "description": (
            "Reconciled DNOS scale-limit DB. Single source of truth across "
            "limits.json + validator.py + cli_rules_db.py. Per-limit provenance, "
            "disagreement flags, and per-consumer PRESERVED effective values so "
            "loaders stay byte-identical until a value is explicitly overridden."
        ),
        "limits": limits,
        "pools": dpl.get("ifindex_pools", {}),
        "soft_limits": dpl.get("soft_limits", {}),
        "pwhe_service_impact": dpl.get("pwhe_service_impact", {}),
        "per_ncp": {
            # Per-NCP overrides; flowspec TCAM is per-NCP. Default applies to all
            # NCP models unless a model-specific override is added here later.
            "_default": {
                "max_flowspec_hw_ipv4_per_ncp": _dig(dpl, "flowspec.hw_tcam_per_ncp.ipv4_capacity"),
                "max_flowspec_hw_ipv6_per_ncp": _dig(dpl, "flowspec.hw_tcam_per_ncp.ipv6_capacity"),
            },
        },
        "hardware_model_mapping": (limits_json.get("notes", {}) or {}).get("hardware_model_mapping", {}),
    }
    diff = {
        "schema_version": SCHEMA_VERSION,
        "generated_by": "scaler/scripts/build_scale_limits.py",
        "summary": (
            f"{len(diff_rows)} consumer value(s) differ from the canonical value; "
            f"all PRESERVED (no behavior change). Review before overriding."
        ),
        "rows": diff_rows,
    }
    return db, diff


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="do not write; exit 1 if scale_limits.json is missing or stale")
    args = ap.parse_args()

    db, diff = build()

    if args.check:
        if not OUT_DB.exists():
            print("scale_limits.json MISSING", file=sys.stderr)
            return 1
        current = json.loads(OUT_DB.read_text())
        # compare limits payload only (ignore volatile top-level metadata)
        if current.get("limits") != db.get("limits") or current.get("per_ncp") != db.get("per_ncp"):
            print("scale_limits.json STALE (re-run build_scale_limits.py)", file=sys.stderr)
            return 1
        print("scale_limits.json up to date")
        return 0

    _atomic_write_json(OUT_DB, db)
    _atomic_write_json(OUT_DIFF, diff)
    n_dis = sum(1 for v in db["limits"].values() if v["disagreement"])
    print(f"[ok] wrote {OUT_DB} ({len(db['limits'])} canonical limits, {n_dis} with source disagreement)")
    print(f"[ok] wrote {OUT_DIFF} ({len(diff['rows'])} preserved consumer diffs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
