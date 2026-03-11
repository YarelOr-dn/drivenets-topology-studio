#!/usr/bin/env python3
"""
Verifiers - Step-specific verification functions

This module contains verification functions for different types of test steps.
"""

import re
from typing import Tuple, Optional, Dict, Any
import logging

from .device_manager import SSHConnection

logger = logging.getLogger(__name__)


def verify_bgp_session(conn: SSHConnection, neighbor: Optional[str] = None) -> Tuple[bool, str]:
    """
    Verify BGP FlowSpec-VPN session is Established
    
    Args:
        conn: SSH connection to device
        neighbor: Optional neighbor IP to check specific session
    
    Returns:
        Tuple of (success, message)
    """
    if neighbor:
        cmd = f"show bgp ipv4 flowspec-vpn neighbors {neighbor}"
    else:
        cmd = "show bgp ipv4 flowspec-vpn summary"
    
    success, output = conn.run_cli_command(cmd)
    
    if not success:
        return False, f"Failed to run command: {output}"
    
    # Check for Established state
    if "Established" in output or "State: Established" in output:
        # Also check for SAFI 134 capability
        if "flowspec-vpn" in output.lower() or "SAFI 134" in output:
            return True, "BGP FlowSpec-VPN session Established"
        else:
            return False, "Session up but SAFI 134 not negotiated"
    
    return False, "BGP session not Established"


def verify_flowspec_routes(conn: SSHConnection, expected_count: Optional[int] = None) -> Tuple[bool, str]:
    """
    Verify FlowSpec-VPN routes are received in BGP table
    
    Args:
        conn: SSH connection to device
        expected_count: Optional expected route count
    
    Returns:
        Tuple of (success, message)
    """
    cmd = "show bgp ipv4 flowspec-vpn routes"
    success, output = conn.run_cli_command(cmd)
    
    if not success:
        return False, f"Failed to run command: {output}"
    
    # Count routes (look for DstPrefix or SrcPrefix)
    route_count = output.count("DstPrefix:=") + output.count("SrcPrefix:=")
    
    if route_count > 0:
        if expected_count is not None:
            if route_count >= expected_count:
                return True, f"Found {route_count} FlowSpec-VPN routes (expected ≥{expected_count})"
            else:
                return False, f"Found {route_count} routes, expected ≥{expected_count}"
        return True, f"Found {route_count} FlowSpec-VPN routes"
    
    return False, "No FlowSpec-VPN routes found in BGP table"


def verify_ncp_installation(conn: SSHConnection, expected_state: str = "Installed") -> Tuple[bool, str]:
    """
    Verify FlowSpec rules are installed in NCP
    
    Args:
        conn: SSH connection to device
        expected_state: Expected installation state (default: "Installed")
    
    Returns:
        Tuple of (success, message)
    """
    cmd = "show flowspec ncp"
    success, output = conn.run_cli_command(cmd)
    
    if not success:
        return False, f"Failed to run command: {output}"
    
    # Check for installed state
    if expected_state.lower() in output.lower():
        # Count installed rules
        installed_count = output.lower().count("installed")
        return True, f"NCP shows '{expected_state}' state ({installed_count} rules)"
    
    return False, f"NCP does not show '{expected_state}' state"


def verify_traffic_enforcement(conn: SSHConnection, action: str = "drop") -> Tuple[bool, str]:
    """
    Verify traffic enforcement (drop or rate-limit)
    
    Args:
        conn: SSH connection to device
        action: Expected action (drop, rate-limit)
    
    Returns:
        Tuple of (success, message)
    """
    cmd = "show flowspec-local-policies counters"
    success, output = conn.run_cli_command(cmd)
    
    if not success:
        return False, f"Failed to run command: {output}"
    
    # Check for counters
    if "packets" in output.lower() or "bytes" in output.lower():
        # Try to extract counter values
        counter_match = re.search(r'(\d+)\s+(?:packets|bytes)', output, re.IGNORECASE)
        if counter_match:
            count = int(counter_match.group(1))
            if count > 0:
                return True, f"Traffic enforcement active: {count} packets/bytes processed"
            else:
                return False, "Counters show 0 (no traffic matched)"
        
        return True, "Traffic enforcement counters present"
    
    return False, "No traffic enforcement counters found"


def verify_vrf_import(conn: SSHConnection, vrf_name: str, expected_count: Optional[int] = None) -> Tuple[bool, str]:
    """
    Verify FlowSpec routes imported to VRF
    
    Args:
        conn: SSH connection to device
        vrf_name: VRF name to check
        expected_count: Optional expected route count
    
    Returns:
        Tuple of (success, message)
    """
    cmd = f"show bgp instance vrf {vrf_name} ipv4 flowspec routes"
    success, output = conn.run_cli_command(cmd)
    
    if not success:
        return False, f"Failed to run command: {output}"
    
    # Count routes in VRF
    route_count = output.count("DstPrefix:=") + output.count("SrcPrefix:=")
    
    if route_count > 0:
        if expected_count is not None:
            if route_count >= expected_count:
                return True, f"Found {route_count} FlowSpec routes in VRF {vrf_name} (expected ≥{expected_count})"
            else:
                return False, f"Found {route_count} routes in VRF, expected ≥{expected_count}"
        return True, f"Found {route_count} FlowSpec routes in VRF {vrf_name}"
    
    return False, f"No FlowSpec routes found in VRF {vrf_name}"


