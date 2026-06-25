// ============================================================================
// TOPOLOGY FILE MANAGER
// ============================================================================
// Handles file operations: auto-save, crash recovery, save, load, export.
// Enhanced with crash recovery and periodic auto-save.
//
// Usage:
//   editor.files.enableAutoSave();          // Start periodic auto-save
//   editor.files.scheduleAutoSave();        // Trigger debounced save
//   editor.files.checkForRecovery();        // Check for crash recovery
//   editor.files.save(filename);            // Save to file
//   editor.files.load(file);                // Load from file
// ============================================================================

class FileManager {
    constructor(editor) {
        this.editor = editor;
        
        // Auto-save settings
        this.autoSaveKey = 'topology_autosave_v2';
        this.recoveryKey = 'topology_recovery';
        this.sessionKey = 'topology_session';
        this.autoSaveTimer = null;
        this.autoSaveInterval = null;
        this.autoSaveDelay = 1000;        // 1 second debounce for change-triggered saves
        this.autoSaveIntervalMs = 30000;  // 30 seconds for periodic saves
        
        // Session tracking
        this.sessionId = this.generateSessionId();
        this.sessionStartTime = Date.now();
        
        // Recovery state
        this.recoveryData = null;
        this.hasShownRecoveryPrompt = false;
        
        // Initialize session
        this.initSession();
    }
    
    /**
     * Generate a unique session ID
     */
    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    /**
     * Initialize session tracking
     */
    initSession() {
        try {
            const previousSession = localStorage.getItem(this.sessionKey);

            // Preserve previous session's closedCleanly BEFORE overwriting
            this.previousSessionClosedCleanly = false;
            if (previousSession) {
                const prev = JSON.parse(previousSession);
                this.previousSessionClosedCleanly = prev.closedCleanly === true;
                const hourAgo = Date.now() - (60 * 60 * 1000);
                if (prev.lastActive > hourAgo && !prev.closedCleanly) {
                    console.log('[FileManager] Previous session may have crashed:', prev.id);
                }
            }

            // Store current session (overwrites previous)
            const sessionData = {
                id: this.sessionId,
                startTime: this.sessionStartTime,
                lastActive: Date.now(),
                url: window.location.href
            };
            localStorage.setItem(this.sessionKey, JSON.stringify(sessionData));

            // Mark session as closed when window closes
            window.addEventListener('beforeunload', () => {
                this.markSessionClosed();
            });

        } catch (e) {
            console.warn('[FileManager] Session init failed:', e);
        }
    }
    
    /**
     * Mark the current session as closed cleanly
     */
    markSessionClosed() {
        try {
            const sessionData = JSON.parse(localStorage.getItem(this.sessionKey) || '{}');
            sessionData.closedCleanly = true;
            sessionData.closedAt = Date.now();
            localStorage.setItem(this.sessionKey, JSON.stringify(sessionData));
        } catch (e) {
            // Ignore errors during unload
        }
    }

    sanitizeObjectsForPersistence(objects) {
        if (!Array.isArray(objects)) return [];
        return objects.map((obj) => {
            if (!obj || typeof obj !== 'object') return obj;
            const copy = { ...obj };
            if (copy._hiddenByGroup) {
                delete copy._hiddenByGroup;
                if (copy._hidden === true) delete copy._hidden;
            }
            delete copy._xrayCaptureActive;
            return copy;
        });
    }
    
    /**
     * Enable periodic auto-save (called on app start)
     * @param {number} intervalMs - Interval in milliseconds (default 30s)
     */
    enableAutoSave(intervalMs = null) {
        if (intervalMs) {
            this.autoSaveIntervalMs = intervalMs;
        }
        
        // Clear any existing interval
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
        }
        
        // Start periodic auto-save
        this.autoSaveInterval = setInterval(() => {
            this.saveRecoveryPoint();
        }, this.autoSaveIntervalMs);
        
