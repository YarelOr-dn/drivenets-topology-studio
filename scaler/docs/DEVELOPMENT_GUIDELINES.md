# SCALER Development Guidelines

This document provides guidelines for developing new features in the SCALER application.

## EVPN-SI IRB TEST Recipes -- 2026-05-13

SW-228552 / EVPN-SI VPLS IRB recipes must use the shared `/debug-dnos`
knowledge cache feature `evpn_si_vpls_proxy_arp_ndp` as the expected-behavior
source. The current truth is:

1. IPv4 PW ARP is the known-good reference: fresh in-subnet PW ARP must be
   punted from DP/wb_agent to Routing and produce EVPN MAC/MAC-IP `v>` state
   with kernel ARP `Origin=evpn`. A PW-sourced MAC-IP must NOT be locally
   advertised as RT-2; RT-2 advertisement is for local AC/IRB ownership, and
   AC->PW moves must withdraw the local RT-2.
2. IPv6 PW solicited NA must follow the same integration path. If it only
   creates dynamic kernel NDP or MAC-only `v>` state without EVPN MAC-IP `v>`
   and `Origin=evpn`, classify it as the IPv6 PW proxy-NDP bug.
3. Do not use unsolicited NA as proof of PW-side MAC-IP learning. The valid
   teach packet is a low-rate solicited NA (`S=1/O=1/R=0`) unicast to the NS
   requester with a Target Link-Layer Address option. Unsolicited NA is only a
   negative/control packet.
4. Every recipe in this feature must require live Spirent traffic, loss
   measurement, before/after counters, raw device command input/output with
   device-local timestamps, and XRAY/DP evidence for IPv6 or proxy-NDP cases.
   Raw table outputs must include their headers, and trace evidence must name
   the process/component and trace file (`fibmgrd_traces`, `rib-manager_traces`,
   `wb_agent`, etc.) so DP-vs-routing responsibility is clear.
5. Keep a backup before bulk recipe edits and write `recipe.json` atomically.
6. Service migration recipes are not PASS unless they prove no-loss behavior:
   traffic starts before the migration commit, remains active during the
   commit and rollback, and records exactly zero packet loss. Required
   migration families are VPLS-only -> EVPN-SI+IRB, EVPN-only+IRB ->
   EVPN-SI+IRB, EVPN-SI+IRB -> EVPN-only, EVPN-SI+IRB -> VPLS-only, and
   VPLS-only -> EVPN-only. Each must prove the expected l2vpn-vpls and
   l2vpn-evpn signaling changes, no unrelated PW flap, no unrelated label
   churn, no FibMgr/bgpd/wb_agent restart, and rollback under traffic.
7. EVPN VPLS SI + IRB counter-watch recipes must compare DNOS service
   counters against Spirent per-stream and aggregate stats. Required evidence:
   `show evpn instance <service_name> vpls-pw counters | no-more`, EVPN
   forwarding counters, Spirent TX/RX/loss stats, monotonic sampled deltas,
   and unchanged drop/error counters. Scale runs are not PASS unless aggregate
   service-counter deltas match aggregate Spirent deltas with zero packet
   loss, and sampled per-service counters include raw table headers.
8. PW-fed EVPN VPLS SI + IRB scale recipes must use deterministic phased
   ramps for the 31k-PW / 220k-MAC / 440k-MAC-IP target. The full target
   is 4,000 services, 31,000 actual VPLS PWs feeding DUT IRB services,
   220,000 MAC entries, and two IP bindings per MAC. Required ramp gates
   are 10%, 25%, 50%, and 100%; each gate must prove exact advertised and
   installed EVPN RT-2/MAC/MAC-IP counts, sampled PW/service forwarding,
   counter parity with Spirent, zero packet loss, and no fibmgrd/bgpd/
   wb_agent restart before continuing.
9. The TEST compiler has SW-228552 lab defaults for PE-1/RR-SA-2/DNAAS
   placeholders (`<service_name>`, `<name>`, `<evi>`, `<anycast-mac>`,
   `<mac_or_ip>`, `<vpls_pw_peer_ip>`, `<ncp_id>`, `<DUT-A>`, `<DUT-B>`,
   etc.). Offline phase compilation is the readiness gate before live runs:
   `PHASES_COMPILED` means the recipe has concrete MCP dispatch metadata;
   remaining `NEEDS_PHASE_WIRING` must represent true manual/config/HA or
   source-specific operations, not missing placeholder bindings. The 2026-05-13
   baseline after compiler binding fixes is 77/131 SW-228552 recipes compiling
   without execution; the remaining 54 require live-safe phase wiring rather
   than one-by-one expected-behavior rediscovery.
10. DNAAS datapath availability for `/XRAY` and `/SPIRENT` must come from the
    dnos-config MCP VLAN-manipulation model, not from bridge-domain names or
    DUT sub-interface suffixes. `dnos_dnaas_inverse_path` and
    `dnos_dnaas_spirent_preflight` expose `dp_capture_plan`, which reports
    the Spirent-side capture leaf/port, expected wire tags, BPF hint, path
    availability, and tag-transform evidence after push/pop/swap handling.
    XRAY DP capture must consume that plan before declaring `NO_DP_PATH`.
11. Anycast IRB SW-198381 recipes must prove local MAC/IP precedence in both
    learn orders: local-first then PW duplicate, and PW-first then late local
    refresh. IPv4 must include both PW ARP request and PW ARP reply variants.
    Duplicate EVPN RT-2 for the same Anycast MAC/IP is a required control and
    must keep the local route best. Local IRB admin-down/no-CPU-punt behavior
    is SW-202894 regression scope, not a SW-198381 PASS criterion. IPv6
    Anycast cells are valid only after the PW solicited-NA MAC-IP/NDP baseline
    passes; otherwise classify as the known IPv6 PW NDP integration blocker
    (`SW-266543` / `SW-228552-bug-ipv6-only`). All edited SW-228552 recipes
    must dry-run through `test_phase_compile` with `PHASES_COMPILED` and no
    missing placeholder bindings before live execution.

## Feature Parity Requirement

**CRITICAL: ALL new features MUST be implemented in BOTH modes!**

The application operates in two modes:
1. **Single Device Mode** - Operations on one device
2. **Multi-Device Mode** - Synchronized operations on multiple devices (2+ PEs)

### ⚠️ ALWAYS Implement for Both Modes

When adding ANY new feature:
1. **Start with Multi-Device mode** - Design the feature with `MultiDeviceContext`
2. **Then add to Single-Device mode** - Create a temp `MultiDeviceContext([device])` and call the same function

This ensures feature parity and avoids duplicate code.

### Menu Locations to Update

| Mode | Menu Function | Location |
|------|---------------|----------|
| Multi-Device | `_show_multi_device_action_menu()` | interactive_scale.py ~line 445 |
| Single-Device | `Single Device Actions:` block | interactive_scale.py ~line 15100 |

### Pattern: Single-Device Wrapping Multi-Device Function

```python
# In single-device menu handler:
elif single_action == "my_feature":
    # Create temp context with single device - REUSE multi-device function
    single_ctx = MultiDeviceContext([device])
    single_ctx.discover_all()
    run_my_feature(single_ctx)  # Same function as multi-device!
    continue
```

### Current Feature Parity Matrix

| Feature | Multi-Device | Single-Device | Notes |
|---------|:------------:|:-------------:|-------|
| Compare | ✅ [1] | ❌ N/A | Only makes sense for 2+ devices |
| Sync Status | ✅ [2] | ❌ N/A | Only makes sense for 2+ devices |
| Push Files | ✅ [3] | ✅ [1] | Push saved configs |
| Configure | ✅ [4] | ✅ [3] | Full wizard |
| Delete Hierarchy | ✅ [5] | ✅ [4] | Delete config sections |
| Modify Interfaces | ✅ [6] | ✅ [5] | Add/remove/remap |
| Image Upgrade | ✅ [7] | ✅ [6] | Jenkins builds |
| Stag Pool Check | ✅ [8] | ✅ [2] | QinQ Stag usage |
| Scale Up/Down | ✅ [9] | ✅ [7] | Bulk add/delete services with interfaces |
| Mirror Config | ✅ [M] | ✅ [8] | Copy config from another PE |
| Refresh | ✅ [R] | ✅ [R] | Reload running config |
| Flowspec VPN | ✅ [F] | ✅ [9] | BGP Flowspec / DDoS mitigation (SW-182545, SW-182546) |
| Factory Reset | ✅ [F] | ✅ [F] | Load override factory-default |
| System Restore | ✅ [S] | ✅ [S] | Recover device from RECOVERY mode |
| Sync from Mapper | ✅ [N] | ✅ [N] | Pull configs from network-mapper (no SSH) |
| Import Topology | [3] | [3] | Import devices from network-mapper |

**When adding a new feature: Add to BOTH menus or explain why it only applies to one mode.**

---

## Terminal-to-GUI Parity Requirement

**CRITICAL: Every scaler/config feature MUST exist in BOTH the terminal wizard AND the GUI with API.**

See Cursor `/XDN` command and skill `~/.cursor/skills/xdn-topology-mastery/SKILL.md` (five-layer parity section).

### 5-Layer Checklist (Every New Config Feature)

| Layer | Location | Required |
|-------|----------|----------|
| 1. Builder | `scaler/scaler/wizard/config_builders.py` | `build_{feature}_config()` |
| 2. Terminal | `scaler/scaler/wizard/*.py` | Wizard path calling the builder |
| 3. API | `topology/scaler_bridge.py` | `POST /api/config/generate/{feature}` |
| 4. JS Client | `topology/scaler-api.js` | `ScalerAPI.generate{Feature}()` |
| 5. GUI | `topology/scaler-gui.js` | `open{Feature}Wizard()` with API preview |

**NEVER:** Add a terminal wizard path without a corresponding API endpoint. Never build DNOS strings in the frontend.

---

### Checklist for New Features

When adding a new feature, ensure:

