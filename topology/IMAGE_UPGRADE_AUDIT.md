# Image Upgrade Wizard - Frontend-Backend Compatibility Audit

**Date:** 2026-03-15  
**Scope:** All image-upgrade endpoints in `topology/scaler-api.js`, `topology/scaler-gui.js`, and `topology/scaler_bridge.py`

---

## Summary

| Endpoint | Method | Status | Issues |
|----------|--------|--------|--------|
| `/api/operations/image-upgrade/branches` | POST | OK | 1 minor |
| `/api/operations/image-upgrade/builds` | POST | OK | 0 |
| `/api/operations/image-upgrade/resolve-url` | POST | OK | 0 |
| `/api/operations/image-upgrade/branch-switch` | POST | OK | 0 |
| `/api/operations/image-upgrade/compat` | POST | OK | 0 |
| `/api/operations/image-upgrade/plan` | POST | OK | 0 |
| `/api/operations/image-upgrade/stack` | POST | OK | 0 |
| `/api/operations/image-upgrade` | POST | OK | 0 |
| `/api/operations/image-upgrade/trigger-build` | POST | OK | 0 |
| `/api/operations/image-upgrade/build-status/{job_id}` | GET | OK | 1 medium |
| `/api/operations/image-upgrade/build-log/{job_id}` | GET | OK | 0 |
| `/api/operations/image-upgrade/device-status` | GET | OK | 0 |
| `/api/operations/image-upgrade/from-urls` | POST | OK | 0 |
| `/api/operations/image-upgrade/recent-sources` | GET | OK | 0 |
| `/api/operations/image-upgrade/verify-stacks` | POST | OK | 0 |
| `/api/operations/image-upgrade/restore-config` | POST | OK | 1 low |

---

## Issues Found

### 1. listBranches('feature') - Backend treats as "all"

| Field | Value |
|-------|-------|
| **Endpoint** | `POST /api/operations/image-upgrade/branches` |
| **Frontend** | `topology/scaler-gui.js` line 6713 |
| **Backend** | `topology/scaler_bridge.py` lines 2768-2788 |
| **Mismatch** | Frontend calls `ScalerAPI.listBranches('feature')` expecting feature branches. Backend only handles `"dev"`, `"release"`, or `"all"`; any other value (including `"feature"`) falls through to the `else` branch and returns dev + release combined. |
| **Impact** | Feature branches are not returned; user sees dev+release instead. |
| **Severity** | **Low** |

---

### 2. build-status fetch without baseUrl (remote backend)

| Field | Value |
|-------|-------|
| **Endpoint** | `GET /api/operations/image-upgrade/build-status/{job_id}` |
| **Frontend** | `topology/scaler-gui.js` lines 7153, 7312 |
| **Backend** | N/A (frontend-only issue) |
| **Mismatch** | Two places use raw `fetch(statusUrl)` with a relative URL. When `ScalerAPI.baseUrl` is set (remote backend), the request hits the wrong origin. Compare: line 6160 correctly uses `(ScalerAPI.baseUrl || '') +` before the path. |
| **Impact** | When the app is served from a different origin than the API (e.g. static hosting + remote backend), build-status polling fails or hits the wrong server. |
| **Severity** | **Medium** |

**Fix:** Use `ScalerAPI._api()` for consistency:
```javascript
const statusUrl = ScalerAPI._api(`/api/operations/image-upgrade/build-status/${encodeURIComponent(branch)}?latest=true&_t=${Date.now()}`);
```

---

### 3. restore-config response not displayed

| Field | Value |
|-------|-------|
| **Endpoint** | `POST /api/operations/image-upgrade/restore-config` |
| **Frontend** | `topology/scaler-gui.js` lines 9227-9232 |
| **Backend** | `topology/scaler_bridge.py` lines 4030-4075 |
| **Mismatch** | Backend returns `{ success: true, results: { device_id: { success, message } } }`. Frontend only shows "Restore initiated" and does not read or display per-device success/failure. |
| **Impact** | User cannot see which devices succeeded or failed. Silent partial failure. |
| **Severity** | **Low** |

---

### 4. imageUpgrade sends unused fields

| Field | Value |
|-------|-------|
| **Endpoint** | `POST /api/operations/image-upgrade` |
| **Frontend** | `topology/scaler-gui.js` lines 7814-7828 |
| **Backend** | `topology/scaler_bridge.py` lines 3107-3227 |
| **Mismatch** | Frontend sends `is_sanitizer` and `parallel: true`. Backend does not read these fields. |
| **Impact** | None (extra fields are ignored). |
| **Severity** | **Low** (cosmetic) |

