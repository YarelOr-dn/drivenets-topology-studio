/**
 * topology-notifications.js - Notification and Hint UI Components
 * 
 * Extracted from topology.js for modular architecture.
 * Contains toast notifications, helper hints, and setup dialogs.
 * 
 * @version 1.0.0
 * @date 2026-02-04
 */

'use strict';

window.NotificationManager = {

    _history: [],
    _maxHistory: 80,
    _centerOpen: false,

    _addToHistory(message, type) {
        const cat = this._classifyMessage(message, type);
        this._history.unshift({ message, type, category: cat, time: Date.now() });
        if (this._history.length > this._maxHistory) this._history.length = this._maxHistory;
        const badge = document.getElementById('notif-badge');
        if (badge && !this._centerOpen) badge.style.display = 'block';
    },

    _classifyMessage(msg, type) {
        const m = msg.toLowerCase();
        if (m.includes('save') || m.includes('saved') || m.includes('quick save') || m.includes('auto-save') || m.includes('export')) return 'save';
        if (m.includes('moved to') || m.includes('move') || m.includes('→') || m.includes('domain')) return 'file';
        if (m.includes('link') || m.includes('curve') || m.includes('detach') || m.includes('sticky') || m.includes('attach')) return 'link';
        if (m.includes('device') || m.includes('ncf') || m.includes('ncm') || m.includes('ncc') || m.includes('router') || m.includes('switch')) return 'device';
        if (m.includes('text') || m.includes('label') || m.includes('font') || m.includes('style cop')) return 'text';
        if (m.includes('undo') || m.includes('redo')) return 'history';
        if (m.includes('load') || m.includes('open') || m.includes('import')) return 'load';
        if (m.includes('ssh') || m.includes('terminal')) return 'ssh';
        if (m.includes('dnaas') || m.includes('discover') || m.includes('lldp')) return 'network';
        if (m.includes('duplicate') || m.includes('copied') || m.includes('paste') || m.includes('clipboard')) return 'clipboard';
        if (type === 'error') return 'error';
        return 'general';
    },

    _formatTime(ts) {
        const d = new Date(ts);
        const hh = d.getHours().toString().padStart(2, '0');
        const mm = d.getMinutes().toString().padStart(2, '0');
        const ss = d.getSeconds().toString().padStart(2, '0');
        return `${hh}:${mm}:${ss}`;
    },

    _formatDate(ts) {
        const d = new Date(ts);
        const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        return `${months[d.getMonth()]} ${d.getDate()}`;
    },

    _timeAgo(ts) {
        const diff = (Date.now() - ts) / 1000;
        if (diff < 60) return 'just now';
        if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
        if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
        return Math.floor(diff / 86400) + 'd ago';
    },

    toggleCenter() {
        const existing = document.getElementById('notification-center-panel');
        if (existing) { this._closeCenter(); return; }
        this._openCenter();
    },

    // Remember the last active tab so the user's choice survives across
    // consecutive opens; default to the topology activity log whenever a
    // topology is currently open (which is what the Log button users
    // expect).
    _lastTab: null,
    _logState: { q: '', actor: '', event_type: '', since: '', until: '', limit: 200, offset: 0 },

    /** Activity log panel: theme rules must track body.dark-mode (not the
     *  theme frozen at first open). */
    _ensureNotifCenterCss() {
        let s = document.getElementById('notif-center-styles');
        if (s) s.remove();
        s = document.createElement('style');
        s.id = 'notif-center-styles';
        s.textContent = `
                @keyframes ncSlideIn { 0% { opacity:0; transform:translateY(12px); } 100% { opacity:1; transform:translateY(0); } }
                @keyframes ncSlideOut { 0% { opacity:1; transform:translateY(0); } 100% { opacity:0; transform:translateY(12px); } }
                #notification-center-panel::-webkit-scrollbar { width: 4px; }
                #notification-center-panel::-webkit-scrollbar-track { background: transparent; }
                body.dark-mode #notification-center-panel::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.18); border-radius: 4px; }
                body:not(.dark-mode) #notification-center-panel::-webkit-scrollbar-thumb { background: rgba(15,23,42,0.22); border-radius: 4px; }
                .nc-entry { transition: background 0.12s ease; }
                body.dark-mode #notification-center-panel .nc-entry:hover { background: rgba(255,255,255,0.05) !important; }
                body:not(.dark-mode) #notification-center-panel .nc-entry:hover { background: rgba(0,0,0,0.04) !important; }
                #notification-center-panel .nc-tab { cursor: pointer; padding: 6px 10px; border-radius: 7px;
                    font-size: 11.5px; font-weight: 500; transition: all 0.14s ease;
                    border: 1px solid transparent; user-select: none; }
                body.dark-mode #notification-center-panel .nc-tab:not(.is-active) { color: rgba(248, 250, 252, 0.78); }
                body:not(.dark-mode) #notification-center-panel .nc-tab:not(.is-active) { color: rgba(15, 23, 42, 0.78); }
                body.dark-mode #notification-center-panel .nc-tab.is-active { background: rgba(96,165,250,0.14);
                    border-color: rgba(96,165,250,0.35); color: #93c5fd; }
                body:not(.dark-mode) #notification-center-panel .nc-tab.is-active { background: rgba(96,165,250,0.12);
                    border-color: rgba(96,165,250,0.3); color: #1d4ed8; }
                body.dark-mode #notification-center-panel .nc-tab:not(.is-active):hover { background: rgba(255,255,255,0.05); }
                body:not(.dark-mode) #notification-center-panel .nc-tab:not(.is-active):hover { background: rgba(0,0,0,0.04); }
                body.dark-mode #notification-center-panel .nc-input,
                body.dark-mode #notification-center-panel .nc-select { background: rgba(255,255,255,0.05);
                    border: 1px solid rgba(255,255,255,0.08); color: rgba(255,255,255,0.88); }
                body:not(.dark-mode) #notification-center-panel .nc-input,
                body:not(.dark-mode) #notification-center-panel .nc-select { background: rgba(0,0,0,0.04);
                    border: 1px solid rgba(0,0,0,0.08); color: rgba(0,0,0,0.82); }
                #notification-center-panel .nc-input, #notification-center-panel .nc-select {
                    border-radius: 7px; padding: 6px 9px; font-size: 11px; font-family: inherit; outline: none; }
                body.dark-mode #notification-center-panel .nc-input:focus,
                body.dark-mode #notification-center-panel .nc-select:focus { border-color: rgba(96,165,250,0.5); }
                body:not(.dark-mode) #notification-center-panel .nc-input:focus,
                body:not(.dark-mode) #notification-center-panel .nc-select:focus { border-color: rgba(59,130,246,0.5); }
                body.dark-mode #notification-center-panel .nc-btn { cursor: pointer; border: 1px solid rgba(255,255,255,0.1);
                    background: rgba(255,255,255,0.04); color: rgba(255,255,255,0.82); }
                body:not(.dark-mode) #notification-center-panel .nc-btn { cursor: pointer; border: 1px solid rgba(0,0,0,0.08);
                    background: rgba(0,0,0,0.03); color: rgba(0,0,0,0.72); }
                #notification-center-panel .nc-btn { border-radius: 7px; padding: 6px 10px; font-size: 11px; font-family: inherit; transition: all 0.12s ease; }
                body.dark-mode #notification-center-panel .nc-btn:hover { background: rgba(255,255,255,0.08); }
                body:not(.dark-mode) #notification-center-panel .nc-btn:hover { background: rgba(0,0,0,0.06); }
                #notification-center-panel .nc-log-row { display:flex; gap:8px; align-items:flex-start;
                    padding: 8px 10px; border-radius: 8px; border: 1px solid transparent;
                    transition: background 0.12s ease, border-color 0.12s ease; }
                body.dark-mode #notification-center-panel .nc-log-row:hover { background: rgba(255,255,255,0.04);
                    border-color: rgba(255,255,255,0.06); }
                body:not(.dark-mode) #notification-center-panel .nc-log-row:hover { background: rgba(0,0,0,0.03);
                    border-color: rgba(0,0,0,0.06); }
                body.dark-mode #notification-center-panel .nc-log-details { color: rgba(255,255,255,0.55);
                    background: rgba(0,0,0,0.25); }
                body:not(.dark-mode) #notification-center-panel .nc-log-details { color: rgba(15,23,42,0.55);
                    background: rgba(0,0,0,0.04); }
                #notification-center-panel .nc-log-details { font-family: 'SF Mono',Menlo,Consolas,monospace; font-size: 10px;
                    margin-top: 4px; white-space: pre-wrap; word-break: break-all;
                    padding: 6px 8px; border-radius: 6px; max-height: 120px; overflow: auto; }
            `;
        document.head.appendChild(s);
    },

    /** Re-apply shell + body when light/dark toggles while the panel is open. */
    restyleOpenCenter() {
        const panel = document.getElementById('notification-center-panel');
        if (!panel || typeof panel._ncApplyShell !== 'function' || typeof panel._ncActivate !== 'function') return;
        try {
            panel._ncApplyShell();
            panel._ncActivate(this._lastTab || 'topology');
        } catch (_) {}
    },

    _openCenter() {
        this._centerOpen = true;
        const badge = document.getElementById('notif-badge');
        if (badge) badge.style.display = 'none';

        const isDm = () => document.body.classList.contains('dark-mode');
        this._ensureNotifCenterCss();
        const panel = document.createElement('div');
        panel.id = 'notification-center-panel';

        const toolbar = document.getElementById('left-toolbar');
        const panelLeft = toolbar ? toolbar.getBoundingClientRect().right + 8 : 210;

        // Decide which tab opens first. A topology is "available" if
        // TopologySync has registered an active (domain_id + topology_id).
        const sync = window.TopologySync;
        const active = (sync && sync.getActive) ? sync.getActive() : null;
        const hasActive = !!(active && active.domain_id && active.topology_id);
        const initialTab = this._lastTab || (hasActive ? 'topology' : 'session');

        const header = document.createElement('div');
        header.style.cssText = `
            display:flex; align-items:center; justify-content:space-between;
            padding: 12px 14px 10px;
            border-bottom: 1px solid ${isDm() ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'};
            gap: 8px;
        `;
        const title = document.createElement('div');
        title.style.cssText = `display:flex;align-items:center;gap:8px;flex:1;min-width:0;`;
        title.innerHTML = `
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="${isDm() ? 'rgba(255,255,255,0.6)' : 'rgba(0,0,0,0.5)'}" stroke-width="2" stroke-linecap="round">
                <path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/>
            </svg>
            <span style="font-size:13px;font-weight:600;color:${isDm() ? 'rgba(255,255,255,0.85)' : 'rgba(0,0,0,0.75)'};letter-spacing:0.3px;">Activity Log</span>
        `;
        header.appendChild(title);

        const tabWrap = document.createElement('div');
        tabWrap.style.cssText = `display:flex;gap:4px;`;
        const topoTab = document.createElement('div');
        topoTab.className = 'nc-tab' + (initialTab === 'topology' ? ' is-active' : '');
        topoTab.textContent = hasActive && active.name ? active.name : 'Topology';
        topoTab.title = hasActive
            ? 'Activity for the currently open topology'
            : 'Open a topology to see its activity log';
        tabWrap.appendChild(topoTab);
        const sessionTab = document.createElement('div');
        sessionTab.className = 'nc-tab' + (initialTab === 'session' ? ' is-active' : '');
        sessionTab.textContent = 'Session';
        sessionTab.title = 'Toasts + notifications from this browser session';
        tabWrap.appendChild(sessionTab);
        header.appendChild(tabWrap);
        panel.appendChild(header);

        const body = document.createElement('div');
        body.id = 'nc-body';
        body.style.cssText = 'flex:1; overflow:hidden; display:flex; flex-direction:column;';
        panel.appendChild(body);

        const applyNcShell = () => {
            const dk = isDm();
            panel.style.cssText = `
            position: fixed;
            bottom: 60px;
            left: ${panelLeft}px;
            width: 440px;
            max-height: 560px;
            z-index: 10001;
            border-radius: 16px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            animation: ncSlideIn 0.25s cubic-bezier(0.22,1,0.36,1) forwards;
            background: ${dk
                ? 'linear-gradient(160deg, rgba(18,22,36,0.92), rgba(12,16,28,0.96))'
                : 'linear-gradient(160deg, rgba(255,255,255,0.88), rgba(240,243,250,0.92))'};
            backdrop-filter: blur(28px) saturate(1.8);
            -webkit-backdrop-filter: blur(28px) saturate(1.8);
            border: 1px solid ${dk ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)'};
            box-shadow:
                0 16px 48px rgba(0,0,0,${dk ? '0.5' : '0.15'}),
                0 4px 12px rgba(0,0,0,${dk ? '0.3' : '0.08'}),
                inset 0 1px 0 ${dk ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.6)'};
            font-family: 'Poppins', -apple-system, sans-serif;
        `;
            header.style.borderBottom = `1px solid ${dk ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'}`;
            const svg = title.querySelector('svg');
            const sp = title.querySelector('span');
            if (svg) svg.setAttribute('stroke', dk ? 'rgba(255,255,255,0.6)' : 'rgba(0,0,0,0.5)');
            if (sp) sp.style.color = dk ? 'rgba(255,255,255,0.85)' : 'rgba(0,0,0,0.75)';
        };
        applyNcShell();

        const self = this;
        const activate = (tab) => {
            self._lastTab = tab;
            topoTab.classList.toggle('is-active', tab === 'topology');
            sessionTab.classList.toggle('is-active', tab === 'session');
            body.innerHTML = '';
            const dkLive = isDm();
            if (tab === 'topology') {
                self._renderTopologyLog(body, dkLive, hasActive, active);
            } else {
                self._renderSessionLog(body, dkLive);
            }
        };
        topoTab.onclick = () => activate('topology');
        sessionTab.onclick = () => activate('session');
        activate(initialTab);

        document.body.appendChild(panel);

        panel._ncApplyShell = applyNcShell;
        panel._ncActivate = activate;

        // Listen for live topology events and refresh the log in place
        // (only while the panel is open). Cheap: the endpoint caps at
        // 200 rows per page, so a re-fetch is ~20kb.
        const liveRefresh = (ev) => {
            const detail = (ev && ev.detail) || {};
            const cur = (sync && sync.getActive) ? sync.getActive() : null;
            if (!cur) return;
            if (detail.topology_id && detail.topology_id !== cur.topology_id) return;
            if (self._lastTab === 'topology') {
                self._refreshTopologyLog(body, isDm(), cur);
            }
        };
        window.addEventListener('topology:event:topology_event', liveRefresh);

        const closeOnClick = (e) => {
            if (!panel.contains(e.target) && !e.target.closest('#btn-notification-center')) {
                self._closeCenter();
                document.removeEventListener('mousedown', closeOnClick);
                window.removeEventListener('topology:event:topology_event', liveRefresh);
            }
        };
        setTimeout(() => document.addEventListener('mousedown', closeOnClick), 50);
    },

    // ------------------------------------------------------------------
    // Topology tab: per-file activity log backed by /api/domains/.../events
    // ------------------------------------------------------------------
    _renderTopologyLog(container, dk, hasActive, active) {
        if (!hasActive) {
            container.innerHTML = `
                <div style="text-align:center;padding:40px 18px;color:${dk ? 'rgba(255,255,255,0.35)' : 'rgba(0,0,0,0.35)'};">
                    <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" style="margin-bottom:8px;opacity:0.7;">
                        <path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/>
                    </svg>
                    <div style="font-size:12px;font-weight:500;margin-bottom:4px;">No topology open</div>
                    <div style="font-size:11px;opacity:0.7;">Open a topology to see its collaboration history.</div>
                </div>
            `;
            return;
        }

        const self = this;
        const state = this._logState;

        // Current user (for the "Mine" chip). The Activity Log lives
        // inside the authenticated app so TopologyAuth is always ready.
        const currentUser = (window.TopologyAuth && window.TopologyAuth.getUsername)
            ? (window.TopologyAuth.getUsername() || '') : '';

        // ---- Simplified filter bar ----
        // Row 1: single unified search box (plain text OR smart tokens:
        //        @actor, #type, >1d for "since last day").
        // Row 2: quick-filter chips (All / Mine / Saves / Last 24h) and
        //        an "Advanced" toggle that reveals the full pickers
        //        (actor dropdown, type dropdown, since, until) for power
        //        users who still want them. The state object keeps the
        //        full set of filters exactly like before.
        const filters = document.createElement('div');
        filters.style.cssText = `
            padding: 10px 12px 4px;
            border-bottom: 1px solid ${dk ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)'};
            display: flex; flex-direction: column; gap: 6px;
        `;
        filters.innerHTML = `
            <div style="position:relative;">
                <svg viewBox="0 0 24 24" width="13" height="13" fill="none"
                     stroke="${dk ? 'rgba(255,255,255,0.35)' : 'rgba(0,0,0,0.35)'}"
                     stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                     style="position:absolute;left:9px;top:50%;transform:translateY(-50%);pointer-events:none;">
                    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                <input class="nc-input" id="nc-q"
                       placeholder="Search · try @alice, #saved, &gt;1d"
                       value="${self._escapeHtml(state.q || '')}"
                       style="padding-left:26px;width:100%;box-sizing:border-box;">
            </div>
            <div id="nc-chip-row" style="display:flex;flex-wrap:wrap;gap:4px;align-items:center;">
                <button class="nc-chip" data-preset="all">All</button>
                <button class="nc-chip" data-preset="mine" title="Events you performed">Mine</button>
                <button class="nc-chip" data-preset="saves" title="topology.saved + topology.created">Saves</button>
                <button class="nc-chip" data-preset="24h" title="Last 24 hours">Last 24h</button>
                <span style="flex:1;"></span>
                <button class="nc-chip nc-chip-ghost" id="nc-advanced-toggle"
                        title="Show detailed filters">Advanced</button>
            </div>
            <div id="nc-advanced" style="display:none;grid-template-columns:1fr 1fr;gap:6px;">
                <select class="nc-select" id="nc-actor">
                    <option value="">All users</option>
                </select>
                <select class="nc-select" id="nc-type">
                    <option value="">All events</option>
                    <option value="topology.created">Created</option>
                    <option value="topology.saved">Saved</option>
                    <option value="topology.renamed">Renamed</option>
                    <option value="topology.deleted">Deleted</option>
                    <option value="topology.shared">Shared</option>
                    <option value="topology.unshared">Unshared</option>
                    <option value="topology.permission_changed">Permission changed</option>
                    <option value="client.micro_op">Canvas op</option>
                </select>
                <input class="nc-input" id="nc-since" type="datetime-local"
                       title="Since" placeholder="Since">
                <input class="nc-input" id="nc-until" type="datetime-local"
                       title="Until" placeholder="Until">
            </div>
        `;
        // Inject chip styling once (idempotent -- picks a unique id so
        // multiple re-mounts don't duplicate the stylesheet). Keeps the
        // liquid-glass look consistent with the rest of the panel.
        if (!document.getElementById('nc-chip-styles')) {
            const st = document.createElement('style');
            st.id = 'nc-chip-styles';
            st.textContent = `
                .nc-chip {
                    font-family: inherit; font-size: 10.5px; font-weight: 500;
                    padding: 3px 9px; border-radius: 999px; cursor: pointer;
                    border: 1px solid ${dk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'};
                    background: ${dk ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)'};
                    color: ${dk ? 'rgba(255,255,255,0.72)' : 'rgba(0,0,0,0.65)'};
                    transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
                }
                .nc-chip:hover {
                    background: ${dk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)'};
                    color: ${dk ? 'rgba(255,255,255,0.9)' : 'rgba(0,0,0,0.85)'};
                }
                .nc-chip.is-active {
                    background: ${dk ? 'rgba(96,165,250,0.22)' : 'rgba(59,130,246,0.14)'};
                    border-color: ${dk ? 'rgba(96,165,250,0.45)' : 'rgba(59,130,246,0.45)'};
                    color: ${dk ? '#93c5fd' : '#1d4ed8'};
                }
                .nc-chip-ghost {
                    background: transparent;
                    border-style: dashed;
                }
            `;
            document.head.appendChild(st);
        }
        // Preselect advanced pickers from state
        const typeSel = filters.querySelector('#nc-type');
        if (state.event_type) typeSel.value = state.event_type;
        const sinceInp = filters.querySelector('#nc-since');
        if (state.since) sinceInp.value = state.since.slice(0, 16);
        const untilInp = filters.querySelector('#nc-until');
        if (state.until) untilInp.value = state.until.slice(0, 16);
        // Restore Advanced panel visibility if any advanced filter is set
        const advPanel = filters.querySelector('#nc-advanced');
        const advToggle = filters.querySelector('#nc-advanced-toggle');
        const hasAdvState = !!(state.actor || state.event_type || state.since || state.until);
        if (hasAdvState) {
            advPanel.style.display = 'grid';
            advToggle.classList.add('is-active');
        }
        advToggle.addEventListener('click', () => {
            const shown = advPanel.style.display !== 'none';
            advPanel.style.display = shown ? 'none' : 'grid';
            advToggle.classList.toggle('is-active', !shown);
        });
        container.appendChild(filters);

        // ---- Toolbar (count + export) ----
        const actions = document.createElement('div');
        actions.style.cssText = `
            padding: 6px 12px; display:flex; align-items:center; justify-content:space-between;
            gap: 8px; font-size: 10px; color: ${dk ? 'rgba(255,255,255,0.35)' : 'rgba(0,0,0,0.35)'};
        `;
        actions.innerHTML = `
            <span id="nc-log-count">Loading…</span>
            <span style="display:flex;gap:6px;">
                <button class="nc-btn" id="nc-export-json" title="Download as JSON">JSON</button>
                <button class="nc-btn" id="nc-export-csv" title="Download as CSV">CSV</button>
                <button class="nc-btn" id="nc-refresh" title="Refresh">Refresh</button>
            </span>
        `;
        container.appendChild(actions);

        // ---- List ----
        const list = document.createElement('div');
        list.id = 'nc-log-list';
        list.style.cssText = 'flex:1; overflow-y:auto; padding: 4px 10px 12px; display:flex; flex-direction:column; gap:4px;';
        container.appendChild(list);

        // Parse smart tokens out of the unified search box. Supported:
        //   @alice            -> actor filter
        //   #topology.saved   -> full event type
        //   #saved            -> shorthand for topology.saved (and a
        //                        couple of common abbreviations)
        //   >24h / >2d / >90m -> "since N time-units ago"
        // Any remaining text becomes the free-text query.
        const _typeShortcuts = {
            saved: 'topology.saved', save: 'topology.saved',
            created: 'topology.created', create: 'topology.created',
            deleted: 'topology.deleted', delete: 'topology.deleted',
            renamed: 'topology.renamed', rename: 'topology.renamed',
            shared: 'topology.shared', share: 'topology.shared',
            unshared: 'topology.unshared',
            permission: 'topology.permission_changed', perm: 'topology.permission_changed',
            canvas: 'client.micro_op', op: 'client.micro_op', micro: 'client.micro_op',
        };
        function _parseSmart(raw) {
            const out = { q: '', actor: '', type: '', since: '' };
            const words = [];
            raw.split(/\s+/).forEach(tok => {
                if (!tok) return;
                if (tok.startsWith('@') && tok.length > 1) {
                    out.actor = tok.slice(1);
                } else if (tok.startsWith('#') && tok.length > 1) {
                    const key = tok.slice(1).toLowerCase();
                    out.type = _typeShortcuts[key] || tok.slice(1);
                } else {
                    const m = tok.match(/^>(\d+)([hdm])$/i);
                    if (m) {
                        const n = parseInt(m[1], 10);
                        const unit = m[2].toLowerCase();
                        const ms = unit === 'd' ? n * 86400000
                                 : unit === 'h' ? n * 3600000
                                 : n * 60000;
                        out.since = new Date(Date.now() - ms).toISOString().slice(0, 19);
                    } else {
                        words.push(tok);
                    }
                }
            });
            out.q = words.join(' ');
            return out;
        }

        // ---- Fetch / render ----
        const fetchAndRender = async () => {
            list.innerHTML = `<div style="padding:24px;text-align:center;font-size:11px;opacity:0.5;">Loading…</div>`;
            const rawQ = filters.querySelector('#nc-q').value.trim();
            const smart = _parseSmart(rawQ);
            // Advanced pickers act as "override" when the user explicitly
            // picked something there; the smart-token parse only fills
            // the gap so simple pasted queries still work.
            const advActor = filters.querySelector('#nc-actor').value;
            const advType = filters.querySelector('#nc-type').value;
            const advSince = filters.querySelector('#nc-since').value;
            const advUntil = filters.querySelector('#nc-until').value;
            // Preset state (chips) lives on `state._preset` so chip
            // activation is stable across re-renders.
            if (state._preset === 'mine' && currentUser) smart.actor = smart.actor || currentUser;
            if (state._preset === 'saves' && !smart.type && !advType) smart.type = 'topology.saved';
            if (state._preset === '24h' && !smart.since && !advSince) {
                smart.since = new Date(Date.now() - 86400000).toISOString().slice(0, 19);
            }

            state.q = smart.q;
            state.actor = advActor || smart.actor || '';
            state.event_type = advType || smart.type || '';
            state.since = advSince
                ? (advSince.length === 16 ? advSince + ':00' : advSince)
                : (smart.since || '');
            state.until = advUntil
                ? (advUntil.length === 16 ? advUntil + ':00' : advUntil)
                : '';

            // Reflect "active" chip visually based on current effective state.
            filters.querySelectorAll('.nc-chip[data-preset]').forEach(chip => {
                const p = chip.getAttribute('data-preset');
                let on = false;
                if (p === 'all') {
                    on = !state.actor && !state.event_type && !state.since && !state.until && !state.q;
                } else if (p === 'mine') {
                    on = !!(currentUser && state.actor === currentUser);
                } else if (p === 'saves') {
                    on = state.event_type === 'topology.saved';
                } else if (p === '24h') {
                    on = !!(state.since && !advSince);
                }
                chip.classList.toggle('is-active', on);
            });

            let payload = { items: [], total: 0 };
            try {
                payload = await window.TopologySync.listEvents({
                    q: state.q, actor: state.actor, event_type: state.event_type,
                    since: state.since, until: state.until,
                    limit: state.limit, offset: 0,
                });
            } catch (_) {}
            const items = payload.items || [];

            // Populate actor dropdown from the server's "actors" facet
            // once (and keep the user's selection if still valid). We
            // rebuild every fetch so newly-seen collaborators show up.
            const sel = filters.querySelector('#nc-actor');
            const prev = sel.value;
            const actors = (payload.actors && payload.actors.length
                ? payload.actors : Array.from(new Set(items.map(i => i.actor_user).filter(Boolean))));
            sel.innerHTML = '<option value="">All users</option>'
                + actors.map(a => {
                    const disp = (payload.actor_display_names && payload.actor_display_names[a]) || a;
                    return `<option value="${self._escapeHtml(a)}"${a === prev ? ' selected' : ''}>${self._escapeHtml(disp)}</option>`;
                }).join('');

            actions.querySelector('#nc-log-count').textContent =
                (payload.total != null ? payload.total : items.length) + ' events';

            if (items.length === 0) {
                list.innerHTML = `
                    <div style="text-align:center;padding:32px 12px;color:${dk ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.3)'};font-size:11px;">
                        No events recorded yet.
                    </div>
                `;
                return;
            }
            list.innerHTML = '';
            let lastDate = '';
            items.forEach(evt => {
                const ts = evt.created_at ? Date.parse(evt.created_at) : 0;
                const dateStr = ts ? self._formatDate(ts) : '';
                if (dateStr && dateStr !== lastDate) {
                    lastDate = dateStr;
                    const sep = document.createElement('div');
                    sep.style.cssText = `font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;color:${dk ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)'};padding:8px 4px 2px;`;
                    sep.textContent = dateStr;
                    list.appendChild(sep);
                }
                const row = document.createElement('div');
                row.className = 'nc-log-row';
                const color = self._logEventColor(evt.event_type);
                const actorName = evt.actor_display_name || evt.actor_user || 'system';
                const summary = self._escapeHtml(evt.summary || '(no summary)');
                row.innerHTML = `
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;margin-top:3px;opacity:0.9;">
                        ${self._logEventIcon(evt.event_type)}
                    </svg>
                    <div style="flex:1;min-width:0;">
                        <div style="font-size:11.5px;color:${dk ? 'rgba(255,255,255,0.9)' : 'rgba(0,0,0,0.8)'};line-height:1.4;">${summary}</div>
                        <div style="font-size:9.5px;color:${dk ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.35)'};margin-top:3px;display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
                            <span style="color:${color};font-weight:600;opacity:0.85;">${self._escapeHtml(self._logEventLabel(evt.event_type))}</span>
                            <span style="opacity:0.4;">·</span>
                            <span>${self._escapeHtml(actorName)}</span>
                            ${ts ? `<span style="opacity:0.4;">·</span><span>${self._formatTime(ts)}</span><span>${self._timeAgo(ts)}</span>` : ''}
                        </div>
                        ${evt.details && Object.keys(evt.details).length
                            ? `<div class="nc-log-details" style="display:none;"></div>`
                            : ''}
                    </div>
                `;
                const detailsEl = row.querySelector('.nc-log-details');
                if (detailsEl) {
                    try { detailsEl.textContent = JSON.stringify(evt.details, null, 2); } catch (_) {}
                    row.style.cursor = 'pointer';
                    row.addEventListener('click', () => {
                        detailsEl.style.display = detailsEl.style.display === 'none' ? 'block' : 'none';
                    });
                }
                list.appendChild(row);
            });
        };

        // ---- Events ----
        let debounceT = null;
        const debounced = () => {
            clearTimeout(debounceT);
            debounceT = setTimeout(fetchAndRender, 220);
        };
        filters.querySelector('#nc-q').addEventListener('input', debounced);
        filters.querySelector('#nc-actor').addEventListener('change', fetchAndRender);
        filters.querySelector('#nc-type').addEventListener('change', fetchAndRender);
        filters.querySelector('#nc-since').addEventListener('change', fetchAndRender);
        filters.querySelector('#nc-until').addEventListener('change', fetchAndRender);
        actions.querySelector('#nc-refresh').addEventListener('click', fetchAndRender);
        actions.querySelector('#nc-export-json').addEventListener('click', () => {
            window.TopologySync.exportEvents('json', state);
        });
        actions.querySelector('#nc-export-csv').addEventListener('click', () => {
            window.TopologySync.exportEvents('csv', state);
        });

        // Quick-filter chips. Each preset resets the relevant advanced
        // pickers so the semantics stay unambiguous ("Saves" really means
        // saves-only, even if the user had a stale type selected).
        filters.querySelectorAll('.nc-chip[data-preset]').forEach(chip => {
            chip.addEventListener('click', () => {
                const p = chip.getAttribute('data-preset');
                state._preset = p === 'all' ? '' : p;
                if (p === 'all') {
                    filters.querySelector('#nc-q').value = '';
                    filters.querySelector('#nc-actor').value = '';
                    filters.querySelector('#nc-type').value = '';
                    filters.querySelector('#nc-since').value = '';
                    filters.querySelector('#nc-until').value = '';
                } else if (p === 'saves') {
                    // Clear the dropdown so the preset's #saved takes effect
                    // without a duplicate advanced selection confusing users.
                    filters.querySelector('#nc-type').value = '';
                } else if (p === '24h') {
                    filters.querySelector('#nc-since').value = '';
                    filters.querySelector('#nc-until').value = '';
                }
                fetchAndRender();
            });
        });

        fetchAndRender();
    },

    _refreshTopologyLog(container, dk, active) {
        // Simple re-mount; filter state is preserved in this._logState.
        container.innerHTML = '';
        this._renderTopologyLog(container, dk, !!active, active);
    },

    _logEventColor(t) {
        t = t || '';
        if (t.startsWith('topology.saved') || t === 'topology.created') return '#4ade80';
        if (t === 'topology.deleted') return '#f87171';
        if (t === 'topology.renamed') return '#fbbf24';
        if (t === 'topology.shared') return '#a78bfa';
        if (t === 'topology.unshared') return '#fb923c';
        if (t === 'topology.permission_changed') return '#60a5fa';
        if (t.startsWith('client.') || t.startsWith('canvas.')) return '#34d399';
        return '#94a3b8';
    },

    _logEventLabel(t) {
        t = t || '';
        const map = {
            'topology.created': 'Created',
            'topology.saved': 'Saved',
            'topology.renamed': 'Renamed',
            'topology.deleted': 'Deleted',
            'topology.shared': 'Shared',
            'topology.unshared': 'Unshared',
            'topology.permission_changed': 'Permission',
            'client.micro_op': 'Canvas',
        };
        return map[t] || t.replace(/^topology\./, '').replace(/^client\./, 'canvas.');
    },

    _logEventIcon(t) {
        // Tiny per-type glyphs. Keep the path markup minimal so the row
        // height stays compact and the SVG reuses stroke color cleanly.
        const icons = {
            save:  '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>',
            del:   '<polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/>',
            edit:  '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>',
            share: '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>',
            lock:  '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
            canvas:'<rect x="4" y="4" width="16" height="16" rx="2"/><line x1="4" y1="10" x2="20" y2="10"/><line x1="10" y1="4" x2="10" y2="20"/>',
            info:  '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
        };
        t = t || '';
        if (t === 'topology.saved' || t === 'topology.created') return icons.save;
        if (t === 'topology.deleted') return icons.del;
        if (t === 'topology.renamed') return icons.edit;
        if (t === 'topology.shared') return icons.share;
        if (t === 'topology.unshared') return icons.lock;
        if (t === 'topology.permission_changed') return icons.lock;
        if (t.startsWith('client.') || t.startsWith('canvas.')) return icons.canvas;
        return icons.info;
    },

    // ------------------------------------------------------------------
    // Session tab: the existing toast-history list. Preserves the
    // pre-tabs behaviour so nothing the user relied on was lost.
    // ------------------------------------------------------------------
    _renderSessionLog(container, dk) {
        const subheader = document.createElement('div');
        subheader.style.cssText = `
            display:flex; align-items:center; justify-content:space-between;
            padding: 8px 14px; font-size:10px;
            color:${dk ? 'rgba(255,255,255,0.35)' : 'rgba(0,0,0,0.35)'};
            border-bottom: 1px solid ${dk ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)'};
        `;
        subheader.innerHTML = `
            <span>${this._history.length} notification${this._history.length === 1 ? '' : 's'} this session</span>
        `;
        const clearBtn = document.createElement('button');
        clearBtn.className = 'nc-btn';
        clearBtn.textContent = 'Clear';
        clearBtn.onclick = () => { this._history.length = 0; this._renderCenterEntries(list, dk); subheader.firstElementChild.textContent = '0 notifications this session'; };
        subheader.appendChild(clearBtn);
        container.appendChild(subheader);

        const list = document.createElement('div');
        list.style.cssText = 'flex:1; overflow-y:auto; padding:6px 8px 10px;';
        this._renderCenterEntries(list, dk);
        container.appendChild(list);
    },

    _categoryMeta: {
        save:      { label: 'Save',      color: '#4ade80', icon: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>' },
        file:      { label: 'File',      color: '#60a5fa', icon: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>' },
        link:      { label: 'Link',      color: '#a78bfa', icon: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>' },
        device:    { label: 'Device',    color: '#f472b6', icon: '<rect x="4" y="4" width="16" height="16" rx="2"/><line x1="9" y1="9" x2="15" y2="9"/><line x1="9" y1="13" x2="13" y2="13"/>' },
        text:      { label: 'Text',      color: '#fbbf24', icon: '<polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/>' },
        history:   { label: 'History',   color: '#94a3b8', icon: '<polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>' },
        load:      { label: 'Load',      color: '#38bdf8', icon: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>' },
        ssh:       { label: 'SSH',       color: '#a3e635', icon: '<polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>' },
        network:   { label: 'Network',   color: '#34d399', icon: '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>' },
        clipboard: { label: 'Clipboard', color: '#fb923c', icon: '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1"/>' },
        error:     { label: 'Error',     color: '#f87171', icon: '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>' },
        general:   { label: 'General',   color: '#60a5fa', icon: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>' },
    },

    _renderCenterEntries(container, dk) {
        if (this._history.length === 0) {
            container.innerHTML = `
                <div style="text-align:center;padding:32px 16px;color:${dk ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.25)'};">
                    <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" style="margin-bottom:8px;opacity:0.5;">
                        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                    </svg>
                    <div style="font-size:12px;font-weight:500;">No notifications yet</div>
                </div>
            `;
            return;
        }

        let lastDate = '';
        container.innerHTML = '';

        this._history.forEach((entry, idx) => {
            const dateStr = this._formatDate(entry.time);
            if (dateStr !== lastDate) {
                lastDate = dateStr;
                const sep = document.createElement('div');
                sep.style.cssText = `font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;color:${dk ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)'};padding:8px 8px 4px;${idx > 0 ? `border-top:1px solid ${dk ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)'};margin-top:4px;` : ''}`;
                sep.textContent = dateStr;
                container.appendChild(sep);
            }

            const cat = entry.category || 'general';
            const meta = this._categoryMeta[cat] || this._categoryMeta.general;

            const row = document.createElement('div');
            row.className = 'nc-entry';
            row.style.cssText = `
                display:flex; align-items:flex-start; gap:8px;
                padding:7px 8px; border-radius:8px; cursor:default;
            `;
            row.innerHTML = `
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="${meta.color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;margin-top:2px;opacity:0.85;">
                    ${meta.icon}
                </svg>
                <div style="flex:1;min-width:0;">
                    <div style="font-size:11.5px;color:${dk ? 'rgba(255,255,255,0.8)' : 'rgba(0,0,0,0.7)'};line-height:1.4;word-break:break-word;">${this._escapeHtml(entry.message)}</div>
                    <div style="font-size:9px;color:${dk ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.25)'};margin-top:2px;display:flex;align-items:center;gap:6px;">
                        <span style="color:${meta.color};opacity:0.7;font-weight:600;">${meta.label}</span>
                        <span style="opacity:0.4;">·</span>
                        <span>${this._formatTime(entry.time)}</span>
                        <span>${this._timeAgo(entry.time)}</span>
                    </div>
                </div>
            `;
            container.appendChild(row);
        });
    },

    _escapeHtml(s) {
        return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    },

    _closeCenter() {
        this._centerOpen = false;
        const panel = document.getElementById('notification-center-panel');
        if (!panel) return;
        panel.style.animation = 'ncSlideOut 0.2s cubic-bezier(0.22,1,0.36,1) forwards';
        setTimeout(() => panel.remove(), 200);
    },

    /**
     * Show split-pane helper hint
     */
    showSplitHelperHint(editor) {
        const existing = document.getElementById('split-helper-hint');
        if (existing) return;
        
        const hint = document.createElement('div');
        hint.id = 'split-helper-hint';
        hint.style.cssText = `
            position: fixed;
            bottom: 120px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(145deg, #1e3a5f, #0f2744);
            border: 1px solid rgba(59, 130, 246, 0.4);
            border-radius: 10px;
            padding: 14px 20px;
            color: #e2e8f0;
            font-size: 13px;
            z-index: 10000;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            max-width: 400px;
        `;
        
        hint.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 18px;">💡</span>
                <div style="flex: 1;">
                    <b>Want auto split-panes?</b> 
                    <a href="#" id="show-split-install" style="color: #60a5fa; text-decoration: underline;">Install helper</a>
                    <span style="color: #64748b; margin-left: 8px; cursor: pointer;" id="dismiss-split-hint">✕</span>
                </div>
            </div>
        `;
        
        document.body.appendChild(hint);
        
        hint.querySelector('#show-split-install').addEventListener('click', (e) => {
            e.preventDefault();
            hint.remove();
            this.showItermSetupHint(editor);
        });
        
        hint.querySelector('#dismiss-split-hint').addEventListener('click', () => {
            localStorage.setItem('iterm_split_hint_shown', 'true');
            hint.remove();
        });
        
        setTimeout(() => hint.remove(), 8000);
    },

    /**
     * Show split-pane notification after copying SSH command
     */
    showSplitPaneNotification(editor, sshCommand, password) {
        const existing = document.getElementById('topology-notification');
        if (existing) existing.remove();
        
        if (!document.getElementById('split-pane-notification-styles')) {
            const style = document.createElement('style');
            style.id = 'split-pane-notification-styles';
            style.textContent = `
                @keyframes slideUp {
                    from { transform: translateX(-50%) translateY(20px); opacity: 0; }
                    to { transform: translateX(-50%) translateY(0); opacity: 1; }
                }
                @keyframes fadeOut {
                    from { opacity: 1; }
                    to { opacity: 0; transform: translateX(-50%) translateY(10px); }
                }
            `;
            document.head.appendChild(style);
        }
        
        const notification = document.createElement('div');
        notification.id = 'topology-notification';
        notification.style.cssText = `
            position: fixed;
            bottom: 60px;
            left: 50%;
            transform: translateX(-50%);
            padding: 16px 24px;
            border-radius: 12px;
            font-size: 14px;
            color: #ffffff;
            z-index: 10000;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            animation: slideUp 0.3s ease-out;
            max-width: 500px;
            text-align: left;
            background: linear-gradient(145deg, #1e3a5f, #0f2744);
            border: 1px solid rgba(59, 130, 246, 0.3);
        `;
        
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="background: #3b82f6; border-radius: 50%; padding: 8px; flex-shrink: 0;">
                    <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" width="20" height="20">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <line x1="12" y1="3" x2="12" y2="21"/>
                    </svg>
                </div>
                <div>
                    <div style="font-weight: 600; margin-bottom: 4px;">SSH command copied! To open in split pane:</div>
                    <div style="color: #93c5fd; font-size: 13px;">
                        <span style="background: rgba(255,255,255,0.15); padding: 2px 8px; border-radius: 4px; font-family: monospace;">⌘D</span>
                        <span style="margin: 0 6px;">→</span>
                        <span style="background: rgba(255,255,255,0.15); padding: 2px 8px; border-radius: 4px; font-family: monospace;">⌘V</span>
                        <span style="margin: 0 6px;">→</span>
                        <span style="background: rgba(255,255,255,0.15); padding: 2px 8px; border-radius: 4px; font-family: monospace;">Enter</span>
                        ${password ? '<span style="margin-left: 12px; color: #fbbf24;">(Password: right-click device)</span>' : ''}
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'fadeOut 0.3s ease-out forwards';
                setTimeout(() => notification.remove(), 300);
            }
        }, 6000);
    },

    /**
     * Show iTerm setup hint dialog
     */
    showItermSetupHint(editor) {
        const overlay = document.createElement('div');
        overlay.id = 'iterm-setup-hint';
        overlay.style.cssText = `
            position: fixed;
            bottom: 100px;
            right: 20px;
            width: 420px;
            background: linear-gradient(145deg, #2d3748, #1a202c);
            border: 1px solid rgba(74, 222, 128, 0.3);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            z-index: 10001;
            color: #e2e8f0;
            font-family: 'Poppins', -apple-system, sans-serif;
        `;
        
        overlay.innerHTML = `
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <div style="background: #4ade80; border-radius: 50%; padding: 8px; flex-shrink: 0;">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#1a202c" stroke-width="2.5" width="20" height="20">
                        <rect x="2" y="3" width="20" height="14" rx="2"/>
                        <polyline points="7,8 9,10 7,12"/>
                        <line x1="11" y1="12" x2="15" y2="12"/>
                    </svg>
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; font-size: 15px; margin-bottom: 8px; color: #4ade80;">
                        🚀 Enable Auto Split-Pane SSH
                    </div>
                    <div style="font-size: 13px; color: #a0aec0; line-height: 1.5; margin-bottom: 12px;">
                        <b>Quick Setup (one-time):</b> Run this in your Mac terminal:
                    </div>
                    <div style="background: #1a202c; border: 1px solid #4a5568; border-radius: 6px; padding: 10px; margin-bottom: 12px; position: relative;">
                        <code id="install-cmd-text" style="font-size: 10px; color: #68d391; word-break: break-all; display: block; padding-right: 30px;">bash <(curl -sL raw.githubusercontent.com/YarelOr-dn/topology-creator/v1.1-dev/install-iterm-helper.sh)</code>
                        <button id="copy-install-cmd" style="position: absolute; right: 6px; top: 50%; transform: translateY(-50%); background: #4a5568; border: none; border-radius: 4px; padding: 4px 8px; color: white; font-size: 10px; cursor: pointer;">Copy</button>
                    </div>
                    <div style="font-size: 12px; color: #a0aec0; margin-bottom: 15px;">
                        Or manually: iTerm2 → Settings → Profiles → General → URL Schemes → check <b>ssh</b>
                    </div>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button id="iterm-hint-installed" style="
                            flex: 1;
                            min-width: 120px;
                            padding: 8px 16px;
                            background: linear-gradient(145deg, #4ade80, #22c55e);
                            border: none;
                            border-radius: 6px;
                            color: #1a202c;
                            font-weight: 600;
                            font-size: 13px;
                            cursor: pointer;
                        ">✓ I've installed it</button>
                        <button id="iterm-hint-ok" style="
                            padding: 8px 16px;
                            background: transparent;
                            border: 1px solid #4a5568;
                            border-radius: 6px;
                            color: #a0aec0;
                            font-size: 13px;
                            cursor: pointer;
                        ">Later</button>
                        <button id="iterm-hint-dismiss" style="
                            padding: 8px 16px;
                            background: transparent;
                            border: 1px solid #4a5568;
                            border-radius: 6px;
                            color: #a0aec0;
                            font-size: 13px;
                            cursor: pointer;
                        ">Don't show</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        const installCmd = 'bash <(curl -sL https://raw.githubusercontent.com/YarelOr-dn/topology-creator/v1.1-dev/install-iterm-helper.sh)';
        overlay.querySelector('#copy-install-cmd').addEventListener('click', (e) => {
            window.safeClipboardWrite(installCmd).then(() => {
                e.target.textContent = '[OK]';
                setTimeout(() => e.target.textContent = 'Copy', 2000);
            });
        });
        
        overlay.querySelector('#iterm-hint-installed').addEventListener('click', () => {
            localStorage.setItem('iterm_helper_installed', 'true');
            localStorage.setItem('iterm_hint_shown', 'true');
            this.showNotification(editor, '🎉 Auto split-pane enabled! Click terminal buttons to test.', 'success');
            overlay.remove();
        });
        
        overlay.querySelector('#iterm-hint-ok').addEventListener('click', () => overlay.remove());
        overlay.querySelector('#iterm-hint-dismiss').addEventListener('click', () => {
            localStorage.setItem('iterm_hint_shown', 'true');
            overlay.remove();
        });
        
        setTimeout(() => {
            if (document.getElementById('iterm-setup-hint')) overlay.remove();
        }, 20000);
    },

    /**
     * Show a temporary notification toast — liquid glass style, bottom-right
     */
    _toastTimer: null,

    showNotification(editor, message, type = 'info') {
        this._addToHistory(message, type);
        if (this._toastTimer) { clearTimeout(this._toastTimer); this._toastTimer = null; }
        const existing = document.getElementById('topology-notification');
        if (existing) existing.remove();

        if (!document.getElementById('toast-anim-styles')) {
            const s = document.createElement('style');
            s.id = 'toast-anim-styles';
            s.textContent = `
                @keyframes glassToastIn {
                    0%   { opacity:0; transform:translateX(-50%) translateY(16px) scale(0.92); }
                    60%  { opacity:1; transform:translateX(-50%) translateY(-3px) scale(1.01); }
                    100% { opacity:1; transform:translateX(-50%) translateY(0) scale(1); }
                }
                @keyframes glassToastOut {
                    0%   { opacity:1; transform:translateX(-50%) translateY(0) scale(1); }
                    100% { opacity:0; transform:translateX(-50%) translateY(10px) scale(0.95); }
                }
                @keyframes glassProgress {
                    from { transform: scaleX(1); }
                    to   { transform: scaleX(0); }
                }
            `;
            document.head.appendChild(s);
        }

        const dk = document.body.classList.contains('dark-mode');
        const notification = document.createElement('div');
        notification.id = 'topology-notification';

        const icons = {
            info:    '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>',
            success: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
            warning: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
            error:   '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>'
        };
        const colors = {
            info:    { accent: '#60a5fa', glow: 'rgba(96,165,250,0.25)',  border: 'rgba(96,165,250,0.3)' },
            success: { accent: '#4ade80', glow: 'rgba(74,222,128,0.25)',  border: 'rgba(74,222,128,0.3)' },
            warning: { accent: '#fbbf24', glow: 'rgba(251,191,36,0.25)', border: 'rgba(251,191,36,0.3)' },
            error:   { accent: '#f87171', glow: 'rgba(248,113,113,0.25)',border: 'rgba(248,113,113,0.3)' }
        };
        const c = colors[type] || colors.info;
        const duration = type === 'error' ? 6000 : type === 'warning' ? 5000 : 4000;

        notification.style.cssText = `
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            padding: 12px 22px 12px 16px;
            border-radius: 14px;
            font-size: 14px;
            color: ${dk ? 'rgba(255,255,255,0.92)' : 'rgba(15,15,30,0.88)'};
            z-index: 10000;
            animation: glassToastIn 0.35s cubic-bezier(0.22,1,0.36,1) forwards;
            background: ${dk
                ? `linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%)`
                : `linear-gradient(135deg, rgba(255,255,255,0.75) 0%, rgba(255,255,255,0.55) 100%)`};
            backdrop-filter: blur(24px) saturate(1.6);
            -webkit-backdrop-filter: blur(24px) saturate(1.6);
            border: 1px solid ${dk ? c.border : 'rgba(255,255,255,0.6)'};
            box-shadow:
                0 8px 32px rgba(0,0,0,${dk ? '0.45' : '0.1'}),
                0 2px 8px ${c.glow},
                inset 0 1px 0 ${dk ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.7)'},
                inset 0 -1px 0 ${dk ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)'};
            max-width: min(600px, 85vw);
            font-family: 'Poppins', -apple-system, sans-serif;
            display: flex;
            align-items: center;
            gap: 10px;
            overflow: hidden;
            cursor: pointer;
        `;

        const iconWrap = document.createElement('span');
        iconWrap.innerHTML = icons[type] || icons.info;
        iconWrap.style.cssText = `
            color: ${c.accent};
            flex-shrink: 0;
            display: flex;
            align-items: center;
            filter: drop-shadow(0 0 4px ${c.glow});
        `;

        const text = document.createElement('span');
        text.textContent = message;
        text.style.cssText = `line-height:1.4; font-weight:500; letter-spacing:0.1px; word-break:break-word;`;

        const progress = document.createElement('div');
        progress.style.cssText = `
            position: absolute;
            bottom: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, ${c.accent}80, ${c.accent}, ${c.accent}80, transparent);
            transform-origin: left;
            animation: glassProgress ${duration}ms linear forwards;
            border-radius: 0 0 14px 14px;
        `;

        notification.appendChild(iconWrap);
        notification.appendChild(text);
        notification.appendChild(progress);
        document.body.appendChild(notification);

        notification.onclick = () => {
            if (this._toastTimer) { clearTimeout(this._toastTimer); this._toastTimer = null; }
            notification.style.animation = 'glassToastOut 0.25s cubic-bezier(0.22,1,0.36,1) forwards';
            setTimeout(() => notification.remove(), 250);
        };

        this._toastTimer = setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'glassToastOut 0.3s cubic-bezier(0.22,1,0.36,1) forwards';
                setTimeout(() => notification.remove(), 300);
            }
            this._toastTimer = null;
        }, duration);
    },

    /**
     * Show validation error toast
     */
    showValidationErrorToast(editor, errors) {
        const existing = document.getElementById('validation-error-toast');
        if (existing) existing.remove();
        
        const toast = document.createElement('div');
        toast.id = 'validation-error-toast';
        toast.style.cssText = `
            position: fixed;
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(145deg, #ef4444, #dc2626);
            border: 1px solid rgba(239, 68, 68, 0.5);
            border-radius: 10px;
            padding: 12px 20px;
            color: white;
            font-size: 13px;
            z-index: 10000;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            max-width: 400px;
        `;
        
        const errorList = errors.map(e => `• ${e}`).join('<br>');
        toast.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 6px;">⚠️ Validation Errors</div>
            <div style="font-size: 12px; opacity: 0.9;">${errorList}</div>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.transition = 'opacity 0.3s';
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }
        }, 5000);
    }
};

(function installApiErrorInterceptor() {
    const _origFetch = window.fetch;
    const _recentErrors = {};
    const SUPPRESS_MS = 10000;
    const API_PATTERN = /^\/api\//;
    const _SILENT_404_EXACT = ['/api/dnaas/interface-details'];
    const _SILENT_404_PREFIX = ['/api/config/', '/api/operations/', '/api/health', '/api/dnaas/enable-lldp/status', '/api/dnaas/device-stack-live'];
    const _FRIENDLY_502_EXACT = ['/api/dnaas/device-gitcommit'];
    const _SILENT_BRIDGE_PREFIX = ['/api/config/', '/api/operations/', '/api/devices/'];
    const _BRIDGE_UNAVAIL_CODES = new Set([404, 501, 502, 503]);
    // Paths where failure is part of the normal UX (optional
    // enrichment, best-effort refresh, etc.). 5xx from these paths
    // should not raise a toast. The matcher checks BOTH suffix
    // (/lldp) and prefix (/api/dnaas/device/) so per-device LLDP
    // fetches from any call site are silenced uniformly.
    const _SILENT_ANY_STATUS = [
        { prefix: '/api/dnaas/device/', suffix: '/lldp' },
        { prefix: '/api/dnaas/device/', suffix: '/interfaces' },
    ];

    function _headerOf(input, init) {
        try {
            if (input instanceof Request && input.headers) {
                const h = input.headers.get('X-Best-Effort');
                if (h) return h;
            }
        } catch (_) { /* ignore */ }
        try {
            const h = init && init.headers;
            if (!h) return '';
            if (typeof h.get === 'function') return h.get('X-Best-Effort') || '';
            if (typeof h === 'object') {
                for (const k of Object.keys(h)) {
                    if (k.toLowerCase() === 'x-best-effort') return h[k] || '';
                }
            }
        } catch (_) { /* ignore */ }
        return '';
    }

    function _matchesAnySilent(cleanUrl) {
        for (const spec of _SILENT_ANY_STATUS) {
            if (spec.prefix && !cleanUrl.startsWith(spec.prefix)) continue;
            if (spec.suffix && !cleanUrl.endsWith(spec.suffix)) continue;
            return true;
        }
        return false;
    }

    window.fetch = async function(...args) {
        const input = args[0];
        const init = args[1];
        const url = typeof input === 'string' ? input : (input?.url || '');
        const bestEffort = !!_headerOf(input, init);

        let resp;
        try {
            resp = await _origFetch.apply(this, args);
        } catch (err) {
            if (API_PATTERN.test(url)) {
                const cleanUrl = url.split('?')[0];
                const isBridgePath = _SILENT_BRIDGE_PREFIX.some(p => cleanUrl.startsWith(p));
                if (!isBridgePath && !bestEffort && !_matchesAnySilent(cleanUrl)) {
                    _showApiError(url, 0, `Network error: ${err.message}`);
                }
            }
            throw err;
        }

        if (!resp.ok && API_PATTERN.test(url)) {
            const cleanUrl = url.split('?')[0];
            const isSilent = (
                bestEffort ||
                _matchesAnySilent(cleanUrl) ||
                (resp.status === 404 && (
                    _SILENT_404_EXACT.some(p => cleanUrl === p) ||
                    _SILENT_404_PREFIX.some(p => cleanUrl.startsWith(p))
                )) ||
                (resp.status === 502 && _FRIENDLY_502_EXACT.some(p => cleanUrl === p)) ||
                (_BRIDGE_UNAVAIL_CODES.has(resp.status) &&
                    _SILENT_BRIDGE_PREFIX.some(p => cleanUrl.startsWith(p)))
            );
            if (!isSilent) {
                _showApiError(url, resp.status, resp.statusText);
            }
        }
        return resp;
    };

    function _showApiError(url, status, statusText) {
        const shortPath = url.split('?')[0].replace(/^\/api\//, '');
        const key = `${status}:${shortPath}`;
        const now = Date.now();
        if (_recentErrors[key] && (now - _recentErrors[key]) < SUPPRESS_MS) return;
        _recentErrors[key] = now;

        const dk = document.body.classList.contains('dark-mode');
        const log = document.getElementById('api-error-log');
        if (log) {
            _appendLogEntry(log, shortPath, status, statusText, dk);
            return;
        }

        const container = document.createElement('div');
        container.id = 'api-error-log';
        container.style.cssText = `
            position: fixed; top: 8px; right: 8px; z-index: 9999;
            max-width: 340px; max-height: 220px; overflow-y: auto;
            display: flex; flex-direction: column; gap: 3px;
            pointer-events: auto;
        `;
        document.body.appendChild(container);
        _appendLogEntry(container, shortPath, status, statusText, dk);
    }

    function _appendLogEntry(container, path, status, statusText, dk) {
        const entry = document.createElement('div');
        const statusColor = status >= 500 ? '#f87171' : status >= 400 ? '#fbbf24' : '#60a5fa';
        entry.style.cssText = `
            padding: 5px 10px; border-radius: 6px; font-size: 11px;
            font-family: 'Space Grotesk', 'SF Mono', monospace;
            background: ${dk ? 'rgba(20,20,30,0.88)' : 'rgba(255,255,255,0.92)'};
            border: 1px solid ${dk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'};
            color: ${dk ? '#c8d0da' : '#333'};
            backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            animation: glassToastIn 0.25s ease-out forwards;
            display: flex; align-items: center; gap: 6px;
            cursor: pointer;
        `;
        const badge = `<span style="background:${statusColor};color:#fff;padding:1px 5px;border-radius:3px;font-size:10px;font-weight:700;">${status || 'ERR'}</span>`;
        const pathText = path.length > 35 ? '...' + path.slice(-32) : path;
        entry.innerHTML = `${badge}<span style="opacity:0.8;">${pathText}</span><span style="margin-left:auto;opacity:0.4;font-size:9px;">${statusText}</span>`;
        entry.title = `${status} ${statusText}\n/${path}`;
        entry.addEventListener('click', () => {
            entry.style.transition = 'opacity 0.2s';
            entry.style.opacity = '0';
            setTimeout(() => {
                entry.remove();
                if (container.children.length === 0) container.remove();
            }, 200);
        });
        container.appendChild(entry);

        while (container.children.length > 5) {
            container.removeChild(container.firstChild);
        }

        setTimeout(() => {
            if (entry.parentNode) {
                entry.style.transition = 'opacity 0.3s';
                entry.style.opacity = '0';
                setTimeout(() => {
                    entry.remove();
                    if (container.children.length === 0) container.remove();
                }, 300);
            }
        }, 8000);
    }
})();

console.log('[topology-notifications.js] NotificationManager loaded');
