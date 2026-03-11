"""Scale Up/Down Operations for DNOS Services and Interfaces.

Provides bulk scale operations:
- Scale DOWN: Delete services with correlated interfaces (e.g., FXC + PWHE)
- Scale UP: Add more services from the last configured one

Supports flexible range specifications:
- "last 300" - last 300 items
- "100,200,500" - specific items by number
- "100-400" - range of items
- "1-100,200-300" - multiple ranges
"""

import os
import re
import json
import time
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich import box
from .core import BackException, TopException, int_prompt_nav, str_prompt_nav

console = Console()


# ═══════════════════════════════════════════════════════════════════════════════
# LLDP NEIGHBOR-AWARE INTERFACE SELECTION
# Only suggests physical interfaces connected to other DN devices or DNAAS
# ═══════════════════════════════════════════════════════════════════════════════

def get_lldp_neighbors(hostname: str) -> List[Dict]:
    """
    Get LLDP neighbors for a device from operational.json.
    
    Returns list of dicts with:
    - interface: Local interface name (e.g., ge100-18/0/0)
    - neighbor: Remote system name
    - remote_port: Remote port ID
    - is_dn_device: True if neighbor is a DN device (DNAAS or local)
    """
    config_base = "/home/dn/SCALER/db/configs"
    ops_path = os.path.join(config_base, hostname, "operational.json")
    
    try:
        with open(ops_path, 'r') as f:
            ops_data = json.load(f)
        return ops_data.get('lldp_neighbors', [])
    except Exception:
        return []


def get_wan_interfaces_from_config(hostname: str) -> List[Dict]:
    """
    Get WAN interfaces from device configuration as fallback when LLDP not available.
    WAN interfaces are typically ge*/xe*/et* interfaces with descriptions containing
    keywords like "wan", "core", "uplink", or that are used in ISIS/OSPF.
    """
    config_base = "/home/dn/SCALER/db/configs"
    config_path = os.path.join(config_base, hostname, "running.txt")
    
    wan_interfaces = []
    
    try:
        with open(config_path, 'r') as f:
            config = f.read()
        
        # Find physical interfaces that are likely WAN/interconnect
        lines = config.split('\n')
        current_iface = None
        current_desc = None
        in_interfaces = False
        
        for line in lines:
            stripped = line.strip()
            
            if stripped == 'interfaces':
                in_interfaces = True
                continue
            
            if in_interfaces:
                # Detect physical parent interface (not sub-interface)
                if re.match(r'^(ge|xe|et)\d+-[\d/]+$', stripped):
                    current_iface = stripped
                    current_desc = None
                elif stripped.startswith('description ') and current_iface:
                    current_desc = stripped.replace('description ', '').strip('"')
                elif stripped == '!' and current_iface:
                    # Check if this looks like a WAN/interconnect interface
                    is_wan = False
                    neighbor_hint = "Physical interface"
                    
                    if current_desc:
                        desc_lower = current_desc.lower()
                        if any(kw in desc_lower for kw in ['wan', 'core', 'uplink', 'backbone', 'p2p', 'to-']):
                            is_wan = True
                            neighbor_hint = current_desc
                    
                    # Also include interfaces used in ISIS/OSPF (check later in config)
                    if f'interface {current_iface}' in config and 'isis' in config.lower():
                        is_wan = True
                        neighbor_hint = "ISIS interface"
                    
                    if is_wan or current_desc:
                        wan_interfaces.append({
                            'interface': current_iface,
                            'neighbor': neighbor_hint,
                            'remote_port': '',
                            'is_dn_device': is_wan
                        })
                    
                    current_iface = None
                    current_desc = None
                elif not line.startswith('  ') and stripped and stripped != '!':
                    in_interfaces = False
        
        return wan_interfaces
    except Exception:
        return []


def get_interfaces_with_lldp(hostname: str, dn_only: bool = True) -> List[Dict]:
    """
    Get physical interfaces that have LLDP neighbors.
    Falls back to WAN interfaces from config if LLDP not available.
    
    Args:
        hostname: Device hostname
        dn_only: If True, only return interfaces connected to DN devices
    
    Returns:
        List of interface dicts with neighbor info
    """
    neighbors = get_lldp_neighbors(hostname)
    
    # If no LLDP neighbors, fall back to WAN interfaces from config
    if not neighbors:
        neighbors = get_wan_interfaces_from_config(hostname)
    
    if dn_only:
        # Filter to only DN device neighbors
        return [n for n in neighbors if n.get('is_dn_device', False)]
    return neighbors


def suggest_physical_interface(
    hostname: str,
    purpose: str = "L2-AC",
    dn_only: bool = True
) -> Optional[str]:
    """
    Suggest a physical interface for configuration based on LLDP neighbors.
    
    Args:
        hostname: Device hostname
        purpose: What the interface will be used for (L2-AC, WAN, DG)
        dn_only: Only suggest interfaces connected to DN devices
    
    Returns:
        Interface name or None if no suitable interface found
    """
    neighbors = get_interfaces_with_lldp(hostname, dn_only=dn_only)
    
    if not neighbors:
        console.print(f"[yellow]No LLDP neighbors found for {hostname}[/yellow]")
        console.print(f"[dim]Run 'show lldp neighbor' on device or wait for next config sync[/dim]")
        return None
    
    # Group by interface (in case multiple neighbors per interface)
    interface_neighbors: Dict[str, List[str]] = {}
    for n in neighbors:
        iface = n.get('interface', '')
        neighbor = n.get('neighbor', 'Unknown')
        if iface:
            if iface not in interface_neighbors:
                interface_neighbors[iface] = []
            interface_neighbors[iface].append(neighbor)
    
    console.print(f"\n[bold cyan]Physical Interfaces with LLDP Neighbors ({hostname}):[/bold cyan]")
    
    iface_list = list(interface_neighbors.keys())
    for i, iface in enumerate(iface_list[:10], 1):  # Show max 10
        neighbors_str = ', '.join(interface_neighbors[iface][:3])
        if len(interface_neighbors[iface]) > 3:
            neighbors_str += '...'
        console.print(f"  [{i}] [green]{iface}[/green] → {neighbors_str}")
    
    if len(iface_list) > 10:
        console.print(f"  [dim]... and {len(iface_list) - 10} more[/dim]")
    
    console.print(f"  [C] Custom interface")
    console.print(f"  [B] Back")
    
    choices = [str(i) for i in range(1, min(len(iface_list), 10) + 1)] + ["c", "C", "b", "B"]
    choice = Prompt.ask(f"Select interface for {purpose}", choices=choices, default="1").lower()
    
    if choice == "b":
        return None
    
    if choice == "c":
        return str_prompt_nav("Enter interface name", default="ge100-0/0/0")
    
    idx = int(choice) - 1
    if idx < len(iface_list):
        return iface_list[idx]
    
    return None


def show_lldp_summary(hostname: str):
    """Display LLDP neighbor summary for a device."""
    neighbors = get_lldp_neighbors(hostname)
    
    if not neighbors:
        console.print(f"[yellow]No LLDP neighbors found for {hostname}[/yellow]")
        return
    
    dn_count = sum(1 for n in neighbors if n.get('is_dn_device', False))
    other_count = len(neighbors) - dn_count
    
    console.print(f"\n[bold cyan]LLDP Neighbors: {hostname}[/bold cyan]")
    console.print(f"  DN Devices:    [green]{dn_count}[/green]")
    console.print(f"  Other:         [dim]{other_count}[/dim]")
    console.print(f"  Total:         {len(neighbors)}")
    
    # Show DN neighbors
    if dn_count > 0:
        console.print(f"\n  [bold]Connected DN Devices:[/bold]")
        for n in neighbors:
            if n.get('is_dn_device', False):
                console.print(f"    {n.get('interface', '?')} → [cyan]{n.get('neighbor', '?')}[/cyan] ({n.get('remote_port', '?')})")


@dataclass
class ServiceScale:
    """Represents a scalable service with its correlated interfaces."""
    service_type: str  # fxc, l2vpn, evpn, vpws, flowspec-vpn
    service_name: str
    service_number: int  # Extracted number from name
    interfaces: List[str] = field(default_factory=list)
    config_block: str = ""
    # EVPN-VPWS specific fields
    vpws_local_id: Optional[int] = None
    vpws_remote_id: Optional[int] = None
    rd: Optional[str] = None  # Route Distinguisher (e.g., "1.1.1.1:1")
    rt: Optional[str] = None  # Route Target (e.g., "1234567:1")
    # FlowSpec VPN specific
    flowspec_afs: List[str] = field(default_factory=list)  # e.g., ['ipv4-flowspec', 'ipv6-flowspec']
    bgp_asn: Optional[str] = None


@dataclass
class ScaleContext:
    """Context for scale operations."""
    hostname: str
    config: str
    services: Dict[str, List[ServiceScale]] = field(default_factory=dict)
    # Correlated interfaces by service
    pwhe_by_fxc: Dict[str, List[str]] = field(default_factory=dict)
    subif_by_service: Dict[str, List[str]] = field(default_factory=dict)


def parse_range_spec(spec: str, max_value: int) -> Set[int]:
    """Parse a range specification into a set of numbers.
    
    Supports:
    - "last 300" or "last300" - last 300 items (1 to max_value, last 300)
    - "100" - single number
    - "100,200,300" - comma-separated
    - "100-400" - range
    - "1-100,200-300,500" - mixed
    
    Args:
        spec: Range specification string
        max_value: Maximum value in the set
        
    Returns:
        Set of integers to operate on
    """
    result = set()
    spec = spec.strip().lower()
    
    # Handle "last N" syntax
    last_match = re.match(r'last\s*(\d+)', spec)
    if last_match:
        n = int(last_match.group(1))
        start = max(1, max_value - n + 1)
        return set(range(start, max_value + 1))
    
    # Split by comma for multiple parts
    parts = [p.strip() for p in spec.split(',')]
    
    for part in parts:
        if not part:
            continue
            
        # Check for range (e.g., "100-400")
        range_match = re.match(r'(\d+)\s*-\s*(\d+)', part)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2))
            result.update(range(start, end + 1))
        else:
            # Single number
            try:
                result.add(int(part))
            except ValueError:
                pass
    
    # Filter to valid range
    return {n for n in result if 1 <= n <= max_value}


def extract_service_number(name: str) -> int:
    """Extract numeric suffix from service name.
    
    Examples:
        FXC_1 -> 1
        l2vpn-instance-100 -> 100
        evpn_service_2000 -> 2000
    """
    match = re.search(r'(\d+)\s*$', name)
    if match:
        return int(match.group(1))
    return 0


def _determine_service_type(section: str, instance_name: str) -> str:
    """Determine service type from section and instance name.
    
    Priority: Instance name pattern > Section context
    
    Args:
        section: Current section (fxc, vpws, evpn, l2vpn, vrf)
        instance_name: Instance name (e.g., FXC_1, EVPN_1, VPWS_1, VRF-1)
    
    Returns:
        Service type key (fxc, vpws, evpn, l2vpn, vrf)
    """
    name_upper = instance_name.upper()
    
    # Match by instance name pattern first (more reliable)
    if name_upper.startswith('FXC'):
        return 'fxc'
    elif name_upper.startswith('VPWS'):
        return 'vpws'
    elif name_upper.startswith('EVPN'):
        return 'evpn'  # EVPN_N instances go to evpn category
    elif name_upper.startswith('VPLS'):
        return 'evpn'  # VPLS goes under evpn category
    elif name_upper.startswith('VRF') or name_upper.startswith('L3VPN'):
        return 'vrf'  # VRF/L3VPN as separate category
    elif name_upper.startswith('FS') or name_upper.startswith('FLOWSPEC'):
        return 'flowspec-vpn'
    elif name_upper.startswith('BD') or name_upper.startswith('BRIDGE'):
        return 'l2vpn'
    
    # Fall back to section context
    return section if section in ('fxc', 'vpws', 'evpn', 'l2vpn', 'vrf', 'flowspec-vpn') else 'l2vpn'


def _detect_flowspec_vpn_vrfs(config: str, services: Dict[str, List['ServiceScale']]) -> None:
    """Scan VRF instances for FlowSpec address-families and populate flowspec-vpn list.
    
    FlowSpec VPN in DNOS is configured per-VRF:
      network-services vrf instance NAME protocols bgp ASN address-family ipv4-flowspec
    
    VRFs with flowspec AFs are added to services['flowspec-vpn'].
    They remain in services['vrf'] too (dual-categorized).
    """
    vrf_block_pattern = re.compile(
        r'instance\s+(\S+)\s*\n(.*?)(?=\n    instance\s+\S+|\n  !\s*\n(?:\s*!\s*\n)?(?:(?:  \S|\S))|\Z)',
        re.DOTALL
    )
    
    in_vrf_section = False
    vrf_section_text = ""
    
    for line in config.split('\n'):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        
        if indent == 2 and stripped == 'vrf':
            in_vrf_section = True
            vrf_section_text = ""
            continue
        elif in_vrf_section and indent == 0 and stripped and stripped != '!':
            in_vrf_section = False
        
        if in_vrf_section:
            vrf_section_text += line + '\n'
    
    if not vrf_section_text:
        return
    
    for match in vrf_block_pattern.finditer(vrf_section_text):
        instance_name = match.group(1)
        block = match.group(2)
        
        fs_afs = []
        if re.search(r'address-family ipv4-flowspec\b(?!-vpn)', block):
            fs_afs.append('ipv4-flowspec')
        if re.search(r'address-family ipv6-flowspec\b(?!-vpn)', block):
            fs_afs.append('ipv6-flowspec')
        
        if not fs_afs:
            continue
        
        interfaces = re.findall(
            r'^\s*interface\s+((?:ph|ge|xe|et|bundle|lag)\S+)',
            block, re.MULTILINE
        )
        
        rd_match = re.search(r'route-distinguisher\s+(\S+)', block)
        rt_match = re.search(r'(?:import|export)-vpn\s+route-target\s+(\S+)', block)
        asn_match = re.search(r'bgp\s+(\d+)', block)
        
        svc = ServiceScale(
            service_type='flowspec-vpn',
            service_name=instance_name,
            service_number=extract_service_number(instance_name),
            interfaces=interfaces,
            config_block="",
            rd=rd_match.group(1) if rd_match else None,
            rt=rt_match.group(1) if rt_match else None,
            flowspec_afs=fs_afs,
            bgp_asn=asn_match.group(1) if asn_match else None
        )
        services['flowspec-vpn'].append(svc)
    
    services['flowspec-vpn'].sort(key=lambda s: s.service_number)


def parse_services_from_config(config: str) -> Dict[str, List[ServiceScale]]:
    """Parse all services from DNOS configuration.
    
    DNOS service structure:
    - network-services / evpn-vpws-fxc / instance FXC_N   (FXC services with PWHE)
    - network-services / evpn-vpws / instance EVPN_N      (EVPN-VPWS services)
    - network-services / evpn-vpws / instance VPWS_N      (VPWS services)
    - network-services / evpn-vpls / instance VPLS_N      (VPLS services)
    - network-services / vrf / instance VRF_N             (VRF services)
    - l2vpn / bridge-domain / ...                         (L2VPN bridge domains)
    
    Returns dict with service types as keys and lists of ServiceScale as values.
    """
    services: Dict[str, List[ServiceScale]] = {
        'fxc': [],
        'l2vpn': [],
        'evpn': [],
        'vpws': [],
        'vrf': [],  # VRF as separate category for L3VPN services
        'flowspec-vpn': []  # VRFs with flowspec address-families
    }
    
    lines = config.split('\n')
    
    # State machine to parse hierarchical config
    current_section = None
    current_instance = None
    current_interfaces = []
    instance_start_line = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        
        # Detect section starts (2-space indent under network-services)
        # Use precise matching to avoid confusion between evpn-vpws and evpn-vpws-fxc
        if indent == 2 and stripped == 'evpn-vpws-fxc':
            current_section = 'fxc'
        elif indent == 2 and stripped == 'evpn-vpws':
            current_section = 'vpws'
        elif indent == 2 and stripped == 'evpn-vpls':
            current_section = 'evpn'  # VPLS goes under evpn category
        elif indent == 2 and stripped == 'evpn':
            current_section = 'evpn'  # Plain evpn section (EVPN_* instances)
        elif indent == 2 and stripped == 'vrf':
            current_section = 'vrf'  # VRF as separate category (L3VPN)
        elif stripped.startswith('bridge-domain') or stripped == 'l2vpn':
            current_section = 'l2vpn'
        # Reset section when exiting network-services (back to 0 indent)
        elif indent == 0 and stripped and not stripped.startswith('#'):
            if stripped not in ('network-services', 'interfaces', 'protocols', 'system', 'routing-policy'):
                # Save current instance before resetting section
                if current_instance and current_section:
                    svc_type = _determine_service_type(current_section, current_instance)
                    svc = ServiceScale(
                        service_type=svc_type,
                        service_name=current_instance,
                        service_number=extract_service_number(current_instance),
                        interfaces=current_interfaces.copy(),
                        config_block=""
                    )
                    services[svc_type].append(svc)
                    current_instance = None
                    current_interfaces = []
                current_section = None
        
        # Detect instance start: "instance NAME" (4-space indent under section)
        instance_match = re.match(r'^(\s*)instance\s+(\S+)\s*$', line)
        if instance_match and current_section:
            instance_indent = len(instance_match.group(1))
            
            # Save previous instance if exists
            if current_instance:
                # Determine service type by BOTH section AND naming pattern
                svc_type = _determine_service_type(current_section, current_instance)
                svc = ServiceScale(
                    service_type=svc_type,
                    service_name=current_instance,
                    service_number=extract_service_number(current_instance),
                    interfaces=current_interfaces.copy(),
                    config_block=""  # We don't need full block for delete
                )
                services[svc_type].append(svc)
            
            # Start new instance
            current_instance = instance_match.group(2)
            current_interfaces = []
            instance_start_line = i
        
        # Detect interface within instance (includes bundle interfaces)
        iface_match = re.match(r'^\s*interface\s+((?:ph|ge|xe|et|ae|lo|lag|bundle)\S*)', stripped)
        if iface_match and current_instance:
            current_interfaces.append(iface_match.group(1))
        
        i += 1
    
    # Don't forget the last instance
    if current_instance and current_section:
        svc_type = _determine_service_type(current_section, current_instance)
        svc = ServiceScale(
            service_type=svc_type,
            service_name=current_instance,
            service_number=extract_service_number(current_instance),
            interfaces=current_interfaces.copy(),
            config_block=""
        )
        services[svc_type].append(svc)
    
    # Post-process: detect VRFs with FlowSpec address-families
    # These become 'flowspec-vpn' entries in addition to (or instead of) 'vrf' entries
    _detect_flowspec_vpn_vrfs(config, services)
    
    # If state machine found services, return them without regex override
    total_found = sum(len(v) for v in services.values())
    if total_found > 0:
        return services
    
    # FALLBACK: Use simple regex approach for FXC (if state machine failed)
    # Pattern: "instance FXC-N" followed by "interface <any>" before next instance
    # Clear FXC list and rebuild properly
    services['fxc'] = []
    
    # Find all FXC instance blocks - match from "instance FXC-N" to next "instance FXC-N" or section end
    # The key is to match until the closing "    !" (4-space indent) which marks end of instance
    fxc_block_pattern = re.compile(
        r'instance\s+(FXC-\d+)\s*\n(.*?)(?=\n    instance\s+FXC-\d+|\n  !|\Z)',
        re.DOTALL
    )
    
    for match in fxc_block_pattern.finditer(config):
        name = match.group(1)
        block = match.group(2)
        num = extract_service_number(name)
        
        # Find ANY interface type within this block (PWHE, L2-AC, bundle, etc.)
        # Pattern matches: phN.M, geN-X/Y/Z.M, xeN-X/Y/Z.M, bundle-N.M, etc.
        iface_matches = re.findall(
            r'interface\s+((?:ph\d+\.\d+|(?:ge|xe|et)\d+-[\d/]+\.\d+|bundle-?\d+\.\d+|lag\d+\.\d+))', 
            block
        )
        # Take only the first interface (the one that belongs to this FXC)
        interfaces = iface_matches[:1] if iface_matches else []
        
        # No default fallback - if no interface found, leave empty
        # This prevents showing wrong interface types for devices
        
        svc = ServiceScale(
            service_type='fxc',
            service_name=name,
            service_number=num,
            interfaces=interfaces,
            config_block=""
        )
        services['fxc'].append(svc)
    
    # ==================== EVPN-VPWS PARSING ====================
    # Clear VPWS list and rebuild with proper regex parsing
    # EVPN-VPWS structure:
    #   instance VPWS-N
    #     protocols
    #       bgp ASN
    #         route-target ASN:N
    #         route-distinguisher RID:N
    #     interface geX.Y
    #       vpws-service-id local N remote N
    services['vpws'] = []
    
    # First, find the evpn-vpws section (not evpn-vpws-fxc)
    vpws_section_match = re.search(
        r'\n  evpn-vpws\n(.*?)(?=\n  evpn-vpws-fxc|\n  evpn\n|\n  !\n!|\Z)',
        config, re.DOTALL
    )
    
    if vpws_section_match:
        vpws_section = vpws_section_match.group(1)
        
        # Parse each VPWS instance
        vpws_instance_pattern = re.compile(
            r'instance\s+(VPWS-\d+|[A-Za-z][\w-]*)\s*\n(.*?)(?=\n    instance\s+|\n  !\n|\Z)',
            re.DOTALL
        )
        
        for match in vpws_instance_pattern.finditer(vpws_section):
            name = match.group(1)
            block = match.group(2)
            num = extract_service_number(name)
            
            # Extract interface
            iface_match = re.search(r'interface\s+((?:ge|xe|et|ph|bundle)\S+)', block)
            interfaces = [iface_match.group(1)] if iface_match else []
            
            # Extract vpws-service-id
            vpws_id_match = re.search(r'vpws-service-id\s+local\s+(\d+)\s+remote\s+(\d+)', block)
            
            # Extract RD and RT
            rd_match = re.search(r'route-distinguisher\s+(\S+)', block)
            rt_match = re.search(r'export-l2vpn-evpn\s+route-target\s+(\S+)', block)
            
            svc = ServiceScale(
                service_type='vpws',
                service_name=name,
                service_number=num,
                interfaces=interfaces,
                config_block=""
            )
            # Store extra data in a dictionary attribute
            svc.vpws_local_id = int(vpws_id_match.group(1)) if vpws_id_match else num
            svc.vpws_remote_id = int(vpws_id_match.group(2)) if vpws_id_match else num
            svc.rd = rd_match.group(1) if rd_match else None
            svc.rt = rt_match.group(1) if rt_match else None
            
            services['vpws'].append(svc)
    
    # Sort each list by service number
    for svc_type in services:
        services[svc_type].sort(key=lambda s: s.service_number)
    
    # Remove duplicates (keep first occurrence)
    for svc_type in services:
        seen = set()
        unique = []
        for svc in services[svc_type]:
            if svc.service_name not in seen:
                seen.add(svc.service_name)
                unique.append(svc)
        services[svc_type] = unique
    
    return services


def find_correlated_pwhe(config: str, fxc_interfaces: List[str]) -> List[str]:
    """Find PWHE interfaces (ph*) that are used by FXC services.
    
    When deleting FXC services, we should also delete the corresponding
    PWHE interfaces that are exclusively used by those FXCs.
    """
    pwhe_interfaces = []
    
    for iface in fxc_interfaces:
        if iface.startswith('ph'):
            pwhe_interfaces.append(iface)
    
    return pwhe_interfaces


