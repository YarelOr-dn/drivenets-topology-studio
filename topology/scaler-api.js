/**
 * SCALER API Client
 * 
 * JavaScript module for communicating with the FastAPI backend.
 * Provides methods for device management, configuration operations,
 * and real-time progress updates via WebSocket.
 * 
 * @version 1.0.0
 * @requires FastAPI backend running on same origin
 *
 * Domain sections in this file (search for "// ====="):
 *   Core helpers | Devices + SSH/console | Config read/write |
 *   Config generation | Push/operations | DNAAS | Multi-BD | Progress SSE/WS |
 *   Health | Image upgrade (Jenkins)
 */

const ScalerAPI = {
    // Base URL - empty for same origin
    baseUrl: '',
    
    // Active WebSocket connections
    _websockets: {},
    
    // Bridge availability tracking -- prevents console 501 spam
    _bridgeUp: true,
    _bridgeRetryAfter: 0,

    /**
     * Resolve API path to full URL (prepends baseUrl for remote server access).
     */
    _api(path) {
        return (this.baseUrl || '') + path;
    },

    /**
     * Authenticated fetch for every backend API call made through ScalerAPI.
     *
     * The global auth monkey-patch covers same-origin "/api/..." calls, but
     * ScalerAPI can also target an explicit bridge baseUrl. In that mode the
     * URL is absolute and the global patch does not see a leading "/api/",
     * so protected bridge endpoints can 401 after device onboarding. Route
     * all ScalerAPI API traffic through TopologyAuth.authFetch when present.
     */
    _fetch(url, opts = {}) {
        if (typeof window !== 'undefined'
            && window.TopologyAuth
            && typeof window.TopologyAuth.authFetch === 'function') {
            return window.TopologyAuth.authFetch(url, opts);
        }
        return fetch(url, opts);
    },

    /**
     * Resolve the active topology scope for per-user / per-topology
     * device overrides (see POST /api/devices/{id}/system-type docstring).
     *
     * Pulls ``{ domain_id, topology_id }`` from TopologySync when it's
     * authoritative, falls back to the topology editor's metadata for
     * file-mode loads, and returns ``{ domain_id: '', topology_id: '' }``
     * when nothing is active (pre-login splash, unit tests). Callers
     * should treat empty strings as "no scope" and let the backend fall
     * back to the per_user layer.
     *
     * Kept as a standalone helper so future endpoints (wizard
     * suggestions, plan build, etc.) that also want to be scope-aware can
     * share the same resolution instead of duplicating it.
     */
    _getTopologyScope() {
        try {
            if (typeof window !== 'undefined' && window.TopologySync
                && typeof window.TopologySync.getActive === 'function') {
                const a = window.TopologySync.getActive();
                if (a && a.topology_id) {
                    return {
                        domain_id: a.domain_id || '',
                        topology_id: a.topology_id || '',
                    };
                }
            }
        } catch (_) {}
        try {
            if (typeof window !== 'undefined' && window.topologyEditor) {
                const ed = window.topologyEditor;
                const meta = ed && ed.metadata;
                if (meta && meta.topology_id) {
                    return {
                        domain_id: meta.domain_id || '',
                        topology_id: meta.topology_id,
                    };
                }
                if (ed && ed._loadedFileName) {
                    return {
                        domain_id: 'file',
                        topology_id: ed._loadedFileName,
                    };
                }
            }
        } catch (_) {}
        return { domain_id: '', topology_id: '' };
    },

    /**
     * WebSocket origin for scaler bridge (device-event bus, in-browser
     * terminal, push-progress streams).
     *
     * Resolution order:
     *   1. Explicit `baseUrl` on ScalerAPI (e.g. `http://lab:8766`) wins.
     *      Preserves "point the app at a remote bridge" flows.
     *   2. Same-origin default via `window.location.host`. serve.py now
     *      proxies WS upgrades under `/api/events/ws`, `/api/terminal/ws`,
     *      and `/ws/progress/*`, so going through port 8080 works from
     *      localhost AND remote-access (CGNAT) deployments where 8766 is
     *      firewalled off. This satisfies the
     *      .cursor/rules/remote-access-proxy.mdc rule that "serve.py is
     *      the single entry point; 8765/8766 are internal".
     *   3. Legacy fallback to `:8766` is kept for headless / test contexts
     *      where `window` isn't available at all.
     *
     * @returns {string} e.g. ws://localhost:8080 or wss://host:8080
     */
    getBridgeWebSocketOrigin() {
        const locProto = (typeof window !== 'undefined' && window.location && window.location.protocol === 'https:')
            ? 'wss:' : 'ws:';
        const base = (this.baseUrl || '').trim();
        if (base) {
            try {
                const u = new URL(base, typeof window !== 'undefined' ? window.location.origin : 'http://localhost');
                const wsProto = u.protocol === 'https:' ? 'wss:' : 'ws:';
                const portPart = u.port ? `:${u.port}` : '';
                return `${wsProto}//${u.hostname}${portPart}`;
            } catch (e) {
                console.warn('[ScalerAPI] getBridgeWebSocketOrigin: invalid baseUrl, fallback', e);
            }
        }
        if (typeof window === 'undefined' || !window.location) {
            return 'ws://localhost:8766';
        }
        // window.location.host includes the port the page was loaded from
        // (e.g. "100.64.6.134:8080" or "localhost:8080"), so the WS stays
        // same-origin and goes through serve.py's WS proxy.
        return `${locProto}//${window.location.host}`;
    },

    _formatError(detail, fallback) {
        if (!detail) return fallback || 'Request failed';
        if (typeof detail === 'string') return detail;
        if (Array.isArray(detail)) {
            return detail.map(d => {
                if (typeof d === 'string') return d;
                const loc = (d.loc || []).join(' > ');
                return loc ? `${loc}: ${d.msg || d.message || ''}` : (d.msg || d.message || JSON.stringify(d));
            }).join('; ');
        }
        return String(detail);
    },

    /**
     * Fetch with timeout using AbortController. Rejects if response takes
     * longer than timeoutMs. Caller's signal (if any) is also respected.
     */
    _fetchWithTimeout(url, opts = {}, timeoutMs = 15000) {
        const controller = new AbortController();
        const externalSignal = opts.signal;
        if (externalSignal?.aborted) return Promise.reject(new DOMException('Aborted', 'AbortError'));
        if (externalSignal) {
            externalSignal.addEventListener('abort', () => controller.abort(), { once: true });
        }
        const timer = setTimeout(() => controller.abort(), timeoutMs);
        return this._fetch(url, { ...opts, signal: controller.signal })
            .finally(() => clearTimeout(timer));
    },

    // =========================================================================
    // CORE (_api, WebSocket origin, errors, fetch timeout)
    // =========================================================================
    
    // =========================================================================
    // DEVICE REGISTRY (GET/POST/PUT/DELETE /api/devices/* where applicable)
    // =========================================================================
    
    /**
     * Get list of all registered devices
     * @returns {Promise<{devices: Array, count: number}>}
     */
    async getDevices() {
        const response = await this._fetch(this._api('/api/devices/'));
        if (!response.ok) {
            throw new Error(`Failed to fetch devices: ${response.statusText}`);
        }
        return response.json();
    },
    
    /**
     * Get a single device by ID
     * @param {string} deviceId - Device identifier
     * @returns {Promise<Object>} Device details
     */
    async getDevice(deviceId) {
        const response = await this._fetch(this._api(`/api/devices/${encodeURIComponent(deviceId)}`));
        if (!response.ok) {
            throw new Error(`Device not found: ${deviceId}`);
        }
        return response.json();
    },
    
    // =========================================================================
    // SSH / CONSOLE / PDU / TERMINAL (scaler_bridge /api/ssh/*, WebSocket terminal)
    // =========================================================================
    
    /**
     * Probe connection methods for a device (TCP reachability check).
     * @param {string} deviceId - Device identifier
     * @param {string} [sshHost] - SSH host/IP from canvas
     * @returns {Promise<{methods: Array, recommended: string, device_state: string}>}
     */
    async probeConnection(deviceId, sshHost = '') {
        if (!this._bridgeUp && Date.now() < this._bridgeRetryAfter) {
            const err = new Error('Scaler bridge unavailable; probe is temporarily paused.');
            err.status = 503;
            err.retryAfterMs = Math.max(0, this._bridgeRetryAfter - Date.now());
            err.bridgeUnavailable = true;
            throw err;
        }
        const response = await this._fetch(this._api('/api/ssh/probe'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: deviceId, ssh_host: sshHost || '' })
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: `Probe failed (HTTP ${response.status})` }));
            const detail = err.detail || `Probe failed (HTTP ${response.status})`;
            const e = new Error(detail);
            e.status = response.status;
            e.detail = detail;
            if (response.status === 501 || response.status === 502 || response.status === 503) {
                this._bridgeUp = false;
                this._bridgeRetryAfter = Date.now() + 15000;
                e.bridgeUnavailable = true;
            }
            throw e;
        }
        this._bridgeUp = true;
        return response.json();
    },

    /**
     * Clear a ghost-IP record for a device (stale mgmt IP after upgrade/re-image).
     *
     * Flags the scaler operational.json as stale, evicts pooled SSH clients,
     * drops the resolve cache, and prunes the legacy devices.json entry so
     * subsequent SSH attempts re-discover instead of dialling the ghost host.
     *
     * @param {string} deviceId        Canvas / scaler id that the user clicked.
     * @param {Object} [opts]
     * @param {string} [opts.ip]              IP that turned out to be wrong.
     * @param {string} [opts.actualHostname]  Hostname that answered at that IP.
     * @param {string} [opts.reason]          Machine tag (default 'user_cleared').
     * @returns {Promise<Object>} Cleanup summary from the bridge.
     */
    async clearGhostIp(deviceId, { ip = '', actualHostname = '', reason = 'user_cleared' } = {}) {
        const response = await this._fetch(this._api('/api/ssh/clear-ghost-ip'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_id: deviceId || '',
                ip: ip || '',
                actual_hostname: actualHostname || '',
                reason: reason || 'user_cleared',
            }),
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: `clear-ghost-ip failed (HTTP ${response.status})` }));
            throw new Error(err.detail || 'clear-ghost-ip failed');
        }
        return response.json();
    },

    /**
     * Ghost-IP pre-flight: SSH-connect to ip, read the prompt/banner and
     * confirm the device hostname matches deviceId. Does NOT leave a shell
     * open. When the hostname clearly belongs to a different device the
     * bridge auto-reaps the stale record (unless opts.autoReap=false).
     *
     * Response shape:
     *   {
     *     reachable: bool,              // TCP 22 open
     *     identity_verified: bool,      // true = safe to iTerm / WS-terminal
     *     actual_hostname: string,      // what the remote advertised
     *     expected_hostname: string,
     *     generic_prompt?: bool,        // true for GI/RECOVERY/BASEOS -- ambiguous
     *     reason?: 'port_closed'|'auth_failed'|'ghost_ip'|'generic_prompt'|'timeout',
     *     reaped?: object,              // reap summary if ghost was cleared
     *   }
     *
     * @param {string} deviceId  canvas / scaler hostname (e.g. "YOR_CL_PE-4")
     * @param {string} ip        IPv4 we plan to dial
     * @param {Object} [opts]
     * @param {number} [opts.port=22]
     * @param {string} [opts.user='dnroot']
     * @param {string} [opts.password='dnroot']
     * @param {boolean}[opts.autoReap=true]
     */
    async verifyDeviceIdentity(deviceId, ip, opts = {}) {
        const { port = 22, user = 'dnroot', password = 'dnroot', autoReap = true } = opts;
        const response = await this._fetch(this._api('/api/ssh/verify-identity'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_id: deviceId || '',
                ip: ip || '',
                port, user, password,
                auto_reap: !!autoReap,
            }),
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: `verify-identity HTTP ${response.status}` }));
            throw new Error(err.detail || 'verify-identity failed');
        }
        return response.json();
    },

    /**
     * Verify operator-entered credentials and capture cluster identity in
     * one composed call. Wraps `/api/devices/:id/verify-credentials`,
     * which itself orchestrates `/api/ssh/verify-identity` (banner check)
     * + `/api/ssh/probe` (cluster identity) + `operational.json`
     * persistence (verified_at + monitor_policy). Used by the SSH
     * dialog Save button as the gate before persisting credentials
     * into the topology JSON.
     *
     * The endpoint NEVER raises on routine credential failures (auth /
     * unreachable / ghost IP / timeout) -- those come back as
     * `{ ok: false, reason: '...' }` so the dialog can render an inline
     * error block. We only raise here when the bridge itself returns a
     * non-2xx status (resolver bug, auth backend down, etc.).
     *
     * @param {string} deviceId  canvas / scaler hostname (e.g. "YOR_CL_PE-4")
     * @param {string} host      IPv4 or hostname the user typed
     * @param {string} user      username (default 'dnroot')
     * @param {string} password  password (default 'dnroot')
     * @param {Object} [opts]
     * @param {string} [opts.discoveryDepth='standard']  'minimal'|'standard'|'full'
     * @param {string} [opts.monitorCadence='fast_initial'] 'default'|'fast_initial'|'aggressive'
     * @param {boolean}[opts.skipProbe=false]            debug knob -- skip /api/ssh/probe
     * @returns {Promise<{
     *   ok: boolean, reason: string, message: string,
     *   verified_at: string, expected_hostname: string, actual_hostname: string,
     *   device_state: string, is_cluster: boolean,
     *   active_ncc_vm: string, active_ncc_host: string, active_ncc_ip: ?string,
     *   kvm_host: string, kvm_host_ip: string, ncc_vms: string[],
     *   monitor_policy: { cadence: string, discovery_depth: string },
     *   raw_verify: Object, raw_probe: ?Object
     * }>}
     */
    async verifyCredentials(deviceId, host, user, password, opts = {}) {
        const clean = (deviceId || '').trim();
        if (!clean) throw new Error('verifyCredentials requires a deviceId');
        if (!host) throw new Error('verifyCredentials requires a host');
        const {
            discoveryDepth = 'standard',
            monitorCadence = 'fast_initial',
            skipProbe = false,
        } = opts;
        const response = await this._fetch(
            this._api(`/api/devices/${encodeURIComponent(clean)}/verify-credentials`),
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    host: String(host || '').trim(),
                    user: String(user || 'dnroot').trim() || 'dnroot',
                    password: String(password || 'dnroot'),
                    discovery_depth: discoveryDepth,
                    monitor_cadence: monitorCadence,
                    skip_probe: !!skipProbe,
                }),
            },
        );
        if (!response.ok) {
            const err = await response.json().catch(
                () => ({ detail: `verify-credentials HTTP ${response.status}` }),
            );
            const e = new Error(err.detail || 'verify-credentials failed');
            e.httpStatus = response.status;
            throw e;
        }
        return response.json();
    },

    // =========================================================================
    // AUTO-MONITOR (Phase 2 MVP)
    // =========================================================================
    //
    // Verify SSH credentials AND register the device in the shared
    // monitor registry. Successful registration:
    //   - upserts the shared registry row (one per chassis IP + serial)
    //   - attaches a per-user reference (idempotent; second call by the
    //     same user is a no-op)
    //   - mirrors the device into the curated SCALER devices.json so the
    //     5-min extract_configs.sh cron picks it up automatically
    //   - best-effort registers with Network Mapper MCP (LLDP discovery)
    //
    // The response shape is a SUPERSET of verify-credentials, so any
    // dialog code that already handles { ok, reason, message, ... } keeps
    // working unchanged. New fields the SSH dialog should consume on
    // success: ``key``, ``newly_registered``, ``newly_attached_for_user``,
    // ``monitor_started_subsystems``, ``references_count_total``,
    // ``references_user_count``.
    //
    // See topology/docs/AUTO_MONITOR_ON_ATTACH.md for the full design.
    async verifyAndRegister(deviceId, host, user, password, opts = {}) {
        const clean = (deviceId || '').trim();
        if (!clean) throw new Error('verifyAndRegister requires a deviceId');
        if (!host) throw new Error('verifyAndRegister requires a host');
        const {
            discoveryDepth = 'standard',
            monitorCadence = 'fast_initial',
            scopeType = 'topology',
            scopeId = '',
        } = opts;
        const response = await this._fetch(this._api('/api/devices/verify-and-register'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_id: clean,
                host: String(host || '').trim(),
                user: String(user || 'dnroot').trim() || 'dnroot',
                password: String(password || 'dnroot'),
                discovery_depth: discoveryDepth,
                monitor_cadence: monitorCadence,
                scope_type: scopeType,
                scope_id: scopeId,
            }),
        });
        if (!response.ok) {
            const err = await response.json().catch(
                () => ({ detail: `verify-and-register HTTP ${response.status}` }),
            );
            const e = new Error(err.detail || 'verify-and-register failed');
            e.httpStatus = response.status;
            throw e;
        }
        return response.json();
    },

    /** List devices the caller has a monitored-registry reference for. */
    async listMonitored() {
        const response = await this._fetch(this._api('/api/devices/monitored'));
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: `listMonitored HTTP ${response.status}` }));
            throw new Error(err.detail || 'listMonitored failed');
        }
        return response.json();
    },

    /** Single monitored device record + per-user reference state. Returns null on 404. */
    async getMonitored(ip) {
        const clean = (ip || '').trim();
        if (!clean) throw new Error('getMonitored requires an ip');
        const response = await this._fetch(this._api(`/api/devices/monitored/${encodeURIComponent(clean)}`));
        if (response.status === 404) return null;
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: `getMonitored HTTP ${response.status}` }));
            throw new Error(err.detail || 'getMonitored failed');
        }
        return response.json();
    },

    /** Idempotent attach for the caller. Use scopeId when available (Phase 4). */
    async attachReference(ip, { scopeType = 'topology', scopeId = '' } = {}) {
        const clean = (ip || '').trim();
        if (!clean) throw new Error('attachReference requires an ip');
        const response = await this._fetch(this._api(`/api/devices/monitored/${encodeURIComponent(clean)}/attach`), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scope_type: scopeType, scope_id: scopeId }),
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: `attachReference HTTP ${response.status}` }));
            throw new Error(err.detail || 'attachReference failed');
        }
        return response.json();
    },

    /** Detach the caller's reference. The response carries
     *  ``would_stop_monitoring`` so the caller can decide whether to
     *  show the "Stop monitoring this device?" modal. */
    async detachReference(ip, { scopeType = 'topology', scopeId = '' } = {}) {
        const clean = (ip || '').trim();
        if (!clean) throw new Error('detachReference requires an ip');
        const params = new URLSearchParams({
            scope_type: scopeType || 'topology',
            scope_id: scopeId || '',
        });
        const response = await this._fetch(
            this._api(`/api/devices/monitored/${encodeURIComponent(clean)}/attach?${params.toString()}`),
            { method: 'DELETE' },
        );
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: `detachReference HTTP ${response.status}` }));
            throw new Error(err.detail || 'detachReference failed');
        }
        return response.json();
    },

    // =========================================================================
    // DEVICE WATCHERS + EVENTS (per-user topology, shared device state)
    // =========================================================================
    //
    // These endpoints keep the shared device DB aware of which users have
    // which devices on their canvas. The backend uses the watcher set to
    // decide who to notify when shared state changes (ghost IP reaped,
    // mgmt IP updated, cluster event, ...). See topology-events.js for
    // the WebSocket side; these HTTP helpers are the REST fallback and
    // the explicit (un)register entry points.

    /**
     * Register the current user as a watcher of `deviceId`. Call when a
     * canvas opens or a new device is added. Idempotent -- re-calling
     * just refreshes last_seen_at on the shared row.
     */
    async watchDevice(deviceId, { topologyId = '', canvasIp = '' } = {}) {
        const clean = (deviceId || '').trim();
        if (!clean) throw new Error('watchDevice requires a deviceId');
        const response = await this._fetch(this._api(`/api/devices/${encodeURIComponent(clean)}/watch`), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topology_id: topologyId || '',
                canvas_ip: canvasIp || '',
            }),
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: `watch HTTP ${response.status}` }));
            throw new Error(err.detail || 'watch failed');
        }
        return response.json();
    },

    /** Remove this user from the device's watcher list. */
    async unwatchDevice(deviceId) {
        const clean = (deviceId || '').trim();
        if (!clean) throw new Error('unwatchDevice requires a deviceId');
        const response = await this._fetch(this._api(`/api/devices/${encodeURIComponent(clean)}/unwatch`), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: `unwatch HTTP ${response.status}` }));
            throw new Error(err.detail || 'unwatch failed');
        }
        return response.json();
    },

    /**
     * Bulk heartbeat / watcher-set sync. The returned object tells you
     * which rows were added, kept, and pruned by this call -- the backend
     * treats `deviceIds` as the *complete* canvas state, not a patch.
     */
    async watchHeartbeat(deviceIds) {
        const ids = Array.isArray(deviceIds) ? deviceIds : [];
        const response = await this._fetch(this._api('/api/devices/watch-heartbeat'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_ids: ids }),
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: `heartbeat HTTP ${response.status}` }));
            throw new Error(err.detail || 'heartbeat failed');
        }
        return response.json();
    },

    /** Who else is currently watching this device? */
    async listDeviceWatchers(deviceId, { activeOnly = true } = {}) {
        const clean = (deviceId || '').trim();
        if (!clean) throw new Error('listDeviceWatchers requires a deviceId');
        const q = activeOnly ? '' : '?active_only=false';
        const response = await this._fetch(this._api(`/api/devices/${encodeURIComponent(clean)}/watchers${q}`));
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'listDeviceWatchers failed');
        }
        return response.json();
    },

    /** Devices the current user is watching (cross-topology). */
    async listMyWatchedDevices({ activeOnly = true } = {}) {
        const q = activeOnly ? '' : '?active_only=false';
        const response = await this._fetch(this._api(`/api/devices/watched${q}`));
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'listMyWatchedDevices failed');
        }
        return response.json();
    },

    /**
     * Polling fallback for the events WebSocket. Prefer the WebSocket
     * (window.TopologyEvents) unless you specifically need to backfill
     * history or you're in a context that can't open a WS (service
     * worker, server-side render, etc.).
     */
    async listDeviceEvents(deviceId, { sinceId = null, sinceIso = null, limit = 50 } = {}) {
        const clean = (deviceId || '').trim();
        if (!clean) throw new Error('listDeviceEvents requires a deviceId');
        const params = new URLSearchParams();
        if (sinceId != null) params.set('since_id', String(sinceId));
        if (sinceIso) params.set('since_iso', sinceIso);
        if (limit) params.set('limit', String(limit));
        const qs = params.toString();
        const url = this._api(`/api/devices/${encodeURIComponent(clean)}/events${qs ? '?' + qs : ''}`);
        const response = await this._fetch(url);
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'listDeviceEvents failed');
        }
        return response.json();
    },

    /** Feed of recent events across every device the caller watches. */
    async listMyRecentEvents({ limit = 100 } = {}) {
        const q = limit ? `?limit=${encodeURIComponent(limit)}` : '';
        const response = await this._fetch(this._api(`/api/devices/events/recent${q}`));
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'listMyRecentEvents failed');
        }
        return response.json();
    },

    /** Read the caller's private per-device prefs (notes, last-working method, ...). */
    async getUserDevicePrefs(deviceId) {
        const clean = (deviceId || '').trim();
        if (!clean) throw new Error('getUserDevicePrefs requires a deviceId');
        const response = await this._fetch(this._api(`/api/devices/${encodeURIComponent(clean)}/user-prefs`));
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'getUserDevicePrefs failed');
        }
        return response.json();
    },

    /** Shallow-merge a patch into the caller's private per-device prefs. */
    async setUserDevicePrefs(deviceId, prefsPatch) {
        const clean = (deviceId || '').trim();
        if (!clean) throw new Error('setUserDevicePrefs requires a deviceId');
        const response = await this._fetch(this._api(`/api/devices/${encodeURIComponent(clean)}/user-prefs`), {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prefs: prefsPatch || {} }),
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'setUserDevicePrefs failed');
        }
        return response.json();
    },

    /**
     * Persist per-user per-device SSH credentials to the backend's
     * `~/.topology_users/<user>/devices.json` so every subsequent bridge
     * SSH call (`_get_credentials`) picks them up automatically. Without
     * this, creds typed into the dialog only lived in the topology JSON
     * and the backend kept falling back to `dnroot/dnroot`.
     * Requires JWT -- the backend scopes the file to the caller's username.
     *
     * @param {string} deviceId - canonical device id (label or hostname).
     * @param {string} user - SSH user to store.
     * @param {string} password - SSH password to store. Sent over HTTPS
     *   when the topology app is served over HTTPS; plain-text otherwise.
     */
    async saveDeviceCredentials(deviceId, user, password) {
        const clean = (deviceId || '').trim();
        if (!clean) throw new Error('saveDeviceCredentials requires a deviceId');
        if (!user) throw new Error('saveDeviceCredentials requires a user');
        if (!password) throw new Error('saveDeviceCredentials requires a password');
        const response = await this._fetch(this._api(`/api/auth/me/device-credentials/${encodeURIComponent(clean)}`), {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user, password }),
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'saveDeviceCredentials failed');
        }
        return response.json();
    },

    /** Fetch the metadata for a saved per-user device credential (no password in response). */
    async getDeviceCredential(deviceId) {
        const clean = (deviceId || '').trim();
        if (!clean) throw new Error('getDeviceCredential requires a deviceId');
        const response = await this._fetch(this._api(`/api/auth/me/device-credentials/${encodeURIComponent(clean)}`));
        if (response.status === 404) return null;
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'getDeviceCredential failed');
        }
        return response.json();
    },

    /** Remove the caller's stored credential for a device. */
    async deleteDeviceCredential(deviceId) {
        const clean = (deviceId || '').trim();
        if (!clean) throw new Error('deleteDeviceCredential requires a deviceId');
        const response = await this._fetch(this._api(`/api/auth/me/device-credentials/${encodeURIComponent(clean)}`), {
            method: 'DELETE',
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'deleteDeviceCredential failed');
        }
        return response.json();
    },

    /** List all of the caller's stored per-device credentials (passwords redacted). */
    async listDeviceCredentials() {
        const response = await this._fetch(this._api('/api/auth/me/device-credentials'));
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'listDeviceCredentials failed');
        }
        return response.json();
    },

    /**
     * Quick TCP check (e.g. port 22 on NCC management IP before iTerm).
     * @param {string} host - IPv4
     * @param {number} [port=22]
     */
    async checkPort(host, port = 22) {
        const q = `?host=${encodeURIComponent(host)}&port=${encodeURIComponent(port)}`;
        const response = await this._fetch(this._api('/api/ssh/check-port' + q));
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'check-port failed');
        }
        return response.json();
    },

    /**
     * Background: virsh console to NCC, show interfaces management, verify SSH; updates operational.json if ok.
     * @param {Object} p
     * @param {string} p.deviceId
     * @param {string} p.kvmHost
     * @param {string} [p.kvmUser]
     * @param {string} p.kvmPass
     * @param {string[]} [p.nccVms]
     * @param {string} [p.activeNcc]
     */
    async discoverNccMgmtIp({ deviceId, kvmHost, kvmUser, kvmPass, nccVms, activeNcc }) {
        const response = await this._fetch(this._api('/api/ssh/discover-ncc-mgmt'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_id: deviceId,
                kvm_host: kvmHost,
                kvm_user: kvmUser || 'dn',
                kvm_pass: kvmPass,
                ncc_vms: nccVms || [],
                active_ncc: activeNcc || ''
            })
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'NCC mgmt discovery failed');
        }
        return response.json();
    },
    
    /**
     * Discover console path via Zohar's DB (primary) or Device42 (fallback).
     * @param {string} deviceId - Device identifier
     * @param {string} [serialNumber] - Serial number (optional)
     * @param {string} [sshHost] - SSH host (optional)
     * @returns {Promise<{console_server, port, source, pdu_entries, serial_no}>}
     */
    async discoverConsole(deviceId, serialNumber = '', sshHost = '') {
        const response = await this._fetch(this._api('/api/ssh/discover-console'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: deviceId, serial_number: serialNumber, ssh_host: sshHost })
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'Console discovery failed');
        }
        return response.json();
    },

    /**
     * PDU power action (reboot / off / on / status) via Zohar's PDU mapping.
     * @param {Object} opts - { serial_number?, device_id?, action: reboot|off|on|status, pdu_host?, outlet? }
     * @returns {Promise<{success, status_output, pdu_host, outlet, cli_type}>}
     */
    async pduPower(opts) {
        const response = await this._fetch(this._api('/api/ssh/pdu-power'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(opts)
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'PDU action failed');
        }
        return response.json();
    },

    /**
     * Scan console server ports to find a device by hostname.
     * Probes each port on known ATEN console servers, looking for a prompt match.
     * @param {string} deviceId
     * @param {string} [serialNumber]
     * @param {string} [consoleServer] - optional hint (e.g. "console-b15")
     * @returns {Promise<{found, console_server, console_host, port, scanned, all_results}>}
     */
    async consoleScan(deviceId, serialNumber = '', consoleServer = '') {
        const response = await this._fetch(this._api('/api/ssh/console-scan'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_id: deviceId,
                serial_number: serialNumber,
                console_server: consoleServer
            })
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'Console scan failed');
        }
        return response.json();
    },

    /**
     * Open in-browser WebSocket terminal to device
     * @param {Object} opts - { deviceId, host, user, password, method, deviceLabel }
     */
    openTerminal(opts) {
        if (typeof window.TerminalPanel !== 'undefined' && window.TerminalPanel.open) {
            window.TerminalPanel.open(opts);
        } else {
            console.warn('[ScalerAPI] TerminalPanel not available');
        }
    },
    
    // =========================================================================
    // DEVICE MUTATIONS (add/update/delete inventory, static JSON)
    // =========================================================================
    
    /**
     * Add a new device
     * @param {Object} device - Device configuration
     * @param {string} device.hostname - Device hostname
     * @param {string} device.ip - Device IP address
     * @param {string} device.platform - Platform type (e.g., 'ncp')
     * @param {string} [device.username] - SSH username
     * @param {string} [device.password] - SSH password
     * @returns {Promise<Object>} Created device
     */
    async addDevice(device) {
        const response = await this._fetch(this._api('/api/devices/'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(device)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to add device');
        }
        return response.json();
    },
    
    /**
     * Update an existing device
     * @param {string} deviceId - Device identifier
     * @param {Object} updates - Fields to update
     * @returns {Promise<Object>} Updated device
     */
    async updateDevice(deviceId, updates) {
        const response = await this._fetch(this._api(`/api/devices/${encodeURIComponent(deviceId)}`), {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(updates)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update device');
        }
        return response.json();
    },
    
    /**
     * Delete a device
     * @param {string} deviceId - Device identifier
     * @returns {Promise<Object>} Deletion result
     */
    async deleteDevice(deviceId) {
        const response = await this._fetch(this._api(`/api/devices/${encodeURIComponent(deviceId)}`), {
            method: 'DELETE'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete device');
        }
        return response.json();
    },
    
    /**
     * Get device inventory from CURSOR/device_inventory.json
     * Contains LLDP neighbors and interface details from scaler-monitor
     * @returns {Promise<Object>} Inventory data with devices object
     */
    async getDeviceInventory() {
        try {
            // Try relative path first (same directory as index.html)
            const response = await fetch('device_inventory.json');
            if (!response.ok) {
                throw new Error(`Failed to fetch inventory: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.warn('[ScalerAPI] Failed to load device inventory:', error);
            return { devices: {} };
        }
    },
    
    /**
     * Test SSH connection to a device
     * @param {string} deviceId - Device identifier
     * @returns {Promise<{status: string, message: string}>}
     */
    async testConnection(deviceId, sshHost = '') {
        if (!this._bridgeUp && Date.now() < this._bridgeRetryAfter) {
            try {
                const h = await this.checkHealth();
                if (h?.scaler_bridge?.status === 'ok') {
                    this._bridgeUp = true;
                } else {
                    throw new Error('Config service unavailable. Start the app with ./start.sh or python3 serve.py.');
                }
            } catch (_) {
                throw new Error('Config service unavailable. Start the app with ./start.sh or python3 serve.py.');
            }
        }
        const params = sshHost ? `?ssh_host=${encodeURIComponent(sshHost)}` : '';
        const response = await this._fetch(this._api(`/api/devices/${encodeURIComponent(deviceId)}/test${params}`), {
            method: 'POST'
        });
        if (!response.ok) {
            let detail = 'Connection test failed';
            try {
                const err = await response.json();
                detail = err.detail || detail;
                if ((response.status === 501 || response.status === 502 || response.status === 503) &&
                    typeof detail === 'string' && detail.toLowerCase().includes('scaler bridge unavailable')) {
                    this._bridgeUp = false;
                    this._bridgeRetryAfter = Date.now() + 15000;
                }
            } catch (_) {}
            throw new Error(detail);
        }
        this._bridgeUp = true;
        return response.json();
    },
    
    /**
     * Sync (extract) running configuration from device
     * @param {string} deviceId - Device identifier
     * @returns {Promise<Object>} Sync result with config
     */
    async syncDevice(deviceId) {
        const response = await this._fetch(this._api(`/api/devices/${encodeURIComponent(deviceId)}/sync`), {
            method: 'POST'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Sync failed');
        }
        return response.json();
    },
    
    // =========================================================================
    // CONFIGURATION OPERATIONS
    // =========================================================================
    
    /**
     * Get running configuration for a device
     * @param {string} deviceId - Device identifier
     * @returns {Promise<{config: string}>}
     */
    async getRunningConfig(deviceId) {
        const response = await this._fetch(this._api(`/api/config/${encodeURIComponent(deviceId)}/running`));
        if (!response.ok) {
            throw new Error(`Failed to get running config for ${deviceId}`);
        }
        return response.json();
    },

    /**
     * Sync (fetch and cache) running config from device.
     * @param {string} deviceId - Device identifier
     * @param {string} [sshHost=''] - SSH host override
     * @returns {Promise<{status: string, message: string, lines: number}>}
     */
    async syncConfig(deviceId, sshHost = '') {
        const url = this._api(`/api/config/${encodeURIComponent(deviceId)}/sync${sshHost ? `?ssh_host=${encodeURIComponent(sshHost)}` : ''}`);
        const response = await this._fetch(url, { method: 'POST' });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Config sync failed');
        }
        return response.json();
    },

    /**
     * Get configuration summary for a device
     * @param {string} deviceId - Device identifier
     * @returns {Promise<Object>} Summary with system, interfaces, services, etc.
     */
    async getConfigSummary(deviceId) {
        const response = await this._fetch(this._api(`/api/config/${encodeURIComponent(deviceId)}/summary`));
        if (!response.ok) {
            throw new Error(`Failed to get config summary for ${deviceId}`);
        }
        return response.json();
    },
    
    /**
     * Get unified device context for wizard suggestions (interfaces, LLDP, config summary, free interfaces).
     * @param {string} deviceId - Device identifier
     * @param {boolean} [live=false] - If true, fetch live config from device
     * @returns {Promise<Object>} Device context with interfaces, lldp, config_summary, wan_interfaces, services, etc.
     */
    /**
     * Fast stack-only refresh used by the Stack dialog Refresh button.
     * Single SSH session that runs ONLY `show system stack` + `show system`
     * (no LLDP, no shell-into-baseos, no config pull). On a healthy active
     * NCC this finishes in 4-8 s vs 15-25 s for the full live-context path,
     * and stays well within the 50-s frontend timeout even on a busy NCC.
     *
     * @param {string} deviceId
     * @param {string} [sshHost]    SSH IP/hostname from canvas device
     * @param {object} [opts]
     * @param {boolean} [opts.bypassCache=false]  Bust the per-(device, user)
     *                                            30-s coalescer so the click
     *                                            triggers a real probe.
     * @param {AbortSignal} [opts.signal]
     * @returns {Promise<{components, device_state, active_ncc_node,
     *                   stack_fetched_at, source, raw_output?}>}
     */
    async getDeviceStackFast(deviceId, sshHost = '', opts = {}) {
        const params = new URLSearchParams();
        if (sshHost) params.set('ssh_host', sshHost);
        if (opts && opts.bypassCache) params.set('bypass_cache', 'true');
        if (opts && opts.identityGuard) params.set('identity_guard', JSON.stringify(opts.identityGuard));
        const qs = params.toString();
        const url = this._api(`/api/devices/${encodeURIComponent(deviceId)}/stack-fast${qs ? '?' + qs : ''}`);
        // 25 s wall-clock timeout: comfortably above the expected 4-15 s
        // happy-path while still well under the dialog's 50-s outer timeout
        // so we have headroom to fall back to /context?live=true.
        const fetchOpts = opts && opts.signal ? { signal: opts.signal } : {};
        const response = await this._fetchWithTimeout(url, fetchOpts, 25000);
        if (!response.ok) {
            const body = await response.json().catch(() => ({}));
            const err = new Error(body.detail || body.error || `Failed stack-fast for ${deviceId}`);
            err.status = response.status;
            throw err;
        }
        return response.json();
    },

    async getDeviceContext(deviceId, live = false, sshHost = '', opts = {}) {
        const params = new URLSearchParams();
        if (live) params.set('live', 'true');
        if (sshHost) params.set('ssh_host', sshHost);
        if (opts && opts.bypassCache) params.set('bypass_cache', 'true');
        if (opts && opts.identityGuard) params.set('identity_guard', JSON.stringify(opts.identityGuard));
        // Scope the request so a per-user per-topology override (e.g. a
        // CL-* pick for a device the bridge mis-read as SA-*) takes
        // precedence over the global scaler curated cache. Fields are
        // left empty when no topology is active; backend handles that as
        // "fall back to the per_user layer, then the global chain".
        try {
            const scope = (typeof this._getTopologyScope === 'function')
                ? this._getTopologyScope() : { domain_id: '', topology_id: '' };
            if (scope && scope.domain_id) params.set('domain_id', scope.domain_id);
            if (scope && scope.topology_id) params.set('topology_id', scope.topology_id);
        } catch (_) {}
        const qs = params.toString();
        const url = this._api(`/api/devices/${encodeURIComponent(deviceId)}/context${qs ? '?' + qs : ''}`);
        const timeout = live ? 30000 : 8000;
        // `opts.signal` lets the DeviceState orchestrator abort an
        // in-flight context fetch when the user switches topology or
        // logs out, so stale responses never land on a swapped canvas.
        const fetchOpts = opts && opts.signal ? { signal: opts.signal } : {};
        const response = await this._fetchWithTimeout(url, fetchOpts, timeout);
        if (!response.ok) {
            const body = await response.json().catch(() => ({}));
            const err = new Error(body.detail || `Failed to get device context for ${deviceId}`);
            err.status = response.status;
            // RFC 7231: Retry-After is either an HTTP-date or a decimal number
            // of seconds. Only the number form is common for 429/503 from our
            // bridge; parse it if present.
            const raw = response.headers.get('Retry-After');
            if (raw) {
                const secs = parseInt(raw, 10);
                if (!Number.isNaN(secs) && secs >= 0) err.retryAfter = secs;
            }
            throw err;
        }
        return response.json();
    },

    /**
     * Get git_commit only (lightweight SSH). Use when context returns null git_commit.
     * @param {string} deviceId - Device identifier
     * @param {string} [sshHost] - SSH IP/hostname from canvas device
     * @param {string} [sshUser] - SSH username (falls back to global default)
     * @param {string} [sshPassword] - SSH password (falls back to global default)
     * @returns {Promise<{git_commit: string|null}>}
     */
    async getDeviceGitCommit(deviceId, sshHost = '', sshUser = '', sshPassword = '') {
        const params = new URLSearchParams();
        if (sshHost) params.set('ssh_host', sshHost);
        if (sshUser) params.set('ssh_user', sshUser);
        if (sshPassword) params.set('ssh_password', sshPassword);
        const qs = params.toString();
        const url = this._api(`/api/devices/${encodeURIComponent(deviceId)}/git-commit${qs ? '?' + qs : ''}`);
        const response = await this._fetchWithTimeout(url, {}, 10000);
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `Failed to get git_commit for ${deviceId}`);
        }
        return response.json();
    },

    /**
     * Get next-wizard suggestions from backend (device_id, completed_wizard, created_data).
     * @param {Object} params - { device_id, completed_wizard, created_data, ssh_host }
     * @returns {Promise<{suggestions: Array}>} Suggestions with wizard, reason, prefill
     */
    async wizardSuggestions(params) {
        const response = await this._fetch(this._api('/api/wizard/suggestions'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Wizard suggestions failed');
        }
        return response.json();
    },

    /**
     * Get interfaces configuration for a device
     * @param {string} deviceId - Device identifier
     * @returns {Promise<Array>} List of interface configurations
     */
    async getInterfaces(deviceId) {
        const response = await this._fetch(this._api(`/api/config/${encodeURIComponent(deviceId)}/interfaces`));
        if (!response.ok) {
            throw new Error(`Failed to get interfaces for ${deviceId}`);
        }
        return response.json();
    },
    
    /**
     * Get services configuration for a device
     * @param {string} deviceId - Device identifier
     * @returns {Promise<Object>} Services summary
     */
    // =========================================================================
    // PUSH/DELETE OPERATIONS
    // =========================================================================
    
    /**
     * Validate configuration before pushing
     * @param {Object} request - Validation request
     * @param {string} request.device_id - Target device
     * @param {string} request.config - Configuration to validate
     * @param {string} request.hierarchy - Hierarchy section
     * @returns {Promise<Object>} Validation result
     */
    async validateConfig(request) {
        const response = await this._fetch(this._api('/api/operations/validate'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(request)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Validation failed');
        }
        return response.json();
    },
    
    // =========================================================================
    // CONFIG GENERATION - Uses SCALER's proper DNOS syntax
    // =========================================================================
    
    /**
     * Generate interface configuration using SCALER's DNOS syntax
     * @param {Object} params - Interface parameters
     * @returns {Promise<{config: string, lines: number, hierarchy: string}>}
     */
    async generateInterfaces(params) {
        const response = await this._fetch(this._api('/api/config/generate/interfaces'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate interfaces');
        }
        return response.json();
    },

    async saveConfigForLater(deviceId, config) {
        const response = await this._fetch(this._api(`/api/config/${encodeURIComponent(deviceId)}/save`), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ config })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save config');
        }
        return response.json();
    },

    async generateUndo(params) {
        const response = await this._fetch(this._api('/api/config/generate/undo'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate undo config');
        }
        return response.json();
    },

    async scanExisting(params) {
        const response = await this._fetch(this._api('/api/config/scan-existing'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Scan failed');
        }
        return response.json();
    },

    async scanIPs(params) {
        const response = await this._fetch(this._api('/api/config/scan-ips'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'IP scan failed');
        }
        return response.json();
    },

    async detectPattern(params) {
        const response = await this._fetch(this._api('/api/config/detect-pattern'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Pattern detection failed');
        }
        return response.json();
    },

    async detectL2ACParent(params) {
        const response = await this._fetch(this._api('/api/config/detect/l2ac-parent'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'L2-AC parent detection failed');
        }
        return response.json();
    },

    async detectBGPNeighbors(params) {
        const response = await this._fetch(this._api('/api/config/detect/bgp-neighbors'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'BGP neighbors detection failed');
        }
        return response.json();
    },

    async getMenuSummary(deviceIds = []) {
        const ids = Array.isArray(deviceIds) ? deviceIds : [];
        const qs = ids.length ? '?device_ids=' + encodeURIComponent(ids.join(',')) : '';
        const response = await this._fetch(this._api('/api/config/menu-summary' + qs));
        if (!response.ok) return { devices: 0, interfaces: { phys: 0, bundle: 0, subif: 0 }, services: { fxc: 0, l2vpn: 0, evpn: 0, vpws: 0, vrf: 0 }, lldp_total: 0 };
        return response.json();
    },

    async detectScaleSuggestions(params) {
        const response = await this._fetch(this._api('/api/config/detect/scale-suggestions'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Scale suggestions failed');
        }
        return response.json();
    },

    async generateSystem(params) {
        const response = await this._fetch(this._api('/api/config/generate/system'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'System config generation failed');
        }
        return response.json();
    },

    async validatePolicy(params) {
        const response = await this._fetch(this._api('/api/config/validate/policy'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Policy validation failed');
        }
        return response.json();
    },

    async generateRoutePolicyStructured(params) {
        const response = await this._fetch(this._api('/api/config/generate/route-policy-structured'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Route policy generation failed');
        }
        return response.json();
    },

    async getSmartDefaults(deviceId, sshHost = '') {
        const url = this._api(`/api/config/templates/smart-defaults/${encodeURIComponent(deviceId)}${sshHost ? `?ssh_host=${encodeURIComponent(sshHost)}` : ''}`);
        const response = await this._fetch(url);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Smart defaults failed');
        }
        return response.json();
    },

    /**
     * Generate service configuration using SCALER's DNOS syntax
     * @param {Object} params - Service parameters
     * @returns {Promise<{config: string, lines: number, hierarchy: string}>}
     */
    async generateServices(params) {
        const response = await this._fetch(this._api('/api/config/generate/services'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate services');
        }
        return response.json();
    },
    async generateBGP(params) {
        const response = await this._fetch(this._api('/api/config/generate/bgp'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate BGP');
        }
        return response.json();
    },
    async generateRoutingPolicy(params) {
        const response = await this._fetch(this._api('/api/config/generate/routing-policy'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Routing policy generation failed');
        }
        return response.json();
    },
    async generateFlowSpec(params) {
        const response = await this._fetch(this._api('/api/config/generate/flowspec'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'FlowSpec generation failed');
        }
        return response.json();
    },
    async flowspecDependencyCheck(params) {
        const response = await this._fetch(this._api('/api/config/flowspec-dependency-check'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'FlowSpec dependency check failed');
        }
        return response.json();
    },
    async generateIGP(params) {
        const response = await this._fetch(this._api('/api/config/generate/igp'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate IGP');
        }
        return response.json();
    },
    async batchGenerate(items) {
        const response = await this._fetch(this._api('/api/config/generate/batch'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ items })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Batch generation failed');
        }
        return response.json();
    },
    async previewConfigDiff(deviceId, config, sshHost = '') {
        const response = await this._fetch(this._api('/api/config/preview-diff'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ device_id: deviceId, config, ssh_host: sshHost })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Diff preview failed');
        }
        return response.json();
    },
    async mirrorAnalyze(params) {
        const response = await this._fetch(this._api('/api/mirror/analyze'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Mirror analyze failed');
        }
        return response.json();
    },
    async mirrorGenerate(params) {
        const response = await this._fetch(this._api('/api/mirror/generate'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Mirror generate failed');
        }
        return response.json();
    },
    async mirrorPreviewDiff(params) {
        const response = await this._fetch(this._api('/api/mirror/preview-diff'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Mirror preview failed');
        }
        return response.json();
    },
    async compareConfigs(deviceIds) {
        const response = await this._fetch(this._api('/api/config/compare'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ device_ids: deviceIds })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Compare failed');
        }
        return response.json();
    },
    async getConfigDiff(deviceId) {
        const response = await this._fetch(this._api(`/api/config/${encodeURIComponent(deviceId)}/diff`));
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Diff failed');
        }
        return response.json();
    },
    async getTemplates() {
        const response = await this._fetch(this._api('/api/config/templates'));
        if (!response.ok) throw new Error('Failed to get templates');
        return response.json();
    },
    async generateTemplate(templateName, values) {
        const response = await this._fetch(this._api('/api/config/templates/generate'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ template_name: templateName, values: values || {} })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Template generation failed');
        }
        return response.json();
    },
    async discoverDevice(ip) {
        const response = await this._fetch(this._api('/api/devices/discover'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ ip })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Discovery failed');
        }
        return response.json();
    },
    async getDeleteHierarchyOptions() {
        const response = await this._fetch(this._api('/api/config/delete-hierarchy-options'));
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'Failed to load hierarchy options');
        }
        return response.json();
    },
    async deleteHierarchyOp(deviceId, hierarchy, dryRun = true, subPath = '') {
        const body = { device_id: deviceId, hierarchy, dry_run: dryRun };
        if (subPath && subPath.trim()) body.sub_path = subPath.trim();
        const response = await this._fetch(this._api('/api/operations/delete-hierarchy'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Delete failed');
        }
        return response.json();
    },
    
    /**
     * Push configuration to a device
     * @param {Object} request - Push request
     * @param {string} request.device_id - Target device
     * @param {string} request.config - Configuration to push
     * @param {string} request.hierarchy - Hierarchy section
     * @param {string} request.mode - Push mode ('merge' or 'replace')
     * @param {boolean} [request.dry_run=true] - If true, only validate
     * @returns {Promise<{job_id: string, status: string}>}
     */
    async setHostname(deviceId, hostname, sshHost) {
        const response = await this._fetch(this._api(`/api/devices/${encodeURIComponent(deviceId)}/set-hostname`), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ hostname, ssh_host: sshHost || '' })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Hostname change failed');
        }
        return response.json();
    },

    /**
     * Persist a manually-chosen ``system_type`` under the authenticated
     * user's workspace (``~/.topology_users/<user>/device_overrides.json``).
     *
     * Used by the Image Upgrade wizard's CL-only mismatch picker so the
     * operator's correction (e.g. CL-86 for a cluster mis-detected as
     * SA-40C8CD) survives across page reloads until a live DNOS probe
     * rewrites operational.json with the matching value.
     *
     * Scope:
     *   * When ``TopologySync`` reports an active topology, both
     *     ``domain_id`` and ``topology_id`` are included so the override
     *     is scoped to that topology specifically (per-user + per-
     *     topology layer).
     *   * The per_user fallback layer is ALWAYS written too, so opening
     *     the same physical device from another topology of the same
     *     user still benefits from the pick.
     *   * The global scaler curated cache (``db/devices.json``) is NO
     *     longer touched by this endpoint -- that's live-probe-only now,
     *     which fixes the cross-user leak documented in
     *     ``.cursor/rules/multiuser-by-default.mdc``.
     *
     * Idempotent (writing the same value again is a no-op on disk).
     */
    async persistSystemType(deviceId, systemType, sshHost, opts) {
        const scope = (typeof this._getTopologyScope === 'function')
            ? this._getTopologyScope() : { domain_id: '', topology_id: '' };
        // ``opts.commitGlobal`` promotes the pick into ``SCALER/db/devices.json``
        // alongside the per-user override, tagged ``operator_pinned``. The
        // backend only honours that flag for cluster (``CL-*``) picks so a
        // non-cluster value can't accidentally leak into another operator's
        // topology through the shared scaler DB. See the PE-4 / CL-86 write-up
        // in ``devices.py::persist_device_system_type`` for the guard rails.
        const commitGlobal = !!(opts && opts.commitGlobal);
        const payload = {
            system_type: systemType,
            ssh_host: sshHost || '',
            domain_id: (scope && scope.domain_id) || '',
            topology_id: (scope && scope.topology_id) || '',
            commit_global: commitGlobal,
        };
        const response = await this._fetch(this._api(`/api/devices/${encodeURIComponent(deviceId)}/system-type`), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload),
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'system_type persist failed');
        }
        return response.json();
    },

    /**
     * Toggle SSH connection pool on/off for faster operations.
     * @param {boolean} enabled - true to enable pool, false to disable
     * @returns {Promise<{enabled: boolean, count: number}>}
     */
    async toggleSSHPool(enabled) {
        const response = await this._fetch(this._api('/api/ssh-pool/toggle'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ enabled: !!enabled })
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'SSH pool toggle failed');
        }
        return response.json();
    },

    /**
     * Get SSH pool status: enabled, count, per-device connection state.
     * @returns {Promise<{enabled: boolean, count: number, entries: Array}>}
     */
    async getSSHPoolStatus() {
        const response = await this._fetch(this._api('/api/ssh-pool/status'));
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'SSH pool status failed');
        }
        return response.json();
    },

    /**
     * Evict (force-close) pooled SSH client(s) for a device.
     * Call when device is deleted or credentials changed.
     * @param {string} ip - Canvas SSH host (IPv4, hostname, or serial)
     * @param {string} [deviceId] - Device label for resolving serial/hostname to mgmt IP
     * @returns {Promise<{status: string, evicted: string, evicted_keys?: string[]}>}
     */
    async evictSSHPoolConnection(ip, deviceId = '') {
        const body = { ip: ip || '' };
        if (deviceId) {
            body.device_id = deviceId;
        }
        const response = await this._fetch(this._api('/api/ssh-pool/evict'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'SSH pool evict failed');
        }
        return response.json();
    },

    async getPushEstimate(params) {
        const response = await this._fetch(this._api('/api/config/push/estimate'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Estimate failed');
        }
        return response.json();
    },

    async pushConfig(request) {
        const body = {
            ...request,
            push_method: request.push_method || 'terminal_paste',
            load_mode: request.load_mode || 'merge',
        };
        const response = await this._fetch(this._api('/api/operations/push'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Push failed');
        }
        return response.json();
    },

    /**
     * Commit held config on same SSH session (after dry_run push when check passed).
     * @param {string} jobId - Job ID from pushConfig
     * @returns {Promise<{status: string, success: boolean, message: string}>}
     */
    async commitHeldJob(jobId) {
        const response = await this._fetch(this._api(`/api/operations/push/${encodeURIComponent(jobId)}/commit`), {
            method: 'POST'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Commit failed');
        }
        return response.json();
    },

    /**
     * Cancel held config (discard candidate) and close SSH session.
     * @param {string} jobId - Job ID from pushConfig
     * @returns {Promise<{status: string, success: boolean, message: string}>}
     */
    async cancelHeldJob(jobId) {
        const response = await this._fetch(this._api(`/api/operations/push/${encodeURIComponent(jobId)}/cancel`), {
            method: 'POST'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Cancel failed');
        }
        return response.json();
    },

    /**
     * Cleanup dirty candidate on device after failed commit check.
     * @param {string} jobId - Job ID from pushConfig
     * @returns {Promise<{status: string, success: boolean, message: string}>}
     */
    async cleanupHeldJob(jobId) {
        const response = await this._fetch(this._api(`/api/operations/push/${encodeURIComponent(jobId)}/cleanup`), {
            method: 'POST'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Cleanup failed');
        }
        return response.json();
    },

    async getJobs() {
        if (!this._bridgeUp && Date.now() < this._bridgeRetryAfter) return { jobs: [] };
        if (window.TopologyAuth && !window.TopologyAuth.isAuthenticated()) {
            this._bridgeUp = false;
            this._bridgeRetryAfter = Date.now() + 30000;
            return { jobs: [] };
        }
        try {
            const response = await this._fetch(this._api('/api/operations/jobs'));
            if (!response.ok) {
                if (response.status === 401 || response.status === 403) {
                    this._bridgeUp = false;
                    this._bridgeRetryAfter = Date.now() + 30000;
                    return { jobs: [] };
                }
                if (response.status === 501 || response.status === 502 || response.status === 503 || response.status === 500) {
                    this._bridgeUp = false;
                    this._bridgeRetryAfter = Date.now() + 15000;
                    return { jobs: [] };
                }
                throw new Error('Failed to fetch jobs');
            }
            this._bridgeUp = true;
            return response.json();
        } catch (e) {
            this._bridgeUp = false;
            this._bridgeRetryAfter = Date.now() + 10000;
            return { jobs: [] };
        }
    },

    async getJob(jobId) {
        const response = await this._fetch(this._api(`/api/operations/jobs/${encodeURIComponent(jobId)}`));
        if (!response.ok) {
            if (response.status === 404) return null;
            throw new Error('Failed to fetch job');
        }
        return response.json();
    },

    async retryJob(jobId) {
        const response = await this._fetch(this._api(`/api/operations/jobs/${encodeURIComponent(jobId)}/retry`), { method: 'POST' });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Retry failed');
        }
        return response.json();
    },

    async deleteJob(jobId) {
        const response = await this._fetch(this._api(`/api/operations/jobs/${encodeURIComponent(jobId)}`), { method: 'DELETE' });
        if (!response.ok) throw new Error('Failed to delete job');
        return response.json();
    },

    /**
     * Get platform limits for a device (max_subifs, etc.)
     * @param {string} deviceId - Device identifier
     * @returns {Promise<{max_subifs: number}>}
     */
    async getLimits(deviceId) {
        if (!this._bridgeUp && Date.now() < this._bridgeRetryAfter) return { max_subifs: 20480 };
        const response = await this._fetch(this._api(`/api/config/limits/${encodeURIComponent(deviceId)}`));
        if (!response.ok) {
            if (response.status === 404) {
                return { max_subifs: 20480 };
            }
            if (response.status === 501 || response.status === 502 || response.status === 503) {
                this._bridgeUp = false;
                this._bridgeRetryAfter = Date.now() + 15000;
                return { max_subifs: 20480 };
            }
            throw new Error('Failed to fetch limits');
        }
        this._bridgeUp = true;
        return response.json();
    },
    
    /**
     * Delete a hierarchy section from a device
     * @param {string} deviceId - Target device
     * @param {string} hierarchy - Hierarchy to delete
     * @returns {Promise<{job_id: string, status: string}>}
     */
    async deleteHierarchy(deviceId, hierarchy) {
        return this.deleteHierarchyOp(deviceId, hierarchy, false);
    },
    
    /**
     * Sync multihoming between devices
     * @param {Object} request - Sync request
     * @param {Array<string>} request.device_ids - Device IDs to sync
     * @param {number} [request.esi_prefix] - ESI prefix
     * @param {boolean} [request.match_neighbor=true] - Match by neighbor
     * @param {string} [request.redundancy_mode='single-active'] - Redundancy mode
     * @returns {Promise<{job_id: string, status: string}>}
     */
    async syncMultihoming(request) {
        const response = await this._fetch(this._api('/api/operations/multihoming/sync'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(request)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Multihoming sync failed');
        }
        return response.json();
    },
    
    /**
     * Compare multihoming configurations between devices
     * @param {Array<string>} deviceIds - Devices to compare
     * @returns {Promise<Object>} Comparison result
     */
    async compareMultihoming(deviceIds) {
        const response = await this._fetch(this._api('/api/operations/multihoming/compare'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({device_ids: deviceIds})
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Comparison failed');
        }
        return response.json();
    },
    
    /**
     * Compare full configurations between two devices
     * @param {Array<string>} deviceIds - Two device IDs to compare
     * @param {string} [hierarchy] - Optional hierarchy to filter (interfaces, services, etc.)
     * @returns {Promise<Object>} Diff result
     */
    /**
     * Cancel a running operation
     * @param {string} jobId - Job identifier
     * @returns {Promise<Object>} Cancellation result
     */
    async cancelOperation(jobId) {
        const response = await this._fetch(this._api(`/api/operations/${encodeURIComponent(jobId)}/cancel`), {
            method: 'POST'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Cancel failed');
        }
        return response.json();
    },
    
    // =========================================================================
    // DNAAS DISCOVERY OPERATIONS
    // =========================================================================
    
    /**
     * Start a DNAAS path discovery
     * @param {Object} request - Discovery request
     * @param {string} request.serial1 - First device serial/hostname
     * @param {string} [request.serial2] - Second device serial/hostname
     * @param {boolean} [request.bd_aware=false] - Enable bridge domain discovery
     * @returns {Promise<{job_id: string, message: string}>}
     */
    async startDnaasDiscovery(request) {
        let response;
        try {
            response = await this._fetch(this._api('/api/dnaas/discovery/start'), {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(request)
            });
        } catch (fetchErr) {
            if (fetchErr.message && (fetchErr.message.includes('Failed to fetch') || fetchErr.message.includes('NetworkError'))) {
                throw new Error('Discovery API unreachable - check if serve.py and discovery_api.py are running');
            }
            throw fetchErr;
        }
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            const msg = error.error || error.detail || (error.endpoint ? `Endpoint ${error.endpoint} failed` : null) || `HTTP ${response.status}`;
            throw new Error(msg);
        }
        return response.json();
    },
    
    /**
     * Get DNAAS discovery job status
     * @param {string} jobId - Job identifier
     * @returns {Promise<Object>} Discovery status with progress and output
     */
    async getDnaasStatus(jobId) {
        const response = await this._fetch(this._api(`/api/dnaas/discovery/status?job_id=${encodeURIComponent(jobId)}`));
        if (!response.ok) {
            throw new Error(`Discovery job not found: ${jobId}`);
        }
        return response.json();
    },

    async findDnaasDiscovery(serial) {
        const response = await this._fetch(this._api(`/api/dnaas/discovery/find?serial=${encodeURIComponent(serial || '')}`));
        if (!response.ok) return { job_id: null, status: 'none' };
        return response.json();
    },
    
    /**
     * List available DNAAS discovery result files
     * @returns {Promise<{files: Array}>}
     */
    async listDnaasFiles() {
        const response = await this._fetch(this._api('/api/dnaas/discovery/list'));
        if (!response.ok) {
            throw new Error('Failed to list discovery files');
        }
        return response.json();
    },
    
    /**
     * Get a specific DNAAS discovery result file
     * @param {string} filename - File name (e.g., dnaas_path_20251230_123456.json)
     * @returns {Promise<Object>} Discovery result data
     */
    async getDnaasFile(filename) {
        const response = await this._fetch(this._api(`/api/dnaas/discovery/file/${encodeURIComponent(filename)}`));
        if (!response.ok) {
            throw new Error(`Discovery file not found: ${filename}`);
        }
        return response.json();
    },
    
    /**
     * Check DNAAS discovery server health
     * @returns {Promise<{status: string, message: string}>}
     */
    async checkDnaasHealth() {
        const response = await this._fetch(this._api('/api/dnaas/discovery/health'));
        return response.json();
    },
    
    /**
     * Cancel a running DNAAS discovery job
     * @param {string} jobId - Job identifier to cancel
     * @returns {Promise<{status: string, message: string}>}
     */
    async cancelDnaasDiscovery(jobId) {
        const response = await this._fetch(this._api('/api/dnaas/discovery/cancel'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ job_id: jobId })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Cancel failed');
        }
        return response.json();
    },
    
    // =========================================================================
    // MULTI-BD DISCOVERY (Discover ALL Bridge Domains)
    // =========================================================================
    
    /**
     * Start Multi-BD discovery - discovers ALL Bridge Domains from a device
     * @param {Object} request - { serial: string }
     * @returns {Promise<{job_id: string, message: string}>}
     */
    async startMultiBDDiscovery(request) {
        const response = await this._fetch(this._api('/api/dnaas/multi-bd/start'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(request)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Multi-BD discovery start failed');
        }
        return response.json();
    },
    
    /**
     * Get Multi-BD discovery status
     * @param {string} jobId - Job ID from startMultiBDDiscovery
     * @returns {Promise<{status: string, message?: string, bd_count?: number, result_file?: string}>}
     */
    async getMultiBDDiscoveryStatus(jobId) {
        const response = await this._fetch(this._api(`/api/dnaas/multi-bd/status?job_id=${encodeURIComponent(jobId)}`));
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `Multi-BD job not found: ${jobId}`);
        }
        return response.json();
    },

    async findMultiBDDiscovery(serial) {
        const response = await this._fetch(this._api(`/api/dnaas/multi-bd/find?serial=${encodeURIComponent(serial || '')}`));
        if (!response.ok) return { job_id: null, status: 'none' };
        return response.json();
    },
    
    /**
     * Get Multi-BD discovery result file
     * @param {string} filename - Result file name
     * @returns {Promise<Object>} - Topology data with BD metadata
     */
    async getMultiBDFile(filename) {
        const response = await this._fetch(this._api(`/api/dnaas/multi-bd/file/${encodeURIComponent(filename)}`));
        if (!response.ok) {
            throw new Error(`Multi-BD file not found: ${filename}`);
        }
        return response.json();
    },
    
    /**
     * Cancel Multi-BD discovery job
     * @param {string} jobId - Job ID to cancel
     * @returns {Promise<{status: string, message: string}>}
     */
    async cancelMultiBDDiscovery(jobId) {
        const response = await this._fetch(this._api('/api/dnaas/multi-bd/cancel'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ job_id: jobId })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Multi-BD cancel failed');
        }
        return response.json();
    },
    
    // =========================================================================
    // WEBSOCKET FOR REAL-TIME PROGRESS
    // =========================================================================
    
    /**
     * Connect to WebSocket for real-time progress updates
     * @param {string} jobId - Job identifier to track
     * @param {Object} callbacks - Event callbacks
     * @param {Function} [callbacks.onProgress] - Called with (percent, message)
     * @param {Function} [callbacks.onTerminal] - Called with (line)
     * @param {Function} [callbacks.onStep] - Called with (current, total, name)
     * @param {Function} [callbacks.onComplete] - Called with (success, result)
     * @param {Function} [callbacks.onError] - Called with (message)
     * @param {Function} [callbacks.onClose] - Called when connection closes
     * @returns {WebSocket} The WebSocket instance
     */
    /**
     * Connect to push progress via SSE (EventSource). Use for config push jobs.
     * @param {string} jobId - Job identifier from pushConfig
     * @param {Object} callbacks - Same as connectProgress
     * @returns {EventSource} The EventSource instance
     */
    connectPushProgress(jobId, callbacks, options) {
        let sseUrl = this._api(`/api/config/push/progress/${encodeURIComponent(jobId)}`);
        if (window.TopologyAuth && window.TopologyAuth.getToken()) {
            sseUrl += '?token=' + encodeURIComponent(window.TopologyAuth.getToken());
        }
        const url = sseUrl;
        let retryCount = 0;
        const MAX_RETRIES = 5;
        let done = false;
        let currentEs = null;
        let heartbeatTimer = null;
        const HEARTBEAT_TIMEOUT = 30000;
        let _terminalLinesSent = (options && options.terminalOffset) || 0;

        const connect = () => {
            const es = new EventSource(url);
            currentEs = es;

            const resetHeartbeat = () => {
                if (heartbeatTimer) clearTimeout(heartbeatTimer);
                heartbeatTimer = setTimeout(() => {
                    if (done) return;
                    console.warn('[ScalerAPI] No SSE data for 30s -- reconnecting');
                    es.close();
                    scheduleReconnect();
                }, HEARTBEAT_TIMEOUT);
            };

            const scheduleReconnect = () => {
                if (done || retryCount >= MAX_RETRIES) {
                    if (!done) callbacks.onError?.('Connection lost after ' + MAX_RETRIES + ' retries. The operation may still be running.');
                    return;
                }
                retryCount++;
                const delay = Math.min(1000 * Math.pow(2, retryCount - 1), 10000);
                console.log(`[ScalerAPI] SSE reconnect attempt ${retryCount}/${MAX_RETRIES} in ${delay}ms`);
                setTimeout(() => { if (!done) connect(); }, delay);
            };

            resetHeartbeat();
            es.onmessage = (event) => {
                resetHeartbeat();
                retryCount = 0;
                try {
                    const data = JSON.parse(event.data);
                    const terminal = data.terminal || [];
                    const terminalFull = data.terminal_full || [];
                    if (Array.isArray(terminal) && terminal.length && callbacks.onTerminal) {
                        const fullCount = terminalFull.length || (_terminalLinesSent + terminal.length);
                        if (_terminalLinesSent > 0 && terminal.length === fullCount) {
                            const newOnly = terminalFull.slice(_terminalLinesSent);
                            newOnly.forEach((chunk) => callbacks.onTerminal(chunk));
                            _terminalLinesSent = fullCount;
                        } else {
                            terminal.forEach((chunk) => callbacks.onTerminal(chunk));
                            _terminalLinesSent += terminal.length;
                        }
                    }
                    if (data.done) {
                        done = true;
                        if (heartbeatTimer) clearTimeout(heartbeatTimer);
                        es.close();
                        callbacks.onProgress?.(data.success ? 100 : 0, data.message, {
                            elapsed_seconds: data.elapsed_seconds,
                            estimated_remaining_seconds: 0,
                        });
                        if (data.device_state && typeof callbacks.onDeviceState === 'function') {
                            callbacks.onDeviceState(data.device_state);
                        }
                        callbacks.onComplete?.(data.success, { message: data.message, terminal_full: data.terminal_full, cancelled: data.cancelled, device_state: data.device_state });
                    } else if (data.awaiting_decision || data.status === 'awaiting_decision') {
                        callbacks.onAwaitingDecision?.(data);
                    } else {
                        const pct = data.percent || 0;
                        callbacks.onProgress?.(pct, data.message || data.phase, {
                            elapsed_seconds: data.elapsed_seconds,
                            estimated_remaining_seconds: data.estimated_remaining_seconds,
                        });
                        if (data.device_state && typeof callbacks.onDeviceState === 'function') {
                            callbacks.onDeviceState(data.device_state);
                        }
                    }
                } catch (e) {
                    console.error('[ScalerAPI] Failed to parse SSE message:', e);
                }
            };
            es.onerror = () => {
                if (heartbeatTimer) clearTimeout(heartbeatTimer);
                es.close();
                if (!done) scheduleReconnect();
            };
        };

        connect();
        return { close: () => { done = true; if (heartbeatTimer) clearTimeout(heartbeatTimer); currentEs?.close(); } };
    },

    connectProgress(jobId, callbacks, options) {
        if (typeof EventSource !== 'undefined') {
            return this.connectPushProgress(jobId, callbacks, options);
        }
        // Fallback: WebSocket (if serve.py ever adds WS support)
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/progress/${jobId}`;
        
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log(`[ScalerAPI] WebSocket connected for job ${jobId}`);
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                switch (data.type) {
                    case 'progress':
                        callbacks.onProgress?.(data.percent, data.message);
                        break;
                    case 'terminal':
                        callbacks.onTerminal?.(data.line);
                        break;
                    case 'step':
                        callbacks.onStep?.(data.current, data.total, data.name);
                        break;
                    case 'complete':
                        callbacks.onComplete?.(data.success, data.result);
                        break;
                    case 'error':
                        callbacks.onError?.(data.message);
                        break;
                    default:
                        console.log(`[ScalerAPI] Unknown message type: ${data.type}`, data);
                }
            } catch (e) {
                console.error('[ScalerAPI] Failed to parse WebSocket message:', e);
            }
        };
        
        ws.onerror = (error) => {
            console.error(`[ScalerAPI] WebSocket error for job ${jobId}:`, error);
            callbacks.onError?.('WebSocket connection error');
        };
        
        ws.onclose = (event) => {
            console.log(`[ScalerAPI] WebSocket closed for job ${jobId}:`, event.code, event.reason);
            delete this._websockets[jobId];
            callbacks.onClose?.();
        };
        
        // Store reference
        this._websockets[jobId] = ws;
        
        return ws;
    },
    
    /**
     * Disconnect WebSocket for a specific job
     * @param {string} jobId - Job identifier
     */
    disconnectProgress(jobId) {
        const ws = this._websockets[jobId];
        if (ws) {
            ws.close();
            delete this._websockets[jobId];
        }
    },
    
    /**
     * Disconnect all active WebSocket connections
     */
    disconnectAll() {
        Object.keys(this._websockets).forEach(jobId => {
            this._websockets[jobId].close();
        });
        this._websockets = {};
    },
    
    // =========================================================================
    // HEALTH CHECK
    // =========================================================================
    
    /**
     * Check API server health
     * @returns {Promise<{status: string, service: string, version: string}>}
     */
    async checkHealth() {
        const response = await this._fetch(this._api('/api/health'));
        if (!response.ok) {
            throw new Error('API server is not healthy');
        }
        const data = await response.json();
        if (data?.scaler_bridge?.status === 'ok') {
            this._bridgeUp = true;
        }
        return data;
    },
    
    // =========================================================================
    // UTILITY METHODS
    // =========================================================================
    
    /**
     * Poll for operation status until complete
     * @param {string} jobId - Job identifier
     * @param {Object} callbacks - Progress callbacks
     * @param {number} [interval=1000] - Polling interval in ms
     * @returns {Promise<Object>} Final result
     */
    async pollUntilComplete(jobId, callbacks, interval = 1000) {
        return new Promise((resolve, reject) => {
            const poll = async () => {
                try {
                    const status = await this.getOperationStatus(jobId);
                    
                    if (status.progress !== undefined) {
                        callbacks.onProgress?.(status.progress, status.message);
                    }
                    
                    if (status.status === 'completed') {
                        callbacks.onComplete?.(true, status.result);
                        resolve(status);
                    } else if (status.status === 'failed' || status.status === 'error') {
                        callbacks.onError?.(status.error || 'Operation failed');
                        reject(new Error(status.error || 'Operation failed'));
                    } else {
                        // Still running, poll again
                        setTimeout(poll, interval);
                    }
                } catch (e) {
                    callbacks.onError?.(e.message);
                    reject(e);
                }
            };
            
            poll();
        });
    },

    // =========================================================================
    // IMAGE UPGRADE / JENKINS (/api/operations/image-upgrade/*)
    // =========================================================================

    async getBuildsForBranch(branch, opts = {}) {
        const resp = await this._fetch(this._api('/api/operations/image-upgrade/builds'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ branch, ...opts }),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to fetch builds (${resp.status})`);
        }
        return resp.json();
    },

    async resolveJenkinsUrl(url) {
        const resp = await this._fetch(this._api('/api/operations/image-upgrade/resolve-url'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to resolve URL (${resp.status})`);
        }
        return resp.json();
    },

    async getBuildStack(branch, buildNumber) {
        const resp = await this._fetch(this._api('/api/operations/image-upgrade/stack'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ branch, build_number: buildNumber }),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to get stack (${resp.status})`);
        }
        return resp.json();
    },

    async listBranches(type = 'dev') {
        const resp = await this._fetch(this._api('/api/operations/image-upgrade/branches'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type }),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to list branches (${resp.status})`);
        }
        return resp.json();
    },

    async getBranchSummaries(branches) {
        const resp = await this._fetch(this._api('/api/operations/image-upgrade/branch-summaries'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ branches }),
        });
        if (!resp.ok) return {};
        const data = await resp.json();
        return data.summaries || {};
    },

    async detectBranchSwitch(params) {
        const resp = await this._fetch(this._api('/api/operations/image-upgrade/branch-switch'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to detect branch switch (${resp.status})`);
        }
        return resp.json();
    },

    async checkVersionCompat(params) {
        const resp = await this._fetch(this._api('/api/operations/image-upgrade/compat'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to check version compat (${resp.status})`);
        }
        return resp.json();
    },

    async getUpgradePlan(params) {
        const resp = await this._fetch(this._api('/api/operations/image-upgrade/plan'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to get upgrade plan (${resp.status})`);
        }
        return resp.json();
    },

    async triggerUpgradeBuild(branch, opts = {}) {
        const resp = await this._fetch(this._api('/api/operations/image-upgrade/trigger-build'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                branch,
                with_baseos: opts.with_baseos !== false,
                qa_version: opts.qa_version || false,
                with_sanitizer: opts.with_sanitizer || false,
                auto_push: opts.auto_push || false,
                device_ids: opts.device_ids || [],
                ssh_hosts: opts.ssh_hosts || {},
                components: opts.components || ['DNOS', 'GI', 'BaseOS'],
            }),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to trigger build (${resp.status})`);
        }
        return resp.json();
    },

    async getUpgradeBuildStatus(jobId, latest = false) {
        const qs = latest ? '?latest=true' : '';
        const resp = await this._fetch(this._api(`/api/operations/image-upgrade/build-status/${encodeURIComponent(jobId)}${qs}`));
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to get build status (${resp.status})`);
        }
        return resp.json();
    },

    async getUpgradeBuildLog(branch, buildNumber) {
        const qs = buildNumber ? `?build_number=${buildNumber}` : '';
        const resp = await this._fetch(this._api(`/api/operations/image-upgrade/build-log/${encodeURIComponent(branch)}${qs}`));
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to get build log (${resp.status})`);
        }
        return resp.json();
    },

    async getUpgradeDeviceStatus(deviceIds, sshHosts = {}, cachedOnly = false) {
        const ids = Array.isArray(deviceIds) ? deviceIds.join(',') : String(deviceIds || '');
        const hosts = Array.isArray(deviceIds) ? deviceIds.map(id => sshHosts[id] || '').join(',') : '';
        const qs = new URLSearchParams({ device_ids: ids });
        if (hosts) qs.set('ssh_hosts', hosts);
        if (cachedOnly) qs.set('cached_only', 'true');
        const timeout = cachedOnly ? 5000 : 30000;
        const resp = await this._fetchWithTimeout(this._api(`/api/operations/image-upgrade/device-status?${qs}`), {}, timeout);
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to get device status (${resp.status})`);
        }
        return resp.json();
    },

    async upgradeFromUrls(body) {
        const resp = await this._fetch(this._api('/api/operations/image-upgrade/from-urls'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to upgrade from URLs (${resp.status})`);
        }
        return resp.json();
    },

    async getUpgradeRecentSources() {
        const resp = await this._fetch(this._api('/api/operations/image-upgrade/recent-sources'));
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to get recent sources (${resp.status})`);
        }
        return resp.json();
    },

    async verifyUpgradeStacks(deviceIds, sshHosts = {}) {
        const resp = await this._fetch(this._api('/api/operations/image-upgrade/verify-stacks'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_ids: deviceIds, ssh_hosts: sshHosts }),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to verify stacks (${resp.status})`);
        }
        return resp.json();
    },

    async restoreUpgradeConfig(deviceIds, sshHosts = {}) {
        const resp = await this._fetch(this._api('/api/operations/image-upgrade/restore-config'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_ids: deviceIds, ssh_hosts: sshHosts }),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to restore config (${resp.status})`);
        }
        return resp.json();
    },

    async waitAndUpgrade(params) {
        const resp = await this._fetch(this._api('/api/operations/image-upgrade/wait-and-upgrade'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to start wait-and-upgrade (${resp.status})`);
        }
        return resp.json();
    },

    /**
     * Stuck-upgrade recovery API.
     *
     * `getStuckDevices` lists devices where the bridge crashed mid-upgrade
     * and the orphan scanner couldn't auto-resume (because the deploy
     * URLs / system_type / ncc_id weren't persisted before the crash).
     *
     * `resumeStuckDevices` re-triggers the orphan-in-GI recovery for one
     * or more of those devices. Optionally accepts `imageUrls` and
     * `deployOverrides` so the operator can supply whatever was missing.
     *
     * `clearStuckDevices` just removes the manual_intervention flag
     * (useful when the operator finished the upgrade out-of-band).
     */
    async getStuckDevices() {
        const resp = await this._fetch(this._api('/api/operations/image-upgrade/stuck-devices'));
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to fetch stuck devices (${resp.status})`);
        }
        return resp.json();
    },

    async resumeStuckDevices(deviceIds, imageUrls = {}, deployOverrides = {}) {
        const resp = await this._fetch(this._api('/api/operations/image-upgrade/resume-stuck'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_ids: deviceIds,
                image_urls: imageUrls,
                deploy_overrides: deployOverrides,
            }),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to resume stuck devices (${resp.status})`);
        }
        return resp.json();
    },

    async clearStuckDevices(deviceIds) {
        const resp = await this._fetch(this._api('/api/operations/image-upgrade/clear-stuck'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_ids: deviceIds }),
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to clear stuck devices (${resp.status})`);
        }
        return resp.json();
    },
};

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ScalerAPI;
}

console.log('[ScalerAPI] Loaded - API client ready');

