"""
Report Generator Module

Generates text reports from topology data.
"""

from datetime import datetime
from typing import Optional


class ReportGenerator:
    """Generates text topology reports"""
    
    def __init__(self, topology_builder, bundle_data: dict = None):
        self.topology = topology_builder
        self.bundle_data = bundle_data or {}
        self.starting_device = ""
        self.enabled_interfaces = []
    
    def set_starting_device(self, device: str) -> None:
        """Set the starting device for the report"""
        self.starting_device = device
    
    def set_enabled_interfaces(self, interfaces: list) -> None:
        """Set the list of interfaces that were enabled"""
        self.enabled_interfaces = interfaces
    
    def generate_header(self) -> str:
        """Generate report header"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        width = 80
        
        lines = [
            "=" * width,
            "NETWORK TOPOLOGY MAP".center(width),
            f"Generated: {now}".center(width),
            f"Starting Device: {self.starting_device}".center(width),
            "=" * width,
            ""
        ]
        return "\n".join(lines)
    
    def generate_interfaces_section(self) -> str:
        """Generate physical interfaces section"""
        lines = ["=== PHYSICAL INTERFACES ENABLED ==="]
        
        if not self.enabled_interfaces:
            lines.append("  (No interfaces recorded)")
        else:
            for iface in self.enabled_interfaces:
                name = iface.get("name", iface) if isinstance(iface, dict) else iface
                bundle_id = None
                
                # Check if interface has bundle-id
                if isinstance(iface, dict):
                    bundle_id = iface.get("bundle_id")
                elif self.bundle_data.get("interfaces"):
                    bundle_id = self.bundle_data["interfaces"].get(name)
                
                if bundle_id:
                    lines.append(f"  {name:<20} enabled, LLDP enabled, bundle-id: {bundle_id}")
                else:
                    lines.append(f"  {name:<20} enabled, LLDP enabled, standalone")
        
        lines.append("")
        return "\n".join(lines)
    
    def generate_bundles_section(self) -> str:
        """Generate bundle membership section"""
        lines = ["=== BUNDLE MEMBERSHIP ==="]
        
        bundles = self.bundle_data.get("bundles", {})
        
        if not bundles:
            lines.append("  (No bundles detected)")
        else:
            for bundle_name, bundle_info in bundles.items():
                members = bundle_info.get("members", [])
                subs = bundle_info.get("sub_interfaces", [])
                
                lines.append(f"  {bundle_name}:")
                if members:
                    lines.append(f"    Members: {', '.join(members)}")
                if subs:
                    lines.append(f"    Sub-interfaces: {', '.join(subs)}")
        
        lines.append("")
        return "\n".join(lines)
    
    def generate_physical_section(self) -> str:
        """Generate physical topology section"""
        lines = ["=== PHYSICAL TOPOLOGY (LLDP) ==="]
        
        physical = self.topology.get_physical_topology()
        links = physical.get("links", [])
        
        if not links:
            lines.append("  (No physical links discovered)")
        else:
            for link in links:
                local = f"{link['local_device']}:{link['local_interface']}"
                remote = f"{link['remote_device']}:{link['remote_interface']}"
                
                if link.get("type") == "snake":
                    lines.append(f"  {local:<35} <----> {remote}  [SNAKE]")
                else:
                    lines.append(f"  {local:<35} <----> {remote}")
        
        lines.append("")
        return "\n".join(lines)
    
    def generate_logical_section(self) -> str:
        """Generate logical topology section"""
        lines = ["=== LOGICAL TOPOLOGY (PE to PE) ==="]
        
        logical = self.topology.get_logical_topology()
        paths = logical.get("paths", [])
        
        if not paths:
            lines.append("  (No logical paths discovered)")
            lines.append("")
            return "\n".join(lines)
        
        for i, path in enumerate(paths, 1):
            source = path.get("source", {})
            dest = path.get("destination", {})
            via = path.get("via", [])
            
            source_dev = source.get("device", "?")
            source_if = source.get("interface", "?")
            source_members = source.get("bundle_members")
            
            dest_dev = dest.get("device", "?")
            dest_if = dest.get("interface", "?")
            dest_members = dest.get("bundle_members")
            
            lines.append("")
            lines.append(f"  Path {i}: {source_dev} <========> {dest_dev}")
            
            # Source info
            if source_members:
                members_str = ", ".join(source_members)
                lines.append(f"    Source:      {source_if} (LAG: {members_str})")
            else:
                lines.append(f"    Source:      {source_if} (standalone)")
            
            # Destination info
            if dest_members:
                members_str = ", ".join(dest_members)
                lines.append(f"    Destination: {dest_if} (LAG: {members_str})")
            else:
                lines.append(f"    Destination: {dest_if} (standalone)")
            
            # Via info
            if via:
                via_str = " -> ".join(via)
                lines.append(f"    Via DNAAS:   {via_str}")
        
        lines.append("")
        return "\n".join(lines)
    
    def generate_snakes_section(self) -> str:
        """Generate snake connections section"""
        lines = ["=== SNAKE CONNECTIONS ==="]
        
        snakes = self.topology.get_snakes()
        
        if not snakes:
            lines.append("  (No snake connections detected)")
        else:
            for snake in snakes:
                device = snake.get("device", "?")
                if1 = snake.get("interface1", "?")
                if2 = snake.get("interface2", "?")
                lines.append(f"  {device}:{if1} <--loopback--> {device}:{if2}")
        
        lines.append("")
        return "\n".join(lines)
    
    def generate_footer(self) -> str:
        """Generate report footer"""
        width = 80
        lines = [
            "=" * width,
            "END OF REPORT".center(width),
            "=" * width
        ]
        return "\n".join(lines)
    
    def generate_full_report(self) -> str:
        """Generate the complete report"""
        sections = [
            self.generate_header(),
            self.generate_interfaces_section(),
            self.generate_bundles_section(),
            self.generate_physical_section(),
            self.generate_logical_section(),
            self.generate_snakes_section(),
            self.generate_footer()
        ]
        return "\n".join(sections)
    
    def write_report(self, output_path: str) -> None:
        """Write report to file"""
        report = self.generate_full_report()
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        print(f"Report written to: {output_path}")
    
    def print_report(self) -> None:
        """Print report to stdout"""
        print(self.generate_full_report())
    
    def __repr__(self):
        return f"ReportGenerator(device={self.starting_device})"











