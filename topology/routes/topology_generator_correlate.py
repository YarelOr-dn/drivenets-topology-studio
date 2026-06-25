"""Per-generation SQLite correlation for Topology Generate.

Builds a temporary per-user database, cross-references devices (BGP, LLDP,
VRF/BD/RT), emits symmetric layout hints, then deletes the DB file.
"""
from __future__ import annotations

import copy
import json
import math
import os
import re
import sqlite3
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

try:
    from api.auth.user_store import user_store
except Exception:  # pragma: no cover
    user_store = None

try:
    from telemetry.lldp_correlator import collect_lldp_edges_from_db
except Exception:  # pragma: no cover
    collect_lldp_edges_from_db = None

_IP_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
_AF_TOKEN_MAP = {
    "ipv4 unicast": "ipv4-unicast",
    "ipv4-unicast": "ipv4-unicast",
    "ipv4 vpn": "ipv4-vpn",
    "ipv4-vpn": "ipv4-vpn",
    "vpnv4": "ipv4-vpn",
    "ipv4 flowspec": "ipv4-flowspec",
    "ipv4-flowspec": "ipv4-flowspec",
    "ipv4 flowspec-vpn": "ipv4-flowspec-vpn",
    "ipv4-flowspec-vpn": "ipv4-flowspec-vpn",
    "ipv4 route target constrains": "ipv4-rt-constrain",
    "ipv4 route target constraints": "ipv4-rt-constrain",
    "ipv4-rt-constrain": "ipv4-rt-constrain",
    "rt-constrain": "ipv4-rt-constrain",
    "ipv6 unicast": "ipv6-unicast",
    "ipv6-unicast": "ipv6-unicast",
    "ipv6 vpn": "ipv6-vpn",
    "ipv6-vpn": "ipv6-vpn",
    "vpnv6": "ipv6-vpn",
    "ipv6 flowspec": "ipv6-flowspec",
    "ipv6-flowspec": "ipv6-flowspec",
    "l2vpn vpls": "l2vpn-vpls",
    "l2vpn-vpls": "l2vpn-vpls",
    "vpls": "l2vpn-vpls",
    "l2vpn evpn": "l2vpn-evpn",
    "l2vpn-evpn": "l2vpn-evpn",
    "evpn": "l2vpn-evpn",
}
_AF_ORDER = [
    "ipv4-unicast",
    "ipv4-vpn",
    "ipv4-flowspec",
    "ipv4-flowspec-vpn",
    "ipv4-rt-constrain",
    "ipv6-unicast",
    "ipv6-vpn",
    "ipv6-flowspec",
    "l2vpn-vpls",
    "l2vpn-evpn",
]


def _norm_name_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _load_known_topology_packs() -> List[Dict[str, Any]]:
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "correlations",
        "known_topologies.json",
    )
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        packs = data.get("topologies") if isinstance(data, dict) else []
        return [p for p in packs if isinstance(p, dict)]
    except Exception:
        return []


def _match_known_topology_pack(
    devices: Dict[str, Dict[str, Any]]
) -> Tuple[Optional[Dict[str, Any]], Dict[str, str]]:
    """Return a canonical knowledge pack and canonical-id -> fact-id map."""
    if not devices:
        return None, {}
    fact_by_name: Dict[str, str] = {}
    for fid, dev in devices.items():
        names = [dev.get("hostname"), dev.get("name"), dev.get("mgmtIp"), dev.get("ip")]
        cfg = dev.get("config") if isinstance(dev.get("config"), dict) else {}
        names.extend([cfg.get("router_id"), cfg.get("loopback0_ip")])
        for name in names:
            key = _norm_name_key(name)
            if key:
                fact_by_name[key] = fid

    best_pack: Optional[Dict[str, Any]] = None
    best_map: Dict[str, str] = {}
    for pack in _load_known_topology_packs():
        candidate: Dict[str, str] = {}
        for cdev in pack.get("devices") or []:
            if not isinstance(cdev, dict):
                continue
            canonical_id = str(cdev.get("id") or "").strip()
            aliases = [canonical_id, cdev.get("hostname"), *(cdev.get("aliases") or [])]
            for alias in aliases:
                fid = fact_by_name.get(_norm_name_key(alias))
                if fid:
                    candidate[canonical_id] = fid
                    break
        if len(candidate) > len(best_map):
            best_pack, best_map = pack, candidate

    if best_pack and len(best_map) >= max(2, len(best_pack.get("devices") or [])):
        return best_pack, best_map
    return None, {}


