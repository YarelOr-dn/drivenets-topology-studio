# ScalerAPI Frontend-Backend Comprehensive Audit

**Date:** 2026-03-15  
**Scope:** All ScalerAPI calls in `topology/scaler-gui.js`, `topology/scaler-api.js` vs backend endpoints in `topology/scaler_bridge.py` (and `topology/serve.py` where applicable).

---

## Executive Summary

| Category | Count |
|----------|-------|
| Critical (broken functionality) | 5 |
| High (wrong endpoint / wrong call) | 3 |
| Medium (baseUrl / missing fields) | 4 |
| Low (unused fields / dead code) | 8 |
| Dead endpoints (backend, no frontend) | 3 |
| Dead frontend methods (never called) | 4 |

---

## 1. Frontend sends fields backend ignores

| Endpoint | Frontend file:line | Backend file:line | Fields ignored | Impact | Severity |
|----------|-------------------|-------------------|----------------|--------|----------|
| `POST /api/operations/image-upgrade` | scaler-gui.js ~7814 | scaler_bridge.py ~3109 | `is_sanitizer`, `parallel` | None | Low |
| `POST /api/operations/push` | scaler-gui.js ~543, ~4090 | scaler_bridge.py ~1916 | `job_name` (backend builds its own via `_build_job_name`) | Backend may use different label | Low |
| `POST /api/config/scan-ips` | scaler-gui.js ~2962 | scaler_bridge.py ~897 | `check_ipv4`, `check_ipv6` (backend uses `ipv4_start`/`ipv6_start` as aliases) | Minor naming mismatch | Low |

---

## 2. Backend expects fields frontend never sends

| Endpoint | Frontend file:line | Backend file:line | Missing field | Impact | Severity |
|----------|-------------------|-------------------|---------------|--------|----------|
| `POST /api/operations/delete-hierarchy` | scaler-gui.js ~9129 | scaler_bridge.py ~1776 | `sub_path` (backend reads but ignores; push module supports it) | Cannot delete single interface when commit conflicts | **High** |
| `POST /api/config/validate/policy` | scaler-gui.js ~5852 | scaler_bridge.py ~1155 | `hierarchy` (optional) | None | Low |

---

## 3. Response fields backend returns but frontend never uses

| Endpoint | Backend returns | Frontend uses | Impact | Severity |
|----------|-----------------|---------------|--------|----------|
| `POST /api/operations/delete-hierarchy` | `commands_preview` | Success/message only | User doesn't see preview of commands | Low |
| `POST /api/operations/image-upgrade/restore-config` | `results: { device_id: { success, message } }` | None (shows generic "Restore initiated") | Silent partial failure | **Medium** |
| `GET /api/config/push/progress/{job_id}` (SSE) | `terminal_full`, `cancelled` | `terminal`, `success`, `message`, `device_state` | Minor | Low |

---

## 4. Response fields frontend reads but backend never returns

| Endpoint | Frontend reads | Backend returns | Impact | Severity |
|----------|----------------|-----------------|--------|----------|
| `POST /api/config/generate/*` | `lines`, `hierarchy` | `config` only (interfaces, services return `config`; some builders may return more) | Frontend may expect `lines` for display | Low |
| `GET /api/operations/jobs` | `job.ssh_host` | Job has `device_id`, `ssh_host` in push jobs | Verify job shape | Low |

---

## 5. baseUrl missing (raw fetch without ScalerAPI._api)

| Endpoint | Frontend file:line | Issue | Impact | Severity |
|----------|-------------------|-------|--------|----------|
| `GET /api/operations/image-upgrade/build-status/{job_id}` | scaler-gui.js ~6160, ~7153, ~7312, ~7356 | Some use `(ScalerAPI.baseUrl || '') +`; others use raw `fetch(url)` with constructed URL. Line 6160 OK; 7153, 7312 use `statusUrl` from `(ScalerAPI.baseUrl || '') +` - actually OK. Line 7155: `fetch(statusUrl)` - statusUrl is built with baseUrl at 7153. Verify all. | Remote backend fails | **Medium** |
| `/api/xray/config`, `/api/xray/verify-mac` | scaler-gui.js ~2268, ~2327, ~2348 | Uses `ScalerAPI._api ? ScalerAPI._api(...) : '/api/...'` - OK | None | - |
| `/api/config/{device_id}/saved-files`, `/api/config/file`, `/api/config/{device_id}/push` | scaler-gui.js ~9568, ~9635, ~9662, ~9699, ~9700 | Uses same pattern - OK when ScalerAPI loaded | None | - |
| `/api/operations/diagnose-recovery` | scaler-gui.js ~6507 | Uses ScalerAPI._api - OK | None | - |

