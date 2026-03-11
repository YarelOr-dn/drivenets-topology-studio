# Topology Creator - Development Guidelines
# ==========================================
# These guidelines document the codebase patterns and rules for development.
# Agents MUST read this file before making changes and UPDATE it after fixes.

## 📁 Key File Locations

| Purpose | Location |
|---------|----------|
| Main topology logic | `topology.js` |
| Styles | `styles.css` |
| HTML entry point | `index.html` |
| Debugger panel | `debugger.js` |
| DNAAS discovery | `dnaas_path_discovery.py` |
| Scaler bridge API | `scaler_bridge.py` (port 8766) |
| Momentum physics | `topology-momentum.js` |
| History/undo | `topology-history.js` |

### Scaler Bridge API (scaler_bridge.py, port 8766)

The bridge wraps scaler-wizard modules for the topology app. serve.py proxies `/api/config/*`, `/api/operations/*`, `/api/devices/discover`, `/api/devices/{id}/test`, and `/api/devices/{id}/context` to it.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/devices/{id}/context` | GET | Unified device context for wizard suggestions. Returns: interfaces (physical, bundle, subinterface, pwhe, free_physical), lldp, config_summary, wan_interfaces, igp, services (fxc_count, vrf_count, next_evi), loopbacks, vrfs, bridge_domains, flowspec_policies, routing_policies, bgp_peers, multihoming, platform_limits. Query `?live=true` for live fetch. |
| `/api/devices/{id}/test` | POST | Test SSH connection to device |
| `/api/config/{id}/running` | GET | Cached or live running config |
| `/api/config/{id}/summary` | GET | Parsed config summary (AS, RTs, EVPN, etc.) |
| `/api/config/{id}/sync` | POST | Fetch and cache config from device |
| `/api/config/{id}/interfaces` | GET | Parsed interface list |
| `/api/config/{id}/diff` | GET | Cached vs live diff, in_sync status |
| `/api/config/compare` | POST | Compare two device configs (device_ids) |
| `/api/config/generate/interfaces` | POST | Generate interface config |
| `/api/config/generate/services` | POST | Generate service config |
| `/api/config/generate/bgp` | POST | Generate BGP peer config |
| `/api/config/generate/igp` | POST | Generate IGP (ISIS/OSPF) config |
| `/api/config/generate/batch` | POST | Batch generate from multiple hierarchies (items: [{hierarchy, params}]) |
| `/api/config/preview-diff` | POST | Preview diff of proposed config vs running (device_id, config) |
| `/api/operations/validate` | POST | Validate DNOS config (config, hierarchy, check_limits, check_interface_order). Returns valid, errors, warnings, suggestions. |
| `/api/config/templates` | GET | List policy templates |
| `/api/config/templates/generate` | POST | Generate from template |
| `/api/operations/delete-hierarchy` | POST | Delete config hierarchy (dry_run) |
| `/api/operations/push` | POST | Push config to device (merge/replace/dry_run). Returns job_id. When dry_run, holds SSH after commit check for commit/cancel. |
| `/api/config/push/progress/{job_id}` | GET | SSE stream for push progress (phase, percent, terminal lines, done, success, awaiting_decision) |
| `/api/operations/push/{job_id}/commit` | POST | Commit held config on same SSH session (after dry_run when check passed) |
| `/api/operations/push/{job_id}/cancel` | POST | Cancel held config (discard candidate) and close SSH session |
| `/api/operations/push/{job_id}/cleanup` | POST | Cleanup dirty candidate on device after failed commit check (connects fresh) |
| `/api/operations/jobs` | GET | List all jobs (active + recent history) |
| `/api/operations/jobs/{job_id}` | GET | Full job state including all terminal output |
| `/api/operations/jobs/{job_id}/retry` | POST | Re-submit same config. Returns new job_id. |
| `/api/operations/jobs/{job_id}` | DELETE | Remove job from history |
| `/api/config/limits/{device_id}` | GET | Platform limits (max_subifs) from limits.json |
| `/api/devices/discover` | POST | SSH discover device by IP, add to inventory |
| `/api/config/scan-existing` | POST | Scan device for existing sub-ids, VRFs, EVIs, L3 conflicts. Body: `{ device_id, ssh_host, scan_type: "interfaces"\|"services"\|"vrfs"\|"all" }`. Returns `existing_sub_ids`, `existing_vrfs`, `existing_evis`, `l3_conflicts`, `next_free`. Used by interface wizard collision check. |
| `/api/config/detect-pattern` | POST | Detect interface pattern (dot1q/qinq, stepping_tag, last_vlan, last_sub_id) from device config. Body: `{ device_id, ssh_host, parent_interface }`. Used for auto-fill in subif flow. |
| `/api/mirror/analyze` | POST | Analyze source vs target config for mirror. Body: `{ source_device_id, target_device_id, ssh_hosts?: [src_ip, tgt_ip] }`. Returns `source_summary`, `target_summary`, `smart_diff`, `interface_map`. |
| `/api/mirror/generate` | POST | Generate mirrored config. Body: `{ source_device_id, target_device_id, ssh_hosts, interface_map, section_selection?, output_mode: "full"\|"diff_only" }`. Returns `config`, `summary`, `line_count`, `diff_stats`. |
| `/api/mirror/preview-diff` | POST | Preview diff of proposed mirrored config vs target running. Body: `{ target_device_id, config, ssh_host }`. Returns `diff_text`, `lines_added`, `lines_removed`. |

**Config generation**: All `generate/*` endpoints use `scaler.wizard.config_builders` (pure DNOS generators). No frontend DNOS string construction. GUI previews always call backend API with full params. The terminal wizard (`interactive_scale.py`) also calls `config_builders.build_from_expansion()` for config generation, ensuring terminal and GUI produce identical DNOS output.

**Type-aware generation** (`config_builders.py`): Two categories with different output rules:
- **Basic types** (bundle, ph, irb): Parent gets `admin-state enabled` only. Sub-ifs get `admin-state` + VLAN + IP. No l2-service, MPLS, flowspec, BFD, or MTU.
- **Physical types** (ge100, ge400, ge10): Full E/7 flow. Sub-ifs support L2 mode (l2-service) OR L3 mode (IP, MPLS, flowspec, BFD, MTU). L2 and L3 are mutually exclusive.
- **Loopback**: `admin-state` + optional description + optional IPv4 (/32). No sub-interfaces.

**Config push**: `POST /api/operations/push` uses `ConfigPusher` from scaler. Progress streamed via SSE at `GET /api/config/push/progress/{job_id}`. The SSE stream includes `terminal` (new SSH output lines since last poll) via `live_output_callback` piped from ConfigPusher. ScalerAPI.connectPushProgress uses EventSource for real-time progress and terminal streaming.

**Hold-and-commit flow** (dry_run): When `dry_run=true`, backend uses `push_config_terminal_check_and_hold()` which pastes config, runs commit check, and keeps SSH session alive. Job enters `awaiting_decision` state. Frontend shows Commit Now / Cancel (discard) buttons in the progress panel. User clicks Commit -> `POST /api/operations/push/{job_id}/commit` sends commit on same session. User clicks Cancel -> `POST /api/operations/push/{job_id}/cancel` sends cancel+exit. No second push job. When commit check fails, Cleanup button calls `POST /api/operations/push/{job_id}/cleanup` to connect fresh and run cancel on device.

**Running Commits Panel**: `ScalerGUI.openCommitsPanel()` opens a persistent panel that polls `GET /api/operations/jobs` every 2s. Shows job cards with status dot (gray=pending, cyan=running, green=completed, red=failed), progress bar, and expand/minimize. Expanded cards show a live terminal view with SSH output. Error lines highlighted red; DNOS errors parsed with `suggestErrorFix()` (patterns: "already exists", "limit exceeded", "Hook failed"). Retry button re-submits via `POST /api/operations/jobs/{job_id}/retry`. Accessible via "Commits" button in Scaler CONFIG menu with active-job badge. Job history persisted to `~/.scaler_push_history.json` (max 50 jobs, terminal truncated to 200 lines on completion).

**Push parity**: All wizards (Interface, Service, VRF, Bridge Domain, FlowSpec, Routing Policy, BGP, IGP) share the same push flow: Review step (generates config, shows preview, validation, optional diff) -> Push step (dry_run / merge / replace / clipboard+SSH). All route through `ScalerAPI.pushConfig()` -> `ScalerGUI.showProgress()` -> commits panel. `ssh_host` is included in all push calls from `deviceContext.mgmt_ip`.

**Wizard Run History** (Phase 2): `recordWizardChange(deviceId, changeType, details, options)` stores full run records with `generatedConfig`, `params`, `pushMode`, `jobId`, `success`. Persisted to `localStorage` key `scaler_wizard_history` (max 100 entries). `updateWizardRunResult(jobId, success)` updates history when push completes. Per-wizard "Last Run" card shows at top of each wizard when history exists for that wizard+device. Global "Wizard Run History" panel in CONFIG menu shows chronological list grouped by date. "Re-run with same params" pre-fills wizard; "Re-run on different device" opens Mirror Wizard with source=history device, target=user-selected device.

**Re-run on different device** (Phase 4c): Both per-wizard Last Run card and global History panel wire "Re-run on different device" to `openMirrorWizard(sourceId)`. User selects target device; Mirror Wizard runs analyze -> generate -> diff vs target -> push. Uses ConfigMirror from `mirror_config.py` for device-agnostic config adaptation.

**Mirror Config Wizard**: `openMirrorWizard(prefillSourceId?, prefillTargetId?)` - when source is pre-filled (e.g. from history), only target selector shown. Flow: Analyze (fetch configs, compare) -> Generate Config (diff-only) -> Show diff vs target -> Push to Target. Uses `ScalerAPI.mirrorAnalyze()`, `mirrorGenerate()`, `mirrorPreviewDiff()`.

**Collision check** (Phase 3b): Interface wizard review step, when `interfaceType === 'subif'` and parent exists, calls `ScalerAPI.scanExisting()` before Generate. Shows warning panel with options: Skip conflicts, Start after existing (#N), Override. Auto-adjusts `startNumber`/`vlanStart` based on user choice.

**Reusable step components** (Phase 4A): `ScalerGUI._buildPushStep(opts)` returns a Push step with configurable `radioName`, `includeClipboard`, `infoText`. `_buildReviewStep(opts)`, `_buildInterfaceSelector(opts)`, `_buildAddressFamilySelector(opts)` provide shared HTML/collectData for wizard steps. VRF, Bridge Domain, FlowSpec, Routing Policy, and Service wizards use `_buildPushStep`.

**Scaler menu order** (Phase 4C): Configuration Wizards: Interface, Service, VRF, Bridge Domain, BGP, IGP, FlowSpec, Routing Policy, Multihoming (matches terminal wizard hierarchy order).

**Cross-wizard dependency warnings** (Phase 4D): `_getWizardDependencyWarnings(wizardType, data)` returns context-based warnings (e.g. VRF needs sub-interfaces, FlowSpec name conflict, Multihoming ESI). `_renderDependencyWarnings(warnings)` displays them. VRF Interface Attachment step shows when no sub-interfaces exist.

**Validation**: Review steps call `ScalerAPI.validateConfig({ config, hierarchy })` after generating config. Errors and warnings displayed in `scaler-validation-box`. Uses `CLIValidator.validate_generated_config()` (syntax, scale limits, interface order).

**Diff preview**: Interface wizard Review step has "Show diff vs running" button. Calls `ScalerAPI.previewConfigDiff(deviceId, config, sshHost)` to show proposed-vs-running unified diff.

**Platform limits**: The sub-interfaces step validates total count against `GET /api/config/limits/{device_id}` (sources `limits.json` vlan_pool max_capacity, default 20480). Warning shown if `count * subifCount > max_subifs`.

ScalerAPI (scaler-api.js) methods: getDevices, getDevice, getDeviceContext, testConnection, syncDevice, generateInterfaces, generateServices, generateBGP, generateIGP, batchGenerate, previewConfigDiff, validateConfig, compareConfigs, getConfigDiff, getInterfaces, getTemplates, generateTemplate, discoverDevice, deleteHierarchyOp, pushConfig, commitHeldJob, cancelHeldJob, cleanupHeldJob, connectPushProgress, getJobs, getJob, retryJob, deleteJob, getLimits, scanExisting, detectPattern, mirrorAnalyze, mirrorGenerate, mirrorPreviewDiff.

### Smart Wizard Suggestions (DeviceContextCache)

Wizards (Interface, Service, VRF, BGP, IGP) use a cached-then-live device context for smart suggestions:

- **Device resolution by SSH**: Canvas labels are NOT backend device IDs. Resolution uses `sshConfig.host` (which may be an IP, hostname, or serial number) as the primary key. `_resolveDeviceId(label)` extracts SSH credentials from the canvas device object. `ScalerAPI.getDeviceContext(deviceId, live, sshHost)` passes `ssh_host` to the backend.
- **Central IP resolution** (`_resolve_mgmt_ip(device_id, ssh_host)` in `scaler_bridge.py`): ALL endpoints use this single function. Uses cached `_build_scaler_ops_index()` (60s TTL) that indexes all `operational.json` files by serial, hostname, mgmt_ip, and dir name. Chain: 1) `ssh_host` is IP -> direct match in index; 2) `ssh_host` is serial/hostname -> match in index; 3) `device_id` exact match in index; 4) discovery API `_resolve_device`; 5) `device_inventory.json` fuzzy match; 6) partial name match (e.g. `PE-1` matches `YOR_PE-1`). Returns `(mgmt_ip, scaler_device_id, resolved_via)`. Results cached for 120s in `_resolve_cache`. Raises 503 if all fail.
- **NEVER add `_resolve_device()` calls directly in endpoints** -- always use `_resolve_mgmt_ip`. The discovery API frequently returns empty `mgmt_ip`; the central function handles all fallbacks.
- **Context builder** (`_get_device_context`): Uses `_resolve_mgmt_ip` first, then tries `_get_cached_config(scaler_device_id)`. Falls back to `_get_cached_config(device_id)` and `_get_cached_config(hostname)`. Returns `resolved_ip` field so frontend shows the actual IP.
- **DeviceContextCache**: `ScalerGUI.getDeviceContext(deviceId)` returns cached context if fresh (<60s), else fetches. `refreshDeviceContextLive(deviceId)` fetches live and updates cache. `invalidateDeviceContext(deviceId)` clears cache.
- **Instant wizard loading**: All wizards (Interface, Service, VRF, BGP, IGP) open instantly with cached data. If no fresh cache exists, the wizard renders immediately with a "Loading..." state, then fetches context in the background and re-renders when ready.
- **Cross-wizard awareness**: `recordWizardChange(deviceId, changeType, details)` logs wizard changes to `_wizardChangeLog`. `getDeviceContext()` merges pending changes into the returned context so the next wizard sees updated free interfaces, next EVI/bundle numbers, etc. Changes persist for 5 minutes. Devices with pending changes show a "changed" badge in the device selector.
- **Context panel**: Collapsible panel at top of each wizard. Compact visual bar for interface counts (phys, bundle, lo, sub-if), LLDP chips with neighbor tooltips, color-coded status (green=has data, orange=partial, red=no SSH). System line: `System | AS | RID`. "Refresh Live" fetches over SSH.

### VRF / L3VPN Wizard (5 Steps)

The VRF wizard creates L3VPN VRF instances via `build_service_config(service_type='vrf')` which delegates to `_generate_vrf_config` from interactive_scale. Steps: VRF Naming (prefix, start, count, description) -> Interface Attachment (optional, sub-interfaces from context) -> BGP & Route Targets (enable BGP, AS, router-id, RT mode same_as_rd/custom) -> Review (config preview, validation) -> Push. Uses `POST /api/config/generate/services` with `service_type: 'vrf'` and params: `attach_interfaces`, `interface_list`, `interfaces_per_vrf`, `enable_bgp`, `bgp_config`, `rt_config`.
- **DNAAS device handling**: DNAAS devices (NCM/NCF/NCC/LEAF/SPINE) are excluded from wizard device selectors. If a DNAAS device does appear in a wizard, LLDP suggestions are disabled (`ctx._isDnaas = true`).
- **Suggestion chips**: `ScalerGUI.renderSuggestionChips(items, { type, onSelect })` renders clickable chips. Types: `lldp` (cyan), `free` (green), `config` (orange), `smart` (purple). Items may have `target` for routing onSelect (e.g. `target: 'evi'` or `target: 'asn'`). Bundle member chips use toggle mode: click to add/remove, `.chip-selected` for selected state.

### Interface Wizard Architecture (7 Steps)

The Interface Wizard has full parity with the scaler-wizard terminal backend. Steps are **dynamically composed per type** using `stepBuilder` -- the step indicator shows only relevant steps for the selected type:

| Type | Steps (in order) | Count |
|------|-------------------|-------|
| **Loopback** | Type → IP & Description → Review → Push | 4 |
| **Bundle** | Type → Bundle Members → Sub-ifs & IP → Encap → Review → Push | 6 |
| **PH / IRB** | Type → Sub-ifs & IP → Encap → Review → Push | 5 |
| **GE100/GE400/GE10** | Type → Location → Mode & Features → Encap → Review → Push | 6 |

When the user changes the type in Step 0 and clicks Next, the WizardController calls `stepBuilder(data)` to recompose the step array, dependencies, and keys. The step indicator re-renders with only the relevant dots.

**Step 3 per-type feature gating** (matches terminal wizard exactly):
- **Loopback**: Description field, IPv4 address (/32). No sub-ifs, no L2/MPLS/etc.
- **Bundle/PH/IRB** (basic): Sub-ifs + VLAN + IP addressing (IPv4/IPv6/dual, 3 step modes). No L2 Service, MPLS, Flowspec, BFD, or MTU.
- **GE100/GE400/GE10** (physical): Sub-ifs + VLAN + Interface Mode selector (L2 vs L3). L2 mode: l2-service, hides IP/L3 features. L3 mode: IP, MPLS, Flowspec, BFD, MTU.

**Dual-stack IP**: When `ipVersion=dual`, separate IPv4 and IPv6 start/prefix fields. Params: `ip_start`, `ip_prefix` (IPv4), `ipv6_start`, `ipv6_prefix` (IPv6).

**Backend parameter contract** (`POST /api/config/generate/interfaces`): `interface_type`, `start_number`, `count`, `create_subinterfaces`, `subif_vlan_start`, `vlan_mode` (single/qinq), `outer_vlan_start`, `inner_vlan_start`, `l2_service` (physical only), `ip_enabled`, `ip_version`, `ip_start`, `ip_prefix`, `ipv6_start`, `ipv6_prefix`, `ip_mode` (per_subif/per_parent/unique_subnet), `mpls_enabled` (physical only), `flowspec_enabled` (physical only), `bundle_members`, `lacp_mode` (active/passive/static), `slot`, `bay`, `port_start`, `mtu` (physical only), `bfd` (physical only), `description`.

**Step re-editing**: `WizardController` supports `stepDependencies`, `stepKeys`, and `skipIf`. When going back and changing a step, dependent steps are invalidated (their collected keys cleared). The "Next" button shows "Update" when re-visiting a prior step. Steps with `skipIf: (data) => bool` are auto-skipped during forward/backward navigation.
- **Device selector alignment**: `openDeviceSelector` uses `_getCanvasDeviceObjects()` to get canvas devices with their SSH credentials. Devices with SSH configured appear first; devices without SSH appear greyed out with "Set SSH first". DNAAS devices are excluded.

---

## 🧩 Modular Architecture

The topology editor uses a modular architecture with wrapper modules that provide clean APIs.

### Module Overview

#### Foundation Layer (load first)
| Module | Class | Property | Purpose |
|--------|-------|----------|---------|
| `topology-errors.js` | ErrorBoundary | `window.ErrorBoundary` | Crash protection & recovery |
| `topology-registry.js` | TopologyRegistry | `window.TopologyRegistry` | **Feature routing - check first!** |
| `topology-events.js` | TopologyEventBus | `editor.events` | Event pub-sub system |
| `topology-geometry.js` | TopologyGeometry | `window.TopologyGeometry` | Math/geometry utilities |
| `topology-platform-data.js` | PlatformData | `editor.platformData` | Platforms & transceivers |

#### Core Layer
| Module | Class | Property | Purpose |
|--------|-------|----------|---------|
| `topology-input.js` | InputManager | `editor.input` | Input state machine |
| `topology-files.js` | FileManager | `editor.files` | Auto-save, crash recovery, session tracking |
| `topology-file-ops.js` | FileOps | `window.FileOps` | Save/load/export, bug topologies, custom sections, clear canvas |
| `topology-drawing.js` | DrawingManager | `editor.drawing` | Canvas rendering |
| `topology-history.js` | HistoryManager | `editor.history` | Undo/redo |

#### Object Managers
| Module | Class | Property | Purpose |
|--------|-------|----------|---------|
| `topology-text.js` | TextManager | `editor.text` | Text handling |
| `topology-shapes.js` | ShapeManager | `editor.shapes` | Shape handling |
| `topology-devices.js` | DeviceManager | `editor.devices` | Device management |
| `topology-links.js` | LinkManager | `editor.links` | Links & BUL chains |

#### UI Layer
| Module | Class | Property | Purpose |
|--------|-------|----------|---------|
| `topology-ui.js` | UIManager | `editor.ui` | Toolbars & panels |
| `topology-menus.js` | MenuManager | `editor.menus` | Context menus |
| `topology-minimap.js` | MinimapManager | `editor.minimapMgr` | Minimap display |
| `topology-link-editor.js` | LinkEditorModal | `editor.linkEditor` | Link details modal |
| `topology-groups.js` | GroupManager | `editor.groups` | Object grouping |
| `topology-toolbar.js` | ToolbarManager | `editor.toolbarMgr` | Toolbar setup |
| `topology-dnaas.js` | DnaasManager | `editor.dnaas` | DNAAS discovery |
| `topology-network-mapper.js` | NetworkMapperManager | `editor.networkMapper` | Recursive LLDP network discovery + auto-layout |

#### Extracted Handlers (Feb 2026 decomposition)
| Module | Global | Purpose |
|--------|--------|---------|
| `topology-context-menu-handlers.js` | `window.ContextMenuHandlers` | Context menus, curve submenus, copy/paste style, layers/device-style submenus |
| `topology-link-details.js` | `window.LinkDetailsHandlers` | Link editor modal, VLAN validation, link details table |
| `topology-shape-methods.js` | `window.ShapeMethods` | Shape creation, hit detection, resize handles, toolbar |
| `topology-selection-popups.js` | `window.SelectionPopups` | Device style palette, link width/style/curve options, LLDP submenu |
| `topology-link-geometry.js` | `window.LinkGeometry` | Link hit detection, distance calculations, BUL chain analysis |
| `topology-text-attachment.js` | `window.TextAttachment` | Text-to-link attachment, nearest link, adjacent text |

#### Mouse Handlers (Feb 2026 decomposition)
| Module | Global | Purpose |
|--------|--------|---------|
| `topology-mouse.js` | `window.MouseHandler` | Thin coordinator - delegates to down/move/up handlers |
| `topology-mouse-down.js` | `window.MouseDownHandler` | Click handling, selection, drag setup, double-tap |
| `topology-mouse-move.js` | `window.MouseMoveHandler` | Drag, link stretch, cursor feedback, collision |
| `topology-mouse-up.js` | `window.MouseUpHandler` | Drag release, link creation, placement, cleanup |

#### Testing
| Module | Class | Property | Purpose |
|--------|-------|----------|---------|
| `topology-tests.js` | TopologyTests | `window.TopologyTests` | Automated test suite |

### Using Modules

All modules use constructor injection and delegate to the main editor:

```javascript
// Modules receive the editor instance
class DeviceManager {
    constructor(editor) {
        this.editor = editor;
    }
    
    // Methods delegate to editor
    getAll() {
        return this.editor.objects?.filter(obj => obj.type === 'device') || [];
    }
}
```

### Accessing Modules

```javascript
// From editor instance
const editor = window.topologyEditor;

// Device operations
editor.devices.getAll();
editor.devices.addAtPosition('SA-40C', 100, 200);
editor.devices.getById('device-1');

// Link operations
editor.links.getAll();
editor.links.analyzeBULChain(link);
editor.links.isHead(link);

// UI operations
editor.ui.showDeviceToolbar(device);
editor.ui.hideAllToolbars();

// Menu operations
editor.menus.showContextMenu(x, y, obj);
```

### Script Load Order

Modules must load BEFORE `topology.js`:

```html
<!-- Foundation -->
<script src="topology-events.js"></script>
<script src="topology-geometry.js"></script>
<script src="topology-platform-data.js"></script>

<!-- Core Services -->
<script src="topology-files.js"></script>
<script src="topology-file-ops.js"></script>
<script src="topology-drawing.js"></script>

<!-- Object Managers -->
<script src="topology-text.js"></script>
<script src="topology-shapes.js"></script>
<script src="topology-devices.js"></script>
<script src="topology-links.js"></script>

<!-- UI Layer -->
<script src="topology-ui.js"></script>
<script src="topology-menus.js"></script>
<script src="topology-minimap.js"></script>
<script src="topology-link-editor.js"></script>
<script src="topology-groups.js"></script>
<script src="topology-toolbar.js"></script>
<script src="topology-dnaas.js"></script>

<!-- Main (loads last, uses all modules) -->
<script src="topology.js"></script>

<!-- Tests (optional) -->
<script src="topology-tests.js"></script>
```

### Running Tests

```javascript
// Run all tests
TopologyTests.runAll();

// Run specific module tests
TopologyTests.runModule('devices');
TopologyTests.runModule('links');
TopologyTests.runModule('ui');
TopologyTests.runModule('linkeditor');
TopologyTests.runModule('stats');

// View module diagnostics
ModuleStats.print();          // Print formatted stats table
ModuleStats.getSummary();     // Get stats object
ModuleStats.getHealth();      // Get 'healthy', 'degraded', or 'critical'
```

---

## 🔗 BUL (Bound Unbound Link) Chain System

### Core Concepts

**UL (Unbound Link)**: A link not attached to devices at both ends. Has two endpoints: `start` and `end`.

**BUL (Bound Unbound Link)**: Multiple ULs merged together into a chain.

**TP (Terminal Point)**: A FREE endpoint - not attached to device AND not connected to another link.

**MP (Merge Point)**: Where two ULs connect - the shared point between parent and child.

### Merge Relationships

Each link can have:
- `mergedWith`: Points to CHILD link (this link is parent)
- `mergedInto`: Points to PARENT link (this link is child)

**A link can only have ONE child (one `mergedWith`)!**

```
Chain: HEAD -- MP1 -- MIDDLE -- MP2 -- TAIL

HEAD:   mergedWith → MIDDLE,  mergedInto = null
MIDDLE: mergedWith → TAIL,    mergedInto → HEAD  
TAIL:   mergedWith = null,    mergedInto → MIDDLE
```

### Key Properties in mergedWith

```javascript
mergedWith = {
    linkId: 'link_123',           // Child link ID
    connectionPoint: {x, y},       // MP position (CLONED, not shared!)
    connectionEndpoint: 'start',   // Which endpoint of PARENT connects to child
    childConnectionEndpoint: 'end', // Which endpoint of CHILD connects to parent
    parentFreeEnd: 'end',          // Which endpoint of PARENT is FREE
    childFreeEnd: 'start',         // Which endpoint of CHILD is FREE
    mpNumber: 1                    // MP number in chain (MP-1, MP-2, etc.)
}
```

### CRITICAL: Endpoint Detection

Use `isEndpointConnected(link, endpoint)` to check if an endpoint is connected:
- Checks BOTH `mergedWith.connectionEndpoint` AND `mergedInto.childEndpoint`
- Returns `true` if endpoint is an MP (connected to another link)
- Returns `false` if endpoint is a TP (free)

**NEVER use only `device1`/`device2` checks - must also check merge connections!**

```javascript
// CORRECT: Check device AND merge connection
const isStartFree = !link.device1 && !this.isEndpointConnected(link, 'start');

// WRONG: Only checks device
const isStartFree = !link.device1;  // Missing merge check!
```

### Extending from TP (Link-from-TP Mode)

When user clicks a TP to extend the chain:

1. **APPEND** (sourceLink has no child): sourceLink becomes parent of newUL
   - `sourceLink.mergedWith → newUL`
   - `newUL.mergedInto → sourceLink`

2. **PREPEND** (sourceLink already has a child): newUL becomes parent (new HEAD)
   - `newUL.mergedWith → sourceLink`
   - `sourceLink.mergedInto → newUL`

**NEVER overwrite existing `mergedWith` - it breaks the chain!**

### Finding All Links in Chain

```javascript
const allLinks = this.getAllMergedLinks(link);
// Traverses both mergedWith (children) and mergedInto (parents)
// Returns array of all connected links
```

---

## 🎯 Hitbox & Selection Rules

### Link Hit Detection

Use `_checkLinkHit(x, y, obj)` which:
- Calculates visual link width based on zoom
- Uses screen-pixel tolerance for consistent feel
- Returns distance to link (-1 if not hit)

**For BUL chains**: TAIL/MIDDLE links delegate hit detection to HEAD.

### Finding Closest Object

`findObjectAt(x, y)` accumulates ALL links within clicking distance and returns the **closest** one, not just the first found.

### Selection Priority (Visual = Hitbox)

Objects are selected based on visual stacking order: higher-layer objects have priority over lower-layer ones. Within the same layer, priority is: text > device > link > shape. Only `mergedToBackground` shapes are always lowest priority. This ensures "what you see is what you click."

---

## 🎨 UI/Style Conventions

### Device Style Buttons
- Active state: **GREEN** gradient (like "Place Device" button)
- Labels: `white-space: nowrap` - no truncation

### Link Style Buttons  
- Active state: **CYAN** gradient

### Button Text
- "Place Device" (not "Add Device")

### Selection Toolbars (Liquid Glass Design)

**Single left-click** on objects shows floating toolbars (no right-click needed):

| Object | Function | Toolbar ID | Trigger |
|--------|----------|------------|---------|
| Text | `showTextSelectionToolbar(textObj)` | `text-selection-toolbar` | Left-click to select |
| Device | `showDeviceSelectionToolbar(device)` | `device-selection-toolbar` | Left-click to select |
| Link | `showLinkSelectionToolbar(link, clickPos?)` | `link-selection-toolbar` | Left-click to select |

**Toolbar Behavior:**
- Appears 150ms after selection (prevents showing during drag)
- Hidden when: dragging starts, clicking empty space, returning to base mode
- **Re-appears after drag ends** at the new object position
- Call `hideAllSelectionToolbars()` to hide all toolbars programmatically

**Toolbar Positioning:**
- **Device**: Below the device center (like text toolbar)
- **Link**: At the click location (where user clicked on the link)
- **Text**: Below the text center

**Toolbar Design Pattern:**
```javascript
toolbar.style.cssText = `
    position: fixed;
    background: rgba(0, 0, 0, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 5px 8px;
    backdrop-filter: blur(20px) saturate(150%);
    display: flex;
    gap: 2px;
`;
```

**Hide All Toolbars:**
```javascript
this.hideAllSelectionToolbars(); // Hides text, device, and link toolbars
```

**Device Toolbar Options:** SSH, Rename, Color, Style, Duplicate, Lock, Delete
- SSH → `handleContextSSHAddress()`
- Rename → `showRenamePopup(device)`
- Color → `showColorPalettePopup(device, 'device')`
- Style → `showDeviceStylePalette(device)`
- Duplicate → `duplicateSelected()`
- Lock → toggle `device.locked`
- Delete → `deleteSelected()`

**Link Toolbar Options:** Add Text, Color, Width, Style, Curve, Duplicate, Delete
- Add Text → `showAdjacentTextMenu(link)`
- Color → `showColorPalettePopup(link, 'link')`
- Width → `showLinkWidthSlider(link)`
- Style → `showLinkStyleOptions(link)`
- Curve → `showLinkCurveOptions(link)`
- Duplicate → `duplicateSelected()`
- Delete → `deleteSelected()`

---

## ✅ Before Making Changes

1. Read this file
2. `grep` for existing patterns in codebase
3. Check related `.md` files for context
4. Read the specific code section before modifying

## ✅ After Making Changes

1. Verify braces are balanced:
   ```bash
   python3 -c "js=open('topology.js').read(); print('✓' if js.count('{')==js.count('}') else '❌')"
   ```
2. Test the change in browser
3. Update this file with new patterns/fixes

---

## 🐛 Recent Fixes (Jan 2026)

### Wizard Smart Features (Mar 2026)

**Phase 1 - Sub-interface count bug**: Step invalidation only when `interfaceType` changes (preserves `subifCount`). `isLoopback` computed inside `updateLimitsWarning` from `data.interfaceType`. Debug logging in review step and `onComplete`.

**Phase 2 - Wizard history**: `recordWizardChange` extended with `generatedConfig`, `params`, `pushMode`, `jobId`. Persisted to `localStorage` (`scaler_wizard_history`, max 100). Per-wizard Last Run card and global History panel. Re-run / Re-run on other device.

**Phase 3 - Skip-existing**: `POST /api/config/scan-existing`, `POST /api/config/detect-pattern`. Interface wizard review step collision check with Skip/Start-after/Override options.

**Phase 4 - Mirror**: `POST /api/mirror/analyze`, `/generate`, `/preview-diff`. Mirror Config wizard (source/target, analyze, generate, diff, push). "Re-run on different device" wired to Mirror Wizard flow.

**Files**: scaler-gui.js, scaler-api.js, scaler_bridge.py, styles.css, scale_operations.py, mirror_config.py.

### Arrow Tips Drawn On Top of Devices (Mar 1)
**Problem**: Link arrowheads were drawn during the link pass (before devices), so device fills covered the arrow tips, making them invisible.
**Fix**: Arrow geometry/styling is now computed in `drawLink`/`drawUnboundLink` and stored on the link object (`_arrowTipEnd`, `_arrowEndAngle`, `_arrowLength`, `_arrowAngleSpread`, `_arrowFillColor`, etc.). A new `drawLinkArrows()` function in `topology-link-drawing.js` renders them in a dedicated "ARROW TIPS PASS" in `topology-draw.js` that runs after devices and labels.
**Files**: `topology-link-drawing.js`, `topology-draw.js`, `topology.js` (delegation stub).

### Layer-Based Selection Priority (Mar 1)
**Problem**: Objects on higher visual layers were not selected with priority — shapes were always forced to lowest selection priority regardless of layer.
**Fix**: `findObjectAt` in `topology-object-detection.js` now sorts candidates by `layer` (descending) first, then by `typeOrder` (text > device > link > shape) within the same layer. Only `mergedToBackground` shapes retain bottom priority.
**Files**: `topology-object-detection.js`.

### Modular Decomposition (Feb 12)
**Change**: Extracted ~11,000 lines from `topology.js` (17K -> 13.4K) and split `topology-mouse.js` (7.5K -> 33 lines coordinator + 3 handler files).
**New modules**: `topology-context-menu-handlers.js` (1605 lines), `topology-link-details.js` (671), `topology-shape-methods.js` (464), `topology-selection-popups.js` (522), `topology-link-geometry.js` (523), `topology-text-attachment.js` (337), `topology-mouse-down.js` (2538), `topology-mouse-move.js` (2775), `topology-mouse-up.js` (1985).
**Pattern**: Each extracted method receives `editor` as first parameter instead of using `this`. Stubs in topology.js delegate via `if (window.ModuleName) return window.ModuleName.method(this, ...args);`
**Load order**: New modules load BEFORE `topology.js` via `<script>` tags in `index.html`.

### Seamless Object-to-Object Toolbar Transition (Feb 12)
**Problem**: Clicking from one device to another caused the old toolbar to linger for 150ms before being replaced, making transitions feel janky.
**Root cause**: `hideAllSelectionToolbars()` was only called when clicking empty grid, not when clicking a different object. The 150ms toolbar delay was the same for first selection and transitions.
**Fix (topology-mouse.js)**:
1. Added `editor.hideAllSelectionToolbars()` immediately in the `!alreadySelected` path (line ~1230), so the old toolbar disappears instantly when clicking a new object.
2. Introduced `hadPreviousSelection` flag to use a shorter toolbar delay (50ms) when transitioning between objects vs. first selection from empty (150ms).
**Result**: Old toolbar vanishes instantly → 50ms pause → new toolbar appears. All object types (device, link, text, shape) benefit.

### Syntax Error in topology-mouse.js (Feb 12)
**Problem**: Duplicate closing code (lines 7515-7520) caused `SyntaxError: Unexpected token '}'`, preventing `window.MouseHandler` from loading. All canvas clicks silently failed.
**Fix**: Removed the duplicate `}`, `},`, `};`, and `console.log` lines at the end of the file.

### TB+Shape Group Jump, Copy Style from TB, CS Cancel (Feb 10)
**TB+Shape jump**: When text box and shape are grouped and dragged, they jumped. Root cause: momentum was not stopped before capturing positions when expanding group selection. Fix: Call momentum.stopAll() and reset() in the group expand path (topology-mouse.js, topology-groups.js) before building multiSelectInitialPositions.

**Copy Style from TB**: Text toolbar Copy Style only set copiedStyle but never pasteStyleMode=true, so click-to-paste didn't work. Fix: Call editor.copyObjectStyle(textObj) instead of manually setting copiedStyle.

**Copy Style cancel**: Added toast on paste-mode entry: "Click objects to paste. Press Escape to cancel." Added toast on exit: "Copy Style cancelled". Escape already cancelled; now it's discoverable.

**Copy Style cross-type rules** (in `_applyStyleToObject`):
| Source → Target | Color mapping | Other |
|---|---|---|
| Device → TB | device.color → TB bg (if has bg) or text; device.labelColor → TB text | font props |
| TB → Device | TB bg → device.color; TB text → device.labelColor | font props |
| TB → Link | TB bg → link.color (if has bg); else TB text → link.color | TB borderStyle → link style; TB borderWidth → link width |
| Link → TB | link.color → TB bg (if has bg) or text | link style → TB borderStyle |
| TB → Shape | TB bg → shape.fill; TB border/text → shape.stroke (if has bg); else text → both | TB borderWidth → stroke width |
| Shape → TB | shape.fill → TB bg (if has bg) or text; shape.stroke → TB border | shape strokeWidth → TB borderWidth |
| Same-type | full property copy | all applicable props |

**Per-TB `alwaysFaceUser`**: Link-attached TBs can toggle `alwaysFaceUser = true` to stay horizontal (readable) regardless of link angle. The drawing code (`topology-canvas-drawing.js` line ~725) checks `text.alwaysFaceUser === true` and forces 0° rotation. This property is preserved in Copy Style (TB→TB) and shown as an eye/eye-off button in the text selection toolbar for link-attached TBs.

### Group Drag: Jump Fix + BUL Restriction (Feb 10, refined Feb 11)
**Problem**: Grouped objects (TB+shape) jump when grabbed and moved.
**Root cause (FINAL)**: Normal selection path in handleMouseDown did NOT expand groups causing dragStart offset/absolute mismatch. Also stale positions and pointer+mouse double events.
**Fix (3 layers)**: (a) ALL mousedown paths expand groups with isMultiSelect. (b) Threshold handler re-captures FRESH positions. (c) Safety net in handleMouseMove fixes dragStart. 8ms dedup timer.
**RULE**: dragStart for multi-select = ABSOLUTE mouse pos. For single-object = OFFSET. Never mix.

**Problem 2**: Merged (BUL) shapes grouped with devices/shapes - moving fails silently.
**Fix**: Before starting group/multi-select drag, check if selection has both BUL links and other objects (device, shape, text). If so, block drag and show toast: "BUL chains grouped with devices/shapes cannot be moved together. Ungroup first, or move each separately."

### Left-Click Selection Toolbars (Jan 12)
**Change**: Toolbars now appear on **single left-click** (selection), not just right-click.

**Trigger:** Left-click to select any object → toolbar appears after 150ms delay
**Hidden when:** Dragging, clicking empty space, or returning to base mode

**Positioning:**
- Device toolbar: Below device center
- Link toolbar: At click location (passed via `clickPos` parameter)
- Text toolbar: Below text center

**Code Pattern:**
```javascript
// In handleMouseDown - after selection:
setTimeout(() => {
    if (this.selectedObject === clickedObject && !this.dragging) {
        if (clickedObject.type === 'text' && !this._inlineTextEditor) {
            this.showTextSelectionToolbar(clickedObject);
        } else if (clickedObject.type === 'device') {
            this.showDeviceSelectionToolbar(clickedObject);
        } else if (clickedObject.type === 'link' || clickedObject.type === 'unbound') {
            this.showLinkSelectionToolbar(clickedObject);
        }
    }
}, 150);
```

### Selection Toolbars - Liquid Glass Design (Jan 12)
**Change**: Replaced traditional right-click context menus with floating liquid glass toolbars.

**New Functions:**
- `showDeviceSelectionToolbar(device)` - SSH, Rename, Color, Style, Lock, Delete
- `showLinkSelectionToolbar(link)` - Add Text, Color, Width, Style, Curve, Delete
- `hideAllSelectionToolbars()` - Hides all toolbars at once

### BUL Extension from TP Bug (Fixed)
**Problem**: Clicking TP to extend chain would create duplicate TP at MP location.

**Root Causes**:
1. `isFreeTP` only checked device attachment, not merge connections
2. Code overwrote `mergedWith` when extending, breaking existing chain

**Fix**:
1. Use `isEndpointConnected()` in `isFreeTP` check
2. Implement PREPEND vs APPEND logic - if sourceLink has child, new link becomes HEAD

### Device Style Button Names (Fixed)
**Problem**: Names truncated ("Cl...", "C...", etc.)

**Fix**: Added `white-space: nowrap; overflow: visible` to `.style-label`

### Refresh (R / Cmd+R) Without Save-As Suggestion (Fixed)
**Problem**: Refreshing the app via **R** or **Cmd+R** could show "Save As..." (File menu) or browser "Leave site?" dialog.

**Fix**:
1. **No `beforeunload` handler** – Removed from `topology.js` and `bundle.js`. Auto-save already persists to localStorage; a handler triggers browser dialogs.
2. **R and Cmd+R/Ctrl+R handled in-app** – In `handleKeyDown`: `preventDefault()`, `stopPropagation()`, close File dropdown (`#file-dropdown-menu`), then `window.location.reload()`. Ensures no menu or save-as suggestion appears on refresh.

**Files**: `topology.js`, `bundle.js`. See `REMOVE_REFRESH_PROMPT_FIX.md` for details.

---

## 🚫 NEVER DO

1. ❌ Set `mergedWith` without checking if link already has a child
2. ❌ Check only `device1`/`device2` for free endpoint (must also check merges)
3. ❌ Share `connectionPoint` objects between mergedWith and mergedInto (CLONE them!)
4. ❌ Modify code without reading it first
5. ❌ Forget to update this file after fixes
6. ❌ Add a `beforeunload` handler that prompts or forces save on refresh (causes "Leave site?" / save-as suggestion)

## ✅ ALWAYS DO

1. ✅ Use `isEndpointConnected()` to check if endpoint is free
2. ✅ Clone connection points: `{ x: point.x, y: point.y }`
3. ✅ Handle both PREPEND and APPEND scenarios for chain extension
4. ✅ Verify braces balance after edits
5. ✅ Update DEVELOPMENT_GUIDELINES.md after successful fixes
6. ✅ Check `TopologyRegistry.whereDoesThisBelong()` before adding new features
7. ✅ Wrap critical operations with `ErrorBoundary`
8. ✅ Run `TopologyTests.runAll()` after changes

---

## 📋 Feature Templates

### Using the Registry

Before adding new features, check the registry:

```javascript
// In browser console:
TopologyRegistry.whereDoesThisBelong("add alignment tool")
// Returns: { action: 'edit', file: 'topology-input.js', module: 'input', reason: '...' }

// Generate code template:
TopologyRegistry.generateTemplate('objectManager', 'Annotation')
TopologyRegistry.generateTemplate('modal', 'Settings')
TopologyRegistry.generateTemplate('integration', 'Monitor')
```

### Template: New Object Manager```javascript
// topology-{thing}.js
class {Thing}Manager {
    constructor(editor) {
        this.editor = editor;
        this.items = [];
        console.log('{Thing}Manager initialized');
    }
    
    // CRUD operations
    create(options) {
        const item = { id: Date.now(), type: '{thing}', ...options };
        this.items.push(item);
        this.editor.events?.emit('{thing}:created', item);
        this.editor.saveState?.();
        return item;
    }
    
    getAll() { return this.items; }
    getById(id) { return this.items.find(i => i.id === id); }
    remove(id) {
        this.items = this.items.filter(i => i.id !== id);
        this.editor.events?.emit('{thing}:removed', { id });
    }
    
    // Spatial query
    findAt(x, y) {
        return this.items.find(item => /* hit test */);
    }
    
    // Drawing
    draw(ctx, item) {
        // Render the item
    }
}