        console.log(`[FileManager] Auto-save enabled (every ${this.autoSaveIntervalMs / 1000}s)`);
    }
    
    /**
     * Disable periodic auto-save
     */
    disableAutoSave() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
            this.autoSaveInterval = null;
        }
        console.log('[FileManager] Auto-save disabled');
    }

    /**
     * Schedule an auto-save with debouncing (called after state changes)
     */
    scheduleAutoSave() {
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }
        const generation = this.editor?._topologyGeneration || 0;
        
        this.autoSaveTimer = setTimeout(() => {
            if (generation !== (this.editor?._topologyGeneration || 0)) return;
            this.autoSave();
        }, this.autoSaveDelay);
    }

    /**
     * Perform immediate auto-save to localStorage
     */
    autoSave() {
        if (this.editor.initializing) return;
        
        try {
            // Delegate to editor's autoSave if available
            if (typeof this.editor.autoSave === 'function') {
                this.editor.autoSave();
            } else {
                // Fallback: direct localStorage save
                this.saveToLocalStorage(this.autoSaveKey);
            }
        } catch (error) {
            console.error('[FileManager] Auto-save failed:', error);
            if (window.ErrorBoundary) {
                ErrorBoundary.handleError(error, 'FileManager.autoSave');
            }
        }
    }
    
    /**
     * Save a recovery point (more comprehensive than regular auto-save)
     */
    saveRecoveryPoint() {
        if (this.editor.initializing) return;
        if (!Array.isArray(this.editor.objects) || this.editor.objects.length === 0) return;
        
        // Sanity check: don't overwrite recovery with massively reduced state
        const prevCount = this._lastRecoveryObjectCount || 0;
        if (prevCount >= 5 && this.editor.objects.length < Math.ceil(prevCount * 0.3)) {
            console.warn(`[FileManager] Recovery save blocked: objects dropped from ${prevCount} to ${this.editor.objects.length}`);
            return;
        }
        
        try {
            const recoveryData = {
                version: '2.0',
                sessionId: this.sessionId,
                timestamp: Date.now(),
                timestampISO: new Date().toISOString(),
                objects: this.sanitizeObjectsForPersistence(this.editor.objects),
                counters: {
                    device: this.editor.deviceIdCounter,
                    link: this.editor.linkIdCounter,
                    text: this.editor.textIdCounter,
                    shape: this.editor.shapeIdCounter || 0,
                    packet: this.editor.packetIdCounter || 0
                },
                deviceCounters: this.editor.deviceCounters,
                viewport: {
                    offsetX: this.editor.offsetX,
                    offsetY: this.editor.offsetY,
                    zoom: this.editor.zoomLevel
                },
                currentFile: this.editor.currentFileName || null,
                historyIndex: this.editor.historyIndex || 0,
                topologySession: {
                    generation: this.editor._topologyGeneration || 0,
                    identity: this.editor._activeTopologyIdentity || null
                }
            };
            
            localStorage.setItem(this.recoveryKey, JSON.stringify(recoveryData));
            this._lastRecoveryObjectCount = this.editor.objects.length;
            
            // Update session activity
            const sessionData = JSON.parse(localStorage.getItem(this.sessionKey) || '{}');
            sessionData.lastActive = Date.now();
            sessionData.objectCount = this.editor.objects.length;
            localStorage.setItem(this.sessionKey, JSON.stringify(sessionData));
        } catch (error) {
            console.error('[FileManager] Recovery point save failed:', error);
        }
    }
    
    /**
     * Check for recovery data and prompt user if found.
     *
     * History note (2026-04-22): The prompt fired on almost every
     * refresh because the "did we already restore this?" check only
     * compared recovery-data against `topology_current`, which is
     * ONLY written by the explicit "Quick Save" command. The normal
     * path (auto-save -> auto-load) writes to `topology_autosave_v2`
     * AND re-hydrates `editor.objects`. So after a clean refresh the
     * canvas already showed the same 8 objects the recovery snapshot
     * had, and the prompt asked "Recover?" for content that was
     * already on screen.
     *
     * New logic:
     *   1. Previous session clean-closed -> skip (unchanged).
     *   2. Recovery is byte-identical to ANY of:
     *        - `topology_current` (Quick Save target)
     *        - `topology_autosave_v2` (debounced auto-save)
     *        - the LIVE `editor.objects` (what's on screen RIGHT NOW
     *          after the auto-loader ran)
     *      -> skip. We only prompt when there's genuinely LOST work.
     *   3. Recovery is smaller than live canvas (subset) -> skip;
     *      whatever is on screen is strictly newer.
     *   4. Suppress-for-session flag `topology_suppress_recovery_until`
     *      -> skip if timestamp is in the future.
     *
     * Everything else stays the same: <24h old, from a different
     * session, has content, show the modal.
     *
     * @returns {Promise<boolean>} True if recovery was offered/performed
     */
    async checkForRecovery() {
        if (this.hasShownRecoveryPrompt) return false;
        
        try {
            const recoveryData = localStorage.getItem(this.recoveryKey);
            if (!recoveryData) return false;
            
            const data = JSON.parse(recoveryData);
            
            // (1) Previous session closed cleanly -> nothing to recover.
            if (this.previousSessionClosedCleanly) {
                data.sessionId = this.sessionId;
                localStorage.setItem(this.recoveryKey, JSON.stringify(data));
                return false;
            }
            
            // (4) User asked us to shut up for a while (e.g. they
            // clicked "Start Fresh" last time and don't want the
            // dialog reappearing on every quick refresh).
            try {
                const suppressUntil = parseInt(
                    localStorage.getItem('topology_suppress_recovery_until') || '0', 10
                );
                if (suppressUntil && Date.now() < suppressUntil) {
                    return false;
                }
            } catch (_) {}

            // Canonicalize an object list the way saveRecoveryPoint does
            // (strip transient fields so cosmetic deltas from
            // auto-layout / selection state don't defeat equality).
            const canon = (arr) => {
                if (!Array.isArray(arr)) return '';
                try {
                    return JSON.stringify(arr.map(o => {
                        if (!o || typeof o !== 'object') return o;
                        const c = Object.assign({}, o);
                        // These are runtime UI state, not content.
                        delete c.selected;
                        delete c.hovered;
                        delete c.dragging;
                        delete c._tempHighlight;
                        delete c._xrayCaptureActive;
                        return c;
                    }));
                } catch (_) { return ''; }
            };
            const recoveryCanon = canon(data.objects);
            const recoveryCount = (data.objects || []).length;

            // (2a) Compare to topology_current (Quick Save target).
            const samplesToCheck = [];
            try {
                const cur = localStorage.getItem('topology_current');
                if (cur) samplesToCheck.push(JSON.parse(cur).objects || []);
            } catch (_) {}
            // (2b) Compare to topology_autosave_v2 (debounced auto-save --
            // this is what the editor actually loaded on boot).
            try {
                const asv2 = localStorage.getItem(this.autoSaveKey);
                if (asv2) samplesToCheck.push(JSON.parse(asv2).objects || []);
            } catch (_) {}
            // (2c) Compare to the LIVE canvas. This is the real
            // anti-false-positive: if whatever we'd "recover" is
            // already on the screen, we stay quiet.
            if (this.editor && Array.isArray(this.editor.objects)) {
                samplesToCheck.push(this.editor.objects);
            }

            for (const sample of samplesToCheck) {
                if (canon(sample) === recoveryCanon) {
                    data.sessionId = this.sessionId;
                    localStorage.setItem(this.recoveryKey, JSON.stringify(data));
                    console.log('[FileManager] Recovery check skipped -- snapshot already on canvas');
                    return false;
                }
            }

            // (3) Recovery is smaller than what's on screen -> the live
            // state is newer, so don't offer to regress. We still show
            // the dialog if live is empty (user may have hit delete-all
            // by accident and reloaded).
            const liveCount = (this.editor && this.editor.objects) ? this.editor.objects.length : 0;
            if (liveCount > 0 && recoveryCount <= liveCount) {
                console.log(
                    '[FileManager] Recovery check skipped -- live canvas has '
                    + liveCount + ' objects vs recovery has ' + recoveryCount
                );
                data.sessionId = this.sessionId;
                localStorage.setItem(this.recoveryKey, JSON.stringify(data));
                return false;
            }
            
            const isFromDifferentSession = data.sessionId !== this.sessionId;
            const isRecent = (Date.now() - data.timestamp) < (24 * 60 * 60 * 1000);
            const hasContent = recoveryCount > 0;
            
            if (isFromDifferentSession && isRecent && hasContent) {
                this.recoveryData = data;
                this.hasShownRecoveryPrompt = true;
                const recovered = await this.showRecoveryPrompt(data);
                return recovered;
            }
        } catch (error) {
            console.error('[FileManager] Recovery check failed:', error);
        }
        
        return false;
    }
    
    /**
     * Show recovery prompt to user
     * @param {object} data - Recovery data
     * @returns {Promise<boolean>} True if user chose to recover
     */
    showRecoveryPrompt(data) {
        return new Promise((resolve) => {
            const timestamp = new Date(data.timestamp);
            const timeAgo = this.formatTimeAgo(timestamp);
            const objectCount = data.objects.length;
            
            // Create modal
            const modal = document.createElement('div');
            modal.id = 'recovery-modal';
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.7);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10001;
                font-family: 'Poppins', -apple-system, sans-serif;
            `;
            
            modal.innerHTML = `
                <div style="
                    background: #1e1e2e;
                    border-radius: 12px;
                    padding: 24px;
                    max-width: 450px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
                    border: 1px solid rgba(255,255,255,0.1);
                ">
                    <h2 style="margin: 0 0 16px; color: #FF7A33; font-size: 18px;">
                        ⚠️ Unsaved Work Found
                    </h2>
                    <p style="margin: 0 0 12px; color: #ccc; font-size: 14px; line-height: 1.5;">
                        We found a previous session with unsaved work:
                    </p>
                    <ul style="margin: 0 0 16px; padding-left: 20px; color: #aaa; font-size: 13px;">
                        <li><strong>${objectCount}</strong> objects (devices, links, etc.)</li>
                        <li>Saved <strong>${timeAgo}</strong></li>
                        ${data.currentFile ? `<li>File: <strong>${data.currentFile}</strong></li>` : ''}
                    </ul>
                    <p style="margin: 0 0 20px; color: #888; font-size: 13px;">
                        Would you like to recover this work?
                    </p>
                    <div style="display: flex; gap: 12px; justify-content: flex-end;">
                        <button id="recovery-discard" style="
                            padding: 10px 20px;
                            border: 1px solid rgba(255,255,255,0.2);
                            background: transparent;
                            color: #aaa;
                            border-radius: 6px;
                            cursor: pointer;
                            font-size: 14px;
                        ">Start Fresh</button>
                        <button id="recovery-restore" style="
                            padding: 10px 20px;
                            border: none;
                            background: #3498db;
                            color: white;
                            border-radius: 6px;
                            cursor: pointer;
                            font-size: 14px;
                            font-weight: 500;
                        ">Recover Work</button>
                    </div>
                </div>
            `;
            
            modal.addEventListener('keydown', (e) => { e.stopPropagation(); });
            modal.addEventListener('keyup', (e) => { e.stopPropagation(); });
            document.body.appendChild(modal);
            
            // Handle buttons
            document.getElementById('recovery-restore').addEventListener('click', () => {
                modal.remove();
                this.performRecovery(data);
                resolve(true);
            });
            
            document.getElementById('recovery-discard').addEventListener('click', () => {
                modal.remove();
                this.clearRecoveryData();
                // Suppress the prompt for 10 minutes so a quick refresh
                // right after "Start Fresh" doesn't replay the same
                // modal from stale data that hasn't been fully wiped.
                try {
                    localStorage.setItem(
                        'topology_suppress_recovery_until',
                        String(Date.now() + 10 * 60 * 1000)
                    );
                } catch (_) {}
                resolve(false);
            });
        });
    }
    
    /**
     * Perform the actual recovery
     * @param {object} data - Recovery data
     */
    performRecovery(data) {
        try {
            // Restore objects
            this.editor.objects = this.sanitizeObjectsForPersistence(data.objects);
            this.editor._xrayCapturing = null;
            
            // Restore counters
            if (data.counters) {
                this.editor.deviceIdCounter = data.counters.device || 0;
                this.editor.linkIdCounter = data.counters.link || 0;
                this.editor.textIdCounter = data.counters.text || 0;
                if (data.counters.shape !== undefined) {
                    this.editor.shapeIdCounter = data.counters.shape;
                }
                if (data.counters.packet !== undefined) {
                    this.editor.packetIdCounter = data.counters.packet;
                }
            }
            
            // Restore device counters
            if (data.deviceCounters) {
                this.editor.deviceCounters = data.deviceCounters;
            }
            
            // Restore viewport
            if (data.viewport) {
                this.editor.offsetX = data.viewport.offsetX || 0;
                this.editor.offsetY = data.viewport.offsetY || 0;
                this.editor.zoomLevel = data.viewport.zoom || 1;
            }
            
            // Restore file name
            if (data.currentFile) {
                this.editor.currentFileName = data.currentFile;
            }
            if (this.editor.groups && typeof this.editor.groups.validate === 'function') {
                this.editor.groups.validate();
            }
            
            // Redraw
            this.editor.draw();
            
            // Save new state
            this.editor.saveState();
            
            console.log(`[FileManager] Recovered ${data.objects.length} objects from ${new Date(data.timestamp).toLocaleString()}`);
            
            // Show success notification
            if (window.ErrorBoundary) {
                ErrorBoundary.showUserNotification(
                    `Recovered ${data.objects.length} objects successfully!`,
                    'info'
                );
            }
            
            // Clear old recovery data (now saved as current)
            this.clearRecoveryData();
            
        } catch (error) {
            console.error('[FileManager] Recovery failed:', error);
            if (window.ErrorBoundary) {
                ErrorBoundary.showUserNotification(
                    'Recovery failed. Please try loading a backup file.',
                    'error'
                );
            }
        }
    }
    
    /**
     * Clear recovery data
     */
    clearRecoveryData() {
        localStorage.removeItem(this.recoveryKey);
        this.recoveryData = null;
    }
    
    /**
     * Format time ago string
     * @param {Date} date - The date to format
     * @returns {string} Human readable time ago
     */
    formatTimeAgo(date) {
        const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
        
        if (seconds < 60) return 'just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
        return `${Math.floor(seconds / 86400)} days ago`;
    }
    
    /**
     * Save current state to localStorage
     * @param {string} key - Storage key
     */
    saveToLocalStorage(key) {
        const data = {
            objects: this.sanitizeObjectsForPersistence(this.editor.objects),
            deviceIdCounter: this.editor.deviceIdCounter,
            linkIdCounter: this.editor.linkIdCounter,
            textIdCounter: this.editor.textIdCounter,
            deviceCounters: this.editor.deviceCounters,
            timestamp: Date.now()
        };
        localStorage.setItem(key, JSON.stringify(data));
    }

    /**
     * Load auto-saved data from localStorage
     * @returns {object|null} Saved data or null
     */
    loadAutoSave() {
        try {
            const data = localStorage.getItem(this.autoSaveKey);
            if (data) {
                return JSON.parse(data);
            }
        } catch (error) {
            console.error('[FileManager] Load auto-save failed:', error);
        }
        return null;
    }

    /**
     * Clear auto-save data
     */
    clearAutoSave() {
        localStorage.removeItem(this.autoSaveKey);
    }

    /**
     * Export topology as JSON file
     * @param {string} filename - Output filename
     */
    exportJSON(filename = 'topology.json') {
        try {
            const data = {
                version: '2.0',
                exported: new Date().toISOString(),
                objects: this.sanitizeObjectsForPersistence(this.editor.objects),
                counters: {
                    device: this.editor.deviceIdCounter,
                    link: this.editor.linkIdCounter,
                    text: this.editor.textIdCounter,
                    shape: this.editor.shapeIdCounter || 0,
                    packet: this.editor.packetIdCounter || 0
                },
                deviceCounters: this.editor.deviceCounters,
                viewport: {
                    offsetX: this.editor.offsetX,
                    offsetY: this.editor.offsetY,
                    zoom: this.editor.zoomLevel
                }
            };
            
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            
            URL.revokeObjectURL(url);
            console.log('[FileManager] Exported to', filename);
        } catch (error) {
            console.error('[FileManager] Export failed:', error);
            if (window.ErrorBoundary) {
                ErrorBoundary.handleError(error, 'FileManager.exportJSON');
            }
        }
    }

    /**
     * Import topology from JSON file
     * @param {File} file - File object to import
     * @returns {Promise<boolean>} Success
     */
    async importJSON(file) {
        try {
            const text = await file.text();
            const data = JSON.parse(text);
            
            if (data.objects && Array.isArray(data.objects)) {
                this.editor.objects = this.sanitizeObjectsForPersistence(data.objects);
                this.editor._xrayCapturing = null;
                if (data.counters) {
                    this.editor.deviceIdCounter = data.counters.device || 0;
                    this.editor.linkIdCounter = data.counters.link || 0;
                    this.editor.textIdCounter = data.counters.text || 0;
                    if (data.counters.shape !== undefined) {
                        this.editor.shapeIdCounter = data.counters.shape;
                    }
                    if (data.counters.packet !== undefined) {
                        this.editor.packetIdCounter = data.counters.packet;
                    }
                }
                if (data.deviceCounters) {
                    this.editor.deviceCounters = data.deviceCounters;
                }
                if (data.viewport) {
                    this.editor.offsetX = data.viewport.offsetX || 0;
                    this.editor.offsetY = data.viewport.offsetY || 0;
                    this.editor.zoomLevel = data.viewport.zoom || 1;
                }
                if (this.editor.groups && typeof this.editor.groups.validate === 'function') {
                    this.editor.groups.validate();
                }
                this.editor.draw();
                this.editor.saveState();
                console.log('[FileManager] Imported', data.objects.length, 'objects');
                return true;
            }
        } catch (error) {
            console.error('[FileManager] Import failed:', error);
            if (window.ErrorBoundary) {
                ErrorBoundary.handleError(error, 'FileManager.importJSON');
            }
        }
        return false;
    }
    
    /**
     * Get storage usage info
     * @returns {object} Storage usage stats
     */
    getStorageInfo() {
        try {
            let totalSize = 0;
            const items = {};
            
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key.startsWith('topology')) {
                    const value = localStorage.getItem(key);
                    const size = new Blob([value]).size;
                    items[key] = size;
                    totalSize += size;
                }
            }
            
            return {
                totalBytes: totalSize,
                totalKB: (totalSize / 1024).toFixed(2),
                items
            };
        } catch (e) {
            return { error: e.message };
        }
    }
}

// Export for use
window.FileManager = FileManager;

window.createFileManager = function(editor) {
    return new FileManager(editor);
};

console.log('[topology-files.js] FileManager with crash recovery loaded');