def generate_delete_commands(
    services: List[ServiceScale], 
    include_interfaces: bool = True,
    current_config: str = None
) -> List[str]:
    """Generate DNOS delete commands for services and their interfaces.
    
    DNOS delete syntax in config mode uses 'no' prefix:
    - FXC: no network-services evpn-vpws-fxc instance FXC-N
    - VPWS: no network-services evpn-vpws instance NAME
    - EVPN: no network-services evpn evpn-instances evpn-instance NAME
    - Multihoming: network-services multihoming / no interface phX.Y
    - Interfaces: no interfaces phX.Y (sub-interface first, then parent)
    
    IMPORTANT ORDER (dependencies):
    1. Delete services FIRST (they reference interfaces)
    2. Delete multihoming references (they reference interfaces)
    3. Delete sub-interfaces (phX.Y)
    4. Delete parent interfaces (phX) - only if not used by other subs
    
    Args:
        services: List of services to delete
        include_interfaces: Whether to also delete correlated interfaces
        current_config: Current device config to check for multihoming references
        
    Returns:
        List of delete command strings
    """
    from .parsers import parse_existing_multihoming
    
    commands = []
    interfaces_to_delete = set()
    pwhe_parents_to_delete = set()  # Track PWHE parents (phX)
    
    # STEP 1: Generate service delete commands FIRST
    for svc in services:
        if svc.service_type == 'fxc':
            commands.append(f"no network-services evpn-vpws-fxc instance {svc.service_name}")
        elif svc.service_type == 'vpws':
            commands.append(f"no network-services evpn-vpws instance {svc.service_name}")
        elif svc.service_type == 'evpn':
            commands.append(f"no network-services evpn evpn-instances evpn-instance {svc.service_name}")
        elif svc.service_type == 'l2vpn':
            commands.append(f"no l2vpn bridge-domains bridge-domain {svc.service_name}")
        elif svc.service_type == 'flowspec-vpn':
            commands.append(f"no network-services vrf instance {svc.service_name}")
        
        if include_interfaces:
            for iface in svc.interfaces:
                interfaces_to_delete.add(iface)
                # Track PWHE parents (phX) for deletion after sub-interfaces
                if re.match(r'^ph\d+\.\d+$', iface):
                    parent = iface.rsplit('.', 1)[0]  # ph1001.1 -> ph1001
                    pwhe_parents_to_delete.add(parent)
    
    # STEP 2: Delete multihoming references BEFORE interfaces
    # Multihoming ESI config references interfaces - must be deleted first
    if include_interfaces and current_config:
        existing_mh = parse_existing_multihoming(current_config)
        mh_ifaces_to_delete = []
        
        # Find which MH interfaces we're about to delete
        for iface in interfaces_to_delete:
            if iface in existing_mh:
                mh_ifaces_to_delete.append(iface)
        
        # Also check parent interfaces (phX without .Y)
        for parent in pwhe_parents_to_delete:
            if parent in existing_mh:
                mh_ifaces_to_delete.append(parent)
        
        if mh_ifaces_to_delete:
            # DNOS requires hierarchical syntax for multihoming delete
            # Enter the multihoming context, delete interfaces, exit
            commands.append("network-services")
            commands.append("  multihoming")
            for iface in sorted(mh_ifaces_to_delete, key=lambda x: extract_service_number(x)):
                commands.append(f"    no interface {iface}")
            commands.append("  !")
            commands.append("!")
    
    # STEP 3: Delete sub-interfaces (they depend on nothing after MH removal)
    sub_interfaces = sorted(
        [i for i in interfaces_to_delete if '.' in i],
        key=lambda x: extract_service_number(x)
    )
    for iface in sub_interfaces:
        commands.append(f"no interfaces {iface}")
    
    # STEP 4: Delete PWHE parent interfaces (phX)
    # Only delete parents that had ALL their sub-interfaces deleted
    for parent in sorted(pwhe_parents_to_delete, key=lambda x: extract_service_number(x)):
        commands.append(f"no interfaces {parent}")
    
    # STEP 5: Delete any non-sub-interface interfaces (rare, but handle it)
    other_interfaces = sorted(
        [i for i in interfaces_to_delete if '.' not in i and i not in pwhe_parents_to_delete],
        key=lambda x: extract_service_number(x)
    )
    for iface in other_interfaces:
        commands.append(f"no interfaces {iface}")
    
    return commands


def show_scale_wizard(multi_ctx: 'MultiDeviceContext', return_config: bool = False) -> Any:
    """Show the Scale Up/Down wizard for bulk service operations.
    
    Args:
        multi_ctx: MultiDeviceContext with connected devices
        return_config: If True, return generated config string instead of pushing
        
    Returns:
        If return_config=True: Generated config string or None if cancelled
        If return_config=False: True if changes were made, False otherwise
    """
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]              📊 Scale Up/Down Services Wizard                     [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════════[/bold cyan]")
    
    # Parse services from all devices
    device_services: Dict[str, Dict[str, List[ServiceScale]]] = {}
    
    for dev in multi_ctx.devices:
        config = multi_ctx.configs.get(dev.hostname, "")
        if config:
            device_services[dev.hostname] = parse_services_from_config(config)
    
    if not device_services:
        console.print("[red]No device configurations loaded. Run Refresh first.[/red]")
        return False
    
    # Show current scale summary
    console.print("\n[bold]Current Service Scale:[/bold]")
    
    summary_table = Table(box=box.ROUNDED)
    summary_table.add_column("Device", style="cyan")
    summary_table.add_column("FXC", justify="right")
    summary_table.add_column("L2VPN", justify="right")
    summary_table.add_column("EVPN", justify="right")
    summary_table.add_column("VPWS", justify="right")
    summary_table.add_column("VRF", justify="right")
    summary_table.add_column("Total Interfaces", justify="right", style="dim")
    
    for hostname, services in device_services.items():
        total_ifaces = sum(
            len(svc.interfaces) 
            for svc_list in services.values() 
            for svc in svc_list
        )
        summary_table.add_row(
            hostname,
            f"{len(services['fxc']):,}",
            f"{len(services['l2vpn']):,}",
            f"{len(services['evpn']):,}",
            f"{len(services['vpws']):,}",
            f"{len(services.get('vrf', [])):,}",
            f"{total_ifaces:,}"
        )
    
    console.print(summary_table)
    
    # Select operation
    console.print("\n[bold]Select Operation:[/bold]")
    console.print("  [1] [red]Scale DOWN[/red] - Delete services with correlated interfaces")
    console.print("  [2] [green]Scale UP[/green] - Add more services from last configured")
    console.print("  [B] Back")
    
    op_choice = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="b").lower()
    
    if op_choice == "b":
        return None if return_config else False
    
    if op_choice == "1":
        return _scale_down_wizard(multi_ctx, device_services, return_config=return_config)
    else:
        return _scale_up_wizard(multi_ctx, device_services, return_config=return_config)


def _scale_down_wizard(multi_ctx: 'MultiDeviceContext', device_services: Dict[str, Dict[str, List[ServiceScale]]], return_config: bool = False) -> Any:
    """Wizard for scaling down (deleting) services."""
    
    console.print("\n[bold red]━━━ Scale DOWN: Delete Services ━━━[/bold red]")
    
    # Select service type
    console.print("\n[bold]Select Service Type to Scale Down:[/bold]")
    console.print("  [1] FXC (Flexible Cross-Connect) + PWHE interfaces")
    console.print("  [2] L2VPN instances + sub-interfaces")
    console.print("  [3] EVPN instances + sub-interfaces")
    console.print("  [4] VPWS instances + sub-interfaces")
    console.print("  [5] VRF (L3VPN) instances + interfaces")
    console.print("  [6] FlowSpec VPN (VRFs with FlowSpec address-families)")
    console.print("  [B] Back")
    
    type_choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "5", "6", "b", "B"], default="b").lower()
    
    if type_choice == "b":
        return False
    
    svc_type_map = {"1": "fxc", "2": "l2vpn", "3": "evpn", "4": "vpws", "5": "vrf", "6": "flowspec-vpn"}
    svc_type = svc_type_map.get(type_choice, "fxc")
    svc_type_name = {"fxc": "FXC", "l2vpn": "L2VPN", "evpn": "EVPN", "vpws": "VPWS", "vrf": "VRF", "flowspec-vpn": "FlowSpec VPN"}[svc_type]
    
    # Show current services of this type
    console.print(f"\n[bold]Current {svc_type_name} Services:[/bold]")
    
    for hostname, services in device_services.items():
        svc_list = services.get(svc_type, [])
        if svc_list:
            console.print(f"\n[cyan]{hostname}:[/cyan]")
            console.print(f"  Total: {len(svc_list):,} services")
            if svc_list:
                first_num = svc_list[0].service_number
                last_num = svc_list[-1].service_number
                console.print(f"  Range: #{first_num} to #{last_num}")
                
                # Show interface count
                total_ifaces = sum(len(s.interfaces) for s in svc_list)
                pwhe_count = sum(1 for s in svc_list for i in s.interfaces if i.startswith('ph'))
                console.print(f"  Correlated interfaces: {total_ifaces:,} (PWHE: {pwhe_count:,})")
                
                if svc_type == 'flowspec-vpn' and hasattr(svc_list[0], 'flowspec_afs') and svc_list[0].flowspec_afs:
                    afs = ', '.join(svc_list[0].flowspec_afs)
                    console.print(f"  FlowSpec AFs: {afs}")
                    if svc_list[0].rd:
                        console.print(f"  RD pattern: {svc_list[0].rd}")
                    if svc_list[0].rt:
                        console.print(f"  RT pattern: {svc_list[0].rt}")
    
    # Get range to delete
    console.print("\n[bold]Specify Range to Delete:[/bold]")
    console.print("[dim]Examples:[/dim]")
    console.print("  [dim]• 'last 300' - delete last 300 services[/dim]")
    console.print("  [dim]• '100-400' - delete services #100 to #400[/dim]")
    console.print("  [dim]• '100,200,300' - delete specific services[/dim]")
    console.print("  [dim]• '1-100,500-600' - delete multiple ranges[/dim]")
    
    range_spec = Prompt.ask("\nEnter range specification")
    if not range_spec:
        return False
    
    # Calculate what will be deleted per device
    delete_preview: Dict[str, Tuple[List[ServiceScale], List[str]]] = {}
    
    for hostname, services in device_services.items():
        svc_list = services.get(svc_type, [])
        if not svc_list:
            continue
            
        max_num = max(s.service_number for s in svc_list)
        numbers_to_delete = parse_range_spec(range_spec, max_num)
        
        services_to_delete = [s for s in svc_list if s.service_number in numbers_to_delete]
        interfaces_to_delete = []
        for s in services_to_delete:
            interfaces_to_delete.extend(s.interfaces)
        
        if services_to_delete:
            delete_preview[hostname] = (services_to_delete, interfaces_to_delete)
    
    if not delete_preview:
        console.print("[yellow]No services match the specified range.[/yellow]")
        return False
    
    # Show preview
    console.print("\n[bold red]⚠ DELETE PREVIEW:[/bold red]")
    
    preview_table = Table(box=box.ROUNDED)
    preview_table.add_column("Device", style="cyan")
    preview_table.add_column(f"{svc_type_name} to Delete", justify="right", style="red")
    preview_table.add_column("Interfaces to Delete", justify="right", style="red")
    preview_table.add_column("Sample Names", style="dim")
    
    total_services = 0
    total_interfaces = 0
    
    for hostname, (svcs, ifaces) in delete_preview.items():
        total_services += len(svcs)
        total_interfaces += len(ifaces)
        
        sample = ", ".join(s.service_name for s in svcs[:3])
        if len(svcs) > 3:
            sample += f"... (+{len(svcs)-3} more)"
        
        preview_table.add_row(
            hostname,
            f"{len(svcs):,}",
            f"{len(ifaces):,}",
            sample
        )
    
    console.print(preview_table)
    console.print(f"\n[bold red]TOTAL: {total_services:,} services + {total_interfaces:,} interfaces will be DELETED[/bold red]")
    
    # Options
    console.print("\n[bold]Options:[/bold]")
    console.print("  [1] Delete services + correlated interfaces (recommended)")
    console.print("  [2] Delete services ONLY (keep interfaces)")
    console.print("  [3] Show detailed delete commands")
    console.print("  [B] Cancel")
    
    del_choice = Prompt.ask("Select", choices=["1", "2", "3", "b", "B"], default="b").lower()
    
    if del_choice == "b":
        return False
    
    include_interfaces = del_choice != "2"
    
    if del_choice == "3":
        # Show commands (just display, no extra confirmation - final confirmation below handles it)
        console.print("\n[bold]Delete Commands Preview:[/bold]")
        for hostname, (svcs, _) in delete_preview.items():
            console.print(f"\n[cyan]# {hostname}[/cyan]")
            current_config = multi_ctx.configs.get(hostname, "")
            commands = generate_delete_commands(svcs, include_interfaces, current_config)
            for cmd in commands[:20]:
                console.print(f"  {cmd}")
            if len(commands) > 20:
                console.print(f"  [dim]... and {len(commands)-20} more commands[/dim]")
    
    # Single final confirmation (no duplicate prompts!)
    if not Confirm.ask(f"\n[bold red]⚠ DELETE {total_services:,} services and {total_interfaces if include_interfaces else 0:,} interfaces?[/bold red]", default=False):
        console.print("[yellow]Cancelled.[/yellow]")
        return None if return_config else False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # RETURN CONFIG MODE - Return generated delete commands instead of pushing
    # ═══════════════════════════════════════════════════════════════════════════
    if return_config:
        # Generate delete commands for all devices and return
        all_commands = []
        for hostname, (svcs, _) in delete_preview.items():
            current_config = multi_ctx.configs.get(hostname, "")
            commands = generate_delete_commands(svcs, include_interfaces, current_config)
            all_commands.extend(commands)
        combined = '\n'.join(all_commands)
        console.print(f"\n[green]✓ Generated {len(all_commands):,} delete commands[/green]")
        return combined
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PUSH OPTIONS - File save, push method, live terminal
    # ═══════════════════════════════════════════════════════════════════════════
    console.print("\n[bold cyan]━━━ Delete Options ━━━[/bold cyan]")
    
    from ..utils import get_device_config_dir, timestamp_filename
    from pathlib import Path
    
    # Push method selection FIRST
    console.print("\n[bold]Select push method:[/bold]")
    console.print("  [1] Terminal Paste (paste directly into CLI)")
    console.print("  [2] File Merge (upload file + load merge)")
    push_method = Prompt.ask("Method", choices=["1", "2"], default="1")
    use_terminal_paste = (push_method == "1")
    
    # Save file: required for File Merge, optional for Terminal Paste
    if use_terminal_paste:
        if Confirm.ask("Save delete commands to file?", default=False):
            for hostname, (svcs, ifaces) in delete_preview.items():
                config_dir = get_device_config_dir(hostname)
                filename = f"scale_down_{svc_type_name}_{len(svcs)}_{timestamp_filename()}.txt"
                filepath = config_dir / filename
                current_config = multi_ctx.configs.get(hostname, "")
                commands = generate_delete_commands(svcs, include_interfaces, current_config)
                with open(filepath, 'w') as f:
                    f.write("\n".join(commands))
                console.print(f"  [green]✓[/green] Saved: {filepath}")
    else:
        # Auto-save for file merge
        for hostname, (svcs, ifaces) in delete_preview.items():
            config_dir = get_device_config_dir(hostname)
            filename = f"scale_down_{svc_type_name}_{len(svcs)}_{timestamp_filename()}.txt"
            filepath = config_dir / filename
            current_config = multi_ctx.configs.get(hostname, "")
            commands = generate_delete_commands(svcs, include_interfaces, current_config)
            with open(filepath, 'w') as f:
                f.write("\n".join(commands))
            console.print(f"  [dim]Auto-saved for upload: {filepath}[/dim]")
    
    # Live terminal output
    show_live_terminal = Confirm.ask("Show live terminal output?", default=True)
    
    # Generate and execute delete commands with live progress display
    console.print("\n[bold red]🗑️ Deleting Scale DOWN Configuration[/bold red]")
    
    from ..config_pusher import ConfigPusher, get_learned_timing_by_scale
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from rich.live import Live
    from rich.panel import Panel
    from rich.columns import Columns
    import threading
    import time
    
    # Prepare delete configs per device
    device_delete_configs = {}
    for hostname, (svcs, ifaces) in delete_preview.items():
        current_config = multi_ctx.configs.get(hostname, "")
        commands = generate_delete_commands(svcs, include_interfaces, current_config)
        device_delete_configs[hostname] = {
            'config': "\n".join(commands),
            'services': len(svcs),
            'interfaces': len(ifaces) if include_interfaces else 0
        }
    
    # Track progress per device - with terminal buffer for split-screen
    device_progress = {
        hostname: {
            "status": "pending", 
            "progress": 0, 
            "message": "Waiting...",
            "terminal_lines": []  # Buffer for terminal output
        } 
        for hostname in device_delete_configs.keys()
    }
    results = {}
    progress_lock = threading.Lock()
    MAX_TERMINAL_LINES = 12  # Lines to show per device terminal
    
    total_commands = sum(len(d['config'].splitlines()) for d in device_delete_configs.values())
    
    # Get accurate timing estimate for delete operations
    from ..config_pusher import get_accurate_push_estimates
    
    # Combine all delete configs for estimation
    combined_delete_config = '\n'.join(d['config'] for d in device_delete_configs.values())
    
    estimates = get_accurate_push_estimates(
        config_text=combined_delete_config,
        platform=list(device_delete_configs.values())[0].get('device', {}).get('platform', 'SA-36CD-S') if device_delete_configs else "SA-36CD-S",
        include_delete=True
    )
    
    # For delete operations, terminal paste is typically used
    estimated_seconds = estimates['estimates']['terminal_paste']['total'] / len(device_delete_configs) if device_delete_configs else 60
    source = estimates['source']
    source_detail = estimates['source_detail']
    
    def format_time(seconds: float) -> str:
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"
    
    console.print(f"[dim]Executing {total_commands:,} delete commands across {len(device_delete_configs)} devices[/dim]")
    
    if source == 'similar_push':
        console.print(f"[green]📊 Est. ~{format_time(estimated_seconds)} per device - {source_detail}[/green]\n")
    elif source == 'scale_type':
        console.print(f"[yellow]📊 Est. ~{format_time(estimated_seconds)} per device - {source_detail}[/yellow]\n")
    else:
        console.print(f"[dim]📊 Est. ~{format_time(estimated_seconds)} per device - {source_detail}[/dim]\n")
    
    operation_start_time = time.time()
    
    def render_split_screen():
        """Render split-screen layout with per-device terminal panels - FIXED HEIGHT."""
        from rich.text import Text
        panels = []
        
        # Fixed height for consistent display (no jumping)
        PANEL_HEIGHT = MAX_TERMINAL_LINES + 5
        
        for hostname, status in device_progress.items():
            status_str = status["status"]
            progress_pct = status["progress"]
            message = status["message"]
            terminal_lines = status.get("terminal_lines", [])
            
            # Build content with Text - use append with style, not markup strings
            content = Text()
            
            # Status line
            if status_str == "pending":
                content.append("⏳ Pending\n", style="dim")
                filled = 0
                bar_style = "dim"
            elif status_str == "connecting":
                content.append("🔌 Connecting...\n", style="yellow")
                filled = 4
                bar_style = "yellow"
            elif status_str == "deleting":
                filled = int(progress_pct / 5)  # 20 char bar
                content.append(f"🗑️ Deleting {message[:20]}\n", style="red")
                bar_style = "red"
            elif status_str == "committing":
                content.append("⚙️ Committing...\n", style="magenta")
                filled = 16
                bar_style = "magenta"
            elif status_str == "success":
                content.append("✓ Success!\n", style="green")
                filled = 20
                bar_style = "green"
            elif status_str == "failed":
                content.append(f"✗ {message[:25]}\n", style="red")
                filled = 20
                bar_style = "red"
            else:
                content.append(f"{status_str}\n")
                filled = 0
                bar_style = "dim"
            
            # Progress bar - use filled (0-20) to compute displayed percentage
            actual_pct_display = (filled * 5) if status_str == "uploading" else progress_pct
            content.append("Progress: ")
            content.append("█" * filled, style=bar_style)
            content.append("░" * (20 - filled), style="dim")
            content.append(f" {actual_pct_display}%\n", style=bar_style)
            
            PANEL_WIDTH = 70  # Wider panel for better error visibility
            content.append("─" * PANEL_WIDTH + "\n")
            
            # Add terminal output - always fill to fixed height
            lines_to_show = terminal_lines[-MAX_TERMINAL_LINES:] if terminal_lines else []
            lines_added = 0
            
            for line in lines_to_show:
                clean = line[:PANEL_WIDTH].replace('[', '\\[').replace(']', '\\]')
                
                # Detect error patterns and show in red
                is_error = any(err in clean.lower() for err in ['error', 'failed', 'cannot', 'hook failed', 'stag', 'limit'])
                
                if clean.startswith('→'):
                    content.append(f"  {clean}\n", style="bright_red")
                elif clean.startswith('←'):
                    content.append(f"  {clean}\n", style="yellow")
                elif clean.startswith('✓'):
                    content.append(f"  {clean}\n", style="green")
                elif clean.startswith('✗') or is_error:
                    content.append(f"  {clean}\n", style="bold red")
                elif clean.startswith('⏳'):
                    content.append(f"  {clean}\n", style="yellow")
                else:
                    content.append(f"  {clean}\n", style="dim")
                lines_added += 1
            
            # Pad to fixed height
            while lines_added < MAX_TERMINAL_LINES:
                content.append("\n")
                lines_added += 1
            
            # Determine border color
            if status_str == "success":
                border_style = "green"
            elif status_str == "failed":
                border_style = "red"
            elif status_str in ("deleting", "committing"):
                border_style = "red"
            else:
                border_style = "dim"
            
            panel = Panel(
                content,
                title=f"[bold white] {hostname} [/bold white]",
                border_style=border_style,
                height=PANEL_HEIGHT,
                expand=True,
                padding=(0, 1)
            )
            panels.append(panel)
        
        # Return columns of panels (side-by-side)
        return Columns(panels, expand=True, equal=True)
    
    def delete_device(hostname: str) -> Tuple[str, bool, str]:
        """Delete config from a single device."""
        device = next((d for d in multi_ctx.devices if d.hostname == hostname), None)
        if not device:
            return hostname, False, "Device not found"
        
        delete_info = device_delete_configs[hostname]
        delete_config = delete_info['config']
        svc_count = delete_info['services']
        iface_count = delete_info['interfaces']
        
        def add_terminal_line(line: str):
            """Add line to device's terminal buffer."""
            with progress_lock:
                device_progress[hostname]["terminal_lines"].append(line)
                # Keep buffer limited
                if len(device_progress[hostname]["terminal_lines"]) > 50:
                    device_progress[hostname]["terminal_lines"] = device_progress[hostname]["terminal_lines"][-50:]
        
        try:
            with progress_lock:
                device_progress[hostname]["status"] = "connecting"
                device_progress[hostname]["progress"] = 10
                device_progress[hostname]["message"] = "Connecting via SSH..."
            add_terminal_line("Connecting to device...")
            
            method_str = "Pasting" if use_terminal_paste else "Uploading"
            with progress_lock:
                device_progress[hostname]["status"] = "deleting"
                device_progress[hostname]["progress"] = 30
                device_progress[hostname]["message"] = f"{method_str} delete for {svc_count} services..."
            add_terminal_line(f"Deleting {svc_count} services, {iface_count} interfaces...")
            
            pusher = ConfigPusher(timeout=120, commit_timeout=1800)
            
            def progress_callback(msg: str, pct: int):
                with progress_lock:
                    if "commit" in msg.lower():
                        device_progress[hostname]["status"] = "committing"
                        device_progress[hostname]["progress"] = 85 + int(pct * 0.15)  # 85-100%
                    else:
                        # Extract actual progress from message "Pasting line X/Y..."
                        line_match = re.search(r'(\d+)/(\d+)', msg)
                        if line_match:
                            current = int(line_match.group(1))
                            total = int(line_match.group(2))
                            # Pasting takes 0-80% of progress
                            actual_pct = int((current / total) * 80) if total > 0 else pct
                            device_progress[hostname]["progress"] = actual_pct
                        else:
                            device_progress[hostname]["progress"] = min(80, pct)
                    device_progress[hostname]["message"] = msg
                add_terminal_line(msg)
            
            def live_output_callback(output: str):
                """Capture live output into device's terminal buffer."""
                for line in output.strip().split('\n'):
                    if line.strip():
                        add_terminal_line(line.strip()[-60:])  # Last 60 chars
            
            # Use terminal paste or file merge based on user selection
            # DON'T use show_live_terminal (causes flickering) - use live_output_callback instead
            if use_terminal_paste:
                success, output = pusher.push_config_terminal_paste(
                    device, 
                    delete_config, 
                    dry_run=False, 
                    progress_callback=progress_callback,
                    live_output_callback=live_output_callback if show_live_terminal else None,
                    show_live_terminal=False  # We handle display ourselves
                )
            else:
                success, output = pusher.push_config_merge(
                    device, 
                    delete_config, 
                    dry_run=False, 
                    progress_callback=progress_callback
                )
            
            if success:
                with progress_lock:
                    device_progress[hostname]["status"] = "success"
                    device_progress[hostname]["progress"] = 100
                    device_progress[hostname]["message"] = f"Deleted {svc_count} svc + {iface_count} iface"
                add_terminal_line("✓ Delete completed successfully!")
                return hostname, True, f"Deleted {svc_count} services"
            else:
                error_msg = output.strip().split('\n')[-1] if output else "Unknown error"
                with progress_lock:
                    device_progress[hostname]["status"] = "failed"
                    device_progress[hostname]["progress"] = 50
                    device_progress[hostname]["message"] = error_msg
                add_terminal_line(f"✗ Error: {error_msg}")
                return hostname, False, error_msg
                
        except Exception as e:
            error_msg = str(e).split('\n')[-1]
            with progress_lock:
                device_progress[hostname]["status"] = "failed"
                device_progress[hostname]["progress"] = 0
                device_progress[hostname]["message"] = error_msg
            add_terminal_line(f"✗ Exception: {error_msg}")
            return hostname, False, error_msg
    
    # Execute in parallel with split-screen live display
    with Live(render_split_screen(), refresh_per_second=4, console=console, transient=False) as live:
        with ThreadPoolExecutor(max_workers=len(device_delete_configs)) as executor:
            futures = {executor.submit(delete_device, hostname): hostname for hostname in device_delete_configs.keys()}
            
            while any(f.running() for f in futures):
                live.update(render_split_screen())
                time.sleep(0.25)
            
            for future in as_completed(futures):
                hostname, success, message = future.result()
                results[hostname] = (success, message)
            
            live.update(render_split_screen())
    
    # Summary
    success_count = sum(1 for s, _ in results.values() if s)
    total_time = time.time() - operation_start_time
    
    console.print(f"\n[bold]Result: {success_count}/{len(delete_preview)} devices updated[/bold]")
    console.print(f"[dim]Total time: {total_time/60:.1f} minutes ({total_time:.0f}s)[/dim]")
    
    # Auto-refresh configs after successful push
    if success_count > 0:
        console.print("\n[dim]Refreshing device configurations...[/dim]")
        multi_ctx.discover_all()
        console.print("[green]✓ Config cache updated[/green]")
    
    return success_count > 0