window.{Thing}Manager = {Thing}Manager;
window.create{Thing}Manager = (editor) => new {Thing}Manager(editor);
```

### Template: New Input State

```javascript
// Add to topology-input.js
class {Mode}Handler extends InputStateHandler {
    constructor(editor, inputManager) {
        super(editor, inputManager);
        this.name = '{mode}';
    }
    
    enter(context = {}) {
        super.enter(context);
        this.editor.canvas.style.cursor = 'crosshair';
    }
    
    exit() {
        this.editor.canvas.style.cursor = 'default';
        super.exit();
    }
    
    onMouseDown(e) { return null; } // null = stay, 'idle' = exit
    onMouseMove(e) { return null; }
    onMouseUp(e) { return 'idle'; }
    onKeyDown(e) { if (e.key === 'Escape') return 'idle'; return null; }
}

// Register: inputManager.registerState('{mode}', new {Mode}Handler(editor, inputManager));
```

### Template: New Modal

```javascript
// topology-{name}-modal.js
class {Name}Modal {
    constructor(editor) {
        this.editor = editor;
        this.element = null;
        this.isVisible = false;
    }
    
    show(data = {}) {
        this.data = data;
        this.createModal();
        this.populateFields();
        this.isVisible = true;
    }
    
    hide() {
        if (this.element) {
            this.element.remove();
            this.element = null;
        }
        this.isVisible = false;
    }
    
