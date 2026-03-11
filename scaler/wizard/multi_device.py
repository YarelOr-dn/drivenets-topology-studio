"""
Multi-Device Context and Operations for the SCALER Wizard.

This module contains:
- DeviceSummary: Parsed device summary class
- MultiDeviceContext: Context for multi-device operations
- Device selection functions
- Quick load menu
- Multi-device comparison and sync functions
"""

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box

from .parsers import parse_route_targets, parse_existing_multihoming
from .validators import validate_dnos_limits

console = Console()


class DeviceSummary:
    """Parsed device summary from running config header."""
    
    def __init__(self):
        # System info
        self.dnos_version: str = ""
        self.system_type: str = ""
        self.serial_number: str = ""
        self.mgmt_ip: str = ""
        self.uptime: str = ""
        self.ncc_status: str = ""
        self.ncp_status: str = ""
        
        # Routing info
        self.igp: str = ""
        self.bgp_asn: int = 0
        self.bgp_peers_up: int = 0
        self.bgp_peers_total: int = 0
        self.label_protocol: str = ""
        
        # Interfaces
        self.total_interfaces: int = 0
        self.interfaces_up: int = 0
        self.pwhe_parent: int = 0
        self.pwhe_sub: int = 0
        self.pwhe_up: int = 0
        
        # Services: type -> (up_count, total_count, transport_type)
        self.services: Dict[str, Tuple[int, int, str]] = {}


class MultiDeviceContext:
    """Context for synchronized multi-device configuration."""
    
    def __init__(self, devices: List):
        self.devices = devices
        self.configs: Dict[str, str] = {}  # hostname -> running config
        self.loopbacks: Dict[str, str] = {}  # hostname -> loopback IP
        self.route_targets: Dict[str, set] = {}  # hostname -> set of RTs
        self.interfaces: Dict[str, List[str]] = {}  # hostname -> interface list
        self.mh_config: Dict[str, dict] = {}  # hostname -> interface->ESI map
        self.bgp_asn: Dict[str, int] = {}  # hostname -> BGP ASN
        self.summaries: Dict[str, DeviceSummary] = {}  # hostname -> parsed summary
        self.bgp_peers: Dict[str, List[str]] = {}  # hostname -> list of peer IPs
        
    def discover_all(self):
        """Discover configuration from all devices."""
        for dev in self.devices:
            config_path = f"db/configs/{dev.hostname}/running.txt"
            try:
                with open(config_path, 'r') as f:
                    config = f.read()
                    self.configs[dev.hostname] = config
                    self._parse_device_info(dev.hostname, config)
                    self._parse_config_header(dev.hostname, config)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load config for {dev.hostname}: {e}[/yellow]")
    
    def _parse_config_header(self, hostname: str, config: str):
        """Parse the config header summary for quick stats."""
        summary = DeviceSummary()
        
        # Extract DNOS version
        dnos_match = re.search(r'#\s*•\s*DNOS:\s*(.+)', config)
        if dnos_match:
            summary.dnos_version = dnos_match.group(1).strip()
        
        # Extract system type
        type_match = re.search(r'#\s*•\s*Type:\s*(.+)', config)
        if type_match:
            summary.system_type = type_match.group(1).strip()
        
        # Extract serial number
        serial_match = re.search(r'#\s*•\s*Serial:\s*(.+)', config)
        if serial_match:
            summary.serial_number = serial_match.group(1).strip()
        
        # Extract management IP
        mgmt_ip_match = re.search(r'#\s*•\s*Mgmt IP:\s*(.+)', config)
        if mgmt_ip_match:
            summary.mgmt_ip = mgmt_ip_match.group(1).strip()
        
        # Extract uptime
        uptime_match = re.search(r'#\s*•\s*Uptime:\s*(.+)', config)
        if uptime_match:
            summary.uptime = uptime_match.group(1).strip()
        
        # Extract NCC/NCP status
        ncc_match = re.search(r'#\s*•\s*NCC:\s*(.+)', config)
        if ncc_match:
            summary.ncc_status = ncc_match.group(1).strip()
        
        ncp_match = re.search(r'#\s*•\s*NCP:\s*(.+)', config)
        if ncp_match:
            summary.ncp_status = ncp_match.group(1).strip()
        
        # Extract IGP type
        igp_match = re.search(r'#\s*•\s*IGP:\s*(.+)', config)
        if igp_match:
            summary.igp = igp_match.group(1).strip()
        
        # Extract BGP info from header
        bgp_header_match = re.search(r'#\s*•\s*BGP:\s*AS\s*(\d+),?\s*(\d+)/(\d+)\s*peers?\s*(UP)?', config)
        if bgp_header_match:
            summary.bgp_asn = int(bgp_header_match.group(1))
            summary.bgp_peers_up = int(bgp_header_match.group(2))
            summary.bgp_peers_total = int(bgp_header_match.group(3))
        
        # Extract label protocol
        label_match = re.search(r'#\s*•\s*Label Protocol:\s*(.+)', config)
        if label_match:
            summary.label_protocol = label_match.group(1).strip()
        
        # Extract PWHE info
        pwhe_match = re.search(r'#\s*•\s*PWHE:\s*(\d+)\s*parent\s*\+\s*(\d+)\s*sub-interfaces\s*\((\d+)\s*UP\)', config)
        if pwhe_match:
            summary.pwhe_parent = int(pwhe_match.group(1))
            summary.pwhe_sub = int(pwhe_match.group(2))
            summary.pwhe_up = int(pwhe_match.group(3))
        
        # Extract services
        system_components = {'NCC', 'NCP', 'NCF', 'NCA'}
        service_pattern = r'#\s*•\s*(\w+):\s*(\d+)/(\d+)\s*UP\s*\(([^)]+)\)'
        for match in re.finditer(service_pattern, config):
            svc_type = match.group(1)
            if svc_type in system_components:
                continue
            svc_up = int(match.group(2))
            svc_total = int(match.group(3))
            svc_transport = match.group(4)
            summary.services[svc_type] = (svc_up, svc_total, svc_transport)
        
        # Extract total interfaces
        total_match = re.search(r'#\s*•\s*Total:\s*(\d+)\s*configured\s*/\s*(\d+)\s*UP', config)
        if total_match:
            summary.total_interfaces = int(total_match.group(1))
            summary.interfaces_up = int(total_match.group(2))
        
        self.summaries[hostname] = summary
    
    def _parse_device_info(self, hostname: str, config: str):
        """Parse device configuration for cross-referencing."""
        # Extract loopback IP
        lo_match = re.search(r'lo0\s*\n\s*.*?\n\s*ipv4-address\s+(\d+\.\d+\.\d+\.\d+)', config)
        if lo_match:
            self.loopbacks[hostname] = lo_match.group(1)
        
        # Extract BGP ASN
        asn_match = re.search(r'bgp\s+(\d+)\s*\n', config)
        if asn_match:
            self.bgp_asn[hostname] = int(asn_match.group(1))
        
        # Extract BGP peers
        peer_pattern = r'neighbor\s+(\d+\.\d+\.\d+\.\d+)\s*\n\s*remote-as'
        self.bgp_peers[hostname] = re.findall(peer_pattern, config)
        
        # Extract route-targets
        self.route_targets[hostname] = parse_route_targets(config)
        
        # Extract multihoming config
        self.mh_config[hostname] = parse_existing_multihoming(config)
        
        # Extract PWHE/L2 interfaces
        iface_pattern = r'interface\s+(ph\d+\.?\d*|[gx]e[\d\-/]+\.\d+)'
        self.interfaces[hostname] = list(set(re.findall(iface_pattern, config)))
    
    def get_peer_suggestions(self, current_hostname: str) -> List[Dict]:
        """Get BGP peer suggestions based on other devices."""
        suggestions = []
        for dev in self.devices:
            if dev.hostname == current_hostname:
                continue
            if dev.hostname in self.loopbacks:
                suggestions.append({
                    'hostname': dev.hostname,
                    'ip': self.loopbacks[dev.hostname],
                    'asn': self.bgp_asn.get(dev.hostname, 0),
                    'shared_rts': len(self.route_targets.get(current_hostname, set()) & 
                                     self.route_targets.get(dev.hostname, set()))
                })
        return suggestions
    
    def get_shared_evpn_peers(self) -> List[Tuple[str, str, int]]:
        """Get pairs of devices that share EVPN RTs."""
        pairs = []
        hostnames = [d.hostname for d in self.devices]
        for i, h1 in enumerate(hostnames):
            for h2 in hostnames[i+1:]:
                shared = len(self.route_targets.get(h1, set()) & 
                            self.route_targets.get(h2, set()))
                if shared > 0:
                    pairs.append((h1, h2, shared))
        return pairs
    
    def validate_all_limits(self, show_table: bool = True) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Validate DNOS platform limits for all devices."""
        all_results = {}
        any_exceeded = False
        
        for dev in self.devices:
            h = dev.hostname
            summary = self.summaries.get(h, DeviceSummary())
            
            # Count resources
            pwhe_count = len([i for i in self.interfaces.get(h, []) if re.match(r'^ph\d+', i)])
            mh_count = len(self.mh_config.get(h, {}))
            bgp_peer_count = len(self.bgp_peers.get(h, []))
            
            # Get FXC/EVPN counts from summary
            fxc_count = summary.services.get('FXC', (0, 0, ''))[1]
            evpn_count = len(self.route_targets.get(h, set()))
            
            # Validate without printing
            results = validate_dnos_limits(
                pwhe_count=pwhe_count,
                fxc_count=fxc_count,
                evpn_count=evpn_count,
                bgp_peer_count=bgp_peer_count,
                mh_interface_count=mh_count,
                show_warnings=False
            )
            
            all_results[h] = results
            
            # Check if any limit exceeded
            for limit_data in results.values():
                if limit_data.get('exceeded'):
                    any_exceeded = True
        
        # Show combined table
        if show_table and all_results:
            self._show_limits_table(all_results, any_exceeded)
        
        return all_results
    
    def _show_limits_table(self, all_results: Dict, any_exceeded: bool):
        """Display a combined limits table for all devices."""
        all_limits = set()
        for device_results in all_results.values():
            all_limits.update(device_results.keys())
        
        if not all_limits:
            return
        
        table = Table(
            title="[bold]DNOS Platform Limits Validation[/bold]" + 
                  (" [red]⚠ LIMITS EXCEEDED[/red]" if any_exceeded else " [green]✓ ALL OK[/green]"),
            box=box.ROUNDED
        )
        table.add_column("Resource", style="cyan", width=20)
        
        for dev in self.devices:
            table.add_column(dev.hostname, justify="center", width=20)
        
        table.add_column("Max", justify="right", width=10)
        
        limit_order = [
            ("multihoming.max_esi_interfaces", "MH ESI Interfaces"),
            ("interfaces.max_pwhe", "PWHE Interfaces"),
            ("services.max_fxc_instances", "FXC Instances"),
            ("services.max_evpn_instances", "EVPN/RTs"),
            ("bgp.max_peers", "BGP Peers"),
        ]
        
        for limit_key, display_name in limit_order:
            row = [display_name]
            max_val = 0
            
            for dev in self.devices:
                h = dev.hostname
                data = all_results.get(h, {}).get(limit_key)
                
                if data:
                    max_val = data['max']
                    pct = data['percentage']
                    value = data['value']
                    
                    if data['exceeded']:
                        cell = f"[bold red]{value:,} ✗[/bold red]"
                    elif pct >= 90:
                        cell = f"[yellow]{value:,} ⚠[/yellow]"
                    elif pct >= 75:
                        cell = f"[cyan]{value:,}[/cyan]"
                    else:
                        cell = f"[green]{value:,} ✓[/green]"
                    row.append(cell)
                else:
                    row.append("[dim]-[/dim]")
            
            row.append(f"{max_val:,}" if max_val > 0 else "-")
            table.add_row(*row)
        
        console.print(table)
        
        if any_exceeded:
            console.print("\n[bold red]⚠ Some limits are exceeded! Configuration may fail.[/bold red]")
            console.print("[dim]Check device capabilities and reduce scale if needed.[/dim]")


def select_multiple_devices(dm) -> Optional[List]:
    """Select multiple devices for synchronized configuration.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import select_multiple_devices as _impl
    return _impl(dm)


