#!/usr/bin/env python3
"""
DNAAS Discovery Using Cached Monitor Data

This script uses the cached operational.json files from scaler-monitor
to quickly discover DNAAS paths without SSH queries.

Usage:
    python3 dnaas_discovery_cached.py <device_label1> [device_label2...]
    
Example:
    python3 dnaas_discovery_cached.py cl-pe-4 PE-1
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Paths
SCALER_DB = Path("/home/dn/SCALER/db/configs")
OUTPUT_DIR = Path("/home/dn/CURSOR/output")

# DNAAS detection keywords
DNAAS_KEYWORDS = ['DNAAS', 'LEAF', 'SPINE', 'FABRIC', 'TOR', 'AGGREGATION', 'SUPERSPINE']

@dataclass
class Device:
    """Represents a network device"""
    hostname: str
    label: str = ""
    device_type: str = "unknown"  # DUT, DNAAS, RR
    lldp_neighbors: List[Dict] = field(default_factory=list)
    mgmt_ip: str = ""
    is_dnaas: bool = False
    
    def __post_init__(self):
        # Auto-detect DNAAS based on hostname
        self.is_dnaas = any(kw in self.hostname.upper() for kw in DNAAS_KEYWORDS)
        if self.is_dnaas:
            self.device_type = "DNAAS"

@dataclass
class DnaasPath:
    """Represents a discovered DNAAS path between two devices"""
    source_device: str
    target_device: str
    hops: List[Dict] = field(default_factory=list)
    total_hops: int = 0
    
    def add_hop(self, from_device: str, from_port: str, to_device: str, to_port: str, hop_num: int):
        self.hops.append({
            "hop": hop_num,
            "from_device": from_device,
            "from_port": from_port,
            "to_device": to_device,
            "to_port": to_port
        })
        self.total_hops = len(self.hops)

class DnaasDiscovery:
    """DNAAS Path Discovery using cached monitor data"""
    
    def __init__(self, db_path: Path = SCALER_DB):
        self.db_path = db_path
        self.devices: Dict[str, Device] = {}
        self.discovered_paths: List[DnaasPath] = []
        
    def load_all_devices(self) -> int:
        """Load all operational.json files from scaler-monitor db"""
        print(f"🔍 Scanning {self.db_path} for cached device data...")
        
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
                    label=hostname,  # Can be overridden from topology
                    lldp_neighbors=data.get('lldp_neighbors', []),
                    mgmt_ip=data.get('mgmt_ip', ''),
                )
                
                self.devices[hostname] = device
                count += 1
                
                print(f"  ✓ Loaded {hostname}: {len(device.lldp_neighbors)} LLDP neighbors")
                
            except Exception as e:
                print(f"  ✗ Error loading {device_dir.name}: {e}")
        
        print(f"\n✅ Loaded {count} devices from cache\n")
        return count
    
    def find_device_by_label(self, label: str) -> Optional[Device]:
        """Find device by label or hostname"""
        # Try exact match first
        if label in self.devices:
            return self.devices[label]
        
        # Try case-insensitive partial match
        label_lower = label.lower()
        for hostname, device in self.devices.items():
            if label_lower in hostname.lower():
                return device
        
        return None
    
    def trace_path(self, source: str, target: str) -> Optional[DnaasPath]:
        """Trace DNAAS path between two devices using LLDP neighbors"""
        
        source_dev = self.find_device_by_label(source)
        target_dev = self.find_device_by_label(target)
        
        if not source_dev:
            print(f"❌ Source device '{source}' not found in cache")
            return None
        
        if not target_dev:
            print(f"❌ Target device '{target}' not found in cache")
            return None
        
        print(f"🔍 Tracing path: {source_dev.hostname} → {target_dev.hostname}")
        
        path = DnaasPath(
            source_device=source_dev.hostname,
            target_device=target_dev.hostname
        )
        
        # BFS to find path through DNAAS fabric
        visited: Set[str] = set()
        queue: List[Tuple[str, List[Dict], int]] = [(source_dev.hostname, [], 0)]
        
        while queue:
            current_hostname, hops, hop_count = queue.pop(0)
            
            if current_hostname in visited:
                continue
            visited.add(current_hostname)
            
            current_dev = self.devices.get(current_hostname)
            if not current_dev:
                continue
            
            # Check if we reached target
            if current_hostname == target_dev.hostname:
                path.hops = hops
                path.total_hops = len(hops)
                return path
            
            # Explore LLDP neighbors
            for neighbor in current_dev.lldp_neighbors:
                neighbor_name = neighbor.get('neighbor', '')
                if not neighbor_name or neighbor_name in visited:
                    continue
                
                neighbor_dev = self.devices.get(neighbor_name)
                if not neighbor_dev:
                    continue
                
                # Only traverse through DNAAS devices (unless it's the target)
                if not neighbor_dev.is_dnaas and neighbor_name != target_dev.hostname:
                    continue
                
                new_hop = {
                    "hop": hop_count + 1,
                    "from_device": current_hostname,
                    "from_port": neighbor.get('interface', ''),
                    "to_device": neighbor_name,
                    "to_port": neighbor.get('remote_port', '')
                }
                
                new_hops = hops + [new_hop]
                queue.append((neighbor_name, new_hops, hop_count + 1))
        
        print(f"  ❌ No path found through DNAAS fabric")
        return None
    
    def discover_paths(self, device_labels: List[str]) -> List[DnaasPath]:
        """Discover DNAAS paths between all device pairs"""
        
        if len(device_labels) < 2:
            print("❌ Need at least 2 devices to discover paths")
            return []
        
        print(f"🔍 Discovering DNAAS paths for {len(device_labels)} devices\n")
        
        paths = []
        for i, source in enumerate(device_labels):
            for target in device_labels[i+1:]:
                path = self.trace_path(source, target)
                if path:
                    paths.append(path)
                    print(f"  ✅ Found path: {path.total_hops} hops\n")
                else:
                    print(f"  ❌ No path found\n")
        
        self.discovered_paths = paths
        return paths
    
    def export_json(self, output_file: Path):
        """Export discovered paths to JSON"""
        data = {
            "discovery_time": datetime.now().isoformat(),
            "total_devices": len(self.devices),
            "total_paths": len(self.discovered_paths),
            "paths": [
                {
                    "source": path.source_device,
                    "target": path.target_device,
                    "total_hops": path.total_hops,
                    "hops": path.hops
                }
                for path in self.discovered_paths
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"📄 Exported JSON: {output_file}")
    
    def print_summary(self):
        """Print discovery summary"""
        print("\n" + "="*70)
        print("DNAAS DISCOVERY SUMMARY (CACHED DATA)")
        print("="*70)
        print(f"Total devices in cache: {len(self.devices)}")
        print(f"Total paths discovered: {len(self.discovered_paths)}")
        print()
        
        for i, path in enumerate(self.discovered_paths, 1):
            print(f"Path {i}: {path.source_device} → {path.target_device}")
            print(f"  Hops: {path.total_hops}")
            for hop in path.hops:
                print(f"    {hop['hop']}. {hop['from_device']}:{hop['from_port']} → "
                      f"{hop['to_device']}:{hop['to_port']}")
            print()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 dnaas_discovery_cached.py <device1> [device2] ...")
        print("Example: python3 dnaas_discovery_cached.py PE-1 PE-2")
        sys.exit(1)
    
    device_labels = sys.argv[1:]
    
    discovery = DnaasDiscovery()
    
    # Load all cached devices
    if discovery.load_all_devices() == 0:
        print("❌ No cached devices found. Is scaler-monitor running?")
        sys.exit(1)
    
    # Discover paths
    paths = discovery.discover_paths(device_labels)
    
    if paths:
        # Export results
        OUTPUT_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = OUTPUT_DIR / f"dnaas_path_{timestamp}.json"
        discovery.export_json(json_file)
        
        # Print summary
        discovery.print_summary()
        
        print(f"\n✅ Discovery complete! Found {len(paths)} path(s)")
    else:
        print("\n❌ No paths discovered")
        sys.exit(1)

if __name__ == "__main__":
    main()