    createModal() {
        this.element = document.createElement('div');
        this.element.className = '{name}-modal-overlay';
        this.element.innerHTML = `
            <div class="{name}-modal">
                <div class="modal-header"><h2>{Name}</h2><button class="close">&times;</button></div>
                <div class="modal-body"><!-- fields --></div>
                <div class="modal-footer"><button class="cancel">Cancel</button><button class="save">Save</button></div>
            </div>
        `;
        document.body.appendChild(this.element);
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        this.element.querySelector('.close')?.addEventListener('click', () => this.hide());
        this.element.querySelector('.cancel')?.addEventListener('click', () => this.hide());
        this.element.querySelector('.save')?.addEventListener('click', () => this.save());
    }
    
    save() { /* validate and save */ this.hide(); }
}

window.{Name}Modal = {Name}Modal;
```

---

## 🛡️ Error Handling Patterns

### Wrapping Event Handlers

```javascript
// Use ErrorBoundary for crash protection
const safeHandler = ErrorBoundary.wrapEventHandler(
    (e) => this.handleClick(e),
    this,
    'click'
);
this.canvas.addEventListener('click', safeHandler);
```

### Safe Module Initialization

```javascript
// In topology.js constructor
this.myModule = ErrorBoundary.safeModuleInit('ModuleName',
    () => new MyModule(this),
    () => ({ /* fallback object */ })
);
```

### Auto-Save and Crash Recovery

```javascript
// Enable auto-save (30 second interval)
this.files.enableAutoSave();

