"""
Push and Verify Functions for the SCALER Wizard.

This module contains:
- push_and_verify(): Main function to push configs to devices
- ask_push_method(): Prompt for push method selection
- suggest_error_fix(): Error diagnosis and suggestions
- show_diff_preview(): Display configuration diff
- delete_hierarchy(): Delete a hierarchy from device config via CLI
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


# ==============================================================================
# HIERARCHY DELETE COMMANDS
# ==============================================================================
# DNOS supports flattened one-liner "no" commands from configure mode.
# Just like "set protocols bgp local-as 65001", you can use:
# "no protocols bgp" to delete BGP in one command from (cfg)# mode.
#
# Syntax: configure -> no <full-hierarchy-path> -> commit check -> commit
#
# Examples from DNOS CLI PDF:
# - no protocols               (removes all protocols)
# - no protocols bgp           (removes BGP only)
# - no protocols isis          (removes ISIS only)
# - no network-services        (removes all network services)
# - no network-services multihoming  (removes multihoming only)
# - no interfaces              (removes all interfaces)

HIERARCHY_DELETE_COMMANDS = {
    'system': {
        'command': 'no system',
        'warning': 'System hierarchy cannot be fully deleted. Individual items can be reset to defaults.'
    },
    'interfaces': {
        # SPECIAL HANDLING: Don't use 'no interfaces' - use smart delete
        'command': None,  # Will be generated dynamically
        'smart_delete': True,  # Flag to use smart interface deletion
        'warning': 'Will delete service interfaces (sub-ifs, PWHE, IRB) but KEEP physical parents & loopbacks.'
    },
    'services': {
        'command': 'no network-services',
        'warning': 'This will remove ALL network services (FXC, EVPN, VRF, etc.)'
    },
    'bgp': {
        'command': 'no protocols bgp',
        'warning': 'This will disable and remove the entire BGP process.'
    },
    'igp': {
        'commands': ['no protocols isis', 'no protocols ospf'],  # Try both - one may not exist
        'warning': 'This will remove ISIS and/or OSPF configurations.'
    },
    'multihoming': {
        'command': 'no network-services multihoming',
        'warning': 'This will remove all ESI/multihoming configurations.'
    },
    'vrf': {
        'command': 'no network-services vrf',
        'warning': 'This will remove all VRF instances and L3VPN configurations.'
    },
    'flowspec': {
        'commands': ['no routing-policy flowspec-local-policies'],
        'warning': 'This will remove all flowspec local policies. BGP flowspec AFI config remains under BGP.'
    },
}

# Hierarchies that require extra confirmation due to impact
CRITICAL_HIERARCHIES = {'system', 'interfaces', 'bgp'}

# Human-readable names for hierarchies
HIERARCHY_DISPLAY_NAMES = {
    'system': 'System Configuration',
    'interfaces': 'Service Interfaces (keeps physical & loopbacks)',
    'services': 'Network Services (FXC/VPLS/EVPN)',
    'vrf': 'VRF / L3VPN Instances',
    'bgp': 'BGP Configuration',
    'igp': 'IGP (ISIS/OSPF)',
    'multihoming': 'Multihoming (ESI)',
    'flowspec': 'Flowspec Policies',
}


def ask_push_method() -> Tuple[bool, bool, bool]:
    """
    Ask user to select the push method.
    
    Returns:
        Tuple of (do_check, do_commit, is_replace)
        - do_check: Run commit check
        - do_commit: Actually commit the config
        - is_replace: Use load replace (vs load merge)
    """
    console.print("\n[bold cyan]Select Push Method:[/bold cyan]")
    console.print("  [1] Commit Check Only (safe - no changes)")
    console.print("  [2] Load Merge + Commit (append to existing config)")
    console.print("  [3] Load Replace + Commit (replace entire config)")
    console.print("  [4] Cancel")
    
    choice = Prompt.ask("Choice", choices=["1", "2", "3", "4"], default="1")
    
    if choice == "1":
        return True, False, False
    elif choice == "2":
        return True, True, False
    elif choice == "3":
        return True, True, True
    else:
        return False, False, False


def suggest_error_fix(error_message: str):
    """
    Analyze a DNOS error message and suggest fixes.
    
    Args:
        error_message: Error message from device
    """
    suggestions = []
    
    # Common error patterns
    if "already exists" in error_message.lower():
        suggestions.append("The configuration item already exists. Try using 'load merge' or modify the existing item.")
    
    if "not found" in error_message.lower():
        suggestions.append("A referenced item doesn't exist. Ensure parent interfaces/services are created first.")
    
    if "invalid" in error_message.lower():
        suggestions.append("Check syntax and valid value ranges for the parameter.")
    
    if "limit" in error_message.lower() or "exceeded" in error_message.lower():
        suggestions.append("Platform limit reached. Check DNOS limits with 'show platform limits'.")
    
    if "ip-addresses and l2-service" in error_message.lower() or "ip-address" in error_message.lower() and "l2-service" in error_message.lower():
        iface_match = re.search(r"\('([^']+)'\)", error_message)
        iface_name = iface_match.group(1) if iface_match else "the interface"
        suggestions.append(
            f"Interface {iface_name} already has IP addresses (L3) on the device. "
            f"Cannot add l2-service enabled (L2) to the same interface. "
            f"Either: (a) delete the IP addresses first, or (b) use a different sub-interface number."
        )
    
    if "conflict" in error_message.lower():
        suggestions.append("Configuration conflict detected. Check for duplicate entries or incompatible settings.")
    
    if "syntax" in error_message.lower():
        suggestions.append("Check for missing keywords, brackets, or incorrect parameter order.")
    
    if suggestions:
        console.print("\n[yellow]💡 Suggestions:[/yellow]")
        for i, suggestion in enumerate(suggestions, 1):
            console.print(f"   {i}. {suggestion}")
    else:
        console.print("\n[dim]No specific suggestions available. Check the error message for details.[/dim]")


def show_diff_preview(*args, **kwargs):
    """
    Display configuration diff preview.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import show_diff_preview as _impl
    return _impl(*args, **kwargs)


