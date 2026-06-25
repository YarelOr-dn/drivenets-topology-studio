// ============================================================================
// TOPOLOGY GROUPS PANEL
// ============================================================================
// Unified floating draggable panel listing BOTH manual groups (objects bound
// together via ``groupId``/``groupLeaderId`` -- see ``topology-groups.js``)
// AND auto-derived bridge-domain groups (the ``_multiBDMetadata`` map that
// the BD legend already drives) in a single place.
//
// Why one panel?
// --------------
// Operators only have one mental model -- "what visual groups exist on the
// canvas and which are visible". Splitting that across two UIs (the legacy
// BD legend + ad-hoc multi-select grouping) made operators hunt for state.
// A single Groups panel:
//   * lists every group with a coloured row, name, member count, eye toggle
//   * lets the user rename / recolor / dissolve manual groups inline
//   * mirrors the BD legend behaviour for BD-derived groups
//   * persists open/closed/position/visibility per authenticated user
//     (``groups_panel_state_<username>``) -- never globally
//
// Multi-user discipline (per ``cursorrules``):
//   * localStorage key ALWAYS suffixed with the authenticated username via
//     :func:`_storageKey`. Anonymous fallback is the old global key so unit
//     tests / login flows don't 500.
//   * Visibility map for BD groups is the SAME ``editor._bdVisibility`` the
//     BD legend already owns -- no new shadow state to drift from.
//
// Lifecycle
// ---------
//   GroupsPanel.toggle(editor)           -- open/close
//   GroupsPanel.show(editor)             -- force open
//   GroupsPanel.hide(editor)             -- force close
//   GroupsPanel.refresh(editor)          -- repaint rows after canvas mutations
//   GroupsPanel.restoreIfNeeded(editor)  -- called from topology bootstrap
//
// Author: agent-edit 2026-04-30
// ============================================================================

'use strict';

