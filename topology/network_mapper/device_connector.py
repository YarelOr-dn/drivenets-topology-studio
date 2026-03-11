"""
Device Connector Module

Handles SSH connections to PE and DNAAS devices with command execution.
"""

import paramiko
import time
import re
from typing import Optional


class DeviceConnector:
    """SSH connection handler for PE and DNAAS devices"""
    
    # Default credentials
    PE_CREDENTIALS = ("dnroot", "dnroot")
    DNAAS_CREDENTIALS = ("sisaev", "Drive1234!")
    
    def __init__(self, hostname: str, username: str, password: str, timeout: int = 30):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.timeout = timeout
        self.client: Optional[paramiko.SSHClient] = None
        self.shell: Optional[paramiko.Channel] = None
        self.device_hostname: Optional[str] = None
        
    @classmethod
    def connect_pe(cls, hostname: str, user: str = None, password: str = None) -> "DeviceConnector":
        """Connect to a PE device using default or provided credentials"""
        user = user or cls.PE_CREDENTIALS[0]
        password = password or cls.PE_CREDENTIALS[1]
        connector = cls(hostname, user, password)
        connector._connect()
        return connector
    
    @classmethod
    def connect_dnaas(cls, hostname: str, user: str = None, password: str = None) -> "DeviceConnector":
        """Connect to a DNAAS device using default or provided credentials"""
        user = user or cls.DNAAS_CREDENTIALS[0]
        password = password or cls.DNAAS_CREDENTIALS[1]
        connector = cls(hostname, user, password)
        connector._connect()
        return connector
    
    def _connect(self) -> None:
        """Establish SSH connection and interactive shell"""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            self.client.connect(
                self.hostname,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
                allow_agent=False,
                look_for_keys=False
            )
            
            # Open interactive shell
            self.shell = self.client.invoke_shell(width=200, height=50)
            time.sleep(2)
            
            # Clear initial output and disable pagination
            self._read_until_prompt()
            self.execute_command("terminal length 0", timeout=5)
            
            # Get device hostname
            self.device_hostname = self._get_device_hostname()
            
        except Exception as e:
            self.close()
            raise ConnectionError(f"Failed to connect to {self.hostname}: {e}")
    
    def _read_until_prompt(self, timeout: int = 10) -> str:
        """Read shell output until prompt is detected"""
        output = ""
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            if self.shell.recv_ready():
                chunk = self.shell.recv(65535).decode('utf-8', errors='ignore')
                output += chunk
                
                # Check for common prompts
                if re.search(r'[#>]\s*$', output.strip()):
                    break
            else:
                time.sleep(0.1)
        
        return output
    
    def _get_device_hostname(self) -> str:
        """Extract device hostname from prompt"""
        output = self.execute_command("", timeout=2)
        # Parse hostname from prompt like "PE-1#" or "DNAAS-LEAF-A01#"
        match = re.search(r'([A-Za-z0-9_-]+)[#>]\s*$', output.strip())
        if match:
            return match.group(1)
        return "unknown"
    
    def execute_command(self, command: str, timeout: int = 30) -> str:
        """Execute a CLI command and return output"""
        if not self.shell:
            raise RuntimeError("Not connected to device")
        
        # Clear any pending output
        while self.shell.recv_ready():
            self.shell.recv(65535)
        
        # Send command
        self.shell.send(command + "\n")
        time.sleep(0.5)
        
        # Read output
        output = ""
        end_time = time.time() + timeout
        last_recv_time = time.time()
        
        while time.time() < end_time:
            if self.shell.recv_ready():
                chunk = self.shell.recv(65535).decode('utf-8', errors='ignore')
                output += chunk
                last_recv_time = time.time()
                
                # Check if we've received the full output (prompt returned)
                # DNOS prompts look like: YOR_PE-2# or [FYOR_PE-2(date)# 
                if re.search(r'[A-Za-z0-9_-]+[#>]\s*$', output.strip()):
                    # Give a bit more time for any trailing data
                    time.sleep(0.2)
                    if self.shell.recv_ready():
                        output += self.shell.recv(65535).decode('utf-8', errors='ignore')
                    break
            else:
                # If no data for 3 seconds after last receive and we have data, check again
                if output and (time.time() - last_recv_time) > 3:
                    if re.search(r'[A-Za-z0-9_-]+[#>]\s*$', output.strip()):
                        break
                time.sleep(0.1)
        
        # Clean output - remove ANSI codes
        output = re.sub(r'\x1b\[[0-9;]*m', '', output)
        
        # Clean output - remove command echo and prompt
        lines = output.split('\n')
        if lines and command in lines[0]:
            lines = lines[1:]
        if lines and re.search(r'[A-Za-z0-9_-]+[#>]\s*$', lines[-1]):
            lines = lines[:-1]
        
        return '\n'.join(lines)
    
    def execute_config(self, config_lines: list) -> bool:
        """Execute configuration commands and commit"""
        if not config_lines:
            return True
        
        try:
            # Enter config mode if not already there
            output = self.execute_command("")
            if "#" in output and "(cfg" not in output:
                self.execute_command("configure")
                time.sleep(0.5)
            
            # Execute each config line
            for line in config_lines:
                if line.strip():
                    self.execute_command(line.strip(), timeout=10)
            
            # Commit
            commit_output = self.execute_command("commit", timeout=60)
            
            # Check for errors
            if "ERROR" in commit_output or "failed" in commit_output.lower():
                print(f"Commit warning: {commit_output}")
                return False
            
            # Exit config mode
            self.execute_command("exit")
            
            return True
            
        except Exception as e:
            print(f"Config error: {e}")
            return False
    
    def get_hostname(self) -> str:
        """Return the device hostname"""
        return self.device_hostname or "unknown"
    
    def close(self) -> None:
        """Close SSH connection"""
        if self.shell:
            self.shell.close()
            self.shell = None
        if self.client:
            self.client.close()
            self.client = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    
    def __repr__(self):
        return f"DeviceConnector({self.hostname}, user={self.username})"