# ═══════════════════════════════════════════════════════════════════════════════
# QUICK SUGGESTIONS ENGINE - Context-aware suggestions for all wizard levels
# ═══════════════════════════════════════════════════════════════════════════════

def _generate_scale_up_suggestions(
    multi_ctx: 'MultiDeviceContext',
    device_services: Dict[str, Dict[str, List[ServiceScale]]]
) -> List[Dict]:
    """
    Generate smart suggestions based on:
    1. Cross-device analysis (what ALL devices have, not just selected ones)
    2. Current device's configuration pattern
    3. Earlier wizard selections (cached pool status, etc.)
    4. Configuration gaps (missing matching services)
    
    IMPORTANT: Even in single-device mode, we load ALL device configs from
    db/configs to find patterns and anomalies across the entire topology.
    """
    suggestions = []
    
    # Get current device context - use first device from device_services
    hostnames = list(device_services.keys())
    if not hostnames:
        return suggestions
    
    current_hostname = hostnames[0]
    current_config = multi_ctx.configs.get(current_hostname, "")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # LOAD ALL DEVICE CONFIGS - Not just selected devices!
    # This enables cross-device analysis even in single-device mode
    # ═══════════════════════════════════════════════════════════════════════════
    all_device_services: Dict[str, Dict[str, List[ServiceScale]]] = {}
    
    # Start with devices in current session
    all_device_services.update(device_services)
    
    # Load OTHER device configs from db/configs
    config_base = "/home/dn/SCALER/db/configs"
    try:
        for device_dir in os.listdir(config_base):
            if device_dir in all_device_services:
                continue  # Already have this one
            
            config_path = os.path.join(config_base, device_dir, "running.txt")
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config = f.read()
                    # Parse services from this config
                    all_device_services[device_dir] = parse_services_from_config(config)
                except Exception:
                    pass  # Skip devices with unreadable configs
    except Exception:
        pass  # If db/configs doesn't exist, just use what we have
    
    # Analyze ALL devices (not just selected ones)
    device_analysis = {}
    for hostname, services in all_device_services.items():
        device_info = {
            "hostname": hostname,
            "fxc_count": len(services.get("fxc", [])),
            "evpn_count": len(services.get("evpn", [])),
            "l2vpn_count": len(services.get("l2vpn", [])),
            "vpws_count": len(services.get("vpws", [])),
            "flowspec_vpn_count": len(services.get("flowspec-vpn", [])),
            "last_fxc": services.get("fxc", [])[-1] if services.get("fxc") else None,
            "last_evpn": services.get("evpn", [])[-1] if services.get("evpn") else None,
            "last_flowspec_vpn": services.get("flowspec-vpn", [])[-1] if services.get("flowspec-vpn") else None,
            "interface_type": None,
            "in_session": hostname in device_services  # Track if in current session
        }
        
        # Detect interface type from last service
        if device_info["last_fxc"] and device_info["last_fxc"].interfaces:
            iface = device_info["last_fxc"].interfaces[0]
            if iface.startswith('ph'):
                device_info["interface_type"] = "PWHE"
            elif iface.startswith(('ge', 'xe', 'et')):
                device_info["interface_type"] = "L2-AC"
            elif iface.startswith(('bundle', 'lag')):
                device_info["interface_type"] = "Bundle"
        
        device_analysis[hostname] = device_info
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SUGGESTION 1: SMART PEERING GAP DETECTION
    # Detects when devices share some services but one has more than the other
    # E.g., PE-1 has 3022 FXC, PE-4 has 2300 → Suggest 722 to match additional
    # Works even in single-device mode by comparing against ALL known devices!
    # ═══════════════════════════════════════════════════════════════════════════
    if current_hostname and len(device_analysis) >= 1:
        current = device_analysis.get(current_hostname, {})
        current_fxc = current.get("fxc_count", 0)
        current_iface_type = current.get("interface_type", "PWHE")
        
        for other_hostname, other_info in device_analysis.items():
            if other_hostname == current_hostname:
                continue
            
            other_fxc = other_info.get("fxc_count", 0)
            other_iface_type = other_info.get("interface_type", "PWHE")
            
            # Detect peering relationship: both have FXC services
            if current_fxc > 0 and other_fxc > 0:
                # Calculate shared vs additional services
                shared_count = min(current_fxc, other_fxc)
                
                if other_fxc > current_fxc:
                    # Other device has MORE services - suggest adding the difference
                    additional = other_fxc - current_fxc
                    
                    # Smart description based on interface types
                    if other_iface_type == "PWHE" and current_iface_type == "L2-AC":
                        # PE-4 (L2-AC) needs to add termination for PE-1's (PWHE) additional services
                        suggestions.insert(0, {  # Insert at top - highest priority
                            "type": "match_peer_additional",
                            "description": f"Add {additional:,} L2-AC services to terminate {other_hostname}'s additional PWHE",
                            "details": f"Shared: {shared_count:,} | {other_hostname} has {additional:,} more → Add matching L2-AC",
                            "service_type": "fxc",
                            "count": additional,
                            "interface_type": "L2-AC",
                            "source_device": other_hostname,
                            "start_num": current_fxc + 1,  # Continue from current last
                            "apply_func": _apply_peer_match_suggestion,
                        })
                    elif other_iface_type == current_iface_type:
                        # Same interface type - simple match
                        suggestions.append({
                            "type": "match_peer",
                            "description": f"Match {other_hostname}: Add {additional:,} {current_iface_type} services",
                            "details": f"Shared: {shared_count:,} | Gap: {additional:,} (FXC-{current_fxc+1} to FXC-{other_fxc})",
                            "service_type": "fxc",
                            "count": additional,
                            "interface_type": current_iface_type,
                            "source_device": other_hostname,
                            "start_num": current_fxc + 1,
                            "apply_func": _apply_peer_match_suggestion,
                        })
                    else:
                        # Different interface types - explain the cross-type match
                        suggestions.append({
                            "type": "match_peer_cross",
                            "description": f"Add {additional:,} {current_iface_type} to match {other_hostname}'s {other_iface_type}",
                            "details": f"{current_hostname}: {current_fxc:,} ({current_iface_type}) ← {other_hostname}: {other_fxc:,} ({other_iface_type})",
                            "service_type": "fxc",
                            "count": additional,
                            "interface_type": current_iface_type,
                            "source_device": other_hostname,
                            "start_num": current_fxc + 1,
                            "apply_func": _apply_peer_match_suggestion,
                        })
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SUGGESTION: L2-AC TERMINATION - Offer to terminate peer's PWHE with L2-AC
    # This appears when BOTH devices use PWHE but user might want to switch to L2-AC
    # E.g., PE-2 has PWHE, PE-1 has PWHE - offer L2-AC termination option
    # ═══════════════════════════════════════════════════════════════════════════
    if current_hostname and len(device_analysis) >= 2:
        current = device_analysis.get(current_hostname, {})
        current_iface_type = current.get("interface_type", "PWHE")
        
        # Only offer if current device uses PWHE (L2-AC devices already terminate)
        if current_iface_type == "PWHE":
            for other_hostname, other_info in device_analysis.items():
                if other_hostname == current_hostname:
                    continue
                
                other_fxc = other_info.get("fxc_count", 0)
                other_iface_type = other_info.get("interface_type", "PWHE")
                
                # Peer has PWHE services - offer L2-AC termination option
                if other_fxc > 0 and other_iface_type == "PWHE":
                    suggestions.append({
                        "type": "l2ac_termination",
                        "description": f"[magenta]Create L2-AC on {current_hostname} to terminate {other_hostname}'s PWHE[/magenta]",
                        "details": f"Switch interface type: Use L2-AC sub-interfaces instead of PWHE",
                        "service_type": "fxc",
                        "count": other_fxc,
                        "interface_type": "L2-AC",
                        "source_device": other_hostname,
                        "apply_func": _apply_l2ac_termination_suggestion,
                    })
                    break  # Only add one L2-AC suggestion
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SUGGESTION 2: Continue current device's pattern (fallback if no peers)
    # ═══════════════════════════════════════════════════════════════════════════
    if current_hostname:
        current = device_analysis.get(current_hostname, {})
        
        # Suggest continuing FXC with same interface type
        if current.get("last_fxc"):
            last_fxc = current["last_fxc"]
            iface_type = current.get("interface_type", "PWHE")
            last_num = last_fxc.service_number
            
            # Check for pool status suggestion
            suggested_count = 100  # Default
            pool_note = ""
            if hasattr(multi_ctx, 'cached_pool_status') and multi_ctx.cached_pool_status:
                pool = multi_ctx.cached_pool_status
                max_add = pool.get("max_additional_pwhe_services", 0)
                if max_add > 0:
                    suggested_count = min(max_add, 500)  # Cap at 500 for suggestion
                    pool_note = f" (pool limit: {max_add:,})"
            
            # Only add this if we don't already have a peer-match suggestion
            if not any(s.get("type", "").startswith("match_peer") for s in suggestions):
                suggestions.append({
                    "type": "continue_fxc",
                    "description": f"Add {suggested_count:,} more FXC services to {current_hostname}",
                    "details": f"Continue from FXC-{last_num} with {iface_type} interfaces{pool_note}",
                    "service_type": "fxc",
                    "count": suggested_count,
                    "interface_type": iface_type,
                    "start_num": last_num + 1,
                    "apply_func": _apply_continue_fxc_suggestion,
                })
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SUGGESTION 4: Scale to match multihoming partner
    # ═══════════════════════════════════════════════════════════════════════════
    # Check if there's an ESI-paired device with different service count
    if current_hostname and "multihoming" in current_config.lower():
        # Find ESI values in current config
        esi_pattern = r'ethernet-segment\s+([0-9a-fA-F:]+)'
        esis = re.findall(esi_pattern, current_config)
        
        for other_hostname, other_info in device_analysis.items():
            if other_hostname == current_hostname:
                continue
            
            # Check if other device shares ESI (would need to check other config)
            # For now, assume PE-1 and PE-2 are MH partners if both have PWHE
            if (current.get("interface_type") == "PWHE" and 
                other_info.get("interface_type") == "PWHE"):
                
                current_fxc = current.get("fxc_count", 0)
                other_fxc = other_info.get("fxc_count", 0)
                
                if current_fxc != other_fxc:
                    diff = abs(other_fxc - current_fxc)
                    action = "Add" if other_fxc > current_fxc else "Already ahead by"
                    
                    if other_fxc > current_fxc:
                        suggestions.append({
                            "type": "mh_sync",
                            "description": f"Sync with MH partner {other_hostname}: Add {diff:,} FXC",
                            "details": f"Both devices should have matching services for multihoming",
                            "service_type": "fxc",
                            "count": diff,
                            "interface_type": "PWHE",
                            "source_device": other_hostname,
                            "apply_func": _apply_mh_sync_suggestion,
                        })
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SUGGESTION 5: FlowSpec VPN - continue adding VRFs with FlowSpec
    # ═══════════════════════════════════════════════════════════════════════════
    if current_hostname:
        current = device_analysis.get(current_hostname, {})
        fs_vpn_list = all_device_services.get(current_hostname, {}).get('flowspec-vpn', [])
        fs_vpn_count = len(fs_vpn_list)
        
        if fs_vpn_count > 0:
            last_fs = fs_vpn_list[-1]
            suggested = min(100, 512 - fs_vpn_count)  # max 512 VRFs with flowspec
            if suggested > 0:
                suggestions.append({
                    "type": "continue_flowspec_vpn",
                    "description": f"Add {suggested:,} more FlowSpec VPN VRFs to {current_hostname}",
                    "details": f"Continue from {last_fs.service_name} "
                               f"({fs_vpn_count:,} existing, limit 512)",
                    "service_type": "flowspec-vpn",
                    "count": suggested,
                    "start_num": last_fs.service_number + 1,
                    "apply_func": _apply_flowspec_vpn_suggestion,
                })
    
    return suggestions


