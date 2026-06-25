"""Canonical protocol-topology blueprint loader.

The AI assistant uses these blueprints as its vocabulary for "show me a
professional BGP / OSPF / EVPN / Clos / campus / ring / DCI topology".
Without them, free-form LLM output lacks the color coding, shapes,
arrows, and text-box annotations that industry-standard network
diagrams carry -- see the plan at
``.cursor/plans/ai_protocol_topology_reference_db_79fab996.plan.md``
for the why.

Storage layout (read-mostly, git-diffable JSON + one INDEX.md):

    topology/ai/blueprints/
        INDEX.md                        <- auto-generated catalog
        bgp/
            ibgp-full-mesh-4.json
            ibgp-rr-hub-spoke-6.json
            ebgp-2as-transit.json
            ...
        ospf/
            single-area-5.json
            ...
        ...

Per-user overrides live at ``~/.topology_users/<user>/ai_blueprints/*.json``
(flat, no sub-dirs) and take precedence on filename collision -- matching
the multi-user doctrine used by ``knowledge.md`` / ``devices.db`` / etc.

Public surface:
    list_blueprints(filter={...}) -> list[dict]
    load_blueprint(name)         -> dict (full JSON)
    reload_blueprints()          -> dict (admin round-trip stats)

Every blueprint JSON has the following MINIMUM shape:

    {
        "name":       "ibgp-full-mesh-4",     # MUST match filename stem
        "protocol":   "bgp",                  # bgp/ibgp/ebgp/ospf/isis/...
        "scale":      "small",                # small/medium/large/enterprise
        "summary":    "One-sentence description.",
        "tags":       ["ibgp", "full-mesh", "4-node"],
        "layout_hint": "mesh",                # optional, mirrors create_topology
        "objects":    [ ...canvas objects... ]
    }

The ``objects`` list is the exact shape ``create_topology`` expects
(type in {device, link, text, shape}), so ``load_blueprint`` output
can be passed almost verbatim into ``create_topology``. The LLM should
adapt device counts/names to the user's ask before emitting.
"""

from __future__ import annotations

import json
import os
import re
import threading
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from api.auth.user_store import user_store
except Exception:  # pragma: no cover
    user_store = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Paths + caches.
# ---------------------------------------------------------------------------
_REPO_BLUEPRINT_ROOT = Path(__file__).with_name("blueprints")
_USER_SUBDIR = "ai_blueprints"  # lives inside each user's workspace

