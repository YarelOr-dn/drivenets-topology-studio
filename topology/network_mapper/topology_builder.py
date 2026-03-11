"""
Topology Builder Module

Builds physical and logical topology graphs from discovered information.
"""

from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PhysicalLink:
    """Represents a physical link between devices"""
    local_device: str
    local_interface: str
    remote_device: str
    remote_interface: str
    link_type: str = "physical"  # physical, snake
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass 
class LogicalPath:
    """Represents a logical path between PE endpoints"""
    source_device: str
    source_interface: str
    source_bundle_members: Optional[list] = None
    destination_device: str = ""
    destination_interface: str = ""
    destination_bundle_members: Optional[list] = None
    via_devices: list = field(default_factory=list)
    bridge_domains: list = field(default_factory=list)


@dataclass
class SnakeConnection:
    """Represents a snake (loopback) connection"""
    device: str
    interface1: str
    interface2: str


class TopologyBuilder:
    """Builds physical and logical topology graphs"""
    
    def __init__(self):
        self._physical_links: list[PhysicalLink] = []
        self._logical_paths: list[LogicalPath] = []
        self._snakes: list[SnakeConnection] = []
        self._devices: dict[str, dict] = {}  # device_name -> info
        self._bundles: dict[str, dict] = {}  # bundle_name -> members info
    
    def add_device(self, name: str, device_type: str = "unknown", 
                   ip: str = None, **kwargs) -> None:
        """Add or update a device in the topology"""
        if name not in self._devices:
            self._devices[name] = {
                "name": name,
                "type": device_type,
                "ip": ip,
                "interfaces": [],
                "neighbors": []
            }
        else:
            if device_type != "unknown":
                self._devices[name]["type"] = device_type
            if ip:
                self._devices[name]["ip"] = ip
        
        # Add any extra info
        self._devices[name].update(kwargs)
    
    def add_physical_link(self, local_device: str, local_interface: str,
                          remote_device: str, remote_interface: str,
                          link_type: str = "physical") -> None:
        """Add a physical link to the topology"""
        # Avoid duplicates
        for link in self._physical_links:
            if (link.local_device == local_device and 
                link.local_interface == local_interface and
                link.remote_device == remote_device):
                return
        
        self._physical_links.append(PhysicalLink(
            local_device=local_device,
            local_interface=local_interface,
            remote_device=remote_device,
            remote_interface=remote_interface,
            link_type=link_type
        ))
        
        # Ensure devices exist
        self.add_device(local_device)
        self.add_device(remote_device)
    
    def add_logical_path(self, source_device: str, source_interface: str,
                         dest_device: str, dest_interface: str,
                         via_devices: list = None,
                         source_bundle: list = None,
                         dest_bundle: list = None) -> None:
        """Add a logical path between PE endpoints"""
        # Avoid duplicates
        for path in self._logical_paths:
            if (path.source_device == source_device and 
                path.source_interface == source_interface and
                path.destination_device == dest_device and
                path.destination_interface == dest_interface):
                return
        
        self._logical_paths.append(LogicalPath(
            source_device=source_device,
            source_interface=source_interface,
            source_bundle_members=source_bundle,
            destination_device=dest_device,
            destination_interface=dest_interface,
            destination_bundle_members=dest_bundle,
            via_devices=via_devices or []
        ))
    
    def add_snake(self, device: str, interface1: str, interface2: str) -> None:
        """Add a snake (loopback) connection"""
        # Avoid duplicates
        for snake in self._snakes:
            if (snake.device == device and 
                {snake.interface1, snake.interface2} == {interface1, interface2}):
                return
        
        self._snakes.append(SnakeConnection(
            device=device,
            interface1=interface1,
            interface2=interface2
        ))
    
    def add_bundle_info(self, bundle_name: str, members: list, 
                        device: str = None) -> None:
        """Add bundle membership information"""
        key = f"{device}:{bundle_name}" if device else bundle_name
        self._bundles[key] = {
            "name": bundle_name,
            "device": device,
            "members": members
        }
    
    def get_bundle_members(self, bundle_name: str, device: str = None) -> list:
        """Get members of a bundle"""
        key = f"{device}:{bundle_name}" if device else bundle_name
        if key in self._bundles:
            return self._bundles[key].get("members", [])
        
        # Try without device prefix
        if bundle_name in self._bundles:
            return self._bundles[bundle_name].get("members", [])
        
        return []
    
    def get_physical_topology(self) -> dict:
        """Get physical topology as a dictionary"""
        return {
            "devices": self._devices.copy(),
            "links": [
                {
                    "local_device": link.local_device,
                    "local_interface": link.local_interface,
                    "remote_device": link.remote_device,
                    "remote_interface": link.remote_interface,
                    "type": link.link_type
                }
                for link in self._physical_links
            ]
        }
    
    def get_logical_topology(self) -> dict:
        """Get logical topology as a dictionary"""
        return {
            "paths": [
                {
                    "source": {
                        "device": path.source_device,
                        "interface": path.source_interface,
                        "bundle_members": path.source_bundle_members
                    },
                    "destination": {
                        "device": path.destination_device,
                        "interface": path.destination_interface,
                        "bundle_members": path.destination_bundle_members
                    },
                    "via": path.via_devices
                }
                for path in self._logical_paths
            ]
        }
    
    def get_snakes(self) -> list[dict]:
        """Get snake connections as list of dicts"""
        return [
            {
                "device": snake.device,
                "interface1": snake.interface1,
                "interface2": snake.interface2
            }
            for snake in self._snakes
        ]
    
    def get_all_bundles(self) -> dict:
        """Get all bundle information"""
        return self._bundles.copy()
    
    def get_device_count(self) -> int:
        """Get number of discovered devices"""
        return len(self._devices)
    
    def get_link_count(self) -> int:
        """Get number of physical links"""
        return len(self._physical_links)
    
    def get_path_count(self) -> int:
        """Get number of logical paths"""
        return len(self._logical_paths)
    
    def get_summary(self) -> dict:
        """Get topology summary"""
        return {
            "devices": len(self._devices),
            "physical_links": len(self._physical_links),
            "logical_paths": len(self._logical_paths),
            "snake_connections": len(self._snakes),
            "bundles": len(self._bundles)
        }
    
    def __repr__(self):
        summary = self.get_summary()
        return (f"TopologyBuilder("
                f"{summary['devices']} devices, "
                f"{summary['physical_links']} links, "
                f"{summary['logical_paths']} paths)")