def show_quick_load_menu(*args, **kwargs):
    """Show quick load menu for device configuration history.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import show_quick_load_menu as _impl
    return _impl(*args, **kwargs)


def _show_multi_device_compare(*args, **kwargs):
    """Compare configurations between devices in multi-device mode.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import _show_multi_device_compare as _impl
    return _impl(*args, **kwargs)


def _refresh_multi_device_configs(*args, **kwargs):
    """Refresh running configurations from all devices.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import _refresh_multi_device_configs as _impl
    return _impl(*args, **kwargs)


def _show_multi_device_sync_status(*args, **kwargs):
    """Show detailed synchronization status between devices.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import _show_multi_device_sync_status as _impl
    return _impl(*args, **kwargs)


def _push_config_to_all_devices(*args, **kwargs):
    """Push configuration to all devices.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import _push_config_to_all_devices as _impl
    return _impl(*args, **kwargs)


def _show_delete_files_menu(*args, **kwargs):
    """Show menu to delete config files.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import _show_delete_files_menu as _impl
    return _impl(*args, **kwargs)


# ==============================================================================
# SERVICE INTERFACE MODIFICATION OPERATIONS
# ==============================================================================

def parse_service_interfaces(config: str, service_type: str = 'evpn-vpws-fxc') -> Dict[str, List[str]]:
    """
    Parse services and their attached interfaces from config.
    
    Args:
        config: Running configuration text
        service_type: Type of service to parse (e.g., 'evpn-vpws-fxc')
    
    Returns:
        Dict of service_name -> list of interfaces
    """
    services = {}
    
    # Pattern to match service instances and their interfaces
    # Looking for: network-services evpn-vpws-fxc instance <name> ... interface <iface>
    service_pattern = rf'(?:network-services\s+)?{re.escape(service_type)}\s+instance\s+(\S+)'
    interface_pattern = r'interface\s+(ph\d+\.?\d*|[gx]e[\d\-/]+\.?\d*|bundle\d+\.?\d*)'
    
    # Find all service blocks
    lines = config.split('\n')
    current_service = None
    indent_level = 0
    
    for line in lines:
        # Check for service instance start
        service_match = re.search(service_pattern, line)
        if service_match:
            current_service = service_match.group(1)
            services[current_service] = []
            indent_level = len(line) - len(line.lstrip())
            continue
        
        if current_service:
            current_indent = len(line) - len(line.lstrip())
            
            # Check if we're still in the service block
            if current_indent <= indent_level and line.strip() and not line.strip().startswith('!'):
                current_service = None
                continue
            
            # Look for interface attachments
            iface_match = re.search(interface_pattern, line)
            if iface_match:
                services[current_service].append(iface_match.group(1))
    
    return services


def modify_service_interfaces(
    multi_ctx: 'MultiDeviceContext',
    operation: str,
    service_filter: str,
    interface_changes: Dict[str, Any],
    mapper: Optional[Any] = None,
    dry_run: bool = True
) -> Dict[str, Tuple[bool, str]]:
    """
    Modify interfaces attached to services across multiple devices at scale.
    
    Args:
        multi_ctx: MultiDeviceContext with devices to operate on
        operation: Operation type ('replace', 'add', 'remove', 'remap')
        service_filter: Service filter (e.g., 'FXC-*', 'all', or specific name)
        interface_changes: Operation-specific data:
            - replace: {'new_interfaces': ['ph1.1', 'ph2.1', ...]}
            - add: {'interfaces': ['ph100.1', 'ph101.1', ...]}
            - remove: {'interfaces': ['ph50.1', 'ph51.1', ...]}
            - remap: {'old_prefix': 'ph', 'new_prefix': 'bundle', 'offset': 0}
        mapper: Optional InterfaceMapper for multi-device interface translation
        dry_run: If True, only show what would be done
    
    Returns:
        Dict of hostname -> (success, message)
    """
    from ..config_pusher import ConfigPusher
    
    results = {}
    
    console.print(f"\n[bold cyan]Modify Service Interfaces[/bold cyan]")
    console.print(f"  Operation: [yellow]{operation}[/yellow]")
    console.print(f"  Filter: [cyan]{service_filter}[/cyan]")
    console.print(f"  Devices: {', '.join([d.hostname for d in multi_ctx.devices])}")
    
    for device in multi_ctx.devices:
        hostname = device.hostname
        console.print(f"\n[cyan]► {hostname}[/cyan]")
        
        config = multi_ctx.configs.get(hostname, "")
        
        # Parse current service interfaces
        current_services = parse_service_interfaces(config)
        
        # Filter services
        matched_services = _filter_services(current_services, service_filter)
        
        if not matched_services:
            results[hostname] = (False, "No matching services found")
            console.print(f"  [yellow]No services match filter '{service_filter}'[/yellow]")
            continue
        
        console.print(f"  [dim]Matched {len(matched_services)} services[/dim]")
        
        # Generate commands based on operation
        commands = _generate_interface_change_commands(
            matched_services,
            operation,
            interface_changes,
            hostname,
            mapper
        )
        
        if not commands:
            results[hostname] = (True, "No changes needed")
            console.print(f"  [dim]No changes needed[/dim]")
            continue
        
        console.print(f"  [dim]{len(commands)} commands to execute[/dim]")
        
        if dry_run:
            # Just show commands
            for cmd in commands[:5]:
                console.print(f"    [yellow]{cmd}[/yellow]")
            if len(commands) > 5:
                console.print(f"    [dim]... and {len(commands) - 5} more[/dim]")
            results[hostname] = (True, f"Would execute {len(commands)} commands")
        else:
            # Execute commands
            pusher = ConfigPusher()
            success, message, _ = pusher.run_cli_commands(device, commands, dry_run=False)
            results[hostname] = (success, message)
            
            if success:
                console.print(f"  [green]✓ {message}[/green]")
            else:
                console.print(f"  [red]✗ {message}[/red]")
    
    return results


def _filter_services(services: Dict[str, List[str]], filter_pattern: str) -> Dict[str, List[str]]:
    """Filter services by name pattern."""
    if filter_pattern.lower() == 'all':
        return services
    
    if '*' in filter_pattern:
        # Wildcard pattern
        pattern = filter_pattern.replace('*', '.*')
        regex = re.compile(f'^{pattern}$', re.IGNORECASE)
        return {k: v for k, v in services.items() if regex.match(k)}
    else:
        # Exact match
        if filter_pattern in services:
            return {filter_pattern: services[filter_pattern]}
        return {}


def _generate_interface_change_commands(
    services: Dict[str, List[str]],
    operation: str,
    changes: Dict[str, Any],
    hostname: str,
    mapper: Optional[Any]
) -> List[str]:
    """Generate CLI commands for interface changes."""
    commands = []
    
    if operation == 'replace':
        new_interfaces = changes.get('new_interfaces', [])
        if mapper:
            new_interfaces = mapper.get_all_interfaces_for_device(new_interfaces, hostname)
        
        for service_name, current_ifaces in services.items():
            # Remove all current interfaces
            for iface in current_ifaces:
                commands.append(f"network-services evpn-vpws-fxc instance {service_name}")
                commands.append(f"no interface {iface}")
            
            # Add new interfaces (up to matching count)
            for i, iface in enumerate(new_interfaces[:len(current_ifaces)]):
                commands.append(f"network-services evpn-vpws-fxc instance {service_name}")
                commands.append(f"interface {iface}")
    
    elif operation == 'add':
        interfaces_to_add = changes.get('interfaces', [])
        if mapper:
            interfaces_to_add = mapper.get_all_interfaces_for_device(interfaces_to_add, hostname)
        
        for service_name in services:
            for iface in interfaces_to_add:
                commands.append(f"network-services evpn-vpws-fxc instance {service_name}")
                commands.append(f"interface {iface}")
    
    elif operation == 'remove':
        interfaces_to_remove = changes.get('interfaces', [])
        if mapper:
            interfaces_to_remove = mapper.get_all_interfaces_for_device(interfaces_to_remove, hostname)
        
        for service_name, current_ifaces in services.items():
            for iface in interfaces_to_remove:
                if iface in current_ifaces:
                    commands.append(f"network-services evpn-vpws-fxc instance {service_name}")
                    commands.append(f"no interface {iface}")
    
    elif operation == 'remap':
        old_prefix = changes.get('old_prefix', 'ph')
        new_prefix = changes.get('new_prefix', 'bundle')
        offset = changes.get('offset', 0)
        
        for service_name, current_ifaces in services.items():
            for iface in current_ifaces:
                if iface.startswith(old_prefix):
                    # Extract number and create new interface name
                    match = re.match(rf'^{re.escape(old_prefix)}(\d+)(.*)', iface)
                    if match:
                        num = int(match.group(1)) + offset
                        suffix = match.group(2)
                        new_iface = f"{new_prefix}{num}{suffix}"
                        
                        # Remove old, add new
                        commands.append(f"network-services evpn-vpws-fxc instance {service_name}")
                        commands.append(f"no interface {iface}")
                        commands.append(f"network-services evpn-vpws-fxc instance {service_name}")
                        commands.append(f"interface {new_iface}")
    
    return commands


