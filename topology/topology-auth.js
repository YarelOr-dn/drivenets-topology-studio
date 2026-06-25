/**
 * topology-auth.js -- Multi-user authentication for Topology Creator.
 *
 * Provides: login overlay, JWT storage, authFetch() wrapper, auto-401 redirect.
 * Exposes window.TopologyAuth for use by other modules.
 */
(function () {
    'use strict';

    const AUTH_API = '/api/auth';
    const TOKEN_KEY = 'topology_jwt';
    const USER_KEY = 'topology_user';
    // Per-tab marker that survives `_clearSession()` so a 401-induced
    // re-auth can still detect a user switch and force a reload.
    // sessionStorage (not localStorage) so it dies with the tab and
    // cannot leak between separate browser sessions.
    const LAST_USER_KEY = 'topology_last_user';

    let _currentUser = null;
    let _token = null;
    let _loginOverlay = null;

    // ----------------------------------------------------------------
    // Global fetch interceptor -- injects JWT on ALL /api/ requests
    // and handles 401 responses universally (covers 18+ JS files)
    // ----------------------------------------------------------------
    var _originalFetch = window.fetch;
    window.fetch = function (input, init) {
        init = init || {};
        var url = typeof input === 'string' ? input
            : (input instanceof Request ? input.url : String(input));
        if (url.startsWith('/api/') && window.TopologyAuth) {
            var tok = window.TopologyAuth.getToken();
            if (tok) {
                if (!init.headers) {
                    init.headers = {};
                }
                if (init.headers instanceof Headers) {
                    if (!init.headers.has('Authorization')) {
                        init.headers.set('Authorization', 'Bearer ' + tok);
                    }
                } else {
                    if (!init.headers['Authorization']) {
                        init.headers['Authorization'] = 'Bearer ' + tok;
                    }
                }
            }
        }
        return _originalFetch.call(window, input, init).then(function (response) {
            if (response.status === 401 && url.startsWith('/api/')
                && !url.startsWith('/api/auth/login')
                && !url.startsWith('/api/auth/register')
                && window.TopologyAuth) {
                try {
                    var u = window.TopologyAuth.getCurrentUser
                        && window.TopologyAuth.getCurrentUser();
                    if (u && u.username) {
                        sessionStorage.setItem(LAST_USER_KEY, u.username);
                    }
                } catch (_) { /* private mode */ }
                window.TopologyAuth.showLoginOverlay('Session expired. Please sign in again.');
            }
            return response;
        });
    };

    // ----------------------------------------------------------------
    // localStorage namespace -- prefix non-global keys with username
    // so multiple users on the same browser don't collide (33+ keys)
    // ----------------------------------------------------------------
    var _GLOBAL_LS_KEYS = [
        'darkMode', TOKEN_KEY, USER_KEY, 'topology_active_domain'
    ];
    var _origLS = {
        get: localStorage.getItem.bind(localStorage),
        set: localStorage.setItem.bind(localStorage),
        rm: localStorage.removeItem.bind(localStorage)
    };
    var _lsPrefix = '';

    function _patchLocalStorage(username) {
        _lsPrefix = username || '';
        if (!_lsPrefix) return;
        localStorage.getItem = function (k) {
            return _GLOBAL_LS_KEYS.indexOf(k) >= 0 ? _origLS.get(k) : _origLS.get(_lsPrefix + ':' + k);
        };
        localStorage.setItem = function (k, v) {
            return _GLOBAL_LS_KEYS.indexOf(k) >= 0 ? _origLS.set(k, v) : _origLS.set(_lsPrefix + ':' + k, v);
        };
        localStorage.removeItem = function (k) {
            return _GLOBAL_LS_KEYS.indexOf(k) >= 0 ? _origLS.rm(k) : _origLS.rm(_lsPrefix + ':' + k);
        };
    }

    function _restoreLocalStorage() {
        _lsPrefix = '';
        localStorage.getItem = _origLS.get;
        localStorage.setItem = _origLS.set;
        localStorage.removeItem = _origLS.rm;
    }

    function _getStoredToken() {
        try { return _origLS.get(TOKEN_KEY); }
        catch { return null; }
    }

    function _storeSession(token, user) {
        _token = token;
        _currentUser = user;
        try {
            _origLS.set(TOKEN_KEY, token);
            _origLS.set(USER_KEY, JSON.stringify(user));
            _patchLocalStorage(user && user.username);
        } catch { /* private browsing */ }
        try {
            window.dispatchEvent(new CustomEvent('topology:auth-login', {
                detail: { user: user }
            }));
        } catch { /* older browsers */ }
    }

    function _clearSession() {
        _token = null;
        _currentUser = null;
        _restoreLocalStorage();
        try {
            _origLS.rm(TOKEN_KEY);
            _origLS.rm(USER_KEY);
        } catch { /* ok */ }
        _scrubCachedCredentials();
        try {
            window.dispatchEvent(new CustomEvent('topology:auth-logout'));
        } catch { /* older browsers */ }
    }

    function _scrubCachedCredentials() {
        try {
            if (window.ObjectDetection && window.ObjectDetection._pendingPassword) {
                window.ObjectDetection._pendingPassword = null;
            }
        } catch { /* ok */ }
        try {
            var editor = window.topologyEditor || window.editor;
            if (editor && editor.objects) {
                for (var i = 0; i < editor.objects.length; i++) {
                    var obj = editor.objects[i];
                    if (obj && obj.sshConfig) {
                        delete obj.sshConfig._userSavedPass;
                        delete obj.sshConfig._userSavedUser;
                        delete obj.sshConfig._userSavedHost;
                    }
                }
            }
        } catch { /* ok */ }
        try {
            if (window.DeviceMonitor && window.DeviceMonitor._cachedCredentials) {
                window.DeviceMonitor._cachedCredentials = null;
            }
        } catch { /* ok */ }
    }

    // ----------------------------------------------------------------
    // Login / logout transition helpers
    //
    // Auth controls per-user data that lives in many places: the
    // canvas (`editor.objects[]`), per-user localStorage keys, the
    // device-monitor poll loop, the scaler-gui device cache, the
    // DNAAS discovery cache, the sidebar topology list, the sharing
    // cache, etc. Resetting all of those individually on every
    // user-switch is fragile -- a single missed cache leaks one
    // user's data into another user's session, which is a security
    // bug, not just a UX wart.
    //
    // The reliable answer is to hard-reload the page on a user
    // switch. The browser tears down everything, the new boot reads
    // the freshly-stored token from localStorage, and topology.js +
    // friends initialize from scratch under the new identity.
    //
    // Same-user re-auth (a 401 -> sign in again as the same person)
    // skips the reload so unsaved canvas work is preserved.
    // ----------------------------------------------------------------
    function _finishLogin(data) {
        var prevUsername = _currentUser && _currentUser.username;
        if (!prevUsername) {
            try { prevUsername = sessionStorage.getItem(LAST_USER_KEY); }
            catch (_) { /* private mode */ }
        }
        var newUsername = data && data.username;
        var newUser = {
            username: data.username,
            role: data.role,
            display_name: data.display_name,
            is_admin: data.is_admin === true || data.role === 'admin',
            is_owner: data.is_owner === true
        };

        var isUserSwitch = !!(prevUsername && newUsername && prevUsername !== newUsername);

        if (isUserSwitch) {
            // Persist the new session WITHOUT activating the localStorage
            // prefix patch: we are about to reload, and patching now would
            // give in-flight auto-save / sidebar code a tiny window in
            // which it could write the previous user's in-memory state
            // under the *new* user's key.
            try {
                _origLS.set(TOKEN_KEY, data.token);
                _origLS.set(USER_KEY, JSON.stringify(newUser));
                sessionStorage.removeItem(LAST_USER_KEY);
            } catch (_) { /* private mode */ }
            try { window.location.reload(); return; }
            catch (_) { /* fall through to in-place update */ }
        }

        _storeSession(data.token, newUser);
        try { sessionStorage.removeItem(LAST_USER_KEY); } catch (_) {}
        hideLoginOverlay();
        _updateUserMenu();
        _startAnnouncementPolling();
        _loadMyAvatarPrefs();
        if (window.TopologyDomains && window.TopologyDomains.init) {
            window.TopologyDomains.init();
        }
    }

    function _doExplicitLogout() {
        // Wipe credentials, then hard-reload so the next sign-in starts
        // from a guaranteed-clean DOM, canvas, and module cache. Without
        // the reload, the previous user's `editor.objects[]`, device-
        // monitor timers, scaler-gui caches, etc. would all linger until
        // the user manually refreshed -- a leak across identities.
        try { sessionStorage.removeItem(LAST_USER_KEY); } catch (_) {}
        _clearSession();
        try {
            window.location.reload();
        } catch (_) {
            _updateUserMenu();
            showLoginOverlay();
        }
    }

    function _initials(name) {
        if (!name) return '??';
        var parts = name.split(/\s+/);
        if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
        return name.substring(0, 2).toUpperCase();
    }

    // Build an avatar for the top-bar user pill (and related surfaces).
    // Uses the shared cloud-face generator published by topology-share.js
    // so every teammate shows up with the same friendly creature across
    // the share dialog, the user pill, and any future presence UI.
    // Falls back to plain initials if CloudAvatar isn't available yet
    // (e.g. topology-share.js hasn't finished loading, though defer order
    // normally guarantees it has).
    function _avatarHtml(user, sizePx) {
        var seed = user && (user.username || user.display_name) || '?';
        if (window.CloudAvatar && typeof window.CloudAvatar.svg === 'function') {
            return window.CloudAvatar.svg(seed, sizePx);
        }
        return _initials(user && user.display_name);
    }

    function _roleBadgeClass(role) {
        var map = { admin: 'role-admin', manager: 'role-manager', team_leader: 'role-leader', engineer: 'role-engineer', viewer: 'role-viewer' };
        return map[role] || 'role-engineer';
    }

    function _roleLabel(role) {
        var map = { admin: 'Admin', manager: 'Manager', team_leader: 'Team Lead', engineer: 'Engineer', viewer: 'Viewer' };
        return map[role] || role;
    }

    // ----------------------------------------------------------------
    // authFetch -- drop-in replacement for fetch() that injects JWT
    // ----------------------------------------------------------------
    async function authFetch(url, options) {
        options = options || {};
        if (!options.headers) options.headers = {};
        if (_token) {
            options.headers['Authorization'] = 'Bearer ' + _token;
        }
        var resp = await fetch(url, options);
        if (resp.status === 401) {
            try {
                if (_currentUser && _currentUser.username) {
                    sessionStorage.setItem(LAST_USER_KEY, _currentUser.username);
                }
            } catch (_) { /* private mode */ }
            _clearSession();
            showLoginOverlay('Session expired. Please sign in again.');
            throw new Error('AUTH_REQUIRED');
        }
        return resp;
    }

    // ----------------------------------------------------------------
    // Login overlay (glass-style, matching DriveNets design)
    // ----------------------------------------------------------------
    function _createLoginOverlay() {
        if (_loginOverlay) return _loginOverlay;

        var overlay = document.createElement('div');
        overlay.id = 'auth-login-overlay';
        overlay.className = 'auth-login-overlay';

        overlay.innerHTML =
            '<div class="auth-login-card">' +
                '<div class="auth-login-logo">' +
                    '<svg width="36" height="36" viewBox="0 0 24 24">' +
                        '<rect x="2" y="5" width="8" height="2.5" rx="1.25" fill="white"/>' +
                        '<rect x="2" y="10.5" width="11" height="2.5" rx="1.25" fill="white"/>' +
                        '<rect x="2" y="16" width="14" height="2.5" rx="1.25" fill="white"/>' +
                        '<line x1="6" y1="4" x2="19" y2="20" stroke="white" stroke-width="2.5" stroke-linecap="round"/>' +
                    '</svg>' +
                    '<span class="auth-login-title">Drive<span class="auth-login-accent">Nets</span> Topology Creator</span>' +
                '</div>' +
                '<div class="auth-login-subtitle">Sign in with your DriveNets credentials</div>' +
                '<div id="auth-login-error" class="auth-login-error" style="display:none;"></div>' +
                '<form id="auth-login-form" class="auth-login-form">' +
                    '<div class="auth-field-group">' +
                        '<label for="auth-username">Username</label>' +
                        '<input type="text" id="auth-username" name="username" autocomplete="username" autocapitalize="off" spellcheck="false" placeholder="firstname or firstname.lastname" required />' +
                    '</div>' +
                    '<div class="auth-field-group">' +
                        '<label for="auth-password">Password</label>' +
                        '<input type="password" id="auth-password" name="password" autocomplete="current-password" placeholder="lastname" required />' +
                    '</div>' +
                    '<button type="submit" class="auth-login-btn" id="auth-login-submit">Sign In</button>' +
                '</form>' +
                '<div class="auth-login-footer">' +
                    '<span class="auth-register-link" id="auth-show-register">New here? Create account</span>' +
                '</div>' +
                '<div id="auth-register-section" class="auth-register-section" style="display:none;">' +
                    '<form id="auth-register-form" class="auth-login-form">' +
                        '<div class="auth-field-group">' +
                            '<label for="auth-reg-username">Username</label>' +
                            '<input type="text" id="auth-reg-username" name="username" autocomplete="username" autocapitalize="off" required />' +
                        '</div>' +
                        '<div class="auth-field-group">' +
                            '<label for="auth-reg-display">Display Name</label>' +
                            '<input type="text" id="auth-reg-display" name="display_name" required />' +
                        '</div>' +
                        '<div class="auth-field-group">' +
                            '<label for="auth-reg-password">Password</label>' +
                            '<input type="password" id="auth-reg-password" name="password" minlength="6" autocomplete="new-password" required />' +
                        '</div>' +
                        '<button type="submit" class="auth-login-btn">Create Account</button>' +
                        '<span class="auth-register-link" id="auth-show-login">Back to Sign In</span>' +
                    '</form>' +
                '</div>' +
            '</div>';

        document.body.appendChild(overlay);
        _loginOverlay = overlay;

        // Login form submit
        document.getElementById('auth-login-form').addEventListener('submit', async function (e) {
            e.preventDefault();
            var btn = document.getElementById('auth-login-submit');
            var errEl = document.getElementById('auth-login-error');
            errEl.style.display = 'none';
            btn.disabled = true;
            btn.textContent = 'Signing in...';

            try {
                var resp = await fetch(AUTH_API + '/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        username: document.getElementById('auth-username').value.trim(),
                        password: document.getElementById('auth-password').value
                    })
                });
                var data = await resp.json();
                if (!resp.ok) {
                    errEl.textContent = data.detail || 'Login failed';
                    errEl.style.display = 'block';
                    return;
                }
                _finishLogin(data);
            } catch (err) {
                errEl.textContent = 'Connection error: ' + err.message;
                errEl.style.display = 'block';
            } finally {
                btn.disabled = false;
                btn.textContent = 'Sign In';
            }
        });

        // Register toggle
        document.getElementById('auth-show-register').addEventListener('click', function () {
            document.getElementById('auth-login-form').style.display = 'none';
            document.querySelector('.auth-login-footer').style.display = 'none';
            document.getElementById('auth-register-section').style.display = 'block';
        });
        document.getElementById('auth-show-login').addEventListener('click', function () {
            document.getElementById('auth-login-form').style.display = '';
            document.querySelector('.auth-login-footer').style.display = '';
            document.getElementById('auth-register-section').style.display = 'none';
        });

        // Register form submit
        document.getElementById('auth-register-form').addEventListener('submit', async function (e) {
            e.preventDefault();
            var errEl = document.getElementById('auth-login-error');
            errEl.style.display = 'none';
            try {
                var resp = await fetch(AUTH_API + '/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        username: document.getElementById('auth-reg-username').value.trim(),
                        password: document.getElementById('auth-reg-password').value,
                        display_name: document.getElementById('auth-reg-display').value.trim()
                    })
                });
                var data = await resp.json();
                if (!resp.ok) {
                    errEl.textContent = data.detail || 'Registration failed';
                    errEl.style.display = 'block';
                    return;
                }
                _finishLogin(data);
            } catch (err) {
                errEl.textContent = 'Connection error: ' + err.message;
                errEl.style.display = 'block';
            }
        });

        return overlay;
    }

    function showLoginOverlay(message) {
        var ov = _createLoginOverlay();
        if (message) {
            var errEl = document.getElementById('auth-login-error');
            if (errEl) { errEl.textContent = message; errEl.style.display = 'block'; }
        }
        ov.classList.add('show');
        var uInput = document.getElementById('auth-username');
        if (uInput) setTimeout(function () { uInput.focus(); }, 100);
    }

    function hideLoginOverlay() {
        if (_loginOverlay) _loginOverlay.classList.remove('show');
    }

    // ----------------------------------------------------------------
    // User menu (top-bar, right side)
    //
    // The top-bar uses overflow-x: auto, which (per CSS spec) coerces
    // overflow-y: visible to overflow-y: auto. That clips any absolutely-
    // positioned descendant (z-index can NOT escape an ancestor scroll
    // container). The dropdown is therefore portaled to document.body and
    // positioned with position: fixed so it lives above the topbar.
    // ----------------------------------------------------------------
    var _docClickBound = false;
    var _resizeBound = false;

    function _bindGlobalDropdownClosers() {
        if (_docClickBound) return;
        document.addEventListener('click', function () {
            var dd = document.getElementById('auth-user-dropdown');
            if (dd) dd.classList.remove('show');
        });
        _docClickBound = true;
    }

    function _bindDropdownReposition() {
        if (_resizeBound) return;
        var reposition = function () {
            var dd = document.getElementById('auth-user-dropdown');
            var pill = document.getElementById('auth-user-pill');
            if (!dd || !pill || !dd.classList.contains('show')) return;
            _positionDropdownAtPill(pill, dd);
        };
        window.addEventListener('resize', reposition);
        window.addEventListener('scroll', reposition, true);
        _resizeBound = true;
    }

    function _positionDropdownAtPill(pill, dd) {
        var r = pill.getBoundingClientRect();
        dd.style.position = 'fixed';
        dd.style.top = (r.bottom + 8) + 'px';
        dd.style.right = (window.innerWidth - r.right) + 'px';
        dd.style.left = 'auto';
    }

    // Small SVG icon bank used by the menu (kept inline so the dropdown
    // doesn't add a font/image dependency). Each icon is 16x16,
    // stroke-based, uses currentColor so it inherits menu-item color.
    var _MENU_ICONS = {
        key:        '<svg class="auth-dd-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>',
        users:      '<svg class="auth-dd-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="7" r="4"/><path d="M2 21v-2a4 4 0 014-4h6a4 4 0 014 4v2"/><path d="M16 3.13a4 4 0 010 7.75M21 21v-2a4 4 0 00-3-3.87"/></svg>',
        logout:     '<svg class="auth-dd-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/></svg>',
        diag:       '<svg class="auth-dd-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9-6-18-3 9H2"/></svg>',
        sparkle:    '<svg class="auth-dd-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5 5l2.5 2.5M16.5 16.5L19 19M5 19l2.5-2.5M16.5 7.5L19 5"/></svg>',
        megaphone:  '<svg class="auth-dd-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11v2a2 2 0 002 2h2l9 4V5l-9 4H5a2 2 0 00-2 2z"/><path d="M18 8a5 5 0 010 8"/></svg>',
        flag:       '<svg class="auth-dd-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 21V4h10l1 3h5v10h-6l-1-3H6v7"/></svg>',
        book:       '<svg class="auth-dd-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 016.5 17H20V3H6.5A2.5 2.5 0 004 5.5v14z"/><path d="M4 19.5V22h16"/></svg>',
        history:    '<svg class="auth-dd-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 11.8 3.7"/><polyline points="3 5 3 12 10 12"/></svg>',
        mask:       '<svg class="auth-dd-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>',
        reset:      '<svg class="auth-dd-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15A9 9 0 1118 5.3"/></svg>',
        power:      '<svg class="auth-dd-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v10"/><path d="M18.36 6.64a9 9 0 11-12.73 0"/></svg>',
        crown:      '<svg class="auth-dd-crown" viewBox="0 0 24 24" fill="currentColor"><path d="M3 7l5 4 4-7 4 7 5-4-2 12H5L3 7z"/></svg>',
        chevron:    '<svg width="12" height="12" viewBox="0 0 24 24" style="opacity:0.6"><path d="M7 10l5 5 5-5" stroke="currentColor" stroke-width="2" fill="none"/></svg>',
        palette:    '<svg class="auth-dd-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="13.5" cy="6.5" r="1.5"/><circle cx="17.5" cy="10.5" r="1.5"/><circle cx="8.5" cy="7.5" r="1.5"/><circle cx="6.5" cy="12.5" r="1.5"/><path d="M12 2a10 10 0 100 20c1.5 0 3-1 3-2.5s-.5-2-1.5-2.5-.5-2.5 1-2.5H17a5 5 0 005-5c0-4.4-4.4-7.5-10-7.5z"/></svg>'
    };

    // Map our role / owner status to the liquid-glass left-stripe class
    // + matching human-readable tier label.
    function _roleStripeClass(u) {
        if (!u) return 'auth-user-dropdown--user';
        if (u.is_owner)        return 'auth-user-dropdown--owner';
        if (u.role === 'admin')   return 'auth-user-dropdown--admin';
        if (u.role === 'manager') return 'auth-user-dropdown--manager';
        return 'auth-user-dropdown--user';
    }

    function _updateUserMenu() {
        var container = document.getElementById('auth-user-menu');
        if (!container) return;

        var oldDd = document.getElementById('auth-user-dropdown');
        if (oldDd) oldDd.remove();

        if (!_currentUser) {
            container.innerHTML = '<button class="auth-signin-btn" id="auth-topbar-signin">Sign In</button>';
            document.getElementById('auth-topbar-signin').addEventListener('click', function () {
                showLoginOverlay();
            });
            return;
        }
        var u = _currentUser;
        var isAdmin = !!(u.is_admin || u.role === 'admin' || u.is_owner);
        var isOwner = !!u.is_owner;

        // Top-bar pill: CloudAvatar.html() already returns its own
        // `<span class="cloud-avatar">` wrapper, so we do NOT re-wrap
        // it in <div class="auth-avatar ...">; doing that caused the
        // pill to render a double-size avatar with clipping + hover
        // bounce being chopped by the outer overflow:hidden. Only the
        // non-CloudAvatar fallback path needs the legacy wrapper.
        var pillAvatar = (window.CloudAvatar && window.CloudAvatar.html)
            ? window.CloudAvatar.html(u.username || u.display_name || '?', 30, {
                bounce: true,
                breathing: true,
                extraClass: 'auth-pill-avatar'
              })
            : ('<div class="auth-avatar auth-avatar-cloud">' + _avatarHtml(u, 30) + '</div>');
        var roleLabelForPill = isOwner ? 'Owner' : _roleLabel(u.role);
        var roleClassForPill = isOwner ? 'role-admin' : _roleBadgeClass(u.role);
        // Palette data attribute lets the CSS pick a pastel halo that
        // matches the avatar's own gradient -- so the closed pill
        // visually "reflects" its cloud icon instead of sitting in a
        // generic grey background.
        var palette = (window.CloudAvatar && window.CloudAvatar.paletteFor)
            ? (window.CloudAvatar.paletteFor(u.username || u.display_name || '?') || '')
            : '';
        var pillRoleAttr = isOwner ? 'owner' : (u.role || 'user');
        container.innerHTML =
            '<div class="auth-user-pill" id="auth-user-pill" tabindex="0" role="button" ' +
                'aria-haspopup="true" aria-expanded="false" ' +
                'data-palette="' + _esc(palette) + '" ' +
                'data-role="' + _esc(pillRoleAttr) + '">' +
                '<span class="auth-user-pill__halo" aria-hidden="true"></span>' +
                pillAvatar +
                '<span class="auth-user-name">' + (u.display_name || u.username) + '</span>' +
                '<span class="auth-role-badge ' + roleClassForPill + '">' + roleLabelForPill + '</span>' +
                _MENU_ICONS.chevron +
            '</div>';

        // Big header avatar gets the breathing idle animation AND the
        // sparkle ring (owners only -- subtle celebration of the tier).
        // Any user whose feature-flag override enables sparkle also
        // gets it, via window.TopoFeatureFlags (if present).
        var sparkleOn = isOwner || (window.TopoFeatureFlags && window.TopoFeatureFlags.cloud_avatar_sparkle === true);
        var headerAvatar = (window.CloudAvatar && window.CloudAvatar.html)
            ? window.CloudAvatar.html(u.username || u.display_name || '?', 48, {
                breathing: true,
                bounce: true,
                sparkle: sparkleOn,
                extraClass: 'auth-dd-cloud'
              })
            : ('<div class="auth-avatar-lg auth-avatar-cloud">' + _avatarHtml(u, 48) + '</div>');

        var paletteHint = (window.CloudAvatar && window.CloudAvatar.paletteFor)
            ? window.CloudAvatar.paletteFor(u.username || u.display_name || '?') : '';

        var dd = document.createElement('div');
        dd.className = 'auth-user-dropdown ' + _roleStripeClass(u);
        dd.id = 'auth-user-dropdown';
        dd.setAttribute('role', 'menu');
        dd.setAttribute('tabindex', '-1');

        var ownerBadge = isOwner
            ? '<span class="auth-dd-owner-badge" title="Deployment owner">' + _MENU_ICONS.crown + ' Owner</span>'
            : '';
        var paletteRow = paletteHint
            ? '<div class="auth-dd-palette-hint">' + paletteHint + ' cloud</div>'
            : '';

        // Build the items in three tiers: regular, admin, owner. A
        // single array keeps the keyboard-nav focus order obvious, and
        // lets the click handler dispatch by `data-action` instead of
        // per-item `getElementById` lookups.
        var items = [];
        items.push({ id: 'changepw', label: 'Change Password',       icon: _MENU_ICONS.key,    cls: '' });
        // Everyone (engineer, viewer, manager, admin, owner) can
        // personalise their cloud avatar. Intentionally NOT gated by
        // role so the UX is universal.
        items.push({ id: 'customize-cloud', label: 'Customize My Cloud', icon: _MENU_ICONS.palette, cls: '' });

        if (isAdmin) {
            items.push({ sectionLabel: 'Admin tools', cls: 'auth-dropdown-section-label--admin' });
            items.push({ id: 'diagnostics',  label: 'Server Diagnostics',   icon: _MENU_ICONS.diag,      cls: '' });
            items.push({ id: 'shared-key',   label: 'AI Shared-Key Status', icon: _MENU_ICONS.sparkle,   cls: '' });
            items.push({ id: 'audit',        label: 'Recent Activity',      icon: _MENU_ICONS.history,   cls: '' });
            items.push({ id: 'broadcast',    label: 'Broadcast Announcement', icon: _MENU_ICONS.megaphone, cls: '' });
            items.push({ id: 'flags',        label: 'Feature Flags',        icon: _MENU_ICONS.flag,      cls: '' });
            items.push({ id: 'reload-knowledge', label: 'Reload AI Knowledge', icon: _MENU_ICONS.book,   cls: '' });
            items.push({ id: 'reload-blueprints', label: 'Reload AI Blueprints', icon: _MENU_ICONS.book, cls: '' });
            items.push({ id: 'users',        label: 'User Management',      icon: _MENU_ICONS.users,     cls: '' });
        } else if (u.role === 'manager') {
            items.push({ id: 'users',        label: 'User Management',      icon: _MENU_ICONS.users,     cls: '' });
        }

        if (isOwner) {
            items.push({ sectionLabel: 'Owner tools', cls: 'auth-dropdown-section-label--owner' });
            items.push({ id: 'impersonate',  label: 'View as another user', icon: _MENU_ICONS.mask,    cls: 'auth-dropdown-owner' });
            items.push({ id: 'reset-configs',label: 'Reset All AI Configs', icon: _MENU_ICONS.reset,   cls: 'auth-dropdown-owner auth-dropdown-danger' });
            items.push({ id: 'restart',      label: 'Restart Server',       icon: _MENU_ICONS.power,   cls: 'auth-dropdown-owner auth-dropdown-danger' });
        }

        // Always-last entry.
        items.push({ sep: true });
        items.push({ id: 'logout',        label: 'Sign Out',             icon: _MENU_ICONS.logout, cls: 'auth-dropdown-danger' });

        var html = '';
        html += '<div class="auth-user-dropdown__stripe"></div>';
        html += '<div class="auth-dropdown-header">';
        html +=   '<div class="auth-dd-avatar-wrap">';
        html +=     headerAvatar;
        if (isOwner) html += _MENU_ICONS.crown.replace('auth-dd-crown', 'auth-dd-crown');
        html +=     '<span class="auth-dd-online-dot" title="Online"></span>';
        html +=   '</div>';
        html +=   '<div class="auth-dd-name-wrap">';
        html +=     '<div class="auth-dd-name">' + (u.display_name || u.username) + ownerBadge + '</div>';
        html +=     '<div class="auth-dd-username">@' + u.username + '</div>';
        html +=     paletteRow;
        html +=   '</div>';
        html += '</div>';

        for (var i = 0; i < items.length; i++) {
            var it = items[i];
            if (it.sep) { html += '<div class="auth-dropdown-sep"></div>'; continue; }
            if (it.sectionLabel) {
                html += '<div class="auth-dropdown-section-label ' + (it.cls || '') + '">' + it.sectionLabel + '</div>';
                continue;
            }
            html += '<div class="auth-dropdown-item ' + (it.cls || '') + '" data-action="' + it.id + '" role="menuitem" tabindex="-1">';
            html += (it.icon || '');
            html += '<span>' + it.label + '</span>';
            html += '</div>';
        }
        dd.innerHTML = html;
        document.body.appendChild(dd);

        var pill = document.getElementById('auth-user-pill');
        pill.addEventListener('click', function (e) {
            e.stopPropagation();
            _positionDropdownAtPill(pill, dd);
            var isShown = dd.classList.toggle('show');
            pill.setAttribute('aria-expanded', isShown ? 'true' : 'false');
            if (isShown) {
                _dropdownResetFocus(dd);
            }
        });
        // Keyboard: open dropdown with Space/Enter/ArrowDown when the pill is focused.
        pill.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
                e.preventDefault();
                _positionDropdownAtPill(pill, dd);
                if (!dd.classList.contains('show')) {
                    dd.classList.add('show');
                    pill.setAttribute('aria-expanded', 'true');
                }
                _dropdownFocusFirst(dd);
            }
        });

        dd.addEventListener('click', function (e) {
            var tgt = e.target.closest('.auth-dropdown-item');
            if (!tgt) { e.stopPropagation(); return; }
            var action = tgt.getAttribute('data-action');
            dd.classList.remove('show');
            pill.setAttribute('aria-expanded', 'false');
            _handleMenuAction(action);
        });

        // Keyboard nav inside the open dropdown: Esc closes, Up/Down move
        // focus, Home/End jump to first/last, Enter activates.
        dd.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                e.preventDefault();
                dd.classList.remove('show');
                pill.setAttribute('aria-expanded', 'false');
                pill.focus();
                return;
            }
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Home' || e.key === 'End') {
                e.preventDefault();
                _dropdownMoveFocus(dd, e.key);
                return;
            }
            if (e.key === 'Enter' || e.key === ' ') {
                var cur = dd.querySelector('.auth-dropdown-item.is-focused');
                if (cur) {
                    e.preventDefault();
                    cur.click();
                }
            }
        });

        _bindGlobalDropdownClosers();
        _bindDropdownReposition();
    }

    // ------------------------------------------------------------
    // Keyboard-nav helpers for the user dropdown
    // ------------------------------------------------------------
    function _dropdownItems(dd) {
        return Array.from(dd.querySelectorAll('.auth-dropdown-item'));
    }
    function _dropdownResetFocus(dd) {
        _dropdownItems(dd).forEach(function (el) { el.classList.remove('is-focused'); });
    }
    function _dropdownFocusFirst(dd) {
        var items = _dropdownItems(dd);
        if (!items.length) return;
        _dropdownResetFocus(dd);
        items[0].classList.add('is-focused');
        items[0].focus();
    }
    function _dropdownMoveFocus(dd, key) {
        var items = _dropdownItems(dd);
        if (!items.length) return;
        var cur = dd.querySelector('.auth-dropdown-item.is-focused');
        var idx = cur ? items.indexOf(cur) : -1;
        var next = idx;
        if (key === 'ArrowDown') next = (idx + 1) % items.length;
        else if (key === 'ArrowUp') next = (idx <= 0 ? items.length - 1 : idx - 1);
        else if (key === 'Home') next = 0;
        else if (key === 'End') next = items.length - 1;
        _dropdownResetFocus(dd);
        items[next].classList.add('is-focused');
        items[next].focus();
    }

    // ------------------------------------------------------------
    // Menu action dispatcher
    // ------------------------------------------------------------
    function _handleMenuAction(action) {
        switch (action) {
            case 'changepw':   return _showChangePasswordDialog();
            case 'customize-cloud': return _showCustomizeCloudDialog();
            case 'users':      return _showUsersDialog();
            case 'diagnostics':return _showDiagnosticsDialog();
            case 'shared-key': return _showSharedKeyDialog();
            case 'audit':      return _showAuditDialog();
            case 'broadcast':  return _showBroadcastDialog();
            case 'flags':      return _showFeatureFlagsDialog();
            case 'reload-knowledge': return _triggerReloadKnowledge();
            case 'reload-blueprints': return _triggerReloadBlueprints();
            case 'impersonate':return _showImpersonateDialog();
            case 'reset-configs':return _showResetConfigsConfirm();
            case 'restart':    return _showRestartConfirm();
            case 'logout':
                _doExplicitLogout();
                return;
        }
    }

    function _showChangePasswordDialog() {
        var existing = document.getElementById('auth-changepw-dialog');
        if (existing) existing.remove();

        var dialog = document.createElement('div');
        dialog.id = 'auth-changepw-dialog';
        dialog.className = 'auth-login-overlay show';
        dialog.innerHTML =
            '<div class="auth-login-card" style="max-width:360px">' +
                '<div class="auth-login-subtitle">Change Password</div>' +
                '<div id="auth-cp-error" class="auth-login-error" style="display:none;"></div>' +
                '<div id="auth-cp-success" class="auth-login-success" style="display:none;"></div>' +
                '<form id="auth-cp-form" class="auth-login-form">' +
                    '<div class="auth-field-group">' +
                        '<label>Current Password</label>' +
                        '<input type="password" id="auth-cp-current" required />' +
                    '</div>' +
                    '<div class="auth-field-group">' +
                        '<label>New Password</label>' +
                        '<input type="password" id="auth-cp-new" minlength="6" required />' +
                    '</div>' +
                    '<button type="submit" class="auth-login-btn">Update Password</button>' +
                    '<button type="button" class="auth-cancel-btn" id="auth-cp-cancel">Cancel</button>' +
                '</form>' +
            '</div>';
        document.body.appendChild(dialog);

        document.getElementById('auth-cp-cancel').addEventListener('click', function () {
            dialog.remove();
        });
        document.getElementById('auth-cp-form').addEventListener('submit', async function (e) {
            e.preventDefault();
            var errEl = document.getElementById('auth-cp-error');
            var sucEl = document.getElementById('auth-cp-success');
            errEl.style.display = 'none';
            sucEl.style.display = 'none';
            try {
                var resp = await authFetch(AUTH_API + '/me/change-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        current_password: document.getElementById('auth-cp-current').value,
                        new_password: document.getElementById('auth-cp-new').value
                    })
                });
                if (!resp.ok) {
                    var d = await resp.json();
                    errEl.textContent = d.detail || 'Failed';
                    errEl.style.display = 'block';
                    return;
                }
                sucEl.textContent = 'Password updated successfully';
                sucEl.style.display = 'block';
                setTimeout(function () { dialog.remove(); }, 1500);
            } catch (err) {
                if (err.message !== 'AUTH_REQUIRED') {
                    errEl.textContent = err.message;
                    errEl.style.display = 'block';
                }
            }
        });
    }

    // ----------------------------------------------------------------
    // Customize Cloud dialog (available to EVERY logged-in user)
    // ----------------------------------------------------------------
    // Built around window.CloudAvatar so the live preview is
    // pixel-identical to the pill, share-dialog chip, and every other
    // surface that renders the user's avatar. The store is a single
    // PATCH /api/auth/me/profile call with an `{ avatar: {...} }` body;
    // unset fields fall back to the deterministic hash, so "reset"
    // clears the whole avatar object on the server and re-renders the
    // default. Accessible via the user dropdown for ALL roles.

    var _CUSTOMIZE_STATE = null;

    async function _showCustomizeCloudDialog() {
        if (!_currentUser) return;
        if (!window.CloudAvatar || typeof window.CloudAvatar.catalogue !== 'function') {
            _toastOrAlert('Avatar customiser not ready yet — reload the page.', 'warn');
            return;
        }
        var seed = _currentUser.username || _currentUser.display_name || '?';
        var catalogue = window.CloudAvatar.catalogue();

        // Snapshot the current overrides so the dialog opens pre-selected
        // to what the user already saved. Missing fields render the
        // deterministic hash defaults (same as the top-bar pill).
        var current = Object.assign({}, window.CloudAvatar.getOverrides(seed));
        _CUSTOMIZE_STATE = {
            seed: seed,
            palette: current.palette || null,
            face: (current.face !== undefined ? current.face : null),
            accessory: (current.accessory !== undefined ? current.accessory : null),
            baseline: current
        };

        var shell = _openDialogShell('Customize My Cloud', _renderCustomizeBody(catalogue), {
            id: 'auth-customize-cloud-dialog',
            width: '640px'
        });
        _bindCustomizeHandlers(shell, catalogue);
    }

    function _renderCustomizeBody(catalogue) {
        var state = _CUSTOMIZE_STATE;
        var previewHtml = _renderCustomizePreview();

        var paletteRow = catalogue.palettes.map(function (p) {
            var selected = (state.palette === p.name) ? ' is-selected' : '';
            return '<button type="button" class="cloud-cust-chip cloud-cust-chip--palette' + selected + '" ' +
                'data-palette="' + _esc(p.name) + '" ' +
                'style="background:' + p.body + ';border-color:' + p.edge + ';" ' +
                'title="' + _esc(p.name) + '" aria-label="' + _esc(p.name) + ' palette">' +
                '<span class="cloud-cust-chip-name">' + _esc(p.name) + '</span>' +
            '</button>';
        }).join('');

        // Face picker: render a real mini cloud-avatar for each face so
        // the user sees exactly what they're picking (happy, wink, etc.).
        // Uses the CURRENT palette choice so the preview swatch also
        // updates when the user re-picks a palette.
        var faceRow = catalogue.faces.map(function (f) {
            var selected = (state.face === f.id) ? ' is-selected' : '';
            var tmpSvg = window.CloudAvatar.svg(state.seed, 40, {
                palette: state.palette || undefined,
                face: f.id,
                accessory: 0
            });
            return '<button type="button" class="cloud-cust-face' + selected + '" ' +
                'data-face="' + f.id + '" aria-label="Face ' + (f.id + 1) + '">' + tmpSvg + '</button>';
        }).join('');

        var accessoryRow = catalogue.accessories.map(function (a) {
            var selected = (state.accessory === a.id) ? ' is-selected' : '';
            var tmpSvg = window.CloudAvatar.svg(state.seed, 40, {
                palette: state.palette || undefined,
                face: state.face !== null ? state.face : undefined,
                accessory: a.id
            });
            return '<button type="button" class="cloud-cust-accessory' + selected + '" ' +
                'data-accessory="' + a.id + '" title="' + _esc(a.label) + '" aria-label="' + _esc(a.label) + '">' +
                tmpSvg +
                '<span class="cloud-cust-accessory-label">' + _esc(a.label) + '</span>' +
            '</button>';
        }).join('');

        return '' +
            '<div class="cloud-cust-wrap">' +
                '<div class="cloud-cust-preview-area">' +
                    '<div class="cloud-cust-preview" id="cloud-cust-preview">' + previewHtml + '</div>' +
                    '<div class="cloud-cust-preview-meta">' +
                        '<div class="cloud-cust-preview-name">' + _esc(_currentUser.display_name || _currentUser.username) + '</div>' +
                        '<div class="cloud-cust-preview-sub">Pick a palette, face, and accessory. Your teammates will see the same cloud everywhere.</div>' +
                    '</div>' +
                '</div>' +
                '<div class="cloud-cust-section">' +
                    '<div class="cloud-cust-section-title">Palette</div>' +
                    '<div class="cloud-cust-grid cloud-cust-grid--palette">' + paletteRow + '</div>' +
                '</div>' +
                '<div class="cloud-cust-section">' +
                    '<div class="cloud-cust-section-title">Expression</div>' +
                    '<div class="cloud-cust-grid cloud-cust-grid--face">' + faceRow + '</div>' +
                '</div>' +
                '<div class="cloud-cust-section">' +
                    '<div class="cloud-cust-section-title">Accessory</div>' +
                    '<div class="cloud-cust-grid cloud-cust-grid--accessory">' + accessoryRow + '</div>' +
                '</div>' +
                '<div class="cloud-cust-footer">' +
                    '<button type="button" id="cloud-cust-reset" class="auth-cancel-btn cloud-cust-reset-btn">Reset to default</button>' +
                    '<div style="flex:1;"></div>' +
                    '<span id="cloud-cust-status" class="cloud-cust-status"></span>' +
                    '<button type="button" id="cloud-cust-save" class="auth-login-btn cloud-cust-save-btn">Save</button>' +
                '</div>' +
            '</div>';
    }

    function _renderCustomizePreview() {
        var state = _CUSTOMIZE_STATE;
        var opts = { bounce: true, breathing: true, sparkle: true };
        if (state.palette) opts.palette = state.palette;
        if (state.face !== null && state.face !== undefined) opts.face = state.face;
        if (state.accessory !== null && state.accessory !== undefined) opts.accessory = state.accessory;
        return window.CloudAvatar.html(state.seed, 128, opts);
    }

    function _bindCustomizeHandlers(shell, catalogue) {
        var body = shell.body;

        function refresh() {
            body.innerHTML = _renderCustomizeBody(catalogue);
            _bindCustomizeHandlers(shell, catalogue);
        }

        body.querySelectorAll('.cloud-cust-chip--palette').forEach(function (btn) {
            btn.addEventListener('click', function () {
                _CUSTOMIZE_STATE.palette = btn.getAttribute('data-palette');
                refresh();
            });
        });
        body.querySelectorAll('.cloud-cust-face').forEach(function (btn) {
            btn.addEventListener('click', function () {
                _CUSTOMIZE_STATE.face = parseInt(btn.getAttribute('data-face'), 10);
                refresh();
            });
        });
        body.querySelectorAll('.cloud-cust-accessory').forEach(function (btn) {
            btn.addEventListener('click', function () {
                _CUSTOMIZE_STATE.accessory = parseInt(btn.getAttribute('data-accessory'), 10);
                refresh();
            });
        });

        var saveBtn = document.getElementById('cloud-cust-save');
        var resetBtn = document.getElementById('cloud-cust-reset');
        var statusEl = document.getElementById('cloud-cust-status');
        if (saveBtn) {
            saveBtn.addEventListener('click', async function () {
                var avatar = {};
                if (_CUSTOMIZE_STATE.palette) avatar.palette = _CUSTOMIZE_STATE.palette;
                if (_CUSTOMIZE_STATE.face !== null) avatar.face = _CUSTOMIZE_STATE.face;
                if (_CUSTOMIZE_STATE.accessory !== null) avatar.accessory = _CUSTOMIZE_STATE.accessory;
                statusEl.textContent = 'Saving...';
                saveBtn.disabled = true;
                try {
                    var resp = await authFetch('/api/auth/me/profile', {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ avatar: avatar })
                    });
                    if (!resp.ok) throw new Error('HTTP ' + resp.status);
                    var data = await resp.json();
                    var saved = (data && data.avatar) || avatar;
                    window.CloudAvatar.setOverrides(_CUSTOMIZE_STATE.seed, saved);
                    statusEl.textContent = 'Saved.';
                    _updateUserMenu();
                    setTimeout(function () { shell.dialog.remove(); }, 600);
                } catch (err) {
                    statusEl.textContent = 'Failed: ' + err.message;
                    saveBtn.disabled = false;
                }
            });
        }
        if (resetBtn) {
            resetBtn.addEventListener('click', async function () {
                statusEl.textContent = 'Resetting...';
                resetBtn.disabled = true;
                try {
                    var resp = await authFetch('/api/auth/me/profile/reset', { method: 'POST' });
                    if (!resp.ok) throw new Error('HTTP ' + resp.status);
                    window.CloudAvatar.clearOverrides(_CUSTOMIZE_STATE.seed);
                    _CUSTOMIZE_STATE.palette = null;
                    _CUSTOMIZE_STATE.face = null;
                    _CUSTOMIZE_STATE.accessory = null;
                    statusEl.textContent = 'Reset.';
                    _updateUserMenu();
                    refresh();
                } catch (err) {
                    statusEl.textContent = 'Failed: ' + err.message;
                } finally {
                    resetBtn.disabled = false;
                }
            });
        }
    }

    // ----------------------------------------------------------------
    // User Management dialog (admin / manager)
    // ----------------------------------------------------------------
    function _escapeHtml(s) {
        if (s == null) return '';
        return String(s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function _fmtDate(iso) {
        if (!iso) return '-';
        try {
            var d = new Date(iso);
            if (isNaN(d.getTime())) return iso;
            return d.toLocaleString();
        } catch (e) { return iso; }
    }

    // Per-instance state so the filter + fetched list stay in sync
    // across re-renders without cluttering the module globals.
    var _usersDialogState = { users: [], filter: '' };

    function _showUsersDialog() {
        var existing = document.getElementById('auth-users-dialog');
        if (existing) existing.remove();

        _usersDialogState = { users: [], filter: '' };

        var canCreate = _currentUser && _currentUser.role === 'admin';
        var dialog = document.createElement('div');
        dialog.id = 'auth-users-dialog';
        dialog.className = 'auth-login-overlay show';
        dialog.innerHTML =
            '<div class="auth-login-card auth-users-card">' +
                '<div class="auth-users-head">' +
                    '<div>' +
                        '<div class="auth-users-title">User Management</div>' +
                        '<div class="auth-users-sub">All users on this server</div>' +
                    '</div>' +
                    '<div class="auth-users-actions">' +
                        (canCreate ? '<button type="button" class="auth-login-btn auth-users-add" id="auth-users-add">+ Add User</button>' : '') +
                        '<button type="button" class="auth-cancel-btn" id="auth-users-close">Close</button>' +
                    '</div>' +
                '</div>' +
                '<div class="auth-admin-search" style="margin:10px 0 4px;">' +
                    '<input type="search" id="auth-users-search" placeholder="Search by name, username, email, or role…" autocomplete="off" />' +
                    '<span class="auth-admin-search-count" id="auth-users-count">0</span>' +
                '</div>' +
                '<div id="auth-users-error" class="auth-login-error" style="display:none;"></div>' +
                '<div id="auth-users-list" class="auth-users-list">' +
                    '<div class="auth-users-loading">Loading users...</div>' +
                '</div>' +
            '</div>';
        document.body.appendChild(dialog);

        document.getElementById('auth-users-close').addEventListener('click', function () {
            dialog.remove();
        });
        document.getElementById('auth-users-search').addEventListener('input', function () {
            _usersDialogState.filter = this.value.trim().toLowerCase();
            _renderUsersTable(_usersDialogState.users);
        });
        if (canCreate) {
            document.getElementById('auth-users-add').addEventListener('click', function () {
                _showCreateUserDialog(function () { _refreshUsersList(); });
            });
        }

        _refreshUsersList();
    }

    async function _refreshUsersList() {
        var listEl = document.getElementById('auth-users-list');
        var errEl = document.getElementById('auth-users-error');
        if (!listEl) return;
        listEl.innerHTML = '<div class="auth-users-loading">Loading users...</div>';
        if (errEl) errEl.style.display = 'none';
        try {
            var resp = await authFetch(AUTH_API + '/users');
            if (!resp.ok) {
                var d = await resp.json().catch(function () { return {}; });
                throw new Error(d.detail || ('HTTP ' + resp.status));
            }
            var data = await resp.json();
            _usersDialogState.users = data.users || [];
            _renderUsersTable(_usersDialogState.users);
        } catch (err) {
            if (err.message === 'AUTH_REQUIRED') return;
            if (errEl) {
                errEl.textContent = 'Failed to load users: ' + err.message;
                errEl.style.display = 'block';
            }
            listEl.innerHTML = '';
        }
    }

    function _renderUsersTable(users) {
        var listEl = document.getElementById('auth-users-list');
        if (!listEl) return;
        var countEl = document.getElementById('auth-users-count');
        var isOwnerViewer = !!(_currentUser && (_currentUser.is_owner
            || _currentUser.username === 'yarel'
            || _currentUser.username === 'yarel-or'
            || _currentUser.username === 'yarelor'));
        var canManage = _currentUser && _currentUser.role === 'admin';
        var meName = _currentUser && _currentUser.username;
        var q = (_usersDialogState && _usersDialogState.filter) || '';
        var filtered = users.filter(function (u) {
            if (!q) return true;
            var hay = ((u.display_name || '') + ' ' + (u.username || '') + ' ' + (u.email || '') + ' ' + (u.role || '')).toLowerCase();
            return hay.indexOf(q) >= 0;
        });
        if (countEl) countEl.textContent = filtered.length + '/' + users.length;
        if (!filtered.length) {
            listEl.innerHTML = '<div class="auth-users-empty">' + (q ? 'No users match "' + _escapeHtml(q) + '".' : 'No users found.') + '</div>';
            return;
        }
        var rows = filtered.map(function (u) {
            var isSelf = u.username === meName;
            var actions = '';
            if (canManage) {
                actions += '<button type="button" class="auth-users-btn-edit" data-u="' + _escapeHtml(u.username) + '">Edit</button>';
            }
            if (isOwnerViewer && !isSelf) {
                actions += '<button type="button" class="auth-users-btn-view" data-u="' + _escapeHtml(u.username) + '" title="Browse this user&#39;s workspace (read-only)">View</button>';
            }
            if (canManage && !isSelf) {
                actions += '<button type="button" class="auth-users-btn-del" data-u="' + _escapeHtml(u.username) + '">Delete</button>';
            }
            return '' +
                '<tr>' +
                    '<td>' +
                        '<div class="auth-users-cell-user">' +
                            '<div class="auth-avatar auth-avatar-cloud" style="width:24px;height:24px;font-size:10px;">' + _avatarHtml(u, 24) + '</div>' +
                            '<div>' +
                                '<div class="auth-users-cell-name">' + _escapeHtml(u.display_name || u.username) + (isSelf ? ' <span class="auth-users-self">(you)</span>' : '') + '</div>' +
                                '<div class="auth-users-cell-uname">@' + _escapeHtml(u.username) + '</div>' +
                            '</div>' +
                        '</div>' +
                    '</td>' +
                    '<td><span class="auth-role-badge ' + _roleBadgeClass(u.role) + '">' + _roleLabel(u.role) + '</span></td>' +
                    '<td>' + _escapeHtml(u.email || '-') + '</td>' +
                    '<td style="text-align:center;">' + (u.topology_count || 0) + '</td>' +
                    '<td>' + _fmtDate(u.last_login) + '</td>' +
                    '<td>' + _fmtDate(u.created_at) + '</td>' +
                    ((canManage || isOwnerViewer) ? '<td class="auth-users-actions-cell">' + actions + '</td>' : '') +
                '</tr>';
        }).join('');

        listEl.innerHTML =
            '<table class="auth-users-table">' +
                '<thead><tr>' +
                    '<th>User</th>' +
                    '<th>Role</th>' +
                    '<th>Email</th>' +
                    '<th>Topologies</th>' +
                    '<th>Last Login</th>' +
                    '<th>Created</th>' +
                    ((canManage || isOwnerViewer) ? '<th></th>' : '') +
                '</tr></thead>' +
                '<tbody>' + rows + '</tbody>' +
            '</table>';

        if (canManage) {
            listEl.querySelectorAll('.auth-users-btn-edit').forEach(function (b) {
                b.addEventListener('click', function () {
                    var uname = b.getAttribute('data-u');
                    var u = users.find(function (x) { return x.username === uname; });
                    if (u) _showEditUserDialog(u, function () { _refreshUsersList(); });
                });
            });
            listEl.querySelectorAll('.auth-users-btn-del').forEach(function (b) {
                b.addEventListener('click', function () {
                    var uname = b.getAttribute('data-u');
                    if (!uname) return;
                    if (!confirm('Deactivate user "' + uname + '"?\n\nThe account will be marked inactive and the user will not be able to log in. Their topology data is preserved on disk.')) return;
                    _deleteUser(uname).then(function () { _refreshUsersList(); });
                });
            });
        }
        // Owner-only "View workspace" shortcut: closes this dialog,
        // reopens the view-as picker, and auto-selects the clicked
        // user so the workspace pane populates immediately. Keeps the
        // leader's "I want to see what @alice sees" journey one click
        // long from either entry point (dropdown or users table).
        if (isOwnerViewer) {
            listEl.querySelectorAll('.auth-users-btn-view').forEach(function (b) {
                b.addEventListener('click', function () {
                    var uname = b.getAttribute('data-u');
                    var u = users.find(function (x) { return x.username === uname; });
                    if (!u) return;
                    var dlg = document.getElementById('auth-users-dialog');
                    if (dlg) dlg.remove();
                    _showImpersonateDialog();
                    setTimeout(function () { _onSelectViewAsUser(u); }, 60);
                });
            });
        }
    }

    async function _deleteUser(username) {
        var errEl = document.getElementById('auth-users-error');
        try {
            var resp = await authFetch(AUTH_API + '/users/' + encodeURIComponent(username), { method: 'DELETE' });
            if (!resp.ok) {
                var d = await resp.json().catch(function () { return {}; });
                throw new Error(d.detail || ('HTTP ' + resp.status));
            }
        } catch (err) {
            if (err.message === 'AUTH_REQUIRED') return;
            if (errEl) {
                errEl.textContent = 'Failed to deactivate user: ' + err.message;
                errEl.style.display = 'block';
            }
        }
    }

    function _showCreateUserDialog(onDone) {
        var existing = document.getElementById('auth-create-user-dialog');
        if (existing) existing.remove();
        var dialog = document.createElement('div');
        dialog.id = 'auth-create-user-dialog';
        dialog.className = 'auth-login-overlay show';
        dialog.style.zIndex = '300001';
        dialog.innerHTML =
            '<div class="auth-login-card" style="max-width:420px">' +
                '<div class="auth-login-subtitle">Add New User</div>' +
                '<div id="auth-cu-error" class="auth-login-error" style="display:none;"></div>' +
                '<form id="auth-cu-form" class="auth-login-form">' +
                    '<div class="auth-field-group">' +
                        '<label>Username</label>' +
                        '<input type="text" id="auth-cu-username" required pattern="[a-zA-Z0-9_.\\-]{2,64}" autocomplete="off" />' +
                    '</div>' +
                    '<div class="auth-field-group">' +
                        '<label>Display Name</label>' +
                        '<input type="text" id="auth-cu-display" required maxlength="128" autocomplete="off" />' +
                    '</div>' +
                    '<div class="auth-field-group">' +
                        '<label>Email (optional)</label>' +
                        '<input type="email" id="auth-cu-email" autocomplete="off" />' +
                    '</div>' +
                    '<div class="auth-field-group">' +
                        '<label>Role</label>' +
                        '<select id="auth-cu-role">' +
                            '<option value="viewer">Viewer</option>' +
                            '<option value="engineer" selected>Engineer</option>' +
                            '<option value="team_leader">Team Lead</option>' +
                            '<option value="manager">Manager</option>' +
                            '<option value="admin">Admin</option>' +
                        '</select>' +
                    '</div>' +
                    '<div class="auth-field-group">' +
                        '<label>Initial Password</label>' +
                        '<input type="password" id="auth-cu-password" minlength="6" required autocomplete="new-password" />' +
                    '</div>' +
                    '<button type="submit" class="auth-login-btn">Create User</button>' +
                    '<button type="button" class="auth-cancel-btn" id="auth-cu-cancel">Cancel</button>' +
                '</form>' +
            '</div>';
        document.body.appendChild(dialog);

        document.getElementById('auth-cu-cancel').addEventListener('click', function () {
            dialog.remove();
        });
        document.getElementById('auth-cu-form').addEventListener('submit', async function (e) {
            e.preventDefault();
            var errEl = document.getElementById('auth-cu-error');
            errEl.style.display = 'none';
            var payload = {
                username: document.getElementById('auth-cu-username').value.trim(),
                display_name: document.getElementById('auth-cu-display').value.trim(),
                email: document.getElementById('auth-cu-email').value.trim() || null,
                role: document.getElementById('auth-cu-role').value,
                password: document.getElementById('auth-cu-password').value
            };
            try {
                var resp = await authFetch(AUTH_API + '/users', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (!resp.ok) {
                    var d = await resp.json().catch(function () { return {}; });
                    var msg = d.detail;
                    if (Array.isArray(msg)) msg = msg.map(function (x) { return x.msg || JSON.stringify(x); }).join('; ');
                    throw new Error(msg || ('HTTP ' + resp.status));
                }
                dialog.remove();
                if (typeof onDone === 'function') onDone();
            } catch (err) {
                if (err.message === 'AUTH_REQUIRED') return;
                errEl.textContent = err.message;
                errEl.style.display = 'block';
            }
        });
    }

    function _showEditUserDialog(u, onDone) {
        var existing = document.getElementById('auth-edit-user-dialog');
        if (existing) existing.remove();
        var dialog = document.createElement('div');
        dialog.id = 'auth-edit-user-dialog';
        dialog.className = 'auth-login-overlay show';
        dialog.style.zIndex = '300001';
        var roles = ['viewer', 'engineer', 'team_leader', 'manager', 'admin'];
        var roleOptions = roles.map(function (r) {
            return '<option value="' + r + '"' + (u.role === r ? ' selected' : '') + '>' + _roleLabel(r) + '</option>';
        }).join('');
        dialog.innerHTML =
            '<div class="auth-login-card" style="max-width:420px">' +
                '<div class="auth-login-subtitle">Edit ' + _escapeHtml(u.display_name || u.username) + '</div>' +
                '<div class="auth-users-cell-uname" style="margin-bottom:10px;">@' + _escapeHtml(u.username) + '</div>' +
                '<div id="auth-eu-error" class="auth-login-error" style="display:none;"></div>' +
                '<div id="auth-eu-success" class="auth-login-success" style="display:none;"></div>' +
                '<form id="auth-eu-form" class="auth-login-form">' +
                    '<div class="auth-field-group">' +
                        '<label>Display Name</label>' +
                        '<input type="text" id="auth-eu-display" value="' + _escapeHtml(u.display_name || '') + '" maxlength="128" autocomplete="off" />' +
                    '</div>' +
                    '<div class="auth-field-group">' +
                        '<label>Email</label>' +
                        '<input type="email" id="auth-eu-email" value="' + _escapeHtml(u.email || '') + '" autocomplete="off" />' +
                    '</div>' +
                    '<div class="auth-field-group">' +
                        '<label>Role</label>' +
                        '<select id="auth-eu-role">' + roleOptions + '</select>' +
                    '</div>' +
                    '<div class="auth-field-group">' +
                        '<label>New Password (leave blank to keep current)</label>' +
                        '<input type="password" id="auth-eu-password" minlength="6" autocomplete="new-password" />' +
                    '</div>' +
                    '<button type="submit" class="auth-login-btn">Save Changes</button>' +
                    '<button type="button" class="auth-cancel-btn" id="auth-eu-cancel">Cancel</button>' +
                '</form>' +
            '</div>';
        document.body.appendChild(dialog);

        document.getElementById('auth-eu-cancel').addEventListener('click', function () {
            dialog.remove();
        });
        document.getElementById('auth-eu-form').addEventListener('submit', async function (e) {
            e.preventDefault();
            var errEl = document.getElementById('auth-eu-error');
            var sucEl = document.getElementById('auth-eu-success');
            errEl.style.display = 'none';
            sucEl.style.display = 'none';
            var payload = {};
            var dn = document.getElementById('auth-eu-display').value.trim();
            var em = document.getElementById('auth-eu-email').value.trim();
            var rl = document.getElementById('auth-eu-role').value;
            var pw = document.getElementById('auth-eu-password').value;
            if (dn && dn !== (u.display_name || '')) payload.display_name = dn;
            if (em !== (u.email || '')) payload.email = em;
            if (rl && rl !== u.role) payload.role = rl;
            if (pw) payload.password = pw;
            if (!Object.keys(payload).length) {
                errEl.textContent = 'No changes to save.';
                errEl.style.display = 'block';
                return;
            }
            try {
                var resp = await authFetch(AUTH_API + '/users/' + encodeURIComponent(u.username), {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (!resp.ok) {
                    var d = await resp.json().catch(function () { return {}; });
                    var msg = d.detail;
                    if (Array.isArray(msg)) msg = msg.map(function (x) { return x.msg || JSON.stringify(x); }).join('; ');
                    throw new Error(msg || ('HTTP ' + resp.status));
                }
                sucEl.textContent = 'User updated successfully';
                sucEl.style.display = 'block';
                setTimeout(function () { dialog.remove(); if (typeof onDone === 'function') onDone(); }, 800);
            } catch (err) {
                if (err.message === 'AUTH_REQUIRED') return;
                errEl.textContent = err.message;
                errEl.style.display = 'block';
            }
        });
    }

    // ----------------------------------------------------------------
    // Admin + Owner dialogs (2026-04-22)
    // ----------------------------------------------------------------
    // Each of these is opened from the user-menu dropdown when the
    // caller has the required tier. The backend endpoints enforce
    // admin / owner gating -- the dialogs are pure UI on top.
    // All dialogs reuse the existing .auth-login-overlay / auth-card
    // styling + liquid-glass classes so they match the rest of the app.
    // ----------------------------------------------------------------
    function _toastOrAlert(message, level) {
        if (window.TopologyNotifications && typeof window.TopologyNotifications.show === 'function') {
            window.TopologyNotifications.show({ message: message, level: level || 'info' });
        } else if (window.Toast && typeof window.Toast.show === 'function') {
            window.Toast.show(message);
        } else {
            alert(message);
        }
    }

    function _openDialogShell(title, innerHtml, opts) {
        var id = (opts && opts.id) || ('auth-admin-dialog-' + Date.now());
        var existing = document.getElementById(id);
        if (existing) existing.remove();
        var dialog = document.createElement('div');
        dialog.id = id;
        dialog.className = 'auth-login-overlay show';
        // The .auth-admin-card modifier carries its own padding / scroll
        // rules (see styles.css) so we only pass width + an inline
        // fallback. Close button becomes a 30x30 X pill sitting flush
        // with the title, which reads as a proper dialog chrome rather
        // than a form cancel.
        dialog.innerHTML =
            '<div class="auth-login-card auth-admin-card" style="max-width:' + (opts && opts.width ? opts.width : '560px') + ';width:92vw">' +
                '<div class="auth-login-subtitle">' +
                    '<span>' + title + '</span>' +
                    '<button type="button" class="auth-cancel-btn" id="' + id + '-close" aria-label="Close" title="Close (Esc)">\u00D7</button>' +
                '</div>' +
                '<div id="' + id + '-body">' + innerHtml + '</div>' +
            '</div>';
        document.body.appendChild(dialog);
        document.getElementById(id + '-close').addEventListener('click', function () { dialog.remove(); });
        dialog.addEventListener('click', function (e) { if (e.target === dialog) dialog.remove(); });
        // Escape-to-close keeps the modal feeling native. We scope the
        // handler to this dialog instance so multiple open modals don't
        // stomp each other, and we clean up when the dialog leaves the
        // DOM so the listener doesn't outlive the UI.
        var escHandler = function (e) {
            if (e.key === 'Escape' && document.body.contains(dialog)) {
                e.preventDefault();
                dialog.remove();
            }
        };
        document.addEventListener('keydown', escHandler);
        var mo = new MutationObserver(function () {
            if (!document.body.contains(dialog)) {
                document.removeEventListener('keydown', escHandler);
                mo.disconnect();
            }
        });
        mo.observe(document.body, { childList: true, subtree: false });
        return { dialog: dialog, body: document.getElementById(id + '-body'), id: id };
    }

    function _esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]; }); }

    // Helpers shared by every admin dialog: keeps the per-dialog code
    // short and ensures every piece of muted/note/status text uses the
    // theme-aware .auth-admin-* classes from styles.css (which adapt to
    // both dark + light mode, unlike the previous ad-hoc inline styles).
    function _adminToolbar(leftHtml, rightHtml) {
        return '<div class="auth-admin-toolbar">' +
                    '<div class="left">' + (leftHtml || '') + '</div>' +
                    '<div class="right">' + (rightHtml || '') + '</div>' +
               '</div>';
    }
    function _adminGhostBtn(id, label, title) {
        return '<button type="button" id="' + id + '" class="auth-admin-ghost"' +
               (title ? ' title="' + _esc(title) + '"' : '') + '>' + label + '</button>';
    }
    function _adminError(msg) { return '<div class="auth-admin-status-err" style="padding:8px 10px;">' + _esc(msg) + '</div>'; }
    function _adminLoading(label) {
        return '<div class="auth-admin-muted" style="padding:14px 4px;">' + _esc(label || 'Loading…') + '</div>';
    }
    function _fmtUptime(sec) {
        sec = Math.max(0, parseInt(sec || 0, 10));
        if (sec < 60) return sec + 's';
        var m = Math.floor(sec / 60); var s = sec % 60;
        if (m < 60) return m + 'm ' + s + 's';
        var h = Math.floor(m / 60); m = m % 60;
        if (h < 48) return h + 'h ' + m + 'm';
        var d = Math.floor(h / 24); h = h % 24;
        return d + 'd ' + h + 'h';
    }

    async function _showDiagnosticsDialog() {
        var shell = _openDialogShell('Server Diagnostics', '', { id: 'auth-diag-dialog', width: '620px' });
        var autoState = { on: false, timer: null };
        async function refresh() {
            var loadingNode = shell.body.querySelector('[data-role="diag-body"]');
            if (loadingNode) loadingNode.innerHTML = _adminLoading('Refreshing…');
            try {
                var resp = await authFetch('/api/admin/diagnostics');
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                var data = await resp.json();
                var svcRows = Object.keys(data.services || {}).map(function (k) {
                    var s = data.services[k] || {};
                    var dot = s.alive
                        ? '<span class="auth-admin-status-ok">● running</span>'
                        : '<span class="auth-admin-status-err">● down</span>';
                    var fail = s.health_fail_count
                        ? ' <span class="auth-admin-status-warn" title="Consecutive health check failures">·' + _esc(s.health_fail_count) + '</span>'
                        : '';
                    return '<tr>' +
                        '<td style="padding:5px 10px;font-weight:600;">' + _esc(k) + '</td>' +
                        '<td style="padding:5px 10px;">' + dot + fail + '</td>' +
                        '<td style="padding:5px 10px;" class="auth-admin-muted">pid ' + _esc(s.pid == null ? '—' : s.pid) + '</td>' +
                        '<td style="padding:5px 10px;" class="auth-admin-muted">' + _esc(_fmtUptime(s.uptime_sec)) + '</td>' +
                    '</tr>';
                }).join('');
                var mem = data.memory || {};
                var sharedKey = data.gemini_shared_key_set
                    ? '<span class="auth-admin-status-ok">ACTIVE</span>'
                    : '<span class="auth-admin-status-warn">not set</span>';
                var bodyHtml =
                    '<div class="auth-admin-note" style="margin-bottom:8px;">Snapshot ' + _esc(data.now_utc) + '</div>' +
                    '<table style="width:100%;border-collapse:collapse;margin-bottom:10px;font-size:12px;">' + svcRows + '</table>' +
                    '<div style="display:grid;grid-template-columns:auto 1fr;gap:6px 14px;font-size:12px;margin-bottom:10px;">' +
                        '<div class="auth-admin-label">Server port</div><div><code>' + _esc(data.server_port) + '</code></div>' +
                        '<div class="auth-admin-label">Users</div><div><code>' + _esc(data.topology_users_count) + '</code></div>' +
                        '<div class="auth-admin-label">Topology files</div><div><code>' + _esc(data.topology_files_count) + '</code></div>' +
                        '<div class="auth-admin-label">Gemini shared key</div><div>' + sharedKey + '</div>' +
                        '<div class="auth-admin-label">Owner override</div><div><code>' + _esc(data.owner_username_override || '(default yarel)') + '</code></div>' +
                        '<div class="auth-admin-label">Memory (RSS)</div><div><code>' + _esc(mem.maxrss_kb || 0) + ' KB</code></div>' +
                        '<div class="auth-admin-label">CPU (user)</div><div><code>' + _esc(mem.user_time_sec || 0) + 's</code></div>' +
                        '<div class="auth-admin-label">CPU (sys)</div><div><code>' + _esc(mem.system_time_sec || 0) + 's</code></div>' +
                    '</div>';
                shell.body.querySelector('[data-role="diag-body"]').innerHTML = bodyHtml;
                shell.body.__lastDiagData = data;
            } catch (err) {
                shell.body.querySelector('[data-role="diag-body"]').innerHTML = _adminError('Could not load diagnostics: ' + err.message);
            }
        }
        shell.body.innerHTML =
            _adminToolbar(
                '<span class="auth-admin-muted">Process + shared-service health</span>',
                _adminGhostBtn('auth-diag-copy', 'Copy JSON', 'Copy the latest response as JSON') +
                _adminGhostBtn('auth-diag-auto', 'Auto off', 'Toggle 5-second auto-refresh') +
                _adminGhostBtn('auth-diag-refresh', 'Refresh', 'Refresh now')) +
            '<div data-role="diag-body">' + _adminLoading() + '</div>';
        document.getElementById('auth-diag-refresh').addEventListener('click', refresh);
        document.getElementById('auth-diag-auto').addEventListener('click', function () {
            autoState.on = !autoState.on;
            this.textContent = autoState.on ? 'Auto on' : 'Auto off';
            if (autoState.on) {
                autoState.timer = setInterval(function () {
                    if (document.body.contains(shell.dialog)) refresh();
                    else { clearInterval(autoState.timer); autoState.timer = null; }
                }, 5000);
            } else if (autoState.timer) {
                clearInterval(autoState.timer); autoState.timer = null;
            }
        });
        document.getElementById('auth-diag-copy').addEventListener('click', function () {
            var payload = shell.body.__lastDiagData;
            if (!payload) return;
            try {
                navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
                this.textContent = 'Copied!';
                var self = this; setTimeout(function () { self.textContent = 'Copy JSON'; }, 1200);
            } catch (_) {}
        });
        refresh();
    }

    async function _showSharedKeyDialog() {
        var shell = _openDialogShell('AI Shared-Key Status', '', { id: 'auth-sharedkey-dialog' });
        async function refresh() {
            var body = shell.body.querySelector('[data-role="sk-body"]');
            if (body) body.innerHTML = _adminLoading('Checking…');
            try {
                var resp = await authFetch('/api/admin/shared-key-status');
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                var data = await resp.json();
                var statusLine = data.enabled
                    ? '<span class="auth-admin-status-ok">● Active</span> <span class="auth-admin-muted">— every user is force-overridden to Gemini</span>'
                    : '<span class="auth-admin-status-warn">● Not set</span> <span class="auth-admin-muted">— users fall back to their own AI config</span>';
                body.innerHTML =
                    '<div style="font-size:12.5px;margin-bottom:10px;">' + statusLine + '</div>' +
                    '<div style="display:grid;grid-template-columns:auto 1fr;gap:6px 14px;font-size:12px;margin-bottom:12px;align-items:center;">' +
                        '<div class="auth-admin-label">Env var</div><div><code>' + _esc(data.env_var) + '</code></div>' +
                        '<div class="auth-admin-label">Masked key</div><div style="display:flex;align-items:center;gap:8px;"><code data-role="sk-masked">' + _esc(data.masked_key || '(none)') + '</code>' +
                            (data.masked_key ? ' <button type="button" class="auth-admin-ghost" id="auth-sk-copy">Copy</button>' : '') + '</div>' +
                        '<div class="auth-admin-label">Per-user AI configs</div><div><code>' + _esc(data.per_user_configs_count) + '</code> <span class="auth-admin-muted">stored (overridden when shared key is active)</span></div>' +
                    '</div>' +
                    '<div class="auth-admin-note">To rotate the key, set a new <code>GEMINI_API_KEY</code> in the server environment and restart the process. The frontend will pick up the new status on the next page load.</div>';
                var copyBtn = document.getElementById('auth-sk-copy');
                if (copyBtn) copyBtn.addEventListener('click', function () {
                    try {
                        navigator.clipboard.writeText(data.masked_key);
                        this.textContent = 'Copied!';
                        var self = this; setTimeout(function () { self.textContent = 'Copy'; }, 1200);
                    } catch (_) {}
                });
            } catch (err) {
                body.innerHTML = _adminError('Could not load shared-key status: ' + err.message);
            }
        }
        shell.body.innerHTML =
            _adminToolbar(
                '<span class="auth-admin-muted">Deployment-wide Gemini override</span>',
                _adminGhostBtn('auth-sk-refresh', 'Refresh')) +
            '<div data-role="sk-body">' + _adminLoading() + '</div>';
        document.getElementById('auth-sk-refresh').addEventListener('click', refresh);
        refresh();
    }

    async function _showAuditDialog() {
        var shell = _openDialogShell('Recent Activity', '', { id: 'auth-audit-dialog', width: '720px' });
        var state = { events: [], filter: '', typeFilter: '' };
        function render() {
            var q = (state.filter || '').toLowerCase();
            var type = state.typeFilter || '';
            var visible = state.events.filter(function (e) {
                if (type && e.event !== type) return false;
                if (!q) return true;
                var detail = '';
                try { detail = JSON.stringify(e.detail || {}); } catch (_) {}
                return (e.event || '').toLowerCase().indexOf(q) >= 0
                    || (e.username || '').toLowerCase().indexOf(q) >= 0
                    || detail.toLowerCase().indexOf(q) >= 0;
            });
            var countEl = document.getElementById('auth-audit-count');
            if (countEl) countEl.textContent = visible.length + '/' + state.events.length;
            var bodyEl = shell.body.querySelector('[data-role="audit-body"]');
            if (!visible.length) {
                bodyEl.innerHTML = '<div class="auth-admin-muted" style="padding:12px 4px;">No events match the current filter.</div>';
                return;
            }
            var rows = visible.map(function (e) {
                var when = new Date((e.ts || 0) * 1000).toLocaleString();
                var detail = '';
                try { detail = JSON.stringify(e.detail || {}); } catch (_) { detail = ''; }
                if (detail === '{}') detail = '';
                return '<tr>' +
                    '<td style="padding:5px 10px;white-space:nowrap;font-size:11px;" class="auth-admin-muted">' + _esc(when) + '</td>' +
                    '<td style="padding:5px 10px;font-weight:600;">' + _esc(e.event) + '</td>' +
                    '<td style="padding:5px 10px;">' + _esc(e.username) + '</td>' +
                    '<td style="padding:5px 10px;font-family:ui-monospace,monospace;font-size:11px;" class="auth-admin-muted">' + _esc(detail) + '</td>' +
                '</tr>';
            }).join('');
            bodyEl.innerHTML =
                '<table style="width:100%;border-collapse:collapse;font-size:12px;">' +
                    '<thead><tr style="text-align:left;border-bottom:1px solid rgba(255,255,255,0.08);">' +
                        '<th style="padding:6px 10px;">When</th><th style="padding:6px 10px;">Event</th><th style="padding:6px 10px;">User</th><th style="padding:6px 10px;">Detail</th>' +
                    '</tr></thead><tbody>' + rows + '</tbody>' +
                '</table>';
        }
        async function refresh() {
            var bodyEl = shell.body.querySelector('[data-role="audit-body"]');
            if (bodyEl) bodyEl.innerHTML = _adminLoading('Refreshing…');
            try {
                var resp = await authFetch('/api/admin/audit');
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                var data = await resp.json();
                state.events = data.events || [];
                var typeSel = document.getElementById('auth-audit-type');
                var current = typeSel ? typeSel.value : '';
                var types = {};
                state.events.forEach(function (e) { types[e.event] = true; });
                if (typeSel) {
                    typeSel.innerHTML = '<option value="">All event types</option>' +
                        Object.keys(types).sort().map(function (t) {
                            return '<option value="' + _esc(t) + '"' + (t === current ? ' selected' : '') + '>' + _esc(t) + '</option>';
                        }).join('');
                    typeSel.value = current;
                }
                render();
            } catch (err) {
                shell.body.querySelector('[data-role="audit-body"]').innerHTML = _adminError('Could not load audit log: ' + err.message);
            }
        }
        shell.body.innerHTML =
            _adminToolbar(
                '<span class="auth-admin-muted">Ring buffer · newest first · last 200 events</span>' +
                '<span class="auth-admin-muted" style="margin-left:8px;">Visible: <strong id="auth-audit-count">–</strong></span>',
                '<select id="auth-audit-type" style="padding:5px 8px;border-radius:6px;font-size:11px;"><option value="">All event types</option></select>' +
                _adminGhostBtn('auth-audit-refresh', 'Refresh')) +
            '<div class="auth-admin-search"><input type="search" id="auth-audit-search" placeholder="Filter by user, event, or detail…" autocomplete="off" /></div>' +
            '<div data-role="audit-body">' + _adminLoading() + '</div>';
        document.getElementById('auth-audit-refresh').addEventListener('click', refresh);
        document.getElementById('auth-audit-search').addEventListener('input', function () {
            state.filter = this.value.trim(); render();
        });
        document.getElementById('auth-audit-type').addEventListener('change', function () {
            state.typeFilter = this.value; render();
        });
        refresh();
    }

    function _showBroadcastDialog() {
        var html =
            '<div class="auth-admin-note" style="margin-bottom:10px;">Your message appears as a toast for every user currently connected. Max 280 characters.</div>' +
            '<textarea id="auth-bc-msg" maxlength="280" rows="4" style="width:100%;box-sizing:border-box;padding:8px;border-radius:8px;font-family:inherit;resize:vertical;"></textarea>' +
            '<div style="display:flex;gap:8px;align-items:center;margin-top:8px;font-size:11px;">' +
                '<div class="auth-admin-muted" id="auth-bc-char">0 / 280</div>' +
            '</div>' +
            '<div style="display:flex;gap:12px;align-items:center;margin-top:10px;flex-wrap:wrap;">' +
                '<label class="auth-admin-label" style="display:flex;flex-direction:column;gap:3px;">Level' +
                    '<select id="auth-bc-level" style="padding:6px;border-radius:6px;font-size:12px;">' +
                        '<option value="info">info</option><option value="success">success</option><option value="warn">warn</option><option value="error">error</option>' +
                    '</select>' +
                '</label>' +
                '<label class="auth-admin-label" style="display:flex;flex-direction:column;gap:3px;">TTL (seconds)' +
                    '<input type="number" id="auth-bc-ttl" value="120" min="5" max="1800" style="width:90px;padding:6px;border-radius:6px;font-size:12px;" />' +
                '</label>' +
            '</div>' +
            '<div style="display:flex;gap:8px;margin-top:14px;">' +
                '<button id="auth-bc-send" class="auth-login-btn" style="flex:1;">Broadcast</button>' +
            '</div>' +
            '<div id="auth-bc-status" class="auth-admin-note" style="margin-top:10px;"></div>' +
            '<div style="margin:16px 0 6px;display:flex;align-items:center;justify-content:space-between;">' +
                '<div class="auth-admin-label">Currently live broadcasts</div>' +
                '<button type="button" class="auth-admin-ghost" id="auth-bc-refresh">Refresh</button>' +
            '</div>' +
            '<div data-role="bc-live" class="auth-admin-muted" style="padding:6px 0;">' + _adminLoading() + '</div>';
        var shell = _openDialogShell('Broadcast Announcement', html, { id: 'auth-broadcast-dialog' });
        async function refreshLive() {
            var liveEl = shell.body.querySelector('[data-role="bc-live"]');
            if (liveEl) liveEl.innerHTML = _adminLoading('Checking…');
            try {
                var resp = await authFetch('/api/admin/announcements');
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                var data = await resp.json();
                var items = data.announcements || [];
                if (!items.length) {
                    liveEl.innerHTML = '<div class="auth-admin-muted" style="padding:8px 2px;">No broadcasts currently active.</div>';
                    return;
                }
                liveEl.innerHTML = items.map(function (a) {
                    var sent = new Date((a.ts || 0) * 1000).toLocaleTimeString();
                    var ttl = Math.max(0, Math.round((a.expires_at - (Date.now() / 1000)) || 0));
                    return '<div style="display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:8px;background:rgba(255,255,255,0.03);margin-bottom:6px;">' +
                        '<div style="flex:1;min-width:0;">' +
                            '<div style="font-weight:600;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + _esc(a.message) + '</div>' +
                            '<div class="auth-admin-muted" style="font-size:10.5px;margin-top:2px;">' + _esc(a.level) + ' · by @' + _esc(a.sender || '?') + ' · sent ' + _esc(sent) + ' · ~' + ttl + 's left</div>' +
                        '</div>' +
                    '</div>';
                }).join('');
            } catch (err) {
                liveEl.innerHTML = _adminError('Live feed unavailable: ' + err.message);
            }
        }
        var ta = document.getElementById('auth-bc-msg');
        var charEl = document.getElementById('auth-bc-char');
        ta.addEventListener('input', function () { charEl.textContent = ta.value.length + ' / 280'; });
        document.getElementById('auth-bc-refresh').addEventListener('click', refreshLive);
        document.getElementById('auth-bc-send').addEventListener('click', async function () {
            var msg = ta.value.trim();
            if (!msg) return;
            var level = document.getElementById('auth-bc-level').value;
            var ttl = parseInt(document.getElementById('auth-bc-ttl').value, 10) || 120;
            document.getElementById('auth-bc-status').textContent = 'Sending…';
            try {
                var resp = await authFetch('/api/admin/broadcast', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: msg, level: level, ttl_sec: ttl })
                });
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                document.getElementById('auth-bc-status').innerHTML = '<span class="auth-admin-status-ok">Broadcast sent.</span>';
                ta.value = ''; charEl.textContent = '0 / 280';
                refreshLive();
            } catch (err) {
                document.getElementById('auth-bc-status').innerHTML = '<span class="auth-admin-status-err">Failed: ' + _esc(err.message) + '</span>';
            }
        });
        refreshLive();
    }

    async function _showFeatureFlagsDialog() {
        var shell = _openDialogShell('Feature Flags', '', { id: 'auth-flags-dialog', width: '560px' });
        var lastData = null;
        async function refresh() {
            var body = shell.body.querySelector('[data-role="flags-body"]');
            if (body) body.innerHTML = _adminLoading('Loading…');
            try {
                var resp = await authFetch('/api/admin/feature-flags');
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                var data = await resp.json();
                lastData = data;
                var keys = Object.keys(data.flags || {});
                if (!keys.length) {
                    body.innerHTML = '<div class="auth-admin-muted" style="padding:12px 4px;">No feature flags registered.</div>';
                    return;
                }
                var rows = keys.map(function (k) {
                    var v = !!data.flags[k];
                    var def = !!(data.defaults || {})[k];
                    var defChip = def ? '<span class="auth-admin-status-ok">default on</span>' : '<span class="auth-admin-muted">default off</span>';
                    var diverged = v !== def ? '<span class="auth-admin-status-warn" style="margin-left:6px;">modified</span>' : '';
                    return '<label style="display:flex;align-items:center;justify-content:space-between;padding:10px 12px;border-radius:8px;background:rgba(255,255,255,0.03);margin-bottom:6px;gap:10px;">' +
                        '<div style="flex:1;min-width:0;"><div style="font-weight:600;font-size:12px;">' + _esc(k) + '</div><div style="font-size:11px;margin-top:2px;">' + defChip + diverged + '</div></div>' +
                        '<input type="checkbox" data-flag="' + _esc(k) + '" data-default="' + (def ? '1' : '0') + '" ' + (v ? 'checked' : '') + ' style="transform:scale(1.2);" />' +
                    '</label>';
                }).join('');
                body.innerHTML = rows +
                    '<div style="display:flex;gap:8px;margin-top:12px;">' +
                        '<button id="auth-flags-save" class="auth-login-btn" style="flex:1;">Save changes</button>' +
                        '<button type="button" class="auth-admin-ghost" id="auth-flags-reset" style="padding:10px 14px;font-size:12px;">Reset all to defaults</button>' +
                    '</div>' +
                    '<div id="auth-flags-status" class="auth-admin-note" style="margin-top:10px;"></div>';
                document.getElementById('auth-flags-save').addEventListener('click', saveFlags);
                document.getElementById('auth-flags-reset').addEventListener('click', function () {
                    shell.body.querySelectorAll('input[data-flag]').forEach(function (el) {
                        el.checked = el.getAttribute('data-default') === '1';
                    });
                    document.getElementById('auth-flags-status').innerHTML = '<span class="auth-admin-muted">All toggles reset to defaults (not yet saved).</span>';
                });
            } catch (err) {
                shell.body.querySelector('[data-role="flags-body"]').innerHTML = _adminError('Could not load flags: ' + err.message);
            }
        }
        async function saveFlags() {
            var out = {};
            shell.body.querySelectorAll('input[data-flag]').forEach(function (el) { out[el.getAttribute('data-flag')] = el.checked; });
            document.getElementById('auth-flags-status').innerHTML = '<span class="auth-admin-muted">Saving…</span>';
            try {
                var r = await authFetch('/api/admin/feature-flags', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ flags: out })
                });
                if (!r.ok) throw new Error('HTTP ' + r.status);
                document.getElementById('auth-flags-status').innerHTML = '<span class="auth-admin-status-ok">Saved.</span> <span class="auth-admin-muted">Reload the app for clients to pick up the change.</span>';
            } catch (err) {
                document.getElementById('auth-flags-status').innerHTML = '<span class="auth-admin-status-err">Failed: ' + _esc(err.message) + '</span>';
            }
        }
        shell.body.innerHTML =
            _adminToolbar(
                '<span class="auth-admin-muted">Applies deployment-wide on next page load</span>',
                _adminGhostBtn('auth-flags-refresh', 'Refresh')) +
            '<div data-role="flags-body">' + _adminLoading() + '</div>';
        document.getElementById('auth-flags-refresh').addEventListener('click', refresh);
        refresh();
    }

    async function _triggerReloadKnowledge() {
        var shell = _openDialogShell('Reload AI Knowledge', '', { id: 'auth-reload-dialog', width: '520px' });
        async function doReload() {
            var body = shell.body.querySelector('[data-role="reload-body"]');
            body.innerHTML = _adminLoading('Reloading…');
            try {
                var resp = await authFetch('/api/admin/reload-knowledge', { method: 'POST' });
                var data = await resp.json();
                if (resp.ok && data.ok) {
                    var detail = data.reloaded_via || 'ok';
                    var rows = [
                        ['Reload hook', '<code>' + _esc(data.reloaded_via || 'unknown') + '</code>'],
                        ['Knowledge size', '<code>' + _esc(data.length || data.size || '–') + ' chars</code>'],
                    ];
                    if (data.path) rows.push(['Source path', '<code>' + _esc(data.path) + '</code>']);
                    if (data.mtime) rows.push(['Last modified', '<code>' + _esc(new Date(data.mtime * 1000).toLocaleString()) + '</code>']);
                    body.innerHTML =
                        '<div class="auth-admin-status-ok" style="font-size:13px;margin-bottom:12px;">● Knowledge digest reloaded.</div>' +
                        '<div style="display:grid;grid-template-columns:auto 1fr;gap:6px 14px;font-size:12px;margin-bottom:10px;align-items:center;">' +
                            rows.map(function (p) { return '<div class="auth-admin-label">' + _esc(p[0]) + '</div><div>' + p[1] + '</div>'; }).join('') +
                        '</div>' +
                        '<div class="auth-admin-note">Next AI request will use the refreshed digest. No per-user configs were touched.</div>';
                    if (typeof _toastOrAlert === 'function') _toastOrAlert('AI knowledge reloaded (' + detail + ').', 'success');
                } else {
                    body.innerHTML = _adminError('Reload failed: ' + (data.error || 'HTTP ' + resp.status));
                }
            } catch (err) {
                body.innerHTML = _adminError('Reload failed: ' + err.message);
            }
        }
        shell.body.innerHTML =
            _adminToolbar(
                '<span class="auth-admin-muted">Hot-reloads <code>ai/knowledge.md</code> without a restart</span>',
                _adminGhostBtn('auth-reload-again', 'Reload now')) +
            '<div data-role="reload-body">' + _adminLoading('Reloading…') + '</div>';
        document.getElementById('auth-reload-again').addEventListener('click', doReload);
        doReload();
    }

    async function _triggerReloadBlueprints() {
        var shell = _openDialogShell('Reload AI Blueprints', '', { id: 'auth-reload-bp-dialog', width: '560px' });
        async function doReload() {
            var body = shell.body.querySelector('[data-role="reload-bp-body"]');
            body.innerHTML = _adminLoading('Reloading blueprint library…');
            try {
                var resp = await authFetch('/api/admin/reload-blueprints', { method: 'POST' });
                var data = await resp.json();
                if (resp.ok && data.ok) {
                    var rows = [
                        ['Blueprints loaded', '<code>' + _esc(data.count != null ? data.count : '–') + '</code>'],
                    ];
                    if (data.path) rows.push(['Repo path', '<code>' + _esc(data.path) + '</code>']);
                    if (data.user_path) rows.push(['Your overrides', '<code>' + _esc(data.user_path) + '</code>']);
                    if (Array.isArray(data.protocols) && data.protocols.length) {
                        rows.push(['Protocols', '<code>' + _esc(data.protocols.join(', ')) + '</code>']);
                    }
                    body.innerHTML =
                        '<div class="auth-admin-status-ok" style="font-size:13px;margin-bottom:12px;">● Blueprint library reloaded.</div>' +
                        '<div style="display:grid;grid-template-columns:auto 1fr;gap:6px 14px;font-size:12px;margin-bottom:10px;align-items:center;">' +
                            rows.map(function (p) { return '<div class="auth-admin-label">' + _esc(p[0]) + '</div><div>' + p[1] + '</div>'; }).join('') +
                        '</div>' +
                        '<div class="auth-admin-note">The AI <code>list_blueprints</code> / <code>load_blueprint</code> tools will see the fresh library on the next turn. Per-user override dir is <code>~/.topology_users/&lt;user&gt;/ai_blueprints/</code>.</div>';
                    if (typeof _toastOrAlert === 'function') _toastOrAlert('Blueprints reloaded (' + (data.count || 0) + ').', 'success');
                } else {
                    body.innerHTML = _adminError('Reload failed: ' + (data.error || 'HTTP ' + resp.status));
                }
            } catch (err) {
                body.innerHTML = _adminError('Reload failed: ' + err.message);
            }
        }
        shell.body.innerHTML =
            _adminToolbar(
                '<span class="auth-admin-muted">Hot-reloads <code>ai/blueprints/*.json</code> without a restart</span>',
                _adminGhostBtn('auth-reload-bp-again', 'Reload now')) +
            '<div data-role="reload-bp-body">' + _adminLoading('Reloading blueprint library…') + '</div>';
        document.getElementById('auth-reload-bp-again').addEventListener('click', doReload);
        doReload();
    }

    // View-as dialog. Originally "cosmetic-only" (just swapped the pill
    // avatar/name). 2026-04-22: extended to also browse the target
    // user's real workspace (domains + saved topologies) via the new
    // owner-only `/api/owner/view-as/<user>/...` endpoints. Two entry
    // actions per user:
    //   1. "Browse workspace" (real view -- loads the target's data)
    //   2. "Cosmetic preview" (cheap UI swap, API calls still run as
    //      the owner)
    // Both are clearly labelled so the owner knows what's about to
    // happen before they click.
    var _viewAsState = { users: [], filter: '', selected: null, selectedUser: null, domains: [], activeDomain: null, topologies: [] };

    async function _showImpersonateDialog() {
        _viewAsState = { users: [], filter: '', selected: null, selectedUser: null, domains: [], activeDomain: null, topologies: [] };
        var shell = _openDialogShell('View as another user', '', { id: 'auth-imp-dialog', width: '820px' });
        shell.body.innerHTML =
            '<div class="auth-admin-note" style="margin-bottom:10px;">Pick a user on the left. <strong>Browse workspace</strong> loads their real domains + topologies on the canvas in view-only mode. <strong>Cosmetic preview</strong> just flips the pill avatar so you can see what a teammate\'s UI looks like while still acting as yourself.</div>' +
            '<div class="auth-viewas-layout">' +
                '<div class="auth-viewas-pane">' +
                    '<div class="auth-viewas-pane-head">Users</div>' +
                    '<div style="padding:8px;"><div class="auth-admin-search" style="margin:0;"><input type="search" id="auth-imp-search" placeholder="Search users…" autocomplete="off" /><span class="auth-admin-search-count" id="auth-imp-count">0</span></div></div>' +
                    '<div class="auth-viewas-pane-body" id="auth-imp-users"></div>' +
                '</div>' +
                '<div class="auth-viewas-pane" style="display:flex;flex-direction:column;">' +
                    '<div class="auth-viewas-pane-head" id="auth-imp-right-head">Workspace</div>' +
                    '<div class="auth-viewas-pane-body" id="auth-imp-right">' +
                        '<div class="auth-viewas-empty">Select a user to browse their workspace.</div>' +
                    '</div>' +
                '</div>' +
            '</div>';

        document.getElementById('auth-imp-search').addEventListener('input', function () {
            _viewAsState.filter = this.value.trim().toLowerCase();
            _renderViewAsUsers();
        });

        try {
            var resp = await authFetch('/api/auth/users');
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            var data = await resp.json();
            _viewAsState.users = (data.users || []).filter(function (u) { return u.username !== (_currentUser && _currentUser.username); });
            _renderViewAsUsers();
        } catch (err) {
            document.getElementById('auth-imp-users').innerHTML = _adminError('Could not load users: ' + err.message);
        }
    }

    function _renderViewAsUsers() {
        var container = document.getElementById('auth-imp-users');
        if (!container) return;
        var q = _viewAsState.filter || '';
        var users = _viewAsState.users.filter(function (u) {
            if (!q) return true;
            var hay = ((u.display_name || '') + ' ' + (u.username || '') + ' ' + (u.email || '') + ' ' + (u.role || '')).toLowerCase();
            return hay.indexOf(q) >= 0;
        });
        document.getElementById('auth-imp-count').textContent = users.length + '/' + _viewAsState.users.length;
        if (!users.length) {
            container.innerHTML = '<div class="auth-viewas-empty">No matches.</div>';
            return;
        }
        container.innerHTML = users.map(function (u) {
            var active = _viewAsState.selected === u.username ? ' is-active' : '';
            return '<div class="auth-viewas-item' + active + '" data-username="' + _esc(u.username) + '">' +
                '<div style="width:28px;height:28px;border-radius:50%;overflow:hidden;flex:none;">' + (window.CloudAvatar ? window.CloudAvatar.svg(u.username, 28) : '') + '</div>' +
                '<div style="flex:1;min-width:0;">' +
                    '<div class="auth-viewas-item-name">' + _esc(u.display_name || u.username) + '</div>' +
                    '<div class="auth-viewas-item-sub">@' + _esc(u.username) + ' · ' + _esc(u.role) + '</div>' +
                '</div>' +
            '</div>';
        }).join('');
        container.querySelectorAll('.auth-viewas-item').forEach(function (row) {
            row.addEventListener('click', function () {
                var un = row.getAttribute('data-username');
                var u = _viewAsState.users.find(function (x) { return x.username === un; });
                if (u) _onSelectViewAsUser(u);
            });
        });
    }

    async function _onSelectViewAsUser(u) {
        _viewAsState.selected = u.username;
        _viewAsState.selectedUser = u;
        _viewAsState.domains = [];
        _viewAsState.activeDomain = null;
        _viewAsState.topologies = [];
        _renderViewAsUsers();
        var right = document.getElementById('auth-imp-right');
        document.getElementById('auth-imp-right-head').textContent = u.display_name + ' (@' + u.username + ')';
        right.innerHTML = _adminLoading('Loading ' + u.display_name + '\'s workspace…');
        try {
            var [sumResp, domResp] = await Promise.all([
                authFetch('/api/owner/view-as/' + encodeURIComponent(u.username) + '/summary'),
                authFetch('/api/owner/view-as/' + encodeURIComponent(u.username) + '/domains'),
            ]);
            if (!sumResp.ok) throw new Error('summary ' + sumResp.status);
            if (!domResp.ok) throw new Error('domains ' + domResp.status);
            var sum = await sumResp.json();
            var doms = await domResp.json();
            _viewAsState.domains = doms.domains || [];
            _viewAsState.activeDomain = _viewAsState.domains[0] || null;
            _renderViewAsWorkspace(sum);
            if (_viewAsState.activeDomain) _loadViewAsTopologies(_viewAsState.activeDomain.id);
        } catch (err) {
            right.innerHTML = _adminError('Could not load workspace: ' + err.message);
        }
    }

    function _renderViewAsWorkspace(sum) {
        var u = _viewAsState.selectedUser;
        if (!u) return;
        var right = document.getElementById('auth-imp-right');
        var target = (sum && sum.target) || {};
        var created = target.created_at ? new Date(target.created_at).toLocaleDateString() : '—';
        var lastLogin = target.last_login ? new Date(target.last_login).toLocaleString() : 'never';
        var domRows = _viewAsState.domains.length
            ? _viewAsState.domains.map(function (d) {
                var active = (_viewAsState.activeDomain && _viewAsState.activeDomain.id === d.id) ? ' is-active' : '';
                var builtIn = d.is_built_in ? ' <span class="auth-admin-muted" style="font-size:10px;">(built-in)</span>' : '';
                return '<div class="auth-viewas-item' + active + '" data-domain-id="' + _esc(d.id) + '">' +
                    '<div style="flex:1;min-width:0;"><div class="auth-viewas-item-name">' + _esc(d.name) + builtIn + '</div>' +
                    '<div class="auth-viewas-item-sub">' + (d.topology_count || 0) + ' file' + ((d.topology_count || 0) === 1 ? '' : 's') + '</div></div>' +
                '</div>';
            }).join('')
            : '<div class="auth-viewas-empty">No domains.</div>';
        right.innerHTML =
            '<div style="display:flex;gap:14px;align-items:center;margin-bottom:10px;padding:10px 12px;border-radius:10px;background:rgba(255,255,255,0.03);">' +
                '<div style="width:48px;height:48px;border-radius:50%;overflow:hidden;flex:none;">' + (window.CloudAvatar ? window.CloudAvatar.svg(u.username, 48) : '') + '</div>' +
                '<div style="flex:1;min-width:0;">' +
                    '<div style="font-weight:700;font-size:14px;">' + _esc(target.display_name || u.display_name) + '</div>' +
                    '<div class="auth-admin-muted" style="font-size:11.5px;">' + _esc(target.role || u.role) + ' · joined ' + _esc(created) + ' · last seen ' + _esc(lastLogin) + '</div>' +
                    '<div class="auth-admin-muted" style="font-size:11.5px;margin-top:2px;">' + (sum.domain_count || 0) + ' domain' + ((sum.domain_count || 0) === 1 ? '' : 's') + ' · ' + (sum.topology_count || 0) + ' topology file' + ((sum.topology_count || 0) === 1 ? '' : 's') + '</div>' +
                '</div>' +
                '<div style="display:flex;gap:6px;flex:none;">' +
                    '<button type="button" class="auth-admin-ghost" id="auth-imp-cosmetic" title="Swap just the pill avatar/name">Cosmetic preview</button>' +
                '</div>' +
            '</div>' +
            '<div style="display:grid;grid-template-columns:180px 1fr;gap:10px;">' +
                '<div class="auth-viewas-pane" style="min-height:240px;">' +
                    '<div class="auth-viewas-pane-head">Domains</div>' +
                    '<div class="auth-viewas-pane-body" id="auth-imp-domains">' + domRows + '</div>' +
                '</div>' +
                '<div class="auth-viewas-pane" style="min-height:240px;">' +
                    '<div class="auth-viewas-pane-head" id="auth-imp-topos-head">Topologies</div>' +
                    '<div class="auth-viewas-pane-body" id="auth-imp-topos"><div class="auth-viewas-empty">Pick a domain.</div></div>' +
                '</div>' +
            '</div>';
        document.getElementById('auth-imp-cosmetic').addEventListener('click', function () {
            _applyCosmeticImpersonation(u);
        });
        document.querySelectorAll('#auth-imp-domains .auth-viewas-item').forEach(function (row) {
            row.addEventListener('click', function () {
                var did = row.getAttribute('data-domain-id');
                _viewAsState.activeDomain = _viewAsState.domains.find(function (d) { return d.id === did; }) || null;
                document.querySelectorAll('#auth-imp-domains .auth-viewas-item').forEach(function (r) { r.classList.toggle('is-active', r === row); });
                _loadViewAsTopologies(did);
            });
        });
    }

    async function _loadViewAsTopologies(domainId) {
        var u = _viewAsState.selectedUser;
        if (!u) return;
        var listEl = document.getElementById('auth-imp-topos');
        if (listEl) listEl.innerHTML = _adminLoading('Loading topologies…');
        var head = document.getElementById('auth-imp-topos-head');
        var d = _viewAsState.activeDomain;
        if (head && d) head.textContent = 'Topologies · ' + d.name;
        try {
            var resp = await authFetch('/api/owner/view-as/' + encodeURIComponent(u.username) + '/domains/' + encodeURIComponent(domainId) + '/topologies');
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            var data = await resp.json();
            _viewAsState.topologies = data.topologies || [];
            if (!_viewAsState.topologies.length) {
                listEl.innerHTML = '<div class="auth-viewas-empty">This domain has no saved topologies.</div>';
                return;
            }
            listEl.innerHTML = _viewAsState.topologies.map(function (t) {
                var updated = t.updated_at ? new Date(t.updated_at).toLocaleString() : '—';
                return '<div class="auth-viewas-topo-row">' +
                    '<div class="meta"><div class="name">' + _esc(t.name) + '</div>' +
                        '<div class="sub">' + (t.device_count || 0) + ' devices · ' + (t.link_count || 0) + ' links · updated ' + _esc(updated) + '</div></div>' +
                    '<button type="button" class="auth-admin-ghost" data-topo-id="' + _esc(t.id) + '" data-topo-name="' + _esc(t.name) + '">Load (view-only)</button>' +
                '</div>';
            }).join('');
            listEl.querySelectorAll('button[data-topo-id]').forEach(function (b) {
                b.addEventListener('click', function () {
                    _loadViewAsTopologyOnCanvas(b.getAttribute('data-topo-id'), b.getAttribute('data-topo-name'));
                });
            });
        } catch (err) {
            listEl.innerHTML = _adminError('Could not load topologies: ' + err.message);
        }
    }

    async function _loadViewAsTopologyOnCanvas(topoId, topoName) {
        var u = _viewAsState.selectedUser;
        var d = _viewAsState.activeDomain;
        if (!u || !d) return;
        try {
            var resp = await authFetch('/api/owner/view-as/' + encodeURIComponent(u.username) + '/domains/' + encodeURIComponent(d.id) + '/topologies/' + encodeURIComponent(topoId));
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            var payload = await resp.json();
            var data = payload.data || payload;
            var editor = window.editor || window.__editor;
            if (editor && typeof editor.loadTopologyFromData === 'function') {
                editor.loadTopologyFromData(data, { domain: d.name + ' · @' + u.username + ' (view-only)' });
            } else {
                _toastOrAlert('Canvas editor unavailable; topology loaded but not rendered.', 'warn');
            }
            _showViewAsBanner(u, d, topoName);
            var shell = document.getElementById('auth-imp-dialog');
            if (shell) shell.remove();
            _toastOrAlert('Loaded "' + topoName + '" from @' + u.username + ' in view-only mode.', 'success');
        } catch (err) {
            _toastOrAlert('Could not load topology: ' + err.message, 'error');
        }
    }

    function _showViewAsBanner(u, domain, topoName) {
        var existing = document.getElementById('auth-viewas-banner');
        if (existing) existing.remove();
        var b = document.createElement('div');
        b.id = 'auth-viewas-banner';
        b.className = 'auth-viewas-banner';
        b.innerHTML =
            'Viewing <strong>' + _esc(topoName) + '</strong> from <strong>@' + _esc(u.username) + '</strong> <span style="opacity:0.75;">· ' + _esc(domain.name) + '</span>' +
            '<button type="button" id="auth-viewas-exit">Exit view-only</button>';
        document.body.appendChild(b);
        document.getElementById('auth-viewas-exit').addEventListener('click', function () {
            b.remove();
            var editor = window.editor || window.__editor;
            if (editor && typeof editor.newTopology === 'function') {
                try { editor.newTopology(); } catch (_) {}
            }
            _toastOrAlert('Exited view-only. Canvas cleared.', 'info');
        });
    }

    function _applyCosmeticImpersonation(u) {
        if (!window.__ownerOriginalUser) window.__ownerOriginalUser = Object.assign({}, _currentUser);
        _currentUser = Object.assign({}, _currentUser, {
            username: u.username,
            display_name: u.display_name,
            role: u.role,
            is_admin: u.role === 'admin',
            is_owner: false,
            _impersonation: true,
        });
        _updateUserMenu();
        var shell = document.getElementById('auth-imp-dialog');
        if (shell) shell.remove();
        _showImpersonationBanner();
    }

    function _showImpersonationBanner() {
        var existing = document.getElementById('auth-imp-banner');
        if (existing) existing.remove();
        var b = document.createElement('div');
        b.id = 'auth-imp-banner';
        b.style.cssText = 'position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:linear-gradient(135deg,rgba(253,224,71,0.95),rgba(234,179,8,0.9));color:#3b2a00;padding:10px 18px;border-radius:999px;font-size:12px;font-weight:700;z-index:999999;box-shadow:0 10px 30px rgba(234,179,8,0.35);display:flex;align-items:center;gap:12px;';
        b.innerHTML =
            'Viewing as <strong>' + _esc(_currentUser.display_name) + '</strong>' +
            '<button id="auth-imp-exit" style="background:rgba(0,0,0,0.2);color:#fff;border:none;padding:4px 12px;border-radius:999px;font-size:11px;font-weight:700;cursor:pointer;">Exit view-as</button>';
        document.body.appendChild(b);
        document.getElementById('auth-imp-exit').addEventListener('click', function () {
            if (window.__ownerOriginalUser) {
                _currentUser = window.__ownerOriginalUser;
                window.__ownerOriginalUser = null;
            }
            b.remove();
            _updateUserMenu();
        });
    }

    function _showResetConfigsConfirm() {
        var shell = _openDialogShell('Reset All AI Configs',
            '<div style="background:rgba(231,76,60,0.12);border:1px solid rgba(231,76,60,0.3);border-radius:10px;padding:12px;font-size:12px;color:#fecaca;margin-bottom:12px;">' +
                '<div style="font-weight:700;margin-bottom:6px;">This deletes every user\'s ai_config.json and jira.json.</div>' +
                'Topologies, sections, domains, and credentials are <strong>NOT</strong> touched. Users will fall back to the default AI (Gemini if the shared key is set).' +
            '</div>' +
            '<div class="auth-admin-label" style="margin-bottom:4px;">Will affect</div>' +
            '<div id="auth-reset-preview" class="auth-admin-muted" style="font-size:11.5px;padding:8px 12px;border-radius:8px;background:rgba(255,255,255,0.03);margin-bottom:12px;">' + _adminLoading('Scanning users…') + '</div>' +
            '<div class="auth-admin-note" style="margin-bottom:8px;">Type <code>RESET</code> to confirm:</div>' +
            '<input type="text" id="auth-reset-confirm" autocomplete="off" style="width:100%;padding:8px;border-radius:8px;box-sizing:border-box;" />' +
            '<div style="display:flex;gap:8px;margin-top:12px;">' +
                '<button id="auth-reset-go" class="auth-login-btn" style="flex:1;background:linear-gradient(135deg,#ef4444,#b91c1c);border-color:rgba(239,68,68,0.6);">Confirm Reset</button>' +
            '</div>' +
            '<div id="auth-reset-status" class="auth-admin-note" style="margin-top:10px;"></div>',
            { id: 'auth-reset-dialog' });
        (async function () {
            try {
                var resp = await authFetch('/api/admin/shared-key-status');
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                var data = await resp.json();
                var n = data.per_user_configs_count || 0;
                var el = document.getElementById('auth-reset-preview');
                if (el) el.innerHTML = 'Approximately <strong>' + n + '</strong> user' + (n === 1 ? '' : 's') + ' currently have a saved AI or Jira config that will be deleted.';
            } catch (err) {
                var elEr = document.getElementById('auth-reset-preview');
                if (elEr) elEr.innerHTML = _adminError('Preview unavailable: ' + err.message);
            }
        })();
        document.getElementById('auth-reset-go').addEventListener('click', async function () {
            var confirm = document.getElementById('auth-reset-confirm').value.trim();
            var statusEl = document.getElementById('auth-reset-status');
            statusEl.innerHTML = '<span class="auth-admin-muted">Resetting…</span>';
            try {
                var resp = await authFetch('/api/owner/reset-configs', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ confirm: confirm })
                });
                var data = await resp.json();
                if (!resp.ok) {
                    statusEl.innerHTML = '<span class="auth-admin-status-err">Failed: ' + _esc(data.error || ('HTTP ' + resp.status)) + '</span>';
                    return;
                }
                statusEl.innerHTML = '<span class="auth-admin-status-ok">Reset complete. Removed ' + (data.count || 0) + ' config file(s).</span>';
                setTimeout(function () { shell.dialog.remove(); }, 1600);
            } catch (err) {
                statusEl.innerHTML = '<span class="auth-admin-status-err">Failed: ' + _esc(err.message) + '</span>';
            }
        });
    }

    async function _showRestartConfirm() {
        var shell = _openDialogShell('Restart Server',
            '<div style="background:rgba(231,76,60,0.12);border:1px solid rgba(231,76,60,0.3);border-radius:10px;padding:12px;font-size:12px;color:#fecaca;margin-bottom:12px;">' +
                'Disconnects every client briefly. Only works when the deployment was started with <code>ALLOW_OWNER_RESTART=1</code> and a process supervisor (systemd / pm2) will bring the server back up.' +
            '</div>' +
            '<div id="auth-restart-preflight" class="auth-admin-note" style="margin-bottom:10px;">' + _adminLoading('Checking supervisor support…') + '</div>' +
            '<div style="display:flex;gap:8px;">' +
                '<button id="auth-restart-go" class="auth-login-btn" style="flex:1;background:linear-gradient(135deg,#ef4444,#b91c1c);border-color:rgba(239,68,68,0.6);">Restart Now</button>' +
            '</div>' +
            '<div id="auth-restart-status" class="auth-admin-note" style="margin-top:10px;"></div>',
            { id: 'auth-restart-dialog' });
        // Preflight check: a plain POST with an unconfirmed body won't
        // actually restart (the endpoint gates on ALLOW_OWNER_RESTART),
        // but we send a HEAD-ish probe via the diagnostics endpoint to
        // surface whether restart is enabled BEFORE the owner clicks.
        // This lets the UI disable the red button up-front.
        var allowed = false;
        try {
            var resp = await authFetch('/api/admin/diagnostics');
            // No direct flag here, but if diagnostics works we can
            // reasonably assume the owner token is valid. The real
            // allow/deny comes from the restart endpoint itself.
            document.getElementById('auth-restart-preflight').innerHTML =
                '<span class="auth-admin-muted">Owner permissions verified. If restart is disabled in the environment you will see a "Blocked" message below.</span>';
            allowed = resp.ok;
        } catch (err) {
            document.getElementById('auth-restart-preflight').innerHTML = _adminError('Preflight failed: ' + err.message);
        }
        document.getElementById('auth-restart-go').addEventListener('click', async function () {
            var statusEl = document.getElementById('auth-restart-status');
            statusEl.innerHTML = '<span class="auth-admin-muted">Requesting restart…</span>';
            try {
                var resp = await authFetch('/api/owner/restart', { method: 'POST' });
                var data = await resp.json();
                if (!resp.ok) {
                    statusEl.innerHTML = '<span class="auth-admin-status-err">Blocked: ' + _esc(data.error || ('HTTP ' + resp.status)) + '</span>' +
                        (data.hint ? '<br><span class="auth-admin-muted">' + _esc(data.hint) + '</span>' : '');
                    return;
                }
                statusEl.innerHTML = '<span class="auth-admin-status-ok">' + _esc(data.message || 'Restart initiated.') + '</span>';
            } catch (err) {
                statusEl.innerHTML = '<span class="auth-admin-status-err">Request failed: ' + _esc(err.message) + '</span>';
            }
        });
    }

    // ----------------------------------------------------------------
    // Announcement polling (every 30s)
    // ----------------------------------------------------------------
    // Every logged-in client long-polls /api/admin/announcements so a
    // broadcast from an admin reaches every tab without a WebSocket.
    // We dedupe by announcement id (kept in-memory) so re-polling
    // doesn't replay old toasts on refresh.
    var _seenAnnouncementIds = {};
    // When the running server is older than the deployed client (e.g. the
    // admin hasn't restarted serve.py after a pull) the announcement
    // endpoint returns 404 on every tick and spams the browser devtools
    // network log. We self-disable on the FIRST 404 and rely on the next
    // full page reload to re-enable polling -- this keeps the console
    // quiet on pre-broadcast-era servers without requiring a client
    // code bump.
    var _announcePolling = { stopped: false };
    async function _pollAnnouncementsOnce() {
        if (_announcePolling.stopped) return;
        try {
            var resp = await authFetch('/api/admin/announcements');
            if (resp.status === 404) {
                _announcePolling.stopped = true;
                if (window.__auth_announcements_stop) {
                    try { window.__auth_announcements_stop(); } catch (_) {}
                }
                return;
            }
            if (!resp.ok) return;
            var data = await resp.json();
            (data.announcements || []).forEach(function (a) {
                if (_seenAnnouncementIds[a.id]) return;
                _seenAnnouncementIds[a.id] = true;
                _toastOrAlert('[' + (a.sender || 'admin') + '] ' + a.message, a.level || 'info');
            });
        } catch (_) { /* ignore */ }
    }
    function _startAnnouncementPolling() {
        if (window.__auth_announcements_started) return;
        window.__auth_announcements_started = true;
        _announcePolling.stopped = false;
        // Prime after 2s so we don't race the initial page paint; then
        // every 30s. Stop ticking when the tab is hidden to be nice to
        // the battery; resume on visibilitychange.
        setTimeout(_pollAnnouncementsOnce, 2000);
        var interval = setInterval(function () {
            if (document.hidden || _announcePolling.stopped) return;
            _pollAnnouncementsOnce();
        }, 30000);
        document.addEventListener('visibilitychange', function () {
            if (!document.hidden && !_announcePolling.stopped) _pollAnnouncementsOnce();
        });
        // Expose a cleanup hook (mostly for tests).
        window.__auth_announcements_stop = function () { clearInterval(interval); window.__auth_announcements_started = false; };
    }

    // Load the signed-in user's avatar prefs and push them into
    // CloudAvatar so every subsequent render (pill, share dialog,
    // impersonation picker) shows the custom face. Silent on any
    // error -- a missing prefs file just means "use the hashed
    // defaults", which is the intended fallback.
    async function _loadMyAvatarPrefs() {
        if (!_currentUser || !window.CloudAvatar || typeof window.CloudAvatar.setOverrides !== 'function') return;
        try {
            var resp = await authFetch('/api/auth/me/profile');
            if (!resp.ok) return;
            var data = await resp.json();
            var avatar = (data && data.avatar) || {};
            if (avatar && (avatar.palette || avatar.face !== undefined || avatar.accessory !== undefined)) {
                window.CloudAvatar.setOverrides(_currentUser.username || _currentUser.display_name || '?', avatar);
                _updateUserMenu();
            }
        } catch (_) { /* silent -- cosmetic overrides only */ }
    }

    // ----------------------------------------------------------------
    // Init -- check stored token on page load
    // ----------------------------------------------------------------
    async function init() {
        var stored = _getStoredToken();
        if (stored) {
            _token = stored;
            try {
                var storedUser = _origLS.get(USER_KEY);
                if (storedUser) {
                    _currentUser = JSON.parse(storedUser);
                    _patchLocalStorage(_currentUser && _currentUser.username);
                }
            } catch { /* ok */ }

            try {
                var resp = await fetch(AUTH_API + '/me', {
                    headers: { 'Authorization': 'Bearer ' + stored }
                });
                if (resp.ok) {
                    var data = await resp.json();
                    // Backend now ships `is_admin` / `is_owner` flags
                    // alongside the classic role so the dropdown can show
                    // the admin-tier / owner-tier items without having to
                    // re-derive ownership on the client.
                    _currentUser = {
                        username: data.username,
                        role: data.role,
                        display_name: data.display_name,
                        is_admin: data.is_admin === true || data.role === 'admin',
                        is_owner: data.is_owner === true
                    };
                    _storeSession(stored, _currentUser);
                    _updateUserMenu();
                    _startAnnouncementPolling();
                    _loadMyAvatarPrefs();
                    return;
                }
            } catch { /* token invalid or server down */ }

            _clearSession();
        }

        // Check if multiuser is even enabled
        try {
            var healthResp = await fetch('/api/health');
            if (healthResp.ok) {
                var health = await healthResp.json();
                if (!health.multiuser) {
                    // Single-user mode: the default user is effectively the
                    // deployment owner. Mirrors the backend behavior in
                    // api/auth/service.py::get_current_user where multiuser
                    // disabled returns is_owner=True. Keeps the
                    // owner-tier menu items (reset-configs / restart /
                    // impersonate) reachable in single-user deployments.
                    _currentUser = {
                        username: 'default',
                        role: 'admin',
                        display_name: 'Default User',
                        is_admin: true,
                        is_owner: true
                    };
                    _updateUserMenu();
                    _startAnnouncementPolling();
                    return;
                }
            }
        } catch { /* can't reach server */ }

        _updateUserMenu();
        showLoginOverlay();
    }

    // ----------------------------------------------------------------
    // Public API
    // ----------------------------------------------------------------
    window.TopologyAuth = {
        init: init,
        authFetch: authFetch,
        login: async function (username, password) {
            var resp = await fetch(AUTH_API + '/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username, password: password })
            });
            if (!resp.ok) return null;
            var data = await resp.json();
            // Note: on a user switch this triggers `window.location.reload()`
            // and never returns. Callers that depend on the return value
            // must run on a fresh page or call this only for first-time
            // sign-in.
            _finishLogin(data);
            return data;
        },
        logout: function () {
            _doExplicitLogout();
        },
        getCurrentUser: function () { return _currentUser; },
        getToken: function () { return _token; },
        isAuthenticated: function () { return !!_token && !!_currentUser; },
        showLoginOverlay: showLoginOverlay,
        hideLoginOverlay: hideLoginOverlay
    };
})();
