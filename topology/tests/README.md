# Topology SSH / Credential Test Suite

Regression guards for the April 20 2026 fixes to SSH method selection,
per-user device credentials, and telemetry. Run these **any time** the
following files change:

- `topology/topology-object-detection.js` (`_shouldUseWebTerminal`, `_pickLaunchMethod`)
- `topology/topology-ssh-dialog.js` (Connect Via picker, `doConnect`, `saveAddress`)
- `topology/api/auth/router.py` (`/api/auth/me/device-credentials/*` endpoints)
- `topology/routes/bridge_helpers.py` (`_get_credentials` resolution order)
- `topology/scaler-api.js` (device credential helpers)

## Tests

### `smoke_ssh_method_matrix.js`

Pure Node.js decision-matrix test for the JS method launcher. Extracts
`_pickLaunchMethod` / `_shouldUseWebTerminal` / `_isMacUA` / `_getSshLaunchPref`
from the live source file and runs them inside a VM sandbox with mocked
`window` / `navigator` / `localStorage`. Verifies **16** platform x pref x
sticky combinations.

```bash
node topology/tests/smoke_ssh_method_matrix.js
```

No network, no device access required. Run it on every JS edit.

### `smoke_ssh_target_picker.js`

Pure Node.js regression test for the shared SSH target picker. It executes the
real `topology-ssh-target.js` helper and pins the all-cluster rule: cluster
targets must resolve to the active NCC hostname before chassis/NCP serials or
stale per-NCC IPs. The matrix includes PE-4-like, generic, monitor-derived, and
identity-derived cluster records so the guard is not tied to one device/user.

```bash
node topology/tests/smoke_ssh_target_picker.js
```

Run this any time `topology-ssh-target.js`, `topology-object-detection.js`, or
`topology-ssh-dialog.js` changes.

### `smoke_per_user_ssh.py`

End-to-end API round-trip over the live proxy on port 8080. Validates:

1. Unauthenticated access is rejected (401)
2. PUT creates a credential, GET retrieves it, LIST includes it, DELETE removes it
3. Response payload redacts `password` (only `has_password: true` is shown)
4. On-disk `~/.topology_users/<user>/devices.json` is **0600**, contains the exact saved value
5. Per-user isolation: user B cannot see user A's credentials (GET returns 404, list is empty)
6. `routes.bridge_helpers._get_credentials(app_user, device_id)` picks up the saved value

```bash
export SMOKE_USER_A=admin SMOKE_PASS_A=drivenets
export SMOKE_USER_B=smoketest_... SMOKE_PASS_B=...
python3 topology/tests/smoke_per_user_ssh.py
```

Requires the topology-app service to be running.

### `scripts/audit_topology_state.py`

Persistent state auditor (runs in ~100ms, no external deps). Checks:

- Shared SQLite (`~/.topology_shared/_device_state.db`) schema, row integrity,
 stale watchers > 24h, JSON validity of `user_device_prefs`
- Per-user `~/.topology_users/<u>/devices.json`: 0600 permissions,
 valid JSON, `user`/`password` fields present, no unknown keys
- Cross-references: every user referenced in the shared DB has a user dir

```bash
python3 topology/scripts/audit_topology_state.py
```

Returns exit 0 on clean state, exit 1 if any `[CRIT]` finding. Run it
periodically (ops / scheduled) or after any migration.

## Telemetry (runtime)

`_shouldUseWebTerminal` logs every decision to the browser console:

```
[SSH] method decision: host=100.64.4.205 web=false reason=auto mac-ua -> iterm
[SSH] method decision: host=100.64.4.205 web=true reason=device-sticky=webterm
[SSH] method decision: host=100.64.4.205 web=false reason=global-pref=iterm
```

Filter the DevTools console on `[SSH]` to watch live decisions when
debugging why a device opened the wrong method.

`doConnect()` also logs credential auto-persist attempts:

```
[SSH] creds auto-persisted on connect for PE-4
[SSH] creds persisted for RR-SA-2 {device_id: "RR-SA-2", has_password: true, ...}
```
