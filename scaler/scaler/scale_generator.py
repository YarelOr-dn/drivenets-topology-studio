"""Scale configuration generator for DNOS devices."""

from typing import List, Dict, Any, Optional
from .models import (
    InterfaceScale,
    ServiceScale,
    BGPPeerScale,
    ScaleConfig,
    ServiceType,
    InterfaceType,
)


class ScaleGenerator:
    """Generates scaled DNOS configuration snippets."""
    
    def __init__(self):
        """Initialize the scale generator."""
        pass
    
    def generate_interfaces(self, scale: InterfaceScale) -> str:
        """Generate interface configuration in correct DNOS hierarchical syntax.
        
        Args:
            scale: Interface scaling parameters
            
        Returns:
            DNOS configuration string
        """
        lines = ["interfaces"]
        interface_type = scale.interface_type.value
        
        for i in range(scale.count):
            iface_num = scale.start_number + i
            
            if interface_type == "bundle":
                iface_name = f"bundle-{iface_num}"
            elif interface_type == "ph":
                iface_name = f"ph{iface_num}"
            elif interface_type == "ge100":
                iface_name = f"ge100-{scale.slot}/{scale.bay}/{scale.port_start + i}"
            elif interface_type == "ge400":
                iface_name = f"ge400-{scale.slot}/{scale.bay}/{scale.port_start + i}"
            else:
                iface_name = f"{interface_type}{iface_num}"
            
            lines.append(f"  {iface_name}")
            lines.append("    admin-state enabled")
            lines.append(f'    description "Scaled interface {i+1}"')
            lines.append("  !")
            
            if scale.create_subinterfaces:
                for j in range(scale.subif_count_per_interface):
                    vlan = scale.subif_vlan_start + (i * scale.subif_count_per_interface + j) * scale.subif_vlan_step
                    if vlan > 4094:
                        vlan = 4094
                    
                    lines.append(f"  {iface_name}.{vlan}")
                    lines.append("    admin-state enabled")
                    lines.append(f"    vlan-id {vlan}")
                    lines.append("  !")
        
        lines.append("!")
        return "\n".join(lines)
    
    def generate_services(self, scale: ServiceScale) -> str:
        """Generate network service configuration.
        
        Args:
            scale: Service scaling parameters
            
        Returns:
            DNOS configuration string
        """
        lines = []
        service_type = scale.service_type.value
        
        for i in range(scale.count):
            svc_num = scale.start_number + i
            svc_name = f"{scale.name_prefix}{svc_num}"
            
            if service_type == "evpn-vpws-fxc":
                lines.append(f"network-services evpn-vpws-fxc instance {svc_name}")
                lines.append(f"  service-id {scale.service_id_start + i}")
                lines.append(f"  evi {scale.evi_start + i}")
                lines.append("  admin-state enabled")
                lines.append("!")
            elif service_type == "vrf":
                lines.append(f"network-services vrf {svc_name}")
                lines.append(f"  rd {scale.rd_base}:{svc_num}")
                lines.append("  admin-state enabled")
                lines.append("!")
            elif service_type == "evpn":
                lines.append(f"network-services evpn {svc_name}")
                lines.append(f"  evi {scale.evi_start + i}")
                lines.append("  admin-state enabled")
                lines.append("!")
        
        return "\n".join(lines)
    
    def generate_bgp_peers(self, scale: BGPPeerScale) -> str:
        """Generate BGP peer configuration.
        
        Args:
            scale: BGP peer scaling parameters
            
        Returns:
            DNOS configuration string
        """
        lines = []
        
        # Parse starting IP
        ip_parts = scale.peer_ip_start.split('.')
        base_ip = [int(p) for p in ip_parts]
        
        lines.append(f"protocols bgp {scale.local_as}")
        
        for i in range(scale.count):
            # Calculate peer IP
            ip = base_ip.copy()
            ip[3] += i * scale.peer_ip_step
            
            # Handle overflow
            while ip[3] > 255:
                ip[3] -= 256
                ip[2] += 1
            while ip[2] > 255:
                ip[2] -= 256
                ip[1] += 1
            
            peer_ip = '.'.join(str(p) for p in ip)
            peer_as = scale.peer_as_start + (i * scale.peer_as_step if scale.peer_as_step else 0)
            
            lines.append(f"  neighbor {peer_ip}")
            lines.append(f"    remote-as {peer_as}")
            if scale.peer_group:
                lines.append(f"    peer-group {scale.peer_group}")
            lines.append("    admin-state enabled")
            lines.append("  !")
        
        lines.append("!")
        
        return "\n".join(lines)
    
    def generate_vlans(self, vlan_start: int, vlan_count: int, vlan_step: int = 1) -> str:
        """Generate VLAN configuration.
        
        Args:
            vlan_start: Starting VLAN ID
            vlan_count: Number of VLANs
            vlan_step: VLAN ID increment
            
        Returns:
            DNOS configuration string
        """
        lines = []
        
        for i in range(vlan_count):
            vlan_id = vlan_start + (i * vlan_step)
            if vlan_id > 4094:
                break
            lines.append(f"vlans vlan {vlan_id}")
            lines.append(f"  name \"VLAN-{vlan_id}\"")
            lines.append("!")
        
        return "\n".join(lines)
    
    def generate_full_config(self, config: ScaleConfig) -> str:
        """Generate complete scaled configuration.
        
        Args:
            config: Complete scale configuration
            
        Returns:
            Full DNOS configuration string
        """
        sections = []
        
        # Interfaces
        if config.interfaces:
            for iface in config.interfaces:
                sections.append(self.generate_interfaces(iface))
        
        # Services
        if config.services:
            for svc in config.services:
                sections.append(self.generate_services(svc))
        
        # BGP Peers
        if config.bgp_peers:
            for bgp in config.bgp_peers:
                sections.append(self.generate_bgp_peers(bgp))
        
        return "\n\n".join(sections)














