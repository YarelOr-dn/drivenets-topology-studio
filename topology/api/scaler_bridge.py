"""
SCALER Bridge Module

Imports and exposes SCALER functionality for the web API.
This module bridges the gap between the FastAPI backend and the SCALER CLI tool.
"""

import sys
import os
import re
from typing import Dict, List, Any, Optional
from functools import lru_cache

# Add SCALER to Python path
SCALER_PATH = '/home/dn/SCALER'
if SCALER_PATH not in sys.path:
    sys.path.insert(0, SCALER_PATH)

# Import SCALER modules
from scaler.device_manager import DeviceManager
from scaler.config_extractor import ConfigExtractor
from scaler.config_parser import ConfigParser
from scaler.models import Device, Platform


# ============================================================================
# Singleton Instances
# ============================================================================

_device_manager: Optional[DeviceManager] = None
_config_extractor: Optional[ConfigExtractor] = None
_config_parser: Optional[ConfigParser] = None


def get_device_manager() -> DeviceManager:
    """Get or create DeviceManager singleton."""
    global _device_manager
    if _device_manager is None:
        _device_manager = DeviceManager()
    return _device_manager


def get_config_extractor() -> ConfigExtractor:
    """Get or create ConfigExtractor singleton."""
    global _config_extractor
    if _config_extractor is None:
        _config_extractor = ConfigExtractor()
    return _config_extractor


def get_config_parser() -> ConfigParser:
    """Get or create ConfigParser singleton."""
    global _config_parser
    if _config_parser is None:
        _config_parser = ConfigParser()
    return _config_parser


# ============================================================================
# Device Operations
# ============================================================================

def _load_operational_for_device(hostname: str) -> Dict[str, Any]:
    """Load mgmt_ip, serial_number, connection_method, and ssh_host from SCALER operational.json for a device."""
    try:
        import json
        from pathlib import Path
        op_path = Path(SCALER_PATH) / "db" / "configs" / hostname / "operational.json"
        if op_path.exists():
            with open(op_path) as f:
                data = json.load(f)
            return {
                "mgmt_ip": data.get("mgmt_ip"),
                "serial_number": data.get("serial_number"),
                "connection_method": data.get("connection_method"),  # e.g., "SSH→SN", "SSH→MGMT", "Console"
                "ssh_host": data.get("ssh_host"),  # The actual host that worked for SSH
            }
    except Exception:
        pass
    return {}


def list_devices() -> List[Dict[str, Any]]:
    """List all configured devices. Includes mgmt_ip and serial_number from operational.json when available."""
    dm = get_device_manager()
    devices = dm.list_devices()
    result = []
    for d in devices:
        entry = {
            "id": d.id,
            "hostname": d.hostname,
            "ip": d.ip,
            "username": d.username,
            "password": d.password,
            "platform": d.platform.value if hasattr(d.platform, 'value') else str(d.platform),
            "last_sync": d.last_sync.isoformat() if d.last_sync else None,
            "description": d.description
        }
        op = _load_operational_for_device(d.hostname)
        if op.get("mgmt_ip") and op["mgmt_ip"] != "N/A":
            entry["mgmt_ip"] = op["mgmt_ip"].split("/")[0] if "/" in str(op["mgmt_ip"]) else op["mgmt_ip"]
        if op.get("serial_number") and op["serial_number"] != "N/A":
            entry["serial_number"] = op["serial_number"]
        # Add connection info for CURSOR SSH dialog
        if op.get("connection_method") and op["connection_method"] != "N/A":
            entry["connection_method"] = op["connection_method"]
        if op.get("ssh_host") and op["ssh_host"] != "N/A" and op["ssh_host"] != "console":
            entry["ssh_host"] = op["ssh_host"]
        result.append(entry)
    return result


