#!/usr/bin/env python3
"""
FlowSpec VPN Monitor - Comprehensive Diagnostic & Bug Detection Tool
======================================================================

This script monitors and diagnoses FlowSpec VPN rule installation across
the complete flow: BGP → Zebra → FPM → wb_agent → TCAM

Features:
- Visual flow chart per device showing rule installation path
- ✓/✗ status indicators with expected vs actual comparison
- Traces from NCC (routing) and NCP (datapath) containers
- vtysh, CLI, and DP show commands
- Daemon mode for continuous monitoring
- Baseline comparison for before/after testing

Usage:
    Wizard mode:      python3 flowspec_vpn_monitor.py wizard
    Analyze device:   python3 flowspec_vpn_monitor.py analyze <device>
    Monitor daemon:   python3 flowspec_vpn_monitor.py start
    Stop daemon:      python3 flowspec_vpn_monitor.py stop
    Show status:      python3 flowspec_vpn_monitor.py status
    Save baseline:    python3 flowspec_vpn_monitor.py baseline
    Compare:          python3 flowspec_vpn_monitor.py compare

Author: FlowSpec VPN Diagnostic Tool
Version: 1.0.0
"""

import os
import sys
import json
import time
import signal
import subprocess
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

# Try to import rich for beautiful output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.tree import Tree
    from rich.live import Live
    from rich.columns import Columns
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: rich library not installed. Install with: pip install rich")

# Configuration
MONITOR_DIR = Path("/home/dn/SCALER/FLOWSPEC_VPN/monitor_data")
PID_FILE = MONITOR_DIR / "daemon.pid"
LOG_FILE = MONITOR_DIR / "monitor.log"
BASELINE_FILE = MONITOR_DIR / "baseline.json"
LATEST_FILE = MONITOR_DIR / "latest.json"
SNAPSHOTS_DIR = MONITOR_DIR / "snapshots"
INTERVAL_SECONDS = 120  # 2 minutes

# Ensure directories exist
MONITOR_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOTS_DIR.mkdir(exist_ok=True)

# Initialize console
console = Console() if RICH_AVAILABLE else None


class CheckStatus(Enum):
    """Status for each check point"""
    PASS = "✓"
    FAIL = "✗"
    WARN = "⚠"
    SKIP = "○"
    UNKNOWN = "?"


@dataclass
class FlowCheckResult:
    """Result of a single flow check"""
    step: str
    component: str
    check_name: str
    status: CheckStatus
    expected: str
    actual: str
    command: str
    details: str = ""
    raw_output: str = ""


@dataclass
class FlowSpecRule:
    """Represents a FlowSpec rule through the system"""
    nlri: str
    vrf_name: str = ""
    vrf_id: int = 0
    rd: str = ""
    rt: str = ""
    action: str = ""
    # Control plane
    bgp_received: bool = False
    bgp_imported_to_vrf: bool = False
    zebra_installed: bool = False
    fpm_sent: bool = False
    # Data plane
    dp_received: bool = False
    dp_supported: bool = False
    dp_installed: bool = False
    tcam_written: bool = False
    # Counters
    match_packets: int = 0
    match_bytes: int = 0
    # Errors
    errors: List[str] = field(default_factory=list)


@dataclass
class DeviceAnalysis:
    """Complete analysis results for a device"""
    hostname: str
    ip: str
    timestamp: str
    dnos_version: str = ""
    # Flow checks
    checks: List[FlowCheckResult] = field(default_factory=list)
    # Rules found
    rules: List[FlowSpecRule] = field(default_factory=list)
    # Summaries
    total_rules: int = 0
    rules_installed: int = 0
    rules_failed: int = 0
    tcam_errors: int = 0
    hw_write_failures: int = 0
    vrf_count: int = 0
    # Problems detected
    problems: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class SSHConnection:
    """SSH connection to a device"""
    
    def __init__(self, hostname: str, ip: str, username: str = "dnroot", password: str = "dnroot"):
        self.hostname = hostname
        self.ip = ip
        self.username = username
        self.password = password
        self._connected = False
    
    def run_cli_command(self, command: str, timeout: int = 30) -> Tuple[bool, str]:
        """Run a DNOS CLI command"""
        try:
            import pexpect
            ssh_cmd = f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {self.username}@{self.ip}"
            child = pexpect.spawn(ssh_cmd, timeout=timeout)
            
            i = child.expect(['password:', 'Password:', pexpect.TIMEOUT, pexpect.EOF], timeout=10)
            if i in [0, 1]:
                child.sendline(self.password)
            
            child.expect(['#', '>'], timeout=10)
            child.sendline(command)
            child.expect(['#', '>'], timeout=timeout)
            
            output = child.before.decode('utf-8', errors='replace')
            child.sendline('exit')
            child.close()
            
            return True, output
            
        except Exception as e:
            return False, str(e)
    
    def run_shell_command(self, command: str, container: str = None, timeout: int = 30) -> Tuple[bool, str]:
        """Run a shell command, optionally in a container"""
        try:
            if container:
                # Run command inside container
                full_cmd = f"run start shell -c '{container}' command '{command}'"
            else:
                full_cmd = f"run start shell command '{command}'"
            
            return self.run_cli_command(full_cmd, timeout)
            
        except Exception as e:
            return False, str(e)
    
    def run_xraycli(self, path: str, ncp_id: int = 0, timeout: int = 30) -> Tuple[bool, str]:
        """Run xraycli command on NCP"""
        cmd = f"xraycli {path}"
        return self.run_shell_command(cmd, container=f"ncp{ncp_id}", timeout=timeout)
    
    def run_vtysh(self, command: str, timeout: int = 30) -> Tuple[bool, str]:
        """Run vtysh command in routing container"""
        cmd = f"vtysh -c '{command}'"
        return self.run_shell_command(cmd, container="ncc0", timeout=timeout)


