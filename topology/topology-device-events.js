/**
 * topology-device-events.js -- Per-user device-maintenance event bus (client side).
 *
 * Connects to the scaler bridge WebSocket at /api/events/ws with the user's
 * JWT and re-broadcasts incoming events as window-level CustomEvents so any
 * module can subscribe without coupling to the WebSocket wire format.
 *
 * This is distinct from `topology-events.js` (the in-app `TopologyEventBus`
 * class for local module-to-module pub/sub). This file owns *device state*
 * events that cross user / tab boundaries -- ghost-IP reaps, maintenance
 * notes, cluster state changes, etc.
 *
 * Contract
 * --------
 * Incoming WS frames come in two shapes:
 *
 *   { type: "hello",   username, watched: [device_id, ...] }
 *   { type: "pong" }
 *   { type: "__ping__" }
 *   { type: "event", event: { type, device_id, payload: {...} } }
 *
 * For every "event" frame we dispatch a CustomEvent:
 *
 *   window.dispatchEvent(new CustomEvent("topology:event", { detail: {...} }))
 *   window.dispatchEvent(new CustomEvent(`topology:event:${event.type}`, { detail: {...} }))
 *
 * Existing listeners (e.g. the SSH dialog's "ssh:ghost-ip-detected" handler)
 * are mirrored onto these channels so code that was already listening
 * locally also receives cross-user broadcasts -- the payload shape matches.
 *
 * Watcher registration
 * --------------------
 * window.TopologyDeviceEvents.setWatchedDevices(['PE-1','PE-4'], { topologyId })
 * registers every canvas device as a watcher for the current user. Call
 * this whenever the canvas device set changes. A 30s heartbeat is set up
 * automatically so rows stay fresh.
 *
 * Lifecycle
 * ---------
 * - Call TopologyDeviceEvents.start() once after login (auto-wired via
 *   the `topology:auth-login` event).
 * - Call TopologyDeviceEvents.stop() on logout so the WS doesn't leak.
 * - The module reconnects with exponential backoff (capped at 30s).
 */