def push_and_verify(*args, **kwargs):
    """
    Push configuration to device and verify.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import push_and_verify as _impl
    return _impl(*args, **kwargs)


def delete_hierarchy(
    device,
    hierarchy: str,
    dry_run: bool = True,
    config_text: str = None,
    quiet: bool = False,
    progress_callback: callable = None
) -> Tuple[bool, str]:
    """
    Delete a hierarchy from device configuration via direct CLI commands.
    
    Uses DNOS flattened one-liner "no" commands from configure mode.
    Example: "no protocols bgp" removes BGP in one command.
    
    For interfaces, uses SMART deletion - keeps physical parents & loopbacks,
    deletes only service interfaces (sub-ifs, PWHE, IRB).
    
    Args:
        device: Target device object
        hierarchy: Hierarchy name (system, interfaces, services, bgp, igp, multihoming)
        dry_run: If True, only run commit check (no actual commit)
        config_text: Optional current config to check what exists
        quiet: If True, suppress console output (for parallel execution)
        progress_callback: Optional callback for progress updates (msg, pct)
    
    Returns:
        Tuple of (success, message)
    """
    from ..config_pusher import ConfigPusher
    
    if hierarchy not in HIERARCHY_DELETE_COMMANDS:
        return False, f"Unknown hierarchy: {hierarchy}. Valid options: {', '.join(HIERARCHY_DELETE_COMMANDS.keys())}"
    
    # Get hierarchy config
    hier_config = HIERARCHY_DELETE_COMMANDS[hierarchy]
    warning = hier_config.get('warning', '')
    
    # SMART INTERFACE DELETION - Keep physical parents & loopbacks, delete service interfaces
    if hierarchy == 'interfaces' and hier_config.get('smart_delete'):
        return _smart_delete_interfaces(device, config_text, dry_run, quiet, progress_callback)
    
    # Get command(s) - some hierarchies have multiple commands (like IGP)
    if 'commands' in hier_config:
        delete_commands = hier_config['commands'].copy()
    else:
        delete_commands = [hier_config['command']]
    
    # For IGP, filter to what actually exists in the config
    if hierarchy == 'igp' and config_text:
        actual_commands = []
        if 'protocols isis' in config_text.lower() or 'isis' in config_text.lower():
            actual_commands.append('no protocols isis')
        if 'protocols ospf' in config_text.lower() or 'ospf' in config_text.lower():
            actual_commands.append('no protocols ospf')
        if actual_commands:
            delete_commands = actual_commands
        else:
            return False, "No IGP (ISIS/OSPF) configuration found to delete."
    
    # Create pusher and execute
    pusher = ConfigPusher()
    
    def progress_cb(msg, pct):
        if progress_callback:
            progress_callback(msg, pct)
        elif not quiet:
            console.print(f"  [dim]{msg}[/dim]")
    
    # Show what we're about to do (unless quiet mode)
    if not quiet:
        console.print(f"\n[bold cyan]Delete Hierarchy: {HIERARCHY_DISPLAY_NAMES.get(hierarchy, hierarchy)}[/bold cyan]")
        if warning:
            console.print(f"[yellow]⚠ {warning}[/yellow]")
        
        console.print(f"\n[bold]DNOS CLI commands to execute:[/bold]")
        console.print(f"  [dim]configure[/dim]")
        for cmd in delete_commands:
            console.print(f"  [yellow]{cmd}[/yellow]")
        console.print(f"  [dim]commit check[/dim]")
        if not dry_run:
            console.print(f"  [dim]commit[/dim]")
    
    success, message, output = pusher.run_cli_commands(
        device=device,
        commands=delete_commands,
        dry_run=dry_run,
        progress_callback=progress_cb
    )
    
    return success, message


def _find_interface_references(config_text: str, interfaces_to_delete: List[str]) -> List[str]:
    """
    Find references to interfaces in other hierarchies and generate delete commands.
    
    When deleting interfaces, we must also remove references to them in:
    - protocols lldp interface <iface>
    - protocols bfd interface <iface>
    - protocols ospf instance <N> area <A> interface <iface>
    - protocols isis instance <N> interface <iface>
    - protocols bgp neighbor <ip> update-source <iface> (delete the neighbor)
    - network-services multihoming interface <iface>
    - interfaces <physical> bundle-id (when bundle is deleted)
    - protocols lacp bundle <N> (when bundle is deleted)
    
    Args:
        config_text: Current device configuration
        interfaces_to_delete: List of interface names being deleted
        
    Returns:
        List of delete commands for interface references
    """
    import re
    
    delete_commands = []
    iface_set = set(interfaces_to_delete)
    
    # === BUNDLE MEMBERSHIP: Remove bundle-id from physical interfaces ===
    # When bundle-X is deleted, physical interfaces with "bundle-id X" need cleanup
    bundles_to_delete = [i for i in interfaces_to_delete if i.lower().startswith('bundle-')]
    if bundles_to_delete:
        # Extract bundle numbers from bundle names (e.g., "bundle-10" -> "10")
        bundle_ids = set()
        for bundle in bundles_to_delete:
            match = re.match(r'bundle-(\d+)', bundle, re.IGNORECASE)
            if match:
                bundle_ids.add(match.group(1))
        
        # Find physical interfaces with bundle-id references
        # Pattern: interface followed by bundle-id N
        iface_pattern = re.compile(r'^  (\S+)\s*\n(?:.*?\n)*?\s+bundle-id\s+(\d+)', re.MULTILINE)
        iface_section_match = re.search(r'^interfaces\s*\n(.*?)(?=^[a-z]|\Z)', config_text, re.MULTILINE | re.DOTALL)
        if iface_section_match:
            iface_section = iface_section_match.group(0)
            
            # Find all interfaces with bundle-id
            for match in re.finditer(r'^  (\S+)\s*\n((?:    .*\n)*)', iface_section, re.MULTILINE):
                iface_name = match.group(1)
                iface_config = match.group(2)
                
                # Check for bundle-id in this interface's config
                bundle_match = re.search(r'bundle-id\s+(\d+)', iface_config)
                if bundle_match and bundle_match.group(1) in bundle_ids:
                    # This physical interface is a member of a deleted bundle
                    delete_commands.append(f'no interfaces {iface_name} bundle-id')
        
        # === LACP: Remove LACP config for deleted bundles ===
        # Pattern: protocols lacp bundle <N>
        for bundle_id in bundle_ids:
            if f'lacp' in config_text.lower() and f'bundle {bundle_id}' in config_text:
                delete_commands.append(f'no protocols lacp bundle {bundle_id}')
    
    # === LLDP interface references ===
    # Pattern: protocols lldp interface <iface>
    lldp_match = re.search(r'protocols\s*\n.*?lldp\s*\n(.*?)(?=^\s{2}[a-z]|\s*!\s*\n\s*!)', config_text, re.MULTILINE | re.DOTALL)
    if lldp_match:
        lldp_section = lldp_match.group(1)
        for iface in interfaces_to_delete:
            if f'interface {iface}' in lldp_section:
                delete_commands.append(f'no protocols lldp interface {iface}')
    
    # === BFD interface references ===
    # Pattern: protocols bfd interface <iface>
    bfd_match = re.search(r'protocols\s*\n.*?bfd\s*\n(.*?)(?=^\s{2}[a-z]|\s*!\s*\n\s*!)', config_text, re.MULTILINE | re.DOTALL)
    if bfd_match:
        bfd_section = bfd_match.group(1)
        for iface in interfaces_to_delete:
            if f'interface {iface}' in bfd_section:
                delete_commands.append(f'no protocols bfd interface {iface}')
    
    # === OSPF interface references ===
    # Pattern: protocols ospf instance <N> area <A> interface <iface>
    ospf_pattern = re.compile(r'instance\s+(\S+)\s*\n.*?area\s+(\S+)\s*\n.*?interface\s+(\S+)', re.DOTALL)
    ospf_section_match = re.search(r'protocols\s*\n.*?ospf\s*\n(.*?)(?=^\s{2}[a-z]|\Z)', config_text, re.MULTILINE | re.DOTALL)
    if ospf_section_match:
        ospf_section = ospf_section_match.group(1)
        # Find all instance/area/interface combos
        for match in re.finditer(r'instance\s+(\S+)', ospf_section):
            instance_id = match.group(1)
            # Find areas within this instance
            instance_start = match.end()
            for area_match in re.finditer(r'area\s+(\S+)', ospf_section[instance_start:]):
                area_id = area_match.group(1)
                area_start = instance_start + area_match.end()
                # Find interfaces within this area
                area_content = ospf_section[area_start:area_start+2000]  # Reasonable chunk
                for iface in interfaces_to_delete:
                    if f'interface {iface}' in area_content:
                        delete_commands.append(f'no protocols ospf instance {instance_id} area {area_id} interface {iface}')
    
    # === ISIS interface references ===
    # Pattern: protocols isis instance <N> interface <iface>
    isis_section_match = re.search(r'protocols\s*\n.*?isis\s*\n(.*?)(?=^\s{2}[a-z]|\Z)', config_text, re.MULTILINE | re.DOTALL)
    if isis_section_match:
        isis_section = isis_section_match.group(1)
        for match in re.finditer(r'instance\s+(\S+)', isis_section):
            instance_id = match.group(1)
            instance_start = match.end()
            instance_content = isis_section[instance_start:instance_start+5000]
            for iface in interfaces_to_delete:
                if f'interface {iface}' in instance_content:
                    delete_commands.append(f'no protocols isis instance {instance_id} interface {iface}')
    
    # === BGP neighbor update-source references ===
    # Pattern: protocols bgp neighbor <ip> update-source <iface>
    # If neighbor uses a deleted interface as update-source, delete the neighbor
    bgp_section_match = re.search(r'protocols\s*\n.*?bgp\s+(\S+)\s*\n(.*?)(?=^protocols|\Z)', config_text, re.MULTILINE | re.DOTALL)
    if bgp_section_match:
        bgp_asn = bgp_section_match.group(1)
        bgp_section = bgp_section_match.group(2)
        
        # Find all neighbors with update-source
        neighbor_pattern = re.compile(r'neighbor\s+(\S+)\s*\n.*?update-source\s+(\S+)', re.DOTALL)
        for match in neighbor_pattern.finditer(bgp_section):
            neighbor_ip = match.group(1)
            update_source = match.group(2)
            if update_source in iface_set:
                # This neighbor uses a deleted interface - delete the neighbor
                delete_commands.append(f'no protocols bgp {bgp_asn} neighbor {neighbor_ip}')
    
    # === Multihoming interface references ===
    # Pattern: network-services multihoming interface <iface>
    mh_section_match = re.search(r'network-services\s*\n.*?multihoming\s*\n(.*?)(?=^\s{2}[a-z]|\Z)', config_text, re.MULTILINE | re.DOTALL)
    if mh_section_match:
        mh_section = mh_section_match.group(1)
        for iface in interfaces_to_delete:
            if f'interface {iface}' in mh_section:
                delete_commands.append(f'no network-services multihoming interface {iface}')
    
    return delete_commands


def _smart_delete_interfaces(
    device,
    config_text: str,
    dry_run: bool = True,
    quiet: bool = False,
    progress_callback: callable = None
) -> Tuple[bool, str]:
    """
    Smart interface deletion - keeps physical parents & loopbacks, deletes service interfaces.
    
    KEEPS:
    - Physical parent interfaces (ge*, xe*, et*, hun*) - no .N suffix
    - Bundle parent interfaces (bundle-N) - no .N suffix  
    - Loopback interfaces (lo*)
    - Control interfaces (ctrl-*, console-*)
    - Management interfaces (mgmt*, ipmi-*)
    
    DELETES:
    - Sub-interfaces (anything with .N suffix)
    - PWHE interfaces (ph*)
    - IRB interfaces (irb*)
    
    Args:
        device: Target device
        config_text: Current device configuration
        dry_run: If True, only run commit check
        quiet: Suppress output
        progress_callback: Progress callback
        
    Returns:
        Tuple of (success, message)
    """
    import re
    from ..config_pusher import ConfigPusher
    
    if not config_text:
        return False, "No configuration available to analyze interfaces"
    
    # Extract interface names from config (2-space indent = interface declaration)
    iface_pattern = re.compile(r'^  (\S+)\s*$', re.MULTILINE)
    
    # Get interfaces section
    iface_section_match = re.search(r'^interfaces\s*\n(.*?)(?=^[a-z]|\Z)', config_text, re.MULTILINE | re.DOTALL)
    if not iface_section_match:
        return False, "No interfaces section found in configuration"
    
    iface_section = iface_section_match.group(0)
    all_interfaces = iface_pattern.findall(iface_section)
    
    # Filter out non-interface lines (like '!')
    all_interfaces = [i for i in all_interfaces if not i.startswith('!') and i]
    
    if not all_interfaces:
        return False, "No interfaces found in configuration"
    
    # Categorize interfaces
    to_keep = []
    to_delete = []
    
    for iface in all_interfaces:
        iface_lower = iface.lower()
        base = iface.split('.')[0].lower()
        has_suffix = '.' in iface  # Sub-interface indicator
        
        # ALWAYS KEEP: Physical parents (no .N suffix)
        if not has_suffix and (base.startswith('ge') or base.startswith('xe') or 
                               base.startswith('et') or base.startswith('te') or 
                               base.startswith('hun')):
            to_keep.append(iface)
        # ALWAYS KEEP: Bundle parents (no .N suffix)
        elif not has_suffix and base.startswith('bundle'):
            to_keep.append(iface)
        # ALWAYS KEEP: Loopbacks
        elif base.startswith('lo'):
            to_keep.append(iface)
        # ALWAYS KEEP: Control/Console interfaces
        elif base.startswith('ctrl') or base.startswith('console'):
            to_keep.append(iface)
        # ALWAYS KEEP: Management/IPMI interfaces
        elif base.startswith('mgmt') or base.startswith('ipmi'):
            to_keep.append(iface)
        # DELETE: Sub-interfaces (anything with .N)
        elif has_suffix:
            to_delete.append(iface)
        # DELETE: PWHE interfaces
        elif base.startswith('ph'):
            to_delete.append(iface)
        # DELETE: IRB interfaces
        elif base.startswith('irb'):
            to_delete.append(iface)
        else:
            # Unknown - keep by default for safety
            to_keep.append(iface)
    
    if not to_delete:
        return False, "No service interfaces found to delete (all interfaces are physical parents or loopbacks)"
    
    # Generate delete commands - flattened one-liner format
    delete_commands = []
    
    # Also find and delete references to these interfaces in other hierarchies
    # This ensures clean deletion without orphaned references
    cascading_deletes = _find_interface_references(config_text, to_delete)
    
    # Add cascading deletes FIRST (delete references before deleting the interface)
    delete_commands.extend(cascading_deletes)
    
    # Then add the interface delete commands
    delete_commands.extend([f"no interfaces {iface}" for iface in to_delete])
    
    if not quiet:
        console.print(f"\n[bold cyan]Smart Interface Deletion[/bold cyan]")
        console.print(f"[green]✓ KEEPING {len(to_keep)} interfaces:[/green] physical parents, bundles, loopbacks, ctrl, mgmt")
        if to_keep[:5]:
            console.print(f"  [dim]Examples: {', '.join(to_keep[:5])}{'...' if len(to_keep) > 5 else ''}[/dim]")
        
        console.print(f"[red]✗ DELETING {len(to_delete)} interfaces:[/red] sub-ifs, PWHE, IRB")
        if to_delete[:5]:
            console.print(f"  [dim]Examples: {', '.join(to_delete[:5])}{'...' if len(to_delete) > 5 else ''}[/dim]")
        
        # Show cascading deletes if any
        if cascading_deletes:
            console.print(f"\n[yellow]⚠ CASCADING DELETES ({len(cascading_deletes)} references):[/yellow]")
            console.print(f"  [dim]Removing interface references from other hierarchies (LLDP, BFD, OSPF, ISIS, BGP, MH)[/dim]")
            
            # Group by type for better display
            bundle_id_count = len([c for c in cascading_deletes if 'bundle-id' in c])
            lacp_count = len([c for c in cascading_deletes if 'lacp' in c])
            lldp_count = len([c for c in cascading_deletes if 'lldp' in c])
            bfd_count = len([c for c in cascading_deletes if 'bfd' in c])
            ospf_count = len([c for c in cascading_deletes if 'ospf' in c])
            isis_count = len([c for c in cascading_deletes if 'isis' in c])
            bgp_count = len([c for c in cascading_deletes if 'bgp' in c])
            mh_count = len([c for c in cascading_deletes if 'multihoming' in c])
            
            if bundle_id_count: console.print(f"  [yellow]• Bundle membership: {bundle_id_count} physical interfaces[/yellow]")
            if lacp_count: console.print(f"  [dim]• LACP: {lacp_count} bundle configs[/dim]")
            if lldp_count: console.print(f"  [dim]• LLDP: {lldp_count} interface refs[/dim]")
            if bfd_count: console.print(f"  [dim]• BFD: {bfd_count} interface refs[/dim]")
            if ospf_count: console.print(f"  [dim]• OSPF: {ospf_count} interface refs[/dim]")
            if isis_count: console.print(f"  [dim]• ISIS: {isis_count} interface refs[/dim]")
            if bgp_count: console.print(f"  [yellow]• BGP: {bgp_count} neighbors (using deleted interface as update-source)[/yellow]")
            if mh_count: console.print(f"  [dim]• Multihoming: {mh_count} interface refs[/dim]")
        
        console.print(f"\n[bold]DNOS CLI commands ({len(delete_commands)} total):[/bold]")
        console.print(f"  [dim]configure[/dim]")
        # Show first few commands - prioritize cascading deletes
        shown = 0
        for cmd in delete_commands[:15]:
            if shown < 10:
                if 'no interfaces' not in cmd:
                    console.print(f"  [yellow]{cmd}[/yellow]")
                else:
                    console.print(f"  [red]{cmd}[/red]")
                shown += 1
        if len(delete_commands) > 15:
            console.print(f"  [dim]... and {len(delete_commands) - 15} more delete commands[/dim]")
        console.print(f"  [dim]commit check[/dim]")
        if not dry_run:
            console.print(f"  [dim]commit[/dim]")
    
    # Execute delete commands
    pusher = ConfigPusher()
    
    def progress_cb(msg, pct):
        if progress_callback:
            progress_callback(msg, pct)
        elif not quiet:
            console.print(f"  [dim]{msg}[/dim]")
    
    success, message, output = pusher.run_cli_commands(
        device=device,
        commands=delete_commands,
        dry_run=dry_run,
        progress_callback=progress_cb
    )
    
    if success:
        return True, f"Deleted {len(to_delete)} service interfaces (kept {len(to_keep)} physical/loopback)"
    else:
        return False, message


def show_delete_hierarchy_menu(device, config_text: str = None) -> Optional[str]:
    """
    Show menu to select which hierarchy to delete.
    
    Args:
        device: Target device
        config_text: Current device configuration (for showing what exists)
    
    Returns:
        Selected hierarchy name or None if cancelled
    """
    console.print("\n[bold red]⚠ DELETE HIERARCHY[/bold red]")
    console.print("[yellow]This will remove entire configuration sections from the device.[/yellow]")
    console.print()
    
    # Show available hierarchies
    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Hierarchy", style="cyan")
    table.add_column("DNOS Command", style="yellow")
    table.add_column("Warning", style="red")
    
    options = list(HIERARCHY_DELETE_COMMANDS.keys())
    
    for i, hier in enumerate(options, 1):
        hier_config = HIERARCHY_DELETE_COMMANDS[hier]
        # Get command(s)
        if hier_config.get('smart_delete'):
            cmd_display = "(Smart: keeps physical, deletes service ifs)"
        elif 'commands' in hier_config:
            cmd_display = ' / '.join(hier_config['commands'])
        else:
            cmd_display = hier_config.get('command', 'N/A')
        warning = "⚠ CRITICAL" if hier in CRITICAL_HIERARCHIES and not hier_config.get('smart_delete') else ""
        table.add_row(str(i), HIERARCHY_DISPLAY_NAMES.get(hier, hier), cmd_display, warning)
    
    console.print(table)
    console.print("  [B] Back/Cancel")
    
    # Get choice
    valid_choices = [str(i) for i in range(1, len(options) + 1)] + ['b', 'B']
    choice = Prompt.ask("Select hierarchy to delete", choices=valid_choices, default="b")
    
    if choice.lower() == 'b':
        return None
    
    return options[int(choice) - 1]


def confirm_delete_hierarchy(hierarchy: str, device) -> bool:
    """
    Show confirmation prompt before deleting a hierarchy.
    
    For critical hierarchies, requires typing 'DELETE' to confirm.
    
    Args:
        hierarchy: Hierarchy name
        device: Target device
    
    Returns:
        True if user confirms, False otherwise
    """
    display_name = HIERARCHY_DISPLAY_NAMES.get(hierarchy, hierarchy)
    hier_config = HIERARCHY_DELETE_COMMANDS[hierarchy]
    
    console.print(f"\n[bold cyan]{'═' * 60}[/bold cyan]")
    console.print(f"[bold cyan]Delete {display_name}[/bold cyan]")
    console.print(f"[bold cyan]{'═' * 60}[/bold cyan]")
    console.print(f"\nDevice: [cyan]{device.hostname}[/cyan] ({device.ip})")
    
    # SMART DELETE for interfaces - show different message
    if hier_config.get('smart_delete'):
        console.print(f"\n[bold green]SMART DELETE MODE[/bold green]")
        console.print("[green]✓ KEEPS:[/green] Physical parents (ge/xe/et/bundle), Loopbacks (lo*), Control, Management")
        console.print("[red]✗ DELETES:[/red] Sub-interfaces (*.N), PWHE (ph*), IRB (irb*)")
        console.print(f"\n[dim]Commands will be generated dynamically based on current config.[/dim]")
    else:
        # Get command(s)
        if 'commands' in hier_config:
            commands = hier_config['commands']
        else:
            commands = [hier_config['command']] if hier_config.get('command') else []
        
        # Show the command sequence
        if commands:
            console.print(f"\n[bold]DNOS CLI commands to execute:[/bold]")
            console.print(f"  [dim]configure[/dim]")
            for cmd in commands:
                console.print(f"  [yellow]{cmd}[/yellow]")
            console.print(f"  [dim]commit check[/dim]")
            console.print(f"  [dim]commit[/dim]")
    
    # Show warning if present
    if hier_config.get('warning'):
        console.print(f"\n[yellow]⚠ {hier_config['warning']}[/yellow]")
    
    if hierarchy in CRITICAL_HIERARCHIES:
        # For interfaces with smart_delete, it's less critical
        if hier_config.get('smart_delete'):
            console.print(f"\n[yellow]⚠ This will delete service interfaces but preserve physical connectivity.[/yellow]")
            return Confirm.ask(f"\nProceed with smart interface deletion?", default=True)
        else:
            console.print(f"\n[bold red]⚠ This is a CRITICAL hierarchy![/bold red]")
        console.print("[yellow]Deleting this may cause connectivity loss or service disruption.[/yellow]")
        console.print("\n[bold]Type 'DELETE' to confirm, or anything else to cancel:[/bold]")
        confirm = Prompt.ask("Confirm")
        return confirm == "DELETE"
    else:
        return Confirm.ask(f"\nDelete {display_name} from {device.hostname}?", default=True)


def execute_delete_hierarchy(device, hierarchy: str, config_text: str = None) -> bool:
    """
    Execute the full delete hierarchy workflow with confirmations.
    
    Args:
        device: Target device
        hierarchy: Hierarchy to delete
        config_text: Current device configuration
    
    Returns:
        True if deletion was successful, False otherwise
    """
    # Step 1: Confirm
    if not confirm_delete_hierarchy(hierarchy, device):
        console.print("[dim]Delete cancelled.[/dim]")
        return False
    
    # Step 2: Dry run first (send commands + commit check, no actual commit)
    console.print("\n[bold cyan]Step 1: Sending delete commands + validating (dry run)...[/bold cyan]")
    success, message = delete_hierarchy(device, hierarchy, dry_run=True, config_text=config_text)
    
    if not success:
        console.print(f"\n[bold red]✗ Commit check failed:[/bold red]")
        console.print(f"  [red]{message}[/red]")
        suggest_error_fix(message)
        return False
    
    console.print(f"\n[bold green]✓ {message}[/bold green]")
    
    # Step 3: Ask to proceed with actual commit
    if not Confirm.ask("\nProceed with actual commit?", default=True):
        console.print("[dim]Commit cancelled. No changes made.[/dim]")
        return False
    
    # Step 4: Execute actual delete
    console.print("\n[bold cyan]Step 2: Committing changes...[/bold cyan]")
    success, message = delete_hierarchy(device, hierarchy, dry_run=False, config_text=config_text)
    
    if success:
        console.print(f"\n[bold green]✓ {message}[/bold green]")
        display_name = HIERARCHY_DISPLAY_NAMES.get(hierarchy, hierarchy)
        console.print(f"\n[green]{display_name} has been deleted from {device.hostname}[/green]")
    else:
        console.print(f"\n[bold red]✗ Delete failed:[/bold red]")
        console.print(f"  [red]{message}[/red]")
        suggest_error_fix(message)
    
    return success


# ==============================================================================
# MULTI-DEVICE DELETE OPERATIONS
# ==============================================================================

# Sub-hierarchy delete commands - more granular deletion
SUB_HIERARCHY_DELETE_COMMANDS = {
    # Network Services sub-hierarchies
    'fxc_instance': {
        'pattern': 'no network-services evpn-vpws-fxc instance {name}',
        'description': 'Delete specific FXC instance'
    },
    'evpn_instance': {
        'pattern': 'no network-services evpn instance {name}',
        'description': 'Delete specific EVPN instance'
    },
    'vrf_instance': {
        'pattern': 'no network-services vrf instance {name}',
        'description': 'Delete specific VRF instance'
    },
    'service_interface': {
        'pattern': 'network-services evpn-vpws-fxc instance {service}\nno interface {interface}',
        'description': 'Delete interface from FXC service'
    },
    
    # BGP sub-hierarchies
    'bgp_neighbor': {
        'pattern': 'protocols bgp\nno neighbor {neighbor}',
        'description': 'Delete specific BGP neighbor'
    },
    'bgp_peer_group': {
        'pattern': 'protocols bgp\nno peer-group {name}',
        'description': 'Delete BGP peer group'
    },
    
    # Interface sub-hierarchies
    'interface': {
        'pattern': 'no interfaces {interface}',
        'description': 'Delete specific interface'
    },
    'interface_range': {
        'pattern': None,  # Dynamic - multiple interfaces
        'description': 'Delete range of interfaces'
    },
    
    # Multihoming sub-hierarchies
    'mh_interface': {
        'pattern': 'network-services multihoming\nno interface {interface}',
        'description': 'Delete interface from multihoming'
    },
}


def delete_sub_hierarchy(
    device,
    sub_type: str,
    params: Dict[str, str],
    dry_run: bool = True
) -> Tuple[bool, str]:
    """
    Delete a sub-hierarchy (granular deletion) from device configuration.
    
    Args:
        device: Target device object
        sub_type: Sub-hierarchy type from SUB_HIERARCHY_DELETE_COMMANDS
        params: Parameters to fill in the command pattern
        dry_run: If True, only run commit check
    
    Returns:
        Tuple of (success, message)
    """
    from ..config_pusher import ConfigPusher
    
    if sub_type not in SUB_HIERARCHY_DELETE_COMMANDS:
        return False, f"Unknown sub-hierarchy type: {sub_type}"
    
    sub_config = SUB_HIERARCHY_DELETE_COMMANDS[sub_type]
    pattern = sub_config['pattern']
    
    if pattern is None:
        return False, f"Sub-hierarchy type '{sub_type}' requires dynamic command generation"
    
    # Fill in parameters
    try:
        command = pattern.format(**params)
    except KeyError as e:
        return False, f"Missing parameter: {e}"
    
    # Split into multiple commands if needed
    commands = [cmd.strip() for cmd in command.split('\n') if cmd.strip()]
    
    # Execute
    pusher = ConfigPusher()
    
    console.print(f"\n[bold cyan]Delete: {sub_config['description']}[/bold cyan]")
    console.print(f"[dim]Commands: {' > '.join(commands)}[/dim]")
    
    success, message, output = pusher.run_cli_commands(
        device=device,
        commands=commands,
        dry_run=dry_run
    )
    
    return success, message


def delete_interface_range(
    device,
    interfaces: List[str],
    dry_run: bool = True
) -> Tuple[bool, str]:
    """
    Delete a range of interfaces from device configuration.
    
    Args:
        device: Target device object
        interfaces: List of interface names to delete
        dry_run: If True, only run commit check
    
    Returns:
        Tuple of (success, message)
    """
    from ..config_pusher import ConfigPusher
    
    if not interfaces:
        return False, "No interfaces specified"
    
    # Build commands
    commands = [f"no interfaces {iface}" for iface in interfaces]
    
    # Execute
    pusher = ConfigPusher()
    
    console.print(f"\n[bold cyan]Delete {len(interfaces)} Interfaces[/bold cyan]")
    console.print(f"[dim]First: {interfaces[0]}, Last: {interfaces[-1]}[/dim]")
    
    success, message, output = pusher.run_cli_commands(
        device=device,
        commands=commands,
        dry_run=dry_run
    )
    
    return success, message


def delete_hierarchy_multi(
    multi_ctx,
    hierarchy: str,
    sub_path: Optional[str] = None,
    dry_run: bool = True
) -> Dict[str, Tuple[bool, str]]:
    """
    Delete hierarchy from all devices in a MultiDeviceContext in PARALLEL.
    
    Args:
        multi_ctx: MultiDeviceContext with devices to operate on
        hierarchy: Hierarchy name (system, interfaces, services, bgp, igp, multihoming)
        sub_path: Optional sub-hierarchy path (e.g., "evpn-vpws-fxc FXC-100")
        dry_run: If True, only run commit check (no actual commit)
    
    Returns:
        Dict of hostname -> (success, message)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from rich.live import Live
    from rich.table import Table as RichTable
    from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
    from rich.panel import Panel
    from rich.columns import Columns
    import threading
    import time
    
    results = {}
    
    display_name = HIERARCHY_DISPLAY_NAMES.get(hierarchy, hierarchy)
    action_word = "Commit Check" if dry_run else "Deleting"
    
    console.print(f"\n[bold cyan]Multi-Device Delete: {display_name}[/bold cyan]")
    device_names = ", ".join([d.hostname for d in multi_ctx.devices])
    console.print(f"[dim]Devices: {device_names}[/dim]")
    
    if sub_path:
        console.print(f"[dim]Sub-path: {sub_path}[/dim]")
    
    # ========================================================================
    # TIME ESTIMATION FOR DELETE OPERATIONS
    # ========================================================================
    from ..config_pusher import get_accurate_push_estimates, save_timing_record
    
    # Build a representative config for estimation
    interface_count = 0
    if hasattr(multi_ctx, '_pending_interface_deletes'):
        interface_count = len(multi_ctx._pending_interface_deletes)
    
    # Create a mock delete config for estimation
    delete_lines = []
    if sub_path:
        delete_lines.append(f"no network-services {sub_path}")
    else:
        hier_config = HIERARCHY_DELETE_COMMANDS.get(hierarchy, {})
        if 'commands' in hier_config:
            delete_lines.extend(hier_config['commands'])
        elif 'command' in hier_config:
            delete_lines.append(hier_config['command'])
    
    # Add interface deletes if applicable
    if interface_count > 0:
        for i in range(interface_count):
            delete_lines.append(f"no interfaces ph{i}.1")
    
    delete_config = '\n'.join(delete_lines)
    
    # Get accurate estimate
    estimates = get_accurate_push_estimates(
        config_text=delete_config,
        platform=multi_ctx.devices[0].platform.value if multi_ctx.devices else "SA-36CD-S",
        include_delete=True
    )
    
    estimated_seconds = estimates['estimates']['terminal_paste']['total']
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
        console.print(f"\n[green]⏱️  Est. ~{format_time(estimated_seconds)} - {source_detail}[/green]")
    elif source == 'scale_type':
        console.print(f"\n[yellow]⏱️  Est. ~{format_time(estimated_seconds)} - {source_detail}[/yellow]")
    else:
        console.print(f"\n[dim]⏱️  Est. ~{format_time(estimated_seconds)} - {source_detail}[/dim]")
    operation_start_time = time.time()
    
    # Track progress per device with more detail
    device_progress = {
        dev.hostname: {
            "status": "pending", 
            "message": "", 
            "progress": 0,
            "stage": "waiting",
            "terminal_output": []
        } for dev in multi_ctx.devices
    }
    progress_lock = threading.Lock()
    
    def delete_from_device(device):
        """Delete hierarchy from a single device."""
        hostname = device.hostname
        
        def progress_cb(msg, pct):
            """Progress callback for live updates."""
            with progress_lock:
                device_progress[hostname]["progress"] = pct
                device_progress[hostname]["message"] = msg[:40]
                device_progress[hostname]["terminal_output"].append(msg)
                if pct < 30:
                    device_progress[hostname]["stage"] = "connecting"
                elif pct < 70:
                    device_progress[hostname]["stage"] = "executing"
                else:
                    device_progress[hostname]["stage"] = "committing"
        
        with progress_lock:
            device_progress[hostname]["status"] = "running"
            device_progress[hostname]["message"] = "Connecting..."
            device_progress[hostname]["stage"] = "connecting"
        
        try:
            config_text = multi_ctx.configs.get(hostname, "")
            
            if sub_path:
                success, message = _execute_sub_hierarchy_delete(
                    device, hierarchy, sub_path, config_text, dry_run, multi_ctx, progress_cb
                )
            else:
                success, message = delete_hierarchy(
                    device, hierarchy, 
                    dry_run=dry_run, 
                    config_text=config_text,
                    quiet=True,  # Suppress console output for parallel mode
                    progress_callback=progress_cb
                )
            
            with progress_lock:
                device_progress[hostname]["status"] = "success" if success else "error"
                device_progress[hostname]["progress"] = 100 if success else device_progress[hostname]["progress"]
                device_progress[hostname]["message"] = message[:50] if message else ("Done!" if success else "Failed")
                device_progress[hostname]["stage"] = "done" if success else "error"
            
            return hostname, success, message
            
        except Exception as e:
            with progress_lock:
                device_progress[hostname]["status"] = "error"
                device_progress[hostname]["message"] = str(e)[:50]
                device_progress[hostname]["stage"] = "error"
            return hostname, False, str(e)
    
    def render_progress():
        """Render parallel progress panels for each device (like push does)."""
        panels = []
        
        for dev in multi_ctx.devices:
            hostname = dev.hostname
            info = device_progress[hostname]
            status = info["status"]
            progress = info["progress"]
            message = info["message"]
            stage = info["stage"]
            terminal_lines = info["terminal_output"][-10:]  # Last 10 lines for display
            
            # Build panel content
            content_lines = []
            
            # Status line
            if status == "pending":
                status_str = "[dim]⏳ Waiting...[/dim]"
            elif status == "running":
                if stage == "connecting":
                    status_str = "[yellow]🔌 Connecting...[/yellow]"
                elif stage == "executing":
                    status_str = "[cyan]⚡ Executing...[/cyan]"
                elif stage == "committing":
                    status_str = "[magenta]💾 Committing...[/magenta]"
                else:
                    status_str = "[yellow]⟳ Running...[/yellow]"
            elif status == "success":
                status_str = "[green]✓ Complete[/green]"
            else:
                status_str = "[red]✗ Error[/red]"
            
            content_lines.append(f"Status: {status_str}")
            
            # Progress bar
            bar_width = 20
            filled = int(bar_width * progress / 100)
            bar = "█" * filled + "░" * (bar_width - filled)
            if status == "success":
                bar_color = "green"
            elif status == "error":
                bar_color = "red"
            elif status == "running":
                bar_color = "cyan"
            else:
                bar_color = "dim"
            content_lines.append(f"[{bar_color}]{bar}[/{bar_color}] {progress}%")
            
            # Current action
            if message:
                content_lines.append(f"[dim]{message}[/dim]")
            
            # Terminal output - show more lines with proper coloring
            PANEL_WIDTH = 70
            MAX_TERMINAL_LINES = 8
            content_lines.append("")
            content_lines.append(f"[dim]{'─' * (PANEL_WIDTH - 4)}[/dim]")
            
            lines_shown = 0
            for line in terminal_lines[-MAX_TERMINAL_LINES:]:
                clean = line[:PANEL_WIDTH - 4].replace('[', '\\[').replace(']', '\\]')
                # Color-code based on content
                is_error = any(err in clean.lower() for err in ['error', 'failed', 'cannot'])
                if clean.startswith('→') or 'no ' in clean.lower():
                    content_lines.append(f"[bright_red]{clean}[/bright_red]")  # Delete commands in red
                elif clean.startswith('←') or clean.startswith('✓'):
                    content_lines.append(f"[green]{clean}[/green]")
                elif is_error or clean.startswith('✗'):
                    content_lines.append(f"[bold red]{clean}[/bold red]")
                else:
                    content_lines.append(f"[dim]{clean}[/dim]")
                lines_shown += 1
            
            # Pad to fixed height
            while lines_shown < MAX_TERMINAL_LINES:
                content_lines.append("")
                lines_shown += 1
            
            # Border color based on status
            if status == "success":
                border = "green"
            elif status == "error":
                border = "red"
            elif status == "running":
                border = "cyan"
            else:
                border = "dim"
            
            panel = Panel(
                "\n".join(content_lines),
                title=f"[bold]{hostname}[/bold]",
                border_style=border,
                width=PANEL_WIDTH
            )
            panels.append(panel)
        
        return Columns(panels, expand=True)
    
    # Show action header
    console.print(f"\n[bold]{action_word}: {display_name}[/bold]")
    console.print()
    
    # Execute in parallel with live progress display
    # Use transient=True to avoid duplicate panel rendering
    with Live(render_progress(), refresh_per_second=4, console=console, transient=True) as live:
        with ThreadPoolExecutor(max_workers=len(multi_ctx.devices)) as executor:
            futures = {executor.submit(delete_from_device, dev): dev for dev in multi_ctx.devices}
            
            while any(f.running() for f in futures):
                live.update(render_progress())
                time.sleep(0.25)
            
            for future in as_completed(futures):
                hostname, success, message = future.result()
                results[hostname] = (success, message)
            
            # Final update before live ends
            live.update(render_progress())
    
    # Print final result panels (since transient=True removed the live display)
    console.print(render_progress())
    
    # Calculate actual time and save for future estimates
    actual_time = time.time() - operation_start_time
    
    # Save timing for learning (use proper function signature)
    success_count = sum(1 for s, _ in results.values() if s)
    if success_count > 0 and not dry_run:
        try:
            # Get first device for platform info
            first_dev = multi_ctx.devices[0] if multi_ctx.devices else None
            platform = first_dev.platform.value if first_dev else "unknown"
            config_lines = sum(len(multi_ctx.configs.get(d.hostname, "").splitlines()) for d in multi_ctx.devices)
            
            save_timing_record(
                platform=platform,
                line_count=config_lines,
                pwhe_count=0,
                fxc_count=0,
                actual_time_seconds=actual_time,
                device_hostname=first_dev.hostname if first_dev else None,
                push_type=delete_type
            )
        except Exception as e:
            console.print(f"[dim]Note: Could not save timing record: {e}[/dim]")
    
    # Show timing comparison
    console.print(f"\n[dim]⏱️  Completed in {actual_time:.1f}s (estimate was {estimated_seconds:.0f}s)[/dim]")
    
    # Summary
    _show_multi_delete_summary(results, hierarchy, dry_run)
    
    return results


