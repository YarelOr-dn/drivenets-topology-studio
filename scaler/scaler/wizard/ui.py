"""
UI and Display Functions for the SCALER Wizard.

This module contains:
- Console output functions
- Prompt helpers with navigation support
- Display functions (split view, summaries, banners)
"""

import re
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.syntax import Syntax
from rich import box

from .core import BackException, TopException, get_wizard_state

# Global console instance
console = Console()


def show_navigation_help():
    """Show navigation options available in the wizard."""
    console.print("\n[dim]Navigation: [B] Back to previous prompt | [T] Top (restart entire wizard)[/dim]")


def print_wizard_banner():
    """Print the wizard banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════════╗
║              SCALER Interactive Configuration Wizard              ║
║                                                                   ║
║     Step-by-step guide to create scaled DNOS configurations      ║
╚═══════════════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold cyan")


def prompt_with_nav(
    prompt_text: str,
    choices: List[str] = None,
    default: str = None,
    show_nav: bool = True,
    is_int: bool = False
) -> str:
    """Prompt with automatic Back/Top navigation support.
    
    Automatically adds B/T to choices and raises appropriate exceptions.
    
    Args:
        prompt_text: The prompt message
        choices: List of valid choices (B/T added automatically)
        default: Default value
        show_nav: Whether to show [B] Back | [T] Top hint
        is_int: Whether to use IntPrompt instead of Prompt
        
    Returns:
        User's input (lowercase for choice-based prompts)
        
    Raises:
        BackException: When user enters 'b' or 'B'
        TopException: When user enters 't' or 'T'
    """
    # Add navigation options to choices if provided
    if choices is not None:
        nav_choices = ['b', 'B', 't', 'T']
        full_choices = list(choices) + [c for c in nav_choices if c.lower() not in [x.lower() for x in choices]]
    else:
        full_choices = None
    
    # Show navigation hint
    if show_nav:
        console.print("[dim]  [B] Back | [T] Top[/dim]")
    
    # Get input
    if is_int:
        try:
            result = Prompt.ask(prompt_text, default=str(default) if default else None)
            if result.lower() == 'b':
                raise BackException()
            if result.lower() == 't':
                raise TopException()
            return int(result)
        except ValueError:
            if result.lower() in ['b', 't']:
                raise BackException() if result.lower() == 'b' else TopException()
            raise
    else:
        if full_choices:
            result = Prompt.ask(prompt_text, choices=full_choices, default=default)
        else:
            result = Prompt.ask(prompt_text, default=default)
        
        # Handle navigation
        if result.lower() == 'b':
            raise BackException()
        if result.lower() == 't':
            raise TopException()
        
        return result.lower() if full_choices else result


def input_with_nav(prompt_text: str = "") -> str:
    """Get user input with Back/Top navigation support.
    
    Use this for free-form text input where B/T should still work.
    
    Args:
        prompt_text: Optional prompt text
        
    Returns:
        User's input string
        
    Raises:
        BackException: When user enters just 'b' or 'B'
        TopException: When user enters just 't' or 'T'
    """
    if prompt_text:
        result = input(prompt_text)
    else:
        result = input()
    
    # Check for navigation (exact match, case insensitive)
    if result.strip().lower() == 'b':
        raise BackException()
    if result.strip().lower() == 't':
        raise TopException()
    
    return result


def display_split_view(left_title: str, left_content: List[str], 
                       right_title: str, right_content: List[str]):
    """Display a split view for two devices."""
    from rich.columns import Columns
    
    left_panel = Panel(
        "\n".join(left_content),
        title=f"[bold cyan]{left_title}[/bold cyan]",
        border_style="cyan",
        expand=True
    )
    
    right_panel = Panel(
        "\n".join(right_content),
        title=f"[bold green]{right_title}[/bold green]",
        border_style="green",
        expand=True
    )
    
    console.print(Columns([left_panel, right_panel], expand=True))


def show_section_summary(
    section_name: str,
    summary_items: Dict[str, Any],
    config_preview: Optional[str] = None,
    max_preview_lines: int = 15
) -> None:
    """Display a summary after completing a configuration section.
    
    Args:
        section_name: Name of the section (e.g., "Interfaces", "Services")
        summary_items: Dictionary of key-value pairs to display
        config_preview: Optional config text to show preview
        max_preview_lines: Max lines to show from config preview
    """
    console.print(f"\n[bold green]{'─'*60}[/bold green]")
    console.print(f"[bold green]✓ {section_name} Configuration Complete[/bold green]")
    console.print(f"[bold green]{'─'*60}[/bold green]")
    
    # Create summary table
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    
    for key, value in summary_items.items():
        if value is not None:
            table.add_row(key, str(value))
    
    console.print(table)
    
    # Show config preview if provided
    if config_preview:
        console.print(f"\n[dim]Configuration Preview (first {max_preview_lines} lines):[/dim]")
        lines = config_preview.split('\n')
        preview_lines = lines[:max_preview_lines]
        for line in preview_lines:
            console.print(f"[dim]{line}[/dim]")
        if len(lines) > max_preview_lines:
            console.print(f"[dim]  ... ({len(lines) - max_preview_lines} more lines)[/dim]")
    
    console.print()


def view_current_config(hierarchy: str = None):
    """Display a summary of the current device configuration for a specific hierarchy or all.
    
    Shows counts and key info, not the full raw config.
    
    Args:
        hierarchy: Specific hierarchy to view, or None for menu
    """
    # Late imports to avoid circular dependencies
    from .parsers import extract_hierarchy_section
    from .interfaces import categorize_interfaces_by_type
    
    _current_state = get_wizard_state()
    
    if _current_state is None or not _current_state.current_config:
        console.print("[yellow]No current configuration available[/yellow]")
        return
    
    if hierarchy:
        # View specific hierarchy SUMMARY
        section = extract_hierarchy_section(_current_state.current_config, hierarchy)
        if section:
            lines = section.strip().split('\n')
            line_count = len(lines)
            
            console.print(f"\n[bold cyan]{hierarchy.upper()} Summary:[/bold cyan]")
            
            if hierarchy == 'system':
                # Parse system info
                name = re.search(r'^\s+name\s+(\S+)', section, re.MULTILINE)
                profile = re.search(r'^\s+profile\s+(\S+)', section, re.MULTILINE)
                timezone = re.search(r'^\s+timezone\s+(\S+)', section, re.MULTILINE)
                users = re.findall(r'^\s+user\s+(\S+)', section, re.MULTILINE)
                
                table = Table(box=box.SIMPLE, show_header=False)
                table.add_column("Property", style="cyan", width=15)
                table.add_column("Value", style="white")
                if name:
                    table.add_row("Name", name.group(1))
                if profile:
                    table.add_row("Profile", profile.group(1))
                if timezone:
                    table.add_row("Timezone", timezone.group(1))
                if users:
                    table.add_row("Users", f"{len(users)} ({', '.join(users[:3])}{'...' if len(users) > 3 else ''})")
                table.add_row("Total Lines", str(line_count))
                console.print(table)
                
            elif hierarchy == 'interfaces':
                # Count interface types
                categories = categorize_interfaces_by_type([l.strip() for l in lines if l.strip() and not l.strip().startswith('!') and l.startswith('  ') and not l.startswith('    ')])
                
                table = Table(title="Interface Summary", box=box.SIMPLE)
                table.add_column("Type", style="cyan")
                table.add_column("Count", justify="right", style="green")
                table.add_column("Examples", style="dim")
                
                for cat, ifaces in categories.items():
                    if ifaces:
                        examples = ", ".join(ifaces[:3])
                        if len(ifaces) > 3:
                            examples += f" (+{len(ifaces) - 3})"
                        table.add_row(cat.replace('_', ' ').title(), str(len(ifaces)), examples)
                
                console.print(table)
                console.print(f"[dim]Total lines: {line_count}[/dim]")
                
            elif hierarchy == 'services':
                # Count service types
                fxc = len(re.findall(r'evpn-vpws-fxc\s+instance', section))
                vpls = len(re.findall(r'evpn-vpls\s+instance', section))
                vrf = len(re.findall(r'^\s{4}vrf\s+', section, re.MULTILINE))
                bridge = len(re.findall(r'bridge-domain\s+', section))
                
                table = Table(title="Services Summary", box=box.SIMPLE)
                table.add_column("Type", style="cyan")
                table.add_column("Count", justify="right", style="green")
                if fxc:
                    table.add_row("EVPN-VPWS-FXC", str(fxc))
                if vpls:
                    table.add_row("EVPN-VPLS", str(vpls))
                if vrf:
                    table.add_row("VRF", str(vrf))
                if bridge:
                    table.add_row("Bridge Domain", str(bridge))
                if not (fxc or vpls or vrf or bridge):
                    table.add_row("(none found)", "-")
                console.print(table)
                console.print(f"[dim]Total lines: {line_count}[/dim]")
                
            elif hierarchy in ['igp', 'bgp']:
                # Show first 15 lines as preview
                console.print(f"[dim]Preview ({line_count} lines total):[/dim]")
                for line in lines[:15]:
                    console.print(f"  [dim]{line}[/dim]")
                if line_count > 15:
                    console.print(f"  [dim]... ({line_count - 15} more lines)[/dim]")
            
            # Option to view full raw text
            if Prompt.ask("\nView full raw config?", choices=["y", "n"], default="n").lower() == "y":
                console.print(Panel(
                    Syntax(section, "text", theme="monokai", line_numbers=True),
                    title=f"[cyan]{hierarchy}[/cyan]",
                    border_style="dim"
                ))
        else:
            console.print(f"[yellow]No {hierarchy} configuration found[/yellow]")
    else:
        # Show menu to select which hierarchy to view
        console.print("\n[bold]View Current Configuration:[/bold]")
        console.print("  [1] System")
        console.print("  [2] Interfaces")
        console.print("  [3] Services")
        console.print("  [4] IGP (ISIS/OSPF)")
        console.print("  [5] BGP")
        console.print("  [A] All (full config summary)")
        console.print("  [B] Back")
        
        choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "5", "a", "A", "b", "B"], default="b").lower()
        
        if choice == "b":
            return
        
        hierarchy_map = {"1": "system", "2": "interfaces", "3": "services", "4": "igp", "5": "bgp"}
        
        if choice == "a":
            # Show all hierarchies summary - import here to avoid circular dependency
            from ..config_parser import ConfigParser
            from .main import show_current_config_summary
            parser = ConfigParser()
            show_current_config_summary(_current_state.current_config, parser)
        elif choice in hierarchy_map:
            view_current_config(hierarchy_map[choice])