// Check for recovery on startup
this.files.checkForRecovery();
```

**Recovery skip conditions** (won't show dialog):
1. Previous session closed cleanly (`beforeunload` → `markSessionClosed()`)
2. Recovery data matches the last saved topology (`topology_current` in localStorage)
3. `quickSaveTopology()` syncs recovery data session ID to current session

### File Menu

The File button (`#btn-file-menu`) in the top bar opens `#file-dropdown-menu` positioned
directly below the button (not centered). Wired in `topology-toolbar-setup.js`.
Close handlers: outside-click + Escape (inline script in `index.html`).

### File Upload

`loadTopology(event)` in `topology.js` reads via `FileReader`, handles wrapped formats
(`{topology: {objects}}`, bare arrays), and resets the file input for re-selection.

---

## 🧪 Testing Checklist

After any code change:

```javascript
// Run all tests
TopologyTests.runAll()

// Run specific module tests
TopologyTests.runModule('devices')
TopologyTests.runModule('links')
TopologyTests.runModule('input')
```

Manual testing:
- [ ] Feature works as expected
- [ ] Selection still works
- [ ] Undo/Redo still works
- [ ] Save/Load still works
- [ ] No console errors
6. ✅ Handle R and Cmd+R/Ctrl+R for refresh in `handleKeyDown` (preventDefault, close file menu, reload) so no save-as appears

