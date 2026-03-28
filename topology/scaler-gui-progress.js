/**
 * ScalerGUI: showProgress (WebSocket) + _analyzeCommitError
 * Source: split from scaler-gui.js.bak
 * @requires scaler-api.js
 * @requires scaler-gui.js (core)
 */
(function (G) {
    'use strict';
    if (!G) {
        console.error('[scaler-gui-progress.js] ScalerGUI core not loaded');
        return;
    }
    Object.assign(G, {
        showProgress(jobId, title, options = {}) {
            const existingPanel = this.state.activePanels[`progress-${jobId}`];
            if (existingPanel) {
                existingPanel.scrollIntoView({ behavior: 'smooth' });
                return;
            }
            const self = this;
            const tl = (title || '').toLowerCase();
            const isUpgrade = !!(options.upgradeDevices && options.upgradeDevices.length > 0)
                || tl.includes('upgrade') || tl.includes('upgrading');
            const content = document.createElement('div');
            content.className = 'scaler-progress-panel';
            if (isUpgrade) {
                content.innerHTML = `
                    <div class="scaler-progress-bar-container">
                        <div class="scaler-progress-bar progress-indeterminate" id="progress-bar-${jobId}">
                            <div class="scaler-progress-fill" id="progress-fill-${jobId}" style="width: 0%"></div>
                        </div>
                        <span class="scaler-progress-text" id="progress-text-${jobId}">Upgrade queued...</span>
                    </div>
                    <div class="upgrade-devices-container" id="progress-devices-${jobId}"></div>
                    <div class="scaler-progress-steps" id="progress-steps-${jobId}" style="display:none"></div>
                    <div class="scaler-progress-actions">
                        <button class="scaler-btn scaler-btn-secondary" id="progress-copylog-${jobId}" title="Copy terminal output to clipboard">Copy Log</button>
                        <button class="scaler-btn scaler-btn-cancel-push" id="progress-cancel-${jobId}" title="Cancel upgrade">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                            Cancel
                        </button>
                    </div>
                `;
            } else {
                content.innerHTML = `
                    <div class="scaler-progress-bar-container">
                        <div class="scaler-progress-bar">
                            <div class="scaler-progress-fill" id="progress-fill-${jobId}" style="width: 0%"></div>
                        </div>
                        <span class="scaler-progress-text" id="progress-text-${jobId}">Connecting...</span>
                    </div>
                    <div class="scaler-progress-steps" id="progress-steps-${jobId}">
                        <div class="scaler-step-info" style="color:var(--dn-orange,#e67e22)">Establishing SSH connection...</div>
                    </div>
                    <div class="scaler-terminal scaler-terminal-live" id="progress-terminal-${jobId}">
                        <div class="scaler-terminal-header">
                            <span class="scaler-terminal-dot"></span> Device Terminal
                        </div>
                        <div class="scaler-terminal-content"></div>
                    </div>
                    <div class="scaler-progress-actions">
                        <button class="scaler-btn scaler-btn-secondary" id="progress-copylog-${jobId}" title="Copy terminal output to clipboard">Copy Log</button>
                        <button class="scaler-btn scaler-btn-cancel-push" id="progress-cancel-${jobId}" title="Abort paste and discard candidate config on device">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                            Cancel (abort + clean device)
                        </button>
                    </div>
                `;
            }
        
            const panel = this.openPanel(`progress-${jobId}`, title, content, {minimizable: true, width: '560px'});
        
            if (panel) {
                const miniBar = document.createElement('div');
                miniBar.className = 'upgrade-minimized-bar';
                miniBar.id = `upgrade-mini-bar-${jobId}`;
                miniBar.innerHTML = `
                    <div class="upgrade-mini-progress"><div class="upgrade-mini-fill" id="upgrade-mini-fill-${jobId}" style="width:0%"></div></div>
                    <span class="upgrade-mini-text" id="upgrade-mini-text-${jobId}">0%</span>`;
                const header = panel.querySelector('.scaler-panel-header');
                if (header) header.after(miniBar);
            }
        
            const actionsEl = document.querySelector(`#progress-cancel-${jobId}`)?.parentElement;
        
            const showAwaitingButtons = () => {
                if (!actionsEl) return;
                actionsEl.innerHTML = `
                    <button class="scaler-btn scaler-btn-primary" id="progress-commit-${jobId}">Commit Now</button>
                    <button class="scaler-btn scaler-btn-cancel-push" id="progress-cancel-held-${jobId}" title="Discard candidate config and close SSH">Cancel (discard)</button>
                `;
                document.getElementById(`progress-commit-${jobId}`).onclick = async () => {
                    try {
                        await ScalerAPI.commitHeldJob(jobId);
                        document.getElementById(`progress-text-${jobId}`).textContent = '100% - Committing...';
                    } catch (e) {
                        this.showNotification(e.message, 'error');
                    }
                };
                document.getElementById(`progress-cancel-held-${jobId}`).onclick = async () => {
                    const btn = document.getElementById(`progress-cancel-held-${jobId}`);
                    if (btn?.disabled) return;
                    try {
                        btn.disabled = true;
                        btn.textContent = 'Cancelling...';
                        await ScalerAPI.cancelHeldJob(jobId);
                        document.getElementById(`progress-text-${jobId}`).textContent = 'Cancelled -- candidate config discarded on device';
                    } catch (e) {
                        this.showNotification(e.message, 'error');
                        if (btn) { btn.disabled = false; btn.textContent = 'Cancel (discard)'; }
                    }
                };
            };
        
            document.getElementById(`progress-cancel-${jobId}`).onclick = async () => {
                const btn = document.getElementById(`progress-cancel-${jobId}`);
                if (btn?.disabled) return;
                try {
                    btn.disabled = true;
                    btn.innerHTML = '<span class="scaler-progress-cancel-spinner"></span> Cancelling...';
                    await ScalerAPI.cancelOperation(jobId);
                    this.showNotification('Operation cancelled', 'warning');
                } catch (e) {
                    const msg = (e.message || '').toLowerCase();
                    if (msg.includes('not found') || msg.includes('404')) {
                        this.showNotification('Job already finished or was cleaned up', 'warning');
                        this.closePanel(`progress-${jobId}`);
                    } else {
                        this.showNotification(e.message, 'error');
                        if (btn) { btn.disabled = false; btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg> Cancel (abort + clean device)'; }
                    }
                }
            };
        
            const _copyLogFromPanel = () => {
                const lines = [];
                const container = document.getElementById(`progress-devices-${jobId}`);
                if (container) {
                    container.querySelectorAll('.upgrade-device-terminal-content .scaler-terminal-line').forEach(el => {
                        lines.push(el.textContent);
                    });
                }
                const mainTerm = document.querySelector(`#progress-terminal-${jobId} .scaler-terminal-content`);
                if (mainTerm) {
                    mainTerm.querySelectorAll('.scaler-terminal-line').forEach(el => {
                        lines.push(el.textContent);
                    });
                }
                if (lines.length === 0) lines.push('(no terminal output yet)');
                const _text = lines.join('\n');
                const _done = () => {
                    const btn = document.getElementById(`progress-copylog-${jobId}`);
                    if (btn) { btn.textContent = 'Copied!'; setTimeout(() => { btn.textContent = 'Copy Log'; }, 2000); }
                };
                const _fb = () => {
                    const ta = document.createElement('textarea');
                    ta.value = _text;
                    ta.style.cssText = 'position:fixed;left:-9999px';
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand('copy');
                    document.body.removeChild(ta);
                    _done();
                };
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(_text).then(_done).catch(_fb);
                } else {
                    _fb();
                }
            };
            const _liveCopyBtn = document.getElementById(`progress-copylog-${jobId}`);
            if (_liveCopyBtn) _liveCopyBtn.onclick = _copyLogFromPanel;
        
            let terminalHasContent = false;
            const _upgradeDeviceSet = new Set(options.upgradeDevices || []);
            const _phaseLabels = {
                'connecting': 'Connecting...', 'snapshot': 'Backing up config...',
                'deleting': 'System delete...', 'waiting-for-gi': 'Waiting for GI mode...',
                'check-target-stack': 'Verifying target-stack...',
                'load': 'Loading images...', 'deploying': 'Deploying system...',
                'pre-check': 'Pre-check...', 'install': 'Installing...',
                'post-deploy-verify': 'Verifying deploy...',
                'installing': 'Installing packages...',
                'config-repair': 'Restoring configuration...',
                'gi-recovery': 'Recovering stuck gi-manager...',
                'gi-recovery-reload': 'Reloading images after recovery...',
                'done': 'Complete', 'error': 'Failed', 'queued': 'Queued',
            };
            const _statusSvg = {
                pending: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>',
                running: '<div class="upgrade-device-spinner"></div>',
                completed: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2ecc71" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="7 13 10 16 17 9"/></svg>',
                failed: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#e74c3c" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
                skipped: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="8" y1="12" x2="16" y2="12"/></svg>',
            };
            let _lastExpandedDevice = null;
        
            const renderDeviceState = (deviceState) => {
                const container = document.getElementById(`progress-devices-${jobId}`);
                if (!container || !deviceState || typeof deviceState !== 'object') return;
                for (const [did, s] of Object.entries(deviceState)) {
                    _upgradeDeviceSet.add(did);
                    const escapedDid = CSS.escape(did);
                    let card = container.querySelector(`.upgrade-device-card[data-device="${escapedDid}"]`);
                    const status = s.status || 'pending';
                    const rawPhase = s.phase || '';
                    const phaseText = s.message || _phaseLabels[rawPhase] || rawPhase || 'Waiting...';
                    const pct = s.percent ?? 0;
                    if (!card) {
                        card = document.createElement('div');
                        card.className = 'upgrade-device-card';
                        card.dataset.device = did;
                        card._currentStatus = null;
                        card._userExpanded = false;
                                    const typeTag = s.upgrade_type === 'delete_deploy'
                                            ? '<span class="upgrade-device-type-tag upgrade-device-type-tag--dd" title="Delete+Deploy: system delete, load images in GI, deploy. Config auto-restored after.">D+D</span>'
                                            : s.upgrade_type === 'gi_deploy'
                                                ? '<span class="upgrade-device-type-tag upgrade-device-type-tag--gi" title="GI Deploy: device already in GI. Load images, deploy. Config auto-restored after.">GI</span>'
                                                : s.upgrade_type === 'skip'
                                                    ? '<span class="upgrade-device-type-tag upgrade-device-type-tag--normal">At Target</span>'
                                                    : s.upgrade_type === 'normal'
                                                        ? '<span class="upgrade-device-type-tag upgrade-device-type-tag--normal" title="Normal: load images to target-stack, install.">Install</span>' : '';
                        card.innerHTML = `
                            <div class="upgrade-device-card-header">
                                <span class="upgrade-device-status-icon">${_statusSvg.pending}</span>
                                <span class="upgrade-device-name">${self.escapeHtml(did)}</span>
                                ${typeTag}
                                <span class="upgrade-device-config-restored upgrade-device-type-tag upgrade-device-type-tag--restored" title="Configuration restored after deploy" style="display:${s.config_restored ? '' : 'none'}">Config restored</span>
                                <span class="upgrade-device-phase">${self.escapeHtml(phaseText)}</span>
                                <svg class="upgrade-device-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
                            </div>
                            <div class="upgrade-device-card-bar"><div class="upgrade-device-card-fill"></div></div>
                            <div class="upgrade-device-card-body"><div class="upgrade-device-terminal-content"></div></div>
                        `;
                        card.querySelector('.upgrade-device-card-header').addEventListener('click', () => {
                            card._userExpanded = !card._userExpanded;
                            card.classList.toggle('expanded', card._userExpanded);
                        });
                        container.appendChild(card);
                    }
                    const wasExpanded = card.classList.contains('expanded');
                    card.className = 'upgrade-device-card ' + status;
                    if (wasExpanded || card._userExpanded) card.classList.add('expanded');
                    if (card._currentStatus !== status) {
                        card.querySelector('.upgrade-device-status-icon').innerHTML = _statusSvg[status] || _statusSvg.pending;
                        card._currentStatus = status;
                    }
                    card.querySelector('.upgrade-device-phase').textContent = phaseText;
                    card.querySelector('.upgrade-device-card-fill').style.width = `${pct}%`;
                    let restoredEl = card.querySelector('.upgrade-device-config-restored');
                    if (s.config_restored) {
                        if (!restoredEl) {
                            restoredEl = document.createElement('span');
                            restoredEl.className = 'upgrade-device-type-tag upgrade-device-type-tag--restored';
                            const phaseEl = card.querySelector('.upgrade-device-phase');
                            if (phaseEl && phaseEl.parentNode) phaseEl.parentNode.insertBefore(restoredEl, phaseEl);
                        }
                        if (s.config_repair_partial) {
                            restoredEl.textContent = 'Config partial';
                            restoredEl.title = 'Config partially restored -- some sections incompatible with this version';
                            restoredEl.className = 'upgrade-device-type-tag upgrade-device-type-tag--partial';
                        } else {
                            restoredEl.textContent = 'Config restored';
                            restoredEl.title = 'Configuration restored after deploy';
                            restoredEl.className = 'upgrade-device-type-tag upgrade-device-type-tag--restored';
                        }
                        restoredEl.style.display = '';
                    } else if (restoredEl) {
                        restoredEl.style.display = 'none';
                    }
        
                    const failures = s.config_repair_failures;
                    let failPanel = card.querySelector('.upgrade-config-failures');
                    if (failures && failures.length > 0) {
                        if (!failPanel) {
                            failPanel = document.createElement('div');
                            failPanel.className = 'upgrade-config-failures';
                            const body = card.querySelector('.upgrade-device-card-body');
                            if (body) body.appendChild(failPanel);
                        }
                        const failRows = failures.map(f => {
                            const cat = f.category || '';
                            const catTag = cat ? `<span class="upgrade-fail-category">${self.escapeHtml(cat)}</span>` : '';
                            return `<div class="upgrade-fail-row">
                                <span class="upgrade-fail-path">${self.escapeHtml(f.path || 'unknown')}</span>
                                <span class="upgrade-fail-reason">${self.escapeHtml(f.reason || '')}</span>
                                ${catTag}
                            </div>`;
                        }).join('');
                        failPanel.innerHTML = `
                            <div class="upgrade-fail-header">Incompatible config sections (${failures.length})</div>
                            ${failRows}
                            <div class="upgrade-fail-hint">These hierarchies need manual adjustment for this DNOS version. Check if syntax was renamed, moved, or removed.</div>
                        `;
                    } else if (failPanel) {
                        failPanel.remove();
                    }
                    if (status === 'running' && _lastExpandedDevice !== did) {
                        container.querySelectorAll('.upgrade-device-card').forEach(c => {
                            if (c.dataset.device !== did && !c._userExpanded) { c.classList.remove('expanded'); }
                        });
                        card.classList.add('expanded');
                        _lastExpandedDevice = did;
                    }
                }
            };
        
            // Pre-populate panel from existing job data (after refresh)
            const _initJob = options._initialJobData;
            if (_initJob && isUpgrade) {
                if (_initJob.device_state) renderDeviceState(_initJob.device_state);
                const pct = _initJob.percent ?? 0;
                const msg = _initJob.message || '';
                const fill0 = document.getElementById(`progress-fill-${jobId}`);
                const text0 = document.getElementById(`progress-text-${jobId}`);
                if (fill0) fill0.style.width = `${pct}%`;
                if (text0) text0.textContent = `${pct}% - ${msg}`;
                const miniFill0 = document.getElementById(`upgrade-mini-fill-${jobId}`);
                const miniText0 = document.getElementById(`upgrade-mini-text-${jobId}`);
                if (miniFill0) miniFill0.style.width = `${pct}%`;
                if (miniText0) miniText0.textContent = `${pct}%`;
                const lines = _initJob.terminal_lines || [];
                if (lines.length > 0) {
                    const container = document.getElementById(`progress-devices-${jobId}`);
                    if (container) {
                        lines.forEach(l => {
                            const sublines = (l || '').split('\n').filter(s => s.trim());
                            sublines.forEach(sl => {
                                const match = sl.match(/^\[(\w+)\]\s+(.+?):\s+(.+)$/);
                                if (!match) return;
                                const [, level, did, msg2] = match;
                                if (!_upgradeDeviceSet.has(did)) return;
                                const card = container.querySelector(`.upgrade-device-card[data-device="${CSS.escape(did)}"]`);
                                if (!card) return;
                                const term = card.querySelector('.upgrade-device-terminal-content');
                                if (!term) return;
                                const displayLine = `[${level}] ${msg2}`;
                                const div = document.createElement('div');
                                div.className = 'scaler-terminal-line';
                                const lt = displayLine.trim().toLowerCase();
                                if (lt.includes('[error]') || lt.startsWith('error:') || lt.includes('failed')) div.classList.add('t-error');
                                else if (lt.includes('[warn') || lt.includes('warning')) div.classList.add('t-warn');
                                else if (lt.includes('success') || lt.includes('[ok]') || lt.includes('complete')) div.classList.add('t-success');
                                else if (lt.includes('[info]')) div.classList.add('t-info');
                                div.textContent = displayLine;
                                term.appendChild(div);
                            });
                        });
                        container.querySelectorAll('.upgrade-device-terminal-content').forEach(t => { t.scrollTop = t.scrollHeight; });
                    }
                }
            }
            const _prePopLineCount = (_initJob && _initJob.terminal_lines) ? _initJob.terminal_lines.length : 0;
        
            const ws = ScalerAPI.connectProgress(jobId, {
                onProgress: (percent, message, timing) => {
                    const fill = document.getElementById(`progress-fill-${jobId}`);
                    const text = document.getElementById(`progress-text-${jobId}`);
                    if (fill) fill.style.width = `${percent}%`;
                    const bar = document.getElementById(`progress-bar-${jobId}`);
                    const isBuildPhase = percent < 50 && (message || '').toLowerCase().includes('build');
                    if (bar) bar.classList.toggle('progress-indeterminate', isBuildPhase);
                    const elapsed = timing?.elapsed_seconds;
                    const remaining = timing?.estimated_remaining_seconds;
                    const fmt = (s) => {
                        if (s == null || s < 0) return '';
                        if (s < 60) return `${Math.round(s)}s`;
                        const m = Math.floor(s / 60);
                        const sec = Math.round(s % 60);
                        return sec ? `${m}m ${sec}s` : `${m}m`;
                    };
                    const timeStr = isBuildPhase
                        ? (elapsed != null ? ` | Elapsed: ${fmt(elapsed)}` : '')
                        : (elapsed != null || remaining != null) ? ` | Elapsed: ${fmt(elapsed)} | Remaining: ~${fmt(remaining)}` : '';
                    if (text) text.textContent = `${percent}% - ${message || ''}${timeStr}`;
                    const stepsEl = document.getElementById(`progress-steps-${jobId}`);
                    if (stepsEl && message) {
                        stepsEl.innerHTML = `<div class="scaler-step-info">${this.escapeHtml(message)}</div>`;
                    }
                    const miniFill = document.getElementById(`upgrade-mini-fill-${jobId}`);
                    const miniText = document.getElementById(`upgrade-mini-text-${jobId}`);
                    if (miniFill) miniFill.style.width = `${percent}%`;
                    if (miniText) miniText.textContent = `${percent}%`;
                },
                onTerminal: (line) => {
                    if (isUpgrade) {
                        const container = document.getElementById(`progress-devices-${jobId}`);
                        if (!container) return;
                        const sublines = (line || '').split('\n').filter(l => l.trim());
                        sublines.forEach(l => {
                            const match = l.match(/^\[(\w+)\]\s+(.+?):\s+(.+)$/);
                            let targetCard = null;
                            let displayLine = l;
                            if (match) {
                                const [, level, did, msg] = match;
                                if (_upgradeDeviceSet.has(did)) {
                                    targetCard = container.querySelector(`.upgrade-device-card[data-device="${CSS.escape(did)}"]`);
                                    displayLine = `[${level}] ${msg}`;
                                }
                            }
                            if (!targetCard) return;
                            if (targetCard) {
                                const term = targetCard.querySelector('.upgrade-device-terminal-content');
                                if (term) {
                                    const div = document.createElement('div');
                                    div.className = 'scaler-terminal-line';
                                    const lt = displayLine.trim().toLowerCase();
                                    if (lt.includes('[error]') || lt.startsWith('error:') || lt.includes('failed')) div.classList.add('t-error');
                                    else if (lt.includes('[warn') || lt.includes('warning')) div.classList.add('t-warn');
                                    else if (lt.includes('success') || lt.includes('[ok]') || lt.includes('complete')) div.classList.add('t-success');
                                    else if (lt.includes('[info]')) div.classList.add('t-info');
                                    div.textContent = displayLine;
                                    term.appendChild(div);
                                    term.scrollTop = term.scrollHeight;
                                }
                            }
                        });
                        return;
                    }
                    const terminal = document.querySelector(`#progress-terminal-${jobId} .scaler-terminal-content`);
                    if (!terminal) return;
                    if (!terminalHasContent) {
                        terminalHasContent = true;
                        const dot = document.querySelector(`#progress-terminal-${jobId} .scaler-terminal-dot`);
                        if (dot) dot.classList.add('active');
                    }
                    const lines = (line || '').split('\n');
                    lines.forEach(l => {
                        if (!l.trim()) return;
                        const div = document.createElement('div');
                        div.className = 'scaler-terminal-line';
                        const lt = l.trim().toLowerCase();
                        if (lt.includes('[error]') || lt.startsWith('error:') || lt.includes('commit check has failed') || lt.includes('commit check failed')) {
                            div.classList.add('t-error');
                        } else if (lt.includes('[warn') || lt.includes('warning')) {
                            div.classList.add('t-warn');
                        } else if (lt.includes('commit succeeded') || lt.includes('[ok]') || lt.includes('success')) {
                            div.classList.add('t-success');
                        } else if (lt.startsWith('#') || lt.includes('config-start') || lt.includes('config-end') || l.match(/^\s*!/)) {
                            div.classList.add('t-comment');
                        } else if (l.match(/^\s*(interfaces|protocols|network-services|routing-policy|system)/)) {
                            div.classList.add('t-keyword');
                        }
                        div.textContent = l;
                        terminal.appendChild(div);
                    });
                    terminal.scrollTop = terminal.scrollHeight;
                },
                onStep: (current, total, name) => {
                    const stepsEl = document.getElementById(`progress-steps-${jobId}`);
                    if (stepsEl) {
                        stepsEl.innerHTML = `<div class="scaler-step-info">Step ${current}/${total}: ${name}</div>`;
                    }
                },
                onError: (msg) => {
                    const text = document.getElementById(`progress-text-${jobId}`);
                    if (text) text.textContent = msg || 'Connection lost';
                    const fill = document.getElementById(`progress-fill-${jobId}`);
                    if (fill) fill.classList.add('scaler-progress-error');
                    const stepsEl = document.getElementById(`progress-steps-${jobId}`);
                    if (stepsEl) stepsEl.innerHTML = '<div class="scaler-step-info" style="color:var(--dn-orange,#e67e22)">Backend connection lost. The operation may still be running. Refresh the page to check status.</div>';
                    const miniFill = document.getElementById(`upgrade-mini-fill-${jobId}`);
                    const miniText = document.getElementById(`upgrade-mini-text-${jobId}`);
                    if (miniFill) miniFill.classList.add('error');
                    if (miniText) miniText.textContent = 'Error';
                },
                onAwaitingDecision: () => {
                    showAwaitingButtons();
                },
                onDeviceState: isUpgrade ? renderDeviceState : undefined,
                onComplete: (success, result) => {
                    if (isUpgrade) {
                        if (result?.device_state) renderDeviceState(result.device_state);
                        try { localStorage.removeItem('scaler_active_upgrade'); } catch (_) {}
                        const container = document.getElementById(`progress-devices-${jobId}`);
                        if (container) {
                            const fullLines = result?.terminal_full || [];
                            if (fullLines.length > 0) {
                                fullLines.forEach(l => {
                                    const sublines = (l || '').split('\n').filter(s => s.trim());
                                    sublines.forEach(sl => {
                                        const match = sl.match(/^\[(\w+)\]\s+(.+?):\s+(.+)$/);
                                        if (!match) return;
                                        const [, level, did, msg] = match;
                                        if (!_upgradeDeviceSet.has(did)) return;
                                        const card = container.querySelector(`.upgrade-device-card[data-device="${CSS.escape(did)}"]`);
                                        if (!card) return;
                                        const term = card.querySelector('.upgrade-device-terminal-content');
                                        if (!term) return;
                                        const displayLine = `[${level}] ${msg}`;
                                        const div = document.createElement('div');
                                        div.className = 'scaler-terminal-line';
                                        const lt = displayLine.trim().toLowerCase();
                                        if (lt.includes('[error]') || lt.startsWith('error:') || lt.includes('failed')) div.classList.add('t-error');
                                        else if (lt.includes('[warn') || lt.includes('warning')) div.classList.add('t-warn');
                                        else if (lt.includes('success') || lt.includes('[ok]') || lt.includes('complete')) div.classList.add('t-success');
                                        else if (lt.includes('[info]')) div.classList.add('t-info');
                                        div.textContent = displayLine;
                                        term.appendChild(div);
                                    });
                                });
                            }
                            container.querySelectorAll('.upgrade-device-card').forEach(c => {
                                c.classList.add('expanded');
                                c._userExpanded = true;
                            });
                        }
                        const ds = result?.device_state || {};
                        const failedIds = Object.entries(ds)
                            .filter(([, s]) => s.status === 'failed')
                            .map(([id]) => id);
                        if (failedIds.length > 0 && actionsEl) {
                            const retryBtn = document.createElement('button');
                            retryBtn.className = 'scaler-btn scaler-btn-primary';
                            retryBtn.textContent = `Retry ${failedIds.length} Failed Device${failedIds.length > 1 ? 's' : ''}`;
                            retryBtn.onclick = async () => {
                                retryBtn.disabled = true;
                                retryBtn.textContent = 'Re-planning...';
                                try {
                                    const sshHosts = options.upgradeSshHosts || {};
                                    const statusResult = await ScalerAPI.getUpgradeDeviceStatus(failedIds, sshHosts);
                                    const newStatus = statusResult.devices || {};
                                    for (const [did, st] of Object.entries(newStatus)) {
                                        if (self.WizardController?.data?.deviceStatus) {
                                            self.WizardController.data.deviceStatus[did] = st;
                                        }
                                    }
                                    self.showNotification(`Re-planned ${failedIds.length} device(s). Open the upgrade wizard Execute step to proceed.`, 'success');
                                    panel?.close?.();
                                } catch (e) {
                                    self.showNotification(`Retry failed: ${e.message}`, 'error');
                                    retryBtn.disabled = false;
                                    retryBtn.textContent = `Retry ${failedIds.length} Failed`;
                                }
                            };
                            actionsEl.innerHTML = '';
                            actionsEl.appendChild(retryBtn);
                        }
                    }
                    const fill = document.getElementById(`progress-fill-${jobId}`);
                    const text = document.getElementById(`progress-text-${jobId}`);
                    if (fill) {
                        fill.style.width = '100%';
                        fill.classList.add(success ? 'scaler-progress-success' : 'scaler-progress-error');
                    }
                    const miniFill = document.getElementById(`upgrade-mini-fill-${jobId}`);
                    const miniText = document.getElementById(`upgrade-mini-text-${jobId}`);
                    if (miniFill) { miniFill.style.width = '100%'; miniFill.classList.add(success ? 'done' : 'error'); }
                    if (miniText) miniText.textContent = success ? 'Done' : 'Failed';
                    let failLabel = 'Failed';
                    if (!success && !result?.cancelled && result?.message) {
                        if (isUpgrade) {
                            failLabel = `Failed -- ${result.message}`;
                        } else {
                            const quickTitle = this._analyzeCommitError(result.message).title;
                            failLabel = `Failed -- ${quickTitle}`;
                        }
                    }
                    if (text) text.textContent = success ? 'Complete!' : (result?.cancelled ? 'Cancelled -- candidate config discarded on device' : failLabel);
                    const dot = document.querySelector(`#progress-terminal-${jobId} .scaler-terminal-dot`);
                    if (dot) { dot.classList.remove('active'); dot.classList.add(success ? 'done' : 'error'); }
        
                    // Show clear error breakdown + smart fix suggestions on failure
                    if (!success && !result?.cancelled && result?.message && !isUpgrade) {
                        const stepsEl = document.getElementById(`progress-steps-${jobId}`);
                        if (stepsEl) {
                            const errMsg = result.message || '';
                            const analysis = this._analyzeCommitError(errMsg);
                            const iconSvgs = {
                                overlap: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#e74c3c" stroke-width="2"><circle cx="9" cy="12" r="5"/><circle cx="15" cy="12" r="5"/></svg>',
                                duplicate: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#e74c3c" stroke-width="2"><rect x="4" y="4" width="12" height="12" rx="2"/><rect x="8" y="8" width="12" height="12" rx="2"/></svg>',
                                limit: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#e74c3c" stroke-width="2"><path d="M12 2v20M2 12h20"/><circle cx="12" cy="12" r="10"/></svg>',
                                error: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#e74c3c" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
                            };
                            const icon = iconSvgs[analysis.icon] || iconSvgs.error;
                            stepsEl.innerHTML = `
                                <div class="scaler-commit-error-panel">
                                    <div class="scaler-commit-error-header">
                                        ${icon}
                                        <div class="scaler-commit-error-title">${this.escapeHtml(analysis.title)}</div>
                                    </div>
                                    <div class="scaler-commit-error-body">
                                        ${analysis.details.map(d => `<div class="scaler-commit-error-detail">${d}</div>`).join('')}
                                    </div>
                                    ${analysis.fixes.length ? `
                                    <div class="scaler-commit-fix-section">
                                        <div class="scaler-commit-fix-label">
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
                                            Suggestion
                                        </div>
                                        ${analysis.fixes.map(f => `<div class="scaler-commit-fix-item">${f}</div>`).join('')}
                                    </div>` : ''}
                                    ${analysis.actions.length ? `
                                    <div class="scaler-commit-actions">
                                        ${analysis.actions.map(a => `<button class="scaler-btn scaler-commit-action-btn scaler-commit-action-${a.style}" data-action-id="${a.id}" title="${this.escapeHtml(a.desc || '')}">${a.label}</button>`).join('')}
                                    </div>` : ''}
                                </div>`;
                            // Wire action buttons
                            stepsEl.querySelectorAll('.scaler-commit-action-btn').forEach(btn => {
                                btn.onclick = () => {
                                    const aid = btn.dataset.actionId;
                                    const deviceId = options.device_id || '';
                                    if (aid === 'reopen-fix-ip' || aid === 'reopen-edit' || aid === 'reopen-reduce' || aid === 'reopen-fix-mode') {
                                        this.closePanel(`progress-${jobId}`);
                                        if (options.onReopenWizard) options.onReopenWizard(analysis);
                                        else if (deviceId) this.showNotification('Re-open the wizard from the Scaler menu to adjust parameters', 'info');
                                    } else if (aid === 'delete-conflicting' || aid === 'delete-then-push') {
                                        const iface = analysis.conflictingIface || analysis.newIface || '';
                                        if (iface && deviceId) {
                                            btn.disabled = true;
                                            btn.textContent = 'Deleting...';
                                            ScalerAPI.deleteHierarchyOp(deviceId, 'interfaces', false, iface)
                                                .then(() => { this.showNotification(`Deleted ${iface}. Re-push your config.`, 'success'); btn.textContent = 'Deleted'; })
                                                .catch(e => { this.showNotification(`Delete failed: ${e.message}`, 'error'); btn.disabled = false; btn.textContent = btn.dataset.label || 'Retry'; });
                                        }
                                    }
                                };
                            });
                        }
                    }
        
                    // Hide the cancel button (job is done)
                    const cancelBtn = document.getElementById(`progress-cancel-${jobId}`);
                    if (cancelBtn) cancelBtn.style.display = 'none';
        
                    if (actionsEl) {
                        actionsEl.innerHTML = '';
        
                        // -- Row 1: primary actions (always visible) --
                        const closeBtn = document.createElement('button');
                        closeBtn.className = 'scaler-btn';
                        closeBtn.textContent = 'Close';
                        closeBtn.onclick = () => this.closePanel(`progress-${jobId}`);
                        actionsEl.appendChild(closeBtn);
        
                        const copyLogBtn = document.createElement('button');
                        copyLogBtn.className = 'scaler-btn scaler-btn-secondary';
                        copyLogBtn.textContent = 'Copy Log';
                        copyLogBtn.title = 'Copy full terminal output to clipboard';
                        copyLogBtn.onclick = () => {
                            const lines = [];
                            const container = document.getElementById(`progress-devices-${jobId}`);
                            if (container) {
                                container.querySelectorAll('.upgrade-device-terminal-content .scaler-terminal-line').forEach(el => {
                                    lines.push(el.textContent);
                                });
                            }
                            const mainTerm = document.querySelector(`#progress-terminal-${jobId} .scaler-terminal-content`);
                            if (mainTerm) {
                                mainTerm.querySelectorAll('.scaler-terminal-line').forEach(el => {
                                    lines.push(el.textContent);
                                });
                            }
                            if (lines.length === 0) lines.push('(no terminal output)');
                            const _text = lines.join('\n');
                            const _onCopied = () => {
                                copyLogBtn.textContent = 'Copied!';
                                setTimeout(() => { copyLogBtn.textContent = 'Copy Log'; }, 2000);
                            };
                            const _fallbackCopy = () => {
                                const ta = document.createElement('textarea');
                                ta.value = _text;
                                ta.style.cssText = 'position:fixed;left:-9999px';
                                document.body.appendChild(ta);
                                ta.select();
                                document.execCommand('copy');
                                document.body.removeChild(ta);
                                _onCopied();
                            };
                            if (navigator.clipboard && navigator.clipboard.writeText) {
                                navigator.clipboard.writeText(_text).then(_onCopied).catch(_fallbackCopy);
                            } else {
                                _fallbackCopy();
                            }
                        };
                        actionsEl.appendChild(copyLogBtn);
        
                        // -- Upgrade failure: dismiss + new upgrade (nothing else) --
                        if (isUpgrade && !success && !result?.cancelled && options.upgradeDevices?.length) {
                            const dismissAlBtn = document.createElement('button');
                            dismissAlBtn.className = 'scaler-btn scaler-btn-secondary';
                            dismissAlBtn.textContent = 'Dismiss alert';
                            dismissAlBtn.title = 'Clear red badge on canvas and hide failure banner';
                            dismissAlBtn.onclick = () => {
                                this.dismissUpgradeFailureAlert(jobId, options.upgradeDevices);
                                this.closePanel(`progress-${jobId}`);
                                this.showNotification('Failure alert dismissed', 'info');
                            };
                            actionsEl.appendChild(dismissAlBtn);
        
                            const newUpgBtn = document.createElement('button');
                            newUpgBtn.className = 'scaler-btn scaler-btn-primary';
                            newUpgBtn.textContent = 'New upgrade';
                            newUpgBtn.title = 'Open Image Upgrade Wizard for this device';
                            newUpgBtn.onclick = () => {
                                const devId = options.upgradeDevices[0];
                                this.dismissUpgradeFailureAlert(jobId, options.upgradeDevices);
                                this.closePanel(`progress-${jobId}`);
                                this.openUpgradeWizard({ deviceId: devId });
                            };
                            actionsEl.appendChild(newUpgBtn);
                        }
        
                        // -- Upgrade success: Undo, Verify Stacks, Restore Config --
                        if (isUpgrade && success) {
                            if (ScalerAPI.generateUndo) {
                                const undoBtn = document.createElement('button');
                                undoBtn.className = 'scaler-btn scaler-btn-secondary';
                                undoBtn.textContent = 'Undo Last Push';
                                undoBtn.title = 'Generate undo config and push to remove what was just committed';
                                undoBtn.onclick = async () => {
                                    try {
                                        undoBtn.disabled = true;
                                        undoBtn.textContent = 'Generating...';
                                        const r = await ScalerAPI.generateUndo({ job_id: jobId });
                                        const undoConfig = r?.config || '';
                                        if (!undoConfig.trim()) {
                                            this.showNotification('No undo commands generated', 'warning');
                                            undoBtn.disabled = false;
                                            undoBtn.textContent = 'Undo Last Push';
                                            return;
                                        }
                                        const job = await ScalerAPI.getJob(jobId).catch(() => ({}));
                                        const deviceId = job?.device_id || options.device_id || '';
                                        if (!deviceId) {
                                            this.showNotification('Device ID not found for undo', 'warning');
                                            undoBtn.disabled = false;
                                            undoBtn.textContent = 'Undo Last Push';
                                            return;
                                        }
                                        this.closePanel(`progress-${jobId}`);
                                        const ctx = await ScalerAPI.getDeviceContext(deviceId, false, job?.ssh_host || '').catch(() => ({}));
                                        const pushResult = await ScalerAPI.pushConfig({
                                            config: 'configure\n' + undoConfig + '\ncommit\nexit\n',
                                            device_id: deviceId,
                                            dry_run: false,
                                            push_method: 'terminal_paste',
                                            load_mode: 'merge',
                                            ssh_host: ctx?.mgmt_ip || ctx?.ip || '',
                                        });
                                        if (pushResult?.job_id) {
                                            this.showProgress(pushResult.job_id, `Undo: ${deviceId}`, { device_id: deviceId, onComplete: () => {} });
                                        } else {
                                            this.showNotification('Undo push started', 'success');
                                        }
                                    } catch (e) {
                                        this.showNotification(`Undo failed: ${e.message}`, 'error');
                                    } finally {
                                        undoBtn.disabled = false;
                                        undoBtn.textContent = 'Undo Last Push';
                                    }
                                };
                                actionsEl.appendChild(undoBtn);
                            }
                            if (options.upgradeDevices?.length && ScalerAPI.verifyUpgradeStacks) {
                                const verifyBtn = document.createElement('button');
                                verifyBtn.className = 'scaler-btn';
                                verifyBtn.textContent = 'Verify Stacks';
                                verifyBtn.onclick = async () => {
                                    try {
                                        verifyBtn.disabled = true;
                                        const r = await ScalerAPI.verifyUpgradeStacks(options.upgradeDevices, options.upgradeSshHosts || {});
                                        this.showNotification('Verify complete - check terminal', 'success');
                                        const terminal = document.querySelector(`#progress-terminal-${jobId} .scaler-terminal-content`);
                                        if (terminal && r?.result) {
                                            Object.entries(r.result || {}).forEach(([dev, data]) => {
                                                const div = document.createElement('div');
                                                div.className = 'scaler-terminal-line';
                                                div.textContent = `${dev}: ${data.error || (data.stack_output || '').slice(0, 200)}`;
                                                terminal.appendChild(div);
                                            });
                                            terminal.scrollTop = terminal.scrollHeight;
                                        }
                                    } catch (e) {
                                        this.showNotification(e.message, 'error');
                                    } finally {
                                        verifyBtn.disabled = false;
                                    }
                                };
                                actionsEl.appendChild(verifyBtn);
                            }
                            if (options.upgradeDevices?.length && ScalerAPI.restoreUpgradeConfig) {
                                const restoreBtn = document.createElement('button');
                                restoreBtn.className = 'scaler-btn';
                                restoreBtn.textContent = 'Restore Config';
                                restoreBtn.onclick = async () => {
                                    try {
                                        restoreBtn.disabled = true;
                                        await ScalerAPI.restoreUpgradeConfig(options.upgradeDevices, options.upgradeSshHosts || {});
                                        this.showNotification('Restore initiated', 'success');
                                    } catch (e) {
                                        this.showNotification(e.message, 'error');
                                    } finally {
                                        restoreBtn.disabled = false;
                                    }
                                };
                                actionsEl.appendChild(restoreBtn);
                            }
                        }
        
                        // -- Non-upgrade failure: cleanup --
                        if (!isUpgrade && !success && !result?.cancelled) {
                            const cleanupBtn = document.createElement('button');
                            cleanupBtn.className = 'scaler-btn scaler-btn-danger';
                            cleanupBtn.textContent = 'Cleanup';
                            cleanupBtn.onclick = async () => {
                                try {
                                    await ScalerAPI.cleanupHeldJob(jobId);
                                    this.showNotification('Cleanup complete', 'success');
                                    cleanupBtn.disabled = true;
                                    cleanupBtn.textContent = 'Cleaned';
                                } catch (e) {
                                    this.showNotification(e.message, 'error');
                                }
                            };
                            actionsEl.appendChild(cleanupBtn);
                        }
                    }
        
                    this.showNotification(
                        success ? 'Operation completed successfully' : (result?.cancelled ? 'Cancelled' : 'Operation failed'),
                        success ? 'success' : 'error'
                    );
        
                    if (isUpgrade) {
                        const ds = result?.device_state || {};
                        const completedDevices = Object.entries(ds)
                            .filter(([, s]) => s.status === 'completed')
                            .map(([id]) => id);
                        const failedDevices = Object.entries(ds)
                            .filter(([, s]) => s.status === 'failed')
                            .map(([id]) => id);
                        window.dispatchEvent(new CustomEvent('device:upgrade-complete', {
                            detail: {
                                jobId,
                                success,
                                completedDevices,
                                failedDevices,
                                allDevices: [..._upgradeDeviceSet],
                            }
                        }));
                    }
        
                    options.onComplete?.(success, { ...result, job_id: jobId });
                },
                onError: (message) => {
                    const dot = document.querySelector(`#progress-terminal-${jobId} .scaler-terminal-dot`);
                    if (dot) dot.classList.add('error');
                    this.showNotification(`Error: ${message}`, 'error');
                }
            }, { terminalOffset: _prePopLineCount });
        
            this.state.jobs[jobId] = { ws, panel };
            return panel;
        },
        _analyzeCommitError(msg) {
            const t = (msg || '').toLowerCase();
            const analysis = { title: 'Commit check failed', icon: 'error', details: [], fixes: [], actions: [] };
        
            // IP overlap -- most common
            const ipOverlap = msg.match(/IP\s+([\d.]+\/\d+)\s+is overlapping with\s+IP\s+([\d.]+\/\d+)\s+on interface\s+([\w\-/.]+)\s+and\s+([\w\-/.]+)/i);
            if (ipOverlap) {
                analysis.title = 'IP Address Overlap';
                analysis.icon = 'overlap';
                analysis.details.push(
                    `Your IP <code>${ipOverlap[1]}</code> conflicts with existing IP on <code>${ipOverlap[3]}</code>`,
                    `Both <code>${ipOverlap[3]}</code> and <code>${ipOverlap[4]}</code> would use the same subnet`
                );
                analysis.fixes.push('The wizard will find a non-overlapping range automatically');
                analysis.conflictingIp = ipOverlap[1];
                analysis.conflictingIface = ipOverlap[3];
                analysis.newIface = ipOverlap[4];
                analysis.actions.push({ id: 'reopen-fix-ip', label: 'Fix IP & Re-push', style: 'primary', desc: 'Re-open wizard at IP step with auto-suggested range' });
                analysis.actions.push({ id: 'delete-conflicting', label: 'Delete Conflicting Interface', style: 'danger', desc: `Remove ${ipOverlap[3]} from device first` });
                return analysis;
            }
        
            // Generic overlap
            if (t.includes('overlapping')) {
                analysis.title = 'Address Overlap';
                analysis.icon = 'overlap';
                analysis.details.push('An IP address or range conflicts with an existing configuration.');
                const ipMatch = msg.match(/IP\s+([\d.]+\/\d+)/i);
                if (ipMatch) analysis.details.push(`Conflicting address: <code>${ipMatch[1]}</code>`);
                analysis.actions.push({ id: 'reopen-fix-ip', label: 'Fix IP & Re-push', style: 'primary', desc: 'Re-open wizard to pick a non-overlapping range' });
                return analysis;
            }
        
            // Already exists
            if (t.includes('already exists') || t.includes('already configured')) {
                analysis.title = 'Duplicate Configuration';
                analysis.icon = 'duplicate';
                const iface = msg.match(/([\w\-/.]+)\s+already exists/i);
                const existingName = iface ? iface[1] : null;
                analysis.details.push(existingName
                    ? `<code>${existingName}</code> is already configured on this device`
                    : 'The object you are creating already exists on this device');
                analysis.actions.push({ id: 'delete-then-push', label: 'Delete & Re-push', style: 'primary', desc: existingName ? `Remove ${existingName}, then push again` : 'Remove existing, then push' });
                analysis.actions.push({ id: 'reopen-edit', label: 'Edit Parameters', style: 'secondary', desc: 'Change start number or VLAN to avoid collision' });
                return analysis;
            }
        
            // Resource limit
            if (t.includes('limit') || t.includes('exceeded') || t.includes('too many elements') || t.includes('stag') || t.includes('leaflist')) {
                analysis.title = 'Platform Limit Exceeded';
                analysis.icon = 'limit';
                analysis.details.push('The device has reached a hardware or software resource limit.');
                const numMatch = msg.match(/(\d+)\s*(?:elements|entries|limit)/i);
                if (numMatch) analysis.details.push(`Current limit: <code>${numMatch[1]}</code>`);
                analysis.actions.push({ id: 'reopen-reduce', label: 'Reduce Count & Re-push', style: 'primary', desc: 'Re-open wizard with a smaller sub-interface count' });
                return analysis;
            }
        
            // Resource allocation
            if (t.includes('hook failed') || t.includes('assign_new_if_index') || t.includes('resource')) {
                analysis.title = 'Resource Allocation Failed';
                analysis.icon = 'resource';
                analysis.details.push('The device could not allocate internal resources for this configuration.');
                analysis.fixes.push('Try pushing fewer interfaces at a time');
                return analysis;
            }
        
            // L2/L3 conflict
            if ((t.includes('ip-address') || t.includes('ip address')) && t.includes('l2-service')) {
                analysis.title = 'L2/L3 Conflict';
                analysis.icon = 'conflict';
                analysis.details.push('Cannot combine IP addressing with L2 service mode on the same interface.');
                analysis.actions.push({ id: 'reopen-fix-mode', label: 'Fix Mode & Re-push', style: 'primary', desc: 'Re-open wizard to change interface mode' });
                return analysis;
            }
        
            // Syntax error
            if (t.includes('syntax') || t.includes('unknown word') || t.includes('invalid input')) {
                analysis.title = 'Syntax Error';
                analysis.icon = 'syntax';
                const wordMatch = msg.match(/Unknown word:\s*'([^']+)'/i) || msg.match(/unknown word:\s*(\S+)/i);
                if (wordMatch) analysis.details.push(`Rejected token: <code>${wordMatch[1]}</code>`);
                analysis.details.push('The device rejected the configuration due to a syntax issue.');
                analysis.fixes.push('Check the terminal output for the exact line that failed');
                return analysis;
            }
        
            // Commit check hook
            if (t.includes('hook:') || t.includes('from hook')) {
                analysis.title = 'Validation Hook Rejected';
                analysis.icon = 'hook';
                const hookMatch = msg.match(/from hook:\s*([\w_]+)/i);
                if (hookMatch) analysis.details.push(`Hook: <code>${hookMatch[1]}</code>`);
                analysis.details.push('A device-side validation hook rejected this configuration.');
                analysis.fixes.push('Review the terminal output for hook-specific error details');
                return analysis;
            }
        
            // Generic fallback
            analysis.details.push(msg.length > 300 ? msg.slice(0, 300) + '...' : msg);
            analysis.fixes.push('Review the terminal output above for details');
            return analysis;
        },

    });
})(window.ScalerGUI);
