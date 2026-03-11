"""
Interface Configuration Functions for the SCALER Wizard.

This module contains:
- Interface extraction and categorization functions
- Bundle and LACP helpers
- PWHE grouping functions
- Interface config block extraction
- Interface-to-service mapping display

The main configure_interfaces() function is in the main module.
"""

import re
from typing import Any, Dict, List, Tuple

from rich.console import Console
from rich.table import Table
from rich import box

console = Console()


def _get_all_interfaces_from_config(config_text: str) -> List[str]:
    """Extract all interface names from config.
    
    Args:
        config_text: Device configuration text
        
    Returns:
        List of all interface names
    """
    interfaces = []
    lines = config_text.split('\n')
    
    in_interfaces_block = False
    
    for line in lines:
        stripped = line.strip()
        current_indent = len(line) - len(line.lstrip())
        
        if stripped == 'interfaces':
            in_interfaces_block = True
            continue
        
        if not in_interfaces_block:
            continue
        
        # End of interfaces block
        if stripped == '!' and current_indent == 0:
            in_interfaces_block = False
            continue
        
        # Interface definition at indent 2
        if current_indent == 2 and stripped and not stripped.startswith('!'):
            # Skip if it's an attribute, not an interface name
            if not stripped.startswith(('admin-state', 'description', 'mtu', 'ipv4', 'ipv6', 'vlan', 'mpls')):
                interfaces.append(stripped)
    
    return interfaces


def categorize_interfaces_by_type(interfaces: List[str]) -> Dict[str, List[str]]:
    """Categorize interfaces by their type.
    
    Separates parent interfaces from sub-interfaces (those with .N suffix).
    
    Args:
        interfaces: List of interface names
        
    Returns:
        Dict with categories including separate parent/subif categories
    """
    categories = {
        'physical': [],           # ge*, xe*, et* (parents only, no .N)
        'physical_subif': [],     # ge*.N, xe*.N, et*.N (sub-interfaces)
        'bundle': [],             # bundle* (parents only)
        'bundle_subif': [],       # bundle*.N (sub-interfaces)
        'pwhe': [],               # ph* (parents only)
        'pwhe_subif': [],         # ph*.N (sub-interfaces)
        'irb': [],                # irb*
        'loopback': [],           # lo*
        'other': []
    }
    
    for iface in interfaces:
        # Check if it's a sub-interface (has .N suffix)
        is_subif = '.' in iface
        
        # Get base name (before . for sub-interfaces)
        base = iface.split('.')[0].lower()
        
        if base.startswith('ge') or base.startswith('xe') or base.startswith('et') or base.startswith('te'):
            if is_subif:
                categories['physical_subif'].append(iface)
            else:
                categories['physical'].append(iface)
        elif base.startswith('bundle'):
            if is_subif:
                categories['bundle_subif'].append(iface)
            else:
                categories['bundle'].append(iface)
        elif base.startswith('ph'):
            if is_subif:
                categories['pwhe_subif'].append(iface)
            else:
                categories['pwhe'].append(iface)
        elif base.startswith('irb'):
            categories['irb'].append(iface)
        elif base.startswith('lo'):
            categories['loopback'].append(iface)
        else:
            categories['other'].append(iface)
    
    return categories


def get_parent_interfaces(interfaces: List[str], all_interfaces: List[str] = None) -> List[str]:
    """Get parent interfaces for a list of sub-interfaces.
    
    For sub-interfaces like 'ge100-6/0/0.14', returns the parent 'ge100-6/0/0'.
    Only returns parents that exist in all_interfaces if provided.
    
    Args:
        interfaces: List of interface names (may include sub-interfaces)
        all_interfaces: Optional list of all available interfaces to check against
        
    Returns:
        List of unique parent interface names
    """
    parents = set()
    
    for iface in interfaces:
        if '.' in iface:
            # It's a sub-interface, extract parent
            parent = iface.split('.')[0]
            parents.add(parent)
    
    # If all_interfaces provided, only return parents that exist
    if all_interfaces is not None:
        all_set = set(all_interfaces)
        parents = {p for p in parents if p in all_set}
    
    return list(parents)


