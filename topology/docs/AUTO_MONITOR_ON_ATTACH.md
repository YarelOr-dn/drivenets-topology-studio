# Auto-Monitor-On-Attach: Reference-Counted Device Registration

**Status:** Phase 1 (design + scaffolding only). No production code lands until
the user reviews this doc.

**Owner:** Topology Creator backend.

**Last updated:** 2026-05-05.

**Companion docs:**

- `topology/DEVELOPMENT_GUIDELINES.md` -> "Multi-User is the Default"
- `topology/api/auth/user_store.py` (path helpers + `_open_db()` SQLite WAL pattern)
- `topology/api/device_state.py` (existing shared-device-state SQLite -- the
  concurrency model we will extend, NOT replace)
- `~/.cursor/rules/multiuser-by-default.mdc`

---

## 1. Goal (one paragraph)

When a user drops a device onto the canvas and saves SSH credentials + a
management IP, the backend MUST verify reachability, register the device once
in a **shared, reference-counted "monitored device" registry**, and ensure all
five existing monitoring subsystems (config extract, LLDP/intf/sysinfo
discovery, sub-IF description telemetry, live link telemetry, alarms/health)
pick it up. A second user attaching the same device on a different topology
or domain MUST NOT spin up a duplicate poller -- both canvas cards read the
same backend record and bump a per-user reference count. Removal only stops
monitoring when the **last** reference is detached, and only after asking the
user when they are themselves the last referencer. When a user drops a device
whose IP is already registered, the canvas card auto-fills hostname /
platform / interface inventory from the existing record (smooth ZTP) without
running an SSH probe.

## 2. Architecture (ASCII)

```
                                BROWSER (canvas)
                                       |
        SSH dialog "Save"  /  Drop on canvas  /  Detach card
                                       |
   ScalerAPI.{verifyAndRegister, attachReference, detachReference, listMonitored}
                                       |
                                  HTTPS + JWT
                                       v
+-----------------------------------------------------------------+
|                   topology/serve.py  (port 8080 proxy)          |
|                                                                 |
|   /api/devices/monitored/*            <-- new router            |
|       _require_auth() -> username                               |
|       hand off to scaler_bridge :8766                           |
+-----------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------+
|             scaler_bridge.py (port 8766, FastAPI)               |
|                                                                 |
|   routes/monitored_devices.py     (NEW)                         |
|     POST /api/devices/verify-and-register                       |
|     POST /api/devices/monitored/attach                          |
|     DELETE /api/devices/monitored/{key}/reference               |
|     GET    /api/devices/monitored/{key}                         |
|     GET    /api/devices/monitored                               |
|     PUT    /api/devices/monitored/{key}/credentials             |
|                                                                 |
|   monitored_registry.py           (NEW, shared SQLite)          |
|     - upsert_record(ip, sn, ...)                                |
|     - add_reference(key, username, scope_type, scope_id)        |
|     - remove_reference(key, username, scope_type, scope_id)     |
|     - is_last_reference(key, username) -> bool                  |
|     - find_by_ip(ip), find_by_key((ip, sn))                     |
|                                                                 |
|   monitored_dispatch.py           (NEW)                         |
|     when a registry record is created, broadcast to             |
|     each subsystem's "registration sink":                       |
|        1. SCALER devices.json    (mirror writer)                |
|        2. NetworkMapper          (discover_device + topology)   |
|        3. SCALER description-monitor cache (warm pass)          |
|        4. link-telemetry         (already on-demand)            |
|        5. alarms/health          (auto: SCALER cron picks up)   |
+-----------------------------------------------------------------+
                       |               |                |
                       v               v                v
             ~/SCALER/db/         ~/Network        ~/.topology_users/
             devices.json         Mapper           <username>/
             monitored_           topology DB      monitored_devices.json
             registry.db                           (per-user references)
```

### 2.1 Where each piece of state lives

