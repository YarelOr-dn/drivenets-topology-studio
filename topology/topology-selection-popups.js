/**
 * topology-selection-popups.js - Selection Popups and Inline Submenus
 * 
 * Extracted from topology.js for modular architecture.
 * All methods receive 'editor' as first parameter instead of using 'this'.
 */

'use strict';

window.SelectionPopups = {
    /**
     * Position a popup element relative to an anchor rect, clamped to viewport.
     * @param {HTMLElement} popup - The popup element (must be in DOM)
     * @param {{left,top,width,height,bottom,right}} anchor - Anchor bounding rect
     * @param {Object} opts - { margin: 8, prefer: 'bottom' }
     */
    positionPopup(popup, anchor, opts = {}) {
        const margin = opts.margin || 8;
        const pr = popup.getBoundingClientRect();
        let left = anchor.left + anchor.width / 2 - pr.width / 2;
        let top = anchor.bottom + margin;
        if (left < 10) left = 10;
        if (left + pr.width > window.innerWidth - 10) left = window.innerWidth - pr.width - 10;
        if (top + pr.height > window.innerHeight - 10) top = anchor.top - pr.height - margin;
        if (top < 10) top = 10;
        popup.style.left = left + 'px';
        popup.style.top = top + 'px';
    },

    _showToolbarTooltip(editor, btn, title) {
        let tooltip = document.getElementById('tb-active-tooltip');
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = 'tb-active-tooltip';
            document.body.appendChild(tooltip);
        }
        tooltip.textContent = title;
        tooltip.style.cssText = `
            position: fixed;
            background: rgba(15, 15, 20, 0.96);
            color: #fff;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 11px;
            font-weight: 500;
            font-family: 'Poppins', -apple-system, sans-serif;
            white-space: nowrap;
            pointer-events: none;
            z-index: 100000;
            box-shadow: 0 3px 12px rgba(0,0,0,0.4);
            opacity: 1;
            visibility: visible;
        `;
        const btnRect = btn.getBoundingClientRect();
        tooltip.style.left = `${btnRect.left + btnRect.width / 2}px`;
        tooltip.style.top = `${btnRect.top - 8}px`;
        tooltip.style.transform = 'translate(-50%, -100%)';
    },

    _hideToolbarTooltip(editor) {
        const tooltip = document.getElementById('tb-active-tooltip');
        if (tooltip) {
            tooltip.style.opacity = '0';
            tooltip.style.visibility = 'hidden';
        }
    },

    _showLldpInlineSubmenu(editor, lldpBtn, device, serial, sshConfig, toolbar, isDarkMode, iconColor, hoverBg) {
        // Close the other submenu if open
        const otherSubmenu = document.getElementById('stack-inline-submenu');
        if (otherSubmenu) otherSubmenu.remove();

        // Remove existing submenu
        const existing = document.getElementById('lldp-inline-submenu');
        if (existing) {
            existing.remove();
            return; // Toggle off
        }
        
        const isLldpRunning = device._lldpRunning || device._lldpAnimating;
        const hasLldpData = device.lldpEnabled || device.lldpDiscoveryComplete;
        const hasNewResults = device._lldpNewResults;
        
        // Create submenu with same styling as toolbar
        const submenu = document.createElement('div');
        submenu.id = 'lldp-inline-submenu';
        const glassBg = isDarkMode ? 'rgba(15, 15, 25, 0.25)' : 'rgba(255, 255, 255, 0.25)';
        const glassBorder = isDarkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.08)';
        const glassShadow = isDarkMode 
            ? '0 4px 30px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.08)'
            : '0 4px 30px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.5)';
        
        submenu.style.cssText = `
            position: fixed;
            z-index: 100001;
            background: ${glassBg};
            border: 1px solid ${glassBorder};
            border-radius: 10px;
            padding: 4px;
            box-shadow: ${glassShadow};
            backdrop-filter: blur(24px) saturate(200%);
            -webkit-backdrop-filter: blur(24px) saturate(200%);
            display: flex;
            gap: 2px;
            align-items: center;
            animation: lldpSubmenuFadeIn 0.15s ease forwards;
        `;
        
        // Add animation
        if (!document.getElementById('lldp-submenu-style')) {
            const style = document.createElement('style');
            style.id = 'lldp-submenu-style';
            style.textContent = `@keyframes lldpSubmenuFadeIn { from { opacity: 0; transform: translateY(-5px); } to { opacity: 1; transform: translateY(0); } }`;
            document.head.appendChild(style);
        }
        
        // Create submenu button helper
        const createSubBtn = (icon, tooltip, onClick, isActive = false, isDisabled = false) => {
            const btn = document.createElement('button');
            const activeColor = isActive ? '#27ae60' : iconColor;
            const activeBg = isActive ? 'rgba(39, 174, 96, 0.15)' : 'transparent';
            btn.style.cssText = `
                width: 28px;
                height: 28px;
                padding: 0;
                border: none;
                background: ${activeBg};
                border-radius: 6px;
                cursor: ${isDisabled ? 'default' : 'pointer'};
                color: ${isDisabled ? 'rgba(128,128,128,0.5)' : activeColor};
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.12s ease;
                opacity: ${isDisabled ? '0.5' : '1'};
            `;
            btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">${icon}</svg>`;
            btn.onmouseenter = () => {
                if (!isDisabled) {
                    btn.style.background = isActive ? 'rgba(39, 174, 96, 0.25)' : hoverBg;
                    btn.style.transform = 'scale(1.12)';
                }
                editor._showToolbarTooltip(btn, tooltip);
            };
            btn.onmouseleave = () => {
                btn.style.background = activeBg;
                btn.style.transform = 'scale(1)';
                editor._hideToolbarTooltip();
            };
            btn.onmousedown = (e) => { e.stopPropagation(); e.preventDefault(); };
            btn.onclick = (e) => {
                e.stopPropagation();
                e.preventDefault();
                if (!isDisabled) {
                    editor._hideToolbarTooltip();
                    submenu.remove();
                    onClick();
                }
            };
            return btn;
        };
        
        // Enable LLDP button
        let enableTooltip = isLldpRunning ? 'LLDP scanning...' : (hasLldpData ? 'LLDP enabled (re-scan)' : 'Enable LLDP');
        const enableIcon = isLldpRunning 
            ? '<circle cx="12" cy="12" r="10" stroke-dasharray="31.4" stroke-dashoffset="0"><animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/></circle>'
            : '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>';
        submenu.appendChild(createSubBtn(
            enableIcon,
            enableTooltip,
            () => {
                if (serial) {
                    editor.enableLldpBackground(device, serial, sshConfig);
                    editor.hideDeviceSelectionToolbar();
                } else {
                    editor.showToast('No SSH address configured', 'error');
                }
            },
            hasNewResults && !isLldpRunning,
            isLldpRunning
        ));
        
        // LLDP Table button
        submenu.appendChild(createSubBtn(
            '<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>',
            'LLDP Table',
            () => {
                editor.hideDeviceSelectionToolbar();
                editor.showLldpTableDialog(device, serial);
            },
            hasNewResults
        ));
        
        submenu.addEventListener('keydown', (e) => { e.stopPropagation(); });
        submenu.addEventListener('keyup', (e) => { e.stopPropagation(); });
        document.body.appendChild(submenu);
        SelectionPopups.positionPopup(submenu, lldpBtn.getBoundingClientRect(), { margin: 6 });
        
        // Close on click outside
        const closeHandler = (e) => {
            if (!submenu.contains(e.target) && e.target !== lldpBtn) {
                submenu.remove();
                document.removeEventListener('mousedown', closeHandler);
            }
        };
        setTimeout(() => document.addEventListener('mousedown', closeHandler), 10);
    },

    _showSystemStackInlineSubmenu(editor, stackBtn, device, serial, sshConfig, toolbar, isDarkMode, iconColor, hoverBg) {
        // Close the other submenu if open
        const otherSubmenu = document.getElementById('lldp-inline-submenu');
        if (otherSubmenu) otherSubmenu.remove();

        const existing = document.getElementById('stack-inline-submenu');
        if (existing) {
            existing.remove();
            return;
        }
        const submenu = document.createElement('div');
        submenu.id = 'stack-inline-submenu';
        const glassBg = isDarkMode ? 'rgba(15, 15, 25, 0.25)' : 'rgba(255, 255, 255, 0.25)';
        const glassBorder = isDarkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.08)';
        const glassShadow = isDarkMode
            ? '0 4px 30px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.08)'
            : '0 4px 30px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.5)';
        submenu.style.cssText = `
            position: fixed;
            z-index: 100001;
            background: ${glassBg};
            border: 1px solid ${glassBorder};
            border-radius: 10px;
            padding: 4px;
            box-shadow: ${glassShadow};
            backdrop-filter: blur(24px) saturate(200%);
            -webkit-backdrop-filter: blur(24px) saturate(200%);
            display: flex;
            gap: 2px;
            align-items: center;
            animation: lldpSubmenuFadeIn 0.15s ease forwards;
        `;
        const _anchorRect = { left: 0, top: 0, width: 0, height: 0, right: 0, bottom: 0 };
        const _captureAnchor = () => {
            const el = document.getElementById('stack-inline-submenu') || stackBtn;
            if (el) {
                const r = el.getBoundingClientRect();
                _anchorRect.left = r.left; _anchorRect.top = r.top;
                _anchorRect.width = r.width; _anchorRect.height = r.height;
                _anchorRect.right = r.right; _anchorRect.bottom = r.bottom;
            }
        };
        const createSubBtn = (icon, tooltip, onClick, isActive = false, isDisabled = false) => {
            const btn = document.createElement('button');
            const activeColor = isActive ? '#27ae60' : iconColor;
            const activeBg = isActive ? 'rgba(39, 174, 96, 0.15)' : 'transparent';
            btn.style.cssText = `
                width: 28px; height: 28px; padding: 0; border: none;
                background: ${activeBg}; border-radius: 6px;
                cursor: ${isDisabled ? 'default' : 'pointer'};
                color: ${isDisabled ? 'rgba(128,128,128,0.5)' : activeColor};
                display: flex; align-items: center; justify-content: center;
                transition: all 0.12s ease; opacity: ${isDisabled ? '0.5' : '1'};
            `;
            btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">${icon}</svg>`;
            btn.onmouseenter = () => {
                if (!isDisabled) { btn.style.background = isActive ? 'rgba(39, 174, 96, 0.25)' : hoverBg; btn.style.transform = 'scale(1.12)'; }
                editor._showToolbarTooltip(btn, tooltip);
            };
            btn.onmouseleave = () => { btn.style.background = activeBg; btn.style.transform = 'scale(1)'; editor._hideToolbarTooltip(); };
            btn.onmousedown = (e) => { e.stopPropagation(); e.preventDefault(); };
            btn.onclick = (e) => {
                e.stopPropagation();
                e.preventDefault();
                if (!isDisabled) {
                    editor._hideToolbarTooltip();
                    _captureAnchor();
                    submenu.remove();
                    const result = onClick();
                    if (result && typeof result.catch === 'function') {
                        result.catch(err => {
                            console.error('[SystemStack submenu]', err);
                            if (editor.showToast) editor.showToast(`Error: ${err.message}`, 'error');
                        });
                    }
                }
            };
            return btn;
        };
        const _isUpgrading = !!(device._upgradeInProgress || device._activeUpgradeJob);
        const _hasStack = !!(device._stackData?.components?.length);
        const _mode = (device._deviceMode || '').toUpperCase();
        const _isGiEmpty = (_mode === 'GI' || _mode === 'BASEOS_SHELL') && !_hasStack;
        const _upgradeTooltip = _isUpgrading
            ? 'Upgrade Stack (upgrade in progress)'
            : 'Upgrade Stack';
        const _stackTableTooltip = _isGiEmpty
            ? 'Stack Table (empty -- device in ' + (_mode || 'GI') + ' mode)'
            : (_isUpgrading ? 'Stack Table (upgrade in progress)' : 'Stack Table');

        submenu.appendChild(createSubBtn(
            '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M17 8l-5-5-5 5"/><path d="M12 3v12"/>',
            _upgradeTooltip,
            () => {
                editor.hideDeviceSelectionToolbar();
                if (window.ScalerGUI && window.ScalerGUI.openUpgradeWizard) {
                    window.ScalerGUI.openUpgradeWizard({ deviceId: device.label || serial });
                } else if (editor.showToast) {
                    editor.showToast('Scaler GUI not available', 'error');
                }
            },
            _isUpgrading
        ));
        submenu.appendChild(createSubBtn(
            '<rect x="4" y="4" width="16" height="4" rx="1"/><rect x="4" y="10" width="16" height="4" rx="1"/><rect x="4" y="16" width="16" height="4" rx="1"/>',
            _stackTableTooltip,
            () => {
                editor.hideDeviceSelectionToolbar();
                if (_isGiEmpty) {
                    if (editor.showToast) editor.showToast(`Device has empty stack (${_mode || 'GI'} mode) -- no stack data to show`, 'warning');
                    return;
                }
                if (editor.showSystemStackDialog) editor.showSystemStackDialog(device, serial);
                else if (editor.showToast) editor.showToast('Stack dialog not available', 'error');
            },
            false,
            false
        ));
        const _gitDisabled = _isUpgrading || _isGiEmpty;
        const _gitTooltip = _isUpgrading
            ? 'Git Commit (unavailable -- upgrade in progress)'
            : (_isGiEmpty ? 'Git Commit (unavailable -- device in ' + (_mode || 'GI') + ' mode)' : 'Git Commit');
        submenu.appendChild(createSubBtn(
            '<path d="M6 3v12"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/>',
            _gitTooltip,
            async () => {
                const host = sshConfig?.host || serial;
                if (!host) {
                    if (editor.showToast) editor.showToast('No SSH address configured', 'error');
                    return;
                }
                const existing = document.getElementById('git-commit-popup');
                if (existing) existing.remove();

                const popup = document.createElement('div');
                popup.id = 'git-commit-popup';
                popup.style.cssText = `
                    position: fixed; z-index: 100003;
                    min-width: 280px; max-width: 420px;
                    background: rgba(20,25,35,0.95);
                    border: 1px solid rgba(255,255,255,0.12);
                    border-radius: 12px;
                    padding: 0;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
                    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                `;
                const cachedHash = (device._gitCommit !== undefined && device._gitCommit !== null && device._gitCommit !== '') ? device._gitCommit : null;
                const cachedTs = cachedHash ? device._gitCommitFetchedAt : null;
                const _fmtTs = (ts) => { if (!ts) return ''; const d = new Date(ts); return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }); };
                const tsStr = _fmtTs(cachedTs);
                const hashEsc = (cachedHash || '').replace(/</g, '&lt;').replace(/"/g, '&quot;');
                popup.innerHTML = `
                    <div id="git-commit-header" style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px 6px; cursor: move; user-select: none;">
                        <span id="git-commit-title" style="color: rgba(255,255,255,0.6); font-size: 11px;">Git Commit${tsStr ? ' - ' + tsStr : ''}</span>
                        <span style="display: flex; gap: 4px;">
                            <button id="git-commit-refresh" type="button" style="
                                background: rgba(0, 180, 216, 0.15);
                                border: 1px solid rgba(0, 180, 216, 0.3);
                                border-radius: 6px;
                                width: 28px; height: 28px; padding: 0;
                                cursor: pointer;
                                display: flex; align-items: center; justify-content: center;
                                transition: all 0.15s;
                            " title="Refresh via live SSH">
                                <svg id="git-commit-refresh-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#00B4D8" stroke-width="2.5" style="transition: transform 0.3s;">
                                    <path d="M23 4v6h-6"/><path d="M1 20v-6h6"/>
                                    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                                </svg>
                            </button>
                            <button id="git-commit-close" type="button" style="
                                background: rgba(255, 255, 255, 0.1);
                                border: none;
                                border-radius: 6px;
                                width: 28px; height: 28px; padding: 0;
                                cursor: pointer;
                                display: flex; align-items: center; justify-content: center;
                                transition: background 0.15s;
                            " title="Close">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" stroke-width="2"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
                            </button>
                        </span>
                    </div>
                    <div style="padding: 0 14px 12px;">
                        <div id="git-commit-body" style="position: relative; background: rgba(0,0,0,0.35); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 10px 36px 10px 12px; font-family: Monaco, Menlo, Consolas, monospace; font-size: 12px; color: rgba(255,255,255,0.9); word-break: break-all;">
                            ${cachedHash ? hashEsc : '<span style="color: rgba(255,255,255,0.5);">Fetching via live SSH...</span>'}
                            <button id="git-commit-copy" type="button" style="position: absolute; top: 8px; right: 8px; width: 24px; height: 24px; padding: 0; background: transparent; border: none; cursor: pointer; color: rgba(255,255,255,0.5); display: flex; align-items: center; justify-content: center; ${cachedHash ? '' : 'display:none;'}" title="Copy">
                                <svg width="14" height="14" viewBox="0 0 24 24"><use href="#ico-copy"/></svg>
                            </button>
                        </div>
                        <div id="git-commit-error" style="color: #e74c3c; font-size: 11px; margin-top: 8px; display: none;"></div>
                    </div>
                `;
                document.body.appendChild(popup);
                SelectionPopups.positionPopup(popup, _anchorRect);

                // Draggable by header
                let _isDragging = false, _startX, _startY, _startLeft, _startTop;
                const headerEl = popup.querySelector('#git-commit-header');
                headerEl.addEventListener('mousedown', (e) => {
                    if (e.target.closest('button')) return;
                    _isDragging = true;
                    const r = popup.getBoundingClientRect();
                    _startX = e.clientX; _startY = e.clientY;
                    _startLeft = r.left; _startTop = r.top;
                    popup.style.transform = 'none';
                    popup.style.left = _startLeft + 'px';
                    popup.style.top = _startTop + 'px';
                });
                const _onMove = (e) => {
                    if (!_isDragging) return;
                    popup.style.left = (_startLeft + e.clientX - _startX) + 'px';
                    popup.style.top = (_startTop + e.clientY - _startY) + 'px';
                };
                const _onUp = () => { _isDragging = false; };
                document.addEventListener('mousemove', _onMove);
                document.addEventListener('mouseup', _onUp);

                // Inject spin keyframe if not present
                if (!document.getElementById('git-commit-spin-style')) {
                    const s = document.createElement('style');
                    s.id = 'git-commit-spin-style';
                    s.textContent = '@keyframes gitCommitSpin { to { transform: rotate(360deg); } }';
                    document.head.appendChild(s);
                }

                // Refresh button hover
                const _refreshBtn = popup.querySelector('#git-commit-refresh');
                const _refreshIcon = popup.querySelector('#git-commit-refresh-icon');
                _refreshBtn.addEventListener('mouseenter', () => {
                    _refreshBtn.style.background = 'rgba(0, 180, 216, 0.3)';
                    _refreshBtn.style.borderColor = 'rgba(0, 180, 216, 0.5)';
                });
                _refreshBtn.addEventListener('mouseleave', () => {
                    _refreshBtn.style.background = 'rgba(0, 180, 216, 0.15)';
                    _refreshBtn.style.borderColor = 'rgba(0, 180, 216, 0.3)';
                });

                // Close button hover
                const _closeBtn = popup.querySelector('#git-commit-close');
                _closeBtn.addEventListener('mouseenter', () => { _closeBtn.style.background = 'rgba(231, 76, 60, 0.3)'; });
                _closeBtn.addEventListener('mouseleave', () => { _closeBtn.style.background = 'rgba(255, 255, 255, 0.1)'; });

                let lastRefreshAbort = null;
                const doClose = () => {
                    if (lastRefreshAbort) lastRefreshAbort.abort();
                    document.removeEventListener('mousemove', _onMove);
                    document.removeEventListener('mouseup', _onUp);
                    popup.remove();
                };
                popup.querySelector('#git-commit-close').onclick = doClose;

                const _wireCopy = (hashVal) => {
                    const copyBtn = popup.querySelector('#git-commit-copy');
                    if (!copyBtn) return;
                    copyBtn.style.display = hashVal ? 'flex' : 'none';
                    copyBtn.onclick = () => {
                        const text = hashVal || '';
                        const svg = copyBtn.querySelector('svg use');
                        const onCopied = () => {
                            if (editor.showToast) editor.showToast('Copied to clipboard', 'success');
                            if (svg) svg.setAttribute('href', '#ico-check');
                            copyBtn.style.color = 'rgba(39,174,96,0.9)';
                            setTimeout(() => { if (svg) svg.setAttribute('href', '#ico-copy'); copyBtn.style.color = 'rgba(255,255,255,0.5)'; }, 1500);
                        };
                        (typeof safeClipboardWrite === 'function' ? safeClipboardWrite(text) : navigator.clipboard.writeText(text)).then(onCopied).catch(() => {});
                    };
                };
                if (cachedHash) _wireCopy(cachedHash);

                const _updateBody = (hashVal, error) => {
                    const bodyEl = popup.querySelector('#git-commit-body');
                    const errEl = popup.querySelector('#git-commit-error');
                    const titleEl = popup.querySelector('#git-commit-title');
                    if (!bodyEl) return;
                    const hEsc = (hashVal || '').replace(/</g, '&lt;').replace(/"/g, '&quot;');
                    bodyEl.innerHTML = `${hEsc || '(empty)'}<button id="git-commit-copy" type="button" style="position: absolute; top: 8px; right: 8px; width: 24px; height: 24px; padding: 0; background: transparent; border: none; cursor: pointer; color: rgba(255,255,255,0.5); display: flex; align-items: center; justify-content: center;" title="Copy"><svg width="14" height="14" viewBox="0 0 24 24"><use href="#ico-copy"/></svg></button>`;
                    _wireCopy(hashVal);
                    if (error) { errEl.textContent = error; errEl.style.display = 'block'; }
                    else { errEl.style.display = 'none'; }
                    if (device._gitCommitFetchedAt) {
                        titleEl.textContent = 'Git Commit - ' + _fmtTs(device._gitCommitFetchedAt);
                    }
                };

                const _doFetch = async () => {
                    const bodyEl = popup.querySelector('#git-commit-body');
                    const errEl = popup.querySelector('#git-commit-error');
                    const refreshBtn = popup.querySelector('#git-commit-refresh');
                    const refreshIcon = popup.querySelector('#git-commit-refresh-icon');
                    if (lastRefreshAbort) lastRefreshAbort.abort();
                    lastRefreshAbort = new AbortController();
                    const signal = lastRefreshAbort.signal;
                    if (refreshBtn) { refreshBtn.disabled = true; refreshBtn.style.opacity = '0.5'; }
                    if (refreshIcon) refreshIcon.style.animation = 'gitCommitSpin 1s linear infinite';
                    if (errEl) errEl.style.display = 'none';
                    bodyEl.innerHTML = '<span style="color: rgba(255,255,255,0.5);">Fetching git commit...</span>';
                    const deviceIdNow = device?.label || device?.deviceSerial || serial || host;
                    try {
                        let newHash = null;
                        if (typeof ScalerAPI !== 'undefined' && ScalerAPI.getDeviceGitCommit) {
                            if (signal.aborted) throw new DOMException('Aborted', 'AbortError');
                            const res = await ScalerAPI.getDeviceGitCommit(deviceIdNow, host, sshConfig?.user || '', sshConfig?.password || '');
                            newHash = res?.git_commit;
                        }
                        if (newHash == null) {
                            if (signal.aborted) throw new DOMException('Aborted', 'AbortError');
                            const _timer = setTimeout(() => lastRefreshAbort?.abort(), 50000);
                            const resp = await fetch('/api/dnaas/device-gitcommit', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ serial: serial || host, ssh_host: host, ssh_user: sshConfig?.user || 'dnroot', ssh_password: sshConfig?.password || 'dnroot' }),
                                signal
                            }).finally(() => clearTimeout(_timer));
                            const data = resp.ok ? await resp.json().catch(() => ({})) : {};
                            newHash = data?.git_commit;
                            if (!resp.ok) throw new Error(data?.detail || `HTTP ${resp.status}`);
                        }
                        if (newHash != null) {
                            device._gitCommit = newHash;
                            device._gitCommitFetchedAt = Date.now();
                            if (editor.requestDraw) editor.requestDraw();
                        }
                        _updateBody(newHash, null);
                    } catch (e) {
                        if (e?.name !== 'AbortError') {
                            _updateBody(device?._gitCommit || null, e?.message || 'Failed to fetch');
                        }
                    } finally {
                        if (refreshBtn) { refreshBtn.disabled = false; refreshBtn.style.opacity = '1'; }
                        if (refreshIcon) refreshIcon.style.animation = 'none';
                    }
                };

                popup.querySelector('#git-commit-refresh').onclick = _doFetch;

                if (!cachedHash) _doFetch();
            },
            false,
            _gitDisabled
        ));
        submenu.addEventListener('keydown', (e) => { e.stopPropagation(); });
        submenu.addEventListener('keyup', (e) => { e.stopPropagation(); });
        document.body.appendChild(submenu);
        SelectionPopups.positionPopup(submenu, stackBtn.getBoundingClientRect(), { margin: 6 });
        const closeHandler = (e) => {
            if (!submenu.contains(e.target) && e.target !== stackBtn) {
                submenu.remove();
                document.removeEventListener('mousedown', closeHandler);
            }
        };
        setTimeout(() => document.addEventListener('mousedown', closeHandler), 10);
    },

    showDeviceStylePalette(editor, device) {
        const existing = document.getElementById('device-style-palette-popup');
        if (existing) { existing.remove(); return; }
        
        const toolbar = editor._deviceSelectionToolbar;
        if (!toolbar) return;
        
        const toolbarRect = toolbar.getBoundingClientRect();
        const isDark = editor.darkMode;
        const textC = isDark ? 'rgba(255,255,255,0.9)' : 'rgba(30,30,50,0.85)';
        const dimC = isDark ? 'rgba(255,255,255,0.5)' : 'rgba(30,30,50,0.45)';
        
        const popup = document.createElement('div');
        popup.id = 'device-style-palette-popup';
        popup.style.cssText = `
            position: fixed;
            left: ${toolbarRect.left + toolbarRect.width / 2}px;
            top: ${toolbarRect.bottom + 8}px;
            transform: translateX(-50%);
            z-index: 100001;
            background: ${isDark
                ? 'linear-gradient(135deg, rgba(15,15,25,0.35) 0%, rgba(15,15,25,0.25) 50%, rgba(15,15,25,0.20) 100%)'
                : 'linear-gradient(135deg, rgba(255,255,255,0.50) 0%, rgba(255,255,255,0.35) 50%, rgba(255,255,255,0.28) 100%)'};
            border: 1px solid ${isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.08)'};
            border-radius: 14px;
            padding: 10px;
            box-shadow: ${isDark
                ? '0 8px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.08), inset 0 0 0 0.5px rgba(255,255,255,0.05)'
                : '0 8px 32px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.6)'};
            backdrop-filter: blur(24px) saturate(200%);
            -webkit-backdrop-filter: blur(24px) saturate(200%);
            display: flex;
            flex-direction: column;
            gap: 6px;
            font-family: 'Poppins', -apple-system, sans-serif;
        `;

        const title = document.createElement('div');
        title.textContent = 'Device Shape';
        title.style.cssText = `font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: ${dimC}; text-align: center; margin-bottom: 2px;`;
        popup.appendChild(title);

        const grid = document.createElement('div');
        grid.style.cssText = 'display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px;';
        
        const styles = [
            { id: 'circle', name: 'Circle' },
            { id: 'classic', name: 'Cylinder' },
            { id: 'simple', name: 'Simple' },
            { id: 'server', name: 'Server' },
            { id: 'hex', name: 'Hexagon' }
        ];

        const _renderStylePreview = (canvas, styleId, color, dark) => {
            const ctx = canvas.getContext('2d');
            const dpr = window.devicePixelRatio || 1;
            const w = 40, h = 28;
            canvas.width = w * dpr; canvas.height = h * dpr;
            canvas.style.width = w + 'px'; canvas.style.height = h + 'px';
            ctx.scale(dpr, dpr);
            ctx.clearRect(0, 0, w, h);
            const r = 11;
            const fakeDevice = { x: w / 2, y: h / 2, radius: r, color: color, rotation: 0, visualStyle: styleId, deviceType: 'router' };
            const fakeEditor = {
                ctx, darkMode: dark,
                defaultDeviceFontFamily: 'Inter, sans-serif'
            };
            try {
                const DS = window.DeviceStyles;
                if (!DS) return;
                switch (styleId) {
                    case 'circle': DS.drawDeviceCircle(fakeEditor, fakeDevice, false); break;
                    case 'classic': DS.drawDeviceClassicRouter(fakeEditor, fakeDevice, false); break;
                    case 'simple': DS.drawDeviceSimpleRouter(fakeEditor, fakeDevice, false); break;
                    case 'server': DS.drawDeviceServerTower(fakeEditor, fakeDevice, false); break;
                    case 'hex': DS.drawDeviceHexRouter(fakeEditor, fakeDevice, false); break;
                }
            } catch (_) {}
        };
        
        styles.forEach(style => {
            const btn = document.createElement('button');
            const isActive = (device.visualStyle || 'circle') === style.id;
            const activeBg = isDark ? 'rgba(52,152,219,0.20)' : 'rgba(52,152,219,0.15)';
            const activeBorder = 'rgba(52,152,219,0.5)';
            const inactiveBg = isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)';
            const inactiveBorder = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';

            const miniCanvas = document.createElement('canvas');
            _renderStylePreview(miniCanvas, style.id, device.color || '#3498db', isDark);
            
            const label = document.createElement('span');
            label.textContent = style.name;
            label.style.cssText = 'font-size:9px; opacity:0.7;';

            btn.appendChild(miniCanvas);
            btn.appendChild(label);
            btn.style.cssText = `
                width: 62px; height: 50px;
                border: 1px solid ${isActive ? activeBorder : inactiveBorder};
                background: ${isActive ? activeBg : inactiveBg};
                color: ${isActive ? '#3498db' : textC};
                border-radius: 8px; cursor: pointer;
                transition: all 0.15s ease;
                display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px;
                font-family: inherit;
            `;
            btn.onmouseenter = () => {
                if (!isActive) {
                    btn.style.background = isDark ? 'rgba(255,255,255,0.10)' : 'rgba(0,0,0,0.06)';
                    btn.style.borderColor = isDark ? 'rgba(255,255,255,0.20)' : 'rgba(0,0,0,0.12)';
                    btn.style.transform = 'scale(1.04)';
                }
            };
            btn.onmouseleave = () => {
                if (!isActive) {
                    btn.style.background = inactiveBg;
                    btn.style.borderColor = inactiveBorder;
                    btn.style.transform = 'scale(1)';
                }
            };
            btn.onclick = () => {
                device.visualStyle = style.id;
                if (editor.reconnectLinksToDevice) editor.reconnectLinksToDevice(device);
                editor.saveState();
                editor.draw();
                popup.remove();
                setTimeout(() => editor.showDeviceSelectionToolbar(device), 50);
            };
            grid.appendChild(btn);
        });
        popup.appendChild(grid);
        
        popup.addEventListener('mousedown', (e) => e.stopPropagation());
        popup.addEventListener('click', (e) => e.stopPropagation());

        const closeOnOutside = (e) => {
            if (!popup.contains(e.target) && !e.target.closest('#device-selection-toolbar')) {
                popup.remove();
                document.removeEventListener('mousedown', closeOnOutside);
            }
        };
        setTimeout(() => document.addEventListener('mousedown', closeOnOutside), 100);
        
        popup.addEventListener('keydown', (e) => { e.stopPropagation(); });
        popup.addEventListener('keyup', (e) => { e.stopPropagation(); });
        document.body.appendChild(popup);

        requestAnimationFrame(() => {
            const pr = popup.getBoundingClientRect();
            if (pr.right > window.innerWidth - 8) popup.style.left = `${window.innerWidth - pr.width / 2 - 8}px`;
            if (pr.left < 8) popup.style.left = `${pr.width / 2 + 8}px`;
            if (pr.bottom > window.innerHeight - 8) {
                const availBelow = window.innerHeight - toolbarRect.bottom - 16;
                if (availBelow >= 120) {
                    popup.style.maxHeight = `${availBelow}px`;
                    popup.style.overflowY = 'auto';
                } else {
                    popup.style.top = `${toolbarRect.bottom + 4}px`;
                    popup.style.maxHeight = `${window.innerHeight - toolbarRect.bottom - 12}px`;
                    popup.style.overflowY = 'auto';
                }
            }
        });
    },

    showLinkWidthSlider(editor, link) {
        const existing = document.getElementById('link-width-slider-popup');
        if (existing) { existing.remove(); return; }
        
        const toolbar = editor._linkSelectionToolbar;
        if (!toolbar) return;
        
        const toolbarRect = toolbar.getBoundingClientRect();
        const isDark = editor.darkMode;
        
        const popup = document.createElement('div');
        popup.id = 'link-width-slider-popup';
        popup.style.cssText = `
            position: fixed;
            left: ${toolbarRect.left + toolbarRect.width / 2}px;
            top: ${toolbarRect.bottom + 8}px;
            transform: translateX(-50%);
            z-index: 10000;
            background: ${isDark
                ? 'linear-gradient(135deg, rgba(15,15,25,0.35) 0%, rgba(15,15,25,0.25) 50%, rgba(15,15,25,0.20) 100%)'
                : 'linear-gradient(135deg, rgba(255,255,255,0.50) 0%, rgba(255,255,255,0.35) 50%, rgba(255,255,255,0.28) 100%)'};
            border: 1px solid ${isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.08)'};
            border-radius: 14px;
            padding: 12px 16px;
            box-shadow: ${isDark
                ? '0 8px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.08)'
                : '0 8px 32px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.6)'};
            backdrop-filter: blur(24px) saturate(200%);
            -webkit-backdrop-filter: blur(24px) saturate(200%);
            min-width: 150px;
            font-family: 'Poppins', -apple-system, sans-serif;
        `;
        
        const label = document.createElement('div');
        label.style.cssText = `color: ${isDark ? 'rgba(255,255,255,0.8)' : 'rgba(30,30,50,0.7)'}; font-size: 10px; font-weight: 500; margin-bottom: 8px; text-align: center; text-transform: uppercase; letter-spacing: 0.5px;`;
        label.textContent = `Width: ${link.width || 2}px`;
        
        const slider = document.createElement('input');
        slider.type = 'range';
        slider.min = '1';
        slider.max = '10';
        slider.value = link.width || 2;
        slider.style.cssText = 'width: 100%; accent-color: #3498db;';
        
        slider.oninput = () => {
            link.width = parseInt(slider.value);
            label.textContent = `Width: ${link.width}px`;
            editor.draw();
        };
        slider.onchange = () => {
            editor.saveState();
        };
        
        popup.appendChild(label);
        popup.appendChild(slider);
        
        popup.addEventListener('mousedown', (e) => e.stopPropagation());
        popup.addEventListener('click', (e) => e.stopPropagation());
        popup.addEventListener('keydown', (e) => { e.stopPropagation(); });
        popup.addEventListener('keyup', (e) => { e.stopPropagation(); });
        
        document.body.appendChild(popup);
    },

    showLinkStyleOptions(editor, link) {
        const existing = document.getElementById('link-style-options-popup');
        if (existing) { existing.remove(); return; }
        
        const toolbar = editor._linkSelectionToolbar;
        if (!toolbar) return;
        
        const toolbarRect = toolbar.getBoundingClientRect();
        const isDark = editor.darkMode;
        const textC = isDark ? 'rgba(255,255,255,0.9)' : 'rgba(30,30,50,0.85)';
        
        const popup = document.createElement('div');
        popup.id = 'link-style-options-popup';
        popup.style.cssText = `
            position: fixed;
            left: ${toolbarRect.left + toolbarRect.width / 2}px;
            top: ${toolbarRect.bottom + 8}px;
            transform: translateX(-50%);
            z-index: 10000;
            background: ${isDark
                ? 'linear-gradient(135deg, rgba(15,15,25,0.35) 0%, rgba(15,15,25,0.25) 50%, rgba(15,15,25,0.20) 100%)'
                : 'linear-gradient(135deg, rgba(255,255,255,0.50) 0%, rgba(255,255,255,0.35) 50%, rgba(255,255,255,0.28) 100%)'};
            border: 1px solid ${isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.08)'};
            border-radius: 14px;
            padding: 8px;
            box-shadow: ${isDark
                ? '0 8px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.08)'
                : '0 8px 32px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.6)'};
            backdrop-filter: blur(24px) saturate(200%);
            -webkit-backdrop-filter: blur(24px) saturate(200%);
            display: flex;
            flex-direction: column;
            gap: 4px;
            font-family: 'Poppins', -apple-system, sans-serif;
        `;
        
        const styles = ['solid', 'dashed', 'dotted', 'arrow', 'double-arrow'];
        const activeBg = isDark ? 'rgba(52,152,219,0.20)' : 'rgba(52,152,219,0.15)';
        const activeBorder = 'rgba(52,152,219,0.5)';
        const inactiveBg = isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)';
        const inactiveBorder = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';
        
        styles.forEach(style => {
            const btn = document.createElement('button');
            const isActive = (link.style || 'solid') === style;
            btn.textContent = style.charAt(0).toUpperCase() + style.slice(1).replace('-', ' ');
            btn.style.cssText = `
                padding: 6px 12px;
                border: 1px solid ${isActive ? activeBorder : inactiveBorder};
                background: ${isActive ? activeBg : inactiveBg};
                color: ${isActive ? '#3498db' : textC};
                border-radius: 7px;
                cursor: pointer;
                font-size: 11px;
                font-family: inherit;
                text-align: left;
                transition: all 0.15s ease;
            `;
            btn.onmouseenter = () => {
                if (!isActive) { btn.style.background = isDark ? 'rgba(255,255,255,0.10)' : 'rgba(0,0,0,0.06)'; btn.style.borderColor = isDark ? 'rgba(255,255,255,0.18)' : 'rgba(0,0,0,0.10)'; }
            };
            btn.onmouseleave = () => {
                if (!isActive) { btn.style.background = inactiveBg; btn.style.borderColor = inactiveBorder; }
            };
            btn.onclick = () => {
                link.style = style;
                editor.saveState();
                editor.draw();
                popup.remove();
            };
            popup.appendChild(btn);
        });
        
        popup.addEventListener('mousedown', (e) => e.stopPropagation());
        popup.addEventListener('click', (e) => e.stopPropagation());
        popup.addEventListener('keydown', (e) => { e.stopPropagation(); });
        popup.addEventListener('keyup', (e) => { e.stopPropagation(); });
        
        document.body.appendChild(popup);
    },

    showLinkCurveOptions(editor, link) {
        const existing = document.getElementById('link-curve-options-popup');
        if (existing) { existing.remove(); return; }
        
        const toolbar = editor._linkSelectionToolbar;
        if (!toolbar) return;
        
        const toolbarRect = toolbar.getBoundingClientRect();
        const isDark = editor.darkMode;
        const textC = isDark ? 'rgba(255,255,255,0.9)' : 'rgba(30,30,50,0.85)';
        
        const popup = document.createElement('div');
        popup.id = 'link-curve-options-popup';
        popup.style.cssText = `
            position: fixed;
            left: ${toolbarRect.left + toolbarRect.width / 2}px;
            top: ${toolbarRect.bottom + 8}px;
            transform: translateX(-50%);
            z-index: 10000;
            background: ${isDark
                ? 'linear-gradient(135deg, rgba(15,15,25,0.35) 0%, rgba(15,15,25,0.25) 50%, rgba(15,15,25,0.20) 100%)'
                : 'linear-gradient(135deg, rgba(255,255,255,0.50) 0%, rgba(255,255,255,0.35) 50%, rgba(255,255,255,0.28) 100%)'};
            border: 1px solid ${isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.08)'};
            border-radius: 14px;
            padding: 8px;
            box-shadow: ${isDark
                ? '0 8px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.08)'
                : '0 8px 32px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.6)'};
            backdrop-filter: blur(24px) saturate(200%);
            -webkit-backdrop-filter: blur(24px) saturate(200%);
            display: flex;
            flex-direction: column;
            gap: 4px;
            min-width: 130px;
            font-family: 'Poppins', -apple-system, sans-serif;
        `;
        
        const activeBg = isDark ? 'rgba(52,152,219,0.20)' : 'rgba(52,152,219,0.15)';
        const activeBorder = 'rgba(52,152,219,0.5)';
        const inactiveBg = isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)';
        const inactiveBorder = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';
        
        const modes = [
            { id: 'global', name: 'Use Global' },
            { id: 'auto', name: 'Auto' },
            { id: 'manual', name: 'Manual' },
            { id: 'off', name: 'Off (Straight)' }
        ];
        
        let currentMode = 'global';
        if (link.curveOverride === false || link.curveMode === 'off') {
            currentMode = 'off';
        } else if (link.curveMode === 'auto') {
            currentMode = 'auto';
        } else if (link.curveMode === 'manual') {
            currentMode = 'manual';
        } else if (link.curveOverride === undefined && link.curveMode === undefined) {
            currentMode = 'global';
        }
        
        const updateButtonStyles = () => {
            popup.querySelectorAll('button').forEach((btn, idx) => {
                const isActive = modes[idx].id === currentMode;
                btn.style.border = `1px solid ${isActive ? activeBorder : inactiveBorder}`;
                btn.style.background = isActive ? activeBg : inactiveBg;
                btn.style.color = isActive ? '#3498db' : textC;
                btn.style.fontWeight = isActive ? '600' : '400';
            });
        };
        
        modes.forEach(mode => {
            const btn = document.createElement('button');
            const isActive = currentMode === mode.id;
            btn.textContent = mode.name;
            btn.style.cssText = `
                padding: 7px 14px;
                border: 1px solid ${isActive ? activeBorder : inactiveBorder};
                background: ${isActive ? activeBg : inactiveBg};
                color: ${isActive ? '#3498db' : textC};
                border-radius: 7px;
                cursor: pointer;
                font-size: 11px;
                font-family: inherit;
                font-weight: ${isActive ? '600' : '400'};
                text-align: left;
                transition: all 0.15s ease;
            `;
            btn.onmouseenter = () => {
                if (currentMode !== mode.id) {
                    btn.style.background = isDark ? 'rgba(255,255,255,0.10)' : 'rgba(0,0,0,0.06)';
                    btn.style.borderColor = isDark ? 'rgba(255,255,255,0.18)' : 'rgba(0,0,0,0.10)';
                }
            };
            btn.onmouseleave = () => {
                if (currentMode !== mode.id) {
                    btn.style.background = inactiveBg;
                    btn.style.borderColor = inactiveBorder;
                }
            };
            btn.onclick = (e) => {
                e.stopPropagation();
                
                // CRITICAL: Use proper curve mode handler for seamless transitions
                // This handles TB position sync, curve data capture, etc.
                editor._curveSubmenuLink = link;
                const newMode = mode.id === 'global' ? null : mode.id;
                editor.handleContextCurveModeChange(newMode);
                editor._curveSubmenuLink = null;
                
                // Update current mode and refresh button styles
                currentMode = mode.id;
                updateButtonStyles();
                
                // DON'T remove popup - keep it open until user clicks elsewhere
            };
            popup.appendChild(btn);
        });
        
        // Prevent clicks from closing toolbar
        popup.addEventListener('mousedown', (e) => e.stopPropagation());
        popup.addEventListener('click', (e) => e.stopPropagation());
        
        // Close popup when clicking elsewhere
        const closePopupOnClickOutside = (e) => {
            if (!popup.contains(e.target) && !e.target.closest('#link-selection-toolbar')) {
                popup.remove();
                document.removeEventListener('mousedown', closePopupOnClickOutside);
            }
        };
        setTimeout(() => {
            document.addEventListener('mousedown', closePopupOnClickOutside);
        }, 100);
        
        popup.addEventListener('keydown', (e) => { e.stopPropagation(); });
        popup.addEventListener('keyup', (e) => { e.stopPropagation(); });
        document.body.appendChild(popup);
    },

    showDeviceLabelStyleMenu(editor, device, toolbar) {
        const existing = document.getElementById('device-label-style-menu');
        if (existing) { existing.remove(); return; }

        if (!toolbar) toolbar = editor._deviceSelectionToolbar;
        if (!toolbar) return;

        const toolbarRect = toolbar.getBoundingClientRect();
        const isDark = editor.darkMode;
        const textC = isDark ? 'rgba(255,255,255,0.9)' : 'rgba(30,30,50,0.85)';
        const dimC = isDark ? 'rgba(255,255,255,0.45)' : 'rgba(30,30,50,0.4)';

        const popup = document.createElement('div');
        popup.id = 'device-label-style-menu';
        popup.style.cssText = `
            position: fixed;
            left: ${toolbarRect.left + toolbarRect.width / 2}px;
            top: ${toolbarRect.bottom + 8}px;
            transform: translateX(-50%);
            z-index: 100001;
            background: ${isDark
                ? 'linear-gradient(135deg, rgba(15,15,25,0.35) 0%, rgba(15,15,25,0.25) 50%, rgba(15,15,25,0.20) 100%)'
                : 'linear-gradient(135deg, rgba(255,255,255,0.50) 0%, rgba(255,255,255,0.35) 50%, rgba(255,255,255,0.28) 100%)'};
            border: 1px solid ${isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.08)'};
            border-radius: 14px;
            padding: 8px 10px;
            box-shadow: ${isDark
                ? '0 8px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.08), inset 0 0 0 0.5px rgba(255,255,255,0.05)'
                : '0 8px 32px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.6)'};
            backdrop-filter: blur(24px) saturate(200%);
            -webkit-backdrop-filter: blur(24px) saturate(200%);
            font-family: 'Poppins', -apple-system, sans-serif;
            color: ${textC};
            min-width: 200px;
            max-width: 260px;
        `;

        const activeBg = isDark ? 'rgba(52,152,219,0.20)' : 'rgba(52,152,219,0.15)';
        const activeBorder = 'rgba(52,152,219,0.5)';
        const inactiveBg = isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)';
        const inactiveBorder = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';
        const hoverBg = isDark ? 'rgba(255,255,255,0.10)' : 'rgba(0,0,0,0.06)';

        const sectionLabel = (text) => {
            const lbl = document.createElement('div');
            lbl.textContent = text;
            lbl.style.cssText = `font-size: 8px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: ${dimC}; margin: 4px 0 2px 0;`;
            return lbl;
        };

        const makeBtn = (label, isActive, extraCSS, onClick) => {
            const btn = document.createElement('button');
            btn.textContent = label;
            btn.style.cssText = `
                padding: 3px 8px; border-radius: 5px; font-size: 10px; cursor: pointer;
                border: 1px solid ${isActive ? activeBorder : inactiveBorder};
                background: ${isActive ? activeBg : inactiveBg};
                color: ${isActive ? '#3498db' : textC};
                transition: all 0.15s ease; font-family: inherit;
                ${extraCSS || ''}
            `;
            btn.onmouseenter = () => { if (!isActive) { btn.style.background = hoverBg; btn.style.borderColor = isDark ? 'rgba(255,255,255,0.18)' : 'rgba(0,0,0,0.10)'; } };
            btn.onmouseleave = () => { if (!isActive) { btn.style.background = inactiveBg; btn.style.borderColor = inactiveBorder; } };
            btn.onclick = (e) => { e.stopPropagation(); onClick(); };
            return btn;
        };

        // --- Font Family --- (same list as TB text fonts)
        popup.appendChild(sectionLabel('Font'));
        const fonts = [
            { name: 'Sans', family: 'Inter, sans-serif' },
            { name: 'Brand', family: "'IBM Plex Sans', sans-serif" },
            { name: 'Hand', family: "'Caveat', cursive" },
            { name: 'Mono', family: "'IBM Plex Mono', monospace" },
            { name: 'Serif', family: 'Georgia, serif' },
            { name: 'Sketch', family: "'Comic Neue', cursive" },
            { name: 'System', family: '-apple-system, BlinkMacSystemFont, sans-serif' },
            { name: 'Classic', family: 'Arial, sans-serif' }
        ];
        const fontGrid = document.createElement('div');
        fontGrid.style.cssText = 'display: grid; grid-template-columns: repeat(4, 1fr); gap: 3px; margin-bottom: 2px;';
        const currentFont = device.fontFamily || editor.defaultDeviceFontFamily || 'Inter, sans-serif';
        fonts.forEach(f => {
            const isActive = currentFont.includes(f.family.split(',')[0].replace(/'/g, ''));
            const btn = document.createElement('button');
            const previewSpan = document.createElement('span');
            previewSpan.textContent = 'Aa';
            previewSpan.style.cssText = `font-family: ${f.family}; font-size: 12px; color: ${isActive ? '#fff' : textC}; line-height: 1;`;
            const labelSpan = document.createElement('span');
            labelSpan.textContent = f.name;
            labelSpan.style.cssText = `font-size: 7px; text-transform: uppercase; letter-spacing: 0.4px; color: ${isActive ? 'rgba(255,255,255,0.85)' : dimC}; font-family: Inter, sans-serif;`;
            btn.appendChild(previewSpan);
            btn.appendChild(labelSpan);
            btn.style.cssText = `
                display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px;
                padding: 4px 2px; min-height: 30px; border-radius: 6px; cursor: pointer;
                border: 1px solid ${isActive ? activeBorder : inactiveBorder};
                background: ${isActive ? 'linear-gradient(135deg, rgba(52,152,219,0.35), rgba(52,152,219,0.20))' : inactiveBg};
                transition: all 0.15s ease; font-family: inherit;
            `;
            btn.onmouseenter = () => { if (!isActive) { btn.style.background = hoverBg; btn.style.borderColor = isDark ? 'rgba(255,255,255,0.20)' : 'rgba(0,0,0,0.12)'; btn.style.transform = 'translateY(-1px)'; } };
            btn.onmouseleave = () => { if (!isActive) { btn.style.background = inactiveBg; btn.style.borderColor = inactiveBorder; btn.style.transform = 'none'; } };
            btn.onclick = (e) => {
                e.stopPropagation();
                device.fontFamily = f.family;
                editor.saveState(); editor.draw();
                popup.remove(); this.showDeviceLabelStyleMenu(editor, device, toolbar);
            };
            fontGrid.appendChild(btn);
        });
        popup.appendChild(fontGrid);

        // --- Font Weight ---
        popup.appendChild(sectionLabel('Weight'));
        const weights = [
            { name: 'Normal', value: '400' },
            { name: 'Medium', value: '500' },
            { name: 'Semi', value: '600' },
            { name: 'Bold', value: 'bold' }
        ];
        const weightRow = document.createElement('div');
        weightRow.style.cssText = 'display: flex; gap: 3px; margin-bottom: 2px;';
        const currentWeight = device.fontWeight || '600';
        weights.forEach(w => {
            const isActive = currentWeight === w.value;
            const btn = makeBtn(w.name, isActive, `font-weight: ${w.value};`, () => {
                device.fontWeight = w.value;
                editor.saveState(); editor.draw();
                popup.remove(); this.showDeviceLabelStyleMenu(editor, device, toolbar);
            });
            weightRow.appendChild(btn);
        });
        popup.appendChild(weightRow);

        // --- Label Color ---
        popup.appendChild(sectionLabel('Color'));
        const colorRow = document.createElement('div');
        colorRow.style.cssText = 'display: flex; align-items: center; gap: 4px; margin-bottom: 2px; flex-wrap: wrap;';
        const labelColors = ['#ECF0F1', '#ffffff', '#0d1b2a', '#e74c3c', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6', '#FF5E1F', '#00bcd4'];
        const currentLabelColor = device.labelColor || (isDark ? '#ECF0F1' : '#0d1b2a');
        labelColors.forEach(c => {
            const swatch = document.createElement('div');
            const isActive = currentLabelColor.toLowerCase() === c.toLowerCase();
            swatch.style.cssText = `
                width: 16px; height: 16px; border-radius: 4px; cursor: pointer;
                background: ${c};
                border: 2px solid ${isActive ? '#3498db' : (isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.08)')};
                transition: all 0.15s ease;
                box-shadow: ${isActive ? '0 0 6px rgba(52,152,219,0.4)' : 'none'};
            `;
            swatch.onmouseenter = () => { swatch.style.transform = 'scale(1.15)'; swatch.style.borderColor = isDark ? 'rgba(255,255,255,0.35)' : 'rgba(0,0,0,0.2)'; };
            swatch.onmouseleave = () => { swatch.style.transform = 'scale(1)'; if (!isActive) swatch.style.borderColor = isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.08)'; };
            swatch.onclick = (e) => {
                e.stopPropagation();
                device.labelColor = c;
                editor.saveState(); editor.draw();
                popup.remove(); this.showDeviceLabelStyleMenu(editor, device, toolbar);
            };
            colorRow.appendChild(swatch);
        });
        const customPicker = document.createElement('input');
        customPicker.type = 'color';
        customPicker.value = currentLabelColor;
        customPicker.style.cssText = `width: 20px; height: 16px; border: 1px solid ${isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.08)'}; border-radius: 4px; cursor: pointer; background: transparent; padding: 0;`;
        customPicker.oninput = (e) => {
            device.labelColor = e.target.value;
            editor.saveState(); editor.draw();
        };
        colorRow.appendChild(customPicker);
        popup.appendChild(colorRow);

        // --- Label Size ---
        popup.appendChild(sectionLabel('Size'));
        const sizeRow = document.createElement('div');
        sizeRow.style.cssText = 'display: flex; align-items: center; gap: 6px; margin-bottom: 2px;';
        const currentSize = device.labelSize || Math.max(12, Math.min(device.radius * 0.5, 36));
        const sizeSlider = document.createElement('input');
        sizeSlider.type = 'range';
        sizeSlider.min = '8';
        sizeSlider.max = '48';
        sizeSlider.value = String(Math.round(currentSize));
        sizeSlider.style.cssText = 'flex: 1; accent-color: #3498db; height: 3px; cursor: pointer;';
        const sizeVal = document.createElement('span');
        sizeVal.textContent = `${Math.round(currentSize)}px`;
        sizeVal.style.cssText = `font-size: 9px; min-width: 28px; text-align: right; color: ${dimC}; font-weight: 500;`;
        sizeSlider.oninput = (e) => {
            device.labelSize = parseInt(e.target.value);
            sizeVal.textContent = `${e.target.value}px`;
            editor.draw();
        };
        sizeSlider.onchange = () => { editor.saveState(); };
        sizeRow.appendChild(sizeSlider);
        sizeRow.appendChild(sizeVal);
        popup.appendChild(sizeRow);

        // --- Label Border/Outline ---
        popup.appendChild(sectionLabel('Outline'));
        const outlineRow = document.createElement('div');
        outlineRow.style.cssText = 'display: flex; align-items: center; gap: 3px; margin-bottom: 2px;';
        const outlineColors = [
            { name: 'Auto', value: null },
            { name: 'Dark', value: 'rgba(13,27,42,0.98)' },
            { name: 'White', value: 'rgba(255,255,255,1)' },
            { name: 'None', value: 'none' }
        ];
        const currentOutline = device.labelOutlineColor || null;
        outlineColors.forEach(oc => {
            const isActive = currentOutline === oc.value;
            const btn = makeBtn(oc.name, isActive, 'font-size: 10px;', () => {
                device.labelOutlineColor = oc.value;
                editor.saveState(); editor.draw();
                popup.remove(); this.showDeviceLabelStyleMenu(editor, device, toolbar);
            });
            outlineRow.appendChild(btn);
        });
        popup.appendChild(outlineRow);

        // --- Reset button ---
        const resetRow = document.createElement('div');
        resetRow.style.cssText = `margin-top: 4px; padding-top: 4px; border-top: 1px solid ${isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)'};`;
        const resetBtn = document.createElement('button');
        resetBtn.textContent = 'Reset to Default';
        resetBtn.style.cssText = `
            width: 100%; padding: 4px 0; border-radius: 6px; font-size: 9px; cursor: pointer;
            font-family: inherit; font-weight: 500; letter-spacing: 0.3px;
            border: 1px solid ${isDark ? 'rgba(255,100,100,0.15)' : 'rgba(192,57,43,0.12)'};
            background: ${isDark ? 'rgba(255,100,100,0.06)' : 'rgba(192,57,43,0.04)'};
            color: ${isDark ? 'rgba(255,120,120,0.85)' : '#c0392b'};
            transition: all 0.15s ease;
        `;
        resetBtn.onmouseenter = () => { resetBtn.style.background = isDark ? 'rgba(255,100,100,0.14)' : 'rgba(192,57,43,0.10)'; resetBtn.style.borderColor = isDark ? 'rgba(255,100,100,0.30)' : 'rgba(192,57,43,0.25)'; };
        resetBtn.onmouseleave = () => { resetBtn.style.background = isDark ? 'rgba(255,100,100,0.06)' : 'rgba(192,57,43,0.04)'; resetBtn.style.borderColor = isDark ? 'rgba(255,100,100,0.15)' : 'rgba(192,57,43,0.12)'; };
        resetBtn.onclick = (e) => {
            e.stopPropagation();
            delete device.fontFamily;
            delete device.fontWeight;
            delete device.labelColor;
            delete device.labelSize;
            delete device.labelOutlineColor;
            editor.saveState(); editor.draw();
            popup.remove(); this.showDeviceLabelStyleMenu(editor, device, toolbar);
        };
        resetRow.appendChild(resetBtn);
        popup.appendChild(resetRow);

        popup.addEventListener('mousedown', (e) => e.stopPropagation());
        popup.addEventListener('click', (e) => e.stopPropagation());

        const closeOnClickOutside = (e) => {
            if (!popup.contains(e.target) && !e.target.closest('#device-selection-toolbar')) {
                popup.remove();
                document.removeEventListener('mousedown', closeOnClickOutside);
            }
        };
        setTimeout(() => document.addEventListener('mousedown', closeOnClickOutside), 100);

        popup.addEventListener('keydown', (e) => { e.stopPropagation(); });
        popup.addEventListener('keyup', (e) => { e.stopPropagation(); });
        document.body.appendChild(popup);

        requestAnimationFrame(() => {
            const pr = popup.getBoundingClientRect();
            // Clamp horizontally
            if (pr.right > window.innerWidth - 8) popup.style.left = `${window.innerWidth - pr.width / 2 - 8}px`;
            if (pr.left < 8) popup.style.left = `${pr.width / 2 + 8}px`;

            // Keep below toolbar — never flip above (that hides the device).
            // If it overflows the viewport, cap height and scroll.
            if (pr.bottom > window.innerHeight - 8) {
                const availBelow = window.innerHeight - toolbarRect.bottom - 16;
                if (availBelow >= 180) {
                    popup.style.maxHeight = `${availBelow}px`;
                    popup.style.overflowY = 'auto';
                } else {
                    // Toolbar too low — position popup to fill from toolbar down to bottom
                    popup.style.top = `${toolbarRect.bottom + 4}px`;
                    popup.style.maxHeight = `${window.innerHeight - toolbarRect.bottom - 12}px`;
                    popup.style.overflowY = 'auto';
                }
            }
        });
    }
};

console.log('[topology-selection-popups.js] SelectionPopups loaded');
