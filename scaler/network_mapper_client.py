"""Network Mapper MCP Client.

Provides OPTIONAL integration with the network-mapper MCP server to:
- Add new devices from network-mapper topology
- Enhance parsing with live device data

This is NOT required for normal SCALER operation - SSH extraction works without it.
"""

import asyncio
import re
import json
import logging
import sys
import io
import signal
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

# Suppress verbose httpx and mcp library errors
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)
logging.getLogger("mcp").setLevel(logging.ERROR)
logging.getLogger("mcp.client.sse").setLevel(logging.CRITICAL)

# MCP import with timeout protection (pydantic schema processing can hang)
MCP_AVAILABLE = False
MCP_IMPORT_ERROR = None

def _timeout_handler(signum, frame):
    raise TimeoutError("MCP import timed out")

try:
    # Set a 5-second timeout for MCP import (pydantic can hang)
    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(5)
    try:
        from mcp import ClientSession
        from mcp.client.sse import sse_client
        MCP_AVAILABLE = True
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
except ImportError as e:
    MCP_IMPORT_ERROR = f"mcp library not installed: {e}"
except TimeoutError:
    MCP_IMPORT_ERROR = "MCP import timed out (pydantic schema processing hung)"
except Exception as e:
    MCP_IMPORT_ERROR = f"MCP import failed: {e}"


@dataclass
class InterfaceInfo:
    """Interface information from network-mapper."""
    name: str
    admin_state: str = "unknown"
    oper_state: str = "unknown"
    mtu: Optional[int] = None
    description: Optional[str] = None


@dataclass
class LLDPNeighbor:
    """LLDP neighbor information."""
    local_interface: str
    neighbor_name: str
    neighbor_interface: str


@dataclass
class TopologyDevice:
    """Device information within a topology."""
    name: str
    version: str = "unknown"
    status: str = "unknown"
    system_type: str = "unknown"
    serial_number: Optional[str] = None
    topology_name: Optional[str] = None


@dataclass
class Topology:
    """Topology information from network-mapper."""
    name: str
    devices: List[TopologyDevice] = field(default_factory=list)