def _prompt_int_with_back(prompt_text: str, default: int, allow_back: bool = True) -> Optional[int]:
    """
    Prompt for an integer value with [B] back support.
    
    Returns:
        Integer value if entered, None if user pressed back
    """
    while True:
        hint = f" [B]ack" if allow_back else ""
        raw = Prompt.ask(f"{prompt_text}{hint}", default=str(default))
        
        if allow_back and raw.lower() == 'b':
            return None
        
        try:
            return int(raw)
        except ValueError:
            console.print(f"[yellow]Please enter a number{' or B for back' if allow_back else ''}[/yellow]")


def _detect_interfaces_from_config(config_text: str) -> Dict[str, Dict]:
    """
    Detect and categorize interfaces from configuration text.
    
    Returns dict with interface types and their details:
    {
        'pwhe': {'parents': [...], 'subs': [...], 'count': N},
        'bundle': {'interfaces': [...], 'count': N},
        'l2ac': {'interfaces': [...], 'count': N},
        'physical': {'interfaces': [...], 'count': N},
        'loopback': {'interfaces': [...], 'count': N},
    }
    """
    import re
    
    result = {
        'pwhe_parent': {'interfaces': [], 'count': 0, 'icon': '🔗', 'name': 'PWHE Parents (phX)'},
        'pwhe_sub': {'interfaces': [], 'count': 0, 'icon': '🔗', 'name': 'PWHE Sub-interfaces (phX.Y)'},
        'bundle': {'interfaces': [], 'count': 0, 'icon': '📦', 'name': 'Bundle Interfaces'},
        'l2ac': {'interfaces': [], 'count': 0, 'icon': '🔌', 'name': 'L2-AC Interfaces'},
        'physical_sub': {'interfaces': [], 'count': 0, 'icon': '📡', 'name': 'Physical Sub-interfaces'},
        'physical_parent': {'interfaces': [], 'count': 0, 'icon': '🔧', 'name': 'Physical Parents'},
        'loopback': {'interfaces': [], 'count': 0, 'icon': '🔄', 'name': 'Loopback Interfaces'},
        'mgmt': {'interfaces': [], 'count': 0, 'icon': '⚙️', 'name': 'Management Interfaces'},
    }
    
    # Parse interfaces section
    in_interfaces = False
    current_iface = None
    current_iface_has_l2 = False
    
    for line in config_text.split('\n'):
        stripped = line.rstrip()
        
        # Detect interfaces section
        if stripped == 'interfaces':
            in_interfaces = True
            continue
        
        # End of interfaces section (new top-level)
        if in_interfaces and stripped and not stripped.startswith(' ') and stripped != '!':
            in_interfaces = False
            continue
        
        if not in_interfaces:
            continue
        
        # Interface definition (2-space indent, no 'interface' keyword in DNOS)
        iface_match = re.match(r'^  (\S+)$', line)
        if iface_match:
            # Save previous interface
            if current_iface:
                _categorize_interface(current_iface, current_iface_has_l2, result)
            
            current_iface = iface_match.group(1)
            current_iface_has_l2 = False
            continue
        
        # Check for l2-service enabled
        if current_iface and 'l2-service enabled' in stripped:
            current_iface_has_l2 = True
    
    # Don't forget last interface
    if current_iface:
        _categorize_interface(current_iface, current_iface_has_l2, result)
    
    # Update counts
    for itype in result:
        result[itype]['count'] = len(result[itype]['interfaces'])
    
    return result


def _categorize_interface(iface_name: str, has_l2: bool, result: Dict) -> None:
    """Categorize a single interface into the result dict."""
    import re
    
    # PWHE interfaces (ph*)
    if iface_name.startswith('ph'):
        if '.' in iface_name:
            result['pwhe_sub']['interfaces'].append(iface_name)
        else:
            result['pwhe_parent']['interfaces'].append(iface_name)
    
    # Bundle interfaces
    elif iface_name.startswith('bundle'):
        result['bundle']['interfaces'].append(iface_name)
    
    # Loopback
    elif iface_name.startswith('lo'):
        result['loopback']['interfaces'].append(iface_name)
    
    # Management
    elif iface_name.startswith(('mgmt', 'ipmi')):
        result['mgmt']['interfaces'].append(iface_name)
    
    # Physical interfaces (ge*, xe*, et*, ce*, etc.)
    elif re.match(r'^(ge|xe|et|ce|oe|qsfp|cfp|sfp)', iface_name):
        if '.' in iface_name:
            # Sub-interface
            if has_l2:
                result['l2ac']['interfaces'].append(iface_name)
            else:
                result['physical_sub']['interfaces'].append(iface_name)
        else:
            result['physical_parent']['interfaces'].append(iface_name)
    
    # Generic sub-interface check
    elif '.' in iface_name:
        if has_l2:
            result['l2ac']['interfaces'].append(iface_name)
        else:
            result['physical_sub']['interfaces'].append(iface_name)


