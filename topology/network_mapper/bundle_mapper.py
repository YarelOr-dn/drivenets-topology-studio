"""
Bundle Mapper Module

Maps physical interfaces to their bundle membership via bundle-id attachments.
"""

import re
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class BundleInfo:
    """Information about a bundle and its members"""
    name: str
    members: list[str] = field(default_factory=list)
    sub_interfaces: list[str] = field(default_factory=list)
    admin_state: str = "disabled"
    oper_state: str = "down"


class BundleMapper:
    """Maps physical interfaces to bundle membership"""
    
    def __init__(self, connector):
        self.connector = connector
        self._bundles: dict[str, BundleInfo] = {}
        self._interface_to_bundle: dict[str, str] = {}
        self._parsed = False
    
    def parse_bundle_attachments(self) -> dict:
        """Parse all bundle attachments from device"""
        if self._parsed:
            return self._get_bundle_data()
        
        # Get interface details
        output = self.connector.execute_command("show interfaces detail", timeout=120)
        self._parse_output(output)
        self._parsed = True
        
        return self._get_bundle_data()
    
    def _parse_output(self, output: str) -> None:
        """Parse show interfaces detail output for bundle info"""
        current_interface = None
        current_bundle_id = None
        
        for line in output.split('\n'):
            # Check for interface header
            # Pattern: ge400-0/0/1 or bundle-1 at start of line
            if_match = re.match(r'^(ge\d+-\d+/\d+/\d+|bundle-\d+)(?:\.\d+)?(?:\s|$)', line)
            if if_match:
                # Save previous interface's bundle-id
                if current_interface and current_bundle_id:
                    self._interface_to_bundle[current_interface] = current_bundle_id
                    if current_bundle_id not in self._bundles:
                        self._bundles[current_bundle_id] = BundleInfo(name=current_bundle_id)
                    if current_interface not in self._bundles[current_bundle_id].members:
                        self._bundles[current_bundle_id].members.append(current_interface)
                
                current_interface = if_match.group(0).strip()
                current_bundle_id = None
                
                # Check if this is a bundle itself
                if current_interface.startswith('bundle-') and '.' not in current_interface:
                    if current_interface not in self._bundles:
                        self._bundles[current_interface] = BundleInfo(name=current_interface)
            
            # Check for bundle-id line
            bundle_match = re.search(r'bundle-id[:\s]+(\S+)', line, re.IGNORECASE)
            if bundle_match and current_interface:
                current_bundle_id = bundle_match.group(1)
        
        # Don't forget last interface
        if current_interface and current_bundle_id:
            self._interface_to_bundle[current_interface] = current_bundle_id
            if current_bundle_id not in self._bundles:
                self._bundles[current_bundle_id] = BundleInfo(name=current_bundle_id)
            if current_interface not in self._bundles[current_bundle_id].members:
                self._bundles[current_bundle_id].members.append(current_interface)
        
        # Also try to get bundle members from bundle interface details
        self._parse_bundle_members(output)
    
    def _parse_bundle_members(self, output: str) -> None:
        """Parse bundle member information"""
        # Look for member patterns in bundle interface sections
        current_bundle = None
        
        for line in output.split('\n'):
            # Check for bundle interface header
            bundle_match = re.match(r'^(bundle-\d+)(?:\s|$)', line)
            if bundle_match:
                current_bundle = bundle_match.group(1)
                if current_bundle not in self._bundles:
                    self._bundles[current_bundle] = BundleInfo(name=current_bundle)
            
            # Check for member list (various formats)
            if current_bundle:
                # Pattern: members: ge400-0/0/1, ge400-0/0/2
                member_match = re.search(r'members?[:\s]+([\w\-/,\s]+)', line, re.IGNORECASE)
                if member_match:
                    members_str = member_match.group(1)
                    for member in re.findall(r'ge\d+-\d+/\d+/\d+', members_str):
                        if member not in self._bundles[current_bundle].members:
                            self._bundles[current_bundle].members.append(member)
                            self._interface_to_bundle[member] = current_bundle
    
    def _get_bundle_data(self) -> dict:
        """Return bundle data in a structured format"""
        return {
            "bundles": {
                name: {
                    "members": info.members,
                    "sub_interfaces": info.sub_interfaces,
                    "admin_state": info.admin_state,
                    "oper_state": info.oper_state
                }
                for name, info in self._bundles.items()
            },
            "interfaces": self._interface_to_bundle.copy()
        }
    
    def get_bundle_members(self, bundle_name: str) -> list[str]:
        """Get list of member interfaces for a bundle"""
        if not self._parsed:
            self.parse_bundle_attachments()
        
        if bundle_name in self._bundles:
            return self._bundles[bundle_name].members.copy()
        return []
    
    def get_interface_bundle(self, interface: str) -> Optional[str]:
        """Get the bundle that an interface belongs to (if any)"""
        if not self._parsed:
            self.parse_bundle_attachments()
        
        return self._interface_to_bundle.get(interface)
    
    def is_bundle_member(self, interface: str) -> bool:
        """Check if an interface is a member of any bundle"""
        return self.get_interface_bundle(interface) is not None
    
    def get_all_bundles(self) -> list[str]:
        """Get list of all bundle names"""
        if not self._parsed:
            self.parse_bundle_attachments()
        
        return list(self._bundles.keys())
    
    def get_bundle_info(self, bundle_name: str) -> Optional[BundleInfo]:
        """Get full bundle info object"""
        if not self._parsed:
            self.parse_bundle_attachments()
        
        return self._bundles.get(bundle_name)
    
    def __repr__(self):
        return f"BundleMapper({len(self._bundles)} bundles, {len(self._interface_to_bundle)} members)"











