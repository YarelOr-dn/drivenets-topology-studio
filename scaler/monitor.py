#!/usr/bin/env python3
"""
SCALER Monitor - Configuration extraction status.

Usage:
    scaler-monitor              # One-time status check (default)
    scaler-monitor --watch      # Live monitoring (refresh every 1s)
    scaler-monitor -w -i 5      # Live monitoring with custom interval
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import subprocess

# Set timezone to Israel
os.environ['TZ'] = 'Asia/Jerusalem'
try:
    time.tzset()
except AttributeError:
    pass  # Windows doesn't have tzset

# Add SCALER to path (resolve symlinks to get real path)
SCALER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCALER_DIR))

# ANSI colors
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    DIM = "\033[2m"


def clear_screen():
    """Clear terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')


def get_terminal_width():
    """Get terminal width."""
    try:
        return os.get_terminal_size().columns
    except:
        return 80


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    elif seconds < 86400:  # Less than 24 hours
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"
    else:  # 1 day or more
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{days}d {hours}h {mins}m"


def format_time_ago(dt: datetime) -> str:
    """Format time as 'X ago'."""
    now = datetime.now()
    diff = now - dt
    seconds = diff.total_seconds()
    
    # Handle negative (future) times - likely timezone issue
    if seconds < 0:
        return "just now"
    
    if seconds < 60:
        return f"{int(seconds)}s ago"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m ago"
    else:
        return f"{int(seconds // 86400)}d ago"


# Global variable to track when monitor started
MONITOR_START_TIME = datetime.now()


def get_service_start_time(log_file: Path) -> Optional[datetime]:
    """Get the timestamp of the first log entry (service start time)."""
    if not log_file.exists():
        return None
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('['):
                    try:
                        ts_end = line.index(']')
                        ts_str = line[1:ts_end]
                        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                    except:
                        continue
    except:
        pass
    return None


def count_total_extractions(log_file: Path) -> dict:
    """Count total extraction cycles and success/failure using grep (fast on large files)."""
    result = {'total': 0, 'successful': 0, 'failed': 0}
    if not log_file.exists():
        return result
    try:
        lf = str(log_file)
        r = subprocess.run(['grep', '-c', 'Starting config extraction', lf],
                          capture_output=True, text=True, timeout=5)
        result['total'] = int(r.stdout.strip() or 0)
        r = subprocess.run(['grep', '-cE', 'No change -|Config changed|Config CHANGED', lf],
                          capture_output=True, text=True, timeout=5)
        result['successful'] = int(r.stdout.strip() or 0)
        r = subprocess.run(['grep', '-c', 'FAILED', lf],
                          capture_output=True, text=True, timeout=5)
        result['failed'] = int(r.stdout.strip() or 0)
    except Exception:
        pass
    return result


def parse_log_entries(log_file: Path, max_entries: int = 100) -> list:
    """Parse extraction log entries (uses tail for efficiency on large logs)."""
    entries = []
    if not log_file.exists():
        return entries
    
    try:
        r = subprocess.run(['tail', '-n', str(max_entries * 5), str(log_file)],
                          capture_output=True, text=True, timeout=5)
        lines = r.stdout.splitlines()
    except Exception:
        return entries
    
    for line in lines:
        line = line.strip()
        if not line or not line.startswith('['):
            continue
        try:
            ts_end = line.index(']')
            ts_str = line[1:ts_end]
            timestamp = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            message = line[ts_end + 2:]
            entries.append({'timestamp': timestamp, 'message': message, 'raw': line})
        except:
            pass
    
    return entries