| Layer | Path | Purpose | Concurrency |
|---|---|---|---|
| Shared registry (canonical) | `~/.topology_shared/monitored_registry.db` | Source of truth: identity, monitoring status, references[]. SQLite WAL via `_open_db()` pattern. | Cross-process / cross-user |
| Lab-scoped device list | `${SCALER_DEVICES_FILE}` (default `~/SCALER/db/devices.json`) | What the 5-min `extract_configs.sh` cron + the SCALER bridge read. We mirror -- never invent a new file here. | File lock + atomic rename |
| Per-user references | `~/.topology_users/<username>/monitored_devices.json` | This user's canvas-membership references (which topologies / domains attach which `(ip, sn)` keys). 0600. | per-user atomic write |
| Network Mapper devices DB | (Network Mapper's own DB, accessed via MCP `discover_device` / `add_device_to_topology`) | What `dnos_list_devices` and the MCP tools read. We push -- never write directly. | MCP server owns |
| Per-user device credentials | `~/.topology_users/<username>/devices.json` (existing, 0600) | Already exists; we keep the same writer (`api/auth/router.py::_write_device_creds`). | existing lock |

**Why three places hold "device data":**

- `~/SCALER/db/devices.json` is the lab profile's device list. The extractor
  cron and the scaler GUI both depend on it. We MUST keep mirroring there or
  the 5-min config extract never runs.
- The Network Mapper has its own DB used by all `user-network-mapper` MCP
  tools and by `dnos-config` (the SCALER cache reader). We MUST add the
  device there or `dnos_list_devices` and `dnos_dnaas_*` won't see it.
- The shared registry (`monitored_registry.db`) is the **only** place that
  holds reference-count + per-user identity bindings. The other two are
  dumb device lists that reflect "monitor this", not "user X owns reference Y".

### 2.2 Concurrency model

Reuse the proven pattern from `topology/api/device_state.py`:

```python
# Identical contract: WAL + busy_timeout=5000 + atomic upsert
@contextmanager
def _open_db():
    path = SHARED_DIR / "monitored_registry.db"
    conn = sqlite3.connect(str(path), timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    yield conn
```

The mirror writers to `~/SCALER/db/devices.json` and the per-user
`monitored_devices.json` use **rename-in-place** atomic writes (`os.replace`)
behind a `threading.Lock`, mirroring `_write_device_creds()` in
`api/auth/router.py`.

## 3. File layout

### 3.1 Per-user file: `~/.topology_users/<username>/monitored_devices.json`

```jsonc
{
  "version": 1,
  "updated_at": "2026-05-05T12:00:00Z",
  "references": [
    {
      "key": "100.64.4.205|WKY1BC7400002B2",
      "scope_type": "topology",            // "topology" | "domain"
      "scope_id": "sec_1771858364/lab.json",
      "scope_label": "Yarel - lab.json",   // human-readable, for UI
      "device_label_on_canvas": "RR-SA-2", // free text from canvas card
      "attached_at": "2026-05-05T12:00:00Z"
    }
  ]
}
```

Path is computed via `user_store.user_data_path(username, "monitored_devices.json")`.
File is chmodded `0600` (it leaks no secrets, but kept consistent with
`devices.json`).

### 3.2 Shared canonical: `~/.topology_shared/monitored_registry.db`

Tables (SQLite, WAL):

```sql
CREATE TABLE monitored_devices (
    key                 TEXT PRIMARY KEY,        -- "<management_ip>|<serial_number>"
    management_ip       TEXT NOT NULL,
    serial_number       TEXT NOT NULL,           -- "" if unknown (e.g., GI mode)
    hostname            TEXT NOT NULL DEFAULT '',
    platform            TEXT NOT NULL DEFAULT '',
    is_cluster          INTEGER NOT NULL DEFAULT 0,
    cluster_ncc_ips_json TEXT NOT NULL DEFAULT '[]',
    legacy_global       INTEGER NOT NULL DEFAULT 0,  -- pre-existing PE-1/PE-4/RR-SA-2 etc.
    monitoring_json     TEXT NOT NULL DEFAULT '{}',  -- per-subsystem state (see 3.4)
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);

CREATE INDEX idx_monitored_ip ON monitored_devices(management_ip);

CREATE TABLE monitored_references (
    key             TEXT NOT NULL,
    username        TEXT NOT NULL,
    scope_type      TEXT NOT NULL,              -- "topology" | "domain"
    scope_id        TEXT NOT NULL,              -- "<sec_id>/<file>" or "<domain_id>"
    device_label    TEXT NOT NULL DEFAULT '',
    attached_at     TEXT NOT NULL,
    PRIMARY KEY (key, username, scope_type, scope_id),
    FOREIGN KEY (key) REFERENCES monitored_devices(key) ON DELETE CASCADE
);

CREATE INDEX idx_ref_user ON monitored_references(username);
CREATE INDEX idx_ref_key  ON monitored_references(key);

CREATE TABLE monitored_audit (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT NOT NULL,
    actor       TEXT NOT NULL,
    action      TEXT NOT NULL,                  -- "register" | "attach" | "detach" | "stop_monitor" | "credentials_update"
    key         TEXT,
    payload_json TEXT
);
```

### 3.3 Identity rule

The canonical key is `(management_ip, serial_number)`. Hostname is a **label**
and may legitimately differ between users (one user calls it `PE-4`, another
calls it `YOR_CL_PE-4` -- the SCALER `aliases` array already accommodates
this). When `serial_number == ""` (e.g., GI mode at first attach) we accept
`management_ip|""` as a temporary key and **upgrade** it to `management_ip|SN`
on the first successful probe. Conflict: if a user later attaches with the
same IP but a *different* SN (genuine device replacement), the verifier emits
the existing `serial_changed` alert (already wired by `extract_configs.sh`).

### 3.4 `monitoring_json` shape

```jsonc
{
  "config_extract": {
    "enabled": true,
    "last_run": "2026-05-05T12:00:00Z",
    "owner": "scaler:extract_configs.sh",   // who runs it
    "status": "ok|stale|failed"
  },
  "discovery_lldp": {
    "enabled": true,
    "last_run": "2026-05-05T11:55:00Z",
    "owner": "network-mapper",
    "task_id": "nm-disc-1234"
  },
  "subif_description": {
    "enabled": true,
    "last_run": "2026-05-05T11:55:00Z",
    "owner": "scaler:subif_monitor.py"      // see 6.3 (open question)
  },
  "link_telemetry": {
    "enabled": true,
    "owner": "topology:link_telemetry",     // on-demand, not background
    "last_seen_request": "2026-05-05T11:50:00Z"
  },
  "alarms_health": {
    "enabled": true,
    "owner": "scaler:extract_configs.sh:integrity",
    "last_run": "2026-05-05T12:00:00Z"
  }
}
```

## 4. The seven endpoints

All paths are mounted in `scaler_bridge.py` and proxied through `serve.py`.
Every handler MUST call `_require_auth()` (or its FastAPI equivalent
`Depends(get_current_user)`) before any DB access. **No exceptions.**

### 4.1 `POST /api/devices/verify-and-register`

**Purpose:** when the SSH dialog is saved with a new IP, the backend probes
the device, captures `(ip, sn, hostname, platform, is_cluster)`, upserts the
shared registry record, and creates the caller's first reference.

**Note:** this composes with the existing `POST /api/devices/{device_id}/verify-credentials`
in `routes/devices.py` -- we **call** that endpoint internally (after JWT
re-resolution) and on `ok=True` we run the upsert + reference + dispatch
flow. We do NOT duplicate the SSH probe logic.

Request body:

```json
{
  "device_label": "PE-4",
  "host": "100.64.10.22",
  "user": "dnroot",
  "password": "dnroot",
  "discovery_depth": "standard",
  "monitor_cadence": "fast_initial",
  "scope_type": "topology",
  "scope_id": "sec_1771858364/lab.json",
  "scope_label": "Yarel - lab.json"
}
```

Response (200):

```json
{
  "status": "ok",
  "newly_created": true,
  "smooth_ztp": false,
  "key": "100.64.10.22|WKZ1AB001",
  "record": {
    "management_ip": "100.64.10.22",
    "serial_number": "WKZ1AB001",
    "hostname": "YOR_CL_PE-4",
    "platform": "CL-86",
    "is_cluster": true,
    "monitoring": { /* monitoring_json */ },
    "references_count": 1
  },
  "message": "Verified -- DNOS cluster, active NCC = ncc-0. Monitoring with fast_initial."
}
```

**Smooth ZTP variant:** if `find_by_ip(host)` already returns a record AND the
caller did not pass an explicit `password`, we skip the SSH probe entirely
and return `smooth_ztp: true, newly_created: false` plus the cached
hostname/platform/interfaces. The frontend pre-fills the credentials panel.

Error responses:

- 400 invalid body
- 401 no JWT
- 422 verify failed (`auth_failed`, `port_closed`, `ghost_ip`,
  `identity_mismatch`, `timeout`, `error`); body matches the existing
  verify-credentials shape so the SSH dialog can render the same status pill

### 4.2 `POST /api/devices/monitored/attach`

**Purpose:** add a reference for a device that is already in the registry --
the smooth-ZTP "I'm using this on a second canvas" path.

Request body:

```json
{
  "key": "100.64.10.22|WKZ1AB001",
  "scope_type": "topology",
  "scope_id": "sec_1771858364/lab.json",
  "scope_label": "Yarel - lab.json",
  "device_label": "PE-4"
}
```

Response (200):

```json
{
  "status": "ok",
  "added": true,                  // false if (user, scope) already referenced
  "references_count": 2,
  "record": { /* same shape as 4.1.record */ }
}
```

### 4.3 `DELETE /api/devices/monitored/{key}/reference`

**Purpose:** decrement the reference count. The body is required to identify
which scope is being detached (a user may have multiple topologies referencing
the same device).

Request body:

```json
{
  "scope_type": "topology",
  "scope_id": "sec_1771858364/lab.json",
  "ack_stop_monitoring": false   // see below
}
```

Response (200):

```json
{
  "status": "ok",
  "removed": true,
  "references_count": 1,
  "needs_user_confirmation": false,
  "would_stop_monitoring": false
}
```

**Last-referencer flow:** the handler computes:

```python
all_refs = registry.list_references(key)
my_refs  = [r for r in all_refs if r.username == current_user]
is_last  = len(all_refs) == 1 and len(my_refs) == 1
```

- If `is_last is False`: detach silently, return `needs_user_confirmation: false`.
- If `is_last is True` and `ack_stop_monitoring is False`: do **NOT** detach,
  return:

  ```json
  {
    "status": "needs_confirmation",
    "needs_user_confirmation": true,
    "would_stop_monitoring": true,
    "references_count": 1,
    "message": "You are the last user referencing this device. Detaching will stop background monitoring. Re-call with ack_stop_monitoring=true to proceed."
  }
  ```

- If `is_last is True` and `ack_stop_monitoring is True`: detach + emit a
  best-effort stop-monitoring dispatch (`monitored_dispatch.tear_down(key)`)
  + audit log.

The frontend uses `would_stop_monitoring` to gate the "are you sure?" modal.

### 4.4 `GET /api/devices/monitored/{key}`

Returns the full record + this user's reference list (other users redacted).

Response (200):

```json
{
  "key": "100.64.10.22|WKZ1AB001",
  "record": { /* full record */ },
  "my_references": [
    { "scope_type": "topology", "scope_id": "...", "device_label": "PE-4" }
  ],
  "references_count_total": 3,
  "is_only_my_references": false
}
```

### 4.5 `GET /api/devices/monitored`

Returns all records this user has at least one reference to. Used by the
canvas to bulk-hydrate device cards on topology load.

### 4.6 `PUT /api/devices/monitored/{key}/credentials`

Updates the per-user credential override. **Always** routed through the
existing `PUT /api/auth/me/device-credentials/{device_id}` writer in
`api/auth/router.py` so we don't fork the credential storage path. This
endpoint is a thin alias whose only job is to use the registry `key`
instead of the device's display label as the lookup -- a frontend
convenience.

### 4.7 `POST /api/devices/monitored/cleanup-stale`

Admin-only. Iterates every record with `references_count == 0` (e.g.,
because a topology was deleted without going through the detach path) and
runs `tear_down`. Hourly cron via systemd timer (Phase 4).

## 5. Verification protocol

We DO NOT reinvent verification. The chain is:

```
SSH dialog Save   -->   POST /api/devices/verify-and-register
                         |
                         |  (1) call existing
                         |      POST /api/devices/{device_label}/verify-credentials
                         |      (already does verify-identity + probe + ops_writer)
                         v
                         |  (2) on ok=True, read fresh operational.json:
                         |        management_ip = ops["mgmt_ip"]
                         |        serial_number = ops["serial_number"]
                         |        hostname      = ops["actual_hostname"] or ops["expected_hostname"]
                         |        platform      = ops["system_type"]
                         |        is_cluster    = bool(ops.get("cluster_active_ncc") is not None)
                         v
                         |  (3) registry.upsert_record(...)
                         v
                         |  (4) registry.add_reference(key, username, scope_type, scope_id)
                         v
                         |  (5) monitored_dispatch.bring_up(key, record):
                         |        - mirror to ${SCALER_DEVICES_FILE}
                         |        - call MCP discover_device(ip, user, pass)
                         |        - prime sub-IF description cache (best-effort)
                         |        - emit monitored_audit row
                         v
                         |  (6) return record + first-reference response
```

The `_resolve_app_user` -> `_get_credentials` chain in `routes/_device_comm.py`
already picks up per-user creds when the bridge later runs SSH for monitoring,
so no additional credential plumbing is needed.

## 6. How each subsystem picks up the new device

| Subsystem | Mechanism today | What dispatch does |
|---|---|---|
| **6.1 Config extraction** | `extract_configs.sh` runs every 5 min via cron, reads `${SCALER_DEVICES_FILE}` (default `~/SCALER/db/devices.json`), greps each device's `hostname` + `ip`, runs the SSH expect script. | **Mirror write** to `${SCALER_DEVICES_FILE}` adding the new device with `hostname`, `ip`, `username=dnroot`, `password=ZG5yb290` (b64). The next cron tick (<5 min) picks it up. No process to start. |
| **6.2 Network Mapper discovery (LLDP / intf / system-info)** | `user-network-mapper` MCP server owns its own DB; `dnos_list_devices` reads it; `dnos_dnaas_*` reads `~/SCALER/db/configs/<host>/running.txt` (kept fresh by 6.1). | Call MCP `discover_device(hostname=<ip>, username, password)`. This fans out -- adds to NM DB, runs initial show commands, captures LLDP. Subsequent `refresh_device` is scheduled by the existing **layered device-mode resolver** in `routes/_device_mode_resolver.py` (already runs `inflight 45s / watcher 15s / global 300s` polling). |
| **6.3 Sub-IF description telemetry (used by `dnos_dnaas_describe_path`)** | `dnos_dnaas_describe_path` reads from a per-host description cache populated by SCALER monitor. The exact monitor script is **TBD** -- see Open Question OQ-1 below. The cache is in-process for `dnaas_cache.py` and per-host on disk; the description part is read via `cache_mod.get_subif_description(hostname, subif)`. | If the monitor reads from `~/SCALER/db/configs/<host>/running.txt`, then 6.1 covers it implicitly. Confirm in Phase 2 by tracing where `get_subif_description` actually loads the per-subif description. |
| **6.4 Live link telemetry** | `routes/link_telemetry.py` is **on-demand**: the canvas calls `POST /api/link-telemetry/refresh` for each link. The provider reads via `DeviceCommHelper`, which uses `_get_credentials` (per-user). | No background work needed. The new device just needs valid per-user credentials in `~/.topology_users/<u>/devices.json` -- the existing `PUT /api/auth/me/device-credentials/{id}` already covers this. |
| **6.5 Alarms / health** | `extract_configs.sh` integrity-checks (hostname-mismatch, serial-changed, IP-changed, stale_data, recovery-mode) write to `~/SCALER/db/alerts.json`. | Same as 6.1 -- the moment the device is in `${SCALER_DEVICES_FILE}`, alerts cascade in. |

**Net effect:** mirroring to `${SCALER_DEVICES_FILE}` + one MCP `discover_device`
call covers 4 of 5 subsystems out of the box. The fifth (sub-IF description)
needs Phase-2 verification.

### 6.6 Lab profile awareness

`monitored_dispatch.bring_up` reads `${SCALER_DEVICES_FILE}` from the
process env (set by `lab_profile.py show --profile active`). When a user is
on a non-default lab profile we mirror to **that** profile's `devices.json`,
not the global one. Per-user `monitored_devices.json` and the shared
registry DB are profile-agnostic (a serial number is a serial number).

## 7. Toolbar parity on monitor-on

The user reported that a freshly-placed NCP device renders a **truncated**
floating selection toolbar compared to what fully monitored devices like
PE-1 / PE-4 / RR-SA-2 show. This section closes the frontend half of that gap
so that **the moment verify-and-register returns success, the canvas card
re-renders the toolbar with the full monitored button set** -- without the
user clicking anywhere.

### 7.1 The visible-state contract

The floating selection toolbar is rendered exclusively by
`showDeviceSelectionToolbar(editor, device)` in
`topology/topology-device-toolbar.js` (single 580-line file, single function).
The contract this design imposes on Phase 2:

1. `verify-and-register` returns success -> the dialog handler MUST set
   `device.sshConfig.{host,user,password}` (already happens today via
   `ScalerAPI.saveDeviceCredentials`) **and** stamp `device._sshReachable =
   true; device._sshReachableAt = Date.now()` (today this is set only by
   the legacy `probeAndShowMethods` path).
2. After stamping, fire `window.dispatchEvent(new CustomEvent(
   'device:context-updated', { detail: { deviceId, device } }))`. The toolbar
   already subscribes to that event (`topology-device-toolbar.js` lines
   528-539); receiving it triggers `hideDeviceSelectionToolbar` ->
   `showDeviceSelectionToolbar` so the new gate is re-evaluated and the
   missing buttons appear.
3. The MVP MUST NOT introduce a new event type -- reuse
   `device:context-updated`. Adding a parallel `device:monitor-registered`
   would split listeners across modules and is unnecessary because the
   existing event already implies "this device just got new context, every
   subscriber should refresh."

Two subtle invariants:

- `_sshReachable` and `hasSshCredentials` are **separate gates**, by design.
  `hasSshCredentials` is a *config* check (`sshConfig.host && .user &&
  .password` are populated). `_sshReachable` is a *runtime* check (the last
  probe / verify actually succeeded). The toolbar today gates LLDP + System
  Stack on `hasSshCredentials` only -- this means even an unverified device
  shows those buttons the second a password is typed-and-saved (LLDP click
  would then 401). Phase 2 should tighten this: LLDP + Stack render only
  when `hasSshCredentials && _sshReachable` (see OQ-7 below).
- Smooth-ZTP (Section 4.1 cached path) MUST hydrate both gates in the same
  tick: when the canvas card's IP matches a registry record, the dispatch
  must populate `sshConfig` from per-user credentials AND stamp
  `_sshReachable = true` from the registry's last successful probe (the
  registry already records `last_seen_ok` per the schema in Section 3).

