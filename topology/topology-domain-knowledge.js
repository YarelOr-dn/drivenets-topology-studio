/**
 * topology-domain-knowledge.js -- Per-domain "project workspace" panel.
 *
 * A Topology Domain used to be just a folder of topology files. This module
 * adds one compact per-domain tool: feature branch image/build monitoring.
 *
 * The panel lives as an inline, expand-on-demand settings bar mounted under
 * each domain row inside the main Topologies dropdown (see
 * `topology-file-ops.js` -- the domain row is `.custom-section-category`).
 * Changes save automatically (debounced 800 ms) so the bar acts as a
 * persistent per-domain settings surface rather than a modal dialog.
 *
 * Hybrid sharing is respected end-to-end:
 *   - public  rows travel with the domain share; the owner authors them
 *   - private rows are your own annotations on someone else's domain
 * The REST layer (knowledge_router.py) enforces write permissions; the UI
 * reflects them by auto-flipping the "New item" radio to 'private' and
 * hiding the edit button for other people's public rows when the viewer
 * only has read access.
 *
 * Live status is refreshed via:
 *   - on-open POST /refresh-all (covers all live kinds at once)
 *   - per-item Refresh button (POST /{kind}/{key}/refresh)
 *   - background poller (ws event 'domain.knowledge.updated')
 *
 * Public API:
 *   window.TopologyDomainKnowledge.mount(domainRowEl, domain)
 *   window.TopologyDomainKnowledge.ensureDropdownButton(domainRowEl, domain)
 *   window.TopologyDomainKnowledge.refresh(domainId)
 */
