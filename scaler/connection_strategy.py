"""
Multi-path device connection strategy with automatic failover.

This module provides intelligent connection strategies for monitoring DriveNets devices:
1. Primary SSH connection
2. Console fallback (for devices with console server access)
3. State detection across all connection methods
4. Automatic failover when one method fails

Usage:
    from scaler.connection_strategy import DeviceConnector, detect_device_state
    
    connector = DeviceConnector(device)
    state, recovery_type, config = connector.connect_and_detect()
"""

import time
import socket
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ConnectionMethod(Enum):
    """Available connection methods for device access."""
    SSH_SN = "ssh_sn"               # Priority 1: SSH to serial number hostname
    SSH_MGMT = "ssh_mgmt"           # Priority 2: SSH to management IP
    CONSOLE = "console"              # Priority 3: Console server access
    SSH_LOOPBACK = "ssh_loopback"   # Priority 4: SSH to loopback IP


# Credential sets to try in order
CREDENTIAL_SETS = [
    {"username": "dnroot", "password": "dnroot"},       # DNOS/GI standard
    {"username": "dn", "password": "drivenets"},        # BaseOS/ONIE
    {"username": "admin", "password": "admin"},         # Some systems
    {"username": "root", "password": "drivenets"},      # Root fallback
]


class DeviceState(Enum):
    """Detected device states."""
    DNOS = "DNOS"                   # Normal DNOS operation
    GI = "GI"                       # GI mode (ready for DNOS deploy)
    BASEOS_SHELL = "BASEOS_SHELL"  # BaseOS shell (need dncli)
    DN_RECOVERY = "DN_RECOVERY"     # DNOS recovery mode
    ONIE = "ONIE"                   # ONIE rescue mode
    STANDALONE = "STANDALONE"       # One NCC down
    UNREACHABLE = "UNREACHABLE"     # Cannot connect via any method
    UNKNOWN = "UNKNOWN"             # Connected but state unclear


@dataclass
class ConnectionResult:
    """Result of a connection attempt."""
    success: bool
    method: ConnectionMethod
    state: DeviceState
    recovery_type: str
    error: Optional[str] = None
    channel: Any = None  # Paramiko channel if successful
    output: str = ""     # Console/SSH output captured


