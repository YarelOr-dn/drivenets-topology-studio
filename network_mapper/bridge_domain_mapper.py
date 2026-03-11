"""
Bridge Domain Mapper Module

Maps paths through DNAAS via Bridge Domain attachments.
"""

import re
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class BridgeDomain:
    """Represents a bridge domain"""
    name: str
    attachments: list[str] = field(default_factory=list)
    admin_state: str = "enabled"
    description: str = ""


class BridgeDomainMapper:
    """Maps paths through DNAAS via Bridge Domains"""
    
    def __init__(self, connector):
        self.connector = connector
        self._bridge_domains: dict[str, BridgeDomain] = {}
        self._interface_to_bd: dict[str, str] = {}
        self._parsed = False
    
    def get_bridge_domains(self) -> list[BridgeDomain]:
        """Get all bridge domains"""
        if not self._parsed:
            self._discover_bridge_domains()
        return list(self._bridge_domains.values())
    
    def _discover_bridge_domains(self) -> None:
        """Discover bridge domains from device"""
        output = self.connector.execute_command(
            "show network-services bridge domain", 
            timeout=60
        )
        self._parse_bd_output(output)
        self._parsed = True
    
    def _parse_bd_output(self, output: str) -> None:
        """Parse bridge domain output"""
        current_bd = None
        
        for line in output.split('\n'):
            line_stripped = line.strip()
            
            # Check for bridge domain name
            # Pattern: "bridge-domain CUST-A" or "BD: CUST-A" or table row
            bd_match = re.match(r'^(?:bridge-domain|BD)[:\s]+(\S+)', line_stripped, re.IGNORECASE)
            if bd_match:
                bd_name = bd_match.group(1)
                current_bd = BridgeDomain(name=bd_name)
                self._bridge_domains[bd_name] = current_bd
                continue
            
            # Check for table format: | BD-NAME | enabled | ...
            table_match = re.match(r'\|\s*(\S+)\s*\|\s*(enabled|disabled)\s*\|', line_stripped)
            if table_match:
                bd_name = table_match.group(1)
                if bd_name.lower() not in ['name', 'bridge-domain', 'bd']:
                    current_bd = BridgeDomain(name=bd_name, admin_state=table_match.group(2))
                    self._bridge_domains[bd_name] = current_bd
                continue
            
            # Check for interface attachments
            if current_bd:
                # Pattern: interface ge100-0/0/5.100 or attachment: ge100-0/0/5
                if_match = re.search(r'(?:interface|attachment)[:\s]+(ge\d+-\d+/\d+/\d+(?:\.\d+)?|bundle-\d+(?:\.\d+)?)', 
                                    line_stripped, re.IGNORECASE)
                if if_match:
                    iface = if_match.group(1)
                    if iface not in current_bd.attachments:
                        current_bd.attachments.append(iface)
                        self._interface_to_bd[iface] = current_bd.name
                    continue
                
                # Also check for interface listed directly (indented under BD)
                if line.startswith('  ') or line.startswith('\t'):
                    iface_match = re.match(r'\s*(ge\d+-\d+/\d+/\d+(?:\.\d+)?|bundle-\d+(?:\.\d+)?)', line)
                    if iface_match:
                        iface = iface_match.group(1)
                        if iface not in current_bd.attachments:
                            current_bd.attachments.append(iface)
                            self._interface_to_bd[iface] = current_bd.name
    
    def get_bd_for_interface(self, interface: str) -> Optional[str]:
        """Get the bridge domain for an interface"""
        if not self._parsed:
            self._discover_bridge_domains()
        
        # Direct lookup
        if interface in self._interface_to_bd:
            return self._interface_to_bd[interface]
        
        # Try parent interface if this is a sub-interface
        if '.' in interface:
            parent = interface.split('.')[0]
            for bd_name, bd in self._bridge_domains.items():
                for attachment in bd.attachments:
                    if attachment.startswith(parent + '.'):
                        # Found a sub-interface of same parent
                        return bd_name
        
        return None
    
    def get_bd_attachments(self, bd_name: str) -> list[str]:
        """Get all interfaces attached to a bridge domain"""
        if not self._parsed:
            self._discover_bridge_domains()
        
        if bd_name in self._bridge_domains:
            return self._bridge_domains[bd_name].attachments.copy()
        return []
    
    def get_remote_attachments(self, bd_name: str, exclude_interface: str) -> list[str]:
        """Get BD attachments excluding a specific interface"""
        attachments = self.get_bd_attachments(bd_name)
        
        # Exclude the specified interface and its parent/children
        exclude_base = exclude_interface.split('.')[0]
        
        return [a for a in attachments 
                if a != exclude_interface and not a.startswith(exclude_base + '.')]
    
    def trace_path_from_interface(self, start_interface: str) -> dict:
        """
        Trace the path from an interface through bridge domains.
        Returns dict with BD info and other attachments.
        """
        if not self._parsed:
            self._discover_bridge_domains()
        
        result = {
            "start_interface": start_interface,
            "bridge_domain": None,
            "other_attachments": [],
            "path": []
        }
        
        # Find the BD for this interface
        bd_name = self.get_bd_for_interface(start_interface)
        if not bd_name:
            return result
        
        result["bridge_domain"] = bd_name
        result["other_attachments"] = self.get_remote_attachments(bd_name, start_interface)
        result["path"].append({
            "type": "bridge_domain",
            "name": bd_name,
            "attachments": result["other_attachments"]
        })
        
        return result
    
    def find_path_to_interface(self, from_interface: str, to_interface_pattern: str) -> Optional[dict]:
        """
        Find a path from one interface to another through bridge domains.
        to_interface_pattern can be a regex pattern.
        """
        trace = self.trace_path_from_interface(from_interface)
        
        if not trace["bridge_domain"]:
            return None
        
        # Check if any attachment matches the target pattern
        pattern = re.compile(to_interface_pattern, re.IGNORECASE)
        for attachment in trace["other_attachments"]:
            if pattern.search(attachment):
                trace["destination"] = attachment
                return trace
        
        return None
    
    def __repr__(self):
        return f"BridgeDomainMapper({len(self._bridge_domains)} BDs)"











