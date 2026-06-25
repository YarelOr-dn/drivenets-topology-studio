// topology-device-mode-gate.js
// Centralized device-mode gating for DNAAS Discovery, Packet Capture,
// AI config apply, terminal banners, and right-click menu chips.
//
// Design contract
// ---------------
// Every entry point that touches a device should call:
//
//   const decision = await DeviceModeGate.check(device, 'dnaas_discovery', { live: false });
//   if (!decision.ok) {
//       DeviceModeGate.showBlockedModal(decision); // returns Promise<'cancel' | 'reprobed' | 'override'>
//       return;
//   }
//
// `check()`:
//   1. Reads `device._deviceMode` and `device._modeFetchedAt` from
//      DeviceMonitor's cache (DeviceMonitor refreshes every 5min via
//      `_refreshOneInner`). If the cache is fresh enough (default
//      300s) we use it immediately.
//   2. Otherwise (or if `live=true` is requested), it hits
//      `GET /api/devices/{id}/mode-probe?live=true` which does a
//      6s SSH probe and updates `operational.json` so every
//      subsequent reader (canvas badge, upgrade wizard, etc.) sees
//      the same answer.
//
// The backend returns a per-operation policy
// (`response.operations.<op>.allowed/reason`) so the UI never
// duplicates the GI/RECOVERY/UPGRADING decision logic. If the
// backend is unreachable we fall back to a permissive decision so
// users can still work offline.
//
// Render helpers:
//   * `renderBadge(mode, opts)`  -> small inline pill HTML
//   * `showBlockedModal(decision)` -> consistent block-with-reason modal
//   * `attachBanner(container, mode, op)` -> warning banner inside dialogs
//
// Cache freshness policy follows the user's directive:
// "the monitoring is anyways every 5 minutes so cache is fine,
//  but it should run a quick probe" -- we treat anything <=5min
// as fresh and force a live probe otherwise.
(function () {
    'use strict';

    const FRESH_MS = 5 * 60 * 1000; // 5 minutes -- matches DeviceMonitor

    const MODE_COLORS = {
        DNOS: { bg: '#27ae60', fg: '#fff', label: 'DNOS' },
        GI: { bg: '#f39c12', fg: '#fff', label: 'GI' },
        RECOVERY: { bg: '#e74c3c', fg: '#fff', label: 'RECOVERY' },
        unknown: { bg: '#7f8c8d', fg: '#fff', label: 'UNKNOWN' },
    };

    const OPERATION_LABELS = {
        dnaas_discovery: 'DNAAS Discovery',
        packet_capture: 'Packet Capture',
        config_apply: 'Apply DNOS Configuration',
        terminal: 'Open Terminal',
    };

    function _normalizeMode(m) {
        const upper = (m || '').toUpperCase();
        if (upper === 'DNOS' || upper === 'GI' || upper === 'RECOVERY') {
            return upper;
        }
        return 'unknown';
    }

    function _ageMs(device) {
        const t = device && device._modeFetchedAt;
        if (!t) return Infinity;
        return Date.now() - t;
    }

    async function _probeBackend(device, opts) {
        const deviceId = device.label || device.deviceSerial || device.serial || '';
        if (!deviceId) {
            return null;
        }
        const sshHost = device.sshConfig?.host || device.sshConfig?.hostBackup || '';
        const liveQS = opts && opts.live ? '&live=true' : '';
        const url = `/api/devices/${encodeURIComponent(deviceId)}/mode-probe`
            + `?ssh_host=${encodeURIComponent(sshHost)}${liveQS}`;
        try {
            const resp = await fetch(url, { method: 'GET' });
            if (!resp.ok) return null;
            const data = await resp.json();
            // Update canvas-side cache so the badge and DeviceMonitor
            // agree on the latest reading.
            if (data && data.mode) {
                device._deviceMode = data.mode === 'unknown'
                    ? (device._deviceMode || 'unknown')
                    : data.mode;
                device._modeFetchedAt = Date.now();
                device._modeProbeSource = data.source || '';
                device._modeRawState = data.raw_state || '';
                device._modeTransientOp = data.transient_op || '';
                device._modeOpsPolicy = data.operations || null;
                window.dispatchEvent(new CustomEvent('device:mode-probed', {
                    detail: { deviceId, device, data }
                }));
            }
            return data;
        } catch (e) {
            return null;
        }
    }

    /**
     * Get the current mode + per-operation policy for a device.
     * Forces a live probe when cache is stale (>5min) or when
     * `opts.live` is true.
     *
     * Returns a `decision` object:
     *   {
     *     ok: bool,                     // operation allowed?
     *     mode: 'DNOS'|'GI'|'RECOVERY'|'unknown',
     *     reason: str,                  // why blocked, '' if allowed
     *     op: string,                   // operation key requested
     *     ageSeconds: number|null,
     *     source: 'cache'|'live'|'live_failed_cache'|'cache_only',
     *     deviceId: string,
     *     device,
     *     transientOp: string,          // 'UPGRADING'|'DEPLOYING'|''
     *     ssh: bool,
     *     raw: object|null              // backend response when available
     *   }
     */
    async function check(device, op, opts) {
        opts = opts || {};
        if (!device) {
            return {
                ok: false,
                mode: 'unknown',
                reason: 'No device selected.',
                op: op,
                ageSeconds: null,
                source: 'cache_only',
                deviceId: '',
                device: null,
                transientOp: '',
                ssh: false,
                raw: null,
            };
        }
        const deviceId = device.label || device.deviceSerial || device.serial || '';
        const cachedMode = _normalizeMode(device._deviceMode);
        const ageMs = _ageMs(device);
        const wantLive = !!opts.live;
        const cacheStale = !device._modeFetchedAt || ageMs > FRESH_MS;
        const needLive = wantLive || cacheStale || cachedMode === 'unknown';

        let backend = null;
        if (needLive) {
            backend = await _probeBackend(device, { live: true });
        } else {
            // Fast-path: trust cached mode and ask backend only for
            // the policy lookup (no live probe). This keeps the gate
            // almost free when DeviceMonitor recently refreshed.
            backend = await _probeBackend(device, { live: false });
        }

        let mode = cachedMode;
        let policy = device._modeOpsPolicy || null;
        let source = 'cache_only';
        let transientOp = '';
        let ssh = !!device._sshReachable;
        let ageSeconds = device._modeFetchedAt
            ? Math.floor((Date.now() - device._modeFetchedAt) / 1000)
            : null;

        if (backend) {
            mode = _normalizeMode(backend.mode);
            policy = backend.operations || policy;
            source = backend.source || source;
            transientOp = backend.transient_op || '';
            ssh = !!backend.ssh_reachable;
            if (backend.age_seconds != null) {
                ageSeconds = backend.age_seconds;
            }
        }

        let opPolicy = (policy && policy[op]) || null;
        if (!opPolicy) {
            // Backend offline -- use a conservative client-side fallback.
            opPolicy = _clientFallbackPolicy(op, mode, ssh, transientOp);
        }

        return {
            ok: !!opPolicy.allowed,
            mode: mode,
            reason: opPolicy.reason || '',
            op: op,
            ageSeconds: ageSeconds,
            source: source,
            deviceId: deviceId,
            device: device,
            transientOp: transientOp,
            ssh: ssh,
            raw: backend,
        };
    }

    function _clientFallbackPolicy(op, mode, ssh, transientOp) {
        if (mode === 'RECOVERY') {
            return op === 'terminal'
                ? { allowed: true, reason: 'Console-only; expect a recovery prompt.' }
                : { allowed: false, reason: 'Device is in RECOVERY mode.' };
        }
        if (mode === 'GI') {
            return op === 'terminal'
                ? { allowed: true, reason: 'GI shell -- limited commands.' }
                : { allowed: false, reason: 'Device is in GI mode -- DNOS CLI not available.' };
        }
        if (mode === 'unknown') {
            if (transientOp) {
                return op === 'terminal'
                    ? { allowed: true, reason: `Transient ${transientOp.toLowerCase()} job.` }
                    : { allowed: false, reason: `Image ${transientOp.toLowerCase()} job in progress.` };
            }
            return op === 'terminal'
                ? { allowed: true, reason: 'Mode unknown; outcome depends on the device.' }
                : { allowed: false, reason: 'Device mode unknown -- click Re-detect.' };
        }
        // DNOS
        if (!ssh && op !== 'terminal') {
            return { allowed: false, reason: 'SSH unreachable -- check management IP.' };
        }
        return { allowed: true, reason: '' };
    }

    function renderBadge(mode, opts) {
        opts = opts || {};
        const meta = MODE_COLORS[_normalizeMode(mode)];
        const size = opts.compact ? '9px' : '10px';
        const pad = opts.compact ? '1px 5px' : '2px 8px';
        const ml = opts.marginLeft || '6px';
        return `<span class="device-mode-pill" style="`
            + `background:${meta.bg};color:${meta.fg};`
            + `padding:${pad};border-radius:4px;font-size:${size};`
            + `font-weight:600;letter-spacing:0.3px;margin-left:${ml};`
            + `text-transform:uppercase;display:inline-block;line-height:1.4;`
            + `">${meta.label}</span>`;
    }

    function attachBanner(container, decision) {
        if (!container || !decision) return;
        const isBlocked = !decision.ok;
        const meta = MODE_COLORS[_normalizeMode(decision.mode)];
        const opLabel = OPERATION_LABELS[decision.op] || decision.op;
        const ageStr = decision.ageSeconds == null
            ? 'just now'
            : decision.ageSeconds < 60
                ? `${decision.ageSeconds}s ago`
                : decision.ageSeconds < 3600
                    ? `${Math.floor(decision.ageSeconds / 60)}m ago`
                    : `${Math.floor(decision.ageSeconds / 3600)}h ago`;

        const div = document.createElement('div');
        div.className = 'device-mode-banner ' + (isBlocked ? 'blocked' : 'allowed');
        div.style.cssText = `
            margin: 8px 0; padding: 8px 12px;
            border-radius: 6px;
            background: ${isBlocked ? 'rgba(231,76,60,0.12)' : 'rgba(39,174,96,0.10)'};
            border: 1px solid ${isBlocked ? 'rgba(231,76,60,0.4)' : 'rgba(39,174,96,0.35)'};
            color: inherit;
            font-size: 12px;
            display: flex; align-items: center; gap: 10px;
        `;
        div.innerHTML = `
            <div style="flex:0 0 auto;">${renderBadge(decision.mode, { marginLeft: '0' })}</div>
            <div style="flex:1 1 auto;">
                <div><strong>${opLabel}</strong>:
                    ${isBlocked
                ? `<span style="color:#e74c3c;">${decision.reason || 'Blocked.'}</span>`
                : `<span style="color:#27ae60;">Ready.</span>`}
                </div>
                <div style="opacity:0.7; font-size:11px; margin-top:2px;">
                    Mode last detected ${ageStr}
                    ${decision.source === 'live' ? '(live probe)' : decision.source === 'cache' ? '(cached)' : ''}
                    ${decision.transientOp ? ' &middot; transient: ' + decision.transientOp : ''}
                </div>
            </div>
            <button class="device-mode-redetect-btn" type="button" style="
                flex: 0 0 auto;
                background: rgba(155,89,182,0.2);
                border: 1px solid rgba(155,89,182,0.5);
                color: inherit; padding: 4px 8px; border-radius: 4px;
                font-size: 11px; cursor: pointer;
            ">Re-detect</button>
        `;
        container.appendChild(div);
        const reBtn = div.querySelector('.device-mode-redetect-btn');
        if (reBtn) {
            reBtn.addEventListener('click', async () => {
                reBtn.disabled = true;
                reBtn.textContent = 'Probing...';
                const fresh = await check(decision.device, decision.op, { live: true });
                div.replaceWith(div); // placeholder no-op
                div.remove();
                attachBanner(container, fresh);
                window.dispatchEvent(new CustomEvent('device:mode-redetected', {
                    detail: { deviceId: decision.deviceId, decision: fresh }
                }));
            });
        }
        return div;
    }

    /**
     * Show a consistent block-with-reason modal. Returns a Promise
     * that resolves with one of:
     *   - 'cancel'    : user dismissed
     *   - 'reprobed'  : user clicked Re-detect AND the new mode now allows the op
     *   - 'override'  : user explicitly chose to proceed anyway (for AI apply only)
     */
    function showBlockedModal(decision, opts) {
        opts = opts || {};
        const allowOverride = !!opts.allowOverride;
        return new Promise((resolve) => {
            const isDark = document.body.classList.contains('dark-mode')
                || window.matchMedia?.('(prefers-color-scheme: dark)').matches;
            const bg = isDark ? 'rgba(30,35,50,0.97)' : 'rgba(255,255,255,0.97)';
            const text = isDark ? '#e0e0e0' : '#1a1a2e';
            const border = isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.1)';
            const inputBg = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)';

            const overlay = document.createElement('div');
            overlay.className = 'device-mode-block-overlay';
            overlay.style.cssText = 'position:fixed;inset:0;z-index:100050;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.55);';

            const opLabel = OPERATION_LABELS[decision.op] || decision.op;
            const dev = decision.deviceId || '(no device)';
            const ageStr = decision.ageSeconds == null
                ? 'just now'
                : decision.ageSeconds < 60
                    ? `${decision.ageSeconds}s ago`
                    : decision.ageSeconds < 3600
                        ? `${Math.floor(decision.ageSeconds / 60)}m ago`
                        : `${Math.floor(decision.ageSeconds / 3600)}h ago`;

            overlay.innerHTML = `
                <div style="background:${bg};border:1px solid ${border};border-radius:12px;padding:22px 26px;max-width:520px;width:92%;color:${text};font-family:system-ui;box-shadow:0 24px 70px rgba(0,0,0,0.45);">
                    <div style="font-size:14px;font-weight:600;margin-bottom:12px;display:flex;align-items:center;gap:8px;">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#e74c3c" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                        ${opLabel} blocked
                        ${renderBadge(decision.mode, { marginLeft: 'auto' })}
                    </div>
                    <div style="font-size:12.5px;line-height:1.5;margin-bottom:14px;">
                        <div><strong>Device:</strong> ${dev}</div>
                        <div style="margin-top:6px;color:#e74c3c;">${decision.reason || 'This operation is not allowed in the current mode.'}</div>
                    </div>
                    <div id="_dmg_extra" style="font-size:11px;margin-bottom:12px;padding:8px;border-radius:6px;background:${inputBg};">
                        Mode last detected ${ageStr}
                        ${decision.source === 'live' ? '(via live SSH probe)' : decision.source === 'cache' ? '(from cache)' : ''}
                        ${decision.transientOp ? '<br>Transient ops flag: <strong>' + decision.transientOp + '</strong>' : ''}
                    </div>
                    <div style="display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap;">
                        <button id="_dmg_cancel" style="padding:6px 14px;font-size:12px;border-radius:6px;border:1px solid ${border};background:${inputBg};color:${text};cursor:pointer;">Cancel</button>
                        <button id="_dmg_redetect" style="padding:6px 14px;font-size:12px;border-radius:6px;border:1px solid rgba(155,89,182,0.5);background:rgba(155,89,182,0.2);color:${text};cursor:pointer;">Re-detect via SSH</button>
                        ${allowOverride ? '<button id="_dmg_override" style="padding:6px 14px;font-size:12px;border-radius:6px;border:1px solid rgba(231,76,60,0.5);background:rgba(231,76,60,0.15);color:#e74c3c;cursor:pointer;">Proceed anyway</button>' : ''}
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);

            const finish = (result) => {
                try { overlay.remove(); } catch (e) { /* noop */ }
                resolve(result);
            };

            overlay.querySelector('#_dmg_cancel').addEventListener('click', () => finish('cancel'));
            const overrideBtn = overlay.querySelector('#_dmg_override');
            if (overrideBtn) {
                overrideBtn.addEventListener('click', () => finish('override'));
            }
            const reBtn = overlay.querySelector('#_dmg_redetect');
            reBtn.addEventListener('click', async () => {
                reBtn.disabled = true;
                reBtn.textContent = 'Probing device...';
                const fresh = await check(decision.device, decision.op, { live: true });
                if (fresh.ok) {
                    finish('reprobed');
                } else {
                    const extra = overlay.querySelector('#_dmg_extra');
                    if (extra) {
                        extra.innerHTML = `Re-probe completed: still <strong>${fresh.mode}</strong>.<br>${fresh.reason || ''}`;
                    }
                    reBtn.disabled = false;
                    reBtn.textContent = 'Re-detect via SSH';
                }
            });

            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) finish('cancel');
            });
        });
    }

    /**
     * Convenience helper: check + show the modal if blocked. Returns
     * `true` when the operation is allowed (either initially, after
     * a re-probe, or after user override), `false` when cancelled.
     */
    async function require(device, op, opts) {
        const decision = await check(device, op, opts);
        if (decision.ok) {
            return decision;
        }
        const result = await showBlockedModal(decision, opts);
        if (result === 'reprobed') {
            const fresh = await check(device, op, { live: false });
            if (fresh.ok) return fresh;
            return null;
        }
        if (result === 'override' && (opts && opts.allowOverride)) {
            decision.ok = true;
            decision.reason = 'User override';
            return decision;
        }
        return null;
    }

    /**
     * Refresh the small mode badges in any open dialog headers tagged
     * `data-mode-badge-host="<deviceId>"`. Called when a device's
     * mode flips (`device:mode-changed` / `device:mode-probed`).
     */
    function _refreshBadges(deviceId, mode) {
        const hosts = document.querySelectorAll(
            `[data-mode-badge-host="${CSS.escape(deviceId)}"]`
        );
        hosts.forEach(h => {
            const slot = h.querySelector('.device-mode-pill') || h;
            if (slot.classList.contains('device-mode-pill')) {
                slot.outerHTML = renderBadge(mode);
            } else {
                h.insertAdjacentHTML('beforeend', renderBadge(mode));
            }
        });
    }

    window.addEventListener('device:mode-changed', (e) => {
        try { _refreshBadges(e.detail?.deviceId, e.detail?.mode); } catch (_) { /* noop */ }
    });
    window.addEventListener('device:mode-probed', (e) => {
        try { _refreshBadges(e.detail?.deviceId, e.detail?.data?.mode); } catch (_) { /* noop */ }
    });

    window.DeviceModeGate = {
        check,
        require,
        renderBadge,
        attachBanner,
        showBlockedModal,
        OPERATION_LABELS,
        FRESH_MS,
    };
})();
