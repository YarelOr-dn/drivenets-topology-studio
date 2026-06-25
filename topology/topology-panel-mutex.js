/*
 * topology-panel-mutex.js -- single-overlay-at-a-time coordinator (2026-04-22)
 *
 * Problem this solves
 * -------------------
 * Before this module the topology app had four or five independent
 * "big overlay" panels (AI Assistant right drawer, Scaler CONFIG stack,
 * in-browser terminal, debugger, BD legend, ...). Each one knew how
 * to open/close itself, but there was no global coordinator, so you
 * could end up with the AI drawer AND the Scaler panel AND the
 * terminal all fighting for the same pixels. The user asked:
 *
 *     "configuration scaler should cancel other left handside of
 *      screen panels, like AI, and vise versa, all on screen panels
 *      should be synced if they overlap"
 *
 * Design
 * ------
 * A single global registry of (name -> { close(), isOpen() }). Every
 * panel that wants to participate calls `register()` once on module
 * init; then it calls `markOpen(name)` at the START of its open path
 * and `markClosed(name)` when it closes. markOpen closes every OTHER
 * registered panel before recording the new active name.
 *
 * What this is NOT
 * ----------------
 *  * It is not a reactive store: panels still do their own DOM work.
 *    We just route close calls.
 *  * It is not a replacement for the existing ad-hoc pairwise mutex
 *    wiring (AI <-> Bugs <-> Share, DNAAS <-> NetMapper <-> Topologies).
 *    That wiring stays intact -- this module sits on top so the
 *    BIG overlays finally respect each other.
 *  * It does not prompt / confirm. The user specifically wanted
 *    snappy auto-close behaviour, matching the existing pattern.
 *
 * Public API
 * ----------
 *   window.TopoPanelMutex.register(name, { close, isOpen? })
 *   window.TopoPanelMutex.markOpen(name)       -- closes all others
 *   window.TopoPanelMutex.markClosed(name)     -- releases the slot
 *   window.TopoPanelMutex.getActive()          -- name or null
 *   window.TopoPanelMutex.list()               -- registered names
 *   window.TopoPanelMutex.closeAll(exceptName?)-- fire all closers
 *
 * Safety
 * ------
 *   * Every close is wrapped in try/catch so a single panel's bug
 *     can't leave other panels in an inconsistent state.
 *   * Re-entrant markOpen is idempotent (if you call markOpen('ai')
 *     while 'ai' is already the active panel, nothing happens).
 *   * Closers that aren't registered yet (race on first open) are
 *     ignored silently; subsequent opens will pick them up.
 *
 * Where this module is loaded
 * ---------------------------
 * index.html imports topology-panel-mutex.js BEFORE every file that
 * calls register/markOpen, so there is no ordering surprise. Modules
 * always guard with `if (window.TopoPanelMutex)` so the app still
 * boots if someone deletes this file by accident.
 */

(function () {
    'use strict';

    // Guard against accidental double-load (cache-buster race on old
    // tabs + new server push). The first instance wins.
    if (window.TopoPanelMutex && window.TopoPanelMutex.__installed) return;

    /** @type {Object<string, { close:Function, isOpen:(Function|null) }>} */
    var registry = {};
    var activeName = null;

    function _warn(msg, err) {
        // Keep failures quiet in production but visible on devtools.
        if (window.console && console.warn) {
            console.warn('[TopoPanelMutex] ' + msg, err || '');
        }
    }

    function register(name, spec) {
        if (!name || typeof name !== 'string') {
            _warn('register() needs a string name');
            return;
        }
        if (!spec || typeof spec.close !== 'function') {
            _warn('register(' + name + ') needs { close: fn }');
            return;
        }
        registry[name] = {
            close: spec.close,
            isOpen: typeof spec.isOpen === 'function' ? spec.isOpen : null,
        };
    }

    function _closeOthers(exceptName) {
        Object.keys(registry).forEach(function (n) {
            if (n === exceptName) return;
            var entry = registry[n];
            if (!entry || !entry.close) return;
            // Skip panels that aren't open (cheap no-op wins when isOpen
            // is provided; otherwise we blindly call close and let the
            // panel's own guard handle it).
            var wasOpen = entry.isOpen ? !!entry.isOpen() : true;
            if (!wasOpen) return;
            try {
                entry.close();
            } catch (e) {
                _warn('close(' + n + ') threw', e);
            }
        });
    }

    function markOpen(name) {
        if (!name) return;
        if (activeName === name) return;
        _closeOthers(name);
        activeName = name;
    }

    function markClosed(name) {
        if (activeName === name) activeName = null;
    }

    function getActive() { return activeName; }
    function list() { return Object.keys(registry); }

    function closeAll(exceptName) {
        _closeOthers(exceptName);
        if (!exceptName) activeName = null;
    }

    window.TopoPanelMutex = {
        __installed: true,
        register: register,
        markOpen: markOpen,
        markClosed: markClosed,
        getActive: getActive,
        list: list,
        closeAll: closeAll,
    };
})();
