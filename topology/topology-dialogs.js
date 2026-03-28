/**
 * topology-dialogs.js - Dialog UI Components (Liquid Glass)
 * 
 * Extracted from topology.js for modular architecture.
 * Contains input, info, and confirm dialogs (replacements for browser prompts).
 * 
 * @version 2.0.0
 * @date 2026-03-10
 */

'use strict';

window.DialogManager = {

    _glassVars() {
        const dk = document.body.classList.contains('dark-mode');
        return {
            dk,
            overlayBg:    dk ? 'rgba(0,0,0,0.5)' : 'rgba(0,0,0,0.3)',
            glassBg:      dk ? 'linear-gradient(145deg, rgba(30,35,45,0.92), rgba(20,25,35,0.96))'
                             : 'linear-gradient(145deg, rgba(255,255,255,0.95), rgba(240,242,245,0.98))',
            glassBorder:  dk ? 'rgba(100,150,200,0.2)' : 'rgba(0,0,0,0.1)',
            glassShadow:  dk ? '0 12px 48px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.1)'
                             : '0 12px 48px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.8)',
            textColor:    dk ? '#ecf0f1' : '#1a1a2e',
            subtextColor: dk ? 'rgba(255,255,255,0.6)' : 'rgba(0,0,0,0.55)',
            inputBg:      dk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)',
            inputBorder:  dk ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.12)',
            cancelBg:     dk ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)',
            cancelColor:  dk ? '#ccc' : '#555',
        };
    },

    _ensureAnim() {
        if (!document.getElementById('dialog-glass-anim')) {
            const s = document.createElement('style');
            s.id = 'dialog-glass-anim';
            s.textContent = '@keyframes dialogGlassIn{from{opacity:0;transform:scale(0.95) translateY(10px)}to{opacity:1;transform:scale(1) translateY(0)}}';
            document.head.appendChild(s);
        }
    },

    _makeOverlay(g) {
        const el = document.createElement('div');
        el.style.cssText = `
            position:fixed; top:0; left:0; right:0; bottom:0;
            width:100vw; height:100vh;
            background:${g.overlayBg};
            backdrop-filter:blur(4px); -webkit-backdrop-filter:blur(4px);
            z-index:9999999;
            display:flex; align-items:center; justify-content:center;
        `;
        return el;
    },

    _makeDialog(g) {
        const el = document.createElement('div');
        el.style.cssText = `
            background:${g.glassBg};
            border:1px solid ${g.glassBorder};
            border-radius:16px;
            padding:24px;
            min-width:380px; max-width:90vw;
            box-shadow:${g.glassShadow};
            backdrop-filter:blur(32px) saturate(180%);
            -webkit-backdrop-filter:blur(32px) saturate(180%);
            animation:dialogGlassIn 0.2s ease;
        `;
        return el;
    },

    /**
     * Show custom input dialog (replacement for prompt())
     */
    showInputDialog(editor, title, placeholder, callback, defaultValue = '') {
        this._ensureAnim();
        const g = this._glassVars();
        const overlay = this._makeOverlay(g);
        const dialog = this._makeDialog(g);

        dialog.innerHTML = `
            <div style="color:${g.textColor};font-size:17px;font-weight:600;margin-bottom:16px;letter-spacing:-0.2px;">${title}</div>
            <input type="text" data-role="input" style="
                width:100%; padding:10px 12px;
                border:1px solid ${g.inputBorder};
                border-radius:8px; background:${g.inputBg};
                color:${g.textColor}; font-size:14px;
                box-sizing:border-box; outline:none;
                transition:border-color 0.2s;
            " placeholder="${placeholder}" value="${defaultValue}"
              onfocus="this.style.borderColor='rgba(0,180,216,0.5)'"
              onblur="this.style.borderColor='${g.inputBorder}'" />
            <div style="margin-top:18px;display:flex;gap:8px;justify-content:flex-end;">
                <button data-role="cancel" style="padding:8px 18px;border:1px solid ${g.glassBorder};border-radius:8px;background:${g.cancelBg};color:${g.cancelColor};cursor:pointer;font-size:13px;">Cancel</button>
                <button data-role="ok" style="padding:8px 18px;border:none;border-radius:8px;background:#27ae60;color:white;cursor:pointer;font-weight:600;font-size:13px;">OK</button>
            </div>
        `;
        
        overlay.appendChild(dialog);
        document.body.appendChild(overlay);
        
        const input = dialog.querySelector('[data-role="input"]');
        const okBtn = dialog.querySelector('[data-role="ok"]');
        const cancelBtn = dialog.querySelector('[data-role="cancel"]');
        
        input.focus();
        input.select();
        
        const cleanup = () => { if (overlay.parentNode) overlay.parentNode.removeChild(overlay); };
        
        okBtn.onclick = () => { cleanup(); callback(input.value.trim()); };
        cancelBtn.onclick = () => { cleanup(); callback(null); };
        input.onkeydown = (e) => {
            if (e.key === 'Enter') { cleanup(); callback(input.value.trim()); }
            else if (e.key === 'Escape') { cleanup(); callback(null); }
        };
        overlay.onclick = (e) => { if (e.target === overlay) { cleanup(); callback(null); } };
    },

    /**
     * Show info dialog (replacement for alert())
     */
    showInfoDialog(editor, title, message) {
        this._ensureAnim();
        const g = this._glassVars();
        const overlay = this._makeOverlay(g);
        const dialog = this._makeDialog(g);
        dialog.style.maxHeight = '80vh';
        dialog.style.overflowY = 'auto';

        dialog.innerHTML = `
            <div style="color:#FF5E1F;font-size:17px;font-weight:600;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid ${g.glassBorder};letter-spacing:-0.2px;">${title}</div>
            <pre style="color:${g.textColor};font-size:13px;white-space:pre-wrap;word-wrap:break-word;margin:0;font-family:'DM Mono',Consolas,Monaco,monospace;line-height:1.5;">${message}</pre>
            <div style="margin-top:20px;display:flex;gap:8px;justify-content:flex-end;">
                <button data-role="close" style="padding:8px 22px;border:none;border-radius:8px;background:#3498db;color:white;cursor:pointer;font-weight:600;font-size:13px;">OK</button>
            </div>
        `;
        
        overlay.appendChild(dialog);
        document.body.appendChild(overlay);
        
        const closeBtn = dialog.querySelector('[data-role="close"]');
        const cleanup = () => { if (overlay.parentNode) overlay.parentNode.removeChild(overlay); };
        
        closeBtn.onclick = cleanup;
        overlay.onclick = (e) => { if (e.target === overlay) cleanup(); };
        document.addEventListener('keydown', function escHandler(e) {
            if (e.key === 'Escape') { cleanup(); document.removeEventListener('keydown', escHandler); }
        });
        
        closeBtn.focus();
    },

    /**
     * Show confirmation dialog (replacement for confirm())
     */
    showConfirmDialog(editor, title, message, onConfirm, onCancel = null, options = {}) {
        this._ensureAnim();
        const g = this._glassVars();
        const overlay = this._makeOverlay(g);
        const dialog = this._makeDialog(g);
        dialog.style.maxHeight = '90vh';
        dialog.style.overflowY = 'auto';

        const confirmLabel = options.confirmLabel || 'Yes, Replace';
        const confirmBg = options.confirmBg || '#e74c3c';
        const htmlMessage = message.replace(/\n/g, '<br>');

        dialog.innerHTML = `
            <div style="color:#FF5E1F;font-size:17px;font-weight:600;margin-bottom:14px;letter-spacing:-0.2px;">${title}</div>
            <div style="color:${g.textColor};font-size:14px;margin-bottom:20px;line-height:1.5;">${htmlMessage}</div>
            <div style="display:flex;gap:8px;justify-content:flex-end;">
                <button data-role="cancel" style="padding:8px 18px;border:1px solid ${g.glassBorder};border-radius:8px;background:${g.cancelBg};color:${g.cancelColor};cursor:pointer;font-size:13px;">Cancel</button>
                <button data-role="confirm" style="padding:8px 18px;border:none;border-radius:8px;background:${confirmBg};color:white;cursor:pointer;font-weight:600;font-size:13px;">${confirmLabel}</button>
            </div>
        `;
        
        overlay.appendChild(dialog);
        document.body.appendChild(overlay);
        
        const cleanup = () => { if (overlay.parentNode) overlay.parentNode.removeChild(overlay); };
        
        dialog.querySelector('[data-role="confirm"]').onclick = () => { cleanup(); if (onConfirm) onConfirm(); };
        dialog.querySelector('[data-role="cancel"]').onclick = () => { cleanup(); if (onCancel) onCancel(); };
        overlay.onclick = (e) => { if (e.target === overlay) { cleanup(); if (onCancel) onCancel(); } };
    }
};

console.log('[topology-dialogs.js] DialogManager loaded (liquid glass v2)');
