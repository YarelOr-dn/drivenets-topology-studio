"""Runtime parameter discovery and per-scenario DUT provisioning.

Extracted from ``mac_mobility_orchestrator.py``. This module walks the DUT
via ``run_show`` callbacks to build the dict of runtime parameters that
every recipe phase consumes: EVPN instance names, AC interface VLAN maps
(Q-in-Q outer/inner), VPLS-PW installed state, RD/RT/EVI of each instance,
and the LDP-resolvable next-hop Spirent must advertise with RT-2.

Public API:
    _provision_scenario_config(...)
    _rollback_scenario_config(...)
    _discover_ac_outer_vlans(...)
    _discover_instance_ac_vlans(...)
    _ensure_pw_transport_params(...)
    _discover_spirent_ldp_loopback()
    resolve_runtime_params(device, run_show, ctx=None) -> Dict[str, str]
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from device_discovery import discover_device_context
from shared.device_runner import get_cached_runner
from shared.mac_parsers import extract_first_mac, strip_ansi

from .constants import _EVPN_FALLBACK, SCENARIO_CONFIG_REQUIREMENTS


# ---------------------------------------------------------------------------
# Per-scenario config provisioning
# ---------------------------------------------------------------------------

def _provision_scenario_config(
    device: str,
    mapped_trigger: str,
    params: Dict[str, str],
    run_show: Callable[[str, str], str],
    evpn_name_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Auto-configure DUT prerequisites for a scenario trigger type.

    Returns dict with applied configs and rollback commands for cleanup.
    """
    req = SCENARIO_CONFIG_REQUIREMENTS.get(mapped_trigger)
    if not req:
        return {"applied": False}

    evpn_name = evpn_name_override or params.get("evpn_name", _EVPN_FALLBACK)
    ac1_vlan = params.get("_si_ac1_inner_vlan", "1000")

    # Use the correct AC interface for the target EVPN instance.
    # PW instance ACs may differ from SI instance ACs.
    _is_pw_target = (evpn_name == params.get("pw_evpn_name"))
    if _is_pw_target and params.get("_pw_ac1_interface"):
        ac1_interface = params["_pw_ac1_interface"]
    else:
        ac1_interface = params.get("_evpn_ac1_interface", "")
        if not ac1_interface:
            ac_ifs = params.get("_evpn_ac_interfaces", "")
            if ac_ifs:
                ac1_interface = ac_ifs.split(",")[0].strip()
    if not ac1_interface:
        try:
            cfg = run_show(
                device,
                f"show config network-services evpn instance {evpn_name} | flatten | no-more",
            )
            m = re.search(r"interface\s+([\w/.-]+)", strip_ansi(cfg))
            if m:
                ac1_interface = m.group(1)
        except Exception:
            pass

    if not ac1_interface:
        return {"applied": False, "reason": "Could not resolve AC1 interface"}

    fmt = {"evpn_name": evpn_name, "ac1_interface": ac1_interface, "ac1_vlan": ac1_vlan}

    check_cmd = req["check_command"].format(**fmt)
    check_out = run_show(device, check_cmd)
    if req["check_pass_pattern"] in strip_ansi(check_out):
        return {"applied": False, "already_configured": True,
                "detail": f"{req['description']} -- already present"}

    config_line = req["config_template"].format(**fmt)
    rollback_line = req["rollback_template"].format(**fmt)

    print(f"    [CONFIG-PROVISION] Applying: {config_line}", flush=True)
    try:
        runner = get_cached_runner(device, agent_callback=run_show)
        runner(device, "config")
        runner(device, config_line)
        commit_out = runner(device, "commit")
        runner(device, "end")
        if "error" in strip_ansi(commit_out).lower():
            print(f"    [CONFIG-PROVISION] Commit failed: {commit_out[:200]}", flush=True)
            runner(device, "rollback 0")
            runner(device, "end")
            return {"applied": False, "error": commit_out[:200]}
        print("    [CONFIG-PROVISION] Applied successfully", flush=True)
    except Exception as exc:
        print(f"    [CONFIG-PROVISION] Exception: {exc}", flush=True)
        return {"applied": False, "error": str(exc)}

    return {
        "applied": True,
        "config": config_line,
        "rollback": rollback_line,
        "description": req["description"],
        "needs_mac_relearn": req.get("needs_mac_relearn", False),
    }