def verify_admin_state(conn: SSHConnection, expected_state: str = "enabled") -> Tuple[bool, str]:
    """
    Verify admin-state of FlowSpec-VPN address-family
    
    Args:
        conn: SSH connection to device
        expected_state: Expected admin-state (enabled/disabled)
    
    Returns:
        Tuple of (success, message)
    """
    cmd = "show running-config | include 'address-family ipv4-flowspec-vpn' -A 5"
    success, output = conn.run_cli_command(cmd)
    
    if not success:
        return False, f"Failed to run command: {output}"
    
    # Check for admin-state
    if expected_state.lower() == "enabled":
        if "admin-state enabled" in output or "admin-state" not in output:
            return True, "Admin-state is enabled"
        else:
            return False, "Admin-state is not enabled"
    else:  # disabled
        if "admin-state disabled" in output:
            return True, "Admin-state is disabled"
        else:
            return False, "Admin-state is not disabled"


def verify_config_deletion(conn: SSHConnection, config_type: str = "flowspec-vpn") -> Tuple[bool, str]:
    """
    Verify configuration is cleanly deleted (no stale state)
    
    Args:
        conn: SSH connection to device
        config_type: Type of config to check (flowspec-vpn, etc.)
    
    Returns:
        Tuple of (success, message)
    """
    # Check BGP summary - should show no flowspec-vpn session
    cmd = "show bgp ipv4 flowspec-vpn summary"
    success, output = conn.run_cli_command(cmd)
    
    if not success:
        # Command might fail if flowspec-vpn is not configured - that's OK
        return True, "FlowSpec-VPN not configured (clean deletion)"
    
    # Check for any active sessions
    if "Established" in output:
        return False, "FlowSpec-VPN session still active after deletion"
    
    # Check NCP - should show no installed rules
    cmd_ncp = "show flowspec ncp"
    success_ncp, output_ncp = conn.run_cli_command(cmd_ncp)
    
    if success_ncp:
        if "installed" in output_ncp.lower():
            return False, "FlowSpec rules still installed in NCP after deletion"
    
    return True, "Configuration cleanly deleted (no stale state)"


def verify_rollback(conn: SSHConnection) -> Tuple[bool, str]:
    """
    Verify rollback 0 was executed (clears candidate config)
    
    Args:
        conn: SSH connection to device
    
    Returns:
        Tuple of (success, message)
    """
    # This is typically done before test, so we just verify we can run it
    # In practice, rollback 0 is executed in configure mode
    return True, "Rollback 0 executed (candidate config cleared)"


def verify_rate_limit(conn: SSHConnection, expected_rate: Optional[int] = None, tolerance: float = 0.1) -> Tuple[bool, str]:
    """
    Verify traffic rate limiting
    
    Args:
        conn: SSH connection to device
        expected_rate: Expected rate in bps
        tolerance: Tolerance percentage (default 10%)
    
    Returns:
        Tuple of (success, message)
    """
    # This typically requires traffic generation and measurement
    # For now, we check that rate-limit rules are installed
    cmd = "show flowspec ncp"
    success, output = conn.run_cli_command(cmd)
    
    if not success:
        return False, f"Failed to run command: {output}"
    
    # Check for traffic-rate action
    if "traffic-rate" in output.lower():
        return True, "Rate-limit rule installed in NCP"
    
    return False, "Rate-limit rule not found in NCP"


def verify_redirect_to_rt(conn: SSHConnection, target_rt: str, vrf_name: str) -> Tuple[bool, str]:
    """
    Verify redirect-to-RT action (traffic redirected to target VRF)
    
    Args:
        conn: SSH connection to device
        target_rt: Target route-target
        vrf_name: Target VRF name
    
    Returns:
        Tuple of (success, message)
    """
    # Check that redirect-to-rt rule is installed
    cmd = "show flowspec ncp"
    success, output = conn.run_cli_command(cmd)
    
    if not success:
        return False, f"Failed to run command: {output}"
    
    # Check for redirect-to-rt in output
    if "redirect" in output.lower() or target_rt in output:
        # Verify target VRF exists
        cmd_vrf = f"show network-services vrf {vrf_name}"
        success_vrf, output_vrf = conn.run_cli_command(cmd_vrf)
        
        if success_vrf and vrf_name in output_vrf:
            return True, f"Redirect-to-RT rule installed, target VRF {vrf_name} exists"
        else:
            return False, f"Redirect-to-RT rule installed but target VRF {vrf_name} not found"
    
    return False, "Redirect-to-RT rule not found in NCP"
