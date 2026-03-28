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

### Cursor /XDN (unified topology + scaler context)

- **Skill:** `~/.cursor/skills/xdn-topology-mastery/` (`SKILL.md`, `architecture-reference.md`, `api-reference.md`, `bul-reference.md`, `editing-patterns.md`, `learning.md`).
- **Slash command:** `/XDN` in Cursor (also under repo `.cursor/commands/XDN.md` when using this workspace).
- **Learning:** `~/.topology_learning.json` -- after substantive topology/scaler sessions or `/XDN learn`, run `python3 ~/.cursor/tools/prune_learning.py --command xdn --sync-only` so `learned_index.md` stays current.

### Scaler Bridge API (scaler_bridge.py, port 8766)

The bridge wraps scaler-wizard modules for the topology app. serve.py proxies `/api/config/*`, `/api/operations/*`, `/api/devices/discover`, `/api/devices/{id}/test`, `/api/devices/{id}/context`, `/api/ssh/probe`, `/api/ssh/check-port`, `/api/ssh/discover-ncc-mgmt`, and related `/api/ssh/*` helpers to it.

**DNOS device communication (SSH):** Shared library `scaler/scaler/dnos_session.py` provides `DNOSSession` (prompt-based show commands, optional `SSHConnectionPool` reuse via `client=`, `config_mode` / `commit` / `send_config_set`). Bridge routes use `topology/routes/_device_comm.py` (`DeviceCommHelper`: `run_show`, `run_show_batch`, `fetch_running_config`, `get_session`). Optional `scaler/scaler/dnos_netmiko.py` wraps Netmiko `generic` for one-off commands. Raw WebSocket terminal, upgrade flows, and `connection_strategy.py` stay on paramiko as documented in the Netmiko integration plan.

**Terminal-to-GUI parity (documented in `~/.cursor/skills/xdn-topology-mastery/SKILL.md` section "Scaler: five-layer parity"; run `/XDN` in Cursor to load):** Every new API endpoint MUST have a corresponding `ScalerAPI.js` method and a scaler GUI entry point (see `scaler-gui*.js` bundles). No terminal-only or GUI-only features. Full chain: `config_builders.py` -> terminal wizard -> `scaler_bridge.py` -> `scaler-api.js` -> `scaler-gui.js` (+ domain modules as needed).

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
| `/api/config/delete-hierarchy-options` | GET | List hierarchies for Delete Hierarchy GUI (display, command, warning). |
| `/api/config/flowspec-dependency-check` | POST | FlowSpec dependency check. Body: `{ device_id, ssh_host }`. Returns `{ issues: [{ component, issue, severity, fix_command, fix_description }], passed }`. |
| `/api/config/scan-ips` | POST | Scan device config for used IPv4/IPv6. Body: `{ device_id, ssh_host, parent_interface?, ipv4_prefix?, ipv6_prefix?, count?, check_ipv4?, check_ipv6? }`. Returns `used_ips`, `suggestion`, `overlap_check` (when check params provided). Used by interface wizard IP collision detection. |
| `/api/config/push/estimate` | POST | Get push time estimates. Body: `{ config?, device_id?, ssh_host? }`. Returns estimates for terminal_paste, file_upload, lofd from timing_history.json. |
| `/api/operations/delete-hierarchy` | POST | Delete config hierarchy (dry_run). Body: `{ device_id, hierarchy, dry_run, ssh_host?, sub_path? }`. |
| `/api/operations/push` | POST | Push config. Body: `{ device_id, config, dry_run, push_method: "terminal_paste"|"file_upload", load_mode: "merge"|"override", ssh_host?, job_name? }`. Returns job_id. |
| `/api/config/push/progress/{job_id}` | GET | SSE stream for push progress (phase, percent, terminal lines, elapsed_seconds, estimated_remaining_seconds, done, success, awaiting_decision) |
| `/api/operations/{job_id}/cancel` | POST | Cancel push job (mid-paste abort or discard held). Sets _cancel_requested for running jobs; calls cancel_held_session for awaiting_decision. |
| `/api/operations/push/{job_id}/commit` | POST | Commit held config on same SSH session (after dry_run when check passed) |
| `/api/operations/push/{job_id}/cancel` | POST | Cancel held config (discard candidate) and close SSH session |
| `/api/operations/push/{job_id}/cleanup` | POST | Cleanup dirty candidate on device after failed commit check (connects fresh) |
| `/api/operations/jobs` | GET | List all jobs (active + recent history) |
| `/api/operations/jobs/{job_id}` | GET | Full job state including all terminal output |
| `/api/operations/jobs/{job_id}/retry` | POST | Re-submit same config. Returns new job_id. |
| `/api/operations/jobs/{job_id}` | DELETE | Remove job from history |
| `/api/config/limits/{device_id}` | GET | Platform limits (max_subifs) from limits.json |
| `/api/devices/discover` | POST | SSH discover device by IP, add to inventory |
| `/api/devices/{id}/resolve` | GET | Resolve device to mgmt_ip (scaler_bridge fallback when discovery_api down) |
| `/api/ssh/probe` | POST | Probe connection methods (TCP reachability). Body: `{ device_id, ssh_host? }`. Returns `{ methods, recommended, device_state }`. |
| `/api/ssh/discover-console` | POST | Discover console path via Zohar's CSV DB (primary, ~700 devices) or Device42 API (fallback). Body: `{ device_id, serial_number?, ssh_host? }`. Returns `{ console_server, port, pdu_entries, source, serial_no }`. Auto-saves to console_mappings.json. |
| `/api/ssh/pdu-power` | POST | PDU power action via Zohar's PDU mapping. Body: `{ serial_number?, device_id?, action: reboot\|off\|on\|status, pdu_host?, outlet? }`. Looks up PDU from Zohar's DB if host/outlet not given. |
| `/api/ssh-pool/evict` | POST | Evict pooled SSH client(s). Body: `{ ip, device_id? }`. Pool is keyed by mgmt IPv4; when `ip` is not dotted IPv4, optional `device_id` (canvas label) is used with `_resolve_mgmt_ip` to evict the resolved IP. Returns `evicted`, `evicted_keys`. |
| WebSocket `/api/terminal/ws` | WS | In-browser terminal. Params: `device_id`, `ssh_host`, `method`. Browser builds URL via `ScalerAPI.getBridgeWebSocketOrigin()` (honors `baseUrl` host/port; else page hostname :8766). Streams stdin/stdout via paramiko. |
| `/api/config/scan-existing` | POST | Scan device for existing sub-ids, VRFs, EVIs, L3 conflicts. Body: `{ device_id, ssh_host, scan_type: "interfaces"\|"services"\|"vrfs"\|"all" }`. Returns `existing_sub_ids`, `l3_conflicts`, `l2_sub_ids`, `outer_inner_map` (QinQ), `sub_id_details`, `next_free`, `config_fetched_at`. Used by interface wizard collision check and encap overlap detection. |
| `/api/config/detect-pattern` | POST | Detect interface pattern (dot1q/qinq, stepping_tag, last_vlan, last_sub_id, suggested_next_vlan) from device config. Body: `{ device_id, ssh_host, parent_interface }`. Used for auto-fill in subif flow. |
| `/api/mirror/analyze` | POST | Analyze source vs target config for mirror. Body: `{ source_device_id, target_device_id, ssh_hosts?: [src_ip, tgt_ip], lldp_neighbors?: [] }`. Returns `source_summary`, `target_summary`, `smart_diff`, `interface_map`, `smart_suggestions` (bgp_neighbors, wan_ips, service_ips, lldp_mapping). |
| `/api/mirror/generate` | POST | Generate mirrored config. Body: `{ source_device_id, target_device_id, ssh_hosts, interface_map, ip_mapping?: { source_ip: target_ip }, section_selection?, section_actions?, output_mode: "full"\|"diff_only" }`. Returns `config`, `summary`, `line_count`, `diff_stats`. |
| `/api/mirror/preview-diff` | POST | Preview diff of proposed mirrored config vs target running. Body: `{ target_device_id, config, ssh_host }`. Returns `diff_text`, `lines_added`, `lines_removed`. |
| `/api/operations/image-upgrade/branches` | POST | List dev/release branches from Jenkins. Body: `{ type: "dev"|"release"|"all" }`. Returns `{ branches: [{name, url}], type }`. |
| `/api/operations/image-upgrade/branch-switch` | POST | Detect branch switch (e.g. dev_v25 -> dev_v26). Body: `{ current_version, target_version }`. Returns `{ is_switch, current_branch, target_branch, requires_delete_deploy }`. |
| `/api/operations/image-upgrade/compat` | POST | Version compatibility report. Body: `{ source_version, target_version, config_text? }`. Returns `{ severity, incompatible_count, recommendation, ... }`. |
| `/api/operations/image-upgrade/builds` | POST | List recent builds with image artifacts for a branch. Body: `{ branch, limit?, max_results?, include_failed? }`. When `include_failed=false` (default), only SUCCESS builds. When `include_failed=true`, includes FAILED builds with valid DNOS/GI/BaseOS artifacts. Returns `{ branch, builds: [...] }`. |
| `/api/operations/image-upgrade/resolve-url` | POST | Resolve Jenkins URL to build info. Body: `{ url }`. Returns `{ branch, build_number, dnos_url, gi_url, baseos_url, is_sanitizer, is_expired, result }`. |
| `/api/operations/image-upgrade/stack` | POST | Get stack URLs for branch + build. Body: `{ branch, build_number }`. Returns `{ dnos_url, gi_url, baseos_url, is_sanitizer, is_expired }`. |
| `/api/operations/image-upgrade/plan` | POST | Per-device upgrade plan. Body: `{ device_ids, ssh_hosts, target_branch?, target_build_number?, target_version?, dnos_url? }`. SSHs to each device, detects mode (DNOS/GI/RECOVERY), current version, upgrade_type (normal/delete_deploy/gi_deploy/blocked). Returns `{ devices: { id: { mode, current_version, target_version, upgrade_type, reason, warnings, components } } }`. |
| `/api/operations/image-upgrade` | POST | Execute image upgrade. Body: `{ device_ids, ssh_hosts, branch, build_number, components, upgrade_type, device_plans?, max_concurrent?, dnos_url, gi_url, baseos_url, ... }`. Supports per-device plans and parallel execution (ThreadPoolExecutor). Returns `{ job_id }`. |
| `/api/config/{device_id}/save` | POST | Save generated config for later push. Body: `{ config }`. Writes to device config dir as wizard_*.txt. |
| `/api/config/generate/undo` | POST | Generate undo config from pushed config. Body: `{ config_text }` or `{ job_id }`. Returns `{ config }`. |
| `/api/operations/image-upgrade/build-status/{job_id}` | GET | Poll build status. Query `?latest=true` for lastBuild (trigger monitoring). |
| `/api/operations/image-upgrade/build-log/{branch}` | GET | Get Jenkins console log. Query `?build_number=N` (optional). |