def _execute_sub_hierarchy_delete(
    device,
    hierarchy: str,
    sub_path: str,
    config_text: str,
    dry_run: bool,
    multi_ctx=None,
    progress_callback=None
) -> Tuple[bool, str]:
    """
    Execute a sub-hierarchy deletion based on the hierarchy and sub-path.
    
    Args:
        device: Target device
        hierarchy: Parent hierarchy
        sub_path: Sub-path specification
        config_text: Current device config
        dry_run: If True, only commit check
        multi_ctx: MultiDeviceContext (optional, for interface deletion tracking)
        progress_callback: Callback for progress updates (msg, pct)
    
    Returns:
        Tuple of (success, message)
    """
    def report(msg, pct):
        """Report progress if callback provided."""
        if progress_callback:
            progress_callback(msg, pct)
    from ..config_pusher import ConfigPusher
    
    # Parse the sub-path to build the correct command
    parts = sub_path.split()
    
    if hierarchy == 'services':
        # Handle service sub-hierarchy
        
        # Check for +interfaces suffix (delete services AND their attached interfaces)
        delete_interfaces = False
        interface_list = []
        if '+interfaces' in sub_path:
            delete_interfaces = True
            sub_path = sub_path.replace('+interfaces', '').strip()
            parts = sub_path.split()  # Re-parse after removing suffix
            
            # Get pending interface deletes from multi_ctx if available
            # NOTE: Don't delete yet - we need it for both dry_run and actual commit
            if hasattr(multi_ctx, '_pending_interface_deletes'):
                interface_list = list(multi_ctx._pending_interface_deletes)  # Copy the list
        
        # Extract service type from the first part of sub_path
        service_type = parts[0] if parts else sub_path  # e.g., "evpn-vpws" or "evpn-vpws-fxc"
        
        if len(parts) >= 2:
            if parts[1] == 'instance' and len(parts) >= 3:
                # Delete specific instance
                instance_name = parts[2]
                command = f"no network-services {service_type} instance {instance_name}"
            elif parts[1] == 'interface' and len(parts) >= 3:
                # Delete interface from service - need service name first
                # Format: "evpn-vpws-fxc FXC-100 interface ph100.1"
                if len(parts) >= 4:
                    instance_name = parts[1]
                    interface = parts[3]
                    commands = [
                        f"network-services {service_type} instance {instance_name}",
                        f"no interface {interface}"
                    ]
                    pusher = ConfigPusher()
                    success, message, _ = pusher.run_cli_commands(device, commands, dry_run)
                    return success, message
                else:
                    return False, f"Invalid sub-path format: {sub_path}"
            else:
                command = f"no network-services {sub_path}"
        else:
            command = f"no network-services {sub_path}"
        
        # If deleting interfaces too, build combined command list
        if delete_interfaces and interface_list:
            pusher = ConfigPusher()
            
            # Step 1: Build ALL delete commands first
            report(f"Step 1: Deleting {service_type} services...", 5)
            report(f"→ {command}", 8)
            
            report(f"Step 2: Deleting {len(interface_list):,} attached interfaces...", 10)
            
            # Sort interfaces numerically by sub-interface number
            # e.g., ge400-0/0/4.1, ge400-0/0/4.2, ..., ge400-0/0/4.10, ge400-0/0/4.100
            def get_subif_number(iface_name):
                """Extract numeric sub-interface ID for sorting."""
                if '.' in iface_name:
                    try:
                        return int(iface_name.split('.')[-1])
                    except ValueError:
                        return 0
                return 0
            
            sorted_interfaces = sorted(interface_list, key=get_subif_number)
            
            # Build interface delete commands
            # DNOS uses FLAT structure: interfaces are siblings, not nested
            # Delete syntax: "no interfaces <interface-name>"
            iface_commands = []
            for iface in sorted_interfaces:
                iface_commands.append(f"no interfaces {iface}")
            
            # Show sample interface commands
            for cmd in iface_commands[:3]:
                report(f"→ {cmd}", 12)
            if len(iface_commands) > 3:
                report(f"→ ... and {len(iface_commands) - 3:,} more interface deletes", 14)
            
            # Combine all commands: service delete + interface deletes
            all_commands = [command] + iface_commands
            total_cmds = len(all_commands)
            
            report(f"Total: {total_cmds:,} delete commands prepared", 20)
            
            # Step 3: Send all delete commands, THEN commit check
            report(f"Step 3: Sending delete commands...", 25)
            
            # Pass report as progress callback to show real-time status
            def cmd_progress(msg, pct):
                report(f"{msg}", 25 + int(pct * 0.5))  # Scale 0-100 to 25-75
            
            success, message, output = pusher.run_cli_commands(device, all_commands, dry_run, progress_callback=cmd_progress)
            
            # Report command output lines
            if output:
                for line in output.split('\n')[-5:]:
                    if line.strip():
                        report(f"← {line.strip()[:60]}", 80)
            
            if success:
                report(f"✓ Deleted {service_type} + {len(interface_list):,} interfaces", 100)
            else:
                report(f"✗ Delete failed: {message[:50]}", 80)
            
            return success, message
    
    elif hierarchy == 'bgp':
        if parts[0] == 'neighbor' and len(parts) >= 2:
            neighbor_ip = parts[1]
            commands = ["protocols bgp", f"no neighbor {neighbor_ip}"]
            pusher = ConfigPusher()
            success, message, _ = pusher.run_cli_commands(device, commands, dry_run)
            return success, message
        elif parts[0] == 'peer-group' and len(parts) >= 2:
            pg_name = parts[1]
            commands = ["protocols bgp", f"no peer-group {pg_name}"]
            pusher = ConfigPusher()
            success, message, _ = pusher.run_cli_commands(device, commands, dry_run)
            return success, message
        else:
            command = f"no protocols bgp {sub_path}"
    
    elif hierarchy == 'interfaces':
        # Delete specific interface
        command = f"no interfaces {sub_path}"
    
    elif hierarchy == 'multihoming':
        if parts[0] == 'interface' and len(parts) >= 2:
            interface = parts[1]
            commands = ["network-services multihoming", f"no interface {interface}"]
            pusher = ConfigPusher()
            success, message, _ = pusher.run_cli_commands(device, commands, dry_run)
            return success, message
        else:
            command = f"no network-services multihoming {sub_path}"
    
    else:
        # Generic sub-path
        hier_config = HIERARCHY_DELETE_COMMANDS.get(hierarchy, {})
        base_cmd = hier_config.get('command', f'no {hierarchy}')
        command = f"{base_cmd} {sub_path}"
    
    # Execute single command with progress
    report(f"→ {command}", 20)
    pusher = ConfigPusher()
    success, message, output = pusher.run_cli_commands(device, [command], dry_run)
    
    # Report output
    if output:
        for line in output.split('\n')[-3:]:
            if line.strip():
                report(f"← {line.strip()[:60]}", 70)
    
    if success:
        report(f"✓ Delete complete", 100)
    else:
        report(f"✗ {message[:50]}", 70)
    
    return success, message