def get_extraction_stats(log_file: Path) -> dict:
    """Calculate extraction statistics from log."""
    entries = parse_log_entries(log_file, max_entries=500)
    
    stats = {
        'total_extractions': 0,
        'successful': 0,
        'failed': 0,
        'last_extraction': None,
        'last_duration': None,
        'avg_duration': None,
        'devices': {},
        'is_running': False,
        'current_device': None,
        'extraction_rate': None,  # Average time between extractions
        'first_extraction': None,  # When monitoring started
        'running_since': None      # Total monitoring time
    }
    
    extraction_starts = {}
    extraction_times = []
    batch_start_times = []  # Track when each batch extraction started
    
    for entry in entries:
        msg = entry['message']
        ts = entry['timestamp']
        
        # Track extraction starts
        if msg.startswith('=== Starting config extraction ==='):
            extraction_starts['batch'] = ts
            stats['total_extractions'] += 1
            batch_start_times.append(ts)
            if stats['first_extraction'] is None:
                stats['first_extraction'] = ts
        
        # Track device extractions
        if 'Extracting ' in msg and ' from ' in msg:
            # e.g., "Extracting PE-1 from wk31d7vv00023..."
            parts = msg.split(' ')
            if len(parts) >= 2:
                device = parts[1]
                stats['current_device'] = device
                extraction_starts[device] = ts
                if device not in stats['devices']:
                    stats['devices'][device] = {'success': 0, 'failed': 0, 'last_status': None}
        
        # Track successes
        if ': No change -' in msg or 'Config changed' in msg:
            device = msg.split(':')[0]
            if device in stats['devices']:
                stats['devices'][device]['success'] += 1
                stats['devices'][device]['last_status'] = 'success'
            stats['successful'] += 1
            stats['last_extraction'] = ts
        
        # Track failures
        if 'FAILED' in msg:
            device = msg.split(':')[0]
            if device in stats['devices']:
                stats['devices'][device]['failed'] += 1
                stats['devices'][device]['last_status'] = 'failed'
            stats['failed'] += 1
        
        # Track extraction complete
        if msg.startswith('=== Extraction complete ==='):
            if 'batch' in extraction_starts:
                duration = (ts - extraction_starts['batch']).total_seconds()
                extraction_times.append(duration)
                stats['last_duration'] = duration
            stats['current_device'] = None
    
    # Calculate average duration
    if extraction_times:
        stats['avg_duration'] = sum(extraction_times) / len(extraction_times)
    
    # Calculate extraction rate (average interval between extractions)
    if len(batch_start_times) >= 2:
        intervals = []
        for i in range(1, len(batch_start_times)):
            interval = (batch_start_times[i] - batch_start_times[i-1]).total_seconds()
            if interval > 0 and interval < 7200:  # Ignore gaps > 2 hours (likely service restart)
                intervals.append(interval)
        if intervals:
            stats['extraction_rate'] = sum(intervals) / len(intervals)
    
    # Calculate running since (from ACTUAL first extraction in log file to now)
    # This gets the real service start time, not just from parsed entries
    service_start = get_service_start_time(log_file)
    if service_start:
        stats['first_extraction'] = service_start
        stats['running_since'] = abs((datetime.now() - service_start).total_seconds())
    elif stats['first_extraction']:
        stats['running_since'] = abs((datetime.now() - stats['first_extraction']).total_seconds())
    
    # Get total extraction count and success/failure from full log file
    full_counts = count_total_extractions(log_file)
    stats['total_extractions'] = full_counts['total']
    stats['successful'] = full_counts['successful']
    stats['failed'] = full_counts['failed']
    
    # Check if currently running (last start without complete within 5 mins)
    if entries:
        last_entry = entries[-1]
        if 'Extracting' in last_entry['message']:
            time_diff = abs((datetime.now() - last_entry['timestamp']).total_seconds())
            if time_diff < 300:  # Within 5 minutes
                stats['is_running'] = True
    
    return stats


