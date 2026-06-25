/**
 * topology-bugs.js -- "Create Bug Topology" INLINE connected panel.
 *
 * UX: lives inside the Bugs row of the Topologies dropdown as a compact
 * connected panel (same visual DNA as .domain-share-form). It is NOT a
 * floating modal anymore -- it expands in place under the Bugs row's
 * Save/Load/Share button strip, right where the "+ Bug" pill sits. This
 * keeps the user anchored to the Bugs domain they are creating into and
 * follows the one-panel-at-a-time rule that TopologyShare already
 * enforces for its own inline forms.
 *
 * Flow: user pastes SW-XXXXX, presses Create. Backend fetches the ticket
 * via the user's per-user Jira API token, parses devices/IPs/VRFs out of
 * the description/comments, and synthesizes a /debug-dnos-style topology
 * JSON in the user's built-in __bugs section. The new topology then opens
 * automatically in the canvas.
 *
 * If the user hasn't configured Jira credentials yet, an inline sub-form
 * surfaces below the SW input (base URL + email + API token). Once saved,
 * the SW input becomes active again.
 *
 * Optional "Advanced" details block (labelled "Manual overrides" in
 * older revisions) still lets the user set title/summary/devices
 * manually, which override anything pulled from Jira -- handy for
 * tickets whose description the parser can't chew. The summary label
 * was shortened in the 2026-04-20f simplification pass; the same four
 * inputs (.bug-title, .bug-summary, .bug-devices, .bug-force-placeholder)
 * are still inside.
 *
 * Mutual exclusion: opening the bug panel closes any open share inline
 * form (via TopologyShare.closeDialog). Opening a share form likewise
 * closes the bug panel (topology-share.js hook). Only one inline panel
 * may be open in the Topologies dropdown at a time.
 *
 * Multi-user: all persistence (Jira creds, bug topologies, sections)
 * goes through JWT-gated per-user paths owned by topology/api/auth/
 * user_store.py. This module never reads/writes global state -- that is
 * now a hard rule for every new feature (see DEVELOPMENT_GUIDELINES.md
 * "Multi-user is the default" section).
 *
 * Dependencies:
 *   - window.TopologyAuth.authFetch (auth-bearing fetch)
 *   - window.topologyEditor (aliased via _editor() for forward-compat)
 *     -- loadTopologyFromData / showToast (canvas + UX)
 *   - window.TopologyShare.closeDialog (mutual exclusion, optional)
 *   - The legacy /api/sections backend (the __bugs section is auto
 *     injected for every authenticated user; see serve.py
 *     BUILTIN_SECTIONS).
 *
 * Regression note (2026-04-21): earlier revisions referenced
 * `window.editor` which is never set -- topology.js only publishes
 * `window.topologyEditor`. That silently broke "open-after-create":
 * the canvas kept the previous topology's objects and only
 * refreshed after the user manually navigated the topologies
 * dropdown. _editor() now resolves both names for safety.
 */
