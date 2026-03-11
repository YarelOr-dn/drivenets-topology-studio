#!/usr/bin/env python3
"""
Device Manager - Device connectivity and command execution

This module handles SSH connections to network devices and command execution,
reusing patterns from flowspec_vpn_monitor.py
"""

import json
import base64
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)

# Try to import pexpect
try:
    import pexpect
    PEXPECT_AVAILABLE = True
except ImportError:
    PEXPECT_AVAILABLE = False
    logger.warning("pexpect not available. Install with: pip install pexpect")


class SSHConnection:
    """SSH connection to a network device"""
    
    def __init__(self, hostname: str, ip: str, username: str = "dnroot", password: str = "dnroot", timeout: int = 30):
        self.hostname = hostname
        self.ip = ip
        self.username = username
        self.password = password
        self.timeout = timeout
        self.child = None
        self.connected = False
    
    def connect(self) -> bool:
        """Establish SSH connection"""
        if not PEXPECT_AVAILABLE:
            logger.error("pexpect not available. Cannot establish SSH connection.")
            return False
        
        try:
            ssh_cmd = f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {self.username}@{self.ip}"
            self.child = pexpect.spawn(ssh_cmd, timeout=self.timeout)
            
            i = self.child.expect(['password:', 'Password:', pexpect.TIMEOUT, pexpect.EOF], timeout=10)
            if i == 0 or i == 1:
                self.child.sendline(self.password)
                self.child.expect(['#', '$', '>', pexpect.TIMEOUT], timeout=10)
                self.connected = True
                logger.info(f"Connected to {self.hostname} ({self.ip})")
                return True
            else:
                logger.error(f"SSH connection timeout or EOF for {self.hostname}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to {self.hostname}: {e}")
            return False
    
    def disconnect(self):
        """Close SSH connection"""
        if self.child:
            try:
                self.child.close(force=True)
            except:
                pass
            self.child = None
        self.connected = False
    
    def run_command(self, command: str, timeout: Optional[int] = None) -> Tuple[bool, str]:
        """
        Run a command on the device
        
        Args:
            command: Command to execute
            timeout: Command timeout (uses self.timeout if None)
        
        Returns:
            Tuple of (success, output)
        """
        if not self.connected or not self.child:
            logger.error(f"Not connected to {self.hostname}")
            return False, "Not connected"
        
        if timeout is None:
            timeout = self.timeout
        
        try:
            # Send command
            self.child.sendline(command)
            
            # Wait for prompt
            i = self.child.expect(['#', '$', '>', pexpect.TIMEOUT], timeout=timeout)
            
            if i == 3:  # TIMEOUT
                logger.warning(f"Command timeout: {command}")
                return False, "Command timeout"
            
            # Get output (before prompt)
            output = self.child.before.decode('utf-8', errors='ignore')
            
            # Clean up output
            output = output.replace(command, "").strip()
            
            return True, output
        except Exception as e:
            logger.error(f"Error running command '{command}' on {self.hostname}: {e}")
            return False, str(e)
    
    def run_cli_command(self, command: str, timeout: Optional[int] = None) -> Tuple[bool, str]:
        """
        Run a DNOS CLI command (show commands, etc.)
        
        Args:
            command: CLI command to execute
            timeout: Command timeout
        
        Returns:
            Tuple of (success, output)
        """
        return self.run_command(command, timeout)
    
    def run_config_command(self, config_lines: List[str], commit: bool = True) -> Tuple[bool, str]:
        """
        Run configuration commands
        
        Args:
            config_lines: List of configuration lines
            commit: Whether to commit after configuration
        
        Returns:
            Tuple of (success, output)
        """
        if not self.connected:
            return False, "Not connected"
        
        try:
            # Enter configure mode
            self.child.sendline("configure")
            self.child.expect(['#', '>'], timeout=5)
            
            output_lines = []
            
            # Send each config line
            for line in config_lines:
                self.child.sendline(line)
                time.sleep(0.2)  # Small delay between commands
                i = self.child.expect(['#', '>', 'Error', 'error'], timeout=5)
                if i == 2 or i == 3:
                    error_output = self.child.before.decode('utf-8', errors='ignore')
                    output_lines.append(f"Error in '{line}': {error_output}")
                    # Exit configure mode
                    self.child.sendline("exit")
                    self.child.expect(['#', '>'], timeout=5)
                    return False, "\n".join(output_lines)
            
            # Commit if requested
            if commit:
                self.child.sendline("commit")
                self.child.expect(['#', '>'], timeout=30)
                commit_output = self.child.before.decode('utf-8', errors='ignore')
                output_lines.append(commit_output)
            
            # Exit configure mode
            self.child.sendline("exit")
            self.child.expect(['#', '>'], timeout=5)
            
            return True, "\n".join(output_lines)
        except Exception as e:
            logger.error(f"Error running config commands on {self.hostname}: {e}")
            return False, str(e)