### 7.2 Audit of current canvas selection toolbar

The canonical render is `topology/topology-device-toolbar.js`. Every
button rendered by that function is in the table below. The "X icon"
column reflects the icon registry name passed to `editor._createIconSvg(...)`
in `topology/index.html` (the LLDP icon is an inline `<svg>` rather than a
registry lookup, hence the dash). The "Code line" column points at the
button's exact append site so the implementer can audit gate edits later.

| # | Button | Icon | Handler | Gate condition | On unmonitored NCP? | On PE-1 (monitored)? | After monitor=on? | Code line |
|---|---|---|---|---|---|---|---|---|
| 1 | Rename | `edit` | `editor.showInlineDeviceRename(device)` | always | yes | yes | unchanged | 296 |
| 2 | SSH / Console | `terminal` (or `console` if last method was console / device in GI/RECOVERY) | `editor.showSSHAddressDialog(device)` | always; **green inset ring** if `_sshReachable && age <= 10 min`, **amber ring** if `age <= 2 h`, no ring otherwise | yes (no ring) | yes (green ring) | **ring flips to green** as `_sshReachable=true` is stamped by the verify response | 326-354 |
| 3 | LLDP scan | inline SVG (circle + 2 arcs) | `editor._showLldpInlineSubmenu(...)` | `hasSshCredentials = sshConfig.host && .user && .password` | **NO** (gate fails) | yes | **YES -- appears once creds saved** | 358-433 |
| 4 | System Stack | `layers` | `editor._showSystemStackInlineSubmenu(...)` | `hasSshCredentials` (same as LLDP) | **NO** (gate fails) | yes | **YES -- appears once creds saved** | 436-447 |
| 5 | Style | `router` | `editor.showDeviceStylePalette(device)` | always | yes | yes | unchanged | 454 |
| 6 | Color | `palette` | `editor.showColorPalettePopupFromToolbar(...)` | always | yes | yes | unchanged | 458 |
| 7 | Label Style | `text` | `editor.showDeviceLabelStyleMenu(...)` | always | yes | yes | unchanged | 462 |
| 8 | Duplicate | `copy` | `editor.duplicateObject(device, false)` | always | yes | yes | unchanged | 470 |
| 9 | Copy Style | `brush` | `editor.copyObjectStyle(device)` | always | yes | yes | unchanged | 475 |
| 10 | Lock / Unlock | `lock` / `unlock` (toggles) | toggles `device.locked` | always | yes | yes | unchanged | 482 |
| 11 | Layer (z-order) | layer badge text (e.g. `20`) + dropdown | `applyLayerAction(...)` | always | yes | yes | unchanged | 490 |
| 12 | Group | `group` | `window.ObjectGroupPopover.toggleFor(...)` | `window.ObjectGroupPopover` defined (always true once bundle loaded) | yes | yes | unchanged | 496-501 |
| 13 | Delete | `trash` (red) | `editor.deleteSelected()` | always | yes | yes | unchanged | 507-510 |