def _show_multi_delete_summary(
    results: Dict[str, Tuple[bool, str]],
    hierarchy: str,
    dry_run: bool
):
    """Display summary of multi-device delete operation."""
    console.print("\n" + "═" * 60)
    
    success_count = sum(1 for s, _ in results.values() if s)
    total = len(results)
    
    if success_count == total:
        if dry_run:
            console.print(f"[bold green]✓ Commit check passed on all {total} devices[/bold green]")
        else:
            console.print(f"[bold green]✓ Successfully deleted from all {total} devices[/bold green]")
    else:
        console.print(f"[bold yellow]⚠ {success_count}/{total} devices succeeded[/bold yellow]")
        
        # Show failures
        for hostname, (success, message) in results.items():
            if not success:
                console.print(f"  [red]✗ {hostname}: {message}[/red]")


def show_delete_hierarchy_menu_multi(
    multi_ctx,
    include_sub_hierarchy: bool = True
) -> Tuple[Optional[str], Optional[str]]:
    """
    Show menu to select hierarchy for multi-device deletion.
    
    Args:
        multi_ctx: MultiDeviceContext
        include_sub_hierarchy: Whether to offer sub-hierarchy deletion
    
    Returns:
        Tuple of (hierarchy, sub_path) or (None, None) if cancelled
    """
    device_names = ", ".join([d.hostname for d in multi_ctx.devices])
    
    console.print(f"\n[bold red]⚠ MULTI-DEVICE DELETE[/bold red]")
    console.print(f"[yellow]Target devices: {device_names}[/yellow]")
    console.print("[yellow]This will remove configuration from ALL selected devices.[/yellow]")
    console.print()
    
    # Show hierarchy options
    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Hierarchy", style="cyan")
    table.add_column("DNOS Command", style="yellow")
    
    options = list(HIERARCHY_DELETE_COMMANDS.keys())
    
    for i, hier in enumerate(options, 1):
        hier_config = HIERARCHY_DELETE_COMMANDS[hier]
        if 'commands' in hier_config:
            cmd_display = ' / '.join(hier_config['commands'])
        else:
            cmd_display = hier_config['command']
        table.add_row(str(i), HIERARCHY_DISPLAY_NAMES.get(hier, hier), cmd_display)
    
    console.print(table)
    
    if include_sub_hierarchy:
        console.print("  [G] Granular deletion (specific items)")
    console.print("  [B] Back/Cancel")
    
    # Get choice
    valid_choices = [str(i) for i in range(1, len(options) + 1)] + ['b', 'B']
    if include_sub_hierarchy:
        valid_choices.extend(['g', 'G'])
    
    choice = Prompt.ask("Select", choices=valid_choices, default="b")
    
    if choice.lower() == 'b':
        return None, None
    
    if choice.lower() == 'g':
        # Granular deletion menu
        return _show_granular_delete_menu(multi_ctx)
    
    hierarchy = options[int(choice) - 1]
    
    # Ask if user wants to delete specific sub-path
    if include_sub_hierarchy and Confirm.ask(
        f"\nDelete specific items within {HIERARCHY_DISPLAY_NAMES.get(hierarchy, hierarchy)}?",
        default=False
    ):
        # For services hierarchy, show detected service types from config
        if hierarchy == 'services' and multi_ctx:
            sub_path = _show_service_type_delete_menu(multi_ctx)
            if sub_path:
                return hierarchy, sub_path
            return None, None
        else:
            sub_path = Prompt.ask("Enter sub-path (or 'b' to go back)", default="")
            if sub_path.lower() in ('b', 'back', ''):
                return None, None  # Go back
            return hierarchy, sub_path
    
    return hierarchy, None