class DeviceConnector:
    """
    Intelligent device connector with multi-path failover.
    
    Attempts connections in priority order:
    1. SSH to management IP (fastest, most reliable)
    2. Console server (for devices without network access)
    3. SSH to loopback IP (alternative if mgmt network down)
    
    Each method returns device state + config access.
    """
    
    def __init__(self, device: Any, console_config: Optional[Dict] = None):
        """
        Initialize connector for a device.
        
        Args:
            device: Device object with ip, hostname, username, password
            console_config: Optional console server config
                {
                    'host': 'console-b15',
                    'port': 13,
                    'user': 'dn',
                    'password': 'drive1234'
                }
        """
        self.device = device
        self.console_config = console_config
        self.last_successful_method = None
        
    def connect_and_detect(self, timeout: int = 30) -> ConnectionResult:
        """
        Connect using best available method and detect device state.
        
        Tries methods in order:
        1. SSH to management IP
        2. Console (if configured)
        3. SSH to loopback IP (if known)
        
        Returns:
            ConnectionResult with success status, method used, and device state
        """
        methods = self._get_connection_methods()
        
        last_error = None
        for method in methods:
            try:
                result = self._try_connection(method, timeout)
                if result.success:
                    self.last_successful_method = method
                    return result
                last_error = result.error
            except Exception as e:
                last_error = str(e)
                continue
        
        # All methods failed
        return ConnectionResult(
            success=False,
            method=methods[0] if methods else ConnectionMethod.SSH_MGMT,
            state=DeviceState.UNREACHABLE,
            recovery_type="",
            error=last_error or "All connection methods failed"
        )
    
    def _get_connection_methods(self) -> list:
        """Get list of connection methods to try, in priority order."""
        methods = []
        
        # 1. SSH to serial number hostname (FASTEST - direct DNS resolution)
        sn = self._get_serial_number()
        if sn:
            methods.append(ConnectionMethod.SSH_SN)
        
        # 2. SSH to management IP
        if hasattr(self.device, 'ip') and self.device.ip:
            methods.append(ConnectionMethod.SSH_MGMT)
        
        # 3. Console (if configured)
        if self.console_config:
            methods.append(ConnectionMethod.CONSOLE)
        
        # 4. SSH to loopback (if known)
        if hasattr(self.device, 'loopback_ip') and self.device.loopback_ip:
            methods.append(ConnectionMethod.SSH_LOOPBACK)
        
        return methods
    
    def _get_serial_number(self) -> Optional[str]:
        """Get device serial number for SSH via SN hostname."""
        # First check device object
        if hasattr(self.device, 'serial_number') and self.device.serial_number:
            return self.device.serial_number
        
        # Check operational.json
        try:
            from pathlib import Path
            import json
            op_file = Path(f"/home/dn/SCALER/db/configs/{self.device.hostname}/operational.json")
            if op_file.exists():
                with open(op_file) as f:
                    data = json.load(f)
                    sn = data.get('serial_number')
                    if sn and sn != 'N/A':
                        return sn
        except:
            pass
        
        return None
    
    def _try_connection(self, method: ConnectionMethod, timeout: int) -> ConnectionResult:
        """Try a specific connection method."""
        if method == ConnectionMethod.SSH_SN:
            sn = self._get_serial_number()
            return self._connect_ssh_multi_creds(sn, timeout, method)
        elif method == ConnectionMethod.SSH_MGMT:
            return self._connect_ssh_multi_creds(self.device.ip, timeout, method)
        elif method == ConnectionMethod.CONSOLE:
            return self._connect_console(timeout)
        elif method == ConnectionMethod.SSH_LOOPBACK:
            return self._connect_ssh_multi_creds(self.device.loopback_ip, timeout, method)
        else:
            return ConnectionResult(
                success=False,
                method=method,
                state=DeviceState.UNKNOWN,
                recovery_type="",
                error="Unsupported connection method"
            )
    
    def _connect_ssh_multi_creds(self, host: str, timeout: int, method: ConnectionMethod) -> ConnectionResult:
        """
        Connect via SSH trying multiple credential sets.
        
        Priority order for credentials:
        1. Device's stored credentials (if any)
        2. dnroot/dnroot (DNOS/GI standard)
        3. dn/drivenets (BaseOS/ONIE)
        4. admin/admin (some systems)
        5. root/drivenets (root fallback)
        """
        import paramiko
        import base64
        
        # Build credential list - device creds first, then standard sets
        creds_to_try = []
        
        # Add device's stored credentials first
        if hasattr(self.device, 'password') and self.device.password:
            password = self.device.password
            try:
                password = base64.b64decode(password).decode('utf-8')
            except:
                pass
            username = getattr(self.device, 'username', None) or 'dnroot'
            creds_to_try.append({"username": username, "password": password})
        
        # Add standard credential sets
        for cred in CREDENTIAL_SETS:
            # Skip if already added from device config
            if not any(c['username'] == cred['username'] and c['password'] == cred['password'] 
                      for c in creds_to_try):
                creds_to_try.append(cred)
        
        last_error = None
        for cred in creds_to_try:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    host,
                    username=cred['username'],
                    password=cred['password'],
                    timeout=timeout,
                    banner_timeout=15,
                    auth_timeout=15,
                    allow_agent=False,
                    look_for_keys=False
                )
                
                # Get prompt to detect state
                channel = ssh.invoke_shell(width=200, height=50)
                time.sleep(2)
                output = channel.recv(8192).decode('utf-8', errors='replace')
                
                # Send newline to get fresh prompt
                channel.send("\r\n")
                time.sleep(1)
                output += channel.recv(8192).decode('utf-8', errors='replace')
                
                # Detect state
                state, recovery_type = self._detect_state_from_output(output)
                
                return ConnectionResult(
                    success=True,
                    method=method,
                    state=state,
                    recovery_type=recovery_type,
                    channel=channel,
                    output=output
                )
                
            except paramiko.AuthenticationException:
                last_error = f"Auth failed for {cred['username']}"
                continue  # Try next credential set
            except socket.timeout:
                last_error = "SSH timeout"
                break  # Don't try more creds if timeout
            except socket.gaierror:
                last_error = f"DNS lookup failed for {host}"
                break  # Don't try more creds if host not found
            except Exception as e:
                last_error = f"SSH failed: {str(e)[:40]}"
                continue
        
        return ConnectionResult(
            success=False,
            method=method,
            state=DeviceState.UNREACHABLE,
            recovery_type="",
            error=last_error or "All credentials failed"
        )
    
    def _connect_console(self, timeout: int) -> ConnectionResult:
        """Connect via console server and detect device state."""
        if not self.console_config:
            return ConnectionResult(
                success=False,
                method=ConnectionMethod.CONSOLE,
                state=DeviceState.UNREACHABLE,
                recovery_type="",
                error="Console not configured"
            )
        
        try:
            import paramiko
            
            # Connect to console server
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.console_config['host'],
                username=self.console_config['user'],
                password=self.console_config['password'],
                timeout=15
            )
            
            channel = ssh.invoke_shell(width=200, height=50)
            channel.settimeout(30)
            time.sleep(1.5)
            _ = channel.recv(8192).decode("utf-8", errors="replace")
            
            # Navigate to device port
            channel.send("3\r\n")  # Port access
            time.sleep(3)
            _ = channel.recv(8192).decode("utf-8", errors="replace")
            
            port = self.console_config.get('port', 13)
            channel.send(f"{port}\r\n")
            time.sleep(1.5)
            channel.send("\r\n")
            time.sleep(2)
            
            output = channel.recv(8192).decode("utf-8", errors="replace")
            
            # Try to login using all credential sets
            lower = output.lower()
            if "login" in lower or "username" in lower:
                logged_in = False
                for cred in CREDENTIAL_SETS:
                    channel.send(cred['username'] + "\r\n")
                    time.sleep(0.8)
                    channel.send(cred['password'] + "\r\n")
                    time.sleep(3)
                    new_output = channel.recv(8192).decode("utf-8", errors="replace")
                    output += new_output
                    
                    # Check if login succeeded (no "incorrect" and got a prompt)
                    new_lower = new_output.lower()
                    if "incorrect" not in new_lower and "failed" not in new_lower:
                        if "#" in new_output or "$" in new_output or ">" in new_output:
                            logged_in = True
                            break
                    
                    # Still at login prompt - try next credential
                    if "login" in new_lower:
                        continue
                    else:
                        # Got past login somehow
                        break
            
            # Get prompt
            channel.send("\r\n")
            time.sleep(2)
            output += channel.recv(8192).decode("utf-8", errors="replace")
            
            # Detect state
            state, recovery_type = self._detect_state_from_output(output)
            
            # If in GI mode, try to get management IP and switch to SSH (preferred)
            if state == DeviceState.GI:
                try:
                    import re
                    channel.send("show interfaces management | no-more\r\n")
                    time.sleep(3)
                    
                    mgmt_output = ""
                    while channel.recv_ready():
                        mgmt_output += channel.recv(8192).decode("utf-8", errors="replace")
                        time.sleep(0.3)
                    
                    # Parse management IP
                    mgmt_ip = None
                    for line in mgmt_output.split('\n'):
                        if 'mgmt' in line.lower() and 'up' in line.lower():
                            ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                            if ip_match:
                                potential_ip = ip_match.group(1)
                                if not potential_ip.startswith('127.'):
                                    mgmt_ip = potential_ip
                                    break
                    
                    if mgmt_ip:
                        # Close console and try SSH to management IP
                        try:
                            channel.close()
                            ssh.close()
                        except:
                            pass
                        
                        # Try SSH with multiple credentials
                        for cred in CREDENTIAL_SETS:
                            try:
                                new_ssh = paramiko.SSHClient()
                                new_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                                new_ssh.connect(
                                    mgmt_ip,
                                    username=cred['username'],
                                    password=cred['password'],
                                    timeout=10,
                                    banner_timeout=10,
                                    auth_timeout=10,
                                    allow_agent=False,
                                    look_for_keys=False
                                )
                                
                                new_channel = new_ssh.invoke_shell(width=200, height=50)
                                time.sleep(1)
                                new_output = new_channel.recv(8192).decode("utf-8", errors="replace")
                                
                                return ConnectionResult(
                                    success=True,
                                    method=ConnectionMethod.SSH_MGMT,
                                    state=state,
                                    recovery_type=recovery_type,
                                    channel=new_channel,
                                    output=new_output
                                )
                            except:
                                continue
                except:
                    pass  # Fall through to return console connection
            
            return ConnectionResult(
                success=True,
                method=ConnectionMethod.CONSOLE,
                state=state,
                recovery_type=recovery_type,
                channel=channel,
                output=output
            )
            
        except Exception as e:
            return ConnectionResult(
                success=False,
                method=ConnectionMethod.CONSOLE,
                state=DeviceState.UNREACHABLE,
                recovery_type="",
                error=f"Console failed: {str(e)[:50]}"
            )
    
    def _detect_state_from_output(self, output: str) -> Tuple[DeviceState, str]:
        """
        Detect device state from console/SSH output.
        
        Returns:
            (DeviceState, recovery_type_string)
        """
        lower = output.lower()
        
        # Priority order for detection (most specific first)
        
        # 1. ONIE rescue mode (highest priority - most critical)
        if "onie:/" in lower or "onie-" in lower or "onie #" in lower:
            return DeviceState.ONIE, "ONIE"
        
        # 2. GI mode - look for GI prompt patterns
        # GI# or GI(timestamp)# or gicli patterns
        import re
        if re.search(r'gi[#>]|gi\([^)]*\)[#>]', lower) or "gicli" in lower:
            return DeviceState.GI, "GI"
        
        # 3. BaseOS shell - dn@SERIAL:~$ pattern
        if re.search(r'(dn|root)@[a-zA-Z0-9]+:~?\$', output):
            return DeviceState.BASEOS_SHELL, "BASEOS_SHELL"
        
        # 4. DN Recovery mode
        if "dn-recovery" in lower or "dnos recovery" in lower or "recovery mode" in lower:
            return DeviceState.DN_RECOVERY, "DN_RECOVERY"
        
        # 5. Standalone mode (one NCC down)
        if "ncc: 1/2 up" in lower or "standalone" in lower:
            return DeviceState.STANDALONE, "STANDALONE"
        
        # 6. Normal DNOS operation - look for DNOS CLI prompt
        # PE-1#, router#, dnos#, or hostname# pattern
        if re.search(r'(pe-?\d+|router|dnos|[a-zA-Z0-9_-]+)[#>]\s*$', lower, re.MULTILINE):
            # Verify it's actually DNOS by checking for DNOS-specific output
            if "#" in output and ("show" in lower or "config" in lower or "interface" in lower 
                                  or "router" in lower or "pe-" in lower):
                return DeviceState.DNOS, "DNOS"
            # Simple prompt check - assume DNOS if we got a # prompt
            if "#" in output:
                return DeviceState.DNOS, "DNOS"
        
        # 7. Unknown state
        return DeviceState.UNKNOWN, ""