# ---------------------------------------------------------------------------
# Terminology / concept bridge.
# ---------------------------------------------------------------------------
# Network engineers describe topologies by USE CASE ("multicast",
# "traffic engineering", "data center", "metro ring") far more often
# than by the specific control-plane protocol. The raw library is keyed
# by protocol (pim / mvpn / sr-mpls / ...), so a literal filter like
# ``list_blueprints(protocol="multicast")`` would return nothing even
# though five multicast blueprints exist.
#
# This alias map is the bridge: every common concept expands to the
# underlying protocol set (and vice-versa, each protocol knows its
# concept labels). The expansion feeds both the ``protocol`` filter and
# the ``query`` tokenizer in list_blueprints so "multicast on MPLS",
# "DC fabric", "Clos", "overlay", "metro ring" all resolve to the right
# blueprints.
#
# Keys are LOWERCASE. Values are a set of related tokens -- each token
# is either a protocol key, a tag value, or another alias key. The
# expansion is transitive (see _expand_aliases).
_PROTOCOL_ALIASES: Dict[str, List[str]] = {
    # --- Multicast family ---------------------------------------------------
    "multicast": ["pim", "igmp", "mvpn", "mldp", "p2mp", "ssm", "asm",
                   "pim-sm", "pim-ssm", "pim-dm", "pim-bidir", "mcast"],
    "mcast": ["multicast"],
    "pim": ["pim-sm", "pim-ssm", "pim-dm", "pim-bidir", "multicast"],
    "mvpn": ["multicast", "l3vpn", "mpls-l3vpn", "rosen", "ng-mvpn"],
    "mldp": ["multicast", "mpls", "p2mp"],
    "igmp": ["multicast"],

    # --- L3VPN / MPLS -------------------------------------------------------
    "l3vpn": ["mpls-l3vpn", "vrf", "mpls", "vpnv4", "vpnv6"],
    "mpls": ["ldp", "rsvp-te", "sr-mpls", "mpls-l3vpn"],
    "vrf": ["mpls-l3vpn", "l3vpn"],
    "rsvp": ["rsvp-te", "mpls", "te"],

    # --- Segment Routing / TE -----------------------------------------------
    "sr": ["sr-mpls", "srv6", "segment-routing", "ti-lfa", "sr-te"],
    "segment-routing": ["sr", "sr-mpls", "srv6", "sr-te"],
    "te": ["sr-te", "rsvp-te", "traffic-engineering"],
    "traffic-engineering": ["te", "sr-te", "rsvp-te"],
    "fast-reroute": ["ti-lfa", "lfa", "rsvp-te"],
    "ti-lfa": ["sr", "fast-reroute"],

    # --- Data-center --------------------------------------------------------
    "dc": ["clos", "evpn-vxlan", "evpn", "vxlan", "leaf-spine", "fabric",
            "datacenter", "data-center"],
    "datacenter": ["dc"],
    "data-center": ["dc"],
    "fabric": ["clos", "evpn-vxlan", "leaf-spine", "dc"],
    "clos": ["leaf-spine", "spine", "leaf", "dc", "fabric"],
    "leaf-spine": ["clos", "dc", "fabric"],
    "overlay": ["evpn", "vxlan", "mvpn", "ibgp"],
    "underlay": ["ospf", "isis", "ebgp"],
    "vxlan": ["evpn", "evpn-vxlan", "overlay", "dc"],
    "evpn": ["evpn-vxlan", "overlay", "mac-vrf", "dc"],
    "anycast-gateway": ["evpn", "evpn-vxlan", "leaf-spine"],

    # --- BGP flavours -------------------------------------------------------
    "bgp": ["ibgp", "ebgp", "bgp-lu", "route-server", "route-reflector",
             "confederation"],
    "route-reflector": ["ibgp", "bgp"],
    "ixp": ["route-server", "ebgp", "bgp"],

    # --- IGP ---------------------------------------------------------------
    # Deliberately narrow: we only list the sibling PROTOCOL keys, never
    # internal design tokens like "area" / "abr" / "stub" -- those are
    # too short / too common and false-positive against other blueprints.
    "igp": ["ospf", "isis"],
    "ospf": ["igp"],
    "isis": ["igp"],

    # --- Metro / rings -----------------------------------------------------
    # Intentionally does NOT include "mpls" -- a user asking for a
    # "metro" topology wants a ring, not every MPLS blueprint in the
    # catalog. If they want metro + MPLS they'll say so.
    "metro": ["ring", "g8032", "erps"],
    "ring": ["metro", "g8032", "erps"],
    "g8032": ["ring", "metro", "erps"],
    "erps": ["ring", "metro"],

    # --- DCI / WAN ---------------------------------------------------------
    "dci": ["l2-extension", "evpn", "vxlan", "wan"],
    "wan": ["dci", "ebgp", "carrier"],
    "carrier": ["mpls", "mpls-l3vpn", "sr", "isis", "wan"],

    # --- Enterprise / campus -----------------------------------------------
    "enterprise": ["campus", "mlag", "ospf"],
    "campus": ["enterprise", "mlag", "3-tier"],
    "mlag": ["campus", "3-tier", "lag"],

    # --- DriveNets-specific ------------------------------------------------
    "drivenets": ["ncp", "ncf", "ncm", "ncc", "dnaas", "dnos"],
    "dnaas": ["drivenets", "discovery"],
    "disaggregated": ["drivenets", "ncp", "ncf"],
    "chassis": ["ncp", "ncf", "ncm", "ncc"],

    # --- QoS family --------------------------------------------------------
    "qos": ["cos", "dscp", "diffserv", "hqos", "shaping", "policing",
             "classification", "ef", "af", "be", "wred", "lle"],
    "cos": ["qos"],
    "dscp": ["qos", "diffserv"],
    "diffserv": ["qos", "dscp"],
    "hqos": ["qos", "hierarchical"],
    "shaping": ["qos", "policing"],
    "policing": ["qos", "shaping"],

    # --- HA / failover -----------------------------------------------------
    "ha": ["vrrp", "hsrp", "glbp", "bfd", "redundancy", "failover",
            "high-availability", "active-standby", "active-active"],
    "high-availability": ["ha"],
    "redundancy": ["ha", "vrrp", "bfd", "failover"],
    "failover": ["ha", "vrrp", "bfd"],
    "vrrp": ["ha", "redundancy", "gateway-redundancy"],
    "hsrp": ["ha", "redundancy"],
    "glbp": ["ha", "redundancy"],
    "bfd": ["ha", "fast-detection"],
    "fast-detection": ["bfd"],

    # --- Site-to-site VPN / tunnels ----------------------------------------
    # NOTE: `vpn` and `tunnel` are kept deliberately narrow -- adding
    # "l3vpn" or "tunnel" as broad aliases drags in every MPLS blueprint
    # and every overlay protocol. If the user literally writes "mpls vpn"
    # we rely on their own query, not alias expansion.
    "vpn": ["ipsec", "gre", "dmvpn", "ssl-vpn", "sslvpn", "wireguard",
             "l2tp", "site-to-site"],
    "ipsec": ["vpn", "ike", "ikev2", "esp", "ah", "encryption"],
    "gre": ["vpn", "overlay-tunnel"],
    "dmvpn": ["vpn", "ipsec", "nhrp", "multipoint-gre"],
    "sslvpn": ["vpn", "remote-access"],
    "ssl-vpn": ["vpn"],
    "wireguard": ["vpn"],
    "l2tp": ["vpn", "pppoe"],
    "site-to-site": ["vpn", "ipsec"],
    "tunnel": ["gre", "ipsec"],

    # --- NAT ---------------------------------------------------------------
    "nat": ["cgnat", "nat44", "nat64", "nat46", "pat", "napt", "dnat", "snat"],
    "cgnat": ["nat", "nat44", "carrier-grade-nat", "lsn"],
    "carrier-grade-nat": ["cgnat", "nat"],
    "nat44": ["nat", "cgnat"],
    "nat64": ["nat", "dual-stack", "ipv6-transition"],
    "nat46": ["nat", "dual-stack"],

    # --- L2 / Spanning-tree ------------------------------------------------
    # STP family stays tight: it MUST NOT leak into generic L2 blueprints
    # (Q-in-Q, L2VPN) just because they mention l2 in their tags.
    "stp": ["rstp", "mstp", "spanning-tree"],
    "spanning-tree": ["stp", "rstp", "mstp"],
    "rstp": ["stp", "spanning-tree"],
    "mstp": ["stp", "spanning-tree", "mst-region"],
    "vlan": ["trunk", "qinq"],
    "qinq": ["vlan", "s-tag", "c-tag"],

    # --- L2VPN family ------------------------------------------------------
    "l2vpn": ["vpls", "vpws", "pseudowire", "pw", "elan", "epl", "evpl",
                "e-line", "e-lan", "evpn-vpws"],
    "vpls": ["l2vpn", "pseudowire", "elan", "e-lan", "meshed-pws"],
    "vpws": ["l2vpn", "pseudowire", "pw", "epl", "evpl", "e-line"],
    "pseudowire": ["pw", "l2vpn", "vpws", "vpls"],
    "pw": ["pseudowire", "l2vpn"],
    "epl": ["vpws", "l2vpn", "e-line"],
    "evpl": ["vpws", "l2vpn", "e-line"],
    "elan": ["vpls", "l2vpn", "e-lan"],
    "e-line": ["vpws", "epl", "evpl"],
    "e-lan": ["vpls", "elan"],

    # --- Security / DDoS / filtering ---------------------------------------
    # `security` is a VERY generic word; we deliberately do NOT alias it
    # to "bgp", "acl", or "filter" because most BGP / policy blueprints
    # would otherwise swamp a search for "security".
    "security": ["flowspec", "rtbh", "ddos", "rpki"],
    "acl": ["filter", "access-list"],
    "firewall": ["zone", "stateful"],
    "flowspec": ["ddos", "rfc5575", "rfc8955", "mitigation"],
    "rtbh": ["blackhole", "ddos", "mitigation"],
    "blackhole": ["rtbh"],
    "ddos": ["flowspec", "rtbh", "mitigation"],
    "rpki": ["roa", "origin-validation"],
    "roa": ["rpki"],
    "origin-validation": ["rpki", "roa"],
    "peering-security": ["rpki", "roa"],

    # --- Broadband / BNG / subscriber --------------------------------------
    # We deliberately do NOT alias "broadband" to "access" -- "access" is
    # a tag on 3tier / campus / ring blueprints and would over-match.
    "broadband": ["bng", "pppoe", "ipoe", "subscriber", "l2tp-lac-lns"],
    "bng": ["broadband", "pppoe", "ipoe", "subscriber", "bras"],
    "bras": ["bng", "broadband"],
    "pppoe": ["broadband", "bng", "subscriber", "ppp"],
    "ipoe": ["broadband", "bng"],
    "subscriber": ["bng", "broadband", "radius"],
    "radius": ["subscriber", "bng", "aaa"],
    "aaa": ["radius", "tacacs"],

    # --- Mobile / 5G / xHaul -----------------------------------------------
    "mobile": ["5g", "4g", "lte", "xhaul", "fronthaul", "midhaul",
                "backhaul", "csr", "ipran", "cran"],
    "5g": ["mobile", "xhaul", "fronthaul", "midhaul", "backhaul",
            "ru", "du", "cu", "upf", "gnb"],
    "4g": ["mobile", "lte", "backhaul", "enb"],
    "lte": ["4g", "mobile"],
    "xhaul": ["fronthaul", "midhaul", "backhaul", "mobile"],
    "fronthaul": ["xhaul", "5g", "ru", "ecpri"],
    "midhaul": ["xhaul", "5g", "du", "cu"],
    "backhaul": ["xhaul", "mobile", "ipran"],
    "csr": ["mobile", "cell-site-router", "backhaul"],
    "cell-site-router": ["csr", "mobile"],
    "ipran": ["mobile", "backhaul"],

    # --- Routing policy / BGP attributes -----------------------------------
    "policy": ["route-map", "prefix-list", "as-path", "community",
                "local-preference", "med", "routing-policy"],
    "routing-policy": ["policy", "route-map", "prefix-list"],
    "route-map": ["policy", "routing-policy"],
    "prefix-list": ["policy", "routing-policy"],
    "community": ["bgp", "policy", "well-known-community"],
    "as-path": ["bgp", "policy"],
    "local-preference": ["policy", "bgp", "local-pref"],
    "med": ["policy", "bgp", "metric"],

    # --- Telemetry / observability -----------------------------------------
    "telemetry": ["gnmi", "netconf", "snmp", "syslog", "sflow",
                   "netflow", "ipfix", "streaming-telemetry",
                   "monitoring", "observability"],
    "monitoring": ["telemetry", "snmp", "syslog"],
    "observability": ["telemetry", "streaming-telemetry"],
    "gnmi": ["telemetry", "streaming-telemetry", "openconfig", "grpc"],
    "netconf": ["telemetry", "yang", "ssh"],
    "snmp": ["telemetry", "monitoring"],
    "sflow": ["telemetry", "flow", "sampling"],
    "netflow": ["telemetry", "flow", "ipfix"],
    "ipfix": ["netflow", "telemetry", "flow"],
    "streaming-telemetry": ["gnmi", "telemetry"],
    "openconfig": ["gnmi", "yang"],

    # --- Load sharing / link aggregation -----------------------------------
    "ecmp": ["multipath", "load-balancing", "equal-cost"],
    "ucmp": ["unequal-cost", "load-balancing"],
    "load-balancing": ["ecmp", "ucmp", "lag"],
    "lacp": ["lag", "bundle"],
    "bond": ["lag", "bundle"],

    # --- Addressing / stack ------------------------------------------------
    "dualstack": ["dual-stack", "ipv4", "ipv6"],
    "dual-stack": ["dualstack", "ipv4", "ipv6"],
    "ipv6": ["slaac", "dual-stack", "ra", "ospfv3"],
    "ipv4": ["dual-stack"],
    "slaac": ["ipv6"],
    "ra": ["ipv6", "router-advertisement"],

    # --- SD-WAN / cloud ----------------------------------------------------
    "sdwan": ["sd-wan", "overlay", "ipsec", "dmvpn", "sase"],
    "sd-wan": ["sdwan"],
    "sase": ["sdwan", "security"],
    "cloud": ["vpc", "transit-gateway", "direct-connect", "expressroute"],
    "vpc": ["cloud"],
    "transit-gateway": ["cloud", "hub-spoke"],
    "direct-connect": ["cloud", "dci"],
    "expressroute": ["cloud", "dci"],
}


