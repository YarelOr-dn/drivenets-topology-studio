#!/usr/bin/env python3
"""Parse DNOS CLI output for EVPN MAC mobility tests.

Covers: basic MAC table, detail view (flags), suppress list,
forwarding-table (NCP flags), loop-prevention state,
dnos-internal MAC mobility counters, bestpath, ghost MACs, FIB state.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b\[\d*F")
MAC_ADDR_RE = re.compile(
    r"(?:[0-9a-f]{2}:){5}[0-9a-f]{2}",
    re.IGNORECASE,
)


def strip_ansi(text: str) -> str:
    if not isinstance(text, str):
        return text
    return _ANSI_RE.sub("", text)


def parse_bgp_l2vpn_evpn_summary(output: str) -> Dict[str, Any]:
    """Parse 'show bgp l2vpn evpn summary' output.

    When a neighbor is ESTABLISHED, the last column is the received prefix count.
    """
    result: Dict[str, Any] = {"neighbors": [], "total": 0, "established": 0, "total_prefixes": 0}
    for line in strip_ansi(output).splitlines():
        parts = line.split()
        if len(parts) >= 10 and re.match(r"\d+\.\d+\.\d+\.\d+", parts[0]):
            state = parts[-1]
            is_established = state.isdigit()
            pfx_count = int(state) if is_established else 0
            neighbor = {
                "ip": parts[0],
                "as": parts[2],
                "state": pfx_count if is_established else state,
                "established": is_established,
                "prefix_count": pfx_count,
            }
            result["neighbors"].append(neighbor)
            result["total"] += 1
            if is_established:
                result["established"] += 1
                result["total_prefixes"] += pfx_count
    return result


def parse_evpn_mac_count(output: str) -> int:
    """Count MAC-looking lines in 'show evpn mac-table' style output."""
    count = 0
    for line in strip_ansi(output).splitlines():
        if MAC_ADDR_RE.search(line):
            count += 1
    return count


def parse_evpn_mac_entries(output: str) -> List[Dict[str, str]]:
    """
    Best-effort parse of MAC table lines into dicts with mac, source hints.

    DNOS column layout varies; we capture MAC and keywords (Local, BGP, PW, sticky).
    """
    entries: List[Dict[str, str]] = []
    for line in strip_ansi(output).splitlines():
        m = MAC_ADDR_RE.search(line)
        if not m:
            continue
        mac = m.group(0).lower()
        upper = line.upper()
        source = "unknown"
        if "LOCAL" in upper and "BGP" not in upper.split()[0:3]:
            source = "local"
        if "BGP" in upper or "EVPN" in upper or "REMOTE" in upper:
            source = "bgp"
        if "PW" in upper or "PSEUDO" in upper or "VPLS" in upper:
            source = "pw"
        sticky = "sticky" in line.lower() or "STICKY" in upper
        # source_aliases: recipes may use "ac" to mean "local AC-learned"
        source_aliases = [source]
        if source == "local":
            source_aliases.append("ac")
        entries.append(
            {
                "mac": mac,
                "line": line.strip(),
                "source_hint": source,
                "source_aliases": source_aliases,
                "sticky": str(sticky).lower(),
            }
        )
    return entries


def parse_system_nodes(output: str) -> Dict[str, Any]:
    """Parse 'show system' for NCC hints (best-effort)."""
    nodes: Dict[str, str] = {}
    active_ncc: Optional[str] = None
    standby_ncc: Optional[str] = None
    text = strip_ansi(output).lower()
    for line in text.splitlines():
        if "ncc" in line and "active" in line:
            match = re.search(r"ncc[- ]?(\d+)", line)
            if match:
                nid = match.group(1)
                if "standby" in line:
                    standby_ncc = nid
                    nodes[f"NCC-{nid}"] = "standby-up"
                elif "active" in line:
                    active_ncc = nid
                    nodes[f"NCC-{nid}"] = "active-up"
    return {
        "nodes": nodes,
        "active_ncc": active_ncc,
        "standby_ncc": standby_ncc,
        "is_cluster_hint": standby_ncc is not None or "standby" in text,
    }


def parse_evpn_instance_names(summary_output: str) -> List[str]:
    """Extract EVPN instance names from 'show evpn summary' (heuristic)."""
    names: List[str] = []
    for line in strip_ansi(summary_output).splitlines():
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("-"):
            continue
        # Lines like "instance foo" or table rows with instance column
        if re.match(r"^[A-Za-z0-9_.-]+$", line_stripped) and len(line_stripped) < 64:
            if line_stripped.lower() not in ("evpn", "instance", "name", "summary"):
                names.append(line_stripped)
    return list(dict.fromkeys(names))


def extract_first_mac(output: str) -> Optional[str]:
    m = MAC_ADDR_RE.search(strip_ansi(output))
    return m.group(0).lower() if m else None


# ---------------------------------------------------------------------------
# Dataclasses for structured parse results
# ---------------------------------------------------------------------------

@dataclass
class MacDetailEntry:
    """One MAC from 'show evpn mac-table detail instance <name>'."""
    mac: str
    sequence: Optional[int] = None
    flags: List[str] = field(default_factory=list)
    source: str = "unknown"
    interface: Optional[str] = None
    next_hop: Optional[str] = None
    esi: Optional[str] = None
    aging_remaining: Optional[int] = None
    raw_block: str = ""


@dataclass
class MacSuppressEntry:
    """One MAC from 'show evpn mac-table instance <name> suppress'."""
    mac: str
    reason: str = "unknown"
    timer_remaining: Optional[int] = None
    instance: Optional[str] = None


@dataclass
class FwdTableEntry:
    """One MAC from 'show evpn forwarding-table mac-address-table'."""
    mac: str
    ncp_id: Optional[str] = None
    flags: str = ""
    fwd_state: str = "unknown"
    interface: Optional[str] = None


@dataclass
class LoopPreventionMacEntry:
    """Per-MAC entry from 'show evpn instance <name> loop-prevention mac-table'."""
    mac: str
    move_count: int = 0
    state: str = "normal"
    last_move_time: Optional[str] = None
    restore_timer: Optional[int] = None


@dataclass
class LoopPreventionIfEntry:
    """Per-interface from 'show evpn instance <name> loop-prevention interface'."""
    interface: str
    local_loop_count: int = 0
    state: str = "enabled"


@dataclass
class FibMacEntry:
    """FIB-level MAC from 'show dnos-internal routing fib-manager database evpn'."""
    mac: str
    service_instance: str = ""
    fib_state: str = "unknown"
    interface: Optional[str] = None


# ---------------------------------------------------------------------------
# A1: Deep MAC table parsers (detail, suppress, forwarding-table)
# ---------------------------------------------------------------------------

_SEQ_RE = re.compile(r"seq(?:uence)?[\s:=]+(\d+)", re.IGNORECASE)
_AGING_RE = re.compile(r"aging[\s:-]+(\d+)", re.IGNORECASE)
_ESI_RE = re.compile(r"esi[\s:]+([0-9a-f:.-]{23,})", re.IGNORECASE)
_NEXTHOP_RE = re.compile(r"next[- ]?hop[\s:]+(\d+\.\d+\.\d+\.\d+)", re.IGNORECASE)
_IFACE_RE = re.compile(
    r"(?:interface|port|ac)[\s:]+(\S+)", re.IGNORECASE
)
_FLAG_MAP = {
    "local": "L", "remote": "R", "static": "S",
    "sticky": "K", "frozen": "F", "duplicate": "D",
    "suppressed": "F", "mobility": "M", "moved": "M",
    "vpls": "P", "pw": "P",
}


def parse_mac_detail(output: str) -> List[MacDetailEntry]:
    """Parse 'show evpn mac-table detail instance <name> | no-more'.

    Splits output into per-MAC blocks and extracts sequence, flags,
    source, interface, next-hop, ESI, aging timer.
    """
    text = strip_ansi(output)
    entries: List[MacDetailEntry] = []

    blocks = re.split(r"(?=(?:[0-9a-f]{2}:){5}[0-9a-f]{2})", text, flags=re.IGNORECASE)

    for block in blocks:
        m = MAC_ADDR_RE.search(block)
        if not m:
            continue
        mac = m.group(0).lower()
        lower = block.lower()

        seq_m = _SEQ_RE.search(block)
        aging_m = _AGING_RE.search(block)
        esi_m = _ESI_RE.search(block)
        nh_m = _NEXTHOP_RE.search(block)
        iface_m = _IFACE_RE.search(block)

        flags: List[str] = []
        for keyword, flag_char in _FLAG_MAP.items():
            if keyword in lower and flag_char not in flags:
                flags.append(flag_char)

        source = "unknown"
        if "local" in lower and "remote" not in lower:
            source = "local"
        elif any(kw in lower for kw in ("bgp", "evpn", "remote")):
            source = "bgp"
        elif any(kw in lower for kw in ("pw", "pseudo", "vpls")):
            source = "pw"

        entries.append(MacDetailEntry(
            mac=mac,
            sequence=int(seq_m.group(1)) if seq_m else None,
            flags=flags,
            source=source,
            interface=iface_m.group(1) if iface_m else None,
            next_hop=nh_m.group(1) if nh_m else None,
            esi=esi_m.group(1) if esi_m else None,
            aging_remaining=int(aging_m.group(1)) if aging_m else None,
            raw_block=block.strip(),
        ))

    return entries


def parse_mac_suppress(output: str) -> List[MacSuppressEntry]:
    """Parse 'show evpn mac-table instance <name> suppress | no-more'.

    Extracts suppressed MACs with reason and timer.
    """
    text = strip_ansi(output)
    entries: List[MacSuppressEntry] = []
    _REASON_RE = re.compile(
        r"(rapid[- ]?move|duplicate|loop|frozen|flap)", re.IGNORECASE
    )
    _TIMER_RE = re.compile(r"timer[\s:]+(\d+)", re.IGNORECASE)
    _INST_RE = re.compile(r"instance[\s:]+(\S+)", re.IGNORECASE)

    for line in text.splitlines():
        m = MAC_ADDR_RE.search(line)
        if not m:
            continue
        mac = m.group(0).lower()
        reason_m = _REASON_RE.search(line)
        timer_m = _TIMER_RE.search(line)
        inst_m = _INST_RE.search(line)

        reason = "unknown"
        if reason_m:
            raw = reason_m.group(1).lower().replace("-", "_").replace(" ", "_")
            if "rapid" in raw or "flap" in raw:
                reason = "rapid-move"
            elif "duplicate" in raw:
                reason = "duplicate"
            elif "loop" in raw:
                reason = "loop"
            elif "frozen" in raw:
                reason = "frozen"

        entries.append(MacSuppressEntry(
            mac=mac,
            reason=reason,
            timer_remaining=int(timer_m.group(1)) if timer_m else None,
            instance=inst_m.group(1) if inst_m else None,
        ))

    return entries


def parse_forwarding_table_flags(output: str) -> List[FwdTableEntry]:
    """Parse 'show evpn forwarding-table mac-address-table instance <name> | no-more'.

    Handles two output formats:
      A) Pipe-delimited table (DNOS 26.x):
         | (*)00:de:ad:00:01:01 | bundle-100.2150 | ... | L |
      B) Whitespace-separated (older format):
         00:de:ad:00:01:01 forwarding bundle-100.2150 L
    """
    text = strip_ansi(output)
    entries: List[FwdTableEntry] = []
    _STATE_RE = re.compile(
        r"(forwarding|filtering|blocking|blocked|drop)", re.IGNORECASE
    )

    current_ncp = None
    for line in text.splitlines():
        ncp_header = re.match(r'NCP[-\s]?ID\s+(\d+)', line, re.IGNORECASE)
        if ncp_header:
            current_ncp = ncp_header.group(1)
            continue

        m = MAC_ADDR_RE.search(line)
        if not m:
            continue
        mac = m.group(0).lower()

        is_active = '(*)' in line[:line.find(mac) + len(mac)]
        fwd_state = "unknown"
        iface = None
        flags_raw = ""

        if '|' in line:
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if len(cells) >= 2:
                iface_cell = cells[1] if len(cells) > 1 else ""
                if re.match(r'(ge|bundle|lag|eth|lo|irb)', iface_cell, re.IGNORECASE):
                    iface = iface_cell
            if len(cells) >= 5:
                flags_raw = cells[-1].strip()
            fwd_state = "forwarding" if is_active else "filtering"
        else:
            state_m = _STATE_RE.search(line)
            if state_m:
                raw = state_m.group(1).lower()
                if raw in ("blocking", "blocked", "drop"):
                    fwd_state = "blocking"
                elif raw == "filtering":
                    fwd_state = "filtering"
                else:
                    fwd_state = "forwarding"
            parts = line.split()
            for p in parts:
                if re.match(r"^[A-Z]{1,6}$", p) and p not in ("MAC", "NCP"):
                    flags_raw = p
                    break
            for p in parts:
                if re.match(r"^(ge|bundle|lag|eth|lo|irb)", p, re.IGNORECASE):
                    iface = p
                    break

        entries.append(FwdTableEntry(
            mac=mac,
            ncp_id=current_ncp,
            flags=flags_raw,
            fwd_state=fwd_state,
            interface=iface,
        ))

    return entries


# ---------------------------------------------------------------------------
# B1: Loop prevention parsers
# ---------------------------------------------------------------------------

def parse_loop_prevention_mac_table(output: str) -> List[LoopPreventionMacEntry]:
    """Parse 'show evpn instance <name> loop-prevention mac-table | no-more'."""
    text = strip_ansi(output)
    entries: List[LoopPreventionMacEntry] = []
    _MOVE_CNT_RE = re.compile(r"move[- ]?count[\s:]+(\d+)", re.IGNORECASE)
    _STATE_RE = re.compile(
        r"(normal|suppressed|frozen|blocked|duplicate)", re.IGNORECASE
    )
    _TIME_RE = re.compile(
        r"last[- ]?move[\s:]+(\S+\s*\S*)", re.IGNORECASE
    )
    _RESTORE_RE = re.compile(r"restore[\s:-]+(\d+)", re.IGNORECASE)

    for line in text.splitlines():
        m = MAC_ADDR_RE.search(line)
        if not m:
            continue
        mac = m.group(0).lower()
        cnt_m = _MOVE_CNT_RE.search(line)
        state_m = _STATE_RE.search(line)
        time_m = _TIME_RE.search(line)
        restore_m = _RESTORE_RE.search(line)

        move_count = int(cnt_m.group(1)) if cnt_m else 0
        if not cnt_m:
            nums = re.findall(r"\b(\d+)\b", line)
            for n in nums:
                val = int(n)
                if 1 <= val <= 100000:
                    move_count = val
                    break

        entries.append(LoopPreventionMacEntry(
            mac=mac,
            move_count=move_count,
            state=state_m.group(1).lower() if state_m else "normal",
            last_move_time=time_m.group(1).strip() if time_m else None,
            restore_timer=int(restore_m.group(1)) if restore_m else None,
        ))

    return entries


def parse_loop_prevention_interface(output: str) -> List[LoopPreventionIfEntry]:
    """Parse 'show evpn instance <name> loop-prevention interface | no-more'."""
    text = strip_ansi(output)
    entries: List[LoopPreventionIfEntry] = []
    _LOOP_CNT_RE = re.compile(r"(?:loop[- ]?count|loops?)[\s:]+(\d+)", re.IGNORECASE)
    _STATE_RE = re.compile(r"(enabled|disabled|suppressed|blocked)", re.IGNORECASE)

    for line in text.splitlines():
        iface_m = re.search(
            r"(ge\S+|bundle\S+|lag\S+|eth\S+)", line, re.IGNORECASE
        )
        if not iface_m:
            continue
        cnt_m = _LOOP_CNT_RE.search(line)
        state_m = _STATE_RE.search(line)
        entries.append(LoopPreventionIfEntry(
            interface=iface_m.group(1),
            local_loop_count=int(cnt_m.group(1)) if cnt_m else 0,
            state=state_m.group(1).lower() if state_m else "enabled",
        ))

    return entries


def parse_loop_prevention_local(output: str) -> Dict[str, Any]:
    """Parse 'show evpn instance <name> loop-prevention local | no-more'.

    Returns dict with admin_state, detection counts, and per-MAC data
    if the output contains MAC-level local loop info.
    """
    text = strip_ansi(output)
    result: Dict[str, Any] = {
        "admin_state": "unknown",
        "total_local_loops": 0,
        "macs": [],
    }

    for line in text.splitlines():
        lower = line.lower().strip()
        if "admin" in lower and ("enabled" in lower or "disabled" in lower):
            result["admin_state"] = "enabled" if "enabled" in lower else "disabled"
        cnt_m = re.search(r"total[\s:-]+(\d+)", lower)
        if cnt_m:
            result["total_local_loops"] = int(cnt_m.group(1))
        m = MAC_ADDR_RE.search(line)
        if m:
            result["macs"].append(m.group(0).lower())

    return result


# ---------------------------------------------------------------------------
# C1: dnos-internal parsers (mobility counter, bestpath, ghost, FIB)
# ---------------------------------------------------------------------------

def parse_mac_mobility_redis_count(output: str) -> Dict[str, int]:
    """Parse 'show dnos-internal routing evpn mac-mobility-redis-count | no-more'.

    Extracts move counters. Field names are best-effort from key-value lines.
    """
    text = strip_ansi(output)
    result: Dict[str, int] = {
        "total_moves": 0,
        "local_moves": 0,
        "remote_moves": 0,
    }

    for line in text.splitlines():
        lower = line.lower().strip()
        num_m = re.search(r"(\d+)\s*$", line.strip())
        if not num_m:
            continue
        val = int(num_m.group(1))
        if "total" in lower:
            result["total_moves"] = val
        elif "local" in lower:
            result["local_moves"] = val
        elif "remote" in lower:
            result["remote_moves"] = val
        elif not any(result.values()):
            result["total_moves"] = val

    return result


def parse_bestpath_compare(output: str) -> Dict[str, Any]:
    """Parse 'show dnos-internal routing evpn instance <name>
    mac-table bestpath-compare mac <mac> | no-more'.

    Returns bestpath decision details.
    """
    text = strip_ansi(output)
    result: Dict[str, Any] = {
        "winner": None,
        "reason": None,
        "sequence_local": None,
        "sequence_remote": None,
        "paths": [],
    }

    for line in text.splitlines():
        lower = line.lower().strip()
        if "winner" in lower or "best" in lower:
            parts = line.split(":", 1)
            if len(parts) == 2:
                result["winner"] = parts[1].strip()
        if "reason" in lower:
            parts = line.split(":", 1)
            if len(parts) == 2:
                result["reason"] = parts[1].strip()
        seq_m = re.search(r"seq(?:uence)?[\s:=]+(\d+)", line, re.IGNORECASE)
        if seq_m:
            val = int(seq_m.group(1))
            if "local" in lower and result["sequence_local"] is None:
                result["sequence_local"] = val
            elif result["sequence_remote"] is None:
                result["sequence_remote"] = val
        ip_m = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
        if ip_m and ("path" in lower or "next" in lower):
            result["paths"].append(ip_m.group(1))

    return result


def parse_ghost_macs(output: str) -> List[str]:
    """Parse 'show dnos-internal routing evpn instance <name>
    mac-table-ghost | no-more'.

    Returns list of ghost MAC addresses.
    """
    text = strip_ansi(output)
    ghosts: List[str] = []
    for line in text.splitlines():
        m = MAC_ADDR_RE.search(line)
        if m:
            ghosts.append(m.group(0).lower())
    return ghosts


def parse_fib_evpn_mac(output: str) -> List[FibMacEntry]:
    """Parse 'show dnos-internal routing fib-manager database evpn
    local-mac service-instance <name> | no-more'.

    Handles key=value comma-separated format (DNOS 26.x):
      evi_id=1, eth_tag=0, mac=00:de:ad:00:01:01, interface=bundle-100.2150,
      dp_index=13320, action_type=New, Type=Add, neighbor_keys_size=0
    """
    text = strip_ansi(output)
    entries: List[FibMacEntry] = []

    for line in text.splitlines():
        m = MAC_ADDR_RE.search(line)
        if not m:
            continue
        mac = m.group(0).lower()

        service_instance = ""
        fib_state = "unknown"
        iface = None

        if 'evi_id=' in line or 'action_type=' in line:
            kv_pairs = {}
            for part in line.split(','):
                part = part.strip()
                if '=' in part:
                    k, v = part.split('=', 1)
                    kv_pairs[k.strip()] = v.strip()
            iface = kv_pairs.get('interface') or None
            if iface == '':
                iface = None
            action = kv_pairs.get('action_type', '').lower()
            type_val = kv_pairs.get('Type', kv_pairs.get('type', '')).lower()
            if action in ('new', 'modify') and type_val == 'add':
                fib_state = "programmed"
            elif type_val in ('delete', 'del'):
                fib_state = "pending"
            elif action in ('error',):
                fib_state = "error"
            else:
                fib_state = "programmed" if action else "unknown"
        else:
            inst_m = re.search(r"(?:instance|service)[\s:]+(\S+)", line, re.IGNORECASE)
            state_m = re.search(r"(programmed|pending|error|installed|stale)", line, re.IGNORECASE)
            iface_m = re.search(r"(?:^|[\s,])(ge\S+|bundle\S+|lag\S+)", line, re.IGNORECASE)
            if inst_m:
                service_instance = inst_m.group(1)
            if state_m:
                fib_state = state_m.group(1).lower()
            if iface_m:
                iface = iface_m.group(1)

        entries.append(FibMacEntry(
            mac=mac,
            service_instance=service_instance,
            fib_state=fib_state,
            interface=iface,
        ))

    return entries


# ---------------------------------------------------------------------------
# D1: ARP table parser
# ---------------------------------------------------------------------------

@dataclass
class ArpTableEntry:
    """One entry from 'show evpn arp-table instance <name>'."""
    ip: str
    mac: str
    interface: Optional[str] = None
    arp_type: str = "unknown"  # dynamic, static, proxy


_IPV4_RE = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")


def parse_arp_table(output: str) -> List[ArpTableEntry]:
    """Parse 'show evpn arp-table instance <name> | no-more'."""
    text = strip_ansi(output)
    entries: List[ArpTableEntry] = []
    _TYPE_RE = re.compile(r"(dynamic|static|proxy)", re.IGNORECASE)

    for line in text.splitlines():
        mac_m = MAC_ADDR_RE.search(line)
        ip_m = _IPV4_RE.search(line)
        if not mac_m or not ip_m:
            continue
        type_m = _TYPE_RE.search(line)
        iface_m = re.search(
            r"(ge\S+|bundle\S+|lag\S+|eth\S+|irb\S*)", line, re.IGNORECASE
        )
        entries.append(ArpTableEntry(
            ip=ip_m.group(1),
            mac=mac_m.group(0).lower(),
            interface=iface_m.group(1) if iface_m else None,
            arp_type=type_m.group(1).lower() if type_m else "unknown",
        ))

    return entries
