#!/usr/bin/env python3
"""
Simple API server for running DNAAS discovery from the web UI.
Run this alongside your web server.
"""

import subprocess
import threading
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import queue

# Pre-import MCP client in main thread (signal.SIGALRM only works in main thread)
try:
    from scaler.network_mapper_client import NetworkMapperClient, MCP_AVAILABLE
    print(f"[Init] MCP client loaded: available={MCP_AVAILABLE}")
except Exception as e:
    MCP_AVAILABLE = False
    print(f"[Init] MCP client import failed: {e}")

SCRIPT_DIR = Path(__file__).parent
# Use main discovery script which supports --multi-bd flag
DISCOVERY_SCRIPT = SCRIPT_DIR / "dnaas_path_discovery.py"
OUTPUT_DIR = SCRIPT_DIR / "output"

# Store running jobs
jobs = {}
job_counter = 0
job_lock = threading.Lock()
job_processes = {}  # Store subprocess handles for cancellation

# Network Mapper jobs (separate from discovery jobs)
nm_jobs = {}
nm_job_counter = 0
nm_job_lock = threading.Lock()

# MCP client singleton (reused across requests to avoid repeated SSE handshakes)
_mcp_client = None
_mcp_client_lock = threading.Lock()


def _get_mcp_client():
    """Get or create the shared NetworkMapperClient instance (thread-safe)."""
    global _mcp_client
    import sys
    if '/home/dn/SCALER' not in sys.path:
        sys.path.insert(0, '/home/dn/SCALER')
    with _mcp_client_lock:
        if _mcp_client is None:
            from scaler.network_mapper_client import NetworkMapperClient
            _mcp_client = NetworkMapperClient()
        return _mcp_client


def _reset_mcp_client():
    """Reset the MCP client (call when connection is known dead)."""
    global _mcp_client
    with _mcp_client_lock:
        if _mcp_client is not None:
            try:
                _mcp_client.close()
            except Exception:
                pass
            _mcp_client = None


def _nm_cleanup_old_jobs():
    """Remove completed nm_jobs older than 30 minutes."""
    cutoff = time.time() - 1800
    with nm_job_lock:
        to_remove = [jid for jid, j in nm_jobs.items()
                     if j.get('status') in ('completed', 'cancelled', 'failed')
                     and j.get('created_at', 0) < cutoff]
        for jid in to_remove:
            nm_jobs.pop(jid, None)


def _cleanup_old_discovery_jobs():
    """Remove completed DNAAS discovery jobs older than 30 minutes."""
    cutoff = time.time() - 1800
    with job_lock:
        to_remove = [jid for jid, j in jobs.items()
                     if j.get('status') in ('completed', 'failed', 'cancelled')
                     and j.get('created_at', 0) < cutoff]
        for jid in to_remove:
            jobs.pop(jid, None)