def get_device_status(configs_dir: Path) -> list:
    """Get status of all configured devices."""
    devices = []
    
    for device_dir in sorted(configs_dir.iterdir()):
        if not device_dir.is_dir():
            continue
        
        device_name = device_dir.name
        operational_file = device_dir / "operational.json"
        running_file = device_dir / "running.txt"
        
        device_info = {
            'name': device_name,
            'has_config': running_file.exists(),
            'config_lines': 0,
            'config_size': 0,
            'last_modified': None,
            'unchanged_since': None,
            'unchanged_until': None,
            'unchanged_checks': 0,
            'upgrade_in_progress': False,
            'system_type': 'N/A',
            'uptime': 'N/A',
            'dnos_version': 'N/A',
            'bgp_peers': 0,
            'bgp_up': 0,
            'interfaces_total': 0,
            'interfaces_up': 0,
            # Network Services - ALL types
            'fxc_total': 0,
            'fxc_up': 0,
            'vpws_total': 0,
            'vpws_up': 0,
            'evpn_total': 0,
            'evpn_up': 0,
            'vrf_total': 0,
            'vrf_up': 0
        }
        
        if running_file.exists():
            stat = running_file.stat()
            device_info['config_size'] = stat.st_size
            device_info['last_modified'] = datetime.fromtimestamp(stat.st_mtime)
            device_info['config_lines'] = sum(1 for _ in open(running_file))
        
        if operational_file.exists():
            try:
                with open(operational_file, 'r') as f:
                    op_data = json.load(f)
                
                device_info['unchanged_since'] = op_data.get('unchanged_since')
                device_info['unchanged_until'] = op_data.get('unchanged_until')
                device_info['unchanged_checks'] = op_data.get('unchanged_checks', 0)
                device_info['upgrade_in_progress'] = op_data.get('upgrade_in_progress', False)
                device_info['recovery_mode_detected'] = op_data.get('recovery_mode_detected', False)
                device_info['recovery_type'] = op_data.get('recovery_type', '')
                device_info['device_state'] = op_data.get('device_state', '')
                device_info['system_type'] = op_data.get('system_type', 'N/A')
                device_info['uptime'] = op_data.get('system_uptime', 'N/A')
                device_info['dnos_version'] = op_data.get('dnos_version', 'N/A')
                device_info['bgp_peers'] = op_data.get('bgp_neighbors', 0)
                device_info['bgp_up'] = op_data.get('bgp_up', 0)
                device_info['interfaces_total'] = op_data.get('interfaces_total', 0)
                device_info['interfaces_up'] = op_data.get('interfaces_up', 0)
                # Network Services - ALL types
                device_info['fxc_total'] = op_data.get('fxc_total', 0)
                device_info['fxc_up'] = op_data.get('fxc_up', 0)
                device_info['vpws_total'] = op_data.get('vpws_total', 0)
                device_info['vpws_up'] = op_data.get('vpws_up', 0)
                device_info['evpn_total'] = op_data.get('evpn_total', 0)
                device_info['evpn_up'] = op_data.get('evpn_up', 0)
                device_info['vrf_total'] = op_data.get('vrf_total', 0)
                device_info['vrf_up'] = op_data.get('vrf_up', 0)
            except:
                pass
        
        devices.append(device_info)
    
    return devices


def print_header():
    """Print monitor header."""
    width = get_terminal_width()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"{Colors.BOLD}{Colors.CYAN}╔{'═' * (width - 2)}╗{Colors.RESET}")
    title = "SCALER Monitor"
    padding = (width - 2 - len(title)) // 2
    print(f"{Colors.BOLD}{Colors.CYAN}║{' ' * padding}{title}{' ' * (width - 2 - padding - len(title))}║{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}╚{'═' * (width - 2)}╝{Colors.RESET}")
    print(f"{Colors.DIM}Last refresh: {now}{Colors.RESET}")
    print()


def print_extraction_status(stats: dict, watch_mode: bool = False):
    """Print extraction status section."""
    print(f"{Colors.BOLD}📊 Extraction Status{Colors.RESET}")
    print(f"{'─' * 50}")
    
    # Running status
    if stats['is_running']:
        print(f"  Status: {Colors.GREEN}● RUNNING{Colors.RESET} (extracting {stats['current_device']})")
    else:
        print(f"  Status: {Colors.DIM}○ Idle{Colors.RESET}")
    
    # Monitor duration (how long this monitor script has been running)
    if watch_mode:
        monitor_duration = (datetime.now() - MONITOR_START_TIME).total_seconds()
        print(f"  Monitor duration: {Colors.CYAN}{format_duration(monitor_duration)}{Colors.RESET}")
    
    # Extraction service uptime (from log entries)
    if stats['running_since']:
        service_uptime = format_duration(stats['running_since'])
        print(f"  Service uptime: {Colors.CYAN}{service_uptime}{Colors.RESET} ({stats['total_extractions']} cycles)")
    
    # Extraction rate/period
    if stats['extraction_rate']:
        rate_str = format_duration(stats['extraction_rate'])
        print(f"  Extraction period: {Colors.CYAN}every {rate_str}{Colors.RESET}")
    
    # Last extraction - use file modification time for more accurate timing
    if stats['last_extraction']:
        last_time = stats['last_extraction'].strftime('%H:%M:%S')
        ago = format_time_ago(stats['last_extraction'])
        print(f"  Last extraction: {last_time} ({ago})")
    
    # Duration stats
    if stats['last_duration']:
        print(f"  Last duration: {format_duration(stats['last_duration'])}")
    if stats['avg_duration']:
        print(f"  Avg duration: {format_duration(stats['avg_duration'])}")
    
    # Success/failure counts
    total = stats['successful'] + stats['failed']
    if total > 0:
        success_rate = (stats['successful'] / total) * 100
        color = Colors.GREEN if success_rate >= 90 else (Colors.YELLOW if success_rate >= 70 else Colors.RED)
        print(f"  Success rate: {color}{success_rate:.1f}%{Colors.RESET} ({stats['successful']}/{total})")
    
    print()