---

## Debug-DNOS Topology Integration

The topology app integrates with `/debug-dnos` bug evidence system:

### Backend (`serve.py`)

- `GET /debug-dnos-topologies/list.json` — scans `~/SCALER/FLOWSPEC_VPN/bug_evidence/*.topology.json` and returns a JSON list
- `GET /debug-dnos-topologies/<filename>` — serves a specific `.topology.json` file

### Frontend (`topology.js` + `index.html`)

- "Topologies" dropdown has a "Debug-DNOS Topologies" section (red accent)
- `showDebugDnosTopologiesSubmenu()` fetches the list
- `showDebugDnosTopologySelector(topologies)` shows a modal picker
- `loadDebugDnosTopology(filename)` fetches and loads into the canvas

### Topology JSON Visual Standards (for generated files)

**Pre-creation checklist (mandatory):**

- Identify the PRIMARY bug (not secondary effects). Re-read the `.md` Expected/Actual sections first.
- VRF panel text must use `show` command language (e.g., "Redirect target: selected"), NOT code internals (e.g., "BGP_CONFIG_RD not set").
- For comparison bugs: both panels show what differs and the result from the user's perspective.
- Scan JSON for code-level leakage (function names, file names, protobuf fields) — remove any.

**Visual rules:**

1. Device labels = name only; IP as separate TB below (`y = device_y + radius + 30`)
2. Every link has a transparent protocol label at midpoint (`_onLinkLine: true`)
3. VRF info uses rectangle shapes as containers with text on top
4. Route info box near ExaBGP with "Route Injected:" header
5. No "BUG:" labels, no code-level details
6. Z-order: Devices → Links → Container shapes → Text → Marker shapes (cross/checkmark LAST)

