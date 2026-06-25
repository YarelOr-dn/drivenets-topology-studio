/**
 * topology-device-state.js -- Device-state orchestrator
 *
 * Single source of truth for per-device polling/caching. All consumers
 * (DeviceMonitor, Upgrade wizard, Stack / LLDP / SSH dialogs, Device
 * Manager, toolbar) SHOULD route their `getDeviceContext` / device-
 * status / stack-live calls through this module instead of hitting
 * `ScalerAPI` directly. The module provides:
 *
 *   * Single-flight dedup keyed by `(scope, deviceId, variant)`. When
 *     three dialogs ask for PE-1's context at the same time, exactly
 *     one backend request is issued; all three callers await the same
 *     Promise.
 *   * TTL cache (default 30s for non-live, 90s ceiling for live) --
 *     matches the server's `LiveCoalescer` TTL so the two layers agree.
 *   * Per-scope namespacing: `scope = "<topology_composite_id>|<user>"`
 *     so that two topologies that both have a device labelled "PE-1"
 *     never share cache, and two users on the same machine never see
 *     each other's cached contexts.
 *   * AbortController per in-flight fetch; `invalidateScope()` or
 *     `abortAll()` cancels everything when the user switches topology
 *     or logs out, so a slow response can't land on the wrong canvas
 *     object.
 *   * Per-device circuit breaker: after N consecutive failures the
 *     module refuses to launch fresh fetches for that device until the
 *     cooldown expires, but still returns the last successful cached
 *     value to consumers.
 *   * Pub/sub: `window.dispatchEvent('device-state:updated', ...)` so
 *     UI pieces can re-render without starting their own poll loop.
 *
 * Design notes:
 *   - Cache entries carry `fetchedAt` + `scope` + `variant`. We NEVER
 *     mutate a cached object in place -- consumers get a shallow copy.
 *   - The orchestrator never writes directly to canvas device objects.
 *     DeviceMonitor remains the component that applies updates to the
 *     canvas; we just feed it a deduped context.
 *   - When scope changes (user loads a different topology or logs out)
 *     every in-flight request is aborted AND every cache entry from
 *     the old scope is dropped. This is the bug where wizard results
 *     from topology A would silently land in topology B's canvas.
 *
 * User reports addressed (2026-04-24):
 *   * "device polling and information should be scalable and consistent
 *      per device per topology per user"
 *   * PE-1 briefly showing stale `sys-type?` or empty stack after
 *     switching topology because in-flight fetches from the previous
 *     topology landed on the new canvas object.
 *   * Multiple wizards + monitor + dialog each SSHing the same device
 *     at once; now exactly one SSH per TTL window.
 */

'use strict';