**Bottom line: the delta is exactly 2 buttons (LLDP + System Stack).** Both
are gated solely on `hasSshCredentials`. Closing the parity gap is therefore
a config-side fix (persist credentials -> gate flips true) plus the
re-render trigger from 7.3.

> **Caveat for the implementer.** Some operator-facing capabilities the user
> may *expect* on a monitored card -- live config view, alarms / health pill,
> sub-IF description drift, link-telemetry inspector, DNAAS / inverse-path,
> cluster-NCC console picker -- are **not** on the canvas selection toolbar
> today. They live in separate UI surfaces (the SSH dialog's submenus,
> right-click context menu in `topology-context-menu-handlers.js`, link
> toolbar, scaler GUI rack view). Adding any of those to the floating
> selection toolbar is **out of scope** for the MVP and tracked under OQ-6.

### 7.3 Render trigger

The reactive plumbing already exists:

```
DeviceMonitor.refreshDeviceContext(device)
        |
        |  (mode/identity/git_commit fetched)
        v
window.dispatchEvent(new CustomEvent('device:context-updated', {
    detail: { deviceId, device }
}))
        |
        v
showDeviceSelectionToolbar()'s registered listener
(topology-device-toolbar.js:539)
        |
        v
hideDeviceSelectionToolbar(editor) + showDeviceSelectionToolbar(editor, d)
```

Phase 2 just plugs the verify-and-register response into the **same** event:

```js
// in topology-ssh-dialog.js, after a successful POST /api/devices/verify-and-register
ScalerAPI.verifyAndRegister(deviceId, host, user, pass).then((res) => {
    if (!res.ok) return;            // verify failed -- handled in 7.5
    device.sshConfig = device.sshConfig || {};
    device.sshConfig.host = host;
    device.sshConfig.user = user;
    device.sshConfig.password = pass;
    device._sshReachable = true;
    device._sshReachableAt = Date.now();
    device._monitorRegistered = true;          // NEW informational flag
    device._monitorRegisteredAt = Date.now();
    if (res.legacy_global)  device._monitorLegacyGlobal = true;
    if (res.smooth_ztp)     device._monitorSmoothZtp    = true;
    window.dispatchEvent(new CustomEvent('device:context-updated', {
        detail: { deviceId, device, source: 'verify-and-register' }
    }));
});
```

`source: 'verify-and-register'` is purely diagnostic (lets us grep the
console for these refreshes in dev). The toolbar re-render handler does not
branch on it.

`closeDialog()` in `topology-ssh-dialog.js:632-638` already calls
`showDeviceSelectionToolbar(device)` directly **after** save -- so a
verify-and-register that finishes BEFORE the dialog closes also works. The
event-driven path is the safety net for verify-and-register completing
**after** the dialog already closed (e.g. user clicked Save and immediately
clicked elsewhere on the canvas; the toolbar may have been hidden, but if
the user later re-selects the same device it must show the full set).

### 7.4 Smooth-ZTP toolbar -- first-paint must be full

When a user drops a device whose mgmt-IP already exists in the registry, the
canvas card MUST be hydrated **before** any toolbar is rendered. The order is:

1. `topology-devices.js::addAtPosition(x, y, ip)` calls
   `ScalerAPI.getMonitored(ip)` (cached path -- Section 4.1).
2. The response populates `device.sshConfig`, `device.label` (hostname),
   `device._systemType`, `device._sshReachable`, `device._sshReachableAt`,
   `device._monitorRegistered`.
3. ONLY THEN does `topology-mouse-up.js` -> `editor.showDeviceSelectionToolbar`
   fire on next selection.

**Consequence:** the smooth-ZTP card paints with all 13 buttons on first
selection -- no progressive reveal where LLDP / Stack pop in 200 ms later.
Implementer note: do not be tempted to delay the smooth-ZTP hydrate until
the user opens the SSH dialog. The whole point of smooth-ZTP is "this
device is already monitored; act like it."

If `getMonitored` fails (registry endpoint down, network blip), the card
falls back to the unmonitored render with a non-blocking toast `"Could not
reach monitored-device registry; functioning offline."` -- the canvas card
is still usable as a topology element; toolbar is the truncated 11-button
set; LLDP / Stack fail-soft because `hasSshCredentials` is false. **Do not
silently ignore the registry failure.**

### 7.5 Failure modes