def _show_service_type_delete_menu(multi_ctx) -> Optional[str]:
    """Show menu of detected service types from current config."""
    import re
    
    # Get config from first device
    config_text = ""
    if multi_ctx and multi_ctx.devices:
        dev = multi_ctx.devices[0]
        from ..utils import get_device_config_dir
        config_path = get_device_config_dir(dev.hostname) / "running.txt"
        if config_path.exists():
            config_text = config_path.read_text()
    
    if not config_text:
        console.print("[yellow]No config available to detect services[/yellow]")
        return None
    
    # Detect configured service types with their attached interfaces
    service_types = []
    service_interfaces = {}  # Map service type -> list of attached interfaces
    
    # EVPN-VPWS (direct P2P services)
    vpws_count = len(re.findall(r'vpws-service-id', config_text))
    if vpws_count > 0 or 'evpn-vpws' in config_text:
        evpn_vpws_instances = len(re.findall(r'evpn-vpws\s*\n\s+instance\s+', config_text))
        # Find interfaces: attached (referenced) vs defined (in interfaces hierarchy)
        vpws_attached, vpws_defined = _extract_service_interfaces(config_text, 'evpn-vpws')
        service_interfaces['evpn-vpws'] = vpws_defined  # Only store deletable interfaces
        if vpws_defined:
            iface_info = f", {len(vpws_defined)} deletable interfaces"
        elif vpws_attached:
            iface_info = f", {len(vpws_attached)} attached (auto-deleted with service)"
        else:
            iface_info = ""
        service_types.append(('evpn-vpws', f'EVPN-VPWS ({vpws_count} vpws-service-ids, {evpn_vpws_instances} instances{iface_info})'))
    
    # EVPN-VPWS-FXC (Flexible Cross-Connect) - usually has PWHE interfaces which ARE defined
    fxc_count = len(re.findall(r'evpn-vpws-fxc\s*\n\s+instance\s+', config_text))
    if fxc_count > 0:
        fxc_attached, fxc_defined = _extract_service_interfaces(config_text, 'evpn-vpws-fxc')
        service_interfaces['evpn-vpws-fxc'] = fxc_defined
        if fxc_defined:
            iface_info = f", {len(fxc_defined)} deletable interfaces"
        elif fxc_attached:
            iface_info = f", {len(fxc_attached)} attached (auto-deleted with service)"
        else:
            iface_info = ""
        service_types.append(('evpn-vpws-fxc', f'EVPN-VPWS-FXC ({fxc_count} instances{iface_info})'))
    
    # EVPN-VPLS
    evpn_vpls_count = len(re.findall(r'evpn-vpls\s*\n\s+instance\s+', config_text))
    if evpn_vpls_count > 0:
        vpls_attached, vpls_defined = _extract_service_interfaces(config_text, 'evpn-vpls')
        service_interfaces['evpn-vpls'] = vpls_defined
        if vpls_defined:
            iface_info = f", {len(vpls_defined)} deletable interfaces"
        elif vpls_attached:
            iface_info = f", {len(vpls_attached)} attached (auto-deleted with service)"
        else:
            iface_info = ""
        service_types.append(('evpn-vpls', f'EVPN-VPLS ({evpn_vpls_count} instances{iface_info})'))
    
    # VRF
    vrf_count = len(re.findall(r'^\s{2}vrf\s+\S+', config_text, re.MULTILINE))
    if vrf_count > 0:
        service_types.append(('vrf', f'VRF ({vrf_count} instances)'))
        service_interfaces['vrf'] = []  # VRF doesn't have L2 interface attachments
    
    if not service_types:
        console.print("[yellow]No service types detected in current config[/yellow]")
        return None
    
    # Show menu
    console.print("\n[bold cyan]Detected Service Types:[/bold cyan]")
    for i, (svc_key, svc_display) in enumerate(service_types, 1):
        console.print(f"  [{i}] {svc_display}")
    console.print("  [B] Back")
    
    valid_choices = [str(i) for i in range(1, len(service_types) + 1)] + ['b', 'B']
    choice = Prompt.ask("Select service type to delete", choices=valid_choices, default="b")
    
    if choice.lower() == 'b':
        return None
    
    selected_type = service_types[int(choice) - 1][0]
    defined_ifaces = service_interfaces.get(selected_type, [])  # Interfaces that exist in interfaces hierarchy
    
    # Show deletion options
    console.print(f"\n[bold cyan]Delete Options for {selected_type}:[/bold cyan]")
    
    if defined_ifaces:
        # Interfaces are defined separately - offer to delete them too
        console.print(f"  [1] Delete services ONLY (keep {len(defined_ifaces):,} interfaces)")
        console.print(f"  [2] Delete services + {len(defined_ifaces):,} interfaces [bold yellow](RECOMMENDED)[/bold yellow]")
        sample = defined_ifaces[:5]
        console.print(f"      [dim]Interfaces: {', '.join(sample)}{'...' if len(defined_ifaces) > 5 else ''}[/dim]")
    else:
        # Interfaces are only attachments inside service - auto-deleted
        console.print(f"  [1] Delete services (attached interfaces auto-removed)")
        console.print(f"      [dim]Note: Interface attachments are inside the service config[/dim]")
        console.print(f"      [dim]      Deleting the service removes the attachments automatically[/dim]")
    console.print(f"  [B] Back")
    
    if defined_ifaces:
        del_choice = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="2")
    else:
        del_choice = Prompt.ask("Select", choices=["1", "b", "B"], default="1")
    
    if del_choice.lower() == 'b':
        return None
    
    delete_interfaces = (del_choice == "2" and defined_ifaces)
    
    # Confirm deletion
    if delete_interfaces:
        if Confirm.ask(f"\n[bold red]Delete ALL {selected_type} services AND {len(defined_ifaces):,} interfaces?[/bold red]", default=False):
            # Store interfaces for deletion in multi_ctx
            if multi_ctx:
                multi_ctx._pending_interface_deletes = defined_ifaces
            return f"{selected_type}+interfaces"
    else:
        if Confirm.ask(f"\n[bold red]Delete ALL {selected_type} services?[/bold red]", default=False):
            return selected_type
    
    return None


