/**
 * topology-sync.js - Live sync + per-topology Activity Log
 *
 * Keeps the currently-opened topology in sync with the server so a
 * write-permission collaborator's edits show up for the originator and
 * every other recipient without requiring a full-page refresh. Also
 * exposes a client-side API that drives the Activity Log panel (Log
 * button in the left toolbar's fixed footer) with full search / filter
 * / export backed by `/api/domains/{did}/topologies/{tid}/events`.
 *
 * Wiring overview
 * ---------------
 *   +-------------------+    load    +-------------------+
 *   |  FileOps.updateTo |---------->|  TopologySync     |
 *   |  pologyIndicator  |            | .setActive({...})|
 *   +-------------------+            +-------------------+
 *                                           |
 *                                           |  owner / domain_id /
 *                                           |  topology_id / updated_at
 *                                           v
 *   /api/events/ws --> topology:event:topology_event
 *   /api/topologies/events (SSE, legacy) --> topology-updated
 *   20s poll fallback --> /api/domains/{did}/topologies/{tid}?meta=1
 *                                           |
 *                                           v
 *                                  matches current topology?
 *                                     + canvas clean?  --> auto-reload
 *                                     + canvas dirty?  --> banner
 *                                                          (Reload / Dismiss)
 *
 * The module is defensive: missing editor, missing auth, or offline
 * backends never throw -- the sync path is additive and falls back to
 * the existing reload-from-dropdown flow.
 */
'use strict';