def get_device(device_id: str) -> Optional[Dict[str, Any]]:
    """Get a single device by ID. Includes mgmt_ip and serial_number from operational.json when available."""
    dm = get_device_manager()
    device = dm.get_device(device_id)
    if device:
        entry = {
            "id": device.id,
            "hostname": device.hostname,
            "ip": device.ip,
            "username": device.username,
            "platform": device.platform.value if hasattr(device.platform, 'value') else str(device.platform),
            "last_sync": device.last_sync.isoformat() if device.last_sync else None,
            "description": device.description
        }
        op = _load_operational_for_device(device.hostname)
        if op.get("mgmt_ip") and op["mgmt_ip"] != "N/A":
            entry["mgmt_ip"] = op["mgmt_ip"].split("/")[0] if "/" in str(op["mgmt_ip"]) else op["mgmt_ip"]
        if op.get("serial_number") and op["serial_number"] != "N/A":
            entry["serial_number"] = op["serial_number"]
        # Add connection info for CURSOR SSH dialog
        if op.get("connection_method") and op["connection_method"] != "N/A":
            entry["connection_method"] = op["connection_method"]
        if op.get("ssh_host") and op["ssh_host"] != "N/A" and op["ssh_host"] != "console":
            entry["ssh_host"] = op["ssh_host"]
        return entry
    return None


def get_device_object(device_id: str) -> Optional[Device]:
    """Get the actual Device object for operations."""
    dm = get_device_manager()
    return dm.get_device(device_id)