# Multi-path connection strategy imports (bypass scaler/__init__.py to avoid
# loading pydantic, paramiko, config_parser, etc. — saves ~700ms startup)
try:
    import importlib.util
    _cs_spec = importlib.util.spec_from_file_location(
        "connection_strategy",
        str(SCALER_DIR / "scaler" / "connection_strategy.py"))
    _cs_mod = importlib.util.module_from_spec(_cs_spec)
    _cs_spec.loader.exec_module(_cs_mod)
    detect_device_state = _cs_mod.detect_device_state
    DeviceState = _cs_mod.DeviceState
    get_console_config_for_device = _cs_mod.get_console_config_for_device
    HAS_CONNECTION_STRATEGY = True
    del _cs_spec, _cs_mod
except Exception:
    HAS_CONNECTION_STRATEGY = False


def update_device_state_live(devices: list, configs_dir: Path, stats: dict) -> list:
    """
    Update device states with live detection via multi-path connection.
    Returns list of detected issues for display.
    """
    if not HAS_CONNECTION_STRATEGY:
        return []
    
    detected_issues = []
    
    for dev in devices:
        # Check if device needs live detection
        dev_stats = stats.get("devices", {}).get(dev['name'], {})
        last_status = dev_stats.get('last_status')
        
        # Run detection if:
        # 1. Device has no config (never connected), OR
        # 2. Last extraction failed, OR  
        # 3. Device is marked in recovery, OR
        # 4. DNOS version is N/A (likely in GI/recovery mode), OR
        # 5. Device state is not DNOS (need to confirm state)
        dnos_version = dev.get('dnos_version', '')
        device_state = dev.get('device_state', '')
        needs_detection = (
            not dev.get('has_config') or
            last_status == 'failed' or
            dev.get('recovery_mode_detected', False) or
            dnos_version in ('N/A', '', None) or
            device_state in ('GI', 'BASEOS_SHELL', 'ONIE', 'DN_RECOVERY', 'UNKNOWN', '')
        )
        
        if not needs_detection:
            continue
        
        # Run live state detection
        try:
            class TempDevice:
                def __init__(self, name, ip, serial_number=None):
                    self.hostname = name
                    self.ip = ip
                    self.serial_number = serial_number
                    self.username = "dnroot"
                    self.password = "dnroot"
            
            # Get serial number from operational data
            serial_number = None
            try:
                op_path = configs_dir / dev['name'] / "operational.json"
                if op_path.exists():
                    with open(op_path, 'r') as f:
                        op_data = json.load(f)
                        sn = op_data.get('serial_number')
                        if sn and sn != 'N/A':
                            serial_number = sn
            except:
                pass
            
            temp_dev = TempDevice(dev['name'], dev.get('mgmt_ip', dev['name']), serial_number)
            state, recovery_type, err = detect_device_state(temp_dev)
            
            if state and state != DeviceState.UNREACHABLE:
                # Don't overwrite a known RECOVERY/DN_RECOVERY state with UNKNOWN
                # (SSH may be unreachable while device is genuinely in recovery)
                current_state = dev.get('device_state', '')
                if state == DeviceState.UNKNOWN and current_state in ('RECOVERY', 'DN_RECOVERY'):
                    continue
                
                # Update operational.json with live state
                op_path = configs_dir / dev['name'] / "operational.json"
                op_path.parent.mkdir(parents=True, exist_ok=True)
                op_data = {}
                if op_path.exists():
                    try:
                        with open(op_path, 'r') as f:
                            op_data = json.load(f)
                    except:
                        pass
                
                # Set recovery fields based on live detection
                # GI mode also needs attention (DNOS not deployed)
                is_recovery = state in [DeviceState.DN_RECOVERY, DeviceState.ONIE, DeviceState.BASEOS_SHELL, DeviceState.GI]
                op_data['recovery_mode_detected'] = is_recovery
                op_data['recovery_type'] = recovery_type
                op_data['device_state'] = state.value
                op_data['last_state_check'] = datetime.now().isoformat()
                
                # Note: connection_method and ssh_host are set by refresh_device_state()
                # which is called separately. If not present, call it now.
                if 'connection_method' not in op_data or not op_data.get('connection_method'):
                    try:
                        _cs = importlib.util.spec_from_file_location("_cs_refresh", str(SCALER_DIR / "scaler" / "connection_strategy.py"))
                        _cm = importlib.util.module_from_spec(_cs); _cs.loader.exec_module(_cm)
                        _cm.refresh_device_state(dev['name'], update_operational=True)
                        # Re-read the updated data
                        with open(op_path, 'r') as f:
                            op_data = json.load(f)
                    except:
                        pass
                
                # If in GI mode, also set DNOS version to indicate not running
                # But PRESERVE target versions if they exist (set by wizard)
                if state == DeviceState.GI:
                    op_data['dnos_version'] = 'N/A (GI Mode)'
                    # Don't overwrite target versions - wizard sets these
                    # They'll be preserved from the existing file
                
                # Write back to operational.json
                try:
                    with open(op_path, 'w') as f:
                        json.dump(op_data, f, indent=2)
                except:
                    pass
                
                # Update running.txt header for recovery mode devices
                if is_recovery:
                    try:
                        _ce_spec = importlib.util.spec_from_file_location("_ce", str(SCALER_DIR / "scaler" / "config_extractor.py"))
                        _ce_mod = importlib.util.module_from_spec(_ce_spec); _ce_spec.loader.exec_module(_ce_mod)
                        _ce_mod.update_recovery_mode_header(dev['name'])
                    except Exception:
                        pass
                
                # Update in-memory device object
                dev['recovery_mode_detected'] = is_recovery
                dev['recovery_type'] = recovery_type
                dev['device_state'] = state.value
                
                # Track for summary display
                console_cfg = get_console_config_for_device(dev['name'])
                detected_issues.append({
                    'name': dev['name'],
                    'state': state,
                    'recovery_type': recovery_type,
                    'console': console_cfg
                })
        except Exception as e:
            pass  # Don't break monitor on errors
    
    return detected_issues