def _rollback_scenario_config(
    device: str,
    provision_result: Dict[str, Any],
    run_show: Callable[[str, str], str],
) -> None:
    """Undo config applied by _provision_scenario_config."""
    if not provision_result.get("applied"):
        return
    rollback_line = provision_result.get("rollback", "")
    if not rollback_line:
        return
    print(f"    [CONFIG-ROLLBACK] Reverting: {rollback_line}", flush=True)
    try:
        runner = get_cached_runner(device, agent_callback=run_show)
        runner(device, "config")
        runner(device, rollback_line)
        runner(device, "commit")
        runner(device, "end")
        print("    [CONFIG-ROLLBACK] Reverted successfully", flush=True)
    except Exception as exc:
        print(f"    [CONFIG-ROLLBACK] Revert failed: {exc}", flush=True)


# ---------------------------------------------------------------------------
# AC / VLAN discovery
# ---------------------------------------------------------------------------

def _discover_ac_outer_vlans(
    device: str,
    run_show: Callable[[str, str], str],
    ac_interfaces: List[str],
) -> Dict[int, int]:
    """Discover Q-in-Q outer VLAN for each EVPN AC interface.

    Returns mapping {inner_vlan: outer_vlan} for interfaces using vlan-tags.
    Interfaces with simple vlan-id (no Q-in-Q) are omitted.
    """
    vlan_map: Dict[int, int] = {}
    if not ac_interfaces:
        return vlan_map
    try:
        cfg = run_show(device, "show config interfaces | flatten | include vlan-tags | no-more")
        for line in strip_ansi(cfg).splitlines():
            m = re.search(
                r"interfaces\s+\S+\s+vlan-tags\s+outer-tag\s+(\d+)\s+inner-tag\s+(\d+)",
                line,
            )
            if m:
                outer = int(m.group(1))
                inner = int(m.group(2))
                vlan_map[inner] = outer
    except Exception:
        pass
    return vlan_map


_FABRIC_VLAN_HINT_RE = re.compile(r"fab(\d{2,4})|B\d+\.(\d{2,4})|->v(\d{2,4})|->(\d{2,4})->", re.IGNORECASE)


def _discover_instance_ac_vlans(
    device: str,
    run_show: Callable[[str, str], str],
    evpn_name: str,
) -> List[Dict[str, Any]]:
    """Discover AC interfaces and their inner/outer VLANs for a specific EVPN instance.

    Returns list of dicts. Three shapes:
      - Q-in-Q AC:        {"interface": "ge400-0/0/5.4001", "inner_vlan": 4001, "outer_vlan": 214, "port_mode": False}
      - Single-tag AC:    {"interface": "ge.../.123", "inner_vlan": 123, "outer_vlan": None, "port_mode": False}
      - Port-mode AC:     {"interface": "ge100-18/0/1", "inner_vlan": None, "outer_vlan": <fabric_hint>, "port_mode": True}

    Port-mode ACs are CRITICAL: they exist on ports that share a fabric VLAN
    via DNAAS but carry untagged frames at the DUT. The fabric VLAN is mined
    from the interface description hint pattern (e.g. "->B14.211->fab211->")
    when present, otherwise None. Callers that need it must consult the
    dnos-config MCP `dnos_dnaas_inverse_path` for authoritative fabric_vlan.
    """
    result: List[Dict[str, Any]] = []
    try:
        cfg = run_show(
            device,
            f"show config network-services evpn instance {evpn_name} | flatten | no-more",
        )
        interfaces = []
        for line in strip_ansi(cfg).splitlines():
            m = re.search(r"instance\s+\S+\s+interface\s+([\w/.-]+)", line)
            if m:
                interfaces.append(m.group(1))

        for iface in interfaces:
            try:
                if_cfg = run_show(device, f"show config interfaces {iface} | flatten | no-more")
                if_cfg_clean = strip_ansi(if_cfg)
                vt = re.search(
                    r"vlan-tags\s+outer-tag\s+(\d+)\s+inner-tag\s+(\d+)",
                    if_cfg_clean,
                )
                if vt:
                    result.append({
                        "interface": iface,
                        "inner_vlan": int(vt.group(2)),
                        "outer_vlan": int(vt.group(1)),
                        "port_mode": False,
                    })
                    continue
                vid = re.search(r"vlan-id\s+(\d+)", if_cfg_clean)
                if vid:
                    result.append({
                        "interface": iface,
                        "inner_vlan": int(vid.group(1)),
                        "outer_vlan": None,
                        "port_mode": False,
                    })
                    continue
                # Port-mode AC: no vlan-tags, no vlan-id. Mine fabric VLAN
                # hint from interface description if present.
                fabric_hint: Optional[int] = None
                try:
                    desc_out = run_show(device, f"show interfaces {iface} | no-more")
                    desc_clean = strip_ansi(desc_out)
                    desc_m = re.search(r"Description:\s*(.+?)\n", desc_clean)
                    if desc_m:
                        for grp in _FABRIC_VLAN_HINT_RE.findall(desc_m.group(1)):
                            for tok in grp:
                                if tok and 1 <= int(tok) <= 4094:
                                    fabric_hint = int(tok)
                                    break
                            if fabric_hint:
                                break
                except Exception:
                    pass
                result.append({
                    "interface": iface,
                    "inner_vlan": None,
                    "outer_vlan": fabric_hint,
                    "port_mode": True,
                })
            except Exception:
                continue
    except Exception:
        pass
    return result