# ANSI escape code pattern for stripping colors
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text for cleaner output."""
    return ANSI_ESCAPE.sub('', text)


def _parse_lldp_output(output: str) -> list:
    """
    Parse 'show lldp neighbor(s)' table output (DNOS style).
    Accepts pipe-separated table or space-aligned columns.
    Returns list of dicts: local_interface, neighbor_device, neighbor_port, capability.
    """
    neighbors = []
    in_table = False
    lines = output.split('\n')
    for line in lines:
        # Detect table header (pipes or Interface + Neighbor)
        if 'Interface' in line and 'Neighbor' in line:
            in_table = True
            continue
        if '---' in line or '|-' in line or '-|' in line:
            continue
        # Stop at CLI prompt
        if re.match(r'^[A-Za-z0-9_.-]+#', line.strip()) or re.match(r'^[A-Za-z0-9_.-]+\(', line.strip()):
            in_table = False
            continue
        # Pipe-separated table
        if in_table and '|' in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 3:
                local_iface = parts[0]
                neighbor_dev = parts[1]
                neighbor_port = parts[2]
                capability = parts[3] if len(parts) > 3 else ''
                if neighbor_dev and neighbor_dev not in ('Neighbor', 'Neighbor System Name', '-', ''):
                    if local_iface and not local_iface.lower().startswith('interface'):
                        neighbors.append({
                            'local_interface': local_iface,
                            'neighbor_device': neighbor_dev,
                            'neighbor_port': neighbor_port,
                            'capability': capability or ''
                        })
            continue
        # Space-aligned table (no pipes): at least 2 spaces between columns
        if in_table and line.strip():
            # Split on 2+ spaces to get columns
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 3:
                local_iface = parts[0]
                neighbor_dev = parts[1]
                neighbor_port = parts[2]
                capability = parts[3] if len(parts) > 3 else ''
                if neighbor_dev and neighbor_dev not in ('Neighbor', '-', ''):
                    if local_iface and not local_iface.lower().startswith('interface'):
                        neighbors.append({
                            'local_interface': local_iface,
                            'neighbor_device': neighbor_dev,
                            'neighbor_port': neighbor_port,
                            'capability': capability or ''
                        })
    return neighbors


# ========================================================================
# Network Mapper — Recursive LLDP Discovery Engine
# ========================================================================

def _nm_resolve_host(name: str, known_devices: list = None) -> str:
    """Resolve a device name/serial/IP to a connectable target.
    known_devices: list of dicts from canvas with {name, host, hostBackup, serial}
    """
    import socket
    if re.match(r'^\d+\.\d+\.\d+\.\d+$', name):
        return name
    # Check canvas/DNAAS known devices first — these have verified IPs
    if known_devices:
        name_lower = name.lower()
        for kd in known_devices:
            kd_name = (kd.get('name') or '').lower()
            kd_backup = (kd.get('hostBackup') or '').lower()
            kd_serial = (kd.get('serial') or '').lower()
            if name_lower in (kd_name, kd_backup, kd_serial) or kd_name in name_lower or name_lower in kd_name:
                resolved = kd.get('host') or kd.get('serial') or ''
                if resolved:
                    return resolved
    domain_suffixes = ['', '.dev.drivenets.net', '.drivenets.net', '.local']
    for suffix in domain_suffixes:
        try:
            return socket.gethostbyname(name + suffix)
        except socket.gaierror:
            continue
    if name != name.upper():
        try:
            return socket.gethostbyname(name.upper())
        except socket.gaierror:
            pass
    # Try SCALER DB
    db_configs = Path('/home/dn/SCALER/db/configs')
    if db_configs.exists():
        for device_dir in db_configs.iterdir():
            if device_dir.is_dir():
                op_file = device_dir / 'operational.json'
                if op_file.exists():
                    try:
                        with open(op_file, 'r') as f:
                            op_data = json.load(f)
                        dev_hostname = (op_data.get('hostname', '') or '').lower()
                        dev_ip = op_data.get('connection_ip', '') or ''
                        if dev_hostname and (name.lower() == dev_hostname or
                                             name.lower() in dev_hostname or
                                             dev_hostname in name.lower()):
                            if dev_ip:
                                return dev_ip
                    except Exception:
                        pass
    # Try device_inventory.json
    inv_file = Path('/home/dn/CURSOR/device_inventory.json')
    if inv_file.exists():
        try:
            with open(inv_file, 'r') as f:
                inv_data = json.load(f)
            devices = inv_data.get('devices', {})
            for key, dev in devices.items():
                dev_hostname = (dev.get('hostname', '') or '').lower()
                if dev_hostname == name.lower() or name.lower() in dev_hostname:
                    mgmt_ip = dev.get('mgmt_ip', '') or ''
                    if mgmt_ip:
                        return mgmt_ip
        except Exception:
            pass
    return name


def _nm_ssh_discover_device(host: str, username: str, password: str, timeout: int = 30) -> dict:
    """SSH to a device and collect hostname, system info, LLDP neighbors, mgmt interfaces."""
    import paramiko
    result = {
        'hostname': host,
        'mgmt_ip': host if re.match(r'^\d+\.\d+\.\d+\.\d+$', host) else '',
        'serial': '',
        'system_type': '',
        'dnos_version': '',
        'lldp_neighbors': [],
        'error': None
    }
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=username, password=password,
                       timeout=timeout, look_for_keys=False, allow_agent=False)
    except Exception as e:
        result['error'] = str(e)
        return result

    try:
        shell = client.invoke_shell(width=250, height=50)
        shell.settimeout(timeout)
        import time as _time
        _time.sleep(3)
        while shell.recv_ready():
            shell.recv(65535)
            _time.sleep(0.2)

        def _run_cmd(cmd, wait=4, max_wait=15):
            shell.send(cmd + ' | no-more\r\n')
            _time.sleep(wait)
            output = ''
            end = _time.time() + max_wait
            while _time.time() < end:
                if shell.recv_ready():
                    output += shell.recv(65535).decode('utf-8', errors='replace')
                    if '#' in output.split('\n')[-1]:
                        _time.sleep(0.3)
                        if shell.recv_ready():
                            output += shell.recv(65535).decode('utf-8', errors='replace')
                        break
                _time.sleep(0.3)
            return strip_ansi(output)

        # Hostname from prompt
        shell.send('\r\n')
        _time.sleep(1)
        prompt_out = ''
        if shell.recv_ready():
            prompt_out = shell.recv(65535).decode('utf-8', errors='replace')
        prompt_clean = strip_ansi(prompt_out).strip()
        prompt_match = re.search(r'([A-Za-z0-9_.-]+)#', prompt_clean)
        if prompt_match:
            result['hostname'] = prompt_match.group(1)

        # System info
        sys_output = _run_cmd('show system', wait=3)
        for line in sys_output.split('\n'):
            line_s = line.strip()
            if 'serial' in line_s.lower() and ':' in line_s:
                result['serial'] = line_s.split(':', 1)[1].strip()
            elif 'type' in line_s.lower() and ':' in line_s and not result['system_type']:
                result['system_type'] = line_s.split(':', 1)[1].strip()
            elif 'version' in line_s.lower() and 'dnos' in line_s.lower():
                result['dnos_version'] = line_s.strip()

        # LLDP neighbors
        lldp_output = _run_cmd('show lldp neighbors', wait=3)
        result['lldp_neighbors'] = _parse_lldp_output(lldp_output)
        if not result['lldp_neighbors']:
            lldp_output2 = _run_cmd('show lldp neighbor', wait=3)
            result['lldp_neighbors'] = _parse_lldp_output(lldp_output2)

        # Management interfaces (for mgmt IP)
        if not result['mgmt_ip']:
            mgmt_output = _run_cmd('show interfaces management', wait=3)
            for line in mgmt_output.split('\n'):
                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)/\d+', line)
                if ip_match and not ip_match.group(1).startswith('127.'):
                    result['mgmt_ip'] = ip_match.group(1)
                    break

        # Interface brief for speed/state (lightweight — no detail)
        result['interfaces'] = {}
        try:
            iface_output = _run_cmd('show interfaces brief', wait=3)
            for line in iface_output.split('\n'):
                parts = line.split()
                if len(parts) >= 3 and re.match(r'(ge|hu|ce|eth|bundle)', parts[0]):
                    iface_name = parts[0]
                    iface_data = {}
                    for p in parts[1:]:
                        if re.match(r'\d+[GMK]', p):
                            iface_data['speed'] = p
                        elif p.lower() in ('up', 'down'):
                            iface_data['oper_state'] = p.lower()
                    if 'bundle' in iface_name.lower():
                        iface_data['is_bundle'] = True
                    result['interfaces'][iface_name] = iface_data
        except Exception:
            pass

        client.close()
    except Exception as e:
        result['error'] = str(e)
        try:
            client.close()
        except Exception:
            pass
    return result


def _nm_try_network_mapper_mcp(name: str) -> dict:
    """Try to get enriched device data from Network Mapper MCP server.
    Returns dict with lldp_neighbors, system_type, dnos_version, serial, interfaces.
    Returns None if MCP has no data for this device.
    """
    try:
        nm = _get_mcp_client()

        # Get LLDP first — if no LLDP, device is unknown to MCP
        nm_neighbors = nm.get_device_lldp(name)
        if not nm_neighbors:
            return None

        lldp = [{
            'local_interface': n.local_interface,
            'neighbor_device': n.neighbor_name,
            'neighbor_port': n.neighbor_interface
        } for n in nm_neighbors]

        result = {'lldp_neighbors': lldp, 'system_type': '', 'dnos_version': '', 'serial': '', 'interfaces': {}}

        # Enrich with system info
        try:
            sys_info = nm.get_device_system_info(name)
            if sys_info:
                result['system_type'] = sys_info.get('system_type', '') or sys_info.get('platform', '') or ''
                result['dnos_version'] = sys_info.get('version', '') or sys_info.get('software_version', '') or ''
                result['serial'] = sys_info.get('serial_number', '') or sys_info.get('serial', '') or ''
        except Exception:
            pass

        # Enrich with interface details (speed, bundle membership)
        try:
            iface_raw = nm._call_tool("get_device_interfaces_detail", {"device_name": name})
            if iface_raw:
                result['interfaces'] = _parse_mcp_interfaces_detail(iface_raw)
        except Exception:
            pass

        return result
    except Exception:
        return None


def _parse_mcp_interfaces_detail(text: str) -> dict:
    """Parse MCP get_device_interfaces_detail markdown into {ifname: {speed, bundle, mtu}}."""
    interfaces = {}
    if not text:
        return interfaces

    current_iface = None
    for line in text.split('\n'):
        line = line.strip()
        # Interface header like "### ge400-0/0/1" or "**ge400-0/0/1**"
        if line.startswith('###') or (line.startswith('**') and line.endswith('**')):
            iface_name = re.sub(r'[#*\s]+', '', line).strip()
            if iface_name:
                current_iface = iface_name
                interfaces[current_iface] = {}
        elif current_iface and ':' in line:
            key, _, val = line.partition(':')
            key = key.strip().lower().replace(' ', '_').replace('**', '')
            val = val.strip()
            if key in ('speed', 'mtu', 'bundle', 'bundle_membership', 'fec', 'mac_address'):
                interfaces[current_iface][key] = val
        elif line.startswith('|') and '---' not in line and current_iface is None:
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 2:
                iface_name = parts[0]
                if iface_name and not iface_name.lower().startswith('interface'):
                    interfaces[iface_name] = {}
                    for i, val in enumerate(parts[1:]):
                        if val:
                            interfaces[iface_name][f'col_{i}'] = val

    return interfaces


def _nm_bfs_crawl(job_id: str, seeds: list, max_depth: int, max_devices: int,
                  username: str, password: str, use_mcp: bool, known_devices: list = None):
    """BFS crawl from seed devices using LLDP to discover the network graph.
    known_devices: canvas/DNAAS devices with SSH info for smarter resolution.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    known_devices = known_devices or []
    # Build credentials lookup from known devices
    known_creds = {}
    for kd in known_devices:
        for key in [kd.get('name',''), kd.get('hostBackup',''), kd.get('serial','')]:
            if key:
                known_creds[key.lower()] = kd

    devices = {}   # hostname -> device_info
    links = []     # [{from_device, to_device, from_interface, to_interface}]
    link_set = set()  # for dedup: frozenset((devA:ifA, devB:ifB))
    errors = []
    visited = set()   # normalized hostnames
    bfs_queue = queue.Queue()

    def normalize(name):
        return (name or '').strip().upper()

    def log(msg):
        print(f"[NM-{job_id}] {msg}")
        with nm_job_lock:
            if job_id in nm_jobs:
                nm_jobs[job_id]['log'].append(msg)

    # Seed the queue
    for seed in seeds:
        seed = seed.strip()
        if seed:
            resolved = _nm_resolve_host(seed, known_devices)
            bfs_queue.put((seed, resolved, 0))
            log(f"Seed: {seed} -> {resolved}")

    with nm_job_lock:
        nm_jobs[job_id]['status'] = 'running'

    batch_size = 5  # concurrent SSH sessions

    while not bfs_queue.empty():
        # Check cancellation
        with nm_job_lock:
            if nm_jobs[job_id].get('cancelled'):
                nm_jobs[job_id]['status'] = 'cancelled'
                log("Discovery cancelled by user")
                return

        # Collect a batch from the queue
        batch = []
        while not bfs_queue.empty() and len(batch) < batch_size:
            name, host, depth = bfs_queue.get()
            norm = normalize(name)
            if norm in visited:
                continue
            if len(devices) >= max_devices:
                log(f"Reached max devices limit ({max_devices})")
                break
            if depth > max_depth:
                continue
            visited.add(norm)
            batch.append((name, host, depth))

        if not batch:
            break

        # Discover batch concurrently
        with ThreadPoolExecutor(max_workers=min(batch_size, len(batch))) as executor:
            futures = {}
            for name, host, depth in batch:
                log(f"Discovering {name} ({host}) at depth {depth}...")
                # Try MCP first for enriched device data
                mcp_result = None
                if use_mcp:
                    mcp_result = _nm_try_network_mapper_mcp(name)

                if mcp_result and mcp_result.get('lldp_neighbors'):
                    device_info = {
                        'hostname': name,
                        'mgmt_ip': host if re.match(r'^\d+\.\d+\.\d+\.\d+$', host) else '',
                        'serial': mcp_result.get('serial', ''),
                        'system_type': mcp_result.get('system_type', ''),
                        'dnos_version': mcp_result.get('dnos_version', ''),
                        'lldp_neighbors': mcp_result['lldp_neighbors'],
                        'interfaces': mcp_result.get('interfaces', {}),
                        'error': None,
                        'source': 'mcp'
                    }
                    futures[executor.submit(lambda d=device_info: d)] = (name, host, depth)
                else:
                    # Use known device credentials if available
                    ssh_user = username
                    ssh_pass = password
                    kd = known_creds.get(name.lower()) or known_creds.get(host.lower())
                    if kd:
                        ssh_user = kd.get('user') or username
                        ssh_pass = kd.get('password') or password
                    futures[executor.submit(
                        _nm_ssh_discover_device, host, ssh_user, ssh_pass
                    )] = (name, host, depth)

            for future in as_completed(futures):
                name, host, depth = futures[future]
                try:
                    dev_info = future.result()
                except Exception as e:
                    errors.append({'device': name, 'host': host, 'error': str(e)})
                    log(f"  FAILED {name}: {e}")
                    continue

                if dev_info.get('error'):
                    errors.append({'device': name, 'host': host, 'error': dev_info['error']})
                    log(f"  FAILED {name}: {dev_info['error']}")
                    # Still store partial data (hostname from seed)
                    dev_info['_failed'] = True

                # Use discovered hostname if available, fall back to seed name
                actual_hostname = dev_info.get('hostname', name) or name
                dev_info['hostname'] = actual_hostname
                dev_info['_connect_host'] = host
                dev_info['_depth'] = depth
                devices[actual_hostname] = dev_info

                with nm_job_lock:
                    nm_jobs[job_id]['devices'] = dict(devices)
                    nm_jobs[job_id]['progress']['discovered'] = len(devices)

                log(f"  OK {actual_hostname}: {len(dev_info.get('lldp_neighbors', []))} LLDP neighbors")

                # Process LLDP neighbors — add links and enqueue new devices
                for neighbor in dev_info.get('lldp_neighbors', []):
                    neighbor_name = neighbor.get('neighbor_device', '')
                    if not neighbor_name:
                        continue

                    local_if = neighbor.get('local_interface', '')
                    remote_if = neighbor.get('neighbor_port', '')

                    # Deduplicate bidirectional links
                    link_key = frozenset([
                        f"{actual_hostname}:{local_if}",
                        f"{neighbor_name}:{remote_if}"
                    ])
                    if link_key not in link_set:
                        link_set.add(link_key)
                        links.append({
                            'from_device': actual_hostname,
                            'to_device': neighbor_name,
                            'from_interface': local_if,
                            'to_interface': remote_if
                        })

                    # Enqueue neighbor if not visited
                    norm_neighbor = normalize(neighbor_name)
                    if norm_neighbor not in visited and len(devices) < max_devices:
                        resolved_neighbor = _nm_resolve_host(neighbor_name, known_devices)
                        bfs_queue.put((neighbor_name, resolved_neighbor, depth + 1))

        # Update progress
        with nm_job_lock:
            nm_jobs[job_id]['links'] = list(links)
            nm_jobs[job_id]['errors'] = list(errors)
            nm_jobs[job_id]['progress']['queued'] = bfs_queue.qsize()
            nm_jobs[job_id]['progress']['failed'] = len(errors)

    # Finalize
    with nm_job_lock:
        nm_jobs[job_id]['status'] = 'completed'
        nm_jobs[job_id]['devices'] = dict(devices)
        nm_jobs[job_id]['links'] = list(links)
        nm_jobs[job_id]['errors'] = list(errors)
        nm_jobs[job_id]['progress']['discovered'] = len(devices)
        nm_jobs[job_id]['progress']['queued'] = 0

    log(f"Discovery complete: {len(devices)} devices, {len(links)} links, {len(errors)} errors")


