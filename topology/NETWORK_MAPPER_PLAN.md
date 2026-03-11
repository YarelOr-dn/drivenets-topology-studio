# Network Topology Mapper - Implementation Plan

**Created**: 2025-12-25  
**Status**: IMPLEMENTED  
**Location**: `/home/dn/CURSOR/network_mapper/`  
**Total Lines**: 1,964

---

## Goal

Create an automated network discovery tool that:
1. Starts from a PE device
2. Enables all physical interfaces and LLDP
3. Discovers LLDP neighbors (DNAAS devices or snake connections)
4. Connects to DNAAS devices to map Bridge Domain paths
5. Traces paths through DNAAS core to remote PEs
6. Generates a text report showing physical and logical topology
7. Includes bundle membership information for logical paths

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     PE-1        │────▶│  DNAAS-LEAF     │────▶│     PE-2        │
│                 │     │                 │     │                 │
│ Physical IFs    │     │ Bridge Domains  │     │ Physical IFs    │
│ Bundle Members  │     │ LLDP Neighbors  │     │ Bundle Members  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
   LLDP Discovery         BD Path Tracing         LLDP Discovery
        │                       │                       │
        └───────────────────────┴───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Topology Report     │
                    │  - Physical Links     │
                    │  - Logical Paths      │
                    │  - Bundle Membership  │
                    │  - Snake Connections  │
                    └───────────────────────┘
```

---

## Discovery Flow

### Phase 1: Local PE Discovery
1. Connect to starting PE device (dnroot/dnroot)
2. Run `show interfaces` to find physical interfaces
3. Filter to real physical interfaces only (ge*, bundle*)
4. Exclude: lo*, ph*, irb*, sub-interfaces (*.N)
5. Parse bundle-id attachments to map bundle membership
6. Generate config to enable interfaces + LLDP
7. Commit configuration

### Phase 2: LLDP Neighbor Discovery
1. Run `show lldp neighbors` on PE
2. For each neighbor:
   - If neighbor device = self → Mark as **SNAKE** connection
   - If neighbor device = DNAAS → Continue to Phase 3
   - If neighbor device = another PE → Record direct PE-PE link

### Phase 3: DNAAS Connection
1. Look up DNAAS device IP from `dnaas_table.xlsx`
2. SSH to DNAAS using **sisaev / Drive1234!**
3. Run `show lldp neighbors` to find interface connected to PE
4. Run `show network-services bridge domain` to find BD attachments

### Phase 4: Bridge Domain Path Tracing
1. Find which BD the PE-facing interface belongs to
2. Get all other interfaces attached to that BD
3. For each attached interface:
   - Check LLDP to see where it leads
   - If leads to another DNAAS → Continue through core
   - If leads to a PE → Record as endpoint

### Phase 5: Topology Building
1. Build physical topology graph (LLDP-based)
2. Build logical topology graph (BD-based, PE endpoints only)
3. Include bundle membership for each interface
4. Mark snake connections

### Phase 6: Report Generation
1. Generate text report with:
   - Physical interfaces enabled
   - Bundle membership
   - Physical topology (LLDP)
   - Logical topology (PE to PE paths)
   - Snake connections

---

## File Structure

```
/home/dn/CURSOR/
├── network_mapper/
│   ├── __init__.py              # Package init
│   ├── mapper.py                # Main orchestrator (~200 lines)
│   ├── device_connector.py      # SSH/CLI handling (~150 lines)
│   ├── interface_discovery.py   # Parse show interfaces (~100 lines)
│   ├── bundle_mapper.py         # Bundle-id detection (~80 lines)
│   ├── lldp_discovery.py        # LLDP neighbor parsing (~80 lines)
│   ├── dnaas_lookup.py          # Excel lookup (~60 lines)
│   ├── bridge_domain_mapper.py  # BD path mapping (~150 lines)
│   ├── topology_builder.py      # Build graphs (~120 lines)
│   └── report_generator.py      # Text output (~100 lines)
├── dnaas_table.xlsx             # DNAAS device inventory (exists)
├── reports/                     # Generated topology reports
│   └── .gitkeep
└── NETWORK_MAPPER_PLAN.md       # This file
```

---

## Module Specifications

### 1. device_connector.py

```python
class DeviceConnector:
    """SSH connection handler for PE and DNAAS devices"""
    
    @staticmethod
    def connect_pe(hostname: str, user: str = "dnroot", 
                   password: str = "dnroot") -> "DeviceConnector"
    
    @staticmethod  
    def connect_dnaas(hostname: str, user: str = "sisaev",
                      password: str = "Drive1234!") -> "DeviceConnector"
    
    def execute_command(self, command: str, timeout: int = 30) -> str
    def execute_config(self, config_lines: list[str]) -> bool
    def get_hostname(self) -> str
    def close(self) -> None
