#!/usr/bin/env python3
"""
Prerequisite Checker - Multi-device prerequisite verification

This module checks prerequisites for test cases across multiple devices,
identifying gaps and missing configurations before test execution.
"""

import re
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

from .device_manager import DeviceManager, SSHConnection
from .test_cases import TestCase

logger = logging.getLogger(__name__)


class PrerequisiteStatus(Enum):
    """Status of a prerequisite check"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


@dataclass
class PrerequisiteCheck:
    """Result of a prerequisite check"""
    prerequisite: str
    device: str
    status: PrerequisiteStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DevicePrerequisites:
    """Prerequisites status for a device"""
    device: str
    checks: List[PrerequisiteCheck]
    all_passed: bool = False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of prerequisite checks"""
        passed = sum(1 for c in self.checks if c.status == PrerequisiteStatus.PASS)
        failed = sum(1 for c in self.checks if c.status == PrerequisiteStatus.FAIL)
        warnings = sum(1 for c in self.checks if c.status == PrerequisiteStatus.WARNING)
        
        return {
            "device": self.device,
            "total": len(self.checks),
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "all_passed": self.all_passed,
        }


class PrerequisiteChecker:
    """Checks prerequisites across multiple devices"""
    
    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager
        self.checks_cache: Dict[str, Dict[str, Any]] = {}
    
    def check_prerequisites(
        self,
        test_cases: List[TestCase],
        devices: Optional[List[str]] = None
    ) -> Dict[str, DevicePrerequisites]:
        """
        Check prerequisites for test cases across devices
        
        Args:
            test_cases: List of test cases to check prerequisites for
            devices: Optional list of device hostnames. If None, checks all devices
        
        Returns:
            Dictionary mapping device hostname to DevicePrerequisites
        """
        # Collect all unique prerequisites from test cases
        all_prerequisites = set()
        for test_case in test_cases:
            all_prerequisites.update(test_case.prerequisites)
        
        if not all_prerequisites:
            logger.warning("No prerequisites found in test cases")
            return {}
        
        # Filter out Spirent/external tool prerequisites (only check DUT-side)
        dut_prerequisites = []
        for prereq in all_prerequisites:
            prereq_lower = prereq.lower()
            # Skip Spirent, traffic generator, and external tool prerequisites
            if any(keyword in prereq_lower for keyword in ["spirent", "traffic gen", "trafficgen", "external tool"]):
                logger.debug(f"Skipping external tool prerequisite: {prereq}")
                continue
            dut_prerequisites.append(prereq)
        
        if not dut_prerequisites:
            logger.warning("No DUT-side prerequisites found after filtering")
            return {}
        
        # Get devices to check (only network devices, not Spirent)
        if devices is None:
            devices = list(self.device_manager.devices.keys())
        
        # Filter out Spirent devices
        network_devices = []
        for device_hostname in devices:
            device_info = self.device_manager.get_device(device_hostname)
            if device_info:
                description = (device_info.get("description") or "").lower()
                hostname_lower = device_hostname.lower()
                # Skip Spirent/traffic generator devices
                if any(keyword in description or keyword in hostname_lower 
                       for keyword in ["spirent", "traffic gen", "trafficgen"]):
                    logger.debug(f"Skipping external tool device: {device_hostname}")
                    continue
            network_devices.append(device_hostname)
        
        if not network_devices:
            logger.warning("No network devices found after filtering")
            return {}
        
        results = {}
        
        for device_hostname in network_devices:
            device_checks = []
            
            for prereq in dut_prerequisites:
                check_result = self._check_single_prerequisite(device_hostname, prereq)
                if check_result:
                    device_checks.append(check_result)
            
            all_passed = all(
                c.status == PrerequisiteStatus.PASS for c in device_checks
            )
            
            results[device_hostname] = DevicePrerequisites(
                device=device_hostname,
                checks=device_checks,
                all_passed=all_passed
            )
        
        return results
    
    def _check_single_prerequisite(
        self,
        device_hostname: str,
        prerequisite: str
    ) -> Optional[PrerequisiteCheck]:
        """
        Check a single prerequisite on a device
        
        Args:
            device_hostname: Device to check
            prerequisite: Prerequisite description
        
        Returns:
            PrerequisiteCheck result
        """
        conn = self.device_manager.get_connection(device_hostname)
        if not conn:
            return PrerequisiteCheck(
                prerequisite=prerequisite,
                device=device_hostname,
                status=PrerequisiteStatus.FAIL,
                message=f"Cannot connect to device {device_hostname}",
            )
        
        # Parse prerequisite to determine what to check
        prereq_lower = prerequisite.lower()
        
        # BGP FlowSpec-VPN session (check for both SAFI 133 and 134)
        if "bgp" in prereq_lower and ("flowspec" in prereq_lower or "vpn" in prereq_lower):
            return self._check_bgp_flowspec_vpn(conn, device_hostname, prerequisite)
        
        # BGP FlowSpec (SAFI 133 - default VRF)
        if "bgp" in prereq_lower and "flowspec" in prereq_lower and "vpn" not in prereq_lower:
            return self._check_bgp_flowspec(conn, device_hostname, prerequisite)
        
        # VRF configuration (smart matching - any VRF with FlowSpec config)
        if "vrf" in prereq_lower:
            return self._check_vrf_config(conn, device_hostname, prerequisite)
        
        # Route Target configuration
        if "route target" in prereq_lower or "rt" in prereq_lower:
            return self._check_route_target(conn, device_hostname, prerequisite)
        
        # Interface configuration
        if "interface" in prereq_lower:
            return self._check_interface_config(conn, device_hostname, prerequisite)
        
        # BGP neighbor
        if "neighbor" in prereq_lower or "peer" in prereq_lower:
            return self._check_bgp_neighbor(conn, device_hostname, prerequisite)
        
        # Default: Generic check (try to find keyword in config)
        return self._check_generic(conn, device_hostname, prerequisite)
    
    def _check_bgp_flowspec_vpn(
        self,
        conn: SSHConnection,
        device: str,
        prerequisite: str
    ) -> PrerequisiteCheck:
        """
        Check BGP FlowSpec-VPN configuration:
        - Global: SAFI 134 (FlowSpec-VPN) and SAFI 128 (VPNv4) should be established
        - VRF: SAFI 133 (FlowSpec) should be established
        """
        checks = {
            "global_134": False,  # FlowSpec-VPN (global)
            "global_128": False,  # VPNv4 (global)
            "vrf_133": False      # FlowSpec (VRF)
        }
        details = {}
        
        # Check Global: SAFI 134 (FlowSpec-VPN)
        cmd_134 = "show bgp ipv4 flowspec-vpn summary"
        success_134, output_134 = conn.run_cli_command(cmd_134)
        if success_134 and "Established" in output_134:
            checks["global_134"] = True
            details["global_134_count"] = output_134.count("Established")
        else:
            details["global_134_output"] = output_134[:300] if success_134 else "Command failed"
        
        # Check Global: SAFI 128 (VPNv4)
        cmd_128 = "show bgp ipv4 vpn summary"
        success_128, output_128 = conn.run_cli_command(cmd_128)
        if success_128 and "Established" in output_128:
            checks["global_128"] = True
            details["global_128_count"] = output_128.count("Established")
        else:
            details["global_128_output"] = output_128[:300] if success_128 else "Command failed"
        
        # Check VRF: SAFI 133 (FlowSpec) - need to check within VRF context
        # Try to find VRFs and check flowspec within each
        cmd_vrf_list = "show vrf"
        success_vrf, vrf_output = conn.run_cli_command(cmd_vrf_list)
        vrf_names = []
        if success_vrf:
            # Extract VRF names from output
            import re
            vrf_matches = re.findall(r'vrf\s+(\S+)', vrf_output, re.IGNORECASE)
            vrf_names = list(set(vrf_matches))
        
        # Check SAFI 133 in each VRF (or default VRF if no VRFs found)
        if vrf_names:
            for vrf in vrf_names[:5]:  # Check first 5 VRFs
                cmd_133_vrf = f"show bgp ipv4 flowspec vrf {vrf} summary"
                success_133_vrf, output_133_vrf = conn.run_cli_command(cmd_133_vrf)
                if success_133_vrf and "Established" in output_133_vrf:
                    checks["vrf_133"] = True
                    details["vrf_133_vrf"] = vrf
                    details["vrf_133_count"] = output_133_vrf.count("Established")
                    break
        else:
            # Check default VRF (no VRF specified)
            cmd_133 = "show bgp ipv4 flowspec summary"
            success_133, output_133 = conn.run_cli_command(cmd_133)
            if success_133 and "Established" in output_133:
                checks["vrf_133"] = True
                details["vrf_133_count"] = output_133.count("Established")
                details["vrf_133_note"] = "Default VRF"
            else:
                details["vrf_133_output"] = output_133[:300] if success_133 else "Command failed"
        
        # Evaluate results
        all_required = checks["global_134"] and checks["global_128"] and checks["vrf_133"]
        
        if all_required:
            return PrerequisiteCheck(
                prerequisite=prerequisite,
                device=device,
                status=PrerequisiteStatus.PASS,
                message=f"BGP FlowSpec-VPN properly configured: Global SAFI 134 ({details.get('global_134_count', 0)}), Global SAFI 128 ({details.get('global_128_count', 0)}), VRF SAFI 133 ({details.get('vrf_133_count', 0)})",
                details=details
            )
        
        # Partial success - report what's missing
        missing = []
        if not checks["global_134"]:
            missing.append("Global SAFI 134 (FlowSpec-VPN)")
        if not checks["global_128"]:
            missing.append("Global SAFI 128 (VPNv4)")
        if not checks["vrf_133"]:
            missing.append("VRF SAFI 133 (FlowSpec)")
        
        return PrerequisiteCheck(
            prerequisite=prerequisite,
            device=device,
            status=PrerequisiteStatus.FAIL,
            message=f"Missing BGP sessions: {', '.join(missing)}",
            details=details
        )
    
    def _check_bgp_flowspec(
        self,
        conn: SSHConnection,
        device: str,
        prerequisite: str
    ) -> PrerequisiteCheck:
        """Check BGP FlowSpec session (SAFI 133 - default VRF)"""
        cmd = "show bgp ipv4 flowspec summary"
        success, output = conn.run_cli_command(cmd)
        
        if not success:
            return PrerequisiteCheck(
                prerequisite=prerequisite,
                device=device,
                status=PrerequisiteStatus.FAIL,
                message="Cannot execute BGP FlowSpec command",
                details={"command": cmd, "error": output}
            )
        
        if "Established" in output:
            established_count = output.count("Established")
            return PrerequisiteCheck(
                prerequisite=prerequisite,
                device=device,
                status=PrerequisiteStatus.PASS,
                message=f"BGP FlowSpec (SAFI 133) session Established ({established_count} neighbor(s))",
                details={"established_count": established_count, "safi": "133"}
            )
        else:
            return PrerequisiteCheck(
                prerequisite=prerequisite,
                device=device,
                status=PrerequisiteStatus.FAIL,
                message="BGP FlowSpec (SAFI 133) session not Established",
                details={"output": output[:500]}
            )
    
    def _check_vrf_config(
        self,
        conn: SSHConnection,
        device: str,
        prerequisite: str
    ) -> PrerequisiteCheck:
        """
        Check VRF configuration - Smart matching
        
        IGNORES the VRF name mentioned in prerequisite - it's just an example.
        Checks if ANY VRF has the required configuration:
        - import-vpn configured
        - route-target configured
        - FlowSpec-related configuration
        - Interfaces with flowspec enabled
        """
        # Extract what configuration is needed (e.g., "import-vpn", "route-target")
        # IGNORE the VRF name - it's just an example
        prereq_lower = prerequisite.lower()
        needs_import_vpn = "import-vpn" in prereq_lower or ("import" in prereq_lower and "vpn" in prereq_lower)
        needs_route_target = "route-target" in prereq_lower or ("route" in prereq_lower and "target" in prereq_lower)
        needs_flowspec = "flowspec" in prereq_lower
        
        # Check all VRFs
        cmd = "show network-services vrf"
        success, output = conn.run_cli_command(cmd)
        
        if not success:
            return PrerequisiteCheck(
                prerequisite=prerequisite,
                device=device,
                status=PrerequisiteStatus.WARNING,
                message="Cannot check VRF configuration",
                details={"command": cmd, "error": output}
            )
        
        # Check for any VRF with FlowSpec-related config
        # Look for: import-vpn, route-target, flowspec, etc.
        flowspec_keywords = ["import-vpn", "route-target", "flowspec", "vpn", "import", "export"]
        vrf_lines = output.split('\n')
        
        matching_vrfs = []
        current_vrf = None
        vrf_context = {}  # Track VRF context and their config
        
        for line in vrf_lines:
            line_lower = line.lower()
            # Detect VRF name (multiple patterns)
            vrf_line_match = re.search(r'vrf\s+(\S+)', line, re.IGNORECASE)
            if vrf_line_match:
                current_vrf = vrf_line_match.group(1)
                if current_vrf not in vrf_context:
                    vrf_context[current_vrf] = {"has_flowspec": False, "has_import": False, "has_rt": False}
            
            # Check if current VRF has FlowSpec-related config
            if current_vrf:
                if any(keyword in line_lower for keyword in flowspec_keywords):
                    vrf_context[current_vrf]["has_flowspec"] = True
                    if "import" in line_lower or "import-vpn" in line_lower:
                        vrf_context[current_vrf]["has_import"] = True
                    if "route-target" in line_lower or "rt" in line_lower:
                        vrf_context[current_vrf]["has_rt"] = True
        
        # Collect VRFs with FlowSpec config
        for vrf_name, config in vrf_context.items():
            if config["has_flowspec"] or config["has_import"] or config["has_rt"]:
                matching_vrfs.append(vrf_name)
        
        # Also check interfaces for flowspec enabled
        iface_cmd = "show running-config interfaces | include 'interface\\|flowspec enabled'"
        iface_success, iface_output = conn.run_cli_command(iface_cmd)
        
        flowspec_interfaces = []
        if iface_success:
            lines = iface_output.split('\n')
            current_iface = None
            for line in lines:
                iface_match = re.match(r'(?:interface\s+)?(\S+)\s*$', line.strip())
                if iface_match and 'flowspec' not in line.lower():
                    potential_iface = iface_match.group(1)
                    if re.match(r'(ge|xe|ce|et|bundle|irb)\d', potential_iface):
                        current_iface = potential_iface
                elif 'flowspec enabled' in line.lower() and current_iface:
                    flowspec_interfaces.append(current_iface)
                    current_iface = None
        
        # Check what configuration is actually needed (ignore VRF name)
        # Look for VRFs that match the required config
        vrfs_with_required_config = []
        
        # Check each VRF for the required configuration
        for vrf_name, config in vrf_context.items():
            matches_requirement = False
            
            if needs_import_vpn:
                # Need import-vpn - check if VRF has it
                if config["has_import"] or "import-vpn" in output.lower():
                    # Check this specific VRF section
                    vrf_section_start = output.find(f"vrf {vrf_name}")
                    if vrf_section_start >= 0:
                        vrf_section = output[vrf_section_start:vrf_section_start+500]
                        if "import-vpn" in vrf_section.lower() or "import" in vrf_section.lower():
                            matches_requirement = True
            
            if needs_route_target:
                # Need route-target - check if VRF has it
                if config["has_rt"]:
                    matches_requirement = True
            
            if needs_flowspec:
                # Need FlowSpec - check if VRF has FlowSpec config
                if config["has_flowspec"]:
                    matches_requirement = True
            
            # If no specific requirement, any VRF with VPN config works
            if not needs_import_vpn and not needs_route_target and not needs_flowspec:
                if config["has_flowspec"] or config["has_import"] or config["has_rt"]:
                    matches_requirement = True
            
            if matches_requirement:
                vrfs_with_required_config.append(vrf_name)
        
        # Build config description for messages
        config_details = []
        if needs_import_vpn:
            config_details.append("import-vpn")
        if needs_route_target:
            config_details.append("route-target")
        if needs_flowspec:
            config_details.append("flowspec")
        config_desc = "/".join(config_details) if config_details else "FlowSpec/VPN"
        
        # Smart evaluation - check if requirements are met (IGNORE VRF name)
        if vrfs_with_required_config:
            # Found VRF(s) with required configuration - PASS
            return PrerequisiteCheck(
                prerequisite=prerequisite,
                device=device,
                status=PrerequisiteStatus.PASS,
                message=f"VRF(s) with {config_desc} config found: {', '.join(vrfs_with_required_config)}",
                details={"matching_vrfs": vrfs_with_required_config, "flowspec_interfaces": flowspec_interfaces, "config_required": config_details}
            )
        elif flowspec_interfaces:
            # Has flowspec-enabled interfaces (SAFI 133 - default VRF) - PASS
            return PrerequisiteCheck(
                prerequisite=prerequisite,
                device=device,
                status=PrerequisiteStatus.PASS,
                message=f"FlowSpec enabled on interfaces (default VRF): {', '.join(flowspec_interfaces[:3])}",
                details={"flowspec_interfaces": flowspec_interfaces, "note": "Using default VRF - no specific VRF name required"}
            )
        elif matching_vrfs:
            # Found VRFs with some FlowSpec config (might work)
            return PrerequisiteCheck(
                prerequisite=prerequisite,
                device=device,
                status=PrerequisiteStatus.PASS,
                message=f"VRF(s) with FlowSpec-related config found: {', '.join(matching_vrfs)}",
                details={"matching_vrfs": matching_vrfs, "note": "VRF name in prerequisite is just an example"}
            )
        else:
            # Check if ANY VRF exists (might work if configured)
            all_vrfs = list(vrf_context.keys())
            if all_vrfs:
                return PrerequisiteCheck(
                    prerequisite=prerequisite,
                    device=device,
                    status=PrerequisiteStatus.WARNING,
                    message=f"VRF(s) exist but may need {config_desc} config: {', '.join(all_vrfs[:3])}",
                    details={"found_vrfs": all_vrfs, "note": "VRF name in prerequisite is just an example - any VRF with proper config works"}
                )
            else:
                return PrerequisiteCheck(
                    prerequisite=prerequisite,
                    device=device,
                    status=PrerequisiteStatus.FAIL,
                    message=f"No VRF with required configuration found (need: {config_desc} config)",
                    details={"note": "VRF name in prerequisite is just an example - checking for ANY VRF with proper config"}
                )
    
    def _check_route_target(
        self,
        conn: SSHConnection,
        device: str,
        prerequisite: str
    ) -> PrerequisiteCheck:
        """Check Route Target configuration"""
        # Try to extract RT from prerequisite
        rt_match = re.search(r'rt[:\s]+(\S+)', prerequisite, re.IGNORECASE)
        rt_value = rt_match.group(1) if rt_match else None
        
        # Check in VRF config
        cmd = "show network-services vrf"
        success, output = conn.run_cli_command(cmd)
        
        if not success:
            return PrerequisiteCheck(
                prerequisite=prerequisite,
                device=device,
                status=PrerequisiteStatus.WARNING,
                message="Cannot check Route Target configuration",
                details={"command": cmd, "error": output}
            )
        
        if rt_value:
            if rt_value in output:
                return PrerequisiteCheck(
                    prerequisite=prerequisite,
                    device=device,
                    status=PrerequisiteStatus.PASS,
                    message=f"Route Target {rt_value} configured",
                    details={"rt": rt_value}
                )
            else:
                return PrerequisiteCheck(
                    prerequisite=prerequisite,
                    device=device,
                    status=PrerequisiteStatus.FAIL,
                    message=f"Route Target {rt_value} not found",
                    details={"rt": rt_value}
                )
        else:
            # Generic RT check
            rt_count = output.count("route-target") if "route-target" in output.lower() else 0
            if rt_count > 0:
                return PrerequisiteCheck(
                    prerequisite=prerequisite,
                    device=device,
                    status=PrerequisiteStatus.PASS,
                    message=f"Route Target configuration present ({rt_count} RT(s) found)",
                    details={"rt_count": rt_count}
                )
            else:
                return PrerequisiteCheck(
                    prerequisite=prerequisite,
                    device=device,
                    status=PrerequisiteStatus.WARNING,
                    message="No Route Target configuration found",
                    details={"output": output[:500]}
                )
    
    def _check_interface_config(
        self,
        conn: SSHConnection,
        device: str,
        prerequisite: str
    ) -> PrerequisiteCheck:
        """Check interface configuration"""
        # Try to extract interface name
        iface_match = re.search(r'interface[:\s]+(\S+)', prerequisite, re.IGNORECASE)
        iface_name = iface_match.group(1) if iface_match else None
        
        if iface_name:
            cmd = f"show interfaces {iface_name}"
        else:
            cmd = "show interfaces"
        
        success, output = conn.run_cli_command(cmd)
        
        if not success:
            return PrerequisiteCheck(
                prerequisite=prerequisite,
                device=device,
                status=PrerequisiteStatus.WARNING,
                message="Cannot check interface configuration",
                details={"command": cmd, "error": output}
            )
        
        if iface_name:
            if iface_name in output:
                return PrerequisiteCheck(
                    prerequisite=prerequisite,
                    device=device,
                    status=PrerequisiteStatus.PASS,
                    message=f"Interface {iface_name} configured",
                    details={"interface": iface_name}
                )
            else:
                return PrerequisiteCheck(
                    prerequisite=prerequisite,
                    device=device,
                    status=PrerequisiteStatus.FAIL,
                    message=f"Interface {iface_name} not found",
                    details={"interface": iface_name}
                )
        else:
            # Generic interface check
            return PrerequisiteCheck(
                prerequisite=prerequisite,
                device=device,
                status=PrerequisiteStatus.WARNING,
                message="Interface check requires specific interface name",
                details={}
            )
    
    def _check_bgp_neighbor(
        self,
        conn: SSHConnection,
        device: str,
        prerequisite: str
    ) -> PrerequisiteCheck:
        """Check BGP neighbor configuration"""
        # Try to extract neighbor IP
        neighbor_match = re.search(r'neighbor[:\s]+(\S+)', prerequisite, re.IGNORECASE)
        neighbor_ip = neighbor_match.group(1) if neighbor_match else None
        
        cmd = "show bgp ipv4 flowspec-vpn neighbors"
        success, output = conn.run_cli_command(cmd)
        
        if not success:
            return PrerequisiteCheck(
                prerequisite=prerequisite,
                device=device,
                status=PrerequisiteStatus.WARNING,
                message="Cannot check BGP neighbor",
                details={"command": cmd, "error": output}
            )
        
        if neighbor_ip:
            if neighbor_ip in output:
                # Check if Established
                neighbor_section = output[output.find(neighbor_ip):output.find(neighbor_ip)+500]
                if "Established" in neighbor_section:
                    return PrerequisiteCheck(
                        prerequisite=prerequisite,
                        device=device,
                        status=PrerequisiteStatus.PASS,
                        message=f"BGP neighbor {neighbor_ip} Established",
                        details={"neighbor": neighbor_ip}
                    )
                else:
                    return PrerequisiteCheck(
                        prerequisite=prerequisite,
                        device=device,
                        status=PrerequisiteStatus.FAIL,
                        message=f"BGP neighbor {neighbor_ip} not Established",
                        details={"neighbor": neighbor_ip, "output": neighbor_section}
                    )
            else:
                return PrerequisiteCheck(
                    prerequisite=prerequisite,
                    device=device,
                    status=PrerequisiteStatus.FAIL,
                    message=f"BGP neighbor {neighbor_ip} not found",
                    details={"neighbor": neighbor_ip}
                )
        else:
            # Generic neighbor check
            neighbor_count = output.count("Neighbor") if "Neighbor" in output else 0
            if neighbor_count > 0:
                return PrerequisiteCheck(
                    prerequisite=prerequisite,
                    device=device,
                    status=PrerequisiteStatus.PASS,
                    message=f"BGP neighbors configured ({neighbor_count} neighbor(s))",
                    details={"neighbor_count": neighbor_count}
                )
            else:
                return PrerequisiteCheck(
                    prerequisite=prerequisite,
                    device=device,
                    status=PrerequisiteStatus.WARNING,
                    message="No BGP neighbors found",
                    details={"output": output[:500]}
                )
    
    def _check_generic(
        self,
        conn: SSHConnection,
        device: str,
        prerequisite: str
    ) -> PrerequisiteCheck:
        """Generic prerequisite check - search in running config"""
        cmd = "show running-config"
        success, output = conn.run_cli_command(cmd)
        
        if not success:
            return PrerequisiteCheck(
                prerequisite=prerequisite,
                device=device,
                status=PrerequisiteStatus.WARNING,
                message="Cannot check prerequisite (cannot read config)",
                details={"command": cmd, "error": output}
            )
        
        # Search for keywords from prerequisite
        keywords = prerequisite.lower().split()
        found_keywords = [kw for kw in keywords if kw in output.lower()]
        
        if found_keywords:
            return PrerequisiteCheck(
                prerequisite=prerequisite,
                device=device,
                status=PrerequisiteStatus.PASS,
                message=f"Prerequisite keywords found in config: {', '.join(found_keywords)}",
                details={"found_keywords": found_keywords}
            )
        else:
            return PrerequisiteCheck(
                prerequisite=prerequisite,
                device=device,
                status=PrerequisiteStatus.WARNING,
                message="Prerequisite keywords not found in config",
                details={"keywords": keywords}
            )
    
    def get_gaps_summary(
        self,
        results: Dict[str, DevicePrerequisites]
    ) -> Dict[str, Any]:
        """
        Get summary of prerequisite gaps across devices
        
        Args:
            results: Dictionary of device prerequisite check results
        
        Returns:
            Summary dictionary with gaps identified
        """
        gaps = {
            "devices_checked": len(results),
            "devices_all_passed": sum(1 for r in results.values() if r.all_passed),
            "devices_with_gaps": sum(1 for r in results.values() if not r.all_passed),
            "failed_checks": [],
            "warnings": [],
        }
        
        for device, device_prereqs in results.items():
            for check in device_prereqs.checks:
                if check.status == PrerequisiteStatus.FAIL:
                    gaps["failed_checks"].append({
                        "device": device,
                        "prerequisite": check.prerequisite,
                        "message": check.message,
                    })
                elif check.status == PrerequisiteStatus.WARNING:
                    gaps["warnings"].append({
                        "device": device,
                        "prerequisite": check.prerequisite,
                        "message": check.message,
                    })
        
        return gaps