(function () {

const PANEL_ID = 'groups-panel';
const HEADER_ID = 'groups-panel-header';
const BODY_ID = 'groups-panel-body';
const RESIZE_HANDLE_ID = 'groups-panel-resize';
const STYLE_ID = 'groups-panel-runtime-styles';
const DEFAULT_LEFT = 188;
const MIN_LEFT = 176;
const DYNAMIC_REFRESH_INTERVAL_MS = 600;

function _ensureGroupsPanelRuntimeStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
        #${PANEL_ID}.groups-panel {
            z-index: 999998 !important;
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.08), transparent 42%),
                rgba(15, 23, 42, 0.92) !important;
            border: 1px solid rgba(148, 163, 184, 0.22) !important;
            border-radius: 18px !important;
            box-shadow:
                0 18px 54px rgba(0, 0, 0, 0.48),
                0 6px 18px rgba(15, 23, 42, 0.35),
                inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
            backdrop-filter: blur(22px) saturate(155%);
            -webkit-backdrop-filter: blur(22px) saturate(155%);
            color: rgba(248,250,252,0.96) !important;
            font-family: 'Inter', 'Poppins', system-ui, sans-serif !important;
            display: flex !important;
            flex-direction: column !important;
            overflow: hidden !important;
            min-width: 280px !important;
            min-height: 220px !important;
        }
        #${PANEL_ID} .groups-panel-header {
            min-height: 58px;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 11px 12px 10px 14px;
            background:
                linear-gradient(90deg, rgba(0, 180, 216, 0.18), rgba(99, 102, 241, 0.10), transparent),
                rgba(255,255,255,0.035);
            border-bottom: 1px solid rgba(148,163,184,0.16);
            cursor: move;
            user-select: none;
        }
        body.dark-mode #${PANEL_ID}.groups-panel {
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.78), rgba(248, 250, 252, 0.92)),
                rgba(248, 250, 252, 0.94) !important;
            border-color: rgba(15, 23, 42, 0.11) !important;
            box-shadow:
                0 18px 54px rgba(15, 23, 42, 0.24),
                0 6px 18px rgba(15, 23, 42, 0.12),
                inset 0 1px 0 rgba(255, 255, 255, 0.85) !important;
            color: rgba(15, 23, 42, 0.95) !important;
        }
        body.dark-mode #${PANEL_ID} .groups-panel-header {
            background:
                linear-gradient(90deg, rgba(0, 180, 216, 0.16), rgba(99, 102, 241, 0.08), transparent),
                rgba(255,255,255,0.55);
            border-bottom-color: rgba(15,23,42,0.09);
        }
        #${PANEL_ID} .groups-panel-title,
        #${PANEL_ID} .groups-panel-header-actions,
        #${PANEL_ID} .groups-panel-row,
        #${PANEL_ID} .groups-panel-section-header {
            display: flex;
            align-items: center;
        }
        #${PANEL_ID} .groups-panel-title { gap: 10px; min-width: 0; }
        #${PANEL_ID} .groups-panel-title-icon {
            width: 30px;
            height: 30px;
            border-radius: 11px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            color: #fff;
            background: linear-gradient(135deg, #00B4D8, #0066FA);
            box-shadow: 0 8px 18px rgba(0,102,250,0.26), inset 0 1px 0 rgba(255,255,255,0.34);
        }
        #${PANEL_ID} .groups-panel-title-main { font-size: 13px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; line-height: 1.1; }
        #${PANEL_ID} .groups-panel-title-sub { margin-top: 3px; font-size: 10px; font-weight: 600; color: rgba(226,232,240,0.58); letter-spacing: .02em; }
        body.dark-mode #${PANEL_ID} .groups-panel-title-sub { color: rgba(51,65,85,0.58); }
        #${PANEL_ID} .groups-panel-header-actions { gap: 6px; }
        #${PANEL_ID} .groups-panel-icon-btn,
        #${PANEL_ID} .groups-panel-action,
        #${PANEL_ID} .groups-panel-mini-btn {
            cursor: pointer;
            border-radius: 9px;
            border: 1px solid rgba(148,163,184,0.22);
            background: rgba(255,255,255,0.07);
            color: rgba(226,232,240,0.86);
            transition: transform .15s ease, background .15s ease, border-color .15s ease, box-shadow .15s ease;
        }
        body.dark-mode #${PANEL_ID} .groups-panel-icon-btn,
        body.dark-mode #${PANEL_ID} .groups-panel-action,
        body.dark-mode #${PANEL_ID} .groups-panel-mini-btn {
            background: rgba(15,23,42,0.045);
            border-color: rgba(15,23,42,0.12);
            color: rgba(15,23,42,0.72);
        }
        #${PANEL_ID} .groups-panel-icon-btn,
        #${PANEL_ID} .groups-panel-action {
            width: 26px;
            height: 26px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        #${PANEL_ID} .groups-panel-icon-btn:hover,
        #${PANEL_ID} .groups-panel-action:hover,
        #${PANEL_ID} .groups-panel-mini-btn:hover {
            transform: translateY(-1px);
            border-color: rgba(0,180,216,0.36);
            box-shadow: 0 6px 14px rgba(0,102,250,0.15);
        }
        #${PANEL_ID} .groups-panel-body { flex: 1 1 auto; overflow-y: auto; padding: 12px; }
        #${PANEL_ID} .groups-panel-section { display: flex; flex-direction: column; gap: 10px; }
        #${PANEL_ID} .groups-panel-section + .groups-panel-section { margin-top: 14px; padding-top: 10px; border-top: 1px solid rgba(148,163,184,0.14); }
        #${PANEL_ID} .groups-panel-section-header { justify-content: space-between; gap: 10px; padding: 0 2px; }
        #${PANEL_ID} .groups-panel-section-actions { display: inline-flex; align-items: center; gap: 4px; flex-wrap: wrap; justify-content: flex-end; }
        #${PANEL_ID} .groups-panel-section-title { font-size: 10px; font-weight: 800; letter-spacing: .11em; text-transform: uppercase; color: rgba(226,232,240,0.64); }
        body.dark-mode #${PANEL_ID} .groups-panel-section-title { color: rgba(51,65,85,0.62); }
        #${PANEL_ID} .groups-panel-section-count,
        #${PANEL_ID} .groups-panel-count { background: rgba(148,163,184,0.12); border: 1px solid rgba(148,163,184,0.16); border-radius: 999px; padding: 2px 7px; font-size: 10px; font-weight: 800; color: rgba(226,232,240,0.78); }
        body.dark-mode #${PANEL_ID} .groups-panel-section-count,
        body.dark-mode #${PANEL_ID} .groups-panel-count { background: rgba(15,23,42,0.055); border-color: rgba(15,23,42,0.10); color: rgba(15,23,42,0.68); }
        #${PANEL_ID} .groups-panel-mini-btn { padding: 5px 9px; color: #67e8f9; border-color: rgba(0,180,216,0.30); font-size: 10px; font-weight: 800; letter-spacing: .02em; }
        body.dark-mode #${PANEL_ID} .groups-panel-mini-btn { color: #0369a1; }
        #${PANEL_ID} .groups-panel-mini-btn.is-primary {
            color: #fff;
            background: linear-gradient(135deg, #00B4D8, #0066FA);
            border-color: rgba(255,255,255,0.24);
            box-shadow: 0 6px 16px rgba(0,102,250,0.22), inset 0 1px 0 rgba(255,255,255,0.26);
        }
        #${PANEL_ID} .groups-panel-section-body { display: flex; flex-direction: column; gap: 7px; }
        #${PANEL_ID} .groups-panel-row {
            position: relative;
            gap: 10px;
            min-height: 54px;
            padding: 9px 9px 9px 12px;
            border-radius: 13px;
            cursor: pointer;
            background:
                linear-gradient(90deg, color-mix(in srgb, var(--group-color, #00B4D8) 22%, rgba(15,23,42,0.86)) 0%, rgba(15,23,42,0.72) 56%, rgba(15,23,42,0.64) 100%);
            border: 1px solid color-mix(in srgb, var(--group-color, #00B4D8) 36%, rgba(148,163,184,0.17));
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.08), 0 4px 12px rgba(0,0,0,0.14);
        }
        #${PANEL_ID} .groups-panel-row:hover { transform: translateY(-1px); box-shadow: inset 0 1px 0 rgba(255,255,255,0.10), 0 7px 18px color-mix(in srgb, var(--group-color, #00B4D8) 16%, rgba(0,0,0,0.22)); }
        body.dark-mode #${PANEL_ID} .groups-panel-row {
            background:
                linear-gradient(90deg, color-mix(in srgb, var(--group-color, #00B4D8) 15%, white) 0%, rgba(255,255,255,0.80) 56%, rgba(255,255,255,0.72) 100%);
            border-color: color-mix(in srgb, var(--group-color, #00B4D8) 28%, rgba(15,23,42,0.11));
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.70), 0 4px 12px rgba(15,23,42,0.07);
        }
        #${PANEL_ID} .groups-panel-row.is-hidden { opacity: 0.62; filter: saturate(0.50); }
        #${PANEL_ID} .groups-panel-accent { position: absolute; left: 0; top: 9px; bottom: 9px; width: 4px; border-radius: 999px; background: var(--group-color, #00B4D8); box-shadow: 0 0 14px color-mix(in srgb, var(--group-color, #00B4D8) 46%, transparent); }
        #${PANEL_ID} .groups-panel-swatch { width: 28px; height: 28px; border-radius: 10px; flex-shrink: 0; border: 1px solid rgba(255,255,255,0.36); box-shadow: inset 0 1px 0 rgba(255,255,255,0.28), 0 5px 12px color-mix(in srgb, var(--group-color, #00B4D8) 26%, transparent); }
        #${PANEL_ID} .groups-panel-main { min-width: 0; flex: 1 1 auto; display: flex; flex-direction: column; gap: 3px; }
        #${PANEL_ID} .groups-panel-name { font-size: 12.5px; font-weight: 800; letter-spacing: .01em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        #${PANEL_ID} .groups-panel-meta { font-size: 10px; font-weight: 650; letter-spacing: .02em; color: rgba(203,213,225,0.58); }
        body.dark-mode #${PANEL_ID} .groups-panel-meta { color: rgba(51,65,85,0.54); }
        #${PANEL_ID} .groups-panel-actions-inline { display: inline-flex; gap: 4px; align-items: center; flex-shrink: 0; }
        #${PANEL_ID} .groups-panel-visibility {
            width: 30px;
            height: 30px;
            border-radius: 10px;
            color: #4ade80;
            border-color: rgba(74,222,128,0.38);
            background: rgba(74,222,128,0.11);
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
        }
        #${PANEL_ID} .groups-panel-visibility.is-off { color: #f59e0b; border-color: rgba(245,158,11,0.34); background: rgba(245,158,11,0.09); }
        #${PANEL_ID} .groups-panel-visibility::after {
            content: "";
            position: absolute;
            right: 3px;
            bottom: 3px;
            width: 7px;
            height: 7px;
            border-radius: 2px;
            background: #4ade80;
            box-shadow: 0 0 0 1px rgba(15,23,42,0.55);
        }
        #${PANEL_ID} .groups-panel-visibility.is-off::after { background: transparent; box-shadow: inset 0 0 0 1px currentColor; }
        #${PANEL_ID} .groups-panel-rename { color: #67e8f9; border-color: rgba(0,180,216,0.28); background: rgba(0,180,216,0.08); }
        #${PANEL_ID} .groups-panel-empty {
            color: rgba(203,213,225,0.58);
            font-size: 12px;
            line-height: 1.45;
            padding: 22px 16px;
            text-align: center;
            border: 1px dashed rgba(148,163,184,0.22);
            border-radius: 14px;
            background: rgba(255,255,255,0.045);
        }
        #${PANEL_ID} .groups-panel-empty strong { display: block; color: rgba(248,250,252,0.90); font-size: 13px; margin-bottom: 4px; }
        body.dark-mode #${PANEL_ID} .groups-panel-empty { color: rgba(51,65,85,0.58); background: rgba(15,23,42,0.035); border-color: rgba(15,23,42,0.12); }
        body.dark-mode #${PANEL_ID} .groups-panel-empty strong { color: rgba(15,23,42,0.86); }
        #${PANEL_ID} .groups-panel-resize { position: absolute; right: 0; bottom: 0; width: 14px; height: 14px; cursor: nwse-resize; }
        #${PANEL_ID}.groups-panel-collapsed { height: 58px !important; }
        #${PANEL_ID}.groups-panel-collapsed .groups-panel-body,
        #${PANEL_ID}.groups-panel-collapsed .groups-panel-resize { display: none !important; }

        /* Theme variants. The earlier rules provide a fallback; these final
           selectors intentionally win so body.dark-mode is always the dark
           glass variant and normal mode is the light glass variant. */
        body:not(.dark-mode) #${PANEL_ID}.groups-panel {
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.78), rgba(248, 250, 252, 0.92)),
                rgba(248, 250, 252, 0.94) !important;
            border-color: rgba(15, 23, 42, 0.11) !important;
            box-shadow:
                0 18px 54px rgba(15, 23, 42, 0.24),
                0 6px 18px rgba(15, 23, 42, 0.12),
                inset 0 1px 0 rgba(255, 255, 255, 0.85) !important;
            color: rgba(15, 23, 42, 0.95) !important;
        }
        body:not(.dark-mode) #${PANEL_ID} .groups-panel-header {
            background:
                linear-gradient(90deg, rgba(0, 180, 216, 0.16), rgba(99, 102, 241, 0.08), transparent),
                rgba(255,255,255,0.55);
            border-bottom-color: rgba(15,23,42,0.09);
        }
        body:not(.dark-mode) #${PANEL_ID} .groups-panel-title-sub { color: rgba(51,65,85,0.58); }
        body:not(.dark-mode) #${PANEL_ID} .groups-panel-icon-btn,
        body:not(.dark-mode) #${PANEL_ID} .groups-panel-action,
        body:not(.dark-mode) #${PANEL_ID} .groups-panel-mini-btn {
            background: rgba(15,23,42,0.045);
            border-color: rgba(15,23,42,0.12);
            color: rgba(15,23,42,0.72);
        }
        body:not(.dark-mode) #${PANEL_ID} .groups-panel-section-title { color: rgba(51,65,85,0.62); }
        body:not(.dark-mode) #${PANEL_ID} .groups-panel-section-count,
        body:not(.dark-mode) #${PANEL_ID} .groups-panel-count {
            background: rgba(15,23,42,0.055);
            border-color: rgba(15,23,42,0.10);
            color: rgba(15,23,42,0.68);
        }
        body:not(.dark-mode) #${PANEL_ID} .groups-panel-mini-btn { color: #0369a1; }
        body:not(.dark-mode) #${PANEL_ID} .groups-panel-row {
            background:
                linear-gradient(90deg, color-mix(in srgb, var(--group-color, #00B4D8) 15%, white) 0%, rgba(255,255,255,0.80) 56%, rgba(255,255,255,0.72) 100%);
            border-color: color-mix(in srgb, var(--group-color, #00B4D8) 28%, rgba(15,23,42,0.11));
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.70), 0 4px 12px rgba(15,23,42,0.07);
        }
        body:not(.dark-mode) #${PANEL_ID} .groups-panel-meta { color: rgba(51,65,85,0.54); }
        body:not(.dark-mode) #${PANEL_ID} .groups-panel-empty {
            color: rgba(51,65,85,0.58);
            background: rgba(15,23,42,0.035);
            border-color: rgba(15,23,42,0.12);
        }
        body:not(.dark-mode) #${PANEL_ID} .groups-panel-empty strong { color: rgba(15,23,42,0.86); }

        body.dark-mode #${PANEL_ID}.groups-panel {
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.08), transparent 42%),
                rgba(15, 23, 42, 0.92) !important;
            border-color: rgba(148, 163, 184, 0.22) !important;
            box-shadow:
                0 18px 54px rgba(0, 0, 0, 0.48),
                0 6px 18px rgba(15, 23, 42, 0.35),
                inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
            color: rgba(248,250,252,0.96) !important;
        }
        body.dark-mode #${PANEL_ID} .groups-panel-header {
            background:
                linear-gradient(90deg, rgba(0, 180, 216, 0.18), rgba(99, 102, 241, 0.10), transparent),
                rgba(255,255,255,0.035);
            border-bottom-color: rgba(148,163,184,0.16);
        }
        body.dark-mode #${PANEL_ID} .groups-panel-title-sub { color: rgba(226,232,240,0.58); }
        body.dark-mode #${PANEL_ID} .groups-panel-icon-btn,
        body.dark-mode #${PANEL_ID} .groups-panel-action,
        body.dark-mode #${PANEL_ID} .groups-panel-mini-btn {
            background: rgba(255,255,255,0.07);
            border-color: rgba(148,163,184,0.22);
            color: rgba(226,232,240,0.86);
        }
        body.dark-mode #${PANEL_ID} .groups-panel-section-title { color: rgba(226,232,240,0.64); }
        body.dark-mode #${PANEL_ID} .groups-panel-section-count,
        body.dark-mode #${PANEL_ID} .groups-panel-count {
            background: rgba(148,163,184,0.12);
            border-color: rgba(148,163,184,0.16);
            color: rgba(226,232,240,0.78);
        }
        body.dark-mode #${PANEL_ID} .groups-panel-mini-btn { color: #67e8f9; }
        body.dark-mode #${PANEL_ID} .groups-panel-row {
            background:
                linear-gradient(90deg, color-mix(in srgb, var(--group-color, #00B4D8) 22%, rgba(15,23,42,0.86)) 0%, rgba(15,23,42,0.72) 56%, rgba(15,23,42,0.64) 100%);
            border-color: color-mix(in srgb, var(--group-color, #00B4D8) 36%, rgba(148,163,184,0.17));
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.08), 0 4px 12px rgba(0,0,0,0.14);
        }
        body.dark-mode #${PANEL_ID} .groups-panel-meta { color: rgba(203,213,225,0.58); }
        body.dark-mode #${PANEL_ID} .groups-panel-empty {
            color: rgba(203,213,225,0.58);
            background: rgba(255,255,255,0.045);
            border-color: rgba(148,163,184,0.22);
        }
        body.dark-mode #${PANEL_ID} .groups-panel-empty strong { color: rgba(248,250,252,0.90); }
    `;
    document.head.appendChild(style);
}

// ----------------------------------------------------------------------------
// Per-user storage helpers
// ----------------------------------------------------------------------------
function _storageKey() {
    try {
        const auth = window.TopologyAuth;
        const u = auth && auth.getCurrentUser && auth.getCurrentUser();
        const username = u && u.username ? String(u.username).trim() : '';
        if (username) return 'groups_panel_state_' + username;
    } catch (_) {}
    return 'groups_panel_state';
}

function _loadState() {
    try {
        const raw = localStorage.getItem(_storageKey());
        if (raw) return JSON.parse(raw);
    } catch (_) {}
    return {};
}

function _saveState(state) {
    try {
        localStorage.setItem(_storageKey(), JSON.stringify(state));
    } catch (_) {}
}

// ----------------------------------------------------------------------------
// Color helpers
// ----------------------------------------------------------------------------
const FALLBACK_PALETTE = [
    '#00B4D8', '#FF5E1F', '#2ecc71', '#9b59b6', '#f39c12',
    '#1abc9c', '#e67e22', '#3b82f6', '#d35400', '#16a085',
    '#27ae60', '#8e44ad', '#f1c40f', '#c0392b', '#64748b'
];
function _colorForId(id, fallbackIdx) {
    const editor = _resolveEditor();
    if (editor?.groups?.colorForGroupId) return editor.groups.colorForGroupId(id);
    if (!id) return FALLBACK_PALETTE[(fallbackIdx || 0) % FALLBACK_PALETTE.length];
    let hash = 0;
    for (let i = 0; i < id.length; i++) hash = ((hash << 5) - hash + id.charCodeAt(i)) | 0;
    return FALLBACK_PALETTE[Math.abs(hash) % FALLBACK_PALETTE.length];
}

function _normalizeColor(color, fallback) {
    const value = String(color || '').trim();
    if (/^#[0-9a-fA-F]{6}$/.test(value) || /^#[0-9a-fA-F]{3}$/.test(value)) return value;
    return fallback || '#00B4D8';
}

function _hydrateVisibility(editor) {
    if (!editor) return;
    const state = _loadState();
    editor._groupVisibility = { ...(editor._groupVisibility || {}), ...(state.manualGroupVisibility || {}) };
    if (!Array.isArray(editor._emptyManualGroups)) {
        editor._emptyManualGroups = Array.isArray(state.emptyManualGroups)
            ? state.emptyManualGroups.filter(g => g && g.id)
            : [];
    }
    if (editor.groups && typeof editor.groups.applyVisibility === 'function') {
        editor.groups.applyVisibility();
    }
}

function _persistVisibility(editor) {
    if (!editor) return;
    const cur = _loadState();
    cur.manualGroupVisibility = { ...(editor._groupVisibility || {}) };
    _saveState(cur);
}

function _persistEmptyGroups(editor) {
    if (!editor) return;
    const cur = _loadState();
    cur.emptyManualGroups = (editor._emptyManualGroups || []).map(g => ({
        id: g.id,
        name: g.name || '',
        color: _normalizeColor(g.color, _colorForId(g.id)),
        visible: g.visible !== false,
        createdAt: g.createdAt || Date.now()
    }));
    _saveState(cur);
}

function _setGroupVisibility(editor, groupId, visible) {
    if (!editor || !groupId) return;
    if (editor.groups && typeof editor.groups.setGroupVisibility === 'function') {
        editor.groups.setGroupVisibility(groupId, visible, { refreshPanel: false });
    } else {
        if (!editor._groupVisibility) editor._groupVisibility = {};
        editor._groupVisibility[groupId] = visible !== false;
        editor.objects.forEach(obj => {
            if (obj.groupId === groupId) obj._hidden = visible === false;
        });
        if (typeof editor.draw === 'function') editor.draw();
    }
    _persistVisibility(editor);
}

// ----------------------------------------------------------------------------
// Group data extraction from editor state
// ----------------------------------------------------------------------------
function _readManualGroups(editor) {
    if (!editor || !Array.isArray(editor.objects)) return [];
    const map = new Map();
    if (Array.isArray(editor._emptyManualGroups)) {
        editor._emptyManualGroups.forEach((group, idx) => {
            if (!group || !group.id) return;
            map.set(group.id, {
                kind: 'manual',
                id: group.id,
                name: group.name || '',
                color: _normalizeColor(group.color, _colorForId(group.id, idx)),
                visible: group.visible !== false && ((editor._groupVisibility || {})[group.id] !== false),
                members: [],
                leaderId: null,
                empty: true
            });
        });
    }
    editor.objects.forEach(obj => {
        if (!obj || !obj.groupId) return;
        if (!map.has(obj.groupId)) {
            map.set(obj.groupId, {
                kind: 'manual',
                id: obj.groupId,
                name: obj.groupName || '',
                color: obj.groupColor || '',
                visible: editor.groups?.isGroupVisible ? editor.groups.isGroupVisible(obj.groupId) : ((editor._groupVisibility || {})[obj.groupId] !== false),
                members: [],
                leaderId: obj.groupLeaderId || null,
                empty: false
            });
        }
        const group = map.get(obj.groupId);
        group.members.push(obj);
        group.empty = false;
        // First object that carries a name/color wins -- members are
        // expected to share these but we tolerate drift.
        if (!group.name && obj.groupName) {
            group.name = obj.groupName;
        }
        if (!group.color && obj.groupColor) {
            group.color = obj.groupColor;
        }
    });
    let idx = 0;
    return Array.from(map.values()).map(g => {
        if (!g.color) {
            g.color = editor.groups?.ensureGroupColor ? editor.groups.ensureGroupColor(g.id) : _colorForId(g.id, idx);
        }
        idx += 1;
        return g;
    }).sort((a, b) => {
        const an = (a.name || a.id || '').toLowerCase();
        const bn = (b.name || b.id || '').toLowerCase();
        return an.localeCompare(bn);
    });
}

// ----------------------------------------------------------------------------
// DOM helpers
// ----------------------------------------------------------------------------
function _esc(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function _renderManualRow(group) {
    const safeName = _esc(group.name || group.id);
    const memberCount = group.members.length;
    const visible = group.visible !== false;
    const title = visible ? 'Hide group' : 'Show group';
    const metaText = group.empty
        ? 'Empty group - add objects later'
        : (visible ? 'Visible on canvas' : 'Hidden on canvas');
    return `
        <div class="groups-panel-row ${visible ? '' : 'is-hidden'}" data-group-kind="manual" data-group-id="${_esc(group.id)}" style="--group-color:${_esc(group.color)};" title="Click row to ${visible ? 'hide' : 'show'} this group">
            <span class="groups-panel-accent" aria-hidden="true"></span>
            <span class="groups-panel-swatch" style="background:${_esc(group.color)};"></span>
            <span class="groups-panel-main">
                <span class="groups-panel-name">${safeName}</span>
                <span class="groups-panel-meta">${metaText}</span>
            </span>
            <span class="groups-panel-count" title="${group.empty ? 'No members yet' : 'Members'}">${memberCount}</span>
            <span class="groups-panel-actions-inline">
                <button class="groups-panel-action groups-panel-visibility ${visible ? '' : 'is-off'}" title="${title}" aria-pressed="${visible ? 'true' : 'false'}">
                    <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
                        ${visible
                            ? '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/>'
                            : '<path d="M17.94 17.94A10.94 10.94 0 0 1 12 19C5 19 1 12 1 12a20.29 20.29 0 0 1 5.06-5.94"/><path d="M9.9 4.24A10.77 10.77 0 0 1 12 4c7 0 11 8 11 8a20.63 20.63 0 0 1-3.17 4.35"/><path d="M1 1l22 22"/><path d="M9.53 9.53A3.5 3.5 0 0 0 12 15.5c.97 0 1.85-.39 2.48-1.02"/>'
                        }
                    </svg>
                </button>
                <button class="groups-panel-action groups-panel-rename" title="Rename group">
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/>
                    </svg>
                </button>
                <button class="groups-panel-action groups-panel-select" title="Select all members">
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
                    </svg>
                </button>
                <button class="groups-panel-action groups-panel-color" title="Change color">
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="13.5" cy="6.5" r=".5"/><circle cx="17.5" cy="10.5" r=".5"/>
                        <circle cx="8.5" cy="7.5" r=".5"/><circle cx="6.5" cy="12.5" r=".5"/>
                        <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/>
                    </svg>
                </button>
                <button class="groups-panel-action groups-panel-dissolve" title="Dissolve group">
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
                        <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                </button>
            </span>
        </div>
    `;
}

function _renderBody(editor) {
    const manual = _readManualGroups(editor);
    const hiddenCount = manual.filter(g => g.visible === false).length;

    const manualRows = manual.length
        ? manual.map(_renderManualRow).join('')
        : '<div class="groups-panel-empty"><strong>No groups yet</strong>Create an empty group here, then add objects later from the object Group actions.</div>';

    return `
        <div class="groups-panel-section">
            <div class="groups-panel-section-header">
                <span class="groups-panel-section-title">Manual groups <span class="groups-panel-section-count">${manual.length}</span></span>
                <div class="groups-panel-section-actions">
                    ${manual.length ? `<button class="groups-panel-mini-btn" data-act="manual-show-all" title="Show all manual groups">Show all</button>` : ''}
                    ${manual.length && hiddenCount < manual.length ? `<button class="groups-panel-mini-btn" data-act="manual-hide-all" title="Hide all manual groups">Hide all</button>` : ''}
                    <button class="groups-panel-mini-btn is-primary" data-act="manual-from-selection" title="Create an empty group or include the current multi-selection">+ New</button>
                </div>
            </div>
            <div class="groups-panel-section-body" data-section="manual">${manualRows}</div>
        </div>
    `;
}

function _groupPanelSignature(editor) {
    if (!editor) return 'no-editor';
    const manual = _readManualGroups(editor).map(g => ({
        id: g.id,
        name: g.name || '',
        color: _normalizeColor(g.color, _colorForId(g.id)),
        visible: g.visible !== false,
        count: g.members.length,
        leaderId: g.leaderId || '',
        empty: !!g.empty,
        members: (g.members || []).map(m => m && m.id).filter(Boolean).sort()
    }));
    const topologyKey = [
        editor.currentTopologyId || '',
        editor.currentTopologyName || '',
        editor.currentTopologyFile || '',
        editor.currentTopologyMetadata?.name || '',
        Array.isArray(editor.objects) ? editor.objects.length : 0,
        document.body.classList.contains('dark-mode') ? 'dark' : 'light'
    ];
    return JSON.stringify({ topologyKey, manual });
}

function _requestRefresh(editor, reason) {
    const panel = document.getElementById(PANEL_ID);
    if (!panel || !window.GroupsPanel || !editor) return;
    if (panel._groupsPanelRefreshPending) return;
    panel._groupsPanelRefreshPending = true;
    requestAnimationFrame(() => {
        panel._groupsPanelRefreshPending = false;
        const latest = _groupPanelSignature(editor);
        if (latest === panel._groupsPanelLastSignature && reason !== 'force') return;
        panel._groupsPanelLastSignature = latest;
        window.GroupsPanel.refresh(editor, { skipSignatureUpdate: true });
    });
}

function _wireDynamicUpdates(editor, panel) {
    if (!editor || !panel || panel._groupsPanelDynamicCleanup) return;

    const refresh = (reason) => _requestRefresh(editor, reason);
    panel._groupsPanelLastSignature = _groupPanelSignature(editor);

    const events = [
        'topology:loaded',
        'topology:saved',
        'topology:changed',
        'topology:objects-changed',
        'topology:selection-changed',
        'topology:groups-changed',
        'topology-ai:applied-edits',
        'topology-generator:merged',
        'topology-generator:saved',
    ];
    const listeners = events.map(name => {
        const fn = () => refresh(name);
        document.addEventListener(name, fn);
        window.addEventListener(name, fn);
        return { name, fn };
    });

    const observer = new MutationObserver(() => refresh('theme'));
    observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });

    const timer = window.setInterval(() => refresh('poll'), DYNAMIC_REFRESH_INTERVAL_MS);

    panel._groupsPanelDynamicCleanup = () => {
        listeners.forEach(({ name, fn }) => {
            document.removeEventListener(name, fn);
            window.removeEventListener(name, fn);
        });
        observer.disconnect();
        window.clearInterval(timer);
        panel._groupsPanelDynamicCleanup = null;
    };
}

// ----------------------------------------------------------------------------
// Drag implementation (lightweight, uses fixed positioning)
// ----------------------------------------------------------------------------
function _wireDrag(panel, header, onMoveEnd) {
    let dragging = false;
    let dx = 0;
    let dy = 0;

    header.addEventListener('mousedown', (e) => {
        if (e.target.tagName === 'BUTTON' || e.target.closest('button')) return;
        if (e.button !== 0) return;
        dragging = true;
        const rect = panel.getBoundingClientRect();
        dx = e.clientX - rect.left;
        dy = e.clientY - rect.top;
        header.style.cursor = 'grabbing';
        document.body.style.userSelect = 'none';
        e.preventDefault();
    });

    function onMove(e) {
        if (!dragging) return;
        const newLeft = Math.max(0, Math.min(window.innerWidth - 80, e.clientX - dx));
        const newTop = Math.max(0, Math.min(window.innerHeight - 40, e.clientY - dy));
        panel.style.left = newLeft + 'px';
        panel.style.top = newTop + 'px';
    }
    function onUp() {
        if (!dragging) return;
        dragging = false;
        header.style.cursor = 'move';
        document.body.style.userSelect = '';
        if (typeof onMoveEnd === 'function') onMoveEnd();
    }
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);

    // Cleanup hook if the panel is removed.
    panel._groupsPanelDragCleanup = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
    };
}

// ----------------------------------------------------------------------------
// Manual group operations (extends GroupManager with names + colors)
// ----------------------------------------------------------------------------
function _promptName(editor, oldName) {
    const defaultValue = oldName || '';
    return new Promise((resolve) => {
        if (editor && typeof editor.showInputDialog === 'function') {
            try {
                editor.showInputDialog(
                    'Group name',
                    'Enter group name',
                    (value) => {
                        resolve(value);
                    },
                    defaultValue
                );
                return;
            } catch (_) {}
        }
        const fallback = window.prompt('Group name', defaultValue);
        resolve(fallback);
    });
}

function _selectGroupMembers(editor, group) {
    if (!editor || !group || !Array.isArray(group.members)) return;
    if (group.visible === false) {
        if (typeof editor.showToast === 'function') {
            editor.showToast('Show the group before selecting its members.', 'info');
        }
        return;
    }
    editor.selectedObjects = group.members.slice();
    editor.selectedObject = group.members[0] || null;
    if (typeof editor.draw === 'function') editor.draw();
    if (typeof editor.updateSelectionUI === 'function') editor.updateSelectionUI();
}

function _renameGroup(editor, group, newName) {
    if (!group || !Array.isArray(group.members)) return;
    if (typeof editor.saveState === 'function') editor.saveState();
    if (group.empty) {
        const empty = (editor._emptyManualGroups || []).find(g => g.id === group.id);
        if (empty) empty.name = newName;
        _persistEmptyGroups(editor);
        return;
    }
    group.members.forEach(obj => { obj.groupName = newName; });
    if (typeof editor.draw === 'function') editor.draw();
}

function _recolorGroup(editor, group, newColor) {
    if (!group || !Array.isArray(group.members)) return;
    if (typeof editor.saveState === 'function') editor.saveState();
    if (group.empty) {
        const empty = (editor._emptyManualGroups || []).find(g => g.id === group.id);
        if (empty) empty.color = newColor;
        _persistEmptyGroups(editor);
        return;
    }
    group.members.forEach(obj => { obj.groupColor = newColor; });
    if (typeof editor.draw === 'function') editor.draw();
}

function _showGroupColorPalette(editor, group, anchor) {
    if (!editor || !group || !anchor) return;
    const currentColor = _normalizeColor(group.color, '#00B4D8');
    if (!window.ColorPopups) {
        const newColor = window.prompt('Group color (hex, e.g. #00B4D8)', currentColor);
        if (newColor) {
            _recolorGroup(editor, group, _normalizeColor(newColor, currentColor));
            window.GroupsPanel.refresh(editor);
        }
        return;
    }

    const existing = document.getElementById('group-color-palette-popup');
    if (existing) existing.remove();
    const otherColorPopup = document.getElementById('color-palette-popup');
    if (otherColorPopup) otherColorPopup.remove();

    const popup = document.createElement('div');
    popup.id = 'group-color-palette-popup';
    popup.className = 'color-popup color-popup--liquid';
    popup.setAttribute('role', 'dialog');
    popup.setAttribute('aria-label', 'Group color picker');

    const title = document.createElement('div');
    title.className = 'color-popup-title';
    const titleIcon = (typeof appIcon === 'function') ? appIcon('palette') : '';
    title.innerHTML = `${titleIcon}<span>Group Colors</span>`;
    popup.appendChild(title);

    const applyColor = (color) => {
        const normalized = _normalizeColor(color, currentColor);
        const latestGroup = _readManualGroups(editor).find(g => g.id === group.id) || group;
        _recolorGroup(editor, latestGroup, normalized);
        if (typeof editor.addRecentColor === 'function') editor.addRecentColor(normalized);
        window.GroupsPanel.refresh(editor);
    };

    const addColorRow = (label, colors, size) => {
        const visible = (colors || []).filter(Boolean);
        if (!visible.length) return;
        popup.appendChild(window.ColorPopups._sectionLabel('palette', label));
        const row = window.ColorPopups._container(label === 'Palette' ? 'color-popup-row--grid-5' : 'color-popup-row--flex');
        if (label === 'Palette') row.style.gridTemplateColumns = 'repeat(5, 1fr)';
        visible.forEach(color => {
            const normalized = _normalizeColor(color, currentColor);
            const swatch = window.ColorPopups._createSwatch(normalized, size, () => applyColor(normalized), {
                isActive: currentColor.toLowerCase() === normalized.toLowerCase(),
                isPinned: Array.isArray(editor.pinnedColors)
                    && editor.pinnedColors.some(c => String(c).toLowerCase() === normalized.toLowerCase()),
            });
            row.appendChild(swatch);
        });
        popup.appendChild(row);
    };

    const pinned = Array.isArray(editor.pinnedColors) ? editor.pinnedColors : [];
    const recent = Array.isArray(editor.recentColors) ? editor.recentColors.slice(0, Math.max(1, editor.recentColorsCap || 8)) : [];
    addColorRow(pinned.length ? 'Pinned + Recent' : 'Recent', pinned.concat(recent), 32);
    addColorRow('Palette', window.ColorPopups.compactColors || window.ColorPopups.standardColors || FALLBACK_PALETTE, 32);
    popup.appendChild(window.ColorPopups._buildCustomPicker(editor, {}, currentColor, applyColor));

    document.body.appendChild(popup);
    const anchorRect = anchor.getBoundingClientRect();
    popup.style.left = `${anchorRect.left}px`;
    popup.style.top = `${anchorRect.bottom + 8}px`;
    const popupRect = popup.getBoundingClientRect();
    if (popupRect.right > window.innerWidth) popup.style.left = `${window.innerWidth - popupRect.width - 10}px`;
    if (popupRect.bottom > window.innerHeight) popup.style.top = `${anchorRect.top - popupRect.height - 8}px`;
    if (popupRect.left < 0) popup.style.left = '10px';

    if (typeof window.ColorPopups._attachKeyboardNav === 'function') {
        window.ColorPopups._attachKeyboardNav(popup);
    }

    const dismiss = (e) => {
        if (e.type === 'keydown' && e.key !== 'Escape') return;
        if (e.type !== 'keydown' && (popup.contains(e.target) || e.target === anchor)) return;
        popup.remove();
        document.removeEventListener('mousedown', dismiss, true);
        document.removeEventListener('keydown', dismiss, true);
    };
    setTimeout(() => {
        document.addEventListener('mousedown', dismiss, true);
        document.addEventListener('keydown', dismiss, true);
    }, 0);
}

function _dissolveGroup(editor, group) {
    if (!group || !Array.isArray(group.members)) return;
    if (typeof editor.saveState === 'function') editor.saveState();
    if (group.empty) {
        editor._emptyManualGroups = (editor._emptyManualGroups || []).filter(g => g.id !== group.id);
        if (editor._groupVisibility) delete editor._groupVisibility[group.id];
        _persistEmptyGroups(editor);
        _persistVisibility(editor);
        if (typeof editor.showToast === 'function') {
            editor.showToast('Empty group removed', 'info');
        }
        return;
    }
    group.members.forEach(obj => {
        obj.groupId = null;
        obj.groupLeaderId = null;
        obj.groupOffsetX = null;
        obj.groupOffsetY = null;
        obj.groupName = null;
        obj.groupColor = null;
    });
    _removeEmptyGroupDefinition(editor, group.id);
    if (typeof editor.showToast === 'function') {
        editor.showToast('Group dissolved', 'info');
    }
    if (typeof editor.draw === 'function') editor.draw();
}

function _removeEmptyGroupDefinition(editor, groupId) {
    if (!editor || !groupId || !Array.isArray(editor._emptyManualGroups)) return;
    const before = editor._emptyManualGroups.length;
    editor._emptyManualGroups = editor._emptyManualGroups.filter(g => g.id !== groupId);
    if (editor._emptyManualGroups.length !== before) {
        _persistEmptyGroups(editor);
    }
}

function _createEmptyManualGroup(editor, name, color) {
    if (!editor) return null;
    if (!Array.isArray(editor._emptyManualGroups)) editor._emptyManualGroups = [];
    const groupId = editor.groups && typeof editor.groups.generateId === 'function'
        ? editor.groups.generateId()
        : 'group_' + Date.now() + '_' + Math.random().toString(36).slice(2, 9);
    const groupColor = _normalizeColor(color, _colorForId(groupId, editor._emptyManualGroups.length));
    const nextNumber = _readManualGroups(editor).length + 1;
    const displayName = String(name || '').trim() || `Group ${nextNumber}`;

    editor._emptyManualGroups.push({
        id: groupId,
        name: displayName,
        color: groupColor,
        visible: true,
        createdAt: Date.now()
    });
    if (!editor._groupVisibility) editor._groupVisibility = {};
    editor._groupVisibility[groupId] = true;
    _persistEmptyGroups(editor);
    _persistVisibility(editor);
    if (typeof editor.showToast === 'function') {
        editor.showToast(`Created empty group "${displayName}"`, 'success');
    }
    return groupId;
}

// Group the current canvas multi-selection into a NEW manual group, or create
// an empty manual group when fewer than two objects are selected.
function _groupCurrentSelection(editor, name, color) {
    const selected = editor && editor.selectedObjects;
    if (!selected || selected.length < 2) {
        return _createEmptyManualGroup(editor, name, color);
    }
    if (typeof editor.saveState === 'function') editor.saveState();

    // Reuse GroupManager when present so leader/offset bookkeeping is
    // identical to the existing right-click "Group" path.
    let groupId = null;
    if (editor.groups && typeof editor.groups.groupSelected === 'function') {
        editor.groups.groupSelected();
        groupId = (selected[0] && selected[0].groupId) || null;
    } else {
        groupId = 'group_' + Date.now() + '_' + Math.random().toString(36).slice(2, 9);
        const leader = selected[0];
        selected.forEach(obj => {
            obj.groupId = groupId;
            obj.groupLeaderId = leader.id;
            obj.groupOffsetX = (obj.x || 0) - (leader.x || 0);
            obj.groupOffsetY = (obj.y || 0) - (leader.y || 0);
        });
    }

    if (groupId) {
        _removeEmptyGroupDefinition(editor, groupId);
        selected.forEach(obj => {
            if (name) obj.groupName = name;
            if (color) obj.groupColor = color;
        });
    }
    if (typeof editor.draw === 'function') editor.draw();
    if (typeof editor.scheduleAutoSave === 'function') editor.scheduleAutoSave();
    return groupId;
}

// ----------------------------------------------------------------------------
// Event wiring
// ----------------------------------------------------------------------------
function _wireBody(editor, body) {
    body.addEventListener('click', async (e) => {
        const row = e.target.closest('.groups-panel-row');
        const sectionAct = e.target.closest('.groups-panel-section-actions [data-act]');

        if (sectionAct) {
            const act = sectionAct.getAttribute('data-act');
            if (act === 'manual-from-selection') {
                const name = await _promptName(editor, '');
                if (name === null || name === undefined) return;
                _groupCurrentSelection(editor, String(name).trim() || null, null);
                window.GroupsPanel.refresh(editor);
            } else if (act === 'manual-show-all' || act === 'manual-hide-all') {
                const visible = act === 'manual-show-all';
                if (editor.groups && typeof editor.groups.setAllGroupsVisibility === 'function') {
                    editor.groups.setAllGroupsVisibility(visible, { refreshPanel: false });
                } else {
                    const groups = _readManualGroups(editor);
                    groups.forEach(g => _setGroupVisibility(editor, g.id, visible));
                }
                _persistVisibility(editor);
                window.GroupsPanel.refresh(editor);
            }
            return;
        }

        if (!row) return;
        const kind = row.getAttribute('data-group-kind');
        const groupId = row.getAttribute('data-group-id');

        if (kind === 'manual') {
            const groups = _readManualGroups(editor);
            const group = groups.find(g => g.id === groupId);
            if (!group) return;

            if (e.target.closest('.groups-panel-select')) {
                _selectGroupMembers(editor, group);
            } else if (e.target.closest('.groups-panel-visibility')) {
                _setGroupVisibility(editor, group.id, group.visible === false);
                window.GroupsPanel.refresh(editor);
            } else if (e.target.closest('.groups-panel-rename')) {
                const newName = await _promptName(editor, group.name || '');
                if (newName === null || newName === undefined) return;
                _renameGroup(editor, group, String(newName).trim());
                window.GroupsPanel.refresh(editor);
            } else if (e.target.closest('.groups-panel-color')) {
                _showGroupColorPalette(editor, group, e.target.closest('.groups-panel-color'));
            } else if (e.target.closest('.groups-panel-dissolve')) {
                if (window.confirm(`Dissolve group "${group.name || group.id}"? Members stay on the canvas.`)) {
                    _dissolveGroup(editor, group);
                    window.GroupsPanel.refresh(editor);
                }
            } else {
                _setGroupVisibility(editor, group.id, group.visible === false);
                window.GroupsPanel.refresh(editor);
            }
        }
    });
}

// ----------------------------------------------------------------------------
// Public API
// ----------------------------------------------------------------------------
window.GroupsPanel = {
    PANEL_ID,

    isOpen() {
        return !!document.getElementById(PANEL_ID);
    },

    show(editor) {
        if (!editor) return;
        _ensureGroupsPanelRuntimeStyles();
        _hydrateVisibility(editor);
        const existing = document.getElementById(PANEL_ID);
        if (existing) {
            this.refresh(editor);
            return existing;
        }

        const state = _loadState();
        const savedTop = Number.isFinite(state.top) ? state.top : 80;
        const savedLeft = Number.isFinite(state.left) ? state.left : DEFAULT_LEFT;
        const savedWidth = Number.isFinite(state.width) ? state.width : 320;
        const savedHeight = Number.isFinite(state.height) ? state.height : 420;
        const width = Math.max(240, Math.min(savedWidth, Math.max(260, window.innerWidth - 24)));
        const height = Math.max(180, Math.min(savedHeight, Math.max(200, window.innerHeight - 72)));
        const top = Math.max(48, Math.min(savedTop, Math.max(48, window.innerHeight - 80)));
        const left = Math.max(MIN_LEFT, Math.min(savedLeft, Math.max(MIN_LEFT, window.innerWidth - 120)));

        const panel = document.createElement('div');
        panel.id = PANEL_ID;
        panel.className = 'groups-panel';
        panel.style.position = 'fixed';
        panel.style.top = top + 'px';
        panel.style.left = left + 'px';
        panel.style.width = width + 'px';
        panel.style.height = height + 'px';
        panel.innerHTML = `
            <div id="${HEADER_ID}" class="groups-panel-header" title="Drag to move">
                <div class="groups-panel-title">
                    <span class="groups-panel-title-icon">
                        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.5">
                            <rect x="3" y="3" width="7" height="7" rx="1.5"/>
                            <rect x="14" y="3" width="7" height="7" rx="1.5"/>
                            <rect x="3" y="14" width="7" height="7" rx="1.5"/>
                            <rect x="14" y="14" width="7" height="7" rx="1.5"/>
                        </svg>
                    </span>
                    <span>
                        <span class="groups-panel-title-main">Groups</span>
                        <span class="groups-panel-title-sub">Visibility and color sets</span>
                    </span>
                </div>
                <div class="groups-panel-header-actions">
                    <button class="groups-panel-icon-btn" data-act="collapse" title="Collapse">
                        <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="5" y1="12" x2="19" y2="12"/>
                        </svg>
                    </button>
                    <button class="groups-panel-icon-btn" data-act="close" title="Close (G)">
                        <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                </div>
            </div>
            <div id="${BODY_ID}" class="groups-panel-body"></div>
            <div id="${RESIZE_HANDLE_ID}" class="groups-panel-resize" title="Resize"></div>
        `;
        document.body.appendChild(panel);

        const header = panel.querySelector('#' + HEADER_ID);
        const body = panel.querySelector('#' + BODY_ID);
        body.innerHTML = _renderBody(editor);

        _wireDrag(panel, header, () => {
            const cur = _loadState();
            cur.top = parseInt(panel.style.top) || 80;
            cur.left = parseInt(panel.style.left) || 16;
            _saveState(cur);
        });
        _wireBody(editor, body);
        _wireDynamicUpdates(editor, panel);

        // Header actions
        header.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-act]');
            if (!btn) return;
            const act = btn.getAttribute('data-act');
            if (act === 'close') {
                this.hide(editor);
            } else if (act === 'collapse') {
                const collapsed = panel.classList.toggle('groups-panel-collapsed');
                const cur = _loadState();
                cur.collapsed = collapsed;
                _saveState(cur);
            }
        });

        // Resize
        const handle = panel.querySelector('#' + RESIZE_HANDLE_ID);
        let resizing = false;
        let rsx = 0, rsy = 0, rsw = 0, rsh = 0;
        handle.addEventListener('mousedown', (e) => {
            resizing = true;
            rsx = e.clientX;
            rsy = e.clientY;
            rsw = panel.offsetWidth;
            rsh = panel.offsetHeight;
            document.body.style.userSelect = 'none';
            e.preventDefault();
            e.stopPropagation();
        });
        const onResizeMove = (e) => {
            if (!resizing) return;
            const w = Math.max(220, rsw + (e.clientX - rsx));
            const h = Math.max(160, rsh + (e.clientY - rsy));
            panel.style.width = w + 'px';
            panel.style.height = h + 'px';
        };
        const onResizeUp = () => {
            if (!resizing) return;
            resizing = false;
            document.body.style.userSelect = '';
            const cur = _loadState();
            cur.width = panel.offsetWidth;
            cur.height = panel.offsetHeight;
            _saveState(cur);
        };
        document.addEventListener('mousemove', onResizeMove);
        document.addEventListener('mouseup', onResizeUp);

        if (state.collapsed) panel.classList.add('groups-panel-collapsed');

        // Persist visible=true so a refresh restores the panel.
        const cur = _loadState();
        cur.visible = true;
        cur.top = top;
        cur.left = left;
        cur.width = width;
        cur.height = height;
        _saveState(cur);

        _updateToolbarButton(true);
        return panel;
    },

    hide(editor) {
        const panel = document.getElementById(PANEL_ID);
        if (panel) {
            try { if (panel._groupsPanelDragCleanup) panel._groupsPanelDragCleanup(); } catch (_) {}
            try { if (panel._groupsPanelDynamicCleanup) panel._groupsPanelDynamicCleanup(); } catch (_) {}
            panel.remove();
        }
        const cur = _loadState();
        cur.visible = false;
        _saveState(cur);
        _updateToolbarButton(false);
    },

    toggle(editor) {
        if (this.isOpen()) this.hide(editor);
        else this.show(editor);
    },

    refresh(editor, options) {
        options = options || {};
        _hydrateVisibility(editor);
        const body = document.getElementById(BODY_ID);
        if (!body) return;
        body.innerHTML = _renderBody(editor);
        const panel = document.getElementById(PANEL_ID);
        if (panel && !options.skipSignatureUpdate) {
            panel._groupsPanelLastSignature = _groupPanelSignature(editor);
        }
    },

    /**
     * Group the current selection with a UI prompt for the name. Used by
     * the per-object floating toolbar's Group button. Returns the new
     * groupId or null.
     */
    async groupSelectionWithPrompt(editor, defaultName) {
        const name = await _promptName(editor, defaultName || '');
        if (name === null || name === undefined) return null;
        const id = _groupCurrentSelection(editor, String(name).trim() || null, null);
        if (id && this.isOpen()) this.refresh(editor);
        return id;
    },

    /**
     * Add a single object into an existing manual group. Used by the
     * per-object Group button popover when the user picks an existing
     * group. The object's offset is computed relative to the leader.
     */
    addObjectToGroup(editor, obj, groupId) {
        if (!editor || !obj || !groupId) return;
        const groups = _readManualGroups(editor);
        const target = groups.find(g => g.id === groupId);
        if (!target) return;
        if (typeof editor.saveState === 'function') editor.saveState();
        const leader = target.members.find(m => m.id === target.leaderId) || target.members[0] || obj;
        const lx = leader.type === 'unbound' && leader.start && leader.end
            ? (leader.start.x + leader.end.x) / 2
            : (leader.x || 0);
        const ly = leader.type === 'unbound' && leader.start && leader.end
            ? (leader.start.y + leader.end.y) / 2
            : (leader.y || 0);
        const ox = obj.type === 'unbound' && obj.start && obj.end
            ? (obj.start.x + obj.end.x) / 2
            : (obj.x || 0);
        const oy = obj.type === 'unbound' && obj.start && obj.end
            ? (obj.start.y + obj.end.y) / 2
            : (obj.y || 0);
        obj.groupId = target.id;
        obj.groupLeaderId = leader.id;
        obj.groupOffsetX = ox - lx;
        obj.groupOffsetY = oy - ly;
        if (target.name) obj.groupName = target.name;
        if (target.color) obj.groupColor = target.color;
        if (typeof editor.draw === 'function') editor.draw();
        if (this.isOpen()) this.refresh(editor);
    },

    removeObjectFromGroup(editor, obj) {
        if (!editor || !obj || !obj.groupId) return;
        if (typeof editor.saveState === 'function') editor.saveState();
        obj.groupId = null;
        obj.groupLeaderId = null;
        obj.groupOffsetX = null;
        obj.groupOffsetY = null;
        obj.groupName = null;
        obj.groupColor = null;
        if (typeof editor.draw === 'function') editor.draw();
        if (this.isOpen()) this.refresh(editor);
    },

    listManualGroups(editor) {
        return _readManualGroups(editor);
    },

    /**
     * Restore the panel after a page refresh / topology load when the
     * user had it open previously. Mirrors ``BDLegend.restoreBDPanelIfNeeded``.
     */
    restoreIfNeeded(editor) {
        try {
            _hydrateVisibility(editor);
            const state = _loadState();
            if (state && state.visible === true && !this.isOpen()) {
                this.show(editor);
            } else {
                _updateToolbarButton(this.isOpen());
            }
            if (editor && typeof editor.draw === 'function') editor.draw();
        } catch (_) {}
    },
};

// ----------------------------------------------------------------------------
// Top toolbar Groups button helper
// ----------------------------------------------------------------------------
function _updateToolbarButton(open) {
    const btn = document.getElementById('btn-groups-panel');
    if (!btn) return;
    btn.classList.toggle('active', !!open);
    btn.setAttribute('aria-pressed', open ? 'true' : 'false');
}

function _resolveEditor() {
    return window.topologyEditor || window.editor || null;
}

function _toggleFromToolbarEvent(e) {
    if (e) {
        if (e.__groupsPanelHandled) return true;
        e.__groupsPanelHandled = true;
        try { e.preventDefault(); } catch (_) {}
        try { e.stopPropagation(); } catch (_) {}
    }
    const editor = _resolveEditor();
    if (!editor) {
        console.warn('[GroupsPanel] Cannot toggle: topology editor is not ready');
        return false;
    }
    try {
        window.GroupsPanel.toggle(editor);
        return true;
    } catch (err) {
        console.error('[GroupsPanel] Failed to toggle panel:', err);
        if (editor.showToast) {
            editor.showToast('Groups panel failed to open. Check console for details.', 'error');
        }
        return false;
    }
}

// Public fallback used by inline HTML and by the delegated listener below.
// This keeps the top-bar button working even if ToolbarSetup binding is
// skipped, runs before/after the module, or is interrupted by another module.
window.toggleGroupsPanelFromToolbar = _toggleFromToolbarEvent;

function _installTopButtonFallback() {
    if (window.__groupsPanelTopButtonFallbackInstalled) return;
    window.__groupsPanelTopButtonFallbackInstalled = true;
    _ensureGroupsPanelRuntimeStyles();
    document.addEventListener('click', (e) => {
        const btn = e.target && e.target.closest && e.target.closest('#btn-groups-panel');
        if (!btn) return;
        _toggleFromToolbarEvent(e);
    }, true);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _installTopButtonFallback, { once: true });
} else {
    _installTopButtonFallback();
}

// ============================================================================
// Per-object Group popover (shared by device/shape/text/link toolbars)
// ----------------------------------------------------------------------------
// The single point where every floating object toolbar wires up its
// "Group" button. Behaviour by selection size:
//
//   * Multi-select (selectedObjects.length >= 2):
//       primary action  -> "Group these N objects"
//       secondary list  -> add to existing group <N>
//       text input      -> name (optional)
//   * Single object NOT in a group:
//       primary action  -> create new group named <input>
//       secondary list  -> add to existing group <N>
//   * Single object IN a group:
//       header          -> "Group: <name> (M members)"
//       primary action  -> "Move to other group" sub-list
//       secondary       -> "Ungroup this object"
//
// The popover anchors to whatever element triggered it (the Group
// button on the toolbar), positions itself just below, and dismisses
// itself on outside click or ``Escape``.
// ============================================================================
function _closeAnyPopover() {
    const open = document.getElementById('object-group-popover');
    if (open) {
        try { document.removeEventListener('mousedown', open._dismiss, true); } catch (_) {}
        try { document.removeEventListener('keydown', open._onKey, true); } catch (_) {}
        open.remove();
    }
}

function _renderExistingGroupsList(editor, currentGroupId) {
    const groups = _readManualGroups(editor);
    const others = groups.filter(g => g.id !== currentGroupId);
    if (others.length === 0) return '';
    return `
        <div class="object-group-popover-section">
            <div class="object-group-popover-title">Existing groups</div>
            ${others.map(g => `
                <div class="object-group-popover-row" data-act="add-existing" data-group-id="${_esc(g.id)}">
                    <span class="groups-panel-swatch" style="background:${_esc(g.color)};"></span>
                    <span class="groups-panel-name">${_esc(g.name || g.id)}</span>
                    <span class="groups-panel-count">${g.members.length}</span>
                </div>
            `).join('')}
        </div>
    `;
}

window.ObjectGroupPopover = {
    /**
     * Open the popover anchored to ``anchorEl``. ``editor`` is the
     * topology editor; behaviour adapts to the current selection.
     */
    open(editor, anchorEl) {
        _closeAnyPopover();
        if (!editor || !anchorEl) return;

        const selected = editor.selectedObjects || [];
        const single = selected.length === 1 ? selected[0] : null;
        const multi = selected.length >= 2;
        const currentGroup = single && single.groupId
            ? _readManualGroups(editor).find(g => g.id === single.groupId)
            : null;

        // Build content
        let html = '';
        if (currentGroup) {
            html += `
                <div class="object-group-popover-section">
                    <div class="object-group-popover-title">Member of</div>
                    <div class="object-group-popover-row" style="cursor:default;">
                        <span class="groups-panel-swatch" style="background:${_esc(currentGroup.color)};"></span>
                        <span class="groups-panel-name">${_esc(currentGroup.name || currentGroup.id)}</span>
                        <span class="groups-panel-count">${currentGroup.members.length}</span>
                    </div>
                </div>
            `;
            const moveList = _renderExistingGroupsList(editor, currentGroup.id);
            if (moveList) {
                // Repurpose section title via small inline tweak
                html += moveList.replace('Existing groups', 'Move to');
            }
            html += `
                <div class="object-group-popover-section">
                    <button class="object-group-popover-secondary" data-act="ungroup-self">Remove from group</button>
                </div>
            `;
        } else if (multi) {
            html += `
                <div class="object-group-popover-section">
                    <div class="object-group-popover-title">Group ${selected.length} objects</div>
                    <input type="text" class="object-group-popover-input" id="object-group-popover-input" placeholder="Group name (optional)" />
                    <button class="object-group-popover-primary" data-act="group-multi">Group these ${selected.length}</button>
                </div>
                ${_renderExistingGroupsList(editor, null)}
            `;
        } else if (single) {
            html += `
                <div class="object-group-popover-section">
                    <div class="object-group-popover-title">Create new group</div>
                    <input type="text" class="object-group-popover-input" id="object-group-popover-input" placeholder="Group name (optional)" />
                    <div style="font-size:10.5px; color:rgba(255,255,255,0.45); padding:0 4px 4px;">
                        Tip: select 2+ objects on the canvas first, then this will group all of them.
                    </div>
                </div>
                ${_renderExistingGroupsList(editor, null)}
            `;
        }

        const pop = document.createElement('div');
        pop.id = 'object-group-popover';
        pop.className = 'object-group-popover';
        pop.innerHTML = html;
        document.body.appendChild(pop);

        // Position below anchor
        const r = anchorEl.getBoundingClientRect();
        const left = Math.min(window.innerWidth - 250, r.left);
        const top = Math.min(window.innerHeight - 220, r.bottom + 6);
        pop.style.left = Math.max(8, left) + 'px';
        pop.style.top = Math.max(8, top) + 'px';

        // Focus name input if present
        const inp = pop.querySelector('#object-group-popover-input');
        if (inp) setTimeout(() => inp.focus(), 0);

        // Dismiss on outside click + Esc
        pop._dismiss = (e) => {
            if (pop.contains(e.target)) return;
            if (anchorEl.contains(e.target)) return; // re-clicking the anchor toggles
            _closeAnyPopover();
        };
        pop._onKey = (e) => {
            if (e.key === 'Escape') {
                e.preventDefault();
                _closeAnyPopover();
            }
        };
        document.addEventListener('mousedown', pop._dismiss, true);
        document.addEventListener('keydown', pop._onKey, true);

        // Wire actions
        pop.addEventListener('click', (e) => {
            const target = e.target.closest('[data-act]');
            if (!target) return;
            const act = target.getAttribute('data-act');
            const name = (inp && inp.value.trim()) || '';

            if (act === 'group-multi') {
                _groupCurrentSelection(editor, name || null, null);
                _closeAnyPopover();
                if (window.GroupsPanel.isOpen()) window.GroupsPanel.refresh(editor);
            } else if (act === 'add-existing') {
                const gid = target.getAttribute('data-group-id');
                if (multi) {
                    selected.forEach(obj => window.GroupsPanel.addObjectToGroup(editor, obj, gid));
                } else if (single) {
                    window.GroupsPanel.addObjectToGroup(editor, single, gid);
                }
                _closeAnyPopover();
            } else if (act === 'ungroup-self' && single) {
                window.GroupsPanel.removeObjectFromGroup(editor, single);
                _closeAnyPopover();
            }
        });

        // Enter inside the input commits "group these N" (or new group of 1)
        if (inp) {
            inp.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    if (multi) {
                        _groupCurrentSelection(editor, inp.value.trim() || null, null);
                        _closeAnyPopover();
                        if (window.GroupsPanel.isOpen()) window.GroupsPanel.refresh(editor);
                    } else if (single) {
                        // Single object -> name is recorded but a single-object
                        // group makes no sense; nudge the user.
                        if (editor.showToast) {
                            editor.showToast('Select 2+ objects first to create a group.', 'warning');
                        }
                    }
                }
            });
        }
    },

    /**
     * Convenience: button click handler that toggles the popover.
     * Pass it as the onClick of the "Group" toolbar button so the
     * second click dismisses without requiring a re-select.
     */
    toggleFor(editor, anchorEl) {
        const open = document.getElementById('object-group-popover');
        if (open) { _closeAnyPopover(); return; }
        this.open(editor, anchorEl);
    },
};

console.log('[topology-groups-panel.js] GroupsPanel module loaded');

})();
