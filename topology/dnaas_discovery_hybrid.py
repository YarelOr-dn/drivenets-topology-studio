#!/usr/bin/env python3
"""
DNAAS Discovery - Hybrid Approach (Cache + Live SSH)

Strategy:
1. Use CACHED data from scaler-monitor for termination devices (PE, RR)
2. Use LIVE SSH only for DNAAS fabric traversal (unavoidable middle hops)
3. This cuts discovery time significantly by eliminating SSH to PE devices

Usage:
    python3 dnaas_discovery_hybrid.py <device1> <device2>
    
Example:
    python3 dnaas_discovery_hybrid.py PE-1 PE-4
"""

import json
import sys
import paramiko
import time
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

# Paths
SCALER_DB = Path("/home/dn/SCALER/db/configs")
OUTPUT_DIR = Path("/home/dn/CURSOR/output")
CREDENTIALS_FILE = Path("/home/dn/CURSOR/device_credentials.json")

# Default DNAAS credentials (fallback if not in credentials file)
DNAAS_USER = "sisaev"
DNAAS_PASS = "Drive1234!"

# DNAAS detection keywords
DNAAS_KEYWORDS = ['DNAAS', 'LEAF', 'SPINE', 'FABRIC', 'TOR', 'AGGREGATION', 'SUPERSPINE']

# ============================================================================
# BRIDGE DOMAIN CLASSES
# ============================================================================

@dataclass
class BridgeDomain:
    """Bridge Domain information from DNAAS device"""
    bd_id: int
    name: str = ""
    vlan_id: Optional[int] = None
    interfaces: List[str] = field(default_factory=list)
    attachment_circuits: List[Dict[str, Any]] = field(default_factory=list)
    state: str = "unknown"

class SimpleBDDiscovery:
    """Simplified BD discovery - just the essential find_bd_from_config method"""
    
    def __init__(self, ssh_client, hostname: str):
        self.hostname = hostname
        self._ssh_client = ssh_client
        self._shell = None
        self._init_shell()
    
    def _init_shell(self):
        """Initialize interactive shell"""
        try:
            self._shell = self._ssh_client.invoke_shell(width=250, height=50)
            self._shell.settimeout(60)
            time.sleep(1)
            if self._shell.recv_ready():
                self._shell.recv(65535)
        except Exception as e:
            print(f"    ✗ Shell init failed: {e}")
    
    def _run_command(self, command: str, timeout: int = 30) -> str:
        """Run command via shell, wait for prompt"""
        if not self._shell:
            return ""
        try:
            self._shell.send(command + "\n")
            output = ""
            end_time = time.time() + timeout
            while time.time() < end_time:
                if self._shell.recv_ready():
                    chunk = self._shell.recv(65535).decode('utf-8', errors='ignore')
                    output += chunk
                    if output.rstrip().endswith('#') or output.rstrip().endswith('>'):
                        break
                else:
                    time.sleep(0.1)
            # Strip ANSI
            ansi_escape = re.compile(r'\x1b\[[0-9;]*m|\033\[[0-9;]*m|\[\d+m')
            return ansi_escape.sub('', output)
        except:
            return ""
    
    def find_bd_from_config(self, interface: str) -> List[str]:
        """Find BD names for interface using config search"""
        bd_names = []
        seen = set()
        base_interface = interface.split('.')[0]
        interfaces_to_search = [interface]
        if interface != base_interface:
            interfaces_to_search.append(base_interface)
        
        for search_if in interfaces_to_search:
            cmd = f"show config network-services bridge-domain | include {search_if} leading 10 trailing 10 | no-more"
            output = self._run_command(cmd, timeout=45)
            
            if not output or 'No match' in output:
                continue
            
            current_bd = None
            for line in output.split('\n'):
                line_stripped = line.strip()
                instance_match = re.match(r'instance\s+(\S+)', line_stripped)
                if instance_match:
                    current_bd = instance_match.group(1)
                    continue
                
                if current_bd and search_if in line_stripped and 'interface' in line_stripped:
                    if 'mgmt' in current_bd.lower():
                        current_bd = None
                        continue
                    if current_bd not in seen:
                        bd_names.append(current_bd)
                        seen.add(current_bd)
                        print(f"    ✓ Found BD: {current_bd} (contains {search_if})")
                        current_bd = None
        return bd_names