| Failure mode | Toolbar behavior | Where rendered | Notes |
|---|---|---|---|
| Credentials saved but `verify-and-register` returns `ok=false, reason=ssh_auth_failed` | Stay at 11 buttons (LLDP / Stack hidden). The credential-save dialog renders the failure inline via `renderVerifyStatus('error', ...)`. **Do not stamp `_sshReachable=true`** even though `hasSshCredentials` is technically true. | `topology-ssh-dialog.js::renderVerifyStatus` already exists | This is why OQ-7 recommends tightening the LLDP / Stack gate to `hasSshCredentials && _sshReachable`. Without that tightening, the user gets the misleading full toolbar where every monitored button 401s on click. |
| Verify succeeds, register succeeds, but a downstream subsystem (config extract, MCP discover) is broken | Render the full 13 buttons. Per-button error state surfaces inline when the user actually clicks. E.g. config-view button shows "config not yet collected (next extract in 4 min)" -- not "missing". | per-button error path in submenu handlers | The toolbar is a control surface, not a status board. The Monitoring pill (Section 12 file inventory, `styles.css` row) is the right place to surface "subsystem X is degraded". |
| User edits credentials on a previously-monitored device with NEW credentials that fail | Toolbar reverts to 11-button minimal. Set `device._sshReachable = false` and clear `device._sshReachableAt`. Monitoring state pill shows `"credentials_invalid"` with an inline `Edit` button. | new pill state | Do not silently keep the full 13 buttons. The user just told us their new password is wrong; pretending nothing happened is misleading. |
| Smooth-ZTP `getMonitored` returns 404 (registry has the IP but registration was torn down) | Render 11-button minimal, toast `"Device registration is no longer active. Click SSH to re-register."` | `topology-devices.js::addAtPosition` | This is the same render as a brand-new drop. |
| `verify-and-register` returns `ok=true` but `mode=GI` or `mode=RECOVERY` (per `topology-device-mode-gate.js`) | Render the full 13 buttons but the SSH icon shows the orange/red mode badge per existing `isModeAlert` code (lines 341-350). LLDP submenu handler internally returns "device in GI/RECOVERY -- discovery skipped" without crashing. | already implemented in toolbar; submenu handlers must respect the gate | The mode-gate logic is independent of the registry; both sources of truth coexist. |

## 8. Removal UX (frontend contract)

The canvas calls `DELETE .../reference` always. The backend tells the
frontend whether it needs to ask the user:

```js
// Frontend pseudo-code in topology-devices.js detachDevice():
const r = await ScalerAPI.detachMonitoredReference(key, scope, /*ack*/ false);

if (r.needs_user_confirmation && r.would_stop_monitoring) {
    const yes = await editor.confirmModal({
        title: 'Stop monitoring this device?',
        body:  `You are the last user referencing ${device.label}. ` +
               `Detaching will stop background monitoring (config extract, ` +
               `LLDP discovery, telemetry).`,
        ok: 'Stop monitoring + remove',
        cancel: 'Keep on canvas',
    });
    if (yes) {
        await ScalerAPI.detachMonitoredReference(key, scope, /*ack*/ true);
        editor.removeDevice(device);
    }
    // else: leave the canvas card alone
} else {
    // Silent path: another user (or another of our own topologies) is
    // still referencing it -- detaching just drops our reference.
    editor.removeDevice(device);
}
```

## 9. Multi-user safety checklist

- [x] All seven endpoints sit behind `_require_auth()` / `Depends(get_current_user)`.
- [x] Per-user references file lives under `user_store.user_data_path(username, "monitored_devices.json")`.
- [x] Shared registry uses `topology/api/device_state.py`'s WAL + busy_timeout=5000 pattern.
- [x] `~/SCALER/db/devices.json` mirror writer takes a `threading.Lock` and uses `os.replace` for atomic write.
- [x] `monitored_references` row PK includes `username` so user A's detach can never delete user B's reference.
- [x] `GET /api/devices/monitored/{key}` redacts other users' references; only `references_count_total` is exposed.
- [x] No new `expanduser("~/.topology_*")` paths outside `user_store.user_data_path` (PR-gate grep clean).
- [x] No new `/tmp/...` shared files.

## 10. Backward compatibility / migration

PE-1 / PE-4 / RR-SA-2 / DNAAS-LEAF-* / DNAAS-SPINE-* are already in
`~/SCALER/db/devices.json` and have no registry entry. On Phase-2 first boot
of the new module:

1. `monitored_registry.py::backfill_legacy()` reads `${SCALER_DEVICES_FILE}`.
2. For each device with `last_sync` set, upsert with
   `legacy_global=True, references=[]`.
3. The reference-count detach logic checks `legacy_global` first -- a record
   with `legacy_global=True` is **never** torn down even when
   `references_count == 0`. That preserves the lab-shared baseline.
4. The next time a user attaches PE-1 on their canvas, an attach-reference
   call adds their reference but does NOT change `legacy_global`. Detach
   from the last user therefore drops their reference but keeps monitoring.

Migration is idempotent and fully read-only against `~/SCALER/db/devices.json`
on the first pass (no writes until a user actually attaches/detaches).

## 11. MVP slice for Phase 2

**Status: SHIPPED 2026-05-05.** See Section 14 for the post-ship summary
(file-by-file change list, test results, multi-user audit, end-to-end
test chain). The implemented surface intentionally went *beyond* the
original "smallest vertical slice" because the OQ-7 toolbar gate fix
required tightening the gate _and_ smooth-ZTP hydration in the same
ship to avoid a flicker on legacy devices (PE-1 / PE-4 / RR-SA-2).

**Original smallest vertical slice (kept for design context):**

`POST /api/devices/verify-and-register` end-to-end + a thin frontend hook
in `topology-ssh-dialog.js` that calls it on save (alongside the existing
`saveDeviceCredentials`) **and emits a `device:context-updated` event the
toolbar bundle already subscribes to (per Section 7.3) so the LLDP +
System Stack buttons appear without the user clicking anywhere**. The
handler:

1. Calls existing `verify-credentials` internally.
2. On success, writes the registry row + this user's first reference.
3. Mirrors to `${SCALER_DEVICES_FILE}` (so the 5-min cron picks it up).
4. Returns a structured response so the dialog renders a "[OK] Monitoring
   started" toast.
5. The frontend hook stamps `device._sshReachable=true`,
   `device._sshReachableAt=Date.now()`, `device._monitorRegistered=true`
   on success and dispatches `device:context-updated` -- this triggers the
   toolbar parity refresh described in Section 7.

**Out of scope for the MVP:**

- Ref-count attach/detach (4.2, 4.3)
- Smooth-ZTP pre-fill (4.1 cached path)
- Sub-IF description warm-pass dispatch (6.3)
- Network Mapper `discover_device` call (we leave this to layered resolver
  picking up the device on next tick)
- Last-referencer modal
- Backfill of legacy globals (devices stay implicitly legacy until first
  attach by anyone)
- Tightening LLDP / Stack toolbar gate to `hasSshCredentials &&
  _sshReachable` (recommended by OQ-7 but a safe deferral -- the existing
  gate is at-worst misleading, never crashing)
- Adding extra toolbar buttons (config view, alarms pill, link telemetry,
  DNAAS path) -- see OQ-6

Effort: **medium (5-7 hours)** -- 4-6h for the backend slice + ~1h for the
frontend toolbar parity wiring (set the three flags on the device object
and dispatch one event; the toolbar's existing `device:context-updated`
listener handles the rest).

## 12. Open questions