def _nm_mcp_full_map(job_id):
    """Build complete topology from MCP data — no SSH needed.

    Uses batch calls for efficiency: one SSE session per device.
    """
    import asyncio

    def log(msg):
        print(f"[MCPMap-{job_id}] {msg}")
        with nm_job_lock:
            if job_id in nm_jobs:
                nm_jobs[job_id]['log'].append(msg)

    def run_async(coro):
        """Run async coroutine safely from any thread."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    with nm_job_lock:
        nm_jobs[job_id]['status'] = 'running'

    try:
        nm = _get_mcp_client()
    except Exception as e:
        with nm_job_lock:
            nm_jobs[job_id]['status'] = 'completed'
            nm_jobs[job_id]['errors'] = [{'device': 'MCP', 'error': str(e)}]
        log(f"MCP init failed: {e}")
        return

    # --- Step 1: list all devices ---
    log("Listing devices from MCP...")
    try:
        raw_list = run_async(nm._call_tool_async("list_devices"))
        all_mcp_devices = nm._parse_devices_markdown(raw_list)
    except Exception as e:
        with nm_job_lock:
            nm_jobs[job_id]['status'] = 'completed'
            nm_jobs[job_id]['errors'] = [{'device': 'MCP', 'error': f"list_devices: {e}"}]
        log(f"list_devices failed: {e}")
        return

    total = len(all_mcp_devices)
    log(f"MCP knows {total} devices")

    if total == 0:
        with nm_job_lock:
            nm_jobs[job_id]['status'] = 'completed'
        log("No devices found")
        return

    # hostname normalization
    clean_name_map = {}
    full_to_clean = {}
    for d in all_mcp_devices:
        clean = nm._extract_hostname(d.name)
        full_to_clean[d.name] = clean
        key = clean.lower()
        if key not in clean_name_map:
            clean_name_map[key] = clean

    # --- Step 2: per-device LLDP + system_info + mgmt_ip ---
    devices = {}
    links = []
    link_set = set()
    errors = []

    for idx, d in enumerate(all_mcp_devices):
        clean = full_to_clean[d.name]
        log(f"[{idx+1}/{total}] {clean}")

        with nm_job_lock:
            nm_jobs[job_id]['progress']['discovered'] = idx + 1

        batch_calls = [
            ("get_device_lldp", {"device_name": d.name}),
            ("get_device_system_info", {"device_name": d.name}),
            ("get_device_management_interfaces", {"device_name": d.name}),
        ]
        batch_results = [None, None, None]
        try:
            batch_results = run_async(nm._call_tools_batch_async(batch_calls))
        except Exception as e:
            errors.append({'device': clean, 'error': f"batch: {e}"})
            log(f"  Error fetching {clean}: {e}")

        lldp_text = batch_results[0] or ''
        sys_text = batch_results[1] or ''
        mgmt_text = batch_results[2] or ''

        lldp_raw = nm._parse_lldp_markdown(lldp_text)
        sys_info = nm._parse_system_info_markdown(sys_text)

        # Parse mgmt IP from management interfaces text
        mgmt_ip = ''
        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', mgmt_text)
        if ip_match:
            mgmt_ip = ip_match.group(1)

        # Clean up version: "DNOS [26.2.0] build [2_priv], Copyright..." -> "26.2.0"
        raw_ver = sys_info.get('version', sys_info.get('software_version', d.version if d.version != 'unknown' else ''))
        ver_match = re.search(r'(\d+\.\d+\.\d+)', raw_ver)
        clean_ver = ver_match.group(1) if ver_match else raw_ver

        # Clean system_type: "SA-36CD-S (NCR)" -> "SA-36CD-S"
        raw_sys = sys_info.get('system_type', sys_info.get('platform', ''))
        sys_match = re.match(r'^([A-Za-z0-9_-]+)', raw_sys)
        clean_sys = sys_match.group(1) if sys_match else raw_sys

        dev_entry = {
            'hostname': clean,
            'mgmt_ip': mgmt_ip,
            'serial': sys_info.get('serial', sys_info.get('serial_number', '')),
            'system_type': clean_sys,
            'dnos_version': clean_ver,
            'lldp_neighbors': [],
            'source': 'mcp',
            '_connect_host': mgmt_ip
        }

        for n in lldp_raw:
            nb_clean = clean_name_map.get(n.neighbor_name.lower(), n.neighbor_name)
            dev_entry['lldp_neighbors'].append({
                'local_interface': n.local_interface,
                'neighbor_device': nb_clean,
                'neighbor_port': n.neighbor_interface
            })
            lk = frozenset([f"{clean}:{n.local_interface}", f"{nb_clean}:{n.neighbor_interface}"])
            if lk not in link_set:
                link_set.add(lk)
                links.append({
                    'from_device': clean,
                    'to_device': nb_clean,
                    'from_interface': n.local_interface,
                    'to_interface': n.neighbor_interface
                })

        devices[clean] = dev_entry

        with nm_job_lock:
            nm_jobs[job_id]['devices'] = dict(devices)
            nm_jobs[job_id]['links'] = list(links)

    # --- Step 3: stubs for LLDP neighbors not in device list ---
    known_lower = {k.lower() for k in devices}
    stubs_added = 0
    for link in links:
        for field in ('from_device', 'to_device'):
            dn = link[field]
            if dn.lower() not in known_lower:
                devices[dn] = {
                    'hostname': dn, 'mgmt_ip': '', 'serial': '',
                    'system_type': '', 'dnos_version': '',
                    'lldp_neighbors': [], 'source': 'lldp_stub', '_connect_host': ''
                }
                known_lower.add(dn.lower())
                stubs_added += 1

    if stubs_added:
        log(f"Added {stubs_added} stub device(s) from LLDP neighbor references")

    with nm_job_lock:
        nm_jobs[job_id]['status'] = 'completed'
        nm_jobs[job_id]['devices'] = dict(devices)
        nm_jobs[job_id]['links'] = list(links)
        nm_jobs[job_id]['errors'] = errors
        nm_jobs[job_id]['progress']['discovered'] = len(devices)
        nm_jobs[job_id]['progress']['queued'] = 0

    log(f"MCP map complete: {len(devices)} devices ({stubs_added} stubs), {len(links)} links")


class DiscoveryHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _enable_lldp_on_device(self, serial: str, job_id: str = None, username: str = 'dnroot', password: str = 'dnroot', skip_host_key: bool = False) -> dict:
        """
        Enable LLDP and admin-state on all PHYSICAL interfaces of a device.
        Only enables on ge*, eth*, hu*, ce*, qsfp* - NOT on loopbacks, management, or sub-interfaces.
        Uses SSH to configure the device.
        
        If job_id is provided, updates the job's output_lines for real-time feedback.
        If skip_host_key is True, ignores all host key verification (like ssh -o StrictHostKeyChecking=no).
        """
        import paramiko
        import re
        import time
        
        def log(msg: str):
            """Log message to job output and print"""
            print(msg)
            if job_id and job_id in jobs:
                jobs[job_id]['output_lines'].append(msg)
        
        try:
            log(f"🔌 Connecting to {serial}...")
            if skip_host_key:
                log(f"🔓 Host key verification: DISABLED (lab/test mode)")
            
            # Resolve hostname to IP - try with domain suffix if bare hostname fails
            import socket
            connect_host = serial
            resolved_ip = None
            
            # Common domain suffixes for DNOS devices
            domain_suffixes = ['', '.dev.drivenets.net', '.drivenets.net', '.local']
            
            for suffix in domain_suffixes:
                try_host = serial + suffix
                try:
                    resolved_ip = socket.gethostbyname(try_host)
                    connect_host = try_host
                    log(f"📍 Resolved {try_host} → {resolved_ip}")
                    break
                except socket.gaierror:
                    continue
            
            if not resolved_ip:
                log(f"⚠ DNS lookup failed for {serial} (tried with domain suffixes)")
                log(f"📍 Trying direct connection to {serial}...")
            else:
                # Use resolved IP for connection (more reliable)
                connect_host = resolved_ip
            
            # Connect to device
            client = paramiko.SSHClient()
            
            # Host key policy: AutoAddPolicy for normal, WarningPolicy that accepts all for skip mode
            if skip_host_key:
                # Create a policy that accepts ANY host key (like -o StrictHostKeyChecking=no)
                class AcceptAllPolicy(paramiko.MissingHostKeyPolicy):
                    def missing_host_key(self, client, hostname, key):
                        pass  # Accept all keys silently
                client.set_missing_host_key_policy(AcceptAllPolicy())
                # Also load system host keys but don't fail on mismatch
                try:
                    client.load_system_host_keys()
                except:
                    pass
            else:
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                client.connect(
                    connect_host,
                    username=username,
                    password=password,
                    timeout=30,
                    look_for_keys=False,
                    allow_agent=False
                )
            except paramiko.ssh_exception.NoValidConnectionsError as conn_err:
                log(f"✗ Cannot connect to {connect_host}: No route to host or connection refused")
                raise Exception(f"Cannot connect to {connect_host}: {conn_err}")
            except paramiko.ssh_exception.AuthenticationException as auth_err:
                log(f"✗ Authentication failed for {connect_host}")
                raise Exception(f"SSH auth failed for {connect_host}: {auth_err}")
            except socket.timeout:
                log(f"✗ Connection timed out for {connect_host}")
                raise Exception(f"SSH connection timed out for {connect_host}")
            except socket.error as sock_err:
                log(f"✗ Socket error connecting to {connect_host}: {sock_err}")
                raise Exception(f"Cannot reach {connect_host}: {sock_err}")
            
            log(f"✓ Connected to {connect_host} (serial: {serial})")
            
            # Store SSH client in job for cancellation support
            if job_id and job_id in jobs:
                jobs[job_id]['_ssh_client'] = client
            
            # Helper to check if cancelled
            def is_cancelled():
                return job_id and job_id in jobs and jobs[job_id].get('cancelled', False)
            
            # Set up transport with keepalive
            transport = client.get_transport()
            transport.set_keepalive(10)  # Send keepalive every 10 seconds (more frequent)
            
            # Get interactive shell
            try:
                shell = client.invoke_shell(width=250, height=50)
                shell.settimeout(180)  # Increase timeout to 3 minutes for slow devices
            except Exception as shell_err:
                log(f"✗ Failed to open shell: {shell_err}")
                raise Exception(f"Failed to open SSH shell on {serial}: {shell_err}")
            
            log("⏳ Waiting for CLI to load...")
            
            # Helper to safely send command
            def safe_send(cmd):
                try:
                    # Check if connection is still alive
                    transport = client.get_transport()
                    if not transport or not transport.is_active():
                        log(f"✗ SSH transport is no longer active")
                        raise Exception(f"SSH connection to {serial} was closed")
                    return shell.send(cmd)
                except BrokenPipeError as e:
                    log(f"✗ Broken pipe - connection closed by remote: {e}")
                    raise Exception(f"SSH connection to {serial} was closed by remote host (broken pipe)")
                except socket.error as e:
                    log(f"✗ Connection lost: {e}")
                    raise Exception(f"SSH connection lost to {serial}: {e}")
                except OSError as e:
                    log(f"✗ OS error: {e}")
                    raise Exception(f"SSH error on {serial}: {e}")
                except Exception as e:
                    log(f"✗ Error: {e}")
                    raise Exception(f"SSH error on {serial}: {e}")
            
            # Helper to safely receive
            def safe_recv(timeout_seconds=10):
                output = ""
                end_time = time.time() + timeout_seconds
                try:
                    while time.time() < end_time:
                        if shell.recv_ready():
                            output += shell.recv(65535).decode('utf-8', errors='ignore')
                        else:
                            time.sleep(0.3)
                        # Break early if we have substantial output and no more coming
                        if len(output) > 5000 and not shell.recv_ready():
                            time.sleep(1)
                            if not shell.recv_ready():
                                break
                except socket.error as e:
                    log(f"⚠ Connection issue while receiving: {e}")
                    # Return what we have so far
                return output
            
            # Wait for initial CLI prompt and read it
            time.sleep(3)  # Wait for DNOS CLI to load
            
            # Read and log initial CLI output
            initial_output = ""
            try:
                while shell.recv_ready():
                    initial_output += shell.recv(65535).decode('utf-8', errors='ignore')
                    time.sleep(0.2)
            except:
                pass
            
            if initial_output:
                # Check for auth failure or error messages
                if 'denied' in initial_output.lower() or 'invalid' in initial_output.lower():
                    log(f"✗ Authentication may have failed: {initial_output[:200]}")
                else:
                    log(f"📝 CLI ready ({len(initial_output)} bytes initial output)")
            else:
                log("📝 CLI ready (no initial output)")
            
            # Verify channel is still active
            if not shell.get_transport() or not shell.get_transport().is_active():
                log("✗ SSH transport closed unexpectedly")
                raise Exception(f"SSH channel to {serial} closed unexpectedly after CLI load")
            
            log("📋 Getting interface list...")
            # Send a newline first to ensure we have a prompt
            safe_send("\n")
            time.sleep(1)
            
            # NOTE: Don't send "exit" here - at the base prompt it logs out!
            # Just go directly to getting interfaces
            safe_send("show interfaces | no-more\n")
            time.sleep(5)  # Wait for interface table output
            
            output = safe_recv(12)
            
            log(f"📊 Raw output length: {len(output)} chars")
            
            # Check for cancellation
            if is_cancelled():
                log("⚠ Cancelled by user")
                client.close()
                return {'success': False, 'error': 'Cancelled by user'}
            
            # Parse ONLY physical NIF interfaces (no sub-interfaces with dots, no loopbacks, no management)
            # Match patterns:
            # - Standard: ge400-0/0/1, ge100-0/0/12, hu0-0/0/1, ce0-0/0/0, qsfp0-0/0/0
            # - Cluster NCP NIF: ge100-0/0/0, ge400-1/0/0 (nodeId is 0 or 1 for NCP-A/NCP-B)
            # Exclude: lo0, mgmt0, *.1 (sub-interfaces), bundle-*, lag-*, ctrl-*, ice*, fab*
            physical_interface_pattern = re.compile(
                r'\b((?:ge|hu|ce|qsfp)\d*-\d+/\d+/\d+)\b',
                re.MULTILINE
            )
            
            # Find all matches and filter out sub-interfaces (containing dots)
            all_matches = physical_interface_pattern.findall(output)
            physical_interfaces = [iface for iface in all_matches if '.' not in iface]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_interfaces = []
            for iface in physical_interfaces:
                if iface.lower() not in seen:
                    seen.add(iface.lower())
                    unique_interfaces.append(iface)
            
            # Detect if this is a cluster (DNAAS) device by checking for NCP patterns
            # Cluster devices have BOTH ge100-* and ge400-* interfaces (NCP + NCF)
            # PE devices typically have only ge400-* interfaces
            has_ge100 = any(iface.startswith('ge100-') for iface in unique_interfaces)
            has_ge400 = any(iface.startswith('ge400-') for iface in unique_interfaces)
            is_cluster = has_ge100 and has_ge400  # True cluster has BOTH types
            
            if is_cluster:
                log(f"📊 Detected CLUSTER device - Found {len(unique_interfaces)} NCP NIF interfaces")
                log(f"   ℹ️  Cluster has both ge100-* ({sum(1 for i in unique_interfaces if i.startswith('ge100-'))}) and ge400-* ({sum(1 for i in unique_interfaces if i.startswith('ge400-'))}) interfaces")
            else:
                log(f"📊 Found {len(unique_interfaces)} physical interfaces (PE/standalone device)")
                if has_ge400:
                    log(f"   ℹ️  Will configure speed 100 + fec none on {sum(1 for i in unique_interfaces if i.startswith('ge400-'))} ge400-* interfaces")
            
            # If no interfaces found, show what we got
            if not unique_interfaces:
                # Try to extract any interface-like patterns for debugging
                any_iface_pattern = re.compile(r'\b(\S*\d+[-/]\d+[/\d]*)\b')
                any_matches = any_iface_pattern.findall(output)[:10]
                log(f"⚠ No ge/hu/ce/qsfp/eth interfaces found. Sample patterns: {any_matches[:5]}")
            
            # ================================================================
            # CHECK IF LLDP IS ALREADY CONFIGURED ON ALL INTERFACES
            # ================================================================
            if unique_interfaces:
                log("🔍 Checking existing LLDP configuration...")
                # Use 'show configuration lldp' which shows current LLDP config state
                safe_send("show configuration protocols lldp | no-more\n")
                time.sleep(3)
                lldp_config_output = safe_recv(10)
                
                # Parse interfaces that already have LLDP configured
                # DNOS format: "interface ge400-0/0/1" under protocols lldp
                lldp_configured_pattern = re.compile(r'interface\s+((?:ge|hu|ce|qsfp)\d*-\d+/\d+/\d+)', re.MULTILINE)
                already_configured = set(lldp_configured_pattern.findall(lldp_config_output))
                
                # Check if admin-state is enabled globally
                lldp_admin_enabled = 'admin-state enabled' in lldp_config_output.lower()
                
                # Compare: which interfaces need LLDP configuration?
                interfaces_needing_lldp = [iface for iface in unique_interfaces if iface not in already_configured]
                
                if lldp_admin_enabled and len(interfaces_needing_lldp) == 0:
                    # LLDP is already fully configured!
                    log(f"✅ LLDP is already configured on all {len(unique_interfaces)} interfaces!")
                    log(f"   Admin-state: enabled")
                    log(f"   Interfaces with LLDP: {len(already_configured)}")
                    
                    # Still check admin-state on physical interfaces
                    log("[INFO] Verifying interface admin-state...")
                    safe_send("show interfaces brief | no-more\n")
                    time.sleep(3)
                    iface_status_output = safe_recv(8)
                    
                    # Count interfaces that are admin-down
                    admin_down_count = 0
                    for iface in unique_interfaces:
                        # Look for interface line with "down" or "admin-down" status
                        iface_pattern = re.compile(rf'{re.escape(iface)}\s+.*?(?:admin-down|down)', re.IGNORECASE)
                        if iface_pattern.search(iface_status_output):
                            admin_down_count += 1
                    
                    if admin_down_count == 0:
                        log(f"✅ All {len(unique_interfaces)} interfaces have admin-state enabled!")
                        client.close()
                        return {
                            'success': True,
                            'message': f'LLDP already configured on all {len(unique_interfaces)} interfaces',
                            'interfaces_enabled': len(unique_interfaces),
                            'interfaces': unique_interfaces[:20],
                            'already_configured': True
                        }
                    else:
                        log(f"⚠ LLDP configured but {admin_down_count} interfaces are admin-down")
                        log(f"   Will enable admin-state on those interfaces...")
                        # Continue to enable admin-state only
                        interfaces_needing_lldp = []  # LLDP is done, just need admin-state
                
                elif len(already_configured) > 0:
                    log(f"📊 LLDP partially configured: {len(already_configured)}/{len(unique_interfaces)} interfaces")
                    log(f"   Need to configure: {len(interfaces_needing_lldp)} more interfaces")
                else:
                    log(f"📊 LLDP not configured - will configure all {len(unique_interfaces)} interfaces")
            
            interfaces_enabled = 0
            
            if unique_interfaces:
                log("📝 Entering configuration mode...")
                safe_send("configure\n")
                time.sleep(1)
                
                # Step 1: Enable LLDP globally (if not already enabled)
                log("🔧 Enabling LLDP globally...")
                safe_send("protocols lldp\n")
                time.sleep(0.5)
                safe_send("admin-state enabled\n")  # DNOS uses 'enabled' not 'enable'
                time.sleep(0.5)
                
                # Step 2: Configure LLDP on all interfaces using batch mode
                # Sends multi-line config blocks instead of one-at-a-time with per-line sleeps
                total = len(unique_interfaces)
                log(f"[FAST] Configuring LLDP on {total} interfaces (batch mode)...")
                
                lldp_lines = []
                for iface in unique_interfaces:
                    lldp_lines.extend([f"interface {iface}", "!"])
                lldp_lines.append("!")  # Exit protocols lldp -> cfg-protocols
                lldp_lines.append("!")  # Exit protocols -> cfg
                
                LLDP_BATCH = 30
                for i in range(0, len(lldp_lines), LLDP_BATCH):
                    if is_cancelled():
                        log("[WARN] Cancelled by user")
                        safe_send("!\n!\n!\nexit\n")
                        client.close()
                        return {'success': False, 'error': 'Cancelled by user'}
                    batch = "\n".join(lldp_lines[i:i+LLDP_BATCH]) + "\n"
                    safe_send(batch)
                    time.sleep(0.3)
                
                safe_recv(2)
                log(f"[OK] LLDP configured on all {total} interfaces")
                
                # Step 3: Enable admin-state on all interfaces using batch mode
                ge400_interfaces = [iface for iface in unique_interfaces if iface.startswith('ge400-')]
                has_400g = len(ge400_interfaces) > 0
                
                if has_400g:
                    log(f"[INFO] Detected {len(ge400_interfaces)} 400G interfaces - will set FEC none + speed 100")
                
                log(f"[FAST] Enabling admin-state on {total} interfaces (batch mode)...")
                
                admin_lines = ["interfaces"]
                ge400_count = 0
                for iface in unique_interfaces:
                    admin_lines.append(iface)
                    admin_lines.append("admin-state enabled")
                    if iface.startswith('ge400-') and not is_cluster:
                        admin_lines.append("fec none")
                        admin_lines.append("speed 100")
                        ge400_count += 1
                    admin_lines.append("!")
                admin_lines.append("!")  # Exit interfaces hierarchy
                
                ADMIN_BATCH = 20
                for i in range(0, len(admin_lines), ADMIN_BATCH):
                    if is_cancelled():
                        log("[WARN] Cancelled by user")
                        safe_send("!\n!\nexit\n")
                        client.close()
                        return {'success': False, 'error': 'Cancelled by user'}
                    batch = "\n".join(admin_lines[i:i+ADMIN_BATCH]) + "\n"
                    safe_send(batch)
                    time.sleep(0.3)
                
                interfaces_enabled = len(unique_interfaces)
                safe_recv(2)
                if ge400_count > 0:
                    log(f"[OK] Admin-state enabled on {total} interfaces ({ge400_count}x 400G: speed 100 + fec none)")
                else:
                    log(f"[OK] Admin-state enabled on {total} interfaces")
                
                # Commit changes with verification
                log("[INFO] Committing configuration...")
                safe_send("commit\n")
                commit_wait = min(15, max(8, len(unique_interfaces) // 5))
                log(f"  Commit wait: {commit_wait}s...")
                time.sleep(commit_wait)
                
                # Read commit output to verify success
                commit_output = safe_recv(10)  # Increased from 5 to 10 seconds
                
                # Log the full commit output for debugging
                if commit_output:
                    log(f"📄 Commit output ({len(commit_output)} chars):")
                    for line in commit_output.splitlines()[:20]:  # Show first 20 lines
                        if line.strip():
                            log(f"   {line[:120]}")  # Truncate long lines
                
                if 'error' in commit_output.lower() or 'failed' in commit_output.lower() or 'invalid' in commit_output.lower():
                    log(f"⚠️  WARNING: Commit may have issues!")
                    log(f"⚠️  Check output above for errors")
                elif 'commit complete' in commit_output.lower():
                    log("✅ Configuration committed successfully!")
                elif not commit_output.strip():
                    log("✅ Configuration committed (no output = success in DNOS)")
                else:
                    log(f"✅ Configuration committed (output: {len(commit_output)} bytes)")
                
                # Verify speed/fec was applied (if PE device with ge400-*)
                if has_400g and not is_cluster:
                    log("🔍 Verifying speed/fec configuration on first ge400-* interface...")
                    test_iface = ge400_interfaces[0]
                    safe_send(f"show config interfaces {test_iface}\n")
                    time.sleep(2)
                    verify_output = safe_recv(5)
                    
                    if 'speed 100' in verify_output and 'fec none' in verify_output:
                        log(f"✅ Verified: speed 100 + fec none applied on {test_iface}")
                    else:
                        log(f"⚠️  WARNING: Could not verify speed/fec on {test_iface}")
                        log(f"   Output: {verify_output[:300]}")
                
                safe_send("exit\n")
                time.sleep(0.5)
                
                # Wait for LLDP hellos -- LLDP PDUs are sent immediately on enable,
                # neighbors typically appear within 5-10s
                log("[INFO] Waiting for LLDP neighbor discovery (10 seconds)...")
                for wait_sec in range(10):
                    if is_cancelled():
                        log("[WARN] Cancelled during LLDP wait")
                        client.close()
                        return {'success': False, 'error': 'Cancelled by user'}
                    time.sleep(1)
                    if (wait_sec + 1) % 5 == 0:
                        log(f"  {wait_sec + 1}/10 seconds elapsed...")
                
                log("[OK] LLDP hello wait completed!")
            else:
                # Even if no interfaces found, still enable LLDP globally
                log("⚠ No physical interfaces detected - enabling LLDP globally anyway...")
                safe_send("configure\n")
                time.sleep(1)
                safe_send("protocols lldp\n")
                time.sleep(0.5)
                safe_send("admin-state enabled\n")  # DNOS uses 'enabled' not 'enable'
                time.sleep(0.5)
                safe_send("!\n")  # Exit protocols lldp
                time.sleep(0.5)
                safe_send("commit\n")
                time.sleep(3)
                safe_send("exit\n")
                time.sleep(0.5)
                log("✓ LLDP enabled globally (interfaces may need manual configuration)")
            
            client.close()
            
            # Build success message
            ge400_count = len([iface for iface in unique_interfaces if iface.startswith('ge400-')])
            if ge400_count > 0:
                log(f"✅ LLDP enabled on {interfaces_enabled} interfaces! ({ge400_count}x 400G set to 100g speed)")
                msg = f'LLDP + admin-state on {interfaces_enabled} interfaces, {ge400_count}x 400G→100g for DNAAS'
            else:
                log(f"✅ LLDP enabled on {interfaces_enabled} interfaces!")
                msg = f'LLDP enabled globally + admin-state enabled on {interfaces_enabled} physical interfaces'
            
            return {
                'success': True,
                'message': msg,
                'interfaces_enabled': interfaces_enabled,
                'interfaces': unique_interfaces[:20]  # Return first 20 for display
            }
            
        except Exception as e:
            error_msg = f"✗ Error: {str(e)}"
            log(error_msg)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _resolve_serial_to_host(self, serial: str) -> str:
        """Resolve a serial/hostname to a connectable IP or hostname.
        Tries: DNS with suffixes -> Scaler DB (fuzzy match) -> uppercase serial.
        """
        import socket
        from difflib import SequenceMatcher
        
        # Already an IP?
        import re
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', serial):
            return serial
        
        # Try DNS resolution with domain suffixes
        domain_suffixes = ['', '.dev.drivenets.net', '.drivenets.net', '.local']
        for suffix in domain_suffixes:
            try_host = serial + suffix
            try:
                resolved_ip = socket.gethostbyname(try_host)
                print(f"[Resolve] {serial} -> {resolved_ip} (DNS: {try_host})")
                return resolved_ip
            except socket.gaierror:
                continue
        
        # Try uppercase (DNOS serials resolve in uppercase)
        if serial != serial.upper():
            try:
                resolved_ip = socket.gethostbyname(serial.upper())
                print(f"[Resolve] {serial} -> {resolved_ip} (DNS uppercase)")
                return resolved_ip
            except socket.gaierror:
                pass
        
        # Fuzzy match against Scaler DB serials
        db_configs = Path('/home/dn/SCALER/db/configs')
        if db_configs.exists():
            input_norm = serial.upper().replace('L', '1')
            for device_dir in db_configs.iterdir():
                if device_dir.is_dir():
                    op_file = device_dir / 'operational.json'
                    if op_file.exists():
                        try:
                            with open(op_file, 'r') as f:
                                op_data = json.load(f)
                            dev_serial = (op_data.get('serial_number', '') or '').upper()
                            dev_ip = op_data.get('connection_ip', '') or ''
                            dev_hostname = op_data.get('hostname', device_dir.name) or device_dir.name
                            
                            if not dev_serial:
                                continue
                            
                            # Fuzzy match (handles l/1 confusion, typos)
                            dev_norm = dev_serial.replace('L', '1')
                            ratio = SequenceMatcher(None, input_norm, dev_norm).ratio()
                            exact = (serial.lower() in dev_hostname.lower() or
                                     dev_hostname.lower() in serial.lower())
                            
                            if ratio >= 0.75 or exact:
                                if dev_ip:
                                    print(f"[Resolve] {serial} -> {dev_ip} (Scaler DB)")
                                    return dev_ip
                                # Try the actual serial (may resolve via DNS)
                                try:
                                    resolved_ip = socket.gethostbyname(dev_serial)
                                    print(f"[Resolve] {serial} -> {resolved_ip} (DNS via DB serial {dev_serial})")
                                    return resolved_ip
                                except socket.gaierror:
                                    pass
                                print(f"[Resolve] {serial} -> {dev_serial} (Scaler DB serial, no IP)")
                                return dev_serial
                        except Exception:
                            pass
        
        return serial

    def _fetch_lldp_neighbors(self, serial: str) -> dict:
        """
        SSH to device, run 'show lldp neighbors | no-more', parse and return neighbors.
        Returns { lldp_neighbors: [...], error?: str }.
        """
        import paramiko
        import socket
        import time
        serial = (serial or '').strip()
        if not serial:
            return {'lldp_neighbors': [], 'error': 'serial is required'}
        connect_host = self._resolve_serial_to_host(serial)
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                connect_host,
                username='dnroot',
                password='dnroot',
                timeout=30,
                look_for_keys=False,
                allow_agent=False
            )
        except Exception as e:
            return {'lldp_neighbors': [], 'error': str(e)}
        try:
            shell = client.invoke_shell(width=250, height=50)
            shell.settimeout(30)
            time.sleep(4)
            while shell.recv_ready():
                shell.recv(65535)
                time.sleep(0.2)
            # Try "show lldp neighbor" (singular) first; some DNOS use "neighbors" (plural)
            for cmd in ("show lldp neighbor | no-more\r\n", "show lldp neighbors | no-more\r\n"):
                shell.send(cmd)
                time.sleep(3)
                output = ""
                end_time = time.time() + 15
                while time.time() < end_time:
                    if shell.recv_ready():
                        output += shell.recv(65535).decode('utf-8', errors='replace')
                        if '#' in output or '>' in output:
                            time.sleep(0.5)
                            if shell.recv_ready():
                                output += shell.recv(65535).decode('utf-8', errors='replace')
                            break
                    time.sleep(0.3)
                raw_clean = strip_ansi(output)
                neighbors = _parse_lldp_output(raw_clean)
                # If we got rows or output looks like a table, we're done
                if neighbors or ('interface' in raw_clean.lower() and 'invalid' not in raw_clean.lower()):
                    client.close()
                    return {'lldp_neighbors': neighbors, 'raw_output': raw_clean}
                # If first command looked like an error, try plural
                if 'invalid' in raw_clean.lower() or 'unknown' in raw_clean.lower() or 'error' in raw_clean.lower():
                    time.sleep(1)
                    while shell.recv_ready():
                        shell.recv(65535)
                    time.sleep(0.5)
                    continue
                # Empty output - return what we have
                client.close()
                return {'lldp_neighbors': neighbors, 'raw_output': raw_clean}
            client.close()
            return {'lldp_neighbors': [], 'raw_output': raw_clean}
        except Exception as e:
            try:
                client.close()
            except Exception:
                pass
            return {'lldp_neighbors': [], 'error': str(e)}
    
    def _save_lldp_to_cache(self, serial: str, lldp_neighbors: list):
        """
        Save LLDP neighbors to scaler-monitor cache (operational.json).
        Uses bidirectional matching to find the right device folder.
        """
        from datetime import datetime
        db_configs = Path('/home/dn/SCALER/db/configs')
        if not db_configs.exists():
            print(f"Cache dir not found: {db_configs}")
            return False
        
        search_term_lower = serial.lower()
        
        # Find matching device folder
        for device_dir in db_configs.iterdir():
            if device_dir.is_dir():
                dev_hostname = device_dir.name.lower()
                # Bidirectional match
                if dev_hostname == search_term_lower or \
                   search_term_lower in dev_hostname or \
                   dev_hostname in search_term_lower:
                    op_file = device_dir / 'operational.json'
                    try:
                        op_data = {}
                        if op_file.exists():
                            with open(op_file, 'r') as f:
                                op_data = json.load(f)
                        
                        # Update LLDP data
                        op_data['lldp_neighbors'] = lldp_neighbors
                        op_data['lldp_neighbor_count'] = len(lldp_neighbors)
                        op_data['lldp_last_updated'] = datetime.now().isoformat()
                        
                        with open(op_file, 'w') as f:
                            json.dump(op_data, f, indent=2)
                        
                        print(f"✓ Saved {len(lldp_neighbors)} LLDP neighbors to cache: {op_file}")
                        return True
                    except Exception as e:
                        print(f"Failed to save cache: {e}")
                        return False
        
        print(f"No matching device folder found for {serial}")
        return False
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/discovery/status':
            # Get status of a job
            params = parse_qs(parsed.query)
            job_id = params.get('job_id', [None])[0]
            
            if job_id and job_id in jobs:
                job = jobs[job_id]
                self._send_json({
                    'job_id': job_id,
                    'status': job['status'],
                    'progress': job['progress'],
                    'output_lines': job['output_lines'][-20:],  # Last 20 lines
                    'result_file': job.get('result_file'),
                    'error': job.get('error')
                })
            else:
                self._send_json({'error': 'Job not found'}, 404)
        
        elif parsed.path == '/api/multi-bd/status':
            # Get status of a multi-BD job
            params = parse_qs(parsed.query)
            job_id = params.get('job_id', [None])[0]
            
            if job_id and job_id in jobs:
                job = jobs[job_id]
                # Strip ANSI codes for clean text matching in UI
                clean_lines = [strip_ansi(line) for line in job['output_lines']]
                self._send_json({
                    'job_id': job_id,
                    'status': job['status'],
                    'progress': job['progress'],
                    'message': clean_lines[-1] if clean_lines else '',
                    'output_lines': clean_lines,  # Include all lines for LLDP detection
                    'bd_count': job.get('bd_count', 0),
                    'result_file': job.get('result_file'),
                    'error': job.get('error')
                })
            else:
                self._send_json({'error': 'Job not found'}, 404)
        
        elif parsed.path == '/api/enable-lldp/status':
            # Get status of an LLDP enable job (for real-time feedback)
            params = parse_qs(parsed.query)
            job_id = params.get('job_id', [None])[0]
            
            if job_id and job_id in jobs:
                job = jobs[job_id]
                self._send_json({
                    'job_id': job_id,
                    'status': job['status'],
                    'progress': job['progress'],
                    'output_lines': job['output_lines'],  # Send all lines for detailed feedback
                    'interfaces_enabled': job.get('interfaces_enabled', 0),
                    'interfaces': job.get('interfaces', []),
                    'already_configured': job.get('already_configured', False),
                    'error': job.get('error')
                })
            else:
                self._send_json({'error': 'Job not found'}, 404)
        
        elif parsed.path == '/api/enable-lldp/cancel':
            # Cancel an LLDP enable job and close SSH session
            params = parse_qs(parsed.query)
            job_id = params.get('job_id', [None])[0]
            
            if job_id and job_id in jobs:
                job = jobs[job_id]
                job['cancelled'] = True
                job['status'] = 'cancelled'
                job['error'] = 'Cancelled by user'
                job['output_lines'].append('⚠ LLDP enable cancelled by user')
                
                # Close SSH client if stored - be aggressive
                if '_ssh_client' in job:
                    try:
                        ssh_client = job['_ssh_client']
                        # Close the transport first to interrupt any pending I/O
                        if ssh_client.get_transport():
                            ssh_client.get_transport().close()
                        ssh_client.close()
                        job['output_lines'].append('✓ SSH session closed')
                    except Exception as e:
                        job['output_lines'].append(f'⚠ SSH close error: {e}')
                
                self._send_json({'job_id': job_id, 'status': 'cancelled', 'message': 'LLDP enable cancelled'})
            else:
                self._send_json({'error': 'Job not found'}, 404)
        
        elif parsed.path.startswith('/api/multi-bd/file/'):
            # Serve a multi-BD result file by name
            filename = parsed.path.replace('/api/multi-bd/file/', '')
            # Security: only allow multi_bd_*.json or dnaas_*.json files
            if (filename.startswith('multi_bd_') or filename.startswith('dnaas_')) and filename.endswith('.json'):
                filepath = OUTPUT_DIR / filename
                if filepath.exists() and filepath.is_file():
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                        self._send_json(data)
                    except Exception as e:
                        self._send_json({'error': f'Failed to read file: {str(e)}'}, 500)
                else:
                    self._send_json({'error': 'File not found'}, 404)
            else:
                self._send_json({'error': 'Invalid filename'}, 400)
        
        elif parsed.path.startswith('/api/device/') and '/lldp' in parsed.path:
            # GET endpoint: /api/device/<serial>/lldp - fetch LLDP from scaler-monitor cache
            # Extract serial from path: /api/device/SERIAL/lldp
            path_parts = parsed.path.split('/')
            # path_parts = ['', 'api', 'device', 'SERIAL', 'lldp']
            if len(path_parts) >= 5:
                serial = path_parts[3]  # URL-encoded serial
                from urllib.parse import unquote
                serial = unquote(serial)
                
                # Priority: NetworkMapper (freshest) > Scaler DB > device_inventory > SSH
                found_device = None
                neighbors = []
                raw_output = ""
                search_term_lower = serial.lower()
                lldp_source = None
                
                # 1. Try NetworkMapper MCP first (most recently updated DB, 15s timeout)
                try:
                    import concurrent.futures
                    nm = _get_mcp_client()
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        future = pool.submit(nm.get_device_lldp, serial)
                        nm_neighbors = future.result(timeout=15)
                    if nm_neighbors:
                        found_device = serial
                        lldp_source = 'network-mapper'
                        for n in nm_neighbors:
                            neighbors.append({
                                'interface': n.local_interface,
                                'neighbor': n.neighbor_name,
                                'remote_port': n.neighbor_interface
                            })
                        print(f"[LLDP] Found {len(neighbors)} neighbors via NetworkMapper for {serial}")
                except concurrent.futures.TimeoutError:
                    print(f"[LLDP] NetworkMapper timed out (15s) for {serial}, trying fallbacks...")
                except Exception as e:
                    print(f"[LLDP] NetworkMapper lookup skipped: {e}")
                
                # 2. Fallback: SCALER operational.json
                if not neighbors:
                    db_configs = Path('/home/dn/SCALER/db/configs')
                    if db_configs.exists():
                        for device_dir in db_configs.iterdir():
                            if device_dir.is_dir():
                                op_file = device_dir / 'operational.json'
                                if op_file.exists():
                                    try:
                                        with open(op_file, 'r') as f:
                                            op_data = json.load(f)
                                        dev_hostname = op_data.get('hostname', device_dir.name)
                                        dev_serial = op_data.get('serial_number', '')
                                        dev_connection_ip = op_data.get('connection_ip', '')
                                        
                                        if dev_hostname.lower() == search_term_lower or \
                                           search_term_lower in dev_hostname.lower() or \
                                           dev_hostname.lower() in search_term_lower or \
                                           (dev_serial and dev_serial.lower() == search_term_lower) or \
                                           (dev_connection_ip and dev_connection_ip == serial):
                                            found_device = dev_hostname
                                            lldp_source = 'scaler-db'
                                            lldp_data = op_data.get('lldp_neighbors', [])
                                            raw_output = op_data.get('lldp_raw', '')
                                            for n in lldp_data:
                                                neighbors.append({
                                                    'interface': n.get('local_interface') or n.get('interface', ''),
                                                    'neighbor': n.get('neighbor_device') or n.get('neighbor', ''),
                                                    'remote_port': n.get('neighbor_port') or n.get('remote_port', '')
                                                })
                                            break
                                    except Exception as e:
                                        print(f"Error reading {op_file}: {e}")
                
                # 3. Fallback: device_inventory.json
                if not neighbors:
                    inventory_file = Path('/home/dn/CURSOR/device_inventory.json')
                    if inventory_file.exists():
                        try:
                            with open(inventory_file, 'r') as f:
                                inventory = json.load(f)
                            devices = inventory.get('devices', {})
                            for device_key, device_data in devices.items():
                                dev_hostname = device_data.get('hostname', device_key)
                                if dev_hostname.lower() == search_term_lower or \
                                   search_term_lower in dev_hostname.lower() or \
                                   dev_hostname.lower() in search_term_lower:
                                    found_device = dev_hostname
                                    lldp_source = 'device-inventory'
                                    for n in device_data.get('lldp_neighbors', []):
                                        neighbors.append({
                                            'interface': n.get('local_interface') or n.get('interface', ''),
                                            'neighbor': n.get('neighbor_device') or n.get('neighbor', ''),
                                            'remote_port': n.get('neighbor_port') or n.get('remote_port', '')
                                        })
                                    break
                        except Exception as e:
                            print(f"Error reading device_inventory.json: {e}")
                
                # If no cached data found, try live SSH and SAVE to cache
                if not neighbors and serial:
                    print(f"No cached LLDP for {serial}, trying live SSH + cache update...")
                    try:
                        live_result = self._fetch_lldp_neighbors(serial)
                        if live_result.get('lldp_neighbors'):
                            lldp_list = live_result['lldp_neighbors']
                            
                            # Save to scaler cache (operational.json)
                            self._save_lldp_to_cache(serial, lldp_list)
                            
                            for n in lldp_list:
                                neighbors.append({
                                    'interface': n.get('local_interface') or n.get('interface', ''),
                                    'neighbor': n.get('neighbor_device') or n.get('neighbor', ''),
                                    'remote_port': n.get('neighbor_port') or n.get('remote_port', '')
                                })
                            raw_output = live_result.get('raw_output', '')
                            found_device = serial
                            self._send_json({
                                'neighbors': neighbors,
                                'raw_output': raw_output,
                                'device': found_device,
                                'cached': False,
                                'live': True,
                                'cache_updated': True
                            })
                            return
                    except Exception as e:
                        print(f"Live SSH fallback failed: {e}")
                
                self._send_json({
                    'neighbors': neighbors,
                    'raw_output': raw_output,
                    'device': found_device or serial,
                    'cached': True,
                    'source': lldp_source or 'unknown'
                })
            else:
                self._send_json({'error': 'Invalid path format'}, 400)
        
        elif parsed.path == '/api/discovery/list':
            # List output files (both dnaas_path and multi_bd)
            files = []
            if OUTPUT_DIR.exists():
                # Get both dnaas_path and multi_bd files
                dnaas_files = list(OUTPUT_DIR.glob('dnaas_path_*.json'))
                multi_bd_files = list(OUTPUT_DIR.glob('multi_bd_*.json'))
                all_files = dnaas_files + multi_bd_files
                # Sort by modification time (newest first) and take top 20
                for f in sorted(all_files, key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
                    files.append({
                        'name': f.name,
                        'path': str(f),
                        'size': f.stat().st_size,
                        'modified': f.stat().st_mtime
                    })
            self._send_json({'files': files})
        
        elif parsed.path.startswith('/api/discovery/file/'):
            # Serve a result file by name
            filename = parsed.path.replace('/api/discovery/file/', '')
            # Security: allow both dnaas_path_*.json and multi_bd_*.json files
            valid_prefix = filename.startswith('dnaas_path_') or filename.startswith('multi_bd_') or filename.startswith('dnaas_')
            if valid_prefix and filename.endswith('.json'):
                filepath = OUTPUT_DIR / filename
                if filepath.exists() and filepath.is_file():
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                        self._send_json(data)
                    except Exception as e:
                        self._send_json({'error': f'Failed to read file: {str(e)}'}, 500)
                else:
                    self._send_json({'error': 'File not found'}, 404)
            else:
                self._send_json({'error': 'Invalid filename'}, 400)
        
        # ================================================================
        # Network Mapper — status endpoint
        # ================================================================
        elif parsed.path == '/api/network-mapper/status':
            params = parse_qs(parsed.query)
            jid = params.get('job_id', [None])[0]
            if not jid or jid not in nm_jobs:
                self._send_json({'error': 'Job not found'}, 404)
                return
            with nm_job_lock:
                job = nm_jobs[jid]
                self._send_json({
                    'status': job['status'],
                    'progress': job['progress'],
                    'devices': job.get('devices', {}),
                    'links': job.get('links', []),
                    'errors': job.get('errors', []),
                    'log': job.get('log', [])[-50:]  # last 50 log lines
                })

        else:
            self._send_json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        global job_counter, nm_job_counter
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/discovery/start':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            
            serial1 = (data.get('serial1') or '').strip()
            serial2 = (data.get('serial2') or '').strip()
            
            if not serial1:
                self._send_json({'error': 'serial1 is required'}, 400)
                return
            
            # Create job
            _cleanup_old_discovery_jobs()
            with job_lock:
                job_counter += 1
                job_id = f"job_{job_counter}"
                jobs[job_id] = {
                    'status': 'starting',
                    'progress': 0,
                    'output_lines': [],
                    'result_file': None,
                    'error': None,
                    'created_at': time.time()
                }
            
            # Start discovery in background thread
            def run_discovery():
                job = jobs[job_id]
                job['status'] = 'running'
                job['progress'] = 10
                job['output_lines'].append(f"Starting hybrid discovery for {serial1}...")
                
                # Use NEW hybrid script: cached PE data + live DNAAS SSH only
                cmd = ['python3', str(DISCOVERY_SCRIPT), serial1]
                if serial2:
                    cmd.append(serial2)
                    job['output_lines'].append(f"Second device: {serial2}")
                job['output_lines'].append("Using hybrid mode: cached PE + minimal DNAAS SSH...")
                
                try:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )
                    
                    # Store process handle for cancellation
                    job_processes[job_id] = process
                    job['progress'] = 20
                    
                    for line in iter(process.stdout.readline, ''):
                        line = line.strip()
                        if line:
                            job['output_lines'].append(line)
                            # Update progress based on output
                            if 'Connecting' in line:
                                job['progress'] = min(job['progress'] + 10, 80)
                            elif 'LLDP' in line:
                                job['progress'] = min(job['progress'] + 5, 85)
                            elif 'saved' in line.lower():
                                job['progress'] = 90
                    
                    process.wait()
                    
                    if process.returncode == 0:
                        job['status'] = 'completed'
                        job['progress'] = 100
                        # Find the latest output file
                        latest = max(OUTPUT_DIR.glob('dnaas_path_*.json'), key=lambda f: f.stat().st_mtime, default=None)
                        if latest:
                            # Return web-accessible URL instead of filesystem path
                            job['result_file'] = f"/api/discovery/file/{latest.name}"
                            job['output_lines'].append(f"✓ Output saved: {latest.name}")
                    else:
                        job['status'] = 'failed'
                        # Check output lines for specific error messages
                        error_msg = f"Process exited with code {process.returncode}"
                        for line in job['output_lines'][-10:]:
                            if 'Failed to connect' in line or 'Connection failed' in line:
                                error_msg = f"Connection failed to device"
                                break
                            elif 'No devices discovered' in line:
                                error_msg = "No devices discovered - connection may have failed"
                                break
                        job['error'] = error_msg
                        job['output_lines'].append(f"✗ Discovery failed: {error_msg}")
                
                except Exception as e:
                    job['status'] = 'failed'
                    job['error'] = str(e)
                    job['output_lines'].append(f"✗ Error: {e}")
                finally:
                    # Clean up process handle
                    if job_id in job_processes:
                        del job_processes[job_id]
            
            thread = threading.Thread(target=run_discovery, daemon=True)
            thread.start()
            
            self._send_json({'job_id': job_id, 'status': 'started'})
        
        elif parsed.path == '/api/discovery/cancel':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            
            job_id = data.get('job_id', '').strip()
            
            if not job_id:
                self._send_json({'error': 'job_id is required'}, 400)
                return
            
            if job_id not in jobs:
                self._send_json({'error': 'Job not found'}, 404)
                return
            
            job = jobs[job_id]
            
            # Try to terminate the process
            if job_id in job_processes:
                try:
                    process = job_processes[job_id]
                    process.terminate()
                    process.wait(timeout=2)
                except:
                    try:
                        process.kill()
                    except:
                        pass
                finally:
                    if job_id in job_processes:
                        del job_processes[job_id]
            
            job['status'] = 'cancelled'
            job['error'] = 'Cancelled by user'
            job['output_lines'].append('⚠ Discovery cancelled by user')
            
            self._send_json({'job_id': job_id, 'status': 'cancelled', 'message': 'Discovery cancelled'})
        
        elif parsed.path == '/api/multi-bd/start':
            # Start Multi-BD discovery
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            
            serial = (data.get('serial') or '').strip()
            
            if not serial:
                self._send_json({'error': 'serial is required'}, 400)
                return
            
            # Create job
            _cleanup_old_discovery_jobs()
            with job_lock:
                job_counter += 1
                job_id = f"multibd_{job_counter}"
                jobs[job_id] = {
                    'status': 'starting',
                    'progress': 0,
                    'output_lines': [],
                    'result_file': None,
                    'error': None,
                    'bd_count': 0,
                    'created_at': time.time()
                }
            
            # Start multi-BD discovery in background thread
            def run_multi_bd_discovery():
                job = jobs[job_id]
                job['status'] = 'running'
                job['progress'] = 10
                job['output_lines'].append(f"Starting Multi-BD discovery for {serial}...")
                
                # Use --multi-bd flag for multi-BD discovery (MUST come before positional args)
                cmd = ['python3', str(DISCOVERY_SCRIPT), '--multi-bd', serial]
                job['output_lines'].append("Discovering ALL Bridge Domains...")
                
                try:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )
                    
                    job_processes[job_id] = process
                    job['progress'] = 20
                    
                    for line in iter(process.stdout.readline, ''):
                        line = line.strip()
                        if line:
                            job['output_lines'].append(line)
                            # Update progress based on output
                            if 'Connecting' in line:
                                job['progress'] = min(job['progress'] + 5, 40)
                            elif 'Bridge Domain' in line or 'BD:' in line:
                                job['progress'] = min(job['progress'] + 5, 60)
                            elif 'LLDP' in line:
                                job['progress'] = min(job['progress'] + 3, 75)
                            elif 'Discovered' in line:
                                # Try to extract BD count
                                import re
                                bd_match = re.search(r'Discovered\s+(\d+)\s+Bridge', line)
                                if bd_match:
                                    job['bd_count'] = int(bd_match.group(1))
                                job['progress'] = 85
                            elif 'saved' in line.lower():
                                job['progress'] = 95
                    
                    process.wait()
                    
                    if process.returncode == 0:
                        job['status'] = 'completed'
                        job['progress'] = 100
                        # Find the latest output file (multi_bd_*.json or dnaas_*.json)
                        multi_bd_files = list(OUTPUT_DIR.glob('multi_bd_*.json'))
                        dnaas_files = list(OUTPUT_DIR.glob('dnaas_path_*.json'))
                        all_files = multi_bd_files + dnaas_files
                        latest = max(all_files, key=lambda f: f.stat().st_mtime, default=None)
                        if latest:
                            job['result_file'] = f"/api/multi-bd/file/{latest.name}"
                            job['output_lines'].append(f"✓ Multi-BD output saved: {latest.name}")
                    else:
                        job['status'] = 'failed'
                        job['error'] = f"Process exited with code {process.returncode}"
                        job['output_lines'].append(f"✗ Multi-BD discovery failed")
                
                except Exception as e:
                    job['status'] = 'failed'
                    job['error'] = str(e)
                    job['output_lines'].append(f"✗ Error: {e}")
                finally:
                    if job_id in job_processes:
                        del job_processes[job_id]
            
            thread = threading.Thread(target=run_multi_bd_discovery, daemon=True)
            thread.start()
            
            self._send_json({'job_id': job_id, 'status': 'started', 'message': 'Multi-BD discovery started'})
        
        elif parsed.path == '/api/multi-bd/cancel':
            # Cancel a Multi-BD discovery job
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            
            job_id = data.get('job_id', '').strip()
            
            if not job_id:
                self._send_json({'error': 'job_id is required'}, 400)
                return
            
            if job_id not in jobs:
                self._send_json({'error': 'Job not found'}, 404)
                return
            
            job = jobs[job_id]
            
            # Try to terminate the process
            if job_id in job_processes:
                try:
                    process = job_processes[job_id]
                    process.terminate()
                    process.wait(timeout=2)
                except:
                    try:
                        process.kill()
                    except:
                        pass
                finally:
                    if job_id in job_processes:
                        del job_processes[job_id]
            
            job['status'] = 'cancelled'
            job['error'] = 'Cancelled by user'
            job['output_lines'].append('⚠ Multi-BD discovery cancelled by user')
            
            self._send_json({'job_id': job_id, 'status': 'cancelled', 'message': 'Multi-BD discovery cancelled'})
        
        elif parsed.path == '/api/enable-lldp':
            # Enable LLDP and admin-state on all interfaces of a device (job-based for real-time updates)
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            
            serial = data.get('serial', '').strip()
            # SSH credentials from device sshConfig (optional, defaults to dnroot/dnroot)
            username = data.get('username', 'dnroot')
            password = data.get('password', 'dnroot')
            skip_host_key = data.get('skipHostKey', False)  # Skip host key verification
            
            if not serial:
                self._send_json({'error': 'serial is required'}, 400)
                return
            
            # Create a job for real-time progress tracking
            _cleanup_old_discovery_jobs()
            with job_lock:
                job_id = f"lldp_{int(time.time() * 1000)}"
                jobs[job_id] = {
                    'id': job_id,
                    'type': 'enable_lldp',
                    'serial': serial,
                    'status': 'running',
                    'progress': 0,
                    'output_lines': [],
                    'started_at': datetime.now().isoformat(),
                    'interfaces_enabled': 0,
                    'created_at': time.time()
                }
            
            # Run in background thread with credentials
            def run_enable_lldp():
                job = jobs[job_id]
                try:
                    result = self._enable_lldp_on_device(serial, job_id, username, password, skip_host_key)
                    job['status'] = 'completed' if result.get('success') else 'failed'
                    job['progress'] = 100
                    job['interfaces_enabled'] = result.get('interfaces_enabled', 0)
                    job['interfaces'] = result.get('interfaces', [])
                    job['already_configured'] = result.get('already_configured', False)
                    if not result.get('success'):
                        job['error'] = result.get('error', 'Unknown error')
                except Exception as e:
                    job['status'] = 'failed'
                    job['error'] = str(e)
                    job['output_lines'].append(f"✗ Error: {str(e)}")
            
            thread = threading.Thread(target=run_enable_lldp, daemon=True)
            thread.start()
            
            self._send_json({'job_id': job_id, 'status': 'started', 'message': f'LLDP enable started for {serial}'})
        
        elif parsed.path == '/api/lldp-neighbors':
            # Fetch LLDP neighbor table from device (show lldp neighbors)
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            serial = (data.get('serial') or '').strip()
            hostname = (data.get('hostname') or '').strip()  # Also accept hostname
            use_cache = data.get('use_cache', True)  # Default: use cached data
            if not serial and not hostname:
                self._send_json({'error': 'serial or hostname is required'}, 400)
                return
            
            # Priority: NetworkMapper (freshest) > device_inventory > Scaler DB > SSH
            cached_device_info = None
            all_devices = []
            search_term = serial or hostname
            search_term_lower = search_term.lower()
            
            if use_cache:
                # FIRST: Try NetworkMapper MCP (most recently updated DB, 15s timeout)
                try:
                    import concurrent.futures
                    nm = _get_mcp_client()
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        future = pool.submit(nm.get_device_lldp, search_term)
                        nm_neighbors = future.result(timeout=15)
                    if nm_neighbors:
                        nm_list = [{
                            'local_interface': n.local_interface,
                            'neighbor_device': n.neighbor_name,
                            'neighbor_port': n.neighbor_interface
                        } for n in nm_neighbors]
                        self._send_json({
                            'lldp_neighbors': nm_list,
                            'cached': True,
                            'source': 'network-mapper',
                            'hostname': search_term
                        })
                        return
                except concurrent.futures.TimeoutError:
                    print(f"[LLDP] NetworkMapper timed out (15s) for {search_term}, trying fallbacks...")
                except Exception as e:
                    print(f"[LLDP] NetworkMapper lookup skipped: {e}")
                
                # SECOND: Check device_inventory.json
                inventory_file = Path('/home/dn/CURSOR/device_inventory.json')
                if inventory_file.exists():
                    try:
                        with open(inventory_file, 'r') as f:
                            inventory = json.load(f)
                        devices = inventory.get('devices', {})
                        
                        for device_key, device_data in devices.items():
                            dev_hostname = device_data.get('hostname', '')
                            dev_serial = device_data.get('serial', '')
                            dev_mgmt_ip = device_data.get('mgmt_ip', '')
                            
                            all_devices.append({
                                'hostname': dev_hostname or device_key,
                                'serial': dev_serial,
                                'ip': dev_mgmt_ip or device_key
                            })
                            
                            if device_key.lower() == search_term_lower or \
                               (dev_hostname and dev_hostname.lower() == search_term_lower) or \
                               (dev_serial and dev_serial.lower() == search_term_lower) or \
                               search_term_lower in device_key.lower() or \
                               (dev_hostname and search_term_lower in dev_hostname.lower()):
                                neighbors = device_data.get('lldp_neighbors', [])
                                last_updated = device_data.get('last_seen', '')
                                if neighbors:
                                    self._send_json({
                                        'lldp_neighbors': neighbors,
                                        'cached': True,
                                        'last_updated': last_updated,
                                        'hostname': dev_hostname or device_key,
                                        'source': 'device-inventory'
                                    })
                                    return
                                break
                    except Exception as e:
                        print(f"Error reading device_inventory.json: {e}")
                
                # THIRD: Check SCALER operational.json files
                db_configs = Path('/home/dn/SCALER/db/configs')
                if db_configs.exists():
                    import re
                    search_clean = re.sub(r'[^a-z0-9]', '', search_term_lower)
                    
                    for device_dir in db_configs.iterdir():
                        if device_dir.is_dir():
                            op_file = device_dir / 'operational.json'
                            if op_file.exists():
                                try:
                                    with open(op_file, 'r') as f:
                                        op_data = json.load(f)
                                    dev_hostname = op_data.get('hostname', device_dir.name)
                                    dev_serial = op_data.get('serial_number', '')
                                    dev_connection_ip = op_data.get('connection_ip', '')
                                    
                                    all_devices.append({
                                        'hostname': dev_hostname,
                                        'serial': dev_serial,
                                        'ip': dev_connection_ip
                                    })
                                    
                                    if dev_hostname.lower() == search_term_lower or \
                                       (dev_serial and dev_serial.lower() == search_term_lower) or \
                                       (dev_connection_ip and dev_connection_ip == search_term):
                                        cached_device_info = (op_data, dev_hostname, dev_connection_ip)
                                        break
                                    
                                    if search_term_lower in dev_hostname.lower() or \
                                       (dev_serial and search_term_lower in dev_serial.lower()):
                                        cached_device_info = (op_data, dev_hostname, dev_connection_ip)
                                        break
                                    
                                    dev_hostname_clean = re.sub(r'[^a-z0-9]', '', dev_hostname.lower())
                                    if search_clean and search_clean in dev_hostname_clean:
                                        cached_device_info = (op_data, dev_hostname, dev_connection_ip)
                                        break
                                except Exception:
                                    pass
            
            if cached_device_info:
                op_data, dev_hostname, dev_connection_ip = cached_device_info
                neighbors = op_data.get('lldp_neighbors', [])
                last_updated = op_data.get('lldp_last_updated', '')
                
                if neighbors:
                    self._send_json({
                        'lldp_neighbors': neighbors,
                        'cached': True,
                        'last_updated': last_updated,
                        'hostname': dev_hostname,
                        'source': 'scaler-db'
                    })
                    return
                else:
                    target = dev_connection_ip or dev_hostname
                    result = self._fetch_lldp_neighbors(target)
                    result['cached'] = False
                    result['hostname'] = dev_hostname
                    result['note'] = f'Fetched live from {target} (cached data was empty)'
                    self._send_json(result)
                    return
            
            # No cached data found - try live SSH with original search term
            target = serial or hostname
            result = self._fetch_lldp_neighbors(target)
            result['cached'] = False
            
            # If live fetch failed and we have similar device names, suggest them
            if result.get('error') and all_devices:
                # Find similar device names using fuzzy matching
                import difflib
                search_term = serial or hostname
                device_names = [d['hostname'] for d in all_devices if d['hostname']]
                matches = difflib.get_close_matches(search_term, device_names, n=3, cutoff=0.4)
                if matches:
                    result['suggestions'] = matches
                    result['error'] = f"{result.get('error')}. Did you mean: {', '.join(matches)}?"
            
            self._send_json(result)
        
        
        elif parsed.path == '/api/lldp-neighbors-live':
            # Fetch LLDP neighbor table LIVE (NetworkMapper first, SSH fallback)
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            serial = (data.get('serial') or '').strip()
            if not serial:
                self._send_json({'error': 'serial is required'}, 400)
                return
            
            # Try NetworkMapper first (fast DB lookup, freshest data)
            try:
                nm = _get_mcp_client()
                nm_neighbors = nm.get_device_lldp(serial)
                if nm_neighbors:
                    nm_list = [{
                        'local_interface': n.local_interface,
                        'neighbor_device': n.neighbor_name,
                        'neighbor_port': n.neighbor_interface
                    } for n in nm_neighbors]
                    self._send_json({
                        'lldp_neighbors': nm_list,
                        'cached': False,
                        'source': 'network-mapper',
                        'hostname': serial
                    })
                    print(f"[LLDP-Live] Served {len(nm_list)} neighbors from NetworkMapper for {serial}")
                    return
            except Exception as e:
                print(f"[LLDP-Live] NetworkMapper failed, falling back to SSH: {e}")
            
            result = self._fetch_lldp_neighbors(serial)
            result['source'] = 'ssh-live'
            self._send_json(result)
        
        # ================================================================
        # Network Mapper — start discovery
        # ================================================================
        elif parsed.path == '/api/network-mapper/start':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return

            seeds = data.get('seeds', [])
            use_inventory = data.get('use_inventory', False)

            # If use_inventory, load seeds from device_inventory.json
            if use_inventory:
                inv_file = Path('/home/dn/CURSOR/device_inventory.json')
                if inv_file.exists():
                    try:
                        with open(inv_file, 'r') as f:
                            inv_data = json.load(f)
                        for key, dev in inv_data.get('devices', {}).items():
                            mgmt_ip = dev.get('mgmt_ip', '') or ''
                            hostname = dev.get('hostname', '') or ''
                            seed = mgmt_ip or hostname or key
                            if seed and seed not in seeds:
                                seeds.append(seed)
                    except Exception as e:
                        print(f"[NM] Failed to load inventory: {e}")

            if not seeds:
                self._send_json({'error': 'No seeds provided. Supply seeds[] or set use_inventory=true'}, 400)
                return

            max_depth = min(int(data.get('max_depth', 10)), 20)
            max_devices = min(int(data.get('max_devices', 50)), 200)
            creds = data.get('credentials', {})
            username = creds.get('username', 'dnroot')
            password = creds.get('password', 'dnroot')
            use_mcp = data.get('use_network_mapper_mcp', True)
            known_devices = data.get('known_devices', [])

            _nm_cleanup_old_jobs()
            with nm_job_lock:
                nm_job_counter += 1
                job_id = f"nm_{nm_job_counter}_{int(time.time())}"
                nm_jobs[job_id] = {
                    'status': 'starting',
                    'progress': {'discovered': 0, 'queued': len(seeds), 'failed': 0, 'max': max_devices},
                    'devices': {},
                    'links': [],
                    'errors': [],
                    'log': [f"Starting network mapper with {len(seeds)} seed(s), max_depth={max_depth}, max_devices={max_devices}"],
                    'cancelled': False,
                    'created_at': time.time()
                }

            thread = threading.Thread(
                target=_nm_bfs_crawl,
                args=(job_id, seeds, max_depth, max_devices, username, password, use_mcp, known_devices),
                daemon=True
            )
            thread.start()
            self._send_json({'job_id': job_id, 'status': 'starting', 'seeds': seeds})

        # Network Mapper — stop discovery
        elif parsed.path == '/api/network-mapper/stop':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({'error': 'Invalid JSON'}, 400)
                return
            jid = data.get('job_id', '')
            if jid and jid in nm_jobs:
                with nm_job_lock:
                    nm_jobs[jid]['cancelled'] = True
                self._send_json({'status': 'cancelling', 'job_id': jid})
            else:
                self._send_json({'error': 'Job not found'}, 404)

        # Network Mapper — full MCP-based topology (no SSH, queries MCP for all devices)
        elif parsed.path == '/api/network-mapper/mcp-map':
            _nm_cleanup_old_jobs()
            with nm_job_lock:
                nm_job_counter += 1
                job_id = f"mcp_{nm_job_counter}_{int(time.time())}"
                nm_jobs[job_id] = {
                    'status': 'starting',
                    'progress': {'discovered': 0, 'queued': 0, 'failed': 0, 'max': 200},
                    'devices': {},
                    'links': [],
                    'errors': [],
                    'log': ['Starting MCP full-map...'],
                    'cancelled': False,
                    'created_at': time.time()
                }
            thread = threading.Thread(target=_nm_mcp_full_map, args=(job_id,), daemon=True)
            thread.start()
            self._send_json({'job_id': job_id, 'status': 'starting'})

        else:
            self._send_json({'error': 'Not found'}, 404)
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def main():
    port = 8765
    server = HTTPServer(('0.0.0.0', port), DiscoveryHandler)
    print(f"Discovery API server running on http://localhost:{port}")
    print("Endpoints:")
    print("  POST /api/discovery/start  - Start discovery (body: {serial1, serial2?})")
    print("  GET  /api/discovery/status?job_id=X  - Get job status")
    print("  GET  /api/discovery/list   - List output files")
    server.serve_forever()

if __name__ == '__main__':
    main()