---

## 6. Dead endpoints (backend routes no frontend calls)

| Endpoint | Backend file:line | Notes |
|----------|-------------------|-------|
| `GET /api/config/{device_id}/services` | N/A - does NOT exist | ScalerAPI.getServices() calls it; 404 |
| `GET /api/config/{device_id}/multihoming` | N/A - does NOT exist | ScalerAPI.getMultihoming() calls it; 404 |
| `GET /api/config/{device_id}/hierarchy/{hierarchy}` | N/A - does NOT exist | ScalerAPI.getHierarchy() calls it; 404 |

**Impact:** getServices, getMultihoming, getHierarchy are never called from scaler-gui.js (grep confirms). They are dead ScalerAPI methods calling non-existent endpoints. If any other code used them, it would 404.

---

## 7. Dead frontend methods (ScalerAPI methods never called from scaler-gui.js)

| Method | scaler-api.js line | Called from | Notes |
|--------|-------------------|-------------|-------|
| `getServices` | 346 | Never | Dead |
| `getMultihoming` | 359 | Never | Dead |
| `getHierarchy` | 373 | Never | Dead |
| `getRunningConfig` | 230 | Never | Dead |
| `getConfigSummary` | 259 | Never | Dead |
| `addDevice` | 98 | Never (serve.py handles /api/devices/ differently) | Dead |
| `updateDevice` | 117 | Never | Dead |
| `deleteDevice` | 136 | Never (scaler-gui uses different flow) | Verify |
| `batchOperation` | 829 | Never | Dead |
| `getOperationStatus` | 849 | Never (uses getJob instead) | Dead |
| `cancelOperation` | 862 | Never (uses cancelHeldJob/cancelJob) | Dead |
| `compareConfigs` | 484 | Never | Dead |
| `getConfigDiff` | 497 | Never | Dead |
| `getTemplates` | 507 | Never | Dead |
| `generateTemplate` | 512 | Never | Dead |
| `generateRoutePolicyStructured` | 381 | Never | Dead |
| `generateSystem` | 543 | Never | Dead |
| `validatePolicy` | 556 | Never - wait, line 5852 uses validatePolicy | Used |
| `mirrorAnalyze`, `mirrorGenerate`, `mirrorPreviewDiff` | 469-498 | Never | Dead |
| `diffConfigs` | 817 | Never | Dead |
| `deleteHierarchy` (not deleteHierarchyOp) | 734 | See Issue 8 | Wrong method |

---

## 8. CRITICAL: Wrong API method / non-existent endpoint

### 8.1 deleteHierarchy vs deleteHierarchyOp (CRITICAL)

| Field | Value |
|-------|-------|
| **Location** | scaler-gui.js ~9129 |
| **Current call** | `ScalerAPI.deleteHierarchy({ device_id: deviceId, hierarchy: 'interfaces', sub_path: iface, dry_run: false, ssh_host: '' })` |
| **Problem 1** | `ScalerAPI.deleteHierarchy(deviceId, hierarchy)` expects TWO positional args, not an object. Passing an object makes deviceId = object, hierarchy = undefined. Body becomes `{ device_id: "[object Object]", hierarchy: undefined }`. |
| **Problem 2** | `ScalerAPI.deleteHierarchy` calls `POST /api/operations/delete` which does NOT exist in scaler_bridge. The bridge has `POST /api/operations/delete-hierarchy`. |
| **Problem 3** | The catch-all `@app.api_route("/api/operations/{path:path}")` returns 501 for `/api/operations/delete`. |
| **Fix** | Call `ScalerAPI.deleteHierarchyOp(deviceId, 'interfaces', false, iface)` instead. |
| **Backend gap** | delete_hierarchy_op does NOT read or pass `sub_path` to the push module. The push module's `_execute_sub_hierarchy_delete` supports `sub_path` for single-interface delete. Bridge must be updated to read `sub_path` and use the sub-path code path. |
| **Severity** | **Critical** |