class DeviceManager:
    """Manages multiple device connections"""
    
    def __init__(self, devices_file: Optional[Path] = None):
        self.devices: Dict[str, Dict] = {}
        self.connections: Dict[str, SSHConnection] = {}
        self.devices_file = devices_file or Path("/home/dn/SCALER/db/devices.json")
    
    def load_devices(self) -> List[Dict]:
        """Load devices from devices.json file"""
        if not self.devices_file.exists():
            logger.warning(f"Devices file not found: {self.devices_file}")
            return []
        
        try:
            with open(self.devices_file) as f:
                data = json.load(f)
            
            # Handle both formats: {"devices": [...]} or [...]
            if isinstance(data, dict) and "devices" in data:
                raw_devices = data["devices"]
            elif isinstance(data, list):
                raw_devices = data
            else:
                raw_devices = [data]
            
            # Decode base64 passwords and normalize
            devices = []
            for dev in raw_devices:
                device = dict(dev)
                
                # Decode base64 password if needed
                if device.get("password"):
                    try:
                        decoded = base64.b64decode(device["password"]).decode('utf-8')
                        device["password"] = decoded
                    except:
                        pass  # Keep original if not base64
                
                # Normalize IP field
                if not device.get("ip") and device.get("management_ip"):
                    device["ip"] = device["management_ip"]
                
                devices.append(device)
                self.devices[device.get("hostname", "unknown")] = device
            
            logger.info(f"Loaded {len(devices)} devices from {self.devices_file}")
            return devices
        except Exception as e:
            logger.error(f"Error loading devices: {e}")
            return []
    
    def get_device(self, hostname: str) -> Optional[Dict]:
        """Get device info by hostname"""
        if not self.devices:
            self.load_devices()
        return self.devices.get(hostname)
    
    def connect_device(self, hostname: str) -> Optional[SSHConnection]:
        """Connect to a device by hostname"""
        device = self.get_device(hostname)
        if not device:
            logger.error(f"Device not found: {hostname}")
            return None
        
        # Check if already connected
        if hostname in self.connections:
            conn = self.connections[hostname]
            if conn.connected:
                return conn
        
        # Create new connection
        conn = SSHConnection(
            hostname=device.get("hostname", hostname),
            ip=device.get("ip", device.get("management_ip", "")),
            username=device.get("username", "dnroot"),
            password=device.get("password", "dnroot"),
        )
        
        if conn.connect():
            self.connections[hostname] = conn
            return conn
        else:
            return None
    
    def disconnect_device(self, hostname: str):
        """Disconnect from a device"""
        if hostname in self.connections:
            self.connections[hostname].disconnect()
            del self.connections[hostname]
    
    def disconnect_all(self):
        """Disconnect from all devices"""
        for hostname in list(self.connections.keys()):
            self.disconnect_device(hostname)
    
    def get_connection(self, hostname: str) -> Optional[SSHConnection]:
        """Get existing connection or connect to device"""
        if hostname in self.connections and self.connections[hostname].connected:
            return self.connections[hostname]
        return self.connect_device(hostname)
    
    def find_device_by_role(self, role: str) -> Optional[Dict]:
        """Find device by role (DUT, PE2, RR, etc.)"""
        if not self.devices:
            self.load_devices()
        
        # Try to match by hostname or description
        role_lower = role.lower()
        for device in self.devices.values():
            hostname = (device.get("hostname") or "").lower()
            description = (device.get("description") or "").lower()
            if role_lower in hostname or role_lower in description:
                return device
        
        return None


# Topology-specific device roles (from SW-234160)
TOPOLOGY_DEVICES = {
    "DUT": {"hostname": "PE1", "serial": "WK31D7VV00023", "type": "SA-36CD-S"},
    "PE2": {"hostname": "PE2", "serial": "WKY1BC7400002B2", "type": "SA-36CD-S"},
    "RR": {"hostname": "CL-408D", "type": "Cluster 2xNCP-40C"},
    "TrafficGen": {"hostname": "Spirent01", "port": "6:13"},
}


def get_topology_device(role: str, device_manager: DeviceManager) -> Optional[SSHConnection]:
    """Get device connection by topology role"""
    device_info = TOPOLOGY_DEVICES.get(role)
    if not device_info:
        logger.error(f"Unknown topology role: {role}")
        return None
    
    hostname = device_info["hostname"]
    return device_manager.get_connection(hostname)
