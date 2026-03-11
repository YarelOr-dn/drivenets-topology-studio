"""Utility functions for SCALER."""

from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
import pytz
import json
import re
import socket
import logging

logger = logging.getLogger(__name__)


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


def _hostname_matches(actual: str, expected: str) -> bool:
    """Check if actual hostname matches expected, with word-boundary awareness.
    
    Handles: DB="PE-4", device="YOR_CL_PE-4" → match (PE-4 at word boundary)
    Rejects: DB="PE-4", device="PE-40" → no match (PE-4 is not a whole word)
    
    Word boundaries are: _ . - or start/end of string.
    """
    a = actual.strip().lower()
    e = expected.strip().lower().replace(' ', '')
    if not a or not e:
        return False
    if a == e:
        return True
    
    shorter, longer = (e, a) if len(e) <= len(a) else (a, e)
    
    pos = longer.find(shorter)
    if pos == -1:
        return False
    
    # Check that the match sits at word boundaries (_, -, . or string edge)
    boundary_chars = {'_', '-', '.'}
    left_ok = (pos == 0) or (longer[pos - 1] in boundary_chars)
    end = pos + len(shorter)
    right_ok = (end == len(longer)) or (longer[end] in boundary_chars)
    
    return left_ok and right_ok


def extract_hostname_from_prompt(output: str) -> Optional[str]:
    """Extract device hostname from SSH prompt output.
    
    Returns None if no recognizable prompt found, or the hostname string.
    Handles: HOSTNAME#  HOSTNAME(timestamp)#  HOSTNAME>  GI#  etc.
    """
    clean = strip_ansi(output).replace('\r', '')
    prompt_match = re.search(
        r'([A-Za-z0-9_][A-Za-z0-9_.-]*[A-Za-z0-9_-])(?:\([^)]*\))?\s*[#>]\s*$',
        clean, re.MULTILINE
    )
    if prompt_match:
        return prompt_match.group(1)
    if re.search(r'\bGI\s*[#>]|\bGI\(', clean):
        return "GI"
    return None


def verify_device_hostname(initial_output: str, expected_hostname: str) -> Tuple[bool, str]:
    """Fast prompt-based hostname verification (Layer 1).
    
    CRITICAL SAFETY CHECK: Prevents executing commands on wrong devices.
    Must be called immediately after SSH connection, before any commands.
    Takes ~0ms (string parsing only, no network).
    
    Returns:
        (matches: bool, actual_hostname: str)
    """
    actual = extract_hostname_from_prompt(initial_output)
    if actual is None:
        return True, "UNKNOWN"
    if actual in ('GI', 'dnRouter', 'localhost', 'UNKNOWN'):
        return True, actual
    return _hostname_matches(actual, expected_hostname), actual


def resolve_device_ip(device, timeout: float = 2.0) -> Tuple[Optional[str], str]:
    """Pre-connection IP resolution: find the best reachable IP for a device (Layer 0).
    
    Resolution order (first reachable wins):
    1. Stored mgmt_ip from operational.json
    2. Stored ncc_mgmt_ip from operational.json (mgmt-ncc-0; survives system delete)
    3. device.ip from devices.json
    4. Serial number DNS resolution (if serial resolves to an IP, verify it's reachable)
    
    After system delete, mgmt0 loses its DHCP IP (config-dependent) but mgmt-ncc-0
    keeps its built-in DHCP lease. The ncc_mgmt_ip ensures the device is still
    reachable even when mgmt0's IP has been reassigned by DHCP to another device.
    
    Each IP is verified with a fast TCP port-22 probe.
    
    Returns:
        (ip: str or None, method: str) - resolved IP and how we found it
    """
    candidates = []
    serial_number = None
    
    try:
        ops_file = get_device_config_dir(device.hostname) / "operational.json"
        if ops_file.exists():
            with open(ops_file) as f:
                ops_data = json.load(f)
            mgmt_ip = ops_data.get("mgmt_ip") or ops_data.get("ssh_host")
            if mgmt_ip and mgmt_ip != "N/A":
                _clean = mgmt_ip.split('/')[0].strip()
                if _clean and 'console' not in _clean.lower():
                    candidates.append((_clean, "MGMT"))
            ncc_ip = ops_data.get("ncc_mgmt_ip")
            if ncc_ip and ncc_ip != "N/A":
                _ncc_clean = ncc_ip.split('/')[0].strip()
                if _ncc_clean and _ncc_clean not in [c[0] for c in candidates]:
                    candidates.append((_ncc_clean, "NCC_MGMT"))
            sn = ops_data.get("serial_number")
            if sn and sn != "N/A":
                serial_number = sn
    except Exception:
        pass
    
    if hasattr(device, 'ip') and device.ip:
        ip = device.ip.split('/')[0].strip()
        if ip and ip not in [c[0] for c in candidates]:
            candidates.append((ip, "DB"))
    
    if serial_number:
        try:
            resolved = socket.getaddrinfo(serial_number, 22, socket.AF_INET, socket.SOCK_STREAM)
            if resolved:
                sn_ip = resolved[0][4][0]
                if sn_ip not in [c[0] for c in candidates]:
                    candidates.append((sn_ip, f"DNS({serial_number})"))
        except (socket.gaierror, socket.herror):
            pass
    
    for ip, method in candidates:
        try:
            sock = socket.create_connection((ip, 22), timeout=timeout)
            sock.close()
            return ip, method
        except (socket.timeout, socket.error, OSError):
            continue
    
    return None, "UNREACHABLE"