---

## UI / Branding Notes (Feb 2026)

### Left Toolbar
- **TEXT ACTIVE hidden**: `#text-mode-indicator` is hidden via CSS (user request). Tool mode indicators for Device/Shape/Link remain visible.
- **Shape Type Grid**: `.shape-type-grid` and `.shape-type-btn` provide scalable, aligned layout for the SHAPER section. Use `minmax(0, 1fr)` for responsive columns.
- **Section alignment**: Toolbar section headers use `min-height: 40px`, `gap: 8px`. Nested subsection headers use `min-height: 28px`. Device/link/font grids use `minmax(0, 1fr)` for equal column sizing.

### XRAY GUI Integration (Feb 2026, updated Mar 2026)

**Overview**: Links between two devices show a magnifying glass icon when selected. Clicking opens an XRAY Capture popup for DP/CP/DNAAS-DP traffic capture, with results delivered to Mac Wireshark.

**Key files:**
- `topology-xray-popup.js` — XRAY popup UI (liquid glass style, mode CP/DP (Arista)/DP (DNAAS), duration, direction, protocol filters, output, POV, SSH prompt when device has no SSH)
- `topology-link-toolbar.js` — Packet Capture button in the link toolbar (first button, only for device-to-device links)
- `topology-mouse-down.js` — Opens link toolbar on link click; calls `XrayPopup.temporaryHide()` when panning starts
- `topology-mouse-up.js` — Calls `XrayPopup.temporaryShow()` when panning ends
- `topology-toolbar-setup.js` — XRAY Settings section handlers (load/save config, Verify Mac)
- `index.html` — XRAY Settings section in left toolbar (Mac IP, user, password, Wireshark path, pcap dir)
- `serve.py` — `/api/xray/run`, `/api/xray/status/{id}`, `/api/xray/stop/{id}`, `/api/xray/config`, `/api/xray/verify-mac`
- `topology-link-details.js` — `autoFillFromLldp()` cross-references LLDP to auto-bind interfaces

**Data flow:**
1. Link selected between 2 devices -> Packet Capture button appears as first button in link toolbar
2. Click button -> `XrayPopup.show()` opens floating popup (positioned below link toolbar center, with notch)
3. If device has no SSH config -> SSH prompt (host, user, pass) shown; user must fill before Start
4. User picks mode/duration/direction/protocol filters/output/POV -> "Start Capture"
5. `POST /api/xray/run` with device, mode, interface, duration, output, direction, capture_filter, dut_host
6. Popup polls `GET /api/xray/status/{id}` for progress
7. Mac delivery: SCP pcap + SSH open Wireshark (credentials from `~/.xray_config.json`)

**Popup features:** Liquid glass styling (matches device/link toolbar), positioned below link toolbar with upward notch. Mode buttons: CP (Control Plane), DP (Arista), DP (DNAAS) with connectivity dots and inline hints when unavailable. Direction (Ingress/Egress/Both), Quick filters (BGP, OSPF, ISIS, LDP, LLDP, BFD multi-select), Exclude DNOS internal traffic (CP only), interface from link table or auto-detect, SSH prompt when device has no `sshConfig.host`. SSH credentials set in popup are stored on device and trigger `editor.saveState()`.

**Capture lifecycle:** Capture continues when popup is closed (toast on completion). Re-opening XRAY for same link while capture runs restores Stop/status UI. Panning (middle-mouse or space+drag) calls `temporaryHide()`; on pan end `temporaryShow()` repositions popup from link midpoint.

**Editor state:**
- `editor._xrayCapturing` — link ID with active capture (button turns orange)

**Settings:** Left toolbar Packet-Capture section (collapsible) — Mac IP, Mac user, Mac password, Wireshark path, pcap directory. Save writes via `POST /api/xray/config`. Verify Mac tests SSH via `POST /api/xray/verify-mac`.

### Brand Assets
- **LingoApp**: Official DriveNets brandbook is at https://www.lingoapp.com/110100/k/d5jKxQ — requires LingoApp login to download. Cannot be fetched programmatically.
- **Local branding**: Use `CURSOR/branding/` PDFs (fetched from Mac) for color/logo reference. Extracted logos in `branding/extracted/`.