def show_modify_service_interfaces_menu(
    multi_ctx: 'MultiDeviceContext',
    mapper: Optional[Any] = None,
    auto_refresh: bool = False
) -> bool:
    """
    Interactive menu for modifying service interfaces.
    
    IMPROVED FLOW:
    1. (Optional) Check config age and offer refresh
    2. Detect interfaces from config and show by TYPE
    3. Let user select which interface type to modify
    4. Then select operation (Replace/Add/Remove/Remap/VLAN)
    
    Args:
        multi_ctx: MultiDeviceContext
        mapper: Optional InterfaceMapper for translation
    
    Returns:
        True if modifications were made
    """
    import re
    from collections import defaultdict
    from datetime import datetime, timedelta
    from rich.table import Table
    
    console.print("\n[bold cyan]━━━ Modify Interfaces ━━━[/bold cyan]")
    console.print("[dim]Modify interfaces by type - add, remove, replace, or remap[/dim]")
    
    # Get config from device
    config_text = ""
    device_name = "unknown"
    dev = None
    if multi_ctx and multi_ctx.devices:
        dev = multi_ctx.devices[0]
        device_name = dev.hostname
        config_text = multi_ctx.configs.get(dev.hostname, "")
        
        # Check config age and offer quick refresh
        if dev.last_sync:
            age = datetime.now() - dev.last_sync
            if age > timedelta(minutes=5):
                age_str = f"{int(age.total_seconds() / 60)}m ago"
                console.print(f"\n[yellow]⚠ Config is {age_str} - may be stale[/yellow]")
                if Confirm.ask("Quick refresh from device?", default=True):
                    console.print("[dim]Refreshing...[/dim]")
                    try:
                        from ..config_extractor import InteractiveExtractor
                        extractor = InteractiveExtractor(dev.ip, dev.username, dev.password)
                        fresh_config = extractor.extract()
                        if fresh_config:
                            multi_ctx.configs[dev.hostname] = fresh_config
                            config_text = fresh_config
                            dev.last_sync = datetime.now()
                            console.print("[green]✓ Config refreshed[/green]")
                    except Exception as e:
                        console.print(f"[red]Refresh failed: {e}[/red]")
                        console.print("[dim]Using cached config[/dim]")
    
    if not config_text:
        console.print("[yellow]No configuration available. Please refresh config first.[/yellow]")
        return False
    
    # Step 1: Detect and show interface types
    console.print(f"\n[bold]Analyzing interfaces on {device_name}...[/bold]")
    
    iface_types = _detect_interfaces_from_config(config_text)
    
    # Build display table
    table = Table(title="Detected Interface Types", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Type", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Sample", style="dim")
    
    type_options = []
    idx = 1
    
    for itype, info in iface_types.items():
        if info['count'] > 0:
            sample = ', '.join(info['interfaces'][:3])
            if info['count'] > 3:
                sample += f"... (+{info['count'] - 3} more)"
            
            table.add_row(
                str(idx),
                f"{info['icon']} {info['name']}",
                f"{info['count']:,}",
                sample
            )
            type_options.append((itype, info))
            idx += 1
    
    if not type_options:
        console.print("[yellow]No interfaces found in configuration.[/yellow]")
        return False
    
    console.print()
    console.print(table)
    
    # Step 2: Select interface type
    console.print("\n[bold]Select Interface Type to Modify:[/bold]")
    for i, (itype, info) in enumerate(type_options, 1):
        console.print(f"  [{i}] {info['icon']} {info['name']} ({info['count']:,})")
    console.print()
    console.print("  [A] All interfaces")
    console.print("  [B] Back")
    
    valid_choices = [str(i) for i in range(1, len(type_options) + 1)] + ['a', 'A', 'b', 'B']
    type_choice = Prompt.ask("Select type", choices=valid_choices, default="b")
    
    if type_choice.lower() == 'b':
        return False
    
    # Determine selected interfaces
    if type_choice.lower() == 'a':
        selected_type = 'all'
        selected_interfaces = []
        for itype, info in type_options:
            selected_interfaces.extend(info['interfaces'])
        type_name = "All Interfaces"
    else:
        type_idx = int(type_choice) - 1
        selected_type, selected_info = type_options[type_idx]
        selected_interfaces = selected_info['interfaces']
        type_name = selected_info['name']
    
    console.print(f"\n[green]✓ Selected: {type_name} ({len(selected_interfaces):,} interfaces)[/green]")
    
    # Step 3: Select operation
    console.print("\n[bold]Select Operation:[/bold]")
    console.print("  [1] [green]Replace All[/green] - Replace with new interface names/numbers")
    console.print("  [2] [cyan]Add More[/cyan] - Add additional interfaces of same type")
    console.print("  [3] [yellow]Remove[/yellow] - Remove specific interfaces")
    console.print("  [4] [magenta]Remap[/magenta] - Change prefix (e.g., ph → bundle)")
    console.print("  [5] [blue]Modify VLANs[/blue] - Change VLAN tags on selected interfaces")
    console.print("  [B] Back")
    
    op_choice = Prompt.ask("Select operation", choices=["1", "2", "3", "4", "5", "b", "B"], default="b")
    
    if op_choice.lower() == 'b':
        return False
    
    # VLAN modification handled separately
    if op_choice == "5":
        return show_modify_vlans_menu(multi_ctx, selected_interfaces)
    
    op_map = {"1": "replace", "2": "add", "3": "remove", "4": "remap"}
    operation = op_map[op_choice]
    
    # Set service_filter based on selected type for downstream compatibility
    service_filter = selected_type if selected_type != 'all' else 'all'
    
    # Detect current prefix from selected interfaces
    current_prefix = ""
    if selected_interfaces:
        # Find common prefix
        first_iface = selected_interfaces[0]
        if first_iface.startswith('ph'):
            current_prefix = 'ph'
        elif first_iface.startswith('bundle'):
            current_prefix = 'bundle'
        elif '/' in first_iface:
            # Physical interface like ge400-0/0/4
            current_prefix = first_iface.rsplit('.', 1)[0] if '.' in first_iface else first_iface
        else:
            current_prefix = first_iface.split('.')[0] if '.' in first_iface else first_iface
    
    # Get operation-specific parameters
    if operation == 'replace':
        console.print("\n[bold]Replace Interfaces[/bold]")
        console.print(f"[dim]Current: {len(selected_interfaces):,} {type_name}[/dim]")
        
        # Show sample of current interfaces
        sample = selected_interfaces[:5]
        console.print(f"[dim]Sample: {', '.join(sample)}{'...' if len(selected_interfaces) > 5 else ''}[/dim]")
        
        console.print("\n[bold]Enter new interface specification:[/bold]")
        console.print("  [dim]New interfaces will replace the selected ones[/dim]")
        
        # Smart defaults based on selected type
        default_prefix = current_prefix if current_prefix else "ph"
        default_count = len(selected_interfaces)
        
        prefix_raw = Prompt.ask(f"New prefix [B]ack", default=default_prefix)
        if prefix_raw.lower() == 'b':
            return False
        prefix = prefix_raw
        
        start = _prompt_int_with_back("Start number", 1)
        if start is None:
            return False
        
        count = _prompt_int_with_back("Count", default_count)
        if count is None:
            return False
        
        # Generate sub-interface format based on prefix type
        if prefix.startswith('ph') or prefix.startswith('bundle'):
            new_interfaces = [f"{prefix}{i}.1" for i in range(start, start + count)]
        else:
            new_interfaces = [f"{prefix}.{i}" for i in range(start, start + count)]
        
        console.print(f"\n[green]Will replace {len(selected_interfaces):,} → {len(new_interfaces):,} interfaces[/green]")
        console.print(f"[dim]New: {', '.join(new_interfaces[:3])}...{new_interfaces[-1] if len(new_interfaces) > 3 else ''}[/dim]")
        
        changes = {'new_interfaces': new_interfaces, 'old_interfaces': selected_interfaces}
    
    elif operation == 'add':
        console.print("\n[bold]Add More Interfaces[/bold]")
        console.print(f"[dim]Current: {len(selected_interfaces):,} {type_name}[/dim]")
        
        # Find the highest number in current interfaces to suggest next
        import re
        max_num = 0
        for iface in selected_interfaces:
            # Extract numbers from interface name
            nums = re.findall(r'(\d+)', iface)
            if nums:
                max_num = max(max_num, max(int(n) for n in nums))
        
        default_start = max_num + 1 if max_num > 0 else 1
        default_prefix = current_prefix if current_prefix else "ph"
        
        console.print(f"[dim]Highest existing number: {max_num}[/dim]")
        
        prefix_raw = Prompt.ask(f"Prefix [B]ack", default=default_prefix)
        if prefix_raw.lower() == 'b':
            return False
        prefix = prefix_raw
        
        start = _prompt_int_with_back("Start number", default_start)
        if start is None:
            return False
        
        count = _prompt_int_with_back("How many to add", 10)
        if count is None:
            return False
        
        # Generate sub-interface format based on prefix type
        if prefix.startswith('ph') or prefix.startswith('bundle'):
            interfaces = [f"{prefix}{i}.1" for i in range(start, start + count)]
        else:
            interfaces = [f"{prefix}.{i}" for i in range(start, start + count)]
        
        console.print(f"\n[green]Will add {len(interfaces):,} new interfaces[/green]")
        console.print(f"[dim]New: {', '.join(interfaces[:3])}...{interfaces[-1] if len(interfaces) > 3 else ''}[/dim]")
        
        changes = {'interfaces': interfaces}
    
    elif operation == 'remove':
        # Use already-detected selected_interfaces from Step 1
        console.print("\n[bold]Remove Interfaces[/bold]")
        console.print(f"[dim]Selected type: {type_name} ({len(selected_interfaces):,} interfaces)[/dim]")
        
        # Allow further filtering within the selected type
        all_interfaces = selected_interfaces
        
        # Get config for WAN detection
        config_text = ""
        if multi_ctx and multi_ctx.devices:
            dev = multi_ctx.devices[0]
            config_text = multi_ctx.configs.get(dev.hostname, "")
        
        if not config_text:
            console.print("[yellow]No config available[/yellow]")
            return False
        
        # Parse interfaces from config - find all sub-interfaces with their descriptions
        import re
        from collections import defaultdict
        
        interface_groups = defaultdict(list)
        all_interfaces = []
        wan_interfaces = []
        non_wan_interfaces = []
        interface_descriptions = {}
        
        # Parse interfaces and their descriptions
        lines = config_text.split('\n')
        in_interfaces = False
        current_iface = None
        
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            
            if stripped == 'interfaces':
                in_interfaces = True
                continue
            if in_interfaces and indent == 0 and stripped and stripped != '!':
                in_interfaces = False
                current_iface = None
                continue
            
            # Interface definition at 2-space indent
            if in_interfaces and indent == 2 and stripped and not stripped.startswith('!'):
                if '.' in stripped:  # Sub-interface
                    current_iface = stripped
                    all_interfaces.append(current_iface)
                    
                    # Group by parent
                    parent = stripped.split('.')[0]
                    interface_groups[parent].append(current_iface)
                else:
                    current_iface = stripped
            
            # Check for description (4-space indent under interface)
            if in_interfaces and indent == 4 and current_iface and stripped.startswith('description '):
                desc = stripped[12:].strip().strip('"\'')
                interface_descriptions[current_iface] = desc
                
                # Categorize by WAN
                if 'wan' in desc.lower():
                    if current_iface in all_interfaces:
                        wan_interfaces.append(current_iface)
        
        # Build non-WAN list
        non_wan_interfaces = [iface for iface in all_interfaces if iface not in wan_interfaces]
        
        if not all_interfaces:
            console.print("[yellow]No sub-interfaces found in config[/yellow]")
            return False
        
        # Build categorized menu
        console.print("\n[bold cyan]Remove Interfaces - Select Category[/bold cyan]")
        console.print()
        
        # Sort groups by count (descending)
        sorted_groups = sorted(interface_groups.items(), key=lambda x: len(x[1]), reverse=True)
        
        options = []
        idx = 1
        
        # Show parent interface groups
        for parent, ifaces in sorted_groups[:5]:  # Show top 5
            sorted_ifaces = sorted(ifaces, key=lambda x: int(x.split('.')[-1]) if x.split('.')[-1].isdigit() else 0)
            first = sorted_ifaces[0].split('.')[-1] if sorted_ifaces else "?"
            last = sorted_ifaces[-1].split('.')[-1] if sorted_ifaces else "?"
            console.print(f"  [{idx}] {parent}.* ({len(ifaces):,} interfaces, .{first} to .{last})")
            options.append(('group', parent, sorted_ifaces))
            idx += 1
        
        console.print()
        
        # WAN/Non-WAN options
        if wan_interfaces:
            console.print(f"  [W] [yellow]WAN interfaces ONLY[/yellow] ({len(wan_interfaces):,} with 'WAN' in description)")
            options.append(('wan', None, wan_interfaces))
        
        if non_wan_interfaces:
            console.print(f"  [N] [green]Non-WAN interfaces[/green] ({len(non_wan_interfaces):,} without 'WAN' in description)")
            options.append(('non_wan', None, non_wan_interfaces))
        
        console.print()
        console.print(f"  [A] All sub-interfaces ({len(all_interfaces):,} total)")
        console.print("  [R] By range - e.g., 1-100,200,300-400")
        console.print("  [C] Custom pattern")
        console.print("  [B] Back")
        
        valid = [str(i) for i in range(1, len(sorted_groups[:5]) + 1)]
        if wan_interfaces:
            valid.extend(['w', 'W'])
        if non_wan_interfaces:
            valid.extend(['n', 'N'])
        valid.extend(['a', 'A', 'r', 'R', 'c', 'C', 'b', 'B'])
        
        choice = Prompt.ask("Select", choices=valid, default="b")
        
        if choice.lower() == 'b':
            return False
        
        interfaces = []
        
        if choice.lower() == 'a':
            interfaces = all_interfaces
        elif choice.lower() == 'w':
            interfaces = wan_interfaces
        elif choice.lower() == 'n':
            interfaces = non_wan_interfaces
        elif choice.lower() == 'r':
            # By range with comma/dash support
            console.print("\n[bold]Specify Range[/bold]")
            parent = Prompt.ask("Parent interface", default=sorted_groups[0][0] if sorted_groups else "ge400-0/0/4")
            console.print("[dim]Format: 1-100,200,300-400 (ranges and individual numbers)[/dim]")
            range_spec = Prompt.ask("Sub-interface numbers", default="1-100")
            
            # Parse range specification
            numbers = set()
            for part in range_spec.replace(' ', '').split(','):
                if '-' in part:
                    try:
                        start, end = part.split('-', 1)
                        numbers.update(range(int(start), int(end) + 1))
                    except ValueError:
                        console.print(f"[yellow]Invalid range: {part}[/yellow]")
                else:
                    try:
                        numbers.add(int(part))
                    except ValueError:
                        console.print(f"[yellow]Invalid number: {part}[/yellow]")
            
            interfaces = [f"{parent}.{n}" for n in sorted(numbers)]
        elif choice.lower() == 'c':
            # Custom pattern
            console.print("\n[bold]Enter Custom Pattern[/bold]")
            console.print("[dim]Format: prefix start count (e.g., 'ge400-0/0/4. 1 100') or [B]ack[/dim]")
            
            prefix_raw = Prompt.ask("Prefix [B]ack", default="ge400-0/0/4.")
            if prefix_raw.lower() == 'b':
                return False
            prefix = prefix_raw
            
            start = _prompt_int_with_back("Start number", 1)
            if start is None:
                return False
            
            count = _prompt_int_with_back("Count", 100)
            if count is None:
                return False
            
            interfaces = [f"{prefix}{i}" for i in range(start, start + count)]
        elif choice.isdigit():
            # Selected a specific parent group
            idx = int(choice) - 1
            _, parent, interfaces = options[idx]
        
        # Sort numerically
        interfaces = sorted(interfaces, key=lambda x: int(x.split('.')[-1]) if x.split('.')[-1].isdigit() else 0)
        
        # Show summary
        console.print(f"\n[bold yellow]Will remove {len(interfaces):,} interfaces[/bold yellow]")
        sample = interfaces[:5]
        console.print(f"[dim]Sample: {', '.join(sample)}{'...' if len(interfaces) > 5 else ''}[/dim]")
        
        # Show WAN warning if applicable
        wan_in_selection = [i for i in interfaces if i in wan_interfaces]
        if wan_in_selection:
            console.print(f"[bold red]⚠ Includes {len(wan_in_selection)} WAN interfaces![/bold red]")
        
        # For remove operation, offer direct deletion (not via services)
        console.print("\n[bold cyan]Delete Method[/bold cyan]")
        console.print("  [1] Direct delete - Remove from 'interfaces' hierarchy (RECOMMENDED)")
        console.print("  [2] Service detach - Remove interface attachments from services only")
        console.print("  [B] Back")
        
        method_choice = Prompt.ask("Select method", choices=["1", "2", "b", "B"], default="1")
        
        if method_choice.lower() == 'b':
            return False
        
        if method_choice == "1":
            # Direct deletion - use CLI commands with live terminal
            return _execute_direct_interface_delete(multi_ctx, interfaces)
        
        # Otherwise fall through to service-based removal
        changes = {'interfaces': interfaces}
    
    elif operation == 'remap':
        console.print("\n[bold]Remap Configuration[/bold]")
        console.print("  [dim]Enter old/new interface prefixes (or [B]ack)[/dim]")
        
        old_prefix_raw = Prompt.ask("Old prefix [B]ack", default="ph")
        if old_prefix_raw.lower() == 'b':
            return False
        old_prefix = old_prefix_raw
        
        new_prefix_raw = Prompt.ask("New prefix [B]ack", default="bundle")
        if new_prefix_raw.lower() == 'b':
            return False
        new_prefix = new_prefix_raw
        
        offset = _prompt_int_with_back("Number offset", 0)
        if offset is None:
            return False
        
        changes = {'old_prefix': old_prefix, 'new_prefix': new_prefix, 'offset': offset}
    
    # Preview (dry run)
    console.print("\n[bold cyan]Preview Changes[/bold cyan]")
    results = modify_service_interfaces(
        multi_ctx, operation, service_filter, changes, mapper, dry_run=True
    )
    
    # Confirm
    if not Confirm.ask("\nProceed with these changes?", default=False):
        console.print("[dim]Cancelled.[/dim]")
        return False
    
    # Execute
    console.print("\n[bold cyan]Executing Changes[/bold cyan]")
    results = modify_service_interfaces(
        multi_ctx, operation, service_filter, changes, mapper, dry_run=False
    )
    
    # Summary
    success_count = sum(1 for s, _ in results.values() if s)
    console.print(f"\n[bold]Summary: {success_count}/{len(results)} devices updated[/bold]")
    
    return success_count > 0


