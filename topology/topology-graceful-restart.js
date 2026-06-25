/* topology-graceful-restart.js
 * ----------------------------------------------------------------------------
 * Coordinator for INTENTIONAL backend restarts (auto-recovery from the
 * external health monitor, manual deploys via `health_monitor.py --announce`,
 * etc.). The backend broadcasts a `service-restart` SSE event a second
 * before the supervisor takes the process down; this module catches it and
 * tells the rest of the app to "be quiet for ~N seconds" so users don't
 * see a wall of red `ERR_CONNECTION_REFUSED` errors in DevTools while the
 * app comes back up.
 *
 * Public API (window.GracefulRestart):
 *   isInWindow()                  -> bool, true while we should suppress
 *                                    polls/reconnects.
 *   secondsRemaining()            -> number, 0 when not in window.
 *   markActive(durationS, info)   -> begin a window (used by the SSE
 *                                    listener and `applySnapshotHint`).
 *   applySnapshotHint(snapshot)   -> consume a /api/monitor/health
 *                                    `restart_announce` block (covers the
 *                                    case where a tab loaded mid-restart
 *                                    and missed the live SSE).
 *   onChange(cb)                  -> subscribe to (active, info) events.
 *
 * The module also renders a small "Backend restarting..." chip in the
 * bottom-right of the page, polls /api/health while in the window, and
 * dispatches `topology:graceful-restart-active` /
 * `topology:graceful-restart-cleared` window events for fine-grained
 * consumers.
 *
 * IMPORTANT: this module never makes the app *less* available. If the
 * backend never comes back, the window times out and the app resumes
 * its normal (loud) reconnect behaviour. We only quiet the noise during
 * announced, expected restarts.
 * ----------------------------------------------------------------------------
 */

