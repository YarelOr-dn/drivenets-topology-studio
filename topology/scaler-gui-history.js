/**
 * ScalerGUI: wizard history panel + commits panel
 * Source: split from scaler-gui.js.bak
 * @requires scaler-api.js
 * @requires scaler-gui.js (core)
 */
(function (G) {
    'use strict';
    if (!G) {
        console.error('[scaler-gui-history.js] ScalerGUI core not loaded');
        return;
    }
    Object.assign(G, {
        openWizardHistoryPanel() {
            const history = this.getWizardHistory();
            const sorted = [...history].sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
            const savedRuns = sorted.filter(r => r.success === 'saved');
            const completedRuns = sorted.filter(r => r.success !== 'saved');
            const content = document.createElement('div');
            content.className = 'scaler-history-panel';
            content.innerHTML = `
                <div class="scaler-history-header">
                    <span>Wizard History</span>
                </div>
                <div class="scaler-history-list" id="scaler-history-list"></div>
            `;
            this.openPanel('wizard-history', 'Wizard Run History', content, { width: '540px', minimizable: true });
            const listEl = document.getElementById('scaler-history-list');
            if (sorted.length === 0) {
                listEl.innerHTML = '<div class="scaler-history-empty">No wizard runs yet. Complete a wizard or use "Save for Later" to see history here.</div>';
                return;
            }
        
            const wizardLabels = { interfaces: 'Interface', services: 'Service', vrf: 'VRF', 'bridge-domain': 'Bridge Domain', flowspec: 'FlowSpec', 'flowspec-vpn': 'FlowSpec VPN', 'routing-policy': 'Routing Policy', bgp: 'BGP', igp: 'IGP' };
            const typeToOpen = { interfaces: 'openInterfaceWizard', services: 'openServiceWizard', vrf: 'openVRFWizard', 'bridge-domain': 'openBridgeDomainWizard', flowspec: 'openFlowSpecWizard', 'flowspec-vpn': 'openFlowSpecVPNWizard', 'routing-policy': 'openRoutingPolicyWizard', bgp: 'openBGPWizard', igp: 'openIGPWizard' };
        
            const self = this;
            const renderEntry = (rec, isSaved) => {
                const summary = this._formatLastRunSummary(rec);
                let status, statusText;
                if (isSaved) {
                    status = 'saved';
                    statusText = 'Saved';
                } else {
                    status = rec.success === true ? 'success' : rec.success === false ? 'failed' : 'pending';
                    statusText = rec.success === true ? 'OK' : rec.success === false ? 'Failed' : 'Pending';
                }
                const openMethod = typeToOpen[rec.wizardType] || 'openInterfaceWizard';
                const li = document.createElement('li');
                li.className = `scaler-history-entry${isSaved ? ' scaler-history-saved' : ''}`;
                li.dataset.recId = rec.id || '';
                const pushBtn = isSaved ? '<button type="button" class="scaler-btn scaler-btn-sm scaler-btn-primary scaler-history-push">Push</button>' : '';
                const deleteBtn = isSaved ? '<button type="button" class="scaler-btn scaler-btn-sm scaler-history-delete" title="Remove saved run">Remove</button>' : '';
                li.innerHTML = `
                    <div class="scaler-history-entry-header">
                        <span class="scaler-history-type">${this.escapeHtml(wizardLabels[rec.wizardType] || rec.wizardType || '?')}</span>
                        <span class="scaler-history-device">${this.escapeHtml(rec.deviceLabel || rec.deviceId || '?')}</span>
                        <span class="scaler-history-status scaler-history-status-${status}">${statusText}</span>
                    </div>
                    <div class="scaler-history-summary">${this.escapeHtml(summary)}</div>
                    <div class="scaler-history-meta">
                        <span class="scaler-history-ts">${rec.timestamp ? new Date(rec.timestamp).toLocaleTimeString() : ''}</span>
                        ${rec.configLineCount ? `<span class="scaler-history-lines">${rec.configLineCount} lines</span>` : ''}
                    </div>
                    <div class="scaler-history-actions" style="display:none">
                        ${pushBtn}
                        <button type="button" class="scaler-btn scaler-btn-sm scaler-history-edit">Edit</button>
                        <button type="button" class="scaler-btn scaler-btn-sm scaler-history-rerun">Re-run</button>
                        ${!isSaved ? '<button type="button" class="scaler-btn scaler-btn-sm scaler-history-rerun-other">Re-run on other device</button>' : ''}
                        ${deleteBtn}
                    </div>
                `;
                li.querySelector('.scaler-history-entry-header')?.addEventListener('click', () => {
                    const acts = li.querySelector('.scaler-history-actions');
                    if (acts) acts.style.display = acts.style.display === 'none' ? 'flex' : 'none';
                });
                li.querySelector('.scaler-history-edit')?.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    self.closePanel('wizard-history');
                    const fn = self[openMethod];
                    if (typeof fn !== 'function') return;
                    if (!rec.deviceId) { self.showNotification('Cannot edit: device not recorded', 'warning'); return; }
                    const { deviceContext, generatedConfig, ...params } = rec.params || {};
                    await fn.call(self, rec.deviceId, params);
                });
                li.querySelector('.scaler-history-push')?.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    self.closePanel('wizard-history');
                    const fn = self[openMethod];
                    if (typeof fn !== 'function') return;
                    if (!rec.deviceId) { self.showNotification('Cannot push: device not recorded', 'warning'); return; }
                    const { deviceContext, ...params } = rec.params || {};
                    params._rerunMode = true;
                    params.generatedConfig = rec.generatedConfig || '';
                    await fn.call(self, rec.deviceId, params);
                });
                li.querySelector('.scaler-history-rerun')?.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    self.closePanel('wizard-history');
                    const fn = self[openMethod];
                    if (typeof fn !== 'function') return;
                    if (!rec.deviceId) { self.showNotification('Cannot re-run: device not recorded', 'warning'); return; }
                    const { deviceContext, ...params } = rec.params || {};
                    params._rerunMode = true;
                    await fn.call(self, rec.deviceId, params);
                });
                li.querySelector('.scaler-history-rerun-other')?.addEventListener('click', (e) => {
                    e.stopPropagation();
                    self.closePanel('wizard-history');
                    self.openMirrorWizard(rec.deviceId);
                });
                li.querySelector('.scaler-history-delete')?.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const idx = self._wizardHistory.findIndex(r => r.id === rec.id);
                    if (idx >= 0) {
                        self._wizardHistory.splice(idx, 1);
                        self._saveWizardHistory();
                        li.remove();
                        self.showNotification('Saved run removed', 'info');
                    }
                });
                return li;
            };
        
            if (savedRuns.length > 0) {
                const savedSection = document.createElement('div');
                savedSection.className = 'scaler-history-group scaler-history-saved-group';
                savedSection.innerHTML = `<div class="scaler-history-date scaler-history-saved-header">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                    Saved for Later <span class="scaler-history-saved-count">${savedRuns.length}</span>
                </div>`;
                const ul = document.createElement('ul');
                ul.className = 'scaler-history-entries';
                savedRuns.forEach(rec => ul.appendChild(renderEntry(rec, true)));
                savedSection.appendChild(ul);
                listEl.appendChild(savedSection);
            }
        
            const byDate = {};
            completedRuns.forEach(r => {
                const d = r.timestamp ? new Date(r.timestamp).toDateString() : 'Unknown';
                if (!byDate[d]) byDate[d] = [];
                byDate[d].push(r);
            });
            if (completedRuns.length > 0) {
                Object.keys(byDate).forEach(date => {
                    const group = document.createElement('div');
                    group.className = 'scaler-history-group';
                    group.innerHTML = `<div class="scaler-history-date">${date}</div>`;
                    const ul = document.createElement('ul');
                    ul.className = 'scaler-history-entries';
                    byDate[date].forEach(rec => ul.appendChild(renderEntry(rec, false)));
                    group.appendChild(ul);
                    listEl.appendChild(group);
                });
            }
        },
        
        openCommitsPanel() {
            const content = document.createElement('div');
            content.className = 'scaler-commits-panel';
            content.innerHTML = `
                <div class="scaler-commits-header">
                    <span>Active and recent configuration pushes</span>
                    <button class="scaler-btn scaler-btn-sm" id="commits-refresh">Refresh</button>
                </div>
                <div class="scaler-commits-list" id="scaler-commits-list">
                    <div class="scaler-loading">Loading jobs...</div>
                </div>
            `;
            const panel = this.openPanel('running-commits', 'Running Commits', content, { width: '560px', minimizable: true });
            let pollTimer = null;
            const listEl = document.getElementById('scaler-commits-list');
        
            const suggestErrorFix = (text) => {
                const t = (text || '').toLowerCase();
                const out = [];
                if (t.includes('already exists')) out.push('Interface already configured. Use Replace mode or delete first.');
                if (t.includes('not found')) out.push('Referenced item missing. Create parent interfaces/services first.');
                if (t.includes('invalid')) out.push('Check syntax and valid value ranges.');
                if (t.includes('limit') || t.includes('exceeded') || t.includes('stag')) out.push('Platform limit reached. Reduce count or delete unused interfaces.');
                if (t.includes('hook failed') || t.includes('assign_new_if_index')) out.push('Resource allocation failed. Check NCC logs.');
                if (t.includes('too many elements') || t.includes('leaflist')) out.push('Too many elements for this hierarchy. Reduce count.');
                if (t.includes('ip-address') && t.includes('l2-service')) out.push('Cannot add L2 to interface with IP. Delete IP first or use different sub-interface.');
                if (t.includes('conflict')) out.push('Configuration conflict. Check for duplicates.');
                if (t.includes('syntax')) out.push('Check missing keywords, brackets, or parameter order.');
                return out.length ? out : ['Check the terminal output above for details.'];
            };
        
            const formatAgo = (iso) => {
                if (!iso) return '';
                const d = new Date(iso);
                const s = Math.floor((Date.now() - d) / 1000);
                if (s < 60) return s + 's ago';
                if (s < 3600) return Math.floor(s / 60) + 'm ago';
                if (s < 86400) return Math.floor(s / 3600) + 'h ago';
                return Math.floor(s / 86400) + 'd ago';
            };
        
            const renderDeviceStateRows = (deviceState) => {
                if (!deviceState || typeof deviceState !== 'object') return '';
                const rows = Object.entries(deviceState).map(([did, s]) => {
                    const status = s.status || 'pending';
                    const phase = s.phase || s.message || 'Waiting...';
                    const pct = s.percent ?? 0;
                    const icon = status === 'completed' ? '[OK]' : status === 'failed' ? '[FAIL]' : status === 'skipped' ? '[SKIP]' : '[...]';
                    const rowClass = status === 'failed' ? 'scaler-progress-device-row--failed' : status === 'completed' ? 'scaler-progress-device-row--ok' : '';
                    return `<div class="scaler-progress-device-row ${rowClass}">
                        <span class="scaler-progress-device-name">${this.escapeHtml(did)}</span>
                        <span class="scaler-progress-device-icon">${icon}</span>
                        <span class="scaler-progress-device-phase">${this.escapeHtml(phase)}</span>
                        <div class="scaler-progress-device-bar"><div class="scaler-progress-device-fill" style="width:${pct}%"></div></div>
                    </div>`;
                });
                return rows.length ? `<div class="scaler-progress-device-rows scaler-job-device-state">${rows.join('')}</div>` : '';
            };
        
            const renderJobCard = (job) => {
                const status = job.status || 'pending';
                const dotClass = status === 'running' ? 'scaler-job-dot-running' : status === 'completed' ? 'scaler-job-dot-ok' : status === 'failed' ? 'scaler-job-dot-fail' : 'scaler-job-dot-pending';
                const name = job.job_name || job.device_id || 'Push';
                const pct = job.percent || 0;
                const msg = job.message || job.phase || '';
                const lines = job.terminal_lines || [];
                const terminalHtml = lines.map((l) => `<div class="scaler-terminal-line">${this.escapeHtml(l)}</div>`).join('');
                const isExpanded = this._commitsExpanded && this._commitsExpanded[job.job_id];
                const fullText = lines.join('\n');
                const suggestions = status === 'failed' ? suggestErrorFix(job.message || fullText) : [];
                const suggestionHtml = suggestions.length ? `<div class="scaler-job-error-box"><strong>Suggestions:</strong><ul>${suggestions.map((s) => `<li>${this.escapeHtml(s)}</li>`).join('')}</ul></div>` : '';
                const deviceStateHtml = renderDeviceStateRows(job.device_state);
                return `
                    <div class="scaler-job-card ${status}" data-job-id="${job.job_id}">
                        <div class="scaler-job-card-header">
                            <span class="scaler-job-dot ${dotClass}"></span>
                            <span class="scaler-job-name">${this.escapeHtml(name)}</span>
                            <span class="scaler-job-ago">${formatAgo(job.started_at)}</span>
                            <button class="scaler-job-toggle" data-job-id="${job.job_id}" title="${isExpanded ? 'Minimize' : 'Expand'}">${isExpanded ? '-' : '+'}</button>
                        </div>
                        <div class="scaler-job-progress" style="display:${status === 'running' ? 'block' : 'none'}">
                            <div class="scaler-progress-bar"><div class="scaler-progress-fill" style="width:${pct}%"></div></div>
                            <span class="scaler-job-phase">${this.escapeHtml(msg)}</span>
                        </div>
                        ${deviceStateHtml ? `<div class="scaler-job-device-state-wrap">${deviceStateHtml}</div>` : ''}
                        <div class="scaler-job-terminal scaler-collapse-section ${isExpanded ? '' : 'collapsed'}" data-job-id="${job.job_id}">
                            <div class="scaler-terminal-content">${terminalHtml}</div>
                            ${suggestionHtml}
                            ${(status === 'failed' || status === 'completed') ? `
                            <div class="scaler-job-actions">
                                <button class="scaler-btn scaler-btn-sm scaler-job-retry" data-job-id="${job.job_id}">Retry</button>
                                <button class="scaler-btn scaler-btn-sm scaler-job-copy" data-job-id="${job.job_id}">Copy output</button>
                            </div>` : ''}
                        </div>
                    </div>`;
            };
        
            const render = async () => {
                if (!listEl.isConnected) {
                    stopPoll();
                    return;
                }
                try {
                    const res = await ScalerAPI.getJobs();
                    const jobs = res.jobs || [];
                    if (jobs.length === 0) {
                        listEl.innerHTML = '<div class="scaler-empty">No push jobs yet. Run a wizard and push config to see them here.</div>';
                    } else {
                        listEl.innerHTML = jobs.map((j) => renderJobCard(j)).join('');
                        listEl.querySelectorAll('.scaler-job-toggle').forEach((btn) => {
                            btn.onclick = () => {
                                this._commitsExpanded = this._commitsExpanded || {};
                                const jid = btn.dataset.jobId;
                                this._commitsExpanded[jid] = !this._commitsExpanded[jid];
                                render();
                            };
                        });
                        listEl.querySelectorAll('.scaler-job-retry').forEach((btn) => {
                            btn.onclick = async () => {
                                try {
                                    const jid = btn.dataset.jobId;
                                    const r = await ScalerAPI.retryJob(jid);
                                    const job = jobs.find((j) => j.job_id === jid);
                                    const deviceIds = job?.device_state ? Object.keys(job.device_state) : [];
                                    const opts = deviceIds.length ? { upgradeDevices: deviceIds } : {};
                                    this.showProgress(r.job_id, job?.job_name || r.job_id, opts);
                                    this.showNotification('Retry started', 'success');
                                    render();
                                } catch (e) {
                                    this.showNotification(e.message, 'error');
                                }
                            };
                        });
                        listEl.querySelectorAll('.scaler-job-copy').forEach((btn) => {
                            btn.onclick = async () => {
                                const card = btn.closest('.scaler-job-card');
                                const jid = card?.dataset?.jobId;
                                const job = jobs.find((j) => j.job_id === jid);
                                const text = (job?.terminal_lines || []).join('');
                                try {
                                    await window.safeClipboardWrite(text);
                                    this.showNotification('Terminal output copied', 'success');
                                } catch (_) {}
                            };
                        });
                    }
                    const activeCount = jobs.filter((j) => j.status === 'running' || j.status === 'pending').length;
                    const badge = document.getElementById('scaler-commits-badge');
                    if (badge) {
                        badge.style.display = activeCount > 0 ? 'inline' : 'none';
                        badge.textContent = activeCount;
                    }
                } catch (e) {
                    listEl.innerHTML = `<div class="scaler-error">Failed to load jobs: ${e.message}</div>`;
                }
            };
        
            const startPoll = () => {
                if (pollTimer) clearInterval(pollTimer);
                pollTimer = setInterval(render, 2000);
            };
            const stopPoll = () => {
                if (pollTimer) clearInterval(pollTimer);
                pollTimer = null;
            };
        
            document.getElementById('commits-refresh').onclick = () => render();
            this._commitsExpanded = this._commitsExpanded || {};
            render();
            startPoll();
        },

    });
})(window.ScalerGUI);