def _execute_direct_interface_delete(multi_ctx: 'MultiDeviceContext', interfaces: List[str]) -> bool:
    """
    Execute direct deletion of interfaces from device using CLI commands.
    Uses live terminal display with paste-to-terminal style output.
    """
    from rich.live import Live
    from rich.panel import Panel
    from ..config_pusher import ConfigPusher
    import threading
    import time
    
    if not interfaces:
        console.print("[yellow]No interfaces to delete[/yellow]")
        return False
    
    device = multi_ctx.devices[0] if multi_ctx.devices else None
    if not device:
        console.print("[red]No device available[/red]")
        return False
    
    # Sort interfaces numerically
    interfaces = sorted(interfaces, key=lambda x: int(x.split('.')[-1]) if '.' in x and x.split('.')[-1].isdigit() else 0)
    
    # Build delete commands
    delete_commands = [f"no interfaces {iface}" for iface in interfaces]
    
    # Time estimation using accurate system
    from ..config_pusher import get_accurate_push_estimates
    
    delete_config = '\n'.join(delete_commands)
    estimates = get_accurate_push_estimates(
        config_text=delete_config,
        platform=device.platform.value if hasattr(device, 'platform') else "SA-36CD-S",
        include_delete=True
    )
    
    estimated_seconds = estimates['estimates']['terminal_paste']['total']
    source = estimates['source']
    source_detail = estimates['source_detail']
    
    def format_time_local(seconds: float) -> str:
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"
    
    console.print(f"\n[bold cyan]Delete {len(interfaces):,} Interfaces from {device.hostname}[/bold cyan]")
    console.print(f"[dim]Commands: {len(delete_commands):,} delete commands[/dim]")
    
    if source == 'similar_push':
        console.print(f"[green]⏱️  Est. ~{format_time_local(estimated_seconds)} - {source_detail}[/green]")
    elif source == 'scale_type':
        console.print(f"[yellow]⏱️  Est. ~{format_time_local(estimated_seconds)} - {source_detail}[/yellow]")
    else:
        console.print(f"[dim]⏱️  Est. ~{format_time_local(estimated_seconds)} - {source_detail}[/dim]")
    console.print()
    
    # Show sample commands
    console.print("[bold]Sample commands:[/bold]")
    for cmd in delete_commands[:5]:
        console.print(f"  [bright_red]{cmd}[/bright_red]")
    if len(delete_commands) > 5:
        console.print(f"  [dim]... and {len(delete_commands) - 5:,} more[/dim]")
    
    # Confirm
    if not Confirm.ask(f"\n[bold yellow]Delete {len(interfaces):,} interfaces?[/bold yellow]", default=False):
        console.print("[dim]Cancelled.[/dim]")
        return False
    
    operation_start_time = time.time()
    
    # Setup live display
    progress_lock = threading.Lock()
    status = {
        "stage": "connecting",
        "progress": 0,
        "message": "Connecting...",
        "terminal_lines": []
    }
    
    def render_panel():
        with progress_lock:
            content_lines = []
            
            # Elapsed time
            elapsed = time.time() - operation_start_time
            remaining = max(0, estimated_seconds - elapsed)
            
            # Status with timing
            if status["stage"] == "connecting":
                content_lines.append("[yellow]🔌 Connecting...[/yellow]")
            elif status["stage"] == "executing":
                content_lines.append(f"[cyan]⚡ Sending delete commands...[/cyan] [dim]({elapsed:.0f}s elapsed, ~{remaining:.0f}s remaining)[/dim]")
            elif status["stage"] == "committing":
                content_lines.append(f"[magenta]💾 Running commit...[/magenta] [dim]({elapsed:.0f}s elapsed)[/dim]")
            elif status["stage"] == "success":
                content_lines.append(f"[green]✓ Complete in {elapsed:.0f}s[/green]")
            elif status["stage"] == "error":
                content_lines.append("[red]✗ Error[/red]")
            
            # Progress bar
            bar_width = 30
            filled = int(bar_width * status["progress"] / 100)
            bar = "█" * filled + "░" * (bar_width - filled)
            content_lines.append(f"[cyan]{bar}[/cyan] {status['progress']}%")
            
            # Message
            content_lines.append(f"[dim]{status['message']}[/dim]")
            content_lines.append("")
            content_lines.append("[dim]" + "─" * 60 + "[/dim]")
            
            # Terminal lines
            for line in status["terminal_lines"][-8:]:
                # Color-code based on content
                clean = line[:60]
                if 'no interfaces' in clean.lower():
                    content_lines.append(f"[bright_red]{clean}[/bright_red]")
                elif 'commit' in clean.lower():
                    content_lines.append(f"[cyan]{clean}[/cyan]")
                elif 'error' in clean.lower() or 'failed' in clean.lower():
                    content_lines.append(f"[bold red]{clean}[/bold red]")
                elif 'succeeded' in clean.lower() or 'passed' in clean.lower():
                    content_lines.append(f"[green]{clean}[/green]")
                else:
                    content_lines.append(f"[dim]{clean}[/dim]")
            
            # Pad to fixed height
            while len(status["terminal_lines"][-8:]) < 8:
                content_lines.append("")
                status["terminal_lines"].append("")
            
            return Panel(
                "\n".join(content_lines),
                title=f"[bold]{device.hostname}[/bold]",
                border_style="cyan",
                width=70
            )
    
    def progress_callback(msg, pct):
        with progress_lock:
            status["progress"] = pct
            status["message"] = msg[:50]
            status["terminal_lines"].append(msg)
            if pct < 30:
                status["stage"] = "connecting"
            elif pct < 80:
                status["stage"] = "executing"
            else:
                status["stage"] = "committing"
    
    # Execute with live display
    console.print()
    pusher = ConfigPusher()
    
    with Live(render_panel(), refresh_per_second=4, console=console, transient=True) as live:
        def run_delete():
            nonlocal success, message
            success, message, output = pusher.run_cli_commands(
                device=device,
                commands=delete_commands,
                dry_run=False,  # Actually commit
                progress_callback=progress_callback
            )
            
            with progress_lock:
                if success:
                    status["stage"] = "success"
                    status["progress"] = 100
                    status["message"] = f"Deleted {len(interfaces):,} interfaces"
                else:
                    status["stage"] = "error"
                    status["message"] = message[:50]
        
        success = False
        message = ""
        
        # Run in thread
        thread = threading.Thread(target=run_delete)
        thread.start()
        
        while thread.is_alive():
            live.update(render_panel())
            time.sleep(0.25)
        
        thread.join()
        live.update(render_panel())
    
    # Print final panel
    console.print(render_panel())
    
    actual_time = time.time() - operation_start_time
    
    if success:
        console.print(f"\n[bold green]✓ Deleted {len(interfaces):,} interfaces successfully![/bold green]")
        console.print(f"[dim]⏱️  Completed in {actual_time:.1f}s (estimate was {estimated_seconds:.0f}s)[/dim]")
        # Refresh config
        console.print("[dim]Refreshing device configuration...[/dim]")
        multi_ctx.discover_all()
    else:
        console.print(f"\n[bold red]✗ Delete failed: {message}[/bold red]")
        console.print(f"[dim]⏱️  Failed after {actual_time:.1f}s[/dim]")
    
    return success


