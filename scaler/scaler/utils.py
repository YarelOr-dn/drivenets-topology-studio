"""Utility functions for SCALER."""

from pathlib import Path
from datetime import datetime
from typing import Optional
import pytz


# Base directories
SCALER_DIR = Path(__file__).parent.parent
DB_DIR = SCALER_DIR / "db"
CONFIGS_DIR = DB_DIR / "configs"
HISTORY_DIR = DB_DIR / "history"


def get_device_config_dir(hostname: str) -> Path:
    """Get the configuration directory for a device.
    
    Args:
        hostname: Device hostname
        
    Returns:
        Path to device config directory
    """
    config_dir = CONFIGS_DIR / hostname
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_device_history_dir(hostname: str) -> Path:
    """Get the history directory for a device.
    
    Args:
        hostname: Device hostname
        
    Returns:
        Path to device history directory
    """
    history_dir = HISTORY_DIR / hostname
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def timestamp_filename(prefix: str = "", suffix: str = ".txt") -> str:
    """Generate a timestamped filename.
    
    Args:
        prefix: Optional prefix for filename
        suffix: File extension (default: .txt)
        
    Returns:
        Filename with timestamp
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if prefix:
        return f"{prefix}_{timestamp}{suffix}"
    return f"{timestamp}{suffix}"


def get_local_now() -> datetime:
    """Get current time in local timezone.
    
    Returns:
        Current datetime with timezone info
    """
    try:
        local_tz = pytz.timezone('Asia/Jerusalem')
        return datetime.now(local_tz)
    except:
        return datetime.now()


def format_size(bytes_size: int) -> str:
    """Format byte size in human-readable format.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} TB"


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text.
    
    Args:
        text: Text with potential ANSI codes
        
    Returns:
        Clean text without ANSI codes
    """
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def get_ssh_hostname(device, fallback_to_device_ip: bool = True) -> str:
    """Get the best SSH hostname/IP for a device.
    
    Prefers mgmt IP from operational.json over devices.json IP.
    This ensures we use the actual working mgmt IP discovered during operations.
    
    Args:
        device: Device object (must have .hostname and .ip attributes)
        fallback_to_device_ip: If True, falls back to device.ip if no mgmt IP found
        
    Returns:
        Hostname/IP to use for SSH connection
        
    Example:
        >>> hostname = get_ssh_hostname(device)
        >>> client.connect(hostname=hostname, ...)
    """
    import json
    
    # Start with device.ip as default
    hostname = device.ip if fallback_to_device_ip else None
    
    try:
        ops_file = get_device_config_dir(device.hostname) / "operational.json"
        if ops_file.exists():
            with open(ops_file) as f:
                ops_data = json.load(f)
                # Try mgmt_ip first, then ssh_host as fallback
                mgmt_ip = ops_data.get("mgmt_ip") or ops_data.get("ssh_host")
                if mgmt_ip and mgmt_ip != "N/A" and mgmt_ip.strip():
                    # Strip subnet mask if present (e.g., "100.64.1.35/20" -> "100.64.1.35")
                    mgmt_ip = mgmt_ip.split('/')[0].strip()
                    return mgmt_ip
    except Exception:
        pass  # Fall back to device.ip on any error
    
    if hostname is None:
        raise ValueError(f"No SSH hostname found for device {device.hostname}")
    
    return hostname


def sync_device_ip_from_operational(hostname: str) -> bool:
    """
    Sync the device IP in devices.json from operational.json.
    
    Call this after successful connections to keep devices.json up to date
    with the working management IP.
    
    Args:
        hostname: Device hostname
        
    Returns:
        True if devices.json was updated, False otherwise
    """
    import json
    from pathlib import Path
    
    try:
        # Get the working IP from operational.json
        ops_file = get_device_config_dir(hostname) / "operational.json"
        if not ops_file.exists():
            return False
            
        with open(ops_file) as f:
            ops_data = json.load(f)
        
        # Get the working mgmt_ip (strip CIDR notation if present)
        mgmt_ip = ops_data.get("mgmt_ip") or ops_data.get("ssh_host")
        if not mgmt_ip or mgmt_ip == "N/A":
            return False
        
        # Strip CIDR notation
        if "/" in mgmt_ip:
            mgmt_ip = mgmt_ip.split("/")[0]
        
        connection_method = ops_data.get("connection_method", "")
        
        # Update devices.json
        devices_file = Path(__file__).parent.parent / "db" / "devices.json"
        if not devices_file.exists():
            return False
            
        with open(devices_file) as f:
            devices_data = json.load(f)
        
        updated = False
        for dev in devices_data.get("devices", []):
            if dev.get("hostname") == hostname:
                old_ip = dev.get("ip", "")
                if old_ip != mgmt_ip:
                    dev["ip"] = mgmt_ip
                    # Store connection method for reference
                    dev["connection_method"] = connection_method
                    updated = True
                break
        
        if updated:
            with open(devices_file, "w") as f:
                json.dump(devices_data, f, indent=2)
        
        return updated
        
    except Exception:
        return False


def update_device_connection_info(hostname: str, ip: str, connection_method: str = "") -> bool:
    """
    Update device connection info in both operational.json and devices.json.
    
    Call this after a successful SSH connection to persist the working IP.
    
    Args:
        hostname: Device hostname
        ip: Working IP address
        connection_method: How we connected (e.g., "SSH→MGMT", "SSH→SN", "Console")
        
    Returns:
        True if updated successfully
    """
    import json
    from pathlib import Path
    from datetime import datetime
    
    try:
        # Update operational.json
        ops_file = get_device_config_dir(hostname) / "operational.json"
        ops_data = {}
        
        if ops_file.exists():
            with open(ops_file) as f:
                ops_data = json.load(f)
        
        # Strip CIDR notation
        clean_ip = ip.split("/")[0] if "/" in ip else ip
        
        ops_data["mgmt_ip"] = clean_ip
        ops_data["ssh_host"] = clean_ip
        if connection_method:
            ops_data["connection_method"] = connection_method
        ops_data["last_connection"] = datetime.now().isoformat()
        
        ops_file.parent.mkdir(parents=True, exist_ok=True)
        with open(ops_file, "w") as f:
            json.dump(ops_data, f, indent=4)
        
        # Also update devices.json
        devices_file = Path(__file__).parent.parent / "db" / "devices.json"
        if devices_file.exists():
            with open(devices_file) as f:
                devices_data = json.load(f)
            
            for dev in devices_data.get("devices", []):
                if dev.get("hostname") == hostname:
                    dev["ip"] = clean_ip
                    if connection_method:
                        dev["connection_method"] = connection_method
                    break
            
            with open(devices_file, "w") as f:
                json.dump(devices_data, f, indent=2)
        
        return True
        
    except Exception:
        return False


def validate_loopback_ip(ip_input: str, auto_correct: bool = True) -> tuple:
    """
    Validate and optionally correct loopback IP address.
    
    Loopback interfaces should ALWAYS use /32 (host route) because:
    - They represent a single router identity, not a network
    - /32 ensures proper route advertisement in ISIS/OSPF/BGP
    - Other prefixes can cause routing conflicts and unexpected behavior
    
    Args:
        ip_input: IP address with optional prefix (e.g., "1.1.1.1" or "1.1.1.1/29")
        auto_correct: If True, automatically correct to /32
        
    Returns:
        Tuple of (corrected_ip, is_valid, warning_message)
        - corrected_ip: The IP with /32 prefix
        - is_valid: True if original was valid (/32 or no prefix)
        - warning_message: Warning if correction was needed, None otherwise
        
    Examples:
        >>> validate_loopback_ip("1.1.1.1")
        ("1.1.1.1/32", True, None)
        
        >>> validate_loopback_ip("1.1.1.1/32")
        ("1.1.1.1/32", True, None)
        
        >>> validate_loopback_ip("1.1.1.1/29")
        ("1.1.1.1/32", False, "Loopback should use /32, not /29")
    """
    import re
    
    if not ip_input:
        return (ip_input, False, "Empty IP address")
    
    ip_input = ip_input.strip()
    
    # Validate IP format
    ip_pattern = r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(/(\d{1,2}))?$'
    match = re.match(ip_pattern, ip_input)
    
    if not match:
        return (ip_input, False, f"Invalid IP format: {ip_input}")
    
    ip_addr = match.group(1)
    prefix = match.group(3)  # May be None
    
    # Validate octets
    octets = ip_addr.split('.')
    for octet in octets:
        if int(octet) > 255:
            return (ip_input, False, f"Invalid IP octet: {octet}")
    
    # Check prefix
    if prefix is None:
        # No prefix specified - valid, add /32
        return (f"{ip_addr}/32", True, None)
    
    if prefix == '32':
        # Correct /32 - valid
        return (ip_input, True, None)
    
    # Wrong prefix - needs correction
    warning = f"Loopback should use /32, not /{prefix}. Corrected."
    if auto_correct:
        return (f"{ip_addr}/32", False, warning)
    else:
        return (ip_input, False, warning)


def normalize_loopback_ip(ip_input: str, warn_callback=None) -> str:
    """
    Normalize loopback IP to always use /32 prefix.
    
    Args:
        ip_input: IP address (e.g., "1.1.1.1" or "1.1.1.1/29")
        warn_callback: Optional callback function to display warning
                       Called with (message) if correction needed
                       
    Returns:
        Normalized IP with /32 prefix
    """
    corrected, is_valid, warning = validate_loopback_ip(ip_input)
    
    if warning and warn_callback:
        warn_callback(warning)
    
    return corrected