class NetworkMapperClient:
    """Client for interacting with network-mapper MCP server."""
    
    DEFAULT_URL = "http://192.168.174.88:8080/sse"
    
    def __init__(self, url: Optional[str] = None):
        """
        Initialize the network-mapper client.
        
        Args:
            url: MCP server URL. Defaults to the standard network-mapper URL.
        """
        self.url = url or self.DEFAULT_URL
        self._session = None
        self._read = None
        self._write = None
        
        if not MCP_AVAILABLE:
            raise ImportError("mcp library not installed. Install with: pip install mcp")
    
    async def _call_tool_async(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """
        Call an MCP tool asynchronously.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        max_retries = 3
        last_error = None
        for attempt in range(max_retries + 1):
            # Suppress stderr during MCP calls to hide library tracebacks
            old_stderr = sys.stderr
            sys.stderr = io.StringIO()
            try:
                async with sse_client(self.url) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments or {})
                        
                        # Extract text content from result
                        if hasattr(result, 'content') and result.content:
                            for item in result.content:
                                if hasattr(item, 'text'):
                                    return item.text
                        return str(result)
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    # Exponential backoff
                    await asyncio.sleep(1.5 * (attempt + 1))
            finally:
                sys.stderr = old_stderr
        raise Exception(f"Network-mapper connection failed after {max_retries + 1} attempts: {last_error}")
    
    def _call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """
        Synchronous wrapper for tool calls.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop and loop.is_running():
            # We're already in an async context - create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self._call_tool_async(tool_name, arguments)
                )
                return future.result(timeout=60)
        else:
            return asyncio.run(self._call_tool_async(tool_name, arguments))
    
    async def _call_tools_batch_async(self, calls: List[tuple]) -> List[Any]:
        """
        Call multiple tools in a single session for efficiency.
        
        Args:
            calls: List of (tool_name, arguments) tuples
            
        Returns:
            List of results in the same order as calls
        """
        results = []
        try:
            async with sse_client(self.url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    for tool_name, arguments in calls:
                        try:
                            result = await session.call_tool(tool_name, arguments or {})
                            
                            if hasattr(result, 'content') and result.content:
                                for item in result.content:
                                    if hasattr(item, 'text'):
                                        results.append(item.text)
                                        break
                                else:
                                    results.append(str(result))
                            else:
                                results.append(str(result))
                        except Exception as e:
                            results.append(None)
        except Exception as e:
            # Return partial results on connection failure
            while len(results) < len(calls):
                results.append(None)
        
        return results
    
    def list_topologies(self) -> List[Topology]:
        """
        Get all available topologies from network-mapper.
        
        Returns:
            List of Topology objects
        """
        result = self._call_tool("list_topologies")
        return self._parse_topologies_markdown(result)
    
    def list_devices(self) -> List[TopologyDevice]:
        """
        Get all devices from network-mapper.
        
        Returns:
            List of TopologyDevice objects
        """
        result = self._call_tool("list_devices")
        return self._parse_devices_markdown(result)
    
    def get_device_system_info(self, device_name: str) -> Dict[str, Any]:
        """
        Get system information for a device.
        
        Args:
            device_name: Device name or partial name
            
        Returns:
            Dict with system info (version, uptime, status, etc.)
        """
        result = self._call_tool("get_device_system_info", {"device_name": device_name})
        return self._parse_system_info_markdown(result)
    
    def get_device_config(self, device_name: str) -> Optional[str]:
        """
        Get running configuration for a device.
        
        Args:
            device_name: Device name or partial name
            
        Returns:
            Configuration text (clean DNOS config, no markdown)
        """
        result = self._call_tool("get_device_config", {"device_name": device_name})
        if not result:
            return None
        
        # Strip markdown code blocks and headers
        return self._clean_config_markdown(result)
    
    def get_device_interfaces(self, device_name: str) -> List[InterfaceInfo]:
        """
        Get interface information for a device.
        
        Args:
            device_name: Device name or partial name
            
        Returns:
            List of InterfaceInfo objects
        """
        result = self._call_tool("get_device_interfaces", {"device_name": device_name})
        return self._parse_interfaces_markdown(result)
    
    def get_device_lldp(self, device_name: str) -> List[LLDPNeighbor]:
        """
        Get LLDP neighbor information for a device.
        
        Args:
            device_name: Device name or partial name
            
        Returns:
            List of LLDPNeighbor objects
        """
        result = self._call_tool("get_device_lldp", {"device_name": device_name})
        return self._parse_lldp_markdown(result)
    
    def batch_get_device_info(self, device_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get system info and configs for multiple devices in a single session.
        
        Args:
            device_names: List of device names
            
        Returns:
            Dict mapping device_name to {system_info: ..., config: ...}
        """
        # Build batch of calls - only system info for speed, skip configs initially
        calls = []
        for name in device_names:
            calls.append(("get_device_system_info", {"device_name": name}))
        
        # Execute batch with timeout
        results = []
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            
            if loop and loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._call_tools_batch_async(calls)
                    )
                    results = future.result(timeout=60)  # Reduced timeout
            else:
                results = asyncio.run(self._call_tools_batch_async(calls))
        except Exception as e:
            # Return empty on any error
            return {name: {'system_info': {}, 'config': None} for name in device_names}
        
        # Parse results
        device_info = {}
        for i, name in enumerate(device_names):
            sys_result = results[i] if i < len(results) else None
            
            device_info[name] = {
                'system_info': self._parse_system_info_markdown(sys_result) if sys_result else {},
                'config': None  # Don't fetch configs during listing - too slow
            }
        
        return device_info
    
    def _extract_hostname(self, device_name: str) -> str:
        """
        Extract clean hostname from network-mapper device name.
        
        Network-mapper device names often include version info like:
        'R1_CL16_Eddie_priv_25.4.0.30' -> 'R1_CL16_Eddie'
        
        Args:
            device_name: Full device name from network-mapper
            
        Returns:
            Clean hostname
        """
        # Remove version suffix pattern (_priv_X.Y.Z.N or _dev_X.Y.Z.N)
        hostname = re.sub(r'_(priv|dev)_\d+\.\d+\.\d+\.?\d*$', '', device_name)
        return hostname
    
    def extract_mgmt_ip_from_config(self, config: str) -> Optional[str]:
        """
        Extract management IP address from running configuration.
        
        Args:
            config: Running configuration text
            
        Returns:
            Management IP address or None if not found
        """
        lines = config.split('\n')
        in_mgmt0 = False
        
        for line in lines:
            stripped = line.strip()
            if stripped == 'mgmt0':
                in_mgmt0 = True
            elif in_mgmt0 and stripped.startswith('ipv4-address'):
                ip_match = re.search(r'ipv4-address\s+(\d+\.\d+\.\d+\.\d+)', stripped)
                if ip_match:
                    return ip_match.group(1)
            elif in_mgmt0 and (stripped == '!' or (stripped and not stripped.startswith(' '))):
                in_mgmt0 = False
        
        return None
    
    def get_device_management_ip(self, device_name: str) -> Optional[str]:
        """
        Get management IP for a device using multiple sources.
        
        Tries in order:
        1. Device inventory JSON (from discovery script)
        2. MCP interfaces with mgmt0 filter
        3. Extract from running config
        
        Args:
            device_name: Device name or partial name
            
        Returns:
            Management IP or None
        """
        hostname = self._extract_hostname(device_name)
        
        # Strategy 1: Try device_inventory.json (discovery script output)
        try:
            import os
            inventory_paths = [
                os.path.expanduser("~/CURSOR/device_inventory.json"),
                "/home/dn/CURSOR/device_inventory.json"
            ]
            
            for inv_path in inventory_paths:
                if os.path.exists(inv_path):
                    with open(inv_path, 'r') as f:
                        inventory = json.load(f)
                    
                    for dev_id, dev_data in inventory.get('devices', {}).items():
                        inv_hostname = dev_data.get('hostname', '')
                        # Match by hostname or device ID
                        if (hostname.lower() in inv_hostname.lower() or 
                            hostname.lower() in dev_id.lower()):
                            mgmt_ip = dev_data.get('mgmt_ip')
                            if mgmt_ip:
                                return mgmt_ip
                            
                            # Also check all_mgmt_interfaces for mgmt0
                            for iface in dev_data.get('all_mgmt_interfaces', []):
                                if iface.get('name', '').lower() == 'mgmt0':
                                    ipv4 = iface.get('ipv4', '')
                                    if ipv4:
                                        # Extract IP from "192.168.x.x/20 (DHCP)" format
                                        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', ipv4)
                                        if ip_match:
                                            return ip_match.group(1)
                    break
        except Exception:
            pass
        
        # Strategy 2: Try to get mgmt0 from MCP interfaces
        try:
            result = self._call_tool("get_device_interfaces", {
                "device_name": device_name,
                "filter_pattern": "mgmt0"
            })
            
            if result:
                for line in result.split('\n'):
                    if '|' in line and 'mgmt0' in line.lower():
                        parts = [p.strip() for p in line.split('|')]
                        for part in parts:
                            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', part)
                            if ip_match:
                                return ip_match.group(1)
        except Exception:
            pass
        
        # Strategy 3: Try to extract from config
        try:
            config = self.get_device_config(device_name)
            if config:
                ip = self.extract_mgmt_ip_from_config(config)
                if ip:
                    return ip
        except Exception:
            pass
        
        return None
    
    def get_device_serial_number(self, device_name: str) -> Optional[str]:
        """
        Get serial number for a device.
        
        Tries multiple strategies:
        1. Extract from device name (e.g., Slava_1_WK31C8V10001BP2_priv_26.1.0.22)
        2. Get NCC serial from system info components table
        3. Get from stored device credentials/original hostname
        
        Args:
            device_name: Device name or partial name
            
        Returns:
            Serial number or None
        """
        # Strategy 1: Extract SN from device name
        # Pattern: letters/numbers that look like a serial (e.g., WK31C8V10001BP2)
        sn_match = re.search(r'_([A-Z]{2}[A-Z0-9]{10,})(?:_|$)', device_name)
        if sn_match:
            return sn_match.group(1)
        
        # Strategy 2: Get NCC/NCP serial from system info (raw markdown)
        try:
            result = self._call_tool("get_device_system_info", {"device_name": device_name})
            if result:
                # Parse markdown table for component serials
                # Priority: NCC active > NCP active > any NCP > any component
                ncc_active_serial = None
                ncc_serial = None
                ncp_active_serial = None
                ncp_serial = None
                any_serial = None
                
                for line in result.split('\n'):
                    if '|' not in line:
                        continue
                    parts = [p.strip() for p in line.split('|')]
                    
                    # Look for serial in the last columns
                    serial = None
                    for part in reversed(parts):
                        if part and re.match(r'^[A-Z0-9]{8,}$', part):
                            serial = part
                            break
                    
                    if not serial:
                        continue
                    
                    # Store as fallback
                    if not any_serial:
                        any_serial = serial
                    
                    # Check component type and state
                    if 'NCC' in line:
                        if 'active' in line.lower():
                            ncc_active_serial = serial
                        elif not ncc_serial:
                            ncc_serial = serial
                    elif 'NCP' in line:
                        if 'active' in line.lower() or 'up' in line.lower():
                            if not ncp_active_serial:
                                ncp_active_serial = serial
                        elif not ncp_serial:
                            ncp_serial = serial
                
                # Return in priority order
                if ncc_active_serial:
                    return ncc_active_serial
                if ncc_serial:
                    return ncc_serial
                if ncp_active_serial:
                    return ncp_active_serial
                if ncp_serial:
                    return ncp_serial
                if any_serial:
                    return any_serial
        except Exception:
            pass
        
        return None
    
    def refresh_device(self, device_name: str) -> bool:
        """
        Refresh device data from network-mapper (re-connects via SSH).
        
        Args:
            device_name: Device name or partial name
            
        Returns:
            True if refresh succeeded
        """
        try:
            result = self._call_tool("refresh_device", {"device_name": device_name})
            return result and "successfully" in result.lower()
        except Exception:
            return False
    
    def get_full_device_info_with_mgmt(self, device_name: str) -> Dict[str, Any]:
        """
        Get complete device info including management IP.
        
        This method tries multiple strategies to find the management IP:
        1. From device_inventory.json (discovery script output)
        2. From mgmt0 interface in interface list
        3. From config (if not truncated)
        4. From system info serial (as connection target fallback)
        
        Args:
            device_name: Device name
            
        Returns:
            Dict with hostname, serial, mgmt_ip, system_info, config_lines
        """
        info = {
            'hostname': self._extract_hostname(device_name),
            'full_name': device_name,
            'serial': None,
            'mgmt_ip': None,
            'system_info': {},
            'config_lines': 0,
            'config_truncated': False
        }
        
        # Get serial number first (fast, from system info)
        serial = self.get_device_serial_number(device_name)
        info['serial'] = serial
        
        # Try to get management IP using all strategies
        mgmt_ip = self.get_device_management_ip(device_name)
        if mgmt_ip:
            info['mgmt_ip'] = mgmt_ip
            info['connection_target'] = mgmt_ip
        elif serial:
            info['connection_target'] = serial
        else:
            info['connection_target'] = None
        
        # Get system info
        sys_info = self.get_device_system_info(device_name)
        info['system_info'] = sys_info
        
        # Get config info (for line count check)
        config = self.get_device_config(device_name)
        if config:
            info['config_lines'] = len(config.split('\n'))
            # Check if truncated (network-mapper limits to ~1000 lines)
            if info['config_lines'] >= 990:
                info['config_truncated'] = True
        
        return info
    
    def get_device_connection_target(self, device_name: str) -> Optional[str]:
        """
        Get the best connection target for a device (IP or serial number).
        
        For DNaaS devices, the serial number can be used as SSH target.
        
        Args:
            device_name: Device name
            
        Returns:
            IP address or serial number for SSH connection
        """
        # Try management IP first
        mgmt_ip = self.get_device_management_ip(device_name)
        if mgmt_ip:
            return mgmt_ip
        
        # Fall back to serial number (works for DNaaS)
        serial = self.get_device_serial_number(device_name)
        if serial:
            return serial
        
        return None
    
    def _clean_config_markdown(self, text: str) -> str:
        """
        Clean markdown formatting from configuration text.
        
        Args:
            text: Raw text possibly containing markdown
            
        Returns:
            Clean configuration text
        """
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        in_code_block = False
        code_started = False
        
        for line in lines:
            stripped = line.strip()
            
            # Check for code block markers
            if stripped.startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    code_started = True
                    continue
                else:
                    in_code_block = False
                    continue
            
            # Skip markdown headers before code block
            if not code_started and stripped.startswith('#'):
                continue
            
            # If we're in a code block, keep the line
            if in_code_block:
                cleaned_lines.append(line)
            # If we never hit a code block marker, assume it's all config
            elif not code_started and not stripped.startswith('#'):
                # Only add if we haven't seen any markdown indicators
                cleaned_lines.append(line)
        
        # If no code block was found, return original (minus markdown headers)
        if not code_started:
            result_lines = []
            for line in lines:
                if not line.strip().startswith('#'):
                    result_lines.append(line)
            return '\n'.join(result_lines).strip()
        
        return '\n'.join(cleaned_lines).strip()
    
    def _parse_topologies_markdown(self, text: str) -> List[Topology]:
        """Parse topology list from markdown format."""
        topologies = []
        
        if not text:
            return topologies
        
        current_topology = None
        in_table = False
        
        for line in text.split('\n'):
            line = line.strip()
            
            # Topology header
            if line.startswith('## '):
                if current_topology:
                    topologies.append(current_topology)
                current_topology = Topology(name=line[3:].strip())
                in_table = False
            
            # Table row (device)
            elif line.startswith('|') and current_topology and '-----' not in line:
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 3 and parts[0] != 'Device':
                    device = TopologyDevice(
                        name=parts[0],
                        version=parts[1] if len(parts) > 1 else "unknown",
                        status=parts[2] if len(parts) > 2 else "unknown",
                        topology_name=current_topology.name
                    )
                    current_topology.devices.append(device)
        
        if current_topology:
            topologies.append(current_topology)
        
        return topologies
    
    def _parse_devices_markdown(self, text: str) -> List[TopologyDevice]:
        """Parse device list from markdown format."""
        devices = []
        
        if not text:
            return devices
        
        for line in text.split('\n'):
            line = line.strip()
            
            if line.startswith('|') and '-----' not in line:
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 3 and parts[0] != 'Device':
                    device = TopologyDevice(
                        name=parts[0],
                        version=parts[1] if len(parts) > 1 else "unknown",
                        status=parts[2] if len(parts) > 2 else "unknown"
                    )
                    devices.append(device)
        
        return devices
    
    def _parse_system_info_markdown(self, text: str) -> Dict[str, Any]:
        """Parse system information from markdown format."""
        info = {}
        
        if not text:
            return info
        
        for line in text.split('\n'):
            line = line.strip()
            
            # Key: Value format
            if ':' in line and not line.startswith('#'):
                # Handle markdown bold/formatting
                clean_line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
                parts = clean_line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower().replace(' ', '_')
                    value = parts[1].strip()
                    info[key] = value
            
            # Table row format
            elif line.startswith('|') and '-----' not in line:
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 2:
                    key = parts[0].lower().replace(' ', '_')
                    value = parts[1]
                    info[key] = value
        
        return info
    
    def _parse_interfaces_markdown(self, text: str) -> List[InterfaceInfo]:
        """Parse interface list from markdown format."""
        interfaces = []
        
        if not text:
            return interfaces
        
        for line in text.split('\n'):
            line = line.strip()
            
            if line.startswith('|') and '-----' not in line:
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 2 and parts[0].lower() != 'interface':
                    iface = InterfaceInfo(
                        name=parts[0],
                        admin_state=parts[1] if len(parts) > 1 else "unknown",
                        oper_state=parts[2] if len(parts) > 2 else "unknown"
                    )
                    interfaces.append(iface)
        
        return interfaces
    
    def _parse_lldp_markdown(self, text: str) -> List[LLDPNeighbor]:
        """Parse LLDP neighbors from markdown format."""
        neighbors = []
        
        if not text:
            return neighbors
        
        for line in text.split('\n'):
            line = line.strip()
            
            if line.startswith('|') and '-----' not in line:
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 3 and 'interface' not in parts[0].lower():
                    neighbor = LLDPNeighbor(
                        local_interface=parts[0],
                        neighbor_name=parts[1] if len(parts) > 1 else "unknown",
                        neighbor_interface=parts[2] if len(parts) > 2 else "unknown"
                    )
                    neighbors.append(neighbor)
        
        return neighbors


# Convenience function for quick access
def get_mapper_client(url: Optional[str] = None) -> NetworkMapperClient:
    """
    Get a NetworkMapperClient instance.
    
    Args:
        url: Optional custom URL for the MCP server
        
    Returns:
        NetworkMapperClient instance
    """
    return NetworkMapperClient(url)
