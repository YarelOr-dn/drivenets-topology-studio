"""
Configuration Parsing Functions for the SCALER Wizard.

This module contains functions for parsing device configurations:
- EVPN service parsing (FXC, VPLS, MPLS)
- Route Target extraction
- Multihoming configuration parsing
- Interface-to-RT and Interface-to-VLAN mappings
- ESI group building by RT+VLAN
- Hierarchy section extraction
- Loopback/AS/Router-ID extraction
- MPLS-enabled interface detection
"""

import re
from typing import Any, Dict, List, Optional, Set


def parse_route_targets(config: str) -> set:
    """Extract all route-targets from a configuration."""
    rt_pattern = r'route-target\s+(\d+:\d+)'
    return set(re.findall(rt_pattern, config))


def parse_existing_multihoming(config: str) -> dict:
    """
    Parse existing multihoming configuration from running config.
    
    Returns:
        Dict mapping interface names to their ESI values
    """
    mh_interfaces = {}
    
    if not config:
        return mh_interfaces
    
    # Strategy: Find "multihoming" section and scan until we hit a line that's
    # NOT indented (meaning we've left the multihoming block)
    
    # Find start of multihoming section
    mh_start = re.search(r'^(\s*)multihoming\s*$', config, re.MULTILINE)
    if not mh_start:
        # Also try without anchor for show command output
        mh_start = re.search(r'multihoming\s*\n', config)
    
    if mh_start:
        start_pos = mh_start.end()
        base_indent = len(mh_start.group(1)) if mh_start.lastindex else 0
        
        # Find where multihoming section ends (next line with same or less indentation)
        remaining = config[start_pos:]
        
        # For full config: find next section at same indent level (or less)
        # Match line that starts with base_indent or fewer spaces followed by non-space
        end_pattern = re.compile(r'^[ ]{0,' + str(base_indent) + r'}[^ \n!]', re.MULTILINE)
        end_match = end_pattern.search(remaining)
        
        if end_match:
            mh_section = remaining[:end_match.start()]
        else:
            mh_section = remaining
    else:
        # Fallback: search entire config for interface+ESI patterns
        mh_section = config
    
    # Parse interface -> ESI mappings (all interface types: ph*, ge*, bundle-*, etc.)
    iface_pattern = r'interface\s+(\S+)\s*\n\s*esi\s+arbitrary\s+value\s+([0-9a-fA-F:]+)'
    for match in re.finditer(iface_pattern, mh_section, re.IGNORECASE):
        iface_name = match.group(1)
        esi_value = match.group(2)
        mh_interfaces[iface_name] = esi_value
    
    return mh_interfaces