(function () {
    'use strict';

    if (window.GracefulRestart) return; // idempotent

    var BANNER_ID = 'topology-graceful-restart-banner';
    var CSS_INJECTED = false;
    var LOG = '[GracefulRestart]';

    // Internal state.
    var _activeUntil = 0;       // epoch ms; 0 = not active
    var _info = null;           // { reason, source, eta, started_at }
    var _listeners = [];
    var _healthPollTimer = null;
    var _bannerEl = null;
    var _ownEventSource = null;

    function _now() { return Date.now(); }

    function isInWindow() {
        return _activeUntil > _now();
    }

    function secondsRemaining() {
        var ms = _activeUntil - _now();
        return ms > 0 ? Math.ceil(ms / 1000) : 0;
    }

    function _injectStyle() {
        if (CSS_INJECTED) return;
        CSS_INJECTED = true;
        var css = ''
            + '#' + BANNER_ID + '{'
            + ' position:fixed;right:14px;bottom:14px;z-index:9999;'
            + ' background:rgba(13,30,55,0.94);color:#eaf3ff;'
            + ' border:1px solid rgba(255,255,255,0.18);'
            + ' border-radius:10px;padding:10px 14px;'
            + ' font:500 12.5px/1.35 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;'
            + ' box-shadow:0 6px 22px rgba(0,0,0,0.34);'
            + ' display:flex;align-items:center;gap:10px;'
            + ' max-width:340px;pointer-events:none;'
            + ' animation:gracefulRestartFade 220ms ease-out both;'
            + '}'
            + '#' + BANNER_ID + ' .gr-dot{'
            + ' width:9px;height:9px;border-radius:50%;background:#f5b342;'
            + ' box-shadow:0 0 0 0 rgba(245,179,66,0.55);'
            + ' animation:gracefulRestartPulse 1.4s infinite ease-in-out;'
            + '}'
            + '#' + BANNER_ID + '[data-state="recovered"] .gr-dot{'
            + ' background:#3ddc97;animation:none;box-shadow:none;'
            + '}'
            + '#' + BANNER_ID + ' .gr-title{font-weight:600;letter-spacing:0.02em;}'
            + '#' + BANNER_ID + ' .gr-sub{opacity:0.78;font-size:11.5px;}'
            + '@keyframes gracefulRestartPulse{'
            + ' 0%{box-shadow:0 0 0 0 rgba(245,179,66,0.55);}'
            + ' 70%{box-shadow:0 0 0 9px rgba(245,179,66,0);}'
            + ' 100%{box-shadow:0 0 0 0 rgba(245,179,66,0);}'
            + '}'
            + '@keyframes gracefulRestartFade{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:none;}}';
        var style = document.createElement('style');
        style.setAttribute('data-graceful-restart', '1');
        style.textContent = css;
        (document.head || document.documentElement).appendChild(style);
    }

    function _renderBanner() {
        _injectStyle();
        if (!_bannerEl) {
            _bannerEl = document.createElement('div');
            _bannerEl.id = BANNER_ID;
            _bannerEl.setAttribute('role', 'status');
            _bannerEl.setAttribute('aria-live', 'polite');
            _bannerEl.innerHTML =
                '<span class="gr-dot"></span>'
                + '<div>'
                + '<div class="gr-title">Backend restarting...</div>'
                + '<div class="gr-sub" data-gr-sub>Reconnecting in <span data-gr-secs>15</span>s</div>'
                + '</div>';
            (document.body || document.documentElement).appendChild(_bannerEl);
        }
        _bannerEl.setAttribute('data-state', 'restarting');
        var titleEl = _bannerEl.querySelector('.gr-title');
        var subEl = _bannerEl.querySelector('[data-gr-sub]');
        var secsEl = _bannerEl.querySelector('[data-gr-secs]');
        if (titleEl) titleEl.textContent = 'Backend restarting...';
        if (subEl) subEl.innerHTML = 'Reconnecting in <span data-gr-secs></span>s';
        var fresh = _bannerEl.querySelector('[data-gr-secs]');
        if (fresh) fresh.textContent = String(secondsRemaining());
        if (_info && _info.reason) {
            var reasonEl = _bannerEl.querySelector('.gr-reason');
            if (!reasonEl) {
                reasonEl = document.createElement('div');
                reasonEl.className = 'gr-sub gr-reason';
                reasonEl.style.fontSize = '11px';
                reasonEl.style.opacity = '0.55';
                _bannerEl.firstElementChild.parentNode.appendChild(reasonEl);
            }
            reasonEl.textContent = String(_info.reason).slice(0, 90);
        }
    }

    function _flashRecovered() {
        if (!_bannerEl) return;
        _bannerEl.setAttribute('data-state', 'recovered');
        var titleEl = _bannerEl.querySelector('.gr-title');
        var subEl = _bannerEl.querySelector('[data-gr-sub]');
        if (titleEl) titleEl.textContent = 'Backend recovered';
        if (subEl) subEl.textContent = 'All services online';
        var dismiss = function () {
            if (_bannerEl && _bannerEl.parentNode) _bannerEl.parentNode.removeChild(_bannerEl);
            _bannerEl = null;
        };
        setTimeout(dismiss, 2200);
    }

    function _tickBanner() {
        if (!_bannerEl) return;
        var el = _bannerEl.querySelector('[data-gr-secs]');
        if (el) el.textContent = String(secondsRemaining());
    }

    var _bannerTickTimer = null;
    function _startBannerTick() {
        if (_bannerTickTimer) return;
        _bannerTickTimer = setInterval(function () {
            if (!isInWindow()) {
                clearInterval(_bannerTickTimer);
                _bannerTickTimer = null;
                return;
            }
            _tickBanner();
        }, 1000);
    }

    function _emit(active) {
        try {
            for (var i = 0; i < _listeners.length; i++) {
                try { _listeners[i](active, _info); } catch (_) { /* ignore */ }
            }
        } catch (_) {}
        try {
            window.dispatchEvent(new CustomEvent(
                active ? 'topology:graceful-restart-active' : 'topology:graceful-restart-cleared',
                { detail: { info: _info, until: _activeUntil } }
            ));
        } catch (_) {}
    }

    function onChange(cb) {
        if (typeof cb === 'function') _listeners.push(cb);
        return function unsubscribe() {
            var idx = _listeners.indexOf(cb);
            if (idx >= 0) _listeners.splice(idx, 1);
        };
    }

    function markActive(durationS, info) {
        var dur = Math.max(2, Math.min(180, Number(durationS) || 15));
        var until = _now() + dur * 1000;
        // Refresh window and info; never shrink an existing window.
        if (until > _activeUntil) _activeUntil = until;
        _info = Object.assign({ started_at: _now(), eta: dur }, info || {});
        try { console.info(LOG, 'window opened for', dur, 's, info=', _info); } catch (_) {}
        _renderBanner();
        _startBannerTick();
        _startHealthPoll();
        _emit(true);
    }

    function _clearWindow() {
        if (_activeUntil === 0) return;
        _activeUntil = 0;
        try { console.info(LOG, 'window cleared, info=', _info); } catch (_) {}
        _flashRecovered();
        _info = null;
        if (_healthPollTimer) {
            clearTimeout(_healthPollTimer);
            _healthPollTimer = null;
        }
        _emit(false);
    }

    // Polls /api/health while in the window. The endpoint is unauthenticated
    // so this works even when the user's JWT expired during the downtime.
    function _startHealthPoll() {
        if (_healthPollTimer) return;
        var schedule = function (delay) {
            _healthPollTimer = setTimeout(function () {
                _healthPollTimer = null;
                _probeHealth().then(function (ok) {
                    if (ok && isInWindow()) {
                        _activeUntil = _now() + 1000;
                    }
                    if (!ok && isInWindow()) {
                        return schedule(1500);
                    }
                    if (ok) {
                        return _clearWindow();
                    }
                    if (!isInWindow()) {
                        return _clearWindow();
                    }
                }).catch(function () {
                    schedule(2000);
                });
            }, delay);
        };
        schedule(2500);
    }

    function _probeHealth() {
        return new Promise(function (resolve) {
            try {
                fetch('/api/health', {
                    method: 'GET',
                    cache: 'no-store',
                    credentials: 'same-origin',
                }).then(function (r) {
                    if (!r || !r.ok) return resolve(false);
                    return r.json().then(function (j) {
                        var ok = !!(j && j.serve && j.serve.status === 'ok'
                            && (!j.discovery_api || j.discovery_api.status === 'ok')
                            && (!j.scaler_bridge || j.scaler_bridge.status === 'ok'));
                        resolve(ok);
                    }, function () { resolve(false); });
                }, function () { resolve(false); });
            } catch (_) { resolve(false); }
        });
    }

    function applySnapshotHint(snapshot) {
        try {
            if (!snapshot || typeof snapshot !== 'object') return;
            var ann = snapshot.restart_announce;
            if (!ann || !ann.recent) return;
            var ageS = Number(ann.age_s || 0);
            var eta = Number(ann.eta_seconds || 15);
            // Convert to remaining-window. If the announce already aged
            // past its ETA AND the health endpoint says we're up, no
            // need to render anything -- the worst is over.
            var remaining = Math.max(0, eta - ageS);
            if (remaining <= 0) return;
            markActive(remaining, {
                reason: ann.reason || 'recent restart',
                source: ann.source || 'unknown',
                via: 'snapshot-hint',
            });
        } catch (_) {}
    }

    // ---- Hook the existing SSE listener -------------------------------------
    // topology-file-ops.js already opens an EventSource on /api/topologies/events
    // and listens for `topology-updated`. We add a second listener for
    // `service-restart` on the same EventSource if/when we can reach it,
    // and also expose a fallback hook so that file-ops can forward events
    // to us directly (for older builds that don't allow late-binding).
    function _hookSseListener() {
        // Strategy: poll for window._topologyEventSource (if file-ops exposes
        // it) for up to 30s; if we never see it, fall back to dispatching our
        // own EventSource. The second EventSource is cheap and the backend
        // dedupes via _sse_subscribers.
        var deadline = _now() + 30000;
        var poll = function () {
            if (window._topologyEventSource && typeof window._topologyEventSource.addEventListener === 'function') {
                _attachToEs(window._topologyEventSource);
                return;
            }
            if (_now() >= deadline) {
                // If topology-file-ops.js is loaded and managing the shared
                // stream, keep waiting for it instead of opening a duplicate
                // tokenized EventSource URL just for restart notifications.
                try {
                    var status = window._topologyEventsStatus && window._topologyEventsStatus();
                    if (status) {
                        setTimeout(poll, 1000);
                        return;
                    }
                } catch (_) {}
                _openOwnEventSource();
                return;
            }
            setTimeout(poll, 500);
        };
        poll();
    }

    function _attachToEs(es) {
        if (es._gracefulHooked) return;
        es._gracefulHooked = true;
        es.addEventListener('service-restart', _onServiceRestartEvent);
        try { console.info(LOG, 'attached to existing EventSource'); } catch (_) {}
    }

    function _openOwnEventSource() {
        if (!window.EventSource) return;
        if (_ownEventSource) return;
        var token = '';
        try {
            if (window.TopologyAuth && window.TopologyAuth.getToken) {
                token = window.TopologyAuth.getToken() || '';
            }
        } catch (_) {}
        if (!token) {
            // Try again later -- without auth the SSE stream returns 401.
            setTimeout(_openOwnEventSource, 1500);
            return;
        }
        try {
            var es = new EventSource('/api/topologies/events?token=' + encodeURIComponent(token));
            _ownEventSource = es;
            es.addEventListener('service-restart', _onServiceRestartEvent);
            es.onerror = function () {
                try { es.close(); } catch (_) {}
                if (_ownEventSource === es) _ownEventSource = null;
                setTimeout(_openOwnEventSource, 5000);
            };
            try { console.debug(LOG, 'opened fallback EventSource for service-restart'); } catch (_) {}
        } catch (e) {
            try { console.warn(LOG, 'EventSource open failed', e); } catch (_) {}
        }
    }

    function _onServiceRestartEvent(ev) {
        var payload = {};
        try { payload = JSON.parse(ev.data || '{}'); } catch (_) {}
        var eta = Number(payload && payload.eta_seconds) || 15;
        markActive(eta + 5, {
            reason: payload && payload.reason,
            source: payload && payload.source,
            via: 'sse',
            kind: payload && payload.kind,
            announced_at: payload && payload.at,
        });
    }

    window.addEventListener('topology:auth-logout', function () {
        if (_ownEventSource) {
            try { _ownEventSource.close(); } catch (_) {}
            _ownEventSource = null;
        }
    });

    // ---- Boot ---------------------------------------------------------------
    function _boot() {
        _hookSseListener();
        // On page load, also consult /api/monitor/health so a tab that
        // reloaded mid-restart still gets the banner + suppressed polls.
        try {
            fetch('/api/monitor/health', { cache: 'no-store' }).then(function (r) {
                if (!r) return;
                return r.json().then(function (j) { applySnapshotHint(j); }, function () {});
            }).catch(function () {});
        } catch (_) {}
    }

    window.GracefulRestart = {
        isInWindow: isInWindow,
        secondsRemaining: secondsRemaining,
        markActive: markActive,
        applySnapshotHint: applySnapshotHint,
        onChange: onChange,
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _boot, { once: true });
    } else {
        _boot();
    }

    try { console.info(LOG, 'coordinator loaded'); } catch (_) {}
})();
