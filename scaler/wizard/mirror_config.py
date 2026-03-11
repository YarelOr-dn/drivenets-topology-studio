"""
Mirror Configuration Module for SCALER Wizard.

This module enables copying configuration from a source PE device to a target device
while preserving device-unique attributes:
- Router ID, Loopback IP
- Route Distinguishers (transformed to use target's loopback)
- WAN interfaces, Bundles, LACP
- LLDP configuration
- System configuration

Mirrored sections (from source):
- Network Services (FXC, EVPN, VRF)
- Routing Policies
- ACLs
- QoS Policies
- Multihoming (ESIs copied for dual-homing)
"""

import os
import re
from typing import Any, Dict, List, Optional, Tuple, Set
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich import box
from .core import BackException, TopException, int_prompt_nav, str_prompt_nav

from .parsers import (
    get_lo0_ip_from_config,
    get_as_number_from_config,
    get_router_id_from_config,
    get_mpls_enabled_interfaces,
    extract_hierarchy_section,
    parse_existing_multihoming,
    parse_existing_evpn_services,
    # New parsers for granular mirroring
    parse_vrf_instances,
    parse_evpn_vpws_instances,
    parse_l2vpn_xconnect,
    parse_l2vpn_bridge_domains,
    detect_device_type,
    get_cluster_specific_interfaces,
    get_ncp_slots,
    get_wan_interfaces,
    get_service_interfaces,
    parse_isis_config,
    parse_ldp_config,
)

console = Console()


# =============================================================================
# STEP-BY-STEP MIRROR FLOW - State Tracking and Step Handlers
# =============================================================================

from dataclasses import dataclass, field
from enum import Enum


class StepAction(Enum):
    """Action taken for a mirror step."""
    INCLUDE = "include"      # Include section as-is (with transformations)
    SKIP = "skip"            # Skip section (keep target's existing)
    SELECT = "select"        # User selected specific items
    CREATE = "create"        # Create new (not from source)
    BACK = "back"            # Go back to previous step


@dataclass
class SectionResult:
    """Result of processing a single section step."""
    action: StepAction
    items_count: int = 0
    items_selected: List[str] = field(default_factory=list)
    transformations: Dict[str, str] = field(default_factory=dict)
    config_snippet: str = ""
    summary: str = ""


@dataclass
class MirrorStepState:
    """
    Tracks state across all mirror steps.
    
    Each section stores its SectionResult after user completes that step.
    Transformations (like hostname, loopback IP) are shared across sections.
    """
    source_hostname: str
    target_hostname: str
    source_config: str
    target_config: str
    
    # Global transformations (detected or user-provided)
    global_transforms: Dict[str, str] = field(default_factory=dict)
    
    # Results for each section
    system: Optional[SectionResult] = None
    interfaces_wan: Optional[SectionResult] = None
    interfaces_service: Optional[SectionResult] = None
    interfaces_loopback: Optional[SectionResult] = None
    fxc_services: Optional[SectionResult] = None
    vpls_services: Optional[SectionResult] = None
    vrf_instances: Optional[SectionResult] = None
    multihoming: Optional[SectionResult] = None
    protocols: Optional[SectionResult] = None
    qos: Optional[SectionResult] = None
    
    # Step tracking
    current_step: int = 0
    total_steps: int = 11  # 10 sections + final review
    
    # Section order (matching SCALER wizard order)
    SECTION_ORDER: List[str] = field(default_factory=lambda: [
        'system',
        'interfaces_wan',
        'interfaces_service',
        'interfaces_loopback',
        'fxc_services',
        'vpls_services',
        'vrf_instances',
        'multihoming',
        'protocols',
        'qos'
    ])
    
    SECTION_DISPLAY_NAMES: Dict[str, str] = field(default_factory=lambda: {
        'system': 'System',
        'interfaces_wan': 'Interfaces - WAN',
        'interfaces_service': 'Interfaces - Service (PWHE/L2-AC)',
        'interfaces_loopback': 'Interfaces - Loopback',
        'fxc_services': 'FXC Services (EVPN-VPWS)',
        'vpls_services': 'VPLS Services (EVPN-VPLS)',
        'vrf_instances': 'VRF Instances',
        'multihoming': 'Multihoming (ESI/DF)',
        'protocols': 'Protocols (ISIS/LDP/BGP)',
        'qos': 'QoS Policies'
    })
    
    def get_section_result(self, section_name: str) -> Optional[SectionResult]:
        """Get result for a section by name."""
        return getattr(self, section_name, None)
    
    def set_section_result(self, section_name: str, result: SectionResult):
        """Set result for a section by name."""
        setattr(self, section_name, result)
    
    def get_included_sections(self) -> List[str]:
        """Get list of sections that are included (not skipped)."""
        included = []
        for section in self.SECTION_ORDER:
            result = self.get_section_result(section)
            if result and result.action in (StepAction.INCLUDE, StepAction.SELECT, StepAction.CREATE):
                included.append(section)
        return included
    
    def get_summary_table_data(self) -> List[Tuple[str, str, str]]:
        """Get data for final review summary table: (section_name, action, items)."""
        data = []
        for section in self.SECTION_ORDER:
            result = self.get_section_result(section)
            display_name = self.SECTION_DISPLAY_NAMES.get(section, section)
            if result:
                action_str = result.action.value.capitalize()
                items_str = result.summary or f"{result.items_count} items"
            else:
                action_str = "Pending"
                items_str = "-"
            data.append((display_name, action_str, items_str))
        return data
    
    def detect_global_transformations(self):
        """
        Auto-detect required transformations between source and target.
        
        Detects:
        - Hostname: source -> target
        - Loopback IP: source lo0 -> target lo0
        - Router ID: source -> target
        - ASN: usually same, but detect if different
        """
        # Hostname transformation
        self.global_transforms['hostname'] = {
            'source': self.source_hostname,
            'target': self.target_hostname
        }
        
        # Loopback IP transformation
        src_lo0 = get_lo0_ip_from_config(self.source_config)
        tgt_lo0 = get_lo0_ip_from_config(self.target_config)
        if src_lo0 and tgt_lo0:
            self.global_transforms['loopback_ip'] = {
                'source': src_lo0.split('/')[0] if '/' in src_lo0 else src_lo0,
                'target': tgt_lo0.split('/')[0] if '/' in tgt_lo0 else tgt_lo0
            }
        elif src_lo0:
            # Target doesn't have lo0 - will need user input
            self.global_transforms['loopback_ip'] = {
                'source': src_lo0.split('/')[0] if '/' in src_lo0 else src_lo0,
                'target': None  # Needs user input
            }
        
        # Router ID transformation
        src_rid = get_router_id_from_config(self.source_config)
        tgt_rid = get_router_id_from_config(self.target_config)
        if src_rid:
            self.global_transforms['router_id'] = {
                'source': src_rid,
                'target': tgt_rid or tgt_lo0  # Default to lo0 if no explicit router-id
            }
        
        # ASN (usually same across PEs in same network)
        src_asn = get_as_number_from_config(self.source_config)
        tgt_asn = get_as_number_from_config(self.target_config)
        if src_asn:
            self.global_transforms['asn'] = {
                'source': src_asn,
                'target': tgt_asn or src_asn  # Keep same if not configured on target
            }


# =============================================================================
# STEP HANDLER FUNCTIONS
# =============================================================================

def show_step_header(
    step_num: int,
    total_steps: int,
    section_name: str,
    source_hostname: str,
    target_hostname: str
):
    """Display the step header panel."""
    console.print(Panel(
        f"[bold white]Step {step_num}/{total_steps}: {section_name.upper()}[/bold white]\n"
        f"[dim]Source: {source_hostname} -> Target: {target_hostname}[/dim]",
        border_style="cyan"
    ))


def show_step_menu(
    items_summary: str,
    transformations: List[Tuple[str, str, str]],  # (name, source_val, target_val)
    has_items: bool = True,
    allow_create: bool = True
) -> str:
    """
    Display standard step menu and get user choice.
    
    Args:
        items_summary: Summary of items found (e.g., "100 PWHE interfaces")
        transformations: List of (name, source_val, suggested_target_val) tuples
        has_items: Whether source has items in this section
        allow_create: Whether to show [C] Create new option
        
    Returns:
        User choice: '1' (include), '2' (select), '3' (skip), 'c' (create), 'b' (back)
    """
    console.print()
    
    if has_items:
        console.print(f"[bold]Found on source:[/bold]")
        console.print(f"  {items_summary}")
        
        if transformations:
            console.print(f"\n[bold]Value Transformations (auto-detected):[/bold]")
            for name, src_val, tgt_val in transformations:
                if tgt_val:
                    console.print(f"  {name}: [yellow]{src_val}[/yellow] -> [green]{tgt_val}[/green]")
                else:
                    console.print(f"  {name}: [yellow]{src_val}[/yellow] -> [red]? (will prompt)[/red]")
        
        console.print(f"\n[bold]Actions:[/bold]")
        console.print(f"  [1] Include all (apply transformations)")
        console.print(f"  [2] Select which items to include")
        console.print(f"  [3] Skip this section (keep target's existing)")
        if allow_create:
            console.print(f"  [C] Create new (not from source)")
        console.print(f"  [B] Back to previous step")
        
        choices = ['1', '2', '3', 'b', 'B']
        if allow_create:
            choices.extend(['c', 'C'])
        
        choice = Prompt.ask("Select", choices=choices, default='1').lower()
    else:
        console.print(f"[yellow]No items found on source device.[/yellow]")
        console.print(f"\n[bold]Actions:[/bold]")
        console.print(f"  [3] Skip this section (keep target's existing)")
        if allow_create:
            console.print(f"  [C] Create new configuration")
        console.print(f"  [B] Back to previous step")
        
        choices = ['3', 'b', 'B']
        if allow_create:
            choices.extend(['c', 'C'])
        
        choice = Prompt.ask("Select", choices=choices, default='3').lower()
    
    return choice


def prompt_transformation_value(
    name: str,
    source_val: str,
    suggested_val: Optional[str] = None
) -> str:
    """
    Prompt user for a transformation value with smart suggestion.
    
    Args:
        name: Name of the value (e.g., "Loopback IP")
        source_val: Value from source device
        suggested_val: Auto-detected suggestion for target
        
    Returns:
        User-confirmed or entered value
    """
    console.print(f"\n[bold]{name}[/bold]")
    console.print(f"  Source value: [yellow]{source_val}[/yellow]")
    
    if suggested_val:
        console.print(f"  Suggested for target: [green]{suggested_val}[/green]")
        value = Prompt.ask(
            f"  Enter target value",
            default=suggested_val
        )
    else:
        value = Prompt.ask(
            f"  Enter target value",
            default=""
        )
        if not value:
            console.print(f"  [red]Value is required.[/red]")
            return prompt_transformation_value(name, source_val, suggested_val)
    
    return value


def select_items_from_list(
    items: List[str],
    item_type: str,
    max_display: int = 20
) -> List[str]:
    """
    Let user select specific items from a list.
    
    Args:
        items: List of item names
        item_type: Type name for display (e.g., "interfaces")
        max_display: Max items to show before summarizing
        
    Returns:
        List of selected item names
    """
    console.print(f"\n[bold]Select {item_type} to include:[/bold]")
    
    if len(items) <= max_display:
        # Show all items with checkboxes
        for i, item in enumerate(items, 1):
            console.print(f"  [{i}] {item}")
    else:
        # Show summary with ranges
        console.print(f"  [dim]{len(items)} items total[/dim]")
        console.print(f"  First: {items[0]}")
        console.print(f"  Last: {items[-1]}")
    
    console.print(f"\n  [A] All items")
    console.print(f"  [N] None (skip)")
    console.print(f"  [R] Enter range (e.g., 1-50)")
    console.print(f"  [B] Back")
    
    choice = Prompt.ask("Select", default="a").lower()
    
    if choice == 'a':
        return items
    elif choice == 'n':
        return []
    elif choice == 'b':
        raise BackException()
    elif choice == 'r':
        range_str = Prompt.ask("Enter range (e.g., 1-50, 1-25,50-75)")
        # Parse range
        selected = []
        for part in range_str.split(','):
            if '-' in part:
                start, end = part.split('-')
                try:
                    start_idx = int(start.strip()) - 1
                    end_idx = int(end.strip())
                    selected.extend(items[start_idx:end_idx])
                except (ValueError, IndexError):
                    console.print(f"[red]Invalid range: {part}[/red]")
            else:
                try:
                    idx = int(part.strip()) - 1
                    if 0 <= idx < len(items):
                        selected.append(items[idx])
                except (ValueError, IndexError):
                    pass
        return selected
    else:
        # Try to parse as item number
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                return [items[idx]]
        except ValueError:
            pass
        return items  # Default to all


# =============================================================================
# WAN INTERFACE MAPPING WIZARD (with LLDP)
# =============================================================================

def wan_interface_mapping_wizard(
    state: MirrorStepState,
    source_wan_interfaces: List[str]
) -> Optional[SectionResult]:
    """
    Interactive wizard for mapping WAN interfaces from source to target.
    
    Uses LLDP neighbors from target device to show available interfaces
    and suggest IP mappings.
    
    Args:
        state: Current mirror state with configs
        source_wan_interfaces: List of WAN interface names from source
        
    Returns:
        SectionResult with mapped interfaces, or None if cancelled
    """
    import json
    from pathlib import Path
    
    console.print(Panel(
        "[bold cyan]WAN Interface Mapping Wizard[/bold cyan]\n"
        f"[dim]Map WAN interfaces from {state.source_hostname} to {state.target_hostname}[/dim]",
        border_style="cyan"
    ))
    
    # Load target's LLDP neighbors from operational.json
    target_lldp = []
    target_op_data = {}
    try:
        target_op_file = Path(f"/home/dn/SCALER/db/configs/{state.target_hostname}/operational.json")
        if target_op_file.exists():
            with open(target_op_file) as f:
                target_op_data = json.load(f)
                target_lldp = target_op_data.get('lldp_neighbors', [])
    except Exception:
        pass
    
    # Get target's available interfaces (from config + LLDP)
    target_wan_interfaces = get_wan_interfaces(state.target_config)
    
    # Parse source WAN interface IPs from config
    source_wan_ips = {}
    for wan in source_wan_interfaces:
        # Extract IP from source config
        ip_match = re.search(
            rf'^\s+{re.escape(wan)}\s*\n(?:.*?\n)*?\s+ipv4-address\s+(\d+\.\d+\.\d+\.\d+(?:/\d+)?)',
            state.source_config, re.MULTILINE
        )
        if ip_match:
            source_wan_ips[wan] = ip_match.group(1)
    
    # Show source WANs with their IPs
    console.print("\n[bold]Source WAN Interfaces:[/bold]")
    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Interface", style="cyan")
    table.add_column("IP Address", style="green")
    
    for i, wan in enumerate(source_wan_interfaces, 1):
        ip = source_wan_ips.get(wan, "[dim]no IP[/dim]")
        table.add_row(str(i), wan, ip)
    console.print(table)
    
    # Show target's available interfaces with LLDP info
    console.print("\n[bold]Target Available Interfaces (with LLDP neighbors):[/bold]")
    if target_lldp:
        lldp_table = Table(box=box.SIMPLE, show_header=True)
        lldp_table.add_column("Interface", style="cyan")
        lldp_table.add_column("Neighbor", style="yellow")
        lldp_table.add_column("Remote Port")
        
        for n in target_lldp[:15]:  # Show first 15
            lldp_table.add_row(
                n.get('local_interface') or n.get('interface', '?'),
                n.get('neighbor_device') or n.get('neighbor', '?'),
                n.get('neighbor_port') or n.get('remote_port', '?')
            )
        console.print(lldp_table)
        
        if len(target_lldp) > 15:
            console.print(f"[dim]... and {len(target_lldp) - 15} more[/dim]")
    else:
        console.print("[yellow]No LLDP neighbors found on target device.[/yellow]")
        console.print("[dim]Tip: Enable LLDP on target device to see neighbors.[/dim]")
    
    # Mapping options - context-aware based on target WANs
    console.print("\n[bold]WAN Mapping Options:[/bold]")
    
    has_target_wans = len(target_wan_interfaces) > 0
    valid_choices = []
    default_choice = "2"  # Default to mapping if no target WANs
    
    if has_target_wans:
        console.print(f"  [1] Keep target's existing WAN configuration ({len(target_wan_interfaces)} WANs) [Recommended]")
        valid_choices.append("1")
        default_choice = "1"
    else:
        console.print(f"  [dim][1] Keep target's existing WAN configuration (target has no WANs)[/dim]")
    
    console.print("  [2] Map source WANs to target interfaces (with IP suggestions)" + 
                  (" [Recommended]" if not has_target_wans else ""))
    valid_choices.append("2")
    
    console.print("  [3] Copy source WAN config as-is (may conflict with target interfaces)")
    valid_choices.append("3")
    
    console.print("  [B] Back")
    valid_choices.extend(["b", "B"])
    
    choice = Prompt.ask("Select option", choices=valid_choices, default=default_choice).lower()
    
    if choice == 'b':
        return None
    elif choice == '1' and has_target_wans:
        return SectionResult(
            action=StepAction.SKIP,
            summary=f"Keep target's {len(target_wan_interfaces)} WANs"
        )
    elif choice == '3':
        return SectionResult(
            action=StepAction.INCLUDE,
            items_count=len(source_wan_interfaces),
            items_selected=source_wan_interfaces,
            summary=f"Copy {len(source_wan_interfaces)} WANs as-is"
        )
    elif choice == '2':
        # Interactive mapping wizard
        mappings = {}
        ip_transformations = {}
        
        # Build list of available target interfaces from LLDP (physical interfaces only)
        available_targets = []
        for n in target_lldp:
            iface = n.get('local_interface') or n.get('interface', '')
            neighbor = n.get('neighbor_device') or n.get('neighbor', '')
            remote_port = n.get('neighbor_port') or n.get('remote_port', '')
            # Only include physical interfaces (no dot in name)
            if iface and '.' not in iface:
                available_targets.append({
                    'interface': iface,
                    'neighbor': neighbor,
                    'remote_port': remote_port
                })
        
        if not available_targets:
            console.print("\n[yellow]No physical interfaces available from LLDP.[/yellow]")
            console.print("[dim]Enable LLDP on target device or use option [3] to copy as-is.[/dim]")
            return None
        
        # Check if source WANs are sub-interfaces
        source_has_subifs = any('.' in wan for wan in source_wan_interfaces)
        
        if source_has_subifs:
            # Group source WANs by parent interface
            source_by_parent = {}
            for wan in source_wan_interfaces:
                if '.' in wan:
                    parent = wan.rsplit('.', 1)[0]
                    subif_id = wan.rsplit('.', 1)[1]
                else:
                    parent = wan
                    subif_id = None
                
                if parent not in source_by_parent:
                    source_by_parent[parent] = []
                source_by_parent[parent].append({
                    'full_name': wan,
                    'subif_id': subif_id,
                    'ip': source_wan_ips.get(wan, '')
                })
            
            console.print("\n[bold cyan]WAN Sub-Interface Mapping[/bold cyan]")
            console.print(f"[dim]Source has {len(source_wan_interfaces)} sub-interfaces on {len(source_by_parent)} parent(s)[/dim]\n")
            
            # For each source parent, ask which target parent to use
            for src_parent, subifs in source_by_parent.items():
                console.print(f"\n[bold]Source parent: [cyan]{src_parent}[/cyan][/bold]")
                console.print(f"  Sub-interfaces: {len(subifs)}")
                for sf in subifs[:5]:
                    console.print(f"    • {sf['full_name']} ({sf['ip'] or 'no IP'})")
                if len(subifs) > 5:
                    console.print(f"    [dim]... and {len(subifs) - 5} more[/dim]")
                
                # Show target physical interfaces
                console.print(f"\n  [bold]Select target parent interface:[/bold]")
                for idx, tgt in enumerate(available_targets, 1):
                    neighbor_info = f" → {tgt['neighbor']}" if tgt['neighbor'] else ""
                    if tgt['remote_port']:
                        neighbor_info += f":{tgt['remote_port']}"
                    console.print(f"    [{idx}] {tgt['interface']}{neighbor_info}")
                console.print(f"    [S] Skip all sub-interfaces on this parent")
                console.print(f"    [B] Back")
                
                valid_choices = [str(i) for i in range(1, len(available_targets) + 1)] + ['s', 'S', 'b', 'B']
                selection = Prompt.ask("  Select", choices=valid_choices, default='1').lower()
                
                if selection == 'b':
                    return None
                elif selection == 's':
                    console.print(f"  [dim]→ Skipping all sub-interfaces on {src_parent}[/dim]")
                    continue
                else:
                    try:
                        selected_idx = int(selection) - 1
                        target_parent = available_targets[selected_idx]['interface']
                        
                        console.print(f"\n  [green]✓ Will create sub-interfaces on {target_parent}:[/green]")
                        
                        # Map each sub-interface
                        for sf in subifs:
                            if sf['subif_id']:
                                target_subif = f"{target_parent}.{sf['subif_id']}"
                            else:
                                target_subif = target_parent
                            
                            mappings[sf['full_name']] = target_subif
                            console.print(f"    {sf['full_name']} → {target_subif}")
                        
                        # Ask for IP transformation strategy
                        console.print(f"\n  [bold]IP Address Configuration:[/bold]")
                        console.print(f"    [1] Keep same IPs as source")
                        console.print(f"    [2] Increment last octet (+1 for each)")
                        console.print(f"    [3] Enter IPs manually for each")
                        
                        ip_choice = Prompt.ask("  Select", choices=['1', '2', '3'], default='1')
                        
                        if ip_choice == '1':
                            console.print(f"  [dim]→ Keeping source IPs[/dim]")
                        elif ip_choice == '2':
                            for sf in subifs:
                                if sf['ip']:
                                    new_ip = _suggest_target_ip(sf['ip'])
                                    ip_transformations[sf['ip']] = new_ip
                                    console.print(f"    {sf['ip']} → {new_ip}")
                        elif ip_choice == '3':
                            console.print(f"  [dim]Enter IP for each sub-interface:[/dim]")
                            for sf in subifs:
                                if sf['ip']:
                                    suggested = _suggest_target_ip(sf['ip'])
                                    new_ip = Prompt.ask(f"    {sf['full_name']} ({sf['ip']})", default=suggested)
                                    if new_ip and new_ip != sf['ip']:
                                        ip_transformations[sf['ip']] = new_ip
                    except (ValueError, IndexError):
                        console.print(f"  [red]Invalid selection[/red]")
                        continue
        else:
            # Source WANs are physical interfaces - do 1:1 mapping
            console.print("\n[bold cyan]Interface Mapping[/bold cyan]")
            console.print("[dim]Map each source WAN to a target interface[/dim]\n")
            
            used_targets = set()
            
            for i, src_wan in enumerate(source_wan_interfaces, 1):
                src_ip = source_wan_ips.get(src_wan, '')
                
                console.print(f"\n[bold]({i}/{len(source_wan_interfaces)}) Source: [cyan]{src_wan}[/cyan][/bold]", end="")
                if src_ip:
                    console.print(f" [green]({src_ip})[/green]")
                else:
                    console.print()
                
                # Show available targets
                console.print("  [dim]Available target interfaces:[/dim]")
                available_for_selection = []
                for idx, tgt in enumerate(available_targets, 1):
                    if tgt['interface'] in used_targets:
                        status = "[dim][used][/dim]"
                    else:
                        status = ""
                        available_for_selection.append((idx, tgt))
                    
                    neighbor_info = f" → {tgt['neighbor']}" if tgt['neighbor'] else ""
                    console.print(f"    [{idx}] {tgt['interface']}{neighbor_info} {status}")
                
                console.print(f"    [S] Skip")
                console.print(f"    [B] Back")
                
                valid_choices = [str(idx) for idx, _ in available_for_selection] + ['s', 'S', 'b', 'B']
                selection = Prompt.ask("  Select", choices=valid_choices, default='s').lower()
                
                if selection == 'b':
                    return None
                elif selection == 's':
                    continue
                else:
                    try:
                        selected_idx = int(selection) - 1
                        target_iface = available_targets[selected_idx]['interface']
                        used_targets.add(target_iface)
                        mappings[src_wan] = target_iface
                        
                        if src_ip:
                            suggested_ip = _suggest_target_ip(src_ip)
                            target_ip = Prompt.ask(f"  Target IP", default=suggested_ip)
                            if target_ip and target_ip != src_ip:
                                ip_transformations[src_ip] = target_ip
                    except (ValueError, IndexError):
                        continue
        
        if not mappings:
            console.print("\n[yellow]No interfaces mapped. Keeping target's existing.[/yellow]")
            return SectionResult(action=StepAction.SKIP, summary="No mappings created")
        
        # Show mapping summary
        console.print("\n[bold]Mapping Summary:[/bold]")
        summary_table = Table(box=box.SIMPLE, show_header=True)
        summary_table.add_column("Source Interface", style="cyan")
        summary_table.add_column("→", width=2)
        summary_table.add_column("Target Interface", style="green")
        summary_table.add_column("Source IP")
        summary_table.add_column("→", width=2)
        summary_table.add_column("Target IP", style="yellow")
        
        for src, tgt in mappings.items():
            src_ip = source_wan_ips.get(src, '-')
            tgt_ip = ip_transformations.get(src_ip, src_ip) if src_ip != '-' else '-'
            summary_table.add_row(src, "→", tgt, src_ip, "→", tgt_ip)
        
        console.print(summary_table)
        
        if Confirm.ask("\nApply these mappings?", default=True):
            return SectionResult(
                action=StepAction.SELECT,
                items_count=len(mappings),
                items_selected=list(mappings.keys()),
                transformations={**mappings, **ip_transformations},
                summary=f"{len(mappings)} WANs mapped"
            )
        else:
            return None
    
    return SectionResult(action=StepAction.SKIP, summary="Skipped")


def _normalize_loopback_ip(ip_input: str, warn: bool = True) -> str:
    """
    Normalize loopback IP - always use /32 for loopbacks.
    
    Loopback interfaces should ALWAYS use /32 (host route) because:
    - They represent a single router identity, not a network
    - /32 ensures proper route advertisement
    - Other prefixes can cause routing conflicts
    
    Examples:
        1.1.1.1 -> 1.1.1.1/32
        1.1.1.1/32 -> 1.1.1.1/32
        1.1.1.1/24 -> 1.1.1.1/32 (corrected with warning)
        1.1.1.1/29 -> 1.1.1.1/32 (corrected with warning)
    """
    if not ip_input:
        return ip_input
    
    ip_input = ip_input.strip()
    
    if '/' not in ip_input:
        # No mask specified, add /32 for loopback
        return f"{ip_input}/32"
    
    # Check if mask is not /32
    parts = ip_input.split('/')
    if len(parts) == 2:
        ip_addr = parts[0]
        mask = parts[1]
        
        if mask != '32':
            if warn:
                console.print(f"[yellow]⚠ Warning: Loopback interfaces should use /32, not /{mask}[/yellow]")
                console.print(f"[yellow]  Correcting: {ip_input} → {ip_addr}/32[/yellow]")
            return f"{ip_addr}/32"
    
    return ip_input


def _extract_hostname_from_config(config: str) -> Optional[str]:
    """
    Extract hostname from DNOS config.
    
    Looks for:
        system
          name HOSTNAME
    
    Returns:
        Hostname string or None if not found
    """
    if not config:
        return None
    
    # Match: system { ... name HOSTNAME ... }
    match = re.search(r'^\s*system\s*\n(?:.*\n)*?\s*name\s+(.+?)$', config, re.MULTILINE)
    if match:
        return match.group(1).strip()
    
    return None


def _suggest_target_ip(source_ip: str) -> str:
    """
    Suggest a target IP by incrementing the last octet.
    
    Example: 10.0.0.1/30 -> 10.0.0.2/30
    """
    # Handle CIDR notation
    if '/' in source_ip:
        ip_part, mask = source_ip.split('/')
    else:
        ip_part = source_ip
        mask = None
    
    parts = ip_part.split('.')
    if len(parts) == 4:
        try:
            last_octet = int(parts[3])
            # For /30 or /31, alternate between .1 and .2
            if mask and int(mask) >= 30:
                new_last = 2 if last_octet == 1 else 1
            else:
                new_last = last_octet + 1 if last_octet < 254 else last_octet - 1
            parts[3] = str(new_last)
            new_ip = '.'.join(parts)
            return f"{new_ip}/{mask}" if mask else new_ip
        except ValueError:
            pass
    
    return source_ip


# =============================================================================
# SERVICE INTERFACE MAPPING WIZARD (PWHE, L2-AC, Bundles)
# =============================================================================

def service_interface_mapping_wizard(
    state: 'MirrorStepState',
    interface_type: str,  # 'pwhe', 'l2ac', 'bundle'
    source_interfaces: List[Dict],
    analysis: Dict
) -> Optional[Dict]:
    """
    Interactive wizard for mapping service interfaces (PWHE/L2-AC/Bundle) to target.
    
    Shows available oper-up physical interfaces on target (from LLDP) and lets
    user select which parent interface to create sub-interfaces on.
    
    Args:
        state: MirrorStepState with source/target config
        interface_type: 'pwhe', 'l2ac', or 'bundle'
        source_interfaces: List of source interface info dicts
        analysis: Config analysis dict
        
    Returns:
        Dict with mapping info or None if cancelled
    """
    import json
    from pathlib import Path
    from rich.table import Table
    
    type_names = {
        'pwhe': 'PWHE (Pseudowire Headend)',
        'l2ac': 'L2-AC (Access Circuit)',
        'bundle': 'Bundle/LACP'
    }
    type_name = type_names.get(interface_type, interface_type.upper())
    
    console.print(Panel(
        f"[bold cyan]{type_name} Interface Mapping[/bold cyan]\n"
        f"[dim]Map {interface_type.upper()} interfaces from {state.source_hostname} to available interfaces on {state.target_hostname}[/dim]",
        border_style="cyan"
    ))
    
    # Load target's LLDP neighbors and operational data
    target_lldp = []
    target_physical_ifaces = []
    try:
        target_op_file = Path(f"/home/dn/SCALER/db/configs/{state.target_hostname}/operational.json")
        if target_op_file.exists():
            with open(target_op_file) as f:
                target_op_data = json.load(f)
                target_lldp = target_op_data.get('lldp_neighbors', [])
    except Exception:
        pass
    
    # Extract available physical interfaces from target config (oper-up preferred)
    # Look for ge*, eth*, xe*, ce*, fab-*, 400G interfaces
    target_iface_pattern = re.compile(r'^  (ge\d+-\d+/\d+/\d+|eth\d+-\d+/\d+/\d+|ce\d+-\d+/\d+/\d+|xe\d+-\d+/\d+/\d+|ge400-\d+/\d+/\d+)\s*$', re.MULTILINE)
    target_physical_ifaces = list(set(target_iface_pattern.findall(state.target_config)))
    target_physical_ifaces.sort()
    
    # Show available target interfaces with LLDP info
    console.print("\n[bold]Available Target Interfaces (LLDP neighbors = oper-up):[/bold]")
    
    if target_lldp:
        lldp_table = Table(box=box.SIMPLE, show_header=True)
        lldp_table.add_column("#", style="dim", width=3)
        lldp_table.add_column("Interface", style="cyan")
        lldp_table.add_column("Neighbor", style="yellow")
        lldp_table.add_column("Remote Port")
        lldp_table.add_column("Status", style="green")
        
        lldp_ifaces = []
        for i, n in enumerate(target_lldp[:20], 1):
            local_iface = n.get('local_interface') or n.get('interface', '?')
            lldp_ifaces.append(local_iface)
            lldp_table.add_row(
                str(i),
                local_iface,
                n.get('neighbor_device') or n.get('neighbor', '?'),
                n.get('neighbor_port') or n.get('remote_port', '?'),
                "[green]oper-up[/green]"
            )
        console.print(lldp_table)
        
        if len(target_lldp) > 20:
            console.print(f"[dim]... and {len(target_lldp) - 20} more neighbors[/dim]")
    else:
        console.print("[yellow]⚠ No LLDP neighbors found on target device.[/yellow]")
        console.print("[dim]Tip: Enable LLDP on target to see oper-up neighbors.[/dim]")
        if target_physical_ifaces:
            console.print(f"\n[dim]Physical interfaces in config: {', '.join(target_physical_ifaces[:10])}[/dim]")
    
    # Show source interface summary
    console.print(f"\n[bold]Source {type_name} Summary:[/bold]")
    
    if interface_type == 'pwhe':
        # Group PWHE by parent interface (ph*)
        parent_groups = {}
        for iface in source_interfaces:
            name = iface.get('name', iface) if isinstance(iface, dict) else str(iface)
            if '.' in name:
                parent = name.split('.')[0]
            else:
                parent = name
            parent_groups.setdefault(parent, []).append(name)
        
        console.print(f"  [cyan]{len(parent_groups)} parent interfaces[/cyan] with {sum(len(v) for v in parent_groups.values())} total sub-interfaces")
        for parent, subs in list(parent_groups.items())[:5]:
            console.print(f"    {parent}: {len(subs)} sub-interfaces")
        if len(parent_groups) > 5:
            console.print(f"    [dim]... and {len(parent_groups) - 5} more parents[/dim]")
            
    elif interface_type == 'l2ac':
        # Group by parent physical interface
        parent_groups = {}
        for iface in source_interfaces:
            name = iface.get('name', iface) if isinstance(iface, dict) else str(iface)
            if '.' in name:
                parent = name.split('.')[0]
            else:
                parent = name
            parent_groups.setdefault(parent, []).append(name)
        
        console.print(f"  [cyan]{len(parent_groups)} parent interfaces[/cyan] with {sum(len(v) for v in parent_groups.values())} sub-interfaces")
        for parent, subs in list(parent_groups.items())[:5]:
            console.print(f"    {parent}: {len(subs)} sub-interfaces")
            
    elif interface_type == 'bundle':
        console.print(f"  [cyan]{len(source_interfaces)} bundle interfaces[/cyan]")
        for iface in source_interfaces[:5]:
            name = iface.get('name', iface) if isinstance(iface, dict) else str(iface)
            members = iface.get('members', []) if isinstance(iface, dict) else []
            console.print(f"    {name}: {len(members)} members" if members else f"    {name}")
    
    # Mapping options
    console.print(f"\n[bold]{type_name} Mapping Options:[/bold]")
    console.print("  [1] [green]Map to target interfaces[/green] - Select physical interface(s) for sub-interfaces")
    console.print("  [2] [cyan]Copy as-is[/cyan] - Use same interface names (may not exist on target)")
    console.print("  [3] [dim]Skip[/dim] - Don't include these interfaces")
    console.print("  [B] Back")
    
    choice = Prompt.ask("Select option", choices=["1", "2", "3", "b", "B"], default="1").lower()
    
    if choice == 'b':
        return None
    elif choice == '3':
        return {'action': 'skip', 'summary': f"Skipped {type_name}"}
    elif choice == '2':
        return {
            'action': 'copy',
            'interfaces': source_interfaces,
            'summary': f"Copy {len(source_interfaces)} {interface_type.upper()} as-is"
        }
    elif choice == '1':
        # Interactive mapping
        return _map_service_interfaces_interactive(
            state, interface_type, source_interfaces, target_lldp, target_physical_ifaces, parent_groups if interface_type in ('pwhe', 'l2ac') else None
        )
    
    return None


def _map_service_interfaces_interactive(
    state: 'MirrorStepState',
    interface_type: str,
    source_interfaces: List,
    target_lldp: List[Dict],
    target_physical_ifaces: List[str],
    parent_groups: Optional[Dict] = None
) -> Optional[Dict]:
    """
    Interactive mapping of source interface parents to target interfaces.
    """
    console.print("\n[bold cyan]━━━ Interface Mapping ━━━[/bold cyan]")
    
    if interface_type == 'bundle':
        # For bundles, need to select member interfaces
        return _map_bundle_members_interactive(state, source_interfaces, target_lldp, target_physical_ifaces)
    
    # For PWHE/L2-AC, map parent interfaces to target physical interfaces
    if not parent_groups:
        console.print("[yellow]No parent interfaces to map.[/yellow]")
        return {'action': 'skip', 'summary': "No interfaces"}
    
    console.print("[dim]For each source parent, select a target physical interface.[/dim]")
    console.print("[dim]Sub-interfaces will be created on the selected target parent.[/dim]\n")
    
    # Build list of available target interfaces (LLDP = oper-up)
    available_targets = []
    if target_lldp:
        for n in target_lldp:
            iface = n.get('local_interface') or n.get('interface', '')
            if iface and iface not in available_targets:
                available_targets.append(iface)
    
    # Add physical interfaces from config if not enough LLDP
    if len(available_targets) < 5:
        for iface in target_physical_ifaces:
            if iface not in available_targets:
                available_targets.append(iface)
    
    if not available_targets:
        console.print("[red]No target interfaces available for mapping.[/red]")
        console.print("[dim]Enable LLDP on target or ensure physical interfaces exist in config.[/dim]")
        return {'action': 'skip', 'summary': "No target interfaces"}
    
    # Show quick reference of available targets
    console.print("[bold]Available targets:[/bold]", end=" ")
    console.print(", ".join(available_targets[:10]) + ("..." if len(available_targets) > 10 else ""))
    console.print()
    
    mappings = {}
    for parent, sub_ifaces in parent_groups.items():
        console.print(f"\n[cyan]Source: {parent}[/cyan] ({len(sub_ifaces)} sub-interfaces)")
        
        # Suggest a target (first available)
        suggested = available_targets[0] if available_targets else ""
        
        target = Prompt.ask(
            f"  Target interface (or 's' to skip)",
            default=suggested
        )
        
        if target.lower() == 's' or not target:
            console.print(f"  [dim]Skipping {parent}[/dim]")
            continue
        
        mappings[parent] = {
            'target': target,
            'sub_interfaces': sub_ifaces
        }
        console.print(f"  [green]✓ {parent}.* -> {target}.*[/green]")
    
    if not mappings:
        console.print("\n[yellow]No interfaces mapped.[/yellow]")
        return {'action': 'skip', 'summary': "No mappings"}
    
    # Show summary
    console.print("\n[bold]Mapping Summary:[/bold]")
    total_subs = 0
    for src_parent, info in mappings.items():
        tgt = info['target']
        sub_count = len(info['sub_interfaces'])
        total_subs += sub_count
        console.print(f"  {src_parent} ({sub_count} subs) -> {tgt}")
    
    if Confirm.ask(f"\nCreate {total_subs} sub-interfaces on {len(mappings)} target parent(s)?", default=True):
        return {
            'action': 'map',
            'mappings': mappings,
            'total_count': total_subs,
            'summary': f"Mapped {total_subs} to {len(mappings)} parents"
        }
    
    return None


def _map_bundle_members_interactive(
    state: 'MirrorStepState',
    source_bundles: List,
    target_lldp: List[Dict],
    target_physical_ifaces: List[str]
) -> Optional[Dict]:
    """
    Interactive mapping of bundle members to target physical interfaces.
    """
    console.print("\n[bold cyan]━━━ Bundle Member Mapping ━━━[/bold cyan]")
    console.print("[dim]Select physical interfaces to use as bundle members on target.[/dim]\n")
    
    # Get available target interfaces
    available_targets = []
    if target_lldp:
        for n in target_lldp:
            iface = n.get('local_interface') or n.get('interface', '')
            if iface and iface not in available_targets:
                available_targets.append(iface)
    
    if not available_targets:
        for iface in target_physical_ifaces:
            if iface not in available_targets:
                available_targets.append(iface)
    
    if not available_targets:
        console.print("[red]No target interfaces available for bundle members.[/red]")
        return {'action': 'skip', 'summary': "No target interfaces"}
    
    console.print("[bold]Available interfaces for bundle members:[/bold]")
    for i, iface in enumerate(available_targets[:20], 1):
        console.print(f"  [{i}] {iface}")
    
    bundle_configs = {}
    for src_bundle in source_bundles:
        name = src_bundle.get('name', src_bundle) if isinstance(src_bundle, dict) else str(src_bundle)
        src_members = src_bundle.get('members', []) if isinstance(src_bundle, dict) else []
        
        console.print(f"\n[cyan]Bundle: {name}[/cyan]")
        console.print(f"  Source has {len(src_members)} members" + (f": {', '.join(src_members[:3])}" if src_members else ""))
        
        create = Confirm.ask(f"  Create {name} on target?", default=True)
        if not create:
            continue
        
        # Select member interfaces
        console.print("  Enter member interface numbers (comma-separated) or interface names:")
        member_input = Prompt.ask("  Members", default="")
        
        members = []
        if member_input:
            parts = [p.strip() for p in member_input.split(',')]
            for p in parts:
                if p.isdigit() and 1 <= int(p) <= len(available_targets):
                    members.append(available_targets[int(p) - 1])
                elif p in available_targets:
                    members.append(p)
                else:
                    console.print(f"  [yellow]Unknown: {p}[/yellow]")
        
        if members:
            bundle_configs[name] = {
                'members': members,
                'copy_config': True  # Copy LACP/bundle config from source
            }
            console.print(f"  [green]✓ {name} with {len(members)} members: {', '.join(members)}[/green]")
    
    if not bundle_configs:
        return {'action': 'skip', 'summary': "No bundles configured"}
    
    return {
        'action': 'map',
        'bundles': bundle_configs,
        'summary': f"{len(bundle_configs)} bundles configured"
    }


def _get_source_interfaces_for_mapping(mirror: 'ConfigMirror', iface_type: str, analysis: Dict) -> List:
    """
    Extract source interfaces of a specific type for mapping wizard.
    
    Args:
        mirror: ConfigMirror object with source config
        iface_type: 'pwhe', 'l2ac', or 'bundles'
        analysis: Config analysis dict
        
    Returns:
        List of interface info dicts
    """
    source_config = mirror.source_config
    interfaces = []
    
    if iface_type == 'pwhe':
        # Extract PWHE interfaces (ph*)
        pwhe_pattern = re.compile(r'^  (ph\d+(?:\.\d+)?)\s*$', re.MULTILINE)
        matches = pwhe_pattern.findall(source_config)
        for m in matches:
            interfaces.append({'name': m, 'type': 'pwhe'})
            
    elif iface_type == 'l2ac':
        # Extract L2-AC sub-interfaces with l2-service enabled
        # Look for interfaces with .\d+ that have l2-service
        l2ac_pattern = re.compile(
            r'^  ((?:ge|eth|xe|ce)\d+-\d+/\d+/\d+\.\d+)\s*\n(?:.*?\n)*?\s+l2-service\s+enabled',
            re.MULTILINE
        )
        matches = l2ac_pattern.findall(source_config)
        for m in matches:
            interfaces.append({'name': m, 'type': 'l2ac'})
            
    elif iface_type == 'bundles':
        # Extract bundle interfaces (be*)
        bundle_pattern = re.compile(r'^  (be\d+)\s*$', re.MULTILINE)
        matches = bundle_pattern.findall(source_config)
        
        for bundle_name in matches:
            # Try to find bundle members
            members = []
            # Look for member-links in bundle config
            member_pattern = re.compile(
                rf'^  {re.escape(bundle_name)}\s*\n(?:.*?\n)*?\s+member-links\s*\n((?:\s+[a-z0-9-]+/\d+/\d+\s*\n)*)',
                re.MULTILINE
            )
            member_match = member_pattern.search(source_config)
            if member_match:
                members = [m.strip() for m in member_match.group(1).strip().split('\n') if m.strip()]
            
            interfaces.append({
                'name': bundle_name,
                'type': 'bundle',
                'members': members
            })
    
    return interfaces


# =============================================================================
# SECTION-SPECIFIC STEP HANDLERS
# =============================================================================

def step_system(state: MirrorStepState, step_num: int) -> Optional[SectionResult]:
    """
    Step handler for System section.
    
    Includes: hostname, NCP config, NTP, SSH, timezone, login
    """
    show_step_header(
        step_num, state.total_steps, 
        state.SECTION_DISPLAY_NAMES['system'],
        state.source_hostname, state.target_hostname
    )
    
    # Parse system section from source
    system_config = extract_hierarchy_section(state.source_config, 'system')
    
    # Detect what's in system section
    has_ntp = 'ntp' in system_config.lower() if system_config else False
    has_ssh = 'ssh' in system_config.lower() if system_config else False
    has_login = 'login' in system_config.lower() if system_config else False
    ncps = get_ncp_slots(state.source_config)
    
    items = []
    if has_ntp:
        items.append("NTP configuration")
    if has_ssh:
        items.append("SSH security settings")
    if has_login:
        items.append("Login/user settings")
    if ncps:
        items.append(f"NCP slots: {ncps}")
    
    summary = ", ".join(items) if items else "Basic system config"
    
    # Transformations
    transforms = [
        ("Hostname", state.source_hostname, state.target_hostname)
    ]
    
    choice = show_step_menu(
        items_summary=summary,
        transformations=transforms,
        has_items=bool(system_config),
        allow_create=True
    )
    
    if choice == 'b':
        return None  # Signal to go back
    elif choice == '3':
        return SectionResult(action=StepAction.SKIP, summary="Skipped")
    elif choice == 'c':
        return SectionResult(action=StepAction.CREATE, summary="Create new")
    elif choice == '1':
        return SectionResult(
            action=StepAction.INCLUDE,
            items_count=len(items),
            summary=summary,
            config_snippet=system_config or "",
            transformations={'hostname': state.target_hostname}
        )
    elif choice == '2':
        # Select specific items - for system, just toggle subsections
        console.print("\n[bold]Select system components:[/bold]")
        include_ntp = Confirm.ask("  Include NTP?", default=has_ntp)
        include_ssh = Confirm.ask("  Include SSH?", default=has_ssh)
        include_login = Confirm.ask("  Include Login settings?", default=has_login)
        
        selected = []
        if include_ntp:
            selected.append("NTP")
        if include_ssh:
            selected.append("SSH")
        if include_login:
            selected.append("Login")
        
        return SectionResult(
            action=StepAction.SELECT,
            items_count=len(selected),
            items_selected=selected,
            summary=", ".join(selected) if selected else "None selected",
            transformations={'hostname': state.target_hostname}
        )
    
    return SectionResult(action=StepAction.SKIP, summary="Skipped")


def step_interfaces_wan(state: MirrorStepState, step_num: int) -> Optional[SectionResult]:
    """
    Step handler for WAN interfaces section.
    
    WAN interfaces are usually device-specific (connected to different neighbors).
    Default recommendation: Skip (keep target's existing).
    
    Offers WAN Mapping Wizard with LLDP suggestions for advanced mapping.
    """
    show_step_header(
        step_num, state.total_steps,
        state.SECTION_DISPLAY_NAMES['interfaces_wan'],
        state.source_hostname, state.target_hostname
    )
    
    # Get WAN interfaces from source
    wan_interfaces = get_wan_interfaces(state.source_config)
    
    if wan_interfaces:
        summary = f"{len(wan_interfaces)} WAN interfaces"
        console.print(f"\n[yellow]Note: WAN interfaces are usually device-specific.[/yellow]")
        console.print(f"[yellow]They connect to different neighbors on each device.[/yellow]")
        console.print(f"[dim]Recommendation: Skip (keep target's existing WAN config)[/dim]")
    else:
        summary = "No WAN interfaces found"
        return SectionResult(action=StepAction.SKIP, summary="No WAN interfaces in source")
    
    # Enhanced menu with WAN Mapping Wizard option
    console.print(f"\n[bold]Available options:[/bold]")
    console.print(f"  [1] Include all {len(wan_interfaces)} WAN interfaces")
    console.print(f"  [2] Select specific interfaces")
    console.print(f"  [3] Skip (keep target's existing) [Recommended]")
    console.print(f"  [W] WAN Mapping Wizard (with LLDP & IP suggestions)")
    console.print(f"  [B] Back")
    
    choice = Prompt.ask(
        "Select option",
        choices=["1", "2", "3", "w", "W", "b", "B"],
        default="3"
    ).lower()
    
    if choice == 'b':
        return None
    elif choice == '3':
        return SectionResult(action=StepAction.SKIP, summary="Skipped (recommended)")
    elif choice == '1':
        return SectionResult(
            action=StepAction.INCLUDE,
            items_count=len(wan_interfaces),
            items_selected=wan_interfaces,
            summary=f"{len(wan_interfaces)} WAN interfaces"
        )
    elif choice == '2':
        selected = select_items_from_list(wan_interfaces, "WAN interfaces")
        return SectionResult(
            action=StepAction.SELECT,
            items_count=len(selected),
            items_selected=selected,
            summary=f"{len(selected)}/{len(wan_interfaces)} WAN interfaces"
        )
    elif choice == 'w':
        # Launch WAN Mapping Wizard
        result = wan_interface_mapping_wizard(state, wan_interfaces)
        if result:
            return result
        # If wizard cancelled, show menu again
        return step_interfaces_wan(state, step_num)
    
    return SectionResult(action=StepAction.SKIP, summary="Skipped")


def step_interfaces_service(state: MirrorStepState, step_num: int) -> Optional[SectionResult]:
    """
    Step handler for Service interfaces (PWHE, L2-AC).
    
    These are the main interfaces to mirror for services.
    """
    show_step_header(
        step_num, state.total_steps,
        state.SECTION_DISPLAY_NAMES['interfaces_service'],
        state.source_hostname, state.target_hostname
    )
    
    # Get service interfaces from source
    service_ifaces = get_service_interfaces(state.source_config)
    
    # Categorize by type
    pwhe_ifaces = [i for i in service_ifaces if i.startswith('ph')]
    l2ac_ifaces = [i for i in service_ifaces if not i.startswith('ph') and '.' in i]
    
    if service_ifaces:
        parts = []
        if pwhe_ifaces:
            parts.append(f"{len(pwhe_ifaces)} PWHE")
        if l2ac_ifaces:
            parts.append(f"{len(l2ac_ifaces)} L2-AC")
        summary = ", ".join(parts) + " interfaces"
    else:
        summary = "No service interfaces found"
    
    # Detect parent interface transformation needs
    transforms = []
    if pwhe_ifaces:
        # Get unique parent interfaces (e.g., ph1, ph2)
        parents = set(re.match(r'(ph\d+)', i).group(1) for i in pwhe_ifaces if re.match(r'(ph\d+)', i))
        for parent in sorted(parents):
            transforms.append((f"Parent interface {parent}", parent, parent))  # Same by default
    
    choice = show_step_menu(
        items_summary=summary,
        transformations=transforms,
        has_items=bool(service_ifaces),
        allow_create=True
    )
    
    if choice == 'b':
        return None
    elif choice == '3':
        return SectionResult(action=StepAction.SKIP, summary="Skipped")
    elif choice == 'c':
        return SectionResult(action=StepAction.CREATE, summary="Create new")
    elif choice == '1':
        return SectionResult(
            action=StepAction.INCLUDE,
            items_count=len(service_ifaces),
            items_selected=service_ifaces,
            summary=summary
        )
    elif choice == '2':
        # Let user select by type
        console.print("\n[bold]Select interface types:[/bold]")
        selected = []
        if pwhe_ifaces:
            if Confirm.ask(f"  Include {len(pwhe_ifaces)} PWHE interfaces?", default=True):
                selected.extend(pwhe_ifaces)
        if l2ac_ifaces:
            if Confirm.ask(f"  Include {len(l2ac_ifaces)} L2-AC interfaces?", default=True):
                selected.extend(l2ac_ifaces)
        
        return SectionResult(
            action=StepAction.SELECT,
            items_count=len(selected),
            items_selected=selected,
            summary=f"{len(selected)}/{len(service_ifaces)} service interfaces"
        )
    
    return SectionResult(action=StepAction.SKIP, summary="Skipped")


def step_interfaces_loopback(state: MirrorStepState, step_num: int) -> Optional[SectionResult]:
    """
    Step handler for Loopback interfaces.
    
    Loopback IP must be unique per device - transformation required.
    """
    show_step_header(
        step_num, state.total_steps,
        state.SECTION_DISPLAY_NAMES['interfaces_loopback'],
        state.source_hostname, state.target_hostname
    )
    
    # Get loopback IPs
    src_lo0 = get_lo0_ip_from_config(state.source_config)
    tgt_lo0 = get_lo0_ip_from_config(state.target_config)
    
    if src_lo0:
        summary = f"lo0: {src_lo0}"
        transforms = [("Loopback IP", src_lo0, tgt_lo0 or "? (will prompt)")]
    else:
        summary = "No loopback configured"
        transforms = []
    
    console.print(f"\n[yellow]Note: Loopback IP must be unique per device.[/yellow]")
    console.print(f"[yellow]It is used for Router-ID and RD transformations.[/yellow]")
    
    choice = show_step_menu(
        items_summary=summary,
        transformations=transforms,
        has_items=bool(src_lo0),
        allow_create=True
    )
    
    if choice == 'b':
        return None
    elif choice == '3':
        return SectionResult(action=StepAction.SKIP, summary="Keep target's existing")
    elif choice == 'c':
        # Prompt for new loopback IP
        new_ip = Prompt.ask("Enter loopback IP for target (e.g., 1.1.1.1 or 1.1.1.1/32)", default="")
        if new_ip:
            # Normalize loopback - always add /32 if not specified
            new_ip = _normalize_loopback_ip(new_ip)
            return SectionResult(
                action=StepAction.CREATE,
                summary=f"Create lo0: {new_ip}",
                transformations={'lo0_ip': new_ip}
            )
        return SectionResult(action=StepAction.SKIP, summary="Skipped")
    elif choice in ('1', '2'):
        # Confirm or prompt for target loopback
        if tgt_lo0:
            confirmed_ip = Prompt.ask("Target loopback IP", default=tgt_lo0)
        else:
            confirmed_ip = prompt_transformation_value("Loopback IP", src_lo0, tgt_lo0)
        
        # Update global transforms
        state.global_transforms['loopback_ip'] = {
            'source': src_lo0,
            'target': confirmed_ip
        }
        
        return SectionResult(
            action=StepAction.INCLUDE,
            items_count=1,
            summary=f"lo0: {confirmed_ip}",
            transformations={'lo0_ip': confirmed_ip}
        )
    
    return SectionResult(action=StepAction.SKIP, summary="Skipped")


def step_fxc_services(state: MirrorStepState, step_num: int) -> Optional[SectionResult]:
    """
    Step handler for FXC (EVPN-VPWS) services.
    """
    show_step_header(
        step_num, state.total_steps,
        state.SECTION_DISPLAY_NAMES['fxc_services'],
        state.source_hostname, state.target_hostname
    )
    
    # Parse FXC services from source
    services = parse_existing_evpn_services(state.source_config)
    fxc_list = services.get('fxc', [])
    
    if fxc_list:
        summary = f"{len(fxc_list)} FXC instances"
        # Get EVI/RT info
        evis = set()
        for fxc in fxc_list:
            if 'evi' in fxc:
                evis.add(fxc.get('evi'))
        if evis:
            summary += f" (EVIs: {min(evis)}-{max(evis)})"
    else:
        summary = "No FXC services found"
    
    # RD transformation based on loopback
    transforms = []
    lo_transform = state.global_transforms.get('loopback_ip', {})
    if lo_transform.get('source') and lo_transform.get('target'):
        transforms.append((
            "RD (Route Distinguisher)",
            f"{lo_transform['source']}:X",
            f"{lo_transform['target']}:X"
        ))
    
    choice = show_step_menu(
        items_summary=summary,
        transformations=transforms,
        has_items=bool(fxc_list),
        allow_create=True
    )
    
    if choice == 'b':
        return None
    elif choice == '3':
        return SectionResult(action=StepAction.SKIP, summary="Skipped")
    elif choice == 'c':
        return SectionResult(action=StepAction.CREATE, summary="Create new FXC")
    elif choice == '1':
        return SectionResult(
            action=StepAction.INCLUDE,
            items_count=len(fxc_list),
            summary=summary
        )
    elif choice == '2':
        # Select by EVI range
        console.print("\n[bold]Select FXC by EVI range:[/bold]")
        evi_range = Prompt.ask("Enter EVI range (e.g., 1000-1099)", default="all")
        if evi_range.lower() == 'all':
            return SectionResult(
                action=StepAction.INCLUDE,
                items_count=len(fxc_list),
                summary=summary
            )
        else:
            # Parse range and filter
            try:
                if '-' in evi_range:
                    start, end = map(int, evi_range.split('-'))
                    filtered = [f for f in fxc_list if start <= f.get('evi', 0) <= end]
                else:
                    evi = int(evi_range)
                    filtered = [f for f in fxc_list if f.get('evi') == evi]
                return SectionResult(
                    action=StepAction.SELECT,
                    items_count=len(filtered),
                    summary=f"{len(filtered)}/{len(fxc_list)} FXC selected"
                )
            except ValueError:
                return SectionResult(
                    action=StepAction.INCLUDE,
                    items_count=len(fxc_list),
                    summary=summary
                )
    
    return SectionResult(action=StepAction.SKIP, summary="Skipped")


def step_vpls_services(state: MirrorStepState, step_num: int) -> Optional[SectionResult]:
    """
    Step handler for VPLS (EVPN-VPLS) services.
    """
    show_step_header(
        step_num, state.total_steps,
        state.SECTION_DISPLAY_NAMES['vpls_services'],
        state.source_hostname, state.target_hostname
    )
    
    # Parse VPLS services from source
    services = parse_existing_evpn_services(state.source_config)
    vpls_list = services.get('vpls', [])
    
    if vpls_list:
        summary = f"{len(vpls_list)} VPLS instances"
    else:
        summary = "No VPLS services found"
    
    # RD transformation
    transforms = []
    lo_transform = state.global_transforms.get('loopback_ip', {})
    if lo_transform.get('source') and lo_transform.get('target'):
        transforms.append((
            "RD (Route Distinguisher)",
            f"{lo_transform['source']}:X",
            f"{lo_transform['target']}:X"
        ))
    
    choice = show_step_menu(
        items_summary=summary,
        transformations=transforms,
        has_items=bool(vpls_list),
        allow_create=True
    )
    
    if choice == 'b':
        return None
    elif choice == '3':
        return SectionResult(action=StepAction.SKIP, summary="Skipped")
    elif choice == 'c':
        return SectionResult(action=StepAction.CREATE, summary="Create new VPLS")
    elif choice in ('1', '2'):
        return SectionResult(
            action=StepAction.INCLUDE,
            items_count=len(vpls_list),
            summary=summary
        )
    
    return SectionResult(action=StepAction.SKIP, summary="Skipped")


def step_vrf_instances(state: MirrorStepState, step_num: int) -> Optional[SectionResult]:
    """
    Step handler for VRF instances.
    """
    show_step_header(
        step_num, state.total_steps,
        state.SECTION_DISPLAY_NAMES['vrf_instances'],
        state.source_hostname, state.target_hostname
    )
    
    # Parse VRF instances from source
    vrf_list = parse_vrf_instances(state.source_config)
    
    if vrf_list:
        vrf_names = [v.get('name', 'unknown') for v in vrf_list]
        summary = f"{len(vrf_list)} VRF instances: {', '.join(vrf_names[:5])}"
        if len(vrf_names) > 5:
            summary += f"... (+{len(vrf_names)-5} more)"
    else:
        summary = "No VRF instances found"
    
    # RD transformation
    transforms = []
    lo_transform = state.global_transforms.get('loopback_ip', {})
    if lo_transform.get('source') and lo_transform.get('target'):
        transforms.append((
            "RD (Route Distinguisher)",
            f"{lo_transform['source']}:X",
            f"{lo_transform['target']}:X"
        ))
    
    choice = show_step_menu(
        items_summary=summary,
        transformations=transforms,
        has_items=bool(vrf_list),
        allow_create=True
    )
    
    if choice == 'b':
        return None
    elif choice == '3':
        return SectionResult(action=StepAction.SKIP, summary="Skipped")
    elif choice == 'c':
        return SectionResult(action=StepAction.CREATE, summary="Create new VRF")
    elif choice == '1':
        return SectionResult(
            action=StepAction.INCLUDE,
            items_count=len(vrf_list),
            items_selected=[v.get('name') for v in vrf_list],
            summary=f"{len(vrf_list)} VRF instances"
        )
    elif choice == '2':
        # Select specific VRFs
        vrf_names = [v.get('name', f'vrf_{i}') for i, v in enumerate(vrf_list)]
        selected = select_items_from_list(vrf_names, "VRF instances")
        return SectionResult(
            action=StepAction.SELECT,
            items_count=len(selected),
            items_selected=selected,
            summary=f"{len(selected)}/{len(vrf_list)} VRFs"
        )
    
    return SectionResult(action=StepAction.SKIP, summary="Skipped")


def step_multihoming(state: MirrorStepState, step_num: int) -> Optional[SectionResult]:
    """
    Step handler for Multihoming (ESI/DF) configuration.
    """
    show_step_header(
        step_num, state.total_steps,
        state.SECTION_DISPLAY_NAMES['multihoming'],
        state.source_hostname, state.target_hostname
    )
    
    # Parse MH config from source
    mh_config = parse_existing_multihoming(state.source_config)
    
    if mh_config:
        summary = f"{len(mh_config)} interfaces with MH config"
        # Show ESI info
        esi_count = sum(1 for v in mh_config.values() if v.get('esi'))
        if esi_count:
            summary += f" ({esi_count} ESIs)"
    else:
        summary = "No multihoming configuration found"
    
    console.print(f"\n[dim]Note: ESIs should match between dual-homed PEs.[/dim]")
    console.print(f"[dim]DF preference may need adjustment for proper failover.[/dim]")
    
    choice = show_step_menu(
        items_summary=summary,
        transformations=[],
        has_items=bool(mh_config),
        allow_create=True
    )
    
    if choice == 'b':
        return None
    elif choice == '3':
        return SectionResult(action=StepAction.SKIP, summary="Skipped")
    elif choice == 'c':
        return SectionResult(action=StepAction.CREATE, summary="Configure new MH")
    elif choice in ('1', '2'):
        return SectionResult(
            action=StepAction.INCLUDE,
            items_count=len(mh_config),
            summary=summary
        )
    
    return SectionResult(action=StepAction.SKIP, summary="Skipped")


def step_protocols(state: MirrorStepState, step_num: int) -> Optional[SectionResult]:
    """
    Step handler for Protocols (ISIS, LDP, BGP).
    """
    show_step_header(
        step_num, state.total_steps,
        state.SECTION_DISPLAY_NAMES['protocols'],
        state.source_hostname, state.target_hostname
    )
    
    # Parse protocols
    isis_config = parse_isis_config(state.source_config)
    ldp_config = parse_ldp_config(state.source_config)
    bgp_section = extract_hierarchy_section(state.source_config, 'protocols bgp')
    
    parts = []
    if isis_config:
        isis_instances = isis_config.get('instances', [])
        parts.append(f"ISIS ({len(isis_instances)} instances)")
    if ldp_config:
        parts.append("LDP enabled")
    if bgp_section:
        asn = state.global_transforms.get('asn', {}).get('source', '?')
        parts.append(f"BGP (AS {asn})")
    
    if parts:
        summary = ", ".join(parts)
    else:
        summary = "No routing protocols found"
    
    # Router-ID transformation
    transforms = []
    if isis_config or bgp_section:
        lo_transform = state.global_transforms.get('loopback_ip', {})
        if lo_transform.get('source') and lo_transform.get('target'):
            transforms.append((
                "Router-ID",
                lo_transform['source'],
                lo_transform['target']
            ))
    
    choice = show_step_menu(
        items_summary=summary,
        transformations=transforms,
        has_items=bool(parts),
        allow_create=True
    )
    
    if choice == 'b':
        return None
    elif choice == '3':
        return SectionResult(action=StepAction.SKIP, summary="Skipped")
    elif choice == 'c':
        return SectionResult(action=StepAction.CREATE, summary="Configure new protocols")
    elif choice == '1':
        return SectionResult(
            action=StepAction.INCLUDE,
            items_count=len(parts),
            summary=summary
        )
    elif choice == '2':
        # Select specific protocols
        console.print("\n[bold]Select protocols to include:[/bold]")
        selected = []
        if isis_config:
            if Confirm.ask("  Include ISIS?", default=True):
                selected.append("ISIS")
        if ldp_config:
            if Confirm.ask("  Include LDP?", default=True):
                selected.append("LDP")
        if bgp_section:
            if Confirm.ask("  Include BGP?", default=True):
                selected.append("BGP")
        
        return SectionResult(
            action=StepAction.SELECT,
            items_count=len(selected),
            items_selected=selected,
            summary=", ".join(selected) if selected else "None"
        )
    
    return SectionResult(action=StepAction.SKIP, summary="Skipped")


def step_qos(state: MirrorStepState, step_num: int) -> Optional[SectionResult]:
    """
    Step handler for QoS policies.
    """
    show_step_header(
        step_num, state.total_steps,
        state.SECTION_DISPLAY_NAMES['qos'],
        state.source_hostname, state.target_hostname
    )
    
    # Check for QoS section
    qos_section = extract_hierarchy_section(state.source_config, 'qos')
    
    if qos_section:
        # Count policies
        policy_count = qos_section.count('policy ')
        queue_count = qos_section.count('queue ')
        summary = f"QoS config: {policy_count} policies, {queue_count} queues"
    else:
        summary = "No QoS configuration found"
    
    choice = show_step_menu(
        items_summary=summary,
        transformations=[],
        has_items=bool(qos_section),
        allow_create=True
    )
    
    if choice == 'b':
        return None
    elif choice == '3':
        return SectionResult(action=StepAction.SKIP, summary="Skipped")
    elif choice == 'c':
        return SectionResult(action=StepAction.CREATE, summary="Configure new QoS")
    elif choice in ('1', '2'):
        return SectionResult(
            action=StepAction.INCLUDE,
            items_count=1,
            summary=summary,
            config_snippet=qos_section or ""
        )
    
    return SectionResult(action=StepAction.SKIP, summary="Skipped")


def show_final_review_summary(state: MirrorStepState) -> bool:
    """
    Show final review summary table and confirm before push.
    
    Includes dependency warnings (services without interfaces, etc.)
    
    Returns:
        True if user confirms, False to go back
    """
    console.print(Panel(
        f"[bold white]FINAL REVIEW[/bold white]\n"
        f"[dim]Source: {state.source_hostname} -> Target: {state.target_hostname}[/dim]",
        border_style="green"
    ))
    
    # Build summary table
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("Section", style="cyan", width=30)
    table.add_column("Action", justify="center", width=12)
    table.add_column("Items", width=35)
    
    included_count = 0
    for section_name, action_str, items_str in state.get_summary_table_data():
        if action_str == "Include" or action_str == "Select":
            style = "green"
            included_count += 1
        elif action_str == "Create":
            style = "yellow"
            included_count += 1
        elif action_str == "Skip":
            style = "dim"
        else:
            style = "dim"
        
        table.add_row(section_name, f"[{style}]{action_str}[/{style}]", items_str)
    
    console.print(table)
    
    # Check for dependency warnings
    warnings = _check_section_dependencies(state)
    if warnings:
        console.print("\n[bold yellow]⚠ Dependency Warnings:[/bold yellow]")
        for warning in warnings:
            console.print(f"  [yellow]• {warning}[/yellow]")
    
    if included_count == 0:
        console.print("\n[yellow]No sections selected to mirror.[/yellow]")
        return False
    
    console.print(f"\n[bold]{included_count} sections will be mirrored/created.[/bold]")
    
    if warnings:
        console.print()
        if not Confirm.ask("Continue despite warnings?", default=True):
            return False
    
    # Offer preview options
    while True:
        console.print("\n[bold]Options:[/bold]")
        console.print("  [P] Preview diff (show changes)")
        console.print("  [C] Continue to push")
        console.print("  [B] Back to edit sections")
        
        choice = Prompt.ask("Select", choices=["p", "P", "c", "C", "b", "B"], default="c").lower()
        
        if choice == 'b':
            return False
        elif choice == 'p':
            # Generate and show diff preview
            console.print("\n[dim]Generating preview...[/dim]")
            # Note: In real implementation, this would use the generated config
            # For now, show section-by-section summary
            _show_section_summaries(state)
            continue
        elif choice == 'c':
            if Confirm.ask("\nProceed to generate and push configuration?", default=True):
                return True
            continue
    
    return False


def _show_section_summaries(state: MirrorStepState) -> None:
    """Show detailed summaries of what will change per section."""
    console.print(Panel(
        "[bold cyan]Section Change Preview[/bold cyan]",
        border_style="cyan"
    ))
    
    for section_name in state.SECTION_ORDER:
        result = state.get_section_result(section_name)
        display_name = state.SECTION_DISPLAY_NAMES.get(section_name, section_name)
        
        if not result or result.action == StepAction.SKIP:
            console.print(f"\n[dim]{display_name}: Skipped (no changes)[/dim]")
            continue
        
        action_color = "green" if result.action in [StepAction.INCLUDE, StepAction.SELECT] else "yellow"
        console.print(f"\n[{action_color}]{display_name}:[/{action_color}]")
        console.print(f"  Action: {result.action.value}")
        
        if result.items_count > 0:
            console.print(f"  Items: {result.items_count}")
            
        if result.items_selected:
            # Show first few items
            for item in result.items_selected[:5]:
                console.print(f"    • {item}")
            if len(result.items_selected) > 5:
                console.print(f"    [dim]... and {len(result.items_selected) - 5} more[/dim]")
        
        if result.transformations:
            console.print(f"  Transformations:")
            for key, value in list(result.transformations.items())[:3]:
                console.print(f"    {key} -> {value}")
            if len(result.transformations) > 3:
                console.print(f"    [dim]... and {len(result.transformations) - 3} more[/dim]")
    
    console.print()


def _check_section_dependencies(state: MirrorStepState) -> List[str]:
    """
    Check for dependency issues between selected sections.
    
    Returns list of warning messages.
    """
    warnings = []
    
    # Check: Services selected but interfaces skipped
    services_selected = any([
        state.fxc_services and state.fxc_services.action in [StepAction.INCLUDE, StepAction.SELECT],
        state.vpls_services and state.vpls_services.action in [StepAction.INCLUDE, StepAction.SELECT],
        state.vrf_instances and state.vrf_instances.action in [StepAction.INCLUDE, StepAction.SELECT],
    ])
    
    service_interfaces_skipped = (
        state.interfaces_service is None or 
        state.interfaces_service.action == StepAction.SKIP
    )
    
    if services_selected and service_interfaces_skipped:
        warnings.append(
            "Services (FXC/VPLS/VRF) are included but Service Interfaces are skipped. "
            "Services may have no interface attachments on target."
        )
    
    # Check: Multihoming selected but interfaces skipped
    mh_selected = (
        state.multihoming and 
        state.multihoming.action in [StepAction.INCLUDE, StepAction.SELECT]
    )
    
    if mh_selected and service_interfaces_skipped:
        warnings.append(
            "Multihoming (ESI/DF) is included but Service Interfaces are skipped. "
            "MH config may reference non-existent interfaces."
        )
    
    # Check: Protocols selected but no interfaces
    protocols_selected = (
        state.protocols and 
        state.protocols.action in [StepAction.INCLUDE, StepAction.SELECT]
    )
    
    wan_skipped = (
        state.interfaces_wan is None or 
        state.interfaces_wan.action == StepAction.SKIP
    )
    
    if protocols_selected and wan_skipped:
        # This is actually OK - protocols will use target's existing interfaces
        pass
    
    return warnings


def show_diff_preview(state: MirrorStepState, new_config: str) -> None:
    """
    Show a diff preview of changes that will be made to target.
    
    Uses difflib to compare target's current config with the new mirrored config.
    """
    import difflib
    
    # Get relevant sections from current target config
    target_lines = state.target_config.split('\n')
    new_lines = new_config.split('\n')
    
    console.print(Panel(
        f"[bold cyan]DIFF PREVIEW[/bold cyan]\n"
        f"[dim]Changes to be applied on {state.target_hostname}[/dim]",
        border_style="cyan"
    ))
    
    # Generate unified diff
    diff = list(difflib.unified_diff(
        target_lines,
        new_lines,
        fromfile=f"{state.target_hostname} (current)",
        tofile=f"{state.target_hostname} (after mirror)",
        lineterm='',
        n=2  # Context lines
    ))
    
    if not diff:
        console.print("[green]No changes detected - configs are identical.[/green]")
        return
    
    # Count changes
    additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
    deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
    
    console.print(f"\n[bold]Summary: [green]+{additions} additions[/green], [red]-{deletions} deletions[/red][/bold]\n")
    
    # Show diff with colors (limit to first 50 lines for readability)
    max_lines = 50
    shown = 0
    
    for line in diff:
        if shown >= max_lines:
            remaining = len(diff) - shown
            console.print(f"\n[dim]... and {remaining} more lines (use full preview to see all)[/dim]")
            break
        
        if line.startswith('+++') or line.startswith('---'):
            console.print(f"[bold]{line}[/bold]")
        elif line.startswith('+'):
            console.print(f"[green]{line}[/green]")
        elif line.startswith('-'):
            console.print(f"[red]{line}[/red]")
        elif line.startswith('@@'):
            console.print(f"[cyan]{line}[/cyan]")
        else:
            console.print(f"[dim]{line}[/dim]")
        shown += 1
    
    console.print()


def generate_section_diff(state: MirrorStepState, section_name: str) -> str:
    """
    Generate diff for a specific section.
    
    Returns formatted diff string.
    """
    import difflib
    
    # Extract section from both configs
    target_section = extract_hierarchy_section(state.target_config, section_name)
    
    # Get the mirrored section based on state
    result = state.get_section_result(section_name)
    if not result or result.action == StepAction.SKIP:
        return "[dim]No changes - section skipped[/dim]"
    
    # For now, show what will be added
    source_section = extract_hierarchy_section(state.source_config, section_name)
    
    if not source_section:
        return "[dim]No content from source[/dim]"
    
    target_lines = target_section.split('\n') if target_section else []
    source_lines = source_section.split('\n')
    
    diff = list(difflib.unified_diff(
        target_lines,
        source_lines,
        lineterm='',
        n=1
    ))
    
    if not diff:
        return "[green]No changes[/green]"
    
    return '\n'.join(diff[:30])  # Limit output


def run_step_by_step_mirror(
    source_config: str,
    target_config: str,
    source_hostname: str,
    target_hostname: str
) -> Optional[MirrorStepState]:
    """
    Run the step-by-step mirror configuration flow.
    
    Returns:
        MirrorStepState with all section results, or None if cancelled
    """
    # Initialize state
    state = MirrorStepState(
        source_hostname=source_hostname,
        target_hostname=target_hostname,
        source_config=source_config,
        target_config=target_config
    )
    
    # Detect global transformations
    state.detect_global_transformations()
    
    # Step handlers in order
    step_handlers = [
        ('system', step_system),
        ('interfaces_wan', step_interfaces_wan),
        ('interfaces_service', step_interfaces_service),
        ('interfaces_loopback', step_interfaces_loopback),
        ('fxc_services', step_fxc_services),
        ('vpls_services', step_vpls_services),
        ('vrf_instances', step_vrf_instances),
        ('multihoming', step_multihoming),
        ('protocols', step_protocols),
        ('qos', step_qos),
    ]
    
    current_step = 0
    
    while current_step < len(step_handlers):
        section_name, handler = step_handlers[current_step]
        step_num = current_step + 1
        
        try:
            result = handler(state, step_num)
            
            if result is None:
                # User pressed Back
                if current_step > 0:
                    current_step -= 1
                    # Clear previous step's result
                    prev_section = step_handlers[current_step][0]
                    state.set_section_result(prev_section, None)
                else:
                    # At first step, cancel
                    if Confirm.ask("Cancel mirror configuration?", default=False):
                        return None
            else:
                # Store result and move to next step
                state.set_section_result(section_name, result)
                current_step += 1
                
        except BackException:
            if current_step > 0:
                current_step -= 1
            else:
                return None
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled.[/yellow]")
            return None
    
    # Final review
    console.print()
    if show_final_review_summary(state):
        return state
    else:
        # Go back to last step
        current_step = len(step_handlers) - 1
        # Re-run from last step (simplified - just return None to cancel for now)
        return None


class ConfigMirror:
    """
    Handles configuration mirroring between DNOS devices.
    
    OPTIMIZED for speed with:
    - Pre-compiled regex patterns
    - Cached section extractions
    - Single-pass transformations
    - Parallel section extraction
    
    Key responsibilities:
    - Extract unique sections from target device (to preserve)
    - Extract mirrored sections from source device (to copy)
    - Transform RDs to use target's loopback IP
    - Map interfaces between source and target
    - Generate merged configuration
    """
    
    def __init__(
        self,
        source_config: str,
        target_config: str,
        source_hostname: str,
        target_hostname: str
    ):
        """
        Initialize ConfigMirror with source and target configurations.
        
        Args:
            source_config: Full running config text from source device
            target_config: Full running config text from target device
            source_hostname: Source device hostname
            target_hostname: Target device hostname
        """
        self.source_config = source_config
        self.target_config = target_config
        self.source_hostname = source_hostname
        self.target_hostname = target_hostname
        
        # Parse key attributes
        self.source_lo0 = get_lo0_ip_from_config(source_config)
        self.target_lo0 = get_lo0_ip_from_config(target_config)
        self.source_rid = get_router_id_from_config(source_config)
        self.target_rid = get_router_id_from_config(target_config)
        self.source_asn = get_as_number_from_config(source_config)
        self.target_asn = get_as_number_from_config(target_config)
        
        # Parse WAN/IGP interfaces (interfaces in ISIS/LDP/OSPF sections)
        # These are more accurate than just "mpls enabled" detection
        self.source_wan = self._get_igp_interfaces(source_config)
        self.target_wan = self._get_igp_interfaces(target_config)
        
        # Parse multihoming
        self.source_mh = parse_existing_multihoming(source_config)
        self.target_mh = parse_existing_multihoming(target_config)
        
        # Parse services
        self.source_services = parse_existing_evpn_services(source_config)
        self.target_services = parse_existing_evpn_services(target_config)
        
        # Interface mapping (populated by map_interfaces)
        self.interface_map: Dict[str, str] = {}
        
        # Flag to track if system config was copied from source (vs preserved from target)
        self.system_copied_from_source = False
        
        # User-entered values for missing target infrastructure (to be included in output)
        self.user_entered_lo0 = None  # If user entered a loopback IP that wasn't in target
        self.user_entered_rid = None  # If user entered a router-id that wasn't in target
        self.user_entered_asn = None  # If user entered an ASN that wasn't in target
        
        # Section selection (from select_sections_to_mirror)
        # If None, all sections are included. Otherwise, dict of section_name -> bool
        self.section_selection: Optional[Dict[str, bool]] = None
        
        # =====================================================================
        # PRE-COMPILED REGEX PATTERNS (for speed)
        # =====================================================================
        self._rd_pattern = None
        self._rid_pattern = None
        self._iface_pattern = None
        self._compile_transform_patterns()
        
        # =====================================================================
        # SECTION CACHE (extract once, use many times)
        # =====================================================================
        self._section_cache: Dict[str, str] = {}
        
        # =====================================================================
        # SECTION STATES (persist across modify_mirror_sections calls)
        # =====================================================================
        self._section_states: Dict[str, dict] = {}  # Will store include/custom for each section
    
    @staticmethod
    def _get_igp_interfaces(config: str) -> List[str]:
        """Extract all interfaces that are configured in IGP protocols (ISIS/LDP/OSPF).
        
        This is more accurate than just checking for 'mpls enabled' since WAN interfaces
        are always part of IGP routing. Excludes loopback interfaces.
        
        Returns:
            List of interface names (e.g., ['ge400-0/0/4.12', 'bundle-100.12'])
        """
        igp_interfaces = set()
        protocols = extract_hierarchy_section(config, 'protocols')
        if not protocols:
            return []
        
        # Pattern matches "interface <name>" under ISIS, LDP, or OSPF sections
        # We need to be in the right context (inside isis/ldp/ospf)
        lines = protocols.split('\n')
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
                    igp_interfaces.add(iface_name)
        
        return sorted(igp_interfaces)
    
    def _compile_transform_patterns(self):
        """Pre-compile regex patterns for faster transformations."""
        # RD pattern
        if self.source_lo0 and self.target_lo0:
            source_ip = self.source_lo0.split('/')[0]
            self._rd_pattern = re.compile(
                rf'(route-distinguisher\s+){re.escape(source_ip)}(:\d+)',
                re.MULTILINE
            )
        
        # Router-ID pattern
        if self.source_rid and self.target_rid:
            self._rid_pattern = re.compile(
                rf'(router-id\s+){re.escape(self.source_rid)}',
                re.MULTILINE
            )
    
    def _get_cached_section(self, config: str, section_name: str) -> str:
        """Get section from cache or extract and cache it."""
        cache_key = f"{id(config)}_{section_name}"
        if cache_key not in self._section_cache:
            self._section_cache[cache_key] = extract_hierarchy_section(config, section_name) or ''
        return self._section_cache[cache_key]
    
    def get_source_summary(self) -> Dict[str, Any]:
        """Get summary of source device configuration."""
        return {
            'hostname': self.source_hostname,
            'lo0': self.source_lo0,
            'router_id': self.source_rid,
            'asn': self.source_asn,
            'wan_interfaces': self.source_wan,
            'wan_count': len(self.source_wan),
            'fxc_count': len(self.source_services.get('fxc', [])),
            'vpls_count': len(self.source_services.get('vpls', [])),
            'mh_interfaces': len(self.source_mh),
        }
    
    def get_target_summary(self) -> Dict[str, Any]:
        """Get summary of target device configuration."""
        return {
            'hostname': self.target_hostname,
            'lo0': self.target_lo0,
            'router_id': self.target_rid,
            'asn': self.target_asn,
            'wan_interfaces': self.target_wan,
            'wan_count': len(self.target_wan),
            'fxc_count': len(self.target_services.get('fxc', [])),
            'vpls_count': len(self.target_services.get('vpls', [])),
            'mh_interfaces': len(self.target_mh),
        }
    
    @property
    def requires_merge(self) -> bool:
        """Check if this mirror operation requires 'load merge' instead of 'load override'.
        
        Returns True if target has bundle interfaces that source doesn't have.
        Bundle interfaces are hardware-created (via physical port LAG membership)
        and cannot be recreated via load override.
        """
        target_bundles = self._extract_bundle_blocks(self.target_config)
        source_bundles = self._extract_bundle_blocks(self.source_config)
        
        # If target has bundles but source doesn't, require merge
        return bool(target_bundles) and not bool(source_bundles)
    
    def get_merge_reason(self) -> str:
        """Get the reason why merge is required, if any."""
        if self.requires_merge:
            target_bundles = self._extract_bundle_blocks(self.target_config)
            bundle_count = len([l for l in target_bundles.split('\n') if l.strip().startswith('bundle')])
            return f"Target has {bundle_count} bundle interfaces that source doesn't have"
        return ""
    
    # =========================================================================
    # EXTRACTION METHODS - Target Unique Sections
    # =========================================================================
    
    def extract_target_unique(self) -> Dict[str, str]:
        """
        Extract sections that must be preserved from target device.
        
        Returns:
            Dict with keys: system, wan_interfaces, lldp, bundles, lacp, lo0
        """
        return {
            'system': self._extract_system_section(self.target_config),
            'wan_interfaces': self._extract_wan_interface_configs(),
            'lldp': self._extract_lldp_section(self.target_config),
            'bundles': self._extract_bundle_configs(),
            'lacp': self._extract_lacp_section(self.target_config),
            'lo0': self._extract_lo0_config(),
            'physical_parents': self._extract_physical_parent_configs(),
        }
    
    def _extract_system_section(self, config: str) -> str:
        """Extract the full system configuration block."""
        lines = config.split('\n')
        result = []
        in_system = False
        brace_count = 0
        
        for line in lines:
            stripped = line.strip()
            
            if stripped == 'system':
                in_system = True
                result.append(line)
                continue
            
            if in_system:
                result.append(line)
                
                # Track end of system block (at base indentation with !)
                if stripped == '!' and len(line) - len(line.lstrip()) == 0:
                    break
                    
        return '\n'.join(result) if result else ''
    
    def _extract_wan_interface_configs(self) -> str:
        """Extract configuration for all WAN interfaces (MPLS-enabled)."""
        if not self.target_wan:
            return ''
        
        interface_configs = []
        
        for iface_name in self.target_wan:
            config_block = self._get_interface_block(self.target_config, iface_name)
            if config_block:
                interface_configs.append(config_block)
        
        return '\n'.join(interface_configs)
    
    def _extract_lldp_section(self, config: str) -> str:
        """Extract LLDP configuration from protocols section."""
        # LLDP is under protocols section
        protocols_section = extract_hierarchy_section(config, 'protocols')
        if not protocols_section:
            return ''
        
        # Find LLDP subsection
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
                # Check if we've exited LLDP block
                if stripped and current_indent <= lldp_indent and stripped != '!':
                    break
                result.append(line)
                if stripped == '!' and current_indent == lldp_indent:
                    break
        
        return '\n'.join(result)
    
    def _extract_bundle_configs(self) -> str:
        """Extract all bundle interface configurations."""
        lines = self.target_config.split('\n')
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
                # Check if this is a bundle interface
                if stripped.startswith('bundle'):
                    if current_bundle:
                        bundles.append('\n'.join(current_bundle))
                    current_bundle = [line]
                    in_bundle = True
                elif stripped == '!':
                    # Block terminator - include it and save bundle
                    if in_bundle:
                        current_bundle.append(line)
                        bundles.append('\n'.join(current_bundle))
                        current_bundle = []
                        in_bundle = False
                elif in_bundle:
                    # End of bundle, start of new non-bundle interface
                    # DON'T include this line (it's the new interface name)
                    bundles.append('\n'.join(current_bundle))
                    current_bundle = []
                    in_bundle = False
            elif in_bundle:
                # Content lines (indent > 2)
                current_bundle.append(line)
        
        if current_bundle:
            bundles.append('\n'.join(current_bundle))
        
        return '\n'.join(bundles)
    
    def _extract_lacp_section(self, config: str) -> str:
        """Extract LACP configuration from protocols section."""
        protocols_section = extract_hierarchy_section(config, 'protocols')
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
    
    def _extract_lo0_config(self) -> str:
        """Extract lo0 interface configuration."""
        return self._get_interface_block(self.target_config, 'lo0')
    
    def _extract_physical_parent_configs(self) -> str:
        """Extract physical parent interfaces (non-subinterface) that are WAN-related."""
        parent_configs = []
        
        # Get all physical parents of WAN interfaces
        wan_parents = set()
        for wan_iface in self.target_wan:
            if '.' in wan_iface:
                parent = wan_iface.split('.')[0]
                wan_parents.add(parent)
            else:
                wan_parents.add(wan_iface)
        
        for parent in wan_parents:
            config_block = self._get_interface_block(self.target_config, parent)
            if config_block:
                parent_configs.append(config_block)
        
        return '\n'.join(parent_configs)
    
    def _get_lldp_interfaces(self) -> Set[str]:
        """
        Extract physical interface names that are configured under LLDP.
        
        These are typically bundle member ports and other infrastructure interfaces
        that should NOT be deleted during mirror cleanup.
        
        Returns:
            Set of interface names (e.g., {'ge400-0/0/0', 'ge400-0/0/2'})
        """
        lldp_interfaces = set()
        lldp_section = self._extract_lldp_section(self.target_config)
        
        if not lldp_section:
            return lldp_interfaces
        
        # Parse LLDP section for interface references
        # Format: interface <name>\n  ...\n!
        lines = lldp_section.split('\n')
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('interface '):
                iface_name = stripped[len('interface '):].strip()
                if iface_name:
                    lldp_interfaces.add(iface_name)
        
        return lldp_interfaces
    
    # =========================================================================
    # EXTRACTION METHODS - Source Mirrored Sections
    # =========================================================================
    
    def extract_source_mirrored(self) -> Dict[str, str]:
        """
        Extract sections to mirror from source device.
        
        Returns:
            Dict with keys: system, services, routing_policy, acls, qos, multihoming
        """
        return {
            'system': self._extract_system_section_mirror(self.source_config),
            'services': self._extract_services_section(self.source_config),
            'routing_policy': self._extract_routing_policy_section(self.source_config),
            'acls': self._extract_acls_section(self.source_config),
            'qos': self._extract_qos_section(self.source_config),
            'multihoming': self._extract_multihoming_section(self.source_config),
            'service_interfaces': self._extract_service_interface_configs(),
        }
    
    def _extract_system_section_mirror(self, config: str) -> str:
        """
        Extract system section from source for mirroring.
        This will be transformed to use target's hostname and preserve target's unique settings.
        """
        return extract_hierarchy_section(config, 'system') or ''
    
    def _extract_services_section(self, config: str) -> str:
        """
        Extract network-services section EXCLUDING multihoming.
        
        Multihoming is handled separately to allow custom modifications.
        The returned section includes network-services header but NOT the
        closing '!' (which will be added after multihoming is inserted).
        """
        full_section = extract_hierarchy_section(config, 'network-services') or ''
        if not full_section:
            return ''
        
        # Remove multihoming subsection and final closing '!'
        # We'll add multihoming and closing later
        lines = full_section.split('\n')
        result = []
        in_multihoming = False
        mh_indent = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            # Detect multihoming start
            if stripped == 'multihoming' and indent == 2:
                in_multihoming = True
                mh_indent = indent
                continue
            
            # Skip lines inside multihoming
            if in_multihoming:
                if stripped == '!' and indent == mh_indent:
                    in_multihoming = False
                continue
            
            # Skip the final closing '!' for network-services
            # (will be added after multihoming)
            if i == len(lines) - 1 and stripped == '!':
                continue
            
            result.append(line)
        
        return '\n'.join(result)
    
    def _extract_routing_policy_section(self, config: str) -> str:
        """Extract routing-policy section."""
        return extract_hierarchy_section(config, 'routing-policy') or ''
    
    def _extract_acls_section(self, config: str) -> str:
        """Extract access-lists section."""
        return extract_hierarchy_section(config, 'access-lists') or ''
    
    def _extract_qos_section(self, config: str) -> str:
        """Extract QoS section."""
        return extract_hierarchy_section(config, 'qos') or ''
    
    def _extract_multihoming_section(self, config: str) -> str:
        """
        Extract multihoming section WITHOUT the trailing top-level '!'.
        
        Multihoming is INSIDE network-services, so the extraction may include
        the parent's closing '!' at indent 0. We need to strip that since
        the assembly code will add the proper closing for network-services.
        """
        full_section = extract_hierarchy_section(config, 'multihoming') or ''
        if not full_section:
            return ''
        
        lines = full_section.split('\n')
        
        # Remove trailing top-level '!' (belongs to network-services, not multihoming)
        while lines and lines[-1].strip() == '!' and len(lines[-1]) - len(lines[-1].lstrip()) == 0:
            lines.pop()
        
        return '\n'.join(lines)
    
    def _extract_service_interface_configs(self) -> str:
        """Extract interface configurations for service-attached interfaces."""
        # Find all interfaces attached to services
        service_interfaces = set()
        
        for svc_type in ['fxc', 'vpls', 'mpls']:
            for svc in self.source_services.get(svc_type, []):
                for iface in svc.get('interfaces', []):
                    service_interfaces.add(iface)
                    # Also add parent if sub-interface
                    if '.' in iface:
                        parent = iface.split('.')[0]
                        service_interfaces.add(parent)
        
        # Use efficient batch extraction instead of per-interface
        interface_blocks = self._get_all_interface_blocks(self.source_config, service_interfaces)
        
        # Sort and join
        configs = [interface_blocks[iface] for iface in sorted(service_interfaces) if iface in interface_blocks]
        
        return '\n'.join(configs)
    
    # =========================================================================
    # TRANSFORMATION METHODS
    # =========================================================================
    
    def transform_rds(self, config: str) -> str:
        """
        Replace all Route Distinguisher IP addresses with target's loopback.
        Uses pre-compiled pattern for speed.
        """
        if not self._rd_pattern:
            return config
        
        target_ip = self.target_lo0.split('/')[0]
        return self._rd_pattern.sub(rf'\g<1>{target_ip}\g<2>', config)
    
    def transform_router_id(self, config: str) -> str:
        """
        Replace router-id with target's router-id.
        Uses pre-compiled pattern for speed.
        """
        if not self._rid_pattern:
            return config
        
        return self._rid_pattern.sub(rf'\g<1>{self.target_rid}', config)
    
    def _compile_interface_pattern(self):
        """Compile the interface mapping pattern (call after map_interfaces)."""
        if not self.interface_map:
            self._iface_pattern = None
            return
        
        # Skip if "copy" strategy (same names)
        if all(src == tgt for src, tgt in self.interface_map.items()):
            self._iface_pattern = None
            return
        
        # Build single regex pattern for ALL interfaces at once
        sorted_interfaces = sorted(self.interface_map.keys(), key=len, reverse=True)
        self._iface_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(iface) for iface in sorted_interfaces) + r')\b'
        )
    
    def transform_interfaces(self, config: str) -> str:
        """
        Apply interface mapping to transform source interface names to target.
        OPTIMIZED: Uses pre-compiled single-pass regex.
        """
        if not self._iface_pattern:
            return config
        
        def replace_interface(match):
            return self.interface_map.get(match.group(1), match.group(1))
        
        return self._iface_pattern.sub(replace_interface, config)
    
    def transform_all(self, config: str) -> str:
        """
        Apply ALL transformations in optimal order.
        FAST: Combines RD, router-id, and interface transforms.
        """
        if not config:
            return config
        
        # Apply transformations in sequence (each is already optimized)
        result = config
        
        # RD transformation (single regex pass)
        if self._rd_pattern:
            target_ip = self.target_lo0.split('/')[0]
            result = self._rd_pattern.sub(rf'\g<1>{target_ip}\g<2>', result)
        
        # Router-ID transformation (single regex pass)
        if self._rid_pattern:
            result = self._rid_pattern.sub(rf'\g<1>{self.target_rid}', result)
        
        # Interface transformation (single regex pass for all interfaces)
        if self._iface_pattern:
            result = self._iface_pattern.sub(
                lambda m: self.interface_map.get(m.group(1), m.group(1)), 
                result
            )
        
        return result
    
    def transform_system_section(self, system_config: str) -> str:
        """
        Transform system section from source for mirroring to target.
        
        Preserves device uniqueness:
        - Hostname: Always use target's hostname
        - ISO-network: Preserve target's value (unique per device)
        - Other unique settings from target are preserved
        
        Args:
            system_config: System section from source device
            
        Returns:
            Transformed system section with target hostname and preserved unique settings
        """
        if not system_config:
            return ''
        
        import re as re_mod
        
        # Replace hostname with target hostname
        hostname_pattern = re_mod.compile(r'(^\s+hostname\s+)(\S+)', re_mod.MULTILINE)
        transformed = hostname_pattern.sub(
            rf'\g<1>{self.target_hostname}',
            system_config
        )
        
        # Get target's ISO-network if it exists (unique per device)
        target_iso = self._get_isis_iso_network(self.target_config)
        if target_iso:
            # Replace source's ISO-network with target's (preserve uniqueness)
            iso_pattern = re_mod.compile(r'(^\s+iso-network\s+)(\S+)', re_mod.MULTILINE)
            if iso_pattern.search(transformed):
                # Replace existing ISO-network
                transformed = iso_pattern.sub(
                    rf'\g<1>{target_iso}',
                    transformed
                )
            else:
                # Add target's ISO-network if source doesn't have it
                # Insert before closing '!'
                lines = transformed.split('\n')
                for i, line in enumerate(lines):
                    if line.strip() == '!' and len(line) - len(line.lstrip()) == 0:
                        lines.insert(i, f"  iso-network {target_iso}")
                        break
                transformed = '\n'.join(lines)
        
        return transformed
    
    def _get_isis_iso_network(self, config: str) -> Optional[str]:
        """Extract ISO-network from system section."""
        system_section = extract_hierarchy_section(config, 'system')
        if not system_section:
            return None
        
        # Look for iso-network line
        for line in system_section.split('\n'):
            stripped = line.strip()
            if stripped.startswith('iso-network'):
                parts = stripped.split()
                if len(parts) >= 2:
                    return parts[1]
        return None
    
    def transform_protocol_attributes(self, protocols: str) -> str:
        """
        Transform protocol-specific attributes for mirroring.
        
        This handles attributes that need special treatment:
        - BGP neighbors: SWAP source_lo0 <-> target_lo0 (peer IPs swap, not just replace)
        - ISO-network: Preserve TARGET's value (unique per device like router-id)
        - LDP transport-address: Use TARGET's loopback (unique per device)
        - Remove SOURCE's WAN interfaces from ISIS/LDP (will add target's separately)
        """
        if not protocols:
            return protocols
        
        result = protocols
        
        # 1. BGP Neighbor transformation - SWAP loopbacks for iBGP peering
        #    If source has neighbor X.X.X.X where X is target's lo0, change to source's lo0
        #    This is the REVERSE of RD transformation for BGP neighbors
        if self.source_lo0 and self.target_lo0:
            source_ip = self.source_lo0.split('/')[0]
            target_ip = self.target_lo0.split('/')[0]
            
            # Pattern: neighbor <target_lo0> -> neighbor <source_lo0>
            # (Source's BGP points to target, so mirrored config should point to source)
            result = re.sub(
                rf'(neighbor\s+){re.escape(target_ip)}(\s)',
                rf'\g<1>{source_ip}\g<2>',
                result
            )
            # Also handle end-of-line case
            result = re.sub(
                rf'(neighbor\s+){re.escape(target_ip)}$',
                rf'\g<1>{source_ip}',
                result,
                flags=re.MULTILINE
            )
        
        # 2. LDP transport-address: Use TARGET's loopback
        if self.source_lo0 and self.target_lo0:
            source_ip = self.source_lo0.split('/')[0]
            target_ip = self.target_lo0.split('/')[0]
            
            # Replace source's transport-address with target's
            result = re.sub(
                rf'(transport-address\s+){re.escape(source_ip)}',
                rf'\g<1>{target_ip}',
                result
            )
        
        # 3. Preserve target's ISO-network by replacing source's with target's
        target_iso = self._get_isis_iso_network(self.target_config)
        if target_iso:
            # Replace any iso-network line with target's value
            result = re.sub(
                r'(iso-network\s+)\S+',
                rf'\g<1>{target_iso}',
                result
            )
        
        # 4. Remove source's WAN interfaces from ISIS/LDP
        #    (Target's WAN interfaces will be added by _merge_wan_protocol_interfaces)
        result = self._remove_source_wan_from_protocols(result)
        
        return result
    
    def _remove_source_wan_from_protocols(self, protocols: str) -> str:
        """Remove source's WAN interface entries from ISIS/LDP/OSPF.
        
        This ensures we don't end up with BOTH source and target WAN interfaces.
        Target's WAN interfaces will be added separately.
        """
        if not self.source_wan:
            return protocols
        
        lines = protocols.split('\n')
        result = []
        skip_interface_block = False
        interface_block_indent = 0
        
        for line in lines:
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            # Detect interface lines that reference source WAN interfaces
            if stripped.startswith('interface '):
                iface_name = stripped.replace('interface ', '').strip()
                # Check if this is a source WAN interface
                iface_parent = iface_name.split('.')[0] if '.' in iface_name else iface_name
                if iface_name in self.source_wan or iface_parent in self.source_wan:
                    skip_interface_block = True
                    interface_block_indent = indent
                    continue
            
            # End of interface block
            if skip_interface_block:
                if stripped == '!' and indent <= interface_block_indent:
                    skip_interface_block = False
                    continue
                if indent <= interface_block_indent and stripped and stripped != '!':
                    skip_interface_block = False
                    # Don't skip this line - it's the start of something new
                    result.append(line)
                    continue
                # Skip lines inside source WAN interface block
                continue
            
            result.append(line)
        
        return '\n'.join(result)
    
    # =========================================================================
    # INTERFACE MAPPING METHODS
    # =========================================================================
    
    def get_source_service_interfaces(self) -> List[str]:
        """Get all interfaces used by services on source device."""
        interfaces = set()
        
        for svc_type in ['fxc', 'vpls', 'mpls']:
            for svc in self.source_services.get(svc_type, []):
                for iface in svc.get('interfaces', []):
                    interfaces.add(iface)
        
        return sorted(interfaces)
    
    def get_target_available_interfaces(self) -> List[str]:
        """Get available interfaces on target that are not WAN."""
        # Parse all interfaces from target config
        all_interfaces = self._get_all_interfaces(self.target_config)
        
        # Exclude WAN interfaces and their sub-interfaces
        wan_parents = set()
        for wan in self.target_wan:
            if '.' in wan:
                wan_parents.add(wan.split('.')[0])
            else:
                wan_parents.add(wan)
        
        available = []
        for iface in all_interfaces:
            # Skip WAN interfaces
            if iface in self.target_wan:
                continue
            # Skip sub-interfaces of WAN parents
            if '.' in iface:
                parent = iface.split('.')[0]
                if parent in wan_parents:
                    continue
            available.append(iface)
        
        return sorted(available)
    
    def map_interfaces_auto(self) -> Dict[str, str]:
        """
        Automatically map source interfaces to target interfaces.
        
        Strategy: Map by interface type (PWHE to PWHE, L2-AC to L2-AC)
        with sequential numbering on target.
        
        Returns:
            Dict mapping source interface names to target interface names
        """
        source_interfaces = self.get_source_service_interfaces()
        
        # Categorize source interfaces by type
        source_pwhe = [i for i in source_interfaces if i.startswith('ph')]
        source_l2ac = [i for i in source_interfaces if re.match(r'^(ge|xe|bundle)\d+', i)]
        
        # Find or create mapping for each type
        mapping = {}
        
        # Map PWHE interfaces
        if source_pwhe:
            # Check if target has PWHE
            target_pwhe = [i for i in self._get_all_interfaces(self.target_config) 
                          if i.startswith('ph')]
            
            # If target has PWHE, map to same names
            # Otherwise, keep same names (will be created)
            for iface in source_pwhe:
                mapping[iface] = iface  # Same interface name
        
        # Map L2-AC interfaces
        if source_l2ac:
            # For L2-AC, need to find available parent on target
            # This is more complex - for now, keep same names
            for iface in source_l2ac:
                mapping[iface] = iface
        
        self.interface_map = mapping
        # Compile interface pattern for transformation
        self._compile_interface_pattern()
        return mapping
    
    def map_interfaces_copy(self) -> Dict[str, str]:
        """
        Map interfaces by copying names exactly.
        OPTIMIZED: Skips regex compilation since no transformation needed.
        
        Returns:
            Dict mapping source interface names to same names
        """
        source_interfaces = self.get_source_service_interfaces()
        mapping = {iface: iface for iface in source_interfaces}
        
        self.interface_map = mapping
        # Don't compile pattern - copy means no transformation needed
        self._iface_pattern = None
        return mapping
    
    def map_interfaces_custom(
        self,
        source_prefix: str,
        target_prefix: str,
        start_offset: int = 0
    ) -> Dict[str, str]:
        """
        Map interfaces with custom prefix transformation.
        
        Args:
            source_prefix: Source interface prefix (e.g., 'ph')
            target_prefix: Target interface prefix (e.g., 'ge400-0/0/4.')
            start_offset: Starting number offset
            
        Returns:
            Dict mapping source interface names to target interface names
        """
        source_interfaces = self.get_source_service_interfaces()
        mapping = {}
        
        counter = start_offset
        for iface in sorted(source_interfaces):
            if iface.startswith(source_prefix):
                # Extract suffix after prefix
                suffix = iface[len(source_prefix):]
                # Generate target name
                if '.' in suffix:
                    # Sub-interface: ph1.100 -> target_prefix.100
                    parts = suffix.split('.', 1)
                    parent_num = counter + int(parts[0]) if parts[0].isdigit() else counter
                    mapping[iface] = f"{target_prefix}{parts[1]}"
                else:
                    # Parent interface
                    mapping[iface] = f"{target_prefix}{counter}"
                    counter += 1
        
        self.interface_map = mapping
        # Compile interface pattern for transformation
        self._compile_interface_pattern()
        return mapping
    
    # =========================================================================
    # CLEANUP/DELETE GENERATION
    # =========================================================================
    
    def generate_cleanup_commands(self) -> str:
        """
        Generate delete commands to remove config from target that doesn't exist on source.
        
        This ensures target PE matches source PE exactly (minus unique attributes).
        
        Deletes:
        - FXC/VPLS services on target that don't exist on source
        - Service interfaces on target that don't exist on source
        - Multihoming interfaces on target that don't exist on source
        
        Returns:
            DNOS delete commands as a string
        """
        delete_commands = []
        
        # 1. Find services to delete (on target but not on source)
        source_fxc_names = {svc['name'] for svc in self.source_services.get('fxc', [])}
        target_fxc_names = {svc['name'] for svc in self.target_services.get('fxc', [])}
        fxc_to_delete = target_fxc_names - source_fxc_names
        
        source_vpls_names = {svc['name'] for svc in self.source_services.get('vpls', [])}
        target_vpls_names = {svc['name'] for svc in self.target_services.get('vpls', [])}
        vpls_to_delete = target_vpls_names - source_vpls_names
        
        # Generate service delete commands (FLAT DNOS syntax)
        # DNOS requires: no network-services evpn-vpws-fxc instance NAME
        # NOT hierarchical: network-services > evpn-vpws-fxc > no instance NAME
        for svc_name in sorted(fxc_to_delete):
            delete_commands.append(f'no network-services evpn-vpws-fxc instance {svc_name}')
        
        for svc_name in sorted(vpls_to_delete):
            delete_commands.append(f'no network-services evpn-vpls instance {svc_name}')
        
        # 2. Find ALL interfaces to delete (including both parents and children)
        # Get ALL interfaces from both configs (both phX and phX.Y)
        target_all_ifaces = set(self._get_all_interfaces(self.target_config))
        source_all_ifaces = set(self._get_all_interfaces(self.source_config))
        
        # Also add parent interfaces for any sub-interfaces in source
        # (ensures we keep parents that have children on source)
        source_parents = set()
        for iface in source_all_ifaces:
            if '.' in iface:
                parent = iface.split('.')[0]
                source_parents.add(parent)
        source_all_ifaces = source_all_ifaces | source_parents
        
        # Apply interface mapping to source interfaces for proper comparison
        # Initialize mapped_source_ifaces (used later for parent/child checks)
        mapped_source_ifaces = set()
        
        if self.interface_map:
            # Map source interface names to target names
            for iface in source_all_ifaces:
                mapped_name = self.interface_map.get(iface, iface)
                mapped_source_ifaces.add(mapped_name)
                # Also map parent if it's a sub-interface
                if '.' in iface:
                    parent = iface.split('.')[0]
                    mapped_parent = self.interface_map.get(parent, parent)
                    mapped_source_ifaces.add(mapped_parent)
            # Interfaces to delete = target interfaces NOT in mapped source set
            all_ifaces_to_delete = target_all_ifaces - mapped_source_ifaces
        else:
            # No mapping - use source interfaces directly
            mapped_source_ifaces = source_all_ifaces
            all_ifaces_to_delete = target_all_ifaces - source_all_ifaces
        
        # Exclude WAN interfaces from deletion (both parent and sub-interfaces)
        wan_set = set(self.target_wan)
        wan_parents = {w.split('.')[0] for w in self.target_wan if '.' in w}
        all_ifaces_to_delete = all_ifaces_to_delete - wan_set - wan_parents
        
        # Exclude loopback interfaces (lo0 etc)
        all_ifaces_to_delete = {i for i in all_ifaces_to_delete if not i.startswith('lo')}
        
        # Exclude bundle interfaces (they're preserved from target)
        all_ifaces_to_delete = {i for i in all_ifaces_to_delete if not i.startswith('bundle')}
        
        # Exclude physical interfaces that are LLDP-configured (bundle members, WAN physical ports)
        # These are essential for connectivity and are preserved with target's LLDP config
        lldp_interfaces = self._get_lldp_interfaces()
        all_ifaces_to_delete = all_ifaces_to_delete - lldp_interfaces
        
        # IMPORTANT: Ensure we delete BOTH parent and child for PWHE interfaces
        # If we're deleting ph2001.1, we must also delete ph2001 (parent)
        # If we're deleting ph2001 (parent), also delete all its children
        final_delete_set = set(all_ifaces_to_delete)
        
        # Determine which source set to compare against
        source_keep_set = mapped_source_ifaces if self.interface_map else source_all_ifaces
        
        for iface in all_ifaces_to_delete:
            if '.' in iface:
                # It's a sub-interface - ensure parent is also in delete set
                parent = iface.split('.')[0]
                if parent in target_all_ifaces and parent not in source_keep_set:
                    final_delete_set.add(parent)
            else:
                # It's a parent - find all its children in target and add them
                for tgt_iface in target_all_ifaces:
                    if tgt_iface.startswith(iface + '.'):
                        final_delete_set.add(tgt_iface)
        
        # Sort: sub-interfaces first (ph1001.1), then parents (ph1001)
        # This ensures sub-ifs are deleted before parents (required order!)
        sub_ifaces = sorted([i for i in final_delete_set if '.' in i])
        parent_ifaces = sorted([i for i in final_delete_set if '.' not in i])
        sorted_ifaces = sub_ifaces + parent_ifaces
        
        # Generate interface delete commands with CORRECT DNOS syntax
        # Each delete is a standalone command: no interfaces <name>
        for iface in sorted_ifaces:
            delete_commands.append(f'no interfaces {iface}')
        
        # 3. Find multihoming interfaces to delete
        # self.source_mh is a dict with interface names as keys
        source_mh_ifaces = set(self.source_mh.keys()) if isinstance(self.source_mh, dict) else set()
        target_mh_ifaces = set(self.target_mh.keys()) if isinstance(self.target_mh, dict) else set()
        mh_to_delete = target_mh_ifaces - source_mh_ifaces
        
        # DNOS multihoming is under network-services hierarchy
        # Use hierarchical syntax: network-services > multihoming > no interface <name>
        if mh_to_delete:
            delete_commands.append('network-services')
            delete_commands.append('  multihoming')
            for iface in sorted(mh_to_delete):
                delete_commands.append(f'    no interface {iface}')
            delete_commands.append('  !')
            delete_commands.append('!')
        
        return '\n'.join(delete_commands)
    
    def _get_target_service_interfaces(self) -> Set[str]:
        """Get all interfaces used by services on target device."""
        interfaces = set()
        
        for svc_type in ['fxc', 'vpls', 'mpls']:
            for svc in self.target_services.get(svc_type, []):
                for iface in svc.get('interfaces', []):
                    interfaces.add(iface)
        
        return interfaces
    
    def get_cleanup_summary(self) -> Dict[str, int]:
        """Get a summary of what will be deleted."""
        source_fxc_names = {svc['name'] for svc in self.source_services.get('fxc', [])}
        target_fxc_names = {svc['name'] for svc in self.target_services.get('fxc', [])}
        
        source_vpls_names = {svc['name'] for svc in self.source_services.get('vpls', [])}
        target_vpls_names = {svc['name'] for svc in self.target_services.get('vpls', [])}
        
        # Count ALL interfaces to delete (both parents and children)
        target_all_ifaces = set(self._get_all_interfaces(self.target_config))
        source_all_ifaces = set(self._get_all_interfaces(self.source_config))
        
        # Also add parent interfaces for any sub-interfaces in source
        source_parents = set()
        for iface in source_all_ifaces:
            if '.' in iface:
                parent = iface.split('.')[0]
                source_parents.add(parent)
        source_all_ifaces = source_all_ifaces | source_parents
        
        # Apply interface mapping to source interfaces for proper comparison
        mapped_source_ifaces = set()
        if self.interface_map:
            for iface in source_all_ifaces:
                mapped_name = self.interface_map.get(iface, iface)
                mapped_source_ifaces.add(mapped_name)
                # Also map parent if it's a sub-interface
                if '.' in iface:
                    parent = iface.split('.')[0]
                    mapped_parent = self.interface_map.get(parent, parent)
                    mapped_source_ifaces.add(mapped_parent)
            all_ifaces_to_delete = target_all_ifaces - mapped_source_ifaces
        else:
            mapped_source_ifaces = source_all_ifaces
            all_ifaces_to_delete = target_all_ifaces - source_all_ifaces
        
        # Exclude WAN and loopback interfaces
        wan_set = set(self.target_wan)
        wan_parents = {w.split('.')[0] for w in self.target_wan if '.' in w}
        all_ifaces_to_delete = all_ifaces_to_delete - wan_set - wan_parents
        all_ifaces_to_delete = {i for i in all_ifaces_to_delete if not i.startswith('lo')}
        all_ifaces_to_delete = {i for i in all_ifaces_to_delete if not i.startswith('bundle')}
        
        # Exclude LLDP interfaces (bundle members, physical infrastructure ports)
        lldp_interfaces = self._get_lldp_interfaces()
        all_ifaces_to_delete = all_ifaces_to_delete - lldp_interfaces
        
        # Ensure we count BOTH parent and child for PWHE interfaces
        final_delete_set = set(all_ifaces_to_delete)
        for iface in all_ifaces_to_delete:
            if '.' in iface:
                # It's a sub-interface - ensure parent is also counted
                parent = iface.split('.')[0]
                if parent in target_all_ifaces and parent not in mapped_source_ifaces:
                    final_delete_set.add(parent)
            else:
                # It's a parent - find all its children in target
                for tgt_iface in target_all_ifaces:
                    if tgt_iface.startswith(iface + '.'):
                        final_delete_set.add(tgt_iface)
        
        # Count sub-interfaces and parents separately
        sub_iface_count = len([i for i in final_delete_set if '.' in i])
        parent_iface_count = len([i for i in final_delete_set if '.' not in i])
        
        # self.source_mh is a dict with interface names as keys
        source_mh_ifaces = set(self.source_mh.keys()) if isinstance(self.source_mh, dict) else set()
        target_mh_ifaces = set(self.target_mh.keys()) if isinstance(self.target_mh, dict) else set()
        
        # Note: Only include main counts in the dict, sub-counts are for display only
        # Total is calculated from: fxc + vpls + interfaces + mh
        return {
            'fxc_to_delete': len(target_fxc_names - source_fxc_names),
            'vpls_to_delete': len(target_vpls_names - source_vpls_names),
            'interfaces_to_delete': sub_iface_count + parent_iface_count,
            'mh_to_delete': len(target_mh_ifaces - source_mh_ifaces),
            # Display-only fields (not included in sum for total):
            '_sub_interfaces': sub_iface_count,
            '_parent_interfaces': parent_iface_count,
        }
    
    def analyze_smart_diff(self) -> Dict[str, Any]:
        """
        Analyze configuration differences for smart/optimized mirroring.
        
        Compares source and target to identify:
        - Identical services (same name, EVI, RT, interfaces) - can skip
        - Modified services (same name, different properties) - only change diffs
        - New services (on source, not target) - add
        - Removed services (on target, not source) - delete
        
        Returns:
            Dict with categorized services/interfaces for optimization
        """
        result = {
            'fxc': {
                'identical': [],    # Skip entirely (same on both)
                'modified': [],     # Same name, different props -> modify
                'add': [],          # Only on source -> add
                'delete': [],       # Only on target -> delete
            },
            'vpls': {
                'identical': [],
                'modified': [],
                'add': [],
                'delete': [],
            },
            'interfaces': {
                'identical': [],
                'modified': [],
                'add': [],
                'delete': [],
            },
            'multihoming': {
                'identical': [],
                'modified': [],
                'add': [],
                'delete': [],
            },
            'summary': {
                'total_items': 0,
                'can_skip': 0,
                'need_modify': 0,
                'need_add': 0,
                'need_delete': 0,
            }
        }
        
        # ═══════════════════════════════════════════════════════════════════
        # FAST PATH: If target is empty, just mark everything as "add"
        # This avoids expensive per-service comparison
        # ═══════════════════════════════════════════════════════════════════
        target_fxc_count = len(self.target_services.get('fxc', []))
        target_vpls_count = len(self.target_services.get('vpls', []))
        target_mh_count = len(self.target_mh) if isinstance(self.target_mh, dict) else 0
        
        if target_fxc_count == 0 and target_vpls_count == 0 and target_mh_count == 0:
            # Target is empty - just add everything from source (no comparison needed)
            source_fxc = [svc['name'] for svc in self.source_services.get('fxc', [])]
            source_vpls = [svc['name'] for svc in self.source_services.get('vpls', [])]
            source_ifaces = self.get_source_service_interfaces()
            source_mh = list(self.source_mh.keys()) if isinstance(self.source_mh, dict) else []
            
            result['fxc']['add'] = source_fxc
            result['vpls']['add'] = source_vpls
            result['interfaces']['add'] = source_ifaces
            result['multihoming']['add'] = source_mh
            
            total = len(source_fxc) + len(source_vpls) + len(source_ifaces) + len(source_mh)
            result['summary'] = {
                'total_items': total,
                'can_skip': 0,
                'need_modify': 0,
                'need_add': total,
                'need_delete': 0,
            }
            return result
        
        # Build lookup maps for efficient comparison
        source_fxc_map = {svc['name']: svc for svc in self.source_services.get('fxc', [])}
        target_fxc_map = {svc['name']: svc for svc in self.target_services.get('fxc', [])}
        
        source_vpls_map = {svc['name']: svc for svc in self.source_services.get('vpls', [])}
        target_vpls_map = {svc['name']: svc for svc in self.target_services.get('vpls', [])}
        
        # Analyze FXC services
        for name, src_svc in source_fxc_map.items():
            if name in target_fxc_map:
                tgt_svc = target_fxc_map[name]
                # Compare key properties (EVI, RT, interfaces)
                if self._services_identical(src_svc, tgt_svc):
                    result['fxc']['identical'].append(name)
                else:
                    # Same name but different - need to check what changed
                    diff = self._get_service_diff(src_svc, tgt_svc)
                    result['fxc']['modified'].append({'name': name, 'diff': diff})
            else:
                # Only on source -> add
                result['fxc']['add'].append(name)
        
        # Services only on target -> delete
        for name in target_fxc_map:
            if name not in source_fxc_map:
                result['fxc']['delete'].append(name)
        
        # Analyze VPLS services (same logic)
        for name, src_svc in source_vpls_map.items():
            if name in target_vpls_map:
                tgt_svc = target_vpls_map[name]
                if self._services_identical(src_svc, tgt_svc):
                    result['vpls']['identical'].append(name)
                else:
                    diff = self._get_service_diff(src_svc, tgt_svc)
                    result['vpls']['modified'].append({'name': name, 'diff': diff})
            else:
                result['vpls']['add'].append(name)
        
        for name in target_vpls_map:
            if name not in source_vpls_map:
                result['vpls']['delete'].append(name)
        
        # Analyze interfaces
        source_ifaces = set(self.get_source_service_interfaces())
        target_ifaces = self._get_target_service_interfaces()
        
        # Apply interface mapping for comparison
        mapped_source = {}
        for iface in source_ifaces:
            mapped_name = self.interface_map.get(iface, iface)
            mapped_source[mapped_name] = iface  # mapped -> original
        
        for mapped_name, orig_name in mapped_source.items():
            if mapped_name in target_ifaces:
                result['interfaces']['identical'].append(mapped_name)
            else:
                result['interfaces']['add'].append(mapped_name)
        
        for iface in target_ifaces:
            if iface not in mapped_source:
                result['interfaces']['delete'].append(iface)
        
        # Analyze multihoming
        source_mh_ifaces = set(self.source_mh.keys()) if isinstance(self.source_mh, dict) else set()
        target_mh_ifaces = set(self.target_mh.keys()) if isinstance(self.target_mh, dict) else set()
        
        for iface in source_mh_ifaces:
            mapped_iface = self.interface_map.get(iface, iface)
            if iface in target_mh_ifaces:
                src_mh = self.source_mh.get(iface, {})
                tgt_mh = self.target_mh.get(iface, {})
                if self._mh_identical(src_mh, tgt_mh):
                    result['multihoming']['identical'].append(iface)
                else:
                    diff = self._get_mh_diff(src_mh, tgt_mh)
                    result['multihoming']['modified'].append({'iface': iface, 'diff': diff})
            else:
                result['multihoming']['add'].append(iface)
        
        for iface in target_mh_ifaces:
            if iface not in source_mh_ifaces:
                result['multihoming']['delete'].append(iface)
        
        # Compute summary
        for category in ['fxc', 'vpls', 'interfaces', 'multihoming']:
            result['summary']['can_skip'] += len(result[category]['identical'])
            result['summary']['need_modify'] += len(result[category]['modified'])
            result['summary']['need_add'] += len(result[category]['add'])
            result['summary']['need_delete'] += len(result[category]['delete'])
        
        result['summary']['total_items'] = (
            result['summary']['can_skip'] + 
            result['summary']['need_modify'] + 
            result['summary']['need_add'] + 
            result['summary']['need_delete']
        )
        
        return result
    
    def _services_identical(self, src_svc: Dict, tgt_svc: Dict) -> bool:
        """Check if two services have identical key properties."""
        # Compare EVI
        if src_svc.get('evi') != tgt_svc.get('evi'):
            return False
        
        # Compare Route Targets (same for EVPN peering)
        if set(src_svc.get('route_targets', [])) != set(tgt_svc.get('route_targets', [])):
            return False
        
        # Compare interface attachments (after mapping)
        src_ifaces = set()
        for iface in src_svc.get('interfaces', []):
            mapped = self.interface_map.get(iface, iface)
            src_ifaces.add(mapped)
        
        tgt_ifaces = set(tgt_svc.get('interfaces', []))
        
        if src_ifaces != tgt_ifaces:
            return False
        
        return True
    
    def _get_service_diff(self, src_svc: Dict, tgt_svc: Dict) -> Dict[str, Any]:
        """Get what's different between two services."""
        diff = {}
        
        # Check RD (expected to be different - uses different loopback)
        if src_svc.get('rd') != tgt_svc.get('rd'):
            diff['rd'] = {'src': src_svc.get('rd'), 'tgt': tgt_svc.get('rd')}
        
        # Check EVI
        if src_svc.get('evi') != tgt_svc.get('evi'):
            diff['evi'] = {'src': src_svc.get('evi'), 'tgt': tgt_svc.get('evi')}
        
        # Check RTs
        src_rts = set(src_svc.get('route_targets', []))
        tgt_rts = set(tgt_svc.get('route_targets', []))
        if src_rts != tgt_rts:
            diff['route_targets'] = {'src': list(src_rts), 'tgt': list(tgt_rts)}
        
        # Check interfaces
        src_ifaces = {self.interface_map.get(i, i) for i in src_svc.get('interfaces', [])}
        tgt_ifaces = set(tgt_svc.get('interfaces', []))
        if src_ifaces != tgt_ifaces:
            diff['interfaces'] = {
                'add': list(src_ifaces - tgt_ifaces),
                'remove': list(tgt_ifaces - src_ifaces),
            }
        
        return diff
    
    def _mh_identical(self, src_mh, tgt_mh) -> bool:
        """Check if two MH configs are identical.
        
        Args:
            src_mh: Either a string (ESI value) or dict with 'esi', 'redundancy_mode'
            tgt_mh: Either a string (ESI value) or dict with 'esi', 'redundancy_mode'
        """
        # Handle string format (just ESI values from parse_existing_multihoming)
        if isinstance(src_mh, str) and isinstance(tgt_mh, str):
            return src_mh == tgt_mh
        
        # Handle mixed types - not identical
        if isinstance(src_mh, str) or isinstance(tgt_mh, str):
            return False
        
        # Handle dict format
        if isinstance(src_mh, dict) and isinstance(tgt_mh, dict):
            # Compare ESI
            if src_mh.get('esi') != tgt_mh.get('esi'):
                return False
            
            # Compare redundancy mode
            if src_mh.get('redundancy_mode') != tgt_mh.get('redundancy_mode'):
                return False
            
            return True
        
        return False
    
    def _get_mh_diff(self, src_mh, tgt_mh) -> Dict[str, Any]:
        """Get what's different between two MH configs.
        
        Args:
            src_mh: Either a string (ESI value) or dict with 'esi', 'redundancy_mode', 'df_preference'
            tgt_mh: Either a string (ESI value) or dict with 'esi', 'redundancy_mode', 'df_preference'
        """
        diff = {}
        
        # Handle string format (just ESI values)
        if isinstance(src_mh, str) and isinstance(tgt_mh, str):
            if src_mh != tgt_mh:
                diff['esi'] = {'src': src_mh, 'tgt': tgt_mh}
            return diff
        
        # Handle mixed - convert strings to dict format
        if isinstance(src_mh, str):
            src_mh = {'esi': src_mh}
        if isinstance(tgt_mh, str):
            tgt_mh = {'esi': tgt_mh}
        
        # Ensure dict type for .get() calls
        src_mh = src_mh if isinstance(src_mh, dict) else {}
        tgt_mh = tgt_mh if isinstance(tgt_mh, dict) else {}
        
        if src_mh.get('esi') != tgt_mh.get('esi'):
            diff['esi'] = {'src': src_mh.get('esi'), 'tgt': tgt_mh.get('esi')}
        
        if src_mh.get('redundancy_mode') != tgt_mh.get('redundancy_mode'):
            diff['redundancy_mode'] = {'src': src_mh.get('redundancy_mode'), 'tgt': tgt_mh.get('redundancy_mode')}
        
        if src_mh.get('df_preference') != tgt_mh.get('df_preference'):
            diff['df_preference'] = {'src': src_mh.get('df_preference'), 'tgt': tgt_mh.get('df_preference')}
        
        return diff
    
    # =========================================================================
    # DIFF-BASED CONFIG GENERATION (for Terminal Paste optimization)
    # =========================================================================
    
    def generate_diff_only_config(self) -> Tuple[str, Dict[str, Any]]:
        """
        Generate configuration containing ONLY the differences (for Terminal Paste).
        
        This is much more efficient than pasting the entire config when the
        target already has most of the configuration.
        
        Uses analyze_smart_diff() to identify:
        - Items to DELETE (on target, not on source)
        - Items to ADD (on source, not on target)  
        - Items to MODIFY (different between source and target)
        - Items to SKIP (identical on both)
        
        Returns:
            Tuple of (diff_config_text, summary_dict)
        """
        diff_analysis = self.analyze_smart_diff()
        
        output_lines = []
        
        # =====================================================================
        # PHASE 1: DELETE commands (items on target but not source)
        # =====================================================================
        delete_lines = []
        
        # Delete FXC services
        for svc_name in diff_analysis['fxc']['delete']:
            delete_lines.append(f'no network-services evpn-vpws-fxc instance {svc_name}')
        
        # Delete VPLS services
        for svc_name in diff_analysis['vpls']['delete']:
            delete_lines.append(f'no network-services evpn-vpls instance {svc_name}')
        
        # Delete interfaces (service interfaces, not WAN/bundle)
        for iface in diff_analysis['interfaces']['delete']:
            delete_lines.append(f'no interfaces {iface}')
        
        # Delete multihoming interfaces
        for iface in diff_analysis['multihoming']['delete']:
            delete_lines.append(f'network-services')
            delete_lines.append(f'  multihoming')
            delete_lines.append(f'    no interface {iface}')
            delete_lines.append(f'  !')
            delete_lines.append(f'!')
        
        if delete_lines:
            output_lines.append('! === DELETE: Items to remove ===')
            output_lines.extend(delete_lines)
            output_lines.append('')
        
        # =====================================================================
        # PHASE 2: ADD/MODIFY commands
        # =====================================================================
        add_lines = []
        
        # Add new FXC services
        for svc_name in diff_analysis['fxc']['add']:
            svc_config = self._generate_fxc_service_config(svc_name)
            if svc_config:
                add_lines.append(svc_config)
        
        # Add new VPLS services
        for svc_name in diff_analysis['vpls']['add']:
            svc_config = self._generate_vpls_service_config(svc_name)
            if svc_config:
                add_lines.append(svc_config)
        
        # Add new interfaces
        for iface in diff_analysis['interfaces']['add']:
            iface_config = self._generate_interface_config(iface)
            if iface_config:
                add_lines.append(iface_config)
        
        # Add new multihoming interfaces
        for iface in diff_analysis['multihoming']['add']:
            mh_config = self._generate_mh_interface_config(iface)
            if mh_config:
                add_lines.append(mh_config)
        
        # Handle modified items (need to delete old + add new, or use replace commands)
        for mod_svc in diff_analysis['fxc']['modified']:
            svc_name = mod_svc['name']
            svc_config = self._generate_fxc_service_config(svc_name)
            if svc_config:
                add_lines.append(f'! Modified FXC: {svc_name}')
                add_lines.append(svc_config)
        
        for mod_svc in diff_analysis['vpls']['modified']:
            svc_name = mod_svc['name']
            svc_config = self._generate_vpls_service_config(svc_name)
            if svc_config:
                add_lines.append(f'! Modified VPLS: {svc_name}')
                add_lines.append(svc_config)
        
        for mod_mh in diff_analysis['multihoming']['modified']:
            iface = mod_mh['iface']
            mh_config = self._generate_mh_interface_config(iface)
            if mh_config:
                add_lines.append(f'! Modified MH: {iface}')
                add_lines.append(mh_config)
        
        if add_lines:
            output_lines.append('! === ADD/MODIFY: New or changed items ===')
            output_lines.extend(add_lines)
        
        diff_config = '\n'.join(output_lines)
        
        summary = {
            'total_changes': len(delete_lines) + len(add_lines),
            'deletes': len(diff_analysis['fxc']['delete']) + len(diff_analysis['vpls']['delete']) + len(diff_analysis['interfaces']['delete']) + len(diff_analysis['multihoming']['delete']),
            'adds': len(diff_analysis['fxc']['add']) + len(diff_analysis['vpls']['add']) + len(diff_analysis['interfaces']['add']) + len(diff_analysis['multihoming']['add']),
            'modifies': len(diff_analysis['fxc']['modified']) + len(diff_analysis['vpls']['modified']) + len(diff_analysis['multihoming']['modified']),
            'skipped': diff_analysis['summary']['can_skip'],
            'diff_analysis': diff_analysis,
        }
        
        return diff_config, summary
    
    def _generate_fxc_service_config(self, svc_name: str) -> str:
        """Generate FXC service configuration block from source."""
        # Find the service in source_services
        for svc in self.source_services.get('fxc', []):
            if svc['name'] == svc_name:
                return self._extract_service_block_from_source('evpn-vpws-fxc', svc_name)
        return ''
    
    def _generate_vpls_service_config(self, svc_name: str) -> str:
        """Generate VPLS service configuration block from source."""
        for svc in self.source_services.get('vpls', []):
            if svc['name'] == svc_name:
                return self._extract_service_block_from_source('evpn-vpls', svc_name)
        return ''
    
    def _generate_interface_config(self, iface_name: str) -> str:
        """Generate interface configuration block from source."""
        # Get original interface name (before mapping)
        orig_iface = iface_name
        for src, tgt in self.interface_map.items():
            if tgt == iface_name:
                orig_iface = src
                break
        
        # Extract interface block from source and transform
        block = self._get_interface_block(self.source_config, orig_iface)
        if block:
            # Apply transformations (RD, interface name)
            block = self.transform_all(block)
        return block
    
    def _generate_mh_interface_config(self, iface_name: str) -> str:
        """Generate multihoming interface configuration block from source.
        
        Preserves the original structure including nested blocks like designated-forwarder.
        Output structure:
          network-services           (0-space)
            multihoming              (2-space)
              interface phX.Y        (4-space)
                esi ...              (6-space)
                designated-forwarder (6-space)
                  algorithm ...      (8-space)
                !                    (6-space)
              !                      (4-space)
            !                        (2-space)
          !                          (0-space)
        """
        mh_section = extract_hierarchy_section(self.source_config, 'multihoming')
        if not mh_section:
            return ''
        
        # Find interface block within multihoming
        lines = mh_section.split('\n')
        result = []
        in_interface = False
        interface_indent = 0
        base_indent = 0  # The indent of interface inside original multihoming
        
        for line in lines:
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            if stripped == f'interface {iface_name}' or stripped.startswith(f'interface {iface_name} '):
                in_interface = True
                interface_indent = indent
                base_indent = indent  # Usually 4 (inside multihoming at 2)
                result.append('network-services')
                result.append('  multihoming')
                result.append(f'    interface {iface_name}')
            elif in_interface:
                # End of this interface block
                if stripped == '!' and indent <= interface_indent:
                    result.append('    !')
                    result.append('  !')
                    result.append('!')
                    break
                elif stripped or stripped == '!':
                    # Preserve relative indentation from the original
                    # Original: base_indent for interface, +2 for each level
                    # Output: 4 for interface, +2 for each level
                    relative_indent = indent - base_indent
                    output_indent = 4 + relative_indent  # 4 is interface's indent in output
                    result.append(' ' * output_indent + stripped)
        
        # If we didn't find a proper end, close the block
        if in_interface and (not result or result[-1] != '!'):
            result.append('    !')
            result.append('  !')
            result.append('!')
        
        return '\n'.join(result)
    
    def _extract_service_block_from_source(self, service_type: str, service_name: str) -> str:
        """Extract a specific service block from source config."""
        ns_section = extract_hierarchy_section(self.source_config, 'network-services')
        if not ns_section:
            return ''
        
        lines = ns_section.split('\n')
        result = []
        in_service_type = False
        in_target_instance = False
        instance_indent = 0
        
        for line in lines:
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            # Detect service type section (e.g., evpn-vpws-fxc)
            if stripped == service_type and indent == 2:
                in_service_type = True
                result.append('network-services')
                result.append(line)
                continue
            
            if in_service_type:
                # Detect target instance
                if stripped.startswith('instance ') and stripped.split()[1] == service_name:
                    in_target_instance = True
                    instance_indent = indent
                    result.append(line)
                    continue
                
                if in_target_instance:
                    result.append(line)
                    # End of instance
                    if stripped == '!' and indent <= instance_indent:
                        # Close the hierarchy properly
                        result.append('  !')  # Close service type
                        result.append('!')  # Close network-services
                        break
                        
                # End of service type section without finding instance
                if stripped == '!' and indent <= 2:
                    in_service_type = False
        
        config = '\n'.join(result)
        # Apply RD transformation
        config = self.transform_rds(config)
        return config
    
    # =========================================================================
    # GENERATE MISSING INFRASTRUCTURE CONFIG
    # =========================================================================
    
    def generate_missing_infrastructure(self) -> Dict[str, str]:
        """
        Generate config blocks for infrastructure that was entered by user but missing from target.
        
        This creates actual DNOS config for:
        - Lo0 interface with IPv4 address (if user entered loopback IP)
        - BGP section with router-id and ASN (if user entered these)
        
        Returns:
            Dict with keys 'lo0', 'bgp' containing config blocks or empty strings
        """
        result = {'lo0': '', 'bgp': ''}
        
        # Generate Lo0 interface if user entered a loopback IP and target didn't have one
        if self.user_entered_lo0:
            lo0_ip = self.user_entered_lo0.split('/')[0]  # Remove /32 if present
            result['lo0'] = f"""  lo0
    ipv4-address {lo0_ip}/32
  !"""
        
        # Generate BGP config with router-id if user entered values
        if self.user_entered_asn or self.user_entered_rid:
            bgp_lines = []
            asn = self.user_entered_asn or self.source_asn
            rid = self.user_entered_rid or self.user_entered_lo0 or self.target_lo0
            
            if asn and rid:
                rid_ip = rid.split('/')[0] if rid else ''
                bgp_lines.append(f"routing")
                bgp_lines.append(f"  bgp {asn}")
                bgp_lines.append(f"    router-id {rid_ip}")
                bgp_lines.append(f"  !")
                bgp_lines.append(f"!")
                result['bgp'] = '\n'.join(bgp_lines)
        
        return result
    
    # =========================================================================
    # MERGE AND GENERATE
    # =========================================================================
    
    def generate_merged_config(self, progress_callback=None) -> str:
        """
        Generate the final merged configuration with CORRECT DNOS syntax.
        
        DNOS Syntax Rules:
        - Each top-level hierarchy ends with ! at column 0
        - Nested blocks end with ! at their indentation level
        - Interface names at 2-space indent (no 'interface' keyword inside interfaces section)
        - Proper 2-space indentation per level
        
        Combines:
        - Target's unique sections (system, WAN, LLDP, bundles, Lo0)
        - Source's mirrored sections (services, policies, etc.)
        - With RD/router-id/interface transformations applied
        
        If section_selection is set, only includes sections that are True.
        
        Args:
            progress_callback: Optional callback(message, percent) for progress updates
            
        Returns:
            Complete merged configuration text
        """
        # Helper to check if a section should be included
        def include_section(section_name: str) -> bool:
            if self.section_selection is None:
                return True  # No selection = include all
            return self.section_selection.get(section_name, True)
        
        def update_progress(msg, pct):
            if progress_callback:
                progress_callback(msg, pct)
        
        # =====================================================================
        # PHASE 1: Extract all sections in parallel-ready manner
        # =====================================================================
        update_progress("Extracting target sections...", 5)
        
        # Extract target unique sections (fast - just text extraction)
        target_system = self._extract_clean_section(self.target_config, 'system')
        target_lo0 = self._extract_lo0_block(self.target_config)
        target_wan = self._extract_wan_interface_blocks(self.target_config)
        target_bundles = self._extract_bundle_blocks(self.target_config)
        target_bundle_members = self._extract_bundle_member_interfaces(self.target_config)
        target_lldp = self._extract_protocol_subsection(self.target_config, 'lldp')
        target_lacp = self._extract_protocol_subsection(self.target_config, 'lacp')
        
        # ─────────────────────────────────────────────────────────────────────
        # SMART SYSTEM SECTION HANDLING
        # Check if system section should be mirrored from source
        # If system is selected for mirroring, use source's system with transformations
        # Otherwise, merge/preserve target's system
        # ─────────────────────────────────────────────────────────────────────
        source_system = self._extract_clean_section(self.source_config, 'system')
        target_system_lines = len(target_system.split('\n')) if target_system else 0
        source_system_lines = len(source_system.split('\n')) if source_system else 0
        
        # Check if system section is selected for mirroring
        mirror_system = include_section('system') and source_system
        
        if mirror_system:
            # Mirror system section from source with device uniqueness preserved
            transformed_system = self.transform_system_section(source_system)
            
            # Merge with target's unique settings (preserve target's unique values)
            if target_system:
                import re as re_mod
                
                # Parse both system sections into key-value pairs
                def parse_system_config(config: str) -> dict:
                    """Parse system config into dict of setting -> full line"""
                    settings = {}
                    lines = config.split('\n')
                    for line in lines:
                        stripped = line.strip()
                        if stripped and stripped != 'system' and stripped != '!':
                            # Use first word as key (e.g., 'hostname', 'contact-info', 'location')
                            key = stripped.split()[0] if stripped.split() else ''
                            if key:
                                settings[key] = line
                    return settings
                
                source_settings = parse_system_config(transformed_system)
                target_settings = parse_system_config(target_system)
                
                # Start with source settings (mirrored)
                merged_settings = source_settings.copy()
                
                # ALWAYS use target's hostname (device uniqueness)
                if 'hostname' in target_settings:
                    merged_settings['hostname'] = target_settings['hostname']
                elif 'hostname' in merged_settings:
                    # Ensure target hostname is used
                    merged_settings['hostname'] = re_mod.sub(
                        r'(\s+hostname\s+)\S+',
                        rf'\g<1>{self.target_hostname}',
                        merged_settings['hostname']
                    )
                
                # Preserve target's unique settings that source doesn't have
                unique_from_target = []
                for key, line in target_settings.items():
                    if key not in source_settings and key != 'hostname':
                        merged_settings[key] = line
                        unique_from_target.append(key)
                
                # Build merged system config
                merged_lines = ['system']
                # Sort settings for consistent output (hostname first)
                for key in ['hostname'] + sorted(k for k in merged_settings.keys() if k != 'hostname'):
                    if key in merged_settings:
                        merged_lines.append(merged_settings[key])
                merged_lines.append('!')
                
                target_system = '\n'.join(merged_lines)
                self.system_copied_from_source = True
                
                # Store what was preserved from target
                if unique_from_target:
                    self._target_unique_system_settings = unique_from_target
            else:
                # Target has no system, use transformed source system
                target_system = transformed_system
                self.system_copied_from_source = True
        
        elif source_system and target_system:
            # Not mirroring system - merge source and target (existing behavior)
            import re as re_mod
            
            # Parse both system sections into key-value pairs
            def parse_system_config(config: str) -> dict:
                """Parse system config into dict of setting -> full line"""
                settings = {}
                lines = config.split('\n')
                for line in lines:
                    stripped = line.strip()
                    if stripped and stripped != 'system' and stripped != '!':
                        # Use first word as key (e.g., 'hostname', 'contact-info', 'location')
                        key = stripped.split()[0] if stripped.split() else ''
                        if key:
                            settings[key] = line
                return settings
            
            source_settings = parse_system_config(source_system)
            target_settings = parse_system_config(target_system)
            
            # Start with source settings
            merged_settings = source_settings.copy()
            
            # ALWAYS use target's hostname
            if 'hostname' in target_settings:
                merged_settings['hostname'] = target_settings['hostname']
            elif 'hostname' in merged_settings:
                # Transform source hostname to target hostname
                merged_settings['hostname'] = re_mod.sub(
                    r'(\s+hostname\s+)\S+',
                    rf'\g<1>{self.target_hostname}',
                    merged_settings['hostname']
                )
            
            # Add unique target settings that source doesn't have
            unique_from_target = []
            for key, line in target_settings.items():
                if key not in source_settings and key != 'hostname':
                    merged_settings[key] = line
                    unique_from_target.append(key)
            
            # Build merged system config
            merged_lines = ['system']
            # Sort settings for consistent output (hostname first)
            for key in ['hostname'] + sorted(k for k in merged_settings.keys() if k != 'hostname'):
                if key in merged_settings:
                    merged_lines.append(merged_settings[key])
            merged_lines.append('!')
            
            target_system = '\n'.join(merged_lines)
            self.system_copied_from_source = True
            
            # Store what was preserved from target
            if unique_from_target:
                self._target_unique_system_settings = unique_from_target
        
        elif source_system and not target_system:
            # Target has no system, use source's with target hostname
            import re as re_mod
            transformed_system = source_system
            
            # Replace hostname
            hostname_pattern = re_mod.compile(r'(^\s+hostname\s+)(\S+)', re_mod.MULTILINE)
            transformed_system = hostname_pattern.sub(
                rf'\g<1>{self.target_hostname}',
                transformed_system
            )
            
            target_system = transformed_system
            self.system_copied_from_source = True
        
        update_progress("Extracting source sections...", 15)
        
        # Extract source sections to mirror (PARALLEL for speed)
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        section_results = {}
        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = {
                executor.submit(self._extract_clean_section, self.source_config, 'network-services'): 'services',
                executor.submit(self._extract_clean_section, self.source_config, 'routing-policy'): 'routing_policy',
                executor.submit(self._extract_clean_section, self.source_config, 'access-lists'): 'acls',
                executor.submit(self._extract_clean_section, self.source_config, 'qos'): 'qos',
                executor.submit(self._extract_clean_section, self.source_config, 'multihoming'): 'mh',
                executor.submit(self._extract_source_protocols): 'protocols',
                executor.submit(self._extract_clean_section, self.source_config, 'routing'): 'routing',
            }
            
            for future in as_completed(futures):
                section_results[futures[future]] = future.result()
        
        source_services = section_results.get('services', '')
        source_routing_policy = section_results.get('routing_policy', '')
        source_acls = section_results.get('acls', '')
        source_qos = section_results.get('qos', '')
        source_mh = section_results.get('mh', '')
        source_protocols = section_results.get('protocols', '')
        source_routing = section_results.get('routing', '')
        
        # Transform system section if mirroring (already handled above in system section logic)
        # System transformation preserves device uniqueness (hostname, ISO-network, etc.)
        
        # =====================================================================
        # PHASE 2: Extract service interfaces (optimized single-pass)
        # =====================================================================
        update_progress("Extracting service interfaces...", 30)
        source_svc_interfaces = self._extract_service_interface_configs()
        
        # =====================================================================
        # PHASE 3: Transform ALL sections (OPTIMIZED - combined regex passes)
        # =====================================================================
        update_progress("Transforming configurations...", 50)
        
        # Use transform_all for maximum speed (combines RD + router-id + interface transforms)
        if source_services:
            source_services = self.transform_all(source_services)
        
        update_progress("Transforming interface configs...", 65)
        if source_svc_interfaces:
            source_svc_interfaces = self.transform_all(source_svc_interfaces)
        
        if source_mh:
            source_mh = self.transform_all(source_mh)
        
        if source_protocols:
            source_protocols = self.transform_router_id(source_protocols)
        
        if source_routing:
            source_routing = self.transform_all(source_routing)  # RD + router-id transforms
        
        # =====================================================================
        # PHASE 4: Build final config with CORRECT DNOS syntax
        # =====================================================================
        update_progress("Building configuration...", 80)
        
        output_lines = []
        
        # --- SYSTEM SECTION ---
        # Note: System section is typically preserved/transformed but can be excluded
        if target_system and include_section('system'):
            output_lines.append(self._ensure_section_format(target_system, 'system'))
            output_lines.append('')
        
        # --- INTERFACES SECTION ---
        # IMPORTANT: Bundle interfaces are hardware-created (via physical port LAG membership).
        # They require physical port membership to exist and cannot be created via config alone.
        # 
        # Strategy: Always include target's bundles in the config (to preserve them).
        # Order matters: Bundles MUST come FIRST so sub-interfaces can reference them.
        # 
        # Note: If source has no bundles but target does, the caller should use 'load merge'
        # instead of 'load override' to preserve the hardware-created bundle interfaces.
        # This is flagged via self.requires_merge property.
        
        # Get any user-entered infrastructure that needs to be added
        missing_infra = self.generate_missing_infrastructure()
        
        iface_content = []
        if target_bundles:
            iface_content.append(target_bundles)  # Bundles FIRST!
        if target_bundle_members:
            iface_content.append(target_bundle_members)  # Bundle members (with bundle-id)
        
        # Use target's lo0 if it exists, otherwise use user-entered lo0
        if target_lo0:
            iface_content.append(target_lo0)
        elif missing_infra.get('lo0'):
            iface_content.append(missing_infra['lo0'])
        
        if target_wan:
            iface_content.append(target_wan)
        if source_svc_interfaces and include_section('service_interfaces'):
            iface_content.append(source_svc_interfaces)
        
        if iface_content:
            output_lines.append('interfaces')
            for content in iface_content:
                # Only strip trailing whitespace - keep leading indentation!
                content = content.rstrip()
                if content and content.strip() != '!':
                    output_lines.append(content)
            output_lines.append('!')
            output_lines.append('')
        
        # --- PROTOCOLS SECTION ---
        # Extract target's WAN/bundle protocol interfaces (ISIS/LDP/OSPF entries for WAN interfaces)
        target_wan_protocols = self._extract_target_wan_protocol_config()
        
        # Merge target's WAN protocol interfaces into source protocols
        if source_protocols and target_wan_protocols:
            source_protocols = self._merge_wan_protocol_interfaces(
                source_protocols, target_wan_protocols
            )
        
        proto_content = []
        if target_lldp:
            proto_content.append(target_lldp)
        if target_lacp:
            proto_content.append(target_lacp)
        if source_protocols and include_section('protocols'):
            proto_content.append(source_protocols)
        
        if proto_content:
            output_lines.append('protocols')
            for content in proto_content:
                # Only strip trailing whitespace - keep leading indentation!
                content = content.rstrip()
                if content and content.strip() != '!' and content.strip() != 'protocols':
                    output_lines.append(content)
            output_lines.append('!')
            output_lines.append('')
        
        # --- NETWORK-SERVICES SECTION ---
        if source_services and include_section('services'):
            output_lines.append(self._ensure_section_format(source_services, 'network-services'))
            output_lines.append('')
        
        # --- ROUTING-POLICY SECTION ---
        if source_routing_policy and include_section('routing_policy'):
            output_lines.append(self._ensure_section_format(source_routing_policy, 'routing-policy'))
            output_lines.append('')
        
        # --- ACCESS-LISTS SECTION ---
        if source_acls and include_section('acls'):
            output_lines.append(self._ensure_section_format(source_acls, 'access-lists'))
            output_lines.append('')
        
        # --- QOS SECTION ---
        if source_qos and include_section('qos'):
            output_lines.append(self._ensure_section_format(source_qos, 'qos'))
            output_lines.append('')
        
        # --- ROUTING SECTION (BGP, etc.) ---
        # Use source's routing (BGP) config, or generate from user-entered values if missing
        if include_section('routing'):
            if source_routing:
                output_lines.append(self._ensure_section_format(source_routing, 'routing'))
                output_lines.append('')
            elif missing_infra.get('bgp'):
                # Target had no BGP config, but user entered ASN/router-id - generate it
                output_lines.append(missing_infra['bgp'])
                output_lines.append('')
        
        # NOTE: Multihoming is NOT added as a separate section here because
        # it's already INSIDE network-services. In DNOS, multihoming is a
        # sub-hierarchy of network-services, not a top-level hierarchy.
        # 
        # If custom multihoming modifications are needed, use modify_mirror_sections()
        # which properly handles extracting network-services WITHOUT multihoming
        # and then inserting the (possibly modified) multihoming before closing.
        
        # =====================================================================
        # PHASE 5: Final cleanup
        # =====================================================================
        update_progress("Finalizing...", 95)
        
        merged = '\n'.join(output_lines)
        
        # Clean up syntax issues
        merged = self._cleanup_dnos_syntax(merged)
        
        update_progress("Complete!", 100)
        return merged
    
    def _extract_clean_section(self, config: str, section_name: str) -> str:
        """Extract a complete hierarchy section cleanly."""
        section = extract_hierarchy_section(config, section_name)
        if not section:
            return ''
        return section.strip()
    
    def _extract_lo0_block(self, config: str) -> str:
        """Extract loopback interface block."""
        blocks = self._get_all_interface_blocks(config, {'lo0'})
        return blocks.get('lo0', '')
    
    def _extract_wan_interface_blocks(self, config: str) -> str:
        """Extract all WAN interfaces (MPLS-enabled) and their parents."""
        wan_set = set()
        for iface in self.target_wan:
            wan_set.add(iface)
            # Add parent if subinterface
            if '.' in iface:
                parent = iface.split('.')[0]
                wan_set.add(parent)
        
        if not wan_set:
            return ''
        
        blocks = self._get_all_interface_blocks(config, wan_set)
        # Sort interfaces: parents first, then subinterfaces
        sorted_ifaces = sorted(blocks.keys(), key=lambda x: (x.split('.')[0], '.' in x, x))
        return '\n'.join(blocks[i] for i in sorted_ifaces if i in blocks)
    
    def _extract_bundle_blocks(self, config: str) -> str:
        """Extract bundle/bundle-ether interface blocks."""
        # Find all bundle interfaces (both 'bundle-N' and 'bundle-ether-N' formats)
        bundle_pattern = re.compile(r'^  (bundle(?:-ether)?-?\d+(?:\.\d+)?)\s*$', re.MULTILINE)
        bundles = set(bundle_pattern.findall(config))
        
        if not bundles:
            return ''
        
        blocks = self._get_all_interface_blocks(config, bundles)
        sorted_bundles = sorted(blocks.keys(), key=lambda x: (x.split('.')[0], '.' in x, x))
        return '\n'.join(blocks[b] for b in sorted_bundles if b in blocks)
    
    def _extract_bundle_member_interfaces(self, config: str) -> str:
        """Extract physical interfaces that are bundle members (have bundle-id configured).
        
        These are interfaces like ge400-0/0/0 with 'bundle-id 100' that become
        members of a bundle (LAG). Without these, bundle interfaces will go DOWN
        because they have no member ports.
        
        Returns:
            String containing all bundle member interface configurations.
        """
        lines = config.split('\n')
        bundle_members = []
        current_block = []
        current_iface = None
        in_interfaces = False
        has_bundle_id = False
        
        for line in lines:
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            # Detect interfaces section
            if stripped == 'interfaces' and indent == 0:
                in_interfaces = True
                continue
            
            # End of interfaces section
            if in_interfaces and indent == 0 and stripped and stripped != '!':
                # Save last block if it had bundle-id
                if current_block and has_bundle_id:
                    bundle_members.extend(current_block)
                in_interfaces = False
                continue
            
            if not in_interfaces:
                continue
            
            # Check for interface start at 2-space indent
            if indent == 2 and stripped and not stripped.startswith('!'):
                # Save previous block if it had bundle-id
                if current_block and has_bundle_id:
                    bundle_members.extend(current_block)
                
                # Start new interface block
                current_iface = stripped
                current_block = [line]
                has_bundle_id = False
                continue
            
            # Check for end of interface block
            if current_iface and stripped == '!' and indent == 2:
                current_block.append(line)
                if has_bundle_id:
                    bundle_members.extend(current_block)
                current_block = []
                current_iface = None
                has_bundle_id = False
                continue
            
            # Accumulate lines in current interface block
            if current_iface:
                current_block.append(line)
                # Check for bundle-id attribute
                if stripped.startswith('bundle-id'):
                    has_bundle_id = True
        
        # Handle trailing interface block
        if current_block and has_bundle_id:
            bundle_members.extend(current_block)
        
        return '\n'.join(bundle_members) if bundle_members else ''
    
    def _extract_protocol_subsection(self, config: str, subsection: str) -> str:
        """Extract a subsection from protocols (e.g., lldp, lacp)."""
        protocols = extract_hierarchy_section(config, 'protocols')
        if not protocols:
            return ''
        
        lines = protocols.split('\n')
        result = []
        in_subsection = False
        subsection_indent = 0
        
        for line in lines:
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            if stripped == subsection and indent == 2:
                in_subsection = True
                subsection_indent = indent
                result.append(line)
                continue
            
            if in_subsection:
                if stripped == '!' and indent <= subsection_indent:
                    result.append(line)
                    break
                if indent <= subsection_indent and stripped and stripped != '!':
                    break
                result.append(line)
        
        return '\n'.join(result)
    
    def _extract_source_protocols(self) -> str:
        """Extract protocols from source, excluding LLDP and LACP.
        
        Also applies protocol-specific transformations:
        - BGP neighbors: swap source_lo0 <-> target_lo0 for iBGP peering
        - ISO-network: preserve target's value
        - LDP transport-address: use target's loopback
        - Remove source's WAN interfaces (target's will be added separately)
        """
        protocols = extract_hierarchy_section(self.source_config, 'protocols')
        if not protocols:
            return ''
        
        # Remove LLDP and LACP (we use target's)
        lines = protocols.split('\n')
        result = []
        skip_until_indent = -1
        
        for line in lines:
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            # Skip the protocols header and footer
            if stripped == 'protocols' or (stripped == '!' and indent == 0):
                continue
            
            # Skip LLDP and LACP blocks
            if stripped in ('lldp', 'lacp') and indent == 2:
                skip_until_indent = indent
                continue
            
            if skip_until_indent >= 0:
                if stripped == '!' and indent <= skip_until_indent:
                    skip_until_indent = -1
                    continue
                if indent <= skip_until_indent and stripped and stripped != '!':
                    skip_until_indent = -1
                else:
                    continue
            
            result.append(line)
        
        # Apply protocol-specific transformations
        filtered_protocols = '\n'.join(result)
        transformed_protocols = self.transform_protocol_attributes(filtered_protocols)
        
        return transformed_protocols
    
    def _extract_target_wan_protocol_config(self) -> Dict[str, str]:
        """Extract target's WAN/bundle interface config from ISIS/LDP/OSPF.
        
        Returns dict with keys like 'isis_interfaces', 'ldp_interfaces', etc.
        These should be merged back when building final config.
        """
        result = {}
        protocols = extract_hierarchy_section(self.target_config, 'protocols')
        if not protocols:
            return result
        
        # Identify WAN/bundle interfaces from target
        wan_ifaces = set(self.target_wan)
        # Add bundle interfaces
        bundle_pattern = re.compile(r'^  (bundle(?:-ether)?-?\d+(?:\.\d+)?)\s*$', re.MULTILINE)
        wan_ifaces.update(bundle_pattern.findall(self.target_config))
        
        if not wan_ifaces:
            return result
        
        # Extract ISIS interfaces for WAN/bundles
        isis_ifaces = self._extract_protocol_interface_entries(protocols, 'isis', wan_ifaces)
        if isis_ifaces:
            result['isis_interfaces'] = isis_ifaces
        
        # Extract LDP interfaces for WAN/bundles
        ldp_ifaces = self._extract_protocol_interface_entries(protocols, 'ldp', wan_ifaces)
        if ldp_ifaces:
            result['ldp_interfaces'] = ldp_ifaces
        
        # Extract OSPF interfaces for WAN/bundles
        ospf_ifaces = self._extract_protocol_interface_entries(protocols, 'ospf', wan_ifaces)
        if ospf_ifaces:
            result['ospf_interfaces'] = ospf_ifaces
        
        return result
    
    def _extract_protocol_interface_entries(self, protocols: str, proto_name: str, 
                                            target_ifaces: set) -> str:
        """Extract interface entries from a protocol section for specific interfaces."""
        lines = protocols.split('\n')
        result = []
        in_proto = False
        in_interface = False
        current_iface_block = []
        current_iface_name = None
        proto_indent = -1
        
        for line in lines:
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            # Detect protocol section start (e.g., "isis 1", "ldp", "ospf 1")
            if indent == 2 and stripped.startswith(proto_name):
                in_proto = True
                proto_indent = indent
                continue
            
            # End of protocol section
            if in_proto and indent <= proto_indent and stripped and stripped != '!':
                in_proto = False
                # Save any pending interface block
                if in_interface and current_iface_name in target_ifaces:
                    result.extend(current_iface_block)
                current_iface_block = []
                in_interface = False
                continue
            
            if not in_proto:
                continue
            
            # Detect interface entry start
            if stripped.startswith('interface ') and indent > proto_indent:
                # Save previous interface block if it was a target interface
                if in_interface and current_iface_name in target_ifaces:
                    result.extend(current_iface_block)
                
                # Start new interface block
                current_iface_name = stripped.replace('interface ', '').strip()
                current_iface_block = [line]
                in_interface = True
                continue
            
            # Collect lines in current interface block
            if in_interface:
                current_iface_block.append(line)
                # Check for interface block end
                if stripped == '!' and indent > proto_indent:
                    if current_iface_name in target_ifaces:
                        result.extend(current_iface_block)
                    current_iface_block = []
                    in_interface = False
        
        # Handle any trailing interface block
        if in_interface and current_iface_name in target_ifaces:
            result.extend(current_iface_block)
        
        return '\n'.join(result) if result else ''
    
    def _merge_wan_protocol_interfaces(self, source_protocols: str, 
                                       target_wan_protocols: Dict[str, str]) -> str:
        """Add target's WAN interfaces to source's routing protocols.
        
        Key behavior: Use SOURCE's routing protocol type, but add TARGET's WAN interfaces.
        
        Example: If source has OSPF and target has ISIS with bundle-100.12:
        - Result: OSPF with bundle-100.12 interface entries
        
        This ensures the routing protocol from source is adopted, but with
        target's actual WAN interfaces configured.
        """
        # Get target's WAN interface names
        wan_ifaces = set(self.target_wan)
        bundle_pattern = re.compile(r'^  (bundle(?:-ether)?-?\d+(?:\.\d+)?)\s*$', re.MULTILINE)
        wan_ifaces.update(bundle_pattern.findall(self.target_config))
        
        # Filter to only sub-interfaces (with IP addresses typically)
        wan_ifaces = {i for i in wan_ifaces if '.' in i or 'bundle' in i}
        
        if not wan_ifaces:
            return source_protocols
        
        lines = source_protocols.split('\n')
        result = []
        
        # Track what we've inserted to avoid duplicates
        isis_inserted = False
        ldp_inserted = False
        ospf_inserted = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            result.append(line)
            
            # Insert WAN interfaces after ISIS instance header (from source)
            # ISIS structure: isis (2-space) > instance IGP (4-space) > interface (6-space)
            if stripped.startswith('instance') and indent == 4 and not isis_inserted:
                # Check if we're inside an ISIS section by looking back
                in_isis = any('isis' in result[j].strip() and len(result[j]) - len(result[j].lstrip()) == 2 
                             for j in range(max(0, len(result)-10), len(result)))
                if in_isis:
                    # Generate ISIS interface entries for target's WAN interfaces
                    wan_isis_config = self._generate_wan_isis_interfaces(wan_ifaces)
                    if wan_isis_config:
                        result.append(wan_isis_config)
                    isis_inserted = True
            
            # Insert WAN interfaces into OSPF (from source)
            elif stripped.startswith('ospf') and indent == 2 and not ospf_inserted:
                # Generate OSPF interface entries for target's WAN interfaces
                wan_ospf_config = self._generate_wan_ospf_interfaces(wan_ifaces)
                if wan_ospf_config:
                    result.append(wan_ospf_config)
                ospf_inserted = True
            
            # Insert WAN interfaces into LDP (from source)
            elif stripped == 'ldp' and indent == 2 and not ldp_inserted:
                # Find where to insert (after address-family block)
                ldp_lines = []
                j = i + 1
                while j < len(lines):
                    ldp_line = lines[j]
                    ldp_stripped = ldp_line.strip()
                    ldp_indent = len(ldp_line) - len(ldp_line.lstrip())
                    
                    if ldp_indent <= 2 and ldp_stripped and ldp_stripped != '!':
                        break
                    ldp_lines.append(ldp_line)
                    j += 1
                
                # Add ldp lines then our WAN interfaces before the closing !
                for ll in ldp_lines[:-1]:  # All but last (which is closing !)
                    result.append(ll)
                
                # Generate LDP interface entries for target's WAN interfaces
                wan_ldp_config = self._generate_wan_ldp_interfaces(wan_ifaces)
                if wan_ldp_config:
                    result.append(wan_ldp_config)
                
                if ldp_lines:
                    result.append(ldp_lines[-1])  # Add closing !
                i = j - 1  # Skip the lines we already added
                ldp_inserted = True
            
            i += 1
        
        return '\n'.join(result)
    
    def _generate_wan_isis_interfaces(self, wan_ifaces: set) -> str:
        """Generate ISIS interface config for WAN interfaces.
        
        ISIS structure (DNOS):
          isis                      (2-space)
            instance IGP            (4-space)
              interface lo0         (6-space)
                admin-state enabled (8-space)
              !                     (6-space)
        """
        lines = []
        for iface in sorted(wan_ifaces):
            # Only add sub-interfaces (with .) for ISIS
            if '.' in iface:
                lines.extend([
                    f'      interface {iface}',         # 6-space (inside instance)
                    '        admin-state enabled',      # 8-space
                    '        network-type point-to-point',
                    '        address-family ipv4-unicast',
                    '        !',
                    '      !',                          # 6-space
                ])
        return '\n'.join(lines)
    
    def _generate_wan_ospf_interfaces(self, wan_ifaces: set) -> str:
        """Generate OSPF interface config for WAN interfaces.
        
        OSPF structure under area:
          ospf 1                    (2-space)
            area 0                  (4-space)
              interface lo0         (6-space)
        """
        lines = []
        for iface in sorted(wan_ifaces):
            if '.' in iface:
                lines.extend([
                    f'      interface {iface}',     # 6-space (under area)
                    '        admin-state enabled',  # 8-space
                    '        network-type point-to-point',
                    '      !',
                ])
        return '\n'.join(lines)
    
    def _generate_wan_ldp_interfaces(self, wan_ifaces: set) -> str:
        """Generate LDP interface config for WAN interfaces.
        
        LDP structure:
          ldp                       (2-space)
            router-id X.X.X.X       (4-space)
            address-family ipv4     (4-space)
              interface lo0         (6-space)
              !                     (6-space)
        """
        lines = []
        for iface in sorted(wan_ifaces):
            if '.' in iface:
                lines.extend([
                    f'      interface {iface}',     # 6-space (under address-family)
                    '      !',
                ])
        return '\n'.join(lines)
    
    def _ensure_section_format(self, section: str, section_name: str) -> str:
        """Ensure a section has proper DNOS format with header and closing !"""
        lines = section.strip().split('\n')
        
        # Check if section header exists
        if not lines or lines[0].strip() != section_name:
            lines.insert(0, section_name)
        
        # Ensure closing ! at indent 0
        if not lines[-1].strip() == '!':
            lines.append('!')
        elif lines[-1] != '!':  # Has indent
            lines[-1] = '!'
        
        return '\n'.join(lines)
    
    def _cleanup_dnos_syntax(self, config: str) -> str:
        """Clean up and validate DNOS syntax. Delegates to standalone function."""
        return cleanup_dnos_config_syntax(config)
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _get_all_interface_blocks(self, config: str, wanted_interfaces: set) -> Dict[str, str]:
        """
        Extract all interface blocks in a single pass (O(n) instead of O(n*m)).
        
        Args:
            config: Full configuration text
            wanted_interfaces: Set of interface names to extract
            
        Returns:
            Dict mapping interface name to its config block
        """
        lines = config.split('\n')
        result = {}
        current_interface = None
        current_block = []
        in_interfaces_section = False
        
        for line in lines:
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            if stripped == 'interfaces':
                in_interfaces_section = True
                continue
            
            if in_interfaces_section and indent == 0 and stripped and stripped != '!':
                # End of interfaces section
                if current_interface and current_block:
                    result[current_interface] = '\n'.join(current_block)
                in_interfaces_section = False
                continue
            
            if in_interfaces_section:
                # Check for interface definition at 2-space indent
                if indent == 2 and stripped and not stripped.startswith('!'):
                    # Save previous interface block
                    if current_interface and current_block:
                        result[current_interface] = '\n'.join(current_block)
                    
                    # Start new interface if it's one we want
                    if stripped in wanted_interfaces:
                        current_interface = stripped
                        current_block = [line]
                    else:
                        current_interface = None
                        current_block = []
                    continue
                
                # Add line to current block if we're tracking an interface
                if current_interface:
                    current_block.append(line)
                    # Check for block end
                    if stripped == '!' and indent == 2:
                        result[current_interface] = '\n'.join(current_block)
                        current_interface = None
                        current_block = []
        
        # Handle last interface
        if current_interface and current_block:
            result[current_interface] = '\n'.join(current_block)
        
        return result
    
    def _get_interface_block(self, config: str, iface_name: str) -> str:
        """Get the configuration block for a specific interface."""
        blocks = self._get_all_interface_blocks(config, {iface_name})
        return blocks.get(iface_name, '')
    
    def _get_all_interfaces(self, config: str) -> List[str]:
        """Get all interface names from config."""
        interfaces = []
        lines = config.split('\n')
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
            
            if in_interfaces and indent == 2 and stripped and stripped != '!':
                interfaces.append(stripped)
        
        return interfaces
    
    def _remove_protocol_subsection(self, protocols: str, subsection: str) -> str:
        """Remove a subsection from protocols block."""
        lines = protocols.split('\n')
        result = []
        skip_until_close = False
        skip_indent = 0
        
        for line in lines:
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            
            if stripped == subsection:
                skip_until_close = True
                skip_indent = indent
                continue
            
            if skip_until_close:
                if stripped == '!' and indent == skip_indent:
                    skip_until_close = False
                continue
            
            result.append(line)
        
        return '\n'.join(result)
    
    def _get_section_content(self, section: str) -> str:
        """Get content of a section without header and closing !."""
        lines = section.split('\n')
        if len(lines) < 2:
            return ''
        
        # Skip first line (header) and last line (closing !)
        content_lines = []
        for line in lines[1:]:
            if line.strip() == '!' and len(line) - len(line.lstrip()) == 0:
                continue
            content_lines.append(line)
        
        return '\n'.join(content_lines)


# =============================================================================
# WIZARD FUNCTIONS
# =============================================================================

def show_mirror_detailed_summary(mirror: ConfigMirror, merged_config: str, source_hostname: str, target_hostname: str) -> None:
    """
    Show a detailed summary of what will be mirrored.
    
    Args:
        mirror: ConfigMirror instance with parsed data
        merged_config: The generated merged configuration
        source_hostname: Source device hostname
        target_hostname: Target device hostname
    """
    from rich.table import Table
    import re
    
    # Extract section statistics
    target_unique = mirror.extract_target_unique()
    source_mirrored = mirror.extract_source_mirrored()
    
    # Count elements in each section
    def count_lines(text: str) -> int:
        return len([l for l in text.split('\n') if l.strip() and l.strip() != '!']) if text else 0
    
    console.print(f"\n[bold cyan]{'═' * 80}[/bold cyan]")
    console.print(f"[bold cyan]              📋 Mirror Configuration Summary                    [/bold cyan]")
    console.print(f"[bold cyan]{'═' * 80}[/bold cyan]")
    
    # Create summary table
    table = Table(box=box.ROUNDED, show_header=True)
    table.add_column("Section", style="cyan", width=25)
    table.add_column("Source", justify="center", width=15)
    table.add_column("Action", justify="center", width=20)
    table.add_column("Lines", justify="right", width=10)
    
    # Preserved from target (green)
    table.add_row(
        "[bold]PRESERVED FROM TARGET[/bold]",
        f"[dim]{target_hostname}[/dim]",
        "[green]Keep[/green]",
        ""
    )
    
    system_lines = count_lines(target_unique.get('system', ''))
    if system_lines:
        # Check if system was copied from source (for minimal target configs)
        if hasattr(mirror, 'system_copied_from_source') and mirror.system_copied_from_source:
            table.add_row("  System Config", f"[dim]{source_hostname}[/dim]", "[cyan]→ Hostname transformed[/cyan]", str(system_lines))
        else:
            table.add_row("  System Config", "", "[green]✓ Preserved[/green]", str(system_lines))
    
    lo0_lines = count_lines(target_unique.get('lo0', ''))
    if lo0_lines:
        table.add_row("  Loopback (Lo0)", "", "[green]✓ Preserved[/green]", str(lo0_lines))
    elif hasattr(mirror, 'user_entered_lo0') and mirror.user_entered_lo0:
        # Lo0 was created from user input
        table.add_row("  Loopback (Lo0)", f"[magenta]USER INPUT[/magenta]", f"[magenta]+ {mirror.user_entered_lo0}[/magenta]", "3")
    
    wan_lines = count_lines(target_unique.get('wan_interfaces', ''))
    if wan_lines:
        table.add_row("  WAN Interfaces", "", "[green]✓ Preserved[/green]", str(wan_lines))
    
    bundle_lines = count_lines(target_unique.get('bundles', ''))
    if bundle_lines:
        table.add_row("  Bundle Interfaces", "", "[green]✓ Preserved[/green]", str(bundle_lines))
    
    lacp_lines = count_lines(target_unique.get('lacp', ''))
    if lacp_lines:
        table.add_row("  LACP Config", "", "[green]✓ Preserved[/green]", str(lacp_lines))
    
    lldp_lines = count_lines(target_unique.get('lldp', ''))
    if lldp_lines:
        table.add_row("  LLDP Config", "", "[green]✓ Preserved[/green]", str(lldp_lines))
    
    # Separator
    table.add_row("", "", "", "")
    
    # Mirrored from source (cyan)
    table.add_row(
        "[bold]MIRRORED FROM SOURCE[/bold]",
        f"[dim]{source_hostname}[/dim]",
        "[cyan]Copy + Transform[/cyan]",
        ""
    )
    
    # System section (if mirrored)
    system_lines = count_lines(source_mirrored.get('system', ''))
    if system_lines and hasattr(mirror, 'system_copied_from_source') and mirror.system_copied_from_source:
        table.add_row("  System Config", "", f"[cyan]→ Hostname: {target_hostname}[/cyan]", str(system_lines))
        # Show what was preserved for uniqueness
        if hasattr(mirror, '_target_unique_system_settings') and mirror._target_unique_system_settings:
            unique_items = ', '.join(mirror._target_unique_system_settings)
            table.add_row("    └─ Preserved", "", f"[dim]{unique_items}[/dim]", "")
    
    services_lines = count_lines(source_mirrored.get('services', ''))
    if services_lines:
        # Count specific service types
        services_text = source_mirrored.get('services', '')
        fxc_count = services_text.count('evpn-vpws-fxc') + len(re.findall(r'instance\s+FXC', services_text))
        table.add_row("  Network Services", "", f"[cyan]→ RD transformed[/cyan]", str(services_lines))
        if fxc_count:
            table.add_row("    └─ FXC Services", "", f"[dim]{fxc_count} instances[/dim]", "")
    
    svc_ifaces_lines = count_lines(source_mirrored.get('service_interfaces', ''))
    if svc_ifaces_lines:
        table.add_row("  Service Interfaces", "", "[cyan]→ Mapped[/cyan]", str(svc_ifaces_lines))
    
    policy_lines = count_lines(source_mirrored.get('routing_policy', ''))
    if policy_lines:
        table.add_row("  Routing Policy", "", "[cyan]→ Copied[/cyan]", str(policy_lines))
    
    acls_lines = count_lines(source_mirrored.get('acls', ''))
    if acls_lines:
        table.add_row("  ACLs", "", "[cyan]→ Copied[/cyan]", str(acls_lines))
    
    qos_lines = count_lines(source_mirrored.get('qos', ''))
    if qos_lines:
        table.add_row("  QoS", "", "[cyan]→ Copied[/cyan]", str(qos_lines))
    
    mh_lines = count_lines(source_mirrored.get('multihoming', ''))
    if mh_lines:
        table.add_row("  Multihoming", "", "[cyan]→ ESIs copied[/cyan]", str(mh_lines))
    
    # Check if user entered any infrastructure values
    user_infra_added = False
    if hasattr(mirror, 'user_entered_asn') and mirror.user_entered_asn:
        if not user_infra_added:
            table.add_row("", "", "", "")
            table.add_row(
                "[bold]GENERATED FROM USER INPUT[/bold]",
                "[magenta]New[/magenta]",
                "[magenta]+ Created[/magenta]",
                ""
            )
            user_infra_added = True
        table.add_row("  BGP ASN", "", f"[magenta]+ {mirror.user_entered_asn}[/magenta]", "")
    
    if hasattr(mirror, 'user_entered_rid') and mirror.user_entered_rid:
        if not user_infra_added:
            table.add_row("", "", "", "")
            table.add_row(
                "[bold]GENERATED FROM USER INPUT[/bold]",
                "[magenta]New[/magenta]",
                "[magenta]+ Created[/magenta]",
                ""
            )
            user_infra_added = True
        table.add_row("  Router-ID", "", f"[magenta]+ {mirror.user_entered_rid}[/magenta]", "")
    
    # Separator and total
    table.add_row("", "", "", "")
    total_lines = len([l for l in merged_config.split('\n') if l.strip()])
    table.add_row("[bold]TOTAL[/bold]", "", "", f"[bold]{total_lines:,}[/bold]")
    
    console.print(table)
    
    # Show key transformations
    console.print(f"\n[bold yellow]Key Transformations Applied:[/bold yellow]")
    
    # System section transformations
    if hasattr(mirror, 'system_copied_from_source') and mirror.system_copied_from_source:
        console.print(f"  • System Config: [dim]{source_hostname}[/dim] → [green]{target_hostname}[/green] (hostname changed)")
        if hasattr(mirror, '_target_unique_system_settings') and mirror._target_unique_system_settings:
            console.print(f"  • System Uniqueness: [green]Preserved[/green] ({', '.join(mirror._target_unique_system_settings)})")
    
    if mirror.source_lo0 and mirror.target_lo0:
        src_ip = mirror.source_lo0.split('/')[0] if mirror.source_lo0 else 'N/A'
        tgt_ip = mirror.target_lo0.split('/')[0] if mirror.target_lo0 else 'N/A'
        console.print(f"  • Route Distinguisher: [dim]{src_ip}:N[/dim] → [green]{tgt_ip}:N[/green]")
    console.print(f"  • Route Targets: [green]Preserved[/green] (same for EVPN peering)")
    if mirror.interface_map:
        console.print(f"  • Interface Mapping: [dim]{len(mirror.interface_map)} interfaces mapped[/dim]")


def _view_section_content(content: str, custom: str, hierarchy: str, desc: str):
    """Display section content with custom additions highlighted."""
    console.print(f"\n[bold]Current Configuration:[/bold]")
    
    if not content and not custom.strip():
        console.print("[dim]  (empty)[/dim]")
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
        return
    
    # Show original content
    orig_lines = content.split('\n') if content else []
    custom_lines = [l for l in custom.split('\n') if l.strip()] if custom.strip() else []
    
    # Display first 40 lines of original
    console.print(f"\n[dim]Original ({len(orig_lines)} lines):[/dim]")
    for i, line in enumerate(orig_lines[:40]):
        console.print(f"  {line}")
    if len(orig_lines) > 40:
        console.print(f"  [dim]... ({len(orig_lines) - 40} more lines)[/dim]")
    
    # Display custom if any
    if custom_lines:
        console.print(f"\n[green]Custom additions ({len(custom_lines)} lines):[/green]")
        for i, line in enumerate(custom_lines[:20]):
            console.print(f"  [green]{line}[/green]")
        if len(custom_lines) > 20:
            console.print(f"  [dim]... ({len(custom_lines) - 20} more lines)[/dim]")
    
    console.print()
    Prompt.ask("[dim]Press Enter to continue[/dim]", default="")


def _parse_range_spec(spec: str, max_val: int = None) -> List[int]:
    """
    Parse a range specification like "1-100", "1,5,10", "1-50,75-100", "all".
    
    Examples:
        "1-100" → [1, 2, 3, ..., 100]
        "1,5,10" → [1, 5, 10]
        "1-10,20-30" → [1, 2, ..., 10, 20, 21, ..., 30]
        "all" → [1, 2, ..., max_val]
    """
    spec = spec.strip().lower()
    
    if spec == 'all' and max_val:
        return list(range(1, max_val + 1))
    
    result = []
    parts = spec.replace(' ', '').split(',')
    
    for part in parts:
        if '-' in part and not part.startswith('-'):
            # Range like "1-100"
            try:
                start, end = part.split('-', 1)
                start, end = int(start), int(end)
                result.extend(range(start, end + 1))
            except ValueError:
                continue
        else:
            # Single number
            try:
                result.append(int(part))
            except ValueError:
                continue
    
    return sorted(set(result))


def _wizard_modify_df_preference(mirror: 'ConfigMirror', content: str, existing_custom: str) -> Optional[str]:
    """Wizard to modify DF preferences in existing multihoming config with smart detection."""
    import re
    
    console.print("\n[bold cyan]═══ Modify DF Preference ═══[/bold cyan]")
    console.print("[dim]Smart detection and bulk modification[/dim]\n")
    
    # Smart detection: Parse all interfaces and their current values
    interface_values = {}  # {interface_name: current_value}
    current_iface = None
    
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped.startswith('interface '):
            current_iface = stripped.split()[1] if len(stripped.split()) > 1 else None
        elif current_iface and 'algorithm highest-preference value' in stripped:
            match = re.search(r'value\s+(\d+)', stripped)
            if match:
                interface_values[current_iface] = int(match.group(1))
            current_iface = None
    
    if not interface_values:
        console.print("[yellow]No interfaces with DF preference found[/yellow]")
        return None
    
    # Analyze current state
    value_counts = {}
    for iface, val in interface_values.items():
        if val not in value_counts:
            value_counts[val] = []
        value_counts[val].append(iface)
    
    # Show smart detection results
    console.print("[bold]📊 Current Configuration Detected:[/bold]")
    console.print(f"  Total interfaces with DF preference: {len(interface_values)}")
    console.print()
    
    for val, ifaces in sorted(value_counts.items()):
        # Try to detect range pattern
        nums = []
        prefix = None
        suffix = None
        for iface in ifaces:
            match = re.match(r'([a-zA-Z]+)(\d+)(\.?\d*)', iface)
            if match:
                if prefix is None:
                    prefix = match.group(1)
                    suffix = match.group(3)
                nums.append(int(match.group(2)))
        
        if nums:
            nums.sort()
            # Detect continuous ranges
            ranges = []
            start = nums[0]
            prev = nums[0]
            for n in nums[1:]:
                if n != prev + 1:
                    ranges.append(f"{start}-{prev}" if start != prev else str(start))
                    start = n
                prev = n
            ranges.append(f"{start}-{prev}" if start != prev else str(start))
            range_str = ','.join(ranges[:3])
            if len(ranges) > 3:
                range_str += f"... ({len(ranges)} ranges)"
            
            console.print(f"  [yellow]value {val}[/yellow]: {len(ifaces)} interfaces")
            console.print(f"    [dim]{prefix}{range_str}{suffix}[/dim]")
        else:
            console.print(f"  [yellow]value {val}[/yellow]: {len(ifaces)} interfaces")
    
    console.print()
    
    # Offer smart options
    console.print("[bold]Options:[/bold]")
    console.print("  [1] Change ALL interfaces to new value")
    console.print("  [2] Change specific value → new value (e.g., 100 → 50)")
    console.print("  [3] Change specific range (e.g., ph1-1000.1)")
    console.print("  [B] Cancel")
    
    choice = Prompt.ask("Select", choices=["1", "2", "3", "b", "B"], default="1")
    
    if choice.lower() == 'b':
        return None
    
    interfaces_to_modify = []
    
    if choice == "1":
        # Change all
        interfaces_to_modify = list(interface_values.keys())
        console.print(f"[cyan]Will modify all {len(interfaces_to_modify)} interfaces[/cyan]")
        
    elif choice == "2":
        # Change specific value
        console.print("\n[bold]Select current value to change:[/bold]")
        for i, val in enumerate(sorted(value_counts.keys()), 1):
            console.print(f"  [{i}] value {val} ({len(value_counts[val])} interfaces)")
        
        val_choice = Prompt.ask("Select value to change", default="1")
        try:
            val_idx = int(val_choice) - 1
            old_val = sorted(value_counts.keys())[val_idx]
            interfaces_to_modify = value_counts[old_val]
            console.print(f"[cyan]Will modify {len(interfaces_to_modify)} interfaces with value {old_val}[/cyan]")
        except (ValueError, IndexError):
            console.print("[red]Invalid selection[/red]")
            return None
            
    elif choice == "3":
        # Change specific range
        console.print("\n[bold]Specify interface range:[/bold]")
        console.print("[dim]Examples: 1-100, 1-50,75-100, 1,5,10,20, all[/dim]")
        
        # Detect prefix/suffix from existing interfaces
        sample_iface = list(interface_values.keys())[0]
        match = re.match(r'([a-zA-Z]+)(\d+)(\.?\d*)', sample_iface)
        if match:
            detected_prefix = match.group(1)
            detected_suffix = match.group(3)
            console.print(f"[dim]Detected pattern: {detected_prefix}<num>{detected_suffix}[/dim]")
        else:
            detected_prefix = "ph"
            detected_suffix = ".1"
        
        prefix = str_prompt_nav("Interface prefix", default=detected_prefix)
        range_spec = str_prompt_nav("Number range (e.g., 1-100 or 1,5,10)", default="1-100")
        suffix = str_prompt_nav("Sub-interface suffix", default=detected_suffix)
        
        # Parse range
        max_num = max(int(re.search(r'\d+', i).group()) for i in interface_values.keys() if re.search(r'\d+', i))
        nums = _parse_range_spec(range_spec, max_num)
        
        for num in nums:
            iface_name = f"{prefix}{num}{suffix}"
            if iface_name in interface_values:
                interfaces_to_modify.append(iface_name)
        
        console.print(f"[cyan]Found {len(interfaces_to_modify)} matching interfaces to modify[/cyan]")
        
        if not interfaces_to_modify:
            console.print("[yellow]No matching interfaces found[/yellow]")
            return None
    
    # Get new value
    console.print("\n[bold]New DF preference value:[/bold]")
    
    # Smart suggestion based on current values
    current_vals = set(interface_values[i] for i in interfaces_to_modify)
    if len(current_vals) == 1:
        current = list(current_vals)[0]
        suggested = 50 if current == 100 else 100
        console.print(f"[dim]Current value: {current}, suggested: {suggested}[/dim]")
    else:
        suggested = 50
    
    new_value = int(Prompt.ask("New value", default=str(suggested)))
    
    # Generate FLAT commands (1 line per interface) - MUCH faster than hierarchical!
    # Format: network-services multihoming interface <name> designated-forwarder algorithm highest-preference value <val>
    lines = []
    for iface in sorted(interfaces_to_modify, key=lambda x: (x.split('.')[0], int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)):
        lines.append(f'network-services multihoming interface {iface} designated-forwarder algorithm highest-preference value {new_value}')
    
    # Summary
    console.print(f"\n[bold green]Summary:[/bold green]")
    console.print(f"  Interfaces: {len(interfaces_to_modify)}")
    console.print(f"  New value:  {new_value}")
    console.print(f"  [dim]Using flat commands ({len(lines)} lines vs {len(interfaces_to_modify) * 5 + 2} hierarchical)[/dim]")
    
    if Confirm.ask("\nApply these changes?", default=True):
        return '\n'.join(lines)
    return None


def _wizard_add_section_config(
    section_key: str,
    section_info: dict,
    mirror: 'ConfigMirror',
    target_hostname: str
) -> Optional[str]:
    """
    Wizard-style interface for adding custom config to a section.
    Returns the generated config text or None if cancelled.
    """
    from rich.panel import Panel
    
    console.print(f"\n[bold cyan]═══ Add to {section_info['desc']} ═══[/bold cyan]")
    console.print(f"[dim]Hierarchy: {section_info['hierarchy']}[/dim]\n")
    
    # Section-specific wizards
    if section_key == 'multihoming':
        return _wizard_multihoming(mirror, target_hostname)
    elif section_key == 'services':
        return _wizard_services(mirror, target_hostname)
    elif section_key == 'svc_ifaces':
        return _wizard_interfaces(mirror, target_hostname, is_service_iface=True)
    elif section_key in ['lo0', 'wan', 'bundles']:
        return _wizard_interfaces(mirror, target_hostname, is_service_iface=False)
    elif section_key == 'protocols':
        return _wizard_protocols(mirror, target_hostname)
    elif section_key == 'routing_policy':
        return _wizard_routing_policy(mirror, target_hostname)
    elif section_key == 'qos':
        return _wizard_qos(mirror, target_hostname)
    else:
        # Generic raw input for system, acls, lldp
        return _wizard_raw_input(section_info['desc'], section_info['hierarchy'])


def _wizard_multihoming(mirror: 'ConfigMirror', target_hostname: str) -> Optional[str]:
    """Wizard for adding multihoming configuration."""
    console.print("[bold]Multihoming Configuration Options:[/bold]")
    console.print("  [1] Add ESI to interface range (bulk)")
    console.print("  [2] Add single ESI to interface")
    console.print("  [3] Set DF preference for interfaces (bulk)")
    console.print("  [B] Cancel")
    
    choice = Prompt.ask("Select", choices=["1", "2", "3", "b", "B"], default="1")
    
    if choice.lower() == 'b':
        return None
    
    if choice == "1":
        # Bulk ESI addition
        console.print("\n[bold]Bulk ESI Addition[/bold]")
        console.print("[dim]Add ESI configuration to a range of interfaces[/dim]\n")
        
        # Interface pattern
        prefix = str_prompt_nav("Interface prefix", default="ph")
        start = int_prompt_nav("Start number", default=1)
        end = int_prompt_nav("End number", default=100)
        suffix = str_prompt_nav("Sub-interface suffix (e.g., .1)", default=".1")
        
        # ESI configuration
        console.print("\n[bold]ESI Configuration:[/bold]")
        esi_prefix = str_prompt_nav("ESI prefix (e.g., 00:00:01:00:00:00:00)", default="00:00:01:00:00:00:00")
        esi_start = int_prompt_nav("ESI starting number", default=1)
        redundancy = Prompt.ask("Redundancy mode", choices=["single-active", "all-active"], default="single-active")
        df_pref = int_prompt_nav("DF preference value", default=100)
        
        # Generate config
        lines = ["multihoming", f"  redundancy-mode {redundancy}"]
        for i, iface_num in enumerate(range(start, end + 1)):
            iface_name = f"{prefix}{iface_num}{suffix}"
            esi_num = esi_start + i
            esi_hex = format(esi_num, '02x')
            esi_value = f"{esi_prefix}:{esi_hex}"
            
            lines.append(f"  interface {iface_name}")
            lines.append(f"    esi arbitrary value {esi_value}")
            lines.append(f"    redundancy-mode {redundancy}")
            lines.append(f"    designated-forwarder")
            lines.append(f"      algorithm highest-preference value {df_pref}")
            lines.append(f"    !")
            lines.append(f"  !")
        lines.append("!")
        
        console.print(f"\n[green]✓ Generated ESI config for {end - start + 1} interfaces[/green]")
        return '\n'.join(lines)
    
    elif choice == "2":
        # Single ESI
        console.print("\n[bold]Single ESI Addition[/bold]")
        iface = Prompt.ask("Interface name (e.g., ph100.1)")
        esi_value = Prompt.ask("ESI value (e.g., 00:00:01:00:00:00:00:01:00)")
        redundancy = Prompt.ask("Redundancy mode", choices=["single-active", "all-active"], default="single-active")
        df_pref = int_prompt_nav("DF preference value", default=100)
        
        lines = [
            "multihoming",
            f"  redundancy-mode {redundancy}",
            f"  interface {iface}",
            f"    esi arbitrary value {esi_value}",
            f"    redundancy-mode {redundancy}",
            f"    designated-forwarder",
            f"      algorithm highest-preference value {df_pref}",
            f"    !",
            f"  !",
            "!"
        ]
        return '\n'.join(lines)
    
    elif choice == "3":
        # DF preference only
        console.print("\n[bold]Set DF Preference (Bulk)[/bold]")
        prefix = str_prompt_nav("Interface prefix", default="ph")
        start = int_prompt_nav("Start number", default=1)
        end = int_prompt_nav("End number", default=100)
        suffix = str_prompt_nav("Sub-interface suffix", default=".1")
        df_pref = int_prompt_nav("DF preference value", default=100)
        
        lines = ["multihoming"]
        for iface_num in range(start, end + 1):
            iface_name = f"{prefix}{iface_num}{suffix}"
            lines.append(f"  interface {iface_name}")
            lines.append(f"    designated-forwarder")
            lines.append(f"      algorithm highest-preference value {df_pref}")
            lines.append(f"    !")
            lines.append(f"  !")
        lines.append("!")
        
        console.print(f"\n[green]✓ Generated DF preference for {end - start + 1} interfaces[/green]")
        return '\n'.join(lines)
    
    return None


def _wizard_services(mirror: 'ConfigMirror', target_hostname: str) -> Optional[str]:
    """Wizard for adding network services configuration."""
    console.print("[bold]Network Services Options:[/bold]")
    console.print("  [1] Add FXC service range (bulk)")
    console.print("  [2] Add single FXC service")
    console.print("  [3] Add VPLS service")
    console.print("  [B] Cancel")
    
    choice = Prompt.ask("Select", choices=["1", "2", "3", "b", "B"], default="1")
    
    if choice.lower() == 'b':
        return None
    
    if choice == "1":
        # Bulk FXC
        console.print("\n[bold]Bulk FXC Service Addition[/bold]")
        prefix = str_prompt_nav("Service name prefix", default="FXC_")
        start = int_prompt_nav("Start number", default=1)
        end = int_prompt_nav("End number", default=100)
        
        # Get target loopback for RD
        target_lo = mirror.target_lo0.split('/')[0] if mirror.target_lo0 else "2.2.2.2"
        
        console.print("\n[bold]Service Configuration:[/bold]")
        evi_start = int_prompt_nav("Starting EVI", default=1000)
        rt_asn = int_prompt_nav("Route Target ASN", default=1234567)
        rt_start = int_prompt_nav("Starting RT number", default=1000)
        
        # Interface attachment?
        attach_ifaces = Confirm.ask("Attach interfaces to services?", default=True)
        if attach_ifaces:
            iface_prefix = str_prompt_nav("Interface prefix", default="ph")
            iface_suffix = str_prompt_nav("Interface suffix", default=".1")
        
        lines = ["network-services", "  evpn-vpws-fxc"]
        for i, svc_num in enumerate(range(start, end + 1)):
            svc_name = f"{prefix}{svc_num}"
            evi = evi_start + i
            rt_num = rt_start + i
            rd = f"{target_lo}:{evi}"
            
            lines.append(f"    instance {svc_name}")
            lines.append(f"      route-distinguisher {rd}")
            lines.append(f"      route-target {rt_asn}:{rt_num}")
            lines.append(f"      evi {evi}")
            
            if attach_ifaces:
                iface_name = f"{iface_prefix}{svc_num}{iface_suffix}"
                lines.append(f"      interface {iface_name}")
                lines.append(f"        local-ac-id {svc_num}")
                lines.append(f"      !")
            
            lines.append(f"    !")
        lines.append("  !")
        lines.append("!")
        
        console.print(f"\n[green]✓ Generated {end - start + 1} FXC services[/green]")
        return '\n'.join(lines)
    
    elif choice == "2":
        # Single FXC
        console.print("\n[bold]Single FXC Service[/bold]")
        svc_name = str_prompt_nav("Service name", default="FXC_CUSTOM")
        target_lo = mirror.target_lo0.split('/')[0] if mirror.target_lo0 else "2.2.2.2"
        evi = int_prompt_nav("EVI", default=9999)
        rd = str_prompt_nav("Route Distinguisher", default=f"{target_lo}:{evi}")
        rt = str_prompt_nav("Route Target (ASN:num)", default="1234567:9999")
        iface = str_prompt_nav("Interface (leave empty to skip)", default="", allow_empty=True)
        
        lines = [
            "network-services",
            "  evpn-vpws-fxc",
            f"    instance {svc_name}",
            f"      route-distinguisher {rd}",
            f"      route-target {rt}",
            f"      evi {evi}",
        ]
        
        if iface:
            lines.extend([
                f"      interface {iface}",
                f"        local-ac-id 1",
                f"      !"
            ])
        
        lines.extend(["    !", "  !", "!"])
        return '\n'.join(lines)
    
    return None


def _wizard_interfaces(mirror: 'ConfigMirror', target_hostname: str, is_service_iface: bool = True) -> Optional[str]:
    """Wizard for adding interface configuration."""
    console.print("[bold]Interface Configuration Options:[/bold]")
    console.print("  [1] Add PWHE interface range (bulk)")
    console.print("  [2] Add single interface")
    console.print("  [3] Add L2-AC sub-interfaces")
    console.print("  [B] Cancel")
    
    choice = Prompt.ask("Select", choices=["1", "2", "3", "b", "B"], default="1")
    
    if choice.lower() == 'b':
        return None
    
    if choice == "1":
        # Bulk PWHE
        console.print("\n[bold]Bulk PWHE Interface Addition[/bold]")
        prefix = str_prompt_nav("Interface prefix", default="ph")
        start = int_prompt_nav("Start number", default=1)
        end = int_prompt_nav("End number", default=100)
        
        console.print("\n[bold]Sub-interface Configuration:[/bold]")
        add_subif = Confirm.ask("Add sub-interfaces (.1)?", default=True)
        l2_service = Confirm.ask("Enable l2-service on sub-ifs?", default=True) if add_subif else False
        add_vlan = Confirm.ask("Add VLAN tags?", default=True) if add_subif else False
        
        lines = ["interfaces"]
        for iface_num in range(start, end + 1):
            parent_name = f"{prefix}{iface_num}"
            lines.append(f"  {parent_name}")
            lines.append(f"    admin-state enabled")
            lines.append(f"  !")
            
            if add_subif:
                subif_name = f"{parent_name}.1"
                lines.append(f"  {subif_name}")
                lines.append(f"    admin-state enabled")
                if l2_service:
                    lines.append(f"    l2-service enabled")
                if add_vlan:
                    lines.append(f"    vlan-tags outer-tag {iface_num} inner-tag 1 outer-tpid 0x8100")
                lines.append(f"  !")
        lines.append("!")
        
        count = (end - start + 1) * (2 if add_subif else 1)
        console.print(f"\n[green]✓ Generated {count} interfaces[/green]")
        return '\n'.join(lines)
    
    elif choice == "2":
        # Single interface
        console.print("\n[bold]Single Interface Addition[/bold]")
        iface_name = Prompt.ask("Interface name (e.g., ph100 or ph100.1)")
        l2_service = Confirm.ask("Enable l2-service?", default=True) if '.' in iface_name else False
        
        lines = [
            "interfaces",
            f"  {iface_name}",
            f"    admin-state enabled",
        ]
        if l2_service:
            lines.append(f"    l2-service enabled")
        lines.extend(["  !", "!"])
        return '\n'.join(lines)
    
    elif choice == "3":
        # L2-AC sub-interfaces
        console.print("\n[bold]L2-AC Sub-interface Addition[/bold]")
        parent = Prompt.ask("Parent interface (e.g., ge400-0/0/4)")
        start_vlan = int_prompt_nav("Start VLAN", default=1)
        end_vlan = int_prompt_nav("End VLAN", default=100)
        
        lines = ["interfaces"]
        for vlan in range(start_vlan, end_vlan + 1):
            subif_name = f"{parent}.{vlan}"
            lines.append(f"  {subif_name}")
            lines.append(f"    admin-state enabled")
            lines.append(f"    l2-service enabled")
            lines.append(f"    vlan-id {vlan}")
            lines.append(f"  !")
        lines.append("!")
        
        console.print(f"\n[green]✓ Generated {end_vlan - start_vlan + 1} sub-interfaces[/green]")
        return '\n'.join(lines)
    
    return None


def _wizard_protocols(mirror: 'ConfigMirror', target_hostname: str) -> Optional[str]:
    """Wizard for protocols configuration."""
    console.print("[bold]Protocol Configuration Options:[/bold]")
    console.print("  [1] Add BGP neighbor")
    console.print("  [2] Add ISIS interface")
    console.print("  [3] Raw config entry")
    console.print("  [B] Cancel")
    
    choice = Prompt.ask("Select", choices=["1", "2", "3", "b", "B"], default="3")
    
    if choice.lower() == 'b':
        return None
    
    if choice == "1":
        # BGP neighbor
        console.print("\n[bold]Add BGP Neighbor[/bold]")
        neighbor_ip = Prompt.ask("Neighbor IP address")
        remote_as = int_prompt_nav("Remote AS", default=1234567)
        update_source = Prompt.ask("Update source interface", default="lo0")
        
        lines = [
            "protocols",
            "  bgp",
            f"    neighbor {neighbor_ip}",
            f"      remote-as {remote_as}",
            f"      update-source {update_source}",
            "      address-family",
            "        l2vpn-evpn",
            "          send-community both",
            "        !",
            "      !",
            "    !",
            "  !",
            "!"
        ]
        return '\n'.join(lines)
    
    elif choice == "2":
        # ISIS interface - show available WAN/bundle interfaces
        console.print("\n[bold]Add ISIS Interface[/bold]")
        
        # Try to detect available WAN/bundle interfaces from target config
        available_ifaces = []
        if mirror and hasattr(mirror, 'target_config'):
            # Find WAN interfaces (ge/xe/bundle with IP addresses)
            iface_pattern = re.compile(r'^  ((?:ge|xe|bundle-ether)\d+(?:\.\d+)?)\s*$', re.MULTILINE)
            potential_ifaces = set(iface_pattern.findall(mirror.target_config))
            # Filter to those with ipv4-address (likely WAN/ISIS interfaces)
            for iface in potential_ifaces:
                iface_block_pattern = re.compile(rf'^  {re.escape(iface)}\s*$.*?^  !', re.MULTILINE | re.DOTALL)
                match = iface_block_pattern.search(mirror.target_config)
                if match and 'ipv4-address' in match.group(0):
                    available_ifaces.append(iface)
        
        if available_ifaces:
            console.print(f"  [dim]Available WAN interfaces: {', '.join(sorted(available_ifaces)[:5])}[/dim]")
            default_iface = sorted(available_ifaces)[0]
        else:
            default_iface = ""
        
        iface = Prompt.ask("Interface name", default=default_iface if default_iface else None)
        if not iface:
            console.print("[yellow]No interface specified, cancelling[/yellow]")
            return None
        
        level = Prompt.ask("ISIS level", choices=["1", "2", "1-2"], default="2")
        
        lines = [
            "protocols",
            "  isis 1",
            f"    interface {iface}",
            f"      point-to-point",
            f"      level {level} metric 10",
            "    !",
            "  !",
            "!"
        ]
        return '\n'.join(lines)
    
    elif choice == "3":
        return _wizard_raw_input("Protocols", "protocols")
    
    return None


def _wizard_routing_policy(mirror: 'ConfigMirror', target_hostname: str) -> Optional[str]:
    """Wizard for routing policy configuration."""
    console.print("[bold]Routing Policy Options:[/bold]")
    console.print("  [1] Add route-policy")
    console.print("  [2] Add prefix-set")
    console.print("  [3] Raw config entry")
    console.print("  [B] Cancel")
    
    choice = Prompt.ask("Select", choices=["1", "2", "3", "b", "B"], default="3")
    
    if choice.lower() == 'b':
        return None
    
    if choice == "3":
        return _wizard_raw_input("Routing Policy", "routing-policy")
    
    # TODO: Implement specific routing policy wizards
    console.print("[yellow]Using raw config entry...[/yellow]")
    return _wizard_raw_input("Routing Policy", "routing-policy")


def _wizard_qos(mirror: 'ConfigMirror', target_hostname: str) -> Optional[str]:
    """Wizard for QoS configuration."""
    console.print("[bold]QoS Configuration Options:[/bold]")
    console.print("  [1] Add QoS policy")
    console.print("  [2] Raw config entry")
    console.print("  [B] Cancel")
    
    choice = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="2")
    
    if choice.lower() == 'b':
        return None
    
    return _wizard_raw_input("QoS", "qos")


def _wizard_raw_input(section_name: str, hierarchy: str) -> Optional[str]:
    """Raw multi-line config input as fallback."""
    console.print(f"\n[bold]Enter {section_name} configuration:[/bold]")
    console.print(f"[dim]Enter DNOS config lines. Empty line to finish.[/dim]")
    console.print(f"[dim]Example: Start with '{hierarchy}' or just the content within it.[/dim]\n")
    
    lines = []
    while True:
        try:
            line = input("  ")
            if not line:
                break
            lines.append(line)
        except EOFError:
            break
    
    if lines:
        return '\n'.join(lines)
    return None


def _merge_custom_with_original(original: str, custom: str, hierarchy: str) -> str:
    """
    Merge custom configuration changes into the original config.
    
    For multihoming: Replace DF preference lines with custom values.
    For other hierarchies: Append custom config.
    
    Args:
        original: Original configuration text
        custom: Custom configuration modifications
        hierarchy: The hierarchy type (multihoming, services, etc.)
        
    Returns:
        Merged configuration text
    """
    if not custom.strip():
        return original
    
    if hierarchy == 'multihoming':
        # Parse custom config to find interface -> DF preference mappings
        custom_df_map = {}
        current_iface = None
        
        for line in custom.split('\n'):
            stripped = line.strip()
            if stripped.startswith('interface '):
                parts = stripped.split()
                if len(parts) >= 2:
                    current_iface = parts[1]
            elif current_iface and 'algorithm' in stripped and 'value' in stripped:
                # Extract DF preference value from custom
                # Format: algorithm highest-preference value <num>
                # Store just the stripped content - indentation will be preserved from original
                custom_df_map[current_iface] = stripped
            elif stripped == '!' and current_iface:
                current_iface = None
        
        if not custom_df_map:
            # No DF preference changes - just append custom
            return original + '\n' + custom
        
        # Replace matching lines in original
        result_lines = []
        current_iface = None
        replaced_ifaces = set()
        
        for line in original.split('\n'):
            stripped = line.strip()
            
            if stripped.startswith('interface '):
                parts = stripped.split()
                if len(parts) >= 2:
                    current_iface = parts[1]
                result_lines.append(line)
            elif current_iface and 'algorithm' in stripped and 'value' in stripped:
                # Check if this interface has a custom DF preference
                if current_iface in custom_df_map:
                    # Replace with custom value but preserve original indentation
                    indent = len(line) - len(line.lstrip())
                    result_lines.append(' ' * indent + custom_df_map[current_iface])
                    replaced_ifaces.add(current_iface)
                else:
                    result_lines.append(line)
            elif stripped == '!':
                current_iface = None
                result_lines.append(line)
            else:
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    else:
        # For other hierarchies, just append custom config
        return original + '\n' + custom


# =============================================================================
# GRANULAR HIERARCHICAL SECTION SELECTION (new implementation)
# =============================================================================

def analyze_source_config(mirror: 'ConfigMirror') -> Dict[str, Any]:
    """
    Analyze source configuration to extract detailed information about all hierarchies.
    
    Returns:
        Dict with detailed analysis of each hierarchy including counts and summaries
    """
    config = mirror.source_config
    
    # Parse all service types
    fxc_services = mirror.source_services.get('fxc', [])
    vpls_services = mirror.source_services.get('vpls', [])
    mpls_services = mirror.source_services.get('mpls', [])
    vrf_instances = parse_vrf_instances(config)
    vpws_instances = parse_evpn_vpws_instances(config)
    xconnects = parse_l2vpn_xconnect(config)
    bridge_domains = parse_l2vpn_bridge_domains(config)
    
    # Parse protocol details
    isis_config = parse_isis_config(config)
    ldp_config = parse_ldp_config(config)
    
    # Get interface categories
    wan_interfaces = get_wan_interfaces(config)
    service_interfaces = get_service_interfaces(config)
    cluster_interfaces = get_cluster_specific_interfaces(config)
    
    # Device type detection
    device_type = detect_device_type(config)
    ncp_slots = get_ncp_slots(config)
    
    # MH info
    mh_interfaces = mirror.source_mh if isinstance(mirror.source_mh, dict) else {}
    
    return {
        'device_type': device_type,
        'ncp_slots': ncp_slots,
        'hierarchies': {
            'system': {
                'exists': bool(extract_hierarchy_section(config, 'system')),
                'summary': f"hostname: {mirror.source_hostname}, NCPs: {ncp_slots}"
            },
            'interfaces': {
                'exists': bool(extract_hierarchy_section(config, 'interfaces')),
                'wan_count': len(wan_interfaces),
                'wan_interfaces': wan_interfaces,
                'service_count': len(service_interfaces.get('pwhe', [])) + len(service_interfaces.get('l2ac', [])),
                'pwhe_count': len(service_interfaces.get('pwhe', [])),
                'l2ac_count': len(service_interfaces.get('l2ac', [])),
                'cluster_count': len(cluster_interfaces),
                'cluster_interfaces': cluster_interfaces,
                'service_interfaces': service_interfaces,
                'summary': f"{len(wan_interfaces)} WAN, {len(service_interfaces.get('pwhe', []))} PWHE, {len(service_interfaces.get('l2ac', []))} L2-AC"
            },
            'network-services': {
                'exists': bool(extract_hierarchy_section(config, 'network-services')),
                'fxc': {'count': len(fxc_services), 'instances': fxc_services},
                'vpls': {'count': len(vpls_services), 'instances': vpls_services},
                'mpls': {'count': len(mpls_services), 'instances': mpls_services},
                'vrf': {'count': len(vrf_instances), 'instances': vrf_instances},
                'vpws': {'count': len(vpws_instances), 'instances': vpws_instances},
                'multihoming': {'count': len(mh_interfaces), 'interfaces': mh_interfaces},
                'summary': f"{len(fxc_services)} FXC, {len(vpls_services)} VPLS, {len(vrf_instances)} VRF, {len(mh_interfaces)} MH"
            },
            'l2vpn': {
                'exists': bool(extract_hierarchy_section(config, 'l2vpn')),
                'xconnect': {'count': len(xconnects), 'instances': xconnects},
                'bridge_domain': {'count': len(bridge_domains), 'instances': bridge_domains},
                'summary': f"{len(xconnects)} xconnect, {len(bridge_domains)} bridge-domain"
            },
            'protocols': {
                'exists': bool(extract_hierarchy_section(config, 'protocols')),
                'isis': isis_config,
                'ldp': ldp_config,
                'summary': f"ISIS: {len(isis_config.get('instances', []))} inst, LDP: {'yes' if ldp_config.get('transport_address') else 'no'}"
            },
            'routing': {
                'exists': bool(extract_hierarchy_section(config, 'routing')),
                'asn': mirror.source_asn,
                'summary': f"ASN: {mirror.source_asn or 'N/A'}"
            },
            'routing-policy': {
                'exists': bool(extract_hierarchy_section(config, 'routing-policy')),
                'summary': 'Route-maps, prefix-lists'
            },
            'qos': {
                'exists': bool(extract_hierarchy_section(config, 'qos')),
                'summary': 'Traffic policies, queues'
            },
            'access-lists': {
                'exists': bool(extract_hierarchy_section(config, 'access-lists')),
                'summary': 'ACL rules'
            }
        }
    }


def select_hierarchies_to_mirror(
    mirror: 'ConfigMirror',
    source_hostname: str,
    target_hostname: str,
    analysis: Dict[str, Any]
) -> Optional[Dict[str, bool]]:
    """
    Step 1: Select which top-level DNOS hierarchies to mirror.
    
    Args:
        mirror: ConfigMirror instance
        source_hostname: Source device hostname
        target_hostname: Target device hostname
        analysis: Pre-analyzed source config from analyze_source_config()
    
    Returns:
        Dict with hierarchy_name -> include (True/False), or None if cancelled
    """
    hierarchies = analysis['hierarchies']
    
    # Build hierarchy selection list
    hierarchy_list = []
    for name, info in hierarchies.items():
        if info.get('exists', False):
            hierarchy_list.append({
                'name': name,
                'summary': info.get('summary', ''),
                'include': True  # Default to include
            })
    
    if not hierarchy_list:
        console.print("[yellow]⚠ No hierarchies found in source device to mirror[/yellow]")
        return None
    
    console.print(f"\n[bold cyan]Step 1: Select DNOS Hierarchies to Mirror from {source_hostname}[/bold cyan]")
    console.print(f"[dim]Target device: {target_hostname}[/dim]\n")
    
    while True:
        # Display table
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=3)
        table.add_column("Hierarchy", width=20)
        table.add_column("Summary", width=40)
        table.add_column("Include", justify="center", width=10)
        
        for i, h in enumerate(hierarchy_list, 1):
            include_str = "[green]✓ Yes[/green]" if h['include'] else "[red]✗ No[/red]"
            table.add_row(str(i), h['name'], h['summary'], include_str)
        
        console.print(table)
        console.print()
        console.print("[dim]Commands: [1-N] Toggle, [D] Drill into sub-sections, [A] All, [N] None, [C] Continue, [B] Back[/dim]")
        
        choices = [str(i) for i in range(1, len(hierarchy_list) + 1)] + ['a', 'A', 'n', 'N', 'c', 'C', 'd', 'D', 'b', 'B']
        choice = Prompt.ask("Select", choices=choices, default='c').lower()
        
        if choice == 'b':
            return None
        
        if choice == 'c':
            selected = sum(1 for h in hierarchy_list if h['include'])
            if selected == 0:
                console.print("[red]✗ At least one hierarchy must be selected[/red]")
                continue
            break
        
        if choice == 'a':
            for h in hierarchy_list:
                h['include'] = True
            console.print("[green]✓ All hierarchies selected[/green]")
            continue
        
        if choice == 'n':
            for h in hierarchy_list:
                h['include'] = False
            console.print("[yellow]All hierarchies deselected[/yellow]")
            continue
        
        if choice == 'd':
            # Drill into sub-sections for selected hierarchies
            console.print("\n[cyan]Select a hierarchy number to drill into its sub-sections:[/cyan]")
            drill_choice = Prompt.ask(
                "Hierarchy #",
                choices=[str(i) for i in range(1, len(hierarchy_list) + 1)] + ['b', 'B'],
                default='b'
            ).lower()
            
            if drill_choice != 'b':
                idx = int(drill_choice) - 1
                if 0 <= idx < len(hierarchy_list):
                    h_name = hierarchy_list[idx]['name']
                    # Store the result of drilling for later use
                    if not hasattr(mirror, '_hierarchy_sub_selections'):
                        mirror._hierarchy_sub_selections = {}
                    
                    sub_result = select_sub_sections(mirror, h_name, analysis, source_hostname, target_hostname)
                    if sub_result:
                        mirror._hierarchy_sub_selections[h_name] = sub_result
                        console.print(f"[green]✓ Sub-sections configured for {h_name}[/green]")
            continue
        
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(hierarchy_list):
                hierarchy_list[idx]['include'] = not hierarchy_list[idx]['include']
                status = "included" if hierarchy_list[idx]['include'] else "excluded"
                console.print(f"[cyan]{hierarchy_list[idx]['name']}: {status}[/cyan]")
    
    return {h['name']: h['include'] for h in hierarchy_list}


def select_sub_sections(
    mirror: 'ConfigMirror',
    hierarchy: str,
    analysis: Dict[str, Any],
    source_hostname: str,
    target_hostname: str
) -> Optional[Dict[str, Any]]:
    """
    Step 2: Drill into a hierarchy and select specific sub-sections.
    
    Args:
        mirror: ConfigMirror instance
        hierarchy: Hierarchy name (e.g., 'network-services', 'protocols')
        analysis: Pre-analyzed source config
        source_hostname: Source device hostname
        target_hostname: Target device hostname
    
    Returns:
        Dict with sub-section selections, or None if cancelled
    """
    h_info = analysis['hierarchies'].get(hierarchy, {})
    
    if hierarchy == 'network-services':
        return _select_network_services_sub_sections(mirror, h_info, source_hostname, target_hostname)
    elif hierarchy == 'protocols':
        return _select_protocols_sub_sections(mirror, h_info, source_hostname, target_hostname)
    elif hierarchy == 'interfaces':
        return _select_interfaces_sub_sections(mirror, h_info, analysis, source_hostname, target_hostname)
    elif hierarchy == 'l2vpn':
        return _select_l2vpn_sub_sections(mirror, h_info, source_hostname, target_hostname)
    else:
        console.print(f"[yellow]No sub-sections available for {hierarchy}[/yellow]")
        return None


def _select_network_services_sub_sections(
    mirror: 'ConfigMirror',
    h_info: Dict,
    source_hostname: str,
    target_hostname: str
) -> Optional[Dict[str, Any]]:
    """Select network-services sub-sections (FXC, VPLS, VRF, MH, etc.)."""
    
    sub_sections = []
    
    # FXC
    fxc_info = h_info.get('fxc', {})
    if fxc_info.get('count', 0) > 0:
        sub_sections.append({
            'key': 'evpn-vpws-fxc',
            'name': 'evpn-vpws-fxc',
            'count': fxc_info['count'],
            'instances': fxc_info.get('instances', []),
            'include': True,
            'drillable': True
        })
    
    # VPLS
    vpls_info = h_info.get('vpls', {})
    if vpls_info.get('count', 0) > 0:
        sub_sections.append({
            'key': 'evpn-vpls',
            'name': 'evpn-vpls',
            'count': vpls_info['count'],
            'instances': vpls_info.get('instances', []),
            'include': True,
            'drillable': True
        })
    
    # VPWS (evpn-vpws)
    vpws_info = h_info.get('vpws', {})
    if vpws_info.get('count', 0) > 0:
        sub_sections.append({
            'key': 'evpn-vpws',
            'name': 'evpn-vpws',
            'count': vpws_info['count'],
            'instances': vpws_info.get('instances', []),
            'include': True,
            'drillable': True
        })
    
    # VRF
    vrf_info = h_info.get('vrf', {})
    if vrf_info.get('count', 0) > 0:
        sub_sections.append({
            'key': 'vrf',
            'name': 'vrf',
            'count': vrf_info['count'],
            'instances': vrf_info.get('instances', []),
            'include': True,
            'drillable': True
        })
    
    # Multihoming
    mh_info = h_info.get('multihoming', {})
    if mh_info.get('count', 0) > 0:
        sub_sections.append({
            'key': 'multihoming',
            'name': 'multihoming',
            'count': mh_info['count'],
            'instances': list(mh_info.get('interfaces', {}).keys()),
            'include': True,
            'drillable': True
        })
    
    if not sub_sections:
        console.print("[yellow]No network-services sub-sections with content found[/yellow]")
        return None
    
    console.print(f"\n[bold cyan]network-services Sub-sections on {source_hostname}[/bold cyan]")
    console.print(f"[dim]Target device: {target_hostname}[/dim]\n")
    
    while True:
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=3)
        table.add_column("Sub-section", width=20)
        table.add_column("Instances", width=40)
        table.add_column("Include", justify="center", width=10)
        
        for i, ss in enumerate(sub_sections, 1):
            include_str = "[green]✓ Yes[/green]" if ss['include'] else "[red]✗ No[/red]"
            
            # Build instance summary
            if ss['key'] == 'vrf':
                # Show VRF details
                inst_summary = f"{ss['count']} instances"
                for inst in ss['instances'][:2]:
                    if isinstance(inst, dict):
                        iface_count = len(inst.get('interfaces', []))
                        fs_info = "flowspec" if inst.get('flowspec', {}).get('ipv4') else ""
                        inst_summary += f"\n  → {inst['name']}: {iface_count} iface" + (f", {fs_info}" if fs_info else "")
                if ss['count'] > 2:
                    inst_summary += f"\n  → ... ({ss['count'] - 2} more)"
            elif ss['key'] == 'multihoming':
                inst_summary = f"{ss['count']} ESI interfaces"
            else:
                inst_summary = f"{ss['count']} instances"
            
            table.add_row(str(i), ss['name'], inst_summary, include_str)
        
        console.print(table)
        console.print()
        console.print("[dim]Commands: [1-N] Toggle include/exclude, [D] Drill into instances, [A] All, [X] None, [C] Continue, [B] Back[/dim]")
        
        choices = [str(i) for i in range(1, len(sub_sections) + 1)]
        choices += ['a', 'A', 'x', 'X', 'c', 'C', 'd', 'D', 'b', 'B']
        
        choice = Prompt.ask("Select", choices=choices, default='c').lower()
        
        if choice == 'b':
            return None
        
        if choice == 'c':
            break
        
        if choice == 'a':
            for ss in sub_sections:
                ss['include'] = True
            console.print("[green]✓ All sub-sections selected[/green]")
            continue
        
        if choice == 'x':
            for ss in sub_sections:
                ss['include'] = False
            console.print("[yellow]All sub-sections deselected[/yellow]")
            continue
        
        # Handle drill
        if choice == 'd':
            # Find drillable sub-sections
            drillable = [(i, ss) for i, ss in enumerate(sub_sections, 1) if ss.get('drillable')]
            if not drillable:
                console.print("[yellow]No sub-sections available for drilling into instances.[/yellow]")
                continue
            
            console.print("\n[cyan]Select sub-section to drill into:[/cyan]")
            for i, ss in drillable:
                console.print(f"  [{i}] {ss['name']} ({ss['count']} instances)")
            
            drill_choices = [str(i) for i, _ in drillable] + ['b', 'B']
            drill_choice = Prompt.ask("Drill into #", choices=drill_choices, default='b').lower()
            
            if drill_choice != 'b':
                idx = int(drill_choice) - 1
                if 0 <= idx < len(sub_sections) and sub_sections[idx].get('drillable'):
                    ss = sub_sections[idx]
                    instance_selection = select_instances(
                        mirror, ss['key'], ss['instances'],
                        source_hostname, target_hostname
                    )
                    if instance_selection:
                        ss['instance_selection'] = instance_selection
                        console.print(f"[green]✓ Instance selection saved for {ss['name']}[/green]")
            continue
        
        # Handle toggle
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(sub_sections):
                sub_sections[idx]['include'] = not sub_sections[idx]['include']
                status = "included" if sub_sections[idx]['include'] else "excluded"
                console.print(f"[cyan]{sub_sections[idx]['name']}: {status}[/cyan]")
                status = "included" if sub_sections[idx]['include'] else "excluded"
                console.print(f"[cyan]{sub_sections[idx]['name']}: {status}[/cyan]")
    
    return {ss['key']: {'include': ss['include'], 'instances': ss.get('instance_selection')} for ss in sub_sections}


def _select_protocols_sub_sections(
    mirror: 'ConfigMirror',
    h_info: Dict,
    source_hostname: str,
    target_hostname: str
) -> Optional[Dict[str, Any]]:
    """Select protocols sub-sections (ISIS, LDP, LLDP, LACP, etc.)."""
    
    sub_sections = []
    
    # ISIS
    isis_info = h_info.get('isis', {})
    if isis_info.get('instances'):
        for inst in isis_info['instances']:
            sub_sections.append({
                'key': f"isis_{inst['name']}",
                'name': f"isis {inst['name']}",
                'summary': f"ISO: {inst.get('iso_network', 'N/A')}, {len(inst.get('interfaces', []))} interfaces",
                'include': True
            })
    
    # LDP
    ldp_info = h_info.get('ldp', {})
    if ldp_info.get('transport_address'):
        sub_sections.append({
            'key': 'ldp',
            'name': 'ldp',
            'summary': f"Transport: {ldp_info['transport_address']}, {len(ldp_info.get('interfaces', []))} interfaces",
            'include': True
        })
    
    # LLDP (always include for connectivity)
    sub_sections.append({
        'key': 'lldp',
        'name': 'lldp',
        'summary': 'Link layer discovery (recommended to preserve)',
        'include': True
    })
    
    # LACP
    sub_sections.append({
        'key': 'lacp',
        'name': 'lacp',
        'summary': 'Link aggregation control',
        'include': True
    })
    
    if not sub_sections:
        console.print("[yellow]No protocols sub-sections found[/yellow]")
        return None
    
    console.print(f"\n[bold cyan]protocols Sub-sections on {source_hostname}[/bold cyan]")
    
    while True:
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=3)
        table.add_column("Sub-section", width=20)
        table.add_column("Details", width=40)
        table.add_column("Include", justify="center", width=10)
        
        for i, ss in enumerate(sub_sections, 1):
            include_str = "[green]✓ Yes[/green]" if ss['include'] else "[red]✗ No[/red]"
            table.add_row(str(i), ss['name'], ss['summary'], include_str)
        
        console.print(table)
        console.print()
        console.print("[dim]Commands: [1-N] Toggle, [A] All, [X] None, [C] Continue, [B] Back[/dim]")
        
        choice = Prompt.ask(
            "Select",
            choices=[str(i) for i in range(1, len(sub_sections) + 1)] + ['a', 'A', 'x', 'X', 'c', 'C', 'b', 'B'],
            default='c'
        ).lower()
        
        if choice == 'b':
            return None
        if choice == 'c':
            break
        if choice == 'a':
            for ss in sub_sections:
                ss['include'] = True
            continue
        if choice == 'x':
            for ss in sub_sections:
                ss['include'] = False
            continue
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(sub_sections):
                sub_sections[idx]['include'] = not sub_sections[idx]['include']
    
    return {ss['key']: ss['include'] for ss in sub_sections}


def _select_interfaces_sub_sections(
    mirror: 'ConfigMirror',
    h_info: Dict,
    analysis: Dict[str, Any],
    source_hostname: str,
    target_hostname: str
) -> Optional[Dict[str, Any]]:
    """Select interfaces sub-sections (WAN, Service, Physical, Cluster)."""
    
    target_type = detect_device_type(mirror.target_config)
    source_type = analysis.get('device_type', 'unknown')
    
    sub_sections = [
        {
            'key': 'wan',
            'name': 'WAN interfaces',
            'count': h_info.get('wan_count', 0),
            'summary': f"{h_info.get('wan_count', 0)} interfaces",
            'behavior': '[UNIQUE]',
            'note': '→ Will prompt for IP mapping',
            'include': True,  # Always handle WAN specially
            'is_unique': True
        },
        {
            'key': 'service',
            'name': 'Service interfaces',
            'count': h_info.get('pwhe_count', 0) + h_info.get('l2ac_count', 0),
            'summary': f"PWHE: {h_info.get('pwhe_count', 0)}, L2-AC: {h_info.get('l2ac_count', 0)}",
            'behavior': '✓ Mirror',
            'note': '',
            'include': True,
            'is_unique': False
        },
        {
            'key': 'loopback',
            'name': 'Loopback (lo0)',
            'count': 1,
            'summary': f"{mirror.source_lo0 or 'N/A'}",
            'behavior': '[UNIQUE]',
            'note': "→ Target's lo0 preserved",
            'include': True,
            'is_unique': True
        }
    ]
    
    # Add cluster interfaces if source is cluster
    if source_type == 'cluster':
        cluster_count = h_info.get('cluster_count', 0)
        skip_note = '→ Skipped (target is Standalone)' if target_type == 'standalone' else ''
        sub_sections.append({
            'key': 'cluster',
            'name': 'Cluster interfaces',
            'count': cluster_count,
            'summary': f"{cluster_count} (fab-*, ctrl-*, console-*)",
            'behavior': '[SKIP]' if target_type == 'standalone' else '[UNIQUE]',
            'note': skip_note,
            'include': False if target_type == 'standalone' else True,
            'is_unique': True
        })
    
    console.print(f"\n[bold cyan]interfaces Sub-sections on {source_hostname}[/bold cyan]")
    console.print(f"[dim]Source: {source_type}, Target: {target_type}[/dim]\n")
    
    while True:
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=3)
        table.add_column("Sub-section", width=20)
        table.add_column("Details", width=30)
        table.add_column("Behavior", justify="center", width=12)
        
        for i, ss in enumerate(sub_sections, 1):
            behavior_col = ss['behavior']
            if ss['note']:
                behavior_col += f"\n[dim]{ss['note']}[/dim]"
            table.add_row(str(i), ss['name'], ss['summary'], behavior_col)
        
        console.print(table)
        console.print()
        console.print("[dim]Commands: [1-N] Toggle (where allowed), [C] Continue, [B] Back[/dim]")
        
        choice = Prompt.ask(
            "Select",
            choices=[str(i) for i in range(1, len(sub_sections) + 1)] + ['c', 'C', 'b', 'B'],
            default='c'
        ).lower()
        
        if choice == 'b':
            return None
        if choice == 'c':
            break
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(sub_sections):
                ss = sub_sections[idx]
                if not ss['is_unique'] or ss['key'] == 'cluster':
                    ss['include'] = not ss['include']
                    console.print(f"[cyan]{ss['name']}: {'included' if ss['include'] else 'excluded'}[/cyan]")
                else:
                    console.print(f"[yellow]{ss['name']} has fixed behavior (unique to device)[/yellow]")
    
    return {ss['key']: {'include': ss['include'], 'is_unique': ss['is_unique']} for ss in sub_sections}


def _select_l2vpn_sub_sections(
    mirror: 'ConfigMirror',
    h_info: Dict,
    source_hostname: str,
    target_hostname: str
) -> Optional[Dict[str, Any]]:
    """Select L2VPN sub-sections (xconnect, bridge-domain)."""
    
    sub_sections = []
    
    xc_info = h_info.get('xconnect', {})
    if xc_info.get('count', 0) > 0:
        sub_sections.append({
            'key': 'xconnect',
            'name': 'xconnect group',
            'count': xc_info['count'],
            'include': True
        })
    
    bd_info = h_info.get('bridge_domain', {})
    if bd_info.get('count', 0) > 0:
        sub_sections.append({
            'key': 'bridge-domain',
            'name': 'bridge-domain',
            'count': bd_info['count'],
            'include': True
        })
    
    if not sub_sections:
        console.print("[yellow]No L2VPN sub-sections with content found[/yellow]")
        return None
    
    console.print(f"\n[bold cyan]l2vpn Sub-sections on {source_hostname}[/bold cyan]")
    
    while True:
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=3)
        table.add_column("Sub-section", width=20)
        table.add_column("Count", width=10)
        table.add_column("Include", justify="center", width=10)
        
        for i, ss in enumerate(sub_sections, 1):
            include_str = "[green]✓ Yes[/green]" if ss['include'] else "[red]✗ No[/red]"
            table.add_row(str(i), ss['name'], str(ss['count']), include_str)
        
        console.print(table)
        console.print()
        
        choice = Prompt.ask(
            "Select [1-N] Toggle, [C] Continue, [B] Back",
            choices=[str(i) for i in range(1, len(sub_sections) + 1)] + ['c', 'C', 'b', 'B'],
            default='c'
        ).lower()
        
        if choice == 'b':
            return None
        if choice == 'c':
            break
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(sub_sections):
                sub_sections[idx]['include'] = not sub_sections[idx]['include']
    
    return {ss['key']: ss['include'] for ss in sub_sections}


def select_instances(
    mirror: 'ConfigMirror',
    service_type: str,
    instances: List[Any],
    source_hostname: str,
    target_hostname: str
) -> Optional[Dict[str, bool]]:
    """
    Step 2b: Select individual service instances to mirror.
    
    Args:
        mirror: ConfigMirror instance
        service_type: Service type (e.g., 'vrf', 'evpn-vpws-fxc')
        instances: List of instance dicts/names
        source_hostname: Source hostname
        target_hostname: Target hostname
    
    Returns:
        Dict with instance_name -> include (True/False)
    """
    if not instances:
        return None
    
    # Normalize instances to list of dicts
    instance_list = []
    for inst in instances:
        if isinstance(inst, dict):
            instance_list.append({
                'name': inst.get('name', str(inst)),
                'data': inst,
                'include': True
            })
        else:
            instance_list.append({
                'name': str(inst),
                'data': None,
                'include': True
            })
    
    console.print(f"\n[bold cyan]{service_type} Instances on {source_hostname}[/bold cyan]")
    console.print(f"[dim]Select individual instances to mirror[/dim]\n")
    
    # For large lists, show summary and offer range selection
    if len(instance_list) > 20:
        console.print(f"[yellow]Found {len(instance_list)} instances. Showing first 10 and last 5.[/yellow]")
        display_indices = list(range(10)) + list(range(len(instance_list) - 5, len(instance_list)))
    else:
        display_indices = list(range(len(instance_list)))
    
    while True:
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=5)
        table.add_column("Instance", width=20)
        table.add_column("Details", width=35)
        table.add_column("Include", justify="center", width=10)
        
        for display_idx, idx in enumerate(display_indices):
            if display_idx == 10 and len(instance_list) > 20:
                table.add_row("...", f"... ({len(instance_list) - 15} more) ...", "", "")
            
            inst = instance_list[idx]
            include_str = "[green]✓ Yes[/green]" if inst['include'] else "[red]✗ No[/red]"
            
            # Build details based on service type
            details = ""
            if inst['data'] and service_type == 'vrf':
                rd = inst['data'].get('rd', 'N/A')
                ifaces = inst['data'].get('interfaces', [])
                nbrs = inst['data'].get('bgp_neighbors', [])
                details = f"RD: {rd}, {len(ifaces)} iface, {len(nbrs)} BGP nbr"
            elif inst['data'] and isinstance(inst['data'], dict):
                rd = inst['data'].get('rd', '')
                ifaces = inst['data'].get('interfaces', [])
                details = f"RD: {rd}, {len(ifaces)} iface" if rd else f"{len(ifaces)} iface"
            
            table.add_row(str(idx + 1), inst['name'], details, include_str)
        
        console.print(table)
        console.print()
        console.print("[dim]Commands: [N] Toggle, [R] Range (e.g., 1-10), [A] All, [X] None, [C] Continue, [B] Back[/dim]")
        
        choice = Prompt.ask("Select", default='c').lower()
        
        if choice == 'b':
            return None
        if choice == 'c':
            break
        if choice == 'a':
            for inst in instance_list:
                inst['include'] = True
            console.print(f"[green]✓ All {len(instance_list)} instances selected[/green]")
            continue
        if choice == 'x':
            for inst in instance_list:
                inst['include'] = False
            console.print(f"[yellow]All instances deselected[/yellow]")
            continue
        
        # Handle range (e.g., "1-10" or "5-20")
        range_match = re.match(r'(\d+)-(\d+)', choice)
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
            for i in range(start - 1, min(end, len(instance_list))):
                instance_list[i]['include'] = not instance_list[i]['include']
            console.print(f"[cyan]Toggled instances {start}-{min(end, len(instance_list))}[/cyan]")
            continue
        
        # Handle single number
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(instance_list):
                instance_list[idx]['include'] = not instance_list[idx]['include']
                status = "included" if instance_list[idx]['include'] else "excluded"
                console.print(f"[cyan]{instance_list[idx]['name']}: {status}[/cyan]")
    
    return {inst['name']: inst['include'] for inst in instance_list}


def show_uniqueness_transformations(
    mirror: 'ConfigMirror',
    source_hostname: str,
    target_hostname: str,
    analysis: Dict[str, Any]
) -> bool:
    """
    Step 3: Display all uniqueness transformations that will be applied.
    
    Shows:
    - Hostname transformation
    - Router-ID transformation
    - Loopback IP handling
    - Route Distinguisher transformation
    - ISO-network transformation
    - LDP transport address transformation
    - WAN interface handling
    - Cluster interface filtering
    
    Returns:
        True to continue, False to go back
    """
    console.print(f"\n[bold cyan]Step 3: Uniqueness Transformations[/bold cyan]")
    console.print(f"[dim]These transformations will be applied during mirroring[/dim]\n")
    
    # Build transformation list
    transformations = []
    
    # Hostname
    transformations.append({
        'item': 'Hostname',
        'source': mirror.source_hostname,
        'target': target_hostname,
        'note': ''
    })
    
    # Router-ID
    if mirror.source_rid and mirror.target_rid:
        transformations.append({
            'item': 'Router-ID',
            'source': mirror.source_rid,
            'target': mirror.target_rid,
            'note': ''
        })
    
    # Loopback IP
    if mirror.source_lo0 and mirror.target_lo0:
        transformations.append({
            'item': 'Loopback IP',
            'source': mirror.source_lo0,
            'target': f"{mirror.target_lo0} (preserved)",
            'note': ''
        })
    
    # Route Distinguisher
    if mirror.source_lo0 and mirror.target_lo0:
        src_ip = mirror.source_lo0.split('/')[0]
        tgt_ip = mirror.target_lo0.split('/')[0]
        transformations.append({
            'item': 'Route Dist.',
            'source': f"{src_ip}:N",
            'target': f"{tgt_ip}:N (auto-transform)",
            'note': ''
        })
    
    # ISIS ISO-network (if present)
    isis_info = analysis['hierarchies'].get('protocols', {}).get('isis', {})
    if isis_info.get('instances'):
        for inst in isis_info['instances']:
            if inst.get('iso_network'):
                transformations.append({
                    'item': 'ISO-network',
                    'source': inst['iso_network'],
                    'target': '(auto-derived from target loopback)',
                    'note': ''
                })
                break
    
    # LDP transport
    ldp_info = analysis['hierarchies'].get('protocols', {}).get('ldp', {})
    if ldp_info.get('transport_address') and mirror.target_lo0:
        tgt_ip = mirror.target_lo0.split('/')[0]
        transformations.append({
            'item': 'LDP transport',
            'source': ldp_info['transport_address'],
            'target': tgt_ip,
            'note': ''
        })
    
    # Display transformations table
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold", title="Uniqueness Transformations (Source → Target)")
    table.add_column("Item", width=15)
    table.add_column("Source", width=30)
    table.add_column("Target", width=30)
    
    for t in transformations:
        table.add_row(t['item'], t['source'], t['target'])
    
    console.print(table)
    console.print()
    
    # Show interface handling summary
    iface_info = analysis['hierarchies'].get('interfaces', {})
    source_type = analysis.get('device_type', 'unknown')
    target_type = detect_device_type(mirror.target_config)
    
    summary_lines = []
    summary_lines.append(f"WAN Interfaces: Target's preserved ({iface_info.get('wan_count', 0)} interfaces)")
    
    if source_type == 'cluster' and target_type == 'standalone':
        cluster_count = iface_info.get('cluster_count', 0)
        summary_lines.append(f"Cluster Ifaces: Filtered ({cluster_count} fab-*, ctrl-*, console-* skipped)")
    
    summary_panel = Panel(
        "\n".join(summary_lines),
        title="Interface Handling",
        border_style="dim"
    )
    console.print(summary_panel)
    console.print()
    
    # Confirm
    return Confirm.ask("Continue with these transformations?", default=True)


# =============================================================================
# ADVANCED MIRRORING: WAN MAPPING, BGP, MULTIHOMING, VALIDATION
# =============================================================================

def prompt_wan_interface_mapping(
    mirror: 'ConfigMirror',
    analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Step 4: WAN interface mapping dialog.
    
    Options:
    1. Preserve target's WAN config (default - recommended)
    2. Derive target WAN IPs from same subnet as source
    3. Map source WAN to specific target WAN parent
    
    Returns:
        Dict with mapping configuration
    """
    source_wan = analysis['hierarchies'].get('interfaces', {}).get('wan_interfaces', [])
    target_wan = get_wan_interfaces(mirror.target_config)
    
    console.print(f"\n[bold cyan]Step 4: WAN Interface Mapping[/bold cyan]")
    console.print(f"[dim]Source has {len(source_wan)} WAN interfaces, Target has {len(target_wan)}[/dim]\n")
    
    # Show WAN interfaces comparison
    if source_wan or target_wan:
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
        table.add_column("Source WAN", width=30)
        table.add_column("Target WAN", width=30)
        
        max_len = max(len(source_wan), len(target_wan))
        for i in range(min(max_len, 5)):  # Show first 5
            src = source_wan[i] if i < len(source_wan) else ""
            tgt = target_wan[i] if i < len(target_wan) else ""
            table.add_row(src, tgt)
        
        if max_len > 5:
            table.add_row(f"... ({len(source_wan) - 5} more)", f"... ({len(target_wan) - 5} more)")
        
        console.print(table)
        console.print()
    
    console.print("[bold]Options:[/bold]")
    console.print("  [1] Preserve target's WAN config [green](default - recommended)[/green]")
    console.print("  [2] Derive target WAN IPs from same subnet as source")
    console.print("      [dim]→ e.g., 14.14.14.4/29 → 14.14.14.2/29 (same subnet)[/dim]")
    console.print("  [3] Map source WAN to specific target WAN parent")
    console.print("  [B] Back")
    
    choice = Prompt.ask(
        "Select",
        choices=['1', '2', '3', 'b', 'B'],
        default='1'
    ).lower()
    
    if choice == 'b':
        return None
    
    result = {
        'mode': 'preserve',  # preserve, derive, map
        'mappings': {}
    }
    
    if choice == '1':
        result['mode'] = 'preserve'
        console.print("[green]✓ Target's WAN configuration will be preserved[/green]")
    
    elif choice == '2':
        result['mode'] = 'derive'
        console.print("\n[cyan]Subnet derivation will calculate target IPs from source subnets.[/cyan]")
        console.print("[dim]Example: If source is 14.14.14.4/29, target could be 14.14.14.2/29[/dim]")
        
        # For each source WAN, show derived IP
        for src_wan in source_wan[:5]:  # Show first 5
            # Get source IP from config
            src_ip = _get_interface_ip(mirror.source_config, src_wan)
            if src_ip:
                derived = _derive_ip_from_subnet(src_ip, mirror.target_lo0)
                if derived:
                    console.print(f"  {src_wan}: {src_ip} → {derived}")
                    result['mappings'][src_wan] = derived
        
        console.print("[green]✓ IPs will be derived from same subnets[/green]")
    
    elif choice == '3':
        result['mode'] = 'map'
        console.print("\n[cyan]Manual mapping: select which target WAN parent to use.[/cyan]")
        
        if not target_wan:
            console.print("[yellow]⚠ No target WAN interfaces found[/yellow]")
        else:
            console.print("Available target WAN parents:")
            for i, wan in enumerate(target_wan[:10], 1):
                console.print(f"  [{i}] {wan}")
            
            selected = Prompt.ask(
                "Select target WAN parent #",
                choices=[str(i) for i in range(1, min(11, len(target_wan) + 1))] + ['b', 'B'],
                default='1'
            ).lower()
            
            if selected != 'b':
                idx = int(selected) - 1
                result['target_wan_parent'] = target_wan[idx]
                console.print(f"[green]✓ Will use {target_wan[idx]} as target WAN parent[/green]")
    
    return result


def _get_interface_ip(config: str, interface: str) -> Optional[str]:
    """Get IPv4 address of an interface from config."""
    # Find interface block
    pattern = re.compile(
        rf'^\s*{re.escape(interface)}\s*$.*?ipv4-address\s+(\S+)',
        re.MULTILINE | re.DOTALL
    )
    match = pattern.search(config)
    if match:
        return match.group(1)
    return None


def _derive_ip_from_subnet(source_ip: str, target_loopback: Optional[str]) -> Optional[str]:
    """
    Derive a target IP from the same subnet as source.
    
    Strategy: Use the last octet from target loopback to offset within subnet.
    e.g., source=14.14.14.4/29, target_lo=2.2.2.2 → 14.14.14.2/29
    """
    if not target_loopback:
        return None
    
    try:
        import ipaddress
        
        # Parse source
        if '/' in source_ip:
            src_net = ipaddress.ip_interface(source_ip)
        else:
            src_net = ipaddress.ip_interface(f"{source_ip}/24")
        
        # Get target's last octet
        tgt_lo_ip = target_loopback.split('/')[0]
        tgt_last_octet = int(tgt_lo_ip.split('.')[-1])
        
        # Get network and derive new host
        network = src_net.network
        hosts = list(network.hosts())
        
        # Use target's last octet modulo number of hosts
        if hosts:
            new_idx = (tgt_last_octet - 1) % len(hosts)
            new_ip = hosts[new_idx]
            return f"{new_ip}/{src_net.network.prefixlen}"
    except Exception:
        pass
    
    return None


def transform_vrf_bgp_config(
    vrf_config: str,
    vrf_data: Dict[str, Any],
    target_interfaces: List[str],
    target_loopback: str
) -> Tuple[str, Dict[str, Any]]:
    """
    Transform VRF BGP configuration for target device.
    
    Handles:
    - Auto-derive update-source from VRF-attached interfaces
    - Transform RD to use target's loopback
    - Keep same RT (for EVPN peering)
    
    Args:
        vrf_config: VRF configuration block
        vrf_data: Parsed VRF data dict
        target_interfaces: List of interfaces that will be attached to VRF on target
        target_loopback: Target device's loopback IP
    
    Returns:
        Tuple of (transformed_config, metadata)
    """
    transformed = vrf_config
    metadata = {}
    
    # Transform RD (replace source loopback with target loopback)
    if target_loopback:
        tgt_ip = target_loopback.split('/')[0]
        # Replace RD IP part
        rd_pattern = re.compile(r'(route-distinguisher\s+)\d+\.\d+\.\d+\.\d+(:\d+)')
        transformed = rd_pattern.sub(rf'\g<1>{tgt_ip}\g<2>', transformed)
        metadata['rd_transformed'] = True
    
    # Transform router-id
    if target_loopback:
        tgt_ip = target_loopback.split('/')[0]
        rid_pattern = re.compile(r'(router-id\s+)\d+\.\d+\.\d+\.\d+')
        transformed = rid_pattern.sub(rf'\g<1>{tgt_ip}', transformed)
        metadata['rid_transformed'] = True
    
    # Auto-derive update-source from VRF interfaces
    if target_interfaces:
        target_iface = target_interfaces[0]  # Use first attached interface
        us_pattern = re.compile(r'(update-source\s+)\S+')
        transformed = us_pattern.sub(rf'\g<1>{target_iface}', transformed)
        metadata['update_source'] = target_iface
    
    return transformed, metadata


def prompt_bgp_neighbor_addresses(
    vrf_data: Dict[str, Any],
    interface_ip: Optional[str]
) -> Dict[str, Dict[str, Optional[str]]]:
    """
    Prompt user for BGP neighbor IP addresses.
    
    Shows suggestions based on interface subnet.
    
    Args:
        vrf_data: Parsed VRF data with existing neighbors
        interface_ip: IP address of the VRF interface
    
    Returns:
        Dict mapping neighbor_ip -> {'ipv4': new_ip, 'ipv6': new_ipv6}
    """
    neighbors = vrf_data.get('bgp_neighbors', [])
    if not neighbors:
        return {}
    
    results = {}
    
    console.print(f"\n[bold cyan]BGP Neighbor Configuration for {vrf_data['name']}[/bold cyan]")
    
    # Calculate subnet suggestions
    suggestions = []
    if interface_ip:
        try:
            import ipaddress
            if '/' in interface_ip:
                net = ipaddress.ip_interface(interface_ip)
                hosts = list(net.network.hosts())[:5]
                suggestions = [str(h) for h in hosts]
        except Exception:
            pass
    
    for nbr in neighbors:
        source_ip = nbr['ip']
        remote_as = nbr.get('remote_as', 'N/A')
        
        console.print(f"\n[dim]Source neighbor: {source_ip} (AS {remote_as})[/dim]")
        
        if suggestions:
            console.print(f"[dim]Suggested from subnet: {', '.join(suggestions[:3])}...[/dim]")
        
        # IPv4
        new_ipv4 = Prompt.ask(
            f"Enter neighbor IPv4 address [B]ack",
            default=source_ip  # Default to same IP (for dual-homing with same CE)
        )
        
        if new_ipv4.lower() == 'b':
            return None
        
        # IPv6 (optional)
        new_ipv6 = Prompt.ask(
            f"Enter neighbor IPv6 address (optional, Enter to skip)",
            default=""
        )
        
        results[source_ip] = {
            'ipv4': new_ipv4,
            'ipv6': new_ipv6 if new_ipv6 else None
        }
    
    return results


def mirror_multihoming_config(
    source_mh: Dict[str, str],
    target_available_interfaces: List[str],
    match_source_esi: bool,
    source_df_pref: int = 50,
    target_df_pref: int = 100
) -> Tuple[str, Dict[str, str]]:
    """
    Generate multihoming configuration for target device.
    
    Follows existing MH section patterns from configure_multihoming().
    
    Args:
        source_mh: Dict of source interface -> ESI mappings
        target_available_interfaces: List of available interfaces on target
        match_source_esi: If True, use same ESI as source (for dual-homing)
        source_df_pref: Source device's DF preference
        target_df_pref: Target device's DF preference (should differ from source)
    
    Returns:
        Tuple of (mh_config_text, interface_to_esi_mapping)
    """
    if not source_mh:
        return '', {}
    
    config_lines = ['multihoming', '  redundancy-mode single-active']
    interface_mapping = {}
    
    for source_iface, source_esi in source_mh.items():
        # Smart-match source interface to target
        target_iface = smart_match_interface(source_iface, target_available_interfaces)
        
        if not target_iface:
            # Skip if no match found
            continue
        
        # Use same ESI for dual-homing, or generate new
        if match_source_esi:
            esi_value = source_esi
        else:
            # Generate new ESI (would need index tracking)
            esi_value = source_esi  # For now, use same
        
        interface_mapping[target_iface] = esi_value
        
        config_lines.append(f'  interface {target_iface}')
        config_lines.append(f'    esi arbitrary value {esi_value}')
        config_lines.append('    redundancy-mode single-active')
        config_lines.append('    designated-forwarder')
        config_lines.append(f'      algorithm highest-preference value {target_df_pref}')
        config_lines.append('    !')
        config_lines.append('  !')
    
    config_lines.append('!')
    
    return '\n'.join(config_lines), interface_mapping


def smart_match_interface(
    source_iface: str,
    target_available: List[str]
) -> Optional[str]:
    """
    Smart-match source interface to target based on naming patterns.
    
    Matching strategies:
    1. Exact match (if exists)
    2. Same VLAN suffix (e.g., .1, .219)
    3. Same interface type with different slot
    
    Args:
        source_iface: Source interface name
        target_available: List of available target interfaces
    
    Returns:
        Best matching target interface or None
    """
    if not target_available:
        return None
    
    # Strategy 1: Exact match
    if source_iface in target_available:
        return source_iface
    
    # Strategy 2: Same VLAN suffix
    if '.' in source_iface:
        vlan_suffix = source_iface.split('.')[-1]
        for target in target_available:
            if target.endswith(f'.{vlan_suffix}'):
                return target
    
    # Strategy 3: Same interface type prefix
    # Extract type (ph, ge100, ge400, bundle)
    source_type = None
    for prefix in ['ph', 'ge400', 'ge100', 'bundle']:
        if source_iface.startswith(prefix):
            source_type = prefix
            break
    
    if source_type:
        for target in target_available:
            if target.startswith(source_type):
                return target
    
    # Strategy 4: Map across interface types (cluster -> SA)
    # ge100-18/0/0.X -> ge400-0/0/4.X
    if source_iface.startswith('ge100-'):
        # Find a ge400 interface with same VLAN suffix
        if '.' in source_iface:
            vlan_suffix = source_iface.split('.')[-1]
            for target in target_available:
                if target.startswith('ge400-') and target.endswith(f'.{vlan_suffix}'):
                    return target
    
    return None


def filter_cluster_interfaces_from_config(
    config: str,
    cluster_interfaces: Set[str]
) -> str:
    """
    Filter out cluster-specific interfaces from configuration.
    
    Removes fab-*, ctrl-*, console-* interface blocks when mirroring
    from Cluster to Standalone.
    
    Args:
        config: Configuration text
        cluster_interfaces: Set of cluster interface names to remove
    
    Returns:
        Filtered configuration
    """
    if not cluster_interfaces:
        return config
    
    lines = config.split('\n')
    result = []
    skip_block = False
    skip_indent = 0
    
    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        
        # Check if this is a cluster interface definition
        if indent == 2 and stripped in cluster_interfaces:
            skip_block = True
            skip_indent = indent
            continue
        
        # Check if we've left the skipped block
        if skip_block:
            if stripped == '!' and indent == skip_indent:
                skip_block = False
                continue
            if indent <= skip_indent and stripped and stripped != '!':
                skip_block = False
            else:
                continue
        
        result.append(line)
    
    return '\n'.join(result)


def validate_mirror_config(config: str) -> Tuple[List[str], List[str]]:
    """
    Validate mirrored configuration against DNOS rules.
    
    Checks:
    1. Hierarchy structure validity
    2. Knob combinations
    3. Known invalid patterns
    
    Args:
        config: Configuration text to validate
    
    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []
    
    # Check 1: Basic hierarchy structure
    lines = config.split('\n')
    indent_stack = []
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        
        indent = len(line) - len(line.lstrip())
        
        # Check for inconsistent indentation
        if indent % 2 != 0:
            errors.append(f"Line {i}: Invalid indentation (not multiple of 2)")
    
    # Check 2: Known invalid combinations
    # flowspec on PWHE is not supported
    if re.search(r'ph\d+\.\d+.*flowspec\s+enabled', config, re.DOTALL):
        warnings.append("flowspec enabled on PWHE interface not supported")
    
    # l2-service and ipv4-address on same interface
    iface_blocks = re.findall(r'^\s{2}(\S+)\s*\n((?:\s{4}.*\n)*)', config, re.MULTILINE)
    for iface_name, iface_block in iface_blocks:
        has_l2_service = 'l2-service enabled' in iface_block
        has_ipv4 = 'ipv4-address' in iface_block
        if has_l2_service and has_ipv4:
            warnings.append(f"{iface_name}: l2-service and ipv4-address on same interface")
    
    # Check 3: Empty service instances
    empty_instances = re.findall(r'instance\s+(\S+)\s*\n\s*!', config)
    for inst in empty_instances:
        warnings.append(f"Empty instance: {inst}")
    
    return errors, warnings


def _render_transformation_header(source_hostname: str, target_hostname: str, analysis: dict) -> Panel:
    """
    Create a transformation header panel showing source -> target mappings.
    
    This panel should be displayed at the top during section selection.
    """
    from rich.text import Text
    import json
    from pathlib import Path
    
    # Get source and target info
    source_type = analysis.get('device_type', 'unknown')
    source_ncps = analysis.get('ncp_slots', [])
    
    # Load target operational data
    target_type = 'unknown'
    target_lo0 = 'N/A'
    target_ncps = []
    
    try:
        target_op_file = Path(f"/home/dn/SCALER/db/configs/{target_hostname}/operational.json")
        if target_op_file.exists():
            with open(target_op_file) as f:
                target_op = json.load(f)
                target_type = target_op.get('system_type', 'unknown')
    except:
        pass
    
    # Load target config for loopback
    try:
        target_config_file = Path(f"/home/dn/SCALER/db/configs/{target_hostname}/running.txt")
        if target_config_file.exists():
            target_config = target_config_file.read_text()
            # Extract lo0 IP
            import re
            lo0_match = re.search(r'lo0\s+.*?address\s+(\d+\.\d+\.\d+\.\d+/\d+)', target_config, re.DOTALL)
            if lo0_match:
                target_lo0 = lo0_match.group(1)
    except:
        pass
    
    # Get source loopback
    source_lo0 = 'N/A'
    try:
        import re
        lo0_match = re.search(r'lo0\s+.*?address\s+(\d+\.\d+\.\d+\.\d+/\d+)', analysis.get('source_config', ''), re.DOTALL)
        if lo0_match:
            source_lo0 = lo0_match.group(1)
    except:
        pass
    
    # Build transformation text
    lines = [
        f"[bold]Source:[/bold] {source_hostname} ({source_type})  [bold]→[/bold]  [bold]Target:[/bold] {target_hostname} ({target_type})",
        "",
        "[bold]Transformations:[/bold]",
        f"  Hostname: {source_hostname} → {target_hostname}",
        f"  Loopback: {source_lo0} → {target_lo0 if target_lo0 != 'N/A' else '[yellow]NEEDS INPUT[/yellow]'}",
    ]
    
    # Get WAN interface info
    wan_count = analysis.get('hierarchies', {}).get('interfaces', {}).get('wan_count', 0)
    if wan_count > 0:
        # Get source WAN interfaces with IPs
        source_wans = get_wan_interfaces(analysis.get('source_config', ''))
        
        # Load target LLDP for available interfaces
        target_lldp_count = 0
        try:
            if target_op_file.exists():
                with open(target_op_file) as f:
                    target_op = json.load(f)
                    target_lldp = target_op.get('lldp_neighbors', [])
                    target_lldp_count = len(target_lldp)
        except:
            pass
        
        lines.append(f"  [bold]WAN Interfaces:[/bold] {wan_count} in source")
        
        # Show first 4 WAN interfaces with their IPs in compact format
        if source_wans:
            for wan in source_wans[:4]:
                # Extract IP from config
                try:
                    ip_match = re.search(
                        rf'^\s+{re.escape(wan)}\s*\n(?:.*\n)*?\s+ipv4-address\s+(\d+\.\d+\.\d+\.\d+(?:/\d+)?)',
                        analysis.get('source_config', ''), re.MULTILINE
                    )
                    ip_addr = ip_match.group(1) if ip_match else 'no IP'
                    lines.append(f"    • {wan} ({ip_addr})")
                except:
                    lines.append(f"    • {wan}")
            
            if len(source_wans) > 4:
                lines.append(f"    [dim]... and {len(source_wans) - 4} more[/dim]")
        
        lines.append(f"  → [cyan]Map to target ({target_lldp_count} LLDP neighbors available)[/cyan]")
    
    # Check for device type mismatch
    if 'cluster' in source_type.lower() and 'standalone' in target_type.lower():
        lines.append("")
        lines.append("[yellow]Cluster → Standalone: fab-*, ctrl-*, console-* will be SKIPPED[/yellow]")
    elif 'standalone' in source_type.lower() and 'cluster' in target_type.lower():
        lines.append("")
        lines.append("[yellow]Standalone → Cluster: May need additional cluster config[/yellow]")
    
    # Hint about Edit option
    lines.append("")
    lines.append("[dim]Use [E]dit to configure WAN mapping and loopback IP[/dim]")
    
    content = "\n".join(lines)
    return Panel(content, title="[bold cyan]Transformation Preview[/bold cyan]", border_style="cyan")


def select_sections_to_mirror(
    mirror: ConfigMirror,
    source_hostname: str,
    target_hostname: str
) -> Optional[Dict[str, Any]]:
    """
    Pre-select which sections to mirror using Keep/Edit/Delete/Skip flow.
    
    NEW IMPLEMENTATION: Section-by-section selection with inline prompts:
    1. Show transformation header panel
    2. For each hierarchy, single-line inline prompt [K]eep/[E]dit/[D]elete/[S]kip
    3. If [E]dit, drill into sub-sections with per-item K/E/D/S
    4. Show summary and confirm
    
    Args:
        mirror: ConfigMirror instance
        source_hostname: Source device hostname
        target_hostname: Target device hostname
        
    Returns:
        Dict with detailed section selection, or None if cancelled
    """
    from rich.table import Table
    
    # Step 0: Analyze source configuration
    console.print(f"\n[bold cyan]Analyzing {source_hostname} configuration...[/bold cyan]")
    analysis = analyze_source_config(mirror)
    analysis['source_config'] = mirror.source_config  # Store for header
    
    # Get hierarchy details
    h = analysis['hierarchies']
    ns = h.get('network-services', {})
    
    # Show quick summary
    console.print(f"[dim]  Device type: {analysis['device_type']}, NCPs: {analysis['ncp_slots']}[/dim]")
    console.print(f"[dim]  Services: {ns.get('fxc', {}).get('count', 0)} FXC, {ns.get('vpls', {}).get('count', 0)} VPLS, {ns.get('vrf', {}).get('count', 0)} VRF[/dim]")
    console.print(f"[dim]  Interfaces: {h.get('interfaces', {}).get('wan_count', 0)} WAN, {h.get('interfaces', {}).get('service_count', 0)} service[/dim]")
    
    # Show transformation header panel
    console.print()
    header_panel = _render_transformation_header(source_hostname, target_hostname, analysis)
    console.print(header_panel)
    
    # Define hierarchies with descriptions and line counts
    hierarchies = []
    hierarchy_content = {}
    
    hierarchy_defs = [
        ('system', 'SYSTEM', f"{source_hostname}"),
        ('interfaces', 'INTERFACES', f"{h.get('interfaces', {}).get('wan_count', 0)} WAN, {h.get('interfaces', {}).get('pwhe_count', 0)} PWHE"),
        ('network-services', 'NETWORK-SERVICES', f"{ns.get('fxc', {}).get('count', 0)} FXC, {ns.get('vpls', {}).get('count', 0)} VPLS, {ns.get('vrf', {}).get('count', 0)} VRF"),
        ('protocols', 'PROTOCOLS', f"ISIS, LDP: {'yes' if h.get('protocols', {}).get('has_ldp') else 'no'}"),
        ('qos', 'QOS', 'policies'),
        ('routing-policy', 'ROUTING-POLICY', 'route-policies'),
        ('access-lists', 'ACCESS-LISTS', 'ACLs'),
    ]
    
    for key, name, desc in hierarchy_defs:
        content = ""
        try:
            content = mirror._extract_clean_section(mirror.source_config, key)
        except:
            pass
        
        lines = len(content.split('\n')) if content else 0
        hierarchy_content[key] = content
        hierarchies.append((key, name, desc, lines))
    
    # Track selections
    hierarchy_selection = {}
    sub_selections = {}
    
    # Show action legend
    console.print("\n[bold]Select action for each section:[/bold]")
    console.print("  [green][K] Keep[/green] - include existing configuration in output")
    console.print("  [yellow][E] Edit[/yellow] - modify/replace this section [cyan](default)[/cyan]")
    console.print("  [red][D] Delete[/red] - remove this section entirely")
    console.print("  [dim][S] Skip[/dim] - EXCLUDE from output")
    console.print("  [B] Back | [T] Top")
    console.print()
    
    # === PHASE 1: Collect all selections on ONE screen ===
    pending_edits = []  # Track which hierarchies need editing
    
    for key, name, desc, lines in hierarchies:
        if lines == 0:
            console.print(f"  [dim]{name} ({desc}) - not in source[/dim]")
            hierarchy_selection[key] = False
            continue
        
        # Build section info line
        info_parts = [f"[bold cyan]{name}[/bold cyan]"]
        info_parts.append(f"[dim]({lines} lines)[/dim]")
        
        # Add special notes inline
        if key == 'system':
            info_parts.append(f"[dim]→ hostname: {target_hostname}[/dim]")
        elif key == 'interfaces':
            if 'cluster' in analysis.get('device_type', '').lower():
                h = analysis.get('hierarchies', {})
                cluster_count = h.get('interfaces', {}).get('cluster_count', 0)
                if cluster_count > 0:
                    info_parts.append(f"[yellow]⚠ {cluster_count} cluster skipped[/yellow]")
        
        section_info = " ".join(info_parts)
        
        # Single line prompt for each section
        action = Prompt.ask(
            f"  {section_info}",
            choices=['k', 'K', 'e', 'E', 'd', 'D', 's', 'S', 'b', 'B', 't', 'T'],
            default='e'  # Default to Edit - most flexible option
        ).lower()
        
        if action == 'b':
            return None
        elif action == 't':
            raise TopException()
        elif action == 'k':
            hierarchy_selection[key] = True
        elif action == 's':
            hierarchy_selection[key] = False
        elif action == 'd':
            hierarchy_selection[key] = 'delete'
        elif action == 'e':
            hierarchy_selection[key] = True
            pending_edits.append((key, name))  # Queue for editing after summary
    
    # === PHASE 2: Show summary before editing ===
    console.print(f"\n[bold cyan]─── Selection Summary ───[/bold cyan]")
    for key, name, desc, lines in hierarchies:
        sel = hierarchy_selection.get(key)
        is_edit = any(k == key for k, _ in pending_edits)
        
        if sel == True and is_edit:
            console.print(f"  {name:12} → [yellow]✎ Edit[/yellow]")
        elif sel == True:
            console.print(f"  {name:12} → [green]✓ Keep[/green]")
        elif sel == 'delete':
            console.print(f"  {name:12} → [red]✗ Delete[/red]")
        elif sel == False:
            console.print(f"  {name:12} → [dim]○ Skip[/dim]")
    
    # Confirm before proceeding
    proceed = Prompt.ask("\nProceed with these choices?", choices=['y', 'Y', 'n', 'N', 'b', 'B'], default='y').lower()
    if proceed in ('n', 'b'):
        console.print("[dim]← Restarting section selection...[/dim]")
        return None
    
    # === PHASE 3: Now process edits for marked sections ===
    if pending_edits:
        console.print(f"\n[bold yellow]━━━ Editing {len(pending_edits)} Section(s) ━━━[/bold yellow]")
        
        for key, name in pending_edits:
            console.print(f"\n[bold]Editing: {name}[/bold]")
            sub_result = _edit_hierarchy_subsections(mirror, key, name, source_hostname, target_hostname, analysis)
            
            if sub_result is None:
                # User cancelled edit - just keep section as-is
                console.print(f"  [dim]Edit cancelled - keeping {name} as mirror[/dim]")
            else:
                sub_selections[key] = sub_result
    
    # Show summary
    console.print(f"\n[bold cyan]━━━ Selection Summary ━━━[/bold cyan]")
    summary_table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    summary_table.add_column("Section", width=20)
    summary_table.add_column("Action", width=15)
    summary_table.add_column("Details", style="dim")
    
    for key, name, desc, lines in hierarchies:
        sel = hierarchy_selection.get(key)
        if sel == True:
            action_display = "[green]Mirror[/green]"
            details = f"{lines} lines"
            if key in sub_selections:
                details += " (customized)"
        elif sel == 'delete':
            action_display = "[red]Delete[/red]"
            details = "Remove from target"
        elif sel == False:
            action_display = "[dim]Skip[/dim]"
            details = "Not included"
        else:
            action_display = "[dim]N/A[/dim]"
            details = "Not in source"
        summary_table.add_row(name, action_display, details)
    
    console.print(summary_table)
    
    # Confirm
    confirm_choice = Prompt.ask(
        "\n[P]roceed | [R]estart selection | [B]ack",
        choices=['p', 'P', 'r', 'R', 'b', 'B'],
        default='p'
    ).lower()
    
    if confirm_choice == 'b':
        return None
    elif confirm_choice == 'r':
        # Restart selection
        return select_sections_to_mirror(mirror, source_hostname, target_hostname)
    
    # Show uniqueness transformations
    if not show_uniqueness_transformations(mirror, source_hostname, target_hostname, analysis):
        return None
    
    # Store sub-selections on mirror object
    mirror._hierarchy_sub_selections = sub_selections
    
    # Build final result
    result = {
        'hierarchies': hierarchy_selection,
        'sub_sections': sub_selections,
        'analysis': analysis,
        # Legacy compatibility
        'system': hierarchy_selection.get('system', False) == True,
        'services': hierarchy_selection.get('network-services', False) == True,
        'service_interfaces': hierarchy_selection.get('interfaces', False) == True,
        'multihoming': hierarchy_selection.get('network-services', False) == True,
        'routing': hierarchy_selection.get('routing', False) == True,
        'routing_policy': hierarchy_selection.get('routing-policy', False) == True,
        'qos': hierarchy_selection.get('qos', False) == True,
        'acls': hierarchy_selection.get('access-lists', False) == True,
        'protocols': hierarchy_selection.get('protocols', False) == True,
    }
    
    return result


# =========================================================================
# SERVICE EDIT WIZARD WITH KNOBS AND INTERFACE DEPENDENCIES
# =========================================================================

def _get_service_attached_interfaces(services: List[Dict], service_type: str) -> Dict[str, List[str]]:
    """
    Extract interfaces attached to each service.
    
    Args:
        services: List of service dicts from parser
        service_type: Service type (fxc, vpws, vpls, vrf)
    
    Returns:
        Dict mapping service name to list of attached interfaces
    """
    result = {}
    for svc in services:
        name = svc.get('name', '')
        interfaces = svc.get('interfaces', [])
        if name:
            result[name] = interfaces
    return result


def _load_target_lldp_neighbors(target_hostname: str) -> List[Dict]:
    """Load LLDP neighbors from target's operational.json."""
    lldp_neighbors = []
    try:
        op_path = f"db/configs/{target_hostname}/operational.json"
        if os.path.exists(op_path):
            import json
            with open(op_path) as f:
                op_data = json.load(f)
                lldp_neighbors = op_data.get('lldp_neighbors', [])
    except Exception:
        pass
    return lldp_neighbors


def _edit_service_knobs_wizard(
    mirror: 'ConfigMirror',
    service_type: str,
    services: List[Dict],
    analysis: dict,
    target_hostname: str,
    interfaces_skipped: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Edit wizard for service knobs and dependent interfaces.
    
    Allows:
    - Viewing/editing specific service knobs (RD, RT, EVI)
    - Detecting attached interfaces
    - Adding essential interfaces if interfaces were skipped
    - Mapping interface parents to target's LLDP neighbors
    
    Args:
        mirror: ConfigMirror instance
        service_type: Type of service (fxc, vpws, vpls, vrf)
        services: List of service dicts from parser
        analysis: Config analysis dict
        target_hostname: Target device hostname
        interfaces_skipped: Whether interfaces section was skipped
    
    Returns:
        Dict with edit configuration, or None to cancel
    """
    from rich.table import Table
    from rich import box
    
    service_names = {
        'fxc': 'EVPN-VPWS-FXC',
        'vpws': 'EVPN-VPWS',
        'vpls': 'EVPN-VPLS',
        'vrf': 'L3VPN/VRF'
    }
    
    service_display = service_names.get(service_type, service_type.upper())
    
    console.print(f"\n[bold cyan]━━━ Edit {service_display} Services ━━━[/bold cyan]")
    
    if not services:
        console.print(f"[dim]No {service_display} services found in source.[/dim]")
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
        return {'action': 'skip'}
    
    # Get attached interfaces for all services
    service_interfaces = _get_service_attached_interfaces(services, service_type)
    total_interfaces = sum(len(ifaces) for ifaces in service_interfaces.values())
    
    # Summary table
    summary_table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    summary_table.add_column("Service", style="cyan", width=25)
    summary_table.add_column("EVI", style="yellow", width=10)
    summary_table.add_column("RD", style="green", width=20)
    summary_table.add_column("RT", style="magenta", width=20)
    summary_table.add_column("Interfaces", style="blue", width=15)
    
    # Show first 10 services
    for svc in services[:10]:
        name = svc.get('name', '?')
        evi = str(svc.get('evi', '-'))
        rd = svc.get('rd', '-')
        rt = svc.get('rt', '-')
        iface_count = len(svc.get('interfaces', []))
        summary_table.add_row(name, evi, rd, rt, f"{iface_count} attached")
    
    if len(services) > 10:
        summary_table.add_row(f"... +{len(services) - 10} more", "", "", "", "")
    
    console.print(summary_table)
    
    console.print(f"\n[bold]Summary:[/bold] {len(services)} services, {total_interfaces} attached interfaces")
    
    # Check if interfaces were skipped and services need them
    if interfaces_skipped and total_interfaces > 0:
        console.print(f"\n[yellow]⚠ Warning:[/yellow] Interfaces section was skipped, but services have {total_interfaces} attached interfaces.")
        console.print("[dim]Without interfaces, services will have no connectivity on target.[/dim]")
    
    # Show edit options
    console.print(f"\n[bold]Edit Options:[/bold]")
    console.print("  [1] Mirror all services (RD transformed)")
    console.print("  [2] Edit service range (select which services to include)")
    console.print("  [3] Edit knobs (RD/RT/EVI values)")
    if total_interfaces > 0:
        console.print("  [4] Edit attached interfaces (view/remap)")
        if interfaces_skipped:
            console.print("  [5] [yellow]Add essential interfaces[/yellow] (required for connectivity)")
    console.print("  [T] Keep target's existing config")
    console.print("  [B] Back")
    
    max_choice = "5" if interfaces_skipped and total_interfaces > 0 else "4" if total_interfaces > 0 else "3"
    choices = [str(i) for i in range(1, int(max_choice) + 1)] + ['t', 'T', 'b', 'B']
    
    choice = Prompt.ask("Select option", choices=choices, default="1").lower()
    
    if choice == 'b':
        return None
    elif choice == 't':
        return {'action': 'keep_target'}
    elif choice == '1':
        # Mirror all services
        return {'action': 'mirror', 'transform_rd': True}
    elif choice == '2':
        # Edit service range
        return _edit_service_range(services, service_type)
    elif choice == '3':
        # Edit knobs
        return _edit_service_knobs(mirror, services, service_type, target_hostname)
    elif choice == '4':
        # Edit attached interfaces
        return _edit_attached_interfaces(mirror, services, service_type, target_hostname, analysis)
    elif choice == '5':
        # Add essential interfaces with LLDP mapping
        return _add_essential_interfaces(mirror, services, service_type, target_hostname, analysis)
    
    return {'action': 'mirror', 'transform_rd': True}


def _edit_service_range(services: List[Dict], service_type: str) -> Dict[str, Any]:
    """Allow selecting a range of services to include."""
    from rich.table import Table
    from rich import box
    
    console.print(f"\n[bold]Select Service Range[/bold]")
    console.print(f"Total services: {len(services)}")
    
    # Get service names
    names = [svc.get('name', f'service_{i}') for i, svc in enumerate(services)]
    
    console.print(f"\n[dim]Services: {names[0]} ... {names[-1]}[/dim]")
    
    start_idx = Prompt.ask("Start index (1-based)", default="1")
    end_idx = Prompt.ask("End index (1-based)", default=str(len(services)))
    
    try:
        start = max(1, int(start_idx)) - 1
        end = min(len(services), int(end_idx))
        selected = services[start:end]
        console.print(f"[green]✓ Selected {len(selected)} services: {names[start]} to {names[end-1]}[/green]")
        return {
            'action': 'range',
            'start': start,
            'end': end,
            'selected_services': selected,
            'transform_rd': True
        }
    except ValueError:
        console.print("[red]Invalid range. Using all services.[/red]")
        return {'action': 'mirror', 'transform_rd': True}


def _edit_service_knobs(mirror: 'ConfigMirror', services: List[Dict], service_type: str, target_hostname: str) -> Dict[str, Any]:
    """Edit specific knobs (RD, RT, EVI) for services."""
    from rich.table import Table
    from rich import box
    
    console.print(f"\n[bold]Edit Service Knobs[/bold]")
    console.print("[dim]Modify RD, RT, or EVI values for services[/dim]")
    
    # Get target loopback for RD transformation
    target_lo0 = mirror.target_lo0.split('/')[0] if mirror.target_lo0 else None
    source_lo0 = mirror.source_lo0.split('/')[0] if mirror.source_lo0 else None
    
    console.print(f"\n[bold]Current RD Transformation:[/bold]")
    console.print(f"  Source loopback: {source_lo0 or 'not detected'}")
    console.print(f"  Target loopback: {target_lo0 or 'not detected'}")
    console.print(f"  [green]RD format: {target_lo0 or '?'}:<evi>[/green]")
    
    console.print(f"\n[bold]Knob Options:[/bold]")
    console.print("  [1] Transform RD to target loopback (default)")
    console.print("  [2] Keep original RD (no transformation)")
    console.print("  [3] Custom RD prefix (enter new prefix)")
    console.print("  [4] Modify RT ASN (change BGP ASN in route-target)")
    console.print("  [5] Offset EVI values (add/subtract from all EVIs)")
    console.print("  [B] Back")
    
    choice = Prompt.ask("Select", choices=['1', '2', '3', '4', '5', 'b', 'B'], default='1').lower()
    
    if choice == 'b':
        return None
    elif choice == '1':
        return {'action': 'mirror', 'transform_rd': True}
    elif choice == '2':
        return {'action': 'mirror', 'transform_rd': False}
    elif choice == '3':
        new_prefix = Prompt.ask("Enter new RD prefix (IP address)", default=target_lo0 or "1.1.1.1")
        return {'action': 'mirror', 'transform_rd': True, 'rd_prefix': new_prefix}
    elif choice == '4':
        # Get current RT ASN from first service
        current_rt = services[0].get('rt', '65000:1') if services else '65000:1'
        current_asn = current_rt.split(':')[0] if ':' in current_rt else '65000'
        new_asn = Prompt.ask("Enter new ASN for RT", default=current_asn)
        return {'action': 'mirror', 'transform_rd': True, 'rt_asn': new_asn}
    elif choice == '5':
        offset = Prompt.ask("EVI offset (+ or -)", default="0")
        try:
            evi_offset = int(offset)
            return {'action': 'mirror', 'transform_rd': True, 'evi_offset': evi_offset}
        except ValueError:
            console.print("[yellow]Invalid offset, using 0[/yellow]")
            return {'action': 'mirror', 'transform_rd': True}
    
    return {'action': 'mirror', 'transform_rd': True}


def _edit_attached_interfaces(
    mirror: 'ConfigMirror',
    services: List[Dict],
    service_type: str,
    target_hostname: str,
    analysis: dict
) -> Dict[str, Any]:
    """View and remap interfaces attached to services."""
    from rich.table import Table
    from rich import box
    
    console.print(f"\n[bold]Attached Interfaces[/bold]")
    
    # Collect all unique interfaces
    all_interfaces = set()
    for svc in services:
        all_interfaces.update(svc.get('interfaces', []))
    
    if not all_interfaces:
        console.print("[dim]No interfaces attached to services.[/dim]")
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
        return {'action': 'mirror', 'transform_rd': True}
    
    # Get interface types (PWHE vs L2-AC)
    pwhe_ifaces = [i for i in all_interfaces if i.startswith('ph')]
    l2ac_ifaces = [i for i in all_interfaces if not i.startswith('ph')]
    
    # Show interface summary
    console.print(f"\n[bold]Interface Summary:[/bold]")
    console.print(f"  Total: {len(all_interfaces)}")
    if pwhe_ifaces:
        console.print(f"  PWHE: {len(pwhe_ifaces)} (e.g., {pwhe_ifaces[0]}...)")
    if l2ac_ifaces:
        console.print(f"  L2-AC: {len(l2ac_ifaces)} (e.g., {l2ac_ifaces[0] if l2ac_ifaces else 'none'}...)")
    
    # Get parent interfaces (physical ports)
    parent_ifaces = set()
    for iface in all_interfaces:
        if '.' in iface:
            parent_ifaces.add(iface.split('.')[0])
        else:
            parent_ifaces.add(iface)
    
    console.print(f"  Parent interfaces: {len(parent_ifaces)}")
    
    # Load target LLDP neighbors
    lldp_neighbors = _load_target_lldp_neighbors(target_hostname)
    
    if lldp_neighbors:
        console.print(f"\n[bold]Target LLDP Neighbors ({len(lldp_neighbors)} available):[/bold]")
        lldp_table = Table(box=box.SIMPLE, show_header=True)
        lldp_table.add_column("Local Interface", style="cyan")
        lldp_table.add_column("Neighbor", style="yellow")
        lldp_table.add_column("Remote Port", style="green")
        
        for n in lldp_neighbors[:10]:
            lldp_table.add_row(
                n.get('local_interface', '?'),
                n.get('neighbor_name', '?'),
                n.get('remote_interface', '?')
            )
        if len(lldp_neighbors) > 10:
            lldp_table.add_row(f"... +{len(lldp_neighbors) - 10} more", "", "")
        
        console.print(lldp_table)
    else:
        console.print("[yellow]⚠ No LLDP neighbors available on target.[/yellow]")
    
    # Options
    console.print(f"\n[bold]Options:[/bold]")
    console.print("  [1] Keep interface names (copy as-is)")
    console.print("  [2] Remap parent interfaces (use LLDP to map)")
    console.print("  [B] Back")
    
    choice = Prompt.ask("Select", choices=['1', '2', 'b', 'B'], default='1').lower()
    
    if choice == 'b':
        return None
    elif choice == '1':
        return {'action': 'mirror', 'transform_rd': True, 'remap_interfaces': False}
    elif choice == '2':
        # Interactive remapping
        mapping = _interactive_interface_mapping(parent_ifaces, lldp_neighbors)
        if mapping:
            return {'action': 'mirror', 'transform_rd': True, 'remap_interfaces': True, 'interface_mapping': mapping}
        return None
    
    return {'action': 'mirror', 'transform_rd': True}


def _interactive_interface_mapping(parent_ifaces: set, lldp_neighbors: List[Dict]) -> Optional[Dict[str, str]]:
    """Interactive wizard to map source parent interfaces to target interfaces."""
    from rich.table import Table
    from rich import box
    
    console.print(f"\n[bold]Interface Mapping Wizard[/bold]")
    console.print("[dim]Map source parent interfaces to target's available interfaces[/dim]")
    
    # Build list of target interfaces from LLDP
    target_ifaces = [n.get('local_interface', '') for n in lldp_neighbors if n.get('local_interface')]
    
    if not target_ifaces:
        console.print("[yellow]⚠ No target interfaces available for mapping.[/yellow]")
        return None
    
    mapping = {}
    source_list = sorted(parent_ifaces)
    
    console.print(f"\n[dim]Source interfaces to map: {len(source_list)}[/dim]")
    console.print(f"[dim]Target interfaces available: {len(target_ifaces)}[/dim]")
    
    # Options
    console.print(f"\n[bold]Mapping Mode:[/bold]")
    console.print("  [1] Auto-map by index (source[0] → target[0], etc.)")
    console.print("  [2] Manual mapping (select each interface)")
    console.print("  [B] Cancel")
    
    mode = Prompt.ask("Select", choices=['1', '2', 'b', 'B'], default='1').lower()
    
    if mode == 'b':
        return None
    elif mode == '1':
        # Auto-map by index
        for i, src in enumerate(source_list):
            if i < len(target_ifaces):
                mapping[src] = target_ifaces[i]
        console.print(f"[green]✓ Auto-mapped {len(mapping)} interfaces[/green]")
    elif mode == '2':
        # Manual mapping
        console.print("\n[dim]For each source interface, enter target interface (or press Enter to skip)[/dim]")
        for src in source_list[:20]:  # Limit to first 20
            target = Prompt.ask(f"  {src} →", default="")
            if target and target.lower() != 'b':
                mapping[src] = target
        if len(source_list) > 20:
            console.print(f"[yellow]Note: Only mapped first 20 interfaces. {len(source_list) - 20} remaining will use original names.[/yellow]")
    
    if mapping:
        # Show mapping summary
        console.print(f"\n[bold]Mapping Summary:[/bold]")
        map_table = Table(box=box.SIMPLE)
        map_table.add_column("Source", style="cyan")
        map_table.add_column("→", style="dim")
        map_table.add_column("Target", style="green")
        for src, tgt in list(mapping.items())[:10]:
            map_table.add_row(src, "→", tgt)
        if len(mapping) > 10:
            map_table.add_row(f"... +{len(mapping) - 10} more", "", "")
        console.print(map_table)
    
    return mapping if mapping else None


def _add_essential_interfaces(
    mirror: 'ConfigMirror',
    services: List[Dict],
    service_type: str,
    target_hostname: str,
    analysis: dict
) -> Dict[str, Any]:
    """Add essential interfaces that services depend on (when interfaces were skipped)."""
    from rich.table import Table
    from rich import box
    
    console.print(f"\n[bold yellow]━━━ Add Essential Interfaces ━━━[/bold yellow]")
    console.print("[dim]Services need interfaces to function. Adding essential interfaces.[/dim]")
    
    # Collect all unique interfaces needed
    needed_interfaces = set()
    for svc in services:
        needed_interfaces.update(svc.get('interfaces', []))
    
    if not needed_interfaces:
        console.print("[dim]No interfaces needed by services.[/dim]")
        return {'action': 'mirror', 'transform_rd': True}
    
    # Get parent interfaces
    parent_ifaces = set()
    sub_ifaces = set()
    for iface in needed_interfaces:
        if '.' in iface:
            parent_ifaces.add(iface.split('.')[0])
            sub_ifaces.add(iface)
        else:
            parent_ifaces.add(iface)
    
    console.print(f"\n[bold]Essential Interfaces Summary:[/bold]")
    console.print(f"  Total needed: {len(needed_interfaces)}")
    console.print(f"  Parent interfaces: {len(parent_ifaces)}")
    console.print(f"  Sub-interfaces: {len(sub_ifaces)}")
    
    # Load LLDP neighbors
    lldp_neighbors = _load_target_lldp_neighbors(target_hostname)
    
    console.print(f"\n[bold]Target LLDP Neighbors ({len(lldp_neighbors)} available):[/bold]")
    
    if lldp_neighbors:
        lldp_table = Table(box=box.SIMPLE, show_header=True)
        lldp_table.add_column("#", style="dim", width=4)
        lldp_table.add_column("Local Interface", style="cyan", width=20)
        lldp_table.add_column("Neighbor", style="yellow", width=20)
        lldp_table.add_column("Remote Port", style="green", width=20)
        
        for i, n in enumerate(lldp_neighbors[:15], 1):
            lldp_table.add_row(
                str(i),
                n.get('local_interface', '?'),
                n.get('neighbor_name', '?'),
                n.get('remote_interface', '?')
            )
        if len(lldp_neighbors) > 15:
            lldp_table.add_row("", f"... +{len(lldp_neighbors) - 15} more", "", "")
        
        console.print(lldp_table)
    else:
        console.print("[yellow]⚠ No LLDP neighbors found on target.[/yellow]")
    
    # Options for adding interfaces
    console.print(f"\n[bold]Options:[/bold]")
    console.print("  [1] Copy interface config from source (keep names)")
    console.print("  [2] Map parent interfaces to target LLDP neighbors")
    console.print("  [3] Skip interfaces (services will have no connectivity)")
    console.print("  [B] Back")
    
    choice = Prompt.ask("Select", choices=['1', '2', '3', 'b', 'B'], default='1').lower()
    
    if choice == 'b':
        return None
    elif choice == '1':
        console.print(f"[green]✓ Will add {len(needed_interfaces)} essential interfaces from source[/green]")
        return {
            'action': 'mirror',
            'transform_rd': True,
            'add_essential_interfaces': True,
            'interface_list': list(needed_interfaces),
            'remap_interfaces': False
        }
    elif choice == '2':
        # Map parent interfaces to LLDP
        mapping = _interactive_interface_mapping(parent_ifaces, lldp_neighbors)
        if mapping:
            console.print(f"[green]✓ Will add interfaces with parent mapping[/green]")
            return {
                'action': 'mirror',
                'transform_rd': True,
                'add_essential_interfaces': True,
                'interface_list': list(needed_interfaces),
                'remap_interfaces': True,
                'interface_mapping': mapping
            }
        return None
    elif choice == '3':
        console.print("[yellow]⚠ Services will have no interface connectivity on target[/yellow]")
        return {'action': 'mirror', 'transform_rd': True, 'add_essential_interfaces': False}
    
    return {'action': 'mirror', 'transform_rd': True}


def _get_subsection_info(key: str, hierarchy_data: dict, config: str, hierarchy_key: str) -> str:
    """
    Get a brief info string for a sub-section showing count/status.
    
    Args:
        key: Sub-section key (wan, pwhe, fxc, etc.)
        hierarchy_data: Hierarchy analysis data dict
        config: Raw config text
        hierarchy_key: Parent hierarchy key (interfaces, network-services, etc.)
    
    Returns:
        Brief info string like "4 interfaces" or "N/A"
    """
    if hierarchy_key == 'interfaces':
        if key == 'wan':
            count = hierarchy_data.get('wan_count', 0)
            if count == 0:
                # Try to count from config
                wan_ifaces = get_wan_interfaces(config) if config else []
                count = len(wan_ifaces)
            return f"{count} WANs" if count > 0 else "None"
        elif key == 'pwhe':
            parent_count = hierarchy_data.get('pwhe_count', 0)
            sub_count = hierarchy_data.get('pwhe_sub_count', 0)
            if parent_count > 0 or sub_count > 0:
                return f"{parent_count}+{sub_count} PWHE"
            return "None"
        elif key == 'l2ac':
            count = hierarchy_data.get('l2ac_count', 0)
            return f"{count} L2-AC" if count > 0 else "None"
        elif key == 'lo0':
            lo0_ip = get_lo0_ip_from_config(config) if config else None
            return lo0_ip if lo0_ip else "Not set"
        elif key == 'bundles':
            count = hierarchy_data.get('bundle_count', 0)
            return f"{count} bundles" if count > 0 else "None"
    elif hierarchy_key == 'network-services':
        if key == 'fxc':
            count = hierarchy_data.get('fxc', {}).get('count', 0)
            return f"{count} FXC" if count > 0 else "None"
        elif key == 'vpws':
            count = hierarchy_data.get('vpws', {}).get('count', 0)
            return f"{count} VPWS" if count > 0 else "None"
        elif key == 'vpls':
            count = hierarchy_data.get('vpls', {}).get('count', 0)
            return f"{count} VPLS" if count > 0 else "None"
        elif key == 'vrf':
            count = hierarchy_data.get('vrf', {}).get('count', 0)
            return f"{count} VRFs" if count > 0 else "None"
        elif key == 'mh':
            count = hierarchy_data.get('mh', {}).get('count', 0)
            return f"{count} ESIs" if count > 0 else "None"
    elif hierarchy_key == 'protocols':
        if key == 'isis':
            count = hierarchy_data.get('isis_instances', 0)
            has_isis = hierarchy_data.get('has_isis', False)
            if count > 0:
                return f"{count} instances"
            return "Configured" if has_isis else "None"
        elif key == 'bgp':
            neighbors = hierarchy_data.get('bgp_neighbors', 0)
            has_bgp = hierarchy_data.get('has_bgp', False)
            if neighbors > 0:
                return f"{neighbors} neighbors"
            return "Configured" if has_bgp else "None"
        elif key == 'ldp':
            return "Configured" if hierarchy_data.get('has_ldp') else "None"
        elif key == 'lldp':
            return "Configured" if hierarchy_data.get('has_lldp') else "None"
        elif key == 'bfd':
            return "Configured" if hierarchy_data.get('has_bfd') else "None"
        elif key == 'lacp':
            return "Configured" if hierarchy_data.get('has_lacp') else "None"
    elif hierarchy_key == 'system':
        if key == 'hostname':
            # Extract hostname from config
            import re
            match = re.search(r'^\s*hostname\s+(\S+)', config or '', re.MULTILINE)
            return match.group(1) if match else "Not set"
        elif key in ('ntp', 'logging', 'aaa', 'profile'):
            return "Configured" if config and key in config.lower() else "None"
    
    return "N/A"


def _edit_hierarchy_subsections(
    mirror: ConfigMirror,
    hierarchy_key: str,
    hierarchy_name: str,
    source_hostname: str,
    target_hostname: str,
    analysis: dict
) -> Optional[Dict[str, Any]]:
    """
    Allow editing sub-sections within a hierarchy using per-subsection K/E/D/S.
    
    Returns dict of sub-section selections, or None to go back.
    """
    from rich.table import Table
    from rich import box
    
    console.print(f"\n[bold yellow]━━━ Edit {hierarchy_name} Sub-sections ━━━[/bold yellow]")
    
    # Define sub-sections based on hierarchy
    sub_sections = []
    
    if hierarchy_key == 'interfaces':
        h = analysis.get('hierarchies', {}).get('interfaces', {})
        # Only include sub-sections that have content
        sub_sections = []
        
        wan_count = h.get('wan_count', 0)
        if wan_count > 0:
            sub_sections.append(('wan', 'WAN Interfaces', f"{wan_count} interfaces", 'target', 'WAN IPs preserved from target'))
        
        pwhe_count = h.get('pwhe_count', 0)
        pwhe_sub = h.get('pwhe_sub_count', 0)
        if pwhe_count > 0 or pwhe_sub > 0:
            sub_sections.append(('pwhe', 'PWHE Interfaces', f"{pwhe_count} parent + {pwhe_sub} sub", 'source', 'Mirror from source'))
        
        l2ac_count = h.get('l2ac_count', 0)
        if l2ac_count > 0:
            sub_sections.append(('l2ac', 'L2-AC Interfaces', f"{l2ac_count} interfaces", 'source', 'Mirror from source'))
        
        # lo0 is always relevant (target has one)
        sub_sections.append(('lo0', 'Loopback (lo0)', "Target's lo0 preserved", 'target', 'Keep target loopback'))
        
        bundle_count = h.get('bundle_count', 0)
        if bundle_count > 0:
            sub_sections.append(('bundles', 'Bundles/LACP', f"{bundle_count} bundles", 'target', 'Target bundles preserved'))
    elif hierarchy_key == 'network-services':
        ns = analysis.get('hierarchies', {}).get('network-services', {})
        # Only include sub-sections that have content
        sub_sections = []
        
        fxc_count = ns.get('fxc', {}).get('count', 0)
        if fxc_count > 0:
            sub_sections.append(('fxc', 'EVPN-VPWS-FXC', f"{fxc_count} instances", 'source', 'RD will be transformed'))
        
        vpws_count = ns.get('vpws', {}).get('count', 0)
        if vpws_count > 0:
            sub_sections.append(('vpws', 'EVPN-VPWS', f"{vpws_count} instances", 'source', 'RD will be transformed'))
        
        vpls_count = ns.get('vpls', {}).get('count', 0)
        if vpls_count > 0:
            sub_sections.append(('vpls', 'EVPN-VPLS', f"{vpls_count} instances", 'source', 'RD will be transformed'))
        
        vrf_count = ns.get('vrf', {}).get('count', 0)
        if vrf_count > 0:
            sub_sections.append(('vrf', 'L3VPN/VRF', f"{vrf_count} instances", 'source', 'Mirror VRFs'))
        
        mh_count = ns.get('mh', {}).get('count', 0)
        if mh_count > 0:
            sub_sections.append(('mh', 'Multihoming', f"{mh_count} ESIs", 'source', 'ESI config'))
    elif hierarchy_key == 'protocols':
        p = analysis.get('hierarchies', {}).get('protocols', {})
        # Only include sub-sections that have content
        sub_sections = []
        
        isis_count = p.get('isis_instances', 0)
        if isis_count > 0 or p.get('has_isis'):
            sub_sections.append(('isis', 'IS-IS', f"{isis_count} instances" if isis_count else "configured", 'source', 'IGP routing'))
        
        if p.get('has_bgp') or p.get('bgp_neighbors', 0) > 0:
            sub_sections.append(('bgp', 'BGP', 'Neighbors, policies', 'source', 'BGP config'))
        
        if p.get('has_ldp'):
            sub_sections.append(('ldp', 'LDP', 'Label distribution', 'source', 'MPLS labels'))
        
        # LLDP is usually present - check if configured
        if p.get('has_lldp'):
            sub_sections.append(('lldp', 'LLDP', 'Neighbor discovery', 'target', 'Keep target LLDP'))
        
        if p.get('has_bfd'):
            sub_sections.append(('bfd', 'BFD', 'Failure detection', 'source', 'BFD timers'))
        
        if p.get('has_lacp'):
            sub_sections.append(('lacp', 'LACP', 'Bundle protocols', 'target', 'Keep target LACP'))
    elif hierarchy_key == 'system':
        sub_sections = [
            ('hostname', 'Hostname', f"→ {target_hostname}", 'transform', 'Will be transformed'),
            ('ntp', 'NTP', 'Time sync servers', 'source', 'Mirror NTP'),
            ('logging', 'Logging', 'Syslog config', 'source', 'Mirror logging'),
            ('aaa', 'AAA', 'Authentication', 'source', 'Mirror AAA'),
            ('profile', 'System Profile', analysis.get('device_type', 'unknown'), 'source', 'Device profile'),
        ]
    else:
        # Generic handling for other hierarchies
        console.print(f"[dim]No sub-sections defined for {hierarchy_name}. Will mirror entire section.[/dim]")
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
        return {'include_all': True}
    
    # Check if any sub-sections were found
    if not sub_sections:
        console.print(f"[dim]No content found in {hierarchy_name}. Will mirror entire section.[/dim]")
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
        return {'include_all': True}
    
    # Track selections with action type
    selections = {}
    for key, name, _, source, _ in sub_sections:
        # Default: keep from source for 'source' items, keep from target for 'target' items
        if source == 'target':
            selections[key] = 'keep_target'
        elif source == 'transform':
            selections[key] = 'transform'
        else:
            selections[key] = 'mirror'
    
    # Track if interfaces were skipped (needed for essential interfaces check)
    interfaces_skipped = False
    
    # Process each sub-section with inline prompts
    # For services (fxc, vpws, vpls, vrf), add [E]dit option
    service_keys = ('fxc', 'vpws', 'vpls', 'vrf')
    
    console.print("\n[dim]For each sub-section:[/dim]")
    console.print("[dim]  [K]eep=[green]Use source[/green] | [E]dit=[yellow]Custom value[/yellow] [cyan](default)[/cyan] | [S]kip=[dim]Keep target's[/dim][/dim]")
    console.print()
    
    for key, name, details, source, note in sub_sections:
        # Build prompt
        source_indicator = ""
        default_action = 'e'  # Default to Edit for most flexibility
        
        if source == 'target':
            source_indicator = "[green][target][/green]"
            default_action = 's'  # Skip = keep target's
        elif source == 'transform':
            source_indicator = "[yellow][transform][/yellow]"
            default_action = 'e'  # Edit to customize transformation
        else:
            source_indicator = "[cyan][source][/cyan]"
            default_action = 'e'  # Edit to customize source values
        
        # Show special hints for certain sub-sections
        if key == 'wan':
            # Check if target has existing WANs
            target_wan_count = analysis.get('target_hierarchies', {}).get('interfaces', {}).get('wan_count', 0)
            if target_wan_count == 0:
                # Try to get from target config directly
                target_wans = get_wan_interfaces(mirror.target_config)
                target_wan_count = len(target_wans) if target_wans else 0
            
            console.print(f"\n  [bold cyan]{name}[/bold cyan] ({details})")
            console.print(f"    [dim][K]eep → Launch WAN mapping wizard (select target interfaces + IPs)[/dim]")
            console.print(f"    [dim][E]dit → Configure WAN mapping options[/dim]")
            if target_wan_count > 0:
                console.print(f"    [dim][S]kip → Keep target's existing WAN config ({target_wan_count} WANs)[/dim]")
            else:
                console.print(f"    [dim][S]kip → No WAN config (target has none)[/dim]")
            prompt_text = "    Action"
            # If target has no WANs, default to 'k' (mapping wizard)
            if target_wan_count == 0:
                default_action = 'k'
            else:
                default_action = 'e'  # Edit is default when options available
        elif key == 'lo0':
            # Check if target has existing lo0
            target_lo0 = get_lo0_ip_from_config(mirror.target_config)
            source_lo0 = get_lo0_ip_from_config(mirror.source_config)
            
            console.print(f"\n  [bold cyan]{name}[/bold cyan] ({details})")
            if source_lo0:
                console.print(f"    [dim][K]eep → Use source loopback: {source_lo0}[/dim]")
            else:
                console.print(f"    [dim][K]eep → Source has no loopback[/dim]")
            console.print(f"    [dim][E]dit → Enter custom loopback IP[/dim]")
            if target_lo0:
                console.print(f"    [dim][S]kip → Keep target's: {target_lo0}[/dim]")
            else:
                console.print(f"    [dim][S]kip → Keep target's (none configured)[/dim]")
            prompt_text = "    Action"
            # Default to edit if neither source nor target has loopback
            if not source_lo0 and not target_lo0:
                default_action = 'e'
        # For service sub-sections, show Edit option with service-specific hints
        elif key in service_keys:
            # Get service count and attached interfaces
            ns = analysis.get('hierarchies', {}).get('network-services', {})
            svc_data = ns.get(key, {})
            svc_count = svc_data.get('count', 0)
            svc_instances = svc_data.get('instances', [])
            
            # Count attached interfaces
            total_ifaces = sum(len(svc.get('interfaces', [])) for svc in svc_instances)
            
            console.print(f"\n  [bold cyan]{name}[/bold cyan] ({details})")
            console.print(f"    [dim][K]eep → Mirror all {svc_count} services (RD transformed)[/dim]")
            console.print(f"    [dim][E]dit → Edit knobs, range, or attached interfaces ({total_ifaces} attached)[/dim]")
            console.print(f"    [dim][S]kip → Keep target's {key.upper()} config[/dim]")
            prompt_text = "    Action"
            default_action = 'e'  # Edit is default for services
        else:
            prompt_text = f"  {name} ({details}) {source_indicator}"
        
        # Determine which choices to offer - ALL sub-sections get [E]dit option now
        # Removed [T]arget - redundant with [S]kip
        action_choices = ['k', 'K', 'e', 'E', 's', 'S', 'b', 'B']
        
        action = Prompt.ask(
            prompt_text,
            choices=action_choices,
            default=default_action
        ).lower()
        
        if action == 'b':
            return None
        elif action == 'k':
            # For WAN interfaces, launch WAN mapping wizard
            if key == 'wan':
                # Get source WAN interfaces
                source_wans = get_wan_interfaces(mirror.source_config)
                console.print(f"\n  [dim]Found {len(source_wans)} source WAN interfaces: {source_wans[:5]}{'...' if len(source_wans) > 5 else ''}[/dim]")
                if source_wans:
                    # Create a minimal state object for the wizard
                    class MiniState:
                        def __init__(self, src_cfg, tgt_cfg, src_host, tgt_host):
                            self.source_config = src_cfg
                            self.target_config = tgt_cfg
                            self.source_hostname = src_host
                            self.target_hostname = tgt_host
                    
                    mini_state = MiniState(mirror.source_config, mirror.target_config, source_hostname, target_hostname)
                    mapping_result = wan_interface_mapping_wizard(mini_state, source_wans)
                    
                    if mapping_result:
                        if mapping_result.action == StepAction.SKIP:
                            selections[key] = 'skip'
                        else:
                            selections[key] = {'action': 'map', 'mapping': mapping_result}
                    else:
                        # User cancelled, keep target's
                        selections[key] = 'keep_target'
                else:
                    selections[key] = 'keep_target'
            # For service interfaces, launch mapping wizard
            elif key in ('pwhe', 'l2ac', 'bundles'):
                # Get source interface list
                source_ifaces = _get_source_interfaces_for_mapping(mirror, key, analysis)
                if source_ifaces:
                    # Create a minimal state object for the wizard
                    class MiniState:
                        def __init__(self, src_cfg, tgt_cfg, src_host, tgt_host):
                            self.source_config = src_cfg
                            self.target_config = tgt_cfg
                            self.source_hostname = src_host
                            self.target_hostname = tgt_host
                    
                    mini_state = MiniState(mirror.source_config, mirror.target_config, source_hostname, target_hostname)
                    mapping_result = service_interface_mapping_wizard(mini_state, key, source_ifaces, analysis)
                    
                    if mapping_result:
                        if mapping_result.get('action') == 'skip':
                            selections[key] = 'skip'
                        elif mapping_result.get('action') == 'copy':
                            selections[key] = 'mirror'
                        elif mapping_result.get('action') == 'map':
                            selections[key] = {'action': 'map', 'mapping': mapping_result}
                    else:
                        # User cancelled, skip
                        selections[key] = 'skip'
                else:
                    selections[key] = 'mirror'
            else:
                selections[key] = 'mirror'
        elif action == 'e':
            # Edit WAN interfaces - Quick edit with smart options
            if key == 'wan':
                import re
                source_wans = get_wan_interfaces(mirror.source_config)
                target_wans = get_wan_interfaces(mirror.target_config)
                
                # Parse source WAN IPs
                source_wan_ips = {}
                for wan in source_wans:
                    ip_match = re.search(
                        rf'^\s+{re.escape(wan)}\s*\n(?:.*?\n)*?\s+ipv4-address\s+(\d+\.\d+\.\d+\.\d+(?:/\d+)?)',
                        mirror.source_config, re.MULTILINE
                    )
                    if ip_match:
                        source_wan_ips[wan] = ip_match.group(1)
                
                # Load target LLDP neighbors
                target_lldp_count = 0
                target_lldp = []
                try:
                    import json
                    from pathlib import Path
                    target_op_file = Path(f"/home/dn/SCALER/db/configs/{target_hostname}/operational.json")
                    if target_op_file.exists():
                        with open(target_op_file) as f:
                            target_op = json.load(f)
                            target_lldp = target_op.get('lldp_neighbors', [])
                            target_lldp_count = len(target_lldp)
                except:
                    pass
                
                # Detect bundle members from target config
                # Parse which physical interfaces are bundle members
                bundle_members = {}  # {interface: bundle_id}
                bundles_detected = set()
                target_config = mirror.target_config
                
                # Find all bundle-id assignments in target config
                bundle_id_matches = re.findall(
                    r'^\s+(ge\d+-\d+/\d+/\d+)\s*\n(?:.*?\n)*?\s+bundle-id\s+(\d+)',
                    target_config, re.MULTILINE
                )
                for iface, bid in bundle_id_matches:
                    bundle_members[iface] = f"bundle-{bid}"
                    bundles_detected.add(f"bundle-{bid}")
                
                # Check which LLDP interfaces are bundle members
                lldp_bundle_members = []
                lldp_standalone = []
                for n in target_lldp:
                    iface = n.get('local_interface', '')
                    if iface in bundle_members:
                        lldp_bundle_members.append({
                            'interface': iface,
                            'bundle': bundle_members[iface],
                            'neighbor': n.get('neighbor_device', 'unknown'),
                            'remote_port': n.get('neighbor_port', '')
                        })
                    else:
                        lldp_standalone.append(n)
                
                # Show WAN summary with smart suggestions
                console.print(f"\n  [bold cyan]WAN Interface Configuration[/bold cyan]")
                console.print(f"    Source: {len(source_wans)} WAN interfaces")
                for wan in source_wans[:4]:
                    ip = source_wan_ips.get(wan, 'no IP')
                    console.print(f"      • {wan} ({ip})")
                if len(source_wans) > 4:
                    console.print(f"      [dim]... and {len(source_wans) - 4} more[/dim]")
                
                console.print(f"    Target: {len(target_wans)} WAN interfaces")
                
                # Show LLDP with bundle detection
                if target_lldp_count > 0:
                    if lldp_bundle_members:
                        console.print(f"    Target LLDP: {target_lldp_count} neighbors")
                        console.print(f"    [yellow]⚠ Bundle Members Detected:[/yellow]")
                        for m in lldp_bundle_members:
                            console.print(f"      • {m['interface']} → [cyan]{m['bundle']}[/cyan] (neighbor: {m['neighbor']})")
                        if bundles_detected:
                            console.print(f"    [green]Available Bundles:[/green] {', '.join(sorted(bundles_detected))}")
                        if lldp_standalone:
                            console.print(f"    [dim]Standalone LLDP: {len(lldp_standalone)} interfaces[/dim]")
                    else:
                        console.print(f"    Target LLDP: {target_lldp_count} standalone neighbors")
                else:
                    console.print(f"    Target LLDP: 0 neighbors available")
                
                console.print(f"\n    [cyan]Quick Options:[/cyan]")
                
                # Build choices based on context
                choices_map = {}
                choice_num = 1
                
                if target_wans:
                    console.print(f"      [{choice_num}] Keep target's WAN config ({len(target_wans)} interfaces) [dim](recommended)[/dim]")
                    choices_map[str(choice_num)] = 'keep_target'
                    choice_num += 1
                
                console.print(f"      [{choice_num}] Copy source WANs as-is ({len(source_wans)} interfaces)")
                choices_map[str(choice_num)] = 'copy_source'
                default_choice = str(choice_num)
                choice_num += 1
                
                # If bundles detected, offer to create sub-interfaces on bundles
                if bundles_detected:
                    bundle_list = ', '.join(sorted(bundles_detected))
                    console.print(f"      [{choice_num}] [green]Create sub-interfaces on bundle(s)[/green] ({bundle_list})")
                    choices_map[str(choice_num)] = 'use_bundles'
                    default_choice = str(choice_num)  # Recommend bundle option
                    choice_num += 1
                
                if target_lldp_count > 0:
                    console.print(f"      [{choice_num}] Map source WANs to target interfaces (using LLDP)")
                    choices_map[str(choice_num)] = 'full_wizard'
                    choice_num += 1
                
                console.print(f"      [S] Skip WAN configuration")
                
                # Build valid choices list
                valid_choices = list(choices_map.keys()) + ['s', 'S', 'b', 'B']
                
                wan_choice = Prompt.ask(
                    "    Select [B]ack",
                    choices=valid_choices,
                    default=default_choice
                ).lower()
                
                if wan_choice == 'b':
                    return None
                elif wan_choice == 's':
                    selections[key] = 'skip'
                    console.print(f"    [dim]✓ WAN configuration skipped[/dim]")
                elif choices_map.get(wan_choice) == 'keep_target':
                    selections[key] = 'keep_target'
                    console.print(f"    [green]✓ Keep target's {len(target_wans)} WAN interfaces[/green]")
                elif choices_map.get(wan_choice) == 'copy_source':
                    selections[key] = 'mirror'
                    console.print(f"    [green]✓ Copy {len(source_wans)} source WAN interfaces[/green]")
                elif choices_map.get(wan_choice) == 'use_bundles':
                    # Create sub-interfaces on detected bundles
                    console.print(f"\n  [bold cyan]Bundle Sub-Interface Configuration[/bold cyan]")
                    console.print(f"    [dim]Source has {len(source_wans)} WAN sub-interfaces[/dim]")
                    console.print(f"    [dim]Target has bundles: {', '.join(sorted(bundles_detected))}[/dim]")
                    
                    # Show what will be created
                    console.print(f"\n    [yellow]This will create sub-interfaces on target bundles:[/yellow]")
                    bundle_list = sorted(bundles_detected)
                    primary_bundle = bundle_list[0] if bundle_list else 'bundle-100'
                    
                    # Map source sub-interface VLANs to bundle sub-interfaces
                    sub_if_mappings = []
                    for src_wan in source_wans[:4]:
                        # Extract VLAN from source (e.g., ge100-18/0/0.14 → 14)
                        vlan_match = re.search(r'\.(\d+)$', src_wan)
                        if vlan_match:
                            vlan = vlan_match.group(1)
                            src_ip = source_wan_ips.get(src_wan, 'no IP')
                            target_sub = f"{primary_bundle}.{vlan}"
                            sub_if_mappings.append({
                                'source': src_wan,
                                'target': target_sub,
                                'vlan': vlan,
                                'source_ip': src_ip
                            })
                            console.print(f"      {src_wan} → [green]{target_sub}[/green] ({src_ip})")
                    
                    if len(source_wans) > 4:
                        console.print(f"      [dim]... and {len(source_wans) - 4} more[/dim]")
                    
                    # Confirm
                    confirm = Prompt.ask(
                        "\n    Create these bundle sub-interfaces? [Y/n/B]ack",
                        choices=['y', 'Y', 'n', 'N', 'b', 'B'],
                        default='y'
                    ).lower()
                    
                    if confirm == 'b':
                        return None
                    elif confirm == 'n':
                        selections[key] = 'skip'
                        console.print(f"    [dim]✓ WAN configuration skipped[/dim]")
                    else:
                        # Store the bundle mapping for config generation
                        selections[key] = {
                            'action': 'bundle_sub_interfaces',
                            'bundle': primary_bundle,
                            'mappings': sub_if_mappings,
                            'source_wans': source_wans,
                            'source_wan_ips': source_wan_ips
                        }
                        console.print(f"    [green]✓ Will create {len(source_wans)} sub-interfaces on {primary_bundle}[/green]")
                elif choices_map.get(wan_choice) == 'full_wizard':
                    # Launch full mapping wizard
                    console.print(f"\n  [dim]Launching WAN mapping wizard...[/dim]")
                    class MiniState:
                        def __init__(self, src_cfg, tgt_cfg, src_host, tgt_host):
                            self.source_config = src_cfg
                            self.target_config = tgt_cfg
                            self.source_hostname = src_host
                            self.target_hostname = tgt_host
                    
                    mini_state = MiniState(mirror.source_config, mirror.target_config, source_hostname, target_hostname)
                    mapping_result = wan_interface_mapping_wizard(mini_state, source_wans)
                    
                    if mapping_result:
                        if mapping_result.action == StepAction.SKIP:
                            selections[key] = 'skip'
                        else:
                            selections[key] = {'action': 'map', 'mapping': mapping_result}
                    else:
                        # User cancelled, keep target's
                        selections[key] = 'keep_target'
                else:
                    # Default: copy source
                    selections[key] = 'mirror'
            
            # Edit service interfaces (pwhe, l2ac, bundles)
            elif key in ('pwhe', 'l2ac', 'bundles'):
                # Get source interface list
                source_ifaces = _get_source_interfaces_for_mapping(mirror, key, analysis)
                if source_ifaces:
                    # Create a minimal state object for the wizard
                    class MiniState:
                        def __init__(self, src_cfg, tgt_cfg, src_host, tgt_host):
                            self.source_config = src_cfg
                            self.target_config = tgt_cfg
                            self.source_hostname = src_host
                            self.target_hostname = tgt_host
                    
                    mini_state = MiniState(mirror.source_config, mirror.target_config, source_hostname, target_hostname)
                    mapping_result = service_interface_mapping_wizard(mini_state, key, source_ifaces, analysis)
                    
                    if mapping_result:
                        if mapping_result.get('action') == 'skip':
                            selections[key] = 'skip'
                        elif mapping_result.get('action') == 'copy':
                            selections[key] = 'mirror'
                        elif mapping_result.get('action') == 'map':
                            selections[key] = {'action': 'map', 'mapping': mapping_result}
                    else:
                        # User cancelled, skip
                        selections[key] = 'skip'
                else:
                    selections[key] = 'mirror'
            
            # Edit wizard for services (fxc, vpws, vpls, vrf)
            elif key in service_keys:
                ns = analysis.get('hierarchies', {}).get('network-services', {})
                svc_data = ns.get(key, {})
                svc_instances = svc_data.get('instances', [])
                
                edit_result = _edit_service_knobs_wizard(
                    mirror, key, svc_instances, analysis, target_hostname, interfaces_skipped
                )
                
                if edit_result is None:
                    # User cancelled, default to mirror
                    selections[key] = 'mirror'
                elif edit_result.get('action') == 'keep_target':
                    selections[key] = 'keep_target'
                elif edit_result.get('action') == 'skip':
                    selections[key] = 'skip'
                else:
                    # Store the edit result with all its configuration
                    selections[key] = {'action': 'edit', 'config': edit_result}
            
            # Edit hostname
            elif key == 'hostname':
                source_hostname_val = _extract_hostname_from_config(mirror.source_config)
                target_hostname_val = _extract_hostname_from_config(mirror.target_config)
                
                console.print(f"\n  [bold cyan]Custom Hostname[/bold cyan]")
                console.print(f"    Source: [dim]{source_hostname_val or 'N/A'}[/dim]")
                console.print(f"    Target: [dim]{target_hostname_val or target_hostname}[/dim]")
                console.print(f"    [cyan]Suggestions:[/cyan]")
                console.print(f"      • {target_hostname} (keep target's)")
                console.print(f"      • {target_hostname}-NEW")
                console.print(f"      • {target_hostname}-BACKUP")
                console.print(f"      • {target_hostname}-MIRROR")
                
                custom_hostname = Prompt.ask(
                    "    Enter hostname [B]ack",
                    default=target_hostname
                )
                
                if custom_hostname.lower() == 'b':
                    return None
                
                # Validate hostname format
                import re
                if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$', custom_hostname):
                    console.print("[red]Invalid hostname format. Using target's value.[/red]")
                    selections[key] = 'keep_target'
                else:
                    selections[key] = {'action': 'custom_hostname', 'value': custom_hostname}
                    console.print(f"    [green]✓ Custom hostname: {custom_hostname}[/green]")
            
            # Edit loopback
            elif key == 'lo0':
                target_lo0 = get_lo0_ip_from_config(mirror.target_config)
                source_lo0 = get_lo0_ip_from_config(mirror.source_config)
                
                console.print(f"\n  [bold cyan]Custom Loopback IP[/bold cyan]")
                console.print(f"    Source lo0: [dim]{source_lo0 or 'N/A'}[/dim]")
                console.print(f"    Target lo0: [dim]{target_lo0 or 'N/A'}[/dim]")
                console.print(f"    [cyan]Suggestions:[/cyan]")
                
                suggestions = []
                if source_lo0:
                    suggestions.append(f"      [1] {source_lo0} (use source)")
                if target_lo0:
                    suggestions.append(f"      [2] {target_lo0} (keep target)")
                
                # Suggest next IP if source has one
                if source_lo0 and '.' in source_lo0:
                    try:
                        ip_part = source_lo0.split('/')[0]
                        octets = ip_part.split('.')
                        last_octet = int(octets[3])
                        next_ip = f"{'.'.join(octets[0:3])}.{last_octet + 1}/32"
                        suggestions.append(f"      [3] {next_ip} (next IP)")
                    except:
                        pass
                
                for sug in suggestions:
                    console.print(sug)
                
                custom_lo0 = Prompt.ask(
                    "    Enter loopback IP/mask [B]ack",
                    default=target_lo0 or source_lo0 or "1.1.1.1/32"
                )
                
                if custom_lo0.lower() == 'b':
                    return None
                
                # Validate IP format
                import re
                if not re.match(r'^\d+\.\d+\.\d+\.\d+(/\d+)?$', custom_lo0):
                    console.print("[red]Invalid IP format. Using target's value.[/red]")
                    selections[key] = 'keep_target'
                else:
                    # Normalize: add /32 if no mask
                    if '/' not in custom_lo0:
                        custom_lo0 += '/32'
                    selections[key] = {'action': 'set_lo0', 'ip': custom_lo0}
                    console.print(f"    [green]✓ Custom loopback: {custom_lo0}[/green]")
            
            # Edit NTP servers
            elif key == 'ntp':
                console.print(f"\n  [bold cyan]Custom NTP Configuration[/bold cyan]")
                console.print(f"    [cyan]Options:[/cyan]")
                console.print(f"      [K] Keep source NTP servers")
                console.print(f"      [T] Keep target NTP servers")
                console.print(f"      [C] Enter custom NTP servers")
                
                ntp_choice = Prompt.ask(
                    "    Select",
                    choices=['k', 'K', 't', 'T', 'c', 'C', 'b', 'B'],
                    default='t'
                ).lower()
                
                if ntp_choice == 'b':
                    return None
                elif ntp_choice == 'k':
                    selections[key] = 'mirror'
                elif ntp_choice == 't':
                    selections[key] = 'keep_target'
                else:
                    # Custom NTP servers
                    ntp_servers = Prompt.ask("    Enter NTP servers (comma-separated IPs)")
                    if ntp_servers:
                        selections[key] = {'action': 'custom_ntp', 'servers': [s.strip() for s in ntp_servers.split(',')]}
                        console.print(f"    [green]✓ Custom NTP servers configured[/green]")
                    else:
                        selections[key] = 'keep_target'
            
            # For other sub-sections, default to mirror
            else:
                console.print(f"\n  [yellow]Edit not yet implemented for {name}[/yellow]")
                console.print(f"  [dim]Defaulting to [K]eep (use source)[/dim]")
                Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
                selections[key] = 'mirror'
        elif action == 's':
            selections[key] = 'skip'
            # Track if interfaces sub-section was skipped
            if key in ('pwhe', 'l2ac', 'bundles'):
                interfaces_skipped = True
    
    # Show smart diff table summary in a styled panel
    from rich.console import Group
    from rich.text import Text
    
    diff_table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan", 
                       border_style="dim", padding=(0, 1))
    diff_table.add_column("Sub-section", style="cyan", width=18)
    diff_table.add_column("Source", style="green", width=16)
    diff_table.add_column("Target", style="yellow", width=16)
    diff_table.add_column("Action", style="bold", width=16)
    diff_table.add_column("Output", style="magenta", width=18)
    
    # Get target hierarchies for comparison
    target_h = analysis.get('target_hierarchies', {}).get(hierarchy_key, {})
    source_h = analysis.get('hierarchies', {}).get(hierarchy_key, {})
    
    for key, name, details, source_type, note in sub_sections:
        sel = selections.get(key, 'skip')
        
        # Get source and target counts for comparison
        source_info = _get_subsection_info(key, source_h, mirror.source_config, hierarchy_key)
        target_info = _get_subsection_info(key, target_h, mirror.target_config, hierarchy_key)
        
        # Determine action and output text
        if isinstance(sel, dict):
            action_type = sel.get('action', '')
            if action_type == 'map':
                mapping_info = sel.get('mapping', {})
                if hasattr(mapping_info, 'summary'):
                    summary = mapping_info.summary
                else:
                    summary = mapping_info.get('summary', 'Mapped')
                action_text = "[green]✎ Map[/green]"
                output_text = f"[green]{summary}[/green]"
            elif action_type == 'set_lo0':
                lo0_ip = sel.get('ip', '?')
                action_text = "[cyan]✎ Set IP[/cyan]"
                output_text = f"[cyan]{lo0_ip}[/cyan]"
            elif action_type == 'edit':
                # Service edit with knobs/interfaces
                edit_config = sel.get('config', {})
                edit_action = edit_config.get('action', 'mirror')
                if edit_config.get('add_essential_interfaces'):
                    iface_count = len(edit_config.get('interface_list', []))
                    action_text = "[yellow]✎ Edit+Ifaces[/yellow]"
                    output_text = f"[yellow]{source_info} +{iface_count} ifaces[/yellow]"
                elif edit_config.get('remap_interfaces'):
                    action_text = "[yellow]✎ Edit+Remap[/yellow]"
                    output_text = f"[yellow]{source_info} remapped[/yellow]"
                elif edit_action == 'range':
                    selected = edit_config.get('selected_services', [])
                    action_text = "[yellow]✎ Edit range[/yellow]"
                    output_text = f"[yellow]{len(selected)} selected[/yellow]"
                else:
                    action_text = "[yellow]✎ Edit[/yellow]"
                    output_text = f"[yellow]{source_info}[/yellow]"
            else:
                action_text = "[green]✓ Configured[/green]"
                output_text = "[green]Custom[/green]"
        elif sel == 'mirror':
            action_text = "[green]← Mirror[/green]"
            output_text = f"[green]{source_info}[/green]"
        elif sel == 'keep_target':
            action_text = "[cyan]→ Keep target[/cyan]"
            output_text = f"[cyan]{target_info}[/cyan]"
        elif sel == 'transform':
            action_text = "[yellow]↔ Transform[/yellow]"
            output_text = f"[yellow]Source→Target[/yellow]"
        else:
            # Skip = keep target's config
            action_text = "[cyan]→ Keep target[/cyan]"
            output_text = f"[cyan]{target_info}[/cyan]"
        
        diff_table.add_row(name, source_info, target_info, action_text, output_text)
    
    # Count actions for summary
    mirror_count = sum(1 for s in selections.values() if s == 'mirror' or (isinstance(s, dict) and s.get('action') in ('mirror', 'edit', 'map')))
    keep_count = sum(1 for s in selections.values() if s == 'keep_target' or s == 'skip')
    
    # Build explanation content
    explanation = Text()
    explanation.append("WHAT THIS DOES:\n", style="bold cyan")
    explanation.append("• ", style="dim")
    explanation.append("← Mirror", style="green")
    explanation.append(" = Copy from source (transforms applied)\n", style="dim")
    explanation.append("• ", style="dim")
    explanation.append("→ Keep target", style="cyan")
    explanation.append(" = Preserve target's existing config\n", style="dim")
    explanation.append("• ", style="dim")
    explanation.append("✎ Edit", style="yellow")
    explanation.append(" = Custom edits (knobs, interfaces, range)\n", style="dim")
    
    # Summary line
    summary = Text()
    summary.append(f"\n✓ {mirror_count} items from source", style="green")
    summary.append(f"  •  ", style="dim")
    summary.append(f"✓ {keep_count} items keep target", style="cyan")
    
    # Wrap in Panel
    panel_content = Group(explanation, diff_table, summary)
    diff_panel = Panel(
        panel_content,
        title=f"[bold]{hierarchy_name} - Smart Diff Summary[/bold]",
        title_align="left",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print()
    console.print(diff_panel)
    
    # Navigation options
    nav = Prompt.ask(
        "\n[C]ontinue to next hierarchy | [R]edo this section | [B]ack",
        choices=['c', 'C', 'r', 'R', 'b', 'B'],
        default='c'
    ).lower()
    
    if nav == 'b':
        return None
    elif nav == 'r':
        # Redo this section
        return _edit_hierarchy_subsections(mirror, hierarchy_key, hierarchy_name, source_hostname, target_hostname, analysis)
    
    console.print(f"[green]✓ {hierarchy_name} configured[/green]")
    return selections


def modify_mirror_sections(
    mirror: ConfigMirror,
    target_hostname: str,
    target_config: str
) -> Tuple[Optional[str], int]:
    """
    Allow user to selectively keep/skip sections for the target device.
    Also allows adding custom configuration to each section.
    
    Args:
        mirror: ConfigMirror instance
        target_hostname: Target device hostname
        target_config: Original target device configuration
        
    Returns:
        Tuple of (modified_config, line_count) or (None, 0) if cancelled
    """
    from rich.table import Table
    
    console.print(f"\n[bold cyan]Modify Sections for {target_hostname}[/bold cyan]")
    console.print("[dim]Select sections to include, view content, or add custom config.[/dim]")
    console.print()
    
    # Define available sections - restore from mirror's stored state if available
    default_sections = {
        'system': {'desc': 'System Config', 'source': 'source', 'include': True, 'custom': '', 'hierarchy': 'system'},
        'lo0': {'desc': 'Loopback (Lo0)', 'source': 'target', 'include': True, 'custom': '', 'hierarchy': 'interfaces'},
        'wan': {'desc': 'WAN Interfaces', 'source': 'target', 'include': True, 'custom': '', 'hierarchy': 'interfaces'},
        'bundles': {'desc': 'Bundle/LACP', 'source': 'target', 'include': True, 'custom': '', 'hierarchy': 'interfaces'},
        'lldp': {'desc': 'LLDP Config', 'source': 'target', 'include': True, 'custom': '', 'hierarchy': 'protocols'},
        'services': {'desc': 'Network Services', 'source': 'source', 'include': True, 'custom': '', 'hierarchy': 'network-services'},
        'svc_ifaces': {'desc': 'Service Interfaces', 'source': 'source', 'include': True, 'custom': '', 'hierarchy': 'interfaces'},
        'routing_policy': {'desc': 'Routing Policy', 'source': 'source', 'include': True, 'custom': '', 'hierarchy': 'routing-policy'},
        'acls': {'desc': 'ACLs', 'source': 'source', 'include': True, 'custom': '', 'hierarchy': 'acls'},
        'qos': {'desc': 'QoS', 'source': 'source', 'include': True, 'custom': '', 'hierarchy': 'qos'},
        'multihoming': {'desc': 'Multihoming ESIs', 'source': 'source', 'include': True, 'custom': '', 'hierarchy': 'multihoming'},
        'protocols': {'desc': 'Protocols (BGP/ISIS)', 'source': 'source', 'include': True, 'custom': '', 'hierarchy': 'protocols'},
    }
    
    # Restore previous state from mirror object if available
    if mirror._section_states:
        sections = {}
        for key, defaults in default_sections.items():
            stored = mirror._section_states.get(key, {})
            sections[key] = {
                'desc': defaults['desc'],
                'source': defaults['source'],
                'hierarchy': defaults['hierarchy'],
                'include': stored.get('include', defaults['include']),
                'custom': stored.get('custom', defaults['custom']),
            }
        # Show that we restored previous state
        custom_count = sum(1 for s in sections.values() if s['custom'].strip())
        if custom_count > 0:
            console.print(f"[magenta]ℹ Restored {custom_count} custom config additions from previous session[/magenta]")
    else:
        sections = default_sections
    
    # Pre-extract sections for viewing
    target_unique = mirror.extract_target_unique()
    source_mirrored = mirror.extract_source_mirrored()
    
    def get_section_content(key: str) -> str:
        """Get the current content for a section."""
        if key == 'system':
            # Show mirrored system if available, otherwise target's system
            if source_mirrored.get('system'):
                return mirror.transform_system_section(source_mirrored['system'])
            return target_unique.get('system', '')
        elif key == 'lo0':
            return target_unique.get('lo0', '')
        elif key == 'wan':
            wan = target_unique.get('wan_interfaces', '')
            parents = target_unique.get('physical_parents', '')
            return wan + '\n' + parents if parents else wan
        elif key == 'bundles':
            return target_unique.get('bundles', '')
        elif key == 'lldp':
            return target_unique.get('lldp', '')
        elif key == 'services':
            svc = source_mirrored.get('services', '')
            return mirror.transform_rds(svc) if svc else ''
        elif key == 'svc_ifaces':
            ifaces = source_mirrored.get('service_interfaces', '')
            return mirror.transform_interfaces(ifaces) if ifaces else ''
        elif key == 'routing_policy':
            return source_mirrored.get('routing_policy', '')
        elif key == 'acls':
            return source_mirrored.get('acls', '')
        elif key == 'qos':
            return source_mirrored.get('qos', '')
        elif key == 'multihoming':
            mh = source_mirrored.get('multihoming', '')
            return mirror.transform_interfaces(mh) if mh else ''
        elif key == 'protocols':
            source_protocols = extract_hierarchy_section(mirror.source_config, 'protocols')
            if source_protocols:
                source_protocols = mirror._remove_protocol_subsection(source_protocols, 'lldp')
                source_protocols = mirror._remove_protocol_subsection(source_protocols, 'lacp')
                return mirror.transform_router_id(source_protocols)
            return ''
        return ''
    
    while True:
        # Filter sections - only show sections that have actual content
        # Target sections always show (system, lo0, wan, bundles, lldp)
        # Source sections only show if they have content
        section_keys = []
        for key in sections.keys():
            sec = sections[key]
            # Target sections always show
            if sec['source'] == 'target':
                section_keys.append(key)
            else:
                # Source sections - check if they have content
                content = get_section_content(key)
                if content and content.strip():
                    section_keys.append(key)
                elif sec['custom'].strip():
                    # Also show if user has added custom config
                    section_keys.append(key)
        
        # Show current section selections
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=3)
        table.add_column("Section", width=20)
        table.add_column("From", width=10)
        table.add_column("Include", justify="center", width=10)
        table.add_column("Custom", justify="center", width=10)
        
        for i, key in enumerate(section_keys, 1):
            sec = sections[key]
            source_str = f"[green]{target_hostname}[/green]" if sec['source'] == 'target' else "[cyan]Source[/cyan]"
            include_str = "[green]✓ Yes[/green]" if sec['include'] else "[red]✗ No[/red]"
            custom_str = f"[magenta]+{len(sec['custom'].split(chr(10)))-1} lines[/magenta]" if sec['custom'].strip() else "[dim]-[/dim]"
            table.add_row(str(i), sec['desc'], source_str, include_str, custom_str)
        
        console.print(table)
        console.print()
        console.print(f"  [bold]Enter section number to modify (1-{len(section_keys)})[/bold]")
        console.print()
        console.print("  [A] Apply changes and regenerate")
        console.print("  [R] Reset all to defaults")
        console.print("  [B] Back (cancel changes)")
        
        action = Prompt.ask("Select", default="a").strip()
        
        if action.lower() == 'b':
            return None, 0
        
        if action.lower() == 'r':
            # Reset all to include and clear custom
            for key in sections:
                sections[key]['include'] = True
                sections[key]['custom'] = ''
            console.print("[green]✓ Reset to defaults[/green]")
            continue
        
        if action.lower() == 'a':
            # Apply changes and regenerate
            break
        
        # Handle section selection by number - opens section menu
        if action.isdigit():
            try:
                num = int(action)
                
                if 1 <= num <= len(section_keys):
                    key = section_keys[num - 1]
                    sec = sections[key]
                    content = get_section_content(key)
                    custom = sec['custom']
                    hierarchy = sec['hierarchy']
                    
                    # Full section menu
                    while True:
                        console.print(f"\n[bold cyan]═══ {sec['desc']} ═══[/bold cyan]")
                        console.print(f"[dim]Hierarchy: {hierarchy}[/dim]")
                        
                        # Show current status
                        orig_lines = len(content.split('\n')) if content else 0
                        custom_lines = len([l for l in custom.split('\n') if l.strip()]) if custom.strip() else 0
                        include_status = "[green]✓ Included[/green]" if sec['include'] else "[red]✗ Excluded[/red]"
                        
                        console.print(f"\n  Status: {include_status}")
                        console.print(f"  Original: {orig_lines} lines")
                        if custom_lines > 0:
                            console.print(f"  Custom:   [green]+{custom_lines} lines[/green]")
                        
                        console.print(f"\n[bold]Options:[/bold]")
                        console.print("  [1] View content - Show current config")
                        console.print("  [2] Toggle include/exclude")
                        
                        # Section-specific options
                        if key == 'system':
                            console.print("  [3] Edit hostname")
                            console.print("  [4] Edit contact-info")
                            console.print("  [5] Edit location")
                            console.print("  [6] Add custom system config")
                        elif key == 'lo0':
                            console.print("  [3] Edit loopback IP")
                            console.print("  [4] Add custom lo0 config")
                        elif key == 'multihoming':
                            console.print("  [3] Change DF preference (bulk) - Modify existing values")
                            console.print("  [4] Add ESI config (bulk)")
                            console.print("  [5] Add single ESI")
                        elif key == 'services':
                            console.print("  [3] Modify service parameters")
                            console.print("  [4] Add custom service config")
                        elif key == 'svc_ifaces':
                            console.print("  [3] Modify interface parameters (bulk)")
                            console.print("  [4] Add interface config")
                        elif key == 'protocols':
                            console.print("  [3] Edit router-ID")
                            console.print("  [4] Edit BGP neighbor")
                            console.print("  [5] Add custom protocol config")
                        else:
                            console.print("  [3] Add custom config")
                        
                        if custom_lines > 0:
                            console.print(f"  [C] Clear custom config ({custom_lines} lines)")
                        console.print("  [B] Back to section list")
                        
                        sec_choice = Prompt.ask("Select", default="b").lower()
                        
                        if sec_choice == 'b':
                            break
                        
                        if sec_choice == '1':
                            # View content
                            _view_section_content(content, custom, hierarchy, sec['desc'])
                            continue
                        
                        if sec_choice == '2':
                            # Toggle include
                            sec['include'] = not sec['include']
                            status = "included" if sec['include'] else "excluded"
                            console.print(f"[green]✓ {sec['desc']} now {status}[/green]")
                            continue
                        
                        if sec_choice == 'c' and custom_lines > 0:
                            sec['custom'] = ""
                            console.print(f"[green]✓ Cleared custom config[/green]")
                            custom = ""
                            continue
                        
                        if sec_choice == '3':
                            if key == 'system':
                                # Edit hostname
                                new_hostname = Prompt.ask("Enter new hostname", default=target_hostname)
                                if new_hostname and new_hostname != target_hostname:
                                    # Add hostname override to custom config
                                    sec['custom'] = f"  hostname {new_hostname}"
                                    mirror.target_hostname = new_hostname
                                    console.print(f"[green]✓ Hostname set to: {new_hostname}[/green]")
                                    custom = sec['custom']
                            elif key == 'lo0':
                                # Edit loopback IP
                                current_ip = mirror.target_lo0.split('/')[0] if mirror.target_lo0 else ''
                                new_ip = Prompt.ask("Enter new loopback IP", default=current_ip)
                                if new_ip:
                                    mirror.target_lo0 = f"{new_ip}/32"
                                    mirror.user_entered_lo0 = f"{new_ip}/32"
                                    mirror.target_rid = new_ip
                                    mirror.user_entered_rid = new_ip
                                    mirror._compile_transform_patterns()
                                    console.print(f"[green]✓ Loopback IP set to: {new_ip}/32[/green]")
                                    console.print(f"[green]✓ RDs will be transformed to: {new_ip}:N[/green]")
                            elif key == 'protocols':
                                # Edit router-ID
                                current_rid = mirror.target_rid or ''
                                new_rid = Prompt.ask("Enter new router-ID", default=current_rid)
                                if new_rid:
                                    mirror.target_rid = new_rid
                                    mirror.user_entered_rid = new_rid
                                    mirror._compile_transform_patterns()
                                    console.print(f"[green]✓ Router-ID set to: {new_rid}[/green]")
                            elif key == 'multihoming':
                                # Bulk DF preference change
                                new_custom = _wizard_modify_df_preference(mirror, content, custom)
                                if new_custom:
                                    sec['custom'] = new_custom  # Replace, not append
                                    console.print(f"[green]✓ Updated DF preferences[/green]")
                                    custom = new_custom
                            elif key in ['services', 'svc_ifaces']:
                                custom_config = _wizard_add_section_config(key, sec, mirror, target_hostname)
                                if custom_config:
                                    sec['custom'] = sec['custom'] + '\n' + custom_config if sec['custom'].strip() else custom_config
                                    custom = sec['custom']
                            else:
                                custom_config = _wizard_add_section_config(key, sec, mirror, target_hostname)
                                if custom_config:
                                    sec['custom'] = sec['custom'] + '\n' + custom_config if sec['custom'].strip() else custom_config
                                    custom = sec['custom']
                            continue
                        
                        if sec_choice == '4':
                            if key == 'system':
                                # Edit contact-info
                                contact = Prompt.ask("Enter contact-info", default="")
                                if contact:
                                    custom_line = f"  contact-info {contact}"
                                    sec['custom'] = sec['custom'] + '\n' + custom_line if sec['custom'].strip() else custom_line
                                    console.print(f"[green]✓ Contact-info set to: {contact}[/green]")
                                    custom = sec['custom']
                            elif key == 'lo0':
                                # Add custom lo0 config
                                custom_config = _wizard_add_section_config(key, sec, mirror, target_hostname)
                                if custom_config:
                                    sec['custom'] = sec['custom'] + '\n' + custom_config if sec['custom'].strip() else custom_config
                                    custom = sec['custom']
                            elif key == 'protocols':
                                # Edit BGP neighbor
                                console.print("[dim]BGP neighbor editing - enter neighbor IP and remote AS[/dim]")
                                neighbor_ip = Prompt.ask("Neighbor IP", default="")
                                if neighbor_ip:
                                    remote_as = Prompt.ask("Remote AS", default=str(mirror.source_asn or ""))
                                    if remote_as:
                                        custom_line = f"      neighbor {neighbor_ip}\n        remote-as {remote_as}\n      !"
                                        sec['custom'] = sec['custom'] + '\n' + custom_line if sec['custom'].strip() else custom_line
                                        console.print(f"[green]✓ Added BGP neighbor: {neighbor_ip} AS {remote_as}[/green]")
                                        custom = sec['custom']
                            else:
                                custom_config = _wizard_add_section_config(key, sec, mirror, target_hostname)
                                if custom_config:
                                    sec['custom'] = sec['custom'] + '\n' + custom_config if sec['custom'].strip() else custom_config
                                    console.print(f"[green]✓ Added config to {sec['desc']}[/green]")
                                    custom = sec['custom']
                            continue
                        
                        if sec_choice == '5':
                            if key == 'system':
                                # Edit location
                                location = Prompt.ask("Enter location", default="")
                                if location:
                                    custom_line = f"  location {location}"
                                    sec['custom'] = sec['custom'] + '\n' + custom_line if sec['custom'].strip() else custom_line
                                    console.print(f"[green]✓ Location set to: {location}[/green]")
                                    custom = sec['custom']
                            elif key == 'protocols':
                                # Add custom protocol config
                                custom_config = _wizard_add_section_config(key, sec, mirror, target_hostname)
                                if custom_config:
                                    sec['custom'] = sec['custom'] + '\n' + custom_config if sec['custom'].strip() else custom_config
                                    custom = sec['custom']
                            else:
                                custom_config = _wizard_add_section_config(key, sec, mirror, target_hostname)
                                if custom_config:
                                    sec['custom'] = sec['custom'] + '\n' + custom_config if sec['custom'].strip() else custom_config
                                    console.print(f"[green]✓ Added config to {sec['desc']}[/green]")
                                    custom = sec['custom']
                            continue
                        
                        if sec_choice == '6':
                            if key == 'system':
                                # Add custom system config
                                custom_config = _wizard_add_section_config(key, sec, mirror, target_hostname)
                                if custom_config:
                                    sec['custom'] = sec['custom'] + '\n' + custom_config if sec['custom'].strip() else custom_config
                                    custom = sec['custom']
                            continue
                else:
                    console.print(f"[yellow]Invalid: enter 1-{len(section_keys)}[/yellow]")
            except ValueError:
                console.print(f"[yellow]Enter section number (1-{len(section_keys)}), A to apply, R to reset, or B to go back[/yellow]")
            continue
    
    # Regenerate config with selected sections and custom additions
    console.print("\n[dim]Regenerating configuration with selected sections...[/dim]")
    
    # Count custom additions
    custom_count = sum(1 for s in sections.values() if s['custom'].strip())
    if custom_count > 0:
        console.print(f"[magenta]Including {custom_count} custom config additions[/magenta]")
    
    # Build config manually based on selections
    config_parts = []
    
    # Re-extract sections (in case they changed)
    target_unique = mirror.extract_target_unique()
    source_mirrored = mirror.extract_source_mirrored()
    
    # System (from target or mirrored from source)
    if sections['system']['include']:
        # Check if system should be mirrored from source
        if source_mirrored.get('system'):
            # Mirror system from source with transformations
            mirrored_system = mirror.transform_system_section(source_mirrored['system'])
            
            # Merge with target's unique settings if target has system config
            if target_unique.get('system'):
                import re as re_mod
                
                def parse_system_config(config: str) -> dict:
                    """Parse system config into dict of setting -> full line"""
                    settings = {}
                    lines = config.split('\n')
                    for line in lines:
                        stripped = line.strip()
                        if stripped and stripped != 'system' and stripped != '!':
                            key = stripped.split()[0] if stripped.split() else ''
                            if key:
                                settings[key] = line
                    return settings
                
                source_settings = parse_system_config(mirrored_system)
                target_settings = parse_system_config(target_unique['system'])
                
                # Start with mirrored source settings
                merged_settings = source_settings.copy()
                
                # ALWAYS use target's hostname (device uniqueness)
                if 'hostname' in target_settings:
                    merged_settings['hostname'] = target_settings['hostname']
                elif 'hostname' in merged_settings:
                    merged_settings['hostname'] = re_mod.sub(
                        r'(\s+hostname\s+)\S+',
                        rf'\g<1>{mirror.target_hostname}',
                        merged_settings['hostname']
                    )
                
                # Preserve target's unique settings
                for key, line in target_settings.items():
                    if key not in source_settings and key != 'hostname':
                        merged_settings[key] = line
                
                # Build merged system config
                merged_lines = ['system']
                for key in ['hostname'] + sorted(k for k in merged_settings.keys() if k != 'hostname'):
                    if key in merged_settings:
                        merged_lines.append(merged_settings[key])
                merged_lines.append('!')
                
                config_parts.append('\n'.join(merged_lines))
            else:
                # No target system, use transformed mirrored system
                config_parts.append(mirrored_system)
        elif target_unique.get('system'):
            # Use target's system (not mirroring)
            config_parts.append(target_unique['system'])
        
        # Add custom system config (inside system hierarchy)
        if sections['system']['custom'].strip():
            # If we already added system, we need to insert custom before closing !
            if config_parts and config_parts[-1].strip().endswith('!'):
                # Insert custom before last !
                last_part = config_parts[-1]
                lines = last_part.split('\n')
                if lines[-1].strip() == '!':
                    lines.insert(-1, sections['system']['custom'])
                    config_parts[-1] = '\n'.join(lines)
                else:
                    config_parts.append(sections['system']['custom'])
            else:
                # No system section yet, create one with custom
                config_parts.append('system')
                config_parts.append(sections['system']['custom'])
                config_parts.append('!')
    
    # Interfaces section
    config_parts.append('interfaces')
    
    if sections['lo0']['include'] and target_unique.get('lo0'):
        config_parts.append(target_unique['lo0'])
        # Custom lo0 additions
        if sections['lo0']['custom'].strip():
            config_parts.append(sections['lo0']['custom'])
    
    if sections['wan']['include']:
        if target_unique.get('wan_interfaces'):
            config_parts.append(target_unique['wan_interfaces'])
        if target_unique.get('physical_parents'):
            config_parts.append(target_unique['physical_parents'])
        # Custom WAN additions
        if sections['wan']['custom'].strip():
            config_parts.append(sections['wan']['custom'])
    
    if sections['bundles']['include'] and target_unique.get('bundles'):
        config_parts.append(target_unique['bundles'])
        # Custom bundle additions
        if sections['bundles']['custom'].strip():
            config_parts.append(sections['bundles']['custom'])
    
    if sections['svc_ifaces']['include'] and source_mirrored.get('service_interfaces'):
        svc_ifaces = source_mirrored['service_interfaces']
        svc_ifaces = mirror.transform_interfaces(svc_ifaces)
        config_parts.append(svc_ifaces)
    
    # Custom interface additions (service interfaces)
    if sections['svc_ifaces']['custom'].strip():
        config_parts.append(sections['svc_ifaces']['custom'])
    
    config_parts.append('!')
    
    # Protocols
    config_parts.append('protocols')
    
    if sections['lldp']['include'] and target_unique.get('lldp'):
        config_parts.append(target_unique['lldp'])
        # Custom LLDP additions
        if sections['lldp']['custom'].strip():
            config_parts.append(sections['lldp']['custom'])
    
    if sections['bundles']['include'] and target_unique.get('lacp'):
        config_parts.append(target_unique['lacp'])
    
    if sections['protocols']['include']:
        source_protocols = extract_hierarchy_section(mirror.source_config, 'protocols')
        if source_protocols:
            source_protocols = mirror._remove_protocol_subsection(source_protocols, 'lldp')
            source_protocols = mirror._remove_protocol_subsection(source_protocols, 'lacp')
            source_protocols = mirror.transform_router_id(source_protocols)
            protocol_content = mirror._get_section_content(source_protocols)
            if protocol_content:
                config_parts.append(protocol_content)
    
    # Custom protocols additions (BGP/ISIS)
    if sections['protocols']['custom'].strip():
        config_parts.append(sections['protocols']['custom'])
    
    config_parts.append('!')
    
    # Network Services (including multihoming inside)
    has_network_services = False
    if sections['services']['include'] and source_mirrored.get('services'):
        services = source_mirrored['services']
        services = mirror.transform_rds(services)
        services = mirror.transform_interfaces(services)
        config_parts.append(services)
        has_network_services = True
    
    # Custom network-services additions
    if sections['services']['custom'].strip():
        config_parts.append(sections['services']['custom'])
    
    # Multihoming - INSIDE network-services (before closing !)
    if sections['multihoming']['include'] and source_mirrored.get('multihoming'):
        mh = source_mirrored['multihoming']
        mh = mirror.transform_interfaces(mh)
        
        # If there's custom config, MERGE it with original (replace matching lines)
        custom_mh = sections['multihoming']['custom'].strip()
        if custom_mh:
            mh = _merge_custom_with_original(mh, custom_mh, 'multihoming')
        
        config_parts.append(mh)
    elif sections['multihoming']['custom'].strip():
        # Only custom, no original - add with proper indentation inside network-services
        custom_mh = sections['multihoming']['custom']
        # Ensure custom starts with proper indent (2-space for inside network-services)
        if not custom_mh.startswith('  '):
            custom_mh = '  ' + custom_mh.replace('\n', '\n  ').rstrip()
        config_parts.append(custom_mh)
    
    # Close network-services
    if has_network_services or sections['multihoming']['include']:
        config_parts.append('!')
    
    # Routing Policy (top-level, OUTSIDE network-services)
    if sections['routing_policy']['include'] and source_mirrored.get('routing_policy'):
        config_parts.append(source_mirrored['routing_policy'])
    # Custom routing-policy additions
    if sections['routing_policy']['custom'].strip():
        config_parts.append(sections['routing_policy']['custom'])
    
    # ACLs
    if sections['acls']['include'] and source_mirrored.get('acls'):
        config_parts.append(source_mirrored['acls'])
    # Custom ACL additions
    if sections['acls']['custom'].strip():
        config_parts.append(sections['acls']['custom'])
    
    # QoS
    if sections['qos']['include'] and source_mirrored.get('qos'):
        config_parts.append(source_mirrored['qos'])
    # Custom QoS additions
    if sections['qos']['custom'].strip():
        config_parts.append(sections['qos']['custom'])
    
    # Note: Multihoming is handled above (inside network-services section)
    
    # Join and clean up with proper DNOS syntax
    merged = '\n'.join(config_parts)
    merged = cleanup_dnos_config_syntax(merged)
    
    # Save section states to mirror object for persistence
    mirror._section_states = {
        key: {'include': sec['include'], 'custom': sec['custom']}
        for key, sec in sections.items()
    }
    
    line_count = len(merged.split('\n'))
    console.print(f"[green]✓ Generated {line_count:,} lines[/green]")
    
    return merged, line_count


def generate_config_with_live_terminal(
    mirror: ConfigMirror,
    source_hostname: str,
    target_hostname: str,
    quiet: bool = False
) -> Tuple[str, int]:
    """
    Generate mirrored configuration with live terminal display.
    
    Shows real-time progress with:
    - Progress bar with percentage
    - Current operation status
    - Elapsed time
    - Live terminal log
    
    Args:
        mirror: ConfigMirror instance
        source_hostname: Source device name
        target_hostname: Target device name
        quiet: If True, skip the live terminal display (for multi-target mode)
        
    Returns:
        Tuple of (merged_config, line_count)
    """
    # Quick mode for multi-target: just generate without the fancy display
    if quiet:
        merged_config = mirror.generate_merged_config()
        line_count = len(merged_config.split('\n'))
        return merged_config, line_count
    
    from rich.live import Live
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
    from rich.layout import Layout
    from rich.table import Table
    import time
    import threading
    
    # State for live updates
    state = {
        'stage': 'Initializing...',
        'progress': 0,
        'log_lines': [],
        'start_time': time.time(),
        'completed': False,
        'result': None,
        'error': None,
    }
    
    PANEL_HEIGHT = 16
    MAX_LOG_LINES = 8
    
    def add_log(msg: str, style: str = "dim"):
        """Add a log line with timestamp."""
        elapsed = time.time() - state['start_time']
        state['log_lines'].append((f"[{elapsed:5.1f}s]", msg, style))
        if len(state['log_lines']) > MAX_LOG_LINES:
            state['log_lines'].pop(0)
    
    def render_panel() -> Panel:
        """Render the live terminal panel."""
        content = Text()
        
        # Header
        content.append(f"📦 Mirroring: ", style="bold cyan")
        content.append(f"{source_hostname}", style="green")
        content.append(" → ", style="dim")
        content.append(f"{target_hostname}\n", style="yellow")
        content.append("─" * 60 + "\n", style="dim")
        
        # Progress bar
        pct = state['progress']
        bar_width = 40
        filled = int(bar_width * pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        content.append(f"  [{bar}] {pct:3.0f}%\n", style="cyan")
        
        # Current stage
        content.append(f"  Stage: ", style="dim")
        content.append(f"{state['stage']}\n", style="bold white")
        
        # Elapsed time
        elapsed = time.time() - state['start_time']
        content.append(f"  Elapsed: {elapsed:.1f}s\n", style="dim")
        content.append("─" * 60 + "\n", style="dim")
        
        # Log lines
        for timestamp, msg, style in state['log_lines']:
            content.append(f"  {timestamp} ", style="dim")
            content.append(f"{msg}\n", style=style)
        
        # Pad to fixed height
        current_lines = len(content.plain.split('\n'))
        for _ in range(PANEL_HEIGHT - current_lines):
            content.append("\n")
        
        return Panel(
            content,
            title=f"[bold cyan]⚡ Configuration Generation[/bold cyan]",
            border_style="cyan",
            height=PANEL_HEIGHT
        )
    
    def progress_callback(msg: str, pct: int):
        """Callback for progress updates from generate_merged_config."""
        state['stage'] = msg
        state['progress'] = pct
        add_log(msg, "green" if pct >= 90 else "white")
    
    def generate_worker():
        """Worker thread to generate config."""
        try:
            add_log("Starting configuration generation...", "cyan")
            result = mirror.generate_merged_config(progress_callback=progress_callback)
            state['result'] = result
            state['completed'] = True
            add_log(f"✓ Generated {len(result.split(chr(10))):,} lines", "green bold")
        except Exception as e:
            state['error'] = str(e)
            state['completed'] = True
            add_log(f"✗ Error: {e}", "red bold")
    
    # Start generation in background thread
    worker = threading.Thread(target=generate_worker, daemon=True)
    worker.start()
    
    # Run live display
    with Live(render_panel(), refresh_per_second=10, console=console, transient=True) as live:
        while not state['completed']:
            live.update(render_panel())
            time.sleep(0.1)
        # Final update
        live.update(render_panel())
        time.sleep(0.3)
    
    if state['error']:
        console.print(f"[red]Error generating config: {state['error']}[/red]")
        return '', 0
    
    merged_config = state['result']
    line_count = len(merged_config.split('\n'))
    
    elapsed = time.time() - state['start_time']
    console.print(f"[green]✓ Generated {line_count:,} lines in {elapsed:.1f}s[/green]")
    
    return merged_config, line_count


def cleanup_dnos_config_syntax(config: str) -> str:
    """
    Clean up and validate DNOS configuration syntax.
    
    Ensures:
    - Proper hierarchy separation with !
    - No multiple consecutive blank lines
    - No blank lines after headers or before closing !
    
    Args:
        config: Raw configuration text
        
    Returns:
        Cleaned configuration text
    """
    lines = config.split('\n')
    cleaned = []
    prev_was_blank = False
    
    for line in lines:
        # Skip multiple consecutive blank lines
        is_blank = not line.strip()
        if is_blank and prev_was_blank:
            continue
        prev_was_blank = is_blank
        
        # Don't add blank line right after a header
        if is_blank and cleaned:
            last = cleaned[-1].strip()
            if last in ('system', 'interfaces', 'protocols', 'network-services', 
                       'routing-policy', 'access-lists', 'qos', 'multihoming', 'routing-options'):
                continue
        
        cleaned.append(line)
    
    # Remove trailing blank lines
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()
    
    return '\n'.join(cleaned)


def view_mirror_section(config: str) -> None:
    """
    View a specific section of the mirrored configuration.
    
    Args:
        config: Full configuration text
    """
    console.print("\n[bold]View Section:[/bold]")
    console.print("  [1] System")
    console.print("  [2] Interfaces")
    console.print("  [3] Protocols")
    console.print("  [4] Network Services")
    console.print("  [5] Routing Policy")
    console.print("  [6] Multihoming")
    console.print("  [B] Back")
    
    section_choice = Prompt.ask("Select section", choices=["1", "2", "3", "4", "5", "6", "b", "B"], default="b")
    
    if section_choice.lower() == 'b':
        return
    
    section_map = {
        "1": "system",
        "2": "interfaces",
        "3": "protocols",
        "4": "network-services",
        "5": "routing-policy",
        "6": "multihoming"
    }
    
    section_name = section_map.get(section_choice, "")
    if not section_name:
        return
    
    # Extract section
    section_text = extract_hierarchy_section(config, section_name)
    
    if section_text:
        console.print(f"\n[bold cyan]─── {section_name.upper()} ───[/bold cyan]")
        lines = section_text.split('\n')
        for line in lines[:80]:
            console.print(line)
        if len(lines) > 80:
            console.print(f"\n[dim]... ({len(lines) - 80} more lines)[/dim]")
        console.print(f"[bold cyan]─── END {section_name.upper()} ───[/bold cyan]")
    else:
        console.print(f"[yellow]Section '{section_name}' not found in configuration.[/yellow]")


def show_mirror_analysis(mirror: ConfigMirror) -> None:
    """
    Display analysis comparison between source and target devices.
    
    Args:
        mirror: ConfigMirror instance with parsed data
    """
    source = mirror.get_source_summary()
    target = mirror.get_target_summary()
    
    table = Table(
        title="[bold]Mirror Configuration Analysis[/bold]",
        box=box.ROUNDED,
        show_header=True
    )
    table.add_column("Attribute", style="cyan", width=20)
    table.add_column(f"Source ({source['hostname']})", width=25)
    table.add_column(f"Target ({target['hostname']})", width=25)
    
    table.add_row("Loopback IP", source['lo0'] or 'N/A', target['lo0'] or 'N/A')
    table.add_row("Router ID", source['router_id'] or 'N/A', target['router_id'] or 'N/A')
    table.add_row("BGP ASN", str(source['asn']) if source['asn'] else 'N/A',
                  str(target['asn']) if target['asn'] else 'N/A')
    table.add_row("WAN Interfaces", str(source['wan_count']), str(target['wan_count']))
    table.add_row("FXC Services", str(source['fxc_count']), str(target['fxc_count']))
    table.add_row("MH Interfaces", str(source['mh_interfaces']), str(target['mh_interfaces']))
    
    console.print(table)
    
    # Get hostnames for display
    target_hostname = target['hostname']
    source_hostname = source['hostname']
    
    # Show what will be preserved/mirrored
    console.print(f"\n[bold green]Will PRESERVE from target ({target_hostname}):[/bold green]")
    console.print(f"  ✓ System config (hostname: {target_hostname})")
    if target['wan_count'] > 0:
        console.print(f"  ✓ WAN interfaces ({target['wan_count']} interfaces)")
    console.print("  ✓ LLDP configuration")
    console.print(f"  ✓ Lo0 address ({target['lo0']})")
    
    console.print(f"\n[bold cyan]Will MIRROR from source ({source_hostname}):[/bold cyan]")
    if source['fxc_count'] > 0:
        console.print(f"  → {source['fxc_count']} FXC services (RD: {source['lo0']} → {target['lo0']})")
    if source['mh_interfaces'] > 0:
        console.print(f"  → Multihoming ESIs ({source['mh_interfaces']} interfaces)")
    console.print("  → Routing policies")
    console.print("  → ACLs and QoS")
    
    # Show what will be DELETED (config on target that doesn't exist on source)
    cleanup = mirror.get_cleanup_summary()
    # Only sum main counts (exclude underscore-prefixed display-only keys)
    total_deletes = sum(v for k, v in cleanup.items() if not k.startswith('_'))
    
    if total_deletes > 0:
        console.print(f"\n[bold red]Will DELETE from target ({target_hostname}) (not on source {source_hostname}):[/bold red]")
        if cleanup['fxc_to_delete'] > 0:
            console.print(f"  ✗ {cleanup['fxc_to_delete']} FXC services")
        if cleanup['vpls_to_delete'] > 0:
            console.print(f"  ✗ {cleanup['vpls_to_delete']} VPLS services")
        if cleanup['interfaces_to_delete'] > 0:
            sub_count = cleanup.get('_sub_interfaces', 0)
            parent_count = cleanup.get('_parent_interfaces', 0)
            console.print(f"  ✗ {cleanup['interfaces_to_delete']} interfaces ({sub_count} sub-ifs, {parent_count} parents)")
        if cleanup['mh_to_delete'] > 0:
            console.print(f"  ✗ {cleanup['mh_to_delete']} multihoming interfaces")
    else:
        console.print(f"\n[dim]No configuration to delete - {target_hostname} is a subset of {source_hostname}.[/dim]")


def select_interface_mapping_strategy(mirror: ConfigMirror) -> Optional[str]:
    """
    Interactive selection of interface mapping strategy.
    
    Args:
        mirror: ConfigMirror instance
        
    Returns:
        Mapping strategy: 'auto', 'copy', 'custom', or None if cancelled
    """
    source_interfaces = mirror.get_source_service_interfaces()
    
    if not source_interfaces:
        console.print("[dim]No service interfaces to map.[/dim]")
        return 'copy'
    
    # Detect interface types
    pwhe_count = sum(1 for i in source_interfaces if i.startswith('ph'))
    l2ac_count = len(source_interfaces) - pwhe_count
    
    console.print("\n[bold]Interface Mapping Strategy[/bold]")
    console.print(f"  Source device has: [cyan]{pwhe_count}[/cyan] PWHE, [cyan]{l2ac_count}[/cyan] L2-AC interfaces")
    console.print()
    
    # Show example interfaces
    sample_pwhe = [i for i in source_interfaces if i.startswith('ph')][:3]
    sample_l2ac = [i for i in source_interfaces if not i.startswith('ph')][:3]
    if sample_pwhe:
        console.print(f"  [dim]Sample PWHE: {', '.join(sample_pwhe)}{'...' if pwhe_count > 3 else ''}[/dim]")
    if sample_l2ac:
        console.print(f"  [dim]Sample L2-AC: {', '.join(sample_l2ac)}{'...' if l2ac_count > 3 else ''}[/dim]")
    console.print()
    
    console.print("  [1] [green]Same names[/green] [bold](recommended)[/bold]")
    console.print("      → Use exact same interface names on target")
    console.print(f"      → Source [dim]ph1.1[/dim] becomes target [dim]ph1.1[/dim]")
    console.print()
    console.print("  [2] [cyan]Remap to target interfaces[/cyan]")
    console.print("      → Map source interfaces to different target interfaces")
    console.print(f"      → Source [dim]ph1.1[/dim] could become target [dim]ge400-0/0/4.1[/dim]")
    console.print()
    console.print("  [3] [yellow]Custom prefix[/yellow]")
    console.print("      → Manually specify prefix transformation")
    console.print()
    console.print("  [B] Back")
    
    choice = Prompt.ask("Select strategy", choices=["1", "2", "3", "b", "B"], default="1")
    
    if choice.lower() == 'b':
        return None
    
    # 1=copy (same names), 2=auto (remap), 3=custom
    strategy_map = {"1": "copy", "2": "auto", "3": "custom"}
    return strategy_map.get(choice, 'copy')


def configure_custom_interface_mapping(mirror: ConfigMirror) -> Dict[str, str]:
    """
    Interactive configuration of custom interface mapping.
    
    Args:
        mirror: ConfigMirror instance
        
    Returns:
        Interface mapping dictionary
    """
    source_interfaces = mirror.get_source_service_interfaces()
    
    # Detect source prefix
    pwhe_ifaces = [i for i in source_interfaces if i.startswith('ph')]
    l2ac_ifaces = [i for i in source_interfaces if not i.startswith('ph')]
    
    mapping = {}
    
    if pwhe_ifaces:
        console.print(f"\n[bold]PWHE Interface Mapping ({len(pwhe_ifaces)} interfaces)[/bold]")
        console.print(f"  Source: ph1.1 - ph{len(pwhe_ifaces)}.1")
        
        target_prefix = Prompt.ask(
            "Target prefix (e.g., 'ph' or 'ge400-0/0/4.')",
            default="ph"
        )
        
        if target_prefix == 'ph':
            # Same PWHE names
            for iface in pwhe_ifaces:
                mapping[iface] = iface
        else:
            # Remap to different prefix
            for iface in pwhe_ifaces:
                if '.' in iface:
                    suffix = iface.split('.', 1)[1]
                    mapping[iface] = f"{target_prefix}{suffix}"
                else:
                    mapping[iface] = target_prefix + iface[2:]
    
    if l2ac_ifaces:
        console.print(f"\n[bold]L2-AC Interface Mapping ({len(l2ac_ifaces)} interfaces)[/bold]")
        sample = l2ac_ifaces[0] if l2ac_ifaces else 'ge100-0/0/1.1'
        console.print(f"  Source sample: {sample}")
        
        keep_same = Confirm.ask("Keep same L2-AC interface names?", default=True)
        
        if keep_same:
            for iface in l2ac_ifaces:
                mapping[iface] = iface
        else:
            target_parent = Prompt.ask(
                "Target parent interface",
                default="ge400-0/0/4"
            )
            
            for i, iface in enumerate(sorted(l2ac_ifaces)):
                if '.' in iface:
                    suffix = iface.split('.', 1)[1]
                    mapping[iface] = f"{target_parent}.{suffix}"
                else:
                    mapping[iface] = f"{target_parent}.{i+1}"
    
    mirror.interface_map = mapping
    return mapping


def run_mirror_config_wizard(
    multi_ctx: 'MultiDeviceContext',
    target_device: Any = None
) -> bool:
    """
    Run the Mirror Configuration wizard.
    
    Args:
        multi_ctx: MultiDeviceContext with devices
        target_device: Optional specific target device (if None, uses first device)
        
    Returns:
        True if configuration was mirrored successfully
    """
    # Import from interactive_scale for proper push method handling with enhanced terminal
    from ..interactive_scale import ask_push_method, push_and_verify
    from rich.table import Table
    
    # Step 1: Identify target device
    if target_device is None:
        target_device = multi_ctx.devices[0] if multi_ctx.devices else None
    
    if not target_device:
        console.print("[red]No target device selected.[/red]")
        return False
    
    target_hostname = target_device.hostname
    target_config = multi_ctx.configs.get(target_hostname, "")
    
    if not target_config:
        console.print(f"[yellow]No configuration found for {target_hostname}.[/yellow]")
        console.print("[dim]Run Refresh first to fetch device configuration.[/dim]")
        return False
    
    # Parse target device summary
    target_lo0 = get_lo0_ip_from_config(target_config)
    target_services = parse_existing_evpn_services(target_config)
    target_fxc = len(target_services.get('fxc', []))
    target_vpls = len(target_services.get('vpls', []))
    target_mh = len(parse_existing_multihoming(target_config))
    
    # Show target device info (what we're copying TO)
    console.print(Panel(
        f"[bold]🪞 Mirror Configuration Mode[/bold]\n\n"
        f"[bold cyan]TARGET DEVICE (copy TO):[/bold cyan]\n"
        f"  Hostname: [bold white]{target_hostname}[/bold white]\n"
        f"  Loopback: [cyan]{target_lo0 or 'N/A'}[/cyan]\n"
        f"  Services: [dim]{target_fxc} FXC, {target_vpls} VPLS[/dim]\n"
        f"  Multihoming: [dim]{target_mh} interfaces[/dim]\n\n"
        f"[dim]Device-unique attributes (Lo0, WAN, LLDP, system) will be preserved.[/dim]",
        box=box.ROUNDED,
        border_style="magenta"
    ))
    
    # Step 2: Select source device with summary table
    console.print(f"\n[bold cyan]SELECT SOURCE DEVICE (copy FROM):[/bold cyan]")
    console.print()
    
    # Helper to validate config
    def is_valid_config(config_text: str) -> bool:
        """Check if config is a valid running config (not empty/reset)."""
        if not config_text or len(config_text) < 500:
            return False
        if 'system' not in config_text or 'interfaces' not in config_text:
            return False
        # Check for real config indicators (hostname/name OR login config OR protocols)
        # Not all devices have hostname configured, but they'll have login users or protocols
        has_name = 'hostname' in config_text or '\n  name ' in config_text
        has_login = 'user dnroot' in config_text or 'login' in config_text
        has_protocols = 'protocols' in config_text
        if not (has_name or has_login or has_protocols):
            return False
        return True
    
    # Build source options with summaries
    source_options = []
    source_data = []
    
    for dev in multi_ctx.devices:
        if dev.hostname != target_hostname:
            config = multi_ctx.configs.get(dev.hostname, "")
            
            # Check if config is valid
            config_valid = is_valid_config(config)
            
            if config:
                # Parse source summary - include VRF
                src_lo0 = get_lo0_ip_from_config(config) if config_valid else None
                if config_valid:
                    src_services = parse_existing_evpn_services(config)
                    src_fxc = len(src_services.get('fxc', []))
                    src_vpls = len(src_services.get('vpls', []))
                    src_vrf = len(parse_vrf_instances(config))
                    src_mh = len(parse_existing_multihoming(config))
                else:
                    src_fxc = src_vpls = src_vrf = src_mh = 0
                
                source_options.append(dev)
                source_data.append({
                    'hostname': dev.hostname,
                    'lo0': src_lo0,
                    'fxc': src_fxc,
                    'vpls': src_vpls,
                    'vrf': src_vrf,
                    'mh': src_mh,
                    'config': config,
                    'valid': config_valid
                })
    
    if not source_options:
        console.print("[yellow]No other devices available as source.[/yellow]")
        console.print("[dim]Add more devices to the session first.[/dim]")
        return False
    
    # Display source options table with VRF column
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=3)
    table.add_column("Hostname", style="cyan", width=15)
    table.add_column("Loopback", width=15)
    table.add_column("FXC", justify="right", width=8)
    table.add_column("VPLS", justify="right", width=8)
    table.add_column("VRF", justify="right", width=8)
    table.add_column("MH", justify="right", width=8)
    table.add_column("Status", justify="center", width=12)
    
    valid_indices = []
    for i, data in enumerate(source_data, 1):
        if data['valid']:
            fxc_str = f"[bold]{data['fxc']:,}[/bold]" if data['fxc'] > 0 else "[dim]0[/dim]"
            vpls_str = f"[bold]{data['vpls']:,}[/bold]" if data['vpls'] > 0 else "[dim]0[/dim]"
            vrf_str = f"[bold]{data['vrf']:,}[/bold]" if data['vrf'] > 0 else "[dim]0[/dim]"
            mh_str = f"[bold]{data['mh']:,}[/bold]" if data['mh'] > 0 else "[dim]0[/dim]"
            table.add_row(
                str(i),
                data['hostname'],
                data['lo0'] or "[dim]N/A[/dim]",
                fxc_str,
                vpls_str,
                vrf_str,
                mh_str,
                "[green]✓ Ready[/green]"
            )
            valid_indices.append(i)
        else:
            # Invalid/empty config - show greyed out
            table.add_row(
                f"[dim]{i}[/dim]",
                f"[dim]{data['hostname']}[/dim]",
                "[dim]N/A[/dim]",
                "[dim]-[/dim]",
                "[dim]-[/dim]",
                "[dim]-[/dim]",
                "[dim]-[/dim]",
                "[red]✗ Empty[/red]"
            )
    
    console.print(table)
    console.print("  [B] Back")
    
    # Only allow selecting valid sources
    if not valid_indices:
        console.print("\n[red]No valid source devices available.[/red]")
        console.print("[dim]Run Refresh to update device configurations.[/dim]")
        return False
    
    choices = [str(i) for i in valid_indices] + ['b', 'B']
    choice = Prompt.ask("\nSelect source device", choices=choices, default="b")
    
    if choice.lower() == 'b':
        return False
    
    source_idx = int(choice) - 1
    source_device = source_options[source_idx]
    
    # Validate the selected source is usable
    if not source_data[source_idx].get('valid'):
        console.print(f"[red]Cannot use {source_device.hostname} - config is empty or invalid.[/red]")
        return False
    
    source_hostname = source_device.hostname
    source_config = source_data[source_idx]['config']
    
    console.print(f"[green]✓ Selected source: {source_hostname}[/green]")
    console.print(f"[dim]Using cached config for {source_hostname} ({len(source_config):,} bytes)[/dim]")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP-BY-STEP SECTION SELECTION (NEW FLOW)
    # ═══════════════════════════════════════════════════════════════════════
    console.print(f"\n[bold cyan]Step 1: Select Sections to Mirror[/bold cyan]")
    console.print(f"[dim]Choose which configuration sections to mirror from {source_hostname} to {target_hostname}[/dim]")
    console.print(f"[dim]Toggle sections on/off, then press [C] to continue[/dim]\n")
    
    # Analyze source config before starting steps
    console.print(f"[dim]Analyzing {source_hostname} configuration...[/dim]")
    device_type, ncps = detect_device_type(source_config)
    services = parse_existing_evpn_services(source_config)
    service_ifaces = get_service_interfaces(source_config)
    wan_ifaces = get_wan_interfaces(source_config)
    vrf_list = parse_vrf_instances(source_config)
    
    console.print(f"  Device type: {device_type}, NCPs: {ncps}")
    console.print(f"  Services: {len(services.get('fxc', []))} FXC, {len(services.get('vpls', []))} VPLS, {len(vrf_list)} VRF")
    console.print(f"  Interfaces: {len(wan_ifaces)} WAN, {len(service_ifaces)} service")
    
    # Run the new step-by-step flow
    step_state = run_step_by_step_mirror(
        source_config=source_config,
        target_config=target_config,
        source_hostname=source_hostname,
        target_hostname=target_hostname
    )
    
    if step_state is None:
        console.print("[yellow]Mirror configuration cancelled.[/yellow]")
        return False
    
    # Convert step state to section selection for ConfigMirror compatibility
    section_selection = {}
    for section_name in step_state.SECTION_ORDER:
        result = step_state.get_section_result(section_name)
        if result and result.action in (StepAction.INCLUDE, StepAction.SELECT, StepAction.CREATE):
            # Map to old section names
            if section_name in ('interfaces_wan', 'interfaces_service', 'interfaces_loopback'):
                section_selection['interfaces'] = True
            elif section_name in ('fxc_services', 'vpls_services', 'vrf_instances'):
                section_selection['network-services'] = True
            elif section_name == 'multihoming':
                section_selection['network-services'] = True  # MH is under network-services
            elif section_name == 'protocols':
                section_selection['protocols'] = True
            elif section_name == 'qos':
                section_selection['qos'] = True
            elif section_name == 'system':
                section_selection['system'] = True
    
    # Create mirror object with selections
    mirror = ConfigMirror(
        source_config=source_config,
        target_config=target_config,
        source_hostname=source_hostname,
        target_hostname=target_hostname
    )
    mirror.section_selection = section_selection
    
    # Apply global transformations from step state
    if step_state.global_transforms.get('loopback_ip', {}).get('target'):
        mirror.target_lo0 = step_state.global_transforms['loopback_ip']['target']
    
    # Show what was selected
    selected_sections = step_state.get_included_sections()
    if not selected_sections:
        console.print("[yellow]No sections selected - nothing to mirror[/yellow]")
        return False
    
    console.print(f"\n[green]✓ Selected sections: {len(selected_sections)} sections[/green]")
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 3: ANALYSIS (now reflects selected sections only)
    # ═══════════════════════════════════════════════════════════════════════
    console.print(f"\n[bold cyan]Step 3: Configuration Analysis[/bold cyan]")
    console.print(f"[dim]Analysis based on selected sections[/dim]")
    show_mirror_analysis(mirror)
    
    # ═══════════════════════════════════════════════════════════════════════
    # CHECK FOR MISSING MANDATORY TARGET VALUES
    # ═══════════════════════════════════════════════════════════════════════
    target_summary = mirror.get_target_summary()
    source_summary = mirror.get_source_summary()
    
    # Check if target is missing critical values that are needed for proper mirroring
    missing_values = []
    if not target_summary.get('lo0'):
        missing_values.append(('Loopback IP (lo0)', 'lo0'))
    if not target_summary.get('router_id') and source_summary.get('router_id'):
        missing_values.append(('Router-ID', 'router_id'))
    if not target_summary.get('asn') and source_summary.get('asn'):
        missing_values.append(('BGP ASN', 'asn'))
    
    if missing_values:
        console.print("\n[bold yellow]╔════════════════════════════════════════════════════════════════════╗[/bold yellow]")
        console.print("[bold yellow]║         ⚠ Target Device Missing Mandatory Values                  ║[/bold yellow]")
        console.print("[bold yellow]╚════════════════════════════════════════════════════════════════════╝[/bold yellow]")
        
        console.print(f"\n[bold]Target device ({target_hostname}) is missing required values:[/bold]")
        for name, _ in missing_values:
            console.print(f"  [red]✗[/red] {name}: [red]Not configured[/red]")
        
        console.print(f"\n[bold]Source device ({source_hostname}) has:[/bold]")
        if source_summary.get('lo0'):
            console.print(f"  [green]✓[/green] Loopback IP: [cyan]{source_summary['lo0']}[/cyan]")
        if source_summary.get('router_id'):
            console.print(f"  [green]✓[/green] Router-ID: [cyan]{source_summary['router_id']}[/cyan]")
        if source_summary.get('asn'):
            console.print(f"  [green]✓[/green] BGP ASN: [cyan]{source_summary['asn']}[/cyan]")
        
        console.print("\n[bold cyan]Enter values for target device ({}):[/bold cyan]".format(target_hostname))
        console.print("[dim]These are required for proper RD/Router-ID transformations[/dim]")
        console.print("[dim]Type 'b' or 'B' to go back[/dim]\n")
        
        new_target_values = {}
        
        # Prompt for each missing value
        for name, key in missing_values:
            if key == 'lo0':
                console.print(f"[bold]Loopback IP (lo0)[/bold] [red](required for RD transformation)[/red]")
                value = Prompt.ask(
                    "   Enter IPv4 address (e.g., 1.1.1.1)",
                    default=""
                )
                if value.lower() == 'b':
                    return False
                if value:
                    new_target_values['lo0'] = value
                    # Also set router_id to same value if not configured
                    if not target_summary.get('router_id'):
                        new_target_values['router_id'] = value
                else:
                    console.print("[red]Loopback IP is required for mirroring services with RDs.[/red]")
                    return False
            
            elif key == 'router_id' and key not in new_target_values:
                console.print(f"\n[bold]Router-ID[/bold]")
                default_rid = new_target_values.get('lo0', source_summary.get('router_id', ''))
                value = Prompt.ask(
                    "   Enter Router-ID",
                    default=default_rid
                )
                if value.lower() == 'b':
                    return False
                if value:
                    new_target_values['router_id'] = value
            
            elif key == 'asn':
                console.print(f"\n[bold]BGP ASN[/bold]")
                value = Prompt.ask(
                    "   Enter BGP AS number",
                    default=str(source_summary.get('asn', ''))
                )
                if value.lower() == 'b':
                    return False
                if value:
                    new_target_values['asn'] = value
        
        # Update the mirror object with the new target values
        if new_target_values.get('lo0'):
            mirror.target_lo0 = new_target_values['lo0']
            # Re-compile the transform patterns with the new loopback
            mirror._compile_transform_patterns()
            console.print(f"\n[green]✓ Target Loopback set to: {new_target_values['lo0']}[/green]")
        
        if new_target_values.get('router_id'):
            mirror.target_rid = new_target_values['router_id']
            mirror._compile_transform_patterns()
            console.print(f"[green]✓ Target Router-ID set to: {new_target_values['router_id']}[/green]")
        
        if new_target_values.get('asn'):
            mirror.target_asn = new_target_values['asn']
            console.print(f"[green]✓ Target BGP ASN set to: {new_target_values['asn']}[/green]")
        
        # Show updated transformation preview
        console.print("\n[bold]Configuration will now transform:[/bold]")
        src_ip = mirror.source_lo0.split('/')[0] if mirror.source_lo0 else 'N/A'
        tgt_ip = mirror.target_lo0.split('/')[0] if mirror.target_lo0 else 'N/A'
        console.print(f"  • Route Distinguisher: [yellow]{src_ip}:N[/yellow] → [green]{tgt_ip}:N[/green]")
        console.print(f"  • Router-ID: [yellow]{mirror.source_rid or src_ip}[/yellow] → [green]{mirror.target_rid or tgt_ip}[/green]")
        console.print()
    
    # Proceed with mirroring? - with [B] Back option per rules
    console.print("\n[bold]Proceed with mirroring?[/bold]")
    console.print("  [Y] Yes - continue")
    console.print("  [N] No - cancel")
    console.print("  [B] Back - modify section selection")
    proceed_choice = Prompt.ask("Select", choices=["y", "Y", "n", "N", "b", "B"], default="y").lower()
    
    if proceed_choice == 'b':
        return False  # Back to re-run wizard
    if proceed_choice == 'n':
        console.print("[yellow]Mirror cancelled.[/yellow]")
        return False
    
    # Step 4: Interface mapping (only if service_interfaces section is selected)
    if section_selection.get('service_interfaces', True):
        console.print(f"\n[bold]Step 3: Interface Mapping[/bold]")
        
        strategy = select_interface_mapping_strategy(mirror)
        if strategy is None:
            return False
        
        if strategy == 'auto':
            mapping = mirror.map_interfaces_auto()
            console.print(f"[green]✓ Auto-mapped {len(mapping)} interfaces[/green]")
        elif strategy == 'copy':
            mapping = mirror.map_interfaces_copy()
            console.print(f"[green]✓ Copied {len(mapping)} interface names[/green]")
        elif strategy == 'custom':
            mapping = configure_custom_interface_mapping(mirror)
            console.print(f"[green]✓ Custom-mapped {len(mapping)} interfaces[/green]")
        
        # Show mapping preview
        if mapping and len(mapping) <= 10:
            console.print("\n[dim]Interface Mapping:[/dim]")
            for src, tgt in list(mapping.items())[:10]:
                console.print(f"  [dim]{src} → {tgt}[/dim]")
            if len(mapping) > 10:
                console.print(f"  [dim]... and {len(mapping) - 10} more[/dim]")
    else:
        console.print(f"\n[dim]Skipping interface mapping (service_interfaces not selected)[/dim]")
        mapping = {}
    
    # Step 5: Generate cleanup + merged config with LIVE TERMINAL
    console.print(f"\n[bold]Step 4: Generate Configuration[/bold]")
    
    # Check if cleanup is needed
    cleanup_summary = mirror.get_cleanup_summary()
    # Only sum main counts (exclude underscore-prefixed display-only keys)
    total_deletes = sum(v for k, v in cleanup_summary.items() if not k.startswith('_'))
    include_cleanup = False
    
    if total_deletes > 0:
        # Get more details for context
        source_fxc = {svc['name'] for svc in mirror.source_services.get('fxc', [])}
        target_fxc = {svc['name'] for svc in mirror.target_services.get('fxc', [])}
        fxc_to_delete = target_fxc - source_fxc
        fxc_to_keep = target_fxc & source_fxc  # intersection - same on both
        
        console.print(f"\n[bold yellow]⚠ Configuration Cleanup Needed[/bold yellow]")
        console.print(f"[dim]Target ({target_hostname}) has items that don't exist on source ({source_hostname})[/dim]")
        console.print()
        
        # FXC Services
        if cleanup_summary['fxc_to_delete'] > 0:
            console.print(f"  [red]✗ Delete:[/red] {cleanup_summary['fxc_to_delete']} FXC services")
            # Show sample of what will be deleted
            sample_delete = sorted(list(fxc_to_delete))[:3]
            if sample_delete:
                console.print(f"    [dim]e.g., {', '.join(sample_delete)}{'...' if len(fxc_to_delete) > 3 else ''}[/dim]")
        
        if len(source_fxc) > 0:
            console.print(f"  [green]✓ Keep/Add:[/green] {len(source_fxc)} FXC services from source")
            sample_keep = sorted(list(source_fxc))[:3]
            if sample_keep:
                console.print(f"    [dim]e.g., {', '.join(sample_keep)}{'...' if len(source_fxc) > 3 else ''}[/dim]")
        
        # Interfaces
        if cleanup_summary['interfaces_to_delete'] > 0:
            sub_count = cleanup_summary.get('_sub_interfaces', 0)
            parent_count = cleanup_summary.get('_parent_interfaces', 0)
            console.print(f"  [red]✗ Delete:[/red] {cleanup_summary['interfaces_to_delete']} interfaces ({sub_count} sub-ifs, {parent_count} parents)")
        
        # MH
        if cleanup_summary['mh_to_delete'] > 0:
            console.print(f"  [red]✗ Delete:[/red] {cleanup_summary['mh_to_delete']} multihoming configs")
        
        console.print()
        console.print("[dim]This ensures target matches source exactly (minus unique WAN/system)[/dim]")
        console.print()
        console.print("  [1] [green]Include cleanup[/green] - Delete extra, then apply mirror [bold](recommended)[/bold]")
        console.print("  [2] [yellow]Skip cleanup[/yellow] - Only add source config (keeps target's unique items)")
        
        cleanup_choice = Prompt.ask("Select", choices=["1", "2"], default="1")
        include_cleanup = (cleanup_choice == "1")
        
        if include_cleanup:
            console.print("[green]✓ Will delete extra configuration before applying mirror[/green]")
        else:
            console.print("[yellow]⚠ Skipping cleanup - target will have both its original AND source config[/yellow]")
    
    merged_config, line_count = generate_config_with_live_terminal(
        mirror, source_hostname, target_hostname
    )
    
    # Generate cleanup commands separately (will be pushed as Phase 1)
    cleanup_commands = ""
    cleanup_lines = 0
    if include_cleanup and total_deletes > 0:
        cleanup_commands = mirror.generate_cleanup_commands()
        if cleanup_commands:
            cleanup_lines = len(cleanup_commands.split('\n'))
            console.print(f"\n[bold yellow]📋 Two-Phase Mirror Operation:[/bold yellow]")
            console.print(f"  [red]Phase 1:[/red] Delete {cleanup_lines} items (services + interfaces)")
            console.print(f"  [green]Phase 2:[/green] Apply {line_count:,} lines of mirrored config")
    
    # Show detailed summary
    show_mirror_detailed_summary(mirror, merged_config, source_hostname, target_hostname)
    
    # Action menu with options
    import os
    from pathlib import Path
    from datetime import datetime
    
    while True:
        console.print(f"\n[bold cyan]Mirror Configuration for {target_hostname} - What would you like to do?[/bold cyan]")
        console.print(f"  [dim]Generated: {line_count:,} lines[/dim]")
        console.print()
        console.print("  [1] [green]Push to device[/green] - Apply mirrored configuration")
        console.print("  [2] [cyan]View configuration[/cyan] - Preview full config")
        console.print("  [3] [yellow]Save and edit[/yellow] - Save to file for manual editing")
        console.print("  [4] [magenta]View section[/magenta] - View specific section")
        console.print("  [5] [bold orange3]Modify sections[/bold orange3] - Keep/skip sections for {target_hostname}")
        console.print("  [B] Back/Cancel")
        
        action = Prompt.ask("Select action", choices=["1", "2", "3", "4", "5", "b", "B"], default="1")
        
        if action.lower() == 'b':
            console.print("[yellow]Mirror cancelled.[/yellow]")
            return False
        
        if action == "2":
            # View full config
            console.print("\n[dim]" + "─" * 80 + "[/dim]")
            lines = merged_config.split('\n')
            for line in lines[:100]:
                console.print(line)
            if len(lines) > 100:
                console.print(f"\n[dim]... ({len(lines) - 100} more lines)[/dim]")
            console.print("[dim]" + "─" * 80 + "[/dim]")
            continue
        
        if action == "3":
            # Save to file for editing
            save_dir = Path.home() / ".scaler" / "mirror_configs"
            save_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = save_dir / f"mirror_{target_hostname}_{timestamp}.txt"
            
            with open(save_path, 'w') as f:
                f.write(merged_config)
            
            console.print(f"[green]✓ Saved to: {save_path}[/green]")
            console.print(f"[dim]Edit the file, then use 'Saved Configs' menu to push.[/dim]")
            
            # Open in editor?
            if Confirm.ask("Open in editor now?", default=True):
                import subprocess
                editor = os.environ.get('EDITOR', 'nano')
                subprocess.call([editor, str(save_path)])
                
                # Reload after edit
                with open(save_path, 'r') as f:
                    merged_config = f.read()
                line_count = len(merged_config.split('\n'))
                console.print(f"[green]✓ Reloaded after edit ({line_count:,} lines)[/green]")
            continue
        
        if action == "4":
            # View specific section
            view_mirror_section(merged_config)
            continue
        
        if action == "5":
            # Modify sections - regenerate with different section selections
            merged_config, line_count = modify_mirror_sections(
                mirror, target_hostname, target_config
            )
            if merged_config is None:
                # User cancelled
                continue
            console.print(f"[green]✓ Regenerated with modified sections ({line_count:,} lines)[/green]")
            continue
        
        if action == "1":
            # Push to device - break out to push flow
            break
    
    # Step 6: Push
    console.print(f"\n[bold]Step 5: Push Configuration[/bold]")
    
    # =========================================================================
    # SMART DIFF ANALYSIS - Check what's different
    # =========================================================================
    diff_config = None
    diff_summary = None
    use_diff_mode = False
    
    # Analyze differences between source and target
    diff_config, diff_summary = mirror.generate_diff_only_config()
    diff_lines = len(diff_config.split('\n')) if diff_config.strip() else 0
    
    if diff_summary['total_changes'] > 0 or diff_summary['skipped'] > 0:
        console.print("\n[bold cyan]Smart Diff Analysis:[/bold cyan]")
        console.print(f"  ✓ [green]Identical (skip):[/green] {diff_summary['skipped']:,} items")
        console.print(f"  + [cyan]To add:[/cyan] {diff_summary['adds']:,} items")
        console.print(f"  ~ [yellow]To modify:[/yellow] {diff_summary['modifies']:,} items")
        console.print(f"  - [red]To delete:[/red] {diff_summary['deletes']:,} items")
        
        if diff_summary['skipped'] > 0 and diff_lines < line_count:
            console.print(f"\n  [dim]Full config: {line_count:,} lines | Diff-only: {diff_lines:,} lines ({100*diff_lines//line_count}% of full)[/dim]")
    
    # Use standard push flow with enhanced terminal UI
    # ask_push_method returns: (use_terminal_paste, dry_run, cancelled, use_merge, use_factory_reset)
    # prefer_terminal_paste=True for mirror mode - direct paste is more reliable for full configs
    push_result = ask_push_method(
        all_add_only=False, 
        config_text=merged_config, 
        prefer_terminal_paste=True,
        default_config_name=f"mirror_{target_hostname}"
    )
    use_terminal_paste, dry_run, cancelled, use_merge, use_factory_reset, custom_config_name = push_result
    
    if cancelled:
        console.print("[yellow]Push cancelled.[/yellow]")
        return False
    
    # =========================================================================
    # SMART DIFF MODE for Terminal Paste
    # =========================================================================
    if use_terminal_paste and diff_summary['skipped'] > 0 and diff_lines > 0 and diff_lines < line_count:
        console.print(f"\n[bold yellow]Terminal Paste Optimization Available![/bold yellow]")
        console.print(f"  Target already has {diff_summary['skipped']:,} identical items.")
        console.print(f"  [1] [green]Paste only changes[/green] ({diff_lines:,} lines) [bold]← Faster![/bold]")
        console.print(f"  [2] [dim]Paste full config[/dim] ({line_count:,} lines)")
        
        diff_choice = Prompt.ask("Select", choices=["1", "2"], default="1")
        
        if diff_choice == "1":
            use_diff_mode = True
            console.print(f"[green]✓ Using diff-only mode - {diff_lines:,} lines instead of {line_count:,}[/green]")
    
    # Use custom config name if provided
    if custom_config_name:
        # Save config locally with the custom name
        from pathlib import Path
        save_dir = Path.home() / ".scaler" / "mirror_configs"
        save_dir.mkdir(parents=True, exist_ok=True)
        local_save_path = save_dir / custom_config_name
        with open(local_save_path, 'w') as f:
            f.write(merged_config)
        console.print(f"[green]✓ Config saved locally: {local_save_path}[/green]")
    
    # Push action selection (commit check only vs full commit)
    if not use_factory_reset:
        console.print("\n[bold]Push Action:[/bold]")
        if cleanup_commands and cleanup_lines > 0:
            console.print(f"  [dim]Two-phase operation: Phase 1 deletes {cleanup_lines} items, Phase 2 applies {line_count:,} lines[/dim]")
            console.print("  [1] Commit check only (dry run) [dim]- validates both phases[/dim]")
            console.print("  [2] Push and commit now [dim]- commits Phase 1, then Phase 2[/dim]")
        else:
            console.print("  [1] Commit check only (dry run)")
            console.print("  [2] Push and commit now")
        action_choice = Prompt.ask("Select action", choices=["1", "2"], default="2")
        dry_run = (action_choice == "1")
    
    # Recommend live terminal for terminal paste
    raw_terminal = True
    if use_terminal_paste:
        console.print("[dim]Terminal paste mode with live terminal display enabled.[/dim]")
    elif not use_factory_reset:
        raw_terminal = Confirm.ask("Show live device terminal output?", default=True)
    
    # =========================================================================
    # DIFF MODE: Single-phase push with all changes in one config
    # =========================================================================
    if use_diff_mode and diff_config:
        console.print(f"\n[bold cyan]═══ Diff-Only Push ({diff_lines:,} lines) ═══[/bold cyan]")
        console.print(f"[dim]Skipping {diff_summary['skipped']:,} identical items[/dim]")
        
        success, message = push_and_verify(
            device=target_device,
            config_text=diff_config,
            dry_run=dry_run,
            use_terminal_paste=True,  # Diff mode is always terminal paste
            use_merge=False,  # Diff config includes all needed commands
            use_factory_reset=False,
            raw_terminal=raw_terminal,
            config_name=custom_config_name.replace('.txt', '_diff.txt') if custom_config_name else f"mirror_{target_device.hostname}_diff.txt",
            phase_info="Diff-Only Push"
        )
    # =========================================================================
    # TWO-PHASE PUSH when there are cleanup commands (full config mode)
    # Phase 1: Delete old config → commit
    # Phase 2: Apply new config → commit
    # =========================================================================
    elif cleanup_commands and cleanup_lines > 0 and not use_factory_reset and not use_diff_mode:
        console.print(f"\n[bold yellow]═══ Phase 1/2: Deleting Old Configuration ({cleanup_lines} deletes) ═══[/bold yellow]")
        
        phase1_success, phase1_msg = push_and_verify(
            device=target_device,
            config_text=cleanup_commands,
            dry_run=dry_run,
            use_terminal_paste=use_terminal_paste,
            use_merge=False,  # Delete commands, not merge
            use_factory_reset=False,
            raw_terminal=raw_terminal,
            config_name=custom_config_name.replace('.txt', '_cleanup.txt') if custom_config_name else f"mirror_{target_device.hostname}_cleanup.txt",
            delete_line_count=cleanup_lines,
            phase_info="Phase 1/2: Delete"
        )
        
        if not phase1_success:
            console.print(f"\n[bold red]✗ Phase 1 (cleanup) failed: {phase1_msg}[/bold red]")
            console.print("[dim]Aborting Phase 2. Check device and retry.[/dim]")
            return False
        
        console.print(f"[green]✓ Phase 1 complete - old configuration deleted[/green]")
        
        if dry_run:
            console.print("[yellow]Dry run - Phase 2 skipped[/yellow]")
            return True
        
        # Small delay between phases
        import time
        console.print("[dim]Waiting 5s before Phase 2...[/dim]")
        time.sleep(5)
        
        console.print(f"\n[bold cyan]═══ Phase 2/2: Applying New Configuration ({line_count:,} lines) ═══[/bold cyan]")
        console.print(f"[dim]   (Phase 1 deleted {cleanup_lines} items successfully)[/dim]")
        
        success, message = push_and_verify(
            device=target_device,
            config_text=merged_config,
            dry_run=False,  # Already did dry run in Phase 1 if requested
            use_terminal_paste=use_terminal_paste,
            use_merge=use_merge,
            use_factory_reset=False,
            raw_terminal=raw_terminal,
            config_name=custom_config_name or f"mirror_{target_device.hostname}.txt",
            phase_info="Phase 2/2: Apply"
        )
    else:
        # Single-phase push (no cleanup needed, or using factory reset)
        if cleanup_commands and use_factory_reset:
            # Factory reset handles cleanup implicitly
            console.print("[dim]Factory reset will implicitly clear existing config[/dim]")
        
        success, message = push_and_verify(
            device=target_device,
            config_text=merged_config,
            dry_run=dry_run,
            use_terminal_paste=use_terminal_paste,
            use_merge=use_merge,
            use_factory_reset=use_factory_reset,
            raw_terminal=raw_terminal,
            config_name=custom_config_name or f"mirror_{target_device.hostname}.txt"
        )
    
    if success:
        console.print(f"\n[bold green]✓ Successfully mirrored configuration from {source_hostname} to {target_hostname}![/bold green]")
    else:
        console.print(f"\n[bold red]✗ Mirror operation failed: {message}[/bold red]")
    
    return success


# ═══════════════════════════════════════════════════════════════════════════════
# MULTI-TARGET MIRROR WIZARD - 1 Source → Multiple Targets
# ═══════════════════════════════════════════════════════════════════════════════

def run_multi_target_mirror_wizard(
    multi_ctx: 'MultiDeviceContext'
) -> bool:
    """
    Run the Multi-Target Mirror Configuration wizard.
    
    Flow:
    1. Select ONE source device (copy FROM)
    2. Select MULTIPLE target devices (copy TO)
    3. Configure per-device refinements for each target
    4. Generate unique configs per target
    5. Push to all targets in parallel
    
    Args:
        multi_ctx: MultiDeviceContext with devices
        
    Returns:
        True if configuration was mirrored successfully to at least one target
    """
    from ..interactive_scale import ask_push_method, push_and_verify_multi
    from rich.table import Table
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    
    if len(multi_ctx.devices) < 2:
        console.print("[red]Multi-target mirror requires at least 2 devices.[/red]")
        return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 1: Select SOURCE device (copy FROM)
    # ═══════════════════════════════════════════════════════════════════════════
    console.print(Panel(
        "[bold white]🪞 Multi-Target Mirror Mode[/bold white]\n\n"
        "[bold cyan]Copy configuration from ONE source to MULTIPLE targets[/bold cyan]\n\n"
        "[dim]Each target can have unique refinements:[/dim]\n"
        "  • Interface mapping (same/offset/custom)\n"
        "  • Loopback/RD adjustments (auto-detected)\n"
        "  • Per-device section modifications",
        title="[bold magenta]Mirror 1 → Many[/bold magenta]",
        border_style="magenta",
        padding=(0, 2)
    ))
    
    console.print(f"\n[bold white on blue] STEP 1 [/bold white on blue] [bold]SELECT SOURCE DEVICE (copy FROM)[/bold]\n")
    
    # Helper to validate config
    def is_valid_config(config_text: str) -> bool:
        """Check if config is a valid running config (not empty/reset)."""
        if not config_text or len(config_text) < 500:
            return False
        if 'system' not in config_text or 'interfaces' not in config_text:
            return False
        # Check for real config indicators (hostname/name OR login config OR protocols)
        # Not all devices have hostname configured, but they'll have login users or protocols
        has_name = 'hostname' in config_text or '\n  name ' in config_text
        has_login = 'user dnroot' in config_text or 'login' in config_text
        has_protocols = 'protocols' in config_text
        if not (has_name or has_login or has_protocols):
            return False
        return True
    
    # Build source options table with VRF column
    source_table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    source_table.add_column("#", style="dim", width=3)
    source_table.add_column("Device", style="cyan", width=20)
    source_table.add_column("Loopback", width=15)
    source_table.add_column("FXC", justify="right", width=8)
    source_table.add_column("VPLS", justify="right", width=8)
    source_table.add_column("VRF", justify="right", width=8)
    source_table.add_column("MH", justify="right", width=8)
    source_table.add_column("Status", justify="center", width=12)
    
    source_data = []
    for dev in multi_ctx.devices:
        config = multi_ctx.configs.get(dev.hostname, "")
        config_valid = is_valid_config(config) if config else False
        
        if config:
            if config_valid:
                lo0 = get_lo0_ip_from_config(config)
                services = parse_existing_evpn_services(config)
                fxc_count = len(services.get('fxc', []))
                vpls_count = len(services.get('vpls', []))
                vrf_count = len(parse_vrf_instances(config))
                mh_count = len(parse_existing_multihoming(config))
            else:
                lo0 = None
                fxc_count = vpls_count = vrf_count = mh_count = 0
            
            source_data.append({
                'device': dev,
                'hostname': dev.hostname,
                'lo0': lo0,
                'fxc': fxc_count,
                'vpls': vpls_count,
                'vrf': vrf_count,
                'mh': mh_count,
                'config': config,
                'valid': config_valid
            })
    
    if len(source_data) < 2:
        console.print("[yellow]Not enough devices with configurations. Run Refresh first.[/yellow]")
        return False
    
    valid_indices = []
    for i, data in enumerate(source_data, 1):
        if data['valid']:
            fxc_str = f"[bold green]{data['fxc']:,}[/bold green]" if data['fxc'] > 0 else "[dim]0[/dim]"
            vpls_str = f"[bold blue]{data['vpls']:,}[/bold blue]" if data['vpls'] > 0 else "[dim]0[/dim]"
            vrf_str = f"[bold magenta]{data['vrf']:,}[/bold magenta]" if data['vrf'] > 0 else "[dim]0[/dim]"
            mh_str = f"[bold yellow]{data['mh']:,}[/bold yellow]" if data['mh'] > 0 else "[dim]0[/dim]"
            
            source_table.add_row(
                str(i),
                data['hostname'],
                data['lo0'] or "[dim]N/A[/dim]",
                fxc_str,
                vpls_str,
                vrf_str,
                mh_str,
                "[green]✓ Ready[/green]"
            )
            valid_indices.append(i)
        else:
            # Invalid/empty config - check for device state (GI mode, etc.)
            # Load device state from operational.json
            import json
            from pathlib import Path
            device_state = ""
            try:
                op_path = Path(f"db/configs/{data['hostname']}/operational.json")
                if op_path.exists():
                    with open(op_path) as f:
                        op_data = json.load(f)
                        device_state = op_data.get('device_state', '')
                        if op_data.get('recovery_mode_detected'):
                            device_state = op_data.get('recovery_type', device_state)
            except:
                pass
            
            # Show device state if in recovery mode
            if device_state in ('GI', 'BASEOS_SHELL', 'ONIE', 'DN_RECOVERY'):
                status = f"[cyan]{device_state}[/cyan]"
            else:
                status = "[red]✗ No config[/red]"
            
            source_table.add_row(
                f"[dim]{i}[/dim]",
                f"[dim]{data['hostname']}[/dim]",
                "[dim]N/A[/dim]",
                "[dim]-[/dim]",
                "[dim]-[/dim]",
                "[dim]-[/dim]",
                "[dim]-[/dim]",
                status
            )
    
    console.print(source_table)
    console.print("\n  [B] Back")
    
    # Only allow selecting valid sources
    if not valid_indices:
        console.print("\n[red]No valid source devices available.[/red]")
        console.print("[dim]Run Refresh to update device configurations.[/dim]")
        return False
    
    choices = [str(i) for i in valid_indices] + ['b', 'B']
    source_choice = Prompt.ask("\nSelect source device", choices=choices, default=str(valid_indices[0]) if valid_indices else "b")
    
    if source_choice.lower() == 'b':
        return False
    
    source_idx = int(source_choice) - 1
    source_device = source_data[source_idx]['device']
    source_hostname = source_device.hostname
    source_config = source_data[source_idx]['config']
    source_lo0 = source_data[source_idx]['lo0']
    
    console.print(f"\n[green]✓ SOURCE: {source_hostname}[/green]")
    console.print(f"  [dim]Lo0: {source_lo0 or 'N/A'}, {source_data[source_idx]['fxc']} FXC, {source_data[source_idx]['vpls']} VPLS, {source_data[source_idx]['vrf']} VRF[/dim]")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 2: Select TARGET devices (copy TO)
    # ═══════════════════════════════════════════════════════════════════════════
    console.print(f"\n[bold white on green] STEP 2 [/bold white on green] [bold]SELECT TARGET DEVICES (copy TO)[/bold]\n")
    
    # Build target options (all except source)
    target_table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    target_table.add_column("#", style="dim", width=3)
    target_table.add_column("Device", style="yellow", width=20)
    target_table.add_column("Loopback", width=15)
    target_table.add_column("Current Services", width=20)
    target_table.add_column("Interfaces", justify="right", width=12)
    
    target_data = [d for d in source_data if d['hostname'] != source_hostname]
    
    for i, data in enumerate(target_data, 1):
        svc_summary = []
        if data['fxc'] > 0:
            svc_summary.append(f"{data['fxc']} FXC")
        if data['vpls'] > 0:
            svc_summary.append(f"{data['vpls']} VPLS")
        if not svc_summary:
            svc_summary = ["[dim]None[/dim]"]
        
        target_table.add_row(
            str(i),
            data['hostname'],
            data['lo0'] or "[dim]N/A[/dim]",
            ", ".join(svc_summary),
            f"{data['iface_count']:,}" if data['iface_count'] > 0 else "[dim]0[/dim]"
        )
    
    console.print(target_table)
    console.print()
    console.print("  [A] Select ALL targets")
    console.print("  Enter device numbers (comma-separated, e.g., 1,2,3)")
    console.print("  [B] Back")
    
    target_choice = Prompt.ask("\nSelect targets", default="a")
    
    if target_choice.lower() == 'b':
        return False
    
    selected_targets = []
    if target_choice.lower() == 'a':
        selected_targets = target_data.copy()
    else:
        try:
            indices = [int(x.strip()) - 1 for x in target_choice.split(',')]
            for idx in indices:
                if 0 <= idx < len(target_data):
                    selected_targets.append(target_data[idx])
        except ValueError:
            console.print("[red]Invalid selection[/red]")
            return False
    
    if not selected_targets:
        console.print("[yellow]No targets selected[/yellow]")
        return False
    
    console.print(f"\n[green]✓ TARGETS: {', '.join([t['hostname'] for t in selected_targets])}[/green]")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 3: Configure per-device refinements
    # ═══════════════════════════════════════════════════════════════════════════
    console.print(f"\n[bold white on cyan] STEP 3 [/bold white on cyan] [bold]CONFIGURE REFINEMENTS FOR EACH TARGET[/bold]\n")
    
    # Ask for global or per-device interface mapping strategy
    console.print(Panel(
        "[bold]Interface Mapping Strategy[/bold]\n\n"
        "  [1] [green]Same for ALL[/green] - Use same mapping strategy for all targets\n"
        "  [2] [yellow]Per-device[/yellow] - Configure mapping separately for each target\n"
        "  [B] Back",
        border_style="cyan",
        padding=(0, 2)
    ))
    
    mapping_mode = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="1")
    
    if mapping_mode.lower() == 'b':
        return False
    
    global_strategy = None
    if mapping_mode == "1":
        # Global mapping strategy
        console.print("\n[bold]Select mapping strategy for ALL targets:[/bold]")
        console.print("  [1] [green]Auto-map[/green] - Match interfaces by slot/port")
        console.print("  [2] [cyan]Copy names[/cyan] - Use exact same interface names")
        console.print("  [3] [yellow]Custom[/yellow] - Define explicit mappings")
        
        strat_choice = Prompt.ask("Select", choices=["1", "2", "3"], default="1")
        global_strategy = {"1": "auto", "2": "copy", "3": "custom"}[strat_choice]
        console.print(f"[green]✓ Using '{global_strategy}' mapping for all targets[/green]")
    
    # Prepare per-target configurations
    target_configs = {}  # hostname → {'mirror': ConfigMirror, 'config': str, 'strategy': str}
    
    for target in selected_targets:
        target_hostname = target['hostname']
        target_config = target['config']
        target_lo0 = target['lo0']
        
        console.print(f"\n[bold cyan]━━━ Configuring {target_hostname} ━━━[/bold cyan]")
        
        # Create mirror object
        mirror = ConfigMirror(
            source_config=source_config,
            target_config=target_config,
            source_hostname=source_hostname,
            target_hostname=target_hostname
        )
        
        # Check for missing mandatory values
        target_summary = mirror.get_target_summary()
        source_summary = mirror.get_source_summary()
        
        if not target_lo0:
            console.print(f"  [yellow]⚠ {target_hostname} missing Loopback IP (required for RD)[/yellow]")
            console.print(f"  [dim]Source {source_hostname} has: {source_lo0}[/dim]")
            
            lo0_input = Prompt.ask(f"  Enter Loopback IP for {target_hostname} (e.g., 1.1.1.1) [B]ack", default="")
            if lo0_input.lower() == 'b':
                return False
            if not lo0_input:
                console.print(f"  [yellow]Skipping {target_hostname} - Loopback required[/yellow]")
                continue
            
            # Normalize loopback - always add /32 if not specified
            lo0_input = _normalize_loopback_ip(lo0_input)
            mirror.target_lo0 = lo0_input
            mirror._compile_transform_patterns()
            target_lo0 = lo0_input
        
        console.print(f"  [green]✓[/green] Lo0: {target_lo0}")
        
        # Determine strategy
        if mapping_mode == "2":
            # Per-device strategy selection
            console.print(f"\n  Interface mapping for {target_hostname}:")
            console.print("    [1] Auto-map  [2] Copy names  [3] Custom")
            strat_choice = Prompt.ask("    Select", choices=["1", "2", "3"], default="1")
            strategy = {"1": "auto", "2": "copy", "3": "custom"}[strat_choice]
        else:
            strategy = global_strategy
        
        # Apply mapping
        if strategy == 'auto':
            mapping = mirror.map_interfaces_auto()
        elif strategy == 'copy':
            mapping = mirror.map_interfaces_copy()
        else:
            mapping = configure_custom_interface_mapping(mirror)
        
        console.print(f"  [green]✓[/green] Mapped {len(mapping)} interfaces ({strategy})")
        
        # Generate config for this target
        merged_config, line_count = generate_config_with_live_terminal(
            mirror, source_hostname, target_hostname, quiet=True
        )
        
        console.print(f"  [green]✓[/green] Generated {line_count:,} lines")
        
        # Store for later
        target_configs[target_hostname] = {
            'device': target['device'],
            'mirror': mirror,
            'config': merged_config,
            'line_count': line_count,
            'strategy': strategy
        }
    
    if not target_configs:
        console.print("[yellow]No targets configured successfully[/yellow]")
        return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 4: Summary and confirmation
    # ═══════════════════════════════════════════════════════════════════════════
    console.print(f"\n[bold white on yellow] STEP 4 [/bold white on yellow] [bold]REVIEW & PUSH[/bold]\n")
    
    summary_table = Table(box=box.ROUNDED, title=f"[bold]Mirror from {source_hostname} to {len(target_configs)} targets[/bold]")
    summary_table.add_column("Target", style="yellow", width=20)
    summary_table.add_column("Mapping", width=12)
    summary_table.add_column("Config Lines", justify="right", width=12)
    summary_table.add_column("Loopback", width=15)
    
    for hostname, data in target_configs.items():
        summary_table.add_row(
            hostname,
            data['strategy'],
            f"{data['line_count']:,}",
            data['mirror'].target_lo0 or "N/A"
        )
    
    console.print(summary_table)
    
    console.print("\n[bold]Options:[/bold]")
    console.print("  [1] [green]Push to ALL targets[/green] (parallel)")
    console.print("  [2] [cyan]View config for specific target[/cyan]")
    console.print("  [3] [yellow]Save all configs to files[/yellow]")
    console.print("  [B] Back/Cancel")
    
    action = Prompt.ask("Select", choices=["1", "2", "3", "b", "B"], default="1")
    
    if action.lower() == 'b':
        return False
    
    if action == "2":
        # View specific target config
        console.print("\nSelect target to view:")
        for i, hostname in enumerate(target_configs.keys(), 1):
            console.print(f"  [{i}] {hostname}")
        
        view_choice = Prompt.ask("Select", choices=[str(i) for i in range(1, len(target_configs) + 1)])
        view_hostname = list(target_configs.keys())[int(view_choice) - 1]
        view_config = target_configs[view_hostname]['config']
        
        console.print(f"\n[bold]Configuration for {view_hostname}:[/bold]")
        console.print("[dim]" + "─" * 80 + "[/dim]")
        lines = view_config.split('\n')
        for line in lines[:50]:
            console.print(line)
        if len(lines) > 50:
            console.print(f"\n[dim]... ({len(lines) - 50} more lines)[/dim]")
        console.print("[dim]" + "─" * 80 + "[/dim]")
        
        # Recurse back to options
        return run_multi_target_mirror_wizard(multi_ctx)
    
    if action == "3":
        # Save all configs
        from pathlib import Path
        from datetime import datetime
        
        save_dir = Path.home() / ".scaler" / "mirror_configs"
        save_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for hostname, data in target_configs.items():
            save_path = save_dir / f"mirror_{source_hostname}_to_{hostname}_{timestamp}.txt"
            with open(save_path, 'w') as f:
                f.write(data['config'])
            console.print(f"[green]✓ Saved: {save_path}[/green]")
        
        console.print(f"\n[green]All {len(target_configs)} configs saved![/green]")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 5: Push to all targets in parallel
    # ═══════════════════════════════════════════════════════════════════════════
    if action == "1":
        console.print(f"\n[bold white on green] STEP 5 [/bold white on green] [bold]PUSHING TO {len(target_configs)} TARGETS[/bold]\n")
        
        # Ask push method
        push_result = ask_push_method(
            all_add_only=False,
            config_text=list(target_configs.values())[0]['config'],
            prefer_terminal_paste=True,
            default_config_name=f"mirror_{source_hostname}_multi"
        )
        use_terminal_paste, dry_run, cancelled, use_merge, use_factory_reset, _ = push_result
        
        if cancelled:
            console.print("[yellow]Push cancelled[/yellow]")
            return False
        
        # Prepare device configs dict for parallel push
        device_configs = {
            hostname: data['config']
            for hostname, data in target_configs.items()
        }
        
        # Use multi-device parallel push
        results = push_and_verify_multi(
            multi_ctx,
            device_configs,
            dry_run=dry_run,
            use_terminal_paste=use_terminal_paste,
            use_merge=use_merge,
            use_factory_reset=use_factory_reset
        )
        
        # Summary
        success_count = sum(1 for success, _ in results.values() if success)
        fail_count = len(results) - success_count
        
        if success_count == len(results):
            console.print(f"\n[bold green]✓ Successfully mirrored to ALL {success_count} targets![/bold green]")
        elif success_count > 0:
            console.print(f"\n[bold yellow]⚠ Mirrored to {success_count}/{len(results)} targets[/bold yellow]")
        else:
            console.print(f"\n[bold red]✗ Mirror failed on all targets[/bold red]")
        
        # Show per-device results
        for hostname, (success, message) in results.items():
            if success:
                console.print(f"  [green]✓[/green] {hostname}: {message}")
            else:
                console.print(f"  [red]✗[/red] {hostname}: {message}")
        
        return success_count > 0
    
    return False


def run_mirror_system_only_wizard(
    multi_ctx: 'MultiDeviceContext',
    target_device: Any = None,
    source_device: Any = None
) -> bool:
    """
    Quick wizard to mirror ONLY the system hierarchy from source to target.
    
    This is a simplified flow that:
    1. Selects source device (if not provided)
    2. Selects target device (if not provided)
    3. Mirrors ONLY system section (with hostname change and uniqueness preservation)
    4. Pushes the config
    
    Args:
        multi_ctx: MultiDeviceContext with devices
        target_device: Optional target device (if None, prompts for selection)
        source_device: Optional source device (if None, prompts for selection)
        
    Returns:
        True if system was mirrored successfully
    """
    from ..interactive_scale import ask_push_method, push_and_verify
    from rich.table import Table
    from rich.panel import Panel
    
    if len(multi_ctx.devices) < 2:
        console.print("[yellow]⚠ At least 2 devices required for mirroring[/yellow]")
        console.print("[dim]Add more devices to the session first.[/dim]")
        return False
    
    # Step 1: Select target device
    if target_device is None:
        # Prompt for target device selection
        console.print(Panel(
            "[bold]🪞 Mirror System Only[/bold]\n\n"
            "[dim]Quick option to mirror ONLY the system hierarchy[/dim]\n"
            "[dim]Hostname will be changed, device uniqueness preserved[/dim]",
            box=box.ROUNDED,
            border_style="green"
        ))
        
        console.print(f"\n[bold cyan]SELECT TARGET DEVICE (copy TO):[/bold cyan]")
        console.print()
        
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=3)
        table.add_column("Hostname", style="cyan", width=20)
        
        for i, dev in enumerate(multi_ctx.devices, 1):
            table.add_row(str(i), dev.hostname)
        
        console.print(table)
        console.print("  [B] Back")
        
        choices = [str(i) for i in range(1, len(multi_ctx.devices) + 1)] + ['b', 'B']
        choice = Prompt.ask("\nSelect target device", choices=choices, default="b")
        
        if choice.lower() == 'b':
            return False
        
        target_idx = int(choice) - 1
        target_device = multi_ctx.devices[target_idx]
    else:
        # Target device already specified (from single-device mode)
        console.print(Panel(
            "[bold]🪞 Mirror System Only[/bold]\n\n"
            "[dim]Quick option to mirror ONLY the system hierarchy[/dim]\n"
            "[dim]Hostname will be changed, device uniqueness preserved[/dim]",
            box=box.ROUNDED,
            border_style="green"
        ))
    
    target_hostname = target_device.hostname
    target_config = multi_ctx.configs.get(target_hostname, "")
    
    if not target_config:
        console.print(f"[yellow]No configuration found for {target_hostname}.[/yellow]")
        console.print("[dim]Run Refresh first to fetch device configuration.[/dim]")
        return False
    
    # Step 2: Select source device (if not provided)
    if source_device is None:
        console.print(f"\n[bold cyan]SELECT SOURCE DEVICE (copy FROM):[/bold cyan]")
        console.print()
        
        source_options = []
        source_data = []
        
        for dev in multi_ctx.devices:
            if dev.hostname != target_hostname:
                config = multi_ctx.configs.get(dev.hostname, "")
                if config:
                    source_system = extract_hierarchy_section(config, 'system')
                    has_system = bool(source_system and source_system.strip())
                    
                    source_options.append(dev)
                    source_data.append({
                        'hostname': dev.hostname,
                        'has_system': has_system,
                        'config': config
                    })
        
        if not source_options:
            console.print("[yellow]No other devices available as source.[/yellow]")
            return False
        
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=3)
        table.add_column("Hostname", style="cyan", width=20)
        table.add_column("Has System", justify="center", width=12)
        
        for i, data in enumerate(source_data, 1):
            system_str = "[green]✓ Yes[/green]" if data['has_system'] else "[dim]No[/dim]"
            table.add_row(str(i), data['hostname'], system_str)
        
        console.print(table)
        console.print("  [B] Back")
        
        choices = [str(i) for i in range(1, len(source_options) + 1)] + ['b', 'B']
        choice = Prompt.ask("\nSelect source device", choices=choices, default="b")
        
        if choice.lower() == 'b':
            return False
        
        source_idx = int(choice) - 1
        source_device = source_options[source_idx]
        source_hostname = source_device.hostname
        source_config = source_data[source_idx]['config']
    else:
        # Source device already provided
        source_hostname = source_device.hostname
        source_config = multi_ctx.configs.get(source_hostname, "")
        
        if not source_config:
            console.print(f"[yellow]No configuration found for {source_hostname}.[/yellow]")
            return False
        
        # Check if source has system config
        source_system = extract_hierarchy_section(source_config, 'system')
        if not source_system or not source_system.strip():
            console.print(f"[yellow]⚠ Source device {source_hostname} has no system configuration[/yellow]")
            if not Confirm.ask("Continue anyway?", default=False):
                return False
    
    console.print(f"[green]✓ Selected source: {source_hostname} → target: {target_hostname}[/green]")
    
    # Step 3: Create mirror instance with ONLY system section selected
    mirror = ConfigMirror(
        source_config=source_config,
        target_config=target_config,
        source_hostname=source_hostname,
        target_hostname=target_hostname
    )
    
    # Set section selection to ONLY system
    mirror.section_selection = {
        'system': True,
        'services': False,
        'service_interfaces': False,
        'multihoming': False,
        'routing': False,
        'routing_policy': False,
        'qos': False,
        'acls': False,
        'protocols': False,
    }
    
    # Generate config with only system section
    console.print(f"\n[bold]Generating system-only configuration...[/bold]")
    merged_config = mirror.generate_merged_config()
    
    if not merged_config or 'system' not in merged_config.lower():
        console.print("[yellow]⚠ No system configuration generated[/yellow]")
        return False
    
    # Show what will be mirrored
    source_system = extract_hierarchy_section(source_config, 'system')
    system_lines = len([l for l in merged_config.split('\n') if 'system' in l.lower() or l.strip().startswith('hostname')])
    
    console.print(Panel(
        f"[bold]📋 System Mirror Summary[/bold]\n\n"
        f"[cyan]Source:[/cyan] {source_hostname}\n"
        f"[green]Target:[/green] {target_hostname}\n\n"
        f"[dim]System config will be mirrored with:[/dim]\n"
        f"  • Hostname changed to: [bold]{target_hostname}[/bold]\n"
        f"  • Device uniqueness preserved (ISO-network, etc.)\n"
        f"  • ~{system_lines} lines",
        box=box.ROUNDED,
        border_style="green"
    ))
    
    # Proceed with system mirror? - with [B] Back option per rules
    console.print("\n[bold]Proceed with system mirror?[/bold]")
    console.print("  [Y] Yes - continue")
    console.print("  [N] No - cancel")
    console.print("  [B] Back")
    proceed_choice = Prompt.ask("Select", choices=["y", "Y", "n", "N", "b", "B"], default="y").lower()
    
    if proceed_choice == 'b':
        return False
    if proceed_choice == 'n':
        console.print("[yellow]System mirror cancelled.[/yellow]")
        return False
    
    # Ask for push method (terminal paste, file upload, etc.)
    from ..interactive_scale import ask_push_method
    
    console.print(f"\n[bold cyan]Select Push Method:[/bold cyan]")
    use_terminal_paste, dry_run, cancelled, use_merge, use_factory_reset, config_name = ask_push_method(
        all_add_only=False,
        config_text=merged_config,
        prefer_terminal_paste=True,  # Prefer terminal paste for quick operations
        default_config_name=f"mirror_system_{target_hostname}.txt",
        skip_action_selection=False,
        device_hostname=target_hostname  # Pass target device hostname for better time estimation
    )
    
    if cancelled:
        console.print("[yellow]System mirror cancelled.[/yellow]")
        return False
    
    # Push the config
    console.print(f"\n[bold green]Pushing system configuration to {target_hostname}...[/bold green]")
    
    success, message = push_and_verify(
        target_device,
        merged_config,
        dry_run=dry_run,
        use_terminal_paste=use_terminal_paste,
        use_merge=use_merge,  # Use merge to preserve other config
        use_factory_reset=use_factory_reset,
        config_name=config_name or f"mirror_system_{target_hostname}.txt"
    )
    
    if success:
        console.print(f"\n[bold green]✓ Successfully mirrored system config from {source_hostname} to {target_hostname}![/bold green]")
        return True
    else:
        console.print(f"\n[bold red]✗ System mirror failed: {message}[/bold red]")
        return False