def post_connect_verify(channel, expected_hostname: str, prompt_output: str = "",
                        run_show_system: bool = True) -> Dict[str, Any]:
    """Multi-layer post-connection verification (Layers 1-3).
    
    Runs fast checks in sequence, aborting on first failure:
      Layer 1: Prompt hostname check (~0ms, string parse)
      Layer 2: 'show system' hostname + serial verification (~3s)
      Layer 3: 'show interfaces management' live IP extraction (~3s)
    
    Args:
        channel: paramiko channel (already connected)
        expected_hostname: hostname from devices.json
        prompt_output: initial SSH output (if already captured)
        run_show_system: if True, runs show system for deeper verification
        
    Returns:
        dict with keys:
            verified: bool - True if device identity confirmed
            actual_hostname: str - hostname seen on device
            abort_reason: str or None - why verification failed
            mgmt_ip: str or None - live management IP from device
            serial_number: str or None - serial from show system
            system_type: str or None - system type from show system
            ncc_type: str or None - 'kvm' or 'physical' (cluster devices only)
            ncc_hosts: list or None - KVM NCC hostnames if ncc_type=kvm
    """
    result = {
        'verified': False,
        'actual_hostname': 'UNKNOWN',
        'abort_reason': None,
        'mgmt_ip': None,
        'serial_number': None,
        'system_type': None,
        'ncc_type': None,
        'ncc_hosts': None,
    }
    
    def _send_and_read(cmd: str, wait: float = 3.0) -> str:
        import time
        channel.send(f"{cmd}\n")
        time.sleep(wait)
        out = ""
        for _ in range(5):
            try:
                if channel.recv_ready():
                    out += channel.recv(65535).decode('utf-8', errors='replace')
            except Exception:
                break
            time.sleep(0.2)
        return strip_ansi(out).replace('\r', '')
    
    # --- Layer 1: Prompt hostname (instant) ---
    if prompt_output:
        actual = extract_hostname_from_prompt(prompt_output)
        if actual:
            result['actual_hostname'] = actual
            if actual not in ('GI', 'dnRouter', 'localhost', 'UNKNOWN'):
                if not _hostname_matches(actual, expected_hostname):
                    result['abort_reason'] = (
                        f"WRONG DEVICE: prompt shows '{actual}', expected '{expected_hostname}'"
                    )
                    return result
    
    if not run_show_system:
        result['verified'] = True
        return result
    
    # --- Layer 2: show system (fast, ~3s) ---
    import time
    sys_out = _send_and_read("show system | no-more", wait=3.0)
    
    for line in sys_out.split('\n'):
        if 'System Name:' in line:
            m = re.search(r'System Name:\s*(\S+)', line)
            if m:
                sys_hostname = m.group(1).rstrip(',')
                result['actual_hostname'] = sys_hostname
                if sys_hostname not in ('GI', 'dnRouter', 'localhost'):
                    if not _hostname_matches(sys_hostname, expected_hostname):
                        result['abort_reason'] = (
                            f"WRONG DEVICE: 'show system' reports '{sys_hostname}', "
                            f"expected '{expected_hostname}'"
                        )
                        return result
        if 'System Type:' in line:
            m = re.search(r'System Type:\s*(\S+)', line)
            if m:
                result['system_type'] = m.group(1).rstrip(',')
    
    # Extract serial from show system install output (faster than show system ncc)
    for line in sys_out.split('\n'):
        sn_match = re.search(r'Serial\s*(?:Number)?[:\s]+([A-Z0-9]{10,})', line, re.IGNORECASE)
        if sn_match:
            result['serial_number'] = sn_match.group(1)
            break
    
    # --- Layer 2.5: NCC type classification (cluster devices only) ---
    # Parse NCC rows from the show system table to determine KVM vs physical NCCs.
    # KVM NCCs: Model=X86, Serial is a DNS hostname (e.g. kvm108-cl408d-ncc0)
    # Physical NCCs: Model is hardware (e.g. NCC-16), Serial is hardware S/N
    sys_type = result.get('system_type', '')
    if sys_type and sys_type.startswith('CL'):
        ncc_hosts = []
        ncc_type = 'physical'
        for line in sys_out.split('\n'):
            if '| NCC' not in line and '|NCC' not in line:
                continue
            parts = [p.strip() for p in line.split('|')]
            if len(parts) < 9:
                continue
            ncc_model = parts[5] if len(parts) > 5 else ''
            ncc_serial = parts[8] if len(parts) > 8 else ''
            if ncc_model.upper() == 'X86':
                ncc_type = 'kvm'
            if ncc_serial and re.match(r'^[a-z]', ncc_serial):
                ncc_hosts.append(ncc_serial)
        result['ncc_type'] = ncc_type
        result['ncc_hosts'] = ncc_hosts
    
    # --- Layer 3: Live management IP (~3s) ---
    mgmt_out = _send_and_read("show interfaces management | no-more", wait=3.0)
    for line in mgmt_out.split('\n'):
        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/(\d{1,2})', line)
        if ip_match:
            candidate_ip = ip_match.group(1)
            if not candidate_ip.startswith('127.') and not candidate_ip.endswith('.255'):
                result['mgmt_ip'] = candidate_ip
                break
    
    result['verified'] = True
    return result