def update_lldp_for_devices(devices: list, configs_dir: Path) -> int:
    """
    Fetch and update LLDP neighbors for healthy DNOS devices.
    
    Only runs for devices in DNOS mode (not recovery/GI mode).
    
    Args:
        devices: List of device info dicts
        configs_dir: Path to configs directory
    
    Returns:
        Number of devices updated
    """
    import paramiko
    
    # Import LLDP functions from config_extractor
    try:
        from scaler.config_extractor import (
            fetch_lldp_neighbors,
            check_lldp_configured,
            enable_lldp_on_device,
            update_lldp_in_operational_json
        )
    except ImportError:
        return 0
    
    updated = 0
    
    for dev in devices:
        # Only update LLDP for healthy DNOS devices
        device_state = dev.get('device_state', '')
        dnos_version = dev.get('dnos_version', '')
        
        # Skip devices in recovery mode or without DNOS
        if device_state in ('GI', 'BASEOS_SHELL', 'ONIE', 'DN_RECOVERY', 'UNREACHABLE'):
            continue
        if not dnos_version or dnos_version.startswith('N/A'):
            continue
        
        # Try SSH connection to fetch LLDP
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Get connection info from operational.json
            op_path = configs_dir / dev['name'] / "operational.json"
            serial_number = None
            mgmt_ip = None
            
            if op_path.exists():
                try:
                    with open(op_path, 'r') as f:
                        op_data = json.load(f)
                        serial_number = op_data.get('serial_number')
                        mgmt_ip = op_data.get('mgmt_ip')
                except:
                    pass
            
            # Try connection - serial number first, then mgmt IP, then hostname
            connected = False
            for target in [serial_number, mgmt_ip, dev['name']]:
                if not target or target == 'N/A':
                    continue
                try:
                    ssh.connect(
                        target,
                        username='dnroot',
                        password='dnroot',
                        timeout=10,
                        allow_agent=False,
                        look_for_keys=False
                    )
                    connected = True
                    break
                except:
                    continue
            
            if not connected:
                continue
            
            # Get shell channel
            channel = ssh.invoke_shell(width=200, height=50)
            channel.settimeout(15)
            time.sleep(1)
            
            # Drain initial output
            while channel.recv_ready():
                channel.recv(65535)
            
            # Fetch LLDP neighbors
            lldp_data = fetch_lldp_neighbors(channel, dev['name'])
            
            # If no neighbors and LLDP not configured, enable it
            if lldp_data.get('lldp_neighbor_count', 0) == 0:
                if not check_lldp_configured(channel):
                    # Enable LLDP
                    if enable_lldp_on_device(channel):
                        # Wait for LLDP to discover neighbors
                        time.sleep(5)
                        # Retry fetch
                        lldp_data = fetch_lldp_neighbors(channel, dev['name'])
            
            # Close connection
            try:
                channel.close()
                ssh.close()
            except:
                pass
            
            # Update operational.json
            if update_lldp_in_operational_json(dev['name'], lldp_data):
                updated += 1
                # Also update in-memory device object
                dev['lldp_neighbor_count'] = lldp_data.get('lldp_neighbor_count', 0)
        
        except Exception as e:
            pass  # Don't break on LLDP fetch errors
    
    return updated