def _ensure_pw_transport_params(
    params: Dict[str, str],
    device: str,
    run_show: Callable[[str, str], str],
) -> None:
    """Discover pw_outer_vlan, pw_inner_vlan, pw_dut_mac from DUT config if missing.

    Called at trigger time when PW label is known but transport params weren't
    discovered during the initial infrastructure phase (e.g., PW came up after
    protocol-start, after the early discovery window closed).
    """
    if params.get("pw_outer_vlan") and params.get("pw_dut_mac"):
        return
    pw_inst = (params.get("pw_evpn_name") or params.get("pw_source_instance")
               or params.get("pw_test_evpn_name", "PW_TEST_ELAN"))
    try:
        pcfg = strip_ansi(run_show(
            device,
            f"show config network-services evpn instance {pw_inst} | flatten | no-more"))
        pif = re.search(r"interface\s+([\w/.-]+\.\d+)", pcfg)
        if not pif:
            return
        icfg = strip_ansi(run_show(
            device,
            f"show config interfaces {pif.group(1)} | flatten | no-more"))
        om = re.search(r"outer-tag\s+(\d+)", icfg)
        im = re.search(r"inner-tag\s+(\d+)", icfg)
        if om and not params.get("pw_outer_vlan"):
            params["pw_outer_vlan"] = om.group(1)
        if im and not params.get("pw_inner_vlan"):
            params["pw_inner_vlan"] = im.group(1)
        if not params.get("pw_dut_mac"):
            bif = pif.group(1).rsplit(".", 1)[0]
            bcfg = strip_ansi(run_show(
                device,
                f"show config interfaces {bif} | flatten | no-more"))
            mm = re.search(r"mac-address\s+([\da-fA-F:]+)", bcfg)
            if mm:
                params["pw_dut_mac"] = mm.group(1)
        print(f"    [PW] Discovered transport: outer={params.get('pw_outer_vlan')}, "
              f"inner={params.get('pw_inner_vlan')}, mac={params.get('pw_dut_mac')}", flush=True)
    except Exception as exc:
        print(f"    [PW] Transport discovery error: {exc}", flush=True)


def _discover_spirent_ldp_loopback() -> str:
    """Read the Spirent session JSON and return the IP of the device that has
    an LDP handle. This is the BGP next-hop the DUT will MPLS-resolve.

    Returns "" if no LDP-enabled device is found.
    """
    try:
        sess_path = Path.home() / "SCALER" / "SPIRENT" / "sessions" / "dn_spirent_main.json"
        if not sess_path.exists():
            return ""
        sess = json.loads(sess_path.read_text())
        for dev in sess.get("devices", []) or []:
            if dev.get("ldp_handle") and dev.get("ip"):
                return str(dev["ip"])
    except Exception:
        pass
    return ""


# ---------------------------------------------------------------------------
# Top-level runtime parameter resolver
# ---------------------------------------------------------------------------

