/**
 * topology-notifications.js - Notification and Hint UI Components
 * 
 * Extracted from topology.js for modular architecture.
 * Contains toast notifications, helper hints, and setup dialogs.
 * 
 * @version 1.0.0
 * @date 2026-02-04
 */

'use strict';

window.NotificationManager = {

    _history: [],
    _maxHistory: 80,
    _centerOpen: false,

    _addToHistory(message, type) {
        const cat = this._classifyMessage(message, type);
        this._history.unshift({ message, type, category: cat, time: Date.now() });
        if (this._history.length > this._maxHistory) this._history.length = this._maxHistory;
        const badge = document.getElementById('notif-badge');
        if (badge && !this._centerOpen) badge.style.display = 'block';
    },

    _classifyMessage(msg, type) {
        const m = msg.toLowerCase();
        if (m.includes('save') || m.includes('saved') || m.includes('quick save') || m.includes('auto-save') || m.includes('export')) return 'save';
        if (m.includes('moved to') || m.includes('move') || m.includes('→') || m.includes('domain')) return 'file';
        if (m.includes('link') || m.includes('curve') || m.includes('detach') || m.includes('sticky') || m.includes('attach')) return 'link';
        if (m.includes('device') || m.includes('ncf') || m.includes('ncm') || m.includes('ncc') || m.includes('router') || m.includes('switch')) return 'device';
        if (m.includes('text') || m.includes('label') || m.includes('font') || m.includes('style cop')) return 'text';
        if (m.includes('undo') || m.includes('redo')) return 'history';
        if (m.includes('load') || m.includes('open') || m.includes('import')) return 'load';
        if (m.includes('ssh') || m.includes('terminal')) return 'ssh';
        if (m.includes('dnaas') || m.includes('discover') || m.includes('lldp')) return 'network';
        if (m.includes('duplicate') || m.includes('copied') || m.includes('paste') || m.includes('clipboard')) return 'clipboard';
        if (type === 'error') return 'error';
        return 'general';
    },

    _formatTime(ts) {
        const d = new Date(ts);
        const hh = d.getHours().toString().padStart(2, '0');
        const mm = d.getMinutes().toString().padStart(2, '0');
        const ss = d.getSeconds().toString().padStart(2, '0');
        return `${hh}:${mm}:${ss}`;
    },

    _formatDate(ts) {
        const d = new Date(ts);
        const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        return `${months[d.getMonth()]} ${d.getDate()}`;
    },

    _timeAgo(ts) {
        const diff = (Date.now() - ts) / 1000;
        if (diff < 60) return 'just now';
        if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
        if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
        return Math.floor(diff / 86400) + 'd ago';
    },

    toggleCenter() {
        const existing = document.getElementById('notification-center-panel');
        if (existing) { this._closeCenter(); return; }
        this._openCenter();
    },

    _openCenter() {
        this._centerOpen = true;
        const badge = document.getElementById('notif-badge');
        if (badge) badge.style.display = 'none';

        const dk = document.body.classList.contains('dark-mode');
        const panel = document.createElement('div');
        panel.id = 'notification-center-panel';

        if (!document.getElementById('notif-center-styles')) {
            const s = document.createElement('style');
            s.id = 'notif-center-styles';
            s.textContent = `
                @keyframes ncSlideIn { 0% { opacity:0; transform:translateY(12px); } 100% { opacity:1; transform:translateY(0); } }
                @keyframes ncSlideOut { 0% { opacity:1; transform:translateY(0); } 100% { opacity:0; transform:translateY(12px); } }
                #notification-center-panel::-webkit-scrollbar { width: 4px; }
                #notification-center-panel::-webkit-scrollbar-track { background: transparent; }
                #notification-center-panel::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 4px; }
                .nc-entry { transition: background 0.12s ease; }
                .nc-entry:hover { background: ${dk ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)'} !important; }
            `;
            document.head.appendChild(s);
        }

        const toolbar = document.getElementById('left-toolbar');
        const panelLeft = toolbar ? toolbar.getBoundingClientRect().right + 8 : 210;

        panel.style.cssText = `
            position: fixed;
            bottom: 60px;
            left: ${panelLeft}px;
            width: 340px;
            max-height: 420px;
            z-index: 10001;
            border-radius: 16px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            animation: ncSlideIn 0.25s cubic-bezier(0.22,1,0.36,1) forwards;
            background: ${dk
                ? 'linear-gradient(160deg, rgba(18,22,36,0.92), rgba(12,16,28,0.96))'
                : 'linear-gradient(160deg, rgba(255,255,255,0.88), rgba(240,243,250,0.92))'};
            backdrop-filter: blur(28px) saturate(1.8);
            -webkit-backdrop-filter: blur(28px) saturate(1.8);
            border: 1px solid ${dk ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)'};
            box-shadow:
                0 16px 48px rgba(0,0,0,${dk ? '0.5' : '0.15'}),
                0 4px 12px rgba(0,0,0,${dk ? '0.3' : '0.08'}),
                inset 0 1px 0 ${dk ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.6)'};
            font-family: 'Poppins', -apple-system, sans-serif;
        `;

        const header = document.createElement('div');
        header.style.cssText = `
            display:flex; align-items:center; justify-content:space-between;
            padding: 14px 16px 10px;
            border-bottom: 1px solid ${dk ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'};
        `;
        header.innerHTML = `
            <div style="display:flex;align-items:center;gap:8px;">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="${dk ? 'rgba(255,255,255,0.6)' : 'rgba(0,0,0,0.5)'}" stroke-width="2" stroke-linecap="round">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                </svg>
                <span style="font-size:13px;font-weight:600;color:${dk ? 'rgba(255,255,255,0.85)' : 'rgba(0,0,0,0.75)'};letter-spacing:0.3px;">Notification Center</span>
                <span style="font-size:10px;color:${dk ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.3)'};font-weight:500;">${this._history.length}</span>
            </div>
        `;
        const clearBtn = document.createElement('button');
        clearBtn.textContent = 'Clear';
        clearBtn.style.cssText = `
            background:none; border:none; cursor:pointer;
            font-size:11px; font-weight:500; font-family:inherit;
            color:${dk ? 'rgba(255,255,255,0.35)' : 'rgba(0,0,0,0.35)'};
            padding:2px 6px; border-radius:4px;
            transition: color 0.12s, background 0.12s;
        `;
        clearBtn.onmouseenter = () => { clearBtn.style.color = dk ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.6)'; clearBtn.style.background = dk ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)'; };
        clearBtn.onmouseleave = () => { clearBtn.style.color = dk ? 'rgba(255,255,255,0.35)' : 'rgba(0,0,0,0.35)'; clearBtn.style.background = 'none'; };
        clearBtn.onclick = () => { this._history.length = 0; this._renderCenterEntries(list, dk); };
        header.appendChild(clearBtn);
        panel.appendChild(header);

        const list = document.createElement('div');
        list.style.cssText = 'flex:1; overflow-y:auto; padding:6px 8px 10px;';
        this._renderCenterEntries(list, dk);
        panel.appendChild(list);

        document.body.appendChild(panel);

        const closeOnClick = (e) => {
            if (!panel.contains(e.target) && !e.target.closest('#btn-notification-center')) {
                this._closeCenter();
                document.removeEventListener('mousedown', closeOnClick);
            }
        };
        setTimeout(() => document.addEventListener('mousedown', closeOnClick), 50);
    },

    _categoryMeta: {
        save:      { label: 'Save',      color: '#4ade80', icon: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>' },
        file:      { label: 'File',      color: '#60a5fa', icon: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>' },
        link:      { label: 'Link',      color: '#a78bfa', icon: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>' },
        device:    { label: 'Device',    color: '#f472b6', icon: '<rect x="4" y="4" width="16" height="16" rx="2"/><line x1="9" y1="9" x2="15" y2="9"/><line x1="9" y1="13" x2="13" y2="13"/>' },
        text:      { label: 'Text',      color: '#fbbf24', icon: '<polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/>' },
        history:   { label: 'History',   color: '#94a3b8', icon: '<polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>' },
        load:      { label: 'Load',      color: '#38bdf8', icon: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>' },
        ssh:       { label: 'SSH',       color: '#a3e635', icon: '<polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>' },
        network:   { label: 'Network',   color: '#34d399', icon: '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>' },
        clipboard: { label: 'Clipboard', color: '#fb923c', icon: '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1"/>' },
        error:     { label: 'Error',     color: '#f87171', icon: '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>' },
        general:   { label: 'General',   color: '#60a5fa', icon: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>' },
    },

    _renderCenterEntries(container, dk) {
        if (this._history.length === 0) {
            container.innerHTML = `
                <div style="text-align:center;padding:32px 16px;color:${dk ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.25)'};">
                    <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" style="margin-bottom:8px;opacity:0.5;">
                        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                    </svg>
                    <div style="font-size:12px;font-weight:500;">No notifications yet</div>
                </div>
            `;
            return;
        }

        let lastDate = '';
        container.innerHTML = '';

        this._history.forEach((entry, idx) => {
            const dateStr = this._formatDate(entry.time);
            if (dateStr !== lastDate) {
                lastDate = dateStr;
                const sep = document.createElement('div');
                sep.style.cssText = `font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;color:${dk ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)'};padding:8px 8px 4px;${idx > 0 ? `border-top:1px solid ${dk ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)'};margin-top:4px;` : ''}`;
                sep.textContent = dateStr;
                container.appendChild(sep);
            }

            const cat = entry.category || 'general';
            const meta = this._categoryMeta[cat] || this._categoryMeta.general;

            const row = document.createElement('div');
            row.className = 'nc-entry';
            row.style.cssText = `
                display:flex; align-items:flex-start; gap:8px;
                padding:7px 8px; border-radius:8px; cursor:default;
            `;
            row.innerHTML = `
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="${meta.color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;margin-top:2px;opacity:0.85;">
                    ${meta.icon}
                </svg>
                <div style="flex:1;min-width:0;">
                    <div style="font-size:11.5px;color:${dk ? 'rgba(255,255,255,0.8)' : 'rgba(0,0,0,0.7)'};line-height:1.4;word-break:break-word;">${this._escapeHtml(entry.message)}</div>
                    <div style="font-size:9px;color:${dk ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.25)'};margin-top:2px;display:flex;align-items:center;gap:6px;">
                        <span style="color:${meta.color};opacity:0.7;font-weight:600;">${meta.label}</span>
                        <span style="opacity:0.4;">·</span>
                        <span>${this._formatTime(entry.time)}</span>
                        <span>${this._timeAgo(entry.time)}</span>
                    </div>
                </div>
            `;
            container.appendChild(row);
        });
    },

    _escapeHtml(s) {
        return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    },

    _closeCenter() {
        this._centerOpen = false;
        const panel = document.getElementById('notification-center-panel');
        if (!panel) return;
        panel.style.animation = 'ncSlideOut 0.2s cubic-bezier(0.22,1,0.36,1) forwards';
        setTimeout(() => panel.remove(), 200);
    },

    /**
     * Show split-pane helper hint
     */
    showSplitHelperHint(editor) {
        const existing = document.getElementById('split-helper-hint');
        if (existing) return;
        
        const hint = document.createElement('div');
        hint.id = 'split-helper-hint';
        hint.style.cssText = `
            position: fixed;
            bottom: 120px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(145deg, #1e3a5f, #0f2744);
            border: 1px solid rgba(59, 130, 246, 0.4);
            border-radius: 10px;
            padding: 14px 20px;
            color: #e2e8f0;
            font-size: 13px;
            z-index: 10000;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            max-width: 400px;
        `;
        
        hint.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 18px;">💡</span>
                <div style="flex: 1;">
                    <b>Want auto split-panes?</b> 
                    <a href="#" id="show-split-install" style="color: #60a5fa; text-decoration: underline;">Install helper</a>
                    <span style="color: #64748b; margin-left: 8px; cursor: pointer;" id="dismiss-split-hint">✕</span>
                </div>
            </div>
        `;
        
        document.body.appendChild(hint);
        
        hint.querySelector('#show-split-install').addEventListener('click', (e) => {
            e.preventDefault();
            hint.remove();
            this.showItermSetupHint(editor);
        });
        
        hint.querySelector('#dismiss-split-hint').addEventListener('click', () => {
            localStorage.setItem('iterm_split_hint_shown', 'true');
            hint.remove();
        });
        
        setTimeout(() => hint.remove(), 8000);
    },

    /**
     * Show split-pane notification after copying SSH command
     */
    showSplitPaneNotification(editor, sshCommand, password) {
        const existing = document.getElementById('topology-notification');
        if (existing) existing.remove();
        
        if (!document.getElementById('split-pane-notification-styles')) {
            const style = document.createElement('style');
            style.id = 'split-pane-notification-styles';
            style.textContent = `
                @keyframes slideUp {
                    from { transform: translateX(-50%) translateY(20px); opacity: 0; }
                    to { transform: translateX(-50%) translateY(0); opacity: 1; }
                }
                @keyframes fadeOut {
                    from { opacity: 1; }
                    to { opacity: 0; transform: translateX(-50%) translateY(10px); }
                }
            `;
            document.head.appendChild(style);
        }
        
        const notification = document.createElement('div');
        notification.id = 'topology-notification';
        notification.style.cssText = `
            position: fixed;
            bottom: 60px;
            left: 50%;
            transform: translateX(-50%);
            padding: 16px 24px;
            border-radius: 12px;
            font-size: 14px;
            color: #ffffff;
            z-index: 10000;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            animation: slideUp 0.3s ease-out;
            max-width: 500px;
            text-align: left;
            background: linear-gradient(145deg, #1e3a5f, #0f2744);
            border: 1px solid rgba(59, 130, 246, 0.3);
        `;
        
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="background: #3b82f6; border-radius: 50%; padding: 8px; flex-shrink: 0;">
                    <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" width="20" height="20">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <line x1="12" y1="3" x2="12" y2="21"/>
                    </svg>
                </div>
                <div>
                    <div style="font-weight: 600; margin-bottom: 4px;">SSH command copied! To open in split pane:</div>
                    <div style="color: #93c5fd; font-size: 13px;">
                        <span style="background: rgba(255,255,255,0.15); padding: 2px 8px; border-radius: 4px; font-family: monospace;">⌘D</span>
                        <span style="margin: 0 6px;">→</span>
                        <span style="background: rgba(255,255,255,0.15); padding: 2px 8px; border-radius: 4px; font-family: monospace;">⌘V</span>
                        <span style="margin: 0 6px;">→</span>
                        <span style="background: rgba(255,255,255,0.15); padding: 2px 8px; border-radius: 4px; font-family: monospace;">Enter</span>
                        ${password ? '<span style="margin-left: 12px; color: #fbbf24;">(Password: right-click device)</span>' : ''}
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'fadeOut 0.3s ease-out forwards';
                setTimeout(() => notification.remove(), 300);
            }
        }, 6000);
    },

    /**
     * Show iTerm setup hint dialog
     */
    showItermSetupHint(editor) {
        const overlay = document.createElement('div');
        overlay.id = 'iterm-setup-hint';
        overlay.style.cssText = `
            position: fixed;
            bottom: 100px;
            right: 20px;
            width: 420px;
            background: linear-gradient(145deg, #2d3748, #1a202c);
            border: 1px solid rgba(74, 222, 128, 0.3);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            z-index: 10001;
            color: #e2e8f0;
            font-family: 'Poppins', -apple-system, sans-serif;
        `;
        
        overlay.innerHTML = `
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <div style="background: #4ade80; border-radius: 50%; padding: 8px; flex-shrink: 0;">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#1a202c" stroke-width="2.5" width="20" height="20">
                        <rect x="2" y="3" width="20" height="14" rx="2"/>
                        <polyline points="7,8 9,10 7,12"/>
                        <line x1="11" y1="12" x2="15" y2="12"/>
                    </svg>
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; font-size: 15px; margin-bottom: 8px; color: #4ade80;">
                        🚀 Enable Auto Split-Pane SSH
                    </div>
                    <div style="font-size: 13px; color: #a0aec0; line-height: 1.5; margin-bottom: 12px;">
                        <b>Quick Setup (one-time):</b> Run this in your Mac terminal:
                    </div>
                    <div style="background: #1a202c; border: 1px solid #4a5568; border-radius: 6px; padding: 10px; margin-bottom: 12px; position: relative;">
                        <code id="install-cmd-text" style="font-size: 10px; color: #68d391; word-break: break-all; display: block; padding-right: 30px;">bash <(curl -sL raw.githubusercontent.com/YarelOr-dn/topology-creator/v1.1-dev/install-iterm-helper.sh)</code>
                        <button id="copy-install-cmd" style="position: absolute; right: 6px; top: 50%; transform: translateY(-50%); background: #4a5568; border: none; border-radius: 4px; padding: 4px 8px; color: white; font-size: 10px; cursor: pointer;">Copy</button>
                    </div>
                    <div style="font-size: 12px; color: #a0aec0; margin-bottom: 15px;">
                        Or manually: iTerm2 → Settings → Profiles → General → URL Schemes → check <b>ssh</b>
                    </div>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button id="iterm-hint-installed" style="
                            flex: 1;
                            min-width: 120px;
                            padding: 8px 16px;
                            background: linear-gradient(145deg, #4ade80, #22c55e);
                            border: none;
                            border-radius: 6px;
                            color: #1a202c;
                            font-weight: 600;
                            font-size: 13px;
                            cursor: pointer;
                        ">✓ I've installed it</button>
                        <button id="iterm-hint-ok" style="
                            padding: 8px 16px;
                            background: transparent;
                            border: 1px solid #4a5568;
                            border-radius: 6px;
                            color: #a0aec0;
                            font-size: 13px;
                            cursor: pointer;
                        ">Later</button>
                        <button id="iterm-hint-dismiss" style="
                            padding: 8px 16px;
                            background: transparent;
                            border: 1px solid #4a5568;
                            border-radius: 6px;
                            color: #a0aec0;
                            font-size: 13px;
                            cursor: pointer;
                        ">Don't show</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        const installCmd = 'bash <(curl -sL https://raw.githubusercontent.com/YarelOr-dn/topology-creator/v1.1-dev/install-iterm-helper.sh)';
        overlay.querySelector('#copy-install-cmd').addEventListener('click', (e) => {
            window.safeClipboardWrite(installCmd).then(() => {
                e.target.textContent = '[OK]';
                setTimeout(() => e.target.textContent = 'Copy', 2000);
            });
        });
        
        overlay.querySelector('#iterm-hint-installed').addEventListener('click', () => {
            localStorage.setItem('iterm_helper_installed', 'true');
            localStorage.setItem('iterm_hint_shown', 'true');
            this.showNotification(editor, '🎉 Auto split-pane enabled! Click terminal buttons to test.', 'success');
            overlay.remove();
        });
        
        overlay.querySelector('#iterm-hint-ok').addEventListener('click', () => overlay.remove());
        overlay.querySelector('#iterm-hint-dismiss').addEventListener('click', () => {
            localStorage.setItem('iterm_hint_shown', 'true');
            overlay.remove();
        });
        
        setTimeout(() => {
            if (document.getElementById('iterm-setup-hint')) overlay.remove();
        }, 20000);
    },

    /**
     * Show a temporary notification toast — liquid glass style, bottom-right
     */
    _toastTimer: null,

    showNotification(editor, message, type = 'info') {
        this._addToHistory(message, type);
        if (this._toastTimer) { clearTimeout(this._toastTimer); this._toastTimer = null; }
        const existing = document.getElementById('topology-notification');
        if (existing) existing.remove();

        if (!document.getElementById('toast-anim-styles')) {
            const s = document.createElement('style');
            s.id = 'toast-anim-styles';
            s.textContent = `
                @keyframes glassToastIn {
                    0%   { opacity:0; transform:translateX(-50%) translateY(16px) scale(0.92); }
                    60%  { opacity:1; transform:translateX(-50%) translateY(-3px) scale(1.01); }
                    100% { opacity:1; transform:translateX(-50%) translateY(0) scale(1); }
                }
                @keyframes glassToastOut {
                    0%   { opacity:1; transform:translateX(-50%) translateY(0) scale(1); }
                    100% { opacity:0; transform:translateX(-50%) translateY(10px) scale(0.95); }
                }
                @keyframes glassProgress {
                    from { transform: scaleX(1); }
                    to   { transform: scaleX(0); }
                }
            `;
            document.head.appendChild(s);
        }

        const dk = document.body.classList.contains('dark-mode');
        const notification = document.createElement('div');
        notification.id = 'topology-notification';

        const icons = {
            info:    '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>',
            success: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
            warning: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
            error:   '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>'
        };
        const colors = {
            info:    { accent: '#60a5fa', glow: 'rgba(96,165,250,0.25)',  border: 'rgba(96,165,250,0.3)' },
            success: { accent: '#4ade80', glow: 'rgba(74,222,128,0.25)',  border: 'rgba(74,222,128,0.3)' },
            warning: { accent: '#fbbf24', glow: 'rgba(251,191,36,0.25)', border: 'rgba(251,191,36,0.3)' },
            error:   { accent: '#f87171', glow: 'rgba(248,113,113,0.25)',border: 'rgba(248,113,113,0.3)' }
        };
        const c = colors[type] || colors.info;
        const duration = type === 'error' ? 6000 : type === 'warning' ? 5000 : 4000;

        notification.style.cssText = `
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            padding: 12px 22px 12px 16px;
            border-radius: 14px;
            font-size: 14px;
            color: ${dk ? 'rgba(255,255,255,0.92)' : 'rgba(15,15,30,0.88)'};
            z-index: 10000;
            animation: glassToastIn 0.35s cubic-bezier(0.22,1,0.36,1) forwards;
            background: ${dk
                ? `linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%)`
                : `linear-gradient(135deg, rgba(255,255,255,0.75) 0%, rgba(255,255,255,0.55) 100%)`};
            backdrop-filter: blur(24px) saturate(1.6);
            -webkit-backdrop-filter: blur(24px) saturate(1.6);
            border: 1px solid ${dk ? c.border : 'rgba(255,255,255,0.6)'};
            box-shadow:
                0 8px 32px rgba(0,0,0,${dk ? '0.45' : '0.1'}),
                0 2px 8px ${c.glow},
                inset 0 1px 0 ${dk ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.7)'},
                inset 0 -1px 0 ${dk ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)'};
            max-width: min(600px, 85vw);
            font-family: 'Poppins', -apple-system, sans-serif;
            display: flex;
            align-items: center;
            gap: 10px;
            overflow: hidden;
            cursor: pointer;
        `;

        const iconWrap = document.createElement('span');
        iconWrap.innerHTML = icons[type] || icons.info;
        iconWrap.style.cssText = `
            color: ${c.accent};
            flex-shrink: 0;
            display: flex;
            align-items: center;
            filter: drop-shadow(0 0 4px ${c.glow});
        `;

        const text = document.createElement('span');
        text.textContent = message;
        text.style.cssText = `line-height:1.4; font-weight:500; letter-spacing:0.1px; word-break:break-word;`;

        const progress = document.createElement('div');
        progress.style.cssText = `
            position: absolute;
            bottom: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, ${c.accent}80, ${c.accent}, ${c.accent}80, transparent);
            transform-origin: left;
            animation: glassProgress ${duration}ms linear forwards;
            border-radius: 0 0 14px 14px;
        `;

        notification.appendChild(iconWrap);
        notification.appendChild(text);
        notification.appendChild(progress);
        document.body.appendChild(notification);

        notification.onclick = () => {
            if (this._toastTimer) { clearTimeout(this._toastTimer); this._toastTimer = null; }
            notification.style.animation = 'glassToastOut 0.25s cubic-bezier(0.22,1,0.36,1) forwards';
            setTimeout(() => notification.remove(), 250);
        };

        this._toastTimer = setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'glassToastOut 0.3s cubic-bezier(0.22,1,0.36,1) forwards';
                setTimeout(() => notification.remove(), 300);
            }
            this._toastTimer = null;
        }, duration);
    },

    /**
     * Show validation error toast
     */
    showValidationErrorToast(editor, errors) {
        const existing = document.getElementById('validation-error-toast');
        if (existing) existing.remove();
        
        const toast = document.createElement('div');
        toast.id = 'validation-error-toast';
        toast.style.cssText = `
            position: fixed;
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(145deg, #ef4444, #dc2626);
            border: 1px solid rgba(239, 68, 68, 0.5);
            border-radius: 10px;
            padding: 12px 20px;
            color: white;
            font-size: 13px;
            z-index: 10000;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            max-width: 400px;
        `;
        
        const errorList = errors.map(e => `• ${e}`).join('<br>');
        toast.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 6px;">⚠️ Validation Errors</div>
            <div style="font-size: 12px; opacity: 0.9;">${errorList}</div>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.transition = 'opacity 0.3s';
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }
        }, 5000);
    }
};