def _extract_service_interfaces(config_text: str, service_type: str) -> tuple:
    """Extract interfaces attached to a service type from config.
    
    Args:
        config_text: Full running config text
        service_type: Service type (evpn-vpws, evpn-vpws-fxc, evpn-vpls)
    
    Returns:
        Tuple of (attached_interfaces, defined_interfaces)
        - attached_interfaces: All interfaces referenced in the service
        - defined_interfaces: Only interfaces that are also defined under 'interfaces' hierarchy
    """
    import re
    attached = set()
    
    # Find the service block and extract attached interfaces
    in_service_block = False
    in_instance = False
    
    for line in config_text.split('\n'):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        
        # Check if entering service block (2-space indent under network-services)
        if indent == 2 and stripped.startswith(service_type):
            in_service_block = True
            continue
        
        # Check if leaving service block
        if in_service_block and indent <= 2 and stripped and not stripped.startswith('!'):
            if not stripped.startswith(service_type):
                in_service_block = False
                in_instance = False
                continue
        
        if in_service_block:
            # Check for instance (4-space indent)
            if indent == 4 and stripped.startswith('instance '):
                in_instance = True
                continue
            
            # Check for interface inside instance (6-space indent)
            if in_instance and indent == 6 and stripped.startswith('interface '):
                match = re.match(r'interface\s+(\S+)', stripped)
                if match:
                    attached.add(match.group(1))
    
    # Now find which interfaces are DEFINED under 'interfaces' hierarchy
    # DNOS format: 2-space indent, NO "interface" keyword
    #   interfaces
    #     ge400-0/0/4.1    <- 2-space indent, just the name
    #       admin-state enabled
    #     !
    defined = set()
    in_interfaces = False
    
    for line in config_text.split('\n'):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        
        # Enter interfaces block
        if stripped == 'interfaces':
            in_interfaces = True
            continue
        
        # Exit interfaces block (any non-indented line except !)
        if in_interfaces and indent == 0 and stripped and stripped != '!':
            in_interfaces = False
            continue
        
        # Find interface definitions at 2-space indent (direct children of interfaces block)
        # Format: "  ge400-0/0/4.1" or "  pwhe-1.500" - no "interface" keyword
        if in_interfaces and indent == 2 and stripped and not stripped.startswith('!'):
            # The stripped line IS the interface name
            iface_name = stripped
            if iface_name in attached:
                defined.add(iface_name)
    
    return sorted(attached), sorted(defined)