def _select_evpn_instance_for_recipe(
    ctx: Dict[str, Any],
    recipe: Optional[Dict[str, Any]],
    evpn_instance_override: Optional[str],
) -> str:
    """Pick the EVPN instance the test MUST run against.

    Preference order (first match wins):
      1. evpn_instance_override (CLI --evpn-instance flag)
      2. recipe.service_capabilities.preferred_instance (if it exists on DUT)
      3. ctx.evpn_name_primary (legacy first-match-from-show-evpn-summary)
      4. _EVPN_FALLBACK constant

    Logged on stdout so the operator sees which path was taken.
    """
    instances_on_dut = list(ctx.get("evpn_instances") or [])
    chosen: Optional[str] = None
    reason: str = ""
    if evpn_instance_override:
        chosen = evpn_instance_override
        reason = "CLI override (--evpn-instance)"
        if instances_on_dut and chosen not in instances_on_dut:
            print(
                f"[EVPN-PICK] WARNING: --evpn-instance={chosen} not in DUT instance list "
                f"{instances_on_dut}; using anyway (caller may have just provisioned it)",
                flush=True,
            )
    if not chosen and recipe:
        caps = recipe.get("service_capabilities") or {}
        pref = caps.get("preferred_instance")
        if pref and (not instances_on_dut or pref in instances_on_dut):
            chosen = pref
            reason = "recipe.service_capabilities.preferred_instance"
        elif pref:
            print(
                f"[EVPN-PICK] WARNING: recipe prefers '{pref}' but DUT only has "
                f"{instances_on_dut}; falling back to evpn_name_primary",
                flush=True,
            )
    if not chosen:
        chosen = ctx.get("evpn_name_primary") or _EVPN_FALLBACK
        reason = "ctx.evpn_name_primary fallback"
    print(f"[EVPN-PICK] {chosen} ({reason})", flush=True)
    return chosen