def _expand_aliases(token: str) -> set:
    """Return the direct 1-hop expansion of an alias token.

    We deliberately DO NOT follow alias chains transitively. Full
    transitive closure would drag every concept into every other
    (``dc -> overlay -> mvpn -> multicast``, ``metro -> mpls ->
    mpls-l3vpn -> ...``), which defeats the purpose of the filter.

    The alias map is authored so each concept already lists every
    sibling it should reach in ONE hop. If a user expects two-hop
    reach (e.g. "pim" -> "multicast" -> "mvpn"), we encode that by
    adding ``mvpn`` directly to the ``pim`` entry.
    """
    tok = (token or "").strip().lower()
    if not tok:
        return set()
    out = {tok}
    for child in _PROTOCOL_ALIASES.get(tok, []):
        c = (child or "").strip().lower()
        if c:
            out.add(c)
    return out


def _tokenize_query(query: str) -> set:
    """Split a free-form query into words, strip punctuation, dedupe.

    "multicast on MPLS with RP" -> {"multicast", "mpls", "with", "rp"}.
    Stopwords are dropped so the intersection step downstream is
    meaningful. The result is later expanded via _expand_aliases.
    """
    if not query:
        return set()
    q = query.lower()
    for ch in ",.;:?!()[]{}\"'/\\":
        q = q.replace(ch, " ")
    words = {w for w in q.split() if w}
    stop = {
        "a", "an", "the", "and", "or", "of", "on", "in", "for", "with",
        "to", "at", "by", "is", "are", "my", "me", "please", "can", "you",
        "give", "show", "make", "build", "create", "generate", "add",
        "topology", "topologies", "network", "diagram", "example", "sample",
        "some", "any", "all", "new",
    }
    return words - stop


