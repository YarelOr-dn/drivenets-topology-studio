/**
 * topology-xray-popup.js - XRAY Capture Popup for Links
 * Shows DP/CP/DNAAS-DP capture options on selected device-to-device links.
 */

'use strict';

window.XrayPopup = {
    _popup: null,
    _activeCapture: null,
    _pollTimer: null,
    _temporarilyHidden: false,
    _lastState: null,

    show(editor, link, screenPos) {
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
        link._xrayCaptureActive = true;

        const device1 = editor.objects.find(d => d.id === link.device1);
        const device2 = editor.objects.find(d => d.id === link.device2);
        if (!device1 || !device2) return;
        this._device1 = device1;
        this._device2 = device2;

        const name1 = device1.label || 'Device 1';
        const name2 = device2.label || 'Device 2';
        const intf1 = link.device1Interface || link.linkDetails?.interfaceA || '';
        const intf2 = link.device2Interface || link.linkDetails?.interfaceB || '';
        const isDark = editor.darkMode;

        // Restore last state for this link, or use defaults
        const saved = this._lastState;
        const st = {
            mode: saved?.mode || 'cp',
            duration: saved?.duration || 10,
            output: saved?.output || 'mac',
            pov: saved?.pov || 'device1',
            direction: saved?.direction || 'both',
            filters: saved?.filters ? [...saved.filters] : [],
            excludeInternal: saved?.excludeInternal !== undefined ? saved.excludeInternal : true
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
                #xray-capture-popup .xray-mode-btn:disabled { opacity: 0.45; cursor: not-allowed; color: ${isDark ? '#777' : '#999'}; }
                #xray-capture-popup .xray-mode-btn .xray-mode-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; margin-right: 4px; vertical-align: middle; }
                #xray-capture-popup .xray-mode-btn:not(:disabled) .xray-mode-dot { background: #27ae60; box-shadow: 0 0 4px rgba(39,174,96,0.6); }
                #xray-capture-popup .xray-mode-btn:disabled .xray-mode-dot { background: rgba(128,128,128,0.5); }
                #xray-capture-popup .xray-mode-help { display: inline-flex; align-items: center; justify-content: center; width: 12px; height: 12px; border-radius: 50%; font-size: 8px; font-weight: 700; margin-left: 3px; vertical-align: middle; cursor: help; background: ${isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.08)'}; color: ${isDark ? '#8899aa' : '#666'}; position: relative; }
                #xray-capture-popup .xray-mode-help:hover { background: ${isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.12)'}; color: ${isDark ? '#aabbcc' : '#333'}; }
                #xray-capture-popup .xray-mode-help .xray-help-tip { display: none; position: absolute; bottom: 18px; left: 50%; transform: translateX(-50%); width: 280px; padding: 10px 12px; border-radius: 8px; font-size: 9px; font-weight: 400; line-height: 1.5; text-align: left; z-index: 10; pointer-events: none; background: ${isDark ? 'rgba(20,25,35,0.97)' : 'rgba(255,255,255,0.98)'}; color: ${isDark ? '#c8d0da' : '#333'}; border: 1px solid ${isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)'}; box-shadow: 0 4px 16px rgba(0,0,0,0.35); max-height: 320px; overflow-y: auto; }
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
                #xray-capture-popup .xray-status { padding: 6px 10px; border-radius: 6px; font-size: 10px; margin-top: 8px; display: none; font-family: 'SF Mono', monospace; max-height: 80px; overflow-y: auto; }
                #xray-capture-popup .xray-toggle-row { display: flex; align-items: center; gap: 6px; font-size: 10px; opacity: 0.85; margin-bottom: 8px; color: ${isDark ? '#c0c8d2' : '#444'}; }
                #xray-capture-popup .xray-toggle-row input[type="checkbox"] { width: 13px; height: 13px; accent-color: #0066FA; cursor: pointer; }
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
                <button class="xray-mode-btn${modeActive('cp')}" data-mode="cp" title="Control Plane - capture on DNOS device">CP</button>
                <button class="xray-mode-btn${modeActive('dp')}" data-mode="dp" disabled title="Checking availability..."><span class="xray-mode-dot"></span>Live Capture<span class="xray-mode-help">?<span class="xray-help-tip"><b>Live Data-Plane Capture (Double-SPAN)</b><br><br>Mirrors live traffic from a DNOS interface through an Arista switch to Wireshark on your Mac.<br><br><b>How it works:</b><br>1. Auto-configures DNOS service port-mirroring session<br>2. Auto-configures Arista monitor session (source &rarr; CPU)<br>3. Streams packets via tcpdump to your Mac / pcap file<br>4. Auto-cleans up both sessions when done<br><br><b>Requirements:</b><br>&bull; An Arista switch in the POV device's LLDP neighbors<br>&bull; SSH access to both the DUT and the Arista (credentials in XRAY config)<br>&bull; The DUT interface is taken from the link table or selected manually<br><br><b>No pre-configuration needed</b> -- port-mirroring and monitor sessions are created and removed automatically.</span></span></button>
                <button class="xray-mode-btn${modeActive('dnaas-dp')}" data-mode="dnaas-dp" disabled title="Checking DNAAS availability..."><span class="xray-mode-dot"></span>DP (DNAAS)</button>
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
                <input type="text" id="xray-ssh-host" placeholder="Host IP" style="width:100%;padding:6px 8px;margin-bottom:6px;border-radius:4px;font-size:12px;box-sizing:border-box;background:rgba(0,0,0,0.2);border:1px solid rgba(255,255,255,0.2);color:inherit;" />
                <input type="text" id="xray-ssh-user" placeholder="User (dnroot)" style="width:100%;padding:6px 8px;margin-bottom:6px;border-radius:4px;font-size:12px;box-sizing:border-box;background:rgba(0,0,0,0.2);border:1px solid rgba(255,255,255,0.2);color:inherit;" />
                <input type="password" id="xray-ssh-pass" placeholder="Password" style="width:100%;padding:6px 8px;border-radius:4px;font-size:12px;box-sizing:border-box;background:rgba(0,0,0,0.2);border:1px solid rgba(255,255,255,0.2);color:inherit;" />
            </div>

            <button class="xray-start-btn" id="xray-start-btn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="vertical-align: -2px; margin-right: 4px;"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/></svg>
                Start Capture
            </button>

            <div class="xray-status" id="xray-status" style="background: ${isDark ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.05)'}; color: ${isDark ? '#aaa' : '#555'};"></div>
        `;

        document.body.appendChild(popup);
        this._popup = popup;
        this._state = st;

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
            });
        });
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
            });
        });
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
        popup.querySelectorAll('.xray-pov-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                popup.querySelectorAll('.xray-pov-btn').forEach(b => {
                    b.classList.remove('active');
                    b.style.background = inactiveBg;
                    b.style.color = inactiveColor;
                });
                btn.classList.add('active');
                btn.style.background = activeBg;
                btn.style.color = activeColor;
                this._state.pov = btn.dataset.pov;
                updateSshPromptVisibility();
                if (this._lldpCache) {
                    this._applyDetectionForPov();
                    applyModeUi(this._state.mode);
                }
            });
        });
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
        const name = (neighbor.neighbor || '').toLowerCase();
        const port = (neighbor.remote_port || '').toLowerCase();
        if (/arista|eos|veos/.test(name)) return true;
        if (port.startsWith('ethernet')) return true;
        if (/^dn-leaf/i.test(neighbor.neighbor || '')) return true;
        return false;
    },

    _isDnaas(neighbor) {
        return /dnaas/i.test(neighbor.neighbor || '');
    },

    _lldpDeviceCache: {},

    async _fetchLldpForDevice(device, signal) {
        const candidates = [
            device?.sshConfig?.host,
            device?.deviceSerial,
            device?.label
        ].filter(Boolean);
        const unique = [...new Set(candidates)];
        const cacheKey = unique.join('|');
        if (this._lldpDeviceCache[cacheKey]) {
            console.log('[XRAY lldp] Cache hit for', cacheKey);
            return this._lldpDeviceCache[cacheKey];
        }
        for (const name of unique) {
            if (signal?.aborted) return [];
            try {
                const ctrl = new AbortController();
                const timer = setTimeout(() => ctrl.abort(), 15000);
                if (signal) signal.addEventListener('abort', () => ctrl.abort());
                const resp = await fetch(`/api/dnaas/device/${encodeURIComponent(name)}/lldp`, { signal: ctrl.signal });
                clearTimeout(timer);
                if (resp.ok) {
                    const data = await resp.json();
                    const neighbors = data.neighbors || data.lldp_neighbors || [];
                    if (neighbors.length > 0) {
                        this._lldpDeviceCache[cacheKey] = neighbors;
                        return neighbors;
                    }
                }
            } catch (_) {}
        }
        return [];
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
        const candidates = [
            device?.sshConfig?.host,
            device?.deviceSerial,
            device?.label
        ].filter(Boolean);
        const unique = [...new Set(candidates)];
        let interfaces = [];
        for (const name of unique) {
            try {
                const ctrl = new AbortController();
                const timer = setTimeout(() => ctrl.abort(), 15000);
                const resp = await fetch(`/api/dnaas/device/${encodeURIComponent(name)}/interfaces`, { signal: ctrl.signal });
                clearTimeout(timer);
                if (resp.ok) {
                    const data = await resp.json();
                    interfaces = data.interfaces || Object.keys(data).filter(k => k !== 'error') || [];
                    if (interfaces.length > 0) break;
                }
            } catch (_) {}
        }
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

        const maxRetries = 2;
        for (let attempt = 0; attempt <= maxRetries; attempt++) {
            if (detectCtrl.signal.aborted) return;
            try {
                const [neighbors1, neighbors2] = await Promise.all([
                    this._fetchLldpForDevice(device1, detectCtrl.signal),
                    this._fetchLldpForDevice(device2, detectCtrl.signal)
                ]);
                console.log(`[XRAY detect] attempt ${attempt}: ${neighbors1.length} + ${neighbors2.length} neighbors`);

                if (neighbors1.length === 0 && neighbors2.length === 0 && attempt < maxRetries) {
                    const waitSec = (attempt + 1) * 3;
                    setHint(`No LLDP yet -- retrying in ${waitSec}s (API may be warming up)...`);
                    console.log(`[XRAY detect] No neighbors, retrying in ${waitSec}s...`);
                    await new Promise(r => setTimeout(r, waitSec * 1000));
                    continue;
                }

                this._lldpCache = { device1: neighbors1, device2: neighbors2 };
                this._applyDetectionForPov();
                return;
            } catch (e) {
                console.error(`[XRAY detect] attempt ${attempt} error:`, e);
                if (attempt < maxRetries) {
                    setHint('Detection error -- retrying...');
                    await new Promise(r => setTimeout(r, 2000));
                    continue;
                }
                setHint('Detection failed -- check console');
            }
        }
    },

    _applyDetectionForPov() {
        const dpBtn = this._popup?.querySelector('.xray-mode-btn[data-mode="dp"]');
        const dnaasBtn = this._popup?.querySelector('.xray-mode-btn[data-mode="dnaas-dp"]');
        const hintEl = this._popup?.querySelector('#xray-mode-hint');
        const setHint = (msg) => { if (hintEl) hintEl.textContent = msg; };
        if (!this._lldpCache) return;

        const isPov1 = this._state.pov === 'device1';
        const povNeighbors = isPov1 ? this._lldpCache.device1 : this._lldpCache.device2;
        const allNeighbors = [...this._lldpCache.device1, ...this._lldpCache.device2];

        const aristaNeighbor = povNeighbors.find(n => this._isArista(n));
        const hasArista = !!aristaNeighbor;

        const hasDnaas = allNeighbors.some(n => this._isDnaas(n));
        const povLabel = isPov1 ? 'device1' : 'device2';
        console.log(`[XRAY detect] POV=${povLabel} | Arista on POV: ${hasArista} | DNAAS: ${hasDnaas}`);

        if (hasArista) {
            const link = this._link;
            const linkIntf = isPov1
                ? (link.device1Interface || link.linkDetails?.interfaceA || '')
                : (link.device2Interface || link.linkDetails?.interfaceB || '');
            this._aristaInfo = {
                host: aristaNeighbor.neighbor,
                srcPort: aristaNeighbor.remote_port,
                dutInterface: linkIntf || '',
                aristaPort: aristaNeighbor.interface || ''
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
            dpBtn.title = `Live stream via ${aristaNeighbor.neighbor}`;
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
            dpBtn.title = 'Live Capture requires an Arista switch visible in LLDP neighbors of this POV device. Ensure the Arista is connected and LLDP is enabled on both sides.';
            hints.push('Live Capture: No Arista in LLDP -- needs Arista connected to this device');
            if (intfRow) intfRow.style.display = 'none';
        }
        if (hasDnaas && dnaasBtn) {
            dnaasBtn.disabled = false;
            dnaasBtn.title = 'Data Plane via DNAAS leaf';
            const dnaasNeighbor = allNeighbors.find(n => this._isDnaas(n));
            if (dnaasNeighbor) {
                this._dnaasInfo = {
                    leafHost: dnaasNeighbor.neighbor,
                    sourcePort: dnaasNeighbor.remote_port,
                    dutInterface: dnaasNeighbor.interface
                };
                console.log('[XRAY detect] DNAAS info:', this._dnaasInfo);
            }
        } else if (dnaasBtn) {
            dnaasBtn.disabled = true;
            dnaasBtn.title = 'No DNAAS leaf available - no DNAAS neighbor in LLDP';
            hints.push('DP (DNAAS): No DNAAS leaf detected');
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
    },

    async _startCapture() {
        const btn = this._popup?.querySelector('#xray-start-btn');
        const status = this._popup?.querySelector('#xray-status');
        if (!btn || !status) return;

        if (this._activeCapture) {
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
        const intf = isPov1 ? (link.device1Interface || link.linkDetails?.interfaceA || '') : (link.device2Interface || link.linkDetails?.interfaceB || '');

        if (!device) {
            editor.showToast('Device not found', 'error');
            return;
        }

        let dutHost = '';
        const hasSsh = device.sshConfig?.host || device.deviceAddress;
        if (!hasSsh) {
            const sshHost = this._popup?.querySelector('#xray-ssh-host')?.value?.trim();
            const sshUser = this._popup?.querySelector('#xray-ssh-user')?.value?.trim() || 'dnroot';
            const sshPass = this._popup?.querySelector('#xray-ssh-pass')?.value || '';
            if (!sshHost) {
                editor.showToast('Enter device host (IP) to capture', 'warning');
                return;
            }
            device.sshConfig = { host: sshHost, user: sshUser, password: sshPass };
            device.deviceAddress = `${sshUser}@${sshHost}`;
            if (editor.saveState) editor.saveState();
            dutHost = sshHost;
        } else {
            dutHost = (device.sshConfig && device.sshConfig.host) || (device.deviceAddress ? String(device.deviceAddress).split('@')[1] : '');
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
            cleanup_server_pcap: cleanupToggle ? cleanupToggle.checked : true
        };

        if (this._state.mode === 'dp' && this._aristaInfo) {
            body.arista_host = this._aristaInfo.host;
            body.arista_src_port = this._aristaInfo.srcPort;
            const manualInput = this._popup?.querySelector('#xray-intf-manual');
            const selectedIntf = this._aristaInfo.dutInterface || manualInput?.value?.trim() || '';
            if (selectedIntf) {
                body.interface = selectedIntf;
            } else {
                editor.showToast('Select or enter source interface for Live Capture', 'warning');
                return;
            }
        }

        if (this._state.mode === 'dnaas-dp' && this._dnaasInfo) {
            body.dnaas_leaf_host = this._dnaasInfo.leafHost;
            body.dnaas_leaf_source_port = this._dnaasInfo.sourcePort;
        }

        const needsMac = (body.output === 'mac' || body.output === 'mac-live');
        if (needsMac) {
            btn.textContent = 'Verifying Mac...';
            btn.disabled = true;
            status.style.display = 'block';
            status.textContent = 'Checking Mac reachability...';
            try {
                const vResp = await fetch('/api/xray/verify-mac', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                });
                const vResult = await vResp.json();
                if (!vResult.reachable) {
                    const currentIp = vResult.ip || '(not set)';
                    status.style.background = 'rgba(255,165,0,0.12)';
                    status.style.color = '#FF9500';
                    status.innerHTML = '';
                    const msg = document.createElement('div');
                    msg.textContent = `Mac unreachable at ${currentIp} -- update IP to continue.`;
                    msg.style.marginBottom = '6px';
                    status.appendChild(msg);
                    const row = document.createElement('div');
                    row.style.cssText = 'display:flex;gap:6px;align-items:center;';
                    const input = document.createElement('input');
                    input.type = 'text';
                    input.placeholder = 'New Mac IP...';
                    input.value = currentIp !== '(not set)' ? currentIp : '';
                    const isDark = document.body.classList.contains('dark-mode');
                    input.style.cssText = `flex:1;padding:5px 8px;border-radius:4px;border:1px solid ${isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)'};background:${isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.03)'};color:${isDark ? '#c8d0da' : '#333'};font-size:10px;font-family:'Space Grotesk',monospace;outline:none;`;
                    input.addEventListener('keydown', e => e.stopPropagation());
                    const retryBtn = document.createElement('button');
                    retryBtn.textContent = 'Retry';
                    retryBtn.style.cssText = `padding:5px 12px;border-radius:4px;border:none;background:#0066FA;color:#fff;font-size:10px;cursor:pointer;font-weight:600;`;
                    const pcapBtn = document.createElement('button');
                    pcapBtn.textContent = 'Use pcap';
                    pcapBtn.style.cssText = `padding:5px 10px;border-radius:4px;border:1px solid ${isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)'};background:transparent;color:${isDark ? '#8899aa' : '#666'};font-size:10px;cursor:pointer;`;
                    row.appendChild(input);
                    row.appendChild(retryBtn);
                    row.appendChild(pcapBtn);
                    status.appendChild(row);
                    btn.textContent = 'Start Capture';
                    btn.disabled = false;
                    retryBtn.onclick = async () => {
                        const newIp = input.value.trim();
                        if (!newIp) return;
                        retryBtn.textContent = 'Checking...';
                        retryBtn.disabled = true;
                        try {
                            await fetch('/api/xray/config', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ mac: { ip_vpn: newIp } })
                            });
                            const r2 = await fetch('/api/xray/verify-mac', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ip: newIp }) });
                            const v2 = await r2.json();
                            if (v2.reachable) {
                                status.style.background = 'rgba(39,174,96,0.15)';
                                status.style.color = '#27ae60';
                                status.textContent = `Mac verified at ${newIp} -- click Start Capture`;
                            } else {
                                retryBtn.textContent = 'Retry';
                                retryBtn.disabled = false;
                                msg.textContent = `Still unreachable at ${newIp} -- check IP and try again.`;
                            }
                        } catch (e) {
                            retryBtn.textContent = 'Retry';
                            retryBtn.disabled = false;
                            msg.textContent = `Verification failed: ${e.message}`;
                        }
                    };
                    pcapBtn.onclick = () => {
                        body.output = 'pcap';
                        this._state.output = 'pcap';
                        status.textContent = 'Switched to pcap output. Click Start Capture.';
                        status.style.background = 'rgba(0,102,250,0.1)';
                        status.style.color = '#0066FA';
                    };
                    input.addEventListener('keydown', e => { if (e.key === 'Enter') retryBtn.click(); });
                    input.focus();
                    return;
                }
            } catch (verr) {
                console.warn('[XRAY] Mac verify-mac check failed, proceeding:', verr);
            }
        }

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
            btn.classList.add('capturing');
            btn.disabled = false;
            status.style.background = 'rgba(0,102,250,0.1)';
            status.style.color = '#0066FA';
            editor.draw();

            this._captureStart = Date.now();
            this._captureDuration = this._state.duration;
            this._updateCountdown(btn, status);
            this._countdownTimer = setInterval(() => this._updateCountdown(btn, status), 500);

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
            const btn = this._popup?.querySelector('#xray-start-btn');
            const popupGone = !this._popup;

            if (data.status === 'running') {
                // Countdown handles the display while timer is active
            } else if (data.status === 'completed') {
                // Stop countdown immediately so the button doesn't say "Finishing..."
                if (this._countdownTimer) {
                    clearInterval(this._countdownTimer);
                    this._countdownTimer = null;
                }
                this._captureStart = null;
                this._captureDuration = null;

                const isMacOutput = this._state?.output === 'mac' || this._state?.mode === 'dp';
                if (data.mac_delivery_failed && isMacOutput) {
                    if (status) {
                        this._showMacFailurePrompt(status, data.local_pcap_path || data.pcap_path);
                    } else if (popupGone && this._editor) {
                        this._editor.showToast('Capture done but Mac delivery failed -- reopen XRAY to retry', 'warning');
                    }
                } else {
                    const fileName = data.pcap_path ? data.pcap_path.split('/').pop() : '';
                    const outputLines = data.output_lines || [];
                    const actuallyDelivered = outputLines.some(l => /delivered to mac|opened in wireshark/i.test(l));
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
                status.style.background = 'rgba(231,76,60,0.15)';
                status.style.color = '#e74c3c';
                status.textContent = 'Error: ' + (data.error || 'Unknown error');
                }
                if (popupGone && this._editor) {
                    this._editor.showToast('Capture error: ' + (data.error || 'Unknown'), 'error');
                }
                this._stopCapture();
            }
        } catch (e) {
            // Poll failed, will retry
        }
    },

    _showMacFailurePrompt(statusEl, localPcapPath) {
        statusEl.style.background = 'rgba(255, 165, 0, 0.12)';
        statusEl.style.color = '#FF9500';
        statusEl.innerHTML = '';

        const msg = document.createElement('div');
        msg.textContent = 'Capture saved on server but Mac delivery failed -- IP may have changed.';
        msg.style.marginBottom = '8px';
        statusEl.appendChild(msg);

        if (localPcapPath) {
            const pathLine = document.createElement('div');
            pathLine.textContent = 'Server file: ' + localPcapPath;
            pathLine.style.cssText = 'font-size: 11px; opacity: 0.7; margin-bottom: 8px; word-break: break-all;';
            statusEl.appendChild(pathLine);
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
            fetch('/api/xray/config').then(r => r.json()).then(cfg => {
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
                const resp = await fetch('/api/xray/redeliver', {
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

        row.appendChild(input);
        row.appendChild(retryBtn);
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
        }

        // Timeout delivery after 45s -- Mac IP may be unreachable
        const DELIVERY_TIMEOUT_MS = 45000;
        if (delivering && this._deliveryStartedAt && (Date.now() - this._deliveryStartedAt > DELIVERY_TIMEOUT_MS)) {
            if (this._countdownTimer) {
                clearInterval(this._countdownTimer);
                this._countdownTimer = null;
            }
            if (btn) {
                btn.innerHTML = 'Start Capture';
                btn.disabled = false;
                btn.classList.remove('capturing');
            }
            if (statusEl) {
                statusEl.style.background = 'rgba(231,76,60,0.15)';
                statusEl.style.color = '#e74c3c';
                statusEl.textContent = 'Mac delivery timed out -- Mac IP may be unreachable. Try pcap output instead.';
            }
            this._deliveryStartedAt = null;
            this._stopCapture();
            return;
        }

        if (btn) {
            if (secs > 0) {
                btn.innerHTML = `<span style="font-variant-numeric: tabular-nums;">${secs}s</span> remaining &mdash; Stop`;
            } else {
                btn.innerHTML = 'Delivering to Mac...';
                btn.disabled = true;
            }
        }
        if (statusEl) {
            const outputLabel = this._state.output === 'mac' ? 'Opening on Mac' : 'Saving pcap';
            const phase = secs > 0 ? secs + 's left' : 'delivering...';
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
