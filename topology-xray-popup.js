/**
 * topology-xray-popup.js - XRAY Capture Popup for Links
 * Shows DP/CP/DNAAS-DP capture options on selected device-to-device links.
 */

'use strict';

window.XrayPopup = {
    _popup: null,
    _activeCapture: null,
    _pollTimer: null,

    show(editor, link, screenPos) {
        this.hide();
        if (!link || !link.device1 || !link.device2) return;

        const device1 = editor.objects.find(d => d.id === link.device1);
        const device2 = editor.objects.find(d => d.id === link.device2);
        if (!device1 || !device2) return;

        const name1 = device1.label || 'Device 1';
        const name2 = device2.label || 'Device 2';
        const intf1 = link.device1Interface || '';
        const intf2 = link.device2Interface || '';
        const isDark = editor.darkMode;

        const popup = document.createElement('div');
        popup.id = 'xray-capture-popup';
        popup.style.cssText = `
            position: fixed;
            left: ${screenPos.x}px;
            top: ${screenPos.y + 20}px;
            z-index: 100000;
            min-width: 340px;
            max-width: 400px;
            background: ${isDark ? 'rgba(15, 15, 25, 0.92)' : 'rgba(255, 255, 255, 0.95)'};
            border: 1px solid ${isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)'};
            border-radius: 14px;
            padding: 16px;
            font-family: 'Poppins', sans-serif;
            color: ${isDark ? '#e0e6ed' : '#1a1a1a'};
            backdrop-filter: blur(24px) saturate(180%);
            -webkit-backdrop-filter: blur(24px) saturate(180%);
            box-shadow: 0 8px 40px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,${isDark ? '0.08' : '0.5'});
            animation: xrayPopupFadeIn 0.2s ease;
        `;

        const modeColor = (active) => active ? '#0066FA' : (isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)');
        const modeText = (active) => active ? '#fff' : (isDark ? '#aaa' : '#666');

        popup.innerHTML = `
            <style>
                @keyframes xrayPopupFadeIn { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
                #xray-capture-popup .xray-mode-btn {
                    padding: 8px 16px; border-radius: 8px; border: 1px solid transparent;
                    cursor: pointer; font-size: 12px; font-weight: 600; font-family: 'Poppins', sans-serif;
                    transition: all 0.15s ease; flex: 1; text-align: center;
                }
                #xray-capture-popup .xray-mode-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,102,250,0.3); }
                #xray-capture-popup .xray-mode-btn:disabled { opacity: 0.35; cursor: not-allowed; }
                #xray-capture-popup .xray-mode-btn.active { background: linear-gradient(135deg, #0066FA, #0052CC); color: #fff; border-color: rgba(255,255,255,0.2); }
                #xray-capture-popup .xray-opt-btn {
                    padding: 5px 10px; border-radius: 6px; border: 1px solid ${isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)'};
                    cursor: pointer; font-size: 11px; font-family: 'Poppins', sans-serif;
                    background: ${isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)'};
                    color: ${isDark ? '#ccc' : '#555'}; transition: all 0.15s ease;
                }
                #xray-capture-popup .xray-opt-btn:hover { background: rgba(0,102,250,0.15); color: #0066FA; }
                #xray-capture-popup .xray-opt-btn.active { background: rgba(0,102,250,0.2); color: #0066FA; border-color: #0066FA; font-weight: 600; }
                #xray-capture-popup .xray-pov-btn {
                    padding: 6px 12px; border-radius: 8px; border: 1px solid ${isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)'};
                    cursor: pointer; font-size: 11px; font-family: 'Poppins', sans-serif;
                    background: ${isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)'};
                    color: ${isDark ? '#ccc' : '#555'}; transition: all 0.15s ease; flex: 1; text-align: center;
                }
                #xray-capture-popup .xray-pov-btn:hover { background: rgba(0,102,250,0.15); }
                #xray-capture-popup .xray-pov-btn.active { background: rgba(0,102,250,0.2); color: #0066FA; border-color: #0066FA; font-weight: 600; }
                #xray-capture-popup .xray-start-btn {
                    width: 100%; padding: 10px; border-radius: 10px; border: none;
                    background: linear-gradient(135deg, #0066FA, #0052CC); color: #fff;
                    font-size: 13px; font-weight: 700; cursor: pointer; font-family: 'Poppins', sans-serif;
                    transition: all 0.2s ease; letter-spacing: 0.3px;
                }
                #xray-capture-popup .xray-start-btn:hover { background: linear-gradient(135deg, #3385FF, #0066FA); transform: translateY(-1px); box-shadow: 0 4px 16px rgba(0,102,250,0.4); }
                #xray-capture-popup .xray-start-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
                #xray-capture-popup .xray-start-btn.capturing { background: linear-gradient(135deg, #FF5E1F, #CC4A16); }
                #xray-capture-popup .xray-section-label { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; opacity: 0.6; }
                #xray-capture-popup .xray-status { padding: 8px 12px; border-radius: 8px; font-size: 11px; margin-top: 10px; display: none; font-family: 'SF Mono', monospace; max-height: 100px; overflow-y: auto; }
            </style>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="font-size: 14px; font-weight: 700; display: flex; align-items: center; gap: 8px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0066FA" stroke-width="2.5"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/></svg>
                    XRAY Capture
                </div>
                <button id="xray-close-btn" style="background: none; border: none; cursor: pointer; color: ${isDark ? '#888' : '#999'}; font-size: 18px; padding: 0 4px;">&times;</button>
            </div>
            <div style="font-size: 11px; opacity: 0.7; margin-bottom: 12px; padding: 6px 10px; background: ${isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)'}; border-radius: 8px;">
                <strong>${name1}</strong> ${intf1 ? '<span style="color:#0066FA">[' + intf1 + ']</span>' : ''} &harr; <strong>${name2}</strong> ${intf2 ? '<span style="color:#0066FA">[' + intf2 + ']</span>' : ''}
            </div>

            <div class="xray-section-label">Capture Mode</div>
            <div style="display: flex; gap: 6px; margin-bottom: 14px;">
                <button class="xray-mode-btn active" data-mode="cp">CP</button>
                <button class="xray-mode-btn" data-mode="dp">DP</button>
                <button class="xray-mode-btn" data-mode="dnaas-dp">DNAAS-DP</button>
            </div>

            <div class="xray-section-label">Duration</div>
            <div style="display: flex; gap: 4px; margin-bottom: 14px;">
                <button class="xray-opt-btn" data-dur="3">3s</button>
                <button class="xray-opt-btn" data-dur="5">5s</button>
                <button class="xray-opt-btn active" data-dur="10">10s</button>
                <button class="xray-opt-btn" data-dur="30">30s</button>
                <button class="xray-opt-btn" data-dur="60">60s</button>
            </div>

            <div class="xray-section-label">Output</div>
            <div style="display: flex; gap: 4px; margin-bottom: 14px;">
                <button class="xray-opt-btn active" data-out="mac" title="SCP to Mac + open Wireshark">Mac Wireshark</button>
                <button class="xray-opt-btn" data-out="pcap" title="Save pcap on server">pcap</button>
                <button class="xray-opt-btn" data-out="auto" title="Full analysis + report">auto</button>
            </div>

            <div class="xray-section-label">Device POV</div>
            <div style="display: flex; gap: 6px; margin-bottom: 16px;">
                <button class="xray-pov-btn active" data-pov="device1">${name1} &rarr;</button>
                <button class="xray-pov-btn" data-pov="device2">&larr; ${name2}</button>
            </div>

            <button class="xray-start-btn" id="xray-start-btn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="vertical-align: -2px; margin-right: 4px;"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/></svg>
                Start Capture
            </button>

            <div class="xray-status" id="xray-status" style="background: ${isDark ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.05)'}; color: ${isDark ? '#aaa' : '#555'};"></div>
        `;

        document.body.appendChild(popup);
        this._popup = popup;
        this._link = link;
        this._editor = editor;
        this._state = { mode: 'cp', duration: 10, output: 'mac', pov: 'device1' };

        // Viewport boundary check
        requestAnimationFrame(() => {
            const r = popup.getBoundingClientRect();
            if (r.right > window.innerWidth - 10) popup.style.left = `${window.innerWidth - r.width - 10}px`;
            if (r.bottom > window.innerHeight - 10) popup.style.top = `${screenPos.y - r.height - 10}px`;
            if (r.left < 10) popup.style.left = '10px';
        });

        // Mode buttons
        popup.querySelectorAll('.xray-mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                popup.querySelectorAll('.xray-mode-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this._state.mode = btn.dataset.mode;
            });
        });
        // Duration buttons
        popup.querySelectorAll('.xray-opt-btn[data-dur]').forEach(btn => {
            btn.addEventListener('click', () => {
                popup.querySelectorAll('.xray-opt-btn[data-dur]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this._state.duration = parseInt(btn.dataset.dur);
            });
        });
        // Output buttons
        popup.querySelectorAll('.xray-opt-btn[data-out]').forEach(btn => {
            btn.addEventListener('click', () => {
                popup.querySelectorAll('.xray-opt-btn[data-out]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this._state.output = btn.dataset.out;
            });
        });
        // POV buttons
        popup.querySelectorAll('.xray-pov-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                popup.querySelectorAll('.xray-pov-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this._state.pov = btn.dataset.pov;
            });
        });
        // Close
        popup.querySelector('#xray-close-btn').addEventListener('click', () => this.hide());
        // Start
        popup.querySelector('#xray-start-btn').addEventListener('click', () => this._startCapture());
        // Prevent canvas interactions
        popup.addEventListener('mousedown', e => e.stopPropagation());
        popup.addEventListener('click', e => e.stopPropagation());
        // Close on outside click
        this._outsideHandler = (e) => {
            if (!popup.contains(e.target)) this.hide();
        };
        setTimeout(() => document.addEventListener('mousedown', this._outsideHandler), 100);

        // Auto-detect available modes
        this._detectModes(editor, link, name1, name2);
    },

    hide() {
        if (this._popup) {
            this._popup.remove();
            this._popup = null;
        }
        if (this._outsideHandler) {
            document.removeEventListener('mousedown', this._outsideHandler);
            this._outsideHandler = null;
        }
        if (this._pollTimer) {
            clearInterval(this._pollTimer);
            this._pollTimer = null;
        }
    },

    async _detectModes(editor, link, name1, name2) {
        const dpBtn = this._popup?.querySelector('.xray-mode-btn[data-mode="dp"]');
        const dnaasBtn = this._popup?.querySelector('.xray-mode-btn[data-mode="dnaas-dp"]');
        try {
            const resp = await fetch(`/api/dnaas/device/${encodeURIComponent(name1)}/lldp`);
            if (resp.ok) {
                const data = await resp.json();
                const neighbors = data.neighbors || data.lldp_neighbors || [];
                const hasArista = neighbors.some(n => /arista|eos|veos/i.test(n.neighbor || ''));
                const hasDnaas = neighbors.some(n => /dnaas|leaf|spine/i.test(n.neighbor || ''));
                if (!hasArista && dpBtn) { dpBtn.disabled = true; dpBtn.title = 'No Arista mirror available'; }
                if (!hasDnaas && dnaasBtn) { dnaasBtn.disabled = true; dnaasBtn.title = 'No DNAAS leaf available'; }
            }
        } catch (e) {
            // Cannot detect — leave all enabled
        }
    },

    async _startCapture() {
        const btn = this._popup?.querySelector('#xray-start-btn');
        const status = this._popup?.querySelector('#xray-status');
        if (!btn || !status) return;

        if (this._activeCapture) {
            // Stop running capture
            try {
                await fetch(`/api/xray/stop/${this._activeCapture}`, { method: 'POST' });
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
        const intf = isPov1 ? (link.device1Interface || '') : (link.device2Interface || '');

        const body = {
            device: device?.label || '',
            mode: this._state.mode,
            interface: intf || 'any',
            duration: this._state.duration,
            output: this._state.output
        };

        btn.textContent = 'Starting...';
        btn.disabled = true;
        status.style.display = 'block';
        status.textContent = 'Initializing capture...';

        try {
            const resp = await fetch('/api/xray/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const result = await resp.json();
            if (result.error) {
                status.textContent = 'Error: ' + result.error;
                status.style.background = 'rgba(231,76,60,0.15)';
                status.style.color = '#e74c3c';
                btn.textContent = 'Start Capture';
                btn.disabled = false;
                return;
            }
            this._activeCapture = result.capture_id;
            editor._xrayCapturing = link.id;
            btn.textContent = 'Stop Capture';
            btn.classList.add('capturing');
            btn.disabled = false;
            status.textContent = 'Capturing...';
            status.style.background = 'rgba(0,102,250,0.1)';
            status.style.color = '#0066FA';
            editor.draw();

            // Poll for status
            this._pollTimer = setInterval(() => this._pollStatus(), 2000);
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
            const resp = await fetch(`/api/xray/status/${this._activeCapture}`);
            const data = await resp.json();
            const status = this._popup?.querySelector('#xray-status');
            if (!status) return;

            if (data.status === 'running') {
                const lines = data.output_lines || [];
                status.textContent = lines.length > 0 ? lines.slice(-5).join('\n') : 'Capturing...';
            } else if (data.status === 'completed') {
                status.style.background = 'rgba(39,174,96,0.15)';
                status.style.color = '#27ae60';
                status.textContent = 'Capture complete!' + (data.pcap_path ? '\nFile: ' + data.pcap_path : '');
                this._stopCapture();
            } else if (data.status === 'error') {
                status.style.background = 'rgba(231,76,60,0.15)';
                status.style.color = '#e74c3c';
                status.textContent = 'Error: ' + (data.error || 'Unknown error');
                this._stopCapture();
            }
        } catch (e) {
            // Poll failed, will retry
        }
    },

    _stopCapture() {
        if (this._pollTimer) {
            clearInterval(this._pollTimer);
            this._pollTimer = null;
        }
        this._activeCapture = null;
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
    }
};

console.log('[topology-xray-popup.js] XrayPopup loaded');
