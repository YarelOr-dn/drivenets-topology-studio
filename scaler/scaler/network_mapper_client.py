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
import time
import threading
from typing import Optional, Dict, Any, List, Tuple
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
    """Client for interacting with network-mapper MCP server.

    Thread-safety: a single persistent worker Task on a dedicated event-loop
    thread owns the SSE session. All MCP calls from any thread are submitted
    as work items to this worker via an asyncio.Queue, and the caller blocks
    on a threading.Event until the result is ready.

    This guarantees that sse_client context managers are always entered AND
    exited inside the same asyncio Task, preventing the anyio
    'cancel scope in different task' RuntimeError.
    """
    
    DEFAULT_URL = "http://192.168.174.88:8080/sse"
    SESSION_TTL = 300   # idle timeout before session is recycled (seconds)
    KEEPALIVE_SEC = 45  # probe interval when queue is idle
    
    def __init__(self, url: Optional[str] = None):
        self.url = url or self.DEFAULT_URL
        self._boot_lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._work_queue: Optional[asyncio.Queue] = None
        self._started = False
        self._state = 'idle'
        self._last_success_ts: float = 0
        self._last_error_msg = ''
        self._stats = {'calls': 0, 'errors': 0, 'reconnects': 0}
        
        if not MCP_AVAILABLE:
            raise ImportError("mcp library not installed. Install with: pip install mcp")
        
        threading.Thread(target=self._warmup, daemon=True, name="mcp-warmup").start()
    
    def _log(self, msg):
        print(f"[NM-MCP] {msg}")
    
    @property
    def is_connected(self) -> bool:
        return self._state == 'connected'
    
    def health(self) -> Dict[str, Any]:
        """Connection health and usage stats."""
        return {
            'state': self._state,
            'url': self.url,
            'calls': self._stats['calls'],
            'errors': self._stats['errors'],
            'reconnects': self._stats['reconnects'],
            'last_error': self._last_error_msg,
        }
    
    def _warmup(self):
        """Eagerly establish SSE session so first real call is fast."""
        try:
            self._submit([("list_devices", {}, 1, 10)], timeout=20)
            self._state = 'connected'
            self._log("Pre-warmed OK")
        except Exception as e:
            self._state = 'error'
            self._last_error_msg = str(e)
            self._log(f"Pre-warm failed (retry on first call): {e}")
    
    def _ensure_worker(self):
        """Start the dedicated loop + worker task if not running."""
        with self._boot_lock:
            if self._started and self._loop is not None and self._loop.is_running():
                return
            ready = threading.Event()
            self._loop = asyncio.new_event_loop()
            self._thread = threading.Thread(
                target=self._run_loop, args=(ready,), daemon=True, name="mcp-loop"
            )
            self._thread.start()
            ready.wait(timeout=5)
            self._started = True

    def _run_loop(self, ready: threading.Event):
        """Entry point for the dedicated thread."""
        asyncio.set_event_loop(self._loop)
        self._work_queue = asyncio.Queue()
        self._loop.create_task(self._worker())
        ready.set()
        self._loop.run_forever()

    async def _worker(self):
        """Persistent Task that owns the SSE session.

        When no work arrives for KEEPALIVE_SEC, sends a lightweight probe
        to detect stale connections before a real call hits them.
        """
        session = None
        sse_cm = None
        session_cm = None
        last_activity: float = 0

        async def fresh_session():
            nonlocal session, sse_cm, session_cm, last_activity
            self._state = 'connecting'
            self._stats['reconnects'] += 1
            session = None
            sse_cm = sse_client(self.url)
            rd, wr = await sse_cm.__aenter__()
            session_cm = ClientSession(rd, wr)
            session = await session_cm.__aenter__()
            await session.initialize()
            last_activity = time.monotonic()
            self._state = 'connected'
            self._log("Session established")

        async def discard_session():
            nonlocal session, sse_cm, session_cm, last_activity
            for cm in (session_cm, sse_cm):
                if cm is not None:
                    try:
                        await cm.__aexit__(None, None, None)
                    except Exception:
                        pass
            session = sse_cm = session_cm = None
            last_activity = 0
            self._state = 'disconnected'

        while True:
            try:
                item = await asyncio.wait_for(
                    self._work_queue.get(), timeout=self.KEEPALIVE_SEC
                )
            except asyncio.TimeoutError:
                # Idle -- probe the session so we know it's alive
                if session is not None:
                    try:
                        await asyncio.wait_for(
                            session.call_tool("list_devices", {}), timeout=10
                        )
                        last_activity = time.monotonic()
                    except Exception:
                        self._log("Keepalive failed, dropping session")
                        await discard_session()
                continue

            if item is None:
                await discard_session()
                return

            calls, result_holder, done_event = item
            try:
                idle = (time.monotonic() - last_activity) if last_activity else float('inf')
                if session is None or idle >= self.SESSION_TTL:
                    await discard_session()
                    await fresh_session()

                results = []
                for call_item in calls:
                    tool_name = call_item[0]
                    arguments = call_item[1] if len(call_item) > 1 else {}
                    max_retries = call_item[2] if len(call_item) > 2 else 1
                    per_call_timeout = call_item[3] if len(call_item) > 3 else 15

                    last_error = None
                    for attempt in range(max_retries + 1):
                        try:
                            if session is None:
                                await fresh_session()
                            result = await asyncio.wait_for(
                                session.call_tool(tool_name, arguments or {}),
                                timeout=per_call_timeout
                            )
                            text = None
                            if hasattr(result, 'content') and result.content:
                                for c_item in result.content:
                                    if hasattr(c_item, 'text'):
                                        text = c_item.text
                                        break
                            results.append(text if text is not None else str(result))
                            last_error = None
                            last_activity = time.monotonic()
                            self._stats['calls'] += 1
                            self._last_success_ts = time.time()
                            break
                        except asyncio.TimeoutError:
                            last_error = TimeoutError(
                                f"{tool_name} timed out ({per_call_timeout}s)")
                            self._log(f"{tool_name} timeout (attempt {attempt+1})")
                            await discard_session()
                            if attempt < max_retries:
                                await asyncio.sleep(1.5 * (attempt + 1))
                        except Exception as e:
                            last_error = e
                            self._log(f"{tool_name} error (attempt {attempt+1}): {e}")
                            await discard_session()
                            if attempt < max_retries:
                                await asyncio.sleep(1.5 * (attempt + 1))
                    if last_error is not None:
                        self._stats['errors'] += 1
                        self._last_error_msg = str(last_error)
                        results.append(last_error)

                result_holder["results"] = results
            except Exception as e:
                result_holder["error"] = e
                self._stats['errors'] += 1
                self._last_error_msg = str(e)
                await discard_session()
            finally:
                done_event.set()

    def close(self):
        """Discard session by telling the worker to recreate on next call."""
        if self._loop and self._loop.is_running() and self._work_queue is not None:
            done = threading.Event()
            holder: Dict[str, Any] = {}
            asyncio.run_coroutine_threadsafe(
                self._work_queue.put(([], holder, done)), self._loop
            )
            done.wait(timeout=5)
    
    def _submit(self, calls, timeout: float = 30) -> List[Any]:
        """Submit work items to the worker and block until done.

        Each item in *calls* is a tuple:
            (tool_name, arguments, max_retries[, per_call_timeout])
        *timeout* is the overall wall-clock limit for the entire batch.
        """
        self._ensure_worker()
        done = threading.Event()
        holder: Dict[str, Any] = {}
        asyncio.run_coroutine_threadsafe(
            self._work_queue.put((calls, holder, done)), self._loop
        )
        if not done.wait(timeout=timeout):
            self._last_error_msg = f"Batch timed out after {timeout}s"
            raise TimeoutError(self._last_error_msg)
        if "error" in holder:
            raise holder["error"]
        results = holder.get("results", [])
        out = []
        for r in results:
            if isinstance(r, Exception):
                raise r
            out.append(r)
        return out

    def _call_tool(self, tool_name: str, arguments: Dict[str, Any] = None,
                   timeout: float = 15) -> Any:
        """Synchronous single-tool call. Safe from any thread.

        *timeout* applies per MCP tool invocation (seconds).
        The overall submit timeout adds 15s buffer for reconnection/retries.
        """
        results = self._submit(
            [(tool_name, arguments, 3, timeout)],
            timeout=timeout + 15
        )
        return results[0]
    
    def list_topologies(self) -> List[Topology]:
        """
        Get all available topologies from network-mapper.
        
        Returns:
            List of Topology objects
        """
        result = self._call_tool("list_topologies", timeout=10)
        return self._parse_topologies_markdown(result)
    
    def list_devices(self) -> List[TopologyDevice]:
        """
        Get all devices from network-mapper.
        
        Returns:
            List of TopologyDevice objects
        """
        result = self._call_tool("list_devices", timeout=10)
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
        result = self._call_tool("get_device_config", {"device_name": device_name}, timeout=20)
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
        result = self._call_tool("get_device_lldp", {"device_name": device_name}, timeout=10)
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
        calls = [("get_device_system_info", {"device_name": name}, 1, 15) for name in device_names]
        
        results = []
        try:
            raw = self._submit(calls, timeout=60)
            results = [r if not isinstance(r, Exception) else None for r in raw]
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
            }, timeout=10)
            
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
            result = self._call_tool("refresh_device", {"device_name": device_name}, timeout=30)
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
