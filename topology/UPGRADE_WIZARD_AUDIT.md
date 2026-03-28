# Image Upgrade Wizard - Presentation & Display Audit

**Scope:** `openUpgradeWizard` and all 6 steps (Devices, Source, Build, Compare, Upgrade Plan, Execute)  
**File:** `topology/scaler-gui.js`  
**Date:** 2026-03-15

---

## 1. HTML Elements Referencing IDs Never Created

| ID | Step | Location | Issue |
|----|------|----------|-------|
| `upgrade-build-area` | Build (Step 3) | ~7005 | Rendered as empty `<div id="upgrade-build-area"></div>` but **never populated**. No code writes to this element. |
| `upgrade-chips-lastused` | Source (Step 2) | ~6591 | Only created when `lastUsed.length > 0`. If user has no recent branches, `upgrade-chips-lastused` does not exist. The collapsible handler uses `getElementById('upgrade-chips-${key}')` with optional `if (!grid) return` — so no crash, but the "Recent Branches" group is never rendered when empty. |

**Severity:** `upgrade-build-area` = **dead-code** (unused placeholder). `upgrade-chips-lastused` = **visual-bug** only when lastUsed is empty and user somehow triggers collapsible (unlikely since the group isn't rendered).

---

## 2. Data Fetched But Never Displayed

| Data | Step | Location | Issue |
|------|------|----------|-------|
| `data._targetStack` | Compare (Step 4) | ~7407–7408 | Used for `targetGi` and `targetBase` in compare cards. **`_targetStack` is never set anywhere.** GI and BaseOS target versions always show `--`. |
| `data._branchSwitch` | Compare (Step 4) | ~7431–7436 | Fetched in afterRender and **displayed** in `alertsHtml`. OK. |
| `data._compatReport` | Compare (Step 4) | ~7439–7450 | Fetched in afterRender and **displayed** in `alertsHtml`. OK. |
| `data._expiredBuild` | Build (Step 3) | ~6993–6994 | **Displayed** in `expiredMsg` when builds.length === 0. OK. |
| `data._resolvedBuildNumber` | Build (Step 3) | ~6989, 6996 | **Displayed** in branch info line when resolving from URL. OK. |

**Severity:** `_targetStack` never populated = **missing-feature** (Compare step GI/BaseOS target always `--`).

---

## 3. Hardcoded Colors Still Remaining

| Location | Line (approx) | Hex | Context |
|----------|---------------|-----|---------|
| Build step `renderBuildRow` (dead code) | 6313–6315 | `#e74c3c`, `#f39c12`, `#888` | Status, ASAN, expired, DNOS/GI/BaseOS cells |
| Build step inline row render | 6974–6983 | Uses CSS classes `upgrade-build-ok`, `upgrade-build-fail`, `upgrade-build-warn` | OK — no hex in table |
| Build detail ASAN warning | 7385 | `#f39c12` | `style="border-color:#f39c12;color:#f39c12"` |
| Source step "Loading branches" | 6599 | `#888` | `style="color:#888"` |
| _injectRunningBuildBanner fetchErrBox selector | 6251 | `e74c3c` | Selector `[style*="e74c3c"]` — targets wrong element (see below) |

**Severity:** **visual-bug** — should use `var(--dn-red, #e74c3c)`, `var(--dn-orange, #f39c12)`, `var(--dn-cloud, #888)`.

---

## 4. Broken Conditional Renders

| Location | Issue |
|----------|-------|
| Compare step afterRender ~7489 | `if (!sb \|\| devs.length === 0 \|\| data._branchSwitch \|\| data._compatReport) return;` — Returns early when we **already have** branch switch or compat report. Intent: only fetch when we don't have data. Logic is correct: we skip the async fetch if data exists. |
| Build step `builds.length === 0` path | When `resolving` is true, we return early with "Loading builds..." and never show `upgrade-build-area` or fetch buttons. Correct. |
| Build step empty state | When `builds.length === 0` and not resolving, we show Fetch builds + Trigger. When `builds.length > 0`, we show the table. No inverted logic found. |

**Severity:** No broken conditionals identified.

---

## 5. Missing Empty States

| Step | Section | Issue |
|------|---------|-------|
| Source | Browse pane | When `!hasBranches` and `!lastUsed.length`, shows "Loading branches... Load". When load fails or returns empty, no explicit "No branches found" message — just empty chip grids. |
| Build | Build table | When `builds.length > 0`, table is shown. When `builds.length === 0`, shows Fetch/Trigger. OK. |
| Compare | Device cards | When `devs.length === 0`, cards is empty string; summary still says "Upgrading 0 device(s)". Minor: could show "Select devices in Step 1" but step is skipIf when no selectedBuild. |
| Upgrade Plan | Empty plan | Shows "Click Fetch Plan to auto-detect" when `Object.keys(devices).length === 0`. OK. |

**Severity:** Source "no branches" = **visual-bug** (no explicit empty message after load).

---

## 6. Build Table Presentation

| Feature | Status |
|---------|--------|
| Selected row highlight | OK — `upgrade-build-selected` class applied when `b.build_number === sel?.build_number` |
| Expired build indicator | OK — `[OLD]` span with `upgrade-build-fail` when `b.is_expired` |
| Build age formatting | OK — `formatAge(b.age_hours)` → `Xm`, `Xh`, `Xd` |
| ASAN badge | OK — `[ASAN]` when `b.is_sanitizer` |
| QA badge | **Missing** — Build API does not return `is_qa`. QA is only in running-build params. Completed builds in table have no QA indicator. |
| BaseOS indicator | OK — `b.has_baseos ? 'OK' : '--'` in BaseOS column |

**Severity:** QA badge = **missing-feature** (API doesn't provide it for completed builds).

---

## 7. Compare Step (Step 4)

| Item | Rendered? |
|------|-----------|
| Branch switch detection | Yes — `data._branchSwitch` in `alertsHtml` when `requires_delete_deploy` or `is_switch` |
| Compat report | Yes — `data._compatReport` in `alertsHtml` with severity, count, recommendation, incompatible_features |
| Target GI/BaseOS | No — `_targetStack` never set, so always `--` |
| Device version cards | Yes — DNOS/GI/BaseOS current vs target |
| Images URLs | Yes — when `hasUrls` |

**Severity:** Target GI/BaseOS = **missing-feature**.

---

## 8. wizardHeader (Device Stack) Rendering

| Item | Status |
|------|--------|
| Refresh button | OK — `#upgrade-ctx-refresh` exists, calls `ScalerAPI.getUpgradeDeviceStatus`, updates `deviceStatus`, re-renders |
| Version columns (DNOS, GI, BaseOS) | Populated from `st.dnos_ver \|\| parsed.dnos` etc. When no status/context, shows `--`. OK. |
| Mode badges | `upgrade-mode-dnos`, `upgrade-mode-gi`, `upgrade-mode-recovery`, `upgrade-mode-loading` — all have CSS. `upgrade-mode-deploying` also exists. |
| Stale indicator | No explicit "stale" (>5 min) indicator in upgrade wizard header (unlike Scale wizard). |

**Severity:** Refresh works. Version columns OK. Mode badges OK. Stale indicator = **missing-feature** (nice-to-have).

---

## 9. Step Indicators

| Item | Status |
|------|--------|
| Completed/active/pending | OK — `scaler-wizard-step-indicator` with `completed`, `active` classes |
| Step titles | OK — `step.label` from step config |
| Connector lines | OK — `step-connector` with `completed` when `idx < currentStep` |
| CSS | `.scaler-wizard-steps`, `.scaler-wizard-step-indicator`, `.step-connector` exist in styles.css |

**Severity:** No issues.

---

## 10. CSS Class Mismatches

| Class Used in JS | In styles.css? |
|------------------|----------------|
| `upgrade-build-selected` | Yes |
| `upgrade-build-ok`, `upgrade-build-fail`, `upgrade-build-warn` | Yes |
| `upgrade-compare-alert--danger`, `--warn`, `--info` | Yes |
| `upgrade-compat-row`, `upgrade-compat-feat`, `upgrade-compat-path` | Yes |
| `upgrade-mode-badge`, `upgrade-mode-dnos`, etc. | Yes |
| `scaler-btn-danger` | Yes |
| `upgrade-chip--active` | Yes |
| `upgrade-dev-row--disabled`, `--expanded` | Yes |
| `upgrade-plan-row--blocked` | Yes |
| `upgrade-compare-card--collapsed` | Yes |

**Severity:** No mismatches found.

---

## 11. Additional Issues

### 11.1 _injectRunningBuildBanner fetchErrBox Selector

**Location:** ~6251  
**Code:** `container.querySelector('.scaler-info-box[style*="e74c3c"]')`  
**Issue:** The fetch error div uses class `upgrade-fetch-error` with CSS `color: var(--dn-red, #e74c3c)` — no inline `style` attribute. Selector never matches. The banner never updates the fetch error text to "No completed builds yet -- build #X is still running."  
**Severity:** **visual-bug** — running build banner injects but fetch error message is not updated.

### 11.2 Dead Code: renderBuildRow

**Location:** ~6310–6323  
**Issue:** `renderBuildRow` is defined but never used. Build step uses inline row rendering.  
**Severity:** **dead-code**.

### 11.3 upgrade-trigger-from-build Click Handler

**Location:** ~7197  
**Code:** `const panel = document.getElementById('upgrade-inline-trigger');`  
**Issue:** Variable named `panel` but it's the trigger div, not a panel. When `isHidden` is true, we set `panel.style.display = 'block'`. The `upgrade-inline-trigger` div exists in the `builds.length === 0` path. When `builds.length > 0`, that HTML is not rendered — we get the table view which does NOT include `upgrade-inline-trigger`. So "Trigger New Build" button exists only in the empty-builds path. In the table path, there is no `upgrade-inline-trigger` — the "Trigger New Build" button is also missing. Checking... In the table path (builds.length > 0) we have:
```html
<label>Include failed builds</label>
<div class="upgrade-build-count">...</div>
<table>...</table>
<div id="upgrade-build-detail"></div>
```
No "Trigger New Build" in the table path! So when user has builds, they cannot trigger a new build from the Build step. The button only exists when builds.length === 0.  
**Severity:** **missing-feature** — Trigger New Build not available when build table is shown.

---

## Summary Table

| # | Issue | Severity |
|---|-------|----------|
| 1 | `upgrade-build-area` never populated | dead-code |
| 2 | `_targetStack` never set → GI/BaseOS always `--` in Compare | missing-feature |
| 3 | Hardcoded `#f39c12`, `#888`, `#e74c3c` in upgrade wizard | visual-bug |
| 4 | fetchErrBox selector `[style*="e74c3c"]` never matches | visual-bug |
| 5 | Source: no explicit "No branches found" empty state | visual-bug |
| 6 | Build table: no QA badge (API doesn't provide) | missing-feature |
| 7 | `renderBuildRow` dead code | dead-code |
| 8 | "Trigger New Build" only in empty-builds path, not when table shown | missing-feature |
