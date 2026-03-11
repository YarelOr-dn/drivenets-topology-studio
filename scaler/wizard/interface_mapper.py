"""
Interface Mapper for Multi-Device Operations.

This module provides interface mapping between devices for synchronized
multi-device configuration operations.

Modes:
    - same: Same interface names on all devices (ph1.1 on PE-1 = ph1.1 on PE-2)
    - offset: Offset interface numbering per device (PE-1: ph1-1000, PE-2: ph1001-2000)
    - mapped: Explicit user-defined mapping between devices
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table
from rich import box
from .core import BackException, TopException, int_prompt_nav, str_prompt_nav

console = Console()


class InterfaceMapper:
    """Maps interfaces between devices for synchronized operations."""
    
    MODES = ['same', 'offset', 'mapped']
    
    def __init__(self, mode: str, devices: List[Any]):
        """
        Initialize the interface mapper.
        
        Args:
            mode: Mapping mode ('same', 'offset', or 'mapped')
            devices: List of device objects
        """
        if mode not in self.MODES:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {self.MODES}")
        
        self.mode = mode
        self.devices = devices
        self.hostnames = [d.hostname for d in devices]
        
        # For offset mode: hostname -> (start, end) range
        self.offset_ranges: Dict[str, Tuple[int, int]] = {}
        
        # For mapped mode: hostname -> {base_interface: mapped_interface}
        self.explicit_mapping: Dict[str, Dict[str, str]] = {}
        
        # Base device (first device) for reference
        self.base_hostname = self.hostnames[0] if self.hostnames else None
    
    def configure_offset_mode(
        self,
        interface_prefix: str = "ph",
        total_count: int = 1000,
        start_number: int = 1
    ):
        """
        Configure offset ranges for each device.
        
        Args:
            interface_prefix: Interface prefix (e.g., 'ph', 'ge100-0/0/')
            total_count: Total interfaces to distribute
            start_number: Starting interface number
        """
        per_device = total_count // len(self.devices)
        remainder = total_count % len(self.devices)
        
        current_start = start_number
        for i, hostname in enumerate(self.hostnames):
            # Add remainder to first device
            count = per_device + (1 if i < remainder else 0)
            self.offset_ranges[hostname] = (current_start, current_start + count - 1)
            current_start += count
    
    def configure_offset_mode_interactive(self):
        """Interactively configure offset ranges."""
        console.print("\n[bold cyan]Configure Interface Offset Mode[/bold cyan]")
        console.print("[dim]Each device will use a different range of interface numbers.[/dim]\n")
        
        interface_prefix = str_prompt_nav("Interface prefix", default="ph")
        total_count = int_prompt_nav("Total interfaces to distribute", default=2000)
        start_number = int_prompt_nav("Starting number", default=1)
        
        # Calculate default distribution
        per_device = total_count // len(self.devices)
        
        console.print(f"\n[bold]Distribution Options:[/bold]")
        console.print(f"  [1] Even split ({per_device} per device)")
        console.print(f"  [2] Custom ranges per device")
        console.print(f"  [B] Back")
        
        dist_choice = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="1").lower()
        
        if dist_choice == "b":
            raise BackException()
        
        if dist_choice == "1":
            self.configure_offset_mode(interface_prefix, total_count, start_number)
        else:
            # Custom ranges
            current_start = start_number
            for hostname in self.hostnames:
                suggested_end = current_start + per_device - 1
                console.print(f"\n[cyan]{hostname}[/cyan]:")
                range_start = int_prompt_nav("  Start", default=current_start)
                range_end = int_prompt_nav("  End", default=suggested_end)
                self.offset_ranges[hostname] = (range_start, range_end)
                current_start = range_end + 1
        
        # Show summary
        self._show_offset_summary()
    
    def _show_offset_summary(self):
        """Display offset ranges summary."""
        table = Table(title="Interface Offset Ranges", box=box.SIMPLE)
        table.add_column("Device", style="cyan")
        table.add_column("Start", justify="right")
        table.add_column("End", justify="right")
        table.add_column("Count", justify="right", style="green")
        
        for hostname in self.hostnames:
            if hostname in self.offset_ranges:
                start, end = self.offset_ranges[hostname]
                count = end - start + 1
                table.add_row(hostname, str(start), str(end), str(count))
        
        console.print(table)
    
    def add_explicit_mapping(
        self,
        base_interface: str,
        device_interfaces: Dict[str, str]
    ):
        """
        Add explicit mapping for an interface.
        
        Args:
            base_interface: Interface name on the base device
            device_interfaces: Dict of hostname -> interface name
        """
        for hostname, interface in device_interfaces.items():
            if hostname not in self.explicit_mapping:
                self.explicit_mapping[hostname] = {}
            self.explicit_mapping[hostname][base_interface] = interface
    
    def configure_mapped_mode_interactive(self, base_interfaces: List[str]):
        """
        Interactively configure explicit mappings.
        
        Args:
            base_interfaces: List of interfaces from the base device
        """
        console.print("\n[bold cyan]Configure Explicit Interface Mapping[/bold cyan]")
        console.print(f"[dim]Map interfaces from {self.base_hostname} to other devices.[/dim]\n")
        
        # Initialize mappings
        for hostname in self.hostnames:
            self.explicit_mapping[hostname] = {}
        
        # Show mapping options
        console.print("[bold]Mapping Options:[/bold]")
        console.print("  [1] One-to-one (same names on all devices)")
        console.print("  [2] Bulk offset (apply numeric offset)")
        console.print("  [3] Manual mapping (specify each)")
        console.print("  [B] Back")
        
        map_choice = Prompt.ask("Select", choices=["1", "2", "3", "b", "B"], default="1").lower()
        
        if map_choice == "b":
            raise BackException()
        
        if map_choice == "1":
            # Same names
            for iface in base_interfaces:
                for hostname in self.hostnames:
                    self.explicit_mapping[hostname][iface] = iface
        
        elif map_choice == "2":
            # Bulk offset
            for i, hostname in enumerate(self.hostnames):
                if hostname == self.base_hostname:
                    offset = 0
                else:
                    offset = int_prompt_nav(f"Offset for {hostname}", default=i * 100)
                
                for iface in base_interfaces:
                    mapped = self._apply_offset_to_interface(iface, offset)
                    self.explicit_mapping[hostname][iface] = mapped
        
        else:
            # Manual mapping
            console.print(f"\n[dim]Enter mapping for each interface (or press Enter to keep same)[/dim]")
            for iface in base_interfaces[:10]:  # Limit to first 10 for sanity
                for hostname in self.hostnames:
                    if hostname == self.base_hostname:
                        self.explicit_mapping[hostname][iface] = iface
                    else:
                        mapped = Prompt.ask(
                            f"  {iface} on {hostname}",
                            default=iface
                        )
                        self.explicit_mapping[hostname][iface] = mapped
            
            # For remaining interfaces, apply pattern
            if len(base_interfaces) > 10:
                console.print(f"\n[yellow]Remaining {len(base_interfaces) - 10} interfaces will use same names.[/yellow]")
                for iface in base_interfaces[10:]:
                    for hostname in self.hostnames:
                        self.explicit_mapping[hostname][iface] = iface
        
        self._show_mapping_summary(base_interfaces[:5])
    
    def _apply_offset_to_interface(self, interface: str, offset: int) -> str:
        """
        Apply numeric offset to an interface name.
        
        Args:
            interface: Original interface name (e.g., 'ph100.1')
            offset: Numeric offset to apply
        
        Returns:
            Offset interface name (e.g., 'ph200.1' with offset=100)
        """
        # Match patterns like ph100, ph100.1, ge100-0/0/1.100
        match = re.match(r'^([a-zA-Z]+)(\d+)(.*)', interface)
        if match:
            prefix = match.group(1)
            number = int(match.group(2))
            suffix = match.group(3)
            return f"{prefix}{number + offset}{suffix}"
        return interface
    
    def _show_mapping_summary(self, sample_interfaces: List[str]):
        """Display mapping summary."""
        table = Table(title="Interface Mapping (sample)", box=box.SIMPLE)
        table.add_column("Base Interface", style="cyan")
        
        for hostname in self.hostnames:
            table.add_column(hostname)
        
        for iface in sample_interfaces:
            row = [iface]
            for hostname in self.hostnames:
                mapped = self.get_interface_for_device(iface, hostname)
                if mapped == iface:
                    row.append(f"[dim]{mapped}[/dim]")
                else:
                    row.append(f"[green]{mapped}[/green]")
            table.add_row(*row)
        
        console.print(table)
    
    def get_interface_for_device(
        self,
        base_interface: str,
        device_hostname: str
    ) -> str:
        """
        Get the corresponding interface for a specific device.
        
        Args:
            base_interface: Interface name from the base device
            device_hostname: Target device hostname
        
        Returns:
            Mapped interface name for the target device
        """
        if self.mode == 'same':
            return base_interface
        
        elif self.mode == 'offset':
            if device_hostname == self.base_hostname:
                return base_interface
            
            # Extract number from interface
            match = re.match(r'^([a-zA-Z]+)(\d+)(.*)', base_interface)
            if not match:
                return base_interface
            
            prefix = match.group(1)
            base_number = int(match.group(2))
            suffix = match.group(3)
            
            # Get base range and target range
            base_range = self.offset_ranges.get(self.base_hostname, (1, 1000))
            target_range = self.offset_ranges.get(device_hostname, (1, 1000))
            
            # Calculate relative position and map to target range
            if base_range[0] <= base_number <= base_range[1]:
                relative_pos = base_number - base_range[0]
                new_number = target_range[0] + relative_pos
                return f"{prefix}{new_number}{suffix}"
            
            return base_interface
        
        elif self.mode == 'mapped':
            mapping = self.explicit_mapping.get(device_hostname, {})
            return mapping.get(base_interface, base_interface)
        
        return base_interface
    
    def get_all_interfaces_for_device(
        self,
        base_interfaces: List[str],
        device_hostname: str
    ) -> List[str]:
        """
        Get all mapped interfaces for a device.
        
        Args:
            base_interfaces: List of interfaces from base device
            device_hostname: Target device hostname
        
        Returns:
            List of mapped interfaces for the target device
        """
        return [
            self.get_interface_for_device(iface, device_hostname)
            for iface in base_interfaces
        ]
    
    def get_reverse_mapping(
        self,
        device_hostname: str,
        device_interface: str
    ) -> Optional[str]:
        """
        Get the base interface that maps to a device interface.
        
        Args:
            device_hostname: Device hostname
            device_interface: Interface on that device
        
        Returns:
            Corresponding base interface, or None if not found
        """
        if self.mode == 'same':
            return device_interface
        
        elif self.mode == 'offset':
            # Reverse the offset calculation
            match = re.match(r'^([a-zA-Z]+)(\d+)(.*)', device_interface)
            if not match:
                return device_interface
            
            prefix = match.group(1)
            dev_number = int(match.group(2))
            suffix = match.group(3)
            
            base_range = self.offset_ranges.get(self.base_hostname, (1, 1000))
            target_range = self.offset_ranges.get(device_hostname, (1, 1000))
            
            if target_range[0] <= dev_number <= target_range[1]:
                relative_pos = dev_number - target_range[0]
                base_number = base_range[0] + relative_pos
                return f"{prefix}{base_number}{suffix}"
            
            return None
        
        elif self.mode == 'mapped':
            mapping = self.explicit_mapping.get(device_hostname, {})
            # Reverse lookup
            for base, mapped in mapping.items():
                if mapped == device_interface:
                    return base
            return None
        
        return None
    
    def generate_interface_config_for_all(
        self,
        base_config_template: str,
        interface_list: List[str]
    ) -> Dict[str, str]:
        """
        Generate interface configuration for all devices.
        
        Args:
            base_config_template: Config template with {interface} placeholder
            interface_list: List of interfaces from base device
        
        Returns:
            Dict of hostname -> generated config
        """
        configs = {}
        
        for hostname in self.hostnames:
            lines = []
            for base_iface in interface_list:
                mapped_iface = self.get_interface_for_device(base_iface, hostname)
                config_line = base_config_template.replace('{interface}', mapped_iface)
                lines.append(config_line)
            configs[hostname] = '\n'.join(lines)
        
        return configs


def select_interface_mapping_mode(devices: List[Any]) -> InterfaceMapper:
    """
    Interactive selection of interface mapping mode.
    
    Args:
        devices: List of device objects
    
    Returns:
        Configured InterfaceMapper instance
    """
    console.print("\n[bold cyan]Interface Mapping Mode[/bold cyan]")
    console.print("[dim]How should interfaces be mapped between devices?[/dim]\n")
    
    console.print("  [1] [green]Same[/green] - Same interface names on all devices")
    console.print("      [dim]ph1.1 on PE-1 = ph1.1 on PE-2[/dim]")
    console.print()
    console.print("  [2] [yellow]Offset[/yellow] - Different ranges per device")
    console.print("      [dim]PE-1: ph1-1000, PE-2: ph1001-2000[/dim]")
    console.print()
    console.print("  [3] [cyan]Mapped[/cyan] - Explicit mapping")
    console.print("      [dim]Define custom mapping between devices[/dim]")
    console.print()
    console.print("  [B] Back")
    
    choice = Prompt.ask(
        "\nSelect mode",
        choices=["1", "2", "3", "b", "B"],
        default="1"
    ).lower()
    
    if choice == "b":
        raise BackException()
    
    mode_map = {"1": "same", "2": "offset", "3": "mapped"}
    mode = mode_map[choice]
    
    mapper = InterfaceMapper(mode, devices)
    
    if mode == 'offset':
        mapper.configure_offset_mode_interactive()
    
    return mapper


def show_interface_mapping_preview(
    mapper: InterfaceMapper,
    sample_interfaces: List[str]
):
    """
    Show preview of interface mapping.
    
    Args:
        mapper: Configured InterfaceMapper
        sample_interfaces: Sample interfaces to show
    """
    console.print(f"\n[bold]Interface Mapping Preview (mode: {mapper.mode})[/bold]")
    
    table = Table(box=box.SIMPLE)
    table.add_column("Base", style="cyan")
    
    for hostname in mapper.hostnames:
        style = "green" if hostname != mapper.base_hostname else "dim"
        table.add_column(hostname, style=style)
    
    for iface in sample_interfaces[:10]:
        row = [iface]
        for hostname in mapper.hostnames:
            mapped = mapper.get_interface_for_device(iface, hostname)
            row.append(mapped)
        table.add_row(*row)
    
    if len(sample_interfaces) > 10:
        table.add_row(f"[dim]... and {len(sample_interfaces) - 10} more[/dim]", 
                      *["" for _ in mapper.hostnames])
    
    console.print(table)













