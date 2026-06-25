/**
 * ScalerGUI: upgrade banners, upgrade/scale/stag wizards, ScalerAPI.operation patches
 * Source: split from scaler-gui.js.bak
 * @requires scaler-api.js
 * @requires scaler-gui.js (core)
 */
(function (G) {
    'use strict';
    if (!G) {
        console.error('[scaler-gui-upgrade.js] ScalerGUI core not loaded');
        return;
    }
    Object.assign(G, {
        async _checkRunningUpgrades() {
            if (window.TopologyAuth && typeof window.TopologyAuth.isAuthenticated === 'function'
                && !window.TopologyAuth.isAuthenticated()) {
                return;
            }
            try {
                const res = await ScalerAPI.getJobs();
                const allJobs = res.jobs || [];
                const running = allJobs.find(
                    j => (j.job_type === 'upgrade' || j.job_type === 'wait_and_upgrade') && (j.status === 'running' || j.status === 'pending') && !j.done
                );
                if (running) {
                    this._showRunningUpgradeProgress(running);
                    return;
                }
        
                const recentFailedRaw = allJobs.filter(j =>
                    (j.job_type === 'upgrade' || j.job_type === 'wait_and_upgrade')
                    && j.done && (j.status === 'failed' || j.phase === 'interrupted')
                    && j.completed_at
                    && (Date.now() - new Date(j.completed_at).getTime()) < 3600000
                );
                const recentFailed = recentFailedRaw.filter((j) => {
                    const dids = this._collectFailedJobDeviceIds([j]);
                    return dids.some((d) => !this._isUpgradeFailureDismissed(j.job_id, d));
                });
                if (recentFailed.length > 0) {
                    this._showFailedUpgradeBanner(recentFailed);
                }
        
                const stored = localStorage.getItem('scaler_active_upgrade');
                if (stored) {
                    try {
                        const info = JSON.parse(stored);
                        if (info.job_id && (Date.now() - info.started_at) < 7200000) {
                            const match = allJobs.find(j => j.job_id === info.job_id);
                            if (match && !match.done) {
                                this._showRunningUpgradeProgress(match);
                                return;
                            }
                            if (match && match.done && (match.status === 'failed' || match.phase === 'interrupted')) {
                                const dids = this._collectFailedJobDeviceIds([match]);
                                if (dids.some((d) => !this._isUpgradeFailureDismissed(match.job_id, d))) {
                                    this._showFailedUpgradeBanner([match]);
                                }
                            }
                        }
                        localStorage.removeItem('scaler_active_upgrade');
                    } catch (_) { localStorage.removeItem('scaler_active_upgrade'); }
                }
            } catch (_) {}

            // Stuck-upgrade banner: surface devices where the bridge
            // crashed mid-upgrade and the orphan scanner couldn't auto-
            // resume (typically because the deploy URLs / system_type /
            // ncc_id weren't persisted). The Resume Stuck Upgrade panel
            // lets the operator complete it without SSH'ing manually.
            try {
                await this._checkStuckDevices();
            } catch (_) {}
        },

        async _checkStuckDevices() {
            try {
                if (!ScalerAPI || typeof ScalerAPI.getStuckDevices !== 'function') return;
                const res = await ScalerAPI.getStuckDevices();
                const stuck = (res && res.stuck_devices) || [];
                if (stuck.length === 0) {
                    const banner = document.getElementById('upgrade-stuck-banner');
                    if (banner) banner.remove();
                    return;
                }
                this._showStuckUpgradeBanner(stuck);
            } catch (e) {
                console.warn('[upgrade] stuck-devices check failed:', e?.message || e);
            }
        },

        _showStuckUpgradeBanner(stuckDevices) {
            const self = this;
            let banner = document.getElementById('upgrade-stuck-banner');
            if (banner) banner.remove();
            banner = document.createElement('div');
            banner.id = 'upgrade-stuck-banner';
            banner.className = 'upgrade-failed-banner';
            banner.style.background = '#7a4d00';
            const devSummary = stuckDevices.map(d => {
                const missing = (d.missing && d.missing.length)
                    ? ` (missing: ${d.missing.join(', ')})` : '';
                return `<span class="upgrade-failed-dev">${self.escapeHtml(d.device_id)}</span>` +
                       `<span class="upgrade-failed-phase">${self.escapeHtml(missing)}</span>`;
            }).join(', ');
            banner.innerHTML = `
                <div class="upgrade-failed-banner-content">
                    <span class="upgrade-failed-icon">!</span>
                    <div class="upgrade-failed-text">
                        <strong>Stuck upgrade(s) need attention</strong> -- ${devSummary}
                    </div>
                    <div class="upgrade-failed-actions">
                        <button type="button" class="scaler-btn scaler-btn-sm scaler-btn-primary" id="upgrade-stuck-resume">Resume</button>
                        <button type="button" class="scaler-btn scaler-btn-sm" id="upgrade-stuck-clear">Clear flag</button>
                        <button type="button" class="scaler-btn scaler-btn-sm" id="upgrade-stuck-dismiss">Dismiss</button>
                    </div>
                </div>
            `;
            document.body.appendChild(banner);
            banner.querySelector('#upgrade-stuck-dismiss').addEventListener('click', () => banner.remove());
            banner.querySelector('#upgrade-stuck-clear').addEventListener('click', async () => {
                try {
                    const ids = stuckDevices.map(d => d.device_id);
                    await ScalerAPI.clearStuckDevices(ids);
                    self.showNotification(`Cleared stuck-upgrade flag for ${ids.length} device(s)`, 'info');
                    banner.remove();
                } catch (e) {
                    self.showNotification(`Clear failed: ${e?.message || e}`, 'error');
                }
            });
            banner.querySelector('#upgrade-stuck-resume').addEventListener('click', async () => {
                // Auto-resumable devices are those with no missing fields.
                const autoResumable = stuckDevices.filter(d => !d.missing || d.missing.length === 0);
                const needsInput = stuckDevices.filter(d => d.missing && d.missing.length > 0);
                if (needsInput.length > 0) {
                    self.showNotification(
                        `${needsInput.length} device(s) missing fields (${needsInput[0].missing.join(', ')}). ` +
                        `Open the upgrade wizard, fill in the missing parameters, then retry.`,
                        'warning', 8000
                    );
                }
                if (autoResumable.length === 0) return;
                try {
                    const ids = autoResumable.map(d => d.device_id);
                    const res = await ScalerAPI.resumeStuckDevices(ids);
                    const queued = Object.entries(res.results || {})
                        .filter(([, v]) => v.status === 'queued')
                        .map(([k]) => k);
                    self.showNotification(`Recovery queued for ${queued.length} device(s): ${queued.join(', ')}`, 'success');
                    banner.remove();
                    setTimeout(() => self._checkRunningUpgrades(), 1500);
                } catch (e) {
                    self.showNotification(`Resume failed: ${e?.message || e}`, 'error');
                }
            });
        },

        /**
         * Persisted dismiss keys: "jobId:deviceLabel" so the canvas red badge and bottom
         * banner stay cleared after the user dismisses (job watcher skips re-applying).
         */
        _getDismissedUpgradeFailureKeys() {
            try {
                const raw = localStorage.getItem('scaler_dismissed_upgrade_failures');
                const arr = raw ? JSON.parse(raw) : [];
                return Array.isArray(arr) ? arr : [];
            } catch (_) {
                return [];
            }
        },
        _isUpgradeFailureDismissed(jobId, deviceLabel) {
            if (!jobId || !deviceLabel) return false;
            return this._getDismissedUpgradeFailureKeys().includes(`${jobId}:${deviceLabel}`);
        },
        /**
         * Mark failure dismissed for listed devices, clear matching canvas badges, remove banner.
         */
        dismissUpgradeFailureAlert(jobId, deviceLabels) {
            const jid = (jobId || '').trim();
            const labels = Array.isArray(deviceLabels) ? deviceLabels.filter(Boolean) : [];
            if (!jid || labels.length === 0) return;
            const keys = this._getDismissedUpgradeFailureKeys();
            for (const lab of labels) {
                const k = `${jid}:${lab}`;
                if (!keys.includes(k)) keys.push(k);
            }
            try {
                localStorage.setItem('scaler_dismissed_upgrade_failures', JSON.stringify(keys));
            } catch (_) {}
            const editor = window.topologyEditor;
            if (editor?.objects) {
                for (const o of editor.objects) {
                    if (o.type !== 'device') continue;
                    if (!labels.includes(o.label)) continue;
                    const fj = o._upgradeFailedJob;
                    if (fj && (fj.jobId === jid || fj.job_id === jid)) {
                        o._upgradeFailedJob = null;
                    }
                }
                if (editor.requestDraw) editor.requestDraw();
            }
            const b = document.getElementById('upgrade-failed-banner');
            if (b) b.remove();
        },
        
        _collectFailedJobDeviceIds(failedJobs) {
            const out = [];
            for (const j of failedJobs || []) {
                const ds = j.device_state || {};
                const fromState = Object.entries(ds)
                    .filter(([, s]) => s && (s.status === 'failed' || s.phase === 'interrupted'))
                    .map(([did]) => did);
                const fromArr = Array.isArray(j.devices) ? j.devices : [];
                let merged = [...fromState, ...fromArr];
                if (merged.length === 0 && j.device_id) merged.push(j.device_id);
                if (merged.length === 0 && (j.status === 'failed' || j.phase === 'interrupted')) {
                    const keys = Object.keys(ds);
                    for (const k of keys) {
                        if (!merged.includes(k)) merged.push(k);
                    }
                }
                for (const d of merged) {
                    if (d && !out.includes(d)) out.push(d);
                }
            }
            return out;
        },
        
        _shouldShowFailedUpgradeBanner(failedJobs) {
            const fj = failedJobs || [];
            if (fj.length === 0) return false;
            for (const j of fj) {
                const jid = j.job_id || '';
                const dids = this._collectFailedJobDeviceIds([j]);
                for (const did of dids) {
                    if (!this._isUpgradeFailureDismissed(jid, did)) return true;
                }
            }
            return false;
        },
        
        _showFailedUpgradeBanner(failedJobs) {
            if (!this._shouldShowFailedUpgradeBanner(failedJobs)) return;
            let banner = document.getElementById('upgrade-failed-banner');
            if (banner) banner.remove();
            banner = document.createElement('div');
            banner.id = 'upgrade-failed-banner';
            banner.className = 'upgrade-failed-banner';
            const self = this;
            const devEntries = failedJobs.flatMap(j => {
                const ds = j.device_state || {};
                return Object.entries(ds)
                    .filter(([, s]) => s.status === 'failed' || s.phase === 'interrupted')
                    .map(([did, s]) => {
                        const phase = s.phase || s.message || 'unknown';
                        return `<span class="upgrade-failed-dev">${self.escapeHtml(did)}</span> <span class="upgrade-failed-phase">(${self.escapeHtml(phase)})</span>`;
                    });
            });
            const devSummary = devEntries.length > 0 ? devEntries.join(', ') : failedJobs.flatMap(j => j.devices || []).join(', ');
            const jobId = failedJobs[0]?.job_id || '';
            const deviceIdsForDismiss = this._collectFailedJobDeviceIds(failedJobs);
            const firstDev = deviceIdsForDismiss[0] || (failedJobs[0]?.devices || [])[0] || '';
            banner.innerHTML = `
                <div class="upgrade-failed-banner-content">
                    <span class="upgrade-failed-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M17 8l-5-5-5 5"/><path d="M12 3v12"/></svg></span>
                    <div class="upgrade-failed-text">
                        <strong>Upgrade failed</strong> -- <span class="upgrade-failed-devs">${devSummary}</span>
                    </div>
                    <div class="upgrade-failed-actions">
                        <button type="button" class="scaler-btn scaler-btn-sm scaler-btn-primary" id="upgrade-failed-new">New upgrade</button>
                        <button type="button" class="scaler-btn scaler-btn-sm" id="upgrade-failed-details">Details</button>
                        <button type="button" class="scaler-btn scaler-btn-sm" id="upgrade-failed-dismiss">Dismiss</button>
                    </div>
                </div>
            `;
            document.body.appendChild(banner);
            banner.querySelector('#upgrade-failed-dismiss').addEventListener('click', () => {
                self.dismissUpgradeFailureAlert(jobId, deviceIdsForDismiss);
                self.showNotification('Failure alert dismissed', 'info');
            });
            banner.querySelector('#upgrade-failed-new').addEventListener('click', () => {
                if (firstDev) {
                    self.dismissUpgradeFailureAlert(jobId, deviceIdsForDismiss);
                    self.openUpgradeWizard({ deviceId: firstDev });
                } else {
                    self.showNotification('No device id for wizard', 'warning');
                }
            });
            banner.querySelector('#upgrade-failed-details').addEventListener('click', () => {
                banner.remove();
                const devices = failedJobs.flatMap(j => j.devices || []);
                const sshHosts = failedJobs[0]?.ssh_hosts || {};
                this.showProgress(jobId, failedJobs[0]?.job_name || 'Failed upgrade', {
                    upgradeDevices: devices.length ? devices : deviceIdsForDismiss,
                    upgradeSshHosts: sshHosts,
                });
            });
        },
        async _findRunningUpgradeJob() {
            try {
                const res = await ScalerAPI.getJobs();
                const allJobs = res.jobs || [];
                const running = allJobs.find(
                    j => (j.job_type === 'upgrade' || j.job_type === 'wait_and_upgrade') && (j.status === 'running' || j.status === 'pending') && !j.done
                );
                if (running) return running;
                const stored = localStorage.getItem('scaler_active_upgrade');
                if (stored) {
                    const info = JSON.parse(stored);
                    if (info.job_id && (Date.now() - info.started_at) < 7200000) {
                        const match = allJobs.find(j => j.job_id === info.job_id && !j.done);
                        if (match) return match;
                    }
                }
            } catch (_) {}
            return null;
        },
        
        _showRunningUpgradeProgress(job) {
            const banner = document.getElementById('upgrade-active-banner');
            if (banner) banner.remove();
            const deviceIds = job.devices || (job.device_state ? Object.keys(job.device_state) : []);
            const sshHosts = job.ssh_hosts || {};
            this.showProgress(job.job_id, job.job_name || `Upgrading ${deviceIds.length} devices`, {
                upgradeDevices: deviceIds,
                upgradeSshHosts: sshHosts,
                _initialJobData: job,
                onComplete: () => {
                    const editor = window.topologyEditor;
                    if (editor?.objects) {
                        editor.objects.forEach(o => { if (o.type === 'device') o._upgradeInProgress = false; });
                    }
                }
            });
        },
        
        _showUpgradeBanner(jobId, jobName, deviceIds, sshHosts) {
            let banner = document.getElementById('upgrade-active-banner');
            if (banner) banner.remove();
            banner = document.createElement('div');
            banner.id = 'upgrade-active-banner';
            banner.className = 'upgrade-active-banner';
            banner.innerHTML = `
                <div class="upgrade-active-banner-inner">
                    <div class="upgrade-banner-pulse"></div>
                    <span class="upgrade-banner-text">Upgrade in progress -- ${deviceIds.length} device${deviceIds.length !== 1 ? 's' : ''}</span>
                    <button class="upgrade-banner-btn">View Progress</button>
                </div>
            `;
            banner.querySelector('.upgrade-banner-btn').onclick = () => {
                banner.remove();
                this._showRunningUpgradeProgress({
                    job_id: jobId,
                    job_name: jobName,
                    devices: deviceIds,
                    ssh_hosts: sshHosts,
                });
            };
            document.body.appendChild(banner);
            setTimeout(() => banner.classList.add('visible'), 50);
        },
        _formatUpgradeAge(h) {
            if (h < 1) return `${Math.round(h * 60)}m`;
            if (h < 24) return `${Math.round(h)}h`;
            return `${(h / 24).toFixed(1)}d`;
        },
        
        _extractVerForUpgrade(s) {
            if (!s) return '';
            const dotted = s.match(/(\d+\.\d+\.\d+[\d._]*)/);
            if (dotted) return dotted[1];
            const devBranch = s.match(/[_/]v(\d+)[_.](\d+)/);
            if (devBranch) return `${devBranch[1]}.${devBranch[2]}`;
            return '';
        },
        
        async _checkRunningBuild(branch, { silent = false } = {}) {
            if (!branch || !this.WizardController) return null;
            const self = this;
            console.log('%c[UpgradeWiz] _checkRunningBuild for: ' + branch, 'color:#ff9800;font-weight:bold');
            self.WizardController.data._runningBuildChecking = true;
            self.WizardController.data._runningBuildCheckedBranch = branch;
            let rb = null;
            try {
                const url = ScalerAPI._api(`/api/operations/image-upgrade/build-status/${encodeURIComponent(branch)}?latest=true&_t=${Date.now()}`);
                console.log('[UpgradeWiz] Fetching:', url);
                const resp = await fetch(url, { cache: 'no-store' });
                console.log('[UpgradeWiz] Response status:', resp.status);
                if (!resp.ok) {
                    const errBody = await resp.text();
                    console.error('[UpgradeWiz] API error:', resp.status, errBody);
                    throw new Error(`API returned ${resp.status}`);
                }
                const st = await resp.json();
                console.log('%c[UpgradeWiz] Build status RAW:', 'color:#00bcd4', JSON.stringify(st));
                if (st.building && st.build_number) {
                    const ageMin = Math.round((st.age_hours || 0) * 60);
                    const params = st.build_params || {};
                    const flags = [];
                    if (params.SHOULD_BUILD_BASEOS_CONTAINERS === 'Yes' || params.WITH_BASEOS === 'true' || params.with_baseos === 'true') flags.push('BaseOS');
                    if ((params.TESTS_TO_RUN && params.TESTS_TO_RUN.includes('ENABLE_SANITIZER')) || (params.TEST_NAMES && params.TEST_NAMES.includes('ENABLE_SANITIZER'))) flags.push('Sanitizer');
                    if (params.QA_VERSION === 'true' || params.QA_VERSION === true) flags.push('QA');
                    const flagStr = flags.length ? ` (${flags.join(', ')})` : '';
                    rb = { build_number: st.build_number, ageMin, flagStr, params, age_hours: st.age_hours };
                    self.WizardController.data._runningBuild = rb;
                    const tgtVer = self._extractVerForUpgrade(branch);
                    if (tgtVer) self.WizardController.data._targetVersion = tgtVer;
                    console.log('%c[UpgradeWiz] RUNNING BUILD DETECTED: #' + st.build_number + flagStr, 'color:#4caf50;font-weight:bold');
                } else {
                    self.WizardController.data._runningBuild = null;
                    console.log('[UpgradeWiz] No running build (building=' + st.building + ', build_number=' + st.build_number + ')');
                }
            } catch (err) {
                console.error('[UpgradeWiz] Running build check FAILED:', err);
                self.WizardController.data._runningBuild = null;
            }
            self.WizardController.data._runningBuildChecking = false;
            if (!silent) {
                self._injectRunningBuildBanner(rb);
                try { self.WizardController.render(); } catch (e) { console.warn('[UpgradeWiz] render() failed:', e); }
            }
            return rb;
        },
        
        _injectRunningBuildBanner(rb) {
            const self = this;
            const inject = (attempt) => {
                const container = document.querySelector('.scaler-wizard-step-content .scaler-form');
                if (!container) {
                    if (attempt < 10) {
                        console.log(`[UpgradeWiz] Banner inject: .scaler-form not found, retry ${attempt + 1}/10 in 500ms`);
                        setTimeout(() => inject(attempt + 1), 500);
                    } else {
                        console.warn('[UpgradeWiz] Banner inject: gave up after 10 retries');
                    }
                    return;
                }
                const existing = container.querySelector('.upgrade-running-banner');
                if (existing) existing.remove();
                if (!rb) return;
                console.log('[UpgradeWiz] Banner inject: inserting banner for build #' + rb.build_number);
                const div = document.createElement('div');
                div.className = 'upgrade-running-banner';
                const _rbDirText = rb._justTriggered && !rb.build_number
                    ? `Build queued${rb.flagStr} -- starting...`
                    : `Build <strong>#${rb.build_number}</strong> is running${rb.flagStr} -- started ${rb.ageMin}m ago.`;
                div.innerHTML = `<div class="scaler-info-box" style="border-color:var(--dn-cyan,#00bcd4);color:var(--dn-cyan,#00bcd4);margin-bottom:10px;padding:10px 14px">
                    <div style="font-weight:600;margin-bottom:4px">Build in progress for this branch</div>
                    <div style="font-size:0.92em">${_rbDirText}</div>
                    <div style="margin-top:8px;display:flex;gap:8px">
                        <button class="scaler-btn scaler-btn-sm scaler-btn-primary" id="upgrade-monitor-running-direct">Monitor Build</button>
                        <button class="scaler-btn scaler-btn-sm" id="upgrade-wait-running-direct" title="Wait for this build to finish then auto-select it">Wait & Select</button>
                    </div>
                </div>`;
                container.insertBefore(div, container.firstChild);
                document.getElementById('upgrade-monitor-running-direct')?.addEventListener('click', () => {
                    self.openCommitsPanel?.();
                });
                document.getElementById('upgrade-wait-running-direct')?.addEventListener('click', async () => {
                    const btn = document.getElementById('upgrade-wait-running-direct');
                    if (btn) { btn.disabled = true; btn.textContent = 'Waiting...'; }
                    const branch = self.WizardController?.data?.branch || '';
                    for (let i = 0; i < 120; i++) {
                        await new Promise(r => setTimeout(r, 15000));
                        try {
                            const st = await ScalerAPI.getUpgradeBuildStatus(branch, true);
                            if (!st.building) {
                                self.WizardController.data._runningBuild = null;
                                self.WizardController.data._runningBuildCheckedBranch = null;
                                self.WizardController.data._fetchAttempted = false;
                                self.WizardController.render();
                                self.showNotification(`Build #${rb.build_number} finished (${st.result || 'UNKNOWN'})`, st.result === 'SUCCESS' ? 'success' : 'warning');
                                return;
                            }
                            const ageMin = Math.round((st.age_hours || 0) * 60);
                            if (btn) btn.textContent = `Waiting... (${ageMin}m)`;
                        } catch (_) {}
                    }
                    if (btn) { btn.disabled = false; btn.textContent = 'Wait & Select'; }
                    self.showNotification('Timed out waiting for build', 'warning');
                });
                // Update fetch error message color/text
                const fetchErrBox = container.querySelector('.upgrade-fetch-error');
                if (fetchErrBox && rb) {
                    fetchErrBox.classList.add('upgrade-fetch-error--running');
                    fetchErrBox.textContent = `No completed builds yet -- build #${rb.build_number} is still running.`;
                }
            };
            inject(0);
        },

        _detectParentBranch(branch) {
            if (!branch) return null;
            const featureMatch = branch.match(/^feature\/(dev_v\d+[_\d]*)\/./);
            if (featureMatch) return featureMatch[1];
            const bugMatch = branch.match(/^(?:bugfix|hotfix|fix)\/(dev_v\d+[_\d]*)\/./);
            if (bugMatch) return bugMatch[1];
            const relMatch = branch.match(/^feature\/(rel_v\d+[_\d]*)\/./);
            if (relMatch) return relMatch[1];
            return null;
        },

        async openUpgradeWizard(opts) {
            const options = opts || {};
        
            const content = document.createElement('div');
            content.innerHTML = '<div class="scaler-loading">Loading devices...</div>';
            this.openPanel('upgrade-wizard', 'Image Upgrade Wizard', content, {
                width: '720px',
                parentPanel: 'scaler-menu'
            });
        
            try {
                const devices = this._getWizardDeviceListSync();
                if (devices.length === 0) {
                    content.innerHTML = '<div class="scaler-info-box" style="color:var(--dn-orange,#e67e22)">Add devices to the topology first. No devices on canvas.</div>';
                    return;
                }
        
                const deviceContexts = {};
                let deviceStatus = {};
                const _ctxFetchPromises = [];
                for (const d of devices) {
                    const cached = this._deviceContexts[d.id];
                    if (cached && (Date.now() - (cached._fetchedAt || 0)) < 600000) {
                        deviceContexts[d.id] = cached;
                    } else if (d._stackData?.components?.length) {
                        deviceContexts[d.id] = { stack: d._stackData.components, _fetchedAt: d._stackCachedAt || Date.now(), _fromMonitor: true };
                    } else {
                        deviceContexts[d.id] = {};
                    }
                    // Seed system_type from the canvas device first --
                    // monitor and prior deploys both write here, so a
                    // device that the operator never opened in the wizard
                    // before still gets a pre-fill instead of "sys-type?".
                    if (!deviceContexts[d.id].system_type) {
                        const _seed = this._sanitizeWizardSystemType(d.platform)
                            || this._sanitizeWizardSystemType(d._systemType)
                            || this._sanitizeWizardSystemType(d._deploySystemType)
                            || '';
                        if (_seed) deviceContexts[d.id].system_type = _seed;
                    }
                    // Non-SSH canvas nodes (e.g. "VRF-A CE", "VRF-A server") are
                    // illustrative topology labels, not real devices registered
                    // in the backend. Hitting /api/devices/<name>/context for
                    // them just returns 404 and pollutes the console. Skip the
                    // fetch for anything without SSH configured.
                    if (!deviceContexts[d.id].system_type && (d.hasSSH || d.ssh_host || d.ip)) {
                        const _did = d.id;
                        const _ssh = d.ssh_host || d.ip || '';
                        // Route through the orchestrator so three open
                        // wizards (or wizard + monitor + SSH dialog) all
                        // share a single SSH hit for this device within
                        // the TTL window.
                        const _ctxPromise = (typeof window !== 'undefined' && window.DeviceState && typeof window.DeviceState.getContext === 'function')
                            ? window.DeviceState.getContext(_did, { live: false, sshHost: _ssh })
                            : ScalerAPI.getDeviceContext(_did, false, _ssh);
                        _ctxFetchPromises.push(
                            _ctxPromise.then(ctx => {
                                // Accept `deploy_system_type` as a fallback
                                // when `system_type` came back empty -- this
                                // is the post-`request system delete` shape
                                // (operational.json reads "N/A" but the
                                // backend's resolver still has the chassis
                                // type from devices.json or a config
                                // backup). User report 2026-04-24:
                                // RR-SA-2 was painting red after delete
                                // even though the type was recoverable.
                                const _rawSt = ctx?.system_type || ctx?.deploy_system_type || '';
                                if (_rawSt) {
                                    const merged = { ...deviceContexts[_did], ...ctx, _fetchedAt: Date.now() };
                                    const cleanSt = this._sanitizeWizardSystemType(_rawSt);
                                    merged.system_type = cleanSt || '';
                                    if (ctx?.deploy_system_type) merged.deploy_system_type = ctx.deploy_system_type;
                                    deviceContexts[_did] = merged;
                                    this._deviceContexts[_did] = deviceContexts[_did];
                                } else if (ctx) {
                                    // Even when system_type was unresolvable
                                    // we still want to merge the rest of
                                    // the context (mode, stack hints, NCC
                                    // info). Without this branch the wizard
                                    // would lose every other field too.
                                    const merged = { ...deviceContexts[_did], ...ctx, _fetchedAt: Date.now() };
                                    delete merged.system_type;
                                    if (deviceContexts[_did].system_type) {
                                        merged.system_type = deviceContexts[_did].system_type;
                                    }
                                    deviceContexts[_did] = merged;
                                    this._deviceContexts[_did] = deviceContexts[_did];
                                }
                            }).catch(() => {})
                        );
                    }
                    if (d._stackData?.components?.length) {
                        const parsed = this._parseStackVersions(d._stackData.components);
                        const monitorMode = d._deviceMode || '';
                        deviceStatus[d.id] = {
                            mode: monitorMode,
                            dnos_ver: parsed.dnos !== '--' ? parsed.dnos : '',
                            gi_ver: parsed.gi !== '--' ? parsed.gi : '',
                            baseos_ver: parsed.baseos !== '--' ? parsed.baseos : '',
                            install_status: '',
                            _fromCache: true
                        };
                    }
                }
        
                const allIds = devices.map(d => d.id);
                const allSshHosts = {};
                devices.forEach(d => { if (d.ssh_host || d.ip) allSshHosts[d.id] = d.ssh_host || d.ip; });
        
                const _bgStatusFetch = ScalerAPI.getUpgradeDeviceStatus(allIds, allSshHosts, true).then(cachedResult => {
                    const cachedDevices = cachedResult.devices || {};
                    // Transient states only: these indicate the device is in the middle of an
                    // operation, so a stable canvas DNOS may be more accurate. Clean "GI" from
                    // operational.json, however, is an authoritative classification (already
                    // written by the backend from device_state) and must NOT be overridden --
                    // that was the bug where PE-4 displayed DNOS while actually in GI.
                    const _transientStates = ['BASEOS_SHELL', 'UPGRADING', 'DEPLOYING', 'ONIE'];
                    let changed = false;
                    for (const [did, st] of Object.entries(cachedDevices)) {
                        const dev = devices.find(x => x.id === did);
                        const canvasMode = ((dev && dev._deviceMode) || '').toUpperCase();
                        if (!deviceStatus[did] || !deviceStatus[did].dnos_ver) {
                            deviceStatus[did] = st;
                            changed = true;
                        } else {
                            if (st.install_status !== undefined) { deviceStatus[did].install_status = st.install_status; changed = true; }
                            // Accept any non-transient backend mode (including GI) -- operational.json
                            // is authoritative for stable states.
                            if (st.mode && !_transientStates.includes((st.mode || '').toUpperCase())) {
                                deviceStatus[did].mode = st.mode; changed = true;
                            }
                        }
                        // Only preserve canvas DNOS when the backend cache is in a transient state
                        // (mid-upgrade, shell, etc.). A stable GI from operational.json wins.
                        if (canvasMode === 'DNOS' && _transientStates.includes((deviceStatus[did]?.mode || '').toUpperCase())) {
                            deviceStatus[did].mode = 'DNOS'; changed = true;
                        }
                    }
                    if (changed && this.WizardController?.data) {
                        this.WizardController.data.deviceStatus = deviceStatus;
                        this.WizardController.render();
                    }
                }).catch(() => {});
        
                if (_ctxFetchPromises.length > 0) {
                    Promise.all(_ctxFetchPromises).then(() => {
                        if (this.WizardController?.data) {
                            this.WizardController.data.deviceContexts = deviceContexts;
                            this.WizardController.data._upgradePlan = null;
                            this.WizardController.render();
                        }
                    });
                }
        
                let preselectedIds = null;
                let skipToStep = 0;
                if (options.deviceId) {
                    const target = devices.find(d => d.id === options.deviceId || d.hostname === options.deviceId || d.label === options.deviceId);
                    if (target && target.hasSSH) {
                        preselectedIds = [target.id];
                        skipToStep = 1;
                    }
                }
        
                let runningUpgradeJob = null;
                this._findRunningUpgradeJob().then(j => {
                    if (j && this.WizardController?.data) {
                        this.WizardController.data._runningJob = j;
                        this.WizardController.render();
                    }
                }).catch(() => {});
        
                const self = this;
                const formatAge = (h) => this._formatUpgradeAge(h);
                const devicesWithSsh = devices.filter(d => d.hasSSH);
                const devicesNoSsh = devices.filter(d => !d.hasSSH);
                const RECENT_SOURCES_LIMIT = 12;
                const LEGACY_LAST_BRANCHES_KEY = 'scaler_upgrade_last_branches';
                const _recentSourceUsername = () => {
                    try {
                        const auth = window.TopologyAuth;
                        const u = auth && auth.getCurrentUser && auth.getCurrentUser();
                        const username = u && u.username ? String(u.username).trim() : '';
                        return username ? username.replace(/[^A-Za-z0-9_.@-]/g, '_') : 'anon';
                    } catch (_) {
                        return 'anon';
                    }
                };
                const _recentSourcesKey = () => `scaler_upgrade_recent_sources_${_recentSourceUsername()}`;
                const _decodeRecentText = (value) => {
                    let result = String(value || '');
                    for (let i = 0; i < 5 && result.includes('%'); i++) {
                        try {
                            const decoded = decodeURIComponent(result);
                            if (decoded === result) break;
                            result = decoded;
                        } catch (_) {
                            break;
                        }
                    }
                    return result;
                };
                const _normalizeBranch = (value) => {
                    const raw = String(value || '').trim();
                    if (!raw) return '';
                    if (!raw.startsWith('http')) return raw;
                    const classicM = raw.match(/\/job\/[^/]+\/job\/[^/]+\/job\/([^/]+)/);
                    const blueM = raw.match(/\/detail\/([^/]+)(?:\/(\d+))?/);
                    const branch = (classicM && classicM[1]) || (blueM && blueM[1]) || '';
                    return branch ? _decodeRecentText(branch) : raw;
                };
                const _normalizeSourceUrl = (value) => {
                    const raw = String(value || '').trim();
                    if (!raw) return '';
                    try {
                        const parsed = new URL(raw);
                        parsed.hash = '';
                        parsed.searchParams.sort();
                        return parsed.toString().replace(/\/$/, '');
                    } catch (_) {
                        return raw.replace(/\/$/, '');
                    }
                };
                const _shortRecentText = (value, maxLen = 48) => {
                    const text = _decodeRecentText(value || '');
                    if (text.length <= maxLen) return text;
                    return '...' + text.slice(-(maxLen - 3));
                };
                const _fileNameFromUrl = (url) => {
                    try {
                        const u = new URL(url);
                        const last = u.pathname.split('/').filter(Boolean).pop() || u.hostname;
                        return _decodeRecentText(last);
                    } catch (_) {
                        const parts = String(url || '').split('/').filter(Boolean);
                        return _decodeRecentText(parts.pop() || url || '');
                    }
                };
                const _componentListFromEntry = (entry) => {
                    if (Array.isArray(entry.components) && entry.components.length) return entry.components;
                    const build = entry.selectedBuild || {};
                    const out = [];
                    if (entry.dnosUrl || build.dnos_url) out.push('DNOS');
                    if (entry.giUrl || build.gi_url) out.push('GI');
                    if (entry.baseosUrl || build.baseos_url) out.push('BaseOS');
                    return out;
                };
                const _recentEntryKey = (entry) => {
                    const type = entry?.type || 'branch';
                    if (type === 'url') return `url:${_normalizeSourceUrl(entry.url || entry.branch || '')}`;
                    if (type === 'directUrls') {
                        return `direct:${[entry.dnosUrl || '', entry.giUrl || '', entry.baseosUrl || ''].map(v => String(v).trim()).join('|')}`;
                    }
                    return `branch:${_normalizeBranch(entry.branch || entry.name || '')}`;
                };
                const _normalizeRecentEntry = (entry) => {
                    if (!entry) return null;
                    if (typeof entry === 'string') {
                        const branch = _normalizeBranch(entry);
                        if (!branch) return null;
                        return { type: 'branch', branch, updatedAt: 0 };
                    }
                    const type = entry.type === 'manual' || entry.type === 'url' || entry.type === 'directUrls'
                        ? entry.type
                        : 'branch';
                    const now = Date.now();
                    if (type === 'url') {
                        const url = _normalizeSourceUrl(entry.url || entry._sourceUrl || entry.branch || '');
                        if (!url) return null;
                        const selectedBuild = entry.selectedBuild ? {
                            ...entry.selectedBuild,
                            dnos_url: entry.selectedBuild.dnos_url || entry.dnosUrl || '',
                            gi_url: entry.selectedBuild.gi_url || entry.giUrl || '',
                            baseos_url: entry.selectedBuild.baseos_url || entry.baseosUrl || '',
                        } : null;
                        return {
                            type,
                            url,
                            branch: _normalizeBranch(entry.branch || '') || '',
                            buildNumber: entry.buildNumber || selectedBuild?.build_number || entry._resolvedBuildNumber || '',
                            displayName: entry.displayName || entry.name || '',
                            dnosUrl: entry.dnosUrl || selectedBuild?.dnos_url || '',
                            giUrl: entry.giUrl || selectedBuild?.gi_url || '',
                            baseosUrl: entry.baseosUrl || selectedBuild?.baseos_url || '',
                            selectedBuild,
                            isExpired: !!(entry.isExpired || entry.is_expired || selectedBuild?.is_expired),
                            isDraft: !!(entry.isDraft || entry.draft || entry.pending || !selectedBuild),
                            status: entry.status || (selectedBuild ? 'resolved' : 'pending'),
                            ageHours: entry.ageHours ?? entry.age_hours ?? selectedBuild?.age_hours,
                            components: entry.components || [],
                            updatedAt: Number(entry.updatedAt || entry.at || now),
                        };
                    }
                    if (type === 'directUrls') {
                        const dnosUrl = String(entry.dnosUrl || entry.dnos_url || '').trim();
                        const giUrl = String(entry.giUrl || entry.gi_url || '').trim();
                        const baseosUrl = String(entry.baseosUrl || entry.baseos_url || '').trim();
                        if (!dnosUrl && !giUrl && !baseosUrl) return null;
                        const selectedBuild = {
                            build_number: 'direct',
                            dnos_url: dnosUrl,
                            gi_url: giUrl,
                            baseos_url: baseosUrl,
                            has_dnos: !!dnosUrl,
                            has_gi: !!giUrl,
                            has_baseos: !!baseosUrl,
                            _urlsVerified: true,
                        };
                        return {
                            type,
                            dnosUrl,
                            giUrl,
                            baseosUrl,
                            selectedBuild,
                            displayName: entry.displayName || _fileNameFromUrl(dnosUrl || giUrl || baseosUrl),
                            components: entry.components || [],
                            updatedAt: Number(entry.updatedAt || entry.at || now),
                        };
                    }
                    const branch = _normalizeBranch(entry.branch || entry.name || '');
                    if (!branch) return null;
                    return {
                        type,
                        branch,
                        displayName: entry.displayName || '',
                        updatedAt: Number(entry.updatedAt || entry.at || now),
                    };
                };
                const _loadRecentSources = () => {
                    const seen = new Set();
                    const out = [];
                    const push = (entry) => {
                        const normalized = _normalizeRecentEntry(entry);
                        if (!normalized) return;
                        const key = _recentEntryKey(normalized);
                        if (!key || seen.has(key)) return;
                        seen.add(key);
                        out.push(normalized);
                    };
                    try {
                        const raw = localStorage.getItem(_recentSourcesKey());
                        const arr = raw ? JSON.parse(raw) : [];
                        if (Array.isArray(arr)) arr.forEach(push);
                    } catch (_) {}
                    try {
                        const legacy = JSON.parse(localStorage.getItem(LEGACY_LAST_BRANCHES_KEY) || '[]');
                        if (Array.isArray(legacy)) legacy.forEach(push);
                    } catch (_) {}
                    out.sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0));
                    return out.slice(0, RECENT_SOURCES_LIMIT);
                };
                const _saveRecentSources = (entries) => {
                    try {
                        localStorage.setItem(_recentSourcesKey(), JSON.stringify((entries || []).slice(0, RECENT_SOURCES_LIMIT)));
                    } catch (_) {}
                };
                const _branchRecentNames = (entries) => {
                    const seen = new Set();
                    return (entries || [])
                        .filter(e => (e.type === 'branch' || e.type === 'manual') && e.branch)
                        .map(e => e.branch)
                        .filter(b => {
                            if (seen.has(b)) return false;
                            seen.add(b);
                            return true;
                        });
                };
                const _recordRecentSource = (entry) => {
                    const normalized = _normalizeRecentEntry({ ...entry, updatedAt: Date.now() });
                    if (!normalized) return _loadRecentSources();
                    const key = _recentEntryKey(normalized);
                    const entries = _loadRecentSources().filter(e => _recentEntryKey(e) !== key);
                    entries.unshift(normalized);
                    _saveRecentSources(entries);
                    if (self.WizardController?.data) {
                        self.WizardController.data._recentSources = entries.slice(0, RECENT_SOURCES_LIMIT);
                        self.WizardController.data._lastUsedBranches = _branchRecentNames(entries);
                    }
                    return entries;
                };
                const _saveLastUsed = (branch, type = 'branch') => _recordRecentSource({ type, branch });
                this.WizardController.init({
                    panelName: 'upgrade-wizard',
                    quickNavKey: 'upgrade',
                    title: 'Image Upgrade Wizard',
                    initialData: {
                        devices,
                        deviceContexts,
                        deviceStatus,
                        selectedDeviceIds: preselectedIds || devicesWithSsh.map(d => d.id),
                        sourceType: 'browse',
                        branch: '',
                        branches: [],
                        builds: [],
                        selectedBuild: null,
                        components: ['DNOS', 'GI', 'BaseOS'],
                        upgradeType: 'normal',
                        _runningJob: runningUpgradeJob,
                    },
                    wizardHeader: (data) => {
                        const wrapper = document.createElement('div');
        
                        const rj = data._runningJob;
                        if (rj) {
                            const rjDevices = rj.devices || (rj.device_state ? Object.keys(rj.device_state) : []);
                            const rjName = rj.job_name || `Upgrading ${rjDevices.length} device${rjDevices.length !== 1 ? 's' : ''}`;
                            const rjSection = document.createElement('div');
                            rjSection.className = 'upgrade-running-section';
                            rjSection.innerHTML = `
                                <div class="upgrade-running-inner">
                                    <div class="upgrade-running-pulse"></div>
                                    <div class="upgrade-running-info">
                                        <div class="upgrade-running-title">Upgrade in progress</div>
                                        <div class="upgrade-running-detail">${self.escapeHtml(rjDevices.join(', '))} -- ${self.escapeHtml(rjName)}</div>
                                    </div>
                                    <button type="button" class="scaler-btn scaler-btn-sm upgrade-running-view-btn">View Progress</button>
                                </div>`;
                            rjSection.querySelector('.upgrade-running-view-btn').addEventListener('click', () => {
                                self.closePanel('upgrade-wizard');
                                const banner = document.getElementById('upgrade-active-banner');
                                if (banner) banner.remove();
                                self._showRunningUpgradeProgress(rj);
                            });
                            wrapper.appendChild(rjSection);
                        }
        
                        const allDevs = data.devices || [];
                        const devs = allDevs.filter(d => (data.selectedDeviceIds || []).includes(d.id));
                        if (devs.length === 0) return wrapper.children.length ? wrapper : null;
                        const hasStatus = data.deviceStatus && Object.keys(data.deviceStatus).length > 0;
                        const _giLikeModes = ['GI', 'BASEOS_SHELL', 'ONIE', 'DEPLOYING', 'RECOVERY', 'DN_RECOVERY'];
                        const rows = devs.map(d => {
                            const st = data.deviceStatus?.[d.id] || {};
                            const ctx = data.deviceContexts?.[d.id] || {};
                            const monitorStack = d._stackData?.components || [];
                            const ctxStack = Array.isArray(ctx.stack) ? ctx.stack : [];
                            const parsed = self._parseStackVersions(monitorStack.length ? monitorStack : ctxStack);
                            // Prefer live backend status (st.mode -- refreshed by Phase 2 live SSH)
                            // over the canvas monitor cache (d._deviceMode), which can lag behind
                            // when a device reboots into GI/BaseOS. Phase 2 is authoritative.
                            const mode = st.mode || d._deviceMode || ctx.mode || '';
                            const modeUpper = (mode || '').toUpperCase();
                            const isGiLike = _giLikeModes.includes(modeUpper);
                            // Ghost-IP: backend identity guard caught us landing on a
                            // different device at the stored mgmt IP. Suppress all
                            // "version/status" fields -- they belong to a stranger.
                            const isGhostIp = modeUpper === 'GHOST-IP';
                            const dnos = (isGiLike || isGhostIp) ? '--' : (st.dnos_ver || parsed.dnos);
                            const gi = (isGiLike || isGhostIp) ? '--' : (st.gi_ver || parsed.gi);
                            const baseos = (isGiLike || isGhostIp) ? '--' : (st.baseos_ver || parsed.baseos);
                            const _badgeCls = isGhostIp ? 'ghost-ip' : mode.toLowerCase();
                            const modeBadge = mode
                                ? `<span class="upgrade-mode-badge upgrade-mode-${_badgeCls}">${mode}</span>`
                                : '<span class="upgrade-mode-badge upgrade-mode-loading">...</span>';
                            const _isEmptyStack = isGiLike || isGhostIp || (monitorStack.length === 0 && ctxStack.length === 0
                                && dnos === '--' && gi === '--' && baseos === '--');
                            const _isUpgrading = !!(d._upgradeInProgress || d._activeUpgradeJob);
                            const shortVer = (v) => {
                                if (!v || v === '--') return '--';
                                const m = v.match(/^(\d+\.\d+\.\d+(?:\.\d+)?)/);
                                return m ? m[1] : (v.length > 18 ? v.slice(0, 16) + '..' : v);
                            };
                            const verCell = (v) => `<td class="upgrade-stack-ver" title="${(v || '--').replace(/"/g, '&quot;')}">${shortVer(v)}</td>`;
                            const hostname = d.hostname || d.id;
                            const installStatus = st.install_status || '';
                            let statusText;
                            if (isGhostIp) {
                                statusText = installStatus || 'Ghost IP: stored mgmt IP now belongs to another device';
                            } else if (isGiLike) {
                                statusText = (modeUpper === 'DEPLOYING' ? 'Deploying...' : `${mode} mode`);
                            } else {
                                statusText = installStatus;
                            }
                            const statusCell = hasStatus
                                ? `<td class="upgrade-stack-status">${statusText ? self.escapeHtml(statusText) : '--'}</td>`
                                : '';
                            if (_isEmptyStack) {
                                const emptyMsg = _isUpgrading
                                    ? 'Upgrading...'
                                    : (isGhostIp
                                        ? 'IP answers as a different device'
                                        : (isGiLike ? `${mode || 'GI'} -- no DNOS stack` : `Empty stack (${mode || 'unknown'})`));
                                const emptyColor = isGhostIp ? 'var(--dn-danger, #e74c3c)' : 'var(--dn-orange,#e67e22)';
                                return `<tr style="opacity:0.6"><td class="upgrade-stack-device">${hostname}</td><td>${modeBadge}</td><td colspan="3" style="text-align:center;font-style:italic;color:${emptyColor}">${emptyMsg}</td>${statusCell}</tr>`;
                            }
                            return `<tr><td class="upgrade-stack-device">${hostname}</td><td>${modeBadge}</td>${verCell(dnos)}${verCell(gi)}${verCell(baseos)}${statusCell}</tr>`;
                        }).join('');
                        const statusHeader = hasStatus ? '<th>Status</th>' : '';
                        const stackDiv = document.createElement('div');
                        stackDiv.className = 'device-context-panel';
                        stackDiv.innerHTML = `<div class="upgrade-stack-header">
                            <span class="upgrade-stack-title">Device Stack</span>
                            <button type="button" class="scaler-btn scaler-btn-sm" id="upgrade-ctx-refresh">Refresh</button>
                        </div>
                        <div class="upgrade-stack-table-wrap">
                            <table class="upgrade-stack-table"><thead><tr>
                                <th>Device</th><th>Mode</th><th>DNOS</th><th>GI</th><th>BaseOS</th>${statusHeader}
                            </tr></thead><tbody>${rows}</tbody></table>
                        </div>`;
                        const refreshBtn = stackDiv.querySelector('#upgrade-ctx-refresh');
                        if (refreshBtn) {
                            refreshBtn.addEventListener('click', async () => {
                                refreshBtn.disabled = true;
                                refreshBtn.textContent = 'Refreshing...';
                                const wd = self.WizardController.data;
                                const ids = wd.selectedDeviceIds || [];
                                const sshHosts = {};
                                allDevs.filter(d => ids.includes(d.id)).forEach(d => {
                                    sshHosts[d.id] = d.ssh_host || d.ip || '';
                                });
                                try {
                                    const statusResult = await ScalerAPI.getUpgradeDeviceStatus(ids, sshHosts);
                                    wd.deviceStatus = statusResult.devices || {};
                                } catch (e) {
                                    self.showNotification(`Refresh failed: ${e.message}`, 'warning');
                                }
                                self.WizardController.render();
                            });
                        }
                        wrapper.appendChild(stackDiv);
                        return wrapper;
                    },
                    wizardFooter: () => null,
                    steps: [
                        {
                            title: 'Devices',
                            render: (data) => {
                                const devs = data.devices || [];
                                const withSsh = devs.filter(d => d.hasSSH);
                                const noSsh = devs.filter(d => !d.hasSSH);
                                const status = data.deviceStatus || {};
                                const renderDev = (d, disabled) => {
                                    const ctx = data.deviceContexts?.[d.id] || {};
                                    const monStack = d._stackData?.components || [];
                                    const ctxStack = Array.isArray(ctx.stack) ? ctx.stack : [];
                                    const parsed = self._parseStackVersions(monStack.length ? monStack : ctxStack);
                                    const st = status[d.id] || {};
                                    const dnos = st.dnos_ver || parsed.dnos;
                                    const gi = st.gi_ver || parsed.gi;
                                    const baseos = st.baseos_ver || parsed.baseos;
                                    const ctxDevState = (ctx.device_state || '').toUpperCase();
                                    const monitorMode = d._deviceMode || '';
                                    // Backend status (st.mode) wins -- the canvas monitor cache can
                                    // be stale for minutes after a GI/BaseOS transition. Phase 2
                                    // live SSH populates st.mode authoritatively.
                                    const mode = st.mode || monitorMode || ctx.mode || self._classifyDeviceState(ctxDevState);
                                    const checked = (data.selectedDeviceIds || []).includes(d.id) ? 'checked' : '';
                                    const _badgeCls = ((mode || '').toUpperCase() === 'GHOST-IP') ? 'ghost-ip' : (mode || '').toLowerCase();
                                    const modeBadge = mode
                                        ? `<span class="upgrade-mode-badge upgrade-mode-${_badgeCls}">${mode}</span>`
                                        : '';
                                    const dnosBadge = mode
                                        ? ''
                                        : (dnos && dnos !== '--' ? `<span class="upgrade-dev-badge">DNOS</span>` : `<span class="upgrade-dev-badge upgrade-dev-badge--unknown">?</span>`);
                                    const summary = ctx?.config_summary || {};
                                    const asn = summary.as_number || '';
                                    const rid = summary.router_id || '';
                                    const ifaces = ctx?.interfaces || {};
                                    const subifCount = Array.isArray(ifaces.subinterface) ? ifaces.subinterface.length : 0;
                                    const bundleCount = Array.isArray(ifaces.bundle) ? ifaces.bundle.length : 0;
                                    const loCount = Array.isArray(ifaces.loopback) ? ifaces.loopback.length : 0;
                                    const hasDetail = dnos || gi || baseos || asn || subifCount || bundleCount;
                                    const detailItems = [];
                                    if (dnos && dnos !== '--') detailItems.push(`<span class="upgrade-dev-detail-chip"><span class="upgrade-dev-detail-label">DNOS</span> ${dnos}</span>`);
                                    if (gi && gi !== '--') detailItems.push(`<span class="upgrade-dev-detail-chip"><span class="upgrade-dev-detail-label">GI</span> ${gi}</span>`);
                                    if (baseos && baseos !== '--') detailItems.push(`<span class="upgrade-dev-detail-chip"><span class="upgrade-dev-detail-label">BaseOS</span> ${baseos}</span>`);
                                    if (asn) detailItems.push(`<span class="upgrade-dev-detail-chip"><span class="upgrade-dev-detail-label">AS</span> ${asn}</span>`);
                                    if (rid) detailItems.push(`<span class="upgrade-dev-detail-chip"><span class="upgrade-dev-detail-label">RID</span> ${rid}</span>`);
                                    if (subifCount) detailItems.push(`<span class="upgrade-dev-detail-chip"><span class="upgrade-dev-detail-label">Sub-if</span> ${subifCount}</span>`);
                                    if (bundleCount) detailItems.push(`<span class="upgrade-dev-detail-chip"><span class="upgrade-dev-detail-label">Bundle</span> ${bundleCount}</span>`);
                                    const ip = d.ssh_host || d.ip || '';
                                    if (ip) detailItems.push(`<span class="upgrade-dev-detail-chip"><span class="upgrade-dev-detail-label">SSH</span> ${ip}</span>`);
                                    return `<div class="upgrade-dev-row${disabled ? ' upgrade-dev-row--disabled' : ''}" data-device-id="${d.id}">
                                        <div class="upgrade-dev-header">
                                            <label class="upgrade-dev-check"><input type="checkbox" value="${d.id}" ${checked}${disabled ? ' disabled' : ''}></label>
                                            <span class="upgrade-dev-name">${d.hostname || d.id}</span>
                                            ${dnosBadge}${modeBadge}
                                            <span class="upgrade-dev-ver">(DNOS ${dnos || '-'})</span>
                                            ${hasDetail && !disabled ? '<button type="button" class="upgrade-dev-expand" title="Show device details">+</button>' : ''}
                                        </div>
                                        ${hasDetail && !disabled ? `<div class="upgrade-dev-detail" style="display:none">
                                            <div class="upgrade-dev-detail-chips">${detailItems.join('')}</div>
                                        </div>` : ''}
                                    </div>`;
                                };
                                const recoveryDevs = withSsh.filter(d => (status[d.id]?.mode || '').toUpperCase() === 'RECOVERY');
                                const recoveryPanel = recoveryDevs.length ? `<div class="upgrade-recovery-panel">
                                    <label class="upgrade-recovery-label">${recoveryDevs.length} device(s) in Recovery mode</label>
                                    <div class="upgrade-recovery-devices">${recoveryDevs.map(d => d.hostname || d.id).join(', ')}</div>
                                    <div class="upgrade-recovery-actions">
                                        <button type="button" class="scaler-btn scaler-btn-sm" id="upgrade-recovery-restore">System Restore</button>
                                        <button type="button" class="scaler-btn scaler-btn-sm" id="upgrade-recovery-diagnostic">Run Diagnostic</button>
                                    </div>
                                </div>` : '';
                                const noSshMsg = withSsh.length === 0 && noSsh.length > 0
                                    ? '<div class="upgrade-no-ssh-guidance">No devices have SSH configured. Right-click a device on the canvas and set SSH host/IP to continue.</div>'
                                    : '';
                                return `<div class="scaler-form">
                                    <div class="scaler-form-group">
                                        <label>Devices</label>
                                        ${noSshMsg}
                                        <div id="upgrade-devices" class="scaler-checkbox-list">
                                            ${withSsh.map(d => renderDev(d, false)).join('')}
                                            ${noSsh.length ? `<div class="scaler-device-select-separator">No SSH configured</div>${noSsh.map(d => renderDev(d, true)).join('')}` : ''}
                                        </div>
                                    </div>
                                    ${recoveryPanel}
                                </div>`;
                            },
                            afterRender: (data) => {
                                const _getSelectedIds = () => self._getCheckedDeviceIds('upgrade-devices');
                                const _getSshHosts = (ids) => {
                                    const hosts = {};
                                    (data.devices || []).filter(d => ids.includes(d.id)).forEach(d => { hosts[d.id] = d.ssh_host || d.ip || ''; });
                                    return hosts;
                                };
                                document.querySelectorAll('.upgrade-dev-expand').forEach(btn => {
                                    btn.addEventListener('click', (e) => {
                                        e.preventDefault();
                                        e.stopPropagation();
                                        const row = btn.closest('.upgrade-dev-row');
                                        const detail = row?.querySelector('.upgrade-dev-detail');
                                        if (!detail) return;
                                        const showing = detail.style.display !== 'none';
                                        detail.style.display = showing ? 'none' : 'block';
                                        btn.textContent = showing ? '+' : '-';
                                        row.classList.toggle('upgrade-dev-row--expanded', !showing);
                                    });
                                });
                                const restoreBtn = document.getElementById('upgrade-recovery-restore');
                                const diagBtn = document.getElementById('upgrade-recovery-diagnostic');
                                if (restoreBtn) {
                                    restoreBtn.onclick = () => self.showNotification('System Restore: use scaler CLI or Batch Operations', 'info');
                                }
                                if (diagBtn) {
                                    diagBtn.onclick = async () => {
                                        const recoveryIds = (data.devices || []).filter(d => (data.deviceStatus?.[d.id]?.mode || '').toUpperCase() === 'RECOVERY').map(d => d.id);
                                        if (recoveryIds.length === 0) return;
                                        diagBtn.disabled = true; diagBtn.textContent = 'Running...';
                                        try {
                                            const resp = await fetch((typeof ScalerAPI !== 'undefined' && ScalerAPI._api ? ScalerAPI._api('/api/operations/diagnose-recovery') : '/api/operations/diagnose-recovery'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ device_ids: recoveryIds }) });
                                            const result = resp.ok ? await resp.json() : { error: await resp.text() };
                                            self.showNotification(result.output ? 'Diagnostic complete' : (result.error || 'Diagnostic failed'), result.error ? 'error' : 'info');
                                        } catch (e) { self.showNotification('Diagnostic failed: ' + e.message, 'error'); }
                                        finally { diagBtn.disabled = false; diagBtn.textContent = 'Run Diagnostic'; }
                                    };
                                }
                                if (!data.deviceStatus || Object.keys(data.deviceStatus).length === 0) {
                                    const ids = _getSelectedIds();
                                    if (ids.length > 0) {
                                        ScalerAPI.getUpgradeDeviceStatus(ids, _getSshHosts(ids)).then(result => {
                                            self.WizardController.data.deviceStatus = result.devices || {};
                                            self.WizardController.render();
                                        }).catch(e => {
                                            self.showNotification(`Device status check failed: ${e.message}`, 'warning');
                                        });
                                    }
                                }
                            },
                            collectData: () => ({
                                selectedDeviceIds: self._getCheckedDeviceIds('upgrade-devices')
                            }),
                            validate: (data) => {
                                const ids = data.selectedDeviceIds || [];
                                if (ids.length === 0) {
                                    self.showNotification('Select at least one device with SSH configured', 'warning');
                                    return false;
                                }
                                return true;
                            }
                        },
                        {
                            title: 'Source',
                            render: (data) => {
                                const st = data.sourceType || 'browse';
                                const branch = data.branch || '';
                                const recentSources = Array.isArray(data._recentSources) ? data._recentSources : _loadRecentSources();
                                data._recentSources = recentSources;
                                data._lastUsedBranches = _branchRecentNames(recentSources);
                                const lastUsed = data._lastUsedBranches || [];
                                const bbt = data._branchesByType || {};
                                const hasBranches = (bbt.dev?.length || bbt.release?.length || bbt.feature?.length);
                                const branchesLoaded = !!data._branchesByType;
                                const _decodeBranch = (s) => {
                                    let r = s;
                                    for (let i = 0; i < 5 && r.includes('%'); i++) {
                                        const d = decodeURIComponent(r);
                                        if (d === r) break;
                                        r = d;
                                    }
                                    return r;
                                };
                                const renderBranchChips = (arr, name) => {
                                    if (!arr || !arr.length) return '';
                                    return arr.map(b => {
                                        const n = typeof b === 'string' ? b : (b.name || b);
                                        const sel = data.branch || branch;
                                        const active = n === sel ? ' upgrade-chip--active' : '';
                                        const display = _decodeBranch(n);
                                        return `<button type="button" class="upgrade-chip${active}" data-branch="${self.escapeHtml(n)}" data-group="${name}" title="${self.escapeHtml(n)}">${self.escapeHtml(display)}</button>`;
                                    }).join('');
                                };
                                const _colState = data._sectionCollapsed || {};
                                const _sums = data._branchSummaries || {};
                                const _fmtAge = (h) => { if (!h && h !== 0) return '--'; if (h < 1) return `${Math.round(h*60)}m`; if (h < 24) return `${Math.round(h)}h`; return `${(h/24).toFixed(1)}d`; };
                                const _fmtSeen = (ts) => {
                                    if (!ts) return '--';
                                    const ageMs = Math.max(0, Date.now() - Number(ts));
                                    const mins = Math.round(ageMs / 60000);
                                    if (mins < 1) return 'now';
                                    if (mins < 60) return `${mins}m ago`;
                                    const hrs = Math.round(mins / 60);
                                    if (hrs < 24) return `${hrs}h ago`;
                                    return `${Math.round(hrs / 24)}d ago`;
                                };
                                const _typeBadge = (type) => {
                                    const label = type === 'manual' ? 'Manual' : (type === 'url' ? 'URL' : (type === 'directUrls' ? 'Direct' : 'Branch'));
                                    return `<span class="upgrade-build-count" style="font-size:10px;padding:1px 6px;margin-right:6px">${label}</span>`;
                                };
                                const _componentsHtml = (entry) => {
                                    const comps = _componentListFromEntry(entry);
                                    const text = comps.length ? comps.join(' / ') : '--';
                                    const expired = entry.isExpired || entry.selectedBuild?.is_expired;
                                    const cls = expired ? 'upgrade-build-fail' : (comps.length ? 'upgrade-build-ok' : '');
                                    const suffix = expired ? ' | Expired' : '';
                                    return cls ? `<span class="${cls}">${self.escapeHtml(text + suffix)}</span>` : self.escapeHtml(text);
                                };
                                const renderRecentRows = () => {
                                    if (!recentSources.length) return '';
                                    const rows = recentSources.map((entry, idx) => {
                                        const type = entry.type || 'branch';
                                        const isBranchLike = type === 'branch' || type === 'manual';
                                        const n = _normalizeBranch(entry.branch || entry.name || '');
                                        const display = isBranchLike
                                            ? _decodeBranch(n)
                                            : (entry.displayName || entry.branch || entry.url || _fileNameFromUrl(entry.dnosUrl || entry.giUrl || entry.baseosUrl || ''));
                                        const short = _shortRecentText(display, 54);
                                        const activeBranch = isBranchLike && data.branch === n;
                                        const activeUrl = type === 'url' && data._sourceUrl && _normalizeSourceUrl(data._sourceUrl) === entry.url;
                                        const sel = (activeBranch || activeUrl) ? ' upgrade-recent-row--active' : '';
                                        const sum = isBranchLike ? _sums[n] : null;
                                        let buildCell = '<span class="upgrade-recent-loading">...</span>';
                                        let validCell = '<span class="upgrade-recent-loading">...</span>';
                                        let ageCell = '';
                                        let rowDimClass = '';
                                        if (!isBranchLike) {
                                            const buildNum = entry.buildNumber || entry.selectedBuild?.build_number || '';
                                            buildCell = buildNum ? `<span class="upgrade-recent-build">#${self.escapeHtml(String(buildNum))}</span>` : `<span class="upgrade-build-warn">${entry.isDraft || entry.status === 'pending' ? 'Pending' : 'Saved source'}</span>`;
                                            validCell = _componentsHtml(entry);
                                            ageCell = _fmtSeen(entry.updatedAt);
                                            if (entry.isExpired || entry.selectedBuild?.is_expired) rowDimClass = ' upgrade-recent-row--expired';
                                        } else if (sum) {
                                            if (sum.latest) {
                                                const ok = sum.latest.result === 'SUCCESS';
                                                const building = sum.latest.result === 'BUILDING';
                                                const resultBadge = ok ? '<span class="upgrade-build-ok">[OK]</span>'
                                                    : (building ? '<span class="upgrade-build-warn">[...]</span>'
                                                    : '<span class="upgrade-build-fail">[FAIL]</span>');
                                                buildCell = `<span class="upgrade-recent-build">#${sum.latest.build_number} ${resultBadge}</span>`;
                                                const ageH = sum.latest.age_hours || 0;
                                                if (ageH > 48) {
                                                    ageCell = `<span class="upgrade-build-fail">${_fmtAge(ageH)}</span>`;
                                                } else if (ageH > 36) {
                                                    ageCell = `<span class="upgrade-build-warn">${_fmtAge(ageH)}</span>`;
                                                } else {
                                                    ageCell = _fmtAge(ageH);
                                                }
                                            } else {
                                                buildCell = '<span style="color:rgba(255,255,255,0.3)">No builds</span>';
                                                rowDimClass = ' upgrade-recent-row--dim';
                                            }
                                            if (sum.valid > 0) {
                                                validCell = `<span class="upgrade-build-ok">${sum.valid} valid</span>`;
                                            } else if (sum.latest) {
                                                validCell = '<span class="upgrade-build-fail">Expired</span>';
                                                rowDimClass = ' upgrade-recent-row--expired';
                                            } else {
                                                validCell = '<span style="color:rgba(255,255,255,0.3)">--</span>';
                                                rowDimClass = ' upgrade-recent-row--dim';
                                            }
                                        }
                                        const title = isBranchLike ? n : (entry.url || entry.dnosUrl || entry.displayName || display);
                                        return `<tr class="upgrade-recent-row${sel}${rowDimClass}" data-recent-index="${idx}">
                                            <td class="upgrade-recent-name" title="${self.escapeHtml(title)}">${_typeBadge(type)}${self.escapeHtml(short)}</td>
                                            <td class="upgrade-recent-build-cell">${buildCell}</td>
                                            <td class="upgrade-recent-valid-cell">${validCell}</td>
                                            <td class="upgrade-recent-age-cell">${ageCell}</td>
                                        </tr>`;
                                    }).join('');
                                    const sumsLoaded = Object.keys(_sums).length > 0;
                                    const validCount = sumsLoaded ? lastUsed.filter(b => { const s = _sums[typeof b === 'string' ? b : (b.name || b)]; return s && s.valid > 0; }).length : -1;
                                    const typedCount = recentSources.filter(e => e.type && e.type !== 'branch').length;
                                    const countLabel = validCount >= 0
                                        ? `<span class="upgrade-section-count">${recentSources.length}</span>${validCount > 0 ? ` <span class="upgrade-build-ok" style="font-size:0.8em;margin-left:4px">${validCount} branches with images</span>` : ''}${typedCount ? ` <span style="font-size:0.8em;margin-left:4px;opacity:0.75">${typedCount} saved inputs</span>` : ''}`
                                        : `<span class="upgrade-section-count">${recentSources.length}</span>${typedCount ? ` <span style="font-size:0.8em;margin-left:4px;opacity:0.75">${typedCount} saved inputs</span>` : ''}`;
                                    const _refreshing = data._branchSummariesRefreshing;
                                    return `<div class="upgrade-branch-group upgrade-branch-group--recent">
                                        <div class="upgrade-section-header" data-collapsible="lastused">
                                            <span class="upgrade-section-icon">${_colState.lastused ? '\u25B6' : '\u25BC'}</span>
                                            <span class="upgrade-section-label">Recent Activity</span>
                                            ${countLabel}
                                            <button class="scaler-btn scaler-btn-sm" id="upgrade-refresh-recents" title="Refresh build status for recent branch/manual rows" style="margin-left:8px;font-size:10px;padding:2px 8px;opacity:${_refreshing || !lastUsed.length ? '0.5' : '0.75'}" ${_refreshing || !lastUsed.length ? 'disabled' : ''}>${_refreshing ? 'Refreshing...' : 'Refresh'}</button>
                                        </div>
                                        <div class="upgrade-recent-table-wrap" id="upgrade-chips-lastused" ${_colState.lastused ? 'style="display:none"' : ''}>
                                            <table class="upgrade-recent-table"><thead><tr>
                                                <th>Source</th><th>Build / Name</th><th>Images</th><th>Age / Seen</th>
                                            </tr></thead><tbody>${rows}</tbody></table>
                                        </div>
                                    </div>`;
                                };
                                const renderSectionHeader = (key, label, count) => {
                                    const collapsed = _colState[key] !== false;
                                    return `<div class="upgrade-section-header" data-collapsible="${key}">
                                        <span class="upgrade-section-icon">${collapsed ? '\u25B6' : '\u25BC'}</span>
                                        <span class="upgrade-section-label">${label}</span>
                                        <span class="upgrade-section-count">${count}</span>
                                    </div>`;
                                };
                                return `<div class="scaler-form">
                                    <div class="upgrade-source-tabs">
                                        <button type="button" class="upgrade-source-tab${st === 'browse' ? ' active' : ''}" data-src="browse">Browse</button>
                                        <button type="button" class="upgrade-source-tab${st === 'manual' ? ' active' : ''}" data-src="manual">Manual</button>
                                        <button type="button" class="upgrade-source-tab${st === 'url' ? ' active' : ''}" data-src="url">URL</button>
                                        <button type="button" class="upgrade-source-tab${st === 'directUrls' ? ' active' : ''}" data-src="directUrls">Direct Images</button>
                                    </div>
                                    ${renderRecentRows()}
                                    <div class="upgrade-source-body">
                                        <div id="upgrade-src-browse" class="upgrade-src-pane" style="display:${st === 'browse' ? 'block' : 'none'}">
                                            ${hasBranches ? (() => {
                                                let html = '';
                                                if (bbt.release?.length) html += `<div class="upgrade-branch-group">${renderSectionHeader('release', 'Release', bbt.release.length)}<div class="upgrade-chip-grid${_colState.release !== false ? ' upgrade-chips-collapsed' : ''}" id="upgrade-chips-release">${renderBranchChips(bbt.release, 'release')}</div></div>`;
                                                if (bbt.dev?.length) html += `<div class="upgrade-branch-group">${renderSectionHeader('dev', 'Dev', bbt.dev.length)}<div class="upgrade-chip-grid${_colState.dev !== false ? ' upgrade-chips-collapsed' : ''}" id="upgrade-chips-dev">${renderBranchChips(bbt.dev, 'dev')}</div></div>`;
                                                if (bbt.feature?.length) html += `<div class="upgrade-branch-group">${renderSectionHeader('feature', 'Feature', bbt.feature.length)}<div class="upgrade-chip-grid${_colState.feature !== false ? ' upgrade-chips-collapsed' : ''}" id="upgrade-chips-feature">${renderBranchChips(bbt.feature, 'feature')}</div></div>`;
                                                return html;
                                            })() : (branchesLoaded
                                                ? '<div style="color:var(--dn-orange,#e67e22);font-size:0.9em;padding:8px 0">No branches found. Try the Manual tab or click Reload.<button class="scaler-btn scaler-btn-sm" id="upgrade-load-branches" style="margin-left:10px">Reload</button></div>'
                                                : '<div style="color:var(--dn-cloud,#ccc);font-size:0.9em;padding:8px 0">Loading branches...<button class="scaler-btn scaler-btn-sm" id="upgrade-load-branches" style="margin-left:10px">Load</button></div>')}
                                        </div>
                                        <div id="upgrade-src-manual" class="upgrade-src-pane" style="display:${st === 'manual' ? 'block' : 'none'}">
                                            <div class="scaler-form-group">
                                                <label>Branch name</label>
                                                <input type="text" id="upgrade-branch" class="scaler-input" value="${self.escapeHtml(branch)}" placeholder="e.g. main, release/21.1, 25.4.13.151_dev">
                                            </div>
                                        </div>
                                        <div id="upgrade-src-url" class="upgrade-src-pane" style="display:${st === 'url' ? 'block' : 'none'}">
                                            <div class="scaler-form-group">
                                                <label>Jenkins Build URL</label>
                                                <input type="text" id="upgrade-jenkins-url" class="scaler-input" placeholder="Paste Jenkins build URL" value="${self.escapeHtml(data._sourceUrl || (st === 'url' && branch.startsWith('http') ? branch : ''))}">
                                            </div>
                                        </div>
                                        <div id="upgrade-src-directUrls" class="upgrade-src-pane" style="display:${st === 'directUrls' ? 'block' : 'none'}">
                                            <div class="scaler-form-group">
                                                <label>Minio / Image URLs</label>
                                                <input type="text" id="upgrade-dnos-url" class="scaler-input" placeholder="DNOS image URL" value="${self.escapeHtml(data.dnosUrl || '')}" style="margin-bottom:6px">
                                                <input type="text" id="upgrade-gi-url" class="scaler-input" placeholder="GI URL (optional)" value="${self.escapeHtml(data.giUrl || '')}" style="margin-bottom:6px">
                                                <input type="text" id="upgrade-baseos-url" class="scaler-input" placeholder="BaseOS URL (optional)" value="${self.escapeHtml(data.baseosUrl || '')}">
                                            </div>
                                        </div>
                                    </div>
                                </div>`;
                            },
                            afterRender: async (data) => {
                                if (!Array.isArray(data._recentSources)) {
                                    self.WizardController.data._recentSources = _loadRecentSources();
                                    self.WizardController.data._lastUsedBranches = _branchRecentNames(self.WizardController.data._recentSources);
                                }
                                const panes = {
                                    browse: document.getElementById('upgrade-src-browse'),
                                    manual: document.getElementById('upgrade-src-manual'),
                                    url: document.getElementById('upgrade-src-url'),
                                    directUrls: document.getElementById('upgrade-src-directUrls'),
                                };
                                const showPane = (v) => {
                                    Object.entries(panes).forEach(([k, el]) => { if (el) el.style.display = k === v ? 'block' : 'none'; });
                                    document.querySelectorAll('.upgrade-source-tab').forEach(t => t.classList.toggle('active', t.dataset.src === v));
                                };
                                document.querySelectorAll('.upgrade-source-tab').forEach(tab => {
                                    tab.onclick = () => {
                                        const v = tab.dataset.src;
                                        const currentUrlInput = document.getElementById('upgrade-jenkins-url');
                                        if (currentUrlInput) {
                                            const currentUrl = currentUrlInput.value.trim();
                                            if (currentUrl) {
                                                self.WizardController.data._sourceUrl = currentUrl;
                                                if (self.WizardController.data.sourceType === 'url' && currentUrl.startsWith('http')) {
                                                    _recordRecentSource({ type: 'url', url: currentUrl, isDraft: true, status: 'pending' });
                                                }
                                            }
                                        }
                                        self.WizardController.data.sourceType = v;
                                        showPane(v);
                                    };
                                });
                                const urlInput = document.getElementById('upgrade-jenkins-url');
                                if (urlInput) {
                                    const persistUrlDraft = (renderAfter = false) => {
                                        const value = urlInput.value.trim();
                                        const wd = self.WizardController.data;
                                        if (!value) return;
                                        const previousUrl = wd._sourceUrl || '';
                                        wd.sourceType = 'url';
                                        wd._sourceUrl = value;
                                        if (value.startsWith('http') && previousUrl !== value) {
                                            wd.branch = value;
                                            wd._resolveUrl = true;
                                            wd._directUrls = false;
                                            wd.selectedBuild = null;
                                            wd.dnosUrl = '';
                                            wd.giUrl = '';
                                            wd.baseosUrl = '';
                                            wd.builds = [];
                                            wd._fetchAttempted = false;
                                            wd._fetchError = '';
                                            wd._upgradePlan = null;
                                        }
                                        if (value.startsWith('http')) {
                                            _recordRecentSource({
                                                type: 'url',
                                                url: value,
                                                branch: wd.branch && wd.branch !== value ? wd.branch : '',
                                                isDraft: true,
                                                status: 'pending',
                                            });
                                            if (renderAfter) {
                                                const cursorPos = urlInput.selectionStart || value.length;
                                                try { self.WizardController.render(); } catch (_) {}
                                                setTimeout(() => {
                                                    const nextInput = document.getElementById('upgrade-jenkins-url');
                                                    if (!nextInput) return;
                                                    nextInput.focus();
                                                    try { nextInput.setSelectionRange(cursorPos, cursorPos); } catch (_) {}
                                                }, 0);
                                            }
                                        }
                                    };
                                    urlInput.addEventListener('input', () => {
                                        persistUrlDraft(false);
                                        clearTimeout(self.WizardController.data._urlDraftTimer);
                                        self.WizardController.data._urlDraftTimer = setTimeout(() => persistUrlDraft(true), 700);
                                    });
                                    urlInput.addEventListener('change', () => persistUrlDraft(true));
                                    urlInput.addEventListener('blur', () => persistUrlDraft(false));
                                }
                                document.querySelectorAll('.upgrade-chip').forEach(chip => {
                                    chip.onclick = () => {
                                        document.querySelectorAll('.upgrade-chip').forEach(c => c.classList.remove('upgrade-chip--active'));
                                        chip.classList.add('upgrade-chip--active');
                                        self.WizardController.data.branch = chip.dataset.branch;
                                        _saveLastUsed(chip.dataset.branch);
                                    };
                                });
                                document.querySelectorAll('.upgrade-section-header[data-collapsible]').forEach(hdr => {
                                    hdr.style.cursor = 'pointer';
                                    hdr.onclick = () => {
                                        const key = hdr.dataset.collapsible;
                                        const grid = document.getElementById(`upgrade-chips-${key}`);
                                        if (!grid) return;
                                        const isHidden = grid.style.display === 'none' || grid.classList.contains('upgrade-chips-collapsed');
                                        if (isHidden) {
                                            grid.style.display = '';
                                            grid.classList.remove('upgrade-chips-collapsed');
                                        } else {
                                            grid.style.display = 'none';
                                            grid.classList.add('upgrade-chips-collapsed');
                                        }
                                        if (!self.WizardController.data._sectionCollapsed) self.WizardController.data._sectionCollapsed = {};
                                        self.WizardController.data._sectionCollapsed[key] = !isHidden;
                                        const icon = hdr.querySelector('.upgrade-section-icon');
                                        if (icon) icon.textContent = isHidden ? '\u25BC' : '\u25B6';
                                    };
                                });
                                document.querySelectorAll('.upgrade-recent-row').forEach(row => {
                                    row.style.cursor = 'pointer';
                                    row.onclick = () => {
                                        const idx = Number(row.dataset.recentIndex);
                                        const entry = (self.WizardController.data._recentSources || [])[idx];
                                        if (!entry) return;
                                        document.querySelectorAll('.upgrade-recent-row').forEach(r => r.classList.remove('upgrade-recent-row--active'));
                                        document.querySelectorAll('.upgrade-chip').forEach(c => c.classList.remove('upgrade-chip--active'));
                                        row.classList.add('upgrade-recent-row--active');
                                        const wd = self.WizardController.data;
                                        wd._fetchAttempted = false;
                                        wd._fetchError = '';
                                        wd._resolving = false;
                                        wd._planLoading = false;
                                        wd._upgradePlan = null;
                                        if (entry.type === 'url') {
                                            const build = entry.selectedBuild || null;
                                            wd.sourceType = 'url';
                                            wd.branch = build ? (entry.branch || entry.url || '') : (entry.url || entry.branch || '');
                                            wd._sourceUrl = entry.url || '';
                                            wd._resolveUrl = !build;
                                            wd._directUrls = !!build;
                                            wd.dnosUrl = entry.dnosUrl || build?.dnos_url || '';
                                            wd.giUrl = entry.giUrl || build?.gi_url || '';
                                            wd.baseosUrl = entry.baseosUrl || build?.baseos_url || '';
                                            wd.selectedBuild = build;
                                            wd.builds = [];
                                            showPane('url');
                                            const urlInput = document.getElementById('upgrade-jenkins-url');
                                            if (urlInput) urlInput.value = entry.url || '';
                                        } else if (entry.type === 'directUrls') {
                                            wd.sourceType = 'directUrls';
                                            wd.branch = '';
                                            wd._directUrls = true;
                                            wd.dnosUrl = entry.dnosUrl || '';
                                            wd.giUrl = entry.giUrl || '';
                                            wd.baseosUrl = entry.baseosUrl || '';
                                            wd.selectedBuild = entry.selectedBuild || {
                                                build_number: 'direct',
                                                dnos_url: wd.dnosUrl,
                                                gi_url: wd.giUrl,
                                                baseos_url: wd.baseosUrl,
                                                has_dnos: !!wd.dnosUrl,
                                                has_gi: !!wd.giUrl,
                                                has_baseos: !!wd.baseosUrl,
                                                _urlsVerified: true,
                                            };
                                            wd.builds = [];
                                            showPane('directUrls');
                                            const dnosInput = document.getElementById('upgrade-dnos-url');
                                            const giInput = document.getElementById('upgrade-gi-url');
                                            const baseosInput = document.getElementById('upgrade-baseos-url');
                                            if (dnosInput) dnosInput.value = wd.dnosUrl;
                                            if (giInput) giInput.value = wd.giUrl;
                                            if (baseosInput) baseosInput.value = wd.baseosUrl;
                                        } else {
                                            const type = entry.type === 'manual' ? 'manual' : 'browse';
                                            wd.sourceType = type;
                                            wd.branch = entry.branch || '';
                                            wd._directUrls = false;
                                            wd.selectedBuild = null;
                                            wd.builds = [];
                                            showPane(type);
                                            const branchInput = document.getElementById('upgrade-branch');
                                            if (branchInput) branchInput.value = wd.branch;
                                        }
                                        _recordRecentSource(entry);
                                    };
                                });
                                const _refreshSummaries = async (silent = false) => {
                                    const branches = self.WizardController?.data?._lastUsedBranches;
                                    if (!branches?.length) return;
                                    if (!silent) {
                                        self.WizardController.data._branchSummariesRefreshing = true;
                                        try { self.WizardController.render(); } catch (_) {}
                                    }
                                    try {
                                        const sums = await ScalerAPI.getBranchSummaries(branches);
                                        if (sums && Object.keys(sums).length > 0) {
                                            self.WizardController.data._branchSummaries = sums;
                                        } else {
                                            console.warn('[UpgradeWiz] Branch summaries returned empty -- keeping stale data');
                                        }
                                    } catch (err) {
                                        console.error('[UpgradeWiz] Branch summaries fetch failed:', err);
                                    }
                                    self.WizardController.data._branchSummariesRefreshing = false;
                                    try { self.WizardController.render(); } catch (_) {}
                                };
                                if (data._lastUsedBranches?.length && !data._branchSummariesLoaded) {
                                    self.WizardController.data._branchSummariesLoaded = true;
                                    _refreshSummaries(true);
                                } else if (data._lastUsedBranches?.length && !data._branchSummaryPollId) {
                                    _refreshSummaries(true);
                                }
                                document.getElementById('upgrade-refresh-recents')?.addEventListener('click', (e) => {
                                    e.stopPropagation();
                                    _refreshSummaries(false);
                                });
                                if (data._lastUsedBranches?.length && !data._branchSummaryPollId) {
                                    self.WizardController.data._branchSummaryPollId = setInterval(() => {
                                        if (document.querySelector('.upgrade-branch-group--recent')) {
                                            _refreshSummaries(true);
                                        } else {
                                            clearInterval(self.WizardController.data._branchSummaryPollId);
                                            self.WizardController.data._branchSummaryPollId = null;
                                        }
                                    }, 60000);
                                }
                                const loadBranches = async () => {
                                    if (self.WizardController.data._branchesLoading) return;
                                    self.WizardController.data._branchesLoading = true;
                                    try {
                                        const results = await Promise.allSettled([
                                            ScalerAPI.listBranches('dev'),
                                            ScalerAPI.listBranches('release'),
                                            ScalerAPI.listBranches('feature').catch(() => ({ branches: [] }))
                                        ]);
                                        const toArr = (r) => (r?.branches || []).map(b => typeof b === 'string' ? b : (b.name || b));
                                        const dev = results[0].status === 'fulfilled' ? results[0].value : {};
                                        const rel = results[1].status === 'fulfilled' ? results[1].value : {};
                                        const feat = results[2].status === 'fulfilled' ? results[2].value : {};
                                        self.WizardController.data._branchesByType = { dev: toArr(dev), release: toArr(rel), feature: toArr(feat) };
                                        self.WizardController.data._branchesLoading = false;
                                        self.WizardController.render();
                                    } catch (e) {
                                        self.WizardController.data._branchesLoading = false;
                                        self.showNotification(`Failed to load branches: ${e.message}`, 'error');
                                        self.WizardController.render();
                                    }
                                };
                                if (!data._branchesByType?.dev?.length && !data._branchesByType?.release?.length && !data._branchesByType?.feature?.length && !data._branchesLoading) {
                                    loadBranches();
                                }
                                document.getElementById('upgrade-load-branches')?.addEventListener('click', async () => {
                                    const btn = document.getElementById('upgrade-load-branches');
                                    if (btn) { btn.disabled = true; btn.textContent = 'Loading...'; }
                                    await loadBranches();
                                });
                            },
                            collectData: () => {
                                const st = document.querySelector('.upgrade-source-tab.active')?.dataset?.src || self.WizardController?.data?.sourceType || 'browse';
                                let branch = self.WizardController?.data?.branch || '';
                                if (st === 'manual') branch = document.getElementById('upgrade-branch')?.value?.trim() || '';
                                else if (st === 'browse') branch = self.WizardController?.data?.branch || '';
                                else if (st === 'url') {
                                    const u = document.getElementById('upgrade-jenkins-url')?.value?.trim() || '';
                                    if (u.startsWith('http')) {
                                        _recordRecentSource({
                                            type: 'url',
                                            url: u,
                                            branch: self.WizardController?.data?._sourceUrl === u ? self.WizardController?.data?.branch : '',
                                            dnosUrl: self.WizardController?.data?._sourceUrl === u ? self.WizardController?.data?.dnosUrl : '',
                                            giUrl: self.WizardController?.data?._sourceUrl === u ? self.WizardController?.data?.giUrl : '',
                                            baseosUrl: self.WizardController?.data?._sourceUrl === u ? self.WizardController?.data?.baseosUrl : '',
                                            selectedBuild: self.WizardController?.data?._sourceUrl === u ? self.WizardController?.data?.selectedBuild : null,
                                        });
                                        const existing = self.WizardController?.data || {};
                                        const reuseResolved = existing._sourceUrl === u && existing.selectedBuild && (existing.dnosUrl || existing.selectedBuild.dnos_url);
                                        return {
                                            sourceType: st,
                                            branch: reuseResolved ? (existing.branch || u) : u,
                                            _sourceUrl: u,
                                            _resolveUrl: !reuseResolved,
                                            _fetchAttempted: false,
                                            _fetchError: '',
                                            builds: [],
                                            selectedBuild: reuseResolved ? existing.selectedBuild : null,
                                            dnosUrl: reuseResolved ? (existing.dnosUrl || existing.selectedBuild.dnos_url || '') : '',
                                            giUrl: reuseResolved ? (existing.giUrl || existing.selectedBuild.gi_url || '') : '',
                                            baseosUrl: reuseResolved ? (existing.baseosUrl || existing.selectedBuild.baseos_url || '') : '',
                                            _directUrls: !!reuseResolved,
                                            _resolving: false,
                                            _planLoading: false,
                                            _upgradePlan: null
                                        };
                                    }
                                    branch = u;
                                }
                                else if (st === 'directUrls') {
                                    const dnosUrl = document.getElementById('upgrade-dnos-url')?.value?.trim() || '';
                                    const giUrl = document.getElementById('upgrade-gi-url')?.value?.trim() || '';
                                    const baseosUrl = document.getElementById('upgrade-baseos-url')?.value?.trim() || '';
                                    const selectedBuild = {
                                        build_number: 'direct',
                                        dnos_url: dnosUrl,
                                        gi_url: giUrl,
                                        baseos_url: baseosUrl,
                                        has_dnos: !!dnosUrl,
                                        has_gi: !!giUrl,
                                        has_baseos: !!baseosUrl,
                                        _urlsVerified: true,
                                    };
                                    if (dnosUrl) _recordRecentSource({ type: st, dnosUrl, giUrl, baseosUrl, selectedBuild });
                                    return {
                                        sourceType: st,
                                        dnosUrl, giUrl, baseosUrl,
                                        _directUrls: true,
                                        selectedBuild
                                    };
                                }
                                if (branch && st !== 'url') {
                                    _saveLastUsed(branch, st === 'manual' ? 'manual' : 'branch');
                                }
                                const prevBranch = self.WizardController?.data?.branch || '';
                                if (branch && branch !== prevBranch) {
                                    return { sourceType: st, branch, _fetchAttempted: false, _fetchError: '', builds: [], selectedBuild: null, _resolving: false, _planLoading: false, _upgradePlan: null };
                                }
                                return { sourceType: st, branch };
                            },
                            validate: (data) => {
                                const st = data.sourceType || 'browse';
                                if (st === 'manual' && !data.branch) { self.showNotification('Enter a branch name', 'warning'); return false; }
                                if (st === 'browse' && !data.branch) { self.showNotification('Select a branch', 'warning'); return false; }
                                if (st === 'url') {
                                    const urlSource = data._sourceUrl || data.branch || '';
                                    if (!urlSource.startsWith('http') && !(data._directUrls && data.selectedBuild)) { self.showNotification('Enter a Jenkins URL', 'warning'); return false; }
                                }
                                if (st === 'directUrls' && !data.dnosUrl) { self.showNotification('Enter at least DNOS URL', 'warning'); return false; }
                                return true;
                            }
                        },
                        {
                            title: 'Build',
                            skipIf: (data) => data._directUrls && data.selectedBuild,
                            navExtra: (data) => {
                                if (!data.branch) return '';
                                const _retH = (b) => b.is_qa ? 1440 : 48;
                                const blds = data.builds || [];
                                const allExp = blds.length > 0 && blds.every(b => Math.max(0, _retH(b) - b.age_hours) <= 0);
                                const open = data._triggerPanelOpen || allExp;
                                return `<button class="scaler-btn ${open ? 'scaler-btn-danger' : 'scaler-btn-secondary'}" id="upgrade-trigger-from-build" title="Trigger a new Jenkins build for this branch">${open ? 'Hide Trigger' : 'New Build'}</button>`;
                            },
                            render: (data) => {
                                const _decodeBr = (s) => { let r = s; for (let i = 0; i < 5 && r.includes('%'); i++) { const d = decodeURIComponent(r); if (d === r) break; r = d; } return r; };
                                const builds = data.builds || [];
                                const sel = data.selectedBuild;
                                const branch = data.branch || '';
                                const branchDisplay = _decodeBr(branch);
                                const resolving = data._resolving || false;
                                const rb = data._runningBuild;
                                // Debug info logged to console only
                                console.log(`[UpgradeWiz] render: rb=${rb ? '#' + rb.build_number : 'null'} chk=${data._runningBuildChecking ? 'Y' : 'N'} br=${(branch || '').slice(-30)}`);
                                const _rbText = rb ? (rb._justTriggered && !rb.build_number
                                    ? `Build queued${rb.flagStr} -- starting...`
                                    : `Build <strong>#${rb.build_number}</strong> is running${rb.flagStr} -- started ${rb.ageMin}m ago.`) : '';
                                const runningBannerHtml = rb ? `<div class="scaler-info-box" style="border-color:var(--dn-cyan,#00bcd4);color:var(--dn-cyan,#00bcd4);margin-bottom:8px;display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                                    <span>${_rbText}</span>
                                    <button class="scaler-btn scaler-btn-sm" id="upgrade-monitor-running" title="Open Running Commits panel to watch build logs">Monitor</button>
                                    <button class="scaler-btn scaler-btn-sm" id="upgrade-wait-running" title="Poll every 15s until build finishes, then auto-select it in this step">Wait & Select</button>
                                    <button class="scaler-btn scaler-btn-sm scaler-btn-primary" id="upgrade-wait-and-push" title="Start backend job that monitors this build and auto-upgrades all devices when it finishes">Wait & Upgrade</button>
                                </div>` : (data._runningBuildChecking ? '<div style="font-size:0.85em;color:var(--dn-cloud,#ccc);margin-bottom:8px">Checking for running builds...</div>' : '');
                                if (resolving || (builds.length === 0 && branch && !data._fetchAttempted)) {
                                    return `<div class="scaler-loading">Loading builds...
                                        <button class="scaler-btn scaler-btn-sm" id="upgrade-cancel-loading" style="margin-top:8px">Cancel</button>
                                    </div>${runningBannerHtml}`;
                                }
                                const fetchErr = data._fetchError || '';
                                const resolvedBuild = data._resolvedBuildNumber;
                                if (builds.length === 0) {
                                    const inclFailed = data._includeFailedBuilds || false;
                                    const shortBranch = branchDisplay.length > 60 ? '...' + branchDisplay.slice(-55) : branchDisplay;
                                    const expiredBuild = data._expiredBuild;
                                    const expiredMsg = expiredBuild ? `<div class="scaler-info-box" style="border-color:var(--dn-orange,#e67e22);color:var(--dn-orange,#e67e22);margin-bottom:8px">Build #${expiredBuild} is expired or has no artifacts. Showing latest builds from the branch.</div>` : '';
                                    return `<div class="scaler-form">
                                        <div class="scaler-info-box">Branch: <strong title="${self.escapeHtml(branch)}">${self.escapeHtml(shortBranch || '(not set)')}</strong>${resolvedBuild ? ` | Build: <strong>#${resolvedBuild}</strong>` : ''}</div>
                                        ${runningBannerHtml}
                                        ${expiredMsg}
                                        ${fetchErr ? `<div class="scaler-info-box upgrade-fetch-error${data._runningBuild ? ' upgrade-fetch-error--running' : ''}">${self.escapeHtml(fetchErr)}${data._suggestedParentBranch ? ` <button class="scaler-btn scaler-btn-sm" id="upgrade-switch-parent" style="margin-left:8px;vertical-align:middle">${self.escapeHtml(data._suggestedParentBranch)}</button>` : ''}</div>` : ''}
                                        <label class="scaler-checkbox-item" style="margin-bottom:8px"><input type="checkbox" id="upgrade-include-failed" ${inclFailed ? 'checked' : ''}> Include failed builds with valid images</label>
                                        <div class="upgrade-build-actions">
                                            <button class="scaler-btn scaler-btn-primary" id="upgrade-fetch-builds">Fetch builds</button>
                                        </div>
                                        <div id="upgrade-inline-trigger" style="display:${data._triggerPanelOpen ? 'block' : 'none'}">
                                            <div class="upgrade-inline-trigger-panel">
                                                <label>Trigger build for: <strong>${self.escapeHtml(shortBranch)}</strong></label>
                                                <div class="upgrade-trigger-options" style="margin:8px 0">
                                                    <label class="scaler-checkbox-item"><input type="checkbox" id="upgrade-inline-baseos" checked> Build BaseOS</label>
                                                    <label class="scaler-checkbox-item"><input type="checkbox" id="upgrade-inline-sanitizer"> Sanitizer</label>
                                                    <label class="scaler-checkbox-item" title="QA version -- 60-day retention on MinIO instead of 48h"><input type="checkbox" id="upgrade-inline-qa"> QA Version (60-day retention)</label>
                                                    <label class="scaler-checkbox-item" title="Auto-push images to selected devices when build succeeds"><input type="checkbox" id="upgrade-inline-autopush"> Auto-push to devices on success</label>
                                                </div>
                                                <button class="scaler-btn scaler-btn-primary" id="upgrade-inline-trigger-btn" style="width:100%">Trigger Build</button>
                                                <div id="upgrade-inline-trigger-status" style="margin-top:6px;font-size:0.85em"></div>
                                            </div>
                                        </div>
                                    </div>`;
                                }
                                const _retH = (b) => b.is_qa ? 1440 : 48;
                                const allExpired = builds.length > 0 && builds.every(b => Math.max(0, _retH(b) - b.age_hours) <= 0);
                                const validBuilds = builds.filter(b => Math.max(0, _retH(b) - b.age_hours) > 0);
                                const _compIcon = (has, valid) => has ? (valid ? '<span style="color:#27ae60">&#10003;</span>' : '<span style="opacity:0.35">&#10003;</span>') : '<span style="opacity:0.2">&mdash;</span>';
                                const rows = builds.map(b => {
                                    const retentionHrs = _retH(b);
                                    const remainHrs = Math.max(0, retentionHrs - b.age_hours);
                                    const valid = remainHrs > 0;
                                    let remainText;
                                    if (!valid) { remainText = '<span class="upgrade-build-fail">--</span>'; }
                                    else if (remainHrs < 1) { remainText = `<span class="upgrade-build-warn">${Math.round(remainHrs * 60)}m</span>`; }
                                    else if (remainHrs < 6) { remainText = `<span class="upgrade-build-warn">${Math.round(remainHrs)}h</span>`; }
                                    else if (remainHrs < 24) { remainText = `${Math.round(remainHrs)}h`; }
                                    else { remainText = `${(remainHrs / 24).toFixed(1)}d`; }
                                    const selClass = b.build_number === sel?.build_number ? ' upgrade-build-selected' : '';
                                    const dimClass = !valid ? ' upgrade-build-row--expired' : '';
                                    return `<tr class="upgrade-build-row${selClass}${dimClass}" data-build="${b.build_number}">
                                        <td>#${b.build_number}</td>
                                        <td style="text-align:center">${_compIcon(b.has_dnos, valid)}</td>
                                        <td style="text-align:center">${_compIcon(b.has_baseos, valid)}</td>
                                        <td style="text-align:center">${_compIcon(b.has_gi, valid)}</td>
                                        <td style="text-align:center">${b.is_sanitizer ? '<span style="color:var(--dn-orange,#e67e22)">S</span>' : '<span style="opacity:0.2">&mdash;</span>'}</td>
                                        <td>${formatAge(b.age_hours)}</td><td>${remainText}</td>
                                    </tr>`;
                                }).join('');
                                const inclFailed = data._includeFailedBuilds || false;
                                const shortBranchTbl = (() => { const b = branch; return b.length > 40 ? '...' + b.slice(-35) : b; })();
                                const triggerOpen = data._triggerPanelOpen || allExpired;
                                const triggerPanel = `<div id="upgrade-inline-trigger" class="upgrade-trigger-section" style="display:${triggerOpen ? 'block' : 'none'}">
                                    <div class="upgrade-inline-trigger-panel">
                                        <div class="upgrade-trigger-options">
                                            <label class="scaler-checkbox-item"><input type="checkbox" id="upgrade-inline-baseos" checked> BaseOS</label>
                                            <label class="scaler-checkbox-item"><input type="checkbox" id="upgrade-inline-sanitizer"> Sanitizer</label>
                                            <label class="scaler-checkbox-item" title="QA version -- 60-day retention on MinIO instead of 48h"><input type="checkbox" id="upgrade-inline-qa"> QA (60-day)</label>
                                            <label class="scaler-checkbox-item" title="Auto-push images to selected devices when build succeeds"><input type="checkbox" id="upgrade-inline-autopush"> Auto-push on success</label>
                                        </div>
                                        <button class="scaler-btn scaler-btn-primary" id="upgrade-inline-trigger-btn" style="width:100%;margin-top:6px">Trigger Build</button>
                                        <div id="upgrade-inline-trigger-status" style="margin-top:4px;font-size:0.85em"></div>
                                    </div>
                                </div>`;
                                return `<div class="scaler-form upgrade-build-step">
                                    ${runningBannerHtml}
                                    ${allExpired ? `<div class="upgrade-build-expired-cta">
                                        <strong>All builds expired</strong> <span style="opacity:0.7">(48h retention)</span>
                                        <span style="flex:1"></span>
                                        <span style="font-size:0.85em;opacity:0.7">Trigger a new build, then Wait &amp; Upgrade</span>
                                    </div>` : ''}
                                    <div class="upgrade-build-toolbar">
                                        <span class="upgrade-build-count">${validBuilds.length ? `${validBuilds.length} of ${builds.length} available` : `${builds.length} builds`}</span>
                                        <label class="scaler-checkbox-item" style="margin:0;font-size:0.85em"><input type="checkbox" id="upgrade-include-failed" ${inclFailed ? 'checked' : ''}> Show failed</label>
                                    </div>
                                    <table class="upgrade-build-table upgrade-build-table--compact">
                                        <thead><tr><th>Build</th><th style="text-align:center">DNOS</th><th style="text-align:center">BaseOS</th><th style="text-align:center">GI</th><th style="text-align:center">San.</th><th>Age</th><th>TTL</th></tr></thead>
                                        <tbody>${rows}</tbody>
                                    </table>
                                    <div id="upgrade-build-detail"></div>
                                    ${triggerPanel}
                                </div>`;
                            },
                            afterRender: (data) => {
                                const _setDirectBuild = (branch, buildNum, stack, extra) => {
                                    const selectedBuild = {
                                        build_number: buildNum,
                                        display_name: `#${buildNum}`,
                                        dnos_url: stack.dnos_url || '', gi_url: stack.gi_url || '', baseos_url: stack.baseos_url || '',
                                        is_sanitizer: extra?.is_sanitizer || false,
                                        result: extra?.result || 'SUCCESS',
                                        age_hours: extra?.age_hours || stack.age_hours || 0,
                                        is_expired: extra?.is_expired || stack.is_expired || false,
                                        _urlsVerified: true,
                                        has_dnos: !!stack.dnos_url, has_gi: !!stack.gi_url, has_baseos: !!stack.baseos_url,
                                    };
                                    self.WizardController.data.selectedBuild = selectedBuild;
                                    self.WizardController.data._directUrls = true;
                                    self.WizardController.data.dnosUrl = stack.dnos_url || '';
                                    self.WizardController.data.giUrl = stack.gi_url || '';
                                    self.WizardController.data.baseosUrl = stack.baseos_url || '';
                                    self.WizardController.data.branch = branch;
                                    self.WizardController.data._resolveUrl = false;
                                    self.WizardController.data._fetchAttempted = true;
                                    self.WizardController.data._resolving = false;
                                    const sourceUrl = self.WizardController.data._sourceUrl || (data.sourceType === 'url' && data.branch?.startsWith('http') ? data.branch : '');
                                    if (sourceUrl) {
                                        _recordRecentSource({
                                            type: 'url',
                                            url: sourceUrl,
                                            branch,
                                            buildNumber: buildNum,
                                            dnosUrl: stack.dnos_url || '',
                                            giUrl: stack.gi_url || '',
                                            baseosUrl: stack.baseos_url || '',
                                            selectedBuild,
                                            isExpired: selectedBuild.is_expired,
                                            ageHours: selectedBuild.age_hours,
                                        });
                                    } else if (branch) {
                                        _saveLastUsed(branch, data.sourceType === 'manual' ? 'manual' : 'branch');
                                    }
                                    self.WizardController.next();
                                };
                                const _extractBranchFromUrl = (url) => {
                                    const classicM = url.match(/\/job\/[^/]+\/job\/[^/]+\/job\/([^/]+)/);
                                    const blueM = url.match(/\/detail\/([^/]+)(?:\/(\d+))?/);
                                    const raw = (classicM && classicM[1]) || (blueM && blueM[1]) || '';
                                    if (!raw) return '';
                                    let decoded = raw;
                                    for (let i = 0; i < 5; i++) {
                                        try {
                                            const next = decodeURIComponent(decoded);
                                            if (next === decoded) break;
                                            decoded = next;
                                        } catch (_) { break; }
                                    }
                                    return decoded;
                                };
                                const fetchBuilds = async () => {
                                    let branch = data.branch || '';
                                    if (data._resolveUrl && branch.startsWith('http')) {
                                        const origUrl = branch;
                                        self.WizardController.data._resolving = true;
                                        self.WizardController.render();
                                        try {
                                            const r = await ScalerAPI.resolveJenkinsUrl(branch);
                                            if (r.branch) {
                                                branch = r.branch;
                                                self.WizardController.data.branch = branch;
                                            }
                                            self.WizardController.data._resolveUrl = false;
                                            self.WizardController.data._resolvedBuildNumber = r.build_number || null;
                                            if (r.build_number && r.dnos_url) {
                                                _setDirectBuild(branch, r.build_number, r, r);
                                                return;
                                            }
                                            if (r.build_number && branch) {
                                                try {
                                                    const stack = await ScalerAPI.getBuildStack(branch, r.build_number);
                                                    if (stack && stack.dnos_url) {
                                                        _setDirectBuild(branch, r.build_number, stack, r);
                                                        return;
                                                    }
                                                } catch (_) {}
                                                self.WizardController.data._expiredBuild = r.build_number;
                                            }
                                            if (r.error_detail) {
                                                self.WizardController.data._expiredBuild = r.build_number || true;
                                            }
                                        } catch (e) {
                                            self.WizardController.data._resolveUrl = false;
                                            const parsed = _extractBranchFromUrl(origUrl);
                                            if (parsed) {
                                                branch = parsed;
                                                self.WizardController.data.branch = branch;
                                            } else {
                                                self.WizardController.data._resolving = false;
                                                self.WizardController.data._fetchError = `Resolve failed: ${e.message}`;
                                                self.WizardController.data._fetchAttempted = true;
                                                self.WizardController.render();
                                                return;
                                            }
                                        }
                                        self.WizardController.data._resolving = false;
                                    } else if (branch.startsWith('http')) {
                                        const extracted = _extractBranchFromUrl(branch);
                                        if (extracted) {
                                            branch = extracted;
                                            self.WizardController.data.branch = branch;
                                            self.WizardController.data._resolveUrl = false;
                                        }
                                    }
                                    if (!branch) { self.showNotification('No branch selected', 'warning'); return; }
                                    self.WizardController.data._runningBuildCheckedBranch = branch;
                                    const inclFailed = document.getElementById('upgrade-include-failed')?.checked || false;
                                    self.WizardController.data._includeFailedBuilds = inclFailed;
                                    self.WizardController.data._fetchError = '';
                                    self.WizardController.data._resolving = true;
                                    self.WizardController.render();
                                    try {
                                        console.log('%c[UpgradeWiz] fetchBuilds: fetching builds for ' + branch, 'color:#ff9800');
                                        const _fetchTimeout = new Promise((_, rej) => setTimeout(() => rej(new Error('Request timed out after 30s')), 30000));
                                        const res = await Promise.race([ScalerAPI.getBuildsForBranch(branch, { include_failed: inclFailed }), _fetchTimeout]);
                                        self.WizardController.data.builds = res.builds || [];
                                        if (!self.WizardController.data.selectedBuild && self.WizardController.data.builds.length) {
                                            self.WizardController.data.selectedBuild = self.WizardController.data.builds[0];
                                        }
                                        self.WizardController.data._resolving = false;
                                        self.WizardController.data._fetchAttempted = true;
                                        console.log('%c[UpgradeWiz] fetchBuilds: got ' + (self.WizardController.data.builds.length) + ' builds, now checking running build...', 'color:#ff9800');
                                        let rb = null;
                                        try {
                                            const statusUrl = ScalerAPI._api(`/api/operations/image-upgrade/build-status/${encodeURIComponent(branch)}?latest=true&_t=${Date.now()}`);
                                            console.log('[UpgradeWiz] Running build check URL:', statusUrl);
                                            const statusResp = await fetch(statusUrl, { cache: 'no-store' });
                                            if (statusResp.ok) {
                                                const st = await statusResp.json();
                                                console.log('%c[UpgradeWiz] Build status response:', 'color:#00bcd4', JSON.stringify(st));
                                                if (st.building && st.build_number) {
                                                    const ageMin = Math.round((st.age_hours || 0) * 60);
                                                    const params = st.build_params || {};
                                                    const flags = [];
                                                    if (params.SHOULD_BUILD_BASEOS_CONTAINERS === 'Yes' || params.WITH_BASEOS === 'true' || params.with_baseos === 'true') flags.push('BaseOS');
                                                    if ((params.TESTS_TO_RUN && params.TESTS_TO_RUN.includes('ENABLE_SANITIZER')) || (params.TEST_NAMES && params.TEST_NAMES.includes('ENABLE_SANITIZER'))) flags.push('Sanitizer');
                                                    if (params.QA_VERSION === 'true' || params.QA_VERSION === true) flags.push('QA');
                                                    const flagStr = flags.length ? ` (${flags.join(', ')})` : '';
                                                    rb = { build_number: st.build_number, ageMin, flagStr, params, age_hours: st.age_hours };
                                                    self.WizardController.data._runningBuild = rb;
                                                    self.WizardController.data._runningBuildCheckedBranch = branch;
                                                    const tgtVer = self._extractVerForUpgrade(branch);
                                                    if (tgtVer) self.WizardController.data._targetVersion = tgtVer;
                                                    console.log('%c[UpgradeWiz] RUNNING BUILD #' + st.build_number + flagStr, 'color:#4caf50;font-weight:bold;font-size:14px');
                                                } else {
                                                    console.log('[UpgradeWiz] No running build: building=' + st.building + ' build_number=' + st.build_number);
                                                }
                                            } else {
                                                console.warn('[UpgradeWiz] Build status API returned ' + statusResp.status);
                                            }
                                        } catch (rbErr) {
                                            console.error('[UpgradeWiz] Running build check error:', rbErr);
                                        }
                                        if (!self.WizardController.data.builds.length) {
                                            if (rb) {
                                                self.WizardController.data._fetchError = `No completed builds yet -- build #${rb.build_number} is still running.`;
                                            } else {
                                                const _parentBranch = self._detectParentBranch(branch);
                                                if (_parentBranch) {
                                                    self.WizardController.data._fetchError = `No builds found -- branch may be merged. Try parent branch:`;
                                                    self.WizardController.data._suggestedParentBranch = _parentBranch;
                                                } else {
                                                    self.WizardController.data._fetchError = 'No builds found for this branch.';
                                                    self.WizardController.data._suggestedParentBranch = null;
                                                }
                                            }
                                        }
                                        // Auto-open trigger panel when all builds are expired and no running build
                                        const _blds = self.WizardController.data.builds || [];
                                        const _retH2 = (b) => b.is_qa ? 1440 : 48;
                                        const _allExp = _blds.length > 0 && _blds.every(b => Math.max(0, _retH2(b) - b.age_hours) <= 0);
                                        if (_allExp && !rb) {
                                            self.WizardController.data._triggerPanelOpen = true;
                                            self.WizardController.data.selectedBuild = null;
                                        }
                                        console.log('[UpgradeWiz] Final state: rb=' + (rb ? '#' + rb.build_number : 'null') + ' builds=' + self.WizardController.data.builds.length + ' allExpired=' + _allExp + ' error=' + (self.WizardController.data._fetchError || 'none'));
                                        self.WizardController.render();
                                    } catch (e) {
                                        console.error('[UpgradeWiz] fetchBuilds FAILED:', e);
                                        self.WizardController.data._resolving = false;
                                        self.WizardController.data._fetchAttempted = true;
                                        self.WizardController.data._fetchError = `Fetch failed: ${e.message}`;
                                        self.WizardController.render();
                                        self.showNotification(`Fetch failed: ${e.message}`, 'error');
                                    }
                                };
                                const fetchBtn = document.getElementById('upgrade-fetch-builds');
                                if (fetchBtn) {
                                    fetchBtn.onclick = () => {
                                        self.WizardController.data._fetchAttempted = false;
                                        self.WizardController.data._fetchError = '';
                                        fetchBuilds();
                                    };
                                }
                                document.getElementById('upgrade-switch-parent')?.addEventListener('click', () => {
                                    const parent = self.WizardController.data._suggestedParentBranch;
                                    if (!parent) return;
                                    self.WizardController.data.branch = parent;
                                    self.WizardController.data._suggestedParentBranch = null;
                                    self.WizardController.data._fetchAttempted = false;
                                    self.WizardController.data._fetchError = '';
                                    self.WizardController.data.builds = [];
                                    self.WizardController.data.selectedBuild = null;
                                    self.WizardController.data._runningBuild = null;
                                    self.WizardController.data._runningBuildCheckedBranch = null;
                                    fetchBuilds();
                                });
                                document.getElementById('upgrade-trigger-from-build')?.addEventListener('click', async function() {
                                    const panel = document.getElementById('upgrade-inline-trigger');
                                    if (!panel) return;
                                    const isHidden = panel.style.display === 'none';
                                    if (!isHidden) {
                                        panel.style.display = 'none';
                                        self.WizardController.data._triggerPanelOpen = false;
                                        this.textContent = 'New Build';
                                        this.classList.remove('scaler-btn-danger');
                                        this.classList.add('scaler-btn-secondary');
                                        return;
                                    }
                                    // Check for running build before showing trigger form
                                    const branch = data.branch || '';
                                    const statusArea = document.getElementById('upgrade-inline-trigger-status');
                                    if (branch) {
                                        this.disabled = true;
                                        this.textContent = 'Checking...';
                                        try {
                                            const st = await ScalerAPI.getUpgradeBuildStatus(branch, true);
                                            if (st.building && st.build_number) {
                                                const ageMin = Math.round((st.age_hours || 0) * 60);
                                                const params = st.build_params || {};
                                                const flags = [];
                                                if (params.SHOULD_BUILD_BASEOS_CONTAINERS === 'Yes' || params.WITH_BASEOS === 'true') flags.push('BaseOS');
                                                if ((params.TESTS_TO_RUN && params.TESTS_TO_RUN.includes('ENABLE_SANITIZER')) || params.TEST_NAMES?.includes('ENABLE_SANITIZER')) flags.push('Sanitizer');
                                                if (params.QA_VERSION === 'true' || params.QA_VERSION === true) flags.push('QA');
                                                const flagStr = flags.length ? ` (${flags.join(', ')})` : '';
                                                self.WizardController.data._runningBuild = { build_number: st.build_number, ageMin, flagStr, params, age_hours: st.age_hours };
                                                const tgtVer = self._extractVerForUpgrade(branch);
                                                if (tgtVer) self.WizardController.data._targetVersion = tgtVer;
                                                if (statusArea) statusArea.innerHTML = `<div class="scaler-info-box" style="border-color:var(--dn-orange,#e67e22);color:var(--dn-orange,#e67e22);margin-top:8px">
                                                    <strong>[WARN] Build #${st.build_number} is already running</strong> for this branch${flagStr} -- started ${ageMin}m ago.<br>
                                                    Triggering a new build will queue behind it or may be rejected by Jenkins.
                                                    <div style="margin-top:6px"><button class="scaler-btn scaler-btn-sm" id="upgrade-monitor-existing">Monitor existing build</button></div>
                                                </div>`;
                                                document.getElementById('upgrade-monitor-existing')?.addEventListener('click', () => {
                                                    self.openCommitsPanel?.();
                                                });
                                            }
                                        } catch (_) {}
                                        this.disabled = false;
                                    }
                                    panel.style.display = 'block';
                                    self.WizardController.data._triggerPanelOpen = true;
                                    this.textContent = 'Hide Trigger';
                                    this.classList.add('scaler-btn-danger');
                                    this.classList.remove('scaler-btn-secondary');
                                });
                                document.getElementById('upgrade-inline-trigger-btn')?.addEventListener('click', async () => {
                                    const branch = data.branch || '';
                                    if (!branch) return;
                                    const btn = document.getElementById('upgrade-inline-trigger-btn');
                                    const statusEl = document.getElementById('upgrade-inline-trigger-status');
                                    if (btn) { btn.disabled = true; btn.textContent = 'Triggering...'; }
                                    try {
                                        const autoPush = document.getElementById('upgrade-inline-autopush')?.checked ?? false;
                                        const selIds = data.selectedDeviceIds || [];
                                        const selDevs = (data.devices || []).filter(d => selIds.includes(d.id));
                                        const deviceIds = selDevs.map(d => d.id);
                                        const sshHosts = {};
                                        selDevs.forEach(d => {
                                            if (d.ssh_host || d.ip) sshHosts[d.id] = d.ssh_host || d.ip || '';
                                        });
                                        const opts = {
                                            with_baseos: document.getElementById('upgrade-inline-baseos')?.checked ?? true,
                                            with_sanitizer: document.getElementById('upgrade-inline-sanitizer')?.checked ?? false,
                                            qa_version: document.getElementById('upgrade-inline-qa')?.checked ?? false,
                                            auto_push: autoPush,
                                            device_ids: deviceIds,
                                            ssh_hosts: sshHosts,
                                        };
                                        const res = await ScalerAPI.triggerUpgradeBuild(branch, opts);
                                        const _db = (s) => { let r = s; for (let i = 0; i < 5 && r.includes('%'); i++) { const d = decodeURIComponent(r); if (d === r) break; r = d; } return r; };
                                        const displayBranch = _db(branch);
                                        if (res.success) {
                                            if (res.reused) {
                                                self.closePanel('upgrade-wizard');
                                                self.showProgress(res.job_id, `Build & Upgrade (${displayBranch.split('/').pop()})`, {
                                                    upgradeDevices: deviceIds,
                                                    upgradeSshHosts: sshHosts,
                                                });
                                                self.showNotification(
                                                    'Build already being monitored -- showing existing job',
                                                    'success');
                                            } else {
                                                if (res.job_id) {
                                                    try {
                                                        localStorage.setItem('scaler_upgrade_last_trigger',
                                                            JSON.stringify({ branch, jobId: res.job_id, at: Date.now() }));
                                                    } catch (_) {}
                                                }
                                                const tFlags = [];
                                                if (opts.with_baseos) tFlags.push('BaseOS');
                                                if (opts.with_sanitizer) tFlags.push('Sanitizer');
                                                if (opts.qa_version) tFlags.push('QA');
                                                const tFlagStr = tFlags.length ? ` (${tFlags.join(', ')})` : '';
                                                self.WizardController.data._runningBuild = {
                                                    build_number: null, ageMin: 0, flagStr: tFlagStr,
                                                    params: {}, age_hours: 0,
                                                    _justTriggered: true, _jobId: res.job_id,
                                                };
                                                self.WizardController.data._rbLastCheckTs = 0;
                                                self.WizardController.data._triggerPanelOpen = false;
        
                                                if (autoPush && deviceIds.length && res.job_id) {
                                                    self.closePanel('upgrade-wizard');
                                                    self.showProgress(res.job_id, `Build & Upgrade ${deviceIds.length} devices`, {
                                                        upgradeDevices: deviceIds,
                                                        upgradeSshHosts: sshHosts,
                                                    });
                                                    self.showNotification(
                                                        `Build triggered + auto-upgrade queued for ${deviceIds.length} device(s)`,
                                                        'success');
                                                } else {
                                                    if (statusEl) statusEl.innerHTML = `Build triggered -- use <strong>Wait &amp; Upgrade</strong> below`;
                                                    self.showNotification(
                                                        `Build triggered for ${displayBranch} -- use Wait & Upgrade to auto-upgrade when ready`,
                                                        'success', 6000);
                                                    self.WizardController.render();
                                                }
                                            }
                                        } else {
                                            if (statusEl) statusEl.textContent = res.message || 'Trigger returned no job';
                                        }
                                    } catch (e) {
                                        if (statusEl) statusEl.textContent = `Trigger failed: ${e.message}`;
                                    } finally {
                                        if (btn) { btn.disabled = false; btn.textContent = 'Trigger Build'; }
                                    }
                                });
                                document.getElementById('upgrade-cancel-loading')?.addEventListener('click', () => {
                                    self.WizardController.data._resolving = false;
                                    self.WizardController.data._fetchAttempted = true;
                                    self.WizardController.data._fetchError = 'Fetch cancelled.';
                                    self.WizardController.render();
                                });
                                if ((data.builds || []).length === 0 && data.branch && !data._resolving && !data._fetchAttempted) {
                                    fetchBuilds();
                                }
                                const _rbLastCheck = self.WizardController.data._rbLastCheckTs || 0;
                                const _rbCheckAge = Date.now() - _rbLastCheck;
                                if (data.branch && !data._resolving && _rbCheckAge > 10000) {
                                    self.WizardController.data._rbLastCheckTs = Date.now();
                                    (async () => {
                                        try {
                                            const br = data.branch;
                                            const url = ScalerAPI._api(`/api/operations/image-upgrade/build-status/${encodeURIComponent(br)}?latest=true&_t=${Date.now()}`);
                                            console.log('[UpgradeWiz] Running build check:', url);
                                            const resp = await fetch(url, { cache: 'no-store' });
                                            if (!resp.ok) { console.warn('[UpgradeWiz] build-status returned', resp.status); return; }
                                            const st = await resp.json();
                                            console.log('[UpgradeWiz] build-status result:', JSON.stringify({ building: st.building, build_number: st.build_number, age: st.age_hours }));
                                            if (st.building && st.build_number) {
                                                const ageMin = Math.round((st.age_hours || 0) * 60);
                                                const params = st.build_params || {};
                                                const flags = [];
                                                if (params.SHOULD_BUILD_BASEOS_CONTAINERS === 'Yes' || params.WITH_BASEOS === 'true') flags.push('BaseOS');
                                                if ((params.TESTS_TO_RUN && params.TESTS_TO_RUN.includes('ENABLE_SANITIZER')) || params.TEST_NAMES?.includes('ENABLE_SANITIZER')) flags.push('Sanitizer');
                                                if (params.QA_VERSION === 'true' || params.QA_VERSION === true) flags.push('QA');
                                                const flagStr = flags.length ? ` (${flags.join(', ')})` : '';
                                                const rb = { build_number: st.build_number, ageMin, flagStr, params, age_hours: st.age_hours };
                                                self.WizardController.data._runningBuild = rb;
                                                self.WizardController.data._runningBuildCheckedBranch = br;
                                                const tgtVer = self._extractVerForUpgrade(br);
                                                if (tgtVer) self.WizardController.data._targetVersion = tgtVer;
                                                console.log('%c[UpgradeWiz] BUILD RUNNING: #' + st.build_number + flagStr, 'color:#4caf50;font-weight:bold;font-size:14px');
                                                if (!self.WizardController.data.builds?.length) {
                                                    self.WizardController.data._fetchError = `No completed builds yet -- build #${rb.build_number} is still running.`;
                                                }
                                                self.WizardController.render();
                                            } else {
                                                self.WizardController.data._runningBuild = null;
                                            }
                                        } catch (err) {
                                            console.error('[UpgradeWiz] Running build check failed:', err);
                                        }
                                    })();
                                }
                                document.getElementById('upgrade-monitor-running')?.addEventListener('click', () => {
                                    self.openCommitsPanel?.();
                                });
                                document.getElementById('upgrade-wait-running')?.addEventListener('click', async () => {
                                    const rb = self.WizardController.data._runningBuild;
                                    if (!rb) return;
                                    const btn = document.getElementById('upgrade-wait-running');
                                    if (btn) { btn.disabled = true; btn.textContent = 'Waiting...'; }
                                    const branch = data.branch || '';
                                    const pollInterval = 15000;
                                    const maxPolls = 120;
                                    for (let i = 0; i < maxPolls; i++) {
                                        await new Promise(r => setTimeout(r, pollInterval));
                                        try {
                                            const st = await ScalerAPI.getUpgradeBuildStatus(branch, true);
                                            if (!st.building) {
                                                self.WizardController.data._runningBuild = null;
                                                self.WizardController.data._runningBuildCheckedBranch = null;
                                                self.WizardController.data._fetchAttempted = false;
                                                self.WizardController.render();
                                                self.showNotification(`Build #${rb.build_number} finished (${st.result || 'UNKNOWN'})`, st.result === 'SUCCESS' ? 'success' : 'warning');
                                                return;
                                            }
                                            const ageMin = Math.round((st.age_hours || 0) * 60);
                                            if (btn) btn.textContent = `Waiting... (${ageMin}m)`;
                                        } catch (_) {}
                                    }
                                    if (btn) { btn.disabled = false; btn.textContent = 'Wait & Select'; }
                                    self.showNotification('Timed out waiting for build', 'warning');
                                });
                                document.getElementById('upgrade-wait-and-push')?.addEventListener('click', async () => {
                                    const rb = self.WizardController.data._runningBuild;
                                    if (!rb) return;
                                    const btn = document.getElementById('upgrade-wait-and-push');
                                    if (btn) { btn.disabled = true; btn.textContent = 'Starting...'; }
        
                                    const wd = self.WizardController.data;
                                    const allDeviceIds = wd.selectedDeviceIds || [];
                                    const devicePlans = wd.device_plans || wd._upgradePlan?.devices || {};
                                    // PE-4 chassis identity guards. The CL-86
                                    // system_type and YOR_CL_PE-4 deploy_name
                                    // are immutable cluster facts -- the
                                    // DNOS deploy command syntactically
                                    // rejects anything else, so backfilling
                                    // them is safe. ncc_id is NOT immutable
                                    // (the cluster fails over during
                                    // `request system delete`); leaving it
                                    // unset forces the server-side trust
                                    // gate to require a fresh probe via
                                    // Re-detect rather than silently using
                                    // the legacy `pe4_deploy_default=1`
                                    // fallback that produced the 2026-05-12
                                    // stuck-in-GI incident.
                                    Object.keys(devicePlans).forEach(did => {
                                        const dev = (wd.devices || []).find(x => x.id === did) || {};
                                        const label = (dev.hostname || did || '').trim();
                                        if (!/^(YOR[_-]CL[_-])?PE[_-]?4$/i.test(label)) return;
                                        devicePlans[did].system_type = 'CL-86';
                                        devicePlans[did].is_cluster = true;
                                        devicePlans[did].deploy_params = devicePlans[did].deploy_params || {};
                                        devicePlans[did].deploy_params.system_type = 'CL-86';
                                        devicePlans[did].deploy_params.name = 'YOR_CL_PE-4';
                                        devicePlans[did].deploy_params.deploy_name = 'YOR_CL_PE-4';
                                    });
                                    const deviceIds = allDeviceIds.filter(did => (devicePlans[did]?.upgrade_type || 'normal') !== 'blocked');
                                    const components = wd.components || ['DNOS', 'GI', 'BaseOS'];
                                    const sshHosts = {};
                                    for (const d of (wd.devices || [])) {
                                        if (deviceIds.includes(d.id)) sshHosts[d.id] = d.ssh_host || d.ip || '';
                                    }
                                    if (deviceIds.length === 0) {
                                        self.showNotification('No devices to upgrade (all blocked/skipped)', 'warning');
                                        if (btn) { btn.disabled = false; btn.textContent = 'Wait & Upgrade'; }
                                        return;
                                    }
                                    // Active-NCC trust pre-flight (2026-05-12).
                                    // Mirrors the backend trust gate in
                                    // `image_upgrade_execute`; identical
                                    // doctrine to the Execute click handler.
                                    {
                                        const _WU_TRUST_PREFIXES = [
                                            'kvm_', 'virsh_console_verified',
                                            'pre_upgrade_snapshot', 'pre_upgrade_backup',
                                            'scaler_db_cache', 'topology_virsh_probe',
                                            'upgrade_start_snapshot', 'post_reboot_virsh_probe',
                                        ];
                                        const _isTrustedWU = (s) => {
                                            const v = String(s || '').trim();
                                            return !!v && _WU_TRUST_PREFIXES.some(p => v.startsWith(p));
                                        };
                                        const _wuUntrusted = [];
                                        for (const _did of deviceIds) {
                                            const _plan = devicePlans[_did] || {};
                                            const _type = String(_plan.upgrade_type || 'normal').toLowerCase();
                                            if (_type !== 'delete_deploy' && _type !== 'gi_deploy') continue;
                                            const _sys = String(_plan.system_type
                                                || _plan.deploy_params?.system_type || '').toUpperCase();
                                            const _isCluster = _plan.is_cluster || _sys.startsWith('CL-');
                                            if (!_isCluster) continue;
                                            const _src = String(_plan.active_ncc_source
                                                || _plan.deploy_params?.active_ncc_source || '').trim();
                                            if (!_isTrustedWU(_src)) {
                                                _wuUntrusted.push(`${_did} (active_ncc_source=${_src || 'empty'})`);
                                            }
                                        }
                                        if (_wuUntrusted.length > 0) {
                                            self.showNotification(
                                                `Refusing destructive Wait & Upgrade for cluster device(s): `
                                                + `${_wuUntrusted.join(', ')}. Click "Re-detect" in the device row `
                                                + `to refresh the Active-NCC probe, then retry. `
                                                + `(2026-05-12 trust gate.)`,
                                                'error', 12000);
                                            if (btn) { btn.disabled = false; btn.textContent = 'Wait & Upgrade'; }
                                            return;
                                        }
                                    }
                                    try {
                                        const result = await ScalerAPI.waitAndUpgrade({
                                            branch: wd.branch || '',
                                            build_number: rb.build_number,
                                            device_ids: deviceIds,
                                            ssh_hosts: sshHosts,
                                            device_plans: devicePlans,
                                            components: components,
                                            max_concurrent: wd.maxConcurrent ?? 3,
                                        });
                                        self.closePanel('upgrade-wizard');
                                        if (result.reused) {
                                            self.showNotification(
                                                'Wait & Upgrade already running for this branch -- showing existing job',
                                                'success');
                                        } else {
                                            try {
                                                localStorage.setItem('scaler_active_upgrade', JSON.stringify({
                                                    job_id: result.job_id, job_name: `Wait & Upgrade ${deviceIds.length} devices`,
                                                    devices: deviceIds, ssh_hosts: sshHosts, started_at: Date.now()
                                                }));
                                            } catch (_) {}
                                            const editor = window.topologyEditor;
                                            if (editor?.objects) {
                                                const upgradeSet = new Set(deviceIds);
                                                editor.objects.forEach(o => {
                                                    if (o.type === 'device' && upgradeSet.has(o.label?.trim())) o._upgradeInProgress = true;
                                                });
                                            }
                                        }
                                        self.showProgress(result.job_id, `Wait & Upgrade ${deviceIds.length} devices`, {
                                            upgradeDevices: deviceIds,
                                            upgradeSshHosts: sshHosts,
                                            onComplete: () => {
                                                const ed = window.topologyEditor;
                                                if (ed?.objects) {
                                                    ed.objects.forEach(o => { if (o.type === 'device') o._upgradeInProgress = false; });
                                                }
                                            }
                                        });
                                    } catch (e) {
                                        self.showNotification(`Wait & Upgrade failed: ${e.message}`, 'error');
                                        if (btn) { btn.disabled = false; btn.textContent = 'Wait & Upgrade'; }
                                    }
                                });
                                document.getElementById('upgrade-include-failed')?.addEventListener('change', (e) => {
                                    self.WizardController.data._includeFailedBuilds = e.target.checked;
                                    self.WizardController.data._fetchAttempted = false;
                                    fetchBuilds();
                                });
                                document.querySelectorAll('.upgrade-build-row').forEach(row => {
                                    row.onclick = () => {
                                        const bn = parseInt(row.dataset.build);
                                        const b = (self.WizardController.data.builds || []).find(x => x.build_number === bn);
                                        self.WizardController.data.selectedBuild = b || null;
                                        self.WizardController.data._urlCheckPending = true;
                                        self.WizardController.data._urlCheckResult = null;
                                        self.WizardController.render();
                                        if (b && !(b._urlsVerified)) {
                                            const branch = self.WizardController.data.branch || '';
                                            ScalerAPI.getBuildStack(branch, b.build_number).then(stack => {
                                                self.WizardController.data._urlCheckPending = false;
                                                const invalid = [];
                                                if (stack.url_status) {
                                                    for (const [k, v] of Object.entries(stack.url_status)) {
                                                        if (v && !v.valid) invalid.push(k.toUpperCase());
                                                    }
                                                }
                                                if ((!stack.dnos_url && !stack.gi_url && !stack.baseos_url) || invalid.length > 0) {
                                                    b._urlsExpired = true;
                                                    b._urlsVerified = true;
                                                    b._invalidComps = invalid;
                                                    self.WizardController.data._urlCheckResult = 'expired';
                                                    self.WizardController.data._triggerPanelOpen = true;
                                                    self.showNotification(
                                                        `Build #${b.build_number} images are no longer available${invalid.length ? ` (${invalid.join(', ')})` : ''}. Trigger a new build below.`,
                                                        'error', 6000);
                                                } else {
                                                    b._urlsExpired = false;
                                                    b._urlsVerified = true;
                                                    self.WizardController.data._urlCheckResult = 'valid';
                                                }
                                                self.WizardController.render();
                                            }).catch(() => {
                                                self.WizardController.data._urlCheckPending = false;
                                                self.WizardController.data._urlCheckResult = null;
                                                self.WizardController.render();
                                            });
                                        } else {
                                            self.WizardController.data._urlCheckPending = false;
                                        }
                                    };
                                });
                                const det = document.getElementById('upgrade-build-detail');
                                if (det && data.selectedBuild) {
                                    const sb = data.selectedBuild;
                                    const retHrs = sb.is_qa ? 1440 : 48;
                                    const remainHrs = Math.max(0, retHrs - (sb.age_hours || 0));
                                    const isExpiredAge = remainHrs <= 0 || sb.is_expired;
                                    const isExpiredUrl = sb._urlsExpired === true;
                                    const isExpired = isExpiredAge || isExpiredUrl;
                                    const parts = [`#${sb.build_number}`];
                                    if (sb.has_dnos) parts.push('DNOS');
                                    if (sb.has_gi) parts.push('GI');
                                    if (sb.has_baseos) parts.push('BaseOS');
                                    if (sb.is_sanitizer) parts.push('[S]');
                                    if (data._urlCheckPending) {
                                        det.innerHTML = `<div class="upgrade-build-detail-bar" style="opacity:0.7">
                                            ${parts.join(' / ')} -- <em>Verifying images...</em>
                                        </div>`;
                                    } else if (isExpired) {
                                        const reason = isExpiredUrl && !isExpiredAge
                                            ? 'Images purged from storage'
                                            : 'Expired';
                                        const comps = sb._invalidComps?.length ? ` (${sb._invalidComps.join(', ')})` : '';
                                        det.innerHTML = `<div class="upgrade-build-detail-bar upgrade-build-detail-bar--expired">
                                            ${parts.join(' / ')} -- <strong>${reason}${comps}</strong>. Configure and trigger a new build below.
                                        </div>`;
                                    } else {
                                        const ttl = remainHrs < 1 ? `${Math.round(remainHrs * 60)}m left` : `${Math.round(remainHrs)}h left`;
                                        const verified = sb._urlsVerified ? ' [images verified]' : '';
                                        det.innerHTML = `<div class="upgrade-build-detail-bar">
                                            ${parts.join(' / ')} -- ${ttl}${verified}
                                        </div>`;
                                    }
                                }
                            },
                            collectData: () => ({}),
                            validate: (data) => {
                                if (!data.selectedBuild) {
                                    self.showNotification('Select a build first, or wait for a running build to complete', 'warning');
                                    return false;
                                }
                                const sb = data.selectedBuild;
                                const retHrs = sb.is_qa ? 1440 : 48;
                                const remainHrs = Math.max(0, retHrs - (sb.age_hours || 0));
                                if (remainHrs <= 0 || sb.is_expired || sb._urlsExpired) {
                                    const reason = sb._urlsExpired
                                        ? 'images no longer available on storage'
                                        : 'images expired (48h retention)';
                                    self.showNotification(
                                        `Build #${sb.build_number}: ${reason}. Trigger a new build and use Wait & Upgrade.`,
                                        'error', 6000
                                    );
                                    data._triggerPanelOpen = true;
                                    self.WizardController.render();
                                    return false;
                                }
                                if (data._urlCheckPending) {
                                    self.showNotification('Image verification in progress -- please wait', 'warning');
                                    return false;
                                }
                                return true;
                            }
                        },
                        {
                            title: 'Compare',
                            render: (data) => {
                                const devs = (data.devices || []).filter(d => (data.selectedDeviceIds || []).includes(d.id));
                                const sb = data.selectedBuild;
                                const branch = data.branch || '';
                                const _cleanVer = (sb) => {
                                    if (!sb) return '--';
                                    const fromUrl = sb.dnos_url?.match(/(\d+\.\d+\.\d+(?:\.\d+)?)/);
                                    if (fromUrl) return fromUrl[1];
                                    const dn = sb.display_name || '';
                                    const vm = dn.match(/(\d+\.\d+\.\d+(?:\.\d+)?)/);
                                    if (vm) return vm[1];
                                    if (dn.startsWith('#')) return dn;
                                    return sb.build_number ? `#${sb.build_number}` : '--';
                                };
                                const rb = data._runningBuild;
                                const targetVer = _cleanVer(sb) || data._targetVersion || '--';
                                const targetGi = data._targetStack?.gi_version || '--';
                                const targetBase = data._targetStack?.baseos_version || '--';
                                const _extractMajor = (s) => { if (!s || s === '--') return 0; const m = s.match(/(\d+)\./); return m ? parseInt(m[1]) : 0; };
                                const _shortVer = (v) => { if (!v || v === '--') return '--'; const m = v.match(/^(\d+\.\d+\.\d+(?:\.\d+)?)/); return m ? m[1] : (v.length > 25 ? v.slice(0,22) + '..' : v); };
                                const targetLabel = branch ? branch.split('/').pop() : (sb ? `build #${sb.build_number}` : (rb ? `build #${rb.build_number} (running)` : '--'));
                                const _isGiMode = (d) => {
                                    const st = data.deviceStatus?.[d.id] || {};
                                    const ctx = data.deviceContexts?.[d.id] || {};
                                    const m = (st.mode || d._deviceMode || ctx.device_state || '').toUpperCase();
                                    return m === 'GI' || m === 'BASEOS_SHELL' || m === 'RECOVERY';
                                };
                                const cards = devs.map((d, i) => {
                                    const ctx = data.deviceContexts?.[d.id] || {};
                                    const monStack = d._stackData?.components || [];
                                    const ctxStack = Array.isArray(ctx.stack) ? ctx.stack : [];
                                    const parsed = self._parseStackVersions(monStack.length ? monStack : ctxStack);
                                    const curMaj = _extractMajor(parsed.dnos);
                                    const tgtMaj = _extractMajor(targetVer);
                                    const devInGi = _isGiMode(d);
                                    const isMajorJump = !devInGi && curMaj > 0 && tgtMaj > 0 && curMaj !== tgtMaj;
                                    const isDowngrade = !devInGi && curMaj > 0 && tgtMaj > 0 && curMaj > tgtMaj;
                                    const _bsDD = data._branchSwitch?.requires_delete_deploy;
                                    const _bsSwitch = data._branchSwitch?.is_switch;
                                    const jumpBadge = devInGi
                                        ? '<span class="upgrade-compare-badge upgrade-compare-badge--gi">GI Deploy</span>'
                                        : isMajorJump
                                            ? `<span class="upgrade-compare-badge upgrade-compare-badge--danger">v${curMaj} -> v${tgtMaj} ${isDowngrade ? 'DOWNGRADE' : 'MAJOR JUMP'}</span>`
                                            : (_bsDD || _bsSwitch)
                                                ? '<span class="upgrade-compare-badge upgrade-compare-badge--danger">BRANCH SWITCH</span>'
                                                : (curMaj > 0 && tgtMaj > 0 ? '<span class="upgrade-compare-badge upgrade-compare-badge--ok">Same major</span>' : '');
                                    const collapsed = i > 0 ? ' upgrade-compare-card--collapsed' : '';
                                    const _verRow = (label, cur, tgt) => {
                                        const changed = cur !== '--' && tgt !== '--' && cur !== tgt;
                                        return `<tr class="${changed ? 'upgrade-ver-changed' : ''}">
                                            <td class="upgrade-ver-label">${label}</td>
                                            <td class="upgrade-ver-cur">${_shortVer(cur)}</td>
                                            <td class="upgrade-ver-arrow">${changed ? '->' : '='}</td>
                                            <td class="upgrade-ver-tgt">${_shortVer(tgt)}</td>
                                        </tr>`;
                                    };
                                    return `<div class="upgrade-compare-card${collapsed}${isMajorJump ? ' upgrade-compare-card--jump' : ''}" data-device="${d.id}">
                                        <div class="upgrade-compare-card-header">
                                            <span class="upgrade-compare-device">${d.hostname || d.id}</span>
                                            ${jumpBadge}
                                            <span class="upgrade-compare-toggle">${i > 0 ? '+' : '-'}</span>
                                        </div>
                                        <div class="upgrade-compare-card-body">
                                            <table class="upgrade-ver-table">
                                                ${_verRow('DNOS', parsed.dnos, targetVer)}
                                                ${_verRow('GI', parsed.gi, targetGi)}
                                                ${_verRow('BaseOS', parsed.baseos, targetBase)}
                                            </table>
                                        </div>
                                    </div>`;
                                }).join('');
                                const jumpDevs = devs.filter(d => {
                                    if (_isGiMode(d)) return false;
                                    const ctx = data.deviceContexts?.[d.id] || {};
                                    const mon = d._stackData?.components || [];
                                    const ctxS = Array.isArray(ctx.stack) ? ctx.stack : [];
                                    const p = self._parseStackVersions(mon.length ? mon : ctxS);
                                    const cm = _extractMajor(p.dnos), tm = _extractMajor(targetVer);
                                    return cm > 0 && tm > 0 && cm !== tm;
                                });
                                const downDevs = jumpDevs.filter(d => {
                                    const ctx = data.deviceContexts?.[d.id] || {};
                                    const mon = d._stackData?.components || [];
                                    const ctxS = Array.isArray(ctx.stack) ? ctx.stack : [];
                                    const p = self._parseStackVersions(mon.length ? mon : ctxS);
                                    return _extractMajor(p.dnos) > _extractMajor(targetVer);
                                });
                                const giDevsList = devs.filter(d => _isGiMode(d));
                                const allGi = devs.length > 0 && giDevsList.length === devs.length;
                                let alertsHtml = '';
                                if (giDevsList.length > 0) {
                                    const giNames = giDevsList.map(d => d.hostname || d.id).join(', ');
                                    const giDetails = giDevsList.map(d => {
                                        const ctx = data.deviceContexts?.[d.id] || {};
                                        const rawSt = ctx.system_type || d.platform || '';
                                        const st = self._sanitizeWizardSystemType(rawSt) || '';
                                        const host = (d.hostname || d.id || '').trim();
                                        const isCl = st && st.toUpperCase().startsWith('CL-');
                                        const deployCmd = st ? `request system deploy system-type ${st} name ${host}` : '';
                                        const stBadge = st
                                            ? `<span style="display:inline-block;background:var(--dn-cyan,#00B4D8);color:#0a1628;font-weight:700;padding:2px 8px;border-radius:3px;font-size:12px;letter-spacing:0.3px">${self.escapeHtml(st)}</span>`
                                            : '<span style="display:inline-block;background:var(--dn-orange,#e67e22);color:#0a1628;font-weight:700;padding:2px 8px;border-radius:3px;font-size:11px">UNKNOWN -- select in Upgrade Plan</span>';
                                        const nccLine = isCl
                                            ? '<span style="font-size:11px;opacity:0.85">NCC auto-detected via NCM LLDP. Pin NCC in Upgrade Plan if needed.</span>'
                                            : '';
                                        return `<div style="margin-top:8px;padding:8px 10px;background:rgba(0,180,216,0.06);border-radius:4px;border-left:3px solid var(--dn-cyan,#00B4D8)">
                                            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap"><strong style="font-size:13px">${self.escapeHtml(host)}</strong>${stBadge}${isCl ? '<span style="font-size:10px;background:rgba(255,255,255,0.08);padding:1px 6px;border-radius:3px;opacity:0.75">CLUSTER</span>' : ''}</div>
                                            ${nccLine ? `<div style="margin-top:4px">${nccLine}</div>` : ''}
                                            ${deployCmd ? `<div style="margin-top:6px;padding:4px 8px;background:rgba(0,0,0,0.25);border-radius:3px;font-family:ui-monospace,monospace;font-size:11px;color:var(--dn-cyan,#00B4D8);word-break:break-all"><span style="opacity:0.5">$ </span>${self.escapeHtml(deployCmd)}</div>` : ''}
                                        </div>`;
                                    }).join('');
                                    alertsHtml += `<div class="upgrade-compare-alert upgrade-compare-alert--info">
                                        <div style="font-size:13px;font-weight:600;margin-bottom:6px">GI Mode -- Fresh Deploy</div>
                                        <div style="font-size:12px;opacity:0.85">GI loads images and runs deploy. Not an in-place DNOS upgrade.</div>
                                        ${giDetails}
                                    </div>`;
                                }
                                if (!allGi && data._branchSwitch) {
                                    const bs = data._branchSwitch;
                                    const _nonGiDevs = devs.filter(d => !_isGiMode(d));
                                    const _branchAffected = jumpDevs.length > 0 ? jumpDevs : _nonGiDevs;
                                    const affectedDevNames = _branchAffected.map(d => d.hostname || d.id).join(', ');
                                    const _giNote = giDevsList.length > 0
                                        ? ` <span style="opacity:0.65;font-size:0.88em">(${giDevsList.map(d => self.escapeHtml(d.hostname || d.id)).join(', ')} already in GI -- handled via Fresh Deploy above)</span>`
                                        : '';
                                    if (_branchAffected.length === 0) {
                                        alertsHtml = alertsHtml;
                                    } else if (bs.requires_delete_deploy && jumpDevs.length > 0) {
                                        alertsHtml += `<div class="upgrade-compare-alert upgrade-compare-alert--danger">
                                            <strong>[WARN] Major version jump detected</strong>
                                            <div style="margin-top:4px">Affected: <strong>${self.escapeHtml(affectedDevNames)}</strong>${_giNote}</div>
                                            <div style="margin-top:4px;font-size:0.9em">Delete-deploy required. All existing config on these devices will be erased and replaced. Back up configuration first.</div>
                                        </div>`;
                                    } else if (bs.requires_delete_deploy && bs.is_switch) {
                                        alertsHtml += `<div class="upgrade-compare-alert upgrade-compare-alert--danger">
                                            <strong>[WARN] Branch switch -- Delete+Deploy required</strong>
                                            <div style="margin-top:4px">${self.escapeHtml(bs.current_branch || '?')} -> ${self.escapeHtml(bs.target_branch || '?')}</div>
                                            <div style="margin-top:4px">Affected: <strong>${self.escapeHtml(affectedDevNames)}</strong>${_giNote}</div>
                                            <div style="margin-top:4px;font-size:0.9em">Switching between branches requires delete+deploy. Existing config will be erased and replaced. Back up configuration first.</div>
                                        </div>`;
                                    } else if (bs.is_switch) {
                                        alertsHtml += `<div class="upgrade-compare-alert upgrade-compare-alert--warn">
                                            <strong>[WARN] Branch switch</strong>
                                            <div style="margin-top:4px">${self.escapeHtml(bs.current_branch || '?')} -> ${self.escapeHtml(bs.target_branch || '?')}</div>
                                            <div style="margin-top:4px">Affected: <strong>${self.escapeHtml(affectedDevNames)}</strong>${_giNote}</div>
                                            <div style="margin-top:4px;font-size:0.9em">This changes the dev branch. Consider Delete+Deploy if config is incompatible.</div>
                                        </div>`;
                                    } else {
                                        alertsHtml += `<div class="upgrade-compare-alert upgrade-compare-alert--info"><strong>[OK] Same branch</strong> -- normal upgrade path.</div>`;
                                    }
                                } else if (!allGi && !data._compatReport) {
                                    alertsHtml += `<div class="upgrade-compare-alert upgrade-compare-alert--info" style="opacity:0.6">Analyzing version compatibility...</div>`;
                                }
                                if (!allGi && data._compatReport) {
                                    const r = data._compatReport;
                                    const sev = r.severity || 'low';
                                    const cls = sev === 'high' ? 'danger' : sev === 'medium' ? 'warn' : 'info';
                                    const direction = r.is_downgrade ? 'DOWNGRADE' : 'UPGRADE';
                                    const dirCls = r.is_downgrade ? 'upgrade-build-fail' : 'upgrade-build-ok';
                                    const incompat = r.incompatible_features || [];
                                    const affectedDevNames = (r.is_downgrade ? downDevs : jumpDevs).map(d => d.hostname || d.id);
                                    const compatRows = incompat.slice(0, 8).map(f => {
                                        const note = f.portability_note ? ` <span style="opacity:0.5;font-size:0.85em">(${self.escapeHtml(f.portability_note)})</span>` : '';
                                        return `<div class="upgrade-compat-row"><span class="upgrade-compat-feat">${self.escapeHtml(f.id || '--')}</span><span class="upgrade-compat-path">${self.escapeHtml(f.config_path || '--')} <span style="opacity:0.35;font-size:0.85em">v${self.escapeHtml(f.added_in || '?')}</span>${note}</span></div>`;
                                    }).join('');
                                    alertsHtml += `<div class="upgrade-compare-alert upgrade-compare-alert--${cls}">
                                        <strong>Compatibility: ${self.escapeHtml(sev.toUpperCase())}</strong> -- <span class="${dirCls}">${direction}</span> -- ${r.incompatible_count || 0} incompatible feature(s)
                                        ${affectedDevNames.length ? `<div style="margin-top:4px;font-size:0.9em">Affected: <strong>${affectedDevNames.map(n => self.escapeHtml(n)).join(', ')}</strong></div>` : ''}
                                        ${r.warning ? `<div style="font-size:0.85em;margin-top:4px">${self.escapeHtml(r.warning)}</div>` : ''}
                                        ${r.recommendation ? `<div style="font-size:0.85em;margin-top:6px;opacity:0.8">${self.escapeHtml(r.recommendation)}</div>` : ''}
                                        ${r.auto_sanitize ? '<div style="font-size:0.85em;margin-top:4px;color:var(--dn-cyan,#00bcd4)">Auto-sanitize: ENABLED -- incompatible config lines will be stripped before restore.</div>' : ''}
                                        ${compatRows ? `<div class="upgrade-compat-list" style="margin-top:8px">${compatRows}</div>` : ''}
                                        ${incompat.length > 8 ? `<div style="font-size:0.8em;opacity:0.4;margin-top:4px">+ ${incompat.length - 8} more</div>` : ''}
                                    </div>`;
                                }
                                const dUrl = data.dnosUrl || sb?.dnos_url || '';
                                const gUrl = data.giUrl || sb?.gi_url || '';
                                const bUrl = data.baseosUrl || sb?.baseos_url || '';
                                const _shortUrl = (u) => {
                                    if (!u) return '--';
                                    try { const p = new URL(u); return '...' + p.pathname.split('/').slice(-2).join('/'); }
                                    catch (_) { return u.length > 50 ? '...' + u.slice(-45) : u; }
                                };
                                const hasUrls = dUrl || gUrl || bUrl;
                                const imagesHtml = hasUrls ? `<div class="upgrade-compare-images">
                                    <div class="upgrade-compare-images-title">Images</div>
                                    ${dUrl ? `<div class="upgrade-compare-img-row"><span class="upgrade-compare-img-label">DNOS</span><span class="upgrade-compare-img-url" title="${self.escapeHtml(dUrl)}">${_shortUrl(dUrl)}</span></div>` : ''}
                                    ${gUrl ? `<div class="upgrade-compare-img-row"><span class="upgrade-compare-img-label">GI</span><span class="upgrade-compare-img-url" title="${self.escapeHtml(gUrl)}">${_shortUrl(gUrl)}</span></div>` : ''}
                                    ${bUrl ? `<div class="upgrade-compare-img-row"><span class="upgrade-compare-img-label">BaseOS</span><span class="upgrade-compare-img-url" title="${self.escapeHtml(bUrl)}">${_shortUrl(bUrl)}</span></div>` : ''}
                                </div>` : '';
                                return `<div class="scaler-form">
                                    <div class="upgrade-compare-summary">Upgrading <strong>${devs.length}</strong> device(s) to <strong>${self.escapeHtml(targetLabel)}</strong>${sb ? ` (build #${sb.build_number})` : (rb ? ` (build #${rb.build_number} running)` : '')}</div>
                                    <div class="upgrade-compare-cards">${cards}</div>
                                    ${alertsHtml}
                                    ${imagesHtml}
                                </div>`;
                            },
                            afterRender: (data) => {
                                document.querySelectorAll('.upgrade-compare-card-header').forEach(hdr => {
                                    hdr.onclick = () => {
                                        const card = hdr.closest('.upgrade-compare-card');
                                        if (!card) return;
                                        const collapsed = card.classList.toggle('upgrade-compare-card--collapsed');
                                        const toggle = card.querySelector('.upgrade-compare-toggle');
                                        if (toggle) toggle.textContent = collapsed ? '+' : '-';
                                    };
                                });
                                const devs = (data.devices || []).filter(d => (data.selectedDeviceIds || []).includes(d.id));
                                const sb = data.selectedBuild;
                                const rb = data._runningBuild;
                                const _isGiModeAr = (d) => {
                                    const st = data.deviceStatus?.[d.id] || {};
                                    const ctx = data.deviceContexts?.[d.id] || {};
                                    const m = (st.mode || d._deviceMode || ctx.device_state || '').toUpperCase();
                                    return m === 'GI' || m === 'BASEOS_SHELL' || m === 'RECOVERY';
                                };
                                const _allGiAr = devs.length > 0 && devs.filter(_isGiModeAr).length === devs.length;
                                if (_allGiAr) {
                                    if (data._branchSwitch) { data._branchSwitch = null; self.WizardController.render(); }
                                    if (data._compatReport) { data._compatReport = null; self.WizardController.render(); }
                                }
                                if (sb && !data._targetStack && data.branch && sb.build_number && sb.build_number !== 'direct') {
                                    (async () => {
                                        try {
                                            const stack = await ScalerAPI.getBuildStack(data.branch, sb.build_number);
                                            const _verFromUrl = (url) => {
                                                if (!url) return null;
                                                const m = url.match(/(\d+\.\d+\.\d+[\d._-]*)/);
                                                return m ? m[1] : null;
                                            };
                                            self.WizardController.data._targetStack = {
                                                gi_version: _verFromUrl(stack.gi_url) || (stack.gi_url ? 'available' : '--'),
                                                baseos_version: _verFromUrl(stack.baseos_url) || (stack.baseos_url ? 'available' : '--'),
                                            };
                                            self.WizardController.render();
                                        } catch (_) {}
                                    })();
                                }
                                if (_allGiAr || (!sb && !rb) || devs.length === 0 || data._branchSwitch || data._compatReport) return;
                                const first = devs[0];
                                const ctx = data.deviceContexts?.[first.id] || {};
                                const st = data.deviceStatus?.[first.id] || {};
                                const monStack = first._stackData?.components || [];
                                const ctxStackArr = Array.isArray(ctx.stack) ? ctx.stack : [];
                                const compsArr = monStack.length ? monStack : ctxStackArr;
                                let curVer = st.dnos_ver || '';
                                if (!curVer) {
                                    for (const c of compsArr) {
                                        const nm = (c.name || c.component || '').toLowerCase();
                                        if (nm.includes('dnos') || nm === 'system') { curVer = c.current || c.version || ''; break; }
                                    }
                                }
                                const curVerFull = ctx.dnos_version || curVer || '';
                                const branch = data.branch || '';
                                const _extractVer = (s) => {
                                    if (!s) return '';
                                    const dotted = s.match(/(\d+\.\d+\.\d+[\d._]*)/);
                                    if (dotted) return dotted[1];
                                    const devBranch = s.match(/[_/]v(\d+)[_.](\d+)/);
                                    if (devBranch) return `${devBranch[1]}.${devBranch[2]}`;
                                    return '';
                                };
                                const curVerClean = _extractVer(curVer);
                                const tgtStack = data._targetStack || {};
                                const tgtVerClean = data._targetVersion || _extractVer(branch) || _extractVer(sb?.display_name || '') || _extractVer(tgtStack.gi_version || '') || _extractVer(sb?.dnos_url || '');
        
                                const _hasEmptyStack = compsArr.length === 0 && !curVer;
                                if (_hasEmptyStack) {
                                    const _mode = (st.mode || first._deviceMode || '').toUpperCase();
                                    self.WizardController.data._branchSwitch = {
                                        is_switch: true,
                                        requires_delete_deploy: false,
                                        current_branch: 'empty',
                                        target_branch: branch || 'target',
                                        _empty_stack: true,
                                    };
                                    self.WizardController.data._compatReport = {
                                        severity: 'low',
                                        is_downgrade: false,
                                        incompatible_count: 0,
                                        incompatible_features: [],
                                        warning: `Device has empty stack${_mode ? ' (mode: ' + _mode + ')' : ''} -- fresh deploy, no compatibility concerns.`,
                                        recommendation: 'gi_deploy will load all images from scratch.',
                                    };
                                    self.WizardController.render();
                                    return;
                                }
        
                                if (!curVerClean && tgtVerClean && data._targetStack) {
                                    self.WizardController.data._branchSwitch = {
                                        is_switch: false,
                                        requires_delete_deploy: false,
                                        _unknown_current: true,
                                    };
                                    self.WizardController.data._compatReport = {
                                        severity: 'low',
                                        incompatible_count: 0,
                                        incompatible_features: [],
                                        warning: 'Current device version unknown -- cannot compare. Deploy will proceed.',
                                    };
                                    self.WizardController.render();
                                    return;
                                }
                                if (!curVerClean || !tgtVerClean) {
                                    if (!data._targetStack) return;
                                }
                                if (curVerClean && tgtVerClean) {
                                    (async () => {
                                        try {
                                            const bs = await ScalerAPI.detectBranchSwitch({
                                                current_version: curVerFull || curVer || curVerClean,
                                                target_version: tgtVerClean,
                                                target_branch_name: branch
                                            });
                                            self.WizardController.data._branchSwitch = bs;
                                            const compat = await ScalerAPI.checkVersionCompat({ source_version: curVerClean, target_version: tgtVerClean });
                                            self.WizardController.data._compatReport = compat;
                                            self.WizardController.render();
                                        } catch (_) {}
                                    })();
                                }
                            },
                            collectData: () => ({}),
                            skipIf: (data) => !data.selectedBuild && !data._runningBuild
                        },
                        {
                            title: 'Upgrade Plan',
                            render: (data) => {
                                const _buildClientPlan = () => {
                                    const requiresDD = data._branchSwitch?.requires_delete_deploy || false;
                                    const isBranchSwitch = data._branchSwitch?.is_switch || false;
                                    const sb = data.selectedBuild;
                                    const _extractVerFromUrl = (url) => {
                                        if (!url) return '';
                                        const m = url.match(/(\d+\.\d+\.\d+(?:\.\d+)?)/);
                                        return m ? m[1] : '';
                                    };
                                    const _cleanDisplayVer = (sb) => {
                                        if (!sb) return '--';
                                        const fromUrl = _extractVerFromUrl(sb.dnos_url);
                                        if (fromUrl) return fromUrl;
                                        const dn = sb.display_name || '';
                                        const verMatch = dn.match(/(\d+\.\d+\.\d+(?:\.\d+)?)/);
                                        if (verMatch) return verMatch[1];
                                        return sb.build_number ? `#${sb.build_number}` : '--';
                                    };
                                    const targetVer = _cleanDisplayVer(sb) || data._targetVersion || '--';
                                    const _exMaj = (s) => { if (!s || s === '--') return 0; const m = s.match(/(\d+)\./); return m ? parseInt(m[1]) : 0; };
                                    const tgtMaj = _exMaj(targetVer);
                                    const status = data.deviceStatus || {};
                                    const plan = { devices: {} };
                                    const devs = (data.devices || []).filter(d => (data.selectedDeviceIds || []).includes(d.id));
                                    for (const d of devs) {
                                        const ctx = data.deviceContexts?.[d.id] || {};
                                        const st = status[d.id] || {};
                                        const monStack = d._stackData?.components || [];
                                        const ctxStack = Array.isArray(ctx.stack) ? ctx.stack : [];
                                        const parsed = self._parseStackVersions(monStack.length ? monStack : ctxStack);
                                        const curDnos = st.dnos_ver || parsed.dnos;
                                        const curMaj = _exMaj(curDnos);
                                        const devMajorJump = curMaj > 0 && tgtMaj > 0 && curMaj !== tgtMaj;
                                        const ctxState = (ctx.device_state || '').toUpperCase();
                                        const mode = (st.mode || self._classifyDeviceState(ctxState)).toUpperCase();
                                        let upgrade_type = 'normal';
                                        let reason = '';
                                        const warnings = [];
                                        if (mode === 'RECOVERY') {
                                            upgrade_type = 'blocked';
                                            reason = 'Device in RECOVERY mode -- restore first';
                                            warnings.push('Cannot upgrade from RECOVERY');
                                        } else if (mode === 'GI') {
                                            upgrade_type = 'gi_deploy';
                                            reason = 'Device in GI mode -- deploy flow';
                                        } else if (devMajorJump) {
                                            upgrade_type = 'delete_deploy';
                                            reason = `Major version change (v${curMaj} -> v${tgtMaj})`;
                                            warnings.push('Delete+Deploy required');
                                        } else if (requiresDD || isBranchSwitch) {
                                            upgrade_type = 'delete_deploy';
                                            const bsCur = data._branchSwitch?.current_branch || '(unknown)';
                                            const bsTgt = data._branchSwitch?.target_branch || '(unknown)';
                                            reason = `Branch switch: ${bsCur} -> ${bsTgt}`;
                                            warnings.push('Branch switch requires Delete+Deploy');
                                        } else {
                                            reason = curDnos !== '--' ? 'Same major version' : 'Version not detected';
                                        }
                                        // Fall back across every cached source so we
                                        // never paint "sys-type?" for a device whose
                                        // chassis is already known. Order matches
                                        // `_getWizardDeviceListSync`. The
                                        // `deploy_system_type` fallback covers the
                                        // post-`system delete` case where
                                        // operational.json was wiped to "N/A" but
                                        // devices.json / backups still remember the
                                        // chassis as e.g. SA-36CD-S.
                                        const _hostLabel = (d.hostname || d.id || '').trim();
                                        const _isPe4DeployTarget = /^(YOR[_-]CL[_-])?PE[_-]?4$/i.test(_hostLabel);
                                        const rawSys = ctx.system_type
                                            || ctx.deploy_system_type
                                            || d.platform
                                            || d._systemType
                                            || d._deploySystemType
                                            || '';
                                        let sysType = (self._sanitizeWizardSystemType(rawSys) || '').toUpperCase();
                                        if (_isPe4DeployTarget) {
                                            sysType = 'CL-86';
                                        }
                                        // Cluster detection must not rely on the
                                        // resolved sys-type alone. When a CL-*
                                        // device is only partially discovered
                                        // (NCC1 down, stale op-state, snapshot
                                        // from before convert, etc.) the cached
                                        // `system_type` can come back as the
                                        // NCP-1 chassis code (e.g. `SA-40C8CD`).
                                        // Treating that as standalone strips the
                                        // NCC selector, sends `ncc-id None` to
                                        // the bridge and silently runs the SA
                                        // deploy path. Trust any cluster signal
                                        // the canvas or hostname gives us, and
                                        // flag the mismatch so the UI can force
                                        // the operator to pick a CL-* sys-type.
                                        // See "Cluster vs SA sys-type guard" in
                                        // DEVELOPMENT_GUIDELINES.md.
                                        const _ctxClusterHint = !!(ctx.is_cluster
                                            || ctx.active_ncc_vm
                                            || ctx.active_ncc_node
                                            || ctx.pre_upgrade_active_ncc_vm
                                            || ctx.kvm_host
                                            || ctx.kvm_host_ip);
                                        const _clusterSignal = !!(d._isCluster
                                            || _ctxClusterHint
                                            || sysType.startsWith('CL-'));
                                        const isCluster = _clusterSignal;
                                        // Operator's own override wins over every
                                        // other signal. If the ctx came back with
                                        // ``user_override_*`` as the source, the
                                        // value in ``sysType`` IS what the operator
                                        // explicitly picked -- never flag that as
                                        // a mismatch. Without this, even after the
                                        // operator corrects SA->CL the banner
                                        // reappears next time Step 5 opens because
                                        // the backend scaler-CLI plan still reads
                                        // the stale SA from db/devices.json.
                                        const _ctxIsOverride = (ctx.system_type_source || '').startsWith('user_override');
                                        const _sysTypeClaimsSA = sysType.startsWith('SA-');
                                        const _sysTypeMismatch = !_ctxIsOverride && isCluster && _sysTypeClaimsSA;
                                        if (_sysTypeMismatch) {
                                            warnings.push('Cluster device reported SA sys-type -- pick CL-* below before Execute');
                                        }
                                        const prevSysType = (ctx.deploy_system_type || ctx.previous_system_type || '').toUpperCase();
                                        const sysTypeChanged = prevSysType && sysType && prevSysType !== sysType;
                                        const sysTypeCategoryChange = sysTypeChanged && (
                                            (prevSysType.startsWith('SA-') && sysType.startsWith('CL-')) ||
                                            (prevSysType.startsWith('CL-') && sysType.startsWith('SA-'))
                                        );
                                        if (sysTypeChanged) {
                                            warnings.push(`System type change: ${prevSysType} -> ${sysType}`);
                                        }
                                        if (sysTypeCategoryChange) {
                                            warnings.push('SA<->CL change requires cleaner on ALL NCEs after deploy');
                                        }
                                        // Active NCC detection for cluster devices. Order of trust:
                                        //   0. `ctx.pre_upgrade_active_ncc_vm`  -- explicit pre-upgrade
                                        //      snapshot stamped the moment the operator begins an
                                        //      upgrade (see `snapshot_active_ncc_for_upgrade` in
                                        //      `topology/routes/bridge_helpers.py`). Wins over live
                                        //      probes while `ctx.pre_upgrade_cleared_at` is unset,
                                        //      because the cluster state can flip during the upgrade
                                        //      window and the wizard MUST keep pointing at the NCC
                                        //      that was active when the operator hit Execute.
                                        //   1. `sshConfig._virshInfo.activeNcc`  -- set by a live
                                        //      virsh console probe (authoritative live signal).
                                        //   2. `ctx.active_ncc_node` / `ctx.active_ncc_vm` -- populated
                                        //      by the backend from operational.json's `active_ncc_vm`
                                        //      (written by a real probe OR by the pre-upgrade
                                        //      snapshot path -- the resolver chain in
                                        //      `_get_device_context` normalizes the value).
                                        // If none of these are available we MUST NOT silently label
                                        // NCC-0 "(active)": on a two-NCC cluster that is a 50/50 coin
                                        // flip and pushing a deploy to the standby NCC fails. Track
                                        // provenance so the UI can down-grade the badge to
                                        // "(default)" and the code above the plan can trigger a live
                                        // probe. See 2026-04-24 note in DEVELOPMENT_GUIDELINES.md.
                                        // 2026-05-12: do NOT silently seed
                                        // `ncc_id=1` / `pe4_deploy_default`
                                        // for PE-4. The destructive-op trust
                                        // gate at Execute would refuse the
                                        // value anyway; leaving these empty
                                        // forces the orange "Re-detect" badge
                                        // to surface instead.
                                        let _activeNccId = 0;
                                        let _activeNccSource = '';
                                        let _activeNccVm = '';
                                        // Propagate `ctx.active_ncc_source` verbatim
                                        // when we adopt the ctx VM, so a fresh
                                        // `kvm_virsh_probe` from the resolver shows
                                        // up as TRUSTED in the dropdown render.
                                        // `ctx.active_ncc_source` may be empty when
                                        // scaler's raw write of operational.json
                                        // dropped the provenance -- in that case
                                        // we tag the value 'context_unverified'
                                        // so the render path can ask for a fresh
                                        // probe instead of mislabelling it
                                        // "(active)".
                                        if (isCluster) {
                                            const _vi = d.sshConfig?._virshInfo || {};
                                            const _preUpgradeVm = (!ctx.pre_upgrade_cleared_at
                                                ? (ctx.pre_upgrade_active_ncc_vm || '')
                                                : '');
                                            const _activeVm = _preUpgradeVm
                                                || _vi.activeNcc
                                                || ctx.active_ncc_node
                                                || ctx.active_ncc_vm
                                                || '';
                                            const _nccMatch = _activeVm.match(/ncc[_-]?(\d+)/i);
                                            if (_nccMatch) {
                                                _activeNccId = parseInt(_nccMatch[1], 10);
                                                _activeNccVm = _activeVm;
                                                if (_preUpgradeVm) {
                                                    _activeNccSource = 'upgrade_start_snapshot';
                                                } else if (_vi.activeNcc) {
                                                    _activeNccSource = 'virsh_console_verified';
                                                } else {
                                                    const _ctxSrc = String(ctx.active_ncc_source || '').trim();
                                                    _activeNccSource = _ctxSrc || 'context_unverified';
                                                }
                                            }
                                            // 2026-05-12: removed unconditional
                                            // _activeNccId=1 / source=pe4_deploy_default
                                            // PE-4 override. The Execute trust
                                            // gate now refuses any untrusted
                                            // source, so silently seeding a
                                            // legacy default just hides the
                                            // "click Re-detect" prompt.
                                        }
                                        // ncc_id contract with the bridge (mirrors scaler CLI):
                                        // - Cluster (KVM/CL): use probed _activeNccId if known,
                                        //   fall back to 0 when probe was inconclusive. Bridge
                                        //   CLI retry flips to 1 automatically if the wrong
                                        //   slot was picked ("doesn't match / auto detected").
                                        // - Single-access (SA): always 0 (only one NCC slot
                                        //   exists on SA hardware).
                                        // NEVER send null -- the bridge used to interpolate
                                        // that as the literal text "ncc-id None" into the
                                        // `request system deploy` command, which GI silently
                                        // accepts without registering any install task. That
                                        // was RR-SA-2's 20-minute-timeout root cause.
                                        const _resolvedNccId = isCluster
                                            ? (Number.isInteger(_activeNccId) ? _activeNccId : 0)
                                            : 0;
                                        plan.devices[d.id] = {
                                            mode, upgrade_type, reason, warnings,
                                            current_version: curDnos !== '--' ? curDnos : '-',
                                            target_version: targetVer,
                                            components: ['DNOS', 'GI', 'BaseOS'],
                                            ncc_id: _resolvedNccId,
                                            active_ncc_source: _activeNccSource,
                                            active_ncc_vm: _activeNccVm,
                                            is_cluster: isCluster,
                                            // Blank out the sys-type when the
                                            // cluster signal disagrees with an
                                            // SA-* resolve so the wizard paints
                                            // the red "sys-type?" selector and
                                            // the operator is forced to pick a
                                            // CL-* before Execute. `reason`
                                            // above already captures the
                                            // mismatch via the pushed warning.
                                            system_type: _sysTypeMismatch ? '' : sysType,
                                            system_type_mismatch: _sysTypeMismatch || false,
                                            system_type_raw: sysType,
                                            cluster_signal_source: (
                                                d._clusterHintSource
                                                || (ctx.is_cluster ? 'context_flag' : '')
                                                || (_ctxClusterHint ? 'context_ncc' : '')
                                                || (sysType.startsWith('CL-') ? 'system_type' : '')
                                                || ''
                                            ),
                                            previous_system_type: prevSysType || '',
                                            system_type_changed: sysTypeChanged || false,
                                            system_type_category_change: sysTypeCategoryChange || false,
                                            deploy_params: {
                                                system_type: _sysTypeMismatch ? '' : sysType,
                                                ncc_id: _resolvedNccId,
                                                active_ncc_source: _activeNccSource,
                                                name: _isPe4DeployTarget ? 'YOR_CL_PE-4' : _hostLabel,
                                                deploy_name: _isPe4DeployTarget ? 'YOR_CL_PE-4' : _hostLabel,
                                            },
                                        };
                                    }
                                    return plan;
                                };
                                const _planDevEntries = data._upgradePlan ? Object.entries(data._upgradePlan.devices || {}) : [];
                                const _planMissingSysType = _planDevEntries.length > 0 && _planDevEntries.some(([_, e]) => !e.system_type);
                                // Rebuild the plan when a row's current_version
                                // is empty ("-") but the canvas now has live
                                // stack data for that device. Without this
                                // trigger a plan that was built before the
                                // monitor finished would keep painting
                                // "CURRENT: -" forever, making the branch-
                                // switch reason look unjustified. Only
                                // applies to `_planSource === 'local'` so we
                                // never overwrite an SSH-verified plan.
                                const _devsNow = (data.devices || []).filter(d => (data.selectedDeviceIds || []).includes(d.id));
                                const _planHasStaleCurrent = data._planSource !== 'ssh'
                                    && _planDevEntries.length > 0
                                    && _planDevEntries.some(([did, e]) => {
                                        const cv = (e.current_version || '').trim();
                                        if (cv && cv !== '-' && cv !== '--') return false;
                                        const dev = _devsNow.find(x => x.id === did);
                                        const hasStack = !!(dev && dev._stackData && dev._stackData.components && dev._stackData.components.length);
                                        const ctxNow = data.deviceContexts?.[did] || {};
                                        const hasCtxStack = Array.isArray(ctxNow.stack) && ctxNow.stack.length > 0;
                                        return hasStack || hasCtxStack;
                                    });
                                if (!data._upgradePlan || Object.keys(data._upgradePlan.devices || {}).length === 0 || _planMissingSysType || _planHasStaleCurrent) {
                                    data._upgradePlan = _buildClientPlan();
                                    data._planSource = 'local';
                                }
                                const plan = data._upgradePlan;
                                const devices = plan.devices || {};
                                const deviceIds = data.selectedDeviceIds || [];
                                const devs = (data.devices || []).filter(d => deviceIds.includes(d.id));
                                const verifying = data._planLoading;
                                const verifyErr = data._planError;
                                const maxConcurrent = data.maxConcurrent ?? 3;
                                const requiresDD = data._branchSwitch?.requires_delete_deploy || false;
                                const isBranchSwitch = data._branchSwitch?.is_switch || false;
                                const sb = data.selectedBuild;
                                const _cleanVer = (sb) => {
                                    if (!sb) return '--';
                                    const fromUrl = sb.dnos_url?.match(/(\d+\.\d+\.\d+(?:\.\d+)?)/);
                                    if (fromUrl) return fromUrl[1];
                                    const dn = sb.display_name || '';
                                    const vm = dn.match(/(\d+\.\d+\.\d+(?:\.\d+)?)/);
                                    if (vm) return vm[1];
                                    return sb.build_number ? `#${sb.build_number}` : '--';
                                };
                                const targetVer = _cleanVer(sb);
                                const _exMaj = (s) => { if (!s || s === '--') return 0; const m = s.match(/(\d+)\./); return m ? parseInt(m[1]) : 0; };
                                const tgtMaj = _exMaj(targetVer);
                                const _attr = (v) => String(v ?? '')
                                    .replace(/&/g, '&amp;')
                                    .replace(/"/g, '&quot;')
                                    .replace(/</g, '&lt;')
                                    .replace(/>/g, '&gt;');
                                const _firstVersionToken = (text) => {
                                    const s = String(text || '').trim();
                                    if (!s) return '';
                                    const ver = s.match(/(\d+\.\d+\.\d+(?:[._-]\d+)*)/);
                                    if (ver) return ver[1];
                                    const build = s.match(/#\d+/);
                                    if (build) return build[0];
                                    return '';
                                };
                                const _isStatusBlob = (text) => {
                                    const s = String(text || '').trim();
                                    return s.length > 48
                                        && /(warn|error|failed|failure|cached|unknown|mismatch|required|blocked|cannot|not detected)/i.test(s);
                                };
                                const _renderPlanVersionCell = (value, rowNotes, label) => {
                                    const raw = String(value ?? '').trim() || '-';
                                    if (_isStatusBlob(raw)) {
                                        rowNotes.push({ label, text: raw });
                                        const compact = _firstVersionToken(raw) || 'See note';
                                        return `<div class="upgrade-plan-ver-cell upgrade-plan-ver-cell--note" title="${_attr(raw)}">${self.escapeHtml(compact)}</div>`;
                                    }
                                    const parts = raw
                                        .split(/\s*(?:;|\s\/\s|\n)\s*/g)
                                        .map(part => part.trim())
                                        .filter(Boolean);
                                    if (parts.length > 1 && parts.length <= 4) {
                                        return `<div class="upgrade-plan-ver-stack" title="${_attr(raw)}">
                                            ${parts.map(part => `<span class="upgrade-plan-ver-pill">${self.escapeHtml(part)}</span>`).join('')}
                                        </div>`;
                                    }
                                    return `<div class="upgrade-plan-ver-cell" title="${_attr(raw)}">${self.escapeHtml(raw)}</div>`;
                                };
                                const _renderPlanNotes = (items) => {
                                    if (!items.length) return '';
                                    const notes = items.map(item => `<div class="upgrade-plan-note">
                                        <span class="upgrade-plan-note-label">${self.escapeHtml(item.label)}:</span>
                                        <span class="upgrade-plan-note-text">${self.escapeHtml(item.text)}</span>
                                    </div>`).join('');
                                    return `<tr class="upgrade-plan-note-row"><td colspan="4"><div class="upgrade-plan-note-list">${notes}</div></td></tr>`;
                                };
                                const rows = devs.map(d => {
                                    const p = devices[d.id] || {};
                                    const upType = p.upgrade_type || 'normal';
                                    const reason = p.reason || '';
                                    const warnings = (p.warnings || []).join('; ');
                                    const curVer = p.current_version || '-';
                                    const tgtVer = p.target_version || '-';
                                    const blocked = upType === 'blocked';
                                    const ctx = data.deviceContexts?.[d.id] || {};
                                    const monStack = d._stackData?.components || [];
                                    const ctxStack = Array.isArray(ctx.stack) ? ctx.stack : [];
                                    const parsed = self._parseStackVersions(monStack.length ? monStack : ctxStack);
                                    const curMaj = _exMaj(parsed.dnos);
                                    const devMajorJump = curMaj > 0 && tgtMaj > 0 && curMaj !== tgtMaj;
                                    const devNeedsDD = requiresDD || devMajorJump;
                                    const mode = (p.mode || '').toUpperCase();
                                    const opts = [];
                                    if (blocked) {
                                        opts.push({ val: 'blocked', label: 'Skip (blocked)' });
                                    } else if (mode === 'GI') {
                                        opts.push({ val: 'gi_deploy', label: 'GI Deploy' });
                                        opts.push({ val: 'blocked', label: 'Skip' });
                                    } else if (devNeedsDD) {
                                        opts.push({ val: 'delete_deploy', label: 'Delete+Deploy' });
                                        opts.push({ val: 'blocked', label: 'Skip' });
                                    } else if (isBranchSwitch) {
                                        opts.push({ val: 'normal', label: 'Normal' });
                                        opts.push({ val: 'delete_deploy', label: 'Delete+Deploy' });
                                        opts.push({ val: 'blocked', label: 'Skip' });
                                    } else {
                                        opts.push({ val: 'normal', label: 'Normal' });
                                        opts.push({ val: 'delete_deploy', label: 'Delete+Deploy' });
                                        opts.push({ val: 'gi_deploy', label: 'GI Deploy' });
                                        opts.push({ val: 'blocked', label: 'Skip' });
                                    }
                                    const selVal = devNeedsDD && upType === 'normal' ? 'delete_deploy' : upType;
                                    const optionsHtml = opts.map(o => `<option value="${o.val}" ${selVal === o.val ? 'selected' : ''}>${o.label}</option>`).join('');
                                    const _sysType = p.system_type || '';
                                    // Cluster detection in the row: union of
                                    // every signal we have. `p.is_cluster` is
                                    // now set by `_buildClientPlan` when the
                                    // context / canvas / hostname convention
                                    // says cluster, even if the resolved
                                    // sys-type is SA-*. Keep the hostname
                                    // regex as a last-resort safety net so
                                    // an SSH-verified plan built by an older
                                    // backend (no `is_cluster` field) still
                                    // paints the row correctly.
                                    const _nameLooksCL = /(^|[_\-])CL([_\-]|$)/i.test(d.hostname || d.id || '');
                                    const _isClDev = !!(
                                        p.is_cluster
                                        || _sysType.startsWith('CL-')
                                        || d._isCluster
                                        || _nameLooksCL
                                    );
                                    // `system_type_mismatch` is stamped by
                                    // `_buildClientPlan`. The SSH-verified plan
                                    // from a newer backend surfaces the same
                                    // through `p.system_type_mismatch`; older
                                    // backends won't, so re-derive here when
                                    // we see a CL-class device with an SA-*
                                    // sys-type.
                                    //
                                    // CRUCIAL: if the cached context says this
                                    // value came from the per-user override
                                    // store (``system_type_source`` starts with
                                    // ``user_override``) and the resolved value
                                    // is already CL-*, the operator has
                                    // explicitly agreed to this pick -- do NOT
                                    // re-flag the mismatch regardless of what
                                    // the backend plan (which doesn't consult
                                    // the override layer) stamped. Without
                                    // this guard YOR_CL_PE-4 keeps showing the
                                    // red banner on every Step-5 open even
                                    // though the operator corrected it.
                                    const _rawSysType = p.system_type_raw || _sysType;
                                    const _ctxOverrideActive = (ctx.system_type_source || '').startsWith('user_override')
                                        && (ctx.system_type || '').toUpperCase().startsWith('CL-');
                                    const _sysTypeMismatch = _ctxOverrideActive ? false : !!(
                                        p.system_type_mismatch
                                        || (_isClDev && _rawSysType.startsWith('SA-'))
                                    );
                                    const _knownSysTypes = self._WIZARD_KNOWN_SYS_TYPES;
                                    let _sysTypeHtml = '';
                                    if (!_sysType || _sysTypeMismatch) {
                                        // Mismatch path: force a CL-only picker
                                        // so the operator can't proceed with an
                                        // SA deploy on a cluster chassis. The
                                        // dropdown is seeded with the current
                                        // raw value (if any) for context.
                                        const _clOnly = _isClDev;
                                        const _filtered = _clOnly
                                            ? _knownSysTypes.filter(t => t.startsWith('CL-'))
                                            : _knownSysTypes;
                                        const _stOpts = _filtered.map(t => `<option value="${t}">${t}</option>`).join('');
                                        const _placeholder = _sysTypeMismatch
                                            ? `sys-type mismatch (${_rawSysType || 'SA-*'}) -- pick CL-*`
                                            : 'sys-type?';
                                        _sysTypeHtml = `<div style="margin-top:1px">
                                            <select class="upgrade-plan-systype-select upgrade-plan-select" data-device="${d.id}" style="width:auto;border-color:var(--dn-red,#e74c3c);color:var(--dn-red,#e74c3c)">
                                                <option value="" selected disabled>${_placeholder}</option>
                                                ${_stOpts}
                                            </select>
                                            ${_sysTypeMismatch ? `<div class="upgrade-plan-systype-warn upgrade-plan-systype-warn--critical" style="margin-top:2px">
                                                <svg width="12" height="12" style="vertical-align:middle;margin-right:3px"><use href="#ico-warning"/></svg>
                                                <strong>Cluster device reported SA chassis</strong>
                                                <br><span style="font-size:9px">Resolved ${self.escapeHtml(_rawSysType || 'SA-*')} but ${self.escapeHtml(d.hostname || d.id)} is a cluster (${self.escapeHtml(p.cluster_signal_source || 'canvas/hostname')}). Pick the correct CL-* before Execute or the deploy will target the wrong profile.</span>
                                            </div>` : ''}
                                        </div>`;
                                    } else {
                                        const _clLabel = _isClDev ? ' cluster' : '';
                                        _sysTypeHtml = `<span style="font-size:10px;opacity:0.65;margin-left:3px">[${_sysType}${_clLabel}]</span>`;
                                    }
                                    const _pf = p.cluster_preflight;
                                    const _pfFail = _pf && _pf.blocked;
                                    const _pfWarn = _pf && _pf.warnings && _pf.warnings.length > 0 && !_pf.blocked;
                                    let _pfHtml = '';
                                    if (_pfFail) {
                                        const shutOff = (_pf.vms_shut_off || []).join(', ');
                                        _pfHtml = `<div class="upgrade-plan-preflight-fail" title="${self.escapeHtml(_pf.block_reason || '')}">
                                            <svg width="14" height="14" style="vertical-align:middle;margin-right:4px;"><use href="#ico-warning"/></svg>
                                            CLUSTER PREFLIGHT FAIL: ${shutOff} shut off on ${_pf.kvm_host || 'KVM'}
                                            <br><span style="font-size:9px;opacity:0.8;">Start all NCC VMs before deploying. Only ${(_pf.vms_running||[]).length}/${(_pf.ncc_vms_expected||[]).length} running.</span>
                                        </div>`;
                                    } else if (_pfWarn) {
                                        _pfHtml = `<div class="upgrade-plan-preflight-warn">${_pf.warnings[0]}</div>`;
                                    }
                                    let _nccSelectorHtml = '';
                                    const _nccOpts = (_pf && _pf.ncc_options) || [];
                                    if (_isClDev && _nccOpts.length > 0 && !_pfFail) {
                                        const _curNcc = p.ncc_id != null ? p.ncc_id : (p.deploy_params?.ncc_id ?? 'autodetect');
                                        const _nccOptHtml = _nccOpts.map(o => {
                                            const val = o.ncc_id != null ? o.ncc_id : o.vm_name;
                                            const sel = String(val) === String(_curNcc) ? 'selected' : '';
                                            return `<option value="${val}" data-vm="${o.vm_name}" ${sel}>${o.label}</option>`;
                                        }).join('');
                                        _nccSelectorHtml = `<div class="upgrade-plan-ncc-selector">
                                            <label class="upgrade-plan-ncc-label">Deploy NCC:</label>
                                            <select class="upgrade-plan-ncc-select" data-device="${d.id}">${_nccOptHtml}</select>
                                        </div>`;
                                    } else if (_isClDev && !_pfFail) {
                                        const _defNcc = p.ncc_id != null ? p.ncc_id : 0;
                                        const _src = String(p.active_ncc_source || '').trim();
                                        // Mirror `_TRUSTED_ACTIVE_NCC_SOURCES` from
                                        // `routes/bridge_helpers.py`. Anything outside
                                        // this set (including the legacy bare
                                        // `ctx.active_ncc_vm` with no source -- which
                                        // we now tag `context_unverified`) means
                                        // scaler's raw json dump dropped the
                                        // provenance and we cannot trust the value
                                        // without a fresh probe.
                                        const _NCC_TRUST_PREFIXES_R = [
                                            'kvm_', 'virsh_console_verified',
                                            'pre_upgrade_snapshot', 'pre_upgrade_backup',
                                            'scaler_db_cache', 'topology_virsh_probe',
                                            'upgrade_start_snapshot', 'post_reboot_virsh_probe',
                                        ];
                                        const _isTrusted = _src
                                            && _NCC_TRUST_PREFIXES_R.some(pref => _src.startsWith(pref));
                                        const _isPreUpgrade = _src === 'upgrade_start_snapshot';
                                        const _isUnverifiedCtx = _src === 'context_unverified';
                                        const _hasGuessedVm = !!p.active_ncc_vm;
                                        const _probing = !!(self._nccProbeInFlight && self._nccProbeInFlight[d.id]);
                                        // Tag semantics:
                                        //   "(active)"     -- trusted live/probe signal.
                                        //   "(pre-upgrade)"-- frozen snapshot stamped when
                                        //                     the upgrade began.
                                        //   "(unverified)" -- a value exists in
                                        //                     operational.json but its
                                        //                     `active_ncc_source` was
                                        //                     dropped (scaler raw write).
                                        //                     Operator must Re-detect
                                        //                     before Execute.
                                        //   "(detecting...)"/"(default -- verify!)" --
                                        //                     no value at all yet.
                                        const _tag = (n) => {
                                            if (_defNcc !== n) return '';
                                            if (_isTrusted) return _isPreUpgrade ? ' (pre-upgrade)' : ' (active)';
                                            if (_isUnverifiedCtx && _hasGuessedVm) return ' (unverified -- re-detect!)';
                                            return _probing ? ' (detecting...)' : ' (default -- verify!)';
                                        };
                                        const _ncc0Label = `NCC-0${_tag(0)}`;
                                        const _ncc1Label = `NCC-1${_tag(1)}`;
                                        const _showWarn = !_isTrusted && !_probing;
                                        const _warnText = _isUnverifiedCtx
                                            ? 'Active NCC source was dropped by scaler write -- '
                                            : 'Active NCC not detected -- ';
                                        const _warn = _showWarn
                                            ? `<div class="upgrade-plan-ncc-warn" style="color:var(--dn-orange,#e67e22);font-size:10px;margin-top:2px">
                                                ${_warnText}click
                                                <a href="#" data-action="probe-active-ncc" data-device="${d.id}" style="color:var(--dn-orange,#e67e22);text-decoration:underline">Re-detect</a>
                                                or verify manually before Execute.
                                            </div>`
                                            : '';
                                        const _preUpgradeHint = _isPreUpgrade
                                            ? `<div class="upgrade-plan-ncc-hint" style="color:var(--dn-green,#27ae60);font-size:10px;margin-top:2px">
                                                Using pre-upgrade snapshot (frozen when upgrade began).
                                               </div>`
                                            : '';
                                        _nccSelectorHtml = `<div class="upgrade-plan-ncc-selector">
                                            <label class="upgrade-plan-ncc-label">Deploy NCC:</label>
                                            <select class="upgrade-plan-ncc-select" data-device="${d.id}">
                                                <option value="0" ${_defNcc === 0 ? 'selected' : ''}>${_ncc0Label}</option>
                                                <option value="1" ${_defNcc === 1 ? 'selected' : ''}>${_ncc1Label}</option>
                                            </select>
                                            ${_warn}
                                            ${_preUpgradeHint}
                                        </div>`;
                                    }
                                    const _jumpTag = devMajorJump ? ` <span class="upgrade-plan-jump-tag">v${curMaj}->v${tgtMaj}</span>` : '';
                                    const _stChanged = p.system_type_changed || false;
                                    const _stCatChange = p.system_type_category_change || false;
                                    const _prevSt = p.previous_system_type || '';
                                    let _stChangeHtml = '';
                                    if (_stCatChange) {
                                        _stChangeHtml = `<div class="upgrade-plan-systype-warn upgrade-plan-systype-warn--critical">
                                            <svg width="12" height="12" style="vertical-align:middle;margin-right:3px"><use href="#ico-warning"/></svg>
                                            <strong>SYSTEM TYPE CHANGE: ${self.escapeHtml(_prevSt)} -> ${self.escapeHtml(_sysType)}</strong>
                                            <br><span style="font-size:9px">SA&lt;-&gt;CL change requires cleaner on ALL NCEs. NCPs/NCFs will NOT join without it.</span>
                                        </div>`;
                                    } else if (_stChanged) {
                                        _stChangeHtml = `<div class="upgrade-plan-systype-warn">
                                            <svg width="12" height="12" style="vertical-align:middle;margin-right:3px"><use href="#ico-warning"/></svg>
                                            System type change: ${self.escapeHtml(_prevSt)} -> ${self.escapeHtml(_sysType)}
                                        </div>`;
                                    }
                                    const _rowNotes = [];
                                    // 2026-05-12: surface the provenance of `Current` so the
                                    // operator knows whether it came from a live SSH probe
                                    // or the operational.json cache (PE-4 / cluster fallback
                                    // path). Without this, the row was visually identical
                                    // whether the SSH probe succeeded, the SSH probe failed
                                    // and we fell back to cache, or the value was simply
                                    // never detected -- and the bug report showed exactly
                                    // that confusion.
                                    const _curVerSrc = String(p.current_version_source || '');
                                    if (_curVerSrc.startsWith('operational_json_cache') || _curVerSrc === 'ssh_failed') {
                                        const _ageSec = Number(p.current_version_age_sec);
                                        const _ageHint = Number.isFinite(_ageSec) && _ageSec >= 0
                                            ? ` (~${_ageSec}s old)`
                                            : '';
                                        const _srcLabel = _curVerSrc === 'ssh_failed'
                                            ? 'SSH probe failed; no cached version available -- click Verify via SSH.'
                                            : `Current from operational.json cache${_ageHint}. Click Verify via SSH for a live re-probe.`;
                                        _rowNotes.push({ label: 'Source', text: _srcLabel });
                                    }
                                    const _curVerHtml = _renderPlanVersionCell(curVer, _rowNotes, 'Current');
                                    const _tgtVerHtml = _renderPlanVersionCell(tgtVer, _rowNotes, 'Target');
                                    const _deviceLabel = self.escapeHtml(d.hostname || d.id);
                                    const _rowTitle = _attr(`${reason} ${warnings}`.trim());
                                    return `<tr class="upgrade-plan-row${blocked ? ' upgrade-plan-row--blocked' : ''}${devNeedsDD ? ' upgrade-plan-row--forced' : ''}${_pfFail ? ' upgrade-plan-row--preflight-fail' : ''}${!_sysType ? ' upgrade-plan-row--no-systype' : ''}${_stCatChange ? ' upgrade-plan-row--systype-critical' : ''}" title="${_rowTitle}">
                                        <td class="upgrade-plan-device">
                                            <div class="upgrade-plan-device-main">
                                                <span class="upgrade-plan-device-name">${_deviceLabel}</span>
                                                ${_jumpTag}
                                            </div>
                                            <div class="upgrade-plan-device-meta">${_sysTypeHtml}${_stChangeHtml}${_pfHtml}${_nccSelectorHtml}</div>
                                        </td>
                                        <td class="upgrade-plan-ver">${_curVerHtml}</td>
                                        <td class="upgrade-plan-ver">${_tgtVerHtml}</td>
                                        <td class="upgrade-plan-type"><select class="upgrade-plan-select" data-device="${d.id}" ${blocked ? 'disabled' : ''}>${optionsHtml}</select></td>
                                    </tr>${_renderPlanNotes(_rowNotes)}`;
                                }).join('');
                                const sourceLabel = data._planSource === 'ssh' ? 'Verified via SSH' : 'Based on cached data';
                                const verifyHtml = verifying
                                    ? '<span class="upgrade-plan-verifying">Verifying via SSH...</span>'
                                    : (verifyErr
                                        ? `<span class="upgrade-plan-verify-err" title="${self.escapeHtml(verifyErr)}">Verify failed</span>`
                                        : `<span class="upgrade-plan-source">${sourceLabel}</span>`);
                                const hasDeleteDeploy = devs.some(d => ((devices[d.id] || {}).upgrade_type || 'normal') === 'delete_deploy');
                                const hasGiDeploy = devs.some(d => ((devices[d.id] || {}).upgrade_type || 'normal') === 'gi_deploy');
                                const ddNames = devs.filter(d => ((devices[d.id] || {}).upgrade_type || 'normal') === 'delete_deploy').map(d => d.hostname || d.id);
                                const giNames = devs.filter(d => ((devices[d.id] || {}).upgrade_type || 'normal') === 'gi_deploy').map(d => d.hostname || d.id);
                                let configRepairBanner = '';
                                if (hasDeleteDeploy) {
                                    configRepairBanner = `<div class="scaler-info-box" style="border-color:var(--dn-orange,#e67e22);color:var(--dn-orange,#e67e22);margin-bottom:8px;font-size:0.82em;line-height:1.35;padding:6px 10px"><strong>Delete+Deploy</strong> (${ddNames.join(', ')}): Config backup -> delete -> load 3 tarballs (GI) -> deploy -> restore.</div>`;
                                }
                                return `<div class="scaler-form" style="gap:6px">
                                    ${configRepairBanner}
                                    <div class="upgrade-plan-table-wrap">
                                        <table class="upgrade-plan-table">
                                            <colgroup>
                                                <col class="upgrade-plan-col-device">
                                                <col class="upgrade-plan-col-current">
                                                <col class="upgrade-plan-col-target">
                                                <col class="upgrade-plan-col-type">
                                            </colgroup>
                                            <thead><tr><th>Device</th><th>Current</th><th>Target</th><th>Type</th></tr></thead>
                                            <tbody>${rows}</tbody>
                                        </table>
                                    </div>
                                    <div class="upgrade-plan-footer">
                                        ${devs.length > 1 ? `<label style="font-size:11px;opacity:0.7;white-space:nowrap">Max parallel:</label>
                                        <input type="number" id="upgrade-max-concurrent" class="scaler-input" value="${maxConcurrent}" min="1" max="${devs.length}" style="width:60px;font-size:11px;padding:3px 5px">` : ''}
                                        <button type="button" class="scaler-btn scaler-btn-secondary" id="upgrade-plan-verify" style="font-size:11px;padding:3px 10px" ${verifying ? 'disabled' : ''}>${verifying ? 'Verifying...' : 'Verify via SSH'}</button>
                                        ${verifyHtml}
                                    </div>
                                </div>`;
                            },
                            afterRender: async (data) => {
                                const verifyPlan = async () => {
                                    if (self.WizardController.data._planFetching) return;
                                    const deviceIds = data.selectedDeviceIds || [];
                                    const sshHosts = {};
                                    (data.devices || []).filter(d => deviceIds.includes(d.id)).forEach(d => {
                                        sshHosts[d.id] = d.ssh_host || d.ip || '';
                                    });
                                    const branch = data.branch || '';
                                    const build = data.selectedBuild;
                                    const dnosUrl = data._directUrls && data.dnosUrl ? data.dnosUrl : null;
                                    self.WizardController.data._planLoading = true;
                                    self.WizardController.data._planFetching = true;
                                    self.WizardController.data._planError = null;
                                    self.WizardController.render();
                                    try {
                                        const params = { device_ids: deviceIds, ssh_hosts: sshHosts };
                                        if (dnosUrl) {
                                            params.dnos_url = dnosUrl;
                                        } else if (branch && build?.build_number) {
                                            params.target_branch = branch;
                                            params.target_build_number = build.build_number;
                                        } else if (data._targetVersion) {
                                            params.target_version = data._targetVersion;
                                        } else {
                                            params.target_version = '0.0.0';
                                        }
                                        // 2026-05-12: extend the timeout from 45s to 90s.
                                        // Cluster devices (CL-86, e.g. PE-4) whose mgmt_ip
                                        // rejects password SSH must fall through the slow
                                        // virsh-console probe in connect_for_upgrade -- one
                                        // device alone can spend 20-30s on that path. With
                                        // 3+ devices selected the 45s budget reliably
                                        // tripped, leaving the row painted with the
                                        // "current_version: -" / "mode: ?" stub the
                                        // exception handler produces (the bug screenshot
                                        // from 2026-05-12). The actual server-side SSH
                                        // call has its own per-step timeouts and bails
                                        // far sooner than 90s when the device is truly
                                        // unreachable; this larger budget just lets the
                                        // virsh-fallback path finish during the same
                                        // user-perceived load.
                                        const _planTimeout = new Promise((_, rej) => setTimeout(() => rej(new Error('SSH verify timed out after 90s')), 90000));
                                        const result = await Promise.race([ScalerAPI.getUpgradePlan(params), _planTimeout]);
                                        // Backend safety-net: older backends only
                                        // set `result_item.system_type` for cluster
                                        // devices, leaving SA-* rows with an empty
                                        // top-level field even when
                                        // `deploy_params.system_type` had the real
                                        // chassis. The newer backend (see
                                        // `routes/upgrade.py` 2026-04-24 patch)
                                        // surfaces it everywhere, but we keep this
                                        // client-side lift so the wizard also works
                                        // against an un-synced server.
                                        try {
                                            const _devsPlan = (result && result.devices) || {};
                                            const _wizDevices = (self.WizardController?.data?.devices) || [];
                                            Object.keys(_devsPlan).forEach(_did => {
                                                const _entry = _devsPlan[_did];
                                                if (!_entry) return;
                                                const _dpSt = (_entry.deploy_params && _entry.deploy_params.system_type) || '';
                                                if (!_entry.system_type && _dpSt) {
                                                    _entry.system_type = _dpSt;
                                                }
                                                // Also backfill from the local
                                                // `_deviceContexts` cache (which
                                                // already went through the fallback
                                                // chain in `openUpgradeWizard`). This
                                                // catches devices the backend still
                                                // has no snapshot for but the UI
                                                // already knows about.
                                                if (!_entry.system_type) {
                                                    const _cachedCtx = self._deviceContexts?.[_did];
                                                    const _cachedSt = _cachedCtx?.system_type || _cachedCtx?.deploy_system_type || '';
                                                    if (_cachedSt) _entry.system_type = _cachedSt;
                                                }
                                                // Cluster-vs-SA guard on the
                                                // SSH-verified plan: if the
                                                // canvas / hostname / context
                                                // all say cluster but the plan
                                                // came back with an SA chassis,
                                                // promote `is_cluster` and blank
                                                // out the bad sys-type so the
                                                // row renders the CL-only
                                                // picker. See user report
                                                // 2026-04-24 (YOR_CL_PE-4).
                                                const _wizDev = _wizDevices.find(x => x.id === _did) || {};
                                                const _cachedCtx = self._deviceContexts?.[_did] || {};
                                                const _nameLooksCL = /(^|[_\-])CL([_\-]|$)/i.test(_wizDev.hostname || _did || '');
                                                const _isPe4DeployTarget = /^(YOR[_-]CL[_-])?PE[_-]?4$/i.test((_wizDev.hostname || _did || '').trim());
                                                if (_isPe4DeployTarget) {
                                                    // PE-4 is a CL-86 cluster -- this is a
                                                    // safety net for legacy backends that
                                                    // didn't surface `system_type` at the
                                                    // top-level. The newer backend
                                                    // (`routes/upgrade.py` 2026-05-12 patch)
                                                    // already surfaces `system_type`,
                                                    // `active_ncc_vm`, and
                                                    // `active_ncc_source` from
                                                    // operational.json so the agent's
                                                    // pre-existing `kvm_first_running`
                                                    // signal flows through to the
                                                    // wizard. We keep the cluster /
                                                    // system_type stamp but ONLY OVERRIDE
                                                    // the active-NCC fields when the
                                                    // backend hasn't already published
                                                    // a value -- otherwise the wizard
                                                    // forces every PE-4 row to the
                                                    // legacy `pe4_deploy_default` source
                                                    // which is NOT in the trusted prefix
                                                    // list, producing the orange
                                                    // "Active NCC not detected" warning
                                                    // the bug screenshot showed.
                                                    if (!_entry.system_type || !_entry.system_type.startsWith('CL-')) {
                                                        _entry.system_type = 'CL-86';
                                                    }
                                                    _entry.system_type_raw = _entry.system_type_raw || _entry.system_type || 'CL-86';
                                                    _entry.is_cluster = true;
                                                    _entry.system_type_mismatch = false;
                                                    _entry.deploy_params = _entry.deploy_params || {};
                                                    if (!_entry.deploy_params.system_type || !String(_entry.deploy_params.system_type).startsWith('CL-')) {
                                                        _entry.deploy_params.system_type = _entry.system_type || 'CL-86';
                                                    }
                                                    if (!_entry.deploy_params.name) {
                                                        _entry.deploy_params.name = 'YOR_CL_PE-4';
                                                    }
                                                    if (!_entry.deploy_params.deploy_name) {
                                                        _entry.deploy_params.deploy_name = 'YOR_CL_PE-4';
                                                    }
                                                    // If the backend gave us NOTHING,
                                                    // try the cached context the
                                                    // wizard already collected (often
                                                    // has the live virsh probe
                                                    // result). When that ALSO has
                                                    // nothing, leave ncc_id unset and
                                                    // tag the source as
                                                    // `untrusted_no_probe` so the
                                                    // Execute trust gate refuses to
                                                    // submit and the operator is
                                                    // prompted to click Re-detect.
                                                    // Silently filling ncc_id=1 with
                                                    // source=pe4_deploy_default was
                                                    // the root cause of the
                                                    // 2026-05-12 PE-4 stuck-in-GI
                                                    // incident.
                                                    if (_entry.active_ncc_vm == null
                                                        && (_entry.active_ncc_source == null || _entry.active_ncc_source === '')) {
                                                        const _ctxNccVm = _cachedCtx.active_ncc_vm || '';
                                                        const _ctxNccSrc = _cachedCtx.active_ncc_source || '';
                                                        if (_ctxNccVm) {
                                                            _entry.active_ncc_vm = _ctxNccVm;
                                                            _entry.active_ncc_source = _ctxNccSrc || 'context_unverified';
                                                            const _m = String(_ctxNccVm).match(/ncc[\s_-]*(\d+)/i);
                                                            if (_m) {
                                                                _entry.ncc_id = parseInt(_m[1], 10);
                                                                _entry.deploy_params.ncc_id = _entry.ncc_id;
                                                            }
                                                        } else {
                                                            _entry.active_ncc_source = 'untrusted_no_probe';
                                                        }
                                                    } else {
                                                        // Backend gave us a trusted /
                                                        // tagged value -- mirror it
                                                        // into deploy_params and pick
                                                        // ncc_id from the VM name when
                                                        // not already set.
                                                        if (_entry.ncc_id == null && _entry.active_ncc_vm) {
                                                            const _m = String(_entry.active_ncc_vm).match(/ncc[\s_-]*(\d+)/i);
                                                            if (_m) {
                                                                _entry.ncc_id = parseInt(_m[1], 10);
                                                            }
                                                        }
                                                        if (_entry.ncc_id != null
                                                            && (_entry.deploy_params.ncc_id == null
                                                                || _entry.deploy_params.ncc_id === '')) {
                                                            _entry.deploy_params.ncc_id = _entry.ncc_id;
                                                        }
                                                    }
                                                }
                                                const _clusterSignal = !!(
                                                    _entry.is_cluster
                                                    || _entry.system_type?.startsWith?.('CL-')
                                                    || _wizDev._isCluster
                                                    || _cachedCtx.is_cluster
                                                    || _cachedCtx.active_ncc_vm
                                                    || _cachedCtx.active_ncc_node
                                                    || _cachedCtx.kvm_host
                                                    || _cachedCtx.kvm_host_ip
                                                    || _nameLooksCL
                                                );
                                                // Lift the per-user override BEFORE the
                                                // mismatch detection fires. The backend
                                                // scaler-CLI plan (``/plan/build``) reads
                                                // straight from ``db/devices.json`` and
                                                // never consults the per-user override
                                                // layer, so it will happily return the
                                                // stale SA-* reading for a cluster
                                                // device whose operator already picked
                                                // CL-86 in a previous session. Trust the
                                                // context's override source -- it's
                                                // authoritative for THIS user on THIS
                                                // topology. Without this check the red
                                                // mismatch banner kept reappearing for
                                                // YOR_CL_PE-4 every time the operator
                                                // opened Step 5 (report 2026-04-24).
                                                const _ctxSrc = (_cachedCtx.system_type_source || '');
                                                const _ctxSt = (_cachedCtx.system_type || '').toUpperCase();
                                                if (_ctxSrc.startsWith('user_override') && _ctxSt.startsWith('CL-')) {
                                                    _entry.system_type = _ctxSt;
                                                    _entry.system_type_raw = _entry.system_type_raw || _ctxSt;
                                                    if (_entry.deploy_params) _entry.deploy_params.system_type = _ctxSt;
                                                    _entry.is_cluster = true;
                                                    _entry.system_type_mismatch = false;
                                                    _entry.system_type_override_scope = _cachedCtx.system_type_override_scope || 'user';
                                                    if (Array.isArray(_entry.warnings)) {
                                                        _entry.warnings = _entry.warnings.filter(w =>
                                                            !/cluster device reported sa/i.test(w));
                                                    }
                                                    return; // don't fall through to the SA mismatch stamp
                                                }
                                                const _saNow = (_entry.system_type || '').toUpperCase().startsWith('SA-');
                                                if (_clusterSignal && _saNow) {
                                                    _entry.system_type_raw = _entry.system_type;
                                                    _entry.system_type = '';
                                                    if (_entry.deploy_params) _entry.deploy_params.system_type = '';
                                                    _entry.is_cluster = true;
                                                    _entry.system_type_mismatch = true;
                                                    _entry.cluster_signal_source = _entry.cluster_signal_source
                                                        || _wizDev._clusterHintSource
                                                        || (_cachedCtx.is_cluster ? 'context_flag' : '')
                                                        || (_cachedCtx.active_ncc_vm || _cachedCtx.active_ncc_node ? 'context_ncc' : '')
                                                        || (_nameLooksCL ? 'hostname' : '');
                                                    const _warn = 'Cluster device reported SA sys-type -- pick CL-* below before Execute';
                                                    _entry.warnings = Array.isArray(_entry.warnings) ? _entry.warnings : [];
                                                    if (!_entry.warnings.includes(_warn)) _entry.warnings.push(_warn);
                                                } else if (_clusterSignal) {
                                                    _entry.is_cluster = true;
                                                }
                                            });
                                        } catch (_liftExc) {
                                            console.warn('[Upgrade] system_type lift failed:', _liftExc);
                                        }
                                        self.WizardController.data._upgradePlan = result;
                                        self.WizardController.data._planSource = 'ssh';
                                        self.WizardController.data._planLoading = false;
                                        self.WizardController.data._planFetching = false;
                                        self.WizardController.render();
                                    } catch (e) {
                                        self.WizardController.data._planLoading = false;
                                        self.WizardController.data._planFetching = false;
                                        self.WizardController.data._planError = e.message;
                                        self.WizardController.render();
                                    }
                                };
                                document.getElementById('upgrade-plan-verify')?.addEventListener('click', verifyPlan);
                                document.querySelectorAll('.upgrade-plan-select').forEach(sel => {
                                    sel.addEventListener('change', (e) => {
                                        const did = e.target.dataset.device;
                                        const plan = self.WizardController.data._upgradePlan = self.WizardController.data._upgradePlan || {};
                                        plan.devices = plan.devices || {};
                                        if (!plan.devices[did]) plan.devices[did] = {};
                                        plan.devices[did].upgrade_type = e.target.value;
                                    });
                                });
                                document.querySelectorAll('.upgrade-plan-ncc-select').forEach(sel => {
                                    sel.addEventListener('change', (e) => {
                                        const did = e.target.dataset.device;
                                        const selectedOpt = e.target.options[e.target.selectedIndex];
                                        const nccId = parseInt(e.target.value, 10);
                                        const vmName = selectedOpt?.dataset?.vm || '';
                                        const plan = self.WizardController.data._upgradePlan = self.WizardController.data._upgradePlan || {};
                                        plan.devices = plan.devices || {};
                                        if (!plan.devices[did]) plan.devices[did] = {};
                                        plan.devices[did].ncc_id = isNaN(nccId) ? 0 : nccId;
                                        plan.devices[did].selected_ncc_vm = vmName;
                                        if (!plan.devices[did].deploy_params) plan.devices[did].deploy_params = {};
                                        plan.devices[did].deploy_params.ncc_id = isNaN(nccId) ? 0 : nccId;
                                        plan.devices[did].deploy_params.selected_ncc_vm = vmName;
                                    });
                                });
                                document.querySelectorAll('.upgrade-plan-systype-select').forEach(sel => {
                                    sel.addEventListener('change', (e) => {
                                        const did = e.target.dataset.device;
                                        const val = e.target.value;
                                        const plan = self.WizardController.data._upgradePlan = self.WizardController.data._upgradePlan || {};
                                        plan.devices = plan.devices || {};
                                        if (!plan.devices[did]) plan.devices[did] = {};
                                        plan.devices[did].system_type = val;
                                        plan.devices[did].is_cluster = val.startsWith('CL-');
                                        // Clear the SA<->CL mismatch flag once
                                        // the operator picks an explicit value.
                                        // Keep the raw (pre-override) sys-type
                                        // in `system_type_raw` for auditing.
                                        plan.devices[did].system_type_mismatch = false;
                                        if (!plan.devices[did].deploy_params) plan.devices[did].deploy_params = {};
                                        plan.devices[did].deploy_params.system_type = val;
                                        e.target.style.borderColor = 'var(--dn-cyan, #00b4d8)';
                                        e.target.style.background = 'rgba(0,180,216,0.08)';
                                        const row = e.target.closest('.upgrade-plan-row');
                                        if (row) {
                                            row.classList.remove('upgrade-plan-row--no-systype');
                                            row.classList.remove('upgrade-plan-row--systype-critical');
                                        }
                                        // Persist to the authenticated operator's
                                        // per-user workspace
                                        // (``~/.topology_users/<user>/device_overrides.json``)
                                        // so the next Step-5 open for this same
                                        // user / topology resolves cleanly via
                                        // the override layer instead of falling
                                        // back to the stale SA-* in
                                        // db/devices.json. Scope is attached by
                                        // ``ScalerAPI.persistSystemType`` from
                                        // ``TopologySync.getActive()``. Fire-and
                                        // -forget; the backend is idempotent
                                        // and a failed POST just means we re-
                                        // prompt next time. The live DNOS probe
                                        // continues to auto-heal
                                        // ``operational.json`` / ``db/devices.json``
                                        // (hardware truth) but no longer stomps
                                        // the user's per-topology pick.
                                        try {
                                            const dev = (self.WizardController?.data?.devices || []).find(x => x.id === did);
                                            const sshHost = dev?.ssh_host || dev?.ip || '';
                                            // Cluster picks (CL-*) additionally promote the
                                            // correction into SCALER/db/devices.json with
                                            // provenance ``operator_pinned``. That's the
                                            // file the scaler CLI's plan-builder reads when
                                            // emitting ``request system deploy system-type
                                            // <T> name <N>``, so without this hop the
                                            // deploy command would keep stamping the stale
                                            // NCP-1 ``SA-*`` code that DNAAS inventory
                                            // remembers for a chassis that briefly wore
                                            // this hostname. The backend rejects
                                            // commit_global for non-cluster picks to
                                            // preserve multi-user isolation on the global
                                            // file. See ``devices.py::persist_device_system_type``.
                                            const isClusterPick = String(val || '').toUpperCase().startsWith('CL-');
                                            ScalerAPI.persistSystemType(did, val, sshHost, { commitGlobal: isClusterPick })
                                                .then(r => {
                                                    if (r && r.persisted) {
                                                        const scopeNote = r.topology_id
                                                            ? `user+topology (${r.topology_id})`
                                                            : 'user';
                                                        const pinNote = r.global_pinned
                                                            ? ' + scaler DB (operator_pinned)'
                                                            : '';
                                                        console.info(`[Upgrade] Persisted system_type=${val} for ${did} -> ${scopeNote} override${pinNote}`);
                                                        // Reflect the override on the plan
                                                        // entry so subsequent SSH-verify
                                                        // lifts / row renders don't re-
                                                        // flag the mismatch locally.
                                                        if (plan.devices[did]) {
                                                            plan.devices[did].system_type_override_scope =
                                                                r.scope === 'per_topology' ? 'topology' : 'user';
                                                            if (r.global_pinned) {
                                                                plan.devices[did].system_type_source = 'operator_pinned';
                                                            }
                                                        }
                                                    }
                                                })
                                                .catch(err => {
                                                    console.warn(`[Upgrade] persistSystemType failed for ${did}:`, err && err.message);
                                                });
                                        } catch (_persistExc) {
                                            console.warn('[Upgrade] persistSystemType setup failed:', _persistExc);
                                        }
                                    });
                                });
                                document.getElementById('upgrade-max-concurrent')?.addEventListener('change', (e) => {
                                    const v = parseInt(e.target.value, 10);
                                    if (!isNaN(v) && v >= 1 && v <= 10) {
                                        self.WizardController.data.maxConcurrent = v;
                                    }
                                });

                                // Active-NCC detection for cluster devices. The plan
                                // builder falls back to NCC-0 when neither
                                // `ctx.active_ncc_node` nor the virsh probe have been
                                // seen -- but that's a 50/50 coin flip on a two-NCC
                                // cluster. Live SSH to the KVM host runs
                                // `virsh console` against each NCC; the backend
                                // persists the winner to `operational.json.active_ncc_vm`
                                // which a subsequent `/api/devices/<id>/context` read
                                // re-exposes as `ctx.active_ncc_node`. We trigger it
                                // once per cluster per plan open, and on explicit
                                // user click of the "Detect" link we added next to
                                // the NCC dropdown (see render above).
                                self._nccProbeInFlight = self._nccProbeInFlight || {};
                                // Trust prefixes mirror `_TRUSTED_ACTIVE_NCC_SOURCES`
                                // in `topology/routes/bridge_helpers.py`. A bare
                                // `ctx.active_ncc_vm` with an empty/legacy source
                                // means scaler's raw `connect_for_upgrade` path
                                // overwrote our atomic write and dropped the
                                // provenance -- treat it as un-verified and force
                                // a fresh probe instead of accepting the guess.
                                const _NCC_TRUST_PREFIXES = [
                                    'kvm_', 'virsh_console_verified',
                                    'pre_upgrade_snapshot', 'pre_upgrade_backup',
                                    'scaler_db_cache', 'topology_virsh_probe',
                                    'upgrade_start_snapshot', 'post_reboot_virsh_probe',
                                ];
                                const _isTrustedNccSrc = (s) => {
                                    const v = String(s || '').trim();
                                    if (!v) return false;
                                    return _NCC_TRUST_PREFIXES.some(p => v.startsWith(p));
                                };
                                const _probeActiveNcc = async (did, forceLive = false) => {
                                    if (self._nccProbeInFlight[did]) return;
                                    const dev = (data.devices || []).find(x => x.id === did);
                                    if (!dev) return;
                                    const ctx = data.deviceContexts?.[did] || {};
                                    const vi = dev.sshConfig?._virshInfo || {};
                                    const _haveTrustedNcc = vi.activeNcc
                                        || _isTrustedNccSrc(ctx.active_ncc_source);
                                    if (_haveTrustedNcc && !forceLive) return;
                                    self._nccProbeInFlight[did] = true;
                                    try {
                                        self.WizardController.render();
                                        const ssh = dev.ssh_host || dev.ip || '';
                                        let fresh = null;
                                        const _useOrch = (typeof window !== 'undefined' && window.DeviceState && typeof window.DeviceState.getContext === 'function');
                                        if (!forceLive) {
                                            try {
                                                fresh = _useOrch
                                                    ? await window.DeviceState.getContext(did, { live: false, sshHost: ssh })
                                                    : await ScalerAPI.getDeviceContext(did, false, ssh);
                                            } catch (_) { /* fall through to live */ }
                                        }
                                        const _hasNcc = (c) => !!(c && (c.active_ncc_vm || c.active_ncc_node));
                                        const _hasTrustedNcc = (c) => _hasNcc(c) && _isTrustedNccSrc(c?.active_ncc_source);
                                        // When `forceLive` is set we know the
                                        // prior ctx was untrusted (scaler
                                        // clobber). Re-accept the cached
                                        // value only if it now carries a
                                        // trusted source -- otherwise hit the
                                        // backend live probe which will
                                        // re-run `_cluster_preprobe` and
                                        // re-stamp `kvm_virsh_probe`.
                                        const _needLive = forceLive
                                            ? !_hasTrustedNcc(fresh)
                                            : !_hasNcc(fresh);
                                        if (_needLive) {
                                            fresh = _useOrch
                                                ? await window.DeviceState.getContext(did, { live: true, sshHost: ssh, bypassCache: true })
                                                : await ScalerAPI.getDeviceContext(did, true, ssh);
                                        }
                                        if (_hasNcc(fresh)) {
                                            const merged = { ...ctx, ...fresh, _fetchedAt: Date.now() };
                                            data.deviceContexts = data.deviceContexts || {};
                                            data.deviceContexts[did] = merged;
                                            if (self._deviceContexts) self._deviceContexts[did] = merged;
                                            data._upgradePlan = null;
                                            self.showNotification(
                                                `Active NCC for ${dev.hostname || did}: ${fresh.active_ncc_vm || fresh.active_ncc_node}`,
                                                'info'
                                            );
                                        } else {
                                            self.showNotification(
                                                `Active NCC probe returned no result for ${dev.hostname || did} -- verify manually before Execute.`,
                                                'warning'
                                            );
                                        }
                                    } catch (e) {
                                        self.showNotification(`Active NCC probe failed (${dev.hostname || did}): ${e.message}`, 'warning');
                                    } finally {
                                        delete self._nccProbeInFlight[did];
                                        self.WizardController.render();
                                    }
                                };
                                document.querySelectorAll('[data-action="probe-active-ncc"]').forEach(a => {
                                    a.addEventListener('click', (ev) => {
                                        ev.preventDefault();
                                        _probeActiveNcc(a.dataset.device, /* forceLive */ true);
                                    });
                                });
                                const _deviceIds = data.selectedDeviceIds || [];
                                for (const did of _deviceIds) {
                                    const dev = (data.devices || []).find(x => x.id === did);
                                    if (!dev) continue;
                                    const ctx = data.deviceContexts?.[did] || {};
                                    const sysTypeStr = String(ctx.system_type || dev.platform || '').toUpperCase();
                                    const isCl = sysTypeStr.startsWith('CL-') || ctx.is_cluster;
                                    const vi = dev.sshConfig?._virshInfo || {};
                                    // Auto-probe condition: cluster device that
                                    // doesn't yet have a TRUSTED active-NCC
                                    // signal. We deliberately ignore an
                                    // un-sourced `ctx.active_ncc_vm` here
                                    // because scaler's raw write of
                                    // operational.json drops the source field
                                    // and can clobber a fresh `kvm_virsh_probe`
                                    // result with a guessed "ncc-0" value
                                    // (see DEVELOPMENT_GUIDELINES.md, "Scaler
                                    // raw-write provenance loss").
                                    const haveTrusted = vi.activeNcc
                                        || _isTrustedNccSrc(ctx.active_ncc_source);
                                    if (isCl && !haveTrusted && !self._nccProbeInFlight[did]) {
                                        // If a stale untrusted VM is already
                                        // sitting in ctx (scaler clobber), the
                                        // non-live branch of `_probeActiveNcc`
                                        // would just re-read the same poisoned
                                        // context. Force a live virsh probe so
                                        // the resolver re-stamps `kvm_virsh_probe`
                                        // and the wizard repaints the trusted tag.
                                        const _ctxHasStaleVm = !!(ctx.active_ncc_vm || ctx.active_ncc_node);
                                        _probeActiveNcc(did, /* forceLive */ _ctxHasStaleVm);
                                    }
                                }
                            },
                            collectData: () => {
                                const plan = self.WizardController?.data?._upgradePlan || {};
                                const devices = plan.devices || {};
                                const device_plans = {};
                                document.querySelectorAll('.upgrade-plan-select').forEach(sel => {
                                    const did = sel.dataset.device;
                                    if (did) {
                                        const p = devices[did] || {};
                                        device_plans[did] = {
                                            ...p,
                                            upgrade_type: sel.value,
                                            components: p.components || ['DNOS', 'GI', 'BaseOS'],
                                        };
                                    }
                                });
                                document.querySelectorAll('.upgrade-plan-systype-select').forEach(sel => {
                                    const did = sel.dataset.device;
                                    if (did && sel.value && device_plans[did]) {
                                        device_plans[did].system_type = sel.value;
                                        if (!device_plans[did].deploy_params) device_plans[did].deploy_params = {};
                                        device_plans[did].deploy_params.system_type = sel.value;
                                    }
                                });
                                document.querySelectorAll('.upgrade-plan-ncc-select').forEach(sel => {
                                    const did = sel.dataset.device;
                                    if (did && device_plans[did]) {
                                        const nccVal = parseInt(sel.value, 10);
                                        const vmName = sel.options[sel.selectedIndex]?.dataset?.vm || '';
                                        device_plans[did].ncc_id = isNaN(nccVal) ? 0 : nccVal;
                                        if (!device_plans[did].deploy_params) device_plans[did].deploy_params = {};
                                        device_plans[did].deploy_params.ncc_id = isNaN(nccVal) ? 0 : nccVal;
                                        if (vmName) device_plans[did].deploy_params.selected_ncc_vm = vmName;
                                    }
                                });
                                Object.keys(device_plans).forEach(did => {
                                    const dev = (self.WizardController?.data?.devices || []).find(x => x.id === did) || {};
                                    const label = (dev.hostname || did || '').trim();
                                    if (!/^(YOR[_-]CL[_-])?PE[_-]?4$/i.test(label)) return;
                                    // PE-4 chassis identity guards only. The
                                    // CL-86 system_type + YOR_CL_PE-4 deploy
                                    // name are immutable cluster facts; the
                                    // DNOS deploy command will syntactically
                                    // reject anything else. NEVER silently
                                    // fill ncc_id=1 + pe4_deploy_default --
                                    // that was the 2026-05-12 stuck-in-GI
                                    // root cause.
                                    device_plans[did].system_type = 'CL-86';
                                    device_plans[did].is_cluster = true;
                                    device_plans[did].deploy_params = device_plans[did].deploy_params || {};
                                    device_plans[did].deploy_params.system_type = 'CL-86';
                                    device_plans[did].deploy_params.name = 'YOR_CL_PE-4';
                                    device_plans[did].deploy_params.deploy_name = 'YOR_CL_PE-4';
                                });
                                const maxC = parseInt(document.getElementById('upgrade-max-concurrent')?.value || '3', 10);
                                const missingSysType = Object.entries(device_plans).filter(([_, dp]) => {
                                    const ut = dp.upgrade_type || '';
                                    if (ut === 'blocked') return false;
                                    return !dp.system_type;
                                });
                                if (missingSysType.length > 0) {
                                    const names = missingSysType.map(([id]) => {
                                        const d = (self.WizardController?.data?.devices || []).find(x => x.id === id);
                                        return d?.hostname || id;
                                    }).join(', ');
                                    self.showToast(`Select system type for: ${names}`, 'warning');
                                    return null;
                                }
                                const sysTypeChanges = Object.entries(device_plans).filter(([_, dp]) => {
                                    if ((dp.upgrade_type || '') === 'blocked') return false;
                                    return dp.system_type_category_change;
                                });
                                if (sysTypeChanges.length > 0 && !self.WizardController.data._sysTypeChangeAcknowledged) {
                                    const changeList = sysTypeChanges.map(([id, dp]) => {
                                        const d = (self.WizardController?.data?.devices || []).find(x => x.id === id);
                                        return `${d?.hostname || id}: ${dp.previous_system_type} -> ${dp.system_type}`;
                                    }).join(', ');
                                    self.showToast(
                                        `[WARN] System type category change detected (${changeList}). ` +
                                        'SA<->CL changes require running the cleaner script on ALL NCEs after deploy. ' +
                                        'Click Next again to confirm.',
                                        'warning'
                                    );
                                    self.WizardController.data._sysTypeChangeAcknowledged = true;
                                    return null;
                                }
                                return {
                                    device_plans: device_plans,
                                    maxConcurrent: isNaN(maxC) ? 3 : Math.max(1, Math.min(10, maxC)),
                                };
                            },
                            skipIf: (data) => (!data.selectedBuild && !data._runningBuild) || !(data.selectedDeviceIds || []).length
                        },
                        {
                            title: 'Execute',
                            finalButtonText: 'Start Upgrade',
                            render: (data) => {
                                const devs = (data.devices || []).filter(d => (data.selectedDeviceIds || []).includes(d.id));
                                const sb = data.selectedBuild;
                                const rb = data._runningBuild;
                                const buildWaiting = rb && !sb;
                                const comps = data.components || ['DNOS', 'GI', 'BaseOS'];
                                const status = data.deviceStatus || {};
                                const dnosDevs = devs.filter(d => (status[d.id]?.mode || '').toUpperCase() === 'DNOS');
                                const giDevs = devs.filter(d => (status[d.id]?.mode || '').toUpperCase() === 'GI');
                                const recoveryDevs = devs.filter(d => (status[d.id]?.mode || '').toUpperCase() === 'RECOVERY');
                                const unknownDevs = devs.filter(d => !status[d.id]?.mode || !['DNOS','GI','RECOVERY'].includes((status[d.id]?.mode || '').toUpperCase()));
                                const modeHtml = Object.keys(status).length > 0
                                    ? `<div class="scaler-form-group">
                                        <label>Device modes</label>
                                        ${dnosDevs.length ? `<div class="upgrade-execute-mode-row"><span class="upgrade-mode-badge upgrade-mode-dnos">DNOS</span> Install: ${dnosDevs.map(d => d.hostname || d.id).join(', ')}</div>` : ''}
                                        ${giDevs.length ? `<div class="upgrade-execute-mode-row"><span class="upgrade-mode-badge upgrade-mode-gi">GI</span> Deploy: ${giDevs.map(d => d.hostname || d.id).join(', ')}</div>` : ''}
                                        ${recoveryDevs.length ? `<div class="upgrade-execute-mode-row upgrade-execute-mode-recovery"><span class="upgrade-mode-badge upgrade-mode-recovery">RECOVERY</span> ${recoveryDevs.map(d => d.hostname || d.id).join(', ')} -- run System Restore first</div>` : ''}
                                        ${unknownDevs.length ? `<div class="upgrade-execute-mode-row upgrade-execute-mode-unknown"><span class="upgrade-mode-badge upgrade-mode-loading">?</span> Unknown: ${unknownDevs.map(d => d.hostname || d.id).join(', ')} -- click Refresh in Device Stack above</div>` : ''}
                                    </div>`
                                    : `<div class="scaler-form-group">
                                        <label>Device modes</label>
                                        <div class="upgrade-execute-mode-row upgrade-execute-mode-unknown">Device modes not yet detected. Click <strong>Refresh</strong> in Device Stack panel above to check.</div>
                                    </div>`;
                                const devicePlans = data.device_plans || (data._upgradePlan?.devices ? Object.fromEntries(Object.entries(data._upgradePlan.devices).map(([k, v]) => [k, { ...v }])) : {});
                                const activeDevs = devs.filter(d => {
                                    const dp = devicePlans[d.id];
                                    return !dp || dp.upgrade_type !== 'blocked';
                                });
                                const skippedDevs = devs.filter(d => devicePlans[d.id]?.upgrade_type === 'blocked');
                                const _typeLabel = (t) => ({ normal: 'Normal', delete_deploy: 'Delete+Deploy', gi_deploy: 'GI Deploy', blocked: 'Skip' }[t] || t || 'Normal');
                                const _typeCls = (t) => t === 'delete_deploy' ? 'upgrade-exec-type--dd' : t === 'gi_deploy' ? 'upgrade-exec-type--gi' : '';
                                const planRows = activeDevs.map(d => {
                                    const dp = devicePlans[d.id] || {};
                                    const ut = dp.upgrade_type || 'normal';
                                    const m = (status[d.id]?.mode || '').toUpperCase();
                                    const modeBadge = m ? `<span class="upgrade-mode-badge upgrade-mode-${m.toLowerCase()}">${m}</span>` : '';
                                    const _st = dp.system_type || '';
                                    const _stTag = _st ? ` <span style="font-size:10px;opacity:0.6">[${_st}]</span>` : '';
                                    return `<tr>
                                        <td class="upgrade-exec-device">${d.hostname || d.id}${_stTag} ${modeBadge}</td>
                                        <td class="upgrade-exec-type ${_typeCls(ut)}">${_typeLabel(ut)}</td>
                                    </tr>`;
                                }).join('');
                                const planTableHtml = activeDevs.length ? `<div class="scaler-form-group">
                                    <label>Upgrade plan (${activeDevs.length} device${activeDevs.length > 1 ? 's' : ''})</label>
                                    <table class="upgrade-exec-plan-table">
                                        <thead><tr><th>Device</th><th>Type</th></tr></thead>
                                        <tbody>${planRows}</tbody>
                                    </table>
                                    ${skippedDevs.length ? `<div class="upgrade-exec-skipped">Skipped: ${skippedDevs.map(d => d.hostname || d.id).join(', ')}</div>` : ''}
                                </div>` : '';
                                const hasDD = activeDevs.some(d => (devicePlans[d.id]?.upgrade_type) === 'delete_deploy');
                                const allCompsRequired = hasDD;
                                const compNotes = {};
                                if (hasDD) {
                                    compNotes['DNOS'] = 'Required for Delete+Deploy';
                                    compNotes['GI'] = 'Required for Delete+Deploy';
                                    compNotes['BaseOS'] = 'Required for Delete+Deploy';
                                }
                                return `<div class="scaler-form">
                                    <div class="scaler-info-box">Review and start upgrade.</div>
                                    <div class="scaler-form-group">
                                        <label>Target</label>
                                        <div class="upgrade-execute-summary">${sb ? `Build #${sb.build_number} (${data.branch || ''})` : (rb ? `Build #${rb.build_number} (${data.branch || ''}) -- building` : (data._targetVersion ? `${data._targetVersion} (${data.branch || ''})` : '--'))}</div>
                                    </div>
                                    ${planTableHtml}
                                    ${modeHtml}
                                    <div class="scaler-form-group">
                                        <label>Components</label>
                                        <div class="scaler-checkbox-list">
                                            ${['DNOS', 'GI', 'BaseOS'].map(c => {
                                                const locked = allCompsRequired;
                                                const note = compNotes[c] || '';
                                                return `<label class="scaler-checkbox-item${locked ? ' scaler-checkbox-locked' : ''}">
                                                    <input type="checkbox" value="${c}" checked ${locked ? 'disabled' : ''}>
                                                    ${c}${note ? `<span class="upgrade-comp-note">${note}</span>` : ''}
                                                </label>`;
                                            }).join('')}
                                        </div>
                                    </div>
                                    <div class="scaler-form-group">
                                        <label>CLI-equivalent flow</label>
                                        <pre class="scaler-syntax-preview upgrade-cli-preview">${activeDevs.map(d => {
                                            const dp = devicePlans[d.id] || {};
                                            const ut = dp.upgrade_type || 'normal';
                                            const m = (status[d.id]?.mode || '').toUpperCase();
                                            const _sysLabel = dp.system_type || '';
                                            if (ut === 'delete_deploy') {
                                                let extra = _sysLabel ? ` system-type ${_sysLabel}` : '';
                                                if (dp.is_cluster) {
                                                    const _selNcc = dp.ncc_id ?? dp.deploy_params?.ncc_id ?? 'auto';
                                                    const _selVm = dp.selected_ncc_vm || dp.deploy_params?.selected_ncc_vm || '';
                                                    extra += ` ncc-id ${_selNcc}${_selVm ? ' (' + _selVm + ')' : ''}`;
                                                }
                                                return `${d.hostname || d.id}: request system delete -> load 3 tarballs (GI) -> deploy${extra}`;
                                            }
                                            if (ut === 'gi_deploy') {
                                                let extra = _sysLabel ? ` system-type ${_sysLabel}` : '';
                                                if (dp.is_cluster) {
                                                    const _selNcc = dp.ncc_id ?? dp.deploy_params?.ncc_id ?? 'auto';
                                                    const _selVm = dp.selected_ncc_vm || dp.deploy_params?.selected_ncc_vm || '';
                                                    extra += ` ncc-id ${_selNcc}${_selVm ? ' (' + _selVm + ')' : ''}`;
                                                }
                                                return `${d.hostname || d.id}: request system deploy${extra} name ${d.hostname || d.id}`;
                                            }
                                            const phases = [];
                                            if (comps.includes('DNOS')) phases.push(m === 'DNOS' ? 'load + install' : m === 'GI' ? 'deploy' : '?');
                                            if (comps.includes('GI') && m === 'GI') phases.push('deploy');
                                            if (comps.includes('BaseOS')) phases.push('baseos');
                                            return `${d.hostname || d.id}: ${phases.join(', ') || 'check status'}`;
                                        }).join('\n')}</pre>
                                    </div>
                                    ${buildWaiting ? `<div class="scaler-info-box upgrade-exec-waiting" style="border-color:var(--dn-cyan,#00bcd4);color:var(--dn-cyan,#00bcd4);margin-top:12px;padding:12px" id="upgrade-exec-wait-banner">
                                        <div style="font-weight:600;margin-bottom:4px">Build #${rb.build_number} still running</div>
                                        <div id="upgrade-exec-wait-timer" style="font-size:0.92em">Started ${rb.ageMin}m ago -- will auto-push when ready</div>
                                        <div style="font-size:0.85em;margin-top:6px;opacity:0.85">Polling every 15s. Start Upgrade will enable when build completes.</div>
                                    </div>` : ''}
                                </div>`;
                            },
                            afterRender: (data) => {
                                const rb = data._runningBuild;
                                const sb = data.selectedBuild;
                                const buildWaiting = rb && !sb;
                                if (buildWaiting) {
                                    const nextBtn = document.querySelector('#wizard-next');
                                    if (nextBtn) {
                                        nextBtn.disabled = true;
                                        nextBtn.textContent = 'Waiting for build...';
                                    }
                                    const pollId = Date.now();
                                    self._execPollId = pollId;
                                    const pollBuild = async () => {
                                        if (self._execPollId !== pollId) return;
                                        const wc = self.WizardController;
                                        if (!wc || !wc.data._runningBuild) return;
                                        if (wc.currentStep !== wc.steps.findIndex(s => s.title === 'Execute')) return;
                                        const branch = wc.data.branch || '';
                                        if (!branch) return;
                                        try {
                                            const st = await ScalerAPI.getUpgradeBuildStatus(branch, true);
                                            if (self._execPollId !== pollId) return;
                                            if (!st.building) {
                                                if (st.result !== 'SUCCESS') {
                                                    wc.data._runningBuild = null;
                                                    wc.data._runningBuildCheckedBranch = null;
                                                    wc.render();
                                                    self.showNotification(`Build #${rb.build_number} finished with ${st.result || 'UNKNOWN'} -- select a build manually`, 'warning');
                                                    return;
                                                }
                                                try {
                                                    const stack = await ScalerAPI.getBuildStack(branch, rb.build_number);
                                                    if (stack && stack.dnos_url) {
                                                        wc.data.selectedBuild = {
                                                            build_number: rb.build_number,
                                                            display_name: `#${rb.build_number}`,
                                                            dnos_url: stack.dnos_url || '', gi_url: stack.gi_url || '', baseos_url: stack.baseos_url || '',
                                                            is_sanitizer: false, result: 'SUCCESS',
                                                            has_dnos: !!stack.dnos_url, has_gi: !!stack.gi_url, has_baseos: !!stack.baseos_url,
                                                        };
                                                        wc.data._runningBuild = null;
                                                        wc.data._runningBuildCheckedBranch = null;
                                                        wc.render();
                                                        self.showNotification(`Build #${rb.build_number} ready -- click Start Upgrade`, 'success');
                                                        return;
                                                    }
                                                } catch (_) {}
                                                wc.data._runningBuild = null;
                                                wc.data._runningBuildCheckedBranch = null;
                                                wc.render();
                                                self.showNotification(`Build #${rb.build_number} finished -- fetch builds to select`, 'warning');
                                                return;
                                            }
                                            const ageMin = Math.round((st.age_hours || 0) * 60);
                                            const timerEl = document.getElementById('upgrade-exec-wait-timer');
                                            if (timerEl) timerEl.textContent = `Started ${ageMin}m ago -- will auto-push when ready`;
                                            setTimeout(pollBuild, 15000);
                                        } catch (_) {
                                            if (self._execPollId === pollId) setTimeout(pollBuild, 15000);
                                        }
                                    };
                                    setTimeout(pollBuild, 15000);
                                }
                                document.querySelectorAll('.scaler-checkbox-list input[value="DNOS"], .scaler-checkbox-list input[value="GI"], .scaler-checkbox-list input[value="BaseOS"]').forEach(cb => {
                                    cb.onchange = () => {
                                        const comps = Array.from(document.querySelectorAll('.scaler-checkbox-list input[value="DNOS"], .scaler-checkbox-list input[value="GI"], .scaler-checkbox-list input[value="BaseOS"]'))
                                            .filter(c => c.checked).map(c => c.value);
                                        self.WizardController.data.components = comps;
                                    };
                                });
                            },
                            collectData: () => ({
                                components: Array.from(document.querySelectorAll('.scaler-checkbox-list input[value="DNOS"], .scaler-checkbox-list input[value="GI"], .scaler-checkbox-list input[value="BaseOS"]'))
                                    .filter(c => c.checked).map(c => c.value),
                            }),
                            validate: (data) => {
                                if (!data.selectedBuild) { self.showNotification('Select a build in the Build step first', 'warning'); return false; }
                                const comps = data.components || [];
                                if (comps.length === 0) { self.showNotification('Select at least one component', 'warning'); return false; }
                                return true;
                            }
                        }
                    ],
                    onComplete: async (data) => {
                        let branch = data.branch || '';
                        if (data._resolveUrl && branch.startsWith('http')) {
                            try {
                                const r = await ScalerAPI.resolveJenkinsUrl(branch);
                                branch = r.branch || branch;
                            } catch (e) {
                                self.showNotification(`Resolve failed: ${e.message}`, 'error');
                                return;
                            }
                        }
                        const allDeviceIds = data.selectedDeviceIds || [];
                        const components = data.components || ['DNOS', 'GI', 'BaseOS'];
                        const selectedBuild = data.selectedBuild;
        
                        const planData = self.WizardController?.data;
                        const device_plans = planData?.device_plans || planData?._upgradePlan?.devices || {};
                        const deviceIds = allDeviceIds.filter(did => (device_plans[did]?.upgrade_type || 'normal') !== 'blocked');
        
                        const sshHosts = {};
                        for (const d of (data.devices || [])) {
                            if (deviceIds.includes(d.id)) {
                                sshHosts[d.id] = d.ssh_host || d.ip || '';
                            }
                        }
        
                        if (deviceIds.length === 0) {
                            self.showNotification('No devices to upgrade (all blocked/skipped)', 'warning');
                            return;
                        }
        
                        // Pre-flight trust gate for destructive upgrades.
                        // Mirrors the backend
                        // `_assert_active_ncc_trusted_for_destructive_op`
                        // helper so the operator gets an immediate
                        // "click Re-detect first" prompt rather than a
                        // round-trip 412 from the server. The trust
                        // prefix list MUST match
                        // `_NCC_TRUST_PREFIXES` in this file (and
                        // `_TRUSTED_ACTIVE_NCC_SOURCES` in
                        // `routes/bridge_helpers.py`).
                        const _UPG_TRUST_PREFIXES = [
                            'kvm_', 'virsh_console_verified',
                            'pre_upgrade_snapshot', 'pre_upgrade_backup',
                            'scaler_db_cache', 'topology_virsh_probe',
                            'upgrade_start_snapshot', 'post_reboot_virsh_probe',
                        ];
                        const _isTrustedUpgSrc = (s) => {
                            const v = String(s || '').trim();
                            return !!v && _UPG_TRUST_PREFIXES.some(p => v.startsWith(p));
                        };
                        const _untrustedDevs = [];
                        for (const _did of deviceIds) {
                            const _plan = device_plans[_did] || {};
                            const _type = String(_plan.upgrade_type || 'normal').toLowerCase();
                            if (_type !== 'delete_deploy' && _type !== 'gi_deploy') continue;
                            const _sys = String(_plan.system_type
                                || _plan.deploy_params?.system_type || '').toUpperCase();
                            const _isCluster = _plan.is_cluster || _sys.startsWith('CL-');
                            if (!_isCluster) continue;
                            const _src = String(_plan.active_ncc_source
                                || _plan.deploy_params?.active_ncc_source || '').trim();
                            if (!_isTrustedUpgSrc(_src)) {
                                _untrustedDevs.push(`${_did} (active_ncc_source=${_src || 'empty'})`);
                            }
                        }
                        if (_untrustedDevs.length > 0) {
                            self.showNotification(
                                `Refusing destructive upgrade for cluster device(s): ${_untrustedDevs.join(', ')}. `
                                + `Click "Re-detect" next to each device in the plan to refresh the live `
                                + `Active-NCC probe, then retry. (Background: \`request system delete\` reboots `
                                + `one NCC and the cluster fails over to the other -- without a trusted live `
                                + `snapshot the deploy targets the wrong NCC. See 2026-05-12 incident.)`,
                                'error', 12000);
                            return;
                        }
        
                        try {
                            let stack;
                            if (data._directUrls && data.dnosUrl) {
                                stack = { dnos_url: data.dnosUrl, gi_url: data.giUrl || '', baseos_url: data.baseosUrl || '' };
                            } else {
                                stack = await ScalerAPI.getBuildStack(branch, selectedBuild.build_number);
                            }
                            // Check if URLs are actually populated
                            const _urlsMissing = !stack.dnos_url && !stack.gi_url && !stack.baseos_url;
                            let _urlsInvalid = [];
                            if (stack.url_status) {
                                _urlsInvalid = Object.entries(stack.url_status)
                                    .filter(([, v]) => v && !v.valid)
                                    .map(([k, v]) => `${k.toUpperCase()}: ${v.status || 'unavailable'}`);
                            }
                            if (_urlsMissing || _urlsInvalid.length > 0) {
                                const reason = _urlsMissing
                                    ? 'No image URLs found -- artifacts expired'
                                    : `Images not accessible: ${_urlsInvalid.join(', ')}`;
                                if (data.selectedBuild) {
                                    data.selectedBuild._urlsExpired = true;
                                    data.selectedBuild._urlsVerified = true;
                                    data.selectedBuild._invalidComps = _urlsInvalid.map(s => s.split(':')[0]);
                                }
                                data._triggerPanelOpen = true;
                                self.showNotification(
                                    `${reason}. Returning to Source step -- trigger a new build.`,
                                    'error', 8000);
                                self.WizardController.goTo(1);
                                return;
                            }
                            const max_concurrent = planData?.maxConcurrent ?? 3;
                            const result = await ScalerAPI.imageUpgrade({
                                device_ids: deviceIds,
                                ssh_hosts: sshHosts,
                                branch: branch,
                                build_number: selectedBuild?.build_number,
                                components: components,
                                upgrade_type: 'normal',
                                device_plans: device_plans,
                                max_concurrent: max_concurrent,
                                dnos_url: stack.dnos_url,
                                gi_url: stack.gi_url,
                                baseos_url: stack.baseos_url,
                                is_sanitizer: selectedBuild.is_sanitizer,
                                parallel: true
                            });
                            self.closePanel('upgrade-wizard');
                            try {
                                localStorage.setItem('scaler_active_upgrade', JSON.stringify({
                                    job_id: result.job_id,
                                    job_name: `Upgrading ${deviceIds.length} devices`,
                                    devices: deviceIds,
                                    ssh_hosts: sshHosts,
                                    started_at: Date.now()
                                }));
                            } catch (_) {}
                            const editor = window.topologyEditor;
                            if (editor?.objects) {
                                const upgradeSet = new Set(deviceIds);
                                editor.objects.forEach(o => {
                                    if (o.type === 'device' && upgradeSet.has(o.label?.trim())) o._upgradeInProgress = true;
                                });
                            }
                            window.dispatchEvent(new CustomEvent('device:upgrade-started', {
                                detail: { jobId: result.job_id, devices: deviceIds }
                            }));
                            self.showProgress(result.job_id, `Upgrading ${deviceIds.length} devices`, {
                                upgradeDevices: deviceIds,
                                upgradeSshHosts: sshHosts,
                                onComplete: () => {
                                    if (editor?.objects) {
                                        editor.objects.forEach(o => { if (o.type === 'device') o._upgradeInProgress = false; });
                                    }
                                }
                            });
                        } catch (e) {
                            self.showNotification(`Upgrade failed: ${e.message}`, 'error');
                        }
                    }
                });
        
                ScalerAPI.getDevices().then(result => {
                    self._mergeWizardDeviceListFromApi(devices, result.devices || []);
                    if (self.WizardController?.data && self.WizardController.panelName === 'upgrade-wizard') {
                        self.WizardController.data.devices = devices;
                        for (const d of devices) {
                            const st = self._sanitizeWizardSystemType(d.platform || '');
                            if (!st) continue;
                            const ctx = self.WizardController.data.deviceContexts[d.id];
                            if (ctx) ctx.system_type = st;
                        }
                        self.WizardController.data._upgradePlan = null;
                        self.WizardController.render();
                    }
                }).catch(() => {});
        
                if (skipToStep > 0 && skipToStep < this.WizardController.steps.length) {
                    this.WizardController.currentStep = skipToStep;
                    this.WizardController._highestStepReached = skipToStep;
                    this.WizardController.render();
                }
        
                // Two-phase background refresh:
                // Phase 1 (fast): cached-only from operational.json (~100ms per device)
                // Phase 2 (slow): live SSH for definitive mode + install status
                const devicesWithIp = devices.filter(d => d.ssh_host || d.ip);
                if (devicesWithIp.length > 0) {
                    const ids = devicesWithIp.map(d => d.id);
                    const sshHosts = {};
                    devicesWithIp.forEach(d => { sshHosts[d.id] = d.ssh_host || d.ip || ''; });
                    ScalerAPI.getUpgradeDeviceStatus(ids, sshHosts, false).then(liveResult => {
                        // Propagate authoritative live-SSH mode back to the canvas monitor so
                        // stale _deviceMode doesn't mislead other UI surfaces (canvas badges,
                        // context menu gating, etc.). This is the most accurate source we have.
                        const liveDevices = liveResult.devices || {};
                        const _validModes = ['GI', 'DNOS', 'RECOVERY', 'BASEOS_SHELL', 'ONIE', 'UPGRADING', 'DEPLOYING'];
                        for (const [did, liveSt] of Object.entries(liveDevices)) {
                            const dev = devices.find(x => x.id === did);
                            if (!dev) continue;
                            const newMode = (liveSt.mode || '').toUpperCase();
                            if (newMode && _validModes.includes(newMode) && dev._deviceMode !== newMode) {
                                const prevMode = dev._deviceMode;
                                dev._deviceMode = newMode;
                                try {
                                    window.dispatchEvent(new CustomEvent('device:mode-changed', {
                                        detail: { deviceId: did, device: dev, mode: newMode, prevMode }
                                    }));
                                } catch (_) {}
                            }
                        }
                        if (self.WizardController?.panelName === 'upgrade-wizard') {
                            const wd = self.WizardController.data;
                            wd.deviceStatus = wd.deviceStatus || {};
                            // 2026-05-12 cluster-fallback: when the Phase 2 live
                            // SSH probe returns an empty / inconclusive payload
                            // (mode "" or "?" AND no version fields populated),
                            // PRESERVE the Phase 1 cached row instead of letting
                            // the live result clobber a known-good cached
                            // device_state. This was the silent failure that
                            // produced the bug screenshot's "Mode = ?, DNOS = -"
                            // for PE-4: Phase 1 read operational.json and got
                            // DNOS + full stack versions, then Phase 2's slow
                            // virsh-fallback path either timed out or returned
                            // partial output, and the wizard re-rendered with
                            // the live row overwriting the cached row. The
                            // guard below keeps cache when live is empty,
                            // merges otherwise.
                            for (const [_did, liveSt] of Object.entries(liveDevices)) {
                                const prev = wd.deviceStatus[_did] || {};
                                const _liveMode = String(liveSt?.mode || '').trim();
                                const _liveModeBlank = !_liveMode || _liveMode === '?' || _liveMode === '...';
                                const _liveVerBlank = !((liveSt?.dnos_ver || '').trim() && (liveSt?.dnos_ver || '').trim() !== '-')
                                    && !((liveSt?.gi_ver || '').trim() && (liveSt?.gi_ver || '').trim() !== '-')
                                    && !((liveSt?.baseos_ver || '').trim() && (liveSt?.baseos_ver || '').trim() !== '-');
                                const _prevMode = String(prev?.mode || '').trim();
                                const _prevModeKnown = _prevMode && _prevMode !== '?' && _prevMode !== '...';
                                const _prevVerKnown = ((prev?.dnos_ver || '').trim() && (prev?.dnos_ver || '').trim() !== '-')
                                    || ((prev?.gi_ver || '').trim() && (prev?.gi_ver || '').trim() !== '-');
                                if (_liveModeBlank && _liveVerBlank && (_prevModeKnown || _prevVerKnown)) {
                                    // Keep cached row; just stamp a hint so the
                                    // operator knows the live probe couldn't
                                    // confirm. The Device Stack badge still
                                    // shows the cached mode so the row no
                                    // longer "regresses to dashes".
                                    wd.deviceStatus[_did] = {
                                        ...prev,
                                        _live_probe_empty: true,
                                        install_status: prev.install_status || 'Live probe unreachable (using cache)'
                                    };
                                } else {
                                    wd.deviceStatus[_did] = { ...prev, ...liveSt };
                                }
                            }
                            self.WizardController.render();
                        }
                    }).catch(e => console.warn('[ScalerGUI] live device status failed:', e.message));
                }
            } catch (e) {
                const panel = this.state.activePanels['upgrade-wizard'];
                if (panel) {
                    const cd = panel.querySelector('.scaler-panel-content');
                    if (cd) cd.innerHTML = `<div class="scaler-error">${e.message}</div>`;
                }
            }
        },
        
        // =========================================================================
        // SCALE WIZARD (WizardController, 3 steps)
        // =========================================================================
        
        async openScaleWizard() {
            const content = document.createElement('div');
            content.innerHTML = '<div class="scaler-loading">Loading devices...</div>';
            this.openPanel('scale-wizard', 'Scale Up/Down Wizard', content, {
                width: '540px',
                parentPanel: 'scaler-menu'
            });
        
            try {
                const devices = await this._getWizardDeviceList();
                if (devices.length === 0) {
                    content.innerHTML = '<div class="scaler-info-box" style="color:var(--dn-orange,#e67e22)">Add devices to the topology first. No devices on canvas.</div>';
                    return;
                }
        
                const deviceContexts = {};
                const _useOrch = (typeof window !== 'undefined' && window.DeviceState && typeof window.DeviceState.getContext === 'function');
                for (const d of devices) {
                    try {
                        deviceContexts[d.id] = _useOrch
                            ? await window.DeviceState.getContext(d.id, { live: false, sshHost: d.ssh_host || d.ip })
                            : await ScalerAPI.getDeviceContext(d.id, false, d.ssh_host || d.ip);
                    } catch (_) {
                        deviceContexts[d.id] = {};
                    }
                }
        
                const self = this;
                const scaleDevicesWithSsh = devices.filter(d => d.hasSSH);
                this.WizardController.init({
                    panelName: 'scale-wizard',
                    title: 'Scale Up/Down Wizard',
                    initialData: {
                        devices,
                        deviceContexts,
                        selectedDeviceIds: scaleDevicesWithSsh.map(d => d.id),
                        operation: 'down',
                        serviceType: 'fxc',
                        rangeSpec: 'last 100',
                        includeInterfaces: true
                    },
                    wizardHeader: (data) => {
                        const devs = (data.devices || []).filter(d => (data.selectedDeviceIds || []).includes(d.id));
                        if (devs.length === 0) return null;
                        const scaleRows = devs.map(d => {
                            const ctx = data.deviceContexts?.[d.id] || {};
                            const svc = ctx.services || {};
                            const cfg = ctx.config_summary || {};
                            const evpn = cfg.evpn_services || {};
                            const evpnCount = typeof evpn === 'object' && evpn !== null ? Object.values(evpn).reduce((a, v) => a + (typeof v === 'number' ? v : 0), 0) : 0;
                            const fxc = svc.fxc_count || 0;
                            const vrf = svc.vrf_count || 0;
                            const ifc = ctx.interfaces || {};
                            const totalIfs = (ifc.physical?.length || 0) + (ifc.bundle?.length || 0) + (ifc.subinterface?.length || 0);
                            return `<tr><td>${d.hostname || d.id}</td><td>${fxc}</td><td>--</td><td>${evpnCount}</td><td>--</td><td>${vrf}</td><td>${totalIfs}</td></tr>`;
                        }).join('');
                        const suggestions = [];
                        devs.forEach(d => {
                            const ctx = data.deviceContexts?.[d.id] || {};
                            (ctx.scale_suggestions || []).slice(0, 2).forEach(s => {
                                const desc = (s.description || s.type || '').replace(/\[.*?\]/g, '').trim().slice(0, 40);
                                if (desc) suggestions.push({ device: d.hostname || d.id, desc });
                            });
                        });
                        const suggRows = suggestions.length > 0 ? suggestions.map(s => `<tr><td>${s.device}</td><td style="font-size:0.85em">${s.desc}</td></tr>`).join('') : '<tr><td colspan="2" style="color:#888;font-size:0.85em">No suggestions</td></tr>';
                        const div = document.createElement('div');
                        div.className = 'scaler-context-panel';
                        div.innerHTML = `<div class="scaler-context-title scaler-collapse-toggle" data-target="scale-current-table" style="display:flex;justify-content:space-between;align-items:center;cursor:pointer">
                            <span>Current Scale</span>
                            <span class="scaler-collapse-icon">-</span>
                        </div>
                        <div id="scale-current-table" class="scaler-collapse-section">
                            <table style="width:100%;font-size:0.85em"><thead><tr style="color:#888"><th>Device</th><th>FXC</th><th>L2VPN</th><th>EVPN</th><th>VPWS</th><th>VRF</th><th>IFs</th></tr></thead><tbody>${scaleRows}</tbody></table>
                        </div>
                        <div class="scaler-context-title" style="display:flex;justify-content:space-between;align-items:center;margin-top:8px">
                            <span>Scale suggestions</span>
                            <button type="button" class="scaler-btn scaler-btn-sm" id="scale-ctx-refresh">Refresh</button>
                        </div>
                            <table style="width:100%;font-size:0.85em"><thead><tr style="color:#888"><th>Device</th><th>Suggestion</th></tr></thead><tbody>${suggRows}</tbody></table>`;
                        div.querySelector('.scaler-collapse-toggle')?.addEventListener('click', () => {
                            const target = document.getElementById('scale-current-table');
                            const icon = div.querySelector('.scaler-collapse-icon');
                            if (target && icon) {
                                target.classList.toggle('collapsed');
                                icon.textContent = target.classList.contains('collapsed') ? '+' : '-';
                            }
                        });
                        div.querySelector('#scale-ctx-refresh')?.addEventListener('click', async () => {
                            const wd = self.WizardController.data;
                            const ids = wd.selectedDeviceIds || [];
                            const devs = wd.devices || [];
                            const _useOrch = (typeof window !== 'undefined' && window.DeviceState && typeof window.DeviceState.getContext === 'function');
                            for (const id of ids) {
                                const d = devs.find(x => x.id === id);
                                if (d) {
                                    try {
                                        const c = _useOrch
                                            ? await window.DeviceState.getContext(id, { live: true, sshHost: d.ssh_host || d.ip, bypassCache: true })
                                            : await ScalerAPI.getDeviceContext(id, true, d.ssh_host || d.ip);
                                        wd.deviceContexts = wd.deviceContexts || {};
                                        wd.deviceContexts[id] = c;
                                    } catch (_) {}
                                }
                            }
                            self.WizardController.render();
                        });
                        return div;
                    },
                    steps: [
                        {
                            title: 'Devices',
                            render: (data) => {
                                const devs = data.devices || [];
                                const withSsh = devs.filter(d => d.hasSSH);
                                const noSsh = devs.filter(d => !d.hasSSH);
                                const renderDev = (d, disabled) => {
                                    const sel = (data.selectedDeviceIds || []).includes(d.id);
                                    return `<label class="scaler-checkbox-item"${disabled ? ' style="opacity:0.5">' : '>'}>
                                        <input type="checkbox" value="${d.id}" ${sel ? 'checked' : ''}${disabled ? ' disabled' : ''}>
                                        <span>${d.hostname || d.id}${disabled ? ' (no SSH)' : ''}</span>
                                    </label>`;
                                };
                                return `<div class="scaler-form">
                                    <div class="scaler-info-box">Select devices for scale operation. Devices without SSH are excluded.</div>
                                    <div class="scaler-form-group">
                                        <label>Devices</label>
                                        <div id="scale-devices" class="scaler-checkbox-list">
                                            ${withSsh.map(d => renderDev(d, false)).join('')}
                                            ${noSsh.length ? `<div class="scaler-device-select-separator" style="margin-top:8px">No SSH configured</div>${noSsh.map(d => renderDev(d, true)).join('')}` : ''}
                                        </div>
                                    </div>
                                </div>`;
                            },
                            collectData: () => ({
                                selectedDeviceIds: self._getCheckedDeviceIds('scale-devices')
                            }),
                            validate: (data) => {
                                if ((data.selectedDeviceIds || []).length === 0) {
                                    self.showNotification('Select at least one device', 'warning');
                                    return false;
                                }
                                return true;
                            }
                        },
                        {
                            title: 'Scale',
                            render: (data) => {
                                return `<div class="scaler-form">
                                    <div class="scaler-info-box">Bulk add or delete services with correlated interfaces.</div>
                                    <div class="scaler-form-row">
                                        <div class="scaler-form-group">
                                            <label>Operation</label>
                                            <select id="scale-op" class="scaler-select">
                                                <option value="down" ${(data.operation || 'down') === 'down' ? 'selected' : ''}>Scale DOWN (Delete)</option>
                                                <option value="up" ${data.operation === 'up' ? 'selected' : ''}>Scale UP (Add)</option>
                                            </select>
                                        </div>
                                        <div class="scaler-form-group">
                                            <label>Service Type</label>
                                            <select id="scale-type" class="scaler-select">
                                                <option value="fxc" ${(data.serviceType || 'fxc') === 'fxc' ? 'selected' : ''}>FXC</option>
                                                <option value="l2vpn" ${data.serviceType === 'l2vpn' ? 'selected' : ''}>L2VPN</option>
                                                <option value="evpn" ${data.serviceType === 'evpn' ? 'selected' : ''}>EVPN</option>
                                                <option value="vpws" ${data.serviceType === 'vpws' ? 'selected' : ''}>VPWS</option>
                                                <option value="vrf" ${data.serviceType === 'vrf' ? 'selected' : ''}>VRF</option>
                                                <option value="flowspec-vpn" ${data.serviceType === 'flowspec-vpn' ? 'selected' : ''}>FlowSpec VPN</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="scaler-form-group">
                                        <label>Range Specification</label>
                                        <input type="text" id="scale-range" class="scaler-input" value="${data.rangeSpec || 'last 100'}" placeholder="last 100, or 100-400, or 1,2,3">
                                        <small class="scaler-form-hint">Examples: "last 300", "100-400", "1,2,50,100"</small>
                                    </div>
                                    <div class="scaler-form-group">
                                        <label><input type="checkbox" id="scale-interfaces" ${data.includeInterfaces !== false ? 'checked' : ''}> Include correlated interfaces (PWHE, sub-interfaces)</label>
                                    </div>
                                    <div class="scaler-form-group">
                                        <button type="button" class="scaler-btn scaler-btn-sm" id="scale-detect-suggestions">Detect suggestions</button>
                                    </div>
                                </div>`;
                            },
                            afterRender: (data) => {
                                document.getElementById('scale-detect-suggestions')?.addEventListener('click', async () => {
                                    const ids = data.selectedDeviceIds || [];
                                    if (ids.length === 0) { self.showNotification('Select devices in step 1 first', 'warning'); return; }
                                    const btn = document.getElementById('scale-detect-suggestions');
                                    if (btn) { btn.disabled = true; btn.textContent = '...'; }
                                    try {
                                        const r = await ScalerAPI.detectScaleSuggestions({ device_ids: ids });
                                        const sugg = r?.suggestions || r?.scale_suggestions || [];
                                        if (sugg.length > 0) {
                                            const first = sugg[0];
                                            if (first.service_type) document.getElementById('scale-type').value = first.service_type;
                                            if (first.range_spec) document.getElementById('scale-range').value = first.range_spec;
                                            self.WizardController.data.serviceType = first.service_type || data.serviceType;
                                            self.WizardController.data.rangeSpec = first.range_spec || data.rangeSpec;
                                            self.showNotification(`Loaded ${sugg.length} suggestion(s)`, 'info');
                                        } else {
                                            self.showNotification('No scale suggestions detected', 'info');
                                        }
                                    } catch (e) {
                                        self.showNotification(`Detect failed: ${e.message}`, 'error');
                                    } finally {
                                        if (btn) { btn.disabled = false; btn.textContent = 'Detect suggestions'; }
                                    }
                                });
                            },
                            collectData: () => ({
                                operation: document.getElementById('scale-op')?.value || 'down',
                                serviceType: document.getElementById('scale-type')?.value || 'fxc',
                                rangeSpec: document.getElementById('scale-range')?.value || 'last 100',
                                includeInterfaces: document.getElementById('scale-interfaces')?.checked !== false
                            }),
                            validate: (data) => (data.selectedDeviceIds || []).length > 0
                        },
                        {
                            title: 'Review',
                            finalButtonText: 'Execute',
                            render: (data) => {
                                const ids = data.selectedDeviceIds || [];
                                const devs = (data.devices || []).filter(d => ids.includes(d.id));
                                const preview = data._scalePreview || null;
                                const previewHtml = preview ? `<div class="scaler-form-group" style="margin-top:12px">
                                    <label>Preview (dry run)</label>
                                    <pre class="scaler-syntax-preview" style="max-height:180px;overflow:auto;font-size:0.85em">${(preview.terminal_lines || []).join('\n')}</pre>
                                </div>` : '';
                                return `<div class="scaler-form">
                                    <div class="scaler-info-box">Review and execute scale operation.</div>
                                    <div class="scaler-form-group">
                                        <label>Devices (${devs.length})</label>
                                        <div style="font-size:0.9em">${devs.map(d => d.hostname || d.id).join(', ')}</div>
                                    </div>
                                    <div class="scaler-form-group">
                                        <label>Operation</label>
                                        <div style="font-size:0.9em">${data.operation || 'down'} ${data.serviceType || 'fxc'}</div>
                                    </div>
                                    <div class="scaler-form-group">
                                        <label>Range</label>
                                        <div style="font-size:0.9em">${data.rangeSpec || 'last 100'}</div>
                                    </div>
                                    <div class="scaler-form-group">
                                        <label>Include interfaces</label>
                                        <div style="font-size:0.9em">${data.includeInterfaces !== false ? 'Yes' : 'No'}</div>
                                    </div>
                                    <div class="scaler-form-group">
                                        <button type="button" class="scaler-btn scaler-btn-sm" id="scale-show-preview">Show detailed commands</button>
                                    </div>
                                    ${previewHtml}
                                </div>`;
                            },
                            afterRender: (data) => {
                                document.getElementById('scale-show-preview')?.addEventListener('click', async () => {
                                    const btn = document.getElementById('scale-show-preview');
                                    if (!btn) return;
                                    btn.disabled = true;
                                    btn.textContent = 'Loading...';
                                    try {
                                        const result = await ScalerAPI.scaleUpDown({
                                            device_ids: data.selectedDeviceIds || [],
                                            operation: data.operation || 'down',
                                            service_type: data.serviceType || 'fxc',
                                            range_spec: data.rangeSpec || 'last 100',
                                            include_interfaces: data.includeInterfaces !== false,
                                            dry_run: true
                                        });
                                        let terminal = [];
                                        if (result.job_id) {
                                            for (let i = 0; i < 20; i++) {
                                                await new Promise(r => setTimeout(r, 500));
                                                const job = await ScalerAPI.getJob(result.job_id);
                                                terminal = job?.terminal_lines || [];
                                                if (job?.done) break;
                                            }
                                        }
                                        self.WizardController.data._scalePreview = { terminal_lines: terminal };
                                        self.WizardController.render();
                                    } catch (e) {
                                        self.showNotification('Preview failed: ' + e.message, 'error');
                                    } finally {
                                        btn.disabled = false;
                                        btn.textContent = 'Show detailed commands';
                                    }
                                });
                            },
                            collectData: () => ({}),
                            validate: (data) => (data.selectedDeviceIds || []).length > 0
                        }
                    ],
                    onComplete: async (data) => {
                        const params = {
                            device_ids: data.selectedDeviceIds || [],
                            operation: data.operation || 'down',
                            service_type: data.serviceType || 'fxc',
                            range_spec: data.rangeSpec || 'last 100',
                            include_interfaces: data.includeInterfaces !== false,
                            dry_run: false
                        };
                        if (params.device_ids.length === 0) return;
                        if (!confirm(`Are you sure you want to scale ${params.operation} ${params.service_type} services?\n\nThis will modify ${params.device_ids.length} device(s).`)) {
                            return;
                        }
                        self.closePanel('scale-wizard');
                        try {
                            const result = await ScalerAPI.scaleUpDown(params);
                            self.showProgress(result.job_id, `Scale ${params.operation} ${params.service_type}`);
                        } catch (e) {
                            self.showNotification(`Scale failed: ${e.message}`, 'error');
                        }
                    }
                });
            } catch (e) {
                const panel = this.state.activePanels['scale-wizard'];
                if (panel) {
                    const cd = panel.querySelector('.scaler-panel-content');
                    if (cd) cd.innerHTML = `<div class="scaler-error">${e.message}</div>`;
                }
            }
        },
        
        // =========================================================================
        // STAG CHECK
        // =========================================================================
        
        async openStagCheck() {
            const content = document.createElement('div');
            content.innerHTML = '<div class="scaler-loading">Loading devices...</div>';
        
            this.openPanel('stag-check', 'Stag Pool Check', content, {
                width: '600px',
                parentPanel: 'scaler-menu'
            });
        
            try {
                const data = await ScalerAPI.getDevices();
        
            content.innerHTML = `
                    <div class="scaler-form">
                        <div class="scaler-info-box">
                            Check QinQ Stag pool usage (ifindex 88001-92000, limit 4000).
                    </div>
                    <div class="scaler-form-group">
                            <label>Select Devices</label>
                            <div id="stag-devices" class="scaler-checkbox-list">
                                ${data.devices.map(dev => `
                                    <label class="scaler-checkbox-item">
                                        <input type="checkbox" value="${dev.id}" checked>
                                        <span>${dev.hostname}</span>
                                    </label>
                                `).join('')}
                    </div>
                </div>
                <div class="scaler-form-actions">
                            <button class="scaler-btn scaler-btn-primary" id="stag-check-btn">Check Stag Pool</button>
                </div>
                        <div id="stag-result" class="scaler-result-box" style="display:none;"></div>
                    </div>
                `;
        
                document.getElementById('stag-check-btn').onclick = async () => {
                    const deviceCheckboxes = document.querySelectorAll('#stag-devices input:checked');
                    const deviceIds = Array.from(deviceCheckboxes).map(cb => cb.value);
        
                    if (deviceIds.length === 0) {
                        this.showNotification('Select at least one device', 'warning');
                        return;
                    }
        
                    const resultBox = document.getElementById('stag-result');
                    resultBox.style.display = 'block';
                    resultBox.innerHTML = '<div class="scaler-loading">Checking Stag pools...</div>';
        
                    try {
                        const result = await ScalerAPI.stagCheck({ device_ids: deviceIds });
        
                        let html = `<table class="scaler-table">
                            <thead>
                                <tr><th>Device</th><th>Stags</th><th>Limit</th><th>Usage</th><th>Status</th></tr>
                            </thead>
                            <tbody>`;
        
                        for (const dev of result.devices) {
                            const statusClass = dev.exceeded ? 'scaler-status-error' : 
                                               (dev.at_risk ? 'scaler-status-warning' : 'scaler-status-ok');
                            const statusText = dev.exceeded ? 'EXCEEDED' : (dev.at_risk ? 'AT RISK' : 'OK');
        
                            html += `<tr>
                                <td>${dev.hostname}</td>
                                <td>${dev.total_stags.toLocaleString()}</td>
                                <td>${dev.limit.toLocaleString()}</td>
                                <td>
                                    <div class="scaler-progress-bar">
                                        <div class="scaler-progress-fill ${statusClass}" style="width: ${dev.percentage}%"></div>
                                    </div>
                                    ${dev.percentage}%
                                </td>
                                <td class="${statusClass}">${statusText}</td>
                            </tr>`;
        
                            if (dev.error) {
                                html += `<tr><td colspan="5" class="scaler-error">${dev.error}</td></tr>`;
                            }
                        }
        
                        html += '</tbody></table>';
                        html += `<div class="scaler-summary">
                            Total: ${result.summary.total_devices} devices | 
                            At Risk: ${result.summary.devices_at_risk} | 
                            Exceeded: ${result.summary.devices_exceeded}
                        </div>`;
        
                        resultBox.innerHTML = html;
                } catch (e) {
                        resultBox.innerHTML = `<div class="scaler-error">${e.message}</div>`;
                    }
                };
            } catch (e) {
                content.innerHTML = `<div class="scaler-error">${e.message}</div>`;
            }
        },

    });

    if (typeof ScalerAPI !== 'undefined') {
        ScalerAPI.imageUpgrade = async function(params) {
            const response = await fetch(ScalerAPI._api('/api/operations/image-upgrade'), {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(params)
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(ScalerAPI._formatError(error.detail, 'Image upgrade failed'));
            }
            return response.json();
        };

        ScalerAPI.stagCheck = async function(params) {
            const response = await fetch(ScalerAPI._api('/api/operations/stag-check'), {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(params)
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(ScalerAPI._formatError(error.detail, 'Stag check failed'));
            }
            return response.json();
        };

        ScalerAPI.scaleUpDown = async function(params) {
            const response = await fetch(ScalerAPI._api('/api/operations/scale-updown'), {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(params)
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(ScalerAPI._formatError(error.detail, 'Scale operation failed'));
            }
            return response.json();
        };
    }
})(window.ScalerGUI);