def taxonomy() -> Dict[str, List[str]]:
    """Return a copy of the concept -> protocols alias map for external use."""
    return {k: list(v) for k, v in _PROTOCOL_ALIASES.items()}


# Per-process caches. The blueprint library is shared across every user on
# this server process, but per-user override files must NEVER bleed into
# another user's view -- every call therefore passes through ``username``
# and hits its own slot.
#
# _repo_cache holds the stock blueprints (same bytes for every user). It
# is rebuilt only when any JSON under ``topology/ai/blueprints/`` changes
# on disk.
#
# _user_cache[username] holds that user's overrides ONLY. At query time
# we merge the repo cache with the per-user slot -- users win on name
# collision, matching the multi-user doctrine used by knowledge.md /
# devices.db / sections/.
#
# All mutations are guarded by _cache_lock so concurrent requests in
# ThreadingHTTPServer can't produce a half-built cache or cross-user
# pollution.
_repo_cache: Dict[str, Any] = {"sig": 0.0, "entries": {}}
_user_cache: Dict[str, Dict[str, Any]] = {}  # username -> {"sig": float, "entries": {...}}
_cache_lock = threading.RLock()


def _safe_json_load(path: Path) -> Optional[Dict[str, Any]]:
    """Return parsed JSON or None on any error. Never raises."""
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _iter_repo_blueprints() -> Iterable[Path]:
    """Yield every ``*.json`` under the bundled blueprint tree."""
    root = _REPO_BLUEPRINT_ROOT
    if not root.is_dir():
        return []
    paths: List[Path] = []
    for p in root.rglob("*.json"):
        if p.is_file() and p.name != "INDEX.md":
            paths.append(p)
    return sorted(paths, key=lambda q: str(q))