- **OQ-1: sub-IF description monitor location.** `dnos_dnaas_describe_path`
  in `dnos_config_mcp/dnaas.py` calls
  `cache_mod.get_subif_description(hostname, subif)`. We need to confirm
  whether that cache is populated by `extract_configs.sh` (sub-IF
  descriptions are in the running.txt it pulls every 5 min) or by a
  separate script. If it is the former, 6.3 is automatic. If the latter,
  Phase 2 must locate that script and document its device list source.

- **OQ-2: DNAAS leaves use `sisaev/Drive1234!` not `dnroot/dnroot`.** The
  `_classify_device_profile` heuristic in `bridge_helpers.py` already
  routes those to the lab DNAAS chain. Question: when a user drags a
  *new* DNAAS leaf onto the canvas, do we want the verify step to try
  the DNAAS chain automatically (yes -- the existing
  `_get_lab_credential_chain(hint_label)` does this) or always require
  the operator to type the password? Recommendation: yes, automatic, but
  surface the chosen profile in the response (`credential_profile: "dnaas_leaves"`).

- **OQ-3: Cluster identity.** A cluster like PE-4 (CL-86) has TWO mgmt IPs
  for the two NCCs. Today's `~/SCALER/db/devices.json` solves this via
  `mgmt_ncc_0_ip` / `mgmt_ncc_1_ip` + `cluster_active_ncc`. The registry
  key is `(management_ip, serial_number)` -- which IP do we key on? The
  recommendation: key on the **chassis** mgmt IP (the one in the top-level
  `ip` field, e.g., `100.64.10.22` for `YOR_CL_PE-4`); store the per-NCC
  IPs inside `cluster_ncc_ips_json`. A user attaching either per-NCC IP
  is resolved to the chassis key during verify (the probe returns the
  chassis identity). Confirm with user.

- **OQ-4: Domain-scope vs topology-scope references.** A topology can be
  shared (existing `shared_topologies` mechanism). When user A shares a
  topology with user B, does user B implicitly inherit a reference, or
  must B explicitly attach? Recommendation: **explicit attach** -- the
  shared-topology mechanism already handles "view someone else's
  topology"; attaching is a *deployment* gesture that says "I want this
  monitored on my own behalf too." Confirm.

- **OQ-5: Auto-detach when topology file is deleted.** Today's topology
  delete path doesn't know about `monitored_devices.json`. We have two
  choices: (a) hook the topology-file-delete handler in
  `serve.py::_section_dir` to call `detach_reference` for every device
  on the topology, or (b) lazy cleanup via the hourly `cleanup-stale`
  endpoint (4.7). Recommendation: **both**. (a) is correct; (b) is the
  safety net for crashes / external deletes.

- **OQ-6: Should monitored devices get *more* toolbar buttons than today?**
  The Section 7.2 audit shows the canvas selection toolbar has 13 buttons
  total; the unmonitored-vs-monitored delta is only 2 (LLDP + System
  Stack). The user's screenshot critique implied a much larger button set
  on PE-1 / PE-4 / RR-SA-2 -- possibly conflating other UI surfaces (SSH
  dialog submenus, link toolbar, scaler GUI rack view). Should Phase 2
  add new canvas-toolbar buttons for: (a) live config view (one click ->
  the running.txt the cron pulled), (b) an alarms / health pill that
  reads from `~/SCALER/db/alerts.json`, (c) link-telemetry inspector
  (already exists on the link toolbar; redundant on device card?), (d)
  sub-IF description drift indicator, (e) DNAAS path / inverse-path
  shortcut, (f) cluster-NCC console picker for cluster devices (today's
  SSH dialog handles this in a submenu). Recommendation: **defer all of
  the above to Phase 5** so the MVP stays scoped to "the 2 currently
  gated buttons appear automatically". Confirm with user before any of
  (a)-(f) lands.

- **OQ-7: Tighten the LLDP / System Stack gate.** Today the gate is
  `hasSshCredentials = sshConfig.host && .user && .password`. That goes
  true the moment a user types a password and clicks Save -- even when
  the verify call subsequently fails with `auth_failed`. Recommendation:
  change the gate to `hasSshCredentials && _sshReachable`. This is one
  line in `topology-device-toolbar.js:357`. Risk: legacy global devices
  (PE-1, PE-4, RR-SA-2) loaded from the topology JSON may not have
  `_sshReachable` populated until the device-monitor refresh tick runs
  -- so the user might briefly see the truncated toolbar on first paint
  for known-good devices. Mitigation: when smooth-ZTP hydrates from the
  registry, stamp `_sshReachable` from `last_seen_ok` so the first paint
  is correct. If `last_seen_ok` is older than the 2-hour stale window,
  render the truncated toolbar with an inline "verify now" call-to-action
  (re-uses `renderVerifyStatus` from the SSH dialog). Confirm.

---

## 13. File inventory (Phase 2 implementation backlog)

**Backend (Python)**

| File | Status | Change |
|---|---|---|
| `topology/api/auth/user_store.py` | edit | add `user_monitored_devices_path(username)` helper |
| `topology/api/monitored_registry.py` | new | SQLite registry DAL (the 4 tables + helpers) |
| `topology/routes/monitored_devices.py` | new | the 7 FastAPI endpoints |
| `topology/routes/monitored_dispatch.py` | new | bring_up/tear_down hooks per subsystem |
| `topology/scaler_bridge.py` | edit | mount `monitored_devices_router` |
| `topology/serve.py` | edit | proxy `/api/devices/monitored/*` and `/api/devices/verify-and-register` to bridge |
| `topology/routes/devices.py` | edit | refactor `verify-credentials` to expose a callable function (not just an endpoint) for internal reuse |
| `topology/routes/bridge_helpers.py` | edit | tiny: `_get_credentials` already covers per-user; add a `find_lab_devices_file()` helper that honours `${SCALER_DEVICES_FILE}` |
| `topology/api/migrations/backfill_monitored.py` | new | one-shot legacy backfill (idempotent) |

**Frontend (JS)**

| File | Status | Change |
|---|---|---|
| `topology/topology-ssh-dialog.js` | edit | call `verifyAndRegister` after `saveDeviceCredentials` on Save; on success stamp `_sshReachable=true`, `_sshReachableAt=Date.now()`, `_monitorRegistered=true` and dispatch `device:context-updated`; render new monitoring-started status |
| `topology/scaler-api.js` | edit | add `verifyAndRegister`, `attachMonitoredReference`, `detachMonitoredReference`, `getMonitored`, `listMonitored` |
| `topology/scaler-gui-devices.js` | edit | hydrate canvas device cards from `listMonitored` response on topology load (smooth ZTP pre-fill) |
| `topology/topology-devices.js` | edit | `addAtPosition` -> if dropped on canvas with a known IP, fetch from registry and pre-fill `sshConfig`, stamp `_sshReachable` from `last_seen_ok`, dispatch `device:context-updated` so the toolbar paints with the full set on first selection |
| `topology/topology.js` | edit | wire detach modal to `detachMonitoredReference` flow (uses `would_stop_monitoring`) |
| `topology/topology-device-monitor.js` | edit (small) | when a device card is added, hit `attachMonitoredReference` once; when removed, hit `detachMonitoredReference`. Also: on `_loadDeviceContext` success when `legacy_global=true` is detected from registry, stamp `device._monitorLegacyGlobal=true` for Section 7 transparency (purely informational). |
| `topology/topology-device-toolbar.js` | edit (one-line, optional / OQ-7 driven) | tighten LLDP + System Stack gate from `hasSshCredentials` to `hasSshCredentials && _sshReachable` (line 357). NO new buttons added in Phase 2. NO new event subscriber added -- the existing `device:context-updated` listener (lines 528-539) already handles toolbar refresh. |
| `topology/topology-toolbar-setup.js` | none | toolbar setup orchestration -- no toolbar parity changes touch this file (it sets up the *editor toolbar* across the top of the canvas, not the floating per-device selection toolbar). Listed here only to confirm we audited it and ruled it out. |
| `topology/topology-toolbar.js` | none | same -- editor-level toolbar; not the per-device floating toolbar. |
| `topology/index.html` | edit | bump cache-buster `?v=` for every edited JS/CSS file |
| `topology/styles.css` | maybe | small: a "Monitoring" pill on device cards (Section 7.5 references this for "credentials_invalid" / "subsystem_degraded" inline state) |

