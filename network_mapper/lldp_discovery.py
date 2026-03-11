"""
LLDP Discovery Module

Parses LLDP neighbors to discover directly connected devices.
"""

import re
from typing import Optional
from dataclasses import dataclass


@dataclass
class LLDPNeighbor:
    """Represents an LLDP neighbor"""
    local_interface: str
    remote_device: str
    remote_interface: str
    remote_port_desc: str = ""
    chassis_id: str = ""
    is_snake: bool = False
    
    def __post_init__(self):
        # Clean up interface names
        self.local_interface = self.local_interface.strip()
        self.remote_interface = self.remote_interface.strip()
        self.remote_device = self.remote_device.strip()


class LLDPDiscovery:
    """Discovers LLDP neighbors"""
    
    def __init__(self, connector, local_hostname: str = None):
        self.connector = connector
        self.local_hostname = local_hostname or connector.get_hostname()
        self._neighbors: list[LLDPNeighbor] = []
    
    def get_neighbors(self) -> list[LLDPNeighbor]:
        """Get all LLDP neighbors"""
        if not self._neighbors:
            self._discover_neighbors()
        return self._neighbors
    
    def _discover_neighbors(self) -> None:
        """Discover LLDP neighbors from device"""
        output = self.connector.execute_command("show lldp neighbors", timeout=30)
        self._neighbors = self._parse_lldp_output(output)
        
        # Mark snake connections
        for neighbor in self._neighbors:
            if self.is_snake_connection(neighbor):
                neighbor.is_snake = True
    
    def _parse_lldp_output(self, output: str) -> list[LLDPNeighbor]:
        """Parse LLDP neighbors output"""
        neighbors = []
        
        # Try table format first
        # Pattern: | ge400-0/0/1 | DNAAS-LEAF-A01 | ge100-0/0/5 | ...
        table_pattern = r'\|\s*(\S+)\s*\|\s*(\S+)\s*\|\s*(\S+)\s*\|'
        
        for match in re.finditer(table_pattern, output):
            local_if = match.group(1)
            remote_dev = match.group(2)
            remote_if = match.group(3)
            
            # Skip header rows
            if 'interface' in local_if.lower() or 'neighbor' in remote_dev.lower():
                continue
            
            # Skip separator rows
            if '-+-' in local_if or '---' in local_if:
                continue
            
            neighbors.append(LLDPNeighbor(
                local_interface=local_if,
                remote_device=remote_dev,
                remote_interface=remote_if
            ))
        
        # If table format didn't work, try other formats
        if not neighbors:
            neighbors = self._parse_lldp_detail(output)
        
        return neighbors
    
    def _parse_lldp_detail(self, output: str) -> list[LLDPNeighbor]:
        """Parse detailed LLDP output (fallback)"""
        neighbors = []
        
        current_local_if = None
        current_remote_dev = None
        current_remote_if = None
        
        for line in output.split('\n'):
            line = line.strip()
            
            # Local interface
            local_match = re.search(r'local\s+(?:interface|port)[:\s]+(\S+)', line, re.IGNORECASE)
            if local_match:
                # Save previous neighbor
                if current_local_if and current_remote_dev:
                    neighbors.append(LLDPNeighbor(
                        local_interface=current_local_if,
                        remote_device=current_remote_dev,
                        remote_interface=current_remote_if or "unknown"
                    ))
                
                current_local_if = local_match.group(1)
                current_remote_dev = None
                current_remote_if = None
            
            # Remote device/system name
            remote_dev_match = re.search(r'(?:system\s+name|neighbor|device)[:\s]+(\S+)', line, re.IGNORECASE)
            if remote_dev_match and current_local_if:
                current_remote_dev = remote_dev_match.group(1)
            
            # Remote interface/port
            remote_if_match = re.search(r'(?:remote\s+)?port(?:\s+id)?[:\s]+(\S+)', line, re.IGNORECASE)
            if remote_if_match and current_local_if:
                current_remote_if = remote_if_match.group(1)
        
        # Don't forget last neighbor
        if current_local_if and current_remote_dev:
            neighbors.append(LLDPNeighbor(
                local_interface=current_local_if,
                remote_device=current_remote_dev,
                remote_interface=current_remote_if or "unknown"
            ))
        
        return neighbors
    
    def is_snake_connection(self, neighbor: LLDPNeighbor) -> bool:
        """Check if neighbor is a snake (self-loop) connection"""
        # Compare hostnames (case-insensitive)
        local_name = self.local_hostname.lower().strip()
        remote_name = neighbor.remote_device.lower().strip()
        
        # Direct match
        if local_name == remote_name:
            return True
        
        # Partial match (hostname might have domain suffix)
        if local_name in remote_name or remote_name in local_name:
            return True
        
        return False
    
    def is_dnaas_device(self, device_name: str) -> bool:
        """Check if device name looks like a DNAAS device"""
        name_lower = device_name.lower()
        return 'dnaas' in name_lower
    
    def get_dnaas_neighbors(self) -> list[LLDPNeighbor]:
        """Get only DNAAS device neighbors"""
        return [n for n in self.get_neighbors() 
                if self.is_dnaas_device(n.remote_device) and not n.is_snake]
    
    def get_snake_connections(self) -> list[LLDPNeighbor]:
        """Get only snake (self-loop) connections"""
        return [n for n in self.get_neighbors() if n.is_snake]
    
    def get_pe_neighbors(self) -> list[LLDPNeighbor]:
        """Get neighbors that appear to be PE devices"""
        return [n for n in self.get_neighbors() 
                if not self.is_dnaas_device(n.remote_device) and not n.is_snake]
    
    def __repr__(self):
        return f"LLDPDiscovery({len(self._neighbors)} neighbors)"