def print_device_table(devices: list):
    """Print device status table."""
    print(f"{Colors.BOLD}📡 Device Status ({len(devices)} devices){Colors.RESET}")
    print(f"{'─' * 130}")
    
    # Header - show ALL network services
    print(f"  {'Device':<8} {'Type':<12} {'DNOS':<25} {'Last':<8} {'Unchanged':<10} {'BGP':<6} {'Services':<35} {'Status'}")
    print(f"  {'─' * 8} {'─' * 12} {'─' * 25} {'─' * 8} {'─' * 10} {'─' * 6} {'─' * 35} {'─' * 10}")
    
    for dev in devices:
        name = dev['name']
        sys_type = dev['system_type'][:12] if dev['system_type'] else 'N/A'
        dnos = dev['dnos_version'][:25] if dev['dnos_version'] else 'N/A'
        
        # Last check
        if dev['last_modified']:
            last_check = format_time_ago(dev['last_modified'])
        else:
            last_check = 'Never'
        
        # Unchanged checks
        unchanged = f"{dev['unchanged_checks']} chks" if dev['unchanged_checks'] > 0 else '-'
        
        # BGP status
        bgp = f"{dev['bgp_up']}/{dev['bgp_peers']}" if dev['bgp_peers'] > 0 else '-'
        
        # Build services string - show ALL service types
        services_parts = []
        
        # FXC
        if dev['fxc_total'] > 0:
            fxc_color = Colors.GREEN if dev['fxc_up'] == dev['fxc_total'] else Colors.YELLOW
            services_parts.append(f"FXC:{fxc_color}{dev['fxc_up']}/{dev['fxc_total']}{Colors.RESET}")
        
        # VPWS (EVPN-VPWS)
        if dev['vpws_total'] > 0:
            vpws_color = Colors.GREEN if dev['vpws_up'] == dev['vpws_total'] else Colors.YELLOW
            services_parts.append(f"VPWS:{vpws_color}{dev['vpws_up']}/{dev['vpws_total']}{Colors.RESET}")
        
        # EVPN (EVPN-VPLS)
        if dev['evpn_total'] > 0:
            evpn_color = Colors.GREEN if dev['evpn_up'] == dev['evpn_total'] else Colors.YELLOW
            services_parts.append(f"EVPN:{evpn_color}{dev['evpn_up']}/{dev['evpn_total']}{Colors.RESET}")
        
        # VRF/L3VPN
        if dev['vrf_total'] > 0:
            vrf_color = Colors.GREEN if dev['vrf_up'] == dev['vrf_total'] else Colors.YELLOW
            services_parts.append(f"VRF:{vrf_color}{dev['vrf_up']}/{dev['vrf_total']}{Colors.RESET}")
        
        services = ' '.join(services_parts) if services_parts else '-'
        
        # Status indicator - show live-detected state if available
        if dev.get('recovery_mode_detected') or dev.get('device_state') == 'RECOVERY':
            recovery_type = dev.get('recovery_type', '')
            if recovery_type == 'ONIE':
                status = f"{Colors.BOLD}{Colors.RED}⚠ ONIE{Colors.RESET}"
            elif recovery_type == 'BASEOS_SHELL':
                status = f"{Colors.YELLOW}⚠ BASEOS_SHELL{Colors.RESET}"
            elif recovery_type == 'DN_RECOVERY' or dev.get('device_state') == 'RECOVERY':
                status = f"{Colors.BOLD}{Colors.RED}🔴 RECOVERY{Colors.RESET}"
            elif recovery_type == 'GI':
                status = f"{Colors.CYAN}ℹ GI_MODE{Colors.RESET}"
            elif recovery_type == 'STANDALONE':
                status = f"{Colors.YELLOW}⚠ STANDALONE{Colors.RESET}"
            else:
                status = f"{Colors.BOLD}{Colors.RED}⚠ RECOVERY{Colors.RESET}"
        elif dev['upgrade_in_progress']:
            status = f"{Colors.MAGENTA}⚡ UPGRADING{Colors.RESET}"
        elif not dev['has_config']:
            status = f"{Colors.RED}✗ No config{Colors.RESET}"
        elif dev['dnos_version'] in ('N/A', '', None) or not dev['dnos_version']:
            # DNOS version N/A means device is likely in GI mode or unreachable
            status = f"{Colors.CYAN}? GI/No DNOS{Colors.RESET}"
        else:
            status = f"{Colors.GREEN}✓ OK{Colors.RESET}"
        
        print(f"  {name:<8} {sys_type:<12} {dnos:<25} {last_check:<8} {unchanged:<10} {bgp:<6} {services:<35} {status}")
    
    print()


