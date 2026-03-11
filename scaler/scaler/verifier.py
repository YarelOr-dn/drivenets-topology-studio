"""Post-commit verification with operational show commands."""

import re
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class VerificationStatus(str, Enum):
    """Status of a verification check."""
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    PENDING = "pending"
    SKIPPED = "skipped"


@dataclass
class VerificationCheck:
    """Result of a single verification check."""
    name: str
    status: VerificationStatus
    expected: Any
    actual: Any
    message: str
    command: str


@dataclass
class VerificationResult:
    """Complete verification result."""
    overall_status: VerificationStatus
    checks: List[VerificationCheck]
    duration_seconds: float
    summary: str


class Verifier:
    """Run post-commit verification checks."""

    # Mapping of configuration type to verification commands
    VERIFICATION_COMMANDS = {
        'interfaces': [
            ('show interfaces | no-more', 'parse_interfaces_status'),
        ],
        'bgp': [
            ('show bgp summary | no-more', 'parse_bgp_status'),
        ],
        'fxc': [
            ('show evpn-vpws-fxc summary | no-more', 'parse_fxc_status'),
        ],
        'vrf': [
            ('show vrf | no-more', 'parse_vrf_status'),
        ],
        'evpn': [
            ('show evpn summary | no-more', 'parse_evpn_status'),
        ],
        'vpws': [
            ('show vpws summary | no-more', 'parse_vpws_status'),
        ],
        'isis': [
            ('show isis adjacency | no-more', 'parse_isis_status'),
        ],
        'ospf': [
            ('show ospf neighbor | no-more', 'parse_ospf_status'),
        ],
        'ldp': [
            ('show ldp neighbor | no-more', 'parse_ldp_status'),
        ],
    }

    def __init__(self):
        """Initialize the verifier."""
        self.results: List[VerificationCheck] = []

    def get_verification_commands(
        self,
        configured_types: List[str]
    ) -> List[Tuple[str, str]]:
        """
        Get the appropriate verification commands based on what was configured.
        
        Args:
            configured_types: List of config types (e.g., ['interfaces', 'fxc', 'bgp'])
        
        Returns:
            List of (command, parser_method) tuples
        """
        commands = []
        for config_type in configured_types:
            if config_type in self.VERIFICATION_COMMANDS:
                commands.extend(self.VERIFICATION_COMMANDS[config_type])
        return commands

    def parse_interfaces_status(
        self,
        output: str,
        expected_interfaces: Optional[List[str]] = None
    ) -> VerificationCheck:
        """
        Parse interface status from show interfaces output.
        
        Args:
            output: Command output
            expected_interfaces: Optional list of interfaces to verify
        
        Returns:
            VerificationCheck result
        """
        # Parse table format: | interface | admin | oper | ...
        up_count = 0
        down_count = 0
        total_count = 0
        
        lines = output.split('\n')
        for line in lines:
            if '|' in line and not line.startswith('+'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4:
                    iface = parts[1] if len(parts) > 1 else ''
                    oper_status = parts[3] if len(parts) > 3 else ''
                    
                    if iface and not iface.startswith('Interface'):
                        total_count += 1
                        if 'up' in oper_status.lower():
                            up_count += 1
                        else:
                            down_count += 1
        
        if total_count == 0:
            status = VerificationStatus.SKIPPED
            message = "No interfaces found in output"
        elif up_count == total_count:
            status = VerificationStatus.PASS
            message = f"All {up_count} interfaces are UP"
        elif up_count > 0:
            status = VerificationStatus.PARTIAL
            message = f"{up_count}/{total_count} interfaces UP ({down_count} DOWN)"
        else:
            status = VerificationStatus.FAIL
            message = f"All {total_count} interfaces are DOWN"
        
        return VerificationCheck(
            name="Interfaces",
            status=status,
            expected=total_count,
            actual=up_count,
            message=message,
            command="show interfaces"
        )

    def parse_bgp_status(
        self,
        output: str,
        expected_peers: Optional[int] = None
    ) -> VerificationCheck:
        """Parse BGP summary output."""
        established = 0
        total = 0
        
        # Look for lines with peer info (IP address at start)
        lines = output.split('\n')
        for line in lines:
            # Match lines starting with IP address
            if re.match(r'^\s*\d+\.\d+\.\d+\.\d+', line):
                total += 1
                if 'established' in line.lower():
                    established += 1
                # Also check for numeric state (established peers show prefix count)
                parts = line.split()
                if len(parts) >= 4:
                    # Last column is usually state/prefix count
                    last = parts[-1]
                    if last.isdigit():
                        established += 1
        
        if total == 0:
            status = VerificationStatus.SKIPPED
            message = "No BGP peers found"
        elif established == total:
            status = VerificationStatus.PASS
            message = f"All {established} BGP peers established"
        elif established > 0:
            status = VerificationStatus.PARTIAL
            message = f"{established}/{total} BGP peers established"
        else:
            status = VerificationStatus.FAIL
            message = f"No BGP peers established (0/{total})"
        
        return VerificationCheck(
            name="BGP Peers",
            status=status,
            expected=expected_peers or total,
            actual=established,
            message=message,
            command="show bgp summary"
        )

    def parse_fxc_status(
        self,
        output: str,
        expected_count: Optional[int] = None
    ) -> VerificationCheck:
        """Parse FXC service status."""
        up_count = 0
        total_count = 0
        
        lines = output.split('\n')
        for line in lines:
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    # Look for state column
                    for part in parts:
                        if part.lower() in ['up', 'down', 'admin-down']:
                            total_count += 1
                            if part.lower() == 'up':
                                up_count += 1
                            break
        
        if total_count == 0:
            status = VerificationStatus.SKIPPED
            message = "No FXC services found"
        elif up_count == total_count:
            status = VerificationStatus.PASS
            message = f"All {up_count} FXC services UP"
        elif up_count > 0:
            status = VerificationStatus.PARTIAL
            message = f"{up_count}/{total_count} FXC services UP"
        else:
            status = VerificationStatus.FAIL
            message = f"No FXC services UP (0/{total_count})"
        
        return VerificationCheck(
            name="FXC Services",
            status=status,
            expected=expected_count or total_count,
            actual=up_count,
            message=message,
            command="show evpn-vpws-fxc summary"
        )

    def parse_vrf_status(
        self,
        output: str,
        expected_count: Optional[int] = None
    ) -> VerificationCheck:
        """Parse VRF status."""
        vrf_count = 0
        
        lines = output.split('\n')
        for line in lines:
            # VRFs are typically listed as table rows
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2 and parts[1] and not parts[1].startswith('VRF'):
                    vrf_count += 1
        
        if vrf_count == 0:
            status = VerificationStatus.SKIPPED
            message = "No VRFs found"
        else:
            status = VerificationStatus.PASS
            message = f"{vrf_count} VRFs configured"
        
        return VerificationCheck(
            name="VRF Instances",
            status=status,
            expected=expected_count or vrf_count,
            actual=vrf_count,
            message=message,
            command="show vrf"
        )

    def parse_evpn_status(
        self,
        output: str,
        expected_count: Optional[int] = None
    ) -> VerificationCheck:
        """Parse EVPN status."""
        up_count = 0
        total_count = 0
        
        lines = output.split('\n')
        for line in lines:
            if '|' in line:
                line_lower = line.lower()
                if 'up' in line_lower or 'down' in line_lower:
                    total_count += 1
                    if 'up' in line_lower and 'down' not in line_lower:
                        up_count += 1
        
        if total_count == 0:
            status = VerificationStatus.SKIPPED
            message = "No EVPN instances found"
        elif up_count == total_count:
            status = VerificationStatus.PASS
            message = f"All {up_count} EVPN instances UP"
        else:
            status = VerificationStatus.PARTIAL
            message = f"{up_count}/{total_count} EVPN instances UP"
        
        return VerificationCheck(
            name="EVPN Instances",
            status=status,
            expected=expected_count or total_count,
            actual=up_count,
            message=message,
            command="show evpn summary"
        )

    def parse_vpws_status(
        self,
        output: str,
        expected_count: Optional[int] = None
    ) -> VerificationCheck:
        """Parse VPWS status."""
        up_count = 0
        total_count = 0
        
        lines = output.split('\n')
        for line in lines:
            if '|' in line:
                line_lower = line.lower()
                if 'up' in line_lower or 'down' in line_lower:
                    total_count += 1
                    if 'up' in line_lower and 'down' not in line_lower:
                        up_count += 1
        
        if total_count == 0:
            status = VerificationStatus.SKIPPED
            message = "No VPWS services found"
        elif up_count == total_count:
            status = VerificationStatus.PASS
            message = f"All {up_count} VPWS services UP"
        else:
            status = VerificationStatus.PARTIAL
            message = f"{up_count}/{total_count} VPWS services UP"
        
        return VerificationCheck(
            name="VPWS Services",
            status=status,
            expected=expected_count or total_count,
            actual=up_count,
            message=message,
            command="show vpws summary"
        )

    def parse_isis_status(
        self,
        output: str,
        expected_adjacencies: Optional[int] = None
    ) -> VerificationCheck:
        """Parse ISIS adjacency status."""
        up_count = 0
        total_count = 0
        
        lines = output.split('\n')
        for line in lines:
            if '|' in line:
                line_lower = line.lower()
                if 'up' in line_lower or 'init' in line_lower or 'down' in line_lower:
                    total_count += 1
                    if 'up' in line_lower:
                        up_count += 1
        
        if total_count == 0:
            status = VerificationStatus.SKIPPED
            message = "No ISIS adjacencies found"
        elif up_count == total_count:
            status = VerificationStatus.PASS
            message = f"All {up_count} ISIS adjacencies UP"
        else:
            status = VerificationStatus.PARTIAL
            message = f"{up_count}/{total_count} ISIS adjacencies UP"
        
        return VerificationCheck(
            name="ISIS Adjacencies",
            status=status,
            expected=expected_adjacencies or total_count,
            actual=up_count,
            message=message,
            command="show isis adjacency"
        )

    def parse_ospf_status(
        self,
        output: str,
        expected_neighbors: Optional[int] = None
    ) -> VerificationCheck:
        """Parse OSPF neighbor status."""
        full_count = 0
        total_count = 0
        
        lines = output.split('\n')
        for line in lines:
            if '|' in line or re.match(r'^\s*\d+\.\d+\.\d+\.\d+', line):
                line_lower = line.lower()
                if 'full' in line_lower or '2way' in line_lower or 'init' in line_lower:
                    total_count += 1
                    if 'full' in line_lower:
                        full_count += 1
        
        if total_count == 0:
            status = VerificationStatus.SKIPPED
            message = "No OSPF neighbors found"
        elif full_count == total_count:
            status = VerificationStatus.PASS
            message = f"All {full_count} OSPF neighbors FULL"
        else:
            status = VerificationStatus.PARTIAL
            message = f"{full_count}/{total_count} OSPF neighbors FULL"
        
        return VerificationCheck(
            name="OSPF Neighbors",
            status=status,
            expected=expected_neighbors or total_count,
            actual=full_count,
            message=message,
            command="show ospf neighbor"
        )

    def parse_ldp_status(
        self,
        output: str,
        expected_neighbors: Optional[int] = None
    ) -> VerificationCheck:
        """Parse LDP neighbor status."""
        up_count = 0
        total_count = 0
        
        lines = output.split('\n')
        for line in lines:
            # Match lines with IP addresses (LDP neighbors)
            if re.match(r'^\s*\d+\.\d+\.\d+\.\d+', line):
                total_count += 1
                line_lower = line.lower()
                if 'operational' in line_lower or 'established' in line_lower:
                    up_count += 1
        
        if total_count == 0:
            status = VerificationStatus.SKIPPED
            message = "No LDP neighbors found"
        elif up_count == total_count:
            status = VerificationStatus.PASS
            message = f"All {up_count} LDP neighbors operational"
        else:
            status = VerificationStatus.PARTIAL
            message = f"{up_count}/{total_count} LDP neighbors operational"
        
        return VerificationCheck(
            name="LDP Neighbors",
            status=status,
            expected=expected_neighbors or total_count,
            actual=up_count,
            message=message,
            command="show ldp neighbor"
        )

    def compare_states(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any]
    ) -> List[VerificationCheck]:
        """
        Compare operational states before and after commit.
        
        Args:
            before: State before commit
            after: State after commit
        
        Returns:
            List of verification checks
        """
        checks = []
        
        # Compare interface counts
        if 'interfaces' in before and 'interfaces' in after:
            before_up = before['interfaces'].get('up', 0)
            after_up = after['interfaces'].get('up', 0)
            
            if after_up >= before_up:
                status = VerificationStatus.PASS
                message = f"Interfaces UP: {before_up} -> {after_up} (+{after_up - before_up})"
            else:
                status = VerificationStatus.FAIL
                message = f"Interfaces UP decreased: {before_up} -> {after_up} ({after_up - before_up})"
            
            checks.append(VerificationCheck(
                name="Interface Count",
                status=status,
                expected=before_up,
                actual=after_up,
                message=message,
                command="compare"
            ))
        
        # Compare service counts
        for svc_type in ['fxc', 'vrf', 'evpn', 'vpws']:
            if svc_type in before and svc_type in after:
                before_count = before[svc_type].get('count', 0)
                after_count = after[svc_type].get('count', 0)
                
                if after_count >= before_count:
                    status = VerificationStatus.PASS
                else:
                    status = VerificationStatus.FAIL
                
                checks.append(VerificationCheck(
                    name=f"{svc_type.upper()} Count",
                    status=status,
                    expected=before_count,
                    actual=after_count,
                    message=f"{svc_type.upper()}: {before_count} -> {after_count}",
                    command="compare"
                ))
        
        return checks

    def generate_summary(self, checks: List[VerificationCheck]) -> str:
        """
        Generate a summary of verification results.
        
        Args:
            checks: List of verification checks
        
        Returns:
            Summary string
        """
        pass_count = sum(1 for c in checks if c.status == VerificationStatus.PASS)
        fail_count = sum(1 for c in checks if c.status == VerificationStatus.FAIL)
        partial_count = sum(1 for c in checks if c.status == VerificationStatus.PARTIAL)
        skipped_count = sum(1 for c in checks if c.status == VerificationStatus.SKIPPED)
        
        total = len(checks)
        
        if fail_count > 0:
            overall = "FAILED"
        elif partial_count > 0:
            overall = "PARTIAL"
        elif pass_count > 0:
            overall = "PASSED"
        else:
            overall = "SKIPPED"
        
        return (
            f"Verification {overall}: "
            f"{pass_count} passed, {fail_count} failed, "
            f"{partial_count} partial, {skipped_count} skipped "
            f"(out of {total} checks)"
        )

    def format_results(
        self,
        checks: List[VerificationCheck],
        use_rich: bool = True
    ) -> str:
        """
        Format verification results for display.
        
        Args:
            checks: List of verification checks
            use_rich: Whether to use Rich markup
        
        Returns:
            Formatted results string
        """
        lines = []
        lines.append("")
        lines.append("Verification Results")
        lines.append("=" * 50)
        
        for check in checks:
            if check.status == VerificationStatus.PASS:
                icon = "[green]✓[/green]" if use_rich else "✓"
            elif check.status == VerificationStatus.FAIL:
                icon = "[red]✗[/red]" if use_rich else "✗"
            elif check.status == VerificationStatus.PARTIAL:
                icon = "[yellow]◐[/yellow]" if use_rich else "◐"
            else:
                icon = "[dim]○[/dim]" if use_rich else "○"
            
            lines.append(f"{icon} {check.name}: {check.message}")
        
        lines.append("")
        lines.append(self.generate_summary(checks))
        
        return '\n'.join(lines)














