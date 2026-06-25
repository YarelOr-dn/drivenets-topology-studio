/**
 * topology-ai.js -- In-app AI assistant drawer.
 *
 * UX: a persistent launcher pill in the bottom-left bar (`#ai-chat-launcher`,
 * sibling of the current-topology indicator) toggles a right-side
 * FLOATING resizable drawer (320-720px wide, no backdrop). The canvas
 * stays interactive while the drawer is open -- this is a utility panel
 * that coexists with normal work, not a blocking modal. "A" toggles it
 * from anywhere; Escape closes it when focused.
 *
 * Flow for topology generation (Phase A):
 *   1. User clicks the pill or hits "A" (outside input fields) -> drawer opens.
 *   2. First time: inline "Set up" form collects provider (Claude / OpenAI),
 *      API key, optional model + base_url. POSTed to PUT /api/users/me/
 *      ai-config. Key is stored per-user, mode 0600, never echoed back.
 *   3. User types "build me a 4-leaf 2-spine clos with VRRP on the border"
 *      and hits Enter (or clicks "Create topology").
 *   4. Frontend calls POST /api/ai/chat with {messages, canvas: snapshot}.
 *      Server builds a knowledge-digest + live-context system prompt,
 *      calls the LlmClient (Anthropic / OpenAI), normalizes tool calls.
 *   5. If the model emits create_topology, the server saves the result
 *      under the built-in __ai domain and returns {tool_calls: [{name:
 *      create_topology, status: saved, topology, section_id, filename,
 *      display_name}]}.
 *   6. The drawer renders a preview card with two actions:
 *        * "Save only"  -- keep the topology in __ai; user loads later.
 *        * "Save + Load" -- immediately loads it on the canvas and
 *          refreshes the Topologies dropdown, mirroring Bugs flow.
 *
 * Mutual exclusion: opening Bugs / Share inline panels closes the AI
 * drawer (strict per user decision). Opening the AI drawer closes any
 * open Bugs/Share inline panel. Only one help/chat surface is active at
 * a time so the user never has to hunt for the state that owns focus.
 *
 * Persistence: open/closed state, drawer width (px) and the last active
 * chat session id are mirrored in localStorage under keys prefixed
 * `tpai.` so a reload restores the same layout. No chat history is
 * persisted client-side in Phase A; the server returns a fresh response
 * per request. (Phase B will add per-user SQLite history with chat_ids.)
 *
 * Multi-user: every API call above routes through window.TopologyAuth.
 * authFetch which attaches the JWT. The server reads the user's
 * ~/.topology_users/<user>/ai_config.json and routes the chat to the
 * LLM provider configured by THAT user. Nothing leaks across users.
 *
 * Dependencies:
 *   - window.TopologyAuth.authFetch (auth-bearing fetch)
 *   - window.topologyEditor (aliased via _editor() for forward-compat)
 *     -- loadTopologyFromData / showToast (canvas + UX)
 *   - window.FileOps.updateTopologyIndicator (bottom-left active bar)
 *   - window.FileOps._renderCustomSectionsInDropdown (optional; refresh)
 *   - window.TopologyBugs.close / window.TopologyShare.close (strict
 *     mutual exclusion)
 */