---

## Endpoint-by-Endpoint Verification

### POST /api/operations/image-upgrade/branches

- **Frontend sends:** `{ type: "dev" | "release" | "feature" }`
- **Backend expects:** `type` (default "dev"); uses "release", "dev", else "all"
- **Backend returns:** `{ branches: [{ name, url }], type }`
- **Frontend uses:** `r?.branches`, `b.name`
- **Status:** OK except `"feature"` treated as "all" (see Issue 1)

---

### POST /api/operations/image-upgrade/builds

- **Frontend sends:** `{ branch, limit?, max_results?, include_failed? }`
- **Backend expects:** `branch` (required), `limit` (default 15), `max_results` (default 10), `include_failed` (default false)
- **Backend returns:** `{ branch, builds: [{ build_number, result, display_name, age_hours, is_expired, is_sanitizer, has_dnos, has_gi, has_baseos, url }] }`
- **Frontend uses:** `res.builds`, `res.builds[0]`, `build_number`, `display_name`, `is_sanitizer`, etc.
- **Status:** OK. Frontend safely uses `res.builds || []`.

---

### POST /api/operations/image-upgrade/resolve-url

- **Frontend sends:** `{ url }` (only when `branch.startsWith('http')`)
- **Backend expects:** `url` (required)
- **Backend returns:** `{ branch, build_number, dnos_url, gi_url, baseos_url, is_expired, is_sanitizer, result, error_detail?, age_hours? }`
- **Frontend uses:** `r.branch`, `r.build_number`, `r.dnos_url`, `r.error_detail`
- **Status:** OK

---

### POST /api/operations/image-upgrade/branch-switch

- **Frontend sends:** `{ current_version, target_version }`
- **Backend expects:** `current_version`, `target_version` (both required)
- **Backend returns:** `{ is_switch, current_branch, target_branch, requires_delete_deploy }`
- **Frontend uses:** All fields
- **Status:** OK

---

### POST /api/operations/image-upgrade/compat

- **Frontend sends:** `{ source_version, target_version }` (config_text optional)
- **Backend expects:** `source_version`, `target_version` (required), `config_text` (optional)
- **Backend returns:** `{ source, target, is_downgrade, severity, incompatible_count, incompatible_features: [{ id, config_path, ... }], recommendation, ... }`
- **Frontend uses:** `r.severity`, `r.incompatible_count`, `r.incompatible_features`, `r.recommendation`, `f.id`, `f.config_path`
- **Status:** OK

---

### POST /api/operations/image-upgrade/plan

- **Frontend sends:** `{ device_ids, ssh_hosts, target_branch?, target_build_number?, target_version?, dnos_url? }`
- **Backend expects:** `device_ids` (required); one of `target_version`, `dnos_url`, or `(target_branch + target_build_number)`
- **Backend returns:** `{ devices: { id: { mode, current_version, target_version, upgrade_type, reason, warnings, components } }, target_version }`
- **Frontend uses:** `result.devices`, `result.target_version`, `p.upgrade_type`, `p.reason`, `p.warnings`, etc.
- **Status:** OK

---

### POST /api/operations/image-upgrade/stack

- **Frontend sends:** `{ branch, build_number }`
- **Backend expects:** `branch`, `build_number` (both required)
- **Backend returns:** `{ branch, build_number, result, is_sanitizer, is_expired, age_hours, dnos_url, gi_url, baseos_url, url_status? }`
- **Frontend uses:** `stack.dnos_url`, `stack.gi_url`, `stack.baseos_url`, `stack.gi_url`, `stack.baseos_url` for version extraction
- **Status:** OK

---

### POST /api/operations/image-upgrade (main execute)

- **Frontend sends:** `{ device_ids, ssh_hosts, branch, build_number, components, upgrade_type, device_plans, max_concurrent, dnos_url, gi_url, baseos_url, is_sanitizer, parallel }`
- **Backend expects:** `device_ids`, `ssh_hosts`, `device_plans`, `max_concurrent`, `branch`, `build_number`, `components`, `upgrade_type`, `dnos_url`, `gi_url`, `baseos_url` (at least one URL required)
- **Backend returns:** `{ job_id, status, message, devices }`
- **Frontend uses:** `result.job_id` for showProgress
- **Status:** OK. Extra fields ignored.

---

### POST /api/operations/image-upgrade/trigger-build