**Config generation**: All `generate/*` endpoints use `scaler.wizard.config_builders` (pure DNOS generators). No frontend DNOS string construction. GUI previews always call backend API with full params. The terminal wizard (`interactive_scale.py`) also calls `config_builders.build_from_expansion()` for config generation, ensuring terminal and GUI produce identical DNOS output.

**Sub-interface-only policy**: Both CLI and GUI wizards only create sub-interfaces on existing physical/bundle parents. Physical interface creation is not supported (hardware-defined). Legacy types (bundle, ph, irb, loopback) are retained in `config_builders.py` for backward compatibility but are not exposed in any menu or wizard.

**Config push**: `POST /api/operations/push` uses `ConfigPusher` from scaler. Progress streamed via SSE at `GET /api/config/push/progress/{job_id}`. The SSE stream includes `terminal` (new SSH output lines since last poll) via `live_output_callback` piped from ConfigPusher. ScalerAPI.connectPushProgress uses EventSource for real-time progress and terminal streaming. For upgrade jobs, SSE also includes `device_state` (per-device status, phase, percent, error); `onDeviceState` callback renders per-device progress rows.

**Push methods**: `push_method` (terminal_paste | file_upload) and `load_mode` (merge | override). Terminal paste: SSH paste + commit. File upload: SCP to /config/ + `load merge` or `load override` + commit. Best for large configs.

**Cancel button**: High-visibility (white text, X icon). During paste: `POST /api/operations/{job_id}/cancel` sets _cancel_requested; paste loop aborts, sends `cancel`+`exit` on device to discard candidate. During held state: same endpoint calls cancel_held_session. Candidate config is always cleaned on device.

**Hold-and-commit flow** (dry_run): When `dry_run=true`, backend uses `push_config_terminal_check_and_hold()` which pastes config, runs commit check, and keeps SSH session alive. Job enters `awaiting_decision` state. Frontend shows Commit Now / Cancel (discard) buttons in the progress panel. User clicks Commit -> `POST /api/operations/push/{job_id}/commit` sends commit on same session. User clicks Cancel -> `POST /api/operations/push/{job_id}/cancel` sends cancel+exit. No second push job. When commit check fails, Cleanup button calls `POST /api/operations/push/{job_id}/cleanup` to connect fresh and run cancel on device.

**Timing learning**: On push completion, `save_timing_record()` writes to `scaler/db/timing_history.json`. `get_accurate_push_estimates()` uses this for per-method estimates. SSE stream includes `elapsed_seconds` and `estimated_remaining_seconds`.

**IP awareness**: `scan_used_ips()` and `suggest_next_ip_range()` in config_builders.py. Interface wizard IP step calls `ScalerAPI.scanIPs()` for used IPs and overlap check. Collision banner + "Use suggested" button (like VLAN encap).

**Running Commits Panel**: `ScalerGUI.openCommitsPanel()` opens a persistent panel that polls `GET /api/operations/jobs` every 2s. Shows job cards with status dot (gray=pending, cyan=running, green=completed, red=failed), progress bar, and expand/minimize. Expanded cards show a live terminal view with SSH output. For upgrade jobs, per-device rows (device_state) shown above terminal. Error lines highlighted red; DNOS errors parsed with `suggestErrorFix()` (patterns: "already exists", "limit exceeded", "Hook failed"). Retry button re-submits via `POST /api/operations/jobs/{job_id}/retry`. Accessible via "Commits" button in Scaler CONFIG menu with active-job badge. Job history persisted to `~/.scaler_push_history.json` (max 50 jobs, terminal truncated to 200 lines on completion).

**Push parity**: All wizards (Interface, Service, VRF, Bridge Domain, FlowSpec, Routing Policy, BGP, IGP) share the same push flow: Review step (generates config, shows preview, validation, optional diff) -> Push step (dry_run / merge / replace / clipboard+SSH). All route through `ScalerAPI.pushConfig()` -> `ScalerGUI.showProgress()` -> commits panel. `ssh_host` is included in all push calls from `deviceContext.mgmt_ip`.

**Wizard Run History** (Phase 2): `recordWizardChange(deviceId, changeType, details, options)` stores full run records with `generatedConfig`, `params`, `pushMode`, `jobId`, `success`. Persisted to `localStorage` key `scaler_wizard_history` (max 100 entries). `updateWizardRunResult(jobId, success)` updates history when push completes. Per-wizard "Last Run" card shows at top of each wizard when history exists for that wizard+device. Global "Wizard Run History" panel in CONFIG menu shows chronological list grouped by date. "Re-run with same params" pre-fills wizard; "Re-run on different device" opens Mirror Wizard with source=history device, target=user-selected device.

**Re-run on different device** (Phase 4c): Both per-wizard Last Run card and global History panel wire "Re-run on different device" to `openMirrorWizard(sourceId)`. User selects target device; Mirror Wizard runs analyze -> generate -> diff vs target -> push. Uses ConfigMirror from `mirror_config.py` for device-agnostic config adaptation.

**Mirror Config Wizard**: `openMirrorWizard(prefillSourceId?, prefillTargetId?)` uses WizardController with 4 steps: (1) Devices -- source + target dropdowns, (2) Smart Mapping -- auto-runs `ScalerAPI.mirrorAnalyze()`, shows editable tables for interface mapping, BGP neighbor IPs, WAN IPs, service IPs, LLDP mapping from `smart_suggestions`, (3) Analyze -- stat cards (add/modify/delete/identical) and per-section action selects (keep/edit/skip/delete), (4) Review -- auto-generates config via `mirrorGenerate()` with `ip_mapping`, shows preview + optional diff toggle via `mirrorPreviewDiff()`. Push on complete via `ScalerAPI.pushConfig()`. When prefilled, device dropdowns are pre-selected. **WizardController fix**: `renderNavigation()` uses `nav.querySelector()` instead of `document.getElementById()` to bind Next/Back/Skip, avoiding stale panel button binding when multiple wizards exist in DOM.

**Multihoming ESI Wizard**: `openMultihomingWizard()` uses WizardController with 3 steps: (1) Device Pair -- checkbox select exactly 2, ESI prefix input, redundancy mode (single-active/all-active), RT matching toggle, (2) Compare -- auto-runs `ScalerAPI.compareMultihoming()`, shows matching/device1-only/device2-only stat cards with re-compare button, (3) Sync -- review summary with key-value rows, push via `ScalerAPI.syncMultihoming()`. Backend uses correct DNOS format (`esi arbitrary value {value}`).

**Collision check** (Phase 3b): Interface wizard encap step and review step, when `interfaceType === 'subif'` and parent exists, call `ScalerAPI.scanExisting()`. Encap step shows early overlap banner with Continue/Skip/Override. Review step shows final safety-net warning. Options: Skip conflicts (passes `skip_vlans` to generate), Start after existing (auto-sets vlanStart), Override. `config_builders.build_interface_config` accepts `skip_vlans` to skip conflicting VLAN IDs during generation (terminal-style vlan_offset).

**Reusable step components** (Phase 4A): `ScalerGUI._buildPushStep(opts)` returns a Push step with configurable `radioName`, `includeClipboard`, `infoText`. `_buildDecisionStep(opts)` returns a Decision step (Save for Later / Push Config / Next Section) with `wizardType` and `getCreatedData`. `_buildReviewStep(opts)`, `_buildInterfaceSelector(opts)`, `_buildAddressFamilySelector(opts)` provide shared HTML/collectData for wizard steps. Interface, BGP, IGP wizards insert Decision step before Push. VRF, Bridge Domain, FlowSpec, Routing Policy, and Service wizards use `_buildPushStep`.

**Config Push Quality Fixes** (2026): (1) **API baseUrl**: All `fetch('/api/...')` in scaler-api.js use `ScalerAPI._api(path)` for remote server access. (2) **Time-based progress**: config_pusher.py progress percentages are phase-time-proportional (connect, paste, commit-check, commit) with 2s tick during long phases. (3) **QinQ naming**: build_interface_config uses inner VLAN as sub-if suffix when outer_step=0. (4) **Undo config**: `build_undo_config()` parses pushed config and emits delete commands; Undo button in push result dialog. (5) **Save for Later**: `POST /api/config/{device_id}/save` stores config to device dir; Decision step "Save for Later" option.

**Scaler menu order** (Phase 4C): Configuration Wizards: Interface, Service, VRF, Bridge Domain, BGP, IGP, FlowSpec, Routing Policy, Multihoming (matches terminal wizard hierarchy order).

