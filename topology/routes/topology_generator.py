"""Scaler bridge routes: AI Topology Generator.

This router gathers per-device facts that the front-end Generate Topology
panel (``topology-generator.js``) normalizes into its facts model and
turns into canvas-ready objects. We deliberately reuse the existing
``_get_device_context`` / ``DeviceCommHelper`` / ``_build_config_summary``
helpers instead of inventing a new SSH path, so the live data is already
multi-user-aware (per-user SSH pool keying, per-user system_type
overrides, etc.).

Endpoints:
    GET  /api/topology-generator/device-facts
        Query params: device_id, ssh_host?, fetch_config?, live?
        Returns:
            {
                "device_id": str,
                "context": {
                    "hostname": str,
                    "system_type": str,
                    "dnos_version": str,
                    "mgmt_ip": str,
                    "role": str,           # best-effort hint
                    "as_number": str,
                    "router_id": str,
                    "loopback0_ip": str
                },
                "config_facts": {
                    "asn": int|None,
                    "vrfs": [str, ...],
                    "route_targets": [str, ...],
                    "evpn_services": {kind: count},
                    "summary_lines": int
                } | None,
                "lldp_neighbors": [
                    {"local_interface": str, "peer_hostname": str,
                     "peer_interface": str, "peer_chassis_id": str}
                ]
            }

The route is read-only (no config push). All errors degrade to a partial
payload so a single failing device never blocks generation for the rest.

Authentication is enforced by the global JWT middleware in
``scaler_bridge.py`` -- this module assumes ``request.state.user`` is
already populated.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request

import json
import re
import time

from routes._device_comm import DeviceCommHelper
from routes._state import _get_request_user
from routes.bridge_helpers import (
    _build_config_summary,
    _build_scaler_ops_index,
    _get_device_context,
    _resolve_device,
    _resolve_mgmt_ip,
)

try:
    from api.auth.user_store import user_store
except Exception:  # pragma: no cover - import path differs in some runners
    user_store = None

try:
    from mcp.auth import current_mcp_user
    from mcp.dispatcher import dispatch as topology_mcp_dispatch
except Exception:  # pragma: no cover - MCP package may be unavailable in isolated tests
    current_mcp_user = None  # type: ignore
    topology_mcp_dispatch = None  # type: ignore

try:
    from routes.topology_generator_correlate import (
        correlate_topology_facts,
        enrich_canvas_link_tables,
    )
except Exception:  # pragma: no cover
    correlate_topology_facts = None  # type: ignore
    enrich_canvas_link_tables = None  # type: ignore

router = APIRouter()


_IP_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
_LEARNING_FILE = "topology_generator_learning.json"


def _norm_key(value: Any) -> str:
    return str(value or "").strip().lower()


def _read_user_device_records(username: str) -> Dict[str, Any]:
    """Read the authenticated user's device credential records, if present."""
    if not username or not user_store:
        return {}
    try:
        path = user_store.user_data_path(username, "devices.json")
        if not path.exists():
            return {}
        with open(path) as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _dispatch_topology_mcp(username: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Call the in-process Topology MCP dispatcher as the authenticated app user."""
    if current_mcp_user is None or topology_mcp_dispatch is None:
        raise HTTPException(status_code=503, detail="Topology MCP dispatcher unavailable")
    marker = current_mcp_user.set(username)
    try:
        result = topology_mcp_dispatch(tool_name, arguments or {})
    finally:
        current_mcp_user.reset(marker)
    if not isinstance(result, dict):
        raise HTTPException(status_code=502, detail="Topology MCP returned an invalid response")
    if result.get("ok") is False:
        raise HTTPException(status_code=400, detail=result.get("error") or "Topology MCP call failed")
    return result


def _read_legacy_sections(username: str) -> List[Dict[str, Any]]:
    if not username or user_store is None:
        return []
    try:
        path = user_store.user_data_path(username, "sections/_sections.json")
        data = json.loads(path.read_text(encoding="utf-8") or "[]")
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _resolve_generator_mcp_domain(username: str, section_id: str = "", domain_id: str = "", domain_name: str = "") -> Dict[str, Any]:
    """Resolve a legacy generator section into the canonical Topology MCP domain."""
    domains_result = _dispatch_topology_mcp(username, "topology_list_domains", {"include_shared": False})
    domains = domains_result.get("domains") or []
    by_id = {str(item.get("id") or ""): item for item in domains if isinstance(item, dict)}
    if domain_id and domain_id in by_id:
        return by_id[domain_id]

    wanted_name = (domain_name or "").strip()
    if section_id:
        for section in _read_legacy_sections(username):
            if not isinstance(section, dict) or str(section.get("id") or "") != str(section_id):
                continue
            wanted_name = wanted_name or str(section.get("name") or "").strip()
            break

    if wanted_name:
        wanted_lc = wanted_name.lower()
        for domain in domains:
            if str(domain.get("name") or "").strip().lower() == wanted_lc:
                return domain

    if domain_id and domain_id not in by_id:
        raise HTTPException(status_code=400, detail=f"Unknown topology MCP domain: {domain_id}")

    created = _dispatch_topology_mcp(username, "topology_create_domain", {
        "name": wanted_name or "Generated Topologies",
        "description": "Created by the topology generator MCP-backed save flow.",
    })
    return created.get("domain") or {}


def _unique_generated_topology_name(username: str, domain_id: str, wanted_name: str) -> str:
    name = (wanted_name or "Generated Topology").strip() or "Generated Topology"
    existing = _dispatch_topology_mcp(username, "topology_list_topologies", {
        "domain_id": domain_id,
        "include_shared": False,
    }).get("topologies") or []
    names = {str(item.get("name") or "").strip().lower() for item in existing if isinstance(item, dict)}
    if name.lower() not in names:
        return name
    for index in range(2, 1000):
        candidate = f"{name} {index}"
        if candidate.lower() not in names:
            return candidate
    return f"{name} {int(time.time())}"


def _record_keys(record_id: str, record: Dict[str, Any]) -> set[str]:
    keys = {_norm_key(record_id)}
    for key in (
        "id", "deviceId", "device_id", "hostname", "host", "label",
        "name", "serial", "deviceSerial", "mgmt_ip", "management_ip", "ip",
        "_registeredDeviceId", "_registeredHostname",
    ):
        value = record.get(key)
        if isinstance(value, list):
            keys.update(_norm_key(item) for item in value if item)
        elif value:
            keys.add(_norm_key(value))
    for key in ("aliases", "alias"):
        aliases = record.get(key)
        if isinstance(aliases, list):
            keys.update(_norm_key(item) for item in aliases if item)
    return {key for key in keys if key}


def _find_user_ssh_config(username: str, *candidates: Any) -> Dict[str, Any]:
    records = _read_user_device_records(username)
    if not records:
        return {}
    wanted = {_norm_key(item) for item in candidates if _norm_key(item)}
    if not wanted:
        return {}
    default_record = records.get("_default") if isinstance(records.get("_default"), dict) else None
    for record_id, record in records.items():
        if record_id == "_default" or not isinstance(record, dict):
            continue
        if wanted.isdisjoint(_record_keys(str(record_id), record)):
            continue
        user = record.get("user") or record.get("device_user")
        password = record.get("password") or record.get("device_password")
        if not user and not password:
            continue
        return {
            "host": record.get("host") or record.get("mgmt_ip") or record.get("management_ip") or "",
            "hostBackup": record.get("hostBackup") or record.get("serial") or record.get("deviceSerial") or "",
            "user": user or "",
            "password": password or "",
            "source": "user-devices.json",
            "confidence": "exact",
            "matched_key": str(record_id),
        }
    if default_record:
        user = default_record.get("user") or default_record.get("device_user")
        password = default_record.get("password") or default_record.get("device_password")
        if user or password:
            return {
                "user": user or "",
                "password": password or "",
                "source": "user-devices.json:_default",
                "confidence": "default",
                "matched_key": "_default",
            }
    return {}


def _safe_role_hint(hostname: str, system_type: str) -> str:
    """Best-effort role inference from hostname/system-type so the
    generator's layout engine has a tier hint when LLDP is silent.

    Mirrors the tier hints used by ``NetworkMapperManager._classifyDevice``
    on the frontend so the deterministic and live paths agree on roles.
    """
    h = (hostname or "").lower()
    st = (system_type or "").lower()
    if "ncm" in st or "ncm" in h or "superspine" in h:
        return "super-spine"
    if "spine" in h:
        return "spine"
    if "ncc" in st or "ncc" in h or "rr" in h:
        return "rr"
    if "ncf" in st or "ncf" in h or "leaf" in h:
        return "leaf"
    if "pe" in h or "router" in h or "dut" in h:
        return "pe"
    if "ce" in h or "customer" in h:
        return "ce"
    if any(t in h for t in ("exabgp", "ixia", "tester", "spirent")):
        return "external"
    if st.startswith("cl-") or st.startswith("sa-"):
        return "ncr"
    return "router"


def _learning_path(username: str):
    if user_store is None:
        raise HTTPException(status_code=503, detail="user store unavailable")
    return user_store.user_data_path(username or "default", _LEARNING_FILE)


def _read_learning(username: str) -> Dict[str, Any]:
    path = _learning_path(username)
    if not path.exists():
        return {"version": 1, "entries": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
    except Exception:
        return {"version": 1, "entries": {}}
    if not isinstance(data, dict):
        return {"version": 1, "entries": {}}
    data.setdefault("version", 1)
    data.setdefault("entries", {})
    if not isinstance(data["entries"], dict):
        data["entries"] = {}
    return data


def _write_learning(username: str, data: Dict[str, Any]) -> None:
    path = _learning_path(username)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _signature_key(signature: Dict[str, Any]) -> str:
    if not isinstance(signature, dict):
        return ""
    key = str(signature.get("key") or "").strip()
    if key:
        return key[:500]
    parts = [
        ",".join(map(str, sorted(signature.get("roles") or []))),
        ",".join(map(str, sorted(signature.get("protocols") or []))),
        ",".join(map(str, sorted(signature.get("asns") or []))),
        ",".join(map(str, sorted(signature.get("vrfs") or []))),
        str(signature.get("size") or ""),
    ]
    return "|".join(parts)[:500]


def _signature_similarity(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    if not isinstance(a, dict) or not isinstance(b, dict):
        return 0.0
    score = 0.0
    for field, weight in (("roles", 0.35), ("protocols", 0.3), ("asns", 0.2), ("vrfs", 0.15)):
        aa = set(map(str, a.get(field) or []))
        bb = set(map(str, b.get(field) or []))
        if not aa and not bb:
            score += weight
        elif aa or bb:
            score += weight * (len(aa & bb) / max(len(aa | bb), 1))
    size_a = int(a.get("size") or 0)
    size_b = int(b.get("size") or 0)
    if size_a and size_b:
        score *= max(0.65, 1.0 - (abs(size_a - size_b) / max(size_a, size_b, 1)))
    return round(score, 4)


def _parse_bgp_summary(output: str) -> Dict[str, Any]:
    peers: List[Dict[str, Any]] = []
    local_as = ""
    router_id = ""
    for line in (output or "").splitlines():
        if "local AS number" in line:
            m = re.search(r"identifier\s+([\d.]+),\s+local AS number\s+(\d+)", line)
            if m:
                router_id, local_as = m.group(1), m.group(2)
        cols = line.split()
        if cols and re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", cols[0]) and len(cols) >= 9:
            peers.append({
                "peer": cols[0],
                "remote_as": cols[2] if len(cols) > 2 else "",
                "state": cols[-1],
                "raw": line.strip()[:220],
            })
    return {"router_id": router_id, "local_as": local_as, "peers": peers, "peer_count": len(peers)}


def _parse_ospf_neighbors(output: str) -> List[Dict[str, Any]]:
    neighbors: List[Dict[str, Any]] = []
    for line in (output or "").splitlines():
        cols = line.split()
        if cols and re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", cols[0]) and len(cols) >= 5:
            neighbors.append({
                "neighbor_id": cols[0],
                "state": cols[2],
                "address": cols[4] if len(cols) > 4 else "",
                "interface": cols[5].split(":")[0] if len(cols) > 5 else "",
                "raw": line.strip()[:220],
            })
    return neighbors


def _parse_route_summary(output: str) -> Dict[str, Any]:
    protocols: Dict[str, Dict[str, str]] = {}
    for line in (output or "").splitlines():
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] and cells[0].lower() not in ("protocol", "------------"):
            if cells[0].startswith("-") or cells[0].startswith("+"):
                continue
            protocols[cells[0]] = {
                "ipv4": cells[1] if len(cells) > 1 else "",
                "ipv6": cells[2] if len(cells) > 2 else "",
            }
    return {"protocols": protocols}


def _normalize_lldp(raw: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
    """Compact LLDP rows into the small shape the generator expects.

    ``_get_device_context`` already returns a normalized list (see
    ``_normalize_lldp_neighbor`` in ``bridge_helpers.py``). We trim it
    further so the JSON wire payload stays small per device.
    """
    out: List[Dict[str, Any]] = []
    for row in raw or []:
        if not isinstance(row, dict):
            continue
        out.append({
            "local_interface": row.get("local_interface")
                or row.get("local_port")
                or row.get("local_intf")
                or "",
            "peer_hostname": row.get("peer_hostname")
                or row.get("neighbor")
                or row.get("system_name")
                or "",
            "peer_interface": row.get("peer_interface")
                or row.get("peer_port")
                or row.get("port_id")
                or "",
            "peer_chassis_id": row.get("peer_chassis_id")
                or row.get("chassis_id")
                or "",
        })
    return out


def _config_facts_from_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    """Pick the small subset of ``_build_config_summary`` fields the
    generator actually uses. Avoids leaking unrelated pieces (RT lists
    can be large) to the browser.
    """
    asn_raw = summary.get("as_number") or ""
    asn: Optional[int] = None
    try:
        if asn_raw:
            asn = int(asn_raw)
    except (TypeError, ValueError):
        asn = None
    rts = summary.get("route_targets") or []
    if isinstance(rts, list):
        rts = [str(x) for x in rts][:64]
    else:
        rts = []
    evpn = summary.get("evpn_services") or {}
    if not isinstance(evpn, dict):
        evpn = {}
    return {
        "asn": asn,
        "vrfs": [],
        "route_targets": rts,
        "evpn_services": evpn,
        "summary_lines": int(summary.get("lines") or 0),
        "loopback0_ip": summary.get("loopback0_ip") or "",
        "router_id": summary.get("router_id") or "",
    }


def _config_facts_from_running(config: str) -> Dict[str, Any]:
    """Richer logical-topology facts pulled directly from running config.

    Goes beyond ``_build_config_summary`` to extract VRFs, BGP peers,
    ISIS/OSPF area, MPLS / LDP / SR / EVPN hints, RD/RT, bridge domains,
    and IPv4 interface addresses. Returns a small JSON-friendly dict the
    Live Devices tab uses for richer logical edges and grouping shapes.

    Best-effort: missing or unrecognised sections collapse to empty
    lists rather than raising, so partial / non-DNOS configs still
    yield whatever can be parsed.
    """
    out: Dict[str, Any] = {
        "asn": None,
        "router_id": "",
        "loopback0_ip": "",
        "vrfs": [],
        "bridge_domains": [],
        "interfaces": [],
        "subinterfaces": [],
        "bundles": [],
        "bgp_peers": [],
        "isis": {"area": "", "interfaces": []},
        "ospf": {"area": "", "interfaces": []},
        "mpls": {"enabled": False, "ldp": False, "sr": False},
        "evpn": {"enabled": False, "bds": 0, "vrfs": 0},
        "route_targets": [],
        "route_distinguishers": [],
    }
    if not config:
        return out

    cfg = config

    # ASN, router-id, loopback come from the existing summary helper.
    try:
        summary = _build_config_summary(cfg) or {}
        try:
            if summary.get("as_number"):
                out["asn"] = int(summary["as_number"])
        except (TypeError, ValueError):
            pass
        out["router_id"] = summary.get("router_id") or ""
        out["loopback0_ip"] = summary.get("loopback0_ip") or ""
        rts = summary.get("route_targets") or []
        if isinstance(rts, list):
            out["route_targets"] = [str(x) for x in rts][:64]
        evpn_svcs = summary.get("evpn_services") or {}
        if isinstance(evpn_svcs, dict) and evpn_svcs:
            out["evpn"]["enabled"] = True
            out["evpn"]["bds"] = int(evpn_svcs.get("bd", 0))
            out["evpn"]["vrfs"] = int(evpn_svcs.get("vrf", 0))
    except Exception:
        pass

    # VRFs -- ``vrf <name>`` blocks at the top hierarchy.
    try:
        for m in re.finditer(r"^\s*vrf\s+(\S+)", cfg, re.MULTILINE):
            name = m.group(1).strip()
            if name and name.lower() not in ("default", "management", "mgmt"):
                if name not in out["vrfs"]:
                    out["vrfs"].append(name)
        out["vrfs"] = out["vrfs"][:64]
    except Exception:
        pass

    # BGP peers -- ``neighbors <ip-or-group>`` and ``remote-as <n>`` pairs.
    try:
        peers: List[Dict[str, Any]] = []
        last_neighbor: Optional[str] = None
        for line in cfg.splitlines():
            line_s = line.strip()
            m = re.match(r"^neighbors?\s+(\S+)", line_s)
            if m:
                last_neighbor = m.group(1)
                continue
            m = re.match(r"^remote-as\s+(\d+)", line_s)
            if m and last_neighbor:
                peers.append({"peer": last_neighbor, "remote_as": int(m.group(1))})
                last_neighbor = None
        out["bgp_peers"] = peers[:64]
    except Exception:
        pass

    # ISIS area / metric.
    try:
        m = re.search(r"isis\s+\d+\s+net\s+(\S+)", cfg)
        if m:
            net = m.group(1)
            parts = net.split(".")
            if len(parts) >= 4:
                out["isis"]["area"] = ".".join(parts[:2])
    except Exception:
        pass

    # OSPF area (first ``area X`` line under router ospf).
    try:
        m = re.search(r"router\s+ospf[\s\S]+?area\s+(\S+)", cfg)
        if m:
            out["ospf"]["area"] = m.group(1)
    except Exception:
        pass

    # MPLS / LDP / SR hints.
    try:
        out["mpls"]["enabled"] = "mpls" in cfg.lower()
        out["mpls"]["ldp"] = "ldp" in cfg.lower()
        out["mpls"]["sr"] = "segment-routing" in cfg.lower() or "isis-sr" in cfg.lower()
    except Exception:
        pass

    # Interfaces, bundles, subinterfaces with IPv4 addresses.
    try:
        ifaces: List[Dict[str, Any]] = []
        subs: List[Dict[str, Any]] = []
        bundles: List[str] = []
        cur_iface: Optional[str] = None
        for line in cfg.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            m = re.match(r"^interfaces?\s+(\S+)", stripped)
            if m:
                cur_iface = m.group(1)
                if cur_iface.lower().startswith("bundle"):
                    if cur_iface not in bundles:
                        bundles.append(cur_iface)
                if "." in cur_iface:
                    subs.append({"name": cur_iface, "ip": ""})
                else:
                    ifaces.append({"name": cur_iface, "ip": ""})
                continue
            if cur_iface and "ipv4 address" in stripped.lower():
                m = re.search(r"ipv4\s+address\s+(\S+)", stripped, re.IGNORECASE)
                if m:
                    ip = m.group(1)
                    target = subs if "." in cur_iface else ifaces
                    for entry in target:
                        if entry["name"] == cur_iface:
                            entry["ip"] = ip
                            break
        out["interfaces"] = ifaces[:128]
        out["subinterfaces"] = subs[:128]
        out["bundles"] = bundles[:64]
    except Exception:
        pass

    # Bridge domains.
    try:
        bds: List[str] = []
        for m in re.finditer(r"^\s*bridge-domain\s+(\S+)", cfg, re.MULTILINE):
            name = m.group(1)
            if name and name not in bds:
                bds.append(name)
        out["bridge_domains"] = bds[:64]
    except Exception:
        pass

    # Route distinguishers.
    try:
        rds: List[str] = []
        for m in re.finditer(r"route-distinguisher\s+(\S+)", cfg):
            rd = m.group(1)
            if rd and rd not in rds:
                rds.append(rd)
        out["route_distinguishers"] = rds[:64]
    except Exception:
        pass

    return out


@router.get("/api/topology-generator/device-facts")
def device_facts(
    device_id: str,
    ssh_host: str = "",
    fetch_config: int = 0,
    live: int = 0,
    domain_id: str = "",
    topology_id: str = "",
    request: Request = None,
):
    """Collect compact, generator-friendly facts for a single device.

    ``domain_id`` / ``topology_id`` mirror ``GET /api/devices/{id}/context``
    so per-user system_type overrides scoped to the current topology
    (via ``TopologySync.getActive()``) take precedence over the global
    scaler curated cache.

    Errors are downgraded to partial responses (with ``warnings``) so the
    frontend always learns something, even when SSH is unreachable.
    """
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")

    app_user = _get_request_user(request) if request else "default"
    warnings: List[str] = []
    context_out: Dict[str, Any] = {
        "hostname": "",
        "system_type": "",
        "dnos_version": "",
        "mgmt_ip": "",
        "role": "",
        "as_number": "",
        "router_id": "",
        "loopback0_ip": "",
    }
    config_facts: Optional[Dict[str, Any]] = None
    operational_facts: Dict[str, Any] = {}
    lldp: List[Dict[str, Any]] = []
    ssh_match: Dict[str, Any] = {}

    try:
        ctx = _get_device_context(
            device_id,
            live=bool(live),
            ssh_host=ssh_host or "",
            app_user=app_user,
            domain_id=domain_id or "",
            topology_id=topology_id or "",
        )
        if isinstance(ctx, dict):
            identity = ctx.get("identity") or {}
            context_out["hostname"] = (
                identity.get("hostname")
                or ctx.get("hostname")
                or device_id
            )
            context_out["system_type"] = (
                ctx.get("system_type")
                or identity.get("system_type")
                or ""
            )
            context_out["dnos_version"] = (
                ctx.get("dnos_version")
                or identity.get("dnos_version")
                or ""
            )
            context_out["mgmt_ip"] = (
                identity.get("mgmt_ip")
                or ctx.get("mgmt_ip")
                or ssh_host
                or ""
            )
            context_out["role"] = _safe_role_hint(
                context_out["hostname"], context_out["system_type"]
            )
            context_out["as_number"] = str(ctx.get("as_number") or "")
            context_out["router_id"] = str(ctx.get("router_id") or "")
            context_out["loopback0_ip"] = str(ctx.get("loopback0_ip") or "")
            lldp = _normalize_lldp(ctx.get("lldp"))
    except HTTPException:
        # Bubble out -- middleware handles 401 / 403.
        raise
    except Exception as exc:
        warnings.append(f"context unavailable: {exc}")

    if fetch_config:
        try:
            running = DeviceCommHelper().fetch_running_config(
                device_id, ssh_host or "", app_user=app_user,
            )
            if running:
                summary = _build_config_summary(running)
                # Merge a richer logical-topology view from the raw
                # config so the Live Devices tab can render VRFs /
                # bridge-domains / BGP peers / interfaces directly,
                # without forcing the frontend to re-parse.
                rich = _config_facts_from_running(running) or {}
                base = _config_facts_from_summary(summary or {})
                base.update({k: v for k, v in rich.items() if v not in (None, "", [], {})})
                config_facts = base
                if context_out.get("hostname") in ("", device_id):
                    context_out["hostname"] = (
                        summary.get("system_name")
                        or summary.get("hostname")
                        or context_out["hostname"]
                    )
                if not context_out["loopback0_ip"]:
                    context_out["loopback0_ip"] = config_facts.get("loopback0_ip", "")
                if not context_out["router_id"]:
                    context_out["router_id"] = config_facts.get("router_id", "")
                if not context_out["as_number"] and config_facts.get("asn") is not None:
                    context_out["as_number"] = str(config_facts["asn"])
        except HTTPException:
            raise
        except Exception as exc:
            warnings.append(f"running-config unavailable: {exc}")

    if live:
        commands = [
            "show bgp summary",
            "show ospf neighbors",
            "show route summary",
        ]
        try:
            show_out = DeviceCommHelper().run_show_batch(
                device_id,
                commands,
                ssh_host=ssh_host or "",
                timeout=45,
                app_user=app_user,
            )
            bgp = _parse_bgp_summary(show_out.get("show bgp summary", ""))
            ospf = _parse_ospf_neighbors(show_out.get("show ospf neighbors", ""))
            route_summary = _parse_route_summary(show_out.get("show route summary", ""))
            operational_facts = {
                "bgp_summary": bgp,
                "ospf_neighbors": ospf,
                "route_summary": route_summary,
                "commands": list(show_out.keys()),
            }
            if not context_out["router_id"] and bgp.get("router_id"):
                context_out["router_id"] = bgp["router_id"]
            if not context_out["as_number"] and bgp.get("local_as"):
                context_out["as_number"] = str(bgp["local_as"])
        except HTTPException:
            raise
        except Exception as exc:
            warnings.append(f"operational facts unavailable: {exc}")

    ssh_match = _find_user_ssh_config(
        app_user,
        device_id,
        ssh_host,
        context_out.get("hostname"),
        context_out.get("mgmt_ip"),
    )
    if ssh_match:
        if context_out.get("mgmt_ip") and not ssh_match.get("host"):
            ssh_match["host"] = context_out["mgmt_ip"]
        elif ssh_host and not ssh_match.get("host"):
            ssh_match["host"] = ssh_host

    return {
        "device_id": device_id,
        "context": context_out,
        "config_facts": config_facts,
        "operational_facts": operational_facts,
        "lldp_neighbors": lldp,
        "ssh": ssh_match or None,
        "warnings": warnings,
    }


@router.post("/api/topology-generator/collect-batch")
def collect_batch(body: dict = None, request: Request = None):
    """Bulk variant of ``/device-facts`` for the Live Devices tab.

    Body::
        {
            "devices": [
                {"device_id": str, "ssh_host": str?},
                ...
            ],
            "fetch_config": bool,
            "live": bool,
            "domain_id": str?,
            "topology_id": str?
        }

    Returns ``{"results": [<device_facts payload>, ...], "warnings": [...]}``.
    Errors per device degrade to a partial entry so a single bad device
    never breaks the whole generator run.
    """
    body = body or {}
    items = body.get("devices") or []
    if not isinstance(items, list) or not items:
        raise HTTPException(status_code=400, detail="devices[] required")
    fetch_config = bool(body.get("fetch_config"))
    live = bool(body.get("live"))
    domain_id = str(body.get("domain_id") or "").strip()
    topology_id = str(body.get("topology_id") or "").strip()
    results: List[Dict[str, Any]] = []
    warnings: List[str] = []
    for entry in items:
        if not isinstance(entry, dict):
            continue
        did = (entry.get("device_id") or "").strip()
        ssh_host = (entry.get("ssh_host") or "").strip()
        if not did:
            warnings.append("missing device_id in batch entry")
            continue
        try:
            results.append(
                device_facts(
                    device_id=did,
                    ssh_host=ssh_host,
                    fetch_config=int(fetch_config),
                    live=int(live),
                    domain_id=domain_id,
                    topology_id=topology_id,
                    request=request,
                )
            )
        except HTTPException as exc:
            warnings.append(f"{did}: HTTP {exc.status_code} {exc.detail}")
            results.append({
                "device_id": did,
                "context": {"hostname": did},
                "config_facts": None,
                "lldp_neighbors": [],
                "warnings": [f"HTTP {exc.status_code}"],
            })
        except Exception as exc:
            warnings.append(f"{did}: {exc}")
            results.append({
                "device_id": did,
                "context": {"hostname": did},
                "config_facts": None,
                "lldp_neighbors": [],
                "warnings": [str(exc)],
            })
    return {"results": results, "warnings": warnings}


@router.post("/api/topology-generator/resolve-targets")
def resolve_targets(body: dict = None, request: Request = None):
    """Resolve a list of operator-supplied DUT targets.

    Body::
        {
            "targets": [
                {"deviceId": str, "host": str?, "ssh": {host?,user?,password?}?, "label": str?, "source": str?},
                ...
            ],
            "credentials": {"user": str?, "password": str?}?,
            "discover_unknown": bool?,
            "domain_id": str?,
            "topology_id": str?
        }

    Returns::
        {
            "resolved": [
                {
                    "deviceId": str,
                    "hostname": str,
                    "mgmt_ip": str,
                    "serial": str,
                    "system_type": str,
                    "dnos_version": str,
                    "role": str,
                    "ssh_user": str,
                    "ssh_password": str,
                    "source": str,
                    "resolved_via": str,
                    "warnings": [str]
                },
                ...
            ],
            "watch_ids": [str],
            "warnings": [str]
        }

    Resolution chain reuses ``_resolve_mgmt_ip`` / ``_resolve_device``
    so we stay aligned with the rest of the app. For raw IPs that
    don't appear in inventory yet, we don't SSH-discover synchronously
    (that can take seconds per device); the frontend can call
    ``POST /api/devices/discover`` separately for those if needed.

    The list of returned ``watch_ids`` is what the frontend should
    feed to ``TopologyDeviceEvents.setWatchedDevices(...)`` so the
    per-user watcher registry tracks the operator's DUTs.
    """
    body = body or {}
    targets = body.get("targets") or []
    if not isinstance(targets, list) or not targets:
        raise HTTPException(status_code=400, detail="targets[] required")
    creds = body.get("credentials") or {}
    default_user = (creds.get("user") or "dnroot").strip() or "dnroot"
    default_password = creds.get("password") or "dnroot"
    domain_id = str(body.get("domain_id") or "").strip()
    topology_id = str(body.get("topology_id") or "").strip()
    app_user = _get_request_user(request) if request else "default"

    resolved: List[Dict[str, Any]] = []
    watch_ids: List[str] = []
    warnings: List[str] = []
    seen: set = set()

    for raw in targets:
        if isinstance(raw, str):
            raw = {"deviceId": raw}
        if not isinstance(raw, dict):
            continue
        device_id = (raw.get("deviceId") or raw.get("device_id") or "").strip()
        host = (raw.get("host") or "").strip()
        ssh_in = raw.get("ssh") or {}
        if not host:
            host = (ssh_in.get("host") or "").strip()
        label = (raw.get("label") or device_id or host or "").strip()
        source_in = (raw.get("source") or "").strip() or "manual"
        ssh_user = (ssh_in.get("user") or default_user).strip() or "dnroot"
        ssh_pass = ssh_in.get("password") if ssh_in.get("password") else default_password
        explicit_ssh = bool(ssh_in.get("user") or ssh_in.get("password"))

        if not device_id and host:
            device_id = host

        target_warnings: List[str] = []
        mgmt_ip = ""
        scaler_id = ""
        resolved_via = ""
        try:
            mgmt_ip, scaler_id, resolved_via = _resolve_mgmt_ip(device_id, host)
        except Exception as exc:
            target_warnings.append(f"resolve_mgmt_ip: {exc}")

        hostname = ""
        serial = ""
        try:
            res = _resolve_device(device_id) or {}
            hostname = (res.get("hostname") or res.get("name") or "").strip()
            serial = (res.get("serial") or "").strip()
        except Exception as exc:
            target_warnings.append(f"resolve_device: {exc}")

        if not hostname:
            # Inventory fuzzy-match -- use the scaler ops index entry,
            # which already merges hostname/serial/IP for us.
            try:
                idx = _build_scaler_ops_index() or {}
                key = (mgmt_ip or device_id or "").lower()
                entry = idx.get(key) or idx.get((host or "").lower())
                if entry:
                    hostname = entry.get("hostname") or hostname
                    serial = serial or entry.get("scaler_id") or ""
            except Exception:
                pass

        if not hostname:
            hostname = label or device_id or host or "unknown"

        # Pull a quick context for system_type/role hints (cached).
        sys_type = ""
        dnos_version = ""
        role = ""
        try:
            ctx = _get_device_context(
                device_id or hostname,
                live=False,
                ssh_host=mgmt_ip or host or "",
                app_user=app_user,
                domain_id=domain_id,
                topology_id=topology_id,
            ) or {}
            ident = ctx.get("identity") or {}
            sys_type = ctx.get("system_type") or ident.get("system_type") or ""
            dnos_version = ctx.get("dnos_version") or ident.get("dnos_version") or ""
            if not hostname or hostname == "unknown":
                hostname = (
                    ident.get("hostname")
                    or ctx.get("hostname")
                    or hostname
                )
            role = _safe_role_hint(hostname, sys_type)
        except Exception as exc:
            target_warnings.append(f"context: {exc}")
            role = _safe_role_hint(hostname, sys_type)

        ssh_match = _find_user_ssh_config(app_user, device_id, host, label, hostname, serial, mgmt_ip)
        if ssh_match and not explicit_ssh:
            ssh_user = ssh_match.get("user") or ssh_user
            ssh_pass = ssh_match.get("password") or ssh_pass
        ssh_config = {
            "host": mgmt_ip or host,
            "hostBackup": serial or hostname or "",
            "user": ssh_user,
            "password": ssh_pass,
        }
        if ssh_match:
            ssh_config.update({
                "source": ssh_match.get("source", ""),
                "confidence": ssh_match.get("confidence", ""),
                "matched_key": ssh_match.get("matched_key", ""),
            })

        watch_id = (hostname or device_id or "").strip()
        is_dup = (watch_id.lower() in seen)
        if watch_id and not is_dup:
            seen.add(watch_id.lower())
            watch_ids.append(watch_id)

        resolved.append({
            "deviceId": device_id or hostname,
            "hostname": hostname,
            "mgmt_ip": mgmt_ip or host,
            "serial": serial,
            "system_type": sys_type,
            "dnos_version": dnos_version,
            "role": role,
            "ssh_user": ssh_user,
            "ssh_password": ssh_pass,
            "ssh": ssh_config,
            "source": source_in,
            "resolved_via": resolved_via,
            "duplicate": is_dup,
            "warnings": target_warnings,
        })

    return {
        "resolved": resolved,
        "watch_ids": watch_ids,
        "warnings": warnings,
        "domain_id": domain_id,
        "topology_id": topology_id,
    }


@router.post("/api/topology-generator/correlate")
def correlate_generate_facts(body: dict = None, request: Request = None):
    """Cross-correlate collected Generate facts in a per-user temp SQLite DB.

    The database file is always removed after the response is built
    (including on errors). Input mirrors the frontend ``facts`` model
    produced by ``adapterLive`` / canvas adapters.
    """
    if correlate_topology_facts is None:
        raise HTTPException(status_code=503, detail="correlation engine unavailable")
    app_user = _get_request_user(request) if request else "default"
    body = body or {}
    facts = body.get("facts") or {}
    options = body.get("options") or {}
    # Echo scope for clients / future audit (no server-side persistence).
    options = dict(options)
    options.setdefault("domain_id", body.get("domain_id") or "")
    options.setdefault("topology_id", body.get("topology_id") or "")
    result = correlate_topology_facts(facts, app_user, options)
    return result


@router.post("/api/topology-generator/enrich-link-tables")
def enrich_generate_link_tables(body: dict = None, request: Request = None):
    """Return per-link auto-fill patches for current canvas link tables.

    The route is stateless and scoped by the authenticated user plus the
    caller-provided domain/topology ids. It never mutates saved topologies;
    the frontend applies returned patches only to empty/auto-owned fields.
    """
    if enrich_canvas_link_tables is None:
        raise HTTPException(status_code=503, detail="link-table enrichment unavailable")
    body = body or {}
    result = enrich_canvas_link_tables(body)
    result["domain_id"] = body.get("domain_id") or ""
    result["topology_id"] = body.get("topology_id") or ""
    result["user"] = _get_request_user(request) if request else "default"
    return result


@router.post("/api/topology-generator/save-via-mcp")
def save_generated_topology_via_mcp(body: dict = None, request: Request = None):
    """Validate and save a generated topology through the Topology MCP dispatcher.

    The legacy generator used ``/api/sections/<id>/save`` directly, which could
    leave the canonical MCP DB and the current dropdown mirror out of sync. This
    route keeps the generator on the same per-user MCP save path as `/TOPOLOGY`:
    validate first, save/create in the DB, and let MCP mirror the legacy section
    file used by the current UI.
    """
    if user_store is None:
        raise HTTPException(status_code=503, detail="user store unavailable")
    app_user = _get_request_user(request) if request else "default"
    if not user_store.has_role_or_higher(app_user, "engineer"):
        raise HTTPException(status_code=403, detail="engineer role required")

    body = body or {}
    state = body.get("state_json") or body.get("topology") or {}
    if not isinstance(state, dict):
        raise HTTPException(status_code=400, detail="state_json/topology object required")

    name = str(body.get("name") or (state.get("metadata") or {}).get("name") or "Generated Topology").strip()
    section_id = str(body.get("section_id") or body.get("legacy_section_id") or "").strip()
    requested_domain_id = str(body.get("domain_id") or "").strip()
    domain_name = str(body.get("domain_name") or "").strip()
    topology_id = str(body.get("topology_id") or "").strip()
    avoid_duplicate = bool(body.get("avoid_duplicate", True))

    domain = _resolve_generator_mcp_domain(app_user, section_id, requested_domain_id, domain_name)
    domain_id = str(domain.get("id") or requested_domain_id or "").strip()
    if not domain_id:
        raise HTTPException(status_code=400, detail="could not resolve topology MCP domain")

    save_name = name
    if avoid_duplicate and not topology_id:
        save_name = _unique_generated_topology_name(app_user, domain_id, name)

    state = dict(state)
    metadata = dict(state.get("metadata") or {})
    metadata["name"] = save_name
    metadata["generatedSavePath"] = "topology-generator-mcp"
    metadata["generatedPlacement"] = {
        "sectionId": section_id,
        "domainId": domain_id,
        "domainName": domain.get("name") or domain_name or domain_id,
        "placedAt": int(time.time()),
    }
    state["metadata"] = metadata

    validation = _dispatch_topology_mcp(app_user, "topology_validate_topology", {"state_json": state})
    if not validation.get("valid", False):
        raise HTTPException(status_code=400, detail={
            "message": "generated topology failed validation",
            "issues": validation.get("issues") or [],
        })

    if topology_id:
        saved = _dispatch_topology_mcp(app_user, "topology_save_topology", {
            "domain_id": domain_id,
            "topology_id": topology_id,
            "name": save_name,
            "state_json": state,
        })
    else:
        saved = _dispatch_topology_mcp(app_user, "topology_create_topology", {
            "domain_id": domain_id,
            "name": save_name,
            "state_json": state,
        })

    topology = saved.get("topology") or {}
    real_topology_id = str(topology.get("id") or topology_id or "").strip()
    if real_topology_id:
        try:
            _dispatch_topology_mcp(app_user, "topology_repair_legacy_visibility", {
                "domain_id": domain_id,
                "topology_id": real_topology_id,
            })
        except HTTPException:
            raise
        except Exception:
            pass

    return {
        "ok": True,
        "name": topology.get("name") or save_name,
        "domain_id": domain_id,
        "domain_name": domain.get("name") or domain_name or domain_id,
        "topology_id": real_topology_id,
        "filename": topology.get("legacy_filename") or "",
        "legacy_section_id": topology.get("legacy_section_id") or section_id,
        "validation": validation.get("summary") or {},
    }


@router.post("/api/topology-generator/learning/match")
def match_learning(body: dict = None, request: Request = None):
    """Return the best per-user Generate learning hints for a signature."""
    app_user = _get_request_user(request) if request else "default"
    body = body or {}
    signature = body.get("signature") or {}
    key = _signature_key(signature)
    data = _read_learning(app_user)
    entries = data.get("entries") or {}
    if key and key in entries:
        entry = entries[key]
        return {
            "matched": True,
            "match_key": key,
            "similarity": 1.0,
            "hints": entry.get("hints") or {},
            "entry": entry,
        }
    best_key = ""
    best_entry: Dict[str, Any] = {}
    best_score = 0.0
    for entry_key, entry in entries.items():
        score = _signature_similarity(signature, entry.get("signature") or {})
        if score > best_score:
            best_score = score
            best_key = entry_key
            best_entry = entry
    if best_entry and best_score >= 0.68:
        return {
            "matched": True,
            "match_key": best_key,
            "similarity": best_score,
            "hints": best_entry.get("hints") or {},
            "entry": best_entry,
        }
    return {"matched": False, "hints": {}, "similarity": best_score}


@router.post("/api/topology-generator/learning")
def save_learning(body: dict = None, request: Request = None):
    """Save accepted generated layout/style hints in per-user storage."""
    app_user = _get_request_user(request) if request else "default"
    body = body or {}
    signature = body.get("signature") or {}
    hints = body.get("hints") or {}
    key = _signature_key(signature)
    if not key:
        raise HTTPException(status_code=400, detail="signature required")
    if not isinstance(hints, dict):
        raise HTTPException(status_code=400, detail="hints object required")
    data = _read_learning(app_user)
    entries = data.setdefault("entries", {})
    previous = entries.get(key) or {}
    count = int(previous.get("accepted_count") or 0) + 1
    entries[key] = {
        "signature": signature,
        "hints": hints,
        "accepted_count": count,
        "last_reason": str(body.get("reason") or "accepted-generated-topology")[:120],
        "updated_at": int(time.time()),
    }
    _write_learning(app_user, data)
    return {"ok": True, "key": key, "accepted_count": count}


@router.post("/api/topology-generator/learning/reset")
def reset_learning(body: dict = None, request: Request = None):
    """Reset one learned signature or all Generate learning for this user."""
    app_user = _get_request_user(request) if request else "default"
    body = body or {}
    key = _signature_key(body.get("signature") or {})
    data = _read_learning(app_user)
    if key:
        removed = key in data.get("entries", {})
        data.get("entries", {}).pop(key, None)
    else:
        removed = bool(data.get("entries"))
        data["entries"] = {}
    _write_learning(app_user, data)
    return {"ok": True, "removed": removed}