(function () {
    'use strict';

    const API_BASE = '/api/domains';
    const SAVE_DEBOUNCE_MS = 800;
    // Freshness threshold for "looks stale" hint (12 h).
    const STALE_HINT_MS = 12 * 60 * 60 * 1000;
    // Debounce window for live-update re-renders. Keeps bursts of WebSocket
    // events (poller finishing a cycle over 20 branches) from causing a
    // render-storm -- we coalesce into a single reload per panel.
    const WS_UPDATE_DEBOUNCE_MS = 250;

    let _kindsCache = null; // loaded once, immutable (same set for every session)
    // domainId -> {items: [], permission, isSharedIn, owner, lastFetch,
    //              kinds, open (sticky across dropdown re-renders),
    //              activeKind (sticky), wsDebounceTimer}
    const _state = Object.create(null);
    // DOM handles for any currently-mounted panels, keyed by domainId.
    const _panels = Object.create(null);

    // ----------------------------------------------------------------
    // Tiny helpers
    // ----------------------------------------------------------------
    function _authFetch(url, opts) {
        if (window.TopologyAuth && window.TopologyAuth.authFetch) {
            return window.TopologyAuth.authFetch(url, opts);
        }
        return fetch(url, opts);
    }

    function _esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;',
                '"': '&quot;', "'": '&#39;',
            })[c];
        });
    }

    function _debounce(fn, ms) {
        let t = null;
        return function () {
            const args = arguments;
            const ctx = this;
            if (t) clearTimeout(t);
            t = setTimeout(function () { fn.apply(ctx, args); }, ms);
        };
    }

    function _relativeTime(isoOrMs) {
        if (!isoOrMs) return 'never';
        let ts;
        if (typeof isoOrMs === 'number') {
            ts = isoOrMs;
        } else {
            ts = Date.parse(isoOrMs);
        }
        if (!ts || Number.isNaN(ts)) return 'unknown';
        const diff = Date.now() - ts;
        const abs = Math.abs(diff);
        if (abs < 60 * 1000) return diff >= 0 ? 'just now' : 'in a moment';
        if (abs < 60 * 60 * 1000) {
            const m = Math.floor(abs / 60000);
            return diff >= 0 ? `${m}m ago` : `in ${m}m`;
        }
        if (abs < 24 * 60 * 60 * 1000) {
            const h = Math.floor(abs / 3600000);
            return diff >= 0 ? `${h}h ago` : `in ${h}h`;
        }
        const d = Math.floor(abs / (24 * 3600000));
        return diff >= 0 ? `${d}d ago` : `in ${d}d`;
    }

    function _toast(msg, kind) {
        try {
            if (window.showToast) {
                window.showToast(msg, kind || 'info');
                return;
            }
        } catch (_) { /* fall through */ }
        console.info('[domain-knowledge]', msg);
    }

    // ----------------------------------------------------------------
    // Kind metadata + icons
    // ----------------------------------------------------------------
    async function _loadKinds() {
        if (_kindsCache) return _kindsCache;
        try {
            const r = await _authFetch(API_BASE + '/knowledge/kinds');
            if (!r.ok) throw new Error('HTTP ' + r.status);
            _kindsCache = await r.json();
        } catch (e) {
            console.warn('[domain-knowledge] kinds fetch failed', e);
            _kindsCache = [];
        }
        return _kindsCache;
    }

    function _monitorKinds(kinds) {
        const branchKind = (Array.isArray(kinds) ? kinds : [])
            .find(function (k) { return k && k.kind === 'branch'; });
        return [branchKind || {
            kind: 'branch',
            label: R.branch.label,
            description: R.branch.hint,
            supports_live: true,
        }];
    }

    function _kindIcon(kind) {
        // Small inline SVGs so we don't need new icon font entries. Keep them
        // visually in the DriveNets brand palette (var(--dn-cyan)).
        const svgs = {
            branch:
                '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="4" cy="3" r="1.6"/><circle cx="4" cy="13" r="1.6"/><circle cx="12" cy="8" r="1.6"/><path d="M4 4.6v6.8"/><path d="M4 8c0-2 2-3.4 4-3.4h2.4"/></svg>',
            jira_epic:
                '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2.5" y="2.5" width="11" height="11" rx="2"/><path d="M5 8h6"/><path d="M8 5v6"/></svg>',
            test_suite:
                '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"><path d="M3 2h10l-1.5 5v6l-3.5 2-3.5-2V7z"/><path d="M4.5 7h7"/></svg>',
            spirent:
                '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 8h3l1.5-3 3 6 1.5-3h3"/></svg>',
            device:
                '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="4" width="12" height="8" rx="1"/><circle cx="4.5" cy="8" r="0.8"/><circle cx="7" cy="8" r="0.8"/></svg>',
            note:
                '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3.5 2.5h6l3 3v8h-9z"/><path d="M9.5 2.5v3h3"/><path d="M5.5 8h5"/><path d="M5.5 10.5h3.5"/></svg>',
            confluence:
                '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3.5 10.5a3 3 0 0 1 0-4 3 3 0 0 1 4 0l1 1a3 3 0 0 0 4 0"/><path d="M12.5 5.5a3 3 0 0 1 0 4 3 3 0 0 1-4 0l-1-1a3 3 0 0 0-4 0"/></svg>',
            cli_preset:
                '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M3 5l3 3-3 3"/><path d="M8 11h5"/></svg>',
            bugs_scope:
                '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 3.5V2"/><path d="M10 3.5V2"/><rect x="4" y="4" width="8" height="8" rx="3"/><path d="M2.5 7.5h2"/><path d="M11.5 7.5h2"/><path d="M2.5 11h2"/><path d="M11.5 11h2"/></svg>',
            ai_scope:
                '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M8 2v2"/><path d="M8 12v2"/><path d="M2 8h2"/><path d="M12 8h2"/><circle cx="8" cy="8" r="3"/></svg>',
        };
        return svgs[kind] || svgs.note;
    }

    // ----------------------------------------------------------------
    // Data layer
    // ----------------------------------------------------------------
    // Legacy per-user sections live only in the per-user JSON store
    // (ids prefixed with `sec_` -- the timestamp-suffixed format created
    // by `/api/sections/create`), NOT in the multi-user `/api/domains`
    // DB. Hitting the knowledge endpoint for them is a guaranteed 404,
    // and while the code below has always tolerated the 404 response,
    // the *browser itself* still logs every failed network request to
    // the devtools console (we can't suppress that from JS). So every
    // gear-click on a `sec_*` row produced a red line in the console.
    //
    // Fix: short-circuit BEFORE the fetch for the known-legacy prefix.
    // The response shape we return is identical to the prior 404 branch
    // so every caller that already expects `_legacy_section: true` (and
    // renders the empty/"no knowledge yet" state) stays happy.
    function _isLegacySectionId(domainId) {
        // Empty / missing IDs are tolerated too -- treated as legacy so
        // we don't bombard /api/domains with blank keys. Non-string
        // values defensively coerce.
        const id = String(domainId == null ? '' : domainId);
        if (!id) return true;
        return id.indexOf('sec_') === 0;
    }

    function _emptyLegacyResult(domainId) {
        return {
            domain_id: domainId,
            permission: 'read',
            is_shared_in: false,
            owner: '',
            items: [],
            _legacy_section: true,
        };
    }

    async function _fetchItems(domainId) {
        if (_isLegacySectionId(domainId)) {
            return _emptyLegacyResult(domainId);
        }
        const r = await _authFetch(
            API_BASE + '/' + encodeURIComponent(domainId) + '/knowledge'
        );
        // Defensive fallback for any non-legacy-prefix ID that the
        // multi-user DB has no record of (e.g. a stale dropdown shown
        // mid-migration). Same "empty panel, no error banner" shape as
        // the pre-flight skip above.
        if (r.status === 404) {
            return _emptyLegacyResult(domainId);
        }
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return await r.json();
    }

    async function _saveItem(domainId, body, existingKey) {
        const url = existingKey
            ? API_BASE + '/' + encodeURIComponent(domainId)
              + '/knowledge/' + encodeURIComponent(body.kind)
              + '/' + encodeURIComponent(existingKey)
            : API_BASE + '/' + encodeURIComponent(domainId) + '/knowledge';
        const r = await _authFetch(url, {
            method: existingKey ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!r.ok) {
            const err = await r.json().catch(() => ({}));
            throw new Error(err.detail || ('HTTP ' + r.status));
        }
        return await r.json();
    }

    async function _deleteItem(domainId, kind, key, visibility) {
        const url = API_BASE + '/' + encodeURIComponent(domainId)
            + '/knowledge/' + encodeURIComponent(kind)
            + '/' + encodeURIComponent(key)
            + '?visibility=' + encodeURIComponent(visibility || 'public');
        const r = await _authFetch(url, { method: 'DELETE' });
        if (!r.ok) {
            const err = await r.json().catch(() => ({}));
            throw new Error(err.detail || ('HTTP ' + r.status));
        }
    }

    async function _refreshItem(domainId, kind, key, visibility) {
        const url = API_BASE + '/' + encodeURIComponent(domainId)
            + '/knowledge/' + encodeURIComponent(kind)
            + '/' + encodeURIComponent(key)
            + '/refresh?visibility=' + encodeURIComponent(visibility || 'public');
        const r = await _authFetch(url, { method: 'POST' });
        if (!r.ok) return null;
        return await r.json();
    }

    async function _refreshAll(domainId, kind) {
        // Same legacy-section short-circuit as _fetchItems: refresh-all
        // on a `sec_*` domain would 404 at /api/domains/<id>/... and
        // pollute the devtools console with one red line per gear-click.
        // Returning null (== "no refresh payload") preserves the caller
        // contract (`resp && resp.items` -> skipped) without any bad UX.
        if (_isLegacySectionId(domainId)) {
            return null;
        }
        const url = API_BASE + '/' + encodeURIComponent(domainId)
            + '/knowledge/refresh-all'
            + (kind ? '?kind=' + encodeURIComponent(kind) : '');
        const r = await _authFetch(url, { method: 'POST' });
        if (!r.ok) return null;
        // Backend returns {status, refreshed, total, items, permission,
        // is_shared_in, owner, errors}. We pipe items straight into the
        // render so the panel updates in a single round-trip.
        return await r.json();
    }

    // ----------------------------------------------------------------
    // Per-kind renderers
    // ----------------------------------------------------------------
    //
    // Each renderer returns HTML for ONE row in a tab. Editors are inline
    // so the panel stays compact; heavy editors (markdown for notes) expand
    // vertically but never push the panel into a separate modal.
    //
    // renderItem(item, ctx) -> string (HTML)
    // renderNew(ctx)        -> string (HTML for the "+ Add" form)
    // readForm(formEl, ctx) -> payload object (or throws with a message)

    const R = Object.create(null);

    // -- BRANCH ------------------------------------------------------
    R.branch = {
        label: 'Image branch monitor',
        hint: 'Monitor Jenkins image builds -- status, sanitizer flag, latest SUCCESS, and artifact expiry.',
        renderItem: function (item) {
            const p = item.payload || {};
            const lb = p.last_build || null;
            const err = p.last_error || '';
            let status = 'no builds';
            let statusClass = 'dk-pill-muted';
            if (lb) {
                if (lb.building) { status = 'BUILDING #' + lb.number; statusClass = 'dk-pill-building'; }
                else if (lb.result === 'SUCCESS') { status = 'SUCCESS #' + lb.number; statusClass = 'dk-pill-ok'; }
                else if (lb.result) { status = lb.result + ' #' + lb.number; statusClass = 'dk-pill-fail'; }
            }
            const age = lb && lb.timestamp ? _relativeTime(lb.timestamp) : '';
            const sanitizer = lb && lb.sanitizer
                ? '<span class="dk-pill dk-pill-sanitizer" title="AddressSanitizer build">SAN</span>' : '';
            const expired = lb && lb.expired
                ? '<span class="dk-pill dk-pill-warn" title="Older than 48h -- artifacts may be gone">EXPIRED</span>' : '';
            const errPill = err
                ? '<span class="dk-meta-err" title="' + _esc(err) + '">sync error</span>' : '';
            const jenkinsHref = lb && lb.url ? lb.url
                : 'https://jenkins.dev.drivenets.net/job/drivenets/job/cheetah/job/' + encodeURIComponent(p.branch_name);
            return '' +
                '<div class="dk-row-main">' +
                    '<div class="dk-row-title">' +
                        '<a href="' + _esc(jenkinsHref) + '" target="_blank" rel="noopener">' +
                            _esc(p.branch_name) +
                        '</a>' +
                        (p.category && p.category !== 'other'
                            ? '<span class="dk-tag">' + _esc(p.category) + '</span>' : '') +
                    '</div>' +
                    '<div class="dk-row-meta">' +
                        '<span class="dk-pill ' + statusClass + '">' + _esc(status) + '</span>' +
                        sanitizer + expired + errPill +
                        (age ? '<span class="dk-meta-dim">' + _esc(age) + '</span>' : '') +
                        (p.last_checked_at
                            ? '<span class="dk-meta-dim" title="Last server refresh">synced ' +
                              _esc(_relativeTime(p.last_checked_at)) + '</span>' : '') +
                    '</div>' +
                    (p.notes ? '<div class="dk-row-notes">' + _esc(p.notes) + '</div>' : '') +
                '</div>';
        },
        renderNew: function () {
            return '' +
                '<input type="text" name="branch_name" placeholder="feature/dev_v26_2/foo OR dev_v26_2" required>' +
                '<select name="category">' +
                    '<option value="feature">feature</option>' +
                    '<option value="dev">dev</option>' +
                    '<option value="release">release</option>' +
                    '<option value="other">other</option>' +
                '</select>' +
                '<input type="text" name="notes" placeholder="notes (optional)">';
        },
        readForm: function (form) {
            const name = (form.querySelector('[name=branch_name]').value || '').trim();
            if (!name) throw new Error('Branch name is required');
            return {
                branch_name: name,
                category: form.querySelector('[name=category]').value || 'feature',
                notes: (form.querySelector('[name=notes]').value || '').trim(),
            };
        },
    };

    // -- JIRA EPIC ---------------------------------------------------
    R.jira_epic = {
        label: 'Jira issues',
        hint: 'Pin a Jira EPIC or ticket. Uses your per-user jira_config to fetch status.',
        renderItem: function (item) {
            const p = item.payload || {};
            const url = p.url || '';
            const summary = p.summary || '(no summary synced yet)';
            const status = p.status || 'unknown';
            const assignee = p.assignee || 'unassigned';
            const priority = p.priority || '';
            const error = p.last_error || '';
            return '' +
                '<div class="dk-row-main">' +
                    '<div class="dk-row-title">' +
                        (url
                            ? '<a href="' + _esc(url) + '" target="_blank" rel="noopener">' + _esc(p.issue_key) + '</a>'
                            : '<span class="dk-key">' + _esc(p.issue_key) + '</span>') +
                        '<span class="dk-ellipsis">' + _esc(summary) + '</span>' +
                    '</div>' +
                    '<div class="dk-row-meta">' +
                        '<span class="dk-pill dk-pill-jira">' + _esc(status) + '</span>' +
                        (priority ? '<span class="dk-pill dk-pill-muted">' + _esc(priority) + '</span>' : '') +
                        '<span class="dk-meta-dim">' + _esc(assignee) + '</span>' +
                        (error ? '<span class="dk-meta-err" title="' + _esc(error) + '">sync error</span>' : '') +
                    '</div>' +
                '</div>';
        },
        renderNew: function () {
            return '' +
                '<input type="text" name="issue_key" placeholder="SW-12345" pattern="[A-Z][A-Z0-9]+-[0-9]+" required>' +
                '<input type="text" name="notes" placeholder="notes (optional)">';
        },
        readForm: function (form) {
            const key = (form.querySelector('[name=issue_key]').value || '').trim().toUpperCase();
            if (!/^[A-Z][A-Z0-9]+-\d+$/.test(key)) throw new Error('Issue key must look like SW-12345');
            return {
                issue_key: key,
                notes: (form.querySelector('[name=notes]').value || '').trim(),
            };
        },
    };

    // -- TEST SUITE --------------------------------------------------
    R.test_suite = {
        label: 'Test suites',
        hint: 'Link a scaler/TEST/catalog/<suite>/ folder. Shows last 5 RUN_* results.',
        renderItem: function (item) {
            const p = item.payload || {};
            const runs = Array.isArray(p.last_runs) ? p.last_runs : [];
            const runsHtml = runs.length
                ? runs.map(function (r) {
                    const v = (r.verdict || 'unknown').toUpperCase();
                    const cls = v === 'PASS' ? 'dk-pill-ok' : (v === 'FAIL' ? 'dk-pill-fail' : 'dk-pill-muted');
                    return '<span class="dk-pill ' + cls + '" title="' + _esc(r.run_id) + '">'
                        + _esc(r.run_id.replace(/^RUN_/, '')) + ' ' + _esc(v) + '</span>';
                }).join('')
                : '<span class="dk-meta-dim">no runs yet</span>';
            return '' +
                '<div class="dk-row-main">' +
                    '<div class="dk-row-title">' +
                        '<code class="dk-path">' + _esc(p.suite_path) + '</code>' +
                    '</div>' +
                    '<div class="dk-row-meta">' + runsHtml + '</div>' +
                '</div>';
        },
        renderNew: function () {
            return '<input type="text" name="suite_path" placeholder="TEST/catalog/evpn_mac_mobility_SW204115" required>'
                + '<input type="text" name="label" placeholder="display name (optional)">';
        },
        readForm: function (form) {
            const path = (form.querySelector('[name=suite_path]').value || '').trim();
            if (!path) throw new Error('Suite path is required');
            return {
                suite_path: path,
                label: (form.querySelector('[name=label]').value || '').trim(),
            };
        },
    };

    // -- SPIRENT -----------------------------------------------------
    R.spirent = {
        label: 'Spirent sessions',
        hint: 'scaler/SPIRENT/sessions/*.json -- stream count, last run.',
        renderItem: function (item) {
            const p = item.payload || {};
            const streams = p.stream_count || 0;
            const devices = p.device_count || 0;
            return '' +
                '<div class="dk-row-main">' +
                    '<div class="dk-row-title">' +
                        '<span>' + _esc(p.label || p.session_path) + '</span>' +
                        '<code class="dk-path-dim">' + _esc(p.session_path) + '</code>' +
                    '</div>' +
                    '<div class="dk-row-meta">' +
                        '<span class="dk-pill dk-pill-muted">' + streams + ' streams</span>' +
                        '<span class="dk-pill dk-pill-muted">' + devices + ' devices</span>' +
                        (p.last_run_at
                            ? '<span class="dk-meta-dim">last run ' + _esc(_relativeTime(p.last_run_at)) + '</span>'
                            : '') +
                    '</div>' +
                '</div>';
        },
        renderNew: function () {
            return '<input type="text" name="session_path" placeholder="SPIRENT/sessions/dn_spirent_main.json" required>'
                + '<input type="text" name="label" placeholder="label (optional)">';
        },
        readForm: function (form) {
            const path = (form.querySelector('[name=session_path]').value || '').trim();
            if (!path) throw new Error('Session path is required');
            return {
                session_path: path,
                label: (form.querySelector('[name=label]').value || '').trim(),
            };
        },
    };

    // -- DEVICE ------------------------------------------------------
    R.device = {
        label: 'Devices',
        hint: 'Explicit device roster for this domain (separate from any canvas).',
        renderItem: function (item) {
            const p = item.payload || {};
            return '' +
                '<div class="dk-row-main">' +
                    '<div class="dk-row-title">' +
                        '<strong>' + _esc(p.device_id) + '</strong>' +
                        (p.role ? '<span class="dk-tag">' + _esc(p.role) + '</span>' : '') +
                    '</div>' +
                    '<div class="dk-row-meta">' +
                        (p.mgmt_ip ? '<code class="dk-path-dim">' + _esc(p.mgmt_ip) + '</code>' : '') +
                        (p.label && p.label !== p.device_id
                            ? '<span class="dk-meta-dim">' + _esc(p.label) + '</span>' : '') +
                    '</div>' +
                '</div>';
        },
        renderNew: function () {
            return '<input type="text" name="device_id" placeholder="PE-1" required>'
                + '<input type="text" name="mgmt_ip" placeholder="mgmt IP (optional)">'
                + '<input type="text" name="role" placeholder="role (optional)">';
        },
        readForm: function (form) {
            const id = (form.querySelector('[name=device_id]').value || '').trim();
            if (!id) throw new Error('Device id is required');
            return {
                device_id: id,
                mgmt_ip: (form.querySelector('[name=mgmt_ip]').value || '').trim(),
                role: (form.querySelector('[name=role]').value || '').trim(),
            };
        },
    };

    // -- NOTE --------------------------------------------------------
    R.note = {
        label: 'Notes',
        hint: 'Domain runbook / scratchpad (plain text, markdown rendered verbatim).',
        renderItem: function (item) {
            const p = item.payload || {};
            const title = p.title || 'Note';
            const body = p.markdown || '';
            const preview = body.length > 200 ? body.slice(0, 200) + ' ...' : body;
            return '<div class="dk-row-main">' +
                '<div class="dk-row-title"><strong>' + _esc(title) + '</strong></div>' +
                '<div class="dk-note-body">' + _esc(preview) + '</div>' +
            '</div>';
        },
        renderNew: function () {
            return '<input type="text" name="title" placeholder="Note title">'
                + '<textarea name="markdown" rows="3" placeholder="Write anything (markdown-safe)..."></textarea>';
        },
        readForm: function (form) {
            return {
                title: (form.querySelector('[name=title]').value || '').trim(),
                markdown: form.querySelector('[name=markdown]').value || '',
            };
        },
    };

    // -- CONFLUENCE --------------------------------------------------
    R.confluence = {
        label: 'Links',
        hint: 'Confluence / external spec URLs for this domain.',
        renderItem: function (item) {
            const p = item.payload || {};
            return '<div class="dk-row-main">' +
                '<div class="dk-row-title">' +
                    '<a href="' + _esc(p.url) + '" target="_blank" rel="noopener">' + _esc(p.title || p.url) + '</a>' +
                '</div>' +
                (p.description ? '<div class="dk-row-notes">' + _esc(p.description) + '</div>' : '') +
            '</div>';
        },
        renderNew: function () {
            return '<input type="url" name="url" placeholder="https://drivenets.atlassian.net/wiki/..." required>'
                + '<input type="text" name="title" placeholder="title (optional)">';
        },
        readForm: function (form) {
            const url = (form.querySelector('[name=url]').value || '').trim();
            if (!/^https?:\/\//.test(url)) throw new Error('URL must start with http:// or https://');
            return {
                url: url,
                title: (form.querySelector('[name=title]').value || '').trim(),
            };
        },
    };

    // -- CLI PRESET --------------------------------------------------
    R.cli_preset = {
        label: 'CLI presets',
        hint: 'Pinned search_cli_docs queries or show commands for this domain.',
        renderItem: function (item) {
            const p = item.payload || {};
            return '<div class="dk-row-main">' +
                '<div class="dk-row-title">' +
                    '<code class="dk-cli">' + _esc(p.query) + '</code>' +
                    (p.category ? '<span class="dk-tag">' + _esc(p.category) + '</span>' : '') +
                '</div>' +
                (p.description ? '<div class="dk-row-notes">' + _esc(p.description) + '</div>' : '') +
            '</div>';
        },
        renderNew: function () {
            return '<input type="text" name="query" placeholder="show evpn mac-table detail" required>'
                + '<input type="text" name="category" placeholder="category (e.g. evpn, bgp)">';
        },
        readForm: function (form) {
            const q = (form.querySelector('[name=query]').value || '').trim();
            if (!q) throw new Error('Query is required');
            return {
                query: q,
                category: (form.querySelector('[name=category]').value || '').trim() || 'general',
            };
        },
    };

    // -- BUGS SCOPE --------------------------------------------------
    R.bugs_scope = {
        label: 'Bug filter',
        hint: 'Scope the Bugs section to this domain (single JQL filter).',
        allowsMultiple: false,
        renderItem: function (item) {
            const p = item.payload || {};
            const status = Array.isArray(p.status_in) && p.status_in.length
                ? p.status_in.join(', ') : 'any';
            return '<div class="dk-row-main">' +
                '<div class="dk-row-title"><strong>Bug scope</strong></div>' +
                '<div class="dk-row-meta">' +
                    (p.project ? '<span class="dk-pill dk-pill-muted">project: ' + _esc(p.project) + '</span>' : '') +
                    '<span class="dk-pill dk-pill-muted">status: ' + _esc(status) + '</span>' +
                '</div>' +
                (p.jql ? '<div class="dk-row-notes"><code>' + _esc(p.jql) + '</code></div>' : '') +
            '</div>';
        },
        renderNew: function () {
            return '<input type="text" name="project" placeholder="SW">'
                + '<input type="text" name="status_in" placeholder="Open, In Progress">'
                + '<input type="text" name="jql" placeholder="custom JQL (optional, overrides)">';
        },
        readForm: function (form) {
            const statuses = (form.querySelector('[name=status_in]').value || '')
                .split(',').map(function (s) { return s.trim(); }).filter(Boolean);
            return {
                project: (form.querySelector('[name=project]').value || '').trim(),
                status_in: statuses,
                jql: (form.querySelector('[name=jql]').value || '').trim(),
            };
        },
    };

    // -- AI SCOPE ----------------------------------------------------
    R.ai_scope = {
        label: 'AI context',
        hint: 'Prompt + pinned chat ids the AI assistant auto-attaches for this domain.',
        allowsMultiple: false,
        renderItem: function (item) {
            const p = item.payload || {};
            const chats = (p.pinned_chat_ids || []).length;
            return '<div class="dk-row-main">' +
                '<div class="dk-row-title"><strong>AI context</strong></div>' +
                '<div class="dk-row-meta">' +
                    '<span class="dk-pill dk-pill-muted">' + chats + ' pinned chats</span>' +
                    (p.auto_attach_bugs
                        ? '<span class="dk-pill dk-pill-ok">bugs attached</span>' : '') +
                '</div>' +
                (p.context_prompt
                    ? '<div class="dk-row-notes">' + _esc(p.context_prompt.slice(0, 240)) +
                      (p.context_prompt.length > 240 ? ' ...' : '') + '</div>' : '') +
            '</div>';
        },
        renderNew: function () {
            return '<textarea name="context_prompt" rows="2" placeholder="You are helping with EVPN MAC mobility tests on PE-1. Prefer show evpn mac-table commands..."></textarea>'
                + '<label class="dk-inline-cb"><input type="checkbox" name="auto_attach_bugs" checked> attach bugs filter</label>';
        },
        readForm: function (form) {
            return {
                context_prompt: form.querySelector('[name=context_prompt]').value || '',
                auto_attach_bugs: !!form.querySelector('[name=auto_attach_bugs]').checked,
                pinned_chat_ids: [],
            };
        },
    };

    // ----------------------------------------------------------------
    // Panel rendering
    // ----------------------------------------------------------------
    //
    // The per-domain knowledge panel is a BODY-LEVEL SIDE DRAWER --
    // it slides out to the right of the #topologies-dropdown-menu
    // rather than expanding inline inside the domain row. This keeps
    // the row list compact (users can see all domains even while a
    // panel is open) and gives the panel enough real-estate for the
    // Workspace tabs + forms without pushing other rows off-screen.
    //
    // Mount location: document.body (fixed-positioned at open time).
    // We tag each drawer with `data-domain-id` so the row can still
    // look up "its" panel via `_panels[domainId]`. The drawer also
    // sets a CSS custom property `--row-accent` on itself so the
    // appearance-editor's live preview can re-tint the drawer header
    // without needing the drawer to be a descendant of the row.
    function _ensurePanel(rowEl, domain) {
        if (!rowEl || !domain) return null;
        let panel = _panels[domain.id];
        if (panel && document.body.contains(panel)) return panel;

        panel = document.createElement('div');
        panel.className = 'domain-knowledge-panel';
        panel.dataset.domainId = domain.id;
        panel.style.display = 'none';

        // Row context -- copy icon/name/color onto the drawer so the
        // header matches without needing a second render pass.
        const domainColor = (typeof domain.color === 'string' && domain.color)
            || rowEl.style.getPropertyValue('--row-accent').trim()
            || '#6366f1';
        const domainName = (typeof domain.name === 'string' && domain.name) || 'Domain';
        const safeName = _esc(domainName);
        panel.style.setProperty('--row-accent', domainColor);

        // Resolve the icon SVG from the live row (the domain object
        // doesn't carry SVG markup, only an icon id). Fallback to a
        // neutral cog if the row somehow lacks its title glyph.
        let iconSvg = '';
        try {
            const rowIcon = rowEl.querySelector('.domain-title > .domain-row-icon')
                || rowEl.querySelector('.domain-title > svg[width="17"]')
                || rowEl.querySelector('.domain-title > svg[width="16"]');
            if (rowIcon) iconSvg = rowIcon.innerHTML;
        } catch (_) { /* best-effort */ }
        if (!iconSvg) iconSvg = '<circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2" fill="none"/>';

        // Keep the domain gear focused: it opens only the feature/image
        // branch monitor. Appearance edits stay in Manage Topology Domains.
        panel.innerHTML = ''
            + '<div class="dk-drawer-header">'
                + '<svg class="dk-drawer-icon" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">' + iconSvg + '</svg>'
                + '<span class="dk-drawer-title">' + safeName + '</span>'
                + '<button type="button" class="dk-close" title="Close" aria-label="Close">'
                    + '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
                        + '<line x1="6" y1="6" x2="18" y2="18"/>'
                        + '<line x1="18" y1="6" x2="6" y2="18"/>'
                    + '</svg>'
                + '</button>'
            + '</div>'
            + '<div class="dk-drawer-scroll">'
                + '<div class="dk-head">'
                    + '<div class="dk-tabs"></div>'
                    + '<div class="dk-head-actions">'
                        + '<button type="button" class="dk-refresh-all" title="Refresh all live items">sync</button>'
                    + '</div>'
                + '</div>'
                + '<div class="dk-tab-body"></div>'
                + '<form class="dk-new" onsubmit="return false">'
                    + '<div class="dk-new-fields"></div>'
                    + '<div class="dk-new-controls">'
                        + '<label class="dk-scope-pick" title="Who should see this?">'
                            + '<select name="visibility">'
                                + '<option value="public">shared with domain</option>'
                                + '<option value="private">only me</option>'
                            + '</select>'
                        + '</label>'
                        + '<button type="submit" class="dk-new-submit">add</button>'
                    + '</div>'
                    + '<div class="dk-new-error" aria-live="polite"></div>'
                + '</form>'
            + '</div>';

        document.body.appendChild(panel);
        _panels[domain.id] = panel;
        _attachPanelHandlers(panel, domain);
        return panel;
    }

    // Re-sync the drawer header when the row's name / icon / colour
    // change (either via the appearance-editor live preview or a full
    // dropdown re-render that discards the row node). Called from
    // mount() and from the onPreview callback.
    function _syncDrawerHeader(panel, rowEl, domain, override) {
        if (!panel) return;
        override = override || {};
        const color = override.color
            || (domain && domain.color)
            || (rowEl && rowEl.style.getPropertyValue('--row-accent').trim())
            || panel.style.getPropertyValue('--row-accent').trim()
            || '#6366f1';
        const name = (typeof override.name === 'string' && override.name !== null)
            ? override.name
            : (domain && domain.name) || 'Domain';
        panel.style.setProperty('--row-accent', color);
        const titleEl = panel.querySelector(':scope > .dk-drawer-header > .dk-drawer-title');
        if (titleEl && typeof name === 'string') titleEl.textContent = name || 'Domain';
        const iconEl = panel.querySelector(':scope > .dk-drawer-header > .dk-drawer-icon');
        if (iconEl) {
            if (override.iconSvg) {
                iconEl.innerHTML = override.iconSvg;
            } else if (rowEl) {
                const rowIcon = rowEl.querySelector('.domain-title > .domain-row-icon')
                    || rowEl.querySelector('.domain-title > svg[width="17"]')
                    || rowEl.querySelector('.domain-title > svg[width="16"]');
                if (rowIcon) iconEl.innerHTML = rowIcon.innerHTML;
            }
        }
    }

    // Compute fixed-position coordinates so the drawer hugs the right
    // edge of #topologies-dropdown-menu, top-aligned with the clicked
    // row when possible. Called on open + on window resize/scroll while
    // the drawer is visible. Clamps the drawer inside the viewport and
    // flips to the left side if there's not enough space on the right
    // (narrow screens or when the dropdown is docked to the right edge).
    function _positionPanel(panel, rowEl) {
        if (!panel || panel.style.display === 'none') return;
        const GAP = 10;
        const MIN_WIDTH = 320;
        const MAX_WIDTH = 380;
        const MARGIN = 12;
        const dd = document.getElementById('topologies-dropdown-menu');
        const anchorRect = rowEl
            ? rowEl.getBoundingClientRect()
            : (dd ? dd.getBoundingClientRect() : null);
        const ddRect = dd ? dd.getBoundingClientRect() : anchorRect;
        if (!ddRect || !anchorRect) return;

        const vw = window.innerWidth || document.documentElement.clientWidth;
        const vh = window.innerHeight || document.documentElement.clientHeight;

        // Drawer width clamped between MIN/MAX, preferring enough room
        // on the right of the dropdown; flip to the left otherwise.
        const rightRoom = Math.max(0, vw - ddRect.right - GAP - MARGIN);
        const leftRoom = Math.max(0, ddRect.left - GAP - MARGIN);
        const width = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, Math.min(rightRoom || MIN_WIDTH, MAX_WIDTH)));

        let left;
        if (rightRoom >= MIN_WIDTH) {
            left = ddRect.right + GAP;
            panel.classList.remove('dk-drawer-left');
        } else if (leftRoom >= MIN_WIDTH) {
            left = ddRect.left - GAP - width;
            panel.classList.add('dk-drawer-left');
        } else {
            // Fallback: slot beneath the dropdown, aligned to its left.
            left = Math.max(MARGIN, ddRect.left);
            panel.classList.remove('dk-drawer-left');
        }

        // Vertical anchor: align to the row top; clamp to viewport so
        // the drawer body always fits.
        const preferredTop = anchorRect.top;
        const maxTop = Math.max(MARGIN, vh - MARGIN - 160); // leave at least 160px of drawer height
        const top = Math.min(Math.max(MARGIN, preferredTop), maxTop);
        const maxHeight = Math.max(180, vh - top - MARGIN);

        panel.style.position = 'fixed';
        panel.style.left = left + 'px';
        panel.style.top = top + 'px';
        panel.style.width = width + 'px';
        panel.style.maxHeight = maxHeight + 'px';
        panel.style.zIndex = '10050'; // above the dropdown's 10000
    }

    // Global close helpers ------------------------------------------------
    // One drawer open at a time: when a user clicks another gear we close
    // the current one before opening the new one. Also close on Esc or
    // clicks outside both the drawer AND the opening row.
    let _activeDrawer = { id: null, rowEl: null, panel: null };
    const _reposHandlers = new WeakMap();

    function _installGlobalClosers() {
        if (document.body.dataset.dkDrawerClosersInstalled) return;
        document.body.dataset.dkDrawerClosersInstalled = '1';
        document.addEventListener('keydown', function (e) {
            if (e.key !== 'Escape') return;
            if (!_activeDrawer.id) return;
            // Don't steal Esc from inputs inside the drawer -- we only
            // close if focus is outside a text-editing element.
            const target = e.target;
            const isEditing = target && (
                target.tagName === 'INPUT' || target.tagName === 'TEXTAREA'
                    || target.isContentEditable
            );
            if (isEditing && _activeDrawer.panel && _activeDrawer.panel.contains(target)) return;
            _closePanel(_activeDrawer.id);
        }, true);
        // Outside-click close (capture so we see clicks before the dropdown
        // eats them). Skip if the click is inside the drawer or inside the
        // anchor row (the gear would immediately re-open us otherwise).
        document.addEventListener('mousedown', function (e) {
            if (!_activeDrawer.id || !_activeDrawer.panel) return;
            const t = e.target;
            if (_activeDrawer.panel.contains(t)) return;
            if (_activeDrawer.rowEl && _activeDrawer.rowEl.contains(t)) return;
            // Clicks on other domain gears are handled by the gear's own
            // click handler (which calls _openPanel on its target domain,
            // which calls _closePanel on us first). Letting those through
            // here would cause a double-close / re-open race.
            const gear = t && t.closest && t.closest('.domain-knowledge-toggle');
            if (gear) return;
            _closePanel(_activeDrawer.id);
        }, true);
        window.addEventListener('resize', function () {
            if (_activeDrawer.id && _activeDrawer.panel && _activeDrawer.rowEl) {
                _positionPanel(_activeDrawer.panel, _activeDrawer.rowEl);
            }
        });
        // Track scroll on the dropdown itself (row moves with it) and
        // on any ancestor with its own scroll context.
        const dd = document.getElementById('topologies-dropdown-menu');
        if (dd) {
            dd.addEventListener('scroll', function () {
                if (_activeDrawer.id && _activeDrawer.panel && _activeDrawer.rowEl) {
                    _positionPanel(_activeDrawer.panel, _activeDrawer.rowEl);
                }
            }, { passive: true });
        }
    }

    // Expand / collapse the appearance accordion. When expanding for
    // the first time we ask FileOps to build the shared name/icon/colour
    // form and slot it into `.dk-appearance-body`; on collapse we throw
    // the form away so the next expand re-reads fresh state from `sec`.
    // Hidden behind `data-expanded` so CSS can animate the chevron and
    // body height without JS touching the style attribute directly.
    function _toggleAppearance(panel, domain, forceState) {
        if (!panel) return;
        const wrap = panel.querySelector(':scope > .dk-appearance');
        if (!wrap) return;
        const head = wrap.querySelector(':scope > .dk-appearance-head');
        const bodyEl = wrap.querySelector(':scope > .dk-appearance-body');
        if (!head || !bodyEl) return;

        const currentlyExpanded = wrap.dataset.expanded === 'true';
        const shouldExpand = (typeof forceState === 'boolean')
            ? forceState
            : !currentlyExpanded;

        if (!shouldExpand) {
            wrap.dataset.expanded = 'false';
            head.setAttribute('aria-expanded', 'false');
            bodyEl.hidden = true;
            bodyEl.innerHTML = '';
            return;
        }

        wrap.dataset.expanded = 'true';
        head.setAttribute('aria-expanded', 'true');
        bodyEl.hidden = false;

        if (bodyEl.firstChild) return; // already populated

        const editor = window.topologyEditor || window.editor || null;
        if (!editor || !window.FileOps
                || typeof window.FileOps._buildDomainAppearanceForm !== 'function') {
            bodyEl.innerHTML = '<div class="dk-appearance-fallback">Appearance editor is unavailable. Open Manage Topology Domains instead.</div>';
            return;
        }
        // The drawer lives on <body>, not inside the row, so we can't
        // use .closest('.custom-section-category') here. Fetch it from
        // the currently-active drawer tracker (set by _openPanel) or
        // re-discover via the known dropdown menu.
        let rowEl = (_activeDrawer.id === domain.id && _activeDrawer.rowEl)
            ? _activeDrawer.rowEl
            : null;
        if (!rowEl) {
            const dd = document.getElementById('topologies-dropdown-menu');
            if (dd) {
                rowEl = dd.querySelector('.custom-section-category[data-section-id="' + domain.id + '"]');
            }
        }
        if (!rowEl) {
            bodyEl.innerHTML = '<div class="dk-appearance-fallback">Domain row missing; try re-opening the Topologies menu.</div>';
            return;
        }

        // Resolve the latest section snapshot. The re-render that
        // follows a domain-domains:changed event replaces rowEl but
        // this panel may still hold a stale `domain` capture; pull
        // fresh data from the editor's in-memory cache when possible.
        let sec = domain;
        if (Array.isArray(editor._customSections)) {
            const fresh = editor._customSections.find(s => s && s.id === domain.id);
            if (fresh) sec = fresh;
        }

        const form = window.FileOps._buildDomainAppearanceForm(editor, sec, rowEl, {
            showCancel: false,
            onClose: function (/* reason */) {
                // Re-render dispatched by a successful save usually
                // destroys this panel outright; the collapse call
                // below is idempotent so it's safe to run either way.
                _toggleAppearance(panel, domain, false);
            },
            onPreview: function (change) {
                // Live-preview hook: repaint the drawer header so the
                // colour swatches / icon picker / name field update the
                // visible domain identity in real time, not just after
                // save. `change` is `{ color, icon, name }` with any
                // field null when that field wasn't the one that moved.
                const override = {};
                if (change && typeof change.color === 'string') override.color = change.color;
                if (change && typeof change.name === 'string')  override.name  = change.name;
                if (change && typeof change.icon === 'string') {
                    const icons = (window.FileOps && typeof window.FileOps._sectionIcons === 'function')
                        ? window.FileOps._sectionIcons() : [];
                    const ic = icons.find(function (i) { return i.id === change.icon; });
                    if (ic) override.iconSvg = ic.svg;
                }
                _syncDrawerHeader(panel, rowEl, sec, override);
            },
        });
        if (form) bodyEl.appendChild(form);
        // Focus the name input so the accordion flow feels as
        // responsive as the old hover-reveal gear.
        if (!sec.builtin) {
            const nameInput = form && form.querySelector('.dq-name');
            if (nameInput) {
                setTimeout(function () {
                    try { nameInput.focus({ preventScroll: true }); } catch (_) {}
                }, 0);
            }
        }
    }

    function _attachPanelHandlers(panel, domain) {
        // Appearance accordion header -- toggles the rename / icon /
        // colour form that replaces the retired standalone gear.
        const appearanceHead = panel.querySelector('.dk-appearance-head');
        if (appearanceHead) {
            appearanceHead.addEventListener('click', function (e) {
                e.stopPropagation();
                _toggleAppearance(panel, domain);
            });
        }
        const closeBtn = panel.querySelector('.dk-close');
        if (closeBtn) closeBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            _closePanel(domain.id);
        });
        const syncBtn = panel.querySelector('.dk-refresh-all');
        if (syncBtn) syncBtn.addEventListener('click', async function (e) {
            e.stopPropagation();
            syncBtn.disabled = true;
            syncBtn.classList.add('dk-spinning');
            try {
                await _refreshAll(domain.id, null);
                await _loadAndRender(panel, domain);
                _toast('Refreshed domain knowledge', 'info');
            } catch (err) {
                console.warn('[domain-knowledge] refresh-all failed', err);
                _toast('Refresh failed: ' + err.message, 'warn');
            } finally {
                syncBtn.disabled = false;
                syncBtn.classList.remove('dk-spinning');
            }
        });

        const newForm = panel.querySelector('.dk-new');
        newForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            e.stopPropagation();
            await _submitNew(panel, domain);
        });
    }

    function _setActiveKind(panel, kind) {
        panel.dataset.activeKind = kind;
        const st = _state[panel.dataset.domainId];
        if (st) st.activeKind = kind;
        panel.querySelectorAll('.dk-tab').forEach(function (t) {
            t.classList.toggle('dk-tab-active', t.dataset.kind === kind);
        });
        _renderTabBody(panel);
        _renderNewForm(panel);
    }

    function _renderTabs(panel) {
        const st = _state[panel.dataset.domainId] || {};
        const kinds = st.kinds || [];
        const active = panel.dataset.activeKind || st.activeKind || (kinds[0] && kinds[0].kind);
        const counts = Object.create(null);
        (st.items || []).forEach(function (it) {
            counts[it.kind] = (counts[it.kind] || 0) + 1;
        });
        const html = kinds.map(function (k) {
            const c = counts[k.kind] || 0;
            const isActive = k.kind === active;
            return '<button type="button" class="dk-tab' + (isActive ? ' dk-tab-active' : '') + '" data-kind="' + _esc(k.kind) + '" title="' + _esc(k.description || '') + '">'
                + '<span class="dk-tab-icon">' + _kindIcon(k.kind) + '</span>'
                + '<span class="dk-tab-label">' + _esc((R[k.kind] && R[k.kind].label) || k.label) + '</span>'
                + (c > 0 ? '<span class="dk-tab-count">' + c + '</span>' : '')
                + '</button>';
        }).join('');
        panel.querySelector('.dk-tabs').innerHTML = html;
        panel.querySelectorAll('.dk-tab').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                _setActiveKind(panel, btn.dataset.kind);
            });
        });
    }

    function _renderTabBody(panel) {
        const st = _state[panel.dataset.domainId] || {};
        const active = panel.dataset.activeKind || 'branch';
        const body = panel.querySelector('.dk-tab-body');
        const renderer = R[active];
        if (!renderer) {
            body.innerHTML = '<div class="dk-empty">Unsupported kind</div>';
            return;
        }
        body.dataset.activeKind = active;
        const rows = (st.items || []).filter(function (it) { return it.kind === active; });
        if (!rows.length) {
            body.innerHTML = '<div class="dk-empty"><em>No ' + _esc(renderer.label.toLowerCase()) + ' yet.</em> ' + _esc(renderer.hint || '') + '</div>';
            return;
        }
        const canWrite = st.permission === 'write' || !st.isSharedIn;
        body.innerHTML = rows.map(function (item) {
            const isOwnRow = !!item.editable;
            const scopeBadge = item.visibility === 'private'
                ? '<span class="dk-pill dk-pill-private" title="Private to you">private</span>'
                : (st.isSharedIn
                    ? '<span class="dk-pill dk-pill-shared" title="Authored by ' + _esc(item.author || st.owner) + '">shared</span>'
                    : '');
            const actions = isOwnRow
                ? '<div class="dk-row-actions">'
                    + (renderer && R[item.kind] && R[item.kind] !== R.note && R[item.kind] !== R.confluence && R[item.kind] !== R.cli_preset && R[item.kind] !== R.device && R[item.kind] !== R.bugs_scope && R[item.kind] !== R.ai_scope
                        ? '<button type="button" class="dk-act dk-refresh" title="Refresh">&#x21bb;</button>' : '')
                    + '<button type="button" class="dk-act dk-remove" title="Remove">&times;</button>'
                + '</div>'
                : '';
            return '<div class="dk-row" data-kind="' + _esc(item.kind) + '" data-key="' + _esc(item.key) + '" data-visibility="' + _esc(item.visibility) + '">'
                + renderer.renderItem(item)
                + scopeBadge
                + actions
            + '</div>';
        }).join('');

        body.querySelectorAll('.dk-row').forEach(function (rowEl) {
            const kind = rowEl.dataset.kind;
            const key = rowEl.dataset.key;
            const vis = rowEl.dataset.visibility;
            const rmBtn = rowEl.querySelector('.dk-remove');
            if (rmBtn) rmBtn.addEventListener('click', async function (e) {
                e.stopPropagation();
                rmBtn.disabled = true;
                try {
                    await _deleteItem(panel.dataset.domainId, kind, key, vis);
                    await _loadAndRender(panel, { id: panel.dataset.domainId });
                } catch (err) {
                    _toast('Delete failed: ' + err.message, 'warn');
                    rmBtn.disabled = false;
                }
            });
            const rfBtn = rowEl.querySelector('.dk-refresh');
            if (rfBtn) rfBtn.addEventListener('click', async function (e) {
                e.stopPropagation();
                rfBtn.disabled = true;
                rfBtn.classList.add('dk-spinning');
                try {
                    await _refreshItem(panel.dataset.domainId, kind, key, vis);
                    await _loadAndRender(panel, { id: panel.dataset.domainId });
                } catch (err) {
                    _toast('Refresh failed: ' + err.message, 'warn');
                } finally {
                    rfBtn.disabled = false;
                    rfBtn.classList.remove('dk-spinning');
                }
            });
        });
        // Not strictly used yet -- kept so the hybrid-sharing UI can grey out
        // the "+ Add public" form on read-only shared-in domains.
        void canWrite;
    }

    function _renderNewForm(panel) {
        const st = _state[panel.dataset.domainId] || {};
        const active = panel.dataset.activeKind || 'branch';
        const renderer = R[active];
        const fields = panel.querySelector('.dk-new-fields');
        const submit = panel.querySelector('.dk-new-submit');
        const visSelect = panel.querySelector('.dk-new select[name=visibility]');
        fields.innerHTML = renderer ? renderer.renderNew() : '';
        panel.querySelector('.dk-new-error').textContent = '';

        // "Only one" kinds: if a row already exists, switch submit to Update.
        const allowsMultiple = !renderer || renderer.allowsMultiple !== false;
        const existing = (st.items || []).filter(function (x) { return x.kind === active; });
        if (!allowsMultiple && existing.length) {
            // Prefill the form with existing payload so "add" becomes "update".
            const p = existing[0].payload || {};
            Object.keys(p).forEach(function (k) {
                const el = fields.querySelector('[name=' + CSS.escape(k) + ']');
                if (!el) return;
                if (el.type === 'checkbox') el.checked = !!p[k];
                else el.value = Array.isArray(p[k]) ? p[k].join(', ') : (p[k] || '');
            });
            submit.textContent = 'update';
            panel.dataset.updateKey = existing[0].key;
            panel.dataset.updateVisibility = existing[0].visibility || 'public';
        } else {
            submit.textContent = 'add';
            delete panel.dataset.updateKey;
            delete panel.dataset.updateVisibility;
        }

        // Hybrid-sharing hint: when the viewer only has read-share on a
        // shared-in domain, default to private and show why.
        if (visSelect) {
            if (st.isSharedIn && st.permission !== 'write') {
                visSelect.value = 'private';
                visSelect.querySelector('option[value=public]').disabled = true;
                visSelect.title = 'You only have read access; new items are saved as your private annotations';
            } else {
                const opts = visSelect.querySelectorAll('option');
                opts.forEach(function (o) { o.disabled = false; });
                visSelect.title = '';
            }
        }
    }

    async function _submitNew(panel, domain) {
        const st = _state[domain.id] || {};
        const active = panel.dataset.activeKind || 'branch';
        const renderer = R[active];
        const form = panel.querySelector('.dk-new');
        const err = panel.querySelector('.dk-new-error');
        err.textContent = '';
        let payload;
        try {
            payload = renderer.readForm(form);
        } catch (e) {
            err.textContent = e.message;
            return;
        }
        const visibility = form.querySelector('[name=visibility]').value || 'public';
        const updateKey = panel.dataset.updateKey;
        const submit = panel.querySelector('.dk-new-submit');
        submit.disabled = true;
        try {
            await _saveItem(domain.id, {
                kind: active,
                payload: payload,
                visibility: visibility,
                key: updateKey || undefined,
            }, updateKey || null);
            form.querySelectorAll('input,textarea').forEach(function (el) {
                if (el.type !== 'checkbox') el.value = '';
                else el.checked = el.defaultChecked;
            });
            await _loadAndRender(panel, domain);
            _toast('Saved', 'info');
        } catch (e) {
            err.textContent = e.message;
        } finally {
            submit.disabled = false;
        }
    }

    function _applyRenderState(panel, domain, resp, kinds) {
        const domainId = domain.id;
        const visibleKinds = _monitorKinds(kinds);
        const visibleKindIds = new Set(visibleKinds.map(function (k) { return k.kind; }));
        const visibleItems = (resp.items || []).filter(function (it) {
            return visibleKindIds.has(it.kind);
        });
        // Preserve sticky open/activeKind flags we may have set earlier.
        const prev = _state[domainId] || {};
        const prevKind = prev.activeKind || panel.dataset.activeKind || 'branch';
        const activeKind = visibleKindIds.has(prevKind) ? prevKind : 'branch';
        _state[domainId] = {
            permission: resp.permission,
            isSharedIn: !!resp.is_shared_in,
            owner: resp.owner,
            items: visibleItems,
            kinds: visibleKinds,
            lastFetch: Date.now(),
            // Sticky UI state -- survives dropdown re-renders.
            open: prev.open === true,
            activeKind: activeKind,
            wsDebounceTimer: prev.wsDebounceTimer || null,
        };
        panel.dataset.activeKind = _state[domainId].activeKind;
        _renderTabs(panel);
        _renderTabBody(panel);
        _renderNewForm(panel);
        // Freshness banner when any live row is older than the threshold.
        const stale = visibleItems.some(function (it) {
            const spec = visibleKinds.find(function (k) { return k.kind === it.kind; });
            if (!spec || !spec.supports_live) return false;
            const ts = it.payload && it.payload.last_checked_at;
            if (!ts) return true;
            const parsed = Date.parse(ts);
            if (!parsed) return true;
            return (Date.now() - parsed) > STALE_HINT_MS;
        });
        panel.classList.toggle('dk-stale', stale);
    }

    async function _loadAndRender(panel, domain) {
        try {
            const resp = await _fetchItems(domain.id);
            const kinds = await _loadKinds();
            _applyRenderState(panel, domain, resp, kinds);
        } catch (e) {
            console.warn('[domain-knowledge] load failed', e);
            const body = panel.querySelector('.dk-tab-body');
            if (body) {
                body.innerHTML =
                    '<div class="dk-empty dk-error">Failed to load: ' + _esc(e.message) + '</div>';
            }
        }
    }

    function _closePanel(domainId) {
        const panel = _panels[domainId];
        if (!panel) return;
        // Animate out first -- the CSS .dk-drawer-closing class plays
        // the slide-out transition; we flip display:none after it
        // settles so the next open starts from a fresh slide-in.
        panel.classList.add('dk-drawer-closing');
        panel.classList.remove('dk-drawer-open');
        setTimeout(function () {
            if (panel.classList.contains('dk-drawer-closing')) {
                panel.style.display = 'none';
                panel.classList.remove('dk-drawer-closing');
            }
        }, 180);
        // Remember "closed" as sticky state so dropdown re-renders don't flip
        // us back open.
        if (_state[domainId]) _state[domainId].open = false;
        // Toggle the dropdown-row button so the user knows it's closed.
        // The row is no longer the panel's DOM parent, so look it up
        // via the known dropdown menu.
        const dd = document.getElementById('topologies-dropdown-menu');
        if (dd) {
            const row = dd.querySelector('.custom-section-category[data-section-id="' + domainId + '"]');
            if (row) {
                const btn = row.querySelector('.domain-knowledge-toggle');
                if (btn) btn.classList.remove('domain-knowledge-toggle-open');
            }
        }
        if (_activeDrawer.id === domainId) {
            _activeDrawer = { id: null, rowEl: null, panel: null };
        }
    }

    async function _openPanel(panel, domain, rowElOverride) {
        // Close any other open drawer first -- one at a time.
        if (_activeDrawer.id && _activeDrawer.id !== domain.id) {
            _closePanel(_activeDrawer.id);
        }
        _installGlobalClosers();

        const dd = document.getElementById('topologies-dropdown-menu');
        const rowEl = rowElOverride
            || (dd && dd.querySelector('.custom-section-category[data-section-id="' + domain.id + '"]'))
            || null;

        panel.style.display = 'flex';
        // Force reflow so the slide-in transition actually plays when
        // the drawer was display:none one frame ago.
        panel.offsetHeight; // eslint-disable-line no-unused-expressions
        panel.classList.add('dk-drawer-open');
        panel.classList.remove('dk-drawer-closing');

        _positionPanel(panel, rowEl);
        _syncDrawerHeader(panel, rowEl, domain);
        _activeDrawer = { id: domain.id, rowEl: rowEl, panel: panel };

        // Persist so a later dropdown re-render can auto-restore.
        if (!_state[domain.id]) _state[domain.id] = {};
        _state[domain.id].open = true;
        if (rowEl) {
            const btn = rowEl.querySelector('.domain-knowledge-toggle');
            if (btn) btn.classList.add('domain-knowledge-toggle-open');
        }
        if (panel.dataset.loaded) return;
        panel.dataset.loaded = '1';

        // First paint: render from the cached DB as fast as possible so the
        // user sees SOMETHING immediately. Then kick off a live refresh
        // whose response includes the merged post-refresh items -- we pipe
        // that straight into _applyRenderState so the panel updates in one
        // round-trip instead of a re-fetch.
        await _loadAndRender(panel, domain);
        try {
            const kinds = await _loadKinds();
            const resp = await _refreshAll(domain.id, null);
            if (resp && resp.items) {
                _applyRenderState(panel, domain, resp, kinds);
            }
        } catch (err) {
            // Best-effort. The background poller will catch up on its own.
            console.debug('[domain-knowledge] refresh-all on open failed', err);
        }
    }

    // ----------------------------------------------------------------
    // Public mounting
    // ----------------------------------------------------------------
    //
    // `mount(row, domain)` is idempotent: it wires up the toggle button
    // and pre-builds the panel shell but does NOT auto-open (to keep
    // the dropdown compact). Panel opens on toggle-button click.

    function mount(rowEl, domain) {
        if (!rowEl || !domain) return null;
        // Synthetic "Shared with me" has no knowledge.
        if (domain.id === '__shared_with_me' || domain.is_shared_with_me_domain) {
            return null;
        }
        const panel = _ensurePanel(rowEl, domain);
        if (!panel) return null;
        // Dropdown re-renders rebuild the row node but reuse the same
        // drawer (which lives on document.body). Refresh the header
        // to pick up any name/icon/color change that prompted the
        // re-render, and rebind _activeDrawer.rowEl so scroll-follow
        // tracks the new row.
        _syncDrawerHeader(panel, rowEl, domain);
        if (_activeDrawer.id === domain.id) {
            _activeDrawer.rowEl = rowEl;
            _positionPanel(panel, rowEl);
        }
        ensureDropdownButton(rowEl, domain, panel);
        // Re-open automatically if the user had this panel open before the
        // dropdown was re-rendered. Without this the user loses their
        // place every time /api/sections/reorder or a domain refresh fires.
        const sticky = _state[domain.id];
        if (sticky && sticky.open === true && !panel.classList.contains('dk-drawer-open')) {
            // Reset the panel-local "loaded" flag since DOM was rebuilt, then
            // open asynchronously to avoid blocking the dropdown render.
            delete panel.dataset.loaded;
            setTimeout(function () { _openPanel(panel, domain, rowEl); }, 0);
        }
        return panel;
    }

    // Settings gear icon for the per-domain knowledge/settings toggle.
    // Inline SVG so we don't ship a separate asset; shapes match the
    // rest of the dropdown-row icon family (14x14 viewBox, 1.5 stroke).
    const _DOMAIN_SETTINGS_GEAR_SVG =
        '<svg viewBox="0 0 24 24" width="14" height="14" fill="none"'
        + ' stroke="currentColor" stroke-width="1.8" stroke-linecap="round"'
        + ' stroke-linejoin="round" aria-hidden="true">'
        + '<circle cx="12" cy="12" r="3"/>'
        + '<path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>'
        + '</svg>';

    function ensureDropdownButton(rowEl, domain, panelOverride) {
        const titleBar = rowEl.querySelector(':scope > .domain-title')
            || rowEl.querySelector(':scope > .section-title');
        if (!titleBar) return null;
        // If we've already wired the button, just keep the reference fresh.
        let btn = titleBar.querySelector('.domain-knowledge-toggle');
        if (!btn) {
            btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'domain-knowledge-toggle';
            // Single compact gear: opens only the branch/image monitor.
            // Appearance edits live in Manage Topology Domains, keeping
            // per-domain row settings from becoming a catch-all drawer.
            btn.title = 'Feature branch image monitor';
            btn.setAttribute('aria-label', 'Feature branch image monitor');
            // Settings gear (replaces the older fork/branch glyph) so the
            // affordance matches what users expect from a "settings" icon.
            btn.innerHTML = _DOMAIN_SETTINGS_GEAR_SVG;
            // Prefer to slot the button immediately before the chevron so
            // visual grouping stays: [name] ... [+ Bug] [settings] [chevron].
            // Fall back to appending if the chevron is missing (defensive --
            // some shared-in rows render without it).
            const chevron = titleBar.querySelector('.domain-chevron');
            if (chevron && chevron.parentElement === titleBar) {
                titleBar.insertBefore(btn, chevron);
            } else {
                titleBar.appendChild(btn);
            }
            // Replace the browser's slow native tooltip (~1s delay, hard
            // edges) with the app's custom fast-fade hover bubble. The
            // tooltip bubble appears almost immediately on mouseenter and
            // fades out cleanly on mouseleave (see FileOps._attachHoverTip).
            try {
                if (window.FileOps && typeof window.FileOps._attachHoverTip === 'function') {
                    window.FileOps._attachHoverTip(btn, { offset: 6 });
                }
            } catch (_) { /* non-fatal -- fall back to native title */ }
            btn.addEventListener('click', async function (e) {
                e.stopPropagation();
                e.preventDefault();
                const panel = panelOverride || _panels[domain.id] || _ensurePanel(rowEl, domain);
                if (!panel) return;
                // Clicking the SAME row's gear while its drawer is open
                // closes the drawer (toggle semantics). Clicking a
                // different row's gear just opens that row's drawer
                // (the _openPanel() call will close the previous one).
                const isOpenForThisRow = panel.classList.contains('dk-drawer-open')
                    && _activeDrawer.id === domain.id;
                if (isOpenForThisRow) {
                    _closePanel(domain.id);
                } else {
                    await _openPanel(panel, domain, rowEl);
                }
            });
        }
        return btn;
    }

    async function refresh(domainId) {
        const panel = _panels[domainId];
        if (!panel) return;
        await _loadAndRender(panel, { id: domainId });
    }

    // ----------------------------------------------------------------
    // Live updates via event bus
    // ----------------------------------------------------------------
    //
    // Burst-coalesce: when the background poller finishes a cycle with 20
    // branches attached it emits 20 events in quick succession. Doing 20
    // list fetches + renders per burst is wasteful and flickers the panel.
    // We defer to `WS_UPDATE_DEBOUNCE_MS` after the LAST event and then
    // do a single reload.
    function _scheduleDebouncedReload(domainId) {
        const st = _state[domainId] = _state[domainId] || {};
        if (st.wsDebounceTimer) clearTimeout(st.wsDebounceTimer);
        st.wsDebounceTimer = setTimeout(function () {
            st.wsDebounceTimer = null;
            // Re-resolve through _panels -- the dropdown may have been
            // rebuilt between the event and this callback, in which case
            // _panels[domainId] points at the current live DOM node.
            const panel = _panels[domainId];
            if (!panel) return;
            // Only reload if the panel is actually visible; no point
            // hitting the network for a panel the user closed.
            if (panel.style.display === 'none' || !st.open) return;
            _loadAndRender(panel, { id: domainId });
        }, WS_UPDATE_DEBOUNCE_MS);
    }

    window.addEventListener('topology:event:domain.knowledge.updated', function (ev) {
        const detail = ev.detail || {};
        const domainId = detail.domain_id || (detail.event && detail.event.domain_id);
        if (!domainId) return;
        _scheduleDebouncedReload(domainId);
    });

    // When the user picks a new active domain we could preload its panel
    // data, but we currently only pre-open on explicit click to keep the
    // dropdown snappy for users with many domains.
    document.addEventListener('topology-domains:changed', function () {
        // Prune state for domains that no longer exist so memory doesn't
        // grow across long sessions.
        if (!window.TopologyDomains) return;
        const live = new Set((window.TopologyDomains.getDomains() || []).map(function (d) { return d.id; }));
        Object.keys(_state).forEach(function (id) {
            if (!live.has(id)) delete _state[id];
        });
    });

    window.TopologyDomainKnowledge = {
        mount: mount,
        ensureDropdownButton: ensureDropdownButton,
        refresh: refresh,
    };
})();
