/**
 * topology-dialogs.js - Dialog UI Components
 * 
 * Extracted from topology.js for modular architecture.
 * Contains input, info, and confirm dialogs (replacements for browser prompts).
 * 
 * @version 1.0.0
 * @date 2026-02-04
 */

'use strict';

window.DialogManager = {

    /**
     * Show custom input dialog (replacement for prompt())
     */
    showInputDialog(editor, title, placeholder, callback, defaultValue = '') {
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0,0,0,0.7);
            z-index: 9999999;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        const dialog = document.createElement('div');
        dialog.style.cssText = `
            background: #2c3e50;
            border-radius: 8px;
            padding: 20px;
            min-width: 350px;
            max-width: 90vw;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5);
            position: relative;
        `;
        dialog.innerHTML = `
            <div style="color:#ecf0f1;font-size:16px;font-weight:bold;margin-bottom:15px;">${title}</div>
            <input type="text" id="dialog-input" style="width:100%;padding:10px;border:1px solid #4a5568;border-radius:4px;background:#1a252f;color:#ecf0f1;font-size:14px;box-sizing:border-box;" placeholder="${placeholder}" value="${defaultValue}">
            <div style="margin-top:15px;display:flex;gap:10px;justify-content:flex-end;">
                <button id="dialog-cancel" style="padding:8px 16px;border:none;border-radius:4px;background:#7f8c8d;color:white;cursor:pointer;">Cancel</button>
                <button id="dialog-ok" style="padding:8px 16px;border:none;border-radius:4px;background:#27ae60;color:white;cursor:pointer;font-weight:bold;">OK</button>
            </div>
        `;
        
        overlay.appendChild(dialog);
        document.body.appendChild(overlay);
        
        const input = dialog.querySelector('#dialog-input');
        const okBtn = dialog.querySelector('#dialog-ok');
        const cancelBtn = dialog.querySelector('#dialog-cancel');
        
        input.focus();
        input.select();
        
        const cleanup = () => {
            document.body.removeChild(overlay);
        };
        
        okBtn.onclick = () => {
            cleanup();
            callback(input.value.trim());
        };
        
        cancelBtn.onclick = () => {
            cleanup();
            callback(null);
        };
        
        input.onkeydown = (e) => {
            if (e.key === 'Enter') {
                cleanup();
                callback(input.value.trim());
            } else if (e.key === 'Escape') {
                cleanup();
                callback(null);
            }
        };
        
        overlay.onclick = (e) => {
            if (e.target === overlay) {
                cleanup();
                callback(null);
            }
        };
    },

    /**
     * Show info dialog (replacement for alert())
     */
    showInfoDialog(editor, title, message) {
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0,0,0,0.7);
            z-index: 9999999;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        const dialog = document.createElement('div');
        dialog.style.cssText = `
            background: #2c3e50;
            border-radius: 8px;
            padding: 20px;
            min-width: 350px;
            max-width: 90vw;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5);
            position: relative;
        `;
        dialog.innerHTML = `
            <div style="color:#FF5E1F;font-size:16px;font-weight:bold;margin-bottom:15px;border-bottom:1px solid #4a5568;padding-bottom:10px;">${title}</div>
            <pre style="color:#ecf0f1;font-size:13px;white-space:pre-wrap;word-wrap:break-word;margin:0;font-family:Consolas,Monaco,monospace;line-height:1.5;">${message}</pre>
            <div style="margin-top:20px;display:flex;gap:10px;justify-content:flex-end;">
                <button id="dialog-close" style="padding:8px 20px;border:none;border-radius:4px;background:#3498db;color:white;cursor:pointer;font-weight:bold;">OK</button>
            </div>
        `;
        
        overlay.appendChild(dialog);
        document.body.appendChild(overlay);
        
        const closeBtn = dialog.querySelector('#dialog-close');
        
        const cleanup = () => document.body.removeChild(overlay);
        
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
    showConfirmDialog(editor, title, message, onConfirm, onCancel = null) {
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0,0,0,0.7);
            z-index: 9999999;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        const dialog = document.createElement('div');
        dialog.style.cssText = `
            background: #2c3e50;
            border-radius: 8px;
            padding: 20px;
            min-width: 350px;
            max-width: 90vw;
            max-height: 90vh;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5);
            position: relative;
            overflow-y: auto;
        `;
        dialog.innerHTML = `
            <div style="color:#FF5E1F;font-size:16px;font-weight:bold;margin-bottom:15px;">${title}</div>
            <div style="color:#ecf0f1;font-size:14px;margin-bottom:20px;line-height:1.5;">${message}</div>
            <div style="display:flex;gap:10px;justify-content:flex-end;">
                <button id="dialog-no" style="padding:8px 16px;border:none;border-radius:4px;background:#7f8c8d;color:white;cursor:pointer;">Cancel</button>
                <button id="dialog-yes" style="padding:8px 16px;border:none;border-radius:4px;background:#e74c3c;color:white;cursor:pointer;font-weight:bold;">Yes, Replace</button>
            </div>
        `;
        
        overlay.appendChild(dialog);
        document.body.appendChild(overlay);
        
        const cleanup = () => document.body.removeChild(overlay);
        
        dialog.querySelector('#dialog-yes').onclick = () => { cleanup(); if (onConfirm) onConfirm(); };
        dialog.querySelector('#dialog-no').onclick = () => { cleanup(); if (onCancel) onCancel(); };
        overlay.onclick = (e) => { if (e.target === overlay) { cleanup(); if (onCancel) onCancel(); } };
    }
};

console.log('[topology-dialogs.js] DialogManager loaded');
