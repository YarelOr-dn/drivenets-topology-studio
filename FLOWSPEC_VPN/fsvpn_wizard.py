#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           FSVPN-WIZARD                                         ║
║           FlowSpec VPN Diagnostic & Monitoring Wizard                          ║
║                                                                                 ║
║  Comprehensive tool for analyzing FlowSpec VPN rule installation               ║
║  from BGP reception through datapath TCAM programming                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝

VRF-ID Semantics (from DP team - Ehud):
  • VRF-ID = 0     → Default VRF (valid, not a bug!)
  • No VRF field   → Rule applies to ALL VRFs
  • VRF-ID > 0     → Specific non-default VRF

FlowSpec AFI-SAFI Semantics:
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ SAFI 133 (flowspec)     → Default VRF / GRT (Global Routing Table)     │
  │   - No RD, No RT required                                              │
  │   - NLRI: Raw FlowSpec rules                                           │
  │   - Affects: Traffic in default/global VRF only                        │
  │                                                                         │
  │ SAFI 134 (flowspec-vpn) → VPN/VRF contexts                             │
  │   - RD required (prefixed to NLRI)                                     │
  │   - RT required (for VRF import/export via extended community)         │
  │   - NLRI: RD:FlowSpec rules                                            │
  │   - Affects: Only VRFs that import the matching RT                     │
  └─────────────────────────────────────────────────────────────────────────┘
  
  ★ SAFI 133 and 134 COEXIST INDEPENDENTLY - They do NOT interfere!
  ★ SAFI 134 rules CANNOT affect GRT/default VRF (no RD/RT to match)
  ★ To affect default VRF, you MUST use SAFI 133 (flowspec)

Priority (Lower number = Higher precedence in TCAM!):
  • Local Policies: Priority 0 - 1,999,999     ← WINS! (lower = first match)
  • BGP FlowSpec:   Priority 2,000,000 - 4,000,000  (higher = loses)

Shared TCAM: 12K IPv4 / 4K IPv6 (BGP + Local Policies combined)

Usage:
    Simply run: python3 fsvpn_wizard.py
    
    The wizard will guide you through device selection and analysis options.

Author: FlowSpec VPN Diagnostic Tool
Version: 3.0.0 - Enhanced with IPv6, Dependency Detection, Multi-Device Support
Branch Reference: easraf/flowspec_vpn/wbox_side

New in v3.0:
  - IPv6 FlowSpec local-policy and BGP checks (parallel to IPv4)
  - Dependency detection with fix suggestions
  - Multi-device parallel analysis with ThreadPoolExecutor
  - Configuration generator for missing FlowSpec components
  - Enhanced menu with new options [9], [A], [C]
