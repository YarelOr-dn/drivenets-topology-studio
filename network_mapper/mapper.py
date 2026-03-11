#!/usr/bin/env python3
"""
Network Topology Mapper - Main Orchestrator

Maps network topology from PE devices through DNAAS infrastructure.

Usage:
    python -m network_mapper.mapper <starting_device> [-o output_dir]
    
Example:
    python -m network_mapper.mapper PE-1 -o reports
    python -m network_mapper.mapper 10.0.0.1
"""

import os
import sys
import argparse
from datetime import datetime
from typing import Optional

from .device_connector import DeviceConnector
from .dnaas_lookup import DNAASLookup
from .interface_discovery import InterfaceDiscovery
from .bundle_mapper import BundleMapper
from .lldp_discovery import LLDPDiscovery
from .bridge_domain_mapper import BridgeDomainMapper
from .topology_builder import TopologyBuilder
from .report_generator import ReportGenerator


class NetworkMapper:
    """Main network topology mapper"""
    
    def __init__(self, starting_device: str, output_dir: str = "reports"):
        self.starting_device = starting_device
        self.output_dir = output_dir
        self.dnaas_lookup = DNAASLookup()
        self.topology = TopologyBuilder()
        self.bundle_data = {}
        self.enabled_interfaces = []
        self.visited_devices = set()
        self._discovery = None  # InterfaceDiscovery instance (reused)
        
    def run(self) -> str:
        """Run the full mapping process and return report path"""
        print(f"\n{'='*60}", flush=True)
        print(f"Network Topology Mapper", flush=True)
        print(f"Starting device: {self.starting_device}", flush=True)
        print(f"{'='*60}\n", flush=True)
        
        try:
            # Phase 1: Connect to starting PE
            print("[Phase 1] Connecting to starting PE...", flush=True)
            pe_connector = self._connect_to_pe(self.starting_device)
            pe_hostname = pe_connector.get_hostname()
            self.visited_devices.add(pe_hostname)
            print(f"  Connected to: {pe_hostname}", flush=True)
            
            # Phase 2: Discover interfaces
            print("\n[Phase 2] Discovering interfaces...", flush=True)
            interfaces, bundles = self._discover_interfaces(pe_connector)
            self.bundle_data = bundles
            print(f"  Found {len(interfaces)} physical interfaces", flush=True)
            
            # Phase 3: Enable all physical interfaces (admin-state)
            print("\n[Phase 3] Enabling physical interfaces...", flush=True)
            enabled_count = self._enable_all_interfaces(pe_connector, interfaces)
            print(f"  Enabled {enabled_count} interfaces", flush=True)
            
            # Phase 4: Wait and check which interfaces are operationally UP
            print("\n[Phase 4] Checking interface operational states...", flush=True)
            import time
            print("  Waiting 5s for links to come up...", flush=True)
            time.sleep(5)
            oper_up_interfaces = self._get_oper_up_interfaces(pe_connector)
            print(f"  Found {len(oper_up_interfaces)} operationally UP interfaces", flush=True)
            for iface in oper_up_interfaces[:5]:
                print(f"    - {iface.name}", flush=True)
            if len(oper_up_interfaces) > 5:
                print(f"    ... and {len(oper_up_interfaces) - 5} more", flush=True)
            
            # Phase 5: Configure LLDP only on oper-up interfaces
            print("\n[Phase 5] Configuring LLDP on UP interfaces...", flush=True)
            lldp_count = self._configure_lldp(pe_connector, oper_up_interfaces)
            print(f"  Configured LLDP on {lldp_count} interfaces", flush=True)
            
            # Wait for LLDP to populate
            print("  Waiting 10s for LLDP neighbors to appear...", flush=True)
            time.sleep(10)
            
            # Phase 6: Discover LLDP neighbors
            print("\n[Phase 6] Discovering LLDP neighbors...", flush=True)
            neighbors = self._discover_lldp(pe_connector, pe_hostname)
            print(f"  Found {len(neighbors)} neighbors", flush=True)
            
            # Phase 7: Process each neighbor
            print("\n[Phase 7] Processing neighbors...", flush=True)
            self._process_neighbors(pe_connector, pe_hostname, neighbors)
            
            # Phase 8: Generate report
            print("\n[Phase 8] Generating report...", flush=True)
            report_path = self._generate_report(pe_hostname)
            
            pe_connector.close()
            
            print(f"\n{'='*60}", flush=True)
            print(f"Mapping complete!", flush=True)
            print(f"Report: {report_path}", flush=True)
            print(f"{'='*60}\n", flush=True)
            
            return report_path
            
        except Exception as e:
            print(f"\nError during mapping: {e}", flush=True)
            import traceback
            traceback.print_exc()
            raise
    
    def _connect_to_pe(self, device: str) -> DeviceConnector:
        """Connect to a PE device"""
        return DeviceConnector.connect_pe(device)
    
    def _connect_to_dnaas(self, device_name: str) -> Optional[DeviceConnector]:
        """Connect to a DNAAS device"""
        ip = self.dnaas_lookup.get_device_ip(device_name)
        if not ip:
            print(f"    Warning: Could not find IP for {device_name}", flush=True)
            return None
        
        try:
            return DeviceConnector.connect_dnaas(ip)
        except Exception as e:
            print(f"    Warning: Could not connect to {device_name} ({ip}): {e}", flush=True)
            return None
    
    def _discover_interfaces(self, connector: DeviceConnector) -> tuple:
        """Discover physical interfaces and bundle membership"""
        # Get interfaces via single 'show interfaces' (60-120s on large devices)
        print("  Running 'show interfaces' (may take 60-120s)...", flush=True)
        self._discovery = InterfaceDiscovery(connector)
        physical_ifs = self._discovery.get_physical_interfaces()
        print(f"  Interface query complete.", flush=True)
        
        # Get bundle info
        bundle_mapper = BundleMapper(connector)
        bundle_data = bundle_mapper.parse_bundle_attachments()
        
        # Add bundle info to topology
        for bundle_name, bundle_info in bundle_data.get("bundles", {}).items():
            self.topology.add_bundle_info(
                bundle_name, 
                bundle_info.get("members", []),
                connector.get_hostname()
            )
        
        # Store interface info
        self.enabled_interfaces = []
        for iface in physical_ifs:
            iface_info = {
                "name": iface.name,
                "bundle_id": bundle_data.get("interfaces", {}).get(iface.name)
            }
            self.enabled_interfaces.append(iface_info)
        
        return physical_ifs, bundle_data
    
    def _enable_all_interfaces(self, connector: DeviceConnector, 
                               interfaces: list) -> int:
        """Enable all physical interfaces (admin-state enabled)"""
        # Generate enable config for disabled interfaces
        enable_config = self._discovery.generate_enable_config(interfaces)
        
        if enable_config:
            print(f"  Applying {len(enable_config)} interface enable commands...", flush=True)
            success = connector.execute_config(enable_config)
            if success:
                return len(enable_config)
        else:
            print("  All interfaces already enabled.", flush=True)
        return 0
    
    def _get_oper_up_interfaces(self, connector: DeviceConnector) -> list:
        """Re-query interfaces to find which are now operationally UP"""
        # Must re-query after enabling to get current oper-state
        print("  Re-querying interface states...", flush=True)
        self._discovery.refresh_interface_states()
        
        # Get only oper-up physical interfaces
        return self._discovery.get_operationally_up_interfaces()
    
    def _configure_lldp(self, connector: DeviceConnector, 
                        oper_up_interfaces: list) -> int:
        """Configure LLDP only on operationally UP interfaces (skip existing)"""
        # Generate LLDP config, skipping interfaces already in LLDP
        lldp_config = self._discovery.generate_lldp_config(
            interfaces=oper_up_interfaces,
            skip_existing=True
        )
        
        if lldp_config:
            print(f"  Applying {len(lldp_config)} LLDP configurations...", flush=True)
            success = connector.execute_config(lldp_config)
            if success:
                return len(lldp_config)
        else:
            print("  No new LLDP configurations needed.", flush=True)
        return 0
    
    def _discover_lldp(self, connector: DeviceConnector, 
                       local_hostname: str) -> list:
        """Discover LLDP neighbors"""
        lldp = LLDPDiscovery(connector, local_hostname)
        neighbors = lldp.get_neighbors()
        
        # Add device to topology
        self.topology.add_device(local_hostname, device_type="pe")
        
        # Process neighbors
        for neighbor in neighbors:
            if neighbor.is_snake:
                # Add snake connection
                self.topology.add_snake(
                    local_hostname,
                    neighbor.local_interface,
                    neighbor.remote_interface
                )
                self.topology.add_physical_link(
                    local_hostname, neighbor.local_interface,
                    local_hostname, neighbor.remote_interface,
                    link_type="snake"
                )
            else:
                # Add physical link
                self.topology.add_physical_link(
                    local_hostname, neighbor.local_interface,
                    neighbor.remote_device, neighbor.remote_interface
                )
        
        return neighbors
    
    def _process_neighbors(self, pe_connector: DeviceConnector,
                           pe_hostname: str, neighbors: list) -> None:
        """Process each LLDP neighbor"""
        lldp = LLDPDiscovery(pe_connector, pe_hostname)
        
        for neighbor in neighbors:
            if neighbor.is_snake:
                print(f"  - {neighbor.remote_device}: SNAKE (skipping)", flush=True)
                continue
            
            if lldp.is_dnaas_device(neighbor.remote_device):
                print(f"  - {neighbor.remote_device}: DNAAS device", flush=True)
                self._process_dnaas_neighbor(
                    pe_hostname, 
                    neighbor.local_interface,
                    neighbor.remote_device,
                    neighbor.remote_interface
                )
            else:
                print(f"  - {neighbor.remote_device}: PE device (direct link)", flush=True)
                # Direct PE-to-PE link
                self.topology.add_logical_path(
                    pe_hostname, neighbor.local_interface,
                    neighbor.remote_device, neighbor.remote_interface
                )
    
    def _process_dnaas_neighbor(self, pe_hostname: str, pe_interface: str,
                                 dnaas_name: str, dnaas_interface: str) -> None:
        """Process a DNAAS neighbor - trace BD paths"""
        if dnaas_name in self.visited_devices:
            return
        
        # Connect to DNAAS
        dnaas_connector = self._connect_to_dnaas(dnaas_name)
        if not dnaas_connector:
            return
        
        self.visited_devices.add(dnaas_name)
        self.topology.add_device(
            dnaas_name, 
            device_type=self.dnaas_lookup.get_device_type(dnaas_name)
        )
        
        try:
            # Get LLDP from DNAAS perspective
            dnaas_lldp = LLDPDiscovery(dnaas_connector, dnaas_name)
            dnaas_neighbors = dnaas_lldp.get_neighbors()
            
            # Get bridge domain info
            bd_mapper = BridgeDomainMapper(dnaas_connector)
            
            # Find the interface facing the PE
            pe_facing_interface = dnaas_interface
            
            # Get bridge domains this interface belongs to
            bd_trace = bd_mapper.trace_path_from_interface(pe_facing_interface)
            
            if bd_trace.get("bridge_domain"):
                print(f"    BD: {bd_trace['bridge_domain']}", flush=True)
                
                # Check where other attachments lead
                for attachment in bd_trace.get("other_attachments", []):
                    # Check LLDP for this attachment (or parent interface)
                    attachment_base = attachment.split('.')[0]
                    
                    for dnaas_neighbor in dnaas_neighbors:
                        if (dnaas_neighbor.local_interface == attachment or
                            dnaas_neighbor.local_interface == attachment_base):
                            
                            remote_dev = dnaas_neighbor.remote_device
                            
                            if dnaas_lldp.is_dnaas_device(remote_dev):
                                # Leads to another DNAAS - continue tracing
                                print(f"    -> {remote_dev} (DNAAS)", flush=True)
                                self._trace_through_dnaas(
                                    pe_hostname, pe_interface,
                                    [dnaas_name, remote_dev],
                                    dnaas_neighbor
                                )
                            else:
                                # Leads to a PE - we found an endpoint!
                                print(f"    -> {remote_dev} (PE endpoint)", flush=True)
                                self._add_logical_path(
                                    pe_hostname, pe_interface,
                                    remote_dev, dnaas_neighbor.remote_interface,
                                    [dnaas_name]
                                )
            
        except Exception as e:
            print(f"    Warning: Error processing {dnaas_name}: {e}", flush=True)
        finally:
            dnaas_connector.close()
    
    def _trace_through_dnaas(self, source_pe: str, source_if: str,
                              via_devices: list, current_neighbor) -> None:
        """Continue tracing through DNAAS core"""
        # Limit depth to prevent infinite loops
        if len(via_devices) > 5:
            print(f"    (max depth reached)", flush=True)
            return
        
        next_dnaas = current_neighbor.remote_device
        
        if next_dnaas in self.visited_devices:
            return
        
        dnaas_connector = self._connect_to_dnaas(next_dnaas)
        if not dnaas_connector:
            return
        
        self.visited_devices.add(next_dnaas)
        self.topology.add_device(
            next_dnaas,
            device_type=self.dnaas_lookup.get_device_type(next_dnaas)
        )
        
        try:
            lldp = LLDPDiscovery(dnaas_connector, next_dnaas)
            neighbors = lldp.get_neighbors()
            bd_mapper = BridgeDomainMapper(dnaas_connector)
            
            # Find BD for the incoming interface
            incoming_if = current_neighbor.remote_interface
            bd_trace = bd_mapper.trace_path_from_interface(incoming_if)
            
            if bd_trace.get("bridge_domain"):
                for attachment in bd_trace.get("other_attachments", []):
                    attachment_base = attachment.split('.')[0]
                    
                    for neighbor in neighbors:
                        if (neighbor.local_interface == attachment or
                            neighbor.local_interface == attachment_base):
                            
                            remote_dev = neighbor.remote_device
                            
                            if lldp.is_dnaas_device(remote_dev):
                                # Continue through DNAAS
                                new_via = via_devices + [remote_dev]
                                self._trace_through_dnaas(
                                    source_pe, source_if,
                                    new_via, neighbor
                                )
                            else:
                                # Found PE endpoint
                                print(f"    -> {remote_dev} (PE endpoint)", flush=True)
                                self._add_logical_path(
                                    source_pe, source_if,
                                    remote_dev, neighbor.remote_interface,
                                    via_devices
                                )
        finally:
            dnaas_connector.close()
    
    def _add_logical_path(self, source_pe: str, source_if: str,
                          dest_pe: str, dest_if: str, via: list) -> None:
        """Add a logical path with bundle info"""
        # Get bundle members for source
        source_bundle = None
        if source_if.startswith("bundle-"):
            source_bundle = self.topology.get_bundle_members(
                source_if.split('.')[0], source_pe
            )
        
        # We don't have bundle info for destination yet
        # (would need to connect to that PE)
        
        self.topology.add_logical_path(
            source_pe, source_if,
            dest_pe, dest_if,
            via_devices=via,
            source_bundle=source_bundle
        )
    
    def _generate_report(self, pe_hostname: str) -> str:
        """Generate the topology report"""
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Generate report
        report = ReportGenerator(self.topology, self.bundle_data)
        report.set_starting_device(pe_hostname)
        report.set_enabled_interfaces(self.enabled_interfaces)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"network_map_{pe_hostname}_{timestamp}.txt"
        filepath = os.path.join(self.output_dir, filename)
        
        report.write_report(filepath)
        
        # Also print summary
        summary = self.topology.get_summary()
        print(f"\n  Summary:", flush=True)
        print(f"    Devices:      {summary['devices']}", flush=True)
        print(f"    Physical:     {summary['physical_links']} links", flush=True)
        print(f"    Logical:      {summary['logical_paths']} paths", flush=True)
        print(f"    Snakes:       {summary['snake_connections']}", flush=True)
        print(f"    Bundles:      {summary['bundles']}", flush=True)
        
        return filepath


def main(starting_device: str = None, output_dir: str = "reports") -> None:
    """Main entry point"""
    if starting_device is None:
        parser = argparse.ArgumentParser(
            description="Network Topology Mapper",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
    python -m network_mapper.mapper PE-1
    python -m network_mapper.mapper 10.0.0.1 -o /tmp/reports
            """
        )
        parser.add_argument(
            "device",
            help="Starting PE device (hostname or IP)"
        )
        parser.add_argument(
            "-o", "--output",
            default="reports",
            help="Output directory for reports (default: reports)"
        )
        
        args = parser.parse_args()
        starting_device = args.device
        output_dir = args.output
    
    mapper = NetworkMapper(starting_device, output_dir)
    mapper.run()


if __name__ == "__main__":
    main()