(function () {
    'use strict';

    const LOG_PREFIX = '[DeviceEvents]';
    const HEARTBEAT_INTERVAL_MS = 30 * 1000;
    const WATCHER_DEBOUNCE_MS = 500;
    const BACKOFF_MIN_MS = 1500;
    const BACKOFF_MAX_MS = 30 * 1000;
    // Cap consecutive reconnect failures before we stop trying. On remote-
    // access deployments where the WS proxy isn't available (e.g. talking
    // to an older serve.py that still expects direct :8766), we used to
    // spam devtools with a reconnect attempt every 1-30s forever. After
    // this many back-to-back failures we log once and go quiet; the next
    // successful open resets the counter.
    const MAX_CONSECUTIVE_FAILURES = 5;
    // Burst-quiet pre-flight (2026-04-24w)
    // ------------------------------------
    // The browser unconditionally logs
    //   "WebSocket connection to 'ws://.../api/events/ws?token=...' failed:"
    // whenever new WebSocket() fails during the handshake -- we cannot
    // suppress that line from JS. During a `uvicorn --reload` cycle on
    // scaler_bridge.py that log fires 1-2 times per save which is pure
    // devtools noise. To avoid it we do a cheap HTTP probe to a known
    // bridge route BEFORE attempting the WS handshake. A fetch() to a
    // 502 / 404 response does NOT log to the console (only true network
    // errors do), and serve.py always proxies so we never see a raw TCP
    // refused even when the bridge is down.
    //
    // Flow:
    //   scheduleReconnect -> wait backoff -> pre-flight probe
    //     pre-flight OK  -> new WebSocket(...) (normal path)
    //     pre-flight KO  -> schedule NEXT reconnect without ever touching WS
    //
    // Result: the "failed:" devtools line only appears for genuinely
    // lost connections (bridge crashed mid-session, network partition)
    // not for routine reload cycles.
    const PREFLIGHT_URL = '/api/events/status';
    const PREFLIGHT_TIMEOUT_MS = 2000;
    // Only activate pre-flight starting at the 2nd attempt. The very
    // first connect after page load hits the WS directly (fast path) --
    // we already know the page itself just loaded from serve.py so the
    // bridge is overwhelmingly likely to be up. Pre-flight kicks in
    // only after a failure, which is exactly the "probably reloading"
    // window we want to filter.
    const PREFLIGHT_AFTER_FAILURES = 1;

    let _ws = null;
    let _started = false;
    let _backoffMs = BACKOFF_MIN_MS;
    let _reconnectTimer = null;
    let _heartbeatTimer = null;
    let _deviceSet = new Set();
    let _pendingWatcherFlush = null;
    let _topologyId = null;
    let _lastHello = null;
    let _consecutiveFailures = 0;
    let _disabledReason = null;
    // When true, the next _connect() should do a pre-flight HTTP probe
    // before attempting the WS handshake. Flipped on by every failure
    // and flipped off by a successful onopen.
    let _needPreflight = false;

    function _log() {
        if (!window.__DEBUG_DEVICE_EVENTS__) return;
        const args = Array.from(arguments);
        args.unshift(LOG_PREFIX);
        console.debug.apply(console, args);
    }

    function _currentUsername() {
        try {
            if (window.TopologyAuth && typeof window.TopologyAuth.getCurrentUser === 'function') {
                const u = window.TopologyAuth.getCurrentUser();
                return u && u.username ? u.username : '';
            }
        } catch (_) { /* swallow */ }
        return '';
    }

    function _currentToken() {
        try {
            if (window.TopologyAuth && typeof window.TopologyAuth.getToken === 'function') {
                return window.TopologyAuth.getToken() || '';
            }
        } catch (_) { /* swallow */ }
        return '';
    }

    function _buildWsUrl() {
        // Prefer ScalerAPI.getBridgeWebSocketOrigin() (same-origin aware,
        // returns ws://<page-host>:<page-port> so serve.py's WS proxy is
        // used on both localhost and CGNAT remote-access deployments).
        // Fall back to the same same-origin shape if ScalerAPI isn't
        // loaded yet -- NOT to the legacy hardcoded :8766, which would
        // fail on remote access where that port is firewalled off.
        let origin;
        if (typeof ScalerAPI !== 'undefined' && typeof ScalerAPI.getBridgeWebSocketOrigin === 'function') {
            origin = ScalerAPI.getBridgeWebSocketOrigin();
        } else {
            const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            origin = `${proto}//${window.location.host}`;
        }
        const params = new URLSearchParams();
        const tok = _currentToken();
        if (tok) params.set('token', tok);
        return `${origin}/api/events/ws?${params.toString()}`;
    }

    function _dispatchEvent(envelope) {
        try {
            window.dispatchEvent(new CustomEvent('topology:event', { detail: envelope }));
            const t = (envelope && envelope.type) || '';
            if (t) {
                window.dispatchEvent(new CustomEvent(`topology:event:${t}`, { detail: envelope }));
            }
            // Back-compat bridge: legacy code listens for 'ssh:ghost-ip-detected'
            // on a per-device basis. Forward matching events so we don't have
            // to refactor every listener in one go. Use the field names the
            // existing topology-ssh-dialog.js handler expects (ip, actual,
            // expected) and include richer names as well so new code can
            // pick the shape that makes sense.
            if (t === 'ghost_ip_reaped') {
                const p = envelope.payload || {};
                const legacy = {
                    deviceId: envelope.device_id || '',
                    ip: p.cleared_ip || '',
                    ghostIp: p.cleared_ip || '',
                    actual: p.actual_hostname || '',
                    actualHostname: p.actual_hostname || '',
                    expected: envelope.device_id || '',
                    reason: p.reason || '',
                    actorUser: p.actor_user || '',
                    source: 'broadcast',
                };
                window.dispatchEvent(new CustomEvent('ssh:ghost-ip-detected', { detail: legacy }));
            }
        } catch (err) {
            console.warn(LOG_PREFIX, 'dispatchEvent failed', err);
        }
    }

    // Cheap HTTP probe that resolves to true iff the bridge's events
    // route is reachable. We accept any 2xx/3xx/4xx as "up" (even 401
    // means the route responded -- the token is just unknown, which is
    // a logical problem not a transport problem). Only 5xx from
    // serve.py's proxy OR a raw network error means "bridge is down".
    // fetch() promises for non-2xx HTTP do NOT log to the console, so
    // this is silent by design.
    async function _preflightOk() {
        try {
            const ctl = (typeof AbortController !== 'undefined') ? new AbortController() : null;
            const timer = ctl ? setTimeout(() => ctl.abort(), PREFLIGHT_TIMEOUT_MS) : null;
            const tok = _currentToken();
            const headers = tok ? { 'Authorization': 'Bearer ' + tok } : {};
            const resp = await fetch(PREFLIGHT_URL, {
                method: 'GET',
                headers,
                signal: ctl ? ctl.signal : undefined,
                cache: 'no-store',
            });
            if (timer) clearTimeout(timer);
            // 5xx from serve.py's proxy almost always means the bridge
            // is mid-reload. Any other response -- 200, 401, 403, 404 --
            // indicates the bridge is answering, so the WS handshake
            // should go through.
            return resp.status < 500;
        } catch (err) {
            // AbortError / network error -- assume bridge is still down.
            _log('preflight failed', err && err.name || err);
            return false;
        }
    }

    async function _connect() {
        if (!_started) return;
        if (_disabledReason) return;  // soft-disabled after repeated failures
        const tok = _currentToken();
        if (!tok) {
            _log('no token; skipping connect');
            return;
        }

        // Pre-flight HTTP probe gate: if we've already seen a failure
        // this session, do a cheap HTTP round-trip first. Skipping the
        // WS handshake on a bad probe is the main mechanism that keeps
        // "WebSocket connection to ... failed" out of devtools during
        // bridge reloads.
        if (_needPreflight && _consecutiveFailures >= PREFLIGHT_AFTER_FAILURES) {
            const ok = await _preflightOk();
            if (!_started || _disabledReason) return;  // stopped / tripped while awaiting
            if (!ok) {
                _log('preflight NOT ok; deferring WS handshake');
                _recordFailureAndMaybeDisable('preflight');
                if (!_disabledReason) _scheduleReconnect();
                return;
            }
        }

        const url = _buildWsUrl();
        _log('connecting', url.replace(/token=[^&]+/, 'token=<redacted>'));
        try {
            _ws = new WebSocket(url);
        } catch (err) {
            _log('WS construct failed', err);
            _needPreflight = true;
            _recordFailureAndMaybeDisable('construct');
            if (!_disabledReason) _scheduleReconnect();
            return;
        }
        // `openSeen` lets onclose differentiate "failed to connect" from
        // "was open, then closed". A failed-to-connect counts toward the
        // consecutive-failure cap; a clean close after OPEN does not.
        let openSeen = false;
        _ws.onopen = function () {
            _log('WS open');
            openSeen = true;
            _backoffMs = BACKOFF_MIN_MS;
            _consecutiveFailures = 0;
            _disabledReason = null;
            _needPreflight = false;  // healthy again -- fast path next time
            _sendHeartbeat();
        };
        _ws.onmessage = function (ev) {
            let frame;
            try {
                frame = JSON.parse(ev.data);
            } catch (parseErr) {
                console.warn(LOG_PREFIX, 'bad WS frame', parseErr, ev.data);
                return;
            }
            const t = frame && frame.type;
            if (t === 'hello') {
                _lastHello = frame;
                _log('hello', frame);
                return;
            }
            if (t === '__ping__') {
                try {
                    _ws.send(JSON.stringify({ type: 'pong' }));
                } catch (err) {
                    _log('pong send failed', err);
                }
                return;
            }
            if (t === 'pong') {
                return;
            }
            if (t === 'event' && frame.event) {
                _dispatchEvent(frame.event);
                return;
            }
            _log('unknown frame', frame);
        };
        _ws.onclose = function (ev) {
            _log('WS close', ev.code, ev.reason);
            _ws = null;
            // Close before OPEN = handshake / network failure. 1006 means
            // "abnormal closure" (connection refused, firewall drop, TLS
            // reset), which is what remote-access users see when port
            // 8766 is blocked and the serve.py WS proxy isn't available.
            if (!openSeen) {
                _needPreflight = true;  // gate future attempts through HTTP
                _recordFailureAndMaybeDisable('close-' + ev.code);
            } else {
                // Post-open close. Could be a clean server-initiated
                // close (idle timeout, restart) or a network drop. Use
                // pre-flight for the next connect so a bridge reload
                // doesn't produce a second "failed:" log in devtools.
                _needPreflight = true;
            }
            if (_started && !_disabledReason) _scheduleReconnect();
        };
        _ws.onerror = function (ev) {
            _log('WS error', ev);
        };
    }

    function _recordFailureAndMaybeDisable(origin) {
        _consecutiveFailures += 1;
        if (_consecutiveFailures < MAX_CONSECUTIVE_FAILURES) return;
        _disabledReason = origin || 'max-retries';
        // One informational log so devtools is quiet afterwards. This
        // does not throw -- real-time device events just stop arriving
        // until the page is reloaded (or .resume() is called).
        console.info(
            LOG_PREFIX,
            `disabling reconnect after ${_consecutiveFailures} consecutive failures (${_disabledReason}); ` +
            `device-event broadcasts are paused. Reload the page once the server is reachable.`
        );
        // Clear any pending reconnect so we truly stop.
        if (_reconnectTimer) {
            clearTimeout(_reconnectTimer);
            _reconnectTimer = null;
        }
    }

    function _scheduleReconnect() {
        if (_reconnectTimer) return;
        if (_disabledReason) return;
        // Defer reconnect during an announced graceful restart. The WS
        // proxy sits behind the same port as serve.py, so a connect
        // attempt while the restart is in progress is guaranteed to log
        // a "WebSocket connection ... failed:" line in DevTools. Wait
        // until the announced window expires, then resume normal
        // backoff.
        if (window.GracefulRestart && window.GracefulRestart.isInWindow()) {
            const remainMs = Math.max(1000, (window.GracefulRestart.secondsRemaining() + 1) * 1000);
            _log(`graceful restart in progress, deferring reconnect ${remainMs}ms`);
            _reconnectTimer = setTimeout(function () {
                _reconnectTimer = null;
                _scheduleReconnect();
            }, remainMs);
            return;
        }
        const delay = _backoffMs;
        _backoffMs = Math.min(BACKOFF_MAX_MS, Math.round(_backoffMs * 1.7));
        _log(`reconnect in ${delay}ms (next backoff ${_backoffMs}ms)`);
        _reconnectTimer = setTimeout(function () {
            _reconnectTimer = null;
            // _connect is async now (pre-flight probe); the promise is
            // self-contained and internal failures loop back through
            // _scheduleReconnect, so we just ignore the return here.
            const p = _connect();
            if (p && typeof p.catch === 'function') {
                p.catch(function (err) { _log('connect error', err); });
            }
        }, delay);
    }

    function _sendHeartbeat() {
        if (!_ws || _ws.readyState !== WebSocket.OPEN) return;
        const ids = Array.from(_deviceSet);
        try {
            _ws.send(JSON.stringify({ type: 'heartbeat', device_ids: ids }));
        } catch (err) {
            _log('heartbeat send failed', err);
        }
    }

    function _startHeartbeatTimer() {
        if (_heartbeatTimer) return;
        _heartbeatTimer = setInterval(_sendHeartbeat, HEARTBEAT_INTERVAL_MS);
    }

    function _stopHeartbeatTimer() {
        if (!_heartbeatTimer) return;
        clearInterval(_heartbeatTimer);
        _heartbeatTimer = null;
    }

    // -- Public watcher management --------------------------------------
    //
    // We debounce the HTTP call so rapid-fire canvas mutations (drag-drop,
    // delete, undo) don't produce a thundering herd of /watch-heartbeat
    // requests. The WebSocket heartbeat path is still live -- this HTTP
    // path is the belt-and-braces fallback for when the WS is offline.

    function _flushWatchersNow() {
        _pendingWatcherFlush = null;
        const ids = Array.from(_deviceSet);
        const tok = _currentToken();
        if (!tok) return;
        fetch('/api/devices/watch-heartbeat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + tok,
            },
            body: JSON.stringify({ device_ids: ids }),
        }).catch(function (err) {
            _log('watcher HTTP heartbeat failed', err);
        });
        _sendHeartbeat();
    }

    let _firstWatcherFlushDone = false;

    function setWatchedDevices(deviceIds, opts) {
        const clean = (deviceIds || [])
            .map(function (d) { return (d == null ? '' : String(d)).trim(); })
            .filter(Boolean);
        _deviceSet = new Set(clean);
        if (opts && opts.topologyId) _topologyId = opts.topologyId;
        if (_pendingWatcherFlush) clearTimeout(_pendingWatcherFlush);

        // First non-empty flush goes out synchronously so the user can
        // click SSH immediately after a topology load without tripping
        // the watcher-only permission check on /api/ssh/clear-ghost-ip.
        // Subsequent flushes stay debounced.
        if (!_firstWatcherFlushDone && clean.length > 0) {
            _firstWatcherFlushDone = true;
            _flushWatchersNow();
        } else {
            _pendingWatcherFlush = setTimeout(_flushWatchersNow, WATCHER_DEBOUNCE_MS);
        }
    }

    function addWatchedDevice(deviceId) {
        const clean = (deviceId == null ? '' : String(deviceId)).trim();
        if (!clean || _deviceSet.has(clean)) return;
        _deviceSet.add(clean);
        if (_pendingWatcherFlush) clearTimeout(_pendingWatcherFlush);
        _pendingWatcherFlush = setTimeout(_flushWatchersNow, WATCHER_DEBOUNCE_MS);
    }

    function removeWatchedDevice(deviceId) {
        const clean = (deviceId == null ? '' : String(deviceId)).trim();
        if (!clean || !_deviceSet.has(clean)) return;
        _deviceSet.delete(clean);
        if (_pendingWatcherFlush) clearTimeout(_pendingWatcherFlush);
        _pendingWatcherFlush = setTimeout(_flushWatchersNow, WATCHER_DEBOUNCE_MS);
    }

    function start() {
        if (_started) return;
        _started = true;
        _backoffMs = BACKOFF_MIN_MS;
        _consecutiveFailures = 0;
        _disabledReason = null;
        _needPreflight = false;  // first attempt takes the fast path
        const p = _connect();
        if (p && typeof p.catch === 'function') {
            p.catch(function (err) { _log('start connect error', err); });
        }
        _startHeartbeatTimer();
    }

    function stop() {
        _started = false;
        if (_reconnectTimer) { clearTimeout(_reconnectTimer); _reconnectTimer = null; }
        _stopHeartbeatTimer();
        if (_pendingWatcherFlush) { clearTimeout(_pendingWatcherFlush); _pendingWatcherFlush = null; }
        if (_ws) {
            try { _ws.close(1000, 'client stop'); } catch (_) { /* swallow */ }
            _ws = null;
        }
        _deviceSet.clear();
        _lastHello = null;
        _firstWatcherFlushDone = false;
        _consecutiveFailures = 0;
        _disabledReason = null;
        _needPreflight = false;
    }

    // Manual escape hatch: if the user brings the server back online
    // after the soft-disable tripped, they can call
    // `window.TopologyDeviceEvents.resume()` from devtools and we will
    // retry immediately instead of waiting for a full page reload.
    function resume() {
        _consecutiveFailures = 0;
        _disabledReason = null;
        _backoffMs = BACKOFF_MIN_MS;
        _needPreflight = false;
        if (_started) {
            const p = _connect();
            if (p && typeof p.catch === 'function') {
                p.catch(function (err) { _log('resume connect error', err); });
            }
        }
    }

    function status() {
        return {
            started: _started,
            connected: !!(_ws && _ws.readyState === WebSocket.OPEN),
            readyState: _ws ? _ws.readyState : null,
            username: _currentUsername(),
            watched: Array.from(_deviceSet),
            hello: _lastHello,
            consecutiveFailures: _consecutiveFailures,
            disabledReason: _disabledReason,
            preflightArmed: _needPreflight,
            preflightUrl: PREFLIGHT_URL,
            nextBackoffMs: _backoffMs,
        };
    }

    // Clean shutdown on tab close so the bridge drops our rows promptly.
    window.addEventListener('beforeunload', function () {
        if (_ws && _ws.readyState === WebSocket.OPEN) {
            try { _ws.send(JSON.stringify({ type: 'bye' })); } catch (_) { /* swallow */ }
        }
    });

    // Auto-lifecycle: start/stop with the auth session so modules that
    // need event-bus plumbing don't each have to duplicate this logic.
    window.addEventListener('topology:auth-login', function () {
        try { start(); } catch (err) { console.warn(LOG_PREFIX, 'auto-start failed', err); }
    });
    window.addEventListener('topology:auth-logout', function () {
        try { stop(); } catch (err) { console.warn(LOG_PREFIX, 'auto-stop failed', err); }
    });

    // Public API. The alias `window.TopologyEvents` is kept so existing
    // callers that used that name keep working; new code should target
    // `window.TopologyDeviceEvents` for clarity.
    const api = {
        start: start,
        stop: stop,
        resume: resume,
        status: status,
        setWatchedDevices: setWatchedDevices,
        addWatchedDevice: addWatchedDevice,
        removeWatchedDevice: removeWatchedDevice,
    };
    window.TopologyDeviceEvents = api;
    if (!window.TopologyEvents || typeof window.TopologyEvents.setWatchedDevices !== 'function') {
        // Don't clobber the in-app TopologyEventBus export if another
        // module (e.g. legacy topology-events.js) already installed it.
        // Instead, attach our watcher helpers on a sibling key that the
        // topology.js sync code can probe.
        window.TopologyEvents = api;
    } else {
        // Layer the device-watcher helpers onto the existing object so
        // existing callers using window.TopologyEvents.setWatchedDevices
        // keep working.
        window.TopologyEvents.start = start;
        window.TopologyEvents.stop = stop;
        window.TopologyEvents.resume = resume;
        window.TopologyEvents.status = status;
        window.TopologyEvents.setWatchedDevices = setWatchedDevices;
        window.TopologyEvents.addWatchedDevice = addWatchedDevice;
        window.TopologyEvents.removeWatchedDevice = removeWatchedDevice;
    }

    // If auth already restored a token before this script ran (common on
    // page refresh), kick off the WS now without waiting for another login.
    try {
        if (window.TopologyAuth
            && typeof window.TopologyAuth.isAuthenticated === 'function'
            && window.TopologyAuth.isAuthenticated()) {
            start();
        }
    } catch (err) { /* swallow */ }
})();