def resolve_runtime_params(
    device: str,
    run_show: Callable[[str, str], str],
    ctx: Optional[Dict[str, Any]] = None,
    recipe: Optional[Dict[str, Any]] = None,
    evpn_instance_override: Optional[str] = None,
    ac_interface_override: Optional[str] = None,
    fabric_vlan_override: Optional[int] = None,
) -> Dict[str, str]:
    params: Dict[str, str] = {}
    if ctx is None:
        ctx = discover_device_context(device, run_show)
    params["active_ncc_id"] = str(ctx.get("active_ncc_id") or "0")
    evpn = _select_evpn_instance_for_recipe(ctx, recipe, evpn_instance_override)
    params["evpn_name"] = evpn
    mac_tbl = run_show(device, f"show evpn mac-table instance {evpn} | no-more")
    mac = extract_first_mac(mac_tbl) or "00:DE:AD:00:01:01"
    params["test_mac"] = mac
    ncp_id = str(ctx.get("first_ncp_id") or "0")
    if ncp_id == "0":
        sys_out = run_show(device, "show system | no-more")
        ncp_match = re.search(r"NCP\s+(\d+)", sys_out)
        if ncp_match:
            ncp_id = ncp_match.group(1)
    params["ncp_id"] = ncp_id

    ac_ifs = ctx.get("evpn_ac_interfaces", [])
    vlan_map = _discover_ac_outer_vlans(device, run_show, ac_ifs)
    params["_ac_outer_vlan_map"] = json.dumps(vlan_map)

    si_acs = _discover_instance_ac_vlans(device, run_show, evpn)

    if ac_interface_override:
        si_acs_pinned = [a for a in si_acs if a.get("interface") == ac_interface_override]
        if si_acs_pinned:
            si_acs = si_acs_pinned + [a for a in si_acs if a.get("interface") != ac_interface_override]
            print(f"[AC-PICK] Pinned AC interface: {ac_interface_override}", flush=True)
        else:
            si_acs = [{
                "interface": ac_interface_override,
                "inner_vlan": None,
                "outer_vlan": fabric_vlan_override,
                "port_mode": True,
            }] + si_acs
            print(
                f"[AC-PICK] WARNING: --ac-interface={ac_interface_override} not found under "
                f"{evpn}; injecting as port-mode AC (caller responsible for correctness)",
                flush=True,
            )

    if si_acs:
        port_mode_acs = [a for a in si_acs if a.get("port_mode")]
        tagged_acs = [a for a in si_acs if not a.get("port_mode") and a.get("inner_vlan")]
        si_inner_vlans = sorted({a["inner_vlan"] for a in tagged_acs if a.get("inner_vlan")})
        if si_inner_vlans:
            params["_si_ac1_inner_vlan"] = str(si_inner_vlans[0])
            params["_si_ac2_inner_vlan"] = str(si_inner_vlans[1] if len(si_inner_vlans) >= 2
                                                else si_inner_vlans[0])
        first_outer: Optional[int] = None
        if fabric_vlan_override is not None:
            first_outer = int(fabric_vlan_override)
        if first_outer is None:
            first_outer = next((a["outer_vlan"] for a in si_acs if a.get("outer_vlan")), None)
        if first_outer is not None:
            params["_si_outer_vlan"] = str(first_outer)
        ac_if_names = [a["interface"] for a in si_acs]
        params["_evpn_ac_interfaces"] = ",".join(ac_if_names)
        if ac_if_names:
            params["_evpn_ac1_interface"] = ac_if_names[0]
        if port_mode_acs:
            params["_si_port_mode_ac_count"] = str(len(port_mode_acs))
            params["_si_port_mode_ac1_interface"] = port_mode_acs[0]["interface"]

        # B9: Discover the site-interface from the EVPN config so callers can
        # report it. We do NOT override _evpn_ac1_interface here -- the smoke
        # test must use the DNAAS-mapped AC (e.g. ge400-0/0/4.1000), even
        # though it goes 'blocking-all' under SI when BGP EVPN is down.
        try:
            si_cfg = strip_ansi(run_show(
                device,
                f"show config network-services evpn instance {evpn} | flatten | no-more",
            ))
            site_if_m = re.search(r"site-interface\s+(\S+)", si_cfg)
            if site_if_m:
                params["_evpn_si_site_interface"] = site_if_m.group(1)
        except Exception:
            pass

    # -- BGP ASN for prerequisite commands --
    bgp_asn = str(ctx.get("bgp_asn") or ctx.get("bgp_as") or "")
    if not bgp_asn:
        try:
            bgp_out = run_show(device, "show bgp summary | no-more")
            asn_m = re.search(r"(?:local\s+AS\s+number|AS)\s+(\d+)", strip_ansi(bgp_out))
            if asn_m:
                bgp_asn = asn_m.group(1)
        except Exception:
            pass
    if not bgp_asn:
        try:
            bgp_cfg = run_show(device, "show config | flatten | no-more")
            asn_m = re.search(r"protocols\s+bgp\s+(\d+)", strip_ansi(bgp_cfg))
            if asn_m:
                bgp_asn = asn_m.group(1)
        except Exception:
            pass
    params["asn"] = bgp_asn

    # -- PW instance discovery (for spirent_vpls_cp tests) --
    # Dynamically discover which EVPN instance has an Installed VPLS PW instead
    # of hardcoding "PW_TEST_ELAN".
    pw_evpn_name = "PW_TEST_ELAN"
    try:
        vpls_pw_out = run_show(device, "show evpn vpls-pw | no-more")
        vpls_pw_clean = strip_ansi(vpls_pw_out)
        _pw_installed_instances = []
        sections = vpls_pw_clean.split("EVPN:")
        for sec in sections:
            if "Installed" not in sec:
                continue
            _inst_m = re.search(r"^\s*(\S+)", sec)
            if not _inst_m:
                continue
            _inst_name = _inst_m.group(1)
            row_m = re.search(
                r"\|\s*([\d.]+)\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+Installed",
                sec,
            )
            if row_m:
                _pw_installed_instances.append({
                    "name": _inst_name,
                    "peer_ip": row_m.group(1),
                    "remote_site_id": row_m.group(2),
                    "ingress_label": row_m.group(3),
                    "local_site_id": row_m.group(4),
                    "egress_label": row_m.group(5),
                })
        if _pw_installed_instances:
            _chosen = next(
                (p for p in _pw_installed_instances if p["name"] == pw_evpn_name),
                _pw_installed_instances[0],
            )
            pw_evpn_name = _chosen["name"]
            params["pw_peer_ip"] = _chosen["peer_ip"]
            params["pw_remote_site_id"] = _chosen["remote_site_id"]
            params["pw_ingress_label"] = _chosen["ingress_label"]
            params["pw_local_site_id"] = _chosen["local_site_id"]
            params["pw_egress_label"] = _chosen["egress_label"]
            params["pw_source_instance"] = pw_evpn_name
            print(f"  [PW] Discovered Installed PW in {pw_evpn_name}: "
                  f"label={_chosen['ingress_label']}, peer={_chosen['peer_ip']}")
    except Exception:
        pass

    params["pw_test_evpn_name"] = pw_evpn_name
    pw_acs = _discover_instance_ac_vlans(device, run_show, pw_evpn_name)
    if pw_acs:
        pw_inner = pw_acs[0]["inner_vlan"]
        params["pw_vlan"] = str(pw_inner)
        params["pw_evpn_name"] = pw_evpn_name
        params["_pw_ac1_interface"] = pw_acs[0]["interface"]
        params["_pw_ac_interfaces"] = ",".join(a["interface"] for a in pw_acs)

    try:
        _pw_inst = params.get("pw_source_instance", pw_evpn_name)
        _pw_cfg_raw = run_show(
            device,
            f"show config network-services evpn instance {_pw_inst} | flatten | no-more",
        )
        _pw_cfg_clean = strip_ansi(_pw_cfg_raw)
        _pw_if_m = re.search(r"interface\s+([\w/.-]+\.\d+)", _pw_cfg_clean)
        _pw_if_name = _pw_if_m.group(1) if _pw_if_m else ""
        if _pw_if_name:
            params["_pw_ac_interface"] = _pw_if_name
            _base_if = _pw_if_name.rsplit(".", 1)[0]
            _if_cfg = run_show(
                device,
                f"show config interfaces {_pw_if_name} | flatten | no-more",
            )
            _if_clean = strip_ansi(_if_cfg)
            outer_m = re.search(r"outer-tag\s+(\d+)", _if_clean)
            inner_m = re.search(r"inner-tag\s+(\d+)", _if_clean)
            if outer_m:
                params["pw_outer_vlan"] = outer_m.group(1)
            if inner_m:
                params["pw_inner_vlan"] = inner_m.group(1)
            _base_cfg = run_show(
                device,
                f"show config interfaces {_base_if} | flatten | no-more",
            )
            mac_m = re.search(r"mac-address\s+([\da-fA-F:]+)", strip_ansi(_base_cfg))
            if mac_m:
                params["pw_dut_mac"] = mac_m.group(1)
            else:
                _live = run_show(device, f"show interfaces {_base_if} | no-more")
                mac_live = re.search(r"MAC Address:\s+([\da-fA-F:]+)", strip_ansi(_live))
                if mac_live:
                    params["pw_dut_mac"] = mac_live.group(1)
            print(f"  [PW] Discovered AC interface {_pw_if_name} "
                  f"(outer={params.get('pw_outer_vlan')}, "
                  f"inner={params.get('pw_inner_vlan')}, "
                  f"mac={params.get('pw_dut_mac', 'NONE')})")
    except Exception:
        pass

    # -- EVPN instance parameters for RT-2 injection --
    try:
        evpn_cfg = run_show(
            device,
            f"show config network-services evpn instance {evpn} | flatten | no-more",
        )
        evpn_cfg_clean = strip_ansi(evpn_cfg)
        rd_m = re.search(r"route-distinguisher\s+(\S+)", evpn_cfg_clean)
        if rd_m:
            params["rd"] = rd_m.group(1)
        import_rt_m = re.search(r"import-l2vpn-evpn\s+route-target\s+(\S+)", evpn_cfg_clean)
        export_rt_m = re.search(r"export-l2vpn-evpn\s+route-target\s+(\S+)", evpn_cfg_clean)
        if import_rt_m:
            params["rt"] = import_rt_m.group(1)
            params["rt_import"] = import_rt_m.group(1)
        if export_rt_m:
            params["rt_export"] = export_rt_m.group(1)
            if "rt" not in params:
                params["rt"] = export_rt_m.group(1)
        evi_out = run_show(device, f"show evpn instance {evpn} detail | no-more")
        evi_m = re.search(r"EVI\s+ID\s*:\s*(\d+)", strip_ansi(evi_out))
        if evi_m:
            params["evi"] = evi_m.group(1)
    except Exception:
        pass

    # -- PW EVPN instance RT discovery (may differ from primary EVPN) --
    pw_evpn = params.get("pw_evpn_name", "")
    if pw_evpn and pw_evpn != evpn:
        try:
            pw_cfg = run_show(
                device,
                f"show config network-services evpn instance {pw_evpn} | flatten | no-more",
            )
            pw_cfg_clean = strip_ansi(pw_cfg)
            pw_rt_m = re.search(r"import-l2vpn-evpn\s+route-target\s+(\S+)", pw_cfg_clean)
            pw_rd_m = re.search(r"route-distinguisher\s+(\S+)", pw_cfg_clean)
            pw_evi_out = run_show(device, f"show evpn instance {pw_evpn} detail | no-more")
            pw_evi_m = re.search(r"EVI\s+ID\s*:\s*(\d+)", strip_ansi(pw_evi_out))
            if pw_rt_m:
                params["pw_rt"] = pw_rt_m.group(1)
            if pw_rd_m:
                params["pw_rd"] = pw_rd_m.group(1)
            if pw_evi_m:
                params["pw_evi"] = pw_evi_m.group(1)
            if pw_rt_m and params.get("rt") != pw_rt_m.group(1):
                print(f"  [RT] PW instance {pw_evpn} RT={pw_rt_m.group(1)} "
                      f"(differs from primary {evpn} RT={params.get('rt')})")
        except Exception:
            pass

    # -- Spirent BGP device names for EVPN RT-2 injection --
    from shared.spirent_vpls_provisioner import EVPN_DEVICE_NAME  # lazy import
    params.setdefault("spirent_evpn_device", EVPN_DEVICE_NAME)
    params.setdefault("spirent_bgp_device", EVPN_DEVICE_NAME)

    # B8: Discover the LDP-reachable next-hop for EVPN RT-2 injection.
    if "spirent_evpn_next_hop" not in params:
        nh_from_session = _discover_spirent_ldp_loopback()
        if nh_from_session:
            params["spirent_evpn_next_hop"] = nh_from_session
            print(f"  [LDP-NH] EVPN RT-2 next-hop override: {nh_from_session} "
                  f"(from Spirent session: device with ldp_handle)")
        else:
            try:
                ldp_out = strip_ansi(run_show(device, "show ldp neighbors | no-more"))
                ldp_nh = ""
                for line in ldp_out.splitlines():
                    if "OPERATIONAL" not in line:
                        continue
                    parts = [p.strip() for p in line.split("|") if p.strip()]
                    for p in parts:
                        m = re.match(r"^(\d+\.\d+\.\d+\.\d+)$", p)
                        if m:
                            ldp_nh = m.group(1)
                            break
                    if ldp_nh:
                        break
                if ldp_nh:
                    params["spirent_evpn_next_hop"] = ldp_nh
                    print(f"  [LDP-NH] EVPN RT-2 next-hop override: {ldp_nh} "
                          f"(live LDP neighbor on {device})")
                else:
                    print(f"  [LDP-NH] No LDP loopback found in Spirent session "
                          f"and no OPERATIONAL LDP neighbor on {device} -- "
                          f"EVPN RT-2 next-hop will fall back to Spirent BGP peer IP "
                          f"(routes may not import to MAC table). Will retry at trigger time.")
            except Exception as e:
                print(f"  [LDP-NH] LDP neighbor discovery failed: {e}")

    # B2: Discover the SI EVPN AC interface base-port MAC.
    si_dut_mac = ""
    si_ac_if_full = params.get("_evpn_ac1_interface", "")
    if si_ac_if_full:
        try:
            si_base_if = si_ac_if_full.rsplit(".", 1)[0]
            si_if_cfg = run_show(
                device,
                f"show config interfaces {si_base_if} | flatten | no-more",
            )
            si_mac_m = re.search(r"mac-address\s+([\da-fA-F:]+)", strip_ansi(si_if_cfg))
            if si_mac_m:
                si_dut_mac = si_mac_m.group(1)
            else:
                si_show = run_show(device, f"show interfaces {si_base_if} | no-more")
                si_show_m = re.search(r"MAC Address:\s+([\da-fA-F:]+)", strip_ansi(si_show))
                if si_show_m:
                    si_dut_mac = si_show_m.group(1)
        except Exception:
            pass
    if si_dut_mac:
        params["_si_dut_mac"] = si_dut_mac
        print(f"  [SI] Discovered SI DUT MAC for {si_ac_if_full}: {si_dut_mac}")

    return params


__all__ = [
    "_provision_scenario_config",
    "_rollback_scenario_config",
    "_discover_ac_outer_vlans",
    "_discover_instance_ac_vlans",
    "_ensure_pw_transport_params",
    "_discover_spirent_ldp_loopback",
    "resolve_runtime_params",
]