**Frontend (no new files)**

The toolbar parity slice does NOT introduce a new JS file. Specifically:

- No new `topology-monitor-event.js` -- the `device:context-updated`
  CustomEvent already exists (`topology-device-monitor.js:362,630` dispatch
  it; `topology-device-toolbar.js:539`, `topology-lldp-dialog.js:194`,
  `topology-stack-dialog.js:222` subscribe). Reuse, don't fork.
- No new render-hook helper -- the toolbar's existing
  `refreshOnContext` closure (`topology-device-toolbar.js:528-539`) does
  the right hide-then-reshow; we just need to fire the event from one
  more code path (the verify-and-register success handler).

**Shared / SCALER**

| File | Status | Change |
|---|---|---|
| `~/SCALER/extract_configs.sh` | none | already reads from `${SCALER_DEVICES_FILE}` -- our mirror writes to that file. Zero changes. |
| `~/SCALER/db/devices.json` | runtime data | NEVER touch directly during design. Phase-2 backfill is read-only on first pass. |
| `topology/scaler-api.js` (mirror notes) | n/a | covered above |

**Tests**

| File | Status | Change |
|---|---|---|
| `topology/tests/test_monitored_registry_unit.py` | new | unit-test the DAL: upsert, add/remove ref, last-referencer detection, audit log, legacy-global guard |
| `topology/tests/test_monitored_endpoints_unit.py` | new | FastAPI test client: 401 without JWT, 200 with JWT, ref-count math, smooth-ZTP path, per-user isolation |
| `topology/tests/smoke_monitored_e2e.py` | new | live API: end-to-end verify-and-register -> attach -> detach for two synthetic users; mirrors `smoke_per_user_ssh.py` style |
| `topology/scripts/audit_topology_state.py` | edit | add a section that audits `monitored_registry.db` schema + cross-checks per-user refs against existing user dirs |

---

## 14. Effort estimates

| Slice | Effort |
|---|---|
| Phase 2 MVP (verify-and-register + registry DAL + first-reference + mirror writer + **toolbar parity event hookup per Section 7.3**) | medium (5-7h) |
| Phase 3a -- attach/detach + last-referencer modal | small (2h) |
| Phase 3b -- smooth-ZTP pre-fill on canvas drop (includes Section 7.4 first-paint full toolbar invariant) | small (1-2h) |
| Phase 3c -- legacy backfill + cleanup-stale endpoint + admin tooling | small (1-2h) |
| Phase 4 -- sub-IF description warm pass + Network-Mapper `discover_device` integration | medium (3-4h) |
| Phase 5 -- frontend bundle integration into device cards (Monitoring pill, ZTP toast, modal styling, optional OQ-6 toolbar additions if user approves) | medium (2-3h) |
| **Total to ship feature-complete** | **medium-large (~15-21h)** |

---

## 15. Phase 2 MVP -- shipped (2026-05-05)

### Locked-in decisions

| ID | Decision | Reason |
|---|---|---|
| OQ-2 | DNAAS-leaf credential auto-routing **deferred** | MVP defaults to `dnroot/dnroot`; verify failure surfaces a clean reason so the operator edits creds. |
| OQ-3 | Cluster identity = **chassis mgmt IP** as canonical key; per-NCC IPs in `cluster_ncc_ips_json` | Matches today's `~/SCALER/db/devices.json` shape. Single SQLite row per cluster. |
| OQ-6 | **No new toolbar buttons** in MVP | Only the 2 already-gated buttons (LLDP + System Stack) + the SSH icon green ring. Bigger button set tracked for Phase 5. |
| OQ-7 | **Tighten gate to `hasSshCredentials && _sshReachable`** with smooth-ZTP hydrate | Without the hydrate we'd flicker on PE-1 / PE-4 / RR-SA-2 first paint. Both shipped together. |
| OQ-1, OQ-4, OQ-5 | Deferred to Phase 4+ | Out of scope for MVP. |

### File-by-file change list