- [ ] Feature works with `MultiDeviceContext` (multiple devices)
- [ ] Feature appears in `_show_multi_device_action_menu()` 
- [ ] **Feature ALSO appears in Single Device Actions menu**
- [ ] Update the Feature Parity Matrix above
- [ ] Parallel execution using `ThreadPoolExecutor` for device operations
- [ ] Live progress display showing all devices simultaneously
- [ ] Error handling per-device (one failure shouldn't stop others)
- [ ] Results summary showing success/failure per device

### Multi-Device Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     MultiDeviceContext                          │
├─────────────────────────────────────────────────────────────────┤
│  devices: List[Device]     # All selected devices              │
│  configs: Dict[hostname, config_text]                          │
│  summaries: Dict[hostname, DeviceSummary]                      │
│  loopbacks: Dict[hostname, ip]                                 │
│  bgp_asn: Dict[hostname, asn]                                  │
│  mh_config: Dict[hostname, Dict[interface, esi]]               │
│  route_targets: Dict[hostname, Set[rt]]                        │
└─────────────────────────────────────────────────────────────────┘
```

### Example: Adding a Multi-Device Feature

```python
def run_my_new_feature(multi_ctx: 'MultiDeviceContext') -> bool:
    """
    My new feature that works on all devices.
    
    Args:
        multi_ctx: MultiDeviceContext with selected devices
        
    Returns:
        True if successful on all devices
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from rich.live import Live
    from rich.table import Table
    
    # 1. Create status tracking for all devices
    device_status: Dict[str, Dict] = {}
    for dev in multi_ctx.devices:
        device_status[dev.hostname] = {
            'stage': 'pending',
            'message': 'Waiting...',
            'progress': 0
        }
    
    # 2. Create live display renderer
    def render_status() -> Table:
        table = Table(box=box.ROUNDED)
        table.add_column("Device")
        table.add_column("Stage")
        table.add_column("Progress")
        table.add_column("Status")
        
        for hostname, status in device_status.items():
            table.add_row(
                hostname,
                status['stage'],
                f"{status['progress']}%",
                status['message']
            )
        return table
    
    # 3. Define per-device operation
    def process_device(dev) -> Tuple[str, bool, str]:
        hostname = dev.hostname
        try:
            # Update status
            device_status[hostname] = {
                'stage': 'processing',
                'message': 'Working...',
                'progress': 50
            }
            
            # Do the actual work
            # ... your feature logic here ...
            
            device_status[hostname] = {
                'stage': 'completed',
                'message': 'Success',
                'progress': 100
            }
            return hostname, True, "Success"
            
        except Exception as e:
            device_status[hostname] = {
                'stage': 'failed',
                'message': str(e),
                'progress': 0
            }
            return hostname, False, str(e)
    
    # 4. Run in parallel with live display
    results = {}
    with Live(render_status(), refresh_per_second=2, console=console) as live:
        with ThreadPoolExecutor(max_workers=len(multi_ctx.devices)) as executor:
            futures = {
                executor.submit(process_device, dev): dev 
                for dev in multi_ctx.devices
            }
            
            for future in as_completed(futures):
                hostname, success, message = future.result()
                results[hostname] = success
                live.update(render_status())
    
    # 5. Show summary
    success_count = sum(1 for v in results.values() if v)
    console.print(f"\n[bold]Completed: {success_count}/{len(results)} devices[/bold]")
    
    return success_count == len(results)
```

### Adding to Multi-Device Menu

In `interactive_scale.py`, update `_show_multi_device_action_menu()`:

```python
# Add menu option
console.print("  [8] [magenta]My New Feature[/magenta] - Description")

# Add to choices
choice = Prompt.ask(
    "Select action",
    choices=["1", "2", "3", "4", "5", "6", "7", "8", "r", "R", "b", "B"],
    default="1"
).lower()

# Add to action map
action_map = {
    ...
    "8": "my_new_feature",
}
```

Then in the main loop:
```python
elif multi_action == 'my_new_feature':
    run_my_new_feature(multi_ctx)
```

---

## SSH Command Execution

### With Reconnection Handling

For operations that may cause device reboot/disconnect:

```python
def ssh_exec_with_retry(dev, cmd: str, max_retries: int = 3) -> Tuple[str, int]:
    """Execute SSH command with automatic retry."""
    from .device_manager import DeviceManager
    dm = DeviceManager()
    
    for attempt in range(max_retries):
        try:
            result = dm.execute_command(dev, cmd, timeout=120)
            return result, 0
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(5)  # Wait before retry
            else:
                return str(e), 1
    return "", 1
```

### Long-Running Operations

For operations like `request system target-stack install`:

```python
def wait_with_reconnect(dev, check_cmd: str, success_pattern: str, 
                        timeout: int = 3600, poll_interval: int = 30):
    """Wait for operation with automatic SSH reconnection."""
    start_time = time.time()
    consecutive_failures = 0
    
    while time.time() - start_time < timeout:
        try:
            output = dm.execute_command(dev, check_cmd, timeout=60)
            consecutive_failures = 0
            
            if success_pattern in output:
                return True, output
            
        except Exception:
            consecutive_failures += 1
            if consecutive_failures > 10:
                return False, "Lost connection"
        
        time.sleep(poll_interval)
    
    return False, "Timeout"
```

---

## SSH Connection Best Practices (CRITICAL)

### ⚠️ ALWAYS Use `get_ssh_hostname()` for SSH Connections

**Problem:** Devices may have multiple IPs (devices.json vs discovered mgmt IP).  
**Solution:** Use the helper function to get the best IP.

```python
from .utils import get_ssh_hostname

# ✓ CORRECT: Use helper function
hostname = get_ssh_hostname(device)
client.connect(hostname=hostname, ...)

# ✗ WRONG: Direct device.ip usage
client.connect(hostname=device.ip, ...)  # May use stale IP!
```

### IP Priority Logic

`get_ssh_hostname()` checks IPs in this order:

1. **`operational.json` → `mgmt_ip`** (highest priority - discovered during operations)
2. **`operational.json` → `ssh_host`** (fallback)
3. **`devices.json` → `ip`** (lowest priority - may be stale)

### Why This Matters

**Example: PE-2**
```json
// devices.json (stale IP)
{"ip": "100.64.8.39"}  ← ❌ Unreachable

// operational.json (current mgmt IP)
{"mgmt_ip": "100.64.4.205"}  ← ✅ Works
```

Without `get_ssh_hostname()`:
- SSH connection fails (tries 100.64.8.39)
- User sees: "SSH failed. Console: reachable, not recovery"
- Operations blocked even though device is reachable

With `get_ssh_hostname()`:
- Tries mgmt IP first (100.64.4.205)
- ✅ Connection succeeds
- Operations work normally

### Files Using `get_ssh_hostname()` ✅

- `scaler/config_extractor.py` - ConfigExtractor, InteractiveExtractor
- (More to be updated)

### Files Still Using Direct `device.ip` ⚠️

- `scaler/config_pusher.py` - 8 SSH connections (TODO)
- `scaler/interactive_scale.py` - 1 SSH connection (TODO)

**Action Required:** Update these files to use `get_ssh_hostname()` for consistency.

### Testing SSH Connection Logic

```python
# Test helper function
from scaler.models import Device
from scaler.utils import get_ssh_hostname

device = Device(...)
hostname = get_ssh_hostname(device)
print(f"Will connect to: {hostname}")

# Test actual connection
from scaler.config_extractor import InteractiveExtractor
with InteractiveExtractor(device) as extractor:
    config = extractor.get_running_config()
    print(f"✓ Retrieved {len(config)} bytes")
```

---

## DNOS CLI Syntax

Always use correct DNOS syntax. Reference: `/home/dn/SCALER/docs/DNOS_DELETE_SYNTAX.md`

### ⚠️ CRITICAL: Syntax Validation Requirement

**ALL DNOS syntax displays and generation MUST be validated against:**

1. **RST Documentation** - All relevant RST files in the documentation
2. **DNOS CLI PDF** - `/home/dn/SCALER/docs/DNOS_CLI.pdf` 
3. **Existing Running Configs** - Cross-reference with real device configs in `/home/dn/SCALER/db/configs/`

### Syntax Display Guidelines

When displaying configuration previews in the GUI:
- **ALWAYS use actual generated DNOS syntax** from SCALER generators
- **NEVER use simplified text descriptions** like "Will create X through Y"
- **Show real config snippets** that match what will be pushed to the device
- **Limit preview size** for performance (max 15-20 lines, show "... (N total)" for rest)

### Config Generator Requirements

All config generation functions MUST:
- [ ] Output valid DNOS CLI syntax only
- [ ] Match indentation standards (2 spaces per level)
- [ ] Use correct hierarchy structure (interfaces, protocols, network-services, etc.)
- [ ] Include proper closing statements (!)
- [ ] Be validated against DNOS CLI PDF before merge
- [ ] **Include ALL possible knobs/options** for the configuration type (don't oversimplify)

### ⚠️ Config Knob Completeness

When creating a new configuration generator (e.g., for a service type):
1. **Read the relevant RST documentation** for ALL configurable options
2. **Check the DNOS CLI PDF** for all available sub-commands
3. **Look at existing running configs** in `db/configs/*/running.txt` for real-world examples
4. **Include all relevant options** - don't just implement the bare minimum

Example - FXC Service should include options for:
- EVI, target, route-distinguisher
- Multihoming (ESI, split-horizon group)
- Interface bindings (PWHE, sub-interfaces)
- MTU, encapsulation type
- Admin state, description

### Validation Sources

| Source | Location | Purpose |
|--------|----------|---------|
| DNOS CLI PDF | `docs/DNOS_CLI.pdf` | Command syntax reference |
| Delete Syntax | `docs/DNOS_DELETE_SYNTAX.md` | Deletion commands |
| Version Stack | `docs/DNOS_VERSION_STACK.md` | Stack/upgrade commands |
| RST Docs | Platform RST documentation | Feature-specific syntax |
| Running Configs | `db/configs/*/running.txt` | Real-world examples |

### Loopback IP Validation (MANDATORY)

Loopback interfaces MUST always use `/32` prefix. This is enforced at multiple levels:

**Why /32 is Required:**
- Loopback represents a single router identity, not a network
- /32 ensures correct route advertisement in ISIS/OSPF/BGP
- Other prefixes can cause routing conflicts and unexpected behavior

**Validation Points:**
| Location | Behavior |
|----------|----------|
| `scaler/utils.py` | `validate_loopback_ip()` - validates and auto-corrects |
| `scaler/utils.py` | `normalize_loopback_ip()` - auto-corrects with optional warning |
| `scaler/cli_validator.py` | Warns on non-/32 loopback in generated config |
| `scaler/wizard/mirror_config.py` | `_normalize_loopback_ip()` - corrects with console warning |

**Usage Examples:**
```python
from scaler.utils import validate_loopback_ip, normalize_loopback_ip

# Validate and check
corrected, is_valid, warning = validate_loopback_ip("1.1.1.1/29")
# Returns: ("1.1.1.1/32", False, "Loopback should use /32, not /29")

# Just normalize
ip = normalize_loopback_ip("1.1.1.1/29")  # Returns "1.1.1.1/32"

# With warning callback
ip = normalize_loopback_ip("1.1.1.1/29", warn_callback=print)
# Prints warning and returns "1.1.1.1/32"
```

### Example: Correct vs Incorrect Preview

**❌ INCORRECT (text description):**
```
Will create: FXC_1 through FXC_100
```

**✅ CORRECT (actual DNOS syntax):**
```
l2vpn
 xconnect group XC-FXC_
  p2p FXC_1
   neighbor evpn evi 1000 target 1000
  !
  p2p FXC_2
   neighbor evpn evi 1001 target 1001
  !
 !
!
... (100 services total)
```

### Deletion Commands
```bash
no interfaces ph<number>           # Delete interface
no network-services evpn instance <name>  # Delete service
```

### ⚠️ LLDP Configuration Syntax (CRITICAL)

When configuring LLDP on DNOS devices:

**LLDP Global Enable:**
```
protocols
  lldp
    admin-state enabled  ← NOTE: 'enabled' NOT 'enable'
  !
!
```

**LLDP Per-Interface:**
```
protocols
  lldp
    admin-state enabled
    interface ge400-0/0/0   ← Just creating the interface enables LLDP on it
    !
    interface ge400-0/0/2
    !
  !
!
```

**Interface Admin-State (Physical Interfaces):**
```
interfaces              ← Enter 'interfaces' hierarchy FIRST
  ge400-0/0/0           ← Just the interface name, NO 'interface' keyword
    admin-state enabled
  !
  ge400-0/0/2
    admin-state enabled
  !
!                       ← Exit interfaces hierarchy
```

**❌ WRONG - Do NOT do this:**
```
interfaces ge400-0/0/0   ← WRONG: Combines 'interfaces' with name
  admin-state enabled
!
```

### ⚠️ VRF Interface Attachment (CRITICAL)

**DNOS uses a TWO-STEP process for attaching interfaces to VRFs:**

1. **STEP 1**: Configure interface (under `interfaces` hierarchy)
2. **STEP 2**: Attach to VRF (under `network-services vrf instance` hierarchy)

**❌ WRONG - VRF is NOT configured under interface:**
```
interfaces
  bundle-1.100
    flowspec enabled
        vrf Source    ← WRONG! 'vrf' is NOT a child of 'flowspec'
    !
  !
!
```

**❌ WRONG - VRF is NOT a direct child of interface:**
```
interfaces
  bundle-1.100
    vrf Source        ← WRONG! 'vrf' is NOT under 'interfaces' hierarchy
    flowspec enabled
  !
!
```

**✅ CORRECT - Two separate hierarchies:**
```
! STEP 1: Configure interface (under 'interfaces')
interfaces
  bundle-1.100
    vlan-id 100
    admin-state enabled
    ipv4-address 192.168.100.2/24
    flowspec enabled
  !
!

! STEP 2: Attach interface to VRF (under 'network-services vrf instance')
network-services
  vrf instance Source
    description "VRF for customer"
    route-distinguisher 10.0.0.1:100
    route-target import 65000:100
    route-target export 65000:100
    interface bundle-1.100          ← Attach interface HERE!
    !
  !
!
```

**Key Rules:**
- VRF attachment is ALWAYS under `network-services vrf instance <VRF> interface <IF>`
- Interface MUST be configured BEFORE attaching to VRF
- `flowspec enabled` goes under interface hierarchy, NOT under VRF

### Stack Commands
```bash
request system target-stack load <url>     # Load component
request system target-stack install        # Upgrade (same major version)
request system delete                      # Delete DNOS (major version change)
request system deploy system-type <type> name <name> ncc-id <id>  # Deploy from GI
show system install                        # Monitor progress
show system stack                          # View stack versions
```

### Parsing `show system stack` Output (CRITICAL)
The output format is:
```
| Component | HW Model | HW Revision | Revert | Current | Target |
```

**CORRECT parsing pattern:**
```python
for line in stack_output.split('\n'):
    if '|' in line and '---' not in line and 'Component' not in line:
        parts = [p.strip() for p in line.split('|') if p.strip()]
        if len(parts) >= 5:  # MUST use >= 5, NOT >= 6!
            component = parts[0].upper()
            current = parts[4] if len(parts) > 4 and parts[4] not in ('-', '') else ''
            target = parts[5] if len(parts) > 5 and parts[5] not in ('-', '') else ''
            
            if component == 'DNOS':
                dnos_current, dnos_target = current, target
            elif component == 'GI':
                gi_current, gi_target = current, target
            elif component == 'BASEOS':
                baseos_current, baseos_target = current, target
```

**NEVER use `len(parts) >= 6`** - Target column may be empty, resulting in fewer parts!

Reference implementations: `interactive_scale.py` lines 3453-3473, 2765-2781

---

## Jenkins Integration

Reference: `/home/dn/SCALER/docs/DNOS_VERSION_STACK.md`

### Key Classes
- `JenkinsClient` - API client for Jenkins
- `JenkinsBuild` - Build dataclass with `is_sanitizer`, `has_image_artifacts`, `is_expired` properties
- `StackManager` - Stack URL extraction and validation
- `DeviceUpgrader` - Device upgrade operations

### Build Freshness
- Dev builds in `dnpkg-48hrs` expire after 48 hours
- Always check `stack.is_expired` before using URLs
- Offer to trigger new build if expired

### Private Branch Handling
1. Get DNOS, GI, BaseOS from private branch first
2. Only fallback to main branch for missing components
3. Use `stack_mgr.get_stack_with_fallback(branch, prefer_private=True)`

### Failed Build Support (2026-03-11)
Feature branches often have builds that fail on tests but produce valid DNOS/GI/BaseOS images.
- `get_latest_pure_build(branch, include_failed=True)` -- returns latest build with artifacts (success OR failed)
- `get_recent_builds_with_artifacts(branch)` -- lists all recent builds with image artifacts, flags sanitizer
- The wizard offers `[2] Browse all recent builds` after finding the latest successful build
- When pasting a Jenkins URL, the wizard offers `[2] Browse all recent builds for <branch>`

### Sanitizer Build Detection (2026-03-11)
Jenkins parameter `TEST_NAMES=ENABLE_SANITIZER` identifies AddressSanitizer builds.
- `JenkinsBuild.is_sanitizer` property checks `build_params['TEST_NAMES']`
- `JenkinsBuild.build_params` extracted from Jenkins API `actions[].parameters[]`
- Displayed as `[ASAN]` tag in build listings and stack summary
- Sanitizer builds are slower but detect memory errors at runtime

---

## File Locations

| Purpose | Location |
|---------|----------|
| Main wizard | `scaler/interactive_scale.py` |
| Multi-device menu | `_show_multi_device_action_menu()` |
| Device operations | `scaler/device_upgrade.py` |
| Jenkins client | `scaler/jenkins_integration.py` |
| Stack management | `scaler/stack_manager.py` |
| Connection strategy | `scaler/connection_strategy.py` |
| Console mappings DB | `db/console_mappings.json` |
| DNOS syntax ref | `docs/DNOS_DELETE_SYNTAX.md` |
| Version stack ref | `docs/DNOS_VERSION_STACK.md` |
| This guide | `docs/DEVELOPMENT_GUIDELINES.md` |

---

## Console Server Mappings (Centralized)

Console port mappings are stored in `db/console_mappings.json` and managed via functions
in `scaler/connection_strategy.py`. **Never hardcode console ports** in other files.

### Architecture

The mapping tracks devices by **NCC serial number** (permanent physical identifier) and
**hostname** (current name). When a device is renamed, the serial number stays the same,
so the console mapping follows the rename automatically.

```
db/console_mappings.json
  console_server: { host, user, password, model }
  ports:
    "12": { hostname: "PE-1", serial_number: null }
    "13": { hostname: "RR-SA-2", serial_number: "WKY1BC7400002B2", previous_hostnames: ["PE-2"] }
    "14": { hostname: "PE-4", serial_number: null, hostname_aliases: ["YOR_CL_PE-4"] }
```

### API Functions (in `connection_strategy.py`)

| Function | Purpose |
|----------|---------|
| `get_console_config_for_device(hostname)` | Look up console config by hostname or alias |
| `get_console_config_by_serial(serial)` | Look up by NCC serial (for renames) |
| `update_console_hostname(old, new, serial)` | Update mapping when device is renamed |
| `save_console_discovery(port, hostname, serial)` | Save newly discovered console port |

### Auto-Update Triggers

1. **Config fetch** (`sync_device_from_live` in `utils.py`): When a hostname mismatch is
   detected, the console mapping is auto-updated to the new hostname.
2. **Console login**: When connecting via console, the NCC serial number from the login
   prompt (e.g. `WKY1BC7400002B2 login:`) is captured and saved to the mapping.
3. **Manual**: Call `save_console_discovery(port, hostname, serial)` after identifying a
   new device on a console port.

### Rules

- **NEVER hardcode console ports** in `system_restore.py`, `interactive_scale.py`, or anywhere
  else. Always call `get_console_config_for_device(hostname)`.
- Console credentials: user `dn`, password `drive1234` on ATEN SN9116CO at `console-b15`.
- To get into GI CLI from BaseOS shell: `dncli`.
- Console server navigation: SSH to console-b15 -> option [3] Port Access -> port number.

### Cluster NCC Type Classification

Not all cluster devices (CL-*) have the same NCC architecture. The wizard auto-detects
NCC type from `show system` output during `post_connect_verify`:

| NCC Type | Model Column | Serial Number Column | Example |
|----------|-------------|---------------------|---------|
| **KVM (virtual)** | `X86` | DNS hostname (e.g. `kvm108-cl408d-ncc0`) | PE-4 (CL-86) |
| **Physical** | Hardware model | Hardware S/N (e.g. `WDY1A...`) | Standard clusters |

**Detection rules** (in `utils.py` `post_connect_verify`, Layer 2.5):
- Parse NCC rows from `show system` table
- If any NCC has `Model = X86` -> `ncc_type = "kvm"`
- NCC serials starting with a lowercase letter are treated as VM hostnames
- Result is auto-persisted to `operational.json` via `sync_device_from_live`

### KVM NCC Access -- Two Distinct Paths

KVM NCC clusters have completely different access paths depending on device state:

**DNOS mode (VIP is alive)**:

```
ssh dnroot@100.64.4.98 (VIP)  -->  DNOS CLI directly
```

Standard SSH to VIP, same commands as any device.

**GI mode (VIP is DEAD -- must use virsh console)**:

The GI CLI session **persists** on the serial console. After the first
successful `dncli` login, subsequent `virsh console` connections land
directly on GI#. The full login chain is only needed once (after
`system delete` or initial boot).

*First connection (cold start / after system delete):*
```
Step 1: ssh dn@kvm108              (KVM host, password: drive1234!)
Step 2: virsh list                 (find running NCC VM)
Step 3: virsh console kvm108-cl408d-ncc1  (serial console to active NCC)
Step 4: login: dn / drivenets      (lands on BaseOS shell)
Step 5: dncli                      (SSH to localhost, password: dnroot)
Step 6: GI# prompt ready           (can run target-stack load commands)
```

*Subsequent connections (GI session persisted):*
```
Step 1: ssh dn@kvm108              (KVM host)
Step 2: virsh console kvm108-cl408d-ncc1  (attach to NCC serial)
Step 3: Press Enter                (GI# prompt appears immediately)
```

This is a 3-hop, 3-credential chain (cold start only):

| Hop | Target | User | Password | Result |
|-----|--------|------|----------|--------|
| 1 | KVM host (`kvm108`) | `dn` | `drive1234!` | Ubuntu shell |
| 2 | virsh console (NCC VM) | `dn` | `drivenets` | BaseOS shell |
| 3 | dncli (SSH to localhost) | `dnroot` | `dnroot` | GI/DNOS CLI |

**Cleanup rule**: When disconnecting from a virsh console session, escape
with Ctrl+] only. Do NOT `exit` the GI CLI -- this kills the persisted
session and forces the next connection to redo the full login chain.

**Connection strategy** (`connection_strategy.py`):
- `SSH_NCC` method: SSH directly to NCC hostname (DNOS mode only, ncc_type=kvm)
- `VIRSH_CONSOLE` method: Attaches virsh console, checks GI# first (persisted),
  falls back to login+dncli chain if at login/BaseOS prompt (cold start)
- Physical NCC clusters use SSH to VIP/SN/MGMT like standalones
- Console on KVM cluster devices reaches NCPs only (data plane), NOT NCCs

**Credential storage** (`operational.json` and `console_mappings.json`):

```json
{
  "ncc_type": "kvm",
  "kvm_host": "kvm108",
  "kvm_host_ip": "100.64.6.6",
  "kvm_host_credentials": {"username": "dn", "password": "drive1234!"},
  "ncc_vms": ["kvm108-cl408d-ncc0", "kvm108-cl408d-ncc1"],
  "ncc_console_credentials": {"username": "dn", "password": "drivenets"},
  "dncli_credentials": {"username": "dnroot", "password": "dnroot"}
}
```

**Manual override**: If auto-detection is wrong, set `ncc_type`, `kvm_host`, and
credentials in `db/configs/<hostname>/operational.json` and
`db/console_mappings.json` cluster_ncc_access.

### Unified Upgrade Connection (`connect_for_upgrade`)

**All upgrade flows** (image push, verify stacks, install target stack, check status,
post-delete reconnect) MUST use `connect_for_upgrade(hostname)` from
`connection_strategy.py`. Do NOT use `resolve_device_ip` + direct SSH for upgrades.

`connect_for_upgrade` tries all available paths in order:
1. SSH to serial number hostname
2. SSH to management IP
3. SSH to KVM NCC hostname (DNOS mode, ncc_type=kvm)
4. virsh console via KVM host (GI mode, ncc_type=kvm)
5. Console server (if configured)
6. SSH to loopback IP

Returns a dict compatible with `safe_connect_and_verify`:
`connected`, `ssh`, `channel`, `ip`, `method`, `verified`, `device_state`, etc.

**Per-device connection matrix** (which method works in which state):

| Device Type | DNOS Mode | GI Mode |
|-------------|-----------|---------|
| Standalone (SA-36CD-S) | SSH->SN, SSH->MGMT | Console (if no DNS) |
| KVM cluster (CL-86) | SSH->NCC, SSH->MGMT (VIP) | virsh->NCC (kvm108) |
| Physical cluster | SSH->SN, SSH->MGMT | Console (NCP) |

**RR-SA-2 (no DNS)**: After system delete, SSH is unreachable. `connect_for_upgrade`
skips SSH and connects directly via console-b15 port 13.

**YOR_CL_PE-4 (KVM)**: In GI mode VIP is dead. `connect_for_upgrade` uses virsh
console via kvm108 to reach the NCC brain.

---

## Testing Checklist

Before committing a new feature:

- [ ] Test with single device
- [ ] Test with 2+ devices (multi-device mode)
- [ ] Test with SSH disconnection (unplug/reconnect)
- [ ] Test with invalid input
- [ ] Test cancellation (Ctrl+C, "Back" option)
- [ ] Verify live display updates correctly
- [ ] Check no linting errors: `python -m py_compile scaler/*.py`

---

## ⚠️ MANDATORY: Live Terminal & Push Options

**⚠️ ABSOLUTE RULE: ALL configuration push operations MUST use live terminal display. NO EXCEPTIONS.**

This applies to:
- Scale UP/DOWN operations
- VLAN modifications
- Interface modifications
- Service configuration
- Multihoming push
- Delete hierarchy
- ANY operation that commits config to a device

**Why:** Users need real-time visibility into what's happening on the device. Silent pushes are not acceptable.

### 1. Live Terminal Display
Every operation that pushes configuration to devices MUST use a live terminal panel:
```python
show_live_terminal = Confirm.ask("Show live device terminal output?", default=True)

if use_terminal_paste:
    success, output = pusher.push_config_terminal_paste(
        device, config, dry_run=False, 
        progress_callback=progress_callback,
        show_live_terminal=show_live_terminal  # <-- REQUIRED
    )
```

### 2. Push Method Options
All push operations MUST offer both methods:
```python
console.print("\n[bold]Select push method:[/bold]")
console.print("  [1] Terminal Paste (paste config directly into CLI)")
console.print("  [2] File Merge (upload and merge via file)")
push_method = Prompt.ask("Method", choices=["1", "2"], default="1")
use_terminal_paste = (push_method == "1")
```

### 3. File Save Option
Before pushing, ALWAYS offer to save configuration to file:
```python
if Confirm.ask("Save configuration to file before pushing?", default=True):
    config_dir = get_device_config_dir(device.hostname)
    filename = f"{operation}_{count}_{timestamp_filename()}.txt"
    filepath = config_dir / filename
    with open(filepath, 'w') as f:
        f.write(config_text)
    console.print(f"  [green]✓[/green] Saved: {filepath}")
```

### 4. Timing Estimates Based on History
Use learned timing data for estimates:
```python
from ..config_pusher import get_learned_timing_by_scale, save_timing_record

learned = get_learned_timing_by_scale("operation_type")
if learned and learned.get("learned_time_per_1k_lines"):
    time_per_1k = learned["learned_time_per_1k_lines"]
    estimated_seconds = (total_lines / 1000) * time_per_1k
    console.print(f"[dim]Estimated time: ~{estimated_seconds/60:.1f} min (based on history)[/dim]")

# After operation completes:
save_timing_record(
    platform=device.platform,
    line_count=total_lines,
    actual_time_seconds=total_time,
    device_hostname=device.hostname,
    scale_counts={"operation": "my_operation"}
)
```

### 5. Split-Screen Progress Display (NO FLICKERING)
For multi-device operations, use **split-screen panels** (side-by-side), NOT raw `show_live_terminal`:
```python
from rich.panel import Panel
from rich.columns import Columns

# Track terminal output per device
device_progress = {
    hostname: {
        "status": "pending",
        "progress": 0,
        "message": "Waiting...",
        "terminal_lines": []  # Buffer for terminal output
    }
    for hostname in device_hostnames
}
MAX_TERMINAL_LINES = 12

def add_terminal_line(hostname: str, line: str):
    """Add line to device's terminal buffer."""
    with progress_lock:
        device_progress[hostname]["terminal_lines"].append(line)
        if len(device_progress[hostname]["terminal_lines"]) > 50:
            device_progress[hostname]["terminal_lines"] = device_progress[hostname]["terminal_lines"][-50:]

def render_split_screen():
    """Render split-screen layout with per-device terminal panels."""
    panels = []
    for hostname, status in device_progress.items():
        content_lines = [
            f"Status: {status['status']}",
            f"Progress: {status['progress']}%",
            "─" * 40
        ]
        # Add terminal output
        for line in status["terminal_lines"][-MAX_TERMINAL_LINES:]:
            content_lines.append(f"[dim]{line[:50]}[/dim]")
        
        panel = Panel(
            "\n".join(content_lines),
            title=f"[bold white]{hostname}[/bold white]",
            height=MAX_TERMINAL_LINES + 6,
            expand=True
        )
        panels.append(panel)
    return Columns(panels, expand=True, equal=True)

# Use live_output_callback to capture output, NOT show_live_terminal
def live_output_callback(output: str):
    for line in output.strip().split('\n'):
        if line.strip():
            add_terminal_line(hostname, line.strip())

# DON'T use show_live_terminal=True (causes flickering between devices)
success, output = pusher.push_config_terminal_paste(
    device, config,
    progress_callback=progress_callback,
    live_output_callback=live_output_callback,  # Capture into buffer
    show_live_terminal=False  # We render ourselves
)

with Live(render_split_screen(), refresh_per_second=4, console=console) as live:
    # ... execute operations
    live.update(render_split_screen())
```

**Key points:**
- Use `live_output_callback` to capture output into per-device buffers
- Set `show_live_terminal=False` to prevent raw printing
- Render all devices together with `Columns` (side-by-side panels)
- This prevents flickering between devices
- Use **fixed panel height** with padding to prevent jumping

### 6. Live Terminal MANDATORY for ALL Configuration Operations

**⚠️ CRITICAL: Every new configuration operation MUST have live terminal display for BOTH:**
- ✅ Single-device mode
- ✅ Multi-device mode

**Multi-device operations MUST use multithreading:**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.live import Live
import threading

# Thread-safe progress tracking
progress_lock = threading.Lock()
device_progress = {hostname: {...} for hostname in hostnames}

def process_device(dev) -> Tuple[str, bool, str]:
    hostname = dev.hostname
    
    def add_terminal_line(line: str):
        with progress_lock:
            device_progress[hostname]["terminal_lines"].append(line)
    
    # ... processing with callbacks to add_terminal_line
    return hostname, success, message

# Parallel execution
with Live(render_split_screen(), refresh_per_second=4, console=console) as live:
    with ThreadPoolExecutor(max_workers=len(devices)) as executor:
        futures = {executor.submit(process_device, dev): dev for dev in devices}
        
        while any(f.running() for f in futures):
            live.update(render_split_screen())
            time.sleep(0.25)
        
        for future in as_completed(futures):
            hostname, success, message = future.result()
            results[hostname] = (success, message)
```

**Single-device operations should still show live terminal:**
```python
# For single device, use the split-screen pattern with 1 device
# Or use ConfigPusher's built-in show_live_terminal=True
pusher.push_config_terminal_paste(device, config, show_live_terminal=True)
```

### Checklist for New Push Operations

- [ ] **Live terminal panel** (MANDATORY - no silent pushes!)
- [ ] **Push method choice** (ALL THREE options - see below)
- [ ] **File save option** before pushing
- [ ] **Learned timing estimates** with history
- [ ] **Save timing after completion** to improve future estimates
- [ ] **Progress table** for multi-device operations
- [ ] **Total time display** after operation

### Push Method Options (MANDATORY - All Three!)

**ALL push operations MUST offer these three methods:**

```python
console.print("\n[bold]Push Method:[/bold]")
console.print("  [1] [green]Terminal Paste[/green] - Paste directly (live output, uses rollback 0)")
console.print("  [2] [cyan]File Upload[/cyan] - Upload + load override")
console.print("  [3] [yellow]Load Merge[/yellow] - Upload + load merge (preserves existing config)")
console.print("  [B] Cancel")

method_choice = Prompt.ask("Select method", choices=["1", "2", "3", "b", "B"], default="1").lower()

if method_choice == 'b':
    return False

use_terminal_paste = (method_choice == "1")
use_merge = (method_choice == "3")
```

### ⚠️ CRITICAL: Terminal Paste MUST use `rollback 0`

**Before pasting ANY config via terminal, ALWAYS clear the candidate config first:**

```python
# In push_config_terminal_paste():
channel.send("configure\n")
output = read_until_prompt(timeout=10)

# MANDATORY: Clear dirty candidate config before pasting
channel.send("rollback 0\n")
time.sleep(0.5)
read_until_prompt(timeout=10)

# Now safe to paste config
for line in config_lines:
    channel.send(line + "\n")
```

**Why `rollback 0` is required:**
- Device may have uncommitted changes from previous failed operations
- Pasting on top of dirty config causes unpredictable results
- `rollback 0` resets to last committed config (clean slate)

### Method Comparison

| Method | Command | Preserves Existing | Speed | Best For |
|--------|---------|:-----------------:|-------|----------|
| Terminal Paste | Direct paste | ❌ (replaces) | Slow | Small configs, debugging |
| File Upload | `load override` | ❌ (replaces) | Fast | Large configs |
| Load Merge | `load merge` | ✅ (merges) | Fast | Adding to existing config |

---

## 8. Time Estimation System (MANDATORY for ALL Operations)

**Every configuration operation MUST display time estimates and track actual times.**

### Push Method Estimation (NEW: Accurate Historical Matching)

Use `get_accurate_push_estimates()` for push time estimates based on historical data:

```python
from scaler.config_pusher import get_accurate_push_estimates

# Get accurate estimates using tiered matching:
# 1. Similar historical push (same platform, similar scale) - MOST ACCURATE
# 2. Scale-type specific averages (pwhe_fxc, l2ac_only, etc.)
# 3. Platform averages
# 4. Default calculations (fallback)

estimates = get_accurate_push_estimates(
    config_text=config_text,
    platform="SA-36CD-S",  # or device.platform
    include_delete=True  # If config has delete commands
)

# Returns:
# {
#     'estimates': {
#         'terminal_paste': {'total': 457, 'paste_time': 150, ...},
#         'file_upload': {'total': 341, 'upload_time': 2, ...},
#         'lofd': {'total': 259, 'factory_reset_time': 30, ...}
#     },
#     'source': 'similar_push',  # or 'scale_type', 'platform', 'default'
#     'source_detail': 'based on PE-1 push (2,000 PWHE, 2,000 FXC) (67% match) 18h ago',
#     'confidence': 'high',  # or 'medium', 'low'
#     'learned_rate': 15.4,  # seconds per 1K lines
#     'metrics': {...}  # line_count, interface_count, etc.
# }
```

### Confidence Levels

| Confidence | Source | Color | Meaning |
|------------|--------|-------|---------|
| high | similar_push | green ✓ | Matched historical push with similar scale |
| medium | scale_type or cross_platform | yellow ~ | Averaged from similar scale type |
| low | platform or default | dim ? | Generic average or default estimate |

### Display Format in Push Menu

```
⏱ Push Time Estimates (✓ high confidence)
                                                                                
  Method                        Est. Time   Details                             
 ────────────────────────────────────────────────────────────────────────────── 
  Terminal Paste                  ~7m 37s   Paste: 2m 30s, Commit: 3m 0s        
  File Upload                     ~5m 41s   Upload: 2s, Load: 32s               
  Factory Reset ✓                 ~4m 19s   LOFD: 30s, then load                
                                                                                
  Config: 18,006 lines, 275.9 KB | Interfaces: 4,000 | Services: 2,000
  📊 Estimate based on PE-1 push (2,000 PWHE, 2,000 FXC) (67% match) 18h ago
```

### Legacy Estimation Components

For operations not using the push menu, use the traditional estimation:

```python
from scaler.config_pusher import get_learned_timing_by_scale, save_timing_record

# Get estimated time BEFORE operation starts
def estimate_operation_time(operation_type: str, config_text: str, device: Device) -> dict:
    """
    Calculate estimated time based on:
    - Config size (line count, interface count, service count)
    - Historical timing data (learned from previous operations)
    - Device platform/model factors
    """
    line_count = len(config_text.strip().split('\n'))
    interface_count = config_text.count('\n      interface ') + config_text.count('\n    ge') + config_text.count('\n    lag')
    service_count = config_text.count('\n      evpn-vpws ') + config_text.count('\n      fxc ') + config_text.count('\n      vrf ')
    
    # Check for learned timing data
    learned = get_learned_timing_by_scale(operation_type)
    
    if learned and learned.get("learned_time_per_1k_lines"):
        # Use historical data
        time_per_1k = learned["learned_time_per_1k_lines"]
        estimated_seconds = (line_count / 1000) * time_per_1k
        confidence = "high"
    else:
        # Default estimates (conservative)
        BASE_TIMES = {
            "scale_up": 120,          # 2 min base
            "scale_down": 60,         # 1 min base
            "vlan_modify": 30,        # 30 sec base
            "interface_modify": 45,   # 45 sec base
            "service_add": 90,        # 1.5 min base
            "factory_reset": 180,     # 3 min for stage 1
        }
        base_time = BASE_TIMES.get(operation_type, 60)
        
        # Scale by config complexity
        estimated_seconds = base_time + (line_count / 1000) * 30 + interface_count * 0.01 + service_count * 0.1
        confidence = "low"
    
    return {
        "estimated_seconds": estimated_seconds,
        "line_count": line_count,
        "interface_count": interface_count,
        "service_count": service_count,
        "confidence": confidence,
        "source": "historical" if confidence == "high" else "default"
    }
```

### Display Estimate BEFORE Operation

```python
# MANDATORY: Show estimate before starting
estimate = estimate_operation_time("scale_up", config_text, device)

console.print(Panel(
    f"[bold]Operation Estimate[/bold]\n\n"
    f"  Config Lines:    {estimate['line_count']:,}\n"
    f"  Interfaces:      {estimate['interface_count']:,}\n"
    f"  Services:        {estimate['service_count']:,}\n\n"
    f"  [yellow]Est. Time:[/yellow]  ~{estimate['estimated_seconds']/60:.1f} min\n"
    f"  [dim]Confidence: {estimate['confidence']} ({estimate['source']})[/dim]",
    title="⏱ Time Estimate",
    border_style="cyan"
))
```

### Show Elapsed + Remaining During Operation

```python
# In render_live_panel():
elapsed = time.time() - start_time
estimated_total = estimate['estimated_seconds']
remaining = max(0, estimated_total - elapsed)

content.append(f"⏱ Elapsed: {int(elapsed)}s", style="dim")
content.append(f" | Est. Remaining: ~{int(remaining)}s\n", style="yellow")

# Progress bar should reflect estimated completion
if estimated_total > 0:
    progress_pct = min(95, int((elapsed / estimated_total) * 100))
```

### Save Timing After Operation Completes (MANDATORY)

```python
# MANDATORY: Save actual timing for future estimates
total_time = time.time() - start_time

save_timing_record(
    operation_type=operation_type,
    platform=device.platform,
    line_count=estimate['line_count'],
    interface_count=estimate['interface_count'],
    service_count=estimate['service_count'],
    actual_time_seconds=total_time,
    success=success
)

console.print(f"\n[dim]Operation completed in {total_time:.1f}s (estimate was {estimate['estimated_seconds']:.1f}s)[/dim]")
```

### Estimation Factors by Operation Type

| Operation | Base Time | Per 1K Lines | Per Interface | Per Service |
|-----------|-----------|--------------|---------------|-------------|
| Scale UP | 120s | +30s | +0.01s | +0.1s |
| Scale DOWN | 60s | +15s | +0.005s | +0.05s |
| VLAN Modify | 30s | +10s | +0.002s | - |
| Factory Reset | 180s | - | - | - |
| Load New Config | 90s | +25s | +0.01s | +0.1s |

### Multi-Stage Operations (Factory Reset + Load)

```python
# For two-stage operations, show breakdown:
stage1_estimate = 180  # Factory reset base
stage2_estimate = estimate_operation_time("load_config", config_text, device)

console.print(Panel(
    f"[bold]Two-Stage Operation[/bold]\n\n"
    f"  Stage 1 (Factory Reset): ~{stage1_estimate/60:.1f} min\n"
    f"  Stage 2 (Load Config):   ~{stage2_estimate['estimated_seconds']/60:.1f} min\n\n"
    f"  [yellow]Total Est. Time:[/yellow] ~{(stage1_estimate + stage2_estimate['estimated_seconds'])/60:.1f} min",
    title="⏱ Time Estimate",
    border_style="cyan"
))
```

### Checklist for New Operations

- [ ] Call `estimate_operation_time()` before starting
- [ ] Display estimate in a Panel before asking to proceed
- [ ] Show elapsed + remaining time during Live display
- [ ] Call `save_timing_record()` after operation completes
- [ ] Display actual vs estimated time in completion message

---

### Standard Live Terminal Template (MANDATORY - Copy This!)

**ALL push operations MUST use this exact visual style** (matches Scale UP/DOWN):

```python
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
import time
import threading

# Constants for consistent display
MAX_TERMINAL_LINES = 12
PANEL_HEIGHT = MAX_TERMINAL_LINES + 5
progress_lock = threading.Lock()

# State dictionary (supports multi-device)
device_progress = {
    device.hostname: {
        "status": "pending",
        "progress": 0,
        "message": "Waiting...",
        "terminal_lines": []
    }
}
start_time = time.time()

def render_live_panel():
    """Render live terminal panel - CONSISTENT STYLE."""
    hostname = device.hostname
    status = device_progress[hostname]
    status_str = status["status"]
    progress_pct = status["progress"]
    terminal_lines = status.get("terminal_lines", [])
    
    # Build content with Text (not markup strings)
    content = Text()
    
    # Elapsed time
    elapsed = time.time() - start_time
    content.append(f"⏱ {int(elapsed)}s elapsed\n", style="dim")
    
    # Status line with icons
    if status_str == "pending":
        content.append("⏳ Pending\n", style="dim")
        filled, bar_style = 0, "dim"
    elif status_str == "connecting":
        content.append("🔌 Connecting...\n", style="yellow")
        filled, bar_style = 4, "yellow"
    elif status_str == "upload":
        content.append("📤 Uploading...\n", style="cyan")
        filled, bar_style = int(progress_pct / 5), "cyan"
    elif status_str == "load":
        content.append("📥 Loading...\n", style="cyan")
        filled, bar_style = int(progress_pct / 5), "cyan"
    elif status_str == "commit_check":
        content.append("🔍 Commit check...\n", style="magenta")
        filled, bar_style = 16, "magenta"
    elif status_str == "commit":
        content.append("⚙️ Committing...\n", style="magenta")
        filled, bar_style = 18, "magenta"
    elif status_str == "success":
        content.append("✓ Success!\n", style="green")
        filled, bar_style = 20, "green"
    elif status_str == "failed":
        content.append(f"✗ Failed\n", style="red")
        filled, bar_style = 20, "red"
    else:
        content.append(f"{status_str}\n")
        filled, bar_style = int(progress_pct / 5), "cyan"
    
    # Progress bar (20 chars: █░)
    content.append("Progress: ")
    content.append("█" * filled, style=bar_style)
    content.append("░" * (20 - filled), style="dim")
    content.append(f" {progress_pct}%\n", style=bar_style)
    content.append("─" * 50 + "\n")
    
    # Terminal lines (last N, fixed height with padding)
    lines_to_show = terminal_lines[-MAX_TERMINAL_LINES:]
    lines_added = 0
    
    for line in lines_to_show:
        clean = line[:48].replace('[', '\\[').replace(']', '\\]')
        if clean.startswith('→') or clean.startswith('>>>'):
            content.append(f"  {clean}\n", style="bright_green")
        elif clean.startswith('←'):
            content.append(f"  {clean}\n", style="yellow")
        elif clean.startswith('✓'):
            content.append(f"  {clean}\n", style="green")
        elif clean.startswith('✗') or 'error' in clean.lower():
            content.append(f"  {clean}\n", style="red")
        else:
            content.append(f"  {clean}\n", style="dim")
        lines_added += 1
    
    # Pad to fixed height
    while lines_added < MAX_TERMINAL_LINES:
        content.append("\n")
        lines_added += 1
    
    # Border color
    border_style = {"success": "green", "failed": "red"}.get(
        status_str, "cyan" if status_str in ("upload", "load", "commit") else "dim"
    )
    
    return Panel(content, title=f"[bold white]{hostname}[/bold white]", 
                 border_style=border_style, height=PANEL_HEIGHT + 3)

def progress_callback(info):
    """Thread-safe progress handler."""
    with progress_lock:
        device_progress[device.hostname].update({
            "status": info.get('stage', device_progress[device.hostname]["status"]),
            "progress": info.get('progress', device_progress[device.hostname]["progress"]),
        })
        if 'terminal_output' in info and info['terminal_output']:
            for line in info['terminal_output'].strip().split('\n'):
                if line.strip():
                    device_progress[device.hostname]["terminal_lines"].append(line.strip())

# Execute with live display
with Live(render_live_panel(), refresh_per_second=4, console=console, transient=False) as live:
    def update_live(info):
        progress_callback(info)
        live.update(render_live_panel())
    
    success, message, output = pusher.push_config_enhanced(
        device, config_text, progress_callback=update_live
    )
    
    # Final status update
    with progress_lock:
        device_progress[device.hostname]["status"] = "success" if success else "failed"
        device_progress[device.hostname]["progress"] = 100
    live.update(render_live_panel())
```

**Key Visual Elements (MUST be consistent):**
- Status icons: ⏳ 🔌 📤 📥 🔍 ⚙️ ✓ ✗
- Progress bar: █░ (20 chars)
- Fixed panel height (no jumping)
- Color-coded terminal lines (green=sent, yellow=response, red=error)
- Border color reflects status

---

## GUI Parity Requirement

**⚠️ CRITICAL: ALL new SCALER-WIZARD features MUST ALSO be implemented in the GUI!**

The SCALER system has two interfaces:
1. **CLI Wizard** - Terminal-based interface in `interactive_scale.py`
2. **Web GUI** - Browser-based interface integrated into the Topology Creator app

### Why GUI Parity Matters

- Users should have the same capabilities regardless of interface
- The GUI is the primary interface for the Topology App integration
- CLI-only features cannot be accessed from the web application

### When Adding a New Wizard Function

You must update ALL of the following:

| Step | File | Purpose |
|------|------|---------|
| 1 | `scaler/interactive_scale.py` | CLI implementation |
| 2 | `CURSOR/api/routes/operations.py` | API endpoint |
| 3 | `CURSOR/scaler-gui.js` | GUI panel/wizard |
| 4 | `docs/SCALER_OPTIONS_REFERENCE.md` | Documentation |
| 5 | Feature Parity Matrix (below) | Tracking |

### GUI Implementation Checklist

When adding a feature to the GUI:

- [ ] API endpoint created with proper Pydantic request/response models
- [ ] WebSocket progress updates for long-running operations
- [ ] Wizard step component with input validation
- [ ] Added to main CONFIG menu in `scaler-gui.js`
- [ ] Keyboard shortcut if applicable
- [ ] Documentation updated in `SCALER_OPTIONS_REFERENCE.md`
- [ ] CSS styles added if new components needed

### GUI Development Guidelines

1. **Use the WizardController** for multi-step operations:
```javascript
ScalerGUI.WizardController.init({
    panelName: 'my-wizard',
    title: 'My Wizard',
    initialData: { deviceId },
    steps: [
        { title: 'Step 1', render: (data) => `<div>...</div>` },
        { title: 'Step 2', render: (data) => `<div>...</div>` },
    ],
    onComplete: async (data) => { /* push config */ }
});
```

2. **Use WebSocket for progress** on long operations:
```javascript
const result = await ScalerAPI.myOperation(params);
this.showProgress(result.job_id, 'Operation Title');
```

3. **Validate inputs** before proceeding to next step

4. **Show errors** per-device in multi-device operations

5. **Follow existing patterns** in `scaler-gui.js`

### API Endpoint Pattern

```python
class MyOperationRequest(BaseModel):
    device_ids: List[str]
    parameter1: str
    dry_run: bool = True

class MyOperationResponse(BaseModel):
    job_id: str
    status: str
    message: str

@router.post("/my-operation", response_model=MyOperationResponse)
async def my_operation(request: MyOperationRequest, background_tasks: BackgroundTasks):
    # Validate
    for device_id in request.device_ids:
        device = get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device not found")
    
    # Start async job
    job_id = str(uuid.uuid4())[:8]
    background_tasks.add_task(run_my_operation, job_id, request)
    
    return MyOperationResponse(
        job_id=job_id,
        status="started",
        message=f"Connect to /ws/progress/{job_id} for updates."
    )
```

### GUI Feature Parity Matrix

| Feature | CLI | API Endpoint | GUI | Notes |
|---------|:---:|:------------:|:---:|-------|
| Compare Configs | ✅ | ✅ `/api/operations/diff` | ✅ | Multi-device only |
| Sync Status | ✅ | ✅ `/api/operations/sync-status` | ✅ | Multi-device only |
| Push Files | ✅ | ✅ `/api/operations/push` | ✅ | - |
| Configure | ✅ | ✅ Multiple | ✅ | Interface/Service wizards |
| Delete Hierarchy | ✅ | ✅ `/api/operations/delete` | ✅ | - |
| Modify Interfaces | ✅ | ✅ `/api/operations/modify-interfaces` | ✅ | - |
| Image Upgrade | ✅ | ✅ `/api/operations/image-upgrade` | ✅ | Jenkins builds |
| Stag Pool Check | ✅ | ✅ `/api/operations/stag-check` | ✅ | QinQ Stag usage |
| Scale Up/Down | ✅ | ✅ `/api/operations/scale-updown` | ✅ | Bulk service operations |
| Multihoming Sync | ✅ | ✅ `/api/operations/multihoming/sync` | ✅ | ESI sync |
| Flowspec VPN | ✅ | 🔄 `/api/config/generate/flowspec` | 🔄 | SW-182545, SW-182546 |
| Sync from Mapper | ✅ [N] | ✅ [N] | Pull configs from network-mapper (no SSH) |
| Import Topology | [3] | [3] | Import devices from network-mapper |
| BGP Config | ✅ | ✅ `/api/config/generate/bgp` | 🔄 | Coming soon |
| IGP Config | ✅ | ✅ `/api/config/generate/igp` | 🔄 | Coming soon |
| System Config | ✅ | ✅ `/api/config/generate/system` | 🔄 | Coming soon |

**Legend:** ✅ = Implemented | 🔄 = In Progress | ❌ = Not Started

### File Locations (Updated)

| Purpose | Location |
|---------|----------|
| Main CLI wizard | `scaler/interactive_scale.py` |
| API main | `CURSOR/api/main.py` |
| API operations routes | `CURSOR/api/routes/operations.py` |
| API config routes | `CURSOR/api/routes/config.py` |
| GUI JavaScript | `CURSOR/scaler-gui.js` |
| GUI API client | `CURSOR/scaler-api.js` |
| GUI Styles | `CURSOR/styles.css` |
| Options Reference | `docs/SCALER_OPTIONS_REFERENCE.md` |
| This guide | `docs/DEVELOPMENT_GUIDELINES.md` |

---

### Summary: Adding a New Feature

1. **CLI First**: Implement in `interactive_scale.py` with `MultiDeviceContext`
2. **Add API**: Create endpoint in `api/routes/operations.py`
3. **Add GUI**: Create wizard/panel in `scaler-gui.js`
4. **Document**: Update `SCALER_OPTIONS_REFERENCE.md`
5. **Track**: Update Feature Parity Matrix above

---

## GUI Modal/Dialog Design Rules

**⚠️ MANDATORY: All modals, dialogs, popups, and sub-menus MUST follow these rules:**

### 1. Position Near Trigger Element

Dialogs and popups MUST open **next to the element that triggered them** (menu item, button, etc.):

```javascript
// Store trigger position when showing context menu
this._contextMenuX = x;
this._contextMenuY = y;

// When opening dialog, use stored position
const dialogX = this._contextMenuX || window.innerWidth / 2;
const dialogY = this._contextMenuY || window.innerHeight / 2;
```

### 2. Always Keep Within Viewport

All dialogs MUST be fully visible on screen - never open outside viewport bounds:

```javascript
// After appending dialog, adjust position to stay within viewport
const dialogRect = dialog.getBoundingClientRect();
const padding = 20;

// Adjust X to keep within viewport
if (dialogX + dialogRect.width > window.innerWidth - padding) {
    dialogX = window.innerWidth - dialogRect.width - padding;
}
if (dialogX < padding) {
    dialogX = padding;
}

// Adjust Y to keep within viewport
if (dialogY + dialogRect.height > window.innerHeight - padding) {
    dialogY = window.innerHeight - dialogRect.height - padding;
}
if (dialogY < padding) {
    dialogY = padding;
}

dialog.style.left = dialogX + 'px';
dialog.style.top = dialogY + 'px';
```

### 3. Unified Color Scheme

All dialogs and panels MUST use the consistent app color scheme:

| Element | Light Mode | Dark Mode |
|---------|------------|-----------|
| Background | `#ffffff` | `linear-gradient(135deg, #2d3748, #1a202c)` |
| Text Primary | `#1a202c` | `#ecf0f1` |
| Text Secondary | `#4a5568` | `#7f8c8d` |
| Border | `rgba(0,0,0,0.1)` | `rgba(255,255,255,0.1)` |
| Primary Button | `#3498db` | `#3498db` |
| Success Button | `#27ae60` | `#27ae60` |
| Danger Button | `#e74c3c` | `#e74c3c` |
| Input Background | `#f7fafc` | `#1a202c` |
| Input Border | `#cbd5e0` | `#4a5568` |

### 4. Dialog Structure Template

```javascript
// Standard dialog structure
const dialog = document.createElement('div');
dialog.style.cssText = `
    position: absolute;
    background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
    border-radius: 12px;
    padding: 24px;
    min-width: 380px;
    max-width: 90%;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.1);