def get_console_config_for_device(hostname: str) -> Optional[Dict]:
    """
    Get console server configuration for a specific device.
    
    Returns console config dict or None if device doesn't have console access.
    """
    # Map of devices to console configurations
    CONSOLE_MAPPINGS = {
        "PE-2": {
            'host': 'console-b15',
            'port': 13,
            'user': 'dn',
            'password': 'drive1234'
        },
        # Add more devices as needed
        # "PE-3": {'host': 'console-b16', 'port': 5, ...},
    }
    
    return CONSOLE_MAPPINGS.get(hostname)


def detect_device_state(device: Any) -> Tuple[DeviceState, str, Optional[str]]:
    """
    High-level helper to detect device state using best available method.
    
    Args:
        device: Device object
        
    Returns:
        (DeviceState, recovery_type, error_message)
    """
    console_config = get_console_config_for_device(device.hostname)
    connector = DeviceConnector(device, console_config)
    result = connector.connect_and_detect()
    
    return result.state, result.recovery_type, result.error


def refresh_device_state(hostname: str, update_operational: bool = True) -> Tuple[DeviceState, str, Optional[str]]:
    """
    Refresh device state and optionally update operational.json.
    
    This is the main entry point for refreshing device state from anywhere.
    
    Connection priority:
    1. SSH to serial number hostname (fastest, direct DNS)
    2. SSH to management IP
    3. Console server (if configured)
    4. SSH to loopback IP
    
    Each method tries multiple credential sets:
    - dnroot/dnroot (DNOS/GI)
    - dn/drivenets (BaseOS/ONIE)
    - admin/admin
    - root/drivenets
    
    Args:
        hostname: Device hostname (e.g., "PE-2")
        update_operational: If True, updates operational.json with detected state
        
    Returns:
        (DeviceState, recovery_type, error_message)
    """
    from pathlib import Path
    import json
    from datetime import datetime
    
    # Load existing operational data to get IP and serial number
    op_path = Path(f"/home/dn/SCALER/db/configs/{hostname}/operational.json")
    serial_number = None
    mgmt_ip = None
    
    if op_path.exists():
        try:
            with open(op_path) as f:
                op_data = json.load(f)
                sn = op_data.get('serial_number')
                if sn and sn != 'N/A':
                    serial_number = sn
                ip = op_data.get('mgmt_ip')
                if ip and ip != 'N/A':
                    mgmt_ip = ip
        except:
            pass
    
    # Create temp device object
    class TempDevice:
        def __init__(self):
            self.hostname = hostname
            self.ip = mgmt_ip
            self.serial_number = serial_number
            self.username = "dnroot"
            self.password = "dnroot"
    
    device = TempDevice()
    console_config = get_console_config_for_device(hostname)
    connector = DeviceConnector(device, console_config)
    result = connector.connect_and_detect()
    
    # Update operational.json with detected state
    if update_operational and result.state != DeviceState.UNREACHABLE:
        try:
            op_data = {}
            if op_path.exists():
                with open(op_path, 'r') as f:
                    op_data = json.load(f)
            
            # Mark GI, BASEOS_SHELL, ONIE, DN_RECOVERY as recovery modes
            is_recovery = result.state in [
                DeviceState.GI, 
                DeviceState.BASEOS_SHELL, 
                DeviceState.ONIE, 
                DeviceState.DN_RECOVERY
            ]
            
            op_data['recovery_mode_detected'] = is_recovery
            op_data['recovery_type'] = result.recovery_type
            op_data['device_state'] = result.state.value
            op_data['last_state_check'] = datetime.now().isoformat()
            
            # Store connection method and the actual host that worked (for CURSOR SSH)
            method_map = {
                ConnectionMethod.SSH_SN: "SSH→SN",
                ConnectionMethod.SSH_MGMT: "SSH→MGMT",
                ConnectionMethod.CONSOLE: "Console",
                ConnectionMethod.SSH_LOOPBACK: "SSH→Loopback"
            }
            op_data['connection_method'] = method_map.get(result.method, str(result.method))
            
            # Store the actual SSH host that worked (serial_number for SSH→SN, mgmt_ip for SSH→MGMT)
            if result.method == ConnectionMethod.SSH_SN and serial_number:
                op_data['ssh_host'] = serial_number
            elif result.method == ConnectionMethod.SSH_MGMT and mgmt_ip:
                # Strip CIDR suffix if present
                op_data['ssh_host'] = mgmt_ip.split('/')[0] if '/' in str(mgmt_ip) else mgmt_ip
            elif result.method == ConnectionMethod.CONSOLE:
                op_data['ssh_host'] = 'console'  # Indicate console-only access
            else:
                op_data['ssh_host'] = serial_number or (mgmt_ip.split('/')[0] if mgmt_ip and '/' in str(mgmt_ip) else mgmt_ip) or hostname
            
            # Update DNOS version indicator based on state
            if result.state == DeviceState.GI:
                op_data['dnos_version'] = 'N/A (GI Mode)'
            elif result.state == DeviceState.BASEOS_SHELL:
                op_data['dnos_version'] = 'N/A (BaseOS Shell)'
            elif result.state == DeviceState.ONIE:
                op_data['dnos_version'] = 'N/A (ONIE)'
            elif result.state == DeviceState.DN_RECOVERY:
                op_data['dnos_version'] = 'N/A (DN Recovery)'
            
            op_path.parent.mkdir(parents=True, exist_ok=True)
            with open(op_path, 'w') as f:
                json.dump(op_data, f, indent=4)
        except Exception:
            pass  # Don't fail on write errors
    
    return result.state, result.recovery_type, result.error