(function (W) {
    if (W.DeviceState) return;

    const DEFAULTS = {
        NON_LIVE_TTL_MS: 30 * 1000,
        LIVE_TTL_MS: 90 * 1000,
        STATUS_TTL_MS: 30 * 1000,
        INFLIGHT_GRACE_MS: 45 * 1000,
        CIRCUIT_THRESHOLD: 4,
        CIRCUIT_MIN_MS: 30 * 1000,
        CIRCUIT_MAX_MS: 15 * 60 * 1000,
    };

    const ORCH = {
        _cache: new Map(),
        _inflight: new Map(),
        _abortControllers: new Map(),
        _circuit: new Map(),
        _lastScopeKey: '',
        _debug: false,
        _init: false,

        init() {
            if (this._init) return;
            this._init = true;
            // Seed `_lastScopeKey` with whatever scope we can resolve at
            // init (usually `local:anon|default` before login/topology
            // load). This makes the first real scope transition trigger
            // `abortScope`, which drops bootstrap cache entries keyed
            // under the anon scope. Without it those entries would only
            // age out on TTL.
            this._lastScopeKey = this.getScope();
            W.addEventListener('topology:loaded', () => this._onScopeChange('topology:loaded'));
            W.addEventListener('topology:unloaded', () => this.abortScope(undefined, 'topology:unloaded'));
            // `topology:active-changed` is the authoritative scope-flip
            // event: TopologySync fires it the moment `_active` moves to
            // the new topology's composite ID. `topology:loaded` fires
            // earlier (during `loadTopologyFromData`, before `setActive`
            // runs), so relying on loaded alone would miss the real
            // scope transition and leave new-canvas requests keyed
            // under the OLD scope for a ~100ms window.
            W.addEventListener('topology:active-changed', () => this._onScopeChange('topology:active-changed'));
            W.addEventListener('topology:auth-logout', () => this.abortAll('topology:auth-logout'));
            W.addEventListener('topology:auth-login', () => this._onScopeChange('topology:auth-login'));
            W.addEventListener('auth:logout', () => this.abortAll('auth:logout'));
            W.addEventListener('auth:login', () => this._onScopeChange('auth:login'));

            // Device lifecycle invalidation: any event that changes the
            // device's operational state should wipe the cached context
            // so the next consumer gets fresh data instead of waiting
            // for the 30-90s TTL to expire. Wizard UI reacts in <1s
            // after these events; the cache needs to keep up.
            const _invalidateFromEvent = (e, reason) => {
                const detail = e && e.detail ? e.detail : {};
                const ids = []
                    .concat(detail.deviceId ? [detail.deviceId] : [])
                    .concat(detail.devices || [])
                    .concat(detail.allDevices || [])
                    .concat(detail.completedDevices || [])
                    .filter(Boolean);
                const uniq = Array.from(new Set(ids));
                for (const did of uniq) {
                    try { this.invalidateDevice(did); } catch (_) {}
                }
                if (this._debug && uniq.length) {
                    console.debug('[DeviceState] invalidated', uniq.length, 'device(s) on', reason);
                }
            };
            W.addEventListener('device:upgrade-started', (e) => _invalidateFromEvent(e, 'device:upgrade-started'));
            W.addEventListener('device:upgrade-complete', (e) => _invalidateFromEvent(e, 'device:upgrade-complete'));
            W.addEventListener('device:upgrade-cancelled', (e) => _invalidateFromEvent(e, 'device:upgrade-cancelled'));
            W.addEventListener('device:config-pushed', (e) => _invalidateFromEvent(e, 'device:config-pushed'));
            W.addEventListener('device:mode-changed', (e) => _invalidateFromEvent(e, 'device:mode-changed'));
            W.addEventListener('device:identity-mismatch', (e) => _invalidateFromEvent(e, 'device:identity-mismatch'));
            if (this._debug) console.debug('[DeviceState] initialized, scope=', this._lastScopeKey);
        },

        _getUser() {
            try {
                if (W.TopologyAuth) {
                    if (typeof W.TopologyAuth.getUsername === 'function') {
                        const u = W.TopologyAuth.getUsername();
                        if (u) return String(u).trim();
                    }
                    if (typeof W.TopologyAuth.getUser === 'function') {
                        const u = W.TopologyAuth.getUser();
                        if (u && typeof u === 'object' && u.username) return String(u.username).trim();
                        if (typeof u === 'string' && u) return u.trim();
                    }
                }
            } catch (_) {}
            return 'default';
        },

        _getTopologyKey() {
            try {
                if (W.TopologySync && typeof W.TopologySync.getActive === 'function') {
                    const a = W.TopologySync.getActive();
                    if (a && a.topology_id) {
                        const owner = a.owner || 'local';
                        const domain = a.domain_id || 'default';
                        return `${owner}:${domain}:${a.topology_id}`;
                    }
                }
            } catch (_) {}
            try {
                const ed = W.topologyEditor;
                if (ed?.metadata?.topology_id) return `local:default:${ed.metadata.topology_id}`;
                if (ed?._loadedFileName) return `local:file:${ed._loadedFileName}`;
            } catch (_) {}
            return 'local:anon';
        },

        getScope() {
            const user = this._getUser();
            const topo = this._getTopologyKey();
            return `${topo}|${user}`;
        },

        _onScopeChange(reason) {
            const prev = this._lastScopeKey;
            const now = this.getScope();
            if (prev && prev !== now) {
                if (this._debug) console.debug('[DeviceState] scope changed', prev, '->', now, '(', reason, ')');
                this.abortScope(prev, reason);
            }
            this._lastScopeKey = now;
        },

        _cacheKey(scope, deviceId, variant) {
            return `${scope}|${deviceId}|${variant}`;
        },

        _ttlFor(variant, live) {
            if (variant === 'status') return DEFAULTS.STATUS_TTL_MS;
            if (live) return DEFAULTS.LIVE_TTL_MS;
            return DEFAULTS.NON_LIVE_TTL_MS;
        },

        _deviceKey(scope, deviceId) {
            return `${scope}|${deviceId}`;
        },

        _circuitOpen(scope, deviceId) {
            const st = this._circuit.get(this._deviceKey(scope, deviceId));
            return !!(st && st.openUntil > Date.now());
        },

        _markFailure(scope, deviceId) {
            const key = this._deviceKey(scope, deviceId);
            const st = this._circuit.get(key) || { fails: 0, backoffMs: 0, openUntil: 0 };
            st.fails = (st.fails || 0) + 1;
            if (st.fails >= DEFAULTS.CIRCUIT_THRESHOLD) {
                const next = Math.min(
                    Math.max((st.backoffMs || 0) * 2, DEFAULTS.CIRCUIT_MIN_MS),
                    DEFAULTS.CIRCUIT_MAX_MS
                );
                st.backoffMs = next;
                st.openUntil = Date.now() + next;
                if (this._debug) {
                    console.warn('[DeviceState] circuit OPEN for', deviceId,
                        'for', Math.round(next / 1000), 's (', st.fails, 'consecutive failures)');
                }
            }
            this._circuit.set(key, st);
        },

        _markSuccess(scope, deviceId) {
            const key = this._deviceKey(scope, deviceId);
            const st = this._circuit.get(key);
            if (st && (st.fails || st.backoffMs || st.openUntil)) {
                st.fails = 0;
                st.backoffMs = 0;
                st.openUntil = 0;
                this._circuit.set(key, st);
            }
        },

        /**
         * Get per-device context with single-flight dedup + TTL cache.
         *
         * @param {string} deviceId -- canvas label (authoritative)
         * @param {object} opts
         *   - sshHost: SSH host / mgmt IP
         *   - live: if true, force a fresh fetch past the TTL
         *   - maxAgeMs: override the default TTL for cache reuse
         *   - bypassCache: if true, always fetch (still deduped)
         * @returns {Promise<object>} resolved context
         */
        async getContext(deviceId, opts) {
            const options = opts || {};
            const live = !!options.live;
            const sshHost = options.sshHost || '';
            const scope = this.getScope();
            const variant = live ? 'context-live' : 'context';
            const ttl = Number.isFinite(options.maxAgeMs) ? options.maxAgeMs : this._ttlFor('context', live);
            const cacheKey = this._cacheKey(scope, deviceId, variant);

            if (!options.bypassCache) {
                const cached = this._cache.get(cacheKey);
                if (cached && (Date.now() - cached.fetchedAt) < ttl) {
                    if (this._debug) console.debug('[DeviceState] cache HIT', deviceId, variant);
                    return cached.value;
                }
                // Non-live caller benefits from a fresher live entry --
                // e.g. post-upgrade refresh just populated `context-live`
                // 5s ago, a wizard asking for non-live should NOT get
                // a 25s-old `context` entry. Prefer the fresher live
                // result when the gap is non-trivial.
                if (!live) {
                    const liveKey = this._cacheKey(scope, deviceId, 'context-live');
                    const liveCached = this._cache.get(liveKey);
                    if (liveCached) {
                        const liveAge = Date.now() - liveCached.fetchedAt;
                        const nonLiveAge = cached ? (Date.now() - cached.fetchedAt) : Infinity;
                        if (liveAge < DEFAULTS.LIVE_TTL_MS && liveAge < nonLiveAge) {
                            if (this._debug) console.debug('[DeviceState] prefer fresher live entry for', deviceId);
                            return liveCached.value;
                        }
                    }
                }
            }

            const inflight = this._inflight.get(cacheKey);
            if (inflight) {
                if (this._debug) console.debug('[DeviceState] dedup HIT', deviceId, variant);
                return inflight.promise;
            }

            if (this._circuitOpen(scope, deviceId) && !options.force) {
                const cached = this._cache.get(cacheKey);
                if (cached) return cached.value;
                const cachedNonLive = this._cache.get(this._cacheKey(scope, deviceId, 'context'));
                if (cachedNonLive) return cachedNonLive.value;
                const err = new Error(`circuit open for ${deviceId}`);
                err.code = 'DEVICE_STATE_CIRCUIT_OPEN';
                throw err;
            }

            const abortCtl = typeof AbortController !== 'undefined' ? new AbortController() : null;
            const recordScope = scope;
            const promise = (async () => {
                try {
                    if (typeof ScalerAPI === 'undefined' || !ScalerAPI.getDeviceContext) {
                        throw new Error('ScalerAPI.getDeviceContext not available');
                    }
                    const fetchOpts = abortCtl ? { signal: abortCtl.signal } : {};
                    const ctx = await ScalerAPI.getDeviceContext(deviceId, live, sshHost, fetchOpts);
                    if (this.getScope() !== recordScope) {
                        const staleErr = new Error('scope changed during fetch');
                        staleErr.code = 'DEVICE_STATE_SCOPE_STALE';
                        throw staleErr;
                    }
                    this._cache.set(cacheKey, {
                        value: ctx,
                        fetchedAt: Date.now(),
                        scope: recordScope,
                        variant,
                    });
                    this._markSuccess(recordScope, deviceId);
                    try {
                        W.dispatchEvent(new CustomEvent('device-state:updated', {
                            detail: { deviceId, scope: recordScope, variant, context: ctx },
                        }));
                    } catch (_) {}
                    return ctx;
                } catch (err) {
                    // Aborts are user-initiated (topology switch,
                    // logout, explicit abortScope) -- they are NOT a
                    // device health signal. Same for deliberate
                    // scope-stale drops. Only real device / network
                    // failures should tick the circuit breaker.
                    const isAbort = err && (err.name === 'AbortError' || err.code === 'DEVICE_STATE_SCOPE_STALE' || err.code === 20);
                    if (!isAbort) {
                        this._markFailure(recordScope, deviceId);
                    }
                    throw err;
                } finally {
                    this._inflight.delete(cacheKey);
                    this._abortControllers.delete(cacheKey);
                }
            })();
            this._inflight.set(cacheKey, { promise, scope: recordScope, deviceId, startedAt: Date.now() });
            if (abortCtl) this._abortControllers.set(cacheKey, abortCtl);
            return promise;
        },

        /**
         * Get cached context without issuing any network request.
         * Returns null if no fresh entry is available for the CURRENT scope.
         */
        peekContext(deviceId, opts) {
            const options = opts || {};
            const scope = this.getScope();
            const variants = options.live ? ['context-live', 'context'] : ['context', 'context-live'];
            const now = Date.now();
            for (const variant of variants) {
                const cached = this._cache.get(this._cacheKey(scope, deviceId, variant));
                if (!cached) continue;
                const ttl = Number.isFinite(options.maxAgeMs) ? options.maxAgeMs : this._ttlFor('context', variant === 'context-live');
                if ((now - cached.fetchedAt) < ttl) return cached.value;
            }
            return null;
        },

        /**
         * Invalidate cache for a single device (current scope). Called
         * after a wizard push, after `request system delete`, after a
         * fresh SSH probe, etc. -- basically whenever the consumer has
         * reason to believe the cached snapshot is stale.
         */
        invalidateDevice(deviceId, opts) {
            const options = opts || {};
            const scopes = options.allScopes ? Array.from(new Set(Array.from(this._cache.keys()).map(k => k.split('|').slice(0, 2).join('|')))) : [this.getScope()];
            for (const scope of scopes) {
                for (const variant of ['context', 'context-live', 'status']) {
                    this._cache.delete(this._cacheKey(scope, deviceId, variant));
                }
            }
        },

        /**
         * Abort every in-flight request for `scope` (defaults to current
         * scope if omitted). Used on topology switch so a slow SSH does
         * not write back to a canvas object that has since been swapped.
         */
        abortScope(scope, reason) {
            const target = scope || this.getScope();
            let aborted = 0;
            for (const [key, ctl] of this._abortControllers.entries()) {
                if (key.startsWith(target + '|')) {
                    try { ctl.abort(reason || 'scope-abort'); } catch (_) {}
                    this._abortControllers.delete(key);
                    aborted++;
                }
            }
            for (const [key, _value] of this._cache.entries()) {
                if (key.startsWith(target + '|')) this._cache.delete(key);
            }
            for (const [key, _value] of this._inflight.entries()) {
                if (key.startsWith(target + '|')) this._inflight.delete(key);
            }
            if (this._debug && aborted) {
                console.debug('[DeviceState] abortScope', target, 'aborted', aborted, 'requests');
            }
        },

        abortAll(reason) {
            let aborted = 0;
            for (const [key, ctl] of this._abortControllers.entries()) {
                try { ctl.abort(reason || 'abort-all'); } catch (_) {}
                this._abortControllers.delete(key);
                aborted++;
            }
            this._cache.clear();
            this._inflight.clear();
            this._circuit.clear();
            if (this._debug) console.debug('[DeviceState] abortAll cleared', aborted, 'in-flight');
        },

        /**
         * Observability snapshot.
         */
        stats() {
            const now = Date.now();
            const circuitOpen = [];
            for (const [key, st] of this._circuit.entries()) {
                if (st.openUntil > now) {
                    circuitOpen.push({
                        device: key.split('|').slice(-1)[0],
                        remainingMs: st.openUntil - now,
                        fails: st.fails,
                    });
                }
            }
            return {
                scope: this.getScope(),
                cacheEntries: this._cache.size,
                inflight: this._inflight.size,
                circuitOpen,
            };
        },
    };

    W.DeviceState = ORCH;

    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => ORCH.init());
        } else {
            ORCH.init();
        }
    }
})(typeof window !== 'undefined' ? window : globalThis);