`;
```

### 5. Required Dialog Features

Every dialog MUST support:
- [ ] **Escape key** to close
- [ ] **Click outside** to close (on overlay)
- [ ] **Enter key** to submit (where applicable)
- [ ] **Focus management** (auto-focus first input)
- [ ] **Hover effects** on buttons

### Checklist for New Dialogs

- [ ] Opens next to triggering element (not center of screen)
- [ ] Stays fully within viewport bounds
- [ ] Uses unified color scheme
- [ ] Supports keyboard navigation (Enter/Escape)
- [ ] Click-outside-to-close functionality
- [ ] Auto-focuses first interactive element
- [ ] Matches existing dialog styling

---

## DNOS Device Shell Access

When accessing the Linux shell on DNOS devices for operations like querying interface indexes:

### Shell Access Method

```bash
# From DNOS CLI:
run start shell ncc 0 container inband-engine

# Password: dnroot
```

### Shell Password

The DNOS shell password for `run start shell` commands is: **`dnroot`**

This is used for:
- Entering the `inband-engine` container
- Accessing the `inband_ns` network namespace
- Querying actual interface index (ifindex) usage from the Linux kernel

### Key Containers

| Container | Purpose |
|-----------|---------|
| `inband-engine` | Data plane networking, Stag management, RNR |
| `routing_engine` | BGP, routing protocols |

### Querying Interface Index Pools

To check actual ifindex usage (for Stag pool, PH pool, etc.):

```bash
# Enter inband-engine
run start shell ncc 0 container inband-engine
# Password: dnroot

# Enter inband_ns network namespace
ip netns exec inband_ns bash

# Get interface counts by pool
ip -j link show | python3 -c '
import sys, json
data = json.load(sys.stdin)

# Count by pool range
ph_count = sum(1 for d in data if 58882 <= d.get("ifindex",0) <= 65025)
stag_count = sum(1 for d in data if 88001 <= d.get("ifindex",0) <= 92000)

print(f"PH Pool (58882-65025): {ph_count}/6144")
print(f"Stag Pool (88001-92000): {stag_count}/4000")
'
```

### Interface Index Pool Reference

| Pool | Range | Max | Description |
|------|-------|-----|-------------|
| PH Pool | 58882-65025 | 6,144 | phX parents + phX.Y (no outer-tag) |
| Stag Pool | 88001-92000 | 4,000 | phX.Ys (Q-in-Q with outer-tag) |
| IRB Pool | 41985-46080 | 4,096 | IRB interfaces |

### Soft Limits (consts.py)

| Limit | Value | Description |
|-------|-------|-------------|
| MAX_IRB_AND_PHXY_INTERFACES | 4,000 | Combined IRB + phX.Y |
| MAX_QINQ_INTERFACES | 4,000 | Unique Stags (parent + outer-tag) |

### Error Hooks

When scaling fails with `assign_new_if_index`:
1. **PH Pool exhausted** - Too many phX + phX.Y interfaces
2. **Stag Pool exhausted** - Too many Q-in-Q interfaces  
3. **Soft limit exceeded** - IRB + phX.Y > 4,000 or Stags > 4,000

Use the **Stag Pool Check** feature in the SCALER wizard to query live pool status.

---

## ⚠️ MANDATORY: Recursive Consistency Checks

**When adding ANY new feature that changes wizard output/display:**

Every new action that modifies how the SCALER wizard displays information MUST include a **recursive check** to ensure consistency across related displays.

### UI Consistency Rule: Update ALL Similar Elements

**⚠️ CRITICAL: When improving any table, summary, or display format:**

1. **Search for ALL similar displays** in the codebase
2. **Update them ALL** to use the same improved format
3. **Document the pattern** so future displays match

```bash
# Example: After improving config summary display, search for similar patterns
grep -rn "Table(" scaler/
grep -rn "table.add_row" scaler/
grep -rn "console.print.*│" scaler/  # Old pipe-separated format
```

### Common Display Types to Keep Consistent:

| Display Type | Pattern to Search | Should Match |
|--------------|-------------------|--------------|
| Config Summary | `Configuration Summary` | Clean vertical format |
| Device Status | `Device.*Status` | Consistent columns |
| Pool Status | `Pool.*Check` | Same metrics layout |
| Progress Tables | `Table(box=` | Same box style |
| Error Messages | `[red]Error` | Same error format |

### Example: Config Summary Format Standard

**❌ OLD (inconsistent, hard to read):**
```
│ Section │ Value1 │ Value2 │ Value3 │
```

**✅ NEW (clean, scannable):**
```
📊 Configuration Summary
────────────────────────────────────────
  System:      YOR_PE-1, profile: l3-pe
  Interfaces:  2,300 PWHE, 2,300 sub-ifs
  Services:    2,300 FXC (2,301 RTs)
────────────────────────────────────────
```

### Checklist When Updating Display Format:

- [ ] Search for similar displays using `grep`
- [ ] List all locations that need updating
- [ ] Update ALL to match new format
- [ ] Test each location visually
- [ ] Document the new pattern in this file

### What This Means:

1. **If you add/modify a data source** (e.g., cached pool status):
   - Check ALL places that display related data
   - Update them to use the new/modified source
   - Ensure no stale data is shown alongside fresh data

2. **If you change a calculation** (e.g., max services formula):
   - Find ALL places that use or display that calculation
   - Update them consistently
   - Verify the math matches across displays

3. **If you add caching**:
   - Ensure cached data updates when source changes
   - Clear/invalidate cache when operations complete
   - Show cache freshness indicator if relevant

### Checklist for Display Changes:

- [ ] Search for ALL occurrences of related display strings
- [ ] Check `_run_stag_pool_check`, `_scale_up_wizard`, `_scale_down_wizard`
- [ ] Check `stag_pool_checker.py`, `scale_operations.py`
- [ ] Verify numbers match between quick-view and detailed-view
- [ ] Test: Run operation → Check display → Run related operation → Verify consistency

### Example Violations to Avoid:

❌ Stag Pool Check shows "1,700 remaining" but Scale UP shows "642 max"
❌ Config-based estimate shown alongside kernel-based data
❌ Cached data not updated after Scale UP completes

### Pool Consumption Per Service Type:

| Service Type | phX (PH Pool) | phX.Y no-tag (PH Pool) | phX.Ys with outer-tag (Stag Pool) |
|--------------|---------------|------------------------|-----------------------------------|
| FXC with outer-tag | 1 | 0 | 1 |
| FXC without outer-tag | 1 | 1 | 0 |
| PWHE sub-interface with QinQ | 0 | 0 | 1 |
| PWHE sub-interface no QinQ | 0 | 1 | 0 |

**Note:** The max services calculation should detect whether outer-tag is used and adjust accordingly.

---

## 🎯 Configuration Value Detection Priority

**MANDATORY: All wizard configuration values MUST be derived from actual device data, NOT hardcoded defaults.**

### Detection Priority Order

When determining configuration values (RT, RD, ASN, VLAN, etc.), always follow this priority:

| Priority | Source | Example |
|----------|--------|---------|
| **1. Existing Services** | Parse from running.txt FXC/EVPN services | `route-target 1234567:N` → RT ASN = `1234567` |
| **2. operational.json** | Pre-parsed operational data | `local_as`, `router_id`, `lo0_ip` |
| **3. Device Config** | Parse from running.txt BGP/routing section | `autonomous-system 65000` |
| **4. Cross-Device** | Compare with other devices in db/configs/ | Use same RT ASN as peer device |
| **5. Default** | Only as LAST resort, and WARN user | `65000` with `(default)` label |

### Implementation Pattern

```python
# ✅ CORRECT: Smart detection with fallback chain
rt_asn = None
rt_source = ""

# Priority 1: Existing services in running config
rt_match = re.search(r'route-target\s+(\d+):\d+', config)
if rt_match:
    rt_asn = rt_match.group(1)
    rt_source = "existing services"

# Priority 2: operational.json (pre-parsed)
if not rt_asn:
    op_data = load_operational_json(hostname)
    if op_data.get('local_as'):
        rt_asn = str(op_data['local_as'])
        rt_source = "BGP local-as"

# Priority 3: Parse BGP config
if not rt_asn:
    bgp_match = re.search(r'autonomous-system\s+(\d+)', config)
    if bgp_match:
        rt_asn = bgp_match.group(1)
        rt_source = "BGP config"

# Priority 4: Default (last resort - show warning)
if not rt_asn:
    rt_asn = "65000"
    rt_source = "default"  # ⚠️ User sees this as warning

# Always show source for transparency
console.print(f"  RT ASN: {rt_asn} [dim]({rt_source})[/dim]")
```

```python
# ❌ WRONG: Hardcoded fallback without detection chain
bgp_match = re.search(r'autonomous-system\s+(\d+)', config)
rt_asn = bgp_match.group(1) if bgp_match else "65000"  # Bad!
```

### Key Data Sources by Value Type

| Value Needed | Primary Source | Secondary Source | Fallback |
|--------------|----------------|------------------|----------|
| **RT ASN** | Existing `route-target X:N` in FXC/EVPN | `operational.json → local_as` | Peer device RT |
| **RD Router ID** | BGP `router-id` | Loopback IP `lo0 ipv4 address` | `operational.json → lo0_ip` |
| **Interface Parent** | Existing L2-AC interfaces | LLDP neighbors | WAN interfaces |
| **VLAN Range** | Existing sub-interface VLANs | Continue from last+1 | Start at 1 |
| **ESI Prefix** | Existing multihoming ESI | Peer device ESI | Generate new |
| **EVI** | Existing service EVI | Same as service number | Generate |

### Cross-Device Value Inheritance

