/**
 * topology-cursor-install.js -- Connect Cursor modal for Topology MCP setup.
 */
(function () {
    'use strict';

    var API = '/api/integration/cursor';
    var _modal = null;
    var _prompt = '';

    function _authFetch(url, opts) {
        if (window.TopologyAuth && window.TopologyAuth.authFetch) {
            return window.TopologyAuth.authFetch(url, opts || {});
        }
        return fetch(url, opts || {});
    }

    function _esc(s) {
        if (s === null || s === undefined) return '';
        return String(s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    function _toast(msg, type) {
        try {
            var editor = window.topologyEditor || window.editor;
            if (editor && typeof editor.showToast === 'function') {
                editor.showToast(msg, type || 'info');
            }
        } catch (_) {}
    }

    function _status(text) {
        var node = _modal && _modal.querySelector('.cursor-install-status');
        if (node) node.textContent = text || '';
    }

    async function _copy(text) {
        if (!text) return;
        await navigator.clipboard.writeText(text);
        _status('Copied to clipboard.');
        _toast('Copied Cursor install prompt', 'success');
    }

    async function _issueToken() {
        _status('Generating token...');
        var resp = await _authFetch(API + '/token', { method: 'POST' });
        var data = await resp.json();
        if (!resp.ok || !data.ok) {
            throw new Error(data.detail || data.error || 'Token generation failed');
        }
        _prompt = data.prompt || '';
        _renderPrompt();
        _status('Token ready. Paste the prompt into Cursor.');
    }

    async function _revokeToken() {
        _status('Revoking token...');
        var resp = await _authFetch(API + '/token', { method: 'DELETE' });
        var data = await resp.json().catch(function () { return {}; });
        if (!resp.ok || data.ok === false) {
            throw new Error(data.detail || data.error || 'Token revoke failed');
        }
        _prompt = '';
        _renderPrompt();
        _status('Token revoked. Generate a new one before installing again.');
    }

    function _renderPrompt() {
        var textarea = _modal && _modal.querySelector('.cursor-install-prompt');
        if (textarea) {
            textarea.value = _prompt || 'Click Generate / Rotate Token to build a fresh install prompt.';
        }
    }

    function _wire() {
        _modal.querySelector('[data-action="close"]').addEventListener('click', close);
        _modal.querySelector('[data-action="generate"]').addEventListener('click', function () {
            _issueToken().catch(function (err) { _status(err.message); });
        });
        _modal.querySelector('[data-action="copy"]').addEventListener('click', function () {
            _copy(_prompt).catch(function (err) { _status(err.message); });
        });
        _modal.querySelector('[data-action="revoke"]').addEventListener('click', function () {
            _revokeToken().catch(function (err) { _status(err.message); });
        });
        _modal.addEventListener('click', function (e) {
            if (e.target === _modal) close();
        });
    }

    function open() {
        if (_modal) {
            _modal.remove();
        }
        _modal = document.createElement('div');
        _modal.className = 'cursor-install-modal-backdrop';
        _modal.innerHTML = '' +
            '<section class="cursor-install-modal" role="dialog" aria-modal="true" aria-label="Connect Cursor">' +
            '  <header>' +
            '    <div><h2>Connect Cursor</h2><p style="margin:4px 0 0;font-size:12px;color:rgba(148,163,184,.9)">Install the per-user Topology MCP and skill for this account.</p></div>' +
            '    <button class="cursor-install-close" type="button" data-action="close" aria-label="Close">x</button>' +
            '  </header>' +
            '  <div class="cursor-install-body">' +
            '    <div class="cursor-install-panel">' +
            '      <div class="cursor-install-panel-title">What this installs</div>' +
            '      <p>A shared MCP endpoint plus a local Cursor skill. The token only resolves to your user, so tools can see and edit only your own domains plus resources explicitly shared with you.</p>' +
            '      <div class="cursor-install-actions">' +
            '        <button class="cursor-install-btn primary" type="button" data-action="generate">Generate / Rotate Token</button>' +
            '        <button class="cursor-install-btn" type="button" data-action="copy">Copy Install Prompt</button>' +
            '        <button class="cursor-install-btn danger" type="button" data-action="revoke">Revoke Token</button>' +
            '      </div>' +
            '    </div>' +
            '    <div class="cursor-install-panel">' +
            '      <div class="cursor-install-panel-title">Prompt for Cursor</div>' +
            '      <textarea class="cursor-install-prompt" readonly></textarea>' +
            '      <div class="cursor-install-status"></div>' +
            '    </div>' +
            '  </div>' +
            '</section>';
        document.body.appendChild(_modal);
        _wire();
        _renderPrompt();
    }

    function close() {
        if (_modal) {
            _modal.remove();
            _modal = null;
        }
    }

    function attachButton() {
        var existing = document.getElementById('btn-connect-cursor');
        if (existing) {
            existing.addEventListener('click', open);
            return;
        }
        var anchor = document.getElementById('btn-refresh-page');
        if (!anchor || !anchor.parentNode) return;
        var btn = document.createElement('button');
        btn.className = 'top-bar-btn';
        btn.id = 'btn-connect-cursor';
        btn.type = 'button';
        btn.setAttribute('data-tooltip', 'Connect Cursor to your topology workspace');
        btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M4 5h16v10H4z"/><path d="M8 19h8M12 15v4"/><path d="M8 9h8M8 12h5"/></svg><span class="status-text">Cursor</span>';
        btn.addEventListener('click', open);
        anchor.parentNode.insertBefore(btn, anchor);
    }

    window.TopologyCursorInstall = { open: open, close: close, attachButton: attachButton };
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', attachButton);
    } else {
        attachButton();
    }
})();