"""

import os
import sys
import json
import time
import signal
import subprocess
import re
import base64
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try to import rich for beautiful output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.tree import Tree
    from rich.live import Live
    from rich.columns import Columns
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.markdown import Markdown
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║  Warning: 'rich' library not installed.                        ║")
    print("║  Install with: pip install rich                                ║")
    print("║  Running in basic mode...                                      ║")
    print("╚════════════════════════════════════════════════════════════════╝")

# Configuration
WIZARD_DIR = Path("/home/dn/SCALER/FLOWSPEC_VPN/wizard_data")
LOG_FILE = WIZARD_DIR / "fsvpn_wizard.log"
SNAPSHOTS_DIR = WIZARD_DIR / "snapshots"
MONITOR_DIR = Path("/home/dn/SCALER/FLOWSPEC_VPN/monitor_data")
MONITOR_SNAPSHOTS_DIR = MONITOR_DIR / "snapshots" if MONITOR_DIR.exists() else None
DEVICES_FILE = Path("/home/dn/SCALER/db/devices.json")
CACHE_MAX_AGE_SECONDS = 300  # 5 minutes - consider cache stale after this

# Ensure directories exist
WIZARD_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOTS_DIR.mkdir(exist_ok=True)

# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.FileHandler(LOG_FILE)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

# Initialize console
console = Console() if RICH_AVAILABLE else None


class CheckStatus(Enum):
    """Status for each check point"""
    PASS = "✓"
    FAIL = "✗"
    WARN = "⚠"
    INFO = "ℹ"
    SKIP = "○"


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


class DeviceRole(Enum):
    """Device role in FlowSpec topology"""
    PE = "PE"           # Provider Edge - has services (VRF, L2VPN, EVPN)
    P = "P"             # Provider/Core - has BGP but no services, not RR
    RR = "RR"           # Route Reflector - has route-reflector-client config
    CE = "CE"           # Customer Edge - originates FlowSpec (rare)
    UNKNOWN = "?"       # Unknown role (no BGP config)


@dataclass
class DeviceInfo:
    """Enhanced device info with role and FlowSpec status"""
    hostname: str
    ip: str
    role: DeviceRole = DeviceRole.UNKNOWN
    flowspec_enabled: bool = False
    flowspec_vpn_enabled: bool = False
    bgp_asn: int = 0
    cluster_id: str = ""
    rr_clients: List[str] = field(default_factory=list)
    bgp_neighbors: List[Dict] = field(default_factory=list)
    profile: str = ""


@dataclass
class BGPRouteInfo:
    """BGP route advertisement/reception info"""
    neighbor_ip: str
    neighbor_hostname: str = ""
    direction: str = ""  # "advertised" or "received"
    afi_safi: str = ""   # e.g., "ipv4-flowspec-vpn"
    route_count: int = 0
    routes: List[Dict] = field(default_factory=list)
    

@dataclass
class DependencyIssue:
    """Represents a missing or misconfigured dependency"""
    component: str
    issue: str
    severity: str  # "critical", "warning", "info"
    fix_command: str
    fix_description: str
    detected_in: str = ""  # Command that detected the issue


@dataclass
class FlowSpecRule:
    """Represents a FlowSpec rule through the system"""
    nlri: str
    nlri_hex: str = ""
    source: str = ""  # "BGP" or "LOCAL"
    vrf_name: str = ""
    vrf_id: int = -1  # -1 = unknown, 0 = default, >0 = specific VRF
    vrf_scope: str = ""  # "default", "specific", "all"
    rd: str = ""
    rt: str = ""
    action: str = ""
    # Priority (CRITICAL: lower = higher precedence = WINS!)
    priority: int = -1  # -1 = unknown
    priority_range: str = ""  # "LOCAL (0-2M)" or "BGP (2M-4M)"
    # Control plane
    bgp_received: bool = False
    bgp_imported_to_vrf: bool = False
    zebra_installed: bool = False
    fpm_sent: bool = False
    # Data plane
    dp_received: bool = False
    dp_supported: bool = False  # support=0 means supported
    dp_installed: bool = False
    dp_tcam_error: bool = False
    # xray fields
    index: int = 0
    support_state: int = -1  # 0=supported, 1=unsupported
    # Rate limit policer
    has_policer: bool = False
    policer_rate_bps: int = 0
    # Counters
    match_packets: int = 0
    match_bytes: int = 0
    
    def get_priority_display(self) -> str:
        """Return human-readable priority info"""
        if self.priority < 0:
            return "Unknown"
        elif self.priority < 2000000:
            return f"{self.priority:,} (LOCAL - WINS)"
        else:
            return f"{self.priority:,} (BGP)"
    
    def would_win_against(self, other: 'FlowSpecRule') -> bool:
        """Check if this rule would win against another (lower priority wins)"""
        if self.priority < 0 or other.priority < 0:
            return False
        return self.priority < other.priority


# Priority constants (from FlowspecRuleData.hpp)
FLOWSPEC_LOCAL_PRIORITY_MIN = 0
FLOWSPEC_LOCAL_PRIORITY_MAX = 1999999
FLOWSPEC_BGP_PRIORITY_MIN = 2000000
FLOWSPEC_BGP_PRIORITY_MAX = 4000000


def extract_ncp_from_interface(interface_name: str) -> Optional[int]:
    """
    Extract NCP number from interface name.
    
    Interface naming convention: ge<speed>-<NCP>/<slot>/<port>[.<subif>]
    Examples:
        ge100-18/0/0      -> NCP 18
        ge400-5/0/1.100   -> NCP 5
        ge100-0/0/0       -> NCP 0
        bundle-1.200      -> None (bundles don't have NCP in name)
        irb1              -> None (IRB doesn't have NCP in name)
        lo0               -> None (loopback doesn't have NCP in name)
    
    Returns:
        NCP number if found, None otherwise
    """
    # Match pattern: ge<speed>-<NCP>/ or similar
    # ge100-18/0/0, ge400-5/0/1.100, etc.
    match = re.match(r'ge\d+-(\d+)/', interface_name)
    if match:
        return int(match.group(1))
    
    # Also check for other physical interfaces with similar pattern
    # e.g., xe100-5/0/0 (10G), ce100-5/0/0 (100G)
    match = re.match(r'[a-z]+\d+-(\d+)/', interface_name)
    if match:
        return int(match.group(1))
    
    return None


def extract_ncps_from_interfaces(interfaces: List[str]) -> List[int]:
    """
    Extract unique NCP numbers from a list of interface names.
    
    Args:
        interfaces: List of interface names (e.g., ['ge100-18/0/0', 'ge100-18/0/1.100'])
    
    Returns:
        Sorted list of unique NCP numbers
    """
    ncps = set()
    for iface in interfaces:
        ncp = extract_ncp_from_interface(iface)
        if ncp is not None:
            ncps.add(ncp)
    return sorted(ncps)


def get_ncp_container_name(ncp_num: int) -> str:
    """
    Get the container name for an NCP.
    
    Args:
        ncp_num: NCP number (e.g., 0, 18, 5)
    
    Returns:
        Container name (e.g., 'ncp0', 'ncp18', 'ncp5')
    """
    return f"ncp{ncp_num}"


def parse_xray_rules(output: str, source: str = "BGP") -> List[FlowSpecRule]:
    """Parse xraycli rules output into FlowSpecRule objects"""
    rules = []
    
    # Split by entries (each entry starts with "index:")
    entries = re.split(r'(?=index:\s*\d+)', output)
    
    for entry in entries:
        if not entry.strip() or 'index:' not in entry:
            continue
        
        rule = FlowSpecRule(nlri="", source=source)
        
        # Parse index
        idx_match = re.search(r'index:\s*(\d+)', entry)
        if idx_match:
            rule.index = int(idx_match.group(1))
        
        # Parse NLRI (hex)
        nlri_match = re.search(r'nlri:\s*([0-9a-fA-F]+)', entry)
        if nlri_match:
            rule.nlri_hex = nlri_match.group(1)
        
        # Parse NLRI readable
        nlri_readable_match = re.search(r'nlri_readable:\s*([^\n]+)', entry)
        if nlri_readable_match:
            rule.nlri = nlri_readable_match.group(1).strip()
        
        # Parse priority (CRITICAL!)
        priority_match = re.search(r'priority:\s*(\d+)', entry)
        if priority_match:
            rule.priority = int(priority_match.group(1))
            if rule.priority < FLOWSPEC_BGP_PRIORITY_MIN:
                rule.priority_range = "LOCAL (0-2M) - WINS"
                rule.source = "LOCAL"
            else:
                rule.priority_range = "BGP (2M-4M)"
                rule.source = "BGP"
        
        # Parse support state (0=supported, 1=unsupported)
        support_match = re.search(r'support:\s*(\d+)', entry)
        if support_match:
            rule.support_state = int(support_match.group(1))
            rule.dp_supported = (rule.support_state == 0)
        
        # Parse rate limit policer
        if 'rate_limit_policer_enabled: true' in entry.lower() or 'rate_limit_policer_enabled: 1' in entry:
            rule.has_policer = True
            rate_match = re.search(r'rate_limit_policer_rate_bytes:\s*(\d+)', entry)
            if rate_match:
                rule.policer_rate_bps = int(rate_match.group(1))
        
        # Only add if we have meaningful data
        if rule.nlri or rule.nlri_hex:
            rules.append(rule)
    
    return rules


def analyze_priority_conflicts(bgp_rules: List[FlowSpecRule], local_rules: List[FlowSpecRule]) -> List[Dict]:
    """Analyze priority conflicts between BGP and Local Policy rules"""
    conflicts = []
    
    for bgp_rule in bgp_rules:
        for local_rule in local_rules:
            # Check for overlapping destination prefixes
            bgp_dst = re.search(r'DstPrefix:=([^\s,]+)', bgp_rule.nlri or "")
            local_dst = re.search(r'DstPrefix:=([^\s,]+)', local_rule.nlri or "")
            
            if bgp_dst and local_dst:
                bgp_prefix = bgp_dst.group(1)
                local_prefix = local_dst.group(1)
                
                # Simple overlap check (exact match for now)
                if bgp_prefix == local_prefix:
                    winner = "LOCAL" if local_rule.priority < bgp_rule.priority else "BGP"
                    conflicts.append({
                        "bgp_rule": bgp_rule,
                        "local_rule": local_rule,
                        "prefix": bgp_prefix,
                        "bgp_priority": bgp_rule.priority,
                        "local_priority": local_rule.priority,
                        "winner": winner,
                        "reason": f"Lower priority ({local_rule.priority if winner == 'LOCAL' else bgp_rule.priority}) wins"
                    })
    
    return conflicts


@dataclass 
class DeviceAnalysis:
    """Complete analysis results for a device"""
    hostname: str
    ip: str
    timestamp: str
    dnos_version: str = ""
    checks: List[FlowCheckResult] = field(default_factory=list)
    
    # Parsed rules (detailed) - IPv4
    bgp_rules: List[FlowSpecRule] = field(default_factory=list)
    local_rules: List[FlowSpecRule] = field(default_factory=list)
    priority_conflicts: List[Dict] = field(default_factory=list)
    
    # Parsed rules (detailed) - IPv6 (NEW)
    bgp_rules_ipv6: List[FlowSpecRule] = field(default_factory=list)
    local_rules_ipv6: List[FlowSpecRule] = field(default_factory=list)
    priority_conflicts_ipv6: List[Dict] = field(default_factory=list)
    
    # BGP FlowSpec summaries - IPv4
    bgp_total: int = 0
    bgp_installed: int = 0
    bgp_unsupported: int = 0
    bgp_tcam_errors: int = 0
    
    # BGP FlowSpec summaries - IPv6 (NEW)
    bgp_total_ipv6: int = 0
    bgp_installed_ipv6: int = 0
    bgp_unsupported_ipv6: int = 0
    bgp_tcam_errors_ipv6: int = 0
    
    # Local Policies summaries - IPv4
    lp_total: int = 0
    lp_installed: int = 0
    lp_unsupported: int = 0
    lp_tcam_errors: int = 0
    
    # Local Policies summaries - IPv6 (NEW)
    lp_total_ipv6: int = 0
    lp_installed_ipv6: int = 0
    lp_unsupported_ipv6: int = 0
    lp_tcam_errors_ipv6: int = 0
    
    # Combined TCAM
    ipv4_capacity: int = 12000
    ipv4_used: int = 0
    ipv6_capacity: int = 4000
    ipv6_used: int = 0
    tcam_full: bool = False
    
    # HW counters
    hw_rules_write_ok: int = 0
    hw_rules_write_fail: int = 0
    hw_policers_write_ok: int = 0
    hw_policers_write_fail: int = 0
    
    # BCM PMF entries
    bcm_pmf_entries: int = 0
    
    # BGP Traces (for flowchart display)
    bgp_trace_updates_rcvd: int = 0
    bgp_trace_updates_sent: int = 0
    bgp_trace_errors: int = 0
    bgp_trace_last_activity: str = ""
    bgp_trace_neighbors: List[str] = field(default_factory=list)
    
    # Legacy fields for compatibility
    total_rules: int = 0
    rules_installed: int = 0
    rules_failed: int = 0
    tcam_errors: int = 0
    hw_write_failures: int = 0
    vrf_count: int = 0
    
    # Dependency issues (NEW)
    dependency_issues: List[DependencyIssue] = field(default_factory=list)
    
    # FlowSpec interfaces and NCPs (NEW - for cluster support)
    flowspec_interfaces: List[str] = field(default_factory=list)
    flowspec_ncps: List[int] = field(default_factory=list)  # Detected NCP numbers from interface names
    is_standalone: bool = True  # True = SA (always NCP 0), False = Cluster (detect NCPs from interfaces)
    
    # Issues
    problems: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info_messages: List[str] = field(default_factory=list)


class SSHConnection:
    """SSH connection to a device"""
    
    def __init__(self, hostname: str, ip: str, username: str = "dnroot", password: str = "dnroot"):
        self.hostname = hostname
        self.ip = ip
        self.username = username
        self.password = password
    
    def run_cli_command(self, command: str, timeout: int = 15) -> Tuple[bool, str]:
        """Run a DNOS CLI command"""
        try:
            import pexpect
            ssh_cmd = f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {self.username}@{self.ip}"
            child = pexpect.spawn(ssh_cmd, timeout=timeout)
            
            i = child.expect(['password:', 'Password:', pexpect.TIMEOUT, pexpect.EOF], timeout=15)
            if i in [0, 1]:
                child.sendline(self.password)
            elif i == 2:
                return False, "Connection timeout"
            elif i == 3:
                return False, "Connection closed"
            
            child.expect(['#', '>'], timeout=15)
            child.sendline(command)
            child.expect(['#', '>'], timeout=timeout)
            
            output = child.before.decode('utf-8', errors='replace')
            child.sendline('exit')
            child.close()
            
            return True, output
            
        except ImportError:
            return False, "pexpect library not installed. Install with: pip install pexpect"
        except Exception as e:
            return False, str(e)
    
    def run_xray_command(self, xray_path: str, ncp_id: int = 0, timeout: int = 30) -> Tuple[bool, str]:
        """
        Run xraycli command via interactive NCP shell.
        
        DNOS syntax:
            1. run start shell ncp <id>  -> enters datapath shell
            2. xraycli <path>            -> run xray command
            3. exit                      -> return to CLI
        
        Args:
            xray_path: xraycli path (e.g., "/wb_agent/flowspec/bgp/ipv4/info")
            ncp_id: NCP ID (default 0 for SA devices)
            timeout: Command timeout in seconds
        
        Returns:
            Tuple of (success, output)
        """
        try:
            import pexpect
            ssh_cmd = f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {self.username}@{self.ip}"
            child = pexpect.spawn(ssh_cmd, timeout=timeout)
            
            # Login
            i = child.expect(['password:', 'Password:', pexpect.TIMEOUT, pexpect.EOF], timeout=15)
            if i in [0, 1]:
                child.sendline(self.password)
            elif i == 2:
                return False, "Connection timeout"
            elif i == 3:
                return False, "Connection closed"
            
            # Wait for CLI prompt
            child.expect(['#', '>'], timeout=15)
            
            # Enter NCP shell: "run start shell ncp <id>"
            child.sendline(f"run start shell ncp {ncp_id}")
            
            # Wait for shell prompt (root@datapath:/# or similar)
            i = child.expect(['root@', 'datapath', '/#', pexpect.TIMEOUT], timeout=15)
            if i == 3:
                # Timeout - might not have entered shell
                child.sendline('exit')
                child.close()
                return False, "Failed to enter NCP shell"
            
            # Wait for actual prompt
            child.expect(['#', '$'], timeout=5)
            
            # Run xraycli command
            child.sendline(f"xraycli {xray_path}")
            
            # Wait for output and prompt
            child.expect(['#', '$'], timeout=timeout)
            output = child.before.decode('utf-8', errors='replace')
            
            # Exit shell back to CLI
            child.sendline('exit')
            child.expect(['#', '>'], timeout=10)
            
            # Exit CLI
            child.sendline('exit')
            child.close()
            
            return True, output
            
        except ImportError:
            return False, "pexpect library not installed"
        except Exception as e:
            return False, f"Shell error: {str(e)}"
    
    def run_ncc_shell_command(self, shell_cmd: str, ncc_id: int = 0, timeout: int = 30) -> Tuple[bool, str]:
        """
        Run a shell command on NCC (routing-engine container).
        
        DNOS syntax:
            1. run start shell ncc <id>  -> enters NCC shell
            2. <shell_cmd>               -> run shell command
            3. exit                      -> return to CLI
        
        Useful for:
            - tail /var/log/bgpd_traces
            - tail /var/log/rib-manager_traces
            - tail /var/log/fib-manager_traces
        
        Args:
            shell_cmd: Shell command to run (e.g., "tail -200 /var/log/bgpd_traces")
            ncc_id: NCC ID (default 0)
            timeout: Command timeout in seconds
        
        Returns:
            Tuple of (success, output)
        """
        try:
            import pexpect
            ssh_cmd = f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {self.username}@{self.ip}"
            child = pexpect.spawn(ssh_cmd, timeout=timeout)
            
            # Login
            i = child.expect(['password:', 'Password:', pexpect.TIMEOUT, pexpect.EOF], timeout=15)
            if i in [0, 1]:
                child.sendline(self.password)
            elif i == 2:
                return False, "Connection timeout"
            elif i == 3:
                return False, "Connection closed"
            
            # Wait for CLI prompt
            child.expect(['#', '>'], timeout=15)
            
            # Enter NCC shell
            child.sendline(f"run start shell ncc {ncc_id}")
            
            # Wait for shell prompt (root@routing-engine:/# or similar)
            i = child.expect(['root@', 'routing-engine', '/#', pexpect.TIMEOUT], timeout=15)
            if i == 3:
                child.sendline('exit')
                child.close()
                return False, "Failed to enter NCC shell"
            
            child.expect(['#', '$'], timeout=5)
            
            # Run shell command
            child.sendline(shell_cmd)
            
            # Wait for output
            child.expect(['#', '$'], timeout=timeout)
            output = child.before.decode('utf-8', errors='replace')
            
            # Exit shell and CLI
            child.sendline('exit')
            child.expect(['#', '>'], timeout=10)
            child.sendline('exit')
            child.close()
            
            return True, output
            
        except ImportError:
            return False, "pexpect library not installed"
        except Exception as e:
            return False, f"Shell error: {str(e)}"
    
    def run_wbox_command(self, wbox_cmd: str, ncp_id: int = 0, timeout: int = 30) -> Tuple[bool, str]:
        """
        Run wbox-cli command via interactive NCP shell.
        
        DNOS syntax:
            1. run start shell ncp <id>  -> enters datapath shell
            2. wbox-cli <command>        -> run wbox command
            3. exit                      -> return to CLI
        
        Args:
            wbox_cmd: wbox-cli command (e.g., "bcm diag field entry list group=24")
            ncp_id: NCP ID (default 0 for SA devices)
            timeout: Command timeout in seconds
        
        Returns:
            Tuple of (success, output)
        """
        try:
            import pexpect
            ssh_cmd = f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {self.username}@{self.ip}"
            child = pexpect.spawn(ssh_cmd, timeout=timeout)
            
            # Login
            i = child.expect(['password:', 'Password:', pexpect.TIMEOUT, pexpect.EOF], timeout=15)
            if i in [0, 1]:
                child.sendline(self.password)
            elif i == 2:
                return False, "Connection timeout"
            elif i == 3:
                return False, "Connection closed"
            
            # Wait for CLI prompt
            child.expect(['#', '>'], timeout=15)
            
            # Enter NCP shell
            child.sendline(f"run start shell ncp {ncp_id}")
            
            # Wait for shell prompt
            i = child.expect(['root@', 'datapath', '/#', pexpect.TIMEOUT], timeout=15)
            if i == 3:
                child.sendline('exit')
                child.close()
                return False, "Failed to enter NCP shell"
            
            child.expect(['#', '$'], timeout=5)
            
            # Run wbox-cli command
            child.sendline(f"wbox-cli {wbox_cmd}")
            
            # Wait for output
            child.expect(['#', '$'], timeout=timeout)
            output = child.before.decode('utf-8', errors='replace')
            
            # Exit shell and CLI
            child.sendline('exit')
            child.expect(['#', '>'], timeout=10)
            child.sendline('exit')
            child.close()
            
            return True, output
            
        except ImportError:
            return False, "pexpect library not installed"
        except Exception as e:
            return False, f"Shell error: {str(e)}"


class FSVPNWizard:
    """Main FlowSpec VPN Wizard class"""
    
    def __init__(self):
        self.devices: List[Dict] = []
        self.console = console
        self.selected_device: Optional[Dict] = None
        self.current_analysis: Optional[DeviceAnalysis] = None
        
    def log(self, msg: str):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {msg}"
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    
    def detect_device_type(self, conn: 'SSHConnection') -> bool:
        """
        Detect if device is Standalone (SA) or Cluster.
        
        SA devices always use NCP 0, so no need to parse interface names.
        Cluster devices need NCP detection from interface names.
        
        Detection method: Check if any interface has a non-zero NCP number,
        or check the platform/NCF count.
        
        Returns:
            True if Standalone (SA), False if Cluster
        """
        # Quick check: look for interfaces with non-zero NCP numbers
        # SA interfaces look like: ge100-0/0/0, ge400-0/0/1
        # Cluster interfaces look like: ge100-18/0/0, ge400-5/0/1
        cmd = "show interfaces brief | include 'ge|xe|ce|et'"
        success, output = conn.run_cli_command(cmd, timeout=10)
        
        if success:
            # Look for any interface with NCP > 0
            # Pattern: ge<speed>-<NCP>/ where NCP > 0
            for line in output.split('\n'):
                match = re.search(r'[gxce]e?\d+-(\d+)/', line)
                if match:
                    ncp_num = int(match.group(1))
                    if ncp_num > 0:
                        # Found a non-zero NCP, this is a Cluster
                        return False
        
        # Default: assume Standalone
        return True
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def print_banner(self):
        """Print wizard banner"""
        if RICH_AVAILABLE:
            console.print()
            console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
            console.print("[bold cyan]                      FSVPN-WIZARD[/bold cyan]")
            console.print("[dim]         FlowSpec VPN Diagnostic & Monitoring Wizard[/dim]")
            console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
            console.print()
            console.print("  [green]✓[/green] BGP FlowSpec-VPN Session & Route Analysis")
            console.print("  [green]✓[/green] VRF Import Verification (RT Matching)")
            console.print("  [green]✓[/green] Datapath Installation Check (NCP/TCAM)")
            console.print("  [green]✓[/green] Local Policies (match-classes, policies, counters)")
            console.print("  [green]✓[/green] Container Trace Extraction (NCC/NCP)")
            console.print()
            console.print("[bold yellow]Priority Rules:[/bold yellow]")
            console.print("  [green]★ LOCAL (0-2M)[/green] = WINS (lower # = higher precedence)")
            console.print("  [blue]  BGP (2M-4M)[/blue]   = Loses to local policies")
            console.print()
            console.print("[dim]VRF-ID: 0=Default VRF | No field=ALL VRFs | >0=Specific VRF[/dim]")
            console.print()
        else:
            print("=" * 80)
            print("                         FSVPN-WIZARD")
            print("          FlowSpec VPN Diagnostic & Monitoring Wizard")
            print("=" * 80)
            print()
            print("VRF-ID Semantics:")
            print("  • VRF-ID = 0     → Default VRF (valid)")
            print("  • No VRF field   → ALL VRFs (global rule)")
            print("  • VRF-ID > 0     → Specific VRF")
            print()
    
    def discover_devices(self) -> List[Dict]:
        """Discover devices from config file with role detection"""
        if DEVICES_FILE.exists():
            try:
                with open(DEVICES_FILE) as f:
                    data = json.load(f)
                
                # Handle format: {"devices": [...]} or [...]
                if isinstance(data, dict) and "devices" in data:
                    raw_devices = data["devices"]
                elif isinstance(data, list):
                    raw_devices = data
                else:
                    raw_devices = [data]
                
                # Decode base64 passwords and normalize
                self.devices = []
                for dev in raw_devices:
                    device = dict(dev)
                    
                    # Decode base64 password
                    if device.get("password"):
                        try:
                            decoded = base64.b64decode(device["password"]).decode('utf-8')
                            device["password"] = decoded
                        except:
                            pass
                    
                    # Normalize IP field
                    if not device.get("ip") and device.get("management_ip"):
                        device["ip"] = device["management_ip"]
                    
                    # Detect role from operational.json
                    device["role"] = self._detect_device_role(device.get("hostname", ""))
                    device["flowspec_status"] = self._get_flowspec_status(device.get("hostname", ""))
                    
                    self.devices.append(device)
                
                return self.devices
            except Exception as e:
                self.log(f"Error loading devices: {e}")
        
        return []
    
    def _detect_device_role(self, hostname: str) -> str:
        """
        Detect device role from actual BGP and service configuration.
        
        Role definitions:
        - RR: Has 'route-reflector-client' in BGP config (reflects routes to clients)
        - PE: Has services (VRF, L2VPN, EVPN, network-services) - customer-facing
        - P:  Has BGP but no services and not an RR - core/transit router
        - ?: No BGP configuration found
        
        Returns:
            "RR" - Route Reflector
            "PE" - Provider Edge (has services)
            "P"  - Provider/Core (has BGP, no services)
            "?" - Unknown (no BGP config)
        """
        has_bgp = False
        is_rr = False
        has_services = False
        
        try:
            config_file = Path(f"/home/dn/SCALER/db/configs/{hostname}/running.txt")
            if config_file.exists():
                config = config_file.read_text()
                
                # ═══════════════════════════════════════════════════════════
                # CHECK FOR BGP CONFIGURATION
                # ═══════════════════════════════════════════════════════════
                import re
                
                # Check for BGP protocol block
                if re.search(r'protocols\s+bgp', config) or re.search(r'neighbor\s+\d+\.\d+\.\d+\.\d+', config):
                    has_bgp = True
                    self.log(f"  {hostname}: Has BGP configuration")
                
                # ═══════════════════════════════════════════════════════════
                # ROUTE REFLECTOR CHECK (definitive)
                # ═══════════════════════════════════════════════════════════
                
                # RR configures neighbors as route-reflector-client
                if "route-reflector-client" in config:
                    is_rr = True
                    self.log(f"  {hostname}: Has route-reflector-client → RR")
                
                # cluster-id is also a strong RR indicator
                if re.search(r'cluster-id\s+\d+', config):
                    is_rr = True
                    self.log(f"  {hostname}: Has cluster-id → RR")
                
                # ═══════════════════════════════════════════════════════════
                # SERVICE CHECK (PE indicator)
                # ═══════════════════════════════════════════════════════════
                
                # VRFs indicate PE (customer services)
                if re.search(r'network-services\s+vrf\s+\S+', config):
                    has_services = True
                    self.log(f"  {hostname}: Has VRF → PE")
                
                # L2VPN services (VPWS, VPLS, FXC)
                if re.search(r'l2vpn', config):
                    has_services = True
                    self.log(f"  {hostname}: Has L2VPN → PE")
                
                # EVPN services
                if re.search(r'evpn\s+', config, re.IGNORECASE):
                    has_services = True
                    self.log(f"  {hostname}: Has EVPN → PE")
                
                # FlowSpec enabled on interfaces (applies rules = PE)
                if "flowspec enabled" in config:
                    has_services = True
                    self.log(f"  {hostname}: Has flowspec enabled on interface → PE")
                
                # PWHE interfaces (pseudowire headend = PE)
                if re.search(r'pwhe-\d+', config):
                    has_services = True
                    self.log(f"  {hostname}: Has PWHE interfaces → PE")
                
                # Check address-families that indicate PE role
                # VPN AFIs (ipv4-vpn, ipv6-vpn, flowspec-vpn) suggest PE
                if re.search(r'address-family\s+ipv[46]-vpn', config):
                    has_services = True
                    self.log(f"  {hostname}: Has VPN address-family → PE")
                
                if re.search(r'address-family\s+ipv[46]-flowspec-vpn', config):
                    has_services = True
                    self.log(f"  {hostname}: Has FlowSpec-VPN address-family → PE")
            
            # ═══════════════════════════════════════════════════════════
            # DECISION LOGIC
            # ═══════════════════════════════════════════════════════════
            
            # Priority 1: RR (has route-reflector-client)
            if is_rr:
                return "RR"
            
            # Priority 2: PE (has services)
            if has_services:
                return "PE"
            
            # Priority 3: P (has BGP but no services)
            if has_bgp:
                return "P"
            
            # No BGP config = unknown
            self.log(f"  {hostname}: No BGP config found, role unknown")
            return "?"
            
        except Exception as e:
            self.log(f"Error detecting role for {hostname}: {e}")
        
        return "?"
    
    def _get_flowspec_status(self, hostname: str) -> Dict[str, bool]:
        """Get FlowSpec configuration status from cached config"""
        status = {"flowspec": False, "flowspec_vpn": False, "local_policy": False}
        
        try:
            config_file = Path(f"/home/dn/SCALER/db/configs/{hostname}/running.txt")
            if config_file.exists():
                config = config_file.read_text()
                
                # Check for FlowSpec AFIs in BGP
                if "address-family ipv4-flowspec" in config:
                    status["flowspec"] = True
                if "address-family ipv4-flowspec-vpn" in config:
                    status["flowspec_vpn"] = True
                
                # Check for local policies
                if "flowspec-local-policies" in config:
                    status["local_policy"] = True
                
                # Check for flowspec enabled on interfaces
                if "flowspec enabled" in config:
                    status["interface_enabled"] = True
        except Exception:
            pass
        
        return status
    
    def connect_to_device(self, device: Dict) -> SSHConnection:
        """Create SSH connection to device"""
        return SSHConnection(
            hostname=device.get("hostname", "unknown"),
            ip=device.get("ip", device.get("management_ip", "")),
            username=device.get("username", "dnroot"),
            password=device.get("password", "dnroot")
        )
    
    # =========================================================================
    # WIZARD MENUS
    # =========================================================================
    
    def show_main_menu(self) -> str:
        """Show main menu and get selection"""
        if RICH_AVAILABLE:
            menu = """
[bold cyan]Main Menu[/bold cyan]

  [1] 🔍 [bold]Full Analysis[/bold]         - Complete FlowSpec VPN flow analysis (IPv4 + IPv6)
  [2] 📊 [bold]Quick Check[/bold]           - Fast status overview
  [3] 📋 [bold]All Rules[/bold]             - Show all installed FlowSpec rules (show flowspec)
  [4] 📜 [bold]Extract Traces[/bold]        - Get traces from containers
  [5] 🔬 [bold]NLRI Trace[/bold]            - Trace specific NLRI through BGP → NCP → Counters
  [6] ⚙️  [bold]Change Device[/bold]         - Select different device
  [7] 💾 [bold]Save Report[/bold]           - Save analysis to file
  [8] 📚 [bold]SAFI 133/134 Guide[/bold]    - Explain FlowSpec vs FlowSpec-VPN
  [9] 🔧 [bold]Dependency Check[/bold]      - Find missing configuration
  [A] 🌐 [bold]Multi-Device Analysis[/bold] - Analyze all devices in parallel
  [P] 🛤️  [bold]Path Trace[/bold]            - Trace FlowSpec routes RR→PE with advertised/received
  [T] 🧪 [bold]TP RUN[/bold]                - Run Test Plan verification tests
  [V] 📊 [bold]Verbose View[/bold]          - Show detailed flow diagram and full table
  
  [B] ← Back to device selection
  [Q] Exit wizard
"""
            console.print(Panel(menu, title="Options", border_style="blue"))
            choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "A", "p", "P", "t", "T", "v", "V", "b", "B", "q", "Q"], default="1")
        else:
            print("\nMain Menu:")
            print("  [1] Full Analysis (IPv4 + IPv6)")
            print("  [2] Quick Check")
            print("  [3] All Rules (show flowspec)")
            print("  [4] Extract Traces")
            print("  [5] NLRI Trace (trace specific rule)")
            print("  [6] Change Device")
            print("  [7] Save Report")
            print("  [8] SAFI 133/134 Guide")
            print("  [9] Dependency Check")
            print("  [P] Path Trace (RR→PE routes)")
            print("  [A] Multi-Device Analysis (NEW)")
            print("  [T] TP RUN - Run Test Plan verification tests (NEW)")
            print("  [B] Back")
            print("  [Q] Quit")
            choice = input("\nSelect option [1]: ").strip() or "1"
        
        return choice.lower()
    
    def show_device_selection(self) -> Optional[Dict]:
        """Show device selection menu with role detection and multi-select"""
        devices = self.discover_devices()
        
        if not devices:
            if RICH_AVAILABLE:
                console.print("[yellow]No devices found in configuration.[/yellow]")
                if Confirm.ask("Enter device manually?", default=True):
                    ip = Prompt.ask("Device IP address")
                    hostname = Prompt.ask("Hostname", default="PE-1")
                    username = Prompt.ask("Username", default="dnroot")
                    password = Prompt.ask("Password", default="dnroot", password=True)
                    role = Prompt.ask("Role", choices=["PE", "RR", "?"], default="PE")
                    return {"hostname": hostname, "ip": ip, "username": username, "password": password, "role": role}
            else:
                print("No devices found. Enter manually:")
                ip = input("Device IP: ")
                hostname = input("Hostname [PE-1]: ") or "PE-1"
                return {"hostname": hostname, "ip": ip, "username": "dnroot", "password": "dnroot", "role": "?"}
            return None
        
        # Display device list with roles
        if RICH_AVAILABLE:
            table = Table(title="🔍 Available Devices - FlowSpec Topology", box=box.ROUNDED)
            table.add_column("#", style="cyan", width=4)
            table.add_column("Hostname", style="green")
            table.add_column("Role", style="bold", width=6)
            table.add_column("IP/Host", style="yellow")
            table.add_column("FlowSpec", style="dim", width=20)
            table.add_column("Description", style="dim")
            
            for i, dev in enumerate(devices, 1):
                description = dev.get("description") or ""
                role = dev.get("role", "?")
                fs_status = dev.get("flowspec_status", {})
                
                # Role styling
                if role == "RR":
                    role_display = "[bold magenta]RR[/bold magenta]"
                elif role == "PE":
                    role_display = "[bold cyan]PE[/bold cyan]"
                elif role == "P":
                    role_display = "[yellow]P[/yellow]"
                else:
                    role_display = "[dim]?[/dim]"
                
                # FlowSpec status
                fs_parts = []
                if fs_status.get("flowspec"):
                    fs_parts.append("[green]FS[/green]")
                if fs_status.get("flowspec_vpn"):
                    fs_parts.append("[green]FS-VPN[/green]")
                if fs_status.get("local_policy"):
                    fs_parts.append("[yellow]LP[/yellow]")
                fs_display = " ".join(fs_parts) if fs_parts else "[dim]Not configured[/dim]"
                
                table.add_row(
                    str(i),
                    dev.get("hostname", "unknown"),
                    role_display,
                    dev.get("ip", "N/A"),
                    fs_display,
                    description[:30]
                )
            
            console.print(table)
            console.print()
            console.print("[bold]Legend:[/bold] [magenta]RR[/magenta]=Route Reflector  [cyan]PE[/cyan]=Provider Edge  [yellow]P[/yellow]=Core Router  [dim]?[/dim]=No BGP")
            console.print("        [green]FS[/green]=FlowSpec  [green]FS-VPN[/green]=FlowSpec-VPN  [yellow]LP[/yellow]=Local Policy")
            console.print()
            console.print("  [bold][A][/bold] Analyze ALL devices (parallel)")
            console.print("  [bold][S][/bold] Select MULTIPLE devices (e.g., 1,2,4)")
            console.print("  [bold][P][/bold] Trace FlowSpec PATH (RR→PE flow)")
            console.print("  [bold][E][/bold] Edit device (rename/change IP)")
            console.print("  [bold][M][/bold] Enter device manually")
            console.print("  [bold][Q][/bold] Quit")
            
            choice = Prompt.ask("\nSelect device or option", default="1")
        else:
            print("\nAvailable Devices:")
            for i, dev in enumerate(devices, 1):
                role = dev.get("role", "?")
                print(f"  [{i}] {dev.get('hostname', 'unknown')} ({role}) - {dev.get('ip', 'N/A')}")
            print("  [A] Analyze ALL")
            print("  [S] Select multiple (e.g., 1,2,4)")
            print("  [P] Trace FlowSpec path")
            print("  [E] Edit device (rename/change IP)")
            print("  [M] Manual entry")
            print("  [Q] Quit")
            choice = input("\nSelect device [1]: ").strip() or "1"
        
        if choice.lower() == 'q':
            return None
        elif choice.lower() == 'a':
            return {"_all_devices": True, "devices": devices}
        elif choice.lower() == 's':
            # Multi-select mode
            return self._multi_select_devices(devices)
        elif choice.lower() == 'p':
            # Path tracing mode
            return self._select_path_tracing(devices)
        elif choice.lower() == 'e':
            # Edit device in DB
            self._edit_device_in_db(devices)
            # Refresh device list and show selection again
            return self.show_device_selection()
        elif choice.lower() == 'm':
            if RICH_AVAILABLE:
                ip = Prompt.ask("Device IP address")
                hostname = Prompt.ask("Hostname", default="Device")
                role = Prompt.ask("Role", choices=["PE", "RR", "?"], default="PE")
            else:
                ip = input("Device IP: ")
                hostname = input("Hostname: ") or "Device"
                role = "?"
            return {"hostname": hostname, "ip": ip, "username": "dnroot", "password": "dnroot", "role": role}
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(devices):
                    return devices[idx]
            except ValueError:
                pass
        
        return devices[0] if devices else None
    
    def _multi_select_devices(self, devices: List[Dict]) -> Optional[Dict]:
        """Allow user to select multiple devices for monitoring"""
        if RICH_AVAILABLE:
            console.print("\n[bold]Multi-Device Selection[/bold]")
            console.print("Enter device numbers separated by commas (e.g., 1,2,4)")
            console.print("Or enter ranges (e.g., 1-3,5)")
            selection = Prompt.ask("Devices", default="1")
        else:
            print("\nEnter device numbers (e.g., 1,2,4 or 1-3,5):")
            selection = input("Devices [1]: ").strip() or "1"
        
        selected_indices = set()
        
        # Parse selection
        for part in selection.split(","):
            part = part.strip()
            if "-" in part:
                try:
                    start, end = map(int, part.split("-"))
                    selected_indices.update(range(start - 1, end))
                except ValueError:
                    pass
            else:
                try:
                    selected_indices.add(int(part) - 1)
                except ValueError:
                    pass
        
        # Filter valid indices
        selected_devices = [devices[i] for i in sorted(selected_indices) if 0 <= i < len(devices)]
        
        if selected_devices:
            if RICH_AVAILABLE:
                console.print(f"\n[green]Selected {len(selected_devices)} devices:[/green]")
                for dev in selected_devices:
                    role = dev.get("role", "?")
                    console.print(f"  • {dev.get('hostname')} ({role})")
            return {"_multi_devices": True, "devices": selected_devices}
        
        return None
    
    def _run_multi_device_summary(self, devices_list: List[Dict]):
        """
        Run multi-device analysis with comprehensive summary.
        
        Shows:
        1. Summary table with roles, BGP, FlowSpec status
        2. Options to analyze specific devices or all
        """
        
        while True:  # Use loop instead of recursion
            if RICH_AVAILABLE:
                console.print(f"\n[bold cyan]━━━ Multi-Device FlowSpec Analysis ━━━[/bold cyan]")
                console.print(f"[dim]Gathering configuration status from {len(devices_list)} devices...[/dim]\n")
            
            # Gather detailed status for each device
            device_status = []
            
            for dev in devices_list:
                hostname = dev.get("hostname", "unknown")
                status = {
                    "hostname": hostname,
                    "ip": dev.get("ip", "N/A"),
                    "role": "?",
                    "bgp_configured": False,
                    "isis_configured": False,
                    "ldp_configured": False,
                    "flowspec": False,
                    "flowspec_vpn": False,
                    "local_policy": False,
                    "services": [],
                    "bgp_neighbors": 0,
                    "flowspec_interfaces": 0,
                }
                
                # Read running config
                config_file = Path(f"/home/dn/SCALER/db/configs/{hostname}/running.txt")
                if config_file.exists():
                    try:
                        config = config_file.read_text()
                        import re
                        
                        # BGP
                        if re.search(r'protocols\s+bgp', config) or re.search(r'neighbor\s+\d+\.\d+\.\d+\.\d+', config):
                            status["bgp_configured"] = True
                            neighbors = re.findall(r'neighbor\s+\d+\.\d+\.\d+\.\d+', config)
                            status["bgp_neighbors"] = len(set(neighbors))
                        
                        # ISIS
                        if re.search(r'protocols\s+isis', config):
                            status["isis_configured"] = True
                        
                        # LDP
                        if re.search(r'protocols\s+ldp', config):
                            status["ldp_configured"] = True
                        
                        # Route Reflector
                        if "route-reflector-client" in config or re.search(r'cluster-id\s+\d+', config):
                            status["role"] = "RR"
                        
                        # Services (PE indicators)
                        services = []
                        if re.search(r'network-services\s+vrf\s+\S+', config):
                            vrf_count = len(re.findall(r'network-services\s+vrf\s+\S+', config))
                            services.append(f"VRF({vrf_count})")
                        if re.search(r'l2vpn', config):
                            services.append("L2VPN")
                        if re.search(r'evpn\s+', config, re.IGNORECASE):
                            services.append("EVPN")
                        
                        status["services"] = services
                        
                        if services and status["role"] != "RR":
                            status["role"] = "PE"
                        elif status["bgp_configured"] and status["role"] == "?":
                            status["role"] = "P"  # Has BGP but no services = P router
                        
                        # FlowSpec
                        if "address-family ipv4-flowspec" in config or "address-family ipv6-flowspec" in config:
                            status["flowspec"] = True
                        if "address-family ipv4-flowspec-vpn" in config or "address-family ipv6-flowspec-vpn" in config:
                            status["flowspec_vpn"] = True
                        if "flowspec-local-policies" in config:
                            status["local_policy"] = True
                        
                        # FlowSpec interfaces
                        fs_ifaces = len(re.findall(r'flowspec enabled', config))
                        status["flowspec_interfaces"] = fs_ifaces
                        
                    except Exception as e:
                        self.log(f"Error reading config for {hostname}: {e}")
                
                device_status.append(status)
            
            # Display summary table
            if RICH_AVAILABLE:
                table = Table(title="📊 Device Configuration Summary", box=box.ROUNDED)
                table.add_column("#", style="cyan", width=3)
                table.add_column("Hostname", style="green")
                table.add_column("Role", style="bold", width=4)
                table.add_column("IP", style="dim")
                table.add_column("IGP", style="dim", width=8)
                table.add_column("BGP", width=12)
                table.add_column("FlowSpec", width=18)
                table.add_column("Services", style="dim")
                
                for i, status in enumerate(device_status, 1):
                    # Role styling
                    role = status["role"]
                    if role == "RR":
                        role_display = "[bold magenta]RR[/bold magenta]"
                    elif role == "PE":
                        role_display = "[bold cyan]PE[/bold cyan]"
                    elif role == "P":
                        role_display = "[yellow]P[/yellow]"
                    else:
                        role_display = "[dim]?[/dim]"
                    
                    # IGP
                    igp_parts = []
                    if status["isis_configured"]:
                        igp_parts.append("ISIS")
                    if status["ldp_configured"]:
                        igp_parts.append("LDP")
                    igp_display = "/".join(igp_parts) if igp_parts else "[dim]-[/dim]"
                    
                    # BGP
                    if status["bgp_configured"]:
                        bgp_display = f"[green]✓[/green] {status['bgp_neighbors']} peers"
                    else:
                        bgp_display = "[dim]Not configured[/dim]"
                    
                    # FlowSpec
                    fs_parts = []
                    if status["flowspec"]:
                        fs_parts.append("[green]FS[/green]")
                    if status["flowspec_vpn"]:
                        fs_parts.append("[green]FS-VPN[/green]")
                    if status["local_policy"]:
                        fs_parts.append("[yellow]LP[/yellow]")
                    if status["flowspec_interfaces"] > 0:
                        fs_parts.append(f"[cyan]{status['flowspec_interfaces']}ifs[/cyan]")
                    fs_display = " ".join(fs_parts) if fs_parts else "[dim]Not configured[/dim]"
                    
                    # Services
                    services_display = ", ".join(status["services"]) if status["services"] else "[dim]-[/dim]"
                    
                    table.add_row(
                        str(i),
                        status["hostname"],
                        role_display,
                        status["ip"],
                        igp_display,
                        bgp_display,
                        fs_display,
                        services_display
                    )
                
                console.print(table)
                console.print()
                console.print("[bold]Legend:[/bold]")
                console.print("  Role: [magenta]RR[/magenta]=Route Reflector  [cyan]PE[/cyan]=Provider Edge  [yellow]P[/yellow]=Core Router  [dim]?[/dim]=No BGP")
                console.print("  FlowSpec: [green]FS[/green]=FlowSpec  [green]FS-VPN[/green]=FlowSpec-VPN  [yellow]LP[/yellow]=Local Policy  [cyan]Nifs[/cyan]=Interfaces enabled")
                console.print()
                
                # Options
                console.print("[bold]Options:[/bold]")
                console.print("  [A] Analyze ALL devices (sequential, one by one)")
                console.print("  [#] Analyze specific device (enter number)")
                console.print("  [R] Refresh (re-read configs)")
                console.print("  [B] Back to device selection")
                console.print("  [Q] Quit")
                
                choice = Prompt.ask("\nSelect", default="1").lower()
                
                if choice == 'q':
                    return
                elif choice == 'b':
                    return  # Return to caller, don't recursively call run()
                elif choice == 'r':
                    # Refresh - loop will continue and re-read configs
                    continue
                elif choice == 'a':
                    # Analyze all devices SEQUENTIALLY (not parallel - avoids garbled output)
                    console.print(f"\n[bold]Running FlowSpec analysis on {len(devices_list)} devices...[/bold]\n")
                    
                    for i, dev in enumerate(devices_list, 1):
                        hostname = dev.get("hostname", "unknown")
                        console.print(f"\n[bold cyan]━━━ Device {i}/{len(devices_list)}: {hostname} ━━━[/bold cyan]")
                        try:
                            self.analyze_device(dev, use_cache=False)
                        except Exception as e:
                            console.print(f"[red]Error analyzing {hostname}: {e}[/red]")
                        
                        if i < len(devices_list):
                            if not Confirm.ask("\nContinue to next device?", default=True):
                                break
                    
                    Prompt.ask("\n[dim]Press Enter to return to summary[/dim]")
                    continue  # Loop back to show summary
                else:
                    # Analyze specific device
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(devices_list):
                            self.analyze_device(devices_list[idx], use_cache=False)
                            Prompt.ask("\n[dim]Press Enter to return to summary[/dim]")
                            continue  # Loop back to show summary
                    except ValueError:
                        console.print("[yellow]Invalid choice[/yellow]")
                        continue
            else:
                # Non-rich fallback
                print(f"\nMulti-Device Analysis: {len(devices_list)} devices")
                for i, status in enumerate(device_status, 1):
                    print(f"  [{i}] {status['hostname']} ({status['role']}) - BGP: {status['bgp_neighbors']} peers")
                
                for dev in devices_list:
                    self.analyze_device(dev, use_cache=True)
                return
    
    def _parse_device_selection(self, selection: str, max_idx: int) -> List[int]:
        """Parse device selection string supporting comma and range notation.
        
        Examples:
            "1" -> [0]
            "1,3,4" -> [0, 2, 3]
            "1-3" -> [0, 1, 2]
            "1-3,5" -> [0, 1, 2, 4]
        """
        indices = set()
        
        for part in selection.split(","):
            part = part.strip()
            if not part:
                continue
                
            if "-" in part:
                try:
                    start, end = map(int, part.split("-", 1))
                    indices.update(range(start - 1, end))
                except ValueError:
                    pass
            else:
                try:
                    indices.add(int(part) - 1)
                except ValueError:
                    pass
        
        # Filter valid indices
        return sorted([i for i in indices if 0 <= i < max_idx])
    
    def _select_path_tracing(self, devices: List[Dict]) -> Optional[Dict]:
        """Set up path tracing between devices with multi-select support"""
        
        if RICH_AVAILABLE:
            console.print("\n[bold]FlowSpec Path Tracing[/bold]")
            console.print("Trace FlowSpec routes from source(s) to destination(s).\n")
            console.print("[dim]Supports: single (1), comma-separated (1,3,4), ranges (1-3), or mixed (1-3,5)[/dim]\n")
            
            # Show device list
            console.print("[cyan]Available Devices:[/cyan]")
            for i, dev in enumerate(devices, 1):
                role = dev.get("role", "?")
                role_color = "magenta" if role == "RR" else "cyan" if role == "PE" else "dim"
                console.print(f"  [{i}] {dev.get('hostname')} ([{role_color}]{role}[/{role_color}])")
            console.print("  [B] Back\n")
            
            # Select source(s)
            console.print("[green]Source(s)[/green] - where FlowSpec routes originate (e.g., RR or CE)")
            source_input = Prompt.ask("Source device(s)", default="1")
            
            if source_input.lower() == 'b':
                return None
            
            source_indices = self._parse_device_selection(source_input, len(devices))
            if not source_indices:
                console.print("[red]Invalid source selection[/red]")
                return None
            
            sources = [devices[i] for i in source_indices]
            console.print(f"  → Selected: {', '.join(d.get('hostname') for d in sources)}\n")
            
            # Select destination(s)
            console.print("[blue]Destination(s)[/blue] - where FlowSpec rules are applied (e.g., PE)")
            
            # Suggest PEs as default
            pe_indices = [i+1 for i, d in enumerate(devices) if d.get("role") == "PE"]
            default_dest = ",".join(map(str, pe_indices)) if pe_indices else "1"
            
            dest_input = Prompt.ask("Destination device(s)", default=default_dest)
            
            if dest_input.lower() == 'b':
                return None
            
            dest_indices = self._parse_device_selection(dest_input, len(devices))
            if not dest_indices:
                console.print("[red]Invalid destination selection[/red]")
                return None
            
            destinations = [devices[i] for i in dest_indices]
            console.print(f"  → Selected: {', '.join(d.get('hostname') for d in destinations)}\n")
            
            # Confirm
            console.print("[bold]Path Trace:[/bold]")
            for src in sources:
                for dst in destinations:
                    if src != dst:
                        console.print(f"  {src.get('hostname')} → {dst.get('hostname')}")
            
            if not Confirm.ask("\nProceed with path trace?", default=True):
                return None
            
            # Return based on selection
            if len(sources) == 1 and len(destinations) == 1:
                # Single source, single destination
                return {
                    "_path_trace": True,
                    "source": sources[0],
                    "destination": destinations[0],
                    "all_devices": devices
                }
            else:
                # Multi-source or multi-destination
                return {
                    "_path_trace_multi": True,
                    "sources": sources,
                    "destinations": destinations,
                    "all_devices": devices
                }
        else:
            # Non-rich fallback
            print("\nFlowSpec Path Tracing")
            print("Supports: single (1), comma (1,3,4), ranges (1-3)\n")
            
            for i, dev in enumerate(devices, 1):
                role = dev.get("role", "?")
                print(f"  [{i}] {dev.get('hostname')} ({role})")
            print("  [B] Back\n")
            
            source_input = input("Source device(s) [1]: ").strip() or "1"
            if source_input.lower() == 'b':
                return None
            
            source_indices = self._parse_device_selection(source_input, len(devices))
            if not source_indices:
                print("Invalid source")
                return None
            
            dest_input = input("Destination device(s) [1]: ").strip() or "1"
            if dest_input.lower() == 'b':
                return None
            
            dest_indices = self._parse_device_selection(dest_input, len(devices))
            if not dest_indices:
                print("Invalid destination")
                return None
            
            sources = [devices[i] for i in source_indices]
            destinations = [devices[i] for i in dest_indices]
            
            if len(sources) == 1 and len(destinations) == 1:
                return {
                    "_path_trace": True,
                    "source": sources[0],
                    "destination": destinations[0],
                    "all_devices": devices
                }
            else:
                return {
                    "_path_trace_multi": True,
                    "sources": sources,
                    "destinations": destinations,
                    "all_devices": devices
                }
        
        return None
    
    def _edit_device_in_db(self, devices: List[Dict]):
        """Edit a device entry in devices.json (rename, change IP, etc.)"""
        if RICH_AVAILABLE:
            console.print("\n[bold]Edit Device in Database[/bold]")
            console.print("Select device to edit:\n")
            for i, dev in enumerate(devices, 1):
                console.print(f"  [{i}] {dev.get('hostname')} - {dev.get('ip', 'N/A')}")
            console.print("  [B] Back")
            
            choice = Prompt.ask("\nDevice to edit", default="b")
        else:
            print("\nEdit Device in Database")
            for i, dev in enumerate(devices, 1):
                print(f"  [{i}] {dev.get('hostname')} - {dev.get('ip', 'N/A')}")
            print("  [B] Back")
            choice = input("\nDevice to edit [b]: ").strip() or "b"
        
        if choice.lower() == 'b':
            return
        
        try:
            idx = int(choice) - 1
            if not (0 <= idx < len(devices)):
                if RICH_AVAILABLE:
                    console.print("[red]Invalid selection[/red]")
                return
        except ValueError:
            return
        
        device = devices[idx]
        old_hostname = device.get("hostname", "")
        old_ip = device.get("ip", "")
        old_desc = device.get("description", "")
        
        if RICH_AVAILABLE:
            console.print(f"\n[bold]Editing: {old_hostname}[/bold]")
            console.print("[dim](Press Enter to keep current value)[/dim]\n")
            
            new_hostname = Prompt.ask("Hostname", default=old_hostname)
            new_ip = Prompt.ask("IP Address", default=old_ip)
            new_desc = Prompt.ask("Description", default=old_desc or "")
            
            # Confirm changes
            if new_hostname != old_hostname or new_ip != old_ip or new_desc != old_desc:
                console.print("\n[bold]Changes:[/bold]")
                if new_hostname != old_hostname:
                    console.print(f"  Hostname: [red]{old_hostname}[/red] → [green]{new_hostname}[/green]")
                if new_ip != old_ip:
                    console.print(f"  IP: [red]{old_ip}[/red] → [green]{new_ip}[/green]")
                if new_desc != old_desc:
                    console.print(f"  Description: [red]{old_desc or '(empty)'}[/red] → [green]{new_desc or '(empty)'}[/green]")
                
                if not Confirm.ask("\nSave changes?", default=True):
                    console.print("[yellow]Cancelled[/yellow]")
                    return
            else:
                console.print("[dim]No changes made[/dim]")
                return
        else:
            print(f"\nEditing: {old_hostname}")
            print("(Press Enter to keep current value)\n")
            
            new_hostname = input(f"Hostname [{old_hostname}]: ").strip() or old_hostname
            new_ip = input(f"IP Address [{old_ip}]: ").strip() or old_ip
            new_desc = input(f"Description [{old_desc}]: ").strip() or old_desc
            
            if new_hostname == old_hostname and new_ip == old_ip and new_desc == old_desc:
                print("No changes made")
                return
            
            confirm = input("Save changes? [Y/n]: ").strip().lower()
            if confirm == 'n':
                print("Cancelled")
                return
        
        # Save changes to devices.json
        try:
            with open(DEVICES_FILE) as f:
                data = json.load(f)
            
            # Find and update the device
            devices_list = data.get("devices", data if isinstance(data, list) else [])
            updated = False
            
            for dev in devices_list:
                if dev.get("hostname") == old_hostname or dev.get("ip") == old_ip:
                    dev["hostname"] = new_hostname
                    dev["ip"] = new_ip
                    if new_desc:
                        dev["description"] = new_desc
                    # Also update device ID when hostname changes
                    if new_hostname != old_hostname:
                        new_id = new_hostname.lower().replace(' ', '_').replace('-', '_').replace('.', '_')
                        old_id = dev.get("id", "")
                        dev["id"] = new_id
                        self.log(f"Updated device ID: {old_id} → {new_id}")
                    updated = True
                    break
            
            if updated:
                # Write back
                if isinstance(data, dict) and "devices" in data:
                    data["devices"] = devices_list
                else:
                    data = devices_list
                
                with open(DEVICES_FILE, 'w') as f:
                    json.dump(data, f, indent=2)
                
                # Also rename config directory if hostname changed
                if new_hostname != old_hostname:
                    old_config_dir = Path(f"/home/dn/SCALER/db/configs/{old_hostname}")
                    new_config_dir = Path(f"/home/dn/SCALER/db/configs/{new_hostname}")
                    
                    if old_config_dir.exists() and not new_config_dir.exists():
                        try:
                            old_config_dir.rename(new_config_dir)
                            if RICH_AVAILABLE:
                                console.print(f"[green]✓[/green] Renamed config directory: {old_hostname} → {new_hostname}")
                        except Exception as e:
                            if RICH_AVAILABLE:
                                console.print(f"[yellow]⚠[/yellow] Could not rename config directory: {e}")
                
                if RICH_AVAILABLE:
                    console.print(f"[green]✓[/green] Device updated in database")
                else:
                    print("Device updated in database")
            else:
                if RICH_AVAILABLE:
                    console.print("[red]Device not found in database[/red]")
                else:
                    print("Device not found in database")
                    
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]Error saving: {e}[/red]")
            else:
                print(f"Error saving: {e}")
    
    def trace_flowspec_path(self, source: Dict, destination: Dict, all_devices: List[Dict]):
        """Trace FlowSpec routes from source to destination showing advertised/received routes"""
        if RICH_AVAILABLE:
            console.print("\n" + "═" * 70)
            console.print("[bold cyan]🔍 FlowSpec Route Path Trace[/bold cyan]")
            console.print("═" * 70)
            console.print(f"\n[bold]Path:[/bold] {source.get('hostname')} ({source.get('role', '?')}) → {destination.get('hostname')} ({destination.get('role', '?')})")
        
        path_results = []
        
        # Connect to source and get advertised routes
        source_conn = self.connect_to_device(source)
        if source_conn.connect():
            source_routes = self._get_bgp_flowspec_routes(source_conn, "advertised", source.get('hostname', ''))
            path_results.append(("source", source.get('hostname'), source_routes))
            source_conn.disconnect()
        
        # Connect to destination and get received routes
        dest_conn = self.connect_to_device(destination)
        if dest_conn.connect():
            dest_routes = self._get_bgp_flowspec_routes(dest_conn, "received", destination.get('hostname', ''))
            path_results.append(("destination", destination.get('hostname'), dest_routes))
            dest_conn.disconnect()
        
        # Display path trace results
        self._display_path_trace_results(path_results, source, destination)
    
    def trace_flowspec_path_multi(self, sources: List[Dict], destinations: List[Dict], all_devices: List[Dict]):
        """Trace FlowSpec routes from multiple sources to multiple destinations"""
        if RICH_AVAILABLE:
            console.print("\n" + "═" * 70)
            console.print("[bold cyan]🔍 FlowSpec Multi-Path Trace[/bold cyan]")
            console.print("═" * 70)
            
            # Show paths
            console.print("\n[bold]Paths to trace:[/bold]")
            path_count = 0
            for src in sources:
                for dst in destinations:
                    if src.get('hostname') != dst.get('hostname'):
                        path_count += 1
                        console.print(f"  {path_count}. {src.get('hostname')} ({src.get('role', '?')}) → {dst.get('hostname')} ({dst.get('role', '?')})")
            console.print()
        
        all_results = []
        
        # Collect data from all sources
        if RICH_AVAILABLE:
            console.print("[yellow]Collecting data from sources...[/yellow]")
        
        source_data = {}
        for src in sources:
            src_conn = self.connect_to_device(src)
            if src_conn.connect():
                source_data[src.get('hostname')] = self._get_bgp_flowspec_routes(
                    src_conn, "advertised", src.get('hostname', '')
                )
                src_conn.disconnect()
                if RICH_AVAILABLE:
                    console.print(f"  [green]✓[/green] {src.get('hostname')}")
        
        # Collect data from all destinations
        if RICH_AVAILABLE:
            console.print("\n[yellow]Collecting data from destinations...[/yellow]")
        
        dest_data = {}
        for dst in destinations:
            dst_conn = self.connect_to_device(dst)
            if dst_conn.connect():
                dest_data[dst.get('hostname')] = self._get_bgp_flowspec_routes(
                    dst_conn, "received", dst.get('hostname', '')
                )
                dst_conn.disconnect()
                if RICH_AVAILABLE:
                    console.print(f"  [green]✓[/green] {dst.get('hostname')}")
        
        # Display comparison table
        if RICH_AVAILABLE:
            console.print("\n")
            
            # Summary table for all paths
            table = Table(title="FlowSpec Route Summary", box=box.ROUNDED)
            table.add_column("Source", style="green")
            table.add_column("Destination", style="cyan")
            table.add_column("IPv4-FS", justify="right")
            table.add_column("IPv4-FS-VPN", justify="right")
            table.add_column("Status", justify="center")
            
            for src in sources:
                src_name = src.get('hostname')
                src_routes = source_data.get(src_name, {})
                
                for dst in destinations:
                    dst_name = dst.get('hostname')
                    if src_name == dst_name:
                        continue
                    
                    dst_routes = dest_data.get(dst_name, {})
                    
                    # Compare route counts
                    src_fs = src_routes.get("ipv4_flowspec", {}).get("count", 0)
                    src_fsvpn = src_routes.get("ipv4_flowspec_vpn", {}).get("count", 0)
                    dst_fs = dst_routes.get("ipv4_flowspec", {}).get("count", 0)
                    dst_fsvpn = dst_routes.get("ipv4_flowspec_vpn", {}).get("count", 0)
                    
                    # Status check
                    fs_match = src_fs == dst_fs if src_fs > 0 or dst_fs > 0 else True
                    fsvpn_match = src_fsvpn == dst_fsvpn if src_fsvpn > 0 or dst_fsvpn > 0 else True
                    
                    if fs_match and fsvpn_match and (src_fs > 0 or src_fsvpn > 0 or dst_fs > 0 or dst_fsvpn > 0):
                        status = "[green]✓ Match[/green]"
                    elif src_fs == 0 and src_fsvpn == 0 and dst_fs == 0 and dst_fsvpn == 0:
                        status = "[dim]No routes[/dim]"
                    else:
                        status = "[yellow]⚠ Mismatch[/yellow]"
                    
                    table.add_row(
                        src_name,
                        dst_name,
                        f"{src_fs}→{dst_fs}",
                        f"{src_fsvpn}→{dst_fsvpn}",
                        status
                    )
            
            console.print(table)
            
            # Show sample routes from each device
            console.print("\n[bold]Sample Routes by Device:[/bold]")
            
            all_data = {**source_data, **dest_data}
            for hostname, routes in all_data.items():
                role = "Source" if hostname in [s.get('hostname') for s in sources] else "Destination"
                console.print(f"\n[cyan]{hostname}[/cyan] ({role}):")
                
                for safi in ["ipv4_flowspec", "ipv4_flowspec_vpn"]:
                    count = routes.get(safi, {}).get("count", 0)
                    samples = routes.get(safi, {}).get("routes", [])
                    if count > 0:
                        console.print(f"  {safi}: {count} routes")
                        for sample in samples[:2]:
                            console.print(f"    [dim]{sample}[/dim]")
    
    def _get_bgp_flowspec_routes(self, conn: SSHConnection, direction: str, hostname: str) -> Dict[str, Any]:
        """Get BGP FlowSpec routes (advertised or received) for all neighbors"""
        routes_info = {
            "hostname": hostname,
            "direction": direction,
            "neighbors": [],
            "ipv4_flowspec": {"count": 0, "routes": []},
            "ipv4_flowspec_vpn": {"count": 0, "routes": []},
            "ipv6_flowspec": {"count": 0, "routes": []},
            "ipv6_flowspec_vpn": {"count": 0, "routes": []},
        }
        
        # Get neighbor list first
        success, output = conn.run_cli_command("show bgp summary | no-more", timeout=15)
        neighbors = []
        if success:
            for line in output.split('\n'):
                ip_match = re.match(r'\s*(\d+\.\d+\.\d+\.\d+)\s+', line)
                if ip_match:
                    neighbors.append(ip_match.group(1))
        
        routes_info["neighbors"] = neighbors
        
        # Get FlowSpec routes for each AFI-SAFI
        safi_list = [
            ("ipv4-flowspec", "ipv4_flowspec"),
            ("ipv4-flowspec-vpn", "ipv4_flowspec_vpn"),
            ("ipv6-flowspec", "ipv6_flowspec"),
            ("ipv6-flowspec-vpn", "ipv6_flowspec_vpn"),
        ]
        
        for safi_name, key in safi_list:
            # Get route count
            if "ipv6" in safi_name:
                cmd = f"show bgp ipv6 {safi_name.replace('ipv6-', '')} routes | no-more"
            else:
                cmd = f"show bgp ipv4 {safi_name.replace('ipv4-', '')} routes | no-more"
            
            success, output = conn.run_cli_command(cmd, timeout=20)
            if success:
                # Count routes (lines with FlowSpec NLRI patterns)
                route_count = 0
                route_samples = []
                
                for line in output.split('\n'):
                    # Look for FlowSpec NLRI patterns
                    if re.search(r'DstPrefix|SrcPrefix|DstPort|SrcPort|Proto|ICMP|DSCP|Frag', line):
                        route_count += 1
                        if len(route_samples) < 5:  # Sample first 5
                            route_samples.append(line.strip()[:80])
                
                routes_info[key]["count"] = route_count
                routes_info[key]["routes"] = route_samples
        
        # Get per-neighbor advertised/received routes
        for neighbor in neighbors[:3]:  # Limit to first 3 neighbors for performance
            neighbor_info = {"ip": neighbor, "advertised": {}, "received": {}}
            
            for safi_name, key in safi_list[:2]:  # Focus on IPv4 for now
                afi = "ipv4" if "ipv4" in safi_name else "ipv6"
                safi_short = safi_name.replace(f"{afi}-", "")
                
                # Advertised routes
                adv_cmd = f"show bgp ipv4 {safi_short} neighbor {neighbor} advertised-routes | no-more"
                success, adv_output = conn.run_cli_command(adv_cmd, timeout=15)
                if success:
                    adv_count = len([l for l in adv_output.split('\n') if re.search(r'DstPrefix|SrcPrefix', l)])
                    neighbor_info["advertised"][safi_name] = adv_count
                
                # Received routes
                rcv_cmd = f"show bgp ipv4 {safi_short} neighbor {neighbor} routes | no-more"
                success, rcv_output = conn.run_cli_command(rcv_cmd, timeout=15)
                if success:
                    rcv_count = len([l for l in rcv_output.split('\n') if re.search(r'DstPrefix|SrcPrefix', l)])
                    neighbor_info["received"][safi_name] = rcv_count
            
            routes_info["neighbors_detail"] = routes_info.get("neighbors_detail", [])
            routes_info["neighbors_detail"].append(neighbor_info)
        
        return routes_info
    
    def _display_path_trace_results(self, path_results: List, source: Dict, destination: Dict):
        """Display path trace results in a visual format"""
        if not RICH_AVAILABLE:
            print("\nPath trace results (install 'rich' for better display)")
            return
        
        console.print("\n")
        
        # Build visual path
        tree = Tree(f"[bold blue]🌐 FlowSpec Route Path[/bold blue]")
        
        for role, hostname, routes in path_results:
            device_role = source.get('role', '?') if role == "source" else destination.get('role', '?')
            
            if role == "source":
                node = tree.add(f"[bold green]📤 {hostname}[/bold green] ({device_role}) - Source")
            else:
                node = tree.add(f"[bold cyan]📥 {hostname}[/bold cyan] ({device_role}) - Destination")
            
            # Add route info
            for safi_key in ["ipv4_flowspec", "ipv4_flowspec_vpn", "ipv6_flowspec", "ipv6_flowspec_vpn"]:
                safi_data = routes.get(safi_key, {})
                count = safi_data.get("count", 0)
                if count > 0:
                    safi_display = safi_key.replace("_", "-").upper()
                    safi_node = node.add(f"[yellow]{safi_display}[/yellow]: {count} routes")
                    
                    # Show sample routes
                    for route in safi_data.get("routes", [])[:3]:
                        safi_node.add(f"[dim]{route}[/dim]")
            
            # Add per-neighbor details
            if routes.get("neighbors_detail"):
                neighbors_node = node.add("[magenta]Per-Neighbor Details[/magenta]")
                for nb in routes["neighbors_detail"]:
                    nb_node = neighbors_node.add(f"[cyan]{nb['ip']}[/cyan]")
                    for safi, adv_count in nb.get("advertised", {}).items():
                        rcv_count = nb.get("received", {}).get(safi, 0)
                        nb_node.add(f"{safi}: [green]→{adv_count}[/green] advertised, [blue]←{rcv_count}[/blue] received")
        
        console.print(tree)
        
        # Summary table
        console.print("\n[bold]Route Summary:[/bold]")
        table = Table(box=box.SIMPLE)
        table.add_column("AFI-SAFI", style="cyan")
        table.add_column(f"{source.get('hostname')} (Source)", style="green", justify="right")
        table.add_column(f"{destination.get('hostname')} (Dest)", style="blue", justify="right")
        table.add_column("Match", style="yellow", justify="center")
        
        for safi_key in ["ipv4_flowspec", "ipv4_flowspec_vpn"]:
            safi_display = safi_key.replace("_", "-")
            src_count = 0
            dst_count = 0
            
            for role, hostname, routes in path_results:
                count = routes.get(safi_key, {}).get("count", 0)
                if role == "source":
                    src_count = count
                else:
                    dst_count = count
            
            match = "✓" if src_count == dst_count and src_count > 0 else ("⚠" if src_count > 0 or dst_count > 0 else "-")
            table.add_row(safi_display, str(src_count), str(dst_count), match)
        
        console.print(table)
    
    def _run_path_trace_from_menu(self):
        """Run path trace from main menu - prompts for device selection"""
        devices = self.discover_devices()
        if not devices:
            if RICH_AVAILABLE:
                console.print("[yellow]No devices available for path tracing.[/yellow]")
            return
        
        path_selection = self._select_path_tracing(devices)
        if path_selection:
            if path_selection.get("_path_trace"):
                self.trace_flowspec_path(
                    source=path_selection["source"],
                    destination=path_selection["destination"],
                    all_devices=path_selection["all_devices"]
                )
            elif path_selection.get("_path_trace_multi"):
                self.trace_flowspec_path_multi(
                    sources=path_selection["sources"],
                    destinations=path_selection["destinations"],
                    all_devices=path_selection["all_devices"]
                )
    
    # =========================================================================
    # ANALYSIS FUNCTIONS
    # =========================================================================
    
    def check_bgp_traces(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """
        Check BGP daemon traces for FlowSpec UPDATE messages.
        
        Runs: run start shell ncc 0 -> tail -200 /var/log/bgpd_traces | grep -i flowspec
        
        This shows recent FlowSpec-related BGP activity including:
        - UPDATE messages received
        - NLRI processing
        - Errors or rejections
        """
        results = []
        
        # Get recent bgpd traces filtered for flowspec
        success, output = conn.run_ncc_shell_command(
            "tail -200 /var/log/bgpd_traces 2>/dev/null | grep -i flowspec | tail -50",
            ncc_id=0,
            timeout=30
        )
        
        if success:
            # Parse traces for useful info
            updates_received = len(re.findall(r'UPDATE.*flowspec|rcvd.*flowspec', output, re.IGNORECASE))
            updates_sent = len(re.findall(r'send.*UPDATE.*flowspec|adv.*flowspec', output, re.IGNORECASE))
            errors = len(re.findall(r'error|fail|reject|invalid', output, re.IGNORECASE))
            
            # Extract recent timestamps
            timestamps = re.findall(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', output)
            last_activity = timestamps[-1] if timestamps else "Unknown"
            
            # Extract neighbor IPs from traces
            neighbors = set(re.findall(r'from\s+(\d+\.\d+\.\d+\.\d+)', output))
            
            if errors > 0:
                status = CheckStatus.WARN
                analysis.warnings.append(f"BGP traces show {errors} FlowSpec errors")
            elif updates_received > 0 or updates_sent > 0:
                status = CheckStatus.PASS
            else:
                status = CheckStatus.INFO
            
            results.append(FlowCheckResult(
                step="BGP-T", component="BGP-Traces", check_name="BGP FlowSpec Activity",
                status=status,
                expected="Recent FlowSpec updates",
                actual=f"Rcvd: {updates_received}, Sent: {updates_sent}, Errors: {errors}, Last: {last_activity}",
                command="tail /var/log/bgpd_traces | grep flowspec",
                raw_output=output[:2000] if len(output) > 2000 else output,
                details=f"Neighbors: {', '.join(neighbors) if neighbors else 'None'}"
            ))
            
            # Store trace info for later display
            analysis.bgp_trace_updates_rcvd = updates_received
            analysis.bgp_trace_updates_sent = updates_sent
            analysis.bgp_trace_errors = errors
            analysis.bgp_trace_last_activity = last_activity
            analysis.bgp_trace_neighbors = list(neighbors)
        else:
            results.append(FlowCheckResult(
                step="BGP-T", component="BGP-Traces", check_name="BGP FlowSpec Activity",
                status=CheckStatus.SKIP,
                expected="BGP traces accessible",
                actual=f"Shell access failed: {output[:50]}",
                command="tail /var/log/bgpd_traces"
            ))
        
        return results
    
    def check_bgp_sessions(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check BGP FlowSpec sessions for BOTH SAFIs:
        - SAFI 133: flowspec (default/global VRF)
        - SAFI 134: flowspec-vpn (VPN/VRF contexts)
        """
        results = []
        total_up = 0
        
        # Check both FlowSpec SAFIs
        safi_checks = [
            ("flowspec", "FlowSpec (Global/Default VRF)", "SAFI-133"),
            ("flowspec-vpn", "FlowSpec-VPN (VRF)", "SAFI-134"),
        ]
        
        for safi_name, description, step_id in safi_checks:
            cmd = f"show bgp ipv4 {safi_name} summary | no-more"
            success, output = conn.run_cli_command(cmd, timeout=15)
            
            if success and output.strip():
                neighbors_up = 0
                neighbors_total = 0
                
                for line in output.split('\n'):
                    # Match lines with IP addresses (neighbor entries)
                    if re.search(r'\d+\.\d+\.\d+\.\d+', line) and 'Neighbor' not in line and 'Total' not in line:
                        neighbors_total += 1
                        # Check for Established state
                        if 'Established' in line:
                            neighbors_up += 1
                        # Also check for numeric state indicators (e.g., "Established" or message counts)
                        elif re.search(r'\s+\d+\s+\d+\s+\d+\s+\d+', line):
                            neighbors_up += 1
                
                total_up += neighbors_up
                
                # Report this SAFI's status
                status = CheckStatus.PASS if neighbors_up > 0 else CheckStatus.WARN
                results.append(FlowCheckResult(
                    step=step_id, component="BGP", check_name=description,
                    status=status,
                    expected="≥1 session Established",
                    actual=f"{neighbors_up}/{neighbors_total} Established",
                    command=cmd, raw_output=output
                ))
            elif success:
                # Command succeeded but no output - SAFI not configured
                results.append(FlowCheckResult(
                    step=step_id, component="BGP", check_name=description,
                    status=CheckStatus.INFO,
                    expected="FlowSpec SAFI configured",
                    actual=f"{safi_name} not configured or no neighbors",
                    command=cmd
                ))
        
        # If no sessions at all across both SAFIs
        if total_up == 0 and len(results) == 0:
            results.append(FlowCheckResult(
                step="1", component="BGP", check_name="FlowSpec Sessions (any SAFI)",
                status=CheckStatus.WARN,
                expected="≥1 session Established",
                actual="No FlowSpec BGP sessions configured",
                command="show bgp ipv4 flowspec[-vpn] summary"
            ))
            analysis.warnings.append("No FlowSpec BGP sessions (check if using Local Policies only)")
        elif total_up == 0:
            analysis.problems.append("FlowSpec BGP configured but no sessions established")
        
        return results
    
    def check_bgp_routes(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check BGP FlowSpec routes for BOTH SAFIs:
        - SAFI 133: flowspec (default/global VRF)
        - SAFI 134: flowspec-vpn (VPN/VRF contexts)
        """
        results = []
        total_routes = 0
        
        safi_checks = [
            ("flowspec", "FlowSpec Routes (Global)", "SAFI-133"),
            ("flowspec-vpn", "FlowSpec-VPN Routes (VRF)", "SAFI-134"),
        ]
        
        for safi_name, description, step_id in safi_checks:
            cmd = f"show bgp ipv4 {safi_name} routes | no-more"
            success, output = conn.run_cli_command(cmd, timeout=15)
            
            if success:
                route_count = output.count("DstPrefix:=") + output.count("SrcPrefix:=")
                total_routes += route_count
                
                # Only report if routes exist
                if route_count > 0:
                    results.append(FlowCheckResult(
                        step=step_id, component="BGP", check_name=description,
                        status=CheckStatus.PASS,
                        expected="≥1 FlowSpec route",
                        actual=f"{route_count} routes received",
                        command=cmd, raw_output=output
                    ))
        
        analysis.total_rules = total_routes
        
        # If no routes in any SAFI
        if total_routes == 0:
            results.append(FlowCheckResult(
                step="2", component="BGP", check_name="FlowSpec Routes (any SAFI)",
                status=CheckStatus.WARN,
                expected="≥1 FlowSpec route",
                actual="No FlowSpec routes received (may be using Local Policies only)",
                command="show bgp ipv4 flowspec[-vpn] routes"
            ))
            analysis.warnings.append("No FlowSpec BGP routes - check Local Policies if expected")
        
        return results
    
    def check_vrf_import(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check VRF FlowSpec import"""
        results = []
        
        # Get VRFs with flowspec
        cmd = "show running-config | include 'vrf instance\\|ipv4-flowspec'"
        success, output = conn.run_cli_command(cmd)
        
        vrfs = []
        current_vrf = None
        for line in output.split('\n'):
            if 'vrf instance' in line:
                match = re.search(r'vrf instance (\S+)', line)
                if match:
                    current_vrf = match.group(1)
            elif 'ipv4-flowspec' in line and current_vrf:
                vrfs.append(current_vrf)
                current_vrf = None
        
        analysis.vrf_count = len(vrfs)
        
        # Check each VRF
        for vrf in vrfs[:3]:
            cmd = f"show bgp instance vrf {vrf} ipv4 flowspec routes"
            success, output = conn.run_cli_command(cmd)
            
            if success:
                count = output.count("DstPrefix:=") + output.count("SrcPrefix:=")
                status = CheckStatus.PASS if count > 0 else CheckStatus.WARN
                
                results.append(FlowCheckResult(
                    step="3", component="VRF", check_name=f"Import to '{vrf}'",
                    status=status,
                    expected="Routes via RT match",
                    actual=f"{count} routes imported",
                    command=cmd, raw_output=output
                ))
        
        if not vrfs:
            results.append(FlowCheckResult(
                step="3", component="VRF", check_name="VRF FlowSpec Config",
                status=CheckStatus.WARN,
                expected="≥1 VRF with ipv4-flowspec",
                actual="0 VRFs configured",
                command=cmd
            ))
            analysis.warnings.append("No VRFs configured with ipv4-flowspec")
        
        return results
    
    def check_vrf_flowspec_instance(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check FlowSpec rules installed per VRF using 'show flowspec instance vrf <vrf-name>'.
        
        This shows the actual DP-installed FlowSpec rules per VRF context.
        Syntax: show flowspec instance vrf <vrf-name> ipv4 [destination <prefix>] [source <prefix>] [nlri <nlri>]
        """
        results = []
        
        # Get VRFs with flowspec enabled
        cmd = "show running-config | include 'vrf instance\\|ipv4-flowspec\\|ipv6-flowspec'"
        success, output = conn.run_cli_command(cmd)
        
        vrfs_ipv4 = []
        vrfs_ipv6 = []
        current_vrf = None
        
        for line in output.split('\n'):
            if 'vrf instance' in line:
                match = re.search(r'vrf instance (\S+)', line)
                if match:
                    current_vrf = match.group(1)
            elif current_vrf:
                if 'ipv4-flowspec' in line:
                    vrfs_ipv4.append(current_vrf)
                if 'ipv6-flowspec' in line:
                    vrfs_ipv6.append(current_vrf)
        
        # Check IPv4 FlowSpec instance per VRF
        for vrf in vrfs_ipv4[:5]:  # Limit to first 5 VRFs
            cmd = f"show flowspec instance vrf {vrf} ipv4"
            success, output = conn.run_cli_command(cmd)
            
            if success:
                # Count rules - look for NLRI patterns
                rule_count = output.count("DstPrefix") + output.count("SrcPrefix") + output.count("Protocol")
                has_rules = rule_count > 0 or "No flows found" not in output
                
                status = CheckStatus.PASS if has_rules else CheckStatus.INFO
                results.append(FlowCheckResult(
                    step="3b", component="VRF-Instance", check_name=f"VRF '{vrf}' IPv4",
                    status=status,
                    expected="FlowSpec rules in VRF",
                    actual=f"{rule_count} rule components" if has_rules else "No flows",
                    command=cmd, raw_output=output
                ))
        
        # Check IPv6 FlowSpec instance per VRF
        for vrf in vrfs_ipv6[:5]:
            cmd = f"show flowspec instance vrf {vrf} ipv6"
            success, output = conn.run_cli_command(cmd)
            
            if success:
                rule_count = output.count("DstPrefix") + output.count("SrcPrefix") + output.count("NextHeader")
                has_rules = rule_count > 0 or "No flows found" not in output
                
                status = CheckStatus.PASS if has_rules else CheckStatus.INFO
                results.append(FlowCheckResult(
                    step="3b", component="VRF-Instance", check_name=f"VRF '{vrf}' IPv6",
                    status=status,
                    expected="FlowSpec rules in VRF",
                    actual=f"{rule_count} rule components" if has_rules else "No flows",
                    command=cmd, raw_output=output
                ))
        
        if not vrfs_ipv4 and not vrfs_ipv6:
            results.append(FlowCheckResult(
                step="3b", component="VRF-Instance", check_name="VRF FlowSpec Instance",
                status=CheckStatus.INFO,
                expected="VRFs with FlowSpec AF",
                actual="No VRFs with FlowSpec address-family",
                command=cmd
            ))
        
        return results
    
    def check_ncp_installation(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check NCP/FPM installation status.
        
        For cluster environments, uses the NCP number(s) detected from FlowSpec-enabled interfaces.
        Interface naming: ge<speed>-<NCP>/<slot>/<port> -> extracts NCP number
        Example: ge100-18/0/0 -> NCP 18
        
        Falls back to NCP 0 if no specific NCPs detected (standalone or bundle interfaces).
        """
        results = []
        
        # Use detected NCPs from interfaces, or fall back to NCP 0
        ncps_to_check = analysis.flowspec_ncps if analysis.flowspec_ncps else [0]
        
        total_installed = 0
        total_not_installed = 0
        all_outputs = []
        
        for ncp in ncps_to_check:
            cmd = f"show flowspec ncp {ncp}"
            success, output = conn.run_cli_command(cmd)
            
            if success:
                installed = output.count("Status: Installed")
                not_installed = output.count("Status: Not installed")
                total_installed += installed
                total_not_installed += not_installed
                all_outputs.append(f"NCP {ncp}: {installed} installed, {not_installed} failed")
        
        # Determine overall status
        if total_installed > 0 and total_not_installed == 0:
            status = CheckStatus.PASS
        elif total_installed > 0:
            status = CheckStatus.WARN
        else:
            status = CheckStatus.FAIL
        
        # Build command string for reporting
        if len(ncps_to_check) == 1:
            cmd_str = f"show flowspec ncp {ncps_to_check[0]}"
        else:
            cmd_str = f"show flowspec ncp [{','.join(str(n) for n in ncps_to_check)}]"
        
        results.append(FlowCheckResult(
            step="4", component="NCP", check_name="Datapath Installation",
            status=status,
            expected="All rules 'Installed'",
            actual=f"Installed: {total_installed}, Failed: {total_not_installed}" + 
                   (f" (NCPs: {','.join(str(n) for n in ncps_to_check)})" if len(ncps_to_check) > 1 else ""),
            command=cmd_str, raw_output="\n".join(all_outputs)
        ))
        
        analysis.rules_installed = total_installed
        analysis.rules_failed = total_not_installed
        
        if total_not_installed > 0:
            analysis.problems.append(f"{total_not_installed} rules failed NCP installation")
        
        return results
    
    def check_xray_info(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check xray FlowSpec table info via interactive NCP shell.
        
        Uses: run start shell ncp <id> -> xraycli /wb_agent/flowspec/bgp/ipv4/info
        
        For cluster environments, uses the NCP(s) detected from FlowSpec-enabled interfaces.
        """
        results = []
        
        # Use detected NCPs, or fall back to NCP 0
        ncps_to_check = analysis.flowspec_ncps if analysis.flowspec_ncps else [0]
        
        total_entries = 0
        total_unsupported = 0
        total_tcam_errors = 0
        all_outputs = []
        
        for ncp in ncps_to_check:
            # Use new interactive shell method
            success, output = conn.run_xray_command("/wb_agent/flowspec/bgp/ipv4/info", ncp_id=ncp, timeout=30)
            
            if success:
                match = re.search(r'number_of_entries:\s*(\d+)', output)
                if match:
                    total_entries += int(match.group(1))
                match = re.search(r'num_unsupported:\s*(\d+)', output)
                if match:
                    total_unsupported += int(match.group(1))
                match = re.search(r'num_tcam_errors:\s*(\d+)', output)
                if match:
                    total_tcam_errors += int(match.group(1))
                all_outputs.append(f"NCP {ncp}: {output[:200]}")
        
        analysis.tcam_errors = total_tcam_errors
        
        status = CheckStatus.PASS if total_tcam_errors == 0 else CheckStatus.FAIL
        ncp_str = ','.join(str(n) for n in ncps_to_check)
        results.append(FlowCheckResult(
            step="5", component="wb_agent", check_name="TCAM Status",
            status=status,
            expected="tcam_errors = 0",
            actual=f"entries: {total_entries}, unsupported: {total_unsupported}, tcam_errors: {total_tcam_errors}" +
                   (f" (NCP: {ncp_str})" if len(ncps_to_check) > 1 or ncps_to_check[0] != 0 else ""),
            command=f"xraycli /wb_agent/flowspec/bgp/ipv4/info (NCP: {ncp_str})",
            raw_output="\n".join(all_outputs)
        ))
        
        if total_tcam_errors > 0:
            analysis.problems.append(f"TCAM ERRORS: {total_tcam_errors} rules failed HW programming")
        
        return results
    
    def check_hw_counters(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check HW write counters.
        
        For cluster environments, uses the NCP(s) detected from FlowSpec-enabled interfaces.
        """
        results = []
        
        # Use detected NCPs, or fall back to NCP 0
        ncps_to_check = analysis.flowspec_ncps if analysis.flowspec_ncps else [0]
        
        total_write_ok = 0
        total_write_fail = 0
        all_outputs = []
        
        for ncp in ncps_to_check:
            # Use new interactive shell method
            success, output = conn.run_xray_command("/wb_agent/flowspec/hw_counters", ncp_id=ncp, timeout=30)
            
            if success:
                match = re.search(r'hw_rules_write_ok:\s*(\d+)', output)
                if match:
                    total_write_ok += int(match.group(1))
                match = re.search(r'hw_rules_write_fail:\s*(\d+)', output)
                if match:
                    total_write_fail += int(match.group(1))
                all_outputs.append(f"NCP {ncp}: {output[:200]}")
        
        analysis.hw_write_failures = total_write_fail
        
        status = CheckStatus.PASS if total_write_fail == 0 else CheckStatus.FAIL
        ncp_str = ','.join(str(n) for n in ncps_to_check)
        results.append(FlowCheckResult(
            step="6", component="wb_agent", check_name="HW Counters",
            status=status,
            expected="write_fail = 0",
            actual=f"writes OK: {total_write_ok}, fails: {total_write_fail}" +
                   (f" (NCP: {ncp_str})" if len(ncps_to_check) > 1 or ncps_to_check[0] != 0 else ""),
            command=f"xraycli /wb_agent/flowspec/hw_counters (NCP: {ncp_str})",
            raw_output="\n".join(all_outputs)
        ))
        
        if total_write_fail > 0:
            analysis.problems.append(f"HW WRITE FAILURES: {total_write_fail}")
        
        return results
    
    def check_match_counters(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check FlowSpec match counters"""
        results = []
        
        cmd = "show flowspec"
        success, output = conn.run_cli_command(cmd)
        
        if success:
            rules_with_traffic = 0
            total_packets = 0
            
            for match in re.finditer(r'Match packet counter:\s*(\d+)', output):
                count = int(match.group(1))
                if count > 0:
                    rules_with_traffic += 1
                    total_packets += count
            
            status = CheckStatus.PASS if rules_with_traffic > 0 else CheckStatus.INFO
            results.append(FlowCheckResult(
                step="7", component="Counters", check_name="Traffic Match",
                status=status,
                expected="Counters incrementing",
                actual=f"{rules_with_traffic} rules matched, {total_packets} packets",
                command=cmd, raw_output=output
            ))
            
            if rules_with_traffic == 0 and analysis.rules_installed > 0:
                analysis.info_messages.append("No traffic matching FlowSpec rules (may be normal if no attack traffic)")
        
        return results
    
    def check_flowspec_interfaces(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check interfaces with flowspec enabled and detect NCP numbers for cluster support.
        
        For Standalone (SA) devices, always uses NCP 0 (no detection needed).
        For Cluster devices, extracts NCP numbers from interface names.
        """
        results = []
        
        # First, detect if this is SA or Cluster
        analysis.is_standalone = self.detect_device_type(conn)
        
        if analysis.is_standalone:
            # SA device: Always NCP 0, just count interfaces without detailed parsing
            cmd = "show running-config | include 'flowspec enabled'"
            success, output = conn.run_cli_command(cmd)
            
            if success:
                iface_count = output.count('flowspec enabled')
                analysis.flowspec_ncps = [0]  # SA always uses NCP 0
                
                status = CheckStatus.PASS if iface_count > 0 else CheckStatus.WARN
                results.append(FlowCheckResult(
                    step="8", component="Interfaces", check_name="FlowSpec Enabled",
                    status=status,
                    expected="≥1 interface",
                    actual=f"{iface_count} interfaces (SA: NCP 0)",
                    command=cmd, raw_output=output
                ))
                
                if iface_count == 0:
                    analysis.warnings.append("No interfaces with 'flowspec enabled' - rules won't apply!")
        else:
            # Cluster device: Parse interface names to extract NCP numbers
            cmd = "show running-config interfaces | include 'interface\\|flowspec enabled'"
            success, output = conn.run_cli_command(cmd)
            
            if success:
                # Parse interface names that have flowspec enabled
                lines = output.split('\n')
                current_iface = None
                flowspec_interfaces = []
                
                for line in lines:
                    line = line.strip()
                    iface_match = re.match(r'(?:interface\s+)?(\S+)\s*$', line)
                    if iface_match and 'flowspec' not in line.lower():
                        potential_iface = iface_match.group(1)
                        if re.match(r'(ge|xe|ce|et|bundle|irb|lo)\d*', potential_iface):
                            current_iface = potential_iface
                    elif 'flowspec enabled' in line.lower() and current_iface:
                        flowspec_interfaces.append(current_iface)
                        current_iface = None
                
                iface_count = len(flowspec_interfaces)
                
                # Extract NCP numbers from interface names
                detected_ncps = extract_ncps_from_interfaces(flowspec_interfaces)
                
                # Store in analysis for use by NCP check functions
                analysis.flowspec_interfaces = flowspec_interfaces
                analysis.flowspec_ncps = detected_ncps if detected_ncps else [0]
                
                # Build actual string with NCP info
                if detected_ncps:
                    ncp_str = ', '.join(str(n) for n in detected_ncps)
                    actual_str = f"{iface_count} interfaces (Cluster NCP: {ncp_str})"
                else:
                    actual_str = f"{iface_count} interfaces"
                
                status = CheckStatus.PASS if iface_count > 0 else CheckStatus.WARN
                results.append(FlowCheckResult(
                    step="8", component="Interfaces", check_name="FlowSpec Enabled",
                    status=status,
                    expected="≥1 interface",
                    actual=actual_str,
                    command=cmd, raw_output=output
                ))
                
                if iface_count == 0:
                    analysis.warnings.append("No interfaces with 'flowspec enabled' - rules won't apply!")
                elif detected_ncps:
                    analysis.info_messages.append(f"Cluster: Detected NCP(s): {ncp_str} from FlowSpec interfaces")
        
        return results
    
    # =========================================================================
    # LOCAL POLICIES CHECKS
    # =========================================================================
    
    def check_local_policies_config(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check FlowSpec Local Policies configuration"""
        results = []
        
        # Check configured policies
        cmd = "show flowspec-local-policies policies"
        success, output = conn.run_cli_command(cmd)
        
        if success:
            policy_count = output.count("Policy:") or output.count("policy ")
            
            status = CheckStatus.PASS if policy_count > 0 else CheckStatus.INFO
            results.append(FlowCheckResult(
                step="LP-1", component="LocalPolicies", check_name="Configured Policies",
                status=status,
                expected="Policies configured (optional)",
                actual=f"{policy_count} policies",
                command=cmd, raw_output=output
            ))
            
            # Store for analysis
            if not hasattr(analysis, 'local_policies_count'):
                analysis.local_policies_count = policy_count
        
        # Check match-classes (including VRF match-class field - NEW in FlowSpec VPN branch!)
        cmd = "show flowspec-local-policies match-classes"
        success, output = conn.run_cli_command(cmd)
        
        if success:
            mc_count = output.count("Match-class:") or output.count("match-class ")
            # Check for VRF-specific match-classes (new feature!)
            vrf_mc_count = len(re.findall(r'vrf\s+\S+', output, re.IGNORECASE))
            
            status = CheckStatus.PASS if mc_count > 0 else CheckStatus.INFO
            
            actual_str = f"{mc_count} match-classes"
            if vrf_mc_count > 0:
                actual_str += f" ({vrf_mc_count} with VRF filter)"
            
            results.append(FlowCheckResult(
                step="LP-2", component="LocalPolicies", check_name="Match Classes",
                status=status,
                expected="Match classes defined (optional)",
                actual=actual_str,
                command=cmd, raw_output=output
            ))
            
            if vrf_mc_count > 0:
                analysis.info_messages.append(f"VRF-specific local policies: {vrf_mc_count} match-classes target specific VRFs")
        
        return results
    
    def check_local_policies_ncp(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check Local Policies NCP installation status.
        
        For cluster environments, uses the NCP number(s) detected from FlowSpec-enabled interfaces.
        Falls back to NCP 0 if no specific NCPs detected.
        """
        results = []
        
        # Use detected NCPs from interfaces, or fall back to NCP 0
        ncps_to_check = analysis.flowspec_ncps if analysis.flowspec_ncps else [0]
        
        total_installed = 0
        total_not_installed = 0
        all_outputs = []
        
        for ncp in ncps_to_check:
            cmd = f"show flowspec-local-policies ncp {ncp}"
            success, output = conn.run_cli_command(cmd)
            
            if success:
                installed = output.count("Status: Installed")
                not_installed = output.count("Status: Not installed")
                total_installed += installed
                total_not_installed += not_installed
                all_outputs.append(f"NCP {ncp}: {installed} installed, {not_installed} failed")
        
        # Determine overall status
        if total_installed > 0 and total_not_installed == 0:
            status = CheckStatus.PASS
        elif total_installed > 0:
            status = CheckStatus.WARN
        elif total_installed == 0 and total_not_installed == 0:
            status = CheckStatus.INFO  # No local policies
        else:
            status = CheckStatus.FAIL
        
        # Build command string for reporting
        if len(ncps_to_check) == 1:
            cmd_str = f"show flowspec-local-policies ncp {ncps_to_check[0]}"
        else:
            cmd_str = f"show flowspec-local-policies ncp [{','.join(str(n) for n in ncps_to_check)}]"
        
        results.append(FlowCheckResult(
            step="LP-3", component="LocalPolicies", check_name="NCP Installation",
            status=status,
            expected="All local policies 'Installed'",
            actual=f"Installed: {total_installed}, Failed: {total_not_installed}" +
                   (f" (NCPs: {','.join(str(n) for n in ncps_to_check)})" if len(ncps_to_check) > 1 else ""),
            command=cmd_str, raw_output="\n".join(all_outputs)
        ))
        
        if total_not_installed > 0:
            analysis.problems.append(f"{total_not_installed} local policies failed NCP installation")
        
        return results
    
    def check_local_policies_xray(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check Local Policies via xray"""
        results = []
        
        # Use interactive shell for xraycli
        success, output = conn.run_xray_command("/wb_agent/flowspec/local_policies/ipv4/info", ncp_id=0, timeout=30)
        
        if success:
            entries = 0
            unsupported = 0
            tcam_errors = 0
            
            match = re.search(r'number_of_entries:\s*(\d+)', output)
            if match:
                entries = int(match.group(1))
            match = re.search(r'num_unsupported:\s*(\d+)', output)
            if match:
                unsupported = int(match.group(1))
            match = re.search(r'num_tcam_errors:\s*(\d+)', output)
            if match:
                tcam_errors = int(match.group(1))
            
            if entries == 0:
                status = CheckStatus.INFO  # No local policies
            elif tcam_errors == 0:
                status = CheckStatus.PASS
            else:
                status = CheckStatus.FAIL
            
            results.append(FlowCheckResult(
                step="LP-4", component="LocalPolicies", check_name="xray Table Info",
                status=status,
                expected="tcam_errors = 0",
                actual=f"entries: {entries}, unsupported: {unsupported}, tcam_errors: {tcam_errors}",
                command="xraycli /wb_agent/flowspec/local_policies/ipv4/info",
                raw_output=output
            ))
            
            if tcam_errors > 0:
                analysis.problems.append(f"LOCAL POLICY TCAM ERRORS: {tcam_errors} rules failed")
        
        return results
    
    def check_local_policies_counters(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check Local Policies counters"""
        results = []
        
        cmd = "show flowspec-local-policies counters"
        success, output = conn.run_cli_command(cmd)
        
        if success:
            rules_with_traffic = 0
            total_packets = 0
            
            # Look for counter patterns
            for match in re.finditer(r'packets:\s*(\d+)', output, re.IGNORECASE):
                count = int(match.group(1))
                if count > 0:
                    rules_with_traffic += 1
                    total_packets += count
            
            if 'No policies' in output or len(output.strip()) < 20:
                status = CheckStatus.INFO
                actual = "No local policies configured"
            elif rules_with_traffic > 0:
                status = CheckStatus.PASS
                actual = f"{rules_with_traffic} policies matched, {total_packets} packets"
            else:
                status = CheckStatus.INFO
                actual = "0 packets matched (may be normal)"
            
            results.append(FlowCheckResult(
                step="LP-5", component="LocalPolicies", check_name="Traffic Counters",
                status=status,
                expected="Counters incrementing",
                actual=actual,
                command=cmd, raw_output=output
            ))
        
        return results
    
    # =========================================================================
    # IPv6 FLOWSPEC CHECKS (NEW - Parallel to IPv4)
    # =========================================================================
    
    def check_bgp_sessions_ipv6(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check BGP IPv6 FlowSpec sessions for BOTH SAFIs:
        - SAFI 133: ipv6-flowspec (default/global VRF)
        - SAFI 134: ipv6-flowspec-vpn (VPN/VRF contexts)
        """
        results = []
        total_up = 0
        
        safi_checks = [
            ("ipv6-flowspec", "IPv6-FlowSpec (Global/Default VRF)", "v6-SAFI-133"),
            ("ipv6-flowspec-vpn", "IPv6-FlowSpec-VPN (VRF)", "v6-SAFI-134"),
        ]
        
        for safi_name, description, step_id in safi_checks:
            # Note: IPv6 FlowSpec uses 'show bgp ipv6 <safi>'
            cmd = f"show bgp ipv6 {safi_name} summary"
            success, output = conn.run_cli_command(cmd)
            
            if success:
                neighbors_up = 0
                neighbors_total = 0
                
                for line in output.split('\n'):
                    # IPv6 addresses have colons
                    if re.search(r'[0-9a-fA-F:]+::', line) or re.search(r'\d+\.\d+\.\d+\.\d+', line):
                        if 'Neighbor' not in line:
                            neighbors_total += 1
                            if 'Established' in line or re.search(r'\d+\s+\d+\s+\d+\s+\d+\s*$', line):
                                neighbors_up += 1
                
                total_up += neighbors_up
                
                if neighbors_total > 0 or neighbors_up > 0:
                    status = CheckStatus.PASS if neighbors_up > 0 else CheckStatus.WARN
                    results.append(FlowCheckResult(
                        step=step_id, component="BGP-IPv6", check_name=description,
                        status=status,
                        expected="≥1 session Established",
                        actual=f"{neighbors_up}/{neighbors_total} Established",
                        command=cmd, raw_output=output
                    ))
        
        # Only log if no IPv6 sessions at all (not an error, just info)
        if total_up == 0 and len(results) == 0:
            results.append(FlowCheckResult(
                step="v6", component="BGP-IPv6", check_name="IPv6-FlowSpec Sessions",
                status=CheckStatus.INFO,
                expected="Sessions if IPv6-FlowSpec configured",
                actual="No IPv6-FlowSpec BGP sessions configured",
                command="show bgp ipv6 flowspec[-vpn] summary"
            ))
            analysis.info_messages.append("No IPv6-FlowSpec BGP sessions (may be normal if IPv4-only)")
        
        return results
    
    def check_bgp_routes_ipv6(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check BGP IPv6 FlowSpec routes for BOTH SAFIs"""
        results = []
        total_routes = 0
        
        safi_checks = [
            ("ipv6-flowspec", "IPv6-FlowSpec Routes (Global)", "v6-SAFI-133"),
            ("ipv6-flowspec-vpn", "IPv6-FlowSpec-VPN Routes (VRF)", "v6-SAFI-134"),
        ]
        
        for safi_name, description, step_id in safi_checks:
            cmd = f"show bgp ipv6 {safi_name} routes"
            success, output = conn.run_cli_command(cmd)
            
            if success:
                # IPv6 prefixes use :: notation
                route_count = output.count("DstPrefix:=") + output.count("SrcPrefix:=")
                total_routes += route_count
                
                if route_count > 0:
                    results.append(FlowCheckResult(
                        step=step_id, component="BGP-IPv6", check_name=description,
                        status=CheckStatus.PASS,
                        expected="≥1 IPv6-FlowSpec route",
                        actual=f"{route_count} routes received",
                        command=cmd, raw_output=output
                    ))
        
        if total_routes > 0:
            analysis.bgp_total_ipv6 = total_routes
        
        return results
    
    def check_local_policies_ipv6(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check IPv6 FlowSpec Local Policies configuration"""
        results = []
        
        # Check IPv6 match-classes
        cmd = "show flowspec-local-policies match-classes ipv6"
        success, output = conn.run_cli_command(cmd)
        
        if success:
            mc_count = output.count("Match-class:") or output.count("match-class ")
            if 'No ' in output or len(output.strip()) < 30:
                mc_count = 0
            
            if mc_count > 0:
                results.append(FlowCheckResult(
                    step="LP6-1", component="LocalPolicies-IPv6", check_name="IPv6 Match Classes",
                    status=CheckStatus.PASS,
                    expected="IPv6 match classes defined",
                    actual=f"{mc_count} IPv6 match-classes",
                    command=cmd, raw_output=output
                ))
        
        # Check IPv6 policies
        cmd = "show flowspec-local-policies policies ipv6"
        success, output = conn.run_cli_command(cmd)
        
        if success:
            policy_count = output.count("Policy:") or output.count("policy ")
            if 'No ' in output or len(output.strip()) < 30:
                policy_count = 0
            
            if policy_count > 0:
                results.append(FlowCheckResult(
                    step="LP6-2", component="LocalPolicies-IPv6", check_name="IPv6 Policies",
                    status=CheckStatus.PASS,
                    expected="IPv6 policies defined",
                    actual=f"{policy_count} IPv6 policies",
                    command=cmd, raw_output=output
                ))
                analysis.lp_total_ipv6 = policy_count
        
        return results
    
    def check_local_policies_xray_ipv6(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check IPv6 Local Policies via xray"""
        results = []
        
        # Use interactive shell for xraycli
        success, output = conn.run_xray_command("/wb_agent/flowspec/local_policies/ipv6/info", ncp_id=0, timeout=30)
        
        if success:
            entries = 0
            unsupported = 0
            tcam_errors = 0
            
            match = re.search(r'number_of_entries:\s*(\d+)', output)
            if match:
                entries = int(match.group(1))
            match = re.search(r'num_unsupported:\s*(\d+)', output)
            if match:
                unsupported = int(match.group(1))
            match = re.search(r'num_tcam_errors:\s*(\d+)', output)
            if match:
                tcam_errors = int(match.group(1))
            
            if entries > 0:
                if tcam_errors == 0:
                    status = CheckStatus.PASS
                else:
                    status = CheckStatus.FAIL
                
                results.append(FlowCheckResult(
                    step="LP6-3", component="LocalPolicies-IPv6", check_name="IPv6 xray Info",
                    status=status,
                    expected="tcam_errors = 0",
                    actual=f"entries: {entries}, unsupported: {unsupported}, tcam_errors: {tcam_errors}",
                    command="xraycli /wb_agent/flowspec/local_policies/ipv6/info",
                    raw_output=output
                ))
                
                analysis.lp_installed_ipv6 = entries - unsupported
                analysis.lp_unsupported_ipv6 = unsupported
                analysis.lp_tcam_errors_ipv6 = tcam_errors
                
                if tcam_errors > 0:
                    analysis.problems.append(f"IPv6 LOCAL POLICY TCAM ERRORS: {tcam_errors} rules failed")
        
        return results
    
    def check_xray_info_ipv6(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check xray IPv6 FlowSpec table info"""
        results = []
        
        # Use interactive shell for xraycli
        success, output = conn.run_xray_command("/wb_agent/flowspec/bgp/ipv6/info", ncp_id=0, timeout=30)
        
        if success:
            entries = 0
            unsupported = 0
            tcam_errors = 0
            
            match = re.search(r'number_of_entries:\s*(\d+)', output)
            if match:
                entries = int(match.group(1))
            match = re.search(r'num_unsupported:\s*(\d+)', output)
            if match:
                unsupported = int(match.group(1))
            match = re.search(r'num_tcam_errors:\s*(\d+)', output)
            if match:
                tcam_errors = int(match.group(1))
            
            if entries > 0:
                status = CheckStatus.PASS if tcam_errors == 0 else CheckStatus.FAIL
                results.append(FlowCheckResult(
                    step="v6-5", component="wb_agent-IPv6", check_name="IPv6 TCAM Status",
                    status=status,
                    expected="tcam_errors = 0",
                    actual=f"entries: {entries}, unsupported: {unsupported}, tcam_errors: {tcam_errors}",
                    command="xraycli /wb_agent/flowspec/bgp/ipv6/info",
                    raw_output=output
                ))
                
                analysis.bgp_installed_ipv6 = entries - unsupported
                analysis.bgp_unsupported_ipv6 = unsupported
                analysis.bgp_tcam_errors_ipv6 = tcam_errors
                
                if tcam_errors > 0:
                    analysis.problems.append(f"IPv6 TCAM ERRORS: {tcam_errors} rules failed HW programming")
        
        return results
    
    def check_vrf_flowspec_af(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check VRFs for FlowSpec address-family configuration (both IPv4 and IPv6)"""
        results = []
        
        # Get VRFs with flowspec AF
        cmd = "show running-config | include 'vrf instance\\|ipv4-flowspec\\|ipv6-flowspec'"
        success, output = conn.run_cli_command(cmd)
        
        vrfs_with_ipv4_fs = []
        vrfs_with_ipv6_fs = []
        current_vrf = None
        
        for line in output.split('\n'):
            if 'vrf instance' in line:
                match = re.search(r'vrf instance (\S+)', line)
                if match:
                    current_vrf = match.group(1)
            elif 'ipv4-flowspec' in line and current_vrf:
                vrfs_with_ipv4_fs.append(current_vrf)
            elif 'ipv6-flowspec' in line and current_vrf:
                vrfs_with_ipv6_fs.append(current_vrf)
        
        # Remove duplicates
        vrfs_with_ipv4_fs = list(set(vrfs_with_ipv4_fs))
        vrfs_with_ipv6_fs = list(set(vrfs_with_ipv6_fs))
        
        if vrfs_with_ipv4_fs:
            results.append(FlowCheckResult(
                step="VRF4", component="VRF", check_name="IPv4-FlowSpec VRFs",
                status=CheckStatus.PASS,
                expected="VRFs with ipv4-flowspec AF",
                actual=f"{len(vrfs_with_ipv4_fs)} VRFs: {', '.join(vrfs_with_ipv4_fs[:3])}{'...' if len(vrfs_with_ipv4_fs) > 3 else ''}",
                command=cmd
            ))
        
        if vrfs_with_ipv6_fs:
            results.append(FlowCheckResult(
                step="VRF6", component="VRF", check_name="IPv6-FlowSpec VRFs",
                status=CheckStatus.PASS,
                expected="VRFs with ipv6-flowspec AF",
                actual=f"{len(vrfs_with_ipv6_fs)} VRFs: {', '.join(vrfs_with_ipv6_fs[:3])}{'...' if len(vrfs_with_ipv6_fs) > 3 else ''}",
                command=cmd
            ))
        
        return results
    
    def check_tcam_capacity(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Check shared TCAM capacity (BGP + Local Policies combined) for both IPv4 and IPv6"""
        results = []
        
        # IPv4 capacity check using DNOS show commands
        ipv4_bgp = 0
        ipv4_lp = 0
        
        # Count BGP FlowSpec rules from 'show flowspec ipv4'
        cmd = "show flowspec ipv4 | no-more"
        success, output = conn.run_cli_command(cmd, timeout=15)
        if success and "No flows found" not in output:
            # Count flow entries (lines with DstPrefix, SrcPrefix, or Priority)
            ipv4_bgp = len(re.findall(r'^\s*(DstPrefix|SrcPrefix|Priority)\s*:', output, re.MULTILINE))
            # Alternative: count unique flows by looking for action lines
            if ipv4_bgp == 0:
                ipv4_bgp = len(re.findall(r'(Traffic-rate|Redirect|allow)', output, re.IGNORECASE))
        
        # Count Local Policy rules from 'show flowspec-local-policies policies'
        cmd = "show flowspec-local-policies policies address-family ipv4 | no-more"
        success, output = conn.run_cli_command(cmd, timeout=15)
        if success and "Unknown word" not in output:
            # Count match-classes (MC-N entries)
            ipv4_lp = len(re.findall(r'MC-\d+:', output))
        
        ipv4_total = ipv4_bgp + ipv4_lp
        ipv4_capacity = 12000
        ipv4_pct = (ipv4_total / ipv4_capacity) * 100 if ipv4_capacity > 0 else 0
        
        if ipv4_pct > 90:
            status = CheckStatus.FAIL
        elif ipv4_pct > 75:
            status = CheckStatus.WARN
        else:
            status = CheckStatus.PASS
        
        results.append(FlowCheckResult(
            step="CAP4", component="TCAM", check_name="IPv4 Capacity",
            status=status,
            expected=f"≤75% of {ipv4_capacity}",
            actual=f"{ipv4_total}/{ipv4_capacity} ({ipv4_pct:.1f}%) - BGP:{ipv4_bgp} LP:{ipv4_lp}",
            command="show flowspec ipv4 + show flowspec-local-policies"
        ))
        
        # IPv6 capacity check using DNOS show commands
        ipv6_bgp = 0
        ipv6_lp = 0
        
        # Count BGP FlowSpec IPv6 rules
        cmd = "show flowspec ipv6 | no-more"
        success, output = conn.run_cli_command(cmd, timeout=15)
        if success and "No flows found" not in output:
            ipv6_bgp = len(re.findall(r'^\s*(DstPrefix|SrcPrefix|Priority)\s*:', output, re.MULTILINE))
            if ipv6_bgp == 0:
                ipv6_bgp = len(re.findall(r'(Traffic-rate|Redirect|allow)', output, re.IGNORECASE))
        
        # Count Local Policy IPv6 rules
        cmd = "show flowspec-local-policies policies address-family ipv6 | no-more"
        success, output = conn.run_cli_command(cmd, timeout=15)
        if success and "Unknown word" not in output:
            ipv6_lp = len(re.findall(r'MC-\d+:', output))
        
        ipv6_total = ipv6_bgp + ipv6_lp
        ipv6_capacity = 4000
        ipv6_pct = (ipv6_total / ipv6_capacity) * 100 if ipv6_capacity > 0 else 0
        
        if ipv6_pct > 90:
            status = CheckStatus.FAIL
        elif ipv6_pct > 75:
            status = CheckStatus.WARN
        else:
            status = CheckStatus.PASS
        
        results.append(FlowCheckResult(
            step="CAP6", component="TCAM", check_name="IPv6 Capacity",
            status=status,
            expected=f"≤75% of {ipv6_capacity}",
            actual=f"{ipv6_total}/{ipv6_capacity} ({ipv6_pct:.1f}%) - BGP:{ipv6_bgp} LP:{ipv6_lp}",
            command="xraycli /wb_agent/flowspec/*/ipv6/info"
        ))
        
        # CRITICAL: When TCAM is full, new policies WON'T override even with better priority!
        if ipv4_pct >= 100 or ipv6_pct >= 100:
            analysis.problems.append(
                "⚠️ TCAM FULL! New policies will NOT be installed even if they have higher priority!"
            )
        elif ipv4_pct > 75 or ipv6_pct > 75:
            analysis.warnings.append(
                f"TCAM approaching limit - IPv4:{ipv4_pct:.1f}% IPv6:{ipv6_pct:.1f}%"
            )
        
        return results
    
    def check_bcm_tcam_entries(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """
        Check FlowSpec local policies installation status at NCP level.
        Uses 'show flowspec-local-policies ncp 0' which shows installed/not-installed status.
        
        Note: BCM shell commands (wbox-cli) require interactive shell access not available via CLI.
        """
        results = []
        
        # Use DNOS CLI command instead of shell command
        cmd = "show flowspec-local-policies ncp 0 | no-more"
        success, output = conn.run_cli_command(cmd, timeout=15)
        
        if success and "Unknown word" not in output:
            # Count installed vs not installed
            installed = len(re.findall(r'Status:\s*Installed\b', output, re.IGNORECASE))
            not_installed = len(re.findall(r'Status:\s*Not installed', output, re.IGNORECASE))
            
            # Check for errors
            has_errors = 'not supported' in output.lower() or 'error' in output.lower()
            
            if not_installed > 0 or has_errors:
                status = CheckStatus.WARN if installed > 0 else CheckStatus.FAIL
                if not_installed > 0:
                    analysis.warnings.append(f"Local policies: {not_installed} rules not installed at NCP")
            else:
                status = CheckStatus.PASS
            
            results.append(FlowCheckResult(
                step="LP-3", component="LocalPolicy", check_name="NCP Installation",
                status=status,
                expected="All local policies 'Installed'",
                actual=f"Installed: {installed}, Failed: {not_installed}",
                command="show flowspec-local-policies ncp 0",
                raw_output=output[:2000] if len(output) > 2000 else output
            ))
        else:
            # Command not available or no local policies configured
            results.append(FlowCheckResult(
                step="LP-3", component="LocalPolicy", check_name="NCP Installation",
                status=CheckStatus.INFO,
                expected="Local policies at NCP level",
                actual="No local policies configured or command not available",
                command="show flowspec-local-policies ncp 0"
            ))
        
        return results
    
    def check_detailed_rules_analysis(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Comprehensive rule analysis with priority parsing"""
        results = []
        
        # =====================================================================
        # PARSE BGP FLOWSPEC RULES
        # =====================================================================
        success, bgp_output = conn.run_xray_command("/wb_agent/flowspec/bgp/ipv4/rules", ncp_id=0, timeout=60)
        
        if success:
            analysis.bgp_rules = parse_xray_rules(bgp_output, source="BGP")
            analysis.bgp_total = len(analysis.bgp_rules)
            analysis.bgp_installed = sum(1 for r in analysis.bgp_rules if r.dp_supported)
            analysis.bgp_unsupported = sum(1 for r in analysis.bgp_rules if not r.dp_supported)
        
        # =====================================================================
        # PARSE LOCAL POLICIES RULES
        # =====================================================================
        success, lp_output = conn.run_xray_command("/wb_agent/flowspec/local_policies/ipv4/rules", ncp_id=0, timeout=60)
        
        if success:
            analysis.local_rules = parse_xray_rules(lp_output, source="LOCAL")
            analysis.lp_total = len(analysis.local_rules)
            analysis.lp_installed = sum(1 for r in analysis.local_rules if r.dp_supported)
            analysis.lp_unsupported = sum(1 for r in analysis.local_rules if not r.dp_supported)
        
        # =====================================================================
        # ANALYZE PRIORITY CONFLICTS
        # =====================================================================
        analysis.priority_conflicts = analyze_priority_conflicts(
            analysis.bgp_rules, 
            analysis.local_rules
        )
        
        # Build summary result
        if analysis.priority_conflicts:
            status = CheckStatus.WARN
            # Count winners
            lp_wins = sum(1 for c in analysis.priority_conflicts if c["winner"] == "LOCAL")
            bgp_wins = sum(1 for c in analysis.priority_conflicts if c["winner"] == "BGP")
            actual = f"{len(analysis.priority_conflicts)} conflicts: LP wins {lp_wins}, BGP wins {bgp_wins}"
            
            analysis.warnings.append(
                f"Priority conflicts detected: {lp_wins} Local Policies override BGP rules (lower priority = wins)"
            )
        else:
            status = CheckStatus.PASS
            actual = f"No conflicts - BGP:{analysis.bgp_total} LP:{analysis.lp_total}"
        
        results.append(FlowCheckResult(
            step="PRI", component="Priority", check_name="Conflict Analysis",
            status=status,
            expected="No overlapping rules, or documented overrides",
            actual=actual,
            command="xraycli /wb_agent/flowspec/*/rules",
            details="Rule: Lower priority number = Higher precedence = WINS"
        ))
        
        # =====================================================================
        # PRIORITY RANGE VALIDATION
        # =====================================================================
        bgp_in_wrong_range = [r for r in analysis.bgp_rules if r.priority >= 0 and r.priority < FLOWSPEC_BGP_PRIORITY_MIN]
        lp_in_wrong_range = [r for r in analysis.local_rules if r.priority >= 0 and r.priority >= FLOWSPEC_BGP_PRIORITY_MIN]
        
        if bgp_in_wrong_range or lp_in_wrong_range:
            status = CheckStatus.FAIL
            actual = f"BGP in LP range: {len(bgp_in_wrong_range)}, LP in BGP range: {len(lp_in_wrong_range)}"
            analysis.problems.append(f"Priority range violation detected!")
        else:
            status = CheckStatus.PASS
            actual = "All rules in correct priority ranges"
        
        results.append(FlowCheckResult(
            step="RNG", component="Priority", check_name="Range Validation",
            status=status,
            expected="BGP: 2M-4M, Local: 0-2M",
            actual=actual,
            command="Priority range check"
        ))
        
        # =====================================================================
        # POLICER ANALYSIS
        # =====================================================================
        bgp_with_policer = [r for r in analysis.bgp_rules if r.has_policer]
        lp_with_policer = [r for r in analysis.local_rules if r.has_policer]
        
        results.append(FlowCheckResult(
            step="POL", component="Policer", check_name="Rate-Limit Policers",
            status=CheckStatus.INFO,
            expected="Policers configured as needed",
            actual=f"BGP: {len(bgp_with_policer)} with policer, LP: {len(lp_with_policer)} with policer",
            command="xraycli rate_limit_policer fields"
        ))
        
        # Update legacy fields
        analysis.total_rules = analysis.bgp_total + analysis.lp_total
        analysis.rules_installed = analysis.bgp_installed + analysis.lp_installed
        
        return results
    
    def check_hw_counters_detailed(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """Detailed HW counters analysis"""
        results = []
        
        # Use interactive shell for xraycli
        success, output = conn.run_xray_command("/wb_agent/flowspec/hw_counters", ncp_id=0, timeout=30)
        
        if success:
            # Parse all counters
            for field, attr in [
                ('hw_rules_write_ok', 'hw_rules_write_ok'),
                ('hw_rules_write_fail', 'hw_rules_write_fail'),
                ('hw_policers_write_ok', 'hw_policers_write_ok'),
                ('hw_policers_write_fail', 'hw_policers_write_fail'),
            ]:
                match = re.search(rf'{field}:\s*(\d+)', output)
                if match:
                    setattr(analysis, attr, int(match.group(1)))
            
            # Determine status
            if analysis.hw_rules_write_fail > 0 or analysis.hw_policers_write_fail > 0:
                status = CheckStatus.FAIL
                analysis.problems.append(
                    f"HW write failures: rules={analysis.hw_rules_write_fail}, policers={analysis.hw_policers_write_fail}"
                )
            else:
                status = CheckStatus.PASS
            
            results.append(FlowCheckResult(
                step="HW", component="Hardware", check_name="Write Counters",
                status=status,
                expected="write_fail = 0",
                actual=f"Rules: OK={analysis.hw_rules_write_ok} FAIL={analysis.hw_rules_write_fail} | Policers: OK={analysis.hw_policers_write_ok} FAIL={analysis.hw_policers_write_fail}",
                command="xraycli /wb_agent/flowspec/hw_counters",
                raw_output=output
            ))
        
        return results
    
    def check_bcm_pmf_detailed(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """
        NCP-level FlowSpec hardware status using 'show flowspec ncp 0'
        """
        results = []
        
        # Use 'show flowspec ncp 0' - works in standard CLI mode
        cmd = "show flowspec ncp 0 | no-more"
        success, output = conn.run_cli_command(cmd, timeout=15)
        
        if success:
            # Parse NCP flowspec output
            installed_match = re.search(r'(\d+)\s+flows?\s+installed', output, re.IGNORECASE)
            pending_match = re.search(r'(\d+)\s+flows?\s+pending', output, re.IGNORECASE)
            failed_match = re.search(r'(\d+)\s+flows?\s+failed', output, re.IGNORECASE)
            
            installed = int(installed_match.group(1)) if installed_match else 0
            pending = int(pending_match.group(1)) if pending_match else 0
            failed = int(failed_match.group(1)) if failed_match else 0
            
            if installed == 0 and 'No flows found' not in output:
                table_entries = len(re.findall(r'^\s*\|.*\|.*\|', output, re.MULTILINE))
                if table_entries > 0:
                    installed = table_entries - 1
            
            analysis.bcm_pmf_entries = installed
            xray_total = analysis.bgp_total + analysis.lp_total
            
            if failed > 0:
                status = CheckStatus.FAIL
                analysis.problems.append(f"NCP FlowSpec: {failed} flows failed installation")
            elif pending > 0:
                status = CheckStatus.WARN
                analysis.warnings.append(f"NCP FlowSpec: {pending} flows pending installation")
            elif installed == 0 and xray_total > 0:
                status = CheckStatus.WARN
                analysis.warnings.append(f"NCP shows 0 flows but xray has {xray_total}")
            else:
                status = CheckStatus.PASS
            
            results.append(FlowCheckResult(
                step="NCP", component="Datapath", check_name="NCP FlowSpec Status",
                status=status,
                expected=f"All rules installed (xray: {xray_total})",
                actual=f"Installed: {installed}, Pending: {pending}, Failed: {failed}",
                command="show flowspec ncp 0",
                details="NCP datapath FlowSpec rule status"
            ))
        else:
            results.append(FlowCheckResult(
                step="NCP", component="Datapath", check_name="NCP FlowSpec Status",
                status=CheckStatus.SKIP,
                expected="NCP FlowSpec command available",
                actual="Command not available or NCP not accessible",
                command="show flowspec ncp 0"
            ))
        
        return results
    
    def check_bcm_hardware_entries(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
        """
        Check BCM PMF hardware entries via wbox-cli (group=24 is FlowSpec PMF).
        Uses interactive shell: run start shell ncp 0 -> wbox-cli bcm diag field entry list group=24
        """
        results = []
        
        # Use wbox-cli via interactive shell
        success, output = conn.run_wbox_command("bcm diag field entry list group=24", ncp_id=0, timeout=60)
        
        if success:
            # Count HW entries
            entry_count = len(re.findall(r'Entry\s+\d+', output))
            
            # Check for errors
            errors = len(re.findall(r'error|fail|invalid', output, re.IGNORECASE))
            
            if errors > 0:
                status = CheckStatus.WARN
                analysis.warnings.append(f"BCM PMF: {errors} errors found")
            else:
                status = CheckStatus.PASS
            
            results.append(FlowCheckResult(
                step="BCM", component="Hardware", check_name="BCM PMF Entries",
                status=status,
                expected="HW entries match software",
                actual=f"{entry_count} entries in group=24 (FlowSpec PMF)",
                command="wbox-cli bcm diag field entry list group=24",
                raw_output=output[:2000] if len(output) > 2000 else output
            ))
        else:
            results.append(FlowCheckResult(
                step="BCM", component="Hardware", check_name="BCM PMF Entries",
                status=CheckStatus.SKIP,
                expected="BCM command available",
                actual=f"Shell access failed: {output[:100]}",
                command="wbox-cli bcm diag field entry list group=24"
            ))
        
        return results
    
    # =========================================================================
    # DEPENDENCY DETECTION (NEW)
    # =========================================================================
    
    def check_dependencies(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[DependencyIssue]:
        """
        Comprehensive dependency check for FlowSpec VPN configuration.
        Detects missing or incomplete configuration with fix suggestions.
        """
        issues = []
        
        # =====================================================================
        # CHECK 1: BGP FlowSpec Address-Families on Global BGP
        # =====================================================================
        cmd = "show config | flatten | include 'address-family.*flowspec'"
        success, output = conn.run_cli_command(cmd)
        
        has_ipv4_flowspec = False
        has_ipv6_flowspec = False
        has_ipv4_flowspec_vpn = False
        has_ipv6_flowspec_vpn = False
        
        if success:
            has_ipv4_flowspec = 'ipv4-flowspec' in output and 'vpn' not in output.split('ipv4-flowspec')[0][-5:]
            has_ipv6_flowspec = 'ipv6-flowspec' in output and 'vpn' not in output.split('ipv6-flowspec')[0][-5:] if 'ipv6-flowspec' in output else False
            has_ipv4_flowspec_vpn = 'ipv4-flowspec-vpn' in output
            has_ipv6_flowspec_vpn = 'ipv6-flowspec-vpn' in output
        
        if not has_ipv4_flowspec and not has_ipv4_flowspec_vpn:
            issues.append(DependencyIssue(
                component="BGP",
                issue="No IPv4-FlowSpec address-family configured on BGP neighbors",
                severity="critical",
                fix_command="""protocols bgp <ASN>
  neighbor <NEIGHBOR-IP>
    address-family ipv4-flowspec
      admin-state enabled
      send-community extended
    !
    address-family ipv4-flowspec-vpn
      admin-state enabled
      send-community extended
    !
  !
!""",
                fix_description="Configure ipv4-flowspec and/or ipv4-flowspec-vpn on BGP neighbors",
                detected_in=cmd
            ))
        
        # =====================================================================
        # CHECK 2: Interface FlowSpec Enabled
        # =====================================================================
        cmd = "show running-config | include 'flowspec enabled'"
        success, output = conn.run_cli_command(cmd)
        
        iface_count = output.count('flowspec enabled') if success else 0
        
        if iface_count == 0:
            issues.append(DependencyIssue(
                component="Interface",
                issue="No interfaces with 'flowspec enabled' - rules will NOT be enforced!",
                severity="critical",
                fix_command="""interfaces
  <interface-name>
    flowspec enabled
  !
!""",
                fix_description="Enable FlowSpec filtering on ingress interfaces",
                detected_in=cmd
            ))
        
        # =====================================================================
        # CHECK 3: VRF FlowSpec Configuration (if VRFs exist)
        # =====================================================================
        cmd = "show network-services vrf | include 'instance '"
        success, output = conn.run_cli_command(cmd)
        
        if success and 'instance' in output:
            vrfs = re.findall(r'instance\s+(\S+)', output)
            
            # Check if VRFs have FlowSpec AF
            for vrf in vrfs[:5]:  # Limit to first 5 VRFs
                cmd_vrf = f"show config | flatten | include 'vrf instance {vrf}.*flowspec'"
                success_vrf, output_vrf = conn.run_cli_command(cmd_vrf)
                
                if success_vrf and 'flowspec' not in output_vrf:
                    issues.append(DependencyIssue(
                        component="VRF",
                        issue=f"VRF '{vrf}' has no FlowSpec address-family - cannot import FlowSpec-VPN routes",
                        severity="warning",
                        fix_command=f"""network-services
  vrf
    instance {vrf}
      protocols
        bgp <ASN>
          address-family ipv4-flowspec
            export-vpn route-target <RT>
            import-vpn route-target <RT>
          !
          address-family ipv6-flowspec
            export-vpn route-target <RT>
            import-vpn route-target <RT>
          !
        !
      !
    !
  !
!""",
                        fix_description=f"Configure FlowSpec AF on VRF {vrf} for FlowSpec-VPN import",
                        detected_in=cmd_vrf
                    ))
        
        # =====================================================================
        # CHECK 4: Local Policy Completeness
        # =====================================================================
        # Check if there are match-classes without policies
        cmd_mc = "show flowspec-local-policies match-classes"
        success_mc, output_mc = conn.run_cli_command(cmd_mc)
        
        cmd_pol = "show flowspec-local-policies policies"
        success_pol, output_pol = conn.run_cli_command(cmd_pol)
        
        cmd_apply = "show config | flatten | include 'apply-policy-to-flowspec'"
        success_apply, output_apply = conn.run_cli_command(cmd_apply)
        
        has_match_classes = success_mc and ('match-class' in output_mc.lower() or 'Match-class' in output_mc)
        has_policies = success_pol and ('policy' in output_pol.lower() and 'No policies' not in output_pol)
        has_apply = success_apply and 'apply-policy-to-flowspec' in output_apply
        
        if has_match_classes and not has_policies:
            issues.append(DependencyIssue(
                component="LocalPolicy",
                issue="Match-classes defined but no policies reference them",
                severity="warning",
                fix_command="""routing-policy
  flowspec-local-policies
    ipv4
      policy <POLICY-NAME>
        match-class <MATCH-CLASS-NAME>
          action-type rate-limit max-rate 0
        !
      !
    !
  !
!""",
                fix_description="Create a policy that references the match-class",
                detected_in=cmd_mc
            ))
        
        if has_policies and not has_apply:
            issues.append(DependencyIssue(
                component="LocalPolicy",
                issue="Policies defined but not applied - rules are NOT active!",
                severity="critical",
                fix_command="""forwarding-options
  flowspec-local
    ipv4
      apply-policy-to-flowspec <POLICY-NAME>
    !
  !
!""",
                fix_description="Apply the policy to activate the local FlowSpec rules",
                detected_in=cmd_apply
            ))
        
        # =====================================================================
        # CHECK 5: Local Policy Match-Class Requirements
        # =====================================================================
        if has_match_classes:
            # Check if match-classes have mandatory dest-ip or source-ip
            cmd_mc_detail = "show config | flatten | include 'match-class\\|dest-ip\\|source-ip'"
            success_mc_detail, output_mc_detail = conn.run_cli_command(cmd_mc_detail)
            
            if success_mc_detail:
                # Simple check: if we have match-class but no dest-ip or source-ip
                has_ip_field = 'dest-ip' in output_mc_detail or 'source-ip' in output_mc_detail
                
                if not has_ip_field:
                    issues.append(DependencyIssue(
                        component="LocalPolicy",
                        issue="Match-class missing mandatory dest-ip or source-ip field",
                        severity="critical",
                        fix_command="""routing-policy
  flowspec-local-policies
    ipv4
      match-class <NAME>
        dest-ip <PREFIX>    ← MANDATORY: At least one IP field required!
        protocol eq 17
        dest-port eq 53
      !
    !
  !
!""",
                        fix_description="Add dest-ip or source-ip to match-class (MANDATORY)",
                        detected_in=cmd_mc_detail
                    ))
        
        # Store issues in analysis
        analysis.dependency_issues = issues
        
        return issues
    
    def show_dependency_report(self, issues: List[DependencyIssue]):
        """Display dependency check results"""
        if not issues:
            if RICH_AVAILABLE:
                console.print(Panel(
                    "[green]✓ All dependencies satisfied![/green]\n\n"
                    "FlowSpec configuration appears complete:\n"
                    "  • BGP FlowSpec AF configured\n"
                    "  • Interfaces with FlowSpec enabled\n"
                    "  • Local policies properly applied (if any)",
                    title="[bold green]Dependency Check: PASSED[/bold green]",
                    border_style="green"
                ))
            else:
                print("\n✓ All dependencies satisfied!")
            return
        
        # Count by severity
        critical = sum(1 for i in issues if i.severity == "critical")
        warnings = sum(1 for i in issues if i.severity == "warning")
        info = sum(1 for i in issues if i.severity == "info")
        
        if RICH_AVAILABLE:
            # Create table of issues
            table = Table(
                title=f"[bold red]Dependency Issues Found: {len(issues)}[/bold red]",
                box=box.ROUNDED,
                border_style="red" if critical > 0 else "yellow"
            )
            table.add_column("#", width=3)
            table.add_column("Severity", width=10)
            table.add_column("Component", width=12)
            table.add_column("Issue", width=50)
            
            for i, issue in enumerate(issues, 1):
                severity_style = {
                    "critical": "[red bold]CRITICAL[/red bold]",
                    "warning": "[yellow]WARNING[/yellow]",
                    "info": "[blue]INFO[/blue]"
                }.get(issue.severity, issue.severity)
                
                table.add_row(
                    str(i),
                    severity_style,
                    issue.component,
                    issue.issue[:50]
                )
            
            console.print(table)
            
            # Show fix suggestions
            console.print("\n[bold cyan]Fix Suggestions:[/bold cyan]\n")
            
            for i, issue in enumerate(issues, 1):
                severity_color = {"critical": "red", "warning": "yellow", "info": "blue"}.get(issue.severity, "white")
                console.print(f"[{severity_color}]#{i}[/{severity_color}] [bold]{issue.fix_description}[/bold]")
                console.print(Panel(
                    f"[green]{issue.fix_command}[/green]",
                    title=f"[dim]{issue.component}[/dim]",
                    border_style="dim"
                ))
                console.print()
            
            # Summary
            summary = f"""
[bold]Summary:[/bold]
  [red]Critical:[/red] {critical} (must fix for FlowSpec to work)
  [yellow]Warnings:[/yellow] {warnings} (recommended fixes)
  [blue]Info:[/blue] {info} (optional improvements)
"""
            console.print(Panel(summary, title="[bold]Dependency Check Complete[/bold]", border_style="cyan"))
        else:
            print(f"\n=== Dependency Issues Found: {len(issues)} ===")
            for i, issue in enumerate(issues, 1):
                print(f"\n{i}. [{issue.severity.upper()}] {issue.component}")
                print(f"   Issue: {issue.issue}")
                print(f"   Fix: {issue.fix_description}")
    
    def preflight_check(self, conn: SSHConnection) -> Tuple[bool, str, Dict]:
        """Quick pre-flight check to see if FlowSpec is configured at all
        
        Uses 'show config | flatten | include flowspec' to check running config FIRST,
        then checks operational state (sessions/routes).
        
        Note: DNOS allows max 3 pipe commands.
        """
        result = {
            "config_bgp_flowspec": False,
            "config_local_policies": False,
            "config_flowspec_interfaces": False,
            "bgp_sessions": 0,
            "bgp_routes": 0,
            "local_policies": 0,
            "config_lines": [],  # Actual config lines found
        }
        
        # =====================================================================
        # STEP 1: Check RUNNING CONFIG for FlowSpec configuration
        # Single command to search entire flattened config (max 3 pipes)
        # =====================================================================
        
        success, output = conn.run_cli_command(
            "show config | flatten | include flowspec", timeout=15
        )
        
        if success and output.strip():
            for line in output.split('\n'):
                line = line.strip()
                # Skip empty lines, prompts, and command echo
                if not line or line.startswith('#') or 'show config' in line.lower():
                    continue
                if 'flowspec' not in line.lower():
                    continue
                    
                # Categorize the config line
                line_lower = line.lower()
                if 'address-family' in line_lower and 'flowspec' in line_lower:
                    result["config_bgp_flowspec"] = True
                    result["config_lines"].append(f"BGP: {line[:70]}")
                elif 'flowspec-local' in line_lower or 'local-policies' in line_lower:
                    result["config_local_policies"] = True
                    result["config_lines"].append(f"Policy: {line[:70]}")
                elif 'forwarding-options' in line_lower:
                    result["config_flowspec_interfaces"] = True
                    result["config_lines"].append(f"Fwd: {line[:70]}")
                elif 'interface' in line_lower or 'flowspec enabled' in line_lower:
                    result["config_flowspec_interfaces"] = True
                    result["config_lines"].append(f"Iface: {line[:70]}")
                else:
                    # Generic flowspec config line
                    result["config_lines"].append(f"Config: {line[:70]}")
        
        # If NO FlowSpec config at all from live command, try cached config
        # Also check if we found ANY config lines (even uncategorized)
        has_config = (result["config_bgp_flowspec"] or 
                     result["config_local_policies"] or 
                     result["config_flowspec_interfaces"] or
                     len(result["config_lines"]) > 0)
        
        if not has_config:
            # =====================================================================
            # FALLBACK: Check CACHED running.txt if live command failed
            # =====================================================================
            hostname = conn.hostname if hasattr(conn, 'hostname') else "unknown"
            cached_config_file = Path(f"/home/dn/SCALER/db/configs/{hostname}/running.txt")
            
            if cached_config_file.exists():
                try:
                    cached_config = cached_config_file.read_text()
                    
                    # Check for FlowSpec patterns in cached config
                    if 'address-family' in cached_config and 'flowspec' in cached_config.lower():
                        result["config_bgp_flowspec"] = True
                        result["config_lines"].append("(from cache) BGP FlowSpec AFI detected")
                    
                    if 'flowspec-local' in cached_config.lower() or 'local-policies' in cached_config.lower():
                        result["config_local_policies"] = True
                        result["config_lines"].append("(from cache) Local policies detected")
                    
                    if 'flowspec enabled' in cached_config.lower():
                        result["config_flowspec_interfaces"] = True
                        # Count interfaces
                        fs_iface_count = cached_config.lower().count('flowspec enabled')
                        result["config_lines"].append(f"(from cache) FlowSpec enabled on {fs_iface_count} interface(s)")
                    
                    has_config = (result["config_bgp_flowspec"] or 
                                 result["config_local_policies"] or 
                                 result["config_flowspec_interfaces"])
                    
                    if has_config:
                        result["config_lines"].append("[dim]Note: Using cached config - live query failed[/dim]")
                        self.log(f"Using cached config for {hostname} - live query returned empty")
                
                except Exception as e:
                    self.log(f"Error reading cached config for {hostname}: {e}")
        
        if not has_config:
            return False, "FlowSpec NOT in running config", result
        
        # =====================================================================
        # STEP 2: Check OPERATIONAL state (only if config exists)
        # Note: Max 2 pipes to stay under limit
        # Check BOTH FlowSpec SAFIs:
        #   - SAFI 133: flowspec (default/global VRF)
        #   - SAFI 134: flowspec-vpn (VPN/VRF contexts)
        # =====================================================================
        
        result["bgp_sessions_global"] = 0  # SAFI 133
        result["bgp_sessions_vpn"] = 0     # SAFI 134
        result["bgp_routes_global"] = 0
        result["bgp_routes_vpn"] = 0
        
        # Check 2a: BGP FlowSpec sessions - SAFI 133 (default VRF)
        success, output = conn.run_cli_command("show bgp ipv4 flowspec summary | no-more", timeout=10)
        if success:
            sessions = len(re.findall(r'Established', output, re.IGNORECASE))
            result["bgp_sessions_global"] = sessions
        
        # Check 2b: BGP FlowSpec sessions - SAFI 134 (VPN)
        success, output = conn.run_cli_command("show bgp ipv4 flowspec-vpn summary | no-more", timeout=10)
        if success:
            sessions = len(re.findall(r'Established', output, re.IGNORECASE))
            result["bgp_sessions_vpn"] = sessions
        
        # Total sessions
        result["bgp_sessions"] = result["bgp_sessions_global"] + result["bgp_sessions_vpn"]
        
        # Check 2c: BGP FlowSpec routes - both SAFIs
        success, output = conn.run_cli_command("show flowspec ipv4 | no-more", timeout=10)
        if success:
            routes = output.count("DstPrefix") + output.count("SrcPrefix") + output.count("Dest:")
            result["bgp_routes"] = routes
        
        # Check 2d: Local policies count
        success, output = conn.run_cli_command("show flowspec-local-policies policies | no-more", timeout=10)
        if success:
            if 'policy' in output.lower() and 'No policies' not in output:
                policy_count = len(re.findall(r'(?:^|\n)\s*policy\s+\S+', output, re.IGNORECASE))
                result["local_policies"] = policy_count
        
        # Build summary
        summary_parts = []
        
        # Config summary
        config_parts = []
        if result["config_bgp_flowspec"]:
            config_parts.append("BGP-FS")
        if result["config_local_policies"]:
            config_parts.append("LocalPol")
        if result["config_flowspec_interfaces"]:
            config_parts.append("Ifaces")
        if config_parts:
            summary_parts.append(f"Config: {'+'.join(config_parts)}")
        
        # Operational summary - show both SAFIs
        session_parts = []
        if result.get("bgp_sessions_global", 0) > 0:
            session_parts.append(f"Global:{result['bgp_sessions_global']}")
        if result.get("bgp_sessions_vpn", 0) > 0:
            session_parts.append(f"VPN:{result['bgp_sessions_vpn']}")
        if session_parts:
            summary_parts.append(f"Sessions({'+'.join(session_parts)})")
        
        if result["bgp_routes"] > 0:
            summary_parts.append(f"Routes: {result['bgp_routes']}")
        if result["local_policies"] > 0:
            summary_parts.append(f"Policies: {result['local_policies']}")
        
        return True, " | ".join(summary_parts), result
    
    def load_cached_analysis(self, device: Dict) -> Optional[DeviceAnalysis]:
        """
        Load cached analysis from snapshots if available and recent
        
        Checks:
        1. wizard_data/snapshots/fsvpn_report_<hostname>_*.json
        2. monitor_data/snapshots/analysis_<hostname>_*.json
        3. monitor_data/latest.json (if hostname matches)
        """
        hostname = device.get("hostname", "unknown")
        
        # Check wizard snapshots - try latest first (fastest)
        if SNAPSHOTS_DIR.exists():
            latest_file = SNAPSHOTS_DIR / f"latest_{hostname}.json"
            if latest_file.exists():
                try:
                    with open(latest_file, 'r') as f:
                        data = json.load(f)
                    cache_time = datetime.fromisoformat(data.get("timestamp", "1970-01-01"))
                    age_seconds = (datetime.now() - cache_time).total_seconds()
                    if age_seconds < CACHE_MAX_AGE_SECONDS:
                        logger.info(f"Loading cached analysis from latest_{hostname}.json (age: {age_seconds:.0f}s)")
                        return self._reconstruct_analysis_from_dict(data)
                except Exception as e:
                    logger.warning(f"Failed to load latest cache: {e}")
            
            # Fallback to timestamped files
            snapshots = sorted(SNAPSHOTS_DIR.glob(f"fsvpn_report_{hostname}_*.json"), reverse=True)
            if not snapshots:
                # Also try analysis_*.json format
                snapshots = sorted(SNAPSHOTS_DIR.glob(f"analysis_{hostname}_*.json"), reverse=True)
            if snapshots:
                try:
                    with open(snapshots[0], 'r') as f:
                        data = json.load(f)
                    # Check if cache is recent
                    cache_time = datetime.fromisoformat(data.get("timestamp", "1970-01-01"))
                    age_seconds = (datetime.now() - cache_time).total_seconds()
                    if age_seconds < CACHE_MAX_AGE_SECONDS:
                        logger.info(f"Loading cached analysis from {snapshots[0]} (age: {age_seconds:.0f}s)")
                        # Reconstruct DeviceAnalysis from saved data
                        return self._reconstruct_analysis_from_dict(data)
                except Exception as e:
                    logger.warning(f"Failed to load cached analysis: {e}")
        
        # Check monitor snapshots
        if MONITOR_DIR.exists():
            monitor_snapshots_dir = MONITOR_DIR / "snapshots"
            if monitor_snapshots_dir.exists():
                snapshots = sorted(monitor_snapshots_dir.glob(f"analysis_{hostname}_*.json"), reverse=True)
                if snapshots:
                    try:
                        with open(snapshots[0], 'r') as f:
                            data = json.load(f)
                        cache_time = datetime.fromisoformat(data.get("timestamp", "1970-01-01"))
                        age_seconds = (datetime.now() - cache_time).total_seconds()
                        if age_seconds < CACHE_MAX_AGE_SECONDS:
                            logger.info(f"Loading cached analysis from monitor {snapshots[0]} (age: {age_seconds:.0f}s)")
                            return self._reconstruct_analysis_from_dict(data)
                    except Exception as e:
                        logger.warning(f"Failed to load monitor cached analysis: {e}")
        
        # Check latest.json from monitor
        latest_file = MONITOR_DIR / "latest.json"
        if latest_file.exists():
            try:
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                if data.get("hostname") == hostname:
                    cache_time = datetime.fromisoformat(data.get("timestamp", "1970-01-01"))
                    age_seconds = (datetime.now() - cache_time).total_seconds()
                    if age_seconds < CACHE_MAX_AGE_SECONDS:
                        logger.info(f"Loading cached analysis from latest.json (age: {age_seconds:.0f}s)")
                        return self._reconstruct_analysis_from_dict(data)
            except Exception as e:
                logger.warning(f"Failed to load latest.json: {e}")
        
        return None
    
    def _reconstruct_analysis_from_dict(self, data: Dict) -> DeviceAnalysis:
        """Reconstruct DeviceAnalysis from saved JSON data"""
        analysis = DeviceAnalysis(
            hostname=data.get("hostname", "unknown"),
            ip=data.get("ip", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            dnos_version=data.get("dnos_version", ""),
        )
        
        # Restore summary fields
        summary = data.get("summary", {})
        analysis.total_rules = summary.get("total_rules", 0)
        analysis.bgp_total = summary.get("bgp_total", 0)
        analysis.bgp_installed = summary.get("bgp_installed", 0)
        analysis.lp_total = summary.get("lp_total", 0)
        analysis.lp_installed = summary.get("lp_installed", 0)
        
        # Restore TCAM data
        tcam = data.get("tcam", {})
        analysis.ipv4_used = tcam.get("ipv4_used", 0)
        analysis.ipv4_capacity = tcam.get("ipv4_capacity", 0)
        analysis.ipv6_used = tcam.get("ipv6_used", 0)
        analysis.ipv6_capacity = tcam.get("ipv6_capacity", 0)
        
        # Restore checks (simplified - just restore status)
        checks_data = data.get("checks", [])
        for check_data in checks_data:
            # Create minimal CheckResult from saved data
            check = CheckResult(
                name=check_data.get("name", ""),
                status=CheckStatus(check_data.get("status", "UNKNOWN")),
                message=check_data.get("message", ""),
            )
            analysis.checks.append(check)
        
        # Restore warnings
        analysis.warnings = data.get("warnings", [])
        
        return analysis
    
    def run_full_analysis(self, device: Dict, use_cache: bool = True) -> DeviceAnalysis:
        """
        Run complete analysis on a device
        
        Args:
            device: Device dictionary
            use_cache: If True, try to load from cache first
        """
        # Try to load from cache first
        if use_cache:
            cached_analysis = self.load_cached_analysis(device)
            if cached_analysis:
                if RICH_AVAILABLE:
                    age_seconds = (datetime.now() - datetime.fromisoformat(cached_analysis.timestamp)).total_seconds()
                    console.print(f"[dim]Using cached analysis (age: {age_seconds:.0f}s)[/dim]")
                else:
                    print("Using cached analysis")
                self.current_analysis = cached_analysis
                return cached_analysis
        
        # No cache or cache expired - run fresh analysis
        conn = self.connect_to_device(device)
        
        analysis = DeviceAnalysis(
            hostname=device.get("hostname", "unknown"),
            ip=device.get("ip", ""),
            timestamp=datetime.now().isoformat()
        )
        
        # Get DNOS version
        success, output = conn.run_cli_command("show system version", timeout=10)
        if success:
            match = re.search(r'Software version:\s*(\S+)', output)
            if match:
                analysis.dnos_version = match.group(1)
        
        # === PRE-FLIGHT CHECK ===
        if RICH_AVAILABLE:
            console.print("[dim]Running pre-flight check...[/dim]")
        
        preflight_ok, preflight_msg, preflight_data = self.preflight_check(conn)
        
        if not preflight_ok:
            if RICH_AVAILABLE:
                console.print(f"\n[yellow]⚠ {preflight_msg}[/yellow]")
                console.print("\n[dim]Pre-flight results (checked running config):[/dim]")
                console.print(f"  BGP FlowSpec in config:    {'Yes' if preflight_data.get('config_bgp_flowspec') else '[red]No[/red]'}")
                console.print(f"  Local Policies in config:  {'Yes' if preflight_data.get('config_local_policies') else '[red]No[/red]'}")
                console.print(f"  FlowSpec interfaces:       {'Yes' if preflight_data.get('config_flowspec_interfaces') else '[red]No[/red]'}")
                
                if preflight_data.get('config_lines'):
                    console.print("\n[dim]Config lines found:[/dim]")
                    for line in preflight_data['config_lines'][:5]:
                        console.print(f"    {line}")
                
                console.print("\n[yellow]Nothing to analyze - configure FlowSpec first.[/yellow]")
                console.print("[dim]Hint: Configure BGP address-family flowspec or local policies[/dim]")
            else:
                print(f"\n⚠ {preflight_msg}")
                print("Nothing to analyze - configure FlowSpec first.")
            
            analysis.warnings.append(preflight_msg)
            return analysis
        
        if RICH_AVAILABLE:
            console.print(f"[green]✓ Pre-flight OK:[/green] {preflight_msg}")
            console.print("[dim]Running full analysis...[/dim]")
        
        # Run all checks - BGP FlowSpec-VPN (IPv4 + IPv6)
        # Format: (function, friendly_name, is_slow)
        #
        # Uses both:
        # - DNOS CLI show commands (fast)
        # - xraycli via interactive shell (for detailed datapath info)
        # - wbox-cli via interactive shell (for BCM hardware info)
        #
        checks = [
            # =================================================================
            # CHECKS ORDERED BY DUT PROCESSING FLOW
            # =================================================================
            #
            # Processing order on DUT:
            # 1. BGP receives UPDATE from peer
            # 2. BGP processes NLRI, stores in RIB
            # 3. VRF import/export applies RT filtering
            # 4. RIB notifies FIB-manager
            # 5. wb_agent receives FlowSpec notification
            # 6. TCAM programming via xray
            # 7. BCM hardware applies rules
            # 8. Rules active on FlowSpec-enabled interfaces
            # 9. Traffic matching and counters
            #
            # =================================================================
            
            # STEP 1: BGP RECEIVE (from peer/RR)
            (self.check_bgp_traces, "1.BGP Traces (Updates)", True),
            (self.check_bgp_sessions, "2.BGP Sessions", False),
            (self.check_bgp_routes, "3.BGP Routes Received", False),
            
            # STEP 2: VRF PROCESSING
            (self.check_vrf_import, "4.VRF RT Import", False),
            (self.check_vrf_flowspec_af, "5.VRF FlowSpec AF", False),
            (self.check_vrf_flowspec_instance, "6.VRF Instance (RIB)", False),
            
            # STEP 3: DATAPATH PROGRAMMING
            (self.check_ncp_installation, "7.NCP Installation", False),
            (self.check_xray_info, "8.XRay TCAM (wb_agent)", True),
            (self.check_hw_counters, "9.HW Write Status", True),
            
            # STEP 4: HARDWARE
            (self.check_bcm_hardware_entries, "10.BCM PMF Hardware", True),
            (self.check_bcm_pmf_detailed, "11.NCP FlowSpec Status", False),
            
            # STEP 5: INTERFACE APPLICATION
            (self.check_flowspec_interfaces, "12.FlowSpec Interfaces", False),
            
            # STEP 6: TRAFFIC MATCHING
            (self.check_match_counters, "13.Traffic Counters", False),
            
            # LOCAL POLICIES (separate path)
            (self.check_local_policies_config, "LP1.Local Policies Config", False),
            (self.check_bcm_tcam_entries, "LP2.Local Policies NCP", False),
            (self.check_local_policies_xray, "LP3.Local Policies XRay", True),
            (self.check_local_policies_counters, "LP4.Local Policies Counters", False),
            
            # IPv6 (parallel path)
            (self.check_bgp_sessions_ipv6, "v6.BGP IPv6-FlowSpec", False),
            (self.check_xray_info_ipv6, "v6.IPv6 XRay TCAM", True),
            (self.check_local_policies_xray_ipv6, "v6.IPv6 LP XRay", True),
            
            # DETAILED ANALYSIS
            (self.check_detailed_rules_analysis, "Detailed Rules Analysis", True),
            (self.check_hw_counters_detailed, "HW Counters Detailed", True),
            (self.check_bcm_pmf_detailed, "NCP FlowSpec Status", False),
        ]
        
        total_checks = len(checks)
        
        # =====================================================================
        # MULTI-THREADED EXECUTION
        # Each check opens its own SSH session, so we can run them in parallel
        # =====================================================================
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading
        
        # Thread-safe result storage
        results_lock = threading.Lock()
        check_results = {}  # {check_name: (results, status_str, error)}
        completed_count = [0]  # Use list to allow modification in nested function
        
        def run_check(check_info):
            """Run a single check in a thread"""
            check_func, check_name, is_slow = check_info
            try:
                results = check_func(conn, analysis)
                
                # Count results
                fail_count = sum(1 for r in results if r.status == CheckStatus.FAIL)
                warn_count = sum(1 for r in results if r.status == CheckStatus.WARN)
                skip_count = sum(1 for r in results if r.status == CheckStatus.SKIP)
                
                # Build status indicator
                slow_indicator = " (slow)" if is_slow else ""
                if fail_count > 0:
                    status_str = f"[red]✗ FAIL ({fail_count})[/red]" if RICH_AVAILABLE else f"✗ FAIL ({fail_count})"
                elif warn_count > 0:
                    status_str = f"[yellow]⚠ WARN ({warn_count})[/yellow]" if RICH_AVAILABLE else f"⚠ WARN ({warn_count})"
                elif skip_count > 0:
                    status_str = f"[dim]○ SKIP[/dim]" if RICH_AVAILABLE else "○ SKIP"
                else:
                    status_str = f"[green]✓ OK[/green]" if RICH_AVAILABLE else "✓ OK"
                
                return (check_name, results, status_str + slow_indicator, None)
            except Exception as e:
                return (check_name, [], None, str(e)[:50])
        
        # Use ThreadPoolExecutor for parallel execution
        # Limit to 6 concurrent SSH sessions to avoid overwhelming the device
        max_workers = min(6, total_checks)
        
        if RICH_AVAILABLE:
            console.print(f"[dim]Running {total_checks} checks in parallel (max {max_workers} threads)...[/dim]")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all checks
            future_to_check = {executor.submit(run_check, check): check for check in checks}
            
            # Process results as they complete
            for future in as_completed(future_to_check):
                check_info = future_to_check[future]
                check_name = check_info[1]
                
                try:
                    name, results, status_str, error = future.result()
                    
                    with results_lock:
                        completed_count[0] += 1
                        count = completed_count[0]
                        
                        if error:
                            if RICH_AVAILABLE:
                                console.print(f"  [{count:2d}/{total_checks}] {name:<35} [red]ERROR: {error}[/red]")
                            else:
                                print(f"  [{count:2d}/{total_checks}] {name:<35} ERROR: {error}")
                            analysis.checks.append(FlowCheckResult(
                                step="?", component="error",
                                check_name=name,
                                status=CheckStatus.FAIL,
                                expected="Check success",
                                actual=f"Error: {error}",
                                command=""
                            ))
                        else:
                            analysis.checks.extend(results)
                            if RICH_AVAILABLE:
                                console.print(f"  [{count:2d}/{total_checks}] {name:<35} {status_str}")
                            else:
                                print(f"  [{count:2d}/{total_checks}] {name:<35} {status_str}")
                
                except Exception as e:
                    with results_lock:
                        completed_count[0] += 1
                        count = completed_count[0]
                        if RICH_AVAILABLE:
                            console.print(f"  [{count:2d}/{total_checks}] {check_name:<35} [red]EXCEPTION: {str(e)[:30]}[/red]")
                        else:
                            print(f"  [{count:2d}/{total_checks}] {check_name:<35} EXCEPTION: {str(e)[:30]}")
        
        return analysis
    
    # =========================================================================
    # TRACE EXTRACTION
    # =========================================================================
    
    def extract_traces(self, conn: SSHConnection, hostname: str) -> Dict[str, str]:
        """Extract FlowSpec traces from containers"""
        traces = {}
        
        containers_cmds = {
            "bgpd (NCC0)": "run start shell -c 'ncc0' command 'tail -300 /var/log/bgpd_traces 2>/dev/null | grep -i flowspec'",
            "rib-manager (NCC0)": "run start shell -c 'ncc0' command 'tail -300 /var/log/rib-manager_traces 2>/dev/null | grep -i flowspec'",
            "fib-manager (NCC0)": "run start shell -c 'ncc0' command 'tail -300 /var/log/fib-manager_traces 2>/dev/null | grep -i flowspec'",
            "wb_agent (NCP0)": "run start shell -c 'ncp0' command 'tail -300 /var/log/wb_agent_traces 2>/dev/null | grep -i flowspec'",
        }
        
        for name, cmd in containers_cmds.items():
            success, output = conn.run_cli_command(cmd, timeout=60)
            if success and output.strip() and len(output) > 50:
                traces[name] = output
        
        return traces
    
    # =========================================================================
    # OUTPUT DISPLAY
    # =========================================================================
    
    def print_quick_summary(self, analysis: DeviceAnalysis):
        """Print a CLEAN, actionable summary - replaces verbose flow diagram"""
        if not RICH_AVAILABLE:
            self._print_summary_simple(analysis)
            return
        
        # Count statuses
        passed = sum(1 for c in analysis.checks if c.status == CheckStatus.PASS)
        failed = sum(1 for c in analysis.checks if c.status == CheckStatus.FAIL)
        warned = sum(1 for c in analysis.checks if c.status == CheckStatus.WARN)
        total = len(analysis.checks)
        
        # Overall status
        if failed > 0:
            status_icon = "[red bold]✗ ISSUES FOUND[/red bold]"
            status_color = "red"
        elif warned > 0:
            status_icon = "[yellow bold]⚠ WARNINGS[/yellow bold]"
            status_color = "yellow"
        else:
            status_icon = "[green bold]✓ ALL OK[/green bold]"
            status_color = "green"
        
        # Build clean summary
        lines = []
        lines.append(f"[bold]{analysis.hostname}[/bold] - {status_icon}")
        lines.append("")
        
        # Quick stats in a simple format
        lines.append("[bold cyan]═══ FlowSpec Status ═══[/bold cyan]")
        lines.append("")
        
        # BGP FlowSpec
        bgp_status = "[green]✓[/green]" if analysis.bgp_total > 0 else "[dim]○[/dim]"
        lines.append(f"  BGP FlowSpec:    {bgp_status} {analysis.bgp_total} rules ({analysis.bgp_installed} installed)")
        
        # Local Policies
        lp_status = "[green]✓[/green]" if analysis.lp_total > 0 else "[dim]○[/dim]"
        lines.append(f"  Local Policies:  {lp_status} {analysis.lp_total} rules ({analysis.lp_installed} installed)")
        
        # TCAM
        tcam_pct = (analysis.ipv4_used / analysis.ipv4_capacity * 100) if analysis.ipv4_capacity else 0
        tcam_status = "[green]✓[/green]" if tcam_pct < 75 else "[yellow]⚠[/yellow]" if tcam_pct < 95 else "[red]✗[/red]"
        lines.append(f"  TCAM Usage:      {tcam_status} {analysis.ipv4_used}/{analysis.ipv4_capacity} ({tcam_pct:.1f}%)")
        
        # HW Errors
        hw_fails = analysis.hw_rules_write_fail + analysis.hw_policers_write_fail
        hw_status = "[green]✓[/green]" if hw_fails == 0 else "[red]✗[/red]"
        lines.append(f"  HW Writes:       {hw_status} {hw_fails} failures")
        
        # VRFs
        vrf_status = "[green]✓[/green]" if analysis.vrf_count > 0 else "[dim]○[/dim]"
        lines.append(f"  VRFs:            {vrf_status} {analysis.vrf_count} with FlowSpec AF")
        
        lines.append("")
        lines.append(f"[dim]Checks: {passed} passed, {failed} failed, {warned} warnings[/dim]")
        
        console.print(Panel("\n".join(lines), title="[bold]Quick Summary[/bold]", border_style=status_color))
        
        # Show problems/warnings if any - simplified
        if analysis.problems:
            console.print(Panel(
                "\n".join([f"[red]✗[/red] {p}" for p in analysis.problems[:5]]),  # Max 5
                title="[bold red]Problems[/bold red]",
                border_style="red"
            ))
        
        if analysis.warnings:
            console.print(Panel(
                "\n".join([f"[yellow]⚠[/yellow] {w}" for w in analysis.warnings[:5]]),  # Max 5
                title="[bold yellow]Warnings[/bold yellow]",
                border_style="yellow"
            ))
        
        # ACTIONABLE: What to do next
        next_steps = []
        
        if analysis.lp_total == 0 and any("local-policies" in str(c.raw_output).lower() for c in analysis.checks if hasattr(c, 'raw_output')):
            next_steps.append("Local policy defined but NOT applied. Add:")
            next_steps.append("  [cyan]forwarding-options flowspec-local ipv4 apply-policy-to-flowspec <POLICY-NAME>[/cyan]")
        
        if analysis.vrf_count == 0 and analysis.bgp_total == 0:
            next_steps.append("No VRFs with FlowSpec. For VRF-based FlowSpec, add:")
            next_steps.append("  [cyan]network-services vrf instance <VRF> address-family ipv4-flowspec[/cyan]")
        
        if analysis.bgp_total == 0 and analysis.lp_total == 0:
            next_steps.append("No FlowSpec rules. Either configure BGP FlowSpec or Local Policies.")
        
        if hw_fails > 0:
            next_steps.append("HW write failures! Check TCAM capacity and retry:")
            next_steps.append("  [cyan]request retry-install flowspec-local-policy-rules ipv4[/cyan]")
        
        if next_steps:
            console.print(Panel(
                "\n".join(next_steps),
                title="[bold green]Next Steps[/bold green]",
                border_style="green"
            ))
    
    def print_flow_diagram(self, analysis: DeviceAnalysis):
        """Print visual flowchart showing DUT processing order"""
        if not RICH_AVAILABLE:
            self._print_flow_simple(analysis)
            return
        
        # Build flowchart showing processing order on DUT
        # Group checks by processing stage
        stages = [
            ("1. BGP RECEIVE", ["BGP-Traces", "BGP"], "Peer/RR → UPDATE → bgpd"),
            ("2. VRF PROCESS", ["VRF", "VRF-Instance"], "RT import → RIB install"),
            ("3. DATAPATH", ["NCP", "wb_agent", "Datapath"], "FIB → wb_agent → xray"),
            ("4. HARDWARE", ["Hardware", "TCAM"], "BCM PMF → ASIC"),
            ("5. INTERFACES", ["Interfaces"], "FlowSpec-enabled ports"),
            ("6. TRAFFIC", ["Counters"], "Match → Action → Count"),
            ("LP. LOCAL-POL", ["LocalPolicies", "LocalPolicy"], "Config → NCP → HW"),
            ("v6. IPv6", ["BGP-IPv6", "wb_agent-IPv6", "LocalPolicies-IPv6"], "IPv6 FlowSpec path"),
        ]
        
        # Create flowchart text
        flowchart_lines = []
        flowchart_lines.append(f"[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]")
        flowchart_lines.append(f"[bold cyan]║     FlowSpec VPN Processing Flow - {analysis.hostname:<24} ║[/bold cyan]")
        flowchart_lines.append(f"[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]")
        flowchart_lines.append("")
        
        for stage_name, components, description in stages:
            # Find checks for this stage
            stage_checks = [c for c in analysis.checks if c.component in components]
            
            if not stage_checks:
                continue
            
            # Determine overall status for stage
            has_fail = any(c.status == CheckStatus.FAIL for c in stage_checks)
            has_warn = any(c.status == CheckStatus.WARN for c in stage_checks)
            all_pass = all(c.status in [CheckStatus.PASS, CheckStatus.INFO] for c in stage_checks)
            
            if has_fail:
                stage_icon = "[red]✗[/red]"
                stage_color = "red"
            elif has_warn:
                stage_icon = "[yellow]⚠[/yellow]"
                stage_color = "yellow"
            elif all_pass:
                stage_icon = "[green]✓[/green]"
                stage_color = "green"
            else:
                stage_icon = "[blue]ℹ[/blue]"
                stage_color = "blue"
            
            # Stage header with arrow
            flowchart_lines.append(f"    {stage_icon} [{stage_color}]┌─ {stage_name} ─────────────────────────────────────┐[/{stage_color}]")
            flowchart_lines.append(f"      [{stage_color}]│[/{stage_color}] [dim]{description}[/dim]")
            
            # Individual checks
            for check in stage_checks:
                check_icon = {
                    CheckStatus.PASS: "[green]✓[/green]",
                    CheckStatus.FAIL: "[red]✗[/red]",
                    CheckStatus.WARN: "[yellow]⚠[/yellow]",
                    CheckStatus.INFO: "[blue]ℹ[/blue]",
                    CheckStatus.SKIP: "[dim]○[/dim]"
                }.get(check.status, "?")
                
                # Truncate actual for display
                actual_short = check.actual[:40] + "..." if len(check.actual) > 40 else check.actual
                flowchart_lines.append(f"      [{stage_color}]│[/{stage_color}]   {check_icon} {check.check_name}: {actual_short}")
            
            flowchart_lines.append(f"      [{stage_color}]└────────────────────────────────────────────────────┘[/{stage_color}]")
            flowchart_lines.append(f"      [{stage_color}]         ↓[/{stage_color}]")
        
        # Final status
        total_pass = sum(1 for c in analysis.checks if c.status == CheckStatus.PASS)
        total_fail = sum(1 for c in analysis.checks if c.status == CheckStatus.FAIL)
        total_warn = sum(1 for c in analysis.checks if c.status == CheckStatus.WARN)
        
        flowchart_lines.append("")
        if total_fail > 0:
            flowchart_lines.append(f"    [red]══════════════════════════════════════════════════════════[/red]")
            flowchart_lines.append(f"    [red]  FLOW STATUS: BLOCKED - {total_fail} checks failed[/red]")
            flowchart_lines.append(f"    [red]══════════════════════════════════════════════════════════[/red]")
        elif total_warn > 0:
            flowchart_lines.append(f"    [yellow]══════════════════════════════════════════════════════════[/yellow]")
            flowchart_lines.append(f"    [yellow]  FLOW STATUS: PARTIAL - {total_warn} warnings[/yellow]")
            flowchart_lines.append(f"    [yellow]══════════════════════════════════════════════════════════[/yellow]")
        else:
            flowchart_lines.append(f"    [green]══════════════════════════════════════════════════════════[/green]")
            flowchart_lines.append(f"    [green]  FLOW STATUS: OK - All {total_pass} checks passed[/green]")
            flowchart_lines.append(f"    [green]══════════════════════════════════════════════════════════[/green]")
        
        console.print(Panel("\n".join(flowchart_lines), title="Processing Flow", border_style="cyan"))
    
    def _print_flow_simple(self, analysis: DeviceAnalysis):
        """Simple text flow diagram"""
        print(f"\n{'='*60}")
        print(f"FlowSpec VPN Flow - {analysis.hostname}")
        print(f"{'='*60}")
        for check in analysis.checks:
            print(f"  [{check.step}] {check.status.value} {check.component}: {check.check_name}")
            print(f"       {check.actual}")
    
    def print_summary_table(self, analysis: DeviceAnalysis):
        """Print summary table"""
        if not RICH_AVAILABLE:
            self._print_summary_simple(analysis)
            return
        
        table = Table(title=f"Analysis Summary - {analysis.hostname}", box=box.ROUNDED)
        table.add_column("Step", width=4)
        table.add_column("Component", width=12)
        table.add_column("Check", width=30)
        table.add_column("Status", width=6, justify="center")
        table.add_column("Expected", width=22)
        table.add_column("Actual", width=22)
        
        for check in analysis.checks:
            status_style = {
                CheckStatus.PASS: "green",
                CheckStatus.FAIL: "red",
                CheckStatus.WARN: "yellow",
                CheckStatus.INFO: "blue"
            }.get(check.status, "white")
            
            table.add_row(
                check.step,
                check.component,
                check.check_name,
                f"[{status_style}]{check.status.value}[/{status_style}]",
                check.expected[:22],
                check.actual[:22]
            )
        
        console.print(table)
        
        # Issues panels
        if analysis.problems:
            console.print(Panel(
                "\n".join([f"[red]✗[/red] {p}" for p in analysis.problems]),
                title="[bold red]Problems[/bold red]",
                border_style="red"
            ))
        
        if analysis.warnings:
            console.print(Panel(
                "\n".join([f"[yellow]⚠[/yellow] {w}" for w in analysis.warnings]),
                title="[bold yellow]Warnings[/bold yellow]",
                border_style="yellow"
            ))
        
        if analysis.info_messages:
            console.print(Panel(
                "\n".join([f"[blue]ℹ[/blue] {m}" for m in analysis.info_messages]),
                title="[bold blue]Info[/bold blue]",
                border_style="blue"
            ))
        
        # Detailed summary with priority info (IPv4 + IPv6)
        summary = f"""
[bold]Device:[/bold] {analysis.hostname} ({analysis.ip})
[bold]Version:[/bold] {analysis.dnos_version}
[bold]Time:[/bold] {analysis.timestamp}

[bold cyan]┌─ BGP FlowSpec IPv4 (Priority 2M-4M) ───────────────┐[/bold cyan]
[bold]  Total:[/bold]       {analysis.bgp_total}
[bold]  Supported:[/bold]   {analysis.bgp_installed}
[bold]  Unsupported:[/bold] {analysis.bgp_unsupported}

[bold blue]┌─ BGP FlowSpec IPv6 (Priority 2M-4M) ───────────────┐[/bold blue]
[bold]  Total:[/bold]       {analysis.bgp_total_ipv6}
[bold]  Supported:[/bold]   {analysis.bgp_installed_ipv6}
[bold]  Unsupported:[/bold] {analysis.bgp_unsupported_ipv6}

[bold green]┌─ Local Policies IPv4 (Priority 0-2M) ★ WINS ★ ────┐[/bold green]
[bold]  Total:[/bold]       {analysis.lp_total}
[bold]  Supported:[/bold]   {analysis.lp_installed}
[bold]  Unsupported:[/bold] {analysis.lp_unsupported}

[bold green]┌─ Local Policies IPv6 (Priority 0-2M) ★ WINS ★ ────┐[/bold green]
[bold]  Total:[/bold]       {analysis.lp_total_ipv6}
[bold]  Supported:[/bold]   {analysis.lp_installed_ipv6}
[bold]  Unsupported:[/bold] {analysis.lp_unsupported_ipv6}

[bold yellow]┌─ TCAM Capacity (Shared) ───────────────────────────┐[/bold yellow]
[bold]  IPv4:[/bold] {analysis.ipv4_used}/{analysis.ipv4_capacity} ({(analysis.ipv4_used/analysis.ipv4_capacity*100) if analysis.ipv4_capacity else 0:.1f}%)
[bold]  IPv6:[/bold] {analysis.ipv6_used}/{analysis.ipv6_capacity} ({(analysis.ipv6_used/analysis.ipv6_capacity*100) if analysis.ipv6_capacity else 0:.1f}%)
[bold]  BCM PMF:[/bold] {analysis.bcm_pmf_entries} HW entries

[bold red]┌─ HW Counters ──────────────────────────────────────┐[/bold red]
[bold]  Rules:[/bold]    OK={analysis.hw_rules_write_ok} FAIL={analysis.hw_rules_write_fail}
[bold]  Policers:[/bold] OK={analysis.hw_policers_write_ok} FAIL={analysis.hw_policers_write_fail}

[bold magenta]┌─ Priority Conflicts ───────────────────────────────┐[/bold magenta]
[bold]  Overlaps:[/bold] {len(analysis.priority_conflicts)} (Local Policies win when lower priority)

[bold]VRFs:[/bold] {analysis.vrf_count} with FlowSpec enabled
"""
        console.print(Panel(summary, title="[bold cyan]Detailed Summary[/bold cyan]", border_style="cyan"))
        
        # Print detailed rules table if we have rules
        self.print_rules_table(analysis)
    
    def _print_summary_simple(self, analysis: DeviceAnalysis):
        """Simple text summary"""
        print(f"\nSummary for {analysis.hostname}")
        print(f"  Version: {analysis.dnos_version}")
        print(f"  Rules: {analysis.total_rules} total, {analysis.rules_installed} installed")
        print(f"  Problems: {len(analysis.problems)}, Warnings: {len(analysis.warnings)}")
    
    def print_rules_table(self, analysis: DeviceAnalysis):
        """Print detailed rules table with priority information"""
        if not RICH_AVAILABLE:
            return
        
        # Combine and sort all rules by priority (lower first = wins)
        all_rules = []
        for rule in analysis.bgp_rules:
            all_rules.append(rule)
        for rule in analysis.local_rules:
            all_rules.append(rule)
        
        if not all_rules:
            console.print("[dim]No rules to display[/dim]")
            return
        
        # Sort by priority (lower wins)
        all_rules.sort(key=lambda r: r.priority if r.priority >= 0 else 999999999)
        
        # Create table
        table = Table(
            title="FlowSpec Rules by Priority (Lower = WINS)",
            box=box.ROUNDED,
            show_lines=True
        )
        table.add_column("#", width=3, style="dim")
        table.add_column("Source", width=6)
        table.add_column("Priority", width=12, justify="right")
        table.add_column("NLRI", width=40, overflow="fold")
        table.add_column("Supported", width=9, justify="center")
        table.add_column("Policer", width=8, justify="center")
        
        for i, rule in enumerate(all_rules[:20], 1):  # Limit to 20 rows
            # Source styling
            if rule.source == "LOCAL":
                source_style = "[green bold]LOCAL[/green bold]"
                priority_style = f"[green]{rule.priority:,}[/green]"
            else:
                source_style = "[blue]BGP[/blue]"
                priority_style = f"[blue]{rule.priority:,}[/blue]"
            
            # Supported status
            if rule.dp_supported:
                supported = "[green]✓ Yes[/green]"
            else:
                supported = "[red]✗ No[/red]"
            
            # Policer
            if rule.has_policer:
                policer = f"[yellow]{rule.policer_rate_bps:,}[/yellow]"
            else:
                policer = "[dim]-[/dim]"
            
            # NLRI (truncate if needed)
            nlri_display = rule.nlri[:40] if rule.nlri else rule.nlri_hex[:20]
            
            table.add_row(
                str(i),
                source_style,
                priority_style,
                nlri_display,
                supported,
                policer
            )
        
        console.print(table)
        
        if len(all_rules) > 20:
            console.print(f"[dim]... and {len(all_rules) - 20} more rules[/dim]")
        
        # Priority legend
        console.print(Panel(
            "[green bold]LOCAL POLICIES[/green bold] (Priority 0 - 1,999,999) → [green]★ WINS ★[/green] (matched first in TCAM)\n"
            "[blue]BGP FLOWSPEC[/blue] (Priority 2,000,000 - 4,000,000) → Matched after local policies\n\n"
            "[yellow]⚠ When TCAM is FULL:[/yellow] First-installed wins, priority ignored!",
            title="Priority Legend",
            border_style="dim"
        ))
        
        # Show conflicts if any
        if analysis.priority_conflicts:
            self.print_conflicts_table(analysis)
    
    def print_conflicts_table(self, analysis: DeviceAnalysis):
        """Print priority conflicts table"""
        if not RICH_AVAILABLE or not analysis.priority_conflicts:
            return
        
        table = Table(
            title="Priority Conflicts (Local Policy Overrides)",
            box=box.ROUNDED,
            border_style="yellow"
        )
        table.add_column("Prefix", width=20)
        table.add_column("Local Priority", width=12, justify="right")
        table.add_column("BGP Priority", width=12, justify="right")
        table.add_column("Winner", width=8, justify="center")
        table.add_column("Reason", width=30)
        
        for conflict in analysis.priority_conflicts[:10]:
            winner_style = "[green bold]LOCAL[/green bold]" if conflict["winner"] == "LOCAL" else "[blue]BGP[/blue]"
            
            table.add_row(
                conflict["prefix"][:20],
                f"[green]{conflict['local_priority']:,}[/green]",
                f"[blue]{conflict['bgp_priority']:,}[/blue]",
                winner_style,
                conflict["reason"][:30]
            )
        
        console.print(table)
        
        if len(analysis.priority_conflicts) > 10:
            console.print(f"[dim]... and {len(analysis.priority_conflicts) - 10} more conflicts[/dim]")
    
    def save_report(self, analysis: DeviceAnalysis) -> Path:
        """Save analysis report to file (also used for caching)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fsvpn_report_{analysis.hostname}_{timestamp}.json"
        filepath = SNAPSHOTS_DIR / filename
        
        # Also save as latest for quick access
        latest_file = SNAPSHOTS_DIR / f"latest_{analysis.hostname}.json"
        
        data = {
            "hostname": analysis.hostname,
            "ip": analysis.ip,
            "timestamp": analysis.timestamp,
            "dnos_version": analysis.dnos_version,
            "summary": {
                "total_rules": analysis.total_rules,
                "bgp_total": analysis.bgp_total,
                "bgp_installed": analysis.bgp_installed,
                "bgp_unsupported": analysis.bgp_unsupported,
                "lp_total": analysis.lp_total,
                "lp_installed": analysis.lp_installed,
                "lp_unsupported": analysis.lp_unsupported,
                "priority_conflicts": len(analysis.priority_conflicts),
            },
            "tcam": {
                "ipv4_used": analysis.ipv4_used,
                "ipv4_capacity": analysis.ipv4_capacity,
                "ipv6_used": analysis.ipv6_used,
                "ipv6_capacity": analysis.ipv6_capacity,
                "bcm_pmf_entries": analysis.bcm_pmf_entries,
            },
            "hw_counters": {
                "rules_write_ok": analysis.hw_rules_write_ok,
                "rules_write_fail": analysis.hw_rules_write_fail,
                "policers_write_ok": analysis.hw_policers_write_ok,
                "policers_write_fail": analysis.hw_policers_write_fail,
            },
            "priority_reference": {
                "local_policies_range": "0 - 1,999,999 (WINS - matched first)",
                "bgp_flowspec_range": "2,000,000 - 4,000,000 (matched after local)",
                "tcam_full_behavior": "First-installed wins when TCAM is full"
            },
            "bgp_rules": [
                {
                    "nlri": r.nlri, "priority": r.priority,
                    "supported": r.dp_supported, "has_policer": r.has_policer
                }
                for r in analysis.bgp_rules
            ],
            "local_rules": [
                {
                    "nlri": r.nlri, "priority": r.priority,
                    "supported": r.dp_supported, "has_policer": r.has_policer
                }
                for r in analysis.local_rules
            ],
            "conflicts": [
                {
                    "prefix": c["prefix"],
                    "local_priority": c["local_priority"],
                    "bgp_priority": c["bgp_priority"],
                    "winner": c["winner"]
                }
                for c in analysis.priority_conflicts
            ],
            "problems": analysis.problems,
            "warnings": analysis.warnings,
            "checks": [
                {
                    "step": c.step, "component": c.component,
                    "check": c.check_name, "status": c.status.value,
                    "expected": c.expected, "actual": c.actual
                }
                for c in analysis.checks
            ]
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        # Also save as latest for quick cache access
        latest_file = SNAPSHOTS_DIR / f"latest_{analysis.hostname}.json"
        try:
            with open(latest_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save latest cache: {e}")
        
        return filepath
    
    # =========================================================================
    # MULTI-DEVICE ANALYSIS (NEW)
    # =========================================================================
    
    def run_multi_device_analysis(self) -> Dict[str, DeviceAnalysis]:
        """Run analysis on multiple devices in parallel using ThreadPoolExecutor"""
        devices = self.discover_devices()
        
        if not devices:
            if RICH_AVAILABLE:
                console.print("[yellow]No devices found in configuration.[/yellow]")
            return {}
        
        if RICH_AVAILABLE:
            console.print(f"\n[bold cyan]Multi-Device Analysis[/bold cyan]")
            console.print(f"[dim]Analyzing {len(devices)} devices in parallel...[/dim]\n")
        else:
            print(f"\nMulti-Device Analysis: {len(devices)} devices")
        
        results: Dict[str, DeviceAnalysis] = {}
        progress_lock = threading.Lock()
        device_status: Dict[str, str] = {d.get('hostname', f'device-{i}'): 'pending' for i, d in enumerate(devices)}
        
        def analyze_single_device(device: Dict) -> Tuple[str, Optional[DeviceAnalysis]]:
            """Analyze a single device (runs in thread)"""
            hostname = device.get('hostname', 'unknown')
            try:
                with progress_lock:
                    device_status[hostname] = 'running'
                
                analysis = self.run_full_analysis(device)
                
                with progress_lock:
                    device_status[hostname] = 'complete'
                
                return hostname, analysis
            except Exception as e:
                with progress_lock:
                    device_status[hostname] = f'error: {str(e)[:30]}'
                return hostname, None
        
        # Run parallel analysis
        max_workers = min(len(devices), 4)  # Limit to 4 parallel connections
        
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"Analyzing {len(devices)} devices...", total=len(devices))
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {executor.submit(analyze_single_device, dev): dev for dev in devices}
                    
                    for future in as_completed(futures):
                        hostname, analysis = future.result()
                        if analysis:
                            results[hostname] = analysis
                        progress.advance(task)
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(analyze_single_device, dev): dev for dev in devices}
                
                for future in as_completed(futures):
                    hostname, analysis = future.result()
                    if analysis:
                        results[hostname] = analysis
                    print(f"  ✓ {hostname}")
        
        # Display comparison summary
        self.show_multi_device_comparison(results)
        
        return results
    
    def show_multi_device_comparison(self, results: Dict[str, DeviceAnalysis]):
        """Display side-by-side comparison of multiple device analyses"""
        if not results:
            if RICH_AVAILABLE:
                console.print("[yellow]No results to compare.[/yellow]")
            return
        
        if RICH_AVAILABLE:
            # Create comparison table
            table = Table(
                title=f"[bold cyan]Multi-Device FlowSpec Comparison ({len(results)} devices)[/bold cyan]",
                box=box.ROUNDED,
                show_lines=True
            )
            
            table.add_column("Metric", style="cyan", width=25)
            for hostname in results.keys():
                table.add_column(hostname[:15], width=15, justify="center")
            
            # Collect metrics
            metrics = [
                ("DNOS Version", lambda a: a.dnos_version[:12] if a.dnos_version else "N/A"),
                ("─── IPv4 ───", lambda a: ""),
                ("BGP Rules (IPv4)", lambda a: str(a.bgp_total)),
                ("Local Policies (IPv4)", lambda a: str(a.lp_total)),
                ("TCAM IPv4 Used", lambda a: f"{a.ipv4_used}/{a.ipv4_capacity}"),
                ("─── IPv6 ───", lambda a: ""),
                ("BGP Rules (IPv6)", lambda a: str(a.bgp_total_ipv6)),
                ("Local Policies (IPv6)", lambda a: str(a.lp_total_ipv6)),
                ("TCAM IPv6 Used", lambda a: f"{a.ipv6_used}/{a.ipv6_capacity}"),
                ("─── Status ───", lambda a: ""),
                ("Problems", lambda a: f"[red]{len(a.problems)}[/red]" if a.problems else "[green]0[/green]"),
                ("Warnings", lambda a: f"[yellow]{len(a.warnings)}[/yellow]" if a.warnings else "[green]0[/green]"),
                ("Dependency Issues", lambda a: f"[red]{len(a.dependency_issues)}[/red]" if a.dependency_issues else "[green]0[/green]"),
                ("HW Write Failures", lambda a: f"[red]{a.hw_rules_write_fail}[/red]" if a.hw_rules_write_fail > 0 else "[green]0[/green]"),
            ]
            
            for metric_name, metric_fn in metrics:
                if metric_name.startswith("───"):
                    # Section header
                    row = [f"[bold]{metric_name}[/bold]"] + ["" for _ in results]
                else:
                    row = [metric_name] + [metric_fn(a) for a in results.values()]
                table.add_row(*row)
            
            console.print(table)
            
            # Show cross-device validation
            self.validate_cross_device(results)
        else:
            print("\n=== Multi-Device Comparison ===")
            for hostname, analysis in results.items():
                print(f"\n{hostname}:")
                print(f"  BGP Rules: {analysis.bgp_total} IPv4, {analysis.bgp_total_ipv6} IPv6")
                print(f"  Local Policies: {analysis.lp_total} IPv4, {analysis.lp_total_ipv6} IPv6")
                print(f"  Problems: {len(analysis.problems)}")
    
    def validate_cross_device(self, results: Dict[str, DeviceAnalysis]):
        """Validate configuration consistency across devices"""
        if len(results) < 2:
            return
        
        issues = []
        
        # Check if all devices have similar FlowSpec state
        analyses = list(results.values())
        hostnames = list(results.keys())
        
        # Check BGP rule count variance
        bgp_counts = [a.bgp_total for a in analyses]
        if max(bgp_counts) > 0 and min(bgp_counts) == 0:
            devices_with_rules = [h for h, a in results.items() if a.bgp_total > 0]
            devices_without = [h for h, a in results.items() if a.bgp_total == 0]
            issues.append(f"BGP rule mismatch: {devices_with_rules} have rules, {devices_without} have none")
        
        # Check interface FlowSpec enabled
        for hostname, analysis in results.items():
            for check in analysis.checks:
                if 'Interface' in check.component and 'flowspec' in check.check_name.lower():
                    if check.status == CheckStatus.WARN:
                        issues.append(f"{hostname}: No interfaces with FlowSpec enabled")
        
        if RICH_AVAILABLE and issues:
            console.print(Panel(
                "\n".join([f"[yellow]⚠[/yellow] {issue}" for issue in issues]),
                title="[bold yellow]Cross-Device Validation[/bold yellow]",
                border_style="yellow"
            ))
    
    # =========================================================================
    # CONFIGURATION GENERATOR (NEW)
    # =========================================================================
    
    def generate_flowspec_config(self):
        """Interactive configuration generator for missing FlowSpec components"""
        if RICH_AVAILABLE:
            console.print("\n[bold cyan]FlowSpec Configuration Generator[/bold cyan]")
            console.print("[dim]Generate DNOS configuration for FlowSpec components[/dim]\n")
            
            menu = """
  [1] BGP FlowSpec Address-Families (IPv4 + IPv6)
  [2] VRF FlowSpec Configuration
  [3] Interface FlowSpec Enablement
  [4] Local Policy (Match-Class + Policy + Apply)
  [5] Complete FlowSpec Setup (All of the above)
  [B] Back
"""
            console.print(Panel(menu, title="Generate Config", border_style="blue"))
            choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "5", "b", "B"], default="5")
        else:
            print("\nConfig Generator:")
            print("  [1] BGP FlowSpec AF")
            print("  [2] VRF FlowSpec")
            print("  [3] Interface FlowSpec")
            print("  [4] Local Policy")
            print("  [5] Complete Setup")
            print("  [B] Back")
            choice = input("Select [5]: ").strip() or "5"
        
        choice = choice.lower()
        
        if choice == 'b':
            return
        
        # Gather parameters
        if RICH_AVAILABLE:
            asn = Prompt.ask("BGP AS Number", default="65001")
            neighbor_ip = Prompt.ask("BGP Neighbor IP (RR or PE)", default="10.0.0.1")
        else:
            asn = input("BGP AS Number [65001]: ").strip() or "65001"
            neighbor_ip = input("BGP Neighbor IP [10.0.0.1]: ").strip() or "10.0.0.1"
        
        configs = []
        
        if choice in ['1', '5']:
            configs.append(self._gen_bgp_flowspec_config(asn, neighbor_ip))
        
        if choice in ['2', '5']:
            if RICH_AVAILABLE:
                vrf_name = Prompt.ask("VRF Name", default="CUSTOMER-A")
                rd = Prompt.ask("Route Distinguisher", default=f"{asn}:100")
                rt = Prompt.ask("Route Target", default=f"{asn}:100")
            else:
                vrf_name = input("VRF Name [CUSTOMER-A]: ").strip() or "CUSTOMER-A"
                rd = input(f"RD [{asn}:100]: ").strip() or f"{asn}:100"
                rt = input(f"RT [{asn}:100]: ").strip() or f"{asn}:100"
            configs.append(self._gen_vrf_flowspec_config(vrf_name, asn, rd, rt))
        
        if choice in ['3', '5']:
            if RICH_AVAILABLE:
                interfaces = Prompt.ask("Interface names (comma-separated)", default="ge400-0/0/0,ge400-0/0/1")
            else:
                interfaces = input("Interfaces [ge400-0/0/0,ge400-0/0/1]: ").strip() or "ge400-0/0/0,ge400-0/0/1"
            configs.append(self._gen_interface_flowspec_config(interfaces))
        
        if choice in ['4', '5']:
            if RICH_AVAILABLE:
                policy_name = Prompt.ask("Policy name", default="DROP-DDOS")
                mc_name = Prompt.ask("Match-class name", default="BLOCK-UDP53")
                dest_prefix = Prompt.ask("Destination prefix", default="10.0.0.0/8")
                protocol = Prompt.ask("Protocol (tcp=6, udp=17, icmp=1)", default="17")
                dest_port = Prompt.ask("Destination port", default="53")
            else:
                policy_name = input("Policy name [DROP-DDOS]: ").strip() or "DROP-DDOS"
                mc_name = input("Match-class [BLOCK-UDP53]: ").strip() or "BLOCK-UDP53"
                dest_prefix = input("Dest prefix [10.0.0.0/8]: ").strip() or "10.0.0.0/8"
                protocol = input("Protocol [17]: ").strip() or "17"
                dest_port = input("Dest port [53]: ").strip() or "53"
            configs.append(self._gen_local_policy_config(policy_name, mc_name, dest_prefix, protocol, dest_port))
        
        # Display generated config
        full_config = "\n!\n".join(configs)
        
        if RICH_AVAILABLE:
            console.print(Panel(
                f"[green]{full_config}[/green]",
                title="[bold]Generated DNOS Configuration[/bold]",
                border_style="green"
            ))
            
            # Offer to save
            if Confirm.ask("Save to file?", default=False):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = WIZARD_DIR / f"flowspec_config_{timestamp}.txt"
                with open(filepath, 'w') as f:
                    f.write(full_config)
                console.print(f"[green]✓[/green] Saved to: {filepath}")
        else:
            print("\n=== Generated Configuration ===")
            print(full_config)
    
    def _gen_bgp_flowspec_config(self, asn: str, neighbor_ip: str) -> str:
        """Generate BGP FlowSpec address-family configuration"""
        return f"""! ==========================================
! BGP FlowSpec Address-Families (SAFI 133 + 134)
! ==========================================
protocols
  bgp {asn}
    !
    ! SAFI 133: FlowSpec (default VRF only)
    address-family ipv4-flowspec
    !
    address-family ipv6-flowspec
    !
    ! SAFI 134: FlowSpec-VPN (VRF contexts)
    address-family ipv4-flowspec-vpn
    !
    address-family ipv6-flowspec-vpn
    !
    neighbor {neighbor_ip}
      !
      address-family ipv4-flowspec
        admin-state enabled
        send-community extended
      !
      address-family ipv6-flowspec
        admin-state enabled
        send-community extended
      !
      address-family ipv4-flowspec-vpn
        admin-state enabled
        send-community extended
      !
      address-family ipv6-flowspec-vpn
        admin-state enabled
        send-community extended
      !
    !
  !
!"""
    
    def _gen_vrf_flowspec_config(self, vrf_name: str, asn: str, rd: str, rt: str) -> str:
        """Generate VRF FlowSpec configuration"""
        return f"""! ==========================================
! VRF FlowSpec Configuration
! ==========================================
network-services
  vrf
    instance {vrf_name}
      protocols
        bgp {asn}
          route-distinguisher {rd}
          !
          address-family ipv4-flowspec
            export-vpn route-target {rt}
            import-vpn route-target {rt}
          !
          address-family ipv6-flowspec
            export-vpn route-target {rt}
            import-vpn route-target {rt}
          !
        !
      !
    !
  !
!"""
    
    def _gen_interface_flowspec_config(self, interfaces: str) -> str:
        """Generate interface FlowSpec enablement configuration"""
        iface_list = [i.strip() for i in interfaces.split(',')]
        config_lines = ["! ==========================================",
                        "! Interface FlowSpec Enablement",
                        "! ==========================================",
                        "interfaces"]
        
        for iface in iface_list:
            config_lines.extend([
                f"  {iface}",
                "    flowspec enabled",
                "  !"
            ])
        
        config_lines.append("!")
        return "\n".join(config_lines)
    
    def _gen_local_policy_config(self, policy_name: str, mc_name: str, 
                                  dest_prefix: str, protocol: str, dest_port: str) -> str:
        """Generate FlowSpec local policy configuration"""
        return f"""! ==========================================
! FlowSpec Local Policy Configuration
! ==========================================
! Step 1: Define match-class (routing-policy)
routing-policy
  flowspec-local-policies
    ipv4
      match-class {mc_name}
        dest-ip {dest_prefix}
        protocol eq {protocol}
        dest-port eq {dest_port}
      !
      policy {policy_name}
        match-class {mc_name}
          action-type rate-limit max-rate 0
        !
      !
    !
  !
!
! Step 2: Apply policy (forwarding-options)
forwarding-options
  flowspec-local
    ipv4
      apply-policy-to-flowspec {policy_name}
    !
  !
!"""
    
    def run_dependency_check(self):
        """Run dependency check on current device"""
        if not self.selected_device:
            if RICH_AVAILABLE:
                console.print("[yellow]No device selected.[/yellow]")
            return
        
        if RICH_AVAILABLE:
            console.print(f"\n[bold cyan]Dependency Check: {self.selected_device.get('hostname')}[/bold cyan]")
            console.print("[dim]Checking for missing or incomplete FlowSpec configuration...[/dim]\n")
        else:
            print(f"\nDependency Check: {self.selected_device.get('hostname')}")
        
        conn = self.connect_to_device(self.selected_device)
        
        # Create a temporary analysis object for dependency check
        analysis = DeviceAnalysis(
            hostname=self.selected_device.get("hostname", "unknown"),
            ip=self.selected_device.get("ip", ""),
            timestamp=datetime.now().isoformat()
        )
        
        if RICH_AVAILABLE:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                task = progress.add_task("Checking dependencies...", total=None)
                issues = self.check_dependencies(conn, analysis)
                progress.update(task, description="Complete!")
        else:
            print("Checking dependencies...")
            issues = self.check_dependencies(conn, analysis)
        
        # Store issues in current analysis if available
        if self.current_analysis:
            self.current_analysis.dependency_issues = issues
        
        # Show report
        self.show_dependency_report(issues)
    
    # =========================================================================
    # MAIN WIZARD LOOP
    # =========================================================================
    
    def show_test_plan_categories(self) -> Optional[str]:
        """Show test plan category menu - dynamically fetched from Jira"""
        try:
            import sys
            from pathlib import Path
            if str(Path(__file__).parent) not in sys.path:
                sys.path.insert(0, str(Path(__file__).parent))
            
            from test_verifier.test_plan_parser import get_all_test_categories_from_jira
            
            # Fetch categories from Jira (via cache)
            categories = get_all_test_categories_from_jira()
            
            if not categories:
                if RICH_AVAILABLE:
                    console.print("[yellow]No test categories found. Categories should be fetched via MCP first.[/yellow]")
                else:
                    print("No test categories found.")
                return None
            
            if RICH_AVAILABLE:
                table = Table(title="Test Plan Categories (from Jira)", box=box.ROUNDED)
                table.add_column("#", style="cyan", width=4)
                table.add_column("Category", style="green")
                table.add_column("Key", style="yellow")
                
                for i, cat in enumerate(categories, 1):
                    summary = cat.get("summary", "Unknown")
                    key = cat.get("key", "N/A")
                    table.add_row(str(i), summary, key)
                
                console.print(table)
                console.print("\n  [B] ← Back to main menu")
                
                valid_choices = [str(i) for i in range(1, len(categories) + 1)] + ["b", "B"]
                choice = Prompt.ask("Select category", choices=valid_choices, default="1")
            else:
                print("\nTest Plan Categories (from Jira):")
                for i, cat in enumerate(categories, 1):
                    summary = cat.get("summary", "Unknown")
                    key = cat.get("key", "N/A")
                    print(f"  [{i}] {summary} ({key})")
                print("  [B] Back")
                choice = input("\nSelect category [1]: ").strip() or "1"
            
            if choice.lower() == 'b':
                return None
            
            # Return category key, not number
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(categories):
                    return categories[idx].get("key")
            except ValueError:
                pass
            
            return None
            
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]Error loading categories: {e}[/red]")
            else:
                print(f"Error loading categories: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def show_category_tests(self, category_key: str) -> List[str]:
        """
        Show tests for a category and get selection
        
        Args:
            category_key: Test category issue key (e.g., "SW-231823")
        
        Returns:
            List of selected test issue keys or test IDs
        """
        try:
            import sys
            from pathlib import Path
            if str(Path(__file__).parent) not in sys.path:
                sys.path.insert(0, str(Path(__file__).parent))
            
            from test_verifier.test_plan_parser import (
                get_category_tests_from_jira,
                get_tests_for_category_issue,
                parse_jira_issue
            )
            
            # Get child test issues for this category
            test_issues = get_category_tests_from_jira(category_key)
            
            if not test_issues:
                if RICH_AVAILABLE:
                    console.print(f"[yellow]No tests found for category {category_key}[/yellow]")
                else:
                    print(f"No tests found for category {category_key}")
                return []
            
            # Show test issues
            if RICH_AVAILABLE:
                table = Table(title=f"Testing Tasks (Category: {category_key})", box=box.ROUNDED)
                table.add_column("#", style="cyan", width=4)
                table.add_column("Test Issue", style="green")
                table.add_column("Summary", style="white")
                
                for i, test_issue in enumerate(test_issues, 1):
                    key = test_issue.get("key", "N/A")
                    summary = test_issue.get("summary", "Unknown")
                    table.add_row(str(i), key, summary)
                
                console.print(table)
                console.print("\n  [ALL] Run all tests in category")
                console.print("  [B] Back to categories")
                
                valid_choices = [str(i) for i in range(1, len(test_issues) + 1)] + ["all", "ALL", "b", "B"]
                selection = Prompt.ask("\nSelect test(s)", default="ALL")
            else:
                print(f"\nTesting Tasks (Category: {category_key}):")
                for i, test_issue in enumerate(test_issues, 1):
                    key = test_issue.get("key", "N/A")
                    summary = test_issue.get("summary", "Unknown")
                    print(f"  [{i}] {key}: {summary}")
                print("  [ALL] Run all tests")
                print("  [B] Back")
                selection = input("\nSelect test(s) [ALL]: ").strip() or "ALL"
            
            if selection.upper() == "ALL":
                # Return all test issue keys - will parse test cases from each
                return [test_issue.get("key") for test_issue in test_issues if test_issue.get("key")]
            elif selection.upper() == "B":
                return []
            else:
                # Parse selection - can be numbers (indices) or test issue keys
                selected = []
                for item in selection.split(","):
                    item = item.strip()
                    try:
                        idx = int(item) - 1
                        if 0 <= idx < len(test_issues):
                            selected.append(test_issues[idx].get("key"))
                    except ValueError:
                        # Assume it's a test issue key
                        if item in [t.get("key") for t in test_issues]:
                            selected.append(item)
                return selected
                
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]Error loading tests: {e}[/red]")
            else:
                print(f"Error loading tests: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def show_basic_functionality_tests(self) -> List[str]:
        """Show Basic Functionality test cases - now uses dynamic category"""
        # Use generic category method for SW-231823
        return self.show_category_tests("SW-231823")
    
    def _wrap_text(self, text: str, max_width: int) -> str:
        """Wrap text at word boundaries to fit within max_width"""
        if len(text) <= max_width:
            return text
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if len(test_line) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return "\n".join(lines)
    
    def _display_prerequisite_results(self, prereq_results: Dict[str, Any]):
        """Display prerequisite check results in a formatted table"""
        if not prereq_results:
            if RICH_AVAILABLE:
                console.print("[yellow]No prerequisite results to display[/yellow]")
            return
        
        if RICH_AVAILABLE:
            from rich.table import Table as RichTable
            from rich import box
            
            # Summary table - wider and more readable
            summary_table = RichTable(
                title="Prerequisite Check Summary",
                box=box.ROUNDED,
                expand=True,
                show_header=True,
                header_style="bold cyan"
            )
            summary_table.add_column("Device", style="cyan", width=12, no_wrap=True)
            summary_table.add_column("Total", style="white", justify="center", width=8)
            summary_table.add_column("Passed", style="green", justify="center", width=10)
            summary_table.add_column("Failed", style="red", justify="center", width=10)
            summary_table.add_column("Warnings", style="yellow", justify="center", width=12)
            summary_table.add_column("Status", style="bold", justify="center", width=8)
            
            for device, device_prereqs in prereq_results.items():
                summary = device_prereqs.get_summary()
                status_icon = "✓" if summary["all_passed"] else "✗"
                status_color = "green" if summary["all_passed"] else "red"
                
                summary_table.add_row(
                    device,
                    str(summary["total"]),
                    f"[green]{summary['passed']}[/green]",
                    f"[red]{summary['failed']}[/red]",
                    f"[yellow]{summary['warnings']}[/yellow]",
                    f"[{status_color}]{status_icon}[/{status_color}]"
                )
            
            console.print(summary_table)
            
            # Detailed failures table
            failed_checks = []
            warning_checks = []
            for device, device_prereqs in prereq_results.items():
                for check in device_prereqs.checks:
                    if check.status.value == "fail":
                        failed_checks.append((device, check))
                    elif check.status.value == "warning":
                        warning_checks.append((device, check))
            
            # Show warnings first (less critical) - simplified format
            if warning_checks:
                console.print("\n[yellow]⚠ Warnings:[/yellow]")
                
                # Group by device
                by_device = {}
                for device, check in warning_checks:
                    if device not in by_device:
                        by_device[device] = []
                    by_device[device].append(check)
                
                # Show warnings grouped by device
                for device, checks in by_device.items():
                    console.print(f"\n[bold cyan]{device}:[/bold cyan]")
                    for check in checks:
                        prereq_display = check.prerequisite
                        if len(prereq_display) > 60:
                            prereq_display = prereq_display[:57] + "..."
                        
                        message_display = check.message
                        if len(message_display) > 70:
                            message_display = self._wrap_text(message_display, 70)
                        
                        console.print(f"  [yellow]⚠[/yellow] [white]{prereq_display}[/white]")
                        console.print(f"      [dim]{message_display}[/dim]")
            
            if failed_checks:
                console.print("\n[bold red]Failed Prerequisites:[/bold red]")
                
                # Group by device for better readability
                by_device = {}
                for device, check in failed_checks:
                    if device not in by_device:
                        by_device[device] = []
                    by_device[device].append(check)
                
                # Show failures grouped by device
                for device, checks in by_device.items():
                    console.print(f"\n[bold cyan]{device}:[/bold cyan]")
                    for check in checks:
                        # Show prerequisite on one line (truncate if too long)
                        prereq_display = check.prerequisite
                        if len(prereq_display) > 60:
                            prereq_display = prereq_display[:57] + "..."
                        
                        # Show message (can wrap)
                        message_display = check.message
                        if len(message_display) > 70:
                            # Wrap at word boundaries
                            message_display = self._wrap_text(message_display, 70)
                        
                        console.print(f"  [red]✗[/red] [white]{prereq_display}[/white]")
                        console.print(f"      [dim]{message_display}[/dim]")
        else:
            print("\nPrerequisite Check Summary:")
            for device, device_prereqs in prereq_results.items():
                summary = device_prereqs.get_summary()
                status = "✓ PASS" if summary["all_passed"] else "✗ FAIL"
                print(f"\n  {device}: {status}")
                print(f"    Total: {summary['total']}, Passed: {summary['passed']}, Failed: {summary['failed']}, Warnings: {summary['warnings']}")
                
                # Show failures
                for check in device_prereqs.checks:
                    if check.status.value == "fail":
                        print(f"    ✗ {check.prerequisite}: {check.message}")
    
    def run_test_plan_tests(self):
        """Execute selected test cases using test_verifier"""
        try:
            # Import test verifier components
            import sys
            from pathlib import Path
            # Add test_verifier to path
            test_verifier_path = Path(__file__).parent / "test_verifier"
            if str(test_verifier_path) not in sys.path:
                sys.path.insert(0, str(Path(__file__).parent))
            
            from test_verifier.device_manager import DeviceManager
            from test_verifier.test_runner import TestRunner
            from test_verifier.report_generator import ReportGenerator
            from test_verifier.test_plan_parser import get_test_by_id
            
            if RICH_AVAILABLE:
                console.print(Panel.fit(
                    "[bold cyan]Test Plan Verification[/bold cyan]",
                    border_style="cyan"
                ))
            
            # Show category menu (returns category key)
            category_key = self.show_test_plan_categories()
            
            if not category_key:
                return
            
            # Get test selection (returns test issue keys)
            test_issue_keys = self.show_category_tests(category_key)
            
            if not test_issue_keys:
                return
            
            # Initialize test runner
            device_manager = DeviceManager()
            device_manager.load_devices()
            
            # Get test cases from test issues
            # Each test issue key (e.g., SW-234158) may contain multiple test cases (HF-01, HF-02, etc.)
            from test_verifier.test_plan_parser import parse_jira_issue, get_tests_for_category_issue
            
            test_cases = []
            for test_issue_key in test_issue_keys:
                # Parse test cases from this test issue
                issue_test_cases = parse_jira_issue(test_issue_key)
                if issue_test_cases:
                    test_cases.extend(issue_test_cases)
                else:
                    # If no test cases parsed, try markdown fallback
                    # For now, log warning
                    logger.warning(f"No test cases parsed from {test_issue_key}, may need markdown fallback")
            
            if not test_cases:
                if RICH_AVAILABLE:
                    console.print("[red]No test cases to run[/red]")
                else:
                    print("No test cases to run")
                return
            
            # Multi-device prerequisite checking (DUT devices only, no Spirent)
            if RICH_AVAILABLE:
                console.print("\n[bold cyan]Checking Prerequisites on DUT Devices...[/bold cyan]")
            
            from test_verifier.prerequisite_checker import PrerequisiteChecker
            
            # Get all available devices (will be filtered to network devices only)
            all_devices = list(device_manager.devices.keys())
            if not all_devices:
                all_devices = device_manager.load_devices()
                all_devices = [d.get("hostname", "unknown") for d in all_devices]
            
            # Check prerequisites (PrerequisiteChecker will filter out Spirent devices and prerequisites)
            prereq_checker = PrerequisiteChecker(device_manager)
            prereq_results = prereq_checker.check_prerequisites(test_cases, all_devices)
            
            # Display prerequisite results
            self._display_prerequisite_results(prereq_results)
            
            # Get gaps summary
            gaps = prereq_checker.get_gaps_summary(prereq_results)
            
            # Ask user if they want to continue with gaps
            if gaps["devices_with_gaps"] > 0:
                try:
                    if RICH_AVAILABLE:
                        continue_anyway = Confirm.ask(
                            f"\n[yellow]⚠ Found {gaps['devices_with_gaps']} device(s) with prerequisite gaps. Continue anyway?[/yellow]",
                            default=False
                        )
                    else:
                        response = input(f"\n⚠ Found {gaps['devices_with_gaps']} device(s) with gaps. Continue? [y/N]: ").strip().lower()
                        continue_anyway = response == 'y'
                    
                    if not continue_anyway:
                        if RICH_AVAILABLE:
                            console.print("[yellow]Test execution cancelled.[/yellow]")
                        return
                except KeyboardInterrupt:
                    # User cancelled with Ctrl+C
                    if RICH_AVAILABLE:
                        try:
                            console.print("\n[yellow]Cancelled.[/yellow]")
                        except:
                            print("\nCancelled.")
                    return
            
            # Use selected device from wizard (or all devices if multi-device mode)
            device_hostname = self.selected_device.get("hostname", "DUT") if self.selected_device else "DUT"
            
            test_runner = TestRunner(device_manager, continue_on_failure=True)
            report_generator = ReportGenerator()
            
            # Run tests
            if RICH_AVAILABLE:
                with Progress() as progress:
                    task = progress.add_task(f"[cyan]Running {len(test_cases)} test(s)...", total=len(test_cases))
                    test_run = test_runner.run_tests(test_cases, device_hostname)
                    progress.update(task, completed=len(test_cases))
            else:
                print(f"\nRunning {len(test_cases)} test(s)...")
                test_run = test_runner.run_tests(test_cases, device_hostname)
            
            # Generate reports
            reports = report_generator.generate_all_reports(test_run)
            
            # Show summary
            summary = test_run.get_summary()
            if RICH_AVAILABLE:
                console.print("\n[bold green]Test Run Complete![/bold green]")
                summary_table = Table(title="Summary", box=box.ROUNDED)
                summary_table.add_column("Metric", style="cyan")
                summary_table.add_column("Value", style="magenta")
                summary_table.add_row("Total", str(summary["total"]))
                summary_table.add_row("Passed", f"[green]{summary['passed']}[/green]")
                summary_table.add_row("Failed", f"[red]{summary['failed']}[/red]")
                summary_table.add_row("Skipped", f"[yellow]{summary['skipped']}[/yellow]")
                summary_table.add_row("Duration", f"{summary['duration']:.2f}s")
                summary_table.add_row("Pass Rate", f"{summary['pass_rate']:.1f}%")
                console.print(summary_table)
                
                console.print("\n[bold]Reports:[/bold]")
                for fmt, path in reports.items():
                    console.print(f"  {fmt.upper()}: {path}")
            else:
                print("\nTest Run Summary:")
                print(f"  Total: {summary['total']}")
                print(f"  Passed: {summary['passed']}")
                print(f"  Failed: {summary['failed']}")
                print(f"  Duration: {summary['duration']:.2f}s")
                print("\nReports:")
                for fmt, path in reports.items():
                    print(f"  {fmt.upper()}: {path}")
        
        except ImportError as e:
            if RICH_AVAILABLE:
                console.print(f"[red]Error importing test verifier: {e}[/red]")
                console.print("[yellow]Make sure test_verifier module is available[/yellow]")
            else:
                print(f"Error importing test verifier: {e}")
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]Error running tests: {e}[/red]")
            else:
                print(f"Error running tests: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """Main wizard entry point"""
        
        # Outer loop for device selection (avoids recursion)
        while True:
            self.clear_screen()
            self.print_banner()
            
            # Device selection
            device = self.show_device_selection()
            if not device:
                if RICH_AVAILABLE:
                    console.print("[yellow]Exiting wizard.[/yellow]")
                else:
                    print("Exiting wizard.")
                return
            
            # Handle special selection modes
            if device.get("_all_devices") or device.get("_multi_devices"):
                devices_list = device.get("devices", [])
                self._run_multi_device_summary(devices_list)
                # Loop back to device selection
                continue
            
            # Handle path tracing mode
            if device.get("_path_trace"):
                self.trace_flowspec_path(
                    source=device["source"],
                    destination=device["destination"],
                    all_devices=device["all_devices"]
                )
                if RICH_AVAILABLE:
                    Prompt.ask("\nPress Enter to continue")
                # Loop back to device selection
                continue
            
            # Handle multi-path tracing mode
            if device.get("_path_trace_multi"):
                self.trace_flowspec_path_multi(
                    sources=device["sources"],
                    destinations=device["destinations"],
                    all_devices=device["all_devices"]
                )
                if RICH_AVAILABLE:
                    Prompt.ask("\nPress Enter to continue")
                # Loop back to device selection
                continue
            
            self.selected_device = device
            
            # Inner loop for main menu
            menu_active = True
            while menu_active:
                choice = self.show_main_menu()
                
                if choice == '1':
                    self.analyze_device(self.selected_device)
                elif choice == '2':
                    self.quick_check(self.selected_device)
                elif choice == '3':
                    self.show_rule_details()
                elif choice == '4':
                    self.extract_and_show_traces()
                elif choice == '5':
                    self.deep_dive_analysis()
                elif choice == '6':
                    new_device = self.show_device_selection()
                    if new_device and not new_device.get("_all_devices") and not new_device.get("_multi_devices"):
                        self.selected_device = new_device
                elif choice == '7':
                    if self.current_analysis:
                        filepath = self.save_report(self.current_analysis)
                        if RICH_AVAILABLE:
                            console.print(f"[green]✓[/green] Report saved to: {filepath}")
                        else:
                            print(f"Report saved to: {filepath}")
                    else:
                        if RICH_AVAILABLE:
                            console.print("[yellow]No analysis to save. Run Full Analysis first.[/yellow]")
                        else:
                            print("No analysis to save.")
                elif choice == '8':
                    self.show_safi_guide()
                elif choice == '9':
                    # Dependency Check
                    self.run_dependency_check()
                elif choice == 'a':
                    # Multi-Device Analysis
                    self.run_multi_device_analysis()
                elif choice == 'p':
                    # Path Trace - trace routes through RR→PE
                    self._run_path_trace_from_menu()
                elif choice == 't':
                    # TP RUN - Test Plan verification
                    self.run_test_plan_tests()
                elif choice == 'v':
                    # Verbose View - show full detailed flow diagram and table
                    if self.current_analysis:
                        if RICH_AVAILABLE:
                            console.print("\n[bold cyan]Verbose View - Full Details[/bold cyan]\n")
                        self.print_flow_diagram(self.current_analysis)
                        self.print_summary_table(self.current_analysis)
                    else:
                        if RICH_AVAILABLE:
                            console.print("[yellow]No analysis available. Run Full Analysis [1] first.[/yellow]")
                        else:
                            print("No analysis available. Run Full Analysis first.")
                elif choice == 'b':
                    # Go back to device selection
                    menu_active = False
                elif choice == 'q':
                    # Exit wizard completely
                    if RICH_AVAILABLE:
                        console.print("[yellow]Exiting wizard.[/yellow]")
                    return
                
                if menu_active and RICH_AVAILABLE:
                    Prompt.ask("\nPress Enter to continue")
            
            # menu_active is False - loop continues to device selection
    
    def analyze_device(self, device: Dict, use_cache: bool = True):
        """
        Run and display full analysis
        
        Args:
            device: Device dictionary
            use_cache: If True, try to load from cache first (default: True)
        """
        hostname = device.get('hostname', 'unknown')
        
        # Try cache first
        if use_cache:
            cached = self.load_cached_analysis(device)
            if cached:
                if RICH_AVAILABLE:
                    age_seconds = (datetime.now() - datetime.fromisoformat(cached.timestamp)).total_seconds()
                    console.print(f"[dim]Using cached analysis for {hostname} (age: {age_seconds:.0f}s)[/dim]")
                self.current_analysis = cached
                # Use CLEAN summary (not verbose flow diagram)
                self.print_quick_summary(cached)
                if cached.bgp_total > 0 or cached.lp_total > 0 or len(cached.problems) > 0:
                    self.print_rules_table(cached)
                return
        
        # No cache - run fresh analysis
        if RICH_AVAILABLE:
            console.print(f"\n[bold cyan]Analyzing {hostname}...[/bold cyan]")
            console.print("[dim]Running checks (this may take 30-60s)...[/dim]")
            # Don't use spinner - let run_full_analysis print progress directly
            analysis = self.run_full_analysis(device, use_cache=False)
            console.print(f"[green]✓ Analysis complete[/green]\n")
        else:
            print(f"\nAnalyzing {hostname}...")
            analysis = self.run_full_analysis(device, use_cache=False)
            print("✓ Analysis complete\n")
        
        self.current_analysis = analysis
        
        # Use CLEAN quick summary instead of verbose flow diagram
        self.print_quick_summary(analysis)
        
        # Only show detailed table if there are rules or significant issues
        if analysis.bgp_total > 0 or analysis.lp_total > 0 or len(analysis.problems) > 0:
            self.print_rules_table(analysis)
        
        # Auto-save to cache
        try:
            self.save_report(analysis)
        except Exception as e:
            logger.warning(f"Failed to auto-save analysis: {e}")
    
    def quick_check(self, device: Dict):
        """Quick status check.
        
        For SA devices: Always uses NCP 0 (no detection needed).
        For Cluster devices: Detects the correct NCP from FlowSpec-enabled interfaces.
        """
        conn = self.connect_to_device(device)
        
        if RICH_AVAILABLE:
            console.print(f"\n[bold cyan]Quick Check: {device.get('hostname')}[/bold cyan]\n")
        else:
            print(f"\nQuick Check: {device.get('hostname')}\n")
        
        # First, detect if SA or Cluster
        is_standalone = self.detect_device_type(conn)
        
        if is_standalone:
            # SA device: Always NCP 0, no interface parsing needed
            ncp_num = 0
            ncp_info = ""
        else:
            # Cluster device: Detect NCP from FlowSpec-enabled interfaces
            iface_cmd = "show running-config interfaces | include 'interface\\|flowspec enabled'"
            success, iface_output = conn.run_cli_command(iface_cmd)
            
            detected_ncps = [0]
            if success:
                lines = iface_output.split('\n')
                current_iface = None
                flowspec_interfaces = []
                
                for line in lines:
                    line = line.strip()
                    iface_match = re.match(r'(?:interface\s+)?(\S+)\s*$', line)
                    if iface_match and 'flowspec' not in line.lower():
                        potential_iface = iface_match.group(1)
                        if re.match(r'(ge|xe|ce|et|bundle|irb|lo)\d*', potential_iface):
                            current_iface = potential_iface
                    elif 'flowspec enabled' in line.lower() and current_iface:
                        flowspec_interfaces.append(current_iface)
                        current_iface = None
                
                if flowspec_interfaces:
                    detected_ncps = extract_ncps_from_interfaces(flowspec_interfaces) or [0]
            
            ncp_num = detected_ncps[0]
            ncp_info = f" (NCP {ncp_num})"
        
        checks = [
            ("BGP Sessions", "show bgp ipv4 flowspec-vpn summary", "Established"),
            ("FlowSpec Routes", "show bgp ipv4 flowspec-vpn routes", "DstPrefix"),
            (f"NCP Status{ncp_info}", f"show flowspec ncp {ncp_num}", "Installed"),
            ("Counters", "show flowspec", "Match packet"),
        ]
        
        for name, cmd, look_for in checks:
            success, output = conn.run_cli_command(cmd)
            found = look_for in output if success else False
            status = "✓" if found else "✗"
            
            if RICH_AVAILABLE:
                color = "green" if found else "red"
                console.print(f"  [{color}]{status}[/{color}] {name}")
            else:
                print(f"  {status} {name}")
    
    def show_rule_details(self):
        """Show detailed rule information"""
        if not self.current_analysis:
            if RICH_AVAILABLE:
                console.print("[yellow]Run Full Analysis first.[/yellow]")
            else:
                print("Run Full Analysis first.")
            return
        
        conn = self.connect_to_device(self.selected_device)
        cmd = "show flowspec"
        success, output = conn.run_cli_command(cmd)
        
        if success and RICH_AVAILABLE:
            console.print(Panel(output[:3000], title="FlowSpec Rules", border_style="green"))
        elif success:
            print(output[:3000])
    
    def extract_and_show_traces(self):
        """Extract and display traces"""
        if not self.selected_device:
            return
        
        if RICH_AVAILABLE:
            console.print("[cyan]Extracting traces from containers...[/cyan]")
        else:
            print("Extracting traces...")
        
        conn = self.connect_to_device(self.selected_device)
        traces = self.extract_traces(conn, self.selected_device.get("hostname", "device"))
        
        if traces:
            for name, trace_data in traces.items():
                if RICH_AVAILABLE:
                    console.print(Panel(trace_data[:2000], title=f"[bold]{name}[/bold]", border_style="yellow"))
                else:
                    print(f"\n=== {name} ===")
                    print(trace_data[:2000])
        else:
            if RICH_AVAILABLE:
                console.print("[yellow]No FlowSpec traces found in container logs.[/yellow]")
            else:
                print("No traces found.")
    
    def deep_dive_analysis(self):
        """Deep dive on specific NLRI.
        
        For SA devices: Always uses NCP 0 (no detection needed).
        For Cluster devices: Detects the correct NCP from FlowSpec-enabled interfaces.
        """
        if RICH_AVAILABLE:
            nlri = Prompt.ask("Enter NLRI to analyze", default="DstPrefix:=10.10.10.1/32")
        else:
            nlri = input("Enter NLRI [DstPrefix:=10.10.10.1/32]: ") or "DstPrefix:=10.10.10.1/32"
        
        if not self.selected_device:
            return
        
        conn = self.connect_to_device(self.selected_device)
        
        if RICH_AVAILABLE:
            console.print(f"[cyan]Analyzing rule: {nlri}[/cyan]\n")
        else:
            print(f"Analyzing: {nlri}")
        
        # First, detect if SA or Cluster
        is_standalone = self.detect_device_type(conn)
        
        if is_standalone:
            # SA device: Always NCP 0, no interface parsing needed
            ncp_num = 0
        else:
            # Cluster device: Detect NCP from FlowSpec-enabled interfaces
            iface_cmd = "show running-config interfaces | include 'interface\\|flowspec enabled'"
            success, iface_output = conn.run_cli_command(iface_cmd)
            
            ncp_num = 0
            if success:
                lines = iface_output.split('\n')
                current_iface = None
                flowspec_interfaces = []
                
                for line in lines:
                    line = line.strip()
                    iface_match = re.match(r'(?:interface\s+)?(\S+)\s*$', line)
                    if iface_match and 'flowspec' not in line.lower():
                        potential_iface = iface_match.group(1)
                        if re.match(r'(ge|xe|ce|et|bundle|irb|lo)\d*', potential_iface):
                            current_iface = potential_iface
                    elif 'flowspec enabled' in line.lower() and current_iface:
                        flowspec_interfaces.append(current_iface)
                        current_iface = None
                
                if flowspec_interfaces:
                    detected_ncps = extract_ncps_from_interfaces(flowspec_interfaces)
                    if detected_ncps:
                        ncp_num = detected_ncps[0]
        
        # Check in various places
        commands = [
            (f'show bgp ipv4 flowspec-vpn nlri "{nlri}"', "BGP FlowSpec-VPN"),
            (f'show flowspec ncp {ncp_num} nlri "{nlri}"', f"NCP {ncp_num} Status"),
            ("show flowspec", "Counters"),
        ]
        
        for cmd, label in commands:
            success, output = conn.run_cli_command(cmd)
            if success and nlri in output:
                if RICH_AVAILABLE:
                    console.print(Panel(output[:1500], title=f"[bold]{label}[/bold]", border_style="blue"))
                else:
                    print(f"\n=== {label} ===")
                    print(output[:1500])
    
    def show_safi_guide(self):
        """Show educational guide about SAFI 133 vs 134 and GRT coexistence"""
        if RICH_AVAILABLE:
            guide = """
[bold cyan]╔═══════════════════════════════════════════════════════════════════════════════╗
║                    FlowSpec SAFI 133 vs 134 Guide                             ║
╚═══════════════════════════════════════════════════════════════════════════════╝[/bold cyan]

[bold yellow]Question: Can GRT have both SAFIs? Will they interfere?[/bold yellow]

[bold green]Answer: YES, they coexist! NO, they do NOT interfere![/bold green]

[bold cyan]┌───────────────────────────────────────────────────────────────────────────────┐
│ SAFI 133: flowspec (RFC 5575)                                                │
├───────────────────────────────────────────────────────────────────────────────┤[/bold cyan]
│ • Target:        Default VRF / GRT (Global Routing Table)                    │
│ • RD Required:   [red]❌ NO[/red]                                                        │
│ • RT Required:   [red]❌ NO[/red]                                                        │
│ • NLRI Format:   Raw FlowSpec NLRI (e.g., DstPrefix:=10.0.0.0/8)             │
│ • Affects:       Traffic in DEFAULT VRF only                                 │
│ • Use Case:      Global internet traffic filtering (DDoS, scrubbing)        │
[cyan]└───────────────────────────────────────────────────────────────────────────────┘[/cyan]

[bold magenta]┌───────────────────────────────────────────────────────────────────────────────┐
│ SAFI 134: flowspec-vpn (RFC 5575 + RFC 4364)                                 │
├───────────────────────────────────────────────────────────────────────────────┤[/bold magenta]
│ • Target:        VPN/VRF contexts (L3VPN customers)                          │
│ • RD Required:   [green]✅ YES[/green] (Route Distinguisher - prefixed to NLRI)              │
│ • RT Required:   [green]✅ YES[/green] (Route Target - extended community for VRF import)    │
│ • NLRI Format:   RD:FlowSpec NLRI (e.g., 65001:100:DstPrefix:=10.0.0.0/8)    │
│ • Affects:       ONLY VRFs that import the matching Route Target             │
│ • Use Case:      Per-customer/per-VRF traffic policies (L3VPN service)      │
[magenta]└───────────────────────────────────────────────────────────────────────────────┘[/magenta]

[bold yellow]Why SAFI 134 CANNOT Affect GRT/Default VRF:[/bold yellow]

  [red]1.[/red] GRT has no Route Distinguisher concept
  [red]2.[/red] GRT does not perform VPN RT (Route Target) import
  [red]3.[/red] SAFI 134 NLRI includes RD prefix that GRT cannot match
  [red]4.[/red] Different address family tables - completely isolated

[bold cyan]Example - How They Stay Separate:[/bold cyan]

  [dim]# SAFI 133 - Affects DEFAULT VRF[/dim]
  [green]BGP FlowSpec NLRI:[/green] DstPrefix:=10.0.0.0/8, Action:rate-limit 1000
  → Installs in [bold]GRT[/bold] (no RD, no RT needed)

  [dim]# SAFI 134 - Affects ONLY specific VRFs[/dim]
  [magenta]BGP FlowSpec-VPN NLRI:[/magenta] RD:65001:100 + DstPrefix:=10.0.0.0/8
  [magenta]RT Extended Community:[/magenta] 65001:100
  → Installs ONLY in VRFs that import RT 65001:100
  → [yellow]GRT ignores this completely![/yellow]

[bold green]★ KEY TAKEAWAYS:[/bold green]

  [green]✓[/green] A router CAN enable both SAFI 133 and 134 simultaneously
  [green]✓[/green] They operate on DIFFERENT address family tables
  [green]✓[/green] SAFI 134 rules are isolated by RD/RT - can NEVER "leak" to GRT
  [green]✓[/green] To filter traffic in GRT, you MUST use SAFI 133
  [green]✓[/green] To filter traffic in a specific VRF, use SAFI 134 with matching RT

[bold yellow]DNOS Commands to Verify:[/bold yellow]

  [dim]# Check SAFI 133 (default VRF)[/dim]
  show bgp ipv4 flowspec summary
  show bgp ipv4 flowspec routes

  [dim]# Check SAFI 134 (VPN/VRF)[/dim]
  show bgp ipv4 flowspec-vpn summary
  show bgp ipv4 flowspec-vpn routes
  show bgp instance vrf <VRF_NAME> ipv4 flowspec routes
"""
            console.print(Panel(guide, title="[bold]FlowSpec SAFI Education Guide[/bold]", border_style="cyan"))
        else:
            print("""
================================================================================
                    FlowSpec SAFI 133 vs 134 Guide
================================================================================

Question: Can GRT have both SAFIs? Will they interfere?
Answer: YES, they coexist! NO, they do NOT interfere!

SAFI 133: flowspec (RFC 5575)
────────────────────────────────────────────────────────────────────────────────
• Target:        Default VRF / GRT (Global Routing Table)
• RD Required:   NO
• RT Required:   NO
• NLRI Format:   Raw FlowSpec NLRI
• Affects:       Traffic in DEFAULT VRF only

SAFI 134: flowspec-vpn (RFC 5575 + RFC 4364)
────────────────────────────────────────────────────────────────────────────────
• Target:        VPN/VRF contexts (L3VPN customers)
• RD Required:   YES (Route Distinguisher)
• RT Required:   YES (Route Target for VRF import)
• NLRI Format:   RD:FlowSpec NLRI
• Affects:       ONLY VRFs that import the matching Route Target

Why SAFI 134 CANNOT Affect GRT:
────────────────────────────────────────────────────────────────────────────────
1. GRT has no Route Distinguisher concept
2. GRT does not perform VPN RT import
3. SAFI 134 NLRI includes RD prefix that GRT cannot match
4. Different address family tables - completely isolated

KEY TAKEAWAYS:
────────────────────────────────────────────────────────────────────────────────
✓ A router CAN enable both SAFI 133 and 134 simultaneously
✓ They operate on DIFFERENT address family tables
✓ SAFI 134 rules can NEVER "leak" to GRT
✓ To filter GRT traffic, you MUST use SAFI 133
✓ To filter VRF traffic, use SAFI 134 with matching RT
""")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point - always runs wizard"""
    wizard = FSVPNWizard()
    
    try:
        wizard.run()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully - use simple print to avoid nested exceptions
        try:
            if RICH_AVAILABLE:
                console.print("\n[yellow]Wizard interrupted.[/yellow]")
            else:
                print("\nWizard interrupted.")
        except (KeyboardInterrupt, Exception):
            # If even the error message fails, just exit silently
            print("\n", end="", flush=True)
            sys.exit(0)
    except Exception as e:
        try:
            if RICH_AVAILABLE:
                console.print(f"[red]Error: {e}[/red]")
            else:
                print(f"Error: {e}")
        except:
            print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