### 8.2 stag-check returns 501 (CRITICAL)

| Field | Value |
|-------|-------|
| **Endpoint** | `POST /api/operations/stag-check` |
| **Frontend** | scaler-gui.js ~8234, ~11058 (ScalerAPI.stagCheck extension) |
| **Backend** | No specific route. Hits catch-all `@app.api_route("/api/operations/{path:path}")` at scaler_bridge.py ~4117 which returns 501. |
| **Impact** | Stag Pool Check panel always fails with "Operation not implemented". |
| **Fix** | Add `@app.post("/api/operations/stag-check")` in scaler_bridge.py (or implement in scaler, then wire bridge). |
| **Severity** | **Critical** |

### 8.3 ScalerAPI.deleteHierarchy points to non-existent /api/operations/delete (HIGH)

| Field | Value |
|-------|-------|
| **Location** | scaler-api.js ~734 |
| **Issue** | `deleteHierarchy(deviceId, hierarchy)` sends to `POST /api/operations/delete`. Backend has `delete-hierarchy`, not `delete`. |
| **Impact** | Any caller of deleteHierarchy gets 501. |
| **Fix** | Remove deleteHierarchy or make it call delete-hierarchy with correct body. Prefer deleteHierarchyOp as the canonical method. |
| **Severity** | **High** |

### 8.4 Config History / Saved Files - endpoints don't exist (CRITICAL)

