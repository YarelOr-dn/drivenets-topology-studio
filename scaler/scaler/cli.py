"""Rich-based interactive CLI for SCALER."""

import sys
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from .wizard.core import BackException, TopException, int_prompt_nav
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.text import Text
from rich import box

from .models import (
    Device,
    Platform,
    ScaleConfig,
    InterfaceScale,
    ServiceScale,
    MultihomingScale,
    BGPPeerScale,
    InterfaceType,
    ServiceType,
    RedundancyMode,
)
from .device_manager import DeviceManager
from .config_extractor import ConfigExtractor
from .config_parser import ConfigParser
from .scale_generator import ScaleGenerator
from .validator import Validator
from .config_pusher import ConfigPusher

console = Console()


def print_banner():
    """Print the SCALER banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║     ███████╗ ██████╗ █████╗ ██╗     ███████╗██████╗           ║
║     ██╔════╝██╔════╝██╔══██╗██║     ██╔════╝██╔══██╗          ║
║     ███████╗██║     ███████║██║     █████╗  ██████╔╝          ║
║     ╚════██║██║     ██╔══██║██║     ██╔══╝  ██╔══██╗          ║
║     ███████║╚██████╗██║  ██║███████╗███████╗██║  ██║          ║
║     ╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝          ║
║                                                               ║
║           DNOS Configuration Scale Manager v1.0               ║
╚═══════════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold cyan")


def main_menu() -> str:
    """Display main menu and get selection."""
    console.print("\n[bold]Main Menu:[/bold]")
    console.print("  [1] Manage Devices")
    console.print("  [2] Extract Configurations")
    console.print("  [3] Create Scaled Configuration")
    console.print("  [4] Push Configuration to Device")
    console.print("  [5] View Configuration History")
    console.print("  [6] Settings")
    console.print("  [7] [bold cyan]Interactive Scale Wizard[/bold cyan] [NEW]")
    console.print("  [8] [bold magenta]Modern TUI Mode[/bold magenta] (with scrollbar)")
    console.print("  [0] Exit")
    console.print()
    
    return Prompt.ask("Select option", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8"], default="0")


def manage_devices_menu(dm: DeviceManager):
    """Device management submenu."""
    while True:
        console.print("\n[bold]Device Management:[/bold]")
        console.print("  [1] List Devices")
        console.print("  [2] Add Device")
        console.print("  [3] Remove Device")
        console.print("  [4] Test Connection")
        console.print("  [5] Discover Management IPs")
        console.print("  [0] Back to Main Menu")
        console.print()
        
        choice = Prompt.ask("Select option", choices=["0", "1", "2", "3", "4", "5"], default="0")
        
        if choice == "0":
            break
        elif choice == "1":
            list_devices(dm)
        elif choice == "2":
            add_device(dm)
        elif choice == "3":
            remove_device(dm)
        elif choice == "4":
            test_connection(dm)
        elif choice == "5":
            discover_management_ips(dm)


def list_devices(dm: DeviceManager):
    """List all devices in a table."""
    devices = dm.list_devices()
    
    if not devices:
        console.print("[yellow]No devices configured.[/yellow]")
        return
    
    table = Table(title="Configured Devices", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Hostname", style="green")
    table.add_column("IP/Host", style="white")
    table.add_column("Mgmt IP", style="dim")
    table.add_column("Platform", style="magenta")
    table.add_column("Last Sync", style="dim")
    
    for dev in devices:
        last_sync = dev.last_sync.strftime("%Y-%m-%d %H:%M") if dev.last_sync else "Never"
        mgmt_ip = dev.management_ip or "-"
        table.add_row(dev.id, dev.hostname, dev.ip, mgmt_ip, dev.platform.value, last_sync)
    
    console.print(table)


def add_device(dm: DeviceManager):
    """Add a new device interactively."""
    console.print("\n[bold]Add New Device[/bold]")
    
    device_id = Prompt.ask("Device ID (unique identifier)")
    
    if dm.device_exists(device_id):
        console.print(f"[red]Device '{device_id}' already exists![/red]")
        return
    
    hostname = Prompt.ask("Hostname")
    ip = Prompt.ask("IP Address or DNS name")
    username = Prompt.ask("SSH Username", default="dnroot")
    password = Prompt.ask("SSH Password", password=True)
    
    platform_choice = Prompt.ask(
        "Platform",
        choices=["NCP", "NCM", "NCP5"],
        default="NCP"
    )
    platform = Platform(platform_choice)
    
    description = Prompt.ask("Description (optional)", default="")
    
    try:
        device = dm.add_device(
            device_id=device_id,
            hostname=hostname,
            ip=ip,
            username=username,
            password=password,
            platform=platform,
            description=description or None
        )
        console.print(f"[green]Device '{device.hostname}' added successfully![/green]")
    except Exception as e:
        console.print(f"[red]Error adding device: {e}[/red]")


def remove_device(dm: DeviceManager):
    """Remove a device."""
    devices = dm.list_devices()
    if not devices:
        console.print("[yellow]No devices to remove.[/yellow]")
        return
    
    list_devices(dm)
    device_id = Prompt.ask("Enter Device ID to remove")
    
    if Confirm.ask(f"Are you sure you want to remove device '{device_id}'?"):
        if dm.remove_device(device_id):
            console.print(f"[green]Device '{device_id}' removed.[/green]")
        else:
            console.print(f"[red]Device '{device_id}' not found.[/red]")


def test_connection(dm: DeviceManager):
    """Test connection to a device."""
    devices = dm.list_devices()
    if not devices:
        console.print("[yellow]No devices configured.[/yellow]")
        return
    
    list_devices(dm)
    device_id = Prompt.ask("Enter Device ID to test")
    
    device = dm.get_device(device_id)
    if not device:
        console.print(f"[red]Device '{device_id}' not found.[/red]")
        return
    
    pusher = ConfigPusher()
    
    with console.status(f"Testing connection to {device.hostname}..."):
        success, message = pusher.test_connectivity(device)
    
    if success:
        console.print(f"[green]{message}[/green]")
        
        # Offer to discover management IP
        if not device.management_ip and Confirm.ask("Discover management IP?", default=True):
            with console.status("Discovering management IP..."):
                _, mgmt_ip = pusher.discover_management_ip(device)
            
            if mgmt_ip:
                dm.update_device(device.id, management_ip=mgmt_ip)
                console.print(f"[green]Discovered management IP: {mgmt_ip}[/green]")
            else:
                console.print("[yellow]Could not discover management IP.[/yellow]")
    else:
        console.print(f"[red]{message}[/red]")


def discover_management_ips(dm: DeviceManager):
    """Discover management IPs for all devices."""
    devices = dm.list_devices()
    if not devices:
        console.print("[yellow]No devices configured.[/yellow]")
        return
    
    list_devices(dm)
    
    device_id = Prompt.ask("Enter Device ID (or 'all' for all devices)")
    
    if device_id.lower() == "all":
        target_devices = devices
    else:
        device = dm.get_device(device_id)
        if not device:
            console.print(f"[red]Device '{device_id}' not found.[/red]")
            return
        target_devices = [device]
    
    pusher = ConfigPusher()
    
    for device in target_devices:
        console.print(f"\n[bold]Discovering management IP for {device.hostname}...[/bold]")
        
        # Show current status
        if device.management_ip:
            console.print(f"  [dim]Current management IP: {device.management_ip}[/dim]")
        
        with console.status(f"Connecting to {device.hostname}..."):
            success, mgmt_ip = pusher.discover_management_ip(device)
        
        if success:
            if mgmt_ip:
                dm.update_device(device.id, management_ip=mgmt_ip)
                console.print(f"  [green]✓ Discovered: {mgmt_ip}[/green]")
            else:
                console.print(f"  [dim]No new management IP found (primary IP is management)[/dim]")
        else:
            console.print(f"  [red]✗ Could not connect to device[/red]")
    
    console.print("\n[green]Discovery complete![/green]")


def extract_configurations(dm: DeviceManager):
    """Extract configurations from devices."""
    devices = dm.list_devices()
    if not devices:
        console.print("[yellow]No devices configured.[/yellow]")
        return
    
    list_devices(dm)
    device_id = Prompt.ask("Enter Device ID (or 'all' for all devices)")
    
    extractor = ConfigExtractor()
    parser = ConfigParser()
    
    if device_id.lower() == "all":
        target_devices = devices
    else:
        device = dm.get_device(device_id)
        if not device:
            console.print(f"[red]Device '{device_id}' not found.[/red]")
            return
        target_devices = [device]
    
    for device in target_devices:
        console.print(f"\n[bold]Extracting config from {device.hostname}...[/bold]")
        
        try:
            with console.status("Connecting..."):
                config = extractor.extract_running_config(device, save_to_db=True)
            
            if config:
                # Parse and display summary
                parsed = parser.parse(config.raw_config)
                iface_counts = parser.get_interface_count(parsed)
                svc_counts = parser.get_service_count(config.raw_config)
                wan_interfaces = parser.identify_wan_interfaces(parsed)
                
                console.print(f"[green]Config extracted successfully![/green]")
                console.print(f"  Interfaces: {iface_counts['total']} (Physical: {iface_counts['physical']}, Sub-if: {iface_counts['subinterfaces']})")
                console.print(f"  Services: {svc_counts['total']} (FXC: {svc_counts['evpn_vpws_fxc']}, VRF: {svc_counts['vrf']})")
                console.print(f"  WAN Interfaces: {len(wan_interfaces)}")
                console.print(f"  Has Protocols: {config.has_protocols}")
                console.print(f"  Has System: {config.has_system}")
                
                # Update last sync time
                dm.update_device(device.id, last_sync=datetime.now())
                
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def create_scaled_configuration(dm: DeviceManager):
    """Create a scaled configuration interactively."""
    devices = dm.list_devices()
    if not devices:
        console.print("[yellow]No devices configured. Add a device first.[/yellow]")
        return
    
    list_devices(dm)
    device_id = Prompt.ask("Select target Device ID")
    
    device = dm.get_device(device_id)
    if not device:
        console.print(f"[red]Device '{device_id}' not found.[/red]")
        return
    
    console.print(f"\n[bold]Creating scaled configuration for {device.hostname}[/bold]")
    
    # Check for existing config
    extractor = ConfigExtractor()
    parser = ConfigParser()
    
    existing_config = extractor.get_saved_config(device.hostname)
    preserved = None
    
    if existing_config:
        console.print("[green]Found existing device configuration.[/green]")
        if Confirm.ask("Use existing config to preserve WAN/protocols/system?", default=True):
            preserved = parser.extract_preserved_config(existing_config.raw_config)
            wan_count = len(preserved.wan_interfaces)
            console.print(f"  [dim]Preserving {wan_count} WAN interfaces, protocols, system, routing-policy[/dim]")
    
    # Interface configuration
    console.print("\n[bold cyan]Interface Configuration[/bold cyan]")
    
    iface_type = Prompt.ask(
        "Interface type",
        choices=["ph", "ge100", "ge400", "bundle"],
        default="ph"
    )
    
    iface_start = int_prompt_nav("Start interface number", default=1)
    iface_count = int_prompt_nav("Number of interfaces", default=100)
    
    create_subif = Confirm.ask("Create sub-interfaces?", default=True)
    
    subif_vlan_start = 1
    subif_vlan_step = 1
    subif_count_per = 1
    
    if create_subif:
        subif_vlan_start = int_prompt_nav("Sub-interface VLAN start", default=1)
        subif_vlan_step = int_prompt_nav("VLAN step", default=1)
        subif_count_per = int_prompt_nav("Sub-interfaces per parent", default=1)
    
    interface_scale = InterfaceScale(
        interface_type=InterfaceType(iface_type),
        start_number=iface_start,
        count=iface_count,
        create_subinterfaces=create_subif,
        subif_vlan_start=subif_vlan_start,
        subif_vlan_step=subif_vlan_step,
        subif_count_per_interface=subif_count_per
    )
    
    # Service configuration
    console.print("\n[bold cyan]Network Service Configuration[/bold cyan]")
    
    svc_type = Prompt.ask(
        "Service type",
        choices=["evpn-vpws-fxc", "vrf", "evpn", "vpws"],
        default="evpn-vpws-fxc"
    )
    
    svc_prefix = Prompt.ask("Service name prefix", default="SVC_")
    svc_start = int_prompt_nav("Start number", default=1)
    svc_count = int_prompt_nav("Number of services", default=iface_count)
    
    # RD/RT configuration
    console.print("\n[bold cyan]Route Distinguisher / Route Target[/bold cyan]")
    
    rd_router_id = Prompt.ask("Router ID for RD (e.g., 10.0.0.1)")
    rd_start = int_prompt_nav("RD start value", default=1)
    rd_step = int_prompt_nav("RD step", default=1)
    
    rt_asn = int_prompt_nav("AS number for RT")
    rt_start = int_prompt_nav("RT start value", default=1)
    rt_step = int_prompt_nav("RT step", default=1)
    
    service_scale = ServiceScale(
        service_type=ServiceType(svc_type),
        name_prefix=svc_prefix,
        start_number=svc_start,
        count=svc_count,
        rd_router_id=rd_router_id,
        rd_start=rd_start,
        rd_step=rd_step,
        rt_asn=rt_asn,
        rt_start=rt_start,
        rt_step=rt_step
    )
    
    # Multihoming
    mh_scale = None
    if Confirm.ask("\nEnable Multihoming (ESI)?", default=False):
        esi_base = Prompt.ask("ESI base", default="00:01:02:03:04:05:06:07:08:00")
        esi_step = int_prompt_nav("ESI step", default=1)
        redundancy = Prompt.ask("Redundancy mode", choices=["all-active", "single-active"], default="all-active")
        
        mh_scale = MultihomingScale(
            enabled=True,
            esi_base=esi_base,
            esi_step=esi_step,
            redundancy_mode=RedundancyMode(redundancy)
        )
    
    # BGP Peers
    bgp_scale = None
    if Confirm.ask("\nAdd scaled BGP peers?", default=False):
        peer_ip = Prompt.ask("Peer IP start (e.g., 10.0.1.1)")
        peer_ip_step = int_prompt_nav("Peer IP step", default=1)
        peer_count = int_prompt_nav("Number of peers", default=1)
        peer_as = int_prompt_nav("Peer AS number")
        
        bgp_scale = BGPPeerScale(
            enabled=True,
            peer_ip_start=peer_ip,
            peer_ip_step=peer_ip_step,
            count=peer_count,
            peer_as=peer_as
        )
    
    # Create ScaleConfig
    scale_config = ScaleConfig(
        device_id=device_id,
        interfaces=interface_scale,
        services=service_scale,
        multihoming=mh_scale,
        bgp_peers=bgp_scale,
        preserved=preserved
    )
    
    # Validate
    console.print("\n[bold]Validating configuration...[/bold]")
    
    validator = Validator()
    result = validator.validate_scale_config(scale_config, device.platform)
    
    # Display validation results
    table = Table(title="Validation Results", box=box.ROUNDED)
    table.add_column("Check", style="white")
    table.add_column("Current", justify="right", style="cyan")
    table.add_column("Limit", justify="right", style="dim")
    table.add_column("Usage", justify="right")
    table.add_column("Status", justify="center")
    
    for check in result.checks:
        status = "[green]✓[/green]" if check["passed"] else "[red]✗[/red]"
        usage = f"{check['percentage']}%"
        usage_style = "green" if check["percentage"] < 80 else ("yellow" if check["percentage"] < 100 else "red")
        
        table.add_row(
            check["name"],
            str(check["current"]),
            str(check["limit"]),
            f"[{usage_style}]{usage}[/{usage_style}]",
            status
        )
    
    console.print(table)
    
    if not result.passed:
        console.print("[red]Validation failed! Please adjust parameters.[/red]")
        for error in result.errors:
            console.print(f"  [red]• {error}[/red]")
        return
    
    console.print("[green]All validations passed![/green]")
    
    # Generate configuration
    if Confirm.ask("\nGenerate configuration?", default=True):
        generator = ScaleGenerator()
        
        with console.status("Generating configuration..."):
            config_text = generator.generate(scale_config)
        
        # Show config size
        config_lines = len(config_text.split('\n'))
        config_size = len(config_text)
        
        console.print(f"[green]Configuration generated![/green]")
        console.print(f"  Lines: {config_lines}")
        console.print(f"  Size: {config_size:,} bytes")
        
        # Save to file
        if Confirm.ask("\nSave configuration to file?", default=True):
            from .utils import get_device_config_dir, timestamp_filename
            
            config_dir = get_device_config_dir(device.hostname)
            filename = f"scaled_{timestamp_filename()}.txt"
            filepath = config_dir / filename
            
            with open(filepath, 'w') as f:
                f.write(config_text)
            
            console.print(f"[green]Saved to: {filepath}[/green]")
        
        # Option to push
        if Confirm.ask("\nPush configuration to device?", default=False):
            push_configuration(device, config_text)


def push_configuration(device: Device, config_text: str = None):
    """Push configuration to a device."""
    pusher = ConfigPusher()
    
    if not config_text:
        # Load from file
        from .utils import get_device_config_dir
        config_dir = get_device_config_dir(device.hostname)
        
        configs = list(config_dir.glob("scaled_*.txt"))
        if not configs:
            console.print("[yellow]No generated configurations found.[/yellow]")
            return
        
        console.print("\nAvailable configurations:")
        for i, cfg in enumerate(sorted(configs, reverse=True)[:5]):
            console.print(f"  [{i+1}] {cfg.name}")
        
        choice = int_prompt_nav("Select configuration", default=1)
        
        if choice < 1 or choice > len(configs):
            console.print("[red]Invalid selection.[/red]")
            return
        
        with open(sorted(configs, reverse=True)[choice-1], 'r') as f:
            config_text = f.read()
    
    # Confirm push
    dry_run = Confirm.ask("Run commit check only (dry run)?", default=True)
    
    if not Confirm.ask(f"Push configuration to {device.hostname}?", default=False):
        return
    
    # Push with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        task = progress.add_task("Pushing configuration...", total=100)
        
        def update_progress(message: str, percent: int):
            progress.update(task, completed=percent, description=message)
        
        success, message = pusher.push_config(
            device,
            config_text,
            dry_run=dry_run,
            progress_callback=update_progress
        )
    
    if success:
        console.print(f"[green]{message}[/green]")
    else:
        console.print(f"[red]{message}[/red]")


def view_history(dm: DeviceManager):
    """View configuration history for devices."""
    devices = dm.list_devices()
    if not devices:
        console.print("[yellow]No devices configured.[/yellow]")
        return
    
    list_devices(dm)
    device_id = Prompt.ask("Enter Device ID")
    
    device = dm.get_device(device_id)
    if not device:
        console.print(f"[red]Device '{device_id}' not found.[/red]")
        return
    
    extractor = ConfigExtractor()
    history = extractor.get_config_history(device.hostname)
    
    if not history:
        console.print("[yellow]No configuration history found.[/yellow]")
        return
    
    table = Table(title=f"Configuration History - {device.hostname}", box=box.ROUNDED)
    table.add_column("#", style="dim")
    table.add_column("Timestamp", style="cyan")
    table.add_column("Size", justify="right", style="dim")
    
    for i, h in enumerate(history[:20]):  # Show last 20
        table.add_row(
            str(i + 1),
            h["timestamp"],
            f"{h['size']:,} bytes"
        )
    
    console.print(table)


def settings_menu(dm: DeviceManager):
    """Settings submenu."""
    settings = dm.get_settings()
    
    console.print("\n[bold]Current Settings:[/bold]")
    console.print(f"  Sync Interval: {settings.get('sync_interval_minutes', 60)} minutes")
    console.print(f"  Auto Sync: {'Enabled' if settings.get('auto_sync_enabled') else 'Disabled'}")
    console.print(f"  Default Platform: {settings.get('default_platform', 'NCP')}")
    
    if Confirm.ask("\nModify settings?", default=False):
        sync_interval = int_prompt_nav("Sync interval (minutes)", default=settings.get('sync_interval_minutes', 60))
        auto_sync = Confirm.ask("Enable auto sync?", default=settings.get('auto_sync_enabled', False))
        default_platform = Prompt.ask("Default platform", choices=["NCP", "NCM", "NCP5"], default=settings.get('default_platform', 'NCP'))
        
        dm.update_settings(
            sync_interval_minutes=sync_interval,
            auto_sync_enabled=auto_sync,
            default_platform=default_platform
        )
        console.print("[green]Settings updated![/green]")


def run_interactive_wizard():
    """Launch the interactive scale wizard."""
    from .interactive_scale import run_wizard
    run_wizard()


def run_textual_tui():
    """Launch the modern Textual TUI with scrollbar support."""
    try:
        from .tui import run_tui
        run_tui()
    except ImportError as e:
        console.print(f"[red]Textual TUI not available: {e}[/red]")
        console.print("[dim]Install with: pip install textual textual-dev[/dim]")


def main():
    """Main entry point for SCALER CLI."""
    print_banner()
    
    dm = DeviceManager()
    
    while True:
        try:
            choice = main_menu()
            
            if choice == "0":
                console.print("[bold]Goodbye![/bold]")
                sys.exit(0)
            elif choice == "1":
                manage_devices_menu(dm)
            elif choice == "2":
                extract_configurations(dm)
            elif choice == "3":
                create_scaled_configuration(dm)
            elif choice == "4":
                devices = dm.list_devices()
                if devices:
                    list_devices(dm)
                    device_id = Prompt.ask("Enter Device ID")
                    device = dm.get_device(device_id)
                    if device:
                        push_configuration(device)
                    else:
                        console.print(f"[red]Device '{device_id}' not found.[/red]")
                else:
                    console.print("[yellow]No devices configured.[/yellow]")
            elif choice == "5":
                view_history(dm)
            elif choice == "6":
                settings_menu(dm)
            elif choice == "7":
                run_interactive_wizard()
            elif choice == "8":
                run_textual_tui()
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    main()