(function installApiErrorInterceptor() {
    const _origFetch = window.fetch;
    const _recentErrors = {};
    const SUPPRESS_MS = 10000;
    const API_PATTERN = /^\/api\//;
    const _SILENT_404_EXACT = ['/api/dnaas/interface-details'];
    const _SILENT_404_PREFIX = ['/api/config/', '/api/operations/', '/api/health', '/api/dnaas/enable-lldp/status', '/api/dnaas/device-stack-live'];
    const _SILENT_BRIDGE_PREFIX = ['/api/config/', '/api/operations/', '/api/devices/'];
    const _BRIDGE_UNAVAIL_CODES = new Set([404, 501, 502, 503]);

    window.fetch = async function(...args) {
        const input = args[0];
        const url = typeof input === 'string' ? input : (input?.url || '');

        let resp;
        try {
            resp = await _origFetch.apply(this, args);
        } catch (err) {
            if (API_PATTERN.test(url)) {
                const cleanUrl = url.split('?')[0];
                const isBridgePath = _SILENT_BRIDGE_PREFIX.some(p => cleanUrl.startsWith(p));
                if (!isBridgePath) {
                    _showApiError(url, 0, `Network error: ${err.message}`);
                }
            }
            throw err;
        }

        if (!resp.ok && API_PATTERN.test(url)) {
            const cleanUrl = url.split('?')[0];
            const isSilent = (
                (resp.status === 404 && (
                    _SILENT_404_EXACT.some(p => cleanUrl === p) ||
                    _SILENT_404_PREFIX.some(p => cleanUrl.startsWith(p))
                )) ||
                (_BRIDGE_UNAVAIL_CODES.has(resp.status) &&
                    _SILENT_BRIDGE_PREFIX.some(p => cleanUrl.startsWith(p)))
            );
            if (!isSilent) {
                _showApiError(url, resp.status, resp.statusText);
            }
        }
        return resp;
    };

    function _showApiError(url, status, statusText) {
        const shortPath = url.split('?')[0].replace(/^\/api\//, '');
        const key = `${status}:${shortPath}`;
        const now = Date.now();
        if (_recentErrors[key] && (now - _recentErrors[key]) < SUPPRESS_MS) return;
        _recentErrors[key] = now;

        const dk = document.body.classList.contains('dark-mode');
        const log = document.getElementById('api-error-log');
        if (log) {
            _appendLogEntry(log, shortPath, status, statusText, dk);
            return;
        }

        const container = document.createElement('div');
        container.id = 'api-error-log';
        container.style.cssText = `
            position: fixed; top: 8px; right: 8px; z-index: 9999;
            max-width: 340px; max-height: 220px; overflow-y: auto;
            display: flex; flex-direction: column; gap: 3px;
            pointer-events: auto;
        `;
        document.body.appendChild(container);
        _appendLogEntry(container, shortPath, status, statusText, dk);
    }

    function _appendLogEntry(container, path, status, statusText, dk) {
        const entry = document.createElement('div');
        const statusColor = status >= 500 ? '#f87171' : status >= 400 ? '#fbbf24' : '#60a5fa';
        entry.style.cssText = `
            padding: 5px 10px; border-radius: 6px; font-size: 11px;
            font-family: 'Space Grotesk', 'SF Mono', monospace;
            background: ${dk ? 'rgba(20,20,30,0.88)' : 'rgba(255,255,255,0.92)'};
            border: 1px solid ${dk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'};
            color: ${dk ? '#c8d0da' : '#333'};
            backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            animation: glassToastIn 0.25s ease-out forwards;
            display: flex; align-items: center; gap: 6px;
            cursor: pointer;
        `;
        const badge = `<span style="background:${statusColor};color:#fff;padding:1px 5px;border-radius:3px;font-size:10px;font-weight:700;">${status || 'ERR'}</span>`;
        const pathText = path.length > 35 ? '...' + path.slice(-32) : path;
        entry.innerHTML = `${badge}<span style="opacity:0.8;">${pathText}</span><span style="margin-left:auto;opacity:0.4;font-size:9px;">${statusText}</span>`;
        entry.title = `${status} ${statusText}\n/${path}`;
        entry.addEventListener('click', () => {
            entry.style.transition = 'opacity 0.2s';
            entry.style.opacity = '0';
            setTimeout(() => {
                entry.remove();
                if (container.children.length === 0) container.remove();
            }, 200);
        });
        container.appendChild(entry);

        while (container.children.length > 5) {
            container.removeChild(container.firstChild);
        }

        setTimeout(() => {
            if (entry.parentNode) {
                entry.style.transition = 'opacity 0.3s';
                entry.style.opacity = '0';
                setTimeout(() => {
                    entry.remove();
                    if (container.children.length === 0) container.remove();
                }, 300);
            }
        }, 8000);
    }
})();

console.log('[topology-notifications.js] NotificationManager loaded');