def get_bundle_members(bundle_name: str, config_text: str) -> List[str]:
    """Get member interfaces for a bundle from configuration.
    
    Args:
        bundle_name: Bundle interface name (e.g., 'bundle-ether1')
        config_text: Full configuration text
        
    Returns:
        List of member interface names
    """
    members = []
    
    # Look for interfaces that have 'bundle-id X' matching this bundle
    # Extract bundle number from name
    bundle_match = re.search(r'bundle-?(?:ether)?(\d+)', bundle_name, re.IGNORECASE)
    if not bundle_match:
        return members
    
    bundle_num = bundle_match.group(1)
    
    # Search for 'bundle-id X' in interface configs
    # Pattern: interface followed by bundle-id
    in_interface = None
    for line in config_text.split('\n'):
        stripped = line.strip()
        current_indent = len(line) - len(line.lstrip())
        
        # Check if this is an interface line (2-space indent under 'interfaces')
        if current_indent == 2 and not stripped.startswith('!'):
            # Could be an interface name
            if not stripped.startswith(('admin-state', 'description', 'mtu', 'ipv4', 'ipv6', 'vlan', 'mpls')):
                in_interface = stripped
        
        # Check for bundle-id
        if in_interface and 'bundle-id' in stripped.lower():
            bid_match = re.search(r'bundle-id\s+(\d+)', stripped, re.IGNORECASE)
            if bid_match and bid_match.group(1) == bundle_num:
                members.append(in_interface)
        
        # End of interface
        if stripped == '!' and current_indent == 2:
            in_interface = None
    
    return members


def group_pwhe_subinterfaces_by_parent(interfaces: List[str]) -> Dict[str, List[str]]:
    """Group phX.Y interfaces by their parent phX.
    
    Only includes PWHE sub-interfaces (phX.Y format), not parent interfaces (phX).
    
    Args:
        interfaces: List of interface names (can include non-PWHE interfaces)
        
    Returns:
        Dict mapping parent to list of sub-interfaces: {'ph1': ['ph1.1', 'ph1.2'], 'ph2': ['ph2.1']}
    """
    grouped = {}
    
    for iface in interfaces:
        # Only process PWHE sub-interfaces (phX.Y format)
        if not iface.lower().startswith('ph'):
            continue
        
        # Must have a dot to be a sub-interface
        if '.' not in iface:
            continue
        
        # Extract parent (everything before the dot)
        parent = iface.split('.')[0]
        
        if parent not in grouped:
            grouped[parent] = []
        grouped[parent].append(iface)
    
    # Sort sub-interfaces within each parent numerically
    for parent in grouped:
        grouped[parent].sort(key=lambda x: int(x.split('.')[1]) if x.split('.')[1].isdigit() else 0)
    
    return grouped


def get_pwhe_subinterfaces_only(interfaces: List[str]) -> List[str]:
    """Filter to only PWHE sub-interfaces (phX.Y format).
    
    Args:
        interfaces: List of interface names
        
    Returns:
        List of only phX.Y format interfaces
    """
    result = []
    for iface in interfaces:
        if iface.lower().startswith('ph') and '.' in iface:
            result.append(iface)
    return result


def get_lacp_config_for_bundles(config_text: str, bundle_names: List[str]) -> str:
    """Extract LACP configuration for specified bundle interfaces.
    
    DNOS LACP config is under:
      protocols
        lacp
          interface <bundle-name>
            mode active|passive
          !
        !
      !
    
    Args:
        config_text: Full device configuration
        bundle_names: List of bundle interface names (e.g., ['bundle-100', 'bundle-200'])
        
    Returns:
        LACP configuration block if found, empty string otherwise
    """
    if not bundle_names:
        return ""
    
    # Normalize bundle names (e.g., 'bundle-100' not 'bundle-100.12')
    bundle_set = set()
    for name in bundle_names:
        # Strip sub-interface suffix if present
        base_name = name.split('.')[0] if '.' in name else name
        if base_name.lower().startswith('bundle'):
            bundle_set.add(base_name)
    
    if not bundle_set:
        return ""
    
    lines = config_text.split('\n')
    result_lines = []
    
    in_protocols = False
    in_lacp = False
    current_bundle = None
    current_block = []
    found_bundles = set()
    
    for line in lines:
        stripped = line.strip()
        current_indent = len(line) - len(line.lstrip())
        
        # Detect protocols section
        if stripped == 'protocols':
            in_protocols = True
            continue
        
        if not in_protocols:
            continue
        
        # End of protocols section
        if stripped == '!' and current_indent == 0:
            in_protocols = False
            continue
        
        # Detect lacp section
        if stripped == 'lacp' and current_indent == 2:
            in_lacp = True
            continue
        
        if not in_lacp:
            continue
        
        # End of lacp section
        if stripped == '!' and current_indent == 2:
            if current_bundle and current_bundle in bundle_set and current_block:
                result_lines.extend(current_block)
                result_lines.append("    !")
                found_bundles.add(current_bundle)
            in_lacp = False
            current_bundle = None
            current_block = []
            continue
        
        # Interface definition within lacp
        if stripped.startswith('interface ') and current_indent == 4:
            # Save previous bundle if matched
            if current_bundle and current_bundle in bundle_set and current_block:
                result_lines.extend(current_block)
                result_lines.append("    !")
                found_bundles.add(current_bundle)
            
            current_bundle = stripped.replace('interface ', '').strip()
            current_block = [f"    interface {current_bundle}"]
            continue
        
        # End of interface block
        if stripped == '!' and current_indent == 4:
            if current_bundle and current_bundle in bundle_set and current_block:
                result_lines.extend(current_block)
                result_lines.append("    !")
                found_bundles.add(current_bundle)
            current_bundle = None
            current_block = []
            continue
        
        # Content within interface
        if current_bundle and current_block:
            current_block.append(line)
    
    if not result_lines:
        return ""
    
    # Wrap in protocols lacp hierarchy
    final_lines = [
        "protocols",
        "  lacp"
    ]
    final_lines.extend(result_lines)
    final_lines.append("  !")
    final_lines.append("!")
    
    return '\n'.join(final_lines)


