"""
Interface Discovery Module

Discovers and enables physical interfaces on network devices.
"""

import re
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Interface:
    """Represents a network interface"""
    name: str
    admin_state: str = "disabled"
    oper_state: str = "down"
    interface_type: str = "unknown"
    is_physical: bool = False
    is_subinterface: bool = False
    parent_interface: Optional[str] = None
    bundle_id: Optional[str] = None
    description: str = ""
    
    @property
    def is_real_physical(self) -> bool:
        """Check if this is a real physical interface (not loopback, irb, ph, etc.)"""
        name_lower = self.name.lower()
        
        # Exclude patterns
        exclude_patterns = [
            r'^lo\d*$',           # loopback
            r'^ph\d+',            # PWHE
            r'^irb\d+',           # IRB
            r'^mgmt',             # Management
            r'^ctrl',             # Control
            r'^ipmi',             # IPMI
            r'^console',          # Console
            r'^fab',              # Fabric
        ]
        
        for pattern in exclude_patterns:
            if re.match(pattern, name_lower):
                return False
        
        # Must be ge* or bundle-* (without sub-interface)
        if re.match(r'^(ge\d+|bundle)-', name_lower) and '.' not in self.name:
            return True
        
        return False


class InterfaceDiscovery:
    """Discovers and enables physical interfaces"""
    
    def __init__(self, connector):
        self.connector = connector
        self._interfaces: list[Interface] = []
    
    def get_all_interfaces(self) -> list[Interface]:
        """Get all interfaces from the device"""
        if not self._interfaces:
            self._parse_interfaces()
        return self._interfaces
    
    def get_physical_interfaces(self) -> list[Interface]:
        """Get only real physical interfaces (ge*, bundle-* parents)"""
        all_ifs = self.get_all_interfaces()
        return [i for i in all_ifs if i.is_real_physical]
    
    def _parse_interfaces(self) -> None:
        """Parse 'show interfaces' output
        
        Note: This can take 60-120 seconds on devices with many interfaces.
        """
        print("    Querying interfaces (60-120s on large devices)...", flush=True)
        output = self.connector.execute_command("show interfaces", timeout=180)
        self._interfaces = self._parse_interface_table(output)
        print(f"    Found {len(self._interfaces)} interfaces", flush=True)
    
    def _parse_interface_table(self, output: str) -> list[Interface]:
        """Parse interface table output"""
        interfaces = []
        
        # Pattern to match interface lines in table format
        # Example: | ge400-0/0/1 | enabled | up | ...
        table_pattern = r'\|\s*(\S+)\s*\|\s*(enabled|disabled)\s*\|\s*(\S+)\s*\|'
        
        for match in re.finditer(table_pattern, output):
            name = match.group(1)
            admin_state = match.group(2)
            oper_state = match.group(3)
            
            # Determine interface type
            if_type = self._determine_interface_type(name)
            is_sub = '.' in name
            parent = name.split('.')[0] if is_sub else None
            
            iface = Interface(
                name=name,
                admin_state=admin_state,
                oper_state=oper_state,
                interface_type=if_type,
                is_physical=(if_type in ['physical', 'bundle']),
                is_subinterface=is_sub,
                parent_interface=parent
            )
            
            interfaces.append(iface)
        
        # If table format didn't work, try detail format
        if not interfaces:
            interfaces = self._parse_interface_detail(output)
        
        return interfaces
    
    def _parse_interface_detail(self, output: str) -> list[Interface]:
        """Parse detailed interface output (fallback)"""
        interfaces = []
        
        # Split by interface sections
        sections = re.split(r'\n(?=\S+\s*$|\S+\n\s+admin-state)', output)
        
        current_name = None
        current_admin = "disabled"
        current_oper = "down"
        
        for line in output.split('\n'):
            line = line.strip()
            
            # Check for interface name (starts at column 0, no leading whitespace)
            if line and not line.startswith(' ') and not line.startswith('|'):
                # Could be an interface name
                name_match = re.match(r'^(ge\d+-\d+/\d+/\d+(?:\.\d+)?|bundle-\d+(?:\.\d+)?|lo\d+|ph\d+(?:\.\d+)?|irb\d+)', line)
                if name_match:
                    # Save previous interface
                    if current_name:
                        if_type = self._determine_interface_type(current_name)
                        is_sub = '.' in current_name
                        parent = current_name.split('.')[0] if is_sub else None
                        
                        interfaces.append(Interface(
                            name=current_name,
                            admin_state=current_admin,
                            oper_state=current_oper,
                            interface_type=if_type,
                            is_physical=(if_type in ['physical', 'bundle']),
                            is_subinterface=is_sub,
                            parent_interface=parent
                        ))
                    
                    current_name = name_match.group(1)
                    current_admin = "disabled"
                    current_oper = "down"
            
            # Check for admin-state
            if 'admin-state' in line.lower():
                if 'enabled' in line.lower():
                    current_admin = "enabled"
                elif 'disabled' in line.lower():
                    current_admin = "disabled"
        
        # Don't forget the last interface
        if current_name:
            if_type = self._determine_interface_type(current_name)
            is_sub = '.' in current_name
            parent = current_name.split('.')[0] if is_sub else None
            
            interfaces.append(Interface(
                name=current_name,
                admin_state=current_admin,
                oper_state=current_oper,
                interface_type=if_type,
                is_physical=(if_type in ['physical', 'bundle']),
                is_subinterface=is_sub,
                parent_interface=parent
            ))
        
        return interfaces
    
    def _determine_interface_type(self, name: str) -> str:
        """Determine interface type from name"""
        name_lower = name.lower()
        
        if name_lower.startswith('ge'):
            return 'physical'
        elif name_lower.startswith('bundle'):
            return 'bundle'
        elif name_lower.startswith('lo'):
            return 'loopback'
        elif name_lower.startswith('ph'):
            return 'pwhe'
        elif name_lower.startswith('irb'):
            return 'irb'
        elif name_lower.startswith('mgmt'):
            return 'management'
        else:
            return 'unknown'
    
    def generate_enable_config(self, interfaces: list[Interface] = None) -> list[str]:
        """Generate config lines to enable interfaces"""
        if interfaces is None:
            interfaces = self.get_physical_interfaces()
        
        config_lines = []
        for iface in interfaces:
            if iface.admin_state != "enabled":
                config_lines.append(f"interfaces {iface.name} admin-state enabled")
        
        return config_lines
    
    def refresh_interface_states(self) -> list[Interface]:
        """Re-fetch interface states to get current oper-state"""
        self._interfaces = []  # Clear cache
        return self.get_all_interfaces()
    
    def get_operationally_up_interfaces(self) -> list[Interface]:
        """Get interfaces that are admin-enabled AND operationally up"""
        all_ifs = self.get_all_interfaces()
        return [
            i for i in all_ifs 
            if i.is_real_physical 
            and i.admin_state == "enabled" 
            and i.oper_state == "up"
        ]
    
    def get_existing_lldp_interfaces(self) -> set:
        """Get list of interfaces already configured under protocols lldp"""
        output = self.connector.execute_command("show lldp", timeout=30)
        
        # Parse LLDP interface table to find configured interfaces
        lldp_interfaces = set()
        
        # Look for interface patterns in LLDP output
        # The output usually shows interfaces with LLDP enabled
        for match in re.finditer(r'(ge\d+-\d+/\d+/\d+|bundle-\d+)', output):
            lldp_interfaces.add(match.group(1))
        
        return lldp_interfaces
    
    def generate_lldp_config(self, interfaces: list[Interface] = None, 
                             skip_existing: bool = True) -> list[str]:
        """Generate config lines to enable LLDP on interfaces
        
        Args:
            interfaces: List of interfaces to configure (defaults to oper-up physical)
            skip_existing: If True, skip interfaces already in LLDP config
        """
        if interfaces is None:
            interfaces = self.get_operationally_up_interfaces()
        
        # Get already configured LLDP interfaces
        existing_lldp = set()
        if skip_existing:
            existing_lldp = self.get_existing_lldp_interfaces()
        
        config_lines = []
        for iface in interfaces:
            # Only enable LLDP on real physical interfaces, not bundles
            if iface.interface_type == 'physical':
                if iface.name not in existing_lldp:
                    config_lines.append(f"protocols lldp interface {iface.name} admin-state enabled")
        
        return config_lines
    
    def __repr__(self):
        return f"InterfaceDiscovery({len(self._interfaces)} interfaces)"