def verify_gi_serial(channel, expected_hostname: str) -> Dict[str, Any]:
    """GI-mode device verification using serial number from 'show system stack'.
    
    In GI mode the prompt is just 'GI#' with no hostname. But 'show system stack'
    still works and returns the NCC serial number. We compare this against the
    stored serial in operational.json.
    
    Returns:
        dict: verified, abort_reason, serial_number, system_type
    """
    import time
    
    result = {
        'verified': False,
        'abort_reason': None,
        'serial_number': None,
        'system_type': None,
    }
    
    # Get stored serial from operational.json
    stored_serial = None
    try:
        ops_file = get_device_config_dir(expected_hostname) / "operational.json"
        if ops_file.exists():
            with open(ops_file) as f:
                ops_data = json.load(f)
            stored_serial = ops_data.get('serial_number')
            if stored_serial == 'N/A':
                stored_serial = None
    except Exception:
        pass
    
    if not stored_serial:
        result['verified'] = True
        return result
    
    # Run 'show system | no-more' - works in both GI and DNOS mode
    # Serial is on the NCP row: | NCP | 0 | enabled | up | Model | Uptime | Desc | SERIAL |
    channel.send("show system | no-more\n")
    time.sleep(4)
    sys_out = ""
    for _ in range(8):
        try:
            if channel.recv_ready():
                sys_out += channel.recv(65535).decode('utf-8', errors='replace')
        except Exception:
            break
        time.sleep(0.3)
    
    sys_clean = strip_ansi(sys_out).replace('\r', '')
    
    live_serial = None
    for line in sys_clean.split('\n'):
        if re.search(r'\bNCP\b', line) and '|' in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            for part in reversed(parts):
                if re.match(r'^[A-Z0-9]{10,}$', part) and not re.match(r'^\d+:\d+:\d+', part):
                    live_serial = part
                    break
            if live_serial:
                break
    
    if not live_serial:
        # Couldn't extract serial from stack output - allow with warning
        result['verified'] = True
        return result
    
    result['serial_number'] = live_serial
    
    if live_serial != stored_serial:
        result['abort_reason'] = (
            f"GI SERIAL MISMATCH: device has '{live_serial}', "
            f"DB expects '{stored_serial}' for '{expected_hostname}'. Wrong device!"
        )
        return result
    
    result['verified'] = True
    return result