**Scaler GUI Overhaul** (2026): Upgrade, Scale, and Multihoming wizards use topology canvas devices only (`_getWizardDeviceList()`). `window.ScalerGUI` is set so the device toolbar "Upgrade Stack" button can call `openUpgradeWizard()`. `_getWizardDeviceList` returns `ssh_host` for fast backend resolution. Upgrade wizard: 5-step WizardController (Devices, Source, Build, Compare, Execute) with branch browse, Jenkins URL, version comparison, branch-switch detection, compatibility report. Scale wizard: 3-step (Devices, Scale, Review) with scale suggestions in header. Multihoming wizard: 3-step (Device Pair, Compare, Sync). All multi-device wizards have context panels with Refresh and stale indicator (>5 min). Wired APIs: `wizardSuggestions` (What's Next), `detectBGPNeighbors` (BGP wizard), `detectScaleSuggestions` (Scale wizard), `validatePolicy` (Routing Policy), `getSmartDefaults` (BGP prefill).

**Upgrade wizard instant load** (Mar 2026): Eliminated the blocking `getDeviceContext()` loop that fetched full device context (config, interfaces, VRFs, etc.) over SSH for each device. The upgrade wizard only needs stack versions and mode, which DeviceMonitor already caches as `device._stackData`. New flow: (1) Wizard opens instantly using `_stackData` from DeviceMonitor cache + ScalerGUI `_deviceContexts` cache. `deviceStatus` is pre-populated from `_parseStackVersions(_stackData.components)`. (2) Phase 1 background: `getUpgradeDeviceStatus(ids, sshHosts, cachedOnly=true)` reads from `operational.json` server-side (~10ms/device, no SSH) to fill in mode and validate versions. (3) Phase 2 background: `getUpgradeDeviceStatus(ids, sshHosts, false)` does live SSH for definitive mode + install status. Refresh button unchanged (full SSH). Backend: `GET /api/operations/image-upgrade/device-status?cached_only=true` reads `operational.json` stack_components, dnos_url, device_state -- no SSH connection. Result: wizard opens in <200ms vs previous 10+ seconds blocking.

**Cross-wizard dependency warnings** (Phase 4D): `_getWizardDependencyWarnings(wizardType, data)` returns context-based warnings (e.g. VRF needs sub-interfaces, FlowSpec name conflict, Multihoming ESI). `_renderDependencyWarnings(warnings)` displays them. VRF Interface Attachment step shows when no sub-interfaces exist.

**Validation**: Review steps call `ScalerAPI.validateConfig({ config, hierarchy })` after generating config. Errors and warnings displayed in `scaler-validation-box`. Uses `CLIValidator.validate_generated_config()` (syntax, scale limits, interface order).

**Diff preview**: Interface wizard Review step has "Show diff vs running" button. Calls `ScalerAPI.previewConfigDiff(deviceId, config, sshHost)` to show proposed-vs-running unified diff.

**Platform limits**: The sub-interfaces step validates total count against `GET /api/config/limits/{device_id}` (sources `limits.json` vlan_pool max_capacity, default 20480). Warning shown if `count * subifCount > max_subifs`.

ScalerAPI (scaler-api.js) methods: getDevices, getDevice, getDeviceContext, testConnection, syncDevice, syncConfig, generateInterfaces, generateServices, generateBGP, generateIGP, batchGenerate, previewConfigDiff, validateConfig, compareConfigs, getConfigDiff, getInterfaces, getTemplates, generateTemplate, discoverDevice, getDeleteHierarchyOptions, deleteHierarchyOp, flowspecDependencyCheck, getPushEstimate, pushConfig, commitHeldJob, cancelHeldJob, cancelOperation, cleanupHeldJob, connectPushProgress (supports onDeviceState for upgrade jobs), getJobs, getJob, retryJob, deleteJob, getLimits, scanExisting, scanIPs, detectPattern, mirrorAnalyze, mirrorGenerate, mirrorPreviewDiff, getBuildsForBranch, resolveJenkinsUrl, getBuildStack, getUpgradePlan, imageUpgrade (accepts device_plans, max_concurrent).

### Smart Wizard Suggestions (DeviceContextCache)

Wizards (Interface, Service, VRF, BGP, IGP) use a cached-then-live device context for smart suggestions:

- **Device resolution by SSH**: Canvas labels are NOT backend device IDs. Resolution uses `sshConfig.host` (which may be an IP, hostname, or serial number) as the primary key. `_resolveDeviceId(label)` extracts SSH credentials from the canvas device object. `ScalerAPI.getDeviceContext(deviceId, live, sshHost)` passes `ssh_host` to the backend.
- **Central IP resolution** (`_resolve_mgmt_ip(device_id, ssh_host)` in `scaler_bridge.py`): ALL endpoints use this single function. Uses cached `_build_scaler_ops_index()` (60s TTL) that indexes all `operational.json` files by serial, hostname, mgmt_ip, and dir name. Chain: 1) `ssh_host` is IP -> direct match in index; 2) `ssh_host` is serial/hostname -> match in index; 3) `device_id` exact match in index; 4) discovery API `_resolve_device`; 5) `device_inventory.json` fuzzy match; 6) partial name match (e.g. `PE-1` matches `YOR_PE-1`). Returns `(mgmt_ip, scaler_device_id, resolved_via)`. Results cached for 120s in `_resolve_cache`. Raises 503 if all fail.
- **NEVER add `_resolve_device()` calls directly in endpoints** -- always use `_resolve_mgmt_ip`. The discovery API frequently returns empty `mgmt_ip`; the central function handles all fallbacks.
- **Context builder** (`_get_device_context`): Uses `_resolve_mgmt_ip` first, then tries `_get_cached_config(scaler_device_id)`. Falls back to `_get_cached_config(device_id)` and `_get_cached_config(hostname)`. Reads stack and git_commit from `operational.json`. When `live=True` and stack/git_commit are missing, fetches via SSH (`show system stack | no-more`, `run start shell` + `cat .gitcommit`) and writes back to operational.json for caching. Returns `resolved_ip` field so frontend shows the actual IP.
- **DeviceContextCache**: `ScalerGUI.getDeviceContext(deviceId)` returns cached context if fresh (<60s), else fetches. `refreshDeviceContextLive(deviceId)` fetches live and updates cache. `invalidateDeviceContext(deviceId)` clears cache.
- **Instant wizard loading**: All wizards (Interface, Service, VRF, BGP, IGP) open instantly with cached data. If no fresh cache exists, the wizard renders immediately with a "Loading..." state, then fetches context in the background and re-renders when ready.
- **Cross-wizard awareness**: `recordWizardChange(deviceId, changeType, details)` logs wizard changes to `_wizardChangeLog`. `getDeviceContext()` merges pending changes into the returned context so the next wizard sees updated free interfaces, next EVI/bundle numbers, etc. Changes persist for 5 minutes. Devices with pending changes show a "changed" badge in the device selector.
- **Context panel**: Collapsible panel at top of each wizard. Compact visual bar for interface counts (phys, bundle, lo, sub-if), LLDP chips with neighbor tooltips, color-coded status (green=has data, orange=partial, red=no SSH). System line: `System | AS | RID`. "Refresh Live" fetches over SSH.

### VRF / L3VPN Wizard (5 Steps)

The VRF wizard creates L3VPN VRF instances via `build_service_config(service_type='vrf')` which delegates to `_generate_vrf_config` from interactive_scale. Steps: VRF Naming (prefix, start, count, description) -> Interface Attachment (optional, sub-interfaces from context) -> BGP & Route Targets (enable BGP, AS, router-id, RT mode same_as_rd/custom) -> Review (config preview, validation) -> Push. Uses `POST /api/config/generate/services` with `service_type: 'vrf'` and params: `attach_interfaces`, `interface_list`, `interfaces_per_vrf`, `enable_bgp`, `bgp_config`, `rt_config`.
- **DNAAS device handling**: DNAAS devices (NCM/NCF/NCC/LEAF/SPINE) are excluded from wizard device selectors. If a DNAAS device does appear in a wizard, LLDP suggestions are disabled (`ctx._isDnaas = true`).
- **Suggestion chips**: `ScalerGUI.renderSuggestionChips(items, { type, onSelect })` renders clickable chips. Types: `lldp` (cyan), `free` (green), `config` (orange), `smart` (purple). Items may have `target` for routing onSelect (e.g. `target: 'evi'` or `target: 'asn'`). Bundle member chips use toggle mode: click to add/remove, `.chip-selected` for selected state.

### Interface Wizard Architecture (7 Steps)

The Interface Wizard creates sub-interfaces on existing physical/bundle parent interfaces. Only `subif` type is exposed in CLI and GUI (physical interface creation is not supported -- they are hardware-defined). Steps use `stepBuilder` for dynamic composition:

| Type | Steps (in order) | Count |
|------|-------------------|-------|
| **Sub-interface** | Type → Parent Selection → Mode & Features → Encap → Review → Decision → Push | 7 |
| **GE100/GE400/GE10** | Type → Location → Mode & Features → Encap → Review → Push | 6 |

When the user changes the type in Step 0 and clicks Next, the WizardController calls `stepBuilder(data)` to recompose the step array, dependencies, and keys. The step indicator re-renders with only the relevant dots.

**Mode & Features step** (sub-interface): Interface Mode selector (L2 vs L3). L2 mode: l2-service enabled, hides IP/L3 features. L3 mode: IP addressing (IPv4/IPv6/dual, multiple step modes), MPLS, Flowspec, BFD, MTU, Description.

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
| `topology-clipboard-utils.js` | (IIFE) | `window.safeClipboardWrite` | Safe clipboard for HTTP (non-secure) contexts; use instead of `navigator.clipboard` when app is accessed via server IP |
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
| `topology-device-monitor.js` | `window.DeviceMonitor` | Background poll: immediate _tick(false) on init (disk cache), then 5-min _tick(true) (live SSH); populates _stackData, _lldpData, _gitCommit; active NCC resolution for clusters; fires device:context-updated |
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

#### Scaler GUI (modular bundles, 2026-03-23)

The scaler UI is split from the former monolith (`scaler-gui.js.bak` backup). **Core** defines `const ScalerGUI = { ... }` and assigns `window.ScalerGUI`; extension scripts call `Object.assign(window.ScalerGUI, { ... })` inside an IIFE. **`scaler-gui-init.js`** runs last and registers `DOMContentLoaded` -> `ScalerGUI.init()`.

| Script (load order) | Role |
|----------------------|------|
| `scaler-gui.js` | State, shared utilities, `WizardController`, device-context cache + shared step builders (`_buildPushStep`, `_buildDecisionStep`, ...), panels, main menu, `handleMenuAction`, `showNotification`, `escapeHtml` |
| `scaler-gui-history.js` | Wizard run history panel, commits panel |
| `scaler-gui-devices.js` | Canvas device list helpers (`_getWizardDeviceList`, ...), device manager, device selector, sync-all, quick-load, compare/sync/delete/batch/templates/add-device |
| `scaler-gui-wizards-network.js` | Interface, service, VRF, bridge-domain, multihoming wizards |
| `scaler-gui-wizards-routing.js` | Routing policy, BGP, IGP wizards |
| `scaler-gui-wizards-security.js` | XRAY settings, FlowSpec, FlowSpec VPN, system config, mirror wizards |
| `scaler-gui-progress.js` | `showProgress` (WebSocket job UI), `_analyzeCommitError` |
| `scaler-gui-upgrade.js` | Upgrade failure/active banners, `_checkRunningUpgrades`, image upgrade / scale / stag wizards, `ScalerAPI.imageUpgrade` / `stagCheck` / `scaleUpDown` patches |
| `scaler-gui-init.js` | `DOMContentLoaded` -> `ScalerGUI.init()` |

**Load order matters**: `scaler-gui-progress.js` must load before `scaler-gui-upgrade.js` because `init()` calls `_checkRunningUpgrades()` which uses `showProgress`. Wizard bundles: `wizards-network` then `wizards-routing` then `wizards-security` (all extend `window.ScalerGUI`).