def show_modify_vlans_menu(multi_ctx: 'MultiDeviceContext') -> bool:
    """
    Interactive menu for bulk VLAN tag modification.
    Supports multi-step modifications with live validation before commit.
    """
    import re
    from rich.table import Table
    from rich import box
    
    console.print("\n[bold cyan]Modify VLAN Tags - Multi-Step Editor[/bold cyan]")
    console.print("[dim]Stack multiple modifications, validate limits, then commit all at once.[/dim]")
    
    # Get device - use first device if multi-device
    devices = multi_ctx.devices
    if not devices:
        console.print("[red]No devices configured[/red]")
        return False
    
    device = devices[0]
    config = multi_ctx.configs.get(device.hostname, "")
    
    # STAG pool limits
    STAG_POOL_MAX = 4000
    
    if not config:
        console.print(f"[yellow]No configuration found for {device.hostname}[/yellow]")
        console.print("[dim]Run Refresh first to fetch device configuration.[/dim]")
        return False
    
    console.print("[dim]Parsing configuration...[/dim]")
    
    # First pass: identify WAN interfaces by description
    wan_interfaces = set()
    current_iface_for_wan = None
    
    for line in config.split('\n'):
        line_stripped = line.strip()
        if line_stripped.startswith('interface '):
            parts = line_stripped.split()
            if len(parts) >= 2:
                current_iface_for_wan = parts[1]
        elif current_iface_for_wan and 'description' in line_stripped.lower():
            if 'wan' in line_stripped.lower():
                # This is a WAN interface - add base name
                base_name = current_iface_for_wan.split('.')[0] if '.' in current_iface_for_wan else current_iface_for_wan
                wan_interfaces.add(base_name)
        elif line_stripped == '!':
            current_iface_for_wan = None
    
    # Fast line-by-line parsing for VLAN tags
    interfaces_with_vlans = []
    wan_skipped = 0
    current_iface = None
    
    # Interface name patterns: ge400-0/0/4.1, ph1.1, bundle1.1, lag1.1, et-0/0/0.1
    iface_pattern = re.compile(r'^(ge\d+-\d+/\d+/\d+\.\d+|ph\d+\.\d+|bundle\d+\.\d+|lag\d+\.\d+|et-\d+/\d+/\d+\.\d+|xe-\d+/\d+/\d+\.\d+)$')
    
    for line in config.split('\n'):
        line_stripped = line.strip()
        
        # Match interface with sub-interface number
        # Format 1: "interface ge400-0/0/4.50"
        # Format 2: "ge400-0/0/4.1" (bare name, indented under parent)
        iface_name = None
        
        if line_stripped.startswith('interface ') and '.' in line_stripped:
            parts = line_stripped.split()
            if len(parts) >= 2:
                iface_name = parts[1]
        elif iface_pattern.match(line_stripped):
            # Bare interface name (sub-interface under parent)
            iface_name = line_stripped
        
        if iface_name:
            # Check if this is a WAN interface - skip it
            base_name = iface_name.split('.')[0] if '.' in iface_name else iface_name
            if base_name in wan_interfaces:
                wan_skipped += 1
                current_iface = None
            else:
                current_iface = iface_name
        
        # Match vlan-tags line
        elif current_iface and 'vlan-tags' in line_stripped and 'outer-tag' in line_stripped:
            # Parse: vlan-tags outer-tag N [inner-tag M]
            outer_match = re.search(r'outer-tag\s+(\d+)', line_stripped)
            inner_match = re.search(r'inner-tag\s+(\d+)', line_stripped)
            
            if outer_match:
                outer_tag = int(outer_match.group(1))
                inner_tag = int(inner_match.group(1)) if inner_match else None
                
                interfaces_with_vlans.append({
                    'interface': current_iface,
                    'outer_tag': outer_tag,
                    'inner_tag': inner_tag,
                    'type': 'qinq' if inner_tag else 'single'
                })
            current_iface = None
        
        # Reset on block end
        elif line_stripped == '!' and current_iface:
            current_iface = None
    
    if wan_skipped:
        console.print(f"[dim]Skipped {wan_skipped} WAN interface(s)[/dim]")
    
    if not interfaces_with_vlans:
        console.print("[yellow]No interfaces with VLAN tags found in configuration.[/yellow]")
        return False
    
    # Group by interface prefix
    prefixes = {}
    for v in interfaces_with_vlans:
        # Extract prefix (e.g., 'ge400-0/0/4' from 'ge400-0/0/4.50')
        prefix = v['interface'].rsplit('.', 1)[0] if '.' in v['interface'] else v['interface']
        if prefix not in prefixes:
            prefixes[prefix] = []
        prefixes[prefix].append(v)
    
    # Detect current VLAN pattern
    # Check if outer-tags follow a pattern (same for all, sequential, etc.)
    outer_tags_list = [v['outer_tag'] for v in interfaces_with_vlans]
    inner_tags_list = [v['inner_tag'] for v in interfaces_with_vlans if v['inner_tag']]
    
    # Detect outer-tag pattern
    outer_pattern = "mixed"
    if len(set(outer_tags_list)) == 1:
        outer_pattern = f"fixed:{outer_tags_list[0]}"
    elif outer_tags_list == sorted(outer_tags_list):
        # Check if sequential
        diffs = [outer_tags_list[i+1] - outer_tags_list[i] for i in range(len(outer_tags_list)-1)]
        if len(set(diffs)) == 1:
            outer_pattern = f"sequential:step={diffs[0]}"
    
    # Detect inner-tag pattern
    inner_pattern = "none"
    if inner_tags_list:
        if len(set(inner_tags_list)) == 1:
            inner_pattern = f"fixed:{inner_tags_list[0]}"
        elif inner_tags_list == sorted(inner_tags_list):
            diffs = [inner_tags_list[i+1] - inner_tags_list[i] for i in range(len(inner_tags_list)-1)]
            if len(set(diffs)) == 1:
                inner_pattern = f"sequential:step={diffs[0]}"
            else:
                inner_pattern = "sequential:varied"
        else:
            inner_pattern = "mixed"
    
    # Show summary
    console.print(f"\n[green]✓ Found {len(interfaces_with_vlans)} interfaces with VLAN tags[/green]")
    
    # Analyze current ranges
    outer_tags = sorted(set(v['outer_tag'] for v in interfaces_with_vlans))
    inner_tags = sorted(set(v['inner_tag'] for v in interfaces_with_vlans if v['inner_tag']))
    
    # Calculate current STAG usage (unique outer-tags)
    current_stag_usage = len(outer_tags)
    
    def show_status_table(working_state, staged_changes):
        """Show current state with validation."""
        # Calculate new STAG usage from working state
        new_outer_tags = set(v['outer_tag'] for v in working_state)
        new_stag_usage = len(new_outer_tags)
        stag_delta = new_stag_usage - current_stag_usage
        
        table = Table(box=box.ROUNDED, title="VLAN Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Current", style="dim")
        table.add_column("After Changes", style="green" if stag_delta <= 0 else "yellow")
        
        table.add_row("Total Interfaces", str(len(interfaces_with_vlans)), str(len(working_state)))
        table.add_row("Unique Outer Tags (STAGs)", str(current_stag_usage), str(new_stag_usage))
        table.add_row("Outer Tags Range", 
                      f"{min(outer_tags)} - {max(outer_tags)}" if outer_tags else "N/A",
                      f"{min(new_outer_tags)} - {max(new_outer_tags)}" if new_outer_tags else "N/A")
        
        new_inner = [v['inner_tag'] for v in working_state if v['inner_tag']]
        table.add_row("Inner Tags Range",
                      f"{min(inner_tags)} - {max(inner_tags)}" if inner_tags else "N/A",
                      f"{min(new_inner)} - {max(new_inner)}" if new_inner else "N/A")
        
        # STAG pool validation
        stag_available = STAG_POOL_MAX - current_stag_usage
        if stag_delta > 0:
            if stag_delta > stag_available:
                table.add_row("⚠ STAG Impact", f"+{stag_delta}", f"[red]EXCEEDS LIMIT ({stag_available} available)[/red]")
            else:
                table.add_row("STAG Impact", f"+{stag_delta}", f"[yellow]{stag_available - stag_delta} remaining[/yellow]")
        else:
            table.add_row("STAG Impact", f"{stag_delta}", f"[green]{stag_available - stag_delta} remaining[/green]")
        
        table.add_row("Staged Modifications", "", f"[cyan]{len(staged_changes)}[/cyan]")
        
        console.print(table)
        
        return new_stag_usage <= STAG_POOL_MAX
    
    # Initialize working state (copy of current)
    working_state = [v.copy() for v in interfaces_with_vlans]
    staged_changes = []  # List of modification descriptions
    all_changes = []  # Accumulated (interface, new_outer, new_inner)
    
    # Multi-step modification loop
    while True:
        console.print("\n" + "─" * 60)
        is_valid = show_status_table(working_state, staged_changes)
        
        if staged_changes:
            console.print(f"\n[bold]Staged Modifications ({len(staged_changes)}):[/bold]")
            for i, desc in enumerate(staged_changes[-5:], 1):
                console.print(f"  {i}. {desc}")
            if len(staged_changes) > 5:
                console.print(f"  [dim]... and {len(staged_changes) - 5} more[/dim]")
        
        console.print("\n[bold]Add Modification:[/bold]")
        console.print("  [1] [cyan]Shift Outer Tags[/cyan] - Add/subtract offset")
        console.print("  [2] [magenta]Shift Inner Tags[/magenta] - Add/subtract offset")
        console.print("  [3] [green]Set Sequential Outer[/green] - New range (⚠ affects STAGs)")
        console.print("  [4] [yellow]Swap Tags[/yellow] - Swap outer ↔ inner")
        console.print("  [5] [blue]Filter & Modify[/blue] - Modify matching interfaces only")
        console.print("  [6] [bold green]Pattern-Based[/bold green] - Change base, keep pattern")
        console.print("\n[bold]Actions:[/bold]")
        if staged_changes:
            console.print("  [C] [green]Commit All[/green] - Push all staged changes")
            console.print("  [U] Undo Last - Remove last modification")
            console.print("  [R] Reset All - Clear all staged changes")
        console.print("  [B] Back/Cancel")
        
        if not is_valid:
            console.print("\n[red]⚠ WARNING: Current changes would exceed STAG pool limit![/red]")
        
        choices = ["1", "2", "3", "4", "5", "6", "b", "B"]
        if staged_changes:
            choices.extend(["c", "C", "u", "U", "r", "R"])
        
        mod_choice = Prompt.ask("Select", choices=choices, default="b").lower()
        
        if mod_choice == 'b':
            if staged_changes:
                if not Confirm.ask("Discard all staged changes?", default=False):
                    continue
            return False
        
        if mod_choice == 'c':
            if not is_valid:
                console.print("[red]Cannot commit - changes exceed STAG limit![/red]")
                continue
            break  # Exit loop to commit
        
        if mod_choice == 'u':
            if staged_changes:
                staged_changes.pop()
                # Rebuild working state from original + remaining changes
                working_state = [v.copy() for v in interfaces_with_vlans]
                all_changes = []
                # Re-apply remaining staged changes would be complex, so we rebuild
                console.print("[yellow]Undo not fully implemented - use Reset instead[/yellow]")
            continue
        
        if mod_choice == 'r':
            staged_changes = []
            all_changes = []
            working_state = [v.copy() for v in interfaces_with_vlans]
            console.print("[green]✓ All changes reset[/green]")
            continue
        
        # Apply a modification
        modification_applied = False
        
        if mod_choice == "1":
            # Shift outer tags
            offset = _prompt_int_with_back("Outer tag offset (+/-)", 0)
            if offset is None:
                continue  # User pressed back, stay in loop
            if offset != 0:
                for v in working_state:
                    v['outer_tag'] += offset
                    all_changes.append((v['interface'], v['outer_tag'], v['inner_tag']))
                staged_changes.append(f"Shift outer tags by {offset:+d}")
                modification_applied = True
        
        elif mod_choice == "2":
            # Shift inner tags
            offset = _prompt_int_with_back("Inner tag offset (+/-)", 0)
            if offset is None:
                continue  # User pressed back, stay in loop
            if offset != 0:
                for v in working_state:
                    if v['inner_tag']:
                        v['inner_tag'] += offset
                        all_changes.append((v['interface'], v['outer_tag'], v['inner_tag']))
                staged_changes.append(f"Shift inner tags by {offset:+d}")
                modification_applied = True
        
        elif mod_choice == "3":
            # Sequential outer tags
            base = _prompt_int_with_back("Starting outer-tag", 1)
            if base is None:
                continue  # User pressed back, stay in loop
            step = _prompt_int_with_back("Step", 1)
            if step is None:
                continue
            working_state.sort(key=lambda x: (x['outer_tag'], x['interface']))
            for i, v in enumerate(working_state):
                v['outer_tag'] = base + (i * step)
                all_changes.append((v['interface'], v['outer_tag'], v['inner_tag']))
            staged_changes.append(f"Sequential outer: {base} to {base + (len(working_state)-1)*step} (step={step})")
            modification_applied = True
        
        elif mod_choice == "4":
            # Swap tags
            qinq = [v for v in working_state if v['inner_tag']]
            if qinq:
                for v in qinq:
                    v['outer_tag'], v['inner_tag'] = v['inner_tag'], v['outer_tag']
                    all_changes.append((v['interface'], v['outer_tag'], v['inner_tag']))
                staged_changes.append(f"Swap outer ↔ inner on {len(qinq)} Q-in-Q interfaces")
                modification_applied = True
            else:
                console.print("[yellow]No Q-in-Q interfaces to swap[/yellow]")
        
        elif mod_choice == "5":
            # Filter and modify
            import fnmatch
            pattern_raw = Prompt.ask("Interface pattern [B]ack", default="*")
            if pattern_raw.lower() == 'b':
                continue  # User pressed back, stay in loop
            pattern = pattern_raw
            filtered = [v for v in working_state if fnmatch.fnmatch(v['interface'], pattern)]
            if filtered:
                console.print(f"[green]✓ {len(filtered)} interfaces match[/green]")
                outer_off = _prompt_int_with_back("Outer offset", 0)
                if outer_off is None:
                    continue
                inner_off = _prompt_int_with_back("Inner offset", 0)
                if inner_off is None:
                    continue
                if outer_off != 0 or inner_off != 0:
                    for v in filtered:
                        v['outer_tag'] += outer_off
                        if v['inner_tag']:
                            v['inner_tag'] += inner_off
                        all_changes.append((v['interface'], v['outer_tag'], v['inner_tag']))
                    staged_changes.append(f"Filter '{pattern}': outer{outer_off:+d}, inner{inner_off:+d}")
                    modification_applied = True
            else:
                console.print(f"[yellow]No match for '{pattern}'[/yellow]")
        
        elif mod_choice == "6":
            # Pattern-based
            curr_outer_base = min(v['outer_tag'] for v in working_state)
            curr_inner_base = min((v['inner_tag'] for v in working_state if v['inner_tag']), default=1)
            new_outer_base = _prompt_int_with_back(f"New outer base (current: {curr_outer_base})", curr_outer_base)
            if new_outer_base is None:
                continue
            new_inner_base = _prompt_int_with_back(f"New inner base (current: {curr_inner_base})", curr_inner_base)
            if new_inner_base is None:
                continue
            outer_off = new_outer_base - curr_outer_base
            inner_off = new_inner_base - curr_inner_base
            if outer_off != 0 or inner_off != 0:
                for v in working_state:
                    v['outer_tag'] += outer_off
                    if v['inner_tag']:
                        v['inner_tag'] += inner_off
                    all_changes.append((v['interface'], v['outer_tag'], v['inner_tag']))
                staged_changes.append(f"Pattern shift: outer{outer_off:+d}, inner{inner_off:+d}")
                modification_applied = True
        
        if modification_applied:
            console.print("[green]✓ Modification staged[/green]")
    
    # Commit all changes
    if not all_changes:
        console.print("[yellow]No changes to apply.[/yellow]")
        return False
    
    # Build final changes from working state
    final_changes = []
    orig_map = {v['interface']: v for v in interfaces_with_vlans}
    for v in working_state:
        orig = orig_map.get(v['interface'], {})
        if v['outer_tag'] != orig.get('outer_tag') or v['inner_tag'] != orig.get('inner_tag'):
            final_changes.append((v['interface'], v['outer_tag'], v['inner_tag']))
    
    # Preview final changes
    console.print(f"\n[bold cyan]Final Preview: {len(final_changes)} interface(s) modified[/bold cyan]")
    
    preview_table = Table(box=box.SIMPLE)
    preview_table.add_column("Interface", style="white")
    preview_table.add_column("Old Tags", style="dim")
    preview_table.add_column("→", style="cyan")
    preview_table.add_column("New Tags", style="green")
    
    for iface, new_outer, new_inner in final_changes[:15]:
        orig = orig_map.get(iface, {})
        old_tags = f"O:{orig.get('outer_tag', '?')} I:{orig.get('inner_tag', '-')}"
        new_tags = f"O:{new_outer} I:{new_inner if new_inner else '-'}"
        preview_table.add_row(iface, old_tags, "→", new_tags)
    
    if len(final_changes) > 15:
        preview_table.add_row(f"... {len(final_changes) - 15} more", "", "", "")
    
    console.print(preview_table)
    
    if not Confirm.ask("\n[bold]Commit these VLAN changes?[/bold]", default=True):
        console.print("[dim]Cancelled.[/dim]")
        return False
    
    changes = final_changes
    
    # Generate configuration commands - DNOS syntax
    # Sub-interfaces are under 'interfaces' block, NOT with 'interface' keyword
    config_lines = ["interfaces"]
    for iface, new_outer, new_inner in changes:
        config_lines.append(f"  {iface}")  # 2 spaces, no 'interface' keyword
        if new_inner:
            config_lines.append(f"    vlan-tags outer-tag {new_outer} inner-tag {new_inner}")
        else:
            config_lines.append(f"    vlan-tags outer-tag {new_outer}")
        config_lines.append("  !")  # 2 spaces before !
    config_lines.append("!")  # Close interfaces block
    
    config_text = "\n".join(config_lines)
    
    # Show generated config
    console.print(f"\n[bold]Generated {len(config_lines)} configuration lines[/bold]")
    if Confirm.ask("View configuration?", default=False):
        console.print("\n[dim]" + config_text[:2000] + ("[/dim]\n... truncated" if len(config_text) > 2000 else "[/dim]"))
    
    # Push configuration with live terminal (Scale UP/DOWN style)
    console.print("\n[bold]Push Method:[/bold]")
    console.print("  [1] [green]Terminal Paste[/green] - Paste directly (live output, uses rollback 0)")
    console.print("  [2] [cyan]File Upload[/cyan] - Upload + load override (replaces config)")
    console.print("  [3] [yellow]Load Merge[/yellow] - Upload + load merge (preserves existing)")
    console.print("  [B] Cancel")
    
    method_choice = Prompt.ask("Select method", choices=["1", "2", "3", "b", "B"], default="1").lower()
    
    if method_choice == 'b':
        return False
    
    use_terminal_paste = (method_choice == "1")
    use_merge = (method_choice == "3")
    
    console.print("\n[bold]Push Action:[/bold]")
    console.print("  [1] Commit check only (dry run)")
    console.print("  [2] Push and commit")
    
    action_choice = Prompt.ask("Select action", choices=["1", "2"], default="1")
    
    dry_run = (action_choice == "1")
    
    # Import push function and live display
    from ..config_pusher import ConfigPusher
    from rich.live import Live
    from rich.panel import Panel
    from rich.text import Text
    from rich.columns import Columns
    import time
    import threading
    
    pusher = ConfigPusher()
    
    # Live terminal state (Scale UP/DOWN consistent style)
    MAX_TERMINAL_LINES = 12
    PANEL_HEIGHT = MAX_TERMINAL_LINES + 5
    progress_lock = threading.Lock()
    
    device_progress = {
        device.hostname: {
            "status": "pending",
            "progress": 0,
            "message": "Waiting...",
            "terminal_lines": []
        }
    }
    start_time = time.time()
    
    def render_live_panel():
        """Render live terminal panel - Scale UP/DOWN consistent style."""
        hostname = device.hostname
        status = device_progress[hostname]
        status_str = status["status"]
        progress_pct = status["progress"]
        message = status["message"]
        terminal_lines = status.get("terminal_lines", [])
        
        # Build content with Text - use append with style
        content = Text()
        
        # Elapsed time
        elapsed = time.time() - start_time
        content.append(f"⏱ {int(elapsed)}s elapsed\n", style="dim")
        
        # Status line with icons
        if status_str == "pending":
            content.append("⏳ Pending\n", style="dim")
            filled = 0
            bar_style = "dim"
        elif status_str == "connecting":
            content.append("🔌 Connecting...\n", style="yellow")
            filled = 4
            bar_style = "yellow"
        elif status_str == "upload":
            content.append(f"📤 Uploading file...\n", style="cyan")
            filled = int(progress_pct / 5)
            bar_style = "cyan"
        elif status_str == "uploading":
            # Terminal paste mode - show line progress
            import re
            line_match = re.search(r'(\d+)/(\d+)', message)
            if line_match:
                current_line = int(line_match.group(1))
                total_lines = int(line_match.group(2))
                actual_pct = int((current_line / total_lines) * 100) if total_lines > 0 else 0
                filled = int(actual_pct / 5)
                content.append(f"📤 Pasting line {current_line:,}/{total_lines:,}\n", style="cyan")
            else:
                content.append(f"📤 Pasting config...\n", style="cyan")
                filled = int(progress_pct / 5)
            bar_style = "cyan"
        elif status_str == "load":
            content.append(f"📥 Loading config...\n", style="cyan")
            filled = int(progress_pct / 5)
            bar_style = "cyan"
        elif status_str == "commit_check":
            content.append("🔍 Commit check...\n", style="magenta")
            filled = 16
            bar_style = "magenta"
        elif status_str == "commit":
            content.append("⚙️ Committing...\n", style="magenta")
            filled = 18
            bar_style = "magenta"
        elif status_str == "success":
            content.append("✓ Success!\n", style="green")
            filled = 20
            bar_style = "green"
        elif status_str == "failed":
            content.append(f"✗ {message[:30]}\n", style="red")
            filled = 20
            bar_style = "red"
        else:
            content.append(f"{status_str}\n")
            filled = int(progress_pct / 5)
            bar_style = "cyan"
        
        # Progress bar
        content.append("Progress: ")
        content.append("█" * filled, style=bar_style)
        content.append("░" * (20 - filled), style="dim")
        content.append(f" {progress_pct}%\n", style=bar_style)
        content.append("─" * 50 + "\n")
        
        # Terminal output (last N lines) - fixed height with padding
        lines_to_show = terminal_lines[-MAX_TERMINAL_LINES:] if terminal_lines else []
        lines_added = 0
        
        for line in lines_to_show:
            # Clean and truncate, escape Rich markup
            clean = line[:48].replace('[', '\\[').replace(']', '\\]')
            if clean.startswith('→') or clean.startswith('>>>'):
                content.append(f"  {clean}\n", style="bright_green")
            elif clean.startswith('←'):
                content.append(f"  {clean}\n", style="yellow")
            elif clean.startswith('✓'):
                content.append(f"  {clean}\n", style="green")
            elif clean.startswith('✗') or 'error' in clean.lower():
                content.append(f"  {clean}\n", style="red")
            elif clean.startswith('⏳'):
                content.append(f"  {clean}\n", style="yellow")
            else:
                content.append(f"  {clean}\n", style="dim")
            lines_added += 1
        
        # Pad to fixed height
        while lines_added < MAX_TERMINAL_LINES:
            content.append("\n")
            lines_added += 1
        
        # Border color based on status
        if status_str == "success":
            border_style = "green"
        elif status_str == "failed":
            border_style = "red"
        elif status_str in ("upload", "load", "commit_check", "commit"):
            border_style = "cyan"
        else:
            border_style = "dim"
        
        return Panel(
            content,
            title=f"[bold white]{hostname} - VLAN Changes[/bold white]",
            border_style=border_style,
            height=PANEL_HEIGHT + 3
        )
    
    def progress_callback(info):
        """Handle progress updates - thread-safe."""
        with progress_lock:
            hostname = device.hostname
            device_progress[hostname]["status"] = info.get('stage', device_progress[hostname]["status"])
            device_progress[hostname]["progress"] = info.get('progress', device_progress[hostname]["progress"])
            device_progress[hostname]["message"] = info.get('message', device_progress[hostname]["message"])
            
            # Capture terminal output
            if 'terminal_output' in info and info['terminal_output']:
                for line in info['terminal_output'].strip().split('\n'):
                    if line.strip():
                        device_progress[hostname]["terminal_lines"].append(line.strip())
                        if len(device_progress[hostname]["terminal_lines"]) > 100:
                            device_progress[hostname]["terminal_lines"] = device_progress[hostname]["terminal_lines"][-100:]
    
    method_str = "Terminal Paste" if use_terminal_paste else "File Upload"
    console.print(f"\n[cyan]{'Testing' if dry_run else 'Pushing'} VLAN changes via {method_str} to {device.hostname}...[/cyan]")
    
    # Add uploading status for terminal paste
    if use_terminal_paste:
        device_progress[device.hostname]["status"] = "uploading"
    
    # Live output callback for terminal paste
    def live_output_callback(output_line: str):
        """Capture live terminal output."""
        with progress_lock:
            for line in output_line.strip().split('\n'):
                if line.strip():
                    device_progress[device.hostname]["terminal_lines"].append(line.strip())
                    if len(device_progress[device.hostname]["terminal_lines"]) > 100:
                        device_progress[device.hostname]["terminal_lines"] = device_progress[device.hostname]["terminal_lines"][-100:]
    
    # Run with live display
    with Live(render_live_panel(), refresh_per_second=4, console=console, transient=False) as live:
        def update_live_dict(info):
            """Callback for push_config_enhanced (dict format)."""
            progress_callback(info)
            live.update(render_live_panel())
        
        def update_live_paste(msg: str, pct: int):
            """Callback for push_config_terminal_paste (message, progress format)."""
            with progress_lock:
                device_progress[device.hostname]["message"] = msg
                device_progress[device.hostname]["progress"] = pct
                # Detect stage from message
                if "connect" in msg.lower():
                    device_progress[device.hostname]["status"] = "connecting"
                elif "past" in msg.lower() or "line" in msg.lower():
                    device_progress[device.hostname]["status"] = "uploading"
                elif "commit check" in msg.lower():
                    device_progress[device.hostname]["status"] = "commit_check"
                elif "commit" in msg.lower():
                    device_progress[device.hostname]["status"] = "commit"
            live.update(render_live_panel())
        
        if use_terminal_paste:
            # Terminal paste with live output
            success, output = pusher.push_config_terminal_paste(
                device, config_text, dry_run=dry_run,
                progress_callback=update_live_paste,
                live_output_callback=live_output_callback,
                show_live_terminal=False  # We handle display ourselves
            )
            message = "" if success else output
        else:
            # File upload (override or merge)
            if use_merge:
                # Load merge - preserves existing config
                success, message = pusher.push_config_merge(
                    device, config_text, dry_run=dry_run,
                    progress_callback=update_live_paste  # Uses same signature
                )
                output = []
            else:
                # Load override - replaces config
                success, message, output = pusher.push_config_enhanced(
                    device, config_text, dry_run=dry_run,
                    progress_callback=update_live_dict
                )
        
        # Final update
        with progress_lock:
            device_progress[device.hostname]["status"] = "success" if success else "failed"
            device_progress[device.hostname]["progress"] = 100
            if not success:
                device_progress[device.hostname]["message"] = str(message)[:50]
        live.update(render_live_panel())
    
    if success:
        if dry_run:
            console.print("[bold green]✓ Commit check passed![/bold green]")
            if Confirm.ask("Proceed with actual commit?", default=True):
                # Reset for second push
                start_time = time.time()
                with progress_lock:
                    device_progress[device.hostname] = {
                        "status": "pending" if not use_terminal_paste else "uploading",
                        "progress": 0,
                        "message": "Starting commit...",
                        "terminal_lines": []
                    }
                
                with Live(render_live_panel(), refresh_per_second=4, console=console, transient=False) as live:
                    def update_live2_dict(info):
                        progress_callback(info)
                        live.update(render_live_panel())
                    
                    def update_live2_paste(msg: str, pct: int):
                        with progress_lock:
                            device_progress[device.hostname]["message"] = msg
                            device_progress[device.hostname]["progress"] = pct
                            if "connect" in msg.lower():
                                device_progress[device.hostname]["status"] = "connecting"
                            elif "past" in msg.lower() or "line" in msg.lower():
                                device_progress[device.hostname]["status"] = "uploading"
                            elif "commit check" in msg.lower():
                                device_progress[device.hostname]["status"] = "commit_check"
                            elif "commit" in msg.lower():
                                device_progress[device.hostname]["status"] = "commit"
                        live.update(render_live_panel())
                    
                    if use_terminal_paste:
                        success, output = pusher.push_config_terminal_paste(
                            device, config_text, dry_run=False,
                            progress_callback=update_live2_paste,
                            live_output_callback=live_output_callback,
                            show_live_terminal=False
                        )
                        message = "" if success else output
                    else:
                        if use_merge:
                            success, message = pusher.push_config_merge(
                                device, config_text, dry_run=False,
                                progress_callback=update_live2_paste  # Uses same signature
                            )
                        else:
                            success, message, output = pusher.push_config_enhanced(
                                device, config_text, dry_run=False,
                                progress_callback=update_live2_dict
                            )
                    
                    # Final update
                    with progress_lock:
                        device_progress[device.hostname]["status"] = "success" if success else "failed"
                        device_progress[device.hostname]["progress"] = 100
                        if not success:
                            device_progress[device.hostname]["message"] = str(message)[:50]
                    live.update(render_live_panel())
                
                if success:
                    console.print("[bold green]✓ VLAN changes committed![/bold green]")
                else:
                    console.print(f"[red]Commit failed: {message}[/red]")
        else:
            console.print("[bold green]✓ VLAN changes committed![/bold green]")
        return True
    else:
        console.print(f"[red]Failed: {message}[/red]")
        return False