```

### 2. interface_discovery.py

```python
class InterfaceDiscovery:
    """Discovers and enables physical interfaces"""
    
    def __init__(self, connector: DeviceConnector)
    def get_all_interfaces(self) -> list[dict]
    def get_physical_interfaces(self) -> list[dict]  # ge*, bundle* only
    def generate_enable_config(self, interfaces: list) -> list[str]
    def generate_lldp_config(self, interfaces: list) -> list[str]
```

**Physical Interface Filter**:
- INCLUDE: `ge*`, `bundle-*` (parents only)
- EXCLUDE: `lo*`, `ph*`, `irb*`, `mgmt*`, `ctrl*`, `*.N` (sub-interfaces)

### 3. bundle_mapper.py

```python
class BundleMapper:
    """Maps physical interfaces to bundle membership"""
    
    def __init__(self, connector: DeviceConnector)
    def parse_bundle_attachments(self) -> dict
    def get_bundle_members(self, bundle_name: str) -> list[str]
    def get_interface_bundle(self, interface: str) -> str | None
    def is_bundle_member(self, interface: str) -> bool
```

**Data Structure**:
```python
{
    "bundles": {
        "bundle-1": ["ge400-0/0/1", "ge400-0/0/2"],
        "bundle-2": ["ge400-0/0/5", "ge400-0/0/6"]
    },
    "interfaces": {
        "ge400-0/0/1": "bundle-1",
        "ge400-0/0/2": "bundle-1",
        "ge400-0/0/3": None  # standalone
    }
}
```

### 4. lldp_discovery.py

```python
class LLDPDiscovery:
    """Parses LLDP neighbors"""
    
    def __init__(self, connector: DeviceConnector)
    def get_neighbors(self) -> list[LLDPNeighbor]
    def is_snake_connection(self, neighbor: LLDPNeighbor) -> bool
    def is_dnaas_device(self, device_name: str) -> bool
```

**LLDPNeighbor Structure**:
```python
@dataclass
class LLDPNeighbor:
    local_interface: str
    remote_device: str
    remote_interface: str
    is_snake: bool = False
```

### 5. dnaas_lookup.py

```python
class DNAASLookup:
    """Looks up DNAAS devices from Excel inventory"""
    
    def __init__(self, xlsx_path: str = "dnaas_table.xlsx")
    def get_device_ip(self, device_name: str) -> str | None
    def get_device_by_serial(self, serial: str) -> dict | None
    def get_all_devices(self) -> list[dict]
    def is_accessible(self, device_name: str) -> bool
```

**Excel Columns**: Index, Rack, Name, Serial, IP Address, Status, TACACS, Accessible

### 6. bridge_domain_mapper.py

```python
class BridgeDomainMapper:
    """Maps paths through DNAAS via Bridge Domains"""
    
    def __init__(self, connector: DeviceConnector)
    def get_bridge_domains(self) -> list[BridgeDomain]
    def get_bd_for_interface(self, interface: str) -> str | None
    def get_bd_attachments(self, bd_name: str) -> list[str]
    def trace_path_from_interface(self, start_if: str) -> list[str]
```

### 7. topology_builder.py

```python
class TopologyBuilder:
    """Builds physical and logical topology graphs"""
    
    def add_physical_link(self, local_dev: str, local_if: str,
                          remote_dev: str, remote_if: str)
    def add_logical_path(self, source: dict, dest: dict, via: list)
    def add_snake(self, device: str, if1: str, if2: str)
    def get_physical_topology(self) -> dict
    def get_logical_topology(self) -> dict
    def get_snakes(self) -> list
```

### 8. report_generator.py

```python
class ReportGenerator:
    """Generates text topology report"""
    
    def __init__(self, topology: TopologyBuilder, bundles: dict)
    def generate_header(self) -> str
    def generate_interfaces_section(self) -> str
    def generate_bundles_section(self) -> str
    def generate_physical_section(self) -> str
    def generate_logical_section(self) -> str
    def generate_snakes_section(self) -> str
    def write_report(self, output_path: str) -> None