#### Scaler bridge backend (FastAPI routers, 2026-03-23)

`topology/scaler_bridge.py` is a thin app factory; route handlers live under `topology/routes/`:

| Module | Role |
|--------|------|
| `routes/bridge_helpers.py` | Shared helpers (device resolution, SSH, config summaries, push job persistence, device context for wizards) |
| `routes/_state.py` | `_push_jobs`, `_push_jobs_lock` |
| `routes/ssh.py` | `/api/ssh*`, `/api/ssh-pool/*`, WebSocket `/api/terminal/ws` |
| `routes/config.py` | `/api/config/*`, `/api/mirror/*`, delete-hierarchy options |
| `routes/operations.py` | validate, push, jobs, multihoming, stag, scale |
| `routes/upgrade.py` | `/api/operations/image-upgrade/*`, cancel job, startup recovery (`_recover_active_*`) |
| `routes/devices.py` | `/api/devices/*`, `/api/wizard/suggestions` |
| `routes/operations_stub.py` | Catch-all 501 for unimplemented `/api/operations/*` (mounted **last**) |

Regenerate from monolith backup: `python3 topology/scripts/split_scaler_bridge.py` (reads `scaler_bridge.py.bak_split` or `scaler_bridge.py`).

**Regenerate splits** (after editing `scaler-gui.js.bak`): `python3 topology/scripts/split_scaler_gui.py` (writes `scaler-gui.js` and the bundle files).

**Adding a new wizard**: implement `openFooWizard` on `ScalerGUI` in the appropriate bundle (or `scaler-gui-wizards-<domain>.js`), add a `data-action` / `handleMenuAction` entry in core, and bump `?v=` in `index.html` for every touched JS/CSS file.

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
| Shape | `showShapeSelectionToolbar(shape)` | `shape-selection-toolbar` | Left-click to select |

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

**Device Toolbar Options:** SSH, Rename, Color, Style, Duplicate, Lock, Layer, Delete
- SSH → Click: always opens SSH dialog (`showSSHAddressDialog`) for credentials, probe methods, and settings. The small terminal button drawn on the canvas device (top-left when selected) calls `openTerminalToDevice(device)` for direct iTerm connect.
- Rename → `showRenamePopup(device)`
- Color → `showColorPalettePopup(device, 'device')`
- Style → `showDeviceStylePalette(device)`
- Duplicate → `duplicateSelected()`
- Lock → toggle `device.locked`
- Layer → Layer widget (down/up arrows, badge with dropdown: Bring to Front, Move Forward, Move Backward, Send to Back, Reset to Default). Uses `editor.getObjectLayer`, `editor.moveObjectForward/Backward`, `editor.moveObjectToFront/ToBack`, `editor.resetObjectLayer`. Same widget in device, link, shape, text toolbars.
- Delete → `deleteSelected()`

**Device Toolbar Tables (LLDP, Stack, Git Commit) and DeviceMonitor (Mar 2026)**

Device toolbar submenu (Stack button) opens LLDP Table, Stack Table, and Git Commit. All use cache-first open for instant display when data exists on the device object.

- **Cache-first open**: Stack dialog checks `device._stackData`; LLDP checks `device._lldpData`; Git Commit checks `device._gitCommit`. If present, render immediately with timestamp (no toast). "Refresh" fetches fresh data via fallback chain (cache first, then SSH). Refresh button toasts: success only; errors toast on load failure.
- **DeviceMonitor** (`topology-device-monitor.js`): Singleton that polls all canvas devices with SSH credentials. On init: runs `_tick(false)` after 2s delay (reads from operational.json, ~50ms/device). Then every 5 min: `_tick(true)` (live SSH via `ScalerAPI.getDeviceContext`). Stores results on `device._stackData`, `device._lldpData`, `device._gitCommit` with timestamps. For cluster devices (subType cluster, nccN pattern): uses `_resolveActiveNcc(device)` via `DnaasHelpers._findActiveNcc` to target active NCC IP. Batches: 5 devices concurrent, 2s delay between batches (scales to 1000+ devices). Fires `device:context-updated` CustomEvent so open dialogs auto-refresh.
- **AbortController**: Stack and LLDP dialogs use `AbortController` when switching devices; in-flight fetches are aborted to avoid stale data.
- **Git Commit**: Cursor-style code-block popup with SVG copy icon (#ico-copy), checkmark feedback on copy, `safeClipboardWrite`. Handles 502 with "Discovery API unavailable". Caches `device._gitCommit` and `device._gitCommitFetchedAt`.
- **serve.py**: `/api/dnaas/device-gitcommit` proxy timeout 15s (was 300s). Startup health check logs discovery_api and scaler_bridge reachability. 502 responses include upstream path in detail.
- **topology-notifications.js**: `_FRIENDLY_502_EXACT` includes `/api/dnaas/device-gitcommit` so 502 from this endpoint does not show raw error toast (caller shows friendly message).

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

## Recent Fixes (Jan 2026)

### SSH Dialog UX Overhaul (Mar 2026)
**Problem**: SSH dialog had broken Discover Console (display-only), connection methods hidden behind Auto-Switch, Open in-browser terminal ignoring selected method, Virsh Console only copying command, password in toasts, recovery modal calling non-existent `openSshDialog`.
**Fix**: Redesigned `topology-ssh-dialog.js`: compact credential row, methods section always visible with auto-probe on open and debounced re-probe on host change. Per-method Connect buttons open external terminal directly. Discover Console results inject clickable method rows with Connect. Removed Auto-Switch checkbox and in-browser terminal button. Toolbar SSH button: click=connect if configured, right-click=settings. Recovery modal fixed to call `showSSHAddressDialog`. Removed password from toasts; replaced emojis with [OK]/[WARN]/[INFO] prefixes.
**Files**: topology-ssh-dialog.js, topology-object-detection.js, topology-device-toolbar.js, index.html.

**Fast-connect always-probe (Mar 2026):** The toolbar SSH button (`openTerminalToDevice`) always probes via `ScalerAPI.probeConnection()` before connecting -- no `autoSwitch` flag required. The probe auto-discovers the best method and updates `sshConfig.host` if the saved host is stale. For non-cluster devices it prefers a reachable IP-based method (for iTerm), falling back to serial/hostname (web terminal). For clusters it auto-selects `virsh_console` with KVM credentials and the running NCC VM. The saved `sshConfig.host` is persisted when the probe finds a different reachable IP, so subsequent connections go to the correct address.

**Cursor /XDN deep reference (Mar 2026):** For agents, full SSH-GUI flow (probe method keys, IPv4 vs non-IP connect split, WebSocket origin, cluster NCP vs NCC console, pool eviction, troubleshooting) lives in `~/.cursor/skills/xdn-topology-mastery/ssh-reference.md`. Load with `/XDN ssh` or read `SKILL.md` section 7 in that folder.

**SSH pool evict + terminal WS (Mar 2026):** `POST /api/ssh-pool/evict` accepts optional `device_id` and resolves non-IPv4 `ip` to mgmt IP before evicting. `ScalerAPI.evictSSHPoolConnection(ip, deviceId)` and SSH dialog save / device delete pass the canvas label. `ScalerAPI.getBridgeWebSocketOrigin()` + `topology-terminal.js` align WebSocket with `ScalerAPI.baseUrl` for remote-bridge setups.

**Web terminal multi-tab (Mar 2026):** `window.TerminalPanel` manages multiple sessions in one bottom panel. VS Code-style tab strip (scrollable): each tab has status dot, device label, method badge, and close (X). `TerminalPanel.open(opts)` dedupes by tab key (`deviceId|method|host` or virsh `deviceId|method|kvmHost|ncc`). Same key focuses existing tab; new key adds a tab. Per-tab: xterm instance, WebSocket, heartbeat, SearchAddon. Shared: font size (localStorage), panel height, drag-resize. Minimize collapses to tab strip + toolbar only (tabs stay clickable). Context menu: Close Tab, Close Other Tabs, Reconnect Tab. Panel X closes all tabs.

**Terminal reliability (Mar 2026):** Auto-reconnect on abnormal WebSocket close with exponential backoff (1s, 2s, 4s, max 3 attempts). Server-initiated close ('eof'/'closed' message) sets `_noAutoReconnect` to prevent reconnect loops. Heartbeat pong timeout (25s): if no pong after ping, force-close and trigger reconnect. Connection timeout (30s): if WebSocket not OPEN by deadline, close with error. `onerror` calls `ws.close()` for consistent cleanup. Debounced resize handler (100ms). Tab close picks left neighbor. Ctrl+Tab / Ctrl+Shift+Tab cycles tabs. Search bar closed on tab switch.

**DNOS iTerm preference (Mar 2026):** The canvas terminal button (top-left on selected device) calls `openTerminalToDevice` which routes to iTerm when the host is an IP and the device is NOT in GI/RECOVERY mode. This applies to **both standalone and cluster** devices. The non-GI/RECOVERY override is the first check in `openTerminalToDevice` (before cluster/standalone branching). Virsh console and web terminal are only used for GI/RECOVERY mode (pre-DNOS boot) or when no IP is available. The **toolbar SSH button** always opens the SSH dialog for credentials and settings. Host classification: IPs -> iTerm; serials -> web terminal (bridge resolves).

**Connect button fixes (Mar 2026):** SSH dialog per-method Connect button now updates `hostInput.value` to the row's host before calling `doConnect` (prevents stale host in sshConfig). Double-click protection via opacity + pointerEvents. Clipboard write uses `.then()`/`.catch()` for accurate success/fail feedback ("Password copied" vs "Paste password manually"). Stale `_lastProbeResult` cleared when host input is emptied. Probe returns 0 reachable methods -> returns early with warning (no longer attempts connection to unreachable host). Probe failure shows user-facing notification.

### Remote Access via Server IP (Mar 2026)
**Problem**: When the app is accessed via `http://<server-ip>:8080/` instead of localhost, `navigator.clipboard.writeText()` fails (requires HTTPS or localhost). Copy-to-clipboard features (config push, link table, SSH command, debugger) silently failed.
**Fix**: Added `topology-clipboard-utils.js` with `window.safeClipboardWrite(text)` that falls back to `document.execCommand('copy')` when the modern API fails. Replaced all raw `navigator.clipboard.writeText()` calls across 10+ JS files. Added CORS headers to `serve.py` `end_headers()` and `do_OPTIONS` handler. Fixed `bundle.js` hardcoded `localhost:8765` to use `/api/dnaas` proxy path.
**Files**: topology-clipboard-utils.js (new), index.html, topology-*.js, scaler-gui.js, debugger.js, bundle.js, serve.py.

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

## Console Discovery & PDU Power (Zohar's DB)

The topology app integrates Zohar Keiserman's lab console database for device recovery operations.

### Data Sources (hosted on `zkeiserman-dev`)

| File | Path on server | Local cache | Purpose |
|------|---------------|-------------|---------|
| Console CSV | `/home/dn/console_db/console_devices.csv` | `/tmp/console_devices_cache.csv` | Serial -> Console Server + Port (~700 devices) |
| PDU Mapping | `/home/dn/console_db/pdu_mapping.json` | `/tmp/pdu_mapping_cache.json` | Serial -> PDU host + outlet (power cycling) |
| PDU CLI Config | `/home/dn/console_db/pdu_cli_config.json` | `/tmp/pdu_cli_config_cache.json` | PDU host -> CLI type (dev_outlet vs ol) |

### Discovery Priority Chain

1. **Zohar's CSV DB** (primary) -- fetched via SFTP from `zkeiserman-dev`, cached 1 hour
2. **Device42 API** (fallback) -- requires `~/.device42_config.json`
3. **console_mappings.json** (cached results) -- auto-saved after any discovery

### Connection Strategy Integration (`connection_strategy.py`)

`get_console_config_for_device(hostname)` resolution order:
1. `console_mappings.json` multi-server format
2. `console_mappings.json` legacy single-server format
3. `console_mappings.json` device_to_console lookup
4. Zohar's CSV (by serial from `operational.json`)

### Frontend Flow

1. SSH dialog "Discover Console" button -> `ScalerAPI.discoverConsole()` -> `POST /api/ssh/discover-console`
2. Results show console server, port, PDU info in the SSH dialog
3. If PDU entries found, "Power Cycle (PDU)" button appears
4. Power cycle -> `ScalerAPI.pduPower()` -> `POST /api/ssh/pdu-power`
5. Auto-switch probe includes console as a viable method when discovered

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

### Dialog Keyboard Isolation & AutoSave Safeguards (Mar 2026)

**Critical bug found and fixed:** The global keyboard handler (`topology-keyboard.js`) is
attached to `document` in capture phase, meaning ALL keystrokes site-wide are processed --
even when floating dialogs (Stack, LLDP, XRAY) are open. This caused accidental object
deletion when the user pressed Delete/Backspace, and full canvas wipe via Ctrl+X, while
interacting with a dialog. The Stack dialog's refresh button (which fetches SSH data for
5-10 seconds) was the trigger point -- during the async wait, any keystroke was processed
by the canvas editor.