| Path | Status | Lines (added/removed in this ship) | Purpose |
|---|---|---|---|
| `topology/api/auth/user_store.py` | edit | +helper | `user_monitored_devices_path(username)` per-user references-file path. |
| `topology/api/monitored_registry.py` | new | +704 | SQLite DAL (devices, references_tbl, monitoring_subsystems, audit_log) at `~/.topology_shared/monitored_registry.db`, WAL + busy_timeout=5000, **`isolation_level=None` autocommit** (matches `device_state.py`). |
| `topology/routes/monitored_devices.py` | new | +416 | FastAPI router, 5 endpoints: `verify-and-register`, `GET /monitored`, `GET /monitored/{ip}`, `POST /monitored/{ip}/attach`, `DELETE /monitored/{ip}/attach`. Each handler uses `_require_user(request)` and redacts other users via `_redact_users()`. |
| `topology/routes/monitored_dispatch.py` | new | dispatch hooks | `bring_up(record)` mirrors device into `${SCALER_DEVICES_FILE}` with file-lock + atomic write, best-effort `discover_device` POST to Network Mapper MCP, schedules other 3 subsystems via existing periodic loops. `tear_down(record)` removes mirror entries unless `legacy_global=True`. |
| `topology/scaler_bridge.py` | edit | +router mount | Mounts `monitored_devices.router`. |
| `topology/serve.py` | edit | +proxy routes | `do_GET` / `do_POST` / `do_DELETE` now forward `/api/devices/verify-and-register` and `/api/devices/monitored/*` (incl. `attach`) to the bridge. DELETE order: `/monitored/*/attach` checked **before** generic `/api/devices/<id>` catch-all. |
| `topology/routes/devices.py` | edit | +`verify_credentials_inline` | Existing `verify-credentials` route refactored to expose a callable that takes `(device_id, body, app_user)` so `verify-and-register` can reuse it without an HTTP round-trip. Synthetic `_RequestShim` provides `request.state.user` for inner SSH helpers. |
| `topology/routes/bridge_helpers.py` | edit | +helper | `find_lab_devices_file()` honours `${SCALER_DEVICES_FILE}` env var (lab-profile aware) with fallback to `~/SCALER/db/devices.json`. |
| `topology/scaler-api.js` | edit | +5 methods | `verifyAndRegister(deviceId, host, user, password, opts)`, `listMonitored()`, `getMonitored(ip)`, `attachReference(ip, opts)`, `detachReference(ip, opts)`. All raw `fetch()` with credentials. |
| `topology/topology-ssh-dialog.js` | edit | +verify-and-register call | Save handler prefers `verifyAndRegister` over legacy `verifyCredentials`. On success stamps `_sshReachable`, `_sshReachableAt`, `_monitorRegistered`, `_monitoredKey`, dispatches `device:context-updated` with full device object in `detail`. |
| `topology/topology-device-toolbar.js` | edit | gate tightening | LLDP + System Stack gates: `hasSshCredentials && (device._sshReachable || _legacyAlwaysOn(device))`. `_legacyAlwaysOn(device)` returns true when device lacks BOTH `_sshReachable` and `_monitorRegistered` flags (preserves PE-1 / PE-4 / RR-SA-2 first-paint behaviour). |
| `topology/topology-devices.js` | edit | +`MonitoredCache` IIFE + delete hook | Module-level cache: `refresh()` (60s TTL), `getByIp()`, `applyTo(device)` stamps `_sshReachable=true` from `last_seen_ok` ONLY when no in-session decision is fresher (harmonized with `topology-device-monitor.js`'s false-stamp on probe failure). Auto-hydrates on every `topology:loaded`. `delete(device)` calls `MonitoredCache.detachOnDelete()` for monitored devices. |
| `topology/topology.js` | edit | +`deleteSelected` detach hook | After splice, fire-and-forget `detachOnDelete()` for each device with `_monitorRegistered=true`. Logs `would_stop_monitoring=true` for future Phase-3 modal hook. |
| `topology/index.html` | edit | cache busters | Bumped 5 script tags to `?v=20260505a-auto-monitor`: `scaler-api.js`, `topology.js`, `topology-ssh-dialog.js`, `topology-device-toolbar.js`, `topology-devices.js`. |
| `topology/tests/test_monitored_registry_unit.py` | new | +247 | DAL unit tests (34 assertions). Caught a real DAL bug during authoring: `_open_db()` was missing `isolation_level=None` and writes were rolling back at close. Fixed in the same patch. |
| `topology/tests/test_monitored_endpoints_unit.py` | new | +275 | FastAPI TestClient unit tests (42 assertions). Stubs `verify_credentials_inline` + `monitored_dispatch.bring_up` so tests run offline. Covers 401 gate, two-user isolation, refcount math, last-referencer detection, idempotent attach, "failed verify must NOT register". |

### Test results

| Test | Command | Result |
|---|---|---|
| DAL unit | `python3 topology/tests/test_monitored_registry_unit.py` | **34 / 34 PASS** (exit 0) |
| Endpoint unit | `python3 topology/tests/test_monitored_endpoints_unit.py` | **42 / 42 PASS** (exit 0) |
| Live deploy DAL | `cd /home/dn/CURSOR && python3 tests/test_monitored_registry_unit.py` | PASS |
| Live deploy endpoints | `cd /home/dn/CURSOR && python3 tests/test_monitored_endpoints_unit.py` | PASS |
| `smoke_monitored_e2e.py` (item 19) | -- | **deferred** (the spec marked it optional and explicitly said "only if it can run cleanly without a live device"; the verify path requires SSH). |

### Multi-user 5-grep audit (`multiuser-by-default.mdc`)

| Grep | Pattern | Findings | Verdict |
|---|---|---|---|
| 1 | `expanduser("~/.topology_*")` in serve.py / ai/ / api/ / new modules | 0 matches | PASS |
| 2 | `open("/tmp/...")` in serve.py / ai/ / api/ / new modules | 0 matches | PASS |
| 3 | `TOPOLOGY_USERS_BASE` reads from new modules | 0 matches (we route through `settings.shared_topologies_dir`) | PASS |
| 4 | `def _require_auth` in serve.py | 3 method definitions, 37 references | PASS |
| 5 | `config_path` / `config_file` without `user_` prefix in new modules | 0 matches | PASS |

### Worktree-deploy-sync diff (`worktree-deploy-sync.mdc`)

All 14 source files plus 2 test files copied from the worktree to the
live deploy and verified with `diff --brief`. Zero `MISMATCH` lines.

### End-to-end chain (for the user to reproduce)

1. **User attaches NCP device to canvas.** Drag from sidebar -> a new
   device card with `_sshReachable=undefined`.
2. **User opens SSH dialog**, types `host=100.64.4.99 user=dnroot
   password=dnroot`, clicks Save.
3. **Frontend** -- `topology-ssh-dialog.js` save handler calls
   `ScalerAPI.verifyAndRegister(deviceId, host, user, password)`. Cookie
   carries the JWT.
4. **Bridge proxy** -- `serve.py` proxies `POST /api/devices/verify-and-register`
   to FastAPI on port 8002.
5. **JWT middleware** decodes the JWT, sets `request.state.user`.
6. **Route** -- `monitored_devices.verify_and_register`:
   - `_require_user(request)` -> `username` (e.g. `"alice"`).
   - `verify_credentials_inline(device_id, body, "alice")` runs the SAME
     SSH probe the legacy endpoint uses (no duplication).
   - On `ok=False`: returns the verify result UNCHANGED with `registered:
     false`. **No registry row written.** (Multi-user safety -- proven
     by the failed-verify test.)
   - On `ok=True`:
     - `reg.upsert_device(...)` (idempotent, field-level merge).
     - `reg.add_reference(key=key, username="alice", scope_type="topology",
       scope_id="")`.
     - `monitored_dispatch.bring_up(record)`:
       - Mirrors device into `${SCALER_DEVICES_FILE}` (default
         `~/SCALER/db/devices.json`) with file-lock + atomic write.
       - Best-effort POST to Network Mapper MCP at `/api/discover_device`.
       - Logs the other 3 subsystems as scheduled (existing periodic
         loops).
     - Returns 200 with `{ ok: true, registered: true, key,
       newly_registered, monitor_started_subsystems, references_count_total,
       references_user_count, hostname, platform, ... }`.
7. **Frontend** -- ssh-dialog stamps:
   - `device._sshReachable = true`
   - `device._sshReachableAt = Date.now()`
   - `device._monitorRegistered = true`
   - `device._monitoredKey = <key>`
   - `device._monitoredSubsystems = monitor_started_subsystems`
   And dispatches `device:context-updated` with full `device` in
   `event.detail`.
8. **Toolbar** -- `topology-device-toolbar.js`'s
   `device:context-updated` listener (line ~528) re-renders for the
   matching device. The tightened gate
   `hasSshCredentials && (device._sshReachable || _legacyAlwaysOn(device))`
   now passes -> LLDP scan + System Stack buttons appear, SSH icon
   gets the green ring.
9. **5 minutes later** -- `extract_configs.sh` cron picks up the new
   entry in `~/SCALER/db/devices.json`, populates
   `~/SCALER/db/configs/<host>/running.txt`. The DNAAS MCP cache
   (which reads that file lazily) automatically picks the device up
   on the next read.
10. **Network Mapper LLDP discovery** already happened at register
    time (step 6, best-effort `discover_device` call).
11. **Smooth-ZTP on next topology load** -- `MonitoredCache.refresh()`
    fetches the user's monitored list once; `applyTo()` stamps
    `_sshReachable=true` for each canvas card whose IP is in the cache
    BEFORE the first toolbar paint. PE-1 / PE-4 / RR-SA-2 keep the full
    toolbar from frame 1 -- no flicker.

### Open items the user must answer next (post-ship)

| ID | Question | Default if you don't answer |
|---|---|---|
| Phase-3 last-referencer modal | Should the canvas remove dialog show a modal `"Stop monitoring this device? Other users still attached: 0"` BEFORE the silent detach when `would_stop_monitoring=true`? Phase 2 logs it; the modal is a Phase 3 polish item. | Stay silent; only log when refcount hits 0. |
| Phase-3 attach-on-paste | When a user pastes a device card whose IP is already in the registry, should the frontend auto-call `attachReference()` (so the user's reference count goes +1) or wait for them to open the SSH dialog? | Wait for SSH dialog (current MVP). |
| Phase-3 OQ-6 toolbar additions | Should monitored devices get a Monitoring pill (alarms/health summary), live-config view, sub-IF drift indicator, or DNAAS path shortcut on the canvas toolbar? Section 12 OQ-6 lists 6 candidates. | Defer all 6 to Phase 5. |
