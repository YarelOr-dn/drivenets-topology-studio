"""
Multihoming/ESI Configuration for the SCALER Wizard.

This module contains:
- ESI generation and validation
- Interface filtering for multihoming
- Synchronized multihoming between PEs
- RT+VLAN based ESI matching
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console

console = Console()


def filter_multihoming_interfaces(interfaces: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """
    Filter interfaces for multihoming.
    
    Supported for ALL redundancy modes:
        - ge*-*/*/*.Y, bundle-*.Y (physical/bundle sub-interfaces with l2-service)
    
    Supported for SINGLE-ACTIVE only (FXC/VPWS):
        - ph*.* (PWHE interfaces) - L3 but supported in active-standby mode
    
    Returns:
        Tuple of (l2_interfaces, pwhe_interfaces, rejected_interfaces)
        - l2_interfaces: Support all redundancy modes
        - pwhe_interfaces: Only support single-active mode
        - rejected_interfaces: Not supported at all
    """
    l2_valid = []
    pwhe_valid = []
    rejected = []
    
    for iface in interfaces:
        # PWHE interfaces (ph*.*) - supported for single-active only
        if re.match(r'^ph\d+', iface):
            pwhe_valid.append(iface)
        # Physical or bundle sub-interfaces - support all modes
        elif re.match(r'^(ge\d+-\d+/\d+/\d+|bundle-\d+)', iface):
            l2_valid.append(iface)
        else:
            rejected.append(iface)
    
    return l2_valid, pwhe_valid, rejected


def extract_interface_number(interface_name: str) -> Optional[int]:
    """
    Extract the numeric identifier from an interface name.
    
    Examples:
        ph1876.1 -> 1876
        ph1.1 -> 1
        ge100-0/0/1.100 -> 100  (uses sub-interface number)
        l2-ac-1234 -> 1234
        
    Args:
        interface_name: Interface name (e.g., ph1876.1)
        
    Returns:
        Integer interface number or None if not extractable
    """
    # PWHE interface: phXXX.Y -> extract XXX
    match = re.match(r'^ph(\d+)\.?\d*$', interface_name)
    if match:
        return int(match.group(1))
    
    # L2-AC interface: ge/xe with sub-interface number
    match = re.match(r'^[gx]e[\d\-/]+\.(\d+)$', interface_name)
    if match:
        return int(match.group(1))
    
    # Generic: extract last numeric group
    numbers = re.findall(r'(\d+)', interface_name)
    if numbers:
        return int(numbers[-1])
    
    return None


def generate_esi(prefix: int, index: int) -> str:
    """
    Generate ESI in arbitrary format (Type-0).
    
    Format: 00:PP:PP:00:00:00:II:II:II
    Where PP:PP = prefix (configurable)
          II:II:II = index (interface number for consistency across PEs)
    
    Args:
        prefix: 16-bit prefix value
        index: Interface number (extracted from interface name for PE consistency)
        
    Returns:
        ESI string in XX:XX:XX:XX:XX:XX:XX:XX:XX format
    """
    # Type-0 arbitrary ESI: 00:prefix_hi:prefix_lo:00:00:00:idx_hi:idx_mid:idx_lo
    prefix_hi = (prefix >> 8) & 0xFF
    prefix_lo = prefix & 0xFF
    idx_hi = (index >> 16) & 0xFF
    idx_mid = (index >> 8) & 0xFF
    idx_lo = index & 0xFF
    
    return f"00:{prefix_hi:02x}:{prefix_lo:02x}:00:00:00:{idx_hi:02x}:{idx_mid:02x}:{idx_lo:02x}"


def match_esi_by_service(
    local_interface: str,
    local_config: str,
    neighbor_rt_to_esi: dict,
    local_iface_to_rt: dict = None
) -> Optional[str]:
    """
    Find the ESI for a local interface by matching its service RT to neighbor's RT->ESI mapping.
    
    This is the core of service-based MH matching:
    1. Find the RT(s) for the local interface's service
    2. Look up that RT in neighbor's rt_to_esi mapping
    3. Return the neighbor's ESI for that RT
    
    Args:
        local_interface: Interface name on local device
        local_config: Local device's running configuration
        neighbor_rt_to_esi: Neighbor's RT->ESI mapping
        local_iface_to_rt: Optional pre-built interface->RT mapping
        
    Returns:
        ESI value from neighbor if matching RT found, None otherwise
    """
    from .parsers import build_interface_to_rt_mapping
    
    # Build local interface->RT mapping if not provided
    if local_iface_to_rt is None:
        local_iface_to_rt = build_interface_to_rt_mapping(local_config)
    
    # Get RTs for this local interface
    local_rts = local_iface_to_rt.get(local_interface, set())
    
    if not local_rts:
        return None
    
    # Get local interface number for matching preference
    local_iface_num = extract_interface_number(local_interface)
    
    # Find all matching RTs and score them
    candidates = []
    for rt in local_rts:
        if rt in neighbor_rt_to_esi:
            neighbor_info = neighbor_rt_to_esi[rt]
            neighbor_iface = neighbor_info.get('interface', '')
            neighbor_iface_num = extract_interface_number(neighbor_iface)
            
            # Score: prefer RTs where neighbor interface number matches local
            if local_iface_num and neighbor_iface_num:
                if local_iface_num == neighbor_iface_num:
                    score = 0  # Perfect match
                else:
                    score = abs(local_iface_num - neighbor_iface_num)
            else:
                score = 999999
            
            candidates.append((score, rt, neighbor_info['esi']))
    
    if not candidates:
        return None
    
    # Sort by score (lowest first = best match) and return best ESI
    candidates.sort(key=lambda x: x[0])
    return candidates[0][2]


def detect_neighbor_pe_with_mh(current_device, current_rts: set) -> Optional[dict]:
    """
    Detect a neighboring PE that shares route-targets and has multihoming configured.
    
    Args:
        current_device: The device we're configuring
        current_rts: Set of route-targets on current device
        
    Returns:
        Dict with neighbor info or None if not found
    """
    from .parsers import parse_route_targets, parse_existing_multihoming, build_rt_to_esi_mapping
    
    try:
        from ..device_manager import DeviceManager
        dm = DeviceManager()
        devices = dm.list_devices()
    except:
        return None
    
    for dev in devices:
        if dev.id == current_device.id:
            continue  # Skip current device
        
        # Load neighbor's running config
        config_path = f"db/configs/{dev.hostname}/running.txt"
        try:
            with open(config_path, 'r') as f:
                neighbor_config = f.read()
        except:
            continue
        
        # Check for matching route-targets
        neighbor_rts = parse_route_targets(neighbor_config)
        shared_rts = current_rts & neighbor_rts
        
        if not shared_rts:
            continue
        
        # Check if neighbor has multihoming configured
        neighbor_mh = parse_existing_multihoming(neighbor_config)
        
        if neighbor_mh:
            # Build RT->ESI mapping for service-based matching
            rt_to_esi_map = build_rt_to_esi_mapping(neighbor_config, neighbor_mh)
            
            return {
                'device': dev,
                'hostname': dev.hostname,
                'shared_rts': shared_rts,
                'mh_interfaces': neighbor_mh,
                'mh_count': len(neighbor_mh),
                'rt_to_esi': rt_to_esi_map,
                'neighbor_config': neighbor_config
            }
    
    return None


# =====================================================================
# Main configuration functions - imported from main module
# =====================================================================

def configure_multihoming(*args, **kwargs):
    """Configure multihoming hierarchy.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import configure_multihoming as _impl
    return _impl(*args, **kwargs)


def push_multihoming_to_existing(*args, **kwargs):
    """Push multihoming config to existing EVPN services.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import push_multihoming_to_existing as _impl
    return _impl(*args, **kwargs)


def push_synchronized_multihoming(*args, **kwargs):
    """Push synchronized multihoming to multiple devices.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import push_synchronized_multihoming as _impl
    return _impl(*args, **kwargs)


def configure_df_invert_preference(*args, **kwargs):
    """Configure DF invert preference.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import configure_df_invert_preference as _impl
    return _impl(*args, **kwargs)