**Fixes applied (6+ files):**
- `topology-keyboard.js`: Dialog guard at top of `handleKeyDown` uses `document.querySelector`
  to check for interactive modal/overlay elements by ID. Covers: enable-LLDP overlay, DNAAS
  dialogs, save/export pickers, style palettes, width/curve/style popups, text/link/device
  editor modals (`.show` qualifier), recovery modal, shortcuts modal. All popup elements are
  created dynamically and removed on close, so DOM existence = visible. **Read-only panels
  (Stack, LLDP, XRAY, git-commit) are intentionally excluded** so canvas shortcuts work while
  viewing reference data -- those panels use defense-in-depth via `stopPropagation` on their
  own keydown/keyup handlers. Also added confirmation prompt to Ctrl+X (clear canvas).
- `index.html`: Canvas element has `tabindex="0"` so it can receive keyboard focus. Required
  for remote access (server IP URL) where the browser may not auto-focus the page content.
- `topology.js`: `canvas.focus()` called after editor construction to grab keyboard focus.
- `topology-mouse-down.js`: `canvas.focus({ preventScroll: true })` on every mousedown to
  maintain keyboard focus after clicking the canvas.
- `styles.css`: `#topology-canvas { outline: none; }` suppresses browser focus outline.
- `topology-stack-dialog.js`: Added keyboard event isolation (`stopPropagation` on keydown
  and keyup). Set `tabindex=-1` and auto-focus on open. Defense in depth.
- `topology-lldp-dialog.js`: Same keyboard isolation pattern.
- `topology-xray-popup.js`: Same keyboard isolation pattern.
- `topology.js` (`autoSave`): Added object count sanity check -- refuses to save if object
  count dropped by more than 70% from last save. Added rotating backup (`topology_autosave_backup`
  key in localStorage). Added `recoverTopology()` console command for emergency recovery.
- `topology-files.js` (`saveRecoveryPoint`): Added empty-state guard and same 70% drop check.

**Rule for ALL new dialogs/modals:** Every floating dialog MUST include:
1. `dialog.addEventListener('keydown', (e) => { e.stopPropagation(); });`
2. `dialog.addEventListener('keyup', (e) => { e.stopPropagation(); });`
3. `dialog.tabIndex = -1;` (allows focus)
4. `dialog.focus();` after appending to document.body
5. An `id` attribute that matches the selector list in the keyboard handler's dialog guard (for interactive modals that should block canvas shortcuts).

**Recovery commands (browser console):**
- `checkAutoSave()` -- shows all backup sources with object counts and timestamps
- `recoverTopology()` -- restores from the backup with the most objects

### LLDP Animation & Dialog Fixes (Mar 2026)

**Root causes fixed:**
- **TB disappearing during LLDP enable**: `_drawCanvasWaveDots` and `_drawPulsingGlow` had no delegation in `topology.js` and used `editor` as a free variable. The TypeError crashed inside `ctx.save()` without `ctx.restore()`, corrupting canvas state and hiding all subsequent objects (TBs, text). Fixed by adding delegations and passing `editor` as first parameter.
- **No link animation**: Same root cause -- wave dots along connected links never rendered because `editor._drawCanvasWaveDots()` was undefined. Fixed with the delegation.
- **Table format inconsistency**: Initial LLDP load used 300+ lines of inline table HTML while refresh used `_buildLldpTableHtml`. These drifted apart (different grouping, colors, field name priorities). Fixed by unifying both paths through `updateLldpContent` -> `_buildLldpTableHtml`. Also added missing Port Mirror and Snake group support to `_buildLldpTableHtml`.
- **Safety**: Added try-catch around `_drawLldpEffects` in canvas drawing to prevent canvas corruption on future errors.
- **SSH host resolution gap (Mar 2026)**: Multiple flows passed only `serial` (device label like "P-SA-2") to APIs without the device's management IP. When the label does not resolve via DNS or Scaler DB, SSH failed silently. Comprehensive fix across all 8 affected call sites:

**Backend (`discovery_api.py`):**
- `_fetch_lldp_neighbors(serial, ssh_host=None)` -- uses `ssh_host` directly when provided, skipping DNS resolution.
- `_enable_lldp_on_device(serial, ..., ssh_host=None)` -- same pattern, uses mgmt IP when frontend provides it.
- `_resolve_serial_to_host(serial)` -- now checks `device_inventory.json` `mgmt_ip` as final fallback after DNS and Scaler DB.
- `GET /api/device/{serial}/lldp` -- accepts `?ssh_host=IP` query param for SSH fallback.
- `POST /api/enable-lldp` -- reads `ssh_host` from body and passes to `_enable_lldp_on_device`.
- `POST /api/lldp-neighbors` -- reads `ssh_host` from body and passes to `_fetch_lldp_neighbors`.
- `POST /api/lldp-neighbors-live` -- reads `ssh_host` from body and passes to `_fetch_lldp_neighbors`.

**Frontend (JS files):**
- `topology-lldp-dialog.js`: `_fetchLldpNeighbors(serial, device)` and `_fetchLldpNeighborsLive(serial, device)` pass `device.sshConfig.host` as `ssh_host`.
- `topology-xray-popup.js`: `_fetchLldpForDevice` and `_fetchDeviceInterfaces` append `?ssh_host=` from `device.sshConfig.host`.
- `topology-link-details.js`: `autoFillFromLldp` passes `device1.sshConfig.host` as `?ssh_host=`.
- `topology-dnaas-helpers.js`: `_showNoLldpDialog` enable-LLDP button resolves the device from canvas and passes `sshConfig`.
- `bundle.js`: `_enableLldpOnDevice(serial, sshConfig)` and `showEnableLldpDialog(serial, sshConfig)` accept and forward `sshConfig`.

**Bridge (`scaler_bridge.py`):**
- `_build_device_context` LLDP fallback now appends `?ssh_host={mgmt_ip}` when calling discovery_api.

**Resolution priority (unified):** NetworkMapper MCP > Scaler DB > device_inventory.json > `ssh_host` param > DNS with domain suffixes > direct serial.

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

## Lab recovery runbook (2026-03-20)

Reference: PE-4 cluster GI stack stuck (`gi-manager` 0/0), RR-SA-2 / PE-1 pre-delete config restore.

### PE-4 (YOR_CL_PE-4) NCC1 -- GI stack repair

1. From KVM: `ssh dn@100.64.6.6` (lab password), `sudo virsh console --force kvm108-cl408d-ncc1`.
2. Serial login: `dn` / `drivenets` when at `login:`.
3. If `gi-manager` is 0/0 and `docker service ps` shows `Rejected` / placement errors, run the **full cleaner** from Confluence QA page *Deployed SA Instead of Cluster - How to Recover Cluster* (docker swarm leave, prune, clear `ncc_id` / `cluster_id` / deploy-plans, `node_flavor`, reboot). Option A (`docker swarm leave --force` only) was not enough in this incident.
4. After reboot, confirm `docker service ls`: `gi-agent` and `gi-manager` both **1/1**.
5. DNOS deploy: `POST /api/operations/image-upgrade` with `upgrade_type` `gi_deploy`, URLs from `SCALER/db/configs/YOR_CL_PE-4/operational.json`, and `device_plans["YOR_CL_PE-4"].deploy_params` including `system_type` **CL-86**, `deploy_name` **YOR_CL_PE-4**, `ncc_id` **1** (active NCC1; do not rely on standby NCC0 for image pull per cluster behavior).

### Config restore via `/api/operations/push`

