/**
 * topology-terminal.js - Multi-tab in-browser WebSocket terminal
 *
 * VS Code-style tab bar: multiple device sessions, switch via tabs.
 * Per-tab xterm + WebSocket. Shared font size, resizable panel, search,
 * reconnect, minimize (tab bar always visible).
 */

'use strict';

window.TerminalPanel = {
    _panel: null,
    _tabs: new Map(),
    _activeTabId: null,
    _tabIdSeq: 0,
    _fontSize: parseInt(localStorage.getItem('terminal-font-size'), 10) || 13,
    _panelHeight: parseInt(localStorage.getItem('terminal-height'), 10) || 340,
    _isMinimized: false,
    _resizeHandler: null,
    _keyHandler: null,
    _statusInterval: null,
    _contextMenu: null,
    _searchBar: null,
    _isSearchOpen: false,
    _isDragging: false,
    _textDecoder: new TextDecoder(),
    _maxReconnectAttempts: 3,
    _pongTimeoutMs: 25000,
    _connectTimeoutMs: 30000,
    _resizeDebounceTimer: null,

    _tabKey(opts) {
        const deviceId = opts.deviceId || opts.device_id || '';
        const method = opts.method || 'ssh_mgmt';
        const host = opts.host || opts.ssh_host || '';
        const vi = opts.virshInfo;
        const ncc = vi && (vi.activeNcc || (vi.nccVms && vi.nccVms[0]) || '');
        if (method === 'virsh_console' && vi) {
            return `${deviceId}|${method}|${vi.kvmHost || ''}|${ncc}`;
        }
        return `${deviceId}|${method}|${host}`;
    },

    _nextTabId() {
        this._tabIdSeq += 1;
        return `t${this._tabIdSeq}`;
    },

    open(opts) {
        console.log('[Terminal] open() called', JSON.stringify({
            deviceId: opts.deviceId || opts.device_id, host: opts.host || opts.ssh_host,
            method: opts.method, hasVirshInfo: !!opts.virshInfo,
            kvmHost: opts.virshInfo?.kvmHost, kvmUser: opts.virshInfo?.kvmUser,
            nccVms: opts.virshInfo?.nccVms, activeNcc: opts.virshInfo?.activeNcc,
        }));
        const normalized = this._normalizeOpts(opts);
        if (!normalized) {
            console.error('[Terminal] _normalizeOpts returned null -- aborting');
            return;
        }

        const key = this._tabKey(normalized);
        for (const [, sess] of this._tabs) {
            if (sess.tabKey === key) {
                console.log(`[Terminal] Reusing existing tab: ${key}`);
                this._switchTab(sess.id);
                return;
            }
        }

        if (!this._panel) {
            this._createPanelShell();
            console.log('[Terminal] Panel shell created');
        }

        const id = this._nextTabId();
        const session = {
            id,
            tabKey: key,
            opts: normalized,
            term: null,
            ws: null,
            fitAddon: null,
            searchAddon: null,
            onDataDisposable: null,
            heartbeatInterval: null,
            connectedAt: null,
            lastLatency: null,
            lastPingSent: null,
            status: 'connecting',
            container: null,
        };

        this._tabs.set(id, session);
        if (this._isMinimized) this._toggleMinimize();
        for (const [, s] of this._tabs) {
            if (s.container) s.container.style.display = 'none';
        }
        this._activeTabId = id;
        this._createSessionTerminal(session);
        this._renderTabBar();
        this._switchTab(id);

        const wsUrl = this._getWsUrl(
            normalized.deviceId,
            normalized.host,
            normalized.method,
            normalized.virshInfo
        );
        console.log(`[Terminal] WS URL: ${wsUrl}`);
        this._connectSession(session, wsUrl);
    },

    _normalizeOpts(opts) {
        const deviceId = opts.deviceId || opts.device_id || '';
        const host = opts.host || opts.ssh_host || '';
        const user = opts.user || opts.username || 'dnroot';
        const password = opts.password || 'dnroot';
        const method = opts.method || 'ssh_mgmt';
        const deviceLabel = opts.deviceLabel || opts.device_label || deviceId;
        const virshInfo = opts.virshInfo || null;

        if (method === 'virsh_console') {
            if (!virshInfo?.kvmHost || !virshInfo?.kvmUser) {
                console.warn('[Terminal] virsh_console requires virshInfo.kvmHost and virshInfo.kvmUser');
                return null;
            }
        } else if (!deviceId && !host) {
            console.warn('[Terminal] No device or host');
            return null;
        }
        return { deviceId, host, user, password, method, deviceLabel, virshInfo };
    },

    _getWsUrl(deviceId, host, method, virshInfo) {
        const origin = (typeof ScalerAPI !== 'undefined' && typeof ScalerAPI.getBridgeWebSocketOrigin === 'function')
            ? ScalerAPI.getBridgeWebSocketOrigin()
            : (() => {
                const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const port = (typeof ScalerAPI !== 'undefined' && ScalerAPI._bridgePort) || 8766;
                return `${proto}//${window.location.hostname}:${port}`;
            })();
        const params = new URLSearchParams();
        if (deviceId) params.set('device_id', deviceId);
        if (host) params.set('ssh_host', host);
        params.set('method', method || 'ssh_mgmt');
        if (method === 'virsh_console' && virshInfo) {
            params.set('kvm_host', virshInfo.kvmHost || '');
            params.set('kvm_user', virshInfo.kvmUser || '');
            params.set('ncc_vms', (virshInfo.nccVms || []).join(','));
        }
        return `${origin}/api/terminal/ws?${params}`;
    },

    _getActiveSession() {
        if (!this._activeTabId) return null;
        return this._tabs.get(this._activeTabId) || null;
    },

    // -----------------------------------------------------------------
    // Panel shell (once)
    // -----------------------------------------------------------------

    _createPanelShell() {
        const panel = document.createElement('div');
        panel.id = 'terminal-panel';
        Object.assign(panel.style, {
            position: 'fixed',
            bottom: '0',
            left: '0',
            right: '0',
            height: this._panelHeight + 'px',
            zIndex: '99998',
            background: 'var(--dn-bg-dark, #0D1B2A)',
            borderTop: '2px solid var(--dn-cyan, #00B4D8)',
            boxShadow: '0 -8px 32px rgba(0,0,0,0.4)',
            display: 'flex',
            flexDirection: 'column',
            transition: 'height 0.15s ease',
        });

        const dragHandle = document.createElement('div');
        Object.assign(dragHandle.style, {
            position: 'absolute', top: '-6px', left: '0', right: '0',
            height: '12px', cursor: 'ns-resize', zIndex: '99999',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
        });
        const dragPill = document.createElement('div');
        Object.assign(dragPill.style, {
            width: '40px', height: '4px', borderRadius: '2px',
            background: 'rgba(0, 180, 216, 0.35)',
            transition: 'background 0.15s',
        });
        dragHandle.appendChild(dragPill);
        dragHandle.addEventListener('mouseenter', () => { dragPill.style.background = 'rgba(0, 180, 216, 0.7)'; });
        dragHandle.addEventListener('mouseleave', () => { dragPill.style.background = 'rgba(0, 180, 216, 0.35)'; });
        dragHandle.addEventListener('mousedown', (e) => this._startDrag(e));
        panel.appendChild(dragHandle);

        const header = document.createElement('div');
        header.id = 'terminal-header-row';
        Object.assign(header.style, {
            display: 'flex', alignItems: 'stretch', gap: '6px',
            padding: '4px 6px 4px 4px',
            background: 'var(--dn-bg-dark-secondary, #1B263B)',
            borderBottom: '1px solid rgba(0, 180, 216, 0.2)',
            minHeight: '36px', flexShrink: '0', userSelect: 'none',
        });

        const tabStrip = document.createElement('div');
        tabStrip.id = 'terminal-tab-strip';
        Object.assign(tabStrip.style, {
            display: 'flex', alignItems: 'center', gap: '4px',
            flex: '1', minWidth: '0', overflowX: 'auto', overflowY: 'hidden',
            scrollbarWidth: 'thin',
        });

        const toolbar = document.createElement('div');
        Object.assign(toolbar.style, {
            display: 'flex', alignItems: 'center', gap: '4px', flexShrink: '0',
        });

        const connInfo = document.createElement('span');
        connInfo.id = 'terminal-conn-info';
        Object.assign(connInfo.style, {
            fontSize: '10px', color: 'rgba(224,230,237,0.5)',
            fontFamily: 'JetBrains Mono, monospace', maxWidth: '100px',
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        });

        toolbar.append(
            this._createFontControls(),
            this._mkToolBtn('Search', 'search', () => this._toggleSearch(), 'Search (Ctrl+Shift+F)'),
            this._mkToolBtn('Reconnect', 'reconnect', () => this._reconnect(), 'Reconnect active tab'),
            this._mkToolBtn('_', 'minimize', () => this._toggleMinimize(), 'Minimize / expand'),
            this._mkToolBtn('X', 'close', () => this.close(), 'Close all tabs', true)
        );

        header.append(tabStrip, connInfo, toolbar);
        panel.appendChild(header);

        const body = document.createElement('div');
        body.id = 'terminal-body';
        Object.assign(body.style, {
            flex: '1', padding: '0 6px',
            overflow: 'hidden', minHeight: '80px',
        });
        panel.appendChild(body);

        const statusBar = document.createElement('div');
        statusBar.id = 'terminal-status-bar';
        Object.assign(statusBar.style, {
            display: 'flex', alignItems: 'center', gap: '12px',
            padding: '2px 10px',
            background: 'var(--dn-bg-dark-secondary, #1B263B)',
            borderTop: '1px solid rgba(0, 180, 216, 0.15)',
            fontSize: '10px', color: 'rgba(224,230,237,0.45)',
            fontFamily: 'JetBrains Mono, monospace',
            minHeight: '22px', flexShrink: '0',
        });
        const sizeInfo = document.createElement('span');
        sizeInfo.id = 'terminal-size-info';
        sizeInfo.textContent = '...';
        const shortcutsInfo = document.createElement('span');
        shortcutsInfo.style.marginLeft = 'auto';
        shortcutsInfo.textContent = 'Ctrl+Tab: cycle tabs | Ctrl+Shift+F: Search | Right-click: Menu';
        statusBar.append(sizeInfo, shortcutsInfo);
        panel.appendChild(statusBar);

        document.body.appendChild(panel);
        this._panel = panel;

        this._keyHandler = (e) => {
            if (!this._panel) return;
            if (e.ctrlKey && e.shiftKey && e.key === 'F') {
                e.preventDefault();
                this._toggleSearch();
            }
            if (e.ctrlKey && (e.key === '=' || e.key === '+')) {
                e.preventDefault();
                this._changeFontSize(1);
            }
            if (e.ctrlKey && e.key === '-') {
                e.preventDefault();
                this._changeFontSize(-1);
            }
            if (e.ctrlKey && e.key === 'Tab') {
                e.preventDefault();
                this._cycleTab(e.shiftKey ? -1 : 1);
            }
        };
        document.addEventListener('keydown', this._keyHandler);

        this._resizeHandler = () => {
            if (this._resizeDebounceTimer) clearTimeout(this._resizeDebounceTimer);
            this._resizeDebounceTimer = setTimeout(() => {
                if (this._panel && !this._isMinimized) {
                    const s = this._getActiveSession();
                    if (s && s.fitAddon) {
                        s.fitAddon.fit();
                        this._sendResize(s);
                        this._updateSizeInfo();
                    }
                }
            }, 100);
        };
        window.addEventListener('resize', this._resizeHandler);

        body.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this._showContextMenu(e.clientX, e.clientY);
        });

        this._statusInterval = setInterval(() => this._updateConnInfo(), 1000);
    },

    _mkToolBtn(text, idSuffix, onClick, title, danger) {
        const btn = document.createElement('button');
        btn.id = `terminal-${idSuffix}`;
        Object.assign(btn.style, {
            padding: '3px 8px', fontSize: '11px', borderRadius: '4px',
            cursor: 'pointer', border: danger ? '1px solid rgba(231,76,60,0.3)' : '1px solid rgba(0,180,216,0.25)',
            background: 'transparent',
            color: danger ? 'var(--dn-red, #E74C3C)' : 'var(--dn-text-light, #E0E6ED)',
            fontFamily: 'Poppins, sans-serif', lineHeight: '1.2',
        });
        btn.textContent = text;
        btn.title = title || '';
        btn.addEventListener('mouseenter', () => {
            btn.style.background = danger ? 'rgba(231,76,60,0.12)' : 'rgba(0,180,216,0.1)';
        });
        btn.addEventListener('mouseleave', () => { btn.style.background = 'transparent'; });
        btn.onclick = onClick;
        return btn;
    },

    _createFontControls() {
        const wrap = document.createElement('span');
        Object.assign(wrap.style, { display: 'inline-flex', alignItems: 'center', gap: '2px' });
        const btnCss = {
            width: '20px', height: '20px', borderRadius: '3px',
            border: '1px solid rgba(0,180,216,0.2)', background: 'transparent',
            color: 'var(--dn-text-light, #E0E6ED)', cursor: 'pointer',
            fontSize: '13px', lineHeight: '1', padding: '0',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
        };
        const minusBtn = document.createElement('button');
        const plusBtn = document.createElement('button');
        Object.assign(minusBtn.style, btnCss);
        Object.assign(plusBtn.style, btnCss);
        minusBtn.textContent = '-';
        plusBtn.textContent = '+';
        minusBtn.title = 'Decrease font (Ctrl+-)';
        plusBtn.title = 'Increase font (Ctrl+=)';
        minusBtn.onclick = () => this._changeFontSize(-1);
        plusBtn.onclick = () => this._changeFontSize(1);
        wrap.append(minusBtn, plusBtn);
        return wrap;
    },

    _renderTabBar() {
        const strip = this._panel?.querySelector('#terminal-tab-strip');
        if (!strip) return;
        strip.innerHTML = '';

        for (const [tid, sess] of this._tabs) {
            const tab = document.createElement('div');
            tab.dataset.tabId = tid;
            const active = tid === this._activeTabId;
            Object.assign(tab.style, {
                display: 'flex', alignItems: 'center', gap: '4px',
                padding: '3px 6px 3px 8px', borderRadius: '4px',
                cursor: 'pointer', flexShrink: '0',
                background: active ? 'rgba(0,180,216,0.15)' : 'rgba(255,255,255,0.06)',
                borderBottom: active ? '2px solid var(--dn-cyan, #00B4D8)' : '2px solid transparent',
                border: active ? '1px solid rgba(0,180,216,0.35)' : '1px solid rgba(255,255,255,0.08)',
            });

            const dot = document.createElement('span');
            dot.className = 'terminal-tab-dot';
            dot.dataset.sessionId = tid;
            this._applyDotStyle(dot, sess.status);

            const label = document.createElement('span');
            Object.assign(label.style, {
                fontSize: '11px', fontWeight: '600', maxWidth: '140px',
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                color: 'var(--dn-text-light, #E0E6ED)', fontFamily: 'Poppins, sans-serif',
            });
            label.textContent = sess.opts.deviceLabel || sess.opts.deviceId || sess.opts.host;

            const badge = document.createElement('span');
            const m = sess.opts.method || 'ssh_mgmt';
            const badgeColor = m === 'virsh_console' ? 'var(--dn-orange, #FF5E1F)' :
                m === 'console' ? '#e67e22' : 'var(--dn-cyan, #00B4D8)';
            Object.assign(badge.style, {
                fontSize: '8px', padding: '1px 4px', borderRadius: '2px',
                background: badgeColor, color: '#fff', fontWeight: '600',
                fontFamily: 'JetBrains Mono, monospace', textTransform: 'uppercase',
            });
            badge.textContent = m.replace(/_/g, ' ').slice(0, 10);

            const closeX = document.createElement('button');
            closeX.type = 'button';
            Object.assign(closeX.style, {
                border: 'none', background: 'transparent', color: 'rgba(224,230,237,0.55)',
                cursor: 'pointer', fontSize: '14px', lineHeight: '1', padding: '0 2px',
            });
            closeX.textContent = '\u00d7';
            closeX.title = 'Close tab';
            closeX.addEventListener('click', (ev) => {
                ev.stopPropagation();
                this._closeTab(tid);
            });

            tab.append(dot, label, badge, closeX);
            tab.addEventListener('click', () => this._switchTab(tid));
            strip.appendChild(tab);
        }
    },

    _applyDotStyle(dot, status) {
        const cfg = {
            connecting: { color: '#f39c12' },
            connected: { color: '#27ae60' },
            disconnected: { color: '#e74c3c' },
        };
        const c = cfg[status] || { color: '#95a5a6' };
        Object.assign(dot.style, {
            width: '7px', height: '7px', borderRadius: '50%',
            background: c.color, flexShrink: '0',
            boxShadow: `0 0 4px ${c.color}`,
        });
    },

    _refreshTabDot(sessionId) {
        const sess = this._tabs.get(sessionId);
        if (!sess) return;
        const strip = this._panel?.querySelector('#terminal-tab-strip');
        const tab = strip?.querySelector(`[data-tab-id="${sessionId}"]`);
        const dot = tab?.querySelector('.terminal-tab-dot');
        if (dot) this._applyDotStyle(dot, sess.status);
    },

    _switchTab(id) {
        if (!this._tabs.has(id)) return;
        this._activeTabId = id;

        if (this._isSearchOpen) this._closeSearch();

        for (const [tid, sess] of this._tabs) {
            if (sess.container) {
                sess.container.style.display = tid === id ? 'block' : 'none';
            }
        }

        this._renderTabBar();
        const sess = this._tabs.get(id);
        if (sess && sess.term) {
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    if (sess.fitAddon && !this._isMinimized) {
                        try { sess.fitAddon.fit(); } catch (_) {}
                        this._sendResize(sess);
                        if ((sess.term.cols === 0 || sess.term.rows === 0)) {
                            setTimeout(() => {
                                try { sess.fitAddon.fit(); } catch (_) {}
                                this._sendResize(sess);
                                sess.term.focus();
                                this._updateSizeInfo();
                            }, 300);
                        }
                    }
                    sess.term.focus();
                    this._updateSizeInfo();
                    this._updateConnInfo();
                });
            });
        }
    },

    _cycleTab(direction) {
        const keys = [...this._tabs.keys()];
        if (keys.length < 2) return;
        const idx = keys.indexOf(this._activeTabId);
        const next = (idx + direction + keys.length) % keys.length;
        this._switchTab(keys[next]);
    },

    // -----------------------------------------------------------------
    // Per-session terminal + WS
    // -----------------------------------------------------------------

    _createSessionTerminal(session) {
        const body = this._panel?.querySelector('#terminal-body');
        if (!body || typeof window.Terminal === 'undefined') {
            console.error(`[Terminal] Cannot create terminal: body=${!!body}, Terminal=${typeof window.Terminal}`);
            if (body) body.innerHTML = '<div style="padding:20px;color:var(--dn-red);">xterm.js not loaded</div>';
            return;
        }

        const container = document.createElement('div');
        container.className = 'terminal-tab-container';
        container.dataset.sessionId = session.id;
        Object.assign(container.style, {
            width: '100%', height: '100%',
            boxSizing: 'border-box', padding: '4px 0 0 0',
            overflow: 'hidden',
        });
        body.appendChild(container);
        const bw = body.clientWidth, bh = body.clientHeight;
        console.log(`[Terminal] Container created, body size: ${bw}x${bh}`);

        const term = new window.Terminal({
            cursorBlink: true,
            cursorStyle: 'bar',
            cursorWidth: 2,
            scrollback: 10000,
            theme: {
                background: '#0a1628',
                foreground: '#dce4ee',
                cursor: '#00d4ff',
                cursorAccent: '#0a1628',
                selectionBackground: 'rgba(0, 180, 216, 0.28)',
                selectionForeground: '#ffffff',
                black: '#1a1a2e',
                red: '#ff6b6b',
                green: '#2ecc71',
                yellow: '#f1c40f',
                blue: '#3498db',
                magenta: '#a29bfe',
                cyan: '#00d4ff',
                white: '#ecf0f1',
                brightBlack: '#636e72',
                brightRed: '#ff8787',
                brightGreen: '#55efc4',
                brightYellow: '#ffeaa7',
                brightBlue: '#74b9ff',
                brightMagenta: '#d1a3ff',
                brightCyan: '#81ecec',
                brightWhite: '#ffffff',
            },
            fontSize: this._fontSize,
            fontFamily: '"JetBrains Mono", "Fira Code", "SF Mono", Menlo, Monaco, "Courier New", monospace',
            fontWeight: '400',
            fontWeightBold: '600',
            letterSpacing: 0,
            lineHeight: 1.15,
            allowTransparency: true,
            drawBoldTextInBrightColors: true,
        });

        const FitAddonClass = window.FitAddon?.FitAddon || window.FitAddon;
        const fitAddon = FitAddonClass ? new FitAddonClass() : null;
        if (fitAddon) term.loadAddon(fitAddon);

        const WebLinksClass = window.WebLinksAddon?.WebLinksAddon || window.WebLinksAddon;
        if (WebLinksClass) {
            try { term.loadAddon(new WebLinksClass()); } catch (_) {}
        }

        let searchAddon = null;
        const SearchAddonClass = window.SearchAddon?.SearchAddon || window.SearchAddon;
        if (SearchAddonClass) {
            try {
                searchAddon = new SearchAddonClass();
                term.loadAddon(searchAddon);
            } catch (_) {}
        }

        term.open(container);
        session.container = container;
        session.term = term;
        session.fitAddon = fitAddon;
        session.searchAddon = searchAddon;
        console.log(`[Terminal] xterm opened, container visible: ${container.style.display !== 'none'}, size: ${container.clientWidth}x${container.clientHeight}`);

        if (fitAddon && !this._isMinimized) {
            const doFit = (attempt) => {
                if (session.id !== this._activeTabId) return;
                try { fitAddon.fit(); } catch (_) {}
                this._sendResize(session);
                this._updateSizeInfo();
                console.log(`[Terminal] Fit attempt ${attempt}: cols=${term.cols}, rows=${term.rows}, container=${container.clientWidth}x${container.clientHeight}`);
                if ((term.cols === 0 || term.rows === 0) && attempt < 8) {
                    setTimeout(() => doFit(attempt + 1), 150 * attempt);
                }
            };
            setTimeout(() => doFit(1), 50);
        }
    },

    _connectSession(session, wsUrl) {
        if (!this._tabs.has(session.id)) return;
        const { opts } = session;
        const { user, password, method, virshInfo } = opts;
        session._reconnectAttempts = session._reconnectAttempts || 0;
        session._lastPongAt = Date.now();

        try {
            console.log(`[Terminal] Connecting WS: ${wsUrl}`);
            const ws = new WebSocket(wsUrl);
            session.ws = ws;
            ws.binaryType = 'arraybuffer';
            session.status = 'connecting';
            this._refreshTabDot(session.id);

            const connectTimer = setTimeout(() => {
                if (ws.readyState !== WebSocket.OPEN) {
                    console.error(`[Terminal] WS connection timed out (30s), readyState=${ws.readyState}`);
                    if (session.term) session.term.writeln('\r\n\x1b[31m[ERROR]\x1b[0m Connection timed out (30s)');
                    try { ws.close(); } catch (_) {}
                }
            }, this._connectTimeoutMs);

            ws.onopen = () => {
                clearTimeout(connectTimer);
                console.log(`[Terminal] WS opened, sending ${method === 'virsh_console' ? 'virsh_auth' : 'auth'}`);
                if (!this._tabs.has(session.id)) { ws.close(); return; }
                if (method === 'virsh_console' && virshInfo) {
                    const authMsg = {
                        type: 'virsh_auth',
                        kvm_pass: virshInfo.kvmPass || password || '',
                        kvm_host: virshInfo.kvmHost,
                        kvm_user: virshInfo.kvmUser,
                        ncc_vms: virshInfo.nccVms || [],
                        active_ncc: virshInfo.activeNcc || (virshInfo.nccVms && virshInfo.nccVms[0]) || ''
                    };
                    console.log(`[Terminal] virsh_auth: kvm=${authMsg.kvm_host}, user=${authMsg.kvm_user}, nccVms=${(authMsg.ncc_vms||[]).join(',')}, activeNcc=${authMsg.active_ncc}`);
                    ws.send(JSON.stringify(authMsg));
                } else {
                    ws.send(JSON.stringify({ type: 'auth', user: user || 'dnroot', password: password || 'dnroot' }));
                }
                session.connectedAt = Date.now();
                session._reconnectAttempts = 0;
                session._lastPongAt = Date.now();
                this._startHeartbeat(session);
                session.status = 'connected';
                this._refreshTabDot(session.id);
                this._sendResize(session);
                if (session.id === this._activeTabId) this._updateConnInfo();
            };

            ws.onmessage = (e) => {
                if (!this._tabs.has(session.id)) return;
                if (typeof e.data === 'string') {
                    try {
                        const msg = JSON.parse(e.data);
                        if (msg.type === 'data' && msg.text && session.term) {
                            session.term.write(msg.text);
                        } else if (msg.type === 'error') {
                            console.error(`[Terminal] Server error: ${msg.message || msg.error}`);
                            if (session.term) session.term.writeln('\r\n\x1b[31m[ERROR]\x1b[0m ' + (msg.message || msg.error || ''));
                            session.status = 'disconnected';
                            this._refreshTabDot(session.id);
                        } else if (msg.type === 'closed' || msg.type === 'eof') {
                            console.log(`[Terminal] Server ${msg.type}: ${msg.message || ''}`);
                            if (session.term) session.term.writeln('\r\n\x1b[33m[INFO]\x1b[0m Remote session ended');
                            session.status = 'disconnected';
                            session._noAutoReconnect = true;
                            this._refreshTabDot(session.id);
                        } else if (msg.type === 'pong') {
                            session._lastPongAt = Date.now();
                            session.lastLatency = Date.now() - (session.lastPingSent || Date.now());
                            if (session.id === this._activeTabId) this._updateConnInfo();
                        }
                    } catch (_) {
                        if (session.term) session.term.write(e.data);
                    }
                } else if (e.data instanceof ArrayBuffer && session.term) {
                    session.term.write(this._textDecoder.decode(e.data));
                }
            };

            ws.onclose = (ev) => {
                clearTimeout(connectTimer);
                console.log(`[Terminal] WS closed: code=${ev.code}, reason=${ev.reason}, clean=${ev.wasClean}`);
                if (!this._tabs.has(session.id)) return;
                this._stopHeartbeat(session);
                session.status = 'disconnected';
                session.connectedAt = null;
                this._refreshTabDot(session.id);
                const reason = ev.code === 1000 ? 'Normal close'
                    : ev.code === 1006 ? 'Connection lost'
                    : ev.code === 1011 ? 'Server error'
                    : `Code ${ev.code}`;
                if (session.term) session.term.writeln(`\r\n\x1b[33m[WARN]\x1b[0m Connection closed (${reason})`);
                if (session.id === this._activeTabId) this._updateConnInfo();

                if (ev.code !== 1000 && !session._noAutoReconnect && session._reconnectAttempts < this._maxReconnectAttempts) {
                    const delay = Math.min(1000 * Math.pow(2, session._reconnectAttempts), 8000);
                    session._reconnectAttempts++;
                    if (session.term) session.term.writeln(`\x1b[36m[INFO]\x1b[0m Auto-reconnecting in ${delay / 1000}s (attempt ${session._reconnectAttempts}/${this._maxReconnectAttempts})...`);
                    session._reconnectTimer = setTimeout(() => {
                        if (!this._tabs.has(session.id)) return;
                        session.status = 'connecting';
                        this._refreshTabDot(session.id);
                        const o = session.opts;
                        const url = this._getWsUrl(o.deviceId, o.host, o.method, o.virshInfo);
                        this._connectSession(session, url);
                    }, delay);
                }
            };

            ws.onerror = (err) => {
                console.error(`[Terminal] WS error`, err);
                if (!this._tabs.has(session.id)) return;
                session.status = 'disconnected';
                this._refreshTabDot(session.id);
                if (session.term) session.term.writeln('\r\n\x1b[31m[ERROR]\x1b[0m WebSocket connection failed');
                try { ws.close(); } catch (_) {}
            };

            if (session.onDataDisposable) {
                try { session.onDataDisposable.dispose(); } catch (_) {}
            }
            if (session.term) {
                session.onDataDisposable = session.term.onData((data) => {
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({ type: 'input', data }));
                    }
                });
            }
        } catch (e) {
            session.status = 'disconnected';
            this._refreshTabDot(session.id);
            if (session.term) session.term.writeln('\x1b[31m[ERROR]\x1b[0m ' + e.message);
        }
    },

    _sendResize(session) {
        if (!session) session = this._getActiveSession();
        if (!session || !session.ws || session.ws.readyState !== WebSocket.OPEN || !session.term) return;
        session.ws.send(JSON.stringify({ type: 'resize', cols: session.term.cols, rows: session.term.rows }));
    },

    _startHeartbeat(session) {
        this._stopHeartbeat(session);
        session._lastPongAt = Date.now();
        session.heartbeatInterval = setInterval(() => {
            if (!this._tabs.has(session.id)) { this._stopHeartbeat(session); return; }
            if (session.ws && session.ws.readyState === WebSocket.OPEN) {
                const sincePong = Date.now() - (session._lastPongAt || 0);
                if (sincePong > this._pongTimeoutMs) {
                    if (session.term) session.term.writeln('\r\n\x1b[33m[WARN]\x1b[0m Connection appears dead (no heartbeat response)');
                    try { session.ws.close(1006); } catch (_) {}
                    return;
                }
                session.lastPingSent = Date.now();
                session.ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 15000);
    },

    _stopHeartbeat(session) {
        if (session.heartbeatInterval) {
            clearInterval(session.heartbeatInterval);
            session.heartbeatInterval = null;
        }
    },

    _updateConnInfo() {
        const el = this._panel?.querySelector('#terminal-conn-info');
        if (!el) return;
        const s = this._getActiveSession();
        if (!s || !s.connectedAt) {
            el.textContent = '';
            return;
        }
        const elapsed = Math.floor((Date.now() - s.connectedAt) / 1000);
        const m = Math.floor(elapsed / 60);
        const sec = elapsed % 60;
        const uptime = m > 0 ? `${m}m ${sec}s` : `${sec}s`;
        const lat = s.lastLatency != null ? ` | ${s.lastLatency}ms` : '';
        el.textContent = `${uptime}${lat}`;
    },

    _updateSizeInfo() {
        const el = this._panel?.querySelector('#terminal-size-info');
        const s = this._getActiveSession();
        if (!el || !s || !s.term) return;
        el.textContent = `${s.term.cols}x${s.term.rows} | ${this._fontSize}px`;
    },

    _startDrag(e) {
        e.preventDefault();
        if (!this._panel) return;
        const startY = e.clientY;
        const startH = this._panelHeight;
        this._panel.style.transition = 'none';
        document.body.style.userSelect = 'none';
        document.body.style.cursor = 'ns-resize';

        const onMove = (me) => {
            const delta = startY - me.clientY;
            const newH = Math.max(120, Math.min(window.innerHeight - 60, startH + delta));
            this._panelHeight = newH;
            this._panel.style.height = newH + 'px';
        };
        const onUp = () => {
            this._panel.style.transition = 'height 0.15s ease';
            document.body.style.userSelect = '';
            document.body.style.cursor = '';
            localStorage.setItem('terminal-height', String(this._panelHeight));
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
            const s = this._getActiveSession();
            if (s && s.fitAddon && !this._isMinimized) {
                try { s.fitAddon.fit(); } catch (_) {}
                this._sendResize(s);
                this._updateSizeInfo();
            }
        };
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    },

    _changeFontSize(delta) {
        this._fontSize = Math.max(9, Math.min(24, this._fontSize + delta));
        localStorage.setItem('terminal-font-size', String(this._fontSize));
        for (const [, sess] of this._tabs) {
            if (sess.term) {
                sess.term.options.fontSize = this._fontSize;
                if (sess.fitAddon && !this._isMinimized) {
                    sess.fitAddon.fit();
                    this._sendResize(sess);
                }
            }
        }
        this._updateSizeInfo();
    },

    _toggleSearch() {
        const s = this._getActiveSession();
        if (this._isSearchOpen) {
            this._closeSearch();
            return;
        }
        if (!s || !s.searchAddon) return;

        this._isSearchOpen = true;
        const bar = document.createElement('div');
        bar.id = 'terminal-search-bar';
        Object.assign(bar.style, {
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '4px 10px',
            background: 'rgba(0,180,216,0.08)',
            borderBottom: '1px solid rgba(0,180,216,0.15)',
        });
        const input = document.createElement('input');
        Object.assign(input.style, {
            flex: '1', background: 'rgba(255,255,255,0.08)',
            border: '1px solid rgba(0,180,216,0.3)', borderRadius: '4px',
            padding: '3px 8px', color: 'var(--dn-text-light, #E0E6ED)',
            fontSize: '12px', fontFamily: 'JetBrains Mono, monospace',
            outline: 'none',
        });
        input.placeholder = 'Search active tab...';

        const prevBtn = document.createElement('button');
        prevBtn.textContent = '<';
        this._styleMiniBtn(prevBtn);
        prevBtn.onclick = () => s.searchAddon.findPrevious(input.value);

        const nextBtn = document.createElement('button');
        nextBtn.textContent = '>';
        this._styleMiniBtn(nextBtn);
        nextBtn.onclick = () => s.searchAddon.findNext(input.value);

        const closeBtn = document.createElement('button');
        closeBtn.textContent = 'X';
        this._styleMiniBtn(closeBtn);
        closeBtn.onclick = () => this._closeSearch();

        input.addEventListener('keydown', (ev) => {
            if (ev.key === 'Enter') {
                ev.preventDefault();
                if (ev.shiftKey) s.searchAddon.findPrevious(input.value);
                else s.searchAddon.findNext(input.value);
            }
            if (ev.key === 'Escape') {
                ev.preventDefault();
                this._closeSearch();
            }
        });
        input.addEventListener('input', () => {
            if (input.value) s.searchAddon.findNext(input.value);
        });

        bar.append(input, prevBtn, nextBtn, closeBtn);
        const header = this._panel?.querySelector('#terminal-header-row');
        if (header && header.nextSibling) {
            this._panel.insertBefore(bar, header.nextSibling);
        } else if (this._panel) {
            this._panel.insertBefore(bar, this._panel.querySelector('#terminal-body'));
        }
        this._searchBar = bar;
        input.focus();
    },

    _styleMiniBtn(btn) {
        Object.assign(btn.style, {
            padding: '3px 8px', fontSize: '11px', borderRadius: '4px',
            cursor: 'pointer', border: '1px solid rgba(0,180,216,0.25)',
            background: 'transparent', color: 'var(--dn-text-light, #E0E6ED)',
        });
    },

    _closeSearch() {
        this._isSearchOpen = false;
        if (this._searchBar) {
            this._searchBar.remove();
            this._searchBar = null;
        }
        const s = this._getActiveSession();
        if (s && s.searchAddon) {
            try { s.searchAddon.clearDecorations(); } catch (_) {}
        }
        if (s && s.term) s.term.focus();
    },

    _showContextMenu(x, y) {
        this._hideContextMenu();
        const menu = document.createElement('div');
        Object.assign(menu.style, {
            position: 'fixed', left: x + 'px', top: y + 'px',
            zIndex: '100000',
            background: 'var(--dn-bg-dark-secondary, #1B263B)',
            border: '1px solid rgba(0,180,216,0.3)',
            borderRadius: '6px', padding: '4px 0',
            boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
            minWidth: '180px',
            fontFamily: 'Poppins, sans-serif',
        });

        const items = [
            { label: 'Copy', action: () => this._copySelection() },
            { label: 'Paste', action: () => this._pasteFromClipboard() },
            { label: 'divider' },
            { label: 'Search', action: () => this._toggleSearch() },
            { label: 'Clear Terminal', action: () => this._getActiveSession()?.term?.clear() },
            { label: 'divider' },
            { label: 'Close Tab', action: () => {
                const sid = this._activeTabId;
                if (sid) this._closeTab(sid);
            } },
            { label: 'Close Other Tabs', action: () => this._closeOtherTabs() },
            { label: 'divider' },
            { label: 'Reconnect Tab', action: () => this._reconnect() },
        ];

        items.forEach(item => {
            if (item.label === 'divider') {
                const hr = document.createElement('div');
                hr.style.cssText = 'height:1px;margin:4px 8px;background:rgba(0,180,216,0.15);';
                menu.appendChild(hr);
                return;
            }
            const row = document.createElement('div');
            Object.assign(row.style, {
                padding: '5px 14px', cursor: 'pointer', fontSize: '12px',
                color: 'var(--dn-text-light, #E0E6ED)',
            });
            row.textContent = item.label;
            row.addEventListener('mouseenter', () => { row.style.background = 'rgba(0,180,216,0.12)'; });
            row.addEventListener('mouseleave', () => { row.style.background = 'transparent'; });
            row.addEventListener('click', () => {
                this._hideContextMenu();
                item.action();
            });
            menu.appendChild(row);
        });

        document.body.appendChild(menu);
        this._contextMenu = menu;
        requestAnimationFrame(() => {
            const rect = menu.getBoundingClientRect();
            if (rect.right > window.innerWidth) menu.style.left = (window.innerWidth - rect.width - 8) + 'px';
            if (rect.bottom > window.innerHeight) menu.style.top = (window.innerHeight - rect.height - 8) + 'px';
        });
        const dismiss = (ev) => {
            if (!menu.contains(ev.target)) {
                this._hideContextMenu();
                document.removeEventListener('mousedown', dismiss);
            }
        };
        setTimeout(() => document.addEventListener('mousedown', dismiss), 0);
    },

    _hideContextMenu() {
        if (this._contextMenu) {
            this._contextMenu.remove();
            this._contextMenu = null;
        }
    },

    _copySelection() {
        const s = this._getActiveSession();
        if (!s || !s.term) return;
        const sel = s.term.getSelection();
        if (sel) {
            const cpFn = (typeof window.safeClipboardWrite === 'function')
                ? window.safeClipboardWrite
                : (navigator.clipboard?.writeText?.bind(navigator.clipboard) || null);
            if (cpFn) cpFn(sel).catch(() => {});
        }
    },

    async _pasteFromClipboard() {
        const s = this._getActiveSession();
        try {
            const text = await navigator.clipboard.readText();
            if (text && s && s.ws && s.ws.readyState === WebSocket.OPEN) {
                s.ws.send(JSON.stringify({ type: 'input', data: text }));
            }
        } catch (_) {}
    },

    _reconnect() {
        const s = this._getActiveSession();
        if (!s) return;
        if (s._reconnectTimer) clearTimeout(s._reconnectTimer);
        s._noAutoReconnect = false;
        s._reconnectAttempts = 0;
        if (s.ws) {
            try {
                if (s.ws.readyState === WebSocket.OPEN) {
                    s.ws.send(JSON.stringify({ type: 'disconnect' }));
                }
                s.ws.close(1000);
            } catch (_) {}
            s.ws = null;
        }
        this._stopHeartbeat(s);
        if (s.onDataDisposable) {
            try { s.onDataDisposable.dispose(); } catch (_) {}
            s.onDataDisposable = null;
        }
        if (s.term) s.term.writeln('\r\n\x1b[36m[INFO]\x1b[0m Reconnecting...');
        const o = s.opts;
        const wsUrl = this._getWsUrl(o.deviceId, o.host, o.method, o.virshInfo);
        s.status = 'connecting';
        this._refreshTabDot(s.id);
        this._connectSession(s, wsUrl);
    },

    _closeTab(id) {
        const sess = this._tabs.get(id);
        if (!sess) return;

        if (sess._reconnectTimer) clearTimeout(sess._reconnectTimer);
        sess._noAutoReconnect = true;
        this._stopHeartbeat(sess);
        if (sess.onDataDisposable) {
            try { sess.onDataDisposable.dispose(); } catch (_) {}
        }
        if (sess.ws) {
            try {
                if (sess.ws.readyState === WebSocket.OPEN) {
                    sess.ws.send(JSON.stringify({ type: 'disconnect' }));
                }
                sess.ws.close(1000);
            } catch (_) {}
        }
        if (sess.term) {
            try { sess.term.dispose(); } catch (_) {}
        }
        if (sess.container) sess.container.remove();

        const allKeys = [...this._tabs.keys()];
        const closedIdx = allKeys.indexOf(id);
        this._tabs.delete(id);

        if (this._activeTabId === id) {
            const remaining = [...this._tabs.keys()];
            if (remaining.length) {
                const newIdx = Math.max(0, Math.min(closedIdx - 1, remaining.length - 1));
                this._activeTabId = remaining[newIdx];
            } else {
                this._activeTabId = null;
            }
            if (this._activeTabId) {
                this._switchTab(this._activeTabId);
            }
        }

        this._renderTabBar();

        if (this._tabs.size === 0) {
            this._destroyPanelCompletely();
        } else if (this._activeTabId) {
            this._updateConnInfo();
            this._updateSizeInfo();
        }
    },

    _closeOtherTabs() {
        const keep = this._activeTabId;
        if (!keep) return;
        for (const tid of [...this._tabs.keys()]) {
            if (tid !== keep) this._closeTab(tid);
        }
    },

    _toggleMinimize() {
        if (!this._panel) return;
        const body = this._panel.querySelector('#terminal-body');
        const statusBar = this._panel.querySelector('#terminal-status-bar');
        const minBtn = this._panel.querySelector('#terminal-minimize');
        const header = this._panel.querySelector('#terminal-header-row');
        this._isMinimized = !this._isMinimized;

        if (this._isMinimized) {
            if (body) body.style.display = 'none';
            if (statusBar) statusBar.style.display = 'none';
            if (this._searchBar) this._searchBar.style.display = 'none';
            this._panel.style.height = (header ? header.offsetHeight : 40) + 'px';
            if (minBtn) minBtn.textContent = '\u25a1';
        } else {
            if (body) body.style.display = '';
            if (statusBar) statusBar.style.display = '';
            if (this._searchBar) this._searchBar.style.display = '';
            this._panel.style.height = this._panelHeight + 'px';
            if (minBtn) minBtn.textContent = '_';
            const s = this._getActiveSession();
            if (s && s.fitAddon) {
                requestAnimationFrame(() => {
                    s.fitAddon.fit();
                    this._sendResize(s);
                    this._updateSizeInfo();
                });
            }
        }
    },

    _destroyPanelCompletely() {
        this._closeSearch();
        this._hideContextMenu();
        if (this._statusInterval) {
            clearInterval(this._statusInterval);
            this._statusInterval = null;
        }
        if (this._keyHandler) {
            document.removeEventListener('keydown', this._keyHandler);
            this._keyHandler = null;
        }
        if (this._resizeHandler) {
            window.removeEventListener('resize', this._resizeHandler);
            this._resizeHandler = null;
        }
        if (this._panel) {
            this._panel.remove();
            this._panel = null;
        }
        this._tabs.clear();
        this._activeTabId = null;
        this._isMinimized = false;
    },

    close() {
        for (const tid of [...this._tabs.keys()]) {
            this._closeTab(tid);
        }
    },
};
