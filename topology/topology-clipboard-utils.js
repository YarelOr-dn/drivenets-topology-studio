/**
 * topology-clipboard-utils.js - Safe clipboard write for HTTP (non-secure) contexts
 *
 * navigator.clipboard.writeText() requires HTTPS or localhost. When the app is
 * accessed via server IP over HTTP, it fails. This utility falls back to
 * document.execCommand('copy') which works in HTTP contexts.
 *
 * Usage: window.safeClipboardWrite(text).then(() => ...).catch(err => ...)
 */
'use strict';

(function() {
    function legacyClipboardWrite(text) {
        return new Promise(function(resolve, reject) {
            try {
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.cssText = 'position:fixed;left:-9999px;top:-9999px;opacity:0';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                const success = document.execCommand('copy');
                document.body.removeChild(textArea);
                if (success) {
                    resolve();
                } else {
                    reject(new Error('execCommand copy failed'));
                }
            } catch (e) {
                reject(e);
            }
        });
    }

    function safeClipboardWrite(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(text).catch(function(err) {
                console.warn('[Clipboard] Modern API failed (HTTP context?), using fallback:', err);
                return legacyClipboardWrite(text);
            });
        }
        return legacyClipboardWrite(text);
    }

    window.safeClipboardWrite = safeClipboardWrite;
})();