| Device | Source file | Notes |
|--------|-------------|--------|
| RR-SA-2 | `SCALER/db/configs/RR-SA-2/pre_delete_backup_sanitized.txt` | `push_method`: `file_upload`, `load_mode`: `merge`. Job completed with merge + commit. |
| YOR_PE-1 | `SCALER/db/configs/PE-1/pre_delete_backup_20260313_114931.txt` | Use config body from **line 55** onward (strip header comments). Push with `ssh_host` **100.64.4.200** when that is the live MGMT IP. |

### Push / IP resolution fixes (same serial, two config dirs)

When both `PE-1/` and `YOR_PE-1/` exist with the same `serial_number`, `operational.json` can disagree on `mgmt_ip`. Fixes applied:

- **`scaler_bridge._resolve_mgmt_ip`**: If `ssh_host` is an IPv4, always use that literal address for TCP; still resolve `scaler_id` from the ops index when the IP is a key (`ssh_ip_literal:`).
- **`scaler.utils.get_ssh_hostname`**: If `device.ip` (IPv4) differs from `mgmt_ip` in the ops file loaded by `device.hostname`, prefer **`device.ip`** so API-requested targets are not overridden by stale ops.

After changing these modules, sync live paths (`CURSOR/scaler_bridge.py`, `SCALER/scaler/utils.py`) and let uvicorn reload (or restart the bridge).

## Image Upgrade Wizard: DNOS vs GI mismatch (2026-03-21)

**Cause:** `operational.json` `device_state` values **`UPGRADING`** and **`DEPLOYING`** were classified as **GI** (same bucket as `GI`, `BASEOS_SHELL`). After an image job finished, a stale `UPGRADING`/`DEPLOYING` left in ops made the wizard and canvas show **GI** while the device was already on **DNOS**.

**Fix:**

- **`scaler/connection_strategy.py`**: `UPGRADING` / `DEPLOYING` return `""` from `classify_device_state`; removed from `GI_STATES`.
- **`scaler_bridge._device_status_from_cache`**: If mode is still empty but `dnos_ver` is present and `upgrade_in_progress` is false, set mode **DNOS**.
- **`scaler-gui.js`**: Wizard merge no longer overwrites **canvas DNOS** with cached GI-like modes; `_classifyDeviceState` aligned with Python.
- **`topology-device-monitor.js`**: Transient `UPGRADING`/`DEPLOYING` from context API do not force **GI** on the canvas (preserve prior mode or `unknown`).

## Cluster NCC management IP discovery (2026-03-21)

For KVM-backed clusters, DNOS CLI is reached reliably via **virsh console** from the KVM host. A **second** SSH session (background) can run `show interfaces management | no-more` on that console path, parse the IPv4, verify **dnroot/dnroot** SSH to that IP, then persist `ncc_mgmt_ip` and `ncc_mgmt_verified_at` in `SCALER/db/configs/<scaler_id>/operational.json`.

| Piece | Location |
|-------|----------|
| Discovery (blocking worker) | `scaler_bridge._discover_ncc_mgmt_ip_sync`, shared virsh setup `_open_virsh_ncc_shell_channel` |
| API | `POST /api/ssh/discover-ncc-mgmt`, `GET /api/ssh/check-port` |
| Proxy (serve.py) | Same pattern as `/api/ssh/probe` |
| Probe enrichment | `probe_connection` adds `ncc_mgmt_ip` / `ncc_mgmt_verified_at` when present in ops |
| GUI | `ScalerAPI.discoverNccMgmtIp`, `ScalerAPI.checkPort`; `topology-object-detection.js` opens **iTerm to cached `_nccMgmtIp`** when port 22 is reachable, else web virsh + background discovery |

`topology-object-detection.js` calls `_fireBackgroundNccDiscovery` after opening the virsh web terminal so the user session is not blocked.

## KVM cluster: dynamic `operational.json` + normal image upgrade (2026-03-21)

**Problem:** For `ncc_type: kvm`, `mgmt_ip` was often the **KVM host** (e.g. `100.64.6.6`). `_run_normal_upgrade` used `_ssh_connect_basic(mgmt_ip)`, which lands on BaseOS/Ubuntu, not DNOS CLI. `delete_deploy` / `gi_deploy` already used `connect_for_upgrade` (virsh-capable).

**Behavior now:**

| Trigger | `operational.json` updates |
|---------|----------------------------|
| `POST /api/ssh/discover-ncc-mgmt` (verified NCC IP) | `ncc_mgmt_ip`, `ncc_mgmt_verified_at`, and **`mgmt_ip` / `ssh_host`** set to that NCC IPv4 |
| `POST /api/ssh/probe` for `ncc_type == kvm` | First reachable **`ssh_mgmt` or `ssh_ncc`** IPv4 in probe results updates **`mgmt_ip` / `ssh_host`** if different (atomic write with `last_working_method` when applicable) |

**Normal upgrade (`_run_device_upgrade`, `upgrade_type == normal`):**

- If `ncc_type == kvm` (after console_mappings merge + re-read of `operational.json`): use cached **`ncc_mgmt_ip`** with **dnroot/dnroot** for `_run_normal_upgrade`.
- If KVM cluster but **no** `ncc_mgmt_ip`: **`connect_for_upgrade`** then `_run_normal_upgrade(..., pre_connected=(ssh, channel))`.

**GUI:** `_getWizardDeviceList` sets `ssh_host` / `ip` from **`sshConfig._nccMgmtIp`** when `_isCluster` so the Image Upgrade wizard passes the NCC target in `ssh_hosts`.

**Code:** `scaler_bridge.py` (`probe_connection`, `discover_ncc_mgmt_ip_endpoint`, `_run_normal_upgrade`, `_run_device_upgrade`); `scaler-gui.js` (`_getCanvasDeviceObjects`, `_getWizardDeviceList`).

## Major version jump detection -- forced delete_deploy (2026-03-20)

**CRITICAL RULE:** When the target DNOS major version differs from the current DNOS major version (e.g. v25.x -> v26.x), the upgrade MUST use `delete_deploy`, NEVER `normal` (target-stack load + install). Loading v26 images into a v25 BaseOS causes crashes and DNOS recovery mode.

**Detection points (all three must agree):**

| Layer | How it detects | Location |
|-------|---------------|----------|
| **Frontend (Plan step)** | Compares `curMaj` vs `tgtMaj` from parsed stack versions. Shows "MAJOR JUMP" badge in Compare step. Forces `upgrade_type: 'delete_deploy'` in device plan. | `scaler-gui.js`, Upgrade Plan step render |
| **Backend (`_run_device_upgrade`)** | Reads `dnos_version` from `operational.json`, extracts major from target DNOS URL via `_extract_version_from_dnos_url`. If majors differ, overrides `upgrade_type` to `delete_deploy`. | `scaler_bridge.py`, `_run_device_upgrade` |
| **Backend (`wait_and_upgrade` auto-plan)** | Same comparison during auto-plan generation. Logs `[WARN] Major version jump` and sets `_ut = "delete_deploy"`. | `scaler_bridge.py`, `_wait_then_upgrade` |

**Cluster upgrade with direct SSH auth fallback (2026-03-20):**

When upgrading KVM cluster devices via direct SSH to the NCC mgmt IP, the code now tests SSH auth before committing. If `dnroot/dnroot` fails (e.g. post-deploy VIP credentials not set), it falls back to `connect_for_upgrade` (virsh console through KVM host).

**Cluster operational fetch: virsh console fallback (2026-03-23):**