def test_device_connection(device_id: str) -> Dict[str, Any]:
    """Test SSH connection to a device."""
    dm = get_device_manager()
    device = dm.get_device(device_id)
    if not device:
        return {"success": False, "error": f"Device {device_id} not found"}
    
    try:
        extractor = get_config_extractor()
        # Try to connect and run a simple command
        result = extractor.test_connection(device)
        return {"success": True, "message": "Connection successful"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# Configuration Extraction
# ============================================================================

def get_running_config(device_id: str) -> Dict[str, Any]:
    """Extract running configuration from device."""
    device = get_device_object(device_id)
    if not device:
        return {"success": False, "error": f"Device {device_id} not found"}
    
    try:
        extractor = get_config_extractor()
        config = extractor.extract_running_config(device, save_to_db=True)
        return {
            "success": True,
            "config": config,
            "lines": len(config.split('\n')) if config else 0
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_cached_config(device_id: str) -> Optional[str]:
    """Get cached configuration from database."""
    dm = get_device_manager()
    device = dm.get_device(device_id)
    if not device:
        return None
    
    # Try to read from cache
    config_path = f"{SCALER_PATH}/db/configs/{device.hostname}/running.txt"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return f.read()
    return None


# ============================================================================
# Configuration Parsing
# ============================================================================

def extract_config_summary(config_text: str) -> Dict[str, Any]:
    """
    Parse configuration and return structured summary.
    Mirrors show_current_config_summary() from interactive_scale.py
    """
    if not config_text:
        return {"error": "No configuration provided"}
    
    summary = {
        "system": {"name": None, "profile": None, "users": 0, "configured": False},
        "interfaces": {"count": 0, "types": {}, "details": []},
        "services": {"count": 0, "types": {}, "rt_count": 0},
        "bgp": {"as_number": None, "peers": 0, "router_id": None},
        "igp": {"protocol": None, "instance": None, "interfaces": 0},
        "multihoming": {"count": 0, "interfaces": {}, "esi_prefix": None}
    }
    
    # Parse system section
    system_match = re.search(r'^\s*system\s*$', config_text, re.MULTILINE)
    if system_match:
        summary["system"]["configured"] = True
        name_match = re.search(r'^\s+name\s+(\S+)', config_text, re.MULTILINE)
        if name_match:
            summary["system"]["name"] = name_match.group(1)
        profile_match = re.search(r'^\s+profile\s+(\S+)', config_text, re.MULTILINE)
        if profile_match:
            summary["system"]["profile"] = profile_match.group(1)
        user_matches = re.findall(r'^\s+user\s+(\S+)', config_text, re.MULTILINE)
        summary["system"]["users"] = len(user_matches)
    
    # Parse interfaces
    in_interfaces = False
    for line in config_text.split('\n'):
        stripped = line.strip()
        if stripped == 'interfaces':
            in_interfaces = True
            continue
        if in_interfaces and stripped and not line.startswith(' ') and stripped != '!':
            in_interfaces = False
        if in_interfaces and line.startswith('  ') and not line.startswith('    '):
            if stripped and stripped != '!':
                summary["interfaces"]["count"] += 1
                has_subif = '.' in stripped
                if stripped.startswith('ph'):
                    itype = 'pwhe_subif' if has_subif else 'pwhe'
                elif stripped.startswith('lo'):
                    itype = 'loopback'
                elif stripped.startswith('bundle'):
                    itype = 'bundle_subif' if has_subif else 'bundle'
                elif re.match(r'^(ge\d+-|ge100-|ge400-|hundredGigE|tenGigE)', stripped):
                    itype = 'physical_subif' if has_subif else 'physical'
                elif stripped.startswith('irb'):
                    itype = 'irb'
                elif stripped.startswith('ipmi'):
                    itype = 'management'
                else:
                    itype = 'other'
                summary["interfaces"]["types"][itype] = summary["interfaces"]["types"].get(itype, 0) + 1
    
    # Parse BGP
    bgp_match = re.search(r'protocols\s+bgp\s+(\d+)', config_text)
    if bgp_match:
        summary["bgp"]["as_number"] = bgp_match.group(1)
    summary["bgp"]["peers"] = len(re.findall(r'neighbor\s+\d+\.\d+\.\d+\.\d+', config_text))
    router_id_match = re.search(r'router-id\s+(\d+\.\d+\.\d+\.\d+)', config_text)
    if router_id_match:
        summary["bgp"]["router_id"] = router_id_match.group(1)
    
    # Parse IGP
    isis_match = re.search(r'^\s{2}isis\s*\n\s+instance\s+(\S+)', config_text, re.MULTILINE)
    if isis_match:
        summary["igp"]["protocol"] = "ISIS"
        summary["igp"]["instance"] = isis_match.group(1)
        isis_interfaces = re.findall(r'^\s{6}interface\s+(\S+)', config_text, re.MULTILINE)
        summary["igp"]["interfaces"] = len(isis_interfaces)
    elif re.search(r'^\s{2}ospf\s*\n\s+instance\s+\S+', config_text, re.MULTILINE):
        summary["igp"]["protocol"] = "OSPF"
    
    # Parse services
    fxc_instances = set(re.findall(r'instance\s+(FXC-?\d+)', config_text, re.IGNORECASE))
    if fxc_instances:
        summary["services"]["types"]["FXC"] = len(fxc_instances)
        summary["services"]["count"] += len(fxc_instances)
    
    vpls_count = len(re.findall(r'evpn-vpls', config_text))
    if vpls_count:
        summary["services"]["types"]["VPLS"] = vpls_count
        summary["services"]["count"] += vpls_count
    
    l3vpn_instances = set(re.findall(r'l3vpn\s+instance\s+(\S+)', config_text))
    if l3vpn_instances:
        summary["services"]["types"]["L3VPN"] = len(l3vpn_instances)
        summary["services"]["count"] += len(l3vpn_instances)
    
    # Count Route Targets
    rt_matches = set(re.findall(r'route-target\s+(\d+:\d+)', config_text))
    summary["services"]["rt_count"] = len(rt_matches)
    
    # Parse Multihoming
    mh_interfaces = parse_multihoming(config_text)
    summary["multihoming"]["count"] = len(mh_interfaces)
    summary["multihoming"]["interfaces"] = mh_interfaces
    
    if mh_interfaces:
        sample_esi = next(iter(mh_interfaces.values()), "")
        if isinstance(sample_esi, dict):
            sample_esi = sample_esi.get('esi', '')
        if sample_esi:
            summary["multihoming"]["esi_prefix"] = ":".join(sample_esi.split(":")[:3])
    
    return summary


def parse_multihoming(config_text: str) -> Dict[str, str]:
    """
    Parse multihoming configuration from running config.
    Returns dict mapping interface names to ESI values.
    """
    mh_interfaces = {}
    
    if not config_text:
        return mh_interfaces
    
    # Find multihoming section
    mh_start = re.search(r'^(\s*)multihoming\s*$', config_text, re.MULTILINE)
    if not mh_start:
        mh_start = re.search(r'multihoming\s*\n', config_text)
    
    if mh_start:
        start_pos = mh_start.end()
        base_indent = len(mh_start.group(1)) if mh_start.lastindex else 0
        remaining = config_text[start_pos:]
        
        # Find interfaces and their ESI values
        current_interface = None
        for line in remaining.split('\n'):
            # Check if we've left the multihoming section
            if line and not line.startswith(' ') and line.strip() not in ('!', ''):
                break
            
            stripped = line.strip()
            
            # Match interface line
            iface_match = re.match(r'interface\s+(\S+)', stripped)
            if iface_match:
                current_interface = iface_match.group(1)
                continue
            
            # Match ESI value
            if current_interface:
                esi_match = re.match(r'esi\s+arbitrary\s+value\s+([0-9a-fA-F:]+)', stripped)
                if esi_match:
                    mh_interfaces[current_interface] = esi_match.group(1)
    
    return mh_interfaces


def extract_hierarchy_section(config_text: str, hierarchy: str) -> Optional[str]:
    """Extract a specific hierarchy section from config."""
    if not config_text:
        return None
    
    # Map hierarchy names to config patterns
    patterns = {
        'system': r'^system\s*\n(.*?)(?=\n[a-z]|\ninterfaces|\Z)',
        'interfaces': r'^interfaces\s*\n(.*?)(?=\n[a-z]|\nnetwork-services|\nprotocols|\Z)',
        'services': r'^network-services\s*\n(.*?)(?=\n[a-z]|\nprotocols|\Z)',
        'bgp': r'^protocols\s*\n\s+bgp\s+\d+\s*\n(.*?)(?=\n\s{2}[a-z]|\Z)',
        'igp': r'^protocols\s*\n\s+isis\s*\n(.*?)(?=\n\s{2}[a-z]|\Z)',
        'multihoming': r'^multihoming\s*\n(.*?)(?=\n[a-z]|\Z)'
    }
    
    pattern = patterns.get(hierarchy.lower())
    if not pattern:
        return None
    
    match = re.search(pattern, config_text, re.MULTILINE | re.DOTALL)
    if match:
        return f"{hierarchy}\n{match.group(1)}"
    return None


# ============================================================================
# Interface Parsing
# ============================================================================

def get_interfaces_from_config(config_text: str) -> List[Dict[str, Any]]:
    """Parse all interfaces from configuration."""
    interfaces = []
    
    if not config_text:
        return interfaces
    
    in_interfaces = False
    current_interface = None
    current_data = {}
    
    for line in config_text.split('\n'):
        stripped = line.strip()
        
        if stripped == 'interfaces':
            in_interfaces = True
            continue
        
        if in_interfaces and stripped and not line.startswith(' ') and stripped != '!':
            in_interfaces = False
            if current_interface:
                interfaces.append(current_data)
            continue
        
        if in_interfaces:
            # New interface definition (2 spaces indent)
            if line.startswith('  ') and not line.startswith('    '):
                if current_interface and current_data:
                    interfaces.append(current_data)
                
                if stripped and stripped != '!':
                    current_interface = stripped
                    has_subif = '.' in stripped
                    
                    # Determine type
                    if stripped.startswith('ph'):
                        itype = 'pwhe'
                    elif stripped.startswith('lo'):
                        itype = 'loopback'
                    elif stripped.startswith('bundle'):
                        itype = 'bundle'
                    elif re.match(r'^(ge\d+-|ge100-|ge400-)', stripped):
                        itype = 'physical'
                    elif stripped.startswith('irb'):
                        itype = 'irb'
                    else:
                        itype = 'other'
                    
                    current_data = {
                        "name": current_interface,
                        "type": itype,
                        "is_subinterface": has_subif,
                        "admin_state": "enabled",
                        "description": None,
                        "vlan": None,
                        "ipv4": None
                    }
                else:
                    current_interface = None
                    current_data = {}
            
            # Interface properties (4+ spaces indent)
            elif line.startswith('    ') and current_interface:
                if 'admin-state disable' in stripped:
                    current_data["admin_state"] = "disabled"
                elif stripped.startswith('description'):
                    current_data["description"] = stripped.replace('description ', '').strip('"')
                elif 'outer-vlan-id' in stripped:
                    match = re.search(r'outer-vlan-id\s+(\d+)', stripped)
                    if match:
                        current_data["vlan"] = int(match.group(1))
                elif 'vlan-id' in stripped and 'outer' not in stripped:
                    match = re.search(r'vlan-id\s+(\d+)', stripped)
                    if match:
                        current_data["vlan"] = int(match.group(1))
                elif stripped.startswith('ipv4 address'):
                    match = re.search(r'ipv4 address\s+(\S+)', stripped)
                    if match:
                        current_data["ipv4"] = match.group(1)
    
    # Don't forget the last interface
    if current_interface and current_data:
        interfaces.append(current_data)
    
    return interfaces


# ============================================================================
# Service Parsing
# ============================================================================

def get_services_from_config(config_text: str) -> List[Dict[str, Any]]:
    """Parse all services from configuration."""
    services = []
    
    if not config_text:
        return services
    
    # Find FXC instances
    fxc_pattern = r'instance\s+(FXC-?\d+)\s*\n(.*?)(?=\n\s{4}instance|\n\s{2}[a-z]|\n[a-z]|\Z)'
    for match in re.finditer(fxc_pattern, config_text, re.DOTALL | re.IGNORECASE):
        name = match.group(1)
        content = match.group(2)
        
        rt_match = re.search(r'route-target\s+(\d+:\d+)', content)
        interfaces = re.findall(r'interface\s+(\S+)', content)
        
        services.append({
            "name": name,
            "type": "FXC",
            "route_target": rt_match.group(1) if rt_match else None,
            "interfaces": interfaces
        })
    
    # Find VPLS instances
    vpls_pattern = r'instance\s+(\S+).*?evpn-vpls.*?(?=\n\s{4}instance|\n\s{2}[a-z]|\Z)'
    for match in re.finditer(vpls_pattern, config_text, re.DOTALL):
        name = match.group(1)
        services.append({
            "name": name,
            "type": "VPLS",
            "route_target": None,
            "interfaces": []
        })
    
    return services


# ============================================================================
# Utility Functions
# ============================================================================

def reload_device_manager():
    """Force reload of device manager (after adding/removing devices)."""
    global _device_manager
    _device_manager = None
    return get_device_manager()


# ============================================================================
# CONFIG GENERATION - Using SCALER's ScaleGenerator
# ============================================================================

from scaler.scale_generator import ScaleGenerator
from scaler.models import InterfaceScale, ServiceScale, InterfaceType, ServiceType

_scale_generator: Optional[ScaleGenerator] = None

def get_scale_generator() -> ScaleGenerator:
    """Get or create ScaleGenerator singleton."""
    global _scale_generator
    if _scale_generator is None:
        _scale_generator = ScaleGenerator()
    return _scale_generator


def generate_interface_config(
    interface_type: str,
    start_number: int = 1,
    count: int = 10,
    slot: int = 0,
    bay: int = 0,
    port_start: int = 0,
    create_subinterfaces: bool = True,
    subif_count: int = 1,
    vlan_start: int = 100,
    vlan_step: int = 1,
    encapsulation: str = "dot1q",
    outer_vlan: int = 1,
    l2_service: bool = False
) -> str:
    """
    Generate interface configuration using proper DNOS syntax.
    
    Validated against DNOS CLI PDF and running configs.
    
    DNOS Interface Naming:
    - Bundle: bundle-<number> (e.g., bundle-100)
    - Physical 400G: ge400-<slot>/<bay>/<port> (e.g., ge400-0/0/0)
    - Physical 100G: ge100-<slot>/<bay>/<port> (e.g., ge100-0/0/0)
    - Physical 10G: ge10-<slot>/<bay>/<port> (e.g., ge10-0/0/0)
    - PWHE: ph<number> (e.g., ph1)
    - Sub-interface: <parent>.<vlan> (e.g., bundle-100.12)
    
    Args:
        interface_type: Type of interface (bundle, ge100, ge400, ph)
        start_number: Starting interface number
        count: Number of interfaces
        slot/bay/port_start: For physical interfaces
        create_subinterfaces: Whether to create sub-interfaces
        subif_count: Number of sub-interfaces per interface
        vlan_start: Starting VLAN ID
        vlan_step: VLAN increment
        encapsulation: dot1q or qinq
        outer_vlan: Outer VLAN for QinQ (inner VLANs will be vlan_start+)
        l2_service: Enable l2-service for FXC attachment
    
    Returns:
        DNOS configuration string
    """
    lines = []
    iface_type = interface_type.lower()
    
    is_bundle = 'bundle' in iface_type
    is_pwhe = iface_type == 'ph'
    
    lines.append("interfaces")
    
    for i in range(count):
        iface_num = start_number + i
        
        if is_bundle:
            # Bundle interface: bundle-<number>
            full_name = f"bundle-{iface_num}"
        elif is_pwhe:
            # PWHE interface: ph<number>
            full_name = f"ph{iface_num}"
        elif iface_type in ['ge400', 'fourhundredgige']:
            # 400G physical: ge400-<slot>/<bay>/<port>
            port = port_start + i
            full_name = f"ge400-{slot}/{bay}/{port}"
        elif iface_type in ['ge100', 'hundredgige']:
            # 100G physical: ge100-<slot>/<bay>/<port>
            port = port_start + i
            full_name = f"ge100-{slot}/{bay}/{port}"
        elif iface_type in ['ge10', 'tengige']:
            # 10G physical: ge10-<slot>/<bay>/<port>
            port = port_start + i
            full_name = f"ge10-{slot}/{bay}/{port}"
        else:
            # Default to bundle
            full_name = f"bundle-{iface_num}"
        
        # Parent interface
        lines.append(f"  {full_name}")
        lines.append(f"    admin-state enabled")
        if is_bundle:
            lines.append(f"    mtu 9216")
        elif not is_pwhe and not is_bundle:
            # Physical interface settings
            lines.append(f"    fec none")
            lines.append(f"    mtu 9216")
            lines.append(f"    speed 100")
        lines.append(f"  !")
        
        # Sub-interfaces
        if create_subinterfaces:
            for j in range(subif_count):
                vlan = vlan_start + j * vlan_step
                subif_name = f"{full_name}.{vlan}"
                
                lines.append(f"  {subif_name}")
                lines.append(f"    admin-state enabled")
                
                if encapsulation == "qinq":
                    # QinQ - vlan-tags with outer and inner
                    inner_vlan = vlan
                    lines.append(f"    vlan-tags outer-tag {outer_vlan} inner-tag {inner_vlan} outer-tpid 0x8100")
                else:
                    # Single tag - vlan-id
                    lines.append(f"    vlan-id {vlan}")
                
                if l2_service:
                    lines.append(f"    l2-service enabled")
                    
                lines.append(f"  !")
    
    lines.append("!")
    
    return "\n".join(lines)


def generate_service_config(
    service_type: str,
    name_prefix: str = "SVC",
    start_number: int = 1,
    count: int = 10,
    service_id_start: int = 1000,
    evi_start: int = 1000,
    rd_base: str = "65000",
    attach_interfaces: List[str] = None,
    router_id: str = "1.1.1.1"
) -> str:
    """
    Generate network service configuration using proper DNOS syntax.
    
    Validated against DNOS CLI PDF and running configs.
    
    Args:
        service_type: Type of service (evpn-vpws-fxc, vrf, evpn)
        name_prefix: Prefix for service names
        start_number: Starting service number
        count: Number of services
        service_id_start: Starting service ID
        evi_start: Starting EVI
        rd_base: Route Distinguisher base (ASN)
        attach_interfaces: List of interfaces to attach
        router_id: Router ID for route-distinguisher
    
    Returns:
        DNOS configuration string
    """
    if attach_interfaces is None:
        attach_interfaces = []
    
    lines = []
    svc_type = service_type.lower()
    
    # Parse rd_base for ASN
    try:
        rd_asn = int(rd_base.split(':')[0]) if ':' in rd_base else int(rd_base)
    except:
        rd_asn = 65000
    
    if svc_type in ['evpn-vpws-fxc', 'fxc', 'l2vpn-fxc']:
        # EVPN-VPWS FXC (Flexible Cross-Connect) - DNOS Syntax
        lines.append("network-services")
        lines.append("  evpn-vpws-fxc")
        
        for i in range(count):
            svc_num = start_number + i
            svc_name = f"{name_prefix}{svc_num}"
            rt_val = service_id_start + i
            rd_val = service_id_start + i
            
            lines.append(f"    instance {svc_name}")
            lines.append(f"      protocols")
            lines.append(f"        bgp {rd_asn}")
            lines.append(f"          export-l2vpn-evpn route-target {rd_asn}:{rt_val}")
            lines.append(f"          import-l2vpn-evpn route-target {rd_asn}:{rt_val}")
            lines.append(f"          route-distinguisher {router_id}:{rd_val}")
            lines.append(f"        !")
            lines.append(f"      !")
            lines.append(f"      transport-protocol")
            lines.append(f"        mpls")
            lines.append(f"          control-word enabled")
            lines.append(f"          fat-label disabled")
            lines.append(f"        !")
            lines.append(f"      !")
            lines.append(f"      admin-state enabled")
            if attach_interfaces and i < len(attach_interfaces):
                lines.append(f"      interface {attach_interfaces[i]}")
            lines.append(f"      !")
            lines.append(f"    !")
        
        lines.append("  !")
        lines.append("!")
            
    elif svc_type in ['vrf', 'l3vpn']:
        # L3VPN VRF - DNOS Syntax
        lines.append("network-services")
        lines.append("  l3vpn")
        
        for i in range(count):
            svc_num = start_number + i
            svc_name = f"{name_prefix}{svc_num}"
            rt_val = service_id_start + i
            
            lines.append(f"    vrf {svc_name}")
            lines.append(f"      protocols")
            lines.append(f"        bgp {rd_asn}")
            lines.append(f"          import-ipv4-unicast route-target {rd_asn}:{rt_val}")
            lines.append(f"          export-ipv4-unicast route-target {rd_asn}:{rt_val}")
            lines.append(f"          route-distinguisher {router_id}:{rt_val}")
            lines.append(f"        !")
            lines.append(f"      !")
            if attach_interfaces and i < len(attach_interfaces):
                lines.append(f"      interface {attach_interfaces[i]}")
            lines.append(f"      !")
            lines.append(f"    !")
        
        lines.append("  !")
        lines.append("!")
            
    elif svc_type in ['evpn', 'vpls', 'l2vpn-vpls']:
        # EVPN VPLS (Bridge Domain) - DNOS Syntax
        lines.append("network-services")
        lines.append("  evpn-vpls")
        
        for i in range(count):
            svc_num = start_number + i
            svc_name = f"{name_prefix}{svc_num}"
            evi = evi_start + i
            rt_val = service_id_start + i
            
            lines.append(f"    instance {svc_name}")
            lines.append(f"      evi {evi}")
            lines.append(f"      protocols")
            lines.append(f"        bgp {rd_asn}")
            lines.append(f"          export-l2vpn-evpn route-target {rd_asn}:{rt_val}")
            lines.append(f"          import-l2vpn-evpn route-target {rd_asn}:{rt_val}")
            lines.append(f"          route-distinguisher {router_id}:{rt_val}")
            lines.append(f"        !")
            lines.append(f"      !")
            if attach_interfaces and i < len(attach_interfaces):
                lines.append(f"      interface {attach_interfaces[i]}")
            lines.append(f"      !")
            lines.append(f"    !")
        
        lines.append("  !")
        lines.append("!")
    
    return "\n".join(lines)

