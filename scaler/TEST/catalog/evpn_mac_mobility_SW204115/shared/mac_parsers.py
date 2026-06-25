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


@dataclass
class MacTableEntry:
    """One MAC from 'show evpn mac-table instance <name> | no-more'.

    The table has 6 pipe-delimited columns:
      Flags | MAC address | ESI | Nexthop | Label/VNI | Resolution
    The ESI column is often empty (spaces only) for single-homed entries.
    NEVER filter out empty columns -- use positional indexing.
    """
    mac: str
    flags: str = ""
    esi: str = ""
    nexthop: str = ""
    label: str = ""
    resolution: str = ""

    @property
    def is_local(self) -> bool:
        return "L" in self.flags

    @property
    def is_remote_evpn(self) -> bool:
        return "B" in self.flags and "v" not in self.flags

    @property
    def is_pw(self) -> bool:
        return "v" in self.flags

    @property
    def is_sticky(self) -> bool:
        return "K" in self.flags

    @property
    def is_selected(self) -> bool:
        return ">" in self.flags

    @property
    def is_suppressed(self) -> bool:
        return "P" in self.flags or "I" in self.flags

    @property
    def source(self) -> str:
        if self.is_pw:
            return "pw"
        if self.is_remote_evpn:
            return "bgp"
        if self.is_local:
            return "local"
        return "unknown"


def parse_mac_table_piped(output: str, mac_filter: Optional[str] = None) -> List[MacTableEntry]:
    """Parse 'show evpn mac-table instance <name> | no-more' (6-col pipe format).

    Handles the standard DNOS pipe-delimited MAC table output correctly,
    including empty ESI, Label, and Resolution columns.
    """
    text = strip_ansi(output)
    entries: List[MacTableEntry] = []
    for line in text.splitlines():
        parts = line.split("|")
        if len(parts) < 4:
            continue
        mac_field = parts[1].strip() if len(parts) > 1 else ""
        if not MAC_ADDR_RE.fullmatch(mac_field):
            continue
        if mac_filter and mac_filter.lower() not in mac_field.lower():
            continue
        entries.append(MacTableEntry(
            mac=mac_field.lower(),
            flags=parts[0].strip(),
            esi=parts[2].strip() if len(parts) > 2 else "",
            nexthop=parts[3].strip() if len(parts) > 3 else "",
            label=parts[4].strip() if len(parts) > 4 else "",
            resolution=parts[5].strip() if len(parts) > 5 else "",
        ))
    return entries


def find_mac(output: str, mac: str) -> Optional[MacTableEntry]:
    """Find a specific MAC in the piped table output. Returns None if not found."""
    entries = parse_mac_table_piped(output, mac_filter=mac)
    return entries[0] if entries else None