def _execute_scale_up(
    multi_ctx: 'MultiDeviceContext',
    device_services: Dict[str, Dict[str, List[ServiceScale]]],
    svc_type: str,
    count: int,
    interface_type: str = "PWHE",
    start_num: Optional[int] = None,
    l2ac_parent: Optional[str] = None
) -> bool:
    """
    Execute a streamlined Scale UP with pre-filled values from suggestions.
    
    This is the core execution function called by suggestion handlers.
    It skips the interactive prompts and goes directly to config generation.
    """
    from scaler.config_pusher import ConfigPusher, get_learned_timing_by_scale, save_timing_record
    
    # Determine starting number if not provided
    if start_num is None:
        last_service = None
        for hostname, services in device_services.items():
            svc_list = services.get(svc_type, [])
            if svc_list:
                last = svc_list[-1]
                if last_service is None or last.service_number > last_service.service_number:
                    last_service = last
        start_num = (last_service.service_number + 1) if last_service else 1
    
    end_num = start_num + count - 1
    
    svc_type_name = {"fxc": "FXC", "vpws": "EVPN-VPWS", "evpn": "EVPN", "l2vpn": "L2VPN", "flowspec-vpn": "FlowSpec VPN"}.get(svc_type, svc_type.upper())
    console.print(f"\n[bold green]━━━ Quick Scale UP: {count:,} {svc_type_name} services ━━━[/bold green]")
    console.print(f"  Range: #{start_num} to #{end_num}")
    console.print(f"  Interface: {interface_type}")
    if l2ac_parent:
        console.print(f"  L2-AC Parent: {l2ac_parent}")
    
    # Prompt for missing L2-AC parent if needed - auto-detect from device config or LLDP
    if interface_type.upper() == "L2-AC" and not l2ac_parent:
        # Detect existing L2-AC parent from device's configuration
        detected_parent = _detect_l2ac_parent_from_config(multi_ctx, device_services)
        
        # Get LLDP-connected interfaces for alternative selection
        hostname = list(device_services.keys())[0] if device_services else None
        lldp_interfaces = get_interfaces_with_lldp(hostname, dn_only=True) if hostname else []
        
        if lldp_interfaces and not detected_parent:
            # Show LLDP-based selection if no existing L2-AC detected
            console.print(f"\n[bold cyan]Physical Interfaces with DN Neighbors:[/bold cyan]")
            for i, n in enumerate(lldp_interfaces[:5], 1):
                console.print(f"  [{i}] [green]{n.get('interface', '?')}[/green] → {n.get('neighbor', '?')}")
            console.print(f"  [C] Custom interface")
            
            choices = [str(i) for i in range(1, min(len(lldp_interfaces), 5) + 1)] + ["c", "C"]
            choice = Prompt.ask("Select parent interface", choices=choices, default="1").lower()
            
            if choice == "c":
                l2ac_parent = str_prompt_nav("Enter interface name", default="ge100-0/0/0")
            else:
                idx = int(choice) - 1
                l2ac_parent = lldp_interfaces[idx].get('interface', 'ge100-0/0/0')
        else:
            # Use detected parent or prompt
            l2ac_parent = Prompt.ask(
                "Enter parent interface for L2-AC",
                default=detected_parent or "ge100-0/0/0"
            )
            if detected_parent:
                console.print(f"  [dim]Auto-detected from existing L2-AC interfaces[/dim]")
    
    # Get RD and RT from device config using smart detection
    hostname = list(device_services.keys())[0]
    config = multi_ctx.configs.get(hostname, "")
    
    # 1. First try to get RD from router-id in BGP config
    rd_match = re.search(r'router-id\s+(\d+\.\d+\.\d+\.\d+)', config)
    rd_router_id = rd_match.group(1) if rd_match else None
    
    # 2. Fallback to loopback IP
    if not rd_router_id:
        lo_match = re.search(r'interface\s+lo\d+\s*\n(?:.*\n)*?\s+ipv4\s+address\s+(\d+\.\d+\.\d+\.\d+)', config)
        rd_router_id = lo_match.group(1) if lo_match else "1.1.1.1"
    
    # RT ASN Detection (Priority Order):
    # 1. Parse from EXISTING FXC services in running config
    # 2. Get from operational.json (local_as from BGP)
    # 3. Parse from BGP autonomous-system in config
    # 4. Last resort: Default
    
    rt_asn = None
    rt_source = ""
    
    # Method 1: Extract from existing FXC route-targets in config
    rt_match = re.search(r'route-target\s+(\d+):\d+', config)
    if rt_match:
        rt_asn = rt_match.group(1)
        rt_source = "existing services"
    
    # Method 2: Get from operational.json (most accurate BGP AS)
    if not rt_asn:
        try:
            op_path = f"/home/dn/SCALER/db/configs/{hostname}/operational.json"
            if os.path.exists(op_path):
                with open(op_path, 'r') as f:
                    op_data = json.load(f)
                    if op_data.get('local_as'):
                        rt_asn = str(op_data['local_as'])
                        rt_source = "BGP local-as"
        except Exception:
            pass
    
    # Method 3: Parse from BGP config
    if not rt_asn:
        bgp_as_match = re.search(r'autonomous-system\s+(\d+)', config)
        if bgp_as_match:
            rt_asn = bgp_as_match.group(1)
            rt_source = "BGP config"
    
    # Method 4: Last resort default
    if not rt_asn:
        rt_asn = "65000"
        rt_source = "default"
    
    console.print(f"  RD Base: {rd_router_id}")
    console.print(f"  RT ASN: {rt_asn} [dim]({rt_source})[/dim]")
    
    if not Confirm.ask("\nProceed with Quick Scale UP?", default=True):
        return False
    
    # Generate configuration
    console.print("\n[cyan]Generating configuration...[/cyan]")
    
    configs_by_device = {}
    
    for hostname in device_services.keys():
        config_lines = []
        
        # Get device-specific router ID if available
        device_config = multi_ctx.configs.get(hostname, "")
        device_asn_match = re.search(r'router-id\s+(\d+\.\d+\.\d+\.\d+)', device_config)
        device_rd = device_asn_match.group(1) if device_asn_match else rd_router_id
        
        # Generate interfaces
        config_lines.append("interfaces")
        
        # For VPWS, detect L2-AC parent from existing services if not provided
        vpws_parent = l2ac_parent
        if svc_type == "vpws" and not vpws_parent:
            # Get from existing VPWS services
            svc_list = device_services.get(hostname, {}).get("vpws", [])
            if svc_list and svc_list[-1].interfaces:
                last_iface = svc_list[-1].interfaces[0]
                # Extract parent from interface like "ge400-0/0/4.1" -> "ge400-0/0/4"
                if "." in last_iface:
                    vpws_parent = last_iface.rsplit(".", 1)[0]
        
        # Scan for L3 sub-interfaces (have IP addresses) that conflict with L2-AC
        l3_conflict_ids = set()
        for _parent in [vpws_parent or l2ac_parent, l2ac_parent]:
            if _parent and device_config:
                l3_conflict_ids |= _scan_l3_sub_ids(device_config, _parent)
        if l3_conflict_ids:
            console.print(f"  [yellow]⚠ {hostname}: {len(l3_conflict_ids)} existing L3 sub-interface(s) "
                          f"on parent (have IP addresses, will skip)[/yellow]")
        
        # Build list of service numbers, skipping L3 conflicts
        svc_numbers = []
        candidate = start_num
        while len(svc_numbers) < count:
            if candidate not in l3_conflict_ids:
                svc_numbers.append(candidate)
            candidate += 1
        
        for svc_num in svc_numbers:
            
            # VPWS always uses L2-AC interfaces
            if svc_type == "vpws":
                parent = vpws_parent or "ge400-0/0/4"
                
                # Detect pattern from existing interfaces (cached per device)
                if not hasattr(_execute_scale_up, '_vpws_iface_pattern_cache'):
                    _execute_scale_up._vpws_iface_pattern_cache = {}
                
                cache_key = f"{hostname}:vpws:{parent}"
                if cache_key not in _execute_scale_up._vpws_iface_pattern_cache:
                    _execute_scale_up._vpws_iface_pattern_cache[cache_key] = _detect_interface_pattern_from_config(
                        device_config, parent
                    )
                
                iface_pattern = _execute_scale_up._vpws_iface_pattern_cache[cache_key]
                
                # L2-AC interface for VPWS
                config_lines.append(f"  {parent}.{svc_num}")
                config_lines.append(f"    admin-state enabled")
                config_lines.append(f"    l2-service enabled")
                
                # Apply detected VLAN pattern (same as FXC L2-AC)
                if iface_pattern["uses_vlan_tags"]:
                    # Use vlan-tags with outer-tag/inner-tag (QinQ)
                    step_mode = iface_pattern.get("step_mode", "inner")
                    
                    if step_mode == "outer":
                        # Outer-tag steps, inner-tag fixed (e.g., outer=N, inner=1)
                        outer_tag = svc_num
                        inner_tag = iface_pattern.get("inner_tag", 1)
                        # Wrap outer-tag if exceeds 4094
                        if outer_tag > 4094:
                            outer_tag = ((svc_num - 1) % 4094) + 1
                    else:
                        # Inner-tag steps, outer-tag fixed (e.g., outer=1, inner=N)
                        outer_tag = iface_pattern.get("outer_tag", 1)
                        inner_tag = svc_num
                        # Wrap inner-tag if exceeds 4094
                        if inner_tag > 4094:
                            outer_tag = iface_pattern.get("outer_tag", 1) + ((svc_num - 1) // 4094)
                            inner_tag = ((svc_num - 1) % 4094) + 1
                    
                    config_lines.append(f"    vlan-tags outer-tag {outer_tag} inner-tag {inner_tag} outer-tpid {iface_pattern['outer_tpid']}")
                elif iface_pattern["uses_vlan_id"]:
                    # Use simple vlan-id
                    vlan_id = svc_num if svc_num <= 4094 else ((svc_num - 1) % 4094) + 1
                    config_lines.append(f"    vlan-id {vlan_id}")
                else:
                    # Default to vlan-tags (QinQ) - most common for VPWS
                    outer_tag = 1
                    inner_tag = svc_num
                    if inner_tag > 4094:
                        outer_tag = (inner_tag - 1) // 4094 + 1
                        inner_tag = ((inner_tag - 1) % 4094) + 1
                    config_lines.append(f"    vlan-tags outer-tag {outer_tag} inner-tag {inner_tag} outer-tpid 0x8100")
                
                # Apply vlan-manipulation if detected
                if iface_pattern["has_vlan_manipulation"]:
                    config_lines.append(f"    vlan-manipulation {iface_pattern['vlan_manipulation']}")
                
                config_lines.append(f"  !")
            
            elif interface_type.upper() == "PWHE":
                # PWHE parent
                config_lines.append(f"  ph{svc_num}")
                config_lines.append(f"    admin-state enabled")
                config_lines.append(f"  !")
                
                # PWHE sub-interface with outer-tag
                outer_tag = 1
                inner_tag = svc_num
                if inner_tag > 4094:
                    outer_tag = (inner_tag - 1) // 4094 + 1
                    inner_tag = ((inner_tag - 1) % 4094) + 1
                
                config_lines.append(f"  ph{svc_num}.1")
                config_lines.append(f"    admin-state enabled")
                config_lines.append(f"    vlan-tags outer-tag {outer_tag} inner-tag {inner_tag} outer-tpid 0x8100")
                config_lines.append(f"  !")
            else:
                # L2-AC interface - detect and replicate existing pattern
                parent = l2ac_parent or "ge100-0/0/0"
                
                # Detect pattern from existing interfaces (cached per device)
                if not hasattr(_execute_scale_up, '_iface_pattern_cache'):
                    _execute_scale_up._iface_pattern_cache = {}
                
                cache_key = f"{hostname}:{parent}"
                if cache_key not in _execute_scale_up._iface_pattern_cache:
                    _execute_scale_up._iface_pattern_cache[cache_key] = _detect_interface_pattern_from_config(
                        device_config, parent
                    )
                
                iface_pattern = _execute_scale_up._iface_pattern_cache[cache_key]
                
                config_lines.append(f"  {parent}.{svc_num}")
                config_lines.append(f"    admin-state enabled")
                config_lines.append(f"    l2-service enabled")
                
                # Apply detected VLAN pattern
                if iface_pattern["uses_vlan_tags"]:
                    # Use vlan-tags with outer-tag/inner-tag
                    outer_tag = iface_pattern["outer_tag"]
                    inner_tag = svc_num
                    # Wrap inner-tag if exceeds 4094
                    if inner_tag > 4094:
                        outer_tag = iface_pattern["outer_tag"] + ((inner_tag - 1) // 4094)
                        inner_tag = ((inner_tag - 1) % 4094) + 1
                    config_lines.append(f"    vlan-tags outer-tag {outer_tag} inner-tag {inner_tag} outer-tpid {iface_pattern['outer_tpid']}")
                elif iface_pattern["uses_vlan_id"]:
                    # Use simple vlan-id
                    vlan_id = svc_num if svc_num <= 4094 else ((svc_num - 1) % 4094) + 1
                    config_lines.append(f"    vlan-id {vlan_id}")
                else:
                    # Default to vlan-tags
                    inner_tag = svc_num if svc_num <= 4094 else ((svc_num - 1) % 4094) + 1
                    config_lines.append(f"    vlan-tags outer-tag 1 inner-tag {inner_tag} outer-tpid 0x8100")
                
                # Apply vlan-manipulation if detected
                if iface_pattern["has_vlan_manipulation"]:
                    config_lines.append(f"    vlan-manipulation {iface_pattern['vlan_manipulation']}")
                
                # Apply any extra lines detected
                for extra_line in iface_pattern.get("extra_lines", []):
                    config_lines.append(f"    {extra_line}")
                
                config_lines.append(f"  !")
        
        config_lines.append("!")
        
        # Generate services based on type
        config_lines.append("network-services")
        
        if svc_type == "vpws":
            # ==================== EVPN-VPWS SERVICES ====================
            config_lines.append("  evpn-vpws")
            
            for i in range(count):
                svc_num = start_num + i
                svc_name = f"VPWS-{svc_num}"
                
                # Interface: L2-AC sub-interface (VPWS typically uses ge/xe.Y)
                if l2ac_parent:
                    # Use l2ac_parent.N format
                    iface_name = f"{l2ac_parent}.{svc_num}"
                else:
                    # Detect from existing VPWS or use PWHE fallback
                    iface_name = f"ge400-0/0/4.{svc_num}"
                
                # EVPN-VPWS instance with correct DNOS hierarchy
                config_lines.append(f"    instance {svc_name}")
                config_lines.append(f"      protocols")
                config_lines.append(f"        bgp {rt_asn}")
                config_lines.append(f"          export-l2vpn-evpn route-target {rt_asn}:{svc_num}")
                config_lines.append(f"          import-l2vpn-evpn route-target {rt_asn}:{svc_num}")
                config_lines.append(f"          route-distinguisher {device_rd}:{svc_num}")
                config_lines.append(f"        !")  # Close bgp
                config_lines.append(f"      !")  # Close protocols
                config_lines.append(f"      transport-protocol")
                config_lines.append(f"        mpls")
                config_lines.append(f"          control-word enabled")
                config_lines.append(f"          fat-label disabled")
                config_lines.append(f"        !")  # Close mpls
                config_lines.append(f"      !")  # Close transport-protocol
                config_lines.append(f"      admin-state enabled")
                config_lines.append(f"      interface {iface_name}")
                config_lines.append(f"        vpws-service-id local {svc_num} remote {svc_num}")
                config_lines.append(f"      !")  # Close interface
                config_lines.append(f"    !")  # Close instance
            
            config_lines.append("  !")  # Close evpn-vpws
        else:
            # ==================== FXC SERVICES ====================
            config_lines.append("  evpn-vpws-fxc")
            
            for i in range(count):
                svc_num = start_num + i
                svc_name = f"FXC-{svc_num}"
                
                if interface_type.upper() == "PWHE":
                    iface_name = f"ph{svc_num}.1"
                else:
                    parent = l2ac_parent or "ge100-0/0/0"
                    iface_name = f"{parent}.{svc_num}"
                
                # FXC instance configuration with proper DNOS hierarchy and ! separators
                config_lines.append(f"    instance {svc_name}")
                config_lines.append(f"      protocols")
                config_lines.append(f"        bgp {rt_asn}")
                config_lines.append(f"          export-l2vpn-evpn route-target {rt_asn}:{svc_num}")
                config_lines.append(f"          import-l2vpn-evpn route-target {rt_asn}:{svc_num}")
                config_lines.append(f"          route-distinguisher {device_rd}:{svc_num}")
                config_lines.append(f"        !")  # Close bgp
                config_lines.append(f"      !")  # Close protocols
                config_lines.append(f"      transport-protocol")
                config_lines.append(f"        mpls")
                config_lines.append(f"          control-word enabled")
                config_lines.append(f"          fat-label disabled")
                config_lines.append(f"        !")  # Close mpls
                config_lines.append(f"      !")  # Close transport-protocol
                config_lines.append(f"      admin-state enabled")
                config_lines.append(f"      interface {iface_name}")  # Interface is a single statement, no ! needed
                config_lines.append(f"    !")  # Close instance
            
            config_lines.append("  !")  # Close evpn-vpws-fxc
        
        config_lines.append("!")  # Close network-services
        
        configs_by_device[hostname] = '\n'.join(config_lines)
    
    # Show preview
    total_lines = sum(len(c.split('\n')) for c in configs_by_device.values())
    console.print(f"\n[green]✓ Generated {total_lines:,} lines for {len(configs_by_device)} device(s)[/green]")
    
    if Confirm.ask("Show config preview?", default=False):
        for hostname, cfg in configs_by_device.items():
            console.print(f"\n[bold cyan]─── {hostname} ───[/bold cyan]")
            console.print(cfg[:2000] + "..." if len(cfg) > 2000 else cfg)
    
    # Show detected interface pattern info
    if interface_type.upper() == "L2-AC" and l2ac_parent:
        iface_pattern = _detect_interface_pattern_from_config(
            multi_ctx.configs.get(list(device_services.keys())[0], ""), 
            l2ac_parent
        )
        console.print(f"\n[dim]Interface pattern detected from existing config:[/dim]")
        if iface_pattern["uses_vlan_tags"]:
            console.print(f"  [dim]• vlan-tags outer-tag {iface_pattern['outer_tag']} inner-tag N outer-tpid {iface_pattern['outer_tpid']}[/dim]")
        if iface_pattern["has_vlan_manipulation"]:
            console.print(f"  [dim]• vlan-manipulation {iface_pattern['vlan_manipulation']}[/dim]")
        if iface_pattern["extra_lines"]:
            console.print(f"  [dim]• Extra: {', '.join(iface_pattern['extra_lines'][:3])}[/dim]")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CONFIGURATION SUMMARY - Show all hierarchies before pushing
    # ═══════════════════════════════════════════════════════════════════════════
    console.print("\n[bold cyan]━━━ Configuration Summary ━━━[/bold cyan]")
    
    for hostname, cfg in configs_by_device.items():
        console.print(f"\n[bold]{hostname}:[/bold]")
        
        # Parse and count items in each hierarchy
        lines = cfg.split('\n')
        
        # Count interfaces
        iface_count = 0
        iface_types = {}
        in_interfaces = False
        current_iface = None
        
        for line in lines:
            stripped = line.strip()
            if stripped == "interfaces":
                in_interfaces = True
                continue
            elif in_interfaces and stripped == "!" and current_iface is None:
                in_interfaces = False
                continue
            
            if in_interfaces and not stripped.startswith("!"):
                # Check if this is an interface name (not a sub-config)
                if not stripped.startswith(("admin-state", "l2-service", "vlan-", "description", "mtu")):
                    if stripped and not stripped.startswith("!"):
                        iface_count += 1
                        current_iface = stripped
                        # Categorize interface type
                        if stripped.startswith("ph") and "." in stripped:
                            iface_types["PWHE Sub-interfaces"] = iface_types.get("PWHE Sub-interfaces", 0) + 1
                        elif stripped.startswith("ph"):
                            iface_types["PWHE Parents"] = iface_types.get("PWHE Parents", 0) + 1
                        elif stripped.startswith(("ge", "xe", "et")) and "." in stripped:
                            iface_types["L2-AC Sub-interfaces"] = iface_types.get("L2-AC Sub-interfaces", 0) + 1
                        elif stripped.startswith("bundle") and "." in stripped:
                            iface_types["Bundle Sub-interfaces"] = iface_types.get("Bundle Sub-interfaces", 0) + 1
                        else:
                            iface_types["Other"] = iface_types.get("Other", 0) + 1
            elif stripped == "!":
                current_iface = None
        
        # Count services
        fxc_count = len(re.findall(r'instance\s+FXC-\d+', cfg))
        evpn_count = len(re.findall(r'instance\s+EVPN-\d+', cfg, re.IGNORECASE))
        vpws_count = len(re.findall(r'instance\s+VPWS-\d+', cfg, re.IGNORECASE))
        
        # Count other hierarchies
        vrf_count = len(re.findall(r'vrf\s+\S+', cfg))
        bgp_count = len(re.findall(r'neighbor\s+\d+\.\d+\.\d+\.\d+', cfg))
        mh_count = len(re.findall(r'esi\s+\S+', cfg))
        
        # Display summary table
        from rich.table import Table
        summary_table = Table(box=None, show_header=False, padding=(0, 2))
        summary_table.add_column("Hierarchy", style="cyan")
        summary_table.add_column("Count", justify="right", style="green")
        summary_table.add_column("Details", style="dim")
        
        # Interfaces section
        if iface_count > 0:
            iface_detail = ", ".join([f"{v} {k}" for k, v in iface_types.items()])
            summary_table.add_row("📦 Interfaces", f"{iface_count:,}", iface_detail)
        
        # Services section
        total_services = fxc_count + evpn_count + vpws_count
        if total_services > 0:
            svc_details = []
            if fxc_count > 0:
                svc_details.append(f"{fxc_count:,} FXC")
            if evpn_count > 0:
                svc_details.append(f"{evpn_count:,} EVPN")
            if vpws_count > 0:
                svc_details.append(f"{vpws_count:,} VPWS")
            summary_table.add_row("🔗 Network Services", f"{total_services:,}", ", ".join(svc_details))
        
        # Other sections
        if vrf_count > 0:
            summary_table.add_row("🌐 VRFs", f"{vrf_count:,}", "")
        if bgp_count > 0:
            summary_table.add_row("🔀 BGP Neighbors", f"{bgp_count:,}", "")
        if mh_count > 0:
            summary_table.add_row("🔄 Multihoming ESIs", f"{mh_count:,}", "")
        
        # Total lines
        summary_table.add_row("📄 Total Lines", f"{len(lines):,}", "")
        
        console.print(summary_table)
        
        # Show service range if FXC
        if fxc_count > 0:
            fxc_nums = [int(m.group(1)) for m in re.finditer(r'instance\s+FXC-(\d+)', cfg)]
            if fxc_nums:
                console.print(f"  [dim]FXC Range: FXC-{min(fxc_nums)} to FXC-{max(fxc_nums)}[/dim]")
        
        # Show interface range
        if iface_types.get("L2-AC Sub-interfaces", 0) > 0:
            l2ac_matches = re.findall(r'((?:ge|xe|et)\d+-[\d/]+)\.(\d+)', cfg)
            if l2ac_matches:
                parents = set(m[0] for m in l2ac_matches)
                nums = [int(m[1]) for m in l2ac_matches]
                console.print(f"  [dim]L2-AC: {', '.join(sorted(parents))} (.{min(nums)} to .{max(nums)})[/dim]")
        
        if iface_types.get("PWHE Sub-interfaces", 0) > 0:
            ph_nums = [int(m.group(1)) for m in re.finditer(r'ph(\d+)\.', cfg)]
            if ph_nums:
                console.print(f"  [dim]PWHE: ph{min(ph_nums)}.1 to ph{max(ph_nums)}.1[/dim]")
    
    console.print("")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # RETURN CONFIG MODE - Return generated config instead of pushing
    # ═══════════════════════════════════════════════════════════════════════════
    if return_config:
        # Combine all device configs and return
        combined = '\n'.join(configs_by_device.values())
        console.print(f"\n[green]✓ Generated {len(combined.split(chr(10))):,} lines[/green]")
        return combined
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PUSH OPTIONS - Streamlined: method first, then auto-save if needed
    # ═══════════════════════════════════════════════════════════════════════════
    console.print("[bold cyan]━━━ Push Options ━━━[/bold cyan]")
    
    # Push method selection FIRST
    console.print("[bold]Select action:[/bold]")
    console.print("  [1] Terminal Paste (paste directly into CLI)")
    console.print("  [2] File Merge (upload file + load merge)")
    console.print("  [3] Edit config before pushing")
    console.print("  [4] Save to file only (don't push)")
    console.print("  [B] Cancel")
    push_method = Prompt.ask("Select", choices=["1", "2", "3", "4", "b", "B"], default="1").lower()
    
    if push_method == "b":
        return None if return_config else False
    
    # Helper to save config files
    def save_configs(prefix="", quiet=False):
        saved_paths = {}
        for hostname, cfg in configs_by_device.items():
            filename = f"scale_up_{hostname}_{svc_type}_{count}.txt"
            filepath = f"/home/dn/SCALER/generated/{filename}"
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(cfg)
            saved_paths[hostname] = filepath
            if not quiet:
                console.print(f"  {prefix}[green]✓[/green] Saved: {filepath}")
        return saved_paths
    
    if push_method == "4":
        # Save only
        save_configs()
        console.print("[yellow]Configuration saved. Not pushing to device.[/yellow]")
        return True
    
    if push_method == "3":
        # Edit mode
        console.print("\n[yellow]Edit Mode:[/yellow] Edit file and save, then press Enter.")
        for hostname, cfg in configs_by_device.items():
            temp_file = f"/tmp/scale_up_{hostname}_edit.txt"
            with open(temp_file, 'w') as f:
                f.write(cfg)
            console.print(f"[cyan]File: {temp_file}[/cyan]")
            input("Press Enter when done editing...")
            
            with open(temp_file, 'r') as f:
                edited_cfg = f.read()
            
            orig_lines, new_lines = len(cfg.split('\n')), len(edited_cfg.split('\n'))
            if orig_lines != new_lines:
                console.print(f"[yellow]Lines: {orig_lines} → {new_lines}[/yellow]")
            
            configs_by_device[hostname] = edited_cfg
            console.print(f"[green]✓ Config updated[/green]")
        
        # Ask push method after edit
        console.print("\n[bold]Push edited config:[/bold]")
        console.print("  [1] Terminal Paste  [2] File Merge")
        edit_push = Prompt.ask("Select", choices=["1", "2"], default="1")
        push_method = edit_push  # Update push_method for file handling below
        
        if not Confirm.ask("Push now?", default=True):
            return False
    
    use_terminal_paste = (push_method == "1")
    
    # Save file: required for File Merge, optional for Terminal Paste
    if not use_terminal_paste:
        # Auto-save for file merge
        console.print("[dim]Auto-saving for upload...[/dim]")
        save_configs(quiet=True)
    
    # Option 3: Live terminal output
    show_live_terminal = Confirm.ask("Show live device terminal output?", default=True)
    
    # Pre-push validation: Check for potential DNOS limits
    console.print(f"\n[bold cyan]Validating configuration limits...[/bold cyan]")
    
    # Known DNOS limits (approximate - varies by platform/version)
    DNOS_LIMITS = {
        'fxc_instances': 8000,      # Max FXC instances per device
        'evpn_instances': 4000,     # Max EVPN instances
        'route_targets': 4000,      # Approximate RT limit (may vary)
        'pwhe_interfaces': 4096,    # Max PWHE interfaces
    }
    
    for hostname in configs_by_device.keys():
        # Check current service count
        current_fxc = len(device_services.get(hostname, {}).get('fxc', []))
        new_total = current_fxc + count
        
        if new_total > DNOS_LIMITS['fxc_instances']:
            console.print(f"[red]✗ {hostname}: Would exceed FXC limit ({new_total} > {DNOS_LIMITS['fxc_instances']})[/red]")
            if not Confirm.ask("Continue anyway?", default=False):
                return False
        elif new_total > DNOS_LIMITS['route_targets']:
            console.print(f"[yellow]⚠ {hostname}: May approach route-target limits ({new_total} services)[/yellow]")
            console.print(f"[dim]  Note: DNOS may have system-wide limits on route-targets (~3000-4000)[/dim]")
        else:
            console.print(f"[green]✓ {hostname}: {current_fxc} + {count} = {new_total} FXC (within limits)[/green]")
    
    # Push configuration
    console.print(f"\n[bold cyan]Pushing configurations...[/bold cyan]")
    
    operation_start_time = time.time()
    results = {}
    
    # Get accurate timing estimate using new system
    from ..config_pusher import get_accurate_push_estimates
    
    # Combine configs for estimation
    combined_config = '\n'.join(configs_by_device.values())
    estimates = get_accurate_push_estimates(
        config_text=combined_config,
        platform=multi_ctx.devices[0].platform.value if multi_ctx.devices else "SA-36CD-S"
    )
    
    est_method = 'terminal_paste' if use_terminal_paste else 'file_upload'
    estimated_seconds = estimates['estimates'][est_method]['total'] / len(configs_by_device) if configs_by_device else 60
    source = estimates['source']
    source_detail = estimates['source_detail']
    
    def format_time(seconds: float) -> str:
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"
    
    if source == 'similar_push':
        console.print(f"[green]📊 Est. ~{format_time(estimated_seconds)} per device - {source_detail}[/green]")
    elif source == 'scale_type':
        console.print(f"[yellow]📊 Est. ~{format_time(estimated_seconds)} per device - {source_detail}[/yellow]")
    else:
        console.print(f"[dim]📊 Est. ~{format_time(estimated_seconds)} per device - {source_detail}[/dim]")
    
    for hostname, cfg in configs_by_device.items():
        device = next((d for d in multi_ctx.devices if d.hostname == hostname), None)
        if not device:
            results[hostname] = (False, "Device not found")
            continue
        
        console.print(f"\n[cyan]Pushing to {hostname}...[/cyan]")
        
        try:
            pusher = ConfigPusher(timeout=120, commit_timeout=1800)
            
            if use_terminal_paste:
                success, output = pusher.push_config_terminal_paste(
                    device,
                    cfg,
                    dry_run=False,
                    show_live_terminal=show_live_terminal,
                    progress_callback=lambda msg, pct: console.print(f"  [dim]{msg}[/dim]")
                )
            else:
                success, output = pusher.push_config_merge(
                    device,
                    cfg,
                    dry_run=False,
                    progress_callback=lambda msg, pct: console.print(f"  [dim]{msg}[/dim]")
                )
            
            if success:
                results[hostname] = (True, f"Added {count} services")
                console.print(f"[green]✓ {hostname}: Success[/green]")
            else:
                # Extract full error message, especially for commit failures
                error_msg = "Unknown error"
                if output:
                    # Look for specific DNOS error patterns
                    commit_error = re.search(r'(TRANSACTION_COMMIT.*?FAILED.*?)(?:\n|$)', output, re.IGNORECASE)
                    yang_error = re.search(r'(Too many elements.*?leaflist.*?)(?:\n|$)', output, re.IGNORECASE)
                    path_error = re.search(r"(in path '[^']+)", output)
                    
                    if commit_error or yang_error:
                        error_parts = []
                        if yang_error:
                            error_parts.append(yang_error.group(1).strip())
                        if path_error:
                            error_parts.append(path_error.group(1).strip())
                        if commit_error and not yang_error:
                            error_parts.append(commit_error.group(1).strip())
                        error_msg = " | ".join(error_parts) if error_parts else output.split('\n')[-1]
                    else:
                        # Fall back to last few meaningful lines
                        lines = [l.strip() for l in output.split('\n') if l.strip() and not l.startswith('#')]
                        error_msg = lines[-1] if lines else "Unknown error"
                
                results[hostname] = (False, error_msg)
                console.print(f"[red]✗ {hostname}: {error_msg}[/red]")
                
                # For YANG/limit errors, provide guidance
                if 'Too many elements' in error_msg or 'leaflist' in error_msg:
                    console.print(f"[yellow]⚠ This appears to be a DNOS limit error. The system may have reached max route-targets or service instances.[/yellow]")
                    console.print(f"[yellow]  Current FXC count: {2300 + count} (limit may be ~3000-4000)[/yellow]")
                
        except Exception as e:
            results[hostname] = (False, str(e))
            console.print(f"[red]✗ {hostname}: {e}[/red]")
    
    # Save timing (with correct function signature)
    total_time = time.time() - operation_start_time
    try:
        for hostname in configs_by_device.keys():
            device = next((d for d in multi_ctx.devices if d.hostname == hostname), None)
            if device and results.get(hostname, (False, ""))[0]:
                platform = device.platform.value if hasattr(device.platform, 'value') else str(device.platform)
                save_timing_record(
                    platform=platform,
                    line_count=len(configs_by_device[hostname].split('\n')),
                    pwhe_count=count if interface_type.upper() == "PWHE" else 0,
                    fxc_count=count,
                    actual_time_seconds=total_time,
                    device_hostname=hostname,
                    push_method="terminal_paste" if use_terminal_paste else "file_merge",
                    push_type="scale_up"
                )
    except Exception as e:
        console.print(f"[dim]Warning: Could not save timing: {e}[/dim]")
    
    # Summary
    success_count = sum(1 for s, _ in results.values() if s)
    console.print(f"\n[bold]Result: {success_count}/{len(configs_by_device)} devices updated[/bold]")
    console.print(f"[dim]Total time: {total_time/60:.1f} minutes ({total_time:.0f}s)[/dim]")
    
    # Auto-refresh configs after successful push
    if success_count > 0:
        console.print("\n[dim]Refreshing device configurations...[/dim]")
        multi_ctx.discover_all()
        console.print("[green]✓ Config cache updated[/green]")
    
    return success_count > 0


def _apply_peer_match_suggestion(
    multi_ctx: 'MultiDeviceContext',
    device_services: Dict[str, Dict[str, List[ServiceScale]]],
    suggestion: Dict
) -> bool:
    """Apply a suggestion to match a peer device's additional services.
    
    This handles the case where devices share some services but one has more.
    E.g., PE-1 (PWHE) has 3022, PE-4 (L2-AC) has 2300 → Add 722 L2-AC to PE-4
    """
    console.print(f"\n[bold cyan]━━━ Matching Peer's Additional Services ━━━[/bold cyan]")
    console.print(f"  Source: [cyan]{suggestion.get('source_device')}[/cyan]")
    console.print(f"  Adding: [green]{suggestion['count']:,}[/green] services")
    console.print(f"  Interface: [yellow]{suggestion.get('interface_type', 'PWHE')}[/yellow]")
    console.print(f"  Starting from: FXC-{suggestion.get('start_num', 1)}")
    
    return _execute_scale_up(
        multi_ctx=multi_ctx,
        device_services=device_services,
        svc_type="fxc",
        count=suggestion["count"],
        interface_type=suggestion.get("interface_type", "PWHE"),
        start_num=suggestion.get("start_num")
    )


def _apply_match_fxc_suggestion(
    multi_ctx: 'MultiDeviceContext',
    device_services: Dict[str, Dict[str, List[ServiceScale]]],
    suggestion: Dict
) -> bool:
    """Apply a suggestion to match another device's FXC count."""
    # This will use the existing scale up logic but with pre-filled values
    return _execute_scale_up(
        multi_ctx=multi_ctx,
        device_services=device_services,
        svc_type="fxc",
        count=suggestion["count"],
        interface_type=suggestion.get("interface_type", "PWHE"),
        start_num=suggestion.get("start_num")
    )


def _apply_continue_fxc_suggestion(
    multi_ctx: 'MultiDeviceContext',
    device_services: Dict[str, Dict[str, List[ServiceScale]]],
    suggestion: Dict
) -> bool:
    """Apply a suggestion to continue adding FXC services."""
    return _execute_scale_up(
        multi_ctx=multi_ctx,
        device_services=device_services,
        svc_type="fxc",
        count=suggestion["count"],
        interface_type=suggestion.get("interface_type", "PWHE"),
        start_num=suggestion.get("start_num")
    )


def _apply_flowspec_vpn_suggestion(
    multi_ctx: 'MultiDeviceContext',
    device_services: Dict[str, Dict[str, List[ServiceScale]]],
    suggestion: Dict
) -> bool:
    """Apply a suggestion to continue adding FlowSpec VPN VRFs."""
    return _execute_flowspec_vpn_scale_up(
        multi_ctx=multi_ctx,
        device_services=device_services,
        count=suggestion["count"],
        start_num=suggestion.get("start_num", 1),
    )


def _detect_interface_pattern_from_config(
    config: str,
    parent_interface: str
) -> Dict[str, Any]:
    """
    Detect the configuration pattern used for existing sub-interfaces.
    FAST version - uses line scanning instead of regex over entire config.
    
    Detects:
    - vlan-tags vs vlan-id
    - Which tag is stepping (outer vs inner)
    - Fixed inner-tag or fixed outer-tag
    - vlan-manipulation settings
    """
    pattern = {
        "uses_vlan_tags": False,
        "uses_vlan_id": False,
        "outer_tag": 1,
        "inner_tag": 1,
        "outer_tpid": "0x8100",
        "step_mode": "outer",
        "has_vlan_manipulation": False,
        "vlan_manipulation": "",
        "has_description": False,
        "description_pattern": "",
        "extra_lines": []
    }
    
    # Fast line-by-line scan - collect samples quickly
    # We need: first 2, last 2, and optionally middle samples
    samples = []
    current_subif = None
    current_block = []
    parent_prefix = f"  {parent_interface}."
    
    # Single pass through lines - stop early once we have first 3 samples
    lines = config.split('\n')
    first_samples = []
    last_samples = []  # Ring buffer for last 2
    sample_count = 0
    
    for i, line in enumerate(lines):
        # Check for sub-interface start
        if line.startswith(parent_prefix) and not line.startswith(parent_prefix + " "):
            # Extract subif number
            rest = line[len(parent_prefix):].strip()
            if rest.isdigit() or (rest and rest.split()[0].isdigit()):
                subif_str = rest.split()[0] if rest.split() else rest
                if subif_str.isdigit():
                    current_subif = int(subif_str)
                    current_block = []
                    continue
        
        # Collect block content
        if current_subif is not None:
            if line.strip() == '!':
                # End of block - parse it
                block_text = '\n'.join(current_block)
    
                # Look for vlan-tags
                vlan_match = re.search(
                    r'vlan-tags\s+outer-tag\s+(\d+)\s+inner-tag\s+(\d+)(?:\s+outer-tpid\s+(0x\w+))?',
                    block_text
    )
                if vlan_match:
                    sample = {
                        "subif": current_subif,
                        "outer": int(vlan_match.group(1)),
                        "inner": int(vlan_match.group(2)),
                        "tpid": vlan_match.group(3) or "0x8100"
                    }
                    
                    # Collect first 3 samples
                    if len(first_samples) < 3:
                        first_samples.append(sample)
                    
                    # Always keep last 2 (ring buffer)
                    if len(last_samples) >= 2:
                        last_samples.pop(0)
                    last_samples.append(sample)
                    
                    sample_count += 1
                    
                    # Check for vlan-manipulation (only once)
                    if not pattern["has_vlan_manipulation"]:
                        manip_match = re.search(r'vlan-manipulation\s+(\S+(?:\s+\d+)?)', block_text)
                        if manip_match:
                            pattern["has_vlan_manipulation"] = True
                            pattern["vlan_manipulation"] = manip_match.group(1)
                else:
                    # Check for vlan-id
                    if 'vlan-id' in block_text:
                        pattern["uses_vlan_id"] = True
                
                current_subif = None
                current_block = []
            else:
                current_block.append(line)
    
    # Combine samples: first 2 + last 2 (deduplicated)
    samples = first_samples[:2]
    for s in last_samples:
        if s not in samples:
            samples.append(s)
    
    if samples:
        pattern["uses_vlan_tags"] = True
        pattern["outer_tpid"] = samples[0]["tpid"]
        
        if len(samples) >= 2:
            # Quick detection: check if inner is same for all (fixed)
            inner_values = set(s["inner"] for s in samples)
            inner_is_fixed = len(inner_values) == 1
            
            # Check if outer follows subif
            outer_follows_subif = all(s["outer"] == s["subif"] for s in samples)
            
            if outer_follows_subif or inner_is_fixed:
                pattern["step_mode"] = "outer"
                pattern["inner_tag"] = samples[0]["inner"]
            else:
                pattern["step_mode"] = "inner"
                pattern["outer_tag"] = samples[0]["outer"]
        else:
            # Single sample - check if outer == subif
            if samples[0]["outer"] == samples[0]["subif"]:
                pattern["step_mode"] = "outer"
                pattern["inner_tag"] = samples[0]["inner"]
            else:
                pattern["step_mode"] = "inner"
                pattern["outer_tag"] = samples[0]["outer"]
    
    return pattern
    if desc_match:
        pattern["has_description"] = True
        pattern["description_pattern"] = desc_match.group(1)
    
    # Capture any other lines (mtu, etc.)
    for line in block_content.split('\n'):
        line = line.strip()
        if line and line != '!' and not any(x in line for x in [
            'admin-state', 'l2-service', 'vlan-tags', 'vlan-id', 
            'vlan-manipulation', 'description'
        ]):
            pattern["extra_lines"].append(line)
    
    return pattern


def _detect_l2ac_parent_from_config_str(config: str) -> Optional[str]:
    """
    Detect L2-AC parent interface from config text using regex.
    E.g., if config has ge100-18/0/0.1, ge100-18/0/0.2, returns 'ge100-18/0/0'
    """
    l2ac_match = re.search(r'interface\s+((?:ge|xe|et)\d+-[\d/]+)\.\d+', config)
    if l2ac_match:
        return l2ac_match.group(1)
    l2ac_matches = re.findall(r'((?:ge|xe|et)\d+-[\d/]+)\.(\d+)', config)
    if l2ac_matches:
        return l2ac_matches[0][0]
    return None


def _detect_l2ac_parent_from_config(
    multi_ctx: 'MultiDeviceContext',
    device_services: Dict[str, Dict[str, List[ServiceScale]]]
) -> Optional[str]:
    """
    Detect L2-AC parent interface from device's existing FXC services.
    If no existing L2-AC found, suggest from LLDP neighbors.
    E.g., if device has ge100-18/0/0.1, ge100-18/0/0.2, returns 'ge100-18/0/0'
    """
    hostname = list(device_services.keys())[0] if device_services else None
    
    # First, check existing FXC services for L2-AC interfaces
    if hostname:
        services = device_services.get(hostname, {})
        fxc_list = services.get('fxc', [])
        
        for svc in fxc_list:
            if svc.interfaces:
                iface = svc.interfaces[0]
                # Check if it's an L2-AC interface (ge/xe/et, not ph)
                if iface.startswith(('ge', 'xe', 'et')) and '.' in iface:
                    # Extract parent (e.g., ge100-18/0/0.1 -> ge100-18/0/0)
                    parent = iface.rsplit('.', 1)[0]
                    return parent
    
    # If no existing L2-AC, check LLDP neighbors for connected interfaces
    if hostname:
        lldp_interfaces = get_interfaces_with_lldp(hostname, dn_only=True)
        if lldp_interfaces:
            # Return first DN-connected physical interface
            first_iface = lldp_interfaces[0].get('interface', '')
            if first_iface:
                console.print(f"[dim]💡 Suggesting {first_iface} (connected to {lldp_interfaces[0].get('neighbor', 'DN device')})[/dim]")
                return first_iface
    
    return None


def _apply_l2ac_termination_suggestion(
    multi_ctx: 'MultiDeviceContext',
    device_services: Dict[str, Dict[str, List[ServiceScale]]],
    suggestion: Dict
) -> bool:
    """Apply a suggestion to add L2-AC termination."""
    source_device = suggestion.get('source_device', 'peer')
    total_services = suggestion.get('count', 0)
    current_hostname = list(device_services.keys())[0] if device_services else "this device"
    
    console.print(f"\n[bold cyan]━━━ Create L2-AC to Terminate {source_device}'s PWHE ━━━[/bold cyan]")
    console.print(f"[dim]This will configure L2-AC sub-interfaces on [bold]{current_hostname}[/bold][/dim]")
    console.print(f"[dim]to terminate PWHE services from [bold]{source_device}[/bold] ({total_services:,} services available)[/dim]\n")
    
    # Detect existing L2-AC parent from device config
    detected_parent = _detect_l2ac_parent_from_config(multi_ctx, device_services)
    
    parent_iface = Prompt.ask(
        "Enter parent interface for L2-AC sub-interfaces",
        default=detected_parent or "ge100-0/0/0"
    )
    if detected_parent:
        console.print(f"  [dim]💡 Auto-detected from existing L2-AC interfaces[/dim]")
    
    # Ask for range
    console.print(f"\n[bold]L2-AC Range Options:[/bold]")
    console.print(f"  [1] [green]Match all[/green]: Create {total_services:,} L2-AC sub-interfaces (VLANs 1-{total_services})")
    console.print(f"  [2] [cyan]Custom count[/cyan]: Specify how many to create")
    console.print(f"  [B] Back")
    
    range_choice = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="1").lower()
    
    if range_choice == "b":
        return False
    
    if range_choice == "2":
        count = int_prompt_nav("How many L2-AC services to create?", default=min(100, total_services))
        start_num = int_prompt_nav("Starting VLAN number?", default=1)
    else:
        count = total_services
        start_num = 1
    
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Target device: [green]{current_hostname}[/green]")
    console.print(f"  Parent interface: [cyan]{parent_iface}[/cyan]")
    console.print(f"  L2-AC sub-interfaces: [magenta]{parent_iface}.{start_num}[/magenta] → [magenta]{parent_iface}.{start_num + count - 1}[/magenta]")
    console.print(f"  Count: [yellow]{count:,}[/yellow] services")
    
    if not Confirm.ask("\nProceed with L2-AC creation?", default=True):
        return False
    
    return _execute_scale_up(
        multi_ctx=multi_ctx,
        device_services=device_services,
        svc_type="fxc",
        count=count,
        interface_type="L2-AC",
        start_num=start_num,
        l2ac_parent=parent_iface
    )


def _apply_mh_sync_suggestion(
    multi_ctx: 'MultiDeviceContext',
    device_services: Dict[str, Dict[str, List[ServiceScale]]],
    suggestion: Dict
) -> bool:
    """Apply a suggestion to sync with multihoming partner."""
    console.print(f"\n[yellow]Syncing with multihoming partner {suggestion.get('source_device')}[/yellow]")
    
    return _execute_scale_up(
        multi_ctx=multi_ctx,
        device_services=device_services,
        svc_type="fxc",
        count=suggestion["count"],
        interface_type="PWHE",
        start_num=None
    )


def _scan_used_sub_ids(config: str, parent_iface: str) -> Set[int]:
    """Scan config for existing sub-interface IDs on a parent interface.
    
    Returns set of integer sub-IDs already in use (e.g., {1, 2, 5, 100}).
    """
    used = set()
    pattern = re.compile(rf'{re.escape(parent_iface)}\.(\d+)')
    for m in pattern.finditer(config):
        try:
            used.add(int(m.group(1)))
        except ValueError:
            pass
    return used


def _scan_l3_sub_ids(config: str, parent_iface: str) -> Set[int]:
    """Scan config for sub-interfaces that have IP addresses (L3 mode).
    
    Returns set of sub-IDs that already have ipv4-address or ipv6-address,
    which cannot coexist with l2-service enabled on the same interface.
    """
    l3_ids = set()
    lines = config.split('\n')
    current_subif_id = None
    parent_prefix = f"  {parent_iface}."
    
    for line in lines:
        if line.startswith(parent_prefix) and not line.strip().startswith('!'):
            rest = line[len(parent_prefix):].strip()
            try:
                current_subif_id = int(rest)
            except ValueError:
                current_subif_id = None
        elif line.strip() == '!' or (line.startswith('  ') and not line.startswith('    ') and current_subif_id is not None):
            current_subif_id = None
        elif current_subif_id is not None and ('ipv4-address' in line or 'ipv6-address' in line):
            l3_ids.add(current_subif_id)
    
    return l3_ids


def _scan_l2_sub_ids(config: str, parent_iface: str) -> Set[int]:
    """Scan config for sub-interfaces that have l2-service enabled (L2 mode).
    
    Returns set of sub-IDs that already have l2-service enabled,
    which cannot coexist with IP addresses on the same interface.
    """
    l2_ids = set()
    lines = config.split('\n')
    current_subif_id = None
    parent_prefix = f"  {parent_iface}."

    for line in lines:
        if line.startswith(parent_prefix) and not line.strip().startswith('!'):
            rest = line[len(parent_prefix):].strip()
            try:
                current_subif_id = int(rest)
            except ValueError:
                current_subif_id = None
        elif line.strip() == '!' or (line.startswith('  ') and not line.startswith('    ') and current_subif_id is not None):
            current_subif_id = None
        elif current_subif_id is not None and 'l2-service' in line:
            l2_ids.add(current_subif_id)

    return l2_ids


def _scan_outer_inner_map(config: str, parent_iface: str) -> Dict[int, List[int]]:
    """Scan config for QinQ outer/inner tag mappings on a parent interface.
    
    Returns dict mapping outer_tag -> [inner_tags...] for sub-interfaces
    that use vlan-tags. Used for QinQ inner-tag continuation suggestions.
    """
    result: Dict[int, List[int]] = {}
    lines = config.split('\n')
    current_subif_id = None
    parent_prefix = f"  {parent_iface}."

    for line in lines:
        if line.startswith(parent_prefix) and not line.strip().startswith('!'):
            rest = line[len(parent_prefix):].strip()
            try:
                current_subif_id = int(rest)
            except ValueError:
                current_subif_id = None
        elif current_subif_id is not None and 'vlan-tags' in line:
            # Parse: vlan-tags outer-tag X inner-tag Y ...
            m = re.search(r'outer-tag\s+(\d+).*?inner-tag\s+(\d+)', line)
            if m:
                outer = int(m.group(1))
                inner = int(m.group(2))
                if outer not in result:
                    result[outer] = []
                result[outer].append(inner)
        elif line.strip() == '!' or (line.startswith('  ') and not line.startswith('    ') and current_subif_id is not None):
            current_subif_id = None

    return result


def _scan_sub_id_details(config: str, parent_iface: str) -> Dict[int, dict]:
    """Scan config and return per-sub-ID metadata for a parent interface.

    Returns dict mapping sub-ID -> {has_ip, has_l2, ipv4, ipv6, vlan_id, vlan_tags}.
    """
    details: Dict[int, dict] = {}
    lines = config.split('\n')
    current_subif_id: Optional[int] = None
    parent_prefix = f"  {parent_iface}."
    current_info: dict = {}

    def _flush():
        nonlocal current_subif_id, current_info
        if current_subif_id is not None:
            details[current_subif_id] = current_info
        current_subif_id = None
        current_info = {}

    for line in lines:
        if line.startswith(parent_prefix) and not line.strip().startswith('!'):
            _flush()
            rest = line[len(parent_prefix):].strip()
            try:
                current_subif_id = int(rest)
                current_info = {"has_ip": False, "has_l2": False, "ipv4": None, "ipv6": None,
                                "vlan_id": None, "vlan_tags": None}
            except ValueError:
                current_subif_id = None
        elif current_subif_id is not None:
            stripped = line.strip()
            if stripped == '!' or (line.startswith('  ') and not line.startswith('    ')):
                _flush()
            elif 'ipv4-address' in stripped:
                current_info["has_ip"] = True
                parts = stripped.split()
                if len(parts) >= 2:
                    current_info["ipv4"] = parts[1]
            elif 'ipv6-address' in stripped:
                current_info["has_ip"] = True
                parts = stripped.split()
                if len(parts) >= 2:
                    current_info["ipv6"] = parts[1]
            elif 'l2-service' in stripped:
                current_info["has_l2"] = True
            elif stripped.startswith('vlan-id '):
                current_info["vlan_id"] = stripped.split()[-1]
            elif stripped.startswith('vlan-tags '):
                current_info["vlan_tags"] = stripped

    _flush()
    return details


def _scan_used_vrf_numbers(config: str, prefix: str = "VRF-") -> Set[int]:
    """Scan config for existing VRF instance numbers with a given prefix.
    
    Returns set of integer VRF numbers already in use.
    """
    used = set()
    pattern = re.compile(rf'instance\s+{re.escape(prefix)}(\d+)')
    for m in pattern.finditer(config):
        try:
            used.add(int(m.group(1)))
        except ValueError:
            pass
    return used


def _find_free_numbers(used: Set[int], count: int, start_from: int = 1) -> List[int]:
    """Find `count` free numbers starting from `start_from`, skipping any in `used`."""
    result = []
    n = start_from
    while len(result) < count:
        if n not in used:
            result.append(n)
        n += 1
    return result


def _scan_used_route_targets(config: str, rt_prefix: str) -> Set[int]:
    """Scan config for all route-target suffixes matching a given prefix.
    
    Finds all RTs like '{prefix}:N' across ALL services (VRF, FXC, EVPN, L2VPN, etc.)
    and returns the set of N values already in use.
    
    This prevents new FlowSpec VPN VRFs from accidentally sharing RTs with
    existing services, which would cause unintended route leaking.
    """
    used = set()
    pattern = re.compile(rf'route-target\s+{re.escape(rt_prefix)}:(\d+)')
    for m in pattern.finditer(config):
        try:
            used.add(int(m.group(1)))
        except ValueError:
            pass
    return used


def _detect_bgp_neighbors(config: str) -> List[Dict[str, str]]:
    """Detect existing BGP neighbors from config.
    
    Returns list of dicts with 'ip', 'remote_as', 'description', and
    which flowspec-vpn AFs are already enabled on them.
    """
    neighbors = []
    neighbor_pattern = re.compile(
        r'neighbor\s+(\d+\.\d+\.\d+\.\d+)\s*\n(.*?)(?=\n\s{4}neighbor\s+\d|\n\s{2}!|\Z)',
        re.DOTALL
    )
    
    bgp_section = ""
    in_global_bgp = False
    for line in config.split('\n'):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if indent == 2 and stripped.startswith('bgp '):
            in_global_bgp = True
            bgp_section = ""
        elif in_global_bgp and indent == 0 and stripped and stripped != '!':
            in_global_bgp = False
        if in_global_bgp:
            bgp_section += line + '\n'
    
    for m in neighbor_pattern.finditer(bgp_section):
        ip = m.group(1)
        block = m.group(2)
        
        desc_m = re.search(r'description\s+"?([^"\n]+)"?', block)
        ras_m = re.search(r'remote-as\s+(\d+)', block)
        
        neighbors.append({
            'ip': ip,
            'remote_as': ras_m.group(1) if ras_m else '',
            'description': desc_m.group(1).strip() if desc_m else '',
            'has_v4_fs_vpn': 'address-family ipv4-flowspec-vpn' in block,
            'has_v6_fs_vpn': 'address-family ipv6-flowspec-vpn' in block,
        })
    
    return neighbors


def _execute_flowspec_vpn_scale_up(
    multi_ctx: 'MultiDeviceContext',
    device_services: Dict[str, Dict[str, List[ServiceScale]]],
    count: int,
    start_num: int,
    return_config: bool = False
) -> Any:
    """Generate FlowSpec VPN scale configuration: VRFs with FlowSpec address-families.
    
    Generates:
    1. VRF instances with BGP flowspec AFs (ipv4-flowspec, ipv6-flowspec) and import/export RT
    2. Sub-interfaces attached to each VRF with flowspec admin-state enabled
    3. Global BGP address-family ipv4/ipv6-flowspec-vpn (if not already present)
    4. BGP neighbor flowspec-vpn AF activation with admin-state + send-community extended
    
    Smart features:
    - Scans existing sub-interfaces and VRF names to avoid collisions
    - Detects existing BGP neighbors for flowspec-vpn AF attachment
    - Supports dual-stack (ipv4-unicast + ipv6-unicast) VRF AFs
    
    Scale targets from SW-206883: ~20K routes, ~8 peers, up to 512 VRFs with flowspec.
    """
    from scaler.config_pusher import ConfigPusher, get_learned_timing_by_scale, save_timing_record
    
    end_num = start_num + count - 1
    console.print(f"\n[bold green]━━━ FlowSpec VPN Scale UP: {count:,} VRFs ━━━[/bold green]")
    
    hostname = list(device_services.keys())[0]
    config = multi_ctx.configs.get(hostname, "")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SMART DETECTION: BGP ASN, router-id, existing patterns
    # ═══════════════════════════════════════════════════════════════════════════
    rt_asn = None
    rt_source = ""
    
    existing_fs = device_services.get(hostname, {}).get('flowspec-vpn', [])
    if existing_fs and existing_fs[-1].bgp_asn:
        rt_asn = existing_fs[-1].bgp_asn
        rt_source = "existing FlowSpec VPN VRFs"
    
    if not rt_asn:
        rt_match = re.search(r'route-target\s+(\d+):\d+', config)
        if rt_match:
            rt_asn = rt_match.group(1)
            rt_source = "existing services"
    
    if not rt_asn:
        try:
            op_path = f"/home/dn/SCALER/db/configs/{hostname}/operational.json"
            if os.path.exists(op_path):
                with open(op_path, 'r') as f:
                    op_data = json.load(f)
                    if op_data.get('local_as'):
                        rt_asn = str(op_data['local_as'])
                        rt_source = "BGP local-as"
        except Exception:
            pass
    
    if not rt_asn:
        bgp_as_match = re.search(r'autonomous-system\s+(\d+)', config)
        if bgp_as_match:
            rt_asn = bgp_as_match.group(1)
            rt_source = "BGP config"
    
    if not rt_asn:
        rt_asn = "65000"
        rt_source = "default"
    
    rd_match = re.search(r'router-id\s+(\d+\.\d+\.\d+\.\d+)', config)
    rd_router_id = rd_match.group(1) if rd_match else None
    if not rd_router_id:
        lo_match = re.search(r'loopback-\d+.*?ipv4-address\s+(\d+\.\d+\.\d+\.\d+)', config, re.DOTALL)
        rd_router_id = lo_match.group(1) if lo_match else "1.1.1.1"
    
    # Detect interface parent from existing FlowSpec VPN VRFs
    detected_parent = None
    if existing_fs and existing_fs[-1].interfaces:
        last_iface = existing_fs[-1].interfaces[0]
        if '.' in last_iface:
            detected_parent = last_iface.rsplit('.', 1)[0]
    
    if not detected_parent:
        lldp_interfaces = get_interfaces_with_lldp(hostname, dn_only=True) if hostname else []
        if lldp_interfaces:
            detected_parent = lldp_interfaces[0].get('interface', 'ge400-0/0/1')
    
    existing_rt_base = None
    if existing_fs and existing_fs[-1].rt:
        existing_rt_base = existing_fs[-1].rt.split(':')[0] if ':' in existing_fs[-1].rt else rt_asn
    
    has_global_fs_vpn_v4 = 'address-family ipv4-flowspec-vpn' in config
    has_global_fs_vpn_v6 = 'address-family ipv6-flowspec-vpn' in config
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 1: Address Family Selection
    # ═══════════════════════════════════════════════════════════════════════════
    console.print(f"\n[bold]FlowSpec VPN Configuration:[/bold]")
    console.print(f"  BGP AS: {rt_asn} [dim]({rt_source})[/dim]")
    console.print(f"  RD Base: {rd_router_id}")
    console.print(f"  Existing FlowSpec VPN VRFs: {len(existing_fs):,}")
    console.print(f"  Global BGP flowspec-vpn: {'[green]already configured[/green]' if has_global_fs_vpn_v4 else '[yellow]will be added[/yellow]'}")
    
    console.print(f"\n[bold]FlowSpec Address Families (VRF level):[/bold]")
    console.print(f"  [1] IPv4 FlowSpec only")
    console.print(f"  [2] IPv6 FlowSpec only")
    console.print(f"  [3] [green]Both IPv4 + IPv6 FlowSpec[/green] (recommended)")
    console.print(f"  [B] Back")
    
    af_choice = Prompt.ask("Select", choices=["1", "2", "3", "b", "B"], default="3").lower()
    if af_choice == "b":
        return False
    
    use_ipv4_fs = af_choice in ("1", "3")
    use_ipv6_fs = af_choice in ("2", "3")
    af_desc = []
    if use_ipv4_fs:
        af_desc.append("ipv4-flowspec")
    if use_ipv6_fs:
        af_desc.append("ipv6-flowspec")
    
    # VRF unicast AF selection (ipv4-unicast always, optionally ipv6-unicast)
    console.print(f"\n[bold]VRF Unicast Address Families:[/bold]")
    console.print(f"  [1] [green]IPv4 unicast only[/green] (standard)")
    console.print(f"  [2] IPv4 + IPv6 unicast (dual-stack VPN)")
    
    unicast_choice = Prompt.ask("Select", choices=["1", "2"], default="1")
    use_ipv6_unicast = (unicast_choice == "2")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 2: Interface Parent Selection
    # ═══════════════════════════════════════════════════════════════════════════
    console.print(f"\n[bold]Interface for VRF attachment:[/bold]")
    if detected_parent:
        console.print(f"  [green]Detected: {detected_parent}[/green] (from existing FlowSpec VPN VRFs)")
    
    lldp_interfaces = get_interfaces_with_lldp(hostname, dn_only=True) if hostname else []
    if lldp_interfaces:
        console.print(f"\n  [bold cyan]Physical Interfaces with DN Neighbors:[/bold cyan]")
        for i, n in enumerate(lldp_interfaces[:5], 1):
            marker = " [green]← current[/green]" if n.get('interface') == detected_parent else ""
            console.print(f"    [{i}] {n.get('interface', '?')} → {n.get('neighbor', '?')}{marker}")
        console.print(f"    [C] Custom interface")
        console.print(f"    [B] Back")
        
        choices = [str(i) for i in range(1, min(len(lldp_interfaces), 5) + 1)] + ["c", "C", "b", "B"]
        if detected_parent:
            choices.extend(["d", "D"])
            console.print(f"    [D] Use detected ({detected_parent})")
        
        iface_choice = Prompt.ask("Select parent interface", choices=choices,
                                   default="d" if detected_parent else "1").lower()
        if iface_choice == "b":
            return False
        elif iface_choice == "c":
            iface_parent = str_prompt_nav("Enter interface name", default="ge400-0/0/1")
        elif iface_choice == "d" and detected_parent:
            iface_parent = detected_parent
        else:
            idx = int(iface_choice) - 1
            iface_parent = lldp_interfaces[idx].get('interface', 'ge400-0/0/1')
    else:
        iface_parent = Prompt.ask("Enter parent interface for VRF sub-interfaces",
                                   default=detected_parent or "ge400-0/0/1")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 3: Collision Avoidance - VRF names, sub-interfaces, AND route-targets
    # ═══════════════════════════════════════════════════════════════════════════
    rt_base = existing_rt_base or rt_asn
    
    used_sub_ids = _scan_used_sub_ids(config, iface_parent)
    used_vrf_nums = _scan_used_vrf_numbers(config, "VRF-")
    used_rt_suffixes = _scan_used_route_targets(config, rt_base)
    
    # Union of ALL occupied numbers: sub-IDs + VRF names + RT suffixes
    all_used = used_sub_ids | used_vrf_nums | used_rt_suffixes
    
    console.print(f"\n[bold yellow]Collision Check:[/bold yellow]")
    if used_sub_ids:
        console.print(f"  Sub-interfaces on {iface_parent}: {len(used_sub_ids):,} "
                      f"(IDs: {min(used_sub_ids)}-{max(used_sub_ids)})")
    else:
        console.print(f"  Sub-interfaces on {iface_parent}: none")
    
    if used_vrf_nums:
        console.print(f"  VRF-N instances: {len(used_vrf_nums):,} "
                      f"(range: {min(used_vrf_nums)}-{max(used_vrf_nums)})")
    else:
        console.print(f"  VRF-N instances: none")
    
    if used_rt_suffixes:
        # Show RT usage across ALL service types
        rt_only = used_rt_suffixes - used_vrf_nums
        console.print(f"  Route-targets {rt_base}:N in use: {len(used_rt_suffixes):,} "
                      f"(range: {min(used_rt_suffixes)}-{max(used_rt_suffixes)})")
        if rt_only:
            console.print(f"    [dim]({len(rt_only)} from non-FlowSpec services: "
                          f"FXC, EVPN, L2VPN, other VRFs)[/dim]")
    else:
        console.print(f"  Route-targets {rt_base}:N in use: none")
    
    if all_used:
        max_existing = max(all_used)
        requested_range = set(range(start_num, start_num + count))
        conflicts_in_range = all_used & requested_range
        
        # Categorize conflicts for clear reporting
        if conflicts_in_range:
            iface_conflicts = conflicts_in_range & used_sub_ids
            vrf_conflicts = conflicts_in_range & used_vrf_nums
            rt_conflicts = conflicts_in_range & used_rt_suffixes
            
            console.print(f"\n  [red]⚠ {len(conflicts_in_range)} conflicts in range "
                          f"#{start_num}-{start_num + count - 1}:[/red]")
            if iface_conflicts:
                console.print(f"    Sub-interface collisions: {len(iface_conflicts)}")
            if vrf_conflicts:
                console.print(f"    VRF name collisions: {len(vrf_conflicts)}")
            if rt_conflicts:
                rt_only_conflicts = rt_conflicts - iface_conflicts - vrf_conflicts
                if rt_only_conflicts:
                    console.print(f"    [yellow]RT collisions (other services): "
                                  f"{len(rt_only_conflicts)} "
                                  f"(would leak routes!)[/yellow]")
            
            free_nums = _find_free_numbers(all_used, count, start_from=start_num)
            contiguous_start = max_existing + 1
            
            console.print(f"\n  [1] [green]Skip conflicts[/green] - use {count} non-contiguous free IDs")
            console.print(f"  [2] [green]Start after existing[/green] - begin at #{contiguous_start} "
                          f"(safe: no name/RT/iface overlap)")
            console.print(f"  [3] Force original range (may overwrite or leak routes)")
            console.print(f"  [B] Back")
            
            collision_choice = Prompt.ask("Select", choices=["1", "2", "3", "b", "B"], default="2").lower()
            if collision_choice == "b":
                return False
            elif collision_choice == "1":
                vrf_numbers = free_nums
                console.print(f"  [green]✓ Using {count} free IDs "
                              f"(#{free_nums[0]} to #{free_nums[-1]})[/green]")
            elif collision_choice == "2":
                start_num = contiguous_start
                vrf_numbers = list(range(start_num, start_num + count))
                console.print(f"  [green]✓ Starting from #{start_num}[/green]")
            else:
                vrf_numbers = list(range(start_num, start_num + count))
                console.print(f"  [yellow]⚠ Using original range, may overwrite[/yellow]")
        else:
            vrf_numbers = list(range(start_num, start_num + count))
            console.print(f"\n  [green]✓ No conflicts in range #{start_num}-{start_num + count - 1}[/green]")
    else:
        vrf_numbers = list(range(start_num, start_num + count))
    
    end_num = vrf_numbers[-1] if vrf_numbers else start_num + count - 1
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 4: BGP Neighbor FlowSpec-VPN AF Activation
    # ═══════════════════════════════════════════════════════════════════════════
    existing_neighbors = _detect_bgp_neighbors(config)
    neighbors_to_activate = []
    
    if existing_neighbors:
        # Find neighbors that don't yet have flowspec-vpn AFs
        candidates = []
        for nbr in existing_neighbors:
            needs_v4 = use_ipv4_fs and not nbr['has_v4_fs_vpn']
            needs_v6 = use_ipv6_fs and not nbr['has_v6_fs_vpn']
            if needs_v4 or needs_v6:
                candidates.append(nbr)
        
        already_active = [n for n in existing_neighbors if n['has_v4_fs_vpn'] or n['has_v6_fs_vpn']]
        
        if already_active:
            console.print(f"\n[bold]BGP Neighbors with FlowSpec-VPN already active:[/bold]")
            for n in already_active:
                afs = []
                if n['has_v4_fs_vpn']:
                    afs.append("v4")
                if n['has_v6_fs_vpn']:
                    afs.append("v6")
                desc = f" ({n['description']})" if n['description'] else ""
                console.print(f"  [green]✓[/green] {n['ip']}{desc} [{', '.join(afs)}]")
        
        if candidates:
            console.print(f"\n[bold]BGP Neighbors needing FlowSpec-VPN activation:[/bold]")
            for i, n in enumerate(candidates[:8], 1):
                desc = f" ({n['description']})" if n['description'] else ""
                console.print(f"  [{i}] {n['ip']}{desc} AS{n['remote_as']}")
            console.print(f"  [A] Activate ALL {len(candidates)} neighbors")
            console.print(f"  [N] Skip - don't activate any neighbors")
            
            nbr_choices = [str(i) for i in range(1, min(len(candidates), 8) + 1)]
            nbr_choices.extend(["a", "A", "n", "N"])
            nbr_choice = Prompt.ask("Select neighbors to activate", choices=nbr_choices, default="a").lower()
            
            if nbr_choice == "a":
                neighbors_to_activate = candidates
            elif nbr_choice != "n":
                idx = int(nbr_choice) - 1
                neighbors_to_activate = [candidates[idx]]
        else:
            console.print(f"\n[dim]All BGP neighbors already have flowspec-vpn AFs active[/dim]")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 5: Options
    # ═══════════════════════════════════════════════════════════════════════════
    enable_iface_flowspec = Confirm.ask(
        "\nEnable flowspec on VRF-attached interfaces?", default=True
    )
    
    console.print(f"\n[bold cyan]━━━ Summary ━━━[/bold cyan]")
    console.print(f"  VRFs: VRF-{vrf_numbers[0]} to VRF-{vrf_numbers[-1]} ({count:,})")
    console.print(f"  VRF AFs: ipv4-unicast{', ipv6-unicast' if use_ipv6_unicast else ''}, "
                  f"{', '.join(af_desc)}")
    console.print(f"  Interface: {iface_parent}.N")
    console.print(f"  Interface flowspec: {'enabled' if enable_iface_flowspec else 'disabled'}")
    console.print(f"  RT: {rt_base}:N | RD: {rd_router_id}:N")
    if neighbors_to_activate:
        nbr_ips = ', '.join(n['ip'] for n in neighbors_to_activate[:3])
        if len(neighbors_to_activate) > 3:
            nbr_ips += f" +{len(neighbors_to_activate)-3} more"
        console.print(f"  BGP neighbor activation: {nbr_ips}")
        console.print(f"    Knobs: admin-state enabled, send-community extended")
    
    if not Confirm.ask("\nProceed with FlowSpec VPN Scale UP?", default=True):
        return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CONFIG GENERATION
    # ═══════════════════════════════════════════════════════════════════════════
    console.print("\n[cyan]Generating configuration...[/cyan]")
    
    configs_by_device = {}
    
    for dev_hostname in device_services.keys():
        config_lines = []
        device_config = multi_ctx.configs.get(dev_hostname, "")
        
        device_rd_match = re.search(r'router-id\s+(\d+\.\d+\.\d+\.\d+)', device_config)
        device_rd = device_rd_match.group(1) if device_rd_match else rd_router_id
        
        # Re-scan collision for this specific device
        dev_used_sub = _scan_used_sub_ids(device_config, iface_parent)
        dev_used_vrf = _scan_used_vrf_numbers(device_config, "VRF-")
        dev_all_used = dev_used_sub | dev_used_vrf
        
        if dev_hostname != hostname and dev_all_used:
            dev_vrf_numbers = _find_free_numbers(dev_all_used, count, start_from=vrf_numbers[0])
        else:
            dev_vrf_numbers = vrf_numbers
        
        # --- Interfaces: sub-interfaces with flowspec enabled ---
        config_lines.append("interfaces")
        for svc_num in dev_vrf_numbers:
            config_lines.append(f"  {iface_parent}.{svc_num}")
            config_lines.append(f"    admin-state enabled")
            
            vlan_id = svc_num if svc_num <= 4094 else ((svc_num - 1) % 4094) + 1
            config_lines.append(f"    vlan-id {vlan_id}")
            
            if enable_iface_flowspec:
                config_lines.append(f"    flowspec admin-state enabled")
            config_lines.append(f"  !")
        config_lines.append("!")
        
        # --- VRF instances with FlowSpec BGP AFs ---
        config_lines.append("network-services")
        config_lines.append("  vrf")
        for svc_num in dev_vrf_numbers:
            vrf_name = f"VRF-{svc_num}"
            
            config_lines.append(f"    instance {vrf_name}")
            config_lines.append(f"      interface {iface_parent}.{svc_num}")
            config_lines.append(f"      protocols")
            config_lines.append(f"        bgp {rt_asn}")
            config_lines.append(f"          route-distinguisher {device_rd}:{svc_num}")
            
            # ipv4-unicast (always)
            config_lines.append(f"          address-family ipv4-unicast")
            config_lines.append(f"            export-vpn route-target {rt_base}:{svc_num}")
            config_lines.append(f"            import-vpn route-target {rt_base}:{svc_num}")
            config_lines.append(f"          !")
            
            # ipv6-unicast (optional dual-stack)
            if use_ipv6_unicast:
                config_lines.append(f"          address-family ipv6-unicast")
                config_lines.append(f"            export-vpn route-target {rt_base}:{svc_num}")
                config_lines.append(f"            import-vpn route-target {rt_base}:{svc_num}")
                config_lines.append(f"          !")
            
            # ipv4-flowspec
            if use_ipv4_fs:
                config_lines.append(f"          address-family ipv4-flowspec")
                config_lines.append(f"            export-vpn route-target {rt_base}:{svc_num}")
                config_lines.append(f"            import-vpn route-target {rt_base}:{svc_num}")
                config_lines.append(f"          !")
            
            # ipv6-flowspec
            if use_ipv6_fs:
                config_lines.append(f"          address-family ipv6-flowspec")
                config_lines.append(f"            export-vpn route-target {rt_base}:{svc_num}")
                config_lines.append(f"            import-vpn route-target {rt_base}:{svc_num}")
                config_lines.append(f"          !")
            
            config_lines.append(f"        !")  # bgp
            config_lines.append(f"      !")  # protocols
            config_lines.append(f"    !")  # instance
        
        config_lines.append("  !")  # vrf
        config_lines.append("!")  # network-services
        
        # --- Global BGP: AFs + neighbor flowspec-vpn activation ---
        dev_has_v4 = 'address-family ipv4-flowspec-vpn' in device_config
        dev_has_v6 = 'address-family ipv6-flowspec-vpn' in device_config
        
        need_global_bgp = False
        global_af_added = []
        
        if (use_ipv4_fs and not dev_has_v4) or (use_ipv6_fs and not dev_has_v6) or neighbors_to_activate:
            need_global_bgp = True
            config_lines.append("protocols")
            config_lines.append(f"  bgp {rt_asn}")
            
            if use_ipv4_fs and not dev_has_v4:
                config_lines.append(f"    address-family ipv4-flowspec-vpn")
                config_lines.append(f"    !")
                global_af_added.append("ipv4-flowspec-vpn")
            if use_ipv6_fs and not dev_has_v6:
                config_lines.append(f"    address-family ipv6-flowspec-vpn")
                config_lines.append(f"    !")
                global_af_added.append("ipv6-flowspec-vpn")
            
            # Neighbor flowspec-vpn AF activation with proper knobs
            for nbr in neighbors_to_activate:
                config_lines.append(f"    neighbor {nbr['ip']}")
                
                needs_v4 = use_ipv4_fs and not nbr['has_v4_fs_vpn']
                needs_v6 = use_ipv6_fs and not nbr['has_v6_fs_vpn']
                
                if needs_v4:
                    config_lines.append(f"      address-family ipv4-flowspec-vpn")
                    config_lines.append(f"        admin-state enabled")
                    config_lines.append(f"        send-community extended")
                    config_lines.append(f"      !")
                if needs_v6:
                    config_lines.append(f"      address-family ipv6-flowspec-vpn")
                    config_lines.append(f"        admin-state enabled")
                    config_lines.append(f"        send-community extended")
                    config_lines.append(f"      !")
                
                config_lines.append(f"    !")  # neighbor
            
            config_lines.append(f"  !")  # bgp
            config_lines.append("!")  # protocols
        
        configs_by_device[dev_hostname] = '\n'.join(config_lines)
    
    # --- Preview and summary ---
    total_lines = sum(len(c.split('\n')) for c in configs_by_device.values())
    console.print(f"\n[green]✓ Generated {total_lines:,} lines for {len(configs_by_device)} device(s)[/green]")
    
    if Confirm.ask("Show config preview?", default=False):
        for dev_hostname, cfg in configs_by_device.items():
            console.print(f"\n[bold cyan]─── {dev_hostname} ───[/bold cyan]")
            preview = cfg[:3000] + "\n..." if len(cfg) > 3000 else cfg
            console.print(preview)
    
    console.print("\n[bold cyan]━━━ Configuration Summary ━━━[/bold cyan]")
    for dev_hostname, cfg in configs_by_device.items():
        console.print(f"\n[bold]{dev_hostname}:[/bold]")
        
        from rich.table import Table
        summary_table = Table(box=None, show_header=False, padding=(0, 2))
        summary_table.add_column("Hierarchy", style="cyan")
        summary_table.add_column("Count", justify="right", style="green")
        summary_table.add_column("Details", style="dim")
        
        summary_table.add_row("📦 Interfaces", f"{count:,}",
                              f"{iface_parent}.{vrf_numbers[0]} to .{vrf_numbers[-1]}")
        summary_table.add_row("🌐 VRFs", f"{count:,}",
                              f"VRF-{vrf_numbers[0]} to VRF-{vrf_numbers[-1]}")
        
        unicast_afs = "ipv4-unicast"
        if use_ipv6_unicast:
            unicast_afs += ", ipv6-unicast"
        fs_detail = ", ".join(af_desc)
        summary_table.add_row("🔒 VRF AFs", f"{count * (len(af_desc) + 1 + (1 if use_ipv6_unicast else 0)):,}",
                              f"{unicast_afs}, {fs_detail}")
        
        if global_af_added:
            summary_table.add_row("🔀 Global BGP AFs", f"{len(global_af_added)}",
                                  ", ".join(global_af_added))
        
        if neighbors_to_activate:
            summary_table.add_row("👥 Neighbor Activation", f"{len(neighbors_to_activate)}",
                                  "admin-state + send-community extended")
        
        summary_table.add_row("📄 Total Lines", f"{len(cfg.split(chr(10))):,}", "")
        console.print(summary_table)
    
    if return_config:
        combined = '\n'.join(configs_by_device.values())
        console.print(f"\n[green]✓ Generated {len(combined.split(chr(10))):,} lines[/green]")
        return combined
    
    # --- Push ---
    console.print("\n[bold cyan]━━━ Push Options ━━━[/bold cyan]")
    console.print("[bold]Select action:[/bold]")
    console.print("  [1] Terminal Paste (paste directly into CLI)")
    console.print("  [2] File Merge (upload file + load merge)")
    console.print("  [S] Save to file only")
    console.print("  [B] Cancel")
    
    push_choice = Prompt.ask("Select", choices=["1", "2", "s", "S", "b", "B"], default="1").lower()
    
    if push_choice == "b":
        return False
    
    if push_choice == "s":
        save_path = f"/home/dn/SCALER/db/generated/flowspec_vpn_scale_{count}vrfs.txt"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'w') as f:
            for dev_hostname, cfg in configs_by_device.items():
                f.write(f"# === {dev_hostname} ===\n")
                f.write(cfg)
                f.write("\n\n")
        console.print(f"\n[green]✓ Saved to {save_path}[/green]")
        return True
    
    push_method = "paste" if push_choice == "1" else "file_merge"
    
    timing_data = get_learned_timing_by_scale(count, "flowspec-vpn")
    if timing_data:
        console.print(f"\n[dim]Estimated time: {timing_data.get('avg_seconds', 0):.0f}s "
                      f"(from {timing_data.get('samples', 0)} previous pushes)[/dim]")
    
    start_time = time.time()
    
    pusher = ConfigPusher(multi_ctx)
    
    success = True
    for dev_hostname, cfg in configs_by_device.items():
        console.print(f"\n[bold cyan]Pushing to {dev_hostname}...[/bold cyan]")
        result = pusher.push_config(dev_hostname, cfg, method=push_method)
        if not result:
            console.print(f"[red]✗ Failed to push to {dev_hostname}[/red]")
            success = False
    
    elapsed = time.time() - start_time
    
    if success:
        console.print(f"\n[bold green]✓ FlowSpec VPN scale UP complete! ({elapsed:.1f}s)[/bold green]")
        save_timing_record(count, "flowspec-vpn", elapsed, push_method)
    
    return success