def get_interface_config_block(config_text: str, interface_names: List[str]) -> str:
    """Extract the full configuration block for specified interfaces.
    
    Args:
        config_text: Full device configuration
        interface_names: List of interface names to extract
        
    Returns:
        Configuration block for those interfaces
    """
    lines = config_text.split('\n')
    result_lines = []
    
    in_interfaces_block = False
    current_interface = None
    current_block = []
    interface_set = set(interface_names)
    
    for line in lines:
        stripped = line.strip()
        current_indent = len(line) - len(line.lstrip())
        
        if stripped == 'interfaces':
            in_interfaces_block = True
            continue
        
        if not in_interfaces_block:
            continue
        
        # End of interfaces block
        if stripped == '!' and current_indent == 0:
            # Save current interface if matched
            if current_interface and current_interface in interface_set and current_block:
                result_lines.extend(current_block)
            in_interfaces_block = False
            continue
        
        # New interface definition at indent 2
        if current_indent == 2 and stripped and not stripped.startswith('!'):
            # Check if it's an interface (not an attribute)
            if not stripped.startswith(('admin-state', 'description', 'mtu', 'ipv4', 'ipv6', 'vlan', 'mpls')):
                # Save previous interface if it matched
                if current_interface and current_interface in interface_set and current_block:
                    result_lines.extend(current_block)
                
                current_interface = stripped
                current_block = [f"  {stripped}"]
                continue
        
        # End of current interface
        if stripped == '!' and current_indent == 2:
            if current_interface and current_interface in interface_set:
                current_block.append("  !")
                result_lines.extend(current_block)
            current_interface = None
            current_block = []
            continue
        
        # Content within interface
        if current_interface and current_block:
            current_block.append(line)
    
    return '\n'.join(result_lines) if result_lines else ""


def show_interface_mapping(interfaces: List[str], service_count: int, prefix: str = "FXC-"):
    """Display interface to service mapping.
    
    Args:
        interfaces: List of interface names
        service_count: Number of services
        prefix: Service name prefix
    """
    console.print("\n[bold cyan]Interface to Service Mapping:[/bold cyan]")
    
    mapping_count = min(len(interfaces), service_count)
    
    # Create table
    table = Table(box=box.SIMPLE)
    table.add_column("#", style="dim", width=5)
    table.add_column("Interface", style="cyan")
    table.add_column("→", style="dim", width=3)
    table.add_column("Service", style="green")
    
    # Show first 15 and last 5 if there are many
    if mapping_count <= 20:
        for i in range(mapping_count):
            table.add_row(str(i+1), interfaces[i], "→", f"{prefix}{i+1}")
    else:
        for i in range(10):
            table.add_row(str(i+1), interfaces[i], "→", f"{prefix}{i+1}")
        table.add_row("...", "...", "", "...")
        for i in range(mapping_count - 5, mapping_count):
            table.add_row(str(i+1), interfaces[i], "→", f"{prefix}{i+1}")
    
    console.print(table)
    
    if len(interfaces) > service_count:
        console.print(f"[yellow]⚠ {len(interfaces) - service_count} interfaces will not be attached (not enough services)[/yellow]")
    elif service_count > len(interfaces):
        console.print(f"[yellow]⚠ {service_count - len(interfaces)} services will have no interface attached[/yellow]")


# =====================================================================
# Main configure_interfaces function - imported from main module
# =====================================================================

def configure_interfaces(*args, **kwargs):
    """Configure interfaces hierarchy.
    
    This function is implemented in the main module for backward compatibility.
    It is re-exported here for module organization.
    """
    # Late import to avoid circular dependencies
    from ..interactive_scale import configure_interfaces as _configure_interfaces
    return _configure_interfaces(*args, **kwargs)


def _configure_single_interface_type(*args, **kwargs):
    """Configure a single interface type.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import _configure_single_interface_type as _impl
    return _impl(*args, **kwargs)