### Brand Integration (DriveNets)
- **Logo**: Top-bar SVG in `index.html` — three horizontal capsule bars + diagonal slash (DriveNets symbol). Favicon: `branding/extracted/OUR_LOGO_p1_i5_180x180.png`.
- **Icon mapping** (SVG symbols in `index.html`):
  - `ico-router` — DriveNets Routers (rounded rect with 4 crossing arrows + arrowhead tips). Used: Device section header, context menus, Place Device.
  - `ico-dn-switch` — DriveNets Network Switch (rect with converging lines/arrows).
  - `ico-dn-chassis` — DriveNets Network Chassis (rect with vertical slots).
  - `ico-dn-cloud` — DriveNets Cloud (cloud outline).
  - `ico-dn-server` — DriveNets Server/Storage (stacked rack units with indicator dots + stand).
  - `ico-dn-tower` — DriveNets Cell Tower (tower with signal arcs).
  - `ico-dn-firewall` — DriveNets Firewall (shield with grid lines).
  - `ico-globe` — Wireframe globe. Used: curve mode "Use Global Setting".
  - `ico-discover` — Network Operations (cloud with nodes). Used: DNAAS discovery.
  - `ico-network` — Branch (building with peaked roof). Used: network-related UI.
- **Topologies button icon**: `#topo-btn-icon` — layer stack SVG updated dynamically by `FileOps._updateTopoBtnIcon()` to show domain colors on each layer.
- **Button active states**: DNAAS (`.dnaas-panel-open`), Network Mapper (`.nm-panel-open`), and Topologies (`.topologies-open`) buttons retain their base glass appearance with only a highlighted outline glow when open.
- **Topology indicator transitions**: `updateTopologyIndicator()` uses fade+slide animation when switching between topologies.
- **Extraction scripts**:
  - `branding/extract_images.py` — extract images from all brand PDFs.
  - `branding/extract_icon_svgs.py` — crop individual icon PNGs from Drivenets Icons PDF (grid crop) and export full-page SVGs for pages 2–3. Run: `python3 extract_icon_svgs.py`. Output: `branding/extracted/icons/` (300 PNGs), `branding/extracted/icons_page*_full.svg`.

### Backend API Reliability (Mar 2026)

**Request chain**: Browser JS -> serve.py:8080 (proxy) -> discovery_api.py:8765 -> NetworkMapperClient (SSE) -> MCP Server

**Improvements:**
- **LLDP proxy**: `topology-lldp-dialog.js` routes via `/api/dnaas/*` (relative URLs) so it works when deployed to h263; no direct port 8765 calls.
- **MCP session reuse**: `network_mapper_client.py` caches SSE sessions (120s TTL) to avoid 5s handshake per tool call.
- **MCP singleton**: `discovery_api.py` uses `_get_mcp_client()` instead of per-request `NetworkMapperClient()`.
- **MCP single-worker-task architecture (Mar 2026)**: Root-cause fix for the `RuntimeError: Attempted to exit cancel scope in a different task` crash. `NetworkMapperClient` now runs a single persistent asyncio Task on a dedicated daemon thread. All MCP calls from any thread are submitted to this worker via `asyncio.Queue`. The worker owns the SSE session exclusively -- context managers are always entered and exited in the same Task, which is what `anyio` requires. Old design used `ThreadPoolExecutor` + `asyncio.run()` per request, creating separate event loops and Tasks that triggered the cross-task crash during session cleanup/GC.
- **MCP auto-reset**: `_mcp_call()` wrapper in `discovery_api.py` retries with client reset on network failures. Now simplified since the root cause (cross-task SSE) is eliminated.
- **Health endpoint**: `GET /api/health` on discovery_api.py returns `{status, mcp_client, uptime_s}`. `serve.py` probes this on 502 to give the UI a specific error (API running but MCP broken vs API not responding).
- **Proxy retry**: `serve.py` uses 30s timeout for GET, 300s for POST; 1 retry with 2s backoff on connection errors; 502 includes endpoint and detail from health probe.
- **XRAY hint clarity**: XRAY popup distinguishes 502 (API down, shows detail from health probe) from network error (server not running) from LLDP-not-found (no neighbors).
- **Job cleanup**: `_nm_cleanup_old_jobs()` and `_cleanup_old_discovery_jobs()` remove completed jobs older than 30 minutes.
- **Error feedback**: LLDP dialog shows API/SSH/MCP-specific errors; Network Mapper shows toast after 3 poll failures; DNAAS distinguishes API-down vs SSH vs timeout.
- **CP direction BPF fix (Mar 2026)**: `cp_capture.py` now injects `outbound`/`inbound` BPF primitives into the filter expression when direction is egress/ingress. Previously direction was only used for analysis labeling, not filtering -- CP captures always grabbed both directions regardless of the panel setting.

### Service Orchestration (Mar 2026)

**serve.py as orchestrator**: When started, serve.py auto-launches `discovery_api.py` (port 8765) and `scaler_bridge.py` (port 8766) as child processes if not already running. A background monitor thread health-checks both every 15s and restarts on crash or after 3 consecutive health failures. Crash-loop protection: stops restarts if a service crashes 5+ times within 2 minutes.

**Auto-reload**:
- `scaler_bridge.py`: Started with uvicorn `--reload` — auto-restarts when its Python files change.
- `discovery_api.py`: Monitor thread checks mtime of `discovery_api.py`; if changed since last start, restarts the process.

**start.sh**: One-command launcher at project root. `./start.sh` kills any existing instances on 8080/8765/8766, optionally starts Network Mapper MCP if `~/network-mapper` exists, then runs `python3 serve.py`. `./start.sh --stop` stops all. `./start.sh --watch` monitors `serve.py` for changes and restarts the full stack when it changes.

**Health endpoint**: `GET /api/health` returns aggregated status: `{ serve, discovery_api, scaler_bridge }` with `status`, `port`, `pid`, `uptime_s` for managed services; `managed: false` when a service was already running before serve.py started.

### 503 Errors and Scaler Bridge Resilience (Mar 2026)

**Root causes of 503 on scaler_bridge-dependent endpoints** (`/api/config/*`, `/api/operations/*`, `/api/devices/{id}/test`):

| Cause | Source | Detail | Fix |
|-------|--------|--------|-----|
| Bridge not running | serve.py proxy | "Scaler bridge unavailable: Connection refused" | Auto-fixed: on-demand restart in proxy + monitor thread |
| Device resolution failed | scaler_bridge | "Could not resolve IP for 'X'. Set SSH address on canvas device." | Right-click device > Set SSH (IP or serial) |
| SSH failed | scaler_bridge | "SSH to X failed: ..." | Check credentials, network, device reachability |

**Root cause bugs fixed (Mar 10 2026):**
1. **Monitor ignored unmanaged services**: `_service_monitor()` wrapped health checks in `if proc is not None:` -- services not started by serve.py (or where startup returned None) were never monitored or restarted. Fixed: monitor always health-checks both services regardless of proc handle.
2. **Health endpoint reported "dead" not "down"**: When a managed proc died, `_handle_health()` reported `"status": "dead"` instead of probing the actual port. Frontend `checkHealth()` only checked for `=== 'ok'`, so "dead" was treated as down forever. Fixed: health endpoint now probes the port directly when proc is dead/absent.
3. **No on-demand restart**: When the proxy hit a connection error, it returned 503 and waited for the 15s monitor cycle. Fixed: proxy now attempts an on-demand bridge start on first failure, retries the request if startup succeeds.
4. **404 triggered false bridge-down**: `getLimits()` treated 404 (device not found) same as 503 (bridge down), putting the bridge in a 60s cooldown. Fixed: 404 returns default limits without touching bridge state.
5. **60s cooldown too long**: With auto-restart in place, bridge recovers in ~2s. Cooldown reduced from 60s to 15s.

**Auto-recovery mechanisms (serve.py):**
- **On-demand restart**: When a proxy request fails with connection error, serve.py starts the bridge immediately and retries the request (single retry).
- **Monitor thread**: Every 15s, checks if bridge proc is dead or health-check fails 3x in a row. Auto-restarts with crash-loop protection (max 5 restarts per 2min window).
- **Startup**: `_start_scaler_bridge()` checks if bridge is already responding before starting a new one. If it can't connect, starts uvicorn subprocess.

**Frontend resilience** (scaler-api.js):
- `_bridgeUp` / `_bridgeRetryAfter`: When 503 contains "Scaler bridge unavailable", skip requests for 15s and show friendly message.
- `testConnection`, `getJobs`, `getLimits`: Check bridge state before requesting; on cooldown, try `checkHealth()` to recover.
- `checkHealth()`: If `scaler_bridge.status === 'ok'`, resets `_bridgeUp` so subsequent requests proceed.

**Silent 503 paths** (topology-notifications.js): `/api/config/`, `/api/operations/`, `/api/devices/` — no toast for 503 (user sees error in ScalerGUI notification). Red console line is browser-built-in and cannot be suppressed.

**Debugging**: Run `curl http://localhost:8080/api/health` to see bridge status. If `scaler_bridge.status` is "down", check `journalctl --user -u topology-app.service` for startup errors.

### LLDP Animation & Dialog Fixes (Mar 2026)