def print_history_summary(history_dir: Path):
    """Print history summary."""
    print(f"{Colors.BOLD}📁 History Summary{Colors.RESET}")
    print(f"{'─' * 50}")
    
    total_files = 0
    total_size = 0
    
    for device_dir in sorted(history_dir.iterdir()):
        if not device_dir.is_dir() or device_dir.name.startswith('.'):
            continue
        
        files = list(device_dir.glob("*.txt"))
        size = sum(f.stat().st_size for f in files)
        total_files += len(files)
        total_size += size
        
        print(f"  {device_dir.name}: {len(files)} files ({size / 1024 / 1024:.1f} MB)")
    
    print(f"  {'─' * 30}")
    print(f"  Total: {total_files} files ({total_size / 1024 / 1024:.1f} MB)")
    print()


def print_recent_activity(log_file: Path, max_lines: int = 10):
    """Print recent log activity."""
    print(f"{Colors.BOLD}📜 Recent Activity{Colors.RESET}")
    print(f"{'─' * 80}")
    
    entries = parse_log_entries(log_file, max_entries=max_lines)
    
    for entry in entries[-max_lines:]:
        ts = entry['timestamp'].strftime('%H:%M:%S')
        msg = entry['message'][:70]
        
        # Color based on content
        if 'FAILED' in msg:
            color = Colors.RED
        elif 'No change' in msg or 'success' in msg.lower():
            color = Colors.GREEN
        elif 'Extracting' in msg:
            color = Colors.CYAN
        elif 'Starting' in msg or 'complete' in msg:
            color = Colors.YELLOW
        else:
            color = Colors.RESET
        
        print(f"  {Colors.DIM}{ts}{Colors.RESET} {color}{msg}{Colors.RESET}")
    
    print()