| Field | Value |
|-------|-------|
| **Endpoints** | `GET /api/config/{device_id}/saved-files`, `GET /api/config/file?path=`, `POST /api/config/{device_id}/push`, `DELETE /api/config/file?path=` |
| **Frontend** | scaler-gui.js ~9568, ~9635, ~9662, ~9699, ~9700 |
| **Backend** | scaler_bridge.py has NO routes for these. All /api/config/* is proxied to bridge. |
| **Impact** | Config History / Saved Files panel fails with 404 on every operation. |
| **Note** | topology/api/routes/config.py has `/{device_id}/saved-files` but that's a different API structure (not used by serve.py). |
| **Fix** | Implement saved-files, file, and device-specific push in scaler_bridge, or add handlers in serve.py before proxying. |
| **Severity** | **Critical** |

### 8.5 diagnose-recovery - verify backend exists

| Field | Value |
|-------|-------|
| **Endpoint** | `POST /api/operations/diagnose-recovery` |
| **Frontend** | scaler-gui.js ~6507 |
| **Backend** | scaler_bridge.py ~3922 has `@app.post("/api/operations/diagnose-recovery")` |
| **Status** | OK - endpoint exists. |

---

## 9. Duplicate ScalerAPI method definitions

| Method | First definition | Second definition | Notes |
|--------|------------------|-------------------|-------|
| `generateInterfaces` | scaler-api.js ~315 | scaler-api.js ~768 | Duplicate - same endpoint |
| `generateServices` | scaler-api.js ~403 | scaler-api.js ~791 | Duplicate - same endpoint |
| `getInterfaces` | scaler-api.js ~331 | scaler-api.js ~506 | Duplicate - same endpoint |

---

## 10. Recommendations

### Immediate (Critical/High)

1. **Fix delete-conflicting flow (scaler-gui.js ~9129):** Replace `ScalerAPI.deleteHierarchy({...})` with `ScalerAPI.deleteHierarchyOp(deviceId, 'interfaces', false, iface)`.
2. **Add sub_path to delete_hierarchy_op (scaler_bridge.py):** Read `sub_path` from body and pass to push module's sub-path delete path when hierarchy supports it.
3. **Implement stag-check in scaler_bridge:** Add route and wire to scaler's stag-check logic (or return 501 with clear message until implemented).
4. **Implement Config History endpoints in scaler_bridge:** Add `GET /api/config/{device_id}/saved-files`, `GET /api/config/file`, `POST /api/config/{device_id}/push`, `DELETE /api/config/file` (or document as future work and hide the panel).
5. **Remove or fix ScalerAPI.deleteHierarchy:** Either remove it or make it a wrapper for deleteHierarchyOp to avoid confusion.

### Medium

6. **restore-config response:** Have frontend read and display `results` from restore-config so user sees per-device success/failure.
7. **build-status baseUrl:** Ensure all build-status fetch URLs use `ScalerAPI._api()` when baseUrl may be set.

### Low

8. **Remove duplicate method definitions** in scaler-api.js (generateInterfaces, generateServices, getInterfaces).
9. **Remove dead ScalerAPI methods** (getServices, getMultihoming, getHierarchy, getRunningConfig, getConfigSummary, etc.) or implement their backend routes if needed.
10. **listBranches('feature'):** Backend treats "feature" as "all"; either add feature support or document.

---

## Appendix: Endpoint Inventory

### Backend (scaler_bridge.py) - Implemented

- `/api/ssh-pool/*` (toggle, status, evict)
- `/api/config/{device_id}/running`
- `/api/config/{device_id}/summary`
- `/api/config/{device_id}/sync`
- `/api/config/generate/interfaces`
- `/api/config/generate/undo`
- `/api/config/{device_id}/save`
- `/api/config/scan-existing`
- `/api/config/scan-ips`
- `/api/config/detect-pattern`
- `/api/config/detect/l2ac-parent`
- `/api/config/detect/bgp-neighbors`
- `/api/config/menu-summary`
- `/api/config/detect/scale-suggestions`
- `/api/config/generate/system`
- `/api/config/validate/policy`
- `/api/config/generate/route-policy-structured`
- `/api/config/generate/services`
- `/api/config/generate/bgp`
- `/api/config/compare`
- `/api/config/{device_id}/interfaces`
- `/api/config/limits/{device_id}`
- `/api/config/templates/smart-defaults/{device_id}`
- `/api/config/templates`
- `/api/config/templates/generate`
- `/api/config/{device_id}/diff`
- `/api/config/generate/routing-policy`
- `/api/config/generate/flowspec`
- `/api/config/flowspec-dependency-check`
- `/api/config/generate/igp`
- `/api/config/generate/batch`
- `/api/config/preview-diff`
- `/api/mirror/analyze`
- `/api/mirror/generate`
- `/api/mirror/preview-diff`
- `/api/config/delete-hierarchy-options`
- `/api/operations/delete-hierarchy`
- `/api/operations/validate`
- `/api/config/push/estimate`
- `/api/operations/push`
- `/api/config/push/progress/{job_id}`
- `/api/operations/push/{job_id}/commit`
- `/api/operations/push/{job_id}/cancel`
- `/api/operations/push/{job_id}/cleanup`
- `/api/operations/jobs`
- `/api/operations/jobs/{job_id}`
- `/api/operations/jobs/{job_id}/retry`
- `DELETE /api/operations/jobs/{job_id}`
- `/api/operations/multihoming/compare`
- `/api/operations/multihoming/sync`
- `/api/operations/scale-updown`
- `/api/operations/image-upgrade/*` (all image-upgrade routes)
- `/api/operations/diagnose-recovery`
- `/api/operations/{job_id}/cancel`
- `/api/wizard/suggestions`
- `/api/devices/{device_id}/context`
- `/api/devices/{device_id}/git-commit`
- `/api/devices/{device_id}/set-hostname`
- `/api/devices/{device_id}/test`
- `/api/devices/discover`
- `/api/health`

### Backend - NOT implemented (frontend calls these)

- `GET /api/config/{device_id}/saved-files`
- `GET /api/config/file`
- `POST /api/config/{device_id}/push`
- `DELETE /api/config/file`
- `GET /api/config/{device_id}/services`
- `GET /api/config/{device_id}/multihoming`
- `GET /api/config/{device_id}/hierarchy/{hierarchy}`
- `POST /api/operations/stag-check`
- `POST /api/operations/delete` (ScalerAPI.deleteHierarchy uses this; should use delete-hierarchy)

### serve.py (handles directly, not scaler_bridge)

- `GET /api/devices/` - aggregated from discovery + inventory + SCALER cache
- `GET /api/devices/{id}` - from discovery
- `GET /api/xray/config`
- `POST /api/xray/config`
- `POST /api/xray/verify-mac`
- `GET /api/health` - aggregated