def _show_granular_delete_menu(multi_ctx) -> Tuple[Optional[str], Optional[str]]:
    """Show menu for granular deletion options."""
    console.print("\n[bold cyan]Granular Deletion Options[/bold cyan]")
    console.print()
    console.print("[bold]Services:[/bold]")
    console.print("  [1] Delete specific FXC instance (evpn-vpws-fxc)")
    console.print("  [2] Delete ALL FXC services (no evpn-vpws-fxc)")
    console.print("  [3] Delete specific EVPN-VPWS instance")
    console.print("  [4] Delete ALL EVPN-VPWS services (no evpn-vpws)")
    console.print()
    console.print("[bold]Other:[/bold]")
    console.print("  [5] Delete specific BGP neighbor")
    console.print("  [6] Delete interface from multihoming")
    console.print("  [7] Delete range of interfaces")
    console.print("  [B] Back")
    
    choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "5", "6", "7", "b", "B"], default="b")
    
    if choice.lower() == 'b':
        return None, None
    
    if choice == "1":
        instance_name = Prompt.ask("FXC instance name (or 'b' to go back)", default="")
        if instance_name.lower() in ('b', 'back', ''):
            return None, None
        return 'services', f"evpn-vpws-fxc instance {instance_name}"
    
    elif choice == "2":
        # Delete ALL FXC services
        if Confirm.ask("Delete ALL evpn-vpws-fxc services?", default=False):
            return 'services', "evpn-vpws-fxc"
        return None, None
    
    elif choice == "3":
        instance_name = Prompt.ask("EVPN-VPWS instance name (or 'b' to go back)", default="")
        if instance_name.lower() in ('b', 'back', ''):
            return None, None
        return 'services', f"evpn-vpws instance {instance_name}"
    
    elif choice == "4":
        # Delete ALL EVPN-VPWS services
        if Confirm.ask("Delete ALL evpn-vpws services?", default=False):
            return 'services', "evpn-vpws"
        return None, None
    
    elif choice == "5":
        neighbor_ip = Prompt.ask("BGP neighbor IP (or 'b' to go back)", default="")
        if neighbor_ip.lower() in ('b', 'back', ''):
            return None, None
        return 'bgp', f"neighbor {neighbor_ip}"
    
    elif choice == "6":
        interface = Prompt.ask("Interface to remove from MH (or 'b' to go back)", default="")
        if interface.lower() in ('b', 'back', ''):
            return None, None
        return 'multihoming', f"interface {interface}"
    
    elif choice == "7":
        # Interface range deletion
        prefix = Prompt.ask("Interface prefix (or 'b' to go back)", default="ph")
        if prefix.lower() in ('b', 'back'):
            return None, None
        start = Prompt.ask("Start number (or 'b' to go back)", default="1")
        if start.lower() in ('b', 'back'):
            return None, None
        end = Prompt.ask("End number (or 'b' to go back)", default="100")
        if end.lower() in ('b', 'back'):
            return None, None
        return 'interfaces', f"{prefix}{start}-{end}"
    
    return None, None