# ============================================================================
# DEVICE & PATH CLASSES
# ============================================================================

# SSH timeout
SSH_TIMEOUT = 10

@dataclass
class Device:
    """Represents a network device"""
    hostname: str
    label: str = ""
    device_type: str = "unknown"  # DUT, DNAAS, RR
    lldp_neighbors: List[Dict] = field(default_factory=list)
    bridge_domains: List[str] = field(default_factory=list)  # BD names
    mgmt_ip: str = ""
    is_dnaas: bool = False
    from_cache: bool = False
    
    def __post_init__(self):
        self.is_dnaas = any(kw in self.hostname.upper() for kw in DNAAS_KEYWORDS)
        if self.is_dnaas:
            self.device_type = "DNAAS"

@dataclass
class DnaasPath:
    """Represents a discovered DNAAS path"""
    source_device: str
    target_device: str
    hops: List[Dict] = field(default_factory=list)
    total_hops: int = 0
    bridge_domains: List[str] = field(default_factory=list)  # BDs in path
    
    def add_hop(self, from_device: str, from_port: str, to_device: str, to_port: str):
        self.hops.append({
            "hop": len(self.hops) + 1,
            "from_device": from_device,
            "from_port": from_port,
            "to_device": to_device,
            "to_port": to_port
        })
        self.total_hops = len(self.hops)