def audit_log(device_hostname: str, ip: str, command: str, context: str = "") -> None:
    """Log destructive commands to an audit trail.
    
    Every deploy, delete, configure, commit sent to a device is logged
    with timestamp, device identity, and connection IP.
    """
    audit_file = DB_DIR / "audit.log"
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cmd_preview = command[:80].replace('\n', ' ')
        entry = f"[{timestamp}] {device_hostname} ({ip}): {cmd_preview}"
        if context:
            entry += f" [{context}]"
        entry += "\n"
        
        with open(audit_file, 'a') as f:
            f.write(entry)
    except Exception:
        pass


def sync_device_from_live(db_hostname: str, live_data: Dict[str, Any]) -> Dict[str, str]:
    """Sync DB (devices.json + operational.json) with verified live device data.
    
    Updates mgmt IP, serial number, system type, and hostname if changed.
    
    Args:
        db_hostname: The hostname as stored in devices.json (lookup key)
        live_data: Dict from post_connect_verify() with verified live info
        
    Returns:
        dict of what was updated: {'ip': 'old->new', 'hostname': 'old->new', ...}
    """
    changes = {}
    
    actual_hostname = live_data.get('actual_hostname')
    live_ip = live_data.get('mgmt_ip')
    live_serial = live_data.get('serial_number')
    live_sys_type = live_data.get('system_type')
    
    # --- Update operational.json ---
    try:
        ops_file = get_device_config_dir(db_hostname) / "operational.json"
        ops_data = {}
        if ops_file.exists():
            with open(ops_file) as f:
                ops_data = json.load(f)
        
        if live_ip:
            old_ip = (ops_data.get('mgmt_ip') or '').split('/')[0]
            if old_ip != live_ip:
                changes['mgmt_ip'] = f"{old_ip} → {live_ip}"
            ops_data['mgmt_ip'] = live_ip
            ops_data['ssh_host'] = live_ip
        
        if live_serial:
            old_sn = ops_data.get('serial_number', '')
            if old_sn != live_serial:
                changes['serial_number'] = f"{old_sn} → {live_serial}"
            ops_data['serial_number'] = live_serial
        
        if live_sys_type:
            old_st = ops_data.get('system_type', '')
            if old_st != live_sys_type:
                changes['system_type'] = f"{old_st} → {live_sys_type}"
            ops_data['system_type'] = live_sys_type
        
        # NCC type classification (cluster devices: kvm vs physical)
        live_ncc_type = live_data.get('ncc_type')
        if live_ncc_type:
            old_ncc_type = ops_data.get('ncc_type', '')
            if old_ncc_type != live_ncc_type:
                changes['ncc_type'] = f"{old_ncc_type or 'unset'} → {live_ncc_type}"
            ops_data['ncc_type'] = live_ncc_type
        
        live_ncc_hosts = live_data.get('ncc_hosts')
        if live_ncc_hosts:
            old_ncc_hosts = ops_data.get('ncc_hosts', [])
            if set(old_ncc_hosts) != set(live_ncc_hosts):
                changes['ncc_hosts'] = f"{old_ncc_hosts} → {live_ncc_hosts}"
            ops_data['ncc_hosts'] = live_ncc_hosts
            if live_ncc_type == 'kvm':
                ops_data['ncc_credentials'] = ops_data.get('ncc_credentials', 
                    {"username": "dnroot", "password": "dnroot"})
        
        ops_data['last_verified'] = datetime.now().isoformat()
        
        ops_file.parent.mkdir(parents=True, exist_ok=True)
        with open(ops_file, 'w') as f:
            json.dump(ops_data, f, indent=4)
    except Exception as e:
        logger.warning(f"Failed to update operational.json for {db_hostname}: {e}")
    
    # --- Update devices.json ---
    try:
        devices_file = DB_DIR / "devices.json"
        if not devices_file.exists():
            return changes
        
        with open(devices_file) as f:
            devices_data = json.load(f)
        
        updated = False
        for dev in devices_data.get("devices", []):
            if dev.get("hostname") != db_hostname:
                continue
            
            if live_ip and dev.get("ip") != live_ip:
                changes['devices_json_ip'] = f"{dev.get('ip')} → {live_ip}"
                dev["ip"] = live_ip
                updated = True
            
            # Hostname sync: if device reports a different hostname, update DB
            if (actual_hostname and
                actual_hostname not in ('GI', 'dnRouter', 'localhost', 'UNKNOWN') and
                actual_hostname != db_hostname and
                not _hostname_matches(actual_hostname, db_hostname)):
                # Only log a warning - hostname rename needs explicit user action
                changes['hostname_mismatch'] = (
                    f"DB='{db_hostname}', Device='{actual_hostname}' (NOT auto-renamed)"
                )
                
                # Auto-update console mapping to track the new hostname
                try:
                    from scaler.connection_strategy import update_console_hostname
                    if update_console_hostname(db_hostname, actual_hostname, live_serial):
                        changes['console_mapping_updated'] = (
                            f"Console port for '{db_hostname}' now maps to '{actual_hostname}'"
                        )
                except Exception:
                    pass
            
            break
        
        if updated:
            with open(devices_file, 'w') as f:
                json.dump(devices_data, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to update devices.json for {db_hostname}: {e}")
    
    return changes


def safe_connect_and_verify(device, credentials: list = None,
                            timeout: float = 2.0,
                            verify_layers: bool = True) -> Dict[str, Any]:
    """Complete safe connection flow: resolve IP → connect → verify → sync DB.
    
    This is the single entry point for safe device connections.
    
    Args:
        device: Device object with .hostname, .ip, optionally .username/.password
        credentials: List of {'username': ..., 'password': ...} dicts to try
        timeout: TCP probe timeout per IP candidate
        verify_layers: If True, runs full post-connect verification
        
    Returns:
        dict with keys:
            connected: bool
            ssh: paramiko.SSHClient or None
            channel: paramiko channel or None
            ip: str - the IP that worked
            method: str - how we connected
            verified: bool - True if device identity confirmed
            actual_hostname: str
            abort_reason: str or None - if connection was aborted (WRONG DEVICE)
            prompt_output: str - initial output from device
            db_changes: dict - what was synced to DB
    """
    import paramiko
    import time
    
    result = {
        'connected': False, 'ssh': None, 'channel': None,
        'ip': None, 'method': None, 'verified': False,
        'actual_hostname': 'UNKNOWN', 'abort_reason': None,
        'prompt_output': '', 'db_changes': {},
    }
    
    if credentials is None:
        credentials = [
            {'username': 'dnroot', 'password': 'dnroot'},
        ]
        if hasattr(device, 'username') and hasattr(device, 'password'):
            import base64
            pwd = device.password
            try:
                pwd = base64.b64decode(device.password).decode('utf-8')
            except Exception:
                pass
            dev_cred = {'username': device.username or 'dnroot', 'password': pwd or 'dnroot'}
            if dev_cred not in credentials:
                credentials.insert(0, dev_cred)
    
    # --- Layer 0: Resolve best IP ---
    resolved_ip, method = resolve_device_ip(device, timeout=timeout)
    if not resolved_ip:
        result['abort_reason'] = f"No reachable IP for {device.hostname}"
        return result
    
    result['ip'] = resolved_ip
    result['method'] = method
    
    # --- Connect SSH ---
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    connected = False
    for cred in credentials:
        try:
            ssh.connect(
                resolved_ip,
                username=cred['username'],
                password=cred['password'],
                timeout=10,
                banner_timeout=10,
                auth_timeout=10,
                allow_agent=False,
                look_for_keys=False,
            )
            connected = True
            break
        except paramiko.AuthenticationException:
            continue
        except Exception:
            break
    
    if not connected:
        result['abort_reason'] = f"SSH auth failed for {device.hostname} at {resolved_ip}"
        return result
    
    channel = ssh.invoke_shell(width=200, height=50)
    channel.settimeout(30)
    time.sleep(2)
    
    prompt_output = ""
    try:
        if channel.recv_ready():
            prompt_output = channel.recv(65535).decode('utf-8', errors='replace')
    except Exception:
        pass
    
    result['ssh'] = ssh
    result['channel'] = channel
    result['connected'] = True
    result['prompt_output'] = prompt_output
    
    if not verify_layers:
        result['verified'] = True
        return result
    
    # --- Layers 1-3: Verify identity + get live data ---
    verify = post_connect_verify(
        channel, device.hostname,
        prompt_output=prompt_output,
        run_show_system=True,
    )
    
    result['verified'] = verify['verified']
    result['actual_hostname'] = verify['actual_hostname']
    result['abort_reason'] = verify.get('abort_reason')
    
    if not verify['verified'] or verify.get('abort_reason'):
        # WRONG DEVICE - close immediately
        try:
            ssh.close()
        except Exception:
            pass
        result['connected'] = False
        result['ssh'] = None
        result['channel'] = None
        return result
    
    # --- Sync DB with live data ---
    result['db_changes'] = sync_device_from_live(device.hostname, verify)
    
    return result


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