- **Frontend sends:** `{ branch, with_baseos, qa_version, with_sanitizer, auto_push, device_ids, ssh_hosts, components }`
- **Backend expects:** `branch` (required), `with_baseos`, `qa_version`, `with_sanitizer`, `device_ids`, `ssh_hosts`, `auto_push`, `components`
- **Backend returns:** `{ success, message, job_id, branch }`
- **Frontend uses:** `res.success`, `res.job_id`, `res.message`
- **Status:** OK

---

### GET /api/operations/image-upgrade/build-status/{job_id}

- **Frontend sends:** Path param `job_id` (branch name when checking running build), query `?latest=true`
- **Backend expects:** `job_id` (path), `latest` (query, bool)
- **Backend returns:** `{ branch, build_number, building, result, age_hours, is_sanitizer, is_expired, duration, build_params }`
- **Frontend uses:** `st.building`, `st.build_number`, `st.age_hours`, `st.build_params`, `st.result`
- **Status:** OK. Note: `job_id` is always branch name for build-status (Jenkins); upgrade job progress uses SSE `/api/config/push/progress/{job_id}` instead. See Issue 2 for baseUrl.

---

### GET /api/operations/image-upgrade/build-log/{job_id}

- **Frontend sends:** Path `job_id` (= branch), query `?build_number=N` (optional)
- **Backend expects:** `job_id` (path = branch), `build_number` (query, optional)
- **Backend returns:** `{ log, success, build_number }` or `{ log, error }`
- **Frontend uses:** `r.log`, `r.error`
- **Status:** OK. URL encoding: frontend uses `encodeURIComponent(branch)`.

---

### GET /api/operations/image-upgrade/device-status

- **Frontend sends:** Query `device_ids=id1,id2`, `ssh_hosts=ip1,ip2` (optional)
- **Backend expects:** `device_ids` (comma-separated), `ssh_hosts` (comma-separated, index-aligned)
- **Backend returns:** `{ devices: { id: { mode, dnos_ver, gi_ver, baseos_ver, install_status, ... } } }`
- **Frontend uses:** `result.devices`
- **Status:** OK. Frontend builds `hosts` as `deviceIds.map(id => sshHosts[id] || '').join(',')` — correct alignment.

---

### POST /api/operations/image-upgrade/from-urls

- **Frontend:** Uses `ScalerAPI.upgradeFromUrls(body)` — passes body through.
- **Backend:** Delegates to `image_upgrade_execute(body)`.
- **Status:** OK

---

### GET /api/operations/image-upgrade/recent-sources

- **Frontend:** `ScalerAPI.getUpgradeRecentSources()` — no params.
- **Backend returns:** `{ recent_urls, recent_branches }`
- **Status:** OK (endpoint exists; GUI usage not fully traced).

---

### POST /api/operations/image-upgrade/verify-stacks

- **Frontend sends:** `{ device_ids, ssh_hosts }`
- **Backend expects:** `device_ids`, `ssh_hosts` (dict)
- **Backend returns:** `{ success, result: { hostname: { stack_output } | { error } } }`
- **Frontend uses:** `r.result`, `data.error`, `data.stack_output`
- **Status:** OK

---

### POST /api/operations/image-upgrade/restore-config

- **Frontend sends:** `{ device_ids, ssh_hosts }`
- **Backend expects:** `device_ids`, `ssh_hosts`
- **Backend returns:** `{ success, results: { device_id: { success, message } } }`
- **Frontend uses:** None (see Issue 3)
- **Status:** OK except UX gap

---

## Encoding

- **Branch names with `/`:** Frontend uses `encodeURIComponent(branch)` for path params (build-status, build-log). Backend uses `{job_id:path}` and `urllib.parse.unquote`. OK.
- **Query params:** `device_ids`, `ssh_hosts` passed via URLSearchParams; no special encoding issues.

---

## Error Handling

- **getBuildsForBranch:** Frontend uses `res.builds || []` — safe.
- **getUpgradePlan:** Frontend uses `result.devices`, `result.target_version` — plan structure is always returned when successful.
- **resolveJenkinsUrl:** Frontend checks `r.branch`, `r.build_number`, `r.error_detail` — handles error responses.
- **build-status:** Frontend checks `st.building`, `st.build_number` — handles null/undefined.
- **verify-stacks:** Frontend uses `r?.result` — safe.

---

## Recommendations

1. **Medium:** Fix build-status fetch to use `ScalerAPI._api()` at lines 7153 and 7312 in `scaler-gui.js`.
2. **Low:** Add support for `"feature"` branch type in backend, or document that it maps to "all".
3. **Low:** Display per-device restore-config results in the GUI (success/failure per device).
