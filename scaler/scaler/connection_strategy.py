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
import logging
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Suppress noisy paramiko transport-layer tracebacks (e.g. SSH banner errors)
logging.getLogger("paramiko").setLevel(logging.WARNING)
logging.getLogger("paramiko.transport").setLevel(logging.WARNING)


class ConnectionMethod(Enum):
    """Available connection methods for device access."""
    SSH_SN = "ssh_sn"               # Priority 1: SSH to serial number hostname
    SSH_MGMT = "ssh_mgmt"           # Priority 2: SSH to management IP
    SSH_NCC = "ssh_ncc"             # Priority 2.5: SSH to KVM NCC hostname (DNOS mode only)
    VIRSH_CONSOLE = "virsh_console" # Priority 2.7: virsh console via KVM host (GI mode for KVM NCCs)
    CONSOLE = "console"              # Priority 3: Console server access (NCP-only for clusters)
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
    ssh: Any = None       # Paramiko SSHClient (needed to keep connection alive)
    channel: Any = None  # Paramiko channel if successful
    output: str = ""     # Console/SSH output captured
    host: str = ""       # IP/hostname that was connected to
    active_ncc_vm: str = ""   # VM name of active NCC (e.g. "kvm108-cl408d-ncc1")
    ncc_id: Optional[int] = None  # Auto-detected NCC ID from VM name (0 or 1)


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
        
        # Check known state from operational.json to optimize connection order
        known_state = None
        try:
            from pathlib import Path
            import json
            op_file = Path(f"/home/dn/SCALER/db/configs/{self.device.hostname}/operational.json")
            if op_file.exists():
                with open(op_file) as f:
                    op_data = json.load(f)
                    known_state = op_data.get('device_state')
        except:
            pass
        
        # If we know it's in GI or RECOVERY, prioritize console/virsh over SSH
        # because SSH might be unreachable due to DHCP/DNS changes after system delete
        if known_state in ('GI', 'BASEOS_SHELL', 'RECOVERY', 'DN_RECOVERY', 'DEPLOYING', 'UPGRADING'):
            kvm_config = self._get_kvm_host_config()
            if kvm_config:
                methods.append(ConnectionMethod.VIRSH_CONSOLE)
            if self.console_config:
                methods.append(ConnectionMethod.CONSOLE)
                
            sn = self._get_serial_number()
            if sn:
                methods.append(ConnectionMethod.SSH_SN)
            if hasattr(self.device, 'ip') and self.device.ip:
                methods.append(ConnectionMethod.SSH_MGMT)
            ncc_hosts = self._get_ncc_hosts()
            if ncc_hosts:
                methods.append(ConnectionMethod.SSH_NCC)
            if hasattr(self.device, 'loopback_ip') and self.device.loopback_ip:
                methods.append(ConnectionMethod.SSH_LOOPBACK)
            return methods
            
        # Default order for DNOS / unknown state
        # 1. SSH to serial number hostname (FASTEST - direct DNS resolution)
        sn = self._get_serial_number()
        if sn:
            methods.append(ConnectionMethod.SSH_SN)
        
        # 2. SSH to management IP
        if hasattr(self.device, 'ip') and self.device.ip:
            methods.append(ConnectionMethod.SSH_MGMT)
        
        # 2.5. SSH to KVM NCC hostname (only for clusters with ncc_type=kvm, DNOS mode)
        ncc_hosts = self._get_ncc_hosts()
        if ncc_hosts:
            methods.append(ConnectionMethod.SSH_NCC)
        
        # 2.7. virsh console via KVM host (GI mode for KVM NCC clusters)
        kvm_config = self._get_kvm_host_config()
        if kvm_config:
            methods.append(ConnectionMethod.VIRSH_CONSOLE)
        
        # 3. Console (if configured -- NCP-only for clusters)
        if self.console_config:
            methods.append(ConnectionMethod.CONSOLE)
        
        # 4. SSH to loopback (if known)
        if hasattr(self.device, 'loopback_ip') and self.device.loopback_ip:
            methods.append(ConnectionMethod.SSH_LOOPBACK)
        
        return methods
    
    def _get_ncc_hosts(self) -> list:
        """Get KVM NCC hostnames for cluster devices with VM-based NCCs.
        
        Only returns hosts when ncc_type is explicitly 'kvm' (auto-detected
        from show system: Model=X86 + hostname-pattern serial).
        Physical NCC clusters (ncc_type='physical' or unset) return empty.
        """
        try:
            from pathlib import Path
            import json
            op_file = Path(f"/home/dn/SCALER/db/configs/{self.device.hostname}/operational.json")
            if op_file.exists():
                with open(op_file) as f:
                    op_data = json.load(f)
                if op_data.get('ncc_type') == 'kvm':
                    return op_data.get('ncc_hosts', [])
        except Exception:
            pass
        
        try:
            from pathlib import Path
            import json
            mappings = Path("/home/dn/SCALER/db/console_mappings.json")
            if mappings.exists():
                with open(mappings) as f:
                    data = json.load(f)
                ncc_info = data.get('cluster_ncc_access', {}).get(self.device.hostname)
                if ncc_info and ncc_info.get('ncc_type') == 'kvm':
                    return ncc_info.get('ncc_hosts', [])
        except Exception:
            pass
        
        return []
    
    def _get_kvm_host_config(self) -> Optional[dict]:
        """Get KVM host config for virsh console access (GI mode on KVM NCC clusters).
        
        Returns dict with kvm_host, kvm_host_credentials, ncc_vms,
        ncc_console_credentials, dncli_credentials -- or None if not a KVM cluster.
        """
        try:
            from pathlib import Path
            import json
            op_file = Path(f"/home/dn/SCALER/db/configs/{self.device.hostname}/operational.json")
            if op_file.exists():
                with open(op_file) as f:
                    op_data = json.load(f)
                if op_data.get('ncc_type') == 'kvm' and op_data.get('kvm_host'):
                    return {
                        'kvm_host': op_data['kvm_host'],
                        'kvm_host_ip': op_data.get('kvm_host_ip'),
                        'kvm_host_credentials': op_data.get('kvm_host_credentials', {}),
                        'ncc_vms': op_data.get('ncc_vms', []),
                        'ncc_console_credentials': op_data.get('ncc_console_credentials', {}),
                        'dncli_credentials': op_data.get('dncli_credentials', {}),
                    }
        except Exception:
            pass
        
        try:
            from pathlib import Path
            import json
            mappings = Path("/home/dn/SCALER/db/console_mappings.json")
            if mappings.exists():
                with open(mappings) as f:
                    data = json.load(f)
                ncc_info = data.get('cluster_ncc_access', {}).get(self.device.hostname)
                if ncc_info and ncc_info.get('ncc_type') == 'kvm' and ncc_info.get('kvm_host'):
                    return {
                        'kvm_host': ncc_info['kvm_host'],
                        'kvm_host_ip': ncc_info.get('kvm_host_ip'),
                        'kvm_host_credentials': ncc_info.get('kvm_host_credentials', {}),
                        'ncc_vms': ncc_info.get('ncc_vms', []),
                        'ncc_console_credentials': ncc_info.get('ncc_console_credentials', {}),
                        'dncli_credentials': ncc_info.get('dncli_credentials', {}),
                    }
        except Exception:
            pass
        
        return None
    
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
        elif method == ConnectionMethod.SSH_NCC:
            return self._connect_ncc(timeout)
        elif method == ConnectionMethod.VIRSH_CONSOLE:
            return self._connect_virsh_console(timeout)
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
                    ssh=ssh,
                    channel=channel,
                    output=output,
                    host=host
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
    
    def _connect_ncc(self, timeout: int) -> ConnectionResult:
        """Connect to KVM NCC VM via SSH. Tries each known NCC hostname
        (active NCC accepts SSH, standby may reject/timeout)."""
        ncc_hosts = self._get_ncc_hosts()
        if not ncc_hosts:
            return ConnectionResult(
                success=False,
                method=ConnectionMethod.SSH_NCC,
                state=DeviceState.UNREACHABLE,
                recovery_type="",
                error="No NCC hosts configured"
            )
        
        ncc_creds = [{"username": "dnroot", "password": "dnroot"}]
        try:
            from pathlib import Path
            import json
            op_file = Path(f"/home/dn/SCALER/db/configs/{self.device.hostname}/operational.json")
            if op_file.exists():
                with open(op_file) as f:
                    op_data = json.load(f)
                stored = op_data.get('ncc_credentials')
                if stored and stored.get('username'):
                    ncc_creds = [{"username": stored['username'], "password": stored['password']}]
        except Exception:
            pass
        
        last_error = None
        for ncc_host in ncc_hosts:
            result = self._connect_ssh_multi_creds(ncc_host, timeout, ConnectionMethod.SSH_NCC)
            if result.success:
                return result
            last_error = result.error
        
        return ConnectionResult(
            success=False,
            method=ConnectionMethod.SSH_NCC,
            state=DeviceState.UNREACHABLE,
            recovery_type="",
            error=last_error or "All NCC hosts unreachable"
        )
    
    def _connect_virsh_console(self, timeout: int) -> ConnectionResult:
        """Connect to KVM NCC via virsh console on the hypervisor host.
        
        3-hop chain (all over one SSH session to KVM host):
          1. SSH to KVM host (e.g. kvm108, user=dn, pass=drive1234!)
          2. virsh console <ncc-vm> -- serial console to NCC VM
          3. Login to BaseOS (user=dn, pass=drivenets)
          4. dncli -- enters GI/DNOS CLI (SSH to localhost, dnroot/dnroot)
        
        Used when VIP/SSH is dead (GI mode on KVM NCC clusters).
        Returns the SSH client + channel positioned at the CLI prompt.
        """
        import paramiko
        import time
        import re
        
        kvm_config = self._get_kvm_host_config()
        if not kvm_config:
            return ConnectionResult(
                success=False, method=ConnectionMethod.VIRSH_CONSOLE,
                state=DeviceState.UNREACHABLE, recovery_type="",
                error="No KVM host config found"
            )
        
        kvm_host = kvm_config.get('kvm_host_ip') or kvm_config.get('kvm_host')
        kvm_creds = kvm_config.get('kvm_host_credentials', {})
        ncc_vms = kvm_config.get('ncc_vms', [])
        console_creds = kvm_config.get('ncc_console_credentials', {})
        dncli_creds = kvm_config.get('dncli_credentials', {})
        
        if not kvm_host or not kvm_creds.get('username'):
            return ConnectionResult(
                success=False, method=ConnectionMethod.VIRSH_CONSOLE,
                state=DeviceState.UNREACHABLE, recovery_type="",
                error="Incomplete KVM host config"
            )
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                kvm_host,
                username=kvm_creds['username'],
                password=kvm_creds['password'],
                timeout=timeout,
                allow_agent=False, look_for_keys=False,
            )
            channel = ssh.invoke_shell(width=200, height=50)
            channel.settimeout(30)
            time.sleep(1)
            
            def _drain(ch, wait=3):
                buf = b""
                deadline = time.time() + wait
                while time.time() < deadline:
                    if ch.recv_ready():
                        buf += ch.recv(65535)
                        deadline = time.time() + 1
                    time.sleep(0.2)
                return buf.decode('utf-8', errors='replace')
            
            def _strip_ansi(text):
                return re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', text)
            
            _drain(channel, wait=2)  # consume SSH banner
            
            # Find active NCC VM via virsh list
            channel.send("virsh list\n")
            time.sleep(3)
            virsh_output = _drain(channel, wait=3)
            
            active_ncc = None
            for vm_name in ncc_vms:
                if vm_name in virsh_output and 'running' in virsh_output.split(vm_name)[1].split('\n')[0].lower():
                    active_ncc = vm_name
                    break
            
            if not active_ncc:
                for line in virsh_output.split('\n'):
                    if 'running' in line.lower():
                        for vm_name in ncc_vms:
                            if vm_name in line:
                                active_ncc = vm_name
                                break
                    if active_ncc:
                        break
            
            if not active_ncc:
                ssh.close()
                return ConnectionResult(
                    success=False, method=ConnectionMethod.VIRSH_CONSOLE,
                    state=DeviceState.UNREACHABLE, recovery_type="",
                    error=f"No running NCC VM found on {kvm_host}"
                )
            
            # Extract NCC ID from VM name (e.g., "kvm108-cl408d-ncc1" -> 1)
            detected_ncc_id = 0
            ncc_id_match = re.search(r'ncc(\d+)', active_ncc)
            if ncc_id_match:
                detected_ncc_id = int(ncc_id_match.group(1))
            
            # Attach virsh console. Try without --force first (preserves
            # persisted GI session), fall back to --force if busy.
            channel.send(f"virsh console {active_ncc}\n")
            time.sleep(5)
            attach_out = _drain(channel, wait=3)
            if 'Active console session' in attach_out:
                channel.send(f"virsh console --force {active_ncc}\n")
                time.sleep(5)
                _drain(channel, wait=3)
            
            # Wake console: send Enters patiently. The GI CLI session
            # persists after the first dncli, so check for GI# FIRST.
            # Priority: GI/DNOS prompt > shell prompt > login prompt.
            already_in_shell = False
            already_in_cli = False
            all_console = ""
            
            for attempt in range(15):
                channel.send(b"\r")
                time.sleep(2)
                chunk = _drain(channel, wait=2)
                all_console += chunk
                stripped = _strip_ansi(chunk)
                
                if 'GI' in stripped or re.search(r'GI\([^)]*\)[#>]', stripped):
                    already_in_cli = True
                    break
                if re.search(r'[A-Z][A-Za-z0-9_-]+[#>]\s*$', stripped, re.MULTILINE):
                    already_in_cli = True
                    break
                if re.search(r'(dn|root)@[a-zA-Z0-9_-]+.*\$', stripped):
                    already_in_shell = True
                    break
                if 'login:' in stripped.lower():
                    break
            
            # Also check accumulated text for any state we might have
            # seen across multiple chunks
            if not already_in_shell and not already_in_cli:
                all_stripped = _strip_ansi(all_console)
                if 'GI' in all_stripped:
                    already_in_cli = True
                elif re.search(r'(dn|root)@[a-zA-Z0-9_-]+.*\$', all_stripped):
                    already_in_shell = True
            
            if not already_in_shell and not already_in_cli:
                if 'login:' in all_console.lower():
                    user = console_creds.get('username', 'dn')
                    pwd = console_creds.get('password', 'drivenets')
                    channel.send(f"{user}\r".encode())
                    time.sleep(3)
                    pw_out = _drain(channel, wait=3)
                    
                    if 'assword' in pw_out.lower():
                        channel.send(f"{pwd}\r".encode())
                        time.sleep(5)
                        shell_out = _drain(channel, wait=5)
                        
                        if 'incorrect' in shell_out.lower():
                            ssh.close()
                            return ConnectionResult(
                                success=False, method=ConnectionMethod.VIRSH_CONSOLE,
                                state=DeviceState.UNREACHABLE, recovery_type="",
                                error=f"NCC console login failed on {active_ncc}"
                            )
                        already_in_shell = True
            
            # BaseOS shell -> dncli -> GI/DNOS CLI
            if already_in_shell and not already_in_cli:
                channel.send(b"dncli\r")
                time.sleep(10)
                dncli_out = _drain(channel, wait=8)
                
                if 'assword' in dncli_out.lower():
                    dncli_pwd = dncli_creds.get('password', 'dnroot')
                    channel.send(f"{dncli_pwd}\r".encode())
                    
                    # GI prompt is slow to appear after dncli login.
                    # Wait generously, then send Enters to pop it.
                    time.sleep(15)
                    cli_out = _drain(channel, wait=5)
                    
                    for _ in range(5):
                        channel.send(b"\r")
                        time.sleep(3)
                        extra = _drain(channel, wait=2)
                        cli_out += extra
                        if 'GI' in extra or re.search(r'[A-Z][A-Za-z0-9_-]+[#>]', _strip_ansi(extra)):
                            break
                    
                    dncli_out += cli_out
                
                already_in_cli = 'GI' in dncli_out or bool(
                    re.search(r'[A-Z][A-Za-z0-9_-]+[#>]', _strip_ansi(dncli_out)))
            
            if already_in_cli:
                channel.send(b"\r")
                time.sleep(3)
                final_out = _drain(channel, wait=3)
                final_stripped = _strip_ansi(final_out)
                
                state = DeviceState.UNKNOWN
                if 'GI' in final_stripped:
                    state = DeviceState.GI
                elif re.search(r'[A-Z][A-Za-z0-9_-]+[#>]', final_stripped):
                    state = DeviceState.DNOS
                
                return ConnectionResult(
                    success=True,
                    method=ConnectionMethod.VIRSH_CONSOLE,
                    state=state,
                    recovery_type="GI" if state == DeviceState.GI else "",
                    ssh=ssh,
                    channel=channel,
                    output=final_out,
                    host=kvm_host,
                    active_ncc_vm=active_ncc,
                    ncc_id=detected_ncc_id,
                )
            
            ssh.close()
            return ConnectionResult(
                success=False, method=ConnectionMethod.VIRSH_CONSOLE,
                state=DeviceState.UNREACHABLE, recovery_type="",
                error=f"Failed to reach CLI via dncli on {active_ncc}"
            )
        
        except Exception as e:
            return ConnectionResult(
                success=False, method=ConnectionMethod.VIRSH_CONSOLE,
                state=DeviceState.UNREACHABLE, recovery_type="",
                error=f"virsh console to {kvm_host}: {str(e)[:60]}"
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
            
            # CRITICAL: Kill any runaway processes from previous sessions.
            # A previous run may have sent 'yes' (a Linux command that prints 'y' forever)
            # which jams the console with yyy... making state detection impossible.
            channel.send("\x03")  # Ctrl+C
            time.sleep(1)
            # Drain all the garbage output
            while channel.recv_ready():
                channel.recv(65535)
            
            # Send clean newlines to get a fresh prompt
            channel.send("\r\n")
            time.sleep(2)
            output = ""
            while channel.recv_ready():
                output += channel.recv(8192).decode("utf-8", errors="replace")
                time.sleep(0.3)
            
            # If still empty, try one more time
            if not output.strip():
                channel.send("\r\n")
                time.sleep(3)
                while channel.recv_ready():
                    output += channel.recv(8192).decode("utf-8", errors="replace")
                    time.sleep(0.3)
            
            # Extract serial number from login prompt (e.g. "WKY1BC7400002B2 login:")
            import re
            serial_from_prompt = None
            sn_match = re.search(r'([A-Z0-9]{10,}) login:', output)
            if sn_match:
                serial_from_prompt = sn_match.group(1)
                port_num = self.console_config.get('port', 0)
                hostname = getattr(self.device, 'hostname', '') or ''
                try:
                    save_console_discovery(port_num, hostname, serial_from_prompt)
                except Exception:
                    pass
            
            # Try to login -- use per-device saved creds first, then standard rotation
            creds_to_try = self.console_config.get('device_credentials', CREDENTIAL_SETS)
            lower = output.lower()
            working_cred = None
            if "login" in lower or "username" in lower:
                logged_in = False
                for cred in creds_to_try:
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
                            working_cred = cred
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
            
            # Transition from BASEOS_SHELL to GI
            if state == DeviceState.BASEOS_SHELL:
                # First send Ctrl+C to break out of any stuck commands (like 'yes')
                channel.send("\x03")
                time.sleep(1)
                while channel.recv_ready():
                    channel.recv(8192)
                
                channel.send("dncli\r\n")
                time.sleep(3)
                
                # Check for password prompt
                dncli_out = ""
                while channel.recv_ready():
                    dncli_out += channel.recv(8192).decode("utf-8", errors="replace")
                
                if 'assword' in dncli_out.lower():
                    channel.send("dnroot\r\n")
                    time.sleep(10)
                
                # Get clean prompt
                for _ in range(3):
                    channel.send("\r\n")
                    time.sleep(2)
                    while channel.recv_ready():
                        channel.recv(8192)
                
                # Re-detect state
                channel.send("\r\n")
                time.sleep(2)
                final_out = channel.recv(8192).decode("utf-8", errors="replace")
                state, recovery_type = self._detect_state_from_output(final_out)
            
            # Save working credential + device state for next time
            if working_cred:
                port_num = self.console_config.get('port', 0)
                try:
                    _save_working_credential(
                        port_num, working_cred, state.value if state else ''
                    )
                except Exception:
                    pass
            
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
                                    ssh=new_ssh,
                                    channel=new_channel,
                                    output=new_output,
                                    host=mgmt_ip
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
                ssh=ssh,
                channel=channel,
                output=output,
                host=self.console_config.get('host', '')
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
        
        # 4. DN Recovery mode - check prompt pattern and keywords
        if ("(recovery)" in lower or "dn-recovery" in lower 
                or "dnos recovery" in lower or "recovery mode" in lower):
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


def _load_console_mappings() -> Dict:
    """Load console mappings from persistent DB file."""
    from pathlib import Path
    import json
    
    mappings_path = Path("/home/dn/SCALER/db/console_mappings.json")
    if not mappings_path.exists():
        return {}
    try:
        with open(mappings_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_working_credential(port: int, cred: Dict, device_state: str, console_server_name: str = None) -> bool:
    """Save which credential worked for a console port device.
    
    Next connection will try this credential first, skipping failed ones.
    Supports multi-server format via console_server_name.
    """
    from datetime import datetime
    
    data = _load_console_mappings()
    if not data:
        return False
    
    port_str = str(port)
    cred_entry = {
        'username': cred['username'],
        'password': cred['password'],
        'device_state': device_state,
        'last_success': datetime.now().isoformat()
    }
    
    # New multi-server format
    if 'console_servers' in data and console_server_name:
        srv = data['console_servers'].get(console_server_name, {})
        ports = srv.get('ports', {})
        if port_str in ports:
            ports[port_str]['working_credentials'] = cred_entry
            return _save_console_mappings(data)
        return False
    
    # Legacy single-server format
    if 'ports' in data and port_str in data['ports']:
        data['ports'][port_str]['working_credentials'] = cred_entry
        return _save_console_mappings(data)
    
    return False


def _save_console_mappings(data: Dict) -> bool:
    """Save console mappings to persistent DB file."""
    from pathlib import Path
    import json
    
    mappings_path = Path("/home/dn/SCALER/db/console_mappings.json")
    try:
        mappings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(mappings_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except IOError:
        return False


def get_console_config_for_device(hostname: str) -> Optional[Dict]:
    """
    Get console server configuration for a specific device.
    
    Reads from persistent DB at db/console_mappings.json.
    Supports multi-server format (console_servers dict) and legacy single-server format.
    Matches by hostname, hostname_aliases, device_to_console lookup, or serial_number.
    
    For KVM clusters: the console server reaches the NCP (data plane), NOT the NCC
    where GI/DNOS runs. Returns None for KVM cluster devices since console is not
    a valid connection method for NCC operations.
    
    Returns console config dict with:
      host, port, user, password (for SSH to console server)
      console_server_name: key in console_servers dict
      device_credentials: list of credential dicts to try on the device itself,
        ordered with last-known-working first
    """
    data = _load_console_mappings()
    if not data:
        return None
    
    # KVM clusters: console server reaches NCP, not NCC -- skip console
    ncc_access = data.get('cluster_ncc_access', {})
    if hostname in ncc_access and ncc_access[hostname].get('ncc_type') == 'kvm':
        return None
    
    hostname_lower = hostname.lower()
    
    # New multi-server format
    if 'console_servers' in data:
        # Fast path: device_to_console lookup
        d2c = data.get('device_to_console', {})
        for dev_name, mapping in d2c.items():
            if dev_name.lower() == hostname_lower:
                srv_name = mapping.get('console_server')
                port_str = mapping.get('port')
                if srv_name and port_str and srv_name in data['console_servers']:
                    srv = data['console_servers'][srv_name]
                    port_info = srv.get('ports', {}).get(str(port_str), {})
                    return _build_console_result(srv, srv_name, port_str, port_info)
        
        # Scan all servers' ports for hostname/alias match
        for srv_name, srv in data['console_servers'].items():
            for port_str, port_info in srv.get('ports', {}).items():
                if port_str == '?':
                    port_hostname = port_info.get('hostname', '')
                    aliases = port_info.get('hostname_aliases', [])
                    all_names = [port_hostname] + aliases
                    if any(name.lower() == hostname_lower for name in all_names):
                        return _build_console_result(srv, srv_name, None, port_info)
                    continue
                port_hostname = port_info.get('hostname', '')
                aliases = port_info.get('hostname_aliases', [])
                all_names = [port_hostname] + aliases
                if any(name.lower() == hostname_lower for name in all_names):
                    return _build_console_result(srv, srv_name, port_str, port_info)
        
        return None
    
    # Legacy single-server format
    if 'ports' not in data:
        return None
    
    server = data.get('console_server', {})
    for port_str, port_info in data['ports'].items():
        port_hostname = port_info.get('hostname', '')
        aliases = port_info.get('hostname_aliases', [])
        all_names = [port_hostname] + aliases
        if any(name.lower() == hostname_lower for name in all_names):
            return _build_console_result(server, 'default', port_str, port_info)
    
    return None


def _build_console_result(server: Dict, srv_name: str, port_str: Optional[str], port_info: Dict) -> Dict:
    """Build the console config result dict from server and port info."""
    device_creds = list(CREDENTIAL_SETS)
    saved_cred = port_info.get('working_credentials')
    if saved_cred and saved_cred.get('username'):
        saved = {
            'username': saved_cred['username'],
            'password': saved_cred['password']
        }
        device_creds = [c for c in device_creds
                        if not (c['username'] == saved['username']
                                and c['password'] == saved['password'])]
        device_creds.insert(0, saved)
    
    result = {
        'host': server.get('host', server.get('ip', '')),
        'user': server.get('user', 'dn'),
        'password': server.get('password', 'drive1234'),
        'console_server_name': srv_name,
        'device_credentials': device_creds
    }
    if port_str and port_str != '?':
        result['port'] = int(port_str)
    return result


def get_console_config_by_serial(serial_number: str) -> Optional[Dict]:
    """
    Look up console config by NCC serial number.
    
    Serial numbers are permanent identifiers -- they survive hostname renames.
    Used as fallback when hostname lookup fails after a device rename.
    Supports multi-server and legacy single-server formats.
    """
    data = _load_console_mappings()
    if not data:
        return None
    
    # New multi-server format
    if 'console_servers' in data:
        # Fast path: serial_to_console lookup
        s2c = data.get('serial_to_console', {})
        if serial_number in s2c:
            mapping = s2c[serial_number]
            srv_name = mapping.get('console_server')
            port_str = mapping.get('port')
            if srv_name and srv_name in data['console_servers']:
                srv = data['console_servers'][srv_name]
                return {
                    'host': srv.get('host', srv.get('ip', '')),
                    'port': int(port_str) if port_str else None,
                    'user': srv.get('user', 'dn'),
                    'password': srv.get('password', 'drive1234'),
                    'console_server_name': srv_name,
                    'mapped_hostname': mapping.get('hostname', '')
                }
        
        # Scan all servers
        for srv_name, srv in data['console_servers'].items():
            for port_str, port_info in srv.get('ports', {}).items():
                if port_info.get('serial_number') == serial_number:
                    return {
                        'host': srv.get('host', srv.get('ip', '')),
                        'port': int(port_str) if port_str != '?' else None,
                        'user': srv.get('user', 'dn'),
                        'password': srv.get('password', 'drive1234'),
                        'console_server_name': srv_name,
                        'mapped_hostname': port_info.get('hostname', '')
                    }
        return None
    
    # Legacy single-server format
    if 'ports' not in data:
        return None
    server = data.get('console_server', {})
    for port_str, port_info in data['ports'].items():
        if port_info.get('serial_number') == serial_number:
            return {
                'host': server.get('host', 'console-b15'),
                'port': int(port_str),
                'user': server.get('user', 'dn'),
                'password': server.get('password', 'drive1234'),
                'console_server_name': 'default',
                'mapped_hostname': port_info.get('hostname', '')
            }
    return None


def update_console_hostname(old_hostname: str, new_hostname: str, serial_number: str = None) -> bool:
    """
    Update console mapping when a device is renamed.
    
    Called automatically when config fetches reveal a hostname change.
    Tracks previous hostnames for audit trail.
    Supports multi-server and legacy single-server formats.
    Also updates device_to_console and serial_to_console lookup tables.
    """
    from datetime import datetime
    
    data = _load_console_mappings()
    if not data:
        return False
    
    old_lower = old_hostname.lower()
    updated = False
    
    def _update_port_entry(port_info):
        prev = port_info.get('previous_hostnames', [])
        current = port_info.get('hostname', '')
        if current and current.lower() != new_hostname.lower() and current not in prev:
            prev.append(current)
        port_info['previous_hostnames'] = prev
        port_info['hostname'] = new_hostname
        port_info['description'] = new_hostname
        if serial_number:
            port_info['serial_number'] = serial_number
        port_info['last_verified'] = datetime.now().isoformat()
    
    # New multi-server format
    if 'console_servers' in data:
        for srv_name, srv in data['console_servers'].items():
            for port_str, port_info in srv.get('ports', {}).items():
                current = port_info.get('hostname', '')
                aliases = port_info.get('hostname_aliases', [])
                all_names = [current] + aliases
                if any(name.lower() == old_lower for name in all_names):
                    _update_port_entry(port_info)
                    updated = True
                    # Update device_to_console
                    d2c = data.setdefault('device_to_console', {})
                    if old_hostname in d2c:
                        d2c[new_hostname] = d2c.pop(old_hostname)
                    else:
                        d2c[new_hostname] = {'console_server': srv_name, 'port': port_str}
                    # Update serial_to_console
                    if serial_number:
                        s2c = data.setdefault('serial_to_console', {})
                        s2c[serial_number] = {'console_server': srv_name, 'port': port_str, 'hostname': new_hostname}
                    break
            if updated:
                break
        
        # If not found by hostname, try serial across all servers
        if not updated and serial_number:
            for srv_name, srv in data['console_servers'].items():
                for port_str, port_info in srv.get('ports', {}).items():
                    if port_info.get('serial_number') == serial_number:
                        _update_port_entry(port_info)
                        updated = True
                        d2c = data.setdefault('device_to_console', {})
                        d2c[new_hostname] = {'console_server': srv_name, 'port': port_str}
                        s2c = data.setdefault('serial_to_console', {})
                        s2c[serial_number] = {'console_server': srv_name, 'port': port_str, 'hostname': new_hostname}
                        break
                if updated:
                    break
    
    # Legacy single-server format
    elif 'ports' in data:
        for port_str, port_info in data['ports'].items():
            current = port_info.get('hostname', '')
            aliases = port_info.get('hostname_aliases', [])
            all_names = [current] + aliases
            if any(name.lower() == old_lower for name in all_names):
                _update_port_entry(port_info)
                updated = True
                break
        
        if not updated and serial_number:
            for port_str, port_info in data['ports'].items():
                if port_info.get('serial_number') == serial_number:
                    _update_port_entry(port_info)
                    updated = True
                    break
    
    if updated:
        _save_console_mappings(data)
    return updated


def save_console_discovery(port: int, hostname: str, serial_number: str = None,
                           console_server_name: str = None) -> bool:
    """
    Save a newly discovered console port mapping.
    
    Called when a device is identified on a console port for the first time,
    or when serial number is discovered via console login prompt.
    Supports multi-server format via console_server_name.
    
    Args:
        port: Console server port number (1-16)
        hostname: Device hostname
        serial_number: NCC serial from login prompt (e.g. WKY1BC7400002B2)
        console_server_name: Which console server (e.g. 'console-b15')
    """
    from datetime import datetime
    
    data = _load_console_mappings()
    port_str = str(port)
    
    # New multi-server format
    if 'console_servers' in data and console_server_name:
        srv = data['console_servers'].get(console_server_name)
        if not srv:
            return False
        ports = srv.setdefault('ports', {})
        
        # Remove placeholder '?' entries for this hostname if replacing with a real port
        for k in list(ports.keys()):
            if k == '?' and ports[k].get('hostname', '').lower() == hostname.lower():
                del ports[k]
        
        if port_str not in ports:
            ports[port_str] = {}
        entry = ports[port_str]
        old_hostname = entry.get('hostname', '')
        if old_hostname and old_hostname.lower() != hostname.lower():
            prev = entry.get('previous_hostnames', [])
            if old_hostname not in prev:
                prev.append(old_hostname)
            entry['previous_hostnames'] = prev
        entry['hostname'] = hostname
        entry['description'] = hostname
        if serial_number:
            entry['serial_number'] = serial_number
        entry['last_verified'] = datetime.now().isoformat()
        
        # Update lookup tables
        d2c = data.setdefault('device_to_console', {})
        d2c[hostname] = {'console_server': console_server_name, 'port': port_str}
        if serial_number:
            s2c = data.setdefault('serial_to_console', {})
            s2c[serial_number] = {'console_server': console_server_name, 'port': port_str, 'hostname': hostname}
        
        return _save_console_mappings(data)
    
    # Legacy single-server format
    if not data:
        data = {
            'console_server': {
                'host': 'console-b15',
                'user': 'dn',
                'password': 'drive1234',
                'model': 'ATEN SN9116CO',
                'total_ports': 16
            },
            'ports': {}
        }
    
    if 'ports' not in data:
        data['ports'] = {}
    
    if port_str not in data['ports']:
        data['ports'][port_str] = {}
    
    entry = data['ports'][port_str]
    old_hostname = entry.get('hostname', '')
    if old_hostname and old_hostname.lower() != hostname.lower():
        prev = entry.get('previous_hostnames', [])
        if old_hostname not in prev:
            prev.append(old_hostname)
        entry['previous_hostnames'] = prev
    entry['hostname'] = hostname
    entry['description'] = hostname
    if serial_number:
        entry['serial_number'] = serial_number
    entry['last_verified'] = datetime.now().isoformat()
    
    return _save_console_mappings(data)


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


def connect_for_upgrade(hostname: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Unified connection for upgrade flows. Tries all available paths
    (SSH, console, virsh) and returns ssh+channel in safe_connect_and_verify format.
    
    Use this instead of safe_connect_and_verify for upgrade flows so that
    GI-mode devices (console, virsh) and KVM clusters are reachable.
    
    Args:
        hostname: Device hostname (e.g., "PE-1", "RR-SA-2", "YOR_CL_PE-4")
        timeout: Connection timeout per method
        
    Returns:
        dict compatible with safe_connect_and_verify:
            connected, ssh, channel, ip, method, verified, actual_hostname,
            abort_reason, prompt_output, db_changes, device_state
    """
    from pathlib import Path
    import json
    
    result = {
        'connected': False, 'ssh': None, 'channel': None,
        'ip': None, 'method': None, 'verified': False,
        'actual_hostname': hostname, 'abort_reason': None,
        'prompt_output': '', 'db_changes': {}, 'device_state': None,
    }
    
    op_path = Path(f"/home/dn/SCALER/db/configs/{hostname}/operational.json")
    serial_number = None
    mgmt_ip = None
    device_ip = None
    
    if op_path.exists():
        try:
            with open(op_path) as f:
                op_data = json.load(f)
                sn = op_data.get('serial_number')
                if sn and sn != 'N/A':
                    serial_number = sn
                ip = op_data.get('mgmt_ip') or op_data.get('ssh_host')
                if ip and ip != 'N/A':
                    mgmt_ip = ip.split('/')[0] if '/' in str(ip) else ip
        except Exception:
            pass
    
    dev_path = Path("/home/dn/SCALER/db/devices.json")
    if dev_path.exists():
        try:
            with open(dev_path) as f:
                data = json.load(f)
                for d in data.get('devices', []):
                    if d.get('hostname') == hostname:
                        device_ip = (d.get('ip') or '').split('/')[0].strip()
                        break
        except Exception:
            pass
    
    class TempDevice:
        pass
    device = TempDevice()
    device.hostname = hostname
    device.ip = mgmt_ip or device_ip
    device.serial_number = serial_number
    device.username = "dnroot"
    device.password = "dnroot"
    
    console_config = get_console_config_for_device(hostname)
    connector = DeviceConnector(device, console_config)
    conn_result = connector.connect_and_detect(timeout=timeout)
    
    if not conn_result.success:
        result['abort_reason'] = conn_result.error or f"No reachable path for {hostname}"
        return result
    
    method_map = {
        ConnectionMethod.SSH_SN: "SSH->SN",
        ConnectionMethod.SSH_MGMT: "SSH->MGMT",
        ConnectionMethod.SSH_NCC: "SSH->NCC",
        ConnectionMethod.VIRSH_CONSOLE: "virsh->NCC",
        ConnectionMethod.CONSOLE: "Console",
        ConnectionMethod.SSH_LOOPBACK: "SSH->Loopback"
    }
    
    result['connected'] = True
    result['ssh'] = conn_result.ssh
    result['channel'] = conn_result.channel
    result['ip'] = conn_result.host or mgmt_ip or device_ip or hostname
    result['method'] = method_map.get(conn_result.method, str(conn_result.method))
    result['verified'] = True
    result['prompt_output'] = conn_result.output or ''
    result['device_state'] = conn_result.state.value if conn_result.state else None
    result['ncc_id'] = conn_result.ncc_id
    result['active_ncc_vm'] = conn_result.active_ncc_vm or ''
    
    return result


def refresh_device_state(hostname: str, update_operational: bool = True) -> Tuple[DeviceState, str, Optional[str]]:
    """
    Refresh device state and optionally update operational.json.
    
    This is the main entry point for refreshing device state from anywhere.
    
    Connection priority:
    1. SSH to serial number hostname (fastest, direct DNS)
    2. SSH to management IP
    2.5. SSH to KVM NCC hostname (DNOS mode, ncc_type=kvm)
    2.7. virsh console via KVM host (GI mode, ncc_type=kvm)
    3. Console server (if configured -- NCP-only for clusters)
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
            
            # Capture previous state BEFORE overwriting (used for DNOS transition IP discovery)
            _prev_device_state = op_data.get('device_state', '')
            
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
                ConnectionMethod.SSH_NCC: "SSH→NCC",
                ConnectionMethod.VIRSH_CONSOLE: "virsh→NCC",
                ConnectionMethod.CONSOLE: "Console",
                ConnectionMethod.SSH_LOOPBACK: "SSH→Loopback"
            }
            op_data['connection_method'] = method_map.get(result.method, str(result.method))
            
            # Store the actual SSH host that worked
            if result.method == ConnectionMethod.SSH_SN and serial_number:
                op_data['ssh_host'] = serial_number
            elif result.method == ConnectionMethod.SSH_MGMT and mgmt_ip:
                op_data['ssh_host'] = mgmt_ip.split('/')[0] if '/' in str(mgmt_ip) else mgmt_ip
            elif result.method == ConnectionMethod.SSH_NCC:
                ncc_hosts = connector._get_ncc_hosts()
                op_data['ssh_host'] = ncc_hosts[0] if ncc_hosts else hostname
            elif result.method == ConnectionMethod.VIRSH_CONSOLE:
                kvm_cfg = connector._get_kvm_host_config()
                op_data['ssh_host'] = kvm_cfg.get('kvm_host', hostname) if kvm_cfg else hostname
            elif result.method == ConnectionMethod.CONSOLE:
                op_data['ssh_host'] = 'console'
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
            
            # When DNOS is detected and the device was previously in a
            # non-DNOS state, fetch the new management IP via the open
            # channel so subsequent SSH operations use the correct IP.
            if (result.state == DeviceState.DNOS
                    and _prev_device_state in ('GI', 'DEPLOYING', 'UPGRADING', 'BASEOS_SHELL', 'DN_RECOVERY', 'RECOVERY')
                    and result.channel is not None):
                try:
                    import re as _re
                    import time as _time
                    result.channel.send(b"show interfaces management | no-more\r")
                    _time.sleep(5)
                    _mgmt_buf = b""
                    _deadline = _time.time() + 8
                    while _time.time() < _deadline:
                        if result.channel.recv_ready():
                            _mgmt_buf += result.channel.recv(65535)
                            _deadline = _time.time() + 2
                        _time.sleep(0.3)
                    _mgmt_text = _mgmt_buf.decode('utf-8', errors='replace')
                    _mgmt_match = _re.search(
                        r'\|\s*mgmt0\s+\|[^|]*\|\s*up\s+\|\s*([\d.]+)(?:/\d+)?',
                        _mgmt_text)
                    _ncc_match = _re.search(
                        r'\|\s*mgmt-ncc-\d+\s+\|[^|]*\|\s*up\s+\|\s*([\d.]+)(?:/\d+)?',
                        _mgmt_text)
                    _new_ip = _mgmt_match.group(1) if _mgmt_match else (
                        _ncc_match.group(1) if _ncc_match else None)
                    if _ncc_match:
                        op_data['ncc_mgmt_ip'] = _ncc_match.group(1)
                    if _new_ip:
                        _old_ip = op_data.get('mgmt_ip', '')
                        if _new_ip != _old_ip:
                            op_data['mgmt_ip'] = _new_ip
                            op_data['upgrade_in_progress'] = False
                            op_data['install_status'] = 'completed'
                            try:
                                _dev_db = Path("/home/dn/SCALER/db/devices.json")
                                if _dev_db.exists():
                                    with open(_dev_db) as _df:
                                        _dj = json.load(_df)
                                    for _dd in _dj.get('devices', []):
                                        if _dd.get('hostname') == hostname:
                                            _dd['ip'] = _new_ip
                                            _dd['last_sync'] = datetime.now().isoformat()
                                    with open(_dev_db, 'w') as _df:
                                        json.dump(_dj, _df, indent=2)
                            except Exception:
                                pass
                    # Also update NCC info from the connection
                    if result.ncc_id is not None:
                        op_data['deploy_ncc_id'] = str(result.ncc_id)
                    if result.active_ncc_vm:
                        op_data['active_ncc_vm'] = result.active_ncc_vm
                except Exception:
                    pass
            
            # When DNOS detected via virsh/console, resolve connection_method
            # to SSH so subsequent operations use the right path.
            if (result.state == DeviceState.DNOS
                    and result.method in (ConnectionMethod.VIRSH_CONSOLE, ConnectionMethod.CONSOLE)):
                _resolved_ip = op_data.get('mgmt_ip', '')
                _resolved_sn = op_data.get('serial_number', '')
                if _resolved_sn and _resolved_sn not in ('N/A', ''):
                    op_data['connection_method'] = f"SSH->SN (dnroot)"
                    op_data['ssh_host'] = _resolved_sn
                elif _resolved_ip and _resolved_ip not in ('N/A', ''):
                    _clean_ip = _resolved_ip.split('/')[0] if '/' in str(_resolved_ip) else _resolved_ip
                    op_data['connection_method'] = f"SSH->MGMT ({_clean_ip})"
                    op_data['ssh_host'] = _clean_ip
                else:
                    _ncc_hosts = op_data.get('ncc_hosts', [])
                    if _ncc_hosts:
                        op_data['connection_method'] = f"SSH->NCC ({_ncc_hosts[0]})"
                        op_data['ssh_host'] = _ncc_hosts[0]
            
            op_path.parent.mkdir(parents=True, exist_ok=True)
            with open(op_path, 'w') as f:
                json.dump(op_data, f, indent=4)
        except Exception:
            pass  # Don't fail on write errors
    
    # Close the connection
    try:
        if result.ssh:
            result.ssh.close()
    except Exception:
        pass
    
    return result.state, result.recovery_type, result.error