(function () {
    if (window.TopologySync) return;

    // ---- private state ----------------------------------------------------
    var _active = null;               // { owner, domain_id, topology_id, name, updated_at, is_shared, permission, domain_name, color, section_id }
    var _lastLoadedSignature = '';    // hash captured right after load / save
    var _pollTimer = null;
    var _lastBannerKey = '';          // dedupes repeat banners for the same event
    var _lastEventAt = 0;
    var _logPanel = null;             // active activity-log overlay
    var _logState = null;             // cached filter / pagination state
    var _microOps = [];               // queued client micro-ops since last save
    var POLL_MS = 20000;
    var STORAGE_KEY = 'topo_active_meta';
    var MAX_MICRO_OPS = 200;          // keep buffer bounded -- backend also trims

    // ---- tiny helpers -----------------------------------------------------
    function _authFetch(url, opts) {
        if (window.TopologyAuth && typeof window.TopologyAuth.authFetch === 'function') {
            return window.TopologyAuth.authFetch(url, opts);
        }
        return fetch(url, opts);
    }

    function _currentUser() {
        try {
            if (window.TopologyAuth) {
                if (typeof window.TopologyAuth.getCurrentUser === 'function') {
                    var current = window.TopologyAuth.getCurrentUser();
                    if (current && current.username) return current.username;
                }
                if (typeof window.TopologyAuth.getUser === 'function') {
                    var u = window.TopologyAuth.getUser();
                    if (u && u.username) return u.username;
                }
                if (typeof window.TopologyAuth.getUsername === 'function') {
                    var n = window.TopologyAuth.getUsername();
                    if (n) return n;
                }
            }
        } catch (_) { /* swallow */ }
        return '';
    }

    function _hashSignature(obj) {
        // Stable-ish signature: sort keys, drop volatile fields so
        // canvas panning / hover highlighting doesn't register as dirt.
        try {
            var s = JSON.stringify(obj, function (k, v) {
                if (k === 'selected' || k === 'hovered' || k === 'dragging') return undefined;
                if (k === '_lastClickedAt' || k === '_lastToggledAt') return undefined;
                return v;
            });
            var h = 0;
            for (var i = 0; i < s.length; i++) {
                h = ((h << 5) - h + s.charCodeAt(i)) | 0;
            }
            return String(h);
        } catch (_) {
            return '';
        }
    }

    function _currentCanvasSignature() {
        var editor = window.topologyEditor || window.editor;
        if (!editor || !window.FileOps || !window.FileOps.generateTopologyData) return '';
        try {
            return _hashSignature(window.FileOps.generateTopologyData(editor));
        } catch (_) { return ''; }
    }

    function _isCanvasClean() {
        if (!_lastLoadedSignature) return true;
        var sig = _currentCanvasSignature();
        return !!sig && sig === _lastLoadedSignature;
    }

    function _toast(msg, type) {
        var editor = window.topologyEditor || window.editor;
        if (editor && typeof editor.showToast === 'function') editor.showToast(msg, type || 'info');
    }

    function _emitActiveChanged() {
        try {
            window.dispatchEvent(new CustomEvent('topology:active-changed', {
                detail: _active ? Object.assign({}, _active) : null,
            }));
        } catch (_) {}
    }

    function _persist() {
        try {
            if (_active) localStorage.setItem(STORAGE_KEY, JSON.stringify(_active));
            else localStorage.removeItem(STORAGE_KEY);
        } catch (_) {}
    }

    function _restore() {
        try {
            var raw = localStorage.getItem(STORAGE_KEY);
            if (!raw) return;
            var d = JSON.parse(raw);
            if (d && d.topology_id) _active = d;
        } catch (_) {}
    }

    // ---- active-topology bookkeeping --------------------------------------
    //
    // setActive({
    //   owner, domain_id, topology_id, name,
    //   updated_at,          // server clock, used as base for conflict guard
    //   is_shared,           // true for topologies loaded from /Shared with me
    //   permission,          // 'read' | 'write'
    //   domain_name,         // optional, for display in banners
    //   section_id,          // legacy /api/sections id (for Quick Save compat)
    //   color                // optional, for the indicator pill
    // })
    function setActive(meta) {
        if (!meta || !meta.topology_id) {
            _active = null;
            _lastLoadedSignature = '';
            _persist();
            _restartPoll();
            _emitActiveChanged();
            return;
        }
        _active = {
            owner: meta.owner || '',
            domain_id: meta.domain_id || '',
            topology_id: meta.topology_id || '',
            name: meta.name || '',
            updated_at: meta.updated_at || '',
            is_shared: !!meta.is_shared,
            permission: meta.permission || 'write',
            domain_name: meta.domain_name || '',
            section_id: meta.section_id || '',
            color: meta.color || '',
        };
        // Capture the signature of the data that was just loaded so we
        // can tell later whether the user has started editing.
        setTimeout(function () {
            _lastLoadedSignature = _currentCanvasSignature();
        }, 60);
        _persist();
        _restartPoll();
        _emitActiveChanged();
    }

    function getActive() { return _active ? Object.assign({}, _active) : null; }

    function clearActive() { setActive(null); }

    function _activeKey() {
        if (!_active) return '';
        return [_active.owner || '', _active.domain_id || '', _active.topology_id || ''].join(':');
    }

    function markSaved(updatedAt) {
        if (!_active) return;
        if (updatedAt) _active.updated_at = updatedAt;
        _lastLoadedSignature = _currentCanvasSignature();
        // Once the server acks the save the buffered micro-ops are already
        // embedded in that save's event row (as details.micro_events), so
        // we drop them here to avoid duplicating them into the next save.
        _microOps = [];
        _persist();
    }

    // ---- micro-op buffer --------------------------------------------------
    //
    // Between two saves the user can perform dozens of visible operations
    // (add a device, drag it, connect a link, rename a label, delete a
    // shape). ``recordOp`` lets call sites append a lightweight descriptor
    // so the server can splice them into ``topology_events.details`` as
    // "micro_events". The Logs panel expands a saved event to show the
    // fine-grained trail underneath the coarse save summary.
    //
    // Entries are best-effort; we auto-cap to MAX_MICRO_OPS so a runaway
    // caller can never blow the save payload size.
    function recordOp(kind, fields) {
        if (!_active || !_active.topology_id) return;
        if (_active.permission && _active.permission !== 'write') return;
        if (!kind) return;
        try {
            var entry = {
                kind: String(kind).slice(0, 64),
                at: new Date().toISOString(),
            };
            if (fields && typeof fields === 'object') {
                for (var k in fields) {
                    if (!Object.prototype.hasOwnProperty.call(fields, k)) continue;
                    var v = fields[k];
                    if (v === null || typeof v === 'string' || typeof v === 'number'
                            || typeof v === 'boolean') {
                        entry[k] = v;
                    } else {
                        try { entry[k] = JSON.stringify(v).slice(0, 300); }
                        catch (_) { /* skip unserializable */ }
                    }
                }
            }
            _microOps.push(entry);
            if (_microOps.length > MAX_MICRO_OPS) {
                _microOps.splice(0, _microOps.length - MAX_MICRO_OPS);
            }
        } catch (_) { /* swallow -- logging must not break editing */ }
    }

    function flushMicroOps() {
        var out = _microOps.slice();
        _microOps = [];
        return out;
    }

    function peekMicroOps() { return _microOps.slice(); }

    function getBaseUpdatedAt() {
        return (_active && _active.updated_at) || '';
    }

    // ---- real-time event handlers -----------------------------------------
    function _matchesActive(env) {
        if (!_active || !_active.topology_id) return false;
        if (!env) return false;
        var sameOwner = !env.owner || !_active.owner || env.owner === _active.owner;
        var sameTopo = env.topology_id === _active.topology_id;
        var sameDomain = !env.domain_id || !_active.domain_id || env.domain_id === _active.domain_id;
        if (sameOwner && sameTopo && sameDomain) return true;
        if (env.composite_id && _active.owner && _active.domain_id && _active.topology_id) {
            return env.composite_id === (_active.owner + ':' + _active.domain_id + ':' + _active.topology_id);
        }
        return false;
    }

    function _isSelfActor(env) {
        var me = _currentUser();
        if (!me) return false;
        var actor = (env && env.actor_user) || '';
        return actor && actor.toLowerCase() === me.toLowerCase();
    }

    function _isCurrentUserOwner() {
        var me = _currentUser();
        if (!me || !_active || !_active.owner) return false;
        return String(_active.owner).toLowerCase() === String(me).toLowerCase();
    }

    function _isCurrentUserRevokedTarget(env) {
        var me = _currentUser();
        if (!me || !env) return false;
        var details = env.details || {};
        var target = details.target_user || env.target_user || '';
        if (target) return String(target).toLowerCase() === String(me).toLowerCase();
        // Older events did not always carry target_user. In that case,
        // only a shared-in viewer is eligible for force-close; the owner
        // must never be closed by a revoke event for someone else.
        return !!(_active && _active.is_shared && !_isCurrentUserOwner());
    }

    function _eventDedupKey(env) {
        return [env.event_type || '', env.created_at || '', env.actor_user || '', env.summary || ''].join('|');
    }

    async function _reloadActiveFromServer(silent) {
        if (!_active || !_active.domain_id || !_active.topology_id) return false;
        var editor = window.topologyEditor || window.editor;
        if (!editor || typeof editor.loadTopologyFromData !== 'function') return false;
        try {
            var activeKey = _activeKey();
            var url = '/api/domains/' + encodeURIComponent(_active.domain_id)
                + '/topologies/' + encodeURIComponent(_active.topology_id);
            var resp = await _authFetch(url);
            if (!resp.ok) return false;
            if (activeKey !== _activeKey()) return false;
            var payload = await resp.json();
            if (activeKey !== _activeKey()) return false;
            var data = payload.data || payload;
            editor.loadTopologyFromData(data, { domain: _active.domain_name || null });
            var updatedAt = payload.updated_at
                || (payload.meta && payload.meta.updated_at)
                || (data && data.updated_at)
                || '';
            if (updatedAt) _active.updated_at = updatedAt;
            _lastLoadedSignature = _currentCanvasSignature();
            _persist();
            if (!silent) _toast('Topology reloaded from server', 'info');
            return true;
        } catch (_) {
            return false;
        }
    }

    // Share-family events (``topology.shared``, ``topology.unshared``,
    // ``topology.permission_changed``, ``domain.shared``, ``domain.unshared``)
    // must ALWAYS drive a domain-list + share-cache refresh, even when the
    // event doesn't target the currently-open canvas -- otherwise the
    // recipient's Shared-with-me dropdown or the owner's share-dialog chip
    // state stays stale until a manual reload. Fixed 2026-04-24d together
    // with the router broadcasting ``domain.shared`` / ``domain.unshared``
    // (previously those routes only wrote the DB without a WS push).
    function _isShareFamily(env) {
        var t = (env && env.event_type) || '';
        return t === 'topology.shared' ||
               t === 'topology.unshared' ||
               t === 'topology.permission_changed' ||
               t === 'domain.shared' ||
               t === 'domain.unshared';
    }

    // Debounced refresh so back-to-back share events (bulk share of 10
    // users at once) still produce a single dropdown rebuild.
    var _sharingRefreshTimer = null;
    function _scheduleSharingRefresh() {
        if (_sharingRefreshTimer) return;
        _sharingRefreshTimer = setTimeout(function () {
            _sharingRefreshTimer = null;
            try {
                if (window.TopologyDomains && typeof window.TopologyDomains.fetchDomains === 'function') {
                    window.TopologyDomains.fetchDomains();
                }
            } catch (_) {}
            try {
                if (window.TopologyShare && typeof window.TopologyShare.refresh === 'function') {
                    window.TopologyShare.refresh();
                }
            } catch (_) {}
        }, 150);
    }

    // Short surface-level toast + share-cache refresh for events that
    // target ME (not fired by me). Returns true iff it fully handled the
    // event so the caller can return early without dropping into the
    // save-like reload path.
    function _handleShareFamilyEvent(env) {
        if (!_isShareFamily(env)) return false;
        _scheduleSharingRefresh();
        if (_isSelfActor(env)) return true;  // my own action echoed back
        var actorDisplay = env.actor_display_name || env.actor_user || 'Someone';
        var thing = (env.details && env.details.name) || env.summary || '';
        var t = env.event_type;
        if (t === 'topology.shared') {
            _toast(actorDisplay + ' shared ' + (thing ? ('"' + thing + '"') : 'a topology') + ' with you', 'info');
        } else if (t === 'topology.permission_changed') {
            _toast(actorDisplay + ' updated your access' + (thing ? ' on "' + thing + '"' : ''), 'info');
        } else if (t === 'domain.shared') {
            _toast(actorDisplay + ' shared domain ' + (thing ? ('"' + thing + '"') : '') + ' with you', 'info');
        } else if (t === 'domain.unshared') {
            _toast(actorDisplay + ' stopped sharing ' + (thing ? ('"' + thing + '"') : 'a domain') + ' with you', 'warn');
        }
        // ``topology.unshared`` is special: if the file IS active we want
        // the big banner (handled below). Otherwise a simple toast is
        // enough and we've already refreshed the list.
        return t !== 'topology.unshared';
    }

    function _onTopologyEvent(ev) {
        var env = (ev && ev.detail) || {};
        // Share-family events always refresh the domain list + share
        // cache. For non-active targets we fully handle them here.
        if (_isShareFamily(env) && !_matchesActive(env)) {
            // Special case: `domain.unshared` never satisfies
            // `_matchesActive` (it carries an empty topology_id) but
            // the receiver could still be *viewing* a topology that
            // lived in the just-revoked domain. Force-close + prompt
            // them so they aren't stranded on content they can no
            // longer save. Self-actor echoes are ignored -- if I'm
            // the one who revoked, my own UI already handled it.
            if (_activeInUnsharedDomain(env) && !_isSelfActor(env) && _isCurrentUserRevokedTarget(env)) {
                var _actor = env.actor_display_name || env.actor_user || 'the owner';
                var _thing = (env.details && env.details.name) || '';
                _forceCloseActiveTopology({
                    title: 'Domain access revoked',
                    body: _actor + ' stopped sharing '
                        + (_thing ? ('the domain "' + _thing + '"') : 'the parent domain')
                        + ' with you. The topology you had open has been closed.',
                });
                return;
            }
            _handleShareFamilyEvent(env);
            return;
        }
        if (!_matchesActive(env)) return;
        _lastEventAt = Date.now();
        var key = _eventDedupKey(env);
        if (key && key === _lastBannerKey) return;
        _lastBannerKey = key;
        if (_isSelfActor(env)) {
            // Our own save echoed back -- just refresh the base timestamp.
            if (env.created_at) {
                if (!_active) return;
                _active.updated_at = env.created_at;
                _persist();
            }
            // Even own-actor share events should refresh the cache so
            // the dialog chip list picks up the new recipient.
            if (_isShareFamily(env)) _scheduleSharingRefresh();
            return;
        }
        var actorDisplay = env.actor_display_name || env.actor_user || 'a collaborator';
        var name = _active && _active.name ? ' "' + _active.name + '"' : '';
        if (env.event_type === 'topology.deleted') {
            // Canvas content is authored by the now-deleted file, so
            // keeping it on screen is misleading (any save attempt would
            // 404). Force-close + prompt mirrors topology.unshared below.
            _forceCloseActiveTopology({
                title: 'This topology was deleted',
                body: actorDisplay + ' deleted the topology you had open. A blank canvas is ready for a new topology.',
            });
            return;
        }
        if (env.event_type === 'topology.unshared') {
            if (!_isCurrentUserRevokedTarget(env)) {
                _scheduleSharingRefresh();
                return;
            }
            // User bug report 2026-04-24: the revoked topology used to
            // stay on the canvas indefinitely. Now we clear the canvas,
            // drop the active tracker, refresh the share cache, AND
            // prompt the receiver with a "Start new topology" button.
            // See `_forceCloseActiveTopology` for the full rationale.
            _forceCloseActiveTopology({
                title: 'Your access was revoked',
                body: actorDisplay + ' stopped sharing this topology with you. A blank canvas is ready for a new topology.',
            });
            return;
        }
        if (env.event_type === 'topology.permission_changed') {
            // Don't reload the canvas for a pure permission change --
            // just toast + refresh share state. Reloading on perm change
            // was wiping unsaved edits when the owner bumped read->write.
            _scheduleSharingRefresh();
            _toast(actorDisplay + ' changed your permission' + name, 'info');
            return;
        }
        if (env.event_type === 'topology.shared') {
            // The target is already on the canvas -- so the share was
            // for THIS open file. Toast + refresh, no reload needed.
            _scheduleSharingRefresh();
            _toast(actorDisplay + ' updated sharing' + name, 'info');
            return;
        }
        if (env.event_type === 'topology.renamed') {
            _reloadActiveFromServer(true);
            _toast('Topology renamed by ' + actorDisplay, 'info');
            return;
        }
        // Save-like events. Clean canvas -> hot-swap; dirty canvas ->
        // let the user decide when to reload so their edits survive.
        if (_isCanvasClean()) {
            _reloadActiveFromServer(true).then(function (ok) {
                if (ok) _toast(actorDisplay + ' updated' + name + ' -- canvas refreshed', 'info');
            });
        } else {
            _showReloadBanner({
                tone: 'info',
                title: 'Updated by ' + actorDisplay,
                body: (env.summary ? env.summary + ' — ' : '')
                    + 'You have unsaved changes on the canvas.',
                primary: { label: 'Reload', onClick: function () { _reloadActiveFromServer(false); } },
                secondary: { label: 'Dismiss', onClick: null },
            });
        }
    }

    // Shim: the existing SSE channel emits `topology-updated` frames from
    // the legacy mirror-on-save path. We reuse it so legacy saves trigger
    // the same reload logic as the new WS `topology_event` channel.
    function _legacySseEvent(payload) {
        if (!payload) return;
        var env = {
            owner: payload.owner || '',
            domain_id: payload.domain_id || '',
            topology_id: payload.topology_id || '',
            event_type: 'topology.' + (payload.kind || 'saved'),
            actor_user: payload.owner || '',
            actor_display_name: payload.owner || '',
            summary: '',
            created_at: payload.at ? new Date(payload.at * 1000).toISOString() : '',
        };
        _onTopologyEvent({ detail: env });
    }

    // ---- forced close on access-revoke ------------------------------------
    //
    // Triggered when the receiver's access to the currently-open canvas
    // is lost while they're still viewing it:
    //   * topology.unshared  (owner revoked this specific topology)
    //   * topology.deleted   (owner deleted the whole topology)
    //   * domain.unshared    (owner revoked the parent domain; any open
    //                         topology from that domain is now dead)
    //
    // Before this helper existed the canvas was left untouched with a
    // dismissible "Your access was revoked" banner at the bottom, so the
    // receiver could keep editing a topology they no longer owned (and
    // whose saves would silently 403 at the server). The user reported
    // this bug on 2026-04-24: "shared topology is still being presented
    // on the receiver side when the originator stopped sharing ... another
    // topology should be opened instead ... with a prompt". We now:
    //   1. Clear the canvas via FileOps.performClearCanvas(editor) --
    //      same helper used by File > New, so all existing teardown
    //      (clear multi-BD, reset counters, clear topology indicator,
    //      remove topo_active localStorage) runs for free.
    //   2. Drop our own _active tracker via clearActive() so the 20s
    //      poller stops hitting the now-dead /topologies/<id>/events
    //      endpoint (which would return 404 after the revoke commits).
    //   3. Refresh the share cache + Shared-with-me dropdown so the
    //      revoked entry disappears from the Topologies dropdown.
    //   4. Show a warn-tone banner with a "Start new topology" primary
    //      button that opens the domain picker (FileOps.confirmNewTopology).
    //      warn banners don't auto-dismiss, so the receiver sees the
    //      prompt until they act or X it out.
    function _forceCloseActiveTopology(opts) {
        opts = opts || {};
        try {
            var editor = window.topologyEditor || window.editor;
            if (editor
                && window.FileOps
                && typeof window.FileOps.performClearCanvas === 'function') {
                window.FileOps.performClearCanvas(editor);
            }
        } catch (_) { /* swallow -- banner still needs to render */ }
        try { clearActive(); } catch (_) { /* swallow */ }
        try { _scheduleSharingRefresh(); } catch (_) { /* swallow */ }
        // After the canvas is wiped, surface the neutral "General"
        // (no-domain) indicator pill so the next Save click opens the
        // domain picker. Mirrors the local-delete flow in
        // topology-file-ops.js so both deletion paths converge on the
        // same UX. The banner above still tells the user *why* the
        // canvas just emptied; the pill tells them *where to go next*.
        try {
            if (window.FileOps
                && typeof window.FileOps.showGeneralTopologyIndicator === 'function') {
                window.FileOps.showGeneralTopologyIndicator('Untitled');
            }
        } catch (_) { /* swallow */ }

        _showReloadBanner({
            tone: opts.tone || 'warn',
            title: opts.title || 'Access revoked',
            body: opts.body
                || 'The topology you had open is no longer available. A blank canvas is ready for a new topology.',
            primary: {
                label: opts.primaryLabel || 'Start new topology',
                onClick: function () {
                    try {
                        var editor = window.topologyEditor || window.editor;
                        if (editor
                            && window.FileOps
                            && typeof window.FileOps.confirmNewTopology === 'function') {
                            window.FileOps.confirmNewTopology(editor);
                        }
                    } catch (_) { /* swallow */ }
                },
            },
        });
    }

    // True when the active topology is a child of the domain named in
    // `env`. Used for `domain.unshared` since those envelopes carry
    // `topology_id: ""` and so can't satisfy `_matchesActive`.
    function _activeInUnsharedDomain(env) {
        if (!env) return false;
        if (env.event_type !== 'domain.unshared') return false;
        if (!_active || !_active.domain_id) return false;
        var envDomainId = env.domain_id || '';
        if (!envDomainId) return false;
        if (_active.domain_id !== envDomainId) return false;
        // If both sides carry owner info, enforce ownership match too --
        // otherwise a namespace collision on domain IDs (two owners with
        // independently-generated `dom_…` IDs that happen to alias in
        // the receiver's cache) could cause a false close. Defensive.
        var envOwner = env.owner || '';
        if (_active.owner && envOwner && _active.owner !== envOwner) return false;
        return true;
    }

    // ---- reload banner ----------------------------------------------------
    //
    // Liquid-glass banner near the topology indicator. Semantic CSS hooks
    // live in the same `.topology-stale-save-banner` family to stay
    // consistent with the existing conflict banner.
    function _showReloadBanner(opts) {
        opts = opts || {};
        var old = document.getElementById('topology-live-sync-banner');
        if (old) old.remove();

        var dk = document.body.classList.contains('dark-mode');
        var banner = document.createElement('div');
        banner.id = 'topology-live-sync-banner';
        banner.setAttribute('role', 'alert');
        banner.setAttribute('aria-live', 'polite');

        var toneColors = {
            info:  { accent: '#60a5fa', glow: 'rgba(96,165,250,0.25)',  border: 'rgba(96,165,250,0.35)' },
            warn:  { accent: '#fbbf24', glow: 'rgba(251,191,36,0.25)', border: 'rgba(251,191,36,0.35)' },
            error: { accent: '#f87171', glow: 'rgba(248,113,113,0.25)',border: 'rgba(248,113,113,0.35)' },
        };
        var c = toneColors[opts.tone || 'info'];

        banner.style.cssText = [
            'position:fixed',
            'left:50%',
            'bottom:72px',
            'transform:translateX(-50%)',
            'z-index:10050',
            'max-width:520px',
            'padding:12px 14px 12px 14px',
            'display:flex',
            'align-items:center',
            'gap:10px',
            'border-radius:12px',
            'font-family:\'Poppins\',-apple-system,sans-serif',
            'color:' + (dk ? 'rgba(255,255,255,0.88)' : 'rgba(0,0,0,0.78)'),
            'background:' + (dk
                ? 'linear-gradient(160deg, rgba(22,28,44,0.96), rgba(15,20,34,0.98))'
                : 'linear-gradient(160deg, rgba(255,255,255,0.94), rgba(245,248,255,0.96))'),
            'border:1px solid ' + c.border,
            'box-shadow: 0 10px 32px rgba(0,0,0,' + (dk ? '0.45' : '0.16') + '), 0 0 0 1px ' + c.glow,
            'backdrop-filter: blur(18px) saturate(1.5)',
            '-webkit-backdrop-filter: blur(18px) saturate(1.5)',
            'animation: ncSlideIn 0.22s cubic-bezier(0.22,1,0.36,1)',
        ].join(';');

        var iconHtml = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="' + c.accent
            + '" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            + (opts.tone === 'warn'
                ? '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'
                : '<path d="M23 4v6h-6"/><path d="M20.49 15A9 9 0 1 1 18 5.29L23 10"/>')
            + '</svg>';

        var bodyHtml = '<div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:2px;">'
            + '<div style="font-size:12px;font-weight:600;letter-spacing:0.2px;color:' + c.accent + ';">'
            + _escape(opts.title || 'Topology updated') + '</div>'
            + '<div style="font-size:11.5px;line-height:1.45;opacity:0.85;">'
            + _escape(opts.body || '') + '</div>'
            + '</div>';

        var actionsHtml = '<div style="display:flex;align-items:center;gap:6px;flex-shrink:0;">';
        if (opts.primary) {
            actionsHtml += '<button type="button" data-role="primary" style="'
                + 'padding:6px 12px;border-radius:7px;border:1px solid ' + c.border + ';'
                + 'background:' + c.accent + ';color:#0b1220;font-size:11px;font-weight:600;cursor:pointer;'
                + '">' + _escape(opts.primary.label) + '</button>';
        }
        actionsHtml += '<button type="button" data-role="dismiss" aria-label="Dismiss" style="'
            + 'width:24px;height:24px;border-radius:6px;border:none;cursor:pointer;'
            + 'background:transparent;color:' + (dk ? 'rgba(255,255,255,0.55)' : 'rgba(0,0,0,0.45)') + ';'
            + 'font-size:18px;line-height:1;font-weight:300;">&times;</button>';
        actionsHtml += '</div>';

        banner.innerHTML = iconHtml + bodyHtml + actionsHtml;

        var teardown = function () {
            if (!banner.parentNode) return;
            banner.style.animation = 'ncSlideOut 0.18s cubic-bezier(0.22,1,0.36,1) forwards';
            setTimeout(function () { if (banner.parentNode) banner.parentNode.removeChild(banner); }, 200);
        };
        banner.querySelector('[data-role="dismiss"]').addEventListener('click', teardown);
        if (opts.primary) {
            banner.querySelector('[data-role="primary"]').addEventListener('click', function () {
                try { opts.primary.onClick && opts.primary.onClick(); } finally { teardown(); }
            });
        }

        // Reuse the ncSlideIn / ncSlideOut keyframes declared by the
        // Notification Center. They stay in the DOM the whole session
        // so we don't need to redefine them here.
        document.body.appendChild(banner);

        // Auto-dismiss info banners after 12s so they don't linger.
        if ((opts.tone || 'info') === 'info' && opts.primary) {
            setTimeout(function () { if (banner.parentNode) teardown(); }, 20000);
        }
    }

    function _escape(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    // ---- 20s poll fallback ------------------------------------------------
    //
    // Covers the window where the WebSocket is transiently disconnected
    // (mobile tether hiccups, laptop wake, ...) or the recipient's tab
    // was still booting when the owner saved. The poll simply asks the
    // server for the current updated_at and reacts to drift. Deliberately
    // gentle (no retry storm, single in-flight, throttled during active
    // editing) so it stays invisible in normal use.
    function _restartPoll() {
        if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
        if (!_active || !_active.topology_id) return;
        _pollTimer = setInterval(_pollActiveUpdatedAt, POLL_MS);
    }

    async function _pollActiveUpdatedAt() {
        if (!_active || !_active.domain_id || !_active.topology_id) return;
        try {
            var url = '/api/domains/' + encodeURIComponent(_active.domain_id)
                + '/topologies/' + encodeURIComponent(_active.topology_id)
                + '/events?limit=1';
            var resp = await _authFetch(url);
            if (!resp.ok) return;
            var payload = await resp.json();
            var items = (payload && payload.items) || [];
            if (items.length === 0) return;
            var top = items[0];
            if (!top.created_at) return;
            // Short-circuit: if the latest event is ours OR older than
            // what we already have, nothing to do.
            if (_isSelfActor(top)) return;
            var base = _active.updated_at || '';
            if (base && top.created_at <= base) return;
            // Pretend it's a fresh WS envelope and let the normal handler
            // decide between silent reload and the "Reload" banner.
            _onTopologyEvent({ detail: {
                owner: _active.owner,
                domain_id: _active.domain_id,
                topology_id: _active.topology_id,
                composite_id: top.composite_id
                    || (_active.owner + ':' + _active.domain_id + ':' + _active.topology_id),
                event_type: top.event_type || 'topology.saved',
                summary: top.summary || '',
                actor_user: top.actor_user || '',
                actor_display_name: top.actor_display_name || '',
                created_at: top.created_at,
            }});
        } catch (_) { /* swallow */ }
    }

    // ---- boot-time refetch ------------------------------------------------
    //
    // Browser restarts, F5, switching tabs can leave the in-memory canvas
    // lagging the server. On the first frame after login we ask the
    // server for the active topology and hot-swap if it moved.
    async function _bootRefetch() {
        if (!_active || !_active.domain_id || !_active.topology_id) return;
        try {
            var activeKey = _activeKey();
            var url = '/api/domains/' + encodeURIComponent(_active.domain_id)
                + '/topologies/' + encodeURIComponent(_active.topology_id);
            var resp = await _authFetch(url);
            if (!resp.ok) return;
            if (activeKey !== _activeKey()) return;
            var payload = await resp.json();
            if (activeKey !== _activeKey()) return;
            var serverUpdatedAt = payload.updated_at
                || (payload.meta && payload.meta.updated_at)
                || (payload.data && payload.data.updated_at)
                || '';
            if (!serverUpdatedAt) return;
            if (!_active.updated_at || serverUpdatedAt > _active.updated_at) {
                // Server is ahead. If the canvas hasn't diverged from
                // what we loaded, hot-swap quietly; otherwise ask.
                if (_isCanvasClean()) {
                    var editor = window.topologyEditor || window.editor;
                    if (editor && typeof editor.loadTopologyFromData === 'function') {
                        var data = payload.data || payload;
                        if (activeKey !== _activeKey()) return;
                        editor.loadTopologyFromData(data, { domain: _active.domain_name || null });
                        _active.updated_at = serverUpdatedAt;
                        _lastLoadedSignature = _currentCanvasSignature();
                        _persist();
                    }
                } else {
                    _showReloadBanner({
                        tone: 'info',
                        title: 'Topology changed while you were away',
                        body: 'Reload to see the latest version.',
                        primary: { label: 'Reload', onClick: function () { _reloadActiveFromServer(false); } },
                        secondary: { label: 'Dismiss', onClick: null },
                    });
                }
            }
        } catch (_) { /* swallow */ }
    }

    // ---- event log API (for Activity Log UI) ------------------------------
    async function listEvents(opts) {
        opts = opts || {};
        if (!_active || !_active.domain_id || !_active.topology_id) return { items: [], total: 0 };
        var params = new URLSearchParams();
        params.set('limit', String(opts.limit || 200));
        params.set('offset', String(opts.offset || 0));
        if (opts.q) params.set('q', opts.q);
        if (opts.actor) params.set('actor', opts.actor);
        if (opts.event_type) params.set('type', opts.event_type);
        if (opts.since) params.set('since', opts.since);
        if (opts.until) params.set('until', opts.until);
        var url = '/api/domains/' + encodeURIComponent(_active.domain_id)
            + '/topologies/' + encodeURIComponent(_active.topology_id)
            + '/events?' + params.toString();
        var resp = await _authFetch(url);
        if (!resp.ok) return { items: [], total: 0 };
        return await resp.json();
    }

    async function recordMicroEvent(summary, details, eventType) {
        if (!_active || !_active.domain_id || !_active.topology_id) return null;
        if (_active.permission && _active.permission !== 'write') return null;
        try {
            var url = '/api/domains/' + encodeURIComponent(_active.domain_id)
                + '/topologies/' + encodeURIComponent(_active.topology_id) + '/events';
            var resp = await _authFetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    event_type: eventType || 'client.micro_op',
                    summary: String(summary || '').slice(0, 500),
                    details: details || {},
                }),
            });
            if (!resp.ok) return null;
            return await resp.json();
        } catch (_) { return null; }
    }

    function exportEvents(fmt, filters) {
        if (!_active || !_active.domain_id || !_active.topology_id) return;
        var params = new URLSearchParams();
        params.set('format', (fmt || 'json').toLowerCase());
        if (filters) {
            if (filters.q) params.set('q', filters.q);
            if (filters.actor) params.set('actor', filters.actor);
            if (filters.event_type) params.set('type', filters.event_type);
            if (filters.since) params.set('since', filters.since);
            if (filters.until) params.set('until', filters.until);
        }
        var url = '/api/domains/' + encodeURIComponent(_active.domain_id)
            + '/topologies/' + encodeURIComponent(_active.topology_id)
            + '/events/export?' + params.toString();
        // Download via a token-auth fetch + object URL so our authFetch
        // adds the Authorization header. Plain anchor downloads drop the
        // header on cross-origin / subdomain setups.
        _authFetch(url).then(function (r) {
            if (!r || !r.ok) return null;
            return r.blob();
        }).then(function (blob) {
            if (!blob) return;
            var objUrl = URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = objUrl;
            a.download = 'topology-log_' + (_active.topology_id || 'active') + '.' + (fmt || 'json');
            document.body.appendChild(a);
            a.click();
            setTimeout(function () {
                a.remove();
                URL.revokeObjectURL(objUrl);
            }, 200);
        });
    }

    // ---- save-with-conflict wrapper ---------------------------------------
    //
    // High-level save used by the new Topologies Save path. Attaches the
    // cached `base_updated_at` so the server can detect collaborators'
    // edits and returns a { conflict: true, ... } envelope instead of
    // throwing. Callers render their own resolution UI (Reload / Save
    // anyway / Cancel) using this envelope.
    async function saveActive(name, data, opts) {
        opts = opts || {};
        if (!_active || !_active.domain_id || !_active.topology_id) {
            throw new Error('No active topology');
        }
        // Splice any buffered client micro-ops into the save payload so
        // the server can attach them to this save's event row (see
        // user_store._build_save_event_payload -> details.micro_events).
        // We clone+extend rather than mutating the caller's ``data``.
        var payloadData = data;
        var ops = _microOps.slice();
        if (ops.length && data && typeof data === 'object') {
            try {
                payloadData = Object.assign({}, data, { __micro_events: ops });
            } catch (_) { payloadData = data; }
        }
        var body = { name: name, data: payloadData };
        // Attach the cached base_updated_at via the query string (server
        // route reads it that way so we can keep the body identical to
        // the legacy shape for AI / bulk save callers).
        var qs = '';
        if (!opts.force && _active.updated_at) {
            qs = '?base_updated_at=' + encodeURIComponent(_active.updated_at);
        }
        var url = '/api/domains/' + encodeURIComponent(_active.domain_id)
            + '/topologies/' + encodeURIComponent(_active.topology_id) + qs;
        var resp = await _authFetch(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (resp.status === 409) {
            var err = {};
            try { err = await resp.json(); } catch (_) {}
            var detail = (err && err.detail) || {};
            return {
                conflict: true,
                current_updated_at: detail.current_updated_at || '',
                last_actor: detail.last_actor || '',
                last_actor_display_name: detail.last_actor_display_name || detail.last_actor || '',
            };
        }
        if (!resp.ok) {
            var e = {};
            try { e = await resp.json(); } catch (_) {}
            throw new Error((e && (e.detail || e.error)) || ('HTTP ' + resp.status));
        }
        var meta = await resp.json();
        markSaved(meta.updated_at || '');
        return meta;
    }

    // ---- wire up listeners -----------------------------------------------
    function _wireWsListener() {
        try {
            window.addEventListener('topology:event:topology_event', _onTopologyEvent);
            // Also listen for share-domain-wide events so "domain-unshared"
            // flows through the same UX.
            window.addEventListener('topology:event:share_domain', _onTopologyEvent);
        } catch (_) {}
    }

    function _wireSseListener() {
        // The SSE channel pre-dates this module and was already live via
        // the legacy mirror-on-save path. Hook into the same custom DOM
        // event that topology-file-ops.js emits so we don't open a second
        // EventSource. We add a generic listener on EventSource emits via
        // the existing handler + also peek at window 'topology-updated'
        // broadcast if the caller surfaces one.
        try {
            window.addEventListener('topology-updated', function (ev) {
                _legacySseEvent((ev && ev.detail) || {});
            });
        } catch (_) {}
    }

    function _onAuthLogin() {
        _bootRefetch();
        _restartPoll();
    }

    function _onAuthLogout() {
        clearActive();
    }

    // ---- public API -------------------------------------------------------
    window.TopologySync = {
        setActive: setActive,
        getActive: getActive,
        clearActive: clearActive,
        markSaved: markSaved,
        getBaseUpdatedAt: getBaseUpdatedAt,
        listEvents: listEvents,
        recordMicroEvent: recordMicroEvent,
        recordOp: recordOp,
        peekMicroOps: peekMicroOps,
        flushMicroOps: flushMicroOps,
        exportEvents: exportEvents,
        saveActive: saveActive,
        reloadActive: function () { return _reloadActiveFromServer(false); },
        isCanvasClean: _isCanvasClean,
        // Mainly exposed for tests / debugging.
        _onEvent: _onTopologyEvent,
        _poll: _pollActiveUpdatedAt,
    };

    // ---- boot ------------------------------------------------------------
    _restore();
    _wireWsListener();
    _wireSseListener();
    window.addEventListener('topology:auth-login', _onAuthLogin);
    window.addEventListener('topology:auth-logout', _onAuthLogout);
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            setTimeout(_bootRefetch, 300);
            _restartPoll();
        });
    } else {
        setTimeout(_bootRefetch, 300);
        _restartPoll();
    }
})();