(function () {
    'use strict';

    // Element id of the inline host. Kept identical to the legacy dialog id
    // so every .querySelector('.bug-*') selector inside the existing handlers
    // continues to work without a rewrite -- the HOST moved from body-level
    // overlay to the Bugs row's .domain-body, but the id is still unique
    // per page because only one inline panel can be open at a time.
    var DIALOG_ID = 'bug-topology-dialog';
    var _jiraConfigured = null; // null = unknown, true/false once probed

    function _authFetch(url, opts) {
        if (window.TopologyAuth && window.TopologyAuth.authFetch) {
            return window.TopologyAuth.authFetch(url, opts);
        }
        return fetch(url, opts);
    }

    // The canvas editor is exposed as `window.topologyEditor` by
    // topology.js -- there is NO `window.editor`. Earlier revisions of
    // this file referenced `window.editor` which was always `undefined`,
    // so `_openCreatedTopology` silently no-op'd: the canvas kept the
    // previous topology's objects until the user manually switched
    // topologies twice in the dropdown (which used the legacy load path
    // via `window.topologyEditor`). Always resolve both names so future
    // renames don't reintroduce the regression.
    function _editor() {
        return window.topologyEditor || window.editor || null;
    }

    function _toast(msg, type) {
        var ed = _editor();
        if (ed && typeof ed.showToast === 'function') {
            ed.showToast(msg, type || 'info');
        } else if (type === 'error') {
            console.error(msg);
        } else {
            console.log(msg);
        }
    }

    function _normalizeSwId(raw) {
        if (!raw) return '';
        var r = String(raw).trim().toUpperCase().replace(/\s+/g, '');
        var m = r.match(/^(SW|BUG|DPI|FR|EPM)-?(\d+)$/);
        if (!m) return '';
        return m[1] + '-' + m[2];
    }

    // --------------------------------------------------------------
    //   Inline host mounting (mirrors TopologyShare's pattern)
    // --------------------------------------------------------------
    //
    // The panel renders inside the Bugs row's .domain-body as a
    // .domain-bug-form element. The Bugs row is resolved by walking up
    // from the anchor (the "+ Bug" pill) via closest, then falling back
    // to a lookup by the "__bugs" section id if the anchor isn't in the
    // DOM anymore (e.g. the dropdown was re-rendered while the panel
    // was open). Only one host may exist at a time.

    function _getTopologiesDropdown() {
        return document.getElementById('topologies-dropdown-menu');
    }

    function _findBugsRow(anchorEl) {
        if (anchorEl && anchorEl.closest) {
            var row = anchorEl.closest('.custom-section-category');
            if (row) return row;
        }
        var dd = _getTopologiesDropdown();
        if (!dd) return null;
        // The Bugs builtin domain is always section id "__bugs".
        return dd.querySelector('.custom-section-category[data-section-id="__bugs"]');
    }

    function _expandDomainBody(row) {
        if (!row) return;
        var body = row.querySelector(':scope > .domain-body');
        if (body && body.style.display === 'none') {
            body.style.display = 'block';
            var chev = row.querySelector('.domain-chevron');
            if (chev) chev.style.transform = 'rotate(0deg)';
            try {
                var editor = window.topologyEditor;
                if (editor && editor._domainCollapsed) {
                    var sid = row.dataset.sectionId;
                    if (sid) editor._domainCollapsed[sid] = false;
                }
            } catch (_) { /* best-effort */ }
        }
    }

    function _removeExistingHost() {
        var old = document.getElementById(DIALOG_ID);
        if (old && old.parentNode) old.parentNode.removeChild(old);
    }

    // Build a fresh .domain-bug-form inside row's .domain-body, positioned
    // immediately BEFORE the domain-topos-list so it reads as a child of
    // the Bugs row (and sits below the Save/Load/Share strip + any share
    // form that might already be mounted above it -- share cleans itself
    // up on mutual-exclusion so this is defensive only).
    function _ensureInlineHost(row) {
        _removeExistingHost();
        if (!row) return null;
        var body = row.querySelector(':scope > .domain-body');
        if (!body) return null;

        var host = document.createElement('div');
        host.id = DIALOG_ID;
        host.className = 'domain-bug-form';
        host.setAttribute('role', 'dialog');
        host.setAttribute('aria-label', 'Create bug topology');
        host.style.display = 'none';
        host.innerHTML = _renderInlineHTML();

        var toposList = body.querySelector(':scope > .domain-topos-list');
        if (toposList) body.insertBefore(host, toposList);
        else body.appendChild(host);

        _wireEvents(host);
        return host;
    }

    // The body HTML is almost identical to the previous dialog body but
    // wrapped in the shared .dsf-head + .dsf-body skeleton so it inherits
    // all the visual treatment that .domain-share-form already has. Every
    // .bug-* class below is the same as before so the existing querySelector
    // code paths (probeJiraConfig, saveJiraConfig, submit, etc.) keep working.
    function _renderInlineHTML() {
        return ''
            + '<div class="dsf-head">'
            +   '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            +     '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>'
            +   '</svg>'
            +   '<span class="dsf-title">Create bug topology</span>'
            +   '<button type="button" class="dsf-close" aria-label="Close create-bug panel">&times;</button>'
            + '</div>'
            + '<div class="dsf-body bug-topology-body">'
            +   '<div class="bug-section bug-main">'
            +     '<div class="bug-sw-wrap">'
            +       '<input class="bug-input bug-sw" type="text" placeholder="SW-243977" autocomplete="off" spellcheck="false" aria-label="Jira ticket" />'
            +       '<div class="bug-jira-status" aria-live="polite">'
            +         '<span class="bug-jira-state" data-state="unknown" title="Jira credentials state">...</span>'
            +         '<button type="button" class="bug-jira-link bug-jira-setup" hidden title="Set up your Atlassian Cloud token">Set up</button>'
            +         '<button type="button" class="bug-jira-link bug-jira-edit" hidden title="Edit your Atlassian Cloud token">Edit</button>'
            +       '</div>'
            +     '</div>'
            +   '</div>'
            +   '<div class="bug-section bug-jira-config" hidden>'
            +     '<div class="bug-section-title">Jira credentials <span class="bug-sec-help" title="Atlassian Cloud only. Token is stored per-user on this server (mode 0600) and never echoed back to the browser.">?</span></div>'
            +     '<div class="bug-jc-saved" hidden aria-live="polite"></div>'
            +     '<label class="bug-field">'
            +       '<span class="bug-label">Site URL</span>'
            +       '<input class="bug-input bug-jc-url" type="text" placeholder="https://drivenets.atlassian.net" autocomplete="off" spellcheck="false" />'
            +     '</label>'
            +     '<label class="bug-field">'
            +       '<span class="bug-label">Email</span>'
            +       '<input class="bug-input bug-jc-email" type="email" placeholder="you@drivenets.com" autocomplete="off" />'
            +     '</label>'
            +     '<label class="bug-field">'
            +       '<span class="bug-label">API token <a class="bug-help-link" href="https://id.atlassian.com/manage-profile/security/api-tokens" target="_blank" rel="noopener" title="Create an Atlassian API token">get one &#x2192;</a></span>'
            +       '<input class="bug-input bug-jc-token" type="password" placeholder="ATATT3x..." autocomplete="off" spellcheck="false" />'
            +     '</label>'
            +     '<div class="bug-jc-error bug-error" hidden></div>'
            +     '<div class="bug-jc-actions">'
            +       '<button type="button" class="share-btn-secondary bug-jc-cancel">Cancel</button>'
            +       '<button type="button" class="share-btn-secondary bug-jc-clear" hidden>Forget</button>'
            +       '<button type="button" class="share-btn-primary bug-jc-save" title="Save (token blank = keep current)">Save</button>'
            +     '</div>'
            +   '</div>'
            +   '<details class="bug-advanced">'
            +     '<summary>Advanced</summary>'
            +     '<label class="bug-field">'
            +       '<span class="bug-label">Short title</span>'
            +       '<input class="bug-input bug-title" type="text" placeholder="EVPN-VPWS blocking-all on bgpd stop" autocomplete="off" />'
            +     '</label>'
            +     '<label class="bug-field">'
            +       '<span class="bug-label">Summary / symptom</span>'
            +       '<textarea class="bug-input bug-summary" rows="3" placeholder="One paragraph describing what is broken."></textarea>'
            +     '</label>'
            +     '<label class="bug-field">'
            +       '<span class="bug-label">Devices (comma-separated)</span>'
            +       '<input class="bug-input bug-devices" type="text" placeholder="ExaBGP, PE-1, RR-SA-2" autocomplete="off" />'
            +     '</label>'
            +     '<label class="bug-checkbox-row">'
            +       '<input type="checkbox" class="bug-force-placeholder" />'
            +       '<span>Placeholder only (skip Jira)</span>'
            +     '</label>'
            +   '</details>'
            +   '<div class="bug-fetch-status" hidden>'
            +     '<svg class="bug-spinner" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="12" cy="12" r="9" stroke-dasharray="40 60" stroke-linecap="round"/></svg>'
            +     '<span class="bug-fetch-msg">Fetching from Jira...</span>'
            +   '</div>'
            +   '<div class="bug-preview" hidden>'
            +     '<div class="bug-preview-title">Loaded from Jira</div>'
            +     '<div class="bug-preview-line"><span class="bug-preview-key">Type</span><span class="bug-preview-val bug-prev-type">&mdash;</span></div>'
            +     '<div class="bug-preview-line"><span class="bug-preview-key">Title</span><span class="bug-preview-val bug-prev-title">&mdash;</span></div>'
            +     '<div class="bug-preview-line"><span class="bug-preview-key">Devices</span><span class="bug-preview-val bug-prev-devices">&mdash;</span></div>'
            +     '<div class="bug-preview-line"><span class="bug-preview-key">VRFs</span><span class="bug-preview-val bug-prev-vrfs">&mdash;</span></div>'
            +   '</div>'
            +   '<div class="bug-not-a-bug" hidden>'
            +     '<div class="bug-not-a-bug-icon">'
            +       '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
            +     '</div>'
            +     '<div class="bug-not-a-bug-body">'
            +       '<div class="bug-not-a-bug-title">Not a bug ticket</div>'
            +       '<div class="bug-not-a-bug-msg"></div>'
            +       '<div class="bug-not-a-bug-actions">'
            +         '<button type="button" class="share-btn-secondary bug-nb-cancel">Cancel</button>'
            +         '<button type="button" class="share-btn-secondary bug-nb-force">Create anyway</button>'
            +       '</div>'
            +     '</div>'
            +   '</div>'
            +   '<div class="bug-error" hidden></div>'
            +   '<div class="share-form-footer bug-form-footer">'
            +     '<button type="button" class="share-btn-primary bug-create" disabled title="Press Enter to create (saved into your built-in Bugs domain)">'
            +       '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>'
            +       'Create'
            +     '</button>'
            +   '</div>'
            + '</div>';
    }

    function _wireEvents(host) {
        var closeBtn = host.querySelector('.dsf-close');
        if (closeBtn) closeBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            closeDialog();
        });

        // Escape while any input inside the panel has focus closes it.
        host.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                e.stopPropagation();
                closeDialog();
            }
        });

        var swInput = host.querySelector('.bug-sw');
        var createBtn = host.querySelector('.bug-create');
        var refreshState = function () {
            var ok = !!_normalizeSwId(swInput.value);
            createBtn.disabled = !ok;
            createBtn.classList.toggle('ready', ok);
        };
        swInput.addEventListener('input', refreshState);
        swInput.addEventListener('blur', function () {
            var n = _normalizeSwId(swInput.value);
            if (n) swInput.value = n;
        });

        // Enter from any input fires create (but not Shift+Enter inside textarea).
        host.querySelectorAll('.bug-input').forEach(function (el) {
            el.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    if (el.tagName === 'TEXTAREA' && !e.metaKey && !e.ctrlKey) return;
                    // Inside the Jira config panel, Enter saves creds instead.
                    if (el.closest('.bug-jira-config')) {
                        e.preventDefault();
                        _saveJiraConfig();
                        return;
                    }
                    e.preventDefault();
                    if (!createBtn.disabled) _submit();
                }
            });
        });
        createBtn.addEventListener('click', _submit);

        var setupBtn = host.querySelector('.bug-jira-setup');
        var editBtn  = host.querySelector('.bug-jira-edit');
        var jcCancel = host.querySelector('.bug-jc-cancel');
        var jcSave   = host.querySelector('.bug-jc-save');
        var jcClear  = host.querySelector('.bug-jc-clear');
        if (setupBtn) setupBtn.addEventListener('click', _openJiraConfig);
        if (editBtn)  editBtn.addEventListener('click', _openJiraConfig);
        if (jcCancel) jcCancel.addEventListener('click', _closeJiraConfig);
        if (jcSave)   jcSave.addEventListener('click', _saveJiraConfig);
        if (jcClear)  jcClear.addEventListener('click', _clearJiraConfig);

        var nbCancel = host.querySelector('.bug-nb-cancel');
        var nbForce  = host.querySelector('.bug-nb-force');
        if (nbCancel) nbCancel.addEventListener('click', function () {
            var notBug = host.querySelector('.bug-not-a-bug');
            if (notBug) notBug.hidden = true;
        });
        if (nbForce) nbForce.addEventListener('click', function () {
            var notBug = host.querySelector('.bug-not-a-bug');
            if (notBug) notBug.hidden = true;
            _submit({ forceNonBug: true });
        });
    }

    // The status row is deliberately minimal: a small colored dot drives the
    // state (via CSS data-state attribute) and either a Set up or Edit button
    // sits next to it. The optional `label` is used only as a tooltip on the
    // state dot + the active action button (e.g. "Jira: you@drivenets.com"),
    // so hovering reveals the current Jira account without using a dedicated
    // text row in the panel body.
    function _setJiraStatus(state, label) {
        var host = document.getElementById(DIALOG_ID);
        if (!host) return;
        var st = host.querySelector('.bug-jira-state');
        var setupBtn = host.querySelector('.bug-jira-setup');
        var editBtn  = host.querySelector('.bug-jira-edit');
        if (st) {
            st.dataset.state = state;
            // The dot itself carries the state color via CSS. No visible text
            // for ready/missing/error -- the Set up / Edit button explains what
            // the user can do next. Keep a short "..." only during the initial
            // probe so the user knows something is happening.
            st.textContent = (state === 'unknown') ? '...' : '';
            if (label) st.title = label;
        }
        if (setupBtn) {
            setupBtn.hidden = (state !== 'missing' && state !== 'error');
            if (label) setupBtn.title = label;
        }
        if (editBtn) {
            editBtn.hidden = (state !== 'ready');
            if (label) editBtn.title = label;
        }
    }

    async function _probeJiraConfig() {
        try {
            var resp = await _authFetch('/api/users/me/jira-config');
            var json = await resp.json();
            if (json && json.configured) {
                _jiraConfigured = true;
                _setJiraStatus('ready', 'Jira: ' + (json.email || 'configured'));
            } else {
                _jiraConfigured = false;
                _setJiraStatus('missing', 'Jira not configured -- click Set up');
            }
        } catch (_) {
            _jiraConfigured = false;
            _setJiraStatus('error', 'Jira config unreachable -- click Set up to retry');
        }
    }

    function _openJiraConfig() {
        var host = document.getElementById(DIALOG_ID);
        if (!host) return;
        var panel = host.querySelector('.bug-jira-config');
        if (!panel) return;
        panel.hidden = false;
        var clearBtn = panel.querySelector('.bug-jc-clear');
        if (clearBtn) clearBtn.hidden = !_jiraConfigured;
        // Reset the "saved" chip before the GET lands so we don't flash a
        // stale state if the probe races the user reopening Edit quickly.
        _renderJiraConfigSavedState(panel, null);
        _authFetch('/api/users/me/jira-config').then(function (r) {
            return r.json();
        }).then(function (j) {
            if (!j) return;
            var u = panel.querySelector('.bug-jc-url');
            var e = panel.querySelector('.bug-jc-email');
            if (u) u.value = j.base_url || u.value || '';
            if (e) e.value = j.email || e.value || '';
            // When creds already exist, put the UI into "keep existing" mode:
            //   - Show "Token saved" chip with hint + age above the token input.
            //   - Change the token placeholder to "Leave blank to keep current".
            //   - Don't preselect the empty field -- focus URL instead so the
            //     user edits rather than accidentally typing a new token first.
            _renderJiraConfigSavedState(panel, j.configured ? j : null);
        }).catch(function () { /* ignore */ });
        requestAnimationFrame(function () {
            var u = panel.querySelector('.bug-jc-url');
            if (u) u.focus();
            try { host.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); } catch (_) {}
        });
    }

    // Render the "Token saved" chip + switch the token input into keep-current
    // mode whenever the server tells us a token is on disk. Call with null to
    // revert to the fresh-token look ("ATATT3x..." placeholder, no chip).
    function _renderJiraConfigSavedState(panel, cfg) {
        if (!panel) return;
        var chip  = panel.querySelector('.bug-jc-saved');
        var tInput = panel.querySelector('.bug-jc-token');
        if (!chip || !tInput) return;
        if (cfg && cfg.configured) {
            var hint = cfg.token_hint || '****';
            var len = cfg.token_len || 0;
            var ageStr = _formatSavedAt(cfg.saved_at);
            chip.hidden = false;
            chip.innerHTML = ''
                + '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>'
                + '<span class="bug-jc-saved-label">Token saved</span>'
                + '<code class="bug-jc-saved-hint" title="Masked preview of the stored token">' + _escapeHtml(hint) + '</code>'
                + '<span class="bug-jc-saved-meta" title="Length of the stored token in characters">' + len + ' chars</span>'
                + (ageStr ? ('<span class="bug-jc-saved-meta">&middot; ' + _escapeHtml(ageStr) + '</span>') : '');
            tInput.placeholder = 'Leave blank to keep current token';
            tInput.dataset.keepExisting = '1';
        } else {
            chip.hidden = true;
            chip.innerHTML = '';
            tInput.placeholder = 'ATATT3x...';
            delete tInput.dataset.keepExisting;
        }
    }

    function _formatSavedAt(ts) {
        if (!ts || typeof ts !== 'number') return '';
        var ageSec = Math.max(0, Math.floor(Date.now() / 1000 - ts));
        if (ageSec < 60)  return 'just now';
        if (ageSec < 3600) return Math.floor(ageSec / 60) + 'm ago';
        if (ageSec < 86400) return Math.floor(ageSec / 3600) + 'h ago';
        if (ageSec < 2592000) return Math.floor(ageSec / 86400) + 'd ago';
        var d = new Date(ts * 1000);
        return d.toISOString().slice(0, 10);
    }

    function _closeJiraConfig() {
        var host = document.getElementById(DIALOG_ID);
        if (!host) return;
        var panel = host.querySelector('.bug-jira-config');
        if (panel) panel.hidden = true;
        var err = host.querySelector('.bug-jc-error');
        if (err) { err.hidden = true; err.textContent = ''; }
        // Clear the transient keep-existing flag so a subsequent "Set up"
        // (e.g. after a Forget) starts fresh instead of silently reusing
        // whatever token was on disk before.
        var t = host.querySelector('.bug-jc-token');
        if (t && t.dataset) delete t.dataset.keepExisting;
    }

    async function _saveJiraConfig() {
        var host = document.getElementById(DIALOG_ID);
        if (!host) return;
        var panel = host.querySelector('.bug-jira-config');
        if (!panel) return;
        var u = panel.querySelector('.bug-jc-url');
        var e = panel.querySelector('.bug-jc-email');
        var t = panel.querySelector('.bug-jc-token');
        var err = panel.querySelector('.bug-jc-error');
        var saveBtn = panel.querySelector('.bug-jc-save');
        var url = (u && u.value || '').trim();
        var email = (e && e.value || '').trim();
        var token = (t && t.value || '').trim();
        // "Keep current token" path: when editing an existing config, the UI
        // lets the user leave the token field blank and the backend reuses
        // the stored token. Only fail fast on URL/email being empty.
        var keepExisting = !!(t && t.dataset && t.dataset.keepExisting === '1');
        if (!url || !email) {
            err.textContent = 'Site URL and email are required.';
            err.hidden = false;
            return;
        }
        if (!token && !keepExisting) {
            err.textContent = 'API token is required.';
            err.hidden = false;
            return;
        }
        err.hidden = true; err.textContent = '';
        var prev = saveBtn.innerHTML;
        saveBtn.disabled = true;
        saveBtn.innerHTML = 'Verifying...';
        try {
            var payload = { base_url: url, email: email };
            // Only include the token when the user actually typed something.
            // Omitting it tells the backend "keep the existing stored token".
            if (token) payload.api_token = token;
            var resp = await _authFetch('/api/users/me/jira-config', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            var json = await resp.json();
            if (resp.status === 409
                    && window.FileOps
                    && window.FileOps._isDomainLimitResult
                    && window.FileOps._isDomainLimitResult(json)
                    && !opts.cleanupRetry) {
                var ed = _editor();
                var bugsSection = null;
                try {
                    bugsSection = (ed._customSections || []).find(function (s) { return s.id === '__bugs'; });
                } catch (_) { /* best-effort */ }
                bugsSection = bugsSection || { id: '__bugs', name: 'Bugs', color: '#e74c3c', builtin: true };
                var cleanup = await window.FileOps._openDomainCleanupPrompt(ed, bugsSection, null, {
                    reason: 'limit',
                    limitResult: json,
                });
                if (cleanup && cleanup.deleted_count > 0) {
                    return await _submit(Object.assign({}, opts, { cleanupRetry: true }));
                }
                return;
            }
            if (!resp.ok || json.error) {
                throw new Error(json.error || ('HTTP ' + resp.status));
            }
            _jiraConfigured = true;
            _setJiraStatus('ready', 'Jira: ' + email);
            // The save response now mirrors the GET payload (token_hint +
            // token_len + saved_at), so we refresh the "Token saved" chip
            // in-place instead of hiding the sub-form and re-fetching.
            _renderJiraConfigSavedState(panel, json);
            if (t) t.value = '';
            // Pulse the chip once so the user gets a visual confirmation
            // that the token round-tripped and was written. We keep the
            // sub-form open for the pulse duration so the animation has a
            // chance to play on-screen before we collapse back to the
            // main panel.
            var chip = panel.querySelector('.bug-jc-saved');
            if (chip && !chip.hidden) {
                chip.classList.remove('pulse');
                void chip.offsetWidth;       // force reflow to restart animation
                chip.classList.add('pulse');
            }
            _toast('Jira credentials saved', 'success');
            setTimeout(function () {
                if (chip) chip.classList.remove('pulse');
                _closeJiraConfig();
            }, 560);
        } catch (ex) {
            err.textContent = (ex && ex.message) ? ex.message : 'Could not save credentials';
            err.hidden = false;
        } finally {
            saveBtn.innerHTML = prev;
            saveBtn.disabled = false;
        }
    }

    async function _clearJiraConfig() {
        var host = document.getElementById(DIALOG_ID);
        if (!host) return;
        try {
            await _authFetch('/api/users/me/jira-config', { method: 'DELETE' });
            _jiraConfigured = false;
            _setJiraStatus('missing', 'Jira not configured -- click Set up');
            _closeJiraConfig();
            _toast('Jira credentials removed', 'info');
        } catch (_) { /* ignore */ }
    }

    // Public entry point. `anchorEl` is the "+ Bug" pill in the Bugs
    // row; we use it only to locate the Bugs row. Mounts the inline
    // panel inside that row, evicting any previously-open share or bug
    // inline form first (mutual exclusion).
    function open(anchorEl) {
        // Mutual exclusion with share inline form: close it first so the
        // dropdown only shows one inline panel at a time.
        try {
            if (window.TopologyShare && typeof window.TopologyShare.closeDialog === 'function') {
                window.TopologyShare.closeDialog();
            }
        } catch (_) { /* best-effort */ }
        // Mutual exclusion with the AI drawer: opening the Bug form
        // closes the AI drawer so the user never has two side/inline
        // panels competing for screen space. Mirrors the reverse hook
        // in topology-ai.js#open().
        try {
            if (window.TopologyAI && typeof window.TopologyAI.close === 'function') {
                window.TopologyAI.close();
            }
        } catch (_) { /* best-effort */ }

        var row = _findBugsRow(anchorEl);
        if (!row) {
            _toast('Bugs domain row is not visible -- open the Topologies dropdown first.', 'warning');
            return;
        }

        // Toggle: clicking + Bug again with the panel already mounted on
        // this row closes it (matches share's toggle-off behaviour).
        var existing = document.getElementById(DIALOG_ID);
        if (existing && row.contains(existing)) {
            closeDialog();
            return;
        }

        _expandDomainBody(row);
        var host = _ensureInlineHost(row);
        if (!host) return;

        // Reset every field so a stale ticket from the last open doesn't
        // bleed through. Matches previous dialog reset semantics.
        var swInput = host.querySelector('.bug-sw');
        var titleInput = host.querySelector('.bug-title');
        var summaryInput = host.querySelector('.bug-summary');
        var devicesInput = host.querySelector('.bug-devices');
        var forcePh = host.querySelector('.bug-force-placeholder');
        var errBox = host.querySelector('.bug-error');
        var createBtn = host.querySelector('.bug-create');
        var preview = host.querySelector('.bug-preview');
        var fetchBox = host.querySelector('.bug-fetch-status');
        var notBug = host.querySelector('.bug-not-a-bug');
        var advanced = host.querySelector('.bug-advanced');
        if (swInput) swInput.value = '';
        if (titleInput) titleInput.value = '';
        if (summaryInput) summaryInput.value = '';
        if (devicesInput) devicesInput.value = '';
        if (forcePh) forcePh.checked = false;
        if (errBox) { errBox.hidden = true; errBox.textContent = ''; }
        if (createBtn) { createBtn.disabled = true; createBtn.classList.remove('ready'); }
        if (preview) preview.hidden = true;
        if (fetchBox) fetchBox.hidden = true;
        if (notBug) notBug.hidden = true;
        if (advanced) advanced.open = false;
        _closeJiraConfig();
        _probeJiraConfig();

        host.style.display = 'block';
        void host.offsetHeight;          // flush so the transition plays
        host.classList.add('open');

        // Mirror open-state on the "+ Bug" pill so the CSS `.active`
        // treatment (inset ring + brighter background) shows while the
        // panel is mounted. This gives the user positive confirmation
        // that the pill they clicked is what is driving the visible
        // panel, mirroring the toggle-off semantics (clicking it again
        // closes the panel).
        _setNewBugBtnActive(row, true);

        requestAnimationFrame(function () {
            try { host.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); } catch (_) {}
            if (swInput) swInput.focus();
        });
    }

    function closeDialog() {
        var host = document.getElementById(DIALOG_ID);
        if (!host) return;
        var row = host.closest && host.closest('.custom-section-category');
        host.classList.remove('open');
        if (row) _setNewBugBtnActive(row, false);
        // Short fade; keep in sync with the opacity transition in
        // styles.css for .domain-bug-form (inherits .domain-share-form).
        setTimeout(function () {
            if (!host.parentNode) return;
            if (host.classList.contains('open')) return; // reopened mid-fade
            host.parentNode.removeChild(host);
        }, 180);
    }

    // Toggle the `.active` visual state on the "+ Bug" pill that lives in
    // the Bugs row header. Keeps the pill in sync with the panel lifecycle
    // so the user always knows "yes, this button is the one that opened
    // the form". Safe no-op if the pill is missing (e.g. row was re-rendered).
    function _setNewBugBtnActive(row, active) {
        if (!row) return;
        var btn = row.querySelector('.domain-newbug-btn');
        if (!btn) return;
        if (active) btn.classList.add('active');
        else btn.classList.remove('active');
    }

    async function _submit(opts) {
        // Tolerate being called as a DOM event handler (click/Enter) where
        // the first arg is an Event, not our options object.
        if (!opts || typeof opts !== 'object' || opts instanceof Event) opts = {};
        var forceNonBug = !!opts.forceNonBug;
        var host = document.getElementById(DIALOG_ID);
        if (!host) return;
        var swInput = host.querySelector('.bug-sw');
        var titleInput = host.querySelector('.bug-title');
        var summaryInput = host.querySelector('.bug-summary');
        var devicesInput = host.querySelector('.bug-devices');
        var forcePh = host.querySelector('.bug-force-placeholder');
        var errBox = host.querySelector('.bug-error');
        var createBtn = host.querySelector('.bug-create');
        var preview = host.querySelector('.bug-preview');
        var fetchBox = host.querySelector('.bug-fetch-status');
        var fetchMsg = host.querySelector('.bug-fetch-msg');
        var notBug = host.querySelector('.bug-not-a-bug');

        var swId = _normalizeSwId(swInput.value);
        if (!swId) {
            errBox.textContent = 'Enter a Jira ticket like SW-243977.';
            errBox.hidden = false;
            return;
        }
        errBox.hidden = true;
        errBox.textContent = '';
        if (preview) preview.hidden = true;
        if (notBug) notBug.hidden = true;

        var devices = (devicesInput.value || '')
            .split(',')
            .map(function (s) { return s.trim(); })
            .filter(function (s) { return s.length > 0; })
            .map(function (label, idx) {
                if (/^\d/.test(label) || /\./.test(label)) {
                    return { label: 'Node-' + (idx + 1), ip: label };
                }
                return { label: label };
            });

        createBtn.disabled = true;
        createBtn.classList.add('busy');
        var prevText = createBtn.innerHTML;
        createBtn.innerHTML = '<svg class="bug-spinner" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="12" cy="12" r="9" stroke-dasharray="40 60" stroke-linecap="round"/></svg> Creating';

        var willFetchJira = (_jiraConfigured && !(forcePh && forcePh.checked));
        if (fetchBox) {
            fetchBox.hidden = !willFetchJira;
            if (fetchMsg) {
                // Two-phase wording: first verify the ticket is a bug, then
                // pull the real ticket payload. Backend returns a 422 with
                // code "not-a-bug" for non-bug-like issuetypes so the user
                // gets a clean rejection before any topology is saved.
                fetchMsg.textContent = forceNonBug
                    ? ('Importing ' + swId + ' (forcing non-bug)...')
                    : ('Verifying ' + swId + ' is a bug...');
            }
        }

        try {
            var resp = await _authFetch('/api/bugs/from-jira', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sw_id: swId,
                    title: (titleInput.value || '').trim(),
                    summary: (summaryInput.value || '').trim(),
                    devices: devices,
                    force_placeholder: !!(forcePh && forcePh.checked),
                    force_non_bug: forceNonBug
                }),
            });
            var json = await resp.json();
            // Wrong-issuetype rejection: don't throw, render the dedicated
            // panel so the user can either pick a real bug ticket or click
            // "Create anyway" to override.
            if (resp.status === 422 && json && json.code === 'not-a-bug') {
                if (notBug) {
                    var msg = notBug.querySelector('.bug-not-a-bug-msg');
                    if (msg) {
                        msg.innerHTML =
                            '<strong>' + _escapeHtml(json.sw_id || swId) + '</strong> is a '
                            + '<strong>' + _escapeHtml(json.issue_type || 'non-bug') + '</strong>'
                            + ' ticket, not a Bug. Bug topologies are only created from '
                            + 'Bug-like tickets. You can pick a different SW or click '
                            + '<em>Create anyway</em> to build it as a bug topology regardless.';
                    }
                    notBug.hidden = false;
                }
                return;
            }
            if (!resp.ok || json.error) {
                throw new Error(json.error || ('HTTP ' + resp.status));
            }
            if (preview && json.source === 'jira') {
                var pt = preview.querySelector('.bug-prev-title');
                var ptype = preview.querySelector('.bug-prev-type');
                var pd = preview.querySelector('.bug-prev-devices');
                var pv = preview.querySelector('.bug-prev-vrfs');
                if (ptype) {
                    var typeName = json.issue_type || 'Unknown';
                    var typeBadge = json.is_bug_like
                        ? '<span class="bug-type-pill bug-type-ok">' + _escapeHtml(typeName) + '</span>'
                        : '<span class="bug-type-pill bug-type-warn">' + _escapeHtml(typeName) + ' (forced)</span>';
                    ptype.innerHTML = typeBadge;
                }
                if (pt) pt.textContent = json.jira_title || '(no title)';
                if (pd) pd.textContent = (json.devices_count || 0) + ' device(s)';
                if (pv) pv.textContent = (json.vrfs_count || 0) + ' VRF(s)';
                preview.hidden = false;
            }
            await _openCreatedTopology(json);
            closeDialog();
            var srcLabel = (json.source === 'jira') ? ' (from Jira)' : '';
            _toast('Bug topology created: ' + (json.name || swId) + srcLabel, 'success');
        } catch (e) {
            var emsg = (e && e.message) ? e.message : 'Failed to create bug topology';
            if (/401|403/.test(emsg)) {
                emsg += ' \u2014 click "Edit" above to refresh your Jira API token.';
            }
            errBox.textContent = emsg;
            errBox.hidden = false;
        } finally {
            createBtn.innerHTML = prevText;
            createBtn.disabled = false;
            createBtn.classList.remove('busy');
            if (fetchBox) fetchBox.hidden = true;
        }
    }

    function _escapeHtml(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    async function _openCreatedTopology(result) {
        if (!result || !result.section_id || !result.filename) return;
        var ed = _editor();
        try {
            var resp = await _authFetch(
                '/api/sections/' + encodeURIComponent(result.section_id)
                + '/topologies/' + encodeURIComponent(result.filename)
            );
            if (!resp.ok) return;
            var data = await resp.json();
            if (ed && typeof ed.loadTopologyFromData === 'function') {
                // Push the freshly generated bug topology onto the canvas
                // immediately. The editor's loadTopologyFromData clears
                // this.objects, resets counters, re-draws and centers --
                // so the canvas must not carry leftover geometry from the
                // previously loaded topology once this completes.
                ed.loadTopologyFromData(data, { domain: 'Bugs' });
            } else {
                // Best-effort fallback for boot race conditions: retry
                // once after the editor finishes constructing. Without
                // this, a user who opened the dropdown before
                // topology.js finished init would land on a stale
                // canvas until switching topologies manually.
                setTimeout(function () {
                    var ed2 = _editor();
                    if (ed2 && typeof ed2.loadTopologyFromData === 'function') {
                        ed2.loadTopologyFromData(data, { domain: 'Bugs' });
                    }
                }, 150);
            }
            if (window.FileOps && typeof window.FileOps.updateTopologyIndicator === 'function') {
                window.FileOps.updateTopologyIndicator(result.name, 'Bugs', '#e74c3c', result.section_id);
            }
            // Close the topologies dropdown so the user lands cleanly on
            // the new canvas; match legacy behaviour.
            var dd = _getTopologiesDropdown();
            if (dd) dd.style.display = 'none';
            var btn = document.getElementById('btn-topologies');
            if (btn) btn.classList.remove('topologies-open');
            // Refresh the inline file list inside the Bugs domain so the
            // newly created topology is visible the next time the dropdown
            // opens, without forcing a full page reload.
            if (window.FileOps && typeof window.FileOps._renderCustomSectionsInDropdown === 'function'
                && ed) {
                try {
                    var sectionsResp = await _authFetch('/api/sections');
                    var sectionsJson = await sectionsResp.json();
                    if (sectionsJson && sectionsJson.sections) {
                        ed._customSections = sectionsJson.sections;
                        window.FileOps._renderCustomSectionsInDropdown(ed);
                    }
                } catch (_) { /* non-fatal */ }
            }
        } catch (_) { /* non-fatal */ }
    }

    window.TopologyBugs = {
        open: open,
        close: closeDialog,
    };
})();