def parse_existing_evpn_services(config_text: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Parse existing EVPN services from running configuration.
    
    Extracts:
    - evpn-vpws-fxc instances with their interfaces
    - evpn-vpls instances with their interfaces
    - evpn-mpls instances with their interfaces
    
    Returns:
        Dict with keys 'fxc', 'vpls', 'mpls' containing list of service dicts:
        {
            'name': 'FXC-1',
            'interfaces': ['ge100-18/0/0.1'],
            'rt_export': ['1234567:1'],
            'rt_import': ['1234567:1'],
            'rd': '4.4.4.4:1'
        }
    """
    services = {
        'fxc': [],
        'vpls': [],
        'mpls': []
    }
    
    def parse_service_block(block_text: str) -> List[Dict[str, Any]]:
        """Parse instances from a service type block."""
        result = []
        lines = block_text.split('\n')
        
        current_instance = None
        current_interfaces = []
        current_rt_export = []
        current_rt_import = []
        current_rd = None
        
        for line in lines:
            stripped = line.strip()
            
            # New instance start
            if stripped.startswith('instance '):
                # Save previous instance if exists
                if current_instance:
                    result.append({
                        'name': current_instance,
                        'interfaces': current_interfaces,
                        'rt_export': current_rt_export,
                        'rt_import': current_rt_import,
                        'rd': current_rd
                    })
                
                current_instance = stripped.replace('instance ', '').strip()
                current_interfaces = []
                current_rt_export = []
                current_rt_import = []
                current_rd = None
            
            # Interface attachment (but not "interface-mode")
            elif stripped.startswith('interface ') and not stripped.startswith('interface-'):
                iface = stripped.replace('interface ', '').strip()
                if iface and iface != '!':
                    current_interfaces.append(iface)
            
            # RT export
            elif 'export-l2vpn-evpn route-target' in stripped:
                match = re.search(r'route-target\s+(\S+)', stripped)
                if match:
                    current_rt_export.append(match.group(1))
            
            # RT import
            elif 'import-l2vpn-evpn route-target' in stripped:
                match = re.search(r'route-target\s+(\S+)', stripped)
                if match:
                    current_rt_import.append(match.group(1))
            
            # RD
            elif stripped.startswith('route-distinguisher '):
                current_rd = stripped.replace('route-distinguisher ', '').strip()
        
        # Save last instance
        if current_instance:
            result.append({
                'name': current_instance,
                'interfaces': current_interfaces,
                'rt_export': current_rt_export,
                'rt_import': current_rt_import,
                'rd': current_rd
            })
        
        return result
    
    # Find evpn-vpws-fxc block
    fxc_start = config_text.find('evpn-vpws-fxc')
    if fxc_start != -1:
        # Find the end - look for closing hierarchy or next service type
        fxc_block_start = fxc_start + len('evpn-vpws-fxc')
        
        # Find next major section at same level (2-space indent) or end
        # CRITICAL: Must stop at 'multihoming' which is a sibling section!
        next_sections = []
        for marker in ['evpn-vpls\n', 'evpn-mpls\n', '\n  multihoming', '\n  !']:
            pos = config_text.find(marker, fxc_block_start)
            if pos != -1:
                next_sections.append(pos)
        
        fxc_end = min(next_sections) if next_sections else len(config_text)
        fxc_block = config_text[fxc_block_start:fxc_end]
        
        services['fxc'] = parse_service_block(fxc_block)
    
    # Find evpn-vpls block
    vpls_start = config_text.find('evpn-vpls')
    if vpls_start != -1:
        vpls_block_start = vpls_start + len('evpn-vpls')
        
        # Stop at sibling sections (2-space indent)
        next_sections = []
        for marker in ['evpn-vpws-fxc\n', 'evpn-mpls\n', '\n  multihoming', '\n  !']:
            pos = config_text.find(marker, vpls_block_start)
            if pos != -1:
                next_sections.append(pos)
        
        vpls_end = min(next_sections) if next_sections else len(config_text)
        vpls_block = config_text[vpls_block_start:vpls_end]
        
        services['vpls'] = parse_service_block(vpls_block)
    
    # Find evpn-mpls block
    mpls_start = config_text.find('evpn-mpls')
    if mpls_start != -1:
        mpls_block_start = mpls_start + len('evpn-mpls')
        
        # Stop at sibling sections (2-space indent)
        next_sections = []
        for marker in ['evpn-vpws-fxc\n', 'evpn-vpls\n', '\n  multihoming', '\n  !']:
            pos = config_text.find(marker, mpls_block_start)
            if pos != -1:
                next_sections.append(pos)
        
        mpls_end = min(next_sections) if next_sections else len(config_text)
        mpls_block = config_text[mpls_block_start:mpls_end]
        
        services['mpls'] = parse_service_block(mpls_block)
    
    return services


def build_rt_to_esi_mapping(config: str, mh_config: dict) -> dict:
    """
    Build a mapping from Route Target to ESI value.
    
    This is the key for service-based ESI matching:
    - Each FXC service has a unique RT
    - Each service has an interface attached
    - If that interface has an ESI, we map: RT -> ESI
    
    This allows PE-2 to find the correct ESI for its service based on RT match,
    regardless of interface name.
    
    Args:
        config: Full running configuration text
        mh_config: Dict of interface -> ESI mappings from parse_existing_multihoming
        
    Returns:
        Dict mapping RT to {'esi': str, 'interface': str, 'service': str}
    """
    rt_to_esi = {}
    
    # Parse all FXC services
    services = parse_existing_evpn_services(config)
    
    # For each FXC service, check if its interface has MH configured
    for svc in services.get('fxc', []):
        svc_name = svc.get('name', '')
        rts = svc.get('rt_export', []) + svc.get('rt_import', [])
        interfaces = svc.get('interfaces', [])
        
        # Unique RTs for this service
        unique_rts = set(rts)
        
        for iface in interfaces:
            if iface in mh_config:
                esi_value = mh_config[iface]
                # Map each RT to this ESI
                for rt in unique_rts:
                    rt_to_esi[rt] = {
                        'esi': esi_value,
                        'interface': iface,
                        'service': svc_name
                    }
    
    # Also handle VPLS services
    for svc in services.get('vpls', []):
        svc_name = svc.get('name', '')
        rts = svc.get('rt_export', []) + svc.get('rt_import', [])
        interfaces = svc.get('interfaces', [])
        
        unique_rts = set(rts)
        
        for iface in interfaces:
            if iface in mh_config:
                esi_value = mh_config[iface]
                for rt in unique_rts:
                    if rt not in rt_to_esi:  # Don't overwrite FXC mappings
                        rt_to_esi[rt] = {
                            'esi': esi_value,
                            'interface': iface,
                            'service': svc_name
                        }
    
    return rt_to_esi


def build_interface_to_vlan_mapping(config: str) -> dict:
    """
    Parse interface vlan-tags configuration.
    
    For EVPN-VPWS-FXC with PWHE, ESI matching requires both RT AND VLAN-TAG matching.
    This function extracts the VLAN configuration for each interface.
    
    Args:
        config: Full running configuration text
        
    Returns:
        Dict mapping interface name to vlan_key string:
        - For vlan-tags: "outer:inner" (e.g., "1:100")
        - For vlan-id: "vid:X" (e.g., "vid:100")
        - If no vlan config: "none"
    """
    iface_to_vlan = {}
    
    # Parse interface blocks
    # Pattern: interface name followed by vlan-tags or vlan-id
    lines = config.split('\n')
    current_iface = None
    indent_level = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Detect interface declaration (phX.Y or other L2 interfaces)
        # Match: "  ph1.1" or "  ge400-0/0/4.50" at interface level
        if re.match(r'^  (ph\d+\.\d+|ge\d+-\d+/\d+/\d+\.\d+|lag\d+\.\d+)$', line):
            current_iface = stripped
            indent_level = len(line) - len(line.lstrip())
            continue
        
        # If we're inside an interface block
        if current_iface:
            current_indent = len(line) - len(line.lstrip())
            
            # Check if we've exited the interface block
            if stripped and current_indent <= indent_level and not stripped.startswith('!'):
                current_iface = None
                continue
            
            # Parse vlan-tags: "vlan-tags outer-tag X inner-tag Y outer-tpid 0x8100"
            vlan_tags_match = re.match(r'vlan-tags\s+outer-tag\s+(\d+)\s+inner-tag\s+(\d+)', stripped)
            if vlan_tags_match:
                outer = vlan_tags_match.group(1)
                inner = vlan_tags_match.group(2)
                iface_to_vlan[current_iface] = f"{outer}:{inner}"
                continue
            
            # Parse vlan-id: "vlan-id X"
            vlan_id_match = re.match(r'vlan-id\s+(\d+)', stripped)
            if vlan_id_match:
                vid = vlan_id_match.group(1)
                iface_to_vlan[current_iface] = f"vid:{vid}"
                continue
            
            # End of interface block
            if stripped == '!':
                # If interface had no vlan config, mark as "none"
                if current_iface and current_iface not in iface_to_vlan:
                    iface_to_vlan[current_iface] = "none"
                current_iface = None
    
    return iface_to_vlan


def build_interface_to_rt_mapping(config: str) -> dict:
    """
    Build a mapping from interface name to its Route Target(s).
    
    Used on the local device to find which RT a local interface belongs to,
    so we can look up the matching ESI from the neighbor.
    
    Args:
        config: Full running configuration text
        
    Returns:
        Dict mapping interface name to set of RTs
    """
    iface_to_rt = {}
    
    services = parse_existing_evpn_services(config)
    
    for svc_type in ['fxc', 'vpls', 'mpls']:
        for svc in services.get(svc_type, []):
            rts = set(svc.get('rt_export', []) + svc.get('rt_import', []))
            interfaces = svc.get('interfaces', [])
            
            for iface in interfaces:
                if iface not in iface_to_rt:
                    iface_to_rt[iface] = set()
                iface_to_rt[iface].update(rts)
    
    return iface_to_rt


def build_interface_to_rt_vlan_mapping(config: str) -> dict:
    """
    Build a combined mapping from interface name to RT(s) and VLAN-TAG.
    
    For EVPN-VPWS-FXC with PWHE multihoming, ESI matching requires:
    1. Same RT (same FXC service)
    2. Same VLAN-TAG (same sub-service within FXC)
    
    This function combines both mappings for efficient lookup.
    
    Args:
        config: Full running configuration text
        
    Returns:
        Dict mapping interface name to:
        {
            'rts': set of Route Targets,
            'vlan_key': VLAN key string ("outer:inner", "vid:X", or "none")
        }
    """
    # Get RT mapping
    iface_to_rt = build_interface_to_rt_mapping(config)
    
    # Get VLAN mapping
    iface_to_vlan = build_interface_to_vlan_mapping(config)
    
    # Combine into unified mapping
    combined = {}
    
    # Start with all interfaces that have RT mapping (in FXC/EVPN services)
    for iface, rts in iface_to_rt.items():
        vlan_key = iface_to_vlan.get(iface, "none")
        combined[iface] = {
            'rts': rts,
            'vlan_key': vlan_key
        }
    
    return combined


def build_esi_groups_by_rt_vlan(dev_mappings: dict) -> dict:
    """
    Build ESI groups from multiple devices based on RT + VLAN matching.
    
    Interfaces from different devices that share the same RT AND VLAN-TAG
    will be grouped together and should receive the same ESI.
    
    Args:
        dev_mappings: Dict of {hostname: {interface: {'rts': set, 'vlan_key': str}}}
        
    Returns:
        Dict of {composite_key: {'esi_index': int, 'devices': {hostname: [interfaces]}}}
        where composite_key = "RT:VLAN_KEY"
    """
    from collections import defaultdict
    
    # Build composite key groups
    # composite_key = "RT:VLAN_KEY" -> {hostname: [interfaces]}
    key_to_devices = defaultdict(lambda: defaultdict(list))
    
    for hostname, iface_mapping in dev_mappings.items():
        for iface, info in iface_mapping.items():
            vlan_key = info.get('vlan_key', 'none')
            for rt in info.get('rts', set()):
                composite_key = f"{rt}:{vlan_key}"
                key_to_devices[composite_key][hostname].append(iface)
    
    # Filter to only include keys that appear on multiple devices (shared services)
    # OR keep all for single-device scenarios
    shared_groups = {}
    esi_index = 1
    
    for composite_key in sorted(key_to_devices.keys()):
        devices = key_to_devices[composite_key]
        # Include if appears on at least one device
        if len(devices) >= 1:
            shared_groups[composite_key] = {
                'esi_index': esi_index,
                'devices': dict(devices)
            }
            esi_index += 1
    
    return shared_groups


def extract_hierarchy_section(config: str, hierarchy: str) -> Optional[str]:
    """Extract a specific hierarchy section from the configuration.
    
    DNOS hierarchy structure requires each top-level section to end with '!'
    to properly close it before the next hierarchy begins.
    """
    hierarchy_map = {
        'system': 'system',
        'interfaces': 'interfaces',
        'services': 'network-services',
        'bgp': 'protocols',
        'vlans': 'interfaces',  # VLANs are within interfaces
    }
    
    target = hierarchy_map.get(hierarchy, hierarchy)
    lines = config.split('\n')
    result = []
    in_section = False
    indent_level = 0
    
    for line in lines:
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)
        
        if stripped.startswith(target) and not in_section:
            in_section = True
            indent_level = current_indent
            result.append(line)
        elif in_section:
            # Check if we've hit the next top-level hierarchy or end marker
            if current_indent == 0 and stripped and not stripped.startswith('!'):
                # New top-level section started - close current and stop
                break
            result.append(line)
            # If this is a closing '!' at the base level, we're done
            if stripped == '!' and current_indent == 0:
                break
    
    # Ensure the section ends with '!' for proper DNOS hierarchy closure
    if result and not result[-1].strip() == '!':
        result.append('!')
    
    return '\n'.join(result) if result else None


def get_lo0_ip_from_config(config_text: str) -> Optional[str]:
    """Extract lo0 IPv4 address from configuration text.
    
    Args:
        config_text: Device configuration text
        
    Returns:
        IPv4 address or None if not found
    """
    # Look for lo0 interface with ipv4-address
    lo0_pattern = re.compile(
        r'^\s*lo0\s*$.*?ipv4-address\s+(\d+\.\d+\.\d+\.\d+/?\d*)',
        re.MULTILINE | re.DOTALL
    )
    
    match = lo0_pattern.search(config_text)
    if match:
        return match.group(1)
    
    # Alternative pattern - simpler search
    lines = config_text.split('\n')
    in_lo0 = False
    for line in lines:
        stripped = line.strip()
        if stripped == 'lo0':
            in_lo0 = True
        elif in_lo0 and stripped.startswith('ipv4-address'):
            parts = stripped.split()
            if len(parts) >= 2:
                return parts[1]
        elif in_lo0 and stripped == '!' or (in_lo0 and stripped.startswith('lo') and stripped != 'lo0'):
            in_lo0 = False
    
    return None


def get_as_number_from_config(config_text: str) -> Optional[int]:
    """Extract BGP AS number from configuration text.
    
    Args:
        config_text: Device configuration text
        
    Returns:
        AS number as int or None if not found
    """
    # Look for "bgp <AS>" pattern
    bgp_pattern = re.compile(r'^\s*bgp\s+(\d+)\s*$', re.MULTILINE)
    match = bgp_pattern.search(config_text)
    if match:
        return int(match.group(1))
    
    return None


def get_router_id_from_config(config_text: str) -> Optional[str]:
    """Extract BGP router-id from configuration text.
    
    Args:
        config_text: Device configuration text
        
    Returns:
        Router ID or None if not found
    """
    # Look for "router-id X.X.X.X" pattern in BGP context
    rid_pattern = re.compile(r'router-id\s+(\d+\.\d+\.\d+\.\d+)', re.MULTILINE)
    match = rid_pattern.search(config_text)
    if match:
        return match.group(1)
    
    return None


def extract_lldp_section(config_text: str) -> str:
    """Extract LLDP configuration from protocols section.
    
    Args:
        config_text: Device configuration text
        
    Returns:
        LLDP configuration text or empty string
    """
    protocols_section = extract_hierarchy_section(config_text, 'protocols')
    if not protocols_section:
        return ''
    
    lines = protocols_section.split('\n')
    result = []
    in_lldp = False
    lldp_indent = 0
    
    for line in lines:
        stripped = line.strip()
        current_indent = len(line) - len(line.lstrip())
        
        if stripped == 'lldp':
            in_lldp = True
            lldp_indent = current_indent
            result.append(line)
            continue
        
        if in_lldp:
            if stripped and current_indent <= lldp_indent and stripped != '!':
                break
            result.append(line)
            if stripped == '!' and current_indent == lldp_indent:
                break
    
    return '\n'.join(result)


def extract_lacp_section(config_text: str) -> str:
    """Extract LACP configuration from protocols section.
    
    Args:
        config_text: Device configuration text
        
    Returns:
        LACP configuration text or empty string
    """
    protocols_section = extract_hierarchy_section(config_text, 'protocols')
    if not protocols_section:
        return ''
    
    lines = protocols_section.split('\n')
    result = []
    in_lacp = False
    lacp_indent = 0
    
    for line in lines:
        stripped = line.strip()
        current_indent = len(line) - len(line.lstrip())
        
        if stripped == 'lacp':
            in_lacp = True
            lacp_indent = current_indent
            result.append(line)
            continue
        
        if in_lacp:
            if stripped and current_indent <= lacp_indent and stripped != '!':
                break
            result.append(line)
            if stripped == '!' and current_indent == lacp_indent:
                break
    
    return '\n'.join(result)


def extract_bundle_interfaces(config_text: str) -> List[str]:
    """Extract all bundle interface configurations.
    
    Args:
        config_text: Device configuration text
        
    Returns:
        List of bundle interface configuration blocks
    """
    lines = config_text.split('\n')
    bundles = []
    current_bundle = []
    in_bundle = False
    in_interfaces = False
    
    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        
        if stripped == 'interfaces':
            in_interfaces = True
            continue
        
        if in_interfaces and indent == 0 and stripped and stripped != '!':
            in_interfaces = False
            continue
        
        if in_interfaces and indent == 2:
            if stripped.startswith('bundle'):
                if current_bundle:
                    bundles.append('\n'.join(current_bundle))
                current_bundle = [line]
                in_bundle = True
            elif in_bundle:
                bundles.append('\n'.join(current_bundle))
                current_bundle = []
                in_bundle = False
        elif in_bundle:
            current_bundle.append(line)
            if stripped == '!' and indent == 2:
                bundles.append('\n'.join(current_bundle))
                current_bundle = []
                in_bundle = False
    
    if current_bundle:
        bundles.append('\n'.join(current_bundle))
    
    return bundles


def extract_acls_section(config_text: str) -> str:
    """Extract access-lists configuration section.
    
    Args:
        config_text: Device configuration text
        
    Returns:
        Access-lists configuration text or empty string
    """
    return extract_hierarchy_section(config_text, 'access-lists') or ''


def extract_qos_section(config_text: str) -> str:
    """Extract QoS configuration section.
    
    Args:
        config_text: Device configuration text
        
    Returns:
        QoS configuration text or empty string
    """
    return extract_hierarchy_section(config_text, 'qos') or ''


def extract_routing_policy_section(config_text: str) -> str:
    """Extract routing-policy configuration section.
    
    Args:
        config_text: Device configuration text
        
    Returns:
        Routing-policy configuration text or empty string
    """
    return extract_hierarchy_section(config_text, 'routing-policy') or ''


def get_mpls_enabled_interfaces(config_text: str, include_subinterfaces: bool = True) -> List[str]:
    """Extract all interfaces with 'mpls enabled' from config.
    
    These are typically WAN/core interfaces that should participate in IGP.
    In DNOS, MPLS is enabled with "mpls enabled" on a single line under the interface.
    
    Args:
        config_text: Device configuration text
        include_subinterfaces: Whether to include sub-interfaces (default True for ISIS)
        
    Returns:
        List of interface names with MPLS enabled
    """
    mpls_interfaces = []
    lines = config_text.split('\n')
    
    current_interface = None
    in_interfaces_block = False
    has_mpls_enabled = False
    
    for line in lines:
        stripped = line.strip()
        raw_line = line
        
        # Track if we're in the interfaces block
        if stripped == 'interfaces':
            in_interfaces_block = True
            continue
        
        if not in_interfaces_block:
            continue
        
        # Calculate current indentation (spaces)
        current_indent = len(raw_line) - len(raw_line.lstrip())
        
        # End of interfaces block (top-level !)
        if stripped == '!' and current_indent == 0:
            # Save current interface if it has MPLS
            if current_interface and has_mpls_enabled:
                mpls_interfaces.append(current_interface)
            in_interfaces_block = False
            current_interface = None
            has_mpls_enabled = False
            continue
        
        # Check for interface definition (indented 2 spaces under 'interfaces')
        # Interface names start with: ge, xe, et, bundle, lo, ph, irb, etc.
        if current_indent == 2 and stripped and not stripped.startswith('!'):
            # If we were tracking an interface, save it if it had MPLS
            if current_interface and has_mpls_enabled:
                mpls_interfaces.append(current_interface)
            
            # Start tracking new interface
            current_interface = stripped
            has_mpls_enabled = False
            continue
        
        # Check for "mpls enabled" under current interface (indented 4 spaces)
        if current_interface and current_indent == 4:
            # DNOS uses "mpls enabled" as a single statement
            if stripped == 'mpls enabled':
                has_mpls_enabled = True
        
        # End of current interface block (! at indent 2)
        if current_interface and stripped == '!' and current_indent == 2:
            if has_mpls_enabled:
                mpls_interfaces.append(current_interface)
            current_interface = None
            has_mpls_enabled = False
    
    # Don't forget the last interface if we ended without seeing !
    if current_interface and has_mpls_enabled:
        mpls_interfaces.append(current_interface)
    
    # Optionally filter to only parent interfaces
    if not include_subinterfaces:
        mpls_interfaces = [iface for iface in mpls_interfaces if '.' not in iface]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_interfaces = []
    for iface in mpls_interfaces:
        if iface not in seen:
            seen.add(iface)
            unique_interfaces.append(iface)
    
    return unique_interfaces


def count_interfaces_in_config(config_text: str) -> Dict[str, int]:
    """
    Count different types of interfaces in a configuration.
    
    Args:
        config_text: Raw running config text
        
    Returns:
        Dict with counts: {'pwhe': N, 'l2ac': N, 'bundle': N, 'physical': N}
    """
    counts = {
        'pwhe': 0,
        'l2ac': 0,
        'bundle': 0,
        'physical': 0
    }
    
    # Pattern for interface lines (2-space indent, just the interface name)
    # DNOS format: "  ge100-0/0/0" or "  ph1001.1" etc.
    in_interfaces = False
    
    for line in config_text.split('\n'):
        stripped = line.strip()
        
        # Track interfaces section
        if stripped == 'interfaces':
            in_interfaces = True
            continue
        
        if not in_interfaces:
            continue
        
        # End of interfaces section
        if stripped == '!' and len(line) - len(line.lstrip()) == 0:
            in_interfaces = False
            continue
        
        # Interface line at 2-space indent
        if len(line) >= 2 and line[:2] == '  ' and len(line) > 2 and line[2] != ' ':
            iface_name = stripped
            
            # Skip closing !
            if iface_name == '!':
                continue
            
            # Classify interface
            if iface_name.startswith('ph'):
                # PWHE - count sub-interfaces (ph1001.1)
                if '.' in iface_name:
                    counts['pwhe'] += 1
            elif iface_name.startswith('Bundle'):
                counts['bundle'] += 1
            elif '.' in iface_name:
                # Sub-interface on physical port = L2-AC
                counts['l2ac'] += 1
            elif re.match(r'^(ge|xe|et|hu)\d+-', iface_name):
                counts['physical'] += 1
    
    return counts


# =============================================================================
# COMPREHENSIVE ROUTING POLICY PARSING
# =============================================================================

def parse_all_routing_policies(config_text: str) -> Dict[str, Any]:
    """
    Parse all routing-policy components from configuration.
    
    Extracts:
    - prefix-lists (IPv4 and IPv6)
    - community-lists
    - extcommunity-lists
    - large-community-lists
    - as-path-lists
    - policies with full rule details
    
    Args:
        config_text: Device configuration text
        
    Returns:
        Dict with keys:
        - prefix_lists_v4: List of parsed IPv4 prefix-lists
        - prefix_lists_v6: List of parsed IPv6 prefix-lists
        - community_lists: List of parsed community-lists
        - extcommunity_lists: List of parsed extcommunity-lists
        - large_community_lists: List of parsed large-community-lists
        - as_path_lists: List of parsed as-path-lists
        - policies: List of parsed policies with rules
    """
    result = {
        'prefix_lists_v4': [],
        'prefix_lists_v6': [],
        'community_lists': [],
        'extcommunity_lists': [],
        'large_community_lists': [],
        'as_path_lists': [],
        'policies': []
    }
    
    # Extract routing-policy section
    rp_section = extract_routing_policy_section(config_text)
    if not rp_section:
        return result
    
    lines = rp_section.split('\n')
    
    # State machine for parsing
    current_block = None  # 'prefix-list', 'community-list', etc.
    current_name = None
    current_ip_version = None
    current_rules = []
    current_policy_rules = []
    current_rule = None  # For policy rules
    current_description = None
    
    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        
        # Skip empty lines and the top-level routing-policy
        if not stripped or stripped == 'routing-policy':
            continue
        
        # Top-level block detection (2-space indent)
        if indent == 2:
            # Save previous block
            if current_block and current_name:
                _save_parsed_block(result, current_block, current_name, 
                                   current_ip_version, current_rules, 
                                   current_policy_rules, current_description)
            
            # Reset state
            current_rules = []
            current_policy_rules = []
            current_rule = None
            current_description = None
            
            # Detect block type
            if stripped.startswith('prefix-list ipv4 '):
                current_block = 'prefix-list'
                current_ip_version = 'ipv4'
                current_name = stripped.replace('prefix-list ipv4 ', '').strip()
            elif stripped.startswith('prefix-list ipv6 '):
                current_block = 'prefix-list'
                current_ip_version = 'ipv6'
                current_name = stripped.replace('prefix-list ipv6 ', '').strip()
            elif stripped.startswith('community-list '):
                current_block = 'community-list'
                current_name = stripped.replace('community-list ', '').strip()
                current_ip_version = None
            elif stripped.startswith('extcommunity-list '):
                current_block = 'extcommunity-list'
                current_name = stripped.replace('extcommunity-list ', '').strip()
                current_ip_version = None
            elif stripped.startswith('large-community-list '):
                current_block = 'large-community-list'
                current_name = stripped.replace('large-community-list ', '').strip()
                current_ip_version = None
            elif stripped.startswith('as-path-list '):
                current_block = 'as-path-list'
                current_name = stripped.replace('as-path-list ', '').strip()
                current_ip_version = None
            elif stripped.startswith('policy '):
                current_block = 'policy'
                current_name = stripped.replace('policy ', '').strip()
                current_ip_version = None
            elif stripped == '!':
                current_block = None
                current_name = None
            else:
                current_block = None
                current_name = None
            continue
        
        # Parse content within blocks
        if current_block and current_name:
            if stripped.startswith('description '):
                current_description = stripped.replace('description ', '').strip()
            elif stripped == '!' and indent == 4 and current_block == 'policy':
                # End of policy rule - MUST check before other elif to avoid being caught
                if current_rule:
                    current_policy_rules.append(current_rule)
                    current_rule = None
            elif stripped.startswith('rule '):
                parsed_rule = _parse_rule_line(stripped, current_block)
                if parsed_rule:
                    if current_block == 'policy':
                        # Save previous policy rule if exists
                        if current_rule:
                            current_policy_rules.append(current_rule)
                        current_rule = parsed_rule
                    else:
                        current_rules.append(parsed_rule)
            elif current_block == 'policy' and current_rule:
                # Parse policy rule internals (match/set/on-match/call)
                _parse_policy_rule_content(current_rule, stripped)
    
    # Save the last block
    if current_block and current_name:
        _save_parsed_block(result, current_block, current_name,
                           current_ip_version, current_rules,
                           current_policy_rules, current_description)
    
    return result


def _save_parsed_block(result: Dict, block_type: str, name: str, 
                       ip_version: str, rules: List, 
                       policy_rules: List, description: str) -> None:
    """Save a parsed block to the result dict."""
    if block_type == 'prefix-list':
        entry = {
            'name': name,
            'ip_version': ip_version,
            'rules': rules,
            'description': description
        }
        if ip_version == 'ipv4':
            result['prefix_lists_v4'].append(entry)
        else:
            result['prefix_lists_v6'].append(entry)
    elif block_type == 'community-list':
        result['community_lists'].append({
            'name': name,
            'rules': rules,
            'description': description
        })
    elif block_type == 'extcommunity-list':
        result['extcommunity_lists'].append({
            'name': name,
            'rules': rules,
            'description': description
        })
    elif block_type == 'large-community-list':
        result['large_community_lists'].append({
            'name': name,
            'rules': rules,
            'description': description
        })
    elif block_type == 'as-path-list':
        result['as_path_lists'].append({
            'name': name,
            'rules': rules,
            'description': description
        })
    elif block_type == 'policy':
        result['policies'].append({
            'name': name,
            'rules': policy_rules,
            'description': description
        })


def _parse_rule_line(line: str, block_type: str) -> Optional[Dict]:
    """Parse a rule line based on block type."""
    # Common pattern: rule <id> <allow|deny> ...
    match = re.match(r'rule\s+(\d+)\s+(allow|deny)\s*(.*)', line)
    if not match:
        return None
    
    rule_id = int(match.group(1))
    action = match.group(2)
    rest = match.group(3).strip()
    
    if block_type == 'prefix-list':
        # Format: rule 10 allow 10.0.0.0/8 [matching-len ge X [le Y] | eq Z]
        prefix_match = re.match(r'(\S+/\d+)\s*(.*)', rest)
        if prefix_match:
            prefix = prefix_match.group(1)
            matching = prefix_match.group(2)
            ge, le, eq = None, None, None
            
            if 'matching-len' in matching:
                ge_match = re.search(r'ge\s+(\d+)', matching)
                le_match = re.search(r'le\s+(\d+)', matching)
                eq_match = re.search(r'eq\s+(\d+)', matching)
                if ge_match:
                    ge = int(ge_match.group(1))
                if le_match:
                    le = int(le_match.group(1))
                if eq_match:
                    eq = int(eq_match.group(1))
            
            return {
                'rule_id': rule_id,
                'action': action,
                'prefix': prefix,
                'ge': ge,
                'le': le,
                'eq': eq
            }
    
    elif block_type == 'community-list':
        # Formats: value X:Y, well-known-community <name>, regex <pattern>
        if rest.startswith('value '):
            return {
                'rule_id': rule_id,
                'action': action,
                'match_type': 'value',
                'value': rest.replace('value ', '').strip()
            }
        elif rest.startswith('well-known-community '):
            return {
                'rule_id': rule_id,
                'action': action,
                'match_type': 'well-known',
                'value': rest.replace('well-known-community ', '').strip()
            }
        elif rest.startswith('regex '):
            return {
                'rule_id': rule_id,
                'action': action,
                'match_type': 'regex',
                'value': rest.replace('regex ', '').strip()
            }
    
    elif block_type == 'extcommunity-list':
        # Formats: rt value X:Y, soo value X:Y, rt regex <pattern>
        if 'rt value ' in rest:
            return {
                'rule_id': rule_id,
                'action': action,
                'ext_type': 'rt',
                'match_type': 'value',
                'value': rest.replace('rt value ', '').strip()
            }
        elif 'soo value ' in rest:
            return {
                'rule_id': rule_id,
                'action': action,
                'ext_type': 'soo',
                'match_type': 'value',
                'value': rest.replace('soo value ', '').strip()
            }
        elif 'rt regex ' in rest:
            return {
                'rule_id': rule_id,
                'action': action,
                'ext_type': 'rt',
                'match_type': 'regex',
                'value': rest.replace('rt regex ', '').strip()
            }
        elif 'soo regex ' in rest:
            return {
                'rule_id': rule_id,
                'action': action,
                'ext_type': 'soo',
                'match_type': 'regex',
                'value': rest.replace('soo regex ', '').strip()
            }
    
    elif block_type == 'large-community-list':
        # Formats: value X:Y:Z, regex <pattern>
        if rest.startswith('value '):
            return {
                'rule_id': rule_id,
                'action': action,
                'match_type': 'value',
                'value': rest.replace('value ', '').strip()
            }
        elif rest.startswith('regex '):
            return {
                'rule_id': rule_id,
                'action': action,
                'match_type': 'regex',
                'value': rest.replace('regex ', '').strip()
            }
    
    elif block_type == 'as-path-list':
        # Formats: regex <pattern>, passes-through <asn>
        if rest.startswith('regex '):
            return {
                'rule_id': rule_id,
                'action': action,
                'match_type': 'regex',
                'value': rest.replace('regex ', '').strip()
            }
        elif rest.startswith('passes-through '):
            return {
                'rule_id': rule_id,
                'action': action,
                'match_type': 'passes-through',
                'value': rest.replace('passes-through ', '').strip()
            }
    
    elif block_type == 'policy':
        # Policy rule starts with just "rule <id> <allow|deny>"
        # Match conditions and set actions are on subsequent lines
        return {
            'rule_id': rule_id,
            'action': action,
            'match_conditions': [],
            'set_actions': [],
            'on_match': None,
            'on_match_goto_rule': None,
            'call_policy': None,
            'description': None
        }
    
    return None


def _parse_policy_rule_content(rule: Dict, line: str) -> None:
    """Parse content within a policy rule (match/set/on-match/call)."""
    if line.startswith('description '):
        rule['description'] = line.replace('description ', '').strip()
    
    elif line.startswith('match '):
        match_content = line.replace('match ', '').strip()
        match_entry = _parse_match_condition(match_content)
        if match_entry:
            rule['match_conditions'].append(match_entry)
    
    elif line.startswith('set '):
        set_content = line.replace('set ', '').strip()
        set_entry = _parse_set_action(set_content)
        if set_entry:
            rule['set_actions'].append(set_entry)
    
    elif line.startswith('on-match '):
        on_match = line.replace('on-match ', '').strip()
        if on_match == 'next':
            rule['on_match'] = 'next'
        elif on_match == 'next-policy':
            rule['on_match'] = 'next-policy'
        elif on_match.startswith('goto '):
            rule['on_match'] = 'goto'
            try:
                rule['on_match_goto_rule'] = int(on_match.replace('goto ', '').strip())
            except ValueError:
                pass
    
    elif line.startswith('call '):
        rule['call_policy'] = line.replace('call ', '').strip()


def _parse_match_condition(content: str) -> Optional[Dict]:
    """Parse a match condition line content."""
    if content.startswith('ipv4 prefix '):
        return {'type': 'ipv4-prefix', 'value': content.replace('ipv4 prefix ', '').strip()}
    elif content.startswith('ipv6 prefix '):
        return {'type': 'ipv6-prefix', 'value': content.replace('ipv6 prefix ', '').strip()}
    elif content.startswith('as-path-length '):
        return {'type': 'as-path-length', 'value': content.replace('as-path-length ', '').strip()}
    elif content.startswith('as-path '):
        return {'type': 'as-path', 'value': content.replace('as-path ', '').strip()}
    elif content.startswith('community '):
        return {'type': 'community', 'value': content.replace('community ', '').strip()}
    elif content.startswith('extcommunity '):
        return {'type': 'extcommunity', 'value': content.replace('extcommunity ', '').strip()}
    elif content.startswith('large-community '):
        return {'type': 'large-community', 'value': content.replace('large-community ', '').strip()}
    elif content.startswith('med '):
        return {'type': 'med', 'value': content.replace('med ', '').strip()}
    elif content.startswith('tag '):
        return {'type': 'tag', 'value': content.replace('tag ', '').strip()}
    elif content.startswith('ipv4 next-hop prefix-list '):
        return {'type': 'ipv4-next-hop', 'value': content.replace('ipv4 next-hop prefix-list ', '').strip()}
    elif content.startswith('ipv6 next-hop prefix-list '):
        return {'type': 'ipv6-next-hop', 'value': content.replace('ipv6 next-hop prefix-list ', '').strip()}
    elif content.startswith('path-type '):
        return {'type': 'path-type', 'value': content.replace('path-type ', '').strip()}
    elif content.startswith('rpki '):
        return {'type': 'rpki', 'value': content.replace('rpki ', '').strip()}
    elif content.startswith('rib-has-route '):
        return {'type': 'rib-has-route', 'value': content.replace('rib-has-route ', '').strip()}
    elif content.startswith('path-mark-count '):
        return {'type': 'path-mark-count', 'value': content.replace('path-mark-count ', '').strip()}
    return None


def _parse_set_action(content: str) -> Optional[Dict]:
    """Parse a set action line content."""
    if content.startswith('local-preference '):
        return {'type': 'local-preference', 'value': content.replace('local-preference ', '').strip()}
    elif content.startswith('med '):
        return {'type': 'med', 'value': content.replace('med ', '').strip()}
    elif content.startswith('community-list '):
        # community-list <name> <operation>
        parts = content.replace('community-list ', '').strip().split()
        if len(parts) >= 2:
            return {'type': 'community-list', 'value': parts[0], 'operation': parts[1]}
    elif content.startswith('community '):
        # community <value> or community additive <value> or community none
        rest = content.replace('community ', '').strip()
        if rest == 'none':
            return {'type': 'community', 'value': 'none', 'extra': 'none'}
        elif rest.startswith('additive '):
            return {'type': 'community', 'value': rest.replace('additive ', '').strip(), 'extra': 'additive'}
        else:
            return {'type': 'community', 'value': rest}
    elif content.startswith('extcommunity-list '):
        parts = content.replace('extcommunity-list ', '').strip().split()
        if len(parts) >= 2:
            return {'type': 'extcommunity-list', 'value': parts[0], 'operation': parts[1]}
    elif content.startswith('extcommunity route-target '):
        rest = content.replace('extcommunity route-target ', '').strip()
        if rest.startswith('additive '):
            return {'type': 'extcommunity-rt', 'value': rest.replace('additive ', '').strip(), 'extra': 'additive'}
        else:
            return {'type': 'extcommunity-rt', 'value': rest}
    elif content.startswith('extcommunity soo '):
        return {'type': 'extcommunity-soo', 'value': content.replace('extcommunity soo ', '').strip()}
    elif content.startswith('extcommunity color '):
        return {'type': 'extcommunity-color', 'value': content.replace('extcommunity color ', '').strip()}
    elif content.startswith('large-community-list '):
        parts = content.replace('large-community-list ', '').strip().split()
        if len(parts) >= 2:
            return {'type': 'large-community-list', 'value': parts[0], 'operation': parts[1]}
    elif content.startswith('large-community '):
        rest = content.replace('large-community ', '').strip()
        if rest == 'none':
            return {'type': 'large-community', 'value': 'none', 'extra': 'none'}
        elif rest.startswith('additive '):
            return {'type': 'large-community', 'value': rest.replace('additive ', '').strip(), 'extra': 'additive'}
        else:
            return {'type': 'large-community', 'value': rest}
    elif content.startswith('as-path prepend '):
        rest = content.replace('as-path prepend ', '').strip()
        if rest.startswith('last-as '):
            return {'type': 'as-path-prepend', 'value': rest.replace('last-as ', '').strip(), 'extra': 'last-as'}
        elif rest.startswith('as-number '):
            return {'type': 'as-path-prepend', 'value': rest.replace('as-number ', '').strip()}
        else:
            return {'type': 'as-path-prepend', 'value': rest}
    elif content.startswith('as-path exclude '):
        return {'type': 'as-path-exclude', 'value': content.replace('as-path exclude ', '').strip()}
    elif content.startswith('ipv4 next-hop '):
        return {'type': 'ipv4-next-hop', 'value': content.replace('ipv4 next-hop ', '').strip()}
    elif content.startswith('ipv6 next-hop '):
        return {'type': 'ipv6-next-hop', 'value': content.replace('ipv6 next-hop ', '').strip()}
    elif content.startswith('weight '):
        return {'type': 'weight', 'value': content.replace('weight ', '').strip()}
    elif content == 'atomic-aggregate':
        return {'type': 'atomic-aggregate', 'value': 'true'}
    elif content.startswith('tag '):
        return {'type': 'tag', 'value': content.replace('tag ', '').strip()}
    elif content.startswith('ospf-metric '):
        return {'type': 'ospf-metric', 'value': content.replace('ospf-metric ', '').strip()}
    elif content.startswith('isis-metric '):
        return {'type': 'isis-metric', 'value': content.replace('isis-metric ', '').strip()}
    elif content.startswith('metric-type '):
        return {'type': 'metric-type', 'value': content.replace('metric-type ', '').strip()}
    elif content.startswith('aigp '):
        return {'type': 'aigp', 'value': content.replace('aigp ', '').strip()}
    elif content.startswith('path-mark '):
        return {'type': 'path-mark', 'value': content.replace('path-mark ', '').strip()}
    elif content.startswith('forwarding-action '):
        return {'type': 'forwarding-action', 'value': content.replace('forwarding-action ', '').strip()}
    return None


def load_policies_from_config(config_text: str) -> 'PolicyManager':
    """
    Load policies from config text into a PolicyManager instance.
    
    Args:
        config_text: Device configuration text
        
    Returns:
        PolicyManager populated with parsed policies
    """
    from .policies import (
        PolicyManager, PrefixList, PrefixListRule, CommunityList, CommunityListRule,
        ExtCommunityList, ExtCommunityListRule, LargeCommunityList, LargeCommunityListRule,
        AsPathList, AsPathListRule, RoutingPolicy, PolicyRule, MatchCondition, SetAction,
        RuleAction, MatchType, SetActionType, OnMatchAction
    )
    
    parsed = parse_all_routing_policies(config_text)
    manager = PolicyManager()
    
    # Load prefix-lists (IPv4)
    for pl_data in parsed['prefix_lists_v4']:
        rules = []
        for r in pl_data.get('rules', []):
            rules.append(PrefixListRule(
                rule_id=r['rule_id'],
                action=RuleAction(r['action']),
                prefix=r['prefix'],
                ge=r.get('ge'),
                le=r.get('le'),
                eq=r.get('eq')
            ))
        manager.add_prefix_list(PrefixList(
            name=pl_data['name'],
            ip_version='ipv4',
            rules=rules,
            description=pl_data.get('description')
        ))
    
    # Load prefix-lists (IPv6)
    for pl_data in parsed['prefix_lists_v6']:
        rules = []
        for r in pl_data.get('rules', []):
            rules.append(PrefixListRule(
                rule_id=r['rule_id'],
                action=RuleAction(r['action']),
                prefix=r['prefix'],
                ge=r.get('ge'),
                le=r.get('le'),
                eq=r.get('eq')
            ))
        manager.add_prefix_list(PrefixList(
            name=pl_data['name'],
            ip_version='ipv6',
            rules=rules,
            description=pl_data.get('description')
        ))
    
    # Load community-lists
    for cl_data in parsed['community_lists']:
        rules = []
        for r in cl_data.get('rules', []):
            rules.append(CommunityListRule(
                rule_id=r['rule_id'],
                action=RuleAction(r['action']),
                match_type=r['match_type'],
                value=r['value']
            ))
        manager.add_community_list(CommunityList(
            name=cl_data['name'],
            rules=rules,
            description=cl_data.get('description')
        ))
    
    # Load extcommunity-lists
    for ecl_data in parsed['extcommunity_lists']:
        rules = []
        for r in ecl_data.get('rules', []):
            rules.append(ExtCommunityListRule(
                rule_id=r['rule_id'],
                action=RuleAction(r['action']),
                ext_type=r['ext_type'],
                match_type=r['match_type'],
                value=r['value']
            ))
        manager.add_extcommunity_list(ExtCommunityList(
            name=ecl_data['name'],
            rules=rules,
            description=ecl_data.get('description')
        ))
    
    # Load large-community-lists
    for lcl_data in parsed['large_community_lists']:
        rules = []
        for r in lcl_data.get('rules', []):
            rules.append(LargeCommunityListRule(
                rule_id=r['rule_id'],
                action=RuleAction(r['action']),
                match_type=r['match_type'],
                value=r['value']
            ))
        manager.add_large_community_list(LargeCommunityList(
            name=lcl_data['name'],
            rules=rules,
            description=lcl_data.get('description')
        ))
    
    # Load as-path-lists
    for apl_data in parsed['as_path_lists']:
        rules = []
        for r in apl_data.get('rules', []):
            rules.append(AsPathListRule(
                rule_id=r['rule_id'],
                action=RuleAction(r['action']),
                match_type=r['match_type'],
                value=r['value']
            ))
        manager.add_as_path_list(AsPathList(
            name=apl_data['name'],
            rules=rules,
            description=apl_data.get('description')
        ))
    
    # Load policies
    for pol_data in parsed['policies']:
        policy_rules = []
        for r in pol_data.get('rules', []):
            # Convert match conditions
            match_conditions = []
            for m in r.get('match_conditions', []):
                match_type_map = {
                    'ipv4-prefix': MatchType.IPV4_PREFIX,
                    'ipv6-prefix': MatchType.IPV6_PREFIX,
                    'as-path': MatchType.AS_PATH,
                    'as-path-length': MatchType.AS_PATH_LENGTH,
                    'community': MatchType.COMMUNITY,
                    'extcommunity': MatchType.EXTCOMMUNITY,
                    'large-community': MatchType.LARGE_COMMUNITY,
                    'med': MatchType.MED,
                    'tag': MatchType.TAG,
                    'ipv4-next-hop': MatchType.IPV4_NEXT_HOP,
                    'ipv6-next-hop': MatchType.IPV6_NEXT_HOP,
                    'path-type': MatchType.PATH_TYPE,
                    'rpki': MatchType.RPKI,
                    'rib-has-route': MatchType.RIB_HAS_ROUTE,
                    'path-mark-count': MatchType.PATH_MARK_COUNT
                }
                if m['type'] in match_type_map:
                    match_conditions.append(MatchCondition(
                        match_type=match_type_map[m['type']],
                        value=m['value']
                    ))
            
            # Convert set actions
            set_actions = []
            for s in r.get('set_actions', []):
                set_type_map = {
                    'local-preference': SetActionType.LOCAL_PREFERENCE,
                    'med': SetActionType.MED,
                    'community': SetActionType.COMMUNITY,
                    'community-list': SetActionType.COMMUNITY_LIST,
                    'extcommunity-rt': SetActionType.EXTCOMMUNITY_RT,
                    'extcommunity-soo': SetActionType.EXTCOMMUNITY_SOO,
                    'extcommunity-color': SetActionType.EXTCOMMUNITY_COLOR,
                    'extcommunity-list': SetActionType.EXTCOMMUNITY_LIST,
                    'large-community': SetActionType.LARGE_COMMUNITY,
                    'large-community-list': SetActionType.LARGE_COMMUNITY_LIST,
                    'as-path-prepend': SetActionType.AS_PATH_PREPEND,
                    'as-path-exclude': SetActionType.AS_PATH_EXCLUDE,
                    'ipv4-next-hop': SetActionType.IPV4_NEXT_HOP,
                    'ipv6-next-hop': SetActionType.IPV6_NEXT_HOP,
                    'weight': SetActionType.WEIGHT,
                    'atomic-aggregate': SetActionType.ATOMIC_AGGREGATE,
                    'tag': SetActionType.TAG,
                    'ospf-metric': SetActionType.OSPF_METRIC,
                    'isis-metric': SetActionType.ISIS_METRIC,
                    'metric-type': SetActionType.METRIC_TYPE,
                    'aigp': SetActionType.AIGP,
                    'path-mark': SetActionType.PATH_MARK,
                    'forwarding-action': SetActionType.FORWARDING_ACTION
                }
                if s['type'] in set_type_map:
                    set_actions.append(SetAction(
                        action_type=set_type_map[s['type']],
                        value=s['value'],
                        extra=s.get('extra') or s.get('operation')
                    ))
            
            # Convert on-match
            on_match = None
            on_match_goto = None
            if r.get('on_match') == 'next':
                on_match = OnMatchAction.NEXT
            elif r.get('on_match') == 'next-policy':
                on_match = OnMatchAction.NEXT_POLICY
            elif r.get('on_match') == 'goto':
                on_match = OnMatchAction.GOTO
                on_match_goto = r.get('on_match_goto_rule')
            
            policy_rules.append(PolicyRule(
                rule_id=r['rule_id'],
                action=RuleAction(r['action']),
                match_conditions=match_conditions,
                set_actions=set_actions,
                on_match=on_match,
                on_match_goto_rule=on_match_goto,
                call_policy=r.get('call_policy'),
                description=r.get('description')
            ))
        
        manager.add_policy(RoutingPolicy(
            name=pol_data['name'],
            rules=policy_rules,
            description=pol_data.get('description')
        ))
    
    return manager


# =============================================================================
# VRF AND ADVANCED SERVICE PARSING (for granular mirror config)
# =============================================================================

def parse_vrf_instances(config_text: str) -> List[Dict[str, Any]]:
    """
    Parse VRF instances from network-services section.
    
    DNOS VRF structure:
    network-services
      vrf
        instance VRF-1
          description "..."
          interface ge100-18/0/0.219
          protocols
            bgp <ASN>
              route-distinguisher X.X.X.X:N
              router-id X.X.X.X
              address-family ipv4-unicast
                export-vpn route-target ASN:N
                import-vpn route-target ASN:N
              address-family ipv4-flowspec
                import-vpn route-target ASN:N
              neighbor X.X.X.X
                remote-as NNNNN
                update-source <interface>
    
    Returns:
        List of VRF dicts with structure:
        [{
            'name': 'VRF-1',
            'description': 'L3VPN customer 1',
            'interfaces': ['ge100-18/0/0.219'],
            'rd': '4.4.4.4:100',
            'router_id': '4.4.4.4',
            'asn': 1234567,
            'rt_import': {'ipv4-unicast': ['1234567:100'], 'ipv6-unicast': ['1234567:200']},
            'rt_export': {'ipv4-unicast': ['1234567:100'], 'ipv6-unicast': ['1234567:200']},
            'flowspec': {'ipv4': ['1234567:300'], 'ipv6': ['1234567:400']},
            'bgp_neighbors': [{'ip': '49.49.49.9', 'remote_as': 65100, 'update_source': 'ge100-18/0/0.219'}]
        }]
    """
    vrfs = []
    
    # Find the VRF section under network-services
    vrf_start = config_text.find('\n  vrf\n')
    if vrf_start == -1:
        # Try alternative pattern
        vrf_start = config_text.find('network-services\n  vrf')
        if vrf_start != -1:
            vrf_start = config_text.find('\n  vrf', vrf_start)
    
    if vrf_start == -1:
        return vrfs
    
    # Find the end of VRF section (next sibling at 2-space indent or closing !)
    vrf_section_start = vrf_start + len('\n  vrf\n')
    
    # Look for next sibling section or end of network-services
    end_markers = ['\n  evpn-vpws-fxc', '\n  evpn-vpws', '\n  evpn-vpls', '\n  evpn-mpls', 
                   '\n  evpn', '\n  multihoming', '\n  !\n!']
    vrf_end = len(config_text)
    for marker in end_markers:
        pos = config_text.find(marker, vrf_section_start)
        if pos != -1 and pos < vrf_end:
            vrf_end = pos
    
    vrf_section = config_text[vrf_section_start:vrf_end]
    
    # Parse each VRF instance
    instance_pattern = re.compile(r'^\s{4}instance\s+(\S+)\s*$', re.MULTILINE)
    
    for match in instance_pattern.finditer(vrf_section):
        vrf_name = match.group(1)
        instance_start = match.end()
        
        # Find end of this instance (next instance or closing !)
        next_instance = instance_pattern.search(vrf_section, instance_start)
        if next_instance:
            instance_end = next_instance.start()
        else:
            instance_end = len(vrf_section)
        
        instance_block = vrf_section[instance_start:instance_end]
        
        vrf_data = {
            'name': vrf_name,
            'description': '',
            'interfaces': [],
            'rd': None,
            'router_id': None,
            'asn': None,
            'rt_import': {},
            'rt_export': {},
            'flowspec': {'ipv4': [], 'ipv6': []},
            'bgp_neighbors': []
        }
        
        # Parse description
        desc_match = re.search(r'description\s+"([^"]*)"', instance_block)
        if desc_match:
            vrf_data['description'] = desc_match.group(1)
        
        # Parse interfaces (6-space indent)
        iface_pattern = re.compile(r'^\s{6}interface\s+(\S+)\s*$', re.MULTILINE)
        for iface_match in iface_pattern.finditer(instance_block):
            vrf_data['interfaces'].append(iface_match.group(1))
        
        # Parse BGP section
        bgp_match = re.search(r'bgp\s+(\d+)', instance_block)
        if bgp_match:
            vrf_data['asn'] = int(bgp_match.group(1))
        
        # Parse RD
        rd_match = re.search(r'route-distinguisher\s+(\S+)', instance_block)
        if rd_match:
            vrf_data['rd'] = rd_match.group(1)
        
        # Parse router-id
        rid_match = re.search(r'router-id\s+(\d+\.\d+\.\d+\.\d+)', instance_block)
        if rid_match:
            vrf_data['router_id'] = rid_match.group(1)
        
        # Parse address-families and their RTs
        # IPv4/IPv6 unicast
        for af in ['ipv4-unicast', 'ipv6-unicast']:
            af_pattern = re.compile(
                rf'address-family\s+{af}\s*\n(.*?)(?=address-family|\s*!\s*\n\s*neighbor|\s*!\s*\n\s*!\s*\n)',
                re.DOTALL
            )
            af_match = af_pattern.search(instance_block)
            if af_match:
                af_block = af_match.group(1)
                
                # Export RT
                export_rts = re.findall(r'export-vpn\s+route-target\s+(\S+)', af_block)
                if export_rts:
                    vrf_data['rt_export'][af] = export_rts
                
                # Import RT
                import_rts = re.findall(r'import-vpn\s+route-target\s+(\S+)', af_block)
                if import_rts:
                    vrf_data['rt_import'][af] = import_rts
        
        # Parse flowspec address-families
        for fs_af, fs_key in [('ipv4-flowspec', 'ipv4'), ('ipv6-flowspec', 'ipv6')]:
            fs_pattern = re.compile(
                rf'address-family\s+{fs_af}\s*\n(.*?)(?=address-family|\s*!\s*\n)',
                re.DOTALL
            )
            fs_match = fs_pattern.search(instance_block)
            if fs_match:
                fs_block = fs_match.group(1)
                import_rts = re.findall(r'import-vpn\s+route-target\s+(\S+)', fs_block)
                vrf_data['flowspec'][fs_key] = import_rts
        
        # Parse BGP neighbors
        neighbor_pattern = re.compile(
            r'neighbor\s+(\S+)\s*\n(.*?)(?=neighbor\s+\S+\s*\n|!\s*\n\s*!\s*\n)',
            re.DOTALL
        )
        for nbr_match in neighbor_pattern.finditer(instance_block):
            nbr_ip = nbr_match.group(1)
            nbr_block = nbr_match.group(2)
            
            neighbor = {
                'ip': nbr_ip,
                'remote_as': None,
                'update_source': None,
                'description': None,
                'address_families': []
            }
            
            # Remote AS
            ras_match = re.search(r'remote-as\s+(\d+)', nbr_block)
            if ras_match:
                neighbor['remote_as'] = int(ras_match.group(1))
            
            # Update source
            us_match = re.search(r'update-source\s+(\S+)', nbr_block)
            if us_match:
                neighbor['update_source'] = us_match.group(1)
            
            # Description
            desc_match = re.search(r'description\s+(\S+)', nbr_block)
            if desc_match:
                neighbor['description'] = desc_match.group(1)
            
            # Address families
            afs = re.findall(r'address-family\s+([\w-]+)', nbr_block)
            neighbor['address_families'] = afs
            
            vrf_data['bgp_neighbors'].append(neighbor)
        
        vrfs.append(vrf_data)
    
    return vrfs


def parse_evpn_vpws_instances(config_text: str) -> List[Dict[str, Any]]:
    """
    Parse EVPN-VPWS instances from network-services section.
    
    DNOS structure:
    network-services
      evpn-vpws
        instance VPWS_1
          protocols
            bgp <ASN>
              export-l2vpn-evpn route-target ASN:N
              import-l2vpn-evpn route-target ASN:N
              route-distinguisher X.X.X.X:N
          transport-protocol
            mpls
              control-word enabled|disabled
              fat-label enabled|disabled
          admin-state enabled
          interface <name>
          vpws-service-id <N>
    
    Returns:
        List of EVPN-VPWS dicts
    """
    services = []
    
    # Find evpn-vpws section (not evpn-vpws-fxc)
    vpws_start = config_text.find('\n  evpn-vpws\n')
    if vpws_start == -1:
        return services
    
    vpws_section_start = vpws_start + len('\n  evpn-vpws\n')
    
    # Find end of section
    end_markers = ['\n  evpn-vpws-fxc', '\n  evpn-vpls', '\n  evpn-mpls', 
                   '\n  evpn', '\n  vrf', '\n  multihoming', '\n  !\n!']
    vpws_end = len(config_text)
    for marker in end_markers:
        pos = config_text.find(marker, vpws_section_start)
        if pos != -1 and pos < vpws_end:
            vpws_end = pos
    
    vpws_section = config_text[vpws_section_start:vpws_end]
    
    # Parse instances
    instance_pattern = re.compile(r'^\s{4}instance\s+(\S+)\s*$', re.MULTILINE)
    
    for match in instance_pattern.finditer(vpws_section):
        svc_name = match.group(1)
        instance_start = match.end()
        
        next_instance = instance_pattern.search(vpws_section, instance_start)
        instance_end = next_instance.start() if next_instance else len(vpws_section)
        
        instance_block = vpws_section[instance_start:instance_end]
        
        svc_data = {
            'name': svc_name,
            'interfaces': [],
            'rd': None,
            'rt_export': [],
            'rt_import': [],
            'vpws_service_id': None,
            'transport': 'mpls',
            'control_word': True,
            'fat_label': False,
            'admin_state': 'enabled'
        }
        
        # Parse interfaces
        iface_matches = re.findall(r'^\s+interface\s+(\S+)\s*$', instance_block, re.MULTILINE)
        svc_data['interfaces'] = [i for i in iface_matches if i != '!']
        
        # Parse RD
        rd_match = re.search(r'route-distinguisher\s+(\S+)', instance_block)
        if rd_match:
            svc_data['rd'] = rd_match.group(1)
        
        # Parse RTs
        export_rts = re.findall(r'export-l2vpn-evpn\s+route-target\s+(\S+)', instance_block)
        import_rts = re.findall(r'import-l2vpn-evpn\s+route-target\s+(\S+)', instance_block)
        svc_data['rt_export'] = export_rts
        svc_data['rt_import'] = import_rts
        
        # Parse vpws-service-id
        vsid_match = re.search(r'vpws-service-id\s+(\d+)', instance_block)
        if vsid_match:
            svc_data['vpws_service_id'] = int(vsid_match.group(1))
        
        # Parse transport options
        if 'srv6' in instance_block.lower():
            svc_data['transport'] = 'srv6'
        
        if 'control-word disabled' in instance_block:
            svc_data['control_word'] = False
        if 'fat-label enabled' in instance_block:
            svc_data['fat_label'] = True
        
        if 'admin-state disabled' in instance_block:
            svc_data['admin_state'] = 'disabled'
        
        services.append(svc_data)
    
    return services


def parse_l2vpn_xconnect(config_text: str) -> List[Dict[str, Any]]:
    """
    Parse L2VPN xconnect groups from configuration.
    
    DNOS structure:
    l2vpn
      xconnect group <name>
        p2p <name>
          interface <name>
          neighbor evpn evi <N> target <N>
    
    Returns:
        List of xconnect dicts
    """
    xconnects = []
    
    l2vpn_start = config_text.find('\nl2vpn\n')
    if l2vpn_start == -1:
        return xconnects
    
    # Find xconnect group sections
    xc_pattern = re.compile(r'xconnect\s+group\s+(\S+)\s*\n(.*?)(?=xconnect\s+group|\n!\n!)', re.DOTALL)
    
    for xc_match in xc_pattern.finditer(config_text[l2vpn_start:]):
        group_name = xc_match.group(1)
        group_block = xc_match.group(2)
        
        # Parse p2p connections
        p2p_pattern = re.compile(r'p2p\s+(\S+)\s*\n(.*?)(?=p2p\s+|\n\s*!)', re.DOTALL)
        
        for p2p_match in p2p_pattern.finditer(group_block):
            p2p_name = p2p_match.group(1)
            p2p_block = p2p_match.group(2)
            
            xc_data = {
                'group': group_name,
                'p2p_name': p2p_name,
                'interfaces': [],
                'evi': None,
                'target': None
            }
            
            # Parse interfaces
            iface_matches = re.findall(r'interface\s+(\S+)', p2p_block)
            xc_data['interfaces'] = iface_matches
            
            # Parse neighbor evpn
            evpn_match = re.search(r'neighbor\s+evpn\s+evi\s+(\d+)\s+target\s+(\d+)', p2p_block)
            if evpn_match:
                xc_data['evi'] = int(evpn_match.group(1))
                xc_data['target'] = int(evpn_match.group(2))
            
            xconnects.append(xc_data)
    
    return xconnects


def parse_l2vpn_bridge_domains(config_text: str) -> List[Dict[str, Any]]:
    """
    Parse L2VPN bridge domains from configuration.
    
    DNOS structure:
    l2vpn
      bridge-domain <name>
        interface <name>
        vfi <name>
          ...
    
    Returns:
        List of bridge domain dicts
    """
    bridge_domains = []
    
    l2vpn_start = config_text.find('\nl2vpn\n')
    if l2vpn_start == -1:
        return bridge_domains
    
    bd_pattern = re.compile(r'bridge-domain\s+(\S+)\s*\n(.*?)(?=bridge-domain\s+|\nxconnect|\n!\n!)', re.DOTALL)
    
    for bd_match in bd_pattern.finditer(config_text[l2vpn_start:]):
        bd_name = bd_match.group(1)
        bd_block = bd_match.group(2)
        
        bd_data = {
            'name': bd_name,
            'interfaces': [],
            'vfi': None
        }
        
        # Parse interfaces
        iface_matches = re.findall(r'interface\s+(\S+)', bd_block)
        bd_data['interfaces'] = iface_matches
        
        # Parse VFI if present
        vfi_match = re.search(r'vfi\s+(\S+)', bd_block)
        if vfi_match:
            bd_data['vfi'] = vfi_match.group(1)
        
        bridge_domains.append(bd_data)
    
    return bridge_domains


# =============================================================================
# DEVICE TYPE DETECTION (Cluster vs Standalone)
# =============================================================================

def detect_device_type(config_text: str) -> str:
    """
    Detect if device is a Cluster or Standalone based on configuration.
    
    Cluster indicators:
    - Multiple NCP definitions (ncp 6, ncp 18, etc.)
    - fab-ncp* interfaces present
    - ctrl-ncp* interfaces present
    
    Returns:
        'cluster' or 'standalone'
    """
    # Check for multiple NCPs
    ncp_pattern = re.compile(r'^\s*ncp\s+(\d+)\s*$', re.MULTILINE)
    ncp_matches = ncp_pattern.findall(config_text)
    
    if len(ncp_matches) > 1:
        return 'cluster'
    
    # Check for fabric interfaces
    if re.search(r'^\s*fab-ncp', config_text, re.MULTILINE):
        return 'cluster'
    
    # Check for ctrl-ncp interfaces
    if re.search(r'^\s*ctrl-ncp', config_text, re.MULTILINE):
        return 'cluster'
    
    return 'standalone'


def get_cluster_specific_interfaces(config_text: str) -> Set[str]:
    """
    Get all cluster-specific interfaces that should be filtered when mirroring to SA.
    
    Cluster-specific interfaces:
    - fab-ncp* (fabric interconnect)
    - ctrl-ncp* (control plane)
    - console-ncp* (console)
    
    Returns:
        Set of interface names
    """
    cluster_ifaces = set()
    
    # Find interfaces section
    iface_section = extract_hierarchy_section(config_text, 'interfaces')
    if not iface_section:
        return cluster_ifaces
    
    # Match cluster-specific interface names
    patterns = [
        r'^\s*(fab-ncp[\w/-]+)\s*$',
        r'^\s*(ctrl-ncp[\w/-]+)\s*$', 
        r'^\s*(console-ncp[\w/-]+)\s*$'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, iface_section, re.MULTILINE)
        cluster_ifaces.update(matches)
    
    return cluster_ifaces


def get_ncp_slots(config_text: str) -> List[int]:
    """
    Get NCP slot numbers from configuration.
    
    Returns:
        List of NCP slot numbers (e.g., [6, 18] for cluster, [0] for SA)
    """
    ncp_pattern = re.compile(r'^\s*ncp\s+(\d+)\s*$', re.MULTILINE)
    ncp_matches = ncp_pattern.findall(config_text)
    
    if ncp_matches:
        return sorted([int(n) for n in ncp_matches])
    
    # For standalone, return [0]
    return [0]


def get_wan_interfaces(config_text: str) -> List[str]:
    """
    Get WAN interfaces (interfaces configured in IGP protocols).
    
    WAN interfaces are those that appear in:
    - ISIS interface entries
    - LDP interface entries
    - OSPF interface entries
    
    Returns:
        List of WAN interface names (excluding loopback)
    """
    wan_interfaces = set()
    
    protocols_section = extract_hierarchy_section(config_text, 'protocols')
    if not protocols_section:
        return []
    
    lines = protocols_section.split('\n')
    in_igp = False
    igp_indent = 0
    
    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        
        # Detect start of IGP section
        if indent == 2 and (stripped.startswith('isis') or 
                            stripped.startswith('ospf') or 
                            stripped == 'ldp'):
            in_igp = True
            igp_indent = indent
            continue
        
        # Detect end of IGP section
        if in_igp and indent <= igp_indent and stripped and stripped != '!':
            in_igp = False
            continue
        
        if in_igp and stripped == '!' and indent <= igp_indent:
            in_igp = False
            continue
        
        # Extract interface names from inside IGP section
        if in_igp and stripped.startswith('interface '):
            iface_name = stripped.replace('interface ', '').strip()
            # Exclude loopback
            if not iface_name.startswith('lo'):
                wan_interfaces.add(iface_name)
    
    return sorted(wan_interfaces)


def get_service_interfaces(config_text: str) -> Dict[str, List[str]]:
    """
    Get service-attached interfaces categorized by type.
    
    Returns:
        Dict with keys:
        - 'pwhe': PWHE interfaces (ph*)
        - 'l2ac': L2-AC interfaces (with l2-service enabled)
        - 'irb': IRB interfaces
    """
    result = {
        'pwhe': [],
        'l2ac': [],
        'irb': []
    }
    
    iface_section = extract_hierarchy_section(config_text, 'interfaces')
    if not iface_section:
        return result
    
    lines = iface_section.split('\n')
    current_iface = None
    has_l2_service = False
    
    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        
        # New interface at 2-space indent
        if indent == 2 and stripped and not stripped.startswith('!'):
            # Save previous interface if it had l2-service
            if current_iface and has_l2_service:
                if not current_iface.startswith('ph') and not current_iface.startswith('irb'):
                    result['l2ac'].append(current_iface)
            
            current_iface = stripped
            has_l2_service = False
            
            # Check if PWHE
            if current_iface.startswith('ph'):
                result['pwhe'].append(current_iface)
            elif current_iface.startswith('irb'):
                result['irb'].append(current_iface)
        
        # Check for l2-service enabled
        elif stripped == 'l2-service enabled':
            has_l2_service = True
    
    # Handle last interface
    if current_iface and has_l2_service:
        if not current_iface.startswith('ph') and not current_iface.startswith('irb'):
            result['l2ac'].append(current_iface)
    
    return result


def parse_isis_config(config_text: str) -> Dict[str, Any]:
    """
    Parse ISIS configuration details.
    
    Returns:
        Dict with ISIS configuration including instance, ISO-network, interfaces
    """
    isis_config = {
        'instances': [],
        'interfaces': []
    }
    
    protocols_section = extract_hierarchy_section(config_text, 'protocols')
    if not protocols_section:
        return isis_config
    
    # Find ISIS section
    isis_pattern = re.compile(r'^\s{2}isis\s+(\S+)\s*\n(.*?)(?=^\s{2}[a-z]|\n\s{2}!)', re.MULTILINE | re.DOTALL)
    
    for isis_match in isis_pattern.finditer(protocols_section):
        instance_name = isis_match.group(1)
        isis_block = isis_match.group(2)
        
        instance_data = {
            'name': instance_name,
            'iso_network': None,
            'interfaces': [],
            'segment_routing': False
        }
        
        # Parse ISO network
        iso_match = re.search(r'iso-network\s+(\S+)', isis_block)
        if iso_match:
            instance_data['iso_network'] = iso_match.group(1)
        
        # Parse interfaces
        iface_matches = re.findall(r'interface\s+(\S+)', isis_block)
        instance_data['interfaces'] = iface_matches
        
        # Check for segment-routing
        if 'segment-routing' in isis_block:
            instance_data['segment_routing'] = True
        
        isis_config['instances'].append(instance_data)
        isis_config['interfaces'].extend(iface_matches)
    
    return isis_config


def parse_ldp_config(config_text: str) -> Dict[str, Any]:
    """
    Parse LDP configuration details.
    
    Returns:
        Dict with LDP configuration including transport address, interfaces
    """
    ldp_config = {
        'transport_address': None,
        'interfaces': []
    }
    
    protocols_section = extract_hierarchy_section(config_text, 'protocols')
    if not protocols_section:
        return ldp_config
    
    # Find LDP section
    ldp_start = protocols_section.find('\n  ldp\n')
    if ldp_start == -1:
        return ldp_config
    
    # Find end of LDP section
    ldp_end = protocols_section.find('\n  !', ldp_start + 1)
    if ldp_end == -1:
        ldp_end = len(protocols_section)
    
    ldp_block = protocols_section[ldp_start:ldp_end]
    
    # Parse transport address
    transport_match = re.search(r'transport-address\s+(\S+)', ldp_block)
    if transport_match:
        ldp_config['transport_address'] = transport_match.group(1)
    
    # Parse interfaces
    iface_matches = re.findall(r'interface\s+(\S+)', ldp_block)
    ldp_config['interfaces'] = [i for i in iface_matches if not i.startswith('lo')]
    
    return ldp_config

