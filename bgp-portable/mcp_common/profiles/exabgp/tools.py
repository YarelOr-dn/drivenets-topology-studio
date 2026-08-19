"""profiles.exabgp.tools - EXABGP tool definitions (Phase 5).

Verbatim move of the inline exabgp tool definitions out of
command_profiles.PROFILES. Helpers come from profiles._shared (re-exported
legacy builders, so schemas hash-match); EXEC_ARG / COMMON_HANDOFF_TOOLS
(and spirent SPIR_*/NDP_SAFE_RATE_PPS) from command_profiles, so the served
surface stays byte-identical (gated by tests/test_split_contract.py).
"""
from __future__ import annotations

from mcp_common.profiles._shared import _tool, _int, _text, _bool, CONFIRM_ARG
from mcp_common.command_profiles import EXEC_ARG, _handoff_tools


EXABGP_TOOLS = [
            _tool("exabgp_start", "Start ExaBGP", "Guarded ExaBGP start. Blocks unless caller confirms no live session.", {"device": _text("Device/session target"), "execute": EXEC_ARG, "confirmed_no_live_session": _bool("Confirmed no live session", False), "timeout_sec": _int("Timeout", 120)}),
            _tool("exabgp_preflight", "ExaBGP preflight", "Read-only DUT-side preflight for static route, .999 interface, neighbor config, and AFI/SAFI. Reuses a short read-only cache; pass refresh=true for live state.", {"device": _text("Device"), "server_ip": _text("ExaBGP server IP"), "neighbor": _text("BGP neighbor IP"), "asn": _text("DUT BGP ASN"), "bgp_as": _text("DUT BGP ASN"), "timeout_sec": _int("Timeout", 120), "dnos_format": _text("Nested dnos output format", "text"), "refresh": _bool("Force a fresh live read instead of the short cache", False), "cache_ttl_sec": _int("Read-only cache TTL seconds", 20)}, ["device"]),
            _tool("exabgp_stop", "Stop ExaBGP", "Stop ExaBGP only when current user message explicitly requested it.", {"explicit_request_text": _text("Exact current user request"), "execute": EXEC_ARG, "confirm": CONFIRM_ARG, "timeout_sec": _int("Timeout", 60)}, ["explicit_request_text"]),
            _tool("exabgp_inject", "Inject ExaBGP routes", "Inject routes into a live ExaBGP session.", {"session_id": _text("Session ID"), "file": _text("Route file"), "route": _text("Single route"), "prefix": _text("Prefix"), "afi": _text("AFI"), "count": _int("Route count"), "device": _text("Device"), "execute": EXEC_ARG, "timeout_sec": _int("Timeout", 120)}),
            _tool("exabgp_withdraw", "Withdraw ExaBGP routes", "Withdraw routes from a live ExaBGP session.", {"session_id": _text("Session ID"), "file": _text("Route file"), "route": _text("Single route"), "prefix": _text("Prefix"), "afi": _text("AFI"), "count": _int("Route count"), "device": _text("Device"), "execute": EXEC_ARG, "timeout_sec": _int("Timeout", 120)}),
            _tool("exabgp_verify", "Verify ExaBGP", "Read-only ExaBGP session verification.", {"session_id": _text("Session ID"), "device": _text("Device"), "timeout_sec": _int("Timeout", 60)}),
            _tool("exabgp_diagnose", "Diagnose ExaBGP", "Read-only ExaBGP diagnosis.", {"session_id": _text("Session ID"), "device": _text("Device"), "timeout_sec": _int("Timeout", 120)}),
            _tool("exabgp_watchdog_status", "ExaBGP watchdog status", "Read watchdog/session status.", {"session_id": _text("Session ID"), "timeout_sec": _int("Timeout", 60)}),
            _tool("exabgp_route_inventory", "ExaBGP route inventory", "List injectable route artifacts and read session status.", {"session_id": _text("Session ID"), "device": _text("Device")}),
            _tool("exabgp_session_handoff", "Save ExaBGP handoff", "Save typed BGP session handoff for XRAY/debug/TEST.", {"device": _text("Device"), "session_id": _text("Session ID"), "state": _text("Session state"), "next_actions": {"type": "array"}}),
            _tool("exabgp_session_save", "Save BGP handoff", "Save ExaBGP session context to handoff store.", {"device": _text("Device"), "session_id": _text("Session ID"), "payload": {"type": "object"}}),
            _tool("exabgp_session_lock", "ExaBGP session lock", "Acquire or inspect the single-instance ExaBGP lease. Mutating start/stop/inject/onboard require a held lease.", {"owner": _text("Lease owner (Cursor user)"), "dut": _text("Target DUT"), "acquire": _bool("Acquire the lease", True), "force": _bool("Force steal (explicit stop phrase only)", False), "ttl_sec": _int("Lease TTL seconds", 3600)}),
            _tool("exabgp_session_release", "ExaBGP session release", "Release the ExaBGP lease for this owner.", {"owner": _text("Lease owner"), "force": _bool("Force release another owner", False)}, ["owner"]),
            _tool("exabgp_onboard", "Onboard DUT VLAN on IL DNAAS", "Dry-run (default) IL DNAAS global-BD search for vlan g_*_vN, plan DUT-facing sub-if AC add. execute=true only after user confirm. Never silent-fallback to g_mgmt_v999.", {"vlan": _int("Global VLAN for this peering"), "vlan_range": _text("Allocated VLAN range e.g. 2100-2199"), "device": _text("DUT hostname"), "bd_name": _text("Confirmed DNAAS global BD name"), "dnaas_leaf": _text("DNAAS leaf"), "bundle": _text("Leaf/DUT bundle name"), "dut_bundle": _text("DUT bundle if different"), "dut_ip": _text("DUT inband IP"), "gateway": _text("Inband gateway"), "subnet": _text("Prefix length or CIDR", "24"), "neighbor": _text("ExaBGP OOB neighbor IP"), "asn": _text("DUT BGP ASN"), "peer_as": _text("ExaBGP AS"), "bd_show_text": _text("Optional injected BD show text (tests)"), "owner": _text("Lease owner"), "execute": EXEC_ARG, "timeout_sec": _int("Timeout", 120)}, ["vlan"]),
            *_handoff_tools(),
        ]

__all__ = ["EXABGP_TOOLS"]
