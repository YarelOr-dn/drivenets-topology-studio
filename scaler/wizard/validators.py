"""
Validation Functions for the SCALER Wizard.

This module contains:
- DNOS platform limit validation
- ESI format validation
- FXC attachment validation
"""

import re
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

# DNOS Platform Limits (loaded from limits.json)
_DNOS_LIMITS = None


def get_dnos_limits() -> Dict[str, Any]:
    """Load DNOS platform limits from limits.json."""
    global _DNOS_LIMITS
    if _DNOS_LIMITS is None:
        limits_path = Path(__file__).parent.parent.parent / "limits.json"
        try:
            with open(limits_path, 'r') as f:
                data = json.load(f)
                _DNOS_LIMITS = data.get('dnos_platform_limits', {})
        except (FileNotFoundError, json.JSONDecodeError):
            # Fallback defaults
            _DNOS_LIMITS = {
                "multihoming": {"max_esi_interfaces": 2000},
                "interfaces": {"max_pwhe": 4096},
                "services": {"max_fxc_instances": 8000, "max_evpn_instances": 4000},
                "bgp": {"max_peers": 2000}
            }
    return _DNOS_LIMITS


def get_limit(category: str, limit_name: str, default: int = 0) -> int:
    """Get a specific DNOS limit value."""
    limits = get_dnos_limits()
    return limits.get(category, {}).get(limit_name, default)


def validate_dnos_limits(
    pwhe_count: int = 0,
    fxc_count: int = 0,
    evpn_count: int = 0,
    bgp_peer_count: int = 0,
    mh_interface_count: int = 0,
    show_warnings: bool = True
) -> Dict[str, Dict[str, Any]]:
    """
    Validate configuration against DNOS platform limits.
    
    Args:
        pwhe_count: Number of PWHE interfaces
        fxc_count: Number of FXC service instances
        evpn_count: Number of EVPN instances
        bgp_peer_count: Number of BGP peers
        mh_interface_count: Number of multihoming interfaces with ESI
        show_warnings: Whether to print warnings to console
    
    Returns:
        Dict with validation results: {limit_name: {value, max, exceeded, message}}
    """
    results = {}
    
    # Check each limit
    checks = [
        ("PWHE Interfaces", pwhe_count, get_limit("interfaces", "max_pwhe", 4096), "interfaces.max_pwhe"),
        ("FXC Instances", fxc_count, get_limit("services", "max_fxc_instances", 8000), "services.max_fxc_instances"),
        ("EVPN Instances", evpn_count, get_limit("services", "max_evpn_instances", 4000), "services.max_evpn_instances"),
        ("BGP Peers", bgp_peer_count, get_limit("bgp", "max_peers", 2000), "bgp.max_peers"),
        ("MH ESI Interfaces", mh_interface_count, get_limit("multihoming", "max_esi_interfaces", 2000), "multihoming.max_esi_interfaces"),
    ]
    
    for name, value, max_val, limit_key in checks:
        if value > 0:
            exceeded = value > max_val
            pct = (value / max_val * 100) if max_val > 0 else 0
            
            results[limit_key] = {
                "name": name,
                "value": value,
                "max": max_val,
                "exceeded": exceeded,
                "percentage": pct,
                "message": f"{name}: {value:,}/{max_val:,} ({pct:.0f}%)"
            }
            
            if show_warnings and exceeded:
                console.print(f"[bold red]⚠ DNOS LIMIT EXCEEDED: {name}[/bold red]")
                console.print(f"  [yellow]Current: {value:,} | Max: {max_val:,} | Over by: {value - max_val:,}[/yellow]")
            elif show_warnings and pct >= 90:
                console.print(f"[yellow]⚠ DNOS LIMIT WARNING: {name} at {pct:.0f}% capacity[/yellow]")
                console.print(f"  [dim]Current: {value:,} | Max: {max_val:,}[/dim]")
    
    return results