def _services_from_known_pack(
    pack: Dict[str, Any],
    canonical_to_fact: Dict[str, str],
    devices: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    services: List[Dict[str, Any]] = []
    for svc in pack.get("services") or []:
        if not isinstance(svc, dict):
            continue
        members = [
            canonical_to_fact[mid]
            for mid in (svc.get("members") or [])
            if mid in canonical_to_fact
        ]
        if len(set(members)) < 2:
            continue
        kind = str(svc.get("kind") or "service").lower()
        name = str(svc.get("name") or kind.upper())
        color = "#f39c12" if kind == "evpn" else ("#1abc9c" if kind == "vrf" else "#ff5e1f")
        services.append(
            _apply_scene_meta({
                "id": f"known:{kind}:{name}",
                "kind": kind,
                "name": name,
                "label": name if kind == "evpn" else f"{kind.upper()} {name}",
                "members": list(dict.fromkeys(members)),
                "memberNames": [
                    str(devices.get(mid, {}).get("hostname") or mid)
                    for mid in list(dict.fromkeys(members))
                ],
                "routeTargets": list(svc.get("route_targets") or []),
                "rds": dict(svc.get("rds") or {}),
                "outer_vlan": svc.get("outer_vlan") or {},
                "inner_vlan": svc.get("inner_vlan") or "",
                "mode": svc.get("mode") or "",
                "color": color,
                "layer": "service",
                "note": svc.get("note") or "verified known service correlation",
                "_source": f"known-topology:{pack.get('id') or ''}",
            }, layer="service", source=f"known-topology:{pack.get('id') or ''}",
                fallback_confidence="verified",
                evidence=[name, *(svc.get("route_targets") or []), *(svc.get("rds") or {}).values()],
                priority=85)
        )
    return services


def _scene_confidence(source: str, fallback: str = "correlated") -> str:
    text = str(source or "").lower()
    if any(token in text for token in ("known-topology", "verified", "lldp", "device-facts", "live")):
        return "verified"
    if any(token in text for token in ("sqlite", "correlat", "bgp", "service", "route-target", "rt")):
        return "correlated"
    if any(token in text for token in ("inferred", "alias", "fallback", "perimeter")):
        return "inferred"
    if any(token in text for token in ("missing", "unmatched", "failed", "skipped")):
        return "missing"
    return fallback


def _apply_scene_meta(
    row: Dict[str, Any],
    *,
    layer: str,
    source: str,
    fallback_confidence: str = "correlated",
    evidence: Optional[List[str]] = None,
    priority: int = 50,
) -> Dict[str, Any]:
    row["layer"] = row.get("layer") or layer
    row["_sceneLayer"] = layer
    row["_confidenceClass"] = row.get("_confidenceClass") or _scene_confidence(source, fallback_confidence)
    row["_source"] = row.get("_source") or source
    row["_evidence"] = list(dict.fromkeys([str(x) for x in (evidence or []) if x]))
    row["_displayPriority"] = row.get("_displayPriority", priority)
    return row


def _norm_ip(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip().split("/")[0].strip().lower()
    return s if _IP_RE.match(s) else ""


def _norm_host(value: Any) -> str:
    return str(value or "").strip().lower()


def _normalize_af_tokens(value: Any) -> List[str]:
    if value is None:
        return []
    raw: List[Any]
    if isinstance(value, list):
        raw = value
    elif isinstance(value, (tuple, set)):
        raw = list(value)
    else:
        raw = re.split(r"[,;/|]+", str(value))
    out: List[str] = []
    for item in raw:
        key = re.sub(r"\s+", " ", str(item or "").strip().lower())
        if not key:
            continue
        token = _AF_TOKEN_MAP.get(key) or _AF_TOKEN_MAP.get(key.replace("_", "-"))
        if not token and "-" in key:
            token = _AF_TOKEN_MAP.get(key.replace("-", " "))
        if token and token not in out:
            out.append(token)
    return sorted(out, key=lambda x: _AF_ORDER.index(x) if x in _AF_ORDER else 999)


def _peer_address_families(cfg: Dict[str, Any], peer_ip: str = "") -> List[str]:
    peer_n = _norm_ip(peer_ip)
    families: List[str] = []
    for p in cfg.get("bgp_peers") or []:
        if not isinstance(p, dict):
            continue
        if peer_n and _norm_ip(p.get("peer")) != peer_n:
            continue
        for key in ("address_families", "addressFamilies", "afi_safi", "afiSafi", "families"):
            for af in _normalize_af_tokens(p.get(key)):
                if af not in families:
                    families.append(af)
        if peer_n:
            break
    return sorted(families, key=lambda x: _AF_ORDER.index(x) if x in _AF_ORDER else 999)


def _inferred_rid_aliases_from_name(value: Any) -> List[str]:
    """Best-effort lab aliasing for preserved DUTs with failed auth.

    Some generated runs keep a PE/RR because it has valid app SSH evidence,
    but the live config fetch can still fail. In the DriveNets lab naming
    scheme PE-4/RR-2 style names commonly use N.N.N.N loopback/router-id.
    Adding that as a low-risk address alias lets other devices' BGP peers
    correlate the preserved node instead of leaving it isolated.
    """
    name = str(value or "").strip().lower()
    m = re.search(r"(?:^|[_-])(pe|rr|p|ce)[_-]?(\d+)(?:\b|[_-])", name)
    if not m:
        return []
    n = int(m.group(2))
    if n <= 0 or n > 254:
        return []
    return [f"{n}.{n}.{n}.{n}"]


def _temp_db_path(username: str) -> str:
    if user_store is None:
        raise RuntimeError("user_store unavailable")
    run_id = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:12]}"
    path = user_store.user_data_path(username, f"tmp/topology_generator/correlate_{run_id}.db")
    return str(path)


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;
        PRAGMA busy_timeout=5000;
        CREATE TABLE devices (
            id TEXT PRIMARY KEY,
            hostname TEXT,
            role TEXT,
            tier INTEGER,
            json TEXT NOT NULL
        );
        CREATE TABLE addresses (
            device_id TEXT NOT NULL,
            addr TEXT NOT NULL,
            PRIMARY KEY (device_id, addr)
        );
        CREATE TABLE bgp_peers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            peer TEXT NOT NULL,
            remote_as TEXT,
            local_as TEXT,
            source TEXT
        );
        CREATE TABLE lldp_rows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            peer_hostname TEXT,
            local_interface TEXT,
            peer_interface TEXT
        );
        CREATE TABLE service_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            name TEXT NOT NULL
        );
        CREATE TABLE correlations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            device_a TEXT,
            device_b TEXT,
            detail TEXT,
            score REAL,
            evidence TEXT
        );
        """
    )


def _populate(conn: sqlite3.Connection, devices: List[Dict[str, Any]]) -> None:
    cur = conn.cursor()
    for d in devices:
        did = str(d.get("id") or "")
        if not did:
            continue
        hostname = str(d.get("hostname") or d.get("label") or "")
        role = str(d.get("role") or "")
        tier = int(d.get("tier") or 1)
        cur.execute(
            "INSERT INTO devices (id, hostname, role, tier, json) VALUES (?,?,?,?,?)",
            (did, hostname, role, tier, json.dumps(d, separators=(",", ":"))),
        )
        cfg = d.get("config") or {}
        addrs: List[str] = []
        for key in ("mgmtIp", "ip", "_loopback0", "_routerId"):
            v = _norm_ip(d.get(key))
            if v:
                addrs.append(v)
        for alias_source in (d.get("hostname"), d.get("label"), d.get("name")):
            addrs.extend(_inferred_rid_aliases_from_name(alias_source))
        v = _norm_ip(cfg.get("loopback0_ip"))
        if v:
            addrs.append(v)
        v = _norm_ip(cfg.get("router_id"))
        if v:
            addrs.append(v)
        for lst in (cfg.get("interfaces") or [], cfg.get("subinterfaces") or []):
            if isinstance(lst, list):
                for row in lst:
                    if isinstance(row, dict):
                        ip = _norm_ip(row.get("ip"))
                        if ip:
                            addrs.append(ip)
        for a in sorted(set(addrs)):
            cur.execute(
                "INSERT OR IGNORE INTO addresses (device_id, addr) VALUES (?,?)",
                (did, a),
            )
        for p in cfg.get("bgp_peers") or []:
            if not isinstance(p, dict):
                continue
            peer = str(p.get("peer") or "").strip()
            if not peer:
                continue
            cur.execute(
                """INSERT INTO bgp_peers (device_id, peer, remote_as, local_as, source)
                   VALUES (?,?,?,?,?)""",
                (
                    did,
                    peer,
                    str(p.get("remote_as") or ""),
                    str(p.get("local_as") or cfg.get("asn") or ""),
                    str(p.get("source") or "config"),
                ),
            )
        for n in d.get("_lldp") or []:
            if not isinstance(n, dict):
                continue
            ph = str(n.get("peer_hostname") or "").strip()
            if not ph:
                continue
            cur.execute(
                """INSERT INTO lldp_rows (device_id, peer_hostname, local_interface, peer_interface)
                   VALUES (?,?,?,?)""",
                (
                    did,
                    ph,
                    str(n.get("local_interface") or ""),
                    str(n.get("peer_interface") or ""),
                ),
            )
        for vrf in cfg.get("vrfs") or []:
            name = str(vrf).strip()
            if name:
                cur.execute(
                    "INSERT INTO service_members (device_id, kind, name) VALUES (?,?,?)",
                    (did, "vrf", name),
                )
        for bd in cfg.get("bridge_domains") or []:
            name = str(bd).strip()
            if name:
                cur.execute(
                    "INSERT INTO service_members (device_id, kind, name) VALUES (?,?,?)",
                    (did, "bd", name),
                )
        for rt in cfg.get("route_targets") or []:
            name = str(rt).strip()
            if name:
                cur.execute(
                    "INSERT INTO service_members (device_id, kind, name) VALUES (?,?,?)",
                    (did, "rt", name),
                )
    conn.commit()


def _collect_bgp_edges(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    edges: List[Dict[str, Any]] = []
    rows = list(
        conn.execute(
            "SELECT id, device_id, peer, remote_as, local_as, source FROM bgp_peers"
        ).fetchall()
    )
    for row in rows:
        _pid, dev_a, peer, remote_as, local_as, source = row
        peer_n = _norm_ip(peer)
        dev_b = ""
        evidence = f"bgp peer {peer}"
        if peer_n:
            r = conn.execute(
                "SELECT device_id FROM addresses WHERE addr = ? AND device_id != ? LIMIT 1",
                (peer_n, dev_a),
            ).fetchone()
            if r:
                dev_b = r[0]
                evidence = f"BGP peer IP {peer} matched device address index"
        if not dev_b:
            r = conn.execute(
                "SELECT id FROM devices WHERE lower(hostname) = ? AND id != ? LIMIT 1",
                (_norm_host(peer), dev_a),
            ).fetchone()
            if r:
                dev_b = r[0]
                evidence = f"BGP peer hostname {peer} matched DUT"
        if not dev_b:
            continue
        la = local_as or ""
        ra = remote_as or ""
        is_ext = bool(la and ra and str(la) != str(ra))
        edges.append(
            {
                "from": dev_a,
                "to": dev_b,
                "is_external": is_ext,
                "local_as": la,
                "remote_as": ra,
                "peer": peer,
                "evidence": evidence,
                "source": source,
            }
        )
    return edges


def _collect_lldp_edges(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    if collect_lldp_edges_from_db:
        return collect_lldp_edges_from_db(conn)
    cur = conn.cursor()
    out: List[Dict[str, Any]] = []
    cur.execute(
        "SELECT l.device_id, l.peer_hostname, l.local_interface, l.peer_interface, d2.id "
        "FROM lldp_rows l JOIN devices d2 ON lower(d2.hostname) = lower(l.peer_hostname) "
        "WHERE l.device_id != d2.id"
    )
    for dev_a, peer_h, lif, pif, dev_b in cur.fetchall():
        out.append(
            {
                "from": dev_a,
                "to": dev_b,
                "peer_hostname": peer_h,
                "local_interface": lif,
                "peer_interface": pif,
                "evidence": f"LLDP {peer_h}",
            }
        )
    return out


def _collect_service_groups(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    groups: List[Dict[str, Any]] = []
    cur.execute(
        """
        SELECT kind, name, group_concat(device_id, '|') AS members
        FROM service_members
        GROUP BY kind, name
        HAVING COUNT(DISTINCT device_id) >= 2
        """
    )
    for kind, name, mem_csv in cur.fetchall():
        members = [m for m in str(mem_csv).split("|") if m]
        groups.append({"kind": kind, "name": name, "members": members})
    return groups


def _split_interface_name(name: Any) -> Tuple[str, str, str]:
    """Return (physical_or_parent, subinterface, vlan_hint)."""
    raw = str(name or "").strip()
    if not raw:
        return "", "", ""
    if "." not in raw:
        return raw, "", ""
    parent, suffix = raw.split(".", 1)
    vlan = suffix.split(".")[-1] if suffix else ""
    return parent, raw, vlan


def _interface_records_from_device(device: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize interface/subinterface facts from Generate or DeviceMonitor context."""
    cfg = device.get("config") or device.get("_monitorContext") or device.get("context") or {}
    if "config" in cfg and isinstance(cfg.get("config"), dict):
        cfg = cfg.get("config") or {}
    ctx_ifaces = cfg.get("interfaces") if isinstance(cfg.get("interfaces"), dict) else {}
    records: List[Dict[str, Any]] = []

    def add_record(row: Dict[str, Any], kind: str = "") -> None:
        if not isinstance(row, dict):
            return
        name = str(row.get("name") or row.get("interface") or row.get("id") or "").strip()
        if not name:
            return
        parent, subif, vlan = _split_interface_name(name)
        rec = {
            "name": name,
            "kind": kind or row.get("kind") or ("subinterface" if subif else "physical"),
            "parent": row.get("parent") or parent,
            "subinterface": row.get("subinterface") or subif,
            "vlan": str(row.get("vlan") or row.get("outer_vlan") or vlan or ""),
            "inner_vlan": str(row.get("inner_vlan") or ""),
            "ip": str(row.get("ip") or row.get("address") or row.get("ipv4") or ""),
            "vrf": str(row.get("vrf") or ""),
            "bd": str(row.get("bd") or row.get("bridge_domain") or ""),
            "bundle": str(row.get("bundle") or row.get("bundle_id") or ""),
            "evidence": str(row.get("evidence") or "config"),
        }
        records.append(rec)

    for row in cfg.get("interfaces") or []:
        add_record(row, "physical")
    for row in cfg.get("subinterfaces") or []:
        add_record(row, "subinterface")
    if isinstance(ctx_ifaces, dict):
        for row in ctx_ifaces.get("physical") or []:
            add_record(row, "physical")
        for row in ctx_ifaces.get("subinterface") or []:
            add_record(row, "subinterface")
        for row in ctx_ifaces.get("bundle") or []:
            add_record(row, "bundle")
    return records