def main():
    parser = argparse.ArgumentParser(description='SCALER Monitor - Monitor config extraction status')
    parser.add_argument('--watch', '-w', action='store_true', help='Continuous monitoring (live refresh)')
    parser.add_argument('--interval', '-i', type=int, default=1, help='Refresh interval in seconds for watch mode (default: 1)')
    parser.add_argument('--compact', '-c', action='store_true', help='Compact output (devices only)')
    # Legacy: --once/-1 still works but is now default
    parser.add_argument('--once', '-1', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    
    configs_dir = SCALER_DIR / "db" / "configs"
    history_dir = SCALER_DIR / "db" / "history"
    log_file = SCALER_DIR / "extraction.log"
    
    # One-time is now default (use --watch/-w for continuous)
    continuous = args.watch
    
    try:
        while True:
            if continuous:
                clear_screen()
            
            print_header()
            
            # Get stats
            stats = get_extraction_stats(log_file)
            devices = get_device_status(configs_dir)
            
            # Get last extraction time from file modification (more reliable)
            if devices:
                last_mod_times = [d['last_modified'] for d in devices if d['last_modified']]
                if last_mod_times:
                    stats['last_extraction'] = max(last_mod_times)
            
            # Get last extraction time from file modification (more reliable)
            if devices:
                last_mod_times = [d['last_modified'] for d in devices if d['last_modified']]
                if last_mod_times:
                    stats['last_extraction'] = max(last_mod_times)
            
            # Live SSH probing only in watch mode (skip for quick one-shot status)
            detected_issues = []
            if continuous:
                detected_issues = update_device_state_live(devices, configs_dir, stats)
                update_lldp_for_devices(devices, configs_dir)
            
            # Print sections (with updated live states)
            print_extraction_status(stats, watch_mode=continuous)
            print_device_table(devices)
            
            # Show detailed summary if issues detected
            if detected_issues:
                print()
                print(f"{Colors.BOLD}{'═' * 80}{Colors.RESET}")
                print(f"{Colors.BOLD}{Colors.CYAN}📊 DEVICE STATE DETECTION SUMMARY{Colors.RESET}")
                print(f"{Colors.BOLD}{'═' * 80}{Colors.RESET}")
                print()
                
                for issue in detected_issues:
                    state = issue['state']
                    name = issue['name']
                    recovery_type = issue['recovery_type']
                    console_cfg = issue['console']
                    
                    if state == DeviceState.ONIE:
                        print(f"{Colors.BOLD}{Colors.RED}⚠️  {name}: ONIE RESCUE MODE{Colors.RESET}")
                        print(f"{Colors.RED}   State: Lowest-level bootloader{Colors.RESET}")
                        print(f"{Colors.YELLOW}   Cause: BaseOS missing or corrupted{Colors.RESET}")
                        if console_cfg:
                            print(f"{Colors.CYAN}   Console: {console_cfg['host']} port {console_cfg['port']}{Colors.RESET}")
                        print(f"{Colors.GREEN}   Fix: System Restore → Install BaseOS → Deploy{Colors.RESET}")
                        print()
                    
                    elif state == DeviceState.BASEOS_SHELL:
                        print(f"{Colors.BOLD}{Colors.YELLOW}⚠️  {name}: BASEOS SHELL MODE{Colors.RESET}")
                        print(f"{Colors.YELLOW}   State: Linux shell (GI not started){Colors.RESET}")
                        print(f"{Colors.YELLOW}   Cause: GI container not running{Colors.RESET}")
                        if console_cfg:
                            print(f"{Colors.CYAN}   Console: {console_cfg['host']} port {console_cfg['port']}{Colors.RESET}")
                        print(f"{Colors.CYAN}   Credentials: dn / drivenets{Colors.RESET}")
                        print(f"{Colors.GREEN}   Fix: System Restore → dncli → Load images → Deploy{Colors.RESET}")
                        print()
                    
                    elif state == DeviceState.DN_RECOVERY:
                        print(f"{Colors.BOLD}{Colors.RED}⚠️  {name}: DN_RECOVERY MODE{Colors.RESET}")
                        print(f"{Colors.RED}   State: DNOS failed to boot{Colors.RESET}")
                        print(f"{Colors.YELLOW}   Cause: Software corruption or config error{Colors.RESET}")
                        if console_cfg:
                            print(f"{Colors.CYAN}   Console: {console_cfg['host']} port {console_cfg['port']}{Colors.RESET}")
                        print(f"{Colors.GREEN}   Fix: System Restore → Factory reset → Deploy{Colors.RESET}")
                        print()
                    
                    elif state == DeviceState.GI:
                        print(f"{Colors.BOLD}{Colors.CYAN}ℹ️  {name}: GI MODE{Colors.RESET}")
                        print(f"{Colors.CYAN}   State: Golden Image ready{Colors.RESET}")
                        print(f"{Colors.GREEN}   Next: Image Upgrade → Load images → Deploy{Colors.RESET}")
                        print()
                    
                    elif state == DeviceState.STANDALONE:
                        print(f"{Colors.BOLD}{Colors.YELLOW}⚠️  {name}: STANDALONE MODE{Colors.RESET}")
                        print(f"{Colors.YELLOW}   State: One NCC down{Colors.RESET}")
                        print(f"{Colors.GREEN}   Action: SSH and diagnose NCC failure{Colors.RESET}")
                        print()
                
                print(f"{Colors.BOLD}{'═' * 80}{Colors.RESET}")
                print()
                
                # Prompt to launch wizard (one-time mode only)
                if not continuous:
                    try:
                        response = input(f"{Colors.GREEN}Launch wizard to fix these devices? [Y/n]: {Colors.RESET}").strip().lower()
                        if response in ('', 'y', 'yes'):
                            print(f"\n{Colors.CYAN}Launching SCALER wizard...{Colors.RESET}\n")
                            subprocess.run(["/home/dn/bin/scaler-wizard"])
                            sys.exit(0)
                    except (EOFError, KeyboardInterrupt):
                        pass
            
            if not args.compact:
                print_history_summary(history_dir)
                print_recent_activity(log_file)
            
            if not continuous:
                break
            
            # Footer for continuous mode - show actual interval
            interval_str = f"{args.interval}s" if args.interval == 1 else f"{args.interval} seconds"
            print(f"{Colors.DIM}Press Ctrl+C to exit. Live refresh: {interval_str}{Colors.RESET}")
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Monitor stopped.{Colors.RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()

