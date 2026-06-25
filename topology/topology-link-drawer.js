/**
 * topology-link-drawer.js - Detachable Live Link Telemetry drawer.
 */

'use strict';

(function () {
    function ensureDrawer() {
        let drawer = document.getElementById('link-live-drawer');
        if (drawer) return drawer;
        drawer = document.createElement('div');
        drawer.id = 'link-live-drawer';
        drawer.className = 'link-live-drawer';
        drawer.innerHTML = `
            <div class="link-live-drawer-header">
                <div>
                    <div class="link-live-drawer-title">Live Link Telemetry</div>
                    <div id="link-live-drawer-subtitle" class="link-live-drawer-subtitle">No link selected</div>
                </div>
                <div class="link-live-drawer-actions">
                    <button id="link-live-drawer-refresh" type="button">Refresh</button>
                    <label><input id="link-live-drawer-auto" type="checkbox"> Auto</label>
                    <button id="link-live-drawer-close" type="button">Close</button>
                </div>
            </div>
            <div id="link-live-drawer-body" class="link-live-drawer-body">
                <div class="lt-live-empty">Select a link and click Refresh.</div>
            </div>
        `;
        document.body.appendChild(drawer);
        return drawer;
    }

    window.LinkLiveDrawer = {
        _editor: null,
        _link: null,

        show(editor, link, result) {
            this._editor = editor || this._editor || window.topologyEditor;
            this._link = link || this._link;
            this.hide();
            if (this._editor && this._link && typeof this._editor.showLinkDetails === 'function') {
                this._editor.showLinkDetails(this._link);
                const tabs = document.getElementById('lt-modal-tabs');
                if (tabs && typeof tabs._activate === 'function') {
                    tabs._activate('live');
                }
            }
        },

        hide() {
            const drawer = document.getElementById('link-live-drawer');
            if (drawer) drawer.classList.remove('open');
            if (this._link?.id) window.LinkTelemetry?.unsubscribeAutoRefresh(this._link.id);
        },

        refresh() {
            if (!this._editor || !this._link || !window.LinkTelemetry) return;
            const body = document.getElementById('link-live-drawer-body');
            if (body) body.innerHTML = '<div class="lt-live-empty">Refreshing live telemetry...</div>';
            window.LinkTelemetry.refreshLink(this._editor, this._link, { force: true })
                .catch(err => {
                    if (body) body.innerHTML = `<div class="lt-live-error">${err.message || err}</div>`;
                });
        },

        update(link, result) {
            this._link = link || this._link;
            const drawer = ensureDrawer();
            const subtitle = document.getElementById('link-live-drawer-subtitle');
            const body = document.getElementById('link-live-drawer-body');
            if (subtitle) subtitle.textContent = this._link ? `Link ${this._link.id || ''}` : 'No link selected';
            if (!body) return;
            body.innerHTML = window.LinkTelemetry?.renderTelemetryHtml(this._link, result) || '<div class="lt-live-empty">No live telemetry rows.</div>';
            window.LinkTelemetry?.wireTelemetryActions(body, this._link, result);
            this._wire(drawer);
        },

        _wire(drawer) {
            const close = document.getElementById('link-live-drawer-close');
            const refresh = document.getElementById('link-live-drawer-refresh');
            const auto = document.getElementById('link-live-drawer-auto');
            if (close && !close._wired) {
                close._wired = true;
                close.onclick = () => this.hide();
            }
            if (refresh && !refresh._wired) {
                refresh._wired = true;
                refresh.onclick = () => this.refresh();
            }
            if (auto && !auto._wired) {
                auto._wired = true;
                auto.onchange = () => {
                    if (!this._link?.id || !window.LinkTelemetry) return;
                    if (auto.checked) window.LinkTelemetry.subscribeAutoRefresh(this._editor, this._link, 30000);
                    else window.LinkTelemetry.unsubscribeAutoRefresh(this._link.id);
                };
            }
        }
    };
})();