def _iter_user_blueprints(username: str) -> Iterable[Path]:
    """Yield every ``*.json`` under the user's personal override dir."""
    if user_store is None or not username:
        return []
    try:
        base = user_store.user_data_path(username, _USER_SUBDIR)
    except Exception:
        return []
    if not base.is_dir():
        return []
    return sorted([p for p in base.glob("*.json") if p.is_file()], key=lambda q: str(q))


def _mtime_signature(paths: Iterable[Path]) -> float:
    """Return the max mtime of the given paths (0.0 if none)."""
    mt = 0.0
    for p in paths:
        try:
            v = p.stat().st_mtime
        except OSError:
            continue
        if v > mt:
            mt = v
    return mt


def _normalise_entry(path: Path, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Turn a raw JSON blob into a {meta, payload} pair, or None if bogus.

    We insist on a non-empty ``name``, a recognised ``protocol``, and
    at least one device in ``objects`` -- every other field is
    defaulted. The ``name`` is forced to match the filename stem so
    ``load_blueprint(filename_stem)`` is always unambiguous (users
    sometimes copy a blueprint file and forget to update the name
    key; this keeps the system honest).
    """
    filename_stem = path.stem.strip()
    if not filename_stem:
        return None
    objects = raw.get("objects")
    if not isinstance(objects, list) or not objects:
        return None
    devices = [o for o in objects if isinstance(o, dict) and o.get("type") == "device"]
    if not devices:
        return None
    links = [o for o in objects if isinstance(o, dict) and o.get("type") == "link"]
    texts = [o for o in objects if isinstance(o, dict) and o.get("type") == "text"]
    shapes = [o for o in objects if isinstance(o, dict) and o.get("type") == "shape"]

    protocol = str(raw.get("protocol") or "").strip().lower() or "default"
    scale = str(raw.get("scale") or "").strip().lower() or "medium"
    if scale not in {"small", "medium", "large", "enterprise"}:
        scale = "medium"
    summary = str(raw.get("summary") or "").strip() or f"{protocol} reference topology"
    layout_hint = str(raw.get("layout_hint") or "").strip().lower() or None

    tags_raw = raw.get("tags") or []
    tags: List[str] = []
    if isinstance(tags_raw, list):
        for t in tags_raw:
            if isinstance(t, str) and t.strip():
                tags.append(t.strip().lower())

    meta = {
        "name": filename_stem,
        "protocol": protocol,
        "scale": scale,
        "summary": summary[:240],
        "tags": tags[:12],
        "layout_hint": layout_hint,
        "device_count": len(devices),
        "link_count": len(links),
        "text_count": len(texts),
        "shape_count": len(shapes),
        "path": str(path),
        # `source` lets the frontend distinguish stock vs per-user
        # blueprints in the list_blueprints response.
        "source": "user" if _USER_SUBDIR in path.parts else "repo",
    }

    payload = dict(raw)
    payload["name"] = filename_stem
    payload["protocol"] = protocol
    payload["scale"] = scale
    payload["summary"] = summary
    if layout_hint:
        payload["layout_hint"] = layout_hint
    payload["tags"] = tags
    payload["objects"] = objects
    payload["_meta"] = meta

    return {"meta": meta, "payload": payload, "path": str(path)}


def _refresh_repo_cache() -> None:
    """Rebuild the shared repo cache when any bundled JSON changed.

    The repo cache is identical for every user, so we only rebuild it
    when ``ai/blueprints/**/*.json`` mtime moves. Thread-safe.
    """
    paths = list(_iter_repo_blueprints())
    sig = _mtime_signature(paths)
    with _cache_lock:
        if _repo_cache.get("sig") == sig and _repo_cache.get("entries"):
            return
        entries: Dict[str, Dict[str, Any]] = {}
        for path in paths:
            raw = _safe_json_load(path)
            if not raw:
                continue
            entry = _normalise_entry(path, raw)
            if entry is None:
                continue
            entries[entry["meta"]["name"]] = entry
        _repo_cache["sig"] = sig
        _repo_cache["entries"] = entries


def _refresh_user_cache(username: str) -> None:
    """Rebuild this user's override cache slot when their dir changed."""
    if not username:
        return
    paths = list(_iter_user_blueprints(username))
    sig = _mtime_signature(paths)
    with _cache_lock:
        slot = _user_cache.get(username)
        if slot and slot.get("sig") == sig:
            return
        entries: Dict[str, Dict[str, Any]] = {}
        for path in paths:
            raw = _safe_json_load(path)
            if not raw:
                continue
            entry = _normalise_entry(path, raw)
            if entry is None:
                continue
            entries[entry["meta"]["name"]] = entry
        _user_cache[username] = {"sig": sig, "entries": entries}


def _merged_entries(username: str) -> Dict[str, Dict[str, Any]]:
    """Return the effective blueprint set for ``username``: repo + overrides.

    Per-user files win on name collision. Returns a new dict so callers
    can iterate safely without holding the cache lock.
    """
    _refresh_repo_cache()
    _refresh_user_cache(username) if username else None
    with _cache_lock:
        merged: Dict[str, Dict[str, Any]] = dict(_repo_cache.get("entries") or {})
        if username:
            slot = _user_cache.get(username) or {}
            for name, entry in (slot.get("entries") or {}).items():
                merged[name] = entry
        return merged


# ---------------------------------------------------------------------------
# Public surface.
# ---------------------------------------------------------------------------
def list_blueprints(
    username: str = "",
    protocol: Optional[str] = None,
    scale: Optional[str] = None,
    tags: Optional[Iterable[str]] = None,
    query: Optional[str] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """Return compact blueprint metadata matching the given filters.

    Filters are AND-combined. All filters are optional -- calling with
    no filters returns every known blueprint (up to ``limit``).

    Key behaviours (updated 2026-04-24 to close the multicast-style
    terminology gap the AI kept falling into):

      * ``protocol`` accepts BOTH specific protocol keys (``pim``,
        ``mpls-l3vpn``, ``sr-mpls``) AND concept keys from the alias
        map (``multicast``, ``dc``, ``overlay``, ``traffic-engineering``,
        ``metro``, ``l3vpn``, ...). Concept keys are transitively
        expanded so ``protocol="multicast"`` matches every PIM / MVPN /
        mLDP / IGMP blueprint via their tags or protocol field.

      * ``query`` is tokenised; each token is alias-expanded; a
        blueprint matches if ANY of its searchable fields
        (name / summary / protocol / tags) contains ANY of the
        expanded tokens. So "multicast on MPLS" hits both the PIM
        blueprints (via multicast -> pim tags) and the MVPN blueprints
        (multicast -> mvpn AND mpls -> mpls-l3vpn).

      * ``tags`` match is still a direct intersection (strict), but
        each requested tag is also alias-expanded to cover the ways
        engineers describe the same thing ("fabric" -> {clos,
        leaf-spine, evpn-vxlan, dc, ...}).

    Net effect: the AI no longer has to know the exact protocol key
    for a concept; it can fire off the concept and the loader resolves
    it.
    """
    entries = _merged_entries(username)
    out: List[Dict[str, Any]] = []

    # Expand each user-supplied tag through the alias map so
    # {"fabric"} also matches blueprints tagged only {"clos"} /
    # {"leaf-spine"} / {"evpn-vxlan"}. Preserves the original tokens
    # too so exact matches keep working.
    raw_tags = {t.strip().lower() for t in (tags or []) if isinstance(t, str) and t.strip()}
    norm_tags: set = set()
    for t in raw_tags:
        norm_tags |= _expand_aliases(t)

    norm_protocol = (protocol or "").strip().lower() or None
    proto_set: set = set()
    if norm_protocol:
        proto_set = _expand_aliases(norm_protocol)

    norm_scale = (scale or "").strip().lower() or None

    # Tokenise the free-form query and alias-expand every token. The
    # result is a flat bag of keywords we can substring-match against
    # each blueprint's searchable text blob.
    query_tokens: set = set()
    for tok in _tokenize_query(query or ""):
        query_tokens |= _expand_aliases(tok)

    for entry in entries.values():
        meta = entry["meta"]
        haystack = set()
        haystack.add(meta.get("protocol") or "")
        haystack.add(meta.get("name") or "")
        for t in (meta.get("tags") or []):
            haystack.add(str(t).lower())

        if proto_set:
            # Blueprint matches when ANY of its searchable tokens
            # appears in the expanded protocol set. Direct set
            # intersection handles the common case cleanly (e.g.
            # protocol=bgp hits blueprints with protocol="bgp" OR a
            # tag of "ibgp"/"ebgp"/"route-reflector").
            if not (proto_set & haystack):
                # Fallback: whole-word (not substring) match in name
                # or summary, so "ring" does NOT match "peering" /
                # "steering" / "sharing", and "metro" does NOT match
                # inside unrelated blueprints. Short aliases (<4 chars)
                # are excluded entirely -- they only work via the
                # direct intersection.
                long_aliases = [p for p in proto_set if len(p) >= 4]
                if not long_aliases:
                    continue
                name_lc = (meta.get("name") or "").lower()
                summary_lc = (meta.get("summary") or "").lower()
                combined = name_lc + " \x00 " + summary_lc
                boundary_hit = False
                for p in long_aliases:
                    if re.search(r"(?:^|[^a-z0-9])" + re.escape(p) + r"(?:$|[^a-z0-9])", combined):
                        boundary_hit = True
                        break
                if not boundary_hit:
                    continue

        if norm_scale and meta["scale"] != norm_scale:
            continue

        if norm_tags and not norm_tags.intersection(set(meta.get("tags") or [])):
            continue

        if query_tokens:
            # Treat query as OR across expanded tokens so broad concept
            # prompts ("show me some dc fabric blueprints") still match.
            # ALWAYS match on word boundaries -- substring `in` checks
            # leak every time ("ring" -> "peering"/"steering"/"sharing",
            # "te"   -> "route"/"site", "sr" -> "server"/"spoke").
            hay_text = " ".join([
                meta.get("name") or "",
                meta.get("summary") or "",
                meta.get("protocol") or "",
                " ".join(meta.get("tags") or []),
            ]).lower()
            matched = False
            for tok in query_tokens:
                if not tok:
                    continue
                pattern = r"(?:^|[^a-z0-9])" + re.escape(tok) + r"(?:$|[^a-z0-9])"
                if re.search(pattern, hay_text):
                    matched = True
                    break
            if not matched:
                continue

        out.append(dict(meta))
    # Stable ordering: protocol then name.
    out.sort(key=lambda m: (m.get("protocol") or "", m.get("name") or ""))
    return out[: max(1, int(limit or 200))]


def load_blueprint(name: str, username: str = "") -> Optional[Dict[str, Any]]:
    """Return the full blueprint payload for ``name`` or None if missing.

    The returned dict is a deep-copy-ish snapshot (cache-internal
    shallow copy is safe because blueprints are read-only) with:

        {
            "name":       "ibgp-full-mesh-4",
            "protocol":   "bgp",
            "scale":      "small",
            "summary":    "...",
            "tags":       [...],
            "layout_hint": "mesh",
            "objects":    [...],
            "_meta":      {...}     # same shape as list_blueprints entry
        }
    """
    if not name or not isinstance(name, str):
        return None
    entries = _merged_entries(username)
    key = name.strip()
    # Accept "bgp/ibgp-full-mesh-4" or the bare stem.
    if "/" in key:
        key = key.rsplit("/", 1)[-1]
    if key.endswith(".json"):
        key = key[:-5]
    entry = entries.get(key)
    if not entry:
        return None
    # Return a shallow copy so callers can mutate freely.
    payload = dict(entry["payload"])
    payload["objects"] = [dict(o) for o in entry["payload"].get("objects") or []]
    return payload


def reload_blueprints(username: str = "") -> Dict[str, Any]:
    """Force a reload of the blueprint cache (admin hook).

    Invalidates BOTH the shared repo cache and every per-user slot so
    that a disk edit followed by admin "Reload AI Blueprints" is
    immediately visible to every logged-in user -- not only the admin.
    Returns a small stats dict:

        {
            "ok": True,
            "count": <int>,        # entries visible to ``username``
            "path": "/abs/path/to/topology/ai/blueprints",
            "user_path": "/abs/path/to/user/override/dir" or "",
            "protocols": ["bgp", "ebgp", ..., "ospf", ...],
            "user_overrides": <int>,
        }
    """
    with _cache_lock:
        _repo_cache["sig"] = 0.0
        _repo_cache["entries"] = {}
        _user_cache.clear()
    entries = _merged_entries(username)
    protocols = sorted({
        entry["meta"]["protocol"] for entry in entries.values()
    })
    user_overrides = 0
    user_path = ""
    if username:
        if user_store is not None:
            try:
                user_path = str(user_store.user_data_path(username, _USER_SUBDIR))
            except Exception:
                user_path = ""
        with _cache_lock:
            slot = _user_cache.get(username) or {}
            user_overrides = len(slot.get("entries") or {})
    return {
        "ok": True,
        "count": len(entries),
        "path": str(_REPO_BLUEPRINT_ROOT),
        "user_path": user_path,
        "protocols": protocols,
        "user_overrides": user_overrides,
    }


def blueprint_summary_for_prompt(username: str = "", limit: int = 80) -> str:
    """Return a compact text block for splicing into the system prompt.

    Lists every blueprint grouped by protocol AND emits a short
    terminology bridge so the model never again says "I couldn't find
    any multicast blueprints" just because the literal string
    "multicast" isn't a top-level protocol in the catalog.

    Shape (deterministic, ~2-3 KB so it fits the token budget):

        ## Blueprints available
          - bgp: ebgp-2as-transit, ibgp-full-mesh-4, ...
          - evpn-vxlan: 2spine-4leaf-anycast-gw, ...
          ...

        ## Concept -> protocol map (use these when the user asks for a
        ## use case, not a specific protocol):
          - multicast -> pim, mvpn, mldp, igmp
          - dc / fabric -> clos, evpn-vxlan, leaf-spine
          - traffic-engineering -> sr-te, rsvp-te
          - overlay -> evpn, vxlan, mvpn, ibgp
          ...

    The model is expected to call
    ``list_blueprints(protocol="multicast")`` directly -- the loader
    now expands concept keys to the underlying protocols.
    """
    entries = list_blueprints(username=username, limit=max(1, int(limit or 80)))
    if not entries:
        return ""
    buckets: Dict[str, List[str]] = {}
    for e in entries:
        buckets.setdefault(e["protocol"], []).append(e["name"])
    lines: List[str] = ["## Blueprints available"]
    for proto in sorted(buckets.keys()):
        names = buckets[proto]
        lines.append(f"  - {proto}: " + ", ".join(sorted(names)))

    # Concept bridge. We keep this hand-picked rather than dumping the
    # full alias map because only a handful of concepts actually need
    # the hint; the rest resolve fine via query tokenisation.
    lines.append("")
    lines.append(
        "## Concept -> protocol map (pass the concept key as "
        "`protocol=` to `list_blueprints` -- the loader expands it)"
    )
    hints = [
        ("multicast", "pim, mvpn, mldp, igmp"),
        ("dc / fabric / leaf-spine", "clos, evpn-vxlan"),
        ("overlay", "evpn, vxlan, mvpn, ibgp"),
        ("underlay", "ospf, isis, ebgp"),
        ("l3vpn / vrf", "mpls-l3vpn"),
        ("l2vpn", "vpls, vpws, pseudowire, epl, evpl"),
        ("traffic-engineering / te", "sr-te, rsvp-te"),
        ("metro / ring", "ring (g8032, erps)"),
        ("dci / wan", "dci, ebgp, mpls"),
        ("enterprise / campus", "campus (3-tier mlag)"),
        ("qos / diffserv / hqos", "qos"),
        ("ha / vrrp / bfd / redundancy", "ha"),
        ("vpn / ipsec / gre / dmvpn / site-to-site", "vpn"),
        ("nat / cgnat / nat64", "nat"),
        ("l2 / stp / rstp / mstp / spanning-tree", "l2, stp"),
        ("security / flowspec / rtbh / ddos / rpki", "security"),
        ("broadband / bng / pppoe / subscriber", "broadband"),
        ("mobile / 5g / xhaul / backhaul / csr", "mobile"),
        ("telemetry / gnmi / netflow / monitoring", "telemetry"),
        ("sdwan / cloud / sase", "sdwan, cloud"),
        ("drivenets / dnaas / disaggregated", "drivenets (ncp/ncf)"),
    ]
    for concept, expansion in hints:
        lines.append(f"  - {concept} -> {expansion}")
    lines.append("")
    lines.append(
        "If the user asks for something that is NOT a literal protocol "
        "name (e.g. 'multicast', 'DC fabric', 'traffic engineering'), "
        "resolve it through the concept map first. If still no exact "
        "blueprint, COMPOSE from related ones: e.g. 'multicast on "
        "MPLS' = load mvpn-mpls-2pe; 'IGP + multicast' = load an "
        "ospf/isis blueprint and add PIM-enabled links."
    )
    return "\n".join(lines)