`_fetch_all_operational_via_ssh` now accepts `scaler_device_id` and falls back to `_fetch_ops_via_virsh_fallback` when direct SSH auth fails (common on KVM clusters where NCCs don't accept password SSH). The fallback:
1. Reads cluster info from `operational.json` (kvm_host, kvm_host_credentials, ncc_vms, active_ncc_vm)
2. Tries each NCC VM in order (stored active first, then others), connecting via `_open_virsh_ncc_shell_channel`
3. Detects standby NCCs (bash `$` prompt after dncli fails) and skips to next
4. Sends `show system stack | no-more` and `show lldp neighbors | no-more` through the virsh channel
5. Enters shell (`run start shell` + password) and runs `cat /.gitcommit` to get the git commit hash
6. Updates `active_ncc_vm` in operational.json when the stored value was stale
This also required fixing `_open_virsh_ncc_shell_channel` to handle the dncli sudo password prompt (sends `dnroot` / `drivenets` / `drive1234!`).
Root cause: PE-4's NCC at 100.64.4.98 rejects password SSH entirely; only virsh console from KVM host works.
`_fetch_git_commit_via_ssh` and `get_device_git_commit` endpoint also fall back to virsh for cluster devices.
The `_send_and_recv` channel helper was fixed to check the FULL accumulated output for the CLI prompt (last line ending with `#` or `>`), not individual chunks -- checking individual chunks would falsely match the command echo containing the hostname prompt.
Also fixed: `routes/ssh.py` was missing top-level `import time, json, os, re` causing probe_connection to crash with NameError (HTTP 500).

**Stack-live and git-commit performance (2026-03-23):**

Added `POST /api/devices/{id}/stack-live` endpoint in `routes/devices.py` -- calls `_fetch_all_operational_via_ssh` (with virsh fallback) instead of discovery_api's direct paramiko SSH. The frontend `_fetchStackLive` tries this scaler_bridge endpoint first, falling back to discovery_api only if needed.
The `get_device_git_commit` endpoint now checks `operational.json` cache before SSH/virsh. After the first virsh fetch, git_commit is cached and subsequent calls return in <5ms. The git commit popup in `topology-selection-popups.js` was also optimized: removed the slow `DeviceMonitor.refreshDevice` call from the fetch chain and goes straight to the fast `ScalerAPI.getDeviceGitCommit` endpoint.

**WARNING -- uvicorn --reload kills background jobs:**

The `_push_jobs` dictionary is in-memory. If `scaler_bridge.py` is modified while a `wait_and_upgrade` background thread is running, uvicorn's `--reload` restarts the process and kills the thread. NEVER sync `scaler_bridge.py` to the live path while a Wait & Upgrade job is active.

## Install prompt handling -- `_send_install_command` (2026-03-21)

**Problem:** `_run_normal_upgrade` used `_send_wait("request system target-stack install", 15)` which does NOT detect or answer the `Do you want to continue? (yes/no)` confirmation prompt. The device would time out waiting for "yes" and the install never happened. This caused upgrades to report "complete" without actually installing new images.

**Fix:** New `_send_install_command(chan, _log)` function (modeled after `_send_deploy_command`):

- Clears channel buffer before sending
- Polls every 0.5s for `yes/no`, `y/n`, `do you want`, or `continue` in output
- Sends `yes\n` when prompt detected
- Handles socket close (expected -- device reboots after install)
- 60s timeout (120 iterations x 0.5s)

**Post-install verification:** New `_post_install_verify` function runs after `_run_normal_upgrade`:

- Waits 60s initial (device rebooting)
- Reconnects via SSH every 20s (timeout 600s)
- Runs `show system install | no-more`
- Verifies each component version from URL appears in install output
- Logs PASS/FAIL per component (observational -- does not raise)

| Function | Purpose | Prompt handling |
|----------|---------|----------------|
| `_make_send_wait` | Generic send-and-wait for `#`/`>` prompt | NO -- bare `_send_wait` never answers yes/no |
| `_send_deploy_command` | `request system deploy` with yes/no | YES -- polls + auto-answers |
| `_send_install_command` | `request system target-stack install` with yes/no | YES -- polls + auto-answers |
| `_send_load_cmd` (in `_load_images_on_channel`) | `request system target-stack load` with overwrite prompt | YES -- checks `continue?`, `(yes/no)`, `overwrite` + Ctrl+C to background |

**RULE:** Any DNOS command that can prompt the user (`delete`, `deploy`, `install`, `load`) must use a prompt-aware sender, NOT `_send_wait`.

## Image loading in GI mode -- Ctrl+C background + proper progress polling (2026-03-22)

**Problem:** `_send_load_cmd` sent `request system target-stack load <url>` and answered `yes`, but in GI mode this command shows inline download progress and blocks the terminal prompt until download completes. The code never sent Ctrl+C to background the download, so all subsequent polling commands (`show system stack`) received garbage output or timed out. Additionally, `_poll_load_progress` used `show system stack` (which only shows images AFTER download+untar is complete) instead of `show system target-stack load | no-more` (which shows real-time `Progress: XX%`).

**Fix (two parts):**

1. `_send_load_cmd`: After answering `yes` and detecting `"Download in progress"` or `"started target-stack load"`, sends `\x03` (Ctrl+C) to background the download and return the `#` prompt. The download continues in the background per DNOS docs.

2. `_poll_load_progress`: Now uses `show system target-stack load | no-more` as PRIMARY source -- parses `Task status: in-progress/complete/failed` and `Progress: XX%`. Falls back to `show system stack` Target column only for final confirmation.

**Monitoring commands (correct usage):**

| Command | What it shows | When to use |
|---------|--------------|-------------|
| `show system target-stack load \| no-more` | Active download progress, Task status, Progress % | During download polling |
| `show system target-stack load history` | Completed/failed load tasks | After download for history |
| `show system stack` | Current + Target stack versions | After download complete to verify |

**Timeouts:** `max_wait` increased from 300s to 600s (large images), `stall_threshold` from 120s to 180s (network latency). Stall detection now tracks time since last progress change, not absolute elapsed time.

## Pre-deploy image verification and config repair (2026-03-21)

### Pre-deploy image verification

Before `request system deploy`, the flow now verifies that ALL expected images are present in the target-stack:

- Parses `show system stack` output for components with non-empty Target column
- Compares against the URL list (DNOS, GI, BaseOS)
- **BLOCKS deploy** with `RuntimeError` if any expected component is missing

This prevents the previous failure mode where deploy was sent with empty target-stack, and the device deployed with old/no images.

### Smart config repair after delete+deploy

`_post_deploy_config_repair` was rewritten to handle version-incompatible config:

1. **Full rollback attempt**: `rollback 1` + `commit`
2. **If commit fails**: Parse error output for specific failure patterns:
   - `configuration item 'X' is not supported` -- hierarchy removed
   - `Unknown word 'X'` -- keyword renamed
   - `invalid value` / `invalid keyword` -- syntax changed
3. **Partial repair**: Load rollback, `delete` each failed hierarchy, commit remainder
4. **Report to GUI**: Each failed hierarchy includes path, reason, and category

Config repair failure categories for user-friendly reporting:

| Category | Meaning |
|----------|---------|
| FlowSpec | FlowSpec syntax may differ between versions |
| BGP | Neighbor/AF structure changed |
| Interface | Interface naming differs |
| VRF/Services | Hierarchy restructured |
| Routing Policy | New vs old policy language |
| IGP/MPLS | Protocol config syntax changed |
| System | System-level config changed |

### Automatic gi-manager recovery (stuck deploy detection)

Added to `_post_deploy_verify` -- automatically detects and recovers from stuck gi-manager after a failed deploy. This handles the scenario where:

- Deploy was sent (e.g. v25 GI trying to deploy v26 images)
- Device reboots but comes back with old GI still running
- gi-manager Docker service is stuck at 0/0 replicas
- `gicli` is not available, `dncli` fails with "CLI is N/A"

**Pre-flight detection** (before loading images -- handles devices ALREADY stuck from a previous attempt):

- `_preflight_gi_health(job_id, device_id, chan, ssh, scaler_hostname, _log)` runs in both `_run_gi_deploy_upgrade` and `_run_delete_deploy_upgrade` (already-in-GI path)
- Tests GI CLI by running `show system stack | no-more` -- if the response doesn't contain table markers, GI CLI is broken
- If broken: navigates to bash, checks gi-manager, runs cleaner if stuck, waits for reboot, reconnects
- Returns new `(ssh, chan, ncc_id, recovered)` tuple so callers use the fresh connection

**Post-deploy detection** (in the post-deploy verify loop):

1. Track how long the device has been in GI mode (`gi_first_seen_at`)
2. After 10 minutes (`GI_STALL_THRESHOLD = 600s`) with no install progress:
   - Navigate to NCC bash shell via `_ensure_ncc_bash` (echo probe to distinguish bash from CLI)
   - Run `_check_gi_manager_health`: checks `docker service ls` for gi-manager replicas and `docker ps` for container version
   - If gi-manager is stuck (0/0 or missing): trigger automatic recovery

**Recovery steps** (`_run_gi_manager_recovery` -- full Confluence cleaner):

1. `sudo docker swarm leave --force`
2. `sudo docker system prune -a -f --volumes`
3. `sudo rm -f /etc/drivenets/ncc_id /etc/drivenets/cluster_id /etc/drivenets/deploy-plans /etc/drivenets/node_flavor`
4. `sudo reboot`

**Post-recovery retry** (back in the verify loop):

1. Wait for NCC to come back in GI mode (fresh gi-manager)
2. Reload all images via `_load_images_on_channel`
3. Re-send `request system deploy`
4. Continue waiting for DNOS mode (timeout reset for the retry)

**Safety**: Recovery is attempted only once per deploy (`gi_recovery_attempted` flag). Only triggers when `url_list` and `deploy_params` are provided (both `_run_gi_deploy_upgrade` and `_run_delete_deploy_upgrade` pass these).

**GUI phases**: `gi-recovery` (cleanup + reboot) and `gi-recovery-reload` (reloading images after recovery) are shown in the progress panel.

**Source**: Confluence QA "Deployed SA Instead of Cluster" recovery procedure. Validated on PE-4 (2026-03-20).

### Image Upgrade Wizard -- config hint (plan step)

Short orange info lines (not a wall of text):

- **GI deploy:** Clarifies no full system delete; config re-apply after DNOS; failures in log.
- **Delete + deploy:** Back up before delete, restore after DNOS; CLI mismatches in log.

Do not use the old single block that said "system delete + deploy" for GI-only plans (incorrect).

### Upgrade failure dismiss (canvas red badge)

When an image upgrade job fails, devices show a red **upgrade failed** badge. Dismiss is persisted in `localStorage` under `scaler_dismissed_upgrade_failures` as keys `jobId:deviceLabel` so the job watcher does not re-apply the badge. Actions: **Dismiss** / **New upgrade** on the bottom failure banner, and **Dismiss alert** / **New upgrade** on the completed failure progress panel.

### GUI device mode states

The upgrade wizard now supports these device mode badges (not just DNOS/GI):

| State | Badge color | When shown |
|-------|-------------|------------|
| DNOS | Green | Normal operation |
| GI | Cyan | GI/BASEOS_SHELL/ONIE |
| RECOVERY | Red | DN_RECOVERY |
| DEPLOYING | Orange (pulsing) | Deploy in progress |
| INSTALLING | Orange (pulsing) | Image install in progress |
| UPGRADING | Cyan (pulsing) | Upgrade flow active |
| BOOT | Purple (pulsing) | Device booting |
| FAILED/ERROR | Red (bold) | Operation failed |
| UNREACHABLE | Light red | SSH timeout/failure |
| CONFIG_REPAIR | Yellow (pulsing) | Config restoration in progress |

## Cluster post-upgrade recovery: NCP/NCF stuck disconnected (2026-03-22)

After `request system delete` + fresh DNOS deploy on a CL-86 cluster, only the active NCC
gets DNOS. All NCPs, NCFs, standby NCC, NCM remain `disconnected` if their GI agents fail
to register with the CMC on the new NCC. Full investigation methodology and remediation
steps are documented in `CLUSTER_POST_UPGRADE_RECOVERY.md`.

**Quick diagnosis checklist**:
1. `show system` -- NCPs/NCFs show `disconnected`, zero uptime, empty serial
2. `show system install` -- only NCC tasks completed, zero NCP/NCF tasks
3. `show system backplane` -- NCM ctrl ports UP but nodes show `unavailable-node`
4. `run start shell ncc <id>` then `ip netns exec host_ns ip neigh show` -- NCPs have ctrl-bond IPs but refuse SSH on port 22
5. CMC log (`cluster_manager_supervisor.log`) shows `CMC_SYS_EVENT_ACTIVE_DOWNSTREAM_EVENT` looping to `disconnected_nces`

**Root cause**: NCP GI agents are not running after system delete. The NCPs have network
connectivity (BaseOS level) but SSH/GI agent containers have not started.

**BGP flapping** (ACTIVE -> CONNECT every 10s) is a symptom: no NCP = no data plane
interfaces = no BGP peering possible with external neighbors.

**Remediation**: Console access to NCP (via IPMI or console server), then restart GI agent
or power-cycle. See `CLUSTER_POST_UPGRADE_RECOVERY.md` for full procedure.

## Legacy cluster deploy rule: ncc-id is autodetected by GI (2026-03-22)

For legacy clusters (CL-* system types with NCM + NCC, no NCCM):
- **NCM port 49 = NCC-0**, **NCM port 50 = NCC-1** (hardcoded in NCC ID allocation)
- The GI CLI **autodetects the ncc-id** via NCM LLDP at boot. The `ncc-id` parameter in
  `request system deploy` **MUST match the autodetected ID** or GI rejects with:
  `Cannot deploy with ncc id that doesn't match the auto detected id`
- Example: `kvm108-cl408d-ncc1` is connected to NCM port 50, so GI autodetects it as NCC-1.
  Deploying with `ncc-id 0` is REJECTED. Must use `ncc-id 1`.

**Key learning (2026-03-22)**: The earlier assumption that "always deploy with ncc-id 0"
was wrong. GI validates ncc-id against hardware detection. The cluster instability
(NCPs/NCFs disconnected) was NOT caused by ncc-id mismatch -- GI rejects mismatches outright.
The NCP/NCF disconnect is a separate issue (physical hardware not joining Docker Swarm).

**GUI behavior** (Image Upgrade Wizard):
- `scaler-gui.js`: upgrade plan builder tags CL-* devices with `is_cluster: true`, `system_type`.
  CLI preview shows `ncc-id autodetected by GI (NCM LLDP)` for deploy/delete-deploy.
  The `ncc_id` field is set to `'autodetect'` -- actual value must come from the device.
- `topology-ssh-dialog.js`: Cluster Components section shows NCM port mapping info.
- `devices.json`: PE-4 platform corrected from "NCP" to "CL-86" with `system_type: "CL-86"`.

**Source**: Confluence "NCC ID allocation post G.I." (page 2291892416) confirms the port mapping.

## Cluster preflight checks for upgrade wizard (2026-03-22)

Before deploying a cluster device, the upgrade wizard backend runs a preflight check:
1. Detects cluster devices by `system_type` starting with `CL-`
2. SSHes to the KVM host (from `connection_strategy` console config)
3. Runs `virsh list --all` to check all NCC VMs
4. If any NCC VM is **shut off**, the deployment is **BLOCKED** with a clear error

**Why this matters (incident 2026-03-22):**
- PE-4 deployment failed because `kvm108-cl408d-ncc0` VM was shut off (autostart=disabled)
- Only NCC-1 was running, so deploy went with `ncc-id 1` (autodetected by GI)
- Starting NCC-0 later (with old BaseOS 2.2610019013 vs NCC-1's 2.2620259017) caused
  a version mismatch that crashed DNOS on NCC-1 (routing_engine container went down)
- Both NCCs ended up in GI mode with no DNOS running

**Implementation:**
- `scaler_bridge.py`: `_cluster_preflight_check(scaler_id)` function, called from
  `image_upgrade_plan` endpoint's `_check_device`. Returns VM states, blocks if shut off.
- `scaler-gui.js`: Renders `upgrade-plan-preflight-fail` div with red alert showing which
  VMs are shut off and which KVM host to fix them on.
- `styles.css`: `.upgrade-plan-row--preflight-fail` and `.upgrade-plan-preflight-fail` classes.

**What the preflight checks:**
| Check | Blocked if |
|-------|-----------|
| All NCC VMs running | Any VM is shut off |
| VM count vs expected | Fewer running than expected (warning only) |
| KVM host reachable | Cannot connect to KVM (warning, not block) |

## NCC selector in upgrade wizard (2026-03-22)

For cluster devices (CL-*), the upgrade wizard now shows an **NCC selector dropdown**
in the upgrade plan table. This lets the user choose which NCC VM the deployment will
target and what `ncc-id` value to use in the `request system deploy` command.

**How it works:**
1. The `_cluster_preflight_check` backend function discovers running NCC VMs via
   `virsh list --all` on the KVM host.
2. It infers each VM's NCC ID from the VM name convention (e.g., `*-ncc0` -> NCC-0,
   `*-ncc1` -> NCC-1). This matches the GI autodetection from NCM LLDP port mapping.
3. The preflight result includes `ncc_options[]` -- an array of running NCC VMs with
   their inferred `ncc_id`, `vm_name`, and display `label`.
4. The frontend (`scaler-gui.js`) renders a `<select>` dropdown for cluster devices
   showing these NCC options. The user's selection updates `device_plans[did].deploy_params.ncc_id`.
5. The backend respects the frontend-provided `ncc_id` -- it only falls back to
   `operational.json` values when no `ncc_id` was provided by the frontend.

**Data flow:**
- Preflight: `_cluster_preflight_check` -> `cluster_preflight.ncc_options[]`
- Frontend: user selects NCC -> `plan.devices[did].deploy_params.ncc_id = N`
- Execution: `_do_one(did)` -> `plan.get("deploy_params", {})` -> `_run_device_upgrade`
- Deploy: `_send_deploy_command(chan, sys_type, d_name, ncc_id, _log)`

**CLI preview:** Shows the selected NCC-ID and VM name in the Execute step
(e.g., `PE-4: delete + deploy (full wipe | ncc-id 0 (kvm108-cl408d-ncc0))`).

**Fallback:** If no NCC selector data is available (preflight failed or not a cluster),
the deploy command falls back to the existing `ncc_id` from `operational.json` or
defaults to 0, with the GI retry logic flipping to `1 - ncc_id` on mismatch.

## Upgrade wizard: system_type source priority and GI Compare (2026-03-22)

**Problem:** `device_inventory.json` (DNAAS cache) can hold stale `system_type` strings
such as `SA-40C8CD, Family: NCR` for a cluster device, while `operational.json` under
`~/SCALER/db/configs/<device_id>/` has the correct value (e.g. `CL-86`).

**Fix (`serve.py` `/api/devices/`):** When merging `operational.json`, always apply
`system_type` / `deploy_system_type` onto the device entry so scaler cache wins over
inventory noise.

**Frontend (`scaler-gui.js`):**
- `_sanitizeWizardSystemType()` strips comma/`Family:` garbage and only keeps values
  that match `_WIZARD_KNOWN_SYS_TYPES` (GI CLI system-type list).
- `_getWizardDeviceListSync()` + `_mergeWizardDeviceListFromApi()` let the Image
  Upgrade Wizard open immediately; `GET /api/devices/` runs in the background to
  fill `platform` / mgmt IP.
- Compare step: if **all** selected devices are GI mode, branch-switch and
  compatibility alerts are hidden; the GI banner includes system type (when known),
  NCC hint for CL-* clusters, and a sample `request system deploy system-type ... name ...` line.

## Wrong system type deploy prevention (2026-03-22)

**Problem**: Deploying a device (especially a cluster) with the wrong `system_type` causes
catastrophic persistent contamination. On clusters, ALL NCEs (NCPs, NCFs, standby NCC)
keep the wrong `cluster_type` in `/golden_data/cm/cluster_type`. They refuse to join the
new cluster. Recovery requires running the cleaner script on every affected NCE manually.

**Root cause from PE-4 incident (2026-03-22)**: NCPs had `cluster_type=SA-36CD-S` from
an old deploy while the NCC was redeployed as CL-86. NCPs refused to join, showed
`disconnected` with zero uptime/serial. Fix: ran Confluence cleaner on both NCPs via
SSH -p 2222 (dn/drivenets). Source: [Deployed SA Instead of Cluster - How to Recover Cluster](https://drivenets.atlassian.net/wiki/spaces/QA/pages/5186093236).

**Detection (3 layers)**:

1. **GUI Wizard** (`scaler-gui.js`):
   - `_buildClientPlan()` tracks `previous_system_type` from `deviceContexts` and detects
     SA<->CL category changes. Sets `system_type_changed` and `system_type_category_change`.
   - Upgrade Plan table row shows red `upgrade-plan-systype-warn--critical` banner for
     SA<->CL changes with guidance about the cleaner script.
   - `collectData` blocks SA<->CL changes with "click Next again to confirm" pattern
     (`_sysTypeChangeAcknowledged` flag).

2. **Backend** (`scaler_bridge.py`):
   - `_check_system_type_change()` called before every deploy in `_run_delete_deploy_upgrade`
     and `_run_gi_deploy_upgrade`.
   - Compares `deploy_params.system_type` with `operational.json`'s stored type.
   - Logs `[CRITICAL]` warning for SA<->CL changes with recovery instructions and Confluence link.
   - Persists `previous_system_type`, `system_type_change_detected`, `system_type_change_at`
     to `operational.json`.

3. **Post-deploy monitoring**: If NCPs stay `disconnected` for >15min after NCC is `active-up`,
   the progress terminal output suggests the cleaner script.

**Key persistent files on NCEs** that cause wrong type:
- `/golden_data/cm/cluster_type` -- deployed type (SA-36CD-S vs CL-86)
- `/run/lock/nce_id`, `/var/opt/.ncc_id`, `/var/opt/.element_id` -- identity
- `/etc/cluster_id`, `/etc/node_flavor` -- cluster binding
- `/var/tmp/deploy-plans/*` -- cached plans

**Cursor rule**: `~/.cursor/rules/wrong-system-type-deploy-prevention.mdc` has the full
cleaner script, access methods, symptom matrix, and recovery procedure.

**CSS classes**: `.upgrade-plan-systype-warn`, `.upgrade-plan-systype-warn--critical`,
`.upgrade-plan-row--systype-critical` in `styles.css`.

## Platform model accepts any system type string (2026-03-22)

**Problem**: The `Platform` enum in `scaler/scaler/models.py` only had `NCP`, `NCM`, `NCP5`.
Devices with `platform: "CL-86"` (like PE-4) failed Pydantic validation silently in
`DeviceManager.list_devices()`, making them invisible in the scaler CLI and wizard.

**Fix**: Changed `Device.platform` from `Platform` enum to `str` field. Added `system_type`
and `connection_method` fields to the `Device` model. The `Platform` enum is kept for backward
compatibility with `WizardState` and `ValidationResult` internal models only.

**Key changes**:
- `scaler/scaler/models.py`: `Device.platform` is now `str`, added `system_type` and
  `connection_method` optional fields
- `scaler/scaler/device_manager.py`: `add_device()` and `update_device()` accept string
  platform and new fields
- `scaler/scaler/interactive_scale.py`: References to `Platform.DNOS` (which never existed)
  and `Platform.NCP` replaced with string `"NCP"`. WizardState creation gracefully handles
  non-enum platform values.
- `topology/scaler_bridge.py`: `_get_device_context()` now falls back to `operational.json`
  for `system_type` when device inventory doesn't have it
- `topology/topology-device-monitor.js`: Caches `system_type` from device context on
  `device._systemType` for instant wizard access