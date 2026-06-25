/**
 * topology-xray-popup.js - XRAY Capture Popup for Links
 * Shows DP/CP/DNAAS-DP capture options on selected device-to-device links.
 */

'use strict';

// Auth-aware fetch: every /api/xray/* hit MUST carry the JWT or the
// backend treats the request as anonymous and returns 401. Bare fetch()
// silently dropped the token in multi-user deployments, so the popup
// would hit "Authentication required" with no useful message in the UI.
// Falls back to plain fetch() when TopologyAuth hasn't loaded yet (test
// harnesses, the legacy single-user mode, etc).
function _xrayAuthFetch(url, opts) {
    if (window.TopologyAuth && typeof window.TopologyAuth.authFetch === 'function') {
        return window.TopologyAuth.authFetch(url, opts);
    }
    return fetch(url, opts);
}

window.XrayPopup = {
    _popup: null,
    _activeCapture: null,
    _pollTimer: null,
    _temporarilyHidden: false,
    _lastState: null,
    _pollFailures: 0,

    // POV-side DNAAS guard: capture against a DNAAS fabric device
    // (LEAF/SPINE/NCM/NCF/...) in cp/dp mode is not supported -- the
    // tcpdump path SSHes into a DNOS shell that doesn't exist on those
    // devices. Use 'dnaas-dp' mode instead (mirror via uplink). Both
    // the popup UI and `_startCapture` consult `_isDnaasPov` so the
    // user gets a clear inline message before the backend has to
    // refuse. Mirrors `editor.isDnaasRouter(label)` -- if that helper
    // is missing (test harness) we fall back to a label-keyword scan.
    _DNAAS_POV_KEYWORDS: ['DNAAS', 'LEAF', 'SPINE', 'FABRIC', 'TOR',
        'AGGREGATION', 'AGG-', 'CORE-', '-LEAF', '-SPINE', 'NCM', 'NCF'],
    _isDnaasPov(device) {
        if (!device) return false;
        const editor = this._editor;
        if (editor && typeof editor.isDnaasRouter === 'function') {
            const lbl = device.label || device.deviceSerial || '';
            return !!editor.isDnaasRouter(lbl);
        }
        const upper = String(device.label || '').toUpperCase();
        return this._DNAAS_POV_KEYWORDS.some(kw => upper.includes(kw));
    },

    // Per-user Mac verification cache (mirrors backend xray.json mac.verified_* fields).
    // When `ok` is true for the current mac.ip_vpn AND within TTL, Start Capture unlocks
    // for mac/mac-live output. Anything else keeps the button locked.
    _macVerification: { ip: null, at: 0, ok: false },
    _MAC_VERIFY_TTL_MS: 30 * 60 * 1000,
    _macVerifyListenerBound: false,
    _dnaasMirrorPreflightCache: {},
    _dnaasMirrorPreflightKey: '',

    _isMacVerificationValid(currentIp) {
        const mv = this._macVerification;
        if (!mv || !mv.ok) return false;
        if (!currentIp) return false;
        if (mv.ip !== currentIp) return false;
        if (!mv.at) return false;
        return (Date.now() - mv.at) < this._MAC_VERIFY_TTL_MS;
    },

    async _refreshMacVerificationFromConfig() {
        try {
            const resp = await _xrayAuthFetch('/api/xray/config');
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const cfg = await resp.json();
            const mac = cfg?.mac || {};
            const ip = (mac.ip_vpn || '').trim();
            const vIp = (mac.verified_ip || '').trim();
            const vAt = mac.verified_at;
            let atMs = 0;
            if (typeof vAt === 'number') atMs = vAt * 1000;
            else if (typeof vAt === 'string' && vAt) {
                const parsed = Date.parse(vAt);
                if (!Number.isNaN(parsed)) atMs = parsed;
            }
            if (ip && vIp && vIp === ip && atMs && (Date.now() - atMs) < this._MAC_VERIFY_TTL_MS) {
                this._macVerification = { ip, at: atMs, ok: true };
            } else {
                this._macVerification = { ip: null, at: 0, ok: false };
            }
            return { currentIp: ip, verifiedIp: vIp, at: atMs };
        } catch (e) {
            this._macVerification = { ip: null, at: 0, ok: false };
            return { error: e.message };
        }
    },

    _needsMacDelivery() {
        if (!this._state) return false;
        return this._state.output === 'mac' || this._state.mode === 'dp';
    },

    _applyMacGate() {
        const btn = this._popup?.querySelector('#xray-start-btn');
        if (!btn) return;
        // Do not override the active-capture/countdown state.
        if (btn.classList.contains('capturing')) return;
        if (!this._needsMacDelivery()) {
            btn.disabled = false;
            btn.title = '';
            btn.removeAttribute('data-mac-locked');
            return;
        }
        if (this._isMacVerificationValid(this._macVerification.ip)) {
            btn.disabled = false;
            btn.title = `Mac verified at ${this._macVerification.ip}`;
            btn.removeAttribute('data-mac-locked');
        } else {
            btn.disabled = true;
            btn.title = 'Verify Mac workstation before starting capture';
            btn.setAttribute('data-mac-locked', '1');
        }
    },

    _renderMacVerifyPanel(reason) {
        const status = this._popup?.querySelector('#xray-status');
        if (!status) return;
        const isDark = document.body.classList.contains('dark-mode');
        status.style.display = 'block';
        status.style.background = 'rgba(255,165,0,0.12)';
        status.style.color = '#FF9500';
        status.innerHTML = '';
        const headline = document.createElement('div');
        const currentIp = this._lastConfigIp || '';
        if (reason === 'no_ip') {
            headline.textContent = 'No Mac IP configured -- set it in XRAY settings.';
        } else if (reason === 'stale_ip') {
            headline.textContent = `Mac IP changed -- re-verify ${currentIp || ''} before capture.`;
        } else if (reason === 'expired') {
            headline.textContent = `Mac verification expired -- re-verify ${currentIp || ''} to continue.`;
        } else if (reason === 'unreachable') {
            headline.textContent = `Mac unreachable at ${currentIp || '(not set)'} -- update IP to continue.`;
        } else {
            headline.textContent = `Verify Mac workstation ${currentIp || ''} to unlock capture.`;
        }
        headline.style.marginBottom = '6px';
        status.appendChild(headline);

        const row = document.createElement('div');
        row.style.cssText = 'display:flex;gap:6px;align-items:center;flex-wrap:wrap;';
        const input = document.createElement('input');
        input.type = 'text';
        input.placeholder = 'Mac IP (e.g. 10.x.x.x)';
        input.value = currentIp;
        input.style.cssText = `flex:1;min-width:140px;padding:5px 8px;border-radius:4px;border:1px solid ${isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)'};background:${isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.03)'};color:${isDark ? '#c8d0da' : '#333'};font-size:11px;font-family:'Space Grotesk',monospace;outline:none;`;
        input.addEventListener('keydown', e => e.stopPropagation());

        const verifyBtn = document.createElement('button');
        verifyBtn.textContent = 'Verify';
        verifyBtn.style.cssText = `padding:5px 12px;border-radius:4px;border:none;background:#0066FA;color:#fff;font-size:11px;cursor:pointer;font-weight:600;`;

        const pcapBtn = document.createElement('button');
        pcapBtn.textContent = 'Use pcap';
        pcapBtn.style.cssText = `padding:5px 10px;border-radius:4px;border:1px solid ${isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)'};background:transparent;color:${isDark ? '#8899aa' : '#666'};font-size:11px;cursor:pointer;`;

        row.appendChild(input);
        row.appendChild(verifyBtn);
        row.appendChild(pcapBtn);
        status.appendChild(row);

        verifyBtn.onclick = async () => {
            const newIp = input.value.trim();
            if (!newIp) { input.style.borderColor = '#e74c3c'; return; }
            verifyBtn.textContent = 'Checking...';
            verifyBtn.disabled = true;
            try {
                if (newIp !== currentIp) {
                    await _xrayAuthFetch('/api/xray/config', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ mac: { ip_vpn: newIp } })
                    });
                }
                const r = await _xrayAuthFetch('/api/xray/verify-mac', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ip: newIp })
                });
                if (!r.ok) throw new Error('HTTP ' + r.status);
                const v = await r.json();
                if (v.reachable) {
                    const atMs = typeof v.verified_at === 'number' ? v.verified_at * 1000 : Date.now();
                    this._macVerification = { ip: newIp, at: atMs, ok: true };
                    this._lastConfigIp = newIp;
                    status.style.background = 'rgba(39,174,96,0.15)';
                    status.style.color = '#27ae60';
                    status.innerHTML = '';
                    status.textContent = `Mac verified at ${newIp} -- click Start Capture`;
                    this._applyMacGate();
                    try {
                        window.dispatchEvent(new CustomEvent('xray-mac-verified', {
                            detail: { ip: newIp, at: atMs }
                        }));
                    } catch (_) {}
                } else {
                    verifyBtn.textContent = 'Retry';
                    verifyBtn.disabled = false;
                    const causeTitles = {
                        auth_failed: 'Wrong Mac username or password',
                        missing_password: 'Mac password missing',
                        missing_user: 'Mac username missing',
                        ssh_refused: 'Remote Login is disabled',
                        ssh_timeout: 'SSH timed out',
                        network_unreachable: 'Mac network unreachable',
                        bad_host: 'Invalid Mac IP or host',
                        missing_sshpass: 'XRAY dependency missing'
                    };
                    const title = causeTitles[v.cause] || `Still unreachable at ${newIp}`;
                    headline.textContent = `${title} -- ${v.error || 'check IP, Remote Login, username, and password.'}`;
                    this._macVerification = { ip: null, at: 0, ok: false };
                    this._applyMacGate();
                }
            } catch (e) {
                verifyBtn.textContent = 'Retry';
                verifyBtn.disabled = false;
                headline.textContent = 'Verification failed: ' + e.message;
                this._macVerification = { ip: null, at: 0, ok: false };
                this._applyMacGate();
            }
        };
        pcapBtn.onclick = () => {
            this._state.output = 'pcap';
            const pcapOptBtn = this._popup?.querySelector(".xray-opt-btn[data-out='pcap']");
            const macOptBtn = this._popup?.querySelector(".xray-opt-btn[data-out='mac']");
            if (pcapOptBtn && macOptBtn) {
                macOptBtn.classList.remove('active');
                pcapOptBtn.classList.add('active');
            }
            const cleanupRow = this._popup?.querySelector('#xray-cleanup-row');
            if (cleanupRow) cleanupRow.style.display = 'none';
            status.style.background = 'rgba(0,102,250,0.1)';
            status.style.color = '#0066FA';
            status.innerHTML = '';
            status.textContent = 'Switched to pcap output. Click Start Capture.';
            this._applyMacGate();
        };
        input.addEventListener('keydown', e => { if (e.key === 'Enter') verifyBtn.click(); });
    },

    async _evaluateMacGate(opts) {
        opts = opts || {};
        if (!this._popup || !this._state) return;
        if (!this._needsMacDelivery()) {
            this._applyMacGate();
            return;
        }
        const info = await this._refreshMacVerificationFromConfig();
        this._lastConfigIp = info?.currentIp || '';
        const status = this._popup?.querySelector('#xray-status');
        if (this._isMacVerificationValid(this._macVerification.ip)) {
            if (status && !opts.preserveStatus) {
                status.style.display = 'block';
                status.style.background = 'rgba(39,174,96,0.15)';
                status.style.color = '#27ae60';
                status.innerHTML = '';
                status.textContent = `Mac verified at ${this._macVerification.ip}`;
            }
            this._applyMacGate();
            return;
        }
        // Not valid -- render inline verify panel with a targeted reason.
        let reason = 'unknown';
        if (!info?.currentIp) reason = 'no_ip';
        else if (info.verifiedIp && info.verifiedIp !== info.currentIp) reason = 'stale_ip';
        else if (info.at && (Date.now() - info.at) >= this._MAC_VERIFY_TTL_MS) reason = 'expired';
        else if (info.verifiedIp) reason = 'expired';
        else reason = 'unreachable';
        this._renderMacVerifyPanel(reason);
        this._applyMacGate();
    },

    _ensureMacVerifyListener() {
        if (this._macVerifyListenerBound) return;
        this._macVerifyListenerBound = true;
        window.addEventListener('xray-mac-verified', (e) => {
            const ip = e?.detail?.ip;
            const at = e?.detail?.at || Date.now();
            if (!ip) return;
            this._macVerification = { ip, at, ok: true };
            this._lastConfigIp = ip;
            if (this._popup) this._applyMacGate();
        });
        window.addEventListener('xray-mac-ip-changed', () => {
            this._macVerification = { ip: null, at: 0, ok: false };
            if (this._popup) this._evaluateMacGate();
        });
    },

    isOpenForLink(editor, link) {
        if (!this._popup || !this._link || !link) return false;
        if (editor && this._editor && editor !== this._editor) return false;
        return this._link === link || (!!link.id && this._link.id === link.id);
    },

    show(editor, link, screenPos, opts = {}) {
        if (this._link && this._link !== link) {
            this._link._xrayCaptureActive = false;
        }
        this._link = link;
        this._editor = editor;
        if (this._popup) {
            this._popup.remove();
            this._popup = null;
        }
        if (this._outsideHandler) {
            document.removeEventListener('mousedown', this._outsideHandler);
            this._outsideHandler = null;
        }
        this._temporarilyHidden = false;
        if (!link || !link.device1 || !link.device2) return;

        const device1 = editor.objects.find(d => d.id === link.device1);
        const device2 = editor.objects.find(d => d.id === link.device2);
        if (!device1 || !device2) return;
        link._xrayCaptureActive = true;
        this._device1 = device1;
        this._device2 = device2;

        const name1 = device1.label || 'Device 1';
        const name2 = device2.label || 'Device 2';
        const srcRows = opts?.srcRows || null;
        const rowForPov = (pov) => {
            if (!srcRows) return null;
            return pov === 'device2'
                ? (srcRows.device2 || srcRows.B || null)
                : (srcRows.device1 || srcRows.A || null);
        };
        const explicitSrcRow = opts?.srcRow || null;
        let srcRow = explicitSrcRow;
        let srcSide = srcRow?.side === 'B' ? 'device2' : (srcRow?.side === 'A' ? 'device1' : '');
        const isDark = editor.darkMode;

        // DNAAS POV pre-check: a DNAAS fabric device cannot be the capture
        // POV in cp/dp modes (only the dedicated dnaas-dp mode handles it
        // via the leaf+uplink mirror flow). Compute once here so the POV
        // header buttons can be disabled at render time and the default
        // POV can flip away from a DNAAS endpoint when the other side is
        // a regular DNOS device.
        const dev1IsDnaas = this._isDnaasPov(device1);
        const dev2IsDnaas = this._isDnaasPov(device2);

        // Restore last state for this link, or use defaults. If the saved
        // POV would land on a DNAAS endpoint but the other side is fine,
        // flip to the non-DNAAS endpoint so the user lands in a usable
        // state and doesn't have to debug a disabled Start button.
        const saved = this._lastState;
        let savedPov = srcSide || opts?.preferredPov || saved?.pov || 'device1';
        if (savedPov === 'device1' && dev1IsDnaas && !dev2IsDnaas) savedPov = 'device2';
        else if (savedPov === 'device2' && dev2IsDnaas && !dev1IsDnaas) savedPov = 'device1';
        if (!explicitSrcRow && srcRows) {
            srcRow = rowForPov(savedPov) || rowForPov(savedPov === 'device1' ? 'device2' : 'device1');
            srcSide = srcRow?.side === 'B' ? 'device2' : (srcRow?.side === 'A' ? 'device1' : '');
        }
        const hasLinkContext = !!(srcRow || srcRows);
        const intf1 = (srcRows?.device1?.ifName || (srcSide === 'device1' && srcRow?.ifName)) || link.device1Interface || link.linkDetails?.interfaceA || '';
        const intf2 = (srcRows?.device2?.ifName || (srcSide === 'device2' && srcRow?.ifName)) || link.device2Interface || link.linkDetails?.interfaceB || '';
        const st = {
            mode: saved?.mode || 'cp',
            duration: saved?.duration || 10,
            output: saved?.output || 'mac',
            pov: savedPov,
            direction: saved?.direction || 'both',
            filters: saved?.filters ? [...saved.filters] : [],
            excludeInternal: saved?.excludeInternal !== undefined ? saved.excludeInternal : true,
            srcRows,
            srcRow,
            useLinkContext: hasLinkContext,
            autoVlanFilter: !!(srcRow && (srcRow.vlanOuter || srcRow.vlanInner)),
            autoIpFilter: !!(srcRow && srcRow.ip)
        };

        const glassBg = isDark ? 'rgba(15, 15, 25, 0.28)' : 'rgba(255, 255, 255, 0.28)';
        const glassBorder = isDark ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.08)';
        const glassShadow = isDark
            ? '0 4px 30px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.08)'
            : '0 4px 30px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.5)';

        const anchorCenter = screenPos.anchor === 'center';
        const toolbarGap = 6;
        const popup = document.createElement('div');
        popup.id = 'xray-capture-popup';
        popup.style.cssText = `
            position: fixed;
            left: ${screenPos.x}px;
            top: ${screenPos.y + toolbarGap}px;
            ${anchorCenter ? 'transform: translateX(-50%);' : ''}
            z-index: 100000;
            min-width: 300px;
            max-width: 360px;
            font-family: 'Poppins', sans-serif;
            color: ${isDark ? '#e0e6ed' : '#1a1a1a'};
            visibility: hidden;
        `;
        popup.style.background = glassBg;
        popup.style.border = '1px solid ' + glassBorder;
        popup.style.borderRadius = '12px';
        popup.style.padding = '12px 14px';
        popup.style.backdropFilter = 'blur(24px) saturate(200%)';
        popup.style.webkitBackdropFilter = 'blur(24px) saturate(200%)';
        popup.style.boxShadow = glassShadow;

        const optGlassBg = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)';
        const optGlassBorder = isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.08)';

        const durActive = (v) => st.duration === v ? ' active' : '';
        const dirActive = (v) => st.direction === v ? ' active' : '';
        const outActive = (v) => st.output === v ? ' active' : '';
        const povActive = (v) => st.pov === v ? ' active' : '';
        const modeActive = (v) => st.mode === v ? ' active' : '';
        const filterActive = (v) => st.filters.includes(v) ? ' active' : '';

        popup.innerHTML = `
            <style>
                @keyframes xrayPopupFadeIn { from { opacity: 0; transform: translateY(-8px) scale(0.98); } to { opacity: 1; transform: translateY(0) scale(1); } }
                #xray-capture-popup { position: relative; }
                #xray-capture-popup::before {
                    content: ''; position: absolute; top: -7px; left: 50%; transform: translateX(-50%);
                    width: 0; height: 0;
                    border-left: 8px solid transparent; border-right: 8px solid transparent;
                    border-bottom: 8px solid ${glassBg};
                }
                #xray-capture-popup.above::before {
                    top: auto; bottom: -7px;
                    border-bottom: none;
                    border-top: 8px solid ${glassBg};
                }
                #xray-capture-popup .xray-mode-btn {
                    padding: 6px 12px; border-radius: 6px; border: 1px solid transparent;
                    cursor: pointer; font-size: 11px; font-weight: 600; font-family: 'Poppins', sans-serif;
                    transition: all 0.12s ease; flex: 1; text-align: center;
                    background: ${optGlassBg}; backdrop-filter: blur(8px);
                    color: ${isDark ? '#d0d6de' : '#333'};
                }
                #xray-capture-popup .xray-mode-btn:hover:not(:disabled) { box-shadow: 0 2px 6px rgba(0,102,250,0.25); }
                #xray-capture-popup .xray-mode-btn:disabled {
                    cursor: not-allowed;
                    color: ${isDark ? 'rgba(208,214,222,0.55)' : 'rgba(51,51,51,0.55)'};
                    background: ${isDark ? 'rgba(255,255,255,0.045)' : 'rgba(0,0,0,0.035)'};
                    border-color: ${isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)'};
                }
                #xray-capture-popup .xray-mode-btn .xray-mode-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; margin-right: 4px; vertical-align: middle; }
                #xray-capture-popup .xray-mode-btn:not(:disabled) .xray-mode-dot { background: #27ae60; box-shadow: 0 0 4px rgba(39,174,96,0.6); }
                #xray-capture-popup .xray-mode-btn:disabled .xray-mode-dot { background: rgba(128,128,128,0.5); }
                #xray-capture-popup .xray-mode-help { display: inline-flex; align-items: center; justify-content: center; width: 12px; height: 12px; border-radius: 50%; font-size: 8px; font-weight: 700; margin-left: 3px; vertical-align: middle; cursor: help; background: ${isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.08)'}; color: ${isDark ? '#8899aa' : '#666'}; position: relative; }
                #xray-capture-popup .xray-mode-help:hover { background: ${isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.12)'}; color: ${isDark ? '#aabbcc' : '#333'}; }
                #xray-capture-popup .xray-mode-help .xray-help-tip { display: none; position: absolute; bottom: 18px; left: 50%; transform: translateX(-50%); width: 300px; padding: 11px 13px; border-radius: 10px; font-size: 10px; font-weight: 500; line-height: 1.55; text-align: left; z-index: 999999; pointer-events: none; background: ${isDark ? '#101827' : '#ffffff'}; color: ${isDark ? '#f8fafc' : '#111827'}; border: 1px solid ${isDark ? 'rgba(148,163,184,0.35)' : 'rgba(15,23,42,0.14)'}; box-shadow: 0 16px 44px rgba(0,0,0,0.55); max-height: 340px; overflow-y: auto; opacity: 1 !important; text-shadow: none; }
                #xray-capture-popup .xray-mode-help:hover .xray-help-tip { display: block; }
                #xray-capture-popup .xray-mode-btn.active { background: linear-gradient(135deg, #0066FA, #0052CC); color: #fff; border-color: rgba(255,255,255,0.2); }
                #xray-capture-popup .xray-opt-btn {
                    padding: 4px 8px; border-radius: 5px; border: 1px solid ${optGlassBorder};
                    cursor: pointer; font-size: 10px; font-family: 'Poppins', sans-serif;
                    background: ${optGlassBg}; backdrop-filter: blur(8px);
                    color: ${isDark ? '#ccc' : '#555'}; transition: all 0.12s ease;
                }
                #xray-capture-popup .xray-opt-btn:hover { background: rgba(0,102,250,0.15); color: #0066FA; }
                #xray-capture-popup .xray-opt-btn.active { background: rgba(0,102,250,0.2); color: #0066FA; border-color: #0066FA; font-weight: 600; }
                #xray-capture-popup .xray-pov-btn {
                    padding: 5px 10px; border-radius: 6px; border: 1px solid ${optGlassBorder};
                    cursor: pointer; font-size: 10px; font-family: 'Poppins', sans-serif;
                    background: ${optGlassBg}; backdrop-filter: blur(8px);
                    color: ${isDark ? '#ccc' : '#555'}; transition: all 0.12s ease; flex: 1; text-align: center;
                }
                #xray-capture-popup .xray-pov-btn:hover { background: rgba(0,102,250,0.15); }
                #xray-capture-popup .xray-pov-btn.active { background: rgba(0,102,250,0.2); color: #0066FA; border-color: #0066FA; font-weight: 600; }
                #xray-capture-popup .xray-start-btn {
                    width: 100%; padding: 8px; border-radius: 8px; border: none;
                    background: linear-gradient(135deg, #0066FA, #0052CC); color: #fff;
                    font-size: 12px; font-weight: 700; cursor: pointer; font-family: 'Poppins', sans-serif;
                    transition: all 0.15s ease; letter-spacing: 0.3px;
                }
                #xray-capture-popup .xray-start-btn:hover { background: linear-gradient(135deg, #3385FF, #0066FA); box-shadow: 0 3px 12px rgba(0,102,250,0.35); }
                #xray-capture-popup .xray-start-btn:disabled { opacity: 0.5; cursor: not-allowed; }
                #xray-capture-popup .xray-start-btn.capturing { background: linear-gradient(135deg, #FF5E1F, #CC4A16); }
                #xray-capture-popup .xray-section-label { font-size: 9px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; opacity: 0.75; color: ${isDark ? '#b0b8c4' : '#555'}; }
                #xray-capture-popup .xray-status { padding: 6px 10px; border-radius: 6px; font-size: 10px; margin-top: 8px; display: none; font-family: 'SF Mono', monospace; max-height: 160px; overflow-y: auto; }
                #xray-capture-popup .xray-toggle-row { display: flex; align-items: center; gap: 6px; font-size: 10px; opacity: 0.85; margin-bottom: 8px; color: ${isDark ? '#c0c8d2' : '#444'}; }
                #xray-capture-popup .xray-toggle-row input[type="checkbox"] { width: 13px; height: 13px; accent-color: #0066FA; cursor: pointer; }
                #xray-capture-popup .xray-selected-interface-pill {
                    display: inline-flex; align-items: center; gap: 5px;
                    padding: 4px 8px; margin: 2px 0;
                    border-radius: 6px; font-weight: 800; font-size: 11px;
                    letter-spacing: 0.2px;
                    color: ${isDark ? '#d9f4ff' : '#003b80'};
                    background: ${isDark ? 'rgba(0,102,250,0.24)' : 'rgba(0,102,250,0.12)'};
                    border: 1px solid ${isDark ? 'rgba(126,207,255,0.45)' : 'rgba(0,102,250,0.28)'};
                    box-shadow: inset 0 0 0 1px ${isDark ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.45)'};
                }
            </style>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <div style="font-size: 11px; font-weight: 600; display: flex; align-items: center; gap: 4px; color: ${isDark ? '#8899aa' : '#777'};">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#0066FA" stroke-width="2.5"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/></svg>
                    Packet Capture
                </div>
                <button id="xray-close-btn" style="background: none; border: none; cursor: pointer; color: ${isDark ? '#888' : '#999'}; font-size: 16px; padding: 0 2px; line-height: 1;">&times;</button>
            </div>
            <div id="xray-pov-header" style="display: flex; align-items: center; gap: 0; margin-bottom: 10px; font-size: 12px; font-weight: 600;">
                <button class="xray-pov-btn${povActive('device1')}" data-pov="device1" style="flex: 1; padding: 6px 8px; border-radius: 6px 0 0 6px; border: 1px solid ${optGlassBorder}; border-right: none; cursor: pointer; background: ${st.pov === 'device1' ? 'linear-gradient(135deg, #0066FA, #0052CC)' : optGlassBg}; color: ${st.pov === 'device1' ? '#fff' : (isDark ? '#b8c0cc' : '#555')}; font-family: 'Poppins', sans-serif; font-size: 11px; font-weight: 600; transition: all 0.12s ease; text-align: center;">
                    ${name1}<span style="font-size:9px; opacity:0.7; margin-left:3px;">${intf1 ? '[' + intf1 + ']' : '[auto]'}</span>
                </button>
                <span style="padding: 6px 6px; background: ${optGlassBg}; border-top: 1px solid ${optGlassBorder}; border-bottom: 1px solid ${optGlassBorder}; color: ${isDark ? '#556' : '#999'}; font-size: 10px; line-height: 1;">&harr;</span>
                <button class="xray-pov-btn${povActive('device2')}" data-pov="device2" style="flex: 1; padding: 6px 8px; border-radius: 0 6px 6px 0; border: 1px solid ${optGlassBorder}; border-left: none; cursor: pointer; background: ${st.pov === 'device2' ? 'linear-gradient(135deg, #0066FA, #0052CC)' : optGlassBg}; color: ${st.pov === 'device2' ? '#fff' : (isDark ? '#b8c0cc' : '#555')}; font-family: 'Poppins', sans-serif; font-size: 11px; font-weight: 600; transition: all 0.12s ease; text-align: center;">
                    ${name2}<span style="font-size:9px; opacity:0.7; margin-left:3px;">${intf2 ? '[' + intf2 + ']' : '[auto]'}</span>
                </button>
            </div>

            <div class="xray-section-label">Mode</div>
            <div style="display: flex; gap: 4px; margin-bottom: 4px;">
                <button class="xray-mode-btn${modeActive('cp')}" data-mode="cp" aria-label="Control Plane - capture on DNOS device">CP</button>
                <button class="xray-mode-btn${modeActive('dp')}" data-mode="dp" disabled aria-label="Checking Live Capture availability"><span class="xray-mode-dot"></span>Live Capture<span class="xray-mode-help">?<span class="xray-help-tip"><b>Live Data-Plane Capture (Double-SPAN)</b><br><br>Mirrors live traffic from a DNOS interface through an Arista switch to Wireshark on your Mac.<br><br><b>How it works:</b><br>1. Auto-configures DNOS service port-mirroring session<br>2. Auto-configures Arista monitor session (source &rarr; CPU)<br>3. Streams packets via tcpdump to your Mac / pcap file<br>4. Auto-cleans up both sessions when done<br><br><b>Requirements:</b><br>&bull; An Arista switch in the POV device's LLDP neighbors<br>&bull; SSH access to both the DUT and the Arista (credentials in XRAY config)<br>&bull; The DUT interface is taken from the link table or selected manually<br><br><b>No pre-configuration needed</b> -- port-mirroring and monitor sessions are created and removed automatically.</span></span></button>
                <button class="xray-mode-btn${modeActive('dnaas-dp')}" data-mode="dnaas-dp" disabled aria-label="Checking DP DNAAS availability"><span class="xray-mode-dot"></span>DP (DNAAS)</button>
            </div>
            <div id="xray-mode-hint" style="font-size: 9px; margin-bottom: 10px; min-height: 14px; color: ${isDark ? '#90989f' : '#888'};">Detecting DP availability...</div>

            <div id="xray-intf-picker-row" style="display: none; margin-bottom: 10px;">
                <div class="xray-section-label">Source Interface</div>
                <div id="xray-intf-info" style="font-size: 10px; color: ${isDark ? '#7ecfff' : '#0066FA'}; margin-bottom: 4px; font-weight: 500;"></div>
                <select id="xray-intf-select" style="display: none; width: 100%; padding: 5px 8px; border-radius: 4px; border: 1px solid ${optGlassBorder}; background: ${optGlassBg}; color: ${isDark ? '#c8d0da' : '#333'}; font-size: 10px; font-family: 'Space Grotesk', monospace; cursor: pointer; outline: none;">
                </select>
                <div id="xray-intf-loading" style="display: none; font-size: 9px; color: ${isDark ? '#90989f' : '#888'};">Fetching interfaces...</div>
            </div>

            <div id="xray-dur-dir-row" style="display: flex; gap: 16px; margin-bottom: 10px;">
                <div style="flex:1;">
            <div class="xray-section-label">Duration</div>
                    <div style="display: flex; gap: 3px;">
                        <button class="xray-opt-btn${durActive(3)}" data-dur="3">3s</button>
                        <button class="xray-opt-btn${durActive(5)}" data-dur="5">5s</button>
                        <button class="xray-opt-btn${durActive(10)}" data-dur="10">10s</button>
                        <button class="xray-opt-btn${durActive(30)}" data-dur="30">30s</button>
                        <button class="xray-opt-btn${durActive(60)}" data-dur="60">60s</button>
                    </div>
                </div>
                <div>
                    <div class="xray-section-label">Direction</div>
                    <div style="display: flex; gap: 3px;">
                        <button class="xray-opt-btn${dirActive('ingress')}" data-dir="ingress">In</button>
                        <button class="xray-opt-btn${dirActive('egress')}" data-dir="egress">Out</button>
                        <button class="xray-opt-btn${dirActive('both')}" data-dir="both">Both</button>
                    </div>
                </div>
            </div>

            <div id="xray-filters-section">
            <div class="xray-section-label">Filters</div>
            <div style="display: flex; flex-wrap: wrap; gap: 3px; margin-bottom: 6px;">
                <button class="xray-opt-btn xray-filter-btn${filterActive('bgp')}" data-filter="bgp">BGP</button>
                <button class="xray-opt-btn xray-filter-btn${filterActive('ospf')}" data-filter="ospf">OSPF</button>
                <button class="xray-opt-btn xray-filter-btn${filterActive('isis')}" data-filter="isis">ISIS</button>
                <button class="xray-opt-btn xray-filter-btn${filterActive('ldp')}" data-filter="ldp">LDP</button>
                <button class="xray-opt-btn xray-filter-btn${filterActive('lldp')}" data-filter="lldp">LLDP</button>
                <button class="xray-opt-btn xray-filter-btn${filterActive('bfd')}" data-filter="bfd">BFD</button>
            </div>
            </div>
            <div class="xray-toggle-row" id="xray-internal-row" style="display: ${st.mode === 'cp' ? 'flex' : 'none'};">
                <input type="checkbox" id="xray-internal-toggle" ${st.excludeInternal ? 'checked' : ''} />
                <label for="xray-internal-toggle" style="cursor:pointer;">Exclude DNOS internal traffic</label>
            </div>
            <div id="xray-filter-hint" style="display:none; font-size:9px; color:#FF9500; margin-bottom:6px; padding:2px 4px;"></div>
            <div class="xray-toggle-row" id="xray-live-filter-row" style="display: ${hasLinkContext ? 'flex' : 'none'}; flex-direction: column; align-items: stretch; gap: 4px;">
                <div id="xray-link-context-summary" style="font-size:9px; color:${isDark ? '#7ecfff' : '#0066FA'};"></div>
                <label style="display:flex; align-items:center; gap:6px; cursor:pointer;">
                    <input type="checkbox" id="xray-link-context-toggle" ${hasLinkContext ? 'checked' : ''} ${hasLinkContext ? '' : 'disabled'} />
                    Use selected POV interface
                </label>
                <label style="display:flex; align-items:center; gap:6px; cursor:pointer;">
                    <input type="checkbox" id="xray-auto-vlan-toggle" ${st.autoVlanFilter ? 'checked' : ''} ${srcRow ? '' : 'disabled'} />
                    <span id="xray-auto-vlan-label">Auto VLAN filter</span>
                </label>
                <label style="display:flex; align-items:center; gap:6px; cursor:pointer;">
                    <input type="checkbox" id="xray-auto-ip-toggle" ${st.autoIpFilter ? 'checked' : ''} ${srcRow ? '' : 'disabled'} />
                    Auto IP filter
                </label>
            </div>

            <div id="xray-output-pov-row" style="margin-bottom: 10px;">
                <div id="xray-output-section">
            <div class="xray-section-label">Output</div>
                    <div style="display: flex; gap: 3px;">
                        <button class="xray-opt-btn${outActive('mac')}" data-out="mac" title="SCP to Mac + open Wireshark">Mac</button>
                        <button class="xray-opt-btn${outActive('pcap')}" data-out="pcap" title="Save pcap on server">pcap</button>
                        <button class="xray-opt-btn${outActive('auto')}" data-out="auto" title="Full analysis + report">auto</button>
                    </div>
                </div>
            </div>

            <div class="xray-toggle-row" id="xray-cleanup-row" style="display: ${st.output === 'mac' ? 'flex' : 'none'};">
                <input type="checkbox" id="xray-cleanup-toggle" checked />
                <label for="xray-cleanup-toggle" style="cursor:pointer;">Delete server pcap after Mac delivery</label>
            </div>

            <div id="xray-ssh-prompt" style="display: none; margin-bottom: 14px; padding: 10px; background: ${isDark ? 'rgba(231,76,60,0.1)' : 'rgba(231,76,60,0.08)'}; border-radius: 8px; border: 1px solid rgba(231,76,60,0.3);">
                <div class="xray-section-label" style="color: #e74c3c;">Device has no SSH. Enter credentials:</div>
                <input type="text" id="xray-ssh-host" placeholder="Host IP" autocomplete="off" style="width:100%;padding:6px 8px;margin-bottom:6px;border-radius:4px;font-size:12px;box-sizing:border-box;background:rgba(0,0,0,0.2);border:1px solid rgba(255,255,255,0.2);color:inherit;" />
                <input type="text" id="xray-ssh-user" placeholder="User (dnroot)" autocomplete="off" style="width:100%;padding:6px 8px;margin-bottom:6px;border-radius:4px;font-size:12px;box-sizing:border-box;background:rgba(0,0,0,0.2);border:1px solid rgba(255,255,255,0.2);color:inherit;" />
                <input type="password" id="xray-ssh-pass" placeholder="Password" autocomplete="new-password" data-lpignore="true" data-1p-ignore="true" style="width:100%;padding:6px 8px;border-radius:4px;font-size:12px;box-sizing:border-box;background:rgba(0,0,0,0.2);border:1px solid rgba(255,255,255,0.2);color:inherit;" />
            </div>

            <button class="xray-start-btn" id="xray-start-btn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="vertical-align: -2px; margin-right: 4px;"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/></svg>
                Start Capture
            </button>

            <div class="xray-status" id="xray-status" style="background: ${isDark ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.05)'}; color: ${isDark ? '#aaa' : '#555'};"></div>
        `;

        // Keyboard isolation: prevent key events from reaching the global editor handler
        popup.addEventListener('keydown', (e) => { e.stopPropagation(); });
        popup.addEventListener('keyup', (e) => { e.stopPropagation(); });
        
        document.body.appendChild(popup);
        this._popup = popup;
        this._state = st;
        this._ensureMacVerifyListener();

        const isReopeningActiveCapture = this._activeCapture && editor._xrayCapturing === link.id;

        const updateSshPromptVisibility = () => {
            const isPov1 = this._state.pov === 'device1';
            const dev = isPov1 ? device1 : device2;
            const sshPrompt = popup.querySelector('#xray-ssh-prompt');
            if (sshPrompt) {
                const hasSsh = dev?.sshConfig?.host || dev?.deviceAddress;
                sshPrompt.style.display = hasSsh ? 'none' : 'block';
                if (sshPrompt.style.display === 'block') {
                    const hostInput = popup.querySelector('#xray-ssh-host');
                    const userInput = popup.querySelector('#xray-ssh-user');
                    if (hostInput && !hostInput.value && dev?.label && /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(dev.label)) hostInput.value = dev.label;
                    if (userInput && !userInput.value) userInput.placeholder = 'User (dnroot)';
                }
            }
        };
        updateSshPromptVisibility();

        // Measure invisible, place correctly, then reveal with animation
        this._anchorCenter = anchorCenter;
        this._screenPos = screenPos;
        requestAnimationFrame(() => {
            this._positionPopup(popup, screenPos, anchorCenter, toolbarGap);
            popup.style.visibility = '';
            popup.style.animation = 'xrayPopupFadeIn 0.15s ease';
        });

        // Mode buttons
        const applyModeUi = (mode) => {
            const isDP = mode === 'dp';
            const isCp = mode === 'cp';
            const durDirRow = popup.querySelector('#xray-dur-dir-row');
            const filtersSection = popup.querySelector('#xray-filters-section');
            const internalRow = popup.querySelector('#xray-internal-row');
            const filterHint = popup.querySelector('#xray-filter-hint');
            const outputSection = popup.querySelector('#xray-output-section');
            const cleanupRow = popup.querySelector('#xray-cleanup-row');
            const startBtn = popup.querySelector('#xray-start-btn');
            const intfRow = popup.querySelector('#xray-intf-picker-row');
            if (durDirRow) durDirRow.style.display = isDP ? 'none' : 'flex';
            if (filtersSection) filtersSection.style.display = '';
            if (internalRow) internalRow.style.display = isCp ? 'flex' : 'none';
            if (filterHint) {
                if (isDP) {
                    filterHint.textContent = 'BPF filter applied on Arista SPAN session';
                    filterHint.style.display = '';
                } else {
                    filterHint.textContent = '';
                    filterHint.style.display = 'none';
                }
            }
            if (outputSection) outputSection.style.display = isDP ? 'none' : '';
            if (cleanupRow) cleanupRow.style.display = isDP ? 'none' : cleanupRow.style.display;
            if (startBtn) startBtn.textContent = isDP ? 'Start Live Stream' : 'Start Capture';
            if (intfRow) intfRow.style.display = (isDP && this._aristaInfo) ? '' : 'none';
        };
        popup.querySelectorAll('.xray-mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                if (btn.disabled) return;
                popup.querySelectorAll('.xray-mode-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this._state.mode = btn.dataset.mode;
                applyModeUi(btn.dataset.mode);
                updateLinkContextUi();
                this._evaluateMacGate();
            });
        });
        // Disabled mode buttons swallow native click events, so users can't
        // tell *why* DP / DP (DNAAS) is unavailable. Catch the click on the
        // mode-row container and, if the click landed on a disabled mode
        // button, surface the reason in a toast + expand the mode hint area.
        const modeRow = popup.querySelector('.xray-mode-btn')?.parentElement;
        if (modeRow) {
            modeRow.addEventListener('click', (ev) => {
                const btn = ev.target.closest('.xray-mode-btn');
                if (!btn || !btn.disabled) return;
                ev.preventDefault();
                ev.stopPropagation();
                this._explainDisabledMode(btn);
            }, true);
        }
        applyModeUi(this._state.mode);
        // Duration buttons
        popup.querySelectorAll('.xray-opt-btn[data-dur]').forEach(btn => {
            btn.addEventListener('click', () => {
                popup.querySelectorAll('.xray-opt-btn[data-dur]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this._state.duration = parseInt(btn.dataset.dur);
            });
        });
        // Output buttons
        const cleanupRow = popup.querySelector('#xray-cleanup-row');
        popup.querySelectorAll('.xray-opt-btn[data-out]').forEach(btn => {
            btn.addEventListener('click', () => {
                popup.querySelectorAll('.xray-opt-btn[data-out]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this._state.output = btn.dataset.out;
                if (cleanupRow) cleanupRow.style.display = btn.dataset.out === 'mac' ? 'flex' : 'none';
                this._evaluateMacGate();
            });
        });
        const L2_PROTOCOLS = ['isis', 'lldp'];
        const filterHint = popup.querySelector('#xray-filter-hint');
        const updateFilterHint = () => {
            if (!filterHint) return;
            const dir = this._state.direction;
            const filters = this._state.filters;
            const hasL2Only = filters.length > 0 && filters.every(f => L2_PROTOCOLS.includes(f));
            if (hasL2Only && dir !== 'both') {
                const names = filters.map(f => f.toUpperCase()).join(', ');
                filterHint.textContent = `${names} is L2 -- direction filter will be ignored (no IP headers)`;
                filterHint.style.display = 'block';
            } else {
                filterHint.style.display = 'none';
            }
        };
        // Direction buttons
        popup.querySelectorAll('.xray-opt-btn[data-dir]').forEach(btn => {
            btn.addEventListener('click', () => {
                popup.querySelectorAll('.xray-opt-btn[data-dir]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this._state.direction = btn.dataset.dir;
                updateFilterHint();
                updateLinkContextUi();
            });
        });
        const linkCtxToggle = popup.querySelector('#xray-link-context-toggle');
        const autoVlanToggle = popup.querySelector('#xray-auto-vlan-toggle');
        const autoIpToggle = popup.querySelector('#xray-auto-ip-toggle');
        const linkCtxSummary = popup.querySelector('#xray-link-context-summary');
        const autoVlanLabel = popup.querySelector('#xray-auto-vlan-label');
        const activeSrcRow = () => {
            const rows = this._state.srcRows || {};
            const row = this._state.pov === 'device2'
                ? (rows.device2 || rows.B)
                : (rows.device1 || rows.A);
            return row || this._state.srcRow || {};
        };
        const resolveCaptureInterface = () => {
            const row = activeSrcRow();
            const rowSide = row.side === 'B' ? 'device2' : (row.side === 'A' ? 'device1' : '');
            const isPov1Now = this._state.pov === 'device1';
            if (this._state.useLinkContext && rowSide === this._state.pov && row.ifName) {
                return this._state.mode === 'dp' ? (row.parent || row.ifName) : row.ifName;
            }
            return isPov1Now
                ? (this._link?.device1Interface || this._link?.linkDetails?.interfaceA || '')
                : (this._link?.device2Interface || this._link?.linkDetails?.interfaceB || '');
        };
        const updateLinkContextUi = () => {
            const row = activeSrcRow();
            this._state.srcRow = row.ifName ? row : (this._state.srcRow || null);
            const enabled = !!this._state.useLinkContext && !!row.ifName;
            const rowSide = row.side === 'B' ? 'device2' : (row.side === 'A' ? 'device1' : '');
            const rowMatchesPov = enabled && rowSide === this._state.pov;
            const captureIntf = resolveCaptureInterface();
            const subInterfaceCapture = enabled && /\.\d+/.test(captureIntf || '');
            if (autoVlanToggle) autoVlanToggle.disabled = !enabled || !rowMatchesPov;
            if (autoIpToggle) autoIpToggle.disabled = !enabled || !rowMatchesPov;
            if (autoVlanLabel) {
                autoVlanLabel.textContent = subInterfaceCapture
                    ? 'Auto VLAN filter (shown only - sub-interface capture)'
                    : 'Auto VLAN filter';
                autoVlanLabel.style.opacity = subInterfaceCapture || !rowMatchesPov ? '0.68' : '';
            }
            if (linkCtxSummary) {
                const side = row.side === 'B' ? 'Side B' : 'Side A';
                const direction = this._state.direction || 'both';
                linkCtxSummary.innerHTML = '';
                if (enabled) {
                    const pill = document.createElement('span');
                    pill.className = 'xray-selected-interface-pill';
                    pill.textContent = captureIntf || row.ifName || 'any';
                    linkCtxSummary.appendChild(document.createTextNode(`Selected link: ${side} `));
                    linkCtxSummary.appendChild(pill);
                    linkCtxSummary.appendChild(document.createTextNode(
                        ` direction=${direction}${row.vlanOuter ? ' vlan ' + row.vlanOuter : ''}${row.ip ? ' ip ' + row.ip : ''}`
                    ));
                    if (subInterfaceCapture && row.vlanOuter) {
                        linkCtxSummary.appendChild(document.createElement('br'));
                        linkCtxSummary.appendChild(document.createTextNode('VLAN tag is not added to BPF because capture is already on the VLAN sub-interface.'));
                    }
                    if (!rowMatchesPov) {
                        linkCtxSummary.appendChild(document.createElement('br'));
                        linkCtxSummary.appendChild(document.createTextNode('Selected row is not the active POV; VLAN/IP filters are suppressed so the capture follows the interface shown above.'));
                    }
                } else {
                    linkCtxSummary.textContent = 'Selected link ignored: general device capture';
                }
            }
        };
        if (linkCtxToggle) {
            linkCtxToggle.addEventListener('change', () => {
                this._state.useLinkContext = linkCtxToggle.checked;
                updateLinkContextUi();
            });
        }
        if (autoVlanToggle) {
            autoVlanToggle.addEventListener('change', () => {
                this._state.autoVlanFilter = autoVlanToggle.checked;
            });
        }
        if (autoIpToggle) {
            autoIpToggle.addEventListener('change', () => {
                this._state.autoIpFilter = autoIpToggle.checked;
            });
        }
        updateLinkContextUi();
        // Protocol filter buttons (multi-select)
        popup.querySelectorAll('.xray-filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const f = btn.dataset.filter;
                const idx = this._state.filters.indexOf(f);
                if (idx >= 0) {
                    this._state.filters.splice(idx, 1);
                    btn.classList.remove('active');
                } else {
                    this._state.filters.push(f);
                    btn.classList.add('active');
                }
                updateFilterHint();
            });
        });
        // Internal traffic exclusion toggle
        const internalToggle = popup.querySelector('#xray-internal-toggle');
        if (internalToggle) {
            internalToggle.addEventListener('change', () => {
                this._state.excludeInternal = internalToggle.checked;
            });
        }
        // POV header buttons -- re-run Arista/DNAAS detection when POV changes
        const activeBg = 'linear-gradient(135deg, #0066FA, #0052CC)';
        const inactiveBg = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)';
        const activeColor = '#fff';
        const inactiveColor = isDark ? '#b8c0cc' : '#555';
        // Disable any POV button whose endpoint is a DNAAS fabric device
        // (cp/dp tcpdump cannot SSH a DNOS shell on a leaf -- use the
        // dnaas-dp mode if you actually want a DNAAS capture). Show a
        // tooltip + reduce opacity so the user understands why the click
        // is rejected. Block POV-flip clicks at the listener level so a
        // direct DOM "click" event can't bypass the disabled attribute.
        popup.querySelectorAll('.xray-pov-btn').forEach(btn => {
            const isDnaasBtn = (btn.dataset.pov === 'device1' && dev1IsDnaas)
                || (btn.dataset.pov === 'device2' && dev2IsDnaas);
            if (isDnaasBtn) {
                btn.disabled = true;
                btn.dataset.dnaasBlocked = '1';
                btn.style.opacity = '0.5';
                btn.style.cursor = 'not-allowed';
                btn.title = 'DNAAS fabric device cannot be a CP/DP capture POV. '
                    + 'Use DP (DNAAS) mode if you need a leaf-mirror capture, '
                    + 'or pick the other endpoint as POV.';
            }
            btn.addEventListener('click', () => {
                if (btn.disabled || btn.dataset.dnaasBlocked === '1') {
                    if (editor && editor.showToast) {
                        editor.showToast(
                            `${btn.textContent.trim().split(/\s+/)[0]} is a DNAAS device -- pick the other endpoint or switch to DP (DNAAS) mode.`,
                            'warning'
                        );
                    }
                    return;
                }
                popup.querySelectorAll('.xray-pov-btn').forEach(b => {
                    b.classList.remove('active');
                    b.style.background = inactiveBg;
                    b.style.color = inactiveColor;
                });
                btn.classList.add('active');
                btn.style.background = activeBg;
                btn.style.color = activeColor;
                this._state.pov = btn.dataset.pov;
                const nextRow = activeSrcRow();
                this._state.srcRow = nextRow.ifName ? nextRow : null;
                updateSshPromptVisibility();
                updateLinkContextUi();
                if (this._lldpCache) {
                    this._applyDetectionForPov();
                    applyModeUi(this._state.mode);
                }
            });
        });

        // Both endpoints are DNAAS -> nothing reasonable to capture.
        // Disable Start, swap status to a clear message, point the user
        // at DP (DNAAS) mode (which doesn't use the POV concept).
        if (dev1IsDnaas && dev2IsDnaas) {
            const startBtn = popup.querySelector('#xray-start-btn');
            const statusEl = popup.querySelector('#xray-status');
            if (startBtn) {
                startBtn.disabled = true;
                startBtn.title = 'Both endpoints are DNAAS fabric devices -- '
                    + 'use DP (DNAAS) mode (no POV needed) or pick a link '
                    + 'with at least one non-DNAAS endpoint.';
                startBtn.dataset.dnaasBothPovBlocked = '1';
            }
            if (statusEl) {
                statusEl.style.display = 'block';
                statusEl.style.background = 'rgba(255,165,0,0.12)';
                statusEl.style.color = '#FF9500';
                statusEl.textContent = 'Both endpoints are DNAAS fabric devices. '
                    + 'CP/DP capture is not supported on DNAAS leaves -- '
                    + 'switch to DP (DNAAS) mode.';
            }
        }
        // Close
        popup.querySelector('#xray-close-btn').addEventListener('click', () => this.hide());
        // Start
        popup.querySelector('#xray-start-btn').addEventListener('click', () => this._startCapture());

        if (isReopeningActiveCapture) {
            const btn = popup.querySelector('#xray-start-btn');
            const status = popup.querySelector('#xray-status');
            if (btn) {
                btn.classList.add('capturing');
                btn.disabled = false;
            }
            if (status) {
                status.style.display = 'block';
                status.style.background = 'rgba(0,102,250,0.1)';
                status.style.color = '#0066FA';
            }
            if (this._captureStart && this._captureDuration && btn && status) {
                this._updateCountdown(btn, status);
                if (this._countdownTimer) clearInterval(this._countdownTimer);
                this._countdownTimer = setInterval(() => this._updateCountdown(btn, status), 500);
            }
        }
        // Prevent canvas interactions
        popup.addEventListener('mousedown', e => e.stopPropagation());
        popup.addEventListener('click', e => e.stopPropagation());
        // Close on outside click -- but not during panning (temporaryHide already ran)
        this._outsideHandler = (e) => {
            if (!popup.contains(e.target)) {
                const linkTb = document.getElementById('link-selection-toolbar');
                if (linkTb && linkTb.contains(e.target)) return;
                if (this._temporarilyHidden) return;
                this.hide();
            }
        };
        setTimeout(() => document.addEventListener('mousedown', this._outsideHandler), 100);

        this._detectModes(editor, link, name1, name2);
        // Gate Start Capture on Mac verification (runs async; safe to fire-and-forget)
        if (!isReopeningActiveCapture) {
            this._evaluateMacGate();
        }
        editor.draw();
    },

    hide() {
        if (this._link) {
            this._link._xrayCaptureActive = false;
            if (this._editor) this._editor.draw();
        }
        if (this._state) {
            this._lastState = { ...this._state, filters: [...(this._state.filters || [])] };
        }
        if (this._popup) {
            this._popup.remove();
            this._popup = null;
        }
        this._temporarilyHidden = false;
        if (this._outsideHandler) {
            document.removeEventListener('mousedown', this._outsideHandler);
            this._outsideHandler = null;
        }
        if (this._activeCapture && this._pollTimer) {
            // Capture running -- keep poll timer alive, show toast on completion
        } else if (this._pollTimer) {
            clearInterval(this._pollTimer);
            this._pollTimer = null;
        }
        if (this._countdownTimer && !this._activeCapture) {
            clearInterval(this._countdownTimer);
            this._countdownTimer = null;
        }
    },

    temporaryHide() {
        if (this._popup && !this._temporarilyHidden) {
            this._popup.style.display = 'none';
            this._temporarilyHidden = true;
        }
    },

    temporaryShow() {
        if (!this._popup || !this._temporarilyHidden || !this._link || !this._editor) return;
        const editor = this._editor;
        const link = this._link;

        if (editor.showLinkSelectionToolbar) {
            editor.showLinkSelectionToolbar(link);
        }

        const linkTb = document.getElementById('link-selection-toolbar');
        if (linkTb) {
            const tbRect = linkTb.getBoundingClientRect();
            const pos = { x: tbRect.left + tbRect.width / 2, y: tbRect.bottom, anchor: 'center' };
            this._positionPopup(this._popup, pos, true, 6);
        }

        this._popup.style.display = '';
        this._temporarilyHidden = false;
    },

    _positionPopup(popup, screenPos, anchorCenter, gap) {
        const r = popup.getBoundingClientRect();
        const vw = window.innerWidth;
        const vh = window.innerHeight;

        // Horizontal: center on anchor, clamp to viewport
        let left = screenPos.x;
        if (anchorCenter) {
            const halfW = r.width / 2;
            if (left - halfW < 10) left = 10 + halfW;
            if (left + halfW > vw - 10) left = vw - 10 - halfW;
            popup.style.left = left + 'px';
            popup.style.transform = 'translateX(-50%)';
        } else {
            if (left + r.width > vw - 10) left = vw - r.width - 10;
            if (left < 10) left = 10;
            popup.style.left = left + 'px';
        }

        // Vertical: prefer ABOVE toolbar so it doesn't cover the selected link
        // (link toolbar sits at the link midpoint; the link extends below it)
        const linkTb = document.getElementById('link-selection-toolbar');
        const tbTop = linkTb ? linkTb.getBoundingClientRect().top : screenPos.y;
        const spaceAbove = tbTop - gap;
        const spaceBelow = vh - screenPos.y - gap;

        if (r.height <= spaceAbove - 10) {
            popup.style.top = (tbTop - r.height - gap) + 'px';
            popup.classList.add('above');
        } else if (r.height <= spaceBelow - 10) {
            popup.style.top = (screenPos.y + gap) + 'px';
            popup.classList.remove('above');
        } else {
            // Not enough space either way -- clamp above with scroll
            popup.style.top = Math.max(10, tbTop - r.height - gap) + 'px';
            popup.classList.add('above');
        }
    },

    _isArista(neighbor) {
        if (this._isDnaas(neighbor)) return false;
        const name = this._neighborName(neighbor).toLowerCase();
        const port = this._neighborRemotePort(neighbor).toLowerCase();
        if (/arista|eos|veos/.test(name)) return true;
        if (port.startsWith('ethernet')) return true;
        return false;
    },

    _isDnaas(neighbor) {
        const name = this._neighborName(neighbor).toUpperCase();
        const remote = this._neighborRemotePort(neighbor).toUpperCase();
        if (/ARISTA|EOS|VEOS/.test(name)) return false;
        if (/DN[-_]?LEAF|DN[-_]?SPINE|DNAAS/.test(name)) return true;
        return this._DNAAS_POV_KEYWORDS.some(kw => name.includes(kw) || remote.includes(kw));
    },

    _neighborName(neighbor) {
        return String(neighbor?.neighbor
            || neighbor?.neighbor_name
            || neighbor?.neighbor_device
            || neighbor?.neighbor_system_name
            || neighbor?.remote_device
            || neighbor?.remote_system_name
            || neighbor?.remote_host
            || neighbor?.system_name
            || neighbor?.hostname
            || neighbor?.device
            || '');
    },

    _neighborLocalInterface(neighbor) {
        return String(neighbor?.interface
            || neighbor?.local
            || neighbor?.local_interface
            || neighbor?.local_port
            || neighbor?.local_port_id
            || neighbor?.port_id
            || '');
    },

    _neighborRemotePort(neighbor) {
        return String(neighbor?.remote_port
            || neighbor?.remote
            || neighbor?.neighbor_port
            || neighbor?.neighbor_interface
            || neighbor?.remote_interface
            || neighbor?.remote_port_id
            || neighbor?.remote_if
            || neighbor?.port
            || '');
    },

    _interfaceBase(name) {
        return String(name || '').split('.')[0].trim();
    },

    _interfaceMatches(a, b) {
        const aa = String(a || '').trim();
        const bb = String(b || '').trim();
        if (!aa || !bb) return false;
        return aa === bb || this._interfaceBase(aa) === this._interfaceBase(bb);
    },

    _cachedLldpForDevice(device) {
        const candidates = [
            device?._lldpData?.neighbors,
            device?._lldpData?.lldp_neighbors,
            device?._monitorContext?.lldp,
            device?._lldp,
            device?.lldp,
            device?.lldp_neighbors
        ];
        for (const list of candidates) {
            if (Array.isArray(list) && list.length) {
                return list.filter(n => this._neighborName(n) && this._neighborRemotePort(n));
            }
        }
        return [];
    },

    _lldpDeviceCache: {},

    _setButtonHint(button, text) {
        if (!button) return;
        button.setAttribute('aria-label', text || '');
        button.removeAttribute('title');
    },

    // Tell the user *exactly* why a disabled DP / DP (DNAAS) mode button
    // can't be selected. Builds the reason from the same evidence the
    // detection code uses (`_aristaInfo`, `_dnaasInfo`, mirror preflight
    // cache) so the on-screen explanation matches reality.
    _explainDisabledMode(btn) {
        const editor = this._editor;
        const mode = btn?.dataset?.mode;
        const reasons = [];
        let title = 'Mode unavailable';
        if (mode === 'dp') {
            title = 'Live Capture (DP) unavailable';
            const isPov1 = this._state?.pov === 'device1';
            const cache = this._lldpCache || {};
            const povNeighbors = isPov1 ? (cache.device1 || []) : (cache.device2 || []);
            const otherNeighbors = isPov1 ? (cache.device2 || []) : (cache.device1 || []);
            const otherHasArista = otherNeighbors.some(n => this._isArista(n));
            if (!povNeighbors.length) {
                reasons.push('No LLDP neighbors visible for the selected POV (DP needs LLDP).');
            } else {
                reasons.push(`No Arista switch in this POV's LLDP (${povNeighbors.length} neighbor${povNeighbors.length === 1 ? '' : 's'} present).`);
            }
            if (otherHasArista) {
                reasons.push('Arista IS visible from the other endpoint -- click that POV header to switch sides.');
            } else {
                reasons.push('Connect an Arista switch to one of the endpoints, or refresh LLDP if you just rewired.');
            }
        } else if (mode === 'dnaas-dp') {
            title = 'DP (DNAAS) unavailable';
            const dnaas = this._dnaasInfo;
            const preflight = dnaas?.mirrorPreflight;
            if (!dnaas) {
                const isPov1 = this._state?.pov === 'device1';
                const cache = this._lldpCache || {};
                const povNeighbors = isPov1 ? (cache.device1 || []) : (cache.device2 || []);
                const dnaasNeighbors = povNeighbors.filter(n => this._isDnaas(n));
                if (!dnaasNeighbors.length) {
                    reasons.push('No DNAAS leaf (DN-LEAF / DN-SPINE) seen in this POV\'s LLDP.');
                    reasons.push('DNAAS-DP needs the POV device to be wired to a DNAAS leaf.');
                } else if (dnaasNeighbors.length > 1) {
                    reasons.push('Multiple DNAAS leaf neighbors found.');
                    reasons.push('Pick a specific DNAAS-facing link/interface in the link table so XRAY knows which leaf to mirror from.');
                } else {
                    const ifs = dnaasNeighbors.map(n => this._neighborLocalInterface(n)).filter(Boolean).join(', ');
                    reasons.push(`Selected POV interface is not on the DNAAS-facing port (DNAAS interfaces: ${ifs || 'unknown'}).`);
                }
            } else if (preflight?.checking) {
                reasons.push(`Still verifying that DNAAS leaf ${dnaas.leafHost} has a free mirror destination...`);
                reasons.push('This usually takes a few seconds; the button enables itself when the check passes.');
            } else if (preflight && !preflight.available) {
                const why = preflight.reason || preflight.error || 'no free mirror port reported';
                reasons.push(`DNAAS mirror preflight refused the leaf: ${why}.`);
                if (preflight.in_use) {
                    reasons.push(`Leaf reports mirror sessions in use: ${preflight.in_use}`);
                }
            } else {
                reasons.push('DP (DNAAS) prerequisites not yet confirmed -- try Refresh LLDP and reopen the popup.');
            }
        }
        const reasonText = reasons.length ? reasons.join(' ') : 'No additional details available.';
        if (editor && typeof editor.showToast === 'function') {
            editor.showToast(`${title} -- ${reasonText}`, 'warning');
        }
        const hintEl = this._popup?.querySelector('#xray-mode-hint');
        if (hintEl) {
            hintEl.textContent = `${title}: ${reasonText}`;
            hintEl.style.color = '#FF9500';
        }
        try { btn.animate?.([
            { transform: 'translateX(0)' },
            { transform: 'translateX(-3px)' },
            { transform: 'translateX(3px)' },
            { transform: 'translateX(0)' }
        ], { duration: 220 }); } catch (_) {}
    },

    _deviceLookupCandidates(device) {
        return [...new Set([
            device?._registeredDeviceId,
            device?._registeredHostname,
            device?.label,
            device?.name,
            device?.hostname,
            device?.device_id,
            device?.deviceSerial,
            device?.serial,
            device?._registeredMgmtIp,
            device?._monitoredKey,
            device?.sshConfig?.host,
            device?.sshConfig?.hostBackup,
            String(device?.deviceAddress || '').includes('@')
                ? String(device.deviceAddress).split('@').pop()
                : device?.deviceAddress
        ].filter(Boolean))];
    },

    _devicePrimaryLabel(device) {
        return String(device?._registeredHostname
            || device?.hostname
            || device?.label
            || device?.name
            || device?.deviceSerial
            || device?.serial
            || '').trim();
    },

    _deviceConnectionHost(device) {
        const address = String(device?.deviceAddress || '').includes('@')
            ? String(device.deviceAddress).split('@').pop()
            : device?.deviceAddress;
        return String(device?._registeredMgmtIp
            || device?.sshConfig?.host
            || device?.sshConfig?.hostBackup
            || address
            || this._devicePrimaryLabel(device)
            || '').trim();
    },

    _linkDnaasEndpoint(isPov1, link, povInterface) {
        const dnaasDevice = isPov1 ? this._device2 : this._device1;
        if (!this._isDnaasPov(dnaasDevice)) return null;
        const dnaasInterface = isPov1
            ? (link.device2Interface || link.linkDetails?.interfaceB || '')
            : (link.device1Interface || link.linkDetails?.interfaceA || '');
        if (!dnaasInterface) return null;
        return {
            leafHost: this._deviceConnectionHost(dnaasDevice),
            leafLabel: this._devicePrimaryLabel(dnaasDevice),
            sourcePort: dnaasInterface,
            dutInterface: povInterface || '',
            source: 'canvas-link'
        };
    },

    _linkDnaasEndpointForNeighbor(isPov1, link, neighbor) {
        const endpoint = this._linkDnaasEndpoint(isPov1, link, this._neighborLocalInterface(neighbor));
        if (!endpoint) return null;
        const neighborName = this._neighborName(neighbor).toLowerCase();
        const endpointLabel = endpoint.leafLabel.toLowerCase();
        if (!neighborName || !endpointLabel) return endpoint;
        const clean = s => String(s || '').replace(/[^a-z0-9]/g, '');
        return clean(neighborName) === clean(endpointLabel)
            || clean(endpointLabel).includes(clean(neighborName))
            || clean(neighborName).includes(clean(endpointLabel))
            ? endpoint
            : null;
    },

    _normalizeContextLldp(list) {
        if (!Array.isArray(list)) return [];
        return list.map(n => ({
            ...n,
            local: n.local || n.local_interface || n.interface || n.local_port || n.local_port_id || n.port_id || '',
            neighbor: n.neighbor || n.neighbor_name || n.neighbor_device || n.neighbor_system_name || n.remote_device || n.remote_system_name || n.remote_host || n.system_name || n.hostname || n.device || '',
            remote: n.remote || n.neighbor_interface || n.neighbor_port || n.remote_port || n.remote_interface || n.remote_port_id || n.remote_if || n.port || ''
        })).filter(n => this._neighborName(n) && this._neighborRemotePort(n));
    },

    async _fetchMonitorContext(device, signal) {
        const candidates = this._deviceLookupCandidates(device);
        const sshHost = device?.sshConfig?.host || device?.sshConfig?.hostBackup || '';
        for (const name of candidates) {
            if (signal?.aborted) return null;
            try {
                const ctrl = new AbortController();
                const timer = setTimeout(() => ctrl.abort(), 18000);
                if (signal) signal.addEventListener('abort', () => ctrl.abort(), { once: true });
                const url = new URL(`/api/devices/${encodeURIComponent(name)}/context`, window.location.origin);
                url.searchParams.set('live', 'true');
                if (sshHost && /^\d+\.\d+\.\d+\.\d+$/.test(sshHost)) {
                    url.searchParams.set('ssh_host', sshHost);
                }
                const resp = await _xrayAuthFetch(url.toString(), { signal: ctrl.signal });
                clearTimeout(timer);
                if (!resp.ok) continue;
                const ctx = await resp.json();
                if (ctx && typeof ctx === 'object') {
                    device._monitorContext = ctx;
                    return ctx;
                }
            } catch (_) {}
        }
        return null;
    },

    _fastLldpForDevice(device) {
        const unique = this._deviceLookupCandidates(device);
        const cacheKey = unique.join('|');
        if (this._lldpDeviceCache[cacheKey]) {
            console.log('[XRAY lldp] Cache hit for', cacheKey);
            return this._lldpDeviceCache[cacheKey];
        }
        const monitorNeighbors = this._normalizeContextLldp(device?._monitorContext?.lldp || device?._monitorContext?.lldp_neighbors || []);
        if (monitorNeighbors.length > 0) {
            this._lldpDeviceCache[cacheKey] = monitorNeighbors;
            console.log('[XRAY lldp] Using cached monitor context for', device?.label || device?.deviceSerial || device?.sshConfig?.host, monitorNeighbors);
            return monitorNeighbors;
        }
        const cached = this._cachedLldpForDevice(device);
        if (cached.length) {
            console.log('[XRAY lldp] Using canvas cache for', device?.label || device?.deviceSerial || device?.sshConfig?.host, cached);
            return cached;
        }
        return [];
    },

    async _fetchLldpForDevice(device, signal, opts) {
        opts = opts || {};
        if (!opts.live) {
            return this._fastLldpForDevice(device);
        }
        const unique = this._deviceLookupCandidates(device);
        const cacheKey = unique.join('|');
        const ctx = await this._fetchMonitorContext(device, signal);
        const monitorNeighbors = this._normalizeContextLldp(ctx?.lldp || ctx?.lldp_neighbors || []);
        if (monitorNeighbors.length > 0) {
            this._lldpDeviceCache[cacheKey] = monitorNeighbors;
            console.log('[XRAY lldp] Using scaler monitor context for', device?.label || device?.deviceSerial || device?.sshConfig?.host, monitorNeighbors);
            return monitorNeighbors;
        }
        return this._fastLldpForDevice(device);
    },

    _dnaasPreflightKey(info) {
        if (!info) return '';
        return `${info.leafHost || ''}|${info.sourcePort || ''}|${info.dutInterface || ''}`;
    },

    async _refreshDnaasMirrorPreflight(info, key) {
        if (!info?.leafHost || !key) return;
        if (this._dnaasMirrorPreflightCache[key]?.checking) return;
        this._dnaasMirrorPreflightCache[key] = { checking: true };
        try {
            const ctrl = new AbortController();
            const timer = setTimeout(() => ctrl.abort(), 22000);
            const resp = await _xrayAuthFetch('/api/xray/dnaas-mirror-preflight', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    leaf_host: info.leafHost,
                    leaf_label: info.leafLabel || info.leafHost,
                    dnaas_leaf_source_port: info.sourcePort || '',
                    dut_interface: info.dutInterface || ''
                }),
                signal: ctrl.signal
            }).finally(() => clearTimeout(timer));
            let body = {};
            try { body = await resp.json(); } catch (_) {}
            if (!resp.ok && !body.error && !body.reason) {
                body.error = `HTTP ${resp.status}`;
            }
            this._dnaasMirrorPreflightCache[key] = body;
        } catch (e) {
            this._dnaasMirrorPreflightCache[key] = {
                available: false,
                error: e.name === 'AbortError'
                    ? 'DNAAS mirror preflight timed out'
                    : (e.message || 'DNAAS mirror preflight failed')
            };
        }
        if (this._popup && this._dnaasMirrorPreflightKey === key) {
            this._applyDetectionForPov();
        }
    },

    async _fetchDeviceInterfaces(isPov1, aristaNeighbor) {
        const intfSelect = this._popup?.querySelector('#xray-intf-select');
        const intfLoading = this._popup?.querySelector('#xray-intf-loading');
        const intfInfo = this._popup?.querySelector('#xray-intf-info');
        if (!intfSelect || !intfLoading) return;
        intfLoading.style.display = '';
        intfSelect.style.display = 'none';
        if (intfInfo) intfInfo.textContent = 'No interface in link table';

        const device = isPov1 ? this._device1 : this._device2;
        let interfaces = [];
        const ctx = device?._monitorContext || await this._fetchMonitorContext(device);
        const ctxIfaces = ctx?.interfaces || {};
        for (const key of ['physical', 'bundle', 'subinterface', 'free_physical']) {
            const rows = Array.isArray(ctxIfaces[key]) ? ctxIfaces[key] : [];
            interfaces.push(...rows.map(row => typeof row === 'string' ? row : (row.name || row.interface || '')).filter(Boolean));
        }
        interfaces = [...new Set(interfaces)];
        intfLoading.style.display = 'none';
        if (interfaces.length === 0) {
            if (intfInfo) intfInfo.textContent = 'Could not fetch interfaces -- enter manually';
            intfSelect.style.display = 'none';
            const existing = this._popup?.querySelector('#xray-intf-manual');
            if (!existing) {
                const input = document.createElement('input');
                input.id = 'xray-intf-manual';
                input.type = 'text';
                input.placeholder = 'e.g. ge100-0/0/1';
                const isDark = document.body.classList.contains('dark-mode');
                input.style.cssText = `width: 100%; padding: 5px 8px; border-radius: 4px; border: 1px solid ${isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)'}; background: ${isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.03)'}; color: ${isDark ? '#c8d0da' : '#333'}; font-size: 10px; font-family: 'Space Grotesk', monospace; outline: none;`;
                input.addEventListener('change', () => {
                    if (this._aristaInfo) this._aristaInfo.dutInterface = input.value.trim();
                });
                intfSelect.parentNode.insertBefore(input, intfSelect.nextSibling);
            }
            return;
        }
        intfSelect.innerHTML = '<option value="">(select interface)</option>';
        for (const intf of interfaces) {
            const name = typeof intf === 'string' ? intf : (intf.name || intf.interface || '');
            if (!name) continue;
            const opt = document.createElement('option');
            opt.value = name;
            opt.textContent = name;
            intfSelect.appendChild(opt);
        }
        intfSelect.style.display = '';
        intfSelect.addEventListener('change', () => {
            if (this._aristaInfo) this._aristaInfo.dutInterface = intfSelect.value;
            if (intfInfo) intfInfo.textContent = intfSelect.value ? `Selected: ${intfSelect.value}` : 'No interface in link table';
        });
    },

    async _detectModes(editor, link, name1, name2) {
        if (this._detectAbort) this._detectAbort.abort();
        const detectCtrl = new AbortController();
        this._detectAbort = detectCtrl;

        const dpBtn = this._popup?.querySelector('.xray-mode-btn[data-mode="dp"]');
        const dnaasBtn = this._popup?.querySelector('.xray-mode-btn[data-mode="dnaas-dp"]');
        const hintEl = this._popup?.querySelector('#xray-mode-hint');
        const setHint = (msg) => { if (hintEl) hintEl.textContent = msg; };

        const device1 = editor.objects.find(d => d.id === link.device1);
        const device2 = editor.objects.find(d => d.id === link.device2);
        console.log('[XRAY detect] Querying LLDP for:', name1, name2,
            'sshHosts:', device1?.sshConfig?.host, device2?.sshConfig?.host,
            'serials:', device1?.deviceSerial, device2?.deviceSerial);

        const neighbors1 = this._fastLldpForDevice(device1);
        const neighbors2 = this._fastLldpForDevice(device2);
        console.log(`[XRAY detect] fast cache: ${neighbors1.length} + ${neighbors2.length} neighbors`);
        this._lldpCache = { device1: neighbors1, device2: neighbors2 };
        this._applyDetectionForPov();
        if (neighbors1.length || neighbors2.length) {
            const currentHint = (hintEl?.textContent || '').trim();
            setHint((currentHint ? currentHint + ' ' : '') + 'Refreshing live...');
        } else {
            setHint('Checking live LLDP from scaler monitor... CP capture is available while this refreshes.');
        }

        const fetchSide = (device, fallback, sideName) => this._fetchLldpForDevice(device, detectCtrl.signal, { live: true })
            .catch((e) => {
                console.warn(`[XRAY detect] ${sideName} live LLDP refresh failed:`, e?.message || e);
                return fallback;
            });
        Promise.all([
            fetchSide(device1, neighbors1, 'device1'),
            fetchSide(device2, neighbors2, 'device2')
        ]).then(([live1, live2]) => {
            if (detectCtrl.signal.aborted || this._detectAbort !== detectCtrl) return;
            console.log(`[XRAY detect] live refresh: ${live1.length} + ${live2.length} neighbors`);
            if (live1.length || live2.length) {
                this._lldpCache = { device1: live1, device2: live2 };
                this._applyDetectionForPov();
                return;
            }
            if (!neighbors1.length && !neighbors2.length) {
                const finalMsg = `No LLDP neighbors discovered for ${name1} / ${name2}. ` +
                    `DP/DNAAS-DP modes need LLDP; CP capture is still available.`;
                setHint(finalMsg);
            }
        }).catch((e) => {
            if (detectCtrl.signal.aborted || this._detectAbort !== detectCtrl) return;
            console.warn('[XRAY detect] live refresh failed:', e?.message || e);
            if (!neighbors1.length && !neighbors2.length) {
                setHint(`Live LLDP refresh failed for ${name1} / ${name2}. CP capture is still available.`);
            }
        });
    },

    _applyDetectionForPov() {
        const dpBtn = this._popup?.querySelector('.xray-mode-btn[data-mode="dp"]');
        const dnaasBtn = this._popup?.querySelector('.xray-mode-btn[data-mode="dnaas-dp"]');
        const hintEl = this._popup?.querySelector('#xray-mode-hint');
        const setHint = (msg) => { if (hintEl) hintEl.textContent = msg; };
        if (!this._lldpCache) return;

        const isPov1 = this._state.pov === 'device1';
        const povNeighbors = isPov1 ? this._lldpCache.device1 : this._lldpCache.device2;
        const link = this._link;
        const selectedPovRow = isPov1
            ? (this._state.srcRows?.device1 || this._state.srcRows?.A)
            : (this._state.srcRows?.device2 || this._state.srcRows?.B);
        const linkIntf = isPov1
            ? ((this._state.useLinkContext && (selectedPovRow?.parent || selectedPovRow?.ifName)) || link.device1Interface || link.linkDetails?.interfaceA || '')
            : ((this._state.useLinkContext && (selectedPovRow?.parent || selectedPovRow?.ifName)) || link.device2Interface || link.linkDetails?.interfaceB || '');
        const aristaNeighbor = povNeighbors.find(n => this._isArista(n));
        const hasArista = !!aristaNeighbor;

        const dnaasNeighbors = povNeighbors.filter(n => this._isDnaas(n));
        const matchedDnaasNeighbor = linkIntf
            ? dnaasNeighbors.find(n => this._interfaceMatches(this._neighborLocalInterface(n), linkIntf))
            : null;
        const fallbackDnaasNeighbor = !linkIntf && dnaasNeighbors.length === 1 ? dnaasNeighbors[0] : null;
        const dnaasNeighbor = matchedDnaasNeighbor || fallbackDnaasNeighbor;
        const linkDnaasEndpoint = dnaasNeighbor
            ? this._linkDnaasEndpointForNeighbor(isPov1, link, dnaasNeighbor)
            : this._linkDnaasEndpoint(isPov1, link, linkIntf);
        const hasDnaas = !!(dnaasNeighbor || linkDnaasEndpoint);
        const povLabel = isPov1 ? 'device1' : 'device2';
        console.log(`[XRAY detect] POV=${povLabel} | Arista on POV: ${hasArista} | DNAAS: ${hasDnaas}`, {
            linkIntf,
            dnaasNeighbors,
            linkDnaasEndpoint
        });

        if (hasArista) {
            this._aristaInfo = {
                host: this._neighborName(aristaNeighbor),
                srcPort: this._neighborRemotePort(aristaNeighbor),
                dutInterface: linkIntf || '',
                aristaPort: this._neighborLocalInterface(aristaNeighbor)
            };
            console.log('[XRAY detect] Arista info:', this._aristaInfo, '| Link intf:', linkIntf || '(none - needs picker)');
        } else {
            this._aristaInfo = null;
        }

        const intfRow = this._popup?.querySelector('#xray-intf-picker-row');
        const intfInfo = this._popup?.querySelector('#xray-intf-info');
        const intfSelect = this._popup?.querySelector('#xray-intf-select');
        const intfLoading = this._popup?.querySelector('#xray-intf-loading');
        const oldManual = this._popup?.querySelector('#xray-intf-manual');
        if (oldManual) oldManual.remove();
        if (intfSelect) { intfSelect.innerHTML = ''; intfSelect.style.display = 'none'; }

        const hints = [];
        if (hasArista && dpBtn) {
            dpBtn.disabled = false;
            const linkIntf = this._aristaInfo?.dutInterface || '';
            this._setButtonHint(dpBtn, `Live stream via ${this._neighborName(aristaNeighbor)}`);
            if (linkIntf) {
                hints.push(`Source: ${linkIntf} (from link table)`);
                if (intfRow) intfRow.style.display = '';
                if (intfInfo) intfInfo.textContent = linkIntf;
                if (intfLoading) intfLoading.style.display = 'none';
            } else {
                hints.push('No interface in link table -- select below');
                if (intfRow) intfRow.style.display = '';
                if (intfInfo) intfInfo.textContent = '';
                this._fetchDeviceInterfaces(isPov1, aristaNeighbor);
            }
        } else if (dpBtn) {
            dpBtn.disabled = true;
            this._setButtonHint(dpBtn, 'Live Capture requires an Arista switch visible in LLDP neighbors of this POV device.');
            hints.push('Live Capture: No Arista in LLDP -- needs Arista connected to this device');
            if (intfRow) intfRow.style.display = 'none';
        }
        if (hasDnaas && dnaasBtn) {
            const leafLabel = this._neighborName(dnaasNeighbor) || linkDnaasEndpoint?.leafLabel || '';
            const sourcePort = this._neighborRemotePort(dnaasNeighbor) || linkDnaasEndpoint?.sourcePort || '';
            const dutInterface = this._neighborLocalInterface(dnaasNeighbor) || linkDnaasEndpoint?.dutInterface || linkIntf || '';
            this._dnaasInfo = {
                leafHost: linkDnaasEndpoint?.leafHost || leafLabel,
                leafLabel,
                sourcePort,
                dutInterface,
                source: linkDnaasEndpoint?.source || 'lldp'
            };
            const preflightKey = this._dnaasPreflightKey(this._dnaasInfo);
            this._dnaasMirrorPreflightKey = preflightKey;
            const mirrorState = this._dnaasMirrorPreflightCache[preflightKey];
            console.log('[XRAY detect] DNAAS info:', this._dnaasInfo, 'mirror:', mirrorState);
            if (mirrorState?.available) {
                dnaasBtn.disabled = false;
                this._dnaasInfo.mirrorUplink = mirrorState.chosen || '';
                this._dnaasInfo.mirrorPreflight = mirrorState;
                this._setButtonHint(dnaasBtn, `Data Plane via DNAAS leaf; mirror ${mirrorState.chosen} is free`);
                hints.push(`DNAAS source: ${this._dnaasInfo.dutInterface} -> ${this._dnaasInfo.leafHost}:${this._dnaasInfo.sourcePort}; mirror ${mirrorState.chosen} free`);
            } else {
                dnaasBtn.disabled = true;
                this._dnaasInfo.mirrorPreflight = mirrorState || { checking: true };
                const reason = mirrorState?.reason || mirrorState?.error || 'checking DNAAS mirror port availability';
                this._setButtonHint(dnaasBtn, `DP (DNAAS) unavailable until a free leaf mirror port is confirmed: ${reason}`);
                hints.push(`DP (DNAAS): ${reason}`);
                if (!mirrorState) {
                    this._refreshDnaasMirrorPreflight(this._dnaasInfo, preflightKey);
                }
            }
        } else if (dnaasBtn) {
            dnaasBtn.disabled = true;
            if (dnaasNeighbors.length && linkIntf) {
                const dnaasIfs = dnaasNeighbors.map(n => this._neighborLocalInterface(n)).filter(Boolean).join(', ');
                this._setButtonHint(dnaasBtn, `DNAAS leaf exists, but selected POV interface ${linkIntf} is not one of the DNAAS-facing interfaces.`);
                hints.push(`DP (DNAAS): select a PE-4 DNAAS-facing link (${dnaasIfs})`);
            } else if (dnaasNeighbors.length > 1) {
                this._setButtonHint(dnaasBtn, 'Multiple DNAAS leaf links found; select a link/interface so XRAY can choose the correct leaf source port.');
                hints.push('DP (DNAAS): choose the PE-4 DNAAS-facing interface first');
            } else {
                this._setButtonHint(dnaasBtn, 'No DNAAS leaf available - no DNAAS neighbor in LLDP');
                hints.push('DP (DNAAS): No DNAAS leaf detected');
            }
            this._dnaasInfo = null;
        }
        // Show green dot on the OTHER header button if that device has Arista
        const otherNeighbors = isPov1 ? this._lldpCache.device2 : this._lldpCache.device1;
        const otherHasArista = otherNeighbors.some(n => this._isArista(n));
        const otherPovKey = isPov1 ? 'device2' : 'device1';
        const headerBtns = this._popup?.querySelectorAll('#xray-pov-header .xray-pov-btn');
        headerBtns?.forEach(btn => {
            let dot = btn.querySelector('.xray-header-dot');
            if (btn.dataset.pov === otherPovKey && otherHasArista) {
                if (!dot) {
                    dot = document.createElement('span');
                    dot.className = 'xray-header-dot';
                    dot.style.cssText = 'width:6px;height:6px;border-radius:50%;background:#27ae60;box-shadow:0 0 4px rgba(39,174,96,0.6);display:inline-block;margin-left:5px;vertical-align:middle;';
                    btn.appendChild(dot);
                }
                dot.style.display = 'inline-block';
                btn.title = 'Live Capture available -- click to switch';
            } else {
                if (dot) dot.style.display = 'none';
                if (btn.dataset.pov === otherPovKey) btn.title = '';
            }
        });

        if (!hasArista && otherHasArista) {
            hints.push('Arista found on other device -- switch POV to enable Live Capture');
        }
        setHint(hints.length ? hints.join('; ') : '');

        if (this._state.mode === 'dp' && dpBtn?.disabled) {
            this._state.mode = 'cp';
            this._popup?.querySelectorAll('.xray-mode-btn').forEach(b => b.classList.remove('active'));
            this._popup?.querySelector('.xray-mode-btn[data-mode="cp"]')?.classList.add('active');
        }
        if (this._state.mode === 'dnaas-dp' && dnaasBtn?.disabled) {
            this._state.mode = 'cp';
            this._popup?.querySelectorAll('.xray-mode-btn').forEach(b => b.classList.remove('active'));
            this._popup?.querySelector('.xray-mode-btn[data-mode="cp"]')?.classList.add('active');
        }
    },

    async _startCapture() {
        const btn = this._popup?.querySelector('#xray-start-btn');
        const status = this._popup?.querySelector('#xray-status');
        if (!btn || !status) return;

        if (this._activeCapture) {
            try {
                await _xrayAuthFetch(`/api/xray/stop/${this._activeCapture}`, { method: 'POST' });
            } catch (e) { /* ignore */ }
            this._stopCapture();
            return;
        }

        const link = this._link;
        const editor = this._editor;
        const device1 = editor.objects.find(d => d.id === link.device1);
        const device2 = editor.objects.find(d => d.id === link.device2);
        const isPov1 = this._state.pov === 'device1';
        const device = isPov1 ? device1 : device2;
        const activeSrcRow = (() => {
            const rows = this._state.srcRows || {};
            const row = isPov1 ? (rows.device1 || rows.A) : (rows.device2 || rows.B);
            return row || this._state.srcRow || {};
        })();
        this._state.srcRow = activeSrcRow.ifName ? activeSrcRow : (this._state.srcRow || null);
        const useLinkContext = !!(this._state.useLinkContext && activeSrcRow.ifName);
        const rowIf = useLinkContext ? (activeSrcRow.ifName || '') : '';
        const rowSide = useLinkContext ? (activeSrcRow.side === 'B' ? 'device2' : (activeSrcRow.side === 'A' ? 'device1' : '')) : '';
        const rowMatchesPov = !!(useLinkContext && rowSide === this._state.pov);
        const rowCaptureInterface = rowMatchesPov
            ? (this._state.mode === 'dp'
                ? (activeSrcRow.parent || rowIf)
                : rowIf)
            : '';
        const intf = useLinkContext
            ? (rowCaptureInterface
                || (isPov1 ? (link.device1Interface || link.linkDetails?.interfaceA || '') : (link.device2Interface || link.linkDetails?.interfaceB || '')))
            : '';
        const isSubInterfaceCapture = !!(intf && /\.\d+/.test(intf));

        if (!device) {
            editor.showToast('Device not found', 'error');
            return;
        }

        // DNAAS POV gate: cp/dp tcpdump cannot run on a DNAAS fabric
        // device. The popup already disables the POV button at render
        // time, but we re-check here in case `_state.pov` was mutated
        // by another code path (saved-state restore, programmatic flip,
        // mode-change race) between popup-open and click. Only the
        // dedicated `dnaas-dp` mode is allowed against a DNAAS POV --
        // it uses a different code path (--dnaas-leaf-host + uplink
        // mirror) and lives behind its own button. Backend mirrors this
        // check in `_xray_run` so a direct API call cannot bypass it.
        if (this._isDnaasPov(device) && this._state.mode !== 'dnaas-dp') {
            editor.showToast(
                `'${device.label}' is a DNAAS fabric device -- pick the other endpoint as POV or switch to DP (DNAAS) mode.`,
                'warning'
            );
            if (status) {
                status.style.display = 'block';
                status.style.background = 'rgba(255,165,0,0.12)';
                status.style.color = '#FF9500';
                status.textContent = 'Blocked: DNAAS fabric device is not a valid CP/DP POV.';
            }
            return;
        }

        // Mode-gate: packet capture (CP or DP) needs DNOS CLI on the
        // device. If the device is in GI/RECOVERY/unknown, surface the
        // central modal instead of letting the SSH attempt fail with
        // an opaque error after a long timeout.
        if (typeof window.DeviceModeGate !== 'undefined') {
            const decision = await window.DeviceModeGate.require(
                device, 'packet_capture', { live: true }
            );
            if (!decision) {
                if (status) {
                    status.textContent = 'Blocked: device not in DNOS mode';
                    status.style.color = '#e74c3c';
                }
                return;
            }
        }

        let dutHost = '';
        const targetPick = window.TopologySshTarget?.pick
            ? window.TopologySshTarget.pick(device)
            : null;
        const pickedHost = String(targetPick?.host || '').trim();
        const pickedIsResolverKey = targetPick?.source === 'serial';
        const hasResolvedTarget = !!(pickedHost && !pickedIsResolverKey);
        const hasManualTarget = device.sshConfig?.host || device.deviceAddress;
        if (!hasResolvedTarget && !hasManualTarget && !(device.label || device.deviceSerial || device.serial)) {
            const sshHost = this._popup?.querySelector('#xray-ssh-host')?.value?.trim();
            const sshUser = this._popup?.querySelector('#xray-ssh-user')?.value?.trim() || 'dnroot';
            const sshPass = this._popup?.querySelector('#xray-ssh-pass')?.value || '';
            if (!sshHost) {
                editor.showToast('Enter device host (IP) to capture', 'warning');
                return;
            }
            device.sshConfig = {
                ...(device.sshConfig || {}),
                host: sshHost, user: sshUser, password: sshPass,
                _userSavedHost: sshHost, _userSavedUser: sshUser, _userSavedPass: sshPass
            };
            device.deviceAddress = `${sshUser}@${sshHost}`;
            if (editor.saveState) editor.saveState();
            dutHost = sshHost;
        } else {
            // Verified IP/host fields must win over display labels. If the
            // picker only has a serial/label, omit dut_host and let the
            // backend resolve the device label through inventory.
            dutHost = hasResolvedTarget ? pickedHost : '';
        }

        const PROTOCOL_BPF = {
            bgp: 'tcp port 179',
            ospf: 'proto ospf',
            isis: 'isis',
            ldp: 'tcp port 646 or udp port 646',
            lldp: 'ether proto 0x88cc',
            bfd: 'udp port 3784 or udp port 4784'
        };
        const DNOS_INTERNAL_EXCLUSION = '(ip or ip6 or isis or arp)';
        const filterParts = this._state.filters.map(f => '(' + (PROTOCOL_BPF[f] || '') + ')').filter(Boolean);
        let captureFilter = '';
        if (filterParts.length > 0) {
            captureFilter = filterParts.join(' or ');
        } else if (this._state.mode === 'cp' && this._state.excludeInternal) {
            captureFilter = DNOS_INTERNAL_EXCLUSION;
        }

        const cleanupToggle = this._popup?.querySelector('#xray-cleanup-toggle');
        const isDP = this._state.mode === 'dp';
        const body = {
            device: device?.label || '',
            mode: this._state.mode,
            interface: intf || 'any',
            duration: isDP ? 0 : this._state.duration,
            output: isDP ? 'mac-live' : this._state.output,
            direction: isDP ? 'both' : (this._state.direction || 'both'),
            capture_filter: captureFilter || undefined,
            dut_host: dutHost || undefined,
            cleanup_server_pcap: cleanupToggle ? cleanupToggle.checked : true,
            link_context_enabled: useLinkContext,
            link_context_filter_enabled: rowMatchesPov,
            auto_vlan_filter: !!(rowMatchesPov && this._state.autoVlanFilter && !isSubInterfaceCapture),
            auto_ip_filter: !!(rowMatchesPov && this._state.autoIpFilter),
            vlan_outer: rowMatchesPov ? (activeSrcRow.vlanOuter || undefined) : undefined,
            vlan_inner: rowMatchesPov ? (activeSrcRow.vlanInner || undefined) : undefined,
            ip: rowMatchesPov ? (activeSrcRow.ip || undefined) : undefined,
            capture_interface: intf || 'any',
            vlan_filter_suppressed: !!(useLinkContext && this._state.autoVlanFilter && (isSubInterfaceCapture || !rowMatchesPov))
        };

        if (this._state.mode === 'dp' && this._aristaInfo) {
            body.arista_host = this._aristaInfo.host;
            body.arista_src_port = this._aristaInfo.srcPort;
            if (!body.arista_host || !body.arista_src_port) {
                editor.showToast('Arista LLDP data is incomplete. Refresh LLDP and try Live Capture again.', 'warning');
                return;
            }
            const manualInput = this._popup?.querySelector('#xray-intf-manual');
            const clickedRowIntf = rowMatchesPov
                ? (activeSrcRow.parent || activeSrcRow.ifName || '')
                : '';
            const selectedIntf = clickedRowIntf || this._aristaInfo.dutInterface || manualInput?.value?.trim() || '';
            if (selectedIntf) {
                body.interface = selectedIntf;
                body.capture_interface = selectedIntf;
            } else {
                editor.showToast('Select or enter source interface for Live Capture', 'warning');
                return;
            }
        }

        if (this._state.mode === 'dnaas-dp' && this._dnaasInfo) {
            body.dnaas_leaf_host = this._dnaasInfo.leafHost;
            body.dnaas_leaf_label = this._dnaasInfo.leafLabel || this._dnaasInfo.leafHost;
            body.dnaas_leaf_source_port = this._dnaasInfo.sourcePort;
            if (this._dnaasInfo.mirrorUplink) {
                body.dnaas_mirror_uplink = this._dnaasInfo.mirrorUplink;
            }
            if (this._dnaasInfo.mirrorPreflight?.spine_host) {
                body.dnaas_spine_host = this._dnaasInfo.mirrorPreflight.spine_host;
            }
            if (!body.dnaas_leaf_host || !body.dnaas_leaf_source_port) {
                editor.showToast('DNAAS LLDP data is incomplete. Refresh LLDP and try DP (DNAAS) again.', 'warning');
                return;
            }
            if (!this._dnaasInfo.mirrorPreflight?.available) {
                editor.showToast('DP (DNAAS) is blocked until XRAY confirms a free DNAAS mirror port.', 'warning');
                return;
            }
        }

        const needsMac = (body.output === 'mac' || body.output === 'mac-live');
        if (needsMac) {
            // Safety re-check in case verification aged out between popup open and click.
            // Note: the Start Capture button should already be locked if this check fails,
            // but we re-check anyway because TTL can expire mid-session and because a
            // direct click could race with a config/verification change on another tab.
            await this._refreshMacVerificationFromConfig();
            const macIp = this._macVerification.ip || this._lastConfigIp || '';
            if (!this._isMacVerificationValid(macIp)) {
                // Keep the button locked and show the inline verify panel instead
                // of silently proceeding. Matches the "locked until verified" contract
                // documented in DEVELOPMENT_GUIDELINES.md (XRAY section).
                btn.textContent = 'Start Capture';
                btn.disabled = true;
                btn.setAttribute('data-mac-locked', '1');
                this._renderMacVerifyPanel('expired');
                return;
            }
        }

        btn.textContent = 'Starting...';
        btn.disabled = true;
        status.style.display = 'block';
        status.textContent = 'Initializing capture...';

        try {
            const resp = await _xrayAuthFetch('/api/xray/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const result = await resp.json();
            if (result.error) {
                const errLower = String(result.error).toLowerCase();
                const isMacVerifyError = /mac.*(not verified|verification|workstation)/i.test(result.error)
                    || errLower.includes('no mac workstation ip configured');
                if (isMacVerifyError) {
                    // Drop the cached verification and relock the button.
                    // Show the inline verify panel so the user can re-verify
                    // without hunting for the settings toolbar.
                    this._macVerification = { ip: null, at: 0, ok: false };
                    btn.textContent = 'Start Capture';
                    btn.disabled = true;
                    btn.setAttribute('data-mac-locked', '1');
                    this._renderMacVerifyPanel('expired');
                    return;
                }
                status.textContent = 'Error: ' + result.error;
                status.style.background = 'rgba(231,76,60,0.15)';
                status.style.color = '#e74c3c';
                btn.textContent = 'Start Capture';
                btn.disabled = false;
                return;
            }
            this._activeCapture = result.capture_id;
            editor._xrayCapturing = link.id;
            btn.classList.add('capturing');
            btn.disabled = false;
            status.style.background = 'rgba(0,102,250,0.1)';
            status.style.color = '#0066FA';
            editor.draw();

            this._captureStart = Date.now();
            this._captureDuration = this._state.duration;
            this._updateCountdown(btn, status);
            this._countdownTimer = setInterval(() => this._updateCountdown(btn, status), 500);

            this._pollIntervalMs = 2000;
            this._pollTimer = setInterval(() => this._pollStatus(), this._pollIntervalMs);
        } catch (e) {
            status.textContent = 'Failed to start: ' + e.message;
            status.style.background = 'rgba(231,76,60,0.15)';
            status.style.color = '#e74c3c';
            btn.textContent = 'Start Capture';
            btn.disabled = false;
        }
    },

    async _pollStatus() {
        if (!this._activeCapture) return;
        try {
            const resp = await _xrayAuthFetch(`/api/xray/status/${this._activeCapture}`);
            if (!resp.ok) {
                throw new Error(`status HTTP ${resp.status}`);
            }
            const data = await resp.json();
            if (data.error && !data.status) {
                throw new Error(data.error);
            }
            this._pollFailures = 0;
            const status = this._popup?.querySelector('#xray-status');
            const btn = this._popup?.querySelector('#xray-start-btn');
            const popupGone = !this._popup;
            const isMacOutput = this._state?.output === 'mac' || this._state?.mode === 'dp';
            const deliveryStatus = data.mac_delivery_status || 'not_required';

            if (data.status === 'running') {
                if (status && isMacOutput && deliveryStatus === 'in_progress') {
                    if (this._countdownTimer) {
                        clearInterval(this._countdownTimer);
                        this._countdownTimer = null;
                    }
                    this._captureStart = null;
                    this._captureDuration = null;
                    // Once the backend reports delivery has started, tighten the
                    // poll cadence so the UI flips to "Wireshark opened" within
                    // ~500ms of the helper finishing instead of the 2s default.
                    this._setPollCadence(500);
                    if (btn) {
                        btn.innerHTML = 'Delivering to Mac...';
                        btn.disabled = true;
                    }
                    status.style.background = 'rgba(0,102,250,0.1)';
                    status.style.color = '#0066FA';
                    this._renderDeliveryProgress(status, data.mac_delivery_step || 'queued');
                }
            } else if (data.status === 'completed') {
                // Stop countdown immediately so the button doesn't say "Finishing..."
                if (this._countdownTimer) {
                    clearInterval(this._countdownTimer);
                    this._countdownTimer = null;
                }
                this._captureStart = null;
                this._captureDuration = null;

                if (isMacOutput && (data.mac_delivery_failed || deliveryStatus === 'failed')) {
                    if (status) {
                        this._showMacRetryPrompt(status, data.local_pcap_path || data.pcap_path, { failed: true });
                    } else if (popupGone && this._editor) {
                        this._editor.showToast('Capture done but Mac delivery failed -- reopen XRAY to retry', 'warning');
                    }
                } else if (isMacOutput && deliveryStatus !== 'delivered') {
                    if (status) {
                        this._showMacRetryPrompt(status, data.local_pcap_path || data.pcap_path, { failed: false });
                    }
                    if (popupGone && this._editor) {
                        this._editor.showToast('Capture saved; Mac delivery was not confirmed -- reopen XRAY to retry', 'warning');
                    }
                } else {
                    const fileName = data.pcap_path ? data.pcap_path.split('/').pop() : '';
                    const outputLines = data.output_lines || [];
                    const actuallyDelivered = deliveryStatus === 'delivered' || outputLines.some(l => /delivered to mac|opened in wireshark|mac helper deployed|live streaming:/i.test(l));
                    const macMsg = isMacOutput ? (actuallyDelivered ? 'Delivered to Mac' : 'Capture complete (check server for pcap)') : 'Capture complete';
                    if (status) {
                status.style.background = 'rgba(39,174,96,0.15)';
                status.style.color = '#27ae60';
                        status.textContent = macMsg + '!' + (fileName ? '\n' + fileName : '');
                    }
                    if (btn) {
                        btn.textContent = 'Start Capture';
                        btn.classList.remove('capturing');
                        btn.disabled = false;
                    }
                    if (popupGone && this._editor) {
                        this._editor.showToast(macMsg + (fileName ? ' -- ' + fileName : ''), 'success');
                    }
                }
                this._stopCapture();
            } else if (data.status === 'error') {
                if (this._countdownTimer) {
                    clearInterval(this._countdownTimer);
                    this._countdownTimer = null;
                }
                if (status) {
                    this._showCaptureError(status, data);
                }
                if (popupGone && this._editor) {
                    this._editor.showToast('Capture error: ' + (data.error || 'Unknown'), 'error');
                }
                this._stopCapture();
            }
        } catch (e) {
            this._pollFailures = (this._pollFailures || 0) + 1;
            if (this._pollFailures < 3) return;
            const status = this._popup?.querySelector('#xray-status');
            if (status) {
                status.style.background = 'rgba(231,76,60,0.15)';
                status.style.color = '#e74c3c';
                status.textContent = `Lost XRAY status: ${e.message}. Reopen Packet Capture and retry.`;
            }
            if (this._editor) {
                this._editor.showToast(`XRAY status lost: ${e.message}`, 'error');
            }
            this._stopCapture();
        }
    },

    _showCaptureError(statusEl, data = {}) {
        const outputLines = Array.isArray(data.output_lines) ? data.output_lines : [];
        const usefulLines = outputLines
            .map(line => String(line || '').trim())
            .filter(Boolean)
            .filter(line => /fatal|error|failed|exception|permission denied|unknown word|timeout|timed out|no route|unreachable|capture may not have started/i.test(line));
        const tail = (usefulLines.length ? usefulLines : outputLines.map(line => String(line || '').trim()).filter(Boolean)).slice(-4);
        statusEl.style.background = 'rgba(231,76,60,0.15)';
        statusEl.style.color = '#e74c3c';
        statusEl.innerHTML = '';

        const title = document.createElement('div');
        title.textContent = 'Error: ' + (data.error || 'Capture failed');
        statusEl.appendChild(title);

        if (tail.length) {
            const details = document.createElement('pre');
            details.textContent = tail.join('\n');
            details.style.cssText = 'margin:6px 0 0; white-space:pre-wrap; word-break:break-word; font:inherit; opacity:0.9;';
            statusEl.appendChild(details);
        }
    },

    _showMacRetryPrompt(statusEl, localPcapPath, options = {}) {
        statusEl.style.background = 'rgba(255, 165, 0, 0.12)';
        statusEl.style.color = '#FF9500';
        statusEl.innerHTML = '';
        const hasPcap = !!localPcapPath;

        const msg = document.createElement('div');
        msg.textContent = hasPcap
            ? (options.failed
                ? 'Capture is temporarily available, but Mac delivery failed -- IP may have changed.'
                : 'Capture is temporarily available. Mac delivery was not confirmed yet -- retry delivery or download.')
            : (options.failed
                ? 'Mac delivery failed and the server-side capture was cleaned up.'
                : 'Mac delivery was not confirmed and the server-side capture was cleaned up.');
        msg.style.marginBottom = '8px';
        statusEl.appendChild(msg);

        if (hasPcap) {
            const pathLine = document.createElement('div');
            pathLine.textContent = 'Temporary server file: ' + localPcapPath;
            pathLine.style.cssText = 'font-size: 11px; opacity: 0.7; margin-bottom: 8px; word-break: break-all;';
            statusEl.appendChild(pathLine);
        }

        if (!hasPcap) {
            return;
        }

        const row = document.createElement('div');
        row.style.cssText = 'display: flex; gap: 6px; align-items: center;';

        const input = document.createElement('input');
        input.type = 'text';
        input.placeholder = 'New Mac IP (e.g. 10.x.x.x)';
        input.style.cssText = `
            flex: 1; padding: 6px 8px; border-radius: 6px;
            border: 1px solid rgba(255,255,255,0.15);
            background: rgba(0,0,0,0.2); color: #fff;
            font-size: 12px; outline: none;
        `;
        try {
            _xrayAuthFetch('/api/xray/config').then(r => r.json()).then(cfg => {
                if (cfg?.mac?.ip_vpn) input.value = cfg.mac.ip_vpn;
            });
        } catch (_) {}

        const retryBtn = document.createElement('button');
        retryBtn.textContent = 'Deliver';
        retryBtn.style.cssText = `
            padding: 6px 14px; border-radius: 6px; border: none;
            background: #0066FA; color: #fff; font-size: 12px;
            font-weight: 600; cursor: pointer; white-space: nowrap;
        `;
        retryBtn.onmouseenter = () => { retryBtn.style.opacity = '0.85'; };
        retryBtn.onmouseleave = () => { retryBtn.style.opacity = '1'; };

        retryBtn.onclick = async (e) => {
            e.stopPropagation();
            const newIp = input.value.trim();
            if (!newIp) { input.style.borderColor = '#e74c3c'; return; }
            retryBtn.disabled = true;
            retryBtn.textContent = 'Delivering...';
            try {
                const resp = await _xrayAuthFetch('/api/xray/redeliver', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pcap_path: localPcapPath, mac_ip: newIp })
                });
                const result = await resp.json();
                if (result.ok) {
                    statusEl.style.background = 'rgba(39,174,96,0.15)';
                    statusEl.style.color = '#27ae60';
                    statusEl.innerHTML = '';
                    statusEl.textContent = 'Delivered to Mac! Opening in Wireshark...';
                } else {
                    retryBtn.textContent = 'Retry';
                    retryBtn.disabled = false;
                    const errLine = document.createElement('div');
                    errLine.textContent = result.error || 'Delivery failed';
                    errLine.style.cssText = 'color: #e74c3c; font-size: 11px; margin-top: 6px;';
                    statusEl.appendChild(errLine);
                }
            } catch (err) {
                retryBtn.textContent = 'Retry';
                retryBtn.disabled = false;
            }
        };

        const downloadBtn = document.createElement('button');
        downloadBtn.textContent = 'Download';
        downloadBtn.style.cssText = `
            padding: 6px 14px; border-radius: 6px; border: none;
            background: rgba(39,174,96,0.9); color: #fff; font-size: 12px;
            font-weight: 600; cursor: pointer; white-space: nowrap;
        `;
        downloadBtn.onmouseenter = () => { downloadBtn.style.opacity = '0.85'; };
        downloadBtn.onmouseleave = () => { downloadBtn.style.opacity = '1'; };
        downloadBtn.onclick = () => {
            if (this._activeCapture) {
                window.location.href = '/api/xray/download/' + this._activeCapture;
            }
        };

        row.appendChild(input);
        row.appendChild(retryBtn);
        row.appendChild(downloadBtn);
        statusEl.appendChild(row);
    },

    _updateCountdown(btn, statusEl) {
        if (!this._captureStart || !this._captureDuration) return;
        const elapsed = (Date.now() - this._captureStart) / 1000;
        const remaining = Math.max(0, this._captureDuration - elapsed);
        const secs = Math.ceil(remaining);
        const pct = Math.min(100, (elapsed / this._captureDuration) * 100);

        // Track when delivery phase started (countdown hit 0)
        const delivering = secs <= 0;
        if (delivering && !this._deliveryStartedAt) {
            this._deliveryStartedAt = Date.now();
            // Don't wait up to 2s for the next scheduled poll: ask the
            // backend for the latest delivery state right now and tighten
            // the cadence so the UI flips to "Wireshark opened" the moment
            // the helper finishes on the Mac.
            this._setPollCadence(500);
            try { this._pollStatus(); } catch (_) {}
        }

        const sharkSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" style="vertical-align:middle;margin-right:4px;"><circle cx="11" cy="11" r="7" stroke="#fff" stroke-width="2" fill="rgba(255,255,255,0.12)"/><path class="xray-shark-fin" d="M11 13 C11 13 9.2 7.5 11 5 C12.8 7.5 11 13 11 13 Z" fill="#fff" stroke="none" opacity="0.95"/><path d="M21 21l-4.35-4.35" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg>`;
        if (btn) {
            if (secs > 0) {
                btn.innerHTML = `${sharkSvg}<span style="font-variant-numeric: tabular-nums;">${secs}s</span> remaining &mdash; Stop`;
            } else {
                btn.innerHTML = `${sharkSvg}Delivering to Mac...`;
                btn.disabled = true;
            }
        }
        if (statusEl) {
            const outputLabel = this._state.output === 'mac' ? 'Opening on Mac' : 'Saving pcap';
            const deliveryElapsed = this._deliveryStartedAt
                ? Math.max(0, Math.floor((Date.now() - this._deliveryStartedAt) / 1000))
                : 0;
            const phase = secs > 0 ? secs + 's left' : `delivering... ${deliveryElapsed}s`;
            statusEl.innerHTML = `
                <div style="display:flex;justify-content:space-between;margin-bottom:4px;font-size:10px;">
                    <span>Capturing... ${phase}</span>
                    <span>${outputLabel}</span>
                </div>
                <div style="height:4px;border-radius:2px;background:rgba(0,102,250,0.15);overflow:hidden;">
                    <div style="height:100%;width:${pct}%;background:#0066FA;border-radius:2px;transition:width 0.4s linear;"></div>
                </div>
            `;
        }
    },

    _stopCapture() {
        if (this._pollTimer) {
            clearInterval(this._pollTimer);
            this._pollTimer = null;
        }
        if (this._countdownTimer) {
            clearInterval(this._countdownTimer);
            this._countdownTimer = null;
        }
        this._captureStart = null;
        this._captureDuration = null;
        this._activeCapture = null;
        this._deliveryStartedAt = null;
        this._pollFailures = 0;
        this._pollIntervalMs = 2000;
        if (this._editor) {
            this._editor._xrayCapturing = null;
            this._editor.draw();
        }
        const btn = this._popup?.querySelector('#xray-start-btn');
        if (btn) {
            btn.textContent = 'Start Capture';
            btn.classList.remove('capturing');
            btn.disabled = false;
        }
    },

    // Re-arm the status poller at a different cadence. Called with 500ms
    // when Mac delivery starts (so we surface "Wireshark opened" within
    // ~500ms instead of waiting up to 2000ms for the default tick) and
    // back at 2000ms when the capture is still running normally.
    _setPollCadence(ms) {
        if (!this._activeCapture) return;
        if (this._pollIntervalMs === ms) return;
        this._pollIntervalMs = ms;
        if (this._pollTimer) clearInterval(this._pollTimer);
        this._pollTimer = setInterval(() => this._pollStatus(), ms);
    },

    // Render a one-line delivery progress indicator with a small step strip
    // so the user knows whether we're still SCPing, opening Wireshark, etc.
    // Steps come from /api/xray/status `mac_delivery_step` and progress
    // monotonically: queued -> sftp_connecting -> mac_verified -> sftp_done
    // -> opening_wireshark -> opened.
    _renderDeliveryProgress(statusEl, step) {
        if (!statusEl) return;
        const STEPS = [
            { key: 'sftp_connecting', label: 'Connect Mac' },
            { key: 'mac_verified',    label: 'SSH OK' },
            { key: 'sftp_done',       label: 'Pcap copied' },
            { key: 'opening_wireshark', label: 'Open Wireshark' },
            { key: 'opened',          label: 'Wireshark up' }
        ];
        const order = ['queued', ...STEPS.map(s => s.key), 'failed'];
        const idx = Math.max(0, order.indexOf(step));
        const phaseHeadline = step === 'opened'
            ? 'Wireshark opened on Mac'
            : (step === 'queued'
                ? 'Capture finished. Preparing Mac delivery...'
                : `Delivering to Mac: ${(STEPS.find(s => s.key === step) || {}).label || step}`);
        const chips = STEPS.map((s, i) => {
            const stepIdx = order.indexOf(s.key);
            const done = stepIdx < idx;
            const active = stepIdx === idx;
            const bg = done ? 'rgba(39,174,96,0.18)'
                : (active ? 'rgba(0,102,250,0.18)' : 'rgba(255,255,255,0.06)');
            const fg = done ? '#27ae60' : (active ? '#0066FA' : 'rgba(200,210,220,0.55)');
            const border = active ? '1px solid rgba(0,102,250,0.45)' : '1px solid transparent';
            return `<span style="padding:2px 6px;border-radius:10px;background:${bg};color:${fg};border:${border};font-size:10px;line-height:14px;white-space:nowrap;">${s.label}</span>`;
        }).join('<span style="color:rgba(200,210,220,0.35);font-size:10px;align-self:center;">&rarr;</span>');
        statusEl.innerHTML = `
            <div style="margin-bottom:6px;font-size:11px;font-weight:500;">${phaseHeadline}</div>
            <div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center;">${chips}</div>
        `;
    }
};

console.log('[topology-xray-popup.js] XrayPopup loaded');