```

### 9. mapper.py (Main Orchestrator)

```python
def main(starting_device: str, output_dir: str = "reports"):
    """Main entry point for network mapping"""
    
    # Phase 1: Connect to starting PE
    # Phase 2: Discover interfaces and bundles
    # Phase 3: Enable interfaces and LLDP
    # Phase 4: Discover LLDP neighbors
    # Phase 5: Connect to DNAAS devices
    # Phase 6: Trace BD paths
    # Phase 7: Build topology
    # Phase 8: Generate report

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("device", help="Starting PE device hostname/IP")
    parser.add_argument("-o", "--output", default="reports", help="Output directory")
    args = parser.parse_args()
    main(args.device, args.output)
```

---

## Output Report Format

```
================================================================================
                        NETWORK TOPOLOGY MAP
                     Generated: 2025-12-25 15:00:00
                     Starting Device: PE-1
================================================================================

=== PHYSICAL INTERFACES ENABLED ===
  ge400-0/0/1   enabled, LLDP enabled, bundle-id: bundle-1
  ge400-0/0/2   enabled, LLDP enabled, bundle-id: bundle-1
  ge400-0/0/3   enabled, LLDP enabled, standalone
  ge400-0/0/4   enabled, LLDP enabled, standalone
  bundle-1      enabled, LLDP enabled

=== BUNDLE MEMBERSHIP ===
  bundle-1:
    Members: ge400-0/0/1, ge400-0/0/2
    Sub-interfaces: bundle-1.100, bundle-1.200

=== PHYSICAL TOPOLOGY (LLDP) ===
  PE-1:ge400-0/0/1     <----> DNAAS-LEAF-A01:ge100-0/0/5
  PE-1:ge400-0/0/2     <----> DNAAS-LEAF-A01:ge100-0/0/6
  PE-1:ge400-0/0/3     <----> PE-1:ge400-0/0/4  [SNAKE]

=== LOGICAL TOPOLOGY (PE to PE) ===
  
  Path 1: PE-1 <========> PE-2
    Source:      bundle-1.100 (LAG: ge400-0/0/1, ge400-0/0/2)
    Destination: ge400-0/0/5.100 (standalone)
    Via DNAAS:   DNAAS-LEAF-A01 -> DNAAS-SPINE-A08 -> DNAAS-LEAF-B01
  
  Path 2: PE-1 <========> PE-3
    Source:      ge400-0/0/5.200 (standalone)
    Destination: bundle-2.200 (LAG: ge400-0/0/1, ge400-0/0/2)
    Via DNAAS:   DNAAS-LEAF-A02 -> DNAAS-SPINE-B09 -> DNAAS-LEAF-C10

=== SNAKE CONNECTIONS ===
  PE-1:ge400-0/0/3 <--loopback--> PE-1:ge400-0/0/4

================================================================================
                              END OF REPORT
================================================================================
```

---

## Dependencies

- **paramiko**: SSH connections
- **openpyxl**: Excel file reading (already installed)
- **dataclasses**: Data structures (stdlib)
- **argparse**: CLI arguments (stdlib)
- **re**: Regex parsing (stdlib)
- **json**: Data serialization (stdlib)

---

## Credentials Reference

| Device Type | Username | Password |
|-------------|----------|----------|
| PE Devices | dnroot | dnroot |
| DNAAS Devices | sisaev | Drive1234! |

---

## DNAAS Inventory

Located at: `/home/dn/CURSOR/dnaas_table.xlsx`

Contains 54 devices:
- DNAAS-LEAF-* (Leaf switches)
- DNAAS-SPINE-* (Spine switches)  
- DNAAS-SuperSpine-* (Super spine)

---

## Implementation Order

1. [x] `device_connector.py` - Core SSH functionality (201 lines)
2. [x] `dnaas_lookup.py` - Excel parsing (122 lines)
3. [x] `interface_discovery.py` - Interface parsing (222 lines)
4. [x] `bundle_mapper.py` - Bundle detection (160 lines)
5. [x] `lldp_discovery.py` - LLDP parsing (169 lines)
6. [x] `bridge_domain_mapper.py` - BD tracing (181 lines)
7. [x] `topology_builder.py` - Graph building (237 lines)
8. [x] `report_generator.py` - Report output (218 lines)
9. [x] `mapper.py` - Main orchestrator (422 lines)
10. [ ] Testing on actual devices

---

## Estimated Effort

- **Total Lines**: ~1,040
- **Files**: 9 Python modules + 1 package init
- **Estimated Time**: 2-3 hours

---

## Notes

- Physical topology uses LLDP only
- Logical topology traces through Bridge Domains (not LLDP) in DNAAS core
- Bundle membership shown in logical paths, not physical
- Snake connections are self-loops (same device on both ends)
- Report hides intermediate Bridge Domain names, shows only PE endpoints