class FlowSpecVPNMonitor:
    """Main FlowSpec VPN monitoring and diagnostic class"""
    
    def __init__(self):
        self.devices: List[Dict] = []
        self.console = console
        self.current_device: Optional[SSHConnection] = None
        
    def log(self, msg: str):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {msg}"
        print(line)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    
    def discover_devices(self) -> List[Dict]:
        """Discover devices from network mapper or config"""
        import base64
        
        devices_file = Path("/home/dn/SCALER/db/devices.json")
        if devices_file.exists():
            try:
                with open(devices_file) as f:
                    data = json.load(f)
                
                # Handle both formats: {"devices": [...]} or [...]
                if isinstance(data, dict) and "devices" in data:
                    raw_devices = data["devices"]
                elif isinstance(data, list):
                    raw_devices = data
                else:
                    raw_devices = [data]
                
                # Decode base64 passwords and normalize IP field
                self.devices = []
                for dev in raw_devices:
                    device = dict(dev)
                    
                    # Decode base64 password if needed
                    if device.get("password"):
                        try:
                            decoded = base64.b64decode(device["password"]).decode('utf-8')
                            device["password"] = decoded
                        except:
                            pass  # Keep original if not base64
                    
                    # Normalize IP field (might be hostname or IP)
                    if not device.get("ip") and device.get("management_ip"):
                        device["ip"] = device["management_ip"]
                    
                    self.devices.append(device)
                
                return self.devices
            except Exception as e:
                self.log(f"Error loading devices: {e}")
        
        # Fallback to manual entry
        return []
    
    def connect_to_device(self, device: Dict) -> SSHConnection:
        """Create SSH connection to device"""
        return SSHConnection(
            hostname=device.get("hostname", "unknown"),
            ip=device.get("ip", device.get("management_ip", "")),
            username=device.get("username", "dnroot"),
            password=device.get("password", "dnroot")
        )
    
    # =========================================================================
    # FLOW CHECKS - Control Plane (BGP → Zebra → FPM)
    # =========================================================================
    
    def check_bgp_flowspec_vpn_session(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check BGP FlowSpec-VPN session status"""
        results = []
        
        # Check BGP summary for flowspec-vpn
        cmd = "show bgp ipv4 flowspec-vpn summary"
        success, output = conn.run_cli_command(cmd)
        
        if success:
            # Parse neighbors and their state
            neighbors_up = 0
            neighbors_total = 0
            neighbor_lines = []
            
            for line in output.split('\n'):
                if re.search(r'\d+\.\d+\.\d+\.\d+', line) and 'Neighbor' not in line:
                    neighbors_total += 1
                    if 'Established' in line or re.search(r'\d+\s+\d+\s+\d+\s+\d+', line):
                        neighbors_up += 1
                        neighbor_lines.append(line.strip())
            
            status = CheckStatus.PASS if neighbors_up > 0 else CheckStatus.FAIL
            results.append(FlowCheckResult(
                step="1",
                component="BGP",
                check_name="FlowSpec-VPN Sessions",
                status=status,
                expected=f"≥1 neighbor Established",
                actual=f"{neighbors_up}/{neighbors_total} Established",
                command=cmd,
                details="\n".join(neighbor_lines[:5]),
                raw_output=output
            ))
            
            if neighbors_up == 0:
                analysis.problems.append("No FlowSpec-VPN BGP sessions established")
        else:
            results.append(FlowCheckResult(
                step="1",
                component="BGP",
                check_name="FlowSpec-VPN Sessions",
                status=CheckStatus.FAIL,
                expected="Command success",
                actual=f"Error: {output[:100]}",
                command=cmd
            ))
        
        return results
    
    def check_bgp_flowspec_vpn_routes(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check BGP FlowSpec-VPN routes received"""
        results = []
        
        cmd = "show bgp ipv4 flowspec-vpn routes"
        success, output = conn.run_cli_command(cmd)
        
        if success:
            # Count routes
            route_count = output.count("DstPrefix:=") + output.count("SrcPrefix:=")
            
            status = CheckStatus.PASS if route_count > 0 else CheckStatus.WARN
            results.append(FlowCheckResult(
                step="2",
                component="BGP",
                check_name="FlowSpec-VPN Routes Received",
                status=status,
                expected="≥1 FlowSpec-VPN routes",
                actual=f"{route_count} routes",
                command=cmd,
                details=output[:500] if route_count > 0 else "No routes",
                raw_output=output
            ))
            
            # Parse routes into FlowSpecRule objects
            current_nlri = ""
            for line in output.split('\n'):
                if 'DstPrefix:=' in line or 'SrcPrefix:=' in line:
                    # Extract NLRI
                    match = re.search(r'((?:DstPrefix|SrcPrefix):=[^\s]+(?:,(?:DstPrefix|SrcPrefix|Protocol|DstPort|SrcPort):=[^\s]+)*)', line)
                    if match:
                        current_nlri = match.group(1)
                        rule = FlowSpecRule(nlri=current_nlri, bgp_received=True)
                        
                        # Try to extract RT
                        rt_match = re.search(r'RT:(\d+:\d+)', output[output.find(current_nlri):])
                        if rt_match:
                            rule.rt = rt_match.group(1)
                        
                        # Try to extract action
                        if 'traffic-rate:0' in output[output.find(current_nlri):output.find(current_nlri)+500]:
                            rule.action = "DROP"
                        elif 'traffic-rate:' in output[output.find(current_nlri):output.find(current_nlri)+500]:
                            rate_match = re.search(r'traffic-rate:(\d+)', output[output.find(current_nlri):])
                            if rate_match:
                                rule.action = f"RATE-LIMIT:{rate_match.group(1)}"
                        
                        analysis.rules.append(rule)
            
            analysis.total_rules = len(analysis.rules)
            
            if route_count == 0:
                analysis.warnings.append("No FlowSpec-VPN routes received from peers")
        
        return results
    
    def check_vrf_flowspec_import(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check FlowSpec routes imported to VRFs"""
        results = []
        
        # First, get list of VRFs with flowspec
        cmd = "show running-config | include 'vrf instance\\|import-vpn route-target\\|ipv4-flowspec'"
        success, output = conn.run_cli_command(cmd)
        
        vrfs_with_flowspec = []
        current_vrf = None
        
        for line in output.split('\n'):
            if 'vrf instance' in line:
                match = re.search(r'vrf instance (\S+)', line)
                if match:
                    current_vrf = match.group(1)
            elif 'ipv4-flowspec' in line and current_vrf:
                vrfs_with_flowspec.append(current_vrf)
                current_vrf = None
        
        analysis.vrf_count = len(vrfs_with_flowspec)
        
        # Check each VRF
        for vrf in vrfs_with_flowspec[:5]:  # Limit to first 5 VRFs
            cmd = f"show bgp instance vrf {vrf} ipv4 flowspec routes"
            success, output = conn.run_cli_command(cmd)
            
            if success:
                route_count = output.count("DstPrefix:=") + output.count("SrcPrefix:=")
                
                status = CheckStatus.PASS if route_count > 0 else CheckStatus.WARN
                results.append(FlowCheckResult(
                    step="3",
                    component="VRF",
                    check_name=f"FlowSpec Import to VRF '{vrf}'",
                    status=status,
                    expected="Routes imported via RT match",
                    actual=f"{route_count} routes imported",
                    command=cmd,
                    raw_output=output
                ))
                
                # Update rules with VRF info
                for rule in analysis.rules:
                    if rule.nlri in output:
                        rule.vrf_name = vrf
                        rule.bgp_imported_to_vrf = True
        
        if not vrfs_with_flowspec:
            results.append(FlowCheckResult(
                step="3",
                component="VRF",
                check_name="FlowSpec VRF Configuration",
                status=CheckStatus.WARN,
                expected="≥1 VRF with ipv4-flowspec",
                actual="0 VRFs configured",
                command=cmd
            ))
            analysis.warnings.append("No VRFs configured with ipv4-flowspec address family")
        
        return results
    
    def check_zebra_flowspec_db(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check Zebra FlowSpec database (RIB)"""
        results = []
        
        cmd = "show dnos-internal routing rib-manager database flowspec"
        success, output = conn.run_cli_command(cmd)
        
        if success:
            # Count entries
            ipv4_match = re.search(r'IPv4 Flowspec table \(total size: (\d+)\)', output)
            ipv6_match = re.search(r'IPv6 Flowspec table \(total size: (\d+)\)', output)
            
            ipv4_count = int(ipv4_match.group(1)) if ipv4_match else 0
            ipv6_count = int(ipv6_match.group(1)) if ipv6_match else 0
            
            status = CheckStatus.PASS if (ipv4_count + ipv6_count) > 0 else CheckStatus.WARN
            results.append(FlowCheckResult(
                step="4",
                component="Zebra",
                check_name="RIB Manager FlowSpec DB",
                status=status,
                expected="Routes in flowspec_db",
                actual=f"IPv4: {ipv4_count}, IPv6: {ipv6_count}",
                command=cmd,
                details=output[:500],
                raw_output=output
            ))
            
            # Update rules
            for rule in analysis.rules:
                if rule.nlri in output:
                    rule.zebra_installed = True
        
        return results
    
    def check_fpm_flowspec(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check FPM FlowSpec installation"""
        results = []
        
        cmd = "show flowspec ncp 0"
        success, output = conn.run_cli_command(cmd)
        
        if success:
            # Count installed vs not installed
            installed = output.count("Status: Installed")
            not_installed = output.count("Status: Not installed")
            
            status = CheckStatus.PASS if installed > 0 and not_installed == 0 else (
                CheckStatus.WARN if installed > 0 else CheckStatus.FAIL
            )
            
            results.append(FlowCheckResult(
                step="5",
                component="FPM",
                check_name="NCP FlowSpec Installation",
                status=status,
                expected="All rules 'Status: Installed'",
                actual=f"Installed: {installed}, Failed: {not_installed}",
                command=cmd,
                raw_output=output
            ))
            
            if not_installed > 0:
                analysis.problems.append(f"{not_installed} FlowSpec rules failed NCP installation")
                
                # Extract failure reasons
                for line in output.split('\n'):
                    if 'Not installed' in line:
                        analysis.problems.append(f"  - {line.strip()}")
            
            # Update rules
            for rule in analysis.rules:
                if rule.nlri in output:
                    if "Status: Installed" in output[output.find(rule.nlri):output.find(rule.nlri)+200]:
                        rule.fpm_sent = True
        
        return results
    
    # =========================================================================
    # FLOW CHECKS - Data Plane (wb_agent → TCAM)
    # =========================================================================
    
    def check_xray_flowspec_rules(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check xray FlowSpec rules in datapath"""
        results = []
        
        # Get rules via xraycli
        cmd = "run start shell -c 'ncp0' command 'xraycli /wb_agent/flowspec/bgp/ipv4/rules'"
        success, output = conn.run_cli_command(cmd)
        
        if success:
            # Parse rules
            rule_count = output.count("index:")
            
            # Check for VRF-ID issues (critical for VPN!)
            vrf_id_zero = len(re.findall(r'vrf_id:\s*0(?:\s|$)', output))
            vrf_id_nonzero = len(re.findall(r'vrf_id:\s*[1-9]\d*', output))
            
            # Check support status
            unsupported = len(re.findall(r'support:\s*1', output))
            
            status = CheckStatus.PASS if rule_count > 0 and vrf_id_zero == 0 else (
                CheckStatus.WARN if rule_count > 0 else CheckStatus.FAIL
            )
            
            results.append(FlowCheckResult(
                step="6",
                component="wb_agent",
                check_name="FlowSpec BGP Rules (xray)",
                status=status,
                expected="Rules with vrf_id ≠ 0 for VPN",
                actual=f"{rule_count} rules, {vrf_id_nonzero} with VRF, {unsupported} unsupported",
                command="xraycli /wb_agent/flowspec/bgp/ipv4/rules",
                raw_output=output
            ))
            
            if vrf_id_zero > 0:
                analysis.problems.append(f"CRITICAL: {vrf_id_zero} rules have vrf_id=0 (VPN isolation broken!)")
            
            if unsupported > 0:
                analysis.warnings.append(f"{unsupported} rules have unsupported NLRI/action")
            
            # Update rules with DP status
            for rule in analysis.rules:
                if rule.nlri in output:
                    rule.dp_received = True
                    # Extract vrf_id
                    idx = output.find(rule.nlri)
                    if idx >= 0:
                        vrf_match = re.search(r'vrf_id:\s*(\d+)', output[max(0,idx-100):idx+100])
                        if vrf_match:
                            rule.vrf_id = int(vrf_match.group(1))
                        if 'support: 0' in output[idx:idx+200]:
                            rule.dp_supported = True
        else:
            results.append(FlowCheckResult(
                step="6",
                component="wb_agent",
                check_name="FlowSpec BGP Rules (xray)",
                status=CheckStatus.FAIL,
                expected="xray access",
                actual=f"Error: {output[:100]}",
                command="xraycli /wb_agent/flowspec/bgp/ipv4/rules"
            ))
        
        return results
    
    def check_xray_flowspec_info(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check xray FlowSpec table info (errors)"""
        results = []
        
        cmd = "run start shell -c 'ncp0' command 'xraycli /wb_agent/flowspec/bgp/ipv4/info'"
        success, output = conn.run_cli_command(cmd)
        
        if success:
            # Parse counters
            entries_match = re.search(r'number_of_entries:\s*(\d+)', output)
            unsupported_match = re.search(r'num_unsupported:\s*(\d+)', output)
            tcam_errors_match = re.search(r'num_tcam_errors:\s*(\d+)', output)
            
            entries = int(entries_match.group(1)) if entries_match else 0
            unsupported = int(unsupported_match.group(1)) if unsupported_match else 0
            tcam_errors = int(tcam_errors_match.group(1)) if tcam_errors_match else 0
            
            analysis.tcam_errors = tcam_errors
            
            status = CheckStatus.PASS if tcam_errors == 0 else CheckStatus.FAIL
            results.append(FlowCheckResult(
                step="7",
                component="wb_agent",
                check_name="FlowSpec Table Info",
                status=status,
                expected="num_tcam_errors = 0",
                actual=f"entries: {entries}, unsupported: {unsupported}, tcam_errors: {tcam_errors}",
                command="xraycli /wb_agent/flowspec/bgp/ipv4/info",
                raw_output=output
            ))
            
            if tcam_errors > 0:
                analysis.problems.append(f"TCAM ERRORS: {tcam_errors} rules failed to write to hardware!")
        
        return results
    
    def check_xray_hw_counters(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check xray HW counters for failures"""
        results = []
        
        cmd = "run start shell -c 'ncp0' command 'xraycli /wb_agent/flowspec/hw_counters'"
        success, output = conn.run_cli_command(cmd)
        
        if success:
            # Parse counters
            write_ok = re.search(r'hw_rules_write_ok:\s*(\d+)', output)
            write_fail = re.search(r'hw_rules_write_fail:\s*(\d+)', output)
            policer_fail = re.search(r'hw_policers_write_fail:\s*(\d+)', output)
            
            write_ok_val = int(write_ok.group(1)) if write_ok else 0
            write_fail_val = int(write_fail.group(1)) if write_fail else 0
            policer_fail_val = int(policer_fail.group(1)) if policer_fail else 0
            
            analysis.hw_write_failures = write_fail_val + policer_fail_val
            
            status = CheckStatus.PASS if write_fail_val == 0 and policer_fail_val == 0 else CheckStatus.FAIL
            results.append(FlowCheckResult(
                step="8",
                component="wb_agent",
                check_name="Hardware Write Counters",
                status=status,
                expected="write_fail = 0, policer_fail = 0",
                actual=f"writes OK: {write_ok_val}, fails: {write_fail_val}, policer fails: {policer_fail_val}",
                command="xraycli /wb_agent/flowspec/hw_counters",
                raw_output=output
            ))
            
            if write_fail_val > 0:
                analysis.problems.append(f"HW WRITE FAILURE: {write_fail_val} rules failed BCM/TCAM programming!")
        
        return results
    
    def check_flowspec_counters(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check FlowSpec match counters"""
        results = []
        
        cmd = "show flowspec"
        success, output = conn.run_cli_command(cmd)
        
        if success:
            # Count rules with traffic
            rules_with_traffic = 0
            total_packets = 0
            
            for match in re.finditer(r'Match packet counter:\s*(\d+)', output):
                count = int(match.group(1))
                if count > 0:
                    rules_with_traffic += 1
                    total_packets += count
            
            status = CheckStatus.PASS if rules_with_traffic > 0 else CheckStatus.WARN
            results.append(FlowCheckResult(
                step="9",
                component="Counters",
                check_name="FlowSpec Match Counters",
                status=status,
                expected="Counters incrementing with traffic",
                actual=f"{rules_with_traffic} rules matched, {total_packets} total packets",
                command=cmd,
                raw_output=output
            ))
            
            # Update rules with counters
            for rule in analysis.rules:
                if rule.nlri in output:
                    idx = output.find(rule.nlri)
                    pkt_match = re.search(r'Match packet counter:\s*(\d+)', output[idx:idx+300])
                    if pkt_match:
                        rule.match_packets = int(pkt_match.group(1))
                    rule.dp_installed = True
                    analysis.rules_installed += 1
        
        return results
    
    # =========================================================================
    # ADDITIONAL CHECKS - Interfaces and VRF
    # =========================================================================
    
    def check_flowspec_enabled_interfaces(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check interfaces with flowspec enabled"""
        results = []
        
        cmd = "show running-config | include 'flowspec enabled'"
        success, output = conn.run_cli_command(cmd)
        
        if success:
            iface_count = output.count('flowspec enabled')
            
            status = CheckStatus.PASS if iface_count > 0 else CheckStatus.WARN
            results.append(FlowCheckResult(
                step="10",
                component="Interfaces",
                check_name="FlowSpec Enabled Interfaces",
                status=status,
                expected="≥1 interface with flowspec enabled",
                actual=f"{iface_count} interfaces",
                command=cmd,
                details=output[:300],
                raw_output=output
            ))
            
            if iface_count == 0:
                analysis.warnings.append("No interfaces have 'flowspec enabled' - rules won't apply to traffic!")
        
        return results
    
    # =========================================================================
    # TRACE EXTRACTION - From Containers (NCC, NCP)
    # =========================================================================
    
    def extract_bgpd_traces(self, conn: SSHConnection, filter_pattern: str = "flowspec") -> str:
        """Extract bgpd traces related to FlowSpec from NCC container"""
        traces = []
        
        # Get recent bgpd traces
        cmd = f"run start shell -c 'ncc0' command 'tail -500 /var/log/bgpd_traces 2>/dev/null | grep -i {filter_pattern}'"
        success, output = conn.run_cli_command(cmd, timeout=60)
        
        if success and output.strip():
            traces.append("=== BGPD TRACES (NCC0) ===")
            traces.append(output[:5000])
        
        return "\n".join(traces)
    
    def extract_zebra_traces(self, conn: SSHConnection, filter_pattern: str = "flowspec") -> str:
        """Extract zebra/rib-manager traces related to FlowSpec from NCC container"""
        traces = []
        
        # Get rib-manager traces
        cmd = f"run start shell -c 'ncc0' command 'tail -500 /var/log/rib-manager_traces 2>/dev/null | grep -i {filter_pattern}'"
        success, output = conn.run_cli_command(cmd, timeout=60)
        
        if success and output.strip():
            traces.append("=== RIB-MANAGER TRACES (NCC0) ===")
            traces.append(output[:5000])
        
        return "\n".join(traces)
    
    def extract_fpm_traces(self, conn: SSHConnection, filter_pattern: str = "flowspec") -> str:
        """Extract FPM/fib-manager traces"""
        traces = []
        
        # Get fib-manager traces
        cmd = f"run start shell -c 'ncc0' command 'tail -500 /var/log/fib-manager_traces 2>/dev/null | grep -i {filter_pattern}'"
        success, output = conn.run_cli_command(cmd, timeout=60)
        
        if success and output.strip():
            traces.append("=== FIB-MANAGER TRACES (NCC0) ===")
            traces.append(output[:5000])
        
        return "\n".join(traces)
    
    def extract_wbox_traces(self, conn: SSHConnection, filter_pattern: str = "flowspec") -> str:
        """Extract wb_agent traces related to FlowSpec from NCP container"""
        traces = []
        
        # Get wbox traces from NCP
        cmd = f"run start shell -c 'ncp0' command 'tail -500 /var/log/wb_agent_traces 2>/dev/null | grep -i {filter_pattern}'"
        success, output = conn.run_cli_command(cmd, timeout=60)
        
        if success and output.strip():
            traces.append("=== WB_AGENT TRACES (NCP0) ===")
            traces.append(output[:5000])
        
        return "\n".join(traces)
    
    def extract_all_flowspec_traces(self, conn: SSHConnection) -> Dict[str, str]:
        """Extract all FlowSpec related traces from all containers"""
        traces = {}
        
        # BGP traces
        bgp_traces = self.extract_bgpd_traces(conn)
        if bgp_traces:
            traces["bgpd"] = bgp_traces
        
        # Zebra/RIB traces
        zebra_traces = self.extract_zebra_traces(conn)
        if zebra_traces:
            traces["zebra"] = zebra_traces
        
        # FPM traces
        fpm_traces = self.extract_fpm_traces(conn)
        if fpm_traces:
            traces["fpm"] = fpm_traces
        
        # WBox traces
        wbox_traces = self.extract_wbox_traces(conn)
        if wbox_traces:
            traces["wbox"] = wbox_traces
        
        return traces
    
    def save_traces(self, traces: Dict[str, str], hostname: str) -> Path:
        """Save extracted traces to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = SNAPSHOTS_DIR / f"traces_{hostname}_{timestamp}.txt"
        
        with open(filepath, "w") as f:
            for component, trace_data in traces.items():
                f.write(f"\n{'='*80}\n")
                f.write(f"COMPONENT: {component.upper()}\n")
                f.write(f"{'='*80}\n")
                f.write(trace_data)
                f.write("\n")
        
        return filepath
    
    # =========================================================================
    # VTYSH COMMANDS - Direct routing daemon access
    # =========================================================================
    
    def run_vtysh_commands(self, conn: SSHConnection) -> Dict[str, str]:
        """Run vtysh commands for detailed BGP FlowSpec debugging"""
        vtysh_outputs = {}
        
        commands = [
            "show bgp ipv4 flowspec",
            "show bgp ipv6 flowspec", 
            "show bgp ipv4 flowspec-vpn",
            "show bgp neighbors",
            "show bgp nexthop",
        ]
        
        for cmd in commands:
            vtysh_cmd = f"run start shell -c 'ncc0' command 'vtysh -c \"{cmd}\"'"
            success, output = conn.run_cli_command(vtysh_cmd, timeout=30)
            if success:
                vtysh_outputs[cmd] = output
        
        return vtysh_outputs
    
    # =========================================================================
    # DEEP DIVE ANALYSIS - Per-rule troubleshooting
    # =========================================================================
    
    def analyze_specific_rule(self, conn: SSHConnection, nlri: str) -> Dict[str, Any]:
        """Deep dive analysis of a specific FlowSpec rule"""
        result = {
            "nlri": nlri,
            "checks": [],
            "traces": [],
        }
        
        # Check in BGP FlowSpec-VPN table
        cmd = f'show bgp ipv4 flowspec-vpn nlri "{nlri}"'
        success, output = conn.run_cli_command(cmd)
        result["bgp_flowspec_vpn"] = {"success": success, "output": output}
        
        # Check in VRF tables (try common VRF names)
        for vrf in ["INTERNET-VRF", "CUSTOMER-A", "VRF-1"]:
            cmd = f'show bgp instance vrf {vrf} ipv4 flowspec nlri "{nlri}"'
            success, output = conn.run_cli_command(cmd)
            if success and "DstPrefix" in output:
                result[f"vrf_{vrf}"] = {"success": success, "output": output}
        
        # Check in NCP datapath
        cmd = f'show flowspec ncp 0 nlri "{nlri}"'
        success, output = conn.run_cli_command(cmd)
        result["ncp_status"] = {"success": success, "output": output}
        
        # Check xray for specific rule
        cmd = f"run start shell -c 'ncp0' command 'xraycli /wb_agent/flowspec/bgp/ipv4/rules'"
        success, output = conn.run_cli_command(cmd)
        if success and nlri in output:
            # Extract the rule section
            idx = output.find(nlri)
            rule_section = output[max(0, idx-200):idx+500]
            result["xray_rule"] = {"success": True, "output": rule_section}
        else:
            result["xray_rule"] = {"success": False, "output": "Rule not found in xray"}
        
        return result
    
    def print_rule_deep_dive(self, analysis: Dict[str, Any]):
        """Print deep dive analysis of a specific rule"""
        if not RICH_AVAILABLE:
            print(json.dumps(analysis, indent=2))
            return
        
        console.print(Panel(
            f"[bold]NLRI:[/] {analysis['nlri']}",
            title="FlowSpec Rule Deep Dive",
            border_style="cyan"
        ))
        
        for key, value in analysis.items():
            if key == "nlri":
                continue
            if isinstance(value, dict) and "output" in value:
                status = "[green]✓[/]" if value.get("success") else "[red]✗[/]"
                console.print(f"\n{status} [bold]{key}[/]")
                if value.get("output"):
                    console.print(Panel(value["output"][:1000], border_style="dim"))
    
    # =========================================================================
    # ANALYSIS AND REPORTING
    # =========================================================================
    
    def run_full_analysis(self, device: Dict) -> DeviceAnalysis:
        """Run complete FlowSpec VPN analysis on a device"""
        conn = self.connect_to_device(device)
        
        analysis = DeviceAnalysis(
            hostname=device.get("hostname", "unknown"),
            ip=device.get("ip", device.get("management_ip", "")),
            timestamp=datetime.now().isoformat()
        )
        
        # Get DNOS version
        success, output = conn.run_cli_command("show system version")
        if success:
            match = re.search(r'Software version:\s*(\S+)', output)
            if match:
                analysis.dnos_version = match.group(1)
        
        # Run all checks
        check_methods = [
            self.check_bgp_flowspec_vpn_session,
            self.check_bgp_flowspec_vpn_routes,
            self.check_vrf_flowspec_import,
            self.check_zebra_flowspec_db,
            self.check_fpm_flowspec,
            self.check_xray_flowspec_rules,
            self.check_xray_flowspec_info,
            self.check_xray_hw_counters,
            self.check_flowspec_counters,
            self.check_flowspec_enabled_interfaces,
        ]
        
        for method in check_methods:
            try:
                results = method(conn, analysis)
                analysis.checks.extend(results)
            except Exception as e:
                analysis.checks.append(FlowCheckResult(
                    step="?",
                    component=method.__name__,
                    check_name=method.__name__,
                    status=CheckStatus.FAIL,
                    expected="Check success",
                    actual=f"Exception: {e}",
                    command=""
                ))
        
        # Calculate final counts
        analysis.rules_failed = analysis.total_rules - analysis.rules_installed
        
        return analysis
    
    def print_flow_diagram(self, analysis: DeviceAnalysis):
        """Print visual flow diagram with check status"""
        if not RICH_AVAILABLE:
            self._print_flow_diagram_simple(analysis)
            return
        
        # Create flow diagram as tree
        tree = Tree(f"[bold cyan]FlowSpec VPN Flow - {analysis.hostname}[/]")
        
        # Group checks by component
        components = {}
        for check in analysis.checks:
            if check.component not in components:
                components[check.component] = []
            components[check.component].append(check)
        
        flow_order = ["BGP", "VRF", "Zebra", "FPM", "wb_agent", "Counters", "Interfaces"]
        
        for component in flow_order:
            if component in components:
                color = "green" if all(c.status == CheckStatus.PASS for c in components[component]) else (
                    "yellow" if any(c.status == CheckStatus.PASS for c in components[component]) else "red"
                )
                branch = tree.add(f"[{color}]{component}[/]")
                
                for check in components[component]:
                    status_icon = check.status.value
                    status_color = "green" if check.status == CheckStatus.PASS else (
                        "yellow" if check.status == CheckStatus.WARN else "red"
                    )
                    branch.add(f"[{status_color}]{status_icon}[/] {check.check_name}")
        
        console.print(Panel(tree, title="Flow Diagram", border_style="blue"))
    
    def _print_flow_diagram_simple(self, analysis: DeviceAnalysis):
        """Print simple flow diagram without rich"""
        print(f"\n{'='*60}")
        print(f"FlowSpec VPN Flow - {analysis.hostname}")
        print(f"{'='*60}")
        
        for check in analysis.checks:
            status = check.status.value
            print(f"  [{check.step}] {status} {check.component}: {check.check_name}")
            print(f"       Expected: {check.expected}")
            print(f"       Actual:   {check.actual}")
        
        print(f"{'='*60}\n")
    
    def print_summary_table(self, analysis: DeviceAnalysis):
        """Print summary table with ✓/✗ indicators"""
        if not RICH_AVAILABLE:
            self._print_summary_table_simple(analysis)
            return
        
        table = Table(
            title=f"FlowSpec VPN Analysis - {analysis.hostname}",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("Step", style="dim", width=4)
        table.add_column("Component", width=12)
        table.add_column("Check", width=35)
        table.add_column("Status", width=6, justify="center")
        table.add_column("Expected", width=25)
        table.add_column("Actual", width=25)
        
        for check in analysis.checks:
            status_icon = check.status.value
            status_style = "green" if check.status == CheckStatus.PASS else (
                "yellow" if check.status == CheckStatus.WARN else "red"
            )
            
            table.add_row(
                check.step,
                check.component,
                check.check_name,
                f"[{status_style}]{status_icon}[/]",
                check.expected[:25],
                check.actual[:25]
            )
        
        console.print(table)
        
        # Problems panel
        if analysis.problems:
            problems_text = "\n".join([f"[red]✗[/] {p}" for p in analysis.problems])
            console.print(Panel(problems_text, title="[bold red]Problems Detected[/]", border_style="red"))
        
        # Warnings panel
        if analysis.warnings:
            warnings_text = "\n".join([f"[yellow]⚠[/] {w}" for w in analysis.warnings])
            console.print(Panel(warnings_text, title="[bold yellow]Warnings[/]", border_style="yellow"))
        
        # Summary panel
        summary = f"""
[bold]Device:[/] {analysis.hostname} ({analysis.ip})
[bold]Version:[/] {analysis.dnos_version}
[bold]Timestamp:[/] {analysis.timestamp}

[bold]FlowSpec Rules:[/]
  Total Received:   {analysis.total_rules}
  Installed in DP:  {analysis.rules_installed}
  Failed:           {analysis.rules_failed}
  TCAM Errors:      {analysis.tcam_errors}
  HW Write Fails:   {analysis.hw_write_failures}

[bold]VRFs with FlowSpec:[/] {analysis.vrf_count}
"""
        console.print(Panel(summary, title="[bold blue]Summary[/]", border_style="blue"))
    
    def _print_summary_table_simple(self, analysis: DeviceAnalysis):
        """Print simple summary without rich"""
        print(f"\n{'='*80}")
        print(f"FlowSpec VPN Analysis Summary - {analysis.hostname}")
        print(f"{'='*80}")
        print(f"{'Step':<5} {'Component':<12} {'Check':<35} {'Status':<8} {'Expected':<20} {'Actual':<20}")
        print(f"{'-'*80}")
        
        for check in analysis.checks:
            print(f"{check.step:<5} {check.component:<12} {check.check_name:<35} {check.status.value:<8} {check.expected[:20]:<20} {check.actual[:20]:<20}")
        
        print(f"\nProblems: {len(analysis.problems)}")
        for p in analysis.problems:
            print(f"  ✗ {p}")
        
        print(f"\nWarnings: {len(analysis.warnings)}")
        for w in analysis.warnings:
            print(f"  ⚠ {w}")
        
        print(f"{'='*80}\n")
    
    def print_detailed_rule_table(self, analysis: DeviceAnalysis):
        """Print detailed table of FlowSpec rules"""
        if not analysis.rules:
            print("No FlowSpec rules found.")
            return
        
        if not RICH_AVAILABLE:
            self._print_rule_table_simple(analysis)
            return
        
        table = Table(
            title="FlowSpec Rules Detail",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("NLRI", width=40)
        table.add_column("VRF", width=15)
        table.add_column("VRF_ID", width=8)
        table.add_column("Action", width=12)
        table.add_column("BGP", width=4, justify="center")
        table.add_column("VRF Imp", width=7, justify="center")
        table.add_column("Zebra", width=6, justify="center")
        table.add_column("DP", width=4, justify="center")
        table.add_column("TCAM", width=5, justify="center")
        table.add_column("Packets", width=10, justify="right")
        
        for rule in analysis.rules:
            def status(val):
                return "[green]✓[/]" if val else "[red]✗[/]"
            
            vrf_id_str = str(rule.vrf_id) if rule.vrf_id > 0 else "[red]0[/]"
            
            table.add_row(
                rule.nlri[:40],
                rule.vrf_name or "-",
                vrf_id_str,
                rule.action or "-",
                status(rule.bgp_received),
                status(rule.bgp_imported_to_vrf),
                status(rule.zebra_installed),
                status(rule.dp_received),
                status(rule.dp_installed),
                str(rule.match_packets)
            )
        
        console.print(table)
    
    def _print_rule_table_simple(self, analysis: DeviceAnalysis):
        """Print simple rule table without rich"""
        print(f"\nFlowSpec Rules ({len(analysis.rules)}):")
        for rule in analysis.rules:
            bgp = "✓" if rule.bgp_received else "✗"
            vrf = "✓" if rule.bgp_imported_to_vrf else "✗"
            dp = "✓" if rule.dp_installed else "✗"
            print(f"  {rule.nlri[:50]} | VRF:{rule.vrf_name or '-'} | BGP:{bgp} VRF:{vrf} DP:{dp} | Pkts:{rule.match_packets}")
    
    # =========================================================================
    # WIZARD MODE
    # =========================================================================
    
    def run_wizard(self):
        """Run interactive wizard mode"""
        if not RICH_AVAILABLE:
            print("Wizard mode requires 'rich' library. Install with: pip install rich")
            return
        
        console.print(Panel.fit(
            "[bold cyan]FlowSpec VPN Diagnostic Wizard[/]\n"
            "This wizard will analyze FlowSpec VPN installation across your network.",
            border_style="cyan"
        ))
        
        # Discover devices
        devices = self.discover_devices()
        
        if not devices:
            console.print("[yellow]No devices found in configuration.[/]")
            ip = Prompt.ask("Enter device IP address")
            hostname = Prompt.ask("Device hostname", default="PE-1")
            username = Prompt.ask("Username", default="dnroot")
            password = Prompt.ask("Password", default="dnroot", password=True)
            devices = [{"hostname": hostname, "ip": ip, "username": username, "password": password}]
        
        # Show device selection
        console.print("\n[bold]Available Devices:[/]")
        for i, dev in enumerate(devices, 1):
            console.print(f"  [{i}] {dev.get('hostname', 'unknown')} ({dev.get('ip', dev.get('management_ip', 'N/A'))})")
        console.print(f"  [A] Analyze ALL devices")
        
        choice = Prompt.ask("Select device(s)", default="1")
        
        if choice.lower() == 'a':
            selected_devices = devices
        else:
            try:
                idx = int(choice) - 1
                selected_devices = [devices[idx]]
            except:
                console.print("[red]Invalid selection[/]")
                return
        
        # Run analysis
        for device in selected_devices:
            console.print(f"\n[bold cyan]Analyzing {device.get('hostname')}...[/]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"Connecting to {device.get('hostname')}...", total=None)
                
                analysis = self.run_full_analysis(device)
                
                progress.update(task, description="Analysis complete!")
            
            # Print results
            self.print_flow_diagram(analysis)
            self.print_summary_table(analysis)
            
            if Confirm.ask("Show detailed rule table?", default=False):
                self.print_detailed_rule_table(analysis)
            
            if Confirm.ask("Show raw command outputs?", default=False):
                for check in analysis.checks:
                    if check.raw_output:
                        console.print(Panel(
                            check.raw_output[:2000],
                            title=f"[bold]{check.command}[/]",
                            border_style="dim"
                        ))
            
            # Trace extraction
            if Confirm.ask("Extract FlowSpec traces from containers (NCC/NCP)?", default=False):
                console.print("[cyan]Extracting traces from containers...[/]")
                traces = self.extract_all_flowspec_traces(conn)
                
                if traces:
                    for component, trace_data in traces.items():
                        console.print(Panel(
                            trace_data[:3000],
                            title=f"[bold]{component.upper()} Traces[/]",
                            border_style="yellow"
                        ))
                    
                    # Save traces
                    trace_file = self.save_traces(traces, device.get('hostname'))
                    console.print(f"[green]✓[/] Traces saved to: {trace_file}")
                else:
                    console.print("[yellow]No FlowSpec traces found in container logs.[/]")
            
            # Deep dive on specific rule
            if analysis.rules and Confirm.ask("Deep dive on a specific rule?", default=False):
                console.print("\n[bold]Available rules:[/]")
                for i, rule in enumerate(analysis.rules[:10], 1):
                    console.print(f"  [{i}] {rule.nlri[:60]}")
                
                choice = Prompt.ask("Select rule number", default="1")
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(analysis.rules):
                        console.print(f"[cyan]Analyzing rule: {analysis.rules[idx].nlri}[/]")
                        deep_analysis = self.analyze_specific_rule(conn, analysis.rules[idx].nlri)
                        self.print_rule_deep_dive(deep_analysis)
                except:
                    console.print("[red]Invalid selection[/]")
            
            # vtysh commands
            if Confirm.ask("Run vtysh commands for additional BGP details?", default=False):
                console.print("[cyan]Running vtysh commands...[/]")
                vtysh_outputs = self.run_vtysh_commands(conn)
                
                for cmd, output in vtysh_outputs.items():
                    if output.strip():
                        console.print(Panel(
                            output[:2000],
                            title=f"[bold]vtysh: {cmd}[/]",
                            border_style="magenta"
                        ))
            
            # Save results
            if Confirm.ask("Save analysis to file?", default=True):
                self.save_analysis(analysis)
    
    def save_analysis(self, analysis: DeviceAnalysis, filename: str = None) -> Path:
        """Save analysis to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_{analysis.hostname}_{timestamp}.json"
        
        filepath = SNAPSHOTS_DIR / filename
        
        # Convert to dict
        data = {
            "hostname": analysis.hostname,
            "ip": analysis.ip,
            "timestamp": analysis.timestamp,
            "dnos_version": analysis.dnos_version,
            "summary": {
                "total_rules": analysis.total_rules,
                "rules_installed": analysis.rules_installed,
                "rules_failed": analysis.rules_failed,
                "tcam_errors": analysis.tcam_errors,
                "hw_write_failures": analysis.hw_write_failures,
                "vrf_count": analysis.vrf_count,
            },
            "problems": analysis.problems,
            "warnings": analysis.warnings,
            "checks": [
                {
                    "step": c.step,
                    "component": c.component,
                    "check_name": c.check_name,
                    "status": c.status.value,
                    "expected": c.expected,
                    "actual": c.actual,
                    "command": c.command,
                }
                for c in analysis.checks
            ],
            "rules": [
                {
                    "nlri": r.nlri,
                    "vrf_name": r.vrf_name,
                    "vrf_id": r.vrf_id,
                    "action": r.action,
                    "bgp_received": r.bgp_received,
                    "bgp_imported_to_vrf": r.bgp_imported_to_vrf,
                    "zebra_installed": r.zebra_installed,
                    "dp_installed": r.dp_installed,
                    "match_packets": r.match_packets,
                }
                for r in analysis.rules
            ]
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        # Also update latest
        with open(LATEST_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        if RICH_AVAILABLE:
            console.print(f"[green]✓[/] Saved to: {filepath}")
        else:
            print(f"✓ Saved to: {filepath}")
        
        return filepath
    
    # =========================================================================
    # DAEMON MODE
    # =========================================================================
    
    def get_pid(self) -> Optional[int]:
        """Get running daemon PID"""
        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text().strip())
                os.kill(pid, 0)
                return pid
            except (ValueError, ProcessLookupError, PermissionError):
                PID_FILE.unlink(missing_ok=True)
        return None
    
    def start_daemon(self):
        """Start monitoring daemon"""
        pid = self.get_pid()
        if pid:
            print(f"Monitor already running (PID: {pid})")
            return
        
        print(f"Starting FlowSpec VPN monitor daemon...")
        print(f"  Interval: {INTERVAL_SECONDS}s")
        print(f"  Log: {LOG_FILE}")
        print(f"  Snapshots: {SNAPSHOTS_DIR}")
        
        # Fork to background
        subprocess.Popen(
            ["nohup", sys.executable, __file__, "_daemon"],
            stdout=open(LOG_FILE, "a"),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
        
        time.sleep(2)
        pid = self.get_pid()
        if pid:
            print(f"✅ Monitor started (PID: {pid})")
        else:
            print("❌ Failed to start. Check log file.")
    
    def stop_daemon(self):
        """Stop monitoring daemon"""
        pid = self.get_pid()
        if not pid:
            print("Monitor is not running.")
            return
        
        print(f"Stopping daemon (PID: {pid})...")
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            if self.get_pid():
                os.kill(pid, signal.SIGKILL)
            print("✅ Monitor stopped.")
        except ProcessLookupError:
            print("Process already stopped.")
        
        PID_FILE.unlink(missing_ok=True)
    
    def run_daemon_loop(self):
        """Main daemon monitoring loop"""
        self.log("Starting FlowSpec VPN monitor daemon")
        
        PID_FILE.write_text(str(os.getpid()))
        
        devices = self.discover_devices()
        if not devices:
            self.log("No devices found! Exiting.")
            return
        
        try:
            while True:
                self.log(f"=== Monitor Run at {datetime.now().isoformat()} ===")
                
                for device in devices:
                    try:
                        analysis = self.run_full_analysis(device)
                        
                        # Log summary
                        passed = sum(1 for c in analysis.checks if c.status == CheckStatus.PASS)
                        failed = sum(1 for c in analysis.checks if c.status == CheckStatus.FAIL)
                        
                        self.log(f"{device.get('hostname')}: {passed} PASS, {failed} FAIL, {len(analysis.problems)} problems")
                        
                        for problem in analysis.problems:
                            self.log(f"  PROBLEM: {problem}")
                        
                        # Save snapshot
                        self.save_analysis(analysis)
                        
                    except Exception as e:
                        self.log(f"Error analyzing {device.get('hostname')}: {e}")
                
                self.log(f"Sleeping {INTERVAL_SECONDS}s...")
                time.sleep(INTERVAL_SECONDS)
                
        except KeyboardInterrupt:
            self.log("Received interrupt, stopping...")
        finally:
            PID_FILE.unlink(missing_ok=True)
            self.log("Monitor daemon stopped.")
    
    def show_status(self):
        """Show daemon status"""
        pid = self.get_pid()
        
        if pid:
            print(f"✅ Monitor is RUNNING (PID: {pid})")
        else:
            print("❌ Monitor is NOT running")
        
        print(f"\n📁 Monitor directory: {MONITOR_DIR}")
        
        if LATEST_FILE.exists():
            with open(LATEST_FILE) as f:
                data = json.load(f)
            print(f"\n📊 Latest analysis: {data.get('timestamp')}")
            print(f"   Device: {data.get('hostname')} ({data.get('ip')})")
            print(f"   Version: {data.get('dnos_version')}")
            s = data.get("summary", {})
            print(f"   Rules: {s.get('total_rules')} total, {s.get('rules_installed')} installed")
            print(f"   Problems: {len(data.get('problems', []))}")
        
        snapshots = list(SNAPSHOTS_DIR.glob("analysis_*.json"))
        print(f"\n📸 Snapshots: {len(snapshots)} saved")


# =============================================================================
# MAIN
# =============================================================================

def print_help():
    """Print help message"""
    print(__doc__)
    print("""
Commands:
  wizard    - Interactive wizard mode (recommended)
  analyze   - Analyze a specific device: analyze <hostname_or_ip>
  traces    - Extract FlowSpec traces from containers: traces <hostname_or_ip>
  deepdive  - Deep dive on specific NLRI: deepdive <hostname_or_ip> "<NLRI>"
  start     - Start monitoring daemon
  stop      - Stop monitoring daemon
  status    - Show daemon status and latest results
  baseline  - Save current state as baseline
  compare   - Compare current state with baseline
  vtysh     - Run vtysh commands: vtysh <hostname_or_ip>
  help      - Show this help message

Examples:
  python3 flowspec_vpn_monitor.py wizard
  python3 flowspec_vpn_monitor.py analyze PE-1
  python3 flowspec_vpn_monitor.py traces PE-1
  python3 flowspec_vpn_monitor.py deepdive PE-1 "DstPrefix:=10.10.10.1/32"
  python3 flowspec_vpn_monitor.py start
""")


def main():
    monitor = FlowSpecVPNMonitor()
    
    if len(sys.argv) < 2:
        print_help()
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == "wizard":
        monitor.run_wizard()
    
    elif cmd == "analyze":
        if len(sys.argv) < 3:
            print("Usage: analyze <device_hostname_or_ip>")
            return
        
        device_id = sys.argv[2]
        devices = monitor.discover_devices()
        
        # Find device
        device = None
        for d in devices:
            if d.get("hostname") == device_id or d.get("ip") == device_id:
                device = d
                break
        
        if not device:
            # Treat as IP
            device = {"hostname": device_id, "ip": device_id, "username": "dnroot", "password": "dnroot"}
        
        print(f"Analyzing {device.get('hostname')}...")
        analysis = monitor.run_full_analysis(device)
        monitor.print_flow_diagram(analysis)
        monitor.print_summary_table(analysis)
        monitor.save_analysis(analysis)
    
    elif cmd == "start":
        monitor.start_daemon()
    
    elif cmd == "stop":
        monitor.stop_daemon()
    
    elif cmd == "status":
        monitor.show_status()
    
    elif cmd == "_daemon":
        monitor.run_daemon_loop()
    
    elif cmd == "baseline":
        devices = monitor.discover_devices()
        if devices:
            print("Saving baseline for all devices...")
            for device in devices:
                analysis = monitor.run_full_analysis(device)
                filepath = MONITOR_DIR / f"baseline_{device.get('hostname')}.json"
                monitor.save_analysis(analysis, filepath.name)
            print("✅ Baseline saved!")
        else:
            print("No devices found.")
    
    elif cmd == "compare":
        devices = monitor.discover_devices()
        if devices:
            for device in devices:
                baseline_file = MONITOR_DIR / f"baseline_{device.get('hostname')}.json"
                if not baseline_file.exists():
                    print(f"No baseline for {device.get('hostname')}. Run 'baseline' first.")
                    continue
                
                print(f"Comparing {device.get('hostname')}...")
                current = monitor.run_full_analysis(device)
                
                with open(baseline_file) as f:
                    baseline = json.load(f)
                
                # Compare
                print(f"\n{'='*60}")
                print(f"Comparison: {device.get('hostname')}")
                print(f"  Baseline: {baseline.get('timestamp')}")
                print(f"  Current:  {current.timestamp}")
                print(f"{'='*60}")
                
                # Compare problems
                old_problems = set(baseline.get("problems", []))
                new_problems = set(current.problems)
                
                added = new_problems - old_problems
                resolved = old_problems - new_problems
                
                if added:
                    print(f"\n🐛 NEW PROBLEMS ({len(added)}):")
                    for p in added:
                        print(f"  ✗ {p}")
                
                if resolved:
                    print(f"\n✅ RESOLVED ({len(resolved)}):")
                    for p in resolved:
                        print(f"  ✓ {p}")
                
                if not added and not resolved:
                    print("\n✅ No changes in problems detected.")
        else:
            print("No devices found.")
    
    elif cmd == "traces":
        if len(sys.argv) < 3:
            print("Usage: traces <device_hostname_or_ip>")
            return
        
        device_id = sys.argv[2]
        devices = monitor.discover_devices()
        
        device = None
        for d in devices:
            if d.get("hostname") == device_id or d.get("ip") == device_id:
                device = d
                break
        
        if not device:
            device = {"hostname": device_id, "ip": device_id, "username": "dnroot", "password": "dnroot"}
        
        print(f"Extracting FlowSpec traces from {device.get('hostname')}...")
        conn = monitor.connect_to_device(device)
        traces = monitor.extract_all_flowspec_traces(conn)
        
        if traces:
            for component, trace_data in traces.items():
                print(f"\n{'='*60}")
                print(f"  {component.upper()} TRACES")
                print(f"{'='*60}")
                print(trace_data[:3000])
            
            filepath = monitor.save_traces(traces, device.get('hostname'))
            print(f"\n✓ Traces saved to: {filepath}")
        else:
            print("No FlowSpec traces found.")
    
    elif cmd == "deepdive":
        if len(sys.argv) < 4:
            print('Usage: deepdive <device_hostname_or_ip> "<NLRI>"')
            print('Example: deepdive PE-1 "DstPrefix:=10.10.10.1/32,Protocol:=6"')
            return
        
        device_id = sys.argv[2]
        nlri = sys.argv[3]
        
        devices = monitor.discover_devices()
        device = None
        for d in devices:
            if d.get("hostname") == device_id or d.get("ip") == device_id:
                device = d
                break
        
        if not device:
            device = {"hostname": device_id, "ip": device_id, "username": "dnroot", "password": "dnroot"}
        
        print(f"Deep diving on rule: {nlri}")
        conn = monitor.connect_to_device(device)
        analysis = monitor.analyze_specific_rule(conn, nlri)
        monitor.print_rule_deep_dive(analysis)
    
    elif cmd == "vtysh":
        if len(sys.argv) < 3:
            print("Usage: vtysh <device_hostname_or_ip>")
            return
        
        device_id = sys.argv[2]
        devices = monitor.discover_devices()
        
        device = None
        for d in devices:
            if d.get("hostname") == device_id or d.get("ip") == device_id:
                device = d
                break
        
        if not device:
            device = {"hostname": device_id, "ip": device_id, "username": "dnroot", "password": "dnroot"}
        
        print(f"Running vtysh commands on {device.get('hostname')}...")
        conn = monitor.connect_to_device(device)
        vtysh_outputs = monitor.run_vtysh_commands(conn)
        
        for cmd_name, output in vtysh_outputs.items():
            print(f"\n{'='*60}")
            print(f"  vtysh: {cmd_name}")
            print(f"{'='*60}")
            print(output[:2000])
    
    elif cmd == "help":
        print_help()
    
    else:
        print(f"Unknown command: {cmd}")
        print_help()


if __name__ == "__main__":
    main()