**Root causes fixed:**
- **TB disappearing during LLDP enable**: `_drawCanvasWaveDots` and `_drawPulsingGlow` had no delegation in `topology.js` and used `editor` as a free variable. The TypeError crashed inside `ctx.save()` without `ctx.restore()`, corrupting canvas state and hiding all subsequent objects (TBs, text). Fixed by adding delegations and passing `editor` as first parameter.
- **No link animation**: Same root cause -- wave dots along connected links never rendered because `editor._drawCanvasWaveDots()` was undefined. Fixed with the delegation.
- **Table format inconsistency**: Initial LLDP load used 300+ lines of inline table HTML while refresh used `_buildLldpTableHtml`. These drifted apart (different grouping, colors, field name priorities). Fixed by unifying both paths through `updateLldpContent` -> `_buildLldpTableHtml`. Also added missing Port Mirror and Snake group support to `_buildLldpTableHtml`.
- **Safety**: Added try-catch around `_drawLldpEffects` in canvas drawing to prevent canvas corruption on future errors.

### Network Mapper (Mar 2026)

**Overview**: Recursive LLDP-based network discovery that auto-generates debug-dnos-quality topology diagrams from live devices. Supports up to 200 devices with hybrid hierarchical/force-directed auto-layout.

**Key files:**
- `topology-network-mapper.js` — Frontend module: panel UI, discovery control, hybrid layout, rich topology generation, save to domain
- `discovery_api.py` — Backend: `_nm_bfs_crawl()` BFS engine with DNAAS/canvas-aware resolution, MCP enrichment, `/api/network-mapper/start|status|stop` endpoints
- `serve.py` — Proxy `/api/network-mapper/*` to discovery_api.py

**Data flow:**
1. User opens Mapper panel (top-bar button or `N` key), enters seed device IP(s)
2. Frontend collects canvas devices with SSH config as `known_devices`
3. "Start Discovery" → `POST /api/network-mapper/start` with seeds, credentials, limits, known_devices
4. Backend resolves neighbors using known_devices first (DNAAS-aware), then DNS/SCALER DB/inventory
5. MCP path enriches with `get_device_system_info` + `get_device_interfaces_detail` (system_type, version, serial, interface speeds)
6. SSH path collects hostname, serial, system_type, DNOS version, LLDP, mgmt IP, interface brief
7. Frontend polls `GET /api/network-mapper/status?job_id=X` every 2s for live progress
8. On completion, "Generate Topology" creates debug-dnos-quality topology with:
   - Properly styled devices (visualStyle: classic/server/simple, role-based colors)
   - IP address labels below each device
   - System info panels above devices (system_type, version, serial)
   - Color-coded links by interface type (bundle-ether green, ge400 blue, hu400 orange)
   - Interface labels on-link in debug-dnos style
   - SSH config embedded for immediate SCALER use
9. "Save" stores to "Network Mapper" domain (auto-created section, color `#06b6d4`, icon `wifi`)

**Discovery sources (priority order):**
1. Canvas/DNAAS known devices — used for neighbor resolution and credentials
2. Network Mapper MCP (`get_device_lldp` + `get_device_system_info` + `get_device_interfaces_detail`) — enriched
3. SSH (`show system`, `show lldp neighbors`, `show interfaces management`, `show interfaces brief`) — full fallback
4. Device inventory / SCALER DB — for hostname-to-IP resolution

**Device classification (tier → visual):**
| Role | Tier | visualStyle | Color | Radius |
|------|------|-------------|-------|--------|
| NCM/superspine | 0 (top) | server | #c0392b | 50 |
| spine/NCC/RR | 0 (top) | server/classic | #9b59b6 | 50/40 |
| NCF/PE/router | 1 (mid) | classic | #3498db | 40 |
| CE/customer | 2 (bot) | simple | #2ecc71 | 30 |
| external/tester | 2 (bot) | server | #e67e22 | 30 |

**Link styling:**
| Interface | Color | Width | Style |
|-----------|-------|-------|-------|
| bundle-ether | #2ecc71 | 3 | solid |
| hu400/ce400 | #e67e22 | 2 | solid |
| ge400 | #85c1e9 | 2 | solid |
| mgmt | #95a5a6 | 1 | dashed |

**Auto-layout (hybrid):**
- Tier detection from `system_type` and hostname patterns
- If 2+ tiers: hierarchical Y by tier (250px spacing), force-directed X within tier
- If 1 tier: pure force-directed (repulsion + attraction + gravity, 500 max iterations)
- Minimum device spacing: 150px within tier, 180px in force-directed

**Editor state:**
- `editor.networkMapper` — NetworkMapperManager instance
- `editor.networkMapper._jobId` — active discovery job
- `editor.networkMapper._lastDiscoveryData` — latest discovery result (devices with interfaces, links)
- `editor.networkMapper._discoveryCredentials` — {username, password} used for SSH config on generated devices

**Panel UI:**
- Button: `#btn-network-mapper`, keyboard shortcut `N`
- Panel: `#network-mapper-panel` (liquid glass, cyan accent `#06b6d4`)
- Mutual exclusion with DNAAS panel and Topologies dropdown
- States: `.nm-panel-open`, `.nm-running` (spinning icon + pulse), `.nm-complete` (checkmark badge)

---

## Slash Command Knowledge Stores

For Cursor slash-command docs and learning stores in `~/.cursor/commands/`, `~/.cursor/*-reference/`,
`~/.cursor/*-docs/`, and `~/.cursor/skills/`:

- **Agent-facing knowledge should be tiered Markdown**:
  - `learned_index.md` = always-read compact summary (includes `Last synced:` timestamp)
  - `learned_rules.md` = detailed rules, read matching sections only
- **JSON remains the machine-compatible backing store** for tools and scripts. Do not break existing JSON readers unless you are also updating the tooling.
- **Staleness detection** (MANDATORY before reading any index):
  - Run `python3 ~/.cursor/tools/prune_learning.py --command <name> --check`
  - Exit code 0 = fresh, exit code 1 = stale (JSON is newer than mirror)
  - If stale, run `--sync-only` BEFORE trusting the index content
- **After any JSON write-back**, sync is MANDATORY (not optional):
  - `python3 ~/.cursor/tools/prune_learning.py --command <name> --sync-only`
  - Skipping this means subsequent reads use outdated rules
- **Auto-sync mode** for bulk operations:
  - `python3 ~/.cursor/tools/prune_learning.py --command all --auto-sync` syncs only stale stores
- **Backup-before-repair**: if a JSON file is malformed, the tool writes a `.bak` copy before
  attempting regex repair, then writes the repaired JSON back. No silent data loss.
- **Large methodology docs must be split** into:
  - a small TOC / quick-reference `SKILL.md` with a Learning Routing Table
  - targeted `sections/*.md` files loaded on demand
- **Command specs must follow the same reading protocol**:
  - always check freshness first (`--check`)
  - read the compact index / TOC
  - then load only the matching detail sections for the current mode or symptom
- **Self-learning has two paths**:
  - JSON-backed commands (BGP, XRAY, SPIRENT, HA, NETCONF): write to JSON, then MANDATORY sync
  - Direct-Markdown commands (/debug-dnos): edit the correct section file per the Learning Routing Table in SKILL.md

## DNOS CLI Syntax Corrections (Validated via MCP run_show_command on PE-4, 2026-03-09)

All commands below were tested live on YOR_CL_PE-4 (25.4.13.146_dev) using the Network Mapper
MCP `run_show_command` tool plus `search_cli_docs` for documentation cross-reference.

| Wrong (was in specs) | Correct (validated) | Files fixed |
|---|---|---|
| `show bgp ipv4 flowspec-vpn summary` | `show bgp ipv4 flowspec summary` | HA.md, BGP.md, debug-dnos.md, feature-ha-mapping.md, known-behaviors.md, learned_rules.md, route-injection.md, phase-procedures.md, debug-dnos.mdc |
| `show mpls lsp` | `show mpls route` or `show mpls forwarding-table` | HA.md, feature-ha-mapping.md, health-check.md |
| `show interfaces brief` | `show interfaces description` (Admin + Oper + Description) | HA.md, dnos-cli-discoveries.mdc |
| `show system process bgpd` | `show system process routing:bgpd` (container-prefixed) | HA.md, snapshots.md, cross-command-integration.mdc, dnos-cli-discoveries.mdc |
| `show system process isisd/fibmgrd` | `show system process routing:isisd` / `routing:fibmgrd` | Same as above |
| `show system process wb_agent ncp <id>` | `show system process wb_agent` (no `ncp` suffix -- shows all NCPs) | Same as above |
| `show system process interface-manager` | Not a valid name. Use `mgmt_interface_manager` or `ctrl_interface_agent` | Same as above |

**Process monitoring approach:** Process names in DNOS use container-prefixed syntax for
`show system process <name>` (e.g., `routing:bgpd`, `routing:fibmgrd`). The short names
(bgpd, isisd) are NOT valid arguments. Discover valid names via `search_cli_docs('show system process')`
or CLI `?` completion on device. Full process name list cached in
`~/.cursor/dnos-cli-completions.json`. Alternative: use container-scoped queries like
`show system ncc <id> container routing-engine` for all routing processes.

**CLI discovery protocol (search first, ask device second):**
1. `search_cli_docs(keyword)` -- PRIMARY. Searches 469+ DNOS commands. No SSH needed.
2. `get_cli_doc_section(doc_name, term)` -- full syntax details when search returns snippets.
3. `~/.cursor/dnos-cli-completions.json` -- cached dynamic values (process names, VRF names).
4. `run_show_command` on device -- only for uncached dynamic arguments.
Rule: `~/.cursor/rules/dnos-cli-completion-protocol.mdc`