class DnaasDiscoveryHybrid:
    """Hybrid DNAAS discovery using cache + live SSH"""
    
    def __init__(self, db_path: Path = SCALER_DB):
        self.db_path = db_path
        self.cached_devices: Dict[str, Device] = {}
        self.live_devices: Dict[str, Device] = {}
        self.ssh_call_count = 0
        self.credentials = self._load_credentials()
    
    def _load_credentials(self) -> Dict[str, Dict]:
        """Load device credentials from file"""
        if not CREDENTIALS_FILE.exists():
            print(f"⚠️  No credentials file found at {CREDENTIALS_FILE}")
            print(f"   Using default DNAAS credentials for all devices")
            return {}
        
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                data = json.load(f)
                creds = data.get('devices', {})
                print(f"✅ Loaded credentials for {len(creds)} devices from {CREDENTIALS_FILE.name}")
                return creds
        except Exception as e:
            print(f"⚠️  Error loading credentials: {e}")
            return {}
        
    def load_cached_devices(self) -> int:
        """Load PE/RR devices from scaler-monitor cache"""
        print(f"📦 Loading cached devices from {self.db_path}")
        
        count = 0
        for device_dir in self.db_path.iterdir():
            if not device_dir.is_dir():
                continue
            
            operational_file = device_dir / "operational.json"
            if not operational_file.exists():
                continue
            
            try:
                with open(operational_file, 'r') as f:
                    data = json.load(f)
                
                hostname = data.get('hostname', device_dir.name)
                device = Device(
                    hostname=hostname,
                    label=hostname,
                    lldp_neighbors=data.get('lldp_neighbors', []),
                    mgmt_ip=data.get('mgmt_ip', ''),
                    from_cache=True
                )
                
                self.cached_devices[hostname] = device
                count += 1
                print(f"  ✓ {hostname}: {len(device.lldp_neighbors)} LLDP neighbors (cached)")
                
            except Exception as e:
                print(f"  ✗ Error loading {device_dir.name}: {e}")
        
        print(f"✅ Loaded {count} cached devices\n")
        return count
    
    def ssh_get_lldp_and_bds(self, hostname: str, mgmt_ip: str = None) -> Tuple[List[Dict], List[str]]:
        """Get both LLDP neighbors AND Bridge Domains in single SSH session"""
        self.ssh_call_count += 1
        print(f"  🔌 SSH #{self.ssh_call_count}: {hostname} (LLDP + BD discovery)")
        
        # Get credentials
        creds = None
        hostname_lower = hostname.lower()
        if hostname_lower in self.credentials:
            creds = self.credentials[hostname_lower]
        
        username = creds.get('user', DNAAS_USER) if creds else DNAAS_USER
        password = creds.get('password', DNAAS_PASS) if creds else DNAAS_PASS
        
        # Try connection: hostname first
        connection_attempts = [hostname]
        if creds and creds.get('mgmt_ip') and creds['mgmt_ip'] != hostname:
            connection_attempts.append(creds['mgmt_ip'])
        if mgmt_ip and mgmt_ip not in connection_attempts:
            connection_attempts.append(mgmt_ip)
        
        last_error = None
        for connect_host in connection_attempts:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(connect_host, username=username, password=password, 
                           timeout=SSH_TIMEOUT, look_for_keys=False, allow_agent=False)
                
                # Get LLDP neighbors
                channel = ssh.invoke_shell(width=250, height=50)
                channel.settimeout(60)
                time.sleep(1)
                if channel.recv_ready():
                    channel.recv(65535)
                
                channel.send('show lldp neighbor | no-more\n')
                lldp_output = ""
                end_time = time.time() + 30
                while time.time() < end_time:
                    if channel.recv_ready():
                        chunk = channel.recv(65535).decode('utf-8', errors='ignore')
                        lldp_output += chunk
                        if lldp_output.rstrip().endswith('#') or lldp_output.rstrip().endswith('>'):
                            break
                    else:
                        time.sleep(0.1)
                
                neighbors = self._parse_lldp_output(lldp_output)
                print(f"    ✓ Found {len(neighbors)} LLDP neighbors")
                
                # Get BDs - check first few interfaces only
                bd_names = set()
                for neighbor in neighbors[:5]:
                    if_name = neighbor.get('interface', '')
                    if if_name:
                        cmd = f"show config network-services bridge-domain | include {if_name} leading 5 trailing 5 | no-more\n"
                        channel.send(cmd)
                        bd_output = ""
                        end_time = time.time() + 15
                        while time.time() < end_time:
                            if channel.recv_ready():
                                chunk = channel.recv(65535).decode('utf-8', errors='ignore')
                                bd_output += chunk
                                if bd_output.rstrip().endswith('#') or bd_output.rstrip().endswith('>'):
                                    break
                            else:
                                time.sleep(0.1)
                        
                        # Parse BD names
                        for line in bd_output.split('\n'):
                            instance_match = re.match(r'instance\s+(\S+)', line.strip())
                            if instance_match:
                                bd_name = instance_match.group(1)
                                if 'mgmt' not in bd_name.lower():
                                    bd_names.add(bd_name)
                
                ssh.close()
                
                bd_list = list(bd_names)
                if bd_list:
                    print(f"    ✓ Found {len(bd_list)} BDs: {', '.join(bd_list[:3])}")
                
                return neighbors, bd_list
                
            except Exception as e:
                last_error = e
                continue
        
        print(f"    ✗ All connection attempts failed. Last error: {last_error}")
        return [], []
        """Live SSH to get LLDP neighbors (for DNAAS devices only)"""
        self.ssh_call_count += 1
        print(f"  🔌 SSH #{self.ssh_call_count}: {hostname} (live query)")
        
        # Get credentials from file first
        creds = None
        hostname_lower = hostname.lower()
        if hostname_lower in self.credentials:
            creds = self.credentials[hostname_lower]
            print(f"    ✓ Using credentials from file")
        
        # Get username and password
        username = creds.get('user', DNAAS_USER) if creds else DNAAS_USER
        password = creds.get('password', DNAAS_PASS) if creds else DNAAS_PASS
        
        # Try connection: hostname first, then mgmt_ip as fallback
        connection_attempts = []
        
        # Priority 1: Direct hostname (as reported by LLDP neighbor)
        connection_attempts.append(hostname)
        
        # Priority 2: mgmt_ip from credentials file (if available)
        if creds and creds.get('mgmt_ip'):
            if creds['mgmt_ip'] != hostname:  # Don't duplicate
                connection_attempts.append(creds['mgmt_ip'])
        
        # Priority 3: Passed mgmt_ip parameter (if different)
        if mgmt_ip and mgmt_ip not in connection_attempts:
            connection_attempts.append(mgmt_ip)
        
        if not creds and not mgmt_ip:
            print(f"    ⚠️  No credentials in file, using defaults")
        
        last_error = None
        for attempt_num, connect_host in enumerate(connection_attempts, 1):
            try:
                print(f"    → Attempt {attempt_num}/{len(connection_attempts)}: {connect_host}")
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    connect_host,
                    username=username,
                    password=password,
                    timeout=SSH_TIMEOUT,
                    look_for_keys=False,
                    allow_agent=False
                )
                
                print(f"    ✓ Connected to {connect_host}")
                
                # Use interactive shell (some DNOS devices require this)
                channel = ssh.invoke_shell(width=250, height=50)
                channel.settimeout(60)
                time.sleep(1)
                
                # Clear initial banner
                if channel.recv_ready():
                    channel.recv(65535)
                
                # Execute LLDP command - try both singular and plural
                channel.send('show lldp neighbor | no-more\n')
                output = ""
                end_time = time.time() + 30  # 30 second timeout
                
                while time.time() < end_time:
                    if channel.recv_ready():
                        chunk = channel.recv(65535).decode('utf-8', errors='ignore')
                        output += chunk
                        # Check for prompt (ends with # or >)
                        if output.rstrip().endswith('#') or output.rstrip().endswith('>'):
                            break
                    else:
                        time.sleep(0.1)
                
                # If invalid/error or empty, try plural form
                if 'invalid' in output.lower() or 'unknown' in output.lower() or len(output.strip()) < 50:
                    print(f"    ⚠️  'show lldp neighbor' failed, trying 'show lldp neighbors'...")
                    
                    channel.send('show lldp neighbors | no-more\n')
                    output = ""
                    end_time = time.time() + 30
                    
                    while time.time() < end_time:
                        if channel.recv_ready():
                            chunk = channel.recv(65535).decode('utf-8', errors='ignore')
                            output += chunk
                            if output.rstrip().endswith('#') or output.rstrip().endswith('>'):
                                break
                        else:
                            time.sleep(0.1)
                
                ssh.close()
                
                # Debug: show raw output
                if output.strip():
                    lines = output.strip().split('\n')
                    print(f"    📄 Raw LLDP output ({len(output)} chars):")
                    print("    " + "\n    ".join(lines[:10]))
                    if len(lines) > 10:
                        print(f"    ... ({len(lines) - 10} more lines)")
                else:
                    print(f"    ⚠️  Empty LLDP output!")
                
                # Parse LLDP output
                neighbors = self._parse_lldp_output(output)
                print(f"    ✓ Found {len(neighbors)} LLDP neighbors")
                
                return neighbors
                
            except Exception as e:
                last_error = e
                print(f"    ✗ Connection failed: {e}")
                continue
        
        # All attempts failed
        print(f"    ✗ All connection attempts failed. Last error: {last_error}")
        return []
    
    def _parse_lldp_output(self, output: str) -> List[Dict]:
        """Parse LLDP neighbor output - using same regex as original script"""
        neighbors = []
        
        for line in output.split('\n'):
            # Parse LLDP neighbor table using regex (from original script)
            # Format: | ge100-0/0/4 | YOR_PE-1 | ge400-0/0/4 | 120 |
            match = re.match(
                r'\|\s*([\w\-/\.]+)\s*\|\s*(\S+)\s*\|\s*([\w\-/\.]+)\s*\|\s*(\d+)',
                line
            )
            if match:
                local_if, neighbor, remote_if, ttl = match.groups()
                # Skip header row
                if local_if.lower() != 'interface' and neighbor.lower() not in ['neighbor', 'system']:
                    # Skip empty neighbor names
                    if neighbor and len(neighbor) > 1:
                        neighbors.append({
                            "interface": local_if,
                            "neighbor": neighbor,
                            "remote_port": remote_if,
                            "is_dn_device": True
                        })
            else:
                # Fallback: try simple whitespace split (from original script)
                parts = line.split()
                if len(parts) >= 3 and (parts[0].startswith('ge') or parts[0].startswith('bundle')):
                    if parts[1] and len(parts[1]) > 1:  # Skip empty neighbors
                        neighbors.append({
                            "interface": parts[0],
                            "neighbor": parts[1],
                            "remote_port": parts[2] if len(parts) > 2 else '',
                            "is_dn_device": True
                        })
        
        return neighbors
    
    def find_device(self, label: str) -> Optional[Device]:
        """Find device by label, hostname, serial number, or IP address (from cache first, then live)"""
        # Try exact hostname match in cache
        if label in self.cached_devices:
            return self.cached_devices[label]
        
        # Try case-insensitive partial hostname match in cache
        label_lower = label.lower()
        for hostname, device in self.cached_devices.items():
            if label_lower in hostname.lower():
                return device
        
        # Try reverse: hostname contains label (e.g., "YOR_PE-1" contains "PE-1")
        for hostname, device in self.cached_devices.items():
            if hostname.lower() in label_lower:
                print(f"  ✓ Matched '{label}' to cached device '{hostname}'")
                return device
        
        # NEW: Try matching by serial number in operational.json
        cache_dir = Path('/home/dn/SCALER/db/configs')
        if cache_dir.exists():
            for device_dir in cache_dir.iterdir():
                if device_dir.is_dir():
                    op_file = device_dir / 'operational.json'
                    if op_file.exists():
                        try:
                            with open(op_file, 'r') as f:
                                op_data = json.load(f)
                            serial = op_data.get('serial_number', '')
                            if serial and (serial.lower() == label_lower or label_lower == serial.lower()):
                                # Found by serial! Use the directory name as hostname
                                hostname = device_dir.name
                                if hostname in self.cached_devices:
                                    print(f"  ✓ Resolved serial {label} → {hostname}")
                                    return self.cached_devices[hostname]
                                # Device exists in cache dir but not loaded yet - shouldn't happen
                                print(f"  ⚠️  Found device by serial but not in loaded cache: {hostname}")
                        except Exception as e:
                            pass
        
        # Try IP address match (strip /netmask if present)
        for hostname, device in self.cached_devices.items():
            if device.mgmt_ip:
                # Handle both "10.1.1.1" and "10.1.1.1/24" formats
                device_ip = device.mgmt_ip.split('/')[0]
                search_ip = label.split('/')[0]
                if device_ip == search_ip:
                    print(f"  ✓ Found device {hostname} by IP {search_ip}")
                    return device
        
        # Check if already queried live
        if label in self.live_devices:
            return self.live_devices[label]
        
        return None
    
    def get_or_discover_device(self, hostname: str) -> Optional[Device]:
        """Get device from cache, or discover via SSH if DNAAS"""
        # Check cache first
        device = self.find_device(hostname)
        if device:
            return device
        
        # If not in cache and looks like DNAAS, SSH to it
        is_dnaas = any(kw in hostname.upper() for kw in DNAAS_KEYWORDS)
        if is_dnaas:
            print(f"  📡 {hostname} not in cache, querying live...")
            
            # Get SSH connection and LLDP + BD in one session
            device = Device(
                hostname=hostname,
                label=hostname,
                lldp_neighbors=[],
                bridge_domains=[],
                is_dnaas=True,
                from_cache=False
            )
            
            # SSH once, get both LLDP and BDs
            try:
                device.lldp_neighbors, device.bridge_domains = self.ssh_get_lldp_and_bds(hostname)
            except Exception as e:
                print(f"    ✗ Discovery failed: {e}")
            
            self.live_devices[hostname] = device
            return device
        
        return None
    
    def trace_path(self, source_label: str, target_label: str) -> Optional[DnaasPath]:
        """Trace DNAAS path using hybrid approach"""
        
        source_dev = self.find_device(source_label)
        target_dev = self.find_device(target_label)
        
        if not source_dev:
            print(f"❌ Source device '{source_label}' not found in cache")
            return None
        
        if not target_dev:
            print(f"❌ Target device '{target_label}' not found in cache")
            return None
        
        print(f"\n🔍 Tracing path: {source_dev.hostname} → {target_dev.hostname}")
        print(f"   Source: {'CACHED' if source_dev.from_cache else 'LIVE'}")
        print(f"   Target: {'CACHED' if target_dev.from_cache else 'LIVE'}\n")
        
        path = DnaasPath(
            source_device=source_dev.hostname,
            target_device=target_dev.hostname
        )
        
        # BFS to find path
        visited: Set[str] = set()
        queue: List[Tuple[str, List[Dict]]] = [(source_dev.hostname, [])]
        max_depth = 10  # Limit path depth to prevent infinite exploration
        
        while queue:
            current_hostname, hops = queue.pop(0)
            
            # Check depth limit
            if len(hops) >= max_depth:
                print(f"  ⚠️  Max depth ({max_depth}) reached, skipping deeper exploration")
                continue
            
            if current_hostname in visited:
                continue
            visited.add(current_hostname)
            
            current_dev = self.get_or_discover_device(current_hostname)
            if not current_dev:
                continue
            
            # Check if we reached target
            if current_hostname == target_dev.hostname:
                print(f"  ✓ Reached target: {current_hostname}")
                path.hops = hops
                path.total_hops = len(hops)
                # Collect BDs from devices in path
                for hop in hops:
                    from_dev = self.live_devices.get(hop['from_device'])
                    if from_dev and from_dev.bridge_domains:
                        path.bridge_domains.extend(from_dev.bridge_domains)
                path.bridge_domains = list(set(path.bridge_domains))  # Dedupe
                return path
            
            # Explore LLDP neighbors
            for neighbor in current_dev.lldp_neighbors:
                neighbor_name = neighbor.get('neighbor', '')
                if not neighbor_name:
                    continue
                
                if neighbor_name in visited:
                    continue
                
                # Try to find neighbor (may need fuzzy matching for hostname variations)
                neighbor_dev = self.find_device(neighbor_name)
                if not neighbor_dev and neighbor_name == target_dev.hostname:
                    print(f"  ✓ Reached target: {neighbor_name}")
                    # Add final hop and return
                    final_hop = {
                        "from_device": current_hostname,
                        "from_port": neighbor.get('interface', ''),
                        "to_device": neighbor_name,
                        "to_port": neighbor.get('remote_port', '')
                    }
                    path.hops = hops + [final_hop]
                    path.total_hops = len(path.hops)
                    # Collect BDs
                    for hop in path.hops:
                        from_dev = self.live_devices.get(hop['from_device'])
                        if from_dev and from_dev.bridge_domains:
                            path.bridge_domains.extend(from_dev.bridge_domains)
                    path.bridge_domains = list(set(path.bridge_domains))
                    return path
                
                print(f"  → Exploring neighbor: {neighbor_name} (from {current_hostname})")
                
                # Add hop
                new_hop = {
                    "from_device": current_hostname,
                    "from_port": neighbor.get('interface', ''),
                    "to_device": neighbor_name,
                    "to_port": neighbor.get('remote_port', '')
                }
                
                new_hops = hops + [new_hop]
                queue.append((neighbor_name, new_hops))
        
        print(f"❌ No path found")
        return None
    
    def print_path(self, path: DnaasPath):
        """Print path details"""
        print("\n" + "="*70)
        print(f"PATH: {path.source_device} → {path.target_device}")
        print("="*70)
        print(f"Total hops: {path.total_hops}")
        if path.bridge_domains:
            print(f"Bridge Domains: {', '.join(path.bridge_domains)}")
        print()
        
        for i, hop in enumerate(path.hops, 1):
            print(f"  {i}. {hop['from_device']}:{hop['from_port']}")
            print(f"     ↓")
            print(f"     {hop['to_device']}:{hop['to_port']}")
            print()
        
        print(f"📊 Performance:")
        print(f"   SSH calls: {self.ssh_call_count}")
        print(f"   Cached devices used: {len([d for d in self.cached_devices.values() if d.hostname in [path.source_device, path.target_device]])}")
        print()
    
    def export_json(self, path: DnaasPath):
        """Export path to JSON"""
        OUTPUT_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = OUTPUT_DIR / f"dnaas_path_{timestamp}.json"
        
        data = {
            "discovery_time": datetime.now().isoformat(),
            "ssh_calls": self.ssh_call_count,
            "source": path.source_device,
            "target": path.target_device,
            "total_hops": path.total_hops,
            "bridge_domains": path.bridge_domains,
            "hops": path.hops
        }
        
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"📄 Exported: {json_file}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 dnaas_discovery_hybrid.py <source> <target>")
        print("Example: python3 dnaas_discovery_hybrid.py PE-1 PE-4")
        sys.exit(1)
    
    source_label = sys.argv[1]
    target_label = sys.argv[2]
    
    discovery = DnaasDiscoveryHybrid()
    
    # Load cached devices (PE, RR from scaler-monitor)
    if discovery.load_cached_devices() == 0:
        print("❌ No cached devices found. Is scaler-monitor running?")
        sys.exit(1)
    
    # Trace path (will SSH only to DNAAS devices in the middle)
    path = discovery.trace_path(source_label, target_label)
    
    if path:
        discovery.print_path(path)
        discovery.export_json(path)
        print(f"✅ Discovery complete!")
    else:
        print("\n❌ No path discovered")
        sys.exit(1)

if __name__ == "__main__":
    main()