def show_dnos_limits_summary(results: Dict[str, Dict[str, Any]]):
    """Display a summary table of DNOS limit validations."""
    if not results:
        return
    
    table = Table(title="DNOS Platform Limits", box=box.ROUNDED)
    table.add_column("Resource", style="cyan")
    table.add_column("Current", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Usage", justify="right")
    table.add_column("Status", width=12)
    
    for limit_key, data in results.items():
        pct = data["percentage"]
        
        # Usage bar
        filled = int(pct / 10)
        bar = "▓" * filled + "░" * (10 - filled)
        
        # Status with color
        if data["exceeded"]:
            status = "[bold red]✗ EXCEEDED[/bold red]"
            bar_color = "red"
        elif pct >= 90:
            status = "[yellow]⚠ WARNING[/yellow]"
            bar_color = "yellow"
        elif pct >= 75:
            status = "[cyan]○ HIGH[/cyan]"
            bar_color = "cyan"
        else:
            status = "[green]✓ OK[/green]"
            bar_color = "green"
        
        table.add_row(
            data["name"],
            f"{data['value']:,}",
            f"{data['max']:,}",
            f"[{bar_color}]{bar}[/{bar_color}] {pct:.0f}%",
            status
        )
    
    console.print(table)


def validate_esi_format(esi: str) -> bool:
    """
    Validate ESI format: 9 octets in XX:XX:XX:XX:XX:XX:XX:XX:XX format.
    
    Returns True if valid, False otherwise.
    """
    pattern = r'^([0-9a-fA-F]{2}:){8}[0-9a-fA-F]{2}$'
    return bool(re.match(pattern, esi))


def validate_fxc_attachment(
    interfaces: List[str], 
    interfaces_per_service: int,
    service_count: int
) -> Tuple[bool, str, List[List[str]]]:
    """Validate FXC interface attachment and create service-to-interface mapping.
    
    Rules:
    1. Only sub-interfaces (with '.') allowed - reject parent interfaces
    2. Supports: phX.Y (PWHE), ge*/bundle*.Y (physical/bundle with l2-service)
    3. All interfaces in same service must share same parent
    4. Sufficient interfaces for requested service count
    
    Args:
        interfaces: List of interfaces to attach (can include mixed types, will be filtered)
        interfaces_per_service: Number of interfaces per service (1, 2, or more)
        service_count: Number of services to create
        
    Returns:
        Tuple of (is_valid, error_message, mapping)
        mapping is list of interface lists, one per service
    """
    # Filter to only sub-interfaces (any type with '.')
    valid_subs = [i for i in interfaces if '.' in i]
    
    if not valid_subs:
        # Check if user provided parent interfaces by mistake
        invalid_parents = [i for i in interfaces if '.' not in i]
        if invalid_parents:
            return False, f"Parent interfaces not allowed for FXC. Found: {', '.join(invalid_parents[:5])}. Use sub-interfaces instead.", []
        return False, "No sub-interfaces found. FXC requires sub-interfaces (phX.Y, ge*.Y, bundle*.Y).", []
    
    # Check if we have enough interfaces
    required = service_count * interfaces_per_service
    if len(valid_subs) < required:
        return False, f"Not enough interfaces. Need {required} ({service_count} services × {interfaces_per_service}), have {len(valid_subs)}.", []
    
    # Group by parent (for any interface type)
    grouped = {}
    for iface in valid_subs:
        parent = iface.rsplit('.', 1)[0]
        grouped.setdefault(parent, []).append(iface)
    
    # Sort function that handles different interface types
    def parent_sort_key(parent: str) -> tuple:
        # PWHE: ph1 -> (0, 1)
        if parent.lower().startswith('ph'):
            try:
                return (0, int(parent[2:]))
            except ValueError:
                return (0, 0)
        # Bundle: bundle-ether1 -> (1, 1)
        elif 'bundle' in parent.lower():
            match = re.search(r'(\d+)', parent)
            return (1, int(match.group(1)) if match else 0)
        # Physical: ge100-6/0/0 -> (2, "ge100-6/0/0")
        else:
            return (2, parent)
    
    # Sort function for sub-interfaces - sort by VLAN number numerically
    def subif_sort_key(iface: str) -> tuple:
        """Sort sub-interfaces numerically by VLAN ID."""
        if '.' in iface:
            parent, vlan = iface.rsplit('.', 1)
            try:
                return (parent, int(vlan))
            except ValueError:
                return (parent, 0)
        return (iface, 0)
    
    # Create the mapping, ensuring same-parent constraint
    mapping = []
    available_interfaces = []
    
    # Flatten grouped interfaces, keeping parent groups together
    for parent in sorted(grouped.keys(), key=parent_sort_key):
        available_interfaces.extend(sorted(grouped[parent], key=subif_sort_key))
    
    if interfaces_per_service == 1:
        # Simple 1:1 mapping, no parent constraint needed
        for i in range(min(service_count, len(available_interfaces))):
            mapping.append([available_interfaces[i]])
    else:
        # Need to respect same-parent constraint
        services_created = 0
        
        for parent in sorted(grouped.keys(), key=parent_sort_key):
            subs = sorted(grouped[parent], key=subif_sort_key)
            sub_idx = 0
            while sub_idx + interfaces_per_service <= len(subs) and services_created < service_count:
                service_ifaces = subs[sub_idx:sub_idx + interfaces_per_service]
                mapping.append(service_ifaces)
                sub_idx += interfaces_per_service
                services_created += 1
        
        if services_created < service_count:
            return False, f"Cannot create {service_count} services with {interfaces_per_service} interfaces each from same parent. Created {services_created}. Consider reducing interfaces per service.", mapping
    
    return True, "", mapping