def _device_key_map(devices: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for d in devices:
        for key in (
            d.get("id"),
            d.get("hostname"),
            d.get("label"),
            d.get("name"),
            d.get("deviceSerial"),
            d.get("serial"),
        ):
            k = str(key or "").strip().lower()
            if k:
                out[k] = d
    return out


def _find_interface_record(device: Dict[str, Any], interface_name: Any = "", ip: Any = "") -> Dict[str, Any]:
    records = _interface_records_from_device(device)
    iface = str(interface_name or "").strip().lower()
    ip_norm = _norm_ip(ip)
    if iface:
        for rec in records:
            if str(rec.get("name") or "").lower() == iface:
                return rec
        for rec in records:
            if str(rec.get("parent") or "").lower() == iface:
                return rec
    if ip_norm:
        for rec in records:
            if _norm_ip(rec.get("ip")) == ip_norm:
                return rec
    return {}


def _endpoint_link_fields(device: Dict[str, Any], interface_name: str = "", peer_ip: str = "") -> Dict[str, Any]:
    cfg = device.get("config") or device.get("_monitorContext") or device.get("context") or {}
    rec = _find_interface_record(device, interface_name, peer_ip)
    iface_name = interface_name or rec.get("name") or ""
    parent, subif, vlan_hint = _split_interface_name(iface_name)
    fields = {
        "interface": iface_name,
        "physicalInterface": rec.get("parent") or parent or iface_name,
        "subInterface": rec.get("subinterface") or subif,
        "ipAddress": rec.get("ip") or "",
        "vlanId": rec.get("vlan") or vlan_hint,
        "innerVlan": rec.get("inner_vlan") or "",
        "bundle": rec.get("bundle") or (parent if str(parent).lower().startswith("bundle") else ""),
        "vrf": rec.get("vrf") or "",
        "bridgeDomain": rec.get("bd") or "",
        "routerId": cfg.get("router_id") or device.get("_routerId") or "",
        "loopback": cfg.get("loopback0_ip") or device.get("_loopback0") or "",
        "asn": cfg.get("asn") or device.get("_asn") or "",
        "evidence": rec.get("evidence") or ("lldp" if interface_name else "config"),
    }
    return fields


def _build_link_details(
    device_a: Dict[str, Any],
    device_b: Dict[str, Any],
    interface_a: str = "",
    interface_b: str = "",
    protocol: str = "",
    link_type: str = "",
    layer: str = "",
    peer_ip: str = "",
    matched_by: str = "",
) -> Dict[str, Any]:
    cfg_a = device_a.get("config") or {}
    cfg_b = device_b.get("config") or {}
    a = _endpoint_link_fields(device_a, interface_a)
    b = _endpoint_link_fields(device_b, interface_b, peer_ip if link_type in ("iBGP", "eBGP") else "")
    afis: List[str] = []
    for af in _peer_address_families(cfg_a, peer_ip):
        if af not in afis:
            afis.append(af)
    reverse_peer = str(cfg_a.get("router_id") or cfg_a.get("loopback0_ip") or "").split("/")[0]
    for af in _peer_address_families(cfg_b, reverse_peer):
        if af not in afis:
            afis.append(af)
    if (cfg_a.get("evpn") or {}).get("enabled") or (cfg_b.get("evpn") or {}).get("enabled") or cfg_a.get("route_targets") or cfg_b.get("route_targets"):
        if "l2vpn-evpn" not in afis:
            afis.append("l2vpn-evpn")
    if cfg_a.get("vrfs") or cfg_b.get("vrfs"):
        if "ipv4-vpn" not in afis:
            afis.append("ipv4-vpn")
        if "ipv6-vpn" not in afis:
            afis.append("ipv6-vpn")
    details = {
        "interfaceA": a["interface"],
        "interfaceB": b["interface"],
        "physicalInterfaceA": a["physicalInterface"],
        "physicalInterfaceB": b["physicalInterface"],
        "subInterfaceA": a["subInterface"],
        "subInterfaceB": b["subInterface"],
        "ipAddressA": a["ipAddress"],
        "ipAddressB": b["ipAddress"],
        "vlanIdA": a["vlanId"],
        "vlanIdB": b["vlanId"],
        "innerVlanA": a["innerVlan"],
        "innerVlanB": b["innerVlan"],
        "bundleA": a["bundle"],
        "bundleB": b["bundle"],
        "vrfA": a["vrf"],
        "vrfB": b["vrf"],
        "bdNameA": a["bridgeDomain"],
        "bdNameB": b["bridgeDomain"],
        "routerIdA": a["routerId"],
        "routerIdB": b["routerId"],
        "loopbackA": a["loopback"],
        "loopbackB": b["loopback"],
        "asnA": str(a["asn"] or ""),
        "asnB": str(b["asn"] or ""),
        "peerIp": peer_ip,
        "protocol": protocol,
        "linkType": link_type,
        "layer": layer,
        "matchedBy": matched_by or ("lldp" if layer == "physical" else "config"),
        "addressFamilies": afis,
        "discoveryEvidence": [
            {
                "source": matched_by or ("lldp" if layer == "physical" else "config"),
                "protocol": protocol,
                "interfaceA": a["interface"],
                "interfaceB": b["interface"],
                "ipAddressA": a["ipAddress"],
                "ipAddressB": b["ipAddress"],
                "routerIdA": a["routerId"],
                "routerIdB": b["routerId"],
            }
        ],
    }
    return {k: v for k, v in details.items() if v not in ("", None, [])}


def _enrich_fact_link(link: Dict[str, Any], devices_by_id: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    a = devices_by_id.get(str(link.get("fromDevice") or ""))
    b = devices_by_id.get(str(link.get("toDevice") or ""))
    if not a or not b:
        return link
    details = _build_link_details(
        a,
        b,
        str(link.get("fromInterface") or ""),
        str(link.get("toInterface") or ""),
        str(link.get("protocol") or ""),
        str(link.get("linkType") or ""),
        str(link.get("layer") or ""),
        str((link.get("extra") or {}).get("peerIp") or link.get("peerIp") or ""),
        str(link.get("matchedBy") or link.get("source") or ""),
    )
    merged = dict(link.get("linkDetails") or {})
    merged.update(details)
    link["linkDetails"] = merged
    link["linkTable"] = {
        "device1Interface": details.get("interfaceA", ""),
        "device2Interface": details.get("interfaceB", ""),
        "device1IpAddress": details.get("ipAddressA", ""),
        "device2IpAddress": details.get("ipAddressB", ""),
        "device1VlanId": details.get("vlanIdA", ""),
        "device2VlanId": details.get("vlanIdB", ""),
        "device1OuterTag": details.get("vlanIdA", ""),
        "device2OuterTag": details.get("vlanIdB", ""),
        "device1InnerTag": details.get("innerVlanA", ""),
        "device2InnerTag": details.get("innerVlanB", ""),
    }
    source = str(link.get("matchedBy") or link.get("source") or link.get("_source") or "")
    layer = str(link.get("layer") or "physical")
    evidence = [
        str(link.get("protocol") or ""),
        str(link.get("linkType") or ""),
        details.get("interfaceA", ""),
        details.get("interfaceB", ""),
        details.get("routerIdA", ""),
        details.get("routerIdB", ""),
        details.get("peerIp", ""),
    ]
    _apply_scene_meta(
        link,
        layer=layer,
        source=source or ("physical-link" if layer == "physical" else "logical-correlation"),
        fallback_confidence="verified" if layer == "physical" else "correlated",
        evidence=evidence,
        priority=90 if layer == "physical" else 80,
    )
    return link


def enrich_canvas_link_tables(body: Dict[str, Any]) -> Dict[str, Any]:
    """Return safe, per-link link-table patches for current canvas objects."""
    devices = body.get("devices") or []
    links = body.get("links") or []
    if not isinstance(devices, list) or not isinstance(links, list):
        return {"ok": False, "patches": [], "warnings": ["devices[] and links[] required"]}
    dev_map = _device_key_map(devices)
    patches: List[Dict[str, Any]] = []
    warnings: List[str] = []
    for link in links:
        if not isinstance(link, dict):
            continue
        link_id = str(link.get("id") or "")
        da_key = str(link.get("device1") or link.get("fromDevice") or "").strip().lower()
        db_key = str(link.get("device2") or link.get("toDevice") or "").strip().lower()
        da = dev_map.get(da_key)
        db = dev_map.get(db_key)
        if not da or not db:
            warnings.append(f"{link_id or 'link'}: endpoint device not found")
            continue
        if_a = str(link.get("device1Interface") or link.get("interface1") or "")
        if_b = str(link.get("device2Interface") or link.get("interface2") or "")
        matched_by = "existing-link"

        # LLDP can fill missing endpoint interfaces when monitor cache has it.
        if not (if_a and if_b):
            lldp = (da.get("_lldpData") or {}).get("neighbors") or da.get("lldp") or []
            db_name = str(db.get("label") or db.get("hostname") or db.get("name") or "").strip().lower()
            for n in lldp:
                nbr = str(n.get("neighbor") or n.get("peer_hostname") or n.get("remote_device") or "").strip().lower()
                if nbr and db_name and nbr == db_name:
                    if_a = if_a or str(n.get("interface") or n.get("local_interface") or "")
                    if_b = if_b or str(n.get("remote_port") or n.get("peer_interface") or n.get("remote_interface") or "")
                    matched_by = "lldp-monitor"
                    break

        details = _build_link_details(
            da,
            db,
            if_a,
            if_b,
            str(link.get("protocol") or link.get("linkType") or ""),
            str(link.get("linkType") or ""),
            str(link.get("layer") or "physical"),
            str(link.get("peerIp") or ""),
            matched_by,
        )
        fields = {
            "device1Interface": details.get("interfaceA", ""),
            "device2Interface": details.get("interfaceB", ""),
            "interface1": details.get("interfaceA", ""),
            "interface2": details.get("interfaceB", ""),
            "device1IpAddress": details.get("ipAddressA", ""),
            "device2IpAddress": details.get("ipAddressB", ""),
            "device1VlanId": details.get("vlanIdA", ""),
            "device2VlanId": details.get("vlanIdB", ""),
            "device1OuterTag": details.get("vlanIdA", ""),
            "device2OuterTag": details.get("vlanIdB", ""),
            "device1InnerTag": details.get("innerVlanA", ""),
            "device2InnerTag": details.get("innerVlanB", ""),
        }
        patches.append({
            "linkId": link_id,
            "fields": {k: v for k, v in fields.items() if v},
            "linkDetails": details,
            "source": matched_by,
            "confidence": 0.95 if matched_by.startswith("lldp") else 0.75,
        })
    return {"ok": True, "patches": patches, "warnings": warnings}


def _infer_topology_family(devices: List[Dict[str, Any]]) -> str:
    roles = {str(d.get("role") or "").lower() for d in devices}
    names = " ".join(str(d.get("hostname") or "").lower() for d in devices)
    if ("rr" in roles or "rr" in names) and ("pe" in roles or "pe" in names):
        return "rr-pe-service"
    if "spine" in roles and "leaf" in roles:
        return "clos"
    if len(devices) <= 4:
        return "small-mesh"
    return "tiered"


def _synthesize_role_hints(
    devices: List[Dict[str, Any]],
    bgp_edges: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, str]:
    """Classify each device as rr / pe / ce / router from name + BGP evidence.

    The Drivenets-style RR sits at a different AS than the PEs it reflects
    for and shows BGP overlay edges to multiple PEs. We use that asymmetry
    on top of the name heuristics so freshly-discovered DUTs (no role yet)
    still get a sensible hub/spoke role assigned for canvas placement.
    """
    bgp_edges = bgp_edges or []
    by_id: Dict[str, Dict[str, Any]] = {str(d.get("id") or ""): d for d in devices}
    overlay_neighbors: Dict[str, set] = {}
    for e in bgp_edges:
        a = str(e.get("from") or "")
        b = str(e.get("to") or "")
        if not a or not b or a == b:
            continue
        overlay_neighbors.setdefault(a, set()).add(b)
        overlay_neighbors.setdefault(b, set()).add(a)

    asn_count: Dict[str, int] = {}
    for d in devices:
        asn = str(((d.get("config") or {}).get("asn")) or "").strip()
        if asn:
            asn_count[asn] = asn_count.get(asn, 0) + 1

    def name_role(name: str) -> str:
        n = (name or "").lower()
        if re.search(r"(^|[-_])rr($|[-_])", n) or "route-reflector" in n or "route_reflector" in n:
            return "rr"
        if re.search(r"(^|[-_])pe[-_0-9]", n):
            return "pe"
        if re.search(r"(^|[-_])ce($|[-_0-9])", n):
            return "ce"
        if "spine" in n:
            return "core"
        return ""

    hints: Dict[str, str] = {}
    for did, d in by_id.items():
        if not did:
            continue
        explicit = str(d.get("role") or "").lower()
        if explicit in {"rr", "pe", "ce", "core", "router", "leaf", "spine", "external"}:
            hints[did] = explicit
            continue
        nm = name_role(str(d.get("hostname") or d.get("label") or ""))
        if nm:
            hints[did] = nm
            continue
        asn = str(((d.get("config") or {}).get("asn")) or "").strip()
        peer_count = len(overlay_neighbors.get(did, set()))
        if asn and peer_count >= 2:
            others = [a for a in asn_count if a != asn]
            if others and asn_count.get(asn, 0) <= 1:
                hints[did] = "rr"
                continue
        hints[did] = "pe" if peer_count >= 1 else "router"
    return hints


def _device_address_index(devices: List[Dict[str, Any]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for d in devices:
        did = str(d.get("id") or "")
        if not did:
            continue
        cfg = d.get("config") or {}
        values: List[Any] = [
            d.get("mgmtIp"),
            d.get("ip"),
            d.get("_loopback0"),
            d.get("_routerId"),
            cfg.get("loopback0_ip"),
            cfg.get("router_id"),
        ]
        for alias_source in (d.get("hostname"), d.get("label"), d.get("name")):
            values.extend(_inferred_rid_aliases_from_name(alias_source))
        for row in (cfg.get("interfaces") or []) + (cfg.get("subinterfaces") or []):
            if isinstance(row, dict):
                values.append(row.get("ip"))
        for value in values:
            ip = _norm_ip(value)
            if ip:
                out[ip] = did
    return out


def _is_fabric_peer_name(value: Any) -> bool:
    name = str(value or "").lower()
    if not name:
        return False
    return any(token in name for token in ("dnaas", "fabric", "leaf", "spine", "ncf", "ncm", "dn-leaf"))


def _is_tester_peer(value: Any, peer_ip: Any = "") -> bool:
    text = f"{value or ''} {peer_ip or ''}".lower()
    return any(token in text for token in ("spirent", "ixia", "exabgp", "100.64.6.134", "100.64.6.135"))


def _ip24(value: Any) -> str:
    ip = _norm_ip(value)
    if not ip:
        return ""
    parts = ip.split(".")
    return ".".join(parts[:3]) + ".0/24"


def _synthesize_perimeter_nodes(
    devices: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Build muted non-DUT evidence nodes around the core DUT triangle."""
    address_index = _device_address_index(devices)
    perimeter: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []
    seen: set = set()
    scale_groups: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}

    def add_node(
        anchor: str,
        kind: str,
        label: str,
        evidence: Dict[str, Any],
        node_id: str = "",
    ) -> None:
        if not anchor or not label:
            return
        safe = re.sub(r"[^a-zA-Z0-9_.:-]+", "-", node_id or label).strip("-").lower()
        did = f"perimeter:{anchor}:{kind}:{safe}"
        if did in seen:
            for row in perimeter:
                if row.get("id") == did:
                    row.setdefault("_evidence", []).append(evidence)
                    row["_perimeterCount"] = len(row.get("_evidence") or [])
                    break
            return
        seen.add(did)
        node = {
            "id": did,
            "hostname": label,
            "label": label,
            "role": "external",
            "tier": 3,
            "radius": 24,
            "color": "#94a3b8",
            "ssh": {},
            "config": {},
            "_perimeter": True,
            "_perimeterKind": kind,
            "_anchorDevice": anchor,
            "_evidence": [evidence],
            "_perimeterCount": 1,
        }
        perimeter.append(node)
        links.append(
            {
                "fromDevice": anchor,
                "toDevice": did,
                "protocol": "Evidence",
                "linkType": "perimeter-evidence",
                "layer": "evidence",
                "originType": "QL",
                "style": {"color": "#94a3b8", "style": "dotted", "width": 1.1, "opacity": 0.45},
                "_perimeterKind": kind,
                "matchedBy": evidence.get("source") or kind,
            }
        )

    for d in devices:
        did = str(d.get("id") or "")
        if not did:
            continue
        cfg = d.get("config") or {}
        fabric_peers: List[Dict[str, Any]] = []
        for n in d.get("_lldp") or []:
            if not isinstance(n, dict):
                continue
            ph = str(n.get("peer_hostname") or "").strip()
            if not ph or any(str(other.get("hostname") or "").lower() == ph.lower() for other in devices):
                continue
            if _is_fabric_peer_name(ph):
                fabric_peers.append(
                    {
                        "source": "lldp",
                        "peer": ph,
                        "local_interface": n.get("local_interface") or "",
                        "peer_interface": n.get("peer_interface") or "",
                    }
                )
        if fabric_peers:
            names = sorted({str(x.get("peer") or "") for x in fabric_peers if x.get("peer")})
            add_node(
                did,
                "fabric",
                f"DNAAS fabric ({len(names)})",
                {"source": "lldp-fabric", "peers": names, "rows": fabric_peers},
                "dnaas-fabric",
            )

        for p in cfg.get("bgp_peers") or []:
            if not isinstance(p, dict):
                continue
            peer = str(p.get("peer") or "").strip()
            peer_ip = _norm_ip(peer)
            if not peer or (peer_ip and peer_ip in address_index):
                continue
            local_as = str(p.get("local_as") or cfg.get("asn") or "").strip()
            remote_as = str(p.get("remote_as") or "").strip()
            if not remote_as:
                continue
            subnet = _ip24(peer_ip)
            evidence = {
                "source": "bgp-peer",
                "peer": peer,
                "remote_as": remote_as,
                "local_as": local_as,
                "address_families": _normalize_af_tokens(
                    p.get("address_families") or p.get("addressFamilies") or p.get("afi_safi") or p.get("families")
                ),
            }
            if subnet:
                scale_groups.setdefault((did, subnet, remote_as), []).append(evidence)
            if _is_tester_peer(p.get("description") or p.get("source") or "", peer):
                add_node(did, "tester", f"ExaBGP CPE {peer}", evidence, peer)
            else:
                add_node(did, "cpe", f"eBGP CPE {peer}", evidence, peer)

        isis = cfg.get("isis") or {}
        local_area = str(isis.get("area") or "").strip()
        for n in isis.get("neighbors") or []:
            if not isinstance(n, dict):
                continue
            areas = n.get("areas") or n.get("area") or []
            area_list = areas if isinstance(areas, list) else [areas]
            clean_areas = [str(x) for x in area_list if str(x)]
            if clean_areas and local_area and all(a != local_area for a in clean_areas):
                peer = str(n.get("hostname") or n.get("system_id") or "foreign-igp").strip()
                add_node(
                    did,
                    "foreign-igp",
                    peer,
                    {"source": "isis-foreign-area", "peer": peer, "areas": clean_areas, "interface": n.get("interface") or ""},
                    peer,
                )

    for (anchor, subnet, remote_as), rows in scale_groups.items():
        if len(rows) < 10:
            continue
        add_node(
            anchor,
            "scale-fan",
            f"{subnet} x{len(rows)} eBGP AS{remote_as}",
            {
                "source": "bgp-scale-fan",
                "peer_subnet": subnet,
                "remote_as": remote_as,
                "count": len(rows),
                "representative": rows[0].get("peer"),
            },
            f"{subnet}-{remote_as}",
        )

    # Remove individual CPE rows that were compacted into a scale-fan.
    compacted = {
        (anchor, subnet, remote_as)
        for (anchor, subnet, remote_as), rows in scale_groups.items()
        if len(rows) >= 10
    }
    if compacted:
        compacted_ids = set()
        for (anchor, subnet, remote_as), rows in scale_groups.items():
            if (anchor, subnet, remote_as) not in compacted:
                continue
            for row in rows:
                peer = str(row.get("peer") or "")
                safe = re.sub(r"[^a-zA-Z0-9_.:-]+", "-", peer).strip("-").lower()
                compacted_ids.add(f"perimeter:{anchor}:cpe:{safe}")
                compacted_ids.add(f"perimeter:{anchor}:tester:{safe}")
        perimeter = [p for p in perimeter if p.get("id") not in compacted_ids]
        links = [l for l in links if l.get("toDevice") not in compacted_ids]
    return perimeter, links, perimeter


def _hub_spoke_triangle_positions(
    devices: List[Dict[str, Any]],
    role_hints: Dict[str, str],
    cx: int = 720,
    top_y: int = 220,
    radius: int = 320,
) -> Dict[str, Dict[str, int]]:
    """Hub-spoke layout: RR(s) anchored top-center, PEs in an arc below.

    Designed for the Drivenets-style RR + dual/multi-PE service pattern so
    a 3-DUT lab (1 RR, 2 PEs) renders as a clean equilateral triangle with
    the RR on top, and 4-6 DUT variants fan their PEs evenly below the RR.
    """
    positions: Dict[str, Dict[str, int]] = {}
    core_devices = [d for d in devices if not d.get("_perimeter")]
    perimeter_devices = [d for d in devices if d.get("_perimeter")]
    rrs = [d for d in core_devices if role_hints.get(str(d.get("id") or "")) == "rr"]
    pes = [d for d in core_devices if role_hints.get(str(d.get("id") or "")) in {"pe", "router", "leaf", "core"}]
    others = [
        d
        for d in core_devices
        if role_hints.get(str(d.get("id") or "")) in {"ce", "external"}
    ]
    rrs.sort(key=lambda x: str(x.get("hostname") or x.get("id") or ""))
    pes.sort(key=lambda x: str(x.get("hostname") or x.get("id") or ""))
    others.sort(key=lambda x: str(x.get("hostname") or x.get("id") or ""))

    if rrs:
        gap = 320
        start = cx - ((len(rrs) - 1) * gap) // 2
        for i, d in enumerate(rrs):
            positions[str(d["id"])] = {"x": int(start + i * gap), "y": top_y}

    spoke_y = top_y + 250
    if pes:
        if len(pes) == 1:
            positions[str(pes[0]["id"])] = {"x": cx, "y": spoke_y}
        elif len(pes) == 2:
            positions[str(pes[0]["id"])] = {"x": cx - 240, "y": spoke_y}
            positions[str(pes[1]["id"])] = {"x": cx + 240, "y": spoke_y}
        else:
            span = math.pi * 0.65
            start_ang = math.pi - (math.pi - span) / 2
            for i, d in enumerate(pes):
                ang = start_ang - (i * span / max(len(pes) - 1, 1))
                positions[str(d["id"])] = {
                    "x": int(cx + math.cos(ang) * radius),
                    "y": int(top_y + 180 + math.sin(ang) * radius * 0.55),
                }

    if others:
        ext_y = spoke_y + 220
        gap = 240
        start = cx - ((len(others) - 1) * gap) // 2
        for i, d in enumerate(others):
            positions[str(d["id"])] = {"x": int(start + i * gap), "y": ext_y}
    per_by_anchor: Dict[str, List[Dict[str, Any]]] = {}
    for d in perimeter_devices:
        anchor = str(d.get("_anchorDevice") or "")
        if anchor:
            per_by_anchor.setdefault(anchor, []).append(d)
    for anchor, arr in per_by_anchor.items():
        base = positions.get(anchor) or {"x": cx, "y": spoke_y}
        arr.sort(key=lambda x: (str(x.get("_perimeterKind") or ""), str(x.get("hostname") or x.get("id") or "")))
        anchor_x = int(base.get("x") or cx)
        anchor_y = int(base.get("y") or spoke_y)
        direction = -1 if anchor_x <= cx else 1
        if abs(anchor_x - cx) < 40:
            direction = 0
        for i, d in enumerate(arr):
            kind = str(d.get("_perimeterKind") or "")
            if kind == "fabric":
                dx, dy = (direction or -1) * 150, -75
            elif kind == "scale-fan":
                dx, dy = (direction or 1) * 280, 190
            else:
                spread = (i - (len(arr) - 1) / 2) * 68
                dx, dy = (direction or 1) * 245, int(spread)
            positions[str(d["id"])] = {"x": int(anchor_x + dx), "y": int(anchor_y + dy)}
    return positions


def _symmetric_positions(
    devices: List[Dict[str, Any]], family: str
) -> Dict[str, Dict[str, int]]:
    positions: Dict[str, Dict[str, int]] = {}

    def bucket(d: Dict[str, Any]) -> str:
        name = str(d.get("hostname") or "").lower()
        role = str(d.get("role") or "").lower()
        if role == "rr" or "rr" in name:
            return "rr"
        if "spine" in role or "spine" in name:
            return "core"
        if role == "pe" or "pe" in name:
            return "pe"
        if role == "ce" or "ce" in name:
            return "ce"
        return "router"

    groups: Dict[str, List[Dict[str, Any]]] = {}
    for d in devices:
        b = bucket(d)
        groups.setdefault(b, []).append(d)
    for arr in groups.values():
        arr.sort(key=lambda x: str(x.get("hostname") or x.get("id") or ""))

    def place_row(arr: List[Dict[str, Any]], y: int, cx: int, gap: int) -> None:
        if not arr:
            return
        start = cx - ((len(arr) - 1) * gap) // 2
        for i, d in enumerate(arr):
            positions[str(d["id"])] = {"x": int(start + i * gap), "y": y}

    if family == "rr-pe-service":
        place_row(groups.get("rr", []) + groups.get("core", []), 220, 720, 260)
        place_row(groups.get("pe", []), 430, 720, 360)
        place_row(groups.get("ce", []) + groups.get("router", []), 650, 720, 260)
    elif family == "clos":
        place_row(groups.get("core", []) + groups.get("rr", []), 220, 720, 240)
        place_row(groups.get("pe", []) + groups.get("router", []), 460, 720, 220)
        place_row(groups.get("ce", []), 680, 720, 220)
    else:
        sorted_d = sorted(devices, key=lambda x: str(x.get("hostname") or ""))
        if len(sorted_d) <= 4:
            r, cx, cy = 230, 720, 430
            for i, d in enumerate(sorted_d):
                ang = -math.pi / 2 + (i * 2 * math.pi / max(len(sorted_d), 1))
                positions[str(d["id"])] = {
                    "x": int(cx + math.cos(ang) * r),
                    "y": int(cy + math.sin(ang) * r),
                }
        else:
            place_row(groups.get("rr", []) + groups.get("core", []), 220, 720, 260)
            place_row(groups.get("pe", []) + groups.get("router", []), 460, 720, 240)
            place_row(groups.get("ce", []), 680, 720, 220)

    for d in devices:
        did = str(d.get("id") or "")
        if did and did not in positions:
            positions[did] = {"x": 720, "y": 820}
    return positions


def _guard_filter_devices(devices: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """Drop DNAAS/fabric-only rows and devices without app SSH targets."""
    skipped: List[Dict[str, str]] = []
    kept: List[Dict[str, Any]] = []
    dnaas_markers = (
        "dnaas",
        "fabric",
        "ncm",
        "ncf",
        "superspine",
        "aggregation",
        "agg-",
        "-leaf",
        "-spine",
    )

    def _is_dnaas_name(hostname: str) -> bool:
        u = (hostname or "").lower()
        if not u:
            return False
        if "dnaas" in u or "fabric" in u:
            return True
        return any(m in u for m in dnaas_markers)

    for d in devices:
        hn = str(d.get("hostname") or d.get("label") or "")
        if d.get("_origin") == "dnaas-bd" or _is_dnaas_name(hn):
            skipped.append({"hostname": hn or d.get("id", ""), "reason": "DNAAS/fabric device excluded from Generate"})
            continue
        ssh = d.get("ssh") or {}
        if not (ssh.get("host") or ssh.get("hostBackup")):
            skipped.append({"hostname": hn or d.get("id", ""), "reason": "No app SSH/SN/active-NCC target"})
            continue
        kept.append(d)
    return kept, skipped


def correlate_topology_facts(
    facts: Dict[str, Any],
    app_user: str,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run correlation in a temp SQLite DB; return enriched facts + evidence."""
    options = options or {}
    if not facts or not isinstance(facts.get("devices"), list):
        return {"facts": facts or {}, "correlationEvidence": {"error": "no devices"}, "ok": False}

    base = copy.deepcopy(facts)
    kept_devices, skipped_guard = _guard_filter_devices(base.get("devices") or [])
    base["devices"] = kept_devices
    kept_ids = {str(d.get("id")) for d in kept_devices if d.get("id")}
    base["links"] = [
        L
        for L in (base.get("links") or [])
        if L.get("fromDevice") in kept_ids and L.get("toDevice") in kept_ids
    ]
    base["physicalLinks"] = [
        L
        for L in (base.get("physicalLinks") or [])
        if L.get("fromDevice") in kept_ids and L.get("toDevice") in kept_ids
    ]
    base["logicalLinks"] = [
        L
        for L in (base.get("logicalLinks") or [])
        if L.get("fromDevice") in kept_ids and L.get("toDevice") in kept_ids
    ]

    devices_in = copy.deepcopy(base["devices"])
    db_path = _temp_db_path(app_user or "default")
    conn: Optional[sqlite3.Connection] = None
    evidence: Dict[str, Any] = {
        "bgp_edges": [],
        "lldp_edges": [],
        "service_groups": [],
        "db_path": os.path.basename(db_path),
    }
    try:
        conn = sqlite3.connect(db_path)
        _create_schema(conn)
        _populate(conn, devices_in)

        bgp_edges = _collect_bgp_edges(conn)
        evidence["bgp_edges"] = bgp_edges
        lldp_edges = _collect_lldp_edges(conn)
        evidence["lldp_edges"] = lldp_edges
        service_groups = _collect_service_groups(conn)
        evidence["service_groups"] = service_groups

        cur = conn.cursor()
        for e in bgp_edges:
            cur.execute(
                """INSERT INTO correlations (kind, device_a, device_b, detail, score, evidence)
                   VALUES (?,?,?,?,?,?)""",
                (
                    "bgp",
                    e["from"],
                    e["to"],
                    json.dumps(
                        {
                            "external": e["is_external"],
                            "local_as": e["local_as"],
                            "remote_as": e["remote_as"],
                        }
                    ),
                    0.95,
                    e.get("evidence") or "",
                ),
            )
        for e in lldp_edges:
            cur.execute(
                """INSERT INTO correlations (kind, device_a, device_b, detail, score, evidence)
                   VALUES (?,?,?,?,?,?)""",
                (
                    "lldp",
                    e["from"],
                    e["to"],
                    json.dumps(
                        {
                            "local_if": e.get("local_interface"),
                            "peer_if": e.get("peer_interface"),
                        }
                    ),
                    0.85,
                    e.get("evidence") or "",
                ),
            )
        conn.commit()

        out = copy.deepcopy(base)
        out_devices = {d["id"]: copy.deepcopy(d) for d in out.get("devices", []) if d.get("id")}
        logical: List[Dict[str, Any]] = []
        seen_logical: set = set()

        def add_logical(
            a: str,
            b: str,
            protocol: str,
            link_type: str,
            layer: str,
            style: Dict[str, Any],
            extra: Optional[Dict[str, Any]] = None,
        ) -> None:
            if not a or not b or a == b:
                return
            key = tuple(sorted([a, b]) + [link_type, protocol])
            if key in seen_logical:
                return
            seen_logical.add(key)
            row: Dict[str, Any] = {
                "fromDevice": a,
                "toDevice": b,
                "protocol": protocol,
                "linkType": link_type,
                "layer": layer,
                "originType": "QL",
                "style": style,
            }
            if extra:
                row.update(extra)
            source = str(row.get("matchedBy") or row.get("source") or row.get("_source") or "logical-correlation")
            _apply_scene_meta(
                row,
                layer=layer,
                source=source,
                fallback_confidence="verified" if layer == "physical" else "correlated",
                evidence=[protocol, link_type, row.get("fromInterface", ""), row.get("toInterface", ""), row.get("peerIp", "")],
                priority=90 if layer == "physical" else 80,
            )
            logical.append(row)

        for e in bgp_edges:
            la = e.get("local_as") or ""
            ra = e.get("remote_as") or ""
            ext = e.get("is_external")
            if ext:
                proto = f"eBGP {la}→{ra}" if la else f"eBGP →{ra}"
                add_logical(
                    e["from"],
                    e["to"],
                    proto,
                    "eBGP",
                    "routing",
                    {"color": "#e67e22", "style": "dashed", "width": 1.8},
                    {"extra": {"peerIp": e.get("peer") or "", "localAs": la, "remoteAs": ra}, "peerIp": e.get("peer") or "", "matchedBy": "bgp-peer-ip"},
                )
            else:
                proto = f"iBGP AS{ra or la or '?'}"
                add_logical(
                    e["from"],
                    e["to"],
                    proto,
                    "iBGP",
                    "routing",
                    {"color": "#3498db", "style": "dashed", "width": 1.6},
                    {"extra": {"peerIp": e.get("peer") or "", "localAs": la, "remoteAs": ra}, "peerIp": e.get("peer") or "", "matchedBy": "bgp-peer-ip"},
                )

        def protocol_stack_label(cfg: Dict[str, Any]) -> Tuple[str, str]:
            isis_area = str(((cfg.get("isis") or {}).get("area")) or "").strip()
            ospf_area = str(((cfg.get("ospf") or {}).get("area")) or "").strip()
            mpls = cfg.get("mpls") or {}
            base = "ISIS" if isis_area else ("OSPF" if ospf_area else "")
            area = isis_area or ospf_area
            if not base:
                return "", ""
            suffix = ""
            if mpls.get("ldp") and mpls.get("sr"):
                suffix = "+LDP+SR"
            elif mpls.get("ldp"):
                suffix = "+LDP"
            elif mpls.get("sr"):
                suffix = "-SR"
            return f"{base}{suffix} area {area}", f"{base}{suffix}"

        igp_groups: Dict[str, List[str]] = {}
        igp_types: Dict[str, str] = {}
        for did, dev in out_devices.items():
            cfg = dev.get("config") or {}
            label, link_type = protocol_stack_label(cfg)
            if label:
                igp_groups.setdefault(label, []).append(did)
                igp_types[label] = link_type

        for label, members in igp_groups.items():
            members = sorted(members, key=lambda x: str(out_devices.get(x, {}).get("hostname") or x))
            link_type = igp_types.get(label) or label.split()[0]
            style_color = "#8e44ad" if link_type.startswith("ISIS") else "#27ae60"
            if len(members) <= 4:
                pairs = [(members[a], members[b]) for a in range(len(members)) for b in range(a + 1, len(members))]
            else:
                pairs = [(members[0], members[i]) for i in range(1, min(len(members), 8))]
            for a, b in pairs:
                add_logical(
                    a,
                    b,
                    label,
                    link_type,
                    "routing",
                    {"color": style_color, "style": "dotted", "width": 1.35},
                    {"matchedBy": "igp-mpls-config"},
                )

        phys_pairs = set()
        for lk in out.get("links") or []:
            fa = lk.get("fromDevice")
            fb = lk.get("toDevice")
            if fa and fb:
                phys_pairs.add(tuple(sorted([fa, fb])))

        for e in lldp_edges:
            pair = tuple(sorted([e["from"], e["to"]]))
            if pair in phys_pairs:
                continue
            add_logical(
                e["from"],
                e["to"],
                "LLDP",
                "physical-lldp",
                "physical",
                {"color": "#5dade2", "style": "solid", "width": 2.2},
                {
                    "extra": {},
                    "fromInterface": e.get("local_interface") or "",
                    "toInterface": e.get("peer_interface") or "",
                },
            )

        perimeter_nodes, perimeter_links, perimeter_evidence = _synthesize_perimeter_nodes(list(out_devices.values()))
        for pnode in perimeter_nodes:
            pid = str(pnode.get("id") or "")
            if pid and pid not in out_devices:
                out_devices[pid] = pnode
        for plink in perimeter_links:
            logical.append(plink)

        existing_logical = base.get("logicalLinks") or []
        for L in existing_logical:
            lt = str(L.get("linkType") or "")
            if lt in ("iBGP", "eBGP", "OSPF", "ISIS"):
                fa, fb = L.get("fromDevice"), L.get("toDevice")
                key = tuple(sorted([fa, fb]) + [lt, str(L.get("protocol") or "")])
                if key not in seen_logical:
                    seen_logical.add(key)
                    logical.append(copy.deepcopy(L))

        out["logicalLinks"] = logical
        out["links"] = [
            _enrich_fact_link(copy.deepcopy(L), out_devices)
            for L in (out.get("links") or [])
        ]
        out["logicalLinks"] = [
            _enrich_fact_link(copy.deepcopy(L), out_devices)
            for L in (out.get("logicalLinks") or [])
        ]

        services = list(out.get("services") or [])
        svc_by_key: Dict[str, Dict[str, Any]] = {}
        for L in existing_logical:
            lt = str(L.get("linkType") or "")
            if lt not in ("VRF", "BD", "EVPN-RT"):
                continue
            fa, fb = L.get("fromDevice"), L.get("toDevice")
            if fa not in out_devices or fb not in out_devices:
                continue
            kind = "evpn" if lt == "EVPN-RT" else lt.lower()
            raw_name = str(L.get("protocol") or L.get("bd") or lt or "service")
            name = re.sub(r"^(VRF|BD|RT)\s+", "", raw_name, flags=re.I).strip() or raw_name
            key = f"{kind}:{name if kind != 'evpn' else 'service'}"
            if key not in svc_by_key:
                svc_by_key[key] = {
                    "id": key,
                    "kind": kind,
                    "name": "EVPN Service" if kind == "evpn" else name,
                    "label": "EVPN Service" if kind == "evpn" else f"{kind.upper()} {name}",
                    "members": [],
                    "memberNames": [],
                    "routeTargets": [name] if kind == "evpn" else [],
                    "color": "#f39c12" if kind == "evpn" else "#1abc9c",
                    "layer": "service",
                    "note": "service with route-target evidence" if kind == "evpn" else "correlated service (from logical link)",
                }
            elif kind == "evpn":
                rt_list = svc_by_key[key].setdefault("routeTargets", [])
                if name not in rt_list:
                    rt_list.append(name)
            svc = svc_by_key[key]
            for did in (fa, fb):
                if did not in svc["members"]:
                    svc["members"].append(did)
                    svc["memberNames"].append(
                        str(out_devices.get(did, {}).get("hostname") or did)
                    )
        for svc in svc_by_key.values():
            if len(svc["members"]) >= 2:
                services.append(svc)

        for sg in sorted(service_groups, key=lambda row: 1 if row.get("kind") == "rt" else 0):
            kind = sg["kind"]
            name = sg["name"]
            mem = sg["members"]
            if len(mem) < 2:
                continue
            member_names = [str(out_devices.get(mid, {}).get("hostname") or mid) for mid in mem]
            if kind == "rt":
                mem_set = set(mem)
                attached = False
                for svc in services:
                    svc_kind = str(svc.get("kind") or "")
                    svc_mem = set(svc.get("members") or [])
                    if svc_kind != "rt" and len(mem_set & svc_mem) >= 2:
                        rt_list = svc.setdefault("routeTargets", [])
                        if name not in rt_list:
                            rt_list.append(name)
                        svc["note"] = "service with route-target evidence"
                        attached = True
                if attached:
                    continue
                kind = "evpn"
                name = "EVPN Service"
            svc = {
                "id": f"{kind}:{name}",
                "kind": kind,
                "name": name,
                "label": ("EVPN Service" if kind == "evpn" else f"{kind.upper()} {name}"),
                "members": mem,
                "memberNames": member_names,
                "routeTargets": [sg["name"]] if kind == "evpn" else [],
                "color": "#f39c12" if kind == "evpn" else "#1abc9c",
                "layer": "service",
                "note": "service correlated via sqlite index",
            }
            services.append(svc)
        known_pack, known_id_map = _match_known_topology_pack(out_devices)
        if known_pack:
            services.extend(_services_from_known_pack(known_pack, known_id_map, out_devices))
            evidence["knownTopology"] = {
                "id": known_pack.get("id"),
                "label": known_pack.get("label"),
                "matchedDevices": len(known_id_map),
            }
        svc_dedup: Dict[str, Dict[str, Any]] = {}
        for s in services:
            sid = str(s.get("id") or "")
            if sid:
                source = str(s.get("_source") or s.get("note") or "service-correlation")
                _apply_scene_meta(
                    s,
                    layer="service",
                    source=source,
                    fallback_confidence="verified" if source.startswith("known-topology") else "correlated",
                    evidence=[
                        str(s.get("name") or ""),
                        *[str(x) for x in (s.get("routeTargets") or [])],
                        *[str(x) for x in (s.get("members") or [])],
                    ],
                    priority=85,
                )
                svc_dedup[sid] = s
        out["services"] = list(svc_dedup.values())

        core_devices_for_layout = [d for d in out_devices.values() if not d.get("_perimeter")]
        family = _infer_topology_family(core_devices_for_layout)
        role_hints = _synthesize_role_hints(list(out_devices.values()), bgp_edges)
        for did, role in role_hints.items():
            if did in out_devices and not str(out_devices[did].get("role") or "").strip():
                out_devices[did]["role"] = role
        rr_count = sum(1 for r in role_hints.values() if r == "rr")
        if family == "rr-pe-service" and rr_count >= 1 and len(core_devices_for_layout) <= 6:
            positions = _hub_spoke_triangle_positions(
                list(out_devices.values()), role_hints
            )
            layout_mode = "hub-spoke-triangle"
        else:
            positions = _symmetric_positions(list(out_devices.values()), family)
            layout_mode = "tiered-rows"
        for did, pos in positions.items():
            if did in out_devices:
                out_devices[did]["position"] = pos
        out["devices"] = list(out_devices.values())

        included = [str(d.get("hostname") or did) for did, d in out_devices.items()]
        unmatched: List[Dict[str, str]] = []
        for did, d in out_devices.items():
            has_edge = any(
                (L.get("fromDevice") == did or L.get("toDevice") == did)
                for L in (out.get("links") or []) + (out.get("logicalLinks") or [])
            )
            if not has_edge:
                unmatched.append(
                    {
                        "hostname": str(d.get("hostname") or did),
                        "reason": "No correlated edge after DB cross-reference",
                    }
                )

        groups = list(out.get("groups") or [])
        groups = [
            {
                **g,
                "members": [m for m in (g.get("members") or []) if m in kept_ids],
            }
            for g in groups
            if len([m for m in (g.get("members") or []) if m in kept_ids]) >= 2
        ]
        if len(unmatched) >= 2:
            um_hosts = {x["hostname"] for x in unmatched}
            groups.append(
                {
                    "id": "unmatched-duts",
                    "kind": "unmatched",
                    "label": "Unmatched DUTs",
                    "members": [
                        did
                        for did, dv in out_devices.items()
                        if str(dv.get("hostname") or did) in um_hosts
                    ],
                    "color": "#95a5a6",
                }
            )
        out["groups"] = groups

        score = 100.0
        score -= max(0, len(logical) - len(out_devices) * 3) * 2
        score -= len(unmatched) * 5

        prior_skipped = list((facts.get("compositionReport") or {}).get("skippedDevices") or [])
        out["compositionReport"] = {
            "includedDevices": included,
            "unmatchedDevices": unmatched,
            "skippedDevices": prior_skipped + skipped_guard,
            "topologyFamily": family,
            "visualProfile": "sqlite-correlation-v1",
            "score": int(score),
            "warnings": list(facts.get("warnings") or []),
        }
        out["generationSignature"] = facts.get("generationSignature") or {}

        curve_hints: Dict[str, Any] = {}
        for e in bgp_edges:
            a, b = sorted([e["from"], e["to"]])
            curve_hints[f"{a}:{b}"] = {"routingBias": 0.12, "kind": "bgp"}
        for e in lldp_edges:
            a, b = sorted([e["from"], e["to"]])
            curve_hints.setdefault(f"{a}:{b}", {"physicalBias": -0.08, "kind": "lldp"})

        evidence["topologyFamily"] = family
        evidence["positions"] = positions
        evidence["layout"] = {
            "positions": positions,
            "bands": {"family": family},
            "curveHints": curve_hints,
            "mode": layout_mode,
        }
        evidence["roleHints"] = role_hints
        evidence["perimeter"] = perimeter_evidence
        evidence["overlayModesAvailable"] = ["real-legs", "via-rr", "both"]
        evidence["overlayDefaultMode"] = "real-legs"
        evidence["logicalLinkCount"] = len(logical)
        evidence["serviceCount"] = len(out["services"])

        return {"facts": out, "correlationEvidence": evidence, "ok": True}
    except Exception as exc:  # pragma: no cover - defensive
        evidence["error"] = str(exc)
        return {"facts": facts, "correlationEvidence": evidence, "ok": False}
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
        try:
            if os.path.isfile(db_path):
                os.unlink(db_path)
        except OSError:
            pass