def execute_delete_hierarchy_multi(
    multi_ctx,
    hierarchy: str,
    sub_path: Optional[str] = None
) -> bool:
    """
    Execute multi-device delete with confirmations and dry-run.
    
    Args:
        multi_ctx: MultiDeviceContext
        hierarchy: Hierarchy to delete
        sub_path: Optional sub-path for granular deletion
    
    Returns:
        True if all deletions successful
    """
    device_names = ", ".join([d.hostname for d in multi_ctx.devices])
    display_name = HIERARCHY_DISPLAY_NAMES.get(hierarchy, hierarchy)
    
    # Confirmation
    console.print(f"\n[bold red]{'═' * 60}[/bold red]")
    console.print(f"[bold red]MULTI-DEVICE DELETE: {display_name}[/bold red]")
    console.print(f"[bold red]{'═' * 60}[/bold red]")
    console.print(f"\nDevices: [cyan]{device_names}[/cyan]")
    
    if sub_path:
        console.print(f"Sub-path: [yellow]{sub_path}[/yellow]")
    
    if hierarchy in CRITICAL_HIERARCHIES:
        console.print(f"\n[bold red]⚠ This is a CRITICAL hierarchy![/bold red]")
        console.print("[yellow]Type 'DELETE ALL' to confirm deletion from all devices:[/yellow]")
        confirm = Prompt.ask("Confirm")
        if confirm != "DELETE ALL":
            console.print("[dim]Delete cancelled.[/dim]")
            return False
    else:
        if not Confirm.ask(f"\nDelete {display_name} from all {len(multi_ctx.devices)} devices?", default=True):
            console.print("[dim]Delete cancelled.[/dim]")
            return False
    
    # Step 1: Dry run on all devices (send commands + commit check, no commit)
    console.print("\n[bold cyan]Step 1: Running commit check on all devices...[/bold cyan]")
    dry_results = delete_hierarchy_multi(multi_ctx, hierarchy, sub_path, dry_run=True)
    
    # Check if all succeeded
    all_success = all(s for s, _ in dry_results.values())
    
    if not all_success:
        console.print("\n[bold red]✗ Some devices failed commit check. Aborting.[/bold red]")
        return False
    
    # Step 2: Auto-commit on success (no extra confirmation needed - user already confirmed the delete)
    console.print("\n[bold green]✓ Commit check passed on all devices![/bold green]")
    console.print("\n[bold cyan]Step 2: Committing changes on all devices...[/bold cyan]")
    commit_results = delete_hierarchy_multi(multi_ctx, hierarchy, sub_path, dry_run=False)
    
    # Final summary
    all_success = all(s for s, _ in commit_results.values())
    
    if all_success:
        console.print(f"\n[bold green]✓ {display_name} deleted from all devices successfully![/bold green]")
        # Clean up the interface list now that commit succeeded
        if hasattr(multi_ctx, '_pending_interface_deletes'):
            del multi_ctx._pending_interface_deletes
    
    return all_success
