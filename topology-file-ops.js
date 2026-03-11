/**
 * topology-file-ops.js - File Operations Module
 * 
 * All save/load/export/import, bug topologies, custom sections,
 * and clear/new topology operations extracted from topology.js.
 * 
 * Methods are injected onto the editor prototype at load time.
 * 
 * @version 1.0.0
 * @date 2026-02-23
 */

'use strict';

window.FileOps = {

    // ========================================================================
    // TOPOLOGY INDICATOR
    // ========================================================================

    updateTopologyIndicator(name, domainName, domainColor, sectionId) {
        const el = document.getElementById('topo-active-indicator');
        const nameEl = document.getElementById('topo-active-name');
        const domEl = document.getElementById('topo-active-domain');
        const sepEl = document.getElementById('topo-active-sep');
        const innerEl = document.getElementById('topo-active-inner');
        const dotEl = document.getElementById('topo-active-color-dot');
        if (!el || !nameEl) return;
        if (!name) { el.style.display = 'none'; return; }

        const applyContent = () => {
            nameEl.textContent = name;
            if (domEl && domainName) {
                domEl.textContent = domainName;
                domEl.style.display = '';
                if (sepEl) sepEl.style.display = '';
            } else {
                if (domEl) domEl.style.display = 'none';
                if (sepEl) sepEl.style.display = 'none';
            }
            if (domainColor && innerEl) {
                innerEl.style.background = `linear-gradient(135deg, ${domainColor}, ${domainColor})`;
                innerEl.style.borderColor = `${domainColor}88`;
            } else if (innerEl) {
                innerEl.style.background = 'linear-gradient(135deg, #0066FA, #0052cc)';
                innerEl.style.borderColor = 'rgba(255,255,255,0.2)';
            }
            if (dotEl) {
                dotEl.style.background = domainColor || '#0066fa';
                dotEl.style.boxShadow = `0 0 6px ${domainColor || '#0066fa'}`;
            }
        };

        if (innerEl) innerEl.style.transition = 'background 0.3s ease, border-color 0.3s ease, opacity 0.2s ease, transform 0.2s ease';

        const wasVisible = el.style.display !== 'none';
        if (wasVisible && nameEl.textContent && nameEl.textContent !== name) {
            el.style.opacity = '0';
            el.style.transform = 'translateY(4px)';
            setTimeout(() => {
                applyContent();
                el.style.display = '';
                requestAnimationFrame(() => {
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                });
            }, 180);
        } else {
            applyContent();
            el.style.display = '';
            if (!wasVisible) {
                el.style.opacity = '0';
                el.style.transform = 'translateY(4px)';
                requestAnimationFrame(() => {
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                });
            }
        }
        try {
            localStorage.setItem('topo_active', JSON.stringify({ name, domain: domainName || '', color: domainColor || '', sectionId: sectionId || '' }));
        } catch (_) {}
        FileOps._refreshDomainDots(sectionId, name);
    },

    clearTopologyIndicator() {
        const el = document.getElementById('topo-active-indicator');
        if (el) el.style.display = 'none';
        const dotsEl = document.getElementById('topo-active-dots');
        if (dotsEl) { dotsEl.innerHTML = ''; dotsEl.style.display = 'none'; }
        FileOps._domainTopoCache = null;
        FileOps._domainTopoCacheId = null;
        try { localStorage.removeItem('topo_active'); } catch (_) {}
    },

    restoreTopologyIndicator() {
        try {
            const raw = localStorage.getItem('topo_active');
            if (!raw) return;
            const d = JSON.parse(raw);
            if (d && d.name) FileOps.updateTopologyIndicator(d.name, d.domain || null, d.color || null, d.sectionId || null);
        } catch (_) {}
        FileOps._initIndicatorSaveBtn();
    },

    _initIndicatorSaveBtn() {
        const saveEl = document.getElementById('topo-active-save');
        if (!saveEl || saveEl._wired) return;
        saveEl._wired = true;
        saveEl.addEventListener('mouseenter', () => { saveEl.style.background = 'rgba(255,255,255,0.25)'; saveEl.style.borderColor = 'rgba(255,255,255,0.35)'; });
        saveEl.addEventListener('mouseleave', () => { saveEl.style.background = 'rgba(255,255,255,0.12)'; saveEl.style.borderColor = 'rgba(255,255,255,0.2)'; });
        saveEl.addEventListener('click', async () => {
            const editor = window.topologyEditor || window.editor;
            if (!editor || !editor.objects || editor.objects.length === 0) return;
            let info;
            try { info = JSON.parse(localStorage.getItem('topo_active')); } catch (_) {}
            // Resolve sectionId: try stored value, then match by domain name
            let sectionId = info?.sectionId;
            if (!sectionId && info?.domain && editor._customSections) {
                const match = editor._customSections.find(s => s.name === info.domain);
                if (match) sectionId = match.id;
            }
            // If still no section, use the first available domain
            if (!sectionId && editor._customSections && editor._customSections.length > 0) {
                sectionId = editor._customSections[0].id;
            }
            if (!sectionId || !info?.name) {
                editor.showToast('No domain to save to', 'warning');
                return;
            }
            const origSvg = saveEl.innerHTML;
            saveEl.style.opacity = '0.5';
            saveEl.style.pointerEvents = 'none';
            try {
                const resp = await fetch('/api/sections/' + sectionId + '/save', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: info.name, topology: FileOps.generateTopologyData(editor) })
                });
                const result = await resp.json();
                if (result.error) { editor.showToast('Save failed: ' + result.error, 'error'); }
                else {
                    // Update stored info with resolved sectionId
                    const sec = (editor._customSections || []).find(s => s.id === sectionId);
                    if (sec) FileOps.updateTopologyIndicator(info.name, sec.name, sec.color, sectionId);
                    saveEl.innerHTML = '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>';
                    editor.showToast('Saved ' + info.name, 'success');
                    setTimeout(() => { saveEl.innerHTML = origSvg; }, 1200);
                }
            } catch (err) { editor.showToast('Save failed: ' + err.message, 'error'); }
            saveEl.style.opacity = '1';
            saveEl.style.pointerEvents = 'auto';
        });
    },

    // ========================================================================
    // DOMAIN DOT NAVIGATION
    // ========================================================================

    _domainTopoCache: null,
    _domainTopoCacheId: null,

    async _refreshDomainDots(sectionId, currentName) {
        const dotsEl = document.getElementById('topo-active-dots');
        if (!dotsEl) return;
        if (!sectionId) { dotsEl.style.display = 'none'; return; }

        try {
            const resp = await fetch(`/api/sections/${sectionId}/topologies`);
            const data = await resp.json();
            const topos = (data.topologies || []).map(t => t.filename || t.name || '');
            if (topos.length <= 1) { dotsEl.style.display = 'none'; FileOps._domainTopoCache = null; return; }

            FileOps._domainTopoCache = topos;
            FileOps._domainTopoCacheId = sectionId;

            const currentFile = (currentName || '').replace(/\.json$/i, '');
            dotsEl.innerHTML = '';
            dotsEl.style.display = 'flex';

            let activeDotTip = null;
            const removeDotTip = () => { if (activeDotTip) { activeDotTip.remove(); activeDotTip = null; } };

            topos.forEach((filename, idx) => {
                const topoName = filename.replace(/\.json$/i, '');
                const isCurrent = topoName === currentFile;
                const keyNum = idx < 9 ? String(idx + 1) : '';
                const dot = document.createElement('button');
                dot.style.cssText = `
                    width: ${isCurrent ? 10 : 6}px; height: ${isCurrent ? 10 : 6}px;
                    border-radius: 50%; border: none; padding: 0; cursor: pointer;
                    background: ${isCurrent ? '#fff' : 'rgba(255,255,255,0.35)'};
                    box-shadow: ${isCurrent ? '0 0 6px rgba(255,255,255,0.6)' : 'none'};
                    transition: all 0.15s ease; flex-shrink: 0; position: relative;
                `;
                dot.onmouseenter = () => {
                    if (!isCurrent) { dot.style.background = 'rgba(255,255,255,0.7)'; dot.style.transform = 'scale(1.4)'; }
                    removeDotTip();
                    const dr = dot.getBoundingClientRect();
                    const tip = document.createElement('div');
                    tip.style.cssText = `
                        position:fixed; z-index:100001; pointer-events:none;
                        bottom:${window.innerHeight - dr.top + 6}px; left:${dr.left + dr.width / 2}px;
                        transform:translateX(-50%); display:flex; align-items:center; gap:5px;
                        padding:4px 8px; border-radius:6px; white-space:nowrap;
                        background:rgba(15,15,30,0.95); box-shadow:0 3px 12px rgba(0,0,0,0.4);
                        opacity:0; transition:opacity 0.08s ease;
                    `;
                    const nameSpan = document.createElement('span');
                    nameSpan.textContent = topoName;
                    nameSpan.style.cssText = 'font-size:10px;color:rgba(255,255,255,0.9);font-weight:500;font-family:Poppins,-apple-system,sans-serif;max-width:180px;overflow:hidden;text-overflow:ellipsis;';
                    tip.appendChild(nameSpan);
                    if (keyNum) {
                        const kbd = document.createElement('kbd');
                        kbd.textContent = keyNum;
                        kbd.style.cssText = `
                            display:inline-block; min-width:15px; text-align:center;
                            padding:1px 4px; font-size:9px; font-weight:600;
                            font-family:-apple-system,'SF Mono',Menlo,Consolas,monospace;
                            background:linear-gradient(180deg,rgba(255,255,255,0.18),rgba(255,255,255,0.06));
                            border:1px solid rgba(255,255,255,0.22); border-bottom-width:2px;
                            border-radius:3px; color:rgba(255,255,255,0.9);
                            box-shadow:0 1px 0 rgba(0,0,0,0.35);
                        `;
                        tip.appendChild(kbd);
                    }
                    document.body.appendChild(tip);
                    requestAnimationFrame(() => { tip.style.opacity = '1'; });
                    activeDotTip = tip;
                };
                dot.onmouseleave = () => {
                    if (!isCurrent) { dot.style.background = 'rgba(255,255,255,0.35)'; dot.style.transform = 'scale(1)'; }
                    removeDotTip();
                };
                dot.onclick = (ev) => { ev.stopPropagation(); removeDotTip(); FileOps._navigateToTopology(idx); };
                dotsEl.appendChild(dot);
            });
        } catch (_) {
            dotsEl.style.display = 'none';
        }
    },

    async _navigateToTopology(index) {
        const topos = FileOps._domainTopoCache;
        const sectionId = FileOps._domainTopoCacheId;
        if (!topos || !sectionId || index < 0 || index >= topos.length) return;

        const editor = window.topologyEditor || window.editor;
        if (!editor) return;

        const filename = topos[index];
        const topoName = filename.replace(/\.json$/i, '');

        let info;
        try { info = JSON.parse(localStorage.getItem('topo_active')); } catch (_) {}
        const currentName = (info?.name || '').replace(/\.json$/i, '');
        if (topoName === currentName) return;

        try {
            const resp = await fetch(`/api/sections/${sectionId}/topologies/${filename}`);
            const data = await resp.json();
            if (data.error) { editor.showToast(data.error, 'error'); return; }

            const sec = (editor._customSections || []).find(s => s.id === sectionId);
            editor.loadTopologyFromData(data);
            FileOps.updateTopologyIndicator(topoName, sec?.name || info?.domain || '', sec?.color || info?.color || '', sectionId);
            editor.showToast(`${topoName}  (${index + 1}/${topos.length})`, 'success');
        } catch (err) {
            editor.showToast('Failed to load: ' + err.message, 'error');
        }
    },

    navigateTopoByOffset(offset) {
        const topos = FileOps._domainTopoCache;
        if (!topos || topos.length <= 1) return;
        let info;
        try { info = JSON.parse(localStorage.getItem('topo_active')); } catch (_) {}
        const currentName = (info?.name || '').replace(/\.json$/i, '');
        const currentIdx = topos.findIndex(f => f.replace(/\.json$/i, '') === currentName);
        if (currentIdx < 0) return;
        const newIdx = (currentIdx + offset + topos.length) % topos.length;
        FileOps._navigateToTopology(newIdx);
    },

    // ========================================================================
    // NEW / CLEAR CANVAS
    // ========================================================================

    confirmNewTopology(editor) {
        if (editor.objects.length === 0) {
            FileOps.performClearCanvas(editor);
            editor.showToast('New topology created', 'success');
            return;
        }
        FileOps.showClearConfirmation(editor);
    },

    clearCanvas(editor) {
        FileOps.showClearConfirmation(editor);
    },

    showClearConfirmation(editor) {
        const existing = document.getElementById('clear-confirmation');
        if (existing) existing.remove();
        
        const dropdown = document.createElement('div');
        dropdown.id = 'clear-confirmation';
        dropdown.style.cssText = `
            position: fixed;
            top: 56px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(135deg, rgba(30, 20, 20, 0.92), rgba(20, 12, 12, 0.96));
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(239, 68, 68, 0.35);
            border-radius: 12px;
            padding: 16px 20px;
            z-index: 10001;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5), 0 0 12px rgba(239, 68, 68, 0.15);
            max-width: 320px;
            color: #e2e8f0;
            font-family: 'Poppins', -apple-system, sans-serif;
            animation: liquidDropdownFadeIn 0.2s ease-out;
        `;
        
        const deviceCount = editor.objects.filter(o => o.type === 'device').length;
        const linkCount = editor.objects.filter(o => o.type === 'link' || o.type === 'unbound').length;
        
        dropdown.innerHTML = `
            <div style="font-size: 14px; font-weight: 600; color: #ef4444; margin-bottom: 8px;">Clear canvas?</div>
            <div style="font-size: 12px; color: #94a3b8; margin-bottom: 12px;">
                ${deviceCount} devices, ${linkCount} links will be removed.
            </div>
            <div style="display: flex; gap: 8px;">
                <button id="confirm-clear-yes" style="
                    flex: 1; padding: 7px 0; background: #ef4444; color: #fff; border: none;
                    border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600;
                    font-family: inherit; transition: background 0.15s;
                ">Clear All</button>
                <button id="confirm-clear-no" style="
                    flex: 1; padding: 7px 0; background: rgba(255,255,255,0.08); color: #94a3b8;
                    border: 1px solid rgba(255,255,255,0.12); border-radius: 6px; cursor: pointer;
                    font-size: 12px; font-family: inherit; transition: background 0.15s;
                ">Cancel</button>
            </div>
        `;
        
        document.body.appendChild(dropdown);
        
        document.getElementById('confirm-clear-yes')?.addEventListener('click', () => {
            FileOps.performClearCanvas(editor);
            document.body.removeChild(dropdown);
            if (editor.debugger) editor.debugger.logSuccess('Canvas cleared');
        });
        
        document.getElementById('confirm-clear-no')?.addEventListener('click', () => {
            document.body.removeChild(dropdown);
            if (editor.debugger) editor.debugger.logInfo('Clear cancelled');
        });
        
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                if (document.body.contains(dropdown)) document.body.removeChild(dropdown);
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);
    },

    performClearCanvas(editor) {
        if (editor._clearBDState) editor._clearBDState();
        editor.objects = [];
        editor.selectedObject = null;
        editor.selectedObjects = [];
        editor.deviceIdCounter = 0;
        editor.linkIdCounter = 0;
        editor.textIdCounter = 0;
        editor.deviceCounters = { router: 0, switch: 0 };
        editor.updatePropertiesPanel();
        editor.draw();
        editor.saveState();
        FileOps.clearTopologyIndicator();
    },

    // ========================================================================
    // GENERATE / SAVE / LOAD / EXPORT
    // ========================================================================

    generateTopologyData(editor) {
        return {
            version: '1.0',
            objects: editor.objects.map(obj => ({ ...obj })),
            metadata: {
                deviceIdCounter: editor.deviceIdCounter,
                linkIdCounter: editor.linkIdCounter,
                textIdCounter: editor.textIdCounter,
                linkCurveMode: editor.linkCurveMode,
                globalCurveMode: editor.globalCurveMode,
                linkContinuousMode: editor.linkContinuousMode,
                linkStyle: editor.linkStyle,
                showLinkTypeLabels: editor.showLinkTypeLabels,
                deviceNumbering: editor.deviceNumbering,
                deviceCollision: editor.deviceCollision,
                movableDevices: editor.movableDevices,
                magneticFieldStrength: editor.magneticFieldStrength,
                gridZoomEnabled: editor.gridZoomEnabled
            }
        };
    },

    quickSaveTopology(editor) {
        const data = FileOps.generateTopologyData(editor);
        localStorage.setItem('topology_current', JSON.stringify(data));
        
        if (editor.files) {
            try {
                const rd = localStorage.getItem(editor.files.recoveryKey);
                if (rd) {
                    const rData = JSON.parse(rd);
                    rData.sessionId = editor.files.sessionId;
                    rData.objects = editor.objects;
                    localStorage.setItem(editor.files.recoveryKey, JSON.stringify(rData));
                }
            } catch (_) {}
        }
        
        const deviceCount = editor.objects.filter(o => o.type === 'device').length;
        const linkCount = editor.objects.filter(o => o.type === 'link' || o.type === 'unbound').length;
        editor.showToast(`Saved: ${deviceCount} devices, ${linkCount} links`, 'success');
    },

    _cmdSave(editor) {
        if (editor.objects.length === 0) { editor.showToast('Nothing to save — canvas is empty', 'warning'); return; }
        let info;
        try { info = JSON.parse(localStorage.getItem('topo_active')); } catch (_) {}
        if (info && info.sectionId && info.name) {
            const topoData = FileOps.generateTopologyData(editor);
            const safeName = info.name.replace(/\.json$/i, '');
            fetch(`/api/sections/${info.sectionId}/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: safeName, topology: topoData })
            }).then(r => r.json()).then(result => {
                if (result.error) { editor.showToast('Save failed: ' + result.error, 'error'); return; }
                editor.showToast(`Saved "${safeName}" → ${info.domain || 'domain'}`, 'success');
                FileOps.quickSaveTopology(editor);
            }).catch(err => {
                editor.showToast('Save failed: ' + err.message, 'error');
            });
        } else {
            FileOps.quickSaveToDomain(editor);
        }
    },

    quickSaveToDomain(editor) {
        if (editor.objects.length === 0) { editor.showToast('Nothing to save — canvas is empty', 'warning'); return; }
        const sections = editor._customSections || [];
        if (sections.length === 0) { editor.showToast('No domains exist. Create one in Topology Domains first.', 'warning'); return; }

        const stale = document.getElementById('quick-save-domain-picker');
        if (stale) stale.remove();

        const isDk = document.body.classList.contains('dark-mode');
        const t = {
            bg: isDk ? 'rgba(17, 25, 40, 0.92)' : 'rgba(255, 255, 255, 0.92)',
            border: isDk ? 'rgba(255, 255, 255, 0.125)' : 'rgba(0, 0, 0, 0.08)',
            text: isDk ? '#e2e8f0' : '#1e1e32',
            muted: isDk ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.45)',
            input: isDk ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)',
            inputBorder: isDk ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.12)',
            hover: isDk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)',
        };

        const overlay = document.createElement('div');
        overlay.id = 'quick-save-domain-picker';
        overlay.style.cssText = `position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);backdrop-filter:blur(6px);z-index:10001;display:flex;align-items:center;justify-content:center;`;

        let selectedId = null;
        const icons = FileOps._sectionIcons();

        const renderStep1 = () => {
            const card = overlay.querySelector('.qs-card') || document.createElement('div');
            card.className = 'qs-card';
            card.style.cssText = `background:${t.bg};border:1px solid ${t.border};border-radius:14px;padding:20px;min-width:340px;max-width:400px;box-shadow:0 12px 48px rgba(0,0,0,0.3);backdrop-filter:blur(16px);font-family:'Poppins',-apple-system,sans-serif;`;
            card.innerHTML = `
                <div style="font-size:15px;font-weight:600;color:${t.text};margin-bottom:4px;">Save to Domain</div>
                <div style="font-size:11px;color:${t.muted};margin-bottom:14px;">Select a domain to save the current topology</div>
                <div class="qs-domains" style="display:flex;flex-direction:column;gap:6px;margin-bottom:14px;"></div>
                <div style="text-align:right;">
                    <button class="qs-cancel" style="padding:7px 14px;background:transparent;border:1px solid ${t.border};border-radius:8px;color:${t.text};cursor:pointer;font-size:12px;">Cancel</button>
                </div>
            `;
            const domainsList = card.querySelector('.qs-domains');
            sections.forEach(sec => {
                const iconSvg = (icons.find(i => i.id === sec.icon) || icons[0]).svg;
                const btn = document.createElement('button');
                btn.style.cssText = `display:flex;align-items:center;gap:10px;padding:10px 12px;background:${sec.color}0d;border:1px solid ${sec.color}30;border-left:3px solid ${sec.color};border-radius:8px;cursor:pointer;transition:all 0.15s;width:100%;text-align:left;`;
                btn.innerHTML = `
                    <div style="width:28px;height:28px;border-radius:6px;background:${sec.color}18;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                        <svg viewBox="0 0 24 24" width="14" height="14" style="stroke:${sec.color};color:${sec.color};">${iconSvg}</svg>
                    </div>
                    <span style="font-size:13px;font-weight:500;color:${t.text};">${sec.name}</span>
                `;
                btn.onmouseenter = () => { btn.style.background = `${sec.color}1a`; btn.style.borderColor = `${sec.color}60`; };
                btn.onmouseleave = () => { btn.style.background = `${sec.color}0d`; btn.style.borderColor = `${sec.color}30`; };
                btn.onclick = () => { selectedId = sec.id; renderStep2(sec, card); };
                domainsList.appendChild(btn);
            });
            card.querySelector('.qs-cancel').onclick = () => overlay.remove();
            if (!overlay.contains(card)) overlay.appendChild(card);
        };

        const renderStep2 = (sec, card) => {
            const defaultName = 'topology_' + new Date().toISOString().slice(0, 10);
            card.innerHTML = `
                <div style="font-size:15px;font-weight:600;color:${t.text};margin-bottom:4px;">Save to ${sec.name}</div>
                <div style="font-size:11px;color:${t.muted};margin-bottom:14px;">Enter a name for the topology</div>
                <input class="qs-name" type="text" value="${defaultName}" placeholder="Topology name" style="
                    width:100%;padding:9px 12px;background:${t.input};border:1px solid ${sec.color}55;border-radius:8px;
                    color:${t.text};font-size:13px;font-family:inherit;box-sizing:border-box;margin-bottom:14px;outline:none;"
                    onclick="event.stopPropagation();">
                <div style="display:flex;gap:8px;justify-content:flex-end;">
                    <button class="qs-back" style="padding:7px 14px;background:transparent;border:1px solid ${t.border};border-radius:8px;color:${t.text};cursor:pointer;font-size:12px;">Back</button>
                    <button class="qs-save" style="padding:7px 16px;background:${sec.color};border:none;border-radius:8px;color:#fff;cursor:pointer;font-size:12px;font-weight:600;">Save</button>
                </div>
            `;
            const input = card.querySelector('.qs-name');
            const saveBtn = card.querySelector('.qs-save');
            input.focus();
            input.select();
            card.querySelector('.qs-back').onclick = () => renderStep1();
            const doSave = async () => {
                const name = input.value.trim();
                if (!name) { editor.showToast('Enter a topology name', 'warning'); return; }
                saveBtn.textContent = 'Saving...';
                saveBtn.disabled = true;
                try {
                    const resp = await fetch(`/api/sections/${sec.id}/save`, {
                        method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name, topology: FileOps.generateTopologyData(editor) })
                    });
                    const result = await resp.json();
                    if (result.error) throw new Error(result.error);
                    overlay.remove();
                    FileOps.updateTopologyIndicator(name, sec.name, sec.color, sec.id);
                    editor.showToast(`Saved to ${sec.name}`, 'success');
                    if (editor.loadCustomSections) editor.loadCustomSections();
                } catch (err) {
                    saveBtn.textContent = 'Save';
                    saveBtn.disabled = false;
                    editor.showToast('Save failed: ' + err.message, 'error');
                }
            };
            saveBtn.onclick = doSave;
            input.addEventListener('keydown', (ev) => { ev.stopPropagation(); if (ev.key === 'Enter') doSave(); if (ev.key === 'Escape') overlay.remove(); });
        };

        document.body.appendChild(overlay);
        overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
        renderStep1();
    },

    saveTopologyAs(editor) {
        const data = FileOps.generateTopologyData(editor);
        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `topology_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        editor.showToast('Topology downloaded', 'success');
    },

    saveTopology(editor) {
        FileOps.saveTopologyAs(editor);
    },

    exportTopologyJSON(editor) {
        FileOps.saveTopologyAs(editor);
    },

    exportTopologyAsPNG(editor) {
        const objs = editor.objects.filter(o => !o._hidden);
        if (objs.length === 0) {
            editor.showToast('Nothing to export — canvas is empty', 'warning');
            return;
        }

        FileOps._showPNGExportDialog(editor, objs);
    },

    _showPNGExportDialog(editor, objs) {
        const existing = document.getElementById('png-export-dialog');
        if (existing) existing.remove();

        const dk = editor.darkMode;
        const overlay = document.createElement('div');
        overlay.id = 'png-export-dialog';
        overlay.style.cssText = 'position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.5);backdrop-filter:blur(4px);';

        const panel = document.createElement('div');
        panel.style.cssText = `background:${dk ? 'rgba(20,24,40,0.92)' : 'rgba(255,255,255,0.95)'};border:1px solid ${dk ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.1)'};border-radius:14px;padding:24px 28px;min-width:320px;max-width:400px;box-shadow:0 16px 48px rgba(0,0,0,0.35);backdrop-filter:blur(20px);font-family:inherit;`;

        const txtPrimary = dk ? '#e2e8f0' : '#1e1e32';
        const txtMuted = dk ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.45)';
        const accentColor = '#3b82f6';

        let selectedScale = 3;
        let includeBg = true;

        const bounds = FileOps._computeExportBounds(objs);
        const baseW = Math.round(bounds.w);
        const baseH = Math.round(bounds.h);

        const updatePreview = () => {
            const pw = baseW * selectedScale;
            const ph = baseH * selectedScale;
            const sizeMB = ((pw * ph * 4) / (1024 * 1024)).toFixed(1);
            dimSpan.textContent = `${pw} × ${ph}px`;
            sizeSpan.textContent = `~${sizeMB} MB uncompressed`;
            scaleButtons.forEach(btn => {
                const s = parseInt(btn.dataset.scale);
                if (s === selectedScale) {
                    btn.style.background = accentColor;
                    btn.style.color = '#fff';
                    btn.style.borderColor = accentColor;
                } else {
                    btn.style.background = dk ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)';
                    btn.style.color = txtPrimary;
                    btn.style.borderColor = dk ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
                }
            });
        };

        panel.innerHTML = `
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;">
                <div style="font-size:15px;font-weight:700;color:${txtPrimary};">Export PNG</div>
                <button id="png-close-btn" style="background:none;border:none;cursor:pointer;color:${txtMuted};font-size:18px;padding:2px 6px;border-radius:6px;" title="Cancel">✕</button>
            </div>
            <div style="margin-bottom:16px;">
                <div style="font-size:11px;font-weight:600;color:${txtMuted};text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;">Scale</div>
                <div id="png-scale-btns" style="display:flex;gap:6px;"></div>
            </div>
            <div style="margin-bottom:16px;">
                <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:12px;color:${txtPrimary};">
                    <input type="checkbox" id="png-bg-check" checked style="accent-color:${accentColor};width:15px;height:15px;cursor:pointer;">
                    Include background
                </label>
            </div>
            <div style="margin-bottom:20px;padding:10px 12px;border-radius:8px;background:${dk ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)'};border:1px solid ${dk ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'};">
                <div style="display:flex;justify-content:space-between;font-size:11px;color:${txtMuted};margin-bottom:4px;">
                    <span>Dimensions</span>
                    <span id="png-dim-span"></span>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:11px;color:${txtMuted};">
                    <span>Estimated size</span>
                    <span id="png-size-span"></span>
                </div>
            </div>
            <div style="display:flex;gap:8px;">
                <button id="png-cancel-btn" style="flex:1;padding:9px;border-radius:8px;border:1px solid ${dk ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'};background:${dk ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)'};color:${txtPrimary};font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;">Cancel</button>
                <button id="png-export-btn" style="flex:2;padding:9px;border-radius:8px;border:none;background:${accentColor};color:#fff;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;">Export</button>
            </div>
        `;

        overlay.appendChild(panel);
        document.body.appendChild(overlay);

        const dimSpan = panel.querySelector('#png-dim-span');
        const sizeSpan = panel.querySelector('#png-size-span');
        const scaleBtnContainer = panel.querySelector('#png-scale-btns');

        const scales = [
            { value: 1, label: '1×' },
            { value: 2, label: '2×' },
            { value: 3, label: '3×' },
            { value: 4, label: '4×' },
        ];

        const scaleButtons = [];
        scales.forEach(s => {
            const btn = document.createElement('button');
            btn.dataset.scale = s.value;
            btn.textContent = s.label;
            btn.style.cssText = `flex:1;padding:7px 0;border-radius:7px;border:1px solid;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;transition:all 0.15s;`;
            btn.addEventListener('click', () => { selectedScale = s.value; updatePreview(); });
            scaleBtnContainer.appendChild(btn);
            scaleButtons.push(btn);
        });

        const bgCheck = panel.querySelector('#png-bg-check');
        bgCheck.addEventListener('change', () => { includeBg = bgCheck.checked; });

        updatePreview();

        const close = () => overlay.remove();
        overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
        panel.querySelector('#png-close-btn').addEventListener('click', close);
        panel.querySelector('#png-cancel-btn').addEventListener('click', close);
        panel.querySelector('#png-export-btn').addEventListener('click', () => {
            close();
            FileOps._renderPNGExport(editor, objs, selectedScale, includeBg);
        });

        document.addEventListener('keydown', function esc(e) {
            if (e.key === 'Escape') { close(); document.removeEventListener('keydown', esc); }
        });
    },

    _computeExportBounds(objs) {
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        const expand = (cx, cy, margin) => {
            if (cx - margin < minX) minX = cx - margin;
            if (cy - margin < minY) minY = cy - margin;
            if (cx + margin > maxX) maxX = cx + margin;
            if (cy + margin > maxY) maxY = cy + margin;
        };
        const expandRect = (cx, cy, hw, hh) => {
            if (cx - hw < minX) minX = cx - hw;
            if (cy - hh < minY) minY = cy - hh;
            if (cx + hw > maxX) maxX = cx + hw;
            if (cy + hh > maxY) maxY = cy + hh;
        };

        objs.forEach(obj => {
            if (obj.type === 'device') {
                const r = obj.radius || 20;
                const bounds = window.DeviceStyles && window.DeviceStyles.getDeviceBounds
                    ? window.DeviceStyles.getDeviceBounds(obj) : null;
                if (bounds && bounds.width) {
                    expandRect(obj.x, obj.y, bounds.width / 2 + 15, Math.max(Math.abs(bounds.top || r), Math.abs(bounds.bottom || r)) + 15);
                } else {
                    expand(obj.x, obj.y, r + 15);
                }
                expand(obj.x, obj.y + r + 22, 50);
            } else if (obj.type === 'link' || obj.type === 'unbound') {
                expand(obj.x, obj.y, 8);
                expand(obj.x2, obj.y2, 8);
                if (obj.manualCurvePoint) expand(obj.manualCurvePoint.x, obj.manualCurvePoint.y, 8);
                if (obj.manualControlPoint) expand(obj.manualControlPoint.x, obj.manualControlPoint.y, 8);
            } else if (obj.type === 'text') {
                const fontSize = obj.fontSize || 14;
                const lines = (obj.text || '').split('\n');
                const maxLine = Math.max(...lines.map(l => l.length));
                const approxW = maxLine * fontSize * 0.6;
                const approxH = lines.length * fontSize * 1.3;
                expandRect(obj.x, obj.y, approxW / 2 + 12, approxH / 2 + 12);
            } else if (obj.type === 'shape') {
                const hw = (obj.width || 100) / 2;
                const hh = (obj.height || 60) / 2;
                expandRect(obj.x, obj.y, hw + 6, hh + 6);
            }
        });

        const pad = 50;
        minX -= pad; minY -= pad; maxX += pad; maxY += pad;
        return { minX, minY, maxX, maxY, w: maxX - minX, h: maxY - minY };
    },

    _renderPNGExport(editor, objs, scale, includeBg) {
        const { minX, minY, w, h } = FileOps._computeExportBounds(objs);
        if (w <= 0 || h <= 0) {
            editor.showToast('Could not determine object bounds', 'error');
            return;
        }

        const offscreen = document.createElement('canvas');
        offscreen.width = Math.round(w * scale);
        offscreen.height = Math.round(h * scale);
        const ctx = offscreen.getContext('2d');
        ctx.scale(scale, scale);

        if (includeBg) {
            ctx.fillStyle = editor.darkMode ? '#1a1a2e' : '#ffffff';
            ctx.fillRect(0, 0, w, h);
        }

        ctx.save();
        ctx.translate(-minX, -minY);

        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';

        const origCtx = editor.ctx;
        const origCanvas = editor.canvas;
        const origSelected = editor.selectedObject;
        const origSelectedArr = editor.selectedObjects;
        const origZoom = editor.zoom;
        const origPan = { ...editor.panOffset };

        editor.ctx = ctx;
        editor.canvas = offscreen;
        editor.selectedObject = null;
        editor.selectedObjects = [];
        editor.zoom = 1;
        editor.panOffset = { x: 0, y: 0 };

        const sorted = [...objs].sort((a, b) => {
            const layerA = a.layer ?? 0, layerB = b.layer ?? 0;
            if (layerA !== layerB) return layerA - layerB;
            const typeOrder = { 'shape': -1, 'link': 0, 'unbound': 0, 'device': 1, 'text': 2 };
            return (typeOrder[a.type] || 0) - (typeOrder[b.type] || 0);
        });

        sorted.forEach(obj => {
            if (obj.type === 'link' || obj.type === 'unbound') {
                editor.drawLink(obj);
            } else if (obj.type === 'device') {
                editor.drawDevice(obj, false, true);
            } else if (obj.type === 'text') {
                if (obj.linkId && !editor.showLinkAttachments) return;
                editor.drawText(obj);
            } else if (obj.type === 'shape') {
                editor.drawShape(obj);
            }
        });
        sorted.forEach(obj => {
            if (obj.type === 'device') editor.drawDeviceLabel(obj);
        });

        ctx.restore();

        editor.ctx = origCtx;
        editor.canvas = origCanvas;
        editor.selectedObject = origSelected;
        editor.selectedObjects = origSelectedArr;
        editor.zoom = origZoom;
        editor.panOffset = origPan;

        const pw = offscreen.width;
        const ph = offscreen.height;
        const stored = JSON.parse(localStorage.getItem('topo_active') || '{}');
        const topoName = (stored.name || 'topology_export').replace(/[^a-zA-Z0-9_\-]/g, '_');
        const link = document.createElement('a');
        link.download = `${topoName}.png`;
        link.href = offscreen.toDataURL('image/png');
        link.click();
        editor.showToast(`PNG exported at ${scale}× (${pw}×${ph}px)`, 'success');
    },

    loadTopology(editor, event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                let data = JSON.parse(e.target.result);
                if (!data.objects && data.topology && data.topology.objects) data = data.topology;
                if (!data.objects && Array.isArray(data)) data = { objects: data };
                if (!data.objects || !Array.isArray(data.objects)) {
                    editor.showToast('Invalid topology file: no objects array found', 'error');
                    return;
                }
                editor.loadTopologyFromData(data);
                const topoName = file.name.replace(/\.json$/i, '');
                FileOps.updateTopologyIndicator(topoName, null);
                editor.showToast(`Loaded ${file.name} (${data.objects.length} objects)`, 'success');
            } catch (error) {
                console.error('[loadTopology] Parse error:', error);
                editor.showToast(`Error loading topology: ${error.message}`, 'error');
            }
        };
        reader.onerror = () => {
            editor.showToast(`Error reading file: ${reader.error?.message || 'unknown error'}`, 'error');
        };
        reader.readAsText(file);
        event.target.value = '';
    },

    // ========================================================================
    // DNAAS TOPOLOGIES
    // ========================================================================

    saveAsDnaasTopology(editor) {
        if (window.DnaasHelpers && window.DnaasHelpers.saveAsDnaasTopology) {
            return window.DnaasHelpers.saveAsDnaasTopology(editor);
        }
    },

    async loadDnaasTopology(editor) {
        try {
            const sectionId = await window.DnaasHelpers._ensureDnaasSection();
            await editor.loadFromSection({ id: sectionId, name: 'DNAAS', color: '#FF5E1F' });
        } catch (err) {
            editor.showToast('Failed to load DNAAS topologies: ' + err.message, 'error');
        }
    },

    // ========================================================================
    // BUG TOPOLOGIES — now managed via the unified sections API
    // ========================================================================

    _bugsSectionId: null,

    async _ensureBugsSection() {
        if (FileOps._bugsSectionId) return FileOps._bugsSectionId;
        try {
            const resp = await fetch('/api/sections');
            const data = await resp.json();
            const sections = data.sections || [];
            const existing = sections.find(s => s.name === 'Bugs');
            if (existing) {
                FileOps._bugsSectionId = existing.id;
                fetch('/api/migrate-bug-topologies', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ section_id: existing.id })
                }).catch(() => {});
                return existing.id;
            }
            const createResp = await fetch('/api/sections', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: 'Bugs', icon: 'alert', color: '#e74c3c' })
            });
            const result = await createResp.json();
            FileOps._bugsSectionId = result.section.id;
            await fetch('/api/migrate-bug-topologies', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ section_id: result.section.id })
            });
            return result.section.id;
        } catch (err) {
            console.error('[Bugs] Failed to ensure section:', err);
            throw err;
        }
    },

    async saveBugTopology(editor) {
        const id = await FileOps._ensureBugsSection();
        editor.saveToSection({ id, name: 'Bugs', color: '#e74c3c' });
    },
    async loadDebugDnosTopology(editor) {
        const id = await FileOps._ensureBugsSection();
        editor.loadFromSection({ id, name: 'Bugs', color: '#e74c3c' });
    },
    showDebugDnosTopologySelector(editor) {},

    // ========================================================================
    // SHARED: Render topology entries with right-click rename
    // ========================================================================

    _formatTimeAgo(mtime) {
        if (!mtime) return '';
        const now = Date.now() / 1000;
        const diff = now - mtime;
        if (diff < 60) return 'just now';
        if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
        if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
        if (diff < 604800) return Math.floor(diff / 86400) + 'd ago';
        const d = new Date(mtime * 1000);
        return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    },

    _renderTopoEntries(editor, container, topos, color, opts) {
        const dk = document.body.classList.contains('dark-mode');
        const txtColor = dk ? '#e2e8f0' : '#1e1e32';
        const iconOpColor = dk ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.5)';
        const mutedColor = dk ? 'rgba(255,255,255,0.35)' : 'rgba(0,0,0,0.45)';
        let html = '';
        topos.forEach(t => {
            const name = (t.name || t.filename || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            const filename = (t.filename || '').replace(/"/g, '&quot;');
            const timeAgo = FileOps._formatTimeAgo(t.modified);
            const borderOp = dk ? '40' : '70';
            html += `<div class="domain-topo-row" data-filename="${filename}" data-section-id="${opts.sectionId || ''}"
                style="display:flex;align-items:center;padding:3px 8px 3px 14px;margin-left:8px;border-left:2px solid ${color}${borderOp};border-radius:3px;cursor:pointer;transition:background 0.15s;user-select:none;">
                <svg class="topo-file-icon" viewBox="0 0 24 24" width="12" height="12" style="color:${iconOpColor};opacity:0.7;flex-shrink:0;margin-right:6px;">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2" fill="none"/>
                    <polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="2" fill="none"/>
                </svg>
                <span class="topo-entry-name" style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:11px;color:${txtColor};">${name}</span>
                ${timeAgo ? `<span class="topo-time" data-tooltip="Last saved: ${t.modified ? new Date(t.modified * 1000).toLocaleString(undefined, { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }) : ''}" style="display:flex;align-items:center;gap:2px;flex-shrink:0;margin-left:4px;font-size:9px;color:${mutedColor};white-space:nowrap;position:relative;cursor:default;">
                    <svg viewBox="0 0 24 24" width="9" height="9" style="opacity:0.7;"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/><polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/></svg>
                    ${timeAgo}
                </span>` : ''}
                <span class="topo-actions" style="display:flex;flex-shrink:0;gap:2px;align-items:center;margin-left:4px;visibility:hidden;opacity:0;transition:opacity 0.12s;">
                    <button class="ta-open ta-btn" title="Open" style="background:none;border:none;cursor:pointer;padding:3px;display:flex;align-items:center;color:${iconOpColor};border-radius:4px;transition:background 0.12s;">
                        <svg viewBox="0 0 24 24" width="13" height="13" style="color:inherit;"><path d="M15 3h6v6M14 10l6.1-6.1M10 5H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/></svg>
                    </button>
                    <button class="ta-rename ta-btn" title="Rename" style="background:none;border:none;cursor:pointer;padding:3px;display:flex;align-items:center;color:${iconOpColor};border-radius:4px;transition:background 0.12s;">
                        <svg viewBox="0 0 24 24" width="13" height="13" style="color:inherit;"><path d="M17 3a2.83 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" stroke="currentColor" stroke-width="2" fill="none"/></svg>
                    </button>
                    <button class="ta-duplicate ta-btn" title="Duplicate to..." style="background:none;border:none;cursor:pointer;padding:3px;display:flex;align-items:center;color:${iconOpColor};border-radius:4px;transition:background 0.12s;">
                        <svg viewBox="0 0 24 24" width="13" height="13" style="color:inherit;"><rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke="currentColor" stroke-width="2" fill="none"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke="currentColor" stroke-width="2" fill="none"/></svg>
                    </button>
                    <button class="ta-delete ta-btn" title="Delete" style="background:none;border:none;cursor:pointer;padding:3px;display:flex;align-items:center;color:${iconOpColor};border-radius:4px;transition:background 0.12s;">
                        <svg viewBox="0 0 24 24" width="13" height="13" style="color:inherit;"><polyline points="3 6 5 6 21 6" stroke="currentColor" stroke-width="2" fill="none"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" fill="none"/></svg>
                    </button>
                </span>
            </div>`;
        });
        container.innerHTML = html;
        
        container.querySelectorAll('.domain-topo-row').forEach(row => {
            row.addEventListener('mouseenter', () => {
                const dk = document.body.classList.contains('dark-mode');
                row.style.background = dk ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.07)';
                const a = row.querySelector('.topo-actions'); if (a) { a.style.visibility = 'visible'; a.style.opacity = '1'; }
            });
            row.addEventListener('mouseleave', () => {
                row.style.background = '';
                const a = row.querySelector('.topo-actions'); if (a) { a.style.visibility = 'hidden'; a.style.opacity = '0'; }
                document.querySelectorAll('.ta-btn-tip').forEach(t => t.remove());
            });
            row.querySelectorAll('.ta-btn').forEach(btn => {
                let btnTip = null;
                btn.addEventListener('mouseenter', () => {
                    btn.style.background = 'rgba(255,255,255,0.12)';
                    const label = btn.getAttribute('title');
                    if (!label) return;
                    const br = btn.getBoundingClientRect();
                    const tip = document.createElement('div');
                    tip.className = 'ta-btn-tip';
                    tip.textContent = label;
                    const isDk = document.body.classList.contains('dark-mode');
                    tip.style.cssText = `
                        position:fixed; z-index:100001; pointer-events:none;
                        bottom:${window.innerHeight - br.top + 5}px;
                        left:${br.left + br.width / 2}px; transform:translateX(-50%);
                        padding:3px 8px; border-radius:5px; white-space:nowrap;
                        font-size:10px; font-weight:500; letter-spacing:0.2px;
                        font-family:'Poppins',-apple-system,sans-serif;
                        background:${isDk ? 'rgba(15,15,30,0.95)' : 'rgba(255,255,255,0.96)'};
                        color:${isDk ? 'rgba(255,255,255,0.9)' : 'rgba(20,20,40,0.85)'};
                        box-shadow:${isDk ? '0 3px 12px rgba(0,0,0,0.4)' : '0 3px 12px rgba(0,0,0,0.12)'};
                        opacity:0; transition:opacity 0.1s ease;
                    `;
                    document.body.appendChild(tip);
                    requestAnimationFrame(() => { tip.style.opacity = '1'; });
                    btnTip = tip;
                });
                btn.addEventListener('mouseleave', () => {
                    btn.style.background = 'none';
                    if (btnTip) { btnTip.remove(); btnTip = null; }
                });
            });

            row.querySelector('.ta-open').onclick = (e) => { e.stopPropagation(); if (opts.loadFn) opts.loadFn(row.dataset.filename); };
            row.querySelector('.ta-rename').onclick = (e) => { e.stopPropagation(); FileOps._showRenameInput(editor, row, color, container, opts); };
            row.querySelector('.ta-duplicate').onclick = (e) => {
                e.stopPropagation();
                FileOps._showDuplicatePicker(editor, row, opts.sectionId, container, opts);
            };
            row.querySelector('.ta-delete').onclick = (e) => {
                e.stopPropagation();
                const existing = container.querySelector('.delete-confirm-bar');
                if (existing) existing.remove();
                const name = row.querySelector('.topo-entry-name')?.textContent?.trim() || row.dataset.filename;
                const bar = document.createElement('div');
                bar.className = 'delete-confirm-bar';
                const isDark = document.body.classList.contains('dark-mode');
                bar.style.cssText = `display:flex;align-items:center;gap:6px;padding:4px 12px 4px 20px;margin-left:8px;background:${isDark ? 'rgba(239,68,68,0.1)' : 'rgba(239,68,68,0.08)'};border-left:2px solid #ef4444;border-radius:3px;`;
                bar.innerHTML = `
                    <span style="flex:1;font-size:10px;">Delete "${name}"?</span>
                    <button class="dc-yes" style="padding:3px 10px;background:#ef4444;border:none;border-radius:4px;color:#fff;font-size:10px;font-weight:600;cursor:pointer;">Delete</button>
                    <button class="dc-no" style="padding:3px 8px;background:${isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)'};border:1px solid ${isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.12)'};border-radius:4px;color:${isDark ? '#94a3b8' : '#475569'};font-size:10px;cursor:pointer;">Cancel</button>
                `;
                row.after(bar);
                bar.querySelector('.dc-yes').onclick = (ev) => { ev.stopPropagation(); bar.remove(); if (opts.deleteFn) opts.deleteFn(row.dataset.filename); };
                bar.querySelector('.dc-no').onclick = (ev) => { ev.stopPropagation(); bar.remove(); };
            };

            // Drag from entire row — click loads, drag reorders/moves
            if (opts.sectionId) {
                row.style.cursor = 'grab';
                row.addEventListener('mousedown', (e) => {
                    if (e.button !== 0) return;
                    if (e.target.closest('.ta-btn') || e.target.closest('.topo-actions') || e.target.closest('.delete-confirm-bar')) return;
                    e.preventDefault();
                    const startY = e.clientY, startX = e.clientX;
                    let dragging = false;
                    let dropIndicator = null;
                    let hoveredDomainId = null;
                    const srcSectionId = opts.sectionId;
                    const dk = document.body.classList.contains('dark-mode');
                    const ease = 'cubic-bezier(0.22, 1, 0.36, 1)';

                    let allRows = [];
                    let offsets = [];
                    let heights = [];
                    let slotYs = [];
                    let currentOrder = [];
                    let dragIdx = -1;

                    const applyRowTransforms = () => {
                        for (let pos = 0; pos < currentOrder.length; pos++) {
                            const idx = currentOrder[pos];
                            if (idx === dragIdx) continue;
                            const dy = slotYs[pos] - offsets[idx];
                            allRows[idx].style.transition = `transform 0.2s ${ease}`;
                            allRows[idx].style.transform = dy ? `translateY(${dy}px)` : '';
                        }
                    };

                    const onMove = (ev) => {
                        if (!dragging && Math.abs(ev.clientY - startY) + Math.abs(ev.clientX - startX) < 6) return;
                        if (!dragging) {
                            dragging = true;
                            editor._topoDragActive = true;

                            const dropdown = document.getElementById('topologies-dropdown-menu');
                            if (dropdown) dropdown.style.overflowY = 'visible';
                            container.style.overflow = 'visible';

                            allRows = [...container.querySelectorAll('.domain-topo-row')];
                            dragIdx = allRows.indexOf(row);
                            allRows.forEach(r => { r.style.transform = ''; r.style.transition = 'none'; });
                            offsets = allRows.map(r => r.offsetTop);
                            heights = allRows.map(r => r.offsetHeight);
                            currentOrder = allRows.map((_, i) => i);
                            slotYs = [];
                            let y = offsets[0];
                            for (let i = 0; i < allRows.length; i++) {
                                slotYs.push(y);
                                if (i < allRows.length - 1) {
                                    const gap = offsets[i + 1] - (offsets[i] + heights[i]);
                                    y += heights[i] + Math.max(gap, 0);
                                }
                            }

                            row.style.position = 'relative';
                            row.style.zIndex = '100';
                            row.style.boxShadow = '0 4px 14px rgba(0,0,0,0.22)';
                            row.style.opacity = '0.92';
                            row.style.borderRadius = '4px';
                            row.style.background = dk ? 'rgba(25,30,50,0.95)' : 'rgba(255,255,255,0.95)';
                            allRows.forEach((r, i) => {
                                if (i !== dragIdx) { r.style.position = 'relative'; r.style.zIndex = '1'; }
                            });

                            dropIndicator = document.createElement('div');
                            dropIndicator.style.cssText = `height:3px;border-radius:2px;pointer-events:none;display:none;position:fixed;z-index:999998;transition:top 0.12s ease,left 0.12s ease,width 0.12s ease;`;
                            document.body.appendChild(dropIndicator);

                            document.body.style.cursor = 'grabbing';
                            row.style.cursor = 'grabbing';
                        }

                        const dy = ev.clientY - startY;
                        row.style.transform = `translateY(${dy}px)`;
                        row.style.transition = 'none';

                        let overOtherDomain = false;
                        let newHoveredId = null;
                        dropIndicator.style.display = 'none';

                        document.querySelectorAll('.custom-section-category').forEach(secEl => {
                            const secId = secEl.dataset.sectionId;
                            const secObj = (editor._customSections || []).find(s => s.id === secId);
                            const sc = secObj?.color || '#3b82f6';
                            const secRect = secEl.getBoundingClientRect();
                            const isDkD = document.body.classList.contains('dark-mode');

                            if (ev.clientY >= secRect.top && ev.clientY <= secRect.bottom && secId !== srcSectionId) {
                                overOtherDomain = true;
                                newHoveredId = secId;

                                const bodyEl = secEl.querySelector('.domain-body');
                                const isCollapsed = bodyEl && bodyEl.style.display === 'none';

                                secEl.style.transition = 'all 0.15s ease';
                                secEl.style.background = `linear-gradient(135deg, ${sc}${isDkD ? '30' : '35'}, ${sc}${isDkD ? '15' : '18'})`;
                                secEl.style.boxShadow = `inset 0 0 0 1.5px ${sc}80, 0 4px 20px ${sc}30`;

                                if (!isCollapsed) {
                                    const topoRows = secEl.querySelectorAll('.domain-topo-row');
                                    const toposList = secEl.querySelector('.domain-topos-list');

                                    let existingGhost = secEl.querySelector('.drop-ghost');
                                    if (!existingGhost) {
                                        existingGhost = document.createElement('div');
                                        existingGhost.className = 'drop-ghost';
                                        existingGhost.style.cssText = `
                                            height: 28px; margin: 2px 8px 2px 14px; border-radius: 6px;
                                            background: ${isDkD
                                                ? 'linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02))'
                                                : 'linear-gradient(135deg, rgba(255,255,255,0.5), rgba(255,255,255,0.25))'};
                                            border: 1px dashed ${sc}50;
                                            backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
                                            box-shadow: inset 0 1px 0 ${isDkD ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.4)'};
                                            transition: opacity 0.15s ease;
                                            pointer-events: none;
                                        `;
                                    }

                                    if (topoRows.length === 0 && toposList) {
                                        if (!toposList.contains(existingGhost)) toposList.appendChild(existingGhost);
                                    } else if (topoRows.length > 0) {
                                        let bestRow = null, bestDist = Infinity, insertAfter = false;
                                        topoRows.forEach(r => {
                                            const rr = r.getBoundingClientRect();
                                            const mid = rr.top + rr.height / 2;
                                            const dist = Math.abs(ev.clientY - mid);
                                            if (dist < bestDist) { bestDist = dist; bestRow = r; insertAfter = ev.clientY > mid; }
                                        });
                                        if (bestRow) {
                                            if (insertAfter) {
                                                bestRow.after(existingGhost);
                                            } else {
                                                bestRow.before(existingGhost);
                                            }
                                        }
                                    }
                                }
                            } else {
                                secEl.style.background = `${sc}${isDkD ? '22' : '28'}`;
                                secEl.style.boxShadow = '';
                                secEl.style.transition = 'all 0.2s ease';
                                const ghost = secEl.querySelector('.drop-ghost');
                                if (ghost) ghost.remove();
                            }
                        });

                        hoveredDomainId = newHoveredId;
                        if (!overOtherDomain) hoveredDomainId = null;

                        if (!overOtherDomain && dragIdx >= 0) {
                            const dragMid = offsets[dragIdx] + dy + heights[dragIdx] / 2;
                            const dragPos = currentOrder.indexOf(dragIdx);

                            if (dragPos > 0) {
                                const aboveIdx = currentOrder[dragPos - 1];
                                const aboveMid = slotYs[dragPos - 1] + heights[aboveIdx] * 0.45;
                                if (dragMid < aboveMid) {
                                    currentOrder.splice(dragPos, 1);
                                    currentOrder.splice(dragPos - 1, 0, dragIdx);
                                    applyRowTransforms();
                                }
                            }
                            if (dragPos < currentOrder.length - 1) {
                                const belowIdx = currentOrder[dragPos + 1];
                                const belowMid = slotYs[dragPos + 1] + heights[belowIdx] * 0.55;
                                if (dragMid > belowMid) {
                                    currentOrder.splice(dragPos, 1);
                                    currentOrder.splice(dragPos + 1, 0, dragIdx);
                                    applyRowTransforms();
                                }
                            }
                        }
                    };

                    const cleanupDrag = () => {
                        document.removeEventListener('mousemove', onMove);
                        document.removeEventListener('mouseup', onUp);
                        document.body.style.cursor = '';
                        editor._topoDragActive = false;
                        if (dropIndicator) { dropIndicator.remove(); dropIndicator = null; }
                        document.querySelectorAll('.drop-ghost').forEach(g => g.remove());
                        document.querySelectorAll('.custom-section-category').forEach(secEl => {
                            const secObj = (editor._customSections || []).find(s => s.id === secEl.dataset.sectionId);
                            const sc = secObj?.color || '#3b82f6';
                            const isDkD = document.body.classList.contains('dark-mode');
                            secEl.style.background = `${sc}${isDkD ? '22' : '28'}`;
                            secEl.style.boxShadow = '';
                            secEl.style.transition = 'all 0.2s ease';
                        });
                        const dropdown = document.getElementById('topologies-dropdown-menu');
                        if (dropdown) dropdown.style.overflowY = 'auto';
                        container.style.overflow = '';
                    };

                    const onUp = async (ev) => {
                        if (!dragging) {
                            document.removeEventListener('mousemove', onMove);
                            document.removeEventListener('mouseup', onUp);
                            if (opts.loadFn) opts.loadFn(row.dataset.filename);
                            return;
                        }

                        const filename = row.dataset.filename;

                        let targetSectionId = null;
                        document.querySelectorAll('.custom-section-category').forEach(secEl => {
                            const secId = secEl.dataset.sectionId;
                            const secRect = secEl.getBoundingClientRect();
                            if (ev.clientY >= secRect.top && ev.clientY <= secRect.bottom && secId !== srcSectionId) {
                                targetSectionId = secId;
                            }
                        });

                        if (targetSectionId && filename) {
                            document.removeEventListener('mousemove', onMove);
                            document.removeEventListener('mouseup', onUp);
                            document.body.style.cursor = '';
                            editor._topoDragActive = false;
                            if (dropIndicator) { dropIndicator.remove(); dropIndicator = null; }
                            document.querySelectorAll('.drop-ghost').forEach(g => g.remove());
                            document.querySelectorAll('.custom-section-category').forEach(secEl => {
                                const secObj2 = (editor._customSections || []).find(s => s.id === secEl.dataset.sectionId);
                                const sc2 = secObj2?.color || '#3b82f6';
                                const isDk2 = document.body.classList.contains('dark-mode');
                                secEl.style.background = `${sc2}${isDk2 ? '22' : '28'}`;
                                secEl.style.boxShadow = '';
                                secEl.style.transition = 'all 0.2s ease';
                            });

                            const moveFile = filename.endsWith('.json') ? filename : filename + '.json';
                            const moveUrl = `/api/sections/${encodeURIComponent(srcSectionId)}/topologies/${encodeURIComponent(moveFile)}/move`;
                            const dstSec = (editor._customSections || []).find(s => s.id === targetSectionId);
                            const srcSec = (editor._customSections || []).find(s => s.id === srcSectionId);
                            const dstColor = dstSec?.color || '#3b82f6';

                            const tgtDiv = document.querySelector(`.custom-section-category[data-section-id="${targetSectionId}"]`);
                            let dstCtr = tgtDiv?.querySelector('.domain-topos-list');

                            if (editor._domainCollapsed && editor._domainCollapsed[targetSectionId] && tgtDiv) {
                                editor._domainCollapsed[targetSectionId] = false;
                                const b = tgtDiv.querySelector('.domain-body'); if (b) b.style.display = 'block';
                                const c = tgtDiv.querySelector('.domain-chevron'); if (c) c.style.transform = 'rotate(0deg)';
                                dstCtr = tgtDiv.querySelector('.domain-topos-list');
                            }

                            const h = row.offsetHeight;
                            row.style.transition = `opacity 0.25s ease, transform 0.25s ${ease}`;
                            row.style.opacity = '0';
                            row.style.transform = `translateX(20px) scale(0.95)`;

                            const siblings = allRows.filter((_, i) => i !== dragIdx);
                            siblings.forEach(r => {
                                r.style.transition = `transform 0.3s ${ease}`;
                                r.style.transform = '';
                            });

                            await new Promise(r => setTimeout(r, 260));

                            row.style.transition = `height 0.2s ${ease}, padding 0.2s ${ease}, margin 0.2s ${ease}, border 0.2s ${ease}`;
                            row.style.height = '0px';
                            row.style.paddingTop = '0px';
                            row.style.paddingBottom = '0px';
                            row.style.marginTop = '0px';
                            row.style.marginBottom = '0px';
                            row.style.overflow = 'hidden';
                            row.style.borderLeftWidth = '0px';


                            await new Promise(r => setTimeout(r, 220));

                            try {
                                const resp = await fetch(moveUrl, {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ target_section_id: targetSectionId })
                                });
                                const revert = async () => {
                                    FileOps._resetRowStyles(allRows);
                                    const srcCtrR = document.querySelector(`.custom-section-category[data-section-id="${srcSectionId}"] .domain-topos-list`);
                                    if (srcCtrR && srcSec) await FileOps._loadDomainTopologiesInline(editor, srcSec, srcCtrR);
                                };
                                if (!resp.ok) { editor.showToast(`Move failed: ${resp.status}`, 'error'); await revert(); return; }
                                const result = await resp.json();
                                if (result.error) { editor.showToast('Move failed: ' + result.error, 'error'); await revert(); return; }

                                editor.showToast(`Moved "${moveFile.replace(/\.json$/, '')}" → ${dstSec?.name || 'domain'}`, 'success');
                                FileOps._resetRowStyles(allRows);

                                const refreshPromises = [];
                                if (srcSec) {
                                    const srcCtrF = document.querySelector(`.custom-section-category[data-section-id="${srcSectionId}"] .domain-topos-list`);
                                    if (srcCtrF) refreshPromises.push(FileOps._loadDomainTopologiesInline(editor, srcSec, srcCtrF));
                                }
                                if (dstSec && dstCtr) {
                                    refreshPromises.push(
                                        FileOps._loadDomainTopologiesInline(editor, dstSec, dstCtr).then(() => {
                                            const movedName = moveFile.replace(/\.json$/, '');
                                            dstCtr.querySelectorAll('.domain-topo-row').forEach(nr => {
                                                if (nr.querySelector('.topo-entry-name')?.textContent?.trim() === movedName) {
                                                    nr.style.opacity = '0';
                                                    nr.style.transform = 'translateY(-4px)';
                                                    requestAnimationFrame(() => {
                                                        nr.style.transition = `opacity 0.3s ease 0.05s, transform 0.3s ${ease} 0.05s`;
                                                        nr.style.opacity = '1';
                                                        nr.style.transform = '';
                                                        nr.style.background = `${dstColor}20`;
                                                        setTimeout(() => { nr.style.transition = 'background 0.8s ease'; nr.style.background = ''; }, 800);
                                                    });
                                                }
                                            });
                                        })
                                    );
                                }
                                await Promise.all(refreshPromises);
                            } catch (err) {
                                editor.showToast('Move failed: ' + err.message, 'error');
                                FileOps._resetRowStyles(allRows);
                                const srcCtrR = document.querySelector(`.custom-section-category[data-section-id="${srcSectionId}"] .domain-topos-list`);
                                if (srcCtrR && srcSec) await FileOps._loadDomainTopologiesInline(editor, srcSec, srcCtrR);
                            }

                            const dropdown2 = document.getElementById('topologies-dropdown-menu');
                            if (dropdown2) dropdown2.style.overflowY = 'auto';
                            container.style.overflow = '';
                            return;
                        }

                        cleanupDrag();

                        // Same-domain reorder
                        const orderChanged = currentOrder.some((idx, pos) => idx !== pos);
                        const dragPos = currentOrder.indexOf(dragIdx);
                        const finalDy = slotYs[dragPos] - offsets[dragIdx];
                        row.style.transition = `transform 0.2s ${ease}, box-shadow 0.2s, opacity 0.2s`;
                        row.style.transform = finalDy ? `translateY(${finalDy}px)` : '';
                        row.style.boxShadow = '';
                        row.style.opacity = '1';

                        setTimeout(() => {
                            FileOps._resetRowStyles(allRows);
                            if (orderChanged) {
                                const frag = document.createDocumentFragment();
                                currentOrder.forEach(idx => frag.appendChild(allRows[idx]));
                                container.appendChild(frag);
                            }
                        }, 210);
                    };

                    document.addEventListener('mousemove', onMove);
                    document.addEventListener('mouseup', onUp);
                });
            } else {
                row.onclick = (e) => { e.stopPropagation(); if (opts.loadFn) opts.loadFn(row.dataset.filename); };
            }
        });
    },

    _resetRowStyles(rows) {
        rows.forEach(r => {
            r.style.transform = '';
            r.style.transition = '';
            r.style.position = '';
            r.style.zIndex = '';
            r.style.boxShadow = '';
            r.style.opacity = '';
            r.style.cursor = '';
            r.style.background = '';
            r.style.borderRadius = '';
        });
    },

    _showRenameInput(editor, btn, color, container, opts) {
        const existing = container.querySelector('.rename-inline-form');
        if (existing) existing.remove();
        
        const filename = btn.dataset.filename;
        const currentName = btn.querySelector('.topo-entry-name')?.textContent?.trim() || '';
        
        const form = document.createElement('div');
        form.className = 'rename-inline-form';
        const isDark = document.body.classList.contains('dark-mode');
        form.style.cssText = 'display:flex;gap:4px;align-items:center;padding:3px 12px 3px 20px;margin-left:8px;';
        form.innerHTML = `
            <input type="text" value="${currentName}" style="flex:1;padding:4px 6px;background:${isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.04)'};border:1px solid ${color}55;border-radius:4px;color:${isDark ? '#e2e8f0' : '#1e1e32'};font-size:10px;font-family:inherit;outline:none;" onclick="event.stopPropagation();">
            <button style="padding:3px 8px;background:${color};border:none;border-radius:4px;color:#fff;font-size:10px;font-weight:600;cursor:pointer;white-space:nowrap;">OK</button>
            <button style="padding:3px 6px;background:${isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)'};border:1px solid ${isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.12)'};border-radius:4px;color:${isDark ? '#94a3b8' : '#475569'};font-size:10px;cursor:pointer;">X</button>
        `;
        btn.after(form);
        const input = form.querySelector('input');
        const okBtn = form.querySelectorAll('button')[0];
        const cancelBtn = form.querySelectorAll('button')[1];
        input.focus(); input.select();
        
        const doRename = () => {
            const newName = input.value.trim();
            if (!newName || newName === currentName) { form.remove(); return; }
            if (opts.renameFn) opts.renameFn(filename, newName);
            form.remove();
        };
        okBtn.onclick = (e) => { e.stopPropagation(); doRename(); };
        cancelBtn.onclick = (e) => { e.stopPropagation(); form.remove(); };
        input.addEventListener('keydown', (e) => { e.stopPropagation(); if (e.key === 'Enter') doRename(); if (e.key === 'Escape') form.remove(); });
    },

    _showDuplicatePicker(editor, row, srcSectionId, container, opts) {
        const existing = document.getElementById('duplicate-picker-popup');
        if (existing) existing.remove();

        const filename = row.dataset.filename;
        const topoName = (row.querySelector('.topo-entry-name')?.textContent?.trim() || filename).replace(/\.json$/i, '');
        const sections = editor._customSections || [];
        const isDark = document.body.classList.contains('dark-mode');

        const rowRect = row.getBoundingClientRect();
        const popup = document.createElement('div');
        popup.id = 'duplicate-picker-popup';
        popup.style.cssText = `
            position: fixed;
            left: ${rowRect.right + 6}px;
            top: ${rowRect.top}px;
            z-index: 100002;
            min-width: 180px;
            background: ${isDark
                ? 'linear-gradient(135deg, rgba(20,25,40,0.95), rgba(15,20,35,0.98))'
                : 'linear-gradient(135deg, rgba(255,255,255,0.98), rgba(245,248,255,0.95))'};
            border: 1px solid ${isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)'};
            border-radius: 10px;
            padding: 6px;
            box-shadow: ${isDark
                ? '0 8px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.08)'
                : '0 8px 32px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.8)'};
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            font-family: 'Poppins', -apple-system, sans-serif;
        `;

        const titleEl = document.createElement('div');
        titleEl.textContent = 'Duplicate to...';
        titleEl.style.cssText = `font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.6px;color:${isDark ? 'rgba(255,255,255,0.45)' : 'rgba(0,0,0,0.4)'};padding:4px 8px 6px;`;
        popup.appendChild(titleEl);

        const doDuplicate = async (targetSectionId, targetName) => {
            popup.remove();
            try {
                const [topoResp, listResp] = await Promise.all([
                    fetch(`/api/sections/${srcSectionId}/topologies/${filename}`),
                    fetch(`/api/sections/${targetSectionId}/topologies`)
                ]);
                const topoData = await topoResp.json();
                if (topoData.error) { editor.showToast(topoData.error, 'error'); return; }
                const listData = await listResp.json();
                const existingNames = new Set((listData.topologies || []).map(t => (t.name || '').toLowerCase()));

                let copyName = topoName + '_copy';
                let n = 2;
                while (existingNames.has(copyName.toLowerCase())) {
                    copyName = topoName + '_copy' + n;
                    n++;
                }

                const saveResp = await fetch(`/api/sections/${targetSectionId}/save`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: copyName, topology: topoData })
                });
                const result = await saveResp.json();
                if (result.error) { editor.showToast('Duplicate failed: ' + result.error, 'error'); return; }

                editor.showToast(`Duplicated → ${targetName}/${copyName}`, 'success');

                const targetCtr = document.querySelector(`.custom-section-category[data-section-id="${targetSectionId}"] .domain-topos-list`);
                const targetSec = sections.find(s => s.id === targetSectionId);
                if (targetCtr && targetSec) await FileOps._loadDomainTopologiesInline(editor, targetSec, targetCtr);
                if (targetSectionId !== srcSectionId && container) {
                    const srcSec = sections.find(s => s.id === srcSectionId);
                    if (srcSec) await FileOps._loadDomainTopologiesInline(editor, srcSec, container);
                }
            } catch (err) {
                editor.showToast('Duplicate failed: ' + err.message, 'error');
            }
        };

        const createOption = (label, color, onClick) => {
            const btn = document.createElement('button');
            btn.style.cssText = `
                display: flex; align-items: center; gap: 8px; width: 100%;
                padding: 6px 10px; border: none; border-radius: 6px; cursor: pointer;
                background: transparent; color: ${isDark ? '#e2e8f0' : '#1e1e32'};
                font-size: 11px; font-family: inherit; text-align: left;
                transition: background 0.12s;
            `;
            const dot = document.createElement('span');
            dot.style.cssText = `width:8px;height:8px;border-radius:50%;background:${color};flex-shrink:0;`;
            const text = document.createElement('span');
            text.textContent = label;
            text.style.cssText = 'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;';
            btn.appendChild(dot);
            btn.appendChild(text);
            btn.onmouseenter = () => { btn.style.background = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)'; };
            btn.onmouseleave = () => { btn.style.background = 'transparent'; };
            btn.onclick = (e) => { e.stopPropagation(); onClick(); };
            return btn;
        };

        const srcSec = sections.find(s => s.id === srcSectionId);
        if (srcSec) {
            const sameBtn = createOption(`${srcSec.name} (same)`, srcSec.color || '#3b82f6', () => doDuplicate(srcSectionId, srcSec.name));
            popup.appendChild(sameBtn);
        }

        const otherSections = sections.filter(s => s.id !== srcSectionId);
        if (otherSections.length > 0 && srcSec) {
            const sep = document.createElement('div');
            sep.style.cssText = `height:1px;background:${isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)'};margin:4px 6px;`;
            popup.appendChild(sep);
        }
        otherSections.forEach(sec => {
            popup.appendChild(createOption(sec.name, sec.color || '#3b82f6', () => doDuplicate(sec.id, sec.name)));
        });

        popup.addEventListener('mousedown', (e) => e.stopPropagation());
        popup.addEventListener('click', (e) => e.stopPropagation());

        document.body.appendChild(popup);

        requestAnimationFrame(() => {
            const pr = popup.getBoundingClientRect();
            if (pr.right > window.innerWidth - 8) popup.style.left = `${rowRect.left - pr.width - 6}px`;
            if (pr.bottom > window.innerHeight - 8) popup.style.top = `${window.innerHeight - pr.height - 8}px`;
        });

        const closePicker = (e) => {
            if (!popup.contains(e.target)) { popup.remove(); document.removeEventListener('mousedown', closePicker); }
        };
        setTimeout(() => document.addEventListener('mousedown', closePicker), 50);
    },

    _updateTopoBtnIcon(editor) {
        const svg = document.getElementById('topo-btn-icon');
        if (!svg) return;
        const sections = editor._customSections || [];
        const colors = sections.map(s => s.color).filter(Boolean);
        const n = Math.min(colors.length, 4);

        if (n === 0) {
            svg.innerHTML = `
                <polygon points="12 2 2 7 12 12 22 7 12 2" stroke="currentColor" fill="none" stroke-width="1.8"/>
                <polyline points="2 12 12 17 22 12" stroke="currentColor" fill="none" stroke-width="1.8"/>
                <polyline points="2 17 12 22 22 17" stroke="currentColor" fill="none" stroke-width="1.8"/>`;
            return;
        }

        // Build layers bottom-up: each domain gets its own layer
        // Vertical space: viewBox 0-24, usable ~2-22
        // Top layer is always a filled polygon, rest are polylines
        const layers = colors.slice(0, 4);
        let inner = '';

        if (n === 1) {
            inner = `<polygon points="12 4 2 10 12 16 22 10 12 4" stroke="${layers[0]}" fill="${layers[0]}30" stroke-width="1.8"/>`;
        } else if (n === 2) {
            inner = `
                <polygon points="12 2 2 8 12 14 22 8 12 2" stroke="${layers[0]}" fill="${layers[0]}30" stroke-width="1.8"/>
                <polyline points="2 14 12 20 22 14" stroke="${layers[1]}" fill="none" stroke-width="1.8"/>`;
        } else if (n === 3) {
            inner = `
                <polygon points="12 2 2 7 12 12 22 7 12 2" stroke="${layers[0]}" fill="${layers[0]}30" stroke-width="1.8"/>
                <polyline points="2 12 12 17 22 12" stroke="${layers[1]}" fill="none" stroke-width="1.8"/>
                <polyline points="2 17 12 22 22 17" stroke="${layers[2]}" fill="none" stroke-width="1.8"/>`;
        } else {
            inner = `
                <polygon points="12 1 2 5.5 12 10 22 5.5 12 1" stroke="${layers[0]}" fill="${layers[0]}30" stroke-width="1.6"/>
                <polyline points="2 10 12 14.5 22 10" stroke="${layers[1]}" fill="none" stroke-width="1.6"/>
                <polyline points="2 14.5 12 19 22 14.5" stroke="${layers[2]}" fill="none" stroke-width="1.6"/>
                <polyline points="2 19 12 23.5 22 19" stroke="${layers[3]}" fill="none" stroke-width="1.6"/>`;
        }

        svg.innerHTML = inner;
    },

    // ========================================================================
    // CUSTOM TOPOLOGY SECTIONS
    // ========================================================================

    _sectionIcons() {
        return [
            { id: 'folder', svg: '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'server', svg: '<rect x="2" y="2" width="20" height="8" rx="2" stroke="currentColor" stroke-width="2" fill="none"/><rect x="2" y="14" width="20" height="8" rx="2" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="6" cy="6" r="1" fill="currentColor"/><circle cx="6" cy="18" r="1" fill="currentColor"/>' },
            { id: 'globe', svg: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10A15.3 15.3 0 0 1 12 2z" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'lab', svg: '<path d="M9 3h6M12 3v7l5 8H7l5-8V3" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>' },
            { id: 'shield', svg: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'zap', svg: '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'layers', svg: '<polygon points="12 2 2 7 12 12 22 7" stroke="currentColor" stroke-width="2" fill="none"/><polyline points="2 17 12 22 22 17" stroke="currentColor" stroke-width="2" fill="none"/><polyline points="2 12 12 17 22 12" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'cpu', svg: '<rect x="4" y="4" width="16" height="16" rx="2" stroke="currentColor" stroke-width="2" fill="none"/><rect x="9" y="9" width="6" height="6" stroke="currentColor" stroke-width="2" fill="none"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3" stroke="currentColor" stroke-width="2"/>' },
            { id: 'wifi', svg: '<path d="M5 12.55a11 11 0 0 1 14.08 0M1.42 9a16 16 0 0 1 21.16 0M8.53 16.11a6 6 0 0 1 6.95 0M12 20h.01" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>' },
            { id: 'star', svg: '<polygon points="12,2 15,9 22,9 17,14 19,21 12,17 5,21 7,14 2,9 9,9" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'network', svg: '<circle cx="6" cy="12" r="3" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="18" cy="6" r="3" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="18" cy="18" r="3" stroke="currentColor" stroke-width="2" fill="none"/><path d="M9 12h6M15 8l-6 4M15 16l-6-4" stroke="currentColor" stroke-width="2"/>' },
            { id: 'box', svg: '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" stroke="currentColor" stroke-width="2" fill="none"/><polyline points="3.27 6.96 12 12.01 20.73 6.96" stroke="currentColor" stroke-width="2" fill="none"/><line x1="12" y1="22.08" x2="12" y2="12" stroke="currentColor" stroke-width="2"/>' },
            { id: 'tool', svg: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'link', svg: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" stroke="currentColor" stroke-width="2" fill="none"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'cloud', svg: '<path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'lock', svg: '<rect x="3" y="11" width="18" height="11" rx="2" stroke="currentColor" stroke-width="2" fill="none"/><path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'alert', svg: '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="currentColor" stroke-width="2" fill="none"/><line x1="12" y1="9" x2="12" y2="13" stroke="currentColor" stroke-width="2"/><line x1="12" y1="17" x2="12.01" y2="17" stroke="currentColor" stroke-width="2"/>' },
            { id: 'bug', svg: '<path d="M8 2l1.88 1.88M16 2l-1.88 1.88M9 7.13v-1a3.003 3.003 0 1 1 6 0v1" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/><path d="M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6z" stroke="currentColor" stroke-width="2" fill="none"/><path d="M12 20v-9M6.53 9C4.6 8.8 3 7.1 3 5M17.47 9c1.93-.2 3.53-1.9 3.53-4M6 13H2M22 13h-4M6 17H2M22 17h-4" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>' },
        ];
    },

    _sectionColors() {
        return ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#FF5E1F', '#14b8a6', '#6366f1', '#f472b6', '#a3e635'];
    },

    async loadCustomSections(editor) {
        try {
            const resp = await fetch('/api/sections');
            const data = await resp.json();
            editor._customSections = data.sections || [];
            FileOps._renderCustomSectionsInDropdown(editor);
            FileOps._updateTopoBtnIcon(editor);
        } catch (_) {
            editor._customSections = [];
        }
    },

    _renderCustomSectionsInDropdown(editor) {
        const dropdown = document.getElementById('topologies-dropdown-menu');
        if (!dropdown) return;
        
        dropdown.querySelectorAll('.custom-section-category').forEach(el => el.remove());
        
        const anchor = document.getElementById('topology-domains-header');
        const insertAfter = anchor ? anchor.nextSibling : null;
        
        if (!editor._domainCollapsed) {
            editor._domainCollapsed = {};
            for (const s of (editor._customSections || [])) {
                editor._domainCollapsed[s.id] = true;
            }
        }

        for (const sec of (editor._customSections || [])) {
            const div = document.createElement('div');
            div.className = 'menu-category custom-section-category';
            div.dataset.sectionId = sec.id;
            const isDkDomain = document.body.classList.contains('dark-mode');
            div.style.cssText = `background: ${sec.color || '#3b82f6'}${isDkDomain ? '22' : '28'}; padding: 0; border-left: 3px solid ${sec.color || '#3b82f6'}${isDkDomain ? '55' : '90'};`;
            
            const icon = (FileOps._sectionIcons().find(i => i.id === sec.icon) || FileOps._sectionIcons()[0]).svg;
            const collapsed = editor._domainCollapsed[sec.id] || false;
            
            const btnColor = isDkDomain ? '#e2e8f0' : '#1e1e32';
            div.innerHTML = `
                <div class="domain-title" style="color: ${sec.color}; display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 800; letter-spacing: 0.5px; padding: 8px 12px; cursor: default; user-select: none;">
                    <svg class="dd-grip" viewBox="0 0 24 24" width="10" height="10" style="color:${sec.color}; flex-shrink:0; opacity:0.45; cursor:grab;"><circle cx="9" cy="7" r="1.3" fill="currentColor"/><circle cx="15" cy="7" r="1.3" fill="currentColor"/><circle cx="9" cy="12" r="1.3" fill="currentColor"/><circle cx="15" cy="12" r="1.3" fill="currentColor"/><circle cx="9" cy="17" r="1.3" fill="currentColor"/><circle cx="15" cy="17" r="1.3" fill="currentColor"/></svg>
                    <svg viewBox="0 0 24 24" width="16" height="16" style="color:${sec.color}; flex-shrink:0;">${icon}</svg>
                    <span style="flex:1;">${(sec.name || 'Untitled').toUpperCase()}</span>
                    <svg class="domain-chevron" viewBox="0 0 24 24" width="12" height="12" style="color:${sec.color}; flex-shrink:0; opacity:0.6; transition: transform 0.2s; transform: rotate(${collapsed ? '-90deg' : '0deg'});">
                        <polyline points="6 9 12 15 18 9" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <div class="domain-body" style="display: ${collapsed ? 'none' : 'block'}; padding: 0 0 6px;">
                    <div style="display:flex;gap:4px;padding:2px 10px;">
                        <button data-action="save" style="flex:1;display:flex;align-items:center;justify-content:center;gap:5px;padding:5px 0;background:${sec.color}${isDkDomain ? '18' : '15'};border:1px solid ${sec.color}${isDkDomain ? '30' : '40'};border-radius:5px;color:${btnColor};font-size:11px;font-weight:600;cursor:pointer;font-family:inherit;transition:background 0.15s;">
                            <svg viewBox="0 0 24 24" width="12" height="12" style="flex-shrink:0;"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" stroke="currentColor" stroke-width="2" fill="none"/><polyline points="17 21 17 13 7 13 7 21" stroke="currentColor" stroke-width="2" fill="none"/><polyline points="7 3 7 8 15 8" stroke="currentColor" stroke-width="2" fill="none"/></svg>
                            Save
                        </button>
                        <button data-action="load-file" style="flex:1;display:flex;align-items:center;justify-content:center;gap:5px;padding:5px 0;background:${sec.color}${isDkDomain ? '18' : '15'};border:1px solid ${sec.color}${isDkDomain ? '30' : '40'};border-radius:5px;color:${btnColor};font-size:11px;font-weight:600;cursor:pointer;font-family:inherit;transition:background 0.15s;">
                            <svg viewBox="0 0 24 24" width="12" height="12" style="flex-shrink:0;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="2" fill="none"/><polyline points="7 10 12 15 17 10" stroke="currentColor" stroke-width="2" fill="none"/><line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" stroke-width="2"/></svg>
                            Load
                        </button>
                    </div>
                    <div class="domain-save-form" style="display:none;padding:4px 10px 8px;"></div>
                    <div class="domain-topos-list" style="max-height:160px;overflow-y:auto;"></div>
                </div>
            `;
            
            const bodyEl = div.querySelector('.domain-body');
            const chevron = div.querySelector('.domain-chevron');

            const baseBg = `${sec.color}${isDkDomain ? '18' : '15'}`;
            const hoverBg = `${sec.color}${isDkDomain ? '30' : '35'}`;
            const activeBg = `${sec.color}${isDkDomain ? '45' : '50'}`;
            div.querySelectorAll('[data-action="save"],[data-action="load-file"]').forEach(btn => {
                btn.addEventListener('mouseenter', () => { if (!btn.dataset.pressed) btn.style.background = hoverBg; });
                btn.addEventListener('mouseleave', () => { if (!btn.dataset.pressed) btn.style.background = baseBg; });
            });

            const saveBtn = div.querySelector('[data-action="save"]');
            const loadFileBtn = div.querySelector('[data-action="load-file"]');
            const saveForm = div.querySelector('.domain-save-form');
            const _setPressed = (btn, on) => {
                if (on) { btn.dataset.pressed = '1'; btn.style.background = activeBg; btn.style.borderColor = `${sec.color}60`; }
                else { delete btn.dataset.pressed; btn.style.background = baseBg; btn.style.borderColor = `${sec.color}30`; }
            };
            saveBtn.onclick = (e) => {
                e.stopPropagation();
                if (editor.objects.length === 0) { editor.showToast('Nothing to save — canvas is empty', 'warning'); return; }
                const isOpen = saveForm.style.display !== 'none';
                saveForm.style.display = isOpen ? 'none' : 'block';
                _setPressed(saveBtn, !isOpen);
                if (!isOpen) {
                    const defaultName = 'topology_' + new Date().toISOString().slice(0, 10);
                    const isDk = document.body.classList.contains('dark-mode');
                    saveForm.innerHTML = `
                        <div style="display:flex;gap:4px;align-items:center;">
                            <input class="domain-save-name" type="text" value="${defaultName}" placeholder="Topology name"
                                style="flex:1;padding:5px 8px;background:${isDk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.04)'};border:1px solid ${sec.color}55;
                                border-radius:5px;color:${isDk ? '#e2e8f0' : '#1e1e32'};font-size:11px;font-family:inherit;outline:none;"
                                onclick="event.stopPropagation();">
                            <button class="domain-save-confirm" style="padding:5px 10px;background:${sec.color};border:none;
                                border-radius:5px;color:#fff;font-size:11px;font-weight:600;cursor:pointer;font-family:inherit;white-space:nowrap;">Save</button>
                        </div>
                    `;
                    const input = saveForm.querySelector('.domain-save-name');
                    const confirmBtn = saveForm.querySelector('.domain-save-confirm');
                    input.focus();
                    input.select();
                    const doSave = async () => {
                        const name = input.value.trim();
                        if (!name) { editor.showToast('Enter a topology name', 'warning'); return; }
                        confirmBtn.textContent = '...';
                        confirmBtn.disabled = true;
                        try {
                            const resp = await fetch('/api/sections/' + sec.id + '/save', {
                                method: 'POST', headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ name, topology: FileOps.generateTopologyData(editor) })
                            });
                            const result = await resp.json();
                            if (result.error) { editor.showToast('Save failed: ' + result.error, 'error'); }
                            else {
                                FileOps.updateTopologyIndicator(name, sec.name, sec.color, sec.id);
                                editor.showToast('Saved to ' + sec.name, 'success');
                                saveForm.style.display = 'none';
                                _setPressed(saveBtn, false);
                                FileOps._loadDomainTopologiesInline(editor, sec, div.querySelector('.domain-topos-list'));
                            }
                        } catch (err) { editor.showToast('Save failed: ' + err.message, 'error'); }
                        confirmBtn.textContent = 'Save';
                        confirmBtn.disabled = false;
                    };
                    confirmBtn.onclick = (ev) => { ev.stopPropagation(); doSave(); };
                    input.addEventListener('keydown', (ev) => { ev.stopPropagation(); if (ev.key === 'Enter') doSave(); if (ev.key === 'Escape') { saveForm.style.display = 'none'; _setPressed(saveBtn, false); } });
                }
            };

            loadFileBtn.onclick = (e) => {
                e.stopPropagation();
                _setPressed(loadFileBtn, true);
                const fileInput = document.createElement('input');
                fileInput.type = 'file';
                fileInput.accept = '.json';
                fileInput.onchange = async () => {
                    const file = fileInput.files[0];
                    if (!file) { _setPressed(loadFileBtn, false); return; }
                    try {
                        const text = await file.text();
                        const data = JSON.parse(text);
                        const name = file.name.replace(/\.json$/i, '');
                        const resp = await fetch(`/api/sections/${sec.id}/save`, {
                            method: 'POST', headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ name, topology: data })
                        });
                        const result = await resp.json();
                        if (result.error) { editor.showToast('Load failed: ' + result.error, 'error'); return; }
                        editor.loadTopologyFromData(data);
                        FileOps.updateTopologyIndicator(name, sec.name, sec.color, sec.id);
                        editor.showToast(`Loaded and saved to ${sec.name}`, 'success');
                        FileOps._loadDomainTopologiesInline(editor, sec, div.querySelector('.domain-topos-list'));
                        const dropdown = document.getElementById('topologies-dropdown-menu');
                        if (dropdown) dropdown.style.display = 'none';
                    } catch (err) { editor.showToast('Failed to load file: ' + err.message, 'error'); }
                    _setPressed(loadFileBtn, false);
                };
                fileInput.addEventListener('cancel', () => _setPressed(loadFileBtn, false));
                fileInput.click();
            };
            
            const titleHandle = div.querySelector('.domain-title');
            titleHandle.addEventListener('mousedown', (e) => {
                if (e.button !== 0) return;
                e.preventDefault();
                let startY = e.clientY;
                const startX = e.clientX;
                let dragging = false;
                let allDomains = [];
                let offsets = [];      // offsetTop relative to parent (scroll-proof)
                let heights = [];
                let slotYs = [];
                let currentOrder = [];
                let dragIdx = -1;
                const ease = 'cubic-bezier(0.22, 1, 0.36, 1)';

                const applyTransforms = () => {
                    for (let pos = 0; pos < currentOrder.length; pos++) {
                        const idx = currentOrder[pos];
                        if (idx === dragIdx) continue;
                        const dy = slotYs[pos] - offsets[idx];
                        allDomains[idx].style.transition = `transform 0.25s ${ease}`;
                        allDomains[idx].style.transform = dy ? `translateY(${dy}px)` : '';
                    }
                };

                let layoutReady = false;

                const recalcLayout = () => {
                    allDomains.forEach(d => { d.style.transform = ''; d.style.transition = 'none'; });
                    offsets = allDomains.map(d => d.offsetTop);
                    heights = allDomains.map(d => d.offsetHeight);
                    currentOrder = allDomains.map((_, i) => i);
                    slotYs = [];
                    let y = offsets[0];
                    for (let i = 0; i < allDomains.length; i++) {
                        slotYs.push(y);
                        if (i < allDomains.length - 1) {
                            const gap = offsets[i + 1] - (offsets[i] + heights[i]);
                            y += heights[i] + Math.max(gap, 0);
                        }
                    }
                    layoutReady = true;
                };

                const onMove = (ev) => {
                    if (!dragging && Math.abs(ev.clientY - startY) + Math.abs(ev.clientX - startX) < 6) return;

                    if (!dragging) {
                        allDomains = [...dropdown.querySelectorAll('.custom-section-category')];
                        if (allDomains.length < 2) { cleanup(); return; }
                        dragIdx = allDomains.indexOf(div);
                        if (dragIdx < 0) { cleanup(); return; }
                        dragging = true;

                        dropdown.style.overflowY = 'hidden';

                        let hasOpenBodies = false;
                        allDomains.forEach(d => {
                            const body = d.querySelector('.domain-body');
                            if (body && body.style.display !== 'none') {
                                hasOpenBodies = true;
                                body.dataset.wasOpen = 'true';
                                const h = body.scrollHeight;
                                body.style.maxHeight = h + 'px';
                                body.style.overflow = 'hidden';
                                body.style.transition = 'none';
                                body.offsetHeight;
                                body.style.transition = `max-height 0.25s ${ease}, opacity 0.2s ease`;
                                body.style.maxHeight = '0px';
                                body.style.opacity = '0';
                            }
                        });

                        const setupDelay = hasOpenBodies ? 270 : 0;
                        const oldDragOffset = div.offsetTop;
                        setTimeout(() => {
                            recalcLayout();
                            // Compensate startY for layout shift after bodies collapsed
                            const newDragOffset = offsets[dragIdx];
                            const layoutShift = newDragOffset - oldDragOffset;
                            startY += layoutShift;

                            allDomains.forEach((d, i) => {
                                d.style.position = 'relative';
                                d.style.zIndex = i === dragIdx ? '100' : '1';
                                if (i === dragIdx) {
                                    d.style.boxShadow = '0 8px 24px rgba(0,0,0,0.32)';
                                    d.style.opacity = '0.95';
                                }
                            });
                        }, setupDelay);

                        allDomains.forEach((d, i) => {
                            d.style.position = 'relative';
                            if (i === dragIdx) {
                                d.style.zIndex = '100';
                                d.style.boxShadow = '0 8px 24px rgba(0,0,0,0.32)';
                                d.style.opacity = '0.95';
                                d.style.transition = 'box-shadow 0.15s, opacity 0.15s';
                            } else {
                                d.style.zIndex = '1';
                            }
                        });

                        document.body.style.cursor = 'grabbing';
                        titleHandle.style.cursor = 'grabbing';
                        const gripEl = div.querySelector('.dd-grip');
                        if (gripEl) gripEl.style.cursor = 'grabbing';
                    }

                    const dy = ev.clientY - startY;
                    div.style.transform = `translateY(${dy}px)`;
                    div.style.transition = 'none';

                    if (!layoutReady || !heights.length) return;

                    const dragMid = offsets[dragIdx] + dy + heights[dragIdx] / 2;
                    const dragPos = currentOrder.indexOf(dragIdx);

                    if (dragPos > 0) {
                        const aboveIdx = currentOrder[dragPos - 1];
                        const aboveMid = slotYs[dragPos - 1] + heights[aboveIdx] * 0.45;
                        if (dragMid < aboveMid) {
                            currentOrder.splice(dragPos, 1);
                            currentOrder.splice(dragPos - 1, 0, dragIdx);
                            applyTransforms();
                        }
                    }

                    if (dragPos < currentOrder.length - 1) {
                        const belowIdx = currentOrder[dragPos + 1];
                        const belowMid = slotYs[dragPos + 1] + heights[belowIdx] * 0.55;
                        if (dragMid > belowMid) {
                            currentOrder.splice(dragPos, 1);
                            currentOrder.splice(dragPos + 1, 0, dragIdx);
                            applyTransforms();
                        }
                    }
                };

                const cleanup = () => {
                    document.removeEventListener('mousemove', onMove);
                    document.removeEventListener('mouseup', onUp);
                    document.body.style.cursor = '';
                    titleHandle.style.cursor = '';
                    const gripEl = div.querySelector('.dd-grip');
                    if (gripEl) gripEl.style.cursor = 'grab';
                    dropdown.style.overflowY = '';
                };

                const onUp = async () => {
                    cleanup();
                    if (!dragging) {
                        const isCollapsed = bodyEl.style.display === 'none';
                        bodyEl.style.display = isCollapsed ? 'block' : 'none';
                        chevron.style.transform = isCollapsed ? 'rotate(0deg)' : 'rotate(-90deg)';
                        editor._domainCollapsed[sec.id] = !isCollapsed;
                        return;
                    }

                    const orderChanged = currentOrder.some((idx, pos) => idx !== pos);

                    const dragPos = currentOrder.indexOf(dragIdx);
                    const finalDy = layoutReady ? (slotYs[dragPos] - offsets[dragIdx]) : 0;
                    div.style.transition = `transform 0.22s ${ease}, box-shadow 0.22s, opacity 0.22s`;
                    div.style.transform = finalDy ? `translateY(${finalDy}px)` : '';
                    div.style.boxShadow = '';
                    div.style.opacity = '1';

                    setTimeout(async () => {
                        if (orderChanged) {
                            const frag = document.createDocumentFragment();
                            currentOrder.forEach(idx => frag.appendChild(allDomains[idx]));
                            const anchor = document.getElementById('topology-domains-header');
                            if (anchor && anchor.nextSibling) {
                                dropdown.insertBefore(frag, anchor.nextSibling);
                            } else {
                                dropdown.appendChild(frag);
                            }
                        }

                        allDomains.forEach(d => {
                            d.style.transition = '';
                            d.style.transform = '';
                            d.style.position = '';
                            d.style.zIndex = '';
                            d.style.boxShadow = '';
                            d.style.opacity = '';
                        });

                        allDomains.forEach(d => {
                            const body = d.querySelector('.domain-body');
                            if (body && body.dataset.wasOpen === 'true') {
                                delete body.dataset.wasOpen;
                                body.style.transition = 'none';
                                body.style.maxHeight = '0px';
                                body.style.opacity = '0';
                                body.style.overflow = 'hidden';
                                body.offsetHeight;
                                const targetH = body.scrollHeight || 200;
                                body.style.transition = `max-height 0.3s ${ease}, opacity 0.25s ease`;
                                body.style.maxHeight = targetH + 'px';
                                body.style.opacity = '1';
                                setTimeout(() => {
                                    body.style.maxHeight = '';
                                    body.style.opacity = '';
                                    body.style.overflow = '';
                                    body.style.transition = '';
                                }, 320);
                            }
                        });

                        if (!orderChanged) return;

                        const finalIds = currentOrder.map(i => allDomains[i].dataset.sectionId);
                        const sections = editor._customSections || [];
                        const reordered = finalIds.map(id => sections.find(s => s.id === id)).filter(Boolean);

                        if (reordered.length !== sections.length) return;

                        editor._customSections = reordered;
                        FileOps._updateTopoBtnIcon(editor);
                        try {
                            await fetch('/api/sections/reorder', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ sections: reordered })
                            });
                        } catch (_) {}
                    }, 230);
                };

                document.addEventListener('mousemove', onMove);
                document.addEventListener('mouseup', onUp);
            });

            if (insertAfter) dropdown.insertBefore(div, insertAfter);
            else if (anchor) anchor.after(div);
            else dropdown.appendChild(div);
            
            FileOps._loadDomainTopologiesInline(editor, sec, div.querySelector('.domain-topos-list'));
        }
    },

    async _loadDomainTopologiesInline(editor, section, container) {
        try {
            const resp = await fetch(`/api/sections/${section.id}/topologies`);
            const data = await resp.json();
            const topos = data.topologies || [];
            if (topos.length === 0) {
                container.innerHTML = `<div style="padding:4px 12px 6px;font-size:10px;color:#64748b;font-style:italic;">No topologies yet</div>`;
                return;
            }
            FileOps._renderTopoEntries(editor, container, topos, section.color, {
                sectionId: section.id,
                section: section,
                loadFn: async (filename) => {
                    const dropdown = document.getElementById('topologies-dropdown-menu');
                    if (dropdown) dropdown.style.display = 'none';
                    try {
                        const r = await fetch(`/api/sections/${section.id}/topologies/${filename}`);
                        const d = await r.json();
                        if (d.error) { editor.showToast(d.error, 'error'); return; }
                        editor.loadTopologyFromData(d);
                        const topoName = filename.replace(/\.json$/i, '');
                        FileOps.updateTopologyIndicator(topoName, section.name, section.color, section.id);
                        editor.showToast(`Loaded from ${section.name}`, 'success');
                    } catch (err) { editor.showToast(err.message, 'error'); }
                },
                renameFn: async (oldFile, newName) => {
                    try {
                        const r = await fetch(`/api/sections/${section.id}/topologies/${oldFile}/rename`, {
                            method: 'POST', headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ name: newName })
                        });
                        const result = await r.json();
                        if (result.error) { editor.showToast('Rename failed: ' + result.error, 'error'); return; }
                        editor.showToast('Renamed', 'success');
                        FileOps._loadDomainTopologiesInline(editor, section, container);
                    } catch (e) { editor.showToast('Rename failed: ' + e.message, 'error'); }
                },
                deleteFn: async (filename) => {
                    try {
                        const r = await fetch(`/api/sections/${section.id}/topologies/${filename}/delete-file`, { method: 'POST' });
                        const res = await r.json();
                        if (res.error) { editor.showToast('Delete failed: ' + res.error, 'error'); return; }
                        editor.showToast('Deleted', 'success');
                        FileOps._loadDomainTopologiesInline(editor, section, container);
                    } catch (e) { editor.showToast('Delete failed: ' + e.message, 'error'); }
                }
            });
        } catch (_) {
            container.innerHTML = `<div style="padding:4px 12px;font-size:10px;color:#ef4444;">Failed to load</div>`;
        }
    },

    async saveToSection(editor, section, topoName) {
        if (editor.objects.length === 0) { editor.showToast('Nothing to save', 'warning'); return; }
        const name = topoName || prompt(`Save to "${section.name}" as:`, 'topology_' + Date.now());
        if (!name) return;
        try {
            const resp = await fetch(`/api/sections/${section.id}/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, topology: FileOps.generateTopologyData(editor) })
            });
            const result = await resp.json();
            if (result.error) editor.showToast('Save failed: ' + result.error, 'error');
            else editor.showToast(`Saved to ${section.name}`, 'success');
        } catch (e) { editor.showToast('Save failed: ' + e.message, 'error'); }
    },

    async loadFromSection(editor, section) {
        try {
            const resp = await fetch(`/api/sections/${section.id}/topologies`);
            const data = await resp.json();
            const topos = data.topologies || [];
            if (topos.length === 0) { editor.showToast(`No topologies in domain "${section.name}"`, 'info'); return; }
            FileOps._showSectionTopologyPicker(editor, section, topos);
        } catch (e) { editor.showToast('Load failed: ' + e.message, 'error'); }
    },

    _showSectionTopologyPicker(editor, section, topos) {
        const existing = document.getElementById('section-topo-picker');
        if (existing) existing.remove();
        
        const div = document.createElement('div');
        div.id = 'section-topo-picker';
        div.className = 'liquid-glass-dropdown';
        div.onclick = (e) => e.stopPropagation();
        
        const anchor = document.getElementById('btn-topologies') || document.querySelector('.top-bar');
        const rect = anchor ? anchor.getBoundingClientRect() : { left: 120, bottom: 48 };
        div.style.cssText = `display:block;position:fixed;left:${rect.left}px;top:${rect.bottom+4}px;z-index:1000000;min-width:260px;max-height:380px;overflow-y:auto;`;
        
        let html = `<div style="font-size:10px;font-weight:600;padding:6px 12px 4px;text-transform:uppercase;letter-spacing:0.8px;color:${section.color};">${section.name}</div>`;
        topos.forEach(t => {
            html += `<button class="liquid-menu-item sec-topo-item" data-filename="${t.filename}" style="border-left:3px solid ${section.color};color:${section.color};">${t.name}</button>`;
        });
        div.innerHTML = html;
        
        div.querySelectorAll('.sec-topo-item').forEach(el => {
            el.onclick = async () => {
                div.remove(); closeHandler();
                try {
                    const r = await fetch(`/api/sections/${section.id}/topologies/${el.dataset.filename}`);
                    const d = await r.json();
                    if (d.error) { editor.showToast(d.error, 'error'); return; }
                    editor.loadTopologyFromData(d);
                    const topoName = el.dataset.filename.replace(/\.json$/i, '');
                    FileOps.updateTopologyIndicator(topoName, section.name, section.color, section.id);
                    editor.showToast(`Loaded from ${section.name}`, 'success');
                } catch (e) { editor.showToast(e.message, 'error'); }
            };
        });
        
        document.body.appendChild(div);
        const closeHandler = (e) => {
            if (e && div.contains(e.target)) return;
            div.remove(); document.removeEventListener('click', closeHandler); document.removeEventListener('keydown', escHandler);
        };
        const escHandler = (e) => { if (e.key === 'Escape') closeHandler(); };
        setTimeout(() => { document.addEventListener('click', closeHandler); document.addEventListener('keydown', escHandler); }, 0);
    },

    showManageSections(editor) {
        const existing = document.getElementById('manage-sections-panel');
        if (existing) { existing.remove(); return; }
        
        const dk = editor.darkMode !== false;
        const t = {
            bg: dk ? 'rgba(17, 25, 40, 0.78)' : 'rgba(255, 255, 255, 0.78)',
            border: dk ? 'rgba(255, 255, 255, 0.125)' : 'rgba(0, 0, 0, 0.08)',
            text: dk ? 'rgba(255, 255, 255, 0.9)' : 'rgba(0, 0, 0, 0.85)',
            muted: dk ? 'rgba(255, 255, 255, 0.45)' : 'rgba(0, 0, 0, 0.45)',
            card: dk ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.03)',
            cardBorder: dk ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)',
            input: dk ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.04)',
            inputBorder: dk ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.12)',
            iconStroke: dk ? 'rgba(255, 255, 255, 0.75)' : 'rgba(0, 0, 0, 0.5)',
            hover: dk ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.05)',
        };
        
        const panel = document.createElement('div');
        panel.id = 'manage-sections-panel';
        panel.onclick = (e) => e.stopPropagation();
        
        const anchor = document.getElementById('btn-topologies');
        const rect = anchor ? anchor.getBoundingClientRect() : { left: 120, bottom: 48 };
        
        panel.style.cssText = `
            position: fixed; left: ${rect.left}px; top: ${rect.bottom + 6}px;
            width: 360px; max-height: 75vh; overflow-y: auto;
            background: ${t.bg};
            border: 1px solid ${t.border};
            border-radius: 16px; padding: 18px;
            z-index: 1000001;
            box-shadow: 0 8px 32px rgba(0, 0, 0, ${dk ? 0.5 : 0.15}), 0 0 0 1px ${t.border};
            font-family: 'Poppins', -apple-system, sans-serif;
            color: ${t.text};
            backdrop-filter: blur(16px) saturate(180%);
            -webkit-backdrop-filter: blur(16px) saturate(180%);
            animation: liquidDropdownFadeIn 0.2s ease-out;
        `;
        
        const icons = FileOps._sectionIcons();
        const colors = FileOps._sectionColors();
        
        const render = () => {
            let html = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
                <div style="display:flex;align-items:center;gap:8px;">
                    <button id="ms-back" style="background:${t.hover};border:1px solid ${t.cardBorder};border-radius:6px;color:${t.text};cursor:pointer;padding:4px 6px;display:flex;align-items:center;justify-content:center;transition:all 0.15s;"
                        onmouseenter="this.style.background='${t.input}';this.style.borderColor='${t.muted}'" onmouseleave="this.style.background='${t.hover}';this.style.borderColor='${t.cardBorder}'" title="Back to Topologies">
                        <svg viewBox="0 0 24 24" width="16" height="16" style="stroke:currentColor;"><polyline points="15 18 9 12 15 6" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    </button>
                    <svg viewBox="0 0 24 24" width="18" height="18" style="stroke:${t.muted};">
                        <polygon points="12 2 2 7 12 12 22 7" stroke="currentColor" stroke-width="2" fill="none"/>
                        <polyline points="2 17 12 22 22 17" stroke="currentColor" stroke-width="2" fill="none"/>
                        <polyline points="2 12 12 17 22 12" stroke="currentColor" stroke-width="2" fill="none"/>
                    </svg>
                    <span style="font-size:14px;font-weight:600;">Topology Domains</span>
                </div>
                <button id="ms-close" style="background:none;border:none;color:${t.muted};cursor:pointer;font-size:16px;padding:2px 6px;border-radius:6px;transition:background 0.15s;"
                    onmouseenter="this.style.background='${t.hover}'" onmouseleave="this.style.background='none'">✕</button>
            </div>`;
            
            const sections = editor._customSections || [];
            if (sections.length === 0) {
                html += `<div style="text-align:center;padding:16px 0;color:${t.muted};font-size:12px;">No domains yet. Create one below.</div>`;
            }
            
            sections.forEach(sec => {
                const iconSvg = (icons.find(i => i.id === sec.icon) || icons[0]).svg;
                html += `<div class="ms-domain-row" data-id="${sec.id}" style="margin-bottom:6px;background:${t.card};border:1px solid ${t.cardBorder};border-radius:10px;border-left:3px solid ${sec.color};">
                    <div style="display:flex;align-items:center;gap:10px;padding:10px 12px;">
                        <div class="ms-drag-handle" style="cursor:grab;flex-shrink:0;color:${t.muted};display:flex;align-items:center;padding:0 2px;" title="Drag to reorder">
                            <svg viewBox="0 0 24 24" width="14" height="14" style="color:inherit;"><circle cx="9" cy="6" r="1.5" fill="currentColor"/><circle cx="15" cy="6" r="1.5" fill="currentColor"/><circle cx="9" cy="12" r="1.5" fill="currentColor"/><circle cx="15" cy="12" r="1.5" fill="currentColor"/><circle cx="9" cy="18" r="1.5" fill="currentColor"/><circle cx="15" cy="18" r="1.5" fill="currentColor"/></svg>
                        </div>
                        <div style="width:32px;height:32px;border-radius:8px;background:${sec.color}18;border:1px solid ${sec.color}30;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                            <svg viewBox="0 0 24 24" width="16" height="16" style="color:${sec.color};">${iconSvg}</svg>
                        </div>
                        <span style="flex:1;font-size:13px;font-weight:500;color:${t.text};">${sec.name}</span>
                        <button class="ms-edit" data-id="${sec.id}" style="background:${t.hover};border:1px solid ${t.cardBorder};border-radius:6px;color:${t.muted};cursor:pointer;font-size:11px;padding:4px 8px;transition:all 0.15s;" title="Edit">Edit</button>
                        <button class="ms-del" data-id="${sec.id}" style="background:none;border:none;color:${t.muted};cursor:pointer;font-size:14px;padding:4px 6px;border-radius:6px;transition:background 0.15s;"
                            onmouseenter="this.style.background='rgba(239,68,68,0.15)';this.style.color='#ef4444'" onmouseleave="this.style.background='none';this.style.color='${t.muted}'" title="Delete">✕</button>
                    </div>
                    <div class="ms-edit-form" data-id="${sec.id}" style="display:none;padding:8px 12px 12px;border-top:1px solid ${t.cardBorder};"></div>
                </div>`;
            });
            
            html += `<div style="margin-top:14px;padding-top:14px;border-top:1px solid ${t.border};">
                <div style="font-size:10px;font-weight:600;color:${t.muted};margin-bottom:8px;text-transform:uppercase;letter-spacing:0.5px;">Add New Domain</div>
                <input id="ms-name" placeholder="Domain name" style="width:100%;padding:9px 12px;background:${t.input};border:1px solid ${t.inputBorder};border-radius:8px;color:${t.text};font-size:12px;font-family:inherit;box-sizing:border-box;margin-bottom:10px;outline:none;transition:border-color 0.2s;"
                    onfocus="this.style.borderColor='#3b82f6'" onblur="this.style.borderColor='${t.inputBorder}'">
                <div style="font-size:10px;color:${t.muted};margin-bottom:5px;">Icon</div>
                <div id="ms-icons" style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px;">
                    ${icons.map(ic => `<button class="ms-icon-btn" data-icon="${ic.id}" style="width:30px;height:30px;padding:0;background:${t.input};border:1px solid ${t.inputBorder};border-radius:8px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.15s;"><svg viewBox="0 0 24 24" width="14" height="14" style="stroke:${t.iconStroke};color:${t.iconStroke};">${ic.svg}</svg></button>`).join('')}
                </div>
                <div style="font-size:10px;color:${t.muted};margin-bottom:5px;">Color</div>
                <div id="ms-colors" style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:12px;">
                    ${colors.map(c => `<button class="ms-color-btn" data-color="${c}" style="width:22px;height:22px;background:${c};border:2px solid transparent;border-radius:50%;cursor:pointer;transition:all 0.15s;box-shadow:0 2px 6px ${c}40;"></button>`).join('')}
                </div>
                <button id="ms-add" style="width:100%;padding:9px;background:linear-gradient(135deg,rgba(59,130,246,0.8),rgba(37,99,235,0.8));border:1px solid rgba(59,130,246,0.3);border-radius:8px;color:#fff;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;backdrop-filter:blur(8px);transition:all 0.2s;"
                    onmouseenter="this.style.background='linear-gradient(135deg,rgba(59,130,246,1),rgba(37,99,235,1))'" onmouseleave="this.style.background='linear-gradient(135deg,rgba(59,130,246,0.8),rgba(37,99,235,0.8))'">Add Domain</button>
            </div>`;
            
            panel.innerHTML = html;
            panel.querySelector('#ms-close').onclick = () => { panel.remove(); cleanup(); };
            panel.querySelector('#ms-back').onclick = () => {
                panel.remove(); cleanup();
                FileOps._renderCustomSectionsInDropdown(editor);
                const dd = document.getElementById('topologies-dropdown-menu');
                const btn = document.getElementById('btn-topologies');
                if (dd && btn) {
                    dd.style.display = 'block';
                    const r = btn.getBoundingClientRect();
                    dd.style.position = 'fixed';
                    dd.style.left = r.left + 'px';
                    dd.style.top = (r.bottom + 4) + 'px';
                    btn.classList.add('topologies-open');
                }
            };
            
            let selectedIcon = icons[0].id;
            let selectedColor = colors[0];
            
            panel.querySelectorAll('.ms-icon-btn').forEach(btn => {
                if (btn.dataset.icon === selectedIcon) btn.style.borderColor = selectedColor;
                btn.onclick = () => {
                    panel.querySelectorAll('.ms-icon-btn').forEach(b => b.style.borderColor = t.inputBorder);
                    btn.style.borderColor = selectedColor;
                    selectedIcon = btn.dataset.icon;
                };
            });
            
            panel.querySelectorAll('.ms-color-btn').forEach(btn => {
                if (btn.dataset.color === selectedColor) btn.style.borderColor = dk ? '#fff' : '#333';
                btn.onclick = () => {
                    panel.querySelectorAll('.ms-color-btn').forEach(b => b.style.borderColor = 'transparent');
                    btn.style.borderColor = dk ? '#fff' : '#333';
                    selectedColor = btn.dataset.color;
                    panel.querySelectorAll('.ms-icon-btn').forEach(b => b.style.borderColor = t.inputBorder);
                    const activeIcon = panel.querySelector(`.ms-icon-btn[data-icon="${selectedIcon}"]`);
                    if (activeIcon) activeIcon.style.borderColor = selectedColor;
                };
            });
            
            panel.querySelector('#ms-add').onclick = async () => {
                const name = panel.querySelector('#ms-name').value.trim();
                if (!name) { editor.showToast('Enter a domain name', 'warning'); return; }
                try {
                    const resp = await fetch('/api/sections', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, icon: selectedIcon, color: selectedColor }) });
                    const result = await resp.json();
                    if (result.ok) { await FileOps.loadCustomSections(editor); render(); editor.showToast(`Domain "${name}" created`, 'success'); }
                } catch (e) { editor.showToast(e.message, 'error'); }
            };
            
            panel.querySelectorAll('.ms-edit').forEach(btn => {
                btn.onclick = () => {
                    const id = btn.dataset.id;
                    const sec = (editor._customSections || []).find(s => s.id === id);
                    if (!sec) return;
                    const form = panel.querySelector(`.ms-edit-form[data-id="${id}"]`);
                    if (!form) return;
                    const isOpen = form.style.display !== 'none';
                    panel.querySelectorAll('.ms-edit-form').forEach(f => f.style.display = 'none');
                    if (isOpen) return;
                    form.style.display = 'block';
                    let editIcon = sec.icon || icons[0].id;
                    let editColor = sec.color || colors[0];
                    const origName = sec.name, origIcon = editIcon, origColor = editColor;

                    const row = btn.closest('.ms-domain-row');
                    const rowIconBox = row ? row.querySelector('div > div:nth-child(2)') : null;
                    const rowIconSvg = rowIconBox ? rowIconBox.querySelector('svg') : null;
                    const rowName = row ? row.querySelector('span') : null;

                    const livePreview = () => {
                        if (row) row.style.borderLeftColor = editColor;
                        if (rowIconBox) { rowIconBox.style.background = editColor + '18'; rowIconBox.style.borderColor = editColor + '30'; }
                        if (rowIconSvg) {
                            const ic = icons.find(i => i.id === editIcon) || icons[0];
                            rowIconSvg.innerHTML = ic.svg;
                            rowIconSvg.style.color = editColor;
                        }
                        const nameInput = form.querySelector('.edit-name');
                        if (rowName && nameInput) rowName.textContent = nameInput.value || origName;
                    };

                    form.innerHTML = `
                        <input class="edit-name" type="text" value="${sec.name}" style="width:100%;padding:7px 10px;background:${t.input};border:1px solid ${t.inputBorder};border-radius:6px;color:${t.text};font-size:11px;font-family:inherit;box-sizing:border-box;margin-bottom:8px;outline:none;transition:border-color 0.15s;"
                            onfocus="this.style.borderColor='${editColor}'" onblur="this.style.borderColor='${t.inputBorder}'">
                        <div style="font-size:9px;color:${t.muted};margin-bottom:3px;">Icon</div>
                        <div class="edit-icons" style="display:flex;flex-wrap:wrap;gap:3px;margin-bottom:8px;">
                            ${icons.map(ic => `<button class="ei-btn" data-icon="${ic.id}" style="width:26px;height:26px;padding:0;background:${ic.id === editIcon ? editColor + '20' : t.input};border:1.5px solid ${ic.id === editIcon ? editColor : t.inputBorder};border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.12s;"><svg viewBox="0 0 24 24" width="12" height="12" style="stroke:${ic.id === editIcon ? editColor : t.iconStroke};color:${ic.id === editIcon ? editColor : t.iconStroke};transition:color 0.12s;">${ic.svg}</svg></button>`).join('')}
                        </div>
                        <div style="font-size:9px;color:${t.muted};margin-bottom:3px;">Color</div>
                        <div class="edit-colors" style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px;">
                            ${colors.map(c => `<button class="ec-btn" data-color="${c}" style="width:20px;height:20px;background:${c};border:2.5px solid ${c === editColor ? (dk?'#fff':'#333') : 'transparent'};border-radius:50%;cursor:pointer;transition:all 0.12s;box-shadow:${c === editColor ? '0 0 8px '+c+'60' : 'none'};transform:${c === editColor ? 'scale(1.15)' : 'scale(1)'};"></button>`).join('')}
                        </div>
                        <div style="display:flex;gap:6px;">
                            <button class="edit-save" style="flex:1;padding:7px;background:linear-gradient(135deg,rgba(59,130,246,0.8),rgba(37,99,235,0.8));border:none;border-radius:6px;color:#fff;font-size:11px;font-weight:600;cursor:pointer;font-family:inherit;transition:all 0.15s;">Save</button>
                            <button class="edit-cancel" style="padding:7px 14px;background:${t.hover};border:1px solid ${t.cardBorder};border-radius:6px;color:${t.muted};font-size:11px;cursor:pointer;font-family:inherit;transition:all 0.15s;">Cancel</button>
                        </div>
                    `;
                    form.querySelector('.edit-name').addEventListener('input', () => livePreview());
                    const refreshIconBtns = () => {
                        form.querySelectorAll('.ei-btn').forEach(b => {
                            const isActive = b.dataset.icon === editIcon;
                            b.style.borderColor = isActive ? editColor : t.inputBorder;
                            b.style.background = isActive ? editColor + '20' : t.input;
                            const svg = b.querySelector('svg');
                            if (svg) { svg.style.color = isActive ? editColor : t.iconStroke; svg.style.stroke = isActive ? editColor : t.iconStroke; }
                        });
                    };
                    const refreshColorBtns = () => {
                        form.querySelectorAll('.ec-btn').forEach(b => {
                            const isActive = b.dataset.color === editColor;
                            b.style.borderColor = isActive ? (dk?'#fff':'#333') : 'transparent';
                            b.style.boxShadow = isActive ? '0 0 8px '+editColor+'60' : 'none';
                            b.style.transform = isActive ? 'scale(1.15)' : 'scale(1)';
                        });
                    };
                    form.querySelectorAll('.ei-btn').forEach(b => {
                        b.onclick = (ev) => { ev.stopPropagation(); editIcon = b.dataset.icon; refreshIconBtns(); livePreview(); };
                    });
                    form.querySelectorAll('.ec-btn').forEach(b => {
                        b.onclick = (ev) => { ev.stopPropagation(); editColor = b.dataset.color; refreshColorBtns(); refreshIconBtns(); livePreview(); };
                    });
                    form.querySelector('.edit-cancel').onclick = (ev) => {
                        ev.stopPropagation(); form.style.display = 'none';
                        editIcon = origIcon; editColor = origColor;
                        if (row) row.style.borderLeftColor = origColor;
                        if (rowIconBox) { rowIconBox.style.background = origColor + '18'; rowIconBox.style.borderColor = origColor + '30'; }
                        if (rowIconSvg) { const ic = icons.find(i => i.id === origIcon) || icons[0]; rowIconSvg.innerHTML = ic.svg; rowIconSvg.style.color = origColor; }
                        if (rowName) rowName.textContent = origName;
                    };
                    form.querySelector('.edit-save').onclick = async (ev) => {
                        ev.stopPropagation();
                        const newName = form.querySelector('.edit-name').value.trim();
                        if (!newName) { editor.showToast('Enter a name', 'warning'); return; }
                        try {
                            await fetch('/api/sections/update', {
                                method: 'POST', headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ id: sec.id, name: newName, icon: editIcon, color: editColor })
                            });
                            await FileOps.loadCustomSections(editor);
                            render();
                            editor.showToast(`Domain "${newName}" updated`, 'success');
                        } catch (e) { editor.showToast(e.message, 'error'); }
                    };
                };
            });
            
            panel.querySelectorAll('.ms-del').forEach(btn => {
                btn.onclick = () => {
                    const id = btn.dataset.id;
                    const sec = (editor._customSections || []).find(s => s.id === id);
                    const row = btn.closest('.ms-domain-row');
                    if (!row || !sec) return;
                    const existing = row.querySelector('.ms-confirm-bar');
                    if (existing) { existing.remove(); return; }
                    const bar = document.createElement('div');
                    bar.className = 'ms-confirm-bar';
                    bar.style.cssText = `display:flex;align-items:center;gap:8px;padding:8px 12px;border-top:1px solid rgba(239,68,68,0.2);background:rgba(239,68,68,0.06);`;
                    bar.innerHTML = `
                        <span style="flex:1;font-size:11px;color:#ef4444;">Delete "${sec.name}" and all its topologies?</span>
                        <button class="dc-yes" style="padding:4px 12px;background:#ef4444;border:none;border-radius:6px;color:#fff;font-size:11px;font-weight:600;cursor:pointer;">Delete</button>
                        <button class="dc-no" style="padding:4px 10px;background:${t.hover};border:1px solid ${t.cardBorder};border-radius:6px;color:${t.muted};font-size:11px;cursor:pointer;">Cancel</button>
                    `;
                    row.appendChild(bar);
                    bar.querySelector('.dc-no').onclick = (ev) => { ev.stopPropagation(); bar.remove(); };
                    bar.querySelector('.dc-yes').onclick = async (ev) => {
                        ev.stopPropagation();
                        try {
                            await fetch(`/api/sections/${id}/delete`, { method: 'POST' });
                            await FileOps.loadCustomSections(editor);
                            render();
                            editor.showToast('Domain deleted', 'success');
                        } catch (e) { editor.showToast(e.message, 'error'); }
                    };
                };
            });

            panel.querySelectorAll('.ms-drag-handle').forEach(handle => {
                handle.addEventListener('mousedown', (e) => {
                    if (e.button !== 0) return;
                    e.preventDefault();
                    const row = handle.closest('.ms-domain-row');
                    const allRows = [...panel.querySelectorAll('.ms-domain-row')];
                    if (allRows.length < 2) return;
                    const srcIdx = allRows.indexOf(row);
                    if (srcIdx < 0) return;

                    const startY = e.clientY;
                    const startRect = row.getBoundingClientRect();
                    const domainColor = row.style.borderLeftColor || '#3b82f6';

                    const ghost = row.cloneNode(true);
                    ghost.style.cssText += `;position:fixed;left:${startRect.left}px;top:${startRect.top}px;width:${startRect.width}px;z-index:999999;opacity:0.92;pointer-events:none;box-shadow:0 8px 24px rgba(0,0,0,0.35);transition:none;`;
                    document.body.appendChild(ghost);
                    document.body.style.cursor = 'grabbing';
                    handle.style.cursor = 'grabbing';

                    row.style.opacity = '0.15';
                    row.style.transition = 'opacity 0.15s';
                    const placeholder = document.createElement('div');
                    placeholder.style.cssText = `height:${startRect.height}px;background:rgba(59,130,246,0.06);border:2px dashed rgba(59,130,246,0.35);border-radius:10px;margin-bottom:6px;transition:all 0.2s ease;`;
                    row.parentNode.insertBefore(placeholder, row);
                    row.style.display = 'none';

                    // Snapshot positions of visible rows (excluding the dragged row)
                    const visibleRows = [...panel.querySelectorAll('.ms-domain-row')].filter(r => r !== row);
                    let currentIdx = srcIdx;

                    const onMove = (ev) => {
                        const dy = ev.clientY - startY;
                        ghost.style.top = (startRect.top + dy) + 'px';

                        const ghostMid = startRect.top + dy + startRect.height / 2;

                        // Find target position among visible rows
                        let newIdx = visibleRows.length;
                        for (let i = 0; i < visibleRows.length; i++) {
                            const r = visibleRows[i].getBoundingClientRect();
                            const mid = r.top + r.height / 2;
                            if (ghostMid < mid) {
                                newIdx = i;
                                break;
                            }
                        }

                        // Convert visible-row index to real section index
                        let realIdx = newIdx;
                        if (newIdx >= srcIdx) realIdx = newIdx + 1;
                        if (realIdx > allRows.length) realIdx = allRows.length;
                        if (realIdx < 0) realIdx = 0;
                        // Normalize: final position after removal
                        const finalIdx = realIdx > srcIdx ? realIdx - 1 : realIdx;

                        if (finalIdx !== currentIdx) {
                            placeholder.remove();
                            if (newIdx >= visibleRows.length) {
                                visibleRows[visibleRows.length - 1].parentNode.insertBefore(placeholder, visibleRows[visibleRows.length - 1].nextSibling);
                            } else {
                                visibleRows[newIdx].parentNode.insertBefore(placeholder, visibleRows[newIdx]);
                            }
                            currentIdx = finalIdx;
                        }
                    };

                    const onUp = async () => {
                        document.removeEventListener('mousemove', onMove);
                        document.removeEventListener('mouseup', onUp);
                        document.body.style.cursor = '';
                        handle.style.cursor = 'grab';
                        ghost.remove();
                        placeholder.remove();
                        row.style.display = '';
                        row.style.opacity = '1';
                        row.style.transition = '';
                        if (currentIdx !== srcIdx) {
                            const sections = [...(editor._customSections || [])];
                            const [moved] = sections.splice(srcIdx, 1);
                            sections.splice(currentIdx, 0, moved);
                            editor._customSections = sections;
                            try {
                                await fetch('/api/sections/reorder', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sections }) });
                                FileOps._renderCustomSectionsInDropdown(editor);
                                FileOps._updateTopoBtnIcon(editor);
                            } catch (_) {}
                            render();
                        }
                    };
                    document.addEventListener('mousemove', onMove);
                    document.addEventListener('mouseup', onUp);
                });
            });
        };
        
        render();
        document.body.appendChild(panel);
        
        const clickOutside = (e) => { if (!panel.contains(e.target) && e.target.id !== 'btn-topologies') { panel.remove(); cleanup(); } };
        const escHandler = (e) => { if (e.key === 'Escape') { panel.remove(); cleanup(); } };
        const cleanup = () => { document.removeEventListener('click', clickOutside); document.removeEventListener('keydown', escHandler); };
        setTimeout(() => { document.addEventListener('click', clickOutside); document.addEventListener('keydown', escHandler); }, 0);
    },

    // ========================================================================
    // SEAMLESS THEME TRANSITION FOR OPEN DROPDOWN
    // ========================================================================

    _updateDropdownTheme(editor) {
        const dropdown = document.getElementById('topologies-dropdown-menu');
        if (!dropdown || dropdown.style.display === 'none') return;
        const dk = document.body.classList.contains('dark-mode');
        const txtColor = dk ? '#e2e8f0' : '#1e1e32';
        const iconOpColor = dk ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.5)';
        const dur = '0.4s';
        const transAll = `background ${dur}, color ${dur}, border-color ${dur}, box-shadow ${dur}`;

        dropdown.querySelectorAll('.custom-section-category').forEach(sec => {
            const sid = sec.dataset.sectionId;
            const secObj = (editor._customSections || []).find(s => s.id === sid);
            const c = secObj?.color || '#3b82f6';
            sec.style.transition = transAll;
            sec.style.background = `${c}${dk ? '22' : '28'}`;

            // Save / Load button text + background
            sec.querySelectorAll('[data-action="save"],[data-action="load-file"]').forEach(btn => {
                btn.style.transition = transAll;
                btn.style.color = txtColor;
                if (!btn.dataset.pressed) {
                    btn.style.background = `${c}18`;
                    btn.style.borderColor = `${c}30`;
                }
            });

            // Topology file rows
            sec.querySelectorAll('.domain-topo-row').forEach(row => {
                row.style.transition = transAll;
                const nameEl = row.querySelector('.topo-entry-name');
                if (nameEl) { nameEl.style.transition = `color ${dur}`; nameEl.style.color = txtColor; }
                row.querySelectorAll('svg').forEach(svg => {
                    svg.style.transition = `color ${dur}`;
                    svg.style.color = iconOpColor;
                });
                row.querySelectorAll('.ta-btn').forEach(btn => {
                    btn.style.transition = `color ${dur}`;
                    btn.style.color = iconOpColor;
                });
            });

            // Save form inputs if open
            sec.querySelectorAll('.domain-save-form input').forEach(inp => {
                inp.style.transition = transAll;
                inp.style.background = dk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.04)';
                inp.style.color = txtColor;
            });
            sec.querySelectorAll('.domain-save-form button').forEach(btn => {
                btn.style.transition = transAll;
            });

            // "No topologies yet" text
            sec.querySelectorAll('.domain-topos-list > div[style*="font-style"]').forEach(el => {
                el.style.transition = `color ${dur}`;
            });
        });

        // Delete confirm bars
        dropdown.querySelectorAll('.delete-confirm-bar').forEach(bar => {
            bar.style.transition = transAll;
            bar.style.background = dk ? 'rgba(239,68,68,0.1)' : 'rgba(239,68,68,0.08)';
            bar.querySelectorAll('.dc-no').forEach(btn => {
                btn.style.transition = transAll;
                btn.style.background = dk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)';
                btn.style.borderColor = dk ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.12)';
                btn.style.color = dk ? '#94a3b8' : '#475569';
            });
        });

        // Rename forms
        dropdown.querySelectorAll('.rename-inline-form input').forEach(inp => {
            inp.style.transition = transAll;
            inp.style.background = dk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.04)';
            inp.style.color = txtColor;
        });
        dropdown.querySelectorAll('.rename-inline-form button:last-child').forEach(btn => {
            btn.style.transition = transAll;
            btn.style.background = dk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)';
            btn.style.borderColor = dk ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.12)';
            btn.style.color = dk ? '#94a3b8' : '#475569';
        });
    },

    // ========================================================================
    // INJECT METHODS ONTO EDITOR
    // ========================================================================

    inject(editor) {
        const methods = [
            'confirmNewTopology', 'clearCanvas', 'showClearConfirmation', 'performClearCanvas',
            'generateTopologyData', 'quickSaveTopology', 'quickSaveToDomain', 'saveTopology', 'saveTopologyAs', 'exportTopologyJSON',
            'exportTopologyAsPNG', 'loadTopology',
            'saveAsDnaasTopology', 'loadDnaasTopology',
            'saveBugTopology', 'showDebugDnosTopologySelector', 'loadDebugDnosTopology', '_ensureBugsSection',
            'loadCustomSections', '_renderCustomSectionsInDropdown', '_updateDropdownTheme',
            'saveToSection', 'loadFromSection', '_showSectionTopologyPicker', 'showManageSections',
            '_sectionIcons', '_sectionColors', '_updateTopoBtnIcon'
        ];
        for (const name of methods) {
            if (FileOps[name]) {
                if (name === '_sectionIcons' || name === '_sectionColors') {
                    editor[name] = () => FileOps[name]();
                } else {
                    editor[name] = (...args) => FileOps[name](editor, ...args);
                }
            }
        }
    }
};

console.log('[topology-file-ops.js] FileOps loaded');