def parse_evpn_mac_entries(output: str) -> List[Dict[str, str]]:
    """
    Best-effort parse of MAC table lines into dicts with mac, source hints.

    Handles two DNOS output formats:
    - List format: flags column before pipe (L>, B>, Lv) + 'via local/remote' in Resolution
    - Per-MAC detail format: 'Protocol: Local/BGP' on the line following the MAC line
    """
    entries: List[Dict[str, str]] = []
    lines = strip_ansi(output).splitlines()
    for i, line in enumerate(lines):
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

        if source == "unknown" and "|" in line:
            flags_part = line.split("|")[0].strip()
            if flags_part and len(flags_part) <= 8:
                if "v" in flags_part:
                    source = "pw"
                elif "B" in flags_part.upper():
                    source = "bgp"
                elif "L" in flags_part.upper():
                    source = "local"

        if source == "unknown":
            for j in range(i + 1, min(i + 5, len(lines))):
                ctx_stripped = lines[j].strip().upper()
                if ctx_stripped.startswith("PROTOCOL:"):
                    proto = ctx_stripped.split(":", 1)[1].strip()
                    if "LOCAL" in proto:
                        source = "local"
                    elif "BGP" in proto or "REMOTE" in proto:
                        source = "bgp"
                    elif "PW" in proto or "PSEUDO" in proto or "VPLS" in proto:
                        source = "pw"
                    break
                if not lines[j].strip() or MAC_ADDR_RE.search(lines[j]):
                    break

        sticky = "sticky" in line.lower() or "STICKY" in upper
        if not sticky and "|" in line:
            flags_part = line.split("|")[0].strip()
            if "K" in flags_part:
                sticky = True
        seq_num = None
        if not sticky or seq_num is None:
            for j in range(i + 1, min(i + 12, len(lines))):
                ctx_line = lines[j].strip().lower()
                if not sticky and ctx_line.startswith("sticky:") and "true" in ctx_line:
                    sticky = True
                if seq_num is None and "sequence" in ctx_line:
                    seq_m = re.search(r"(\d+)", ctx_line)
                    if seq_m:
                        seq_num = int(seq_m.group(1))
                if not lines[j].strip() or MAC_ADDR_RE.search(lines[j]):
                    break
        source_aliases = [source]
        if source == "local":
            source_aliases.extend(["ac", "l", "l>"])
        if source == "bgp":
            source_aliases.extend(["evpn", "remote", "b", "b>"])
        if source == "pw":
            source_aliases.extend(["pseudo", "vpls", "v", "v>"])
        entry = {
            "mac": mac,
            "line": line.strip(),
            "source_hint": source,
            "source_aliases": source_aliases,
            "sticky": str(sticky).lower(),
        }
        if seq_num is not None:
            entry["sequence"] = seq_num
        entries.append(entry)
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
        proto_m = re.search(r"protocol\s*:\s*(\S+)", lower)
        if proto_m:
            proto_val = proto_m.group(1)
            if proto_val in ("local", "static"):
                source = "local"
            elif proto_val in ("bgp", "evpn", "remote"):
                source = "bgp"
            elif proto_val in ("pw", "pseudo", "vpls"):
                source = "pw"
        else:
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

    Returns dict with admin_state, detection counts, and per-MAC data with move counts.
    DUT output format:
        | 00:de:ad:00:01:01 | 0 / 5 |
        where 0 = current moves in window, 5 = threshold
    """
    text = strip_ansi(output)
    result: Dict[str, Any] = {
        "admin_state": "unknown",
        "total_local_loops": 0,
        "threshold": 0,
        "window_sec": 0,
        "macs": [],
        "mac_moves": {},
    }

    for line in text.splitlines():
        lower = line.lower().strip()
        if "loop prevention" in lower and ("enabled" in lower or "disabled" in lower):
            result["admin_state"] = "enabled" if "enabled" in lower else "disabled"
        if "loop detection threshold" in lower:
            tm = re.search(r"(\d+)\s*$", lower)
            if tm:
                result["threshold"] = int(tm.group(1))
        if "loop detection window" in lower:
            wm = re.search(r"(\d+)", lower)
            if wm:
                result["window_sec"] = int(wm.group(1))
        if "number of shutdown" in lower:
            sm = re.search(r"(\d+)\s*$", lower)
            if sm:
                result["total_local_loops"] = int(sm.group(1))
        m = MAC_ADDR_RE.search(line)
        if m:
            mac = m.group(0).lower()
            result["macs"].append(mac)
            move_m = re.search(r"(\d+)\s*/\s*(\d+)", line[m.end():])
            if move_m:
                result["mac_moves"][mac] = {
                    "moves": int(move_m.group(1)),
                    "threshold": int(move_m.group(2)),
                }

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

    Returns only MAC addresses that look like real ghost/suppression entries.

    DNOS implements the ghost detail command as an "also include ghosts" view:
    selected active MACs are printed too. A plain MAC-address count therefore
    produces false failures for healthy L>, B>, or v> entries.
    """
    text = strip_ansi(output)
    ghosts: List[str] = []
    chunks = re.split(r"(?=^MAC address:\s*)", text, flags=re.MULTILINE)
    for chunk in chunks:
        m = re.search(r"^MAC address:\s*(" + MAC_ADDR_RE.pattern + r")", chunk, re.MULTILINE)
        if not m:
            continue
        mac = m.group(1).lower()
        lower = chunk.lower()
        has_selected_protocol = "protocol:" in lower
        has_suppression = (
            "suppression: suppressed" in lower
            or "suppression: indefinitely" in lower
            or "traffic handling: drop" in lower
        )
        has_stale_protocol = re.search(r"protocol:\s+\S+,\s*stale", lower) is not None
        has_no_bestpath = not has_selected_protocol

        if has_suppression or has_stale_protocol or has_no_bestpath:
            ghosts.append(mac)
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
