# SCALER Wizard Complete Options Reference

> **Version**: 1.0.0  
> **Last Updated**: December 31, 2025  
> **Purpose**: Comprehensive documentation of all SCALER wizard options, parameters, and API endpoints for GUI implementation

---

## Table of Contents

1. [Overview](#overview)
2. [Multi-Device Menu Options](#multi-device-menu-options)
3. [Single-Device Menu Options](#single-device-menu-options)
4. [Configuration Wizards](#configuration-wizards)
5. [API Endpoints Reference](#api-endpoints-reference)
6. [WebSocket Events](#websocket-events)
7. [Data Models](#data-models)

---

## Overview

The SCALER wizard operates in two modes:
- **Single Device Mode**: Operations on one device
- **Multi-Device Mode**: Synchronized operations across multiple PEs

All features are available in both modes (where applicable) to maintain feature parity.

---

## Multi-Device Menu Options

### [1] Compare Configurations

**Description**: Show detailed configuration diff between devices.

| Property | Value |
|----------|-------|
| CLI Function | `_show_multi_device_compare(multi_ctx)` |
| API Endpoint | `POST /api/operations/diff` |
| Required Devices | 2+ |

**Parameters**:
```json
{
  "device_ids": ["pe1", "pe2"],
  "hierarchy": null  // null = full config, or "interfaces", "services", "bgp", "igp", "system"
}
```

**Response**:
```json
{
  "device1": "PE-1",
  "device2": "PE-2",
  "hierarchy": null,
  "lines_device1": 5000,
  "lines_device2": 4800,
  "lines_added": 150,
  "lines_removed": 50,
  "lines_changed": 30,
  "diff_sections": [
    {
      "type": "added",
      "title": "Interfaces only in PE-1",
      "lines": ["interface Bundle-Ether100.500", "..."]
    },
    {
      "type": "removed",
      "title": "Interfaces only in PE-2",
      "lines": ["interface Bundle-Ether200.600", "..."]
    },
    {
      "type": "changed",
      "title": "Modified sections",
      "changes": [{"from": "...", "to": "..."}]
    }
  ],
  "summary": "200 lines different"
}
```

---

### [2] Sync Status

**Description**: Detailed synchronization analysis between EVPN peers.

| Property | Value |
|----------|-------|
| CLI Function | `_show_multi_device_sync_status(multi_ctx)` |
| API Endpoint | `POST /api/operations/sync-status` |
| Required Devices | 2+ |

**Parameters**:
```json
{
  "device_ids": ["pe1", "pe2"]
}
```

**Response**:
```json
{
  "devices": ["PE-1", "PE-2"],
  "shared_route_targets": 150,
  "shared_evis": 100,
  "multihoming": {
    "pe1_count": 200,
    "pe2_count": 200,
    "matching_esi": 198,
    "mismatched_esi": 2,
    "only_pe1": 0,
    "only_pe2": 0
  },
  "sync_status": "synced",  // "synced", "partial", "out_of_sync"
  "recommendations": []
}
```

---

### [3] Push Files

**Description**: Push saved configuration files to all devices.

| Property | Value |
|----------|-------|
| CLI Function | `_push_config_to_all_devices(multi_ctx, [])` |
| API Endpoint | `GET /api/config/{device_id}/saved-files` + `POST /api/operations/push` |
| Required Devices | 1+ |

**Get Saved Files Request**:
```json
GET /api/config/pe1/saved-files
```

**Get Saved Files Response**:
```json
{
  "device_id": "pe1",
  "files": [
    {
      "filename": "config_20251230_143022.txt",
      "path": "/home/dn/SCALER/db/configs/PE-1/history/config_20251230_143022.txt",
      "timestamp": "2025-12-30T14:30:22",
      "lines": 1500,
      "validated": true,
      "pushed": false
    }
  ]
}
```

**Push Request**:
```json
{
  "device_id": "pe1",
  "config": "interfaces\n  Bundle-Ether1.100\n    encapsulation dot1q 100\n  !\n!",
  "hierarchy": "interfaces",
  "mode": "merge",  // "merge" or "replace"
  "dry_run": false
}
```

---

### [4] Configure All

**Description**: Full configuration wizard for all hierarchies.

| Property | Value |
|----------|-------|
| CLI Function | `run_wizard()` main flow |
| API Endpoint | Multiple endpoints per hierarchy |
| Required Devices | 1+ |

See [Configuration Wizards](#configuration-wizards) section for details.

---

### [5] Delete Hierarchy

**Description**: Delete configuration sections from all devices.

| Property | Value |
|----------|-------|
| CLI Function | `show_delete_hierarchy_menu_multi()` |
| API Endpoint | `POST /api/operations/delete` |
| Required Devices | 1+ |

**Parameters**:
```json
{
  "device_id": "pe1",
  "hierarchy": "interfaces",  // "system", "interfaces", "services", "bgp", "igp", "multihoming"
  "sub_path": "Bundle-Ether1.100"  // Optional: specific element
}
```

**Hierarchy Options**:

| Hierarchy | Description | DNOS Delete Command |
|-----------|-------------|---------------------|
| `system` | System configuration | `no system` |
| `interfaces` | All interfaces | `no interfaces <name>` |
| `services` | Network services | `no network-services evpn instance <name>` |
| `bgp` | BGP configuration | `no protocols bgp <asn>` |
| `igp` | ISIS/OSPF config | `no protocols isis` |
| `multihoming` | ESI config | `no multihoming` |

---

### [6] Modify Service Interfaces

**Description**: Add, remove, or remap interfaces attached to services.

| Property | Value |
|----------|-------|
| CLI Function | `show_modify_service_interfaces_menu(multi_ctx)` |
| API Endpoint | `POST /api/operations/modify-interfaces` |
| Required Devices | 1+ |

**Parameters**:
```json
{
  "device_ids": ["pe1", "pe2"],
  "operation": "add",  // "add", "remove", "remap"
  "service_filter": "FXC_*",
  "interfaces": {
    "add": ["Bundle-Ether1.500", "Bundle-Ether1.501"],
    "remove": ["Bundle-Ether1.100"],
    "remap": {
      "Bundle-Ether1.100": "Bundle-Ether2.100"
    }
  },
  "dry_run": true
}
```

**Response**:
```json
{
  "job_id": "abc12345",
  "status": "started",
  "affected_services": 50,
  "changes_preview": [
    {
      "service": "FXC_1",
      "action": "add_interface",
      "interface": "Bundle-Ether1.500"
    }
  ]
}
```

---

### [7] Image Upgrade

**Description**: Upgrade DNOS/GI/BaseOS from Jenkins builds.

| Property | Value |
|----------|-------|
| CLI Function | `run_image_upgrade_wizard(multi_ctx)` |
| API Endpoint | `POST /api/operations/image-upgrade` |
| Required Devices | 1+ |

**Parameters**:
```json
{
  "device_ids": ["pe1", "pe2"],
  "branch": "main",  // or private branch name
  "components": ["DNOS", "GI", "BaseOS"],  // which components to upgrade
  "build_number": null,  // null = latest, or specific build number
  "upgrade_type": "normal",  // "normal", "delete_deploy" (major version change)
  "parallel": true
}
```

**Response** (async with WebSocket progress):
```json
{
  "job_id": "upg_12345",
  "status": "started",
  "message": "Connecting to Jenkins..."
}
```

**Progress Events**:
```json
{"type": "step", "current": 1, "total": 5, "name": "Fetching stack URLs from Jenkins"}
{"type": "progress", "percent": 20, "message": "Loading DNOS..."}
{"type": "terminal", "line": "> request system target-stack load http://..."}
{"type": "complete", "success": true, "result": {"from_version": "24.3.0", "to_version": "24.4.0"}}
```

---

### [8] Stag Pool Check

**Description**: Live QinQ Stag usage from Linux shell.

| Property | Value |
|----------|-------|
| CLI Function | `_run_stag_pool_check(multi_ctx)` |
| API Endpoint | `POST /api/operations/stag-check` |
| Required Devices | 1+ |

**Parameters**:
```json
{
  "device_ids": ["pe1", "pe2"]
}
```

**Response**:
```json
{
  "devices": [
    {
      "hostname": "PE-1",
      "device_ip": "10.0.0.1",
      "total_stags": 2500,
      "limit": 4000,
      "percentage": 63,
      "remaining": 1500,
      "at_risk": false,
      "exceeded": false,
      "stags": [
        {"ifindex": 88001, "ifname": "stag.100", "parent": "Bundle-Ether1", "outer_tag": 100}
      ]
    }
  ],
  "summary": {
    "total_devices": 2,
    "devices_at_risk": 0,
    "devices_exceeded": 0
  }
}
```

---

### [9] Scale Up/Down

**Description**: Bulk add or delete services with correlated interfaces.

| Property | Value |
|----------|-------|
| CLI Function | `show_scale_wizard(multi_ctx)` |
| API Endpoint | `POST /api/operations/scale-updown` |
| Required Devices | 1+ |

**Parameters**:
```json
{
  "device_ids": ["pe1", "pe2"],
  "operation": "down",  // "up" or "down"
  "service_type": "fxc",  // "fxc", "l2vpn", "evpn", "vpws"
  "range_spec": "last 300",  // "last N", "100-400", "1,2,3", "100-200,300-400"
  "include_interfaces": true,  // Delete correlated PWHE/subifs
  "dry_run": true
}
```

**Range Spec Formats**:

| Format | Example | Description |
|--------|---------|-------------|
| Last N | `last 300` | Last 300 services by number |
| Single | `100` | Service with number 100 |
| List | `100,200,300` | Specific services |
| Range | `100-400` | Services 100 through 400 |
| Mixed | `1-100,200-300,500` | Multiple ranges and singles |

**Response**:
```json
{
  "job_id": "scale_12345",
  "status": "started",
  "preview": {
    "services_affected": 300,
    "interfaces_affected": 600,
    "services": ["FXC_701", "FXC_702", "..."],
    "interfaces": ["ph1.701", "ph1.702", "..."]
  }
}
```

---

## Single-Device Menu Options

The single-device menu provides the same features wrapped for single device operation:

| Option | Action | Multi-Device Equivalent |
|--------|--------|------------------------|
| [1] Push Files | Push saved config | Same |
| [2] Stag Pool Check | QinQ usage | Same |
| [R] Refresh | Reload config | Same |
| [3] Configure Device | Full wizard | Configure All |
| [4] Delete Hierarchy | Delete sections | Same |
| [5] Modify Interfaces | Add/remove/remap | Same |
| [6] Image Upgrade | Jenkins upgrade | Same |
| [7] Scale Up/Down | Bulk operations | Same |

---

## Configuration Wizards

### Interface Wizard

**Steps**:

1. **Select Parent Interfaces**
   - Choose existing parent interfaces (Bundle-Ether, HundredGigE, etc.)
   - Or create new parent interfaces

2. **Configure Pattern**
   - Sub-interfaces per parent
   - Starting interface number
   - Increment pattern

3. **VLAN Configuration**
   - Single tag (dot1q) or Double tag (QinQ)
   - Outer VLAN start and step
   - Inner VLAN start and step (QinQ only)

4. **IP Configuration** (Optional)
   - IPv4, IPv6, or Both
   - Starting IP and prefix length
   - IP increment step

5. **Review Configuration**
   - Preview generated config
   - DNOS limit validation

6. **Push to Device**
   - Dry run (commit check) option
   - Progress tracking

**API Endpoint**: `POST /api/config/generate/interfaces`

**Request**:
```json
{
  "interface_type": "bundle",  // "bundle", "ge100", "ge400", "ge10"
  "start_number": 1,
  "count": 10,
  "slot": 0,
  "bay": 0,
  "port_start": 0,
  "create_subinterfaces": true,
  "subif_count_per_interface": 100,
  "subif_vlan_start": 100,
  "subif_vlan_step": 1,
  "encapsulation": "dot1q"  // "dot1q" or "qinq"
}
```

---

### Service Wizard

**Steps**:

1. **Select Service Type**
   - EVPN VPWS FXC (Flexible Cross-Connect)
   - EVPN VPLS (Bridge Domain)
   - L3VPN VRF

2. **Naming Configuration**
   - Name prefix (e.g., "FXC_", "CUST-A_")
   - Start number
   - Count

3. **Route Target Configuration**
   - EVI/Service ID start
   - Route Distinguisher base ASN
   - Auto-generate or manual RTs

4. **Interface Attachment**
   - Select interfaces to attach
   - Interface-to-service mapping

5. **Push to Device**
   - Preview and validation
   - Progress tracking

**API Endpoint**: `POST /api/config/generate/services`

**Request**:
```json
{
  "service_type": "evpn-vpws-fxc",  // "evpn-vpws-fxc", "vrf", "evpn"
  "name_prefix": "FXC_",
  "start_number": 1,
  "count": 100,
  "service_id_start": 1000,
  "evi_start": 1000,
  "rd_base": "65000",
  "attach_interfaces": ["Bundle-Ether1.100", "Bundle-Ether1.101"]
}
```

---

### Multihoming Wizard

**Steps**:

1. **Select Devices**
   - Choose 2+ devices for ESI sync

2. **Matching Mode**
   - Match by Route Target + VLAN
   - Match by interface name pattern
   - Manual mapping

3. **ESI Configuration**
   - ESI prefix (Type 1 format: `00:11:22:33:44`)
   - Redundancy mode: Single-Active or All-Active
   - Designated Forwarder election

4. **Review Matches**
   - Show matched interface pairs
   - Highlight mismatches

5. **Sync ESI**
   - Generate matching ESI values
   - Push to both devices

**API Endpoints**:
- Compare: `POST /api/operations/multihoming/compare`
- Sync: `POST /api/operations/multihoming/sync`

**Compare Request**:
```json
{
  "device_ids": ["pe1", "pe2"]
}
```

**Sync Request**:
```json
{
  "device_ids": ["pe1", "pe2"],
  "esi_prefix": "00:11:22:33:44",
  "match_neighbor": true,
  "redundancy_mode": "single-active"
}
```

---

### BGP Configuration

**Parameters**:

| Field | Type | Description |
|-------|------|-------------|
| `as_number` | int | BGP Autonomous System number |
| `router_id` | string | Router ID (usually loopback IP) |
| `neighbors` | array | List of BGP peers |
| `address_families` | array | AFI/SAFI to enable |

**API Endpoint**: `POST /api/config/generate/bgp`

**Request**:
```json
{
  "as_number": 65000,
  "router_id": "10.0.0.1",
  "neighbors": [
    {
      "ip": "10.0.0.2",
      "remote_as": 65000,
      "update_source": "Loopback0",
      "address_families": ["ipv4-unicast", "l2vpn-evpn"]
    }
  ]
}
```

---

### IGP Configuration (ISIS/OSPF)

**Parameters**:

| Field | Type | Description |
|-------|------|-------------|
| `protocol` | string | "isis" or "ospf" |
| `instance_name` | string | Instance name (e.g., "IGP") |
| `net` | string | ISIS NET address |
| `area` | string | OSPF area ID |
| `interfaces` | array | Interfaces to add |

**API Endpoint**: `POST /api/config/generate/igp`

**Request**:
```json
{
  "protocol": "isis",
  "instance_name": "IGP",
  "net": "49.0001.0100.0000.0001.00",
  "interfaces": [
    {"name": "Loopback0", "passive": true},
    {"name": "HundredGigE0/0/0", "passive": false, "metric": 10}
  ],
  "level": "level-2-only"
}
```

---

### System Configuration

**Parameters**:

| Field | Type | Description |
|-------|------|-------------|
| `hostname` | string | Device hostname |
| `profile` | string | System profile (e.g., "l3-pe") |
| `domain_name` | string | Domain name |
| `users` | array | Local users |
| `ssh` | object | SSH configuration |
| `logging` | object | Logging configuration |

**API Endpoint**: `POST /api/config/generate/system`

**Request**:
```json
{
  "hostname": "PE-1",
  "profile": "l3-pe",
  "domain_name": "lab.local",
  "users": [
    {"name": "admin", "password_hash": "...", "role": "root-system"}
  ],
  "ssh": {
    "enabled": true,
    "port": 22
  }
}
```

---

## API Endpoints Reference

### Device Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/devices/` | List all devices |
| GET | `/api/devices/{id}` | Get single device |
| POST | `/api/devices/` | Add new device |
| PUT | `/api/devices/{id}` | Update device |
| DELETE | `/api/devices/{id}` | Delete device |
| POST | `/api/devices/{id}/test` | Test connection |
| POST | `/api/devices/{id}/sync` | Sync running config |
| POST | `/api/devices/reload` | Reload device list |

### Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config/{id}/running` | Get running config |
| GET | `/api/config/{id}/summary` | Get config summary |
| GET | `/api/config/{id}/interfaces` | List interfaces |
| GET | `/api/config/{id}/services` | List services |
| GET | `/api/config/{id}/multihoming` | Get MH config |
| GET | `/api/config/{id}/hierarchy/{name}` | Get hierarchy section |
| GET | `/api/config/{id}/saved-files` | List saved config files |
| POST | `/api/config/generate/interfaces` | Generate interface config |
| POST | `/api/config/generate/services` | Generate service config |
| POST | `/api/config/generate/system` | Generate system config |
| POST | `/api/config/generate/bgp` | Generate BGP config |
| POST | `/api/config/generate/igp` | Generate IGP config |

### Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/operations/validate` | Validate config |
| POST | `/api/operations/push` | Push config to device |
| POST | `/api/operations/delete` | Delete hierarchy |
| POST | `/api/operations/diff` | Compare configs |
| POST | `/api/operations/sync-status` | Sync status analysis |
| POST | `/api/operations/multihoming/compare` | Compare MH |
| POST | `/api/operations/multihoming/sync` | Sync MH |
| POST | `/api/operations/modify-interfaces` | Modify service interfaces |
| POST | `/api/operations/image-upgrade` | Jenkins upgrade |
| POST | `/api/operations/stag-check` | Stag pool check |
| POST | `/api/operations/scale-updown` | Scale up/down |
| POST | `/api/operations/batch` | Batch operations |
| GET | `/api/operations/{job_id}` | Get job status |
| POST | `/api/operations/{job_id}/cancel` | Cancel job |

---

## WebSocket Events

Connect to `/ws/progress/{job_id}` for real-time updates.

### Event Types

```javascript
// Progress update
{"type": "progress", "percent": 45, "message": "Loading configuration..."}

// Step update
{"type": "step", "current": 2, "total": 5, "name": "Committing changes"}

// Terminal output
{"type": "terminal", "line": "> configure"}

// Operation complete
{"type": "complete", "success": true, "result": {...}}

// Error occurred
{"type": "error", "message": "Connection timeout"}
```

---

## Data Models

### Device

```json
{
  "id": "pe1",
  "hostname": "PE-1",
  "ip": "10.0.0.1",
  "platform": "ncp",
  "username": "dnroot",
  "last_sync": "2025-12-30T14:30:22",
  "description": "Lab PE router"
}
```

### ConfigSummary

```json
{
  "system": {
    "hostname": "PE-1",
    "profile": "l3-pe",
    "users": 2
  },
  "interfaces": {
    "parents": 4,
    "subinterfaces": 200,
    "pwhe": 50,
    "types": {"bundle": 2, "physical": 2, "loopback": 1}
  },
  "services": {
    "fxc": 100,
    "vpls": 50,
    "vrf": 10,
    "route_targets": 150
  },
  "bgp": {
    "as_number": 65000,
    "peer_count": 2,
    "router_id": "10.0.0.1"
  },
  "igp": {
    "protocol": "isis",
    "instance": "IGP",
    "interface_count": 6
  },
  "multihoming": {
    "count": 200,
    "esi_prefix": "00:01:02"
  }
}
```

### OperationResponse

```json
{
  "job_id": "abc12345",
  "status": "started",
  "message": "Operation started. Connect to /ws/progress/abc12345 for updates."
}
```

### ValidationResult

```json
{
  "valid": true,
  "errors": [],
  "warnings": ["Interface count approaching limit (90%)"],
  "config_lines": 500
}
```

---

## DNOS Platform Limits

Reference limits for validation:

| Resource | Limit | Config Key |
|----------|-------|------------|
| PWHE Interfaces | 4,096 | `interfaces.max_pwhe` |
| FXC Instances | 8,000 | `services.max_fxc_instances` |
| EVPN Instances | 4,000 | `services.max_evpn_instances` |
| BGP Peers | 2,000 | `bgp.max_peers` |
| MH ESI Interfaces | 2,000 | `multihoming.max_esi_interfaces` |
| Stag Pool | 4,000 | PR-86760 limit |

---

## GUI Implementation Notes

When implementing GUI components:

1. **Use Wizard Steps** - Sequential panels with Next/Back navigation
2. **Real-time Validation** - Validate inputs before proceeding
3. **WebSocket Progress** - Show live progress for long operations
4. **Error Handling** - Display errors per device in multi-device mode
5. **Keyboard Shortcuts** - Escape to close, Enter to confirm

See `DEVELOPMENT_GUIDELINES.md` for GUI parity requirements.








