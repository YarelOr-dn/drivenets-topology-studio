#!/usr/bin/env python3
"""
Device profile builder -- the device-agnostic layer.

Eliminates hardcoded assumptions like:
    - ASN = 1234567 (PE-1 specific)
    - Update-source format = "ge400-0/0/<X>" (PE-1 specific)
    - Parent interface "ge400-0/0" (PE-1 specific)
    - Router-id, BGP neighbors, EVPN instances (per-device)

Instead, the orchestrator builds a `DeviceProfile` once per run by:
    1. Looking up the device in `~/SCALER/db/devices.json` (hostname / IP / alias)
    2. Live-discovering ASN, router-id, EVPN instances, sub-ifs, BGP peers
    3. Computing free inner VLANs per outer VLAN (collision-free pool)
    4. Detecting parent interface naming pattern (NCP vs CL, ge25-X vs ge100-X vs ge400-X)

The profile is then passed to every helper that needs device-specific values.
This way the same orchestrator runs on PE-1, PE-4, RR-SA-2, R7-Natan -- whatever
the user picks at runtime.

Usage:
    from shared.device_profile import build_device_profile

    profile = build_device_profile(run_show, "PE-1")  # or "100.64.4.200"
    print(profile.bgp_asn)              # 1234567 (discovered)
    print(profile.parent_interface)     # "ge400-0/0" (discovered)
    print(profile.free_inner_vlans(214, count=3))  # [10, 11, 12]

    # Pass to existing helpers
    new_subif = profile.subif_for(outer=214, inner=10)  # "ge400-0/0.10"
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

RunShowFn = Callable[[str, str], str]


# Common device DB locations -- checked in order, first existing wins.
_DEVICE_DB_PATHS = [
    Path.home() / "SCALER" / "db" / "devices.json",
    Path("/home/dn/drivenets-topology-studio/scaler/db/devices.json"),
    Path(__file__).resolve().parent.parent.parent.parent / "db" / "devices.json",
]


# ---------------------------------------------------------------------------
# Helpers for parsing DNOS show output (kept narrow + tolerant)
# ---------------------------------------------------------------------------

_BGP_ASN_RE = re.compile(r"\bbgp\s+(\d+)\b")
_ROUTER_ID_RE = re.compile(r"router-id\s+([\d\.]+)", re.IGNORECASE)
_SUBIF_RE = re.compile(r"^([a-z]+\d+(?:-\d+/\d+/\d+)?)\.(\d+)\b")
_VLAN_TAGS_RE = re.compile(
    r"vlan-tags\s+outer-tag\s+(\d+)\s+inner-tag\s+(\d+)", re.IGNORECASE
)
_VLAN_ID_RE = re.compile(r"\bvlan-id\s+(\d+)\b", re.IGNORECASE)
_IP_PREFIX_RE = re.compile(r"ipv4-address\s+([\d\.]+/\d+)", re.IGNORECASE)
_EVPN_INSTANCE_RE = re.compile(
    r"network-services\s+evpn\s+instance\s+(\S+)", re.IGNORECASE
)
_NEIGHBOR_RE = re.compile(r"neighbor\s+([\d\.a-fA-F:]+)\s+remote-as\s+(\d+)",
                          re.IGNORECASE)


# ---------------------------------------------------------------------------
# Profile dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SubInterface:
    """A discovered sub-interface on the device.

    Captures everything the orchestrator might need to build new sub-ifs in
    the same parent or to pick a free inner VLAN.
    """
    name: str                       # 'ge400-0/0/5.10'
    parent: str                     # 'ge400-0/0/5'
    outer_vlan: Optional[int] = None  # from vlan-id or vlan-tags outer
    inner_vlan: Optional[int] = None  # from vlan-tags inner; None if single-tagged
    ipv4_address: Optional[str] = None  # 'a.b.c.d/30'
    vrf: Optional[str] = None       # 'default' / 'ALPHA' / etc.
    admin_up: Optional[bool] = None
    oper_up: Optional[bool] = None


@dataclass
class BgpNeighbor:
    """A configured BGP neighbor on the device."""
    address: str                    # peer IP
    remote_as: int
    address_families: List[str] = field(default_factory=list)
    update_source: Optional[str] = None


@dataclass
class DeviceProfile:
    """Device-agnostic profile -- one per (device, run).

    All fields are populated either from `devices.json` (static) or live
    discovery (dynamic). Helpers use this profile instead of hardcoding
    device-specific values.
    """
    # Static identity (from devices.json)
    device_id: str = ""             # 'pe1' (DB primary key)
    hostname: str = ""              # 'PE-1' (used as `device` in run_show calls)
    ip: str = ""                    # mgmt IP
    platform: str = ""              # 'NCP' / 'CL-86'
    aliases: List[str] = field(default_factory=list)

    # Discovered routing identity
    bgp_asn: Optional[int] = None
    router_id: Optional[str] = None

    # Discovered topology
    sub_interfaces: List[SubInterface] = field(default_factory=list)
    bgp_neighbors: List[BgpNeighbor] = field(default_factory=list)
    evpn_instances: List[str] = field(default_factory=list)

    # Per-outer-VLAN: set of inner VLANs already in use (so callers can avoid
    # collisions when allocating new sub-ifs).
    inner_vlans_in_use: Dict[int, Set[int]] = field(default_factory=dict)

    # Detected parent interface pattern (for new sub-if creation).
    # E.g. on PE-1 this is 'ge400-0/0/5'; on PE-4 it might be 'ge100-18/0/6'.
    parent_interface: Optional[str] = None

    # Discovery status (so callers know what failed and can fall back).
    discovery_warnings: List[str] = field(default_factory=list)

    def find_subif(self, outer_vlan: int, inner_vlan: Optional[int] = None
                   ) -> Optional[SubInterface]:
        """Return the first sub-interface matching outer (and optional inner) VLAN."""
        for s in self.sub_interfaces:
            if s.outer_vlan != outer_vlan:
                continue
            if inner_vlan is not None and s.inner_vlan != inner_vlan:
                continue
            return s
        return None

    def find_neighbor(self, peer_ip: str) -> Optional[BgpNeighbor]:
        for n in self.bgp_neighbors:
            if n.address == peer_ip:
                return n
        return None

    def free_inner_vlans(self, outer_vlan: int, count: int = 1,
                         start: int = 10, end: int = 4090,
                         reserved: Optional[Set[int]] = None) -> List[int]:
        """Return up to `count` inner VLANs in [start, end] not already used.

        Reserved set defaults to {0, 1, 999, 4095} to dodge mgmt + edge tags.
        """
        if reserved is None:
            reserved = {0, 1, 999, 4095}
        used = self.inner_vlans_in_use.get(outer_vlan, set()) | reserved
        out: List[int] = []
        for v in range(start, end + 1):
            if v in used:
                continue
            out.append(v)
            if len(out) >= count:
                break
        return out

    def subif_for(self, outer: int, inner: int,
                  parent: Optional[str] = None) -> str:
        """Build a canonical sub-if name for the device's parent interface.

        DNOS convention: <parent>.<inner_vlan> when Q-in-Q with separate
        vlan-tags lines, OR <parent>.<vlan-id> for single-tag.
        We use the inner VLAN as the sub-if numeric suffix so it stays unique
        per outer VLAN -- the orchestrator's existing convention.
        """
        p = parent or self.parent_interface
        if not p:
            raise ValueError(
                "DeviceProfile has no parent_interface and none was supplied. "
                "Discovery may have failed -- check profile.discovery_warnings."
            )
        return f"{p}.{inner}"

    def as_dict(self) -> Dict[str, object]:
        """JSON-friendly snapshot for evidence dumps."""
        return {
            "device_id": self.device_id,
            "hostname": self.hostname,
            "ip": self.ip,
            "platform": self.platform,
            "aliases": list(self.aliases),
            "bgp_asn": self.bgp_asn,
            "router_id": self.router_id,
            "parent_interface": self.parent_interface,
            "sub_interface_count": len(self.sub_interfaces),
            "bgp_neighbor_count": len(self.bgp_neighbors),
            "evpn_instance_count": len(self.evpn_instances),
            "inner_vlans_in_use": {
                str(k): sorted(v) for k, v in self.inner_vlans_in_use.items()
            },
            "discovery_warnings": list(self.discovery_warnings),
        }


# ---------------------------------------------------------------------------
# DB lookup
# ---------------------------------------------------------------------------

def _load_device_db() -> List[Dict]:
    for p in _DEVICE_DB_PATHS:
        if p.is_file():
            try:
                data = json.loads(p.read_text())
                return list(data.get("devices") or data or [])
            except Exception:
                continue
    return []


def _match_device_record(records: List[Dict], target: str) -> Optional[Dict]:
    """Match by id / hostname / alias / ip (case-insensitive on hostname/alias)."""
    t = target.strip()
    t_low = t.lower()
    for rec in records:
        if rec.get("id", "") == t:
            return rec
        if str(rec.get("hostname", "")).lower() == t_low:
            return rec
        if rec.get("ip", "") == t:
            return rec
        for alias in rec.get("aliases", []) or []:
            if str(alias).lower() == t_low:
                return rec
    return None


# ---------------------------------------------------------------------------
# Live discovery (best-effort -- never raises; logs warnings to profile)
# ---------------------------------------------------------------------------

def _safe_show(run_show: RunShowFn, device: str, cmd: str,
               profile: DeviceProfile) -> str:
    try:
        return run_show(device, cmd) or ""
    except Exception as exc:
        profile.discovery_warnings.append(
            f"show '{cmd}' raised {exc.__class__.__name__}: {exc}"
        )
        return ""


def _discover_bgp_identity(run_show: RunShowFn, device: str,
                           profile: DeviceProfile) -> None:
    """Populate `bgp_asn` + `router_id` + `bgp_neighbors` from running config."""
    cfg = _safe_show(run_show, device,
                     "show config | flatten | no-more", profile)

    if not cfg:
        profile.discovery_warnings.append("no BGP config returned")
        return

    asn_m = _BGP_ASN_RE.search(cfg)
    if asn_m:
        try:
            profile.bgp_asn = int(asn_m.group(1))
        except ValueError:
            pass

    rid_m = _ROUTER_ID_RE.search(cfg)
    if rid_m:
        profile.router_id = rid_m.group(1)

    seen: Set[str] = set()
    for nm in _NEIGHBOR_RE.finditer(cfg):
        peer = nm.group(1)
        if peer in seen:
            continue
        seen.add(peer)
        try:
            remote_as = int(nm.group(2))
        except ValueError:
            continue
        profile.bgp_neighbors.append(
            BgpNeighbor(address=peer, remote_as=remote_as)
        )


def _discover_subinterfaces(run_show: RunShowFn, device: str,
                            profile: DeviceProfile) -> None:
    """Parse `show config interfaces | flatten` for sub-ifs + VLAN tags + IPs."""
    cfg = _safe_show(run_show, device,
                     "show config interfaces | flatten | no-more", profile)
    if not cfg:
        cfg = _safe_show(run_show, device,
                         "show config interfaces | no-more", profile)
    if not cfg:
        profile.discovery_warnings.append("no interfaces config returned")
        return

    # Flatten lines look like:
    #   interfaces ge400-0/0/5.10 admin-state enabled
    #   interfaces ge400-0/0/5.10 vlan-tags outer-tag 214 inner-tag 10
    #   interfaces ge400-0/0/5.10 ipv4-address 19.19.19.10/30
    by_subif: Dict[str, SubInterface] = {}
    for line in cfg.splitlines():
        if "interfaces " not in line:
            continue
        # Strip leading 'interfaces '
        i = line.find("interfaces ")
        chunk = line[i + len("interfaces "):].strip()
        head, _, _ = chunk.partition(" ")
        m = _SUBIF_RE.match(head)
        if not m:
            continue
        parent, suffix = m.group(1), int(m.group(2))
        sub_name = f"{parent}.{suffix}"
        sub = by_subif.get(sub_name)
        if sub is None:
            sub = SubInterface(name=sub_name, parent=parent)
            by_subif[sub_name] = sub
        rest = chunk[m.end():]

        vt = _VLAN_TAGS_RE.search(rest)
        if vt:
            sub.outer_vlan = int(vt.group(1))
            sub.inner_vlan = int(vt.group(2))
        else:
            vid = _VLAN_ID_RE.search(rest)
            if vid:
                sub.outer_vlan = int(vid.group(1))

        ipm = _IP_PREFIX_RE.search(rest)
        if ipm:
            sub.ipv4_address = ipm.group(1)

    profile.sub_interfaces = list(by_subif.values())

    # Build inner-vlan-in-use map
    for sub in profile.sub_interfaces:
        if sub.outer_vlan is None or sub.inner_vlan is None:
            continue
        profile.inner_vlans_in_use.setdefault(sub.outer_vlan, set()).add(
            sub.inner_vlan
        )


def _detect_parent_interface(profile: DeviceProfile) -> None:
    """Infer the most common parent interface (the 'big port' the test uses).

    Strategy: the parent with the most sub-interfaces is almost always the
    DNAAS-facing high-bandwidth port. Tie-break on numeric suffix (prefer
    higher port-numbered parents).
    """
    if not profile.sub_interfaces:
        return
    counts: Dict[str, int] = {}
    for s in profile.sub_interfaces:
        counts[s.parent] = counts.get(s.parent, 0) + 1
    best = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    profile.parent_interface = best[0][0]


def _discover_evpn_instances(run_show: RunShowFn, device: str,
                             profile: DeviceProfile) -> None:
    """List EVPN instance names from `show evpn`."""
    out = _safe_show(run_show, device, "show evpn | no-more", profile)
    instances: List[str] = []
    for line in out.splitlines():
        line = line.strip()
        if not line or line.startswith("|") and not line[1:].strip():
            continue
        # Look for typical 'Instance name <X>' or summary table entries
        if line.lower().startswith("instance"):
            parts = line.split()
            if len(parts) >= 2:
                instances.append(parts[-1])
    if instances:
        profile.evpn_instances = sorted(set(instances))
        return

    # Fallback: parse from config
    cfg = _safe_show(run_show, device,
                     "show config network-services evpn | flatten | no-more",
                     profile)
    seen: Set[str] = set()
    for em in _EVPN_INSTANCE_RE.finditer(cfg or ""):
        seen.add(em.group(1))
    profile.evpn_instances = sorted(seen)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def build_device_profile(
    run_show: RunShowFn,
    device: str,
    skip_live_discovery: bool = False,
) -> DeviceProfile:
    """Build a DeviceProfile for `device` (hostname, alias, id, or IP).

    Steps:
      1. Look up the static record in devices.json (best-effort).
      2. Optionally live-discover ASN, router-id, sub-ifs, BGP neighbors,
         EVPN instances using `run_show`.
      3. Detect parent interface pattern.

    Never raises -- on partial failure, returns whatever was discovered with
    warnings appended to `profile.discovery_warnings`.
    """
    records = _load_device_db()
    rec = _match_device_record(records, device) if records else None

    profile = DeviceProfile(
        device_id=rec.get("id", "") if rec else "",
        hostname=(rec.get("hostname") if rec else device) or device,
        ip=(rec.get("ip") if rec else "") or "",
        platform=(rec.get("platform") if rec else "") or "",
        aliases=list(rec.get("aliases") or []) if rec else [],
    )

    if rec is None:
        profile.discovery_warnings.append(
            f"no devices.json record found for '{device}' -- using as hostname"
        )

    if skip_live_discovery:
        return profile

    # Use the resolved hostname for run_show (Network Mapper expects the name
    # the device is registered under).
    target = profile.hostname or device

    _discover_bgp_identity(run_show, target, profile)
    _discover_subinterfaces(run_show, target, profile)
    _detect_parent_interface(profile)
    _discover_evpn_instances(run_show, target, profile)

    return profile


__all__ = [
    "DeviceProfile",
    "SubInterface",
    "BgpNeighbor",
    "build_device_profile",
]
