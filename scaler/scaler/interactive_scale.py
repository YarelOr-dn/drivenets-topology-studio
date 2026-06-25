"""Interactive SCALER Configuration Wizard.

A step-by-step wizard for creating scaled DNOS configurations with
validation, diff-style previews, and full commit/verify workflow.
"""

# Suppress the "found in sys.modules after import" warning
import warnings
warnings.filterwarnings("ignore", message=".*found in sys.modules after import.*", category=RuntimeWarning)

import sys
import os
import re
import json
import time
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Set
from datetime import datetime
try:
    from dataclasses import dataclass
except ImportError:
    # Fallback for older Python versions (though we require 3.10+)
    from dataclasses import dataclass
from urllib.parse import quote

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.syntax import Syntax
from rich import box
from rich.text import Text

from .models import (
    Device,
    Platform,
    HierarchyAction,
    NamingPattern,
    NamingFormat,
    VlanType,
    HierarchyConfig,
    InterfaceScaleInput,
    ServiceScaleInput,
    BGPScaleInput,
    BatchScaleConfig,
    WizardState,
    ValidationResult,
    InterfaceScale,
    ServiceScale,
    BGPPeerScale,
    ScaleConfig,
    ServiceType,
    InterfaceType,
)
from .device_manager import DeviceManager
from .config_extractor import ConfigExtractor
from .config_parser import ConfigParser
from .scale_generator import ScaleGenerator
from .validator import Validator
from .config_pusher import ConfigPusher
from .pattern_parser import PatternParser, parse_count_input
from .diff_generator import DiffGenerator
from .verifier import Verifier, VerificationStatus
from .cli_validator import CLIValidator, ValidationSeverity

# Network-mapper integration (optional - used only for adding new devices)
# This is NOT required for normal SCALER operation
try:
    from .network_mapper_client import (
        NetworkMapperClient,
        Topology,
        TopologyDevice,
        get_mapper_client,
        MCP_AVAILABLE,
        MCP_IMPORT_ERROR,
    )
    NETWORK_MAPPER_AVAILABLE = MCP_AVAILABLE
except Exception:
    NETWORK_MAPPER_AVAILABLE = False
    MCP_IMPORT_ERROR = "network_mapper_client import failed"

# ==============================================================================
# RE-EXPORTS FROM WIZARD SUBPACKAGE
# ==============================================================================
# The wizard subpackage contains modular components of this file for easier
# maintenance and debugging. The core functions remain here for backward
# compatibility, but helper functions are organized in the wizard subpackage.
#
# Submodules:
#   - wizard.core: BackException, TopException, StepNavigator, navigation
#   - wizard.ui: Console helpers, prompts, display functions
#   - wizard.parsers: Config parsing (EVPN, MH, RT, VLAN)
#   - wizard.validators: DNOS limits, validation helpers
#   - wizard.interfaces: Interface categorization and helpers
#   - wizard.multihoming: ESI generation and matching
#   - wizard.multi_device: MultiDeviceContext, DeviceSummary
#   - wizard.push: Push and verify functions
#
# Usage:
#   from scaler.wizard import BackException, parse_route_targets
#   # or
#   from scaler.interactive_scale import BackException, parse_route_targets
# ==============================================================================

console = Console()


# ==============================================================================
# NAVIGATION ENHANCEMENTS - Arrow Key Alternative (B for Back)
# ==============================================================================

class NavigablePrompt:
    """Enhanced prompts with consistent [B] Back navigation.
    
    Provides uniform navigation across all prompts in the wizard.
    Arrow keys aren't reliably supported in all terminals, so we use 'B' consistently.
    
    Usage:
        result = NavigablePrompt.ask("Enter value", default="123")
        if result == NavigablePrompt.BACK:
            raise BackException()
    """
    BACK = "__NAVIGATE_BACK__"
    
    @staticmethod
    def ask(
        prompt_text: str,
        default: str = "",
        choices: List[str] = None,
        password: bool = False,
        allow_back: bool = True
    ) -> str:
        """Prompt with [B] Back support for ALL prompts.
        
        Args:
            prompt_text: The prompt message
            default: Default value
            choices: Valid choices (if any)
            password: Hide input
            allow_back: Enable [B] back navigation
        
        Returns:
            User input or NavigablePrompt.BACK
            
        Note: If user needs to enter literal 'b' or 'B', they should use a different value.
              'b' and 'B' are reserved for back navigation.
        """
        # Auto-append [B]ack hint if not already in prompt
        if allow_back and '[B]' not in prompt_text and '[b]' not in prompt_text:
            full_prompt = f"{prompt_text} [dim][[B]ack][/dim]"
        else:
            full_prompt = prompt_text
        
        try:
            if choices:
                # Add 'b' and 'B' to choices if not present
                valid_choices = list(choices)
                if allow_back and 'b' not in [c.lower() for c in valid_choices]:
                    valid_choices.extend(['b', 'B'])
                result = Prompt.ask(full_prompt, choices=valid_choices, default=default)
            else:
                result = Prompt.ask(full_prompt, default=default, password=password)
            
            # Check for back command (works for all prompts)
            if allow_back and result.lower() == 'b':
                return NavigablePrompt.BACK
            
            return result
        except KeyboardInterrupt:
            if allow_back:
                return NavigablePrompt.BACK
            raise
    
    @staticmethod
    def ask_int(
        prompt_text: str,
        default: int = None,
        min_value: int = None,
        max_value: int = None,
        allow_back: bool = True
    ) -> Any:
        """Integer prompt with [B] Back support.
        
        For integer prompts, 'b' is treated as a back command since
        it's not a valid integer anyway.
        
        Returns:
            int value or NavigablePrompt.BACK
        """
        # Auto-append [B]ack hint for integer prompts
        if allow_back:
            if '[B]' not in prompt_text and '[b]' not in prompt_text:
                full_prompt = f"{prompt_text} [dim][[B]ack][/dim]"
            else:
                full_prompt = prompt_text
        else:
            full_prompt = prompt_text
        
        while True:
            result = Prompt.ask(full_prompt, default=str(default) if default is not None else "")
            
            if allow_back and result.lower() == 'b':
                return NavigablePrompt.BACK
            
            try:
                val = int(result)
                if min_value is not None and val < min_value:
                    console.print(f"[red]Value must be >= {min_value}[/red]")
                    continue
                if max_value is not None and val > max_value:
                    console.print(f"[red]Value must be <= {max_value}[/red]")
                    continue
                return val
            except ValueError:
                if allow_back:
                    console.print("[red]Please enter a valid integer or 'b' to go back[/red]")
                else:
                    console.print("[red]Please enter a valid integer[/red]")


# Global state reference for breadcrumb access
_current_state: Optional['WizardState'] = None

# DNOS Platform Limits (loaded from limits.json)
_DNOS_LIMITS = None

def get_dnos_limits() -> Dict[str, Any]:
    """Load DNOS platform limits from limits.json."""
    global _DNOS_LIMITS
    if _DNOS_LIMITS is None:
        limits_path = Path(__file__).parent.parent / "limits.json"
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


def set_wizard_state(state: 'WizardState'):
    """Set the global wizard state for breadcrumb access."""
    global _current_state
    _current_state = state


def sanitize_config_for_version(config_text: str, target_version: str = "",
                                source_version: str = "") -> tuple:
    """Strip config sections known to be incompatible across DNOS major versions.
    
    Data-driven: reads incompatible features from db/dnos_version_compat.json.
    When new incompatibilities are discovered, add them to the JSON knowledge base
    and they are automatically picked up here.
    
    If source_version and target_version are provided, only strips features that
    are in source but not in target. Otherwise strips all known version-specific
    features (safe fallback for unknown version pairs).
    
    Returns: (cleaned_config, list_of_stripped_items)
    """
    try:
        from .version_compat import sanitize_config
        return sanitize_config(config_text, source_version, target_version)
    except Exception:
        pass
    
    # Fallback: hardcoded patterns if version_compat module fails to load.
    # This ensures config restore works even if the JSON DB is missing/corrupt.
    import re
    lines = config_text.split('\n')
    cleaned = []
    stripped = []
    skip_until_depth = -1
    
    SINGLE_LINE_REMOVALS = [
        (r'^\s+suppress-event-list\s', 'logging suppress-event-list'),
        (r'^\s+utc-normalize\s', 'logging utc-normalize'),
        (r'^\s+cli-timestamp\s', 'system cli-timestamp'),
        (r'^\s+timing-mode\s', 'system timing-mode'),
        (r'^\s+profile\s+default\s*$', 'system profile'),
        (r'^\s+bgp\s+nsr\s', 'bgp nsr'),
    ]
    
    BLOCK_REMOVALS = [
        (r'^\s+user\s+dntechsupport\b', 'user dntechsupport (role techsupport)'),
        (r'^\s+ipmi\s*$', 'system login ipmi'),
        (r'^\s+grpc\s*$', 'system grpc'),
        (r'^\s+speed-ranges\s*$', 'qos speed-ranges'),
        (r'^\s+security\s*$', 'ssh security (algorithms)'),
        (r'^\s+timestamp-format\s*$', 'logging timestamp-format'),
    ]
    
    COLLAPSIBLE_PARENTS = {
        'ssh', 'ntp', 'logging', 'syslog', 'hw-mapping', 'queue-size', 'qos',
    }
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped_line = line.rstrip()
        indent = len(line) - len(line.lstrip())
        if skip_until_depth >= 0:
            if stripped_line.strip() == '!' and indent <= skip_until_depth:
                skip_until_depth = -1
            i += 1
            continue
        single_matched = False
        for pattern, desc in SINGLE_LINE_REMOVALS:
            if re.match(pattern, line):
                stripped.append(desc)
                single_matched = True
                break
        if single_matched:
            i += 1
            continue
        block_matched = False
        for pattern, desc in BLOCK_REMOVALS:
            if re.match(pattern, line):
                stripped.append(f"[block] {desc}")
                skip_until_depth = indent
                block_matched = True
                break
        if block_matched:
            i += 1
            continue
        cleaned.append(stripped_line)
        i += 1
    
    changed = True
    while changed:
        changed = False
        result = []
        j = 0
        while j < len(cleaned):
            line = cleaned[j]
            keyword = line.strip()
            if (j + 1 < len(cleaned) and
                keyword in COLLAPSIBLE_PARENTS and
                cleaned[j + 1].strip() == '!'):
                indent_cur = len(line) - len(line.lstrip())
                indent_next = len(cleaned[j + 1]) - len(cleaned[j + 1].lstrip())
                if indent_next == indent_cur:
                    stripped.append(f"[empty] {keyword}")
                    j += 2
                    changed = True
                    continue
            result.append(line)
            j += 1
        cleaned = result
    
    return '\n'.join(cleaned), stripped


def _get_config_history_path(device_name: str) -> Path:
    """Get path to config history JSON file for a device."""
    from .utils import get_device_config_dir
    config_dir = get_device_config_dir(device_name)
    return config_dir / ".config_history.json"


def _save_config_history(device_name: str, filepath: Path, section_actions: Dict[str, str], config_text: str):
    """Save configuration metadata to history for quick-load feature."""
    history_path = _get_config_history_path(device_name)
    
    # Load existing history
    history = []
    if history_path.exists():
        try:
            with open(history_path, 'r') as f:
                history = json.load(f)
        except:
            history = []
    
    # Calculate summary stats
    line_count = len(config_text.split('\n'))
    
    # Create summary of what was configured
    configured_sections = [k for k, v in section_actions.items() if v in ('keep', 'edit')]
    
    # Add new entry
    entry = {
        'filepath': str(filepath),
        'filename': filepath.name,
        'timestamp': datetime.now().isoformat(),
        'sections': configured_sections,
        'line_count': line_count,
        'pushed': False  # Will be updated on successful push
    }
    
    # Add to front of list
    history.insert(0, entry)
    
    # Keep only last 10 entries
    history = history[:10]
    
    # Save
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)


def _mark_config_validated(device_name: str, filepath: Path):
    """Mark a configuration as having passed commit check."""
    history_path = _get_config_history_path(device_name)
    
    if not history_path.exists():
        return
    
    try:
        with open(history_path, 'r') as f:
            history = json.load(f)
        
        for entry in history:
            if entry['filepath'] == str(filepath):
                entry['validated'] = True
                entry['validated_time'] = datetime.now().isoformat()
                break
        
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2)
    except:
        pass


def _mark_config_pushed(device_name: str, filepath: Path):
    """Mark a configuration as successfully committed."""
    history_path = _get_config_history_path(device_name)
    
    if not history_path.exists():
        return
    
    try:
        with open(history_path, 'r') as f:
            history = json.load(f)
        
        for entry in history:
            if entry['filepath'] == str(filepath):
                entry['pushed'] = True
                entry['validated'] = True  # If pushed, it was also validated
                entry['push_time'] = datetime.now().isoformat()
                break
        
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2)
    except:
        pass


def _load_config_history(device_name: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Load recent configuration history for quick-load feature."""
    history_path = _get_config_history_path(device_name)
    
    if not history_path.exists():
        return []
    
    try:
        with open(history_path, 'r') as f:
            history = json.load(f)
        
        # Filter to only include existing files
        valid_entries = []
        for entry in history:
            if Path(entry['filepath']).exists():
                valid_entries.append(entry)
                if len(valid_entries) >= limit:
                    break
        
        return valid_entries
    except:
        return []


# =============================================================================
# MULTI-DEVICE HELPER FUNCTIONS
# =============================================================================

def _show_multi_device_action_menu(multi_ctx: 'MultiDeviceContext', primary_device) -> str:
    """
    Show enhanced multi-device action menu with split view of both devices.
    
    Args:
        multi_ctx: MultiDeviceContext with selected devices
        primary_device: Primary device for reference
    
    Returns:
        Action string: 'configure', 'delete', 'modify_interfaces', 'compare',
                       'sync_status', 'push', 'refresh', 'exit'
    """
    from rich.columns import Columns
    from rich.panel import Panel
    
    console.print(f"\n[bold cyan]{'═' * 80}[/bold cyan]")
    console.print(f"[bold cyan]Multi-Device Actions[/bold cyan]")
    console.print(f"[bold cyan]{'═' * 80}[/bold cyan]")
    
    # Detect device states for all devices
    device_states = {}  # hostname -> {'state': str, 'is_gi': bool, 'is_recovery': bool}
    any_in_gi = False
    any_in_recovery = False
    all_in_limited_mode = True  # True if ALL devices are in GI/recovery
    
    for dev in multi_ctx.devices:
        h = dev.hostname
        state_info = {'state': 'DNOS', 'is_gi': False, 'is_recovery': False, 'display': ''}
        try:
            op_file = Path(f"/home/dn/SCALER/db/configs/{h}/operational.json")
            if op_file.exists():
                with open(op_file) as f:
                    op_data = json.load(f)
                    device_state = op_data.get('device_state', 'DNOS')
                    dnos_version = op_data.get('dnos_version', '')
                    recovery_type = op_data.get('recovery_type', '')
                    
                    # Auto-detect stale state: if system delete was initiated
                    # after the last state check, device is in GI (not DNOS)
                    delete_ts = op_data.get('delete_initiated', '')
                    last_verified = op_data.get('last_verified', '')
                    if (device_state == 'DNOS' and delete_ts
                            and delete_ts > last_verified):
                        device_state = 'GI'
                        op_data['device_state'] = 'GI'
                        op_data['recovery_mode_detected'] = True
                        op_data['recovery_type'] = 'GI'
                        try:
                            with open(op_file, 'w') as fw:
                                json.dump(op_data, fw, indent=4)
                        except IOError:
                            pass
                    
                    if device_state == 'GI' or recovery_type == 'GI':
                        state_info = {'state': 'GI', 'is_gi': True, 'is_recovery': False, 'display': '[cyan]GI[/cyan]'}
                        any_in_gi = True
                    elif device_state in ('BASEOS_SHELL', 'ONIE', 'DN_RECOVERY', 'RECOVERY') or recovery_type in ('BASEOS_SHELL', 'ONIE', 'DN_RECOVERY'):
                        state_info = {'state': device_state or recovery_type, 'is_gi': False, 'is_recovery': True, 'display': f'[red]{device_state or recovery_type}[/red]'}
                        any_in_recovery = True
                    elif device_state == 'DEPLOYING':
                        state_info = {'state': 'DEPLOYING', 'is_gi': True, 'is_recovery': False, 'display': '[cyan]DEPLOYING[/cyan]'}
                        any_in_gi = True
                    elif device_state == 'UPGRADING':
                        state_info = {'state': 'UPGRADING', 'is_gi': False, 'is_recovery': False, 'display': '[yellow]UPGRADING[/yellow]'}
                        all_in_limited_mode = False
                    elif dnos_version in ('N/A', '', None) or 'N/A' in str(dnos_version):
                        state_info = {'state': 'GI?', 'is_gi': True, 'is_recovery': False, 'display': '[cyan]GI?[/cyan]'}
                        any_in_gi = True
                    else:
                        all_in_limited_mode = False
        except:
            all_in_limited_mode = False  # Assume DNOS if can't read
        
        device_states[h] = state_info
    
    # Build side-by-side device panels
    panels = []
    for dev in multi_ctx.devices:
        h = dev.hostname
        lo = multi_ctx.loopbacks.get(h, "N/A")
        asn = multi_ctx.bgp_asn.get(h, 0)
        rt_count = len(multi_ctx.route_targets.get(h, set()))
        mh_count = len(multi_ctx.mh_config.get(h, {}))
        iface_count = len(multi_ctx.interfaces.get(h, []))
        summary = multi_ctx.summaries.get(h)
        
        lines = []
        
        # Device state (if not DNOS)
        state_info = device_states.get(h, {})
        if state_info.get('display'):
            lines.append(f"[bold]State:[/bold] {state_info['display']}")
        
        # Loopback & ASN
        lines.append(f"[cyan]Loopback:[/cyan] {lo}")
        lines.append(f"[cyan]BGP AS:[/cyan] {asn}")
        
        # Services summary
        if summary and summary.services:
            svc_parts = []
            for svc_type, (up, total, _) in summary.services.items():
                if up == total:
                    svc_parts.append(f"[green]{svc_type}: {up}/{total}[/green]")
                elif up > 0:
                    svc_parts.append(f"[yellow]{svc_type}: {up}/{total}[/yellow]")
                else:
                    svc_parts.append(f"[red]{svc_type}: {up}/{total}[/red]")
            if svc_parts:
                lines.append(f"[cyan]Services:[/cyan] " + ", ".join(svc_parts[:2]))
                if len(svc_parts) > 2:
                    lines.append(f"          " + ", ".join(svc_parts[2:]))
        
        # Counts
        lines.append(f"[cyan]RTs:[/cyan] {rt_count:,}")
        lines.append(f"[cyan]Interfaces:[/cyan] {iface_count:,}")
        
        # MH status
        if mh_count > 0:
            lines.append(f"[green]Multihoming:[/green] {mh_count:,} ESIs")
        else:
            lines.append(f"[dim]Multihoming:[/dim] Not configured")
        
        # Uptime if available
        if summary and summary.uptime:
            lines.append(f"[dim]Uptime: {summary.uptime}[/dim]")
        
        # Determine panel color
        if mh_count > 0 and rt_count > 0:
            border_style = "green"
        elif rt_count > 0:
            border_style = "cyan"
        else:
            border_style = "yellow"
        
        panel = Panel(
            "\n".join(lines),
            title=f"[bold white]{h}[/bold white]",
            subtitle=f"[dim]{dev.ip}[/dim]",
            border_style=border_style,
            expand=True,
            padding=(0, 1)
        )
        panels.append(panel)
    
    # Show devices side-by-side
    console.print(Columns(panels, expand=True, equal=True))
    
    # Show sync status
    shared_pairs = multi_ctx.get_shared_evpn_peers()
    if shared_pairs:
        console.print(f"\n[bold cyan]🔗 Sync Status:[/bold cyan]")
        for h1, h2, shared_rt in shared_pairs:
            mh1 = len(multi_ctx.mh_config.get(h1, {}))
            mh2 = len(multi_ctx.mh_config.get(h2, {}))
            if mh1 > 0 and mh2 > 0 and mh1 == mh2:
                sync_icon = "[green]✓ Synced[/green]"
            elif mh1 > 0 and mh2 > 0:
                sync_icon = f"[yellow]⚠ MH: {mh1} vs {mh2}[/yellow]"
            elif mh1 > 0 or mh2 > 0:
                sync_icon = "[yellow]⚠ MH mismatch[/yellow]"
            else:
                sync_icon = "[dim]○ No MH[/dim]"
            console.print(f"  {h1} ↔ {h2}: [cyan]{shared_rt:,} shared RTs[/cyan] • {sync_icon}")
    
    console.print()
    
    # Check if there are any config files to push
    has_push_files = False
    for dev in multi_ctx.devices:
        dev_history = _load_config_history(dev.hostname, limit=1)
        if dev_history:
            has_push_files = True
            break
    
    # Show warning if any devices are in limited mode
    if any_in_gi or any_in_recovery:
        gi_devs = [h for h, s in device_states.items() if s.get('is_gi')]
        rec_devs = [h for h, s in device_states.items() if s.get('is_recovery')]
        if gi_devs:
            console.print(f"[cyan]⚙ Devices in GI mode:[/cyan] {', '.join(gi_devs)}")
        if rec_devs:
            console.print(f"[red]⚠ Devices in recovery:[/red] {', '.join(rec_devs)}")
        if all_in_limited_mode:
            console.print("[dim]Most options disabled - use Image Upgrade or System Restore[/dim]")
        console.print()
    
    # Action menu - Status/View operations first, then config actions
    console.print("[bold]Status & View:[/bold]")
    if all_in_limited_mode:
        console.print("  [dim][1] Compare Configurations - Show detailed diff (N/A)[/dim]")
        console.print("  [dim][2] Sync Status - Detailed synchronization analysis (N/A)[/dim]")
        console.print("  [dim][3] Push Files - Push saved config files to all devices (N/A)[/dim]")
        console.print("  [dim][4] Stag Pool Check - Live QinQ Stag usage (N/A)[/dim]")
    else:
        console.print("  [1] Compare Configurations - Show detailed diff")
        console.print("  [2] Sync Status - Detailed synchronization analysis")
        if has_push_files:
            console.print("  [3] Push Files - Push saved config files to all devices")
        else:
            console.print("  [dim][3] Push Files - No saved configs available[/dim]")
        console.print("  [4] [cyan]Stag Pool Check[/cyan] - Live QinQ Stag usage from Linux shell")
    console.print("  [R] Refresh - Reload configs from all devices / Verify states")
    console.print("  [I] [cyan]Change IP[/cyan] - Update management IP for a device")
    console.print()
    
    console.print("[bold]Configuration Actions:[/bold]")
    if all_in_limited_mode:
        console.print("  [dim][5] Configure - Full configuration wizard (N/A)[/dim]")
        console.print("  [dim][6] Delete Hierarchy - Delete config sections (N/A)[/dim]")
        console.print("  [dim][7] Modify Service Interfaces - Add/remove/remap interfaces (N/A)[/dim]")
    else:
        console.print("  [5] [green]Configure[/green] - Full configuration wizard (select device)")
        console.print("  [6] [red]Delete Hierarchy[/red] - Delete config sections from all devices")
        console.print("  [7] [yellow]Modify Service Interfaces[/yellow] - Add/remove/remap interfaces at scale")
    
    # Image Upgrade always available
    console.print("  [8] [magenta]Image Upgrade[/magenta] - Upgrade DNOS/GI/BaseOS + Deploy")
    
    if all_in_limited_mode:
        console.print("  [dim][9] Scale Up/Down - Bulk add/delete services (N/A)[/dim]")
        console.print("  [dim][M] 🪞 Mirror Config - Copy config from another PE (N/A)[/dim]")
        console.print("  [dim][W] 🛡️ Flowspec Sync - Configure BGP Flowspec (N/A)[/dim]")
        console.print("  [dim][F] 🔄 Factory Reset - Load override factory-default (N/A)[/dim]")
    else:
        console.print("  [9] [bold orange3]Scale Up/Down[/bold orange3] - Bulk add/delete services with correlated interfaces")
        console.print("  [M] [bold bright_magenta]🪞 Mirror Config[/bold bright_magenta] - Copy config from another PE")
        console.print("  [W] [bold magenta]🛡️ Flowspec Sync[/bold magenta] - Configure BGP Flowspec (DDoS protection)")
        console.print("  [F] [bold red]🔄 Factory Reset[/bold red] - Load override factory-default on ALL devices")
    
    # System Restore always available
    console.print("  [S] [bold red]🔧 System Restore[/bold red] - Recover device(s) from RECOVERY mode")
    if NETWORK_MAPPER_AVAILABLE:
        console.print("  [N] [magenta]📡 Sync from Network-Mapper[/magenta] - Pull configs without SSH")
    console.print("  [B] Back to device selection")
    
    # Build valid choices based on mode
    if all_in_limited_mode:
        # Limited mode: only 8 (Image Upgrade), S (System Restore), R (Refresh), I (Change IP), B (Back)
        valid_choices = ["8", "s", "S", "r", "R", "i", "I", "b", "B"]
        if NETWORK_MAPPER_AVAILABLE:
            valid_choices.extend(["n", "N"])
    else:
        valid_choices = ["1", "2", "4", "5", "6", "7", "8", "9", "m", "M", "w", "W", "f", "F", "s", "S", "r", "R", "i", "I", "b", "B"]
        if has_push_files:
            valid_choices.append("3")
        if NETWORK_MAPPER_AVAILABLE:
            valid_choices.extend(["n", "N"])
    
    choice = Prompt.ask(
        "Select action",
        choices=valid_choices,
        default="1"
    ).lower()
    
    action_map = {
        "1": "compare",
        "2": "sync_status",
        "3": "push",
        "4": "stag_check",
        "5": "configure",
        "6": "delete",
        "7": "modify_interfaces",
        "8": "image_upgrade",
        "9": "scale_updown",
        "m": "mirror_config",
        "w": "flowspec_sync",
        "f": "factory_reset",
        "s": "system_restore",
        "n": "sync_mapper",
        "r": "refresh",
        "i": "change_ip",
        "b": "exit",
    }
    
    return action_map.get(choice, "configure")


def _show_flowspec_menu_multi_device(multi_ctx: 'MultiDeviceContext') -> None:
    """Show enhanced FlowSpec menu for multi-device mode.
    
    Options:
    1. Local Policies (IPv4)
    2. Local Policies (IPv6)
    3. Local Policies (Dual-Stack)
    4. BGP FlowSpec AFI/SAFI
    5. VRF FlowSpec AFI
    6. Interface FlowSpec
    7. Sync FlowSpec across devices
    8. Dependency Check (all devices)
    """
    set_path(["Multi-Device", "FlowSpec Menu"])
    show_breadcrumb()
    
    while True:
        console.print("\n[bold magenta]━━━ FlowSpec Configuration Menu ━━━[/bold magenta]")
        
        # Quick dependency check across all devices for inline status
        total_critical = 0
        total_warning = 0
        device_issues = {}
        
        for dev in multi_ctx.devices:
            temp_state = WizardState()
            temp_state.current_config = multi_ctx.configs.get(dev.hostname, "")
            issues = check_flowspec_dependencies(temp_state)
            device_issues[dev.hostname] = issues
            total_critical += sum(1 for i in issues if i.severity == "critical")
            total_warning += sum(1 for i in issues if i.severity == "warning")
        
        # Show status inline
        if total_critical == 0 and total_warning == 0:
            console.print(f"[green]✓ All {len(multi_ctx.devices)} devices: dependencies satisfied[/green]")
        else:
            status_parts = []
            if total_critical:
                status_parts.append(f"[red]{total_critical} critical[/red]")
            if total_warning:
                status_parts.append(f"[yellow]{total_warning} warnings[/yellow]")
            console.print(f"⚠ Across {len(multi_ctx.devices)} devices: {', '.join(status_parts)}")
            
            # Show which devices have issues
            for hostname, issues in device_issues.items():
                if issues:
                    crit = sum(1 for i in issues if i.severity == "critical")
                    warn = sum(1 for i in issues if i.severity == "warning")
                    if crit:
                        console.print(f"  [red]✗ {hostname}:[/red] {crit} critical, {warn} warnings")
                    else:
                        console.print(f"  [yellow]⚠ {hostname}:[/yellow] {warn} warnings")
        
        console.print()
        console.print("[bold]Configuration Options:[/bold]")
        console.print("  [1] [red]Local Policies[/red] - Define static protection rules (IPv4/IPv6)")
        console.print("  [2] [cyan]BGP FlowSpec AFI[/cyan] - Configure SAFI 133/134 on neighbors")
        console.print("  [3] [yellow]Interface FlowSpec[/yellow] - Enable on WAN interfaces")
        console.print("  [4] [green]VRF FlowSpec AFI[/green] - Configure FlowSpec in VRFs (for FS-VPN)")
        console.print("")
        console.print("[bold]Sync & Analysis:[/bold]")
        console.print("  [5] [green]Sync FlowSpec[/green] - Replicate config across devices")
        console.print("  [D] [blue]Dependency Check[/blue] - Full report with fix commands")
        console.print("  [A] [magenta]FSVPN Wizard[/magenta] - Launch FlowSpec VPN diagnostic tool")
        console.print("")
        console.print("  [V] View FlowSpec config")
        console.print("  [B] Back")
        
        choice = Prompt.ask("Select", choices=[
            "1", "2", "3", "4", "5", "d", "D", "a", "A", "v", "V", "b", "B"
        ], default="d").lower()
        
        if choice == "b":
            return
        
        # For configuration options, we need a device state
        # Use first device's state or create a temporary one
        temp_state = WizardState()
        if multi_ctx.devices:
            first_dev = multi_ctx.devices[0]
            temp_state.current_config = multi_ctx.configs.get(first_dev.hostname, "")
            temp_state.hostname = first_dev.hostname
        
        try:
            if choice == "1":
                # Local Policies (IPv4/IPv6 selection is inside the function)
                result = configure_flowspec_policies(temp_state, {}, multi_ctx)
                if result:
                    _push_flowspec_result(multi_ctx, result.new_config, "Local Policies")
            
            elif choice == "2":
                # BGP FlowSpec AFI/SAFI
                result = configure_bgp_flowspec_afi(temp_state, {}, multi_ctx)
                if result:
                    _push_flowspec_result(multi_ctx, result.new_config, "BGP FlowSpec AFI/SAFI")
            
            elif choice == "3":
                # Interface FlowSpec
                flowspec_configs = sync_flowspec_across_devices(multi_ctx)
                if flowspec_configs:
                    _push_flowspec_result_multi(multi_ctx, flowspec_configs, "Interface FlowSpec")
            
            elif choice == "4":
                # VRF FlowSpec AFI Configuration
                console.print("\n[bold green]━━━ VRF FlowSpec Configuration (Multi-Device) ━━━[/bold green]")
                console.print("[dim]Configure ipv4/ipv6-flowspec inside VRFs for FlowSpec-VPN import[/dim]\n")
                
                # Collect VRF configs across all devices
                all_vrfs = set()
                for dev in multi_ctx.devices:
                    config = multi_ctx.configs.get(dev.hostname, "")
                    vrf_instances = re.findall(r'instance\s+(\S+)', config)
                    user_vrfs = [v for v in vrf_instances if v not in ['management', 'default', '__base__', 'P']]
                    all_vrfs.update(user_vrfs)
                
                if not all_vrfs:
                    console.print("[yellow]No user VRFs found across devices[/yellow]")
                    continue
                
                console.print(f"[cyan]Found {len(all_vrfs)} unique VRFs across {len(multi_ctx.devices)} devices[/cyan]")
                console.print(f"  [dim]{', '.join(list(all_vrfs)[:5])}{'...' if len(all_vrfs) > 5 else ''}[/dim]")
                
                # Get BGP ASN
                asn_match = re.search(r'protocols\s+bgp\s+(\d+)', temp_state.current_config or "")
                bgp_asn = asn_match.group(1) if asn_match else "65000"
                
                # Get RT
                console.print(f"\n[dim]Route-Target for FlowSpec-VPN import/export[/dim]")
                rt_suggestion = f"{bgp_asn}:100"
                rt_value = Prompt.ask("Route-Target", default=rt_suggestion)
                
                # Generate config for each device (only VRFs that exist on that device)
                flowspec_configs = {}
                for dev in multi_ctx.devices:
                    config = multi_ctx.configs.get(dev.hostname, "")
                    vrf_instances = re.findall(r'instance\s+(\S+)', config)
                    user_vrfs = [v for v in vrf_instances if v not in ['management', 'default', '__base__', 'P']]
                    
                    # Check which VRFs need FlowSpec
                    vrfs_needing_fs = []
                    for vrf in user_vrfs:
                        vrf_pattern = rf'instance\s+{re.escape(vrf)}.*?(?=instance\s+\S+|$)'
                        vrf_config = re.search(vrf_pattern, config, re.DOTALL)
                        if vrf_config and 'ipv4-flowspec' not in vrf_config.group():
                            vrfs_needing_fs.append(vrf)
                    
                    if vrfs_needing_fs:
                        config_lines = ["network-services", "  vrf"]
                        for vrf in vrfs_needing_fs:
                            config_lines.extend([
                                f"    instance {vrf}",
                                "      protocols",
                                f"        bgp {bgp_asn}",
                                "          address-family ipv4-flowspec",
                                f"            export-vpn route-target {rt_value}",
                                f"            import-vpn route-target {rt_value}",
                                "          !",
                                "          address-family ipv6-flowspec",
                                f"            export-vpn route-target {rt_value}",
                                f"            import-vpn route-target {rt_value}",
                                "          !",
                                "        !",
                                "      !",
                                "    !",
                            ])
                        config_lines.extend(["  !", "!"])
                        flowspec_configs[dev.hostname] = '\n'.join(config_lines)
                
                if flowspec_configs:
                    console.print(f"\n[green]Generated VRF FlowSpec config for {len(flowspec_configs)} device(s)[/green]")
                    _push_flowspec_result_multi(multi_ctx, flowspec_configs, "VRF FlowSpec")
                else:
                    console.print("[green]✓ All VRFs already have FlowSpec configured[/green]")
            
            elif choice == "5":
                # Full sync
                flowspec_configs = sync_flowspec_across_devices(multi_ctx)
                if flowspec_configs:
                    _push_flowspec_result_multi(multi_ctx, flowspec_configs, "FlowSpec Sync")
            
            elif choice == "a":
                # Launch FSVPN Wizard
                console.print("\n[bold magenta]━━━ FSVPN Wizard (FlowSpec VPN Diagnostic Tool) ━━━[/bold magenta]")
                console.print("[dim]Comprehensive analysis: BGP sessions, VRF import, TCAM/datapath, local policies[/dim]\n")
                
                fsvpn_path = Path("/home/dn/SCALER/FLOWSPEC_VPN/fsvpn_wizard.py")
                if not fsvpn_path.exists():
                    console.print("[red]FSVPN Wizard not found at expected path[/red]")
                    continue
                
                console.print("[bold]Options:[/bold]")
                console.print("  [1] Launch interactive wizard (new session)")
                console.print("  [2] Quick multi-device analysis")
                console.print("  [B] Back")
                
                fsvpn_choice = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="1").lower()
                
                if fsvpn_choice == "b":
                    continue
                elif fsvpn_choice == "1":
                    import subprocess
                    console.print("[cyan]Launching FSVPN Wizard in new terminal...[/cyan]")
                    try:
                        subprocess.Popen(
                            ["tmux", "new-window", "-n", "fsvpn", f"python3 {fsvpn_path}"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        console.print("[green]✓ FSVPN Wizard launched in tmux window 'fsvpn'[/green]")
                    except Exception as e:
                        console.print(f"[yellow]Could not launch in tmux: {e}[/yellow]")
                        console.print(f"[dim]Run manually: python3 {fsvpn_path}[/dim]")
                elif fsvpn_choice == "2":
                    console.print(f"\n[cyan]Analyzing FlowSpec on {len(multi_ctx.devices)} devices...[/cyan]")
                    for dev in multi_ctx.devices:
                        config = multi_ctx.configs.get(dev.hostname, "")
                        fs_count = config.count('flowspec enabled')
                        bgp_fs = 'ipv4-flowspec' in config or 'ipv6-flowspec' in config
                        console.print(f"  {dev.hostname}: [cyan]{fs_count} interfaces[/cyan], BGP FS: {'[green]✓[/green]' if bgp_fs else '[red]✗[/red]'}")
            
            elif choice == "d":
                # Dependency check on all devices
                console.print("\n[bold cyan]━━━ Per-Device Dependency Check ━━━[/bold cyan]")
                
                all_issues = []
                for dev in multi_ctx.devices:
                    h = dev.hostname
                    config = multi_ctx.configs.get(h, "")
                    
                    dev_state = WizardState()
                    dev_state.current_config = config
                    dev_state.hostname = h
                    
                    issues = check_flowspec_dependencies(dev_state, config)
                    all_issues.append((h, issues))
                
                # Display results
                console.print()
                for h, issues in all_issues:
                    if not issues:
                        console.print(f"[green]✓ {h}:[/green] All dependencies satisfied")
                    else:
                        critical = sum(1 for i in issues if i.severity == "critical")
                        warning = sum(1 for i in issues if i.severity == "warning")
                        color = "red" if critical > 0 else "yellow"
                        console.print(f"[{color}]✗ {h}:[/{color}] {critical} critical, {warning} warning")
                        for issue in issues[:3]:  # Show first 3 issues
                            severity_color = {"critical": "red", "warning": "yellow"}.get(issue.severity, "white")
                            console.print(f"    [{severity_color}]•[/{severity_color}] {issue.issue[:60]}")
                
                # Summary
                total_critical = sum(sum(1 for i in issues if i.severity == "critical") for _, issues in all_issues)
                total_warning = sum(sum(1 for i in issues if i.severity == "warning") for _, issues in all_issues)
                
                console.print(Panel(
                    f"""[bold]Multi-Device Summary:[/bold]
  Devices checked: {len(multi_ctx.devices)}
  [red]Critical issues:[/red] {total_critical}
  [yellow]Warnings:[/yellow] {total_warning}""",
                    title="[bold]Dependency Check Complete[/bold]",
                    border_style="cyan"
                ))
            
            elif choice == "v":
                # View FlowSpec config on all devices
                console.print("\n[bold cyan]━━━ FlowSpec Config per Device ━━━[/bold cyan]")
                for dev in multi_ctx.devices:
                    h = dev.hostname
                    config = multi_ctx.configs.get(h, "")
                    
                    fs_section = _extract_flowspec_section(config) if config else None
                    
                    console.print(f"\n[bold magenta]{h}:[/bold magenta]")
                    if fs_section:
                        syntax = Syntax(fs_section[:2000], "bash", theme="monokai")
                        console.print(syntax)
                    else:
                        console.print("[dim]No FlowSpec configuration found[/dim]")
        
        except BackException:
            continue
        except TopException:
            return


def _push_flowspec_result(multi_ctx: 'MultiDeviceContext', config: str, description: str) -> None:
    """Push FlowSpec config result to all devices.
    
    Args:
        multi_ctx: Multi-device context
        config: Configuration to push
        description: Description for logging
    """
    console.print(f"\n[green]Generated {description} configuration[/green]")
    
    # Create config dict for all devices
    device_configs = {dev.hostname: config for dev in multi_ctx.devices}
    
    if Confirm.ask("Push to all devices?", default=True):
        from .wizard.push import push_and_verify_multi
        success, results = push_and_verify_multi(
            multi_ctx,
            device_configs,
            dry_run=False,
            use_terminal_paste=False,
            use_merge=True  # Merge to preserve existing config
        )
        if success:
            console.print(f"[bold green]✓ {description} pushed successfully![/bold green]")
            _refresh_multi_device_configs(multi_ctx)


def _push_flowspec_result_multi(multi_ctx: 'MultiDeviceContext', device_configs: Dict[str, str], description: str) -> None:
    """Push per-device FlowSpec configs.
    
    Args:
        multi_ctx: Multi-device context
        device_configs: Dict mapping hostname to config
        description: Description for logging
    """
    console.print(f"\n[green]Generated {description} for {len(device_configs)} device(s)[/green]")
    
    if Confirm.ask("Push to devices?", default=True):
        from .wizard.push import push_and_verify_multi
        success, results = push_and_verify_multi(
            multi_ctx,
            device_configs,
            dry_run=False,
            use_terminal_paste=False,
            use_merge=True
        )
        if success:
            console.print(f"[bold green]✓ {description} pushed successfully![/bold green]")
            _refresh_multi_device_configs(multi_ctx)


def _show_flowspec_menu_single_device(device: 'DNDevice', running_config: str, single_ctx: 'MultiDeviceContext') -> None:
    """Show enhanced FlowSpec menu for single-device mode.
    
    Args:
        device: Target device
        running_config: Device's current running configuration
        single_ctx: Single device context (wrapped as MultiDeviceContext)
    """
    set_path(["Single-Device", "FlowSpec Menu"])
    show_breadcrumb()
    
    while True:
        console.print("\n[bold magenta]━━━ FlowSpec Configuration Menu ━━━[/bold magenta]")
        
        # Quick dependency check for inline status
        try:
            _tmp_plat = Platform(device.platform)
        except (ValueError, KeyError):
            _tmp_plat = Platform.NCP
        temp_state = WizardState(
            device=device,
            platform=_tmp_plat,
            current_config=running_config
        )
        issues = check_flowspec_dependencies(temp_state)
        critical_count = sum(1 for i in issues if i.severity == "critical")
        warning_count = sum(1 for i in issues if i.severity == "warning")
        
        # Show status inline
        if not issues:
            console.print("[green]✓ All dependencies satisfied[/green]")
        else:
            status_parts = []
            if critical_count:
                status_parts.append(f"[red]{critical_count} critical[/red]")
            if warning_count:
                status_parts.append(f"[yellow]{warning_count} warnings[/yellow]")
            console.print(f"⚠ Dependencies: {', '.join(status_parts)}")
            
            # Show top 2 issues inline
            for issue in issues[:2]:
                sev_icon = "🔴" if issue.severity == "critical" else "🟡"
                console.print(f"  {sev_icon} {issue.component}: [dim]{issue.issue[:55]}...[/dim]" if len(issue.issue) > 55 else f"  {sev_icon} {issue.component}: [dim]{issue.issue}[/dim]")
            if len(issues) > 2:
                console.print(f"  [dim]... and {len(issues) - 2} more (press D for details)[/dim]")
        
        console.print()
        console.print("[bold]Configuration Options:[/bold]")
        console.print("  [1] [red]Local Policies[/red] - Define static protection rules (IPv4/IPv6)")
        console.print("  [2] [cyan]BGP FlowSpec AFI[/cyan] - Configure SAFI 133/134 on neighbors")
        console.print("  [3] [yellow]Interface FlowSpec[/yellow] - Enable on WAN interfaces")
        console.print("  [4] [green]VRF FlowSpec AFI[/green] - Configure FlowSpec in VRFs (for FS-VPN)")
        console.print("")
        console.print("[bold]Analysis & Monitoring:[/bold]")
        console.print("  [D] [blue]Dependency Check[/blue] - Full dependency report with fix commands")
        console.print("  [A] [magenta]FSVPN Wizard[/magenta] - Launch FlowSpec VPN diagnostic tool")
        console.print("")
        console.print("  [V] View FlowSpec config")
        console.print("  [B] Back")
        
        choice = Prompt.ask("Select", choices=[
            "1", "2", "3", "4", "d", "D", "v", "V", "a", "A", "b", "B"
        ], default="d").lower()
        
        if choice == "b":
            return
        
        # Create a temporary state for this device (reuse from inline check)
        temp_state.hostname = device.hostname
        
        try:
            if choice == "1":
                # Local Policies (includes IPv4/IPv6 selection)
                result = configure_flowspec_policies(temp_state, get_dnos_limits(), single_ctx)
                if result and result.new_config:
                    console.print("\n[bold]Push Flowspec Configuration?[/bold]")
                    if Confirm.ask("Proceed?", default=True):
                        from .wizard.push import push_and_verify
                        success, message = push_and_verify(
                            device, 
                            result.new_config,
                            dry_run=False,
                            use_terminal_paste=False,
                            use_merge=True
                        )
                        if success:
                            console.print("[bold green]✓ FlowSpec local policies applied![/bold green]")
                            single_ctx.discover_all()
            
            elif choice == "2":
                # BGP FlowSpec AFI/SAFI
                result = configure_bgp_flowspec_afi(temp_state, get_dnos_limits(), single_ctx)
                if result and result.new_config:
                    console.print("\n[bold]Push BGP FlowSpec AFI Configuration?[/bold]")
                    if Confirm.ask("Proceed?", default=True):
                        from .wizard.push import push_and_verify
                        success, message = push_and_verify(
                            device, 
                            result.new_config,
                            dry_run=False,
                            use_terminal_paste=False,
                            use_merge=True
                        )
                        if success:
                            console.print("[bold green]✓ BGP FlowSpec AFI/SAFI applied![/bold green]")
                            single_ctx.discover_all()
            
            elif choice == "3":
                # Interface FlowSpec
                console.print("\n[bold yellow]━━━ Interface FlowSpec Configuration ━━━[/bold yellow]")
                
                # Get current flowspec interfaces
                current_fs = get_flowspec_enabled_interfaces(running_config) if running_config else []
                wan_interfaces = get_mpls_enabled_interfaces(running_config, include_subinterfaces=False) if running_config else []
                
                console.print(f"[cyan]FlowSpec-enabled:[/cyan] {len(current_fs)}")
                console.print(f"[cyan]WAN interfaces:[/cyan] {len(wan_interfaces)}")
                
                # Find interfaces without FlowSpec
                interfaces_needing_fs = [i for i in wan_interfaces if i not in current_fs]
                
                if not interfaces_needing_fs:
                    console.print("[green]✓ All WAN interfaces already have FlowSpec enabled[/green]")
                    continue
                
                console.print(f"\n[yellow]Found {len(interfaces_needing_fs)} WAN interfaces without FlowSpec[/yellow]")
                
                if Confirm.ask(f"Enable FlowSpec on these {len(interfaces_needing_fs)} interfaces?", default=True):
                    config_lines = ["interfaces"]
                    for iface in interfaces_needing_fs:
                        config_lines.append(f"  {iface}")
                        config_lines.append("    flowspec enabled")
                        config_lines.append("  !")
                    config_lines.append("!")
                    
                    interface_config = '\n'.join(config_lines)
                    
                    # Show preview
                    syntax = Syntax(interface_config, "bash", theme="monokai")
                    console.print(Panel(syntax, title="Interface FlowSpec Config", border_style="yellow"))
                    
                    if Confirm.ask("Push this configuration?", default=True):
                        from .wizard.push import push_and_verify
                        success, message = push_and_verify(
                            device, 
                            interface_config,
                            dry_run=False,
                            use_terminal_paste=False,
                            use_merge=True
                        )
                        if success:
                            console.print(f"[bold green]✓ FlowSpec enabled on {len(interfaces_needing_fs)} interfaces![/bold green]")
                            single_ctx.discover_all()
                            # Refresh config
                            running_config = single_ctx.configs.get(device.hostname, "")
                            temp_state.current_config = running_config
            
            elif choice == "4":
                # VRF FlowSpec AFI Configuration
                console.print("\n[bold green]━━━ VRF FlowSpec Configuration ━━━[/bold green]")
                console.print("[dim]Configure ipv4/ipv6-flowspec address-family inside VRFs for FlowSpec-VPN import[/dim]\n")
                
                # Find VRFs
                vrf_instances = re.findall(r'instance\s+(\S+)', running_config) if running_config else []
                # Filter out system VRFs
                user_vrfs = [v for v in vrf_instances if v not in ['management', 'default', '__base__', 'P']]
                
                if not user_vrfs:
                    console.print("[yellow]No user VRFs found in configuration[/yellow]")
                    console.print("[dim]VRF FlowSpec is for importing FlowSpec-VPN routes into specific VRFs[/dim]")
                    continue
                
                # Check which VRFs already have FlowSpec
                vrfs_with_fs = []
                vrfs_without_fs = []
                for vrf in user_vrfs:
                    vrf_pattern = rf'instance\s+{re.escape(vrf)}.*?(?=instance\s+\S+|$)'
                    vrf_config = re.search(vrf_pattern, running_config, re.DOTALL)
                    if vrf_config and 'ipv4-flowspec' in vrf_config.group():
                        vrfs_with_fs.append(vrf)
                    else:
                        vrfs_without_fs.append(vrf)
                
                console.print(f"[green]VRFs with FlowSpec:[/green] {len(vrfs_with_fs)}")
                if vrfs_with_fs:
                    console.print(f"  [dim]{', '.join(vrfs_with_fs[:5])}{'...' if len(vrfs_with_fs) > 5 else ''}[/dim]")
                
                console.print(f"[yellow]VRFs without FlowSpec:[/yellow] {len(vrfs_without_fs)}")
                if vrfs_without_fs:
                    console.print(f"  [dim]{', '.join(vrfs_without_fs[:5])}{'...' if len(vrfs_without_fs) > 5 else ''}[/dim]")
                
                if not vrfs_without_fs:
                    console.print("\n[green]✓ All VRFs already have FlowSpec configured[/green]")
                    continue
                
                # Ask which VRFs to configure
                console.print("\n[bold]Select VRFs to configure:[/bold]")
                console.print(f"  [A] All {len(vrfs_without_fs)} VRFs without FlowSpec")
                console.print("  [S] Select specific VRFs")
                console.print("  [B] Back")
                
                vrf_choice = Prompt.ask("Select", choices=["a", "A", "s", "S", "b", "B"], default="a").lower()
                
                if vrf_choice == "b":
                    continue
                
                if vrf_choice == "a":
                    selected_vrfs = vrfs_without_fs
                else:
                    # Show list and let user select
                    for i, vrf in enumerate(vrfs_without_fs, 1):
                        console.print(f"  [{i}] {vrf}")
                    selection = Prompt.ask("Enter VRF numbers (comma-separated)", default="1")
                    try:
                        indices = [int(x.strip()) - 1 for x in selection.split(",")]
                        selected_vrfs = [vrfs_without_fs[i] for i in indices if 0 <= i < len(vrfs_without_fs)]
                    except (ValueError, IndexError):
                        console.print("[red]Invalid selection[/red]")
                        continue
                
                if not selected_vrfs:
                    continue
                
                # Get BGP ASN for VRF config
                asn_match = re.search(r'protocols\s+bgp\s+(\d+)', running_config)
                bgp_asn = asn_match.group(1) if asn_match else "65000"
                
                # Get RT from existing VRF or ask
                console.print(f"\n[dim]Route-Target for FlowSpec-VPN import/export[/dim]")
                rt_suggestion = f"{bgp_asn}:100"
                rt_value = Prompt.ask("Route-Target", default=rt_suggestion)
                
                # Generate config
                config_lines = ["network-services", "  vrf"]
                for vrf in selected_vrfs:
                    config_lines.extend([
                        f"    instance {vrf}",
                        "      protocols",
                        f"        bgp {bgp_asn}",
                        "          address-family ipv4-flowspec",
                        f"            export-vpn route-target {rt_value}",
                        f"            import-vpn route-target {rt_value}",
                        "          !",
                        "          address-family ipv6-flowspec",
                        f"            export-vpn route-target {rt_value}",
                        f"            import-vpn route-target {rt_value}",
                        "          !",
                        "        !",
                        "      !",
                        "    !",
                    ])
                config_lines.extend(["  !", "!"])
                
                vrf_config = '\n'.join(config_lines)
                
                syntax = Syntax(vrf_config, "bash", theme="monokai")
                console.print(Panel(syntax, title=f"VRF FlowSpec Config ({len(selected_vrfs)} VRFs)", border_style="green"))
                
                if Confirm.ask("Push this configuration?", default=True):
                    from .wizard.push import push_and_verify
                    success, message = push_and_verify(
                        device,
                        vrf_config,
                        dry_run=False,
                        use_terminal_paste=False,
                        use_merge=True
                    )
                    if success:
                        console.print(f"[bold green]✓ FlowSpec configured on {len(selected_vrfs)} VRFs![/bold green]")
                        single_ctx.discover_all()
                        running_config = single_ctx.configs.get(device.hostname, "")
                        temp_state.current_config = running_config
            
            elif choice == "a":
                # Launch FSVPN Wizard
                console.print("\n[bold magenta]━━━ FSVPN Wizard (FlowSpec VPN Diagnostic Tool) ━━━[/bold magenta]")
                console.print("[dim]Comprehensive analysis: BGP sessions, VRF import, TCAM/datapath, local policies[/dim]\n")
                
                fsvpn_path = Path("/home/dn/SCALER/FLOWSPEC_VPN/fsvpn_wizard.py")
                if not fsvpn_path.exists():
                    console.print("[red]FSVPN Wizard not found at expected path[/red]")
                    continue
                
                console.print("[bold]Options:[/bold]")
                console.print("  [1] Launch interactive wizard (new session)")
                console.print("  [2] Quick analysis on this device")
                console.print("  [B] Back")
                
                fsvpn_choice = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="1").lower()
                
                if fsvpn_choice == "b":
                    continue
                elif fsvpn_choice == "1":
                    import subprocess
                    console.print("[cyan]Launching FSVPN Wizard in new terminal...[/cyan]")
                    console.print("[dim]Close the wizard window when done, then return here[/dim]")
                    try:
                        subprocess.Popen(
                            ["tmux", "new-window", "-n", "fsvpn", f"python3 {fsvpn_path}"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        console.print("[green]✓ FSVPN Wizard launched in tmux window 'fsvpn'[/green]")
                    except Exception as e:
                        console.print(f"[yellow]Could not launch in tmux: {e}[/yellow]")
                        console.print(f"[dim]Run manually: python3 {fsvpn_path}[/dim]")
                elif fsvpn_choice == "2":
                    # Quick analysis - run show commands
                    console.print(f"\n[cyan]Running FlowSpec analysis on {device.hostname}...[/cyan]")
                    
                    # Try to get live data
                    try:
                        from .device_connector import DeviceConnector
                        connector = DeviceConnector(device)
                        
                        with console.status("[cyan]Connecting...[/cyan]"):
                            ssh = connector.connect()
                        
                        if ssh:
                            channel = ssh.invoke_shell()
                            channel.settimeout(30)
                            time.sleep(1)
                            while channel.recv_ready():
                                channel.recv(65535)
                            
                            analysis_results = []
                            
                            # Quick analysis commands
                            commands = [
                                ("BGP FlowSpec Summary", "show protocols bgp summary | include flowspec"),
                                ("FlowSpec Interfaces", "show config | flatten | include 'flowspec enabled'"),
                                ("Local Policies", "show routing-policy flowspec-local-policies"),
                                ("FS Rules (sample)", "show forwarding-options flowspec | head 20"),
                            ]
                            
                            for name, cmd in commands:
                                channel.send(f"{cmd}\n")
                                time.sleep(2)
                                output = ""
                                while channel.recv_ready():
                                    output += channel.recv(65535).decode('utf-8', errors='ignore')
                                analysis_results.append((name, output.strip()[-500:]))  # Last 500 chars
                            
                            channel.close()
                            ssh.close()
                            
                            # Display results
                            for name, output in analysis_results:
                                if output and len(output) > 50:
                                    console.print(f"\n[bold cyan]{name}:[/bold cyan]")
                                    # Clean output
                                    clean = re.sub(r'\x1b\[[0-9;]*m', '', output)
                                    for line in clean.split('\n')[-10:]:
                                        if line.strip():
                                            console.print(f"  [dim]{line.strip()[:80]}[/dim]")
                                else:
                                    console.print(f"\n[bold cyan]{name}:[/bold cyan] [dim]No data[/dim]")
                        else:
                            console.print("[yellow]Could not connect to device[/yellow]")
                    except Exception as e:
                        console.print(f"[yellow]Analysis error: {e}[/yellow]")
            
            elif choice == "d":
                # Dependency check
                show_flowspec_dependency_report(temp_state)
            
            elif choice == "v":
                # View FlowSpec config
                fs_section = _extract_flowspec_section(running_config) if running_config else None
                
                if fs_section:
                    syntax = Syntax(fs_section, "bash", theme="monokai")
                    console.print(Panel(syntax, title=f"FlowSpec Config - {device.hostname}", border_style="magenta"))
                else:
                    console.print("[dim]No FlowSpec configuration found[/dim]")
        
        except (BackException, TopException):
            continue


def _show_multi_device_compare(multi_ctx: 'MultiDeviceContext'):
    """Compare configurations between ALL devices in multi-device mode."""
    from rich.columns import Columns
    from rich.panel import Panel
    
    num_devices = len(multi_ctx.devices)
    hostnames = [d.hostname for d in multi_ctx.devices]
    
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════════[/bold cyan]")
    console.print(f"[bold cyan]        📊 Multi-Device Configuration Comparison ({num_devices} devices)        [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════════[/bold cyan]")
    
    if num_devices < 2:
        console.print("[yellow]Need at least 2 devices to compare.[/yellow]")
        return
    
    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 1: System Info - ALL Devices Grid
    # ═══════════════════════════════════════════════════════════════════════
    console.print("\n[bold]━━━ System Information (All Devices) ━━━[/bold]")
    
    sys_table = Table(box=box.ROUNDED, show_header=True)
    sys_table.add_column("Property", style="cyan", width=15)
    for h in hostnames:
        # Truncate hostname for column header
        display_name = h[:12] + "…" if len(h) > 12 else h
        sys_table.add_column(display_name, width=14, justify="center")
    sys_table.add_column("Match", justify="center", width=7)
    
    # Gather all data
    summaries = {h: multi_ctx.summaries.get(h, DeviceSummary()) for h in hostnames}
    
    # DNOS Version row
    versions = [summaries[h].dnos_version or "N/A" for h in hostnames]
    all_same = len(set(versions)) == 1
    match = "[green]✓[/green]" if all_same else "[yellow]≠[/yellow]"
    sys_table.add_row("DNOS Version", *versions, match)
    
    # System Type row
    types = [summaries[h].system_type or "N/A" for h in hostnames]
    all_same = len(set(types)) == 1
    match = "[green]✓[/green]" if all_same else "[yellow]≠[/yellow]"
    sys_table.add_row("System Type", *types, match)
    
    # BGP ASN row
    asns = [str(multi_ctx.bgp_asn.get(h, 0) or "N/A") for h in hostnames]
    non_zero = [a for a in asns if a != "0" and a != "N/A"]
    all_same = len(set(non_zero)) <= 1
    match = "[green]✓[/green]" if all_same else "[red]✗[/red]"
    sys_table.add_row("BGP ASN", *asns, match)
    
    # Loopback row
    loopbacks = [multi_ctx.loopbacks.get(h, "N/A") for h in hostnames]
    sys_table.add_row("Loopback", *loopbacks, "[dim]-[/dim]")
    
    # Uptime row
    uptimes = [summaries[h].uptime or "N/A" for h in hostnames]
    # Truncate uptime for display
    uptimes_display = [u[:12] + "…" if len(u) > 12 else u for u in uptimes]
    sys_table.add_row("Uptime", *uptimes_display, "[dim]-[/dim]")
    
    console.print(sys_table)
    
    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 2: Scale Comparison - ALL Devices
    # ═══════════════════════════════════════════════════════════════════════
    console.print("\n[bold]━━━ Scale & Counts (All Devices) ━━━[/bold]")
    
    # Gather data for all devices
    all_rt = {h: multi_ctx.route_targets.get(h, set()) for h in hostnames}
    all_ifaces = {h: set(multi_ctx.interfaces.get(h, [])) for h in hostnames}
    all_mh = {h: multi_ctx.mh_config.get(h, {}) for h in hostnames}
    
    # Categorize interfaces per device
    all_pwhe = {h: {i for i in all_ifaces[h] if i.startswith('ph')} for h in hostnames}
    all_l2 = {h: {i for i in all_ifaces[h] if re.match(r'^[gx]e[\d\-/]+\.\d+', i)} for h in hostnames}
    all_bundle = {h: {i for i in all_ifaces[h] if 'bundle' in i.lower()} for h in hostnames}
    
    # Service counts
    def count_services(config: str) -> dict:
        fxc = len(re.findall(r'flexible-cross-connect-group', config))
        l2vpn = len(re.findall(r'l2vpn-instance\s+\S+', config))
        evpn = len(re.findall(r'evpn-instance\s+\S+', config))
        vpws = len(re.findall(r'vpws-service-id\s+\d+', config))
        vrf_blocks = re.findall(r'^\s{2}vrf\n(.*?)(?=^\s{2}\S|\Z)', config, re.MULTILINE | re.DOTALL)
        vrf = sum(len(re.findall(r'^\s{4}instance\s+\S+', block, re.MULTILINE)) for block in vrf_blocks)
        return {'fxc': fxc, 'l2vpn': l2vpn, 'evpn': evpn, 'vpws': vpws, 'vrf': vrf}
    
    all_svc = {h: count_services(multi_ctx.configs.get(h, "")) for h in hostnames}
    
    scale_table = Table(box=box.ROUNDED, show_header=True)
    scale_table.add_column("Category", style="cyan", width=18)
    for h in hostnames:
        display_name = h[:10] + "…" if len(h) > 10 else h
        scale_table.add_column(display_name, justify="right", width=12)
    scale_table.add_column("Status", justify="center", width=8)
    
    def add_scale_row(name, data_dict, is_set=True):
        if is_set:
            values = [f"{len(data_dict[h]):,}" for h in hostnames]
            counts = [len(data_dict[h]) for h in hostnames]
        else:
            values = [f"{data_dict[h]:,}" for h in hostnames]
            counts = list(data_dict.values())
        
        # Check if all same (or all zero)
        non_zero = [c for c in counts if c > 0]
        if not non_zero:
            status = "[dim]✓[/dim]"
        elif len(set(counts)) == 1:
            status = "[green]✓ SYNC[/green]"
        else:
            status = "[yellow]≠ DIFF[/yellow]"
        
        scale_table.add_row(name, *values, status)
    
    add_scale_row("Route Targets", all_rt)
    add_scale_row("Interfaces", all_ifaces)
    add_scale_row("  └ PWHE", all_pwhe)
    add_scale_row("  └ L2 Sub-ifs", all_l2)
    add_scale_row("  └ Bundles", all_bundle)
    add_scale_row("Multihoming", {h: set(all_mh[h].keys()) for h in hostnames})
    
    # Services
    for svc_name in ['fxc', 'l2vpn', 'evpn', 'vpws', 'vrf']:
        svc_data = {h: all_svc[h].get(svc_name, 0) for h in hostnames}
        add_scale_row(f"Svc: {svc_name.upper()}", svc_data, is_set=False)
    
    console.print(scale_table)
    
    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 3: VRF & Route Target Analysis
    # ═══════════════════════════════════════════════════════════════════════
    console.print("\n[bold]━━━ VRF & Route Targets ━━━[/bold]")
    
    # Count VRFs per device from config
    def count_vrfs(config: str) -> dict:
        # VRF instances
        vrf_names = set(re.findall(r'vrf\s+(\S+)\s*\n', config))
        # L3VPN VRFs
        l3vpn_vrfs = set(re.findall(r'l3vpn\s+vrf\s+(\S+)', config))
        vrf_names.update(l3vpn_vrfs)
        return vrf_names
    
    all_vrfs = {h: count_vrfs(multi_ctx.configs.get(h, "")) for h in hostnames}
    
    # VRF table
    vrf_table = Table(box=box.ROUNDED, show_header=True, title="[bold]VRF Scale[/bold]")
    vrf_table.add_column("Device", style="cyan", width=18)
    vrf_table.add_column("VRFs", justify="right", width=8)
    vrf_table.add_column("RTs", justify="right", width=8)
    vrf_table.add_column("Route Targets", width=50)
    
    for h in hostnames:
        vrf_count = len(all_vrfs[h])
        rt_count = len(all_rt[h])
        rt_sample = sorted(list(all_rt[h]))[:4]
        rt_display = ", ".join(rt_sample)
        if len(all_rt[h]) > 4:
            rt_display += f"... (+{len(all_rt[h]) - 4})"
        vrf_table.add_row(
            h[:16] + "…" if len(h) > 16 else h,
            f"{vrf_count:,}",
            f"{rt_count:,}",
            rt_display if rt_display else "[dim]none[/dim]"
        )
    
    console.print(vrf_table)
    
    # Shared RT analysis
    if any(all_rt[h] for h in hostnames):
        # Find RTs that appear on multiple devices
        rt_device_map = {}  # RT -> list of devices that have it
        for h in hostnames:
            for rt in all_rt[h]:
                if rt not in rt_device_map:
                    rt_device_map[rt] = []
                rt_device_map[rt].append(h)
        
        shared_rts = {rt: devs for rt, devs in rt_device_map.items() if len(devs) > 1}
        unique_rts = {rt: devs[0] for rt, devs in rt_device_map.items() if len(devs) == 1}
        
        if shared_rts:
            console.print(f"\n[bold green]✓ Shared RTs ({len(shared_rts)}):[/bold green]")
            for rt, devs in sorted(shared_rts.items())[:10]:
                dev_names = ", ".join([d[:10] for d in devs])
                console.print(f"  • [green]{rt}[/green] → {dev_names}")
            if len(shared_rts) > 10:
                console.print(f"  [dim]... and {len(shared_rts) - 10} more shared RTs[/dim]")
        
        if unique_rts:
            console.print(f"\n[bold yellow]⚠ Unique RTs ({len(unique_rts)}):[/bold yellow]")
            # Group by device
            by_device = {}
            for rt, dev in unique_rts.items():
                if dev not in by_device:
                    by_device[dev] = []
                by_device[dev].append(rt)
            
            for dev, rts in by_device.items():
                sample = sorted(rts)[:5]
                console.print(f"  [cyan]{dev[:15]}[/cyan]: {', '.join(sample)}{'...' if len(rts) > 5 else ''}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 4: Pairwise Differences Summary
    # ═══════════════════════════════════════════════════════════════════════
    console.print("\n[bold]━━━ Pairwise Differences ━━━[/bold]")
    
    # Find unique items per device (not on any other device)
    unique_items = {}
    for h in hostnames:
        other_rt = set().union(*[all_rt[oh] for oh in hostnames if oh != h])
        other_pwhe = set().union(*[all_pwhe[oh] for oh in hostnames if oh != h])
        unique_items[h] = {
            'rt': all_rt[h] - other_rt,
            'pwhe': all_pwhe[h] - other_pwhe,
        }
    
    has_unique = any(unique_items[h]['rt'] or unique_items[h]['pwhe'] for h in hostnames)
    
    if has_unique:
        for h in hostnames:
            u = unique_items[h]
            if u['rt'] or u['pwhe']:
                console.print(f"\n[cyan]{h}[/cyan] unique items:")
                if u['rt']:
                    sample = sorted(list(u['rt']))[:5]
                    console.print(f"  • [yellow]{len(u['rt'])} Route Targets[/yellow]: {', '.join(sample)}{'...' if len(u['rt']) > 5 else ''}")
                if u['pwhe']:
                    sample = sorted(list(u['pwhe']))[:5]
                    console.print(f"  • [yellow]{len(u['pwhe'])} PWHE interfaces[/yellow]: {', '.join(sample)}{'...' if len(u['pwhe']) > 5 else ''}")
    else:
        console.print("[green]✓ No unique items - devices share similar configurations[/green]")
    
    # Options
    console.print("\n[bold]Options:[/bold]")
    console.print("  [1] Export all diffs to file")
    if num_devices > 2:
        console.print("  [2] Compare specific pair (detailed)")
    console.print("  [B] Back")
    
    valid_choices = ["1", "b", "B"]
    if num_devices > 2:
        valid_choices.append("2")
    
    choice = Prompt.ask("Select", choices=valid_choices, default="b").lower()
    
    if choice == "1":
        # Export diff for all devices
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        diff_path = Path(f"db/configs/compare_all_{num_devices}devices_{timestamp}.txt")
        with open(diff_path, 'w') as f:
            f.write(f"Configuration Comparison: {', '.join(hostnames)}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")
            
            for h in hostnames:
                f.write(f"\n=== {h} ===\n")
                f.write(f"Route Targets ({len(all_rt[h])}): {sorted(all_rt[h])}\n")
                f.write(f"PWHE ({len(all_pwhe[h])}): {sorted(all_pwhe[h])}\n")
                f.write(f"Services: FXC={all_svc[h]['fxc']}, L2VPN={all_svc[h]['l2vpn']}, EVPN={all_svc[h]['evpn']}\n")
            
            f.write(f"\n=== Unique Items ===\n")
            for h in hostnames:
                u = unique_items[h]
                if u['rt'] or u['pwhe']:
                    f.write(f"\n{h}:\n")
                    if u['rt']:
                        f.write(f"  Unique RTs: {sorted(u['rt'])}\n")
                    if u['pwhe']:
                        f.write(f"  Unique PWHE: {sorted(u['pwhe'])}\n")
        
        console.print(f"[green]✓ Exported to {diff_path}[/green]")
    
    elif choice == "2" and num_devices > 2:
        # Select pair for detailed comparison
        console.print("\n[bold]Select devices to compare:[/bold]")
        for i, h in enumerate(hostnames, 1):
            console.print(f"  [{i}] {h}")
        
        d1 = Prompt.ask("First device", choices=[str(i) for i in range(1, num_devices + 1)], default="1")
        d2 = Prompt.ask("Second device", choices=[str(i) for i in range(1, num_devices + 1)], default="2")
        
        h1_sel = hostnames[int(d1) - 1]
        h2_sel = hostnames[int(d2) - 1]
        
        if h1_sel == h2_sel:
            console.print("[yellow]Same device selected - please choose different devices[/yellow]")
        else:
            console.print(f"\n[bold cyan]Detailed comparison: {h1_sel} vs {h2_sel}[/bold cyan]")
            
            # Quick diff
            rt1, rt2 = all_rt[h1_sel], all_rt[h2_sel]
            pwhe1, pwhe2 = all_pwhe[h1_sel], all_pwhe[h2_sel]
            
            console.print(f"\n[cyan]Route Targets:[/cyan]")
            console.print(f"  Shared: {len(rt1 & rt2)}, Only {h1_sel}: {len(rt1 - rt2)}, Only {h2_sel}: {len(rt2 - rt1)}")
            
            console.print(f"\n[cyan]PWHE Interfaces:[/cyan]")
            console.print(f"  Shared: {len(pwhe1 & pwhe2)}, Only {h1_sel}: {len(pwhe1 - pwhe2)}, Only {h2_sel}: {len(pwhe2 - pwhe1)}")
            
            if pwhe1 - pwhe2:
                sample = sorted(list(pwhe1 - pwhe2))[:5]
                console.print(f"    {h1_sel}: {', '.join(sample)}{'...' if len(pwhe1 - pwhe2) > 5 else ''}")
            if pwhe2 - pwhe1:
                sample = sorted(list(pwhe2 - pwhe1))[:5]
                console.print(f"    {h2_sel}: {', '.join(sample)}{'...' if len(pwhe2 - pwhe1) > 5 else ''}")
    
    Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")


def _check_device_upgrade_status(multi_ctx: 'MultiDeviceContext'):
    """Check and display the upgrade/install status of all devices."""
    import paramiko
    from rich.table import Table as RichTable
    from pathlib import Path
    from datetime import datetime
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from rich.live import Live
    from rich.spinner import Spinner
    from rich.text import Text
    
    def check_single_device(device):
        """Check status of a single device - runs in thread."""
        return _check_single_device_status(device)
    
    # Show spinner while checking
    console.print("[cyan]📊 Checking devices in parallel...[/cyan]")
    
    # Check all devices in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=min(len(multi_ctx.devices), 8)) as executor:
        futures = {executor.submit(check_single_device, dev): dev for dev in multi_ctx.devices}
        for future in as_completed(futures):
            device = futures[future]
            try:
                results[device.hostname] = future.result()
            except Exception as e:
                results[device.hostname] = {
                    'mode': f"[red]Error: {str(e)[:15]}[/red]",
                    'dnos_ver': "-",
                    'gi_ver': "-",
                    'baseos_ver': "-",
                    'install_status': f"[red]{str(e)[:25]}[/red]"
                }
    
    # Build table from results
    table = RichTable(title="Device Upgrade Status", box=box.ROUNDED, expand=True, show_header=True)
    table.add_column("Device", style="cyan", width=8, no_wrap=True)
    table.add_column("Mode", style="yellow", width=14, no_wrap=False)
    table.add_column("DNOS", style="green", width=20, no_wrap=False)
    table.add_column("GI", style="blue", width=18, no_wrap=False)
    table.add_column("BaseOS", style="magenta", width=18, no_wrap=False)
    table.add_column("Install Status", min_width=35, no_wrap=False, overflow="fold")
    
    recovery_devices = []  # Track devices in recovery mode
    
    for device in multi_ctx.devices:
        r = results.get(device.hostname, {})
        
        # Helper to safely truncate Rich markup strings
        def truncate_rich_text(text, max_len):
            """Truncate text while preserving Rich markup if present."""
            text_str = str(text)
            # Remove Rich markup tags for length calculation
            import re
            clean_text = re.sub(r'\[/?[^\]]+\]', '', text_str)
            if len(clean_text) <= max_len:
                return text
            # Truncate and add ellipsis
            trunc_len = max_len - 3
            return text_str[:trunc_len] + "..."
        
        # Truncate long version strings if needed (but keep Install Status longer)
        dnos_ver = truncate_rich_text(r.get('dnos_ver', '-'), 20)
        gi_ver = truncate_rich_text(r.get('gi_ver', '-'), 18)
        baseos_ver = truncate_rich_text(r.get('baseos_ver', '-'), 18)
        # Don't truncate Install Status - let it wrap/overflow
        install_status = r.get('install_status', '[dim]Unknown[/dim]')
        
        # Track recovery mode devices
        if '[bold red]RECOVERY[/bold red]' in str(r.get('mode', '')):
            recovery_devices.append(device)
        
        table.add_row(
            device.hostname,
            r.get('mode', '[dim]?[/dim]'),
            dnos_ver,
            gi_ver,
            baseos_ver,
            install_status
        )
    
    console.print(table)
    console.print("\n[dim]💡 Tip: If devices are rebooting, wait 10-15 minutes and check again.[/dim]")
    
    # If any devices in recovery mode, offer diagnostic or restore
    if recovery_devices:
        console.print(f"\n[bold red]⚠ {len(recovery_devices)} device(s) in RECOVERY mode detected![/bold red]")
        for dev in recovery_devices:
            console.print(f"  • {dev.hostname}")
        
        console.print("\n[bold]Options:[/bold]")
        console.print("  [1] [red]🔧 System Restore[/red] - Restore device(s) from recovery mode")
        console.print("  [2] [cyan]🔍 Run Diagnostic[/cyan] - Analyze recovery mode state")
        console.print("  [3] Skip - Return to menu")
        
        recovery_choice = Prompt.ask("Select", choices=["1", "2", "3"], default="1")
        
        if recovery_choice == "1":
            # Run System Restore
            for dev in recovery_devices:
                try:
                    from .wizard.system_restore import run_system_restore_wizard
                    run_system_restore_wizard(dev, multi_ctx)
                except Exception as e:
                    console.print(f"[red]Error restoring {dev.hostname}: {e}[/red]")
        elif recovery_choice == "2":
            # Run diagnostic
            for dev in recovery_devices:
                _diagnose_device_recovery(dev)


def _check_single_device_status(device) -> dict:
    """Check upgrade status of a single device. Returns dict with status info."""
    import paramiko
    from pathlib import Path
    from datetime import datetime
    
    result = {
        'mode': '[dim]?[/dim]',
        'dnos_ver': '-',
        'gi_ver': '-',
        'baseos_ver': '-',
        'install_status': '[dim]Unknown[/dim]'
    }
    
    # Load saved info from operational.json
    try:
        op_file = Path(f"db/configs/{device.hostname}/operational.json")
        if op_file.exists():
            with open(op_file) as f:
                op_data = json.load(f)
            # PE-2: use console-detected recovery when SSH may be down (synced from Refresh flow)
            if device.hostname == "PE-2" and op_data.get("console_recovery_detected") is True:
                result['mode'] = "[bold red]RECOVERY[/bold red]"
                result['install_status'] = "[bold red]❌ In recovery (detected via console)[/bold red]"
                return result
            import re
            # Extract versions from saved URLs (no "v" prefix to match device output)
            dnos_url = op_data.get('dnos_url', '')
            if dnos_url:
                match = re.search(r'dnos[_-](\d+\.\d+\.\d+\.\d+)', dnos_url)
                if match:
                    result['dnos_ver'] = f"[dim]{match.group(1)}[/dim]"  # dim = from cache
            gi_url = op_data.get('gi_url', '')
            if gi_url:
                match = re.search(r'gi[_-](\d+\.\d+\.\d+\.\d+)', gi_url)
                if match:
                    result['gi_ver'] = f"[dim]{match.group(1)}[/dim]"
                else:
                    result['gi_ver'] = "[dim]✓[/dim]"
            baseos_url = op_data.get('baseos_url', '')
            if baseos_url:
                match = re.search(r'base[_-]?os[_-](\d+\.\d+)', baseos_url, re.IGNORECASE)
                if match:
                    result['baseos_ver'] = f"[dim]{match.group(1)}[/dim]"
                else:
                    result['baseos_ver'] = "[dim]✓[/dim]"
    except:
        pass
    
    # Try connection (SSH, console, virsh) via unified path
    try:
        from .connection_strategy import connect_for_upgrade
        conn = connect_for_upgrade(device.hostname, timeout=15)
        if not conn['connected']:
            # Ghost-IP landing: we reached SSH but hit a different device
            # (e.g. the old mgmt IP has been reassigned in the lab). Surface
            # this explicitly so the wizard row shows a diagnostic badge
            # instead of silently reporting "?" -- which looks identical to
            # a normal SSH timeout and hides the real problem.
            if conn.get('ghost_ip'):
                remote = (conn.get('ghost_remote_hostname') or '').strip() or 'another device'
                result['mode'] = "[bold red]GHOST-IP[/bold red]"
                result['install_status'] = (
                    f"[bold red]Stored mgmt IP answers as {remote}. Re-run SSH discovery.[/bold red]"
                )
            return result

        ssh = conn['ssh']
        channel = conn['channel']
        
        conn_state = (conn.get('device_state') or '').upper()
        
        # Use single shell for all commands - much faster
        channel.settimeout(8)
        channel.send("\r\n")
        time.sleep(0.5)
        initial_output = channel.recv(10000).decode(errors='ignore')
        if not initial_output and conn.get('prompt_output'):
            initial_output = conn['prompt_output']
        
        from .connection_strategy import detect_device_mode, classify_device_state
        mode = classify_device_state(conn_state) or detect_device_mode(initial_output)
        
        if mode == "RECOVERY":
            result['mode'] = "[bold red]RECOVERY[/bold red]"
            result['install_status'] = "[bold red]BOOT FAILURE - Device in recovery mode[/bold red]"
            ssh.close()
            return result
        
        # Tri-state classifier. The previous code used a binary
        # `is_gi_mode ? GI : DNOS` which DEFAULTED every unknown/
        # ambiguous detection to DNOS -- causing PE-4 (live in GI)
        # to be re-stamped as DNOS whenever the probe landed on a
        # noisy banner (virsh attach chatter, password prompt echo,
        # partial shell output). `_persist_live_status_to_ops` then
        # wrote device_state=DNOS to operational.json, overwriting
        # the legitimate GI classification from connect_for_upgrade.
        # See `/home/dn/drivenets-topology-studio/topology/DEVELOPMENT_GUIDELINES.md`
        # section "DNOS Phantom Classification (2026-04)".
        is_gi_mode = (mode == "GI")
        is_dnos_mode = (mode == "DNOS")
        if is_gi_mode:
            result['mode'] = "[yellow]GI[/yellow]"
        elif is_dnos_mode:
            result['mode'] = "[green]DNOS[/green]"
        else:
            # Mode detection failed: connection succeeded (we reached
            # a prompt) but we cannot confidently classify the output
            # as GI or DNOS. Report indeterminate and bail early --
            # this is what `_persist_live_status_to_ops` treats as
            # an SSH error (does not overwrite a known-good state
            # in the DB). Never default to DNOS here.
            result['mode'] = "[dim]?[/dim]"
            result['install_status'] = "[dim]Mode indeterminate (prompt unclassified)[/dim]"
            try:
                ssh.close()
            except Exception:
                pass
            return result
        
        if is_gi_mode:
            # In GI mode the stack is wiped -- there is no "current" DNOS
            # version until post-deploy verify re-populates it. Setting the
            # version fields to "-" keeps `_persist_live_status_to_ops` from
            # writing a fake value (the previous implementation prefixed the
            # cached URL version with a loading emoji and leaked both the
            # emoji AND the stale version string into operational.json).
            result['dnos_ver'] = "-"
            result['gi_ver'] = "-"
            result['baseos_ver'] = "-"
            result['install_status'] = "[yellow][LOADING] Deploying...[/yellow]"
        else:
            # DNOS mode - get stack info with single command
            channel.send("show system stack | no-more\n")
            time.sleep(0.8)
            stack_output = ""
            while channel.recv_ready():
                stack_output += channel.recv(65535).decode(errors='ignore')
            
            # Parse stack output for versions and check if fully deployed
            all_synced = True  # Track if Current == Target for all components
            has_dnos = False
            
            for line in stack_output.split('\n'):
                if '|' in line and '---' not in line:
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    if len(parts) >= 5:
                        component = parts[0].upper()
                        current_version = parts[4]
                        target_version = parts[5] if len(parts) > 5 else '-'
                        
                        if current_version and current_version != '-':
                            if 'DNOS' in component:
                                has_dnos = True
                                result['dnos_ver'] = f"[green]{current_version[:15]}[/green]"
                                # Check if synced
                                if target_version and target_version != '-' and current_version != target_version:
                                    all_synced = False
                            elif 'GI' in component:
                                result['gi_ver'] = f"[green]{current_version[:10]}[/green]"
                            elif 'BASE' in component:
                                result['baseos_ver'] = f"[green]{current_version[:10]}[/green]"
                        elif target_version and target_version != '-':
                            # Has target but no current = still loading
                            all_synced = False
            
            # Get install status
            channel.send("show system install | no-more\n")
            time.sleep(0.8)
            install_output = ""
            while channel.recv_ready():
                install_output += channel.recv(65535).decode(errors='ignore')
            
            # Check operational.json for install initiation timestamp
            install_initiated = None
            target_dnos_version = None
            try:
                op_file = Path(f"db/configs/{device.hostname}/operational.json")
                if op_file.exists():
                    with open(op_file) as f:
                        op_data = json.load(f)
                        install_initiated = op_data.get('install_start')
                        target_dnos_version = op_data.get('dnos_version')
                        upgrade_in_progress = op_data.get('upgrade_in_progress', False)
            except:
                pass
            
            # Quick parse for install status
            # Check for actual in-progress tasks (not just section headers)
            has_running_task = False
            running_pkg = None
            
            in_running_section = False
            for line in install_output.split('\n'):
                if 'Running tasks:' in line:
                    in_running_section = True
                    continue
                elif 'Finished tasks:' in line:
                    in_running_section = False
                    continue
                
                # Only look for tasks in the Running tasks section
                if in_running_section and '|' in line and '---' not in line:
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    # Valid running task: NCC/NCP/NCF/NCM | node_id | serial | pkg_type | ...
                    if len(parts) >= 4 and parts[0] in ('NCC', 'NCP', 'NCF', 'NCM'):
                        has_running_task = True
                        running_pkg = parts[3] if len(parts) > 3 else 'Unknown'
                        break
            
            # Check if target stack exists and differs from current
            has_target_stack = False
            target_differs = False
            for line in stack_output.split('\n'):
                if '|' in line and '---' not in line:
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    if len(parts) >= 6:
                        component = parts[0].upper()
                        current_version = parts[4]
                        target_version = parts[5]
                        if 'DNOS' in component and target_version and target_version != '-' and target_version != current_version:
                            has_target_stack = True
                            target_differs = True
                            break
                        elif 'DNOS' in component and target_version and target_version != '-':
                            has_target_stack = True
            
            if has_running_task:
                result['install_status'] = f"[yellow]🔄 {running_pkg} installing...[/yellow]"
            elif 'FAILED' in install_output:
                result['install_status'] = "[red]❌ Failed[/red]"
            elif target_differs:
                # Target stack exists and differs from current - install pending
                result['install_status'] = "[yellow]⏳ Target stack ready, install pending[/yellow]"
            elif has_target_stack and not all_synced:
                # Has target stack but not fully synced yet
                result['install_status'] = "[yellow]⏳ Installing...[/yellow]"
            elif all_synced and has_dnos:
                # All components synced (Current == Target) and DNOS is present
                if install_initiated or upgrade_in_progress:
                    # Install was initiated - check if it completed recently
                    result['install_status'] = "[green]✅ Ready (install completed)[/green]"
                else:
                    # No install was initiated - device was already at this version
                    result['install_status'] = "[green]✅ Ready (no install needed)[/green]"
            elif 'idle' in install_output.lower() or 'no running' in install_output.lower():
                if install_initiated:
                    result['install_status'] = "[green]✅ Ready (install completed)[/green]"
                else:
                    result['install_status'] = "[green]✅ Ready[/green]"
            else:
                result['install_status'] = "[dim]Ready[/dim]"
        
        channel.close()
        ssh.close()
        
    except Exception as e:
        error_msg = str(e)[:30]
        if 'timeout' in error_msg.lower() or 'timed out' in error_msg.lower():
            result['mode'] = "[yellow]⏳ Rebooting[/yellow]"
        elif 'refused' in error_msg.lower():
            result['mode'] = "[yellow]⏳ Starting[/yellow]"
        elif 'auth' in error_msg.lower():
            result['mode'] = "[red]🔒 Auth Fail[/red]"
        else:
            result['mode'] = f"[dim]? {error_msg[:12]}[/dim]"
        result['install_status'] = f"[dim]Conn: {error_msg[:20]}[/dim]"
    
    return result



def _monitor_triggered_builds(jenkins: 'JenkinsClient', multi_ctx: 'MultiDeviceContext'):
    """Monitor and display status of recently triggered/running builds."""
    from rich.table import Table as RichTable
    from rich.live import Live
    from rich.panel import Panel
    from rich.text import Text
    
    console.print("\n[bold magenta]📊 Monitor Triggered Builds[/bold magenta]")
    console.print("[dim]Check build status, monitor progress, trigger new builds[/dim]\n")
    
    # Ask for branch or show recent
    console.print("  [1] Enter branch name to monitor")
    console.print("  [2] Show dev branches (dev_v*)")
    console.print("  [3] Show feature branches (feature/*)")
    console.print("  [4] Show all recent branches")
    console.print("  [B] Back")
    
    mon_choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "b", "B"], default="1").lower()
    
    if mon_choice == "b":
        return
    
    if mon_choice in ["2", "3", "4"]:
        # Show builds for different branch patterns
        # Note: Jenkins URL-encodes branch names, so feature/xxx becomes feature%2Fxxx
        if mon_choice == "2":
            pattern = r'^dev_v\d+'
            title = "Dev Branch Builds (dev_v*)"
        elif mon_choice == "3":
            # Match both feature/ and feature%2F (URL-encoded)
            pattern = r'(^feature[/%]|feature%2F)'
            title = "Feature Branch Builds (feature/*)"
        else:
            pattern = None  # All branches
            title = "All Recent Builds"
        
        console.print(f"\n[dim]Fetching {title.lower()} (this may take a moment)...[/dim]")
        try:
            # Get branches matching pattern
            branches = jenkins.list_cheetah_branches(pattern=pattern)[:20]
            
            if not branches:
                console.print(f"[yellow]No branches found matching pattern[/yellow]")
                Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")
                return
            
            table = RichTable(title=title, box=box.ROUNDED)
            table.add_column("Branch", style="cyan", max_width=50)
            table.add_column("Build #", justify="right")
            table.add_column("Status")
            table.add_column("Age", justify="right")
            table.add_column("ETA", justify="right")
            
            builds_found = 0
            console.print(f"[dim]Checking {len(branches)} branches...[/dim]")
            
            for i, branch in enumerate(branches):
                # Fetch the latest build for this branch
                try:
                    build = jenkins.get_build_info(branch.name)
                    if build:
                        builds_found += 1
                        status_icon = "🔄" if build.building else ("✅" if build.result == "SUCCESS" else "❌")
                        status_text = "Building..." if build.building else (build.result or "Unknown")
                        
                        # Calculate ETA for building
                        if build.building:
                            # Estimate ~45 min total build time
                            elapsed_min = build.age_hours * 60
                            eta_min = max(0, 45 - elapsed_min)
                            eta = f"~{int(eta_min)}m" if eta_min > 0 else "Soon"
                        else:
                            eta = "-"
                        
                        age = f"{build.age_hours:.1f}h" if build.age_hours < 24 else f"{build.age_hours/24:.1f}d"
                        
                        # Highlight building or recent builds
                        branch_style = "bold yellow" if build.building else ("green" if build.age_hours < 2 else "cyan")
                        
                        table.add_row(
                            f"[{branch_style}]{branch.name[:50]}[/{branch_style}]",
                            f"#{build.build_number}",
                            f"{status_icon} {status_text}",
                            age,
                            eta
                        )
                except Exception:
                    # Skip branches we can't fetch
                    pass
            
            if builds_found > 0:
                console.print(table)
                console.print(f"\n[dim]Showing {builds_found} branches. Yellow = building, Green = recent (<2h).[/dim]")
            else:
                console.print("[yellow]No builds found for any branches[/yellow]")
            
        except Exception as e:
            console.print(f"[red]Error fetching builds: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        
        Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")
        return
    
    # Monitor specific branch
        console.print("[dim]Enter branch name (e.g., feature/dev_v26_1/flowspec_vpn, dev_v26_1)[/dim]")
        console.print("[dim]Do NOT include build number like '#8-' prefix[/dim]")
        branch = Prompt.ask("Branch name [B to cancel]")
        if not branch or branch.lower() == 'b':
            return
    
    console.print(f"\n[dim]Checking {branch}...[/dim]")
    
    try:
        build = jenkins.get_build_info(branch)
        
        if not build:
            console.print(f"[yellow]No builds found for {branch}[/yellow]")
            console.print("[dim]Note: Branch name should NOT include build number (e.g., use 'feature/dev_v26_1/flowspec_vpn' not '#8-feature/...').[/dim]")
            
            console.print("\n  [Y] Yes - Trigger a new build")
            console.print("  [N] No - Go back")
            console.print("  [B] Back to menu")
            trigger_choice = Prompt.ask("Trigger new build?", choices=["y", "Y", "n", "N", "b", "B"], default="n").lower()
            
            if trigger_choice == "y":
                with_baseos = Confirm.ask("Build with BaseOS containers?", default=True)
                qa_version = Confirm.ask("QA version (60-day retention)?", default=False)
                
                success, message = jenkins.trigger_build(branch, with_baseos=with_baseos, qa_version=qa_version)
                if success:
                    console.print(f"[green]✓ {message}[/green]")
                else:
                    console.print(f"[red]✗ {message}[/red]")
            return
        
        # Show current build status
        console.print(f"\n[bold]Build #{build.build_number} for {branch}[/bold]")
        
        if build.building:
            console.print(f"[yellow]🔄 Status: BUILDING[/yellow]")
            
            # Calculate estimated time
            elapsed_min = build.age_hours * 60
            total_estimate_min = 45  # Typical build time
            remaining_min = max(0, total_estimate_min - elapsed_min)
            progress_pct = min(95, int((elapsed_min / total_estimate_min) * 100))
            
            console.print(f"  Elapsed: {int(elapsed_min)} minutes")
            console.print(f"  Estimated remaining: ~{int(remaining_min)} minutes")
            console.print(f"  Progress: ~{progress_pct}%")
            
            # Progress bar
            bar_width = 40
            filled = int(bar_width * progress_pct / 100)
            bar = '█' * filled + '░' * (bar_width - filled)
            console.print(f"  [{bar}] {progress_pct}%")
            
            console.print(f"\n[cyan]Jenkins URL: {build.url}[/cyan]")
            
            if Confirm.ask("\nMonitor until completion?", default=True):
                console.print("\n[yellow]Monitoring build progress...[/yellow]")
                console.print("[dim]Press Ctrl+C to stop monitoring (build continues in Jenkins)[/dim]\n")
                
                from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("{task.fields[eta]}"),
                    TimeElapsedColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task(f"Building {branch}...", total=100, eta="Calculating...")
                    
                    try:
                        while True:
                            build = jenkins.get_build_info(branch, build.build_number)
                            if not build:
                                break
                            
                            if not build.building:
                                # Build finished!
                                progress.update(task, completed=100, description=f"Build #{build.build_number}")
                                break
                            
                            elapsed_min = build.age_hours * 60
                            remaining_min = max(0, total_estimate_min - elapsed_min)
                            progress_pct = min(95, int((elapsed_min / total_estimate_min) * 100))
                            
                            progress.update(
                                task, 
                                completed=progress_pct,
                                description=f"Building {branch} #{build.build_number}",
                                eta=f"~{int(remaining_min)}m remaining"
                            )
                            
                            time.sleep(30)
                            
                    except KeyboardInterrupt:
                        console.print("\n[yellow]Stopped monitoring. Build continues in Jenkins.[/yellow]")
                        return
                
                # Build finished - show result
                if build.result == "SUCCESS":
                    console.print(f"\n[green]✓ Build #{build.build_number} COMPLETED SUCCESSFULLY![/green]")
                    urls = jenkins.get_stack_urls(branch, build.build_number)
                    console.print(f"  DNOS: {'✓' if urls.get('dnos') else '✗'}")
                    console.print(f"  GI: {'✓' if urls.get('gi') else '✗'}")
                    console.print(f"  BaseOS: {'✓' if urls.get('baseos') else '✗'}")
                    
                    if Confirm.ask("\nContinue with upgrade using this build?", default=True):
                        return {
                            'branch': branch,
                            'build': build.build_number,
                            'dnos_url': urls.get('dnos'),
                            'gi_url': urls.get('gi'),
                            'baseos_url': urls.get('baseos'),
                        }
                else:
                    console.print(f"\n[red]✗ Build #{build.build_number} {build.result}[/red]")
        
        else:
            # Build already completed
            status_icon = "✅" if build.result == "SUCCESS" else "❌"
            console.print(f"{status_icon} Status: {build.result}")
            console.print(f"  Completed: {build.age_hours:.1f} hours ago")
            console.print(f"  URL: {build.url}")
            
            if build.result == "SUCCESS":
                urls = jenkins.get_stack_urls(branch, build.build_number)
                has_dnos = urls.get('dnos') and urls.get('dnos') != 'N/A'
                has_gi = urls.get('gi') and urls.get('gi') != 'N/A'
                
                console.print(f"\n[bold]Artifacts:[/bold]")
                console.print(f"  DNOS: {'✓ Available' if has_dnos else '✗ N/A'}")
                console.print(f"  GI: {'✓ Available' if has_gi else '✗ N/A'}")
                console.print(f"  BaseOS: {'✓' if urls.get('baseos') else '✗ N/A'}")
                
                if build.is_expired:
                    console.print(f"\n[yellow]⚠ Build is expired ({build.age_hours:.0f}h old) - artifacts may be unavailable[/yellow]")
                
                if (has_dnos or has_gi) and Confirm.ask("\nContinue with upgrade using this build?", default=True):
                    return {
                        'branch': branch,
                        'build': build.build_number,
                        'dnos_url': urls.get('dnos'),
                        'gi_url': urls.get('gi'),
                        'baseos_url': urls.get('baseos'),
                    }
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    
    Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")
    return None


def _restore_pre_delete_configs(multi_ctx: 'MultiDeviceContext'):
    """Restore configurations that were backed up before system delete."""
    from pathlib import Path
    from rich.table import Table as RichTable
    from rich.prompt import Confirm
    
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]           📦 Restore Pre-Delete Configuration                      [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════════[/bold cyan]")
    
    # Find backup files for each device
    backup_info = {}
    
    for dev in multi_ctx.devices:
        device_dir = Path(f"db/configs/{dev.hostname}")
        op_file = device_dir / "operational.json"
        
        # Check operational.json for backup path
        saved_backup = None
        if op_file.exists():
            try:
                with open(op_file) as f:
                    op_data = json.load(f)
                    saved_backup = op_data.get('pre_delete_backup')
            except:
                pass
        
        # Find all backup files (pre_delete and pre_upgrade)
        backup_files = list(device_dir.glob("pre_delete_backup_*.txt")) + list(device_dir.glob("pre_upgrade_backup_*.txt"))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        if backup_files:
            newest = backup_files[0]
            with open(newest) as f:
                lines = len(f.readlines())
            backup_info[dev.hostname] = {
                'device': dev,
                'backup_path': newest,
                'lines': lines,
                'age': (time.time() - newest.stat().st_mtime) / 3600  # Hours
            }
        elif saved_backup and Path(saved_backup).exists():
            with open(saved_backup) as f:
                lines = len(f.readlines())
            backup_info[dev.hostname] = {
                'device': dev,
                'backup_path': Path(saved_backup),
                'lines': lines,
                'age': (time.time() - Path(saved_backup).stat().st_mtime) / 3600
            }
    
    if not backup_info:
        console.print("\n[yellow]⚠ No pre-delete backup files found for any device.[/yellow]")
        console.print("[dim]Backups are created when using major version upgrades with system delete.[/dim]")
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
        return
    
    # Show available backups
    console.print("\n[bold]Available Pre-Delete Backups:[/bold]\n")
    
    table = RichTable(box=box.ROUNDED)
    table.add_column("#", style="dim")
    table.add_column("Device", style="cyan")
    table.add_column("Backup File", style="green")
    table.add_column("Lines", justify="right")
    table.add_column("Age", justify="right")
    table.add_column("Status")
    
    for i, (hostname, info) in enumerate(backup_info.items(), 1):
        age_str = f"{info['age']:.1f}h ago"
        
        # Check if device is online
        status = "[dim]Unknown[/dim]"
        try:
            import paramiko
            
            password = info['device'].password
            if password:
                import base64
                try:
                    password = base64.b64decode(password).decode('utf-8')
                except:
                    pass
            
            _status_creds = [
                (info['device'].username or 'dnroot', password),
                ('dnroot', 'dnroot'),
                ('dn', 'drivenets'),
            ]
            _status_seen = set()
            _status_unique = []
            for _su, _sp in _status_creds:
                _sk = f"{_su}:{_sp}"
                if _sk not in _status_seen:
                    _status_seen.add(_sk)
                    _status_unique.append((_su, _sp))
            
            _status_ok = False
            for _su, _sp in _status_unique:
                try:
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(info['device'].ip, username=_su,
                               password=_sp, timeout=5,
                               allow_agent=False, look_for_keys=False)
                    
                    channel = ssh.invoke_shell()
                    channel.settimeout(3)
                    time.sleep(0.5)
                    output = channel.recv(10000).decode(errors='ignore')
                    channel.close()
                    ssh.close()
                    
                    if 'GI(' in output or 'GI#' in output:
                        status = "[yellow]GI Mode[/yellow]"
                    else:
                        status = "[green]DNOS OK[/green]"
                    _status_ok = True
                    break
                except paramiko.AuthenticationException:
                    continue
                except Exception:
                    break
            if not _status_ok:
                status = "[red]Offline[/red]"
        except:
            status = "[red]Offline[/red]"
        
        table.add_row(
            str(i),
            hostname,
            str(info['backup_path'].name),
            f"{info['lines']:,}",
            age_str,
            status
        )
    
    console.print(table)
    
    # Options
    console.print("\n[bold]Options:[/bold]")
    console.print("  [A] Push ALL backups to devices (parallel)")
    console.print("  [1-9] Push specific device backup")
    console.print("  [P] Preview a backup file")
    console.print("  [B] Back")
    
    choice = Prompt.ask("Select", default="b").lower()
    
    if choice == "b":
        return
    
    elif choice == "p":
        # Preview
        if len(backup_info) == 1:
            hostname = list(backup_info.keys())[0]
        else:
            preview_num = Prompt.ask("Which device to preview? [1-9]", default="1")
            try:
                hostname = list(backup_info.keys())[int(preview_num) - 1]
            except:
                console.print("[red]Invalid selection[/red]")
                return
        
        info = backup_info[hostname]
        console.print(f"\n[bold]Preview: {hostname} ({info['backup_path'].name})[/bold]")
        console.print("[dim]First 50 lines:[/dim]\n")
        
        with open(info['backup_path']) as f:
            for i, line in enumerate(f):
                if i >= 50:
                    console.print("[dim]... truncated ...[/dim]")
                    break
                console.print(f"[dim]{line.rstrip()}[/dim]")
        
        Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")
        return _restore_pre_delete_configs(multi_ctx)
    
    elif choice == "a" or choice.isdigit():
        # Determine which devices to push
        if choice == "a":
            devices_to_push = list(backup_info.keys())
        else:
            try:
                idx = int(choice) - 1
                devices_to_push = [list(backup_info.keys())[idx]]
            except:
                console.print("[red]Invalid selection[/red]")
                return
        
        # Filter to only DNOS-ready devices
        ready_devices = []
        _restore_working_creds = {}
        _known_cred_sets = [
            ('dnroot', 'dnroot'),
            ('dn', 'drivenets'),
            ('admin', 'admin'),
            ('root', 'drivenets'),
        ]
        for hostname in devices_to_push:
            info = backup_info[hostname]
            try:
                import paramiko
                
                password = info['device'].password
                if password:
                    import base64
                    try:
                        password = base64.b64decode(password).decode('utf-8')
                    except:
                        pass
                
                _dev_creds = [(info['device'].username or 'dnroot', password)] + _known_cred_sets
                _seen_rc = set()
                _unique_rc = []
                for _rcu, _rcp in _dev_creds:
                    _rck = f"{_rcu}:{_rcp}"
                    if _rck not in _seen_rc:
                        _seen_rc.add(_rck)
                        _unique_rc.append((_rcu, _rcp))
                
                _connected = False
                for _rcu, _rcp in _unique_rc:
                    try:
                        ssh = paramiko.SSHClient()
                        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh.connect(info['device'].ip, username=_rcu,
                                   password=_rcp, timeout=10,
                                   allow_agent=False, look_for_keys=False)
                        
                        channel = ssh.invoke_shell()
                        channel.settimeout(5)
                        time.sleep(0.5)
                        output = channel.recv(10000).decode(errors='ignore')
                        channel.close()
                        ssh.close()
                        
                        if 'GI(' not in output and 'GI#' not in output:
                            ready_devices.append(hostname)
                            _restore_working_creds[hostname] = (_rcu, _rcp)
                        else:
                            console.print(f"[yellow]-- {hostname}: Still in GI mode - skipping[/yellow]")
                        _connected = True
                        break
                    except paramiko.AuthenticationException:
                        continue
                    except Exception as e:
                        console.print(f"[red]x {hostname}: Cannot connect - {str(e)[:30]}[/red]")
                        break
                if not _connected:
                    console.print(f"[red]x {hostname}: Authentication failed with all credential sets[/red]")
            except Exception as e:
                console.print(f"[red]x {hostname}: Cannot connect - {str(e)[:30]}[/red]")
        
        if not ready_devices:
            console.print("\n[red]No devices are ready for config push.[/red]")
            console.print("[dim]Wait for devices to complete DNOS install and try again.[/dim]")
            Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
            return
        
        # Confirm push
        console.print(f"\n[bold]Ready to push config to {len(ready_devices)} device(s):[/bold]")
        for hostname in ready_devices:
            info = backup_info[hostname]
            console.print(f"  • {hostname}: {info['lines']:,} lines from {info['backup_path'].name}")
        
        if not Confirm.ask("\nPush configurations?", default=True):
            return
        
        # Push configs
        from .config_pusher import ConfigPusher
        
        console.print("\n[bold cyan]Pushing configurations...[/bold cyan]\n")
        
        for hostname in ready_devices:
            info = backup_info[hostname]
            dev = info['device']
            
            console.print(f"[cyan]Pushing to {hostname}...[/cyan]")
            
            try:
                with open(info['backup_path']) as f:
                    config_text = f.read()
                
                _lines_r = [l for l in config_text.strip().split('\n') if not l.startswith('#')]
                _cfg_no_comments_r = '\n'.join(_lines_r)
                _src_ver_r = ''
                _tgt_ver_r = ''
                try:
                    _op_r = Path(f"db/configs/{hostname}/operational.json")
                    if _op_r.exists():
                        with open(_op_r) as _fr:
                            _opd_r = json.load(_fr)
                        _tgt_ver_r = _opd_r.get('dnos_version', '')
                        _src_ver_r = _opd_r.get('pre_upgrade_version', '')
                except Exception:
                    pass
                _cfg_clean_r, _stripped_items_r = sanitize_config_for_version(
                    _cfg_no_comments_r, source_version=_src_ver_r, target_version=_tgt_ver_r)
                if _stripped_items_r:
                    console.print(f"  [dim]Sanitized: removed {len(_stripped_items_r)} version-incompatible items[/dim]")
                    for _si in _stripped_items_r[:5]:
                        console.print(f"    [dim]- {_si}[/dim]")
                    if len(_stripped_items_r) > 5:
                        console.print(f"    [dim]... and {len(_stripped_items_r) - 5} more[/dim]")
                
                pusher = ConfigPusher()
                
                _orig_u = dev.username
                _orig_p = dev.password
                _wc = _restore_working_creds.get(hostname)
                if _wc:
                    dev.username = _wc[0]
                    dev.password = Device.encode_password(_wc[1])
                
                success, message = pusher.push_config(
                    dev, _cfg_clean_r,
                    config_name=f"manual_restore_{hostname}"
                )
                
                dev.username = _orig_u
                dev.password = _orig_p
                
                if success:
                    console.print(f"  [green]OK {hostname}: Config pushed successfully[/green]")
                    
                    try:
                        op_file = Path(f"db/configs/{hostname}/operational.json")
                        if op_file.exists():
                            with open(op_file) as f:
                                op_data = json.load(f)
                            op_data.pop('pre_delete_backup', None)
                            op_data.pop('pre_delete_backup_time', None)
                            op_data['config_restored'] = time.strftime("%Y-%m-%d %H:%M:%S")
                            with open(op_file, 'w') as f:
                                json.dump(op_data, f, indent=4)
                    except:
                        pass
                else:
                    console.print(f"  [red]x {hostname}: {message}[/red]")
                    
            except Exception as e:
                console.print(f"  [red]x {hostname}: Error - {str(e)[:40]}[/red]")
        
        console.print("\n[bold]Configuration restore complete![/bold]")
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")


def _diagnose_device_recovery(device: 'Device'):
    """Comprehensive diagnostic for a device in RECOVERY mode."""
    import paramiko
    from rich.panel import Panel
    from rich.syntax import Syntax
    
    console.print(f"\n[bold red]🔍 Diagnosing {device.hostname} (RECOVERY Mode)[/bold red]")
    console.print(f"[dim]Connecting to {device.ip}...[/dim]\n")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        password = device.password
        if hasattr(device, 'password') and device.password:
            import base64
            try:
                password = base64.b64decode(device.password).decode('utf-8')
            except:
                password = device.password
        
        ssh.connect(device.ip, username=device.username or 'dnroot', password=password, timeout=10,
                    allow_agent=False, look_for_keys=False)
        channel = ssh.invoke_shell()
        channel.settimeout(8)
        time.sleep(0.5)
        initial_output = channel.recv(10000).decode(errors='ignore')
        
        # Check if actually in recovery mode
        is_recovery = 'RECOVERY' in initial_output or 'dnRouter(RECOVERY)' in initial_output
        if not is_recovery:
            console.print("[yellow]⚠ Device is not in RECOVERY mode[/yellow]")
            ssh.close()
            return
        
        console.print("[bold red]✓ Confirmed: Device is in RECOVERY mode[/bold red]\n")
        
        diagnostics = {}
        
        # RECOVERY mode has limited commands - try basic ones
        console.print("[cyan]1. Checking Available Commands...[/cyan]")
        channel.send("help\n")
        time.sleep(1)
        help_output = ""
        while channel.recv_ready():
            help_output += channel.recv(65535).decode(errors='ignore')
        diagnostics['help'] = help_output
        
        # Try to get system info if available
        console.print("[cyan]2. Checking System Info...[/cyan]")
        channel.send("show version\n")
        time.sleep(1)
        version_output = ""
        while channel.recv_ready():
            version_output += channel.recv(65535).decode(errors='ignore')
        diagnostics['version'] = version_output
        
        # Try show system (might work)
        console.print("[cyan]3. Checking System Status...[/cyan]")
        channel.send("show system\n")
        time.sleep(1)
        system_output = ""
        while channel.recv_ready():
            system_output += channel.recv(65535).decode(errors='ignore')
        diagnostics['system'] = system_output
        
        # Try to see what's available
        console.print("[cyan]4. Checking Boot/Recovery Info...[/cyan]")
        channel.send("?\n")
        time.sleep(0.5)
        cmd_list = ""
        while channel.recv_ready():
            cmd_list += channel.recv(65535).decode(errors='ignore')
        diagnostics['commands'] = cmd_list
        
        ssh.close()
        
        # Display diagnostics
        console.print("\n[bold]═══════════════════════════════════════════════════════════[/bold]")
        console.print("[bold]DIAGNOSTIC RESULTS (RECOVERY MODE)[/bold]")
        console.print("[bold]═══════════════════════════════════════════════════════════[/bold]\n")
        
        # Available Commands
        if diagnostics.get('help'):
            console.print(Panel(
                diagnostics.get('help', 'N/A'),
                title="[bold]Available Commands (help)[/bold]",
                border_style="cyan"
            ))
        
        # Version Info
        if diagnostics.get('version'):
            console.print(Panel(
                diagnostics.get('version', 'N/A'),
                title="[bold]Version Information[/bold]",
                border_style="yellow"
            ))
        
        # System Status
        if diagnostics.get('system'):
            console.print(Panel(
                diagnostics.get('system', 'N/A'),
                title="[bold]System Status[/bold]",
                border_style="magenta"
            ))
        
        # Command List
        if diagnostics.get('commands'):
            console.print(Panel(
                diagnostics.get('commands', 'N/A'),
                title="[bold]Available Commands[/bold]",
                border_style="blue"
            ))
        
        # Analysis
        console.print("\n[bold yellow]📋 ANALYSIS:[/bold yellow]")
        console.print("\n[bold red]⚠ CRITICAL: Device is in RECOVERY mode[/bold red]")
        console.print("This means the device failed to boot with the new image and")
        console.print("fell back to a recovery/fallback image.\n")
        
        console.print("[bold]LIKELY CAUSES:[/bold]")
        console.print("  1. Corrupted image download (network interruption)")
        console.print("  2. Image incompatibility with hardware")
        console.print("  3. Installation failure (device rebooted before install completed)")
        console.print("  4. Boot failure (new image failed to initialize)")
        console.print("  5. Hardware/driver compatibility issue\n")
        
        console.print("[bold]RECOMMENDED ACTIONS:[/bold]")
        console.print("  1. [yellow]Check recovery mode commands above for rollback options[/yellow]")
        console.print("  2. [yellow]Try: 'request system rollback' or similar recovery commands[/yellow]")
        console.print("  3. [yellow]If rollback available, restore to previous working image[/yellow]")
        console.print("  4. [yellow]Retry upgrade with validated image (validation now enabled)[/yellow]")
        console.print("  5. [yellow]Contact support if hardware issue suspected[/yellow]")
        console.print()
        console.print("[dim]Note: RECOVERY mode has limited commands. Standard DNOS commands")
        console.print("may not be available. Use recovery-specific commands shown above.[/dim]")
        
    except Exception as e:
        from rich.text import Text
        error_msg = str(e)
        console.print("\n[bold red]✗ Connection failed[/bold red]")
        console.print(Text(error_msg, style="red"))
        console.print("[yellow]Device may be unreachable or SSH service not responding.[/yellow]")


def _verify_device_stacks_live(multi_ctx: 'MultiDeviceContext') -> dict:
    """
    SSH to devices in PARALLEL to verify current stack versions.
    Uses ThreadPoolExecutor for concurrent connections (much faster than sequential).
    """
    import paramiko
    import socket
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from rich.panel import Panel as RichPanel
    from .connection_strategy import CREDENTIAL_SETS, DeviceState
    
    num_devs = len(multi_ctx.devices)
    console.print(f"[dim]  Connecting to {num_devs} device(s) in parallel...[/dim]")
    
    device_results = {}
    
    def _verify_one(device):
        """Per-device SSH + stack check. Runs in its own thread."""
        hostname = device.hostname
        result = {
            'state': None,
            'dnos': 'N/A',
            'gi': 'N/A', 
            'baseos': 'N/A',
            'target_dnos': 'N/A',
            'channel': None,
            'ssh': None,
            'connection_method': None,
            'error': None
        }
        
        # Get serial number and stored mgmt_ip from operational.json
        serial_number = None
        stored_mgmt_ip = None
        try:
            op_file = Path(f"/home/dn/SCALER/db/configs/{hostname}/operational.json")
            if op_file.exists():
                with open(op_file) as f:
                    op_data = json.load(f)
                    sn = op_data.get('serial_number')
                    if sn and sn != 'N/A':
                        serial_number = sn
                    mgmt = op_data.get('mgmt_ip')
                    if mgmt and mgmt != 'N/A':
                        stored_mgmt_ip = mgmt
        except:
            pass
        
        # Build connection targets in priority order
        connection_targets = []
        
        # 1. SSH to serial number hostname (fastest - direct DNS)
        if serial_number:
            connection_targets.append(('SSH→SN', serial_number))
        
        # 2. SSH to stored management IP (from previous GI mode connection)
        if stored_mgmt_ip:
            connection_targets.append(('SSH→MGMT', stored_mgmt_ip))
        
        # 3. SSH to device.ip if different from stored
        if device.ip and device.ip != stored_mgmt_ip:
            connection_targets.append(('SSH→MGMT', device.ip))
        
        # 4. Console (handled separately below if SSH fails)
        
        # 5. SSH to loopback if known
        if hasattr(device, 'loopback_ip') and device.loopback_ip:
            connection_targets.append(('SSH→LO', device.loopback_ip))
        
        connected = False
        ssh = None
        channel = None
        connection_method = None
        
        # Try each SSH target with multiple credentials
        for method_name, target in connection_targets:
            for cred in CREDENTIAL_SETS:
                try:
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(
                        target,
                        username=cred['username'],
                        password=cred['password'],
                        timeout=10,
                        banner_timeout=10,
                        auth_timeout=10,
                        allow_agent=False,
                        look_for_keys=False
                    )
                    connected = True
                    connection_method = f"{method_name} ({cred['username']})"
                    break
                except paramiko.AuthenticationException:
                    continue  # Try next credential
                except socket.timeout:
                    break  # Timeout means host unreachable, try next target
                except socket.gaierror:
                    break  # DNS failure, try next target
                except Exception:
                    continue
            
            if connected:
                break
        
        # If SSH failed, try console
        if not connected:
            try:
                from .connection_strategy import get_console_config_for_device
                console_cfg = get_console_config_for_device(hostname)
                if console_cfg:
                    console_ssh = paramiko.SSHClient()
                    console_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    console_ssh.connect(
                        console_cfg['host'],
                        username=console_cfg['user'],
                        password=console_cfg['password'],
                        timeout=15
                    )
                    console_channel = console_ssh.invoke_shell(width=200, height=50)
                    console_channel.settimeout(30)
                    time.sleep(1.5)
                    _ = console_channel.recv(8192)
                    
                    # Navigate to device port
                    console_channel.send("3\r\n")
                    time.sleep(3)
                    _ = console_channel.recv(8192)
                    console_channel.send(f"{console_cfg['port']}\r\n")
                    time.sleep(1.5)
                    console_channel.send("\r\n")
                    time.sleep(2)
                    output = console_channel.recv(8192).decode('utf-8', errors='replace')
                    
                    # Try login with all credentials
                    console_cred = None
                    output_lower = output.lower()
                    
                    # Check if already at a prompt (GI#, root@, etc.)
                    if 'gi#' in output_lower or 'gi(' in output_lower or '@' in output_lower and '$' in output_lower:
                        console_cred = CREDENTIAL_SETS[0]  # Already logged in
                    elif "login" in output_lower or "password" in output_lower:
                        for cred in CREDENTIAL_SETS:
                            console_channel.send(cred['username'] + "\r\n")
                            time.sleep(1)
                            console_channel.send(cred['password'] + "\r\n")
                            time.sleep(3)
                            new_out = console_channel.recv(8192).decode('utf-8', errors='replace')
                            output += new_out
                            if "incorrect" not in new_out.lower() and "denied" not in new_out.lower():
                                console_cred = cred
                                break
                    else:
                        # Unknown state, try sending newlines
                        console_channel.send("\r\n\r\n")
                        time.sleep(2)
                        new_out = console_channel.recv(8192).decode('utf-8', errors='replace')
                        if 'gi#' in new_out.lower() or '#' in new_out or '$' in new_out:
                            console_cred = CREDENTIAL_SETS[0]
                    
                    if console_cred:
                        # Get management IP from console to switch to SSH
                        console_channel.send("\r\n")
                        time.sleep(1)
                        console_channel.send("show interfaces management | no-more\r\n")
                        time.sleep(4)  # Give more time for GI mode
                        
                        mgmt_output = ""
                        try:
                            for _ in range(5):  # Try multiple reads
                                if console_channel.recv_ready():
                                    mgmt_output += console_channel.recv(8192).decode('utf-8', errors='replace')
                                time.sleep(0.5)
                        except:
                            pass
                        
                        # Parse management IP from output
                        # In GI mode, look for IP in various formats
                        mgmt_ip = None
                        for line in mgmt_output.split('\n'):
                            line_lower = line.lower()
                            # Look for mgmt interface lines or IP addresses
                            if 'mgmt' in line_lower or 'management' in line_lower:
                                # Extract IP address pattern
                                ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                                if ip_match:
                                    potential_ip = ip_match.group(1)
                                    # Skip localhost/loopback and broadcast
                                    if not potential_ip.startswith('127.') and not potential_ip.endswith('.255'):
                                        mgmt_ip = potential_ip
                                        break
                        
                        # Also try to find IP in any line with IPv4 pattern
                        if not mgmt_ip:
                            for line in mgmt_output.split('\n'):
                                if 'inet ' in line or 'address' in line.lower():
                                    ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                                    if ip_match:
                                        potential_ip = ip_match.group(1)
                                        if not potential_ip.startswith('127.') and not potential_ip.endswith('.255'):
                                            mgmt_ip = potential_ip
                                            break
                        
                        # If we got a management IP, save it and try SSH
                        if mgmt_ip:
                            # Save mgmt_ip to operational.json
                            try:
                                op_path = Path(f"/home/dn/SCALER/db/configs/{hostname}/operational.json")
                                if op_path.exists():
                                    with open(op_path, 'r') as f:
                                        op_data_temp = json.load(f)
                                    op_data_temp['mgmt_ip'] = mgmt_ip
                                    with open(op_path, 'w') as f:
                                        json.dump(op_data_temp, f, indent=4)
                            except:
                                pass
                            
                            # Close console connection
                            try:
                                console_channel.close()
                                console_ssh.close()
                            except:
                                pass
                            
                            # Try SSH to management IP with multiple credentials
                            for cred in CREDENTIAL_SETS:
                                try:
                                    ssh = paramiko.SSHClient()
                                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                                    ssh.connect(
                                        mgmt_ip,
                                        username=cred['username'],
                                        password=cred['password'],
                                        timeout=10,
                                        banner_timeout=10,
                                        auth_timeout=10,
                                        allow_agent=False,
                                        look_for_keys=False
                                    )
                                    connected = True
                                    connection_method = f"SSH→MGMT ({mgmt_ip})"
                                    break
                                except paramiko.AuthenticationException:
                                    return hostname, result, "[red]Unreachable[/red]", "-"
                                except Exception:
                                    break  # Network error, don't try more creds
                        
                        # If SSH to mgmt IP failed or no mgmt IP, use console directly
                        if not connected:
                            # Already have console_channel open, just use it
                            if console_cred:
                                ssh = console_ssh
                                channel = console_channel
                                connected = True
                                connection_method = f"Console ({console_cred['username']})"
                            else:
                                # No credential worked, report error
                                result['error'] = "Console login failed"
                        else:
                            channel = None  # Will create new channel below
            except Exception as e:
                result['error'] = f"Console: {str(e)[:30]}"
        
        if not connected:
            try:
                from .connection_strategy import connect_for_upgrade
                conn = connect_for_upgrade(hostname, timeout=30)
                if conn['connected']:
                    ssh = conn['ssh']
                    channel = conn['channel']
                    connected = True
                    connection_method = conn.get('method', 'DeviceConnector')
            except Exception:
                pass
        
        if not connected:
            result['error'] = result.get('error') or "All connection methods failed"
            return hostname, result, "[red]Unreachable[/red]", "-"
        
        # Get interactive shell if not from console
        if not channel:
            channel = ssh.invoke_shell(width=200, height=50)
            channel.settimeout(20)
            time.sleep(1)
            _ = channel.recv(10000)
        
        # Send multiple newlines to get a fresh prompt (important for console)
        channel.send("\r\n\r\n")
        time.sleep(2)
        
        # Collect all output
        prompt_output = ""
        try:
            while channel.recv_ready():
                prompt_output += channel.recv(8192).decode('utf-8', errors='replace')
                time.sleep(0.3)
        except:
            pass
        
        # If still empty, try one more time
        if not prompt_output.strip():
            channel.send("\r\n")
            time.sleep(2)
            try:
                while channel.recv_ready():
                    prompt_output += channel.recv(8192).decode('utf-8', errors='replace')
                    time.sleep(0.3)
            except:
                pass
        
        # CRITICAL: Multi-layer device verification before sending any commands
        from .utils import verify_device_hostname, post_connect_verify, sync_device_from_live
        host_ok, actual_host = verify_device_hostname(prompt_output, hostname)
        if not host_ok:
            result['error'] = f"WRONG DEVICE: prompt shows '{actual_host}', expected '{hostname}'"
            result['state'] = DeviceState.UNKNOWN
            try:
                ssh.close()
            except:
                pass
            return hostname, result, f"[bold red]⛔ WRONG DEVICE ({actual_host})[/bold red]", "-"
        
        # Layer 2-3: Deep verification + live IP extraction + DB sync
        if actual_host not in ('GI', 'UNKNOWN'):
            verify_result = post_connect_verify(
                channel, hostname, prompt_output=prompt_output, run_show_system=True
            )
            if verify_result.get('abort_reason'):
                result['error'] = verify_result['abort_reason']
                result['state'] = DeviceState.UNKNOWN
                try:
                    ssh.close()
                except:
                    pass
                return hostname, result, f"[bold red]⛔ {verify_result['abort_reason'][:40]}[/bold red]", "-"
            
            # Sync DB with verified live data
            db_changes = sync_device_from_live(hostname, verify_result)
            if db_changes:
                result['db_synced'] = db_changes
        elif actual_host == 'GI':
            # GI mode: verify serial number from show system stack
            from .utils import verify_gi_serial
            gi_verify = verify_gi_serial(channel, hostname)
            if gi_verify.get('abort_reason'):
                result['error'] = gi_verify['abort_reason']
                result['state'] = DeviceState.UNKNOWN
                try:
                    ssh.close()
                except:
                    pass
                return hostname, result, f"[bold red]⛔ GI SERIAL MISMATCH[/bold red]", "-"
        
        # Detect device state from prompt
        lower_prompt = prompt_output.lower()
        import re
        
        # More robust state detection patterns
        # GI mode: GI#, GI>, GI(timestamp)#, etc.
        gi_pattern = r'gi\s*[#>]|gi\([^)]*\)\s*[#>]|^gi\s*$'
        # BaseOS shell: dn@WKY...:~$ or root@hostname:~$
        baseos_pattern = r'(dn|root)@[a-zA-Z0-9_-]+:\s*~?\s*\$'
        # ONIE: ONIE:/ # or similar
        onie_pattern = r'onie[:\-/]|onie\s*#'
        # DNOS: PE-1#, router#, hostname# (but NOT GI#)
        dnos_pattern = r'[a-zA-Z][a-zA-Z0-9_-]*[#>]\s*$'
        
        if re.search(gi_pattern, lower_prompt, re.MULTILINE | re.IGNORECASE):
            result['state'] = DeviceState.GI
            state_display = "[cyan]GI Mode[/cyan]"
        elif re.search(baseos_pattern, prompt_output, re.MULTILINE):
            result['state'] = DeviceState.BASEOS_SHELL
            state_display = "[yellow]BaseOS Shell[/yellow]"
        elif re.search(onie_pattern, lower_prompt, re.IGNORECASE):
            result['state'] = DeviceState.ONIE
            state_display = "[red]ONIE[/red]"
        elif "recovery" in lower_prompt or "dn-recovery" in lower_prompt:
            result['state'] = DeviceState.DN_RECOVERY
            state_display = "[red]DN Recovery[/red]"
        elif re.search(dnos_pattern, lower_prompt, re.MULTILINE) and 'gi' not in lower_prompt:
            result['state'] = DeviceState.DNOS
            state_display = "[green]DNOS[/green]"
        else:
            # Try to detect from commands - send show system stack to see if it works
            result['state'] = DeviceState.UNKNOWN
            state_display = "[yellow]Unknown[/yellow]"
        
        # Always get stack information - works in both GI and DNOS mode
        # Run 'show system stack | no-more' to get versions
        channel.send("show system stack | no-more\r\n")
        time.sleep(3)  # Give more time for console
        
        stack_output = ""
        try:
            while channel.recv_ready():
                stack_output += channel.recv(65535).decode(errors='ignore')
                time.sleep(0.3)
        except:
            pass
        
        # If we still don't know state, try to detect from command output
        if result['state'] == DeviceState.UNKNOWN or result['state'] is None:
            # Check if we got a valid response
            stack_lower = stack_output.lower()
            if 'component' in stack_lower or 'dnos' in stack_lower:
                # Command worked - likely GI or DNOS
                if 'gi#' in stack_lower or 'gi(' in stack_lower:
                    result['state'] = DeviceState.GI
                    state_display = "[cyan]GI Mode[/cyan]"
                else:
                    result['state'] = DeviceState.DNOS
                    state_display = "[green]DNOS[/green]"
            elif 'error' in stack_lower or 'unknown' in stack_lower:
                # Command failed - might be in different mode
                if 'dn@' in stack_output or ':~$' in stack_output:
                    result['state'] = DeviceState.BASEOS_SHELL
                    state_display = "[yellow]BaseOS Shell[/yellow]"
        
        # Parse: | Component | HW Model | HW Revision | Revert | Current | Target |
        for line in stack_output.split('\n'):
            if '|' in line and '---' not in line and 'Component' not in line:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 5:
                    component = parts[0].upper()
                    # Current is column 4 (index 4), Target is column 5 (index 5)
                    current = parts[4] if len(parts) > 4 and parts[4] not in ('-', '') else 'N/A'
                    target = parts[5] if len(parts) > 5 and parts[5] not in ('-', '') else 'N/A'
                    
                    if component == 'DNOS':
                        result['dnos'] = current if current != 'N/A' else '-'
                        result['target_dnos'] = target if target != 'N/A' else '-'
                    elif component == 'GI':
                        result['gi'] = current if current != 'N/A' else '-'
                        result['target_gi'] = target if target != 'N/A' else '-'
                    elif component == 'BASEOS':
                        result['baseos'] = current if current != 'N/A' else '-'
                        result['target_baseos'] = target if target != 'N/A' else '-'
        
        # Update operational.json with detected state
        try:
            op_path = Path(f"/home/dn/SCALER/db/configs/{hostname}/operational.json")
            op_data = {}
            if op_path.exists():
                with open(op_path, 'r') as f:
                    op_data = json.load(f)
            
            # Update state fields
            is_recovery = result['state'] in [DeviceState.GI, DeviceState.BASEOS_SHELL, DeviceState.ONIE, DeviceState.DN_RECOVERY]
            op_data['recovery_mode_detected'] = is_recovery
            op_data['recovery_type'] = result['state'].value if result['state'] else ''
            op_data['device_state'] = result['state'].value if result['state'] else 'UNKNOWN'
            op_data['connection_method'] = connection_method if connection_method else 'N/A'
            op_data['last_state_check'] = datetime.now().isoformat()
            
            # Update current version info
            if result['dnos'] not in ('N/A', '-', None):
                op_data['dnos_version'] = result['dnos']
            elif result['state'] == DeviceState.GI:
                op_data['dnos_version'] = 'N/A (GI Mode)'
            
            if result['gi'] not in ('N/A', '-', None):
                op_data['gi_version'] = result['gi']
            if result['baseos'] not in ('N/A', '-', None):
                op_data['baseos_version'] = result['baseos']
            
            # Update target version info (staged stacks ready to deploy)
            if result.get('target_dnos') not in ('N/A', '-', None):
                op_data['target_dnos_version'] = result['target_dnos']
            if result.get('target_gi') not in ('N/A', '-', None):
                op_data['target_gi_version'] = result['target_gi']
            if result.get('target_baseos') not in ('N/A', '-', None):
                op_data['target_baseos_version'] = result['target_baseos']
            
            op_path.parent.mkdir(parents=True, exist_ok=True)
            with open(op_path, 'w') as f:
                json.dump(op_data, f, indent=4)
            
            # Update running.txt header for recovery mode devices
            if is_recovery:
                try:
                    from .config_extractor import update_recovery_mode_header
                    update_recovery_mode_header(hostname)
                except Exception:
                    pass
        except Exception:
            pass  # Don't fail on write errors
        
        # Store channel and ssh for potential follow-up actions
        result['channel'] = channel
        result['ssh'] = ssh
        result['connection_method'] = connection_method

        return hostname, result, state_display, connection_method
    
    # Execute all device verifications in parallel
    with ThreadPoolExecutor(max_workers=min(num_devs, 8)) as pool:
        futures = {pool.submit(_verify_one, dev): dev for dev in multi_ctx.devices}
        for future in as_completed(futures):
            try:
                hostname, result, state_display, conn_method = future.result()
                device_results[hostname] = result
            except Exception as e:
                dev = futures[future]
                device_results[dev.hostname] = {
                    'state': None, 'dnos': 'N/A', 'gi': 'N/A', 'baseos': 'N/A',
                    'target_dnos': 'N/A', 'target_gi': '-', 'target_baseos': '-',
                    'error': str(e)[:50]
                }
    
    # Display panels in device order (not completion order)
    state_map = {'DNOS': '[green]DNOS[/green]', 'GI': '[cyan]GI[/cyan]',
                 'BASEOS_SHELL': '[yellow]BaseOS[/yellow]', 'ONIE': '[red]ONIE[/red]',
                 'DN_RECOVERY': '[red]Recovery[/red]', 'RECOVERY': '[red]Recovery[/red]',
                 'UNKNOWN': '[yellow]?[/yellow]'}
    
    for device in multi_ctx.devices:
        hostname = device.hostname
        r = device_results.get(hostname, {})
        
        if r.get('error') and r.get('state') is None:
            title = f"[cyan]{hostname}[/cyan] [red]Error[/red]"
            body = f"  [red]{r['error'][:80]}[/red]"
        else:
            state_val = r.get('state')
            sv = state_val.value if hasattr(state_val, 'value') else str(state_val or '?')
            sd = state_map.get(sv, f'[yellow]{sv}[/yellow]')
            conn = r.get('connection_method', '-') or '-'
            title = f"[cyan]{hostname}[/cyan] {sd} [dim]{conn}[/dim]"
            
            lines = []
            for label, cur_k, tgt_k in [('DNOS', 'dnos', 'target_dnos'), ('GI', 'gi', 'target_gi'), ('BaseOS', 'baseos', 'target_baseos')]:
                cur = r.get(cur_k, '-') or '-'
                tgt = r.get(tgt_k, '-') or '-'
                if tgt and tgt != '-':
                    lines.append(f"  [bold]{label:6s}[/bold]  [dim]cur:[/dim] {cur}")
                    lines.append(f"          [dim]tgt:[/dim] [bold yellow]{tgt}[/bold yellow]")
                else:
                    lines.append(f"  [bold]{label:6s}[/bold]  {cur}")
            body = "\n".join(lines)
        
        console.print(RichPanel(body, title=title, title_align="left",
                                border_style="dim", expand=True, padding=(0, 1)))
    
    # Offer follow-up actions based on detected states
    _offer_stack_actions(multi_ctx, device_results)
    
    return device_results




def _offer_stack_actions(multi_ctx: 'MultiDeviceContext', device_results: dict):
    """
    After verifying stacks, offer appropriate actions based on device states.
    
    - GI Mode: Offer to deploy DNOS
    - DNOS Mode: Offer to load new images (target-stack)
    """
    from .connection_strategy import DeviceState
    
    # Categorize devices by state
    gi_devices = [h for h, r in device_results.items() if r.get('state') == DeviceState.GI]
    dnos_devices = [h for h, r in device_results.items() if r.get('state') == DeviceState.DNOS]
    baseos_devices = [h for h, r in device_results.items() if r.get('state') == DeviceState.BASEOS_SHELL]
    unknown_devices = [h for h, r in device_results.items() if r.get('state') in (DeviceState.UNKNOWN, None)]
    
    if not gi_devices and not dnos_devices and not baseos_devices and not unknown_devices:
        console.print("\n[dim]No actionable devices found.[/dim]")
        return
    
    if unknown_devices:
        console.print(f"\n[yellow]⚠ Unknown state for: {', '.join(unknown_devices)}[/yellow]")
        console.print("[dim]Try refreshing or check device manually.[/dim]")
    
    console.print("\n[bold]Available Actions:[/bold]")
    
    options = []
    if gi_devices:
        # Build target images summary for each GI device
        target_images = []
        for h in gi_devices:
            r = device_results.get(h, {})
            dnos_t = r.get('target_dnos', '-')
            gi_t = r.get('gi', '-')
            baseos_t = r.get('baseos', '-')
            if dnos_t not in ('-', 'N/A', None):
                target_images.append(f"{h}: {dnos_t[:20]}")
        
        if target_images:
            console.print(f"  [D] [cyan]System Deploy[/cyan] - Deploy target stacks on {len(gi_devices)} device(s):")
            for img in target_images:
                console.print(f"      └─ {img}")
        else:
            console.print(f"  [D] [cyan]System Deploy[/cyan] - Deploy on {len(gi_devices)} device(s) in GI mode: {', '.join(gi_devices)}")
        options.append('d')
    
    if dnos_devices:
        # Check which DNOS devices have target stacks waiting
        dnos_with_targets = []
        for h in dnos_devices:
            r = device_results.get(h, {})
            tgt = r.get('target_dnos', '-')
            if tgt and tgt not in ('-', 'N/A', None):
                dnos_with_targets.append((h, tgt))
        
        if dnos_with_targets:
            console.print(f"  [I] [bold green]⚡ Install Target Stack[/bold green] - Pre-check + Install on {len(dnos_with_targets)} device(s):")
            for h, tgt in dnos_with_targets:
                console.print(f"      └─ {h}: → {tgt}")
            options.append('i')
        
        console.print(f"  [L] [green]Load Images[/green] - Target-stack load on {len(dnos_devices)} DNOS device(s): {', '.join(dnos_devices)}")
        options.append('l')
    
    if baseos_devices:
        console.print(f"  [G] [yellow]Enter GI Mode[/yellow] - Run dncli on {len(baseos_devices)} BaseOS device(s): {', '.join(baseos_devices)}")
        options.append('g')
    
    console.print("  [B] Back")
    options.append('b')
    
    all_choices = list(set(options + [o.upper() for o in options]))
    choice = Prompt.ask("Select", choices=all_choices, default="b").lower()
    
    if choice == 'b':
        # Close all connections
        for hostname, result in device_results.items():
            try:
                if result.get('channel'):
                    result['channel'].close()
                if result.get('ssh'):
                    result['ssh'].close()
            except:
                pass
        return
    
    elif choice == 'd' and gi_devices:
        _deploy_dnos_on_devices(multi_ctx, device_results, gi_devices)
    
    elif choice == 'i' and dnos_devices:
        # Build targets list from device_results
        install_targets = []
        for h in dnos_devices:
            r = device_results.get(h, {})
            tgt = r.get('target_dnos', '-')
            if tgt and tgt not in ('-', 'N/A', None):
                install_targets.append((h, tgt))
        if install_targets:
            # Close existing connections first (install function opens its own)
            for hostname, result in device_results.items():
                try:
                    if result.get('channel'):
                        result['channel'].close()
                    if result.get('ssh'):
                        result['ssh'].close()
                except:
                    pass
            _install_target_stack_on_devices(multi_ctx, install_targets)
    
    elif choice == 'l' and dnos_devices:
        console.print("\n[cyan]To load new images, go back and select a branch or enter URLs.[/cyan]")
        console.print("[dim]The Image Upgrade wizard will handle target-stack loading.[/dim]")
    
    elif choice == 'g' and baseos_devices:
        _enter_gi_mode_on_devices(multi_ctx, device_results, baseos_devices)
    
    # Close connections after action
    for hostname, result in device_results.items():
        try:
            if result.get('channel'):
                result['channel'].close()
            if result.get('ssh'):
                result['ssh'].close()
        except:
            pass


def _deploy_dnos_on_devices(multi_ctx: 'MultiDeviceContext', device_results: dict, gi_devices: list):
    """System Deploy - Deploy target stacks (DNOS, GI, BaseOS) on devices in GI mode."""
    console.print(f"\n[bold cyan]━━━ System Deploy on {len(gi_devices)} Device(s) ━━━[/bold cyan]")
    
    # Get system type for each device
    for hostname in gi_devices:
        result = device_results.get(hostname)
        if not result or not result.get('channel'):
            console.print(f"[red]{hostname}: No active connection[/red]")
            continue
        
        channel = result['channel']
        
        # Get system type from device or operational.json
        system_type = "SA-36CD-S"  # Default
        try:
            op_file = Path(f"/home/dn/SCALER/db/configs/{hostname}/operational.json")
            if op_file.exists():
                with open(op_file) as f:
                    op_data = json.load(f)
                    st = op_data.get('system_type')
                    if st and st != 'N/A':
                        system_type = st
        except:
            pass
        
        # Ask for confirmation - show target stacks
        console.print(f"\n[cyan]{hostname}[/cyan]: System type = [yellow]{system_type}[/yellow]")
        
        # Show target stacks
        dnos_target = result.get('target_dnos', '-')
        gi_ver = result.get('gi', '-')
        baseos_ver = result.get('baseos', '-')
        console.print(f"  Target Stacks:")
        console.print(f"    DNOS:   [green]{dnos_target}[/green]")
        console.print(f"    GI:     {gi_ver}")
        console.print(f"    BaseOS: {baseos_ver}")
        
        # Auto-detect NCC ID from connection result or operational.json
        _sd_ncc = result.get('ncc_id') if result.get('ncc_id') is not None else 0
        if _sd_ncc == 0:
            try:
                _ncc_vms = op_data.get('ncc_vms', [])
                for _vm in _ncc_vms:
                    _vm_m = re.search(r'ncc(\d+)', _vm)
                    if _vm_m:
                        _sd_ncc = int(_vm_m.group(1))
                        break
            except:
                pass
        
        cmd = f"request system deploy system-type {system_type} name {hostname} ncc-id {_sd_ncc}"
        console.print(f"  Command: [dim]{cmd}[/dim]")
        
        confirm = Prompt.ask(f"  Deploy target stacks on {hostname}?", choices=["y", "n", "b"], default="y").lower()
        if confirm == 'b':
            return
        if confirm != 'y':
            console.print(f"  [dim]Skipped {hostname}[/dim]")
            continue
        
        # Execute deploy command with NCC ID retry
        console.print(f"  [yellow]Deploying (NCC {_sd_ncc})...[/yellow]")
        channel.send(cmd + "\r\n")
        time.sleep(5)
        
        output = ""
        try:
            while channel.recv_ready():
                output += channel.recv(65535).decode(errors='ignore')
                time.sleep(0.5)
        except:
            pass
        
        # NCC ID mismatch - retry with the other NCC
        if "doesn't match" in output.lower() or 'auto detected' in output.lower():
            _sd_ncc = 1 - _sd_ncc
            cmd = f"request system deploy system-type {system_type} name {hostname} ncc-id {_sd_ncc}"
            console.print(f"  [yellow]NCC ID mismatch, retrying with ncc-id {_sd_ncc}...[/yellow]")
            channel.send(cmd + "\r\n")
            time.sleep(5)
            output = ""
            try:
                while channel.recv_ready():
                    output += channel.recv(65535).decode(errors='ignore')
                    time.sleep(0.5)
            except:
                pass
        
        # Handle confirmation prompt
        if 'yes/no' in output.lower() or 'do you want' in output.lower() or 'y/n' in output.lower():
            channel.send("yes\r\n")
            time.sleep(5)
            try:
                while channel.recv_ready():
                    output += channel.recv(65535).decode(errors='ignore')
                    time.sleep(0.5)
            except:
                pass
        
        if "error" in output.lower() or "failed" in output.lower():
            console.print(f"  [red]Deploy may have failed:[/red]")
            console.print(f"  [dim]{output[-200:]}[/dim]")
        else:
            console.print(f"  [green]Deploy initiated (ncc-id {_sd_ncc})[/green]")
            console.print(f"  [dim]Device will boot into DNOS with target stacks. This takes 3-5 minutes.[/dim]")
            console.print(f"  [dim]After boot, device will be accessible via SSH.[/dim]")
    
    Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")


def _enter_gi_mode_on_devices(multi_ctx: 'MultiDeviceContext', device_results: dict, baseos_devices: list):
    """Run dncli on BaseOS devices to enter GI mode."""
    console.print(f"\n[bold yellow]━━━ Enter GI Mode on {len(baseos_devices)} Device(s) ━━━[/bold yellow]")
    
    for hostname in baseos_devices:
        result = device_results.get(hostname)
        if not result or not result.get('channel'):
            console.print(f"[red]{hostname}: No active connection[/red]")
            continue
        
        channel = result['channel']
        
        console.print(f"\n[cyan]{hostname}[/cyan]: Running dncli...")
        
        # Run dncli to enter GI mode
        channel.send("dncli\r\n")
        time.sleep(2)
        
        # May need password
        output = ""
        try:
            while channel.recv_ready():
                output += channel.recv(65535).decode(errors='ignore')
                time.sleep(0.3)
        except:
            pass
        
        if "password" in output.lower():
            channel.send("dnroot\r\n")
            time.sleep(3)
            try:
                while channel.recv_ready():
                    output += channel.recv(65535).decode(errors='ignore')
                    time.sleep(0.3)
            except:
                pass
        
        if "gi#" in output.lower() or "gi(" in output.lower():
            console.print(f"  [green]✓ Entered GI mode successfully[/green]")
        else:
            console.print(f"  [yellow]⚠ Check manually - output:[/yellow]")
            console.print(f"  [dim]{output[-200:]}[/dim]")
    
    Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")


def _install_target_stack_on_devices(multi_ctx: 'MultiDeviceContext', devices_with_targets: list):
    """
    Run pre-check + install on DNOS devices that already have images in their target stack.
    No loading needed -- just pre-check and install.
    
    Args:
        multi_ctx: Multi-device context
        devices_with_targets: List of (hostname, target_version) tuples
    """
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    num = len(devices_with_targets)
    console.print(f"\n[bold]Install Target Stack on {num} device(s)[/bold]")
    console.print(f"[yellow]⚠ Devices will reboot after install![/yellow]")
    
    confirm = Prompt.ask("Proceed?", choices=["y", "n"], default="y").lower()
    if confirm != 'y':
        console.print("[dim]Cancelled.[/dim]")
        return
    
    print_lock = threading.Lock()
    
    def live_print(hostname, msg, style="dim"):
        with print_lock:
            console.print(f"  [cyan]{hostname:<12}[/cyan] [{style}]{msg}[/{style}]")
    
    def _install_one(hostname, target_ver):
        """Connect to device and run pre-check + install. Thread-safe."""
        result = {"precheck": "?", "install": "?", "detail": ""}
        
        def log(msg):
            pass  # Only use live_print for screen output
        
        from .connection_strategy import connect_for_upgrade
        conn = connect_for_upgrade(hostname, timeout=30)
        if not conn['connected']:
            live_print(hostname, "Connection failed", "red")
            return hostname, False, conn.get('abort_reason') or "Connection failed"
        
        ssh = conn['ssh']
        channel = conn['channel']
        conn_method = conn.get('method', 'DeviceConnector')
        live_print(hostname, f"Connected ({conn_method})")
        channel.settimeout(20)
        channel.send("\r\n")
        time.sleep(1)
        _ = channel.recv(10000)
        
        def send_cmd(cmd, wait=5):
            channel.sendall((cmd + "\n").encode('utf-8'))
            time.sleep(wait)
            out = ""
            attempts = 0
            while attempts < 10:
                if channel.recv_ready():
                    out += channel.recv(65535).decode('utf-8', errors='replace')
                    attempts = 0
                else:
                    attempts += 1
                    time.sleep(0.3)
                    if attempts >= 3 and out:
                        break
            return out
        
        # Step 1: Pre-check
        live_print(hostname, "Pre-check running...")
        precheck_out = send_cmd("request system target-stack pre-check", wait=10)
        precheck_lower = precheck_out.lower()
        
        precheck_ok = None
        if 'status: ok' in precheck_lower:
            precheck_ok = True
        elif 'status: error' in precheck_lower:
            precheck_ok = False
        
        # Poll until task completes (pre-check is async)
        if precheck_ok is None:
            failed_tests = []
            for poll in range(12):  # Up to ~2 min
                time.sleep(10)
                elapsed = (poll + 1) * 10
                live_print(hostname, f"Pre-check running... ({elapsed}s)")
                show_out = send_cmd("show system target-stack pre-check", wait=8)
                show_lower = show_out.lower()
                
                if 'in-progress' in show_lower or 'in_progress' in show_lower or 'running' in show_lower:
                    continue
                
                for sline in show_out.split('\n'):
                    sl = sline.lower().strip()
                    if 'pre-check result' in sl:
                        if 'passed' in sl:
                            precheck_ok = True
                        elif 'failed' in sl:
                            precheck_ok = False
                    if '| failed' in sl or '|failed' in sl:
                        parts = [p.strip() for p in sline.split('|') if p.strip()]
                        if len(parts) >= 2:
                            failed_tests.append(parts[0][:40])
                
                if precheck_ok is not None:
                    break
                if 'status: ok' in show_lower:
                    precheck_ok = True
                    break
                elif 'task status' in show_lower and 'done' in show_lower:
                    precheck_ok = True
                    break
        
        if precheck_ok is None:
            precheck_ok = True
            live_print(hostname, "⚠ Pre-check timed out, proceeding", "yellow")
        
        if precheck_ok:
            live_print(hostname, "✓ Pre-check passed", "green")
            result["precheck"] = "OK"
        else:
            live_print(hostname, "✗ Pre-check FAILED", "red")
            try:
                channel.close()
                ssh.close()
            except:
                pass
            return hostname, False, "Pre-check failed"
        
        # Step 2: Install
        live_print(hostname, "Installing...")
        install_out = send_cmd("request system target-stack install", wait=15)
        install_lower = install_out.lower()
        confirm_out = ""
        
        # If "another precheck in-progress", wait and retry
        if 'another precheck' in install_lower or ('precheck' in install_lower and 'already' in install_lower):
            for retry in range(6):
                time.sleep(10)
                live_print(hostname, f"Waiting for pre-check... ({(retry + 1) * 10}s)")
                install_out = send_cmd("request system target-stack install", wait=15)
                install_lower = install_out.lower()
                if 'another precheck' not in install_lower and 'already' not in install_lower:
                    break
        
        # DNOS may auto-wait: "Precheck in progress, waiting till finished"
        if 'precheck in progress' in install_lower and 'waiting' in install_lower:
            live_print(hostname, "DNOS running pre-check internally...")
            time.sleep(15)
            extra = ""
            try:
                att = 0
                while att < 20:
                    if channel.recv_ready():
                        extra += channel.recv(65535).decode('utf-8', errors='replace')
                        att = 0
                    else:
                        att += 1
                        time.sleep(1)
                        if att >= 5 and extra:
                            break
            except:
                pass
            install_out += extra
            install_lower = install_out.lower()
        
        # Only send "yes" if DNOS is actually prompting
        if 'yes/no' in install_lower or 'do you want' in install_lower or 'continue' in install_lower:
            confirm_out = send_cmd("yes", wait=10)
        
        combined = (install_out + confirm_out).lower()
        
        install_ok = False
        if 'task id' in combined or 'started' in combined:
            install_ok = True
            live_print(hostname, "✓ Install started — device will reboot", "green")
        elif 'rebooting' in combined:
            install_ok = True
            live_print(hostname, "✓ Rebooting!", "green")
        elif 'error' in combined or 'failed' in combined:
            live_print(hostname, "✗ Install error — check device", "red")
        else:
            live_print(hostname, "⚠ Install sent — verify on device", "yellow")
        
        try:
            channel.close()
            ssh.close()
        except:
            pass
        
        return hostname, install_ok, "OK" if install_ok else "Check manually"
    
    # Run all installs in parallel — live_print shows progress in real time
    console.print()
    results = {}
    
    with ThreadPoolExecutor(max_workers=min(num, 8)) as pool:
        futures = {pool.submit(_install_one, h, tgt): (h, tgt) for h, tgt in devices_with_targets}
        for future in as_completed(futures):
            h, tgt = futures[future]
            try:
                hostname, success, status = future.result()
                results[h] = success
            except Exception as e:
                live_print(h, f"✗ {str(e)[:50]}", "red")
                results[h] = False
    
    # Summary
    ok_count = sum(1 for v in results.values() if v)
    fail_count = num - ok_count
    console.print()
    if ok_count == num:
        console.print(f"[bold green]✓ All {num} device(s) installing — will reboot.[/bold green]")
    elif ok_count > 0:
        console.print(f"[yellow]⚠ {ok_count}/{num} installing, {fail_count} need attention.[/yellow]")
    else:
        console.print(f"[red]✗ No installs started.[/red]")
    
    Prompt.ask("\n[dim]Press Enter[/dim]", default="")


def _deploy_target_stack_on_gi_devices(multi_ctx: 'MultiDeviceContext', gi_devices: list):
    """
    Deploy target stacks on GI-mode devices (request system deploy).
    Images are already loaded -- just run pre-check + deploy.
    
    Args:
        multi_ctx: Multi-device context
        gi_devices: List of (hostname, target_version, system_type) tuples
    """
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    num = len(gi_devices)
    console.print(f"\n[bold]Deploy Target Stack on {num} GI device(s)[/bold]")
    console.print(f"[yellow]Devices will reboot after deploy![/yellow]")
    
    # Show deploy parameters for each device
    console.print(f"\n[bold]Deploy Parameters:[/bold]")
    deploy_params = {}
    for hostname, tgt_ver, sys_type in gi_devices:
        console.print(f"  [cyan]{hostname}[/cyan]: system-type {sys_type}, name {hostname}, ncc-id [dim]auto[/dim]")
        deploy_params[hostname] = {
            'system_type': sys_type,
            'deploy_name': hostname,
            'target_version': tgt_ver
        }
    
    confirm = Prompt.ask("\nProceed with deploy?", choices=["y", "n"], default="y").lower()
    if confirm != 'y':
        console.print("[dim]Cancelled.[/dim]")
        return
    
    print_lock = threading.Lock()
    
    def live_print(hostname, msg, style="dim"):
        with print_lock:
            console.print(f"  [cyan]{hostname:<12}[/cyan] [{style}]{msg}[/{style}]")
    
    def _deploy_one(hostname, tgt_ver, sys_type):
        """Connect to GI device and run deploy. Thread-safe."""
        from .connection_strategy import connect_for_upgrade
        conn = connect_for_upgrade(hostname, timeout=30)
        if not conn['connected']:
            live_print(hostname, "Connection failed", "red")
            return hostname, False, conn.get('abort_reason') or "Connection failed"
        
        ssh = conn['ssh']
        channel = conn['channel']
        conn_method = conn.get('method', 'DeviceConnector')
        live_print(hostname, f"Connected ({conn_method})")
        channel.settimeout(30)
        channel.send("\r\n")
        time.sleep(1)
        _ = channel.recv(10000)
        
        def send_cmd(cmd, wait=5):
            channel.sendall((cmd + "\n").encode('utf-8'))
            time.sleep(wait)
            out = ""
            attempts = 0
            while attempts < 10:
                if channel.recv_ready():
                    out += channel.recv(65535).decode('utf-8', errors='replace')
                    attempts = 0
                else:
                    attempts += 1
                    time.sleep(0.3)
                    if attempts >= 3 and out:
                        break
            return out
        
        # Capture old install task ID before deploy
        old_install = send_cmd("show system install | no-more", wait=3)
        old_install_match = re.search(r'Task ID:\s*(\d+)', old_install)
        old_install_task_id = old_install_match.group(1) if old_install_match else ""
        
        # Step 1: Pre-check
        live_print(hostname, "Pre-check running...")
        precheck_out = send_cmd("show system target-stack pre-check | no-more", wait=5)
        precheck_lower = precheck_out.lower()
        
        precheck_ok = False
        if 'succeeded' in precheck_lower or 'passed' in precheck_lower:
            precheck_ok = True
        elif 'task status' in precheck_lower and 'done' in precheck_lower:
            precheck_ok = True
        
        if not precheck_ok:
            live_print(hostname, "Running fresh pre-check...")
            req_out = send_cmd("request system target-stack pre-check", wait=10)
            for poll in range(12):
                time.sleep(10)
                show_out = send_cmd("show system target-stack pre-check | no-more", wait=5)
                sl = show_out.lower()
                if 'succeeded' in sl or 'passed' in sl:
                    precheck_ok = True
                    break
                if 'failed' in sl and 'pre-check result' in sl:
                    break
                if 'task status' in sl and 'done' in sl:
                    precheck_ok = True
                    break
                live_print(hostname, f"Pre-check running... ({(poll+1)*10}s)")
        
        if not precheck_ok:
            live_print(hostname, "Pre-check failed or timed out", "red")
            try:
                ssh.close()
            except:
                pass
            return hostname, False, "Pre-check failed"
        
        live_print(hostname, "Pre-check passed", "green")
        
        # Step 2: Deploy (auto-detect NCC ID from connection, retry on mismatch)
        _dep_ncc = conn.get('ncc_id') if conn.get('ncc_id') is not None else 0
        deploy_cmd = f"request system deploy system-type {sys_type} name {hostname} ncc-id {_dep_ncc}"
        live_print(hostname, f"> deploy ncc-id {_dep_ncc}...")
        
        deploy_out = send_cmd(deploy_cmd, wait=12)
        deploy_lower = deploy_out.lower()
        confirm_out = ""
        
        # NCC ID mismatch - retry with the other NCC
        if "doesn't match" in deploy_lower or 'auto detected' in deploy_lower:
            _dep_ncc = 1 - _dep_ncc
            deploy_cmd = f"request system deploy system-type {sys_type} name {hostname} ncc-id {_dep_ncc}"
            live_print(hostname, f"NCC retry -> ncc-id {_dep_ncc}")
            deploy_out = send_cmd(deploy_cmd, wait=12)
            deploy_lower = deploy_out.lower()
        
        if 'yes/no' in deploy_lower or 'do you want' in deploy_lower or 'continue' in deploy_lower or 'y/n' in deploy_lower:
            confirm_out = send_cmd("yes", wait=5)
            live_print(hostname, "> yes")
        elif not deploy_lower.strip():
            time.sleep(5)
            extra = ""
            while channel.recv_ready():
                extra += channel.recv(65535).decode('utf-8', errors='replace')
                time.sleep(0.3)
            if extra:
                deploy_out += extra
                deploy_lower = deploy_out.lower()
                if 'yes/no' in deploy_lower or 'do you want' in deploy_lower or 'y/n' in deploy_lower:
                    confirm_out = send_cmd("yes", wait=5)
                    live_print(hostname, "> yes")
        
        combined = (deploy_out + confirm_out).lower()
        
        if 'error' in combined and 'pre-check result' not in combined:
            live_print(hostname, f"Deploy error: {combined[:60]}", "red")
            try:
                ssh.close()
            except:
                pass
            return hostname, False, "Deploy failed"
        
        # Step 3: Verify deploy started via show system install
        deploy_ok = False
        socket_lost = False
        for verify_attempt in range(10):
            time.sleep(8)
            try:
                inst_out = send_cmd("show system install | no-more", wait=5)
                inst_lower = inst_out.lower()
                inst_match = re.search(r'Task ID:\s*(\d+)', inst_out)
                inst_id = inst_match.group(1) if inst_match else ""
                
                if inst_id and inst_id != old_install_task_id:
                    live_print(hostname, f"Deploy started (task {inst_id})", "green")
                    deploy_ok = True
                    break
                if 'in-progress' in inst_lower:
                    live_print(hostname, "Installation in progress", "green")
                    deploy_ok = True
                    break
            except Exception as e:
                if 'socket' in str(e).lower() or 'closed' in str(e).lower() or 'eof' in str(e).lower():
                    socket_lost = True
                    live_print(hostname, "Device rebooting (deploy in progress)", "green")
                    deploy_ok = True
                    break
            elapsed = (verify_attempt + 1) * 8
            live_print(hostname, f"Waiting for deploy to register... ({elapsed}s)")
        
        if deploy_ok or socket_lost:
            # Update operational.json
            try:
                from pathlib import Path as _P
                _opf = _P(f"db/configs/{hostname}/operational.json")
                if _opf.exists():
                    with open(_opf) as f:
                        _opd = json.load(f)
                    _opd['device_state'] = 'DEPLOYING'
                    _opd['install_status'] = 'initiated'
                    _opd['upgrade_in_progress'] = True
                    with open(_opf, 'w') as f:
                        json.dump(_opd, f, indent=4)
            except:
                pass
        else:
            live_print(hostname, "Deploy NOT confirmed -- check device", "red")
        
        try:
            ssh.close()
        except:
            pass
        
        return hostname, deploy_ok, "Deploy started" if deploy_ok else "Deploy not confirmed"
    
    console.print()
    results = {}
    
    with ThreadPoolExecutor(max_workers=min(num, 8)) as pool:
        futures = {pool.submit(_deploy_one, h, tgt, st): (h, tgt) for h, tgt, st in gi_devices}
        for future in as_completed(futures):
            h, tgt = futures[future]
            try:
                hostname, success, status = future.result()
                results[h] = success
            except Exception as e:
                live_print(h, f"Error: {str(e)[:50]}", "red")
                results[h] = False
    
    ok_count = sum(1 for v in results.values() if v)
    fail_count = num - ok_count
    console.print()
    if ok_count == num:
        console.print(f"[bold green]All {num} device(s) deploying -- will reboot into DNOS.[/bold green]")
    elif ok_count > 0:
        console.print(f"[yellow]{ok_count}/{num} deploying, {fail_count} need attention.[/yellow]")
    else:
        console.print(f"[red]No deploys started.[/red]")
    
    Prompt.ask("\n[dim]Press Enter[/dim]", default="")


def _save_to_upgrade_history(history_path: Path, recent_urls: list, recent_branches: list, 
                              stack: dict, choice: str, url: str = ""):
    """Save a valid source to upgrade history for Recent Sources."""
    history_data = {'recent_urls': recent_urls, 'recent_branches': recent_branches, 'max_entries': 10}
    
    # Extract version info from URL
    dnos_version = 'N/A'
    if stack.get('dnos_url') and stack.get('dnos_url') != 'N/A':
        try:
            dnos_version = stack.get('dnos_url', '').split('/')[-1].replace('.tar', '')[:40]
        except:
            pass
    
    new_entry = {
        'url': url,
        'timestamp': datetime.now().isoformat(),
        'dnos_version': dnos_version,
        'branch': stack.get('branch'),
        'build': stack.get('build'),
        'source_type': {
            "1": "dev_branch",
            "2": "release_branch",
            "3": "manual_branch",
            "4": "jenkins_url",
            "5": "minio_url",
        }.get(choice, "other"),
        'has_dnos': bool(stack.get('dnos_url') and stack.get('dnos_url') != 'N/A'),
        'has_gi': bool(stack.get('gi_url') and stack.get('gi_url') != 'N/A'),
        'has_baseos': bool(stack.get('baseos_url') and stack.get('baseos_url') != 'N/A'),
    }
    
    if choice == "4":
        # For Jenkins URLs, add to recent_urls
        history_data['recent_urls'] = [new_entry] + [u for u in recent_urls if u.get('branch') != new_entry.get('branch') or u.get('build') != new_entry.get('build')][:9]
    else:
        # For branches (options 1, 2, 3, 5), add to recent_branches
        history_data['recent_branches'] = [new_entry] + [b for b in recent_branches if b.get('branch') != new_entry.get('branch') or b.get('build') != new_entry.get('build')][:9]
    
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with open(history_path, 'w') as f:
        json.dump(history_data, f, indent=2)


def _show_build_failure_log(jenkins: 'JenkinsClient', branch: str, build_number: int):
    """Fetch and display failure details from Jenkins console log."""
    from rich.panel import Panel
    
    console.print("\n[bold red]📋 Fetching Failure Details...[/bold red]")
    
    try:
        success, failed_stage, log_content = jenkins.get_failed_stage_log(branch, build_number)
        
        if success:
            console.print(f"\n[bold yellow]Failed Stage: {failed_stage}[/bold yellow]")
            console.print(Panel(
                log_content[:3000],
                title="[red]Error Log[/red]",
                border_style="red",
                expand=False
            ))
        else:
            console.print(f"[yellow]Could not fetch log: {log_content}[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Error fetching failure log: {e}[/yellow]")


def _handle_build_failure_with_retry(jenkins: 'JenkinsClient', branch: str, build_number: int,
                                      build_result: str, multi_ctx: 'MultiDeviceContext',
                                      with_baseos: bool = True, retry_count: int = 0) -> Tuple[bool, Optional[Dict]]:
    """Handle a failed build - detect infrastructure issues and auto-retry.
    
    Returns:
        Tuple of (should_continue_to_push, stack_dict or None)
    """
    console.print(f"\n[red]✗ Build #{build_number} {build_result}[/red]")
    
    # Check if it's an infrastructure failure
    is_infra, reason, node_name = jenkins.is_infrastructure_failure(branch, build_number)
    
    if is_infra:
        console.print(f"[yellow]⚠ Infrastructure failure: {reason}[/yellow]")
        if node_name:
            console.print(f"[dim]Node: {node_name} (blocklisted for 24h)[/dim]")
        
        if retry_count >= 3:
            console.print(f"[red]Max retries ({retry_count}) reached.[/red]")
            _show_build_failure_log(jenkins, branch, build_number)
            return False, None
        
        console.print(f"\n  [1] 🔄 Auto-retry (attempt {retry_count + 1}/3)")
        console.print("  [2] 📋 Show failure log")
        console.print("  [B] Back to menu")
        retry_choice = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="1").lower()
        
        if retry_choice == "2":
            _show_build_failure_log(jenkins, branch, build_number)
            if not Confirm.ask("\nRetry build?", default=True):
                return False, None
        elif retry_choice == "b":
            return False, None
        
        # Trigger retry
        console.print(f"\n[bold yellow]🔄 Retrying build (attempt {retry_count + 1}/3)...[/bold yellow]")
        
        success, message = jenkins.trigger_build(branch, with_baseos=with_baseos, qa_version=False)
        if not success:
            console.print(f"[red]✗ Failed to trigger retry: {message}[/red]")
            return False, None
        
        console.print(f"[green]✓ {message}[/green]")
        console.print("[dim]Waiting for build to start...[/dim]")
        
        new_build_number = jenkins.wait_for_build_start(branch, timeout=180)
        if not new_build_number:
            console.print("[yellow]Build queued but not started. Try later.[/yellow]")
            return False, None
        
        console.print(f"[green]✓ Build #{new_build_number} started![/green]")
        console.print("\n[yellow]📊 Monitoring retry build...[/yellow]")
        console.print("[dim]Press Ctrl+C to detach[/dim]\n")
        
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.fields[status]}"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"Building #{new_build_number}...", total=100, status="Starting...")
            
            def update_progress(msg, pct):
                progress.update(task, completed=pct, description=msg, status=f"{pct}%")
            
            try:
                new_build = jenkins.wait_for_build_completion(
                    branch, new_build_number,
                    timeout=3600, poll_interval=30,
                    progress_callback=update_progress
                )
                
                if new_build and new_build.result == "SUCCESS":
                    console.print(f"\n[bold green]✓ Build #{new_build_number} SUCCEEDED![/bold green]")
                    
                    urls = jenkins.get_stack_urls(branch, new_build_number)
                    console.print("\n[bold]Artifacts Ready:[/bold]")
                    console.print(f"  • DNOS: {'✓' if urls.get('dnos') else '✗'}")
                    console.print(f"  • GI: {'✓' if urls.get('gi') else '✗'}")
                    console.print(f"  • BaseOS: {'✓' if urls.get('baseos') else '✗'}")
                    
                    return True, {
                        'branch': branch,
                        'build': new_build_number,
                        'dnos_url': urls.get('dnos'),
                        'gi_url': urls.get('gi'),
                        'baseos_url': urls.get('baseos') if with_baseos else None,
                        'age_hours': 0,
                    }
                elif new_build:
                    # Recursive retry
                    return _handle_build_failure_with_retry(
                        jenkins, branch, new_build_number, new_build.result,
                        multi_ctx, with_baseos, retry_count + 1
                    )
                else:
                    console.print("\n[yellow]Build timed out[/yellow]")
                    return False, None
            except KeyboardInterrupt:
                console.print("\n[yellow]Detached. Build continues in Jenkins.[/yellow]")
                return False, None
    else:
        # Not infrastructure - real code issue
        console.print("[dim]This appears to be a code issue, not infrastructure.[/dim]")
        _show_build_failure_log(jenkins, branch, build_number)
        return False, None


def run_image_upgrade_wizard(multi_ctx: 'MultiDeviceContext') -> bool:
    """
    Interactive wizard for upgrading DNOS/GI/BaseOS from Jenkins builds.
    
    Args:
        multi_ctx: MultiDeviceContext with selected devices
        
    Returns:
        True if upgrade was successful
    """
    from pathlib import Path
    from .jenkins_integration import JenkinsClient, get_stack_from_url, list_dev_branches
    
    def _select_build_from_branch(jenkins_client, branch_name, console, skip_to_browse=False):
        """Show builds for a branch with option to include failed builds + sanitizer detection.
        
        Args:
            skip_to_browse: If True, skip the latest-pure-build search and go straight
                           to the full build table (used when caller already showed a build).
        
        Returns stack dict or None to go back.
        """
        from urllib.parse import unquote as _unquote
        # Normalize branch name: decode any URL-encoded slashes (%2F -> /)
        # Jenkins API functions handle their own encoding internally
        raw_branch = _unquote(branch_name)
        
        sel = "2" if skip_to_browse else None
        
        if not skip_to_browse:
            console.print(f"\n[dim]Finding latest successful pure build for {raw_branch}...[/dim]")
            console.print("[dim]   (Excluding NIGHTLY, EMUX, SILICON, NCPL, NCP3, Polaris builds)[/dim]")
            
            pure_build = jenkins_client.get_latest_pure_build(raw_branch)
            
            if pure_build:
                build = pure_build['build']
                age_hours = build.age_hours
                if age_hours < 1:
                    age_str = f"{int(age_hours * 60)}m ago"
                elif age_hours < 24:
                    hours = int(age_hours)
                    mins = int((age_hours - hours) * 60)
                    age_str = f"{hours}h {mins}m ago" if mins > 0 else f"{hours}h ago"
                else:
                    days = int(age_hours / 24)
                    hours = int(age_hours % 24)
                    age_str = f"{days}d {hours}h ago" if hours > 0 else f"{days}d ago"
                
                console.print(f"\n[bold green][OK] Latest Successful Build #{build.build_number}[/bold green]")
                console.print(f"  [cyan]Display Name:[/cyan] {pure_build['display_name']}")
                console.print(f"  [cyan]Age:[/cyan]          {age_str}")
                if build.is_sanitizer:
                    console.print(f"  [yellow][ASAN] This build includes AddressSanitizer[/yellow]")
                console.print(f"  [cyan]Artifacts:[/cyan]")
                console.print(f"    DNOS:   {'[green][OK] Available[/green]' if pure_build['has_dnos'] else '[red][FAIL] Not found[/red]'}")
                console.print(f"    GI:     {'[green][OK] Available[/green]' if pure_build['has_gi'] else '[red][FAIL] Not found[/red]'}")
                console.print(f"    BaseOS: {'[green][OK] Available[/green]' if pure_build['has_baseos'] else '[yellow][WARN] Not included[/yellow]'}")
                
                if not pure_build['has_baseos']:
                    console.print("\n[yellow][WARN] This build does NOT include BaseOS.[/yellow]")
                    console.print("[dim]  BaseOS updates are typically only needed for major version jumps.[/dim]")
                
                console.print(f"\n  [1] Use build #{build.build_number} (latest successful)")
                console.print(f"  [2] Browse all recent builds (includes failed builds with artifacts)")
                console.print(f"  [B] Back")
                sel = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="1").lower()
                
                if sel == "b":
                    return None
                elif sel == "1":
                    urls = jenkins_client.get_stack_urls(raw_branch, build.build_number)
                    return {
                        'branch': raw_branch,
                        'build': build.build_number,
                        'dnos_url': urls.get('dnos'),
                        'gi_url': urls.get('gi'),
                        'baseos_url': urls.get('baseos') if pure_build['has_baseos'] else None,
                    }
            else:
                console.print(f"[yellow]No successful pure build found for {raw_branch}[/yellow]")
                console.print("[dim]Searching all recent builds (including failed) for usable images...[/dim]\n")
                sel = "2"
        
        if sel == "2":
            console.print(f"\n[dim]Scanning recent builds for {raw_branch} (including failed)...[/dim]")
            all_builds = jenkins_client.get_recent_builds_with_artifacts(raw_branch, limit=15, max_results=10)
            
            if not all_builds:
                console.print("[yellow]No builds with image artifacts found[/yellow]")
                return None
            
            console.print(f"\n[bold]Recent Builds with Image Artifacts:[/bold]")
            console.print("[dim]Includes failed builds that produced valid DNOS/GI/BaseOS images[/dim]\n")
            
            from rich.table import Table as RichTable
            tbl = RichTable(box=None, pad_edge=False)
            tbl.add_column("#", width=3, style="dim")
            tbl.add_column("Build", width=7)
            tbl.add_column("Status", width=10)
            tbl.add_column("Age", width=12)
            tbl.add_column("DNOS", width=5)
            tbl.add_column("GI", width=5)
            tbl.add_column("BaseOS", width=6)
            tbl.add_column("Flags", width=12)
            
            for i, bi in enumerate(all_builds, 1):
                b = bi['build']
                age_h = b.age_hours
                if age_h < 1:
                    a_str = f"{int(age_h * 60)}m"
                elif age_h < 24:
                    a_str = f"{int(age_h)}h"
                else:
                    a_str = f"{age_h / 24:.1f}d"
                
                status_style = "[green]SUCCESS[/green]" if b.result == "SUCCESS" else "[red]FAILURE[/red]"
                dnos_mark = "[green][OK][/green]" if bi['has_dnos'] else "[red]--[/red]"
                gi_mark = "[green][OK][/green]" if bi['has_gi'] else "[red]--[/red]"
                baseos_mark = "[green][OK][/green]" if bi['has_baseos'] else "[dim]--[/dim]"
                
                flags = []
                if bi['is_sanitizer']:
                    flags.append("[yellow][ASAN][/yellow]")
                if b.is_expired:
                    flags.append("[red][EXPIRED][/red]")
                flag_str = " ".join(flags) if flags else ""
                
                tbl.add_row(str(i), f"#{b.build_number}", status_style, a_str,
                            dnos_mark, gi_mark, baseos_mark, flag_str)
            
            console.print(tbl)
            console.print(f"\n  [B] Back")
            
            valid = [str(i) for i in range(1, len(all_builds) + 1)] + ["b", "B"]
            pick = Prompt.ask("Select build", choices=valid, default="1").lower()
            
            if pick == "b":
                return None
            
            selected = all_builds[int(pick) - 1]
            sb = selected['build']
            
            if sb.result != 'SUCCESS':
                console.print(f"\n[yellow][WARN] Build #{sb.build_number} result: {sb.result}[/yellow]")
                console.print("[dim]  The build failed on tests, but image artifacts were still created.[/dim]")
            if selected['is_sanitizer']:
                console.print(f"[yellow][ASAN] Build #{sb.build_number} includes AddressSanitizer instrumentation[/yellow]")
                console.print("[dim]  Sanitizer builds are slower but detect memory errors at runtime.[/dim]")
            if sb.is_expired:
                console.print(f"[red][WARN] Build #{sb.build_number} artifacts may be expired (>{int(sb.age_hours)}h old)[/red]")
            
            if not Confirm.ask(f"\nUse build #{sb.build_number}?", default=True):
                return None
            
            urls = jenkins_client.get_stack_urls(raw_branch, sb.build_number)
            return {
                'branch': raw_branch,
                'build': sb.build_number,
                'dnos_url': urls.get('dnos'),
                'gi_url': urls.get('gi'),
                'baseos_url': urls.get('baseos') if selected['has_baseos'] else None,
                '_is_sanitizer': selected['is_sanitizer'],
                '_build_result': sb.result,
            }
        
        return None
    
    console.print("\n[bold cyan]═════════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]              Image Upgrade Wizard                              [/bold cyan]")
    console.print("[bold cyan]═════════════════════════════════════════════════════════════════[/bold cyan]")
    
    device_names = ", ".join([d.hostname for d in multi_ctx.devices])
    console.print(f"[dim]Target devices: {device_names}[/dim]\n")
    
    # Show current stacks from DB cache (instant, no SSH)
    # Panel-per-device layout: full version strings, no column truncation
    console.print("[bold]Current Device Stacks:[/bold] [dim](from cache)[/dim]")
    from rich.panel import Panel as RichPanel
    
    device_stacks = {}
    any_missing = False
    
    for dev in multi_ctx.devices:
        stk = {'dnos': '-', 'dnos_t': '-', 'gi': '-', 'gi_t': '-', 'baseos': '-', 'baseos_t': '-'}
        device_state = "Unknown"
        state_display = "[yellow]?[/yellow]"
        connection_via = "-"
        
        try:
            op_file = Path(f"/home/dn/SCALER/db/configs/{dev.hostname}/operational.json")
            if op_file.exists():
                with open(op_file) as f:
                    op_data = json.load(f)
                
                stk['dnos'] = op_data.get('dnos_version', '-') or '-'
                stk['gi'] = op_data.get('gi_version', '-') or '-'
                stk['baseos'] = op_data.get('baseos_version', '-') or '-'
                stk['dnos_t'] = op_data.get('target_dnos_version', '-') or '-'
                stk['gi_t'] = op_data.get('target_gi_version', '-') or '-'
                stk['baseos_t'] = op_data.get('target_baseos_version', '-') or '-'
                
                cached_state = op_data.get('device_state', 'Unknown')
                state_map = {'DNOS': '[green]DNOS[/green]', 'GI': '[cyan]GI[/cyan]',
                             'BaseOS': '[yellow]BaseOS[/yellow]', 'BASEOS_SHELL': '[yellow]BaseOS[/yellow]',
                             'ONIE': '[red]ONIE[/red]', 'DEPLOYING': '[cyan]GI[/cyan]',
                             'UPGRADING': '[yellow]Upgrading[/yellow]', 'DN_RECOVERY': '[red]Recovery[/red]'}
                state_display = state_map.get(cached_state, f'[yellow]{cached_state}[/yellow]')
                device_state = cached_state
                # DEPLOYING without a confirmed install task means the device is still in GI
                if cached_state == 'DEPLOYING':
                    install_status = op_data.get('install_status', '')
                    if install_status != 'initiated':
                        device_state = 'GI'
                connection_via = op_data.get('connection_method', '-') or '-'
                
                if stk['dnos'] == '-' and device_state not in ('GI', 'BaseOS', 'ONIE'):
                    any_missing = True
            else:
                any_missing = True
        except Exception:
            any_missing = True
        
        device_stacks[dev.hostname] = stk['dnos'] if stk['dnos'] != "-" else "Unknown"
        
        lines = []
        for label, cur_k, tgt_k in [('DNOS', 'dnos', 'dnos_t'), ('GI', 'gi', 'gi_t'), ('BaseOS', 'baseos', 'baseos_t')]:
            cur = stk[cur_k]
            tgt = stk[tgt_k]
            if tgt and tgt != '-':
                lines.append(f"  [bold]{label:6s}[/bold]  [dim]cur:[/dim] {cur}")
                lines.append(f"          [dim]tgt:[/dim] [bold yellow]{tgt}[/bold yellow]")
            else:
                lines.append(f"  [bold]{label:6s}[/bold]  {cur}")
        
        title = f"[cyan]{dev.hostname}[/cyan] {state_display} [dim]{connection_via}[/dim]"
        console.print(RichPanel("\n".join(lines), title=title, title_align="left",
                                border_style="dim", expand=True, padding=(0, 1)))
    
    if any_missing:
        console.print("[dim]  Tip: Use [V] Verify Stacks Live to refresh from devices[/dim]")
    
    # Detect devices with target stacks waiting to be installed/deployed
    devices_with_targets = []
    gi_devices_with_targets = []
    for dev in multi_ctx.devices:
        try:
            op_file = Path(f"/home/dn/SCALER/db/configs/{dev.hostname}/operational.json")
            if op_file.exists():
                with open(op_file) as f:
                    op_data = json.load(f)
                tgt = op_data.get('target_dnos_version', '-') or '-'
                state = op_data.get('device_state', '')
                _inst_status = op_data.get('install_status', '')
                if tgt != '-' and state == 'DNOS':
                    devices_with_targets.append((dev.hostname, tgt))
                elif tgt != '-' and state in ('GI', 'DEPLOYING', 'BASEOS_SHELL'):
                    gi_devices_with_targets.append((dev.hostname, tgt, op_data.get('system_type', 'SA-36CD-S')))
        except Exception:
            pass
    
    # Check for recent sources history
    history_path = Path("db/upgrade_sources_history.json")
    has_history = history_path.exists()
    recent_urls = []
    recent_branches = []
    if has_history:
        try:
            with open(history_path) as f:
                history = json.load(f)
                recent_urls = history.get('recent_urls', [])
                recent_branches = history.get('recent_branches', [])
        except:
            pass
    
    console.print("\n[bold]Step 1: Select Source[/bold]")
    if has_history and (recent_urls or recent_branches):
        console.print("  [0] [yellow]⚡ Recent Sources[/yellow] (quick load from history)")
    console.print("  [1] Browse development branches (dev_v*)")
    console.print("  [2] Browse release branches (rel_v*)")
    console.print("  [3] Enter branch name manually")
    console.print("  [4] [cyan]Paste Jenkins URL[/cyan] (Blue Ocean or classic)")
    console.print("  [5] Enter direct Minio URLs")
    console.print("  [6] [green]🔨 Trigger New Build[/green] (build from source)")
    console.print("  [T] [magenta]📊 Monitor Triggered Builds[/magenta] (watch build progress)")
    console.print("  [S] 📊 Check Upgrade Status (show install progress on devices)")
    if devices_with_targets:
        dev_list = ", ".join([f"{h}" for h, _ in devices_with_targets])
        tgt_ver = devices_with_targets[0][1]
        console.print(f"  [I] [bold green]⚡ Install Target Stack[/bold green] - Pre-check + Install on {len(devices_with_targets)} device(s): {dev_list}")
        console.print(f"      [dim]Target: {tgt_ver}[/dim]")
    if gi_devices_with_targets:
        gi_dev_list = ", ".join([f"{h}" for h, _, _ in gi_devices_with_targets])
        gi_tgt_ver = gi_devices_with_targets[0][1]
        console.print(f"  [D] [bold cyan]⚡ Deploy Target Stack[/bold cyan] - Deploy on {len(gi_devices_with_targets)} GI device(s): {gi_dev_list}")
        console.print(f"      [dim]Target: {gi_tgt_ver}[/dim]")
    console.print("  [V] 🔄 Verify Stacks Live (SSH→SN/MGMT/Console + Deploy/Install)")
    console.print("  [R] 📦 Restore Pre-Delete Config (push backed-up config)")
    console.print("  [B] Back")
    
    base_choices = ["1", "2", "3", "4", "5", "6", "t", "T", "s", "S", "v", "V", "r", "R", "b", "B"]
    if has_history:
        base_choices = ["0"] + base_choices
    if devices_with_targets:
        base_choices.extend(["i", "I"])
    if gi_devices_with_targets:
        base_choices.extend(["d", "D"])
    choices = base_choices
    _default = "0" if has_history else "b"
    choice = Prompt.ask("Select", choices=choices, default=_default).lower()
    
    if choice == "b":
        return False
    
    stack = None
    jenkins = JenkinsClient()
    
    try:
        if choice == "0" and has_history:
            # Recent sources - show all saved sources with better formatting
            console.print("\n[bold]Recent Sources:[/bold]")
            items = []
            
            # Combine and sort by timestamp
            all_entries = []
            for entry in recent_urls:
                entry['_type'] = 'url'
                all_entries.append(entry)
            for entry in recent_branches:
                entry['_type'] = 'branch'
                all_entries.append(entry)
            
            # Sort by timestamp (most recent first)
            all_entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Deduplicate by branch - keep only first (most recent) entry per branch
            seen_branches = set()
            deduplicated = []
            for entry in all_entries:
                branch = entry.get('branch', '')
                entry_type = entry.get('_type', '')
                
                # For URL entries without a branch, always keep them (use URL as key)
                if entry_type == 'url' and not branch:
                    key = entry.get('url', str(len(deduplicated)))
                else:
                    key = branch
                
                if key and key not in seen_branches:
                    seen_branches.add(key)
                    deduplicated.append(entry)
            
            all_entries = deduplicated
            
            # For branch entries, fetch latest build numbers (parallel with timeout)
            console.print("[dim]Checking latest builds...[/dim]", end="\r")
            
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import requests as _requests
            
            def _validate_entry(idx_entry):
                """Validate a single history entry (runs in thread)."""
                i, entry = idx_entry
                branch = entry.get('branch', 'Unknown')
                stored_build = entry.get('build', '?')
                source_type = entry.get('source_type', entry.get('_type', 'unknown'))
                result = {'idx': i, 'entry': entry}
                
                try:
                    if entry.get('_type') == 'branch' and branch and branch != 'Unknown':
                        latest = jenkins.get_last_successful_build(branch)
                        if latest:
                            build = latest.build_number
                            urls = jenkins.get_stack_urls(branch, build)
                            dnos_url = urls.get('dnos', '')
                            gi_url = urls.get('gi', '')
                            
                            has_dnos = "✗"
                            has_gi = "✗"
                            if dnos_url and dnos_url != 'N/A':
                                try:
                                    has_dnos = "✓" if _requests.head(dnos_url, timeout=2).status_code == 200 else "[red]✗[/red]"
                                except:
                                    has_dnos = "[red]✗[/red]"
                            if gi_url and gi_url != 'N/A':
                                try:
                                    has_gi = "✓" if _requests.head(gi_url, timeout=2).status_code == 200 else "[red]✗[/red]"
                                except:
                                    has_gi = "[red]✗[/red]"
                            
                            if stored_build and isinstance(stored_build, int) and build > stored_build:
                                build_display = f"#{build} [green]↑{build - stored_build}[/green]"
                            else:
                                build_display = f"#{build}"
                            
                            entry['_latest_urls'] = urls
                            entry['_latest_build'] = build
                        else:
                            build_display = f"#{stored_build} [dim]?[/dim]"
                            has_dnos = "[dim]?[/dim]"
                            has_gi = "[dim]?[/dim]"
                    else:
                        build_display = f"#{stored_build}"
                        dnos_url = entry.get('dnos_url', '')
                        gi_url = entry.get('gi_url', '')
                        has_dnos = "✗"
                        has_gi = "✗"
                        if dnos_url:
                            try:
                                has_dnos = "✓" if _requests.head(dnos_url, timeout=2).status_code == 200 else "[red]✗[/red]"
                            except:
                                has_dnos = "[red]✗[/red]"
                        if gi_url:
                            try:
                                has_gi = "✓" if _requests.head(gi_url, timeout=2).status_code == 200 else "[red]✗[/red]"
                            except:
                                has_gi = "[red]✗[/red]"
                except Exception:
                    build_display = f"#{stored_build} [dim]err[/dim]"
                    has_dnos = "[dim]?[/dim]"
                    has_gi = "[dim]?[/dim]"
                
                type_label = {
                    'dev_branch': '[cyan]dev[/cyan]',
                    'release_branch': '[green]rel[/green]',
                    'manual_branch': '[yellow]branch[/yellow]',
                    'jenkins_url': '[blue]url[/blue]',
                    'minio_url': '[magenta]minio[/magenta]',
                    'url': '[blue]url[/blue]',
                    'branch': '[yellow]branch[/yellow]',
                }.get(source_type, source_type)
                branch_display = branch[:45] + "..." if len(branch) > 48 else branch
                
                result['display'] = f"{type_label} {branch_display} {build_display} | MinIO Images: DNOS:{has_dnos} GI:{has_gi}"
                return result
            
            entries_to_check = list(enumerate(all_entries[:10], 1))
            validated = {}
            
            with ThreadPoolExecutor(max_workers=4) as pool:
                futures = {pool.submit(_validate_entry, e): e for e in entries_to_check}
                try:
                    for future in as_completed(futures, timeout=8):
                        r = future.result()
                        validated[r['idx']] = (str(r['idx']), r['display'], r['entry'])
                except Exception:
                    pass
            
            # Build items in original order, fill in timed-out entries
            for i, entry in entries_to_check:
                if i in validated:
                    items.append(validated[i])
                else:
                    branch = entry.get('branch', 'Unknown')
                    stored_build = entry.get('build', '?')
                    source_type = entry.get('source_type', entry.get('_type', 'unknown'))
                    type_label = {'dev_branch': '[cyan]dev[/cyan]', 'release_branch': '[green]rel[/green]',
                                  'manual_branch': '[yellow]branch[/yellow]', 'jenkins_url': '[blue]url[/blue]',
                                  'url': '[blue]url[/blue]', 'branch': '[yellow]branch[/yellow]'}.get(source_type, source_type)
                    branch_display = branch[:45] + "..." if len(branch) > 48 else branch
                    items.append((str(i), f"{type_label} {branch_display} #{stored_build} [dim]timeout[/dim]", entry))
            
            # Clear the "Checking..." message
            console.print(" " * 40, end="\r")
            
            for idx, desc, _ in items:
                console.print(f"  [{idx}] {desc}")
            console.print("  [B] Back")
            
            sel = Prompt.ask("Select", choices=[i[0] for i in items] + ["b", "B"], default="1").lower()
            if sel == "b":
                return run_image_upgrade_wizard(multi_ctx)
            
            selected = next((i for i in items if i[0] == sel), None)
            if selected:
                entry = selected[2]
                display_text = selected[1] if len(selected) > 1 else ''
                
                # Early warning if artifacts are expired (✗ in display)
                _artifacts_expired = '✗' in display_text and '✓' not in display_text
                if _artifacts_expired and entry.get('branch'):
                    _branch_name = entry.get('branch', 'Unknown')
                    console.print(f"\n[yellow]⚠ Artifacts for this build are expired (48h MinIO retention)[/yellow]")
                    console.print(f"[dim]  Branch: {_branch_name}[/dim]")
                    
                    # Check if a build is already running for this branch
                    _current_build = None
                    try:
                        _current_build = jenkins.get_build_info(_branch_name, latest=True)
                    except Exception:
                        pass
                    
                    if _current_build and _current_build.building:
                        _elapsed_min = int((time.time() - _current_build.timestamp / 1000) / 60)
                        # Check if it has BaseOS by looking at artifacts so far
                        _cur_urls = jenkins.get_stack_urls(_branch_name, _current_build.build_number)
                        _has_baseos_hint = bool(_cur_urls.get('baseos'))
                        
                        console.print(f"\n[bold green]✓ Build #{_current_build.build_number} is already running![/bold green]")
                        console.print(f"  [dim]Running for: {_elapsed_min} minutes[/dim]")
                        if _has_baseos_hint:
                            console.print(f"  [dim]BaseOS: included[/dim]")
                        
                        console.print(f"\n  [1] Monitor this build + auto-upgrade when ready (recommended)")
                        console.print(f"  [2] Trigger a NEW build instead")
                        console.print(f"  [3] Fetch latest completed build (may be expired)")
                        console.print(f"  [B] Back")
                        _run_sel = Prompt.ask("Select", choices=["1", "2", "3", "b", "B"], default="1").lower()
                        
                        if _run_sel == "1":
                            # Monitor existing running build
                            console.print(f"\n[yellow]📊 Monitoring build #{_current_build.build_number}...[/yellow]")
                            console.print("[dim]Press Ctrl+C to detach (build continues in Jenkins)[/dim]\n")
                            
                            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
                            
                            try:
                                with Progress(
                                    SpinnerColumn(),
                                    TextColumn("[progress.description]{task.description}"),
                                    BarColumn(),
                                    TextColumn("{task.fields[status]}"),
                                    console=console
                                ) as _bprogress:
                                    _btask = _bprogress.add_task("Building...", total=100, status=f"Running ({_elapsed_min}m)")
                                    
                                    def _bupdate(msg, pct):
                                        _bprogress.update(_btask, completed=pct, description=msg, status=f"{pct}%")
                                    
                                    _build = jenkins.wait_for_build_completion(
                                        _branch_name, _current_build.build_number,
                                        timeout=3600, poll_interval=30,
                                        progress_callback=_bupdate
                                    )
                                    if _build and _build.result == "SUCCESS":
                                        console.print(f"\n[bold green]✓ Build #{_current_build.build_number} COMPLETED![/bold green]")
                                        _urls = jenkins.get_stack_urls(_branch_name, _current_build.build_number)
                                        stack = {
                                            'branch': _branch_name,
                                            'build': _current_build.build_number,
                                            'dnos_url': _urls.get('dnos'),
                                            'gi_url': _urls.get('gi'),
                                            'baseos_url': _urls.get('baseos'),
                                        }
                                        console.print(f"  DNOS: {'✓' if _urls.get('dnos') else '✗'}")
                                        console.print(f"  GI: {'✓' if _urls.get('gi') else '✗'}")
                                        console.print(f"  BaseOS: {'✓' if _urls.get('baseos') else '✗'}")
                                        console.print("\n[bold cyan]Continuing with upgrade...[/bold cyan]")
                                    elif _build:
                                        console.print(f"\n[red]✗ Build #{_current_build.build_number} {_build.result}[/red]")
                                        return False
                                    else:
                                        console.print("\n[yellow]Build timed out — check Jenkins manually[/yellow]")
                                        return False
                            except KeyboardInterrupt:
                                console.print("\n[yellow]Detached. Build continues in Jenkins.[/yellow]")
                                return run_image_upgrade_wizard(multi_ctx)
                        elif _run_sel == "2":
                            pass  # Fall through to trigger new build below
                        elif _run_sel == "3":
                            pass  # Fall through to fetch latest below (_exp_sel = "2" path)
                        elif _run_sel == "b":
                            return run_image_upgrade_wizard(multi_ctx)
                        
                        # If user chose [1] and build succeeded, stack is set — skip the menu below
                        if stack:
                            pass  # stack set from monitoring, continue to upgrade flow
                        elif _run_sel == "3":
                            _exp_sel = "2"  # Reuse the "fetch latest" path
                        elif _run_sel == "2":
                            _exp_sel = "1"  # Reuse the "trigger new" path
                        else:
                            _exp_sel = None
                    else:
                        console.print(f"\n  [1] Trigger new build + monitor + auto-upgrade when ready")
                        console.print(f"  [2] Fetch latest build anyway (may also be expired)")
                        console.print(f"  [B] Back")
                        _exp_sel = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="1").lower()
                    
                    if _exp_sel == "1" and not stack:
                        console.print(f"\n[bold]Build Options for: {_branch_name}[/bold]")
                        with_baseos = Confirm.ask("Build with BaseOS containers?", default=True)
                        qa_version = Confirm.ask("QA version (60-day retention)?", default=False)
                        
                        console.print(f"\n[yellow]Triggering new build for {_branch_name}...[/yellow]")
                        _trig_ok, _trig_msg = jenkins.trigger_build(_branch_name, with_baseos=with_baseos, qa_version=qa_version)
                        if _trig_ok:
                            console.print(f"[green]✓ {_trig_msg}[/green]")
                            console.print("\n[dim]Waiting for build to start...[/dim]")
                            
                            _build_number = jenkins.wait_for_build_start(_branch_name, timeout=120)
                            if _build_number:
                                from urllib.parse import quote
                                console.print(f"[green]✓ Build #{_build_number} started![/green]")
                                console.print(f"[dim]Jenkins: {jenkins.CHEETAH_BASE}/job/{quote(quote(_branch_name, safe=''), safe='')}/{_build_number}/[/dim]")
                                
                                console.print("\n[yellow]📊 Monitoring build progress...[/yellow]")
                                console.print("[dim]Press Ctrl+C to detach (build continues in Jenkins)[/dim]")
                                console.print(f"[dim]Will auto-continue upgrade when build completes[/dim]\n")
                                
                                from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
                                
                                try:
                                    with Progress(
                                        SpinnerColumn(),
                                        TextColumn("[progress.description]{task.description}"),
                                        BarColumn(),
                                        TextColumn("{task.fields[status]}"),
                                        console=console
                                    ) as _bprogress:
                                        _btask = _bprogress.add_task("Building...", total=100, status="Starting...")
                                        
                                        def _bupdate(msg, pct):
                                            _bprogress.update(_btask, completed=pct, description=msg, status=f"{pct}%")
                                        
                                        _build = jenkins.wait_for_build_completion(
                                            _branch_name, _build_number,
                                            timeout=3600, poll_interval=30,
                                            progress_callback=_bupdate
                                        )
                                        if _build and _build.result == "SUCCESS":
                                            console.print(f"\n[bold green]✓ Build #{_build_number} COMPLETED![/bold green]")
                                            
                                            _urls = jenkins.get_stack_urls(_branch_name, _build_number)
                                            stack = {
                                                'branch': _branch_name,
                                                'build': _build_number,
                                                'dnos_url': _urls.get('dnos'),
                                                'gi_url': _urls.get('gi'),
                                                'baseos_url': _urls.get('baseos'),
                                            }
                                            console.print(f"  DNOS: {'✓' if _urls.get('dnos') else '✗'}")
                                            console.print(f"  GI: {'✓' if _urls.get('gi') else '✗'}")
                                            console.print(f"  BaseOS: {'✓' if _urls.get('baseos') else '✗'}")
                                            console.print("\n[bold cyan]Continuing with upgrade...[/bold cyan]")
                                            # stack is set — falls through to the upgrade flow below
                                        elif _build:
                                            console.print(f"\n[red]✗ Build #{_build_number} {_build.result}[/red]")
                                            return False
                                        else:
                                            console.print("\n[yellow]Build timed out — check Jenkins manually[/yellow]")
                                            return False
                                except KeyboardInterrupt:
                                    console.print("\n[yellow]Detached. Build continues in Jenkins.[/yellow]")
                                    console.print("[dim]Use [T] Monitor Triggered Builds to check later.[/dim]")
                                    return run_image_upgrade_wizard(multi_ctx)
                            else:
                                console.print("[yellow]Build didn't start within 2 minutes. Check Jenkins.[/yellow]")
                                return False
                        else:
                            console.print(f"[red]✗ {_trig_msg}[/red]")
                            return False
                    elif _exp_sel == "b":
                        return run_image_upgrade_wizard(multi_ctx)
                    # _exp_sel == "2" falls through to fetch latest
                
                # Check if it's a URL entry (has non-empty url) or a branch entry
                if entry.get('url'):
                    console.print(f"[dim]Loading from URL...[/dim]")
                    stack = get_stack_from_url(entry['url'])
                else:
                    # It's a branch entry - fetch LATEST build from this branch
                    branch = entry.get('branch')
                    console.print(f"[dim]Loading branch {branch} (fetching latest build)...[/dim]")
                    
                    # Get the LATEST build, not the stored one
                    build_info = jenkins.get_last_successful_build(branch)
                    if build_info:
                        build_num = build_info.build_number
                        urls = jenkins.get_stack_urls(branch, build_num)
                        
                        # Show if newer than stored
                        stored_build = entry.get('build')
                        if stored_build and build_num > stored_build:
                            console.print(f"[green]✓ Newer build available: #{build_num} (was #{stored_build})[/green]")
                        
                        stack = {
                            'branch': branch, 
                            'build': build_num,
                            'dnos_url': urls.get('dnos'),
                            'gi_url': urls.get('gi'),
                            'baseos_url': urls.get('baseos'),
                        }
                    else:
                        console.print(f"[yellow]Could not fetch latest build for {branch}[/yellow]")
                        stack = None
        
        elif choice == "1":
            # Browse dev branches
            console.print("\n[dim]Loading development branches...[/dim]")
            branches = jenkins.list_dev_branches()
            if not branches:
                console.print("[yellow]No development branches found[/yellow]")
                return False
            
            console.print("\n[bold]Development Branches:[/bold]")
            console.print("[dim]Sorted by version (newest first)[/dim]\n")
            for i, b in enumerate(branches[:15], 1):
                console.print(f"  [{i}] {b.name} ({b.version})")
            console.print("  [B] Back")
            
            sel = Prompt.ask("Select", choices=[str(i) for i in range(1, min(16, len(branches)+1))] + ["b", "B"], default="b").lower()
            if sel == "b":
                return run_image_upgrade_wizard(multi_ctx)
            
            branch = branches[int(sel) - 1]
            stack = _select_build_from_branch(jenkins, branch.name, console)
            if stack is None:
                return run_image_upgrade_wizard(multi_ctx)
        
        elif choice == "2":
            # Browse release branches
            console.print("\n[dim]Loading release branches...[/dim]")
            branches = jenkins.list_release_branches()
            if not branches:
                console.print("[yellow]No release branches found[/yellow]")
                return False
            
            console.print("\n[bold]Release Branches:[/bold]")
            console.print("[dim]Sorted by version (newest first)[/dim]\n")
            for i, b in enumerate(branches[:15], 1):
                console.print(f"  [{i}] {b.name} ({b.version})")
            console.print("  [B] Back")
            
            sel = Prompt.ask("Select", choices=[str(i) for i in range(1, min(16, len(branches)+1))] + ["b", "B"], default="b").lower()
            if sel == "b":
                return run_image_upgrade_wizard(multi_ctx)
            
            branch = branches[int(sel) - 1]
            stack = _select_build_from_branch(jenkins, branch.name, console)
            if stack is None:
                return run_image_upgrade_wizard(multi_ctx)
        
        elif choice == "3":
            # Manual branch entry
            branch = Prompt.ask("Enter branch name (e.g., dev_v25_4_13, rel_v26_1, feature/dev_v26_2/my-feature)")
            if not branch:
                return False
            
            # Auto-detect if it's a URL
            if branch.startswith("http"):
                console.print("[dim]Detected URL, fetching...[/dim]")
                stack = get_stack_from_url(branch)
            else:
                # Normalize dots to underscores for dev_v*/rel_v* branches
                if re.match(r'^(dev|rel)_v\d+\.', branch):
                    normalized = branch.replace('.', '_')
                    console.print(f"[dim]Normalized: {branch} -> {normalized}[/dim]")
                    branch = normalized
                
                stack = _select_build_from_branch(jenkins, branch, console)
                if stack is None:
                    return run_image_upgrade_wizard(multi_ctx)
        
        elif choice == "4":
            # Jenkins URL
            url = Prompt.ask("Paste Jenkins URL")
            if not url:
                return False
            
            console.print("[dim]Fetching build info...[/dim]")
            stack = get_stack_from_url(url)
            
            if stack and not stack.get('error'):
                from urllib.parse import unquote as _url_unquote
                branch_name = _url_unquote(stack.get('branch', ''))
                build_num = stack.get('build')
                
                # Detect sanitizer from the resolved build
                if build_num and branch_name:
                    try:
                        resolved_build = jenkins.get_build_info(branch_name, build_num)
                        if resolved_build:
                            stack['_is_sanitizer'] = resolved_build.is_sanitizer
                            stack['_build_result'] = resolved_build.result
                            if resolved_build.is_sanitizer:
                                console.print(f"[yellow][ASAN] Build #{build_num} includes AddressSanitizer[/yellow]")
                            if resolved_build.result != 'SUCCESS':
                                console.print(f"[yellow][WARN] Build #{build_num} result: {resolved_build.result}[/yellow]")
                                console.print("[dim]  Build failed on tests, but image artifacts may still be usable.[/dim]")
                    except Exception:
                        pass
                
                # Offer to browse all builds for this branch
                if branch_name:
                    console.print(f"\n  [1] Use this build (#{build_num})")
                    console.print(f"  [2] Browse all recent builds for {branch_name}")
                    console.print(f"  [B] Back")
                    url_sel = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="1").lower()
                    if url_sel == "b":
                        return run_image_upgrade_wizard(multi_ctx)
                    elif url_sel == "2":
                        # Skip straight to the build table -- user already saw the resolved build
                        stack = _select_build_from_branch(jenkins, branch_name, console, skip_to_browse=True)
                        if stack is None:
                            return run_image_upgrade_wizard(multi_ctx)
        
        elif choice == "5":
            # Direct Minio URLs
            console.print("\n[bold]Enter Minio URLs:[/bold]")
            dnos_url = Prompt.ask("DNOS URL (required)")
            if not dnos_url:
                return False
            gi_url = Prompt.ask("GI URL (optional)", default="")
            baseos_url = Prompt.ask("BaseOS URL (optional)", default="")
            
            stack = {'dnos_url': dnos_url, 'gi_url': gi_url or None, 'baseos_url': baseos_url or None, 'branch': 'manual'}
        
        elif choice == "6":
            # Trigger new build
            console.print("\n[bold green]🔨 Trigger New Build[/bold green]")
            console.print("[dim]Enter branch name to build (e.g., dev_v26_1, feature/dev_v26_1/my-feature)[/dim]")
            branch = Prompt.ask("\nBranch name [B to cancel]")
            if not branch or branch.lower() == 'b':
                return run_image_upgrade_wizard(multi_ctx)
            
            console.print(f"\n[bold]Build Options for: {branch}[/bold]")
            with_baseos = Confirm.ask("Build with BaseOS containers?", default=True)
            qa_version = Confirm.ask("QA version (60-day retention)?", default=False)
            
            # Pre-select artifacts BEFORE triggering so user can walk away
            console.print(f"\n[bold]Pre-select Artifacts to Push:[/bold]")
            console.print("[dim]Choose now so install runs automatically after build completes[/dim]\n")
            pre_push_dnos = Confirm.ask("  Push DNOS?", default=True)
            pre_push_gi = Confirm.ask("  Push GI (Golden Image)?", default=True)
            pre_push_baseos = False
            if with_baseos:
                _is_dd = stack.get('_requires_delete_deploy', False) if 'stack' in dir() else False
                if _is_dd:
                    pre_push_baseos = Confirm.ask("  Push BaseOS? (required for delete+deploy)", default=True)
                else:
                    pre_push_baseos = Confirm.ask("  Push BaseOS? (usually not needed for in-place)", default=False)
            
            if not pre_push_dnos and not pre_push_gi and not pre_push_baseos:
                console.print("[yellow]No artifacts selected. Aborting.[/yellow]")
                return run_image_upgrade_wizard(multi_ctx)
            
            selected_names = []
            if pre_push_dnos: selected_names.append("DNOS")
            if pre_push_gi: selected_names.append("GI")
            if pre_push_baseos: selected_names.append("BaseOS")
            console.print(f"  [green]✓ Will push: {', '.join(selected_names)}[/green]")
            
            # Ask about auto-monitor and push
            console.print("\n[bold]After Build Completes:[/bold]")
            console.print("  [1] 🚀 Auto-monitor & push when complete (recommended)")
            console.print("  [2] 📊 Monitor only (push manually later)")
            console.print("  [3] ⏸️  Detach (build continues in background)")
            build_option = Prompt.ask("Select", choices=["1", "2", "3"], default="1")
            
            auto_push = (build_option == "1")
            
            # Now trigger the build
            console.print(f"\n[yellow]Triggering build for {branch}...[/yellow]")
            success, message = jenkins.trigger_build(branch, with_baseos=with_baseos, qa_version=qa_version)
            
            if success:
                console.print(f"[green]✓ {message}[/green]")
                multi_ctx._last_triggered_branch = branch
                multi_ctx._last_build_with_baseos = with_baseos
                multi_ctx._pre_push_dnos = pre_push_dnos
                multi_ctx._pre_push_gi = pre_push_gi
                multi_ctx._pre_push_baseos = pre_push_baseos
                console.print("\n[dim]Waiting for build to start...[/dim]")
                
                build_number = jenkins.wait_for_build_start(branch, timeout=120)
                if build_number:
                    console.print(f"[green]✓ Build #{build_number} started![/green]")
                    console.print(f"\n[cyan]Jenkins URL: {jenkins.CHEETAH_BASE}/job/{quote(quote(branch, safe=''), safe='')}/{build_number}/[/cyan]")
                    
                    if build_option == "3":
                        console.print("\n[cyan]Build running in background.[/cyan]")
                        console.print("[dim]Use [T] Monitor Triggered Builds to check status.[/dim]")
                        console.print(f"[dim]Pre-selected artifacts: {', '.join(selected_names)}[/dim]")
                        return run_image_upgrade_wizard(multi_ctx)
                    
                    console.print("\n[yellow]📊 Monitoring build progress...[/yellow]")
                    console.print("[dim]Press Ctrl+C to detach (build continues in Jenkins)[/dim]")
                    if auto_push:
                        console.print(f"[dim]Will auto-push [{', '.join(selected_names)}] to: {', '.join([d.hostname for d in multi_ctx.devices])}[/dim]\n")
                    
                    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
                    
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        BarColumn(),
                        TextColumn("{task.fields[status]}"),
                        console=console
                    ) as progress:
                        task = progress.add_task("Building...", total=100, status="Starting...")
                        
                        def update_progress(msg, pct):
                            progress.update(task, completed=pct, description=msg, status=f"{pct}%")
                        
                        try:
                            build = jenkins.wait_for_build_completion(branch, build_number, 
                                                                      timeout=3600, poll_interval=30,
                                                                      progress_callback=update_progress)
                            if build:
                                if build.result == "SUCCESS":
                                    console.print(f"\n[bold green]✓ Build #{build_number} COMPLETED SUCCESSFULLY![/bold green]")
                                    
                                    urls = jenkins.get_stack_urls(branch, build_number)
                                    console.print("\n[bold]Artifacts Available:[/bold]")
                                    console.print(f"  • DNOS: {'✓' if urls.get('dnos') else '✗'}")
                                    console.print(f"  • GI: {'✓' if urls.get('gi') else '✗'}")
                                    console.print(f"  • BaseOS: {'✓' if urls.get('baseos') else '✗ (not requested)'}")
                                    
                                    # Apply pre-selected artifact choices
                                    stack = {
                                        'branch': branch, 
                                        'build': build_number,
                                        'dnos_url': urls.get('dnos') if pre_push_dnos else None,
                                        'gi_url': urls.get('gi') if pre_push_gi else None,
                                        'baseos_url': urls.get('baseos') if pre_push_baseos else None,
                                    }
                                    
                                    if auto_push:
                                        console.print(f"\n[bold cyan]🚀 Auto-pushing pre-selected [{', '.join(selected_names)}] to devices...[/bold cyan]")
                                    else:
                                        console.print(f"\n[bold]Pre-selected: {', '.join(selected_names)}[/bold]")
                                        console.print("\n[bold]What would you like to do?[/bold]")
                                        console.print("  [1] Push pre-selected artifacts to devices now")
                                        console.print("  [2] Re-select artifacts")
                                        console.print("  [3] Return to menu (push later)")
                                        post_build = Prompt.ask("Select", choices=["1", "2", "3"], default="1")
                                        
                                        if post_build == "3":
                                            console.print("[dim]Return to Image Upgrade menu to push when ready.[/dim]")
                                            return run_image_upgrade_wizard(multi_ctx)
                                        elif post_build == "2":
                                            stack = {
                                                'branch': branch, 
                                                'build': build_number,
                                                'dnos_url': urls.get('dnos'),
                                                'gi_url': urls.get('gi'),
                                                'baseos_url': urls.get('baseos'),
                                            }
                                else:
                                    console.print(f"\n[red]✗ Build #{build_number} {build.result}[/red]")
                                    return False
                            else:
                                console.print("\n[yellow]Build timed out - check Jenkins manually[/yellow]")
                                return False
                        except KeyboardInterrupt:
                            console.print("\n[yellow]Detached from build monitoring. Build continues in Jenkins.[/yellow]")
                            console.print("[dim]Use [T] Monitor Triggered Builds to check status later.[/dim]")
                            console.print(f"[dim]Pre-selected artifacts: {', '.join(selected_names)}[/dim]")
                            return run_image_upgrade_wizard(multi_ctx)
                else:
                    console.print("[yellow]Build queued but not started yet. Check Jenkins manually.[/yellow]")
                    return False
            else:
                console.print(f"[red]✗ {message}[/red]")
                return False
        
        elif choice == "s":
            # Check upgrade status
            console.print("\n[bold cyan]📊 Checking Upgrade Status on Devices[/bold cyan]")
            _check_device_upgrade_status(multi_ctx)
            return run_image_upgrade_wizard(multi_ctx)
        
        elif choice == "i" and devices_with_targets:
            # Install target stacks directly (no new load needed)
            console.print("\n[bold green]⚡ Installing Target Stacks on Devices[/bold green]")
            _install_target_stack_on_devices(multi_ctx, devices_with_targets)
            return run_image_upgrade_wizard(multi_ctx)
        
        elif choice == "d" and gi_devices_with_targets:
            # Deploy target stacks on GI-mode devices
            console.print("\n[bold cyan]⚡ Deploying Target Stacks on GI Devices[/bold cyan]")
            _deploy_target_stack_on_gi_devices(multi_ctx, gi_devices_with_targets)
            return run_image_upgrade_wizard(multi_ctx)
        
        elif choice == "v":
            # Verify stacks live
            console.print("\n[bold cyan]🔄 Verifying Stacks Live from Devices[/bold cyan]")
            _verify_device_stacks_live(multi_ctx)
            return run_image_upgrade_wizard(multi_ctx)
        
        elif choice == "t":
            # Monitor triggered builds — if build completes, continue to upgrade flow
            _mon_result = _monitor_triggered_builds(jenkins, multi_ctx)
            if _mon_result:
                stack = _mon_result
            else:
                return run_image_upgrade_wizard(multi_ctx)
        
        elif choice == "r":
            # Restore pre-delete config
            _restore_pre_delete_configs(multi_ctx)
            return run_image_upgrade_wizard(multi_ctx)
        
        # Display stack info
        if not stack:
            console.print("[red]Could not find valid stack[/red]")
            return False
        
        if 'error' in stack:
            console.print(f"[red]Error: {stack['error']}[/red]")
            return False
        
        console.print(f"\n[green][OK] Found build:[/green]")
        console.print(f"  Branch: {stack.get('branch', 'N/A')}")
        _build_num_display = f"#{stack.get('build', 'N/A')}"
        _build_flags = []
        if stack.get('_is_sanitizer'):
            _build_flags.append("[yellow][ASAN][/yellow]")
        if stack.get('_build_result') and stack.get('_build_result') != 'SUCCESS':
            _build_flags.append(f"[red][{stack.get('_build_result')}][/red]")
        _flags_str = f" {' '.join(_build_flags)}" if _build_flags else ""
        console.print(f"  Build: {_build_num_display}{_flags_str}")
        console.print(f"  DNOS: {stack.get('dnos_url', 'N/A')[:60] + '...' if stack.get('dnos_url') else 'N/A'}")
        console.print(f"  GI: {stack.get('gi_url', 'N/A')[:60] + '...' if stack.get('gi_url') else 'N/A'}")
        console.print(f"  BaseOS: {stack.get('baseos_url', 'N/A')[:60] + '...' if stack.get('baseos_url') else 'N/A'}")
        
        # Check if artifacts are missing (N/A)
        dnos_missing = not stack.get('dnos_url') or stack.get('dnos_url') == 'N/A'
        gi_missing = not stack.get('gi_url') or stack.get('gi_url') == 'N/A'
        
        # Save to history immediately when a valid build is found (even if user doesn't proceed)
        # This makes it available in Recent Sources for next time
        if stack.get('branch') and (not dnos_missing or not gi_missing):
            try:
                _save_to_upgrade_history(
                    history_path, recent_urls, recent_branches, stack, choice,
                    url if choice == "4" else ""
                )
            except:
                pass  # Don't fail if history can't be saved
        
        if dnos_missing and gi_missing:
            console.print(f"\n[red]⚠ No artifacts found for this build![/red]")
            console.print("[dim]Build may have failed, or artifacts expired (48h retention).[/dim]")
            console.print("\n  [1] Trigger new build for this branch")
            console.print("  [2] Try a different source")
            console.print("  [B] Back")
            no_artifact_choice = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="1").lower()
            
            if no_artifact_choice == "1":
                branch = stack.get('branch', '')
                if branch and branch != 'manual':
                    console.print(f"\n[bold]Build Options for: {branch}[/bold]")
                    with_baseos = Confirm.ask("Build with BaseOS containers?", default=True)
                    qa_version = Confirm.ask("QA version (60-day retention)?", default=False)
                    
                    console.print(f"\n[yellow]Triggering new build for {branch}...[/yellow]")
                    success, message = jenkins.trigger_build(branch, with_baseos=with_baseos, qa_version=qa_version)
                    if success:
                        console.print(f"[green]✓ {message}[/green]")
                        console.print("[dim]Build will be available in 30-60 minutes.[/dim]")
                        console.print("[cyan]Run Image Upgrade again after build completes.[/cyan]")
                    else:
                        console.print(f"[red]✗ {message}[/red]")
                else:
                    console.print("[yellow]Cannot trigger build - no branch name available[/yellow]")
                return False
            elif no_artifact_choice == "2":
                return run_image_upgrade_wizard(multi_ctx)
            else:
                return False
        
        if stack.get('is_expired'):
            console.print(f"\n[yellow]⚠ Build is expired ({stack.get('age_hours', 0):.0f}h old)[/yellow]")
            console.print("  [1] Use anyway (may fail)")
            console.print("  [2] Trigger new build")
            console.print("  [B] Back")
            exp_choice = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="b").lower()
            if exp_choice == "b":
                return run_image_upgrade_wizard(multi_ctx)
            elif exp_choice == "2":
                branch = stack.get('branch', '')
                if branch and branch != 'manual':
                    console.print(f"\n[bold]Build Options for: {branch}[/bold]")
                    with_baseos = Confirm.ask("Build with BaseOS containers?", default=True)
                    qa_version = Confirm.ask("QA version (60-day retention)?", default=False)
                    
                    console.print(f"\n[yellow]Triggering new build for {branch}...[/yellow]")
                    success, message = jenkins.trigger_build(branch, with_baseos=with_baseos, qa_version=qa_version)
                    if success:
                        console.print(f"[green]✓ {message}[/green]")
                        console.print("[dim]Build will be available in 30-60 minutes.[/dim]")
                    else:
                        console.print(f"[red]✗ {message}[/red]")
                else:
                    console.print("[yellow]Cannot trigger build - no branch name available[/yellow]")
                return False
        
        # === VERSION JUMP DETECTION ===
        # Major version jumps (25.3→25.4, 25.x→26.x) require system delete + deploy
        def parse_version(ver_str: str) -> tuple:
            """Parse version string to (major, minor, patch) tuple."""
            if not ver_str or ver_str in ('Unknown', 'N/A'):
                return (0, 0, 0)
            # Clean up version string - extract numeric parts
            # Handle formats like: "25.3.0", "25.3.0.7_7", "DNOS 25.3.0"
            ver_str = ver_str.replace('DNOS', '').strip()
            ver_str = ver_str.split('_')[0]  # Remove build suffix
            parts = re.findall(r'\d+', ver_str)
            if len(parts) >= 3:
                return (int(parts[0]), int(parts[1]), int(parts[2]))
            elif len(parts) == 2:
                return (int(parts[0]), int(parts[1]), 0)
            elif len(parts) == 1:
                return (int(parts[0]), 0, 0)
            return (0, 0, 0)
        
        def is_major_version_jump(current: tuple, target: tuple) -> tuple:
            """
            Check if version jump requires system delete + deploy.
            
            Returns: (is_major_jump: bool, jump_type: str)
            
            Major jumps:
            - Different major version (25.x → 26.x)
            - Different minor version (25.3 → 25.4)
            """
            if current[0] == 0 or target[0] == 0:
                return (False, "unknown")
            
            if current[0] != target[0]:
                return (True, f"major branch ({current[0]}.x → {target[0]}.x)")
            
            if current[1] != target[1]:
                return (True, f"minor branch ({current[0]}.{current[1]} → {target[0]}.{target[1]})")
            
            return (False, "patch only")
        
        # Extract URLs from stack for use in version detection and later
        dnos_url = stack.get('dnos_url')
        gi_url = stack.get('gi_url')
        baseos_url = stack.get('baseos_url')
        
        # Extract target version from DNOS URL or branch name
        target_version_str = ""
        branch_name = stack.get('branch', '')
        if dnos_url and dnos_url != 'N/A':
            # Extract version from filename: drivenets_dnos_25.4.0.tar → 25.4.0
            ver_match = re.search(r'(\d+\.\d+\.\d+)', dnos_url)
            if ver_match:
                target_version_str = ver_match.group(1)
        if not target_version_str and branch_name:
            # Extract from branch: dev_v25.4 → 25.4
            ver_match = re.search(r'v?(\d+\.\d+)', branch_name)
            if ver_match:
                target_version_str = ver_match.group(1)
        
        target_version = parse_version(target_version_str)
        
        # Determine which devices have active DNOS (skip GI/RECOVERY/ONIE -- no stack to compare)
        _devices_with_dnos = set()
        for dev in multi_ctx.devices:
            try:
                _opf = Path(f"db/configs/{dev.hostname}/operational.json")
                if _opf.exists():
                    with open(_opf) as f:
                        _opd = json.load(f)
                    _ds = (_opd.get('device_state') or '').upper()
                    if _ds in ('GI', 'RECOVERY', 'DN_RECOVERY', 'BASEOS_SHELL', 'ONIE', 'DEPLOYING'):
                        continue
            except:
                pass
            _devices_with_dnos.add(dev.hostname)
        stack['_devices_with_dnos_set'] = _devices_with_dnos
        
        # Check each device for version jumps (only devices running DNOS)
        version_jumps = []
        for dev in multi_ctx.devices:
            if dev.hostname not in _devices_with_dnos:
                continue
            current_ver_str = device_stacks.get(dev.hostname, "Unknown")
            current_version = parse_version(current_ver_str)
            
            is_jump, jump_type = is_major_version_jump(current_version, target_version)
            if is_jump:
                version_jumps.append({
                    'hostname': dev.hostname,
                    'current': f"{current_version[0]}.{current_version[1]}.{current_version[2]}",
                    'target': f"{target_version[0]}.{target_version[1]}.{target_version[2]}",
                    'jump_type': jump_type
                })
        
        requires_delete_deploy = len(version_jumps) > 0
        
        # === EXACT VERSION MATCH DETECTION ===
        # Skip devices that are already running the exact target build
        _target_full = ''
        if dnos_url and dnos_url != 'N/A':
            _target_full = dnos_url.rstrip('/').split('/')[-1].replace('drivenets_dnos_', '').replace('.tar', '')
        
        _already_on_target = []
        for dev in multi_ctx.devices:
            if dev.hostname not in _devices_with_dnos:
                continue
            cur_full = device_stacks.get(dev.hostname, '')
            if cur_full and cur_full != 'Unknown' and _target_full and cur_full == _target_full:
                _already_on_target.append(dev.hostname)
        
        if _already_on_target:
            console.print(f"\n[bold green]✓ EXACT VERSION MATCH[/bold green]")
            console.print("[dim]The following devices are already running the target build:[/dim]\n")
            
            from rich.table import Table as RichTable
            skip_table = RichTable(box=box.ROUNDED)
            skip_table.add_column("Device", style="cyan")
            skip_table.add_column("Version", style="dim")
            skip_table.add_column("Action", style="green")
            
            for h in _already_on_target:
                skip_table.add_row(h, _target_full, "SKIP (already on target)")
            
            console.print(skip_table)
            
            console.print("\n[bold]Options:[/bold]")
            console.print("  [C] [green]Continue (skip these devices)[/green]")
            console.print("  [F] [yellow]Force upgrade all[/yellow] [dim](re-install even if version matches)[/dim]")
            console.print("  [B] Back")
            
            skip_choice = Prompt.ask("  Select", choices=['c', 'C', 'f', 'F', 'b', 'B'], default='c').lower()
            if skip_choice == 'b':
                return False
            elif skip_choice == 'c':
                stack['_skip_devices'] = set(_already_on_target)
                console.print(f"[dim]Will skip {len(_already_on_target)} device(s).[/dim]")
            else:
                stack['_skip_devices'] = set()
                console.print(f"[dim]Force upgrade enabled - will re-install on all devices.[/dim]")
        
        # === BRANCH SWITCH DETECTION ===
        # Same major.minor but different branch can cause DN_RECOVERY
        branch_switches = []
        if not requires_delete_deploy and dnos_url and dnos_url != 'N/A':
            from .stack_manager import StackManager as _SM
            _url_fname = dnos_url.rstrip('/').split('/')[-1].replace('drivenets_dnos_', '').replace('.tar', '')
            for dev in multi_ctx.devices:
                if dev.hostname not in _devices_with_dnos:
                    continue
                cur_full = device_stacks.get(dev.hostname, "")
                if cur_full and cur_full != "Unknown":
                    is_sw, cur_br, tgt_br = _SM.detect_branch_switch(cur_full, _url_fname)
                    if is_sw:
                        branch_switches.append({
                            'hostname': dev.hostname,
                            'current_full': cur_full,
                            'target_full': _url_fname,
                            'current_branch': cur_br,
                            'target_branch': tgt_br,
                        })
        
        if branch_switches and not requires_delete_deploy:
            console.print("\n[bold yellow]⚠ BRANCH SWITCH DETECTED[/bold yellow]")
            console.print("[yellow]Switching between development branches may require system delete + deploy.[/yellow]")
            console.print("[dim]In-place install can fail and cause DN_RECOVERY if branches are incompatible.[/dim]\n")
            
            from rich.table import Table as RichTable
            br_table = RichTable(title="Branch Switches", box=box.ROUNDED)
            br_table.add_column("Device", style="cyan")
            br_table.add_column("Current Branch", style="yellow")
            br_table.add_column("→", style="dim")
            br_table.add_column("Target Branch", style="green")
            for bs in branch_switches:
                br_table.add_row(bs['hostname'], bs['current_branch'], "→", bs['target_branch'])
            console.print(br_table)
            
            console.print("\n[bold]Options:[/bold]")
            console.print("  [D] [red]System Delete + Deploy[/red] [dim](safe — backs up config, wipes & re-deploys)[/dim]")
            console.print("  [I] [yellow]Try in-place install[/yellow] [dim](faster — may cause DN_RECOVERY if incompatible)[/dim]")
            console.print("  [B] Back")
            
            br_choice = Prompt.ask("  Select", choices=['d', 'D', 'i', 'I', 'b', 'B'], default='d').lower()
            if br_choice == 'b':
                return False
            elif br_choice == 'd':
                requires_delete_deploy = True
                stack['_requires_delete_deploy'] = True
                stack['_branch_switch'] = True
                console.print("[bold]Using system delete + deploy flow.[/bold]")
        
        if requires_delete_deploy and version_jumps:
            console.print("\n[bold red]⚠ MAJOR VERSION JUMP DETECTED[/bold red]")
            console.print("[yellow]This upgrade requires: system delete → deploy (not in-place upgrade)[/yellow]")
            console.print("")
            
            from rich.table import Table as RichTable
            jump_table = RichTable(title="Version Jumps", box=box.ROUNDED)
            jump_table.add_column("Device", style="cyan")
            jump_table.add_column("Current", style="yellow")
            jump_table.add_column("→", style="dim")
            jump_table.add_column("Target", style="green")
            jump_table.add_column("Jump Type", style="magenta")
            
            for j in version_jumps:
                jump_table.add_row(
                    j['hostname'],
                    j['current'],
                    "→",
                    j['target'],
                    j['jump_type']
                )
            console.print(jump_table)
            console.print("")
            
            # === VERSION COMPATIBILITY REPORT ===
            try:
                from .version_compat import build_compatibility_report, format_report_for_terminal
                for j in version_jumps:
                    compat_report = build_compatibility_report(j['current'], j['target'])
                    if compat_report['incompatible_count'] > 0:
                        console.print(format_report_for_terminal(compat_report))
                        console.print("")
                        stack['_compat_report'] = compat_report
                        stack['_source_version'] = j['current']
                        stack['_target_version'] = j['target']
                        break
            except Exception as e:
                console.print(f"[dim]Version compat check skipped: {e}[/dim]")
            
            if not Confirm.ask("[bold yellow]Proceed with system delete + deploy?[/bold yellow]", default=False):
                return False
            
            stack['_requires_delete_deploy'] = True
            console.print("")
        elif not requires_delete_deploy:
            if not Confirm.ask("\nProceed with upgrade?", default=False):
                return False
        
        # === AUTO-BACKUP CONFIG BEFORE ANY UPGRADE ===
        from pathlib import Path
        from datetime import datetime
        import shutil
        backup_configs = {}
        backup_label = "pre_delete" if requires_delete_deploy else "pre_upgrade"
        backup_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for dev in multi_ctx.devices:
            cached_config_path = Path(f"db/configs/{dev.hostname}/running.txt")
            backup_path = Path(f"db/configs/{dev.hostname}/{backup_label}_backup_{backup_ts}.txt")
            if cached_config_path.exists():
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(cached_config_path, backup_path)
                backup_configs[dev.hostname] = str(backup_path)
        
        if backup_configs:
            console.print(f"[dim]Auto-backed up {len(backup_configs)} config(s) -> db/configs/*/[/dim]")
            stack['_pre_delete_backups'] = backup_configs
        
        # Save pre-upgrade version to operational.json for each device
        # so the config sanitizer knows the source version during restore
        for dev in multi_ctx.devices:
            _cur_ver = device_stacks.get(dev.hostname, "")
            if _cur_ver and _cur_ver not in ('Unknown', 'N/A', ''):
                try:
                    _op_path = Path(f"db/configs/{dev.hostname}/operational.json")
                    _op_data = {}
                    if _op_path.exists():
                        with open(_op_path) as f:
                            _op_data = json.load(f)
                    _op_data['pre_upgrade_version'] = _cur_ver
                    _op_data['target_upgrade_version'] = target_version_str
                    with open(_op_path, 'w') as f:
                        json.dump(_op_data, f, indent=2)
                except Exception:
                    pass
        
        # === ARTIFACT SELECTION ===
        # Devices in GI/RECOVERY need all 3 images (same as delete+deploy)
        _needs_full_deploy = requires_delete_deploy or any(
            d.hostname not in _devices_with_dnos for d in multi_ctx.devices)
        
        console.print("\n[bold]Select Artifacts to Push:[/bold]")
        if _needs_full_deploy:
            console.print("[yellow]Deploy from GI/RECOVERY requires all 3 images (DNOS + GI + BaseOS)[/yellow]\n")
        else:
            console.print("[dim]Choose which components to upgrade on devices[/dim]\n")
        
        dnos_url = stack.get('dnos_url')
        gi_url = stack.get('gi_url')
        baseos_url = stack.get('baseos_url')
        
        dnos_available = dnos_url and dnos_url != 'N/A'
        gi_available = gi_url and gi_url != 'N/A'
        baseos_available = baseos_url and baseos_url != 'N/A'
        
        # Helper to extract clean artifact name from URL
        def get_artifact_name(url):
            if not url:
                return "N/A"
            # Get filename from URL (last part)
            filename = url.split('/')[-1] if '/' in url else url
            # Remove .tar extension
            if filename.endswith('.tar'):
                filename = filename[:-4]
            # Truncate if too long
            return filename[:55] + "..." if len(filename) > 55 else filename
        
        # Show available artifacts with selection
        push_dnos = False
        push_gi = False
        push_baseos = False
        
        if dnos_available:
            dnos_name = get_artifact_name(dnos_url)
            console.print(f"  [green]✓[/green] DNOS: {dnos_name}")
            push_dnos = Confirm.ask(f"    Push DNOS?", default=True)
        else:
            console.print("  [red]✗[/red] [dim]DNOS: Not available[/dim]")
        
        if gi_available:
            gi_name = get_artifact_name(gi_url)
            console.print(f"  [green]✓[/green] GI: {gi_name}")
            push_gi = Confirm.ask(f"    Push GI (Golden Image)?", default=True)
        else:
            console.print("  [red]✗[/red] [dim]GI: Not available[/dim]")
        
        if baseos_available:
            baseos_name = get_artifact_name(baseos_url)
            console.print(f"  [green]✓[/green] BaseOS: {baseos_name}")
            if _needs_full_deploy:
                push_baseos = Confirm.ask(f"    Push BaseOS? (required for GI/deploy)", default=True)
            else:
                push_baseos = Confirm.ask(f"    Push BaseOS? (usually not needed for in-place)", default=False)
        else:
            if _needs_full_deploy:
                console.print("  [red]✗[/red] [yellow]BaseOS: Not available (required for GI/deploy!)[/yellow]")
            else:
                console.print("  [red]✗[/red] [dim]BaseOS: Not available[/dim]")
        
        if not push_dnos and not push_gi and not push_baseos:
            console.print("[yellow]No artifacts selected. Aborting.[/yellow]")
            return False
        
        # Update stack with user selections
        if not push_dnos:
            stack['dnos_url'] = None
        if not push_gi:
            stack['gi_url'] = None
        if not push_baseos:
            stack['baseos_url'] = None
        
        # Summary of what will be pushed
        selected = []
        if push_dnos:
            selected.append("DNOS")
        if push_gi:
            selected.append("GI")
        if push_baseos:
            selected.append("BaseOS")
        
        console.print(f"\n[green]✓ Selected: {', '.join(selected)}[/green]")
        
        # === VALIDATE ARTIFACT URLs AND AUTO-FIND NEWER BUILDS IF INVALID ===
        from .jenkins_integration import validate_artifact_url
        from rich.progress import Progress as ValidationProgress, SpinnerColumn, TextColumn
        
        max_retry_builds = 5  # Check up to 5 newer builds
        retry_count = 0
        original_build = stack.get('build')
        original_branch = stack.get('branch')
        validation_errors = []  # Initialize outside loop
        
        while retry_count <= max_retry_builds:
            console.print("\n[bold cyan]🔍 Validating Artifact URLs...[/bold cyan]")
            
            validation_errors = []  # Reset for each iteration
            urls_to_validate = []
            
            if push_dnos and stack.get('dnos_url'):
                urls_to_validate.append(("DNOS", stack.get('dnos_url')))
            if push_gi and stack.get('gi_url'):
                urls_to_validate.append(("GI", stack.get('gi_url')))
            if push_baseos and stack.get('baseos_url'):
                urls_to_validate.append(("BaseOS", stack.get('baseos_url')))
            
            validation_results = []
            with ValidationProgress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as validation_progress:
                for artifact_name, url in urls_to_validate:
                    task = validation_progress.add_task(f"[cyan]Validating {artifact_name}...", total=None)
                    is_valid, message = validate_artifact_url(url, timeout=15)
                    validation_results.append((artifact_name, url, is_valid, message))
                    
                    if is_valid:
                        validation_progress.update(task, description=f"[green]{artifact_name}: {message}[/green]")
                    else:
                        validation_progress.update(task, description=f"[red]{artifact_name}: {message}[/red]")
                        validation_errors.append((artifact_name, url, message))
            
            for artifact_name, url, is_valid, message in validation_results:
                if is_valid:
                    console.print(f"  [green]✓ {artifact_name}:[/green] {message}")
                else:
                    console.print(f"  [red]✗ {artifact_name}:[/red] {message}")
            
            if not validation_errors:
                # All URLs valid!
                if retry_count > 0:
                    console.print(f"\n[green]✓ Found valid images in build #{stack.get('build')}[/green]")
                else:
                    console.print("[green]✓ All artifacts validated successfully![/green]")
                break
            
            # Some URLs are invalid - try to find newer build
            if retry_count < max_retry_builds and original_branch:
                retry_count += 1
                console.print(f"\n[yellow]⚠ Some artifacts are invalid. Searching for newer build with valid images...[/yellow]")
                
                try:
                    # Get the latest successful build from the branch
                    latest_build_info = jenkins.get_last_successful_build(original_branch)
                    
                    if latest_build_info and latest_build_info.build_number > original_build:
                        # Get URLs for the latest build
                        latest_urls = jenkins.get_stack_urls(original_branch, latest_build_info.build_number)
                        
                        console.print(f"[cyan]Checking latest build #{latest_build_info.build_number}...[/cyan]")
                        
                        # Update stack with latest build
                        stack['build'] = latest_build_info.build_number
                        stack['dnos_url'] = latest_urls.get('dnos') if push_dnos else None
                        stack['gi_url'] = latest_urls.get('gi') if push_gi else None
                        stack['baseos_url'] = latest_urls.get('baseos') if push_baseos else None
                        
                        console.print(f"[green]✓ Found newer build #{latest_build_info.build_number}[/green]")
                        continue
                    else:
                        # No newer successful build found
                        console.print(f"[yellow]No newer successful build found (latest is #{latest_build_info.build_number if latest_build_info else 'N/A'})[/yellow]")
                        break
                except Exception as e:
                    console.print(f"[yellow]Error checking for newer build: {str(e)[:50]}[/yellow]")
                    break
            else:
                # No more retries or no branch info
                break
        
        # Final check - if still invalid, show error and abort
        if validation_errors:
            console.print("\n[bold red]❌ Validation Failed![/bold red]")
            console.print("[yellow]The following artifacts are not accessible:[/yellow]")
            for artifact_name, url, error_msg in validation_errors:
                console.print(f"  • [red]{artifact_name}[/red]: {error_msg}")
                console.print(f"    [dim]URL: {url[:80]}...[/dim]")
            console.print("\n[yellow]Possible reasons:[/yellow]")
            console.print("  • Artifact expired (MinIO 48h retention)")
            console.print("  • Build was deleted")
            console.print("  • Network connectivity issue")
            console.print("  • Invalid URL")
            console.print("\n[dim]Please select a different build or source.[/dim]")
            return False
        
        # For GI/RECOVERY devices: confirm deploy params (hostname + system-type)
        # These are needed for: request system deploy system-type <T> name <N> ncc-id <auto>
        _gi_deploy_params = {}
        _gi_devices = [d for d in multi_ctx.devices if d.hostname not in _devices_with_dnos]
        if _gi_devices:
            console.print("\n[bold cyan]═══ GI/Recovery Deploy Configuration ═══[/bold cyan]")
            console.print("[dim]These devices need hostname and system-type for the deploy command.[/dim]\n")
            
            for _gd in _gi_devices:
                _cached_type = None
                _cached_name = _gd.hostname
                try:
                    _opf = Path(f"db/configs/{_gd.hostname}/operational.json")
                    if _opf.exists():
                        with open(_opf) as f:
                            _opd = json.load(f)
                        _cached_type = _opd.get('system_type') or _opd.get('deploy_system_type')
                        _sn = _opd.get('deploy_name') or _opd.get('pre_delete_hostname')
                        if _sn:
                            _cached_name = _sn
                except:
                    pass
                
                if not _cached_type or _cached_type == 'N/A':
                    _cached_type = _gd.platform.value if hasattr(_gd, 'platform') else 'SA-36CD-S'
                
                console.print(f"  [bold cyan]{_gd.hostname}[/bold cyan]")
                _deploy_name = Prompt.ask(
                    f"    Deploy hostname", default=_cached_name)
                _deploy_type = Prompt.ask(
                    f"    System type", default=_cached_type)
                
                _gi_deploy_params[_gd.hostname] = {
                    'deploy_name': _deploy_name,
                    'system_type': _deploy_type,
                }
                console.print(f"    [green]→ deploy system-type {_deploy_type} name {_deploy_name}[/green]\n")
            
            stack['_gi_deploy_params'] = _gi_deploy_params
        
        # Push images to devices
        console.print(f"\n[bold green]🚀 Pushing Stack to Devices[/bold green]")
        
        dnos_url = stack.get('dnos_url')
        gi_url = stack.get('gi_url')
        baseos_url = stack.get('baseos_url')
        
        # Display what will be pushed
        if dnos_url and dnos_url != 'N/A':
            dnos_name = dnos_url.split('/')[-2] if '/' in dnos_url else dnos_url[:50]
            console.print(f"  [cyan]DNOS:[/cyan] {dnos_name}")
        if gi_url and gi_url != 'N/A':
            gi_name = gi_url.split('/')[-2] if '/' in gi_url else gi_url[:50]
            console.print(f"  [cyan]GI:[/cyan] {gi_name}")
        if baseos_url and baseos_url != 'N/A':
            baseos_name = baseos_url.split('/')[-2] if '/' in baseos_url else baseos_url[:50]
            console.print(f"  [cyan]BaseOS:[/cyan] {baseos_name}")
        
        console.print(f"  [cyan]Devices:[/cyan] {', '.join(d.hostname for d in multi_ctx.devices)}")
        
        # Per-device action plan for mixed-mode awareness
        _dnos_set = stack.get('_devices_with_dnos_set', set())
        _mixed_modes = False
        _per_device_flows = {}
        for _pd in multi_ctx.devices:
            _pd_state = 'DNOS'
            try:
                _pd_opf = Path(f"db/configs/{_pd.hostname}/operational.json")
                if _pd_opf.exists():
                    with open(_pd_opf) as f:
                        _pd_op = json.load(f)
                    _pd_state = (_pd_op.get('device_state', '') or 'DNOS').upper()
                    if _pd_state in ('', 'UNKNOWN'):
                        _pd_state = 'DNOS' if _pd.hostname in _dnos_set else 'GI'
            except Exception:
                pass
            
            if _pd.hostname in stack.get('_skip_devices', set()):
                _per_device_flows[_pd.hostname] = ('already on target (skip)', _pd_state, 'magenta')
            elif stack.get('_requires_delete_deploy', False) and _pd.hostname in _dnos_set:
                _per_device_flows[_pd.hostname] = ('delete + deploy', _pd_state, 'red')
            elif _pd_state in ('GI', 'BASEOS_SHELL', 'ONIE', 'DN_RECOVERY', 'RECOVERY', 'DEPLOYING'):
                _per_device_flows[_pd.hostname] = ('GI deploy', _pd_state, 'cyan')
            else:
                _per_device_flows[_pd.hostname] = ('in-place upgrade', _pd_state, 'green')
        
        _flow_set = set(f[0] for f in _per_device_flows.values())
        _mixed_modes = len(_flow_set) > 1
        
        if _mixed_modes or any(f[0] != 'in-place upgrade' for f in _per_device_flows.values()):
            _plan_table = Table(title="Per-Device Upgrade Plan", box=box.SIMPLE)
            _plan_table.add_column("Device", style="cyan")
            _plan_table.add_column("Current State", style="dim")
            _plan_table.add_column("Upgrade Action", style="bold")
            _plan_table.add_column("Details", style="dim")
            
            for _pd_h, (_pd_flow, _pd_st, _pd_color) in _per_device_flows.items():
                if _pd_flow == 'delete + deploy':
                    _details = "system delete -> GI -> load images -> deploy"
                elif _pd_flow == 'GI deploy':
                    _details = "load images -> deploy (already in GI)"
                elif _pd_flow == 'already on target (skip)':
                    _details = "no action needed (exact match)"
                else:
                    _details = "request system install -> automatic"
                _plan_table.add_row(
                    _pd_h, _pd_st,
                    f"[{_pd_color}]{_pd_flow}[/{_pd_color}]",
                    _details
                )
            
            console.print()
            console.print(_plan_table)
            
            if _mixed_modes:
                console.print(f"\n[bold yellow][!!] Mixed modes detected:[/bold yellow] "
                              f"devices will follow different upgrade paths.")
                console.print("[dim]Each device is handled independently in parallel. "
                              "GI/recovery devices go straight to deploy, DNOS devices "
                              f"{'need system delete first' if stack.get('_requires_delete_deploy') else 'use in-place install'}.[/dim]")
        
        # Data-driven time estimate from past upgrades
        _is_dd = stack.get('_requires_delete_deploy', False)
        _any_gi = any(
            d.hostname not in stack.get('_devices_with_dnos_set', set())
            for d in multi_ctx.devices
        ) if '_devices_with_dnos_set' in stack else False
        _flow_type = 'delete_deploy' if _is_dd else ('gi_deploy' if _any_gi else 'in_place')
        
        _hist_times = []  # seconds
        _hist_label = ""
        try:
            # Read history file first
            _hf = Path("db/upgrade_history.json")
            if _hf.exists():
                with open(_hf) as f:
                    _hist = json.load(f)
                for _he in _hist.get('entries', []):
                    if _he.get('flow_type') == _flow_type and _he.get('elapsed_s', 0) > 0:
                        _hist_times.append(_he['elapsed_s'])
            
            # Also scan operational.json for past timings
            for _opdir in Path("db/configs").iterdir():
                _opj = _opdir / "operational.json"
                if _opj.exists():
                    with open(_opj) as f:
                        _opd = json.load(f)
                    _ie = _opd.get('install_elapsed', '')
                    _it = _opd.get('install_type', '')
                    if _ie and ':' in _ie:
                        parts = _ie.split(':')
                        _secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2].split('.')[0])
                        if _secs > 0:
                            _matches = False
                            if _flow_type == 'in_place' and _it in ('upgrade', 'in_place', ''):
                                _matches = True
                            elif _flow_type in ('delete_deploy', 'gi_deploy') and _it in ('gi_deploy', 'deploy', 'delete_deploy'):
                                _matches = True
                            if _matches and _secs not in _hist_times:
                                _hist_times.append(_secs)
        except Exception:
            pass
        
        total_est_seconds = 600  # default 10 min
        if _hist_times:
            _avg_s = sum(_hist_times) / len(_hist_times)
            _max_s = max(_hist_times)
            if _flow_type == 'delete_deploy':
                _est_s = _max_s + 300  # delete adds ~5min on top of deploy
                _est_label = "delete + deploy"
            else:
                _est_s = _avg_s
                _est_label = "GI deploy" if _flow_type == 'gi_deploy' else "in-place"
            total_est_seconds = int(_est_s)
            _em, _es = divmod(int(_est_s), 60)
            _hist_label = f"[dim](based on {len(_hist_times)} past upgrade{'s' if len(_hist_times) > 1 else ''})[/dim]"
            console.print(f"\n[dim]Estimated time: ~{_em}m {_es:02d}s per device ({_est_label}) {_hist_label}[/dim]")
        else:
            _defaults = {'in_place': (5, 'in-place'), 'gi_deploy': (15, 'GI deploy'), 'delete_deploy': (20, 'delete + deploy')}
            _def_min, _def_label = _defaults.get(_flow_type, (10, 'upgrade'))
            total_est_seconds = _def_min * 60
            console.print(f"\n[dim]Estimated time: ~{_def_min}m per device ({_def_label}) (no history yet)[/dim]")
        
        console.print("[dim]This runs on SERVER - safe to close Cursor.[/dim]\n")
        
        # Check for recovery mode devices BEFORE starting push
        import paramiko
        import base64
        recovery_devices = []
        
        console.print("[cyan]🔍 Checking device status...[/cyan]")
        for device in multi_ctx.devices:
            try:
                ssh_check = paramiko.SSHClient()
                ssh_check.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                password = device.password
                if device.password:
                    try:
                        password = base64.b64decode(device.password).decode('utf-8')
                    except:
                        pass
                
                ssh_check.connect(device.ip, username=device.username or 'dnroot', password=password, timeout=10,
                                  allow_agent=False, look_for_keys=False)
                channel_check = ssh_check.invoke_shell(width=200, height=50)
                time.sleep(1)
                initial_check = channel_check.recv(65535).decode('utf-8', errors='replace')
                
                if 'RECOVERY' in initial_check or 'dnRouter(RECOVERY)' in initial_check:
                    recovery_devices.append(device)
                
                ssh_check.close()
            except Exception as e:
                # Connection failed - will be handled during actual push
                # Don't print error here as it might contain Rich markup
                pass
        
        # PE-2: include console-detected recovery (synced from Refresh when SSH failed)
        for device in multi_ctx.devices:
            if device.hostname == "PE-2" and device not in recovery_devices:
                try:
                    op_file = Path(f"db/configs/PE-2/operational.json")
                    if op_file.exists():
                        with open(op_file) as f:
                            d = json.load(f)
                        if d.get("console_recovery_detected") is True:
                            recovery_devices.append(device)
                except Exception:
                    pass
        
        # If any devices are in recovery mode, prompt user
        if recovery_devices:
            console.print("\n[bold red]⚠ RECOVERY MODE DETECTED[/bold red]")
            for dev in recovery_devices:
                console.print(f"  • [red]{dev.hostname}[/red] is in RECOVERY mode")
            
            console.print("\n[bold yellow]What will happen if you proceed:[/bold yellow]")
            console.print("  1. [yellow]Save deployment parameters[/yellow] (system-type, hostname) before restore")
            console.print("  2. [yellow]Execute 'request system restore factory-default'[/yellow] (restores to factory defaults)")
            console.print("  3. [yellow]Wait for GI mode[/yellow] (device reboots, ~2-5 minutes)")
            console.print("  4. [yellow]Load new images[/yellow] (DNOS, GI, BaseOS)")
            console.print("  5. [yellow]Deploy fresh DNOS[/yellow] using 'request system deploy'")
            console.print("\n[dim]Note: All configuration will be lost. Deployment parameters (system-type, hostname) are saved for the deploy command.[/dim]\n")
            
            if not Confirm.ask(f"[bold yellow]Proceed with fresh deployment for {len(recovery_devices)} device(s) in recovery mode?[/bold yellow]", default=False):
                console.print("[yellow]Upgrade cancelled by user.[/yellow]")
                return False
        
        # Execute push using paramiko
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from rich.live import Live
        from rich.layout import Layout
        from rich.panel import Panel
        from rich.text import Text
        import threading
        
        progress_lock = threading.Lock()
        device_progress = {dev.hostname: {
            'status': 'pending',
            'progress': 0,
            'stage': 'Connecting...',
            'terminal_lines': [],
            'error': None,
            'elapsed': 0,
        } for dev in multi_ctx.devices}
        
        start_time = time.time()
        
        def render_multi_device_panel():
            """Render fixed-height panel for device upgrade progress."""
            from rich.table import Table
            from datetime import datetime
            
            panels = []
            num_devices = len(multi_ctx.devices)
            
            if num_devices == 1:
                panel_height = 18
                panel_width = 70
                terminal_lines_count = 8
            elif num_devices == 2:
                panel_height = 16
                panel_width = 60
                terminal_lines_count = 5
            elif num_devices == 3:
                panel_height = 14
                panel_width = 50
                terminal_lines_count = 4
            else:
                panel_height = 12
                panel_width = 45
                terminal_lines_count = 3
            
            for dev in multi_ctx.devices:
                with progress_lock:
                    info = device_progress[dev.hostname].copy()  # Copy to avoid lock issues
                
                status_icon = {'pending': '⏳', 'loading': '📥', 'installing': '🔧', 'success': '✅', 'failed': '❌'}.get(info['status'], '⏳')
                status_color = {'pending': 'yellow', 'loading': 'cyan', 'installing': 'yellow', 'success': 'green', 'failed': 'red'}.get(info['status'], 'white')
                
                lines = []
                
                # Header with status
                lines.append(f"{status_icon} {info['status'].upper()}")
                
                # Progress bar
                pct = info['progress']
                bar_width = 25
                filled = int(bar_width * pct / 100)
                bar = '█' * filled + '░' * (bar_width - filled)
                lines.append(f"[{bar}] {pct}%")
                
                elapsed = int(time.time() - start_time)
                mins, secs = divmod(elapsed, 60)
                est_remaining = max(0, total_est_seconds - elapsed)
                rem_mins, rem_secs = divmod(est_remaining, 60)
                lines.append(f"⏱ {mins:02d}:{secs:02d} elapsed | ~{rem_mins:02d}:{rem_secs:02d} remaining")
                lines.append("")
                
                # Current stage with timestamp
                now = datetime.now().strftime("%H:%M:%S")
                lines.append(f"[{now}] {info['stage']}")
                
                # Error if any
                if info.get('error'):
                    lines.append(f"❌ ERROR: {info['error'][:50]}")
                
                lines.append("─" * (panel_width - 6))
                
                # Terminal output - FIXED number of lines (pad if needed)
                term_lines = info.get('terminal_lines', [])[-terminal_lines_count:]
                while len(term_lines) < terminal_lines_count:
                    term_lines.append("")  # Pad with empty lines
                
                max_line_len = panel_width - 8
                for tl in term_lines:
                    lines.append(tl[:max_line_len] if tl else "")
                
                # Build content with fixed lines
                content = Text()
                for line in lines:
                    content.append(line + "\n")
                
                panels.append(Panel(
                    content, 
                    title=f"─── {dev.hostname} ───", 
                    height=panel_height, 
                    width=panel_width, 
                    border_style=status_color
                ))
            
            from rich.columns import Columns
            from rich.console import Group
            
            if num_devices == 1:
                return panels[0]  # Single panel, no columns
            elif num_devices <= 3:
                return Columns(panels, expand=True, equal=True)  # Side by side
            else:
                # Grid layout: 2 columns per row (4+ devices)
                rows = []
                for i in range(0, len(panels), 2):
                    row_panels = panels[i:i+2]
                    rows.append(Columns(row_panels, expand=True, equal=True))
                return Group(*rows)
        
        def push_to_device(device):
            from datetime import datetime
            hostname = device.hostname
            is_gi_mode = False
            system_type = None
            
            try:
                if hostname in stack.get('_skip_devices', set()):
                    with progress_lock:
                        device_progress[hostname]['status'] = 'success'
                        device_progress[hostname]['stage'] = 'Skipped (already on target)'
                        device_progress[hostname]['progress'] = 100
                    return True, "Skipped (already on target)"
                
                with progress_lock:
                    device_progress[hostname]['status'] = 'loading'
                    device_progress[hostname]['stage'] = 'Connecting to device...'
                
                # Get system_type from operational.json (needed for GI deploy)
                # This persists even when device goes to GI mode
                try:
                    op_file = Path(f"db/configs/{hostname}/operational.json")
                    if op_file.exists():
                        with open(op_file) as f:
                            op_data = json.load(f)
                            system_type = op_data.get('system_type')
                            if system_type == 'N/A':
                                system_type = None
                except:
                    pass
                
                # Fallback: Try to parse from config header (# • Type: SA-36CD-S)
                if not system_type:
                    try:
                        config = multi_ctx.configs.get(hostname, "")
                        type_match = re.search(r'#\s*•?\s*Type:\s*(\S+)', config)
                        if type_match:
                            system_type = type_match.group(1)
                    except:
                        pass
                
                # Final fallback: use a common type or device.platform
                if not system_type:
                    system_type = (device.system_type or device.platform or 'SA-36CD-S') if hasattr(device, 'platform') else 'SA-36CD-S'
                
                # Override with user-confirmed GI deploy params if available
                deploy_hostname = hostname
                _gdp = stack.get('_gi_deploy_params', {}).get(hostname)
                if _gdp:
                    system_type = _gdp['system_type']
                    deploy_hostname = _gdp['deploy_name']
                
                def get_timestamp():
                    """Get current time as HH:MM:SS."""
                    from datetime import datetime
                    return datetime.now().strftime("%H:%M:%S")
                
                def sanitize_terminal(text):
                    """Remove ANSI escape codes and control characters from terminal output."""
                    import re
                    # Remove ANSI escape sequences
                    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                    text = ansi_escape.sub('', text)
                    # Remove carriage returns and other control chars
                    text = text.replace('\r', '').replace('\x00', '')
                    # Remove any remaining non-printable chars except newline
                    text = ''.join(c for c in text if c == '\n' or (ord(c) >= 32 and ord(c) < 127))
                    return text.strip()
                
                def add_terminal_line(msg):
                    """Add a timestamped line to terminal output."""
                    # Sanitize and take first line only
                    msg = sanitize_terminal(str(msg))
                    if '\n' in msg:
                        msg = msg.split('\n')[0]
                    msg = msg[:50]  # Truncate to fit panel
                    
                    with progress_lock:
                        # Limit terminal lines to prevent memory growth
                        if len(device_progress[hostname]['terminal_lines']) > 50:
                            device_progress[hostname]['terminal_lines'] = device_progress[hostname]['terminal_lines'][-30:]
                        if msg:  # Only add non-empty lines
                            device_progress[hostname]['terminal_lines'].append(f"[{get_timestamp()}] {msg}")

                # Connect via unified path (SSH, console, virsh) for all device types
                from .connection_strategy import connect_for_upgrade
                conn = connect_for_upgrade(hostname, timeout=30)
                
                if not conn['connected'] or not conn['verified']:
                    reason = conn.get('abort_reason') or 'Connection failed'
                    with progress_lock:
                        device_progress[hostname]['status'] = 'failed'
                        device_progress[hostname]['error'] = reason[:60]
                        device_progress[hostname]['stage'] = reason[:80]
                    return False, f"SAFETY: {reason}"
                
                ssh = conn['ssh']
                channel = conn['channel']
                initial_output = conn['prompt_output']
                
                method_used = conn.get('method', 'Unknown')
                if hasattr(method_used, 'value'):
                    method_used = method_used.value
                add_terminal_line(f"Connected via {method_used}")
                
                # Update system_type from live data if available
                
                # Log system type
                add_terminal_line(f"System: {system_type}")
                
                # Per-device delete decision: only DNOS devices need system delete
                # GI/RECOVERY devices already had DNOS removed -- skip delete, go straight to load+deploy
                _dnos_devices = stack.get('_devices_with_dnos_set', set())
                requires_delete_deploy = (stack.get('_requires_delete_deploy', False)
                                          and hostname in _dnos_devices)
                
                # Also skip delete if connect_for_upgrade already detected GI/BASEOS state
                if requires_delete_deploy and conn.get('device_state') in ('GI', 'BASEOS_SHELL'):
                    requires_delete_deploy = False
                    is_gi_mode = True
                    add_terminal_line(f"Device already in GI mode -- skipping system delete")
                
                # Detect RECOVERY mode - user already confirmed, proceed with delete
                is_recovery_mode = 'RECOVERY' in initial_output or 'dnRouter(RECOVERY)' in initial_output
                if is_recovery_mode:
                    add_terminal_line("⚠ RECOVERY MODE DETECTED")
                    add_terminal_line("🔄 Executing system delete (user confirmed)...")
                    
                    # Save system_type and hostname BEFORE delete for deploy command later
                    add_terminal_line(f"💾 Saving deploy params: {system_type}, {hostname}")
                    try:
                        op_file = Path(f"db/configs/{hostname}/operational.json")
                        op_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        op_data = {}
                        if op_file.exists():
                            with open(op_file) as f:
                                op_data = json.load(f)
                        
                        _detected_ncc = conn.get('ncc_id') if conn.get('ncc_id') is not None else 0
                        _update = {
                            'deploy_system_type': system_type,
                            'deploy_name': deploy_hostname,
                            'deploy_ncc_id': str(_detected_ncc),
                            'deploy_command': f"request system deploy system-type {system_type} name {deploy_hostname} ncc-id {_detected_ncc}",
                            'pre_delete_system_type': system_type,
                            'pre_delete_hostname': deploy_hostname,
                            'delete_initiated': datetime.now().isoformat(),
                            'recovery_mode_detected': True,
                            'device_state': 'GI',
                            'recovery_type': 'GI',
                            'recovery_mode_detected_at': datetime.now().isoformat()
                        }
                        try:
                            from .connection_strategy import get_console_config_for_device
                            _ccfg = get_console_config_for_device(hostname)
                            if _ccfg and _ccfg.get('port'):
                                _update['connection_method'] = f"Console ({_ccfg.get('console_server_name', 'console')} p{_ccfg['port']})"
                        except ImportError:
                            pass
                        op_data.update(_update)
                        
                        with open(op_file, 'w') as f:
                            json.dump(op_data, f, indent=4)
                        add_terminal_line("✓ Deploy params saved")
                    except Exception as save_err:
                        add_terminal_line(f"⚠ Save failed: {str(save_err)[:30]}")
                    
                    with progress_lock:
                        device_progress[hostname]['stage'] = 'RECOVERY: Executing system restore...'
                    
                    # Define send_and_wait helper for delete command
                    def send_and_wait_temp(cmd, wait_time=5):
                        """Temporary send and wait for delete command."""
                        channel.sendall((cmd + "\n").encode('utf-8'))
                        time.sleep(wait_time)
                        output = ""
                        while channel.recv_ready():
                            output += channel.recv(65535).decode('utf-8', errors='replace')
                            time.sleep(0.3)
                        return output
                    
                    # In RECOVERY mode, use 'request system restore factory-default' 
                    # RECOVERY mode doesn't support 'delete' command - use 'restore factory-default' to factory defaults
                    add_terminal_line("⚠ RECOVERY mode: Using 'request system restore factory-default'")
                    send_and_wait_temp("request system restore factory-default", wait_time=3)
                    # Answer confirmation prompt
                    send_and_wait_temp("yes", wait_time=2)  # Confirm "Do you want to continue? (yes/no) [no]?"
                    add_terminal_line("✓ System restore factory-default confirmed")
                    
                    # Wait for GI mode (device reboots into GI)
                    with progress_lock:
                        device_progress[hostname]['stage'] = 'RECOVERY: Waiting for GI mode...'
                    add_terminal_line("⏳ Waiting for GI mode (device rebooting)...")
                    
                    # Close current connection
                    ssh.close()
                    
                    # Wait and reconnect (system restore can take 5-15 minutes)
                    gi_mode_timeout = 900  # 15 minutes (increased from 5)
                    gi_check_interval = 20  # Check every 20 seconds (faster detection)
                    gi_start = time.time()
                    gi_connected = False
                    consecutive_failures = 0
                    max_consecutive_failures = 3  # Allow some connection failures during reboot
                    
                    add_terminal_line(f"⏳ Will wait up to {gi_mode_timeout // 60} minutes for GI mode...")
                    
                    while time.time() - gi_start < gi_mode_timeout:
                        elapsed = int(time.time() - gi_start)
                        mins, secs = divmod(elapsed, 60)
                        
                        with progress_lock:
                            device_progress[hostname]['stage'] = f'RECOVERY: Waiting for GI mode... ({mins}m {secs}s)'
                        
                        # Wait before checking
                        time.sleep(gi_check_interval)
                        
                        try:
                            from .connection_strategy import connect_for_upgrade
                            conn = connect_for_upgrade(hostname, timeout=15)
                            if conn['connected']:
                                ssh = conn['ssh']
                                channel = conn['channel']
                                state = conn.get('device_state') or ''
                                if state in ('GI', 'BASEOS_SHELL'):
                                    is_gi_mode = True
                                    gi_connected = True
                                    add_terminal_line(f"✓ GI mode reached after {mins}m {secs}s")
                                    try:
                                        _opf = Path(f"db/configs/{hostname}/operational.json")
                                        _opd = {}
                                        if _opf.exists():
                                            with open(_opf) as f:
                                                _opd = json.load(f)
                                        _opd['device_state'] = 'GI'
                                        _opd['recovery_mode_detected'] = False
                                        _opd['upgrade_in_progress'] = True
                                        _opd['install_type'] = 'gi_deploy'
                                        with open(_opf, 'w') as f:
                                            json.dump(_opd, f, indent=4)
                                    except:
                                        pass
                                    break
                                add_terminal_line(f"⏳ Connected but not in GI mode yet... ({mins}m {secs}s)")
                                consecutive_failures = 0
                                try:
                                    ssh.close()
                                except:
                                    pass
                            else:
                                consecutive_failures += 1
                                if consecutive_failures <= max_consecutive_failures:
                                    add_terminal_line(f"⏳ Connection attempt failed, retrying... ({mins}m {secs}s)")
                                else:
                                    add_terminal_line(f"⏳ Still waiting for device... ({mins}m {secs}s)")
                        except paramiko.ssh_exception.SSHException as ssh_err:
                            # SSH-specific errors (connection refused, etc.)
                            consecutive_failures += 1
                            if consecutive_failures <= max_consecutive_failures:
                                add_terminal_line(f"⏳ Device rebooting... ({mins}m {secs}s)")
                            else:
                                add_terminal_line(f"⏳ Still rebooting... ({mins}m {secs}s)")
                        except Exception as conn_err:
                            # Other connection errors
                            consecutive_failures += 1
                            if consecutive_failures <= max_consecutive_failures:
                                add_terminal_line(f"⏳ Connection attempt failed, retrying... ({mins}m {secs}s)")
                            else:
                                add_terminal_line(f"⏳ Still waiting for device... ({mins}m {secs}s)")
                    
                    if not gi_connected:
                        elapsed_total = int(time.time() - gi_start)
                        mins_total, secs_total = divmod(elapsed_total, 60)
                        with progress_lock:
                            device_progress[hostname]['status'] = 'failed'
                            device_progress[hostname]['error'] = f'Timeout waiting for GI mode after {mins_total}m {secs_total}s'
                        return False, f"Timeout waiting for GI mode after recovery restore (waited {mins_total}m {secs_total}s)"
                    
                    # After recovery delete, we're now in GI mode - continue to load images
                    # The code will continue below to load components
                
                # Detect GI mode from prompt OR from connect_for_upgrade state detection
                # Also use operational.json as fallback when connect returns UNKNOWN
                # (e.g. console was jammed by previous 'yes' command)
                _conn_state = conn.get('device_state', '')
                _op_state = None
                if _conn_state in ('UNKNOWN', '', None):
                    try:
                        _op_check = Path(f"db/configs/{hostname}/operational.json")
                        if _op_check.exists():
                            with open(_op_check) as f:
                                _op_state = json.load(f).get('device_state')
                    except:
                        pass
                
                _is_gi_from_prompt = ('GI(' in initial_output or 'GI#' in initial_output or 'GI>' in initial_output)
                _is_gi_from_connect = _conn_state in ('GI', 'BASEOS_SHELL')
                _is_gi_from_db = _op_state in ('GI', 'BASEOS_SHELL', 'RECOVERY')
                
                if _is_gi_from_prompt or _is_gi_from_connect or _is_gi_from_db:
                    is_gi_mode = True
                    if _is_gi_from_connect:
                        _gi_src = f"connect ({_conn_state})"
                    elif _is_gi_from_db:
                        _gi_src = f"operational.json ({_op_state})"
                    else:
                        _gi_src = "prompt"
                    add_terminal_line(f"GI mode (detected via {_gi_src})")
                    
                    # Clean up channel before sending any GI commands.
                    # A previous session may have left 'yes' or other commands running.
                    channel.sendall(b"\x03")  # Ctrl+C to kill stuck processes
                    time.sleep(1)
                    while channel.recv_ready():
                        channel.recv(65535)
                    
                    # Check if we're in BaseOS shell and need dncli
                    _need_dncli = (
                        _conn_state == 'BASEOS_SHELL' 
                        or 'dn@' in initial_output 
                        or ':~$' in initial_output
                        or (_is_gi_from_db and not _is_gi_from_prompt)
                    )
                    
                    if _need_dncli:
                        add_terminal_line("Entering dncli from BaseOS shell...")
                            
                        channel.sendall(b"dncli\n")
                        time.sleep(3)
                        
                        # Handle potential password prompt
                        dncli_out = ""
                        while channel.recv_ready():
                            dncli_out += channel.recv(65535).decode('utf-8', errors='replace')
                        if 'assword' in dncli_out.lower():
                            channel.sendall(b"dnroot\n")
                            time.sleep(15)  # Wait for GI prompt to initialize
                        
                        # Send enter to get clean prompt
                        for _ in range(3):
                            channel.sendall(b"\n")
                            time.sleep(2)
                            while channel.recv_ready():
                                channel.recv(65535)
                elif requires_delete_deploy:
                    _dd_reason = "Branch switch" if stack.get('_branch_switch') else "Version jump"
                    add_terminal_line(f"🔄 {_dd_reason} - deleting system...")
                    
                    # CRITICAL: Save system_type and hostname BEFORE delete for deploy command later
                    add_terminal_line(f"💾 Saving deploy params: {system_type}, {hostname}")
                    try:
                        op_file = Path(f"db/configs/{hostname}/operational.json")
                        op_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        op_data = {}
                        if op_file.exists():
                            with open(op_file) as f:
                                op_data = json.load(f)
                        
                        _detected_ncc2 = conn.get('ncc_id') if conn.get('ncc_id') is not None else 0
                        _update2 = {
                            'deploy_system_type': system_type,
                            'deploy_name': deploy_hostname,
                            'deploy_ncc_id': str(_detected_ncc2),
                            'deploy_command': f"request system deploy system-type {system_type} name {deploy_hostname} ncc-id {_detected_ncc2}",
                            'pre_delete_system_type': system_type,
                            'pre_delete_hostname': deploy_hostname,
                            'delete_initiated': datetime.now().isoformat(),
                            'device_state': 'GI',
                            'recovery_mode_detected': True,
                            'recovery_type': 'GI',
                            'recovery_mode_detected_at': datetime.now().isoformat()
                        }
                        try:
                            from .connection_strategy import get_console_config_for_device
                            _ccfg2 = get_console_config_for_device(hostname)
                            if _ccfg2 and _ccfg2.get('port'):
                                _update2['connection_method'] = f"Console ({_ccfg2.get('console_server_name', 'console')} p{_ccfg2['port']})"
                        except ImportError:
                            pass
                        op_data.update(_update2)
                        
                        with open(op_file, 'w') as f:
                            json.dump(op_data, f, indent=4)
                        add_terminal_line("✓ Deploy params saved")
                    except Exception as save_err:
                        add_terminal_line(f"⚠ Save failed: {str(save_err)[:30]}")
                    
                    with progress_lock:
                        device_progress[hostname]['stage'] = 'Executing system delete...'
                    
                    # Define send_and_wait helper for delete command
                    def send_and_wait_temp(cmd, wait_time=5):
                        """Temporary send and wait for delete command."""
                        channel.sendall((cmd + "\n").encode('utf-8'))
                        time.sleep(wait_time)
                        output = ""
                        while channel.recv_ready():
                            output += channel.recv(65535).decode('utf-8', errors='replace')
                            time.sleep(0.3)
                        return output
                    
                    from .utils import audit_log
                    audit_log(hostname, device.ip, "request system delete", "recovery-delete-deploy")
                    send_and_wait_temp("request system delete", wait_time=3)
                    send_and_wait_temp("yes", wait_time=2)
                    add_terminal_line("✓ System delete initiated")
                    
                    # Wait for GI mode (device reboots into GI)
                    with progress_lock:
                        device_progress[hostname]['stage'] = 'Waiting for GI mode (device rebooting)...'
                    add_terminal_line("⏳ Waiting for GI mode...")
                    
                    # Close current connection
                    ssh.close()
                    
                    # Wait and reconnect (system delete takes ~2-5 minutes)
                    gi_mode_timeout = 300  # 5 minutes
                    gi_check_interval = 30  # Check every 30 seconds
                    gi_start = time.time()
                    gi_connected = False
                    
                    while time.time() - gi_start < gi_mode_timeout:
                        elapsed = int(time.time() - gi_start)
                        with progress_lock:
                            device_progress[hostname]['stage'] = f'Waiting for GI mode... ({elapsed}s)'
                        
                        time.sleep(gi_check_interval)
                        
                        try:
                            from .connection_strategy import connect_for_upgrade
                            conn = connect_for_upgrade(hostname, timeout=15)
                            if conn['connected']:
                                ssh = conn['ssh']
                                channel = conn['channel']
                                state = conn.get('device_state') or ''
                                if state in ('GI', 'BASEOS_SHELL'):
                                    is_gi_mode = True
                                    gi_connected = True
                                    add_terminal_line("✓ Device now in GI mode")
                                    try:
                                        _opf = Path(f"db/configs/{hostname}/operational.json")
                                        _opd = {}
                                        if _opf.exists():
                                            with open(_opf) as f:
                                                _opd = json.load(f)
                                        _opd['device_state'] = 'GI'
                                        _opd['recovery_mode_detected'] = False
                                        _opd['upgrade_in_progress'] = True
                                        _opd['install_type'] = 'gi_deploy'
                                        with open(_opf, 'w') as f:
                                            json.dump(_opd, f, indent=4)
                                    except:
                                        pass
                                    break
                                try:
                                    ssh.close()
                                except:
                                    pass
                        except Exception:
                            add_terminal_line(f"⏳ Reconnect attempt... ({elapsed}s)")
                    
                    if not gi_connected:
                        with progress_lock:
                            device_progress[hostname]['status'] = 'failed'
                            device_progress[hostname]['error'] = 'Timeout waiting for GI mode after delete'
                        return False, "Timeout waiting for GI mode after system delete"
                
                def send_and_wait(cmd, wait_time=5, look_for=None, silent=False):
                    """Send command and wait for output.
                    
                    Args:
                        cmd: Command to send
                        wait_time: Seconds to wait for output
                        look_for: Optional string to look for in output
                        silent: If True, don't log command or output to terminal
                    """
                    # Use sendall to ensure all bytes are sent
                    channel.sendall((cmd + "\n").encode('utf-8'))
                    
                    # Wait for command to process
                    time.sleep(wait_time)
                    
                    # Collect all available output
                    output = ""
                    read_attempts = 0
                    while read_attempts < 10:  # Max 10 attempts
                        if channel.recv_ready():
                            chunk = channel.recv(65535).decode('utf-8', errors='replace')
                            output += chunk
                            read_attempts = 0  # Reset on successful read
                        else:
                            read_attempts += 1
                            time.sleep(0.3)
                            if read_attempts >= 3 and output:  # Have output, waited enough
                                break
                    
                    # Only show meaningful output (errors, warnings), skip routine responses
                    if not silent:
                        clean_output = sanitize_terminal(output)
                        for line in clean_output.split('\n')[-3:]:
                            line = line.strip()
                            # Only show errors, warnings, or important status
                            if line and len(line) > 5:
                                line_lower = line.lower()
                                if any(kw in line_lower for kw in ['error', 'fail', 'warning', 'success', 'complete', 'started']):
                                    add_terminal_line(line[:60])
                    
                    return output
                
                def wait_for_download_complete(timeout=300, component="", base_progress=5, progress_range=25):
                    """Wait for download to reach 100% with stall detection."""
                    start = time.time()
                    last_pct = 0
                    poll_count = 0
                    last_update = 0
                    first_progress_at = None
                    stall_threshold = 120
                    
                    add_terminal_line(f"📥 Downloading {component}...")
                    
                    while time.time() - start < timeout:
                        poll_count += 1
                        elapsed = int(time.time() - start)
                        
                        with progress_lock:
                            device_progress[hostname]['stage'] = f"Downloading {component}..."
                        
                        output = send_and_wait("show system target-stack load | no-more", wait_time=4, silent=True)
                        
                        pct_match = re.search(r'(\d+)\s*%', output)
                        if not pct_match:
                            pct_match = re.search(r'Progress[:\s]+(\d+)', output, re.IGNORECASE)
                        
                        if pct_match:
                            pct = int(pct_match.group(1))
                            if first_progress_at is None:
                                first_progress_at = time.time()
                            if pct >= last_update + 20:
                                last_update = pct
                                add_terminal_line(f"📥 {component}: {pct}%")
                            if pct > last_pct:
                                last_pct = pct
                            
                            actual_progress = base_progress + int((pct / 100) * progress_range)
                            with progress_lock:
                                device_progress[hostname]['stage'] = f"📥 {component} {pct}%"
                                device_progress[hostname]['progress'] = actual_progress
                        
                        output_lower = output.lower()
                        if 'completed' in output_lower or last_pct >= 100:
                            add_terminal_line(f"✓ {component} complete!")
                            return True, output
                        
                        if ('no download' in output_lower or 'no tasks' in output_lower) and last_pct > 0:
                            add_terminal_line(f"✓ {component} complete!")
                            return True, output
                        
                        if 'failed' in output_lower:
                            add_terminal_line(f"✗ {component} FAILED")
                            return False, output
                        
                        # Stall detection: if 0% for > stall_threshold, signal retry
                        if last_pct == 0 and elapsed > stall_threshold:
                            _no_dl = 'no download' in output_lower or 'no tasks' in output_lower
                            _err = 'error' in output_lower or 'upgrade in progress' in output_lower
                            if _no_dl or _err or not pct_match:
                                add_terminal_line(f"⚠ {component} stalled at 0% ({elapsed}s) — will retry")
                                return False, f"STALL:{output}"
                        
                        time.sleep(5)
                    
                    add_terminal_line(f"✗ {component} timeout {timeout}s")
                    return False, f"Timeout after {timeout}s"
                
                # Calculate progress steps based on what we're loading
                # Safety: clean channel before sending any commands
                channel.sendall(b"\x03")  # Ctrl+C
                time.sleep(0.5)
                while channel.recv_ready():
                    channel.recv(65535)
                
                # Verify we have a CLI prompt (not stuck in shell)
                channel.sendall(b"\n")
                time.sleep(2)
                _prompt_check = ""
                while channel.recv_ready():
                    _prompt_check += channel.recv(8192).decode('utf-8', errors='replace')
                
                if 'dn@' in _prompt_check or ':~$' in _prompt_check:
                    add_terminal_line("In BaseOS shell, entering dncli...")
                    channel.sendall(b"dncli\n")
                    time.sleep(3)
                    _dncli_out = ""
                    while channel.recv_ready():
                        _dncli_out += channel.recv(8192).decode('utf-8', errors='replace')
                    if 'assword' in _dncli_out.lower():
                        channel.sendall(b"dnroot\n")
                        time.sleep(15)
                    for _ in range(3):
                        channel.sendall(b"\n")
                        time.sleep(2)
                        while channel.recv_ready():
                            channel.recv(65535)
                
                components_to_load = []
                if dnos_url and dnos_url != 'N/A':
                    components_to_load.append(('DNOS', dnos_url))
                if gi_url and gi_url != 'N/A':
                    components_to_load.append(('GI', gi_url))
                if baseos_url and baseos_url != 'N/A':
                    components_to_load.append(('BaseOS', baseos_url))
                
                total_components = len(components_to_load)
                if total_components == 0:
                    with progress_lock:
                        device_progress[hostname]['status'] = 'failed'
                        device_progress[hostname]['error'] = 'No components to load'
                    return False, "No components to load"
                
                # Check target stack to skip images already loaded on the device
                try:
                    # Use 'show system stack' which shows Target column with loaded versions
                    _ts_check = send_and_wait("show system stack | no-more", wait_time=5, silent=True)
                    _ts_clean = sanitize_terminal(_ts_check).lower()
                    
                    _already_loaded = []
                    _still_needed = []
                    for comp_name, comp_url in components_to_load:
                        # Extract version from URL: .../drivenets_dnos_25.4.13.146_dev.dev_v25_4_13_578.tar
                        _url_ver = comp_url.rstrip('/').split('/')[-1]
                        _url_ver = _url_ver.replace('drivenets_dnos_', '').replace('drivenets_gi_', '').replace('drivenets_baseos_', '')
                        _url_ver = _url_ver.replace('.tar', '').replace('.gz', '')
                        
                        if _url_ver and _url_ver.lower() in _ts_clean:
                            _already_loaded.append(comp_name)
                        else:
                            _still_needed.append((comp_name, comp_url))
                            add_terminal_line(f"{comp_name}: not in stack yet")
                    
                    if _already_loaded:
                        _skip_msg = ", ".join(_already_loaded)
                        add_terminal_line(f"Already in target: {_skip_msg}")
                    
                    if _still_needed:
                        components_to_load = _still_needed
                        total_components = len(components_to_load)
                    elif _already_loaded:
                        add_terminal_line("All images already in target stack!")
                        components_to_load = []
                        total_components = 0
                except Exception:
                    pass  # If check fails, proceed with loading all
                
                # If all images already in target stack, skip loading entirely
                _all_images_preloaded = (total_components == 0 and bool(locals().get('_already_loaded')))
                
                if _all_images_preloaded:
                    add_terminal_line("Skipping image upload (all in target)")
                    with progress_lock:
                        device_progress[hostname]['stage'] = 'All images already loaded'
                        device_progress[hostname]['progress'] = 90
                
                # After system delete + GI reconnect, device needs time before accepting loads.
                if not _all_images_preloaded and is_gi_mode and requires_delete_deploy:
                    add_terminal_line("⏳ Settling after delete (30s)...")
                    time.sleep(30)
                    for _settle in range(12):
                        _ts_out = send_and_wait("show system target-stack | no-more", wait_time=3, silent=True)
                        _ts_lower = _ts_out.lower()
                        if 'upgrade in progress' in _ts_lower or 'in-progress' in _ts_lower or 'error' in _ts_lower:
                            _sw = (_settle + 1) * 15
                            add_terminal_line(f"⏳ GI busy, waiting... ({30 + _sw}s)")
                            time.sleep(15)
                        else:
                            break
                elif not _all_images_preloaded and is_gi_mode:
                    add_terminal_line("⏳ Settling GI (15s)...")
                    time.sleep(15)
                
                if _all_images_preloaded:
                    progress_per_component = 0
                else:
                    progress_per_component = 85 // total_components  # Reserve 15% for install
                current_progress = 5
                
                # Load each component
                for idx, (comp_name, comp_url) in enumerate(components_to_load):
                    with progress_lock:
                        device_progress[hostname]['stage'] = f'Loading {comp_name}...'
                        device_progress[hostname]['progress'] = current_progress
                    
                    # Send load command with retry for "upgrade in progress"
                    _load_ok = False
                    for _load_try in range(4):
                        load_output = send_and_wait(f"request system target-stack load {comp_url}", wait_time=3)
                        
                        time.sleep(1)
                        if channel.recv_ready():
                            immediate_output = channel.recv(65535).decode('utf-8', errors='replace')
                            load_output += immediate_output
                            clean_output = sanitize_terminal(immediate_output)
                            for line in clean_output.split('\n')[-4:]:
                                line = line.strip()
                                if line and len(line) > 5:
                                    add_terminal_line(line)
                        
                        _lo = load_output.lower()
                        if 'upgrade in progress' in _lo or 'error downloading' in _lo:
                            add_terminal_line(f"⏳ Device busy, retry in 15s ({_load_try+1}/4)")
                            time.sleep(15)
                            continue
                        
                        # Only send 'yes' if there's a confirmation prompt.
                        # NEVER send 'yes' blindly -- in BaseOS Linux 'yes' is an infinite loop command.
                        if 'command not found' in _lo or 'unknown command' in _lo:
                            add_terminal_line(f"✗ {comp_name}: not in CLI mode!")
                            break
                        
                        if 'continue' in _lo or '[yes/no]' in _lo or 'y/n' in _lo or 'confirm' in _lo:
                            send_and_wait("yes", wait_time=2)
                        
                        _load_ok = True
                        break
                    
                    if not _load_ok:
                        add_terminal_line(f"✗ {comp_name}: device busy after retries")
                        with progress_lock:
                            device_progress[hostname]['status'] = 'failed'
                            device_progress[hostname]['error'] = f'{comp_name}: device busy'
                        ssh.close()
                        return False, f"{comp_name} load failed: device reports upgrade in progress"
                    
                    add_terminal_line(f"✓ {comp_name} load started")
                    
                    # Wait for download with stall-retry loop
                    _dl_attempts = 0
                    _dl_max_attempts = 3
                    _dl_success = False
                    while _dl_attempts < _dl_max_attempts:
                        _dl_attempts += 1
                        success, output = wait_for_download_complete(
                            timeout=300, 
                            component=comp_name,
                            base_progress=current_progress,
                            progress_range=progress_per_component
                        )
                        if success:
                            _dl_success = True
                            break
                        if isinstance(output, str) and output.startswith("STALL:"):
                            add_terminal_line(f"🔄 Retrying {comp_name} load ({_dl_attempts}/{_dl_max_attempts})...")
                            time.sleep(10)
                            send_and_wait(f"request system target-stack load {comp_url}", wait_time=3)
                            time.sleep(1)
                            if channel.recv_ready():
                                channel.recv(65535)
                            send_and_wait("yes", wait_time=2)
                            add_terminal_line(f"✓ {comp_name} re-sent")
                            continue
                        break
                    
                    if not _dl_success:
                        with progress_lock:
                            device_progress[hostname]['status'] = 'failed'
                            device_progress[hostname]['error'] = f'{comp_name} load failed'
                        ssh.close()
                        return False, f"{comp_name} load failed"
                    
                    current_progress += progress_per_component
                    with progress_lock:
                        device_progress[hostname]['progress'] = current_progress
                    add_terminal_line(f"✓ {comp_name} loaded")
                
                # Pre-check phase: run pre-check then verify result
                with progress_lock:
                    device_progress[hostname]['status'] = 'installing'
                    device_progress[hostname]['progress'] = 88
                    device_progress[hostname]['stage'] = 'Running pre-check...'
                
                add_terminal_line("Pre-check...")
                req_output = send_and_wait("request system target-stack pre-check", wait_time=15)
                req_lower = req_output.lower()
                
                precheck_passed = None
                precheck_detail = ""
                failed_tests = []
                
                if 'status: ok' in req_lower or 'result: succeeded' in req_lower or 'result: passed' in req_lower:
                    precheck_passed = True
                    precheck_detail = "OK"
                elif 'status: error' in req_lower:
                    precheck_passed = False
                    for rline in req_output.split('\n'):
                        if 'reason' in rline.lower():
                            precheck_detail = rline.strip()[:80]
                            break
                    if not precheck_detail:
                        precheck_detail = "Error"
                elif 'in progress' in req_lower or 'in-progress' in req_lower:
                    add_terminal_line("  Pre-check in progress, polling...")
                
                # If request output was unclear, poll show command
                if precheck_passed is None:
                    with progress_lock:
                        device_progress[hostname]['progress'] = 90
                        device_progress[hostname]['stage'] = 'Waiting for pre-check to complete...'
                    
                    for poll_attempt in range(12):  # Up to ~2 minutes (12 x 10s)
                        time.sleep(10)
                        show_output = send_and_wait("show system target-stack pre-check", wait_time=8)
                        show_lower = show_output.lower()
                        
                        if 'in-progress' in show_lower or 'in_progress' in show_lower or 'running' in show_lower:
                            elapsed_s = (poll_attempt + 1) * 10
                            add_terminal_line(f"  Pre-check running... ({elapsed_s}s)")
                            with progress_lock:
                                device_progress[hostname]['stage'] = f'Pre-check running... ({elapsed_s}s)'
                            continue
                        
                        for sline in show_output.split('\n'):
                            sl = sline.lower().strip()
                            if 'pre-check result' in sl:
                                if 'passed' in sl or 'succeeded' in sl:
                                    precheck_passed = True
                                    precheck_detail = "Passed"
                                elif 'failed' in sl:
                                    precheck_passed = False
                                    precheck_detail = sline.strip()
                            if '| failed' in sl or '|failed' in sl:
                                parts = [p.strip() for p in sline.split('|') if p.strip()]
                                if len(parts) >= 2:
                                    failed_tests.append(parts[0][:40])
                        
                        if precheck_passed is not None:
                            break
                        
                        # Task done but no explicit result -- likely OK
                        if 'task status' in show_lower and 'done' in show_lower:
                            precheck_passed = True
                            precheck_detail = "Task completed"
                            break
                    
                    add_terminal_line("> show system target-stack pre-check")
                
                # Default: if still unknown after all attempts, proceed (don't block install)
                if precheck_passed is None:
                    precheck_passed = True
                    precheck_detail = "Pre-check inconclusive, proceeding with install"
                    add_terminal_line("⚠ Pre-check output unclear, proceeding with install")
                
                if not precheck_passed:
                    # Check if Stack Validity specifically failed due to "will cause DNOS deletion"
                    # This means the upgrade requires system delete + deploy
                    stack_validity_deletion = False
                    _show_out = show_output if 'show_output' in locals() else ""
                    all_output = (req_output + "\n" + _show_out).lower()
                    if 'stack validity' in ' '.join(t.lower() for t in failed_tests) or 'stack validity' in all_output:
                        if 'deletion' in all_output or 'cause dnos' in all_output:
                            stack_validity_deletion = True
                    
                    if stack_validity_deletion:
                        add_terminal_line("⚠ DNOS says: upgrade requires system delete + deploy")
                        add_terminal_line("Auto-switching to delete+deploy flow...")
                        with progress_lock:
                            device_progress[hostname]['stage'] = 'System delete required - switching flow...'
                        
                        # Full flow: delete → wait GI → reload images → deploy
                        try:
                            add_terminal_line("> request system delete")
                            delete_output = send_and_wait("request system delete", wait_time=5)
                            if 'yes/no' in delete_output.lower() or 'confirm' in delete_output.lower():
                                send_and_wait("yes", wait_time=3)
                                add_terminal_line("> yes")
                        except Exception as del_err:
                            _de = str(del_err).lower()
                            if not ('socket' in _de or 'closed' in _de or 'eof' in _de):
                                add_terminal_line(f"✗ Delete failed: {str(del_err)[:35]}")
                                with progress_lock:
                                    device_progress[hostname]['status'] = 'failed'
                                    device_progress[hostname]['error'] = 'System delete failed'
                                return False, f"System delete failed: {del_err}"
                        
                        time.sleep(5)
                        try:
                            ssh.close()
                        except:
                            pass
                        
                        add_terminal_line("⏳ Waiting for GI mode...")
                        _pw = getattr(device, 'password', 'dnroot') or 'dnroot'
                        _gi_timeout = 300
                        _gi_start = time.time()
                        _gi_ok = False
                        
                        while time.time() - _gi_start < _gi_timeout:
                            _el = int(time.time() - _gi_start)
                            with progress_lock:
                                device_progress[hostname]['stage'] = f'Delete: waiting for GI ({_el}s)'
                            time.sleep(30)
                            try:
                                ssh = paramiko.SSHClient()
                                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                                from .utils import resolve_device_ip
                                _rip, _rm = resolve_device_ip(device, timeout=2.0)
                                _tip = _rip or device.ip
                                ssh.connect(_tip, username='dnroot', password=_pw, timeout=15,
                                            allow_agent=False, look_for_keys=False)
                                channel = ssh.invoke_shell(width=200, height=50)
                                time.sleep(2)
                                _nout = channel.recv(65535).decode('utf-8', errors='replace')
                                if 'GI(' in _nout or 'GI#' in _nout or 'GI>' in _nout:
                                    _gi_ok = True
                                    add_terminal_line(f"✓ GI mode ({_el}s)")
                                    break
                                ssh.close()
                            except:
                                add_terminal_line(f"⏳ Reconnecting... ({_el}s)")
                        
                        if not _gi_ok:
                            with progress_lock:
                                device_progress[hostname]['status'] = 'failed'
                                device_progress[hostname]['error'] = 'Timeout: GI after delete'
                            return False, "Timeout waiting for GI after system delete"
                        
                        add_terminal_line("⏳ Settling after delete (30s)...")
                        time.sleep(30)
                        for _stl in range(12):
                            _stl_out = send_and_wait("show system target-stack | no-more", wait_time=3, silent=True)
                            if 'upgrade in progress' in _stl_out.lower() or 'in-progress' in _stl_out.lower() or 'error' in _stl_out.lower():
                                add_terminal_line(f"⏳ GI busy ({30 + (_stl+1)*15}s)")
                                time.sleep(15)
                            else:
                                break
                        
                        add_terminal_line("📥 Reloading images...")
                        with progress_lock:
                            device_progress[hostname]['stage'] = 'Reloading images...'
                            device_progress[hostname]['progress'] = 40
                        
                        for _cn, _cu in components_to_load:
                            _rl_ok = False
                            for _rl_try in range(4):
                                _rl_out = send_and_wait(f"request system target-stack load {_cu}", wait_time=3)
                                time.sleep(1)
                                if channel.recv_ready():
                                    _rl_out += channel.recv(65535).decode('utf-8', errors='replace')
                                if 'upgrade in progress' in _rl_out.lower() or 'error downloading' in _rl_out.lower():
                                    add_terminal_line(f"⏳ Device busy, retry in 15s ({_rl_try+1}/4)")
                                    time.sleep(15)
                                    continue
                                send_and_wait("yes", wait_time=2)
                                _rl_ok = True
                                break
                            if not _rl_ok:
                                add_terminal_line(f"✗ {_cn}: device busy after retries")
                                with progress_lock:
                                    device_progress[hostname]['status'] = 'failed'
                                    device_progress[hostname]['error'] = f'{_cn} reload failed'
                                ssh.close()
                                return False, f"{_cn} reload failed: device busy"
                            
                            add_terminal_line(f"📥 {_cn}...")
                            _dl_attempts_fb = 0
                            _dl_ok = False
                            while _dl_attempts_fb < 3:
                                _dl_attempts_fb += 1
                                _dl_ok, _dl_out = wait_for_download_complete(
                                    timeout=300, component=_cn, base_progress=40, progress_range=15)
                                if _dl_ok:
                                    break
                                if isinstance(_dl_out, str) and _dl_out.startswith("STALL:"):
                                    add_terminal_line(f"🔄 Retrying {_cn} ({_dl_attempts_fb}/3)...")
                                    time.sleep(10)
                                    send_and_wait(f"request system target-stack load {_cu}", wait_time=3)
                                    time.sleep(1)
                                    if channel.recv_ready():
                                        channel.recv(65535)
                                    send_and_wait("yes", wait_time=2)
                                    continue
                                break
                            
                            if not _dl_ok:
                                with progress_lock:
                                    device_progress[hostname]['status'] = 'failed'
                                    device_progress[hostname]['error'] = f'{_cn} reload failed'
                                ssh.close()
                                return False, f"{_cn} reload failed after delete"
                            add_terminal_line(f"✓ {_cn} loaded")
                        
                        add_terminal_line("Pre-check...")
                        with progress_lock:
                            device_progress[hostname]['stage'] = 'Pre-check after reload...'
                            device_progress[hostname]['progress'] = 85
                        send_and_wait("request system target-stack pre-check", wait_time=15)
                        
                        _pc_ok = False
                        for _ in range(12):
                            time.sleep(10)
                            _pc_out = send_and_wait("show system target-stack pre-check", wait_time=8)
                            _pcl = _pc_out.lower()
                            if 'succeeded' in _pcl or 'status: ok' in _pcl:
                                _pc_ok = True
                                add_terminal_line("✓ Pre-check passed")
                                break
                            if 'failed' in _pcl and ('status' in _pcl or 'result' in _pcl):
                                add_terminal_line("✗ Pre-check failed")
                                with progress_lock:
                                    device_progress[hostname]['status'] = 'failed'
                                    device_progress[hostname]['error'] = 'Pre-check failed after reload'
                                ssh.close()
                                return False, "Pre-check failed after delete + reload"
                        
                        if not _pc_ok:
                            add_terminal_line("⚠ Pre-check inconclusive, deploying...")
                        
                        _fb_ncc = conn.get('ncc_id') if conn.get('ncc_id') is not None else 0
                        deploy_cmd = f"request system deploy system-type {system_type} name {deploy_hostname} ncc-id {_fb_ncc}"
                        add_terminal_line(f"Deploying (NCC {_fb_ncc})...")
                        with progress_lock:
                            device_progress[hostname]['stage'] = 'Deploying DNOS...'
                            device_progress[hostname]['progress'] = 92
                        
                        from .utils import audit_log as _al
                        _al(hostname, device.ip, deploy_cmd, "precheck-fallback-deploy")
                        _dep_out = ""
                        try:
                            _dep_out = send_and_wait(deploy_cmd, wait_time=8)
                            _dep_lower = _dep_out.lower()
                            # NCC ID mismatch - retry with the other NCC
                            if "doesn't match" in _dep_lower or 'auto detected' in _dep_lower:
                                _fb_ncc = 1 - _fb_ncc
                                deploy_cmd = f"request system deploy system-type {system_type} name {deploy_hostname} ncc-id {_fb_ncc}"
                                add_terminal_line(f"Retrying NCC {_fb_ncc}...")
                                _dep_out = send_and_wait(deploy_cmd, wait_time=8)
                                _dep_lower = _dep_out.lower()
                            if 'yes/no' in _dep_lower or 'do you want' in _dep_lower or 'y/n' in _dep_lower or 'continue' in _dep_lower:
                                send_and_wait("yes", wait_time=5)
                        except Exception as _derr:
                            _ds = str(_derr).lower()
                            if not ('socket' in _ds or 'closed' in _ds or 'eof' in _ds):
                                raise
                        
                        _dtm = re.search(r'task\s*(?:id|ID)?\s*[=:]\s*(\d+)', _dep_out)
                        _tid = _dtm.group(1) if _dtm else ""
                        
                        add_terminal_line(f"✓ Deploy started{f' ({_tid})' if _tid else ''}")
                        with progress_lock:
                            device_progress[hostname]['status'] = 'success'
                            device_progress[hostname]['progress'] = 100
                            device_progress[hostname]['stage'] = f'Deployed{f" (task {_tid})" if _tid else ""}'
                        is_gi_mode = True
                        try:
                            ssh.close()
                        except:
                            pass
                        return True, f"Delete+reload+deploy done{f' (task {_tid})' if _tid else ''}"
                    
                    fail_summary = precheck_detail
                    if failed_tests:
                        fail_summary += f" [{', '.join(failed_tests)}]"
                        for t in failed_tests:
                            add_terminal_line(f"  ✗ {t}: Failed")
                    add_terminal_line(f"✗ Pre-check FAILED: {fail_summary[:80]}")
                    with progress_lock:
                        device_progress[hostname]['status'] = 'failed'
                        device_progress[hostname]['error'] = f'Pre-check failed: {fail_summary[:120]}'
                    ssh.close()
                    return False, f"Pre-check failed: {fail_summary}"
                
                add_terminal_line(f"✓ Pre-check: {precheck_detail}")
                
                with progress_lock:
                    device_progress[hostname]['progress'] = 92
                
                # Install/Deploy phase
                if is_gi_mode:
                    with progress_lock:
                        device_progress[hostname]['stage'] = f'Deploying DNOS (GI mode)...'
                    
                    add_terminal_line(f"🚀 GI deploy: {system_type}")
                    
                    # Capture old task IDs BEFORE deploy so we can detect fresh ones
                    old_precheck = send_and_wait("show system target-stack pre-check | no-more", wait_time=3)
                    old_task_id = ""
                    old_task_match = re.search(r'Task ID:\s*(\d+)', old_precheck)
                    if old_task_match:
                        old_task_id = old_task_match.group(1)
                    
                    old_install = send_and_wait("show system install | no-more", wait_time=3)
                    old_install_task_id = ""
                    old_install_match = re.search(r'Task ID:\s*(\d+)', old_install)
                    if old_install_match:
                        old_install_task_id = old_install_match.group(1)
                    
                    _main_ncc = conn.get('ncc_id') if conn.get('ncc_id') is not None else 0
                    deploy_cmd = f"request system deploy system-type {system_type} name {deploy_hostname} ncc-id {_main_ncc}"
                    add_terminal_line(f"> deploy ncc-id {_main_ncc}...")
                    
                    from .utils import audit_log
                    audit_log(hostname, conn.get('ip', device.ip), deploy_cmd, "multi-device-upgrade")
                    deploy_output = send_and_wait(deploy_cmd, wait_time=12)
                    deploy_lower = deploy_output.lower()
                    confirm_output = ""
                    
                    # NCC ID mismatch - retry with the other NCC
                    if "doesn't match" in deploy_lower or 'auto detected' in deploy_lower:
                        _main_ncc = 1 - _main_ncc
                        deploy_cmd = f"request system deploy system-type {system_type} name {deploy_hostname} ncc-id {_main_ncc}"
                        add_terminal_line(f"NCC retry -> ncc-id {_main_ncc}")
                        deploy_output = send_and_wait(deploy_cmd, wait_time=12)
                        deploy_lower = deploy_output.lower()
                    
                    if 'yes/no' in deploy_lower or 'do you want' in deploy_lower or 'continue' in deploy_lower or 'y/n' in deploy_lower or 'proceed' in deploy_lower:
                        confirm_output = send_and_wait("yes", wait_time=5)
                        add_terminal_line("> yes")
                    elif not deploy_lower.strip() or ('deploy' not in deploy_lower and 'task' not in deploy_lower and 'error' not in deploy_lower):
                        time.sleep(5)
                        extra_out = ""
                        while channel.recv_ready():
                            extra_out += channel.recv(65535).decode('utf-8', errors='replace')
                            time.sleep(0.3)
                        if extra_out:
                            deploy_output += extra_out
                            deploy_lower = deploy_output.lower()
                            if 'yes/no' in deploy_lower or 'do you want' in deploy_lower or 'continue' in deploy_lower or 'y/n' in deploy_lower:
                                confirm_output = send_and_wait("yes", wait_time=5)
                                add_terminal_line("> yes")
                    
                    combined_output = (deploy_output + confirm_output).lower()
                    
                    # Extract task ID from deploy response
                    deploy_task_match = re.search(r'task\s*(?:id|ID)?\s*[=:]\s*(\d+)', deploy_output + confirm_output)
                    deploy_task_id = deploy_task_match.group(1) if deploy_task_match else ""
                    
                    if 'error' in combined_output or 'failed' in combined_output:
                        # Ignore false positives: "Pre-check result: Failed" in combined_output
                        # is NOT a deploy error -- it's leftover from show commands
                        _real_error = True
                        if 'pre-check result' in combined_output:
                            _real_error = False
                        if _real_error:
                            add_terminal_line(f"Deploy error: {combined_output[:60]}")
                            with progress_lock:
                                device_progress[hostname]['status'] = 'failed'
                                device_progress[hostname]['error'] = 'Deploy command failed'
                                device_progress[hostname]['stage'] = 'Deploy failed'
                            ssh.close()
                            return False, "Deploy command failed"
                    
                    if 'started' in combined_output or deploy_task_id:
                        add_terminal_line(f"Started deployment{f', task ID = {deploy_task_id}' if deploy_task_id else ''}")
                    else:
                        add_terminal_line("Deploy command sent - verifying...")
                    
                    with progress_lock:
                        device_progress[hostname]['progress'] = 93
                        device_progress[hostname]['stage'] = 'Verifying deploy...'
                    
                    # Verify deployment actually started.
                    # PRIMARY check: `show system install` for a NEW or IN-PROGRESS install task.
                    # SECONDARY: new pre-check task ID (deploy triggers its own pre-check).
                    # The OLD pre-check result must NEVER be used as proof of deploy start.
                    deploy_verified = False
                    verify_start = time.time()
                    max_verify_time = 90
                    socket_lost = False
                    
                    while time.time() - verify_start < max_verify_time:
                        time.sleep(8)
                        
                        # PRIMARY: check show system install for active deploy
                        try:
                            install_output = send_and_wait("show system install | no-more", wait_time=5)
                            install_lower = install_output.lower()
                            
                            install_task_match = re.search(r'Task ID:\s*(\d+)', install_output)
                            install_task_id = install_task_match.group(1) if install_task_match else ""
                            
                            # New install task (different from the one before deploy)
                            if install_task_id and install_task_id != old_install_task_id:
                                if 'in-progress' in install_lower or 'in_progress' in install_lower:
                                    add_terminal_line(f"Installation in progress (task {install_task_id})")
                                    deploy_verified = True
                                    break
                                elif 'done' in install_lower or 'completed' in install_lower:
                                    add_terminal_line(f"Install task completed (task {install_task_id})")
                                    deploy_verified = True
                                    break
                                else:
                                    add_terminal_line(f"New install task detected ({install_task_id})")
                                    deploy_verified = True
                                    break
                            
                            # Same install task ID but now has running tasks
                            if 'in-progress' in install_lower:
                                add_terminal_line("Installation in progress")
                                deploy_verified = True
                                break
                            
                        except Exception as inst_err:
                            err_str = str(inst_err).lower()
                            if 'socket' in err_str or 'closed' in err_str or 'eof' in err_str or 'reset' in err_str:
                                socket_lost = True
                                add_terminal_line("Device rebooting (deploy in progress)")
                                break
                            raise
                        
                        # SECONDARY: check pre-check for a NEW task (deploy triggers its own)
                        try:
                            precheck_output = send_and_wait("show system target-stack pre-check | no-more", wait_time=3)
                            new_task_match = re.search(r'Task ID:\s*(\d+)', precheck_output)
                            new_task_id = new_task_match.group(1) if new_task_match else ""
                            task_status_match = re.search(r'Task status:\s*(\S+)', precheck_output)
                            task_status = task_status_match.group(1) if task_status_match else ""
                            
                            # ONLY trust a genuinely NEW pre-check task (different ID)
                            _is_new_task = new_task_id and new_task_id != old_task_id
                            
                            if _is_new_task:
                                _is_done = task_status.upper() in ('COMPLETED', 'DONE')
                                if _is_done:
                                    result_match = re.search(r'Pre-check result:\s*(\S+)', precheck_output)
                                    result = result_match.group(1) if result_match else ""
                                    if result.lower() in ('succeeded', 'passed'):
                                        add_terminal_line(f"Deploy pre-check passed (task {new_task_id})")
                                        deploy_verified = True
                                        break
                                    elif result.lower() == 'failed':
                                        add_terminal_line(f"Deploy pre-check failed: {result}")
                                        with progress_lock:
                                            device_progress[hostname]['status'] = 'failed'
                                            device_progress[hostname]['error'] = f'Deploy pre-check: {result}'
                                            device_progress[hostname]['stage'] = f'Pre-check {result}'
                                        ssh.close()
                                        return False, f"Deploy pre-check failed: {result}"
                                elif task_status.upper() == 'IN-PROGRESS':
                                    add_terminal_line(f"  Deploy pre-check running (task {new_task_id})...")
                                    with progress_lock:
                                        device_progress[hostname]['stage'] = 'Deploy pre-check in progress...'
                                    continue
                        except Exception as pc_err:
                            err_str = str(pc_err).lower()
                            if 'socket' in err_str or 'closed' in err_str or 'eof' in err_str or 'reset' in err_str:
                                socket_lost = True
                                add_terminal_line("Device rebooting (deploy in progress)")
                                break
                        
                        elapsed = int(time.time() - verify_start)
                        add_terminal_line(f"  Waiting for deploy to register... ({elapsed}s)")
                    
                    if socket_lost:
                        with progress_lock:
                            device_progress[hostname]['status'] = 'success'
                            device_progress[hostname]['progress'] = 100
                            device_progress[hostname]['stage'] = f'Deploy in progress - device rebooting{f" (task {deploy_task_id})" if deploy_task_id else ""}'
                    elif deploy_verified:
                        with progress_lock:
                            device_progress[hostname]['status'] = 'success'
                            device_progress[hostname]['progress'] = 100
                            device_progress[hostname]['stage'] = 'Deploy verified - DNOS installing'
                    else:
                        # Deploy not confirmed after max_verify_time -- mark as FAILED
                        add_terminal_line("Deploy NOT confirmed - no new install task detected")
                        add_terminal_line("Check manually: show system install")
                        with progress_lock:
                            device_progress[hostname]['status'] = 'failed'
                            device_progress[hostname]['error'] = 'Deploy not confirmed'
                            device_progress[hostname]['stage'] = 'Deploy not confirmed - check device'
                        # Reset device_state back to GI (don't leave as DEPLOYING)
                        try:
                            _opf = Path(f"db/configs/{hostname}/operational.json")
                            if _opf.exists():
                                with open(_opf) as f:
                                    _opd = json.load(f)
                                if _opd.get('device_state') == 'DEPLOYING':
                                    _opd['device_state'] = 'GI'
                                    _opd['install_status'] = 'deploy_failed'
                                    _opd['upgrade_in_progress'] = False
                                    with open(_opf, 'w') as f:
                                        json.dump(_opd, f, indent=4)
                        except:
                            pass
                        ssh.close()
                        return False, "Deploy not confirmed - no install task detected"
                else:
                    with progress_lock:
                        device_progress[hostname]['stage'] = 'Installing...'
                    
                    add_terminal_line("Installing...")
                    from .utils import audit_log as _audit
                    _audit(hostname, conn.get('ip', device.ip), "request system target-stack install", "multi-device-upgrade")
                    install_output = send_and_wait("request system target-stack install", wait_time=15)
                    install_lower = install_output.lower()
                    confirm_output = ""
                    
                    # If "another precheck in-progress", wait and retry
                    if 'another precheck' in install_lower or ('precheck' in install_lower and 'already' in install_lower):
                        add_terminal_line("  Waiting for pre-check to finish...")
                        for retry_n in range(6):
                            time.sleep(10)
                            install_output = send_and_wait("request system target-stack install", wait_time=15)
                            install_lower = install_output.lower()
                            if 'another precheck' not in install_lower and 'already' not in install_lower:
                                break
                            add_terminal_line(f"  Retrying... ({(retry_n + 1) * 10}s)")
                    
                    # DNOS auto-waits: "Precheck in progress, waiting till finished"
                    if 'precheck in progress' in install_lower and 'waiting' in install_lower:
                        add_terminal_line("  DNOS waiting for pre-check...")
                        time.sleep(15)
                        extra = ""
                        try:
                            att = 0
                            while att < 20:
                                if channel.recv_ready():
                                    extra += channel.recv(65535).decode('utf-8', errors='replace')
                                    att = 0
                                else:
                                    att += 1
                                    time.sleep(1)
                                    if att >= 5 and extra:
                                        break
                        except:
                            pass
                        install_output += extra
                        install_lower = install_output.lower()
                    
                    # Only confirm if DNOS is actually prompting
                    if 'yes/no' in install_lower or 'do you want' in install_lower or 'continue' in install_lower:
                        confirm_output = send_and_wait("yes", wait_time=10)
                        add_terminal_line("> yes")
                    elif 'started' in install_lower or 'task id' in install_lower:
                        pass
                    else:
                        add_terminal_line("  No confirmation prompt detected")
                    
                    combined_output = (install_output + confirm_output).lower()
                    
                    install_started = False
                    if 'task id' in combined_output or 'started' in combined_output:
                        install_started = True
                        add_terminal_line("✓ Install started!")
                    elif 'rebooting' in combined_output:
                        install_started = True
                        add_terminal_line("✓ Rebooting!")
                    elif 'error' in combined_output or 'failed' in combined_output:
                        add_terminal_line("✗ Install error")
                    
                    if not install_started:
                        add_terminal_line("⚠ Verify on device")
                    
                    with progress_lock:
                        device_progress[hostname]['status'] = 'success'
                        device_progress[hostname]['progress'] = 100
                        device_progress[hostname]['stage'] = 'Install initiated' if install_started else 'Verify manually'
                
                ssh.close()
                
                # Save stack info to operational.json for status tracking
                try:
                    op_file = Path(f"db/configs/{hostname}/operational.json")
                    op_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Load existing or create new
                    op_data = {}
                    if op_file.exists():
                        with open(op_file) as f:
                            op_data = json.load(f)
                    
                    op_data.update({
                        'dnos_url': dnos_url if dnos_url and dnos_url != 'N/A' else op_data.get('dnos_url'),
                        'gi_url': gi_url if gi_url and gi_url != 'N/A' else op_data.get('gi_url'),
                        'baseos_url': baseos_url if baseos_url and baseos_url != 'N/A' else op_data.get('baseos_url'),
                        'install_status': 'initiated',
                        'install_start': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'install_type': 'gi_deploy' if is_gi_mode else 'upgrade',
                        'device_state': 'DEPLOYING' if is_gi_mode else 'UPGRADING',
                        'recovery_mode_detected': False,
                        'upgrade_in_progress': True,
                        'system_type': system_type,
                    })
                    
                    # Extract version from URL for easier display
                    if dnos_url and dnos_url != 'N/A':
                        dnos_version = dnos_url.split('/')[-1].replace('.tar', '').replace('drivenets_dnos_', '')
                        op_data['dnos_version'] = dnos_version
                    
                    with open(op_file, 'w') as f:
                        json.dump(op_data, f, indent=4)
                    
                    add_terminal_line(f"✓ Saved stack info")
                except Exception as save_err:
                    add_terminal_line(f"⚠ Could not save: {str(save_err)[:30]}")
                
                # ═══ PER-DEVICE POST-DEPLOY: wait for DNOS + auto-restore config ═══
                # Each device waits in its own thread -- no dependency on other devices
                _backup_path = stack.get('_pre_delete_backups', {}).get(hostname)
                _has_backup = _backup_path and Path(_backup_path).exists()
                if True:  # Always wait for DNOS boot to reset device_state
                    with progress_lock:
                        device_progress[hostname]['stage'] = 'Waiting for DNOS boot...'
                    add_terminal_line("Waiting for device to boot DNOS...")
                    
                    _boot_timeout = 1200  # 20 minutes
                    _boot_interval = 20
                    _boot_start = time.time()
                    _config_restored = False
                    
                    while time.time() - _boot_start < _boot_timeout:
                        time.sleep(_boot_interval)
                        _elapsed = int(time.time() - _boot_start)
                        _bm, _bs = divmod(_elapsed, 60)
                        
                        with progress_lock:
                            device_progress[hostname]['stage'] = f'Waiting for DNOS boot... ({_bm}m {_bs}s)'
                        
                        try:
                            from .connection_strategy import connect_for_upgrade
                            _rc = connect_for_upgrade(hostname, timeout=20)
                            if not _rc['connected']:
                                _reason = (_rc.get('abort_reason') or 'unreachable')[:40]
                                add_terminal_line(f"  Probe: {_reason} ({_bm}m {_bs}s)")
                                continue
                            
                            _state = _rc.get('device_state', '')
                            _prompt = _rc.get('prompt_output', '') or ''
                            
                            if _state in ('GI', 'BASEOS_SHELL'):
                                add_terminal_line(f"Still in GI mode ({_bm}m {_bs}s)")
                                try:
                                    _rc['ssh'].close()
                                except:
                                    pass
                                continue
                            
                            if _state == 'DN_RECOVERY':
                                add_terminal_line(f"[!!] RECOVERY mode ({_bm}m {_bs}s)")
                                try:
                                    _rc['ssh'].close()
                                except:
                                    pass
                                continue
                            
                            _is_booted = _state in ('DNOS', 'STANDALONE')
                            if not _is_booted and '#' in _prompt:
                                _is_booted = True
                            
                            if not _is_booted:
                                add_terminal_line(f"  State: {_state or 'unknown'} ({_bm}m {_bs}s)")
                                try:
                                    _rc['ssh'].close()
                                except:
                                    pass
                                continue
                            
                            # Verify system health: show system -> check NCP UP + NCC active-up
                            _ch_health = _rc.get('channel')
                            _health_ok = False
                            _health_info = ""
                            
                            if _ch_health:
                                try:
                                    with progress_lock:
                                        device_progress[hostname]['stage'] = 'Checking system health...'
                                    
                                    _ch_health.sendall(b"show system | no-more\n")
                                    time.sleep(5)
                                    _sys_out = ""
                                    _rd = 0
                                    while _rd < 10:
                                        if _ch_health.recv_ready():
                                            _sys_out += _ch_health.recv(8192).decode('utf-8', errors='replace')
                                            _rd = 0
                                        else:
                                            _rd += 1
                                            time.sleep(0.5)
                                            if _rd >= 3 and _sys_out:
                                                break
                                    
                                    _ncp_up_c, _ncp_total_c = 0, 0
                                    _ncc_up_c, _ncc_total_c = 0, 0
                                    
                                    for _sl in _sys_out.split('\n'):
                                        if '|' in _sl:
                                            _parts = [p.strip() for p in _sl.split('|')]
                                            if len(_parts) >= 5:
                                                _ntype = _parts[1].upper() if len(_parts) > 1 else ""
                                                _ostate = _parts[4].lower() if len(_parts) > 4 else ""
                                                
                                                if 'NCP' in _ntype:
                                                    _ncp_total_c += 1
                                                    if _ostate == 'up':
                                                        _ncp_up_c += 1
                                                elif 'NCC' in _ntype:
                                                    _ncc_total_c += 1
                                                    if 'up' in _ostate:
                                                        _ncc_up_c += 1
                                    
                                    if _ncp_total_c > 0 and _ncp_up_c == 0:
                                        add_terminal_line(f"NCP initializing (0/{_ncp_total_c} UP), waiting... ({_bm}m {_bs}s)")
                                        try:
                                            _rc['ssh'].close()
                                        except:
                                            pass
                                        continue
                                    
                                    if _ncc_total_c > 0 and _ncc_up_c == 0:
                                        add_terminal_line(f"NCC initializing (0/{_ncc_total_c} UP), waiting... ({_bm}m {_bs}s)")
                                        try:
                                            _rc['ssh'].close()
                                        except:
                                            pass
                                        continue
                                    
                                    if _ncp_total_c > 0:
                                        _health_info = f"NCP {_ncp_up_c}/{_ncp_total_c} UP"
                                    if _ncc_total_c > 0:
                                        _sep = ", " if _health_info else ""
                                        _health_info += f"{_sep}NCC {_ncc_up_c}/{_ncc_total_c} UP"
                                    if not _health_info:
                                        _health_info = "CLI ready"
                                    
                                    _health_ok = True
                                    
                                except Exception:
                                    _health_ok = True
                                    _health_info = "CLI ready"
                            else:
                                _health_ok = True
                                _health_info = "connected"
                            
                            if not _health_ok:
                                try:
                                    _rc['ssh'].close()
                                except:
                                    pass
                                continue
                            
                            if True:
                                add_terminal_line(f"DNOS online: {_health_info} ({_bm}m {_bs}s)")
                                
                                # Fetch the new management IP from the live device
                                _new_mgmt_ip = None
                                _new_conn_method = None
                                try:
                                    _ch = _rc.get('channel')
                                    if _ch:
                                        _ch.sendall(b"show interfaces management | no-more\n")
                                        time.sleep(3)
                                        _mgmt_out = ""
                                        while _ch.recv_ready():
                                            _mgmt_out += _ch.recv(8192).decode('utf-8', errors='replace')
                                            time.sleep(0.3)
                                        
                                        _ncc_mgmt_ip = None
                                        for _ml in _mgmt_out.split('\n'):
                                            _ml_lower = _ml.lower()
                                            if 'up' not in _ml_lower:
                                                continue
                                            _ip_m = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', _ml)
                                            if not _ip_m:
                                                continue
                                            _pip = _ip_m.group(1)
                                            if _pip.startswith('127.') or _pip.startswith('0.'):
                                                continue
                                            if re.search(r'\bmgmt0\b', _ml_lower) or re.search(r'\bmgmt\s*\|', _ml_lower):
                                                _new_mgmt_ip = _pip
                                            elif 'mgmt-ncc' in _ml_lower and not _ncc_mgmt_ip:
                                                _ncc_mgmt_ip = _pip
                                                if not _new_mgmt_ip:
                                                    _new_mgmt_ip = _pip
                                        
                                        if not _new_mgmt_ip:
                                            _ip_m2 = re.search(r'inet\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', _mgmt_out)
                                            if _ip_m2:
                                                _pip2 = _ip_m2.group(1)
                                                if not _pip2.startswith('127.'):
                                                    _new_mgmt_ip = _pip2
                                except Exception:
                                    pass
                                
                                # Try SSH to the new mgmt IP to confirm it works
                                if _new_mgmt_ip:
                                    add_terminal_line(f"New mgmt IP: {_new_mgmt_ip}")
                                    _ssh_cred_sets = [
                                        ('dnroot', 'dnroot'),
                                        ('dn', 'drivenets'),
                                        ('admin', 'admin'),
                                        ('root', 'drivenets'),
                                    ]
                                    _ssh_ok = False
                                    _working_creds = ('dnroot', 'dnroot')
                                    for _tu, _tp in _ssh_cred_sets:
                                        try:
                                            import paramiko as _pmk
                                            _test_ssh = _pmk.SSHClient()
                                            _test_ssh.set_missing_host_key_policy(_pmk.AutoAddPolicy())
                                            _test_ssh.connect(
                                                _new_mgmt_ip,
                                                username=_tu, password=_tp,
                                                timeout=10, banner_timeout=10, auth_timeout=10,
                                                allow_agent=False, look_for_keys=False
                                            )
                                            _test_ssh.close()
                                            _ssh_ok = True
                                            _working_creds = (_tu, _tp)
                                            break
                                        except _pmk.AuthenticationException:
                                            continue
                                        except Exception:
                                            break
                                    if _ssh_ok:
                                        _new_conn_method = f"SSH->MGMT ({_new_mgmt_ip})"
                                        add_terminal_line(f"SSH to {_new_mgmt_ip} OK (user={_working_creds[0]})")
                                    else:
                                        add_terminal_line(f"SSH to {_new_mgmt_ip} not ready yet")
                                
                                # Reset device_state to DNOS in operational.json
                                try:
                                    _opf = Path(f"db/configs/{hostname}/operational.json")
                                    if _opf.exists():
                                        with open(_opf) as f:
                                            _opd = json.load(f)
                                        _opd['device_state'] = 'DNOS'
                                        _opd['recovery_mode_detected'] = False
                                        _opd['upgrade_in_progress'] = False
                                        _opd['install_status'] = 'completed'
                                        _opd['install_finish'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        if _new_mgmt_ip:
                                            _opd['mgmt_ip'] = _new_mgmt_ip
                                            _opd['ssh_host'] = _new_mgmt_ip
                                        elif _rc.get('ip'):
                                            _fallback_ip = str(_rc['ip'])
                                            if 'console' not in _fallback_ip.lower():
                                                _opd['mgmt_ip'] = _fallback_ip
                                                _opd['ssh_host'] = _fallback_ip
                                            else:
                                                _opd['mgmt_ip'] = _dev_obj.ip if hasattr(_dev_obj, 'ip') else _fallback_ip
                                                _opd['ssh_host'] = _opd['mgmt_ip']
                                        if _ncc_mgmt_ip:
                                            _opd['ncc_mgmt_ip'] = _ncc_mgmt_ip
                                        if _new_conn_method:
                                            _opd['connection_method'] = _new_conn_method
                                        elif _rc.get('method'):
                                            _m = _rc['method']
                                            if hasattr(_m, 'value'):
                                                _m = _m.value
                                            _opd['connection_method'] = _m
                                        # Save active NCC ID (may have changed after reboot)
                                        _post_ncc = _rc.get('ncc_id')
                                        if _post_ncc is not None:
                                            _opd['deploy_ncc_id'] = str(_post_ncc)
                                        _post_vm = _rc.get('active_ncc_vm')
                                        if _post_vm:
                                            _opd['active_ncc_vm'] = _post_vm
                                        with open(_opf, 'w') as f:
                                            json.dump(_opd, f, indent=4)
                                except Exception:
                                    pass
                                
                                # Also update the device entry in devices.json
                                if _new_mgmt_ip:
                                    try:
                                        _dev_file = Path("db/devices.json")
                                        if _dev_file.exists():
                                            with open(_dev_file) as f:
                                                _dev_data = json.load(f)
                                            for _dd in _dev_data.get('devices', []):
                                                if _dd.get('hostname') == hostname:
                                                    _dd['ip'] = _new_mgmt_ip
                                                    break
                                            with open(_dev_file, 'w') as f:
                                                json.dump(_dev_data, f, indent=2)
                                    except Exception:
                                        pass
                                
                                # Push backed-up config if available
                                if _has_backup:
                                    with progress_lock:
                                        device_progress[hostname]['stage'] = 'Restoring config...'
                                    
                                    # Wait for SSH to stabilize after DNOS boot
                                    add_terminal_line("Waiting for SSH to stabilize (30s)...")
                                    time.sleep(30)
                                    
                                    add_terminal_line("Restoring pre-delete config...")
                                    
                                    try:
                                        _dev_obj = next(
                                            (d for d in multi_ctx.devices if d.hostname == hostname), None)
                                        if _dev_obj:
                                            if _new_mgmt_ip:
                                                _dev_obj.ip = _new_mgmt_ip
                                            
                                            from .config_pusher import ConfigPusher
                                            _pusher = ConfigPusher()
                                            with open(_backup_path) as f:
                                                _cfg = f.read()
                                            _lines = [l for l in _cfg.strip().split('\n')
                                                       if not l.startswith('#')]
                                            _cfg_no_comments = '\n'.join(_lines)
                                            _src_ver = stack.get('_source_version', '')
                                            _tgt_ver = stack.get('_target_version', '')
                                            _cfg_clean, _stripped_items = sanitize_config_for_version(
                                                _cfg_no_comments, source_version=_src_ver, target_version=_tgt_ver)
                                            if _stripped_items:
                                                add_terminal_line(f"Sanitized config: removed {len(_stripped_items)} version-incompatible items ({_src_ver} -> {_tgt_ver})")
                                            
                                            _restore_ok = False
                                            _orig_user = _dev_obj.username
                                            _orig_pw = _dev_obj.password
                                            _restore_creds = [
                                                (_orig_user, _orig_pw),
                                                ('dnroot', Device.encode_password('dnroot')),
                                                ('dn', Device.encode_password('drivenets')),
                                                ('admin', Device.encode_password('admin')),
                                            ]
                                            _seen_creds = set()
                                            _unique_restore_creds = []
                                            for _rcu, _rcp in _restore_creds:
                                                _ck = f"{_rcu}:{_rcp}"
                                                if _ck not in _seen_creds:
                                                    _seen_creds.add(_ck)
                                                    _unique_restore_creds.append((_rcu, _rcp))
                                            
                                            for _rcu, _rcp in _unique_restore_creds:
                                                _dev_obj.username = _rcu
                                                _dev_obj.password = _rcp
                                                for _restore_attempt in range(2):
                                                    _ok, _msg = _pusher.push_config(
                                                        _dev_obj, _cfg_clean,
                                                        config_name=f"auto_restore_{hostname}")
                                                    if _ok:
                                                        _config_restored = True
                                                        _restore_ok = True
                                                        add_terminal_line(f"Config restored ({len(_lines)} lines)")
                                                        break
                                                    else:
                                                        _m_lower = _msg.lower() if _msg else ""
                                                        if 'auth' in _m_lower:
                                                            add_terminal_line(f"Auth failed ({_rcu}), trying next credential...")
                                                            break
                                                        if 'timeout' in _m_lower or 'refused' in _m_lower or 'reset' in _m_lower:
                                                            add_terminal_line(f"Config push attempt {_restore_attempt+1}/2: {_msg[:35]}")
                                                            if _restore_attempt < 1:
                                                                time.sleep(20)
                                                                continue
                                                        add_terminal_line(f"Config push failed: {_msg[:40]}")
                                                        break
                                                if _restore_ok:
                                                    break
                                            _dev_obj.username = _orig_user
                                            _dev_obj.password = _orig_pw
                                    except Exception as _re:
                                        add_terminal_line(f"Restore error: {str(_re)[:35]}")
                                
                                try:
                                    _rc['ssh'].close()
                                except:
                                    pass
                                break
                        except Exception as _boot_err:
                            add_terminal_line(f"  Error: {str(_boot_err)[:35]} ({_bm}m {_bs}s)")
                            pass
                    
                    if _config_restored:
                        with progress_lock:
                            device_progress[hostname]['stage'] = 'Done (config restored)'
                        return True, "Upgrade + config restore done"
                    else:
                        with progress_lock:
                            device_progress[hostname]['stage'] = 'Done (config NOT restored)'
                        add_terminal_line("Config not auto-restored, use [R] to retry")
                
                return True, f"Upgrade initiated {'(GI deploy)' if is_gi_mode else ''}successfully"
                
            except Exception as e:
                with progress_lock:
                    device_progress[hostname]['status'] = 'failed'
                    device_progress[hostname]['error'] = str(e)[:50]
                try:
                    ssh.close()
                except:
                    pass
                return False, str(e)
        
        # Execute in parallel with Ctrl+C handling
        results = {}
        cancelled = False
        try:
            with Live(render_multi_device_panel(), refresh_per_second=1, console=console, vertical_overflow="crop") as live:
                with ThreadPoolExecutor(max_workers=len(multi_ctx.devices)) as executor:
                    futures = {executor.submit(push_to_device, dev): dev for dev in multi_ctx.devices}
                    
                    try:
                        while not all(f.done() for f in futures):
                            live.update(render_multi_device_panel())
                            time.sleep(1.0)
                    except KeyboardInterrupt:
                        console.print("\n[yellow]⚠ Cancelling... (push operations may continue on devices)[/yellow]")
                        cancelled = True
                        executor.shutdown(wait=False, cancel_futures=True)
                    
                    # Final update
                    live.update(render_multi_device_panel())
                    
                    for future, dev in futures.items():
                        try:
                            if not future.cancelled():
                                results[dev.hostname] = future.result(timeout=1)
                            else:
                                results[dev.hostname] = (False, "Cancelled")
                        except Exception as e:
                            results[dev.hostname] = (False, str(e))
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠ Interrupted[/yellow]")
            cancelled = True
        
        # Summary
        total_time = int(time.time() - start_time)
        console.print(f"\n{'═' * 40}")
        if cancelled:
            console.print(f"[bold yellow]Interrupted[/bold yellow] (after {total_time}s)")
        else:
            console.print(f"[bold]Results:[/bold] (completed in {total_time}s)")
        
        success_count = 0
        for hostname, (success, message) in results.items():
            if success:
                console.print(f"  [green]✓ {hostname}:[/green] {message}")
                success_count += 1
            else:
                console.print(f"  [red]✗ {hostname}:[/red] {message}")
        
        console.print(f"\n[bold]Summary:[/bold] {success_count}/{len(results)} devices upgraded")
        
        if success_count > 0:
            # Collect all successfully upgraded devices for post-deploy tracking
            _upgraded_hosts = [h for h, (s, _) in results.items() if s]
            pre_delete_backups = stack.get('_pre_delete_backups', {})
            restore_targets = {h: str(p) for h, p in pre_delete_backups.items()
                               if h in _upgraded_hosts} if pre_delete_backups else {}
            
            for _h, _bp in restore_targets.items():
                try:
                    op_file = Path(f"db/configs/{_h}/operational.json")
                    op_data = {}
                    if op_file.exists():
                        with open(op_file) as f:
                            op_data = json.load(f)
                    op_data['pre_delete_backup'] = _bp
                    op_data['pre_delete_backup_time'] = datetime.now().isoformat()
                    with open(op_file, 'w') as f:
                        json.dump(op_data, f, indent=4)
                except:
                    pass
            
            # ═══════════════════════════════════════════════════════════════
            # POST-DEPLOY: Wait for all devices to boot DNOS + auto-restore
            # Always wait, regardless of whether config backups exist
            # ═══════════════════════════════════════════════════════════════
            _post_state = {}  # hostname -> {status, elapsed, ip, config_restored}
            for _h in _upgraded_hosts:
                _post_state[_h] = {
                    'status': 'rebooting', 'elapsed': 0, 'ip': '',
                    'config_backup': restore_targets.get(_h),
                    'config_restored': False, 'config_msg': '',
                    'attempts': 0, 'last_probe': '',
                }
            
            _post_start = time.time()
            _post_max = 1200  # 20 minutes max
            _all_done = len(_upgraded_hosts) == 0
            
            def _render_post_deploy_panel():
                from rich.table import Table as _PDT
                from rich.console import Group
                _we = int(time.time() - _post_start)
                _wm, _ws = divmod(_we, 60)
                
                tbl = _PDT(title=f"Post-Deploy Progress  ⏱ {_wm:02d}:{_ws:02d}", box=box.ROUNDED, expand=True)
                tbl.add_column("Device", style="cyan", width=14)
                tbl.add_column("Status", width=20)
                tbl.add_column("Elapsed", width=10, justify="right")
                tbl.add_column("Config Restore", width=30)
                
                for _h in _upgraded_hosts:
                    _s = _post_state[_h]
                    _em, _es = divmod(_s['elapsed'], 60)
                    _elapsed_str = f"{_em}m {_es}s"
                    
                    if _s['status'] == 'rebooting':
                        _status = f"[yellow]⏳ Rebooting[/yellow] [dim]({_s['attempts']})[/dim]"
                    elif _s['status'] in ('gi_detected', 'gi_installing'):
                        _status = f"[cyan]⚙ GI installing[/cyan] [dim]({_s['attempts']})[/dim]"
                    elif _s['status'] == 'ncp_waiting':
                        _status = f"[yellow]⚙ NCP initializing[/yellow] [dim]({_s['attempts']})[/dim]"
                    elif _s['status'] == 'dnos_up':
                        _status = "[green]✓ DNOS UP[/green]"
                    elif _s['status'] == 'timeout':
                        _status = "[red]⏰ Timeout[/red]"
                    elif _s['status'] == 'done':
                        _status = "[bold green]✅ Ready[/bold green]"
                    else:
                        _status = f"[dim]{_s['status']}[/dim]"
                    
                    if _s['config_backup']:
                        if _s['config_restored']:
                            _cfg = f"[green]✓ Restored[/green] {_s['config_msg']}"
                        elif _s['status'] in ('dnos_up', 'done'):
                            _cfg = "[cyan]Pushing...[/cyan]"
                        elif _s['status'] == 'ncp_waiting':
                            _cfg = "[yellow]Waiting for NCP...[/yellow]"
                        elif _s['config_msg']:
                            _cfg = f"[yellow]{_s['config_msg'][:28]}[/yellow]"
                        else:
                            _cfg = "[dim]Waiting for DNOS...[/dim]"
                    else:
                        if _s['status'] in ('dnos_up', 'done'):
                            _cfg = "[dim]No backup (use [P] to push)[/dim]"
                        else:
                            _cfg = "[dim]No backup[/dim]"
                    
                    tbl.add_row(_h, _status, _elapsed_str, _cfg)
                
                _remaining = _post_max - int(time.time() - _post_start)
                _rm, _rs = divmod(max(0, _remaining), 60)
                footer = f"[dim]Timeout in {_rm}m {_rs}s — Ctrl+C to skip wait[/dim]"
                
                from rich.panel import Panel as _PDP
                from rich.columns import Columns
                return _PDP(
                    Group(tbl, Text(footer, justify="center")),
                    title="[bold]Waiting for devices to come online[/bold]",
                    border_style="cyan", expand=True
                )
            
            console.print(f"\n[bold cyan]{'═' * 50}[/bold cyan]")
            console.print(f"[bold]⏳ Waiting for {len(_upgraded_hosts)} device(s) to boot DNOS...[/bold]")
            if restore_targets:
                console.print(f"[dim]Config will be auto-restored when devices come online.[/dim]")
            console.print(f"[dim]Timeout: 20 minutes. Ctrl+C to skip.[/dim]\n")
            
            try:
                with Live(_render_post_deploy_panel(), refresh_per_second=0.5, console=console) as _post_live:
                    while not _all_done and (time.time() - _post_start) < _post_max:
                        for _h in _upgraded_hosts:
                            _s = _post_state[_h]
                            _s['elapsed'] = int(time.time() - _post_start)
                            
                            if _s['status'] in ('done', 'timeout'):
                                continue
                            
                            _dev = next((d for d in multi_ctx.devices if d.hostname == _h), None)
                            if not _dev:
                                _s['status'] = 'done'
                                continue
                            
                            _pw_raw = getattr(_dev, 'password', 'dnroot') or 'dnroot'
                            try:
                                _pw = _dev.get_password() if hasattr(_dev, 'get_password') else _pw_raw
                            except Exception:
                                _pw = _pw_raw
                            _s['attempts'] += 1
                            
                            try:
                                import paramiko as _pm
                                _ssh = _pm.SSHClient()
                                _ssh.set_missing_host_key_policy(_pm.AutoAddPolicy())
                                from .utils import resolve_device_ip
                                _rip, _rm = resolve_device_ip(_dev, timeout=2.0)
                                _ip = _rip or _dev.ip
                                if _ip and 'console' in str(_ip).lower():
                                    _ip = _dev.ip
                                _post_cred_sets = [
                                    ('dnroot', _pw),
                                    ('dnroot', 'dnroot'),
                                    ('dn', 'drivenets'),
                                    ('admin', 'admin'),
                                    ('root', 'drivenets'),
                                ]
                                _post_seen = set()
                                _post_unique = []
                                for _pu, _pp in _post_cred_sets:
                                    _pk = f"{_pu}:{_pp}"
                                    if _pk not in _post_seen:
                                        _post_seen.add(_pk)
                                        _post_unique.append((_pu, _pp))
                                _post_connected = False
                                _post_working_user = 'dnroot'
                                _post_working_pw = 'dnroot'
                                for _pu, _pp in _post_unique:
                                    try:
                                        _ssh = _pm.SSHClient()
                                        _ssh.set_missing_host_key_policy(_pm.AutoAddPolicy())
                                        _ssh.connect(_ip, username=_pu, password=_pp, timeout=10,
                                                    allow_agent=False, look_for_keys=False)
                                        _post_connected = True
                                        _post_working_user = _pu
                                        _post_working_pw = _pp
                                        break
                                    except _pm.AuthenticationException:
                                        continue
                                    except Exception:
                                        raise
                                if not _post_connected:
                                    raise _pm.AuthenticationException("All credential sets failed")
                                _ch = _ssh.invoke_shell(width=200, height=50)
                                time.sleep(3)
                                _out = ""
                                if _ch.recv_ready():
                                    _out = _ch.recv(65535).decode('utf-8', errors='replace')
                                _ch.send("\r\n")
                                time.sleep(2)
                                if _ch.recv_ready():
                                    _out += _ch.recv(65535).decode('utf-8', errors='replace')
                                _ol = _out.lower()
                                _is_gi = 'gi(' in _ol or 'gi#' in _ol or 'gi>' in _ol
                                _is_dnos = '#' in _out and 'gi' not in _ol and 'recovery' not in _ol and '~$' not in _out
                                
                                # Identity verification: check hostname in prompt
                                # After system delete, DHCP may reassign mgmt0 IP to
                                # a different device. Reject if prompt doesn't match.
                                _identity_ok = True
                                if _is_dnos:
                                    _h_lower = _h.lower().replace('-', '').replace('_', '')
                                    _prompt_lower = _ol.replace('-', '').replace('_', '')
                                    if _h_lower not in _prompt_lower:
                                        _identity_ok = False
                                elif _is_gi:
                                    pass
                                
                                if not _identity_ok:
                                    _ssh.close()
                                    _s['last_probe'] = f'Wrong device at {_ip}, trying alt IPs...'
                                    # Try ncc_mgmt_ip as fallback
                                    try:
                                        _opf2 = Path(f"db/configs/{_h}/operational.json")
                                        if _opf2.exists():
                                            with open(_opf2) as _f2:
                                                _od2 = json.load(_f2)
                                            _ncc_ip = _od2.get('ncc_mgmt_ip')
                                            if _ncc_ip and _ncc_ip != _ip:
                                                _ip = _ncc_ip
                                                _s['last_probe'] = f'Trying NCC mgmt IP {_ncc_ip}...'
                                    except Exception:
                                        pass
                                    continue
                                
                                _ncp_ready = True
                                if _is_dnos and _s.get('config_backup'):
                                    try:
                                        _ch.send("show system | no-more\r\n")
                                        time.sleep(5)
                                        _sys_out = ""
                                        if _ch.recv_ready():
                                            _sys_out = _ch.recv(65535).decode('utf-8', errors='replace')
                                        _sys_lo = _sys_out.lower()
                                        if 'initializing' in _sys_lo or 'not-ready' in _sys_lo:
                                            _ncp_ready = False
                                    except Exception:
                                        pass
                                
                                _ssh.close()
                                
                                if _is_gi:
                                    _s['status'] = 'gi_installing'
                                    _s['ip'] = _ip
                                    _s['last_probe'] = 'GI active, waiting for DNOS...'
                                elif _is_dnos:
                                    _s['ip'] = _ip
                                    
                                    if not _ncp_ready:
                                        _s['status'] = 'ncp_waiting'
                                        _s['last_probe'] = 'NCP initializing, waiting...'
                                        continue
                                    
                                    _s['status'] = 'dnos_up'
                                    
                                    # Update operational.json
                                    try:
                                        _opf = Path(f"db/configs/{_h}/operational.json")
                                        _opd = {}
                                        if _opf.exists():
                                            with open(_opf) as f:
                                                _opd = json.load(f)
                                        _opd['device_state'] = 'DNOS'
                                        _opd['recovery_mode_detected'] = False
                                        _opd['upgrade_in_progress'] = False
                                        _opd['install_status'] = 'completed'
                                        _opd['install_finish'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        if _ip and 'console' not in str(_ip).lower():
                                            _opd['mgmt_ip'] = _ip
                                            _opd['ssh_host'] = _ip
                                        with open(_opf, 'w') as f:
                                            json.dump(_opd, f, indent=4)
                                    except Exception:
                                        pass
                                    
                                    # Auto-restore config if backup exists
                                    if _s['config_backup']:
                                        _post_live.update(_render_post_deploy_panel())
                                        try:
                                            from .config_pusher import ConfigPusher
                                            _pusher = ConfigPusher()
                                            with open(_s['config_backup']) as f:
                                                _cfg = f.read()
                                            _lines = [l for l in _cfg.strip().split('\n') if not l.startswith('#')]
                                            _cfg_clean = '\n'.join(_lines)
                                            
                                            _orig_dev_user = _dev.username
                                            _orig_dev_pw = _dev.password
                                            _dev.username = _post_working_user
                                            _dev.password = Device.encode_password(_post_working_pw)
                                            
                                            _ok, _msg = _pusher.push_config(_dev, _cfg_clean,
                                                config_name=f"auto_restore_{_h}")
                                            if _ok:
                                                _s['config_restored'] = True
                                                _s['config_msg'] = f"({len(_lines)} lines)"
                                            else:
                                                _post_restore_creds = [
                                                    ('dnroot', 'dnroot'),
                                                    ('dn', 'drivenets'),
                                                    ('admin', 'admin'),
                                                ]
                                                for _pru, _prp in _post_restore_creds:
                                                    if _pru == _post_working_user and _prp == _post_working_pw:
                                                        continue
                                                    _dev.username = _pru
                                                    _dev.password = Device.encode_password(_prp)
                                                    _ok2, _msg2 = _pusher.push_config(_dev, _cfg_clean,
                                                        config_name=f"auto_restore_{_h}")
                                                    if _ok2:
                                                        _s['config_restored'] = True
                                                        _s['config_msg'] = f"({len(_lines)} lines)"
                                                        break
                                                if not _s.get('config_restored'):
                                                    _s['config_msg'] = _msg[:40]
                                            _dev.username = _orig_dev_user
                                            _dev.password = _orig_dev_pw
                                        except Exception as _pe:
                                            _s['config_msg'] = f"Error: {str(_pe)[:30]}"
                                    
                                    _s['status'] = 'done'
                            except Exception:
                                pass
                        
                        _post_live.update(_render_post_deploy_panel())
                        
                        # Check if all done
                        _all_done = all(_post_state[h]['status'] in ('done', 'timeout')
                                       for h in _upgraded_hosts)
                        if _all_done:
                            break
                        
                        time.sleep(20)
                    
                    # Mark remaining as timeout
                    for _h in _upgraded_hosts:
                        _s = _post_state[_h]
                        _s['elapsed'] = int(time.time() - _post_start)
                        if _s['status'] not in ('done',):
                            _s['status'] = 'timeout'
                    _post_live.update(_render_post_deploy_panel())
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]⚠ Wait skipped. Devices may still be rebooting.[/yellow]")
                console.print("[dim]Use [R] Refresh to check device state later.[/dim]")
            
            # Report restore failures prominently
            _failed_restores = [h for h in _upgraded_hosts
                                if _post_state[h].get('config_backup')
                                and not _post_state[h].get('config_restored')]
            if _failed_restores:
                console.print(f"\n[bold red]⚠ Config restore FAILED on {len(_failed_restores)} device(s):[/bold red]")
                for _fh in _failed_restores:
                    _fs = _post_state[_fh]
                    _reason = _fs.get('config_msg') or _fs.get('status', 'unknown')
                    _backup_path = _fs.get('config_backup', 'N/A')
                    console.print(f"  [red]• {_fh}[/red]: {_reason}")
                    console.print(f"    Backup file: {_backup_path}")
                console.print("[yellow]Use [R] Restore Pre-Delete Config to retry manually.[/yellow]")
            
            # Final summary
            _up_count = sum(1 for h in _upgraded_hosts if _post_state[h]['status'] == 'done')
            _restored = sum(1 for h in _upgraded_hosts if _post_state[h].get('config_restored'))
            _total_elapsed = int(time.time() - _post_start)
            _tm, _ts = divmod(_total_elapsed, 60)
            
            console.print(f"\n[bold]{'═' * 50}[/bold]")
            console.print(f"[bold]Post-Deploy Summary[/bold] ({_tm}m {_ts}s)")
            for _h in _upgraded_hosts:
                _s = _post_state[_h]
                if _s['status'] == 'done':
                    _extra = f" | Config restored" if _s.get('config_restored') else ""
                    console.print(f"  [green]✓ {_h}: DNOS UP{_extra}[/green]")
                else:
                    console.print(f"  [yellow]⚠ {_h}: {_s['status']} — check with [R] Refresh[/yellow]")
            
            # Save upgrade timing to history for future estimates
            _full_elapsed = int(time.time() - start_time)
            try:
                _hf = Path("db/upgrade_history.json")
                _hist = {'entries': []}
                if _hf.exists():
                    with open(_hf) as f:
                        _hist = json.load(f)
                _flow = 'delete_deploy' if stack.get('_requires_delete_deploy') else (
                    'gi_deploy' if any(d.hostname not in stack.get('_devices_with_dnos_set', set())
                                       for d in multi_ctx.devices) else 'in_place')
                _hist['entries'].append({
                    'timestamp': datetime.now().isoformat(),
                    'devices': [d.hostname for d in multi_ctx.devices],
                    'flow_type': _flow,
                    'elapsed_s': _full_elapsed,
                    'success_count': success_count,
                    'total_count': len(results),
                    'post_deploy_s': int(time.time() - _post_start) if '_post_start' in dir() else 0,
                })
                _hist['entries'] = _hist['entries'][-50:]
                with open(_hf, 'w') as f:
                    json.dump(_hist, f, indent=2)
            except Exception:
                pass
        
        return success_count > 0
        
    except Exception as e:
        # Use Text() to render error message as plain text to avoid Rich markup conflicts
        from rich.text import Text
        error_msg = str(e)
        console.print(Text(f"Error: {error_msg}", style="red"))
        import traceback
        traceback_text = traceback.format_exc()
        console.print(Text(traceback_text, style="dim"))
        return False


def _run_stag_pool_check(multi_ctx: 'MultiDeviceContext'):
    """Show Stag usage from cached configs (fast) or live from Linux shell."""
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]              🔍 Stag Pool Check (QinQ Validation)                  [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════════[/bold cyan]")
    console.print(f"[dim]PR-86760 limit: {multi_ctx.STAG_LIMIT} unique Stags (parent + outer-tag)[/dim]\n")
    
    from rich.table import Table as RichTable
    
    # Check if we have cached kernel-based data (from previous live check)
    has_cached_kernel_data = hasattr(multi_ctx, 'cached_pool_status') and multi_ctx.cached_pool_status
    
    if has_cached_kernel_data:
        # Show accurate kernel-based data
        console.print("[bold green]✓ Pool Status (from Live Kernel Check):[/bold green]\n")
        
        table = RichTable(box=box.ROUNDED)
        table.add_column("Device", style="cyan")
        table.add_column("PH Pool", justify="right")
        table.add_column("Stag Pool", justify="right")
        table.add_column("Can Add", justify="right", style="green")
        table.add_column("Bottleneck", justify="left")
        
        for dev in multi_ctx.devices:
            pool_data = multi_ctx.cached_pool_status.get(dev.hostname, {})
            if pool_data:
                ph_used = pool_data.get('ph_pool_used', 0)
                ph_max = pool_data.get('ph_pool_max', 0)
                stag_used = pool_data.get('stag_pool_used', 0)
                stag_max = pool_data.get('stag_pool_max', 0)
                max_svc = pool_data.get('max_additional_pwhe_services', 0)
                bottleneck = pool_data.get('bottleneck', 'Unknown').split('(')[0].strip()
                
                table.add_row(
                    dev.hostname,
                    f"{ph_used:,}/{ph_max:,}",
                    f"{stag_used:,}/{stag_max:,}",
                    f"{max_svc:,}",
                    bottleneck
                )
            else:
                table.add_row(dev.hostname, "[dim]N/A[/dim]", "[dim]N/A[/dim]", "[dim]N/A[/dim]", "[dim]No data[/dim]")
        
        console.print(table)
        
        # Show options
        console.print("\n[bold]Options:[/bold]")
        console.print("  [1] Show breakdown by parent interface (from config)")
        console.print("  [2] [green]Refresh live from Linux shell[/green]")
        console.print("  [B] Back")
    else:
        # Show config-based estimate (no kernel data yet)
        console.print("[bold]Current Stag Usage (from cached config):[/bold]\n")
        console.print("[dim]💡 Select [2] for accurate kernel-based data[/dim]\n")
        
        table = RichTable(box=box.ROUNDED)
        table.add_column("Device", style="cyan")
        table.add_column("Stags", justify="right")
        table.add_column("Usage", justify="center", width=15)
        table.add_column("Status", justify="center")
        table.add_column("Remaining", justify="right")
        
        for dev in multi_ctx.devices:
            stag_info = multi_ctx.stag_usage.get(dev.hostname, {})
            if stag_info:
                count = stag_info.get('count', 0)
                pct = stag_info.get('percentage', 0)
                filled = int(pct / 10)
                bar = '█' * filled + '░' * (10 - filled)
                
                if stag_info.get('exceeded'):
                    status = "[red]⛔ EXCEEDED[/red]"
                elif stag_info.get('at_risk'):
                    status = "[yellow]⚠ HIGH[/yellow]"
                else:
                    status = "[green]✓ OK[/green]"
                
                table.add_row(
                    dev.hostname,
                    f"{count:,}",
                    f"{pct}% {bar}",
                    status,
                    f"{stag_info.get('remaining', 0):,}"
                )
            else:
                table.add_row(dev.hostname, "[dim]0[/dim]", "[dim]0%[/dim]", "[dim]No QinQ[/dim]", "[dim]4,000[/dim]")
        
        console.print(table)
        
        # Show options
        console.print("\n[bold]Options:[/bold]")
        console.print("  [1] Show breakdown by parent interface")
        console.print("  [2] [yellow]Check live from Linux shell (SSH into devices)[/yellow]")
        console.print("  [B] Back")
    
    choice = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="b").lower()
    
    if choice == "1":
        # Show breakdown by parent
        for dev in multi_ctx.devices:
            config = multi_ctx.configs.get(dev.hostname, "")
            if not config:
                continue
            
            # Parse parent breakdown
            stags = set()
            current_parent = None
            
            for line in config.split('\n'):
                iface_match = re.match(r'^  (\S+\.\d+)\s*$', line)
                if iface_match:
                    current_parent = iface_match.group(1).rsplit('.', 1)[0]
                    continue
                if current_parent and 'outer-tag' in line:
                    outer_match = re.search(r'outer-tag\s+(\d+)', line)
                    if outer_match:
                        stags.add((current_parent, int(outer_match.group(1))))
            
            # Group by parent
            parent_counts = {}
            for parent, outer in stags:
                if parent not in parent_counts:
                    parent_counts[parent] = set()
                parent_counts[parent].add(outer)
            
            if parent_counts:
                console.print(f"\n[bold cyan]═══ {dev.hostname} - {len(stags)} Stags ═══[/bold cyan]")
                
                breakdown = RichTable(box=box.SIMPLE)
                breakdown.add_column("Parent", style="cyan")
                breakdown.add_column("Count", justify="right")
                breakdown.add_column("Outer Tags", justify="center")
                
                for parent in sorted(parent_counts.keys())[:15]:
                    tags = sorted(parent_counts[parent])
                    breakdown.add_row(parent, str(len(tags)), f"{min(tags)}-{max(tags)}")
                
                console.print(breakdown)
                if len(parent_counts) > 15:
                    console.print(f"[dim]  ... and {len(parent_counts) - 15} more parents[/dim]")
    
    elif choice == "2":
        # Live check from Linux shell
        console.print("\n[bold cyan]🔍 Querying LIVE pool status from device kernel...[/bold cyan]")
        console.print("[dim]This connects to the inband-engine container and checks actual ifindex usage[/dim]\n")
        
        try:
            from .stag_pool_checker import run_stag_pool_check, calculate_max_services
            import base64
            
            # Build device list
            devices = []
            for dev in multi_ctx.devices:
                devices.append({
                    'hostname': dev.hostname,
                    'ip': dev.ip,
                    'username': dev.username,
                    'password': base64.b64decode(dev.password).decode() if dev.password else 'dnroot'
                })
            
            # Run live check with shell password "dnroot" [[memory:12623112]]
            all_status = run_stag_pool_check(devices, shell_password="dnroot")
            
            # Cache results in multi_ctx for use by Scale UP wizard
            if all_status:
                multi_ctx.cached_pool_status = {}
                for status in all_status:
                    if not status.error:
                        max_services, bottleneck = calculate_max_services(status)
                        multi_ctx.cached_pool_status[status.hostname] = {
                            'ph_pool_used': status.ph_pool.used,
                            'ph_pool_max': status.ph_pool.max_capacity,
                            'ph_pool_remaining': status.ph_pool.remaining,
                            'stag_pool_used': status.stag_pool.used,
                            'stag_pool_max': status.stag_pool.max_capacity,
                            'stag_pool_remaining': status.stag_pool.remaining,
                            'max_additional_pwhe_services': max_services,
                            'bottleneck': bottleneck,
                            'timestamp': datetime.now().isoformat()
                        }
                console.print(f"\n[green]✓ Pool status cached for Scale UP suggestions[/green]")
            
        except Exception as e:
            console.print(f"[red]Error running live check: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            console.print("\n[yellow]Alternative: Run manually:[/yellow]")
            console.print("[dim]  python3 /home/dn/SCALER/scaler/stag_pool_checker.py <device_ip>[/dim]")
    
    Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")


def _show_lldp_status_menu(device: 'Device', multi_ctx: 'MultiDeviceContext'):
    """
    Show LLDP status for a device with options to enable/configure LLDP.
    
    Features:
    - Display detailed LLDP neighbor table
    - Enable LLDP if not configured
    - Fix speed/FEC for 400G interfaces if LLDP not coming up
    """
    from rich.table import Table as RichTable
    from rich.panel import Panel
    import paramiko
    
    console.print("\n[bold cyan]━━━ LLDP Status ━━━[/bold cyan]")
    console.print(f"Device: [green]{device.hostname}[/green]")
    
    # Read cached LLDP data from operational.json
    op_file = Path(f"/home/dn/SCALER/db/configs/{device.hostname}/operational.json")
    op_data = {}
    lldp_neighbors = []
    
    try:
        if op_file.exists():
            with open(op_file) as f:
                op_data = json.load(f)
            lldp_neighbors = op_data.get('lldp_neighbors', [])
    except Exception:
        pass
    
    # Display LLDP neighbor table
    if lldp_neighbors:
        table = RichTable(title=f"LLDP Neighbors ({len(lldp_neighbors)})", box=box.ROUNDED)
        table.add_column("Local Interface", style="cyan")
        table.add_column("Neighbor Device", style="green")
        table.add_column("Neighbor Port", style="yellow")
        table.add_column("Capability", style="dim")
        table.add_column("DN Device", style="magenta")
        
        for n in lldp_neighbors:
            # Support both old format (interface/neighbor/remote_port) and new format (local_interface/neighbor_device/neighbor_port)
            local_if = n.get('local_interface') or n.get('interface', '?')
            neighbor = n.get('neighbor_device') or n.get('neighbor', '?')
            remote_port = n.get('neighbor_port') or n.get('remote_port', '?')
            capability = n.get('capability', '-')
            is_dn = "[green]Yes[/green]" if n.get('is_dn_device', False) else "[dim]No[/dim]"
            table.add_row(local_if, neighbor, remote_port, capability, is_dn)
        
        console.print(table)
        
        # Show unique neighbor count - support both formats
        unique_neighbors = len(set(
            n.get('neighbor_device') or n.get('neighbor', '') 
            for n in lldp_neighbors
        ))
        console.print(f"\n[dim]Total: {len(lldp_neighbors)} interfaces connected to {unique_neighbors} unique neighbors[/dim]")
    else:
        console.print("[yellow]No LLDP neighbors found in cache.[/yellow]")
        console.print("[dim]LLDP may not be configured or no neighbors are connected.[/dim]")
    
    # Show last update time
    last_updated = op_data.get('lldp_last_updated', 'Unknown')
    console.print(f"[dim]Last updated: {last_updated}[/dim]")
    
    # Show options
    console.print("\n[bold]Options:[/bold]")
    console.print("  [1] [cyan]Refresh LLDP[/cyan] - Fetch latest LLDP neighbors")
    console.print("  [2] [green]Enable LLDP[/green] - Configure LLDP on device")
    console.print("  [3] [yellow]Fix Speed/FEC[/yellow] - Set fec none + speed 100 for 400G interfaces")
    console.print("  [B] Back")
    
    choice = Prompt.ask("Select", choices=["1", "2", "3", "b", "B"], default="b").lower()
    
    if choice == "b":
        return
    elif choice == "1":
        # Refresh LLDP - fetch live from device
        _refresh_lldp_live(device)
    elif choice == "2":
        # Enable LLDP on device
        _enable_lldp_on_device_interactive(device)
    elif choice == "3":
        # Fix speed/FEC for 400G interfaces
        _fix_interface_speed_fec(device)


def _refresh_lldp_live(device: 'Device'):
    """Fetch LLDP neighbors live from device."""
    from .config_extractor import fetch_lldp_neighbors, update_lldp_in_operational_json
    
    console.print(f"\n[cyan]Connecting to {device.hostname}...[/cyan]")
    
    try:
        from .utils import safe_connect_and_verify
        conn = safe_connect_and_verify(device, timeout=2.0, verify_layers=True)
        
        if not conn['connected'] or not conn['verified']:
            reason = conn.get('abort_reason') or 'Connection failed'
            console.print(f"[bold red]⛔ {reason}[/bold red]")
            return
        
        ssh = conn['ssh']
        channel = conn['channel']
        console.print(f"[green]✓ Connected & verified: {conn['actual_hostname']} ({conn['ip']} via {conn['method']})[/green]")
        
        if conn.get('db_changes'):
            for key, change in conn['db_changes'].items():
                console.print(f"[dim]  DB sync: {key}: {change}[/dim]")
        
        console.print("[dim]Fetching LLDP neighbors...[/dim]")
        lldp_data = fetch_lldp_neighbors(channel, device.hostname)
        
        # Also get interface status to detect oper-up without LLDP
        channel.send("show interfaces | no-more\r\n")
        time.sleep(3)
        iface_output = ""
        while channel.recv_ready():
            iface_output += channel.recv(65535).decode('utf-8', errors='replace')
        
        channel.close()
        ssh.close()
        
        # Update operational.json
        update_lldp_in_operational_json(device.hostname, lldp_data)
        
        # Show results
        neighbors = lldp_data.get('lldp_neighbors', [])
        if neighbors:
            console.print(f"[green]✓ Found {len(neighbors)} LLDP neighbors[/green]")
            for n in neighbors[:5]:
                console.print(f"  {n.get('local_interface')} -> {n.get('neighbor_device')}:{n.get('neighbor_port')}")
            if len(neighbors) > 5:
                console.print(f"  ... and {len(neighbors) - 5} more")
        else:
            console.print("[yellow]No LLDP neighbors found.[/yellow]")
            
            # Check for oper-up interfaces without LLDP neighbors
            import re
            oper_up_ifaces = re.findall(r'(ge400-\d+/\d+/\d+).*?oper-status\s+up', iface_output, re.IGNORECASE | re.DOTALL)
            if oper_up_ifaces:
                console.print(f"\n[yellow]⚠ Found {len(oper_up_ifaces)} oper-up interfaces without LLDP neighbors:[/yellow]")
                for iface in oper_up_ifaces[:5]:
                    console.print(f"  [cyan]{iface}[/cyan]")
                console.print("\n[yellow]This may indicate:[/yellow]")
                console.print("  • LLDP not enabled on device")
                console.print("  • LLDP not enabled on neighbor")
                console.print("  • Speed/FEC mismatch (for 400G: try fec none + speed 100)")
                console.print("\n[dim]Use option [2] to enable LLDP or [3] to fix speed/FEC[/dim]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    
    Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")


def _enable_lldp_on_device_interactive(device: 'Device'):
    """Enable LLDP on device interactively."""
    from .config_extractor import check_lldp_configured, enable_lldp_on_device
    
    console.print(f"\n[cyan]Connecting to {device.hostname} to enable LLDP...[/cyan]")
    
    try:
        from .utils import safe_connect_and_verify
        conn = safe_connect_and_verify(device, timeout=2.0, verify_layers=True)
        
        if not conn['connected'] or not conn['verified']:
            reason = conn.get('abort_reason') or 'Connection failed'
            console.print(f"[bold red]⛔ {reason}[/bold red]")
            return
        
        ssh = conn['ssh']
        channel = conn['channel']
        connected = True
        console.print(f"[green]✓ Connected & verified: {conn['actual_hostname']} ({conn['ip']} via {conn['method']})[/green]")
        
        # Check if LLDP is already configured
        if check_lldp_configured(channel):
            console.print("[green]LLDP is already configured on this device.[/green]")
            console.print("[dim]Refreshing LLDP neighbors...[/dim]")
            # Just refresh
            channel.close()
            ssh.close()
            _refresh_lldp_live(device)
            return
        
        # Confirm enable
        if not Confirm.ask("[yellow]Enable LLDP on all physical interfaces?[/yellow]", default=True):
            channel.close()
            ssh.close()
            return
        
        def _lldp_progress(msg):
            console.print(f"  [dim]{msg}[/dim]")
        
        console.print("[bold]Enabling LLDP:[/bold]")
        if enable_lldp_on_device(channel, progress_callback=_lldp_progress):
            console.print("[green]✓ LLDP enabled successfully[/green]")
            console.print("[dim]Waiting for LLDP discovery (10 seconds)...[/dim]")
            time.sleep(10)
            
            # Refresh to see neighbors
            channel.close()
            ssh.close()
            _refresh_lldp_live(device)
        else:
            console.print("[red]✗ Failed to enable LLDP[/red]")
            console.print("[dim]Possible causes: no physical interfaces detected from 'show interfaces', or commit error. Try [1] Refresh LLDP first.[/dim]")
            channel.close()
            ssh.close()
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    
    Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")


def _fix_interface_speed_fec(device: 'Device'):
    """
    Fix speed and FEC settings for 400G interfaces.
    
    For ge400-* interfaces that are oper-up but have no LLDP neighbors,
    this might be due to speed/FEC mismatch with DNAAS fabric.
    Sets: fec none + speed 100
    """
    import paramiko
    import re
    
    console.print(f"\n[cyan]Connecting to {device.hostname}...[/cyan]")
    
    try:
        # Get connection info
        op_file = Path(f"/home/dn/SCALER/db/configs/{device.hostname}/operational.json")
        serial_number = None
        lldp_neighbors = []
        
        if op_file.exists():
            with open(op_file) as f:
                op_data = json.load(f)
                serial_number = op_data.get('serial_number')
                lldp_neighbors = op_data.get('lldp_neighbors', [])
        
        # Get interfaces that already have LLDP neighbors
        lldp_interfaces = set(n.get('local_interface', '') for n in lldp_neighbors)
        
        # Connect
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Use safe connection with IP resolution + verification
        from .utils import resolve_device_ip, verify_device_hostname
        resolved_ip, method = resolve_device_ip(device)
        target = resolved_ip if resolved_ip else device.ip
        ssh.connect(target, username='dnroot', password='dnroot', timeout=15, allow_agent=False, look_for_keys=False)
        
        channel = ssh.invoke_shell(width=200, height=50)
        channel.settimeout(30)
        time.sleep(1)
        _prompt = ""
        try:
            while channel.recv_ready():
                _prompt += channel.recv(65535).decode('utf-8', errors='replace')
        except:
            pass
        
        _hok, _ah = verify_device_hostname(_prompt, device.hostname)
        if not _hok:
            console.print(f"[bold red]⛔ WRONG DEVICE: '{_ah}' at {target} (expected '{device.hostname}'). Aborting.[/bold red]")
            ssh.close()
            return
        console.print(f"[green]✓ Connected & verified: {_ah}[/green]")
        
        # Get interface status
        channel.send("show interfaces | no-more\r\n")
        time.sleep(3)
        iface_output = ""
        while channel.recv_ready():
            iface_output += channel.recv(65535).decode('utf-8', errors='replace')
        
        # Find 400G interfaces that are oper-up or admin-enabled
        ge400_pattern = r'(ge400-\d+/\d+/\d+)'
        all_ge400 = list(set(re.findall(ge400_pattern, iface_output)))
        
        # Filter to only those without LLDP neighbors
        interfaces_to_fix = [iface for iface in all_ge400 if iface not in lldp_interfaces]
        
        if not interfaces_to_fix:
            console.print("[green]All 400G interfaces have LLDP neighbors - no fix needed.[/green]")
            channel.close()
            ssh.close()
            return
        
        console.print(f"\n[yellow]Found {len(interfaces_to_fix)} 400G interfaces without LLDP neighbors:[/yellow]")
        for iface in interfaces_to_fix[:10]:
            console.print(f"  [cyan]{iface}[/cyan]")
        if len(interfaces_to_fix) > 10:
            console.print(f"  ... and {len(interfaces_to_fix) - 10} more")
        
        console.print("\n[yellow]This will apply to each interface:[/yellow]")
        console.print("  [dim]fec none[/dim]")
        console.print("  [dim]speed 100[/dim]")
        console.print("  [dim]admin-state enabled[/dim]")
        
        if not Confirm.ask(f"\n[yellow]Apply speed/FEC fix to {len(interfaces_to_fix)} interfaces?[/yellow]", default=False):
            channel.close()
            ssh.close()
            return
        
        # Apply fix
        console.print("\n[dim]Entering configure mode...[/dim]")
        channel.send("configure\r\n")
        time.sleep(0.5)
        channel.send("interfaces\r\n")
        time.sleep(0.3)
        
        fixed_count = 0
        for iface in interfaces_to_fix:
            console.print(f"  Fixing [cyan]{iface}[/cyan]...", end=" ")
            channel.send(f"{iface}\r\n")
            time.sleep(0.1)
            channel.send("fec none\r\n")
            time.sleep(0.1)
            channel.send("speed 100\r\n")
            time.sleep(0.1)
            channel.send("admin-state enabled\r\n")
            time.sleep(0.1)
            channel.send("!\r\n")
            time.sleep(0.1)
            fixed_count += 1
            console.print("[green]✓[/green]")
        
        channel.send("!\r\n")  # Close interfaces
        time.sleep(0.3)
        
        console.print("\n[dim]Committing changes...[/dim]")
        channel.send("commit\r\n")
        time.sleep(5)
        
        # Drain output
        while channel.recv_ready():
            channel.recv(65535)
        
        console.print(f"[green]✓ Fixed {fixed_count} interfaces[/green]")
        console.print("[dim]Waiting for link to come up (10 seconds)...[/dim]")
        time.sleep(10)
        
        channel.close()
        ssh.close()
        
        # Refresh LLDP to see if neighbors appeared
        console.print("\n[dim]Checking for new LLDP neighbors...[/dim]")
        _refresh_lldp_live(device)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")


def _execute_factory_reset_multi(multi_ctx: 'MultiDeviceContext'):
    """Execute factory reset (load override factory-default) on all devices in parallel.
    
    This resets all devices to factory defaults, removing ALL configuration.
    Use with extreme caution!
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from rich.live import Live
    from rich.table import Table as RichTable
    from rich.panel import Panel
    from rich.prompt import Confirm
    import threading
    
    from .config_pusher import ConfigPusher
    
    console.print("\n[bold red]{'═' * 70}[/bold red]")
    console.print("[bold red]        🔄 FACTORY RESET - Load Override Factory Default             [/bold red]")
    console.print("[bold red]{'═' * 70}[/bold red]")
    
    # Show devices
    console.print(f"\n[bold]Target Devices ({len(multi_ctx.devices)}):[/bold]")
    for dev in multi_ctx.devices:
        console.print(f"  • [cyan]{dev.hostname}[/cyan] ({dev.ip})")
    
    console.print("\n[bold yellow]⚠ WARNING: This will RESET ALL DEVICES to factory defaults![/bold yellow]")
    console.print("[yellow]All configuration (interfaces, services, protocols) will be REMOVED.[/yellow]")
    console.print("[yellow]Only system minimum config will remain.[/yellow]")
    
    console.print("\n[bold]DNOS Commands to execute on each device:[/bold]")
    console.print("  [dim]configure[/dim]")
    console.print("  [yellow]load override factory-default[/yellow]")
    console.print("  [dim]commit check[/dim]")
    console.print("  [yellow]commit[/yellow]")
    
    # Require typing FACTORY to confirm
    console.print("\n[bold]Type 'FACTORY' to confirm factory reset on ALL devices, or anything else to cancel:[/bold]")
    confirm = Prompt.ask("Confirm")
    
    if confirm != "FACTORY":
        console.print("[dim]Factory reset cancelled.[/dim]")
        return
    
    # Second confirmation
    if not Confirm.ask(f"\n[bold red]Are you ABSOLUTELY SURE you want to factory reset {len(multi_ctx.devices)} devices?[/bold red]", default=False):
        console.print("[dim]Factory reset cancelled.[/dim]")
        return
    
    # Track progress per device
    device_progress = {dev.hostname: {"status": "pending", "message": ""} for dev in multi_ctx.devices}
    progress_lock = threading.Lock()
    
    def factory_reset_device(device):
        """Execute factory reset on a single device."""
        hostname = device.hostname
        
        with progress_lock:
            device_progress[hostname]["status"] = "running"
            device_progress[hostname]["message"] = "Connecting..."
        
        try:
            pusher = ConfigPusher()
            
            # Update progress
            with progress_lock:
                device_progress[hostname]["message"] = "Loading factory-default..."
            
            # Execute factory reset commands
            commands = ["load override factory-default"]
            
            success, message, output = pusher.run_cli_commands(
                device=device,
                commands=commands,
                dry_run=False,  # Actually commit!
                progress_callback=lambda msg, pct: None  # Silent
            )
            
            if success:
                with progress_lock:
                    device_progress[hostname]["status"] = "success"
                    device_progress[hostname]["message"] = "Factory reset complete!"
                return hostname, True, "Factory reset complete"
            else:
                with progress_lock:
                    device_progress[hostname]["status"] = "error"
                    device_progress[hostname]["message"] = message[:40]
                return hostname, False, message
                
        except Exception as e:
            with progress_lock:
                device_progress[hostname]["status"] = "error"
                device_progress[hostname]["message"] = str(e)[:40]
            return hostname, False, str(e)
    
    def render_progress():
        """Render progress table."""
        table = RichTable(box=box.ROUNDED, show_header=True, title="Factory Reset Progress")
        table.add_column("Device", style="cyan", width=20)
        table.add_column("Status", width=12)
        table.add_column("Details", width=35)
        
        for hostname, info in device_progress.items():
            status = info["status"]
            if status == "pending":
                status_str = "[dim]⏳ Waiting[/dim]"
            elif status == "running":
                status_str = "[yellow]⏳ Running[/yellow]"
            elif status == "success":
                status_str = "[green]✓ Done[/green]"
            else:
                status_str = "[red]✗ Error[/red]"
            
            table.add_row(hostname, status_str, info["message"])
        
        return table
    
    console.print("\n[bold cyan]🔄 Executing Factory Reset...[/bold cyan]\n")
    
    # Execute in parallel with live display
    with Live(render_progress(), refresh_per_second=4, console=console) as live:
        with ThreadPoolExecutor(max_workers=len(multi_ctx.devices)) as executor:
            futures = {executor.submit(factory_reset_device, dev): dev for dev in multi_ctx.devices}
            
            while any(f.running() for f in futures):
                live.update(render_progress())
                import time
                time.sleep(0.25)
            
            # Final update
            live.update(render_progress())
    
    # Summary
    success_count = sum(1 for info in device_progress.values() if info["status"] == "success")
    error_count = len(device_progress) - success_count
    
    console.print(f"\n[bold]Results:[/bold]")
    if success_count > 0:
        console.print(f"  [green]✓ {success_count} devices factory reset successfully[/green]")
    if error_count > 0:
        console.print(f"  [red]✗ {error_count} devices failed[/red]")
        for hostname, info in device_progress.items():
            if info["status"] != "success":
                console.print(f"    • {hostname}: {info['message']}")
    
    if success_count > 0:
        console.print("\n[bold yellow]⚠ Devices are now at factory defaults.[/bold yellow]")
        console.print("[dim]You may need to reconfigure system settings, interfaces, and protocols.[/dim]")


def _execute_factory_reset_single(device: 'Device'):
    """Execute factory reset (load override factory-default) on a single device.
    
    This resets the device to factory defaults, removing ALL configuration.
    Use with extreme caution!
    """
    from rich.panel import Panel
    from rich.prompt import Confirm
    from rich.live import Live
    from rich.text import Text
    import threading
    import time
    
    from .config_pusher import ConfigPusher
    
    console.print("\n[bold red]{'═' * 70}[/bold red]")
    console.print("[bold red]        🔄 FACTORY RESET - Load Override Factory Default             [/bold red]")
    console.print("[bold red]{'═' * 70}[/bold red]")
    
    # Show target device
    console.print(f"\n[bold]Target Device:[/bold]")
    console.print(f"  • [cyan]{device.hostname}[/cyan] ({device.ip})")
    
    console.print("\n[bold yellow]⚠ WARNING: This will RESET the device to factory defaults![/bold yellow]")
    console.print("[yellow]All configuration (interfaces, services, protocols) will be REMOVED.[/yellow]")
    console.print("[yellow]Only system minimum config will remain.[/yellow]")
    
    console.print("\n[bold]DNOS Commands to execute:[/bold]")
    console.print("  [dim]configure[/dim]")
    console.print("  [yellow]load override factory-default[/yellow]")
    console.print("  [dim]commit check[/dim]")
    console.print("  [yellow]commit[/yellow]")
    
    # Require typing FACTORY to confirm
    console.print("\n[bold]Type 'FACTORY' to confirm, or [B]ack to cancel:[/bold]")
    confirm = Prompt.ask("Confirm", default="b")
    
    if confirm.lower() == 'b' or confirm != "FACTORY":
        console.print("[dim]Factory reset cancelled.[/dim]")
        return
    
    # Second confirmation
    if not Confirm.ask(f"\n[bold red]Are you ABSOLUTELY SURE you want to factory reset {device.hostname}?[/bold red]", default=False):
        console.print("[dim]Factory reset cancelled.[/dim]")
        return
    
    # Track progress
    progress_info = {"stage": "Connecting...", "terminal_lines": [], "progress": 0}
    progress_lock = threading.Lock()
    
    def add_terminal_line(line: str):
        with progress_lock:
            progress_info["terminal_lines"].append(line)
            if len(progress_info["terminal_lines"]) > 12:
                progress_info["terminal_lines"] = progress_info["terminal_lines"][-12:]
    
    def render_progress():
        """Render progress panel."""
        content = Text()
        
        # Stage
        stage = progress_info.get("stage", "Initializing...")
        content.append(f"Stage: {stage}\n\n", style="bold cyan")
        
        # Progress bar
        pct = progress_info.get("progress", 0)
        bar_width = 40
        filled = int(bar_width * pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        content.append(f"Progress: [{bar}] {pct}%\n\n", style="yellow")
        
        # Terminal output
        content.append("Terminal Output:\n", style="bold")
        for line in progress_info.get("terminal_lines", [])[-10:]:
            if "error" in line.lower() or "fail" in line.lower():
                content.append(f"  {line}\n", style="red")
            elif "success" in line.lower() or "complete" in line.lower():
                content.append(f"  {line}\n", style="green")
            else:
                content.append(f"  {line}\n", style="dim")
        
        return Panel(content, title=f"🔄 Factory Reset: {device.hostname}", border_style="red", height=20)
    
    console.print("\n[bold cyan]🔄 Executing Factory Reset...[/bold cyan]\n")
    
    def do_factory_reset():
        """Execute factory reset commands."""
        hostname = device.hostname
        
        try:
            pusher = ConfigPusher()
            
            with progress_lock:
                progress_info["stage"] = "Connecting to device..."
                progress_info["progress"] = 10
            # Get best available IP from operational.json
            from .utils import get_ssh_hostname
            ssh_host = get_ssh_hostname(device)
            add_terminal_line(f"Connecting to {ssh_host}...")
            
            # Open SSH connection
            import paramiko
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=ssh_host,
                username=device.username,
                password=device.password,
                look_for_keys=False,
                allow_agent=False,
                timeout=30
            )
            
            channel = client.invoke_shell(width=200, height=50)
            channel.settimeout(60)
            
            add_terminal_line("✓ Connected")
            time.sleep(1)
            
            def send_cmd(cmd, wait=3):
                """Send command and get response."""
                channel.send(cmd + "\n")
                time.sleep(wait)
                output = ""
                while channel.recv_ready():
                    output += channel.recv(65536).decode('utf-8', errors='replace')
                return output
            
            # Drain initial output
            send_cmd("", 2)
            
            # Enter configure mode
            with progress_lock:
                progress_info["stage"] = "Entering configure mode..."
                progress_info["progress"] = 20
            add_terminal_line("> configure")
            output = send_cmd("configure", 2)
            
            # Load override factory-default
            with progress_lock:
                progress_info["stage"] = "Loading factory-default..."
                progress_info["progress"] = 40
            add_terminal_line("> load override factory-default")
            output = send_cmd("load override factory-default", 5)
            
            if "error" in output.lower():
                add_terminal_line(f"[ERROR] {output[:60]}")
                return False, f"Load failed: {output[:100]}"
            
            add_terminal_line("✓ Factory-default loaded")
            
            # Commit check
            with progress_lock:
                progress_info["stage"] = "Running commit check..."
                progress_info["progress"] = 60
            add_terminal_line("> commit check")
            output = send_cmd("commit check", 10)
            
            if "error" in output.lower() or "failed" in output.lower():
                add_terminal_line(f"[ERROR] Commit check failed")
                return False, f"Commit check failed: {output[:100]}"
            
            add_terminal_line("✓ Commit check passed")
            
            # Commit
            with progress_lock:
                progress_info["stage"] = "Committing..."
                progress_info["progress"] = 80
            add_terminal_line("> commit")
            output = send_cmd("commit", 30)
            
            if "error" in output.lower() and "commit" in output.lower():
                add_terminal_line(f"[ERROR] Commit failed")
                return False, f"Commit failed: {output[:100]}"
            
            add_terminal_line("✓ Commit complete")
            
            # Exit and cleanup
            send_cmd("end", 1)
            client.close()
            
            with progress_lock:
                progress_info["stage"] = "Factory reset complete!"
                progress_info["progress"] = 100
            add_terminal_line("✓ Factory reset successful!")
            
            return True, "Factory reset complete"
            
        except Exception as e:
            add_terminal_line(f"[ERROR] {str(e)[:50]}")
            return False, str(e)
    
    # Execute with live display
    result = [None]
    
    def run_reset():
        result[0] = do_factory_reset()
    
    reset_thread = threading.Thread(target=run_reset)
    
    with Live(render_progress(), refresh_per_second=4, console=console) as live:
        reset_thread.start()
        
        while reset_thread.is_alive():
            live.update(render_progress())
            time.sleep(0.25)
        
        reset_thread.join()
        live.update(render_progress())
    
    success, message = result[0] if result[0] else (False, "Unknown error")
    
    # Show result
    if success:
        console.print(f"\n[bold green]✓ Factory reset complete for {device.hostname}![/bold green]")
        console.print("\n[bold yellow]⚠ Device is now at factory defaults.[/bold yellow]")
        console.print("[dim]You may need to reconfigure system settings, interfaces, and protocols.[/dim]")
    else:
        console.print(f"\n[bold red]✗ Factory reset failed: {message}[/bold red]")
    
    Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")


def _run_system_restore_multi(multi_ctx: 'MultiDeviceContext'):
    """Run System Restore wizard for devices in RECOVERY mode.
    
    This function:
    1. Detects which devices are in RECOVERY mode
    2. Shows previous device knowledge (system_type, hostname)
    3. Guides user through restore process for each device
    """
    from .wizard.system_restore import (
        DeviceKnowledge, 
        run_system_restore_wizard,
        check_recovery_and_prompt,
        show_device_knowledge_panel
    )
    from rich.panel import Panel
    
    console.print("\n")
    console.print(Panel(
        "[bold red]🔧 SYSTEM RESTORE - Recovery Mode Devices[/bold red]\n\n"
        "This wizard helps restore devices that are in RECOVERY mode.\n"
        "It uses previous device knowledge to configure deployment correctly.",
        border_style="red"
    ))
    
    # Check each device for recovery mode
    recovery_devices = []
    normal_devices = []
    
    console.print("\n[bold]Checking device status...[/bold]")
    
    for device in multi_ctx.devices:
        knowledge = DeviceKnowledge.from_operational_json(device.hostname)
        
        # Check if previously detected as recovery
        if knowledge.recovery_mode_detected or knowledge.console_recovery_detected:
            recovery_devices.append((device, knowledge))
            console.print(f"  [red]⚠ {device.hostname}[/red] - RECOVERY mode detected (from previous scan)")
            continue
        
        # Try live check via SSH
        result = check_recovery_and_prompt(device)
        if result is True:
            knowledge.recovery_mode_detected = True
            recovery_devices.append((device, knowledge))
            console.print(f"  [red]⚠ {device.hostname}[/red] - RECOVERY mode (live check)")
        elif result is False:
            # User declined restore for this device
            console.print(f"  [yellow]○ {device.hostname}[/yellow] - Recovery detected but user declined restore")
        else:
            # Not in recovery
            normal_devices.append(device)
            console.print(f"  [green]✓ {device.hostname}[/green] - Normal operation")
    
    if not recovery_devices:
        console.print("\n[green]No devices in RECOVERY mode found.[/green]")
        console.print("[dim]Use the Image Upgrade option to upgrade DNOS on working devices.[/dim]")
        Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")
        return
    
    # Show summary of devices to restore
    console.print(f"\n[bold red]Found {len(recovery_devices)} device(s) in RECOVERY mode:[/bold red]")
    for device, knowledge in recovery_devices:
        system_type = knowledge.system_type or "[unknown]"
        prev_version = knowledge.previous_dnos_version or "N/A"
        console.print(f"  • [cyan]{device.hostname}[/cyan] ({device.ip})")
        console.print(f"    [dim]System Type: {system_type} | Previous DNOS: {prev_version}[/dim]")
    
    if normal_devices:
        console.print(f"\n[green]{len(normal_devices)} device(s) operating normally (skipped):[/green]")
        for device in normal_devices:
            console.print(f"  • [green]{device.hostname}[/green]")
    
    # Ask to proceed
    console.print("\n[bold]Options:[/bold]")
    console.print("  [1] Restore all recovery devices")
    console.print("  [2] Select specific device to restore")
    console.print("  [B] Back - Cancel restore")
    
    choice = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="1").lower()
    
    if choice == 'b':
        return
    
    devices_to_restore = []
    
    if choice == '1':
        devices_to_restore = [dev for dev, _ in recovery_devices]
    else:
        # Select specific device
        console.print("\n[bold]Select device to restore:[/bold]")
        for i, (device, knowledge) in enumerate(recovery_devices, 1):
            console.print(f"  [{i}] {device.hostname}")
        console.print("  [B] Back")
        
        device_choice = Prompt.ask("Select", choices=[str(i) for i in range(1, len(recovery_devices)+1)] + ['b', 'B'], default="1").lower()
        if device_choice == 'b':
            return
        
        idx = int(device_choice) - 1
        devices_to_restore = [recovery_devices[idx][0]]
    
    # Run restore wizard for each selected device
    results = {}
    for device in devices_to_restore:
        console.print(f"\n[bold cyan]{'═' * 70}[/bold cyan]")
        console.print(f"[bold cyan]  Restoring: {device.hostname}[/bold cyan]")
        console.print(f"[bold cyan]{'═' * 70}[/bold cyan]")
        
        try:
            success = run_system_restore_wizard(device, multi_ctx)
            results[device.hostname] = success
        except KeyboardInterrupt:
            console.print(f"\n[yellow]Restore cancelled for {device.hostname}[/yellow]")
            results[device.hostname] = False
            break
        except Exception as e:
            console.print(f"\n[red]Error restoring {device.hostname}: {e}[/red]")
            results[device.hostname] = False
    
    # Show summary
    console.print(f"\n[bold]{'═' * 70}[/bold]")
    console.print("[bold]System Restore Summary:[/bold]")
    
    success_count = sum(1 for v in results.values() if v)
    fail_count = len(results) - success_count
    
    if success_count > 0:
        console.print(f"  [green]✓ {success_count} device(s) restored successfully[/green]")
    if fail_count > 0:
        console.print(f"  [red]✗ {fail_count} device(s) failed[/red]")
        for hostname, success in results.items():
            if not success:
                console.print(f"    • {hostname}")
    
    if success_count > 0:
        console.print("\n[dim]Run 'Refresh' to update device configurations.[/dim]")
    
    Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")


def _refresh_multi_device_configs(multi_ctx: 'MultiDeviceContext'):
    """Refresh running configurations from all devices in parallel."""
    from .config_extractor import ConfigExtractor
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from rich.live import Live
    from rich.table import Table as RichTable
    import threading
    
    console.print("\n[bold cyan]🔄 Refreshing Configurations from All Devices[/bold cyan]")
    
    # Track progress per device
    device_progress = {dev.hostname: {"status": "pending", "message": ""} for dev in multi_ctx.devices}
    results = {}
    progress_lock = threading.Lock()
    
    def fetch_config(device):
        """Fetch config from a single device."""
        hostname = device.hostname
        
        with progress_lock:
            device_progress[hostname]["status"] = "running"
            device_progress[hostname]["message"] = "Connecting..."
        
        try:
            extractor = ConfigExtractor()
            result = extractor.extract_running_config(device, save_to_db=True)
            
            if result and result.raw_config:
                config = result.raw_config
                
                # Update multi_ctx
                multi_ctx.configs[hostname] = config
                multi_ctx._parse_device_info(hostname, config)
                
                with progress_lock:
                    device_progress[hostname]["status"] = "success"
                    device_progress[hostname]["message"] = f"{len(config.splitlines()):,} lines"
                
                return hostname, True, f"{len(config.splitlines()):,} lines saved"
            else:
                with progress_lock:
                    device_progress[hostname]["status"] = "error"
                    device_progress[hostname]["message"] = "No config received"
                return hostname, False, "No config received"
                
        except Exception as e:
            err_msg = str(e)
            detail = err_msg[:50]
            console_recovery = None
            console_error = None
            if hostname == "PE-2":
                try:
                    from .pe2_console import check_pe2_recovery_via_console
                    in_rec, rec_type, con_err = check_pe2_recovery_via_console()
                    console_recovery = in_rec
                    console_error = con_err
                    if in_rec:
                        # Show the recovery type (GI, BASEOS_SHELL, ONIE, etc.)
                        detail = f"SSH failed. Console: PE-2 in {rec_type or 'recovery'}"
                    elif con_err:
                        detail = ("SSH failed. Console: " + con_err)[:55]
                    else:
                        detail = "SSH failed. Console: reachable, not recovery"
                except Exception as cx:
                    console_error = str(cx)
                    detail = ("SSH failed. Console: " + str(cx))[:55]
            with progress_lock:
                device_progress[hostname]["status"] = "error"
                device_progress[hostname]["message"] = detail
                if hostname == "PE-2":
                    device_progress[hostname]["console_recovery"] = console_recovery
                    device_progress[hostname]["console_error"] = console_error
            return hostname, False, err_msg
    
    def render_progress():
        """Render progress table."""
        table = RichTable(box=box.ROUNDED, show_header=True)
        table.add_column("Device", style="cyan", width=15)
        table.add_column("Status", width=12)
        table.add_column("Details", width=55)
        
        for hostname, info in device_progress.items():
            status = info["status"]
            message = info["message"]
            
            if status == "pending":
                status_display = "[dim]⏳ Pending[/dim]"
            elif status == "running":
                status_display = "[yellow]⟳ Fetching[/yellow]"
            elif status == "success":
                status_display = "[green]✓ Done[/green]"
            else:
                status_display = "[red]✗ Error[/red]"
            
            table.add_row(hostname, status_display, message)
        
        return table
    
    # Execute in parallel with live progress
    with Live(render_progress(), refresh_per_second=4, console=console, transient=False) as live:
        with ThreadPoolExecutor(max_workers=len(multi_ctx.devices)) as executor:
            futures = {executor.submit(fetch_config, dev): dev for dev in multi_ctx.devices}
            
            while any(f.running() for f in futures):
                live.update(render_progress())
                time.sleep(0.25)
            
            for future in as_completed(futures):
                hostname, success, message = future.result()
                results[hostname] = (success, message)
            
            live.update(render_progress())
    
    # Summary
    success_count = sum(1 for s, _ in results.values() if s)
    console.print(f"\n[bold]Completed: {success_count}/{len(multi_ctx.devices)} devices refreshed[/bold]")
    # If PE-2 failed, show console fallback result and persist recovery state for wizard
    pe2_info = device_progress.get("PE-2", {})
    if pe2_info.get("status") == "error":
        cr = pe2_info.get("console_recovery")
        ce = pe2_info.get("console_error")
        if cr is True:
            console.print("[yellow]PE-2: SSH failed. Console check: PE-2 is in recovery mode.[/yellow]")
        elif ce:
            console.print(f"[dim]PE-2: SSH failed. Console: {ce}[/dim]")
        elif cr is False:
            console.print("[dim]PE-2: SSH failed. Console reachable, device not in recovery.[/dim]")
        # Persist console recovery state so wizard (upgrade status, push flow) knows PE-2 is in recovery
        if cr is not None:
            try:
                from .utils import get_device_config_dir
                ops_file = get_device_config_dir("PE-2") / "operational.json"
                op_data = {}
                if ops_file.exists():
                    with open(ops_file) as f:
                        op_data = json.load(f)
                op_data["console_recovery_detected"] = bool(cr)
                op_data["console_recovery_detected_at"] = datetime.now().isoformat()
                with open(ops_file, "w") as f:
                    json.dump(op_data, f, indent=2)
            except Exception:
                pass
    Prompt.ask("[dim]Press Enter to continue[/dim]", default="")


def _show_multi_device_sync_status(multi_ctx: 'MultiDeviceContext'):
    """Show detailed synchronization status between devices."""
    from rich.columns import Columns
    from rich.panel import Panel
    
    console.print("\n[bold cyan]🔍 Detailed Multi-Device Sync Status[/bold cyan]")
    
    panels = []
    
    for dev in multi_ctx.devices:
        h = dev.hostname
        lo = multi_ctx.loopbacks.get(h, "N/A")
        asn = multi_ctx.bgp_asn.get(h, "N/A")
        rt_count = len(multi_ctx.route_targets.get(h, set()))
        iface_count = len(multi_ctx.interfaces.get(h, []))
        mh_count = len(multi_ctx.mh_config.get(h, {}))
        
        # Get PWHE interfaces
        pwhe_ifaces = [i for i in multi_ctx.interfaces.get(h, []) if re.match(r'^ph\d+', i)]
        l2_ifaces = [i for i in multi_ctx.interfaces.get(h, []) if re.match(r'^[gx]e[\d\-/]+\.\d+', i)]
        
        # Check config file age
        from .utils import get_device_config_dir
        running_path = get_device_config_dir(h) / "running.txt"
        if running_path.exists():
            import os
            mtime = os.path.getmtime(running_path)
            age_mins = int((time.time() - mtime) / 60)
            if age_mins < 60:
                age_str = f"{age_mins}m ago"
            elif age_mins < 1440:
                age_str = f"{age_mins // 60}h ago"
            else:
                age_str = f"{age_mins // 1440}d ago"
        else:
            age_str = "[red]Not cached[/red]"
        
        content = [
            f"[cyan]Loopback:[/cyan] {lo}",
            f"[cyan]BGP ASN:[/cyan] {asn}",
            f"[cyan]Config Age:[/cyan] {age_str}",
            "",
            f"[bold]Scale:[/bold]",
            f"  Route Targets: {rt_count}",
            f"  PWHE Interfaces: {len(pwhe_ifaces)}",
            f"  L2 Interfaces: {len(l2_ifaces)}",
            "",
            f"[bold]Multihoming:[/bold]",
        ]
        
        if mh_count > 0:
            content.append(f"  [green]✓ {mh_count} interfaces configured[/green]")
            # Sample ESI
            mh_cfg = multi_ctx.mh_config.get(h, {})
            sample = list(mh_cfg.items())[:2]
            for iface, cfg in sample:
                # cfg can be a string (ESI value) or dict with 'esi' key
                esi = cfg if isinstance(cfg, str) else cfg.get('esi', 'N/A')
                content.append(f"    {iface}: {esi[:25]}...")
        else:
            content.append(f"  [yellow]⚠ Not configured[/yellow]")
        
        border_color = "green" if mh_count > 0 else "yellow"
        panel = Panel(
            "\n".join(content),
            title=f"[bold]{h}[/bold]",
            border_style=border_color,
            expand=True
        )
        panels.append(panel)
    
    console.print(Columns(panels, expand=True))
    
    # Show sync summary for all device pairs
    if len(multi_ctx.devices) >= 2:
        console.print(f"\n[bold]Sync Summary (All Device Pairs):[/bold]")
        
        # Compare each pair of devices
        from itertools import combinations
        for dev1, dev2 in combinations(multi_ctx.devices, 2):
            h1, h2 = dev1.hostname, dev2.hostname
            rt1 = multi_ctx.route_targets.get(h1, set())
            rt2 = multi_ctx.route_targets.get(h2, set())
            shared_rt = len(rt1 & rt2)
            
            mh1 = set(multi_ctx.mh_config.get(h1, {}).keys())
            mh2 = set(multi_ctx.mh_config.get(h2, {}).keys())
            shared_mh = len(mh1 & mh2)
            
            # Calculate sync status
            mh_status = ""
            if mh1 and mh2:
                sync_pct = (shared_mh / max(len(mh1), len(mh2))) * 100
                if sync_pct == 100:
                    mh_status = "[green]✓ MH synced[/green]"
                elif sync_pct > 0:
                    mh_status = f"[yellow]⚠ MH {sync_pct:.0f}%[/yellow]"
                else:
                    mh_status = "[red]✗ MH not synced[/red]"
            elif mh1 or mh2:
                mh_status = "[yellow]⚠ MH mismatch[/yellow]"
            else:
                mh_status = "[dim]No MH[/dim]"
            
            console.print(f"  {h1} ↔ {h2}: {shared_rt} shared RTs • {mh_status}")
    
    Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")


def _push_config_to_all_devices(multi_ctx: 'MultiDeviceContext', history: list):
    """Push a configuration file to all devices in multi-device mode."""
    from .config_pusher import ConfigPusher
    
    console.print("\n[bold cyan]📤 Push Configuration to All Devices[/bold cyan]")
    device_names = ", ".join([d.hostname for d in multi_ctx.devices])
    console.print(f"[dim]Target devices: {device_names}[/dim]")
    
    # Option to select config source
    console.print("\n[bold]Select Configuration Source:[/bold]")
    console.print("  [1] Select from recent configs")
    console.print("  [2] Enter file path manually")
    console.print("  [B] Back")
    
    source_choice = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="1").lower()
    
    if source_choice == "b":
        return
    
    config_text = None
    config_name = None
    
    if source_choice == "1":
        # Show all recent configs from all devices
        all_history = []
        for dev in multi_ctx.devices:
            dev_history = _load_config_history(dev.hostname, limit=3)
            for entry in dev_history:
                entry['device'] = dev.hostname
                all_history.append(entry)
        
        if not all_history:
            console.print("[yellow]No recent configurations found.[/yellow]")
            return
        
        # Sort by timestamp
        all_history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        table = Table(title="Available Configurations", box=box.ROUNDED)
        table.add_column("#", style="dim", width=3)
        table.add_column("Device", width=10)
        table.add_column("Filename", min_width=20)
        table.add_column("Lines", justify="right", width=8)
        
        for i, entry in enumerate(all_history[:6], 1):
            table.add_row(
                str(i),
                entry.get('device', '?'),
                entry['filename'][:25],
                f"{entry.get('line_count', '?'):,}"
            )
        
        console.print(table)
        
        choice = Prompt.ask("Select config number", default="1")
        if choice.isdigit() and 1 <= int(choice) <= len(all_history[:6]):
            entry = all_history[int(choice) - 1]
            filepath = Path(entry['filepath'])
            if filepath.exists():
                with open(filepath, 'r') as f:
                    config_text = f.read()
                config_name = entry['filename']
            else:
                console.print("[red]Config file not found.[/red]")
                return
        else:
            return
    
    elif source_choice == "2":
        filepath = Prompt.ask("Enter config file path")
        if Path(filepath).exists():
            with open(filepath, 'r') as f:
                config_text = f.read()
            config_name = Path(filepath).name
        else:
            console.print("[red]File not found.[/red]")
            return
    
    if not config_text:
        console.print("[red]No configuration loaded.[/red]")
        return
    
    console.print(f"\n[green]✓ Loaded: {config_name} ({len(config_text.splitlines()):,} lines)[/green]")
    
    # =========================================================================
    # CONFIG CONTENT ANALYSIS & LIMIT VALIDATION
    # =========================================================================
    console.print("\n[bold]Configuration Content Analysis:[/bold]")
    
    # Count various elements in the config being pushed
    config_pwhe = len(re.findall(r'^\s*ph\d+', config_text, re.MULTILINE))
    config_fxc = len(re.findall(r'fxc\s+\S+', config_text))
    config_mh = len(re.findall(r'interface\s+ph\d+\.\d+\s*\n\s*esi\s', config_text, re.MULTILINE))
    
    if config_pwhe or config_fxc or config_mh:
        console.print(f"  Detected in config:")
        if config_pwhe:
            console.print(f"    [cyan]PWHE interfaces:[/cyan] ~{config_pwhe}")
        if config_fxc:
            console.print(f"    [cyan]FXC services:[/cyan] ~{config_fxc}")
        if config_mh:
            console.print(f"    [cyan]MH ESI configs:[/cyan] ~{config_mh}")
        
        # Check against current + new
        any_exceeded = False
        for dev in multi_ctx.devices:
            h = dev.hostname
            current_mh = len(multi_ctx.mh_config.get(h, {}))
            total_mh = current_mh + config_mh
            
            mh_limit = get_limit("multihoming", "max_esi_interfaces", 2000)
            if total_mh > mh_limit:
                console.print(f"  [red]⚠ {h}: MH would be {total_mh} (exceeds {mh_limit})[/red]")
                any_exceeded = True
        
        if any_exceeded:
            console.print("\n[bold yellow]⚠ Config may exceed DNOS limits on some devices[/bold yellow]")
            if not Confirm.ask("Continue anyway?", default=True):
                return
    
    # Confirm push
    console.print(f"\n[bold yellow]⚠ This will push the same config to ALL {len(multi_ctx.devices)} devices![/bold yellow]")
    console.print("\n[bold]Push Options:[/bold]")
    console.print("  [1] Commit check only (dry run)")
    console.print("  [2] Push and commit to ALL devices")
    console.print("  [B] Cancel")
    
    push_choice = Prompt.ask("Select", choices=["1", "2", "b", "B"], default="1").lower()
    
    if push_choice == "b":
        console.print("[yellow]Cancelled.[/yellow]")
        return
    
    dry_run = (push_choice == "1")
    
    # Push to devices in PARALLEL with progress tracking
    from rich.live import Live
    from rich.table import Table as RichTable
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    
    # Calculate ETA using accurate estimation system
    from .config_pusher import get_accurate_push_estimates
    
    estimates = get_accurate_push_estimates(
        config_text=config_text,
        platform=multi_ctx.devices[0].platform.value if multi_ctx.devices else "SA-36CD-S"
    )
    
    # Get file upload estimate (default push method)
    estimated_seconds = estimates['estimates']['file_upload']['total']
    source = estimates['source']
    source_detail = estimates['source_detail']
    
    def format_time_est(seconds: float) -> str:
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"
    
    console.print(f"\n[bold cyan]⏱ Estimated time: ~{format_time_est(estimated_seconds)} per device[/bold cyan]")
    console.print(f"[dim]Pushing {len(config_text.splitlines()):,} lines to {len(multi_ctx.devices)} devices[/dim]")
    
    # Show estimate source
    if source == 'similar_push':
        console.print(f"[green]📊 {source_detail}[/green]")
    elif source == 'scale_type':
        console.print(f"[yellow]📊 {source_detail}[/yellow]")
    else:
        console.print(f"[dim]📊 {source_detail}[/dim]")
    console.print()
    
    device_progress = {dev.hostname: {"status": "pending", "progress": 0, "message": ""} 
                      for dev in multi_ctx.devices}
    results = {}
    lock = threading.Lock()
    config_lines_count = len(config_text.splitlines())
    
    def push_device(dev):
        hostname = dev.hostname
        def progress_callback(msg, pct):
            with lock:
                device_progress[hostname]["status"] = "pushing"
                device_progress[hostname]["progress"] = pct
                device_progress[hostname]["message"] = msg[:40]
        
        try:
            with lock:
                device_progress[hostname]["status"] = "connecting"
                device_progress[hostname]["message"] = "Connecting..."
            
            pusher = ConfigPusher()
            success, message = pusher.push_config_terminal_paste(
                dev, config_text, dry_run=dry_run,
                progress_callback=progress_callback
            )
            
            with lock:
                if success:
                    device_progress[hostname]["status"] = "success"
                    device_progress[hostname]["progress"] = 100
                    device_progress[hostname]["message"] = "Complete!"
                else:
                    device_progress[hostname]["status"] = "failed"
                    device_progress[hostname]["message"] = message[:40] if message else "Failed"
            
            return hostname, success, message
        except Exception as e:
            with lock:
                device_progress[hostname]["status"] = "error"
                device_progress[hostname]["message"] = str(e)[:40]
            return hostname, False, str(e)
    
    def render_progress():
        table = RichTable(box=box.ROUNDED, title="Multi-Device Push Progress", expand=True)
        table.add_column("Device", style="cyan", width=12)
        table.add_column("Status", width=12)
        table.add_column("Progress", width=30)
        table.add_column("Message", width=35)
        
        for dev in multi_ctx.devices:
            h = dev.hostname
            info = device_progress[h]
            status = info["status"]
            
            if status == "pending":
                status_str = "[dim]⏳ Pending[/dim]"
            elif status == "connecting":
                status_str = "[yellow]🔌 Connecting[/yellow]"
            elif status == "pushing":
                status_str = "[cyan]📤 Pushing[/cyan]"
            elif status == "success":
                status_str = "[green]✓ Success[/green]"
            else:
                status_str = f"[red]✗ {status}[/red]"
            
            pct = info["progress"]
            filled = int(pct / 5)
            bar = "━" * filled + "╺" + "─" * (19 - filled)
            color = "green" if status == "success" else "red" if status in ("failed", "error") else "cyan"
            bar_str = f"[{color}]{bar}[/{color}] {pct}%"
            
            table.add_row(h, status_str, bar_str, info["message"])
        return table
    
    start_time = time.time()
    
    # Use transient=False to prevent screen jumping
    with Live(render_progress(), refresh_per_second=4, console=console, transient=False, vertical_overflow="visible") as live:
        with ThreadPoolExecutor(max_workers=len(multi_ctx.devices)) as executor:
            futures = {executor.submit(push_device, dev): dev for dev in multi_ctx.devices}
            
            while any(f.running() for f in futures):
                live.update(render_progress())
                time.sleep(0.25)
            
            for future in as_completed(futures):
                hostname, success, message = future.result()
                results[hostname] = (success, message)
            
            live.update(render_progress())
    
    elapsed = time.time() - start_time
    success_count = sum(1 for s, _ in results.values() if s)
    
    console.print()
    console.print(f"[bold]Completed: {success_count}/{len(multi_ctx.devices)} devices {'validated' if dry_run else 'configured'}[/bold]")
    console.print(f"[dim]Total time: {elapsed:.1f}s[/dim]")
    Prompt.ask("[dim]Press Enter to continue[/dim]", default="")


def _edit_config_by_sections(
    config_text: str, 
    filepath: Path,
    device: 'Device' = None,
    multi_ctx: 'MultiDeviceContext' = None
) -> Optional[str]:
    """
    Parse configuration into sections and provide FULL WIZARD experience to edit each.
    
    Uses the same wizard functions as the normal configuration flow:
    - System → configure_system() with profile, hostname, logging options
    - Interfaces → configure_interfaces() with PWHE/L2-AC/Bundle options  
    - Services → configure_services() with FXC/EVPN/VPWS wizards
    - Protocols → configure_bgp(), configure_igp() with full options
    
    Actions:
    - [S] Skip - Keep section unchanged
    - [E] Edit - Use FULL WIZARD to edit this section
    - [V] View - View full section content
    - [D] Delete - Remove this section
    - [R] Raw - Open in external editor (advanced)
    - [B] Back - Go to previous section
    - [T] Top - Exit to Quick Load menu
    
    Args:
        config_text: Full configuration text
        filepath: Path to the config file (for saving)
        device: Device object for wizard context
        multi_ctx: MultiDeviceContext for wizard context
        
    Returns:
        Modified config text if changes made, None if cancelled
    """
    import tempfile
    import subprocess
    from rich.panel import Panel
    from rich.text import Text
    
    # Section display names and icons
    SECTION_INFO = {
        'system': ('⚙️', 'System', 'System profile, hostname, logging, users'),
        'interfaces': ('🔌', 'Interfaces', 'Physical and logical interfaces'),
        'network-services': ('🔗', 'Network Services', 'FXC, EVPN-VPWS, VPLS, VRF'),
        'protocols': ('📡', 'Protocols', 'BGP, OSPF, ISIS, LLDP, BFD, LACP'),
        'routing-policy': ('📋', 'Routing Policy', 'Route maps, prefix lists, communities'),
        'qos': ('📊', 'QoS', 'Quality of Service policies'),
    }
    
    # Parse config into sections
    def parse_sections(text: str) -> Tuple[Dict[str, str], List[str]]:
        sections = {}
        section_order = []
        current_section = None
        current_lines = []
        
        for line in text.split('\n'):
            stripped = line.rstrip()
            # Detect top-level section start (no leading space)
            if stripped and not stripped.startswith(' ') and not stripped.startswith('!'):
                # Save previous section
                if current_section and current_lines:
                    sections[current_section] = '\n'.join(current_lines)
                    if current_section not in section_order:
                        section_order.append(current_section)
                
                # Determine section name
                first_word = stripped.split()[0] if stripped.split() else stripped
                current_section = first_word
                current_lines = [line]
            elif current_section:
                current_lines.append(line)
        
        # Don't forget the last section
        if current_section and current_lines:
            sections[current_section] = '\n'.join(current_lines)
            if current_section not in section_order:
                section_order.append(current_section)
        
        return sections, section_order
    
    sections, section_order = parse_sections(config_text)
    
    if not sections:
        console.print("[yellow]Could not parse configuration into sections.[/yellow]")
        return None
    
    # Track section actions
    section_actions = {sec: 'keep' for sec in section_order}  # default: keep
    modified = False
    console.print("\n[bold cyan]━━━ Edit Configuration by Sections ━━━[/bold cyan]")
    console.print(f"[dim]File: {filepath.name}[/dim]")
    console.print(f"[dim]Detected {len(sections)} sections[/dim]")
    
    # ══════════════════════════════════════════════════════════════════════
    # PHASE 1: Quick section overview and action selection (like option 3)
    # ══════════════════════════════════════════════════════════════════════
    console.print("\n[bold]Select action for each section:[/bold]")
    console.print("[dim]  [K]eep = preserve unchanged  |  [E]dit = modify with wizard  |  [D]elete = remove  |  [S]kip = ignore[/dim]\n")
    
    # Show all sections with info and collect initial actions
    for section_name in section_order:
        section_content = sections.get(section_name, "")
        line_count = len(section_content.split('\n')) if section_content else 0
        
        # Get display info
        icon, display_name, description = SECTION_INFO.get(
            section_name, ('📄', section_name.title(), 'Configuration section')
        )
        
        # Build info string based on section type
        if section_name == 'system':
            # Parse system info
            sys_name = ""
            profile = ""
            for line in section_content.split('\n'):
                if 'host-name' in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        sys_name = parts[-1]
                if 'profile' in line and 'mode' not in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        profile = parts[-1]
            info_parts = []
            if sys_name:
                info_parts.append(sys_name)
            if profile:
                info_parts.append(f"profile: {profile}")
            info_parts.append(f"{line_count} lines")
            info = ", ".join(info_parts)
            default_action = "k"  # Keep system by default
        elif section_name == 'interfaces':
            # Count interfaces
            iface_count = section_content.count('\n  ') if section_content else 0
            info = f"~{iface_count} interfaces, {line_count} lines"
            default_action = "k"
        elif section_name == 'network-services':
            info = f"{line_count} lines"
            default_action = "k"
        elif section_name == 'protocols':
            # Check for BGP AS
            as_match = re.search(r'bgp\s+(\d+)', section_content) if section_content else None
            if as_match:
                info = f"BGP AS {as_match.group(1)}, {line_count} lines"
            else:
                info = f"{line_count} lines"
            default_action = "k"
        else:
            info = f"{line_count} lines" if line_count > 0 else "[dim]empty[/dim]"
            default_action = "k" if line_count > 0 else "s"
        
        # Prompt for action
        prompt_text = f"  {icon} {display_name.upper():18} ({info})"
        action = Prompt.ask(
            prompt_text,
            choices=["k", "K", "e", "E", "d", "D", "s", "S"],
            default=default_action
        ).lower()
        
        action_map = {'k': 'keep', 'e': 'edit', 'd': 'delete', 's': 'skip'}
        section_actions[section_name] = action_map.get(action, 'keep')
    
    # Show summary
    console.print("\n[bold cyan]─── Selection Summary ───[/bold cyan]")
    action_icons = {
        'keep': '[green]✓ Keep[/green]',
        'edit': '[yellow]✎ Edit[/yellow]',
        'delete': '[red]✗ Delete[/red]',
        'skip': '[dim]○ Skip[/dim]'
    }
    for section_name in section_order:
        action = section_actions.get(section_name, 'keep')
        icon, display_name, _ = SECTION_INFO.get(section_name, ('📄', section_name.title(), ''))
        console.print(f"  {icon} {display_name:18} → {action_icons.get(action, action)}")
    
    # Confirm or modify
    console.print("\n[bold]Options:[/bold]")
    console.print("  [C] Continue - proceed with these actions")
    console.print("  [M] Modify - change a specific section")
    console.print("  [V] View - view a section's content")
    console.print("  [B] Back - cancel and return")
    
    confirm_action = Prompt.ask(
        "Select",
        choices=["c", "C", "m", "M", "v", "V", "b", "B"],
        default="c"
    ).lower()
    
    if confirm_action == 'b':
        raise BackException()
    
    # ══════════════════════════════════════════════════════════════════════
    # PHASE 2: Handle modifications if requested
    # ══════════════════════════════════════════════════════════════════════
    while confirm_action in ('m', 'v'):
        if confirm_action == 'v':
            # View a section
            console.print("\n[bold]Which section to view?[/bold]")
            for i, section_name in enumerate(section_order, 1):
                icon, display_name, _ = SECTION_INFO.get(section_name, ('📄', section_name.title(), ''))
                console.print(f"  [{i}] {icon} {display_name}")
            console.print("  [B] Back")
            
            view_choice = Prompt.ask("Select", default="b").lower()
            if view_choice != 'b' and view_choice.isdigit():
                idx = int(view_choice) - 1
                if 0 <= idx < len(section_order):
                    section_name = section_order[idx]
                    section_content = sections.get(section_name, "")
                    icon, display_name, _ = SECTION_INFO.get(section_name, ('📄', section_name.title(), ''))
                    console.print(f"\n[bold]{icon} {display_name} Configuration:[/bold]")
                    console.print("-" * 70)
                    for line in section_content.split('\n')[:50]:
                        console.print(line)
                    if len(section_content.split('\n')) > 50:
                        console.print(f"[dim]... ({len(section_content.split(chr(10))) - 50} more lines)[/dim]")
                    console.print("-" * 70)
                    Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
        
        elif confirm_action == 'm':
            # Modify a section's action
            console.print("\n[bold]Which section to modify?[/bold]")
            for i, section_name in enumerate(section_order, 1):
                icon, display_name, _ = SECTION_INFO.get(section_name, ('📄', section_name.title(), ''))
                current = section_actions.get(section_name, 'keep')
                console.print(f"  [{i}] {icon} {display_name} - currently: {action_icons.get(current, current)}")
            console.print("  [B] Back")
            
            mod_choice = Prompt.ask("Select", default="b").lower()
            if mod_choice != 'b' and mod_choice.isdigit():
                idx = int(mod_choice) - 1
                if 0 <= idx < len(section_order):
                    section_name = section_order[idx]
                    icon, display_name, _ = SECTION_INFO.get(section_name, ('📄', section_name.title(), ''))
                    console.print(f"\n[bold]New action for {display_name}:[/bold]")
                    console.print("  [K] Keep  [E] Edit  [D] Delete  [S] Skip")
                    new_action = Prompt.ask("Action", choices=["k", "K", "e", "E", "d", "D", "s", "S"], default="k").lower()
                    section_actions[section_name] = action_map.get(new_action, 'keep')
                    console.print(f"[green]✓ {display_name} set to {action_icons.get(section_actions[section_name])}[/green]")
        
        # Show updated summary and ask again
        console.print("\n[bold cyan]─── Updated Summary ───[/bold cyan]")
        for section_name in section_order:
            action = section_actions.get(section_name, 'keep')
            icon, display_name, _ = SECTION_INFO.get(section_name, ('📄', section_name.title(), ''))
            console.print(f"  {icon} {display_name:18} → {action_icons.get(action, action)}")
        
        confirm_action = Prompt.ask(
            "\n[C]ontinue / [M]odify / [V]iew / [B]ack",
            choices=["c", "C", "m", "M", "v", "V", "b", "B"],
            default="c"
        ).lower()
        
        if confirm_action == 'b':
            raise BackException()
    
    # ══════════════════════════════════════════════════════════════════════
    # PHASE 3: Process sections marked for editing (using wizards)
    # ══════════════════════════════════════════════════════════════════════
    sections_to_edit = [s for s in section_order if section_actions.get(s) == 'edit']
    
    if sections_to_edit:
        console.print(f"\n[bold cyan]━━━ Editing {len(sections_to_edit)} Section(s) ━━━[/bold cyan]")
    
    section_idx = 0
    while section_idx < len(sections_to_edit):
        section_name = sections_to_edit[section_idx]
        section_content = sections.get(section_name, "")
        line_count = len(section_content.split('\n'))
        
        # Get display info
        icon, display_name, description = SECTION_INFO.get(
            section_name, ('📄', section_name.title(), 'Configuration section')
        )
        
        console.print(f"\n[bold cyan]─── Editing {icon} {display_name} ({section_idx + 1}/{len(sections_to_edit)}) ───[/bold cyan]")
        console.print(f"[dim]{line_count} lines | {description}[/dim]")
        
        # Show edit options
        console.print("\n[bold]Edit Options:[/bold]")
        console.print("  [W] Wizard - Use guided configuration wizard")
        console.print("  [R] Raw - Open in text editor (nano/vim)")
        console.print("  [V] View - View current content first")
        console.print("  [S] Skip - Keep unchanged (change mind)")
        console.print("  [B] Back - Return to previous section")
        
        edit_action = Prompt.ask(
            "Select",
            choices=["w", "W", "r", "R", "v", "V", "s", "S", "b", "B"],
            default="w"
        ).lower()
        
        if edit_action == 'b':
            # Go back to previous section
            if section_idx > 0:
                section_idx -= 1
                prev_section = sections_to_edit[section_idx]
                prev_icon, prev_name, _ = SECTION_INFO.get(prev_section, ('📄', prev_section.title(), ''))
                console.print(f"\n[yellow]← Going back to {prev_name}[/yellow]")
            else:
                console.print("\n[bold]Already at first section. Return to section selection?[/bold]")
                if Confirm.ask("Return", default=False):
                    # Would need to restart the whole flow - for now just continue
                    pass
            continue
        
        elif edit_action == 's':
            # Skip - change mind, keep unchanged
            section_actions[section_name] = 'keep'
            console.print(f"[dim]Changed to keep {display_name} unchanged[/dim]")
            section_idx += 1
            continue
        
        elif edit_action == 'v':
            # View full section
            console.print(f"\n[bold]Full {display_name} Configuration:[/bold]")
            console.print("-" * 70)
            for line in section_content.split('\n')[:100]:
                console.print(line)
            if len(section_content.split('\n')) > 100:
                console.print(f"[dim]... ({len(section_content.split(chr(10))) - 100} more lines)[/dim]")
            console.print("-" * 70)
            Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
            continue  # Stay on same section
        
        elif edit_action == 'w':
            # Edit using WIZARD functions - same as normal config wizard
            console.print(f"\n[bold cyan]━━━ Wizard: {display_name} ━━━[/bold cyan]")
            
            if not device or not multi_ctx:
                console.print("[yellow]Wizard mode requires device context. Use [R] Raw edit instead.[/yellow]")
                continue
            
            try:
                # Create a temporary wizard state for this section
                from .models import WizardState, HierarchyConfig, HierarchyAction
                from .config_parser import ConfigParser
                
                temp_state = WizardState(device_id=device.device_id if hasattr(device, 'device_id') else 'temp')
                parser = ConfigParser()
                parser.parse(section_content)
                
                # Store current config in multi_ctx for wizard to detect
                multi_ctx.configs[device.hostname] = config_text
                
                new_content = None
                
                # Call appropriate wizard function based on section
                if section_name == 'system':
                    result = configure_system(temp_state, section_content, parser, multi_ctx)
                    if result and result != 's':
                        new_content = temp_state.hierarchies.get('system', HierarchyConfig(name='system')).new_config
                
                elif section_name == 'interfaces':
                    result = configure_interfaces(temp_state, section_content, parser, multi_ctx)
                    if result and result != 's':
                        new_content = temp_state.hierarchies.get('interfaces', HierarchyConfig(name='interfaces')).new_config
                
                elif section_name == 'network-services':
                    result = configure_services(temp_state, section_content, parser, multi_ctx)
                    if result and result != 's':
                        new_content = temp_state.hierarchies.get('services', HierarchyConfig(name='services')).new_config
                
                elif section_name == 'protocols':
                    # Protocols section - offer BGP/IGP sub-menu
                    console.print("\n[bold]Protocols - Select sub-section:[/bold]")
                    console.print("  [1] BGP - Border Gateway Protocol")
                    console.print("  [2] IGP - OSPF/ISIS routing")
                    console.print("  [3] All protocols (full wizard)")
                    console.print("  [B] Back")
                    
                    proto_choice = Prompt.ask("Select", choices=["1", "2", "3", "b", "B"], default="b").lower()
                    
                    if proto_choice == "1":
                        result = configure_bgp(temp_state, section_content, parser, multi_ctx)
                        if result and result != 's':
                            new_content = temp_state.hierarchies.get('bgp', HierarchyConfig(name='bgp')).new_config
                    elif proto_choice == "2":
                        result = configure_igp(temp_state, section_content, parser, multi_ctx)
                        if result and result != 's':
                            new_content = temp_state.hierarchies.get('igp', HierarchyConfig(name='igp')).new_config
                    elif proto_choice == "3":
                        # Run both
                        configure_igp(temp_state, section_content, parser, multi_ctx)
                        configure_bgp(temp_state, section_content, parser, multi_ctx)
                        # Combine results
                        igp_config = temp_state.hierarchies.get('igp', HierarchyConfig(name='igp')).new_config or ""
                        bgp_config = temp_state.hierarchies.get('bgp', HierarchyConfig(name='bgp')).new_config or ""
                        if igp_config or bgp_config:
                            new_content = (igp_config + "\n" + bgp_config).strip()
                
                else:
                    # Other sections - fall back to raw edit
                    console.print(f"[yellow]No wizard available for {display_name}. Use [R] Raw edit.[/yellow]")
                    continue
                
                # Apply changes if wizard produced new content
                if new_content and new_content.strip():
                    sections[section_name] = new_content
                    section_actions[section_name] = 'edit'
                    modified = True
                    new_lines = len(new_content.split('\n'))
                    console.print(f"[green]✓ {display_name} configured ({new_lines:,} lines)[/green]")
                else:
                    console.print(f"[dim]{display_name} unchanged[/dim]")
                
            except BackException:
                console.print(f"[dim]Cancelled editing {display_name}[/dim]")
                continue  # Stay on same section
            except Exception as e:
                console.print(f"[red]Error in wizard: {e}[/red]")
                console.print("[dim]Use [R] Raw edit as fallback[/dim]")
                continue
            
            section_idx += 1
        
        elif edit_action == 'r':
            # Raw edit in external editor (advanced)
            console.print(f"[cyan]Opening {display_name} in external editor...[/cyan]")
            
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'_{section_name}.txt', delete=False) as tf:
                tf.write(section_content)
                temp_path = tf.name
            
            editor = os.environ.get('EDITOR', 'nano')
            subprocess.call([editor, temp_path])
            
            with open(temp_path, 'r') as f:
                new_content = f.read()
            
            os.unlink(temp_path)
            
            if new_content != section_content:
                sections[section_name] = new_content
                section_actions[section_name] = 'edit'
                modified = True
                new_lines = len(new_content.split('\n'))
                console.print(f"[green]✓ {display_name} modified ({new_lines:,} lines)[/green]")
            else:
                console.print(f"[dim]{display_name} unchanged[/dim]")
            
            section_idx += 1
    
    # ══════════════════════════════════════════════════════════════════════
    # PHASE 4: Summary and save
    # ══════════════════════════════════════════════════════════════════════
    console.print("\n" + "="*70)
    console.print("[bold cyan] SUMMARY [/bold cyan]")
    console.print("="*70)
    
    for sec in section_order:
        icon, display_name, _ = SECTION_INFO.get(sec, ('📄', sec.title(), ''))
        action = section_actions.get(sec, 'keep')
        lines = len(sections.get(sec, '').split('\n'))
        
        if action == 'keep':
            console.print(f"  {icon} {display_name}: [green]Keep[/green] ({lines:,} lines)")
        elif action == 'edit':
            console.print(f"  {icon} {display_name}: [yellow]Edited[/yellow] ({lines:,} lines)")
        elif action == 'delete':
            console.print(f"  {icon} {display_name}: [red]Delete[/red]")
    
    console.print()
    
    if not modified:
        console.print("[dim]No changes made.[/dim]")
        if Confirm.ask("Continue without changes?", default=True):
            return None
        else:
            # Let user re-edit
            return _edit_config_by_sections(config_text, filepath, device, multi_ctx)
    
    # Confirm save
    if Confirm.ask("[bold]Save changes to file?[/bold]", default=True):
        # Reassemble config excluding deleted sections
        new_config_parts = []
        for sec in section_order:
            if section_actions.get(sec) != 'delete':
                new_config_parts.append(sections[sec])
        
        new_config = '\n'.join(new_config_parts)
        
        # Save to file
        with open(filepath, 'w') as f:
            f.write(new_config)
        
        console.print(f"[green]✓ Configuration saved ({len(new_config.split(chr(10))):,} lines)[/green]")
        return new_config
    else:
        console.print("[dim]Changes discarded.[/dim]")
        return None


def show_quick_load_menu(device: 'Device', multi_ctx: 'MultiDeviceContext' = None) -> Optional[Tuple[str, bool, Path]]:
    """Show menu for quick-loading recent configurations.
    
    Args:
        device: Primary device for configuration loading
        multi_ctx: Optional multi-device context for synchronized operations
    
    Returns:
        Tuple of (config_text, already_validated, filepath) if user selects one, None otherwise
    """
    from rich.columns import Columns
    from rich.panel import Panel
    
    # In multi-device mode, load history for ALL devices
    if multi_ctx and len(multi_ctx.devices) > 1:
        all_history = {}
        for dev in multi_ctx.devices:
            dev_history = _load_config_history(dev.hostname, limit=3)
            if dev_history:
                all_history[dev.hostname] = dev_history
        history = _load_config_history(device.hostname, limit=3)  # Primary device
    else:
        history = _load_config_history(device.hostname, limit=3)
        all_history = {device.hostname: history} if history else {}
    
    if not history and not all_history:
        return None
    
    # Multi-device mode: Show split view with both devices
    if multi_ctx and len(multi_ctx.devices) >= 2:
        console.print("\n[bold cyan]╔══════════════════════════════════════════════════════════════════╗[/bold cyan]")
        console.print("[bold cyan]║          📋 Multi-Device Configuration Overview                  ║[/bold cyan]")
        console.print("[bold cyan]╚══════════════════════════════════════════════════════════════════╝[/bold cyan]")
        
        panels = []
        for dev in multi_ctx.devices:
            h = dev.hostname
            lo = multi_ctx.loopbacks.get(h, "N/A")
            asn = multi_ctx.bgp_asn.get(h, 0)
            rt_count = len(multi_ctx.route_targets.get(h, set()))
            mh_count = len(multi_ctx.mh_config.get(h, {}))
            peer_list = multi_ctx.bgp_peers.get(h, [])
            summary = multi_ctx.summaries.get(h)
            
            content_lines = []
            
            # ─── SYSTEM ───
            content_lines.append("[bold white]─── SYSTEM ───[/bold white]")
            if summary and summary.system_type:
                content_lines.append(f"  [dim]Type:[/dim] {summary.system_type}")
            if summary and summary.dnos_version:
                ver_short = summary.dnos_version.split('_')[0] if '_' in summary.dnos_version else summary.dnos_version[:20]
                content_lines.append(f"  [dim]DNOS:[/dim] {ver_short}")
            if summary and summary.uptime:
                content_lines.append(f"  [dim]Up:[/dim] {summary.uptime}")
            
            # ─── ROUTING ───
            content_lines.append("")
            content_lines.append("[bold white]─── ROUTING ───[/bold white]")
            content_lines.append(f"  [cyan]Loopback:[/cyan] {lo}")
            if asn:
                content_lines.append(f"  [cyan]BGP AS:[/cyan] {asn}")
            
            # BGP peers with status
            if summary and summary.bgp_peers_total > 0:
                peer_status = f"{summary.bgp_peers_up}/{summary.bgp_peers_total}"
                if summary.bgp_peers_up == summary.bgp_peers_total:
                    peer_str = f"[green]{peer_status} UP[/green]"
                elif summary.bgp_peers_up == 0:
                    peer_str = f"[red]{peer_status} UP[/red]"
                else:
                    peer_str = f"[yellow]{peer_status} UP[/yellow]"
                content_lines.append(f"  [cyan]Peers:[/cyan] {peer_str}")
            elif peer_list:
                content_lines.append(f"  [cyan]Peers:[/cyan] {len(peer_list)} configured")
            
            if summary and summary.igp:
                content_lines.append(f"  [dim]IGP:[/dim] {summary.igp}")
            if summary and summary.label_protocol:
                content_lines.append(f"  [dim]Labels:[/dim] {summary.label_protocol}")
            
            # ─── SERVICES ───
            content_lines.append("")
            content_lines.append("[bold white]─── SERVICES ───[/bold white]")
            if summary and summary.services:
                for svc_type, (up, total, transport) in summary.services.items():
                    if up == total:
                        svc_str = f"[green]{up}/{total} UP[/green]"
                    elif up == 0:
                        svc_str = f"[red]{up}/{total} UP[/red]"
                    else:
                        svc_str = f"[yellow]{up}/{total} UP[/yellow]"
                    content_lines.append(f"  [cyan]{svc_type}:[/cyan] {svc_str} ({transport})")
            else:
                content_lines.append(f"  [cyan]RTs:[/cyan] {rt_count} configured")
            
            if summary and summary.pwhe_parent > 0:
                pwhe_str = f"{summary.pwhe_parent:,} × 2"
                if summary.pwhe_up > 0:
                    pwhe_str += f" [green]({summary.pwhe_up:,} UP)[/green]"
                else:
                    pwhe_str += " [dim](0 UP)[/dim]"
                content_lines.append(f"  [dim]PWHE:[/dim] {pwhe_str}")
            
            # ─── MULTIHOMING ───
            content_lines.append("")
            content_lines.append("[bold white]─── MULTIHOMING ───[/bold white]")
            if mh_count > 0:
                # Get a sample ESI to show prefix pattern
                mh_dict = multi_ctx.mh_config.get(h, {})
                sample_esi = next(iter(mh_dict.values()), "") if mh_dict else ""
                esi_prefix = ":".join(sample_esi.split(":")[:3]) if sample_esi else "?"
                content_lines.append(f"  [green]✓ {mh_count} interfaces[/green]")
                content_lines.append(f"  [dim]ESI prefix:[/dim] {esi_prefix}:...")
                
                # Check if any services have MH configured (interfaces that match service ACs)
                mh_ifaces = set(mh_dict.keys())
                # Count matching services
                pwhe_ifaces = set(multi_ctx.interfaces.get(h, []))
                mh_in_services = len(mh_ifaces & pwhe_ifaces)
                if mh_in_services > 0:
                    content_lines.append(f"  [green]✓ In services: {mh_in_services}[/green]")
            else:
                content_lines.append("  [yellow]○ Not configured[/yellow]")
                content_lines.append("  [dim]Use [M] to add MH[/dim]")
            
            # ─── RECENT ───
            dev_history = _load_config_history(h, limit=1)
            if dev_history:
                content_lines.append("")
                content_lines.append("[bold white]─── RECENT ───[/bold white]")
                entry = dev_history[0]
                try:
                    ts = datetime.fromisoformat(entry['timestamp'])
                    date_str = ts.strftime("%m-%d %H:%M")
                except:
                    date_str = "?"
                status_icon = "[green]✓[/green]" if entry.get('pushed') else ("[cyan]◉[/cyan]" if entry.get('validated') else "[dim]○[/dim]")
                fname = entry['filename'][:22] + "..." if len(entry['filename']) > 22 else entry['filename']
                content_lines.append(f"  {status_icon} {fname}")
                content_lines.append(f"  [dim]{date_str} • {entry.get('line_count', '?'):,} lines[/dim]")
            
            # Determine panel color based on overall health
            if mh_count > 0 and summary and summary.services:
                total_svc = sum(t for _, t, _ in summary.services.values())
                total_up = sum(u for u, _, _ in summary.services.values())
                if total_up == total_svc:
                    border_style = "green"
                elif total_up > 0:
                    border_style = "yellow"
                else:
                    border_style = "red"
            elif mh_count > 0:
                border_style = "green"
            else:
                border_style = "yellow"
            
            panel = Panel(
                "\n".join(content_lines),
                title=f"[bold white]{h}[/bold white]",
                subtitle=f"[dim]{lo}[/dim]" if lo != "N/A" else None,
                border_style=border_style,
                expand=True,
                padding=(0, 1)
            )
            panels.append(panel)
        
        console.print(Columns(panels, expand=True, equal=True))
        
        # Show cross-device analysis
        shared_pairs = multi_ctx.get_shared_evpn_peers()
        if shared_pairs:
            console.print(f"\n[bold cyan]🔗 EVPN Peering Analysis:[/bold cyan]")
            for h1, h2, shared_rt in shared_pairs:
                mh1 = len(multi_ctx.mh_config.get(h1, {}))
                mh2 = len(multi_ctx.mh_config.get(h2, {}))
                if mh1 > 0 and mh2 > 0:
                    sync_status = "[green]✓ MH synced[/green]"
                elif mh1 > 0 or mh2 > 0:
                    sync_status = "[yellow]⚠ MH mismatch[/yellow]"
                else:
                    sync_status = "[dim]○ No MH[/dim]"
                console.print(f"  {h1} ↔ {h2}: [cyan]{shared_rt:,} shared RTs[/cyan] • {sync_status}")
        console.print()
    else:
        # Single device mode: Show traditional table
        console.print("\n[bold cyan]📋 Recent Configurations[/bold cyan]")
    
    table = Table(box=box.ROUNDED, show_header=True)
    table.add_column("#", style="dim", width=3)
    if multi_ctx and len(multi_ctx.devices) > 1:
        table.add_column("Device", width=10)
    table.add_column("Filename", min_width=25)
    table.add_column("Sections", min_width=15)
    table.add_column("Lines", justify="right", width=8)
    table.add_column("Date", width=18)
    table.add_column("Status", width=12)
    
    # Build combined list for multi-device mode
    combined_entries = []
    if multi_ctx and len(multi_ctx.devices) > 1:
        for hostname, dev_history in all_history.items():
            for entry in dev_history:
                combined_entries.append((hostname, entry))
        # Sort by timestamp descending
        combined_entries.sort(key=lambda x: x[1].get('timestamp', ''), reverse=True)
        # Limit to 6 entries total
        combined_entries = combined_entries[:6]
    else:
        combined_entries = [(device.hostname, entry) for entry in (history or [])]
    
    for i, (hostname, entry) in enumerate(combined_entries, 1):
        # Parse timestamp
        try:
            ts = datetime.fromisoformat(entry['timestamp'])
            date_str = ts.strftime("%Y-%m-%d %H:%M")
        except:
            date_str = "Unknown"
        
        sections = ', '.join(entry.get('sections', []))
        
        # Status: Committed > Validated > New
        if entry.get('pushed'):
            status = "[green]Committed[/green]"
        elif entry.get('validated'):
            status = "[cyan]Validated[/cyan]"
        else:
            status = "[dim]New[/dim]"
        
        if multi_ctx and len(multi_ctx.devices) > 1:
            # Color-code device name
            dev_color = "cyan" if hostname == multi_ctx.devices[0].hostname else "magenta"
            table.add_row(
                str(i),
                f"[{dev_color}]{hostname}[/{dev_color}]",
                entry['filename'],
                sections,
                f"{entry.get('line_count', '?'):,}",
                date_str,
                status
            )
        else:
            table.add_row(
                str(i),
                entry['filename'],
                sections,
                f"{entry.get('line_count', '?'):,}",
                date_str,
                status
            )
    
    console.print(table)
    
    console.print("\n[bold cyan]Options:[/bold cyan]")
    console.print("  [cyan][1-3][/cyan] Select a configuration to load")
    console.print("  [green][N][/green] Start new configuration [dim](default)[/dim]")
    console.print("  [magenta][G][/magenta] Get/Save running config from device")
    console.print("  [yellow][D][/yellow] Delete/manage saved configs")
    console.print("  [dim][B][/dim] Back to device menu")
    
    if multi_ctx and len(multi_ctx.devices) > 1:
        device_names = ", ".join([d.hostname for d in multi_ctx.devices])
        console.print(f"\n[bold cyan]── Multi-Device Options ({device_names}) ──[/bold cyan]")
        console.print(f"  [C] [cyan]Compare Configs[/cyan] - Diff between devices")
        console.print(f"  [R] [cyan]Refresh Configs[/cyan] - Fetch running configs from all")
        console.print(f"  [S] [cyan]Sync Status[/cyan] - Detailed device comparison")
        console.print(f"  [P] [cyan]Push to All[/cyan] - Push same config to all devices")
    
    choice = Prompt.ask("Select", default="n").lower()
    
    if choice == 'b':
        # Back one step in wizard
        raise BackException()
    
    if choice == 'd':
        # Show delete menu
        _show_delete_files_menu(device, history)
        # After delete, show menu again
        return show_quick_load_menu(device, multi_ctx)
    
    if choice == 'g':
        # Get/Save running config from device
        _save_running_config_from_device(device, multi_ctx)
        # After save, show menu again
        return show_quick_load_menu(device, multi_ctx)
    
    if choice == 'c' and multi_ctx and len(multi_ctx.devices) > 1:
        # Compare configurations between devices
        _show_multi_device_compare(multi_ctx)
        return show_quick_load_menu(device, multi_ctx)
    
    if choice == 'r' and multi_ctx and len(multi_ctx.devices) > 1:
        # Refresh running configs from all devices
        _refresh_multi_device_configs(multi_ctx)
        return show_quick_load_menu(device, multi_ctx)
    
    if choice == 's' and multi_ctx and len(multi_ctx.devices) > 1:
        # Show detailed sync status
        _show_multi_device_sync_status(multi_ctx)
        return show_quick_load_menu(device, multi_ctx)
    
    if choice == 'p' and multi_ctx and len(multi_ctx.devices) > 1:
        # Push config to all devices
        _push_config_to_all_devices(multi_ctx, history)
        return show_quick_load_menu(device, multi_ctx)
    
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(combined_entries):
            selected_hostname, entry = combined_entries[idx]
            filepath = Path(entry['filepath'])
            if filepath.exists():
                with open(filepath, 'r') as f:
                    config_text = f.read()
                
                already_validated = entry.get('validated', False) or entry.get('pushed', False)
                
                # In multi-device mode, show which device this config is for
                if multi_ctx and len(multi_ctx.devices) > 1:
                    console.print(f"[green]✓ Loaded: {filepath.name}[/green] [dim](for {selected_hostname})[/dim]")
                    # Check if this config is being applied to a different device
                    if selected_hostname != device.hostname:
                        console.print(f"[yellow]⚠ Note: This config was created for {selected_hostname}[/yellow]")
                        console.print(f"[dim]  Will be applied to primary device: {device.hostname}[/dim]")
                else:
                    console.print(f"[green]✓ Loaded: {filepath.name}[/green]")
                
                if already_validated:
                    console.print("[cyan]  This config was previously validated - can commit directly[/cyan]")
                
                return (config_text, already_validated, filepath)
            else:
                console.print(f"[red]File not found: {filepath}[/red]")
    
    return None


def _save_running_config_from_device(device: 'Device', multi_ctx: 'MultiDeviceContext' = None):
    """Fetch and save running configuration from device.
    
    Connects to the device via SSH, fetches the current running configuration,
    and saves it to a timestamped file in the device's config directory.
    """
    from datetime import datetime
    from .utils import get_device_config_dir
    from .config_extractor import InteractiveExtractor
    from rich.progress import Progress, SpinnerColumn, TextColumn
    
    console.print(f"\n[bold cyan]💾 Save Running Configuration from {device.hostname}[/bold cyan]")
    console.print("[dim]This will connect to the device and fetch the current running config.[/dim]")
    
    # Confirm
    if not Confirm.ask("Proceed?", default=True):
        return
    
    # In multi-device mode, ask if user wants to save from all devices
    devices_to_fetch = [device]
    if multi_ctx and len(multi_ctx.devices) > 1:
        console.print(f"\n[bold]Devices available:[/bold]")
        for i, dev in enumerate(multi_ctx.devices, 1):
            console.print(f"  [{i}] {dev.hostname}")
        console.print(f"  [A] All devices")
        console.print(f"  [B] Cancel")
        
        fetch_choice = Prompt.ask("Select device(s)", default="A").lower()
        
        if fetch_choice == 'b':
            return
        elif fetch_choice == 'a':
            devices_to_fetch = multi_ctx.devices
        elif fetch_choice.isdigit():
            idx = int(fetch_choice) - 1
            if 0 <= idx < len(multi_ctx.devices):
                devices_to_fetch = [multi_ctx.devices[idx]]
    
    # Fetch from each device
    for dev in devices_to_fetch:
        console.print(f"\n[cyan]Connecting to {dev.hostname}...[/cyan]")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task(f"Fetching config from {dev.hostname}...", total=None)
                
                # Use InteractiveExtractor to get running config
                with InteractiveExtractor(dev, timeout=180) as extractor:
                    running_config = extractor.get_running_config()
                
                progress.update(task, description="Processing...")
            
            if not running_config or len(running_config) < 100:
                console.print(f"[red]✗ Failed to get config from {dev.hostname}[/red]")
                continue
            
            # Count lines and significant content
            line_count = len(running_config.split('\n'))
            
            console.print(f"\n[green]✓ Fetched {line_count:,} lines from {dev.hostname}[/green]")
            
            # Always ask for a descriptive name
            console.print("\n[bold]Save Configuration[/bold]")
            console.print(f"[dim]File will be saved as: [cyan]{dev.hostname}[/cyan]_<your-name>.txt[/dim]")
            console.print("[dim]Examples: L2-AC-2300, EVPN-Scale, Baseline, Pre-Upgrade[/dim]")
            console.print("[dim]Enter [B] to cancel.[/dim]")
            
            config_name = Prompt.ask("Config name").strip()
            
            if config_name.lower() == 'b':
                console.print("[yellow]Save cancelled.[/yellow]")
                continue
            
            if not config_name:
                console.print("[red]Config name cannot be empty.[/red]")
                continue
            
            # Clean up the name
            import re
            # Remove .txt extension if user added it
            config_name = re.sub(r'\.txt$', '', config_name, flags=re.IGNORECASE)
            # Remove device hostname prefix if user added it (avoid duplication)
            hostname_lower = dev.hostname.lower()
            name_lower = config_name.lower()
            if name_lower.startswith(hostname_lower + '_'):
                config_name = config_name[len(dev.hostname) + 1:]
            elif name_lower.startswith(hostname_lower + '-'):
                config_name = config_name[len(dev.hostname) + 1:]
            elif name_lower == hostname_lower:
                config_name = "running"
            # Sanitize: only allow alphanumeric, underscore, dash
            config_name = re.sub(r'[^a-zA-Z0-9_\-]', '-', config_name)
            # Remove leading/trailing dashes or underscores
            config_name = config_name.strip('-_')
            # Remove multiple consecutive dashes/underscores
            config_name = re.sub(r'[-_]+', '-', config_name)
            
            if not config_name:
                console.print("[red]Config name cannot be empty after cleanup.[/red]")
                continue
            
            # Get save directory
            config_dir = get_device_config_dir(dev.hostname)
            config_dir.mkdir(parents=True, exist_ok=True)
            
            # Build filename: hostname_configname.txt
            filename = f"{dev.hostname}_{config_name}.txt"
            filepath = config_dir / filename
            
            # Show preview of final filename
            console.print(f"[dim]Will save as: [cyan]{filename}[/cyan][/dim]")
            
            # Check if file exists and ask for overwrite
            if filepath.exists():
                console.print(f"\n[yellow]⚠ File '{filename}' already exists.[/yellow]")
                overwrite = Prompt.ask(
                    "Overwrite existing file?",
                    choices=["y", "n"],
                    default="n"
                ).lower()
                if overwrite != 'y':
                    console.print("[yellow]Save cancelled.[/yellow]")
                    continue
            
            # Save the configuration
            with open(filepath, 'w') as f:
                f.write(running_config)
            
            # Also update running.txt (the cached version)
            running_path = config_dir / "running.txt"
            with open(running_path, 'w') as f:
                f.write(running_config)
            
            console.print(f"\n[green]✓ Saved {line_count:,} lines to:[/green]")
            console.print(f"  [bold]→ {filepath}[/bold]")
            console.print(f"  [dim]→ {running_path} (cache updated)[/dim]")
            
            # Update config history - use correct function with correct parameters
            # Create section_actions dict for running config
            section_actions = {'running': 'keep'}
            _save_config_history(
                dev.hostname,
                filepath,
                section_actions,
                running_config
            )
            console.print("[dim]✓ Configuration history updated[/dim]")
            
        except Exception as e:
            console.print(f"[red]✗ Error fetching config from {dev.hostname}: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
    
    console.print("\n[green]Done![/green]")
    Prompt.ask("[dim]Press Enter to continue[/dim]", default="")


def _show_delete_files_menu(device: 'Device', history: List[Dict] = None):
    """Show menu to delete configuration files for a device."""
    from .utils import get_device_config_dir
    
    config_dir = get_device_config_dir(device.hostname)
    
    # Get all config files (not just history)
    all_files = sorted(config_dir.glob("*.txt"), key=lambda f: f.stat().st_mtime, reverse=True)
    # Exclude running.txt
    all_files = [f for f in all_files if f.name != "running.txt"]
    
    if not all_files:
        console.print("[yellow]No configuration files to delete.[/yellow]")
        return
    
    console.print(f"\n[bold red]🗑️  Delete Configuration Files ({device.hostname})[/bold red]")
    
    table = Table(box=box.ROUNDED, show_header=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Filename", min_width=30)
    table.add_column("Size", justify="right", width=10)
    table.add_column("Modified", width=18)
    
    for i, f in enumerate(all_files[:10], 1):  # Show max 10 files
        size_kb = f.stat().st_size / 1024
        mod_time = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        table.add_row(str(i), f.name, f"{size_kb:.1f} KB", mod_time)
    
    if len(all_files) > 10:
        table.add_row("...", f"({len(all_files) - 10} more files)", "", "")
    
    console.print(table)
    
    console.print("\n[bold]Delete Options:[/bold]")
    console.print("  [1-10] Delete specific file by number")
    console.print("  [A] Delete ALL files (except running.txt)")
    console.print("  [B] Back")
    
    choice = Prompt.ask("Select", default="b").lower()
    
    if choice == 'b':
        return
    
    if choice == 'a':
        if Confirm.ask(f"[red]Delete ALL {len(all_files)} configuration files?[/red]", default=False):
            deleted = 0
            for f in all_files:
                try:
                    f.unlink()
                    deleted += 1
                except Exception as e:
                    console.print(f"[red]Failed to delete {f.name}: {e}[/red]")
            
            # Also clear history
            history_path = _get_config_history_path(device.hostname)
            if history_path.exists():
                history_path.unlink()
            
            console.print(f"[green]✓ Deleted {deleted} files[/green]")
        return
    
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(all_files[:10]):
            file_to_delete = all_files[idx]
            if Confirm.ask(f"Delete [red]{file_to_delete.name}[/red]?", default=False):
                try:
                    file_to_delete.unlink()
                    console.print(f"[green]✓ Deleted {file_to_delete.name}[/green]")
                    
                    # Remove from history
                    history_path = _get_config_history_path(device.hostname)
                    if history_path.exists():
                        try:
                            with open(history_path, 'r') as f:
                                hist = json.load(f)
                            hist = [h for h in hist if h.get('filename') != file_to_delete.name]
                            with open(history_path, 'w') as f:
                                json.dump(hist, f, indent=2)
                        except:
                            pass
                except Exception as e:
                    console.print(f"[red]Failed to delete: {e}[/red]")


def show_breadcrumb(path: List[str] = None):
    """Display the current navigation path as a breadcrumb.
    
    Args:
        path: Optional path to display. If None, uses global state.
    """
    if path is None and _current_state is not None:
        path = _current_state.nav_path
    
    if not path:
        return
    
    # Build breadcrumb string with styling
    breadcrumb_parts = []
    for i, part in enumerate(path):
        if i == len(path) - 1:
            # Current location (highlighted)
            breadcrumb_parts.append(f"[bold cyan]{part}[/bold cyan]")
        else:
            # Parent path (dim)
            breadcrumb_parts.append(f"[dim]{part}[/dim]")
    
    breadcrumb = " › ".join(breadcrumb_parts)
    console.print(f"\n[dim]📍[/dim] {breadcrumb}")


def push_path(segment: str):
    """Add a segment to the navigation path."""
    if _current_state is not None:
        _current_state.nav_path.append(segment)


def pop_path():
    """Remove the last segment from the navigation path."""
    if _current_state is not None and _current_state.nav_path:
        _current_state.nav_path.pop()


def set_path(path: List[str]):
    """Set the entire navigation path."""
    if _current_state is not None:
        _current_state.nav_path = path.copy()


def view_current_config(hierarchy: str = None, multi_ctx: 'MultiDeviceContext' = None):
    """Display a summary of the current device configuration for a specific hierarchy or all.
    
    Shows counts and key info, not the full raw config.
    Supports multi-device mode with per-device summaries.
    
    Args:
        hierarchy: Specific hierarchy to view, or None for menu
        multi_ctx: Multi-device context for per-device summaries
    """
    # Multi-device mode: Show per-device summaries
    if multi_ctx and len(multi_ctx.devices) > 1 and hasattr(multi_ctx, 'running_configs'):
        if hierarchy:
            _view_hierarchy_multi_device(hierarchy, multi_ctx)
        else:
            # Show menu for hierarchy selection
            # Note: VRF is part of Services (Network Services), not listed separately
            console.print("\n[bold]View Current Configuration:[/bold]")
            console.print("  [1] System")
            console.print("  [2] Interfaces")
            console.print("  [3] Services (includes VRF/L3VPN)")
            console.print("  [4] IGP (ISIS/OSPF)")
            console.print("  [5] BGP")
            console.print("  [6] Flowspec")
            console.print("  [A] All (full config summary)")
            console.print("  [B] Back")
            
            choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "5", "6", "a", "A", "b", "B"], default="b").lower()
            
            if choice == "b":
                return
            
            # VRF is part of services, not listed separately
            hierarchy_map = {"1": "system", "2": "interfaces", "3": "services", "4": "igp", "5": "bgp", "6": "flowspec"}
            
            if choice == "a":
                # Show all hierarchies summary per device
                for dev in multi_ctx.devices:
                    h = dev.hostname
                    dev_config = multi_ctx.running_configs.get(h, multi_ctx.configs.get(h, ""))
                    if dev_config:
                        from .config_parser import ConfigParser
                        parser = ConfigParser()
                        console.print(f"\n[bold cyan]{'═' * 30} {h} {'═' * 30}[/bold cyan]")
                        show_current_config_summary(dev_config, parser, h)
            elif choice in hierarchy_map:
                _view_hierarchy_multi_device(hierarchy_map[choice], multi_ctx)
        return
    
    # Single device mode
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
                
                # Friendly display names for categories
                cat_display_names = {
                    'physical': 'Physical',
                    'physical_subif': 'Physical Sub-ifs',
                    'bundle': 'Bundle',
                    'bundle_subif': 'Bundle Sub-ifs',
                    'pwhe': 'PWHE',
                    'pwhe_subif': 'PWHE Sub-ifs',
                    'irb': 'IRB',
                    'loopback': 'Loopback',
                    'ctrl': 'Control',
                    'mgmt': 'Management',
                    'other': 'Other'
                }
                
                table = Table(title="Interface Summary", box=box.SIMPLE)
                table.add_column("Type", style="cyan")
                table.add_column("Count", justify="right", style="green")
                table.add_column("Examples", style="dim")
                
                for cat, ifaces in categories.items():
                    if ifaces:
                        display_name = cat_display_names.get(cat, cat.replace('_', ' ').title())
                        examples = ", ".join(ifaces[:3])
                        if len(ifaces) > 3:
                            examples += f" (+{len(ifaces) - 3})"
                        table.add_row(display_name, str(len(ifaces)), examples)
                
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
            # Show all hierarchies summary
            from .config_parser import ConfigParser
            parser = ConfigParser()
            show_current_config_summary(_current_state.current_config, parser)
        elif choice in hierarchy_map:
            view_current_config(hierarchy_map[choice])


def _view_hierarchy_multi_device(hierarchy: str, multi_ctx: 'MultiDeviceContext'):
    """View hierarchy summary for all devices in multi-device mode.
    
    Args:
        hierarchy: The hierarchy to view (system, interfaces, services, igp, bgp)
        multi_ctx: Multi-device context with configs
    """
    from rich.columns import Columns
    from rich.panel import Panel
    from rich.table import Table
    
    console.print(f"\n[bold cyan]{hierarchy.upper()} Summary - All Devices[/bold cyan]")
    
    panels = []
    for dev in multi_ctx.devices:
        h = dev.hostname
        dev_config = multi_ctx.running_configs.get(h, multi_ctx.configs.get(h, ""))
        section = extract_hierarchy_section(dev_config, hierarchy) if dev_config else ""
        
        content_lines = []
        if section:
            lines = section.strip().split('\n')
            line_count = len(lines)
            content_lines.append(f"[bold]{line_count} lines[/bold]\n")
            
            if hierarchy == 'system':
                # Parse system info
                name = re.search(r'^\s+name\s+(\S+)', section, re.MULTILINE)
                profile = re.search(r'^\s+profile\s+(\S+)', section, re.MULTILINE)
                users = re.findall(r'^\s+user\s+(\S+)', section, re.MULTILINE)
                
                if name:
                    content_lines.append(f"[cyan]Name:[/cyan] {name.group(1)}")
                if profile:
                    content_lines.append(f"[cyan]Profile:[/cyan] {profile.group(1)}")
                if users:
                    content_lines.append(f"[cyan]Users:[/cyan] {len(users)} ({', '.join(users[:2])}{'...' if len(users) > 2 else ''})")
            
            elif hierarchy == 'interfaces':
                # Count interface types
                iface_pattern = re.compile(r'^  (\S+)\s*$', re.MULTILINE)
                ifaces = iface_pattern.findall(section)
                categories = categorize_interfaces_by_type([i for i in ifaces if not i.startswith('!')])
                
                # Friendly display names for categories
                cat_display_names = {
                    'physical': 'Physical',
                    'physical_subif': 'Physical Sub-ifs',
                    'bundle': 'Bundle',
                    'bundle_subif': 'Bundle Sub-ifs',
                    'pwhe': 'PWHE',
                    'pwhe_subif': 'PWHE Sub-ifs',
                    'irb': 'IRB',
                    'loopback': 'Loopback',
                    'ctrl': 'Control',
                    'mgmt': 'Management',
                    'other': 'Other'
                }
                
                for cat, iface_list in categories.items():
                    if iface_list:
                        display_name = cat_display_names.get(cat, cat)
                        content_lines.append(f"[cyan]{display_name}:[/cyan] {len(iface_list)}")
            
            elif hierarchy == 'services':
                fxc = len(re.findall(r'evpn-vpws-fxc\s+instance', section))
                vpls = len(re.findall(r'evpn-vpls\s+instance', section))
                vrf = len(re.findall(r'^\s+vrf\s+', section, re.MULTILINE))
                
                if fxc:
                    content_lines.append(f"[cyan]FXC:[/cyan] {fxc}")
                if vpls:
                    content_lines.append(f"[cyan]VPLS:[/cyan] {vpls}")
                if vrf:
                    content_lines.append(f"[cyan]VRF:[/cyan] {vrf}")
                if not (fxc or vpls or vrf):
                    content_lines.append("[dim]No services[/dim]")
            
            elif hierarchy == 'vrf':
                # Parse VRF instances
                vrf_instances = re.findall(r'instance\s+(\S+)', section)
                interfaces = re.findall(r'interface\s+(\S+)', section)
                bgp_as = re.search(r'bgp\s+(\d+)', section)
                rd = re.findall(r'route-distinguisher\s+(\S+)', section)
                rt_import = re.findall(r'import-vpn\s+route-target\s+(\S+)', section)
                rt_export = re.findall(r'export-vpn\s+route-target\s+(\S+)', section)
                
                if vrf_instances:
                    content_lines.append(f"[cyan]VRF Instances:[/cyan] {len(vrf_instances)}")
                    if len(vrf_instances) <= 3:
                        for vrf in vrf_instances:
                            content_lines.append(f"  • {vrf}")
                    else:
                        content_lines.append(f"  • {', '.join(vrf_instances[:3])}...")
                if interfaces:
                    content_lines.append(f"[cyan]Attached Interfaces:[/cyan] {len(interfaces)}")
                if bgp_as:
                    content_lines.append(f"[cyan]BGP AS:[/cyan] {bgp_as.group(1)}")
                if rd:
                    content_lines.append(f"[cyan]RD:[/cyan] {len(rd)} configured")
                if rt_import or rt_export:
                    content_lines.append(f"[cyan]Route Targets:[/cyan] {len(rt_import)} import, {len(rt_export)} export")
                if not vrf_instances:
                    content_lines.append("[dim]No VRF configured[/dim]")
            
            elif hierarchy == 'flowspec':
                # Parse flowspec configuration
                policies = re.findall(r'policy\s+(\S+)', section)
                rules = re.findall(r'rule\s+(\S+)', section)
                match_src = len(re.findall(r'match-source-prefix', section))
                match_dst = len(re.findall(r'match-destination-prefix', section))
                actions = len(re.findall(r'action\s+', section))
                
                if policies:
                    content_lines.append(f"[magenta]Policies:[/magenta] {len(policies)}")
                if rules:
                    content_lines.append(f"[magenta]Rules:[/magenta] {len(rules)}")
                if match_src:
                    content_lines.append(f"[cyan]Match-Source:[/cyan] {match_src}")
                if match_dst:
                    content_lines.append(f"[cyan]Match-Dest:[/cyan] {match_dst}")
                if actions:
                    content_lines.append(f"[cyan]Actions:[/cyan] {actions}")
                if not (policies or rules):
                    content_lines.append("[dim]No flowspec policies[/dim]")
            
            elif hierarchy in ['bgp', 'igp']:
                # Show first few lines
                for line in lines[:8]:
                    display_line = line[:35] + "..." if len(line) > 35 else line
                    content_lines.append(f"[dim]{display_line}[/dim]")
                if line_count > 8:
                    content_lines.append(f"[dim]... ({line_count - 8} more)[/dim]")
        else:
            content_lines.append("[dim]No configuration[/dim]")
        
        panel = Panel(
            "\n".join(content_lines),
            title=f"[cyan]{h}[/cyan]",
            border_style="dim",
            width=40,
            padding=(0, 1)
        )
        panels.append(panel)
    
    # Display panels side-by-side (2 per row)
    for i in range(0, len(panels), 2):
        row = panels[i:i+2]
        if len(row) == 2:
            console.print(Columns(row, equal=True, expand=True))
        else:
            console.print(row[0])
    
    # Option to view raw config for a specific device
    console.print("\n[dim]View raw config? Enter device number or [N]o[/dim]")
    device_choices = [str(i+1) for i in range(len(multi_ctx.devices))] + ["n", "N"]
    dev_choice = Prompt.ask("Select device", choices=device_choices, default="n").lower()
    
    if dev_choice != "n":
        idx = int(dev_choice) - 1
        if 0 <= idx < len(multi_ctx.devices):
            dev = multi_ctx.devices[idx]
            dev_config = multi_ctx.running_configs.get(dev.hostname, multi_ctx.configs.get(dev.hostname, ""))
            section = extract_hierarchy_section(dev_config, hierarchy) if dev_config else ""
            if section:
                from rich.syntax import Syntax
                console.print(Panel(
                    Syntax(section, "text", theme="monokai", line_numbers=True),
                    title=f"[cyan]{dev.hostname} - {hierarchy}[/cyan]",
                    border_style="dim"
                ))


def show_multi_device_dashboard(multi_ctx: 'MultiDeviceContext', state: 'WizardState' = None):
    """Show comprehensive per-device dashboard with physical/sub-interface correlation.
    
    Displays:
    - Physical interfaces and their operational status (UP/DOWN)
    - Sub-interfaces derived from each physical parent
    - Summary of all hierarchies per device
    - Pending configuration changes
    
    Args:
        multi_ctx: Multi-device context with configs
        state: Optional wizard state for pending changes
    """
    from rich.table import Table
    from rich.panel import Panel
    from rich.columns import Columns
    from pathlib import Path
    import json
    
    console.print("\n[bold cyan]{'═' * 80}[/bold cyan]")
    console.print("[bold cyan]📊 MULTI-DEVICE DASHBOARD - Physical/Sub-Interface Correlation[/bold cyan]")
    console.print(f"[bold cyan]{'═' * 80}[/bold cyan]")
    
    for dev in multi_ctx.devices:
        h = dev.hostname
        dev_config = multi_ctx.running_configs.get(h, multi_ctx.configs.get(h, ""))
        
        # Load operational data if available
        op_data = {}
        try:
            ops_path = Path(f"db/configs/{h}/operational.json")
            if ops_path.exists():
                with open(ops_path, 'r') as f:
                    op_data = json.load(f)
        except:
            pass
        
        console.print(f"\n[bold yellow]{'─' * 40}[/bold yellow]")
        console.print(f"[bold white]📱 {h}[/bold white]")
        console.print(f"[bold yellow]{'─' * 40}[/bold yellow]")
        
        # === SYSTEM INFO ===
        system_type = op_data.get('system_type', 'Unknown')
        dnos_version = op_data.get('dnos_version', 'Unknown')
        mgmt_ip = op_data.get('mgmt_ip', dev.host if hasattr(dev, 'host') else 'Unknown')
        uptime = op_data.get('system_uptime', 'Unknown')
        
        name_match = re.search(r'^\s+name\s+(\S+)', dev_config, re.MULTILINE)
        profile_match = re.search(r'^\s+profile\s+(\S+)', dev_config, re.MULTILINE)
        
        console.print(f"  [cyan]System:[/cyan] {name_match.group(1) if name_match else 'N/A'} | {profile_match.group(1) if profile_match else 'N/A'}")
        console.print(f"  [cyan]Type:[/cyan] {system_type} | [cyan]IP:[/cyan] {mgmt_ip}")
        if uptime != 'Unknown':
            console.print(f"  [cyan]Uptime:[/cyan] {uptime}")
        
        # === PHYSICAL INTERFACES & SUB-INTERFACES ===
        console.print(f"\n  [bold]Physical Interfaces & Sub-Interfaces:[/bold]")
        
        # Parse all interfaces from config
        all_ifaces = _get_all_interfaces_from_config(dev_config) if dev_config else []
        categories = categorize_interfaces_by_type(all_ifaces)
        
        # Get physical parents and their sub-interfaces
        physical_parents = categories.get('physical', [])
        physical_subifs = categories.get('physical_subif', [])
        bundle_parents = categories.get('bundle', [])
        bundle_subifs = categories.get('bundle_subif', [])
        pwhe_parents = categories.get('pwhe', [])
        pwhe_subifs = categories.get('pwhe_subif', [])
        
        # Get WAN interfaces (MPLS-enabled)
        wan_interfaces = set(get_mpls_enabled_interfaces(dev_config)) if dev_config else set()
        
        # Create interface table
        iface_table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
        iface_table.add_column("Parent", style="cyan", width=20)
        iface_table.add_column("Type", width=10)
        iface_table.add_column("WAN", width=5, justify="center")
        iface_table.add_column("Sub-ifs", justify="right", width=8)
        iface_table.add_column("Examples", style="dim", width=30)
        
        # Physical interfaces with sub-interface counts
        for parent in sorted(physical_parents)[:15]:  # Limit display
            is_wan = "✓" if parent in wan_interfaces else ""
            # Count sub-interfaces for this parent
            subifs = [s for s in physical_subifs if s.startswith(f"{parent}.")]
            subif_count = len(subifs)
            examples = ", ".join(subifs[:3]) + ("..." if len(subifs) > 3 else "") if subifs else "-"
            iface_table.add_row(parent, "Physical", is_wan, str(subif_count) if subif_count else "-", examples)
        
        if len(physical_parents) > 15:
            iface_table.add_row(f"... +{len(physical_parents) - 15} more", "", "", "", "")
        
        # Bundle interfaces
        for parent in sorted(bundle_parents):
            is_wan = "✓" if parent in wan_interfaces else ""
            subifs = [s for s in bundle_subifs if s.startswith(f"{parent}.")]
            subif_count = len(subifs)
            # Also get bundle members
            members = get_bundle_members(parent, dev_config)
            member_info = f"members: {len(members)}" if members else ""
            examples = ", ".join(subifs[:2]) + ("..." if len(subifs) > 2 else "") if subifs else member_info
            iface_table.add_row(parent, "Bundle", is_wan, str(subif_count) if subif_count else "-", examples)
        
        # PWHE interfaces
        for parent in sorted(pwhe_parents)[:5]:
            subifs = [s for s in pwhe_subifs if s.startswith(f"{parent}.")]
            subif_count = len(subifs)
            examples = ", ".join(subifs[:3]) + ("..." if len(subifs) > 3 else "") if subifs else "-"
            iface_table.add_row(parent, "PWHE", "", str(subif_count) if subif_count else "-", examples)
        
        if len(pwhe_parents) > 5:
            iface_table.add_row(f"... +{len(pwhe_parents) - 5} more PWHE", "", "", "", "")
        
        console.print(iface_table)
        
        # === INTERFACE TOTALS ===
        total_physical = len(physical_parents) + len(physical_subifs)
        total_bundle = len(bundle_parents) + len(bundle_subifs)
        total_pwhe = len(pwhe_parents) + len(pwhe_subifs)
        total_wan = len(wan_interfaces)
        
        console.print(f"\n  [bold]Totals:[/bold] {len(all_ifaces):,} interfaces")
        console.print(f"    Physical: {len(physical_parents)} parents + {len(physical_subifs):,} sub-ifs = {total_physical:,}")
        console.print(f"    Bundle:   {len(bundle_parents)} parents + {len(bundle_subifs):,} sub-ifs = {total_bundle:,}")
        console.print(f"    PWHE:     {len(pwhe_parents)} parents + {len(pwhe_subifs):,} sub-ifs = {total_pwhe:,}")
        console.print(f"    WAN (MPLS): {total_wan} interfaces")
        
        # === PROTOCOLS ===
        console.print(f"\n  [bold]Protocols:[/bold]")
        
        # BGP
        bgp_match = re.search(r'^  bgp\s+(\d+)', dev_config, re.MULTILINE)
        if bgp_match:
            peer_count = len(re.findall(r'\n\s{4,}neighbor\s+\d+\.\d+\.\d+\.\d+', dev_config))
            console.print(f"    [green]✓[/green] BGP AS {bgp_match.group(1)}, {peer_count} peers")
        else:
            console.print(f"    [dim]○ BGP: Not configured[/dim]")
        
        # IGP
        if re.search(r'^  isis\s*$', dev_config, re.MULTILINE):
            instance_match = re.search(r'^  isis\s*\n\s+instance\s+(\S+)', dev_config, re.MULTILINE)
            instance = instance_match.group(1) if instance_match else ""
            console.print(f"    [green]✓[/green] ISIS {instance}")
        elif re.search(r'^  ospf\s*$', dev_config, re.MULTILINE):
            console.print(f"    [green]✓[/green] OSPF")
        else:
            console.print(f"    [dim]○ IGP: Not configured[/dim]")
        
        # LDP/SR
        if re.search(r'^  ldp\s*$', dev_config, re.MULTILINE):
            console.print(f"    [green]✓[/green] LDP")
        if re.search(r'segment-routing', dev_config, re.IGNORECASE):
            console.print(f"    [green]✓[/green] Segment Routing")
        
        # === SERVICES ===
        fxc_count = len(re.findall(r'evpn-vpws-fxc\s+instance', dev_config))
        vpls_count = len(re.findall(r'evpn-vpls\s+instance', dev_config))
        vrf_count = len(re.findall(r'^\s+vrf\s+', dev_config, re.MULTILINE))
        
        console.print(f"\n  [bold]Services:[/bold]")
        if fxc_count or vpls_count or vrf_count:
            if fxc_count:
                console.print(f"    [green]✓[/green] EVPN-VPWS-FXC: {fxc_count}")
            if vpls_count:
                console.print(f"    [green]✓[/green] EVPN-VPLS: {vpls_count}")
            if vrf_count:
                console.print(f"    [green]✓[/green] VRF: {vrf_count}")
        else:
            console.print(f"    [dim]○ No L2/L3VPN services configured[/dim]")
        
        # === MULTIHOMING ===
        esi_count = dev_config.count('\n      esi ')
        if esi_count:
            console.print(f"\n  [bold]Multihoming:[/bold] {esi_count} ESI interfaces")
        
        # === FLOWSPEC VPN SCALE (Epic SW-182545) ===
        try:
            import json
            limits_path = Path("limits.json")
            if limits_path.exists():
                with open(limits_path, 'r') as f:
                    limits_data = json.load(f)
                fs_scale = get_flowspec_vpn_scale(dev_config, limits_data)
                
                if fs_scale['interfaces']['current'] > 0 or fs_scale['vrfs_with_flowspec']['current'] > 0:
                    console.print(f"\n  [bold magenta]Flowspec VPN:[/bold magenta]")
                    console.print(f"    Interfaces w/flowspec: {fs_scale['interfaces']['current']}/{fs_scale['interfaces']['max']} ({fs_scale['interfaces']['percent']:.0f}%)")
                    console.print(f"    VRFs w/flowspec AFI:   {fs_scale['vrfs_with_flowspec']['current']}/{fs_scale['vrfs_with_flowspec']['max']} ({fs_scale['vrfs_with_flowspec']['percent']:.0f}%)")
                    if fs_scale['bgp_flowspec_vpn_neighbors']['current'] > 0:
                        console.print(f"    BGP FS-VPN neighbors:  {fs_scale['bgp_flowspec_vpn_neighbors']['current']}")
                    
                    # Show warnings if any
                    for warning in fs_scale['warnings']:
                        console.print(f"    [yellow]{warning}[/yellow]")
        except Exception:
            pass  # Silently skip flowspec scale check if limits.json not available
    
    # === SUMMARY TABLE ===
    console.print(f"\n[bold cyan]{'═' * 80}[/bold cyan]")
    console.print("[bold]Cross-Device Comparison:[/bold]")
    
    summary_table = Table(box=box.ROUNDED, show_header=True)
    summary_table.add_column("Device", style="cyan", width=20)
    summary_table.add_column("Physical", justify="right", width=10)
    summary_table.add_column("Sub-ifs", justify="right", width=10)
    summary_table.add_column("Bundles", justify="right", width=10)
    summary_table.add_column("WAN", justify="right", width=8)
    summary_table.add_column("BGP", justify="center", width=12)
    summary_table.add_column("IGP", justify="center", width=10)
    summary_table.add_column("Services", justify="right", width=10)
    
    for dev in multi_ctx.devices:
        h = dev.hostname
        dev_config = multi_ctx.running_configs.get(h, multi_ctx.configs.get(h, ""))
        
        all_ifaces = _get_all_interfaces_from_config(dev_config) if dev_config else []
        categories = categorize_interfaces_by_type(all_ifaces)
        
        physical = len(categories.get('physical', []))
        subifs = len(categories.get('physical_subif', [])) + len(categories.get('bundle_subif', [])) + len(categories.get('pwhe_subif', []))
        bundles = len(categories.get('bundle', []))
        wan = len(get_mpls_enabled_interfaces(dev_config)) if dev_config else 0
        
        bgp_match = re.search(r'^  bgp\s+(\d+)', dev_config, re.MULTILINE)
        bgp_info = f"AS {bgp_match.group(1)}" if bgp_match else "[dim]-[/dim]"
        
        igp_info = "[dim]-[/dim]"
        if re.search(r'^  isis\s*$', dev_config, re.MULTILINE):
            igp_info = "ISIS"
        elif re.search(r'^  ospf\s*$', dev_config, re.MULTILINE):
            igp_info = "OSPF"
        
        svc_count = len(re.findall(r'evpn-vpws-fxc\s+instance', dev_config)) + \
                   len(re.findall(r'evpn-vpls\s+instance', dev_config))
        
        summary_table.add_row(
            h[:18] + "…" if len(h) > 18 else h,
            str(physical),
            f"{subifs:,}",
            str(bundles),
            str(wan),
            bgp_info,
            igp_info,
            str(svc_count) if svc_count else "[dim]-[/dim]"
        )
    
    console.print(summary_table)
    
    console.print(f"\n[dim]Press Enter to continue...[/dim]")
    input()


# === Navigation Helpers ===
# BackException and TopException are defined later in the file

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


# === Helper Functions ===

def ip_to_isis_net(ip_address: str, area_id: str = "49.0001") -> str:
    """Convert an IPv4 address to ISIS NET address format.
    
    Example: 4.4.4.4 -> 49.0001.0004.0004.0004.00
    
    Format: <area>.<oct1_oct2>.<oct2_oct3>.<oct3_oct4>.00
    where each octet is padded to 4 digits and grouped as 2.2.2
    
    Args:
        ip_address: IPv4 address (e.g., "4.4.4.4" or "4.4.4.4/32")
        area_id: Area prefix (default: "49.0001")
        
    Returns:
        ISIS NET address (e.g., "49.0001.0004.0004.0004.00")
    """
    # Strip CIDR if present
    ip = ip_address.split('/')[0]
    octets = ip.split('.')
    
    if len(octets) != 4:
        return f"{area_id}.0000.0000.0001.00"  # Fallback
    
    # Pad each octet to 4 digits and group
    # Format: AAAA.BBBB.CCCC -> A.AAA.B.BBB.C.CCC (but actually 2+2.2+2.2+2)
    # Each pair of octets forms a group
    padded = [f"{int(o):04d}" for o in octets]
    
    # ISIS NET format: area.xxxx.xxxx.xxxx.00
    # where xxxx is formed from groups of octet digits
    # Common format: 49.0001.OOOO.OOOO.OOOO.00 where O is octet value
    # Example: 4.4.4.4 -> each octet 4 -> padded 0004 -> 49.0001.0004.0004.0004.00
    
    return f"{area_id}.{padded[0]}.{padded[1]}.{padded[2]}.00"


def calculate_next_ip(base_ip: str, index: int, mode: str, prefix_len: int, 
                      parent_idx: int = 0, subif_within_parent: int = 0,
                      custom_step: int = None) -> str:
    """Calculate the next IP address based on stepping mode.
    
    Args:
        base_ip: Starting IP address (e.g., "10.0.0.1")
        index: Global sub-interface index (0-based)
        mode: Stepping mode - "per_subif", "per_parent", or "unique_subnet"
        prefix_len: Prefix length (e.g., 30 for /30)
        parent_idx: Parent interface index (for per_parent mode)
        subif_within_parent: Sub-interface index within parent
        custom_step: Custom step value (overrides auto-calculated step for unique_subnet)
        
    Returns:
        Calculated IP address as string
    """
    import ipaddress
    
    try:
        # Parse base IP
        if '/' in base_ip:
            base_ip = base_ip.split('/')[0]
        
        # Detect IPv4 vs IPv6
        if ':' in base_ip:
            # IPv6
            ip_int = int(ipaddress.IPv6Address(base_ip))
            is_v6 = True
        else:
            # IPv4
            ip_int = int(ipaddress.IPv4Address(base_ip))
            is_v6 = False
        
        if mode == "per_subif":
            # Simple increment per sub-interface
            step = custom_step if custom_step is not None else 1
            new_ip_int = ip_int + (index * step)
            
        elif mode == "per_parent":
            # Increment 3rd octet per parent, 4th octet for sub-if
            # Example: 10.0.1.1, 10.0.1.2, ... 10.0.2.1, 10.0.2.2, ...
            if is_v6:
                # For IPv6: increment per parent in higher bits
                new_ip_int = ip_int + (parent_idx * 256) + subif_within_parent
            else:
                # For IPv4: parent changes 3rd octet, subif changes 4th
                base_octets = [
                    (ip_int >> 24) & 0xFF,
                    (ip_int >> 16) & 0xFF,
                    (ip_int >> 8) & 0xFF,
                    ip_int & 0xFF
                ]
                base_octets[2] = (base_octets[2] + parent_idx) % 256
                base_octets[3] = (base_octets[3] + subif_within_parent) % 256
                new_ip_int = (base_octets[0] << 24) + (base_octets[1] << 16) + \
                             (base_octets[2] << 8) + base_octets[3]
                
        elif mode == "unique_subnet":
            # Each sub-interface gets unique subnet
            # Use custom_step if provided, otherwise calculate from prefix
            if custom_step is not None:
                step = custom_step
            elif is_v6:
                step = 2 ** (128 - prefix_len)
            else:
                step = 2 ** (32 - prefix_len)
            new_ip_int = ip_int + (index * step)
            
        else:
            # Default: per_subif
            step = custom_step if custom_step is not None else 1
            new_ip_int = ip_int + (index * step)
        
        # Convert back to IP string
        if is_v6:
            return str(ipaddress.IPv6Address(new_ip_int))
        else:
            return str(ipaddress.IPv4Address(new_ip_int))
            
    except Exception:
        # Fallback: return base IP
        return base_ip


def get_interfaces_in_services(config_text: str) -> Dict[str, List[str]]:
    """Extract interfaces already attached to services from config.
    
    Args:
        config_text: Device configuration text
        
    Returns:
        Dictionary mapping service type to list of attached interfaces:
        {
            'fxc': ['ph1.1', 'ph1.2', ...],
            'evpn-vpws': ['ph2.1', ...],
            'bridge-domain': ['ge400-0/0/1.100', ...],
            'evpn-vpls': [...],
            'vrf': [...]
        }
    """
    import re
    
    result = {
        'fxc': [],
        'evpn-vpws': [],
        'bridge-domain': [],
        'evpn-vpls': [],
        'vrf': []
    }
    
    if not config_text:
        return result
    
    # FXC / EVPN-VPWS-FXC interfaces
    # Pattern: evpn-vpws-fxc ... instance ... interface <name>
    fxc_section = re.search(r'evpn-vpws-fxc\s*\n(.*?)(?=\n\s*!\s*\n\s*!|\Z)', config_text, re.DOTALL)
    if fxc_section:
        fxc_ifaces = re.findall(r'interface\s+(\S+)', fxc_section.group(1))
        result['fxc'].extend(fxc_ifaces)
    
    # EVPN-VPWS interfaces
    vpws_section = re.search(r'evpn-vpws\s*\n(?!.*fxc)(.*?)(?=\n\s*!\s*\n\s*!|\Z)', config_text, re.DOTALL)
    if vpws_section:
        vpws_ifaces = re.findall(r'interface\s+(\S+)', vpws_section.group(1))
        result['evpn-vpws'].extend(vpws_ifaces)
    
    # Bridge Domain interfaces
    bd_section = re.search(r'bridge-domain\s*\n(.*?)(?=\n\s*!\s*\n\s*!|\Z)', config_text, re.DOTALL)
    if bd_section:
        bd_ifaces = re.findall(r'interface\s+(\S+)', bd_section.group(1))
        result['bridge-domain'].extend(bd_ifaces)
    
    # EVPN-VPLS interfaces
    vpls_section = re.search(r'evpn-vpls\s*\n(.*?)(?=\n\s*!\s*\n\s*!|\Z)', config_text, re.DOTALL)
    if vpls_section:
        vpls_ifaces = re.findall(r'interface\s+(\S+)', vpls_section.group(1))
        result['evpn-vpls'].extend(vpls_ifaces)
    
    # VRF interfaces
    vrf_section = re.search(r'\n\s+vrf\s+\S+\s*\n(.*?)(?=\n\s*!\s*\n\s*!|\Z)', config_text, re.DOTALL)
    if vrf_section:
        vrf_ifaces = re.findall(r'interface\s+(\S+)', vrf_section.group(1))
        result['vrf'].extend(vrf_ifaces)
    
    # Remove duplicates
    for key in result:
        result[key] = list(set(result[key]))
    
    return result


def get_all_allocated_interfaces(config_text: str) -> Set[str]:
    """Get all interfaces already allocated to any service.
    
    Args:
        config_text: Device configuration text
        
    Returns:
        Set of interface names that are already attached to services
    """
    service_ifaces = get_interfaces_in_services(config_text)
    allocated = set()
    for ifaces in service_ifaces.values():
        allocated.update(ifaces)
    return allocated


def get_lo0_ip_from_config(config_text: str) -> Optional[str]:
    """Extract lo0 IPv4 address from configuration text.
    
    Args:
        config_text: Device configuration text
        
    Returns:
        IPv4 address or None if not found
    """
    import re
    
    # Look for lo0 interface with ipv4-address
    lo0_pattern = re.compile(
        r'^\s*lo0\s*$.*?ipv4-address\s+(\d+\.\d+\.\d+\.\d+/?\d*)',
        re.MULTILINE | re.DOTALL
    )
    
    match = lo0_pattern.search(config_text)
    if match:
        return match.group(1)
    
    # Alternative pattern - simpler search
    lines = config_text.split('\n')
    in_lo0 = False
    for line in lines:
        stripped = line.strip()
        if stripped == 'lo0':
            in_lo0 = True
        elif in_lo0 and stripped.startswith('ipv4-address'):
            parts = stripped.split()
            if len(parts) >= 2:
                return parts[1]
        elif in_lo0 and stripped == '!' or (in_lo0 and stripped.startswith('lo') and stripped != 'lo0'):
            in_lo0 = False
    
    return None


def get_as_number_from_config(config_text: str) -> Optional[int]:
    """Extract BGP AS number from configuration text.
    
    Args:
        config_text: Device configuration text
        
    Returns:
        AS number as int or None if not found
    """
    import re
    
    # Look for "bgp <AS>" pattern
    bgp_pattern = re.compile(r'^\s*bgp\s+(\d+)\s*$', re.MULTILINE)
    match = bgp_pattern.search(config_text)
    if match:
        return int(match.group(1))
    
    return None


def get_router_id_from_config(config_text: str) -> Optional[str]:
    """Extract BGP router-id from configuration text.
    
    Args:
        config_text: Device configuration text
        
    Returns:
        Router ID or None if not found
    """
    import re
    
    # Look for "router-id X.X.X.X" pattern in BGP context
    rid_pattern = re.compile(r'router-id\s+(\d+\.\d+\.\d+\.\d+)', re.MULTILINE)
    match = rid_pattern.search(config_text)
    if match:
        return match.group(1)
    
    return None


def _calculate_scale_info(hierarchy_name: str, config_text: str, state: 'WizardState') -> Dict[str, Any]:
    """Calculate scale information for a hierarchy.
    
    Args:
        hierarchy_name: Name of the hierarchy (interfaces, services, bgp, igp)
        config_text: The configuration text
        state: Wizard state with created resources
        
    Returns:
        Dict with 'count' and 'type' for display
    """
    import re
    
    if not config_text:
        return {}
    
    if hierarchy_name == "system":
        # Count system elements
        user_count = len(re.findall(r'^\s+user\s+(\S+)', config_text, re.MULTILINE))
        name_match = re.search(r'^\s+name\s+(\S+)', config_text, re.MULTILINE)
        profile_match = re.search(r'^\s+profile\s+(\S+)', config_text, re.MULTILINE)
        
        details = []
        if name_match:
            details.append(name_match.group(1))
        if profile_match:
            details.append(profile_match.group(1))
        if user_count:
            details.append(f"{user_count} users")
        
        return {'count': user_count, 'type': ', '.join(details) if details else 'system config'}
    
    if hierarchy_name == "interfaces":
        # Count interface entries
        interface_matches = re.findall(r'^\s{2}(\S+)\s*$', config_text, re.MULTILINE)
        parent_count = 0
        subif_count = 0
        
        for iface in interface_matches:
            if iface == '!':
                continue
            if '.' in iface:
                subif_count += 1
            elif iface.startswith(('ph', 'ge', 'et', 'bundle', 'irb', 'lo')):
                parent_count += 1
        
        if subif_count > 0:
            # Determine interface type
            iface_type = "sub-ifs"
            if any('ph' in i for i in interface_matches):
                iface_type = "ph sub-ifs"
            return {'count': subif_count, 'type': iface_type}
        elif parent_count > 0:
            return {'count': parent_count, 'type': 'interfaces'}
        
    elif hierarchy_name == "services":
        # Count service instances
        instance_matches = re.findall(r'^\s+instance\s+(\S+)', config_text, re.MULTILINE)
        count = len(instance_matches)
        
        # Determine service type
        svc_type = "services"
        if 'evpn-vpws-fxc' in config_text:
            svc_type = "FXC services"
        elif 'vrf' in config_text.lower():
            svc_type = "VRF instances"
        elif 'evpn' in config_text.lower():
            svc_type = "EVPN instances"
        
        return {'count': count, 'type': svc_type}
    
    elif hierarchy_name == "bgp":
        # Count BGP neighbors
        neighbor_matches = re.findall(r'^\s+neighbor\s+(\S+)', config_text, re.MULTILINE)
        count = len(neighbor_matches)
        
        # Detect iBGP vs eBGP
        as_matches = re.findall(r'bgp\s+(\d+)', config_text)
        remote_as_matches = re.findall(r'remote-as\s+(\d+)', config_text)
        
        peer_type = "peers"
        if as_matches and remote_as_matches:
            local_as = as_matches[0] if as_matches else None
            if local_as and all(r == local_as for r in remote_as_matches):
                peer_type = "iBGP peers"
            elif remote_as_matches:
                peer_type = "eBGP peers"
        
        return {'count': count, 'type': peer_type}
    
    elif hierarchy_name == "igp":
        # Count ISIS/OSPF interfaces
        interface_matches = re.findall(r'^\s+interface\s+(\S+)', config_text, re.MULTILINE)
        count = len(interface_matches)
        
        igp_type = "interfaces"
        if 'isis' in config_text.lower():
            igp_type = "ISIS interfaces"
        elif 'ospf' in config_text.lower():
            igp_type = "OSPF interfaces"
        
        return {'count': count, 'type': igp_type}
    
    return {}


def get_mpls_enabled_interfaces(config_text: str, include_subinterfaces: bool = True) -> List[str]:
    """Extract all interfaces with 'mpls enabled' from config.
    
    These are typically WAN/core interfaces that should participate in IGP.
    In DNOS, MPLS is enabled with "mpls enabled" on a single line under the interface.
    
    Args:
        config_text: Device configuration text
        include_subinterfaces: Whether to include sub-interfaces (default True for ISIS)
        
    Returns:
        List of interface names with MPLS enabled
    """
    mpls_interfaces = []
    lines = config_text.split('\n')
    
    current_interface = None
    in_interfaces_block = False
    has_mpls_enabled = False
    
    for line in lines:
        stripped = line.strip()
        raw_line = line
        
        # Track if we're in the interfaces block
        if stripped == 'interfaces':
            in_interfaces_block = True
            continue
        
        if not in_interfaces_block:
            continue
        
        # Calculate current indentation (spaces)
        current_indent = len(raw_line) - len(raw_line.lstrip())
        
        # End of interfaces block (top-level !)
        if stripped == '!' and current_indent == 0:
            # Save current interface if it has MPLS
            if current_interface and has_mpls_enabled:
                mpls_interfaces.append(current_interface)
            in_interfaces_block = False
            current_interface = None
            has_mpls_enabled = False
            continue
        
        # Check for interface definition (indented 2 spaces under 'interfaces')
        # Interface names start with: ge, xe, et, bundle, lo, ph, irb, etc.
        if current_indent == 2 and stripped and not stripped.startswith('!'):
            # If we were tracking an interface, save it if it had MPLS
            if current_interface and has_mpls_enabled:
                mpls_interfaces.append(current_interface)
            
            # Start tracking new interface
            current_interface = stripped
            has_mpls_enabled = False
            continue
        
        # Check for "mpls enabled" under current interface (indented 4 spaces)
        if current_interface and current_indent == 4:
            # DNOS uses "mpls enabled" as a single statement
            if stripped == 'mpls enabled':
                has_mpls_enabled = True
        
        # End of current interface block (! at indent 2)
        if current_interface and stripped == '!' and current_indent == 2:
            if has_mpls_enabled:
                mpls_interfaces.append(current_interface)
            current_interface = None
            has_mpls_enabled = False
    
    # Don't forget the last interface if we ended without seeing !
    if current_interface and has_mpls_enabled:
        mpls_interfaces.append(current_interface)
    
    # Optionally filter to only parent interfaces
    if not include_subinterfaces:
        mpls_interfaces = [iface for iface in mpls_interfaces if '.' not in iface]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_interfaces = []
    for iface in mpls_interfaces:
        if iface not in seen:
            seen.add(iface)
            unique_interfaces.append(iface)
    
    return unique_interfaces


def get_flowspec_vpn_scale(config_text: str, limits: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze Flowspec VPN scale from configuration and compare against limits.
    
    Per Epic SW-182545, tracks:
    - Flowspec-enabled interfaces
    - VRFs with flowspec AFI
    - BGP neighbors with flowspec-vpn SAFI (134)
    - Local flowspec policies and match-classes
    
    Args:
        config_text: Device configuration text
        limits: Platform limits from limits.json
        
    Returns:
        Dict with current scale, limits, and warnings
    """
    flowspec_limits = limits.get('dnos_platform_limits', {}).get('flowspec', {})
    
    # Count flowspec-enabled interfaces
    fs_interfaces = get_flowspec_enabled_interfaces(config_text)
    
    # Count VRFs with flowspec
    vrf_flowspec_pattern = re.compile(
        r'instance\s+(\S+).*?address-family\s+ipv[46]-flowspec',
        re.DOTALL | re.MULTILINE
    )
    vrfs_with_flowspec = vrf_flowspec_pattern.findall(config_text)
    
    # Count BGP neighbors with flowspec-vpn (SAFI 134)
    bgp_fs_vpn_pattern = re.compile(
        r'neighbor\s+(\S+).*?address-family\s+ipv[46]-flowspec-vpn',
        re.DOTALL | re.MULTILINE
    )
    bgp_fs_vpn_neighbors = bgp_fs_vpn_pattern.findall(config_text)
    
    # Count local policies
    local_policies = re.findall(r'flowspec-local-policies.*?policy\s+(\S+)', config_text, re.DOTALL)
    
    # Count match-classes
    match_classes = re.findall(r'match-class\s+(\S+)', config_text)
    
    # Get limits
    max_interfaces = flowspec_limits.get('max_flowspec_interfaces', 1000)
    max_vrfs = flowspec_limits.get('max_vrfs_with_flowspec', 512)
    max_policies = flowspec_limits.get('max_local_policies', 40)
    max_match_classes = flowspec_limits.get('max_match_classes', 12000)
    
    # Calculate percentages and warnings
    warnings = []
    
    iface_pct = (len(fs_interfaces) / max_interfaces * 100) if max_interfaces > 0 else 0
    vrf_pct = (len(vrfs_with_flowspec) / max_vrfs * 100) if max_vrfs > 0 else 0
    policy_pct = (len(local_policies) / max_policies * 100) if max_policies > 0 else 0
    mc_pct = (len(match_classes) / max_match_classes * 100) if max_match_classes > 0 else 0
    
    if iface_pct > 80:
        warnings.append(f"⚠️ Flowspec interfaces at {iface_pct:.0f}% ({len(fs_interfaces)}/{max_interfaces})")
    if vrf_pct > 80:
        warnings.append(f"⚠️ VRFs with flowspec at {vrf_pct:.0f}% ({len(vrfs_with_flowspec)}/{max_vrfs})")
    if policy_pct > 80:
        warnings.append(f"⚠️ Local policies at {policy_pct:.0f}% ({len(local_policies)}/{max_policies})")
    if mc_pct > 80:
        warnings.append(f"⚠️ Match-classes at {mc_pct:.0f}% ({len(match_classes)}/{max_match_classes})")
    
    return {
        'interfaces': {
            'current': len(fs_interfaces),
            'max': max_interfaces,
            'percent': iface_pct,
            'list': fs_interfaces[:10]  # First 10 for display
        },
        'vrfs_with_flowspec': {
            'current': len(vrfs_with_flowspec),
            'max': max_vrfs,
            'percent': vrf_pct,
            'list': vrfs_with_flowspec[:5]
        },
        'bgp_flowspec_vpn_neighbors': {
            'current': len(bgp_fs_vpn_neighbors),
            'list': bgp_fs_vpn_neighbors[:5]
        },
        'local_policies': {
            'current': len(local_policies),
            'max': max_policies,
            'percent': policy_pct
        },
        'match_classes': {
            'current': len(match_classes),
            'max': max_match_classes,
            'percent': mc_pct
        },
        'warnings': warnings,
        'within_limits': len(warnings) == 0
    }


def get_flowspec_enabled_interfaces(config_text: str, include_subinterfaces: bool = True) -> List[str]:
    """Extract all interfaces with 'flowspec enabled' from config.
    
    These are interfaces where BGP Flowspec (DDoS filtering) rules will be applied.
    In DNOS, Flowspec is enabled with "flowspec enabled" on interfaces for ingress filtering.
    
    Supported interface types: Physical, Physical VLAN, Bundle, Bundle VLAN, IRB
    
    Args:
        config_text: Device configuration text
        include_subinterfaces: Whether to include sub-interfaces (default True)
        
    Returns:
        List of flowspec-enabled interface names
    """
    flowspec_interfaces = []
    lines = config_text.split('\n')
    
    current_interface = None
    in_interfaces_block = False
    has_flowspec_enabled = False
    
    for line in lines:
        stripped = line.strip()
        raw_line = line
        
        # Track if we're in the interfaces block
        if stripped == 'interfaces':
            in_interfaces_block = True
            continue
        
        # Exit interfaces block at top-level !
        if stripped == '!' and in_interfaces_block and (not raw_line.startswith(' ') or raw_line.startswith('!')):
            in_interfaces_block = False
            continue
        
        if not in_interfaces_block:
            continue
        
        # Calculate indentation
        current_indent = len(raw_line) - len(raw_line.lstrip())
        
        # Interface definition at 2-space indent - DNOS uses flat interface names
        if current_indent == 2 and stripped and stripped != '!' and not stripped.startswith('!'):
            # Save previous interface if it had flowspec
            if current_interface and has_flowspec_enabled:
                flowspec_interfaces.append(current_interface)
            
            # Valid interface patterns for flowspec: ge*, xe*, et*, hun*, bundle-*, irb*
            if re.match(r'^(ge|xe|et|hun)\d+', stripped) or \
               stripped.lower().startswith('bundle-') or \
               stripped.lower().startswith('irb'):
                current_interface = stripped
                has_flowspec_enabled = False
            else:
                current_interface = None
                has_flowspec_enabled = False
            continue
        
        # Check for "flowspec enabled" under current interface (indented 4 spaces)
        if current_interface and current_indent == 4:
            # DNOS uses "flowspec enabled" as a single statement
            if stripped == 'flowspec enabled':
                has_flowspec_enabled = True
        
        # End of current interface block (! at indent 2)
        if current_interface and stripped == '!' and current_indent == 2:
            if has_flowspec_enabled:
                flowspec_interfaces.append(current_interface)
            current_interface = None
            has_flowspec_enabled = False
    
    # Don't forget the last interface if we ended without seeing !
    if current_interface and has_flowspec_enabled:
        flowspec_interfaces.append(current_interface)
    
    # Optionally filter to only parent interfaces
    if not include_subinterfaces:
        flowspec_interfaces = [iface for iface in flowspec_interfaces if '.' not in iface]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_interfaces = []
    for iface in flowspec_interfaces:
        if iface not in seen:
            seen.add(iface)
            unique_interfaces.append(iface)
    
    return unique_interfaces


def get_active_interfaces_from_device(device: 'Device', config_text: str = None, 
                                       progress_callback: callable = None) -> Tuple[List[str], Dict[str, Any]]:
    """
    Get operationally UP interfaces from a device via SSH.
    
    This runs 'show interfaces brief' and parses the output to find interfaces
    that are operationally UP. Bundle members are excluded if their parent bundle
    is UP (the bundle is suggested instead).
    
    Args:
        device: Device object with connection info
        config_text: Optional config text for bundle member detection
        progress_callback: Optional callback for progress updates
        
    Returns:
        Tuple of (list of active interface names, dict with stats)
    """
    import paramiko
    
    active_interfaces = []
    stats = {
        'physical_up': [],
        'bundle_up': [],
        'bundle_members': [],  # Members to exclude (their bundle is UP)
        'loopback_up': [],
        'pwhe_up': [],
        'irb_up': [],
        'total_up': 0,
        'total_configured': 0,
        'error': None
    }
    
    try:
        if progress_callback:
            progress_callback("Connecting to device...", 10)
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        addresses = device.get_connection_addresses() if hasattr(device, 'get_connection_addresses') else [device.ip]
        
        connected = False
        for address in addresses:
            try:
                client.connect(
                    hostname=address,
                    username=device.username,
                    password=device.get_password() if hasattr(device, 'get_password') else device.password,
                    timeout=30,
                    look_for_keys=False,
                    allow_agent=False
                )
                connected = True
                break
            except Exception:
                continue
        
        if not connected:
            stats['error'] = "Could not connect to device"
            return [], stats
        
        if progress_callback:
            progress_callback("Running show interfaces...", 30)
        
        # Run show interfaces (correct DNOS command - not 'brief')
        channel = client.invoke_shell()
        channel.settimeout(60)
        time.sleep(0.5)
        channel.recv(10000)  # Clear banner
        
        channel.send("show interfaces | no-more\n")
        time.sleep(3)
        
        output = ""
        while channel.recv_ready() or time.sleep(0.3) is None:
            if channel.recv_ready():
                output += channel.recv(65535).decode(errors='ignore')
            else:
                break
        
        channel.close()
        client.close()
        
        if progress_callback:
            progress_callback("Parsing interface state...", 60)
        
        # Parse the output
        # Format: | Interface | Admin | Operational | Speed/Type | MTU | Description |
        bundles_up = set()
        all_up_interfaces = []
        
        for line in output.split('\n'):
            line = line.strip()
            
            # Skip headers and separators
            if not line or line.startswith('+') or 'Interface' in line and 'Admin' in line:
                continue
            
            if line.startswith('|'):
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 3:
                    iface_name = parts[0].split()[0]  # Get interface name, strip (L2) etc
                    admin_state = parts[1].lower()
                    oper_state = parts[2].lower()
                    
                    stats['total_configured'] += 1
                    
                    is_up = 'up' in oper_state and 'not' not in oper_state
                    
                    if is_up:
                        stats['total_up'] += 1
                        all_up_interfaces.append(iface_name)
                        
                        # Categorize
                        if iface_name.startswith('bundle') and '.' not in iface_name:
                            stats['bundle_up'].append(iface_name)
                            bundles_up.add(iface_name)
                        elif iface_name.startswith(('ge', 'xe', 'et', 'hun')) and '.' not in iface_name:
                            stats['physical_up'].append(iface_name)
                        elif iface_name.startswith('lo'):
                            stats['loopback_up'].append(iface_name)
                        elif re.match(r'^ph\d+', iface_name):
                            stats['pwhe_up'].append(iface_name)
                        elif iface_name.startswith('irb'):
                            stats['irb_up'].append(iface_name)
        
        if progress_callback:
            progress_callback("Filtering bundle members...", 80)
        
        # Now filter out bundle members if their parent bundle is UP
        # A physical interface is a bundle member if it has 'bundle-id X' in config
        bundle_member_map = {}  # iface -> bundle
        
        if config_text and bundles_up:
            for bundle in bundles_up:
                members = get_bundle_members(bundle, config_text)
                for member in members:
                    bundle_member_map[member] = bundle
                    stats['bundle_members'].append(member)
        
        # Build final list: UP interfaces minus bundle members (replaced by their bundles)
        for iface in all_up_interfaces:
            # Skip internal/control interfaces
            if any(iface.startswith(p) for p in ('ctrl-', 'console-', 'ipmi-', 'mgmt-')):
                continue
            
            if iface in bundle_member_map:
                # This is a bundle member, the bundle is already in the list
                continue
            else:
                active_interfaces.append(iface)
        
        # Dedupe while preserving order
        seen = set()
        unique_active = []
        for iface in active_interfaces:
            if iface not in seen:
                seen.add(iface)
                unique_active.append(iface)
        
        if progress_callback:
            progress_callback("Complete", 100)
        
        return unique_active, stats
        
    except Exception as e:
        stats['error'] = str(e)
        return [], stats


def get_active_interfaces_multi(multi_ctx: 'MultiDeviceContext', 
                                 progress_callback: callable = None) -> Dict[str, Tuple[List[str], Dict]]:
    """
    Get active/UP interfaces from all devices in parallel.
    
    Args:
        multi_ctx: Multi-device context
        progress_callback: Optional progress callback
        
    Returns:
        Dict mapping hostname -> (active_interfaces, stats)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    
    results = {}
    progress_lock = threading.Lock()
    device_progress = {dev.hostname: {"status": "pending", "message": ""} for dev in multi_ctx.devices}
    
    def fetch_device_interfaces(device):
        hostname = device.hostname
        config_text = multi_ctx.configs.get(hostname, "")
        
        with progress_lock:
            device_progress[hostname]["status"] = "running"
            device_progress[hostname]["message"] = "Connecting..."
        
        def update_progress(msg, pct):
            with progress_lock:
                device_progress[hostname]["message"] = msg
        
        active, stats = get_active_interfaces_from_device(device, config_text, update_progress)
        
        with progress_lock:
            device_progress[hostname]["status"] = "success" if not stats.get('error') else "error"
            device_progress[hostname]["message"] = f"{len(active)} UP" if not stats.get('error') else stats.get('error', '')[:30]
        
        return hostname, active, stats
    
    console.print("\n[bold cyan]📡 Fetching interface state from all devices...[/bold cyan]")
    
    with ThreadPoolExecutor(max_workers=min(len(multi_ctx.devices), 4)) as executor:
        futures = {executor.submit(fetch_device_interfaces, dev): dev.hostname for dev in multi_ctx.devices}
        
        for future in as_completed(futures):
            hostname, active, stats = future.result()
            results[hostname] = (active, stats)
    
    return results


class BackException(Exception):
    """Exception to signal going back one step within a section."""
    pass


class TopException(Exception):
    """Exception to signal returning to the start of the wizard (all hierarchies)."""
    pass


class StepNavigator:
    """
    Helper class to implement step-based navigation within a configuration section.
    
    Usage:
        nav = StepNavigator()
        
        while not nav.done:
            try:
                if nav.step == 0:
                    # First prompt
                    name = prompt_with_nav("Enter name")
                    nav.set_value('name', name)
                    nav.next()
                elif nav.step == 1:
                    # Second prompt
                    count = prompt_with_nav("Enter count", is_int=True)
                    nav.set_value('count', count)
                    nav.next()
                elif nav.step == 2:
                    nav.finish()
            except BackException:
                nav.back()
            except TopException:
                raise  # Propagate to restart wizard
        
        # Access values
        name = nav.get('name')
        count = nav.get('count')
    """
    
    def __init__(self, total_steps: int = 100):
        self.step = 0
        self.max_step = 0
        self.total_steps = total_steps
        self.values = {}
        self.done = False
    
    def next(self):
        """Move to next step."""
        self.step += 1
        self.max_step = max(self.max_step, self.step)
    
    def back(self):
        """Go back one step. Returns False if already at step 0."""
        if self.step > 0:
            self.step -= 1
            console.print(f"[yellow]← Going back...[/yellow]")
            return True
        return False
    
    def finish(self):
        """Mark navigation as complete."""
        self.done = True
    
    def set_value(self, key: str, value: Any):
        """Store a value for later retrieval."""
        self.values[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a stored value."""
        return self.values.get(key, default)
    
    def has(self, key: str) -> bool:
        """Check if a value is stored."""
        return key in self.values
    
    def get_default(self, key: str, fallback: Any = None) -> Any:
        """Get stored value for use as a default (shows previous input when going back)."""
        return self.values.get(key, fallback)


def show_navigation_help():
    """Show navigation options available in the wizard."""
    console.print("\n[dim]Navigation: [B] Back to previous prompt | [T] Top (restart entire wizard)[/dim]")


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
        'physical': [],           # ge*, xe*, et*, hun* (parents only, no .N)
        'physical_subif': [],     # ge*.N, xe*.N, et*.N, hun*.N (sub-interfaces)
        'bundle': [],             # bundle* (parents only)
        'bundle_subif': [],       # bundle*.N (sub-interfaces)
        'pwhe': [],               # ph* (parents only)
        'pwhe_subif': [],         # ph*.N (sub-interfaces)
        'irb': [],                # irb*
        'loopback': [],           # lo*
        'ctrl': [],               # ctrl-*, console-* (control/console interfaces)
        'mgmt': [],               # mgmt*, ipmi-* (management/IPMI interfaces)
        'other': []
    }
    
    for iface in interfaces:
        # Check if it's a sub-interface (has .N suffix)
        is_subif = '.' in iface
        
        # Get base name (before . for sub-interfaces)
        base = iface.split('.')[0].lower()
        
        # DNOS Control interfaces (ctrl-*, console-*)
        if base.startswith('ctrl-') or base.startswith('ctrl_') or base.startswith('console-') or base.startswith('console_'):
            categories['ctrl'].append(iface)
        # DNOS Management interfaces (mgmt*, ipmi-*)
        elif base.startswith('mgmt') or base.startswith('ipmi-') or base.startswith('ipmi_'):
            categories['mgmt'].append(iface)
        elif base.startswith('ge') or base.startswith('xe') or base.startswith('et') or base.startswith('te') or base.startswith('hun'):
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
        
        # Check if this is an interface line (2-space indent under 'interfaces')
        if line.startswith('  ') and not line.startswith('    ') and stripped and stripped != '!':
            if not stripped.startswith('!') and not stripped.startswith('#'):
                in_interface = stripped
        elif line.startswith('    ') and in_interface:
            # Check for bundle-id
            bundle_id_match = re.match(rf'bundle-id\s+{bundle_num}\b', stripped)
            if bundle_id_match:
                members.append(in_interface)
        elif not line.startswith(' '):
            in_interface = None
    
    return members


def parse_number_selection(selection: str, items: List[Any], key: str = None) -> List[Any]:
    """Parse number selection like '1,3,5-8' into list of items.
    
    Supports:
    - Single numbers: '3' → [items[2]]
    - Comma-separated: '1,3,5' → [items[0], items[2], items[4]]
    - Ranges: '1-5' → [items[0], items[1], ..., items[4]]
    - Mixed: '1,3-5,8' → [items[0], items[2], items[3], items[4], items[7]]
    
    Args:
        selection: User input string like '1,3,5-8'
        items: List of items (can be dicts or any objects)
        key: If items are dicts, use this key to extract the value
             If None, return the items directly
    
    Returns:
        List of selected items (or values if key is provided)
        Duplicates are removed while preserving order
    """
    selected = []
    try:
        parts = selection.replace(' ', '').split(',')
        for part in parts:
            if '-' in part and not part.startswith('-'):
                # Handle range like '3-7'
                range_parts = part.split('-')
                if len(range_parts) == 2:
                    start, end = int(range_parts[0]), int(range_parts[1])
                    for i in range(start, end + 1):
                        if 1 <= i <= len(items):
                            item = items[i - 1]
                            if key and isinstance(item, dict):
                                selected.append(item[key])
                            else:
                                selected.append(item)
            else:
                # Handle single number
                i = int(part)
                if 1 <= i <= len(items):
                    item = items[i - 1]
                    if key and isinstance(item, dict):
                        selected.append(item[key])
                    else:
                        selected.append(item)
    except (ValueError, KeyError, IndexError):
        pass
    
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for item in selected:
        try:
            item_key = id(item) if not isinstance(item, (str, int, float, tuple)) else item
        except TypeError:
            item_key = id(item)
        if item_key not in seen:
            seen.add(item_key)
            unique.append(item)
    
    return unique


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


def print_wizard_banner():
    """Print the wizard banner with device status aligned inside the box."""
    # Banner width = 69 characters (matching the box)
    console.print()
    console.print("[bold cyan]╔═══════════════════════════════════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║[/bold cyan]              [bold white]SCALER Interactive Configuration Wizard[/bold white]              [bold cyan]║[/bold cyan]")
    console.print("[bold cyan]║[/bold cyan]                                                                   [bold cyan]║[/bold cyan]")
    console.print("[bold cyan]║[/bold cyan]     [dim]Step-by-step guide to create scaled DNOS configurations[/dim]      [bold cyan]║[/bold cyan]")
    console.print("[bold cyan]╚═══════════════════════════════════════════════════════════════════╝[/bold cyan]")


def _show_device_alerts() -> None:
    """Show any unacknowledged device integrity alerts from extraction monitoring.
    Offers context-aware actions: recovery for RECOVERY devices, IP change for connection issues."""
    alerts_file = Path("db/alerts.json")
    if not alerts_file.exists():
        return
    try:
        with open(alerts_file) as f:
            data = json.load(f)
        alerts = [a for a in data.get('alerts', []) if not a.get('acknowledged')]
        if not alerts:
            return
        
        # Filter out alerts for devices no longer in devices.json
        devices_file = Path("db/devices.json")
        known_hostnames = set()
        if devices_file.exists():
            try:
                with open(devices_file) as df:
                    known_hostnames = {d.get('hostname') for d in json.load(df).get('devices', [])}
            except Exception:
                pass
        
        if known_hostnames:
            stale = [a for a in alerts if a.get('device') not in known_hostnames]
            if stale:
                data['alerts'] = [a for a in data.get('alerts', []) if a.get('device') in known_hostnames]
                with open(alerts_file, 'w') as f:
                    json.dump(data, f, indent=2)
                alerts = [a for a in data['alerts'] if not a.get('acknowledged')]
        
        if not alerts:
            return
        
        # Deduplicate: if a device has recovery_mode alert, suppress stale_data/extraction_failed
        recovery_devices = {a['device'] for a in alerts if a.get('type') == 'recovery_mode'}
        if recovery_devices:
            alerts = [a for a in alerts if not (
                a.get('device') in recovery_devices and 
                a.get('type') in ('stale_data', 'extraction_failed')
            )]
            # Also clean up the file
            data['alerts'] = [a for a in data.get('alerts', []) if not (
                a.get('device') in recovery_devices and 
                a.get('type') in ('stale_data', 'extraction_failed')
            )]
            with open(alerts_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        # Suppress ALL extraction alerts for GI-mode devices. After system delete:
        # - mgmt IP is invalid (DHCP reassigns, another device may now have it)
        # - hostname_mismatch is expected (wrong device at old IP)
        # - serial_changed is expected (wrong device at old IP)
        # - stale_data / extraction_failed are expected (SSH won't work)
        _gi_alert_types = ('stale_data', 'extraction_failed', 'hostname_mismatch', 'serial_changed')
        gi_devices = set()
        for a in alerts:
            dev = a.get('device', '')
            if a.get('type') in _gi_alert_types and dev:
                op_path = Path(f"db/configs/{dev}/operational.json")
                if op_path.exists():
                    try:
                        with open(op_path) as of:
                            op = json.load(of)
                        if op.get('device_state') in ('GI', 'RECOVERY', 'DEPLOYING', 'BASEOS_SHELL', 'DN_RECOVERY'):
                            gi_devices.add(dev)
                    except Exception:
                        pass
        if gi_devices:
            alerts = [a for a in alerts if not (
                a.get('device') in gi_devices and
                a.get('type') in _gi_alert_types
            )]
            data['alerts'] = [a for a in data.get('alerts', []) if not (
                a.get('device') in gi_devices and
                a.get('type') in _gi_alert_types
            )]
            with open(alerts_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        if not alerts:
            return
        
        critical = [a for a in alerts if a['severity'] == 'CRITICAL']
        warnings = [a for a in alerts if a['severity'] == 'WARNING']
        
        fixable_devices = []
        
        if critical:
            console.print()
            for a in critical:
                if a.get('type') == 'recovery_mode':
                    console.print(f"  [bold red]🔴 {a['device']}:[/bold red] [red]{a['message']}[/red]")
                else:
                    console.print(f"  [bold red]⛔ {a['device']}:[/bold red] [red]{a['message']}[/red]")
                    if a.get('type') in ('stale_data', 'extraction_failed', 'hostname_mismatch', 'serial_changed'):
                        if a['device'] not in fixable_devices:
                            fixable_devices.append(a['device'])
        if warnings:
            if not critical:
                console.print()
            for a in warnings:
                console.print(f"  [yellow]⚠ {a['device']}:[/yellow] [dim]{a['message']}[/dim]")
                if a.get('type') in ('stale_data', 'extraction_failed', 'ip_changed'):
                    if a['device'] not in fixable_devices:
                        fixable_devices.append(a['device'])
        
        # Show context-aware action prompt
        has_recovery = bool(recovery_devices)
        has_fixable = bool(fixable_devices)
        
        if has_recovery or has_fixable:
            console.print()
            options = []
            if has_recovery:
                options.append("[R] Recover device (System Restore)")
            if has_fixable:
                options.append("[A] Auto-recover IP (Network Mapper)")
                options.append("[I] Change IP manually")
            options.append("[N] Skip")
            console.print(f"  [bold]{' | '.join(options)}[/bold]")
            
            choice = Prompt.ask("  [bold]Action[/bold]", default="n").strip().lower()
            
            if choice == 'r' and has_recovery:
                from .device_manager import DeviceManager
                from .wizard.system_restore import run_system_restore_wizard
                dm = DeviceManager()
                for rdev_name in recovery_devices:
                    device = dm.get_device(rdev_name)
                    if device:
                        console.print(f"\n[bold red]  Launching System Restore for {rdev_name}...[/bold red]")
                        try:
                            run_system_restore_wizard(device, None)
                        except Exception as e:
                            console.print(f"[red]  Error restoring {rdev_name}: {e}[/red]")
                    else:
                        console.print(f"[red]  Device '{rdev_name}' not found in database[/red]")
            elif choice == 'a' and has_fixable:
                _auto_recover_device_ip(fixable_devices)
            elif choice == 'i' and has_fixable:
                hostname = Prompt.ask(
                    f"  [bold]Enter hostname[/bold] ({', '.join(fixable_devices)})",
                    default=fixable_devices[0] if len(fixable_devices) == 1 else ""
                ).strip()
                if hostname:
                    matched = None
                    for d in fixable_devices:
                        if hostname.lower() in d.lower() or d.lower() in hostname.lower():
                            matched = d
                            break
                    if matched:
                        _update_device_ip_interactive(matched)
                    else:
                        console.print(f"[dim]  No match. Available: {', '.join(fixable_devices)}[/dim]")
    except Exception:
        pass


def _auto_recover_device_ip(fixable_devices: list) -> None:
    """Auto-recover device IP(s) via Network Mapper serial number discovery."""
    from .recover_device_ip import recover_device_ip

    if len(fixable_devices) == 1:
        targets = fixable_devices
        console.print(f"  [cyan]Attempting auto-recovery for {targets[0]}...[/cyan]")
    else:
        hostname = Prompt.ask(
            f"  [bold]Enter hostname or 'all'[/bold] ({', '.join(fixable_devices)})",
            default="all" if len(fixable_devices) <= 3 else fixable_devices[0]
        ).strip()

        if hostname.lower() == 'all':
            targets = fixable_devices
        else:
            matched = None
            for d in fixable_devices:
                if hostname.lower() in d.lower() or d.lower() in hostname.lower():
                    matched = d
                    break
            if not matched:
                console.print(f"  [dim]No match. Available: {', '.join(fixable_devices)}[/dim]")
                return
            targets = [matched]

    for target in targets:
        console.print(f"  [cyan]Recovering {target} via Network Mapper...[/cyan]", end=" ")
        try:
            new_ip = recover_device_ip(target)
            if new_ip:
                console.print(f"[green]✓ New IP: {new_ip}[/green]")
            else:
                console.print(f"[yellow]✗ Could not recover (no SN or device unreachable)[/yellow]")
                console.print(f"  [dim]  Use [I] Change IP to set it manually.[/dim]")
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")


def _update_device_ip_interactive(hostname: str) -> None:
    """Let user update a device's management IP from the wizard."""
    new_ip = Prompt.ask(f"  [cyan]Enter new management IP for {hostname}[/cyan]").strip()
    
    if not new_ip:
        return
    
    # Validate IP format
    import re
    if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', new_ip):
        console.print(f"  [red]Invalid IP format: {new_ip}[/red]")
        return
    
    try:
        # Update devices.json
        devices_file = Path("db/devices.json")
        with open(devices_file) as f:
            devices_data = json.load(f)
        
        old_ip = None
        for dev in devices_data.get("devices", []):
            if dev.get("hostname") == hostname:
                old_ip = dev.get("ip")
                dev["ip"] = new_ip
                break
        
        with open(devices_file, 'w') as f:
            json.dump(devices_data, f, indent=2)
        
        # Update operational.json
        ops_file = Path(f"db/configs/{hostname}/operational.json")
        if ops_file.exists():
            with open(ops_file) as f:
                ops_data = json.load(f)
            ops_data['mgmt_ip'] = new_ip
            ops_data['ssh_host'] = new_ip
            with open(ops_file, 'w') as f:
                json.dump(ops_data, f, indent=4)
        
        # Clear related alerts
        alerts_file = Path("db/alerts.json")
        if alerts_file.exists():
            with open(alerts_file) as f:
                alert_data = json.load(f)
            alert_data['alerts'] = [
                a for a in alert_data.get('alerts', [])
                if a.get('device') != hostname or a.get('type') not in 
                   ('stale_data', 'extraction_failed', 'ip_changed', 'hostname_mismatch')
            ]
            with open(alerts_file, 'w') as f:
                json.dump(alert_data, f, indent=2)
        
        console.print(f"  [green]✓ {hostname}: IP updated {old_ip} → {new_ip}[/green]")
        console.print(f"  [dim]Next extraction cycle will use the new IP.[/dim]")
    except Exception as e:
        console.print(f"  [red]Failed to update IP: {e}[/red]")


def _print_db_status_header(dm: DeviceManager) -> None:
    """Print DB/configs status line: device count and per-device status with specific recovery types."""
    devices = dm.list_devices()
    if not devices:
        console.print()
        return
    configs_base = Path("db/configs")
    parts = []
    for d in devices:
        op_file = configs_base / d.hostname / "operational.json"
        in_recovery = False
        recovery_type = ""
        if op_file.exists():
            try:
                with open(op_file) as f:
                    op_data = json.load(f)
                    dev_state = op_data.get("device_state", "")
                    in_recovery = (
                        op_data.get("recovery_mode_detected", False) or
                        dev_state in ("GI", "RECOVERY", "DEPLOYING", "BASEOS_SHELL", "DN_RECOVERY")
                    )
                    recovery_type = op_data.get("recovery_type", "")
                    if not recovery_type and dev_state == "GI":
                        recovery_type = "GI"
                    elif not recovery_type and dev_state in ("RECOVERY", "DN_RECOVERY"):
                        recovery_type = "DN_RECOVERY"
                    elif not recovery_type and dev_state == "BASEOS_SHELL":
                        recovery_type = "BASEOS_SHELL"
                    elif not recovery_type and dev_state == "DEPLOYING":
                        recovery_type = "GI"
            except Exception:
                pass
        
        # Show specific recovery type, not generic "RECOVERY"
        if in_recovery and recovery_type:
            if recovery_type == "DN_RECOVERY":
                parts.append(f"[bold red]{d.hostname}[/bold red]")
            elif recovery_type == "BASEOS_SHELL":
                parts.append(f"[yellow]{d.hostname}[/yellow]")
            elif recovery_type == "ONIE":
                parts.append(f"[bold red]{d.hostname}[/bold red]")
            elif recovery_type == "GI":
                parts.append(f"[cyan]{d.hostname}[/cyan]")
            elif recovery_type == "STANDALONE":
                parts.append(f"[yellow]{d.hostname}[/yellow]")
            else:
                parts.append(f"[red]{d.hostname}[/red]")
        else:
            parts.append(f"[green]{d.hostname}[/green] ✓")
    
    # Format: "db/configs: 4 device(s) — PE-1 ✓  RR-SA-2 ✓  PE-4 ✓  eCdnos-RR ✓"
    device_list = "  ".join(parts)
    console.print(f"\n[dim]db/configs:[/dim] [bold]{len(devices)}[/bold] device(s) — {device_list}")
    
    # Show integrity alerts from extraction monitoring
    _show_device_alerts()
    console.print()


class DeviceSummary:
    """Parsed device summary from running config header."""
    
    def __init__(self):
        # System info
        self.dnos_version: str = ""
        self.system_type: str = ""
        self.uptime: str = ""
        self.mgmt_ip: str = ""
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
    
    STAG_LIMIT = 4000  # PR-86760: Max unique Stags (parent + outer-tag combinations)
    
    def __init__(self, devices: List[Device]):
        self.devices = devices
        self.configs: Dict[str, str] = {}  # hostname -> running config
        self.loopbacks: Dict[str, str] = {}  # hostname -> loopback IP
        self.route_targets: Dict[str, set] = {}  # hostname -> set of RTs
        self.interfaces: Dict[str, List[str]] = {}  # hostname -> interface list
        self.mh_config: Dict[str, dict] = {}  # hostname -> interface->ESI map
        self.bgp_asn: Dict[str, int] = {}  # hostname -> BGP ASN
        self.summaries: Dict[str, DeviceSummary] = {}  # hostname -> parsed summary
        self.bgp_peers: Dict[str, List[str]] = {}  # hostname -> list of peer IPs
        self.stag_usage: Dict[str, Dict] = {}  # hostname -> {count, limit, parents}
        self.per_device_interfaces: Dict[str, List[str]] = {}  # hostname -> kept interfaces list
        
        # Cross-device context awareness for smart suggestions
        from .models import CrossDeviceContext as CrossDeviceCtx
        self.cross_device_context = CrossDeviceCtx()
    
    def count_stags(self, hostname: str, config: str) -> Dict:
        """Count unique Stags (parent + outer-tag combinations) for QinQ validation."""
        stags = set()
        current_parent = None
        
        for line in config.split('\n'):
            iface_match = re.match(r'^  (\S+\.\d+)\s*$', line)
            if iface_match:
                current_parent = iface_match.group(1).rsplit('.', 1)[0]
                continue
            if current_parent and 'outer-tag' in line:
                outer_match = re.search(r'outer-tag\s+(\d+)', line)
                if outer_match:
                    stags.add((current_parent, int(outer_match.group(1))))
        
        count = len(stags)
        return {
            'count': count,
            'limit': self.STAG_LIMIT,
            'percentage': int(count * 100 / self.STAG_LIMIT) if count > 0 else 0,
            'remaining': self.STAG_LIMIT - count,
            'at_risk': count > self.STAG_LIMIT * 0.9,
            'exceeded': count > self.STAG_LIMIT
        }
        
    def discover_all(self):
        """Discover configuration from all devices."""
        for dev in self.devices:
            config_path = f"db/configs/{dev.hostname}/running.txt"
            ops_path = f"db/configs/{dev.hostname}/operational.json"
            try:
                with open(config_path, 'r') as f:
                    config = f.read()
                    self.configs[dev.hostname] = config
                    self._parse_device_info(dev.hostname, config)
                    self._parse_config_header(dev.hostname, config)
                    self.stag_usage[dev.hostname] = self.count_stags(dev.hostname, config)
                
                # Also read operational.json for additional data (especially for network-mapper devices)
                try:
                    with open(ops_path, 'r') as f:
                        ops_data = json.load(f)
                        
                        # Override with operational data if available
                        if ops_data.get('lo0_ip') and dev.hostname not in self.loopbacks:
                            self.loopbacks[dev.hostname] = ops_data['lo0_ip']
                        if ops_data.get('router_id') and dev.hostname not in self.loopbacks:
                            self.loopbacks[dev.hostname] = ops_data['router_id']
                        if ops_data.get('local_as') and dev.hostname not in self.bgp_asn:
                            self.bgp_asn[dev.hostname] = ops_data['local_as']
                        
                        # Update DeviceSummary with operational data
                        if dev.hostname in self.summaries:
                            summary = self.summaries[dev.hostname]
                            if ops_data.get('dnos_version') and not summary.dnos_version:
                                summary.dnos_version = ops_data['dnos_version']
                            if ops_data.get('system_type') and not summary.system_type:
                                summary.system_type = ops_data['system_type']
                            if ops_data.get('system_uptime') and not summary.uptime:
                                summary.uptime = ops_data['system_uptime']
                            if ops_data.get('mgmt_ip'):
                                summary.mgmt_ip = ops_data['mgmt_ip']
                        
                        # Enhance summary with operational data
                        if dev.hostname in self.summaries:
                            summary = self.summaries[dev.hostname]
                            if ops_data.get('system_uptime') and not summary.uptime:
                                summary.uptime = ops_data['system_uptime']
                            if ops_data.get('system_type') and not summary.system_type:
                                summary.system_type = ops_data['system_type']
                            if ops_data.get('serial_number'):
                                summary.serial_number = ops_data['serial_number']
                            if ops_data.get('interfaces_total'):
                                summary.total_interfaces = ops_data['interfaces_total']
                            if ops_data.get('pwhe_total'):
                                summary.pwhe_parent = ops_data['pwhe_total']
                            if ops_data.get('fxc_total') and 'FXC' not in summary.services:
                                summary.services['FXC'] = (0, ops_data['fxc_total'], 'MPLS')
                            if ops_data.get('vpws_total') and 'VPWS' not in summary.services:
                                summary.services['VPWS'] = (0, ops_data['vpws_total'], 'MPLS')
                except FileNotFoundError:
                    pass  # No operational.json yet
                except Exception:
                    pass  # Ignore JSON parse errors
                    
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
        
        # Extract BGP info from header (e.g., "BGP: AS 1234567, 2/2 peers UP")
        bgp_header_match = re.search(r'#\s*•\s*BGP:\s*AS\s*(\d+),?\s*(\d+)/(\d+)\s*peers?\s*(UP)?', config)
        if bgp_header_match:
            summary.bgp_asn = int(bgp_header_match.group(1))
            summary.bgp_peers_up = int(bgp_header_match.group(2))
            summary.bgp_peers_total = int(bgp_header_match.group(3))
        
        # Extract label protocol
        label_match = re.search(r'#\s*•\s*Label Protocol:\s*(.+)', config)
        if label_match:
            summary.label_protocol = label_match.group(1).strip()
        
        # Extract PWHE info (e.g., "PWHE: 2300 parent + 2300 sub-interfaces (0 UP)")
        pwhe_match = re.search(r'#\s*•\s*PWHE:\s*(\d+)\s*parent\s*\+\s*(\d+)\s*sub-interfaces\s*\((\d+)\s*UP\)', config)
        if pwhe_match:
            summary.pwhe_parent = int(pwhe_match.group(1))
            summary.pwhe_sub = int(pwhe_match.group(2))
            summary.pwhe_up = int(pwhe_match.group(3))
        
        # Extract services (e.g., "FXC: 2299/2300 UP (MPLS)")
        # Exclude system components like NCC, NCP from services
        system_components = {'NCC', 'NCP', 'NCF', 'NCA'}
        service_pattern = r'#\s*•\s*(\w+):\s*(\d+)/(\d+)\s*UP\s*\(([^)]+)\)'
        for match in re.finditer(service_pattern, config):
            svc_type = match.group(1)
            if svc_type in system_components:
                continue  # Skip system components
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
        
        # Extract PWHE/L2 interfaces (DNOS format: 2-space indent under 'interfaces')
        # Match: ph1.1, ge100-0/0/12.1, bundle-2.1, etc.
        iface_pattern = r'^  (ph\d+(?:\.\d+)?|(?:ge|xe)\d+-[\d/]+(?:\.\d+)?|bundle-\d+(?:\.\d+)?)'
        self.interfaces[hostname] = list(set(re.findall(iface_pattern, config, re.MULTILINE)))
    
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
    
    def record_service_config(
        self, 
        hostname: str, 
        service_type: str, 
        name_pattern: str,
        count: int,
        start_index: int = 1,
        rt_asn: int = None,
        rt_format: str = None,
        rd_router_id: str = None,
        interfaces: List[str] = None,
        parent_interfaces: List[str] = None,
        transport: str = "mpls",
        has_mh: bool = False,
        mh_esi_prefix: str = None,
        vpws_service_id_start: int = None,
        vpws_service_id_mode: str = "sequential",
        control_word: bool = True,
        fat_label: bool = False
    ):
        """Record service configuration for cross-device suggestions."""
        from .models import ServiceRecord, DeviceConfigRecord
        
        # Create service record
        svc_record = ServiceRecord(
            service_type=service_type,
            name_pattern=name_pattern,
            count=count,
            start_index=start_index,
            rt_asn=rt_asn,
            rt_format=rt_format,
            rd_router_id=rd_router_id,
            interfaces=interfaces or [],
            parent_interfaces=parent_interfaces or [],
            transport=transport,
            has_mh=has_mh,
            mh_esi_prefix=mh_esi_prefix,
            vpws_service_id_start=vpws_service_id_start,
            vpws_service_id_mode=vpws_service_id_mode,
            control_word=control_word,
            fat_label=fat_label
        )
        
        # Get or create device record
        if hostname not in self.cross_device_context.device_records:
            self.cross_device_context.device_records[hostname] = DeviceConfigRecord(
                hostname=hostname,
                loopback_ip=self.loopbacks.get(hostname),
                bgp_asn=self.bgp_asn.get(hostname)
            )
        
        # Add service to device record
        self.cross_device_context.device_records[hostname].configured_services.append(svc_record)
    
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
        """
        Validate DNOS platform limits for all devices.
        
        Returns:
            Dict: {hostname: {limit_key: {value, max, exceeded, ...}}}
        """
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
            
            # Validate without printing (we'll show a combined table)
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
        # Collect unique limit types
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
        
        # Add column for each device
        for dev in self.devices:
            table.add_column(dev.hostname, justify="center", width=20)
        
        table.add_column("Max", justify="right", width=10)
        
        # Add rows for each limit type
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


def show_cross_device_suggestions(multi_ctx: 'MultiDeviceContext', target_hostname: str) -> Optional[str]:
    """
    Show configuration suggestions based on other devices' configurations.
    
    This implements the "self-aware wizard" feature that suggests matching
    configurations for a device based on what was configured on other devices.
    
    Args:
        multi_ctx: MultiDeviceContext with cross-device tracking
        target_hostname: Hostname of the device being configured
        
    Returns:
        Generated config string if user selects Quick Apply, None otherwise
    """
    # Use cross_device_context for suggestions
    if not hasattr(multi_ctx, 'cross_device_context') or not multi_ctx.cross_device_context:
        return None
    
    if not multi_ctx.cross_device_context.has_suggestions_for(target_hostname):
        return None
    
    target_loopback = multi_ctx.loopbacks.get(target_hostname, "N/A")
    suggestions = multi_ctx.cross_device_context.get_suggestions_for_device(target_hostname, target_loopback)
    if not suggestions:
        return None
    
    console.print("\n[bold cyan]╔═══════════════════════════════════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║  💡 Smart Suggestions Based on Previous Configuration              ║[/bold cyan]")
    console.print("[bold cyan]╠═══════════════════════════════════════════════════════════════════╣[/bold cyan]")
    
    # Group suggestions by source device
    by_source = {}
    for sug in suggestions:
        src = sug.source_device
        if src not in by_source:
            by_source[src] = []
        by_source[src].append(sug)
    
    # Display what was configured on other devices
    for source_host, source_suggestions in by_source.items():
        source_loopback = multi_ctx.loopbacks.get(source_host, "N/A")
        console.print(f"[bold cyan]║[/bold cyan]  [white]From {source_host}[/white] (Loopback: {source_loopback})")
        
        for sug in source_suggestions:
            if sug.suggestion_type == "matching_services":
                console.print(f"[bold cyan]║[/bold cyan]    • {sug.service_count:,} {sug.service_type} services")
            elif sug.suggestion_type == "matching_vrfs":
                console.print(f"[bold cyan]║[/bold cyan]    • VRF configuration")
            elif sug.suggestion_type == "mh_pairing":
                console.print(f"[bold cyan]║[/bold cyan]    • Multihoming ESI pairing")
    
    console.print(f"[bold cyan]║[/bold cyan]")
    console.print(f"[bold cyan]║[/bold cyan]  [green]Suggested for {target_hostname}[/green] (Loopback: {target_loopback}):")
    console.print(f"[bold cyan]║[/bold cyan]    • Same services with unique RD ({target_loopback}:N)")
    console.print(f"[bold cyan]║[/bold cyan]    • Same RTs for EVPN peering")
    if any(s.same_esi for s in suggestions):
        console.print(f"[bold cyan]║[/bold cyan]    • Same ESI for multihoming")
    
    console.print(f"[bold cyan]║[/bold cyan]")
    console.print("[bold cyan]║[/bold cyan]  [bold]Options:[/bold]")
    console.print("[bold cyan]║[/bold cyan]    [Q] [green]Quick Match[/green] - Apply suggested config now")
    console.print("[bold cyan]║[/bold cyan]    [V] View Generated Config")
    console.print("[bold cyan]║[/bold cyan]    [M] Modify & Apply")
    console.print("[bold cyan]║[/bold cyan]    [S] Skip - Configure manually")
    
    # Next step hints
    next_hints = [s.next_step_hint for s in suggestions if s.next_step_hint]
    if next_hints:
        console.print(f"[bold cyan]║[/bold cyan]")
        console.print("[bold cyan]║[/bold cyan]  [bold]Next Step Suggestions:[/bold]")
        for hint in set(next_hints):
            console.print(f"[bold cyan]║[/bold cyan]    [dim]→ {hint}[/dim]")
    
    console.print("[bold cyan]╚═══════════════════════════════════════════════════════════════════╝[/bold cyan]")
    
    choice = Prompt.ask("\nSelect", choices=["q", "Q", "v", "V", "m", "M", "s", "S"], default="s").lower()
    
    if choice == "s":
        console.print("[dim]Skipping suggestions, continuing with manual configuration...[/dim]")
        return None
    
    # Generate the matching configuration
    all_configs = []
    for sug in suggestions:
        config = multi_ctx.generate_matching_config(sug, target_hostname)
        if config:
            all_configs.append(config)
    
    combined_config = "\n\n".join(all_configs)
    
    if choice == "v":
        # View the generated config
        console.print("\n[bold]Generated Configuration:[/bold]")
        console.print(Panel(combined_config[:2000] + ("..." if len(combined_config) > 2000 else ""),
                           title="Suggested Config", border_style="cyan"))
        
        if len(combined_config) > 2000:
            console.print(f"[dim]... ({len(combined_config.split(chr(10)))} total lines)[/dim]")
        
        # Ask what to do with it
        console.print("\n[bold]What would you like to do?[/bold]")
        console.print("  [A] Apply this configuration")
        console.print("  [E] Edit before applying")
        console.print("  [S] Save to file only")
        console.print("  [C] Cancel")
        
        action = Prompt.ask("Select", choices=["a", "A", "e", "E", "s", "S", "c", "C"], default="a").lower()
        
        if action == "a":
            return combined_config
        elif action == "e":
            console.print("\n[yellow]Edit mode not yet implemented. Use Save to file option.[/yellow]")
            return None
        elif action == "s":
            # Save to file
            config_dir = Path(f"db/configs/{target_hostname}")
            config_dir.mkdir(parents=True, exist_ok=True)
            filepath = config_dir / f"suggested_{time.strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filepath, 'w') as f:
                f.write(combined_config)
            console.print(f"[green]✓ Saved to: {filepath}[/green]")
            return None
        else:
            return None
    
    elif choice == "q":
        # Quick apply
        console.print(f"\n[green]✓ Applying suggested configuration ({len(combined_config.split(chr(10)))} lines)...[/green]")
        return combined_config
    
    elif choice == "m":
        # Modify & apply (show config, allow edits, then apply)
        console.print("\n[yellow]Modify mode: Configuration will be saved to file for editing[/yellow]")
        config_dir = Path(f"db/configs/{target_hostname}")
        config_dir.mkdir(parents=True, exist_ok=True)
        filepath = config_dir / f"suggested_edit_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filepath, 'w') as f:
            f.write(combined_config)
        console.print(f"[green]✓ Saved to: {filepath}[/green]")
        console.print("[dim]Edit the file and use 'Push Files' option to apply.[/dim]")
        return None
    
    return None


def select_multiple_devices(dm: DeviceManager) -> Optional[List[Device]]:
    """Select multiple devices for synchronized configuration."""
    
    def _is_device_in_recovery(dev: Device) -> bool:
        """Check if device is in recovery mode."""
        try:
            op_file = Path(f"db/configs/{dev.hostname}/operational.json")
            if op_file.exists():
                with open(op_file) as f:
                    return json.load(f).get('recovery_mode_detected', False)
        except:
            pass
        return False
    
    def _is_device_configurable(dev: Device) -> bool:
        """Check if device can be configured (GI, STANDALONE, or not in recovery)."""
        try:
            op_file = Path(f"db/configs/{dev.hostname}/operational.json")
            if op_file.exists():
                with open(op_file) as f:
                    op_data = json.load(f)
                    if not op_data.get('recovery_mode_detected', False):
                        return True  # Not in recovery
                    recovery_type = op_data.get('recovery_type', '')
                    # GI and STANDALONE are semi-operational
                    return recovery_type in ['GI', 'STANDALONE']
        except:
            pass
        return True  # Default: assume configurable
    
    while True:
        devices = dm.list_devices()
        
        if not devices:
            console.print("[red]No devices configured. Please add a device first.[/red]")
            return None
        
        if len(devices) < 2:
            console.print("[yellow]Multi-device mode requires at least 2 devices.[/yellow]")
            return None
        
        # Display devices table with checkboxes
        console.print("\n[bold cyan]Multi-Device Selection[/bold cyan]")
        console.print("[dim]Select devices to configure simultaneously (synchronized)[/dim]\n")
        
        table = Table(box=box.ROUNDED)
        table.add_column("#", style="dim", width=3)
        table.add_column("Hostname", style="green")
        table.add_column("Loopback", style="yellow")
        table.add_column("Connection", style="cyan")
        table.add_column("IP", style="dim")
        table.add_column("Status", style="dim")
        
        for i, dev in enumerate(devices, 1):
            # Try to get loopback from cached config
            loopback = "N/A"
            try:
                config_path = f"db/configs/{dev.hostname}/running.txt"
                with open(config_path, 'r') as f:
                    config = f.read()
                    lo_match = re.search(r'lo0\s*\n\s*.*?\n\s*ipv4-address\s+(\d+\.\d+\.\d+\.\d+)', config)
                    if lo_match:
                        loopback = lo_match.group(1)
            except:
                pass
            
            # Get system type, connection info, and recovery status
            system_type = dev.platform.value
            status_str = "[green]OK[/green]"
            in_recovery = False
            recovery_type = ""
            dnos_version = ""
            connection_method = "[dim]unknown[/dim]"
            mgmt_ip = dev.ip
            
            try:
                op_file = Path(f"db/configs/{dev.hostname}/operational.json")
                if op_file.exists():
                    with open(op_file) as f:
                        op_data = json.load(f)
                        if op_data.get('system_type'):
                            system_type = op_data['system_type']
                        dnos_version = op_data.get('dnos_version', '')
                        
                        # Get connection method and IP
                        conn_method = op_data.get('connection_method', '')
                        stored_mgmt_ip = op_data.get('mgmt_ip') or op_data.get('ssh_host', '')
                        if stored_mgmt_ip:
                            mgmt_ip = stored_mgmt_ip.split('/')[0] if '/' in stored_mgmt_ip else stored_mgmt_ip
                        
                        # Dynamic connection method resolution based on device state.
                        # Non-DNOS states prefer virsh/console; DNOS prefers SSH.
                        _dev_state_for_conn = (op_data.get('device_state', '') or '').upper()
                        _is_limited_mode = _dev_state_for_conn in ('GI', 'BASEOS_SHELL', 'ONIE', 'DN_RECOVERY', 'RECOVERY', 'DEPLOYING')
                        _is_dnos_mode = _dev_state_for_conn in ('DNOS', '')
                        _sys_type = (op_data.get('system_type', '') or '').upper()
                        _is_cluster = _sys_type.startswith('CL-')
                        _ncc_type = (op_data.get('ncc_type', '') or '').lower()
                        
                        if _is_limited_mode:
                            if _is_cluster and _ncc_type == 'kvm' and op_data.get('kvm_host'):
                                _kvm_host = op_data['kvm_host']
                                conn_method = f"virsh->NCC ({_kvm_host})"
                                op_data['connection_method'] = conn_method
                                try:
                                    with open(op_file, 'w') as fw:
                                        json.dump(op_data, fw, indent=4)
                                except IOError:
                                    pass
                            elif 'SSH' in conn_method if conn_method else bool(stored_mgmt_ip):
                                try:
                                    from .connection_strategy import get_console_config_for_device
                                    _console_cfg = get_console_config_for_device(dev.hostname)
                                    if _console_cfg and _console_cfg.get('port'):
                                        _srv = _console_cfg.get('console_server_name', 'console')
                                        _port = _console_cfg['port']
                                        _suffix = " NCP" if _is_cluster and _ncc_type == 'kvm' else ""
                                        conn_method = f"Console ({_srv} p{_port}{_suffix})"
                                        op_data['connection_method'] = conn_method
                                        try:
                                            with open(op_file, 'w') as fw:
                                                json.dump(op_data, fw, indent=4)
                                        except IOError:
                                            pass
                                except ImportError:
                                    pass
                        elif _is_dnos_mode and conn_method and 'SSH' not in conn_method:
                            _resolved = False
                            _sn = op_data.get('serial_number', '')
                            _mgmt = (stored_mgmt_ip or '').split('/')[0] if stored_mgmt_ip else ''
                            _ncc_hosts = op_data.get('ncc_hosts', []) if _ncc_type == 'kvm' else []
                            if _sn and _sn not in ('N/A', ''):
                                conn_method = f"SSH->SN ({dev.username or 'dnroot'})"
                                _resolved = True
                            elif _mgmt:
                                conn_method = f"SSH->MGMT ({_mgmt})"
                                _resolved = True
                            elif _ncc_hosts:
                                conn_method = f"SSH->NCC ({_ncc_hosts[0]})"
                                _resolved = True
                            if _resolved:
                                op_data['connection_method'] = conn_method
                                try:
                                    with open(op_file, 'w') as fw:
                                        json.dump(op_data, fw, indent=4)
                                except IOError:
                                    pass
                        
                        if conn_method:
                            if 'virsh' in conn_method:
                                connection_method = f"[magenta]{conn_method}[/magenta]"
                            elif 'SSH' in conn_method:
                                connection_method = f"[green]{conn_method}[/green]"
                            elif 'Console' in conn_method:
                                connection_method = f"[yellow]{conn_method}[/yellow]"
                            else:
                                connection_method = f"[cyan]{conn_method}[/cyan]"
                        elif stored_mgmt_ip:
                            connection_method = "[dim]SSH (cached)[/dim]"
                        
                        # Check device_state directly (primary) and recovery_mode_detected (secondary)
                        cached_state = op_data.get('device_state', '')
                        delete_ts = op_data.get('delete_initiated', '')
                        last_verified = op_data.get('last_verified', '')
                        
                        # Auto-detect: if delete was initiated after last verification,
                        # device must be in GI regardless of what state says
                        if cached_state == 'DNOS' and delete_ts and delete_ts > last_verified:
                            cached_state = 'GI'
                            op_data['device_state'] = 'GI'
                            op_data['recovery_mode_detected'] = True
                            op_data['recovery_type'] = 'GI'
                            try:
                                with open(op_file, 'w') as fw:
                                    json.dump(op_data, fw, indent=4)
                            except IOError:
                                pass
                        
                        if op_data.get('recovery_mode_detected') or cached_state in ('GI', 'BASEOS_SHELL', 'ONIE', 'DN_RECOVERY', 'RECOVERY', 'DEPLOYING'):
                            in_recovery = True
                            recovery_type = op_data.get('recovery_type', '') or cached_state
                            if recovery_type == 'DN_RECOVERY':
                                status_str = "[bold red]DN_RECOVERY[/bold red]"
                            elif recovery_type == 'BASEOS_SHELL':
                                status_str = "[yellow]BASEOS_SHELL[/yellow]"
                            elif recovery_type == 'ONIE':
                                status_str = "[bold red]ONIE[/bold red]"
                            elif recovery_type in ('GI', 'DEPLOYING'):
                                status_str = "[cyan]GI_MODE[/cyan]"
                            elif recovery_type == 'STANDALONE':
                                status_str = "[yellow]STANDALONE[/yellow]"
                            else:
                                status_str = "[bold red]RECOVERY[/bold red]"
                        elif dnos_version in ('N/A', '', None) or not dnos_version:
                            status_str = "[cyan]? GI/No DNOS[/cyan]"
                            in_recovery = True
                            recovery_type = "GI"
            except:
                pass
            
            configurable_states = ['GI', 'STANDALONE', 'DEPLOYING', '']
            is_configurable = not in_recovery or recovery_type in configurable_states
            
            if not is_configurable:
                table.add_row(
                    f"[dim]{i}[/]",
                    f"[dim strike]{dev.hostname}[/]",
                    f"[dim]{loopback}[/]",
                    f"[dim]{connection_method}[/]",
                    f"[dim]{mgmt_ip}[/]",
                    f"[dim]{status_str}[/]"
                )
            else:
                # Normal display for configurable devices
                table.add_row(str(i), dev.hostname, loopback, connection_method, mgmt_ip, status_str)
        
        console.print(table)
        
        # Show note about recovery devices
        recovery_devices = [d for d in devices if _is_device_in_recovery(d) and not _is_device_configurable(d)]
        if recovery_devices:
            console.print(f"\n[dim]Note: [strike]Greyed devices[/strike] are in recovery mode and cannot be configured.[/dim]")
            console.print(f"[dim]      Fix them first using System Restore wizard (single device mode).[/dim]")
        
        # Selection prompt
        console.print("\n[bold]Selection Options:[/bold]")
        console.print("  Enter device numbers: commas (1,3,5) or ranges (1-4) or both (1-3,5)")
        console.print("  Or 'all' to select all [green]available[/green] devices")
        console.print("  Or 'd' to [red]delete[/red] device(s) from cache")
        console.print("  Or 'b' to go back\n")
        
        selection = Prompt.ask("Select devices", default="1,2")
        
        if selection.lower() == 'b':
            return None
        
        # Handle delete
        if selection.lower() == 'd':
            delete_devices_from_cache(dm)
            continue
        
        selected = []
        if selection.lower() == 'all':
            selected = [d for d in devices if not _is_device_in_recovery(d) or _is_device_configurable(d)]
        else:
            max_num = len(devices)
            requested_nums = set()
            bad_input = False
            try:
                for part in selection.replace(' ', '').split(','):
                    if not part:
                        continue
                    if '-' in part:
                        range_parts = part.split('-')
                        nums = [p for p in range_parts if p]
                        if len(nums) != 2 or not nums[0].isdigit() or not nums[1].isdigit():
                            console.print(f"[red]'{part}' is not a valid range. Use N-M format (e.g., 1-{max_num})[/red]")
                            bad_input = True
                            continue
                        start, end = int(nums[0]), int(nums[1])
                        if start > end:
                            console.print(f"[red]Invalid range '{part}': start must be <= end[/red]")
                            bad_input = True
                            continue
                        if start < 1 or start > max_num:
                            console.print(f"[red]Range start {start} is out of bounds. Valid devices: 1-{max_num}[/red]")
                            bad_input = True
                            continue
                        if end > max_num:
                            console.print(f"[red]Range end {end} exceeds available devices. Valid: 1-{max_num}[/red]")
                            bad_input = True
                            continue
                        for n in range(start, end + 1):
                            requested_nums.add(n)
                    elif part.isdigit():
                        n = int(part)
                        if 1 <= n <= max_num:
                            requested_nums.add(n)
                        else:
                            console.print(f"[red]Device #{n} does not exist. Valid: 1-{max_num}[/red]")
                            bad_input = True
                    else:
                        console.print(f"[red]'{part}' is not a valid number[/red]")
                        bad_input = True
            except Exception:
                console.print(f"[red]Invalid input. Enter numbers 1-{max_num}, commas, or ranges (e.g., 1-{min(3,max_num)})[/red]")
                continue
            
            if bad_input:
                continue
            
            if not requested_nums:
                console.print(f"[red]No devices selected. Choose from 1-{max_num}[/red]")
                continue
            
            selected = [devices[n - 1] for n in sorted(requested_nums)]
        
        # Filter out non-configurable devices
        invalid_devices = [d for d in selected if _is_device_in_recovery(d) and not _is_device_configurable(d)]
        if invalid_devices:
            console.print(f"\n[red]✗ Cannot select devices in recovery mode:[/red]")
            for d in invalid_devices:
                try:
                    op_file = Path(f"db/configs/{d.hostname}/operational.json")
                    if op_file.exists():
                        with open(op_file) as f:
                            recovery_type = json.load(f).get('recovery_type', 'RECOVERY')
                    console.print(f"  • {d.hostname} ([red]{recovery_type}[/red])")
                except:
                    console.print(f"  • {d.hostname} ([red]RECOVERY[/red])")
            console.print(f"\n[yellow]Fix these devices first:[/yellow]")
            console.print(f"  1. Exit multi-device mode ([B]ack)")
            console.print(f"  2. Select device in single-device mode")
            console.print(f"  3. Run System Restore wizard")
            console.print(f"  4. Return to multi-device mode")
            Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")
            continue
        
        if len(selected) < 2:
            console.print("[yellow]Please select at least 2 devices for multi-device mode[/yellow]")
            continue
        
        # Confirm selection
        console.print(f"\n[green]✓ Selected {len(selected)} devices:[/green]")
        for dev in selected:
            loopback = "N/A"
            try:
                config_path = f"db/configs/{dev.hostname}/running.txt"
                with open(config_path, 'r') as f:
                    config = f.read()
                    lo_match = re.search(r'lo0\s*\n\s*.*?\n\s*ipv4-address\s+(\d+\.\d+\.\d+\.\d+)', config)
                    if lo_match:
                        loopback = lo_match.group(1)
            except:
                pass
            console.print(f"  • {dev.hostname} ({loopback})")
        
        return selected


def display_split_view(left_title: str, left_content: List[str], 
                       right_title: str, right_content: List[str]):
    """Display a split view for two devices."""
    from rich.columns import Columns
    from rich.panel import Panel
    
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


def push_synchronized_multihoming(multi_ctx: MultiDeviceContext) -> bool:
    """
    Push synchronized multihoming configuration to multiple devices.
    
    Uses RT-BASED MATCHING: Interfaces sharing the same Route Target get the same ESI.
    This is the correct approach per RFC 7432 - ESI identifies a shared Ethernet Segment.
    """
    from rich.columns import Columns
    from rich.panel import Panel
    from .utils import get_device_config_dir
    
    console.print("\n[bold cyan]🔗 Synchronized Multi-Device Multihoming (RT+VLAN Based)[/bold cyan]")
    console.print("[dim]Matching ESI values based on shared Route Targets AND VLAN-TAG configuration[/dim]")
    
    if len(multi_ctx.devices) < 2:
        console.print("[yellow]Need at least 2 devices for synchronized MH.[/yellow]")
        return False
    
    dev1, dev2 = multi_ctx.devices[0], multi_ctx.devices[1]
    
    # =========================================================================
    # STEP 1: Load fresh configs from cache
    # =========================================================================
    console.print("\n[bold]Step 1: Loading device configurations...[/bold]")
    
    device_configs_raw = {}
    for dev in multi_ctx.devices:
        config_path = get_device_config_dir(dev.hostname) / "running.txt"
        if config_path.exists():
            with open(config_path, 'r') as f:
                device_configs_raw[dev.hostname] = f.read()
            console.print(f"  [green]✓ {dev.hostname}[/green]: loaded ({config_path.stat().st_size // 1024} KB)")
        else:
            console.print(f"  [red]✗ {dev.hostname}[/red]: running.txt not found")
            console.print(f"    [dim]Run scaler-wizard to fetch config first[/dim]")
            return False
    
    # =========================================================================
    # STEP 2: Build interface → RT + VLAN mapping for each device
    # =========================================================================
    console.print("\n[bold]Step 2: Building interface → RT + VLAN mappings...[/bold]")
    
    dev_iface_mapping = {}  # {hostname: {interface: {'rts': set, 'vlan_key': str}}}
    
    for dev in multi_ctx.devices:
        config = device_configs_raw.get(dev.hostname, "")
        iface_mapping = build_interface_to_rt_vlan_mapping(config)
        dev_iface_mapping[dev.hostname] = iface_mapping
        
        # Count unique RTs and VLAN configs
        all_rts = set()
        vlan_keys = set()
        for info in iface_mapping.values():
            all_rts.update(info.get('rts', set()))
            vlan_keys.add(info.get('vlan_key', 'none'))
        
        console.print(f"  [green]✓ {dev.hostname}[/green]: {len(iface_mapping)} interfaces, {len(all_rts)} RTs, {len(vlan_keys)} VLAN configs")
    
    # =========================================================================
    # STEP 3: Build ESI groups based on RT + VLAN matching
    # Interfaces with SAME RT + SAME VLAN-TAG get the SAME ESI
    # =========================================================================
    console.print("\n[bold]Step 3: Building ESI groups (RT + VLAN matching)...[/bold]")
    
    esi_groups = build_esi_groups_by_rt_vlan(dev_iface_mapping)
    
    # Find shared groups (appear on both devices)
    shared_groups = {}
    only_dev1_groups = {}
    only_dev2_groups = {}
    
    for key, group in esi_groups.items():
        devices_in_group = set(group['devices'].keys())
        if dev1.hostname in devices_in_group and dev2.hostname in devices_in_group:
            shared_groups[key] = group
        elif dev1.hostname in devices_in_group:
            only_dev1_groups[key] = group
        elif dev2.hostname in devices_in_group:
            only_dev2_groups[key] = group
    
    console.print(f"  [green]✓ Shared ESI groups:[/green] {len(shared_groups)}")
    if only_dev1_groups:
        console.print(f"  [yellow]⚠ Only on {dev1.hostname}:[/yellow] {len(only_dev1_groups)} groups")
    if only_dev2_groups:
        console.print(f"  [yellow]⚠ Only on {dev2.hostname}:[/yellow] {len(only_dev2_groups)} groups")
    
    if not shared_groups:
        console.print("\n[red]✗ No matching RT+VLAN groups found between devices![/red]")
        console.print("[dim]Devices must have matching RT AND VLAN-TAG to share ESI.[/dim]")
        return False
    
    # =========================================================================
    # STEP 4: Assign ESI values to each group
    # =========================================================================
    console.print("\n[bold]Step 4: Assigning ESI values to RT+VLAN groups...[/bold]")
    
    esi_prefix = IntPrompt.ask("ESI prefix (16-bit value)", default=1)
    
    # Assign ESI per group (not per interface or per RT alone)
    group_to_esi = {}  # {composite_key: esi_value}
    dev_iface_to_esi = {}  # {hostname: {interface: esi_value}}
    
    for dev in multi_ctx.devices:
        dev_iface_to_esi[dev.hostname] = {}
    
    # Process shared groups first (priority)
    esi_idx = 1
    for key in sorted(shared_groups.keys()):
        group = shared_groups[key]
        esi_value = generate_esi(esi_prefix, esi_idx)
        group_to_esi[key] = esi_value
        
        # Assign to all interfaces in this group on all devices
        for hostname, interfaces in group['devices'].items():
            for iface in interfaces:
                dev_iface_to_esi[hostname][iface] = esi_value
        
        esi_idx += 1
    
    # Also include device-only groups (they still need ESI, just not shared)
    for key in sorted(only_dev1_groups.keys()):
        group = only_dev1_groups[key]
        esi_value = generate_esi(esi_prefix, esi_idx)
        group_to_esi[key] = esi_value
        for hostname, interfaces in group['devices'].items():
            for iface in interfaces:
                dev_iface_to_esi[hostname][iface] = esi_value
        esi_idx += 1
    
    for key in sorted(only_dev2_groups.keys()):
        group = only_dev2_groups[key]
        esi_value = generate_esi(esi_prefix, esi_idx)
        group_to_esi[key] = esi_value
        for hostname, interfaces in group['devices'].items():
            for iface in interfaces:
                dev_iface_to_esi[hostname][iface] = esi_value
        esi_idx += 1
    
    total_ifaces_per_dev = {h: len(ifaces) for h, ifaces in dev_iface_to_esi.items()}
    for h, count in total_ifaces_per_dev.items():
        console.print(f"  [green]✓ {h}[/green]: {count} interfaces will get ESI")
    
    # =========================================================================
    # STEP 5: Show RT+VLAN → Interface → ESI mapping preview
    # =========================================================================
    console.print("\n[bold]RT+VLAN ESI Mapping Preview:[/bold]")
    console.print("[dim]Same RT + Same VLAN-TAG → Same ESI[/dim]\n")
    
    # Show first 5 shared groups
    sample_keys = sorted(shared_groups.keys())[:5]
    for key in sample_keys:
        esi = group_to_esi[key]
        group = shared_groups[key]
        
        # Parse the composite key (RT:VLAN_KEY)
        parts = key.split(':', 2)  # Split into RT (may contain :) and VLAN key
        if len(parts) >= 2:
            rt_part = ':'.join(parts[:-1]) if len(parts) > 2 else parts[0]
            vlan_part = parts[-1]
        else:
            rt_part, vlan_part = key, "?"
        
        console.print(f"  [cyan]RT {rt_part} + VLAN {vlan_part}[/cyan] → ESI [green]{esi}[/green]")
        for hostname, interfaces in group['devices'].items():
            iface_list = ', '.join(interfaces[:3])
            suffix = f' ... (+{len(interfaces)-3})' if len(interfaces) > 3 else ''
            console.print(f"    {hostname}: {iface_list}{suffix}")
    
    if len(shared_groups) > 5:
        console.print(f"  [dim]... and {len(shared_groups) - 5} more groups[/dim]")
    
    # =========================================================================
    # DNOS PLATFORM LIMIT CHECK
    # =========================================================================
    MAX_ESI_INTERFACES = get_limit("multihoming", "max_esi_interfaces", 2000)
    
    console.print("\n[bold]DNOS Limit Validation:[/bold]")
    will_exceed = False
    selected_ifaces_per_dev = {}
    
    for dev in multi_ctx.devices:
        h = dev.hostname
        current_mh = len(multi_ctx.mh_config.get(h, {}))
        new_mh = total_ifaces_per_dev.get(h, 0)
        total_mh = current_mh + new_mh
        
        if total_mh > MAX_ESI_INTERFACES:
            console.print(f"  [red]✗ {h}: {current_mh} existing + {new_mh} new = {total_mh} (exceeds {MAX_ESI_INTERFACES})[/red]")
            will_exceed = True
            # Limit to first N RTs that fit
            allowed_new = MAX_ESI_INTERFACES - current_mh
            console.print(f"    [yellow]Will limit to {allowed_new} interfaces[/yellow]")
        else:
            pct = (total_mh / MAX_ESI_INTERFACES) * 100
            console.print(f"  [green]✓ {h}: {current_mh} existing + {new_mh} new = {total_mh} ({pct:.0f}% of limit)[/green]")
    
    if will_exceed:
        if not Confirm.ask("\nProceed with limited interfaces?", default=True):
            return False
    
    # =========================================================================
    # STEP 6: Generate config for each device
    # PRIORITIZE: Interfaces in SHARED groups (matching RT+VLAN on both devices)
    # =========================================================================
    console.print("\n[bold]Step 6: Generating configurations...[/bold]")
    console.print("[dim]Prioritizing interfaces with matching RT+VLAN across devices[/dim]")
    
    device_configs = {}
    
    # Build set of interfaces that are in SHARED groups (matching on both devices)
    shared_ifaces_per_dev = {dev.hostname: set() for dev in multi_ctx.devices}
    for key, group in shared_groups.items():
        for hostname, interfaces in group['devices'].items():
            shared_ifaces_per_dev[hostname].update(interfaces)
    
    for dev in multi_ctx.devices:
        h = dev.hostname
        iface_esi_map = dev_iface_to_esi.get(h, {})
        
        # Apply DNOS limit if needed
        current_mh = len(multi_ctx.mh_config.get(h, {}))
        max_new = MAX_ESI_INTERFACES - current_mh
        
        # PRIORITIZE shared interfaces (matching RT+VLAN on both devices)
        shared_ifaces = [i for i in iface_esi_map.keys() if i in shared_ifaces_per_dev[h]]
        only_local = [i for i in iface_esi_map.keys() if i not in shared_ifaces_per_dev[h]]
        
        # Sort each group numerically
        shared_sorted = sorted(shared_ifaces, key=lambda x: extract_interface_number(x) or 999999)
        only_local_sorted = sorted(only_local, key=lambda x: extract_interface_number(x) or 999999)
        
        # Take shared first, then local-only if room
        sorted_ifaces = shared_sorted + only_local_sorted
        
        if len(sorted_ifaces) > max_new:
            sorted_ifaces = sorted_ifaces[:max_new]
            # Report how many shared vs local-only
            selected_shared = len([i for i in sorted_ifaces if i in shared_ifaces_per_dev[h]])
            selected_local = len(sorted_ifaces) - selected_shared
            console.print(f"  [yellow]{h}: Limited to {max_new} interfaces (DNOS limit)[/yellow]")
            console.print(f"    [dim]→ {selected_shared:,} matching + {selected_local:,} local-only[/dim]")
        
        # Generate config
        config_lines = []
        config_lines.append("network-services")
        config_lines.append("  multihoming")
        config_lines.append("    designated-forwarder")
        config_lines.append("      algorithm mod")
        config_lines.append("    !")
        config_lines.append("    redundancy-mode single-active")
        
        for iface in sorted_ifaces:
            esi_value = iface_esi_map.get(iface)
            if esi_value:
                config_lines.append(f"    interface {iface}")
                config_lines.append(f"      esi arbitrary value {esi_value}")
                config_lines.append("      redundancy-mode single-active")
                config_lines.append("    !")
        
        config_lines.append("  !")
        config_lines.append("!")
        device_configs[h] = "\n".join(config_lines)
        console.print(f"  [green]✓ {h}[/green]: {len(sorted_ifaces)} interfaces, {len(config_lines)} lines")
    
    # =========================================================================
    # Split view preview - NUMERICAL SUMMARY
    # =========================================================================
    if len(multi_ctx.devices) >= 2:
        # Calculate actual numbers for each device
        h1, h2 = dev1.hostname, dev2.hostname
        
        # Get actual configured counts (after limit applied)
        cfg1_lines = device_configs.get(h1, "").count("interface ")
        cfg2_lines = device_configs.get(h2, "").count("interface ")
        
        # Get RT+VLAN matched vs local-only
        shared1 = len(shared_ifaces_per_dev.get(h1, set()))
        shared2 = len(shared_ifaces_per_dev.get(h2, set()))
        total1 = total_ifaces_per_dev.get(h1, 0)
        total2 = total_ifaces_per_dev.get(h2, 0)
        local_only1 = total1 - shared1
        local_only2 = total2 - shared2
        
        current_mh1 = len(multi_ctx.mh_config.get(h1, {}))
        current_mh2 = len(multi_ctx.mh_config.get(h2, {}))
        
        left_content = [
            f"[bold]ESI Configuration Summary[/bold]",
            f"───────────────────────────",
            f"RT+VLAN matched:  [green]{shared1:,}[/green]",
            f"Local-only:       [yellow]{local_only1:,}[/yellow]",
            f"───────────────────────────",
            f"Will configure:   [bold]{cfg1_lines:,}[/bold]",
            f"Existing MH:      {current_mh1:,}",
            f"Total after push: {current_mh1 + cfg1_lines:,}",
            f"[dim]Limit: {MAX_ESI_INTERFACES:,}[/dim]",
        ]
        right_content = [
            f"[bold]ESI Configuration Summary[/bold]",
            f"───────────────────────────",
            f"RT+VLAN matched:  [green]{shared2:,}[/green]",
            f"Local-only:       [yellow]{local_only2:,}[/yellow]",
            f"───────────────────────────",
            f"Will configure:   [bold]{cfg2_lines:,}[/bold]",
            f"Existing MH:      {current_mh2:,}",
            f"Total after push: {current_mh2 + cfg2_lines:,}",
            f"[dim]Limit: {MAX_ESI_INTERFACES:,}[/dim]",
        ]
        
        # Extract actual configured interfaces from config (parse)
        import re
        ifaces1 = re.findall(r'interface (ph\S+)', device_configs.get(h1, ""))
        ifaces2 = re.findall(r'interface (ph\S+)', device_configs.get(h2, ""))
        
        if ifaces1:
            left_content.append("")
            left_content.append(f"[cyan]Range:[/cyan] {ifaces1[0]} → {ifaces1[-1]}")
        
        if ifaces2:
            right_content.append("")
            right_content.append(f"[cyan]Range:[/cyan] {ifaces2[0]} → {ifaces2[-1]}")
        
        display_split_view(h1, left_content, h2, right_content)
    
    # Show config preview option
    console.print("\n[bold]Push Options:[/bold]")
    console.print("  [1] Push to ALL devices simultaneously")
    for i, dev in enumerate(multi_ctx.devices, 2):
        console.print(f"  [{i}] Push to {dev.hostname} only")
    console.print("  [V] View full config preview")
    console.print("  [B] Cancel")
    
    choices = ["1", "v", "V", "b", "B"] + [str(i) for i in range(2, len(multi_ctx.devices) + 2)]
    push_choice = Prompt.ask("Select", choices=choices, default="1").lower()
    
    if push_choice == "v":
        # Show full config preview for first device
        sample_config = device_configs.get(multi_ctx.devices[0].hostname, "")
        lines = sample_config.split('\n')
        console.print(f"\n[bold cyan]Config Preview ({multi_ctx.devices[0].hostname}):[/bold cyan]")
        console.print("[dim]First 30 lines:[/dim]")
        for line in lines[:30]:
            console.print(f"  [cyan]{line}[/cyan]")
        if len(lines) > 30:
            console.print(f"  [dim]... ({len(lines) - 30} more lines)[/dim]")
        console.print(f"\n[dim]Last 10 lines:[/dim]")
        for line in lines[-10:]:
            console.print(f"  [cyan]{line}[/cyan]")
        console.print(f"\n[bold]Total: {len(lines)} lines[/bold]")
        
        # Ask again
        push_choice = Prompt.ask("\nPush now? [1=All/B=Cancel]", choices=["1", "b", "B"], default="1").lower()
    
    if push_choice == "b":
        console.print("[yellow]Cancelled[/yellow]")
        return False
    
    # Determine which devices to push to
    if push_choice == "1":
        devices_to_push = multi_ctx.devices
    else:
        idx = int(push_choice) - 2
        devices_to_push = [multi_ctx.devices[idx]]
    
    # Ask for dry run
    dry_run = not Confirm.ask("Commit configuration?", default=True)
    
    # Push to devices in PARALLEL with progress tracking
    from .config_pusher import ConfigPusher
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
    from rich.live import Live
    from rich.table import Table as RichTable
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    
    # Calculate estimated time based on line count (approx 1 line per 0.05 seconds)
    total_lines = sum(len(device_configs.get(d.hostname, "").split("\n")) for d in devices_to_push)
    estimated_seconds = max(30, total_lines * 0.05)  # At least 30 seconds
    estimated_mins = estimated_seconds / 60
    
    console.print(f"\n[bold cyan]⏱ Estimated completion time: ~{estimated_mins:.1f} minutes[/bold cyan]")
    console.print(f"[dim]Total config lines: {total_lines:,} across {len(devices_to_push)} devices[/dim]")
    console.print()
    
    # Track progress for each device
    device_progress = {dev.hostname: {"status": "pending", "progress": 0, "message": "", "lines_pushed": 0} 
                      for dev in devices_to_push}
    results = {}
    lock = threading.Lock()
    
    def push_device(dev, config):
        """Push config to a single device with progress tracking."""
        hostname = dev.hostname
        total_cfg_lines = len(config.split("\n"))
        
        def progress_callback(msg, pct):
            with lock:
                device_progress[hostname]["status"] = "pushing"
                device_progress[hostname]["progress"] = pct
                device_progress[hostname]["message"] = msg[:40]
                device_progress[hostname]["lines_pushed"] = int(total_cfg_lines * pct / 100)
        
        try:
            with lock:
                device_progress[hostname]["status"] = "connecting"
                device_progress[hostname]["message"] = "Connecting..."
            
            pusher = ConfigPusher()
            success, message = pusher.push_config_terminal_paste(
                dev, config, dry_run=dry_run,
                progress_callback=progress_callback
            )
            
            with lock:
                if success:
                    device_progress[hostname]["status"] = "success"
                    device_progress[hostname]["progress"] = 100
                    device_progress[hostname]["message"] = "Complete!"
                else:
                    device_progress[hostname]["status"] = "failed"
                    device_progress[hostname]["message"] = message[:40] if message else "Failed"
            
            return hostname, success, message
        except Exception as e:
            with lock:
                device_progress[hostname]["status"] = "error"
                device_progress[hostname]["message"] = str(e)[:40]
            return hostname, False, str(e)
    
    def render_progress_table():
        """Render the progress table for all devices."""
        table = RichTable(box=box.ROUNDED, title="Multi-Device Push Progress", expand=True)
        table.add_column("Device", style="cyan", width=12)
        table.add_column("Status", width=12)
        table.add_column("Progress", width=30)
        table.add_column("Lines", justify="right", width=12)
        table.add_column("Message", width=30)
        
        for dev in devices_to_push:
            h = dev.hostname
            info = device_progress[h]
            
            # Status with color
            status = info["status"]
            if status == "pending":
                status_str = "[dim]⏳ Pending[/dim]"
            elif status == "connecting":
                status_str = "[yellow]🔌 Connecting[/yellow]"
            elif status == "pushing":
                status_str = "[cyan]📤 Pushing[/cyan]"
            elif status == "success":
                status_str = "[green]✓ Success[/green]"
            elif status == "failed":
                status_str = "[red]✗ Failed[/red]"
            else:
                status_str = f"[red]⚠ {status}[/red]"
            
            # Progress bar
            pct = info["progress"]
            filled = int(pct / 5)  # 20 chars total
            bar = "━" * filled + "╺" + "─" * (19 - filled)
            if status == "success":
                bar_str = f"[green]{bar}[/green] {pct}%"
            elif status in ("failed", "error"):
                bar_str = f"[red]{bar}[/red] {pct}%"
            else:
                bar_str = f"[cyan]{bar}[/cyan] {pct}%"
            
            # Lines
            total_lines_dev = len(device_configs.get(h, "").split("\n"))
            lines_str = f"{info['lines_pushed']:,}/{total_lines_dev:,}"
            
            table.add_row(h, status_str, bar_str, lines_str, info["message"])
        
        return table
    
    # Run pushes in parallel with live progress display
    start_time = time.time()
    
    # Use transient=False to prevent screen jumping
    with Live(render_progress_table(), refresh_per_second=4, console=console, transient=False, vertical_overflow="visible") as live:
        with ThreadPoolExecutor(max_workers=len(devices_to_push)) as executor:
            futures = {
                executor.submit(push_device, dev, device_configs.get(dev.hostname, "")): dev
                for dev in devices_to_push
            }
            
            while any(f.running() for f in futures):
                live.update(render_progress_table())
                time.sleep(0.25)
            
            # Collect results
            for future in as_completed(futures):
                hostname, success, message = future.result()
                results[hostname] = (success, message)
            
            # Final update
            live.update(render_progress_table())
    
    elapsed = time.time() - start_time
    success_count = sum(1 for s, _ in results.values() if s)
    
    # Summary
    console.print()
    console.print(f"[bold]═══════════════════════════════════════════════════════════════[/bold]")
    console.print(f"[bold]Completed: {success_count}/{len(devices_to_push)} devices configured[/bold]")
    console.print(f"[dim]Total time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)[/dim]")
    
    for hostname, (success, message) in results.items():
        if success:
            console.print(f"  [green]✓ {hostname}[/green]")
        else:
            # Show full error message, wrap if too long
            console.print(f"  [red]✗ {hostname}:[/red]")
            console.print(f"    [red dim]{message}[/red dim]")
    
    # Prompt user for next action after successful push
    if success_count > 0:
        console.print()
        console.print("[bold]What would you like to do next?[/bold]")
        console.print("  [1] Continue configuring (add more interfaces/services)")
        console.print("  [2] Refresh configs from devices")
        console.print("  [3] Return to multi-device menu")
        console.print("  [B] Exit to main menu")
        
        next_choice = Prompt.ask("Select", choices=["1", "2", "3", "b", "B"], default="3").lower()
        
        if next_choice == "1":
            # Return special value to indicate continue configuring
            return "continue"
        elif next_choice == "2":
            # Refresh configs
            _refresh_multi_device_configs(multi_ctx)
            return True
        elif next_choice == "b":
            return "exit"
        # Default: return to multi-device menu
        return True
    
    return success_count > 0


# =============================================================================
# NETWORK-MAPPER INTEGRATION FUNCTIONS
# =============================================================================

def show_network_mapper_topologies(dm: DeviceManager) -> Optional[Tuple[List[Device], Optional['MultiDeviceContext']]]:
    """
    Show available topologies from network-mapper and allow device import.
    
    Args:
        dm: DeviceManager for adding/updating devices
        
    Returns:
        Tuple of (selected_devices, multi_ctx) or None if cancelled
    """
    if not NETWORK_MAPPER_AVAILABLE:
        console.print("[red]Network-mapper client not available[/red]")
        return None
    
    try:
        mapper_client = get_mapper_client()
        
        console.print("\n[dim]Connecting to network-mapper...[/dim]")
        
        # Retry connection up to 3 times with better error handling
        topologies = None
        last_error = None
        for attempt in range(3):
            try:
                topologies = mapper_client.list_topologies()
                if topologies:
                    break
            except Exception as conn_err:
                last_error = conn_err
                error_msg = str(conn_err)
                # Suppress verbose httpx errors
                if "RemoteProtocolError" in error_msg or "disconnected" in error_msg.lower():
                    if attempt < 2:
                        console.print(f"[yellow]Connection attempt {attempt + 1}/3 - server busy, retrying...[/yellow]")
                    else:
                        console.print(f"[red]Network-mapper server not responding after 3 attempts[/red]")
                        console.print("[dim]Make sure the MCP server is running on your Mac (192.168.174.88:8080)[/dim]")
                        return None
                elif attempt < 2:
                    console.print(f"[yellow]Attempt {attempt + 1}/3 failed: {error_msg[:50]}...[/yellow]")
                import time
                time.sleep(1.5 * (attempt + 1))  # Increasing backoff
        
        if not topologies and last_error:
            console.print(f"[red]Failed to connect: {str(last_error)[:80]}[/red]")
            return None
        
        if not topologies:
            console.print("[yellow]No topologies found in network-mapper[/yellow]")
            return None
        
        # Display topologies table
        table = Table(title="Network Mapper Topologies", box=box.ROUNDED)
        table.add_column("#", style="dim", width=5)
        table.add_column("Topology", style="cyan", width=20)
        table.add_column("Devices", style="green", justify="center", width=10)
        table.add_column("Device List", style="dim", width=50)
        
        for i, topo in enumerate(topologies, 1):
            device_names = [mapper_client._extract_hostname(d.name) for d in topo.devices]
            if len(device_names) > 3:
                device_list = ", ".join(device_names[:3]) + f" +{len(device_names) - 3} more"
            else:
                device_list = ", ".join(device_names)
            
            table.add_row(str(i), topo.name, str(len(topo.devices)), device_list)
        
        console.print(table)
        
        # Options
        console.print("\n[bold]Options:[/bold]")
        console.print("  Enter topology number to import")
        console.print("  [A] Show all devices across all topologies")
        console.print("  [B] Back")
        
        choices = [str(i) for i in range(1, len(topologies) + 1)] + ["a", "A", "b", "B"]
        choice = Prompt.ask("Select topology", choices=choices, default="1").lower()
        
        if choice == "b":
            return None
        
        if choice == "a":
            # Show all devices across all topologies
            all_devices = []
            for topo in topologies:
                for dev in topo.devices:
                    dev.topology_name = topo.name
                    all_devices.append((topo.name, dev))
            return _show_topology_device_selection(dm, mapper_client, all_devices, "All Topologies")
        
        # Selected specific topology
        topo_idx = int(choice) - 1
        selected_topo = topologies[topo_idx]
        devices_with_topo = [(selected_topo.name, dev) for dev in selected_topo.devices]
        
        return _show_topology_device_selection(dm, mapper_client, devices_with_topo, selected_topo.name)
        
    except Exception as e:
        console.print(f"[red]Network-mapper error: {e}[/red]")
        return None


def _show_topology_device_selection(
    dm: DeviceManager,
    mapper_client: 'NetworkMapperClient',
    devices_list: List[tuple],
    topology_name: str
) -> Optional[Tuple[List[Device], Optional['MultiDeviceContext']]]:
    """
    Show device selection for a topology and handle import.
    
    Args:
        dm: DeviceManager
        mapper_client: NetworkMapperClient
        devices_list: List of (topology_name, TopologyDevice) tuples
        topology_name: Name for display
        
    Returns:
        Tuple of (selected_devices, multi_ctx) or None
    """
    # Use cached topology data instead of fetching again (much faster!)
    # The topology listing already has system_type, version, status
    device_info_cache = {}
    
    # Check which devices are already in SCALER
    existing_devices = {d.hostname: d for d in dm.list_devices()}
    
    # Display devices with enriched info
    table = Table(title=f"Devices in {topology_name}", box=box.ROUNDED)
    table.add_column("#", style="dim", width=5)
    table.add_column("Device", style="cyan", width=25)
    table.add_column("System Type", style="magenta", width=15)
    table.add_column("Version", style="dim", width=20)
    table.add_column("Status", style="green", width=12)
    table.add_column("In SCALER", style="yellow", width=10)
    
    for i, (topo_name, dev) in enumerate(devices_list, 1):
        hostname = mapper_client._extract_hostname(dev.name)
        
        # Use topology data directly (already cached, no network calls needed)
        system_type = dev.system_type if dev.system_type and dev.system_type != "unknown" else "unknown"
        version = dev.version if dev.version and dev.version != "Unknown" else "Unknown"
        status = dev.status if dev.status and dev.status != "Unknown" else "Unknown"
        
        if len(version) > 20:
            version = version[:17] + "..."
        
        in_scaler = "✓" if hostname in existing_devices else "—"
        
        table.add_row(
            str(i),
            f"{hostname}\n[dim]{topo_name}[/dim]",
            system_type,
            version,
            status,
            in_scaler
        )
    
    console.print(table)
    
    # Count devices already in SCALER
    devices_in_scaler = [(t, d) for t, d in devices_list 
                         if mapper_client._extract_hostname(d.name) in existing_devices]
    devices_not_in_scaler = [(t, d) for t, d in devices_list 
                              if mapper_client._extract_hostname(d.name) not in existing_devices]
    
    all_in_scaler = len(devices_in_scaler) == len(devices_list)
    none_in_scaler = len(devices_in_scaler) == 0
    
    # Smart menu based on what's already in SCALER
    valid_choices = ["b", "B"]
    default_choice = "s" if all_in_scaler else "a"
    
    if all_in_scaler:
        # ALL devices already in SCALER - show sync as primary
        console.print(f"\n[bold green]✓ All {len(devices_list)} devices already in SCALER[/bold green]")
        console.print("\n[bold]Options:[/bold]")
        console.print("  [S] [green]Sync configs[/green] - Refresh configs via SSH")
        console.print("  [B] Back")
        valid_choices.extend(["s", "S"])
    elif none_in_scaler:
        # NO devices in SCALER - show import options only
        console.print("\n[bold]Import Options:[/bold]")
        console.print("  [A] Import ALL devices")
        console.print("  Enter device numbers (comma-separated, e.g., 1,2,3)")
        console.print("  [B] Back")
        valid_choices.extend(["a", "A"])
        # Also allow numeric selections
        for i in range(1, len(devices_list) + 1):
            valid_choices.append(str(i))
    else:
        # SOME devices in SCALER - show full menu
        console.print(f"\n[dim]{len(devices_in_scaler)}/{len(devices_list)} devices already in SCALER[/dim]")
        console.print("\n[bold]Options:[/bold]")
        console.print(f"  [A] Import ALL devices ({len(devices_not_in_scaler)} new)")
        console.print("  Enter device numbers (comma-separated, e.g., 1,2,3)")
        console.print(f"  [S] Sync existing ({len(devices_in_scaler)} devices)")
        console.print("  [B] Back")
        valid_choices.extend(["a", "A", "s", "S"])
        for i in range(1, len(devices_list) + 1):
            valid_choices.append(str(i))
    
    choice = Prompt.ask("Select", default=default_choice).lower()
    
    if choice == "b":
        return None
    
    if choice == "r":
        # Refresh devices from Network Mapper
        console.print("\n[bold]Refresh Options:[/bold]")
        console.print("  [A] Refresh ALL devices")
        console.print("  [U] Refresh only Unknown devices")
        console.print("  Enter device numbers (comma-separated, e.g., 1,2,3)")
        console.print("  [B] Back")
        
        refresh_choice = Prompt.ask("Select", default="u" if unknown_devices else "a").lower()
        
        if refresh_choice == "b":
            # Re-display the device list
            return _show_topology_devices(mapper_client, dm, devices_list, topology_name)
        
        if refresh_choice == "a":
            refresh_indices = list(range(len(devices_list)))
        elif refresh_choice == "u":
            refresh_indices = [i for i, (t, d) in enumerate(devices_list) 
                              if (t, d) in unknown_devices]
        else:
            try:
                refresh_indices = [int(x.strip()) - 1 for x in refresh_choice.split(",")]
                refresh_indices = [i for i in refresh_indices if 0 <= i < len(devices_list)]
            except ValueError:
                console.print("[red]Invalid selection[/red]")
                return _show_topology_devices(mapper_client, dm, devices_list, topology_name)
        
        if not refresh_indices:
            console.print("[yellow]No devices to refresh[/yellow]")
            return _show_topology_devices(mapper_client, dm, devices_list, topology_name)
        
        # Refresh selected devices
        console.print(f"\n[dim]Refreshing {len(refresh_indices)} device(s) from Network Mapper...[/dim]")
        refreshed_count = 0
        failed_count = 0
        
        with console.status("[cyan]Refreshing devices...[/cyan]") as status:
            for idx in refresh_indices:
                topo_name, dev = devices_list[idx]
                hostname = mapper_client._extract_hostname(dev.name)
                status.update(f"[cyan]Refreshing {hostname}...[/cyan]")
                
                try:
                    success = mapper_client.refresh_device(dev.name)
                    if success:
                        console.print(f"  [green]✓[/green] {hostname}")
                        refreshed_count += 1
                    else:
                        console.print(f"  [yellow]⚠[/yellow] {hostname} - refresh returned no success")
                        failed_count += 1
                except Exception as e:
                    console.print(f"  [red]✗[/red] {hostname} - {e}")
                    failed_count += 1
        
        console.print(f"\n[green]Refreshed {refreshed_count} device(s)[/green]", end="")
        if failed_count:
            console.print(f", [yellow]{failed_count} failed[/yellow]")
        else:
            console.print()
        
        # Re-display with updated info
        console.print("[dim]Re-fetching device info...[/dim]")
        return _show_topology_devices(mapper_client, dm, devices_list, topology_name)
    
    if choice == "s":
        # Sync configs only for existing devices
        if not devices_in_scaler:
            console.print("[yellow]No devices from this topology are in SCALER yet.[/yellow]")
            return None
        
        synced = _sync_topology_configs(dm, mapper_client, devices_in_scaler, device_info_cache)
        if synced:
            return (synced, None)
        return None
    
    # Determine which devices to import
    if choice == "a":
        selected_indices = list(range(len(devices_list)))
    else:
        try:
            selected_indices = [int(x.strip()) - 1 for x in choice.split(",")]
            selected_indices = [i for i in selected_indices if 0 <= i < len(devices_list)]
        except ValueError:
            console.print("[red]Invalid selection[/red]")
            return None
    
    if not selected_indices:
        console.print("[red]No devices selected[/red]")
        return None
    
    # Ask for SSH credentials
    console.print("\n[bold]SSH Credentials:[/bold]")
    console.print("  [1] Use default credentials (dnroot/dnroot)")
    console.print("  [2] Enter custom credentials")
    
    cred_choice = Prompt.ask("Select", choices=["1", "2"], default="1")
    
    if cred_choice == "1":
        username = "dnroot"
        password = "dnroot"
    else:
        username = Prompt.ask("Username", default="dnroot")
        password = Prompt.ask("Password", password=True)
    
    # Import selected devices
    imported_devices = []
    console.print(f"\n[bold]Importing {len(selected_indices)} device(s)...[/bold]")
    
    for idx in selected_indices:
        topo_name, dev = devices_list[idx]
        hostname = mapper_client._extract_hostname(dev.name)
        
        console.print(f"  • [cyan]{hostname}[/cyan]... ", end="")
        
        # Check if already exists
        existing = existing_devices.get(hostname)
        
        # Try to get connection target (IP or serial number) from network-mapper
        info = device_info_cache.get(dev.name, {})
        config_text = info.get('config')
        connection_target = None
        
        # Check if config is truncated
        is_config_truncated = config_text and '... (truncated,' in config_text
        
        # Strategy 1: Extract mgmt IP from cached config (if not truncated)
        if config_text and not is_config_truncated:
            connection_target = mapper_client.extract_mgmt_ip_from_config(config_text)
            if connection_target:
                console.print(f"[green]mgmt IP: {connection_target}[/green] ", end="")
        
        # Strategy 2: Get connection target (IP or SN) from network-mapper
        if not connection_target:
            console.print(f"[dim]finding connection target...[/dim] ", end="")
            try:
                connection_target = mapper_client.get_device_connection_target(dev.name)
                if connection_target:
                    # Check if it looks like a serial number vs IP
                    if re.match(r'\d+\.\d+\.\d+\.\d+', connection_target):
                        console.print(f"[green]IP: {connection_target}[/green] ", end="")
                    else:
                        console.print(f"[cyan]SN: {connection_target}[/cyan] ", end="")
            except Exception:
                pass
        
        # Strategy 3: Try to extract serial from device name pattern
        if not connection_target:
            # Pattern for serial numbers in device names (e.g., WK31C8V10001BP2)
            sn_match = re.search(r'([A-Z]{2}[A-Z0-9]{10,})', dev.name)
            if sn_match:
                connection_target = sn_match.group(1)
                console.print(f"[cyan]SN from name: {connection_target}[/cyan] ", end="")
        
        # If still nothing found, ask user
        if not connection_target:
            default_val = existing.ip if existing else hostname
            console.print(f"\n    [yellow]Enter IP or Serial Number for SSH:[/yellow]")
            connection_target = Prompt.ask(f"    Target for {hostname}", default=default_val)
            if not connection_target:
                connection_target = hostname
        
        if existing:
            # Update existing device
            existing.ip = connection_target
            existing.username = username
            existing.password = Device.encode_password(password)
            dm.update_device(existing)
            imported_devices.append(existing)
            console.print("[green]updated[/green]")
        else:
            # Create new device using DeviceManager
            device_id = hostname.lower().replace(" ", "_").replace("-", "_")
            new_device = dm.add_device(
                device_id=device_id,
                hostname=hostname,
                ip=connection_target,
                username=username,
                password=password,  # add_device handles encoding
                platform="NCP"
            )
            imported_devices.append(new_device)
            existing_devices[hostname] = new_device  # Update cache
            console.print("[green]added[/green]")
    
    if not imported_devices:
        console.print("[yellow]No devices were imported[/yellow]")
        return None
    
    # Offer to sync configs from network-mapper
    if Confirm.ask("Sync running configs from network-mapper?", default=True):
        selected_for_sync = [(devices_list[i][0], devices_list[i][1]) for i in selected_indices]
        _sync_topology_configs(dm, mapper_client, selected_for_sync, device_info_cache)
    
    console.print(f"\n[green]✓ Imported {len(imported_devices)} device(s)[/green]")
    
    return (imported_devices, None)


def _sync_topology_configs(
    dm: DeviceManager,
    mapper_client: 'NetworkMapperClient',
    devices_list: List[tuple],
    device_info_cache: dict
) -> Optional[List[Device]]:
    """
    Sync configs for devices from network-mapper cache.
    Creates proper SCALER-format headers for compatibility with MultiDeviceContext.
    
    Args:
        dm: DeviceManager
        mapper_client: NetworkMapperClient
        devices_list: List of (topology_name, TopologyDevice) tuples
        device_info_cache: Cached device info from batch_get_device_info
        
    Returns:
        List of synced Device objects or None
    """
    from pathlib import Path
    
    synced_devices = []
    config_base = Path(__file__).parent.parent / "db" / "configs"
    parser = ConfigParser()
    skip_all_truncated = False  # Flag to skip all truncated configs
    
    console.print("\n[bold]Preparing SSH sync...[/bold]")
    
    # ALL devices need full config via SSH - use existing SCALER device info
    all_devices = []
    
    for i, (topo_name, dev) in enumerate(devices_list, 1):
        hostname = mapper_client._extract_hostname(dev.name)
        device_obj = dm.get_device(hostname)
        if not device_obj:
            console.print(f"  [{i}/{len(devices_list)}] [dim]{hostname}[/dim] - not in SCALER, skipping")
            continue
        
        # Device already in SCALER - use existing IP, no network-mapper calls needed
        console.print(f"  [{i}/{len(devices_list)}] {hostname}: [cyan]{device_obj.ip}[/cyan]")
        
        # Use cached system info if available for operational.json
        sys_info = None
        if device_info_cache and dev.name in device_info_cache:
            cached_info = device_info_cache.get(dev.name, {})
            sys_info = cached_info.get('system_info', {})
        
        # Create/update operational.json from cached info (if available)
        try:
            if sys_info:
                from .utils import get_device_config_dir
                from datetime import datetime
                import json
                
                config_dir = get_device_config_dir(hostname)
                config_dir.mkdir(parents=True, exist_ok=True)
                ops_file = config_dir / "operational.json"
                
                # Build operational data from cached info
                ops_data = {
                    "last_sync": datetime.now().isoformat(),
                    "sync_source": "network-mapper",
                    "system_type": sys_info.get("system_type", "N/A"),
                    "dnos_version": sys_info.get("version", "N/A"),
                    "system_uptime": sys_info.get("uptime", "N/A"),
                    "mgmt_ip": device_obj.ip,
                    "status": sys_info.get("status", "N/A"),
                    "bgp_nsr": sys_info.get("bgp_nsr", "N/A"),
                }
                
                # Load existing ops data to preserve fields
                if ops_file.exists():
                    try:
                        with open(ops_file) as f:
                            existing = json.load(f)
                        # Update only new fields, preserve existing
                        for key, val in existing.items():
                            if key not in ops_data:
                                ops_data[key] = val
                    except Exception:
                        pass
                
                with open(ops_file, 'w') as f:
                    json.dump(ops_data, f, indent=2)
        except Exception:
            pass
        
        # Serial number not needed for sync - we have the IP
        serial = None
        all_devices.append((topo_name, dev, device_obj, serial))
    
    if not all_devices:
        console.print("[yellow]No devices to sync[/yellow]")
        return None
    
    # Show devices and their connection targets, then fetch automatically
    console.print(f"\n[bold]Fetching configs via SSH for {len(all_devices)} device(s)...[/bold]")
    for topo_name, dev, device_obj, serial in all_devices:
        # Determine connection target
        conn_target = device_obj.ip if device_obj.ip and device_obj.ip != device_obj.hostname else serial
        if conn_target:
            console.print(f"  • {device_obj.hostname}: [cyan]{conn_target}[/cyan]")
        else:
            console.print(f"  • {device_obj.hostname}: [yellow]need IP[/yellow]")
    
    # Fetch ALL configs in parallel via SSH
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    
    console.print()
    
    fetch_results = {}
    fetch_lock = threading.Lock()
    
    def fetch_device_config(args):
        topo_name, dev, device_obj, serial = args
        hostname = device_obj.hostname
        
        # device_obj.ip should already be the mgmt IP (set earlier in the flow)
        # Only use IP addresses, not serial numbers (DNS doesn't resolve serials here)
        ssh_target = device_obj.ip
        
        # Validate it's an IP address, not a hostname/serial
        if not ssh_target or not re.match(r'^\d+\.\d+\.\d+\.\d+$', ssh_target):
            return (hostname, False, 0, f"No valid IP - have '{ssh_target}'")
        
        try:
            extractor = ConfigExtractor()
            device_config = extractor.extract_running_config(device_obj, save_to_db=True)
            
            if device_config:
                return (hostname, True, len(device_config.raw_config), ssh_target)
            else:
                return (hostname, False, 0, "No config returned")
        except Exception as e:
            return (hostname, False, 0, str(e))
    
    failed_devices = []
    synced_devices = []
    
    with ThreadPoolExecutor(max_workers=min(4, len(all_devices))) as executor:
        futures = {executor.submit(fetch_device_config, args): args for args in all_devices}
        
        for future in as_completed(futures):
            args = futures[future]
            hostname = args[2].hostname
            try:
                result = future.result(timeout=300)  # 5 min for large configs
                result_hostname, success, size, error = result
                
                if success:
                    console.print(f"  ✓ [green]{hostname}[/green]: {size:,} bytes")
                    synced_devices.append(args[2])
                else:
                    console.print(f"  ✗ [yellow]{hostname}[/yellow]: {error}")
                    failed_devices.append(args)
            except Exception as e:
                console.print(f"  ✗ [yellow]{hostname}[/yellow]: {e}")
                failed_devices.append(args)
    
    # Handle failed devices - prompt for management IP
    if failed_devices:
        console.print(f"\n[bold yellow]⚠ {len(failed_devices)} device(s) need management IP[/bold yellow]")
        console.print("[dim]Serial number DNS doesn't work from this machine.[/dim]")
        console.print("[dim]Find the IP from: Device console (show interface mgmt0) or DNaaS portal[/dim]\n")
        
        for topo_name, dev, device_obj, serial in failed_devices:
            hostname = device_obj.hostname
            console.print(f"\n  [cyan]{hostname}[/cyan] (serial: [yellow]{serial}[/yellow])")
            console.print(f"    💡 On device console: [bold]show interface mgmt0 | include ipv4[/bold]")
            
            ip_input = Prompt.ask(f"    Enter mgmt IP [S]kip", default="")
            
            if not ip_input or ip_input.lower() == 's':
                console.print(f"    [dim]Skipped - sync later with [N] option[/dim]")
                continue
            
            # Validate IP format
            if not re.match(r'^\d+\.\d+\.\d+\.\d+$', ip_input):
                console.print(f"    [yellow]Invalid IP format, skipping[/yellow]")
                continue
            
            # Try with the provided IP
            console.print(f"    Connecting to {ip_input}...", end=" ")
            try:
                device_obj.ip = ip_input
                dm.update_device(device_obj)  # Save the IP permanently
                
                extractor = ConfigExtractor()
                device_config = extractor.extract_running_config(device_obj, save_to_db=True)
                
                if device_config:
                    console.print(f"[green]✓ {len(device_config.raw_config):,} bytes[/green]")
                    console.print(f"    [dim]IP saved - won't ask again[/dim]")
                    synced_devices.append(device_obj)
                else:
                    console.print("[red]Failed[/red]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
    
    # All devices processed via SSH - configs saved by ConfigExtractor with full headers
    
    if synced_devices:
        console.print(f"\n[green]✓ Synced configs for {len(synced_devices)} device(s)[/green]")
    
    return synced_devices if synced_devices else None


def _sync_configs_from_network_mapper(multi_ctx: 'MultiDeviceContext', dm: DeviceManager):
    """
    Sync configs from network-mapper for devices in multi-device context.
    
    Args:
        multi_ctx: MultiDeviceContext with devices
        dm: DeviceManager
    """
    if not NETWORK_MAPPER_AVAILABLE:
        console.print("[red]Network-mapper not available[/red]")
        return
    
    try:
        mapper_client = get_mapper_client()
        
        console.print("\n[dim]Fetching configs from network-mapper...[/dim]")
        
        # Get device names for batch fetch
        device_names = [d.hostname for d in multi_ctx.devices]
        
        # Search for matching devices in network-mapper
        all_devices = mapper_client.list_devices()
        name_mapping = {}  # SCALER hostname -> network-mapper device name
        
        for dev in all_devices:
            hostname = mapper_client._extract_hostname(dev.name)
            if hostname in device_names:
                name_mapping[hostname] = dev.name
        
        if not name_mapping:
            console.print("[yellow]No matching devices found in network-mapper[/yellow]")
            return
        
        # Batch fetch
        mapper_names = list(name_mapping.values())
        device_info_cache = mapper_client.batch_get_device_info(mapper_names)
        
        # Build devices_list for sync
        devices_list = []
        for hostname, mapper_name in name_mapping.items():
            # Create a TopologyDevice-like object
            class TempDevice:
                def __init__(self, name):
                    self.name = name
            devices_list.append(("network-mapper", TempDevice(mapper_name)))
        
        # Sync configs
        _sync_topology_configs(dm, mapper_client, devices_list, device_info_cache)
        
        # Refresh multi_ctx after sync
        console.print("\n[dim]Refreshing device context...[/dim]")
        multi_ctx.discover_all()
        
    except Exception as e:
        console.print(f"[red]Error syncing from network-mapper: {e}[/red]")


def delete_devices_from_cache(dm: DeviceManager) -> bool:
    """
    Interactively delete device(s) from the device cache.
    
    Removes:
    - Device entry from db/devices.json
    - Cached configs from db/configs/{hostname}/
    - Optionally: History from db/history/{hostname}/
    
    Args:
        dm: DeviceManager instance
        
    Returns:
        True if any devices were deleted
    """
    import shutil
    
    devices = dm.list_devices()
    
    if not devices:
        console.print("[yellow]No devices in cache to delete.[/yellow]")
        return False
    
    while True:
        # Display devices table with checkboxes
        console.print("\n[bold red]🗑️ Delete Devices from Cache[/bold red]")
        console.print("[dim]Select devices to permanently remove from cache[/dim]\n")
        
        table = Table(box=box.ROUNDED)
        table.add_column("#", style="dim", width=3)
        table.add_column("ID", style="cyan")
        table.add_column("Hostname", style="green")
        table.add_column("IP", style="yellow")
        table.add_column("Type", style="magenta")
        table.add_column("Config Size", style="dim")
        table.add_column("Status", style="dim")
        
        for i, dev in enumerate(devices, 1):
            # Check config cache size
            config_dir = Path(f"/home/dn/SCALER/db/configs/{dev.hostname}")
            cache_size = "None"
            if config_dir.exists():
                total_size = sum(f.stat().st_size for f in config_dir.rglob('*') if f.is_file())
                if total_size > 1024 * 1024:
                    cache_size = f"{total_size / (1024 * 1024):.1f} MB"
                elif total_size > 1024:
                    cache_size = f"{total_size / 1024:.1f} KB"
                else:
                    cache_size = f"{total_size} B"
            
            # Get system type and recovery status from operational data if available
            system_type = dev.platform.value
            status_str = "[green]OK[/green]"
            try:
                op_file = Path(f"/home/dn/SCALER/db/configs/{dev.hostname}/operational.json")
                if op_file.exists():
                    with open(op_file) as f:
                        op_data = json.load(f)
                        if op_data.get('system_type'):
                            system_type = op_data['system_type']
                        dnos_version = op_data.get('dnos_version', '')
                        if op_data.get('recovery_mode_detected'):
                            status_str = "[bold red]RECOVERY[/bold red]"
                        elif dnos_version in ('N/A', '', None) or not dnos_version:
                            # DNOS version N/A but not detected as recovery - likely GI mode
                            status_str = "[cyan]? GI/No DNOS[/cyan]"
            except Exception:
                pass
            
            table.add_row(str(i), dev.id, dev.hostname, dev.ip or "-", system_type, cache_size, status_str)
        
        console.print(table)
        console.print("\n[bold]Options:[/bold]")
        console.print("  [dim]Enter device numbers separated by commas (e.g., 1,3,5)[/dim]")
        console.print("  [A] Delete ALL devices")
        console.print("  [B] Back/Cancel")
        
        # Build valid choices
        choices = [str(i) for i in range(1, len(devices) + 1)]
        
        selection = Prompt.ask("Select devices to delete [B]ack").strip()
        
        if not selection or selection.lower() == "b":
            return False
        
        # Parse selection
        to_delete = []
        if selection.lower() == "a":
            to_delete = list(devices)
        else:
            # Parse comma-separated numbers
            try:
                indices = [int(x.strip()) for x in selection.split(",") if x.strip().isdigit()]
                for idx in indices:
                    if 1 <= idx <= len(devices):
                        to_delete.append(devices[idx - 1])
            except ValueError:
                console.print("[red]Invalid selection. Use numbers separated by commas.[/red]")
                continue
        
        if not to_delete:
            console.print("[yellow]No valid devices selected.[/yellow]")
            continue
        
        # Confirmation
        console.print(f"\n[bold red]⚠️ About to delete {len(to_delete)} device(s):[/bold red]")
        for dev in to_delete:
            console.print(f"  • {dev.hostname} ({dev.id})")
        
        console.print("\n[dim]This will remove:[/dim]")
        console.print("  • Device entry from devices.json")
        console.print("  • Cached configs from db/configs/{hostname}/")
        
        # Ask about history
        delete_history = Confirm.ask("Also delete history (db/history/{hostname})?", default=False)
        
        if not Confirm.ask(f"\n[bold red]Permanently delete {len(to_delete)} device(s)?[/bold red]", default=False):
            console.print("[yellow]Deletion cancelled.[/yellow]")
            continue
        
        # Perform deletion
        deleted_count = 0
        
        # Load or create hostname history file (to remember hostnames for re-adding)
        hostname_history_path = Path("/home/dn/SCALER/db/hostname_history.json")
        hostname_history = {}
        try:
            if hostname_history_path.exists():
                with open(hostname_history_path, 'r') as f:
                    hostname_history = json.load(f)
        except Exception:
            pass
        
        for dev in to_delete:
            hostname = dev.hostname
            device_id = dev.id
            
            console.print(f"\n[cyan]Deleting {hostname}...[/cyan]")
            
            # 0. Save hostname mapping for later re-discovery
            # Try to get serial number from operational.json
            serial_number = None
            try:
                op_file = Path(f"/home/dn/SCALER/db/configs/{hostname}/operational.json")
                if op_file.exists():
                    with open(op_file) as f:
                        op_data = json.load(f)
                        serial_number = op_data.get('serial_number') or op_data.get('serial')
            except Exception:
                pass
            
            # Save mapping by both IP and serial number (if available)
            if dev.ip:
                hostname_history[dev.ip] = {
                    'hostname': hostname,
                    'device_id': device_id,
                    'deleted_at': datetime.now().isoformat()
                }
            if serial_number:
                hostname_history[serial_number] = {
                    'hostname': hostname,
                    'device_id': device_id,
                    'deleted_at': datetime.now().isoformat()
                }
            
            # 1. Remove from devices.json
            if dm.remove_device(device_id):
                console.print(f"  [green]✓[/green] Removed from devices.json")
            else:
                console.print(f"  [yellow]⚠[/yellow] Device not found in devices.json")
            
            # 2. Delete config cache
            config_dir = Path(f"/home/dn/SCALER/db/configs/{hostname}")
            if config_dir.exists():
                try:
                    shutil.rmtree(config_dir)
                    console.print(f"  [green]✓[/green] Deleted db/configs/{hostname}/")
                except Exception as e:
                    console.print(f"  [red]✗[/red] Failed to delete configs: {e}")
            else:
                console.print(f"  [dim]  No config cache found[/dim]")
            
            # 3. Delete history if requested
            if delete_history:
                history_dir = Path(f"/home/dn/SCALER/db/history/{hostname}")
                if history_dir.exists():
                    try:
                        shutil.rmtree(history_dir)
                        console.print(f"  [green]✓[/green] Deleted db/history/{hostname}/")
                    except Exception as e:
                        console.print(f"  [red]✗[/red] Failed to delete history: {e}")
                else:
                    console.print(f"  [dim]  No history found[/dim]")
            
            # 4. Clear any alerts for this device
            alerts_file = Path("/home/dn/SCALER/db/alerts.json")
            try:
                if alerts_file.exists():
                    with open(alerts_file) as af:
                        alert_data = json.load(af)
                    before = len(alert_data.get('alerts', []))
                    alert_data['alerts'] = [
                        a for a in alert_data.get('alerts', [])
                        if a.get('device') != hostname
                    ]
                    if len(alert_data['alerts']) < before:
                        with open(alerts_file, 'w') as af:
                            json.dump(alert_data, af, indent=2)
                        console.print(f"  [green]✓[/green] Cleared alerts for {hostname}")
            except Exception:
                pass
            
            deleted_count += 1
        
        # Save hostname history for future re-discovery
        try:
            hostname_history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(hostname_history_path, 'w') as f:
                json.dump(hostname_history, f, indent=2)
            console.print(f"\n[dim]💾 Saved hostname mappings for future re-discovery[/dim]")
        except Exception as e:
            console.print(f"[dim]Could not save hostname history: {e}[/dim]")
        
        console.print(f"\n[bold green]✓ Deleted {deleted_count} device(s) from cache[/bold green]")
        
        # Refresh device list
        devices = dm.list_devices()
        
        if not devices:
            console.print("[dim]No more devices in cache.[/dim]")
            return True
        
        if not Confirm.ask("Delete more devices?", default=False):
            return True
    
    return False


def edit_device_in_db(dm: DeviceManager, devices: List[Device]) -> bool:
    """
    Interactively edit a device entry in the database.
    
    Allows changing:
    - Hostname (renames config directory too)
    - IP address
    - Description
    
    Args:
        dm: DeviceManager instance
        devices: List of Device objects
        
    Returns:
        True if device was updated
    """
    if not devices:
        console.print("[yellow]No devices to edit.[/yellow]")
        return False
    
    console.print("\n[bold cyan]✏️ Edit Device[/bold cyan]")
    console.print("[dim]Select device to edit[/dim]\n")
    
    # Show device list
    for i, dev in enumerate(devices, 1):
        console.print(f"  [{i}] {dev.hostname} - {dev.ip or 'N/A'}")
    console.print("  [B] Back")
    
    choices = [str(i) for i in range(1, len(devices) + 1)] + ['b', 'B']
    selection = Prompt.ask("\nDevice to edit", choices=choices, default="1")
    
    if selection.lower() == 'b':
        return False
    
    try:
        idx = int(selection) - 1
        if not (0 <= idx < len(devices)):
            console.print("[red]Invalid selection[/red]")
            return False
    except ValueError:
        return False
    
    device = devices[idx]
    old_hostname = device.hostname
    old_ip = device.ip or ""
    old_desc = device.description or ""
    
    console.print(f"\n[bold]Editing: {old_hostname}[/bold]")
    console.print("[dim](Press Enter to keep current value)[/dim]\n")
    
    # Get new values
    new_hostname = Prompt.ask("Hostname", default=old_hostname)
    new_ip = Prompt.ask("IP Address", default=old_ip)
    new_desc = Prompt.ask("Description", default=old_desc or "")
    
    # Check for changes
    has_changes = (new_hostname != old_hostname or new_ip != old_ip or new_desc != old_desc)
    
    if not has_changes:
        console.print("[dim]No changes made[/dim]")
        return False
    
    # Show diff
    console.print("\n[bold]Changes:[/bold]")
    if new_hostname != old_hostname:
        console.print(f"  Hostname: [red]{old_hostname}[/red] → [green]{new_hostname}[/green]")
    if new_ip != old_ip:
        console.print(f"  IP: [red]{old_ip or '(empty)'}[/red] → [green]{new_ip or '(empty)'}[/green]")
    if new_desc != old_desc:
        console.print(f"  Description: [red]{old_desc or '(empty)'}[/red] → [green]{new_desc or '(empty)'}[/green]")
    
    if not Confirm.ask("\nSave changes?", default=True):
        console.print("[yellow]Cancelled[/yellow]")
        return False
    
    # Load devices.json and update
    devices_file = Path("/home/dn/SCALER/db/devices.json")
    try:
        with open(devices_file) as f:
            data = json.load(f)
        
        # Find and update the device
        devices_list = data.get("devices", data if isinstance(data, list) else [])
        updated = False
        
        for dev_entry in devices_list:
            if dev_entry.get("hostname") == old_hostname or dev_entry.get("id") == device.id:
                dev_entry["hostname"] = new_hostname
                dev_entry["ip"] = new_ip
                if new_desc:
                    dev_entry["description"] = new_desc
                elif "description" in dev_entry and not new_desc:
                    dev_entry["description"] = None
                # Also update device ID when hostname changes (keeps ID in sync)
                if new_hostname != old_hostname:
                    old_id = dev_entry.get("id", "")
                    new_id = new_hostname.lower().replace(' ', '_').replace('-', '_').replace('.', '_')
                    dev_entry["id"] = new_id
                    console.print(f"  Device ID: [red]{old_id}[/red] → [green]{new_id}[/green]")
                updated = True
                break
        
        if updated:
            # Write back
            if isinstance(data, dict) and "devices" in data:
                data["devices"] = devices_list
            else:
                data = {"devices": devices_list, "settings": data.get("settings", {})}
            
            with open(devices_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            console.print(f"[green]✓[/green] Updated devices.json")
            
            # Rename config directory if hostname changed
            if new_hostname != old_hostname:
                old_config_dir = Path(f"/home/dn/SCALER/db/configs/{old_hostname}")
                new_config_dir = Path(f"/home/dn/SCALER/db/configs/{new_hostname}")
                
                if old_config_dir.exists() and not new_config_dir.exists():
                    try:
                        old_config_dir.rename(new_config_dir)
                        console.print(f"[green]✓[/green] Renamed config directory: {old_hostname} → {new_hostname}")
                    except Exception as e:
                        console.print(f"[yellow]⚠[/yellow] Could not rename config directory: {e}")
                
                # Also rename history directory if exists
                old_history_dir = Path(f"/home/dn/SCALER/db/history/{old_hostname}")
                new_history_dir = Path(f"/home/dn/SCALER/db/history/{new_hostname}")
                
                if old_history_dir.exists() and not new_history_dir.exists():
                    try:
                        old_history_dir.rename(new_history_dir)
                        console.print(f"[green]✓[/green] Renamed history directory: {old_hostname} → {new_hostname}")
                    except Exception as e:
                        console.print(f"[yellow]⚠[/yellow] Could not rename history directory: {e}")
            
            console.print(f"\n[bold green]✓ Device updated successfully[/bold green]")
            return True
        else:
            console.print("[red]Device not found in database[/red]")
            return False
            
    except Exception as e:
        console.print(f"[red]Error saving: {e}[/red]")
        return False


def _get_previous_hostname(target: str, serial_number: str = None) -> Optional[str]:
    """
    Check if we have a previously used hostname for this device.
    
    Looks up by IP address or serial number in hostname_history.json.
    
    Args:
        target: IP address or hostname used for connection
        serial_number: Serial number if known
        
    Returns:
        Previously used hostname, or None
    """
    hostname_history_path = Path("/home/dn/SCALER/db/hostname_history.json")
    try:
        if hostname_history_path.exists():
            with open(hostname_history_path, 'r') as f:
                hostname_history = json.load(f)
            
            # Try serial number first (most reliable)
            if serial_number and serial_number in hostname_history:
                return hostname_history[serial_number].get('hostname')
            
            # Try IP address
            if target in hostname_history:
                return hostname_history[target].get('hostname')
    except Exception:
        pass
    
    return None


def _run_full_discovery(channel, add_line, live, render_panel) -> Dict[str, Any]:
    """
    Run full device discovery - same show commands as monitoring script.
    
    Collects:
    - System: type, uptime, serial, management IP, node counts
    - Versions: DNOS, GI, BaseOS  
    - Routing: Router ID, Local AS, IGP, Label protocol
    - BGP: Neighbor counts
    - Services: FXC, VRF, EVPN, VPWS counts
    - Interfaces: Physical, Bundle, Loopback, IRB, PWHE counts
    - LLDP: Neighbor info
    """
    import re
    
    info = {}
    full_output = ""
    
    # Helper to run command and collect output
    def run_cmd(cmd: str, wait: float = 2.0) -> str:
        channel.send(f"{cmd}\n")
        time.sleep(wait)
        output = ""
        while channel.recv_ready():
            output += channel.recv(65535).decode(errors='ignore')
            time.sleep(0.1)
        return output
    
    # =========================================================================
    # 1. SYSTEM STACK - DNOS/GI/BaseOS versions
    # =========================================================================
    add_line("Fetching system stack versions...", "yellow")
    live.update(render_panel())
    
    stack_output = run_cmd("show system stack | no-more", 2.0)
    full_output += stack_output
    
    # Parse versions from stack table: | Component | HW Model | HW Revision | Revert | Current | Target |
    for line in stack_output.split('\n'):
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 6:
                component = parts[1].upper() if len(parts) > 1 else ""
                target_ver = parts[5] if len(parts) > 5 else ""
                if 'DNOS' in component and target_ver:
                    info['dnos_version'] = target_ver
                elif 'BASEOS' in component and target_ver:
                    info['baseos_version'] = target_ver
                elif component.strip() == 'GI' and target_ver:
                    info['gi_version'] = target_ver
    
    if info.get('dnos_v