(function () {
    'use strict';

    var LAUNCHER_ID = 'ai-chat-launcher';
    var DRAWER_ID   = 'ai-drawer';
    var LS = {
        open: 'tpai.drawer.open',
        width: 'tpai.drawer.width',
        chatId: 'tpai.chat.id',
    };
    var MIN_WIDTH = 320;
    var MAX_WIDTH = 720;
    var DEFAULT_WIDTH = 420;

    // Provider presets (mirrors ai/service.PROVIDER_DEFAULTS). Kept in
    // sync by hand; when a provider's "recommended" model changes, bump
    // both files and the cache buster. The token hint helps the user
    // recognize which key was last saved without exposing the secret.
    //
    // `get_key_url` is the provider's "create API key" page -- wired up
    // as a "Get a key" shortcut next to the API-key input (mirrors the
    // Bugs panel's Atlassian "get one ->" link). Per-user intent: every
    // logged-in user opens the provider's console under their OWN
    // provider account and pastes the resulting key into THIS drawer,
    // where it lands in ~/.topology_users/<user>/ai_config.json.
    // Curated per-provider model list. The `label` is what we show in the
    // dropdown (human-friendly); the object key is the exact API model id
    // that gets persisted server-side and sent to the provider. The first
    // entry of each list is the default and is used whenever the user
    // switches providers -- we never carry a model name across providers,
    // since that was the root cause of the "Claude provider + OpenAI key +
    // claude-3-5-sonnet-latest" misconfiguration.
    //
    // The special __custom__ id is handled in _renderConfigPanel: selecting
    // it swaps the dropdown for a free-text input so compatible-endpoint
    // users (Together, Groq, self-hosted vLLM, etc.) can type any model.
    // 2026-04-22: per owner decision, the AI assistant is locked to
    // Google Gemini. Removing other providers (Anthropic, OpenAI, Groq,
    // Ollama) from the UI avoids the "my stale Llama key is still
    // selected" footgun and makes the shared-key experience the norm.
    //
    // IMPORTANT: the BACKEND still contains AnthropicClient, OpenAiClient,
    // Groq and Ollama presets under ai/service.py. That code is kept as
    // a dormant safety net so existing per-user configs don't break
    // mid-request if someone disables the override or switches back;
    // the frontend just never surfaces those provider choices now. If
    // you need to re-enable another provider in the UI, add it back
    // here -- the dispatch pipeline will light up automatically.
    var PROVIDER_PRESETS = {
        // Google Gemini (OpenAI-compatible free-tier endpoint). Keys
        // are "AIza..." issued from https://aistudio.google.com/app/apikey
        // -- no billing required. When the server operator exports
        // GEMINI_API_KEY in the process environment, the backend
        // resolver swaps the shared key in at request time so a blank
        // field still works.
        gemini: {
            label: 'Google Gemini (free tier)',
            short_label: 'Gemini',
            placeholder: 'AIza...',
            tokensHint: 'FREE tier: ~15 RPM, 1M TPM on Flash. No billing required.',
            get_key_url: 'https://aistudio.google.com/app/apikey',
            get_key_host: 'aistudio.google.com',
            steps: 'Sign in with Google -> Get API key -> Create API key -> copy AIza...',
            key_prefix: 'AIza',
            default_base_url: 'https://generativelanguage.googleapis.com/v1beta/openai',
            // 2026-04-24s -- reordered so `gemini-2.5-flash-lite` is the
            // first (default) pick for new users. The `-lite` model has a
            // SEPARATE daily quota bucket from `-flash`, is ~2x faster,
            // and is more than capable for the app's tool-calling path
            // (domain create, apply_canvas_edits, small topology
            // generations). Users who want richer reasoning can still
            // pick `gemini-2.5-flash` or `-pro` below. Previous default
            // (`gemini-2.5-flash`) pushed every new user straight at the
            // same quota bucket the error-card auto-switch falls back
            // from -- starting on lite sidesteps that.
            // 2026-04-24t -- `gemini-flash-latest` is now the default
            // pick. It's a Google-managed alias that routes to the
            // newest-available flash model with capacity (skips the
            // per-model daily quota traps that pinned users to a dead
            // bucket for 24h). The backend also walks this ladder
            // automatically on 402/429/503 so the user doesn't have
            // to manually switch models mid-session.
            models: [
                { id: 'gemini-flash-latest',        label: 'Gemini Flash (latest)',       note: 'Default -- Google-routed alias, dodges per-model quota caps' },
                { id: 'gemini-flash-lite-latest',   label: 'Gemini Flash Lite (latest)',  note: 'Faster + lighter alias, own routing bucket' },
                { id: 'gemini-2.5-flash-lite',      label: 'Gemini 2.5 Flash Lite',       note: 'Pinned 2.5-lite -- separate daily quota bucket' },
                { id: 'gemini-2.5-flash',           label: 'Gemini 2.5 Flash',            note: 'Pinned 2.5 -- heavier reasoning, separate bucket' },
                { id: 'gemini-2.0-flash',           label: 'Gemini 2.0 Flash',            note: 'GA, proven stable' },
                { id: 'gemini-2.5-pro',             label: 'Gemini 2.5 Pro',              note: 'Higher quality, tighter quota' },
            ],
        },
    };

    // Legacy provider names that may still be in a user's
    // ai_config.json on disk. The config loader silently rewrites
    // them to gemini so a stale groq / anthropic / openai / ollama
    // config doesn't land the drawer in a "provider not found" state.
    var LEGACY_PROVIDERS_TO_MIGRATE = ['anthropic', 'openai', 'groq', 'ollama', 'claude', 'azure'];

    // Back-compat shim: lots of legacy code paths (badges, tool-save meta,
    // debug output) reference `preset.model` as a single string. Treat the
    // first entry of `models` as the canonical default so nothing breaks.
    (function () {
        Object.keys(PROVIDER_PRESETS).forEach(function (k) {
            var p = PROVIDER_PRESETS[k];
            if (!p.model && Array.isArray(p.models) && p.models[0]) {
                p.model = p.models[0].id;
            }
        });
    })();

    // Does `modelId` appear in the provider's curated list? Decides whether
    // to select it natively in the <select> or drop into "Custom model".
    function _isKnownProviderModel(providerId, modelId) {
        var p = PROVIDER_PRESETS[providerId];
        if (!p || !Array.isArray(p.models) || !modelId) return false;
        for (var i = 0; i < p.models.length; i += 1) {
            if (p.models[i].id === modelId) return true;
        }
        return false;
    }

    // Detect which provider a pasted key most likely belongs to. Used
    // to warn the user BEFORE they hit Save with a mismatched combo
    // (Claude provider + OpenAI key is the common footgun we saw in
    // the initial rollout -- Anthropic returns 502 "upstream" which
    // looks scary). `sk-ant-` is Anthropic's canonical prefix; `sk-`
    // without `ant-` is almost always OpenAI (also used by OpenAI-
    // compatible providers via the `base_url` override). We deliberately
    // do NOT block submission -- compatible endpoints can reuse the
    // sk- prefix, so we just surface the mismatch and offer a one-click
    // switch.
    function _detectProviderFromKey(rawKey) {
        var key = (rawKey || '').trim();
        if (!key) return null;
        // Gemini-only mode (2026-04-22): we still detect AIza so the
        // key field can show a positive "looks like a Gemini key"
        // confirmation, but we no longer suggest switching TO another
        // provider because the UI doesn't support them. Returning a
        // non-gemini provider id here would make the mismatch banner
        // offer a "Switch to Anthropic" button that we've removed.
        if (key.indexOf('AIza') === 0) return 'gemini';
        return null;
    }

    // In-memory state. The drawer DOM is built lazily the first time the
    // user opens it so pages that never touch AI don't pay the DOM cost.
    var _drawerBuilt = false;
    var _drawerEl = null;
    var _launcherEl = null;
    var _aiConfig = { configured: null, provider: '', model: '', token_hint: '', saved_at: 0, shared_gemini: false, forced: false };
    var _messages = []; // [{role, content, tool_calls?, _id}]
    // Remember the last outbound user prompt so the "Retry" button on
    // error cards (quota, rate-limit, timeout) can resend without the
    // user having to retype. Cleared on conversation clear.
    var _lastUserMessage = '';
    var _msgCounter = 0;
    var _sending = false;

    // --------------------------------------------------------------
    //   Conversation state (per-user multi-conversation persistence)
    //
    //   The server is the source of truth (see
    //   /api/ai/conversations in serve.py + ai/conversation_store.py),
    //   but we mirror the last N conversations into localStorage so
    //   the drawer paints instantly when the user reopens it instead
    //   of blocking on a network round-trip. The cache is keyed by
    //   username so multiple accounts on the same browser stay
    //   isolated without additional plumbing.
    // --------------------------------------------------------------
    var _currentConvId = null;         // null = "new chat, not yet saved"
    var _currentConvTitle = '';
    var _conversations = [];           // [{id, title, updated_at, turn_count, archived, pinned}]
    var _convListOpen = false;
    var _convListSyncing = false;
    var CONV_CACHE_VERSION = 1;
    var CONV_CACHE_MAX_ITEMS = 10;     // localStorage cap; server keeps the rest

    function _currentUsername() {
        try {
            if (window.TopologyAuth && typeof window.TopologyAuth.getCurrentUser === 'function') {
                var u = window.TopologyAuth.getCurrentUser();
                if (u && u.username) return u.username;
            }
        } catch (_) {}
        return '';
    }

    function _convCacheKey() {
        return 'ai-conversations:v' + CONV_CACHE_VERSION + ':' + (_currentUsername() || '_anon');
    }

    function _saveConvCache() {
        try {
            var payload = {
                currentId: _currentConvId,
                currentTitle: _currentConvTitle,
                // Cache messages of the CURRENT conversation only; the
                // rest come from the server on demand. This keeps the
                // cached blob well under the 5MB origin budget even for
                // power users with thousands of past chats.
                currentMessages: _messages.slice(-200).map(function (m) {
                    return {
                        role: m.role,
                        content: m.content,
                        tool: m.tool || null,
                        receipt: m.receipt || null,
                        applied: !!m.applied,
                        error: !!m.error,
                        notice: !!m.notice,
                        retryInfo: m.retryInfo || null,
                        // 2026-04-26 -- DNOS-grounded reply metadata.
                        // Persisted so a page reload keeps the
                        // "Verified from DNOS docs" card and source
                        // chips visible without a re-query.
                        dnosGrounded: !!m.dnosGrounded,
                        dnosSources: m.dnosSources || null,
                        dnosValidation: m.dnosValidation || null,
                        dnosError: m.dnosError || null,
                        dnosConfig: m.dnosConfig || '',
                        dnosIntent: m.dnosIntent || null,
                    };
                }),
                conversations: (_conversations || []).slice(0, CONV_CACHE_MAX_ITEMS),
                saved_at: Date.now(),
            };
            localStorage.setItem(_convCacheKey(), JSON.stringify(payload));
        } catch (_) {
            // Quota exceeded or privacy-mode localStorage: best-effort.
        }
    }

    function _loadConvCache() {
        try {
            var raw = localStorage.getItem(_convCacheKey());
            if (!raw) return null;
            var parsed = JSON.parse(raw);
            if (!parsed || typeof parsed !== 'object') return null;
            return parsed;
        } catch (_) {
            return null;
        }
    }

    // Drop the cache on logout so the next user on the same browser
    // doesn't inherit anything. Wired on `beforeunload` isn't enough --
    // we actively clear when TopologyAuth flips identity. The
    // `storage` event is fired in OTHER tabs; same-tab we rely on
    // auth.js calling this directly if exposed. Defensive.
    function _discardConvCache() {
        try {
            var key = _convCacheKey();
            localStorage.removeItem(key);
        } catch (_) {}
        _conversations = [];
        _currentConvId = null;
        _currentConvTitle = '';
    }
    // AbortController for the in-flight /api/ai/chat request. Exposed
    // at module scope so the Stop button in the loading bubble can
    // cancel the fetch from outside _sendUserMessage's try/catch.
    var _currentAbort = null;
    var _width = DEFAULT_WIDTH;

    // --------------------------------------------------------------
    //   Small helpers (auth, toast, editor aliasing)
    // --------------------------------------------------------------
    function _authFetch(url, opts) {
        if (window.TopologyAuth && window.TopologyAuth.authFetch) {
            return window.TopologyAuth.authFetch(url, opts);
        }
        return fetch(url, opts);
    }

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

    function _escapeHtml(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function _lsGet(key, fallback) {
        try {
            var v = localStorage.getItem(key);
            return v == null ? fallback : v;
        } catch (_) { return fallback; }
    }
    function _lsSet(key, value) {
        try { localStorage.setItem(key, String(value)); } catch (_) {}
    }

    function _nextId() { _msgCounter += 1; return 'm' + _msgCounter; }

    // --------------------------------------------------------------
    //   Launcher wiring (always-on button in the bottom-left bar)
    // --------------------------------------------------------------
    function _initLauncher() {
        _launcherEl = document.getElementById(LAUNCHER_ID);
        if (!_launcherEl) {
            // The launcher is declared directly in index.html, so this
            // branch only happens if an aggressive DOM rewrite removed
            // the bottom-left bar. Be defensive so the "A" shortcut
            // still works even then.
            return;
        }
        _launcherEl.addEventListener('click', function (e) {
            e.preventDefault();
            toggle();
        });
        // Initial styling hint: show the "needs setup" pulse until we
        // know whether the user has configured a key. Avoids a flicker
        // of the pulsing state on every page load for configured users.
        _launcherEl.classList.remove('needs-setup');
        // Probe in the background. If unauthenticated yet, skip -- the
        // auth module will fire `tp:authenticated` when ready.
        _probeAiConfig();
    }

    function _setLauncherActive(active) {
        if (!_launcherEl) return;
        _launcherEl.classList.toggle('active', !!active);
    }

    function _updateNeedsSetupBadge() {
        if (!_launcherEl) return;
        var needs = _aiConfig.configured === false;
        _launcherEl.classList.toggle('needs-setup', needs);
    }

    // --------------------------------------------------------------
    //   Drawer DOM (built on first open)
    // --------------------------------------------------------------
    function _buildDrawer() {
        if (_drawerBuilt) return;
        _drawerBuilt = true;

        _width = parseInt(_lsGet(LS.width, String(DEFAULT_WIDTH)), 10) || DEFAULT_WIDTH;
        _width = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, _width));

        var drawer = document.createElement('div');
        drawer.id = DRAWER_ID;
        drawer.className = 'ai-drawer';
        drawer.setAttribute('role', 'complementary');
        drawer.setAttribute('aria-label', 'AI assistant');
        drawer.setAttribute('aria-hidden', 'true');
        drawer.style.width = _width + 'px';
        drawer.innerHTML = _renderDrawerHTML();

        document.body.appendChild(drawer);
        _drawerEl = drawer;

        _injectDrawerStyles();
        _wireDrawerEvents();
        _renderChatLog();
    }

    function _renderDrawerHTML() {
        return ''
            + '<div class="ai-drawer__resizer" aria-hidden="true"></div>'
            + '<header class="ai-drawer__header">'
            +   '<span class="ai-drawer__icon" aria-hidden="true">'
            +     '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
            +       '<path d="M12 3l1.8 4.5L18 9l-4.2 1.5L12 15l-1.8-4.5L6 9l4.2-1.5L12 3z"/>'
            +       '<path d="M19 13l.7 1.6L21.3 15l-1.6.4L19 17l-.7-1.6L16.7 15l1.6-.4L19 13z"/>'
            +     '</svg>'
            +   '</span>'
            +   '<span class="ai-drawer__title">AI Assistant</span>'
            +   '<span class="ai-drawer__conv-title" data-role="conv-title-chip" hidden></span>'
            +   '<span class="ai-drawer__provider" data-role="provider-badge" hidden></span>'
            +   '<div class="ai-drawer__head-actions">'
            +     '<button type="button" class="ai-drawer__icon-btn" data-action="history" title="Conversation history" aria-label="Conversation history">'
            +       '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            +         '<path d="M3 3v5h5"/>'
            +         '<path d="M3.05 13a9 9 0 1 0 2.5-6.9L3 8"/>'
            +         '<path d="M12 7v5l4 2"/>'
            +       '</svg>'
            +     '</button>'
            +     '<button type="button" class="ai-drawer__icon-btn" data-action="new-chat" title="New chat (archive current)" aria-label="Start a new chat">'
            +       '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            +         '<path d="M12 20h9"/>'
            +         '<path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/>'
            +         '<line x1="12" y1="5" x2="12" y2="5"/>'
            +       '</svg>'
            +     '</button>'
            +     '<button type="button" class="ai-drawer__icon-btn" data-action="settings" title="AI settings (provider, API key)" aria-label="Open AI settings">'
            +       '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            +         '<circle cx="12" cy="12" r="3"/>'
            +         '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h.01a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v.01a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>'
            +       '</svg>'
            +     '</button>'
            +     '<button type="button" class="ai-drawer__icon-btn" data-action="close" title="Close (Esc)" aria-label="Close AI assistant">'
            +       '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
            +         '<line x1="18" y1="6" x2="6" y2="18"/>'
            +         '<line x1="6" y1="6" x2="18" y2="18"/>'
            +       '</svg>'
            +     '</button>'
            +   '</div>'
            + '</header>'
            // Chat toolbar lives BETWEEN header and body so it's not
            // covered by the absolute-positioned settings/history overlays
            // (.ai-config-panel and .ai-conv-list both use `position:
            // absolute; inset: 0` on top of .ai-drawer__body -- putting
            // the toolbar inside body would make it invisible while those
            // panels are open, which defeats the whole point).
            + '<div class="ai-chat-toolbar" data-role="chat-toolbar">'
            +   '<button type="button" class="ai-chat-toolbar__primary" data-action="new-chat" title="Start a new chat. The current one is archived to your history, not deleted.">'
            +     '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            +       '<line x1="12" y1="5" x2="12" y2="19"/>'
            +       '<line x1="5" y1="12" x2="19" y2="12"/>'
            +     '</svg>'
            +     '<span>New chat</span>'
            +   '</button>'
            +   '<div class="ai-chat-toolbar__spacer"></div>'
            +   '<button type="button" class="ai-chat-toolbar__btn" data-action="copy-transcript" title="Copy the whole conversation to the clipboard as Markdown" aria-label="Copy transcript">'
            +     '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            +       '<rect x="9" y="9" width="12" height="12" rx="2"/>'
            +       '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>'
            +     '</svg>'
            +     '<span>Copy</span>'
            +   '</button>'
            +   '<button type="button" class="ai-chat-toolbar__btn" data-action="regenerate" title="Re-ask the last user message. Replaces the most recent assistant answer." aria-label="Regenerate last answer">'
            +     '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            +       '<path d="M3 12a9 9 0 0 1 15.5-6.3L21 8"/>'
            +       '<path d="M21 3v5h-5"/>'
            +       '<path d="M21 12a9 9 0 0 1-15.5 6.3L3 16"/>'
            +       '<path d="M3 21v-5h5"/>'
            +     '</svg>'
            +     '<span>Regenerate</span>'
            +   '</button>'
            +   '<button type="button" class="ai-chat-toolbar__btn ai-chat-toolbar__btn--icon" data-action="export-markdown" title="Download this chat as a Markdown (.md) file" aria-label="Download chat as Markdown">'
            +     '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            +       '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
            +       '<polyline points="7 10 12 15 17 10"/>'
            +       '<line x1="12" y1="15" x2="12" y2="3"/>'
            +     '</svg>'
            +   '</button>'
            + '</div>'
            + '<section class="ai-drawer__body" data-role="body">'
            +   '<div class="ai-config-panel" data-role="config" hidden></div>'
            +   '<div class="ai-conv-list" data-role="conv-list" hidden></div>'
            +   '<div class="ai-chat-log" data-role="log" aria-live="polite"></div>'
            + '</section>'
            + '<footer class="ai-drawer__footer">'
            +   '<div class="ai-chips" data-role="chips">'
            +     '<button type="button" class="ai-chip" data-chip="clos">Build 4-leaf 2-spine Clos</button>'
            +     '<button type="button" class="ai-chip" data-chip="dc-pod">DC pod w/ ToR + border leafs</button>'
            +     '<button type="button" class="ai-chip" data-chip="explain-canvas">Explain my canvas</button>'
            +     '<button type="button" class="ai-chip" data-chip="shortcuts">Show keyboard shortcuts</button>'
            +   '</div>'
            +   '<form class="ai-composer" data-role="composer" autocomplete="off">'
            +     '<textarea class="ai-composer__input" rows="2" placeholder="Describe a topology, ask about the app, or paste an error..." data-role="composer-input" aria-label="Message the AI assistant"></textarea>'
            +     '<div class="ai-composer__row" data-role="composer-row">'
            +       '<span class="ai-composer__hint">Shift+Enter for newline. Enter to send.</span>'
            +       '<button type="submit" class="ai-composer__send" data-role="send" disabled>'
            +         '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
            +           '<line x1="22" y1="2" x2="11" y2="13"/>'
            +           '<polygon points="22 2 15 22 11 13 2 9 22 2"/>'
            +         '</svg>'
            +         '<span>Send</span>'
            +       '</button>'
            +     '</div>'
            +   '</form>'
            + '</footer>';
    }

    // Keeping the drawer CSS next to the JS (via an injected style tag)
    // means everything that ships with this module lives in this file.
    // The launcher + wrapper styles stay in index.html because they
    // affect the baseline layout regardless of whether the drawer is
    // ever opened.
    function _injectDrawerStyles() {
        if (document.getElementById('ai-drawer-styles')) return;
        // Brand palette reference (kept in sync with topology/styles.css):
        //   --dn-blue        #0066FA   primary brand blue
        //   --dn-blue-light  #3385FF   hover / active blue
        //   --dn-blue-dark   #0052CC   deep shadow blue
        //   --dn-cyan        #00B4D8   accent / highlight cyan
        //   --dn-cyan-bright #3EE0FF   spot highlight
        //   --dn-navy-deep   #0D1B2A   drawer background base
        //   --dn-bg-dark-sec #1B263B   panel inner background
        //   --dn-text-light  #E0E6ED   primary drawer text
        // Everything that used to be purple is now on the blue/cyan scale
        // so the AI drawer feels like part of DriveNets rather than a bolt-on.
        var css = ''
            + '.ai-drawer {'
            +   'position: fixed; top: 56px; right: 0; bottom: 0; z-index: 99;'
            +   'display: flex; flex-direction: column;'
            // 2026-04-24j -- DROPPED the backdrop-filter and made the
            // drawer surface FULLY OPAQUE. The previous 97/98 %-alpha
            // gradient + 14 px backdrop blur created a compositor layer
            // that Chrome composites children onto using "source-over"
            // with the backdrop's blurred saturation bleeding through.
            // On several machines (reported 2026-04-24) this made the
            // entire chat-log area read as a ghost layer *under* the
            // drawer chrome -- exactly the "text is on a separate layer
            // under the drawer" symptom the user described. Solid #0D1B2A
            // paints a flat, predictable surface; no compositor
            // shenanigans, no surprise blending.
            +   'background: linear-gradient(180deg, #0B1624 0%, #0D1B2A 56%, #08111C 100%);'
            +   'color: #E0E6ED;'
            // Pin the drawer to a dark colour scheme so Chrome/Safari
            // "auto dark mode" doesn't invert our text.
            +   'color-scheme: dark;'
            // `isolation: isolate` promotes this to its own stacking
            // context so NO ancestor's mix-blend-mode or filter can
            // leak into the drawer. Cheap insurance against future
            // CSS regressions elsewhere in the app.
            +   'isolation: isolate;'
            +   'font-family: "Inter", "Poppins", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;'
            +   'font-size: 13px; line-height: 1.5;'
            +   '-webkit-font-smoothing: antialiased;'
            +   '-moz-osx-font-smoothing: grayscale;'
            +   'text-rendering: optimizeLegibility;'
            +   'border-left: 1px solid rgba(0, 180, 216, 0.30);'
            +   'box-shadow: -12px 0 36px rgba(0,0,0,0.55), inset 1px 0 0 rgba(255,255,255,0.04);'
            +   'transform: translateX(100%);'
            +   'transition: transform 0.22s cubic-bezier(0.22, 1, 0.36, 1);'
            + '}'
            + '.ai-drawer.open { transform: translateX(0); }'
            + '@media (prefers-reduced-motion: reduce) {'
            +   '.ai-drawer { transition: none; }'
            + '}'
            + '.ai-drawer__resizer {'
            +   'position: absolute; top: 0; left: -3px; bottom: 0; width: 6px;'
            +   'cursor: ew-resize; z-index: 2;'
            + '}'
            + '.ai-drawer__resizer:hover { background: rgba(0, 180, 216, 0.32); }'
            + '.ai-drawer__resizer.dragging { background: rgba(0, 180, 216, 0.48); }'
            + '.ai-drawer__header {'
            +   'display: flex; align-items: center; gap: 10px;'
            +   'padding: 12px 14px; border-bottom: 1px solid rgba(0, 180, 216, 0.22);'
            +   'background: linear-gradient(135deg, rgba(0, 180, 216, 0.16), rgba(0, 102, 250, 0.08));'
            +   'box-shadow: 0 10px 24px rgba(0,0,0,0.18);'
            + '}'
            + '.ai-drawer__icon { color: #3EE0FF; display: inline-flex; filter: drop-shadow(0 1px 3px rgba(0, 180, 216, 0.55)); }'
            + '.ai-drawer__title {'
            +   'font-weight: 600; font-size: 13.5px; letter-spacing: 0.2px;'
            +   'color: #F2F6FA;'
            + '}'
            + '.ai-drawer__provider {'
            +   'font-size: 10.5px; font-weight: 500; letter-spacing: 0.3px;'
            +   'padding: 2px 8px; border-radius: 6px;'
            +   'background: rgba(0, 180, 216, 0.10); border: 1px solid rgba(0, 180, 216, 0.24);'
            +   'color: #C6EAF6;'
            + '}'
            + '.ai-drawer__conv-title {'
            +   'font-size: 11.5px; font-weight: 500; color: #E6F4FB;'
            +   'padding: 3px 9px; border-radius: 12px;'
            +   'background: rgba(120, 220, 255, 0.10);'
            +   'border: 1px solid rgba(120, 220, 255, 0.22);'
            +   'max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'
            + '}'
            + '.ai-drawer__head-actions { margin-left: auto; display: flex; gap: 4px; }'
            // ---- Conversation list panel (slides down over the chat log)
            + '.ai-conv-list {'
            +   'position: absolute; inset: 0; z-index: 3;'
            +   'background: linear-gradient(180deg, rgba(11, 20, 32, 0.98) 0%, rgba(15, 25, 40, 0.98) 100%);'
            +   'border-bottom: 1px solid rgba(0, 180, 216, 0.22);'
            +   'display: flex; flex-direction: column;'
            + '}'
            // 2026-04-24o -- Root-cause fix for "chat is under the
            // drawer and barely seen". The conv-list overlay gets
            // `display: flex` from the base rule above, which (ties
            // on specificity, cascades after the UA sheet) overrides
            // the HTML `hidden` attribute's default `display: none`.
            // Without THIS explicit `[hidden]` guard, the conv-list
            // was always rendered at `position: absolute; inset: 0;
            // z-index: 3; background: rgba(11,20,32,0.98)`, covering
            // the entire chat log with a 98 %-opaque sheet. Chat
            // text was physically underneath and bled through at 2 %
            // alpha -- which the user experienced as "text on a
            // separate layer under the drawer". Verified by DOM
            // `elementFromPoint(bubbleCx, bubbleCy)` returning
            // `.ai-conv-row__main` / `.ai-conv-list__head` at every
            // bubble centre. Sibling `.ai-config-panel[hidden]` has
            // the identical guard rule below -- that variant was
            // correctly hidden; only this one was missing.
            + '.ai-conv-list[hidden] { display: none !important; }'
            + '.ai-conv-list__head {'
            +   'display: flex; align-items: center; gap: 10px;'
            +   'padding: 10px 14px; border-bottom: 1px solid rgba(0, 180, 216, 0.18);'
            +   'background: rgba(0, 180, 216, 0.06);'
            + '}'
            + '.ai-conv-list__title { font-weight: 600; font-size: 13px; color: #F2F6FA; }'
            + '.ai-conv-list__archived {'
            +   'margin-left: auto; font-size: 11.5px; color: #B9CCD8; cursor: pointer;'
            +   'display: inline-flex; align-items: center; gap: 5px;'
            + '}'
            + '.ai-conv-list__archived input { margin: 0; }'
            + '.ai-conv-list__body { flex: 1 1 auto; min-height: 0; overflow-y: auto; padding: 6px; }'
            + '.ai-conv-empty { padding: 22px 14px; font-size: 12.5px; color: #9AB0BC; text-align: center; }'
            + '.ai-conv-row {'
            +   'display: flex; align-items: stretch; gap: 4px;'
            +   'padding: 2px;'
            +   'border-radius: 8px; margin-bottom: 2px;'
            +   'transition: background 0.12s ease;'
            + '}'
            + '.ai-conv-row:hover { background: rgba(0, 180, 216, 0.07); }'
            + '.ai-conv-row--current { background: rgba(0, 180, 216, 0.14); }'
            + '.ai-conv-row--current:hover { background: rgba(0, 180, 216, 0.18); }'
            + '.ai-conv-row__main {'
            +   'flex: 1 1 auto; min-width: 0;'
            +   'background: transparent; border: 0;'
            +   'text-align: left; padding: 7px 9px; border-radius: 6px;'
            +   'color: #ECF2F8; cursor: pointer;'
            +   'display: flex; flex-direction: column; gap: 2px;'
            + '}'
            + '.ai-conv-row__main:hover { background: rgba(0, 180, 216, 0.10); }'
            + '.ai-conv-row__title {'
            +   'font-size: 12.5px; font-weight: 500; color: #F2F6FA;'
            +   'white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'
            + '}'
            + '.ai-conv-row__meta { font-size: 11px; color: #8FA5B2; }'
            + '.ai-conv-row__actions { display: flex; gap: 2px; align-items: center; opacity: 0.55; transition: opacity 0.12s ease; }'
            + '.ai-conv-row:hover .ai-conv-row__actions { opacity: 1; }'
            + '.ai-conv-row__btn {'
            +   'width: 24px; height: 24px; border-radius: 6px; cursor: pointer;'
            +   'background: transparent; border: 1px solid transparent;'
            +   'color: rgba(224, 230, 237, 0.70);'
            +   'display: inline-flex; align-items: center; justify-content: center;'
            + '}'
            + '.ai-conv-row__btn:hover { background: rgba(0, 180, 216, 0.18); color: #fff; border-color: rgba(0, 180, 216, 0.38); }'
            + '.ai-conv-row__btn--danger:hover { background: rgba(240, 90, 90, 0.22); border-color: rgba(240, 90, 90, 0.48); color: #FFD6D6; }'
            + '.ai-drawer__icon-btn {'
            +   'width: 28px; height: 28px; border-radius: 7px; background: transparent;'
            +   'border: 1px solid transparent; color: rgba(224, 230, 237, 0.78); cursor: pointer;'
            +   'display: inline-flex; align-items: center; justify-content: center;'
            +   'transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;'
            + '}'
            + '.ai-drawer__icon-btn:hover {'
            +   'background: rgba(0, 180, 216, 0.18); color: #fff;'
            +   'border-color: rgba(0, 180, 216, 0.38);'
            + '}'
            + '.ai-drawer__body {'
            +   'flex: 1 1 auto; min-height: 0; position: relative;'
            +   'display: flex; flex-direction: column;'
            + '}'
            // ----------------------------------------------------------
            //   Chat toolbar (sub-header strip, always visible)
            // ----------------------------------------------------------
            //
            // Lives between .ai-drawer__header and .ai-drawer__body. We
            // keep it OUTSIDE body on purpose -- the settings + history
            // panels overlay the body at z-index 3 and would hide it.
            // The toolbar stays reachable even when those panels are
            // open so "New chat" never disappears behind a modal.
            + '.ai-chat-toolbar {'
            +   'flex: 0 0 auto;'
            +   'display: flex; align-items: center; gap: 6px;'
            +   'padding: 7px 10px;'
            +   'background: rgba(11, 20, 32, 0.92);'
            +   'border-bottom: 1px solid rgba(0, 180, 216, 0.18);'
            + '}'
            + '.ai-chat-toolbar__spacer { flex: 1 1 auto; }'
            + '.ai-chat-toolbar__primary {'
            +   'display: inline-flex; align-items: center; gap: 6px;'
            +   'padding: 5px 11px; border-radius: 999px;'
            +   'font-family: inherit; font-size: 11.5px; font-weight: 600; letter-spacing: 0.25px;'
            +   '-webkit-font-smoothing: antialiased;'
            +   'background: linear-gradient(135deg, rgba(0,180,216,0.22), rgba(0,102,250,0.22));'
            +   'color: #F2F8FF;'
            +   'border: 1px solid rgba(62, 224, 255, 0.48);'
            +   'cursor: pointer;'
            +   'transition: background 0.15s ease, border-color 0.15s ease, transform 0.12s ease, box-shadow 0.15s ease;'
            + '}'
            + '.ai-chat-toolbar__primary:hover {'
            +   'background: linear-gradient(135deg, rgba(0,180,216,0.38), rgba(0,102,250,0.38));'
            +   'border-color: rgba(62, 224, 255, 0.80);'
            +   'transform: translateY(-1px);'
            +   'box-shadow: 0 4px 12px rgba(0, 82, 204, 0.28);'
            + '}'
            + '.ai-chat-toolbar__primary:active { transform: translateY(0); }'
            + '.ai-chat-toolbar__primary:disabled {'
            +   'opacity: 0.55; cursor: not-allowed; transform: none; box-shadow: none;'
            + '}'
            + '.ai-chat-toolbar__btn {'
            +   'display: inline-flex; align-items: center; gap: 5px;'
            +   'padding: 4px 9px; border-radius: 7px;'
            +   'font-family: inherit; font-size: 11px; font-weight: 500; letter-spacing: 0.2px;'
            +   '-webkit-font-smoothing: antialiased;'
            +   'background: rgba(255, 255, 255, 0.045);'
            +   'color: rgba(224, 230, 237, 0.82);'
            +   'border: 1px solid rgba(255, 255, 255, 0.10);'
            +   'cursor: pointer;'
            +   'transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;'
            + '}'
            + '.ai-chat-toolbar__btn:hover:not(:disabled) {'
            +   'background: rgba(0, 180, 216, 0.18);'
            +   'color: #FFFFFF;'
            +   'border-color: rgba(0, 180, 216, 0.44);'
            + '}'
            + '.ai-chat-toolbar__btn:disabled { opacity: 0.45; cursor: not-allowed; }'
            + '.ai-chat-toolbar__btn--icon { padding: 4px 7px; }'
            + '.ai-chat-toolbar--busy .ai-chat-toolbar__btn,'
            + '.ai-chat-toolbar--busy .ai-chat-toolbar__primary {'
            +   'opacity: 0.70;'
            + '}'
            + '.ai-chat-toolbar__btn--flash {'
            +   'background: rgba(62, 224, 255, 0.30) !important;'
            +   'color: #FFFFFF !important;'
            +   'border-color: rgba(62, 224, 255, 0.80) !important;'
            + '}'
            + '.ai-chat-log {'
            +   'flex: 1 1 auto; min-height: 0; overflow-y: auto;'
            // Tighter gap (10 -> 8 px) so bubbles cluster into turn
            // groups instead of drifting apart.
            +   'padding: 16px; display: flex; flex-direction: column; gap: 10px;'
            +   'color: #ECF2F8;'
            +   'background: radial-gradient(circle at 18% 0%, rgba(0,180,216,0.10), transparent 34%), radial-gradient(circle at 88% 18%, rgba(0,102,250,0.10), transparent 32%);'
            + '}'
            + '.ai-chat-log::-webkit-scrollbar { width: 8px; }'
            + '.ai-chat-log::-webkit-scrollbar-thumb {'
            +   'background: rgba(0, 180, 216, 0.32); border-radius: 4px;'
            + '}'
            + '.ai-chat-log::-webkit-scrollbar-thumb:hover { background: rgba(0, 180, 216, 0.50); }'
            + '.ai-msg {'
            +   'position: relative;'  // 2026-04-24s -- anchor for .ai-msg__copy overlay.
            +   'max-width: 92%; padding: 12px 14px; border-radius: 14px;'
            +   'font-size: 13.5px; line-height: 1.6;'
            +   'white-space: pre-wrap; word-wrap: break-word;'
            +   'letter-spacing: 0.1px;'
            +   'color: #ECF2F8;'
            + '}'
            // 2026-04-24s -- per-message Copy button. Absolutely
            // positioned top-right so it doesn't disturb the bubble's
            // reading flow. Fades in on bubble hover to stay quiet
            // while scanning, then becomes fully clickable with a
            // visible focus ring for keyboard users.
            + '.ai-msg__copy {'
            +   'position: absolute; top: 6px; right: 6px;'
            +   'display: inline-flex; align-items: center; gap: 4px;'
            +   'padding: 3px 7px 3px 6px; border-radius: 6px;'
            +   'font-size: 10.5px; letter-spacing: 0.3px; font-weight: 600;'
            +   'text-transform: uppercase;'
            +   'background: rgba(0, 0, 0, 0.32);'
            +   'color: rgba(255, 255, 255, 0.82);'
            +   'border: 1px solid rgba(255, 255, 255, 0.18);'
            +   'cursor: pointer; opacity: 0; transition: opacity 120ms ease-in,'
            +                 'background 120ms ease-in, color 120ms ease-in;'
            +   'z-index: 2;'
            + '}'
            + '.ai-msg:hover .ai-msg__copy, .ai-msg:focus-within .ai-msg__copy {'
            +   'opacity: 0.85;'
            + '}'
            + '.ai-msg__copy:hover {'
            +   'opacity: 1 !important;'
            +   'background: rgba(0, 180, 216, 0.38);'
            +   'color: #ffffff;'
            +   'border-color: rgba(62, 224, 255, 0.55);'
            + '}'
            + '.ai-msg__copy:focus-visible {'
            +   'opacity: 1;'
            +   'outline: 2px solid rgba(62, 224, 255, 0.75); outline-offset: 1px;'
            + '}'
            + '.ai-msg__copy.is-copied {'
            +   'opacity: 1 !important;'
            +   'background: rgba(46, 204, 113, 0.42);'
            +   'color: #ffffff;'
            +   'border-color: rgba(80, 220, 140, 0.70);'
            + '}'
            + '.ai-msg__copy-ico {'
            +   'font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;'
            +   'font-size: 11px; line-height: 1; letter-spacing: 0;'
            + '}'
            // Error / error-card bubbles have padding that can clip a
            // button at the exact corner; nudge slightly inward.
            + '.ai-msg.error .ai-msg__copy, .ai-msg.error-card .ai-msg__copy {'
            +   'top: 8px; right: 8px;'
            + '}'
            // Push bubble text left of the overlay so long first words
            // don't run under the Copy pill while it's visible.
            + '.ai-msg.user, .ai-msg.assistant, .ai-msg.notice, .ai-msg.system, .ai-msg.error {'
            +   'padding-right: 54px;'
            + '}'
            // 2026-04-24n -- CONTRAST-driven fix. Previous rounds had
            // CSS technically applied (proven by debug instrumentation
            // 2026-04-24n: computed backgrounds matched hex values
            // exactly, zero inline overrides, no ancestor opacity /
            // filter / blend), but the bubble backgrounds were only
            // 5-20 RGB units above the drawer base (#0D1B2A), so the
            // eye couldn't separate bubble from drawer. User reported
            // "text on a separate layer under the drawer" -- not a
            // compositor bug, a perception bug caused by insufficient
            // foreground-surface brightness delta.
            // Every bubble now sits at least 40 RGB units above the
            // drawer base on the relevant channel, plus a 2 px rim at
            // 0.55+ alpha so each chip reads as a distinct surface.
            + '.ai-msg.user {'
            +   'align-self: flex-end;'
            +   'background: linear-gradient(135deg, #0066FA, #0050B8) !important;'
            +   'border: 2px solid rgba(62, 224, 255, 0.70) !important;'
            +   'color: #FFFFFF !important;'
            +   'box-shadow: 0 3px 14px rgba(0, 82, 204, 0.46),'
            +                 'inset 0 1px 0 rgba(255, 255, 255, 0.22);'
            + '}'
            + '.ai-msg.assistant {'
            +   'align-self: flex-start;'
            // #243B5C is +23/+32/+50 above the drawer base #0D1B2A;
            // previously #1A2A42 was only +13/+15/+24 which was
            // visually indistinguishable. The text-shadow adds sub-
            // pixel crispness so 13.5 px white reads clean at macOS
            // Retina / JPEG-compressed screenshot resolutions.
            +   'background: linear-gradient(135deg, #243B5C, #172B45) !important;'
            +   'border: 2px solid rgba(62, 224, 255, 0.42) !important;'
            +   'color: #FFFFFF !important;'
            +   'text-shadow: 0 1px 2px rgba(0, 0, 0, 0.45);'
            +   'box-shadow: 0 2px 12px rgba(0, 0, 0, 0.42),'
            +                 'inset 0 1px 0 rgba(255, 255, 255, 0.10);'
            + '}'
            // Any descendant element inherits the forced white colour
            // too -- synthesized tool-only summaries render raw text
            // directly under the bubble's root so a wildcard child
            // selector keeps them crisp even if a future refactor
            // wraps the text in a <p> / <span>.
            + '.ai-msg.assistant *, .ai-msg.user * { color: inherit !important; }'
            + '.ai-msg.assistant:hover { border-color: rgba(62, 224, 255, 0.70) !important; }'
            // 2026-04-24n -- bumped brightness + rim thickness per
            // instrumented-run evidence. Old #122538 notice was only
            // +5/+10/+14 RGB above drawer -> visually merged. New
            // #1F3F66 is +18/+36/+60, clearly a distinct chip.
            + '.ai-msg.system, .ai-msg.notice {'
            +   'align-self: stretch;'
            +   'background: #1F3F66 !important;'
            +   'border: 2px solid rgba(0, 180, 216, 0.70) !important;'
            +   'color: #FFFFFF !important;'
            +   'font-size: 12.5px; padding: 10px 12px; line-height: 1.55;'
            +   'text-shadow: 0 1px 2px rgba(0, 0, 0, 0.45);'
            +   'box-shadow: 0 2px 10px rgba(0, 0, 0, 0.40),'
            +                 'inset 0 1px 0 rgba(0, 180, 216, 0.22);'
            + '}'
            // Old #3A1515 error was a dark muddy red indistinguishable
            // from a tinted drawer. #5C1F1F is noticeably lighter and
            // the 2 px rim at 0.85 alpha outlines the chip clearly.
            + '.ai-msg.error {'
            +   'align-self: stretch;'
            +   'background: #5C1F1F !important;'
            +   'border: 2px solid rgba(255, 110, 96, 0.85) !important;'
            +   'color: #FFFFFF !important;'
            +   'font-size: 13px; line-height: 1.55;'
            +   'text-shadow: 0 1px 2px rgba(0, 0, 0, 0.55);'
            +   'box-shadow: 0 2px 10px rgba(231, 76, 60, 0.30);'
            + '}'
            // Error card carries the most important content (billing
            // CTA, quota detail) so it gets the widest rim + a clear
            // warm-red fill. #4A1818 is 60 % brighter than the old
            // #2E1010.
            + '.ai-msg.error-card {'
            +   'align-self: stretch;'
            +   'background: #4A1818 !important;'
            +   'border: 2px solid rgba(255, 110, 96, 0.85) !important;'
            +   'border-radius: 10px; padding: 12px 12px 10px;'
            +   'box-shadow: 0 4px 18px rgba(231, 76, 60, 0.36),'
            +                 'inset 0 1px 0 rgba(255, 110, 96, 0.24);'
            +   'color: #FFFFFF !important;'
            +   'font-size: 13px; line-height: 1.55;'
            +   'text-shadow: 0 1px 2px rgba(0, 0, 0, 0.55);'
            + '}'
            // Keep nested title / hint / msg colours bright. The
            // existing rules painted them pink-on-dark-red which the
            // user read as "dim text"; white with a shadow matches
            // the rest of the chat log.
            + '.ai-err-card__title { color: #FFFFFF !important; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.55); }'
            + '.ai-err-card__hint  { color: #FFE6DF !important; }'
            + '.ai-err-card__msg   { color: #FFFFFF !important; background: rgba(0, 0, 0, 0.35) !important; }'
            + '.ai-err-card__title {'
            +   'font-weight: 700; font-size: 13.5px; letter-spacing: 0.2px;'
            +   'color: #FFD8D2; margin-bottom: 4px;'
            + '}'
            + '.ai-err-card__hint {'
            +   'color: #F5E3DF; margin-bottom: 8px;'
            + '}'
            + '.ai-err-card__msg {'
            +   'background: rgba(0,0,0,0.24); border: 1px solid rgba(231,76,60,0.35);'
            +   'border-radius: 6px; padding: 7px 9px; margin-bottom: 8px;'
            +   'font-size: 12px; line-height: 1.5; color: #FFE6E1;'
            +   'word-break: break-word;'
            + '}'
            + '.ai-err-card__msg-label {'
            +   'font-weight: 700; color: #FFBDB2; letter-spacing: 0.2px;'
            +   'font-size: 10.5px; text-transform: uppercase; margin-right: 4px;'
            + '}'
            + '.ai-err-card__actions {'
            +   'display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 4px;'
            + '}'
            + '.ai-err-card__actions .ai-btn {'
            +   'text-decoration: none;'
            + '}'
            + '.ai-err-card__details {'
            +   'margin-top: 8px; font-size: 11.5px; color: rgba(255, 224, 219, 0.78);'
            + '}'
            + '.ai-err-card__details summary {'
            +   'cursor: pointer; user-select: none; color: #FFBDB2;'
            +   'font-weight: 600; letter-spacing: 0.2px;'
            + '}'
            + '.ai-err-card__details summary:hover { color: #fff; }'
            + '.ai-err-card__details pre {'
            +   'margin: 6px 0 0; padding: 8px 10px;'
            +   'background: rgba(0,0,0,0.35); border: 1px solid rgba(231,76,60,0.3);'
            +   'border-radius: 6px; max-height: 200px; overflow: auto;'
            +   'font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;'
            +   'font-size: 11px; line-height: 1.45; color: #FFE6E1;'
            +   'white-space: pre-wrap; word-break: break-word;'
            + '}'
            // 2026-04-24n -- loading bubble matches assistant brightness.
            + '.ai-msg.loading {'
            +   'align-self: flex-start;'
            +   'background: #243B5C !important;'
            +   'border: 2px solid rgba(62, 224, 255, 0.42) !important;'
            +   'color: #FFFFFF !important;'
            +   'font-size: 13px; padding: 9px 11px; max-width: 85%;'
            +   'text-shadow: 0 1px 2px rgba(0, 0, 0, 0.45);'
            +   'box-shadow: 0 2px 10px rgba(0, 0, 0, 0.32);'
            + '}'
            + '.ai-loading__row {'
            +   'display: flex; align-items: center; gap: 9px;'
            + '}'
            + '.ai-loading__label { font-style: italic; flex: 1 1 auto; }'
            + '.ai-loading__dot {'
            +   'display: inline-block; width: 8px; height: 8px; border-radius: 50%;'
            +   'background: #00B4D8; flex: 0 0 auto;'
            +   'animation: ai-loading-pulse 1.1s ease-in-out infinite;'
            + '}'
            + '@keyframes ai-loading-pulse {'
            +   '0%, 100% { opacity: 0.35; transform: scale(0.85); }'
            +   '50%     { opacity: 1;    transform: scale(1.15); }'
            + '}'
            + '.ai-loading__timer {'
            +   'font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;'
            +   'font-size: 11px; color: rgba(198, 234, 246, 0.82);'
            +   'letter-spacing: 0.4px; flex: 0 0 auto;'
            + '}'
            + '.ai-loading__hint {'
            +   'margin-top: 7px; padding-top: 7px;'
            +   'border-top: 1px dashed rgba(255,255,255,0.14);'
            +   'font-size: 11px; line-height: 1.5; font-style: normal;'
            +   'color: rgba(224, 230, 237, 0.74);'
            + '}'
            + '.ai-msg .ai-msg__meta {'
            // 2026-04-24i -- slimmed the meta label so it reads as a
            // quiet sender caption instead of a chunky banner. The
            // previous 10.5px/uppercase combo competed with the actual
            // message content for attention; 9.5px at 0.75 opacity is
            // enough to identify speaker without dominating.
            +   'display: block; font-size: 9.5px; color: rgba(198, 234, 246, 0.72);'
            +   'margin-bottom: 4px; letter-spacing: 0.55px;'
            +   'font-weight: 600; text-transform: uppercase;'
            + '}'
            // Auto-recovered-from-429 chip -- small, unobtrusive pill
            // that trails the successful assistant reply. Amber tint so
            // the user notices (briefly) without it looking like an
            // error card.
            + '.ai-msg__retry-chip {'
            +   'display: inline-block; margin-top: 6px;'
            +   'padding: 2px 8px 3px; border-radius: 999px;'
            +   'font-size: 10.5px; letter-spacing: 0.2px;'
            +   'background: rgba(255, 183, 77, 0.16);'
            +   'border: 1px solid rgba(255, 183, 77, 0.36);'
            +   'color: rgba(255, 216, 167, 0.92);'
            +   'cursor: help;'
            + '}'
            // 2026-04-24t -- model-fallback chip. Blue tint (informational,
            // NOT an error) with an inline "Switch" button that persists
            // the fallback model as the user's default. Distinct from
            // the amber retry-chip so a visual scan distinguishes
            // "same model, slower" from "different model, your choice
            // was out of quota".
            + '.ai-msg__fallback-chip {'
            +   'display: flex; flex-wrap: wrap; align-items: center; gap: 8px;'
            +   'margin-top: 6px; padding: 4px 10px 5px;'
            +   'font-size: 10.5px; letter-spacing: 0.15px; line-height: 1.4;'
            +   'background: rgba(86, 156, 214, 0.14);'
            +   'border: 1px solid rgba(86, 156, 214, 0.40);'
            +   'border-radius: 999px;'
            +   'color: rgba(208, 226, 244, 0.92);'
            +   'cursor: help;'
            +   'transition: opacity 0.25s ease;'
            + '}'
            + '.ai-msg__fallback-chip--saved { opacity: 0.7; }'
            + '.ai-msg__fallback-label b {'
            +   'font-weight: 600; color: #CDEBFF;'
            + '}'
            + '.ai-msg__fallback-from {'
            +   'color: rgba(208, 226, 244, 0.68); font-size: 10px;'
            +   'margin-left: 4px;'
            + '}'
            + '.ai-msg__fallback-btn {'
            +   'appearance: none; -webkit-appearance: none; cursor: pointer;'
            +   'border: 1px solid rgba(86, 156, 214, 0.60);'
            +   'background: rgba(86, 156, 214, 0.24);'
            +   'color: #E6F3FF; font-size: 10px; font-weight: 600;'
            +   'padding: 2px 9px; border-radius: 999px;'
            +   'letter-spacing: 0.3px; text-transform: uppercase;'
            +   'transition: background 0.15s ease, transform 0.15s ease;'
            + '}'
            + '.ai-msg__fallback-btn:hover:not(:disabled) {'
            +   'background: rgba(86, 156, 214, 0.40);'
            +   'transform: translateY(-1px);'
            + '}'
            + '.ai-msg__fallback-btn:disabled {'
            +   'opacity: 0.65; cursor: default;'
            + '}'
            + '.ai-msg__fallback-btn--saved {'
            +   'background: rgba(76, 175, 80, 0.30);'
            +   'border-color: rgba(76, 175, 80, 0.60);'
            + '}'
            // 2026-04-24r -- consulted-blueprint chip, shown below the
            // assistant bubble. Teal tint (matches the tool cards)
            // because it is attribution, not a warning. One-line flex
            // layout; `+N more` overflow pill when the list is long.
            + '.ai-consulted-chip {'
            +   'display: flex; flex-wrap: wrap; align-items: center; gap: 6px;'
            +   'margin-top: 6px; padding: 4px 8px;'
            +   'font-size: 10.5px; letter-spacing: 0.15px;'
            +   'background: rgba(0, 180, 216, 0.10);'
            +   'border: 1px solid rgba(0, 180, 216, 0.28);'
            +   'border-radius: 8px;'
            +   'color: rgba(224, 230, 237, 0.88);'
            +   'cursor: help;'
            + '}'
            + '.ai-consulted-chip__label {'
            +   'font-weight: 600; color: #A9E4F4; margin-right: 2px;'
            + '}'
            + '.ai-consulted-chip__item {'
            +   'padding: 1px 6px; border-radius: 999px;'
            +   'background: rgba(0, 180, 216, 0.22);'
            +   'color: #E0F7FA;'
            + '}'
            // 2026-04-26 -- DNOS-grounded reply styling. Used when the
            // backend intent gate routed the turn through the strict
            // RST/MCP grounding path. The bubble shows the validated
            // CLI block in a monospace pre, plus a "Verified from DNOS
            // docs" chip enumerating each source.
            + '.ai-dnos-card {'
            +   'align-self: stretch; margin-top: 4px;'
            +   'background: linear-gradient(135deg, rgba(38, 166, 154, 0.12), rgba(0, 121, 107, 0.12));'
            +   'border: 1px solid rgba(38, 166, 154, 0.42); border-radius: 12px;'
            +   'padding: 10px 12px; color: #E0F2F1;'
            +   'box-shadow: 0 4px 14px rgba(0, 121, 107, 0.18), inset 0 1px 0 rgba(255,255,255,0.06);'
            + '}'
            + '.ai-dnos-card__hdr {'
            +   'display: flex; align-items: center; justify-content: space-between;'
            +   'gap: 8px; margin-bottom: 6px;'
            +   'font-size: 11px; letter-spacing: 0.4px; text-transform: uppercase;'
            +   'color: #80CBC4; font-weight: 700;'
            + '}'
            + '.ai-dnos-card__hdr .ai-dnos-card__intent {'
            +   'font-size: 10.5px; font-weight: 500; letter-spacing: 0.2px;'
            +   'color: rgba(178, 223, 219, 0.75); text-transform: none;'
            + '}'
            + '.ai-dnos-card__pre {'
            +   'margin: 0; padding: 10px 12px;'
            +   'background: rgba(0, 0, 0, 0.42); border-radius: 8px;'
            +   'font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;'
            +   'font-size: 12.5px; line-height: 1.5;'
            +   'color: #B2DFDB; white-space: pre; overflow-x: auto;'
            +   'border: 1px solid rgba(38, 166, 154, 0.18);'
            + '}'
            + '.ai-dnos-card__copy {'
            +   'background: rgba(38, 166, 154, 0.18);'
            +   'border: 1px solid rgba(38, 166, 154, 0.4);'
            +   'color: #E0F2F1; cursor: pointer;'
            +   'padding: 3px 8px; font-size: 10.5px; border-radius: 999px;'
            +   'letter-spacing: 0.3px;'
            + '}'
            + '.ai-dnos-card__copy:hover { background: rgba(38, 166, 154, 0.32); }'
            + '.ai-dnos-sources {'
            +   'display: flex; flex-wrap: wrap; align-items: center; gap: 6px;'
            +   'margin-top: 6px; padding: 4px 8px;'
            +   'font-size: 10.5px; letter-spacing: 0.15px;'
            +   'background: rgba(38, 166, 154, 0.10);'
            +   'border: 1px solid rgba(38, 166, 154, 0.25);'
            +   'border-radius: 999px; color: #B2DFDB;'
            + '}'
            + '.ai-dnos-sources__label {'
            +   'font-weight: 600; color: #80CBC4; margin-right: 2px;'
            + '}'
            + '.ai-dnos-sources__item {'
            +   'padding: 1px 6px; border-radius: 999px;'
            +   'background: rgba(38, 166, 154, 0.20);'
            +   'color: #E0F2F1; cursor: help;'
            + '}'
            + '.ai-dnos-validation {'
            +   'margin-top: 6px; padding: 4px 8px;'
            +   'font-size: 10.5px; border-radius: 8px;'
            +   'background: rgba(0, 0, 0, 0.18);'
            +   'border: 1px dashed rgba(255, 167, 38, 0.40);'
            +   'color: #FFCC80;'
            + '}'
            + '.ai-dnos-validation--ok {'
            +   'border-color: rgba(102, 187, 106, 0.40); color: #A5D6A7;'
            + '}'
            + '.ai-dnos-validation li { margin: 2px 0 0 16px; }'
            + '.ai-dnos-error {'
            +   'margin-top: 6px; padding: 6px 10px;'
            +   'font-size: 11.5px; border-radius: 8px;'
            +   'background: rgba(244, 67, 54, 0.10);'
            +   'border: 1px solid rgba(244, 67, 54, 0.32);'
            +   'color: #EF9A9A;'
            + '}'
            // 2026-04-24r -- chip-picker / proposal-card variants.
            // Blue-violet tint for question cards so the user
            // visually distinguishes "assistant is asking me" from
            // "assistant is telling me". Proposal cards reuse the
            // default teal card look plus a denser edit list.
            + '.ai-tool-card--question {'
            +   'background: linear-gradient(135deg, rgba(147, 112, 219, 0.16), rgba(102, 51, 153, 0.16));'
            +   'border-color: rgba(147, 112, 219, 0.42);'
            +   'box-shadow: 0 4px 14px rgba(102, 51, 153, 0.24);'
            + '}'
            + '.ai-tool-card__chips {'
            +   'flex-wrap: wrap; gap: 6px;'
            + '}'
            + '.ai-chip--ghost {'
            +   'opacity: 0.75;'
            + '}'
            + '.ai-tool-card__edit-list {'
            +   'color: rgba(224, 230, 237, 0.92);'
            + '}'
            + '.ai-tool-card__edit-list li {'
            +   'margin-bottom: 2px;'
            + '}'
            + '.ai-tool-card__edit-list b { color: #fff; font-weight: 600; }'
            + '.ai-tool-card {'
            +   'align-self: stretch;'
            +   'background: linear-gradient(135deg, rgba(0, 180, 216, 0.14), rgba(0, 102, 250, 0.14));'
            +   'border: 1px solid rgba(62, 224, 255, 0.46); border-radius: 14px;'
            +   'padding: 13px 13px 11px; color: #E0E6ED;'
            +   'box-shadow: 0 8px 24px rgba(0, 82, 204, 0.26), inset 0 1px 0 rgba(255,255,255,0.08);'
            + '}'
            + '.ai-tool-card__title {'
            +   'display: flex; align-items: center; gap: 8px;'
            +   'font-weight: 600; font-size: 13px; letter-spacing: 0.2px;'
            +   'margin-bottom: 6px; color: #E8F6FC;'
            + '}'
            + '.ai-tool-card__stats {'
            +   'font-size: 11.5px; color: rgba(224, 230, 237, 0.78); margin-bottom: 8px;'
            + '}'
            + '.ai-tool-card__stats b { color: #fff; font-weight: 600; }'
            + '.ai-tool-card__actions {'
            +   'display: flex; gap: 8px; flex-wrap: wrap;'
            + '}'
            + '.ai-btn {'
            +   'padding: 7px 12px; border-radius: 8px; border: 1px solid transparent;'
            +   'font-family: inherit;'
            +   'font-size: 12.5px; font-weight: 600; cursor: pointer; letter-spacing: 0.25px;'
            +   '-webkit-font-smoothing: antialiased;'
            +   'transition: transform 0.12s ease, background 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;'
            + '}'
            + '.ai-btn.primary {'
            +   'background: linear-gradient(135deg, #00B4D8, #0066FA);'
            +   'color: #fff; border-color: rgba(255,255,255,0.18);'
            +   'box-shadow: 0 4px 14px rgba(0, 82, 204, 0.44);'
            + '}'
            + '.ai-btn.primary:hover {'
            +   'transform: translateY(-1px);'
            +   'background: linear-gradient(135deg, #3EE0FF, #3385FF);'
            +   'box-shadow: 0 6px 18px rgba(0, 82, 204, 0.52);'
            + '}'
            + '.ai-btn.secondary {'
            +   'background: rgba(255,255,255,0.06); color: #E0E6ED;'
            +   'border-color: rgba(255,255,255,0.16);'
            + '}'
            + '.ai-btn.secondary:hover {'
            +   'background: rgba(0, 180, 216, 0.18);'
            +   'border-color: rgba(0, 180, 216, 0.42);'
            +   'color: #fff;'
            + '}'
            + '.ai-btn.tiny {'
            +   'padding: 4px 10px; font-size: 11px; border-radius: 6px; letter-spacing: 0.3px;'
            + '}'
            + '.ai-btn.tiny:not(.ghost):not(.secondary) {'
            +   'background: linear-gradient(135deg, #00B4D8, #0066FA); color: #fff;'
            +   'border-color: rgba(255,255,255,0.18);'
            + '}'
            + '.ai-btn.tiny.ghost {'
            +   'background: transparent; color: rgba(224, 230, 237, 0.80);'
            +   'border-color: rgba(255,255,255,0.18);'
            + '}'
            + '.ai-btn.tiny.ghost:hover {'
            +   'background: rgba(255, 255, 255, 0.06); color: #fff;'
            + '}'
            + '.ai-btn:disabled { opacity: 0.55; cursor: not-allowed; transform: none; }'
            + '.ai-placement { padding-bottom: 10px; }'
            + '.ai-placement__note {'
            +   'font-size: 11px; color: rgba(224, 230, 237, 0.7);'
            +   'margin: 4px 0 8px; font-style: italic;'
            + '}'
            + '.ai-placement__row {'
            +   'display: flex; align-items: center; gap: 8px;'
            +   'margin-bottom: 8px; flex-wrap: nowrap;'
            + '}'
            + '.ai-placement__opt {'
            +   'display: inline-flex; align-items: center; gap: 6px;'
            +   'min-width: 110px; font-size: 12px; font-weight: 500;'
            +   'color: rgba(224, 230, 237, 0.86); cursor: pointer;'
            +   '-webkit-user-select: none; user-select: none;'
            + '}'
            + '.ai-placement__opt--static { cursor: default; }'
            + '.ai-placement__opt input[type="radio"] {'
            +   'accent-color: #00B4D8; margin: 0; cursor: pointer;'
            + '}'
            + '.ai-placement__opt input[type="radio"]:disabled {'
            +   'cursor: not-allowed;'
            + '}'
            + '.ai-placement__select, .ai-placement__input {'
            +   'flex: 1; min-width: 0; padding: 6px 8px;'
            +   'border-radius: 6px;'
            +   'background: rgba(11, 22, 36, 0.6);'
            +   'border: 1px solid rgba(0, 180, 216, 0.32);'
            +   'color: #E8F6FC; font-family: inherit; font-size: 12px;'
            +   'outline: none;'
            +   'transition: border-color 0.15s ease, box-shadow 0.15s ease;'
            + '}'
            + '.ai-placement__select:focus, .ai-placement__input:focus {'
            +   'border-color: rgba(0, 180, 216, 0.75);'
            +   'box-shadow: 0 0 0 2px rgba(0, 180, 216, 0.22);'
            + '}'
            + '.ai-placement__select:disabled, .ai-placement__input:disabled {'
            +   'opacity: 0.55; cursor: not-allowed;'
            + '}'
            + '.ai-placement__select option {'
            +   'background: #0b1624; color: #E8F6FC;'
            + '}'
            + '.ai-config-panel {'
            +   'padding: 14px; border-bottom: 1px solid rgba(0, 180, 216, 0.22);'
            +   'background: rgba(11, 22, 36, 0.75);'
            + '}'
            + '.ai-config-panel[hidden] { display: none !important; }'
            + '.ai-config-title {'
            +   'font-size: 12.5px; font-weight: 600; margin: 0 0 10px; color: #3EE0FF;'
            +   'letter-spacing: 0.4px; text-transform: uppercase;'
            + '}'
            + '.ai-config-row { display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px; }'
            // 2026-04-24r -- tone toggle styling. Two-card radio with
            // a subtle teal highlight on the currently-checked option
            // and a slightly larger click target than the default
            // input/label pair.
            + '.ai-tone-toggle { display: flex; gap: 8px; }'
            + '.ai-tone-opt {'
            +   'flex: 1 1 0; display: flex; flex-direction: column; gap: 3px;'
            +   'padding: 8px 10px; border-radius: 8px; cursor: pointer;'
            +   'border: 1px solid rgba(255,255,255,0.12);'
            +   'background: rgba(255,255,255,0.03);'
            +   'transition: border-color 0.15s ease, background 0.15s ease;'
            + '}'
            + '.ai-tone-opt:hover { border-color: rgba(0, 180, 216, 0.55); background: rgba(0,180,216,0.06); }'
            + '.ai-tone-opt input { margin: 0 6px 0 0; }'
            + '.ai-tone-opt:has(input:checked) {'
            +   'border-color: rgba(0, 180, 216, 0.85);'
            +   'background: rgba(0, 180, 216, 0.12);'
            +   'box-shadow: 0 0 0 1px rgba(0, 180, 216, 0.28) inset;'
            + '}'
            + '.ai-tone-opt__title { font-weight: 600; font-size: 12.5px; color: #E8F6FC; }'
            + '.ai-tone-opt__body  { font-size: 11px; color: rgba(224,230,237,0.7); line-height: 1.35; }'
            + '.ai-config-row label {'
            +   'font-size: 11px; color: rgba(224, 230, 237, 0.70);'
            +   'letter-spacing: 0.4px; text-transform: uppercase; font-weight: 500;'
            + '}'
            + '.ai-input, .ai-select {'
            +   'padding: 8px 10px; border-radius: 7px;'
            +   'background: rgba(255,255,255,0.045); border: 1px solid rgba(255,255,255,0.14);'
            +   'color: #fff; font-size: 12.5px; font-family: inherit;'
            +   '-webkit-font-smoothing: antialiased;'
            + '}'
            + '.ai-input:focus, .ai-select:focus {'
            +   'outline: none; border-color: rgba(0, 180, 216, 0.75);'
            +   'box-shadow: 0 0 0 3px rgba(0, 180, 216, 0.22);'
            + '}'
            + '.ai-input::placeholder { color: rgba(224, 230, 237, 0.36); }'
            + '.ai-config-help {'
            +   'font-size: 11.5px; color: #B8C4D2;'
            +   'margin-top: -4px; margin-bottom: 6px; line-height: 1.5;'
            + '}'
            + '.ai-config-help a { color: #3EE0FF; }'
            + '.ai-config-model-custom { margin-top: 6px; }'
            + '.ai-config-key-head {'
            +   'display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap;'
            +   'justify-content: space-between;'
            + '}'
            + '.ai-config-key-head label { flex: 1 1 auto; min-width: 0; }'
            + '.ai-config-key-sub {'
            +   'color: rgba(224, 230, 237, 0.46); font-weight: 400;'
            +   'text-transform: none; letter-spacing: 0;'
            + '}'
            + '.ai-get-key {'
            +   'display: inline-flex; align-items: center; gap: 6px;'
            +   'padding: 4px 9px 4px 10px; border-radius: 999px;'
            +   'font-size: 10.5px; font-weight: 600; letter-spacing: 0.35px;'
            +   'text-transform: uppercase; text-decoration: none;'
            +   'color: #C6EAF6;'
            +   'background: linear-gradient(135deg, rgba(0, 180, 216, 0.22), rgba(0, 102, 250, 0.14));'
            +   'border: 1px solid rgba(0, 180, 216, 0.48);'
            +   'box-shadow: 0 2px 6px rgba(0, 82, 204, 0.24), inset 0 1px 0 rgba(255,255,255,0.10);'
            +   'transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease, transform 0.12s ease;'
            +   'white-space: nowrap; max-width: 100%;'
            + '}'
            + '.ai-get-key:hover {'
            +   'color: #fff; border-color: rgba(62, 224, 255, 0.78);'
            +   'background: linear-gradient(135deg, rgba(62, 224, 255, 0.32), rgba(0, 180, 216, 0.18));'
            +   'transform: translateY(-1px);'
            + '}'
            + '.ai-get-key:active { transform: translateY(0); }'
            + '.ai-get-key__host {'
            +   'font-weight: 500; text-transform: none; letter-spacing: 0;'
            +   'color: rgba(198, 234, 246, 0.72);'
            +   'overflow: hidden; text-overflow: ellipsis;'
            +   'max-width: 160px;'
            + '}'
            + '.ai-get-key__icon { color: rgba(198, 234, 246, 0.80); flex: none; }'
            /* Narrow drawer: hide the host string so the pill stays compact
               and the "API key (leave blank to keep current)" label keeps
               breathing room. The full host still appears in the title
               tooltip and the link href itself. */
            + '@media (max-width: 440px) {'
            +   '.ai-get-key__host { display: none; }'
            + '}'
            + '.ai-config-steps {'
            +   'display: flex; align-items: center; gap: 6px;'
            +   'color: rgba(198, 234, 246, 0.90); margin-top: 2px; margin-bottom: 8px;'
            +   'font-size: 11px; letter-spacing: 0.15px;'
            + '}'
            + '.ai-config-steps__icon {'
            +   'display: inline-flex; align-items: center; color: rgba(62, 224, 255, 0.80);'
            +   'flex: none;'
            + '}'
            /* --- Provider / key mismatch warning ---
               Surfaces right below the API key input when a pasted key's
               prefix (e.g. sk-ant-) doesn't match the currently-selected
               provider. The common case (and the reason this exists):
               user paste an OpenAI "sk-..." key while the Anthropic
               provider is selected -- Anthropic then returns an HTTP 401
               that bubbles up as "502 upstream" in chat and feels
               confusing. A soft warning + one-click switch is smoother
               than blocking save, since OpenAI-compatible endpoints also
               use "sk-" prefixes with a custom base_url.  */
            + '.ai-config-mismatch {'
            +   'display: flex; align-items: center; gap: 8px; flex-wrap: wrap;'
            +   'margin: 4px 0 6px;'
            +   'padding: 8px 10px;'
            +   'border-radius: 8px;'
            +   'background: linear-gradient(135deg, rgba(255, 94, 31, 0.14), rgba(255, 94, 31, 0.06));'
            +   'border: 1px solid rgba(255, 94, 31, 0.42);'
            +   'color: #FFD7C4; font-size: 11.5px; line-height: 1.45;'
            + '}'
            + '.ai-config-mismatch[hidden] { display: none !important; }'
            + '.ai-config-mismatch__icon {'
            +   'display: inline-flex; color: #FF8A55; flex: none;'
            + '}'
            + '.ai-config-mismatch__text { flex: 1 1 160px; min-width: 0; }'
            + '.ai-config-mismatch__text b { color: #fff; font-weight: 600; }'
            + '.ai-config-actions {'
            +   'display: flex; gap: 8px; justify-content: flex-end; margin-top: 6px;'
            + '}'
            + '.ai-config-saved-hint {'
            +   'display: block; font-size: 11.5px; color: #C6D2DF;'
            +   'margin-bottom: 10px; padding: 6px 9px;'
            +   'background: rgba(0, 180, 216, 0.08);'
            +   'border: 1px solid rgba(0, 180, 216, 0.22);'
            +   'border-radius: 6px;'
            + '}'
            + '.ai-config-saved-hint b { color: #FFFFFF; font-weight: 600; }'
            + '.ai-config-locked {'
            +   'display: flex; align-items: flex-start; gap: 8px;'
            +   'margin: 0 0 10px; padding: 8px 10px;'
            +   'border-radius: 8px;'
            +   'background: linear-gradient(135deg, rgba(100, 181, 246, 0.14), rgba(100, 181, 246, 0.06));'
            +   'border: 1px solid rgba(100, 181, 246, 0.42);'
            +   'color: #D6E4F5; font-size: 11.5px; line-height: 1.45;'
            + '}'
            + '.ai-config-locked__icon {'
            +   'display: inline-flex; color: #8FB6E8; flex: none; margin-top: 2px;'
            + '}'
            + '.ai-config-locked__text { flex: 1 1 160px; min-width: 0; }'
            + '.ai-config-locked__text b { color: #FFFFFF; font-weight: 600; }'
            + '.ai-config-locked__text code { background: rgba(0,0,0,0.25); padding: 1px 5px; border-radius: 4px; font-size: 11px; }'
            + '.ai-select:disabled {'
            +   'opacity: 0.55; cursor: not-allowed;'
            + '}'
            + '.ai-quickstart {'
            +   'display: flex; flex-direction: column; gap: 6px;'
            +   'padding: 12px 12px 11px; margin: 4px 0 12px;'
            +   'background: linear-gradient(135deg, rgba(0, 180, 216, 0.18), rgba(0, 102, 250, 0.14));'
            +   'border: 1px solid rgba(0, 180, 216, 0.55); border-radius: 10px;'
            +   'box-shadow: 0 4px 14px rgba(0, 82, 204, 0.22);'
            + '}'
            + '.ai-quickstart__title {'
            +   'display: flex; align-items: center; gap: 7px;'
            +   'font-size: 13px; font-weight: 700; color: #E8F6FC; letter-spacing: 0.2px;'
            + '}'
            + '.ai-quickstart__body {'
            +   'font-size: 11.5px; line-height: 1.45; color: rgba(224, 230, 237, 0.86);'
            +   'margin-bottom: 2px;'
            + '}'
            + '.ai-quickstart .ai-btn.primary { align-self: flex-start; }'
            + '.ai-config-advanced {'
            +   'margin: 6px 0 4px; border-top: 1px dashed rgba(255,255,255,0.10);'
            +   'padding-top: 8px;'
            + '}'
            + '.ai-config-advanced > summary {'
            +   'cursor: pointer; user-select: none;'
            +   'font-size: 11.5px; color: rgba(224, 230, 237, 0.68);'
            +   'letter-spacing: 0.25px; font-weight: 600;'
            +   'padding: 2px 0; outline: none;'
            + '}'
            + '.ai-config-advanced > summary:hover { color: #E0E6ED; }'
            + '.ai-config-advanced[open] > summary { color: #E0E6ED; margin-bottom: 6px; }'
            + '.ai-error { color: #FFA3A3; font-size: 11.5px; margin-top: 6px; }'
            + '.ai-drawer__footer {'
            +   'border-top: 1px solid rgba(0, 180, 216, 0.22);'
            +   'background: linear-gradient(180deg, rgba(8, 17, 28, 0.92), rgba(5, 12, 22, 0.98)); padding: 11px 12px 12px;'
            + '}'
            + '.ai-chips { display: flex; gap: 7px; flex-wrap: wrap; margin-bottom: 10px; }'
            // 2026-04-24i -- chip refinement: slightly-more-opaque fill
            // + softer cyan rim so the preset pills read as distinct
            // actionable shortcuts rather than ghost outlines. Brighter
            // text (0.92 vs 0.86 alpha) keeps them legible on the same
            // near-black composer base.
            + '.ai-chip {'
            +   'padding: 5px 11px; border-radius: 999px; font-size: 11px;'
            +   'font-family: inherit; font-weight: 500;'
            +   'background: rgba(255, 255, 255, 0.055);'
            +   'border: 1px solid rgba(62, 224, 255, 0.24);'
            +   'color: rgba(238, 248, 255, 0.92); cursor: pointer; letter-spacing: 0.2px;'
            +   '-webkit-font-smoothing: antialiased;'
            +   'transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease, transform 0.12s ease;'
            + '}'
            + '.ai-chip:hover {'
            +   'background: rgba(0, 180, 216, 0.24); border-color: rgba(62, 224, 255, 0.62);'
            +   'color: #FFFFFF; transform: translateY(-1px);'
            + '}'
            + '.ai-chip:active { transform: translateY(0); }'
            + '.ai-composer {'
            +   'display: flex; flex-direction: column; gap: 6px;'
            + '}'
            // 2026-04-24i -- composer input: slightly richer background
            // (0.055 vs 0.050) + brighter placeholder + a neutral
            // caret-colour hint so the cursor is visible even on pale
            // plates. Focus ring unchanged (the cyan halo was already
            // good).
            + '.ai-composer__input {'
            +   'width: 100%; resize: none; min-height: 46px; max-height: 180px;'
            +   'background: linear-gradient(180deg, rgba(255,255,255,0.075), rgba(255,255,255,0.045));'
            +   'border: 1px solid rgba(62, 224, 255, 0.24);'
            +   'border-radius: 12px; color: #FFFFFF;'
            +   'caret-color: #3EE0FF;'
            +   'padding: 9px 11px; font-size: 13px;'
            +   'line-height: 1.5; font-family: inherit; box-sizing: border-box;'
            +   'letter-spacing: 0.1px;'
            +   '-webkit-font-smoothing: antialiased;'
            + '}'
            + '.ai-composer__input::placeholder {'
            +   'color: rgba(225, 236, 247, 0.48); font-style: italic;'
            + '}'
            + '.ai-composer__input:focus {'
            +   'outline: none; border-color: rgba(0, 180, 216, 0.70);'
            +   'box-shadow: 0 0 0 3px rgba(0, 180, 216, 0.22);'
            + '}'
            + '.ai-composer__row { display: flex; align-items: center; justify-content: space-between; gap: 10px; }'
            + '.ai-composer__hint {'
            +   'font-size: 10.5px; color: rgba(224, 230, 237, 0.56); letter-spacing: 0.25px;'
            + '}'
            + '.ai-composer__send {'
            +   'display: inline-flex; align-items: center; gap: 6px;'
            +   'padding: 7px 13px; border-radius: 10px;'
            +   'font-family: inherit; font-size: 12.5px; font-weight: 600; letter-spacing: 0.25px;'
            +   '-webkit-font-smoothing: antialiased;'
            +   'background: linear-gradient(135deg, #00B4D8, #0066FA); color: #fff;'
            +   'border: 1px solid rgba(255,255,255,0.18);'
            +   'box-shadow: 0 4px 14px rgba(0, 82, 204, 0.42);'
            +   'cursor: pointer; transition: transform 0.12s ease, box-shadow 0.15s ease, background 0.15s ease;'
            + '}'
            + '.ai-composer__send:hover:not(:disabled) {'
            +   'transform: translateY(-1px);'
            +   'background: linear-gradient(135deg, #3EE0FF, #3385FF);'
            +   'box-shadow: 0 6px 18px rgba(0, 82, 204, 0.50);'
            + '}'
            + '.ai-composer__send:disabled { opacity: 0.55; cursor: not-allowed; }';
        var styleEl = document.createElement('style');
        styleEl.id = 'ai-drawer-styles';
        styleEl.textContent = css;
        document.head.appendChild(styleEl);
    }

    // --------------------------------------------------------------
    //   Events (drawer-level + composer + resizer + chips)
    // --------------------------------------------------------------
    function _wireDrawerEvents() {
        _drawerEl.addEventListener('click', function (e) {
            var btn = e.target.closest('[data-action]');
            if (!btn) return;
            var action = btn.dataset.action;
            if (action === 'close') close();
            else if (action === 'settings') _toggleConfigPanel();
            else if (action === 'new-chat') _clearConversation();
            else if (action === 'clear') _clearConversation(); // legacy alias
            else if (action === 'copy-transcript') _copyTranscript(btn);
            else if (action === 'export-markdown') _exportTranscriptAsMarkdown();
            else if (action === 'regenerate') _regenerateLastAnswer();
            else if (action === 'history') _toggleConvListPanel();
            else if (action === 'conv-close') _toggleConvListPanel(false);
            else if (action === 'conv-open') {
                var cid = btn.dataset.convId || '';
                if (cid) _openConversation(cid);
            }
            else if (action === 'conv-delete') {
                var did = btn.dataset.convId || '';
                if (did) {
                    var title = '';
                    (_conversations || []).some(function (c) {
                        if (c.id === did) { title = c.title || ''; return true; }
                        return false;
                    });
                    if (confirm('Delete conversation "' + (title || did.slice(0, 8)) + '"? This removes the full transcript.')) {
                        _deleteConversation(did);
                    }
                }
            }
            else if (action === 'conv-rename') {
                var rid = btn.dataset.convId || '';
                if (rid) {
                    var existing = '';
                    (_conversations || []).some(function (c) {
                        if (c.id === rid) { existing = c.title || ''; return true; }
                        return false;
                    });
                    var next = prompt('Rename conversation:', existing);
                    if (next !== null) _renameConversation(rid, next);
                }
            }
            // Error-card actions. Buttons come from _renderChatErrorCard.
            else if (action === 'ai-error-settings') _toggleConfigPanel(true);
            else if (action === 'ai-error-clear') _clearConversation();
            else if (action === 'ai-error-retry') {
                // Find the error card that holds this button and strip it
                // so the log reads cleanly after a successful retry. If
                // nothing to resend, just open the composer.
                var card = btn.closest('.ai-msg.error-card');
                if (card && card.dataset.id) _removeMessage(card.dataset.id);
                if (_lastUserMessage) {
                    _sendUserMessage(_lastUserMessage);
                } else {
                    var input = _drawerEl.querySelector('[data-role="composer-input"]');
                    if (input) input.focus();
                }
            }
            // 2026-04-24l -- one-click model swap for Gemini daily
            // quota hits. Each Gemini model has its own daily bucket,
            // so flipping gemini-2.5-flash <-> gemini-2.5-flash-lite
            // immediately unblocks the user without making them leave
            // the chat. We PUT the new model with api_key: '' so the
            // server reuses the stored key (see _handle_ai_config_put
            // in serve.py line ~2446).
            else if (action === 'ai-error-switch-gemini-model') {
                var targetModel = (btn.dataset.targetModel || '').trim();
                if (!targetModel) return;
                var errCard = btn.closest('.ai-msg.error-card');
                // Show a tiny inline status so the user sees feedback
                // while the save + retry lands. Swap the button out of
                // "click" state to avoid a double-fire.
                var prevLabel = btn.textContent;
                btn.disabled = true;
                btn.textContent = 'Switching...';
                (async function () {
                    try {
                        await _saveAiConfig({
                            provider: 'gemini',
                            model: targetModel,
                            base_url: '',
                            api_key: '',  // server reuses existing key
                        });
                        // Clear the error card now that we're retrying
                        // with a different model -- keeping it around
                        // would visually conflict with the new reply.
                        if (errCard && errCard.dataset.id) {
                            _removeMessage(errCard.dataset.id);
                        }
                        if (_lastUserMessage) {
                            _sendUserMessage(_lastUserMessage);
                        } else {
                            _appendSystem('Switched to ' + targetModel
                                + '. Send your next message whenever.');
                        }
                    } catch (err) {
                        btn.disabled = false;
                        btn.textContent = prevLabel;
                        _appendSystem('Could not switch model: '
                            + ((err && err.message) ? err.message : err));
                    }
                })();
            }
            // 2026-04-24t -- "Switch" button on the model-fallback
            // chip. The server already answered THIS turn using the
            // fallback model; clicking here persists that model as the
            // user's default so FUTURE turns start there, without a
            // page refresh or trip through the settings panel. We
            // reuse the same PUT-with-empty-api-key pattern as the
            // error-card gemini-model swap so the stored key stays
            // intact.
            else if (action === 'ai-switch-default-model') {
                var switchTarget = (btn.dataset.targetModel || '').trim();
                if (!switchTarget) return;
                var prevLbl = btn.textContent;
                btn.disabled = true;
                btn.textContent = 'Saving...';
                (async function () {
                    try {
                        await _saveAiConfig({
                            provider: (_aiConfig && _aiConfig.provider) || 'gemini',
                            model: switchTarget,
                            base_url: (_aiConfig && _aiConfig.base_url) || '',
                            api_key: '',  // server reuses existing key
                        });
                        btn.textContent = 'Saved';
                        btn.classList.add('ai-msg__fallback-btn--saved');
                        setTimeout(function () {
                            var chip = btn.closest('.ai-msg__fallback-chip');
                            if (chip) chip.classList.add('ai-msg__fallback-chip--saved');
                        }, 120);
                    } catch (err) {
                        btn.disabled = false;
                        btn.textContent = prevLbl;
                        _appendSystem('Could not save default model: '
                            + ((err && err.message) ? err.message : err));
                    }
                })();
            }
        });

        var composer = _drawerEl.querySelector('[data-role="composer"]');
        var input = _drawerEl.querySelector('[data-role="composer-input"]');
        var sendBtn = _drawerEl.querySelector('[data-role="send"]');

        input.addEventListener('input', function () {
            sendBtn.disabled = _sending || !input.value.trim();
            input.style.height = 'auto';
            input.style.height = Math.min(180, input.scrollHeight) + 'px';
        });
        input.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!sendBtn.disabled) composer.requestSubmit();
            }
        });
        composer.addEventListener('submit', function (e) {
            e.preventDefault();
            var text = input.value.trim();
            if (!text) return;
            input.value = '';
            input.style.height = 'auto';
            sendBtn.disabled = true;
            _sendUserMessage(text);
        });

        _drawerEl.querySelectorAll('.ai-chip').forEach(function (chip) {
            chip.addEventListener('click', function () {
                var prompt = _chipPrompt(chip.dataset.chip);
                if (!prompt) return;
                input.value = prompt;
                input.dispatchEvent(new Event('input'));
                input.focus();
            });
        });

        _wireResizer();
    }

    function _chipPrompt(id) {
        switch (id) {
            case 'clos':
                return 'Build a 4-leaf 2-spine Clos topology with eBGP between each leaf and both spines. Use 100G point-to-point links with /31 addresses, clean leaf/spine grouping, link labels, and 2-3 short annotations. Name: clos-4x2.';
            case 'dc-pod':
                return 'Build a DC pod with 2 border leafs, 4 ToR leafs, and 2 spines. Tag border leafs as DNAAS, spines as DNOS. Show leaf-spine and ToR-spine links clearly, with simplified grouping shapes and 2-3 concise callouts.';
            case 'explain-canvas':
                return 'Explain what is currently on my canvas: which devices, how many links, any VRFs, and anything that looks incomplete or unusual.';
            case 'shortcuts':
                return 'List the most useful keyboard shortcuts for the canvas (selection, copy, pan/zoom, and your own "A" to toggle this drawer).';
            default:
                return '';
        }
    }

    function _wireResizer() {
        var grip = _drawerEl.querySelector('.ai-drawer__resizer');
        if (!grip) return;
        var startX = 0, startW = 0;
        var onMove = function (e) {
            var dx = startX - e.clientX; // drag left grows width
            var w = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, startW + dx));
            _width = w;
            _drawerEl.style.width = w + 'px';
        };
        var onUp = function () {
            grip.classList.remove('dragging');
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
            document.body.style.userSelect = '';
            _lsSet(LS.width, _width);
        };
        grip.addEventListener('mousedown', function (e) {
            e.preventDefault();
            startX = e.clientX;
            startW = _drawerEl.getBoundingClientRect().width;
            grip.classList.add('dragging');
            document.body.style.userSelect = 'none';
            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onUp);
        });
    }

    // --------------------------------------------------------------
    //   Open / close / toggle
    // --------------------------------------------------------------
    function open() {
        _buildDrawer();
        if (!_drawerEl) return;
        // Strict mutex -- per user decision, opening AI closes the other
        // help/chat surfaces so the user never juggles two side panels.
        try {
            if (window.TopologyBugs && typeof window.TopologyBugs.close === 'function') {
                window.TopologyBugs.close();
            }
        } catch (_) {}
        try {
            if (window.TopologyShare && typeof window.TopologyShare.close === 'function') {
                window.TopologyShare.close();
            }
        } catch (_) {}
        // Global single-overlay mutex: opening the AI drawer auto-closes
        // every other registered "big overlay" (Scaler CONFIG stack,
        // in-browser terminal, debugger, BD legend, ...). See
        // topology-panel-mutex.js. Guarded so the app still boots if
        // the mutex module was deleted or failed to load.
        if (window.TopoPanelMutex) {
            try { window.TopoPanelMutex.markOpen('ai'); } catch (_) {}
        }

        _drawerEl.classList.add('open');
        _drawerEl.setAttribute('aria-hidden', 'false');
        _setLauncherActive(true);
        _lsSet(LS.open, '1');
        // Refresh config + canvas snapshot on every open so reconfigured
        // keys or just-loaded topologies surface without a full reload.
        _probeAiConfig().then(function () {
            if (_aiConfig.configured === false) {
                _toggleConfigPanel(true);
            } else {
                _toggleConfigPanel(false);
            }
        });
        // Paint fast from the localStorage cache, then reconcile with
        // the server in the background. This pattern (cache -> paint
        // -> fetch -> reconcile) keeps the drawer opening in <50ms
        // even over slow links, while still converging on the
        // authoritative transcript within seconds.
        if (_messages.length === 0) {
            var hydrated = _hydrateFromConvCache();
            if (hydrated) {
                _renderChatLog();
                _updateConvTitleChip();
            } else {
                _appendSystem(
                    'Hey! I remember our chats now. Ask anything, describe a topology to build, '
                    + 'or press the history icon above to revisit a past conversation. '
                    + 'Press "A" anywhere (outside text fields) to toggle me.'
                );
            }
        }
        _refreshConvListFromServer();
        setTimeout(function () {
            var input = _drawerEl && _drawerEl.querySelector('[data-role="composer-input"]');
            if (input) input.focus();
        }, 160);
    }

    function close() {
        if (!_drawerEl) {
            _setLauncherActive(false);
            _lsSet(LS.open, '0');
            if (window.TopoPanelMutex) {
                try { window.TopoPanelMutex.markClosed('ai'); } catch (_) {}
            }
            return;
        }
        _drawerEl.classList.remove('open');
        _drawerEl.setAttribute('aria-hidden', 'true');
        _setLauncherActive(false);
        _lsSet(LS.open, '0');
        if (window.TopoPanelMutex) {
            try { window.TopoPanelMutex.markClosed('ai'); } catch (_) {}
        }
    }

    function _isOpen() {
        return !!(_drawerEl && _drawerEl.classList.contains('open'));
    }

    function toggle() {
        if (_drawerEl && _drawerEl.classList.contains('open')) close();
        else open();
    }

    // --------------------------------------------------------------
    //   Config panel (inline AI setup -- BYOK)
    // --------------------------------------------------------------
    function _toggleConfigPanel(forceOpen) {
        if (!_drawerEl) return;
        var host = _drawerEl.querySelector('[data-role="config"]');
        if (!host) return;
        var wantOpen = (forceOpen === true) || (forceOpen === false ? false : host.hasAttribute('hidden'));
        if (wantOpen) {
            _renderConfigPanel(host);
            host.hidden = false;
        } else {
            host.hidden = true;
        }
    }

    // Pill-shaped shortcut rendered in the key-field header. Mirrors the
    // intent of bug panel's "get one ->" link (topology-bugs.js) but
    // styled for the dark AI drawer and with a small external-link
    // glyph so the user knows it jumps out of the app.
    // Build the <select> markup for the Model row. The currently-saved
    // model (if any) determines whether we pre-select a known preset or
    // drop into "Custom model...". Kept pure so the calling code can
    // splice it inline into the config panel HTML without any DOM work.
    function _renderModelSelect(preset, savedModel) {
        var models = Array.isArray(preset && preset.models) ? preset.models : [];
        var known = savedModel && _isKnownProviderModel(_providerIdFromPreset(preset), savedModel);
        // When no model is saved yet, highlight the first (recommended) option.
        var active = savedModel || (models[0] && models[0].id) || '';
        var html = '<select class="ai-select" data-role="cfg-model-select">';
        for (var i = 0; i < models.length; i += 1) {
            var m = models[i];
            var isActive = known ? (m.id === savedModel) : (i === 0 && !savedModel);
            html += '<option value="' + _escapeHtml(m.id) + '"' + (isActive ? ' selected' : '')
                 + '>' + _escapeHtml(m.label) + (m.note ? ' -- ' + _escapeHtml(m.note) : '')
                 + '</option>';
        }
        // If the saved model is NOT in the curated list (e.g. an older preset
        // we removed, or a compatible-endpoint model like
        // "together/qwen2-72b"), offer Custom pre-selected with the saved
        // value as the free-text default.
        var customSelected = (savedModel && !known) ? ' selected' : '';
        html += '<option value="__custom__"' + customSelected + '>Custom model name...</option>';
        html += '</select>';
        return html;
    }

    function _providerIdFromPreset(preset) {
        var keys = Object.keys(PROVIDER_PRESETS);
        for (var i = 0; i < keys.length; i += 1) {
            if (PROVIDER_PRESETS[keys[i]] === preset) return keys[i];
        }
        return '';
    }

    // Returns a sentence that describes what the selected model is best at
    // + the provider's general context/tooling note. Rendered just below
    // the dropdown so the user sees why one option is "recommended".
    function _modelHintFor(preset, modelId) {
        var base = (preset && preset.tokensHint) || '';
        var models = (preset && preset.models) || [];
        var note = '';
        for (var i = 0; i < models.length; i += 1) {
            if (models[i].id === modelId) { note = models[i].note || ''; break; }
        }
        if (note && base) return note + ' - ' + base;
        return note || base || '';
    }

    // Tiny subtext next to the "API key" label. Three states:
    //   * provider doesn't need a key (Ollama)         -> "(not required for Ollama)"
    //   * user already has a saved key on this provider -> "(leave blank to keep current)"
    //   * brand-new setup                               -> ""
    // Rebuilt on provider change so switching Claude -> Ollama at runtime
    // doesn't leave a stale "(leave blank...)" next to a field that isn't
    // checked anyway.
    function _keySubLabel(preset, current) {
        if (preset && preset.key_optional) {
            return '(not required for ' + (preset.short_label || 'local') + ')';
        }
        if (current && current.configured
            && (current.provider || '').toLowerCase() === _keyOfPreset(preset)) {
            return '(leave blank to keep current)';
        }
        return '';
    }

    function _keyOfPreset(preset) {
        var keys = Object.keys(PROVIDER_PRESETS);
        for (var i = 0; i < keys.length; i += 1) {
            if (PROVIDER_PRESETS[keys[i]] === preset) return keys[i];
        }
        return '';
    }

    function _renderGetKeyLink(preset) {
        if (!preset || !preset.get_key_url) return '';
        return ''
            + '<a class="ai-get-key"'
            +   ' href="' + _escapeHtml(preset.get_key_url) + '"'
            +   ' target="_blank" rel="noopener noreferrer"'
            +   ' data-role="cfg-get-key"'
            +   ' title="Opens ' + _escapeHtml(preset.get_key_host) + ' in a new tab">'
            +   '<span class="ai-get-key__label">Get a key</span>'
            +   '<span class="ai-get-key__host" data-role="cfg-get-key-host">' + _escapeHtml(preset.get_key_host) + '</span>'
            +   '<svg class="ai-get-key__icon" viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            +     '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
            +     '<polyline points="15 3 21 3 21 9"/>'
            +     '<line x1="10" y1="14" x2="21" y2="3"/>'
            +   '</svg>'
            + '</a>';
    }

    function _renderConfigPanel(host) {
        var presetKeys = Object.keys(PROVIDER_PRESETS);
        var current = _aiConfig || {};
        var provider = (current.provider || presetKeys[0]).toLowerCase();
        var preset = PROVIDER_PRESETS[provider] || PROVIDER_PRESETS[presetKeys[0]];
        var savedLabel = '';
        if (current.configured && current.token_hint) {
            var when = current.saved_at ? new Date(current.saved_at * 1000).toLocaleString() : '';
            // Prefer the curated short_label ("Anthropic" / "OpenAI") over
            // the raw backend id ("anthropic"/"openai") so the banner reads
            // the same as the dropdown. Fall back to the raw id if we ever
            // pick up a provider we don't have a preset for.
            var savedPreset = PROVIDER_PRESETS[(current.provider || '').toLowerCase()];
            var savedProviderLabel = (savedPreset && savedPreset.short_label) || current.provider || '?';
            savedLabel = 'Current: <b>' + _escapeHtml(savedProviderLabel) + '</b>'
                + (current.model ? ' &middot; model <b>' + _escapeHtml(current.model) + '</b>' : '')
                + ' &middot; key ' + _escapeHtml(current.token_hint)
                + (when ? ' &middot; saved ' + _escapeHtml(when) : '');
        }
        var options = presetKeys.map(function (k) {
            var p = PROVIDER_PRESETS[k];
            var sel = (k === provider) ? ' selected' : '';
            return '<option value="' + k + '"' + sel + '>' + _escapeHtml(p.label) + '</option>';
        }).join('');
        // Quick-start hero. Two variants, picked at render time from
        // the /api/ai/config response:
        //
        //   1. shared_gemini = true (operator exported GEMINI_API_KEY
        //      on the server): offer "Use Gemini (free, no setup)".
        //      Click -> save provider=gemini, model=gemini-2.5-flash,
        //      empty key. serve.py stashes "__server_shared__" as the
        //      stored key placeholder and the resolver swaps in the
        //      real env-var key at request time. This is the preferred
        //      default now that Gemini is the primary provider for
        //      the whole deployment.
        //
        //   2. Otherwise: keep the historical "Use local AI now" hero
        //      that auto-configures Ollama with the best installed
        //      local model. No key, no sign-up, no billing.
        //
        // Users who already have a saved config don't see a hero at
        // all to avoid visual noise.
        var heroHtml = '';
        if (!current.configured) {
            if (current.shared_gemini) {
                heroHtml = ''
                    + '<div class="ai-quickstart" data-role="cfg-hero">'
                    +   '<div class="ai-quickstart__title">'
                    +     '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>'
                    +     'Quick start: Gemini, free, no setup'
                    +   '</div>'
                    +   '<div class="ai-quickstart__body">'
                    +     'Uses Google Gemini 2.5 Flash via a shared key provided by this server. No API key, no sign-up, no billing.'
                    +   '</div>'
                    +   '<button type="button" class="ai-btn primary" data-role="cfg-quick-gemini">'
                    +     'Use Gemini now'
                    +   '</button>'
                    + '</div>';
            } else {
                heroHtml = ''
                    + '<div class="ai-quickstart" data-role="cfg-hero">'
                    +   '<div class="ai-quickstart__title">'
                    +     '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>'
                    +     'Quick start: free, on this server'
                    +   '</div>'
                    +   '<div class="ai-quickstart__body">'
                    +     'Uses a local AI running on the topology-app host. No API key, no sign-up, no billing.'
                    +   '</div>'
                    +   '<button type="button" class="ai-btn primary" data-role="cfg-quick-local">'
                    +     'Use local AI now'
                    +   '</button>'
                    + '</div>';
            }
        }
        // Forced-Gemini banner: when the server has exported
        // GEMINI_API_KEY AND the user doesn't have a personal AIza key
        // stored, the deployment is locked to Gemini. Explain why the
        // provider dropdown is disabled and that saves of other
        // providers will be rejected with HTTP 409. Kept small and
        // calm (no red), it's an info note not an error.
        var lockedHtml = '';
        if (current.forced) {
            lockedHtml = ''
                + '<div class="ai-config-locked" data-role="cfg-locked">'
                +   '<span class="ai-config-locked__icon" aria-hidden="true">'
                +     '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>'
                +   '</span>'
                +   '<span class="ai-config-locked__text">'
                +     'This deployment is locked to <b>Google Gemini</b> via a shared server key. '
                +     'Provider selection is disabled; model can still be changed. '
                +     'Paste a personal <code>AIza...</code> key below if you want your own quota.'
                +   '</span>'
                + '</div>';
        }
        // Gemini-only UI (2026-04-22): the provider row is always a
        // single option now, so we HIDE the <select> entirely (still
        // present in the DOM as a hidden input so _saveAiConfig and
        // the existing event handlers can read .value without
        // special-casing the one-provider case). The row styling
        // bloat goes with it, keeping the config panel short.
        var providerRowHidden = (presetKeys.length === 1) ? ' style="display:none"' : '';
        var providerDisabledAttr = current.forced ? ' disabled aria-disabled="true" title="Locked to Gemini by server admin"' : '';
        host.innerHTML = ''
            + '<h3 class="ai-config-title">AI Assistant &middot; Credentials</h3>'
            + (savedLabel ? '<div class="ai-config-saved-hint">' + savedLabel + '</div>' : '')
            + lockedHtml
            + heroHtml
            + '<div class="ai-config-row"' + providerRowHidden + '>'
            +   '<label>Provider</label>'
            +   '<select class="ai-select" data-role="cfg-provider"' + providerDisabledAttr + '>' + options + '</select>'
            + '</div>'
            + '<div class="ai-config-row">'
            +   '<label>Model</label>'
            +   _renderModelSelect(preset, current.model)
            +   '<input class="ai-input ai-config-model-custom" data-role="cfg-model-custom" type="text" value="' + _escapeHtml(current.model || '') + '" placeholder="e.g. ' + _escapeHtml(preset.model) + '" hidden />'
            +   '<p class="ai-config-help" data-role="cfg-model-hint">' + _escapeHtml(_modelHintFor(preset, current.model || preset.model)) + '</p>'
            + '</div>'
            + '<div class="ai-config-row ai-config-row--key">'
            +   '<div class="ai-config-key-head">'
            +     '<label>API key '
            +       '<span class="ai-config-key-sub" data-role="cfg-key-sub">'
            +         _escapeHtml(_keySubLabel(preset, current))
            +       '</span>'
            +     '</label>'
            +     _renderGetKeyLink(preset)
            +   '</div>'
            +   '<input class="ai-input" data-role="cfg-key" type="password" autocomplete="off" spellcheck="false" placeholder="' + _escapeHtml(preset.placeholder) + '" />'
            +   '<div class="ai-config-mismatch" data-role="cfg-mismatch" role="alert" aria-live="polite" hidden>'
            +     '<span class="ai-config-mismatch__icon" aria-hidden="true">'
            +       '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
            +     '</span>'
            +     '<span class="ai-config-mismatch__text">This looks like a <b data-role="cfg-mismatch-detected">?</b> key, but the selected provider is <b data-role="cfg-mismatch-current">?</b>.</span>'
            +     '<button type="button" class="ai-btn tiny" data-role="cfg-mismatch-switch">Switch to <span data-role="cfg-mismatch-switch-label">?</span></button>'
            +     '<button type="button" class="ai-btn tiny ghost" data-role="cfg-mismatch-dismiss" title="Dismiss for compatible providers">Use anyway</button>'
            +   '</div>'
            +   '<p class="ai-config-help ai-config-steps" data-role="cfg-steps">'
            +     '<span class="ai-config-steps__icon" aria-hidden="true">'
            +       '<svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
            +     '</span>'
            +     '<span data-role="cfg-steps-text">' + _escapeHtml(preset.steps) + '</span>'
            +   '</p>'
            +   '<p class="ai-config-help">Stored on THIS server under your per-user workspace (mode 0600). Never shared across users.</p>'
            + '</div>'
            // 2026-04-24r -- tone preamble. "senior" = the default
            // terse, CLI-ready style we ship today. "junior" = the
            // AI explains its reasoning, expands acronyms, and
            // over-narrates -- good for first-time users or for
            // tutoring. Stored in ai_config.json server-side so the
            // preamble is injected into the system prompt on every
            // turn (see serve.py::_build_ai_system_prompt).
            + '<div class="ai-config-row ai-tone-row">'
            +   '<label>Assistant tone</label>'
            +   '<div class="ai-tone-toggle" role="radiogroup" aria-label="Assistant tone">'
            +     '<label class="ai-tone-opt">'
            +       '<input type="radio" name="cfg-tone" value="senior"'
            +       ((current.tone || 'senior') === 'senior' ? ' checked' : '') + ' data-role="cfg-tone" />'
            +       '<span class="ai-tone-opt__title">Senior</span>'
            +       '<span class="ai-tone-opt__body">Terse, CLI-ready answers. Assumes DNOS fluency.</span>'
            +     '</label>'
            +     '<label class="ai-tone-opt">'
            +       '<input type="radio" name="cfg-tone" value="junior"'
            +       ((current.tone || 'senior') === 'junior' ? ' checked' : '') + ' data-role="cfg-tone" />'
            +       '<span class="ai-tone-opt__title">Junior</span>'
            +       '<span class="ai-tone-opt__body">Explains reasoning, expands acronyms, over-narrates. Good for onboarding.</span>'
            +     '</label>'
            +   '</div>'
            + '</div>'
            + '<details class="ai-config-advanced">'
            +   '<summary>Advanced</summary>'
            +   '<div class="ai-config-row">'
            +     '<label>Base URL (optional, for compatible providers)</label>'
            +     '<input class="ai-input" data-role="cfg-base-url" type="text" value="' + _escapeHtml(current.base_url || '') + '" placeholder="https://api.anthropic.com" />'
            +   '</div>'
            + '</details>'
            + '<div class="ai-error" data-role="cfg-error" hidden></div>'
            + '<div class="ai-config-actions">'
            +   (current.configured ? '<button type="button" class="ai-btn secondary" data-role="cfg-forget">Forget key</button>' : '')
            +   '<button type="button" class="ai-btn secondary" data-role="cfg-cancel">Cancel</button>'
            +   '<button type="button" class="ai-btn primary" data-role="cfg-save">Save</button>'
            + '</div>';

        var providerSel = host.querySelector('[data-role="cfg-provider"]');
        var modelSel    = host.querySelector('[data-role="cfg-model-select"]');
        var modelCustom = host.querySelector('[data-role="cfg-model-custom"]');
        var modelHint   = host.querySelector('[data-role="cfg-model-hint"]');
        var keyInput   = host.querySelector('[data-role="cfg-key"]');
        var baseInput  = host.querySelector('[data-role="cfg-base-url"]');
        var errBox     = host.querySelector('[data-role="cfg-error"]');
        var stepsText  = host.querySelector('[data-role="cfg-steps-text"]');
        var getKeyLink = host.querySelector('[data-role="cfg-get-key"]');
        var getKeyHost = host.querySelector('[data-role="cfg-get-key-host"]');
        var mismatchBox   = host.querySelector('[data-role="cfg-mismatch"]');
        var mismatchDet   = host.querySelector('[data-role="cfg-mismatch-detected"]');
        var mismatchCur   = host.querySelector('[data-role="cfg-mismatch-current"]');
        var mismatchSw    = host.querySelector('[data-role="cfg-mismatch-switch"]');
        var mismatchSwLab = host.querySelector('[data-role="cfg-mismatch-switch-label"]');
        var mismatchDis   = host.querySelector('[data-role="cfg-mismatch-dismiss"]');
        // Re-evaluated on every input/provider change. Session-scoped so
        // that "Use anyway" is sticky until the user re-opens the panel.
        var _mismatchDismissed = false;
        var _lastDetectedProvider = null;

        function _refreshMismatch() {
            if (!mismatchBox) return;
            var curPreset0 = PROVIDER_PRESETS[providerSel.value];
            // If the selected provider doesn't need a key (Ollama), there's
            // nothing to mismatch against -- stay quiet no matter what the
            // user typed.
            if (curPreset0 && curPreset0.key_optional) {
                mismatchBox.hidden = true;
                return;
            }
            var detected = _detectProviderFromKey(keyInput.value);
            _lastDetectedProvider = detected;
            if (_mismatchDismissed || !detected || detected === providerSel.value) {
                mismatchBox.hidden = true;
                return;
            }
            var detPreset = PROVIDER_PRESETS[detected];
            var curPreset = PROVIDER_PRESETS[providerSel.value];
            if (!detPreset || !curPreset) { mismatchBox.hidden = true; return; }
            if (mismatchDet) mismatchDet.textContent = detPreset.short_label || detected;
            if (mismatchCur) mismatchCur.textContent = curPreset.short_label || providerSel.value;
            if (mismatchSwLab) mismatchSwLab.textContent = detPreset.short_label || detected;
            if (mismatchSw) mismatchSw.setAttribute('data-target', detected);
            mismatchBox.hidden = false;
        }

        // When the user swaps providers we have to REBUILD the model
        // dropdown because each provider has its own curated list. We also
        // always reset to the new provider's first (recommended) model --
        // carrying over "claude-3-5-sonnet-latest" into OpenAI was the
        // footgun that started this whole thread.
        //
        // For Ollama we additionally fire off an async fetch of the LIVE
        // model inventory (`/api/ai/ollama/models`) and replace the hard-
        // coded preset list with what's actually on disk. Picking a model
        // the server didn't pull used to produce a chat-time "model not
        // found" error -- showing only installed tags makes that
        // impossible. The hardcoded list stays as a transient placeholder
        // so the dropdown never looks empty mid-fetch.
        function _rebuildModelSelectForProvider(providerId) {
            if (!modelSel) return;
            var p = PROVIDER_PRESETS[providerId];
            if (!p) return;
            var defaultModel = (p.models && p.models[0] && p.models[0].id) || '';
            modelSel.innerHTML = '';
            (p.models || []).forEach(function (m, idx) {
                var opt = document.createElement('option');
                opt.value = m.id;
                opt.textContent = m.label + (m.note ? ' -- ' + m.note : '');
                if (idx === 0) opt.selected = true;
                modelSel.appendChild(opt);
            });
            var customOpt = document.createElement('option');
            customOpt.value = '__custom__';
            customOpt.textContent = 'Custom model name...';
            modelSel.appendChild(customOpt);
            if (modelCustom) {
                modelCustom.hidden = true;
                modelCustom.value = '';
                modelCustom.placeholder = 'e.g. ' + defaultModel;
            }
            if (modelHint) modelHint.textContent = _modelHintFor(p, defaultModel);
            if (providerId === 'ollama') {
                _loadOllamaInstalledModels();
            }
        }

        // Replace the Ollama dropdown with models actually pulled on the
        // server. Called every time the provider flips to ollama. Falls
        // back gracefully: if the endpoint returns `{ok:false}` (Ollama
        // down) we keep the hardcoded placeholder list + show a hint.
        async function _loadOllamaInstalledModels() {
            if (!modelSel) return;
            if (modelHint) modelHint.textContent = 'Checking installed models on this server...';
            try {
                var resp = await _authFetch('/api/ai/ollama/models');
                var json = null;
                try { json = await resp.json(); } catch (_) { /* tolerated */ }
                if (!resp.ok || !json) throw new Error('HTTP ' + resp.status);

                // Only rebuild if the user is still on Ollama. If they
                // flipped back to OpenAI mid-fetch, leave their dropdown
                // alone.
                if (providerSel.value !== 'ollama') return;

                if (!json.installed) {
                    if (modelHint) {
                        modelHint.textContent = json.error
                            || 'Ollama runtime is not reachable on this server.';
                    }
                    return;
                }
                if (!json.models || !json.models.length) {
                    // Clear stale placeholder list -- an empty dropdown is
                    // actually clearer than showing models the user can't use.
                    modelSel.innerHTML = '';
                    var opt = document.createElement('option');
                    opt.value = '__custom__';
                    opt.textContent = 'Custom model name...';
                    modelSel.appendChild(opt);
                    if (modelHint) {
                        modelHint.textContent =
                            'No Ollama models installed on this server. Ask an admin '
                            + 'to run: ollama pull qwen2.5:7b-instruct';
                    }
                    return;
                }
                // Rebuild with real, on-disk models. Preserve the current
                // selection if it's still installed (prevents a surprise
                // reset while the user was mid-edit).
                var prevPick = modelSel.value;
                modelSel.innerHTML = '';
                json.models.forEach(function (m, idx) {
                    var o = document.createElement('option');
                    o.value = m.id;
                    var sizeBit = m.size_mb ? ' -- ' + Math.round(m.size_mb) + ' MB on disk' : '';
                    o.textContent = m.id + sizeBit;
                    if (m.id === prevPick || (idx === 0 && prevPick !== '__custom__')) {
                        o.selected = true;
                    }
                    modelSel.appendChild(o);
                });
                var custom = document.createElement('option');
                custom.value = '__custom__';
                custom.textContent = 'Custom model name...';
                if (prevPick === '__custom__') custom.selected = true;
                modelSel.appendChild(custom);
                var firstId = modelSel.value;
                if (modelHint) {
                    modelHint.textContent = json.count
                        + ' model' + (json.count === 1 ? '' : 's')
                        + ' installed locally on the server.';
                }
                // Refresh the visibility of the custom text input in case
                // the previous pick was Custom.
                _syncModelCustomVisibility();
            } catch (err) {
                if (modelHint) {
                    modelHint.textContent = 'Could not query local Ollama: '
                        + (err && err.message || 'unknown error');
                }
            }
        }

        // Show/hide the custom-model input and refresh the per-model hint
        // whenever the select changes. Keeping the custom input's value
        // blank when the user leaves "Custom" prevents stale text from
        // sneaking into the save payload.
        function _syncModelCustomVisibility() {
            if (!modelSel) return;
            var picked = modelSel.value;
            var p = PROVIDER_PRESETS[providerSel.value];
            if (picked === '__custom__') {
                if (modelCustom) {
                    modelCustom.hidden = false;
                    // focus only if the custom input is empty -- don't hijack
                    // focus when the user is merely scrolling the dropdown.
                    if (!modelCustom.value) setTimeout(function () { modelCustom.focus(); }, 0);
                }
                if (modelHint) modelHint.textContent = 'Type the exact API model id (used as-is).';
            } else {
                if (modelCustom) modelCustom.hidden = true;
                if (modelHint) modelHint.textContent = _modelHintFor(p, picked);
            }
        }
        if (modelSel) modelSel.addEventListener('change', _syncModelCustomVisibility);

        providerSel.addEventListener('change', function () {
            var p = PROVIDER_PRESETS[providerSel.value];
            if (!p) return;
            _rebuildModelSelectForProvider(providerSel.value);
            keyInput.placeholder = p.placeholder;
            if (stepsText) stepsText.textContent = p.steps || '';
            if (getKeyLink && p.get_key_url) {
                getKeyLink.href = p.get_key_url;
                getKeyLink.title = 'Opens ' + p.get_key_host + ' in a new tab';
            }
            if (getKeyHost) getKeyHost.textContent = p.get_key_host || '';
            // Update the "(not required / leave blank)" sub-label. Critical
            // when switching Claude -> Ollama at runtime: otherwise the
            // field reads "(leave blank to keep current)" next to a field
            // we no longer check, which is confusing.
            var keySub = host.querySelector('[data-role="cfg-key-sub"]');
            if (keySub) keySub.textContent = _keySubLabel(p, current);
            // Hint the base URL for local providers so users don't have to
            // know the magic Ollama port. We set a placeholder, not a
            // value, so existing overrides are preserved.
            if (baseInput) {
                baseInput.placeholder = p.default_base_url
                    ? p.default_base_url
                    : 'https://api.' + (p.short_label || providerSel.value).toLowerCase() + '.com';
            }
            // User intent changed -- give them a fresh chance to see
            // the warning instead of keeping a stale "Use anyway".
            _mismatchDismissed = false;
            _refreshMismatch();
        });
        // Initial-render pass: if the saved model isn't in the curated list
        // the select will already be on "__custom__" (see _renderModelSelect)
        // but we still need to expose the text input.
        _syncModelCustomVisibility();
        // If the saved provider is already Ollama, swap the hardcoded
        // list for the live one on open, same as on provider-change.
        if (provider === 'ollama') _loadOllamaInstalledModels();
        keyInput.addEventListener('input', _refreshMismatch);
        if (mismatchSw) {
            mismatchSw.addEventListener('click', function () {
                var target = mismatchSw.getAttribute('data-target');
                if (!target || !PROVIDER_PRESETS[target]) return;
                providerSel.value = target;
                // Manual `change` dispatch rebuilds the model <select> for
                // the target provider and resets to its recommended default
                // -- critical so we don't carry "claude-3-5-sonnet-latest"
                // into an OpenAI save.
                providerSel.dispatchEvent(new Event('change'));
            });
        }
        if (mismatchDis) {
            mismatchDis.addEventListener('click', function () {
                _mismatchDismissed = true;
                if (mismatchBox) mismatchBox.hidden = true;
            });
        }
        // Clicking "Get a key" opens the provider console in a new tab
        // AND focuses the API-key input on this tab, so when the user
        // returns with a freshly copied key the cursor is already in
        // the right place. No auto-paste -- browser security blocks it
        // across tabs and would feel creepy anyway.
        if (getKeyLink) {
            getKeyLink.addEventListener('click', function () {
                setTimeout(function () {
                    try { keyInput.focus({ preventScroll: false }); } catch (_) { keyInput.focus(); }
                }, 60);
            });
        }
        host.querySelector('[data-role="cfg-cancel"]').addEventListener('click', function () {
            _toggleConfigPanel(false);
        });
        // Quick-start hero: flip to Ollama, pick the first installed model
        // (fallback: the preset default), save with a blank key (server
        // stashes "ollama" placeholder). Zero input from the user.
        var quickLocalBtn = host.querySelector('[data-role="cfg-quick-local"]');
        if (quickLocalBtn) {
            quickLocalBtn.addEventListener('click', async function () {
                quickLocalBtn.disabled = true;
                var origLabel = quickLocalBtn.textContent;
                quickLocalBtn.textContent = 'Setting up local AI...';
                errBox.hidden = true; errBox.textContent = '';
                var chosenModel = '';
                try {
                    var resp = await _authFetch('/api/ai/ollama/models');
                    var j = null;
                    try { j = await resp.json(); } catch (_) {}
                    if (resp.ok && j && j.installed && j.models && j.models.length) {
                        chosenModel = j.models[0].id;
                    } else if (j && j.installed === false) {
                        throw new Error('Ollama is not running on this server. Ask an admin to start it.');
                    }
                } catch (err) {
                    errBox.textContent = (err && err.message) || 'Could not reach local Ollama.';
                    errBox.hidden = false;
                    quickLocalBtn.disabled = false;
                    quickLocalBtn.textContent = origLabel;
                    return;
                }
                if (!chosenModel) {
                    var olp = PROVIDER_PRESETS.ollama || {};
                    chosenModel = (olp.models && olp.models[0] && olp.models[0].id) || 'qwen2.5:7b-instruct';
                }
                _saveAiConfig({
                    provider: 'ollama',
                    model: chosenModel,
                    base_url: '',
                    api_key: '', // server stashes "ollama" placeholder
                }).then(function (ok) {
                    if (ok) {
                        _toast('Local AI ready -- model: ' + chosenModel, 'success');
                        _toggleConfigPanel(false);
                    } else {
                        quickLocalBtn.disabled = false;
                        quickLocalBtn.textContent = origLabel;
                    }
                }).catch(function (err) {
                    errBox.textContent = (err && err.message) || 'Failed to save AI credentials.';
                    errBox.hidden = false;
                    quickLocalBtn.disabled = false;
                    quickLocalBtn.textContent = origLabel;
                });
            });
        }
        // Quick-start hero (shared-Gemini variant): save a gemini config
        // with blank key. The server backs it with the GEMINI_API_KEY
        // env var at request time (__server_shared__ placeholder). Zero
        // input from the user -- they just click and can start prompting.
        // If the admin removes GEMINI_API_KEY later, the first chat
        // request gets a normal 401 and the error card nudges the user
        // to paste their own AIza key.
        var quickGeminiBtn = host.querySelector('[data-role="cfg-quick-gemini"]');
        if (quickGeminiBtn) {
            quickGeminiBtn.addEventListener('click', function () {
                quickGeminiBtn.disabled = true;
                var origLabel = quickGeminiBtn.textContent;
                quickGeminiBtn.textContent = 'Setting up Gemini...';
                errBox.hidden = true; errBox.textContent = '';
                var gp = PROVIDER_PRESETS.gemini || {};
                // 2026-04-24s -- default is now `gemini-2.5-flash-lite`
                // (first entry in the models list above). Preserved
                // fallback literal matches so a broken PROVIDER_PRESETS
                // never lands us on the heavier `-flash` bucket.
                var chosenModel = (gp.models && gp.models[0] && gp.models[0].id) || 'gemini-2.5-flash-lite';
                _saveAiConfig({
                    provider: 'gemini',
                    model: chosenModel,
                    base_url: '',
                    api_key: '', // server substitutes GEMINI_API_KEY env var
                }).then(function (ok) {
                    if (ok) {
                        _toast('Gemini ready -- model: ' + chosenModel, 'success');
                        _toggleConfigPanel(false);
                    } else {
                        quickGeminiBtn.disabled = false;
                        quickGeminiBtn.textContent = origLabel;
                    }
                }).catch(function (err) {
                    errBox.textContent = (err && err.message) || 'Failed to save AI credentials.';
                    errBox.hidden = false;
                    quickGeminiBtn.disabled = false;
                    quickGeminiBtn.textContent = origLabel;
                });
            });
        }
        host.querySelector('[data-role="cfg-save"]').addEventListener('click', function () {
            errBox.hidden = true; errBox.textContent = '';
            // Resolve the model id from either the curated <select> or the
            // Custom text input. If Custom is selected but the input is
            // empty, fall back to the provider's recommended default
            // instead of sending an empty model (which the backend rejects).
            var pNow = PROVIDER_PRESETS[providerSel.value] || {};
            var modelId = '';
            if (modelSel) {
                modelId = modelSel.value;
                if (modelId === '__custom__') {
                    modelId = (modelCustom && modelCustom.value || '').trim();
                    if (!modelId) modelId = (pNow.models && pNow.models[0] && pNow.models[0].id) || '';
                }
            }
            // 2026-04-24r -- carry the selected tone into the save
            // payload. Defaults to "senior" when the radio group
            // somehow isn't present (older cached HTML).
            var toneSel = 'senior';
            var toneEl = host.querySelector('input[name="cfg-tone"]:checked');
            if (toneEl && (toneEl.value === 'senior' || toneEl.value === 'junior')) {
                toneSel = toneEl.value;
            }
            var payload = {
                provider: providerSel.value,
                model: modelId,
                base_url: baseInput.value.trim(),
                api_key: keyInput.value,
                tone: toneSel,
            };
            _saveAiConfig(payload).then(function (ok) {
                if (ok) {
                    _toast('AI credentials saved.', 'success');
                    _toggleConfigPanel(false);
                }
            }).catch(function (err) {
                errBox.textContent = (err && err.message) || 'Failed to save AI credentials.';
                errBox.hidden = false;
            });
        });
        var forgetBtn = host.querySelector('[data-role="cfg-forget"]');
        if (forgetBtn) {
            forgetBtn.addEventListener('click', function () {
                if (!window.confirm('Delete your AI credentials from this server?')) return;
                _deleteAiConfig().then(function () {
                    _toast('AI credentials deleted.', 'info');
                    _renderConfigPanel(host);
                });
            });
        }
    }

    async function _probeAiConfig() {
        if (window.TopologyAuth && typeof window.TopologyAuth.isAuthenticated === 'function'
            && !window.TopologyAuth.isAuthenticated()) {
            _aiConfig = { configured: null, provider: '', model: '', token_hint: '', saved_at: 0, shared_gemini: false, forced: false };
            _updateNeedsSetupBadge();
            _renderProviderBadge();
            return;
        }
        try {
            var resp = await _authFetch('/api/users/me/ai-config');
            if (resp.status === 401) {
                _aiConfig = { configured: null, provider: '', model: '', token_hint: '', saved_at: 0, shared_gemini: false, forced: false };
                _updateNeedsSetupBadge();
                _renderProviderBadge();
                return;
            }
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            var json = await resp.json();
            // shared_gemini tells the config panel's Quick-start hero
            // whether the operator has exported GEMINI_API_KEY on the
            // server. forced tells the panel that this deployment is
            // locked to Gemini (the resolver ignores any stored non-
            // Gemini provider) so we should disable the provider picker
            // and show a "Locked" banner. Never store the actual key
            // client-side -- the server resolves it at request time
            // (see resolve_client_for_user).
            _aiConfig = {
                configured: !!json.configured,
                provider: json.provider || '',
                model: json.model || '',
                base_url: json.base_url || '',
                token_hint: json.token_hint || '',
                saved_at: json.saved_at || 0,
                shared_gemini: !!json.shared_gemini,
                forced: !!json.forced,
                // 2026-04-24r -- server-persisted tone preamble.
                // Falls back to "senior" when the server returns an
                // older schema (no tone field) so the UI doesn't
                // show an empty radio group.
                tone: (function () {
                    var t = (json.tone || '').toString().toLowerCase();
                    return (t === 'senior' || t === 'junior') ? t : 'senior';
                })(),
            };
            // Gemini-only UI (2026-04-22): if the server returned a
            // legacy provider (groq / openai / anthropic / ollama) for
            // this user, silently migrate their config to Gemini so
            // the drawer never asks them to pick again. If they had
            // an AIza key for Gemini we keep it; for all other key
            // prefixes we blank the key and surface the Gemini quick-
            // start hero on the next render. The PUT is fire-and-
            // forget -- worst case the user sees one extra error card
            // if the server rejected, and the next render re-probes.
            var currentProvider = (_aiConfig.provider || '').toLowerCase();
            if (currentProvider && LEGACY_PROVIDERS_TO_MIGRATE.indexOf(currentProvider) !== -1) {
                try {
                    console.info('[AI] Migrating legacy ' + currentProvider + ' config to Gemini (UI is Gemini-only).');
                    await _authFetch('/api/users/me/ai-config', {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            provider: 'gemini',
                            // 2026-04-24s -- legacy migrations now land
                            // on `gemini-2.5-flash-lite` (lightest / own
                            // quota bucket) so rescued users get the
                            // same default as fresh signups.
                            model: 'gemini-2.5-flash-lite',
                            base_url: '',
                            // Intentionally blank: a stale gsk_/sk-/sk-ant-
                            // key won't work with Gemini. User can paste
                            // an AIza key or the server's shared key
                            // picks it up automatically.
                            api_key: '',
                        }),
                    });
                    // Re-probe so _aiConfig reflects the new state
                    // (configured may flip to false until the server
                    // either has a shared key or the user pastes AIza).
                    var r2 = await _authFetch('/api/users/me/ai-config');
                    if (r2.ok) {
                        var j2 = await r2.json();
                        _aiConfig = {
                            configured: !!j2.configured,
                            provider: j2.provider || 'gemini',
                            model: j2.model || 'gemini-2.5-flash-lite',
                            base_url: j2.base_url || '',
                            token_hint: j2.token_hint || '',
                            saved_at: j2.saved_at || 0,
                            shared_gemini: !!j2.shared_gemini,
                            forced: !!j2.forced,
                        };
                    }
                } catch (e) {
                    console.warn('[AI] Legacy-provider migration failed:', e);
                }
            }
        } catch (_) {
            _aiConfig = { configured: false, provider: '', model: '', token_hint: '', saved_at: 0, shared_gemini: false, forced: false };
        }
        _updateNeedsSetupBadge();
        _renderProviderBadge();
    }

    async function _saveAiConfig(payload) {
        var resp = await _authFetch('/api/users/me/ai-config', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        var json = null;
        try { json = await resp.json(); } catch (_) {}
        if (!resp.ok || !json || !json.ok) {
            throw new Error((json && json.error) || ('HTTP ' + resp.status));
        }
        _aiConfig = {
            configured: true,
            provider: json.provider || payload.provider,
            model: json.model || payload.model,
            base_url: json.base_url || payload.base_url,
            token_hint: json.token_hint || '',
            saved_at: json.saved_at || 0,
            shared_gemini: !!json.shared_gemini,
            forced: !!json.forced,
        };
        _updateNeedsSetupBadge();
        _renderProviderBadge();
        return true;
    }

    async function _deleteAiConfig() {
        try {
            await _authFetch('/api/users/me/ai-config', { method: 'DELETE' });
        } catch (_) {}
        // Preserve the shared_gemini / forced flags: deleting a user
        // config does NOT remove the server-side GEMINI_API_KEY env
        // var, so the Quick-start hero should still offer the Gemini
        // shared-key path on the next render. `forced` stays true for
        // a no-config state under shared-key mode because the server
        // still force-overrides to Gemini at resolve time.
        var prevSharedGemini = !!(_aiConfig && _aiConfig.shared_gemini);
        _aiConfig = { configured: false, provider: '', model: '', token_hint: '', saved_at: 0, shared_gemini: prevSharedGemini, forced: prevSharedGemini };
        _updateNeedsSetupBadge();
        _renderProviderBadge();
    }

    function _renderProviderBadge() {
        if (!_drawerEl) return;
        var badge = _drawerEl.querySelector('[data-role="provider-badge"]');
        if (!badge) return;
        if (_aiConfig.configured && _aiConfig.provider) {
            var label = _aiConfig.provider;
            if (_aiConfig.model) label += ' / ' + _aiConfig.model;
            badge.textContent = label;
            badge.hidden = false;
        } else {
            badge.hidden = true;
        }
    }

    // --------------------------------------------------------------
    //   Chat plumbing
    // --------------------------------------------------------------
    function _clearConversation() {
        // "Start a new chat" semantics: archive the current (so it
        // stays in history, but out of the default list) and open a
        // fresh, empty conversation. Non-destructive -- the user can
        // still scroll back to the archived chat from the history
        // panel and delete it explicitly if they want it gone.
        var oldId = _currentConvId;
        if (oldId) {
            _authFetch('/api/ai/conversations/' + encodeURIComponent(oldId), {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ archived: true }),
            }).catch(function () { /* non-fatal */ });
        }
        _currentConvId = null;
        _currentConvTitle = '';
        _messages.length = 0;
        _lastUserMessage = '';
        _renderChatLog();
        _updateConvTitleChip();
        _appendSystem('New chat started. Previous conversation archived -- open the history panel to revisit it.');
        _saveConvCache();
        // Refresh the list in the background so the just-archived chat
        // moves into the archived bucket the next time the panel opens.
        _refreshConvListFromServer();
    }

    // --------------------------------------------------------------
    //   Toolbar helpers (Copy / Regenerate / Export / state)
    // --------------------------------------------------------------
    //
    // 2026-04-24s -- user asked for a "clear new chat button and more
    // options for better usability". We already had a pencil icon in
    // the header that archived the current chat, but it was a) not
    // labelled, b) mixed in with settings/close, and c) had no
    // companion actions. The sub-header toolbar exposes:
    //
    //   + New chat     -- primary, archives the current and opens empty
    //   Copy           -- clipboard copy of the whole transcript (md)
    //   Regenerate     -- re-ask the last user prompt, removes the
    //                     outdated assistant answer(s) first
    //   [download]     -- export chat as <title>-<timestamp>.md
    //
    // The strip is INTENTIONALLY outside .ai-drawer__body so the
    // absolute-positioned settings and history overlays can't hide it.

    function _transcriptUserTurns() {
        // Count "real" exchange turns (user messages) so we can disable
        // Copy / Regenerate / Export when the chat has nothing to copy.
        // Notices and tool-only assistant frames don't count on their
        // own -- if the user hasn't sent anything, there's no point.
        var n = 0;
        for (var i = 0; i < _messages.length; i += 1) {
            if (_messages[i].role === 'user') n += 1;
        }
        return n;
    }

    function _buildTranscriptMarkdown() {
        // Renders _messages as a portable Markdown transcript. Used by
        // both "Copy" (clipboard) and "Export" (file download). We keep
        // the format simple and stable so diffing two exports works.
        var lines = [];
        var title = _currentConvTitle || 'Untitled chat';
        lines.push('# ' + title);
        var provider = (_aiConfig && _aiConfig.provider) ? _aiConfig.provider : '';
        var model = (_aiConfig && _aiConfig.model) ? _aiConfig.model : '';
        var stampIso = new Date().toISOString();
        var meta = ['Exported: ' + stampIso];
        if (provider) meta.push('Provider: ' + provider + (model ? ' / ' + model : ''));
        lines.push('');
        lines.push('> ' + meta.join(' \u00b7 '));
        lines.push('');
        for (var i = 0; i < _messages.length; i += 1) {
            var m = _messages[i];
            if (!m || m.loading) continue; // in-flight bubbles have no real text
            var role = m.role || 'system';
            var heading;
            if (role === 'user') heading = '**You**';
            else if (role === 'assistant') heading = '**Assistant**' + (m.error ? ' (error)' : '');
            else if (role === 'tool') heading = '**Tool output**';
            else heading = '_System_';
            var body = (m.content == null) ? '' : String(m.content);
            // Tool-only assistant replies sometimes have no `content`
            // but carry `tool_calls`. Fall back to a short summary so
            // the transcript isn't mysteriously blank.
            if (!body.trim() && Array.isArray(m.tool_calls) && m.tool_calls.length) {
                var names = m.tool_calls.map(function (c) { return (c && c.name) || '(unnamed)'; });
                body = '(tool call: ' + names.join(', ') + ')';
            }
            lines.push(heading);
            lines.push('');
            lines.push(body || '_(empty)_');
            lines.push('');
        }
        return lines.join('\n').replace(/\n{3,}/g, '\n\n').trimEnd() + '\n';
    }

    function _fallbackCopy(text) {
        // Clipboard API is unavailable on non-HTTPS / non-localhost in
        // some browsers. Falling back to execCommand('copy') keeps the
        // button useful in those environments.
        try {
            var ta = document.createElement('textarea');
            ta.value = text;
            ta.setAttribute('readonly', '');
            ta.style.position = 'fixed';
            ta.style.left = '-9999px';
            document.body.appendChild(ta);
            ta.select();
            var ok = document.execCommand('copy');
            document.body.removeChild(ta);
            return !!ok;
        } catch (_) { return false; }
    }

    function _flashToolbarBtn(btn) {
        // Brief cyan flash so the user knows the click landed without
        // needing the toast to be visible. Matches the existing
        // pattern used by the error-card buttons.
        if (!btn) return;
        btn.classList.add('ai-chat-toolbar__btn--flash');
        setTimeout(function () { btn.classList.remove('ai-chat-toolbar__btn--flash'); }, 600);
    }

    function _copyTranscript(sourceBtn) {
        if (_transcriptUserTurns() === 0) {
            _toast('Nothing to copy yet -- send a message first.', 'info');
            return;
        }
        var md = _buildTranscriptMarkdown();
        var done = function (ok) {
            if (ok) { _flashToolbarBtn(sourceBtn); _toast('Chat copied to clipboard.', 'success'); }
            else { _toast('Could not copy to clipboard.', 'error'); }
        };
        try {
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(md).then(function () { done(true); }, function () {
                    done(_fallbackCopy(md));
                });
                return;
            }
        } catch (_) { /* fall through to execCommand */ }
        done(_fallbackCopy(md));
    }

    function _exportTranscriptAsMarkdown() {
        if (_transcriptUserTurns() === 0) {
            _toast('Nothing to export yet -- send a message first.', 'info');
            return;
        }
        var md = _buildTranscriptMarkdown();
        var safeTitle = (_currentConvTitle || 'chat')
            .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 48) || 'chat';
        var stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        var fname = 'ai-' + safeTitle + '-' + stamp + '.md';
        try {
            var blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
            var url = URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url; a.download = fname;
            document.body.appendChild(a);
            a.click();
            setTimeout(function () {
                try { document.body.removeChild(a); } catch (_) {}
                try { URL.revokeObjectURL(url); } catch (_) {}
            }, 0);
            _toast('Exported ' + fname, 'success');
        } catch (e) {
            _toast('Could not export chat: ' + (e && e.message ? e.message : e), 'error');
        }
    }

    function _regenerateLastAnswer() {
        if (_sending) {
            _toast('Still waiting on the current answer -- use Stop inside the thinking bubble first.', 'info');
            return;
        }
        if (!_lastUserMessage) {
            _toast('No previous message to regenerate. Send something first.', 'info');
            return;
        }
        // Strip trailing assistant / tool / system messages that came
        // AFTER the last user turn so the transcript doesn't show two
        // answers to the same question. We keep the last user message
        // itself -- _sendUserMessage will re-append a fresh copy.
        var lastUserIdx = -1;
        for (var i = _messages.length - 1; i >= 0; i -= 1) {
            if (_messages[i].role === 'user') { lastUserIdx = i; break; }
        }
        if (lastUserIdx === -1) {
            _toast('No previous message to regenerate.', 'info');
            return;
        }
        // Drop everything AT or AFTER the last user so _sendUserMessage
        // can re-add the user bubble (preserves the existing flow,
        // including tool_call execution and conversation_id propagation).
        _messages.splice(lastUserIdx);
        _renderChatLog();
        _sendUserMessage(_lastUserMessage);
    }

    function _updateChatToolbarState() {
        if (!_drawerEl) return;
        var bar = _drawerEl.querySelector('[data-role="chat-toolbar"]');
        if (!bar) return;
        var hasTurns = _transcriptUserTurns() > 0;
        var busy = !!_sending;
        bar.classList.toggle('ai-chat-toolbar--busy', busy);
        var copyBtn = bar.querySelector('[data-action="copy-transcript"]');
        var exportBtn = bar.querySelector('[data-action="export-markdown"]');
        var regenBtn = bar.querySelector('[data-action="regenerate"]');
        var newBtn = bar.querySelector('[data-action="new-chat"]');
        if (copyBtn) copyBtn.disabled = !hasTurns;
        if (exportBtn) exportBtn.disabled = !hasTurns;
        if (regenBtn) regenBtn.disabled = busy || !_lastUserMessage;
        if (newBtn) newBtn.disabled = busy; // don't archive mid-send
    }

    // ---- Conversation API helpers (server-side persistence) -------

    async function _refreshConvListFromServer(opts) {
        opts = opts || {};
        if (_convListSyncing) return;
        _convListSyncing = true;
        try {
            var qs = opts.includeArchived ? '?archived=1' : '';
            var resp = await _authFetch('/api/ai/conversations' + qs);
            if (!resp || !resp.ok) return;
            var json = await resp.json().catch(function () { return null; });
            if (!json || !Array.isArray(json.conversations)) return;
            _conversations = json.conversations;
            _saveConvCache();
            if (_convListOpen) _renderConvListPanel();
        } catch (_) {
            // Offline or auth error: leave the cached list as-is.
        } finally {
            _convListSyncing = false;
        }
    }

    async function _openConversation(convId) {
        if (!convId) return;
        try {
            var resp = await _authFetch('/api/ai/conversations/' + encodeURIComponent(convId));
            if (!resp || !resp.ok) {
                _appendSystem('Could not load conversation (server returned ' + (resp && resp.status) + ').');
                return;
            }
            var json = await resp.json();
            var conv = json && json.conversation;
            if (!conv) return;
            _currentConvId = conv.id;
            _currentConvTitle = conv.title || '';
            _messages.length = 0;
            (conv.messages || []).forEach(function (m) {
                if (m.role !== 'user' && m.role !== 'assistant') return;
                var content = m.content || '';
                var toolCalls = Array.isArray(m.tool_calls) ? m.tool_calls : [];
                // 2026-04-24i -- tool-only assistant replies come back
                // with content = "" and the real payload in
                // `tool_calls`. Before this fix we only copied
                // `content`, so a previously-opened "add a device"
                // conversation rendered as an EMPTY assistant bubble
                // with no indication that the canvas had been edited.
                // Synthesize a short text summary from each tool_call
                // so the re-opened conversation reads sensibly.
                //
                // We deliberately do NOT rebuild the live
                // `{ tool, receipt, applied: true }` object -- those
                // drive apply/save/undo buttons that would duplicate
                // work if clicked (add_device runs again, etc.). A
                // text summary is the safer historical record.
                if (!content.trim() && toolCalls.length > 0) {
                    var lines = toolCalls.map(function (tc) {
                        var tname = tc && tc.name || 'tool';
                        var summary = (tc && tc.summary || '').toString().trim();
                        if (tname === 'apply_canvas_edits') {
                            var editCount = (tc && Array.isArray(tc.edits)) ? tc.edits.length : 0;
                            var detail = summary
                                ? summary
                                : (editCount
                                    ? (editCount + ' edit' + (editCount === 1 ? '' : 's'))
                                    : 'no changes');
                            return '\u2713 Canvas updated: ' + detail;
                        }
                        if (tname === 'create_topology') {
                            var tmeta = tc && tc.topology && tc.topology.metadata;
                            var topoName = (tc && tc.display_name)
                                || (tc && tc.suggested_name)
                                || (tmeta && tmeta.name)
                                || 'ai-topology';
                            return '\u2713 Topology "' + topoName + '" was generated';
                        }
                        return '\u2713 Tool used: ' + tname;
                    });
                    content = lines.join('\n');
                }
                // Preserve the retry chip on history turns too -- the
                // backend writes retry_info to the DB whenever a turn
                // auto-recovered (rate-limit / model-overload / CDN
                // challenge). Without this the chip only shows on the
                // live turn and disappears after reload, which lies
                // about what actually happened on that turn.
                var retryInfo = m.retry_info || null;
                _messages.push({
                    _id: _nextId(),
                    role: m.role,
                    content: content,
                    loading: false,
                    error: false,
                    retryInfo: retryInfo,
                });
            });
            _lastUserMessage = '';
            // Find the last user message for the Retry button (we no
            // longer surface failed turns, but keep the retry action
            // primed).
            for (var i = _messages.length - 1; i >= 0; i--) {
                if (_messages[i].role === 'user') {
                    _lastUserMessage = _messages[i].content || '';
                    break;
                }
            }
            _renderChatLog();
            _updateConvTitleChip();
            _saveConvCache();
            _toggleConvListPanel(false);
        } catch (e) {
            _appendSystem('Could not load conversation: ' + (e && e.message ? e.message : e));
        }
    }

    async function _deleteConversation(convId) {
        if (!convId) return;
        try {
            var resp = await _authFetch('/api/ai/conversations/' + encodeURIComponent(convId), {
                method: 'DELETE',
            });
            if (!resp.ok) return;
            if (convId === _currentConvId) {
                _currentConvId = null;
                _currentConvTitle = '';
                _messages.length = 0;
                _renderChatLog();
                _updateConvTitleChip();
            }
            _conversations = (_conversations || []).filter(function (c) { return c.id !== convId; });
            _saveConvCache();
            if (_convListOpen) _renderConvListPanel();
        } catch (_) { /* non-fatal */ }
    }

    async function _renameConversation(convId, title) {
        if (!convId) return;
        title = (title || '').trim();
        if (!title) return;
        try {
            var resp = await _authFetch('/api/ai/conversations/' + encodeURIComponent(convId), {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: title }),
            });
            if (!resp.ok) return;
            var json = await resp.json().catch(function () { return null; });
            var updated = json && json.conversation;
            if (updated) {
                _conversations = (_conversations || []).map(function (c) {
                    return c.id === convId ? updated : c;
                });
                if (convId === _currentConvId) {
                    _currentConvTitle = updated.title || '';
                    _updateConvTitleChip();
                }
                _saveConvCache();
                if (_convListOpen) _renderConvListPanel();
            }
        } catch (_) { /* non-fatal */ }
    }

    function _updateConvTitleChip() {
        if (!_drawerEl) return;
        var chip = _drawerEl.querySelector('[data-role="conv-title-chip"]');
        if (!chip) return;
        if (_currentConvTitle) {
            chip.textContent = _currentConvTitle;
            chip.hidden = false;
        } else {
            chip.textContent = '';
            chip.hidden = true;
        }
    }

    function _toggleConvListPanel(force) {
        if (!_drawerEl) return;
        var next = typeof force === 'boolean' ? force : !_convListOpen;
        _convListOpen = next;
        var panel = _drawerEl.querySelector('[data-role="conv-list"]');
        if (!panel) return;
        panel.hidden = !next;
        if (next) {
            _renderConvListPanel();
            _refreshConvListFromServer();
        }
    }

    function _formatRelativeTime(ts) {
        if (!ts) return '';
        var diff = Date.now() - ts;
        if (diff < 60_000) return 'just now';
        if (diff < 3600_000) return Math.floor(diff / 60_000) + 'm ago';
        if (diff < 86400_000) return Math.floor(diff / 3600_000) + 'h ago';
        if (diff < 7 * 86400_000) return Math.floor(diff / 86400_000) + 'd ago';
        try {
            return new Date(ts).toLocaleDateString();
        } catch (_) { return ''; }
    }

    function _renderConvListPanel() {
        if (!_drawerEl) return;
        var panel = _drawerEl.querySelector('[data-role="conv-list"]');
        if (!panel) return;
        var list = _conversations || [];
        // Recent-first (server already sorts; defensive re-sort in case
        // we merge a locally-created conv that the server hasn't ack'd).
        var sorted = list.slice().sort(function (a, b) {
            return (b.updated_at || 0) - (a.updated_at || 0);
        });
        var rows = sorted.map(function (c) {
            var isCurrent = c.id === _currentConvId;
            return ''
                + '<div class="ai-conv-row' + (isCurrent ? ' ai-conv-row--current' : '') + '" data-conv-id="' + _escapeHtml(c.id) + '">'
                +   '<button type="button" class="ai-conv-row__main" data-action="conv-open" data-conv-id="' + _escapeHtml(c.id) + '" title="Open this conversation">'
                +     '<span class="ai-conv-row__title">' + _escapeHtml(c.title || 'Untitled') + '</span>'
                +     '<span class="ai-conv-row__meta">'
                +       _escapeHtml(String(c.turn_count || 0)) + ' turns \u00b7 '
                +       _escapeHtml(_formatRelativeTime(c.updated_at))
                +     '</span>'
                +   '</button>'
                +   '<div class="ai-conv-row__actions">'
                +     '<button type="button" class="ai-conv-row__btn" data-action="conv-rename" data-conv-id="' + _escapeHtml(c.id) + '" title="Rename" aria-label="Rename">'
                +       '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                +         '<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/>'
                +       '</svg>'
                +     '</button>'
                +     '<button type="button" class="ai-conv-row__btn ai-conv-row__btn--danger" data-action="conv-delete" data-conv-id="' + _escapeHtml(c.id) + '" title="Delete" aria-label="Delete">'
                +       '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                +         '<polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>'
                +       '</svg>'
                +     '</button>'
                +   '</div>'
                + '</div>';
        }).join('');
        panel.innerHTML = ''
            + '<div class="ai-conv-list__head">'
            +   '<span class="ai-conv-list__title">Conversations</span>'
            +   '<label class="ai-conv-list__archived">'
            +     '<input type="checkbox" data-role="conv-archived-toggle"> show archived'
            +   '</label>'
            +   '<button type="button" class="ai-drawer__icon-btn" data-action="conv-close" title="Hide history" aria-label="Hide history">'
            +     '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
            +       '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>'
            +     '</svg>'
            +   '</button>'
            + '</div>'
            + '<div class="ai-conv-list__body">'
            +   (rows || '<div class="ai-conv-empty">No previous conversations. Start chatting and they appear here.</div>')
            + '</div>';
        var toggle = panel.querySelector('[data-role="conv-archived-toggle"]');
        if (toggle) {
            toggle.addEventListener('change', function () {
                _refreshConvListFromServer({ includeArchived: toggle.checked });
            });
        }
    }

    function _hydrateFromConvCache() {
        var cached = _loadConvCache();
        if (!cached) return false;
        if (Array.isArray(cached.conversations)) _conversations = cached.conversations;
        _currentConvId = cached.currentId || null;
        _currentConvTitle = cached.currentTitle || '';
        if (Array.isArray(cached.currentMessages) && cached.currentMessages.length > 0) {
            _messages.length = 0;
            cached.currentMessages.forEach(function (m) {
                _messages.push({
                    _id: _nextId(),
                    role: m.role || 'assistant',
                    content: m.content || '',
                    tool: m.tool || null,
                    receipt: m.receipt || null,
                    applied: !!m.applied,
                    error: !!m.error,
                    notice: !!m.notice,
                    retryInfo: m.retryInfo || null,
                    dnosGrounded: !!m.dnosGrounded,
                    dnosSources: m.dnosSources || null,
                    dnosValidation: m.dnosValidation || null,
                    dnosError: m.dnosError || null,
                    dnosConfig: m.dnosConfig || '',
                    dnosIntent: m.dnosIntent || null,
                    loading: false,
                });
            });
            // Prime the Retry button target.
            for (var i = _messages.length - 1; i >= 0; i--) {
                if (_messages[i].role === 'user') {
                    _lastUserMessage = _messages[i].content || '';
                    break;
                }
            }
            return true;
        }
        return false;
    }

    // Debounced cache save. Rendering fires many times per turn (typing
    // indicators, tool receipts, etc.) so a raw write per render would
    // be wasteful. 300ms batches every legitimate rapid sequence.
    var _convCacheSaveTimer = null;
    function _scheduleConvCacheSave() {
        if (_convCacheSaveTimer) return;
        _convCacheSaveTimer = setTimeout(function () {
            _convCacheSaveTimer = null;
            _saveConvCache();
        }, 300);
    }

    function _appendMessage(role, content, opts) {
        opts = opts || {};
        var entry = {
            _id: _nextId(),
            role: role,
            content: content,
        };
        if (opts.tool) entry.tool = opts.tool;
        if (opts.error) entry.error = opts.error;
        if (opts.notice) entry.notice = opts.notice;
        if (opts.loading) entry.loading = opts.loading;
        if (opts.retryInfo) entry.retryInfo = opts.retryInfo;
        if (opts.pending) entry.pending = opts.pending;
        // 2026-04-24r -- blueprint-consulted chip metadata. Server
        // emits `blueprints_consulted: [{name, args, ok, summary}, ...]`
        // after a chat turn that hit one of the read-only lookup tools.
        // We stash it on the assistant bubble so the renderer can show
        // a small "Consulted N blueprint(s)" pill without needing a
        // separate round-trip to enumerate them.
        if (opts.consulted) entry.consulted = opts.consulted;
        _messages.push(entry);
        _renderChatLog();
        _scheduleConvCacheSave();
        return entry;
    }

    function _replaceMessage(id, updater) {
        for (var i = 0; i < _messages.length; i += 1) {
            if (_messages[i]._id === id) {
                _messages[i] = Object.assign({}, _messages[i], updater || {});
                _renderChatLog();
                _scheduleConvCacheSave();
                return _messages[i];
            }
        }
        return null;
    }

    function _removeMessage(id) {
        _messages = _messages.filter(function (m) { return m._id !== id; });
        _renderChatLog();
        _scheduleConvCacheSave();
    }

    function _appendSystem(text, opts) {
        // 2026-04-24s -- accept an optional opts bag so async ops can
        // post a "Creating domain X..." pending bubble that swaps to
        // "Created" / "Could not create" via _replaceMessage. The
        // pending flag toggles a CSS spinner on the notice; error
        // recolours it red.
        opts = opts || {};
        var entry = { notice: true };
        if (opts.pending) entry.pending = true;
        if (opts.error) entry.error = true;
        return _appendMessage('system', text, entry);
    }

    // ---- 2026-04-24s reserved-domain client check --------------------
    //
    // Mirrors the BUILTIN_SECTIONS list in topology/serve.py. We keep
    // both so that:
    //   1. The placement card can show an inline warning BEFORE the
    //      user clicks "Place on canvas".
    //   2. The apply_canvas_edits create_domain path can short-circuit
    //      without a wasted POST + 400 round-trip.
    // The server enforcement is still authoritative; this is a UX
    // optimisation, not a security boundary.
    function _isReservedDomainName(name) {
        if (!name || typeof name !== 'string') return false;
        var n = name.trim().toLowerCase();
        if (!n) return false;
        if (n === 'ai' || n === 'bugs' || n === 'dnaas') return true;
        if (n.indexOf('__') === 0) return true;  // hidden ids like __ai
        return false;
    }

    // 2026-04-24s -- per-message Copy button.
    //
    // Every bubble with user-visible text (user prompts, assistant
    // replies, system notices, error text, error cards) carries a
    // small pill-shaped Copy button anchored top-right. The click
    // handler (wired once per render pass below) reads the plain-text
    // representation of the bubble and pushes it to the clipboard via
    // `navigator.clipboard.writeText`. We deliberately skip tool
    // cards (they already have an action row + diffs; copying a
    // receipt is rarely useful) and loading bubbles (no content yet).
    //
    // The HTML is generated once here so the markup stays consistent
    // across every bubble type. Caller passes the message id; click
    // handler uses it to look up the message in `_messages` and falls
    // back to the bubble's own `innerText` for rich cards.
    function _copyButtonHtml(msgId) {
        return '<button type="button" class="ai-msg__copy" '
            +   'data-role="msg-copy" data-msg-id="' + _escapeHtml(msgId) + '" '
            +   'title="Copy message text" aria-label="Copy message">'
            +   '<span class="ai-msg__copy-ico" aria-hidden="true">&#x29C9;</span>'
            +   '<span>Copy</span>'
            + '</button>';
    }

    // Resolve the plain-text payload for a given message. For simple
    // text bubbles we lift `m.content` directly (it is the exact
    // string the user sent or the assistant wrote). For rich bubbles
    // (error-card assembled HTML) we fall back to the bubble's
    // `innerText`, minus the Copy button and speaker meta label, so
    // what the user sees is what they get on the clipboard.
    function _messageCopyText(msgId, btn) {
        var msg = _messages.find(function (x) { return x._id === msgId; });
        if (msg && typeof msg.content === 'string' && msg.content.length) {
            return msg.content;
        }
        if (!btn) return '';
        var bubble = btn.closest('.ai-msg');
        if (!bubble) return '';
        var clone = bubble.cloneNode(true);
        clone.querySelectorAll('.ai-msg__copy, .ai-msg__meta').forEach(function (el) {
            el.parentNode && el.parentNode.removeChild(el);
        });
        // innerText preserves line breaks from block elements; trim to
        // avoid leading/trailing whitespace from padding divs.
        return (clone.innerText || clone.textContent || '').trim();
    }

    // Modern async Clipboard API with a legacy execCommand fallback
    // for the rare case that the drawer is focused inside an iframe
    // / insecure context where `navigator.clipboard` is unavailable.
    function _copyTextToClipboard(text) {
        if (navigator && navigator.clipboard && window.isSecureContext) {
            return navigator.clipboard.writeText(text).then(function () { return true; });
        }
        return new Promise(function (resolve) {
            try {
                var ta = document.createElement('textarea');
                ta.value = text;
                ta.setAttribute('readonly', '');
                ta.style.position = 'absolute';
                ta.style.left = '-9999px';
                document.body.appendChild(ta);
                ta.select();
                var ok = false;
                try { ok = document.execCommand('copy'); } catch (_) { ok = false; }
                document.body.removeChild(ta);
                resolve(ok);
            } catch (_) {
                resolve(false);
            }
        });
    }

    // Swap label to "Copied!" (or "Copy failed") for ~1.4 s so the
    // user gets a visual confirmation without a disruptive toast on
    // every click. CSS handles the colour flash via .is-copied.
    function _flashCopyButton(btn, ok) {
        if (!btn) return;
        var labelSpan = btn.querySelector('span:not(.ai-msg__copy-ico)');
        var original = labelSpan ? labelSpan.textContent : null;
        btn.classList.add('is-copied');
        if (labelSpan) labelSpan.textContent = ok ? 'Copied!' : 'Copy failed';
        window.setTimeout(function () {
            btn.classList.remove('is-copied');
            if (labelSpan && original !== null) labelSpan.textContent = original;
        }, 1400);
    }

    function _renderChatLog() {
        if (!_drawerEl) return;
        var log = _drawerEl.querySelector('[data-role="log"]');
        if (!log) return;
        var html = _messages.map(function (m) {
            if (m.tool) return _renderToolCard(m);
            if (m.errorCardHtml) {
                // Rich error card (billing, rate-limit, key rejected...).
                // HTML was assembled by _renderChatErrorCard which escapes
                // every dynamic field, so it's safe to splice raw here.
                return '<div class="ai-msg error-card" data-id="' + m._id + '">'
                    + _copyButtonHtml(m._id)
                    + m.errorCardHtml + '</div>';
            }
            if (m.error) {
                return '<div class="ai-msg error" data-id="' + m._id + '">'
                    + _copyButtonHtml(m._id)
                    + _escapeHtml(m.content)
                    + '</div>';
            }
            if (m.loading) {
                // The bubble gets re-rendered whenever _messages changes,
                // but not on a timer -- so we render the elapsed-time
                // counter, the hint, and the Stop button here, and a
                // 1-second interval below just patches the counter text
                // in place without a full re-render.
                var elapsed = m._elapsed || 0;
                var hintHtml = '';
                // Only show provider-specific slow-path hints when the
                // hint actually applies. Showing "switch to Groq" while
                // the user IS on Groq was a bug that made the UX feel
                // broken. For hosted providers we show a neutral
                // reassurance after a longer delay (sub-second on Groq
                // means anything past ~6s is already suspicious).
                var _provSlow = (_aiConfig && _aiConfig.provider || '').toLowerCase();
                if (_provSlow === 'ollama' && elapsed >= 12) {
                    hintHtml = '<div class="ai-loading__hint">'
                        + 'Local CPU models can take 1-3 min for the first answer. '
                        + 'For faster hosted responses, use Gemini Flash in settings.'
                        + '</div>';
                } else if (_provSlow !== 'ollama' && elapsed >= 8) {
                    hintHtml = '<div class="ai-loading__hint">'
                        + 'Still waiting on the provider. Tool-heavy topology '
                        + 'turns can take longer; the server will retry or fall '
                        + 'back automatically when the model rate-limits.'
                        + '</div>';
                }
                return '<div class="ai-msg loading" data-id="' + m._id + '">'
                    + '<div class="ai-loading__row">'
                    +   '<span class="ai-loading__dot"></span>'
                    +   '<span class="ai-loading__label">' + _escapeHtml(m.content || 'Thinking...') + '</span>'
                    +   '<span class="ai-loading__timer" data-role="loading-timer">' + elapsed + 's</span>'
                    +   '<button type="button" class="ai-btn tiny ghost" data-role="loading-stop" data-msg-id="' + m._id + '">Stop</button>'
                    + '</div>'
                    + hintHtml
                    + '</div>';
            }
            if (m.notice || m.role === 'system') {
                // 2026-04-24s -- pending state shows a spinner so the
                // user sees an in-flight async op (e.g. "Creating
                // domain X..."); error state recolours red so the user
                // doesn't have to read carefully to spot a failure.
                var noticeMods = '';
                var noticePrefix = '';
                if (m.pending) {
                    noticeMods += ' notice--pending';
                    noticePrefix = '<span class="ai-notice__spinner" aria-hidden="true"></span>';
                }
                if (m.error) noticeMods += ' notice--error';
                return '<div class="ai-msg notice' + noticeMods + '" data-id="' + m._id + '">'
                    + _copyButtonHtml(m._id)
                    + noticePrefix + _escapeHtml(m.content)
                    + '</div>';
            }
            var meta = m.role === 'user' ? 'You' : 'Assistant';
            // Auto-retry chip: server transparently retried after a
            // transient upstream error (429 rate-limit, 503 overloaded,
            // or Cloudflare bot challenge). Tiny pill so the user
            // knows why this turn took a few extra seconds, without
            // surfacing a scary red card for a call that ultimately
            // SUCCEEDED. 2026-04-24h: the backend retry wrapper was
            // broadened from 429-only to (429 / 503 overloaded /
            // Cloudflare 1020), so we now also surface `attempts` and
            // `kind` when the backend passes them (backwards-compatible
            // with the old 2-field shape).
            var retryChip = '';
            if (m.retryInfo && typeof m.retryInfo.wait_s === 'number') {
                var retryProv = (m.retryInfo.provider || '').toString();
                var waitTxt = m.retryInfo.wait_s.toFixed(m.retryInfo.wait_s < 10 ? 1 : 0);
                // Human-readable label per retry cause. Fall back to
                // "rate limit" for old server builds that don't emit
                // `kind` (the retry wrapper used to be 429-only).
                var retryKind = (m.retryInfo.kind || '').toString();
                var retryReason;
                var retryTooltip;
                if (retryKind === 'upstream_overloaded') {
                    retryReason = 'model overload';
                    retryTooltip = 'The upstream model was temporarily overloaded. The assistant waited and retried automatically.';
                } else if (retryKind === 'cf_bot_blocked') {
                    retryReason = 'CDN challenge';
                    retryTooltip = 'The provider\'s CDN issued a bot-challenge. The assistant retried automatically with a fresh request.';
                } else {
                    retryReason = 'rate limit';
                    retryTooltip = 'The provider hit a momentary rate limit. The assistant waited and retried automatically.';
                }
                var attemptsTxt = '';
                if (typeof m.retryInfo.attempts === 'number' && m.retryInfo.attempts > 2) {
                    attemptsTxt = ', ' + m.retryInfo.attempts + ' attempts';
                }
                retryChip = '<div class="ai-msg__retry-chip" title="' + _escapeHtml(retryTooltip) + '">'
                    + 'auto-recovered from ' + _escapeHtml(retryProv || 'provider') + ' '
                    + _escapeHtml(retryReason) + ' (waited ' + waitTxt + 's' + attemptsTxt + ')'
                    + '</div>';
            }
            // 2026-04-24t -- model-fallback chip. The server swapped to
            // a sibling model mid-turn because the user's chosen model
            // was quota-exhausted or overloaded. Stays visible + blue
            // (not red) so the user knows the answer came from a
            // different brain without making them think something
            // failed. Clicking "Switch" writes the fallback model into
            // their saved config so future turns start there.
            var fallbackChip = '';
            if (m.retryInfo && m.retryInfo.fallback && m.retryInfo.fallback.to_model) {
                var fb = m.retryInfo.fallback;
                var fromModel = fb.from_model || '?';
                var toModel = fb.to_model;
                var reasonLabel = 'quota exhausted';
                var fbKind = (fb.reason_kind || '').toString();
                if (fbKind === 'upstream_overloaded') reasonLabel = 'temporarily overloaded';
                else if (fbKind === 'rate_limited')     reasonLabel = 'rate-limited';
                else if (fbKind === 'insufficient_quota') reasonLabel = 'daily quota exhausted';
                var tooltip = 'Your chosen model (' + fromModel + ') was ' + reasonLabel
                    + '. The server auto-switched to ' + toModel + ' for this turn only. '
                    + 'Click "Switch" to make the fallback your default so the next turns start on it.';
                fallbackChip = '<div class="ai-msg__fallback-chip" title="' + _escapeHtml(tooltip) + '" role="group" aria-label="Model fallback">'
                    + '<span class="ai-msg__fallback-label">'
                    + 'answered by <b>' + _escapeHtml(toModel) + '</b> '
                    + '<span class="ai-msg__fallback-from">(your ' + _escapeHtml(fromModel) + ' was ' + _escapeHtml(reasonLabel) + ')</span>'
                    + '</span>'
                    + '<button type="button" class="ai-msg__fallback-btn" data-action="ai-switch-default-model" data-target-model="' + _escapeHtml(toModel) + '" title="Save ' + _escapeHtml(toModel) + ' as your default model">Switch</button>'
                    + '</div>';
            }
            // 2026-04-26 -- DNOS-grounded card. When the backend
            // intent gate fires we render the validated CLI block in
            // a green/teal "Verified from DNOS docs" card with the
            // source chips below. We deliberately suppress the raw
            // assistant text in that case (the body is already in
            // the card, no need to double-render).
            var dnosCardHtml = '';
            var suppressBody = false;
            if (m.dnosGrounded || m.dnosError || (Array.isArray(m.dnosSources) && m.dnosSources.length)) {
                dnosCardHtml = _renderDnosGroundedCard(m);
                suppressBody = !!dnosCardHtml;
            }
            // 2026-04-24r -- blueprint-consulted chip. One line,
            // enumerates each consulted blueprint inline so the user
            // sees *which* protocol/topology recipes the model looked
            // up before replying. Hovering the pill shows the full
            // arg payload for debugging flaky tool selection.
            var consultedChip = '';
            if (Array.isArray(m.consulted) && m.consulted.length) {
                var names = m.consulted.slice(0, 6).map(function (c) {
                    var argStr = '';
                    try { argStr = JSON.stringify(c.args || {}); } catch (_) {}
                    var label = (c.summary && String(c.summary).trim())
                        || (c.name && String(c.name).trim())
                        || 'blueprint';
                    return '<span class="ai-consulted-chip__item" title="'
                        + _escapeHtml(c.name + ' ' + argStr)
                        + '">' + _escapeHtml(label) + '</span>';
                }).join('');
                var extra = m.consulted.length > 6
                    ? ' <span class="ai-consulted-chip__item">+' + (m.consulted.length - 6) + ' more</span>'
                    : '';
                consultedChip = '<div class="ai-consulted-chip" '
                    + 'title="These recipes were consulted before the reply.">'
                    + '<span class="ai-consulted-chip__label">Consulted:</span>'
                    + names + extra
                    + '</div>';
            }
            var bodyHtml = suppressBody ? '' : _escapeHtml(m.content);
            return '<div class="ai-msg ' + m.role + '" data-id="' + m._id + '">'
                + _copyButtonHtml(m._id)
                + '<span class="ai-msg__meta">' + meta + '</span>'
                + bodyHtml
                + dnosCardHtml
                + retryChip
                + fallbackChip
                + consultedChip
                + '</div>';
        }).join('');
        log.innerHTML = html;
        // 2026-04-24s -- wire the per-message Copy buttons. Built here
        // (vs a shared global delegate) so the handler stays local to
        // the renderer and refs the current `_messages` snapshot.
        log.querySelectorAll('[data-role="msg-copy"]').forEach(function (btn) {
            btn.addEventListener('click', function (ev) {
                ev.stopPropagation();
                var mid = btn.dataset.msgId || '';
                var text = _messageCopyText(mid, btn);
                if (!text) return;
                _copyTextToClipboard(text).then(function (ok) {
                    _flashCopyButton(btn, ok);
                }, function () {
                    _flashCopyButton(btn, false);
                });
            });
        });
        // 2026-04-26 -- "Copy DNOS" button on grounded reply cards.
        // We copy ONLY the validated CLI block (the `dnos_config`
        // field the backend stamped on the message), not the whole
        // bubble. That matters because users paste this straight into
        // a DNOS shell or commit it via `/api/operations/validate`.
        log.querySelectorAll('[data-role="dnos-copy"]').forEach(function (btn) {
            btn.addEventListener('click', function (ev) {
                ev.stopPropagation();
                var mid = btn.dataset.msgId || '';
                var msg = _messages.find(function (x) { return x._id === mid; });
                var text = '';
                if (msg && typeof msg.dnosConfig === 'string' && msg.dnosConfig.trim()) {
                    text = msg.dnosConfig.trim();
                } else {
                    var pre = btn.closest('.ai-dnos-card');
                    var preEl = pre && pre.querySelector('[data-role="dnos-config"]');
                    text = (preEl && (preEl.innerText || preEl.textContent) || '').trim();
                }
                if (!text) return;
                _copyTextToClipboard(text).then(function (ok) {
                    btn.classList.add('is-copied');
                    var prev = btn.textContent;
                    btn.textContent = ok ? 'Copied!' : 'Copy failed';
                    setTimeout(function () {
                        btn.classList.remove('is-copied');
                        btn.textContent = prev;
                    }, 1400);
                }, function () { /* noop */ });
            });
        });
        // Wire tool-card action handlers (fresh DOM every render -- easy
        // and small; chat log is usually <50 messages).
        log.querySelectorAll('[data-role="tool-action"]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var mid = btn.dataset.msgId;
                var action = btn.dataset.toolAction;
                var msg = _messages.find(function (m) { return m._id === mid; });
                if (!msg || !msg.tool) return;
                if (action === 'save-load') _loadSavedTopology(msg.tool);
                else if (action === 'place') _placePendingTopology(btn, msg);
                else if (action === 'dismiss') _removeMessage(mid);
                else if (action === 'undo-edits') {
                    // Delegate to the editor's undo stack -- the
                    // apply_canvas_edits executor calls editor.saveState()
                    // once before the batch so a single Ctrl+Z reverts
                    // the whole batch. We call it as many times as the
                    // executor pushed states (currently always 1).
                    var ed = _editor();
                    if (ed && typeof ed.undo === 'function') {
                        try { ed.undo(); } catch (e) { console.warn('[AI] undo failed:', e); }
                        _toast('Reverted last AI canvas edit', 'info');
                    }
                    _removeMessage(mid);
                }
                else if (action === 'propose-apply') {
                    // 2026-04-24r -- user clicked Apply on a proposal
                    // card. Re-use the apply_canvas_edits executor
                    // (same edit wire-format) and swap the proposal
                    // card for an applied receipt card so the log has
                    // exactly one row per action.
                    try {
                        var receipt = _applyCanvasEdits(msg.tool);
                        var receiptTool = {
                            name: 'apply_canvas_edits',
                            status: 'apply',
                            summary: msg.tool.summary || '',
                            edits: msg.tool.edits || [],
                        };
                        _replaceMessage(mid, {
                            tool: receiptTool,
                            receipt: receipt,
                            applied: true,
                        });
                        _toast('Applied ' + ((msg.tool.edits || []).length)
                            + ' proposed edit' + ((msg.tool.edits || []).length === 1 ? '' : 's'), 'info');
                    } catch (err) {
                        _appendMessage('assistant',
                            'Apply failed: ' + (err && err.message ? err.message : err),
                            { error: true });
                    }
                }
                else if (action === 'propose-tweak') {
                    // "Tweak..." -- pre-fill the composer with a
                    // refinement prompt. The user can edit then press
                    // Enter / Send to refine. We leave the proposal
                    // card in place so they can still Apply / Cancel.
                    var tweakText = 'Refine the proposed edits: '
                        + (msg.tool.summary || '(no summary)')
                        + '. Please describe what I should change.';
                    var tweakInput = _drawerEl && _drawerEl.querySelector('[data-role="composer-input"]');
                    if (tweakInput) {
                        tweakInput.value = tweakText;
                        tweakInput.dispatchEvent(new Event('input'));
                        tweakInput.focus();
                    }
                }
                else if (action === 'question-pick') {
                    if (_sending || btn.dataset.busy === '1') return;
                    btn.dataset.busy = '1';
                    btn.disabled = true;
                    // Chip-picker: send the chip's value back as the
                    // next user message. Non-blocking; the existing
                    // send path handles all the plumbing.
                    var picked = btn.dataset.value || '';
                    if (picked) {
                        _removeMessage(mid);
                        if (typeof _sendUserMessage === 'function') {
                            _sendUserMessage(picked);
                        }
                    }
                }
                else if (action === 'question-free') {
                    // "Something else..." -- focus the composer so
                    // the user can type a free-text answer. We add
                    // the question text above the field as a ghost
                    // placeholder so they know what they're answering.
                    var qInput = _drawerEl && _drawerEl.querySelector('[data-role="composer-input"]');
                    if (qInput) {
                        var questionText = (msg.tool && msg.tool.question) || '';
                        if (questionText) {
                            qInput.placeholder = 'Re: ' + questionText.slice(0, 80);
                        }
                        qInput.focus();
                    }
                    _removeMessage(mid);
                }
            });
        });
        // Auto-flip the placement radio when the user interacts with the
        // paired control directly -- lets them just click the input they
        // want without first hunting for the radio.
        log.querySelectorAll('.ai-placement').forEach(function (card) {
            var existing = card.querySelector('[data-role="placement-existing"]');
            var newInput = card.querySelector('[data-role="placement-new-name"]');
            var topoInput = card.querySelector('[data-role="placement-topo-name"]');
            var radios = card.querySelectorAll('input[type="radio"]');
            var preview = card.querySelector('[data-role="placement-preview"]');
            var primaryBtn = card.querySelector('[data-tool-action="place"]');
            var resvWarn = null;
            function _checkRadio(val) {
                radios.forEach(function (r) { r.checked = (r.value === val); });
                _refreshPreview();
            }
            // 2026-04-24s -- live preview line so the user knows
            // exactly what happens when they click Place. Recomputes
            // when they pick a different domain, type a new name, or
            // flip the radio. Also surfaces a reserved-name warning
            // pre-click so server 400s for "AI"/"Bugs"/"DNAAS"
            // collisions stop being a surprise.
            function _refreshPreview() {
                if (!preview) return;
                var mode = 'existing';
                radios.forEach(function (r) { if (r.checked) mode = r.value; });
                var topoInput = card.querySelector('[data-role="placement-topo-name"]');
                var topoName = (topoInput && topoInput.value || '').trim() || 'topology';
                var nDevices = '';
                if (typeof primaryBtn !== 'undefined' && primaryBtn) {
                    var midAttr = primaryBtn.dataset && primaryBtn.dataset.msgId;
                    var mEntry = midAttr && _messages.find(function (mm) { return String(mm._id) === String(midAttr); });
                    if (mEntry && mEntry.tool && mEntry.tool.topology) {
                        var dn = _topologyCounts(mEntry.tool.topology).devices;
                        if (dn) nDevices = dn + (dn === 1 ? ' device' : ' devices');
                    }
                }
                var what = nDevices ? (nDevices + ' (' + _escapeHtml(topoName) + ')') : _escapeHtml(topoName);
                var resvWarnText = '';
                if (mode === 'new') {
                    var nm = (newInput && newInput.value || '').trim();
                    if (!nm) {
                        preview.textContent = 'Enter a name for the new domain to enable Place.';
                    } else if (_isReservedDomainName(nm)) {
                        preview.innerHTML = 'Will create domain "' + _escapeHtml(nm) + '" and place ' + what + '.';
                        resvWarnText = '"' + nm + '" is a reserved built-in domain name -- pick another name (e.g. "'
                            + nm + ' Lab") before placing.';
                    } else {
                        preview.innerHTML = 'Will create domain "' + _escapeHtml(nm) + '" and place ' + what + '.';
                    }
                } else {
                    var optName = '';
                    if (existing && existing.options && existing.selectedIndex >= 0) {
                        var opt = existing.options[existing.selectedIndex];
                        if (opt) optName = opt.textContent;
                    }
                    if (!optName) {
                        preview.textContent = 'Pick an existing domain to enable Place.';
                    } else {
                        preview.innerHTML = 'Will place ' + what + ' in existing domain "' + _escapeHtml(optName) + '".';
                    }
                }
                // Toggle reserved-name banner without re-rendering
                // the whole card (avoids losing focus / cursor).
                if (resvWarnText) {
                    if (!resvWarn) {
                        resvWarn = document.createElement('div');
                        resvWarn.className = 'ai-placement__note ai-placement__note--warn';
                        resvWarn.dataset.role = 'placement-live-warn';
                        preview.parentNode.insertBefore(resvWarn, preview);
                    }
                    resvWarn.innerHTML = '<b>Heads up:</b> ' + _escapeHtml(resvWarnText);
                } else if (resvWarn && resvWarn.parentNode) {
                    resvWarn.parentNode.removeChild(resvWarn);
                    resvWarn = null;
                }
                // Disable Place when the form isn't in a runnable
                // state so the user can't fire a doomed POST.
                if (primaryBtn && !primaryBtn.classList.contains('ai-btn--working')) {
                    var disable = false;
                    if (mode === 'new') {
                        var nameTrim = (newInput && newInput.value || '').trim();
                        if (!nameTrim || _isReservedDomainName(nameTrim)) disable = true;
                    } else {
                        if (!existing || !existing.value) disable = true;
                    }
                    primaryBtn.disabled = disable;
                    primaryBtn.title = disable
                        ? (mode === 'new' ? 'Enter a non-reserved domain name first' : 'Pick a domain first')
                        : '';
                }
            }
            if (existing) {
                existing.addEventListener('focus', function () { _checkRadio('existing'); });
                existing.addEventListener('change', function () {
                    _checkRadio('existing');
                    _refreshUniquePlacementName(card);
                });
            }
            if (newInput) {
                newInput.addEventListener('focus', function () { _checkRadio('new'); });
                newInput.addEventListener('input', function () { _checkRadio('new'); });
            }
            if (topoInput) {
                topoInput.addEventListener('input', function () {
                    if (topoInput.dataset.autoUnique !== '1') {
                        topoInput.dataset.userEdited = '1';
                    }
                    _refreshPreview();
                });
            }
            radios.forEach(function (r) {
                r.addEventListener('change', _refreshPreview);
            });
            // Enter inside either placement input triggers the primary
            // action so keyboard-driven users don't need to mouse back to
            // the button.
            card.querySelectorAll('.ai-placement__input, .ai-placement__select').forEach(function (el) {
                el.addEventListener('keydown', function (ev) {
                    if (ev.key === 'Enter' && !ev.shiftKey) {
                        ev.preventDefault();
                        var primary = card.querySelector('[data-tool-action="place"]');
                        if (primary && !primary.disabled) primary.click();
                    }
                });
            });
            // Initial preview render so the message reflects defaults
            // (also re-runs the disable-button check on mount).
            _refreshPreview();
            _refreshUniquePlacementName(card);
        });
        // Stop button inside the "Thinking..." bubble -- aborts the
        // in-flight fetch. Noop if the request already resolved.
        log.querySelectorAll('[data-role="loading-stop"]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                if (_currentAbort) {
                    try { _currentAbort.abort(); } catch (_) {}
                }
            });
        });
        log.scrollTop = log.scrollHeight;
        // Keep the Copy / Regenerate / Export buttons in sync with
        // whatever the log currently contains. Cheap -- the toolbar
        // is 4 buttons and the state check reads a flag + a counter.
        _updateChatToolbarState();
    }

    // --------------------------------------------------------------
    //   Rich error cards (billing, rate-limit, key rejected, ...)
    // --------------------------------------------------------------
    //
    // The backend classifies upstream failures into a stable ``kind`` so
    // the chat UI can surface a targeted card instead of dumping the raw
    // provider JSON into a generic red bubble. Each card shows:
    //
    //   * a short title (what went wrong, in one line)
    //   * a human-readable hint (what to do about it)
    //   * the provider's own message (if useful and not redundant)
    //   * primary / secondary action buttons (links open in a new tab)
    //   * a <details> disclosure with the raw body for debugging
    //
    // Known kinds (kept in sync with ai/service.py::_classify_upstream_error):
    //   - insufficient_quota, rate_limited, api_key_rejected
    //   - model_not_found, context_overflow, timeout, unreachable
    //   - cf_bot_blocked (CDN bot-management challenge; transient)
    //   - upstream_error (generic fallback)
    //
    // Actions are dispatched via delegated click handlers in
    // _wireDrawerEvents -- see data-action="ai-error-*".
    function _providerShortLabel(providerId) {
        var p = PROVIDER_PRESETS[(providerId || '').toLowerCase()];
        return (p && p.short_label) || providerId || 'provider';
    }

    function _renderChatErrorCard(kind, message, details, provider) {
        var title = 'AI call failed';
        var hint = '';
        var primary = null;
        var secondary = null;
        // Tertiary is a ghost-styled, link-like third action used for
        // "Or try <other provider>" nudges. Set it to null for cards
        // that don't need a provider-switch suggestion; the renderer
        // will just omit it.
        var tertiary = null;

        var providerLabel = _providerShortLabel(provider);
        var providerLower = (provider || '').toLowerCase();

        if (kind === 'insufficient_quota') {
            title = providerLabel + ' quota exhausted';
            hint = 'The provider account has no credits left. Top it up, or '
                 + 'switch to a different provider in settings.';
            if (providerLower === 'openai') {
                primary = { label: 'Open OpenAI billing', href: 'https://platform.openai.com/account/billing/overview' };
            } else if (providerLower === 'anthropic') {
                primary = { label: 'Open Anthropic billing', href: 'https://console.anthropic.com/settings/billing' };
            } else if (providerLower === 'gemini') {
                // 2026-04-24k -- Gemini free tier caps at 20 req/day/model
                // for gemini-2.5-flash. Gemini-2.5-flash-lite has its
                // OWN separate daily bucket, so a one-click "try the
                // other model" button is the fastest unbrick path:
                // instead of leaving the drawer to upgrade billing or
                // retype the key, the user stays in the chat, we PUT
                // the new model via /api/users/me/ai-config (blank
                // api_key reuses the stored one), then auto-resend the
                // last user message. Paid upgrade stays available as
                // the secondary link.
                title = 'Gemini daily quota hit';
                var currentModel = (_aiConfig && _aiConfig.model || 'gemini-2.5-flash').toLowerCase();
                var altModel = (currentModel.indexOf('lite') !== -1)
                    ? 'gemini-2.5-flash'
                    : 'gemini-2.5-flash-lite';
                hint = 'Google\'s free tier caps the daily quota per model. '
                     + 'Each Gemini model has its OWN daily bucket, so '
                     + 'switching to "' + altModel + '" usually gets you '
                     + 'going again immediately. You can also wait for '
                     + 'the midnight-UTC reset, or upgrade your AI Studio '
                     + 'plan.';
                primary = {
                    label: 'Switch to ' + altModel,
                    action: 'ai-error-switch-gemini-model',
                    dataset: { targetModel: altModel },
                };
                secondary = { label: 'Upgrade AI Studio plan', href: 'https://aistudio.google.com/app/plan' };
                tertiary = { label: 'Open settings', action: 'ai-error-settings' };
            } else {
                secondary = { label: 'Switch provider', action: 'ai-error-settings' };
            }
        } else if (kind === 'rate_limited') {
            title = 'Rate limit hit on ' + providerLabel;
            // Groq and OpenAI both put a "Please try again in N.Ns"
            // hint in the body. Extract it so the user sees an actual
            // seconds-to-wait instead of the generic "a few seconds".
            // Matches both "try again in 1.615s" and "try again in 45
            // seconds" styles.
            var retryHint = '';
            try {
                var src = (details || message || '');
                var m = src.match(/try again in\s+([0-9]+(?:\.[0-9]+)?)\s*(s|sec|seconds?)?/i);
                if (m) {
                    var secs = parseFloat(m[1]);
                    if (isFinite(secs) && secs > 0) {
                        retryHint = ' Try again in about ' + Math.ceil(secs) + 's.';
                    }
                }
            } catch (_) {}
            hint = 'The provider is throttling requests (per-minute token '
                 + 'or request budget temporarily exhausted).' + retryHint
                 + ' If you hit this often, switch to a faster model '
                 + '(e.g. GPT-OSS 120B or 20B) so each turn uses fewer '
                 + 'tokens against the same per-minute budget.';
            primary = { label: 'Retry', action: 'ai-error-retry' };
            secondary = { label: 'Open settings', action: 'ai-error-settings' };
            // Groq's free tier blows its 12k TPM budget on a single
            // create_topology turn easily. Gemini's free tier has a
            // completely separate quota (different company, different
            // rate limiter) so jumping over is the cleanest way out
            // of a 429 storm -- nudge the user towards it.
            if (providerLower === 'groq') {
                tertiary = {
                    label: 'Or try Gemini (free, separate quota)',
                    action: 'ai-error-settings',
                };
            }
        } else if (kind === 'api_key_rejected') {
            title = providerLabel + ' rejected the API key';
            hint = 'The key was rejected by the provider. Most common cause: '
                 + 'the key belongs to a different provider than the one '
                 + 'selected. Check your settings.';
            primary = { label: 'Open settings', action: 'ai-error-settings' };
        } else if (kind === 'model_not_found') {
            title = 'Model not available on this key';
            hint = 'The selected model isn\'t reachable with this API key. '
                 + 'Pick a different model or switch provider.';
            primary = { label: 'Open settings', action: 'ai-error-settings' };
        } else if (kind === 'context_overflow') {
            title = 'Conversation too long for this model';
            hint = 'The prompt exceeded the model\'s context window. Clear the '
                 + 'conversation, or switch to a larger-context model.';
            primary = { label: 'Clear conversation', action: 'ai-error-clear' };
            secondary = { label: 'Open settings', action: 'ai-error-settings' };
        } else if (kind === 'timeout') {
            title = 'Provider timed out';
            hint = 'The provider took too long to respond. Try again.';
            primary = { label: 'Retry', action: 'ai-error-retry' };
        } else if (kind === 'unreachable') {
            title = 'Provider unreachable';
            hint = 'Could not reach the provider endpoint. Check network or '
                 + 'the Base URL override in settings.';
            primary = { label: 'Retry', action: 'ai-error-retry' };
            secondary = { label: 'Open settings', action: 'ai-error-settings' };
        } else if (kind === 'cf_bot_blocked') {
            // Cloudflare managed-challenge / bot-ban at the CDN layer.
            // The user's key is fine -- don't push them back to settings,
            // just offer a retry. If they retry and hit it again we'll
            // show the same card; the fix is backend-side (proper User-
            // Agent, which is now in place).
            title = 'Blocked by upstream CDN';
            hint = providerLabel + '\'s CDN (Cloudflare) flagged this '
                 + 'request as automated. This is transient and not an '
                 + 'issue with your API key. Retry in a few seconds.';
            primary = { label: 'Retry', action: 'ai-error-retry' };
            secondary = { label: 'Switch provider', action: 'ai-error-settings' };
        } else if (kind === 'upstream_overloaded') {
            // Provider-side overload spike (Gemini's 503 UNAVAILABLE,
            // Anthropic's 529 overloaded_error, OpenAI's "server
            // overloaded"). Not a config issue -- the model is up,
            // just throttling THIS call. Retry is the right action;
            // switching model/provider is the escape hatch if the
            // spike drags on.
            title = providerLabel + ' is temporarily overloaded';
            hint = 'The model is up but throttling requests right now. '
                 + 'Wait a few seconds and retry, or switch to a '
                 + 'different model if the spike persists.';
            primary = { label: 'Retry', action: 'ai-error-retry' };
            secondary = { label: 'Switch model', action: 'ai-error-settings' };
        } else {
            title = 'AI call failed';
            hint = message || 'The request failed.';
            primary = { label: 'Retry', action: 'ai-error-retry' };
        }

        var parts = [];
        parts.push('<div class="ai-err-card__title">' + _escapeHtml(title) + '</div>');
        if (hint) parts.push('<div class="ai-err-card__hint">' + _escapeHtml(hint) + '</div>');
        // Show the provider's own one-line message if it adds information
        // (it usually does: insufficient_quota includes the billing URL,
        // model_not_found includes the offending model id, etc.).
        if (message && message !== hint) {
            parts.push('<div class="ai-err-card__msg">'
                + '<span class="ai-err-card__msg-label">Provider says:</span> '
                + _escapeHtml(message) + '</div>');
        }
        if (primary || secondary || tertiary) {
            var actions = '<div class="ai-err-card__actions">';
            var _renderAction = function (a, cls) {
                if (!a) return '';
                if (a.href) {
                    return '<a class="ai-btn ' + cls + ' tiny" href="' + _escapeHtml(a.href)
                        + '" target="_blank" rel="noopener noreferrer">'
                        + _escapeHtml(a.label) + ' &#x2197;</a>';
                }
                // 2026-04-24l -- serialise optional `dataset` so action
                // handlers can read side-channel args (e.g. the target
                // model name for ai-error-switch-gemini-model). Keys are
                // written as `data-<kebab-case>`; the wildcard sanitiser
                // mirrors HTML's built-in kebab rules so the reader can
                // pick them up from `btn.dataset.<camelCase>`.
                var dataAttrs = '';
                if (a.dataset && typeof a.dataset === 'object') {
                    Object.keys(a.dataset).forEach(function (k) {
                        var kebab = k.replace(/[A-Z]/g, function (c) {
                            return '-' + c.toLowerCase();
                        });
                        dataAttrs += ' data-' + _escapeHtml(kebab)
                            + '="' + _escapeHtml(String(a.dataset[k])) + '"';
                    });
                }
                return '<button type="button" class="ai-btn ' + cls + ' tiny"'
                    + ' data-action="' + _escapeHtml(a.action) + '"' + dataAttrs + '>'
                    + _escapeHtml(a.label) + '</button>';
            };
            actions += _renderAction(primary, 'primary');
            actions += _renderAction(secondary, 'secondary');
            // Tertiary uses the `ghost` tiny style so it reads as a
            // subtle link-like nudge instead of competing with the
            // primary Retry button visually.
            actions += _renderAction(tertiary, 'ghost');
            actions += '</div>';
            parts.push(actions);
        }
        // Collapsible technical details -- shown only when we got a raw
        // body back. Keep it lean: OpenAI's body is ~200 bytes of JSON,
        // Anthropic's is similar. We cap at 2 KB at the backend.
        if (details && String(details).trim()) {
            parts.push('<details class="ai-err-card__details">'
                + '<summary>Technical details</summary>'
                + '<pre>' + _escapeHtml(String(details)) + '</pre>'
                + '</details>');
        }
        return parts.join('');
    }

    // 2026-04-24r -- condense a proposed edit into one human-readable
    // line. Mirrors the few op names the server-side CANVAS_EDITS
    // schema accepts (see ai/context.py). We cap the preview list at
    // 12 lines to keep the card from ballooning in the log.
    function _renderProposedEditRow(edit, idx) {
        if (!edit || typeof edit !== 'object') return '';
        var op = String(edit.op || '').toLowerCase();
        var txt = '';
        if (op === 'add_device') {
            txt = 'Add device <b>' + _escapeHtml(String(edit.label || 'device-' + (idx + 1)))
                + '</b>' + (edit.role ? ' (' + _escapeHtml(edit.role) + ')' : '');
        } else if (op === 'add_link') {
            txt = 'Link <b>' + _escapeHtml(String(edit.from || edit.device1 || '?'))
                + '</b> &harr; <b>' + _escapeHtml(String(edit.to || edit.device2 || '?')) + '</b>';
        } else if (op === 'add_text') {
            txt = 'Add note <i>' + _escapeHtml(String(edit.text || '')).slice(0, 60) + '</i>';
        } else if (op === 'remove') {
            txt = 'Remove <b>' + _escapeHtml(String(edit.id || edit.label || 'object')) + '</b>';
        } else if (op === 'move') {
            txt = 'Move <b>' + _escapeHtml(String(edit.id || edit.label || 'object'))
                + '</b> to (' + Math.round(edit.x) + ', ' + Math.round(edit.y) + ')';
        } else if (op === 'relabel' || op === 'rename') {
            txt = 'Relabel <b>' + _escapeHtml(String(edit.id || edit.label || '?'))
                + '</b> &rarr; <b>' + _escapeHtml(String(edit.new_label || edit.to || '?')) + '</b>';
        } else if (op === 'recolor') {
            txt = 'Recolor <b>' + _escapeHtml(String(edit.id || edit.label || '?'))
                + '</b> &rarr; ' + _escapeHtml(String(edit.color || '?'));
        } else {
            txt = _escapeHtml(op || 'edit') + ' ' + _escapeHtml(JSON.stringify(edit).slice(0, 120));
        }
        return '<li>' + txt + '</li>';
    }

    // ---- DNOS-grounded reply renderer ----------------------------------
    //
    // The backend intent gate (`ai/dnos_config_grounding.py`) routes
    // turns asking for DNOS configuration through a strict path that:
    //   1. Searches Network Mapper `search_cli_docs` + bundled RST
    //      docs for evidence,
    //   2. Calls the LLM with a tool-less prompt locked to that
    //      evidence,
    //   3. Validates the produced CLI body via cli_validator.
    // The response carries `dnos_*` metadata that we render here as a
    // green/teal card with: header (Verified from DNOS docs), the
    // validated CLI block (mono pre with copy button), a source
    // chip row, an optional validation receipt, and an error banner
    // when grounding could not produce a valid block.
    function _renderDnosGroundedCard(m) {
        var sources = Array.isArray(m.dnosSources) ? m.dnosSources : [];
        var validation = m.dnosValidation || null;
        var err = m.dnosError || null;
        var intent = m.dnosIntent || null;
        // Body: prefer the explicit CLI text the backend set; fall
        // back to extracting from the bubble content (```dnos block).
        var configText = '';
        if (typeof m.dnosConfig === 'string' && m.dnosConfig.trim()) {
            configText = m.dnosConfig.trim();
        } else if (typeof m.content === 'string') {
            var fence = m.content.match(/```(?:dnos|cli|text)?\s*\n([\s\S]*?)```/i);
            if (fence) configText = fence[1].trim();
        }
        var html = '<div class="ai-dnos-card" role="group" aria-label="DNOS verified configuration">';
        var intentLabel = '';
        if (intent && intent.query) {
            intentLabel = '<span class="ai-dnos-card__intent" title="Backend search query for the RST + Network Mapper docs">'
                + 'query: ' + _escapeHtml(String(intent.query).slice(0, 80))
                + '</span>';
        }
        html += '<div class="ai-dnos-card__hdr">'
            + '<span>DNOS &mdash; verified from docs</span>'
            + intentLabel
            + '</div>';
        if (configText) {
            html += '<pre class="ai-dnos-card__pre" data-role="dnos-config">'
                + _escapeHtml(configText)
                + '</pre>';
            html += '<div style="display:flex;justify-content:flex-end;margin-top:6px;">'
                + '<button type="button" class="ai-dnos-card__copy" '
                + 'data-role="dnos-copy" data-msg-id="' + _escapeHtml(m._id) + '" '
                + 'title="Copy DNOS commands">Copy DNOS</button>'
                + '</div>';
        }
        if (err && (err.kind || err.message)) {
            html += '<div class="ai-dnos-error">'
                + _escapeHtml(err.message || ('DNOS grounding error: ' + (err.kind || 'unknown')))
                + '</div>';
        }
        if (sources.length) {
            var chips = sources.slice(0, 6).map(function (s) {
                var label = (s.doc_name || s.path || s.source || 'doc');
                var sourceTag = (s.source === 'mcp') ? ' (mcp)' : '';
                var tooltip = (s.path || '') + (s.snippet ? '\n\n' + String(s.snippet).slice(0, 400) : '');
                return '<span class="ai-dnos-sources__item" title="'
                    + _escapeHtml(tooltip) + '">'
                    + _escapeHtml(label) + sourceTag
                    + '</span>';
            }).join('');
            var more = sources.length > 6
                ? ' <span class="ai-dnos-sources__item">+' + (sources.length - 6) + ' more</span>'
                : '';
            html += '<div class="ai-dnos-sources" '
                + 'title="Hover any chip to preview the matched DNOS doc snippet.">'
                + '<span class="ai-dnos-sources__label">Verified sources:</span>'
                + chips + more + '</div>';
        }
        if (validation) {
            var issues = Array.isArray(validation.issues) ? validation.issues : [];
            var problems = issues.filter(function (it) {
                var sev = (it && (it.severity || '')).toString().toLowerCase();
                return sev === 'error' || sev === 'critical' || sev === 'warning';
            });
            var okClass = (validation.ok && problems.length === 0)
                ? 'ai-dnos-validation--ok' : '';
            var head;
            if (validation.validator_unavailable) {
                head = 'Validation skipped (cli_validator unavailable on this host).';
            } else if (validation.ok && problems.length === 0) {
                head = 'Validation passed (cli_validator).';
            } else if (validation.ok) {
                head = 'Validation passed with ' + problems.length + ' warning(s):';
            } else {
                head = 'Validation found ' + problems.length + ' issue(s):';
            }
            var listHtml = '';
            if (problems.length) {
                var li = problems.slice(0, 4).map(function (it) {
                    var sev = (it && (it.severity || 'info')).toString();
                    return '<li><b>' + _escapeHtml(sev) + ':</b> '
                        + _escapeHtml((it && it.message) || '') + '</li>';
                }).join('');
                if (problems.length > 4) {
                    li += '<li>+' + (problems.length - 4) + ' more...</li>';
                }
                listHtml = '<ul style="margin:4px 0 0 0;padding:0;list-style:none;">' + li + '</ul>';
            }
            html += '<div class="ai-dnos-validation ' + okClass + '">'
                + _escapeHtml(head) + listHtml
                + '</div>';
        }
        html += '</div>';
        return html;
    }

    function _renderToolCard(m) {
        var t = m.tool || {};
        // 2026-04-24r -- chip-picker card. Each chip, when clicked,
        // sends its `value` back as the next user message so the
        // model resumes with a concrete answer. allow_free_text
        // surfaces an additional "Something else..." chip that opens
        // the composer focused with a hint instead of sending right
        // away.
        if (t.name === 'ask_user_question' && t.status === 'question') {
            var chips = (t.options || []).map(function (o) {
                return '<button class="ai-chip" data-role="tool-action" '
                    + 'data-tool-action="question-pick" '
                    + 'data-msg-id="' + m._id + '" '
                    + 'data-value="' + _escapeHtml(o.value || o.label) + '">'
                    + _escapeHtml(o.label) + '</button>';
            }).join('');
            if (t.allow_free_text) {
                chips += '<button class="ai-chip ai-chip--ghost" data-role="tool-action" '
                    + 'data-tool-action="question-free" data-msg-id="' + m._id + '">'
                    + 'Something else...' + '</button>';
            }
            return '<div class="ai-tool-card ai-tool-card--question">'
                + '<div class="ai-tool-card__title">'
                +   '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9 9.5a3 3 0 1 1 5 2.3c-1 .7-2 1.3-2 2.7"/><circle cx="12" cy="17.5" r="0.6" fill="currentColor"/></svg>'
                +   'Quick question'
                + '</div>'
                + '<div class="ai-tool-card__stats">' + _escapeHtml(t.question || '') + '</div>'
                + '<div class="ai-tool-card__actions ai-tool-card__chips">' + chips + '</div>'
                + '</div>';
        }
        // 2026-04-24r -- canvas-edit *proposal*. Same payload shape as
        // apply_canvas_edits, but gated behind an Apply button so the
        // user can audit destructive / bulk edits before they mutate
        // the canvas.
        if (t.name === 'propose_canvas_edits' && t.status === 'propose') {
            var edits = (t.edits || []);
            var rows = edits.slice(0, 12).map(_renderProposedEditRow).join('');
            var extraRow = edits.length > 12
                ? '<li style="opacity:.7">...and ' + (edits.length - 12) + ' more edits</li>'
                : '';
            var proposedSummary = (t.summary || '').trim();
            return '<div class="ai-tool-card ai-tool-card--proposal">'
                + '<div class="ai-tool-card__title">'
                +   '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v16M4 12h16"/></svg>'
                +   'Proposed canvas edits (' + edits.length + ')'
                + '</div>'
                + (proposedSummary
                    ? '<div class="ai-tool-card__stats">' + _escapeHtml(proposedSummary) + '</div>'
                    : '')
                + '<ul class="ai-tool-card__edit-list" style="margin:6px 0 10px 18px;padding:0;font-size:12px;line-height:1.5;">'
                +   rows + extraRow
                + '</ul>'
                + '<div class="ai-tool-card__actions">'
                +   '<button class="ai-btn primary" data-role="tool-action" data-tool-action="propose-apply" data-msg-id="' + m._id + '">Apply edits</button>'
                +   '<button class="ai-btn secondary" data-role="tool-action" data-tool-action="propose-tweak" data-msg-id="' + m._id + '">Tweak...</button>'
                +   '<button class="ai-btn secondary" data-role="tool-action" data-tool-action="dismiss" data-msg-id="' + m._id + '">Cancel</button>'
                + '</div>'
                + '</div>';
        }
        // apply_canvas_edits renders a compact receipt instead of the
        // save-load card. The edits already executed on the canvas by
        // the time we reach this render, so there's no button to press.
        if (t.name === 'apply_canvas_edits') {
            var receipt = m.receipt || {};
            var counts = receipt.counts || {};
            var changeBits = [];
            if (counts.added_devices) changeBits.push('<b>' + counts.added_devices + '</b> device' + (counts.added_devices === 1 ? '' : 's') + ' added');
            if (counts.added_links)   changeBits.push('<b>' + counts.added_links   + '</b> link'   + (counts.added_links   === 1 ? '' : 's') + ' added');
            if (counts.added_texts)   changeBits.push('<b>' + counts.added_texts   + '</b> note'   + (counts.added_texts   === 1 ? '' : 's') + ' added');
            if (counts.removed)       changeBits.push('<b>' + counts.removed       + '</b> object' + (counts.removed       === 1 ? '' : 's') + ' removed');
            if (counts.moved)         changeBits.push('<b>' + counts.moved         + '</b> moved');
            if (counts.relabeled)     changeBits.push('<b>' + counts.relabeled     + '</b> relabeled');
            // 2026-04-24s -- pending_domains is bumped by the async
            // create_domain branch so the receipt no longer shows
            // "(no changes applied)" on a turn whose only visible
            // action is a domain being created in the background.
            if (counts.pending_domains) changeBits.push('<b>' + counts.pending_domains + '</b> domain'
                + (counts.pending_domains === 1 ? '' : 's') + ' creating...');
            if (!changeBits.length) changeBits.push('(no changes applied)');
            var warnHtml = '';
            if (Array.isArray(receipt.warnings) && receipt.warnings.length) {
                warnHtml = '<div class="ai-tool-card__stats" style="color:#f0b429;">'
                    + '<b>Notes:</b> '
                    + receipt.warnings.map(_escapeHtml).join('; ')
                    + '</div>';
            }
            var summary = (t.summary || '').trim();
            // 2026-04-24s -- pick a title that matches the dominant
            // action: synchronous canvas changes -> "Canvas updated";
            // only async domain creation -> "Domain ready"-style; no
            // change at all -> "Tool ran". Hides the "Undo" button
            // when there's nothing to undo (avoids the confusing
            // "Undo (no changes applied)" state from the screenshot).
            var didSync = (counts.added_devices + counts.added_links + counts.added_texts
                + counts.removed + counts.moved + counts.relabeled) > 0;
            var hasPending = !!counts.pending_domains;
            var cardTitle, cardIcon;
            if (didSync) {
                cardTitle = 'Canvas updated';
                cardIcon = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l5 5L20 7"/></svg>';
            } else if (hasPending) {
                cardTitle = counts.pending_domains === 1 ? 'Creating domain' : 'Creating domains';
                cardIcon = '<span class="ai-notice__spinner" aria-hidden="true" style="position:relative;top:1px;"></span>';
            } else {
                cardTitle = 'Tool ran (no canvas change)';
                cardIcon = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>';
            }
            var actionsHtml = '<div class="ai-tool-card__actions">';
            if (didSync) {
                actionsHtml += '<button class="ai-btn secondary" data-role="tool-action" data-tool-action="undo-edits" data-msg-id="' + m._id + '">Undo</button>';
            }
            actionsHtml += '<button class="ai-btn secondary" data-role="tool-action" data-tool-action="dismiss" data-msg-id="' + m._id + '">Dismiss</button>'
                + '</div>';
            return '<div class="ai-tool-card">'
                + '<div class="ai-tool-card__title">' + cardIcon + cardTitle + '</div>'
                + '<div class="ai-tool-card__stats">' + changeBits.join(' &middot; ') + '</div>'
                + (summary ? '<div class="ai-tool-card__stats">' + _escapeHtml(summary) + '</div>' : '')
                + warnHtml
                + actionsHtml
                + '</div>';
        }
        var topology = t.topology || {};
        var name = (topology.metadata && topology.metadata.name)
            || t.display_name || t.suggested_name || t.filename || 'untitled';
        var counts = _topologyCounts(topology);
        var devicesCount = counts.devices;
        var linksCount = counts.links;
        var statsBits = [];
        statsBits.push('<b>' + _escapeHtml(name) + '</b>');
        if (t.section_id) statsBits.push('domain <b>' + _escapeHtml(t.section_id === '__ai' ? 'AI' : t.section_id) + '</b>');
        statsBits.push('<b>' + devicesCount + '</b> device' + (devicesCount === 1 ? '' : 's'));
        statsBits.push('<b>' + linksCount + '</b> link' + (linksCount === 1 ? '' : 's'));
        if (t.status === 'rejected') {
            return '<div class="ai-tool-card">'
                + '<div class="ai-tool-card__title">Topology rejected</div>'
                + '<div class="ai-tool-card__stats">' + _escapeHtml(t.error || 'Unknown error') + '</div>'
                + '<div class="ai-tool-card__actions">'
                +   '<button class="ai-btn secondary" data-role="tool-action" data-tool-action="dismiss" data-msg-id="' + m._id + '">Dismiss</button>'
                + '</div>'
                + '</div>';
        }
        // Pending-placement card: the server generated the topology but
        // hasn't persisted it anywhere. Render a compact inline picker so
        // the user chooses (a) an existing domain, or (b) a brand-new
        // domain (name input). The AI used to dump every generation into
        // a hidden `__ai` domain, which users then had to clean up by
        // hand -- this path replaces that behaviour.
        if (t.status === 'pending_placement') {
            return _renderPendingPlacementCard(m, t, name, statsBits);
        }
        // Legacy saved path: older server builds still return status:
        // "saved" with section_id+filename already populated. Keep it
        // working so a mid-deploy cache never strands users with a card
        // they can't action.
        var saveLoadBtn = t.section_id && t.filename
            ? '<button class="ai-btn primary" data-role="tool-action" data-tool-action="save-load" data-msg-id="' + m._id + '">Save + Load on canvas</button>'
            : '';
        return '<div class="ai-tool-card">'
            + '<div class="ai-tool-card__title">'
            +   '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.8 4.5L18 9l-4.2 1.5L12 15l-1.8-4.5L6 9l4.2-1.5L12 3z"/></svg>'
            +   'Topology ready'
            + '</div>'
            + '<div class="ai-tool-card__stats">' + statsBits.join(' &middot; ') + '</div>'
            + '<div class="ai-tool-card__actions">'
            +   saveLoadBtn
            +   '<button class="ai-btn secondary" data-role="tool-action" data-tool-action="dismiss" data-msg-id="' + m._id + '">Dismiss</button>'
            + '</div>'
            + '</div>';
    }

    // --------------------------------------------------------------
    //   Pending-placement card (new: replaces auto-save-to-__ai flow)
    // --------------------------------------------------------------
    //
    // The card shows:
    //   [Topology stats]
    //   [radio] Existing domain <select> ...                 (default)
    //   [radio] New domain        <input name="...">
    //   [text] Topology name      <input name="...">
    //   [Place on canvas] [Dismiss]
    //
    // Domain list comes from the editor's cached `_customSections`
    // (populated by FileOps.loadCustomSections() on load). Builtin
    // `__bugs` is filtered out -- Bugs is Jira-ticket-only and refusing
    // a non-bug topology under it surfaces as a confusing server error.
    // `__ai` is also filtered to keep users from re-introducing the
    // exact behaviour we just removed.
    function _buildDomainOptions() {
        var ed = _editor();
        var domains = (ed && ed._customSections) || [];
        var out = [];
        for (var i = 0; i < domains.length; i += 1) {
            var d = domains[i] || {};
            if (!d.id || !d.name) continue;
            if (d.id === '__bugs' || d.id === '__ai') continue;
            if (d.is_shared_with_me_domain) continue;
            // Skip read-only shared-in domains -- we can't save to them.
            if (d.permission === 'read') continue;
            out.push({ id: d.id, name: d.name, color: d.color || '' });
        }
        // Alphabetise for predictability; user domains tend to outnumber
        // builtins and there's no "last active" signal here worth sorting on.
        out.sort(function (a, b) {
            return (a.name || '').toLowerCase().localeCompare((b.name || '').toLowerCase());
        });
        return out;
    }

    function _renderPendingPlacementCard(m, t, displayName, statsBits) {
        var options = _buildDomainOptions();
        var hasExisting = options.length > 0;
        // 2026-04-24s -- honour target_domain_existing / target_domain_new
        // hints emitted by the model. The point is to remove the
        // "now I have to fill out a form" gap between the assistant
        // saying "I'll put it in your new MPLS Lab" and the user
        // actually clicking Place. When the hint is present, we:
        //   - default the radio to "new" (or "existing" + select the
        //     resolved id) so the user just clicks Place.
        //   - prefill the new-domain name input.
        //   - show a reserved-name warning inline if the model
        //     suggested "AI" / "Bugs" / "DNAAS" so the user knows to
        //     rename before clicking.
        var hintExisting = (typeof t.target_domain_existing === 'string')
            ? t.target_domain_existing.trim() : '';
        var hintNew = (t.target_domain_new && typeof t.target_domain_new === 'object')
            ? t.target_domain_new : null;
        var hintNewName = (hintNew && typeof hintNew.name === 'string')
            ? hintNew.name.trim() : '';
        // Resolve hintExisting (may be a section id OR a display name)
        // against the editor's cache so we can pre-select the correct
        // <option>. Mismatches fall back to "no preselect" rather than
        // surfacing a confusing error.
        var hintExistingOptionId = '';
        if (hintExisting) {
            var hintLower = hintExisting.toLowerCase();
            for (var hi = 0; hi < options.length; hi += 1) {
                if (options[hi].id === hintExisting
                    || (options[hi].name || '').toLowerCase() === hintLower) {
                    hintExistingOptionId = options[hi].id;
                    break;
                }
            }
        }
        var defaultMode;
        if (hintNewName) defaultMode = 'new';
        else if (hintExistingOptionId) defaultMode = 'existing';
        else defaultMode = hasExisting ? 'existing' : 'new';
        var optionsHtml = options.map(function (d) {
            var sel = (d.id === hintExistingOptionId) ? ' selected' : '';
            return '<option value="' + _escapeHtml(d.id) + '"' + sel + '>' + d.name + '</option>';
        }).join('');
        var suggestedNewDomain = hintNewName || (hasExisting ? '' : 'AI Generated');
        var existingDisabled = hasExisting ? '' : ' disabled';
        // Reserved-name warning: keep the user from getting a server
        // 400 by flagging the collision before they click Place.
        var reservedHint = '';
        if (hintNewName && _isReservedDomainName(hintNewName)) {
            reservedHint = '<div class="ai-placement__note ai-placement__note--warn">'
                + '<b>Heads up:</b> "' + _escapeHtml(hintNewName) + '" is a reserved built-in domain name. '
                + 'Rename it (e.g. "' + _escapeHtml(hintNewName) + ' Lab") before placing.'
                + '</div>';
        }
        // Also warn when the model explicitly suggested putting it in a
        // built-in (AI/Bugs/DNAAS) -- those are filtered out of the
        // <select> so the "existing" branch would silently fall through
        // to "first available" and confuse the user.
        if (hintExisting && !hintExistingOptionId && _isReservedDomainName(hintExisting)) {
            reservedHint += '<div class="ai-placement__note ai-placement__note--warn">'
                + '<b>Heads up:</b> "' + _escapeHtml(hintExisting) + '" is a reserved built-in domain. '
                + 'Pick another domain or create a new one for this topology.'
                + '</div>';
        }
        var noteWhenEmpty = hasExisting
            ? ''
            : '<div class="ai-placement__note">No topology domains yet. A new one will be created for you.</div>';
        // 2026-04-24s -- subtitle that previews exactly what the Place
        // button will do, mirroring whichever radio is currently checked.
        // Updated client-side via the radio change handler so the user
        // always sees an accurate "next action" preview.
        var actionPreview;
        if (defaultMode === 'new') {
            actionPreview = 'Will create domain "' + _escapeHtml(hintNewName || suggestedNewDomain || 'New Domain')
                + '" and place ' + (devicesPlural(t) || 'topology') + ' inside it.';
        } else if (hintExistingOptionId) {
            var preName = '';
            for (var pi = 0; pi < options.length; pi += 1) {
                if (options[pi].id === hintExistingOptionId) { preName = options[pi].name; break; }
            }
            actionPreview = 'Will place ' + (devicesPlural(t) || 'topology') + ' in existing domain "'
                + _escapeHtml(preName) + '".';
        } else if (hasExisting) {
            actionPreview = 'Will place ' + (devicesPlural(t) || 'topology') + ' in the selected existing domain.';
        } else {
            actionPreview = 'Will create the domain above and place the topology in it.';
        }
        return '<div class="ai-tool-card ai-placement" data-msg-id="' + m._id + '">'
            + '<div class="ai-tool-card__title">'
            +   '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.8 4.5L18 9l-4.2 1.5L12 15l-1.8-4.5L6 9l4.2-1.5L12 3z"/></svg>'
            +   'Topology ready - where should it go?'
            + '</div>'
            + '<div class="ai-tool-card__stats">' + statsBits.join(' &middot; ') + '</div>'
            + noteWhenEmpty
            + reservedHint
            + '<div class="ai-placement__row">'
            +   '<label class="ai-placement__opt">'
            +     '<input type="radio" name="ai-placement-' + m._id + '" value="existing" data-role="placement-mode" ' + (defaultMode === 'existing' ? 'checked' : '') + existingDisabled + '>'
            +     '<span>Existing domain</span>'
            +   '</label>'
            +   '<select class="ai-placement__select" data-role="placement-existing" ' + existingDisabled + '>'
            +     optionsHtml
            +   '</select>'
            + '</div>'
            + '<div class="ai-placement__row">'
            +   '<label class="ai-placement__opt">'
            +     '<input type="radio" name="ai-placement-' + m._id + '" value="new" data-role="placement-mode" ' + (defaultMode === 'new' ? 'checked' : '') + '>'
            +     '<span>New domain</span>'
            +   '</label>'
            +   '<input type="text" class="ai-placement__input" data-role="placement-new-name" placeholder="Domain name (e.g. Lab Rigs)" value="' + _escapeHtml(suggestedNewDomain) + '">'
            + '</div>'
            + '<div class="ai-placement__row">'
            +   '<label class="ai-placement__opt ai-placement__opt--static"><span>Topology name</span></label>'
            +   '<input type="text" class="ai-placement__input" data-role="placement-topo-name" placeholder="topology name" value="' + _escapeHtml(displayName || '') + '" data-original-suggestion="' + _escapeHtml(displayName || '') + '">'
            + '</div>'
            + '<div class="ai-placement__preview" data-role="placement-preview">' + actionPreview + '</div>'
            + '<div class="ai-tool-card__actions">'
            +   '<button class="ai-btn primary" data-role="tool-action" data-tool-action="place" data-msg-id="' + m._id + '">Place on canvas</button>'
            +   '<button class="ai-btn secondary" data-role="tool-action" data-tool-action="dismiss" data-msg-id="' + m._id + '">Dismiss</button>'
            + '</div>'
            + '</div>';
    }

    function devicesPlural(t) {
        // Tiny helper for the placement preview line. Returns "5
        // devices" / "1 device" / "" so the preview reads naturally
        // when the topology has any devices, and falls back to a
        // generic "topology" when it doesn't.
        var n = _topologyCounts(t && t.topology).devices;
        if (!n) return '';
        return n + (n === 1 ? ' device' : ' devices');
    }

    async function _refreshUniquePlacementName(card) {
        if (!card) return;
        var modeRadio = card.querySelector('input[type="radio"]:checked');
        if (modeRadio && modeRadio.value === 'new') return;
        var existing = card.querySelector('[data-role="placement-existing"]');
        var topoInput = card.querySelector('[data-role="placement-topo-name"]');
        if (!existing || !existing.value || !topoInput) return;
        var original = (topoInput.dataset.originalSuggestion || topoInput.value || '').trim() || 'ai-topology';
        var current = (topoInput.value || '').trim();
        if (current && current !== original && current.indexOf(original + '-') !== 0) {
            topoInput.dataset.userEdited = '1';
            return;
        }
        if (topoInput.dataset.userEdited === '1') return;
        var unique = await _ensureUniqueTopologyName(existing.value, original);
        if (unique && unique !== current) {
            topoInput.dataset.autoUnique = '1';
            topoInput.value = unique;
            topoInput.dataset.originalSuggestion = original;
            topoInput.dispatchEvent(new Event('input', { bubbles: true }));
            delete topoInput.dataset.autoUnique;
        }
    }

    function _topologyCounts(topology) {
        var out = { devices: 0, links: 0 };
        if (!topology || typeof topology !== 'object') return out;
        if (Array.isArray(topology.devices)) out.devices = topology.devices.length;
        if (Array.isArray(topology.links)) out.links = topology.links.length;
        if (Array.isArray(topology.objects)) {
            out.devices = 0;
            out.links = 0;
            topology.objects.forEach(function (o) {
                if (!o || typeof o !== 'object') return;
                if (o.type === 'device') out.devices += 1;
                else if (o.type === 'link') out.links += 1;
            });
        }
        return out;
    }

    function _topologyNameKey(name) {
        return String(name || '')
            .replace(/\.json$/i, '')
            .trim()
            .replace(/[^A-Za-z0-9_-]/g, '_')
            .toLowerCase();
    }

    function _uniqueTopologyName(baseName, topologies) {
        var base = String(baseName || '').trim() || 'ai-topology';
        var used = new Set();
        (topologies || []).forEach(function (t) {
            if (!t) return;
            used.add(_topologyNameKey(t.name || t.filename || ''));
        });
        if (!used.has(_topologyNameKey(base))) return base;
        for (var i = 2; i < 1000; i += 1) {
            var candidate = base + '-' + i;
            if (!used.has(_topologyNameKey(candidate))) return candidate;
        }
        return base + '-' + Date.now();
    }

    async function _fetchSectionTopologies(sectionId) {
        if (!sectionId) return [];
        var resp = await _authFetch('/api/sections/' + encodeURIComponent(sectionId) + '/topologies');
        if (!resp.ok) return [];
        var json = await resp.json().catch(function () { return null; });
        return (json && Array.isArray(json.topologies)) ? json.topologies : [];
    }

    async function _ensureUniqueTopologyName(sectionId, name) {
        try {
            return _uniqueTopologyName(name, await _fetchSectionTopologies(sectionId));
        } catch (_) {
            return String(name || '').trim() || 'ai-topology';
        }
    }

    async function _sendUserMessage(text) {
        if (_sending) return;
        _sending = true;
        _lastUserMessage = text;
        _appendMessage('user', text);
        // 2026-04-24s -- include the provider/model in the loading
        // bubble so the user sees WHICH brain is thinking. Big UX win
        // for users who switch between Gemini Lite / Groq / Anthropic
        // -- before, the bubble just said "Thinking..." with no
        // attribution, making it hard to correlate latency or quality
        // problems with a specific provider.
        // First beat: server may run a fast topology-intent preflight before
        // the LLM; then we swap to the provider-specific label after ~650ms.
        var loadingLabel = 'Checking topology intent…';
        var loading = _appendMessage('assistant', loadingLabel, { loading: true });
        var sendBtn = _drawerEl && _drawerEl.querySelector('[data-role="send"]');
        if (sendBtn) {
            sendBtn.disabled = true;
            // The send button is a SVG icon + a <span>Send</span>; we
            // only swap the span's text so the icon stays put.
            var sendLabel = sendBtn.querySelector('span');
            if (sendLabel) {
                if (!sendBtn.dataset.origLabel) sendBtn.dataset.origLabel = sendLabel.textContent || 'Send';
                sendLabel.textContent = 'Sending...';
            }
            sendBtn.classList.add('ai-btn--working');
        }
        // Tiny click acknowledgement -- a 120ms accent flash on the
        // input row tells the user "yes I saw your click" even before
        // the loading bubble lands. Prevents the "did anything happen?"
        // double-click problem on slow turns.
        try { _flashSendAck(); } catch (_) {}
        // Grey out the chat toolbar while the request is in-flight so
        // Regenerate / New chat / Export can't race the fetch.
        _updateChatToolbarState();
        // Elapsed-time ticker. Without this the user stares at a static
        // "Thinking..." for up to 4 minutes on a CPU-bound local model
        // and can't tell if the request is actually making progress or
        // if the tab has hung. We patch only the timer span to avoid a
        // full re-render every second (the chat log is a DOM repaint
        // that would flicker the mouse hover / selection).
        var _startTs = Date.now();
        loading._elapsed = 0;
        var _phase2Timer = setTimeout(function () {
            if (!_sending) return;
            var log2 = _drawerEl && _drawerEl.querySelector('[data-role="log"]');
            var bubble2 = log2 && log2.querySelector('.ai-msg.loading[data-id="' + loading._id + '"]');
            var label2 = bubble2 && bubble2.querySelector('.ai-loading__label');
            if (label2) label2.textContent = _composeLoadingLabel();
        }, 650);
        var _tickTimer = setInterval(function () {
            if (!_sending) {
                clearInterval(_tickTimer);
                try { clearTimeout(_phase2Timer); } catch (_) {}
                return;
            }
            var secs = Math.floor((Date.now() - _startTs) / 1000);
            loading._elapsed = secs;
            var log = _drawerEl && _drawerEl.querySelector('[data-role="log"]');
            if (!log) return;
            var bubble = log.querySelector('.ai-msg.loading[data-id="' + loading._id + '"]');
            if (!bubble) return;
            var timer = bubble.querySelector('[data-role="loading-timer"]');
            if (timer) timer.textContent = secs + 's';
            // First time we cross the provider-appropriate threshold,
            // splice in the slow-path hint. Ollama -> "local CPU is slow,
            // try Groq". Everything else (Groq / OpenAI / Anthropic) ->
            // "try GPT-OSS 120B on Groq" because anything past ~8s on a
            // hosted provider is already abnormal. We NEVER tell a Groq
            // user to "switch to Groq" (that was the regression from
            // 2026-04-21h that made the UX feel broken).
            var _p = (_aiConfig && _aiConfig.provider || '').toLowerCase();
            var _threshold = (_p === 'ollama') ? 12 : 8;
            if (secs === _threshold && !bubble.querySelector('.ai-loading__hint')) {
                var hint = document.createElement('div');
                hint.className = 'ai-loading__hint';
                if (_p === 'ollama') {
                    hint.textContent = 'Local CPU models can take 1-3 min for the first answer. '
                        + 'For faster hosted responses, use Gemini Flash in settings.';
                } else {
                    hint.textContent = 'Still waiting on the provider. '
                        + 'Tool-heavy topology turns can take longer; the server '
                        + 'will retry or fall back automatically when the model rate-limits.';
                }
                bubble.appendChild(hint);
            }
        }, 1000);
        // AbortController lets the user actually cancel a request mid-
        // flight instead of waiting for the server timeout. The Stop
        // button below calls .abort() which rejects the fetch with an
        // AbortError -- we catch it and render a "cancelled" message.
        var _abort = new AbortController();
        _currentAbort = _abort;
        try {
            if (_aiConfig.configured === false) {
                _replaceMessage(loading._id, {
                    loading: false, error: true,
                    content: 'No AI credentials configured yet. Click the gear icon to set up your key.',
                });
                _toggleConfigPanel(true);
                return;
            }
            var canvasSnapshot = _collectCanvasSnapshot();
            var chatHistory = _messages
                .filter(function (m) { return m.role === 'user' || (m.role === 'assistant' && !m.loading && !m.error); })
                .map(function (m) { return { role: m.role, content: m.content }; });
            var resp = await _authFetch('/api/ai/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: chatHistory,
                    canvas: canvasSnapshot,
                    conversation_id: _currentConvId || undefined,
                }),
                signal: _abort.signal,
            });
            var json = null;
            try { json = await resp.json(); } catch (_) {}
            if (!resp.ok || !json || json.error) {
                var msg = (json && json.error) || ('HTTP ' + resp.status);
                if (json && json.code === 'not-configured') {
                    _replaceMessage(loading._id, {
                        loading: false, error: true,
                        content: 'AI is not configured yet on this server. Click the gear icon to add your key.',
                    });
                    _toggleConfigPanel(true);
                    return;
                }
                // Upstream failures now carry a classified ``kind``
                // (insufficient_quota, rate_limited, api_key_rejected,
                // model_not_found, context_overflow, timeout,
                // unreachable, upstream_error). Render a targeted card
                // with next-step actions instead of dumping the raw
                // provider JSON.
                var kind = (json && json.kind) || '';
                if (!kind && resp.status === 401) kind = 'api_key_rejected';
                if (!kind && resp.status === 402) kind = 'insufficient_quota';
                if (!kind && resp.status === 429) kind = 'rate_limited';
                // 503 on this path means either our proxy couldn't reach
                // the bridge OR the upstream model reported overload.
                // `json.details` often contains the upstream body and
                // makes the call -- use the "overloaded"/"unavailable"
                // signals the backend classifier already knows about.
                if (!kind && resp.status === 503) {
                    var detailsLower = ((json && json.details) || '').toLowerCase();
                    if (detailsLower.indexOf('overloaded') !== -1
                        || detailsLower.indexOf('unavailable') !== -1
                        || detailsLower.indexOf('experiencing high demand') !== -1) {
                        kind = 'upstream_overloaded';
                    }
                }
                var provider = (json && json.provider) || (_aiConfig && _aiConfig.provider) || '';
                var details  = (json && json.details) || '';
                var cardHtml = _renderChatErrorCard(kind || 'upstream_error', msg, details, provider);
                _replaceMessage(loading._id, {
                    loading: false, error: true, errorCardHtml: cardHtml,
                    content: msg, // keep for accessibility / copy-paste fallbacks
                });
                // For the two cases where the user has to edit config to
                // recover (no way forward without), nudge the panel open.
                if (kind === 'api_key_rejected') _toggleConfigPanel(true);
                return;
            }
            // Happy path. If the model produced text, replace the
            // loading bubble with it; otherwise remove it. Then append
            // tool cards for each tool call (create_topology saved /
            // rejected / preview).
            // `json.retried` is populated when the server auto-retried
            // a transient 429 -- we attach it so the final assistant
            // message shows an "auto-recovered" pill.
            var retryInfo = (json && json.retried) || null;
            // Capture conversation metadata (id + title) that the
            // server echoes back. On the FIRST turn of a brand-new
            // conversation this is when we learn our id -- the chip
            // updates immediately, and subsequent turns send the id.
            if (json && json.conversation_id) {
                var wasNew = !_currentConvId;
                _currentConvId = json.conversation_id;
                if (json.conversation && json.conversation.title) {
                    _currentConvTitle = json.conversation.title;
                }
                _updateConvTitleChip();
                if (wasNew) {
                    // Server just created the row; prepend a stub to
                    // the cached list so "History" shows it right
                    // away without waiting for the refresh GET.
                    var stub = {
                        id: _currentConvId,
                        title: _currentConvTitle || 'New chat',
                        updated_at: Date.now(),
                        turn_count: (json.conversation && json.conversation.turn_count) || 2,
                        archived: false,
                        pinned: false,
                    };
                    _conversations = [stub].concat((_conversations || []).filter(function (c) {
                        return c.id !== stub.id;
                    }));
                } else {
                    _conversations = (_conversations || []).map(function (c) {
                        if (c.id !== _currentConvId) return c;
                        return Object.assign({}, c, {
                            updated_at: Date.now(),
                            turn_count: (json.conversation && json.conversation.turn_count) || (c.turn_count || 0) + 2,
                        });
                    });
                }
                // Quietly pull the authoritative list in the background.
                // This corrects turn_count drift and picks up changes
                // from another tab/session without blocking the UI.
                setTimeout(_refreshConvListFromServer, 50);
            }
            // 2026-04-24r -- surface the server's blueprint-consulted
            // list as a chip on the assistant bubble (see
            // _renderChatLog).
            var consultedList = Array.isArray(json && json.blueprints_consulted)
                ? json.blueprints_consulted : null;
            // 2026-04-26 -- DNOS-grounded turn metadata. When the
            // backend intent gate fires, the response carries:
            //   dnos_grounded      : true
            //   dnos_intent        : { is_config_intent, confidence, reason }
            //   dnos_sources       : [ {source, doc_name, category, path, snippet} ]
            //   dnos_validation    : { ok, issues[] }
            //   dnos_config        : raw CLI body (already inside ``` in text)
            //   dnos_error         : { kind, message } when the model could not ground
            // We stash these fields on the assistant bubble; the renderer
            // promotes the message to a "Verified from DNOS docs" card.
            var dnosGrounded = !!(json && json.dnos_grounded);
            var dnosSources = (json && Array.isArray(json.dnos_sources))
                ? json.dnos_sources : null;
            var dnosValidation = (json && json.dnos_validation) || null;
            var dnosError = (json && json.dnos_error) || null;
            var dnosConfig = (json && typeof json.dnos_config === 'string') ? json.dnos_config : '';
            var dnosIntent = (json && json.dnos_intent) || null;
            if (json.text && json.text.trim()) {
                _replaceMessage(loading._id, {
                    loading: false, content: json.text,
                    retryInfo: retryInfo,
                    consulted: consultedList,
                    dnosGrounded: dnosGrounded,
                    dnosSources: dnosSources,
                    dnosValidation: dnosValidation,
                    dnosError: dnosError,
                    dnosConfig: dnosConfig,
                    dnosIntent: dnosIntent,
                });
            } else if (retryInfo) {
                // Tool-only reply: keep a tiny notice so the retry is
                // still visible.
                _replaceMessage(loading._id, {
                    loading: false,
                    notice: true,
                    content: 'Auto-recovered from ' + (retryInfo.provider || 'provider')
                        + ' rate limit (waited ' + Number(retryInfo.wait_s).toFixed(1) + 's).',
                    consulted: consultedList,
                });
            } else if (consultedList && consultedList.length) {
                // No text AND no retry, but blueprints were consulted
                // (e.g. the model only called list_blueprints then
                // emitted a tool call). Keep the chip visible so the
                // user still sees the lookup attribution.
                _replaceMessage(loading._id, {
                    loading: false,
                    notice: true,
                    content: 'Consulted ' + consultedList.length
                        + ' blueprint' + (consultedList.length === 1 ? '' : 's') + '.',
                    consulted: consultedList,
                });
            } else {
                _removeMessage(loading._id);
            }
            var calls = Array.isArray(json.tool_calls) ? json.tool_calls : [];
            calls.forEach(function (tc) {
                if (tc.name === 'create_topology') {
                    _appendMessage('assistant', '', { tool: tc });
                } else if (tc.name === 'apply_canvas_edits' && tc.status === 'apply') {
                    // Live canvas edit -- execute immediately, then
                    // render a summary receipt instead of a load card.
                    try {
                        var receipt = _applyCanvasEdits(tc);
                        _appendMessage('assistant', '', { tool: tc, receipt: receipt, applied: true });
                    } catch (err) {
                        _appendMessage('assistant',
                            'Canvas edit failed: ' + (err && err.message ? err.message : err),
                            { error: true });
                    }
                } else if (tc.name === 'apply_canvas_edits' && tc.status === 'rejected') {
                    _appendMessage('assistant',
                        'Edit rejected by server: ' + (tc.error || 'unknown reason'),
                        { error: true });
                } else if (tc.name === 'propose_canvas_edits' && tc.status === 'propose') {
                    // 2026-04-24r -- preview card. We do NOT mutate
                    // the canvas yet; user presses Apply on the card
                    // to run _applyCanvasEdits, or Cancel to discard.
                    _appendMessage('assistant', '', { tool: tc });
                } else if (tc.name === 'propose_canvas_edits' && tc.status === 'rejected') {
                    _appendMessage('assistant',
                        'Proposal rejected by server: ' + (tc.error || 'unknown reason'),
                        { error: true });
                } else if (tc.name === 'ask_user_question' && tc.status === 'question') {
                    // 2026-04-24r -- chip-picker card. Each chip's
                    // value is sent back as the next user turn when
                    // clicked (see tool-action "question-pick").
                    _appendMessage('assistant', '', { tool: tc });
                } else if (tc.name === 'ask_user_question' && tc.status === 'rejected') {
                    _appendMessage('assistant',
                        'Question rejected by server: ' + (tc.error || 'unknown reason'),
                        { error: true });
                } else {
                    _appendMessage('assistant',
                        'The model requested an unsupported tool: ' + (tc.name || '?')
                        + '. (Ignored for now.)', { notice: true });
                }
            });
        } catch (e) {
            var isAbort = e && (e.name === 'AbortError' || e.code === 20);
            if (isAbort) {
                _replaceMessage(loading._id, {
                    loading: false, notice: true,
                    content: 'Request cancelled.',
                });
            } else {
                _replaceMessage(loading._id, {
                    loading: false, error: true,
                    content: 'Network error: ' + (e && e.message ? e.message : e),
                });
            }
        } finally {
            _sending = false;
            _currentAbort = null;
            try { clearInterval(_tickTimer); } catch (_) {}
            try { clearTimeout(_phase2Timer); } catch (_) {}
            if (sendBtn) {
                var input = _drawerEl.querySelector('[data-role="composer-input"]');
                sendBtn.disabled = !input || !input.value.trim();
                // Restore the original button label (was "Sending..."
                // during the request) without destroying the SVG icon.
                // Older code assigned sendBtn.textContent, which replaced
                // the whole button DOM after the first send.
                var restoreLabel = sendBtn.querySelector('span');
                if (restoreLabel) {
                    restoreLabel.textContent = sendBtn.dataset.origLabel || 'Send';
                } else {
                    sendBtn.textContent = sendBtn.dataset.origLabel || 'Send';
                }
                sendBtn.classList.remove('ai-btn--working');
            }
            // Re-enable Regenerate / New chat / Export now that the
            // request is done (success OR error OR cancel).
            _updateChatToolbarState();
        }
    }

    // 2026-04-24s -- pretty model label for the loading bubble.
    // Mirrors the dropdown's short-label so the bubble reads
    // "Asking Gemini Flash Lite..." without us having to thread the
    // model id through the renderer. Falls back to "Thinking..." when
    // we genuinely don't know what's running (e.g. corrupted cache).
    function _composeLoadingLabel() {
        try {
            if (!_aiConfig || _aiConfig.configured === false) return 'Thinking...';
            var prov = (_aiConfig.provider || '').toLowerCase();
            var preset = (typeof PROVIDER_PRESETS !== 'undefined') ? PROVIDER_PRESETS[prov] : null;
            var pretty = (preset && preset.short_label) || prov || 'AI';
            var modelId = _aiConfig.model || '';
            // Strip noisy version suffixes for the bubble; the full
            // model id stays available in settings if the user cares.
            var modelShort = modelId
                .replace(/^models\//, '')
                .replace(/-2025-\d{2}-\d{2}/, '')
                .replace(/-latest$/, '');
            if (modelShort && modelShort.length > 28) {
                modelShort = modelShort.slice(0, 25) + '...';
            }
            if (modelShort) return 'Asking ' + pretty + ' (' + modelShort + ')...';
            return 'Asking ' + pretty + '...';
        } catch (_) { return 'Thinking...'; }
    }

    // Brief click-acknowledgement flash on the composer's send row.
    // The class is removed via setTimeout (not transitionend, which
    // can be flaky on rapid retries). 120ms keeps it under the human
    // perceptual threshold for "feels instant" while still being
    // visible enough to register.
    function _flashSendAck() {
        if (!_drawerEl) return;
        var row = _drawerEl.querySelector('[data-role="composer-row"]')
            || _drawerEl.querySelector('.ai-composer-row')
            || (_drawerEl.querySelector('[data-role="send"]')
                && _drawerEl.querySelector('[data-role="send"]').parentNode);
        if (!row) return;
        row.classList.add('ai-composer-row--ack');
        setTimeout(function () { row.classList.remove('ai-composer-row--ack'); }, 220);
    }

    // ------------------------------------------------------------------
    //   apply_canvas_edits executor
    // ------------------------------------------------------------------
    //
    // The server's /api/ai/chat emits tool_calls with:
    //   { name: 'apply_canvas_edits', status: 'apply',
    //     summary: str, edits: [{op, ...}, ...] }
    //
    // We mutate the live canvas in-place, without going through the
    // save-to-disk-then-reload path. One saveState() at the top lets
    // Ctrl+Z (or the Undo button on the tool card) revert the whole
    // batch atomically.
    //
    // Smart placement: when an add_device or add_text edit omits x/y
    // we pick coords based on the device's `role`. Spines go into the
    // spine row, leaves into the leaf row, etc. The row positions are
    // derived from existing devices if the canvas already has any
    // matching role; otherwise we fall back to a fresh coordinate
    // band. See _pickSmartPlacement below.
    // ------------------------------------------------------------------
    var _AI_ROLE_TIERS = {
        // Data-center fabric
        'super-spine': 0, 'superspine': 0, 'ssp': 0,
        'spine': 1,
        'leaf':  2, 'tor': 2,
        // Service-provider backbone
        'rr':    0, 'route-reflector': 0,
        'core':  1, 'p':    1,
        'pe':    2, 'edge': 2, 'border': 2,
        'ce':    3, 'cpe':  3, 'host': 3,
        // Enterprise campus
        'dist':  1, 'distribution': 1, 'agg': 1,
        'access': 2, 'sw':  2,
    };
    var _AI_LAYOUT = {
        tierGap: 300,      // vertical distance between tiers
        siblingGap: 200,   // horizontal distance between same-tier neighbours
        originX: 400,
        originY: 250,
    };
    function _aiTierForRole(role) {
        if (!role) return null;
        var norm = String(role).toLowerCase().trim();
        if (Object.prototype.hasOwnProperty.call(_AI_ROLE_TIERS, norm)) {
            return _AI_ROLE_TIERS[norm];
        }
        // Longest-prefix match so "super-spine-01" still hits 0.
        var bestTier = null;
        var bestLen = -1;
        Object.keys(_AI_ROLE_TIERS).forEach(function (k) {
            if (norm.indexOf(k) !== -1 && k.length > bestLen) {
                bestTier = _AI_ROLE_TIERS[k];
                bestLen = k.length;
            }
        });
        return bestTier;
    }
    function _aiFindDevice(editor, idOrLabel) {
        if (!editor || !idOrLabel) return null;
        var needle = String(idOrLabel);
        var objs = editor.objects || [];
        // Exact id hit first.
        for (var i = 0; i < objs.length; i += 1) {
            if (objs[i].type === 'device' && String(objs[i].id) === needle) return objs[i];
        }
        // Then exact label hit.
        for (var j = 0; j < objs.length; j += 1) {
            if (objs[j].type === 'device' && String(objs[j].label || '').trim() === needle.trim()) {
                return objs[j];
            }
        }
        // Case-insensitive label as last resort.
        var lc = needle.toLowerCase().trim();
        for (var k = 0; k < objs.length; k += 1) {
            if (objs[k].type === 'device' && String(objs[k].label || '').toLowerCase().trim() === lc) {
                return objs[k];
            }
        }
        return null;
    }
    function _aiFindAny(editor, idOrLabel) {
        if (!editor || !idOrLabel) return null;
        var needle = String(idOrLabel);
        var objs = editor.objects || [];
        for (var i = 0; i < objs.length; i += 1) {
            if (String(objs[i].id) === needle) return objs[i];
        }
        for (var j = 0; j < objs.length; j += 1) {
            if (String(objs[j].label || '').trim() === needle.trim()) return objs[j];
        }
        return null;
    }
    function _pickSmartPlacement(editor, role) {
        // Given a role, return {x, y} that places a new device in the
        // same row as existing same-role peers (right of the rightmost
        // one), or drops into a fresh row if none exist.
        var tier = _aiTierForRole(role);
        var allDevices = (editor.objects || []).filter(function (o) { return o.type === 'device'; });
        // Group existing devices by their detected tier.
        var tiers = {};
        allDevices.forEach(function (d) {
            var r = d.role || d.deviceType || d.label || '';
            var t = _aiTierForRole(r);
            if (t === null || t === undefined) return;
            (tiers[t] = tiers[t] || []).push(d);
        });
        var rowY;
        if (tier === null || tier === undefined) {
            // No role hint -- stack to the right of the newest device.
            // Find the max x on the canvas; drop at max_x + siblingGap.
            var maxX = _AI_LAYOUT.originX - _AI_LAYOUT.siblingGap;
            var someY = _AI_LAYOUT.originY + _AI_LAYOUT.tierGap; // middle-ish
            allDevices.forEach(function (d) {
                if (typeof d.x === 'number' && d.x > maxX) maxX = d.x;
                if (typeof d.y === 'number') someY = d.y;
            });
            return { x: maxX + _AI_LAYOUT.siblingGap, y: someY };
        }
        var row = tiers[tier] || [];
        if (row.length === 0) {
            // Seed a new row at tier*tierGap offset.
            rowY = _AI_LAYOUT.originY + tier * _AI_LAYOUT.tierGap;
            return { x: _AI_LAYOUT.originX, y: rowY };
        }
        // Peers exist -- place to the right of the rightmost peer at
        // the same Y band.
        var maxPeerX = -Infinity;
        var avgPeerY = 0;
        row.forEach(function (d) {
            if (typeof d.x === 'number' && d.x > maxPeerX) maxPeerX = d.x;
            avgPeerY += (typeof d.y === 'number' ? d.y : _AI_LAYOUT.originY);
        });
        avgPeerY /= row.length;
        return {
            x: (isFinite(maxPeerX) ? maxPeerX : _AI_LAYOUT.originX) + _AI_LAYOUT.siblingGap,
            y: avgPeerY,
        };
    }
    function _applyCanvasEdits(tool) {
        var ed = _editor();
        if (!ed) throw new Error('Editor not ready');
        var edits = (tool && Array.isArray(tool.edits)) ? tool.edits : [];
        // Single saveState for the whole batch -> one undo to revert.
        if (typeof ed.saveState === 'function') {
            try { ed.saveState(); } catch (_) {}
        }
        var counts = {
            added_devices: 0, added_links: 0, added_texts: 0,
            removed: 0, moved: 0, relabeled: 0,
        };
        var warnings = [];
        // Track newly-created devices by their incoming labels so
        // subsequent edits in the SAME batch can reference them before
        // they're committed to editor.objects (we push immediately, but
        // add_link can legally come before or after the target
        // add_device if the LLM doesn't preserve order).
        var justAddedByLabel = {};
        edits.forEach(function (edit, idx) {
            if (!edit || typeof edit !== 'object') return;
            var op = String(edit.op || '').toLowerCase();
            try {
                if (op === 'add_device') {
                    var deviceType = edit.deviceType || 'router';
                    var role = edit.role || '';
                    var coords = (typeof edit.x === 'number' && typeof edit.y === 'number')
                        ? { x: edit.x, y: edit.y }
                        : _pickSmartPlacement(ed, role);
                    // addAtPosition auto-generates a label; override if
                    // the caller supplied one. Uniqueness is ensured
                    // because addAtPosition's own label generator is
                    // already unique, and we only replace the label on
                    // the returned object.
                    var mgr = ed.devices;
                    var dev = null;
                    if (mgr && typeof mgr.addAtPosition === 'function') {
                        dev = mgr.addAtPosition(deviceType, coords.x, coords.y);
                    } else if (typeof ed.addDeviceAtPosition === 'function') {
                        dev = ed.addDeviceAtPosition(deviceType, coords.x, coords.y);
                    }
                    if (!dev) {
                        warnings.push('edit[' + idx + '] add_device: could not create device');
                        return;
                    }
                    if (edit.label && typeof edit.label === 'string') {
                        // Keep uniqueness: if label collides, append a
                        // suffix. addAtPosition already failed early
                        // when deviceNumbering is on and duplicates
                        // would occur, so we only reach this for manual
                        // labels where the user chose explicit naming.
                        var desired = edit.label.trim();
                        var taken = (ed.objects || []).some(function (o) {
                            return o !== dev && o.type === 'device' && (o.label || '') === desired;
                        });
                        if (taken) {
                            var suffix = 2;
                            while ((ed.objects || []).some(function (o) {
                                return o !== dev && o.type === 'device' && (o.label || '') === (desired + '-' + suffix);
                            })) suffix += 1;
                            dev.label = desired + '-' + suffix;
                            warnings.push('label "' + desired + '" was taken; used "' + dev.label + '"');
                        } else {
                            dev.label = desired;
                        }
                    }
                    if (role) dev.role = role;
                    if (edit.ip) dev.ip = String(edit.ip);
                    if (edit.color) dev.color = String(edit.color);
                    if (edit.visualStyle) dev.visualStyle = String(edit.visualStyle);
                    justAddedByLabel[(dev.label || '').trim()] = dev;
                    counts.added_devices += 1;
                } else if (op === 'add_link') {
                    var from = edit.from || edit.device1;
                    var to = edit.to || edit.device2;
                    if (!from || !to) {
                        warnings.push('edit[' + idx + '] add_link missing from/to');
                        return;
                    }
                    var a = justAddedByLabel[String(from).trim()] || _aiFindDevice(ed, from);
                    var b = justAddedByLabel[String(to).trim()]   || _aiFindDevice(ed, to);
                    if (!a || !b) {
                        warnings.push('edit[' + idx + '] add_link: could not resolve '
                            + (a ? '' : '"' + from + '"')
                            + (a || b ? '' : ' and ')
                            + (b ? '' : '"' + to + '"'));
                        return;
                    }
                    if (a === b) {
                        warnings.push('edit[' + idx + '] add_link: self-loop ignored');
                        return;
                    }
                    if (typeof ed.createLink === 'function') {
                        ed.createLink(a, b);
                        // createLink() pushes the new link as the LAST
                        // object. We grab it to apply caller-provided
                        // styling (color/style/width/label/linkType)
                        // so protocol-tagged links render correctly
                        // via topology-link-styles.js even when the LLM
                        // only emitted linkType.
                        var newLink = null;
                        for (var li = (ed.objects || []).length - 1; li >= 0; li -= 1) {
                            var oCand = ed.objects[li];
                            if (oCand && oCand.type === 'link'
                                    && oCand.device1 === a.id && oCand.device2 === b.id) {
                                newLink = oCand;
                                break;
                            }
                        }
                        if (newLink) {
                            if (typeof edit.color === 'string' && edit.color) newLink.color = edit.color;
                            if (typeof edit.style === 'string' && edit.style) newLink.style = edit.style;
                            if (typeof edit.width === 'number' && edit.width > 0) newLink.width = edit.width;
                            if (typeof edit.label === 'string' && edit.label.trim()) newLink.label = edit.label.trim();
                            if (typeof edit.linkType === 'string' && edit.linkType) {
                                newLink.linkType = edit.linkType.trim().toLowerCase();
                            }
                            // Link-table metadata (2026-04-26): topology
                            // generator and AI enrichment can attach
                            // interface names, VLAN id, bridge domain
                            // and a free-form `linkDetails` blob so the
                            // built-in link-table popup picks them up.
                            if (typeof edit.interface1 === 'string' && edit.interface1) {
                                newLink.interface1 = edit.interface1.trim();
                            }
                            if (typeof edit.interface2 === 'string' && edit.interface2) {
                                newLink.interface2 = edit.interface2.trim();
                            }
                            if (edit.vlan != null && String(edit.vlan).trim() !== '') {
                                newLink.vlan = String(edit.vlan).trim();
                            }
                            if (typeof edit.bd === 'string' && edit.bd) {
                                newLink.bd = edit.bd.trim();
                            }
                            if (edit.linkDetails && typeof edit.linkDetails === 'object') {
                                newLink.linkDetails = Object.assign(
                                    {},
                                    newLink.linkDetails || {},
                                    edit.linkDetails
                                );
                            }
                        }
                        counts.added_links += 1;
                    } else {
                        warnings.push('edit[' + idx + '] add_link: editor.createLink() unavailable');
                    }
                } else if (op === 'add_unbound_link') {
                    // 'UL' / unbounded link: both endpoints float (no
                    // device connection). Used when the user asks for
                    // a placeholder / BUL-chain seed / loose link they
                    // plan to drag onto devices themselves.
                    //
                    // Placement priority (highest -> lowest):
                    //   1. Explicit x1/y1/x2/y2 on the edit.
                    //   2. anchor + anchor_position ("above spine-1").
                    //   3. Explicit x/y center (length+orientation spread).
                    //   4. ed.createUnboundLink() with smart Y collision
                    //      avoidance (canvas centre).
                    var ul = null;
                    var lenPx = (typeof edit.length === 'number' && edit.length > 20) ? edit.length : 120;
                    var half = lenPx / 2;
                    var orient = (edit.orientation === 'vertical') ? 'vertical' : 'horizontal';
                    var startPt = null, endPt = null;
                    if (typeof edit.x1 === 'number' && typeof edit.y1 === 'number'
                            && typeof edit.x2 === 'number' && typeof edit.y2 === 'number') {
                        startPt = { x: edit.x1, y: edit.y1 };
                        endPt   = { x: edit.x2, y: edit.y2 };
                    } else if (edit.anchor) {
                        var anchorDev = justAddedByLabel[String(edit.anchor).trim()]
                            || _aiFindDevice(ed, edit.anchor);
                        if (!anchorDev) {
                            warnings.push('edit[' + idx + '] add_unbound_link: anchor "' + edit.anchor + '" not found');
                            return;
                        }
                        var pos = (edit.anchor_position || 'above').toLowerCase();
                        var ar = (typeof anchorDev.radius === 'number') ? anchorDev.radius : 30;
                        var gap = Math.max(60, ar + 36);  // clear the device body + breathing room
                        var ax = anchorDev.x, ay = anchorDev.y;
                        if (pos === 'below') {
                            orient = 'horizontal';
                            startPt = { x: ax - half, y: ay + gap };
                            endPt   = { x: ax + half, y: ay + gap };
                        } else if (pos === 'left') {
                            orient = 'vertical';
                            startPt = { x: ax - gap, y: ay - half };
                            endPt   = { x: ax - gap, y: ay + half };
                        } else if (pos === 'right') {
                            orient = 'vertical';
                            startPt = { x: ax + gap, y: ay - half };
                            endPt   = { x: ax + gap, y: ay + half };
                        } else { // 'above' (default)
                            orient = 'horizontal';
                            startPt = { x: ax - half, y: ay - gap };
                            endPt   = { x: ax + half, y: ay - gap };
                        }
                    } else if (typeof edit.x === 'number' && typeof edit.y === 'number') {
                        if (orient === 'vertical') {
                            startPt = { x: edit.x, y: edit.y - half };
                            endPt   = { x: edit.x, y: edit.y + half };
                        } else {
                            startPt = { x: edit.x - half, y: edit.y };
                            endPt   = { x: edit.x + half, y: edit.y };
                        }
                    }
                    if (startPt && endPt) {
                        // Build the same object shape createUnboundLink()
                        // produces so the rest of the app (hit-testing,
                        // BUL merging, style picker, save/load) treats
                        // it identically to a user-drawn UL.
                        var nextId = 'link_' + (ed.linkIdCounter != null ? ed.linkIdCounter++ : Date.now());
                        ul = {
                            id: nextId,
                            type: 'unbound',
                            originType: 'UL',
                            createdAt: Date.now(),
                            _createdAt: Date.now(),
                            device1: null,
                            device2: null,
                            color: (edit.color && String(edit.color)) || ed.defaultLinkColor
                                   || ((ed.darkMode) ? '#ffffff' : '#666666'),
                            start: startPt,
                            end: endPt,
                            connectedStart: null,
                            connectedEnd: null,
                            style: (edit.style && String(edit.style)) || ed.linkStyle || 'solid',
                        };
                        if (edit.label && typeof edit.label === 'string') {
                            ul.label = edit.label.trim();
                        }
                        if (edit.linkType && typeof edit.linkType === 'string') {
                            ul.linkType = edit.linkType.trim().toLowerCase();
                        }
                        if (typeof edit.width === 'number' && edit.width > 0) ul.width = edit.width;
                        (ed.objects || []).push(ul);
                    } else if (typeof ed.createUnboundLink === 'function') {
                        ed.createUnboundLink();
                        ul = ed.unboundLink || null;
                        if (ul) {
                            if (edit.label && typeof edit.label === 'string') ul.label = edit.label.trim();
                            if (edit.color && typeof edit.color === 'string') ul.color = edit.color;
                            if (edit.style && typeof edit.style === 'string') ul.style = edit.style;
                            if (typeof edit.width === 'number' && edit.width > 0) ul.width = edit.width;
                            if (edit.linkType && typeof edit.linkType === 'string') {
                                ul.linkType = edit.linkType.trim().toLowerCase();
                            }
                        }
                    } else {
                        warnings.push('edit[' + idx + '] add_unbound_link: editor.createUnboundLink() unavailable');
                        return;
                    }
                    counts.added_links += 1;
                } else if (op === 'add_text') {
                    var txtContent = String(edit.text || '').trim();
                    if (!txtContent) {
                        warnings.push('edit[' + idx + '] add_text: empty text');
                        return;
                    }
                    var tx = (typeof edit.x === 'number') ? edit.x : (_AI_LAYOUT.originX - 120);
                    var ty = (typeof edit.y === 'number') ? edit.y : (_AI_LAYOUT.originY - 80);
                    if (typeof ed.createText === 'function') {
                        var obj = ed.createText(tx, ty);
                        if (obj) {
                            obj.text = txtContent;
                            if (typeof edit.fontSize === 'number' && edit.fontSize > 0) obj.fontSize = edit.fontSize;
                            if (typeof edit.color === 'string' && edit.color) obj.color = edit.color;
                            if (typeof edit.showBackground === 'boolean') obj.showBackground = edit.showBackground;
                            if (typeof edit.backgroundColor === 'string' && edit.backgroundColor) {
                                obj.backgroundColor = edit.backgroundColor;
                                obj.bgColor = edit.backgroundColor; // mirror legacy alias
                            }
                            if (typeof edit.backgroundOpacity === 'number') {
                                // Accept 0..1 (preferred) or 0..100.
                                obj.backgroundOpacity = edit.backgroundOpacity > 1
                                    ? Math.max(0, Math.min(1, edit.backgroundOpacity / 100))
                                    : Math.max(0, Math.min(1, edit.backgroundOpacity));
                            }
                            if (typeof edit.backgroundPadding === 'number' && edit.backgroundPadding >= 0) {
                                obj.backgroundPadding = edit.backgroundPadding;
                            }
                            if (typeof edit.showBorder === 'boolean') obj.showBorder = edit.showBorder;
                            if (typeof edit.borderColor === 'string' && edit.borderColor) obj.borderColor = edit.borderColor;
                            if (typeof edit.borderWidth === 'number' && edit.borderWidth >= 0) obj.borderWidth = edit.borderWidth;
                            (ed.objects || []).push(obj);
                            counts.added_texts += 1;
                        } else {
                            warnings.push('edit[' + idx + '] add_text: createText returned null');
                        }
                    }
                } else if (op === 'add_shape') {
                    // 2026-04-24 -- drop a geometric shape (AS boundary,
                    // OSPF area, cloud, cross, checkmark, arrow, diamond,
                    // ...). Used by protocol blueprints to add grouping
                    // boxes and annotation markers that make the
                    // topology self-explanatory.
                    var shapeType = String(edit.shapeType || 'rectangle').trim().toLowerCase();
                    // Normalise legacy alias 'oval' -> 'ellipse' (the
                    // actual shape the canvas supports).
                    if (shapeType === 'oval') shapeType = 'ellipse';
                    var sx = (typeof edit.x === 'number') ? edit.x : _AI_LAYOUT.originX;
                    var sy = (typeof edit.y === 'number') ? edit.y : _AI_LAYOUT.originY;
                    if (typeof ed.createShape !== 'function') {
                        warnings.push('edit[' + idx + '] add_shape: editor.createShape() unavailable');
                        return;
                    }
                    var shp = ed.createShape(sx, sy, shapeType);
                    if (!shp) {
                        warnings.push('edit[' + idx + '] add_shape: createShape returned null');
                        return;
                    }
                    if (typeof edit.width === 'number' && edit.width > 0) shp.width = edit.width;
                    if (typeof edit.height === 'number' && edit.height > 0) shp.height = edit.height;
                    if (typeof edit.fillColor === 'string' && edit.fillColor) shp.fillColor = edit.fillColor;
                    if (typeof edit.fillOpacity === 'number') {
                        shp.fillOpacity = edit.fillOpacity > 1
                            ? Math.max(0, Math.min(1, edit.fillOpacity / 100))
                            : Math.max(0, Math.min(1, edit.fillOpacity));
                    }
                    if (typeof edit.fillEnabled === 'boolean') shp.fillEnabled = edit.fillEnabled;
                    if (typeof edit.strokeColor === 'string' && edit.strokeColor) shp.strokeColor = edit.strokeColor;
                    if (typeof edit.strokeWidth === 'number' && edit.strokeWidth >= 0) shp.strokeWidth = edit.strokeWidth;
                    if (typeof edit.strokeEnabled === 'boolean') shp.strokeEnabled = edit.strokeEnabled;
                    if (typeof edit.cornerRadius === 'number' && edit.cornerRadius >= 0) shp.cornerRadius = edit.cornerRadius;
                    if (typeof edit.rotation === 'number') shp.rotation = edit.rotation;
                    if (typeof edit.label === 'string' && edit.label.trim()) shp.label = edit.label.trim();
                    // 2026-04-26: container shapes drag inner objects together.
                    if (edit.containerMode === true) shp.containerMode = true;
                    counts.added_shapes = (counts.added_shapes || 0) + 1;
                } else if (op === 'remove') {
                    var targetId = edit.id || edit.label;
                    var t = _aiFindAny(ed, targetId);
                    if (!t) {
                        warnings.push('edit[' + idx + '] remove: "' + targetId + '" not found');
                        return;
                    }
                    // When deleting a device, also delete its links to
                    // avoid dangling references. We don't cascade for
                    // other object types (text/shape have no children).
                    var removed = [];
                    if (t.type === 'device') {
                        (ed.objects || []).forEach(function (o) {
                            if (o.type === 'link' && (o.device1 === t.id || o.device2 === t.id)) {
                                removed.push(o);
                            }
                        });
                    }
                    removed.push(t);
                    ed.objects = (ed.objects || []).filter(function (o) {
                        return removed.indexOf(o) === -1;
                    });
                    counts.removed += removed.length;
                } else if (op === 'move') {
                    var mt = _aiFindAny(ed, edit.id || edit.label);
                    if (!mt) {
                        warnings.push('edit[' + idx + '] move: "' + (edit.id || edit.label) + '" not found');
                        return;
                    }
                    if (typeof edit.x === 'number') mt.x = edit.x;
                    if (typeof edit.y === 'number') mt.y = edit.y;
                    counts.moved += 1;
                } else if (op === 'relabel') {
                    var rt = _aiFindAny(ed, edit.id);
                    if (!rt) {
                        warnings.push('edit[' + idx + '] relabel: "' + edit.id + '" not found');
                        return;
                    }
                    if (edit.label) rt.label = String(edit.label).trim();
                    counts.relabeled += 1;
                } else if (op === 'style') {
                    // 2026-04-24q -- change an existing object's visual
                    // attributes without moving or renaming it. Useful
                    // for prompts like "color all spines red" (one
                    // `style` per matching device) or "make Leaf-3
                    // bigger". Only fields actually present are
                    // applied; null/absent preserves the existing
                    // value so the LLM doesn't have to echo every
                    // property back.
                    var sty = _aiFindAny(ed, edit.id);
                    if (!sty) {
                        warnings.push('edit[' + idx + '] style: "' + edit.id + '" not found');
                        return;
                    }
                    var changed = false;
                    if (typeof edit.color === 'string' && edit.color) {
                        sty.color = edit.color; changed = true;
                    }
                    if (typeof edit.visualStyle === 'string' && edit.visualStyle) {
                        sty.visualStyle = edit.visualStyle; changed = true;
                    }
                    if (typeof edit.fontSize === 'number' && edit.fontSize > 0) {
                        sty.fontSize = edit.fontSize; changed = true;
                    }
                    // Link-specific style fields (applies when `sty` is a
                    // link or unbound link).
                    if (typeof edit.style === 'string' && edit.style) {
                        sty.style = edit.style; changed = true;
                    }
                    if (typeof edit.width === 'number' && edit.width > 0) {
                        sty.width = edit.width; changed = true;
                    }
                    if (typeof edit.linkType === 'string' && edit.linkType) {
                        sty.linkType = edit.linkType.trim().toLowerCase();
                        changed = true;
                    }
                    // Shape-specific style fields.
                    if (typeof edit.fillColor === 'string' && edit.fillColor) {
                        sty.fillColor = edit.fillColor; changed = true;
                    }
                    if (typeof edit.strokeColor === 'string' && edit.strokeColor) {
                        sty.strokeColor = edit.strokeColor; changed = true;
                    }
                    if (typeof edit.fillOpacity === 'number') {
                        sty.fillOpacity = edit.fillOpacity > 1
                            ? Math.max(0, Math.min(1, edit.fillOpacity / 100))
                            : Math.max(0, Math.min(1, edit.fillOpacity));
                        changed = true;
                    }
                    // 2026-04-26: containerMode toggle on shapes. Lets the
                    // AI promote an existing AS / area / tenant frame
                    // into a draggable container, or demote a shape that
                    // should NOT carry inner objects (cross / checkmark
                    // callouts). Ignored on non-shape objects.
                    if (sty.type === 'shape' && typeof edit.containerMode === 'boolean') {
                        sty.containerMode = edit.containerMode;
                        changed = true;
                    }
                    // Link-table metadata fields (2026-04-26): allow
                    // the topology generator + AI enrichment to drop
                    // interface names / VLAN / bridge-domain hints onto
                    // an EXISTING link so the link-table popup shows
                    // them. Only applied when sty is a link/unbound.
                    if (typeof edit.interface1 === 'string' && edit.interface1) {
                        sty.interface1 = edit.interface1.trim(); changed = true;
                    }
                    if (typeof edit.interface2 === 'string' && edit.interface2) {
                        sty.interface2 = edit.interface2.trim(); changed = true;
                    }
                    if (edit.vlan != null && String(edit.vlan).trim() !== '') {
                        sty.vlan = String(edit.vlan).trim(); changed = true;
                    }
                    if (typeof edit.bd === 'string' && edit.bd) {
                        sty.bd = edit.bd.trim(); changed = true;
                    }
                    if (edit.linkDetails && typeof edit.linkDetails === 'object') {
                        sty.linkDetails = Object.assign(
                            {}, sty.linkDetails || {}, edit.linkDetails
                        );
                        changed = true;
                    }
                    // Text-specific style fields.
                    if (typeof edit.showBackground === 'boolean') {
                        sty.showBackground = edit.showBackground; changed = true;
                    }
                    if (typeof edit.backgroundColor === 'string' && edit.backgroundColor) {
                        sty.backgroundColor = edit.backgroundColor;
                        sty.bgColor = edit.backgroundColor;
                        changed = true;
                    }
                    if (typeof edit.showBorder === 'boolean') {
                        sty.showBorder = edit.showBorder; changed = true;
                    }
                    if (typeof edit.borderColor === 'string' && edit.borderColor) {
                        sty.borderColor = edit.borderColor; changed = true;
                    }
                    if (typeof edit.borderWidth === 'number' && edit.borderWidth >= 0) {
                        sty.borderWidth = edit.borderWidth; changed = true;
                    }
                    if (changed) {
                        counts.relabeled += 1;  // reuse counter for "modified in-place" so the receipt reflects the change
                    } else {
                        warnings.push('edit[' + idx + '] style: no recognised style fields (color / visualStyle / fontSize / style / width / linkType / fillColor / strokeColor / background*)');
                    }
                } else if (op === 'select') {
                    // Select one or more objects by id-or-label so the
                    // user sees the highlighted cluster the assistant
                    // is talking about. Accepts either a single `id`
                    // or an array `ids`; no-op if nothing resolves.
                    var targets = [];
                    var selRaw = Array.isArray(edit.ids) ? edit.ids
                               : (edit.id != null ? [edit.id] : []);
                    for (var si2 = 0; si2 < selRaw.length; si2 += 1) {
                        var hit = _aiFindAny(ed, selRaw[si2]);
                        if (hit && targets.indexOf(hit) === -1) targets.push(hit);
                    }
                    if (targets.length === 0) {
                        warnings.push('edit[' + idx + '] select: no ids resolved ("' + (selRaw.join(',') || '<empty>') + '")');
                        return;
                    }
                    try {
                        if (typeof ed.clearSelection === 'function') ed.clearSelection();
                        else { ed.selectedObjects = []; ed.selectedObject = null; }
                        ed.selectedObjects = targets.slice();
                        ed.selectedObject = targets[0];
                        if (typeof ed.events === 'object' && ed.events && typeof ed.events.emit === 'function') {
                            ed.events.emit('selection:change', { objects: targets });
                        }
                    } catch (err0) {
                        warnings.push('edit[' + idx + '] select failed: ' + (err0 && err0.message || err0));
                    }
                } else if (op === 'create_domain') {
                    // 2026-04-24r -- create a brand-new topology domain
                    // in the user's workspace. Runs async (network
                    // POST) but the outer batch stays synchronous:
                    // we fire-and-forget here and post a system
                    // notice when the server response lands. That
                    // keeps the `receipt` counts honest for the
                    // synchronous ops that ran alongside.
                    //
                    // 2026-04-24s -- responsive UX upgrade: bump the
                    // pendingDomains counter so the receipt no longer
                    // shows "no changes applied" on a turn whose only
                    // visible action is the asynchronous domain
                    // creation. Also post an immediate "Creating domain
                    // X..." system bubble so the user sees something
                    // happen at click-time, not 300 ms later when the
                    // POST resolves. The follow-up "Created" / "Could
                    // not create" bubble swaps in via _replaceMessage,
                    // so the log doesn't grow with stale "Creating..."
                    // chatter.
                    var dName = (edit.label || edit.name || '').toString().trim();
                    if (!dName) {
                        warnings.push('edit[' + idx + '] create_domain: `label` (domain name) is required');
                        return;
                    }
                    // Reject reserved built-in names client-side too so
                    // the "Could not create domain ... reserved built-in"
                    // round-trip is replaced with an immediate inline
                    // warning + helpful suggestion. The server still
                    // enforces the same rule as a second line of
                    // defence (see BUILTIN_SECTIONS in serve.py).
                    if (_isReservedDomainName(dName)) {
                        warnings.push('edit[' + idx + '] create_domain: "' + dName
                            + '" is a reserved built-in name -- try "'
                            + dName + ' Lab" or a project-specific variant.');
                        return;
                    }
                    var dColor = (typeof edit.color === 'string' && edit.color) ? edit.color : '#8e5cff';
                    var dIcon  = (typeof edit.icon  === 'string' && edit.icon)  ? edit.icon  : 'sparkles';
                    counts.pending_domains = (counts.pending_domains || 0) + 1;
                    var creatingMsg = _appendSystem('Creating domain "' + dName + '"...', { pending: true });
                    (function (name, color, icon, pendingMsg) {
                        _authFetch('/api/sections', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ name: name, color: color, icon: icon }),
                        }).then(function (resp) {
                            return resp.json().then(function (json) { return [resp, json]; });
                        }).then(function (pair) {
                            var resp = pair[0], json = pair[1];
                            if (!resp.ok || !json || json.error) {
                                var msg = (json && json.error) || ('HTTP ' + resp.status);
                                if (pendingMsg && pendingMsg._id) {
                                    _replaceMessage(pendingMsg._id, {
                                        notice: true, error: true, pending: false,
                                        content: 'Could not create domain "' + name + '": ' + msg,
                                    });
                                } else {
                                    _appendSystem('Could not create domain "' + name + '": ' + msg);
                                }
                                return;
                            }
                            // Refresh the Topologies dropdown cache so
                            // the new domain row shows up immediately,
                            // and nudge any open dropdown to re-render.
                            try {
                                var edRef = _editor();
                                if (edRef && typeof edRef.loadCustomSections === 'function') {
                                    edRef.loadCustomSections();
                                }
                            } catch (_) {}
                            if (pendingMsg && pendingMsg._id) {
                                _replaceMessage(pendingMsg._id, {
                                    notice: true, pending: false,
                                    content: 'Created domain "' + name + '" -- it\'s now in your Topologies dropdown.',
                                });
                            } else {
                                _appendSystem('Created domain "' + name + '" -- it\'s now in your Topologies dropdown.');
                            }
                        }).catch(function (err) {
                            var emsg = err && err.message ? err.message : err;
                            if (pendingMsg && pendingMsg._id) {
                                _replaceMessage(pendingMsg._id, {
                                    notice: true, error: true, pending: false,
                                    content: 'Could not create domain "' + name + '": ' + emsg,
                                });
                            } else {
                                _appendSystem('Could not create domain "' + name + '": ' + emsg);
                            }
                        });
                    })(dName, dColor, dIcon, creatingMsg);
                } else if (op === 'zoom_to') {
                    // Pan + zoom the canvas to a single object
                    // (`id`), a world rect (`x`+`y`+`w`+`h`), or
                    // nothing at all (fit-to-all). Uses the editor's
                    // own centre helpers when present so the motion
                    // matches the rest of the app; falls back to
                    // direct zoom/pan assignment.
                    var didZoom = false;
                    try {
                        if (edit.id) {
                            var zt = _aiFindAny(ed, edit.id);
                            if (!zt) {
                                warnings.push('edit[' + idx + '] zoom_to: "' + edit.id + '" not found');
                                return;
                            }
                            if (typeof ed.centerOnObject === 'function') {
                                ed.centerOnObject(zt); didZoom = true;
                            } else if (typeof ed.panOffset === 'object' && typeof ed.zoom === 'number'
                                    && typeof zt.x === 'number' && typeof zt.y === 'number') {
                                var z1 = Math.min(1.5, Math.max(0.5, ed.zoom || 1));
                                ed.zoom = z1;
                                ed.panOffset.x = (ed.canvasW || 800) / 2 - zt.x * z1;
                                ed.panOffset.y = (ed.canvasH || 600) / 2 - zt.y * z1;
                                didZoom = true;
                            }
                        } else if (typeof edit.x === 'number' && typeof edit.y === 'number'
                                && typeof edit.w === 'number' && typeof edit.h === 'number') {
                            // Fit a rect: pick a zoom that makes the
                            // rect occupy ~80 % of the viewport.
                            var cw1 = ed.canvasW || 800;
                            var ch1 = ed.canvasH || 600;
                            var fitZ = Math.min(
                                (cw1 * 0.8) / Math.max(1, edit.w),
                                (ch1 * 0.8) / Math.max(1, edit.h)
                            );
                            fitZ = Math.min(2.0, Math.max(0.1, fitZ));
                            ed.zoom = fitZ;
                            ed.panOffset.x = cw1 / 2 - (edit.x + edit.w / 2) * fitZ;
                            ed.panOffset.y = ch1 / 2 - (edit.y + edit.h / 2) * fitZ;
                            didZoom = true;
                        } else {
                            if (typeof ed.centerOnDevices === 'function') {
                                ed.centerOnDevices(); didZoom = true;
                            } else if (typeof ed.fitAll === 'function') {
                                ed.fitAll(); didZoom = true;
                            }
                        }
                    } catch (err1) {
                        warnings.push('edit[' + idx + '] zoom_to failed: ' + (err1 && err1.message || err1));
                    }
                    if (didZoom) {
                        counts.moved += 1;  // re-use counter so the receipt shows a camera action happened
                    }
                } else {
                    warnings.push('edit[' + idx + '] unknown op: ' + op);
                }
            } catch (e) {
                warnings.push('edit[' + idx + '] failed: ' + (e && e.message ? e.message : String(e)));
            }
        });
        // Post-batch: repaint, auto-save, re-centre if we added
        // anything that might be off-screen.
        try { if (typeof ed.draw === 'function') ed.draw(); } catch (_) {}
        try { if (typeof ed.autoSave === 'function') ed.autoSave(); } catch (_) {}
        if (counts.added_devices > 0 && typeof ed.centerOnDevices === 'function') {
            // Only auto-centre when the user would benefit -- i.e. we
            // added fresh devices. Centre after 1 frame so the final
            // layout is stable.
            setTimeout(function () { try { ed.centerOnDevices(); } catch (_) {} }, 16);
        }
        // 2026-04-24s -- a turn that only fires create_domain (async)
        // would have shown the generic "Canvas updated" toast even
        // though no synchronous canvas mutation happened. When the
        // ONLY work is pending domain creation, swap to a more honest
        // "Creating domain..." toast so the user's click feedback
        // matches the system bubble that just appeared above.
        var didSyncWork = (counts.added_devices + counts.added_links + counts.added_texts
            + counts.removed + counts.moved + counts.relabeled) > 0;
        var fallbackToast;
        if (didSyncWork) {
            fallbackToast = 'Canvas updated';
        } else if (counts.pending_domains) {
            fallbackToast = counts.pending_domains === 1
                ? 'Creating domain...' : 'Creating ' + counts.pending_domains + ' domains...';
        } else {
            fallbackToast = 'No changes applied';
        }
        _toast((tool.summary || fallbackToast), didSyncWork ? 'success' : 'info');
        return { counts: counts, warnings: warnings };
    }

    // Resolve the chosen domain from the pending-placement card, then
    // save the topology there and load it onto the canvas. We expect the
    // clicked button's card to contain the radios + inputs rendered by
    // _renderPendingPlacementCard.
    async function _placePendingTopology(clickedBtn, msg) {
        if (!msg || !msg.tool || !msg.tool.topology) return;
        var card = clickedBtn.closest('.ai-tool-card');
        if (!card) {
            _toast('Placement controls missing - please retry', 'error');
            return;
        }
        var modeRadio = card.querySelector('input[type="radio"]:checked');
        var mode = modeRadio ? modeRadio.value : 'existing';
        var existingSel = card.querySelector('[data-role="placement-existing"]');
        var newInput = card.querySelector('[data-role="placement-new-name"]');
        var topoInput = card.querySelector('[data-role="placement-topo-name"]');
        var topoName = topoInput ? (topoInput.value || '').trim() : '';
        if (!topoName) topoName = msg.tool.display_name || msg.tool.suggested_name || 'ai-topology';
        var topologyCounts = _topologyCounts(msg.tool.topology);
        if (topologyCounts.devices < 2 || topologyCounts.links < 1) {
            _toast('AI topology is too small to place. Regenerate it with at least 2 connected devices.', 'warning');
            return;
        }

        // Lock the card while we're in flight so double-clicks don't
        // create two copies of the topology under the same name.
        // 2026-04-24s -- also lock the secondary inputs so the user
        // can't change their mind mid-flight (the in-flight state was
        // already committed when the first POST returned). The
        // _unlockCard closure flips the lock back when we abort early
        // OR throw -- keeping the success path's `_removeMessage`
        // call as the only "card disappears" trigger.
        var primaryBtn = card.querySelector('[data-tool-action="place"]');
        if (primaryBtn) {
            primaryBtn.disabled = true;
            primaryBtn.textContent = 'Placing...';
            primaryBtn.classList.add('ai-btn--working');
        }
        var lockEls = card.querySelectorAll('input, select, button:not([data-tool-action="place"])');
        lockEls.forEach(function (el) { el.disabled = true; });
        function _unlockCard() {
            if (primaryBtn) {
                primaryBtn.disabled = false;
                primaryBtn.textContent = 'Place on canvas';
                primaryBtn.classList.remove('ai-btn--working');
                primaryBtn.title = '';
            }
            lockEls.forEach(function (el) { el.disabled = false; });
            // Also re-disable the existing-domain controls when the
            // workspace has no domains yet -- they were rendered with
            // the `disabled` attribute on purpose.
            var existsEl = card.querySelector('[data-role="placement-existing"]');
            if (existsEl && existsEl.options && existsEl.options.length === 0) existsEl.disabled = true;
        }

        try {
            var sectionId = null;
            var sectionName = '';
            var sectionColor = '';
            if (mode === 'new') {
                var newName = newInput ? (newInput.value || '').trim() : '';
                if (!newName) {
                    _toast('Enter a name for the new domain', 'warning');
                    _unlockCard();
                    if (newInput) newInput.focus();
                    return;
                }
                if (_isReservedDomainName(newName)) {
                    _toast('"' + newName + '" is a reserved built-in name -- pick another', 'warning');
                    _unlockCard();
                    if (newInput) { newInput.focus(); newInput.select(); }
                    return;
                }
                // 2026-04-24s -- honour target_domain_new.color / .icon
                // hints from the model so "make it blue" lands blue on
                // first click. Falls back to the AI-purple default when
                // the model didn't emit a hint.
                var hintObj = (msg.tool && msg.tool.target_domain_new) || {};
                var wantedColor = (typeof hintObj.color === 'string' && hintObj.color.trim())
                    ? hintObj.color.trim() : '#8e5cff';
                var wantedIcon = (typeof hintObj.icon === 'string' && hintObj.icon.trim())
                    ? hintObj.icon.trim() : 'sparkles';
                // Step the primary button text so the user can SEE the
                // multi-stage operation in flight (was a flat "Placing..."
                // for the whole 1-2 s + 2 round-trips, which read as
                // hung). Each branch updates _placeStep so the chain
                // below shows "Creating domain X..." -> "Saving topology
                // ..." -> "Loading on canvas..." in order.
                _placeStep(primaryBtn, 'Creating domain ' + newName + '...');
                // Create the domain first. The backend assigns sec_<ts>
                // ids and rejects built-in name collisions ("Bugs" / "AI"
                // / "DNAAS") with a 400 JSON error -- surface that as a
                // toast so the user can rename and retry.
                var createResp = await _authFetch('/api/sections', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: newName,
                        color: wantedColor,
                        icon: wantedIcon,
                    }),
                });
                var createJson = null;
                try { createJson = await createResp.json(); } catch (_) {}
                if (!createResp.ok || !createJson || createJson.error) {
                    var errMsg = (createJson && createJson.error) || ('HTTP ' + createResp.status);
                    _toast('Could not create domain: ' + errMsg, 'error');
                    _unlockCard();
                    return;
                }
                var sec = (createJson && createJson.section) || {};
                sectionId = sec.id || null;
                sectionName = sec.name || newName;
                sectionColor = sec.color || '#8e5cff';
            } else {
                if (!existingSel || !existingSel.value) {
                    _toast('Pick a domain from the list', 'warning');
                    _unlockCard();
                    return;
                }
                sectionId = existingSel.value;
                var chosenOpt = existingSel.options[existingSel.selectedIndex];
                sectionName = chosenOpt ? chosenOpt.textContent : sectionId;
                // Look up the colour from the editor's cache so we can
                // paint the indicator with the same accent that the
                // dropdown row uses. Missing cache is non-fatal.
                try {
                    var ed0 = _editor();
                    var cached = (ed0 && (ed0._customSections || []).find(function (s) { return s && s.id === sectionId; }));
                    if (cached) sectionColor = cached.color || '';
                } catch (_) {}
            }
            var uniqueTopoName = await _ensureUniqueTopologyName(sectionId, topoName);
            if (uniqueTopoName !== topoName) {
                topoName = uniqueTopoName;
                if (topoInput) topoInput.value = topoName;
            }
            // Persist the topology under the chosen section. We send the
            // raw topology payload from the tool call; the backend
            // sanitises filename but NOT topology contents -- which is
            // fine because normalize_topology_payload on the server side
            // already validated the schema.
            _placeStep(primaryBtn, 'Saving topology...');
            var saveResp = await _authFetch(
                '/api/sections/' + encodeURIComponent(sectionId) + '/save',
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: topoName,
                        topology: msg.tool.topology,
                        avoid_duplicate: true,
                    }),
                }
            );
            var saveJson = null;
            try { saveJson = await saveResp.json(); } catch (_) {}
            if (!saveResp.ok || !saveJson || saveJson.error) {
                var saveErr = (saveJson && saveJson.error) || ('HTTP ' + saveResp.status);
                _toast('Save failed: ' + saveErr, 'error');
                _unlockCard();
                return;
            }
            var filename = saveJson.filename;
            topoName = (saveJson && saveJson.name) || topoName;
            // Reuse the existing loader so the canvas centering, indicator
            // update, and section-dropdown refresh logic all run through
            // one code path. Stash the resolved id+filename on the tool so
            // future interactions (e.g. a second click) behave correctly.
            msg.tool.section_id = sectionId;
            msg.tool.filename = filename;
            msg.tool.display_name = topoName;
            msg.tool.status = 'saved';
            _placeStep(primaryBtn, 'Loading on canvas...');
            await _loadSavedTopology({
                section_id: sectionId,
                filename: filename,
                display_name: topoName,
                // Hand the real domain name + colour to the loader so
                // the bottom-left indicator no longer hard-codes "AI".
                domain_name: sectionName,
                domain_color: sectionColor,
                // Suppress the loader's default toast -- we pop a more
                // specific "Placed X in Y" one right after.
                silent_toast: true,
            });
            // Remove the picker card so the log reflects the final state
            // without the user needing to dismiss manually.
            _removeMessage(msg._id);
            _toast('Placed "' + topoName + '" in ' + sectionName, 'success');
            _appendSystem('Placed "' + topoName + '" in domain "' + sectionName + '" -- centred on the canvas.');
        } catch (e) {
            _toast('Placement failed: ' + (e && e.message ? e.message : e), 'error');
            _unlockCard();
        }
    }

    // --------------------------------------------------------------
    //  Multi-step button text helper (placement + create_domain async).
    //
    //  Browser layout passes for inline button text changes are CHEAP
    //  (no reflow above the card), so we can swap label/spinner state
    //  on every async step without flicker. Adds the `--working` mod
    //  class so CSS can paint a subtle spinner / pulsing background.
    //  Falls back gracefully when `btn` is null (caller may have
    //  removed the card before the next step landed).
    // --------------------------------------------------------------
    function _placeStep(btn, label) {
        if (!btn) return;
        btn.disabled = true;
        btn.textContent = label;
        btn.classList.add('ai-btn--working');
    }

    async function _loadSavedTopology(tool) {
        if (!tool || !tool.section_id || !tool.filename) return;
        try {
            var resp = await _authFetch(
                '/api/sections/' + encodeURIComponent(tool.section_id)
                + '/topologies/' + encodeURIComponent(tool.filename)
            );
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            var data = await resp.json();
            // Resolve display metadata for the bottom-left indicator.
            // Callers that know the target domain pass `domain_name` /
            // `domain_color` directly (the new placement flow does);
            // older callers still trigger the legacy lookup by id,
            // falling back to the now-deprecated hard-coded "AI" label
            // so existing tool cards keep rendering something sane.
            var resolvedDomainName = tool.domain_name || '';
            var resolvedDomainColor = tool.domain_color || '';
            if (!resolvedDomainName || !resolvedDomainColor) {
                try {
                    var edLookup = _editor();
                    var cached = edLookup && (edLookup._customSections || [])
                        .find(function (s) { return s && s.id === tool.section_id; });
                    if (cached) {
                        resolvedDomainName = resolvedDomainName || cached.name || '';
                        resolvedDomainColor = resolvedDomainColor || cached.color || '';
                    }
                } catch (_) { /* cache miss ok */ }
            }
            // Legacy __ai files still drop through the old label so
            // users looking at historical cards don't see "undefined".
            if (!resolvedDomainName && tool.section_id === '__ai') resolvedDomainName = 'AI';
            if (!resolvedDomainColor && tool.section_id === '__ai') resolvedDomainColor = '#8e5cff';
            // The saved topology may already carry the tool's display
            // name in metadata; surface it back into data.metadata so
            // bottom-left indicator, event bus, and save-as flows all
            // see the same canonical name. Keep existing fields.
            try {
                data.metadata = data.metadata || {};
                if (!data.metadata.name && tool.display_name) {
                    data.metadata.name = tool.display_name;
                }
                // Tag this load so other modules can spot an AI-origin
                // canvas (future: badge in the domain indicator).
                data.metadata.source = data.metadata.source || 'ai-assistant';
            } catch (_) { /* non-fatal */ }

            var ed = _editor();
            function _loadAndCentre(editor) {
                if (!editor || typeof editor.loadTopologyFromData !== 'function') return;
                editor.loadTopologyFromData(data, { domain: resolvedDomainName || 'AI' });
                // Centre + fit-to-view the new topology. Without this the
                // user's viewport stays wherever the last canvas was
                // panned / zoomed, and a freshly-loaded AI topology can
                // land entirely off-screen -- which feels exactly like
                // "the topology didn't load" from the user's chair.
                // centerOnDevices() is a no-op when the topology has no
                // devices, so it's always safe to call.
                if (typeof editor.centerOnDevices === 'function') {
                    try { editor.centerOnDevices(); } catch (_) {}
                }
            }
            if (ed) {
                _loadAndCentre(ed);
            } else {
                setTimeout(function () { _loadAndCentre(_editor()); }, 200);
            }
            if (window.FileOps && typeof window.FileOps.updateTopologyIndicator === 'function') {
                window.FileOps.updateTopologyIndicator(
                    tool.display_name || tool.filename.replace(/\.json$/, ''),
                    resolvedDomainName || null,
                    resolvedDomainColor || null,
                    tool.section_id,
                );
            }
            // Full section + dropdown refresh so the new AI topology
            // appears immediately in the Topologies menu without needing
            // a browser reload. `loadCustomSections()` (preferred) hits
            // the domains API and rebuilds `_customSections` with the
            // accurate `topology_count` per domain; the older
            // `/api/sections` path is a fallback for older bundles.
            try {
                if (window.FileOps && typeof window.FileOps.loadCustomSections === 'function' && ed) {
                    // Returns a Promise that resolves after the dropdown
                    // has been re-rendered with fresh topology_count.
                    await window.FileOps.loadCustomSections(ed);
                } else if (window.FileOps && typeof window.FileOps._renderCustomSectionsInDropdown === 'function' && ed) {
                    var sectionsResp = await _authFetch('/api/sections');
                    var sectionsJson = await sectionsResp.json();
                    if (sectionsJson && sectionsJson.sections) {
                        ed._customSections = sectionsJson.sections;
                        window.FileOps._renderCustomSectionsInDropdown(ed);
                    }
                }
            } catch (_) { /* non-fatal */ }
            // Skip the generic "Loaded AI topology" toast when the caller
            // already pops a more specific one (the placement flow shows
            // "Placed X in <domain>"); `silent_toast: true` is our opt-in
            // signal. Keep the toast for the legacy save-load button so
            // that path still feels responsive.
            if (!tool.silent_toast) {
                _toast('Loaded AI topology: ' + (tool.display_name || tool.filename), 'success');
            }
        } catch (e) {
            _toast('Failed to load topology: ' + (e && e.message ? e.message : e), 'error');
        }
    }

    // --------------------------------------------------------------
    //   Canvas snapshot (sent to the server on every turn)
    // --------------------------------------------------------------
    //
    // The server truncates anything over ~6 KB anyway, so we send a
    // compact, already-summarized view. Each device exposes id, name,
    // type, dnos, vrf count; each link exposes endpoints and capacity.
    // Full object arrays (with coordinates etc.) stay client-side.
    function _collectCanvasSnapshot() {
        try {
            var ed = _editor();
            if (!ed) return {};
            var objs = (ed.objects || ed._objects || []);
            var devices = [], links = [], shapes = 0, texts = 0;
            // Label -> id lookup for human-readable link endpoints.
            // Without this the LLM sees `{from: 3, to: 7}` and has to
            // cross-reference ids by hand; with it we can also echo
            // human labels.
            var idToLabel = {};
            for (var i0 = 0; i0 < objs.length; i0 += 1) {
                var oo = objs[i0] || {};
                if (oo && oo.id != null && (oo.name || oo.label)) {
                    idToLabel[String(oo.id)] = oo.name || oo.label;
                }
            }
            for (var i = 0; i < objs.length; i += 1) {
                var o = objs[i] || {};
                var t = (o.type || '').toLowerCase();
                if (t === 'device' || t === 'router' || t === 'switch' || t === 'node') {
                    // 2026-04-24q -- include spatial info (x/y) and style
                    // so the LLM has real spatial awareness. Without this
                    // the model can only reason about labels/roles and
                    // cannot honour prompts like "between spine-1 and
                    // spine-2", "200 px below the router", "top-left
                    // corner", etc. Coordinates are in WORLD space
                    // (i.e. the same space the LLM emits via add_device
                    // x/y), so round-tripping is loss-less.
                    devices.push({
                        id: o.id || o.name || null,
                        name: o.name || o.label || null,
                        dnos: o.dnos || o.os || null,
                        role: o.role || null,
                        vrfs: Array.isArray(o.vrfs) ? o.vrfs.length : 0,
                        x: (typeof o.x === 'number') ? Math.round(o.x) : null,
                        y: (typeof o.y === 'number') ? Math.round(o.y) : null,
                        color: o.color || null,
                        visualStyle: o.visualStyle || null,
                    });
                } else if (t === 'link' || t === 'connection' || t === 'edge') {
                    var fromId = o.from || (o.endpoints && o.endpoints[0]) || null;
                    var toId   = o.to   || (o.endpoints && o.endpoints[1]) || null;
                    // Prefer the device1/device2 refs which may be
                    // object pointers on the live canvas -- flatten
                    // them to ids. Labels are echoed alongside for
                    // prompt-friendly natural-language matching.
                    if (!fromId && o.device1 && typeof o.device1 === 'object') fromId = o.device1.id;
                    if (!toId   && o.device2 && typeof o.device2 === 'object') toId   = o.device2.id;
                    links.push({
                        from: fromId,
                        to: toId,
                        from_label: fromId != null ? (idToLabel[String(fromId)] || null) : null,
                        to_label:   toId   != null ? (idToLabel[String(toId)]   || null) : null,
                        linkType: o.linkType || null,
                        speed: o.speed || o.capacity || null,
                    });
                } else if (t === 'shape' || t === 'rect' || t === 'circle') {
                    shapes += 1;
                } else if (t === 'text') {
                    texts += 1;
                }
            }
            var topologyName = null, domainName = null, domainId = null;
            try {
                topologyName = (ed.currentTopology && (ed.currentTopology.name || ed.currentTopology.id)) || null;
                domainName = (ed._currentSectionName) || null;
                domainId = (ed._currentSectionId) || null;
            } catch (_) {}
            // Viewport block: what the user can currently see on screen
            // in world coords, plus zoom + total canvas size. The LLM
            // needs this to map natural-language regions ("top-left",
            // "centre", "off-screen to the right") to coordinates.
            var viewport = null;
            try {
                var cw = (typeof ed.canvasW === 'number') ? ed.canvasW
                       : (ed.canvas && ed.canvas.width && ed.dpr ? ed.canvas.width / ed.dpr : 0);
                var ch = (typeof ed.canvasH === 'number') ? ed.canvasH
                       : (ed.canvas && ed.canvas.height && ed.dpr ? ed.canvas.height / ed.dpr : 0);
                var zoom = (typeof ed.zoom === 'number') ? ed.zoom : 1;
                var panX = (ed.panOffset && typeof ed.panOffset.x === 'number') ? ed.panOffset.x : 0;
                var panY = (ed.panOffset && typeof ed.panOffset.y === 'number') ? ed.panOffset.y : 0;
                // World-space rectangle currently visible on screen.
                var visX = -panX / zoom;
                var visY = -panY / zoom;
                var visW = cw / zoom;
                var visH = ch / zoom;
                viewport = {
                    zoom: Math.round(zoom * 100) / 100,
                    pan: { x: Math.round(panX), y: Math.round(panY) },
                    canvas_px: { w: Math.round(cw), h: Math.round(ch) },
                    visible_world: {
                        x: Math.round(visX), y: Math.round(visY),
                        w: Math.round(visW), h: Math.round(visH),
                        cx: Math.round(visX + visW / 2),
                        cy: Math.round(visY + visH / 2),
                    },
                };
            } catch (_) {}
            // Selection: labels of currently-selected objects so the
            // LLM can honour "move these...", "color the selected
            // ones red", etc. without re-listing them.
            var selection = [];
            try {
                var sels = ed.selectedObjects || (ed.selectedObject ? [ed.selectedObject] : []);
                for (var si = 0; si < sels.length && si < 12; si += 1) {
                    var so = sels[si] || {};
                    selection.push(so.label || so.name || so.id || null);
                }
            } catch (_) {}
            return {
                topology: { name: topologyName, domain: domainName, section_id: domainId },
                counts: { devices: devices.length, links: links.length, shapes: shapes, texts: texts },
                viewport: viewport,
                selection: selection,
                devices: devices.slice(0, 64),
                links: links.slice(0, 96),
            };
        } catch (_) {
            return {};
        }
    }

    // --------------------------------------------------------------
    //   Global init
    // --------------------------------------------------------------
    function _installKeyboardShortcut() {
        // Non-text <input> types (color swatches, checkboxes, radios,
        // sliders, buttons) should NOT block the shortcut -- that's the
        // same logic topology-keyboard.js uses for 'd', 'b', 't', etc.
        var NON_TEXT_INPUT_TYPES = {
            color: 1, checkbox: 1, radio: 1, range: 1,
            button: 1, submit: 1, reset: 1,
        };
        function _isTypingContext(target) {
            if (!target) return false;
            var tag = target.tagName;
            if (tag === 'TEXTAREA' || tag === 'SELECT') return true;
            if (tag === 'INPUT') {
                var typ = (target.type || 'text').toLowerCase();
                return !NON_TEXT_INPUT_TYPES[typ];
            }
            if (target.isContentEditable) return true;
            return false;
        }
        document.addEventListener('keydown', function (e) {
            // Bare "A" toggles the drawer when the user is NOT typing
            // into a field. We explicitly reject Ctrl/Cmd/Alt/Shift
            // modifiers so we don't eat Ctrl+A (select all), Cmd+A, or
            // canvas-reserved Alt combinations. Uppercase 'A' on macOS
            // comes through with Shift held, so requiring no shift is
            // intentional -- caps-lock still works because e.key is 'A'
            // but no modifiers are set.
            var isA = (e.key === 'a' || e.key === 'A');
            var noModifiers = !e.ctrlKey && !e.metaKey && !e.altKey && !e.shiftKey;
            // Leading-edge guard: if the Bugs or Share modal is open, or
            // any generic modal is open, refuse to capture 'A' so normal
            // typing still works in those dialogs.
            var modalOpen = !!document.querySelector(
                '.bugs-modal.show, .share-modal.show, .dialog-overlay.show, .modal-overlay.show'
            );
            if (isA && noModifiers && !_isTypingContext(e.target) && !modalOpen) {
                e.preventDefault();
                toggle();
                return;
            }
            // Escape closes the drawer only when focus is inside the
            // drawer, so typing Escape in a wizard modal doesn't also
            // kill the AI drawer unexpectedly.
            if (e.key === 'Escape' && _drawerEl && _drawerEl.classList.contains('open')) {
                if (_drawerEl.contains(document.activeElement)) {
                    e.preventDefault();
                    close();
                }
            }
        });
    }

    function _onAuthenticated() {
        // Fired after the JWT is set. Probe immediately so the launcher
        // badge reflects real state and silently restore the last open
        // position.
        _probeAiConfig().then(function () {
            var shouldOpen = _lsGet(LS.open, '0') === '1';
            if (shouldOpen) open();
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        _initLauncher();
        _installKeyboardShortcut();
    });

    // The auth module dispatches this once the user logs in. If auth is
    // instantaneous (token in localStorage), the listener fires during
    // boot; otherwise it fires after the login form is submitted.
    document.addEventListener('tp:authenticated', _onAuthenticated);
    // Fallback: if the auth module never dispatches, still try to probe
    // after a short delay so the launcher reflects reality.
    setTimeout(function () {
        if (_aiConfig.configured === null) _probeAiConfig();
    }, 1500);

    window.TopologyAI = {
        open: open,
        close: close,
        toggle: toggle,
        // Used by topology-bugs.js and topology-share.js to enforce the
        // "only one side-panel at a time" rule. Safe if called before
        // the drawer has ever been built (just flips the launcher style).
        closeFromMutex: close,
        isOpen: _isOpen,
        // 2026-04-26 -- exposed so topology-generator.js can ship the
        // exact same canvas snapshot to /api/ai/chat for AI enrichment.
        // Falling back to a server-side snapshot would lose viewport
        // info (where the user is currently looking) and the LLM
        // would emit coords outside the visible rect.
        collectCanvasSnapshot: _collectCanvasSnapshot,
        // 2026-04-26 -- exposed so topology-generator.js can apply an
        // apply_canvas_edits tool batch through the same code path the
        // chat drawer uses (single saveState -> one undo, summary toast,
        // smart auto-placement). The argument shape matches the
        // tool-call envelope (`{ summary, edits }`).
        applyCanvasEdits: _applyCanvasEdits,
    };

    // Join the global single-overlay mutex. markOpen('ai') is called
    // from open(); this registration exposes our close() so OTHER
    // panels can auto-close the AI drawer when they open.
    if (window.TopoPanelMutex) {
        window.TopoPanelMutex.register('ai', {
            close: close,
            isOpen: _isOpen,
        });
    }
})();
