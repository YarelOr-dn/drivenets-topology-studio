"""
Main Wizard Functions for the SCALER Wizard.

This module contains the main entry points and helper functions that
orchestrate the wizard flow.
"""

import json
import ipaddress
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.prompt import Prompt

console = Console()


def _get_config_history_path(device_name: str) -> Path:
    """Get path to config history JSON file for a device."""
    from ..utils import get_device_config_dir
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
        'pushed': False
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
                entry['validated'] = True
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
        custom_step: Custom step value
        
    Returns:
        Calculated IP address as string
    """
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
            step = custom_step if custom_step is not None else 1
            new_ip_int = ip_int + (index * step)
            
        elif mode == "per_parent":
            if is_v6:
                new_ip_int = ip_int + (parent_idx * 256) + subif_within_parent
            else:
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
            if custom_step is not None:
                step = custom_step
            elif is_v6:
                step = 2 ** (128 - prefix_len)
            else:
                step = 2 ** (32 - prefix_len)
            new_ip_int = ip_int + (index * step)
            
        else:
            new_ip_int = ip_int + index
        
        # Convert back to string
        if is_v6:
            return str(ipaddress.IPv6Address(new_ip_int))
        else:
            return str(ipaddress.IPv4Address(new_ip_int))
            
    except Exception:
        return base_ip


def _calculate_scale_info(hierarchy_name: str, config_text: str, state) -> Dict[str, Any]:
    """Calculate scale information for a hierarchy.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import _calculate_scale_info as _impl
    return _impl(hierarchy_name, config_text, state)


def show_current_config_summary(*args, **kwargs):
    """Show summary of current configuration.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import show_current_config_summary as _impl
    return _impl(*args, **kwargs)


def select_device(*args, **kwargs):
    """Select a device from the device manager.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import select_device as _impl
    return _impl(*args, **kwargs)


def fetch_current_config(*args, **kwargs):
    """Fetch current configuration from device.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import fetch_current_config as _impl
    return _impl(*args, **kwargs)


def display_hierarchy_config(*args, **kwargs):
    """Display hierarchy configuration.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import display_hierarchy_config as _impl
    return _impl(*args, **kwargs)


def select_configuration_mode(*args, **kwargs):
    """Select configuration mode.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import select_configuration_mode as _impl
    return _impl(*args, **kwargs)


def run_wizard(*args, **kwargs):
    """Run the interactive SCALER wizard.
    
    This function is implemented in the main module.
    """
    from ..interactive_scale import run_wizard as _impl
    return _impl(*args, **kwargs)