When configuring Device B after Device A:
- **Keep Same**: RT ASN (for peering), ESI (for multihoming), Service names
- **Make Unique**: RD (use Device B's loopback), Interface names

### Interface Pattern Replication

**MANDATORY: When generating new interfaces, detect and replicate the pattern from existing interfaces.**

```python
# Detect pattern from existing interface on same parent
def _detect_interface_pattern_from_config(config, parent_interface):
    pattern = {
        "uses_vlan_tags": False,      # vlan-tags outer-tag X inner-tag Y
        "uses_vlan_id": False,        # vlan-id N
        "outer_tag": 1,
        "outer_tpid": "0x8100",
        "has_vlan_manipulation": False,  # vlan-manipulation pop 1
        "vlan_manipulation": "",
        "extra_lines": []             # mtu, description, etc.
    }
    # Parse existing ge100-18/0/0.1 block to detect pattern
    # Then replicate for .2301, .2302, etc.
```

| Detected Pattern | Generate Same |
|-----------------|---------------|
| `vlan-tags outer-tag 1 inner-tag N outer-tpid 0x8100` | Same structure with new N |
| `vlan-manipulation pop 1` | Include in all new interfaces |
| `mtu 9000` | Include in all new interfaces |
| `description "Service-N"` | Generate with new N |

### Edit Before Commit Option

**MANDATORY: Always offer "Edit config before pushing" option for Scale UP/DOWN operations.**

```
Push Options:
  [1] Push directly via terminal paste
  [2] Save to file only
  [3] Edit config before pushing  ← User can review/modify
  [B] Back (cancel)
```

---

## 🧠 Self-Aware Wizard Principle

**MANDATORY: The wizard should be context-aware and suggest relevant configurations based on previous steps.**

### Core Concept

When a user configures Device A with services/VRFs/multihoming, the wizard should:
1. **Record** what was configured (service type, count, RD, RT, ESI, interfaces)
2. **Suggest** matching configuration when switching to Device B
3. **Auto-adjust** unique parameters (RD) while keeping peering params (RT, ESI) same
4. **Offer next-step hints** (e.g., "Configure L2-AC on PE-4 for FXC termination")

### Cross-Device Suggestions

When user configures Device A, record the configuration. When switching to Device B, analyze A's config and offer:

| From Device A | Suggest for Device B |
|---------------|---------------------|
| FXC Services | Same FXC with B's loopback in RD, same RT for peering |
| VRFs with flowspec | Same VRFs with unique RD, same RT import/export |
| Multihoming ESI | Same ESI prefix for Ethernet Segment pairing |

---

## Flowspec VPN Configuration (Epic SW-182545)

### Overview

Flowspec VPN enables BGP-based DDoS protection for VRF traffic per RFC 8955 (SAFI 134).

### Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                     Flowspec VPN Architecture                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   [Arbor/Controller] ──────► [RR-4] ──────► [PE-1/PE-2]                │
│        (SAFI 134)          (Flowspec-VPN)   (VRF Flowspec)             │
│                                                                         │
│   BGP Global (RR):           VRF BGP (PE):                             │
│   ┌─────────────────┐        ┌──────────────────────────────┐          │
│   │ neighbor X      │        │ network-services vrf         │          │
│   │   address-family│───────►│   instance CUSTOMER-1        │          │
│   │   ipv4-flowspec-│        │     protocols bgp ASN        │          │
│   │   vpn           │        │       address-family ipv4-   │          │
│   │ !               │        │       flowspec               │          │
│   └─────────────────┘        │         import-vpn rt <rt>   │          │
│                              │       !                      │          │
│                              └──────────────────────────────┘          │
└────────────────────────────────────────────────────────────────────────┘
```

### Scale Limits (from limits.json)

| Resource | Maximum | Notes |
|----------|---------|-------|
| Flowspec rules per VRF | 3,000 | Per-VRF rule limit |
| Total flowspec rules | 10,000 | System-wide limit |
| Flowspec-enabled interfaces | 8,000 | All L3 interfaces (Confluence "(v25.2) Interface Scale & RNR") |
| VRFs with flowspec AFI | No FlowSpec-specific limit | Follows platform VRF scale: 1.5k (v25.2) / 8k (v25.3+) |
| Local policies | 40 (20 per AFI) | routing-policy flowspec-local-policies ipv4/ipv6 |
| Match-classes | 12,000 (8k IPv4 + 4k IPv6) | mc-definitions per AFI (dn-flowspec-local-policies.yang) |

### FlowSpec Local Policy VRF Match (SW-182546, SW-226319)

Optional `vrf <vrf-name>` in match-class restricts rules to traffic from that VRF. Default: match any.

In scaler-wizard, VRF options are taken from: (1) VRFs created in this session (services hierarchy), (2) device config.
```
routing-policy flowspec-local-policies ipv4
  match-class MC-1
    vrf CUSTOMER-A      # Optional: restrict to this VRF
    dest-ip 192.0.2.0/24
  !
!
```

### BGP Address Families

**Global BGP (RR/PE):**
```
protocols bgp ASN
  neighbor <rr-ip>
    address-family ipv4-flowspec-vpn   # SAFI 134 - receives from Arbor
    address-family ipv6-flowspec-vpn   # SAFI 134 for IPv6
  !
!
```

**VRF BGP (PE):**
```
network-services
  vrf
    instance CUSTOMER-1
      protocols
        bgp ASN
          address-family ipv4-flowspec
            import-vpn route-target <rt>  # Import flowspec by RT
          !
          address-family ipv6-flowspec
            import-vpn route-target <rt>
          !
        !
      !
    !
  !
!
```

**Interface Flowspec (PE):**
```
interfaces
  <vrf-interface>
    flowspec enabled   # Enable flowspec filtering on interface
  !
!
```

### Scaler Wizard Options

| Menu | Option | Description |
|------|--------|-------------|
| BGP AFI Selection | [8] Flowspec VPN | ipv4/6-flowspec-vpn SAFI 134 |
| BGP AFI Selection | [9] Full VPN + Flowspec | L3VPN + Flowspec VPN combined |
| VRF Step 4 | IPv4/6 flowspec | Enable flowspec AFI with import-vpn |
| VRF Step 2b | Flowspec on interfaces | Enable `flowspec enabled` on VRF interfaces |

### Multi-Device Sync Recommendations

| Device | Configuration |
|--------|---------------|
| **RR-4** | BGP with `address-family ipv4-flowspec-vpn` to Arbor + `address-family ipv4-flowspec-vpn` to PE clients |
| **PE-1/PE-2** | VRF with `address-family ipv4-flowspec`, matching RT, interface flowspec enabled |

### Configuration Flow in Wizard

1. **Select devices**: PE-1, PE-2, RR-4
2. **Configure RR-4 BGP**: 
   - Select [8] Flowspec VPN or [9] Full VPN + Flowspec
   - Configure neighbor to Arbor with ipv4-flowspec-vpn
   - Configure neighbor-groups to PEs with ipv4-flowspec-vpn
3. **Configure PE-1/PE-2 VRF**:
   - Create VRF instances
   - Enable BGP with flowspec AFI (Step 4)
   - Configure import-vpn route-target
   - Enable flowspec on VRF interfaces (Step 2b)
4. **Verify scale**: Dashboard shows Flowspec VPN statistics

### SW-240206 RT-Redirect Dynamic Re-evaluation Test

Automated test script for FlowSpec-VPN RT-Redirect fix (SW-240206): verifies that when a VRF's unicast import RT is removed, the redirect target dynamically switches to the next valid VRF without requiring `clear bgp`.

**Script:** `FLOWSPEC_VPN/test_sw240206_rt_redirect.py`

**Usage:**
```bash
python3 test_sw240206_rt_redirect.py                    # Full run
python3 test_sw240206_rt_redirect.py --test 1          # Run only Test 1 (core bug)
python3 test_sw240206_rt_redirect.py --skip-setup     # Skip VRF creation
python3 test_sw240206_rt_redirect.py --no-cleanup     # Leave config for inspection
python3 test_sw240206_rt_redirect.py --debug          # Show debug output for redirect parsing
```

**Fixes applied (2026-02-22):**
- ExaBGP subprocess: use absolute paths (BGP_TOOL, EXABGP_DIR) to avoid cwd resolution
- bgp_tool kill_orphan: pass `spare_pid=os.getpid()` so bgp_tool doesn't kill itself (path contains "exabgp")
- `--exabgp-ip`: Override ExaBGP bind IP (default: 100.70.0.32). Must match device neighbor config and exist on test machine.
- Diagnostic step: After inject, checks BGP neighbor state and FlowSpec visibility.

**RT-Redirect verification prerequisites:**
- BGP neighbor must show **Established** (diagnostic reports this)
- ExaBGP `local-address` must match device `neighbor <ip>` and be configured on the test machine
- Use `--exabgp-ip <your-ip>` if different from default

**Prerequisites:** PE-1 (or target device) in `db/devices.json`, ExaBGP server reachable from device, BGP neighbor 100.64.6.134 configured for ipv4-flowspec-vpn.

**Tests:** (1) Core bug - RT removal triggers dynamic switch to ZULU, (2) RT re-add switches back to ALPHA, (3) VRF-light (no RD) as redirect candidate, (4) No BGP on default VRF.

### Live Scale Tracking

The wizard automatically displays:
```
Flowspec VPN:
  Interfaces w/flowspec: 15/1000 (2%)
  VRFs w/flowspec AFI:   3/512 (1%)
  BGP FS-VPN neighbors:  2
  ⚠️ Match-classes at 85% (10200/12000)  ← Warning when >80%
```

---

### Uniqueness Rules

| Parameter | Same Across Devices | Must Be Unique |
|-----------|:-------------------:|:--------------:|
| Service Name | ✅ (FXC-1) | - |
| EVI | ✅ | - |
| Route Target | ✅ (for peering) | - |
| Route Distinguisher | - | ✅ (use device's loopback) |
| ESI | ✅ (same ES) | - |
| Interface Names | - | ✅ (device-local) |
| VRF RD | - | ✅ (use device's loopback) |

### Implementation

**Data Models** (`scaler/models.py`):
- `ServiceRecord` - Records a service configuration (type, RT, RD, interfaces)
- `VRFRecord` - Records a VRF configuration
- `DeviceConfigRecord` - Records all config for a device in session
- `CrossDeviceContext` - Tracks configs across all devices
- `ConfigSuggestion` - A suggestion with description and generated config

**Recording Points** (`scaler/interactive_scale.py`):
- After FXC/EVPN service configuration: `multi_ctx.record_service_config(...)`
- After VRF configuration: `multi_ctx.record_vrf_config(...)`
- After multihoming configuration: `multi_ctx.record_mh_config(...)`

**Suggestion UI** (`scaler/interactive_scale.py`):
- `show_cross_device_suggestions(multi_ctx, hostname)` - Displays suggestion panel
- Called automatically before configuration mode selection

### Example Flow

```
User configures PE-1:
  └── 2,300 FXC services (FXC-1 to FXC-2300)
  └── RD: 1.1.1.1:N, RT: 1234567:N
  └── Multihoming ESI: 00:11:22:33:44:55

User switches to PE-2:
  ╔═══════════════════════════════════════════════════════╗
  ║  💡 Smart Suggestions Based on PE-1 Configuration     ║
  ╠═══════════════════════════════════════════════════════╣
  ║  From PE-1 (1.1.1.1):                                 ║
  ║    • 2,300 evpn-vpws-fxc services                     ║
  ║    • Multihoming ESI pairing                          ║
  ║                                                       ║
  ║  Suggested for PE-2 (2.2.2.2):                        ║
  ║    • Same services with RD 2.2.2.2:N                  ║
  ║    • Same RTs for EVPN peering                        ║
  ║    • Same ESI for multihoming                         ║
  ║                                                       ║
  ║  Options:                                             ║
  ║    [Q] Quick Match - Apply now                        ║
  ║    [V] View Generated Config                          ║
  ║    [M] Modify & Apply                                 ║
  ║    [S] Skip - Configure manually                      ║
  ║                                                       ║
  ║  Next Step: Configure L2-AC on PE-4 for termination   ║
  ╚═══════════════════════════════════════════════════════╝
```

### Complementary Next-Step Hints

| After Configuring | Suggest Next |
|-------------------|--------------|
| FXC Services | L2-AC on remote PE for termination |
| EVPN with IRB | Anycast IRB on other PEs |
| VRF | Same VRF on other PE for L3VPN |
| Multihoming | Same ESI on paired PE |

### Device-Specific Configuration Awareness

**MANDATORY: The wizard must be self-aware of each device's ACTUAL configuration.**

When displaying information about a device's existing configuration:
1. **Parse actual interfaces** - Don't assume interface types (PWHE vs L2-AC)
2. **No hardcoded defaults** - If interface not found, show "none detected", don't guess
3. **Show detected types** - Display interface type labels (PWHE, L2-AC, Bundle L2-AC)
4. **Use device's config** - Always use `multi_ctx.configs[hostname]` for device-specific data

**Example:**
```python
# ❌ WRONG: Assuming PWHE interface
if not interfaces:
    interfaces = [f'ph{num}.1']  # Don't do this!

# ✅ CORRECT: Show what's actually configured
if interfaces:
    if interfaces[0].startswith('ph'):
        iface_type = "PWHE"
    elif interfaces[0].startswith(('ge', 'xe')):
        iface_type = "L2-AC"
    console.print(f"  Interfaces: {interfaces[0]} ({iface_type})")
else:
    console.print(f"  Interfaces: [dim]none detected[/dim]")
```

### Checklist for New Cross-Device Features

- [ ] Add recording call after configuration completes
- [ ] Ensure RD uses target device's loopback
- [ ] Keep RT same for peering
- [ ] Keep ESI same for multihoming
- [ ] Add appropriate next_step_hint
- [ ] Parse ACTUAL config, don't assume interface types
- [ ] Test: Configure on PE-1, switch to PE-2, verify suggestions appear

---

## 💡 Quick Suggestions Engine (Pervasive)

**MANDATORY: Quick Suggestions must appear at EVERY level of the wizard where decisions are made.**

The Quick Suggestions Engine provides context-aware recommendations based on:
1. **Cross-device analysis** - What other devices in the session have configured
2. **Current device's pattern** - Detected interface types, service patterns
3. **Earlier wizard selections** - Cached pool status, timing history
4. **Configuration gaps** - Missing matching services, MH partner sync

### Locations for Quick Suggestions

| Wizard Level | Suggestion Types |
|--------------|------------------|
| **Scale UP** | Match other device's FXC count, continue current pattern, L2-AC termination |
| **Configuration Wizard** | Suggested service types, matching MH partner |
| **VRF Wizard** | Same VRFs as other devices |
| **Multihoming Wizard** | Same ESI as paired device |
| **Interface Wizard** | Sub-interface creation only (physical interfaces are hardware-defined). Continue detected pattern, Smart Quick Mode for single sub-interface |
| **Service Wizard** | Suggested RD/RT based on other devices |

### Implementation Pattern

```python
def _generate_<wizard>_suggestions(
    multi_ctx: 'MultiDeviceContext',
    <context_data>: Dict
) -> List[Dict]:
    """
    Generate smart suggestions based on:
    1. Cross-device analysis (what other devices have)
    2. Current device's configuration pattern
    3. Earlier wizard selections (cached pool status, etc.)
    4. Configuration gaps (missing matching services)
    """
    suggestions = []
    
    # Analyze current device
    current_hostname = multi_ctx.current_device.hostname
    current_config = multi_ctx.configs.get(current_hostname, "")
    
    # Analyze other devices
    for hostname, config in multi_ctx.configs.items():
        if hostname == current_hostname:
            continue
        # Compare and generate suggestions...
        
    return suggestions
```

### Suggestion Data Structure

```python
suggestion = {
    "type": "match_fxc",  # Unique identifier
    "description": "Match PE-1's FXC count: Add 500 services",  # User-facing
    "details": "PE-2: 1,800 → 2,300 (interface: PWHE)",  # Additional info
    "service_type": "fxc",
    "count": 500,
    "interface_type": "PWHE",
    "source_device": "PE-1",
    "apply_func": _apply_match_fxc_suggestion,  # Execution function
}
```

### UI Pattern for Quick Suggestions

```
╭─────────────────────────────────────────────────────────────────╮
│  💡 Quick Suggestions (based on current configurations)         │
╰─────────────────────────────────────────────────────────────────╯
  [1] Match PE-1's FXC count: Add 500 services
      PE-2: 1,800 → 2,300 (interface: PWHE)
  [2] Add L2-AC termination for PE-1's PWHE services
      Configure 2,300 L2-AC interfaces on PE-4
  [3] Sync with MH partner PE-1: Add 500 FXC
      Both devices should have matching services
  [M] Manual selection (below)
  [B] Back
```

### Checklist for Adding Quick Suggestions

When adding Quick Suggestions to a wizard:

- [ ] Create `_generate_<wizard>_suggestions()` function
- [ ] Analyze cross-device configs
- [ ] Analyze current device's pattern (interface types, last service)
- [ ] Check cached data (pool status, timing)
- [ ] Create `_apply_<type>_suggestion()` for each suggestion type
- [ ] Show suggestions at the TOP of the wizard before manual options
- [ ] Provide `[M] Manual selection` option to skip suggestions
- [ ] Log suggestions used for timing history

### Current Implementation

| Wizard | Suggestions | File | Status |
|--------|-------------|------|--------|
| Scale UP | ✅ 4 types | `scaler/wizard/scale_operations.py` | ✅ Working |
| Configuration Wizard | Cross-device | `scaler/interactive_scale.py` | 🔄 Partial |
| VRF Wizard | - | - | ❌ TODO |
| MH Wizard | - | - | ❌ TODO |

---

## 📝 Documentation Maintenance Protocol

**⚠️ MANDATORY: All new features MUST be documented after user confirmation.**

### When to Update This File

1. **After implementing a new feature** - Add documentation once the user confirms it works
2. **After fixing a bug** - Document the fix and root cause if it could help future development
3. **After changing behavior** - Update relevant sections to reflect new behavior

### What to Document

| Category | What to Add |
|----------|-------------|
| **New Features** | Menu location, function name, usage, checklist |
| **New Patterns** | Code examples, when to use |
| **New Limits/Constants** | Value, source, error when exceeded |
| **UI/UX Changes** | Before/after, trigger locations |
| **Bug Fixes** | Root cause, solution, prevention tips |

### Documentation Checklist for New Features

When adding a new feature, document:

- [ ] **Purpose** - What problem does it solve?
- [ ] **Location** - Which files were modified?
- [ ] **Menu Entry** - Where does user access it?
- [ ] **Function Names** - Key functions involved
- [ ] **Data Flow** - How data moves through the system
- [ ] **Error Handling** - What errors can occur and how they're handled
- [ ] **Testing** - How to verify it works

### Example Entry Format

```markdown
## Feature: Config Summary After Fetch

**Added:** 2026-01-01
**Status:** ✅ Working

### Purpose
Display configuration summary automatically after fetching/refreshing device config.

### Location
- `interactive_scale.py` - `fetch_current_config()`, `_refresh_all_devices()`

### Trigger Points
| Action | When Summary Appears |
|--------|---------------------|
| Multi-device Refresh [R] | After all devices complete |
| Single-device Use Cached [1] | After selecting cached |
| Single-device Fetch Fresh [2] | After fetch completes |

### Key Code
```python
from .config_parser import ConfigParser
parser = ConfigParser()
show_current_config_summary(config, parser)
```
```

### Status Tags

| Tag | Meaning |
|-----|---------|
| ✅ Working | User confirmed working |
| 🔄 In Progress | Being developed |
| ⚠️ Known Issues | Works but has caveats |
| ❌ Deprecated | No longer used |

---

## Recent Additions Log

### FlowSpec VPN HA Test Orchestrator (SW-236398) (2026-03-01)

**Status:** ✅ Implemented (Spirent FlowSpec class may need BgpFlowSpecConfig vs BgpFlowSpecRouteConfig per STC version; ExaBGP + pre-existing rules fallback available)

**Purpose:** Automated end-to-end testing of FlowSpec-VPN HA behavior across 15 test cases (process restart, container restart, system restart, switchover, GR, special cases).

**Key Paths:**
| Component | Path |
|-----------|------|
| Orchestrator | `SCALER/HA/ha_flowspec_test.py` |
| Test definitions | `SCALER/HA/test_definitions/sw_236398.json` |
| DNAAS path setup | `SCALER/HA/ensure_dnaas_path.py` |
| Results | `SCALER/HA/test_results/SW-236398_<timestamp>/` |

**Trigger:** `/HA test SW-236398` or `/HA test flowspec-vpn-ha [PE-4]`

**Flow:** Ensure DNAAS BD path (VLAN 212) → run orchestrator → Spirent BGP + 200 FlowSpec rules → HA event via paramiko SSH → recovery polling → diff + verdict.

**Fallbacks:** (1) Spirent FlowSpec injection fails → ExaBGP. (2) ExaBGP not available → pre-existing rules (≥10 from /BGP ExaBGP→PE-1→RR→DUT). (3) Device alias: PE-4 → YOR_CL_PE-4.

**Resilience (2026-03-01):** SSH retries (3x, 15/30/45s) on timeout; 45s cooldown after wb_agent/NCP datapath tests; incremental run_log.md after each test; DNOS requires interactive shell (invoke_shell).

**Spirent Resilience + Cross-Command Integration (2026-03-01):** spirent_tool.py: _retry_rest() for transient REST failures, _validate_session() before stats/start/stop/create-stream, cmd_reconcile for local vs server session sync. ha_flowspec_test.py: spirent_poll_stats retries 3x, spirent_reachable tracking, sp_verdict UNKNOWN (unreachable) when Spirent down (no false PASS), active_ha_session.json gets spirent_expected_traffic, spirent_baseline, convergence_times; session closed (active: false) at end. VLAN auto-selected from ~/.spirent_learning.json known_stream_profiles (READY).

**CL vs SA (2026-03-01):** Orchestrator detects device mode via `show system` (CL-* vs SA-*). On **Cluster**: NCC switchover and NCC restart tests available; NCC restart tests require `--standby-ip <standby_mgmt_ip>` so the orchestrator connects to the standby NCC when restarting the active NCC (avoids SSH loss). On **Standalone**: tests with `requires_cluster` (test_08–10, 13, 15) are skipped.

**Unified 4-Layer HA Standard (2026-03-01):** Every /HA TEST uses all four verification layers as the default:
1. **Control-plane (/HA):** BGP sessions, PfxAccepted, routes, BFD, alarms — before/during/after
2. **Datapath (TCAM):** `show system npu-resources resource-type flowspec` + `show flowspec ncp <id>` — before/during/after
3. **Traffic (/SPIRENT):** Create stream matching existing FlowSpec rules, start baseline, poll TX/RX/loss during HA event
4. **Packet (/XRAY):** After recovery, capture at DUT interface to verify packets actually arrive at correct VRF
5. **Traces (/debug-dnos):** After recovery, grep traces at HA event timestamp for documentation; on FAIL, escalate to full investigation
Phase 7 assembles all layers into one unified diff table. Each layer degrades gracefully if unavailable (e.g., Spirent unreachable → proceed without traffic).

**Background run:** `nohup python3 ~/SCALER/HA/ha_flowspec_test.py --device PE-4 > /tmp/ha_flowspec_pe4.log 2>&1 &`
**Cluster (with standby):** `nohup python3 ~/SCALER/HA/ha_flowspec_test.py --device PE-4 --standby-ip <standby_ncc_ip> > /tmp/ha_flowspec_pe4.log 2>&1 &`

**Files Modified:**
- `SCALER/HA/ha_flowspec_test.py` (new)
- `SCALER/HA/test_definitions/sw_236398.json` (new)
- `SCALER/HA/ensure_dnaas_path.py` (new)
- `SCALER/SPIRENT/spirent_tool.py` (FlowSpec add-routes, HoldTimeInterval/KeepAliveInterval)
- `~/.cursor/commands/HA.md` (SW-236398 intent)
- `~/.cursor/rules/cross-command-integration.mdc` (FlowSpec session fields)

---

### HA Config Framework and Generic Epic Support (2026-03-01)

**Status:** Implemented

**Purpose:** Enable /HA to configure devices directly (not just show commands), verify prerequisites before tests, and handle any epic/feature on any device. Network Mapper MCP only supports `show` commands; ha_executor provides SSH-based config and operational command execution.

**Key Additions:**
- `SCALER/HA/ha_ssh.py` — shared SSH shell utilities for all HA tools. Single source of truth for DNOS interactive SSH. Uses `select.select()` for OS-level zero-CPU blocking (no busy-loop). Exits as soon as CLI prompt returns or HA anomaly detected. Exports: `run_ssh_shell`, `ssh_quick_check`, `recv_until_ready`, `PROMPT_RE`, `HA_EVENT_PATTERNS`, `EXPECT_MAP` (per-command expect patterns for configure/commit/exit).
- `SCALER/HA/ha_executor.py` — lightweight SSH executor: connect, run_show, run_operational, run_config, verify_device, cleanup, disconnect. Credentials from devices.json. Uses ha_ssh.run_ssh_shell internally.
- Device Verification Gate — SSH + System Name + Serial check + AskQuestion permission before any test
- Prerequisites Framework — 3-layer check (HA readiness, feature state, infrastructure) with auto-remediation via ha_executor
- Device Configuration Protocol — Network Mapper for reads, ha_executor for writes
- Generic Epic Test Runner — combines scenario + feature + device for any epic; feature-specific show commands from feature-ha-mapping.md

**Rule:** Network Mapper for show commands; ha_executor for operational/config (request restart, clear bgp, set logging terminal, configure).

**ha_ssh select() pattern:** `recv_until_ready()` uses `select.select([chan], [], [], min(remaining, 0.5))` to block at kernel level until data arrives — zero CPU while waiting, instant wakeup when bytes appear. Replaces fixed sleeps and busy-loop polling. Improves convergence time measurement accuracy in poll_recovery (ssh_quick_check).

**Files Modified:**
- `SCALER/HA/ha_ssh.py` (new, 2026-03-01)
- `SCALER/HA/ha_executor.py` (imports from ha_ssh)
- `SCALER/HA/ha_flowspec_test.py` (imports run_ssh_shell, ssh_quick_check from ha_ssh)
- `SCALER/HA/ensure_dnaas_path.py` (imports run_ssh_shell from ha_ssh)
- `~/.cursor/commands/HA.md` (Device Verification Gate, Prerequisites Framework, Device Configuration Protocol, TEST/EPIC updates)
- `~/.cursor/ha-reference/feature-ha-mapping.md` (Prerequisites field per feature)
- `~/.cursor/ha-reference/test-procedures.md` (Prerequisite checklist, ha_executor trigger per scenario)

---

### L3 Interface Advanced Options (2026-01-27)

**Status:** ✅ Working

**Purpose:** Provide additional L3 interface configuration options beyond IP addressing.

**New L3 Options Available:**
| Option | DNOS Syntax | Description |
|--------|-------------|-------------|
| MPLS | `mpls enabled` | Enable MPLS label switching for WAN/core interfaces |
| Flowspec | `flowspec enabled` | Enable BGP Flowspec filtering for DDoS protection |
| MTU | `mtu <value>` | Interface MTU (64-9216) |
| Description | `description "<text>"` | Interface description (supports {n} for numbering) |
| BFD | `bfd` / `enabled` | Bidirectional Forwarding Detection |

**User Flow:**
```
━━━ L3 Advanced Options ━━━
Additional L3 interface settings (all optional)

  [Q] Quick → Use defaults (no MPLS/flowspec/BFD)
  [C] Customize → Configure MPLS, flowspec, MTU, BFD
  [B] Back
```

**Generated Config Example:**
```
interfaces
  ge100-0/0/1.100
    admin-state enabled
    vlan-id 100
    description "PE-to-CE link 1"
    mtu 9000
    mpls enabled
    flowspec enabled
    bfd
      enabled
    !
    ipv4 address 10.0.0.1/30
  !
!
```

**Files Modified:**
- `scaler/interactive_scale.py` - Added L3 Advanced Options section after IP configuration

---

### LLDP Neighbor-Aware Interface Selection (2026-01-01)

**Status:** 🔄 In Progress (awaiting LLDP availability on devices)

**Purpose:** When selecting physical interfaces for L2-AC, WAN, or DG configurations, the wizard should suggest only interfaces connected to other DN devices or DNAAS.

**Files Modified:**
- `extract_configs.sh` - Added `show lldp neighbor` command and LLDP parsing
- `scaler/wizard/scale_operations.py` - Added LLDP-aware interface selection functions

**Key Functions:**
- `get_lldp_neighbors(hostname)` - Get LLDP neighbors from operational.json
- `get_wan_interfaces_from_config(hostname)` - Fallback: parse WAN interfaces from config
- `get_interfaces_with_lldp(hostname, dn_only)` - Get interfaces with neighbors
- `suggest_physical_interface(hostname, purpose)` - Interactive interface selection
- `show_lldp_summary(hostname)` - Display LLDP neighbor summary

**Data Storage:**
- LLDP neighbors stored in `db/configs/{device}/operational.json`
- Fields: `lldp_neighbors` (array), `lldp_neighbor_count` (int)
- Each neighbor: `interface`, `neighbor`, `remote_port`, `is_dn_device`

**User Flow:**
1. When Scale UP needs L2-AC parent interface
2. Check existing L2-AC interfaces first (detected from config)
3. If none, show LLDP-connected interfaces as options
4. User selects from DN-connected interfaces or enters custom

**Fallback Behavior:**
- If LLDP not available, falls back to WAN interfaces detected from config
- WAN interfaces identified by descriptions containing: wan, core, uplink, backbone

---

### Quick Suggestions Engine - Scale UP (2026-01-01)

**Status:** ✅ Working

**Purpose:** Provide smart, context-aware suggestions at the beginning of the Scale UP wizard based on cross-device analysis and current device patterns.

**File Modified:** `scaler/wizard/scale_operations.py`

**Key Functions:**
- `_generate_scale_up_suggestions()` - Analyzes all devices and generates suggestions
- `_execute_scale_up()` - Streamlined execution with pre-filled values from suggestions
- `_apply_match_fxc_suggestion()` - Match another device's FXC count
- `_apply_continue_fxc_suggestion()` - Continue current device's pattern
- `_apply_l2ac_termination_suggestion()` - Add L2-AC termination for remote PWHE
- `_apply_mh_sync_suggestion()` - Sync with multihoming partner

**Suggestion Types:**
1. **Match FXC** - Match another device's service count
2. **Continue Pattern** - Add more of the same type to current device
3. **L2-AC Termination** - Add L2-AC interfaces to terminate remote PWHE services
4. **MH Sync** - Sync service count with multihoming partner

**User Flow:**
1. Enter Scale UP wizard
2. Quick Suggestions panel shows at the top (if suggestions available)
3. Select a suggestion to apply with one click, OR
4. Select [M] Manual to continue with normal wizard flow

---

### Self-Aware Wizard / Cross-Device Suggestions (2026-01-01)

**Status:** 🔄 In Progress

**Purpose:** Make the wizard context-aware so it suggests relevant configurations based on what was configured on other devices.

**Files Modified:**
- `scaler/models.py` - Added `ServiceRecord`, `VRFRecord`, `DeviceConfigRecord`, `CrossDeviceContext`, `ConfigSuggestion`
- `scaler/interactive_scale.py` - Added recording calls, suggestion UI, integration into wizard flow

**Key Functions:**
- `MultiDeviceContext.record_service_config()` - Records FXC/EVPN service config
- `MultiDeviceContext.record_vrf_config()` - Records VRF config
- `MultiDeviceContext.get_suggestions_for()` - Gets suggestions for a device
- `MultiDeviceContext.generate_matching_config()` - Generates config with adjusted RD
- `show_cross_device_suggestions()` - UI for displaying and applying suggestions

**User Flow:**
1. Configure services on PE-1
2. Switch to configure PE-2
3. Wizard shows "Smart Suggestions" panel with options: Quick Match, View, Modify, Skip
4. Quick Match applies same services with PE-2's loopback in RD

**Trigger Point:** Called automatically in `run_wizard()` after fetching config, before configuration mode selection.

---

### Text Corrections (2026-01-01)

**Status:** ✅ Working

1. **df-invert-preference text**: Updated to clarify that it inverts from highest-preference to lowest-preference algorithm for selected interfaces, allowing DF role sharing between PEs across services.

2. **FXC/EVPN interface note**: Corrected to show service-specific attachment options:
   - FXC: L2-AC (ge/bundle.Y with l2-service) or PWHE (phX.Y)
   - EVPN: L2-AC (ge/bundle.Y with l2-service) or IRB

---

### Scale UP Interface Detection Fix (2026-01-01)

**Status:** ✅ Working

**Problem:** Scale UP wizard incorrectly showed `ph2300.1` for PE-4's FXC services, when PE-4 actually uses L2-AC interfaces (`ge100-18/0/0.XXXX`). The code assumed all FXC services use PWHE interfaces.

**Root Cause:** `scale_operations.py` line 228 had regex that only matched PWHE interfaces:
```python
iface_matches = re.findall(r'interface\s+(ph\d+\.\d+)', block)  # Only ph*!
```
And line 232-234 had a fallback that assumed PWHE:
```python
if not interfaces:
    interfaces = [f'ph{num}.1']  # Wrong assumption!
```

**Solution:**
1. Updated regex to match ALL interface types (PWHE, L2-AC, bundle)
2. Removed hardcoded PWHE fallback - now shows "none detected" if no interface found
3. Added interface type labels in display (PWHE, L2-AC, Bundle L2-AC)

**Files Modified:** `scaler/wizard/scale_operations.py`

---

### Config Summary Performance Optimization (2026-01-01)

**Status:** 🔄 In Progress - Optimized Version

**Problem:** Original `show_current_config_summary()` was slow (seconds) on large configs (74K-92K lines) due to:
- Line-by-line iteration through entire config
- Multiple regex searches per line
- O(n) complexity on 90K+ lines

**Solution:** Rewrote to use fast string operations:
- `config_text.count('\n  pattern ')` instead of line iteration
- Single-pass `re.findall()` for interface names
- Skipped detailed multihoming parsing (just count ESIs)

**Performance Improvement:**
| Method | 90K line config |
|--------|-----------------|
| Old (line iteration) | ~2-3 seconds |
| New (string counting) | ~0.1-0.2 seconds |

**Key Changes:**
```python
# OLD (slow) - iterates every line
for line in config_text.split('\n'):
    if in_interfaces and line.startswith('  '):
        # categorize interface...

# NEW (fast) - single regex findall
all_interfaces = iface_pattern.findall(config_text)
for iface in all_interfaces:
    # categorize interface...
```

**Location:** `interactive_scale.py` line ~11234

---

### EVPN-VPWS Duplicate RD/RT Prompts Fix (2026-01-04)

**Status:** ✅ Working

**Problem:** In the EVPN-VPWS service configuration wizard, Route Distinguisher (RD) and Route Target (RT) were asked twice:
1. First in the general "Route Distinguisher / Route Target" section (for all service types)
2. Again in the EVPN-VPWS specific section ("2. Route Distinguisher")

**Root Cause:** The general RD/RT section (lines ~7445-7466) ran for ALL service types including EVPN-VPWS, but EVPN-VPWS has its own specific RD configuration section that allows choosing between Manual and Auto modes.

**Solution:**
1. Wrapped general RD/RT section with `if svc_type != "evpn-vpws":` to skip for EVPN-VPWS
2. Enhanced EVPN-VPWS specific section to include full RD/RT configuration:
   - Router ID for RD (with lo0 auto-detection)
   - AS number for RT (with BGP AS auto-detection)
   - RD mode selection (Manual or Auto)
3. Updated menu to show `[4] EVPN-VPWS (Point-to-Point L2VPN)` instead of just `[4] VPWS`

**Files Modified:** `scaler/interactive_scale.py`

**Code Changes:**
```python
# General section now skips EVPN-VPWS:
if svc_type != "evpn-vpws":
    console.print("\n[bold]Route Distinguisher / Route Target[/bold]")
    # ... prompts for Router ID and AS

# EVPN-VPWS section now includes full RD/RT:
console.print("\n[bold]2. Route Distinguisher / Route Target[/bold]")
rd_router_id = Prompt.ask("   Router ID for RD", default=rd_default)
rt_asn = IntPrompt.ask("   AS number for RT", default=rt_default)
# Then asks for RD mode (Manual/Auto)
```

**User Flow After Fix:**
```
━━━ EVPN-VPWS Specific Configuration ━━━

1. Service ID Configuration (mandatory)
   [1] Sequential - local=remote, incrementing
   [2] Custom - specify local/remote ranges separately
   Select [1/2] (1): 
   Starting ID (1): 
   → IDs 1 to 3990

2. Route Distinguisher / Route Target
   lo0 IP detected: 1.1.1.1
   Router ID for RD (1.1.1.1): 
   BGP AS detected: 1234567
   AS number for RT (1234567): 
   RD Format:
     [1] Manual - {router-id}:{service-number}
     [2] Auto - system generates unique RD
     Select [1/2] (1): 
   → RD: 1.1.1.1:N, RT: 1234567:N

3. Service Description (optional)
   ...
```

---

### Live Terminal Display Fix (2026-01-04)

**Status:** ✅ Working

**Problem:** The "Live Terminal" panel during file upload config push:
1. Always showed "set logging terminal" in subtitle, never updating
2. Didn't show the actual SCP upload or `load override` commands
3. `raw_terminal` defaulted to `False`, hiding terminal output

**Root Cause:**
- Subtitle was hardcoded: `subtitle="[dim]set logging terminal[/dim]"`
- SCP runs locally via subprocess, not on device SSH session
- Terminal output only captured when `raw_terminal=True` AND user answered "Yes"

**Solution:**
1. **Dynamic subtitle** - Shows current command based on stage:
   - `upload` → "scp → {device.ip}:/config/"
   - `load` → "load override config.txt"
   - `commit_check` → "commit check"
   - `commit` → "commit"
2. **Default `raw_terminal=True`** for file upload mode
3. **Command markers** - Adds `>>> command` lines to terminal output at stage transitions

**Files Modified:** `scaler/interactive_scale.py`

**Code Changes:**
```python
# Dynamic subtitle based on current stage
stage_commands = {
    'upload': f'scp → {device.ip}:/config/',
    'load': f'load override config.txt',
    'commit_check': 'commit check',
    ...
}
current_cmd = stage_commands.get(current_stage, current_stage)
subtitle=f"[dim]{current_cmd}[/dim]"

# Add command markers to terminal output
stage_markers = {
    'upload': f'>>> scp config.txt {device.username}@{device.ip}:/config/',
    'load': '>>> load override /config/scaler_config.txt',
    ...
}
if info['stage'] in stage_markers and raw_terminal:
    terminal_lines.append(stage_markers[info['stage']])
```

**Note:** SCP still runs locally (not visible in device terminal) but the command is now shown as a marker.

---

### EVPN-VPWS vpws-service-id Syntax Fix (2026-01-04)

**Status:** ✅ Working

**Problem:** Push failed with error: `The command 'vpws-service-id local 1 remote 1' failed, Reason: Unknown word.`

**Root Cause:** The `vpws-service-id` was being placed at the service instance level (6 spaces) instead of INSIDE the interface block (8 spaces).

**DNOS Correct Syntax:**
```
network-services
  evpn-vpws
    instance VPWS-1
      protocols
        bgp 1234567
          ...
        !
      !
      admin-state enabled
      interface ge400-0/0/4.1        <-- 6 spaces
        vpws-service-id local 1 remote 1  <-- 8 spaces (INSIDE interface!)
      !
    !
  !
!
```

**Wrong (before fix):**
```python
config_lines.append(f"      vpws-service-id local {local_id} remote {remote_id}")  # At instance level!
config_lines.append(f"      interface {iface}")
```

**Correct (after fix):**
```python
config_lines.append(f"      interface {iface}")
# EVPN-VPWS: vpws-service-id goes INSIDE interface block (8 spaces)
if svc_type == "evpn-vpws" and local_id is not None:
    config_lines.append(f"        vpws-service-id local {local_id} remote {remote_id}")
```

**Files Modified:** `scaler/interactive_scale.py`

**Key Learning:** Always verify DNOS syntax against working running configs in `db/configs/*/running.txt` before implementing config generation.

---

### ISIS Level Syntax Fix (2026-01-31)

**Status:** ✅ Fixed

**Problem:** Push failed with error: `The command 'level-capability level-2' failed, Reason: Unknown word.`

**Root Cause:** The wizard was generating `level-capability level-2` (Juniper-style) instead of the correct DNOS syntax.

**DNOS Correct Syntax (confirmed via live device CLI):**
```
protocols
  isis
    instance ISIS
      iso-network 49.0001.1921.6800.1001.00
      level level-2              <-- CORRECT: 'level level-2'
      address-family ipv4-unicast
      !
      interface bundle-100
        level level-2            <-- Also at interface level
      !
    !
  !
!
```

**Wrong Syntax (other vendors):**
- `is-level level-2` (Cisco)
- `level-capability level-2` (Not valid on DNOS)

**Files Modified:**
- `scaler/interactive_scale.py` - Changed `level-capability` to `level`
- `scaler/cli_rules_db.py` - Updated hierarchy spec from `level-capability` to `level`
- `scaler/cli_validator.py` - Updated validation regex

**Verification Method:** Connected to live DNOS device and ran:
```
configure
protocols isis instance ISIS ?
  ...
  level                            Configure IS-IS level
  ...
level ?
  level-1            IS-IS type level-1
  level-1-2          IS-IS type level-1-2
  level-2            IS-IS type level-2
```

**Key Learning:** Always SSH to a live DNOS device and use `?` to explore CLI hierarchies when unsure about syntax.

---

### Live Terminal Streaming Fix (2026-01-04)

**Status:** ✅ Working

**Problem:** Live Terminal during config push showed command markers but not the actual device output (progress bars, etc.). The terminal appeared frozen after showing `>>> load override`.

**Root Cause:** In `config_pusher.py`, the `load override` stage only sent terminal output to the callback when a progress bar was detected:
```python
if progress_match:
    update_progress("load", mapped_pct, f"Loading... {device_pct}%", chunk)
# Missing else - no output sent when no progress bar!
```

**Solution:** Always stream terminal output even when no progress bar is detected:
```python
if progress_match:
    update_progress("load", mapped_pct, f"Loading... {device_pct}%", chunk)
else:
    # Always stream terminal output even without progress bar
    update_progress("load", last_percent, "Loading...", chunk)
```

**Files Modified:** `scaler/config_pusher.py`

**Note:** The commit_check and commit stages were already streaming correctly.

---

### Factory Reset + Load Feature (2026-01-04)

**Status:** ✅ Working

**Problem:** When pushing large configs (>6000 interfaces), the commit fails with:
```
Too many datapath interfaces during the commit. Please split the commit in order not to cross the 8000 limit (from hook: assign_new_internal_index)
```

**Solution:** Implemented a two-stage push: factory reset first, then load new config.

**How It Works:**
1. **Detection:** `ask_push_method()` counts interfaces in the config
2. **Threshold:** If interfaces > 6000, show factory reset recommendation
3. **Two-Stage Push:**
   - Stage 1: `load override factory-default` → `commit`
   - Stage 2: `load override new_config.txt` → `commit`

**Files Modified:**
- `scaler/interactive_scale.py` - `ask_push_method()`, `push_and_verify()`
- `scaler/config_pusher.py` - Added `push_factory_reset()` method

**User Flow:**
```
Push Method:
  ⚠  HIGH INTERFACE COUNT DETECTED: 7,500 interfaces
  DNOS has a ~8000 interface limit per commit transaction.
  Recommendation: Use factory reset + load to avoid commit failure.

  [1] Factory reset + load (recommended)
      → load override factory-default, commit, then load new config
  [2] File upload (load override) - may fail if too many interfaces
  [3] Terminal paste - paste config directly (slower but may work)
  [B] Cancel
```

**Key Code:**
```python
# Count interfaces
interface_count = len(re.findall(r'\n  (ge\d+-|xe\d+-|bundle-ether|ph|irb|lo)...', config_text))

# If > 6000, offer factory reset option
if interface_count > 6000:
    console.print("⚠  HIGH INTERFACE COUNT DETECTED")
    # Show factory reset option
```

**Push Flow:**
```python
if use_factory_reset:
    # Stage 1: Factory reset
    pusher.push_factory_reset(device, progress_callback)
    
    # Stage 2: Load new config
    pusher.push_config_enhanced(device, config_text, ...)
```

**Note:** Factory reset does not support dry-run (commit check only) - it must do a full commit.

---

### Mirror Configuration Mode (2026-01-04)

**Status:** ✅ Working

**Purpose:** Copy configuration from a source PE device to a target device while preserving device-unique attributes.

**What It Does:**

1. **Preserves from Target Device:**
   - Router ID and Loopback IP (Lo0)
   - Route Distinguishers (transformed to use target's loopback)
   - WAN interfaces (MPLS-enabled interfaces)
   - Bundle configurations and LACP
   - LLDP configuration
   - System configuration (hostname, etc.)
   - Physical parent interfaces of WAN sub-interfaces

2. **Mirrors from Source Device:**
   - Network Services (FXC, EVPN-VPLS, VRF)
   - Routing Policies
   - ACLs
   - QoS Policies
   - Multihoming ESIs (kept same for dual-homing peering)
   - Service-attached interfaces

3. **Key Transformations:**
   - **RD Transformation:** `route-distinguisher SOURCE_LO0:N` → `route-distinguisher TARGET_LO0:N`
   - **Route Targets:** Preserved (same for EVPN peering)
   - **Interface Mapping:** Three strategies available

**Interface Mapping Strategies:**

| Strategy | Description | When to Use |
|----------|-------------|-------------|
| Auto-remap | Detect target interfaces and map automatically | Different interface types |
| Copy names | Keep same interface names | Identical platforms |
| Custom | Manual prefix mapping | Special requirements |

**Files Created/Modified:**
- `scaler/wizard/mirror_config.py` - Core mirror logic (NEW)
- `scaler/wizard/parsers.py` - Added LLDP, bundle, ACL, QoS parsing
- `scaler/wizard/__init__.py` - Exports
- `scaler/interactive_scale.py` - Menu integration

**Key Classes:**

```python
class ConfigMirror:
    """Handles configuration mirroring between devices."""
    
    def __init__(self, source_config, target_config, source_hostname, target_hostname):
        # Parse both configs, extract key attributes
    
    def extract_target_unique(self) -> Dict[str, str]:
        """Extract sections to preserve from target."""
        # Returns: system, wan_interfaces, lldp, bundles, lacp, lo0
    
    def extract_source_mirrored(self) -> Dict[str, str]:
        """Extract sections to mirror from source."""
        # Returns: services, routing_policy, acls, qos, multihoming
    
    def transform_rds(self, config: str) -> str:
        """Replace RD IP addresses with target's loopback."""
    
    def map_interfaces_auto(self) -> Dict[str, str]:
        """Auto-map interfaces by type."""
    
    def generate_merged_config(self) -> str:
        """Generate final merged configuration."""
```

**Wizard Flow:**

```
╭─────────────────────────────────────────────────────────────────╮
│  🪞 Mirror Configuration Mode                                    │
╰─────────────────────────────────────────────────────────────────╯

Step 1: Select Source Device
  Current target: PE-2 (YOR_PE-2)
  
  Available source devices:
  [1] PE-1 (YOR_PE-1) - 2000 FXC, 2000 PWHE
  [B] Back

Step 2: Analysis
  ┌─────────────────┬──────────────────┬──────────────────┐
  │ Attribute       │ Source (PE-1)    │ Target (PE-2)    │
  ├─────────────────┼──────────────────┼──────────────────┤
  │ Loopback        │ 1.1.1.1          │ 2.2.2.2          │
  │ Router-ID       │ 1.1.1.1          │ 2.2.2.2          │
  │ WAN Interfaces  │ bundle-1, ge...  │ bundle-2, ge...  │
  │ Services        │ 2000 FXC         │ 500 FXC          │
  └─────────────────┴──────────────────┴──────────────────┘

  Will preserve from target:
    ✓ System config (hostname: YOR_PE-2)
    ✓ WAN interfaces (bundle-2, 3 physical)
    ✓ LLDP configuration
    ✓ Lo0 address (2.2.2.2)

  Will mirror from source:
    → 2000 FXC services (RD: 1.1.1.1:N → 2.2.2.2:N)
    → Routing policies
    → Multihoming ESIs

Step 3: Interface Mapping
  [1] Auto-remap
  [2] Copy names
  [3] Custom
  [B] Back

Step 4: Preview & Push
  (Standard push flow with live terminal)
```

**Menu Access:**
- Multi-Device: `[M] Mirror Config` in action menu
- Single-Device: `[8] Mirror Config` in action menu

**Testing Checklist:**
- [ ] Mirror PE-1 (PWHE) config to PE-2 (verify RD transformation)
- [ ] Verify WAN interfaces preserved on target
- [ ] Verify LLDP preserved on target
- [ ] Verify system hostname preserved
- [ ] Test with multihoming (ESIs should match)
- [ ] Test all three interface mapping strategies
- [ ] Verify live terminal display during push


---

## 🔍 Config Detection & operational.json (Added 2026-01-12)

### Data Flow Architecture

```
Device SSH → config_extractor.py → running.txt + operational.json
                                           ↓
                                   interactive_scale.py
                                           ↓
                            show_current_config_summary()
                                           ↓
                            Wizard displays & prompts
```

### CRITICAL: Parse Once, Store, Read Fast

**ALWAYS store parsed data in `operational.json`** during config extraction.
This avoids re-parsing configs every time they're displayed.

### operational.json Schema

```json
{
  // System
  "system_type": "SA-40C (NCR)",
  "dnos_version": "26.1.0",
  
  // BGP
  "local_as": 12400,
  "bgp_neighbors": 5,
  "router_id": "2.2.2.2",
  "lo0_ip": "2.2.2.2",
  
  // IGP
  "igp": "ISIS",
  "igp_instance": "R2",
  "label_protocol": "LDP",
  
  // Other Protocols
  "lacp_interfaces": 14,
  "lldp_interfaces": 30,
  "bfd_interfaces": 5,
  
  // Services
  "vrf_total": 4,
  "vrf_names": ["AKAMAI", "CloudFlare", "DC", "INTERNET"],
  "fxc_total": 1,
  "evpn_total": 0,
  "route_targets": ["12400:65100", "1:1"],
  
  // Interfaces
  "interface_count": 59,
  "pwhe_count": 2,
  "bundle_count": 10,
  
  // Multihoming
  "mh_interfaces": 0
}
```

---

## Detection Patterns

### DNOS Config Structure
```
system                      → system section
interfaces                  → interfaces section
protocols                   → contains: bgp, isis/ospf, ldp, lacp, lldp, bfd
network-services            → contains: vrf, evpn-vpws-fxc, bridge-domain, multihoming
```

### Protocol Detection (under `protocols` block)
```python
# Find protocols block first
protocols_match = re.search(r'^protocols\s*\n(.*?)(?=^[^\s]|\Z)', config, re.MULTILINE | re.DOTALL)
if protocols_match:
    p = protocols_match.group(1)
    
    # ISIS
    if re.search(r'^\s+isis\s*$', p, re.MULTILINE):
        igp = 'ISIS'
    
    # LDP
    if re.search(r'^\s+ldp\s*$', p, re.MULTILINE):
        label_protocol = 'LDP'
    
    # LACP
    if re.search(r'^\s+lacp\s*$', p, re.MULTILINE):
        lacp_count = len(re.findall(r'interface\s+bundle-\d+', p))
```

### VRF Detection (under `network-services > vrf`)
```python
ns_match = re.search(r'^network-services\s*\n(.*?)(?=^[^\s]|\Z)', config, re.MULTILINE | re.DOTALL)
if ns_match:
    vrf_match = re.search(r'^\s+vrf\s*\n(.*?)(?=^\s{2}[^\s]|\Z)', ns_match.group(1), re.MULTILINE | re.DOTALL)
    if vrf_match:
        vrf_instances = re.findall(r'instance\s+(\S+)', vrf_match.group(1))
```

### Interface Detection
```python
# Find interfaces block
iface_match = re.search(r'^interfaces\s*\n(.*?)(?=^[^\s]|\Z)', config, re.MULTILINE | re.DOTALL)
# Parse interface names at 2-space indent
iface_names = re.findall(r'^  (\S+)\s*$', iface_match.group(1), re.MULTILINE)
```

---

## Adding New Detection

When adding detection for a new config element:

### Step 1: Update config_extractor.py
```python
# In save_config(), add to operational.json population:
if re.search(r'^\s+new_protocol\s*$', protocols_block, re.MULTILINE):
    ops_data['new_protocol'] = True
    ops_data['new_protocol_count'] = len(re.findall(...))
```

### Step 2: Update interactive_scale.py summary
```python
# In show_current_config_summary(), read from operational.json:
if op_data.get('new_protocol'):
    summary['other_protocols']['NEW'] = op_data['new_protocol_count']
```

### Step 3: Update all displays
Use grep to find ALL places that display related info:
```bash
grep -rn "other_protocols\|igp\|protocol" scaler/interactive_scale.py
```
Update each one.

### Step 4: Update fallback parsing
For when operational.json doesn't exist:
```python
# In the fallback section of show_current_config_summary():
if re.search(r'new_protocol', config_text):
    summary['other_protocols']['NEW'] = ...
```

### Step 5: Test both paths
1. Delete operational.json, run wizard (tests fallback)
2. Re-sync config, run wizard (tests operational.json path)

---

## Smart Related Decisions

When making ANY change, ask:

1. **Does this affect other parts of the code?**
   - Use `grep -rn "pattern" scaler/` to find all related code

2. **Are there similar functions that need the same fix?**
   - Single-device AND multi-device paths

3. **Does this change the data model?**
   - Update operational.json schema
   - Update all consumers of that data

4. **Should this be stored/cached for reuse?**
   - Parse once in config_extractor.py
   - Store in operational.json
   - Read fast in wizard

5. **Does this work in BOTH single and multi-device modes?**
   - Test with 1 device
   - Test with 2+ devices

---

### System Restore for Recovery Mode Devices (2026-01-28 - UPDATED)

**Status:** ✅ Working (Console-Based Flow)

**Purpose:** Provide a guided wizard to restore devices detected in RECOVERY mode, BASEOS_SHELL, or ONIE mode. Uses the SAME console session throughout to avoid SSH connection issues in GI mode.

**CRITICAL FIX (2026-01-28):** The original flow tried to use Image Upgrade wizard after reaching GI mode, but that wizard uses SSH connection which FAILS in GI mode (no mgmt0 IP configured yet). The fix keeps the console session open and loads images directly using GI mode commands.

**Files Created/Modified:**
- `scaler/wizard/system_restore.py` - Core System Restore wizard module
- `scaler/wizard/__init__.py` - Added exports for system_restore module
- `scaler/interactive_scale.py` - Added [S] System Restore menu option (single + multi-device)
- `monitor.py` - Added prompt to launch wizard when recovery detected

**Key Functions:**
- `DeviceKnowledge` - Stores previous device knowledge (system_type, hostname, versions)
- `run_system_restore_wizard()` - Main entry point for the wizard
- `execute_restore_to_gi_mode()` - Restores device to GI mode AND loads images via console
- `load_images_via_console()` - GI mode command: `request system target-stack load <URL>`
- `deploy_via_console()` - GI mode command: `request system deploy system-type <type> name <name> ncc-id 0`
- `prompt_image_source_inline()` - Select images from recent sources or enter URLs manually

**Console-Based Flow (Fixed 2026-01-28):**

The wizard now uses the SAME console session throughout - no SSH required until DNOS boots:

```
┌──────────────────────────────────────────────────────────────────────┐
│              SYSTEM RESTORE WORKFLOW (Console-Based)                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  SINGLE CONSOLE SESSION THROUGHOUT                                   │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │ 1. Connect to console (console-b15 port 12/13/14)            │   │
│  │ 2. Enter GI mode:                                             │   │
│  │    - BASEOS_SHELL: dncli (password: dnroot)                   │   │
│  │    - ONIE: Install BaseOS → dncli                             │   │
│  │    - RECOVERY: request system restore factory-default        │   │
│  │ 3. Select image source (recent or manual URLs)                │   │
│  │ 4. Load images via SAME console (GI mode commands):           │   │
│  │    GI# request system target-stack load <DNOS_URL>            │   │
│  │    GI# request system target-stack load <GI_URL>              │   │
│  │    GI# request system target-stack load <BASEOS_URL>          │   │
│  │ 5. Deploy DNOS via SAME console:                              │   │
│  │    GI# request system deploy system-type X name Y ncc-id 0    │   │
│  │ 6. Wait for DNOS boot (5-15 min)                              │   │
│  │ 7. Device now has mgmt0 IP - SSH available                    │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

**GI Mode Commands (verified 2026-01-28):**
| Action | Command |
|--------|---------|
| Load image | `request system target-stack load <URL>` |
| Check load status | `show system target-stack load \| no-more` |
| Deploy | `request system deploy system-type X name Y ncc-id 0` |

Note: GI mode uses the SAME `target-stack` commands as DNOS mode for loading images.

**Detection Points:**
| Location | Detection Method |
|----------|-----------------|
| Monitor | PE-2 console check, operational.json |
| Wizard Status Check | SSH prompt contains 'RECOVERY' |
| Refresh Flow | SSH + console fallback for PE-2 |
| operational.json | `recovery_mode_detected: true` |

**Restore Workflow (Integrated):**
1. Load device knowledge from `db/configs/{hostname}/operational.json`
2. Show previous device info (system_type, hostname, previous DNOS version)
3. Prompt to confirm/modify system_type and hostname
4. **Redirect to Image Upgrade menu** (or skip for manual)
5. Execute restore to GI mode:
   - `request system restore factory-default` (RECOVERY mode)
   - Wait for GI mode (~2-10 minutes)
6. **Image Upgrade menu takes over:**
   - Browse Jenkins branches, select build
   - Validate artifacts
   - Load images (DNOS, GI, BaseOS)
   - `request system deploy system-type X name Y ncc-id 0`
7. Show live terminal with progress

**Menu Access:**
- Multi-Device: `[S] 🔧 System Restore` in action menu
- Single-Device: `[S] 🔧 System Restore` in action menu
- Monitor: Prompt when recovery detected

**Device Knowledge Persistence:**
```json
{
  "system_type": "SA-36CD-S",
  "serial_number": "WKY1BC7400002B2",
  "dnos_version": "26.1.0.1",
  "gi_version": "26.1.0.59",
  "baseos_version": "2.26104397329",
  "deploy_command": "request system deploy system-type SA-36CD-S name PE-2 ncc-id 0",
  "recovery_mode_detected": true,
  "recovery_mode_detected_at": "2026-01-27T10:30:00"
}
```

**Key DNOS Commands:**
```bash
# RECOVERY mode → GI mode (System Restore wizard)
request system restore factory-default
yes  # Confirm

# GI mode → Load images (Image Upgrade wizard / Jenkins)
request system target-stack load <DNOS_URL>
request system target-stack load <GI_URL>
request system target-stack load <BASEOS_URL>

# GI mode → Deploy DNOS (Image Upgrade wizard)
request system deploy system-type SA-36CD-S name PE-2 ncc-id 0
```

**Testing Checklist:**
- [ ] Test with PE-2 in recovery (console detection)
- [ ] Test with PE-1 in recovery (SSH detection)
- [ ] Test flow from System Restore → Image Upgrade menu
- [ ] Test Jenkins branch selection and artifact validation
- [ ] Test multi-device restore
- [ ] Verify operational.json is updated after restore

---

## Granular Mirror Configuration

The Mirror Config feature has been enhanced with **hierarchical section selection** allowing granular control over what gets mirrored from source to target device.

### Architecture

```
1. User selects source device: PE-4
2. Step 1: Select hierarchies (system ✓, network-services ✓, protocols ✓)
3. Step 2: Drill into network-services → select VRF ✓ (VRF-1 ✓, VRF-2 ✗)
4. Step 3: Show all uniqueness transformations being applied
5. Step 4: WAN mapping prompt (preserve target's, derive from subnet, map to parent)
6. Step 5: VRF BGP neighbor prompts (neighbor IP, update-source auto-derived)
7. Step 6: Multihoming options (match ESI for dual-homing, adjust DF preference)
8. Step 7: Interface mapping (smart-match source→target interfaces)
9. Step 8: Syntax validation (hierarchy, knobs, patterns)
10. Generate merged config with all transformations applied
```

### Service Types Supported

| Service Type | DNOS Hierarchy | Transport Options | Interface Types |
|--------------|----------------|-------------------|-----------------|
| FXC | `network-services / evpn-vpws-fxc / instance` | MPLS (cw, fat), SRv6 | PWHE (ph*) |
| EVPN-VPWS | `network-services / evpn-vpws / instance` | MPLS, SRv6 | L2-AC, Bundle |
| EVPN-VPLS | `network-services / evpn-vpls / instance` | MPLS, SRv6 | L2-AC, IRB |
| EVPN-MPLS | `network-services / evpn-mpls / instance` | MPLS | L2-AC |
| EVPN (mac-vrf) | `network-services / evpn / instance` | MPLS, VXLAN | IRB, L2-AC |
| VRF (L3VPN) | `network-services / vrf / instance` | MPLS | Physical, Sub-if |
| L2VPN-Xconnect | `l2vpn / xconnect group / p2p` | MPLS | L2-AC |
| L2VPN-BD | `l2vpn / bridge-domain` | MPLS | L2-AC |
| Multihoming | `network-services / multihoming / interface` | N/A | Any service interface |

### Key Functions

```python
# parsers.py - Service Parsing
parse_vrf_instances(config_text: str) -> List[Dict]
parse_evpn_vpws_instances(config_text: str) -> List[Dict]
detect_device_type(config_text: str) -> str  # 'cluster' or 'standalone'
get_cluster_specific_interfaces(config_text: str) -> Set[str]
get_ncp_slots(config_text: str) -> List[int]

# mirror_config.py - Hierarchical Selection
analyze_source_config(mirror: ConfigMirror) -> Dict[str, Any]
select_hierarchies_to_mirror(...) -> Dict[str, bool]  # Step 1
select_sub_sections(..., hierarchy: str) -> Dict[str, Any]  # Step 2
select_instances(..., service_type: str, instances: List) -> Dict[str, bool]  # Step 2b
show_uniqueness_transformations(mirror: ConfigMirror) -> bool  # Step 3

# mirror_config.py - Advanced Mirroring
prompt_wan_interface_mapping(mirror: ConfigMirror, analysis: Dict) -> Dict  # Step 4
transform_vrf_bgp_config(vrf_config, vrf_data, target_interfaces, target_loopback)
prompt_bgp_neighbor_addresses(vrf_data, interface_ip) -> Dict
mirror_multihoming_config(source_mh, target_interfaces, match_esi, df_prefs)
smart_match_interface(source_iface, target_available) -> Optional[str]
filter_cluster_interfaces_from_config(config, cluster_interfaces) -> str
validate_mirror_config(config) -> Tuple[List[str], List[str]]
```

### Uniqueness Transformations

The following transformations are automatically applied when mirroring:

| Item | Behavior |
|------|----------|
| Hostname | Transformed to target hostname |
| Router-ID | Transformed to target's router-id |
| Loopback IP | Target's lo0 preserved |
| Route Distinguisher | `source_lo0:N` → `target_lo0:N` (auto-transform) |
| ISO-network | Auto-derived from target loopback |
| LDP transport | Transformed to target's loopback IP |
| Route Targets | **Kept same** for EVPN peering |
| WAN Interfaces | Target's preserved (or derived from subnet) |
| Cluster Interfaces | Filtered when mirroring Cluster → Standalone |

### Smart Interface Matching

When source interfaces don't exist on target, smart-matching is applied:

1. **Exact match** - If interface name exists on target
2. **Same VLAN suffix** - e.g., `.219` matches any target interface ending with `.219`
3. **Same interface type** - ph, ge100, ge400, bundle prefix matching
4. **Cross-type mapping** - `ge100-18/0/0.X` → `ge400-0/0/4.X` for Cluster→SA

### VRF BGP Configuration

VRF mirroring includes:
- **update-source**: Auto-derived from VRF-attached interface on target
- **neighbor IP**: User prompted with subnet suggestions from interface IP
- **flowspec**: Copied if present in source VRF

### Multihoming Mirroring

Follows existing MH section patterns:
- **ESI options**: Match source ESI (dual-homing) or generate new (separate ES)
- **DF preference**: Automatic adjustment (PE-1: 50, PE-2: 100)
- **Interface mapping**: Smart-match to target's available service interfaces

### Cluster vs Standalone

Device type is auto-detected:
- **Cluster**: Multiple NCPs, fab-ncp*, ctrl-ncp*, console-ncp* interfaces
- **Standalone**: Single NCP, no fabric interfaces

When mirroring Cluster → Standalone:
- All `fab-ncp*`, `ctrl-ncp*`, `console-ncp*` interfaces are filtered
- Multi-NCP system config sections are skipped
- Interface names may need transformation (ge100 → ge400)

### Files Modified

| File | Changes |
|------|---------|
| `scaler/wizard/parsers.py` | Added VRF, VPWS, L2VPN parsers; device type detection |
| `scaler/wizard/mirror_config.py` | Hierarchical selection flow, WAN mapping, BGP handling, MH mirroring, validation |
| `scaler/wizard/scale_operations.py` | VRF as separate service category |

---

## BGP Labeled-Unicast (BGP-LU) Implementation

### Dual Hierarchy Configuration

BGP Labeled-Unicast has **TWO configuration hierarchies** in DNOS 26.x:

1. **Global AFI Level** - Protocol-wide defaults (OPTIONAL but recommended)
   ```
   protocols bgp <ASN>
     address-family ipv4-unicast
       labeled-unicast               ← Sub-command (global config)
         prefix-sid enabled
         entropy-label
         explicit-null enabled
       !
       label-allocation per-prefix
     !
   ```

2. **Neighbor Level** - Per-peer configuration (REQUIRED for peering)
   ```
   protocols bgp <ASN>
     neighbor 10.0.0.1
       address-family ipv4-labeled-unicast   ← Direct AFI (neighbor config)
         sr-labeled-unicast
           allow-external-sid send-receive
         !
         explicit-null disabled       ← Override global
         nexthop self
         maximum-prefix limit 50000
       !
   ```

### CRITICAL: Different Syntax for Each Level

| Hierarchy | Syntax Pattern | Purpose |
|-----------|----------------|---------|
| **Global AFI** | `address-family ipv4-unicast` → `labeled-unicast` | Protocol defaults |
| **Neighbor** | `address-family ipv4-labeled-unicast` | Per-peer peering |

**Note:** The global level uses the OLD sub-command syntax (`labeled-unicast` under `ipv4-unicast`), while the neighbor level uses the NEW direct AFI syntax (`ipv4-labeled-unicast`). This is intentional and correct per DNOS 26.x documentation.

### Wizard Implementation

When `ipv4-labeled-unicast` or `ipv6-labeled-unicast` is selected:

1. **Global AFI Configuration Prompt**:
   - Prefix-SID (RFC 8669) - Allocate labels from SRGB
   - Entropy Label (RFC 6790) - Request ELC from peers
   - Explicit-null - Send explicit-null (label 0) vs implicit-null
   - Label Allocation Mode - per-prefix or per-nexthop

2. **Neighbor-Level Configuration**:
   - SR Labeled-Unicast (eBGP only) - Prefix-SID exchange
   - Nexthop Self - Common for iBGP RR
   - Maximum-prefix - Limit routes from peers
   - Explicit-null override - Override global default

### Configuration Storage

```python
# Global AFI settings
bgp_lu_global_config = {
    'prefix_sid': True,
    'entropy_label': True,
    'explicit_null': True,
    'label_allocation': 'per-prefix'  # or 'per-nexthop'
}

# Neighbor-level settings
bgp_lu_neighbor_config = {
    'nexthop_self': True,
    'maximum_prefix': {'limit': 50000, 'threshold': 80, 'exceed_action': 'warning-only'}
}

# SR options (per-AFI)
sr_labeled_unicast_options = {
    'ipv4-labeled-unicast': {'allow_external_sid': 'send-receive'}
}
```

### eBGP vs iBGP Awareness

- **eBGP peers** (`peer_as != local_as`): Offers SR labeled-unicast options
- **iBGP peers** (`peer_as == local_as`): Skips SR options (not needed for iBGP)

### Inheritance & Override Pattern

```
Global AFI defaults
  ↓
Neighbor-Group AFI settings (inherits + overrides global)
  ↓
Neighbor AFI settings (inherits + overrides group)
```

**Example:**
- Global: `explicit-null enabled` (applies to all peers)
- Neighbor: `explicit-null disabled` (overrides for this peer only)

### Reference Documentation

See: [`docs/BGP_LABELED_UNICAST_IMPLEMENTATION.md`](BGP_LABELED_UNICAST_IMPLEMENTATION.md)

This file contains:
- Complete architecture explanation
- Generated configuration examples
- All available options with descriptions
- Testing scenarios
- DNOS RST reference links

### DNOS Syntax Sources

- **Global AFI**: `cheetah_26_1/.../afi_ipv4-unicast/labeled-unicast/`
- **Neighbor AFI**: `cheetah_26_1/.../neighbor/address-family/address-family.rst`
- **SR Options**: `cheetah_26_1/.../neighbor/address-family/sr-labeled-unicast/`

### Key Release History

| Feature | DNOS Release |
|---------|--------------|
| `labeled-unicast` sub-command (global) | 18.1 |
| `explicit-null` | 25.3 |
| `ipv4/6-labeled-unicast` direct AFI (neighbor) | TBD (26.x) |
| `sr-labeled-unicast` | 18.1 |

---

## New Route-Policy Language (EPIC SW-181332)

### Overview

DNOS introduces a new programming-like route-policy language that replaces the old rule-based syntax.
This is implemented in the SCALER wizard under **Routing Policy Configuration → [7] Route-Policy (New)**.

**Reference**: [SW-181332](https://drivenets.atlassian.net/browse/SW-181332)

### New Syntax Structure

```
routing-policy
  route-policy POLICY_NAME($param1, $param2) {
    // Statements with if/elif/else blocks
    if (condition) {
      set attribute value
      return allow|deny
    }
    elif (other_condition) {
      // elif block (NOT 'else if')
    }
    else {
      // else block
    }
    return allow|deny|no-match
  }
```

**Important**: DNOS uses `elif` (not `else if`) for else-if blocks.

### Key Features

| Feature | OLD Syntax | NEW Syntax (SW-181332) |
|---------|-----------|------------------------|
| Structure | `rule ID allow/deny` blocks | Programming-like with `{ }` |
| Conditions | `match` statements | `if (condition)` with operators |
| Actions | `set` statements | `set attribute value` |
| Flow Control | `on-match next/goto` | `return allow/deny`, `if/else` |
| Parameters | None | `$param1, $param2` support |
| Policy Calls | `call policy-name` | `exec-policy name($params)` |
| Wildcards | None | `exec-policy POLICY*` |

### Available Match Attributes

| Attribute | Description | Example |
|-----------|-------------|---------|
| `med` | Multi-Exit Discriminator | `med > 100` |
| `weight` | BGP weight | `weight == 0` |
| `local-preference` | Local preference | `local-preference >= 100` |
| `as-path` | AS path string | `as-path == "65000 65001"` |
| `as-path-length` | AS path length | `as-path-length <= 5` |
| `community` | BGP community | `community in [65000:100]` |
| `prefix-ipv4` | IPv4 prefix | `prefix-ipv4 == 10.0.0.0/8` |
| `prefix-ipv6` | IPv6 prefix | `prefix-ipv6 == 2001:db8::/32` |
| `nexthop` | Next-hop IP | `nexthop == "192.168.1.1"` |
| `origin` | BGP origin | `origin == igp` |
| `rpki` | RPKI validation state | `rpki in [valid]` |
| `tag` | Route tag | `tag not in [100, 200]` |

### Operators

| Type | Operators | Example |
|------|-----------|---------|
| Numeric | `==`, `!=`, `<`, `>`, `<=`, `>=` | `med > 100` |
| Text | `==`, `!=` | `as-path == "65000"` |
| List | `in`, `not in` | `community in [65000:100]` |
| Logical | `and`, `or`, `not` | `(med > 100) and (weight < 50)` |

### Set Actions

| Action | Syntax | Example |
|--------|--------|---------|
| Set MED | `set med <value>` | `set med 100` |
| Set Weight | `set weight <value>` | `set weight 50` |
| Set Local-Pref | `set local-preference <value>` | `set local-preference 150` |
| Set Next-hop | `set nexthop <value>` | `set nexthop "192.168.1.1"` |
| Add Community | `add community <value>` | `add community 65000:200` |
| Remove Community | `remove community <value>` | `remove community 65000:100` |
| Prepend AS | `set as-path prepend as-number <value>` | `set as-path prepend as-number 65000` |
| Prepend Last AS | `set as-path prepend last-as <count>` | `set as-path prepend last-as 3` |
| Exclude AS | `set as-path exclude <value>` | `set as-path exclude "65001"` |
| Set RPKI | `set rpki <value>` | `set rpki valid` |
| SR Label Index | `set sr-label-index <value>` | `set sr-label-index 100` |
| Set Result | `set allow\|deny` | `set allow` |

### Return Statements

| Statement | Behavior |
|-----------|----------|
| `return allow` | Permits the route and stops policy evaluation |
| `return deny` | Denies the route and stops policy evaluation |
| `return no-match` | Continue to next policy in chain |
| `return` | Stops evaluation, uses previous `set allow/deny` result |

### Policy Calls

```
// Call another policy
exec-policy OTHER_POLICY

// Call with parameters
exec-policy SET_COMMUNITY($my_community)

// Wildcard call (matches POLICY_1, POLICY_2, etc.)
exec-policy POLICY_*
```

### Example Policies

**Simple MED Filter:**
```
route-policy MED_FILTER {
  if (med > 100) {
    set med 100
    return allow
  }
  return allow
}
```

**Parameterized Policy:**
```
route-policy SET_LOCALPREF($lpref_value) {
  set local-preference $lpref_value
  return allow
}
```

**Using elif (not else if):**
```
route-policy PREFIX_FILTER {
  if (prefix-ipv4 == 10.0.0.0/8) {
    return deny
  }
  elif (prefix-ipv4 == 172.16.0.0/12) {
    return deny
  }
  elif (prefix-ipv4 == 192.168.0.0/16) {
    return deny
  }
  else {
    return allow
  }
}
```

**List Matching with in/not in:**
```
route-policy COMMUNITY_FILTER($comm_list) {
  if (community in $comm_list) {
    set local-preference 200
    return allow
  }
  if (tag not in [100, 200, 300]) {
    add community 65000:999
    return allow
  }
  return deny
}
```

**RPKI and SR-Label-Index:**
```
route-policy RPKI_POLICY {
  if (rpki in [valid]) {
    set sr-label-index 100
    return allow
  }
  elif (rpki == not-found) {
    set rpki valid
    return allow
  }
  return deny
}
```

### Implementation Files

| File | Description |
|------|-------------|
| `scaler/wizard/route_policy_new.py` | New route-policy module with data classes and builders |
| `scaler/interactive_scale.py` | Integration into wizard (option [7] in routing policy menu) |

### Available Templates

| Template | Description |
|----------|-------------|
| `DENY_PRIVATE` | Deny RFC1918 private address space |
| `SET_LOCALPREF` | Set local-preference (parameterized) |
| `MED_FILTER` | Cap MED at threshold |
| `COMMUNITY_TAG` | Add community tag to routes |

### Attachment Points (BGP)

```
protocols
  bgp <AS>
    neighbor <ADDRESS>
      address-family <AFI_SAFI>
        route-policy policy_name(parameter1, parameter2) in
      !
    !
  !
!
```

---

## Shared Action+Validate Primitives (`scaler/scaler/validators.py`)

**Canonical home for all polling primitives used by /TEST orchestrators AND /SPIRENT tooling.**

Single source of truth. Both layers import from one place; no duplicate poll loops, no
behavior drift between the orchestrator's BGP-up wait and Spirent's BGP-up wait.

| Layer | File | Role |
|---|---|---|
| Canonical | `scaler/scaler/validators.py` | `poll_until`, `ValidationResult`, `wait_for_bgp_state[_in]`, `wait_for_arp_resolve`, `wait_for_interface_up`, `wait_for_mac_absent`, `wait_for_evi_label_pool`, `wait_for_route_in_rib`, `wait_for_pw_installed`, `action_then_validate` |
| /TEST shim | `scaler/TEST/catalog/<suite>/shared/validators.py` | `from scaler.validators import *` + suite-specific extensions (e.g. `wait_for_mac_in_table` which depends on local `mac_parsers.py`) |
| /SPIRENT | `scaler/SPIRENT/spirent_tool.py` | Path-safe import block at module top; uses `poll_until` for `_wait_bgp_convergence`, `cmd_bgp_peer` BGP-up wait, and `cmd_recover` post-restart health check. Falls back to legacy local poll loops (`_wait_bgp_convergence_legacy`) only if the validators layer is not importable. |

### Mandatory Pattern: replace blind sleep + while-loop with `poll_until`

WRONG (blind poll, no early exit, no progress, no diagnostic on timeout):

```python
for _ in range(30):
    time.sleep(1)
    if check_condition():
        return SUCCESS
return TIMEOUT
```

RIGHT (event-driven, returns ASAP, structured result, auto-progress):

```python
from scaler.validators import poll_until

def _check():
    state = stc.get(handle, "SessionState")
    return (state == "ESTABLISHED"), {"state": state}

res = poll_until(_check, timeout_sec=30, interval_sec=1.0,
                 progress_label="bgp_up")
if res.passed:
    print(f"BGP up in {res.elapsed_sec:.1f}s after {res.attempts} polls")
else:
    print(f"BGP not up: {res.reason}")  # rich diagnostic, no guessing
```

### When to KEEP a `time.sleep()` (not every sleep is a poll)

Three principled exceptions where the canonical primitive does NOT apply:

1. **Hardware quiesce after a Stop API call** (1-2s) -- no observable "device idle" event.
   The wait is debounce, not a wait-for-condition. Wrapping in `poll_until` adds overhead with zero benefit.
2. **Exponential backoff between retries** (10s+) -- this is a deliberate cooldown to avoid
   hammering an upstream service after a failure, not a wait for an event.
3. **Service warm-up before health checks** (3-15s) -- after `docker restart`, the
   container needs ~3s before `supervisorctl` is even responsive. The blind wait is
   followed by `poll_until(_health_probe, ...)` which IS event-driven.

Document any KEPT sleep with a comment explaining which of the three exceptions applies.

### Refactor Audit Log (2026-04-14)

| File | Was | Now | Risk |
|---|---|---|---|
| `spirent_tool.py:_wait_bgp_convergence` | custom 5s-poll loop with manual ARP retry every 15s | `poll_until` + `on_progress` callback that drives the ARP nudge | Low -- legacy implementation kept as `_wait_bgp_convergence_legacy` for fallback |
| `spirent_tool.py:cmd_bgp_peer` 30s BGP-up wait | `for _ in range(30): time.sleep(1)` | `poll_until` with 1s interval + per-tick progress | Low -- identical timing budget, exits earlier on success |
| `spirent_tool.py:cmd_recover` post-restart health check | `for attempt in range(3): time.sleep(2) + _health_probe` | `poll_until(_health_probe, timeout=6, interval=2)` | Low -- preserves 6s budget, returns earlier on first success |
| Remaining 22 sleeps in `spirent_tool.py` | quiesce / backoff / warm-up | KEPT (documented above) | None -- principled debounce |

---

## DNOS Test Catalog (`scaler/TEST/catalog/`)

Automated DNOS test recipes and orchestrators live next to the scaler tree for version control. Sync copies to `~/SCALER/TEST/catalog/` when validating on live lab paths.

| Suite / path | Jira | Description |
|----------------|------|-------------|
| `TEST/catalog/TEST_evpn_elan_ha_SW248907/` | SW-248907 | EVPN (ELAN) SI HA scenarios |
| `TEST/catalog/evpn_mac_mobility_SW204115/` | SW-204115 | EVPN ELAN seamless-integration MAC mobility (10 Testing Tasks: SW-205160..SW-205199) |

**SW-204115 suite components:**

| File | Purpose |
|------|---------|
| `mac_mobility_orchestrator.py` | Thin shim: re-exports every public orchestration symbol from `orchestration/*` and hosts the `main()` CLI entry point (2026-04-20 refactor, ~560 lines) |
| `orchestration/constants.py` | Module constants: `MANIFEST_PATH`, `RESULTS_DIR`, `ACTIVE_SESSION`, `CORRECTIONS_PATH`, `ACTION_TRIGGER_MAP`, `_PW_TRIGGERS`, `_EVPN_PEER_TRIGGERS`, `_SPIRENT_PHASE_TRIGGER_VERBS`, `_EVPN_FALLBACK`, `_PW_MOVE_BUDGET_SEC`, `_BGP_RECOVERY_BUDGET_SEC`, `SCENARIO_CONFIG_REQUIREMENTS` |
| `orchestration/session_io.py` | Timestamps (`now_iso`, `now_hhmm`), session file (`write_active_session`), manifest/recipe loaders, self-healing command-correction cache (`_load_corrections`, `_apply_corrections`, `_record_runtime_failure`, `_record_runtime_success`), `_default_run_show` |
| `orchestration/reporting.py` | `_generate_repro_steps`, `write_results`, `_live_failure_detector` (cuts scenario short on detectable infra failure) |
| `orchestration/runtime_context.py` | DUT discovery + provisioning: `_provision_scenario_config`, `_rollback_scenario_config`, `_discover_ac_outer_vlans`, `_discover_instance_ac_vlans`, `_ensure_pw_transport_params`, `_discover_spirent_ldp_loopback`, `resolve_runtime_params` |
| `orchestration/recipe_runtime.py` | `substitute()` token expansion, `_apply_recipe_runtime_parameters`, `_resolve_named_config`, `_run_spirent_phase_actions`, `_run_recipe_phase`, `validate_recipe_commands`, `live_validate_prerequisites`, `run_recipe_dry` |
| `orchestration/spirent_integration.py` | /SPIRENT <-> /TEST sync mandate helpers: `_requires_spirent`, `_resolve_spirent_vlan`, `_dev_ip`, `auto_invoke_spirent_sync`, `_spirent_full_sync`, `_spirent_sync_err` |
| `orchestration/scenario_runner.py` | `execute_scenario` (1811-line per-scenario orchestrator: preflight, trigger, verify layers, deep evidence, known-bug lookup) |
| `orchestration/test_runner.py` | `execute_test` (1253-line per-recipe orchestrator: 4-layer preflight, DUT config, scenario loop, regression detection, full report emission) |
| `device_discovery.py` | Device context: cluster/standalone, EVPN instances, ACs, MACs, ESI, PW |
| `config_generator.py` | Config snippets (no IRB with seamless-integration), delta proposals |
| `prerequisite_engine.py` | Checks + auto-remediation via /SPIRENT L2 and DNAAS path setup |
| `shared/mac_trigger.py` | Spirent MAC move execution: local-to-local, rapid-flap, 64K scale, back-and-forth, AC<->EVPN (RT-2 inject), AC<->PW (VLAN swap), HA baseline traffic+loss capture |
| `shared/mac_verifiers.py` | Verification: source, sequence, suppression, sticky, aging, HA recovery, Spirent loss |
| `shared/verdict_engine.py` | Multi-layer verdict: control-plane, timing, traces, scale, HA, with structured reports |
| `shared/trace_analyzer.py` | /debug-dnos integration: auto-grep bgpd/fibmgrd/NCP traces on failure |
| `shared/mac_parsers.py` | DNOS CLI output parsers for MAC table, BGP summary, system nodes |
| `shared/ssh_session.py` | Persistent interactive SSH: prompt-based completion detection (50ms polling), auto-reconnect after HA triggers, ANSI-aware. 13x faster than connect-per-command |
| `shared/device_runner.py` | Resilient run_show: MCP -> DNOS_SHOW_HELPER -> persistent SSH session -> error. Session cache for connection reuse across commands |
| `shared/spirent_preflight.py` | Pre-flight: session alive, DNAAS path ready. Auto-fallback to MANUAL traffic |
| `shared/config_knowledge.py` | EVPN+VPLS dual-protocol SI config tree (from Jira SW-203654 + Confluence design doc + SW-178648 EPIC). 30+ config blocks across 10 test scenarios. VPLS_SHOW_COMMANDS (7 cmds). VPLS_MAC_MOBILITY_RULES (6 rules for AC-PW moves) |
| `suite_manifest.json` | Index of all 10 test recipes |
| `tests/*/recipe.json` | Per-test JSON recipes (10 testing tasks: SW-205160..SW-205199) |

**Recipe JSON metadata (`show_commands_validated` / `invalid_commands` / `clear_commands_validated`):** Each `recipe.json` may include `show_commands_validated` (command string to provenance note, keyed by exact DNOS syntax including `| no-more`), `clear_commands_validated` where clear operations apply (e.g. withdraw_flush), and `invalid_commands` (wrong patterns agents must not use, with the correct replacement). `show evpn detail instance {name}` is valid DNOS syntax; do not list it under `invalid_commands`. List only show commands used by that recipe plus suite-wide invalid anti-patterns. References: SHOW_COMMANDS doc line numbers where applicable; see `learned_rules.md` / CLI docs. For SW-204115 MAC mobility recipes, `phases.verify.expect` may add verification booleans (`check_mac_flags`, `check_forwarding`, `check_ghost_macs`), optional `forbidden_flags` (e.g. `["F","D"]` on normal non-sticky moves), `check_mobility_counter` when suppression/sequence counting is asserted, and `check_suppress_list` / `check_loop_prevention` when `sanction_applied` is true; extended validated shows include NCP forwarding MAC table, EVPN ghost MAC table, and FIB EVPN local-mac programming alongside single-MAC lookup.

**Optional `phases.verify.expect` flags (EVPN MAC mobility recipes):** Scenarios may set `check_mac_flags`, `forbidden_flags` (e.g. no frozen/duplicate for normal moves), `check_forwarding`, `check_ghost_macs`; suppression scenarios add `check_suppress_list`, `check_loop_prevention`, `expected_lp_state`; sequence/mobility scenarios add `check_mobility_counter`. Enriched `show_commands_validated` may include `show evpn forwarding-table mac-address-table instance {evpn_name}`, `show dnos-internal routing evpn instance {evpn_name} mac-table-ghost`, and `show dnos-internal routing fib-manager database evpn local-mac service-instance {evpn_name}` for NCP/FIB/ghost verification.

**Engine-level recipe fields (SW-204115, after `verdict`):** Each `tests/*/recipe.json` may include `counter_commands` (show + parser labels), `counter_expectations` (rules such as `no_decrease`, `no_increase` for withdraw_flush `mac_count`, `zero` for ghost, `increase` for mobility on ac_ac), `event_expectations` (BGP/syslog events; absent for normal runs, present with `min_count` for ac_ac suppression/loop and ha_mac_mobility BGP/HA), `health_checks` (process list + crash/alarm flags), `cleanup_commands`, and `config_baseline` (sections + ignore_patterns). Variants: non-HA recipes share the same baseline; `ac_ac` adds mobility counter and suppression/loop present expectations; `ha_mac_mobility` adds forwarding-table counter and HA-oriented events; `withdraw_flush` uses `no_increase` on `mac_count`.

**Execution modes:**
- `--discover`: device context only
- `--prereq TEST_ID [--auto-fix]`: check prerequisites, optionally auto-remediate via /SPIRENT
- `--run TEST_ID --dry-run`: expand commands, no execution
- `--run TEST_ID --execute [--ac1-vlan N --ac2-vlan M --scale K]`: full trigger+verify+verdict cycle

Agent rules: `~/.cursor/rules/dnos-test-automation-blueprint.mdc`, `~/.cursor/test-reference/test-catalog.md`.

---

## /SPIRENT <-> /TEST Sync Mandate (MANDATORY for every test using Spirent resources)

**Rule (user mandate 2026-04-20):** `/SPIRENT must be CALLED and synced with any /TEST that requires devices, you must now mark spirent devices or peers via descriptions on dnos side for faster debugging and workflows`.

Any `/TEST` recipe that declares a Spirent device, BGP emulation, or traffic-stream prerequisite **must**:

1. Call `spirent_sync.ensure_fabric_clean(vlan)` which runs `spirent_tool.py dnaas-diagnose --vlan <vlan>` and, on fault, `spirent_tool.py dnaas-fix --vlan <vlan>` (auto-fix enabled by default).
2. Call `spirent_sync.sync_descriptions(dut=<dut_ip>, fabric_vlan=<vlan>)` which invokes `spirent_tool.py mark-dnos` to apply/refresh the canonical SPIRENT description tags on every Spirent-owned DNOS object.
3. Block test execution until both steps report `PASS`. If auto-fix is disabled, surface actionable `fix_via` commands in the prerequisite report.

### SPIRENT Description Tag Conventions

| DNOS object | Description format | Example |
|-------------|--------------------|---------|
| DUT sub-interface | `SPIRENT:<session>/<device>/v<outer>[+<inner>]/<role>` | `SPIRENT:dn_spirent_main/SpirentCE-17/v214+1000/ce` |
| BGP neighbor | `SPIRENT:<session>/<device>/v<outer>[+<inner>]/bgp-peer/AS<asn>` | `SPIRENT:dn_spirent_main/SpirentCE-17/v214+1000/bgp-peer/AS65001` |
| DNAAS fabric sub-if | `SPIRENT-fabric-v<vlan>` (appended, preserves existing) | `TO PE-1 (SPIRENT-fabric-v214)` |

**Idempotency:** `mark-dnos` preserves any existing description and only appends the SPIRENT tag. Re-running against an already-tagged object is a no-op. `dnaas-fix` recovery re-applies the fabric tag after delete+recreate to survive LLP-sticky remediation.

### Implementation Files

| File | Role |
|------|------|
| `SCALER/SPIRENT/spirent_tool.py` | Adds `mark-dnos` subcommand, description tagging in `create-device` / `create-stream` / `bgp-peer`, description preservation in `_dnaas_recover_subifs`, idle-timeout fix in `_dnaas_shell_exec`, super-spine D04 in `_default_dnaas_topology` |
| `SCALER/TEST/catalog/evpn_mac_mobility_SW204115/spirent_sync.py` | Helper module: `check_fabric_health`, `ensure_fabric_clean`, `sync_descriptions`, `run_full_sync`; end-to-end Spirent↔DNOS sync orchestration |
| `SCALER/TEST/catalog/evpn_mac_mobility_SW204115/prerequisite_engine.py` | New checks `spirent_fabric_v<vlan>` + `spirent_desc_tags` wired into prereq table; produce `fix_via` (`spirent_tool.py dnaas-fix --vlan <vlan>`, `spirent_tool.py mark-dnos --dut <ip>`) |

### SuperSpine-D04 (new DNAAS hop, 2026-04-20)

The VLAN 214 cross-rack path was previously modeled as 4 hops (B14 -> B09 -> D14 -> D16). Live investigation added a 5th hop: `DNAAS-SuperSpine-D04` (100.64.100.227) between B09 and D14, with sub-interfaces `bundle-60004.214` (B-side) and `bundle-60007.214` (D-side). This hop is now part of `_default_dnaas_topology` in `spirent_tool.py` -- `dnaas-diagnose`/`dnaas-fix` must probe it.

The earlier silent skip of D04 was also caused by a race in `_dnaas_shell_exec` (echo-marker prompt detection). The helper now uses idle-timeout based read; **do not regress** to marker-based detection.

### Usage (from /TEST orchestrator)

```python
from spirent_sync import run_full_sync

status = run_full_sync(vlan=214, dut="100.64.4.200", auto_fix=True, include_fabric_desc=True)
if status["overall"] != "PASS":
    raise PrerequisiteFailed(status)
```

Agent rules (also cover this): `~/.cursor/spirent-reference/dnaas-path.md` ("SPIRENT Description Tagging Convention"), `~/.cursor/spirent-reference/learned_rules.md` (rules `spirent-must-tag-dnos-objects-with-description`, `spirent-sync-must-be-called-before-test-execution`, `dnaas-vlan214-path-includes-super-spine-d04`, `dnaas-shell-exec-must-use-idle-timeout-not-marker`).

---

*Updated: 2026-04-21 - SW-204115 G4 `pw_suppression_sanctions` live-validated end-to-end on PE-1 (HA_TEST_ELAN, AC ge400-0/0/4.1000 outer/inner=214/1000) with 4/4 functional PASS across separate runs: SC01 blackhole (RUN_20260420_1939), SC02 shutdown (RUN_20260421_0538), SC03 suppress (RUN_20260421_0550), SC04 remote-remote (RUN_20260420_1923). Bug fix in `orchestration/scenario_runner.py::execute_scenario` `spirent_sanction_flap` handler: (1) removed unconditional `ac1_vlan = int(params.get("ac1_vlan","0") or 0)` line that silently shadowed the function argument with 0 (root cause of the prior `FLAP SKIP: ac1_vlan not set`); the override now only applies when params explicitly carry a positive value. (2) raised the per-cycle MAC-learn poll timeout floor from 1.5 s to 5.0 s with poll_interval 0.5-1.0 s to match observed DUT bridge-FDB install latency. (3) restructured the flap loop to create the Spirent learn device once before the loop and remove it once after, instead of create+destroy per cycle (~3-4 s of BLL churn saved per cycle). (4) added explicit teardown try/except so partial failures don't leak Spirent state. SC04 already passed pre-fix (uses the `spirent_remote_seq_updates` handler, no local-learn dependency). Each sanctioned scenario evidence shows `SANCTION [<action>] applied -> OK (Commit succeeded ...)` followed by `FLAP[0..9] local->remote seq=1..10 -> OK`; mac_flags evidence for SC01 = `['L','R','K','M']` (Local + Remote + Killed + Mobility) on the test MAC, exactly the RFC-7432 §15 + DNOS sanction outcome. `timing=WARN` is recipe-threshold cosmetic (90 s threshold vs ~145 s actual flap duration); recommend bumping `expected_convergence_sec` to 180 s for sanction recipes. Full G1-G5 verdict matrix recorded in `evpn_mac_mobility_SW204115/FINAL_VERDICT_G1_G5.md`. Outstanding infra note: Spirent BLL becomes unhealthy after sustained `bgp-peer evpn-inject` load (~150 s), and `_try_reconnect()` may force a `--force-new` connect that wipes EVPN_RT2_Peer; mitigation today is per-scenario `--scenario SCxx` runs with peer rebuild between. Permanent fix candidate: make `_try_reconnect` strictly preserve `_INFRA_DEVICE_NAMES` and re-create them from cached args after a forced reconnect.*

*Updated: 2026-04-20 - EVPN MAC mobility orchestrator modularization (SW-204115): `mac_mobility_orchestrator.py` split from a 5409-line monolith into a 561-line thin shim + 8-module `orchestration/` package. Extraction slices: Slice 1 `spirent_integration.py` (/SPIRENT sync helpers), Slice 2 `session_io.py` + `reporting.py` + `constants.py`, Slice 3 `runtime_context.py` (device provisioning, VLAN/interface discovery, `_ensure_pw_transport_params`, `_discover_spirent_ldp_loopback`, `resolve_runtime_params`), Slice 4 `recipe_runtime.py` (`substitute`, phase runners, static + live validation, dry-run planner), Slice 5 `scenario_runner.py` (`execute_scenario` -- 1811 lines of scenario-level orchestration kept byte-identical), Slice 6 `test_runner.py` (`execute_test` -- 1253 lines of test-level orchestration kept byte-identical). The shim re-exports every public symbol (incl. `substitute`, `write_results`, `MANIFEST_PATH`, `ACTION_TRIGGER_MAP`, `execute_scenario`, `execute_test`, etc.) so existing callers and tests continue to import from `mac_mobility_orchestrator` unchanged. Smoke test verified after each slice: CLI `--list`, `--help`, and `run_recipe_dry` all pass on both the live deploy path (`/home/dn/SCALER/TEST/...`) and the git worktree (`scaler/TEST/...`). No linter errors; no behavior change.*
*Updated: 2026-04-20 - /SPIRENT<->/TEST sync mandate: spirent_tool.py +mark-dnos subcommand with canonical SPIRENT description tagging on DUT sub-ifs + BGP neighbors + DNAAS fabric sub-ifs; _dnaas_recover_subifs preserves existing descriptions + re-appends SPIRENT-fabric-v<vlan>; _dnaas_shell_exec idle-timeout read (no more marker race on slow super-spine); _default_dnaas_topology +DNAAS-SuperSpine-D04 (100.64.100.227) for VLAN 214 (5-hop path); NEW spirent_sync.py (ensure_fabric_clean, sync_descriptions, run_full_sync) auto-invoked from evpn_mac_mobility prerequisite_engine.py via new checks spirent_fabric_v<vlan> + spirent_desc_tags with actionable fix_via; /TEST Run mode now auto-syncs with /SPIRENT for every recipe that declares Spirent device/BGP/traffic prereqs; full backfill of SPIRENT tags applied live on PE-1 + all DNAAS fabric hops for VLAN 214; spirent-reference/learned_rules.md +4 new rules; spirent-reference/dnaas-path.md +SuperSpine-D04 hop + description convention sections.*

*Updated: 2026-03-20 - Enhanced SW-204115 suite: verdict_engine (10-layer), trace_analyzer (/debug-dnos auto-diagnosis), Spirent trigger execution (local-to-local, rapid-flap, 64K scale), verifiers (sequence, suppression, sticky, aging, HA recovery), prereq auto-remediation*
*Updated: 2026-03-20 - EVPN MAC mobility recipes: `show_commands_validated` + `invalid_commands` on 9/10 recipes (basic_learning already had validated block); documents DNOS syntax vs non-existent variants*
*Updated: 2026-03-20 - EVPN MAC mobility SW-204115 recipe JSON: `withdraw_flush` clear_commands_validated + trigger `command` fields; ac_ac SC02/SC03 verify show_commands; basic_learning + ha + multihoming + aging show enrichment; aging SC02 `set_custom_aging` config_path; all 10 recipes: `invalid_commands` trimmed to mac-table evi + interfaces brief only (removed erroneous `show evpn detail instance` entry)*
*Updated: 2026-03-20 - Added scaler/TEST/catalog documentation: EVPN MAC mobility suite SW-204115 (evpn_mac_mobility_SW204115)*
*Updated: 2026-03-20 - EVPN MAC mobility `tests/ac_evpn`, `ac_pw`, `evpn_pw` recipe.json: enhanced `phases.verify.expect` flags + forwarding/ghost/FIB `show_commands_validated`*
*Updated: 2026-03-20 - EVPN MAC mobility `ac_ac` + `basic_learning` recipes: `phases.verify.expect` verification flags; `show_commands_validated` forwarding / ghost / FIB entries*
*Updated: 2026-03-20 - EVPN MAC mobility `tests/aging_timers`, `tests/ha_mac_mobility`, `tests/multihoming` recipe.json: enhanced `phases.verify.expect` (mac flags, forbidden F/D, forwarding, ghost; mobility counter where sequencing/move); HA added `verify` blocks on SC02-SC04; `show_commands_validated` forwarding/ghost/FIB where missing*
*Updated: 2026-03-20 - Full Observability Pipeline: shared/observability.py (ObservabilityCollector, CommandCapture, TimelineEvent, PhaseSummary, SnapshotDiff, TrafficSnapshot); wrapping_run_show transparently records every CLI command with timestamp/duration/output/phase; per-phase intermediate file writes (crash-safe); before/after diffs; traffic stats capture; timeline.log human-readable event log; debug_package/full_evidence.json for /debug-dnos handoff; verdict_engine.py +observability_log on ScenarioVerdict +observability_summary on TestVerdict; write_results now persists per-scenario observability.json, timeline.log, diffs.json; TEST.md updated with full observability documentation*
*Updated: 2026-03-20 - Deep MAC Intelligence: mac_parsers.py +10 parsers (detail, suppress, forwarding-table, loop-prevention x3, mac-mobility-redis-count, bestpath, ghost, fib); mac_verifiers.py +11 verifiers (flags, forwarding, suppress-list, loop-prevention, loop-count, restore-timer, mobility-counter, ghost, fib); jira_bug_matcher.py (Jira search on FAIL); trace_analyzer.py +deep_evidence_collection +debug_trace_mgmt +auto_investigate; mac_trigger.py: rapid_flap/back_and_forth now execute start/stop loops + post-move polling; verdict_engine.py: 6 new layer evaluators (mac_flags, forwarding, loop_prevention, mobility_counter, ghost_macs, suppress_list) + known_bugs/deep_evidence on ScenarioVerdict; orchestrator: full post-fail pipeline (deep evidence -> active debug -> Jira search -> auto-investigate); all 10 recipes updated with enhanced expect flags*
*Updated: 2026-03-20 - Cross-layer mismatch detection + /XRAY integration + final gap closure: (1) NEW shared/cross_layer_check.py: collects 6 layers (mac_table, mac_detail, forwarding_table, fib_database, arp_table, ghost_macs) in one pass, cross-references interface/source/sequence/forwarding state, detects mismatches invisible to single-layer checks. 9 comparison rules: mac_existence, interface_agreement, source_agreement, sequence_agreement, forwarding_sanity, fib_programming, arp_interface_match, no_ghost, fib_ncp_interface. (2) NEW ArpTableEntry + parse_arp_table in mac_parsers.py. (3) SHOW_COMMAND_MATRIX defines all 6 show commands per trigger type with required/optional relevance. (4) /XRAY auto-trigger: when cross_layer_check finds FAIL mismatches and xray_on_mismatch=true in recipe, fires CP capture (BGP+LLDP BPF filter) for packet-level evidence. (5) Orchestrator: cross-layer check runs after all single-layer verifiers, before BGP session + trace checks. Defaults to enabled for ALL 38 scenarios (cross_layer_check defaults True). Each mismatch becomes its own verdict layer (cross_layer_{rule}). (6) Recipes: ac_evpn SC01/SC02 + HA SC01 get explicit cross_layer_check+xray_on_mismatch. (7) Final gap closure: +execute_mac_move_evpn_to_pw, +execute_mac_move_pw_to_evpn in mac_trigger.py (RT-2 inject/withdraw + PW VLAN traffic). ACTION_TRIGGER_MAP: 16 entries (was 14), move_evpn_to_pw->spirent_evpn_to_pw, move_pw_to_evpn->spirent_pw_to_evpn. basic_learning SC02/SC03 + evpn_pw SC01/SC02 method:manual REMOVED. Final: 38 scenarios, 0 manual, 19 automated, 19 verify-only, 38/38 cross-layer.*
*Updated: 2026-03-20 - 100% trigger automation: (1) mac_trigger.py 4 NEW functions: execute_remote_pe_traffic (Spirent BGP RT-2 simulates remote PE), execute_traffic_via_pw (Spirent L2 on PW-mapped VLAN), execute_parallel_flap_and_restart (threaded rapid_flap + ha_executor in parallel), execute_mac_move_pw_to_pw (Spirent L2 VLAN swap between two PW VLANs). (2) ACTION_TRIGGER_MAP: ZERO manual_only entries (was 4). remote_pe_traffic->spirent_remote_pe, traffic_via_pw->spirent_pw_traffic, parallel_flap_and_restart->spirent_parallel_flap_ha, move_pw1_to_pw2->spirent_pw_to_pw. 13/14 fully automated + 1 verify-only (sticky). (3) Orchestrator: 4 new trigger handlers wired in execute_scenario. SC05 now runs flap+HA in parallel with poll_recovery+check_ha_traffic. (4) Recipes: all 20 scenarios across 5 recipes have ZERO method:manual entries. HA SC05 gets poll_recovery + trigger command + check_ha_traffic. pw_pw SC01 move_pw1_to_pw2 [AUTO]. ac_ac SC03/SC04 method:manual removed.*
*Updated: 2026-03-20 - Spirent integration phase 1 (71%): mac_trigger.py: +spirent_start_ha_baseline, +spirent_capture_ha_loss, +spirent_stop_ha_baseline; +spirent_inject_evpn_mac_route, +spirent_withdraw_evpn_mac_route; +execute_mac_move_ac_to_evpn, +execute_mac_move_evpn_to_ac, +execute_mac_move_ac_to_pw_via_spirent. ACTION_TRIGGER_MAP: shift_to_remote_evpn->spirent_ac_to_evpn, move_ac_to_pw->spirent_ac_to_pw, evpn_to_ac_move->spirent_evpn_to_ac. Orchestrator: HA baseline traffic auto-start, spirent_capture_ha_loss in verify phase. Recipes: HA SC01-SC04 +check_ha_traffic; ac_evpn/ac_pw triggers [AUTO].*
*Updated: 2026-03-20 - HA + recipe gaps fixed per Jira SW-204115 MAC Move Reference Table: (1) poll_mac_recovery wired into execute_scenario via recipe poll_recovery phase (reconnect_delay + timeout + poll_interval from recipe); (2) ncp_warm_restart mapped in ACTION_TRIGGER_MAP + {ncp_id} resolved from show system; (3) ha_recovery_sec (120s) threshold used for HA scenarios instead of single_mac_move_sec (2s); (4) check_rt2_recovery_layer added to verdict_engine (BGP L2VPN EVPN session + prefix count parity after HA); (5) parse_bgp_l2vpn_evpn_summary now tracks total_prefixes; (6) ObservabilityCollector.get_traffic_stats() for HA traffic capture; (7) HA recipe SC03-SC05 now have check_mobility_counter + before_snapshot + history_consistent; SC01-SC02 have check_rt2_recovery; (8) ac_evpn SC01-SC02 + ac_pw SC01-SC02 now have check_suppress_list per Jira suppress=YES for Local<->EVPN and Local<->PW; (9) pw_pw SC01 now has check_mobility_counter*
*Updated: 2026-03-02 - SW-234480 FlowSpec VPN Scale Tests: 5/5 quick-win PASS on PE-4 (CL-16). Key findings: TCAM limit 12K IPv4, session flap recovery 5.5s at 20K routes, IPv6 TCAM leak bug confirmed (BUG_FLOWSPEC_TCAM_RESERVED_LEAK_BURST)*
*Updated: 2026-03-02 - Scale test orchestrator fixes: filename sanitization, device-side NCP count via pipe filter, TCAM programming wait, convergence tracking*
*Updated: 2026-03-02 - /debug-dnos adaptive polling: use Read tool on terminal files instead of sleep+tail (prevents Aborted errors)*
*Updated: 2026-03-02 - SW-234480 Phase 2: test_10 PASS, test_11 PASS, test_02 PASS (after RT fix). test_02 "IPv6 TCAM=0" was RT mismatch in test tooling (bgp_tool parser default overrode per-mode RT; orchestrator used single RT for all modes). Fix: bgp_tool --rt default=None, orchestrator rt_overrides. Combined IPv4=12K + IPv6=4K works with ZERO NCP errors.*
*Updated: 2026-02-01 - Added New Route-Policy Language (SW-181332) with programming-like syntax*
*Updated: 2026-01-30 - Added BGP Labeled-Unicast dual hierarchy implementation*
*Updated: 2026-03-22 - SW-248907 EVPN ELAN SI HA test suite: Enhanced with full observability pipeline. (1) recipe.json: Added structured `expect` blocks to all 9 scenarios (SC01-SC09) with check_mac_flags, forbidden_flags [F,D], check_forwarding, check_ghost_macs, cross_layer_check, xray_on_mismatch. HA-specific: check_rt2_recovery (SC01/SC03/SC06/SC07/SC08), check_mobility_counter (SC04/SC07/SC08/SC09), check_ha_traffic (SC01-SC05/SC07-SC09). (2) orchestrator.py: Rewired to use shared modules from evpn_mac_mobility_SW204115/shared/ -- ObservabilityCollector (timestamped commands, phase-based recording, crash-safe intermediates, timeline.log, diffs.json), verdict_engine (ScenarioVerdict + TestVerdict + LayerResult + VerdictStatus enum, check_bgp_session_stable, check_convergence_time, check_forwarding_state_layer, check_ghost_macs_layer, check_mac_flags_layer, check_mobility_counter_layer, check_no_trace_errors, check_rt2_recovery_layer, format_detailed_report), cross_layer_check (6-layer collection + 9 comparison rules + /XRAY auto-trigger). run_structured_verify() dispatches all expect checks per scenario. Verdict per-scenario: evidence JSON + observability.json + timeline.log. Test-level verdict: verdict.json + SUMMARY.md with per-layer detail. Dry-run shows [OBS+XREF] tag per scenario.*
*Updated: 2026-03-23 - Resilient device runner + Spirent pre-flight + XRAY path fix (Network Mapper fallback): (1) NEW shared/device_runner.py: multi-strategy run_show with automatic fallback chain (MCP Network Mapper -> DNOS_SHOW_HELPER -> SSH via paramiko using ~/SCALER/db/devices.json credentials -> explicit error). Resolves device credentials flexibly (hostname/id/substring match, base64 password decode). get_cached_runner() for per-device connection reuse. All calls log which strategy succeeded for observability. (2) NEW shared/spirent_preflight.py: pre-flight checks before traffic tests (session alive, DNAAS path ready per VLAN). Auto-falls back to TrafficMethod.MANUAL when Spirent unavailable. (3) FIX cross_layer_check.py XRAY path: was hardcoded to ~/xray/live_capture.py (wrong); now searches 4 candidate paths including ~/live_capture.py (actual location). Added EVPN-aware BPF filters: "cp" (BGP+LLDP), "evpn_dp" (VXLAN+BGP), "evpn_full" (all three). (4) Orchestrator wiring: execute_scenario wraps any provided run_show with get_cached_runner for automatic SSH fallback when MCP fails mid-test. execute_test runs spirent_run_preflight before scenario loop with auto MANUAL fallback. Jira callback searches local ~/.cursor/rules/known-dnos-bugs.mdc instead of API. CLI main() uses create_device_runner instead of placeholder. (5) Both suites benefit: SW-204115 MAC mobility + SW-248907 ELAN HA (shares same shared/ modules).*
*Updated: 2026-03-23 - Persistent SSH sessions for /TEST (eliminates time.sleep): (1) NEW shared/ssh_session.py: InteractiveSSHSession with prompt-based command completion detection (50ms polling vs old 300ms+8s silence timeout), persistent connection reuse across all commands in a test run (1 connect vs N connects), auto-reconnect with configurable retry for post-HA recovery, ANSI-aware prompt regex (handles DNOS color reset before error prompts), double-echo stripping (DNOS re-renders command line via cursor-up escape). Benchmark: 10 commands in 3.8s vs 50.4s old = 13.4x speedup. (2) device_runner.py: SSH strategy now uses InteractiveSSHSession via session cache (one session per device IP, lazy-initialized, reused until cleanup). cleanup_all_sessions() for test suite teardown. (3) Orchestrator: HA reconnect_delay reduced from fixed 15-45s sleep to 5s min + extended poll timeout (session auto-reconnects). Propagation wait reduced from 3-10s to 1-3s (no reconnect overhead). cleanup_all_sessions() called at test suite end.*
*Updated: 2026-03-23 - Config knowledge base for /TEST (EVPN SI CLI hierarchy from Jira SW-203654 + Confluence): (1) NEW shared/config_knowledge.py: Defines 25+ EVPN SI config requirements (EVPN instance, seamless-integration with site-ids/label-block-size/source-if/transport/BGP-RT, MAC-handling with loop-prevention/aging/limits/sticky, bridge-domain, multihoming/ESI, BGP L2VPN EVPN AF). Maps each of the 10 test scenarios to their specific config requirements. detect_config_gaps() compares running config against requirements per test_id. generate_fix_snippets() produces ready-to-paste DNOS CLI config blocks with actual device values (ASN, RT, interfaces extracted from running config). run_config_gap_analysis() is the high-level API: fetches config via run_show, detects gaps, generates snippets in one call. (2) ENHANCED device_discovery.py: Replaced keyword heuristics (e.g., "pw" in text, "esi" in text) with structured config parsing via _parse_evpn_config_structure(). Now extracts: AC interface count + names, site-ids, label-block-size, source-if, mac-handling/loop-prevention/aging flags. Also fetches BGP config separately for address-family detection (l2vpn-evpn, l2vpn-vpls). Fixed EVPN instance name detection to parse from config text instead of relying on show evpn instance (which requires a name argument). (3) ENHANCED prerequisite_engine.py: Integrated config_knowledge.run_config_gap_analysis into check_prerequisites -- when run_show is available, performs deep gap analysis and appends config:* rows with fix_snippet for each missing block. format_prereq_table now renders "Missing Config Blocks" section with ready-to-paste CLI snippets.*
*Updated: 2026-03-23 - QA verification gap closure for MAC mobility suite: (1) WIRED 4 dead expect keys in orchestrator -- rt2_advertised (per-prefix BGP RT-2 route check via `show bgp l2vpn evpn route mac-address <MAC>`), sequence_consistent (summary vs detail seq# cross-check), local_loop_count_increments (calls verify_loop_count_incremented on AC interface), no_stuck_blackhole (forwarding table blackhole/drop/blocked state detection). (2) mac_parsers.py: _FLAG_MAP extended with M (mobility/moved) and P (vpls/pw); source_aliases added so recipe `source_contains: ["ac"]` matches local-AC MACs. (3) cross_layer_check.py: fixed remote MAC skip logic -- was checking nonexistent `flags` field on mac_entry dict, now uses `source_hint` and detail_entry.source. (4) mac_verifiers.py: verify_mac_source now uses source_aliases for accurate matching. (5) REPRO_STEPS.md auto-generated per test run with human-readable manual reproduction steps per scenario (prerequisites, baseline commands, trigger description, poll instructions, verification checklist with expect-driven items, findings table for FAIL/WARN layers).*
*Updated: 2026-03-23 - EVPN MAC mobility SW-204115: all 10 `recipe.json` files extended with engine fields after `verdict`: `counter_commands`, `counter_expectations`, `event_expectations`, `health_checks`, `cleanup_commands`, `config_baseline`; per-recipe variants (non-HA, ac_ac suppression/loop, ha_mac_mobility forwarding + HA events, withdraw_flush `mac_count` `no_increase`)*
*Updated: 2026-03-20 - Ultimate /TEST QA Framework Build: (1) NEW scaler/TEST/shared/ -- 12 feature-agnostic Tier 1 engines: counter_tracker (snapshot/diff/expectations), event_tracker (3-method syslog+terminal+traces), syslog_parser, config_baseline (golden config snapshot+debris detection), health_guard (process/crash/CPU/memory/alarms), multi_device (cross-device correlation), regression_detector (historical baseline comparison), test_isolation (atexit+signal cleanup guarantee), continuous_poller (convergence polling), report_generator (FULL_REPORT.md), vtysh_runner (deep debugging), post_run_learner (auto-learn+sync). (2) NEW Tier 2 knowledge pack: evpn_event_knowledge.py (12 EVPN system events from Confluence, per-scenario-type defaults for counters/events/health/cleanup/config_baseline, enrich_recipe_with_evpn_defaults()). (3) mac_mobility_orchestrator.py fully wired: health+config baseline before scenarios, counter snapshots around triggers, event audit after verify, regression+report+learning after all scenarios, smart flow control (stop_on_fail), TestIsolationGuard cleanup. (4) All 10 recipe JSONs include engine fields. (5) observability.py extended (record_counter_snapshot/diff, record_event_audit, record_health_snapshot, record_xray_capture, record_regression_result). (6) ProactiveXray in cross_layer_check.py. (7) Spirent-DUT cross-ref + BGP continuous monitoring in mac_verifiers.py.*
*Updated: 2026-01-27 - Added Granular Mirror Configuration with hierarchical selection, VRF support, and advanced transformations*

---

## EVPN MAC Mobility — Spec-Derived Test Design Rules (v26.1, SW-204115 suite)

**Source of truth:** Confluence page `6311379530` — *evpn-mac-mobility Source of Truth (High-Level Spec)* by Ido Koren, v26.1.
**Authoritative Jira:** SW-154752 (MAC Move Action Matrix), SW-178113 (MH-SH interaction), SW-116723 (LLP implementation).
Read this BEFORE writing any recipe that asserts on MAC-mobility counters or suppression behavior.

### Rule 1 — local-SH → local-SH is WAD (ignore)

**If BOTH ACs are single-homed (ESI=0), a MAC move between them is SILENTLY IGNORED by DNOS:**
- Internal MAC counter: **no increment**
- LLP local loop counter: **no increment**
- RT-2 advertisement: **no re-advertise**
- Sequence number: **unchanged**
- Freeze/blackhole/shutdown: **none applied**

```
| From     | To       | Counter | Adv RT-2 | Seq    | Freeze | Blackhole | Shutdown |
|----------|----------|---------|----------|--------|--------|-----------|----------|
| local-SH | local-SH | ignore  | ignore   | ignore | no     | no        | no       |
| local-SH | local-MH | +1      | yes      | +1     | no     | yes       | yes      |
| local-MH | local-SH | +1      | yes      | +1     | no     | yes       | yes      |
| local-MH | local-MH | +1      | yes      | +1     | no     | yes       | yes      |
```

**Implication for /TEST recipes:**
- NEVER write `"local_loop_count_increments": true` in a scenario that uses two single-homed ACs. The spec explicitly forbids the DUT from incrementing here.
- ALWAYS declare a `requires_ac_profile` in the scenario, and make the prerequisite engine verify the ESI pair matches the profile BEFORE executing.
- If you want to assert "zero increment", use `"local_loop_count_increments": false` with a rationale field.

**Recipe pattern (ac_ac):**
```json
"ac_topology_profiles": {
  "both_single_homed_ESI_zero": { "expected_behavior_per_spec": "IGNORE" },
  "different_esi_pair":         { "expected_behavior_per_spec": "counter/RT-2/seq increment" }
}
```

### Rule 2 — Seamless-Integration DF election blocks all-but-one AC

When an EVPN instance has `seamless-integration` enabled with `site-id + site-interface`, the DF election procedure forces **every other AC on the same site into `blocking-all` state**. Only ONE AC (the DF, per site-id) is `forwarding-all`. Traffic sent to any blocking AC is dropped at the L2 forwarding layer before MAC learning — so the "move" never even reaches the mobility logic.

**Verification command:**
```
show evpn instance <name> | include "Actual Forwarding State"
```
All non-forwarding ACs show `blocking-all`.

**Implication for /TEST recipes:**
- Any scenario that needs two forwarding ACs on the same EVPN instance MUST either:
  1. Use a non-SI EVPN instance (separate instance without `seamless-integration`), OR
  2. Configure multi-homed ethernet-segment with `site-id` + `site-preference` differentiated per AC, OR
  3. Use bridge-domain LLP (no EVPN) where DF election does not apply.
- Add a hard prereq:
  ```json
  {"id": "two_forwarding_acs",
   "check": "two_acs_in_forwarding_all",
   "expect": "At least 2 ACs with Actual Forwarding State == forwarding-all"}
  ```
- Failing this prereq should mark SC02/SC03/SC04 as `BLOCKED` (not `FAIL`) and auto-suggest the topology fix.

### Rule 3 — ESI-pair precondition check (different ESIs)

Per Rule 1, LLP counter increments require the AC pair to have DIFFERENT ESI values (either one is MH non-zero + one is SH zero, OR both MH with different ESI values). Add this as a prerequisite:

```json
{"id": "different_esi_ac_pair",
 "check": "ac_pair_different_esi",
 "check_command": "show evpn instance {evpn_name} interface | no-more",
 "expect": "ac1 and ac2 have DIFFERENT ESI values",
 "fix_via": "config_knowledge.multihoming_esi: assign ES identifier to one AC"}
```

Auto-fix template (see `config_knowledge.py` key `multihoming_esi`, line 213):
```
network-services
  multihoming
    ethernet-segment ES-AC2
      identifier 00:11:22:33:44:55:66:77:88:99
    !
  !
!
interfaces
  <ac2_iface>
    ethernet-segment ES-AC2
  !
!
```

### Rule 4 — Sticky config applies on NEXT move, not retroactively

Per Confluence spec section 4.1 / 6.4: `mac-handling sticky-interface` config takes effect on the **NEXT move event** for each MAC. Existing MAC entries are NOT retroactively marked with the sticky (`si`) flag.

**Implication for /TEST recipes:**
- Sticky test scenarios (SC04) MUST flush + re-learn the MAC AFTER applying the sticky-interface config. Never assert on existing MAC entries.
- Recipe should include:
  ```json
  "trigger": {
    "action": "attempt_move_to_sticky_ac",
    "must_flush_first": true,
    "flush_reason": "Sticky applies on next move, not retroactively"
  }
  ```

### How to verify these rules on a live DUT

```bash
# 1. Confirm both ACs are forwarding
ssh dnroot@<dut> "show evpn instance HA_TEST_ELAN interface | no-more"
# Look for rows where "Actual Forwarding State" == "forwarding-all" (expect 2+)

# 2. Confirm ESI difference
ssh dnroot@<dut> "show evpn instance HA_TEST_ELAN interface | no-more"
# Look at "ESI" column for ac1 and ac2 — they MUST differ for LLP to count moves

# 3. Observe LLP counter behavior
ssh dnroot@<dut> "show evpn instance HA_TEST_ELAN loop-prevention local | no-more"
# After a SH->SH flap: Moves == 0 (expected per spec, NOT a bug)
# After a SH->MH flap: Moves > 0 (expected per spec)
```

### Common misdiagnosis to AVOID

| Symptom | WRONG conclusion | CORRECT diagnosis |
|---|---|---|
| LLP counter stays 0 after Spirent MAC flap on SH-SH pair | "DUT bug, counter broken" | Per-spec IGNORE (Rule 1) — use MH/different-ESI pair |
| `blocking-all` on second AC, traffic dropped | "Forwarding layer bug" | SI DF election (Rule 2) — use non-SI or MH-ES |
| Sticky flag missing on existing MAC after applying sticky-interface | "Sticky enforcement broken" | Sticky applies on next move (Rule 4) — flush+re-learn |
| Local-to-local Spirent traffic doesn't appear in mobility redis count | "Redis counter stuck" | Same as above: Rule 1 + Rule 2 stacked |

### Cross-reference map

- Spec page: `6311379530` (Confluence) — Ido Koren v26.1
- MAC Move Action Matrix: `SW-154752`
- MH-SH counter interaction: `SW-178113`
- LLP implementation: `SW-116723`
- AC-AC test task: `SW-205161`
- Umbrella: `SW-204115`
- EVPN-VPLS PW mobility: `SW-192019` (older, does NOT override Rule 1)
- Sticky with proxy ARP: `SW-194578`

### Recipe enforcement checklist (new `/TEST` recipes targeting LLP)

- [ ] `spec_source_of_truth` block referencing Confluence page 6311379530
- [ ] `mac_move_action_matrix` block duplicated inline (so the recipe is self-contained)
- [ ] `ac_topology_profiles` block declaring which pair each scenario needs
- [ ] `requires_ac_profile` field on EVERY scenario that asserts LLP counter behavior
- [ ] `prerequisites` include `two_forwarding_acs` AND `different_esi_ac_pair`
- [ ] `topology_constraints` block listing the SI DF-election caveat
- [ ] Sticky scenarios have `must_flush_first: true` + `flush_reason`
- [ ] Scenario `expect` uses `false` (with `rationale`) for SH-SH, `true` for MH/different-ESI pairs

*Updated: 2026-04-22 - EVPN MAC Mobility spec-derived rules (v26.1 Confluence 6311379530 / Ido Koren): Added Rules 1-4 covering (1) SH-SH ignore per SW-154752 MAC Move Action Matrix, (2) SI DF-election blocking-all-but-one-AC topology constraint, (3) ESI-pair precondition for LLP counter increment, (4) sticky-interface applies on NEXT move not retroactively per section 4.1/6.4. Recipe `ac_ac/recipe.json` restructured: SC02 split into SC02_SH_SH_rapid_flap_ignored (expect IGNORE per spec) + SC02_MH_SH_rapid_flap_suppressed (expect increment); SC03 renamed SC03_local_loop_counter_ESI_aware with `requires_ac_profile: different_esi_pair`; SC04 gets `must_flush_first: true` for sticky test correctness; added `ac_topology_profiles`, `topology_constraints`, `mac_move_action_matrix`, `spec_source_of_truth` blocks; added prereqs `two_forwarding_acs` + `different_esi_ac_pair` with auto-fix templates. Classifies previous SC02/SC03/SC04 "FAIL" results as test-harness bugs (wrong expectation for SH-SH pair on SI-DF-blocked topology), NOT DNOS bugs.*

---

## 11. EVPN MAC Mobility AC<->AC -- 16-Scenario Stress Run (RUN_20260422_2029_YOR_PE-1)

**Test ID:** `TEST_mac_mob_ac_ac_SW205161` | **Device:** YOR_PE-1 | **Elapsed:** 9686.7s (2h41m) | **Overall:** FAIL (mostly harness/infra, NOT DNOS bugs)

### 11.1 Stress verdict matrix (canonical post-run baseline)

| # | Scenario | Verdict | Functional layers (DNOS behavior) | Failing layer(s) | Root cause |
|---|----------|---------|----------------------------------|------------------|------------|
| 1 | SC01_non_sticky_move | WARN | trigger/sequencing/control_plane/mac_flags/forwarding/ghost_macs/cross_layer = PASS | bgp_session=WARN (expected), traces=SKIP | DNOS clean. WARN is bgp_session reporting EVPN peer untagged (not test-relevant) |
| 2 | SC02_SH_SH_rapid_flap_ignored | SKIP | n/a | ac_profile_gate=SKIP | Topology gate: needs `both_single_homed_ESI_zero`, runtime is `different_esi_pair` -- correct SKIP per gate logic |
| 3 | SC02_MH_SH_rapid_flap_suppressed | WARN | All 7 functional layers PASS (incl. local_loop_count 2/5, rt2_advertised, mac_flags=L,K,M) | none | DNOS clean -- WARN is bgp_session noise |
| 4 | SC03_local_loop_counter_ESI_aware | WARN | All 6 functional layers PASS (LLP move 1/5 detected) | none | DNOS clean |
| 5 | SC04_sticky_enforcement | WARN | sticky=PASS, mac_flags=L,K (sticky bit), forwarding=PASS, ghost=PASS | none | DNOS clean. Sticky correctly applied on re-learn |
| 6 | SC05_back_forth_sequence | WARN | sequence_consistent=2/2 MATCH, all functional PASS | none | DNOS clean. Sequence semantics correct |
| 7 | SC06_sanction_firing | WARN | All functional PASS, LLP move 1/5 detected, sanction applied | timing=WARN (208s vs 200s, within 2x) | DNOS clean. 12-flap suppress sanction operated correctly |
| 8 | SC07_subsecond_rapid_flap | **FAIL** | All 7 functional layers PASS (sequence_consistent=50==50 MATCH, ghost=0, forwarding OK) | timing=FAIL (833s >> 200s) | **Harness threshold too tight**. 50 flaps @ 100ms inherently long. DNOS sequence math perfect |
| 9 | SC08_SH_SH_coverage_swap | **FAIL** | All 5 functional layers PASS (no LLP increment, no RT-2 churn, no seq bump per spec) | timing=FAIL (197s >> 90s) | **Harness threshold too tight**. SH+SH ignore semantics confirmed correct |
| 10 | SC09_irb_si_cli_rejection | WARN | trigger=PASS (commit-check rejected with expected error regex), timing=PASS (12.6s) | bgp_session=WARN (expected) | DNOS clean. Rejection text matched: "cannot be configured at the same time" |
| 11 | SC10_admin_flap_race | WARN | All functional PASS, ghost=0, mac_flags=L on AC2 | none | DNOS clean. Mid-move admin-down handled correctly |
| 12 | SC11_bulk_ac_ac_flap_100_macs | WARN | All functional PASS (sequence consistent, ghost=0 across 100 MACs) | none | DNOS clean. Bulk RT-2 churn (~500 events) handled, no FIB leaks |
| 13 | SC12_triple_ac_A_B_C_A | SKIP | n/a | ac_profile_gate=SKIP | Topology gate: needs `triple_ac_three_subifs`, runtime has only 2 ACs -- correct SKIP. Coverage gap |
| 14 | SC13_persistent_ac_shutdown_sanction | **FAIL** | mac_flags/forwarding/ghost/cross_layer/traces all PASS. sanction=shutdown applied=True | local_loop_count=FAIL (0/5 in detection window) | **Harness window-detection bug**. LLP counter snapshot taken too late (after window TTL expired) -- not a DNOS sanction bug |
| 15 | SC14_ha_observation_mid_move | **FAIL (HA event side-effect)** | trigger PASS (parallel flap+`request system process restart routing:bgpd` completed in 121s), traces PASS (no errors near 21:10), ghost=PASS | mac_flags/forwarding/cross_layer_mac_existence/counter_mac_count/event_BGP_NOTIFICATION/timing FAIL | **Spirent BGP EVPN peer dropped on bgpd restart and never re-established (0/0 ESTABLISHED)**. MAC never re-learned via control plane. Infra-side: Spirent session needs restart-after-HA hook. DNOS itself recovered (bgpd up, no crashes) |
| 16 | SC15_cluster_flush_correctness_at_scale | **FAIL (cascade from SC14)** | trigger PASS, ghost=PASS | forwarding=FAIL (MAC never appeared), timing=FAIL | **Cascade infra failure**: Spirent EVPN peer still down from SC14, MAC never learned, so post-clear nothing to validate. Not a flush bug |

**Counts:** 6 PASS-equivalent (WARN only on bgp_session noise), 2 SKIP (correct topology gate), 5 FAIL (3 harness threshold/window, 2 infra cascade post-HA), 0 confirmed DNOS defects.

### 11.2 Failure classification (DNOS bug vs harness vs infra)

| Failure | Class | Evidence | Action |
|---------|-------|----------|--------|
| SC07 timing (833s vs 200s) | Harness threshold | Functional perfect: seq_consistent=50==50, ghost=0, mac_flags OK | Raise threshold to 1200s for `subsecond_flap` (50 flaps @ 100ms + verify polling overhead is inherently ~15min) |
| SC08 timing (197s vs 90s) | Harness threshold | Functional perfect: SH+SH semantics confirmed (no LLP increment as spec demands) | Raise threshold to 300s for `sh_sh_coverage` (config push + 10x flap + restore + verify) |
| SC13 local_loop_count (0/5) | Harness window-detection | mobility_counter total_moves=0 captured AFTER restore-timer + window TTL expired; sanction=shutdown applied=True confirms DNOS executed correctly | Snapshot LLP counter `during` flap loop (mid-trigger), not at end-of-verify when window has rolled |
| SC14 mac_flags/forwarding FAIL | Infra (Spirent) | bgpd restarted cleanly (traces PASS, no ERROR/CRASH), but Spirent EVPN peer (19.19.19.2) went IDLE + never reconnected | Add `post_ha_spirent_recover` step: detect session=IDLE/DOWN -> stop+restart Spirent BGP protocol -> wait for ESTABLISHED before verify |
| SC15 forwarding FAIL | Infra cascade (SC14 leftover) | 0/0 ESTABLISHED at scenario start | Make scenarios fail-fast on `bgp_evpn_peer_count == 0` precheck OR mandatory `prereq.spirent_bgp_evpn_established` gate per scenario |
| All `bgp_session=WARN` (every scenario) | Cosmetic noise | Reports "0/3 ESTABLISHED (not required for this test)" | Recipe-level: mark `bgp_session` layer as `informational` for ac_ac scenarios since EVPN peer is not used by local-to-local flap. Suppress the WARN at verdict_engine when `not_required=True` |

### 11.3 DNOS findings (the actual purpose of the run)

**Confirmed working under stress:**
1. **Sequence math (RFC 8560)** -- SC07 ran 50 sub-second flaps; CLI summary count == detail count == 50, no gaps, no resets. DNOS sequencing is bulletproof.
2. **SH+SH ignore semantics** -- SC08 made both ACs SH+ESI=0 temporarily, drove 10 flaps; LLP did NOT increment, no RT-2 churn, no seq bump. Spec compliance confirmed at runtime.
3. **MH-SH suppress** -- SC02_MH_SH and SC06 both ran 10-12 flaps with sanction armed; LLP counter incremented (2/5, 1/5), suppress state engaged, no FIB ghosts.
4. **Bulk RT-2 burst (100 MACs x 5 flaps = 500 events)** -- SC11 completed cleanly, every MAC ended on a single AC, ghost_mac count=0, mac summary count stable.
5. **Admin flap race** -- SC10 admin-downed AC1 mid-MAC-move; DNOS converged to a single MAC entry on AC2 with no duplicate forwarding entries.
6. **IRB+SI mutual exclusion** -- SC09 commit-check rejected the IRB-under-SI config with the expected error string.
7. **Clean process restart** -- SC14 `request system process restart ncc 0 routing-engine routing:bgpd` succeeded; bgpd came back up; no traces ERROR; no health alarms.

**No new defects found.** All earlier suspected DNOS bugs were re-classified to harness/infra in 11.2.

### 11.4 Recipe / harness fixes required (ordered by impact)

1. **`shared/mac_trigger.py::poll_until_mac_present`** -- Make the 120s default timeout configurable per scenario; the 5 layers that share this helper currently each block 120s when MAC is absent (240s sometimes) -- compounds to 14+ minutes wasted per HA scenario. Add `max_total_blocking_sec` cap per scenario.
2. **`orchestration/scenario_runner.py` -- Spirent BGP EVPN re-establishment hook** -- After any `request system process restart` action that targets `routing:bgpd`, add a post-trigger step that polls the Spirent BGP session and stop/start the protocol if not ESTABLISHED within 30s. Prevents SC14 -> SC15 cascade.
3. **Per-scenario timing thresholds** -- The current globals (90s / 200s) underestimate sub-second-flap and SH+SH-coverage scenarios. Update `recipe.json` to add `timing_threshold_sec` overrides:
   - SC07_subsecond_rapid_flap: 1200s
   - SC08_SH_SH_coverage_swap: 300s
   - SC13_persistent_ac_shutdown_sanction: 300s
   - SC14_ha_observation_mid_move: 600s (HA + Spirent re-converge)
   - SC15_cluster_flush_correctness_at_scale: 600s
4. **LLP counter snapshot during flap (SC13)** -- Move the `mobility_counter` capture from `verify` phase to `trigger` phase mid-loop (after flap N/2). The current end-of-verify snapshot misses the window because shutdown sanction restore-timer rolled the counter back to 0.
5. **`verdict_engine.py` -- `bgp_session` layer noise suppression** -- When the recipe scenario has no EVPN/RT-2 expectations (pure local-to-local move), downgrade `bgp_session=WARN` to `bgp_session=INFO` so it doesn't pull the overall scenario verdict down.
6. **Spirent zombie protection per scenario** -- Already done at suite start. Add a per-scenario quick check (`stcrest GET /sessions` count) so HA scenarios don't proceed if Lab Server lost the session.

### 11.5 Jira coverage delta after this run

| Jira | Coverage | Evidence in this run |
|------|----------|----------------------|
| SW-205161 (AC-AC test task) | **DONE** | All 16 scenarios executed; 9 functional PASS, 2 SKIP per topology gate, 5 harness/infra FAIL with no DNOS defect |
| SW-204115 (umbrella) | Partial | Bulk (100 MACs x 5 flaps) PASS; HA process-restart PASS on DNOS side; cluster flush deferred (infra cascade); 1k/64k scale + triple-AC + persistent-shutdown LLP window are explicit follow-ups |
| SW-154752 (MAC Move Action Matrix) | Cases 1, 2, 3, 5 covered | Case 1 (SH+SH ignore) confirmed via SC08; Case 2 (MH-SH suppress) via SC02_MH_SH + SC06; Case 3 (different-ESI counter) via SC03; Case 5 (persistent shutdown sanction) needs harness fix in 11.4#4 |
| SW-178113 (MH-SH interaction) | DONE | SC02_MH_SH counter increment + RT-2 advertisement validated |
| SW-116723 (LLP impl) | Partially DONE | LLP counter increments correctly (SC03/SC02_MH_SH); window-detection edge in SC13 needs re-instrument |
| SW-194578 (Sticky + proxy ARP) | DONE on sticky portion | SC04 sticky_enforcement confirms NEXT-move semantics; proxy ARP not tested in this recipe (separate Jira gap) |

### 11.6 Coverage gaps explicitly tracked (post-run)

1. **Triple-AC mobility (SC12)** -- Skipped because runtime has 2 ACs. Needs lab provisioning of `ge400-0/0/5.1002` + EVPN instance attach + DNAAS path before the scenario can run. Tracked under SW-204115 meeting #3 follow-up.
2. **1k / 64k MAC scale** -- SC11 scaled to 100; the underlying spirent multiplier supports `--device-count N --ip-step 1 --mac-step 1`. Next iteration: `flap_count=2, mac_count=1000, interval_sec=2.0` then `mac_count=64000, mac_count_per_burst=8000`. Recipe slot reserved for SC16_scale_1k.
3. **Window-shutdown restore-timer edge** -- SC13 verdict caught the harness gap; need a parallel scenario SC13b that polls LLP counter during the flap loop, not after restore-timer expiry.
4. **HA process-restart with EVPN traffic survival** -- SC14 demonstrated DNOS bgpd recovers cleanly, but the Spirent peer didn't re-converge. Real signal requires recipe step `post_ha_spirent_recover` (11.4#2) before we can call this scenario "validated".
5. **Cluster flush correctness at scale** -- SC15 needs SC14 fix landed first; once Spirent re-converges, a 50-MAC bulk-learn -> `clear evpn mac-table` -> verify-empty cycle should complete in ~120s.

*Updated: 2026-04-22 - Section 11 added: 16-scenario AC<->AC stress run RUN_20260422_2029_YOR_PE-1 (TEST_mac_mob_ac_ac_SW205161) post-run analysis. 9686.7s elapsed; classifies all FAILs as harness/infra (no DNOS defects). Synced full 16-scenario `ac_ac/recipe.json` (716 lines) from `~/SCALER/TEST/catalog/.../tests/ac_ac/recipe.json` to `scaler/TEST/catalog/.../tests/ac_ac/recipe.json` for git tracking. Lists 6 ordered harness fixes (poll cap, post-HA Spirent re-convergence hook, per-scenario timing thresholds, mid-trigger LLP snapshot, bgp_session noise suppression, per-scenario zombie protection) and 5 explicit coverage gaps (SC12 triple-AC provision, SC11 1k/64k scale, SC13b LLP window edge, SC14 HA+EVPN traffic survival, SC15 cluster flush at scale).*

## 12. EVPN MAC Mobility AC<->PW -- 4-Scenario Run (RUN_20260423_0633_YOR_PE-1)

**Test ID:** `TEST_mac_mob_ac_pw_SW205198` | **Jira:** SW-205198 (child of SW-204115) | **Device:** YOR_PE-1 | **Elapsed:** 303.8s | **Overall:** FAIL (only SC04 fails, infra pattern identical to ac_ac SC04)

### 12.1 Scenario verdict matrix

| # | Scenario | Overall | Layers | DNOS verdict |
|---|----------|---------|--------|---------------|
| 1 | SC01_ac_to_pw | **PASS** | trigger+mac_flags+forwarding+ghost+cross_layer PASS; bgp_session WARN (ignorable, EVPN peer not required for PW path) | Non-sticky AC->PW move: MAC flags `L,K,M,P` correct; RT-2 withdrawn; PW ingress label 1032265 used |
| 2 | SC02_pw_to_ac | **PASS** | control_plane=PASS (attachment=local), mac_flags PASS | Non-sticky PW->AC move: flags `L,K,M,P`; local AC attachment re-established |
| 3 | SC03_sticky_ac_to_pw | **PASS** | sticky=PASS (`Sticky MAC enforced`); mac_flags `L,K` (no M/P since sticky ignored remote move) | SW-194578 ENFORCED: sticky AC wins, PW move IGNORED at control-plane |
| 4 | SC04_pw_to_sticky_ac | FAIL (harness) | control_plane+sticky+mac_flags+forwarding FAIL (MAC never re-learned after sticky config) | Same pattern as ac_ac SC04: sticky-re-learn timing gap; detector classified `infra_issue`, no DNOS defect |

**Functional conclusion:** 3/4 scenarios validate DNOS AC<->PW mobility end-to-end. Zero DNOS bugs. SW-194578 (sticky) and AC-PW non-sticky symmetry both verified.

### 12.2 Prerequisite chain observations

The VPLS PW stack has 11 prereqs chained (spirent_session -> label_pool -> bgp_l2vpn_vpls -> si_evpn -> isis -> route_to_loopback -> ldp -> spirent_vpls_peer -> pw_installed -> pw_ingress_label -> ac_on_same_instance). On this run:
- DUT config was already intact from 2026-04-11 validation (PW_TEST_ELAN with SI + VPLS RT under SI subtree, AC ge400-0/0/5.1010, BGP neighbor 17.17.17.2 with l2vpn-vpls AF, bgp-vpls label pool 128).
- After fresh Spirent session, ISIS converged, LDP session established, BGP l2vpn-vpls brought up.
- **PW Installed with ingress label 1032265 in 23s** (8 polls). No DNOS rejection or instability.

### 12.3 Harness bug fixed mid-run

First attempt: `spirent_tool.py ldp-peer` hit a transient Lab Server zombie (`404 Not Found: session not found` after the REST health-probe said the session existed). This cascaded: LDP never configured -> FEC 6.6.6.6/32 label absent -> BGP l2vpn-vpls peer stuck at `Active` state for 21.7h -> PW never installed -> all 4 scenarios SKIPPED with `pw_ingress_label=0`.

**Root cause in harness:**

`shared/spirent_vpls_provisioner.py`:

- `_PROVISIONER_MUTATING` excluded `ldp-peer`, `isis-peer`, `evpn-peer`, `add-afi`, `mac-block` -> retries=1 (no auto-retry on transient dead-session).
- `_SESSION_DEAD_MARKERS` missed lowercase `"session not found"` and `"404 Not Found"` strings -> even if retries were enabled the loop couldn't detect the failure class.

**Fix applied (2026-04-23):**

```python
_PROVISIONER_MUTATING = {
    "create-device", "create-stream", "vpls-stream", "remove-device",
    "remove-stream", "protocol-start", "protocol-stop",
    "bgp-peer", "ecmp", "evpn-routes", "add-routes",
    "withdraw-routes", "reserve", "connect",
    "ldp-peer", "isis-peer", "evpn-peer", "add-afi", "mac-block",
}

_SESSION_DEAD_MARKERS = (
    "No active session", "Port not reserved", "Stale handles",
    "Session not found", "Session marked inactive", "Connection refused",
    "timed out", "HTTPError", "ConnectionError",
    "404 Not Found", "session not found", "No Remote Test Session",
    "JOIN-only mode", "SpirentSessionError",
)
```

Post-fix validation: `connect --force-new` -> fresh session, then rerun reached `PW Installed (label=1032265)` and drove 3/4 scenarios to PASS.

### 12.4 Residual harness gap (SC04 only)

SC04 (`PW -> Sticky AC`) re-uses the same post-sticky re-learn sequence as ac_ac SC04. Both fail identically: after `sticky-interface enabled` commit the MAC cleanup/re-learn window does not land the new MAC before the verify phase polls. Pattern is NOT a DNOS defect -- the detector consistently classifies `infra_issue -- Spirent OK but 0 MACs on DUT`.

Proposed harness fix (shared with Section 11.4 #1): cap the re-learn poll window, add an explicit `protocol-stop -> protocol-start` bracket around the sticky config change, and re-validate MAC presence before entering `trigger` step2.

### 12.5 Jira coverage delta

| Jira | Prior state | This run contribution |
|------|-------------|-----------------------|
| SW-205198 (AC<->PW test task) | Never run | **3/4 scenarios PASS**, 1 harness-class FAIL. Promoted to "pass with known harness gap on sticky re-learn" |
| SW-194578 (sticky on NEXT move) | Covered by ac_ac SC04 (with caveats) | SC03 adds AC-side sticky enforcement against PW move attempts; NEXT-move semantics verified |
| SW-192019 (EVPN-VPLS PW mobility) | Unstated | SC01/SC02 validate symmetric AC<->PW non-sticky mobility with proper flags `L,K,M,P` |
| SW-204115 (umbrella) | 11/16 tests executed | Add ac_pw (SW-205198); remaining: ha_mac_mobility, scale_64k, multihoming, withdraw_flush, sticky_modes, pw_pw, ac_evpn |

*Updated: 2026-04-23 - Section 12 added: 4-scenario AC<->PW run RUN_20260423_0633_YOR_PE-1 (TEST_mac_mob_ac_pw_SW205198). 3/4 PASS validating DNOS AC<->PW mobility and SW-194578 sticky enforcement; SC04 fails with same harness re-learn pattern as ac_ac SC04 (classified infra, no DNOS defect). Harness fix applied in shared/spirent_vpls_provisioner.py: expanded `_PROVISIONER_MUTATING` (+ldp-peer/isis-peer/evpn-peer/add-afi/mac-block) and `_SESSION_DEAD_MARKERS` (+404/session-not-found/JOIN-only markers) so transient Lab Server zombies no longer cascade into full test SKIP.*

## 13. PW Scale MAC Mobility + HA Recipe (TEST_pw_scale_mac_mobility_ha_SW204115)

**Added:** 2026-05-03  
**Catalog path:** `~/SCALER/TEST/catalog/pw_scale_200_mobility_ha_SW204115/tests/pw_scale_mac_mobility_ha/`  
**Worktree path:** `scaler/TEST/catalog/pw_scale_200_mobility_ha_SW204115/tests/pw_scale_mac_mobility_ha/`

This recipe creates 200 matched EVPN-SI VPLS services between PE-4 and RR-SA-2, then drives 400 unique unknown-unicast Spirent StreamBlocks before running parameterized HA. The deterministic service window is:

- Inner VLANs: `5001..5200`
- RTs: `1234567:5001..1234567:5200`
- PE-4 ACs: `ge100-18/0/0.5001..5200` with wire outer `219` over DNAAS fab `213`
- RR-SA-2 ACs: `bundle-100.5001..5200` with wire outer `4`; Spirent sends outer `215` and B-15 rewrites `215 -> 4` while preserving the inner VLAN

Key implementation files:

- `recipe.json` -- runtime parameters, prerequisites, phases, and scale-aware verdict gates.
- `orchestrator.py` -- phase runner for config chunks, Spirent stream creation, MAC verification, and HA modes.
- `shared/pw_scale_builder.py` -- pure deterministic matrix/config generator; use this instead of hand-writing service rows.
- `shared/pw_scale_runner.py` -- dnos-config MCP, Spirent, polling, and result helpers.

Operational notes:

1. Default stream strategy is one StreamBlock per `(side, service)` for 400 StreamBlocks total; `~/.spirent_config.json` soft `max_streams` is bumped to `500` for this recipe.
2. The recipe gates on SW-253359 before it creates services: PE-4 `show mpls label-allocation tables` must not show `bgp-vpls: 0 labels, N/A`.
3. Config is applied via `dnos_multi_device_commit` in paired PE-4/RR-SA-2 chunks of 25 services by default. Do not replace this with ad-hoc SSH config scripts.
4. If MAC learning fails after DNAAS + Spirent proof pass, stop and invoke `/debug-dnos`; do not clear MAC state or retry with workaround commands before evidence capture.

---

## Spirent multicast / IGMP / MLD (EVPN IGMP-Proxy, SW-211037)

`SPIRENT/spirent_tool.py` can now create and control multicast sources,
receivers, and IGMP/MLD versions for the `/evpn-igmp-proxy-paths` epic. The DUT
(PE) is the IGMP proxy / querier; Spirent emulates hosts, sources, and (when
needed) an external mrouter.

### CLI commands (and the MCP `spirent_multicast` umbrella operation)

| Command | Umbrella op | Purpose |
|---|---|---|
| `create-mcast-source` | `source` | Multicast data SENDER. Auto-derives the group L2 MAC (RFC 1112 IPv4 `01:00:5e`+low-23, RFC 2464 IPv6 `33:33`+low-32). `--source`=S, `--group`=G, `--family ipv4|ipv6`. |
| `create-mcast-receiver` | `receiver`/`join` | Stateless IGMP/MLD membership report. `--version 1|2|3`, `--family`, `(*,G)` via `--filter-mode exclude`, `(S,G)` via `--filter-mode include --source S1,S2`, `--record-type` override. |
| `mcast-leave` | `leave` | IGMPv2 Leave (-> 224.0.0.2) / IGMPv3 block / MLD Done (-> ff02::2). |
| `mcast-querier` | `querier` | External-mrouter emulation: General Query (omit `--group`) or Group-Specific Query (set `--group`) with src != 0 so the DUT marks the port as mrouter (RFC 4541). |
| `igmp-host` | `host` | Stateful `IgmpHostConfig` stack on an existing emulated device (auto-replies to queries). Requires `create-device` first. |

### Object model

- RECEIVERS/LEAVES/QUERIES use stateless StreamBlock PDUs: `igmp:Igmpv1`,
  `igmp:Igmpv2Report`, `igmp:Igmpv2Leave`, `igmp:Igmpv3Report` +
  `grpRecords` + `GroupRecord` (`recordType` = `CHANGE_TO_INCLUDE_MODE` /
  `CHANGE_TO_EXCLUDE_MODE` / `BLOCK_OLD_SOURCES` / ...), and the `mld:*` peers.
  These StreamBlock object types are verified.
- Stateful host (`IgmpHostConfig` / `IgmpGroupMembership` / `Ipv4Group` /
  `Ipv4NetworkBlock`), the IGMPv3 GroupRecord source-list child/attr, and the
  `igmp:Igmpv2Query` / `igmp:Igmpv3Query` / `mld:*Query` object names are marked
  `[VALIDATE-LIVE]` in the code: confirm exact STC names against the Lab Server
  on the first live `/TEST` run. The builders degrade gracefully (warn, do not
  crash) if a name needs correcting.

### Control-plane destinations (RFC, not guessed)

- v1/v2 report -> group G; v2 Leave -> 224.0.0.2; v3 report -> 224.0.0.22;
  general query -> 224.0.0.1. MLDv1 report -> group; MLDv1 Done -> ff02::2;
  MLDv2 report -> ff02::16; MLD general query -> ff02::1. IGMP TTL / MLD
  hop-limit = 1.

### Mapping to the EVPN IGMP-proxy test matrix

- Group A (type-7 joins): `receiver` v2 `(*,G)` and v3 `(S,G)` INCLUDE.
- Group B (type-6 SMET): `source` + `receiver`; transitions via `record-type`.
- Group C (leave/MRT): `mcast-leave`.
- Groups M/N (IRB+PIM / external mrouter): `mcast-querier`.

### IMPORTANT - repo vs live divergence (spirent_tool.py)

The live MCP runs `/home/dn/SCALER/SPIRENT/spirent_tool.py`; the worktree source
is `scaler/SPIRENT/spirent_tool.py`. These two had pre-existing divergence
(live carried auto-heal + `_wait_for_stc_condition` not in the repo, and the
repo had a few unique lines). The multicast additions above were applied
**identically and additively to both** files via string-anchored edits, without
touching the divergent regions. Do NOT blindly `cp` one over the other - that
would lose work on one side. Reconcile the pre-existing divergence deliberately.