def _scale_up_wizard(multi_ctx: 'MultiDeviceContext', device_services: Dict[str, Dict[str, List[ServiceScale]]], return_config: bool = False) -> Any:
    """Wizard for scaling up (adding) services - generates and pushes config directly.
    
    If return_config=True, returns generated config string instead of pushing."""
    
    console.print("\n[bold green]━━━ Scale UP: Add More Services ━━━[/bold green]")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # QUICK SUGGESTIONS - Self-aware context from all devices and current config
    # ═══════════════════════════════════════════════════════════════════════════
    
    suggestions = _generate_scale_up_suggestions(multi_ctx, device_services)
    quick_apply_config = None
    
    if suggestions:
        console.print("\n[bold cyan]╭─────────────────────────────────────────────────────────────────╮[/bold cyan]")
        console.print("[bold cyan]│  💡 Quick Suggestions (based on current configurations)         │[/bold cyan]")
        console.print("[bold cyan]╰─────────────────────────────────────────────────────────────────╯[/bold cyan]")
        
        for i, sug in enumerate(suggestions[:3], 1):  # Show max 3 suggestions
            console.print(f"  [{i}] {sug['description']}")
            if sug.get('details'):
                console.print(f"      [dim]{sug['details']}[/dim]")
        
        console.print("")
        console.print("  [O] [bold yellow]⚙ Advanced Options[/bold yellow] [dim](L2-AC termination, custom ranges, interface type selection)[/dim]")
        console.print("  [B] Back")
        
        choices = [str(i) for i in range(1, min(len(suggestions), 3) + 1)] + ["o", "O", "b", "B"]
        quick_choice = Prompt.ask("\nSelect", choices=choices, default="1").lower()
        
        if quick_choice == "b":
            return False
        
        if quick_choice != "o" and quick_choice.isdigit():
            idx = int(quick_choice) - 1
            if idx < len(suggestions):
                selected_sug = suggestions[idx]
                console.print(f"\n[green]✓ Selected: {selected_sug['description']}[/green]")
                
                # Apply the suggestion
                if selected_sug.get('apply_func'):
                    return selected_sug['apply_func'](multi_ctx, device_services, selected_sug)
        
        console.print("\n[dim]Showing all options...[/dim]")
    
    # Select service type
    console.print("\n[bold]Select Service Type to Scale Up:[/bold]")
    console.print("  [1] FXC (Flexible Cross-Connect)")
    console.print("  [2] L2VPN instances + sub-interfaces")
    console.print("  [3] EVPN instances + sub-interfaces")
    console.print("  [4] VPWS instances + sub-interfaces")
    console.print("  [5] VRF (L3VPN) instances + interfaces")
    console.print("  [6] FlowSpec VPN (VRFs with FlowSpec address-families)")
    console.print("  [B] Back")
    
    console.print("\n[dim]Note: FXC services can use PWHE (phX.Y) or L2-AC (ge/bundle.Y) interfaces[/dim]")
    
    type_choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "5", "6", "b", "B"], default="b").lower()
    
    if type_choice == "b":
        return False
    
    svc_type_map = {"1": "fxc", "2": "l2vpn", "3": "evpn", "4": "vpws", "5": "vrf", "6": "flowspec-vpn"}
    svc_type = svc_type_map.get(type_choice, "fxc")
    svc_type_name = {"fxc": "FXC", "l2vpn": "L2VPN", "evpn": "EVPN", "vpws": "VPWS", "vrf": "VRF", "flowspec-vpn": "FlowSpec VPN"}[svc_type]
    
    # Show current scale and last service
    console.print(f"\n[bold]Current {svc_type_name} Services:[/bold]")
    
    last_service: Optional[ServiceScale] = None
    last_hostname: Optional[str] = None
    
    for hostname, services in device_services.items():
        svc_list = services.get(svc_type, [])
        if svc_list:
            console.print(f"\n[cyan]{hostname}:[/cyan]")
            console.print(f"  Total: {len(svc_list):,} services")
            last = svc_list[-1]
            console.print(f"  Last service: [green]{last.service_name}[/green] (#{last.service_number})")
            
            # Display interfaces with detected type
            if last.interfaces:
                iface_str = ', '.join(last.interfaces[:3])
                if len(last.interfaces) > 3:
                    iface_str += '...'
                # Detect interface type from actual interface
                if last.interfaces[0].startswith('ph'):
                    iface_type = "[magenta]PWHE[/magenta]"
                elif last.interfaces[0].startswith(('ge', 'xe', 'et')):
                    iface_type = "[yellow]L2-AC[/yellow]"
                elif last.interfaces[0].startswith(('bundle', 'lag')):
                    iface_type = "[blue]Bundle L2-AC[/blue]"
                else:
                    iface_type = ""
                console.print(f"  Last interface: {iface_str} {iface_type}")
            else:
                console.print(f"  Last interface: [dim]none detected[/dim]")
            
            # FlowSpec VPN specific info
            if svc_type == 'flowspec-vpn':
                if hasattr(last, 'flowspec_afs') and last.flowspec_afs:
                    console.print(f"  FlowSpec AFs: {', '.join(last.flowspec_afs)}")
                if hasattr(last, 'rd') and last.rd:
                    console.print(f"  RD pattern: {last.rd}")
                if hasattr(last, 'rt') and last.rt:
                    console.print(f"  RT pattern: {last.rt}")
            
            # EVPN-VPWS specific info (show all in one place to avoid redundant prompts)
            if svc_type == 'vpws':
                if hasattr(last, 'rd') and last.rd:
                    console.print(f"  RD pattern: {last.rd}")
                if hasattr(last, 'rt') and last.rt:
                    console.print(f"  RT pattern: {last.rt}")
                if hasattr(last, 'vpws_local_id') and last.vpws_local_id:
                    console.print(f"  vpws-service-id: local {last.vpws_local_id} remote {last.vpws_remote_id}")
                
                # Show VLAN pattern here to avoid later redundant display
                if last.interfaces and '.' in last.interfaces[0]:
                    parent = last.interfaces[0].rsplit('.', 1)[0]
                    config = multi_ctx.configs.get(hostname, "")
                    vlan_pattern = _detect_interface_pattern_from_config(config, parent)
                    if vlan_pattern["uses_vlan_tags"]:
                        step_mode = vlan_pattern.get("step_mode", "inner")
                        if step_mode == "outer":
                            console.print(f"  VLAN: outer-tag=N (steps), inner-tag={vlan_pattern.get('inner_tag', 1)} (fixed)")
                        else:
                            console.print(f"  VLAN: outer-tag={vlan_pattern.get('outer_tag', 1)} (fixed), inner-tag=N (steps)")
                    elif vlan_pattern["uses_vlan_id"]:
                        console.print(f"  VLAN: Single tag (vlan-id N)")
            
            if last_service is None or last.service_number > last_service.service_number:
                last_service = last
                last_hostname = hostname
    
    if not last_service:
        console.print(f"[yellow]No existing {svc_type_name} services found.[/yellow]")
        last_num = 0
    else:
        last_num = last_service.service_number
    
    # Allow user to specify starting number
    console.print(f"\n[bold]Starting Number Options:[/bold]")
    if last_num > 0:
        console.print(f"  [1] [green]Continue from #{last_num + 1}[/green] (after last: {last_service.service_name})")
    else:
        console.print(f"  [1] [green]Start from #1[/green]")
    console.print(f"  [2] [cyan]Custom starting number[/cyan]")
    
    # Simplified: L2-AC termination is now available as a Quick Suggestion at the top of Scale UP
    # No need to duplicate it here in Starting Number Options
    current_device_hostname = last_hostname if last_hostname else list(device_services.keys())[0] if device_services else None
    
    console.print(f"  [B] Back")
    console.print(f"\n[dim]💡 Tip: For L2-AC termination, go back and select from Quick Suggestions[/dim]")
    
    valid_choices = ["1", "2", "b", "B"]
    
    start_choice = Prompt.ask("Select", choices=valid_choices, default="1").lower()
    
    if start_choice == "b":
        return False
    
    if start_choice == "2":
        # Custom starting number
        custom_start = int_prompt_nav("Enter starting service number", default=last_num + 1)
        if custom_start <= 0:
            console.print("[red]Invalid starting number[/red]")
            return False
        
        # Check if this would overlap with existing services
        if custom_start <= last_num:
            console.print(f"[yellow]⚠ Warning: Services up to #{last_num} already exist![/yellow]")
            if not Confirm.ask("Overlap may cause conflicts. Continue anyway?", default=False):
                return False
        
        start_num_base = custom_start
        console.print(f"\n[bold]Will start from: [green]#{start_num_base}[/green][/bold]")
    else:
        # Continue from last
        start_num_base = last_num + 1
        if last_num > 0:
            console.print(f"\n[bold]Will continue from: [green]{last_service.service_name}[/green][/bold]")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STAG LIMIT PRE-VALIDATION (matches PR-86760 validation)
    # Each unique (parent_interface, outer_vlan_id) = 1 Stag
    # Stag pool: ifindex 88001-92000 = 4000 slots maximum
    # SAFETY_MARGIN: DNOS may reject at exactly 4000, so leave some headroom
    # ═══════════════════════════════════════════════════════════════════════════
    STAG_LIMIT = 4000
    STAG_SAFETY_MARGIN = 5  # Leave 5 slots free to avoid edge-case rejections
    
    # FAST STAG counting: simple string-based scan instead of regex
    # Count unique (parent, outer_tag) combinations
    device_stag_counts = {}
    for hostname, config in multi_ctx.configs.items():
        unique_stags = set()
        current_parent = None
        
        for line in config.split('\n'):
            stripped = line.strip()
            
            # Fast check: sub-interface line (has a dot and starts with known prefix)
            if '.' in stripped and not stripped.startswith('!'):
                # Extract parent: "ge400-0/0/4.123" -> "ge400-0/0/4"
                # Only process lines that look like interface declarations
                if stripped.startswith(('ge', 'xe', 'et', 'ph', 'bundle', 'lag')):
                    parts = stripped.split()
                    if parts:
                        iface = parts[0]
                        if '.' in iface:
                            current_parent = iface.rsplit('.', 1)[0]
            
            # Fast check: vlan-tags outer-tag line
            elif 'outer-tag' in stripped and current_parent:
                # Extract outer-tag value: "vlan-tags outer-tag 123 inner-tag 1"
                parts = stripped.split()
                try:
                    idx = parts.index('outer-tag')
                    if idx + 1 < len(parts):
                        outer_tag = int(parts[idx + 1])
                    unique_stags.add((current_parent, outer_tag))
                except (ValueError, IndexError):
                    pass
        
        device_stag_counts[hostname] = len(unique_stags)
    
    # Use maximum Stag count across devices for validation
    current_stags = max(device_stag_counts.values()) if device_stag_counts else 0
    
    # Apply safety margin - DNOS may reject at exactly 4000
    effective_limit = STAG_LIMIT - STAG_SAFETY_MARGIN
    remaining_stags = effective_limit - current_stags
    if remaining_stags < 0:
        remaining_stags = 0
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK FOR CACHED POOL STATUS FROM EARLIER STAG POOL CHECK
    # If user ran "Stag Pool Check" earlier, use the accurate kernel-based data
    # ═══════════════════════════════════════════════════════════════════════════
    suggested_max = None
    suggested_bottleneck = None
    has_cached_pool_data = hasattr(multi_ctx, 'cached_pool_status') and multi_ctx.cached_pool_status
    
    if has_cached_pool_data:
        # Use cached results from live kernel query - more accurate than config parsing
        console.print(f"\n[bold cyan]━━━ Pool Status (from Kernel Check) ━━━[/bold cyan]")
        
        min_max_services = None
        worst_bottleneck = None
        
        for hostname, pool_data in multi_ctx.cached_pool_status.items():
            max_svc = pool_data.get('max_additional_pwhe_services', 0)
            bottleneck = pool_data.get('bottleneck', 'Unknown')
            ph_used = pool_data.get('ph_pool_used', 0)
            ph_max = pool_data.get('ph_pool_max', 0)
            stag_used = pool_data.get('stag_pool_used', 0)
            stag_max = pool_data.get('stag_pool_max', 0)
            
            console.print(f"  [cyan]{hostname}:[/cyan]")
            console.print(f"    PH Pool:   {ph_used:,} / {ph_max:,}")
            console.print(f"    Stag Pool: {stag_used:,} / {stag_max:,}")
            console.print(f"    [green]Can add: {max_svc:,} PWHE+FXC services[/green]")
            console.print(f"    [dim]Bottleneck: {bottleneck.split('(')[0].strip()}[/dim]")
            
            if min_max_services is None or max_svc < min_max_services:
                min_max_services = max_svc
                worst_bottleneck = bottleneck
        
        if min_max_services is not None:
            suggested_max = min_max_services
            suggested_bottleneck = worst_bottleneck
            console.print(f"\n  [bold]➤ Maximum to add: [cyan]{suggested_max:,}[/cyan] services[/bold]")
        
        # Warn about Stag exhaustion but allow override
        if suggested_max is not None and suggested_max <= 0:
            console.print(f"\n[bold red]⚠ POOL AT LIMIT![/bold red]")
            console.print(f"[red]Warning: {worst_bottleneck}[/red]")
            console.print(f"[dim]Expected error: 'Hook failed - assign_new_if_index'[/dim]")
            if not Confirm.ask("[yellow]Proceed anyway (will likely fail)?[/yellow]", default=False):
                return False
            suggested_max = 10  # Allow manual entry
    else:
        # No cached data - show config-based Stag estimate (less accurate)
        console.print(f"\n[bold cyan]━━━ Stag Pool Status (from config) ━━━[/bold cyan]")
        for hostname, stag_count in sorted(device_stag_counts.items()):
            pct = stag_count * 100 // STAG_LIMIT
            color = "red" if pct >= 90 else "yellow" if pct >= 70 else "green"
            console.print(f"  {hostname}: [{color}]{stag_count:,}[/{color}] / {STAG_LIMIT:,} ({pct}%)")
        console.print(f"  [bold]Highest:[/bold] [yellow]{current_stags:,}[/yellow] / {STAG_LIMIT:,}")
        console.print(f"  Safe capacity: [green]{remaining_stags:,}[/green] Stags [dim](limit: {effective_limit:,}, margin: {STAG_SAFETY_MARGIN})[/dim]")
        
        if remaining_stags <= 0:
            console.print(f"\n[bold red]⚠ STAG POOL AT LIMIT![/bold red]")
            console.print(f"[red]Warning: at {current_stags:,} Stags (safe limit: {effective_limit:,})[/red]")
            console.print(f"[dim]Expected error: 'Hook failed - assign_new_if_index'[/dim]")
            if not Confirm.ask("[yellow]Proceed anyway (will likely fail)?[/yellow]", default=False):
                return False
            remaining_stags = 10  # Allow manual entry
    
    # How many to add?
    if suggested_max is not None:
        default_count = suggested_max  # Use full suggested amount as default
        # Kernel-based limit already shown above - no need to repeat
    else:
        default_count = min(100, remaining_stags)
        console.print(f"\n[dim]Maximum you can add: {remaining_stags:,} (based on config Q-in-Q count)[/dim]")
        console.print(f"[dim]Note: For kernel-level accuracy, use 'Stag Pool Check' from main menu first.[/dim]")
    
    count = int_prompt_nav("How many more services to add?", default=default_count)
    if count <= 0:
        return False
    
    # Determine the effective maximum (prefer cached kernel data)
    effective_max = suggested_max if suggested_max is not None else remaining_stags
    effective_source = "kernel pool check" if suggested_max is not None else "Stag limit"
    
    # Check if requested count exceeds effective maximum
    if count > effective_max:
        console.print(f"\n[bold red]⚠ WARNING: Requested {count:,} but only {effective_max:,} available ({effective_source})![/bold red]")
        if suggested_max is not None and suggested_bottleneck:
            console.print(f"[yellow]Bottleneck: {suggested_bottleneck}[/yellow]")
        console.print(f"[yellow]This WILL fail with 'assign_new_if_index' hook error![/yellow]")
        if not Confirm.ask(f"Reduce to {effective_max:,} services instead?", default=True):
            if not Confirm.ask("Proceed anyway (will likely fail)?", default=False):
                return False
        else:
            count = effective_max
            console.print(f"[green]✓ Reduced to {count:,} services[/green]")
    
    start_num = start_num_base
    end_num = start_num + count - 1
    
    # Final Stag calculation
    final_stags = current_stags + count
    console.print(f"\n[green]Will create {svc_type_name} #{start_num} to #{end_num} ({count} services)[/green]")
    pct_after = final_stags * 100 // STAG_LIMIT
    headroom = effective_limit - final_stags
    headroom_color = "green" if headroom > 10 else "yellow" if headroom > 0 else "red"
    console.print(f"[dim]After scaling: {final_stags:,} / {STAG_LIMIT:,} Stags ({pct_after}%) | Headroom: [{headroom_color}]{headroom}[/{headroom_color}][/dim]")
    
    # FXC, VPWS, and FlowSpec VPN are fully supported
    if svc_type == "flowspec-vpn":
        return _execute_flowspec_vpn_scale_up(
            multi_ctx, device_services, count, start_num_base, return_config=return_config
        )
    
    if svc_type not in ("fxc", "vpws"):
        console.print(f"\n[yellow]⚠ Scale UP for {svc_type_name} requires the full configuration wizard.[/yellow]")
        return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # INTERFACE TYPE DETECTION - Self-aware wizard reads device's actual config
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Detect interface type from existing services
    detected_iface_type = None
    detected_parent = None
    detected_last_vlan = 0
    
    if last_service and last_service.interfaces:
        sample_iface = last_service.interfaces[0]
        if sample_iface.startswith('ph'):
            detected_iface_type = 'pwhe'
        elif sample_iface.startswith(('ge', 'xe', 'et')):
            detected_iface_type = 'l2ac'
            # Extract parent (e.g., ge100-18/0/0.2304 -> ge100-18/0/0)
            if '.' in sample_iface:
                detected_parent = sample_iface.rsplit('.', 1)[0]
                try:
                    detected_last_vlan = int(sample_iface.rsplit('.', 1)[1])
                except ValueError:
                    detected_last_vlan = 0
        elif sample_iface.startswith(('bundle', 'lag')):
            detected_iface_type = 'bundle'
            if '.' in sample_iface:
                detected_parent = sample_iface.rsplit('.', 1)[0]
                try:
                    detected_last_vlan = int(sample_iface.rsplit('.', 1)[1])
                except ValueError:
                    detected_last_vlan = 0
    
    # If not detected, scan the full config for existing FXC interface patterns
    if not detected_iface_type:
        config = multi_ctx.configs.get(list(device_services.keys())[0], "")
        # Look for FXC interface patterns in config
        l2ac_match = re.search(r'interface\s+((?:ge|xe|et)\d+-[\d/]+)\.\d+', config)
        pwhe_match = re.search(r'interface\s+ph\d+\.\d+', config)
        
        if l2ac_match:
            detected_iface_type = 'l2ac'
            detected_parent = l2ac_match.group(1)
            console.print(f"\n[cyan]Detected L2-AC parent from config: {detected_parent}[/cyan]")
        elif pwhe_match:
            detected_iface_type = 'pwhe'
            console.print(f"\n[cyan]Detected PWHE interface usage from config[/cyan]")
    
    # Ask user to confirm or select interface type
    # VPWS always uses L2-AC interfaces - streamlined flow
    if svc_type == "vpws":
        use_l2ac = True
        # Skip redundant display - info already shown in service summary
        if not (detected_iface_type == 'l2ac' and detected_parent):
            detected_parent = None
    else:
        # FXC can use either PWHE or L2-AC
        console.print("\n[bold]Interface Type for FXC Services:[/bold]")
        
        if detected_iface_type == 'l2ac':
            console.print(f"  [green]✓ Detected: L2-AC ({detected_parent}.XXXX)[/green]")
            console.print(f"  [1] [green]Use L2-AC[/green] - Continue with {detected_parent}.{detected_last_vlan + 1}+")
            console.print(f"  [2] Switch to PWHE (phX.Y)")
            console.print(f"  [B] Back")
            
            iface_choice = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="1").lower()
            if iface_choice == "b":
                return False
            use_l2ac = (iface_choice == "1")
        elif detected_iface_type == 'pwhe':
            console.print(f"  [green]✓ Detected: PWHE (phX.Y)[/green]")
            console.print(f"  [1] [green]Use PWHE[/green] - Continue with ph{start_num}.1+")
            console.print(f"  [2] Switch to L2-AC (ge/bundle.Y)")
            console.print(f"  [B] Back")
            
            iface_choice = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="1").lower()
            if iface_choice == "b":
                return False
            use_l2ac = (iface_choice == "2")
        else:
            console.print(f"  [yellow]⚠ Could not detect interface type from existing config[/yellow]")
            console.print(f"  [1] PWHE (phX.Y) - Creates new PWHE interfaces")
            console.print(f"  [2] L2-AC (ge/bundle.Y) - Uses existing physical interface")
            console.print(f"  [B] Back")
            
            iface_choice = Prompt.ask("Select interface type", choices=["1", "2", "b", "B"], default="1").lower()
            if iface_choice == "b":
                return False
            use_l2ac = (iface_choice == "2")
    
    # If L2-AC selected, get parent interface details
    l2ac_parent = None
    l2ac_start_vlan = 0
    
    if use_l2ac:
        default_vlan = detected_last_vlan + 1 if detected_last_vlan else start_num
        
        if detected_parent:
            # Auto-use detected parent for VPWS, just confirm starting VLAN
            l2ac_parent = str_prompt_nav("Parent interface", default=detected_parent)
            l2ac_start_vlan = int_prompt_nav("Starting VLAN/sub-interface number", default=default_vlan)
        else:
            console.print("\n[bold]L2-AC Configuration:[/bold]")
            console.print("  [dim]Example: ge100-18/0/0, bundle-1, xe100-0/0/1[/dim]")
            l2ac_parent = Prompt.ask("Parent interface")
        if not l2ac_parent:
            console.print("[red]Parent interface required for L2-AC[/red]")
            return False
        l2ac_start_vlan = int_prompt_nav("Starting VLAN/sub-interface number", default=default_vlan)
    
    # Generate configuration
    console.print("\n[bold]Generating configuration...[/bold]")
    
    # Get BGP ASN from config
    config = multi_ctx.configs.get(list(device_services.keys())[0], "")
    asn_match = re.search(r'bgp\s+(\d+)', config)
    bgp_asn = asn_match.group(1) if asn_match else "1234567"
    
    # Get loopback for RD
    loopback = multi_ctx.loopbacks.get(list(device_services.keys())[0], "1.1.1.1")
    
    # Detect VLAN pattern from existing interfaces
    config = multi_ctx.configs.get(list(device_services.keys())[0], "")
    iface_pattern = _detect_interface_pattern_from_config(config, l2ac_parent) if l2ac_parent else None
    
    # Scan for L3 sub-interfaces on L2-AC parent (IP addresses conflict with l2-service)
    l3_conflict_vlans = set()
    if use_l2ac and l2ac_parent and config:
        l3_conflict_vlans = _scan_l3_sub_ids(config, l2ac_parent)
        if l3_conflict_vlans:
            console.print(f"[yellow]⚠ {len(l3_conflict_vlans)} existing L3 sub-interface(s) on {l2ac_parent} "
                          f"(have IP addresses, will skip)[/yellow]")
    
    # Generate interface config based on type
    if use_l2ac:
        # L2-AC interfaces (ge/bundle sub-interfaces with l2-service)
        iface_config = "interfaces\n"
        vlan_list = []
        candidate_vlan = l2ac_start_vlan
        needed = end_num - start_num + 1
        while len(vlan_list) < needed:
            if candidate_vlan not in l3_conflict_vlans:
                vlan_list.append(candidate_vlan)
            candidate_vlan += 1
        
        for i, n in enumerate(range(start_num, end_num + 1)):
            vlan = vlan_list[i]
            iface_config += f"  {l2ac_parent}.{vlan}\n"
            iface_config += f"    admin-state enabled\n"
            iface_config += f"    l2-service enabled\n"
            
            # Apply detected VLAN pattern
            if iface_pattern and iface_pattern["uses_vlan_tags"]:
                # Use vlan-tags with outer-tag/inner-tag (QinQ)
                step_mode = iface_pattern.get("step_mode", "inner")
                
                if step_mode == "outer":
                    # Outer-tag steps, inner-tag fixed (e.g., outer=N, inner=1)
                    outer_tag = vlan
                    inner_tag = iface_pattern.get("inner_tag", 1)
                    if outer_tag > 4094:
                        outer_tag = ((vlan - 1) % 4094) + 1
                else:
                    # Inner-tag steps, outer-tag fixed (e.g., outer=1, inner=N)
                    outer_tag = iface_pattern.get("outer_tag", 1)
                    inner_tag = vlan
                    if inner_tag > 4094:
                        outer_tag = iface_pattern.get("outer_tag", 1) + ((vlan - 1) // 4094)
                        inner_tag = ((vlan - 1) % 4094) + 1
                
                iface_config += f"    vlan-tags outer-tag {outer_tag} inner-tag {inner_tag} outer-tpid {iface_pattern['outer_tpid']}\n"
            elif iface_pattern and iface_pattern["uses_vlan_id"]:
                iface_config += f"    vlan-id {vlan}\n"
            else:
                # Default to vlan-tags for VPWS, vlan-id for FXC
                if svc_type == "vpws":
                    outer_tag = 1
                    inner_tag = vlan
                    if inner_tag > 4094:
                        outer_tag = (inner_tag - 1) // 4094 + 1
                        inner_tag = ((inner_tag - 1) % 4094) + 1
                    iface_config += f"    vlan-tags outer-tag {outer_tag} inner-tag {inner_tag} outer-tpid 0x8100\n"
                else:
                    iface_config += f"    vlan-id {vlan}\n"
            
            # Apply vlan-manipulation if detected
            if iface_pattern and iface_pattern["has_vlan_manipulation"]:
                iface_config += f"    vlan-manipulation {iface_pattern['vlan_manipulation']}\n"
            
            iface_config += f"  !\n"
        iface_config += "!\n"
        
        iface_type_display = "L2-AC"
    else:
        # PWHE interfaces (phX + phX.Y with QinQ)
        iface_config = "interfaces\n"
        for n in range(start_num, end_num + 1):
            # Calculate VLAN tags - inner-tag max is 4094
            outer_tag = ((n - 1) // 4094) + 1
            inner_tag = ((n - 1) % 4094) + 1
            
            # Parent interface
            iface_config += f"  ph{n}\n"
            iface_config += f"    admin-state enabled\n"
            iface_config += f"  !\n"
            # Sub-interface with QinQ VLAN tags
            iface_config += f"  ph{n}.1\n"
            iface_config += f"    admin-state enabled\n"
            iface_config += f"    vlan-tags outer-tag {outer_tag} inner-tag {inner_tag} outer-tpid 0x8100\n"
            iface_config += f"  !\n"
        iface_config += "!\n"
        
        iface_type_display = "PWHE"
    
    # Generate services based on type
    svc_config = "network-services\n"
    
    if svc_type == "vpws":
        # EVPN-VPWS services
        svc_config += "  evpn-vpws\n"
        for i, n in enumerate(range(start_num, end_num + 1)):
            vlan = l2ac_start_vlan + i if l2ac_start_vlan else n
            iface_name = f"{l2ac_parent}.{vlan}"
            
            svc_config += f"    instance VPWS-{n}\n"
            svc_config += f"      protocols\n"
            svc_config += f"        bgp {bgp_asn}\n"
            svc_config += f"          export-l2vpn-evpn route-target {bgp_asn}:{n}\n"
            svc_config += f"          import-l2vpn-evpn route-target {bgp_asn}:{n}\n"
            svc_config += f"          route-distinguisher {loopback}:{n}\n"
            svc_config += f"        !\n"
            svc_config += f"      !\n"
            svc_config += f"      transport-protocol\n"
            svc_config += f"        mpls\n"
            svc_config += f"          control-word enabled\n"
            svc_config += f"          fat-label disabled\n"
            svc_config += f"        !\n"
            svc_config += f"      !\n"
            svc_config += f"      admin-state enabled\n"
            svc_config += f"      interface {iface_name}\n"
            svc_config += f"        vpws-service-id local {n} remote {n}\n"
            svc_config += f"      !\n"
            svc_config += f"    !\n"
        svc_config += "  !\n"
    else:
        # FXC services
        svc_config += "  evpn-vpws-fxc\n"
    for i, n in enumerate(range(start_num, end_num + 1)):
        # Determine interface name based on type
        if use_l2ac:
            vlan = l2ac_start_vlan + i
            iface_name = f"{l2ac_parent}.{vlan}"
        else:
            iface_name = f"ph{n}.1"
        
            svc_config += f"    instance FXC-{n}\n"
            svc_config += f"      protocols\n"
            svc_config += f"        bgp {bgp_asn}\n"
            svc_config += f"          export-l2vpn-evpn route-target {bgp_asn}:{n}\n"
            svc_config += f"          import-l2vpn-evpn route-target {bgp_asn}:{n}\n"
            svc_config += f"          route-distinguisher {loopback}:{n}\n"
            svc_config += f"        !\n"
            svc_config += f"      !\n"
            svc_config += f"      transport-protocol\n"
            svc_config += f"        mpls\n"
            svc_config += f"          control-word enabled\n"
            svc_config += f"          fat-label disabled\n"
            svc_config += f"        !\n"
            svc_config += f"      !\n"
            svc_config += f"      admin-state enabled\n"
            svc_config += f"      interface {iface_name}\n"
            svc_config += f"      !\n"
            svc_config += f"    !\n"
        svc_config += "  !\n"
    
    svc_config += "!\n"
    
    # Combine configs
    full_config = iface_config + "\n" + svc_config
    
    # Show preview
    lines = full_config.split('\n')
    console.print(f"\n[bold]Configuration Preview ({len(lines)} lines):[/bold]")
    console.print("[dim]First 20 lines:[/dim]")
    for line in lines[:20]:
        console.print(f"  [dim]{line}[/dim]")
    console.print(f"  [dim]... ({len(lines) - 20} more lines)[/dim]")
    
    # Confirm
    console.print(f"\n[bold yellow]⚠ This will add {count} {svc_type_name} services + {count} {iface_type_display} interfaces[/bold yellow]")
    if use_l2ac:
        console.print(f"[bold yellow]  Interface range: {l2ac_parent}.{l2ac_start_vlan} to {l2ac_parent}.{l2ac_start_vlan + count - 1}[/bold yellow]")
    else:
        console.print(f"[bold yellow]  Total Stags after: ~{final_stags}[/bold yellow]")
    
    if not Confirm.ask("\nProceed with configuration?", default=False):
        console.print("[yellow]Cancelled.[/yellow]")
        return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PUSH OPTIONS - File save, push method, live terminal
    # ═══════════════════════════════════════════════════════════════════════════
    console.print("\n[bold cyan]━━━ Push Options ━━━[/bold cyan]")
    
    # Option 1: Save to file
    from ..utils import get_device_config_dir, timestamp_filename
    from pathlib import Path
    
    # Push method selection FIRST (determines if save is needed)
    console.print("\n[bold]Select push method:[/bold]")
    console.print("  [1] Terminal Paste (paste directly into CLI)")
    console.print("  [2] File Merge (upload file + load merge)")
    push_method = Prompt.ask("Method", choices=["1", "2"], default="1")
    use_terminal_paste = (push_method == "1")
    
    # Save file: required for File Merge, optional for Terminal Paste
    saved_filepath = None
    if use_terminal_paste:
        # Optional save for terminal paste
        if Confirm.ask("Save configuration to file?", default=False):
            for dev in multi_ctx.devices:
                config_dir = get_device_config_dir(dev.hostname)
                filename = f"scale_up_{svc_type_name}_{count}_{timestamp_filename()}.txt"
                filepath = config_dir / filename
                with open(filepath, 'w') as f:
                    f.write(full_config)
                console.print(f"  [green]✓[/green] Saved: {filepath}")
                saved_filepath = filepath
    else:
        # Auto-save for file merge (required)
        for dev in multi_ctx.devices:
            config_dir = get_device_config_dir(dev.hostname)
            filename = f"scale_up_{svc_type_name}_{count}_{timestamp_filename()}.txt"
            filepath = config_dir / filename
            with open(filepath, 'w') as f:
                f.write(full_config)
            console.print(f"  [dim]Auto-saved for upload: {filepath}[/dim]")
            saved_filepath = filepath
    
    # Live terminal output option
    show_live_terminal = Confirm.ask("Show live terminal output?", default=True)
    
    # Push to devices with live progress display (same pattern as other operations)
    console.print("\n[bold cyan]🚀 Pushing Scale UP Configuration[/bold cyan]")
    
    from ..config_pusher import ConfigPusher, get_learned_timing_by_scale, save_timing_record
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.console import Group
    import threading
    import time
    
    # Track progress per device - now includes terminal_lines for split-screen
    device_progress = {
        dev.hostname: {
            "status": "pending", 
            "progress": 0, 
            "message": "Waiting...", 
            "start_time": None,
            "terminal_lines": []  # Buffer for terminal output
        } 
        for dev in multi_ctx.devices
    }
    results = {}
    progress_lock = threading.Lock()
    MAX_TERMINAL_LINES = 12  # Lines to show per device terminal
    
    # Calculate ETA using accurate timing data
    total_lines = len(full_config.splitlines())
    
    # Use the new accurate estimation system
    from ..config_pusher import get_accurate_push_estimates
    
    estimates = get_accurate_push_estimates(
        config_text=full_config,
        platform=multi_ctx.devices[0].platform.value if multi_ctx.devices else "SA-36CD-S"
    )
    
    # Get file upload estimate (we're using SCP + load)
    estimated_seconds = estimates['estimates']['file_upload']['total']
    source = estimates['source']
    source_detail = estimates['source_detail']
    confidence = estimates['confidence']
    
    # Show estimation with source info
    def format_time(seconds: float) -> str:
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"
    
    console.print(f"[dim]Pushing {total_lines:,} lines × {len(multi_ctx.devices)} devices[/dim]")
    
    if source == 'similar_push':
        console.print(f"[green]📊 Est. ~{format_time(estimated_seconds)} per device - {source_detail}[/green]\n")
    elif source == 'scale_type':
        console.print(f"[yellow]📊 Est. ~{format_time(estimated_seconds)} per device - {source_detail}[/yellow]\n")
    else:
        console.print(f"[dim]📊 Est. ~{format_time(estimated_seconds)} per device - {source_detail}[/dim]\n")
    
    operation_start_time = time.time()
    
    def render_split_screen():
        """Render split-screen layout with per-device terminal panels - FIXED HEIGHT."""
        from rich.text import Text
        panels = []
        
        # Fixed height for consistent display (no jumping)
        PANEL_HEIGHT = MAX_TERMINAL_LINES + 5  # Total panel height
        
        for hostname, status in device_progress.items():
            status_str = status["status"]
            progress_pct = status["progress"]
            message = status["message"]
            terminal_lines = status.get("terminal_lines", [])
            
            # Build content with Text - use append with style, not markup strings
            content = Text()
            
            # Status line
            if status_str == "pending":
                content.append("⏳ Pending\n", style="dim")
                filled = 0
                bar_style = "dim"
            elif status_str == "connecting":
                content.append("🔌 Connecting...\n", style="yellow")
                filled = 4
                bar_style = "yellow"
            elif status_str == "uploading":
                filled = int(progress_pct / 5)  # 20 char bar (0-100% -> 0-20 blocks)
                # Extract line count from message like "Pasting line 901/40007..."
                import re
                line_match = re.search(r'(\d+)/(\d+)', message)
                if line_match:
                    current_line = int(line_match.group(1))
                    total_line = int(line_match.group(2))
                    # Recalculate progress based on actual line count
                    actual_pct = int((current_line / total_line) * 100) if total_line > 0 else 0
                    filled = int(actual_pct / 5)  # Map 0-100% to 0-20 blocks
                    content.append(f"📤 Line {current_line:,}/{total_line:,}\n", style="cyan")
                else:
                    content.append(f"📤 {message[:30]}\n", style="cyan")
                bar_style = "cyan"
            elif status_str == "committing":
                content.append("⚙️ Committing...\n", style="magenta")
                filled = 16
                bar_style = "magenta"
            elif status_str == "success":
                content.append("✓ Success!\n", style="green")
                filled = 20
                bar_style = "green"
            elif status_str == "failed":
                content.append(f"✗ {message[:25]}\n", style="red")
                filled = 20
                bar_style = "red"
            else:
                content.append(f"{status_str}\n")
                filled = 0
                bar_style = "dim"
            
            # Progress bar - use filled (0-20) to compute displayed percentage
            actual_pct_display = (filled * 5) if status_str == "uploading" else progress_pct
            content.append("Progress: ")
            content.append("█" * filled, style=bar_style)
            content.append("░" * (20 - filled), style="dim")
            content.append(f" {actual_pct_display}%\n", style=bar_style)
            
            PANEL_WIDTH = 70  # Wider panel for better error visibility
            content.append("─" * PANEL_WIDTH + "\n")
            
            # Add terminal output (show last N lines) - always fill to fixed height
            lines_to_show = terminal_lines[-MAX_TERMINAL_LINES:] if terminal_lines else []
            lines_added = 0
            
            for line in lines_to_show:
                # Clean and truncate line, escape Rich markup
                clean = line[:PANEL_WIDTH].replace('[', '\\[').replace(']', '\\]')
                
                # Detect error patterns and show in red
                is_error = any(err in clean.lower() for err in ['error', 'failed', 'cannot', 'hook failed', 'stag', 'limit'])
                
                if clean.startswith('→'):
                    # Config line being sent - green
                    content.append(f"  {clean}\n", style="bright_green")
                elif clean.startswith('←'):
                    # Device response - yellow
                    content.append(f"  {clean}\n", style="yellow")
                elif clean.startswith('✓'):
                    content.append(f"  {clean}\n", style="green")
                elif clean.startswith('✗') or is_error:
                    # Errors in red
                    content.append(f"  {clean}\n", style="bold red")
                elif clean.startswith('⏳'):
                    content.append(f"  {clean}\n", style="yellow")
                else:
                    content.append(f"  {clean}\n", style="dim")
                lines_added += 1
            
            # Pad to fixed height
            while lines_added < MAX_TERMINAL_LINES:
                content.append("\n")
                lines_added += 1
            
            # Determine border color
            if status_str == "success":
                border_style = "green"
            elif status_str == "failed":
                border_style = "red"
            elif status_str in ("uploading", "committing"):
                border_style = "cyan"
            else:
                border_style = "dim"
            
            panel = Panel(
                content,
                title=f"[bold white] {hostname} [/bold white]",
                border_style=border_style,
                height=PANEL_HEIGHT,
                expand=True,
                padding=(0, 1)
            )
            panels.append(panel)
        
        # Return columns of panels (side-by-side)
        return Columns(panels, expand=True, equal=True)
    
    def push_device(dev) -> Tuple[str, bool, str]:
        """Push config to a single device."""
        hostname = dev.hostname
        
        def add_terminal_line(line: str):
            """Add line to device's terminal buffer."""
            with progress_lock:
                device_progress[hostname]["terminal_lines"].append(line)
                # Keep buffer limited
                if len(device_progress[hostname]["terminal_lines"]) > 50:
                    device_progress[hostname]["terminal_lines"] = device_progress[hostname]["terminal_lines"][-50:]
        
        try:
            with progress_lock:
                device_progress[hostname]["status"] = "connecting"
                device_progress[hostname]["progress"] = 10
                device_progress[hostname]["message"] = "Connecting via SSH..."
            add_terminal_line("Connecting to device...")
            
            # Adjust loopback/RD per device
            dev_loopback = multi_ctx.loopbacks.get(hostname, loopback)
            dev_config = full_config.replace(f"route-distinguisher {loopback}:", f"route-distinguisher {dev_loopback}:")
            
            method_str = "Pasting" if use_terminal_paste else "Uploading"
            with progress_lock:
                device_progress[hostname]["status"] = "uploading"
                device_progress[hostname]["progress"] = 30
                device_progress[hostname]["message"] = f"{method_str} {len(dev_config.splitlines()):,} lines..."
            add_terminal_line(f"{method_str} {len(dev_config.splitlines()):,} config lines...")
            
            pusher = ConfigPusher(timeout=120, commit_timeout=1800)
            
            # Store total lines for accurate progress calculation
            total_config_lines = len(dev_config.splitlines())
            
            def progress_callback(msg: str, pct: int):
                with progress_lock:
                    if "commit" in msg.lower():
                        device_progress[hostname]["status"] = "committing"
                        device_progress[hostname]["progress"] = 85 + int(pct * 0.15)  # 85-100%
                    else:
                        # Extract actual progress from message "Pasting line X/Y..."
                        line_match = re.search(r'(\d+)/(\d+)', msg)
                        if line_match:
                            current = int(line_match.group(1))
                            total = int(line_match.group(2))
                            # Pasting takes 0-80% of progress, commit is 80-100%
                            actual_pct = int((current / total) * 80) if total > 0 else pct
                            device_progress[hostname]["progress"] = actual_pct
                        else:
                            device_progress[hostname]["progress"] = min(80, pct)
                    device_progress[hostname]["message"] = msg
                add_terminal_line(msg)
            
            def live_output_callback(output: str):
                """Capture live output into device's terminal buffer."""
                for line in output.strip().split('\n'):
                    if line.strip():
                        add_terminal_line(line.strip()[-60:])  # Last 60 chars
            
            # Use terminal paste or file merge based on user selection
            # DON'T use show_live_terminal (causes flickering) - use live_output_callback instead
            if use_terminal_paste:
                success, output = pusher.push_config_terminal_paste(
                    dev, 
                    dev_config, 
                    dry_run=False, 
                    progress_callback=progress_callback,
                    live_output_callback=live_output_callback if show_live_terminal else None,
                    show_live_terminal=False  # We handle display ourselves
                )
            else:
                success, output = pusher.push_config_merge(
                    dev, 
                    dev_config, 
                    dry_run=False, 
                    progress_callback=progress_callback
                )
            
            if success:
                with progress_lock:
                    device_progress[hostname] = {"status": "success", "progress": 100, "message": f"Added {count} FXC + {count} PWHE"}
                return hostname, True, f"Added {count} services"
            else:
                # Extract ACTUAL error message from device output
                error_msg = "Unknown error"
                if output:
                    # Look for specific DNOS error patterns in output
                    for line in output.split('\n'):
                        if 'Number of unique Stags cannot be greater than' in line:
                            error_msg = line.strip()
                            break
                        elif 'assign_new_if_index' in line or 'Hook failed' in line:
                            error_msg = line.strip()
                            break
                        elif 'Reason:' in line:
                            error_msg = line.strip()
                            break
                        elif 'Load failed' in line or 'Commit failed' in line:
                            error_msg = line.strip()
                            break
                    else:
                        # Fallback to last non-empty line
                        lines = [l.strip() for l in output.strip().split('\n') if l.strip()]
                        if lines:
                            error_msg = lines[-1]
                
                with progress_lock:
                    device_progress[hostname] = {"status": "failed", "progress": 50, "message": error_msg, "terminal_lines": device_progress[hostname].get("terminal_lines", [])}
                return hostname, False, error_msg
                
        except Exception as e:
            # Extract actual error message from exception
            error_str = str(e)
            error_msg = error_str.split('\n')[-1] if error_str else "Unknown error"
            
            # Try to find specific DNOS error in exception text
            for line in error_str.split('\n'):
                if 'Number of unique Stags' in line or 'Hook failed' in line:
                    error_msg = line.strip()
                    break
            
            with progress_lock:
                device_progress[hostname] = {"status": "failed", "progress": 0, "message": error_msg, "terminal_lines": device_progress[hostname].get("terminal_lines", [])}
            return hostname, False, error_msg
    
    # Execute in parallel with split-screen live display
    with Live(render_split_screen(), refresh_per_second=4, console=console, transient=False) as live:
        with ThreadPoolExecutor(max_workers=len(multi_ctx.devices)) as executor:
            futures = {executor.submit(push_device, dev): dev for dev in multi_ctx.devices}
            
            while any(f.running() for f in futures):
                live.update(render_split_screen())
                time.sleep(0.25)
            
            for future in as_completed(futures):
                hostname, success, message = future.result()
                results[hostname] = (success, message)
            
            live.update(render_split_screen())
    
    # Summary
    success_count = sum(1 for s, _ in results.values() if s)
    total_time = time.time() - operation_start_time
    
    console.print(f"\n[bold]Result: {success_count}/{len(multi_ctx.devices)} devices configured[/bold]")
    console.print(f"[dim]Total time: {total_time/60:.1f} minutes ({total_time:.0f}s)[/dim]")
    
    # Save timing for successful pushes to improve future estimates
    if success_count > 0:
        for dev in multi_ctx.devices:
            if results.get(dev.hostname, (False, ""))[0]:  # If success
                try:
                    save_timing_record(
                        platform=dev.platform.value if hasattr(dev.platform, 'value') else str(dev.platform),
                        line_count=total_lines,
                        pwhe_count=count,
                        fxc_count=count,
                        actual_time_seconds=total_time,
                        device_hostname=dev.hostname,
                        scale_counts={
                            "pwhe_subifs": count,
                            "fxc_services": count,
                            "operation": "scale_up"
                        }
                    )
                    console.print(f"[dim]✓ Saved timing data for {dev.hostname}[/dim]")
                except Exception as e:
                    pass  # Don't fail on timing save error
    
    if success_count < len(multi_ctx.devices):
        console.print("\n[yellow]Some devices failed - this may be due to the Stag limit validation![/yellow]")
        console.print("[dim]Check device logs for: 'Number of unique Stags cannot be greater than 4000'[/dim]")
    
    # Auto-refresh configs after successful push (ensures next Scale UP shows correct state)
    if success_count > 0:
        console.print("\n[dim]Refreshing device configurations...[/dim]")
        multi_ctx.discover_all()
        console.print("[green]✓ Config cache updated[/green]")
    
    return success_count > 0


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATE QUICK SCALE CONFIG - For adding to existing saved configs
# ═══════════════════════════════════════════════════════════════════════════════

def generate_quick_scale_config(
    device: Any,
    count: int,
    interface_type: str,  # "pwhe" or "l2ac"
    include_services: bool = True,
    start_index: int = 1,
    existing_config: str = "",
    l2ac_parent: str = None
) -> str:
    """
    Generate scale UP configuration for adding services + interfaces.
    
    Used by the Quick Load Mode to add more services/interfaces to an existing config.
    
    Args:
        device: Device object with hostname
        count: Number of services/interfaces to add
        interface_type: "pwhe" or "l2ac"
        include_services: Whether to include FXC services
        start_index: Starting service/interface number
        existing_config: Existing config to detect patterns from
        l2ac_parent: Parent interface for L2-AC (e.g., "ge100-0/0/0")
        
    Returns:
        Generated configuration string
    """
    config_lines = []
    hostname = device.hostname if hasattr(device, 'hostname') else str(device)
    
    # Detect RT ASN from existing config
    rt_asn = None
    
    # Method 1: Parse from existing services
    rt_match = re.search(r'route-target\s+(\d+):', existing_config)
    if rt_match:
        rt_asn = rt_match.group(1)
    
    # Method 2: Get from operational.json
    if not rt_asn:
        try:
            op_path = f"/home/dn/SCALER/db/configs/{hostname}/operational.json"
            if os.path.exists(op_path):
                with open(op_path, 'r') as f:
                    op_data = json.load(f)
                    if op_data.get('local_as'):
                        rt_asn = str(op_data['local_as'])
        except Exception:
            pass
    
    # Method 3: Parse from BGP config
    if not rt_asn:
        bgp_as_match = re.search(r'autonomous-system\s+(\d+)', existing_config)
        if bgp_as_match:
            rt_asn = bgp_as_match.group(1)
    
    # Default
    if not rt_asn:
        rt_asn = "65000"
    
    # Detect RD router-id from existing config
    rd_router_id = None
    rd_match = re.search(r'route-distinguisher\s+(\d+\.\d+\.\d+\.\d+):', existing_config)
    if rd_match:
        rd_router_id = rd_match.group(1)
    
    if not rd_router_id:
        # Try operational.json
        try:
            op_path = f"/home/dn/SCALER/db/configs/{hostname}/operational.json"
            if os.path.exists(op_path):
                with open(op_path, 'r') as f:
                    op_data = json.load(f)
                    if op_data.get('lo0_ip'):
                        rd_router_id = op_data['lo0_ip'].split('/')[0]
                    elif op_data.get('router_id'):
                        rd_router_id = op_data['router_id']
        except Exception:
            pass
    
    if not rd_router_id:
        rd_router_id = "1.1.1.1"
    
    # Detect L2-AC parent if not provided
    if interface_type.lower() == "l2ac" and not l2ac_parent:
        # Try to detect from existing config
        l2ac_match = re.search(r'^\s+(ge\d+-\d+/\d+/\d+|xe\d+-\d+/\d+/\d+)\.\d+', existing_config, re.MULTILINE)
        if l2ac_match:
            l2ac_parent = l2ac_match.group(1)
        else:
            l2ac_parent = "ge100-0/0/0"  # Default
    
    # Detect interface pattern from existing config
    iface_pattern = _detect_interface_pattern_from_config(existing_config, l2ac_parent) if l2ac_parent else {
        "uses_vlan_tags": True,
        "uses_vlan_id": False,
        "outer_tag": 1,
        "inner_tag": 1,
        "outer_tpid": "0x8100",
        "step_mode": "inner",
        "has_vlan_manipulation": False,
        "vlan_manipulation": "",
        "extra_lines": []
    }
    
    # Scan for L3 sub-interfaces on L2-AC parent
    l3_conflict_ids = set()
    if interface_type.lower() != "pwhe" and l2ac_parent and existing_config:
        l3_conflict_ids = _scan_l3_sub_ids(existing_config, l2ac_parent)
        if l3_conflict_ids:
            console.print(f"[yellow]⚠ {len(l3_conflict_ids)} existing L3 sub-interface(s) on {l2ac_parent} "
                          f"(have IP addresses, will skip)[/yellow]")
    
    # Build service number list, skipping L3 conflicts for L2-AC
    svc_number_list = []
    candidate = start_index
    while len(svc_number_list) < count:
        if interface_type.lower() == "pwhe" or candidate not in l3_conflict_ids:
            svc_number_list.append(candidate)
        candidate += 1
    
    # Generate interfaces
    config_lines.append("interfaces")
    
    for svc_num in svc_number_list:
        if interface_type.lower() == "pwhe":
            # PWHE parent
            config_lines.append(f"  ph{svc_num}")
            config_lines.append(f"    admin-state enabled")
            config_lines.append(f"  !")
            
            # PWHE sub-interface with outer-tag
            outer_tag = 1
            inner_tag = svc_num
            if inner_tag > 4094:
                outer_tag = (inner_tag - 1) // 4094 + 1
                inner_tag = ((inner_tag - 1) % 4094) + 1
            
            config_lines.append(f"  ph{svc_num}.1")
            config_lines.append(f"    admin-state enabled")
            config_lines.append(f"    vlan-tags outer-tag {outer_tag} inner-tag {inner_tag} outer-tpid 0x8100")
            config_lines.append(f"  !")
        else:
            # L2-AC interface
            config_lines.append(f"  {l2ac_parent}.{svc_num}")
            config_lines.append(f"    admin-state enabled")
            config_lines.append(f"    l2-service enabled")
            
            # Apply detected VLAN pattern
            if iface_pattern.get("uses_vlan_tags"):
                outer_tag = iface_pattern.get("outer_tag", 1)
                inner_tag = svc_num
                if inner_tag > 4094:
                    outer_tag = outer_tag + ((inner_tag - 1) // 4094)
                    inner_tag = ((inner_tag - 1) % 4094) + 1
                config_lines.append(f"    vlan-tags outer-tag {outer_tag} inner-tag {inner_tag} outer-tpid {iface_pattern.get('outer_tpid', '0x8100')}")
            elif iface_pattern.get("uses_vlan_id"):
                vlan_id = svc_num if svc_num <= 4094 else ((svc_num - 1) % 4094) + 1
                config_lines.append(f"    vlan-id {vlan_id}")
            else:
                inner_tag = svc_num if svc_num <= 4094 else ((svc_num - 1) % 4094) + 1
                config_lines.append(f"    vlan-tags outer-tag 1 inner-tag {inner_tag} outer-tpid 0x8100")
            
            # Apply vlan-manipulation if detected
            if iface_pattern.get("has_vlan_manipulation"):
                config_lines.append(f"    vlan-manipulation {iface_pattern['vlan_manipulation']}")
            
            config_lines.append(f"  !")
    
    config_lines.append("!")
    
    # Generate FXC services if requested
    if include_services:
        config_lines.append("network-services")
        config_lines.append("  evpn-vpws-fxc")
        
        for svc_num in svc_number_list:
            svc_name = f"FXC_{svc_num}"
            
            # Interface name
            if interface_type.lower() == "pwhe":
                iface_name = f"ph{svc_num}.1"
            else:
                iface_name = f"{l2ac_parent}.{svc_num}"
            
            # FXC instance with correct DNOS hierarchy
            config_lines.append(f"    instance {svc_name}")
            config_lines.append(f"      protocols")
            config_lines.append(f"        bgp {rt_asn}")
            config_lines.append(f"          export-l2vpn-evpn route-target {rt_asn}:{svc_num}")
            config_lines.append(f"          import-l2vpn-evpn route-target {rt_asn}:{svc_num}")
            config_lines.append(f"          route-distinguisher {rd_router_id}:{svc_num}")
            config_lines.append(f"        !")  # Close bgp
            config_lines.append(f"      !")  # Close protocols
            config_lines.append(f"      transport-protocol")
            config_lines.append(f"        mpls")
            config_lines.append(f"          control-word enabled")
            config_lines.append(f"          fat-label disabled")
            config_lines.append(f"        !")  # Close mpls
            config_lines.append(f"      !")  # Close transport-protocol
            config_lines.append(f"      admin-state enabled")
            config_lines.append(f"      interface {iface_name}")
            config_lines.append(f"        fxc-service-id local {svc_num} remote {svc_num}")
            config_lines.append(f"      !")  # Close interface
            config_lines.append(f"    !")  # Close instance
        
        config_lines.append("  !")  # Close evpn-vpws-fxc
        config_lines.append("!")  # Close network-services
    
    return "\n".join(config_lines)

