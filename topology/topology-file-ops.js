/**
 * topology-file-ops.js - File Operations Module
 * 
 * All save/load/export/import, bug topologies, custom sections,
 * and clear/new topology operations extracted from topology.js.
 * 
 * Methods are injected onto the editor prototype at load time.
 * 
 * @version 1.0.0
 * @date 2026-02-23
 */

'use strict';

window.FileOps = {

    // ========================================================================
    // TOPOLOGY INDICATOR
    // ========================================================================

    // sharedInfo (optional 5th arg) carries shared-in attribution:
    //   { isSharedIn, isInbox, owner, ownerDisplay, permission }
    // When present, the "Shared with me" / domain pill gets a native
    // title tooltip naming the originating user, AND `_refreshDomainDots`
    // switches to the /api/domains/{id}/topologies endpoint so the
    // multi-topology toggles appear for shared-in domains too (they
    // don't live in /api/sections).
    //
    // opts (optional 6th arg) carries presentation flags:
    //   { isGeneral: true }
    // When `isGeneral` is set, the pill renders in the neutral
    // "General" mode -- a grey badge with no domain color, used after
    // the user deletes the topology they were currently editing. The
    // canvas keeps whatever the user has drawn but the pill makes it
    // obvious the topology is no longer attached to any domain. The
    // Save button then opens a domain picker (see
    // `_showSaveToDomainPicker`) instead of falling through to the
    // legacy "no domain" warning.
    updateTopologyIndicator(name, domainName, domainColor, sectionId, sharedInfo, opts) {
        const el = document.getElementById('topo-active-indicator');
        const nameEl = document.getElementById('topo-active-name');
        const nameWrapEl = document.getElementById('topo-active-name-wrap');
        const domEl = document.getElementById('topo-active-domain');
        const sepEl = document.getElementById('topo-active-sep');
        const innerEl = document.getElementById('topo-active-inner');
        const dotEl = document.getElementById('topo-active-color-dot');
        if (!el || !nameEl) return;
        if (!name) { el.style.display = 'none'; return; }
        FileOps._initIndicatorPillBtn();
        FileOps._initIndicatorSaveBtn();

        const isGeneral = !!(opts && opts.isGeneral);
        // Mark the indicator with a data attribute so the Save handler
        // (and any future CSS hooks) can branch on the General mode
        // without re-parsing names.
        try {
            if (isGeneral) el.setAttribute('data-mode', 'general');
            else el.removeAttribute('data-mode');
        } catch (_) {}

        const sharedTip = (() => {
            if (!sharedInfo || !(sharedInfo.isSharedIn || sharedInfo.isInbox)) return '';
            const display = (sharedInfo.ownerDisplay || '').trim();
            const user = (sharedInfo.owner || '').trim();
            let who;
            if (display && user && display.toLowerCase() !== user.toLowerCase()) {
                who = `${display} (${user})`;
            } else {
                who = display || user;
            }
            // User-facing terminology: read -> View, write -> Edit.
            // Wire token preserved in sharedInfo.permission for downstream
            // logic; only the visible label flips.
            const _shareApi = (typeof window !== 'undefined') ? window.TopologyShare : null;
            const permLabelText = sharedInfo.permission
                ? ((_shareApi && typeof _shareApi.permissionLabel === 'function')
                    ? _shareApi.permissionLabel(sharedInfo.permission)
                    : (sharedInfo.permission === 'write' ? 'Edit' : 'View'))
                : '';
            const perm = permLabelText ? ` - ${permLabelText}` : '';
            if (!who) {
                return sharedInfo.isInbox
                    ? 'Shared with you by another user'
                    : 'Shared by another user';
            }
            return `Shared by ${who}${perm}`;
        })();

        const applyContent = () => {
            nameEl.textContent = name;
            const indicatorColor = isGeneral ? '#94a3b8' : (domainColor || '#0066fa');
            const skinV2 = !!(document.body && document.body.classList.contains('ui-skin-v2'));
            if (innerEl) innerEl.style.setProperty('--topo-active-domain-color', indicatorColor);
            if (domEl) domEl.style.setProperty('--topo-active-domain-color', indicatorColor);
            if (el) el.style.setProperty('--topo-active-domain-color', indicatorColor);
            // Surface the full name in a native tooltip too, so users
            // on reduced-motion (animation disabled) or who just don't
            // want to hover-and-wait can still read the truncated tail.
            if (nameWrapEl) nameWrapEl.setAttribute('title', name);
            if (domEl && domainName) {
                domEl.textContent = domainName;
                domEl.style.display = '';
                if (sepEl) sepEl.style.display = '';
                if (isGeneral) {
                    // General-mode tooltip nudges the user toward the
                    // domain picker so they know the pill is actionable
                    // (Save button opens it). No shared-in tooltip can
                    // be active in this mode by definition.
                    domEl.setAttribute('title',
                        'No domain assigned -- click Save to pick one');
                    domEl.style.cursor = 'help';
                } else if (sharedTip) {
                    // Shared-in: attribute the originating user on hover
                    // so the reader sees "who shared this" without having
                    // to open the Topologies menu. Cleared on own
                    // topologies so a native "Shared with me" never gets
                    // a stale title from a prior shared-in load.
                    domEl.setAttribute('title', sharedTip);
                    domEl.style.cursor = 'help';
                } else {
                    domEl.removeAttribute('title');
                    domEl.style.cursor = '';
                }
            } else {
                if (domEl) domEl.style.display = 'none';
                if (sepEl) sepEl.style.display = 'none';
            }

            // Shared-by chip + View / Edit badge segments.
            // Only rendered when the active topology was shared INTO this
            // user (sharedInfo present + isSharedIn|isInbox). The chip is
            // a button that opens a small popover with the owner's
            // attribution, the permission row, and Remove-from-Shared
            // affordance; the badge mirrors the sidebar's
            // .ta-perm-badge.view/.edit visual contract so users see the
            // same Cyan/Orange semantics on the canvas top-bar as in the
            // Topologies dropdown.
            //
            // See DEVELOPMENT_GUIDELINES.md -> "Shared Topology
            // Permissions -- View / Edit -- 2026-05-12" -> "Top-bar pill"
            // subsection for the layout contract + invariants.
            FileOps._updateIndicatorShareSegments(name, sectionId, sharedInfo, isGeneral);
            if (skinV2 && innerEl) {
                // v2.3.12 owns the active topology pill entirely in CSS so
                // light/dark theme changes can animate as a text-first,
                // mode-aware surface. Keep only the domain-color variable
                // above; clear legacy gradient leftovers from older renders.
                innerEl.style.removeProperty('background');
                innerEl.style.removeProperty('border-color');
            } else if (isGeneral && innerEl) {
                // Neutral grey gradient -- visually distinct from any
                // domain color and from the legacy blue "no domain
                // yet" fallback. Pairs with the grey dot below so the
                // entire pill reads as "unassigned / general".
                innerEl.style.background = (
                    `linear-gradient(135deg, rgba(8, 14, 30, 0.55), rgba(8, 14, 30, 0.35)),` +
                    `linear-gradient(135deg, rgba(148, 163, 184, 0.95), rgba(100, 116, 139, 0.95))`
                );
                innerEl.style.borderColor = 'rgba(148, 163, 184, 0.55)';
            } else if (domainColor && innerEl) {
                // Two-layer gradient: a dark base ALWAYS sits behind the
                // domain hue so white text on the pill stays readable
                // regardless of how light/saturated the user's domain color
                // is. Picking a pastel/cyan domain previously left "MULTICAST"
                // white-on-light-blue, barely visible at distance. The dark
                // overlay tints toward navy while still letting the domain
                // color come through at ~55-65% strength.
                innerEl.style.background = (
                    `linear-gradient(135deg, rgba(8, 14, 30, 0.55), rgba(8, 14, 30, 0.35)),` +
                    `linear-gradient(135deg, ${domainColor}f2, ${domainColor}cc)`
                );
                innerEl.style.borderColor = `${domainColor}aa`;
            } else if (innerEl) {
                innerEl.style.background = 'linear-gradient(135deg, rgba(0, 102, 250, 0.92), rgba(0, 70, 188, 0.95))';
                innerEl.style.borderColor = 'rgba(255,255,255,0.22)';
            }
            if (dotEl) {
                const dotColor = indicatorColor;
                dotEl.style.background = dotColor;
                dotEl.style.color = dotColor;
                dotEl.style.boxShadow = `0 0 10px ${dotColor}, inset 0 0 4px rgba(255,255,255,0.3)`;
            }
            // After the text is in the DOM, measure whether it actually
            // overflows the wrapper. Only then do we enable the hover
            // marquee (otherwise short names would still have a hover
            // animation, which looks jittery and pointless). We also
            // size the animation distance + duration off the real
            // overflow so a 40-char name scrolls farther AND longer
            // than a 15-char one -- constant-speed ~60 px/sec reads
            // as "readable" across the range.
            if (nameWrapEl) {
                // Reset transform-affecting state before measuring so a
                // leftover animation doesn't fool scrollWidth/clientWidth.
                nameEl.style.transform = '';
                requestAnimationFrame(() => {
                    const overflow = nameEl.scrollWidth - nameWrapEl.clientWidth;
                    if (overflow > 2) {
                        const shift = overflow + 24;           // px to scroll
                        const duration = Math.max(4, shift / 60); // ~60 px/sec
                        nameWrapEl.style.setProperty('--marquee-shift', `-${shift}px`);
                        nameWrapEl.style.setProperty('--marquee-duration', `${duration.toFixed(2)}s`);
                        nameWrapEl.classList.add('overflowing');
                        nameWrapEl.classList.remove('no-fade');
                    } else {
                        nameWrapEl.classList.remove('overflowing');
                        nameWrapEl.classList.add('no-fade');
                        nameWrapEl.style.removeProperty('--marquee-shift');
                        nameWrapEl.style.removeProperty('--marquee-duration');
                    }
                });
            }
        };

        if (innerEl) innerEl.style.transition = 'background-color 0.35s ease, background 0.35s ease, border-color 0.35s ease, color 0.35s ease, opacity 0.2s ease, transform 0.2s ease';

        const wasVisible = el.style.display !== 'none';
        if (wasVisible && nameEl.textContent && nameEl.textContent !== name) {
            el.style.opacity = '0';
            el.style.transform = 'translateY(4px)';
            setTimeout(() => {
                applyContent();
                el.style.display = '';
                requestAnimationFrame(() => {
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                });
            }, 180);
        } else {
            applyContent();
            el.style.display = '';
            if (!wasVisible) {
                el.style.opacity = '0';
                el.style.transform = 'translateY(4px)';
                requestAnimationFrame(() => {
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                });
            }
        }
        try {
            localStorage.setItem('topo_active', JSON.stringify({
                name,
                domain: domainName || '',
                color: domainColor || '',
                sectionId: sectionId || '',
                shared: sharedInfo || null,
                general: isGeneral || false
            }));
        } catch (_) {}
        // In General mode there is no real domain to fetch siblings for
        // -- skip the dots refresh entirely so we don't trigger a
        // misleading /api/sections call with a null id.
        if (!isGeneral) FileOps._refreshDomainDots(sectionId, name, sharedInfo);
        else {
            const dotsEl = document.getElementById('topo-active-dots');
            if (dotsEl) { dotsEl.innerHTML = ''; dotsEl.style.display = 'none'; }
        }
        FileOps._markActiveDomainRow(isGeneral ? null : sectionId);
    },

    _updateIndicatorShareSegments(name, sectionId, sharedInfo, isGeneral) {
        const sharedByEl = document.getElementById('topo-active-shared-by');
        const permEl = document.getElementById('topo-active-perm-badge');
        if (!sharedByEl && !permEl) return;

        const isShared = !isGeneral && !!(sharedInfo && (sharedInfo.isSharedIn || sharedInfo.isInbox));
        if (!isShared) {
            if (sharedByEl) {
                sharedByEl.style.display = 'none';
                sharedByEl.textContent = '';
                sharedByEl.removeAttribute('title');
                sharedByEl.onclick = null;
            }
            if (permEl) {
                permEl.style.display = 'none';
                permEl.className = '';
                permEl.textContent = '';
                permEl.removeAttribute('title');
            }
            return;
        }

        const display = (sharedInfo.ownerDisplay || '').trim();
        const user = (sharedInfo.owner || '').trim();
        const ownerLabel = display || user || 'another user';
        const fullOwner = display && user && display.toLowerCase() !== user.toLowerCase()
            ? `${display} (${user})`
            : ownerLabel;
        const permission = sharedInfo.permission || 'read';
        const shareApi = (typeof window !== 'undefined') ? window.TopologyShare : null;
        const permLabel = shareApi && typeof shareApi.permissionLabel === 'function'
            ? shareApi.permissionLabel(permission)
            : (permission === 'write' ? 'Edit' : 'View');
        const permTitle = shareApi && typeof shareApi.permissionTitle === 'function'
            ? shareApi.permissionTitle(permission)
            : (permission === 'write'
                ? 'Edit: can open, modify, and save'
                : 'View only: can open and inspect');
        const permClass = permission === 'write' ? 'edit' : 'view';

        if (sharedByEl) {
            sharedByEl.textContent = `BY ${ownerLabel}`;
            sharedByEl.style.display = '';
            sharedByEl.style.cssText = `
                display:inline-flex;align-items:center;gap:4px;min-height:20px;
                padding:2px 7px;border-radius:999px;border:1px solid rgba(167,139,250,0.44);
                background:rgba(167,139,250,0.14);color:#e9ddff;
                font-size:9px;font-weight:800;letter-spacing:0.5px;text-transform:uppercase;
                line-height:1;white-space:nowrap;cursor:help;flex-shrink:0;
            `;
            sharedByEl.setAttribute('title', `Shared by ${fullOwner}`);
            sharedByEl.onclick = (ev) => {
                ev.preventDefault();
                ev.stopPropagation();
                try {
                    const topoName = (name || '').replace(/\.json$/i, '');
                    const detail = `Shared by ${fullOwner} - ${permTitle}`;
                    if (window.topologyEditor && window.topologyEditor.showToast) {
                        window.topologyEditor.showToast(`${topoName}: ${detail}`, 'info');
                    }
                } catch (_) {}
            };
        }
        if (permEl) {
            const icon = permission === 'write'
                ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/></svg>'
                : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
            permEl.className = `ta-perm-badge ${permClass}`;
            permEl.innerHTML = `${icon}${permLabel}`;
            permEl.style.display = '';
            permEl.setAttribute('title', permTitle);
        }
    },

    // Convenience wrapper -- shows the pill in the neutral "General"
    // (no-domain) state with the supplied name (defaults to "Untitled").
    // Used after a user deletes the topology they were currently
    // editing, so the canvas keeps the work but the pill clearly
    // signals "this is unassigned, pick a domain to save it".
    showGeneralTopologyIndicator(name) {
        FileOps.updateTopologyIndicator(
            name || 'Untitled',
            'General',
            null,
            null,
            null,
            { isGeneral: true }
        );
    },

    // Adds `.is-active` to exactly one `.custom-section-category` in the
    // Topologies dropdown -- the row that owns the currently-loaded
    // topology. Styling is defined in styles.css (domain-row v2). Safe
    // to call before the dropdown has been rendered; the class will be
    // picked up on the next `_renderCustomSectionsInDropdown()` because
    // that renderer reads the same localStorage key.
    _markActiveDomainRow(sectionId) {
        const dd = document.getElementById('topologies-dropdown-menu');
        if (!dd) return;
        const rows = dd.querySelectorAll('.custom-section-category');
        if (!rows.length) return;
        rows.forEach(r => {
            const match = sectionId && r.dataset.sectionId === sectionId;
            r.classList.toggle('is-active', !!match);
        });
    },

    clearTopologyIndicator() {
        const el = document.getElementById('topo-active-indicator');
        if (el) el.style.display = 'none';
        const dotsEl = document.getElementById('topo-active-dots');
        if (dotsEl) { dotsEl.innerHTML = ''; dotsEl.style.display = 'none'; }
        FileOps._domainTopoCache = null;
        FileOps._domainTopoCacheId = null;
        FileOps._domainTopoCacheShared = null;
        try { localStorage.removeItem('topo_active'); } catch (_) {}
        FileOps._markActiveDomainRow(null);
    },

    _topologyDirtySkipKeys: new Set([
        'selected', 'hovered', 'dragging',
        '_lastClickedAt', '_lastToggledAt',
        '_badgeWorlds', '_hostnameMismatch', '_mismatchDismissed',
        '_identity', '_configHostname',
        '_stackData', '_stackCachedAt',
        '_lldpData', '_lldpCompletedAt',
        '_gitCommit', '_gitCommitFetchedAt', '_gitCommitFailed',
        '_renaming', '_activeConfigJob', '_activeUpgradeJob',
        '_upgradeFailedJob', '_upgradeInProgress',
        '_mismatchRefreshPending', '_xrayCaptureActive', '_createdAt',
        '_sshReachable', '_sshReachableAt', '_deviceMode', '_modeRawState',
        '_onboarding', '_monitorCapabilities', '_monitoringOptions',
        '_monitorContext', '_monitorConfigFacts', '_monitoredSubsystems',
        '_monitoredReferenceTotal', '_monitoredReferenceUserCount',
        '_verifiedAt', '_autoClearHostKeysUpdatedAt', '_snVerifiedAt',
        '_snClearedByUserAt', '_userPinnedAt'
    ]),

    _topologyDirtyMetadataSkipKeys: new Set([
        'deviceIdCounter', 'linkIdCounter', 'textIdCounter',
        'shapeIdCounter', 'packetIdCounter', 'deviceCounters', 'topologySession'
    ]),

    _stableDirtyStringify(value) {
        if (value === null || typeof value !== 'object') return JSON.stringify(value);
        if (Array.isArray(value)) {
            return '[' + value.map(v => FileOps._stableDirtyStringify(v)).join(',') + ']';
        }
        const keys = Object.keys(value).sort();
        return '{' + keys.map(k => JSON.stringify(k) + ':' + FileOps._stableDirtyStringify(value[k])).join(',') + '}';
    },

    _sanitizeForDirtySignature(value, parentKey) {
        if (value === null || typeof value !== 'object') return value;
        if (Array.isArray(value)) {
            return value.map(v => FileOps._sanitizeForDirtySignature(v, parentKey));
        }
        const out = {};
        Object.keys(value).sort().forEach(k => {
            if (FileOps._topologyDirtySkipKeys.has(k)) return;
            if (parentKey === 'metadata' && FileOps._topologyDirtyMetadataSkipKeys.has(k)) return;
            out[k] = FileOps._sanitizeForDirtySignature(value[k], k);
        });
        return out;
    },

    _getTopologyDirtySignature(editor) {
        if (!editor || typeof FileOps.generateTopologyData !== 'function') return '';
        try {
            const data = FileOps.generateTopologyData(editor);
            const clean = FileOps._sanitizeForDirtySignature(data, '');
            return FileOps._stableDirtyStringify(clean);
        } catch (_) {
            return '';
        }
    },

    _markTopologyClean(editor, reason) {
        const sig = FileOps._getTopologyDirtySignature(editor);
        if (!sig) return;
        FileOps._cleanTopologySignature = sig;
        FileOps._cleanTopologyReason = reason || '';
    },

    _hasUnsavedTopologyChanges(editor) {
        if (!editor || editor.initializing) return false;
        const sig = FileOps._getTopologyDirtySignature(editor);
        if (!sig) return false;
        if (!FileOps._cleanTopologySignature) return false;
        return sig !== FileOps._cleanTopologySignature;
    },

    _activeTopologyBasename() {
        try {
            const info = JSON.parse(localStorage.getItem('topo_active') || '{}');
            return String(info && info.name || '').replace(/\.json$/i, '');
        } catch (_) {
            return '';
        }
    },

    _saveCurrentTopologyBeforeSwitch(editor, opts = {}) {
        return new Promise(async (resolve, reject) => {
            if (!editor || (!opts.allowEmpty && editor.objects.length === 0)) {
                FileOps._markTopologyClean(editor, 'empty-before-switch');
                resolve();
                return;
            }
            let info;
            try { info = JSON.parse(localStorage.getItem('topo_active') || '{}'); } catch (_) {}
            const topoData = opts.data || FileOps.generateTopologyData(editor);
            const syncActive = (window.TopologySync && window.TopologySync.getActive)
                ? window.TopologySync.getActive() : null;
            try {
                if (syncActive && syncActive.domain_id && syncActive.topology_id) {
                    if (syncActive.permission && syncActive.permission !== 'write') {
                        throw new Error('Current shared topology is view-only.');
                    }
                    const safeName = (syncActive.name || info?.name || 'topology').replace(/\.json$/i, '');
                    const result = await window.TopologySync.saveActive(safeName, topoData);
                    if (result && result.conflict) {
                        throw new Error('Save conflict: reload or save anyway before switching topology.');
                    }
                    FileOps._writeLocalCurrentSnapshot(editor, topoData);
                    FileOps._markTopologyClean(editor, 'switch-save-sync');
                    if (!opts.silent) editor.showToast(`Saved "${safeName}" before switching`, 'success');
                    resolve();
                    return;
                }
                if (info && info.shared && (info.shared.isSharedIn || info.shared.isInbox)) {
                    throw new Error('Shared topology save target is unavailable. Reload it before saving.');
                }
                if (info && info.sectionId && info.name && !info.general) {
                    const safeName = info.name.replace(/\.json$/i, '');
                    const result = await FileOps._sectionSaveWithConflict(
                        editor,
                        info.sectionId,
                        { name: safeName, topology: topoData },
                        () => {
                            if (!opts.silent) editor.showToast(`Saved "${safeName}" before switching`, 'success');
                            FileOps._writeLocalCurrentSnapshot(editor, topoData);
                            FileOps._markTopologyClean(editor, 'switch-save-section');
                        }
                    );
                    if (result && (result.conflict || result.error)) {
                        throw new Error(result.conflict
                            ? 'Save conflict: resolve it before switching topology.'
                            : 'Save failed.');
                    }
                    resolve();
                    return;
                }
                FileOps._showSaveToDomainPicker(editor, {
                    onSaved: () => {
                        FileOps._markTopologyClean(editor, 'switch-save-new');
                        resolve();
                    }
                });
            } catch (err) {
                reject(err);
            }
        });
    },

    _showUnsavedSwitchPrompt(editor, targetName, callbacks) {
        const stale = document.getElementById('topology-unsaved-switch-prompt');
        if (stale) stale.remove();
        const isDk = FileOps._menuDark(editor);
        const safeTarget = String(targetName || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
        const t = {
            bg: isDk ? 'rgba(15, 23, 42, 0.98)' : 'rgba(255, 255, 255, 0.98)',
            border: isDk ? 'rgba(148, 163, 184, 0.28)' : 'rgba(15, 23, 42, 0.12)',
            text: isDk ? '#e2e8f0' : '#0f172a',
            muted: isDk ? '#94a3b8' : '#64748b',
            subtle: isDk ? 'rgba(255,255,255,0.06)' : 'rgba(15,23,42,0.04)',
        };
        const overlay = document.createElement('div');
        overlay.id = 'topology-unsaved-switch-prompt';
        overlay.style.cssText = 'position:fixed;inset:0;z-index:10003;display:flex;align-items:center;justify-content:center;background:rgba(2,6,23,0.46);backdrop-filter:blur(5px);';
        overlay.innerHTML = `
            <div role="dialog" aria-modal="true" aria-labelledby="tusp-title"
                style="width:min(420px,calc(100vw - 32px));background:${t.bg};border:1px solid ${t.border};border-radius:14px;box-shadow:0 18px 60px rgba(0,0,0,0.32);padding:18px;font-family:'Poppins',-apple-system,sans-serif;color:${t.text};">
                <div id="tusp-title" style="font-size:15px;font-weight:700;margin-bottom:6px;">Save topology changes?</div>
                <div style="font-size:12px;line-height:1.55;color:${t.muted};margin-bottom:14px;">
                    You have unsaved canvas or device identity changes. Save before opening${safeTarget ? ` "${safeTarget}"` : ' another topology'}?
                </div>
                <div style="display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap;">
                    <button type="button" class="tusp-cancel" style="padding:8px 12px;border-radius:8px;border:1px solid ${t.border};background:transparent;color:${t.muted};font-size:12px;cursor:pointer;">Cancel</button>
                    <button type="button" class="tusp-discard" style="padding:8px 12px;border-radius:8px;border:1px solid ${t.border};background:${t.subtle};color:${t.text};font-size:12px;cursor:pointer;">Discard</button>
                    <button type="button" class="tusp-save" style="padding:8px 14px;border-radius:8px;border:0;background:#2563eb;color:#fff;font-size:12px;font-weight:700;cursor:pointer;">Save</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        const close = () => overlay.remove();
        overlay.querySelector('.tusp-cancel').onclick = () => { close(); callbacks.cancel?.(); };
        overlay.querySelector('.tusp-discard').onclick = () => { close(); callbacks.discard?.(); };
        overlay.querySelector('.tusp-save').onclick = async () => {
            const btn = overlay.querySelector('.tusp-save');
            btn.disabled = true;
            btn.textContent = 'Saving...';
            close();
            try {
                await callbacks.save?.();
            } catch (err) {
                editor.showToast('Save failed: ' + (err && err.message || err), 'error');
            }
        };
    },

    _requestTopologySwitch(editor, targetName, loadFn) {
        if (!editor || typeof loadFn !== 'function') return;
        const targetBase = String(targetName || '').replace(/\.json$/i, '');
        if (targetBase && targetBase === FileOps._activeTopologyBasename()) {
            loadFn();
            return;
        }
        if (!FileOps._hasUnsavedTopologyChanges(editor)) {
            loadFn();
            return;
        }
        if (FileOps._hasPersistentAutoSaveTarget(editor, { allowEmpty: true })) {
            FileOps._saveCurrentTopologyBeforeSwitch(editor, { allowEmpty: true, silent: true })
                .then(loadFn)
                .catch((err) => {
                    editor.showToast('Save before switch failed: ' + (err && err.message || err), 'error');
                });
            return;
        }
        FileOps._showUnsavedSwitchPrompt(editor, targetBase, {
            save: async () => {
                await FileOps._saveCurrentTopologyBeforeSwitch(editor, { allowEmpty: true });
                loadFn();
            },
            discard: () => loadFn(),
            cancel: () => {}
        });
    },

    _beginTopologyLoad(editor, identity) {
        if (!editor || typeof editor.beginTopologySwitch !== 'function') return null;
        return editor.beginTopologySwitch(identity || {});
    },

    _isTopologyLoadCurrent(editor, token) {
        if (!editor || token === null || token === undefined) return true;
        if (typeof editor.isTopologySwitchCurrent !== 'function') return true;
        return editor.isTopologySwitchCurrent(token);
    },

    _cancelTopologyLoad(editor, token) {
        if (!editor || token === null || token === undefined) return;
        if (typeof editor.cancelTopologySwitch === 'function') {
            editor.cancelTopologySwitch(token);
        }
    },

    _loadIntoEditor(editor, data, identity = {}) {
        if (!editor || !data) return false;
        const token = identity.loadToken !== undefined
            ? identity.loadToken
            : FileOps._beginTopologyLoad(editor, identity);
        if (!FileOps._isTopologyLoadCurrent(editor, token)) return false;
        if (identity.name) {
            FileOps.updateTopologyIndicator(
                identity.name,
                identity.domain || null,
                identity.color || null,
                identity.sectionId || null,
                identity.shared || null,
                identity.general ? { isGeneral: true } : null
            );
        }
        const loaded = editor.loadTopologyFromData(data, {
            domain: identity.domain || null,
            name: identity.name || '',
            filename: identity.filename || '',
            sectionId: identity.sectionId || '',
            topologyId: identity.topologyId || '',
            shared: identity.shared || null,
            loadToken: token,
        });
        if (loaded) FileOps._markTopologyClean(editor, 'topology-load');
        return loaded;
    },

    restoreTopologyIndicator() {
        try {
            const raw = localStorage.getItem('topo_active');
            if (raw) {
                const d = JSON.parse(raw);
                if (d && d.name) {
                    FileOps.updateTopologyIndicator(
                        d.name,
                        d.domain || null,
                        d.color || null,
                        d.sectionId || null,
                        d.shared || null,
                        d.general ? { isGeneral: true } : null
                    );
                    FileOps._initIndicatorSaveBtn();
                    return;
                }
            }
            // Fallback: TopologySync keeps a parallel `topo_active_meta`
            // key. When the user reaches the canvas through a path that
            // doesn't go through FileOps.updateTopologyIndicator (auto-
            // save reload, AI Topology Generator, Network Mapper auto-
            // draw, etc.), `topo_active` is empty but TopologySync's
            // metadata still names the current topology. Rehydrate the
            // pill from there so the bottom-left indicator survives the
            // refresh, matching the historical UX.
            const metaRaw = localStorage.getItem('topo_active_meta');
            if (metaRaw) {
                let meta = null;
                try { meta = JSON.parse(metaRaw); } catch (_) { meta = null; }
                if (meta && meta.name) {
                    const sharedInfo = (meta.is_shared || meta.permission)
                        ? {
                            isSharedIn: !!meta.is_shared,
                            isInbox: false,
                            owner: meta.owner || '',
                            ownerDisplay: meta.owner_display || '',
                            permission: meta.permission || '',
                        }
                        : null;
                    FileOps.updateTopologyIndicator(
                        meta.name,
                        meta.domain_name || null,
                        meta.color || null,
                        meta.section_id || null,
                        sharedInfo
                    );
                }
            }
        } catch (_) {}
        FileOps._initIndicatorSaveBtn();
    },

    _initIndicatorSaveBtn() {
        const saveEl = document.getElementById('topo-active-save');
        if (!saveEl || saveEl._wired) return;
        saveEl._wired = true;
        // Keep the old `data-tooltip` attribute away so the global
        // tooltip system doesn't race our custom "Quick Save ⌘S" chip
        // (user reported a duplicate: dark "Quick Save" AT TOP and a
        // second light "Save current topology" UNDERNEATH the button
        // before this cleanup).
        try { saveEl.removeAttribute('data-tooltip'); } catch (_) {}
        try { saveEl.removeAttribute('title'); } catch (_) {}
        let saveTip = null;
        saveEl.addEventListener('mouseenter', () => {
            if (saveTip) saveTip.remove();
            const r = saveEl.getBoundingClientRect();
            saveTip = document.createElement('div');
            // Light-themed chip. Same shape as before but on a white
            // liquid-glass background with dark text -- matches the
            // system-wide tooltip palette the user asked for.
            saveTip.style.cssText = `
                position:fixed; z-index:100001; pointer-events:none;
                bottom:${window.innerHeight - r.top + 8}px; left:${r.left + r.width / 2}px;
                transform:translateX(-50%); display:flex; align-items:center; gap:6px;
                padding:6px 11px; border-radius:8px; white-space:nowrap;
                background:rgba(255,255,255,0.96);
                backdrop-filter:blur(16px) saturate(160%);
                -webkit-backdrop-filter:blur(16px) saturate(160%);
                box-shadow:0 6px 20px rgba(15,23,42,0.18), 0 2px 6px rgba(15,23,42,0.08);
                border:1px solid rgba(15,23,42,0.08);
                opacity:0; transition:opacity 0.12s ease;
            `;
            const label = document.createElement('span');
            label.textContent = 'Quick Save';
            label.style.cssText = 'font-size:11px;color:#1e293b;font-weight:600;font-family:Poppins,-apple-system,sans-serif;letter-spacing:0.1px;';
            saveTip.appendChild(label);
            const kbd = document.createElement('kbd');
            const isMac = navigator.platform?.includes('Mac');
            kbd.textContent = isMac ? '\u2318S' : 'Ctrl+S';
            // KBD chip also repainted for a light shell.
            kbd.style.cssText = `
                display:inline-block; padding:1px 6px; font-size:9.5px; font-weight:600;
                font-family:-apple-system,'SF Mono',Menlo,Consolas,monospace;
                background:linear-gradient(180deg,#f8fafc,#e2e8f0);
                border:1px solid rgba(15,23,42,0.16); border-bottom-width:2px;
                border-radius:4px; color:#475569;
                box-shadow:0 1px 0 rgba(15,23,42,0.10);
            `;
            saveTip.appendChild(kbd);
            document.body.appendChild(saveTip);
            // Capture the chip in a local before scheduling the fade-in so
            // that a synchronous `mouseleave` (which nulls `saveTip`) can't
            // turn the rAF callback into a "Cannot read 'style' of null"
            // crash. Also re-check `isConnected` in case the chip was
            // removed between rAF schedule and execution.
            const tipRef = saveTip;
            requestAnimationFrame(() => {
                if (tipRef && tipRef.isConnected) tipRef.style.opacity = '1';
            });
        });
        saveEl.addEventListener('mouseleave', () => {
            if (saveTip) { saveTip.remove(); saveTip = null; }
        });
        saveEl.addEventListener('click', async (ev) => {
            if (ev) {
                ev.preventDefault();
                ev.stopPropagation();
            }
            const editor = window.topologyEditor || window.editor;
            if (!editor || !editor.objects || editor.objects.length === 0) return;
            saveEl.style.transform = 'scale(0.9)';
            setTimeout(() => { saveEl.style.transform = 'scale(1)'; }, 100);
            let info;
            try { info = JSON.parse(localStorage.getItem('topo_active')); } catch (_) {}

            const origSvg = saveEl.innerHTML;
            saveEl.style.opacity = '0.5';
            saveEl.style.pointerEvents = 'none';
            const restore = () => {
                saveEl.style.opacity = '1';
                saveEl.style.pointerEvents = 'auto';
            };
            const markOk = () => {
                saveEl.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>';
                setTimeout(() => { saveEl.innerHTML = origSvg; }, 1200);
            };

            // General (no-domain) mode -- the user just deleted the
            // topology they were editing or otherwise detached from
            // any domain. The canvas still has their work, but there
            // is no destination to write to. Open the Save-to-domain
            // picker so they can pick (or create) a domain and name
            // the topology in one shot. We skip the TopologySync /
            // /api/sections fallbacks entirely in this branch -- they
            // both require a sectionId/domain_id we don't have yet.
            const isGeneralMode = !!(info && info.general);
            if (isGeneralMode) {
                if (typeof FileOps._showSaveToDomainPicker === 'function') {
                    FileOps._showSaveToDomainPicker(editor, {
                        defaultName: (info && info.name && info.name !== 'Untitled')
                            ? info.name
                            : '',
                        onSaved: () => markOk(),
                    });
                } else {
                    editor.showToast('Pick a domain to save into -- use Topologies menu', 'warning');
                    const btnTopo = document.getElementById('btn-topologies');
                    if (btnTopo) btnTopo.click();
                }
                restore();
                return;
            }

            // Prefer TopologySync for any topology registered with the
            // live-sync hub -- that includes shared-in topologies (which
            // the legacy /api/sections path can't save at all) and
            // owner-side topologies that already have a multi-user row.
            // The sync path enforces base_updated_at conflict guard,
            // records an audit-log entry, and broadcasts the new save to
            // every collaborator over the event bus.
            const syncActive = (window.TopologySync && window.TopologySync.getActive)
                ? window.TopologySync.getActive() : null;
            if (syncActive && syncActive.domain_id && syncActive.topology_id) {
                try {
                    const data = FileOps.generateTopologyData(editor);
                    const result = await window.TopologySync.saveActive(syncActive.name || info?.name || 'topology', data);
                    if (result && result.conflict) {
                        FileOps._showStaleSaveBanner(editor, {
                            currentUpdatedAt: result.current_updated_at || '',
                            onReload: () => {
                                if (window.TopologySync && window.TopologySync.reloadActive) {
                                    window.TopologySync.reloadActive();
                                }
                            },
                            onForce: async () => {
                                try {
                                    await window.TopologySync.saveActive(
                                        syncActive.name || info?.name || 'topology',
                                        data, { force: true },
                                    );
                                    editor.showToast('Overwrote server copy', 'success');
                                    FileOps._markTopologyClean(editor, 'indicator-save-force');
                                    markOk();
                                } catch (err) {
                                    editor.showToast('Save failed: ' + (err && err.message || err), 'error');
                                }
                            },
                        });
                        const who = result.last_actor_display_name || result.last_actor || 'someone';
                        editor.showToast('Save conflict: ' + who + ' changed this topology while you had it open', 'warning');
                    } else {
                        editor.showToast('Saved ' + (syncActive.name || info?.name || 'topology'), 'success');
                        FileOps._markTopologyClean(editor, 'indicator-save-sync');
                        markOk();
                    }
                } catch (err) {
                    editor.showToast('Save failed: ' + (err && err.message || err), 'error');
                }
                restore();
                return;
            }

            // Legacy fallback: write through /api/sections for plain
            // on-disk topologies that haven't been migrated yet.
            let sectionId = info?.sectionId;
            if (!sectionId && info?.domain && editor._customSections) {
                const match = editor._customSections.find(s => s.name === info.domain);
                if (match) sectionId = match.id;
            }
            if (!sectionId && editor._customSections && editor._customSections.length > 0) {
                sectionId = editor._customSections[0].id;
            }
            if (!sectionId || !info?.name) {
                editor.showToast('No domain to save to -- use Topologies menu', 'warning');
                const btnTopo = document.getElementById('btn-topologies');
                if (btnTopo) btnTopo.click();
                restore();
                return;
            }
            try {
                const result = await FileOps._sectionSaveWithConflict(
                    editor,
                    sectionId,
                    { name: info.name, topology: FileOps.generateTopologyData(editor) },
                    null,
                );
                if (result && !result.error && !result.conflict && !result.quota) {
                    const sec = (editor._customSections || []).find(s => s.id === sectionId);
                    if (sec) FileOps.updateTopologyIndicator(info.name, sec.name, sec.color, sectionId);
                    editor.showToast('Saved ' + info.name, 'success');
                    FileOps._markTopologyClean(editor, 'indicator-save-section');
                    markOk();
                }
            } catch (err) { editor.showToast('Save failed: ' + err.message, 'error'); }
            restore();
        });
    },

    _initIndicatorPillBtn() {
        const innerEl = document.getElementById('topo-active-inner');
        if (!innerEl || innerEl._wiredOpenTopologies) return;
        innerEl._wiredOpenTopologies = true;
        innerEl.style.cursor = 'pointer';
        innerEl.setAttribute('role', 'button');
        innerEl.setAttribute('tabindex', '0');
        innerEl.setAttribute('title', 'Open Topologies menu');
        const openTopologies = (ev) => {
            if (ev) {
                const target = ev.target;
                if (target && target.closest && (
                    target.closest('#topo-active-save') ||
                    target.closest('#topo-active-dots') ||
                    target.closest('#topo-active-shared-by')
                )) {
                    return;
                }
                ev.preventDefault();
                ev.stopPropagation();
            }
            FileOps._toggleTopologiesFromIndicator(innerEl);
        };
        innerEl.addEventListener('click', openTopologies);
        innerEl.addEventListener('keydown', (ev) => {
            if (ev.key === 'Enter' || ev.key === ' ') openTopologies(ev);
        });
    },

    _toggleTopologiesFromIndicator(anchorEl) {
        const dropdown = document.getElementById('topologies-dropdown-menu');
        const btnTopo = document.getElementById('btn-topologies');
        if (!dropdown) {
            if (btnTopo) btnTopo.click();
            return;
        }
        const isVisible = dropdown.style.display === 'block' && !dropdown.classList.contains('is-closing');
        if (isVisible) {
            FileOps._hideTopologiesDropdown(dropdown, btnTopo);
            return;
        }

        const editor = window.topologyEditor || window.editor || null;
        if (editor && typeof editor.hideAllSelectionToolbars === 'function') {
            editor.hideAllSelectionToolbars();
        }
        const debugPanel = document.getElementById('debug-dnos-topo-selector');
        if (debugPanel) debugPanel.remove();
        const dnaasDialog = document.getElementById('dnaas-topology-dialog');
        if (dnaasDialog) dnaasDialog.remove();
        const dnaasPanel = document.getElementById('dnaas-panel');
        const dnaasBtn = document.getElementById('btn-dnaas');
        if (dnaasPanel && dnaasPanel.style.display === 'block') {
            dnaasPanel.style.display = 'none';
            if (dnaasBtn) dnaasBtn.classList.remove('dnaas-panel-open');
        }
        const nmPanel = document.getElementById('network-mapper-panel');
        const nmBtn = document.getElementById('btn-network-mapper');
        if (nmPanel && nmPanel.style.display === 'block') {
            nmPanel.style.display = 'none';
            if (nmBtn) nmBtn.classList.remove('nm-panel-open');
        }

        if (dropdown._topologiesCloseTimer) {
            clearTimeout(dropdown._topologiesCloseTimer);
            dropdown._topologiesCloseTimer = null;
        }
        dropdown.classList.remove('is-closing', 'is-open');
        dropdown.classList.add('is-preparing');
        dropdown.style.display = 'block';
        dropdown.style.position = 'fixed';
        dropdown.style.visibility = 'hidden';
        dropdown.style.pointerEvents = 'none';
        if (btnTopo) btnTopo.classList.add('topologies-open');
        const openToken = String(Date.now()) + '-' + Math.random().toString(36).slice(2);
        dropdown.dataset.openToken = openToken;
        // The bottom-left active-topology pill is a shortcut to the same
        // Topologies menu, not a spatial anchor. Anchoring the full dropdown
        // to that pill makes the panel float mid-canvas above the HUD, which
        // looks detached and can cover the topology. Keep placement identical
        // to the toolbar Topologies button no matter which shortcut opened it.
        const rect = (btnTopo || anchorEl || dropdown).getBoundingClientRect();

        const revealDropdown = () => {
            if (dropdown.dataset.openToken !== openToken || dropdown.classList.contains('is-closing')) return;
            if (editor && FileOps._renderCustomSectionsInDropdown) {
                FileOps._renderCustomSectionsInDropdown(editor);
                editor._topoDropdownThemeDirty = false;
            }
            requestAnimationFrame(() => {
                if (dropdown.dataset.openToken !== openToken || dropdown.classList.contains('is-closing')) return;
                if (FileOps._fitDropdownToContent) FileOps._fitDropdownToContent();
                FileOps._placeTopologiesDropdown(dropdown, rect);
                dropdown.classList.remove('is-preparing');
                dropdown.classList.add('is-opening');
                dropdown.style.visibility = '';
                requestAnimationFrame(() => {
                    if (dropdown.dataset.openToken !== openToken || dropdown.classList.contains('is-closing')) return;
                    dropdown.classList.remove('is-opening');
                    dropdown.classList.add('is-open');
                    dropdown.style.pointerEvents = '';
                });
            });
        };

        if (FileOps._refreshSharingCache) {
            FileOps._suspendDropdownRefresh = (FileOps._suspendDropdownRefresh || 0) + 1;
            const refreshPromise = FileOps._refreshSharingCache(true).catch(() => {});
            const boundedRefresh = Promise.race([
                refreshPromise,
                new Promise(resolve => setTimeout(resolve, 160))
            ]);
            boundedRefresh.then(revealDropdown);
            refreshPromise.finally(() => {
                FileOps._suspendDropdownRefresh = Math.max(
                    0, (FileOps._suspendDropdownRefresh || 1) - 1,
                );
            });
        } else {
            if (window.TopologyDomains && window.TopologyDomains.fetchDomains) {
                window.TopologyDomains.fetchDomains().catch(() => {});
            }
            revealDropdown();
        }
    },

    _hideTopologiesDropdown(dropdown, btnTopo) {
        if (!dropdown) return;
        if (dropdown._topologiesCloseTimer) {
            clearTimeout(dropdown._topologiesCloseTimer);
            dropdown._topologiesCloseTimer = null;
        }
        dropdown.classList.remove('is-preparing', 'is-opening', 'is-open');
        dropdown.classList.add('is-closing');
        dropdown.style.pointerEvents = 'none';
        if (btnTopo) btnTopo.classList.remove('topologies-open');
        dropdown._topologiesCloseTimer = setTimeout(() => {
            if (!dropdown.classList.contains('is-closing')) return;
            dropdown.style.display = 'none';
            dropdown.style.pointerEvents = '';
            dropdown.classList.remove('is-closing');
            delete dropdown.dataset.openToken;
            dropdown._topologiesCloseTimer = null;
        }, 180);
    },

    _placeTopologiesDropdown(dropdown, anchorRect) {
        if (!dropdown) return;
        const rect = anchorRect || dropdown.getBoundingClientRect();
        const left = FileOps._clampDropdownLeft
            ? FileOps._clampDropdownLeft(rect.left)
            : Math.max(12, Math.min(rect.left, window.innerWidth - 340));
        const h = dropdown.offsetHeight || 360;
        let top = rect.top - h - 8;
        if (top < 12) top = Math.min(rect.bottom + 8, window.innerHeight - h - 12);
        dropdown.style.left = `${left}px`;
        dropdown.style.top = `${Math.max(12, top)}px`;
    },

    // ========================================================================
    // DOMAIN DOT NAVIGATION
    // ========================================================================

    _domainTopoCache: null,
    _domainTopoCacheId: null,

    async _refreshDomainDots(sectionId, currentName, sharedInfo) {
        const dotsEl = document.getElementById('topo-active-dots');
        if (!dotsEl) return;
        if (!sectionId) { dotsEl.style.display = 'none'; return; }

        const isSharedIn = !!(sharedInfo && (sharedInfo.isSharedIn || sharedInfo.isInbox));

        try {
            // Unified shape for both own + shared-in so the rest of
            // this function doesn't care where the list came from:
            //   { name, filename, id?, shared }
            // id is only meaningful for shared-in (the backend uses
            // topology_id there; own-section loads are by filename).
            let topos;
            if (isSharedIn) {
                // Shared-in domains + the synthetic "Shared with me"
                // inbox live in user_store -- /api/sections has no
                // idea they exist. Mirror the endpoint + shape used
                // by _loadSharedInDomainTopologiesInline so the dots
                // lineup matches the dropdown lineup exactly.
                const authFetch = (window.TopologyAuth && window.TopologyAuth.authFetch)
                    ? window.TopologyAuth.authFetch : (u, o) => fetch(u, o);
                const resp = await authFetch('/api/domains/' + encodeURIComponent(sectionId) + '/topologies');
                if (!resp.ok) throw new Error('shared-in topologies fetch failed');
                const list = await resp.json();
                if (!Array.isArray(list)) throw new Error('shared-in topologies shape');
                topos = list.map(t => ({
                    name: t.name || '',
                    filename: FileOps._sanitizeTopologyBasename(t.name || '') + '.json',
                    id: t.id || null,
                    shared: true
                }));
            } else {
                const resp = await fetch(`/api/sections/${sectionId}/topologies`);
                const data = await resp.json();
                topos = (data.topologies || []).map(t => ({
                    name: (t.filename || t.name || '').replace(/\.json$/i, ''),
                    filename: t.filename || t.name || '',
                    id: null,
                    shared: false
                }));
            }

            if (topos.length <= 1) {
                dotsEl.style.display = 'none';
                FileOps._domainTopoCache = null;
                FileOps._domainTopoCacheShared = null;
                return;
            }

            FileOps._domainTopoCache = topos;
            FileOps._domainTopoCacheId = sectionId;
            FileOps._domainTopoCacheShared = isSharedIn ? (sharedInfo || {}) : null;

            const currentFile = (currentName || '').replace(/\.json$/i, '');
            dotsEl.innerHTML = '';
            dotsEl.style.display = 'flex';

            let activeDotTip = null;
            const removeDotTip = () => { if (activeDotTip) { activeDotTip.remove(); activeDotTip = null; } };

            topos.forEach((entry, idx) => {
                const topoName = (entry.name || entry.filename || '').replace(/\.json$/i, '');
                const isCurrent = topoName === currentFile;
                const keyNum = idx < 9 ? String(idx + 1) : '';
                const dot = document.createElement('button');
                dot.style.cssText = `
                    width: ${isCurrent ? 10 : 6}px; height: ${isCurrent ? 10 : 6}px;
                    border-radius: 50%; border: none; padding: 0; cursor: pointer;
                    background: ${isCurrent ? '#fff' : 'rgba(255,255,255,0.35)'};
                    box-shadow: ${isCurrent ? '0 0 6px rgba(255,255,255,0.6)' : 'none'};
                    transition: all 0.15s ease; flex-shrink: 0; position: relative;
                `;
                dot.onmouseenter = () => {
                    if (!isCurrent) { dot.style.background = 'rgba(255,255,255,0.7)'; dot.style.transform = 'scale(1.4)'; }
                    removeDotTip();
                    const dr = dot.getBoundingClientRect();
                    const tip = document.createElement('div');
                    tip.style.cssText = `
                        position:fixed; z-index:100001; pointer-events:none;
                        bottom:${window.innerHeight - dr.top + 6}px; left:${dr.left + dr.width / 2}px;
                        transform:translateX(-50%); display:flex; align-items:center; gap:5px;
                        padding:4px 8px; border-radius:6px; white-space:nowrap;
                        background:rgba(15,15,30,0.95); box-shadow:0 3px 12px rgba(0,0,0,0.4);
                        opacity:0; transition:opacity 0.08s ease;
                    `;
                    const nameSpan = document.createElement('span');
                    nameSpan.textContent = topoName;
                    nameSpan.style.cssText = 'font-size:10px;color:rgba(255,255,255,0.9);font-weight:500;font-family:Poppins,-apple-system,sans-serif;max-width:180px;overflow:hidden;text-overflow:ellipsis;';
                    tip.appendChild(nameSpan);
                    if (keyNum) {
                        const kbd = document.createElement('kbd');
                        kbd.textContent = keyNum;
                        kbd.style.cssText = `
                            display:inline-block; min-width:15px; text-align:center;
                            padding:1px 4px; font-size:9px; font-weight:600;
                            font-family:-apple-system,'SF Mono',Menlo,Consolas,monospace;
                            background:linear-gradient(180deg,rgba(255,255,255,0.18),rgba(255,255,255,0.06));
                            border:1px solid rgba(255,255,255,0.22); border-bottom-width:2px;
                            border-radius:3px; color:rgba(255,255,255,0.9);
                            box-shadow:0 1px 0 rgba(0,0,0,0.35);
                        `;
                        tip.appendChild(kbd);
                    }
                    document.body.appendChild(tip);
                    requestAnimationFrame(() => { tip.style.opacity = '1'; });
                    activeDotTip = tip;
                };
                dot.onmouseleave = () => {
                    if (!isCurrent) { dot.style.background = 'rgba(255,255,255,0.35)'; dot.style.transform = 'scale(1)'; }
                    removeDotTip();
                };
                dot.onclick = (ev) => { ev.stopPropagation(); removeDotTip(); FileOps._navigateToTopology(idx); };
                dotsEl.appendChild(dot);
            });
        } catch (_) {
            dotsEl.style.display = 'none';
        }
    },

    async _navigateToTopology(index, opts = {}) {
        const topos = FileOps._domainTopoCache;
        const sectionId = FileOps._domainTopoCacheId;
        const sharedInfo = FileOps._domainTopoCacheShared;
        if (!topos || !sectionId || index < 0 || index >= topos.length) return;

        const editor = window.topologyEditor || window.editor;
        if (!editor) return;

        const entry = topos[index];
        const topoName = (entry && (entry.name || entry.filename) || '').replace(/\.json$/i, '');

        let info;
        try { info = JSON.parse(localStorage.getItem('topo_active')); } catch (_) {}
        const currentName = (info?.name || '').replace(/\.json$/i, '');
        if (topoName === currentName) return;
        if (!opts.confirmed) {
            FileOps._requestTopologySwitch(editor, topoName, () => {
                FileOps._navigateToTopology(index, { confirmed: true });
            });
            return;
        }

        const loadIdentity = {
            name: topoName,
            filename: entry?.filename || '',
            sectionId,
            topologyId: entry?.id || entry?.topology_id || '',
            shared: sharedInfo || null,
        };
        const loadToken = FileOps._beginTopologyLoad(editor, loadIdentity);

        try {
            let data;
            let domainName;
            let domainColor;
            if (sharedInfo && entry && entry.shared && entry.id) {
                // Shared-in nav mirrors _loadSharedInDomainTopologiesInline's
                // load path (by topology id, not filename) so the exact
                // same endpoint handles both menu clicks and dot clicks.
                const authFetch = (window.TopologyAuth && window.TopologyAuth.authFetch)
                    ? window.TopologyAuth.authFetch : (u, o) => fetch(u, o);
                const r = await authFetch('/api/domains/' + encodeURIComponent(sectionId)
                    + '/topologies/' + encodeURIComponent(entry.id));
                if (!r.ok) {
                    const err = await r.json().catch(() => ({}));
                    FileOps._cancelTopologyLoad(editor, loadToken);
                    editor.showToast(err.detail || 'Failed to open shared topology', 'error');
                    return;
                }
                if (!FileOps._isTopologyLoadCurrent(editor, loadToken)) return;
                const payload = await r.json();
                data = payload.data || payload;
                domainName = (info && info.domain) || (sharedInfo.isInbox ? 'Shared with me' : 'Shared');
                domainColor = (info && info.color) || '#a78bfa';
            } else {
                const resp = await fetch(`/api/sections/${sectionId}/topologies/${entry.filename}`);
                if (!FileOps._isTopologyLoadCurrent(editor, loadToken)) return;
                data = await resp.json();
                if (data.error) {
                    FileOps._cancelTopologyLoad(editor, loadToken);
                    editor.showToast(data.error, 'error');
                    return;
                }
                const sec = (editor._customSections || []).find(s => s.id === sectionId);
                domainName = sec?.name || info?.domain || '';
                domainColor = sec?.color || info?.color || '';
            }

            if (!FileOps._isTopologyLoadCurrent(editor, loadToken)) return;
            const loaded = FileOps._loadIntoEditor(editor, data, {
                ...loadIdentity,
                domain: domainName,
                color: domainColor,
                loadToken,
            });
            if (!loaded) return;
            editor.showToast(`${topoName}  (${index + 1}/${topos.length})`, 'success');
        } catch (err) {
            if (!FileOps._isTopologyLoadCurrent(editor, loadToken)) return;
            FileOps._cancelTopologyLoad(editor, loadToken);
            editor.showToast('Failed to load: ' + err.message, 'error');
        }
    },

    navigateTopoByOffset(offset) {
        const topos = FileOps._domainTopoCache;
        if (!topos || topos.length <= 1) return;
        let info;
        try { info = JSON.parse(localStorage.getItem('topo_active')); } catch (_) {}
        const currentName = (info?.name || '').replace(/\.json$/i, '');
        const currentIdx = topos.findIndex(entry => {
            const entryName = (entry && (entry.name || entry.filename) || '')
                .replace(/\.json$/i, '');
            return entryName === currentName;
        });
        if (currentIdx < 0) return;
        const newIdx = (currentIdx + offset + topos.length) % topos.length;
        FileOps._navigateToTopology(newIdx);
    },

    // ========================================================================
    // NEW / CLEAR CANVAS
    // ========================================================================

    confirmNewTopology(editor) {
        if (editor.objects.length === 0) {
            FileOps._showNewTopologyDomainPicker(editor);
            return;
        }
        FileOps._autoSaveThenNewTopology(editor);
    },

    clearCanvas(editor) {
        if (editor.objects.length === 0) {
            FileOps.performClearCanvas(editor, { preserveActive: true });
            return;
        }
        if (FileOps._hasPersistentAutoSaveTarget(editor, { allowEmpty: true })) {
            FileOps._clearCurrentTopologyOnly(editor);
            return;
        }
        FileOps.performClearCanvas(editor);
        FileOps._showNewTopologyDomainPicker(editor);
    },

    async _clearCurrentTopologyOnly(editor) {
        let info = null;
        try { info = JSON.parse(localStorage.getItem('topo_active') || '{}'); } catch (_) {}
        const activeName = (info && info.name || FileOps._activeTopologyBasename() || 'current topology')
            .replace(/\.json$/i, '');
        const ok = window.confirm(
            `Clear "${activeName}" only?\n\nThis saves an empty canvas to the currently opened topology. Other topologies and domains are untouched.`
        );
        if (!ok) return;

        const before = Array.isArray(editor.objects) ? editor.objects.length : 0;
        editor._intentionalObjectCountDrop = {
            before,
            expiresAt: Date.now() + 5000,
            reason: 'clear-current-topology',
        };
        FileOps.performClearCanvas(editor, { preserveActive: true, markClean: false });
        const emptyData = FileOps.generateTopologyData(editor);
        try {
            editor.autoSave({ force: true, allowEmpty: true });
            await FileOps._saveCurrentTopologyBeforeSwitch(editor, {
                allowEmpty: true,
                data: emptyData,
                silent: true,
            });
            FileOps._writeLocalCurrentSnapshot(editor, emptyData);
            FileOps._markTopologyClean(editor, 'clear-current-topology');
            editor.showToast(`Cleared "${activeName}" only`, 'success');
        } catch (err) {
            editor.showToast('Clear save failed: ' + (err && err.message || err), 'error');
        }
    },

    async _autoSaveThenNewTopology(editor) {
        try {
            await FileOps._saveCurrentTopologyBeforeSwitch(editor, { allowEmpty: true });
        } catch (err) {
            editor.showToast('Save before new topology failed: ' + (err && err.message || err), 'error');
            return;
        }

        FileOps.performClearCanvas(editor);
        FileOps._showNewTopologyDomainPicker(editor);
    },

    _showNewTopologyDomainPicker(editor) {
        const stale = document.getElementById('new-topo-domain-picker');
        if (stale) stale.remove();

        // Modal overlays must follow the *app* theme (not the inverted
        // "Topologies menu" convention `_menuDark` uses). Dark mode means
        // dark card; light mode means light card. Anything else makes
        // the picker appear ghosted on the canvas it's covering.
        const isDk = (() => {
            try {
                if (editor && typeof editor.darkMode === 'boolean') return !!editor.darkMode;
            } catch (_) {}
            return document.body.classList.contains('dark-mode');
        })();
        const t = {
            bg: isDk ? 'linear-gradient(135deg, rgba(15,15,25,0.92), rgba(10,10,18,0.96))' : 'linear-gradient(135deg, rgba(255,255,255,0.95), rgba(240,240,245,0.98))',
            border: isDk ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.08)',
            text: isDk ? '#e2e8f0' : '#1e293b',
            muted: isDk ? '#94a3b8' : '#64748b',
            input: isDk ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)',
            inputBorder: isDk ? 'rgba(255,255,255,0.16)' : 'rgba(0,0,0,0.12)',
            iconStroke: isDk ? 'rgba(255,255,255,0.75)' : 'rgba(0,0,0,0.5)',
            accent: '#6366f1',                 // indigo -- matches "Manage Topology Domains" header
            accentBgDk: 'rgba(99,102,241,0.14)',
            accentBgLt: 'rgba(99,102,241,0.10)',
            accentBorderDk: 'rgba(99,102,241,0.38)',
            accentBorderLt: 'rgba(99,102,241,0.40)',
            // Brand variables for the breadcrumb. Inline fallbacks so we
            // still light up correctly if the user is on a stylesheet
            // build that predates the CSS variable being registered.
            cyan: 'var(--dn-cyan, #00B4D8)',
            cloud: isDk ? 'rgba(226, 232, 240, 0.78)' : 'var(--dn-cloud-soft, #94a3b8)',
        };
        const icons = FileOps._sectionIcons();
        const colors = FileOps._sectionColors();

        // The "owned domains" view drives the onboarding decision: a
        // user whose only section is the built-in Bugs domain (or the
        // synthetic Shared-with-me bucket) is effectively starting
        // from zero and is better served by the create-domain pane up
        // front. Once they've owned at least one domain we default to
        // the picker pane so they can re-use it for follow-up
        // topologies.
        const _ownedSections = () => (editor._customSections || []).filter(s =>
            !s.builtin && s.id !== '__shared_with_me'
        );

        const overlay = document.createElement('div');
        overlay.id = 'new-topo-domain-picker';
        overlay.style.cssText = `position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);backdrop-filter:blur(6px);z-index:10001;display:flex;align-items:center;justify-content:center;`;

        const card = document.createElement('div');
        card.style.cssText = `background:${t.bg};border:1px solid ${t.border};border-radius:14px;padding:20px;min-width:340px;max-width:420px;box-shadow:0 12px 48px rgba(0,0,0,0.3);backdrop-filter:blur(16px);font-family:'Poppins',-apple-system,sans-serif;`;

        // Multi-pane wizard inside a single overlay so the flow never
        // pops a separate dialog over itself. The card skeleton is
        // rendered once and the three panes (.nt-pane-domain,
        // .nt-pane-create-domain, .nt-pane-topology) are toggled via
        // display:none. A two-step breadcrumb (Domain -> Topology)
        // up top shows progress -- current step in --dn-cyan,
        // completed step fades to the cloud-soft tone.
        //
        // Cross-pane state lives in `wizardState`:
        //   - pane             : the active pane name.
        //   - createdDomain    : {id,name,color} once a fresh domain
        //                        has been persisted server-side.
        //   - topologyCommitted: true once we have published the
        //                        topology to the indicator (so Cancel
        //                        after-domain-create can surface the
        //                        "Domain X created. Add a topology
        //                        when you're ready." toast).
        //   - typedTopologyName: last typed value in the domain-pane
        //                        name input, carried forward to the
        //                        topology pane so the user doesn't
        //                        have to retype it.
        card.innerHTML = `
            <div class="nt-breadcrumb" role="navigation" aria-label="New topology steps"
                 style="display:flex;align-items:center;gap:6px;font-size:10px;letter-spacing:0.4px;text-transform:uppercase;font-weight:600;margin-bottom:10px;color:${t.muted};">
                <span class="nt-crumb-domain" style="color:${t.cyan};border-bottom:1.5px solid ${t.cyan};padding-bottom:2px;">Domain</span>
                <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="${t.muted}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;opacity:0.55;"><polyline points="9 18 15 12 9 6"/></svg>
                <span class="nt-crumb-topology" style="color:${t.muted};border-bottom:1.5px solid transparent;padding-bottom:2px;">Topology</span>
            </div>

            <div class="nt-pane nt-pane-domain">
                <div style="font-size:15px;font-weight:600;color:${t.text};margin-bottom:4px;">New Topology</div>
                <div class="nt-subtitle" style="font-size:11px;color:${t.muted};margin-bottom:10px;"></div>
                <label style="display:block;font-size:10.5px;font-weight:600;color:${t.muted};letter-spacing:0.4px;text-transform:uppercase;margin-bottom:5px;">Topology name</label>
                <input class="nt-name" type="text" placeholder="Untitled" autocomplete="off" spellcheck="false"
                    style="width:100%;box-sizing:border-box;padding:8px 10px;margin-bottom:14px;
                           background:${t.input};border:1px solid ${t.inputBorder};border-radius:8px;
                           color:${t.text};font-size:13px;font-family:'Poppins',-apple-system,sans-serif;outline:none;" />
                <div class="nt-domains" style="display:flex;flex-direction:column;gap:6px;margin-bottom:10px;max-height:240px;overflow-y:auto;"></div>
                <button class="nt-new-domain" title="Create a new domain without leaving this wizard"
                    style="display:flex;align-items:center;gap:10px;padding:10px 12px;width:100%;text-align:left;
                           background:${isDk ? t.accentBgDk : t.accentBgLt};
                           border:1px dashed ${isDk ? t.accentBorderDk : t.accentBorderLt};
                           border-left:3px solid ${t.accent};
                           border-radius:8px;cursor:pointer;transition:all 0.15s ease;margin-bottom:14px;">
                    <div style="width:28px;height:28px;border-radius:6px;background:${isDk ? 'rgba(99,102,241,0.20)' : 'rgba(99,102,241,0.15)'};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                        <svg viewBox="0 0 24 24" width="14" height="14" style="stroke:${t.accent};color:${t.accent};" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="12" y1="5" x2="12" y2="19"/>
                            <line x1="5" y1="12" x2="19" y2="12"/>
                        </svg>
                    </div>
                    <div style="flex:1;min-width:0;">
                        <div style="font-size:13px;font-weight:600;color:${t.accent};">Create new domain</div>
                        <div style="font-size:10.5px;color:${t.muted};margin-top:1px;">Name, icon, and color -- all in this wizard</div>
                    </div>
                    <svg viewBox="0 0 24 24" width="14" height="14" style="stroke:${t.muted};flex-shrink:0;opacity:0.6;" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="9 18 15 12 9 6"/>
                    </svg>
                </button>
                <div style="display:flex;gap:8px;justify-content:flex-end;">
                    <button class="nt-skip" style="padding:7px 14px;background:transparent;border:1px solid ${t.border};border-radius:8px;color:${t.muted};cursor:pointer;font-size:12px;">No domain</button>
                    <button class="nt-cancel" style="padding:7px 14px;background:transparent;border:1px solid ${t.border};border-radius:8px;color:${t.text};cursor:pointer;font-size:12px;">Cancel</button>
                </div>
            </div>

            <div class="nt-pane nt-pane-create-domain" style="display:none;">
                <div style="font-size:15px;font-weight:600;color:${t.text};margin-bottom:4px;">Create new domain</div>
                <div class="nt-cd-subtitle" style="font-size:11px;color:${t.muted};margin-bottom:14px;">Give your domain a name, icon, and color. You'll name the topology next.</div>
                <label style="display:block;font-size:10.5px;font-weight:600;color:${t.muted};letter-spacing:0.4px;text-transform:uppercase;margin-bottom:5px;">Domain name</label>
                <input class="nt-domain-name" type="text" placeholder="My Lab" autocomplete="off" spellcheck="false" maxlength="60"
                    style="width:100%;box-sizing:border-box;padding:8px 10px;margin-bottom:12px;
                           background:${t.input};border:1px solid ${t.inputBorder};border-radius:8px;
                           color:${t.text};font-size:13px;font-family:'Poppins',-apple-system,sans-serif;outline:none;" />
                <div style="font-size:9px;font-weight:700;color:${t.muted};margin-bottom:4px;text-transform:uppercase;letter-spacing:0.5px;">Icon</div>
                <div class="nt-icons" style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px;max-height:120px;overflow-y:auto;">
                    ${icons.map(ic => `<button class="nt-icon-btn" data-icon="${ic.id}" type="button" title="${ic.id}" style="width:28px;height:28px;padding:0;background:${t.input};border:1.5px solid ${t.inputBorder};border-radius:7px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.15s;"><svg viewBox="0 0 24 24" width="13" height="13" style="stroke:${t.iconStroke};color:${t.iconStroke};">${ic.svg}</svg></button>`).join('')}
                </div>
                <div style="font-size:9px;font-weight:700;color:${t.muted};margin-bottom:4px;text-transform:uppercase;letter-spacing:0.5px;">Color</div>
                <div class="nt-colors" style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:14px;">
                    ${colors.map(c => `<button class="nt-color-btn" data-color="${c}" type="button" style="width:22px;height:22px;background:${c};border:2px solid transparent;border-radius:50%;cursor:pointer;transition:all 0.15s;box-shadow:0 2px 6px ${c}40;"></button>`).join('')}
                </div>
                <div class="nt-cd-footer" style="display:flex;gap:8px;justify-content:space-between;align-items:center;">
                    <button class="nt-cd-back" style="padding:7px 12px;background:transparent;border:1px solid ${t.border};border-radius:8px;color:${t.muted};cursor:pointer;font-size:12px;display:inline-flex;align-items:center;gap:5px;">
                        <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
                        Back
                    </button>
                    <div style="display:flex;gap:8px;">
                        <button class="nt-cd-cancel" style="padding:7px 14px;background:transparent;border:1px solid ${t.border};border-radius:8px;color:${t.text};cursor:pointer;font-size:12px;">Cancel</button>
                        <button class="nt-cd-create" style="padding:7px 16px;background:linear-gradient(135deg,rgba(99,102,241,0.85),rgba(79,70,229,0.95));border:1px solid rgba(99,102,241,0.45);border-radius:8px;color:#fff;font-size:12px;font-weight:600;cursor:pointer;transition:filter 0.15s, opacity 0.2s;">Create domain</button>
                    </div>
                </div>
            </div>

            <div class="nt-pane nt-pane-topology" style="display:none;">
                <div style="font-size:15px;font-weight:600;color:${t.text};margin-bottom:4px;">Name your topology</div>
                <div class="nt-topology-subtitle" style="font-size:11px;color:${t.muted};margin-bottom:14px;"></div>
                <label style="display:block;font-size:10.5px;font-weight:600;color:${t.muted};letter-spacing:0.4px;text-transform:uppercase;margin-bottom:5px;">Topology name</label>
                <input class="nt-topology-name" type="text" placeholder="Untitled" autocomplete="off" spellcheck="false"
                    style="width:100%;box-sizing:border-box;padding:8px 10px;margin-bottom:14px;
                           background:${t.input};border:1px solid ${t.inputBorder};border-radius:8px;
                           color:${t.text};font-size:13px;font-family:'Poppins',-apple-system,sans-serif;outline:none;" />
                <div style="display:flex;gap:8px;justify-content:space-between;align-items:center;">
                    <button class="nt-tp-back" style="padding:7px 12px;background:transparent;border:1px solid ${t.border};border-radius:8px;color:${t.muted};cursor:pointer;font-size:12px;display:inline-flex;align-items:center;gap:5px;">
                        <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
                        Back
                    </button>
                    <div style="display:flex;gap:8px;">
                        <button class="nt-tp-cancel" style="padding:7px 14px;background:transparent;border:1px solid ${t.border};border-radius:8px;color:${t.text};cursor:pointer;font-size:12px;">Cancel</button>
                        <button class="nt-tp-create" style="padding:7px 16px;background:linear-gradient(135deg,rgba(0,180,216,0.92),rgba(0,140,180,0.95));border:1px solid rgba(0,180,216,0.45);border-radius:8px;color:#fff;font-size:12px;font-weight:600;cursor:pointer;transition:filter 0.15s;">Create topology</button>
                    </div>
                </div>
            </div>
        `;

        const domainsList = card.querySelector('.nt-domains');
        const subtitleEl = card.querySelector('.nt-subtitle');
        const nameInput = card.querySelector('.nt-name');
        const crumbDomain = card.querySelector('.nt-crumb-domain');
        const crumbTopology = card.querySelector('.nt-crumb-topology');
        const paneDomain = card.querySelector('.nt-pane-domain');
        const paneCreateDomain = card.querySelector('.nt-pane-create-domain');
        const paneTopology = card.querySelector('.nt-pane-topology');
        const domainNameInput = card.querySelector('.nt-domain-name');
        const topologyNameInput = card.querySelector('.nt-topology-name');
        const topologySubtitle = card.querySelector('.nt-topology-subtitle');
        const cdBackBtn = card.querySelector('.nt-cd-back');
        const cdCancelBtn = card.querySelector('.nt-cd-cancel');
        const cdCreateBtn = card.querySelector('.nt-cd-create');
        const tpBackBtn = card.querySelector('.nt-tp-back');
        const tpCancelBtn = card.querySelector('.nt-tp-cancel');
        const tpCreateBtn = card.querySelector('.nt-tp-create');

        const wizardState = {
            pane: 'domain',
            createdDomain: null,
            topologyCommitted: false,
            typedTopologyName: '',
            selectedIcon: icons[0].id,
            selectedColor: colors[0],
        };

        // Default suggestion is "Untitled". When the user picks a domain
        // we'll fetch that domain's existing topology list and bump to
        // "Untitled 2", "Untitled 3", ... if the basename collides. The
        // input itself is left blank-styled with a placeholder so users
        // see the suggestion without us clobbering whatever they type.
        const SUGGEST_BASE = 'Untitled';
        nameInput.value = SUGGEST_BASE;

        // ---- Pane / breadcrumb switching ------------------------------
        const updateBreadcrumb = () => {
            if (!crumbDomain || !crumbTopology) return;
            // Topology pane = Domain step is complete (cloud tone, no
            // underline), Topology step is active (cyan underline).
            // Anything else = Domain in progress, Topology pending.
            const onTopology = wizardState.pane === 'topology';
            crumbDomain.style.color = onTopology ? t.cloud : t.cyan;
            crumbDomain.style.borderBottomColor = onTopology ? 'transparent' : t.cyan;
            crumbTopology.style.color = onTopology ? t.cyan : t.muted;
            crumbTopology.style.borderBottomColor = onTopology ? t.cyan : 'transparent';
        };

        const showPane = (paneName) => {
            wizardState.pane = paneName;
            if (paneDomain) paneDomain.style.display = (paneName === 'domain') ? 'block' : 'none';
            if (paneCreateDomain) paneCreateDomain.style.display = (paneName === 'create-domain') ? 'block' : 'none';
            if (paneTopology) paneTopology.style.display = (paneName === 'topology') ? 'block' : 'none';
            updateBreadcrumb();
            // Auto-focus the primary input in the active pane after a
            // brief tick so the browser has time to lay out the newly
            // visible elements (focus() before layout = ignored).
            try {
                setTimeout(() => {
                    if (paneName === 'domain' && nameInput) {
                        nameInput.focus(); nameInput.select();
                    } else if (paneName === 'create-domain' && domainNameInput) {
                        domainNameInput.focus(); domainNameInput.select();
                    } else if (paneName === 'topology' && topologyNameInput) {
                        topologyNameInput.focus(); topologyNameInput.select();
                    }
                }, 30);
            } catch (_) {}
        };

        // Selecting the text on focus mimics OS "Save As" affordance:
        // the user can immediately type a real name, hit Enter, and the
        // first domain row receives the click.
        nameInput.addEventListener('focus', () => {
            try { nameInput.select(); } catch (_) {}
        });
        nameInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const firstBtn = domainsList.querySelector('button');
                if (firstBtn) firstBtn.click();
            } else if (e.key === 'Escape') {
                closeOverlay();
            }
            e.stopPropagation();
        });
        nameInput.addEventListener('input', () => {
            // Carry the typed value forward so the topology-naming step
            // in the post-domain-create flow can pre-fill it.
            wizardState.typedTopologyName = (nameInput.value || '').trim();
        });

        // Build a unique "Untitled N" against the chosen domain's existing
        // topologies so a fresh canvas already has a save-friendly name
        // before the user types anything. Falls back to whatever the user
        // typed (with `Untitled` as a last-resort default) on network errors.
        const _resolveSuggestedName = async (sectionId, sourceInput) => {
            const inputEl = sourceInput || nameInput;
            const typed = (inputEl && inputEl.value || '').trim();
            if (typed && typed.toLowerCase() !== SUGGEST_BASE.toLowerCase()) {
                return typed;
            }
            try {
                const authFetch = (window.TopologyAuth && window.TopologyAuth.authFetch)
                    ? window.TopologyAuth.authFetch : (u, o) => fetch(u, o);
                const resp = await authFetch(`/api/sections/${encodeURIComponent(sectionId)}/topologies`);
                if (!resp.ok) return SUGGEST_BASE;
                const data = await resp.json();
                const existing = new Set((data.topologies || []).map(t => {
                    const name = (t.filename || t.name || '').replace(/\.json$/i, '');
                    return name.toLowerCase();
                }));
                if (!existing.has(SUGGEST_BASE.toLowerCase())) return SUGGEST_BASE;
                for (let i = 2; i < 1000; i++) {
                    const candidate = `${SUGGEST_BASE} ${i}`;
                    if (!existing.has(candidate.toLowerCase())) return candidate;
                }
            } catch (_) {}
            return typed || SUGGEST_BASE;
        };

        // --- List renderer (re-used on every refresh event) -----------
        //
        // `highlightIds` is the set of section ids that just appeared or
        // were updated; those rows get a brief ring pulse so the user
        // sees the delta immediately instead of hunting for it.
        const renderDomainList = (highlightIds) => {
            const sections = editor._customSections || [];
            const hasSections = sections.length > 0;
            subtitleEl.textContent = hasSections
                ? 'Select a domain for the new topology'
                : 'You have no domains yet. Create one to continue.';
            // Keep the list slot present (empty) so the "+ Create new
            // domain" button doesn't jump around when domains appear
            // or disappear.
            domainsList.style.marginBottom = hasSections ? '10px' : '0';
            domainsList.innerHTML = '';

            const hi = highlightIds instanceof Set ? highlightIds
                : (highlightIds ? new Set([].concat(highlightIds)) : null);

            sections.forEach(sec => {
                const iconSvg = (icons.find(i => i.id === sec.icon) || icons[0]).svg;
                const btn = document.createElement('button');
                btn.style.cssText = `display:flex;align-items:center;gap:10px;padding:10px 12px;background:${sec.color}0d;border:1px solid ${sec.color}30;border-left:3px solid ${sec.color};border-radius:8px;cursor:pointer;transition:all 0.15s;width:100%;text-align:left;`;
                btn.innerHTML = `
                    <div style="width:28px;height:28px;border-radius:6px;background:${sec.color}18;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                        <svg viewBox="0 0 24 24" width="14" height="14" style="stroke:${sec.color};color:${sec.color};">${iconSvg}</svg>
                    </div>
                    <span style="font-size:13px;font-weight:500;color:${t.text};">${sec.name}</span>
                `;
                btn.onmouseenter = () => { btn.style.background = `${sec.color}1a`; btn.style.borderColor = `${sec.color}60`; };
                btn.onmouseleave = () => { btn.style.background = `${sec.color}0d`; btn.style.borderColor = `${sec.color}30`; };
                btn.onclick = async () => {
                    btn.disabled = true;
                    btn.style.opacity = '0.65';
                    const suggested = await _resolveSuggestedName(sec.id);
                    wizardState.topologyCommitted = true;
                    closeOverlay();
                    FileOps.updateTopologyIndicator(suggested, sec.name, sec.color, sec.id);
                    editor.showToast(`New topology "${suggested}" in ${sec.name}`, 'success');
                };
                domainsList.appendChild(btn);

                if (hi && hi.has(sec.id)) {
                    // Subtle ~0.9s ring pulse so a freshly-created domain
                    // is obvious the moment the picker rerenders. Fade to
                    // transparent (not `none`) so the box-shadow
                    // transition interpolates smoothly across all browsers.
                    btn.style.boxShadow = `0 0 0 2px ${sec.color}, 0 6px 18px ${sec.color}60`;
                    btn.style.transition = 'box-shadow 0.9s ease-out, background 0.15s, border-color 0.15s';
                    setTimeout(() => {
                        if (btn.isConnected) btn.style.boxShadow = `0 0 0 0 ${sec.color}00, 0 0 0 0 ${sec.color}00`;
                    }, 60);
                }
            });
        };

        // --- Open / close plumbing ------------------------------------
        //
        // Single teardown path: removes the overlay, drops the Escape
        // listener, AND detaches the `topology-domains:changed` listener
        // so a refresh-after-close doesn't try to mutate a detached DOM.
        // Cancel-mid-flow semantics: if we already persisted a new
        // domain server-side but the user closed before committing the
        // topology, fire a "Domain X created. Add a topology when you're
        // ready." toast so the new (empty) domain doesn't feel orphaned.
        let closed = false;
        const closeOverlay = () => {
            if (closed) return;
            closed = true;
            try { document.removeEventListener('keydown', escHandler); } catch (_) {}
            try { document.removeEventListener('topology-domains:changed', onDomainsChanged); } catch (_) {}
            if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
            const cd = wizardState.createdDomain;
            if (cd && !wizardState.topologyCommitted) {
                try {
                    editor.showToast(
                        `Domain "${cd.name}" created. Add a topology when you're ready.`,
                        'info'
                    );
                } catch (_) {}
            }
        };

        // Snapshot the ids we have BEFORE any listener fires so the
        // first refresh can distinguish "new since you opened the
        // picker" from "was already here". Stored in a closure so it
        // updates after each refresh and only genuinely-new ids pulse.
        let knownIds = new Set((editor._customSections || []).map(s => s.id));

        const onDomainsChanged = (evt) => {
            const before = knownIds;
            const nowSections = editor._customSections || [];
            const nowIds = new Set(nowSections.map(s => s.id));
            const appeared = new Set();
            nowIds.forEach(id => { if (!before.has(id)) appeared.add(id); });
            // Updates (rename/recolor) aren't in `appeared` but the
            // event's detail carries their id; pulse those too.
            try {
                const detailId = evt && evt.detail && evt.detail.domainId;
                if (detailId && before.has(detailId)) appeared.add(detailId);
            } catch (_) {}
            knownIds = nowIds;
            renderDomainList(appeared);
        };

        // ---- Inline "+ Create new domain" wiring ---------------------
        //
        // 2026-05-12 -- previously this button hid the picker and
        // opened the full Manage Topology Domains panel, so the user
        // had to navigate, expand a collapsed form, pick icon/color,
        // create, then close the panel before being dropped back into
        // the picker to finally pick the new domain. The new behaviour
        // swaps the panel out for an inline pane in-place: same card,
        // same overlay, three logical steps (domain -> create-domain
        // -> topology). The flow is one continuous wizard.
        const newDomainBtn = card.querySelector('.nt-new-domain');
        newDomainBtn.onmouseenter = () => {
            newDomainBtn.style.background = isDk ? 'rgba(99,102,241,0.22)' : 'rgba(99,102,241,0.16)';
            newDomainBtn.style.borderColor = isDk ? 'rgba(99,102,241,0.60)' : 'rgba(99,102,241,0.58)';
            newDomainBtn.style.transform = 'translateX(1px)';
        };
        newDomainBtn.onmouseleave = () => {
            newDomainBtn.style.background = isDk ? t.accentBgDk : t.accentBgLt;
            newDomainBtn.style.borderColor = isDk ? t.accentBorderDk : t.accentBorderLt;
            newDomainBtn.style.transform = '';
        };
        newDomainBtn.onclick = () => showPane('create-domain');

        // ---- Pane 2: Create-domain (icon / color grids + commit) ----
        const refreshIconBtns = () => {
            card.querySelectorAll('.nt-icon-btn').forEach(btn => {
                const isActive = btn.dataset.icon === wizardState.selectedIcon;
                btn.style.borderColor = isActive ? wizardState.selectedColor : t.inputBorder;
                btn.style.background = isActive ? wizardState.selectedColor + '20' : t.input;
                const svg = btn.querySelector('svg');
                if (svg) {
                    svg.style.color = isActive ? wizardState.selectedColor : t.iconStroke;
                    svg.style.stroke = isActive ? wizardState.selectedColor : t.iconStroke;
                }
            });
        };
        const refreshColorBtns = () => {
            card.querySelectorAll('.nt-color-btn').forEach(btn => {
                const isActive = btn.dataset.color === wizardState.selectedColor;
                btn.style.borderColor = isActive ? (isDk ? '#fff' : '#1f2937') : 'transparent';
                btn.style.transform = isActive ? 'scale(1.15)' : 'scale(1)';
                btn.style.boxShadow = isActive
                    ? `0 0 8px ${wizardState.selectedColor}60`
                    : `0 2px 6px ${btn.dataset.color}40`;
            });
        };
        card.querySelectorAll('.nt-icon-btn').forEach(btn => {
            btn.addEventListener('click', (ev) => {
                ev.stopPropagation();
                wizardState.selectedIcon = btn.dataset.icon;
                refreshIconBtns();
            });
        });
        card.querySelectorAll('.nt-color-btn').forEach(btn => {
            btn.addEventListener('click', (ev) => {
                ev.stopPropagation();
                wizardState.selectedColor = btn.dataset.color;
                refreshColorBtns();
                refreshIconBtns();
            });
        });
        refreshIconBtns();
        refreshColorBtns();

        const _createDomainViaApi = async () => {
            const rawName = (domainNameInput.value || '').trim();
            if (!rawName) {
                domainNameInput.focus();
                domainNameInput.style.borderColor = '#ef4444';
                setTimeout(() => { domainNameInput.style.borderColor = t.inputBorder; }, 800);
                editor.showToast('Enter a domain name', 'warning');
                return null;
            }
            if (rawName.toLowerCase() === 'dnaas') {
                editor.showToast('"DNAAS" is a reserved domain name', 'warning');
                return null;
            }
            const exists = (editor._customSections || []).some(s =>
                (s.name || '').toLowerCase() === rawName.toLowerCase()
            );
            if (exists) {
                editor.showToast(`Domain "${rawName}" already exists`, 'warning');
                return null;
            }
            cdCreateBtn.disabled = true;
            cdCreateBtn.style.opacity = '0.65';
            const restoreBtn = () => {
                cdCreateBtn.disabled = false;
                cdCreateBtn.style.opacity = '';
            };
            try {
                const resp = await FileOps._authFetch('/api/sections', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: rawName,
                        icon: wizardState.selectedIcon,
                        color: wizardState.selectedColor,
                    }),
                });
                let payload = null;
                try { payload = await resp.json(); } catch (_) {}
                if (!resp.ok || (payload && payload.error)) {
                    const msg = (payload && payload.error) || `HTTP ${resp.status}`;
                    editor.showToast('Domain create failed: ' + msg, 'error');
                    restoreBtn();
                    return null;
                }
                const created = (payload && payload.section) || {
                    id: `sec_${Date.now()}`,
                    name: rawName,
                    icon: wizardState.selectedIcon,
                    color: wizardState.selectedColor,
                };
                // Refresh the in-memory section cache + dropdown so the
                // outer app reflects the new domain immediately (sidebar,
                // top-bar dropdown, etc.). Best-effort -- we don't want a
                // sync glitch to block the wizard transition.
                try {
                    if (typeof editor.loadCustomSections === 'function') {
                        await editor.loadCustomSections();
                    } else {
                        await FileOps.loadCustomSections(editor);
                    }
                } catch (_) {}
                try {
                    document.dispatchEvent(new CustomEvent('topology-domains:changed', {
                        detail: { reason: 'domain-created', domainId: created.id, domainName: created.name },
                    }));
                } catch (_) {}
                wizardState.createdDomain = {
                    id: created.id,
                    name: created.name,
                    color: created.color || wizardState.selectedColor,
                };
                editor.showToast(`Domain "${created.name}" created`, 'success');
                restoreBtn();
                return wizardState.createdDomain;
            } catch (e) {
                editor.showToast('Domain create failed: ' + (e && e.message ? e.message : e), 'error');
                restoreBtn();
                return null;
            }
        };

        const _enterTopologyPane = (sec) => {
            // Subtitle confirms which domain we're saving to, keeping
            // the user oriented after the pane swap.
            if (topologySubtitle) {
                topologySubtitle.textContent = `Saving to ${sec.name}`;
                topologySubtitle.style.color = sec.color || t.muted;
            }
            // Pre-fill: respect anything the user typed in the domain
            // pane, otherwise fall back to a unique "Untitled N" against
            // the just-created domain (empty server-side, so just "Untitled").
            const carry = (wizardState.typedTopologyName || '').trim();
            topologyNameInput.value = carry || SUGGEST_BASE;
            showPane('topology');
        };

        cdBackBtn.onclick = () => {
            // Going back from create-domain to the picker does NOT
            // undo a successful create (the row is already persisted).
            // It simply returns the user to the existing domain list.
            showPane('domain');
        };
        cdCancelBtn.onclick = () => closeOverlay();
        cdCreateBtn.onclick = async () => {
            const created = await _createDomainViaApi();
            if (created) _enterTopologyPane(created);
        };
        domainNameInput.addEventListener('keydown', (ev) => {
            if (ev.key === 'Enter') {
                ev.preventDefault();
                cdCreateBtn.click();
            } else if (ev.key === 'Escape') {
                ev.preventDefault();
                closeOverlay();
            }
            ev.stopPropagation();
        });

        // ---- Pane 3: Topology name commit ----------------------------
        const _commitTopologyToCreatedDomain = async () => {
            const sec = wizardState.createdDomain;
            if (!sec) return;
            const rawName = (topologyNameInput.value || '').trim();
            if (!rawName) {
                topologyNameInput.focus();
                topologyNameInput.style.borderColor = '#ef4444';
                setTimeout(() => { topologyNameInput.style.borderColor = t.inputBorder; }, 800);
                editor.showToast('Enter a topology name', 'warning');
                return;
            }
            tpCreateBtn.disabled = true;
            tpCreateBtn.style.opacity = '0.65';
            const suggested = await _resolveSuggestedName(sec.id, topologyNameInput);
            wizardState.topologyCommitted = true;
            closeOverlay();
            FileOps.updateTopologyIndicator(suggested, sec.name, sec.color, sec.id);
            editor.showToast(`New topology "${suggested}" in ${sec.name}`, 'success');
        };

        tpBackBtn.onclick = () => {
            // Going back from the topology pane re-shows the domain
            // picker. The just-created domain is in the list (with a
            // pulse) thanks to the topology-domains:changed dispatch
            // earlier, so a user that wants to bail on a partial flow
            // can pick a different existing domain and commit there
            // without losing the new domain they made.
            showPane('domain');
        };
        tpCancelBtn.onclick = () => closeOverlay();
        tpCreateBtn.onclick = _commitTopologyToCreatedDomain;
        topologyNameInput.addEventListener('keydown', (ev) => {
            if (ev.key === 'Enter') {
                ev.preventDefault();
                tpCreateBtn.click();
            } else if (ev.key === 'Escape') {
                ev.preventDefault();
                closeOverlay();
            }
            ev.stopPropagation();
        });

        card.querySelector('.nt-skip').onclick = () => {
            const typed = (nameInput.value || '').trim() || SUGGEST_BASE;
            wizardState.topologyCommitted = true;
            closeOverlay();
            // No domain selected -> indicator goes into General mode but
            // we still seed the user's chosen name so Save / autosave pick
            // it up immediately (instead of falling back to "untitled").
            FileOps.updateTopologyIndicator(typed, '', null, null, null, { isGeneral: true });
            editor.showToast(`New topology "${typed}" created`, 'success');
        };
        card.querySelector('.nt-cancel').onclick = closeOverlay;

        overlay.appendChild(card);
        overlay.addEventListener('keydown', (e) => { e.stopPropagation(); });
        overlay.addEventListener('keyup', (e) => { e.stopPropagation(); });
        document.body.appendChild(overlay);
        overlay.onclick = (e) => { if (e.target === overlay) closeOverlay(); };
        // Esc always closes the wizard. We no longer need to guard
        // against "picker hidden behind manage panel" because the new
        // flow keeps everything inline.
        const escHandler = (e) => {
            if (e.key !== 'Escape') return;
            closeOverlay();
        };
        document.addEventListener('keydown', escHandler);

        // Wire the domain-list auto-refresh AFTER the overlay is in the
        // DOM so the first render fires inside the same tick without
        // competing with the appendChild reflow.
        document.addEventListener('topology-domains:changed', onDomainsChanged);
        renderDomainList(null);

        // Zero-section onboarding: jump straight to the create-domain
        // pane so a first-time user doesn't see an empty list before
        // being told they have to create one. The Back button on the
        // create-domain pane still works (it returns to the empty
        // list, which is a useful escape hatch in case they realised
        // they're on the wrong user account).
        if (_ownedSections().length === 0) {
            showPane('create-domain');
        } else {
            // Auto-focus the name input + select the suggested "Untitled" so the
            // user can either type immediately (replaces the suggestion) or
            // hit Enter to accept it and click the first domain.
            try { setTimeout(() => { nameInput.focus(); nameInput.select(); }, 30); } catch (_) {}
        }
    },

    // Save-to-domain picker -- opened from the indicator pill's Save
    // button when the active topology is in the General (no-domain)
    // mode (e.g. right after deleting the topology you were editing).
    //
    // Mirrors the visual language of `_showNewTopologyDomainPicker`
    // but the action is "save the current canvas to the chosen
    // domain" instead of "clear the canvas and start a new topology
    // there". The user types a name once at the top, then clicks any
    // domain to save -- or hits "+ New domain..." to open the manage
    // panel and create one. After a successful save we update the
    // indicator pill so the General mode flips to a normal coloured
    // domain pill, and we register the file with TopologySync (when
    // a multi-user mirror exists) so live-sync picks it up.
    //
    // opts:
    //   defaultName -- pre-populated topology name (string)
    //   onSaved     -- callback fired on successful save (no args)
    _showSaveToDomainPicker(editor, opts) {
        opts = opts || {};
        const stale = document.getElementById('save-to-domain-picker');
        if (stale) stale.remove();

        const isDk = FileOps._menuDark(editor);
        const t = {
            bg: isDk ? 'linear-gradient(135deg, rgba(15,15,25,0.92), rgba(10,10,18,0.96))' : 'linear-gradient(135deg, rgba(255,255,255,0.95), rgba(240,240,245,0.98))',
            border: isDk ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.08)',
            text: isDk ? '#e2e8f0' : '#1e293b',
            muted: isDk ? '#94a3b8' : '#64748b',
            input: isDk ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)',
            inputBorder: isDk ? 'rgba(255,255,255,0.16)' : 'rgba(0,0,0,0.12)',
            accent: '#6366f1',
            accentBgDk: 'rgba(99,102,241,0.14)',
            accentBgLt: 'rgba(99,102,241,0.10)',
            accentBorderDk: 'rgba(99,102,241,0.38)',
            accentBorderLt: 'rgba(99,102,241,0.40)',
        };
        const icons = FileOps._sectionIcons();

        const overlay = document.createElement('div');
        overlay.id = 'save-to-domain-picker';
        overlay.style.cssText = `position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);backdrop-filter:blur(6px);z-index:10001;display:flex;align-items:center;justify-content:center;`;

        const card = document.createElement('div');
        card.style.cssText = `background:${t.bg};border:1px solid ${t.border};border-radius:14px;padding:20px;min-width:340px;max-width:420px;box-shadow:0 12px 48px rgba(0,0,0,0.3);backdrop-filter:blur(16px);font-family:'Poppins',-apple-system,sans-serif;`;

        const defaultName = (opts.defaultName && String(opts.defaultName).trim())
            || ('topology_' + Date.now());

        card.innerHTML = `
            <div style="font-size:15px;font-weight:600;color:${t.text};margin-bottom:4px;">Save to Domain</div>
            <div class="std-subtitle" style="font-size:11px;color:${t.muted};margin-bottom:12px;">
                Pick a domain to save this topology
            </div>
            <label style="display:block;font-size:10.5px;font-weight:600;color:${t.muted};text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px;">Topology name</label>
            <input class="std-name" type="text" autocomplete="off" spellcheck="false"
                style="width:100%;box-sizing:border-box;padding:9px 11px;background:${t.input};
                       border:1px solid ${t.inputBorder};border-radius:8px;color:${t.text};
                       font-size:13px;font-family:inherit;margin-bottom:14px;outline:none;"
                value="" />
            <div class="std-domains" style="display:flex;flex-direction:column;gap:6px;margin-bottom:10px;max-height:240px;overflow-y:auto;"></div>
            <button class="std-new-domain" title="Open Topology Domain management to create a new domain"
                style="display:flex;align-items:center;gap:10px;padding:10px 12px;width:100%;text-align:left;
                       background:${isDk ? t.accentBgDk : t.accentBgLt};
                       border:1px dashed ${isDk ? t.accentBorderDk : t.accentBorderLt};
                       border-left:3px solid ${t.accent};
                       border-radius:8px;cursor:pointer;transition:all 0.15s ease;margin-bottom:14px;">
                <div style="width:28px;height:28px;border-radius:6px;background:${isDk ? 'rgba(99,102,241,0.20)' : 'rgba(99,102,241,0.15)'};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <svg viewBox="0 0 24 24" width="14" height="14" style="stroke:${t.accent};color:${t.accent};" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="12" y1="5" x2="12" y2="19"/>
                        <line x1="5" y1="12" x2="19" y2="12"/>
                    </svg>
                </div>
                <div style="flex:1;min-width:0;">
                    <div style="font-size:13px;font-weight:600;color:${t.accent};">New domain...</div>
                    <div style="font-size:10.5px;color:${t.muted};margin-top:1px;">Opens Topology Domain management</div>
                </div>
                <svg viewBox="0 0 24 24" width="14" height="14" style="stroke:${t.muted};flex-shrink:0;opacity:0.6;" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="9 18 15 12 9 6"/>
                </svg>
            </button>
            <div style="display:flex;gap:8px;justify-content:flex-end;">
                <button class="std-cancel" style="padding:7px 14px;background:transparent;border:1px solid ${t.border};border-radius:8px;color:${t.text};cursor:pointer;font-size:12px;">Cancel</button>
            </div>
        `;

        const nameInput = card.querySelector('.std-name');
        const domainsList = card.querySelector('.std-domains');
        const subtitleEl = card.querySelector('.std-subtitle');
        nameInput.value = defaultName;
        // Pre-select so a user that just wants `topology_<ts>` can
        // hit Enter / click a domain immediately.
        try { nameInput.setSelectionRange(0, nameInput.value.length); } catch (_) {}

        let closed = false;
        let savingTo = null; // section.id while a save is in flight

        const closeOverlay = () => {
            if (closed) return;
            closed = true;
            try { document.removeEventListener('keydown', escHandler); } catch (_) {}
            try { document.removeEventListener('topology-domains:changed', onDomainsChanged); } catch (_) {}
            if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
        };

        // Best-effort lookup of a multi-user mirror so we can register
        // the freshly-saved file with TopologySync. Same shape as the
        // /api/sections load path uses; failures are non-fatal.
        const _registerWithSync = async (sec, topoName) => {
            if (!window.TopologySync || !window.TopologySync.setActive) return;
            try {
                const filename = FileOps._sanitizeTopologyBasename(topoName) + '.json';
                const mr = await fetch('/api/sections/'
                    + encodeURIComponent(sec.id)
                    + '/_mirror-map/'
                    + encodeURIComponent(filename));
                const mm = mr.ok ? await mr.json() : {};
                if (mm && mm.mirrored && mm.topology_id) {
                    const meUser = (window.TopologyAuth
                        && window.TopologyAuth.getUser
                        && window.TopologyAuth.getUser()) || {};
                    window.TopologySync.setActive({
                        owner: meUser.username || '',
                        domain_id: mm.domain_id,
                        topology_id: mm.topology_id,
                        name: topoName,
                        updated_at: mm.updated_at || '',
                        is_shared: false,
                        permission: 'write',
                        domain_name: sec.name,
                        section_id: sec.id,
                        color: sec.color,
                    });
                }
            } catch (_) { /* sync wiring is best-effort */ }
        };

        const saveTo = async (sec) => {
            if (savingTo) return;
            const rawName = (nameInput.value || '').trim();
            if (!rawName) {
                nameInput.focus();
                nameInput.style.borderColor = '#ef4444';
                setTimeout(() => { nameInput.style.borderColor = t.inputBorder; }, 800);
                editor.showToast('Enter a name first', 'warning');
                return;
            }
            if (!editor.objects || editor.objects.length === 0) {
                editor.showToast('Nothing to save -- canvas is empty', 'warning');
                return;
            }
            savingTo = sec.id;
            try {
                const result = await FileOps._sectionSaveWithConflict(
                    editor,
                    sec.id,
                    {
                        name: rawName,
                        topology: FileOps.generateTopologyData(editor)
                    },
                    null,
                );
                if (result && (result.error || result.conflict || result.quota)) {
                    savingTo = null;
                    return;
                }
                // Flip the pill out of General mode now that we have a
                // real domain home. Keep the same name so the user
                // recognises what they just saved.
                FileOps.updateTopologyIndicator(rawName, sec.name, sec.color, sec.id);
                await _registerWithSync(sec, rawName);
                editor.showToast(`Saved "${rawName}" to ${sec.name}`, 'success');
                FileOps._markTopologyClean(editor, 'save-to-domain-picker');
                if (typeof opts.onSaved === 'function') {
                    try { opts.onSaved(); } catch (_) {}
                }
                closeOverlay();
            } catch (e) {
                editor.showToast('Save failed: ' + e.message, 'error');
                savingTo = null;
            }
        };

        const renderDomainList = () => {
            const sections = editor._customSections || [];
            domainsList.innerHTML = '';
            if (sections.length === 0) {
                const empty = document.createElement('div');
                empty.style.cssText = `padding:14px;font-size:11px;color:${t.muted};text-align:center;border:1px dashed ${t.inputBorder};border-radius:8px;`;
                empty.textContent = 'You have no domains yet. Click "New domain..." below to create one.';
                domainsList.appendChild(empty);
                return;
            }
            sections.forEach(sec => {
                const iconSvg = (icons.find(i => i.id === sec.icon) || icons[0]).svg;
                const btn = document.createElement('button');
                btn.style.cssText = `display:flex;align-items:center;gap:10px;padding:10px 12px;background:${sec.color}0d;border:1px solid ${sec.color}30;border-left:3px solid ${sec.color};border-radius:8px;cursor:pointer;transition:all 0.15s;width:100%;text-align:left;`;
                btn.innerHTML = `
                    <div style="width:28px;height:28px;border-radius:6px;background:${sec.color}18;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                        <svg viewBox="0 0 24 24" width="14" height="14" style="stroke:${sec.color};color:${sec.color};">${iconSvg}</svg>
                    </div>
                    <div style="flex:1;min-width:0;">
                        <div style="font-size:13px;font-weight:500;color:${t.text};">${sec.name}</div>
                        <div style="font-size:10.5px;color:${t.muted};margin-top:1px;">Save here</div>
                    </div>
                    <svg viewBox="0 0 24 24" width="14" height="14" style="stroke:${t.muted};flex-shrink:0;opacity:0.6;" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="9 18 15 12 9 6"/>
                    </svg>
                `;
                btn.onmouseenter = () => { btn.style.background = `${sec.color}1a`; btn.style.borderColor = `${sec.color}60`; };
                btn.onmouseleave = () => { btn.style.background = `${sec.color}0d`; btn.style.borderColor = `${sec.color}30`; };
                btn.onclick = () => saveTo(sec);
                domainsList.appendChild(btn);
            });
        };

        const onDomainsChanged = () => renderDomainList();

        // "+ New domain" -> hide the picker (don't destroy it) and open
        // the Manage Topology Domains panel. The same pattern used by
        // _showNewTopologyDomainPicker so a freshly-created domain
        // shows up in the list as soon as we re-show.
        const newDomainBtn = card.querySelector('.std-new-domain');
        newDomainBtn.onmouseenter = () => {
            newDomainBtn.style.background = isDk ? 'rgba(99,102,241,0.22)' : 'rgba(99,102,241,0.16)';
            newDomainBtn.style.borderColor = isDk ? 'rgba(99,102,241,0.60)' : 'rgba(99,102,241,0.58)';
            newDomainBtn.style.transform = 'translateX(1px)';
        };
        newDomainBtn.onmouseleave = () => {
            newDomainBtn.style.background = isDk ? t.accentBgDk : t.accentBgLt;
            newDomainBtn.style.borderColor = isDk ? t.accentBorderDk : t.accentBorderLt;
            newDomainBtn.style.transform = '';
        };
        newDomainBtn.onclick = () => {
            if (typeof editor.showManageSections !== 'function') {
                closeOverlay();
                const btnTopo = document.getElementById('btn-topologies');
                if (btnTopo) btnTopo.click();
                editor.showToast('Open the Topologies menu -> Manage Topology Domains to create a new domain', 'info');
                return;
            }
            overlay.style.display = 'none';
            editor.showManageSections();
            const managePanel = document.getElementById('manage-sections-panel');
            if (!managePanel) {
                overlay.style.display = 'flex';
                return;
            }
            const observer = new MutationObserver(() => {
                if (!document.body.contains(managePanel) && !closed) {
                    observer.disconnect();
                    overlay.style.display = 'flex';
                    renderDomainList();
                }
            });
            observer.observe(document.body, { childList: true, subtree: false });
        };

        card.querySelector('.std-cancel').onclick = closeOverlay;

        // Enter inside the name input picks the first domain (fast
        // path for users who don't want to click). If there are no
        // domains it just nudges them toward "+ New domain".
        nameInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const sections = editor._customSections || [];
                if (sections.length > 0) saveTo(sections[0]);
                else newDomainBtn.click();
            }
        });

        overlay.appendChild(card);
        overlay.addEventListener('keydown', (e) => { e.stopPropagation(); });
        overlay.addEventListener('keyup', (e) => { e.stopPropagation(); });
        document.body.appendChild(overlay);
        overlay.onclick = (e) => { if (e.target === overlay) closeOverlay(); };
        const escHandler = (e) => {
            if (e.key !== 'Escape') return;
            if (overlay.style.display === 'none') return;
            closeOverlay();
        };
        document.addEventListener('keydown', escHandler);

        document.addEventListener('topology-domains:changed', onDomainsChanged);
        renderDomainList();

        // Focus the name input on open so the user can type
        // immediately. Done after appendChild so the element actually
        // has a layout box.
        setTimeout(() => { try { nameInput.focus(); } catch (_) {} }, 0);
    },

    performClearCanvas(editor, opts = {}) {
        if (editor._clearBDState) editor._clearBDState();
        editor.objects = [];
        editor.selectedObject = null;
        editor.selectedObjects = [];
        editor.deviceIdCounter = 0;
        editor.linkIdCounter = 0;
        editor.textIdCounter = 0;
        editor.deviceCounters = { router: 0, switch: 0 };
        editor.updatePropertiesPanel();
        editor.draw();
        editor.saveState();
        if (!opts.preserveActive) FileOps.clearTopologyIndicator();
        if (opts.markClean !== false) FileOps._markTopologyClean(editor, 'clear-canvas');
    },

    // ========================================================================
    // GENERATE / SAVE / LOAD / EXPORT
    // ========================================================================

    generateTopologyData(editor) {
        const meta = {
                deviceIdCounter: editor.deviceIdCounter,
                linkIdCounter: editor.linkIdCounter,
                textIdCounter: editor.textIdCounter,
                linkCurveMode: editor.linkCurveMode,
                globalCurveMode: editor.globalCurveMode,
                linkContinuousMode: editor.linkContinuousMode,
                linkStyle: editor.linkStyle,
                showLinkTypeLabels: editor.showLinkTypeLabels,
                deviceNumbering: editor.deviceNumbering,
                deviceCollision: editor.deviceCollision,
                movableDevices: editor.movableDevices,
                magneticFieldStrength: editor.magneticFieldStrength,
                gridZoomEnabled: editor.gridZoomEnabled
        };
        if (editor._multiBDMetadata?.bridge_domains?.length > 0) {
            meta.bridge_domains = editor._multiBDMetadata.bridge_domains;
            meta.isDnaas = true;
        }
        const cleanObjects = editor.objects.map(obj => {
            const copy = { ...obj };
            if (copy._hiddenByGroup) {
                delete copy._hiddenByGroup;
                if (copy._hidden === true) delete copy._hidden;
            }
            if ((copy.type === 'link' || copy.type === 'unbound') && copy._hidden) {
                delete copy._hidden;
            }
            delete copy._badgeWorlds;
            delete copy._hostnameMismatch;
            delete copy._mismatchDismissed;
            delete copy._identity;
            delete copy._configHostname;
            delete copy._stackData;
            delete copy._stackCachedAt;
            delete copy._lldpData;
            delete copy._lldpCompletedAt;
            delete copy._gitCommit;
            delete copy._gitCommitFetchedAt;
            delete copy._renaming;
            delete copy._activeConfigJob;
            delete copy._activeUpgradeJob;
            delete copy._upgradeFailedJob;
            delete copy._mismatchRefreshPending;
            delete copy._xrayCaptureActive;
            delete copy._createdAt;
            delete copy._renderColorOverride;
            return copy;
        });
        return { version: '1.0', objects: cleanObjects, metadata: meta };
    },

    quickSaveTopology(editor) {
        const data = FileOps.generateTopologyData(editor);
        localStorage.setItem('topology_current', JSON.stringify(data));

        if (editor.files) {
            try {
                const rd = localStorage.getItem(editor.files.recoveryKey);
                if (rd) {
                    const rData = JSON.parse(rd);
                    rData.sessionId = editor.files.sessionId;
                    rData.objects = editor.files?.sanitizeObjectsForPersistence
                        ? editor.files.sanitizeObjectsForPersistence(editor.objects)
                        : FileOps.generateTopologyData(editor).objects;
                    localStorage.setItem(editor.files.recoveryKey, JSON.stringify(rData));
                }
            } catch (_) {}
        }

        const deviceCount = editor.objects.filter(o => o.type === 'device').length;
        const linkCount = editor.objects.filter(o => o.type === 'link' || o.type === 'unbound').length;
        FileOps._markTopologyClean(editor, 'quick-save');
        editor.showToast(`Saved: ${deviceCount} devices, ${linkCount} links`, 'success');
    },

    _writeLocalCurrentSnapshot(editor, data) {
        try {
            const snapshot = data || FileOps.generateTopologyData(editor);
            localStorage.setItem('topology_current', JSON.stringify(snapshot));
        } catch (_) {}
    },

    _hasPersistentAutoSaveTarget(editor, opts = {}) {
        if (!editor || editor.initializing || !Array.isArray(editor.objects)) {
            return false;
        }
        if (editor.objects.length === 0 && !opts.allowEmpty) return false;
        const syncActive = (window.TopologySync && window.TopologySync.getActive)
            ? window.TopologySync.getActive() : null;
        if (syncActive && syncActive.domain_id && syncActive.topology_id) {
            return !syncActive.permission || syncActive.permission === 'write';
        }
        let info = null;
        try { info = JSON.parse(localStorage.getItem('topo_active') || '{}'); } catch (_) {}
        if (info && info.shared && (info.shared.isSharedIn || info.shared.isInbox)) {
            return false;
        }
        return !!(info && info.sectionId && info.name && !info.general);
    },

    _schedulePersistentAutoSave(editor, opts = {}) {
        if (!FileOps._hasPersistentAutoSaveTarget(editor, opts)) return;
        if (!opts.force && !FileOps._hasUnsavedTopologyChanges(editor)) return;
        if (FileOps._persistentAutoSaveConflict) return;
        const delay = Number.isFinite(opts.delayMs) ? Math.max(0, opts.delayMs) : 350;
        if (FileOps._persistentAutoSaveTimer) {
            clearTimeout(FileOps._persistentAutoSaveTimer);
        }
        FileOps._persistentAutoSaveTimer = setTimeout(() => {
            FileOps._persistentAutoSaveTimer = null;
            FileOps._persistentAutoSaveNow(editor, opts);
        }, delay);
    },

    async _persistentAutoSaveNow(editor, opts = {}) {
        if (!FileOps._hasPersistentAutoSaveTarget(editor, opts)) return null;
        if (!opts.force && !FileOps._hasUnsavedTopologyChanges(editor)) return null;
        if (FileOps._persistentAutoSaveInFlight) {
            FileOps._persistentAutoSaveQueued = true;
            return null;
        }
        FileOps._persistentAutoSaveInFlight = true;
        FileOps._persistentAutoSaveQueued = false;
        try {
            const data = FileOps.generateTopologyData(editor);
            const syncActive = (window.TopologySync && window.TopologySync.getActive)
                ? window.TopologySync.getActive() : null;
            if (syncActive && syncActive.domain_id && syncActive.topology_id) {
                const safeName = (syncActive.name || 'topology').replace(/\.json$/i, '');
                const result = await window.TopologySync.saveActive(safeName, data);
                if (result && result.conflict) {
                    FileOps._persistentAutoSaveConflict = true;
                    FileOps._showStaleSaveBanner(editor, {
                        currentUpdatedAt: result.current_updated_at || '',
                        lastWriter: {
                            username: result.last_actor || '',
                            display_name: result.last_actor_display_name || '',
                        },
                        onReload: () => {
                            FileOps._persistentAutoSaveConflict = false;
                            if (window.TopologySync && window.TopologySync.reloadActive) {
                                window.TopologySync.reloadActive();
                            }
                        },
                        onForce: async () => {
                            FileOps._persistentAutoSaveConflict = false;
                            await window.TopologySync.saveActive(safeName, data, { force: true });
                            FileOps._writeLocalCurrentSnapshot(editor, data);
                            FileOps._markTopologyClean(editor, 'persistent-autosave-force');
                        },
                    });
                    return result;
                }
                FileOps._persistentAutoSaveConflict = false;
                FileOps._writeLocalCurrentSnapshot(editor, data);
                FileOps._markTopologyClean(editor, 'persistent-autosave-sync');
                return result;
            }

            let info = null;
            try { info = JSON.parse(localStorage.getItem('topo_active') || '{}'); } catch (_) {}
            if (info && info.sectionId && info.name && !info.general) {
                const safeName = info.name.replace(/\.json$/i, '');
                const result = await FileOps._sectionSaveWithConflict(
                    editor,
                    info.sectionId,
                    { name: safeName, topology: data },
                    () => {
                        FileOps._writeLocalCurrentSnapshot(editor, data);
                        FileOps._markTopologyClean(editor, 'persistent-autosave-section');
                    },
                );
                if (result && result.conflict) FileOps._persistentAutoSaveConflict = true;
                else FileOps._persistentAutoSaveConflict = false;
                return result;
            }
        } catch (err) {
            console.warn('[AutoSave] Persistent save failed:', err && err.message || err);
            return { error: true };
        } finally {
            FileOps._persistentAutoSaveInFlight = false;
            if (FileOps._persistentAutoSaveQueued && !FileOps._persistentAutoSaveConflict) {
                FileOps._persistentAutoSaveQueued = false;
                FileOps._schedulePersistentAutoSave(editor, { delayMs: 250, source: 'queued' });
            }
        }
        return null;
    },

    _cmdSave(editor) {
        if (editor.objects.length === 0) { editor.showToast('Nothing to save — canvas is empty', 'warning'); return; }
        let info;
        try { info = JSON.parse(localStorage.getItem('topo_active')); } catch (_) {}

        // Route through TopologySync for any topology registered with
        // the live-sync hub (shared-in + migrated own topologies). This
        // ensures a collaborator's concurrent edit triggers a clear
        // Reload / Save-anyway prompt instead of a silent overwrite.
        const syncActive = (window.TopologySync && window.TopologySync.getActive)
            ? window.TopologySync.getActive() : null;
        if (syncActive && syncActive.domain_id && syncActive.topology_id) {
            const topoData = FileOps.generateTopologyData(editor);
            const safeName = (syncActive.name || info?.name || 'topology').replace(/\.json$/i, '');
            window.TopologySync.saveActive(safeName, topoData).then(function (result) {
                if (result && result.conflict) {
                    FileOps._showStaleSaveBanner(editor, {
                        currentUpdatedAt: result.current_updated_at || '',
                        onReload: function () {
                            if (window.TopologySync && window.TopologySync.reloadActive) {
                                window.TopologySync.reloadActive();
                            }
                        },
                        onForce: async function () {
                            try {
                                await window.TopologySync.saveActive(safeName, topoData, { force: true });
                                editor.showToast('Overwrote server copy', 'success');
                            } catch (err) {
                                editor.showToast('Save failed: ' + (err && err.message || err), 'error');
                            }
                        },
                    });
                    var who = result.last_actor_display_name || result.last_actor || 'someone';
                    editor.showToast(who + ' changed this topology — resolve the conflict', 'warning');
                    return;
                }
                editor.showToast('Saved "' + safeName + '" → ' + (syncActive.domain_name || info?.domain || 'domain'), 'success');
                FileOps.quickSaveTopology(editor);
            }).catch(function (err) {
                editor.showToast('Save failed: ' + (err && err.message || err), 'error');
            });
            return;
        }

        if (info && info.sectionId && info.name) {
            const topoData = FileOps.generateTopologyData(editor);
            const safeName = info.name.replace(/\.json$/i, '');
            FileOps._sectionSaveWithConflict(
                editor, info.sectionId,
                { name: safeName, topology: topoData },
                () => {
                    editor.showToast(`Saved "${safeName}" → ${info.domain || 'domain'}`, 'success');
                    FileOps.quickSaveTopology(editor);
                },
            );
        } else {
            FileOps.quickSaveToDomain(editor);
        }
    },

    // Central wrapper for /api/sections/<sid>/save. Handles the 409
    // stale-save conflict response from the backend by rendering a sticky
    // banner with "Reload" and "Save anyway" buttons. Every other error
    // type flows through the existing generic toast path so callers don't
    // need to change.
    async _sectionSaveWithConflict(editor, sectionId, body, onSuccess) {
        try {
            const authFetch = (window.TopologyAuth && window.TopologyAuth.authFetch)
                ? window.TopologyAuth.authFetch : (u, o) => fetch(u, o);
            const sendBody = Object.assign({}, body || {});
            const quotaCleanupRetry = !!sendBody.__quota_cleanup_retry;
            delete sendBody.__quota_cleanup_retry;
            const resp = await authFetch('/api/sections/' + encodeURIComponent(sectionId) + '/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(sendBody),
            });
            const result = await resp.json().catch(() => ({}));
            if (resp.status === 409 && result && result.conflict) {
                // Quieter than the browser's default 409 red line: we
                // already handle this with a banner + buttons, so log a
                // friendly info line so devs reading the console see
                // context next to the unavoidable HTTP status log.
                try {
                    const ageIso = result.current_updated_at || '';
                    const lastWriter = result.last_writer || {};
                    const who = lastWriter.display_name || result.last_actor_display_name || lastWriter.username || result.last_actor || '';
                    console.info(
                        '[topology] stale-save 409 for section ' + sectionId
                        + (ageIso ? ' (remote updated_at=' + ageIso + ')' : '')
                        + (who ? ' last_writer=' + who : '')
                        + ' -- showing reload/overwrite banner. Not an error.',
                        result.conflict_debug || {}
                    );
                } catch (_) { /* no console */ }
                FileOps._showStaleSaveBanner(editor, {
                    currentUpdatedAt: result.current_updated_at || '',
                    lastWriter: result.last_writer || {
                        username: result.last_actor || '',
                        display_name: result.last_actor_display_name || '',
                    },
                    conflictReason: result.conflict_reason || '',
                    conflictDebug: result.conflict_debug || null,
                    onReload: () => {
                        if (editor && typeof editor.loadCustomSections === 'function') {
                            editor.loadCustomSections();
                        }
                        editor.showToast('Reload the topology from the Topologies dropdown to see the latest changes', 'info');
                    },
                    onForce: async () => {
                        await FileOps._sectionSaveWithConflict(
                            editor, sectionId,
                            Object.assign({}, body, { force: true }),
                            onSuccess,
                        );
                    },
                });
                return { conflict: true };
            }
            if (FileOps._isDomainLimitResult(result) && !quotaCleanupRetry) {
                const section = (editor._customSections || []).find(s => s.id === sectionId)
                    || { id: sectionId, name: 'this domain', color: '#3b82f6' };
                const cleanup = await FileOps._openDomainCleanupPrompt(editor, section, null, {
                    reason: 'limit',
                    limitResult: result,
                });
                if (cleanup && cleanup.deleted_count > 0) {
                    return await FileOps._sectionSaveWithConflict(
                        editor,
                        sectionId,
                        Object.assign({}, body, { __quota_cleanup_retry: true }),
                        onSuccess,
                    );
                }
                return { error: true, quota: true };
            }
            if (!resp.ok || (result && result.error)) {
                editor.showToast('Save failed: ' + ((result && result.error) || ('HTTP ' + resp.status)), 'error');
                return { error: true };
            }
            // Refresh the live-sync base_updated_at for any legacy file
            // that has been mirrored into the multi-user DB. Without
            // this, the very next save would race against its own echo
            // and the user sees a spurious conflict banner.
            if (window.TopologySync && window.TopologySync.markSaved
                    && result && result.mirror_updated_at) {
                try { window.TopologySync.markSaved(result.mirror_updated_at); } catch (_) {}
            }
            if (typeof onSuccess === 'function') onSuccess(result);
            FileOps._markTopologyClean(editor, 'section-save');
            return result;
        } catch (err) {
            editor.showToast('Save failed: ' + (err && err.message || err), 'error');
            return { error: true };
        }
    },

    // Stale-save banner. All layout/visual rules live in `styles.css`
    // under `.topology-stale-save-banner`; we only build the semantic
    // markup and wire the button handlers here. The banner is:
    //  - responsive (stacks actions on narrow viewports via @media)
    //  - themed (dark/light via body.dark-mode)
    //  - dismissable via Esc, click-outside, Reload, Save-anyway, or x
    //  - animated in (fade + slide) and respects prefers-reduced-motion
    _showStaleSaveBanner(editor, opts) {
        opts = opts || {};
        // Remove any previous banner so we don't stack them. The previous
        // keyboard listener is attached with { once: true } to clean up
        // after itself even if we never hit Escape, so no listener leak.
        const old = document.getElementById('topology-stale-save-banner');
        if (old) old.remove();

        const banner = document.createElement('div');
        banner.id = 'topology-stale-save-banner';
        banner.className = 'topology-stale-save-banner';
        banner.setAttribute('role', 'alertdialog');
        banner.setAttribute('aria-live', 'assertive');
        banner.setAttribute('aria-labelledby', 'topology-stale-save-title');

        const ageHtml = opts.currentUpdatedAt
            ? '<span class="ssb-age">(updated ' + FileOps._escapeHtml(FileOps._prettyAgo(opts.currentUpdatedAt)) + ')</span>'
            : '';
        const lastWriter = opts.lastWriter || {};
        const writerName = lastWriter.display_name || lastWriter.displayName
            || lastWriter.username || '';
        const writerUser = lastWriter.username || '';
        const writerLabel = writerName
            ? FileOps._escapeHtml(writerName + (writerUser && writerUser !== writerName ? ' (' + writerUser + ')' : ''))
            : '';
        const writerHtml = writerLabel
            ? '<div class="ssb-detail">Last saved by <strong>' + writerLabel + '</strong>.</div>'
            : '';
        const dbg = opts.conflictDebug || {};
        const shares = dbg.shares || {};
        const debugParts = [];
        if (dbg.reason) debugParts.push('reason=' + dbg.reason);
        if (typeof dbg.delta_seconds === 'number') debugParts.push('delta=' + dbg.delta_seconds + 's');
        if (typeof shares.write_share_recipient_count === 'number') {
            debugParts.push('write-shares=' + shares.write_share_recipient_count);
        }
        const debugHtml = debugParts.length
            ? '<div class="ssb-debug">debug: ' + FileOps._escapeHtml(debugParts.join(', ')) + '</div>'
            : '';

        banner.innerHTML =
            '<svg class="ssb-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            +   '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
            +   '<line x1="12" y1="9" x2="12" y2="13"/>'
            +   '<line x1="12" y1="17" x2="12.01" y2="17"/>'
            + '</svg>'
            + '<div class="ssb-body">'
            +   '<div class="ssb-title" id="topology-stale-save-title">Someone else edited this topology' + ageHtml + '</div>'
            +   '<div class="ssb-msg">Reload to see their changes, or overwrite if you are sure.</div>'
            +   writerHtml
            +   debugHtml
            + '</div>'
            + '<div class="ssb-actions">'
            +   '<button type="button" class="ssb-btn ssb-btn-secondary ssb-reload" title="Discard local edits and reload the latest version">Reload</button>'
            +   '<button type="button" class="ssb-btn ssb-btn-primary ssb-force" title="Overwrite the server copy with your local edits">Save anyway</button>'
            + '</div>'
            + '<button type="button" class="ssb-close" aria-label="Dismiss stale-save warning" title="Dismiss (Esc)">&times;</button>';

        const reloadBtn = banner.querySelector('.ssb-reload');
        const forceBtn = banner.querySelector('.ssb-force');
        const closeBtn = banner.querySelector('.ssb-close');

        // Remove the banner with a short fade so the dismiss feels
        // intentional rather than a DOM pop-off. Guarded against
        // double-invocation (every action path calls this first).
        let removed = false;
        const teardown = () => {
            if (removed) return;
            removed = true;
            banner.classList.add('dismissing');
            setTimeout(() => {
                if (banner.parentNode) banner.parentNode.removeChild(banner);
                try { document.removeEventListener('keydown', onEsc, true); } catch (_) {}
            }, 160);
        };

        reloadBtn.addEventListener('click', () => {
            teardown();
            if (typeof opts.onReload === 'function') opts.onReload();
        });
        forceBtn.addEventListener('click', () => {
            teardown();
            if (typeof opts.onForce === 'function') opts.onForce();
        });
        closeBtn.addEventListener('click', teardown);

        // Esc dismisses the banner without firing Reload or Force. Use
        // capture:true so we run before any modal's keydown consumer.
        const onEsc = (e) => {
            if (e.key === 'Escape') {
                e.stopPropagation();
                teardown();
            }
        };
        document.addEventListener('keydown', onEsc, true);

        document.body.appendChild(banner);
        // Focus the (safer) Reload button so keyboard users can act
        // immediately. Deferred to next frame so the insertion + CSS
        // transition start together.
        requestAnimationFrame(() => {
            try { reloadBtn.focus({ preventScroll: true }); } catch (_) {}
        });
    },

    _escapeHtml(value) {
        return String(value == null ? '' : value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    },

    _prettyAgo(iso) {
        try {
            const then = new Date(iso).getTime();
            const secs = Math.max(0, Math.round((Date.now() - then) / 1000));
            if (secs < 60) return secs + 's ago';
            if (secs < 3600) return Math.round(secs / 60) + 'm ago';
            if (secs < 86400) return Math.round(secs / 3600) + 'h ago';
            return Math.round(secs / 86400) + 'd ago';
        } catch (_) { return 'moments ago'; }
    },

    quickSaveToDomain(editor) {
        if (editor.objects.length === 0) { editor.showToast('Nothing to save — canvas is empty', 'warning'); return; }
        const sections = editor._customSections || [];
        if (sections.length === 0) { editor.showToast('No domains exist. Create one in Topology Domains first.', 'warning'); return; }

        const stale = document.getElementById('quick-save-domain-picker');
        if (stale) stale.remove();

        const isDk = FileOps._menuDark(editor);
        const t = {
            bg: isDk ? 'rgba(17, 25, 40, 0.92)' : 'rgba(255, 255, 255, 0.92)',
            border: isDk ? 'rgba(255, 255, 255, 0.125)' : 'rgba(0, 0, 0, 0.08)',
            text: isDk ? '#e2e8f0' : '#1e1e32',
            muted: isDk ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.45)',
            input: isDk ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)',
            inputBorder: isDk ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.12)',
            hover: isDk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)',
        };

        const overlay = document.createElement('div');
        overlay.id = 'quick-save-domain-picker';
        overlay.style.cssText = `position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);backdrop-filter:blur(6px);z-index:10001;display:flex;align-items:center;justify-content:center;`;

        let selectedId = null;
        const icons = FileOps._sectionIcons();

        const renderStep1 = () => {
            const card = overlay.querySelector('.qs-card') || document.createElement('div');
            card.className = 'qs-card';
            card.style.cssText = `background:${t.bg};border:1px solid ${t.border};border-radius:14px;padding:20px;min-width:340px;max-width:400px;box-shadow:0 12px 48px rgba(0,0,0,0.3);backdrop-filter:blur(16px);font-family:'Poppins',-apple-system,sans-serif;`;
            card.innerHTML = `
                <div style="font-size:15px;font-weight:600;color:${t.text};margin-bottom:4px;">Save to Domain</div>
                <div style="font-size:11px;color:${t.muted};margin-bottom:14px;">Select a domain to save the current topology</div>
                <div class="qs-domains" style="display:flex;flex-direction:column;gap:6px;margin-bottom:14px;"></div>
                <div style="text-align:right;">
                    <button class="qs-cancel" style="padding:7px 14px;background:transparent;border:1px solid ${t.border};border-radius:8px;color:${t.text};cursor:pointer;font-size:12px;">Cancel</button>
                </div>
            `;
            const domainsList = card.querySelector('.qs-domains');
            sections.forEach(sec => {
                const iconSvg = (icons.find(i => i.id === sec.icon) || icons[0]).svg;
                const btn = document.createElement('button');
                btn.style.cssText = `display:flex;align-items:center;gap:10px;padding:10px 12px;background:${sec.color}0d;border:1px solid ${sec.color}30;border-left:3px solid ${sec.color};border-radius:8px;cursor:pointer;transition:all 0.15s;width:100%;text-align:left;`;
                btn.innerHTML = `
                    <div style="width:28px;height:28px;border-radius:6px;background:${sec.color}18;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                        <svg viewBox="0 0 24 24" width="14" height="14" style="stroke:${sec.color};color:${sec.color};">${iconSvg}</svg>
                    </div>
                    <span style="font-size:13px;font-weight:500;color:${t.text};">${sec.name}</span>
                `;
                btn.onmouseenter = () => { btn.style.background = `${sec.color}1a`; btn.style.borderColor = `${sec.color}60`; };
                btn.onmouseleave = () => { btn.style.background = `${sec.color}0d`; btn.style.borderColor = `${sec.color}30`; };
                btn.onclick = () => { selectedId = sec.id; renderStep2(sec, card); };
                domainsList.appendChild(btn);
            });
            card.querySelector('.qs-cancel').onclick = () => overlay.remove();
            if (!overlay.contains(card)) overlay.appendChild(card);
        };

        const renderStep2 = (sec, card) => {
            const defaultName = 'topology_' + new Date().toISOString().slice(0, 10);
            card.innerHTML = `
                <div style="font-size:15px;font-weight:600;color:${t.text};margin-bottom:4px;">Save to ${sec.name}</div>
                <div style="font-size:11px;color:${t.muted};margin-bottom:14px;">Enter a name for the topology</div>
                <input class="qs-name" type="text" value="${defaultName}" placeholder="Topology name" style="
                    width:100%;padding:9px 12px;background:${t.input};border:1px solid ${sec.color}55;border-radius:8px;
                    color:${t.text};font-size:13px;font-family:inherit;box-sizing:border-box;margin-bottom:14px;outline:none;"
                    onclick="event.stopPropagation();">
                <div style="display:flex;gap:8px;justify-content:flex-end;">
                    <button class="qs-back" style="padding:7px 14px;background:transparent;border:1px solid ${t.border};border-radius:8px;color:${t.text};cursor:pointer;font-size:12px;">Back</button>
                    <button class="qs-save" style="padding:7px 16px;background:${sec.color};border:none;border-radius:8px;color:#fff;cursor:pointer;font-size:12px;font-weight:600;">Save</button>
                </div>
            `;
            const input = card.querySelector('.qs-name');
            const saveBtn = card.querySelector('.qs-save');
            input.focus();
            input.select();
            card.querySelector('.qs-back').onclick = () => renderStep1();
            const doSave = async () => {
                const name = input.value.trim();
                if (!name) { editor.showToast('Enter a topology name', 'warning'); return; }
                saveBtn.textContent = 'Saving...';
                saveBtn.disabled = true;
                try {
                    const result = await FileOps._sectionSaveWithConflict(
                        editor,
                        sec.id,
                        { name, topology: FileOps.generateTopologyData(editor) },
                        null,
                    );
                    if (result && (result.error || result.conflict || result.quota)) {
                        saveBtn.textContent = 'Save';
                        saveBtn.disabled = false;
                        return;
                    }
                    overlay.remove();
                    FileOps.updateTopologyIndicator(name, sec.name, sec.color, sec.id);
                    editor.showToast(`Saved to ${sec.name}`, 'success');
                    FileOps._markTopologyClean(editor, 'quick-save-domain');
                    if (editor.loadCustomSections) editor.loadCustomSections();
                } catch (err) {
                    saveBtn.textContent = 'Save';
                    saveBtn.disabled = false;
                    editor.showToast('Save failed: ' + err.message, 'error');
                }
            };
            saveBtn.onclick = doSave;
            input.addEventListener('keydown', (ev) => { ev.stopPropagation(); if (ev.key === 'Enter') doSave(); if (ev.key === 'Escape') overlay.remove(); });
        };

        overlay.addEventListener('keydown', (e) => { e.stopPropagation(); });
        overlay.addEventListener('keyup', (e) => { e.stopPropagation(); });
        document.body.appendChild(overlay);
        overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
        renderStep1();
    },

    saveTopologyAs(editor) {
        const data = FileOps.generateTopologyData(editor);
        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `topology_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        editor.showToast('Topology downloaded', 'success');
    },

    saveTopology(editor) {
        FileOps.saveTopologyAs(editor);
    },

    exportTopologyJSON(editor) {
        FileOps.saveTopologyAs(editor);
    },

    exportTopologyAsPNG(editor) {
        const objs = editor.objects.filter(o => !o._hidden);
        if (objs.length === 0) {
            editor.showToast('Nothing to export — canvas is empty', 'warning');
            return;
        }

        FileOps._showPNGExportDialog(editor, objs);
    },

    _showPNGExportDialog(editor, objs) {
        const existing = document.getElementById('png-export-dialog');
        if (existing) existing.remove();

        const dk = editor.darkMode;
        const overlay = document.createElement('div');
        overlay.id = 'png-export-dialog';
        overlay.style.cssText = 'position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.5);backdrop-filter:blur(4px);';

        const panel = document.createElement('div');
        panel.style.cssText = `background:${dk ? 'rgba(20,24,40,0.92)' : 'rgba(255,255,255,0.95)'};border:1px solid ${dk ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.1)'};border-radius:14px;padding:24px 28px;min-width:320px;max-width:400px;box-shadow:0 16px 48px rgba(0,0,0,0.35);backdrop-filter:blur(20px);font-family:inherit;`;

        const txtPrimary = dk ? '#e2e8f0' : '#1e1e32';
        const txtMuted = dk ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.45)';
        const accentColor = '#3b82f6';

        let selectedScale = 3;
        let includeBg = true;

        const bounds = FileOps._computeExportBounds(objs);
        const baseW = Math.round(bounds.w);
        const baseH = Math.round(bounds.h);

        const updatePreview = () => {
            const pw = baseW * selectedScale;
            const ph = baseH * selectedScale;
            const sizeMB = ((pw * ph * 4) / (1024 * 1024)).toFixed(1);
            dimSpan.textContent = `${pw} × ${ph}px`;
            sizeSpan.textContent = `~${sizeMB} MB uncompressed`;
            scaleButtons.forEach(btn => {
                const s = parseInt(btn.dataset.scale);
                if (s === selectedScale) {
                    btn.style.background = accentColor;
                    btn.style.color = '#fff';
                    btn.style.borderColor = accentColor;
                } else {
                    btn.style.background = dk ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)';
                    btn.style.color = txtPrimary;
                    btn.style.borderColor = dk ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
                }
            });
        };

        panel.innerHTML = `
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;">
                <div style="font-size:15px;font-weight:700;color:${txtPrimary};">Export PNG</div>
                <button id="png-close-btn" style="background:none;border:none;cursor:pointer;color:${txtMuted};font-size:18px;padding:2px 6px;border-radius:6px;" title="Cancel">✕</button>
            </div>
            <div style="margin-bottom:16px;">
                <div style="font-size:11px;font-weight:600;color:${txtMuted};text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;">Scale</div>
                <div id="png-scale-btns" style="display:flex;gap:6px;"></div>
            </div>
            <div style="margin-bottom:16px;">
                <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:12px;color:${txtPrimary};">
                    <input type="checkbox" id="png-bg-check" checked style="accent-color:${accentColor};width:15px;height:15px;cursor:pointer;">
                    Include background
                </label>
            </div>
            <div style="margin-bottom:20px;padding:10px 12px;border-radius:8px;background:${dk ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)'};border:1px solid ${dk ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'};">
                <div style="display:flex;justify-content:space-between;font-size:11px;color:${txtMuted};margin-bottom:4px;">
                    <span>Dimensions</span>
                    <span id="png-dim-span"></span>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:11px;color:${txtMuted};">
                    <span>Estimated size</span>
                    <span id="png-size-span"></span>
                </div>
            </div>
            <div style="display:flex;gap:8px;">
                <button id="png-cancel-btn" style="flex:1;padding:9px;border-radius:8px;border:1px solid ${dk ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'};background:${dk ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)'};color:${txtPrimary};font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;">Cancel</button>
                <button id="png-export-btn" style="flex:2;padding:9px;border-radius:8px;border:none;background:${accentColor};color:#fff;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;">Export</button>
            </div>
        `;

        overlay.appendChild(panel);
        overlay.addEventListener('keydown', (e) => { e.stopPropagation(); });
        overlay.addEventListener('keyup', (e) => { e.stopPropagation(); });
        document.body.appendChild(overlay);

        const dimSpan = panel.querySelector('#png-dim-span');
        const sizeSpan = panel.querySelector('#png-size-span');
        const scaleBtnContainer = panel.querySelector('#png-scale-btns');

        const scales = [
            { value: 1, label: '1×' },
            { value: 2, label: '2×' },
            { value: 3, label: '3×' },
            { value: 4, label: '4×' },
        ];

        const scaleButtons = [];
        scales.forEach(s => {
            const btn = document.createElement('button');
            btn.dataset.scale = s.value;
            btn.textContent = s.label;
            btn.style.cssText = `flex:1;padding:7px 0;border-radius:7px;border:1px solid;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;transition:all 0.15s;`;
            btn.addEventListener('click', () => { selectedScale = s.value; updatePreview(); });
            scaleBtnContainer.appendChild(btn);
            scaleButtons.push(btn);
        });

        const bgCheck = panel.querySelector('#png-bg-check');
        bgCheck.addEventListener('change', () => { includeBg = bgCheck.checked; });

        updatePreview();

        const close = () => overlay.remove();
        overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
        panel.querySelector('#png-close-btn').addEventListener('click', close);
        panel.querySelector('#png-cancel-btn').addEventListener('click', close);
        panel.querySelector('#png-export-btn').addEventListener('click', () => {
            close();
            FileOps._renderPNGExport(editor, objs, selectedScale, includeBg);
        });

        document.addEventListener('keydown', function esc(e) {
            if (e.key === 'Escape') { close(); document.removeEventListener('keydown', esc); }
        });
    },

    _computeExportBounds(objs) {
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        const expand = (cx, cy, margin) => {
            if (cx - margin < minX) minX = cx - margin;
            if (cy - margin < minY) minY = cy - margin;
            if (cx + margin > maxX) maxX = cx + margin;
            if (cy + margin > maxY) maxY = cy + margin;
        };
        const expandRect = (cx, cy, hw, hh) => {
            if (cx - hw < minX) minX = cx - hw;
            if (cy - hh < minY) minY = cy - hh;
            if (cx + hw > maxX) maxX = cx + hw;
            if (cy + hh > maxY) maxY = cy + hh;
        };

        objs.forEach(obj => {
            if (obj.type === 'device') {
                const r = obj.radius || 20;
                const bounds = window.DeviceStyles && window.DeviceStyles.getDeviceBounds
                    ? window.DeviceStyles.getDeviceBounds(obj) : null;
                if (bounds && bounds.width) {
                    expandRect(obj.x, obj.y, bounds.width / 2 + 15, Math.max(Math.abs(bounds.top || r), Math.abs(bounds.bottom || r)) + 15);
                } else {
                    expand(obj.x, obj.y, r + 15);
                }
                expand(obj.x, obj.y + r + 22, 50);
            } else if (obj.type === 'link' || obj.type === 'unbound') {
                expand(obj.x, obj.y, 8);
                expand(obj.x2, obj.y2, 8);
                if (obj.manualCurvePoint) expand(obj.manualCurvePoint.x, obj.manualCurvePoint.y, 8);
                if (obj.manualControlPoint) expand(obj.manualControlPoint.x, obj.manualControlPoint.y, 8);
            } else if (obj.type === 'text') {
                const fontSize = obj.fontSize || 14;
                const lines = (obj.text || '').split('\n');
                const maxLine = Math.max(...lines.map(l => l.length));
                const approxW = maxLine * fontSize * 0.6;
                const approxH = lines.length * fontSize * 1.3;
                expandRect(obj.x, obj.y, approxW / 2 + 12, approxH / 2 + 12);
            } else if (obj.type === 'shape') {
                const hw = (obj.width || 100) / 2;
                const hh = (obj.height || 60) / 2;
                expandRect(obj.x, obj.y, hw + 6, hh + 6);
            }
        });

        const pad = 50;
        minX -= pad; minY -= pad; maxX += pad; maxY += pad;
        return { minX, minY, maxX, maxY, w: maxX - minX, h: maxY - minY };
    },

    _renderPNGExport(editor, objs, scale, includeBg) {
        const { minX, minY, w, h } = FileOps._computeExportBounds(objs);
        if (w <= 0 || h <= 0) {
            editor.showToast('Could not determine object bounds', 'error');
            return;
        }

        const offscreen = document.createElement('canvas');
        offscreen.width = Math.round(w * scale);
        offscreen.height = Math.round(h * scale);
        const ctx = offscreen.getContext('2d');
        ctx.scale(scale, scale);

        if (includeBg) {
            ctx.fillStyle = editor.darkMode ? '#1a1a2e' : '#ffffff';
            ctx.fillRect(0, 0, w, h);
        }

        ctx.save();
        ctx.translate(-minX, -minY);

        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';
        if (editor.configureCanvasQuality) {
            editor.configureCanvasQuality(ctx, { smoothing: true });
        } else {
            ctx.imageSmoothingEnabled = true;
            ctx.imageSmoothingQuality = 'high';
        }

        const origCtx = editor.ctx;
        const origCanvas = editor.canvas;
        const origSelected = editor.selectedObject;
        const origSelectedArr = editor.selectedObjects;
        const origZoom = editor.zoom;
        const origPan = { ...editor.panOffset };

        editor.ctx = ctx;
        editor.canvas = offscreen;
        editor.selectedObject = null;
        editor.selectedObjects = [];
        editor.zoom = 1;
        editor.panOffset = { x: 0, y: 0 };

        const sorted = [...objs].sort((a, b) => {
            const layerA = a.layer ?? 0, layerB = b.layer ?? 0;
            if (layerA !== layerB) return layerA - layerB;
            const typeOrder = { 'shape': -1, 'link': 0, 'unbound': 0, 'device': 1, 'text': 2 };
            return (typeOrder[a.type] || 0) - (typeOrder[b.type] || 0);
        });

        sorted.forEach(obj => {
            if (obj.type === 'link' || obj.type === 'unbound') {
                editor.drawLink(obj);
            } else if (obj.type === 'device') {
                editor.drawDevice(obj, false, true);
            } else if (obj.type === 'text') {
                if (obj.linkId && !editor.showLinkAttachments) return;
                if (obj.linkId && obj._interfaceLabel === true && !editor.showLinkTypeLabels) return;
                editor.drawText(obj);
            } else if (obj.type === 'shape') {
                editor.drawShape(obj);
            }
        });
        sorted.forEach(obj => {
            if (obj.type === 'device') editor.drawDeviceLabel(obj);
        });

        ctx.restore();

        editor.ctx = origCtx;
        editor.canvas = origCanvas;
        editor.selectedObject = origSelected;
        editor.selectedObjects = origSelectedArr;
        editor.zoom = origZoom;
        editor.panOffset = origPan;

        const pw = offscreen.width;
        const ph = offscreen.height;
        const stored = JSON.parse(localStorage.getItem('topo_active') || '{}');
        const topoName = (stored.name || 'topology_export').replace(/[^a-zA-Z0-9_\-]/g, '_');
        const link = document.createElement('a');
        link.download = `${topoName}.png`;
        link.href = offscreen.toDataURL('image/png');
        link.click();
        editor.showToast(`PNG exported at ${scale}× (${pw}×${ph}px)`, 'success');
    },

    loadTopology(editor, event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                let data = JSON.parse(e.target.result);
                if (!data.objects && data.topology && data.topology.objects) data = data.topology;
                if (!data.objects && Array.isArray(data)) data = { objects: data };
                if (!data.objects || !Array.isArray(data.objects)) {
                    editor.showToast('Invalid topology file: no objects array found', 'error');
                    return;
                }
                const topoName = file.name.replace(/\.json$/i, '');
                FileOps._loadIntoEditor(editor, data, {
                    name: topoName,
                    filename: file.name,
                });
                editor.showToast(`Loaded ${file.name} (${data.objects.length} objects)`, 'success');
            } catch (error) {
                console.error('[loadTopology] Parse error:', error);
                editor.showToast(`Error loading topology: ${error.message}`, 'error');
            }
        };
        reader.onerror = () => {
            editor.showToast(`Error reading file: ${reader.error?.message || 'unknown error'}`, 'error');
        };
        reader.readAsText(file);
        event.target.value = '';
    },

    // ========================================================================
    // DNAAS TOPOLOGIES
    // ========================================================================

    saveAsDnaasTopology(editor, ...args) {
        if (window.DnaasHelpers && window.DnaasHelpers.saveAsDnaasTopology) {
            return window.DnaasHelpers.saveAsDnaasTopology(editor, ...args);
        }
    },

    async loadDnaasTopology(editor) {
        try {
            const sectionId = await window.DnaasHelpers._ensureDnaasSection();
            await editor.loadFromSection({ id: sectionId, name: 'DNAAS', color: '#FF5E1F' });
        } catch (err) {
            editor.showToast('Failed to load DNAAS topologies: ' + err.message, 'error');
        }
    },

    // ========================================================================
    // BUG TOPOLOGIES — now managed via the unified sections API
    // ========================================================================

    _bugsSectionId: null,

    // Resolve the per-user __bugs section id. The backend injects
    // __bugs as a BUILTIN in every user's /api/sections response
    // (see BUILTIN_SECTIONS in serve.py), so the id is always "__bugs"
    // and this function is essentially a thin cache used by a handful
    // of legacy saveBugTopology / loadDebugDnosTopology call sites.
    //
    // IMPORTANT (2026-04-21 multi-user leak fix): earlier revisions of
    // this function POSTed to /api/migrate-bug-topologies as a side
    // effect, which copied every file in the shared
    // ~/SCALER/FLOWSPEC_VPN/bug_evidence/*.topology.json folder into
    // the calling user's __bugs section on every page load. That made
    // every user see yarel's historical bug evidence as their own
    // BUGS content, which directly violated the "multi-user is the
    // default" rule in DEVELOPMENT_GUIDELINES.md. Do NOT reintroduce
    // any automatic migration here -- bugs must enter a user's __bugs
    // section ONLY through that user's own /api/bugs/from-jira calls
    // (topology-bugs.js Create Bug flow) or an explicit user action.
    async _ensureBugsSection() {
        if (FileOps._bugsSectionId) return FileOps._bugsSectionId;
        try {
            const resp = await fetch('/api/sections');
            const data = await resp.json();
            const sections = data.sections || [];
            const existing = sections.find(s => s.id === '__bugs' || s.name === 'Bugs');
            if (existing) {
                FileOps._bugsSectionId = existing.id;
                return existing.id;
            }
            FileOps._bugsSectionId = '__bugs';
            return '__bugs';
        } catch (err) {
            console.error('[Bugs] Failed to resolve bugs section:', err);
            throw err;
        }
    },

    async saveBugTopology(editor) {
        const id = await FileOps._ensureBugsSection();
        editor.saveToSection({ id, name: 'Bugs', color: '#e74c3c' });
    },
    async loadDebugDnosTopology(editor) {
        const id = await FileOps._ensureBugsSection();
        editor.loadFromSection({ id, name: 'Bugs', color: '#e74c3c' });
    },
    showDebugDnosTopologySelector(editor) {},

    // ========================================================================
    // SHARED: Render topology entries with right-click rename
    // ========================================================================

    _formatTimeAgo(mtime) {
        if (!mtime) return '';
        const now = Date.now() / 1000;
        const diff = now - mtime;
        if (diff < 60) return 'just now';
        if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
        if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
        if (diff < 604800) return Math.floor(diff / 86400) + 'd ago';
        const d = new Date(mtime * 1000);
        return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    },

    _renderTopoEntries(editor, container, topos, color, opts) {
        const dk = FileOps._menuDark(editor);
        const txtColor = dk ? '#e2e8f0' : '#1e1e32';
        const iconOpColor = dk ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.5)';
        const shareActionColor = dk ? '#ffffff' : '#000000';
        const mutedColor = dk ? 'rgba(255,255,255,0.35)' : 'rgba(0,0,0,0.45)';
        // Sharing context lets us decorate each row with "shared-out" /
        // "shared-in" badges. opts.ownDomain pins the caller-side owner
        // domain when rendering legacy sections; opts.isSharedIn marks
        // virtual rows fed by /api/domains/... (domain I received from
        // someone else, or the synthetic "Shared with me" inbox).
        const sharingIndex = opts.sharingIndex || FileOps._buildSharingIndex();
        const ownDomain = opts.ownDomain || null;
        // Stable purple used for EVERY shared-in surface (icon, pill,
        // inline "by" text, border tint). Must match the value in
        // _renderSharedInSectionsInDropdown so the dropdown reads as one
        // coherent "this is not mine" zone regardless of which row
        // renderer produced the markup.
        const SHARED_IN_ACCENT = '#a78bfa';
        let html = '';
        topos.forEach(t => {
            const name = (t.name || t.filename || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            const filename = (t.filename || '').replace(/"/g, '&quot;');
            const timeAgo = FileOps._formatTimeAgo(t.modified);
            const borderOp = dk ? '40' : '70';
            // Per-file shared indicator:
            // 1. Outgoing -- I own this file and it appears in
            //    /api/domains/share/files/outgoing. Match on
            //    `<ownDomain.id>|<sanitized basename>`.
            // 2. Incoming -- the topology row has `is_shared_with_me`
            //    or explicit owner metadata (synthetic inbox, or a
            //    shared-in domain whose topologies are fetched through
            //    /api/domains).
            let fileBadgeSvg = '';
            let badgeTooltip = '';
            let outgoingRecipients = null;
            let rowHit = null;
            if (ownDomain && ownDomain.id) {
                const basename = String(t.filename || t.name || '').replace(/\.json$/i, '');
                const sanitized = FileOps._sanitizeTopologyBasename(basename);
                rowHit = sharingIndex.outgoingFilesByKey[ownDomain.id + '|' + sanitized];
                if (rowHit && Array.isArray(rowHit.recipients) && rowHit.recipients.length > 0) {
                    outgoingRecipients = rowHit.recipients;
                }
            }
            const incomingOwner = t.owner || (t.is_shared_with_me ? (t.owner_display_name || t.owner) : null);
            const isSharedIn = !!(t.is_shared_with_me || opts.isSharedIn);
            const isSharedOut = !!outgoingRecipients;
            let rowOwnerDisplay = '';
            let rowOwnerUsername = '';
            let rowPermission = '';
            if (isSharedIn) {
                rowOwnerDisplay = t.owner_display_name || incomingOwner
                    || (opts.ownerLabel || 'another user');
                rowOwnerUsername = t.owner || (opts.section && opts.section._owner) || '';
                rowPermission = t.permission
                    || (opts.section && opts.section._permission) || 'read';
            }
            const recipientNames = outgoingRecipients
                ? outgoingRecipients.map(r => r.display_name || r.username).filter(Boolean)
                : [];
            const recipientShortList = recipientNames.length <= 6
                ? recipientNames.join(', ')
                : recipientNames.slice(0, 6).join(', ') + ' +' + (recipientNames.length - 6);
            if (isSharedOut) {
                badgeTooltip = `Shared with ${recipientShortList}`;
                fileBadgeSvg = FileOps._sharedOutIconHtml(shareActionColor, badgeTooltip);
            } else if (isSharedIn) {
                // Owner attribution for the hover bubble:
                //   - "Shared by Alice Smith (alice, write)" when we have
                //     both a display name and a distinct username (email)
                //   - "Shared by alice (write)" when we only have one
                //   - "Shared by <name>" when no permission is set
                // The username comes through as the auth `owner` field
                // (typically the login handle / email), display is the
                // friendlier label the owner set in their profile.
                const perm = rowPermission ? `, ${rowPermission}` : '';
                const u = (rowOwnerUsername || '').trim();
                const d = (rowOwnerDisplay || '').trim();
                let attribution;
                if (d && u && d.toLowerCase() !== u.toLowerCase()) {
                    attribution = `${d} (${u}${perm})`;
                } else {
                    const who = d || u || 'another user';
                    attribution = perm ? `${who} (${perm.slice(2)})` : who;
                }
                badgeTooltip = `Shared by ${attribution}`;
                fileBadgeSvg = FileOps._sharedInIconHtml(SHARED_IN_ACCENT, badgeTooltip);
            }
            // We intentionally DO NOT render inline "by <owner>" /
            // "→ recipients" text anymore -- the dropdown has to stay
            // tight for long filenames. All that information lives in
            // the share icon badge's tooltip (custom hover bubble, no
            // native-title delay) + the "BY <OWNER>" pill on the
            // shared-in domain header. The icon itself is the discovery
            // affordance; hover reveals the full attribution.
            const composite = (rowHit && rowHit.composite_id)
                || t.composite_id || (t._raw && t._raw.composite_id) || '';
            const topologyId = (t.id && !isSharedIn) ? t.id
                : ((t._raw && (t._raw.source_topology_id || t._raw.topology_id)) || t.id || '');
            const rowMetaAttrs =
                ` data-is-shared-in="${isSharedIn ? '1' : '0'}"`
                + ` data-is-shared-out="${isSharedOut ? '1' : '0'}"`
                + ` data-owner-username="${(rowOwnerUsername || '').replace(/"/g, '&quot;')}"`
                + ` data-owner-display="${(rowOwnerDisplay || '').replace(/"/g, '&quot;')}"`
                + ` data-permission="${(rowPermission || '').replace(/"/g, '&quot;')}"`
                + ` data-composite-id="${String(composite || '').replace(/"/g, '&quot;')}"`
                + ` data-topology-id="${String(topologyId || '').replace(/"/g, '&quot;')}"`;
            // Action-button visibility rules:
            //   Owner + shared-out  → Open, Rename, Duplicate, Share,
            //                          "Stop sharing with everyone" (×),
            //                          Delete.
            //   Owner + not shared  → Open, Rename, Duplicate, Share,
            //                          Delete.
            //   Recipient           → Open, Duplicate (can copy into
            //                          your own section), "Remove from
            //                          my list". Rename / Share / Delete
            //                          are hidden because the backend
            //                          rejects them anyway.
            const btnStyle = `style="background:none;border:none;cursor:pointer;padding:3px;display:flex;align-items:center;color:${iconOpColor};border-radius:4px;transition:background 0.12s;"`;
            const btnStyleTinted = (c) => `style="background:none;border:none;cursor:pointer;padding:3px;display:flex;align-items:center;color:${c};border-radius:4px;transition:background 0.12s;"`;
            const btnOpen = `<button class="ta-open ta-btn" ${btnStyle} title="Open"><svg viewBox="0 0 24 24" width="13" height="13" style="color:inherit;"><path d="M15 3h6v6M14 10l6.1-6.1M10 5H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/></svg></button>`;
            const btnRename = `<button class="ta-rename ta-btn" ${btnStyle} title="Rename"><svg viewBox="0 0 24 24" width="13" height="13" style="color:inherit;"><path d="M17 3a2.83 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" stroke="currentColor" stroke-width="2" fill="none"/></svg></button>`;
            const btnDuplicate = `<button class="ta-duplicate ta-btn" ${btnStyle} title="Duplicate to..."><svg viewBox="0 0 24 24" width="13" height="13" style="color:inherit;"><rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke="currentColor" stroke-width="2" fill="none"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke="currentColor" stroke-width="2" fill="none"/></svg></button>`;
            const btnShare = `<button class="ta-share ta-btn" ${btnStyleTinted(shareActionColor)} title="Share this file"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg></button>`;
            const btnUnshareAll = `<button class="ta-unshare-all ta-btn" ${btnStyleTinted(shareActionColor)} title="Stop sharing this file with everyone"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/><line x1="2" y1="2" x2="22" y2="22" stroke-width="2.3"/></svg></button>`;
            const btnDelete = `<button class="ta-delete ta-btn" ${btnStyle} title="Delete"><svg viewBox="0 0 24 24" width="13" height="13" style="color:inherit;"><polyline points="3 6 5 6 21 6" stroke="currentColor" stroke-width="2" fill="none"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" fill="none"/></svg></button>`;
            const btnRemoveMine = `<button class="ta-remove-mine ta-btn" ${btnStyleTinted(shareActionColor)} title="Remove from my Shared-with-me list (does not affect the owner)"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><circle cx="12" cy="12" r="9"/></svg></button>`;
            let actionsHtml;
            if (isSharedIn) {
                actionsHtml = btnOpen + btnDuplicate + btnRemoveMine;
            } else if (isSharedOut) {
                actionsHtml = btnOpen + btnRename + btnDuplicate + btnShare + btnUnshareAll + btnDelete;
            } else {
                actionsHtml = btnOpen + btnRename + btnDuplicate + btnShare + btnDelete;
            }
            // Per-topology View / Edit permission badge for shared-in
            // rows. Translates the wire token (read/write) to the
            // user-facing label via window.TopologyShare.permissionLabel.
            // Tooltip echoes who shared it so the recipient knows where
            // to go for an upgrade ("Shared by Alice (View only)").
            // Wire tokens stay unchanged on the data-permission attr
            // for downstream gating; only the label flips view/edit.
            let permBadgeHtml = '';
            if (isSharedIn) {
                const _shareApi = (typeof window !== 'undefined') ? window.TopologyShare : null;
                const _permLabel = (_shareApi && typeof _shareApi.permissionLabel === 'function')
                    ? _shareApi.permissionLabel(rowPermission)
                    : (rowPermission === 'write' ? 'Edit' : 'View');
                const _permTitle = (_shareApi && typeof _shareApi.permissionTitle === 'function')
                    ? _shareApi.permissionTitle(rowPermission)
                    : (rowPermission === 'write'
                        ? 'Edit: can open, modify, and save'
                        : 'View only: can open and inspect');
                const _ownerForTip = (rowOwnerDisplay || rowOwnerUsername || 'another user').replace(/"/g, '&quot;');
                const _permTipText = `${_permTitle} -- shared by ${_ownerForTip}`;
                const _permClass = (rowPermission === 'write') ? 'edit' : 'view';
                // Eye icon for View, pencil icon for Edit. Both inline so
                // dark/light themes inherit currentColor from the badge.
                const _permIconSvg = (rowPermission === 'write')
                    ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/></svg>'
                    : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
                permBadgeHtml = `<span class="ta-perm-badge ${_permClass}" data-perm="${rowPermission || 'read'}" title="${_permTipText.replace(/"/g, '&quot;')}">${_permIconSvg}${_permLabel}</span>`;
            }
            html += `<div class="domain-topo-row" data-filename="${filename}" data-section-id="${opts.sectionId || ''}"${rowMetaAttrs}
                style="display:flex;align-items:center;padding:3px 8px 3px 14px;margin-left:8px;border-left:2px solid ${isSharedIn ? SHARED_IN_ACCENT : color}${borderOp};border-radius:3px;cursor:pointer;transition:background 0.15s;user-select:none;">
                <svg class="topo-file-icon" viewBox="0 0 24 24" width="12" height="12" style="color:${iconOpColor};opacity:0.7;flex-shrink:0;margin-right:6px;">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2" fill="none"/>
                    <polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="2" fill="none"/>
                </svg>
                ${fileBadgeSvg ? `<span class="topo-shared-badge" title="${(badgeTooltip || '').replace(/"/g, '&quot;')}" style="display:flex;align-items:center;margin-right:5px;flex-shrink:0;">${fileBadgeSvg}</span>` : ''}
                ${permBadgeHtml ? `<span class="topo-perm-badge-wrap" style="display:flex;align-items:center;margin-right:5px;flex-shrink:0;">${permBadgeHtml}</span>` : ''}
                <span class="topo-entry-name" style="flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:11px;color:${txtColor};">${name}</span>
                ${timeAgo ? `<span class="topo-time" data-tooltip="Last saved: ${t.modified ? new Date(t.modified * 1000).toLocaleString(undefined, { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }) : ''}" style="display:flex;align-items:center;gap:2px;flex-shrink:0;margin-left:4px;font-size:9px;color:${mutedColor};white-space:nowrap;position:relative;cursor:default;">
                    <svg viewBox="0 0 24 24" width="9" height="9" style="opacity:0.7;"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/><polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/></svg>
                    ${timeAgo}
                </span>` : ''}
                <span class="topo-actions" style="display:flex;flex-shrink:0;gap:2px;align-items:center;margin-left:4px;visibility:hidden;opacity:0;transition:opacity 0.12s;">
                    ${actionsHtml}
                </span>
            </div>`;
        });
        container.innerHTML = html;

        // Regrow the dropdown to fit the widest filename. Deferred a
        // frame so the browser has finished laying out the new rows --
        // synchronously measuring right after innerHTML assignment
        // sometimes returns pre-reflow sizes in Firefox.
        requestAnimationFrame(() => FileOps._fitDropdownToContent());

        container.querySelectorAll('.domain-topo-row').forEach(row => {
            row.addEventListener('mouseenter', () => {
                const dk = FileOps._menuDark(editor);
                row.style.background = dk ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.07)';
                const a = row.querySelector('.topo-actions'); if (a) { a.style.visibility = 'visible'; a.style.opacity = '1'; }
            });
            row.addEventListener('mouseleave', () => {
                row.style.background = '';
                const a = row.querySelector('.topo-actions'); if (a) { a.style.visibility = 'hidden'; a.style.opacity = '0'; }
                document.querySelectorAll('.ta-btn-tip').forEach(t => t.remove());
            });
            row.querySelectorAll('.ta-btn').forEach(btn => FileOps._attachHoverTip(btn, {
                hoverBg: 'rgba(255,255,255,0.12)',
            }));
            // Rich hover tooltip on the share badge (purple receive
            // icon for shared-in, 3-circle icon for shared-out) so
            // hovering the badge surfaces "Shared by Alice (read)" or
            // "Shared with bob, carol" instantly -- no inline text on
            // the row itself, per the tight-row design.
            row.querySelectorAll('.topo-shared-badge')
                .forEach(el => FileOps._attachHoverTip(el));
            // Same custom hover bubble for the View / Edit permission
            // badge so users see "Edit: can open, modify, and save --
            // shared by Alice" instantly. Title attribute is on the
            // badge so _attachHoverTip pulls it as the bubble text.
            row.querySelectorAll('.ta-perm-badge')
                .forEach(el => FileOps._attachHoverTip(el));

            const openBtn = row.querySelector('.ta-open');
            if (openBtn) {
                openBtn.onclick = (e) => {
                    e.stopPropagation();
                    if (opts.loadFn) {
                        const label = row.querySelector('.topo-entry-name')?.textContent || row.dataset.filename;
                        FileOps._requestTopologySwitch(editor, label, () => opts.loadFn(row.dataset.filename, row));
                    }
                };
            }
            const renameBtn = row.querySelector('.ta-rename');
            if (renameBtn) {
                renameBtn.onclick = (e) => { e.stopPropagation(); FileOps._showRenameInput(editor, row, color, container, opts); };
            }
            const dupBtn = row.querySelector('.ta-duplicate');
            if (dupBtn) {
                dupBtn.onclick = (e) => {
                    e.stopPropagation();
                    FileOps._showDuplicatePicker(editor, row, opts.sectionId, container, opts);
                };
            }
            const shareTopoBtn = row.querySelector('.ta-share');
            if (shareTopoBtn) {
                shareTopoBtn.addEventListener('mousedown', (e) => { e.stopPropagation(); });
                shareTopoBtn.onclick = async (e) => {
                    e.stopPropagation();
                    const topoName = (row.querySelector('.topo-entry-name')?.textContent || '').trim()
                        || (row.dataset.filename || '').replace(/\.json$/i, '');
                    const topoFilename = row.dataset.filename
                        || (topoName.toLowerCase().endsWith('.json') ? topoName : topoName + '.json');
                    const anchorEl = e.currentTarget;

                    if (!(window.TopologyShare && typeof window.TopologyShare.openForDomain === 'function')) {
                        if (window.TopologyShare && typeof window.TopologyShare.open === 'function') {
                            window.TopologyShare.open(anchorEl);
                        } else {
                            editor.showToast('Share is not available right now', 'warning');
                        }
                        return;
                    }

                    // Re-entrance guard: the first share-click on a legacy
                    // file runs a multi-step migration (3-4 HTTP roundtrips)
                    // and users instinctively double-click. Without this
                    // guard the second click spawns a parallel migration
                    // and the mirror-register race can leave the mapping
                    // pointing at the wrong row.
                    if (shareTopoBtn.dataset.working === '1') return;
                    shareTopoBtn.dataset.working = '1';
                    shareTopoBtn.disabled = true;
                    const prevIconHtml = shareTopoBtn.innerHTML;
                    shareTopoBtn.innerHTML = FileOps._inlineSpinnerHtml(color || '#9ca3af');

                    // CRITICAL: suspend the global `topology-domains:changed`
                    // listener while we migrate + open the popover. Migration
                    // calls fetchDomains() 2-3 times, and each emit would
                    // trigger _renderCustomSectionsInDropdown, which REPLACES
                    // the dropdown DOM -- orphaning `anchorEl` and the
                    // surrounding `.custom-section-category`. The share
                    // popover then mounts into a detached subtree and the
                    // user just sees the panel "flap" with no dialog.
                    FileOps._suspendDropdownRefresh = (FileOps._suspendDropdownRefresh || 0) + 1;

                    // Legacy -> multi-user bridge: ensure a real UUID pair
                    // exists for this topology before the share dialog asks
                    // the server to grant access. Without this the POST to
                    // /api/domains/<?>/topologies/<legacy_name>/share returns
                    // 404 because the multi-user DB never saw this file.
                    let migrated = null;
                    let popoverOpened = false;
                    try {
                        migrated = await FileOps._ensureLegacyTopologyMigrated(
                            editor, opts.sectionId, opts.section, topoFilename
                        );
                        // Persist the mapping server-side so future legacy
                        // saves / renames / deletes can mirror into the
                        // multi-user DB without another migration round-trip.
                        // Retry up to 3 times with exponential backoff because
                        // the mapping is load-bearing: if it never lands,
                        // owner saves stop propagating silently.
                        if (migrated && migrated.domain && migrated.topology) {
                            const ok = await FileOps._mirrorRegisterWithRetry(
                                opts.sectionId, topoFilename,
                                migrated.domain.id, migrated.topology.id,
                            );
                            if (!ok) {
                                editor.showToast(
                                    'Share will work, but save-sync is offline ' +
                                    '(mapping could not be saved server-side). ' +
                                    'Re-share this file to retry.',
                                    'warning',
                                );
                            }
                        }
                        // Resolve the hint + open the popover SYNCHRONOUSLY
                        // against the still-live DOM. anchorEl is the button
                        // the user just clicked; .closest('.custom-section-
                        // category') walks up to the live domain row.
                        const domainHint = (migrated && migrated.domain && migrated.domain.id)
                            || (opts.section && opts.section.name)
                            || opts.sectionId;
                        const topoHint = (migrated && migrated.topology && migrated.topology.name) || topoName;
                        await window.TopologyShare.openForDomain(domainHint, topoHint, anchorEl);
                        popoverOpened = true;
                    } catch (err) {
                        const msg = (err && err.message) ? err.message : String(err);
                        editor.showToast('Cannot prepare sharing: ' + msg, 'error');
                    } finally {
                        shareTopoBtn.disabled = false;
                        shareTopoBtn.innerHTML = prevIconHtml;
                        delete shareTopoBtn.dataset.working;
                        FileOps._suspendDropdownRefresh = Math.max(
                            0, (FileOps._suspendDropdownRefresh || 1) - 1,
                        );
                        // Refresh the sharing cache so the outgoing-share
                        // badge appears next time the dropdown is rebuilt.
                        // We DO NOT re-render the dropdown now: the popover
                        // is live inside the dropdown DOM and a rebuild
                        // would rip it out. Once the popover closes, the
                        // next natural re-render (hover, open, listener)
                        // will pick up the fresh cache.
                        if (popoverOpened && FileOps._suspendDropdownRefresh === 0) {
                            FileOps._refreshSharingCache(true).catch(() => {});
                        }
                    }
                };
            }
            const deleteBtn = row.querySelector('.ta-delete');
            if (deleteBtn) {
                deleteBtn.onclick = (e) => {
                    e.stopPropagation();
                    const existing = container.querySelector('.delete-confirm-bar');
                    if (existing) existing.remove();
                    const nameTxt = row.querySelector('.topo-entry-name')?.textContent?.trim() || row.dataset.filename;
                    const bar = document.createElement('div');
                    bar.className = 'delete-confirm-bar';
                    const isDark = FileOps._menuDark(editor);
                    bar.style.cssText = `display:flex;align-items:center;gap:6px;padding:4px 12px 4px 20px;margin-left:8px;background:${isDark ? 'rgba(239,68,68,0.1)' : 'rgba(239,68,68,0.08)'};border-left:2px solid #ef4444;border-radius:3px;`;
                    bar.innerHTML = `
                        <span style="flex:1;font-size:10px;">Delete "${nameTxt}"?</span>
                        <button class="dc-yes" style="padding:3px 10px;background:#ef4444;border:none;border-radius:4px;color:#fff;font-size:10px;font-weight:600;cursor:pointer;">Delete</button>
                        <button class="dc-no" style="padding:3px 8px;background:${isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)'};border:1px solid ${isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.12)'};border-radius:4px;color:${isDark ? '#94a3b8' : '#475569'};font-size:10px;cursor:pointer;">Cancel</button>
                    `;
                    row.after(bar);
                    bar.querySelector('.dc-yes').onclick = (ev) => { ev.stopPropagation(); bar.remove(); if (opts.deleteFn) opts.deleteFn(row.dataset.filename); };
                    bar.querySelector('.dc-no').onclick = (ev) => { ev.stopPropagation(); bar.remove(); };
                };
            }

            // Owner "Stop sharing with everyone" -- collapses the share
            // popover's revoke-per-user flow into a single click. We
            // collect every current recipient from the share index and
            // issue one unshare-topology POST per recipient (the backend
            // has no bulk endpoint today, but the calls are idempotent
            // and fast). Guarded by an inline confirm bar so a
            // miss-click doesn't silently detach everyone.
            const unshareAllBtn = row.querySelector('.ta-unshare-all');
            if (unshareAllBtn) {
                unshareAllBtn.onclick = async (e) => {
                    e.stopPropagation();
                    const existing = container.querySelector('.unshare-confirm-bar');
                    if (existing) existing.remove();
                    const nameTxt = row.querySelector('.topo-entry-name')?.textContent?.trim()
                        || row.dataset.filename;
                    const bar = document.createElement('div');
                    bar.className = 'unshare-confirm-bar';
                    const isDark = FileOps._menuDark(editor);
                    bar.style.cssText = `display:flex;align-items:center;gap:6px;padding:4px 12px 4px 20px;margin-left:8px;background:${isDark ? 'rgba(167,139,250,0.12)' : 'rgba(167,139,250,0.10)'};border-left:2px solid #a78bfa;border-radius:3px;`;
                    bar.innerHTML = `
                        <span style="flex:1;font-size:10px;">Stop sharing "${nameTxt}" with everyone?</span>
                        <button class="uc-yes" style="padding:3px 10px;background:#a78bfa;border:none;border-radius:4px;color:#fff;font-size:10px;font-weight:600;cursor:pointer;">Stop sharing</button>
                        <button class="uc-no" style="padding:3px 8px;background:${isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)'};border:1px solid ${isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.12)'};border-radius:4px;color:${isDark ? '#94a3b8' : '#475569'};font-size:10px;cursor:pointer;">Cancel</button>
                    `;
                    row.after(bar);
                    bar.querySelector('.uc-no').onclick = (ev) => { ev.stopPropagation(); bar.remove(); };
                    bar.querySelector('.uc-yes').onclick = async (ev) => {
                        ev.stopPropagation();
                        bar.remove();
                        await FileOps._unshareAllRecipientsForRow(editor, row, opts);
                    };
                };
            }

            // Recipient "Remove from my list" -- hits the new recipient
            // self-remove endpoint with the row's composite_id (or the
            // synthesized <owner>:<src_dom>:<src_topo> for shared-in
            // domain files whose id isn't a composite). Optimistically
            // removes the row on success; toast + restore on error.
            const removeMineBtn = row.querySelector('.ta-remove-mine');
            if (removeMineBtn) {
                removeMineBtn.onclick = async (e) => {
                    e.stopPropagation();
                    const existing = container.querySelector('.remove-mine-confirm-bar');
                    if (existing) existing.remove();
                    const nameTxt = row.querySelector('.topo-entry-name')?.textContent?.trim()
                        || row.dataset.filename;
                    const ownerDisp = row.dataset.ownerDisplay || 'the owner';
                    const bar = document.createElement('div');
                    bar.className = 'remove-mine-confirm-bar';
                    const isDark = FileOps._menuDark(editor);
                    bar.style.cssText = `display:flex;align-items:center;gap:6px;padding:4px 12px 4px 20px;margin-left:8px;background:${isDark ? 'rgba(167,139,250,0.12)' : 'rgba(167,139,250,0.10)'};border-left:2px solid #a78bfa;border-radius:3px;`;
                    bar.innerHTML = `
                        <span style="flex:1;font-size:10px;">Remove "${nameTxt}" from your list? (${ownerDisp} still keeps the original.)</span>
                        <button class="rm-yes" style="padding:3px 10px;background:#a78bfa;border:none;border-radius:4px;color:#fff;font-size:10px;font-weight:600;cursor:pointer;">Remove</button>
                        <button class="rm-no" style="padding:3px 8px;background:${isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)'};border:1px solid ${isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.12)'};border-radius:4px;color:${isDark ? '#94a3b8' : '#475569'};font-size:10px;cursor:pointer;">Cancel</button>
                    `;
                    row.after(bar);
                    bar.querySelector('.rm-no').onclick = (ev) => { ev.stopPropagation(); bar.remove(); };
                    bar.querySelector('.rm-yes').onclick = async (ev) => {
                        ev.stopPropagation();
                        bar.remove();
                        await FileOps._removeIncomingShareForRow(editor, row, container, opts);
                    };
                };
            }

            // Drag from entire row — click loads, drag reorders/moves
            if (opts.sectionId) {
                row.style.cursor = 'grab';
                row.addEventListener('mousedown', (e) => {
                    if (e.button !== 0) return;
                    if (e.target.closest('.ta-btn') || e.target.closest('.topo-actions') || e.target.closest('.delete-confirm-bar')) return;
                    e.preventDefault();
                    const startY = e.clientY, startX = e.clientX;
                    let dragging = false;
                    let dropIndicator = null;
                    let hoveredDomainId = null;
                    const srcSectionId = opts.sectionId;
                    const dk = FileOps._menuDark(editor);
                    const ease = 'cubic-bezier(0.22, 1, 0.36, 1)';

                    let allRows = [];
                    let offsets = [];
                    let heights = [];
                    let slotYs = [];
                    let currentOrder = [];
                    let dragIdx = -1;
                    let dragDropdown = null;
                    let sourceBodyEl = null;
                    let startContainerScrollTop = 0;
                    let startDropdownScrollTop = 0;

                    const applyRowTransforms = () => {
                        for (let pos = 0; pos < currentOrder.length; pos++) {
                            const idx = currentOrder[pos];
                            if (idx === dragIdx) continue;
                            const dy = slotYs[pos] - offsets[idx];
                            allRows[idx].style.transition = `transform 0.17s ${ease}`;
                            allRows[idx].style.transform = dy ? `translateY(${dy}px)` : '';
                        }
                    };

                    const rebuildDragGeometry = () => {
                        offsets = allRows.map(r => r.offsetTop);
                        heights = allRows.map(r => r.offsetHeight);
                        slotYs = [];
                        let y = offsets[0] || 0;
                        for (let i = 0; i < allRows.length; i++) {
                            slotYs.push(y);
                            if (i < allRows.length - 1) {
                                const gap = offsets[i + 1] - (offsets[i] + heights[i]);
                                y += heights[i] + Math.max(gap, 0);
                            }
                        }
                    };

                    const autoScrollDuringRowDrag = (clientY) => {
                        const scrollTargets = [container, dragDropdown]
                            .filter((el, idx, arr) => el && arr.indexOf(el) === idx);
                        scrollTargets.forEach(el => {
                            if (!el || el.scrollHeight <= el.clientHeight + 2) return;
                            const rect = el.getBoundingClientRect();
                            const edge = Math.min(42, Math.max(24, rect.height * 0.18));
                            let delta = 0;
                            if (clientY > rect.bottom - edge) {
                                delta = Math.ceil((clientY - (rect.bottom - edge)) / 3);
                            } else if (clientY < rect.top + edge) {
                                delta = -Math.ceil(((rect.top + edge) - clientY) / 3);
                            }
                            if (!delta) return;
                            const before = el.scrollTop;
                            el.scrollTop = Math.max(0, Math.min(el.scrollTop + delta, el.scrollHeight - el.clientHeight));
                            if (el.scrollTop !== before && el === container) {
                                rebuildDragGeometry();
                                applyRowTransforms();
                            }
                        });
                    };

                    const onMove = (ev) => {
                        if (!dragging && Math.abs(ev.clientY - startY) + Math.abs(ev.clientX - startX) < 6) return;
                        if (!dragging) {
                            dragging = true;
                            editor._topoDragActive = true;

                            dragDropdown = document.getElementById('topologies-dropdown-menu');
                            sourceBodyEl = row.closest('.domain-body');
                            if (dragDropdown) {
                                dragDropdown.classList.add('is-topo-row-dragging');
                            }
                            if (sourceBodyEl) {
                                sourceBodyEl.classList.add('is-drag-source-body');
                            }
                            container.classList.add('is-drag-source');

                            allRows = [...container.querySelectorAll('.domain-topo-row')];
                            dragIdx = allRows.indexOf(row);
                            allRows.forEach(r => { r.style.transform = ''; r.style.transition = 'none'; });
                            currentOrder = allRows.map((_, i) => i);
                            startContainerScrollTop = container.scrollTop || 0;
                            startDropdownScrollTop = dragDropdown ? (dragDropdown.scrollTop || 0) : 0;
                            rebuildDragGeometry();

                            row.style.position = 'relative';
                            row.style.zIndex = '100';
                            row.classList.add('is-dragging');
                            row.style.boxShadow = '0 4px 14px rgba(0,0,0,0.22)';
                            row.style.opacity = '0.92';
                            row.style.borderRadius = '4px';
                            row.style.background = dk ? 'rgba(25,30,50,0.95)' : 'rgba(255,255,255,0.95)';
                            allRows.forEach((r, i) => {
                                if (i !== dragIdx) { r.style.position = 'relative'; r.style.zIndex = '1'; }
                            });

                            dropIndicator = document.createElement('div');
                            dropIndicator.style.cssText = `height:3px;border-radius:2px;pointer-events:none;display:none;position:fixed;z-index:999998;transition:top 0.12s ease,left 0.12s ease,width 0.12s ease;`;
                            document.body.appendChild(dropIndicator);

                            document.body.style.cursor = 'grabbing';
                            row.style.cursor = 'grabbing';
                        }

                        autoScrollDuringRowDrag(ev.clientY);
                        const pointerDy = ev.clientY - startY;
                        const containerScrollDy = (container.scrollTop || 0) - startContainerScrollTop;
                        const dropdownScrollDy = dragDropdown ? ((dragDropdown.scrollTop || 0) - startDropdownScrollTop) : 0;
                        const contentDy = pointerDy + containerScrollDy;
                        const visualDy = pointerDy + containerScrollDy + dropdownScrollDy;
                        row.style.transform = `translateY(${visualDy}px)`;
                        row.style.transition = 'none';

                        let overOtherDomain = false;
                        let newHoveredId = null;
                        dropIndicator.style.display = 'none';

                        const dropTarget = FileOps._getDomainDropTarget(
                            editor, ev.clientX, ev.clientY, srcSectionId
                        );
                        document.querySelectorAll('.custom-section-category:not([data-shared-in="1"])').forEach(secEl => {
                            const secId = secEl.dataset.sectionId;
                            const secObj = (editor._customSections || []).find(s => s.id === secId);
                            const sc = secObj?.color || '#3b82f6';
                            const isDkD = FileOps._menuDark(editor);
                            const isTarget = dropTarget && dropTarget.element === secEl;

                            if (isTarget) {
                                overOtherDomain = true;
                                newHoveredId = secId;

                                const bodyEl = secEl.querySelector('.domain-body');
                                const isCollapsed = dropTarget.isCollapsed || (bodyEl && bodyEl.style.display === 'none');

                                secEl.style.transition = 'all 0.15s ease';
                                // Drag-hover must be clearly brighter than the resting
                                // chip (now 38/48). Bump to 55/60 -> 28/32 so the
                                // gradient still peaks visibly above the baseline.
                                secEl.style.background = `linear-gradient(135deg, ${sc}${isDkD ? '55' : '60'}, ${sc}${isDkD ? '28' : '32'})`;
                                secEl.style.boxShadow = `inset 0 0 0 1.5px ${sc}a0, 0 4px 20px ${sc}40`;
                                secEl.classList.add('is-drag-target');

                                if (!isCollapsed) {
                                    const topoRows = secEl.querySelectorAll('.domain-topo-row');
                                    const toposList = secEl.querySelector('.domain-topos-list');

                                    let existingGhost = secEl.querySelector('.drop-ghost');
                                    if (!existingGhost) {
                                        existingGhost = document.createElement('div');
                                        existingGhost.className = 'drop-ghost';
                                        existingGhost.style.cssText = `
                                            height: 28px; margin: 2px 8px 2px 14px; border-radius: 6px;
                                            background: ${isDkD
                                                ? 'linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02))'
                                                : 'linear-gradient(135deg, rgba(255,255,255,0.5), rgba(255,255,255,0.25))'};
                                            border: 1px dashed ${sc}50;
                                            backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
                                            box-shadow: inset 0 1px 0 ${isDkD ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.4)'};
                                            transition: opacity 0.15s ease;
                                            pointer-events: none;
                                        `;
                                    }

                                    if (topoRows.length === 0 && toposList) {
                                        if (!toposList.contains(existingGhost)) toposList.appendChild(existingGhost);
                                    } else if (topoRows.length > 0) {
                                        let bestRow = null, bestDist = Infinity, insertAfter = false;
                                        topoRows.forEach(r => {
                                            const rr = r.getBoundingClientRect();
                                            const mid = rr.top + rr.height / 2;
                                            const dist = Math.abs(ev.clientY - mid);
                                            if (dist < bestDist) { bestDist = dist; bestRow = r; insertAfter = ev.clientY > mid; }
                                        });
                                        if (bestRow) {
                                            if (insertAfter) {
                                                bestRow.after(existingGhost);
                                            } else {
                                                bestRow.before(existingGhost);
                                            }
                                        }
                                    }
                                }
                            } else {
                                secEl.style.background = `${sc}${isDkD ? '38' : '48'}`;
                                secEl.style.boxShadow = '';
                                secEl.style.transition = 'all 0.2s ease';
                                secEl.classList.remove('is-drag-target');
                                const ghost = secEl.querySelector('.drop-ghost');
                                if (ghost) ghost.remove();
                            }
                        });

                        hoveredDomainId = newHoveredId;
                        if (!overOtherDomain) hoveredDomainId = null;

                        if (!overOtherDomain && dragIdx >= 0) {
                            const dragMid = offsets[dragIdx] + contentDy + heights[dragIdx] / 2;
                            const dragPos = currentOrder.indexOf(dragIdx);

                            if (dragPos > 0) {
                                const aboveIdx = currentOrder[dragPos - 1];
                                const aboveMid = slotYs[dragPos - 1] + heights[aboveIdx] * 0.45;
                                if (dragMid < aboveMid) {
                                    currentOrder.splice(dragPos, 1);
                                    currentOrder.splice(dragPos - 1, 0, dragIdx);
                                    applyRowTransforms();
                                }
                            }
                            if (dragPos < currentOrder.length - 1) {
                                const belowIdx = currentOrder[dragPos + 1];
                                const belowMid = slotYs[dragPos + 1] + heights[belowIdx] * 0.55;
                                if (dragMid > belowMid) {
                                    currentOrder.splice(dragPos, 1);
                                    currentOrder.splice(dragPos + 1, 0, dragIdx);
                                    applyRowTransforms();
                                }
                            }
                        }
                    };

                    const releaseTopoDragContainers = () => {
                        if (dragDropdown) {
                            dragDropdown.classList.remove('is-topo-row-dragging');
                            dragDropdown.style.removeProperty('overflow');
                            dragDropdown.style.removeProperty('overflow-y');
                        }
                        if (sourceBodyEl) {
                            sourceBodyEl.classList.remove('is-drag-source-body');
                            sourceBodyEl.style.removeProperty('overflow');
                            sourceBodyEl.style.removeProperty('overflow-y');
                        }
                        container.classList.remove('is-drag-source');
                        container.style.removeProperty('overflow');
                        container.style.removeProperty('overflow-y');
                    };

                    const cleanupDrag = () => {
                        document.removeEventListener('mousemove', onMove);
                        document.removeEventListener('mouseup', onUp);
                        document.body.style.cursor = '';
                        editor._topoDragActive = false;
                        if (dropIndicator) { dropIndicator.remove(); dropIndicator = null; }
                        document.querySelectorAll('.drop-ghost').forEach(g => g.remove());
                        releaseTopoDragContainers();
                        document.querySelectorAll('.custom-section-category').forEach(secEl => {
                            const secObj = (editor._customSections || []).find(s => s.id === secEl.dataset.sectionId);
                            const sc = secObj?.color || '#3b82f6';
                            const isDkD = FileOps._menuDark(editor);
                            secEl.style.background = `${sc}${isDkD ? '38' : '48'}`;
                            secEl.style.boxShadow = '';
                            secEl.style.transition = 'all 0.2s ease';
                            secEl.classList.remove('is-drag-target');
                        });
                    };

                    const onUp = async (ev) => {
                        if (!dragging) {
                            document.removeEventListener('mousemove', onMove);
                            document.removeEventListener('mouseup', onUp);
                            if (opts.loadFn) {
                                const label = row.querySelector('.topo-entry-name')?.textContent || row.dataset.filename;
                                FileOps._requestTopologySwitch(editor, label, () => opts.loadFn(row.dataset.filename, row));
                            }
                            return;
                        }

                        const filename = row.dataset.filename;

                        const finalDropTarget = FileOps._getDomainDropTarget(
                            editor, ev.clientX, ev.clientY, srcSectionId
                        );
                        const targetSectionId = finalDropTarget ? finalDropTarget.sectionId : null;

                        if (targetSectionId && filename) {
                            const moveFile = filename.endsWith('.json') ? filename : filename + '.json';
                            const targetDivBeforeCleanup = document.querySelector(`.custom-section-category[data-section-id="${targetSectionId}"]`);
                            const targetOrderBeforeCleanup = FileOps._topologyOrderFromDom(
                                targetDivBeforeCleanup?.querySelector('.domain-topos-list'),
                                moveFile
                            );
                            document.removeEventListener('mousemove', onMove);
                            document.removeEventListener('mouseup', onUp);
                            document.body.style.cursor = '';
                            editor._topoDragActive = false;
                            if (dropIndicator) { dropIndicator.remove(); dropIndicator = null; }
                            document.querySelectorAll('.drop-ghost').forEach(g => g.remove());
                            document.querySelectorAll('.custom-section-category').forEach(secEl => {
                                const secObj2 = (editor._customSections || []).find(s => s.id === secEl.dataset.sectionId);
                                const sc2 = secObj2?.color || '#3b82f6';
                                const isDk2 = FileOps._menuDark(editor);
                                secEl.style.background = `${sc2}${isDk2 ? '38' : '48'}`;
                                secEl.style.boxShadow = '';
                                secEl.style.transition = 'all 0.2s ease';
                                secEl.classList.remove('is-drag-target');
                            });

                            const moveUrl = `/api/sections/${encodeURIComponent(srcSectionId)}/topologies/${encodeURIComponent(moveFile)}/move`;
                            const dstSec = (editor._customSections || []).find(s => s.id === targetSectionId);
                            const srcSec = (editor._customSections || []).find(s => s.id === srcSectionId);
                            const dstColor = dstSec?.color || '#3b82f6';

                            const tgtDiv = document.querySelector(`.custom-section-category[data-section-id="${targetSectionId}"]`);
                            let dstCtr = tgtDiv?.querySelector('.domain-topos-list');

                            if (editor._domainCollapsed && editor._domainCollapsed[targetSectionId] && tgtDiv) {
                                editor._domainCollapsed[targetSectionId] = false;
                                const b = tgtDiv.querySelector('.domain-body'); if (b) b.style.display = 'block';
                                const c = tgtDiv.querySelector('.domain-chevron'); if (c) c.style.transform = 'rotate(0deg)';
                                dstCtr = tgtDiv.querySelector('.domain-topos-list');
                            }

                            const h = row.offsetHeight;
                            row.style.transition = `opacity 0.25s ease, transform 0.25s ${ease}`;
                            row.style.opacity = '0';
                            row.style.transform = `translateX(20px) scale(0.95)`;

                            const siblings = allRows.filter((_, i) => i !== dragIdx);
                            siblings.forEach(r => {
                                r.style.transition = `transform 0.3s ${ease}`;
                                r.style.transform = '';
                            });

                            await new Promise(r => setTimeout(r, 260));

                            row.style.transition = `height 0.2s ${ease}, padding 0.2s ${ease}, margin 0.2s ${ease}, border 0.2s ${ease}`;
                            row.style.height = '0px';
                            row.style.paddingTop = '0px';
                            row.style.paddingBottom = '0px';
                            row.style.marginTop = '0px';
                            row.style.marginBottom = '0px';
                            row.style.overflow = 'hidden';
                            row.style.borderLeftWidth = '0px';


                            await new Promise(r => setTimeout(r, 220));

                            try {
                                const targetOrder = targetOrderBeforeCleanup || FileOps._topologyOrderFromDom(dstCtr, moveFile);
                                const payload = { target_section_id: targetSectionId };
                                if (targetOrder && targetOrder.length) payload.target_order = targetOrder;
                                const resp = await FileOps._authFetch(moveUrl, {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify(payload)
                                });
                                const revert = async () => {
                                    releaseTopoDragContainers();
                                    FileOps._resetRowStyles(allRows);
                                    const srcCtrR = document.querySelector(`.custom-section-category[data-section-id="${srcSectionId}"] .domain-topos-list`);
                                    if (srcCtrR && srcSec) await FileOps._loadDomainTopologiesInline(editor, srcSec, srcCtrR);
                                };
                                const result = await resp.json();
                                if (!resp.ok) {
                                    if (FileOps._isDomainLimitResult(result) && dstSec) {
                                        await FileOps._openDomainCleanupPrompt(editor, dstSec, dstCtr, {
                                            reason: 'limit',
                                            limitResult: result,
                                        });
                                        editor.showToast('Move not completed. Drag the topology again after cleanup.', 'info');
                                    } else {
                                        editor.showToast(`Move failed: ${resp.status}`, 'error');
                                    }
                                    await revert();
                                    return;
                                }
                                if (result.error) { editor.showToast('Move failed: ' + result.error, 'error'); await revert(); return; }

                                editor.showToast(`Moved "${moveFile.replace(/\.json$/, '')}" → ${dstSec?.name || 'domain'}`, 'success');
                                FileOps._resetRowStyles(allRows);

                                const refreshPromises = [];
                                if (srcSec) {
                                    const srcCtrF = document.querySelector(`.custom-section-category[data-section-id="${srcSectionId}"] .domain-topos-list`);
                                    if (srcCtrF) refreshPromises.push(FileOps._loadDomainTopologiesInline(editor, srcSec, srcCtrF));
                                }
                                if (dstSec && dstCtr) {
                                    refreshPromises.push(
                                        FileOps._loadDomainTopologiesInline(editor, dstSec, dstCtr).then(() => {
                                            const movedName = moveFile.replace(/\.json$/, '');
                                            dstCtr.querySelectorAll('.domain-topo-row').forEach(nr => {
                                                if (nr.querySelector('.topo-entry-name')?.textContent?.trim() === movedName) {
                                                    nr.style.opacity = '0';
                                                    nr.style.transform = 'translateY(-4px)';
                                                    requestAnimationFrame(() => {
                                                        nr.style.transition = `opacity 0.3s ease 0.05s, transform 0.3s ${ease} 0.05s`;
                                                        nr.style.opacity = '1';
                                                        nr.style.transform = '';
                                                        nr.style.background = `${dstColor}20`;
                                                        setTimeout(() => { nr.style.transition = 'background 0.8s ease'; nr.style.background = ''; }, 800);
                                                    });
                                                }
                                            });
                                        })
                                    );
                                }
                                await Promise.all(refreshPromises);
                            } catch (err) {
                                editor.showToast('Move failed: ' + err.message, 'error');
                                FileOps._resetRowStyles(allRows);
                                const srcCtrR = document.querySelector(`.custom-section-category[data-section-id="${srcSectionId}"] .domain-topos-list`);
                                if (srcCtrR && srcSec) await FileOps._loadDomainTopologiesInline(editor, srcSec, srcCtrR);
                            }

                            releaseTopoDragContainers();
                            return;
                        }

                        cleanupDrag();

                        // Same-domain reorder
                        const orderChanged = currentOrder.some((idx, pos) => idx !== pos);
                        const dragPos = currentOrder.indexOf(dragIdx);
                        const finalDy = slotYs[dragPos] - offsets[dragIdx];
                        row.style.transition = `transform 0.18s ${ease}, box-shadow 0.18s, opacity 0.18s`;
                        row.style.transform = finalDy ? `translateY(${finalDy}px)` : '';
                        row.style.boxShadow = '';
                        row.style.opacity = '1';

                        setTimeout(async () => {
                            FileOps._resetRowStyles(allRows);
                            if (orderChanged) {
                                const frag = document.createDocumentFragment();
                                currentOrder.forEach(idx => frag.appendChild(allRows[idx]));
                                container.appendChild(frag);
                                const finalOrder = currentOrder.map(idx => allRows[idx]?.dataset?.filename).filter(Boolean);
                                try {
                                    await FileOps._persistTopologyOrder(editor, srcSectionId, finalOrder);
                                } catch (err) {
                                    editor.showToast('Topology order was updated locally, but saving the order failed: ' + err.message, 'warning');
                                }
                            }
                        }, 210);
                    };

                    document.addEventListener('mousemove', onMove);
                    document.addEventListener('mouseup', onUp);
                });
            } else {
                row.onclick = (e) => {
                    e.stopPropagation();
                    if (opts.loadFn) {
                        const label = row.querySelector('.topo-entry-name')?.textContent || row.dataset.filename;
                        FileOps._requestTopologySwitch(editor, label, () => opts.loadFn(row.dataset.filename, row));
                    }
                };
            }
        });
    },

    _resetRowStyles(rows) {
        rows.forEach(r => {
            r.classList.remove('is-dragging');
            r.style.transform = '';
            r.style.transition = '';
            r.style.position = '';
            r.style.zIndex = '';
            r.style.boxShadow = '';
            r.style.opacity = '';
            r.style.cursor = '';
            r.style.background = '';
            r.style.borderRadius = '';
        });
    },

    _authFetch(url, options) {
        const fn = (window.TopologyAuth && window.TopologyAuth.authFetch)
            ? window.TopologyAuth.authFetch.bind(window.TopologyAuth)
            : fetch;
        return fn(url, options);
    },

    _unwrapErrorDetail(result) {
        if (result && result.detail && typeof result.detail === 'object') {
            return result.detail;
        }
        return result || {};
    },

    _isDomainLimitResult(result) {
        const detail = FileOps._unwrapErrorDetail(result);
        return !!(detail && detail.code === 'domain-topology-limit');
    },

    async _fetchSectionTopologies(sectionId) {
        const resp = await FileOps._authFetch(
            `/api/sections/${encodeURIComponent(sectionId)}/topologies`,
        );
        const data = await resp.json().catch(() => ({}));
        if (!resp.ok || data.error) {
            throw new Error(data.error || 'Topology list unavailable');
        }
        return Array.isArray(data.topologies) ? data.topologies : [];
    },

    async _cleanupSectionTopologies(sectionId, filenames) {
        const resp = await FileOps._authFetch(
            `/api/sections/${encodeURIComponent(sectionId)}/topologies/cleanup`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filenames: filenames || [] }),
            },
        );
        const data = await resp.json().catch(() => ({}));
        if (!resp.ok || data.error) {
            throw new Error(data.error || 'Cleanup failed');
        }
        return data;
    },

    async _openDomainCleanupPrompt(editor, section, container, opts = {}) {
        const stale = document.getElementById('domain-topology-cleanup-prompt');
        if (stale) stale.remove();
        const limitDetail = FileOps._unwrapErrorDetail(opts.limitResult || {});
        let topologies = Array.isArray(limitDetail.topologies) ? limitDetail.topologies : null;
        try {
            if (!topologies) topologies = await FileOps._fetchSectionTopologies(section.id);
        } catch (err) {
            editor.showToast('Cannot load domain topologies: ' + (err.message || err), 'error');
            return null;
        }
        if (!topologies.length) {
            editor.showToast('Domain is already clean', 'info');
            return null;
        }
        const isLimit = opts.reason === 'limit';
        const t = FileOps._menuDark(editor)
            ? { bg: '#101828', panel: '#111f33', text: '#e5eefb', muted: '#8ea0b8', border: 'rgba(255,255,255,0.16)' }
            : { bg: '#ffffff', panel: '#f8fafc', text: '#172033', muted: '#64748b', border: 'rgba(15,23,42,0.14)' };
        const accent = (section && section.color) || '#3b82f6';
        const overlay = document.createElement('div');
        overlay.id = 'domain-topology-cleanup-prompt';
        overlay.style.cssText = 'position:fixed;inset:0;z-index:10005;display:flex;align-items:center;justify-content:center;background:rgba(2,6,23,0.50);backdrop-filter:blur(5px);';
        const safeSectionName = FileOps._escapeHtml(section.name || 'this domain');
        const rows = topologies.map((topo, idx) => {
            const filenameRaw = String(topo.filename || topo.name || '');
            const filename = FileOps._escapeHtml(filenameRaw);
            const name = FileOps._escapeHtml(topo.name || filename.replace(/\.json$/i, '') || 'Topology');
            const checked = isLimit && idx === topologies.length - 1 ? ' checked' : '';
            return `
                <label style="display:flex;gap:8px;align-items:center;padding:7px 8px;border-radius:8px;background:${t.panel};border:1px solid ${t.border};cursor:pointer;">
                    <input type="checkbox" value="${filename}"${checked} style="accent-color:${accent};">
                    <span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${name}</span>
                </label>`;
        }).join('');
        overlay.innerHTML = `
            <div role="dialog" aria-modal="true" aria-labelledby="domain-cleanup-title"
                 style="width:min(480px,calc(100vw - 32px));max-height:min(74vh,620px);display:flex;flex-direction:column;background:${t.bg};color:${t.text};border:1px solid ${t.border};border-radius:16px;box-shadow:0 18px 60px rgba(0,0,0,0.34);font-family:'Poppins',-apple-system,sans-serif;">
                <div style="padding:18px 18px 10px;border-bottom:1px solid ${t.border};">
                    <div id="domain-cleanup-title" style="font-size:16px;font-weight:800;">${isLimit ? 'Domain limit reached' : 'Clean domain topologies'}</div>
                    <div style="margin-top:6px;font-size:12px;line-height:1.45;color:${t.muted};">
                        ${isLimit
                            ? `This domain has ${topologies.length} topologies. The limit is ${limitDetail.limit || 15}. Select which topology files to delete, then the save will retry.`
                            : `Select topology files to delete from ${safeSectionName}. The domain itself is kept.`}
                    </div>
                </div>
                <div class="domain-cleanup-list" style="display:flex;flex-direction:column;gap:6px;overflow:auto;padding:12px 14px;min-height:120px;">
                    ${rows}
                </div>
                <div style="display:flex;gap:8px;align-items:center;justify-content:space-between;padding:12px 14px 14px;border-top:1px solid ${t.border};">
                    <button class="dc-select-all" type="button" style="padding:7px 10px;border-radius:9px;border:1px solid ${t.border};background:transparent;color:${t.text};font-size:12px;cursor:pointer;">Select all</button>
                    <div style="display:flex;gap:8px;">
                        <button class="dc-cancel" type="button" style="padding:8px 12px;border-radius:9px;border:1px solid ${t.border};background:transparent;color:${t.text};font-size:12px;cursor:pointer;">Cancel</button>
                        <button class="dc-delete" type="button" style="padding:8px 12px;border-radius:9px;border:1px solid #dc2626;background:#dc2626;color:#fff;font-size:12px;font-weight:700;cursor:pointer;">Delete selected</button>
                    </div>
                </div>
            </div>`;
        document.body.appendChild(overlay);
        return await new Promise(resolve => {
            const close = (result) => {
                document.removeEventListener('keydown', onKey, true);
                overlay.remove();
                resolve(result || null);
            };
            const onKey = (ev) => {
                if (ev.key === 'Escape') close(null);
            };
            document.addEventListener('keydown', onKey, true);
            overlay.addEventListener('click', (ev) => {
                if (ev.target === overlay) close(null);
            });
            overlay.querySelector('.dc-cancel').addEventListener('click', () => close(null));
            overlay.querySelector('.dc-select-all').addEventListener('click', () => {
                overlay.querySelectorAll('.domain-cleanup-list input[type="checkbox"]').forEach(cb => { cb.checked = true; });
            });
            overlay.querySelector('.dc-delete').addEventListener('click', async () => {
                const selected = Array.from(overlay.querySelectorAll('.domain-cleanup-list input[type="checkbox"]:checked'))
                    .map(cb => cb.value)
                    .filter(Boolean);
                if (!selected.length) {
                    editor.showToast('Select at least one topology to delete', 'warning');
                    return;
                }
                try {
                    const result = await FileOps._cleanupSectionTopologies(section.id, selected);
                    editor.showToast('Deleted ' + (result.deleted_count || selected.length) + ' topology file(s)', 'success');
                    if (container && container.isConnected) {
                        await FileOps._loadDomainTopologiesInline(editor, section, container);
                    }
                    close(result);
                } catch (err) {
                    editor.showToast('Cleanup failed: ' + (err.message || err), 'error');
                }
            });
        });
    },

    _normalizeTopologyFilename(filename) {
        let value = String(filename || '').trim();
        if (!value) return '';
        if (!value.toLowerCase().endsWith('.json')) value += '.json';
        return value.split('/').pop().split('\\').pop();
    },

    _getDomainDropTarget(editor, clientX, clientY, sourceSectionId) {
        const dropdown = document.getElementById('topologies-dropdown-menu') || document;
        const rows = Array.from(
            dropdown.querySelectorAll('.custom-section-category:not([data-shared-in="1"])')
        ).filter(secEl => {
            const secId = secEl && secEl.dataset ? secEl.dataset.sectionId : '';
            return secId && secId !== sourceSectionId;
        });
        const pointInRect = (rect) => !!rect
            && clientX >= rect.left && clientX <= rect.right
            && clientY >= rect.top && clientY <= rect.bottom;

        // Closed domains are represented only by their header. Prefer title
        // hits before expanded bodies so a long open domain above cannot steal
        // the drop target from the closed domain header the pointer is over.
        for (const secEl of rows) {
            const titleEl = secEl.querySelector('.domain-title');
            if (!titleEl) continue;
            if (pointInRect(titleEl.getBoundingClientRect())) {
                const bodyEl = secEl.querySelector('.domain-body');
                const bodyStyle = bodyEl ? window.getComputedStyle(bodyEl) : null;
                return {
                    element: secEl,
                    sectionId: secEl.dataset.sectionId,
                    isCollapsed: !bodyEl || bodyStyle.display === 'none'
                };
            }
        }

        for (const secEl of rows) {
            const bodyEl = secEl.querySelector('.domain-body');
            if (!bodyEl) continue;
            const bodyStyle = window.getComputedStyle(bodyEl);
            if (bodyStyle.display === 'none' || bodyStyle.visibility === 'hidden') continue;
            if (pointInRect(bodyEl.getBoundingClientRect())) {
                return {
                    element: secEl,
                    sectionId: secEl.dataset.sectionId,
                    isCollapsed: false
                };
            }
        }

        return null;
    },

    _topologyOrderFromDom(container, movingFilename) {
        if (!container) return null;
        const moving = FileOps._normalizeTopologyFilename(movingFilename);
        const out = [];
        let sawGhost = false;
        let sawRow = false;
        Array.from(container.children || []).forEach(child => {
            if (!child || !child.classList) return;
            if (child.classList.contains('drop-ghost')) {
                if (moving && !out.includes(moving)) out.push(moving);
                sawGhost = true;
                return;
            }
            if (!child.classList.contains('domain-topo-row')) return;
            const fname = FileOps._normalizeTopologyFilename(child.dataset.filename);
            if (fname && fname !== moving && !out.includes(fname)) out.push(fname);
            sawRow = true;
        });
        if (!sawGhost && !sawRow) return null;
        if (moving && !out.includes(moving)) out.push(moving);
        return out;
    },

    async _persistTopologyOrder(editor, sectionId, order) {
        if (!sectionId || !Array.isArray(order) || order.length === 0) return;
        const normalized = order
            .map(f => FileOps._normalizeTopologyFilename(f))
            .filter(Boolean);
        if (!normalized.length) return;
        const resp = await FileOps._authFetch(
            `/api/sections/${encodeURIComponent(sectionId)}/topologies/reorder`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order: normalized })
            }
        );
        if (!resp.ok) {
            throw new Error(`HTTP ${resp.status}`);
        }
    },

    _showRenameInput(editor, btn, color, container, opts) {
        const existing = container.querySelector('.rename-inline-form');
        if (existing) existing.remove();
        
        const filename = btn.dataset.filename;
        const currentName = btn.querySelector('.topo-entry-name')?.textContent?.trim() || '';
        
        const form = document.createElement('div');
        form.className = 'rename-inline-form';
        const isDark = FileOps._menuDark(editor);
        form.style.cssText = 'display:flex;gap:4px;align-items:center;padding:3px 12px 3px 20px;margin-left:8px;';
        form.innerHTML = `
            <input type="text" value="${currentName}" style="flex:1;padding:4px 6px;background:${isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.04)'};border:1px solid ${color}55;border-radius:4px;color:${isDark ? '#e2e8f0' : '#1e1e32'};font-size:10px;font-family:inherit;outline:none;" onclick="event.stopPropagation();">
            <button style="padding:3px 8px;background:${color};border:none;border-radius:4px;color:#fff;font-size:10px;font-weight:600;cursor:pointer;white-space:nowrap;">OK</button>
            <button style="padding:3px 6px;background:${isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)'};border:1px solid ${isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.12)'};border-radius:4px;color:${isDark ? '#94a3b8' : '#475569'};font-size:10px;cursor:pointer;">X</button>
        `;
        btn.after(form);
        const input = form.querySelector('input');
        const okBtn = form.querySelectorAll('button')[0];
        const cancelBtn = form.querySelectorAll('button')[1];
        input.focus(); input.select();
        
        const doRename = () => {
            const newName = input.value.trim();
            if (!newName || newName === currentName) { form.remove(); return; }
            if (opts.renameFn) opts.renameFn(filename, newName);
            form.remove();
        };
        okBtn.onclick = (e) => { e.stopPropagation(); doRename(); };
        cancelBtn.onclick = (e) => { e.stopPropagation(); form.remove(); };
        input.addEventListener('keydown', (e) => { e.stopPropagation(); if (e.key === 'Enter') doRename(); if (e.key === 'Escape') form.remove(); });
    },

    _showDuplicatePicker(editor, row, srcSectionId, container, opts) {
        const existing = document.getElementById('duplicate-picker-popup');
        if (existing) existing.remove();

        const filename = row.dataset.filename;
        const topoName = (row.querySelector('.topo-entry-name')?.textContent?.trim() || filename).replace(/\.json$/i, '');
        const sections = editor._customSections || [];
        const isDark = FileOps._menuDark(editor);

        const rowRect = row.getBoundingClientRect();
        const popup = document.createElement('div');
        popup.id = 'duplicate-picker-popup';
        popup.style.cssText = `
            position: fixed;
            left: ${rowRect.right + 6}px;
            top: ${rowRect.top}px;
            z-index: 100002;
            min-width: 180px;
            background: ${isDark
                ? 'linear-gradient(135deg, rgba(20,25,40,0.95), rgba(15,20,35,0.98))'
                : 'linear-gradient(135deg, rgba(255,255,255,0.98), rgba(245,248,255,0.95))'};
            border: 1px solid ${isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)'};
            border-radius: 10px;
            padding: 6px;
            box-shadow: ${isDark
                ? '0 8px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.08)'
                : '0 8px 32px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.8)'};
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            font-family: 'Poppins', -apple-system, sans-serif;
        `;

        const titleEl = document.createElement('div');
        titleEl.textContent = 'Duplicate to...';
        titleEl.style.cssText = `font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.6px;color:${isDark ? 'rgba(255,255,255,0.45)' : 'rgba(0,0,0,0.4)'};padding:4px 8px 6px;`;
        popup.appendChild(titleEl);

        const doDuplicate = async (targetSectionId, targetName) => {
            popup.remove();
            try {
                const [topoResp, listResp] = await Promise.all([
                    fetch(`/api/sections/${srcSectionId}/topologies/${filename}`),
                    fetch(`/api/sections/${targetSectionId}/topologies`)
                ]);
                const topoData = await topoResp.json();
                if (topoData.error) { editor.showToast(topoData.error, 'error'); return; }
                const listData = await listResp.json();
                const existingNames = new Set((listData.topologies || []).map(t => (t.name || '').toLowerCase()));

                let copyName = topoName + '_copy';
                let n = 2;
                while (existingNames.has(copyName.toLowerCase())) {
                    copyName = topoName + '_copy' + n;
                    n++;
                }

                const result = await FileOps._sectionSaveWithConflict(
                    editor,
                    targetSectionId,
                    { name: copyName, topology: topoData },
                    null,
                );
                if (result && (result.error || result.conflict || result.quota)) return;

                editor.showToast(`Duplicated → ${targetName}/${copyName}`, 'success');

                const targetCtr = document.querySelector(`.custom-section-category[data-section-id="${targetSectionId}"] .domain-topos-list`);
                const targetSec = sections.find(s => s.id === targetSectionId);
                if (targetCtr && targetSec) await FileOps._loadDomainTopologiesInline(editor, targetSec, targetCtr);
                if (targetSectionId !== srcSectionId && container) {
                    const srcSec = sections.find(s => s.id === srcSectionId);
                    if (srcSec) await FileOps._loadDomainTopologiesInline(editor, srcSec, container);
                }
            } catch (err) {
                editor.showToast('Duplicate failed: ' + err.message, 'error');
            }
        };

        const createOption = (label, color, onClick) => {
            const btn = document.createElement('button');
            btn.style.cssText = `
                display: flex; align-items: center; gap: 8px; width: 100%;
                padding: 6px 10px; border: none; border-radius: 6px; cursor: pointer;
                background: transparent; color: ${isDark ? '#e2e8f0' : '#1e1e32'};
                font-size: 11px; font-family: inherit; text-align: left;
                transition: background 0.12s;
            `;
            const dot = document.createElement('span');
            dot.style.cssText = `width:8px;height:8px;border-radius:50%;background:${color};flex-shrink:0;`;
            const text = document.createElement('span');
            text.textContent = label;
            text.style.cssText = 'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;';
            btn.appendChild(dot);
            btn.appendChild(text);
            btn.onmouseenter = () => { btn.style.background = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)'; };
            btn.onmouseleave = () => { btn.style.background = 'transparent'; };
            btn.onclick = (e) => { e.stopPropagation(); onClick(); };
            return btn;
        };

        const srcSec = sections.find(s => s.id === srcSectionId);
        if (srcSec) {
            const sameBtn = createOption(`${srcSec.name} (same)`, srcSec.color || '#3b82f6', () => doDuplicate(srcSectionId, srcSec.name));
            popup.appendChild(sameBtn);
        }

        const otherSections = sections.filter(s => s.id !== srcSectionId);
        if (otherSections.length > 0 && srcSec) {
            const sep = document.createElement('div');
            sep.style.cssText = `height:1px;background:${isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)'};margin:4px 6px;`;
            popup.appendChild(sep);
        }
        otherSections.forEach(sec => {
            popup.appendChild(createOption(sec.name, sec.color || '#3b82f6', () => doDuplicate(sec.id, sec.name)));
        });

        popup.addEventListener('mousedown', (e) => e.stopPropagation());
        popup.addEventListener('click', (e) => e.stopPropagation());

        document.body.appendChild(popup);

        requestAnimationFrame(() => {
            const pr = popup.getBoundingClientRect();
            if (pr.right > window.innerWidth - 8) popup.style.left = `${rowRect.left - pr.width - 6}px`;
            if (pr.bottom > window.innerHeight - 8) popup.style.top = `${window.innerHeight - pr.height - 8}px`;
        });

        const closePicker = (e) => {
            if (!popup.contains(e.target)) { popup.remove(); document.removeEventListener('mousedown', closePicker); }
        };
        setTimeout(() => document.addEventListener('mousedown', closePicker), 50);
    },

    _updateTopoBtnIcon(editor) {
        const svg = document.getElementById('topo-btn-icon');
        if (!svg) return;
        // Respect the persisted manual domain order. A prior hue-sort pass
        // made drag reorder appear to work during the gesture, then snap
        // back on the next render.
        const sections = editor._customSections || [];
        // Mirror the dropdown's hide-__ai rule so the legacy AI domain
        // never steals one of the 4 visible layer slots. (__bugs still
        // counts -- we want the bug pill to show in the icon stack.)
        //
        // Shared-with-me content is not part of /api/sections; it is a
        // virtual dropdown section backed by the domain sharing cache.
        // Add one purple layer when there is any shared-in domain or
        // per-file inbox content so the Topologies button still reflects
        // that visible layer.
        const visibleSections = sections.filter(s => s && s.id !== '__ai');
        try {
            const domains = (FileOps._sharingCache && FileOps._sharingCache.domains) || [];
            const hasSharedInLayer = domains.some(d => d && (
                (d.is_shared && !d.is_shared_with_me_domain)
                || (d.is_shared_with_me_domain && d.topology_count)
            ));
            if (hasSharedInLayer) {
                visibleSections.push({
                    id: '__shared_with_me_visual',
                    name: 'Shared with me',
                    color: '#a78bfa',
                });
            }
        } catch (_) {}
        const colors = visibleSections.map(s => s.color).filter(Boolean);
        const n = Math.min(colors.length, 4);

        if (n === 0) {
            svg.innerHTML = `
                <polygon points="12 2 2 7 12 12 22 7 12 2" stroke="currentColor" fill="none" stroke-width="1.8"/>
                <polyline points="2 12 12 17 22 12" stroke="currentColor" fill="none" stroke-width="1.8"/>
                <polyline points="2 17 12 22 22 17" stroke="currentColor" fill="none" stroke-width="1.8"/>`;
            return;
        }

        // Build layers bottom-up: each domain gets its own layer
        // Vertical space: viewBox 0-24, usable ~2-22
        // Top layer is always a filled polygon, rest are polylines
        const layers = colors.slice(0, 4);
        let inner = '';

        if (n === 1) {
            inner = `<polygon points="12 4 2 10 12 16 22 10 12 4" stroke="${layers[0]}" fill="${layers[0]}30" stroke-width="1.8"/>`;
        } else if (n === 2) {
            inner = `
                <polygon points="12 2 2 8 12 14 22 8 12 2" stroke="${layers[0]}" fill="${layers[0]}30" stroke-width="1.8"/>
                <polyline points="2 14 12 20 22 14" stroke="${layers[1]}" fill="none" stroke-width="1.8"/>`;
        } else if (n === 3) {
            inner = `
                <polygon points="12 2 2 7 12 12 22 7 12 2" stroke="${layers[0]}" fill="${layers[0]}30" stroke-width="1.8"/>
                <polyline points="2 12 12 17 22 12" stroke="${layers[1]}" fill="none" stroke-width="1.8"/>
                <polyline points="2 17 12 22 22 17" stroke="${layers[2]}" fill="none" stroke-width="1.8"/>`;
        } else {
            inner = `
                <polygon points="12 1 2 5.5 12 10 22 5.5 12 1" stroke="${layers[0]}" fill="${layers[0]}30" stroke-width="1.6"/>
                <polyline points="2 10 12 14.5 22 10" stroke="${layers[1]}" fill="none" stroke-width="1.6"/>
                <polyline points="2 14.5 12 19 22 14.5" stroke="${layers[2]}" fill="none" stroke-width="1.6"/>
                <polyline points="2 19 12 23.5 22 19" stroke="${layers[3]}" fill="none" stroke-width="1.6"/>`;
        }

        svg.innerHTML = inner;
    },

    // ========================================================================
    // CUSTOM TOPOLOGY SECTIONS
    // ========================================================================

    // The Topologies dropdown and most surfaces it launches (New Topology
    // picker, domain pickers, inline rename form, duplicate picker, hover
    // tooltips on menu items) render with the OPPOSITE theme to the body
    // on purpose. **Exception (ui-skin-v2):** Manage Topology Domains uses
    // `_topologyChromeDark` so it matches the app light/dark toggle.
    // Dark body -> light menus, light body -> dark menus. This keeps
    // the popover chrome visually distinct from the canvas behind it
    // regardless of which mode the user is running. Every render path
    // that used to call `document.body.classList.contains('dark-mode')`
    // or `editor.darkMode` for Topologies-menu styling funnels through
    // this helper so the inversion is applied in exactly one place.
    _menuDark(editor) {
        try {
            if (editor && typeof editor.darkMode === 'boolean') return !editor.darkMode;
        } catch (_) {}
        return !document.body.classList.contains('dark-mode');
    },

    /** Dark-styled chrome for Topology panels: matches app theme under ui-skin-v2. */
    _topologyChromeDark(editor) {
        try {
            if (document.body && document.body.classList.contains('ui-skin-v2')) {
                if (editor && typeof editor.darkMode === 'boolean') return !!editor.darkMode;
                return document.body.classList.contains('dark-mode');
            }
        } catch (_) {}
        return FileOps._menuDark(editor);
    },

    /** Re-render Manage Topology Domains if open (e.g. after light/dark toggle). */
    _refreshManageSectionsForTheme(editor) {
        const msp = document.getElementById('manage-sections-panel');
        if (msp && typeof msp._msThemeRefresh === 'function') {
            try {
                msp._msThemeRefresh();
            } catch (_) {}
        }
    },

    // Grows the Topologies dropdown to fit its widest visible content.
    //
    // 2026-04-24g rewrite -- the previous `child.scrollWidth` approach was
    // broken in practice. For a flex item that carries
    //     flex: 1 1 auto; min-width: 0; overflow: hidden
    // (which is exactly how `.topo-entry-name` is styled), `scrollWidth`
    // returns the *allocated* width after flex distribution, not the
    // intrinsic text width. Once the span was clipped by ellipsis the
    // measurement saw the clipped size and happily reported "we fit",
    // so the dropdown never grew for long filenames -- which is exactly
    // what the user was seeing (topology full names ellipsized even when
    // there was lots of viewport room).
    //
    // The fix: measure the name span's text width with a shared 2D
    // canvas context that mirrors the span's computed font, then add the
    // widths of its flex siblings (icon / shared badge / time pill /
    // action icons) and the row padding. That number is the row's true
    // intrinsic width regardless of flex distribution.
    //
    // Capped at `min(1200, viewport - 20)` so outlier filenames still
    // ellipsize instead of blowing out the screen.
    _fitDropdownToContent() {
        const dropdown = document.getElementById('topologies-dropdown-menu');
        if (!dropdown) return;
        if (dropdown.style.display === 'none') return;

        // Lazily-initialised shared measurement canvas. Cheaper than
        // creating a throwaway one per row, and the 2D context's
        // `measureText()` is exact and framework-free (no DOM reflow).
        if (!FileOps._textMeasureCtx) {
            try {
                const c = document.createElement('canvas');
                FileOps._textMeasureCtx = c.getContext('2d');
            } catch (_) { FileOps._textMeasureCtx = null; }
        }
        const measureText = (text, fontShorthand) => {
            if (!text) return 0;
            const ctx = FileOps._textMeasureCtx;
            if (!ctx) return 0;
            ctx.font = fontShorthand || '11px Poppins, -apple-system, sans-serif';
            const m = ctx.measureText(text);
            // `actualBoundingBoxLeft/Right` is more accurate for italic /
            // fancy glyphs but isn't universally reported; fall back to
            // `width` which is always defined. Pad +2 to forgive sub-pixel
            // hinting differences between canvas and DOM render.
            const w = Math.max(m.width || 0,
                (m.actualBoundingBoxLeft || 0) + (m.actualBoundingBoxRight || 0));
            return Math.ceil(w) + 2;
        };

        let widestRow = 0;
        const rows = dropdown.querySelectorAll('.domain-topo-row');
        rows.forEach(row => {
            // offsetParent === null -> ancestor has display:none (collapsed
            // domain body). Skip; its children report bogus zero widths.
            if (row.offsetParent === null) {
                return;
            }
            let total = 0;
            for (const child of row.children) {
                const cs = getComputedStyle(child);
                const ml = parseFloat(cs.marginLeft) || 0;
                const mr = parseFloat(cs.marginRight) || 0;
                let w;
                if (child.classList && child.classList.contains('topo-entry-name')) {
                    // True intrinsic text width via canvas. The span's
                    // computed font matches the row row as long as we
                    // read it back from getComputedStyle, which picks
                    // up the font-family inherited from <body> and the
                    // explicit font-size on the span's inline style.
                    const font = cs.font
                        || [cs.fontStyle, cs.fontVariant, cs.fontWeight, cs.fontSize, cs.fontFamily]
                            .filter(Boolean).join(' ').trim();
                    w = measureText(child.textContent || '', font);
                    // Falls back to the old approach if canvas came up
                    // empty (privacy add-ons can null the canvas 2D API).
                    if (!w) w = Math.max(child.scrollWidth, child.offsetWidth);
                } else {
                    // Non-text children (icons, badges, time pill, action
                    // buttons) usually report their real layout width via
                    // offsetWidth. SVG elements, however, do not expose
                    // scrollWidth in all browsers; passing undefined into
                    // Math.max() turns the whole row total into NaN, which
                    // prevents the dropdown from ever widening.
                    const rectW = (child.getBoundingClientRect && child.getBoundingClientRect().width) || 0;
                    w = Math.max(child.offsetWidth || 0, child.scrollWidth || 0, rectW);
                }
                total += w + ml + mr;
            }
            const rowCs = getComputedStyle(row);
            total += (parseFloat(rowCs.paddingLeft) || 0)
                   + (parseFloat(rowCs.paddingRight) || 0)
                   + (parseFloat(rowCs.marginLeft) || 0)
                   + (parseFloat(rowCs.marginRight) || 0);
            if (total > widestRow) widestRow = total;
        });

        // Chrome = dropdown's own border + the 4px accent stripe on each
        // `.custom-section-category` + a 12px breathing buffer so the
        // longest topology name never visually crowds the right-side
        // hover-actions icons.
        const chrome = 20;

        // Grow to the viewport edge minus a 20px safety margin, with a
        // soft 1200px hard-cap so a single absurdly long filename can't
        // blow the dropdown to fill the whole screen.
        const minW = 300;
        const maxW = Math.max(minW, Math.min(1200, window.innerWidth - 20));
        const needed = widestRow > 0 ? Math.ceil(widestRow + chrome) : minW;
        // Keep the panel visually stable while it is open. Expanding/collapsing
        // domains changes `widestRow`; shrinking the dropdown on every toggle
        // reads as a layout bug. Grow when needed, clamp to viewport, but do not
        // shrink until the viewport itself requires it.
        const previousStable = parseFloat(dropdown.dataset.stableWidth || dropdown.style.width) || minW;
        const target = Math.max(minW, Math.min(Math.max(needed, previousStable), maxW));

        dropdown.dataset.stableWidth = String(target);
        dropdown.style.width = target + 'px';
    },

    // Keep the Topologies dropdown from spilling over the left toolbar
    // sidebar. Every site that places the dropdown uses
    // `btn-topologies.getBoundingClientRect().left` as the anchor -- fine
    // normally, but on narrow viewports (or when the top-bar padding
    // isn't enough) the button's left edge can fall inside the 200px
    // sidebar, making the dropdown visually eat into the toolbar.
    //
    // Pass the proposed `leftPx`; we'll return a value clamped to the
    // toolbar's right edge + a small gap when the sidebar is actually
    // visible on the left. Callers stay simple and don't have to reach
    // into the DOM to know about the sidebar.
    _clampDropdownLeft(leftPx) {
        try {
            const tb = document.querySelector('.toolbar');
            if (!tb) return leftPx;
            const r = tb.getBoundingClientRect();
            // Collapsed / hidden toolbar -- nothing to avoid.
            if (r.width < 20) return leftPx;
            // Toolbar not docked to the left edge (e.g. RTL or detached
            // layouts we haven't thought of). Leave the caller's value
            // alone instead of producing a surprising jump.
            if (r.left > 10) return leftPx;
            const minLeft = Math.round(r.right + 6);
            return Math.max(leftPx, minLeft);
        } catch (_) {
            return leftPx;
        }
    },

    _sectionIcons() {
        // All icons are drawn with `stroke="currentColor"` + `stroke-width="2"`
        // so CSS can re-tint them on the fly. The rendering layer (topology
        // row title, accordion grid) additionally applies a drop-shadow +
        // bumped stroke-width via `.domain-row-icon` so they read as "bold
        // outlined" the same way the domain title text does.
        return [
            { id: 'folder',    svg: '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'server',    svg: '<rect x="2" y="2" width="20" height="8" rx="2" stroke="currentColor" stroke-width="2" fill="none"/><rect x="2" y="14" width="20" height="8" rx="2" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="6" cy="6" r="1" fill="currentColor"/><circle cx="6" cy="18" r="1" fill="currentColor"/>' },
            { id: 'globe',     svg: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10A15.3 15.3 0 0 1 12 2z" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'lab',       svg: '<path d="M9 3h6M12 3v7l5 8H7l5-8V3" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>' },
            { id: 'shield',    svg: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'zap',       svg: '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'layers',    svg: '<polygon points="12 2 2 7 12 12 22 7" stroke="currentColor" stroke-width="2" fill="none"/><polyline points="2 17 12 22 22 17" stroke="currentColor" stroke-width="2" fill="none"/><polyline points="2 12 12 17 22 12" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'cpu',       svg: '<rect x="4" y="4" width="16" height="16" rx="2" stroke="currentColor" stroke-width="2" fill="none"/><rect x="9" y="9" width="6" height="6" stroke="currentColor" stroke-width="2" fill="none"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3" stroke="currentColor" stroke-width="2"/>' },
            { id: 'wifi',      svg: '<path d="M5 12.55a11 11 0 0 1 14.08 0M1.42 9a16 16 0 0 1 21.16 0M8.53 16.11a6 6 0 0 1 6.95 0M12 20h.01" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>' },
            { id: 'star',      svg: '<polygon points="12,2 15,9 22,9 17,14 19,21 12,17 5,21 7,14 2,9 9,9" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'network',   svg: '<circle cx="6" cy="12" r="3" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="18" cy="6" r="3" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="18" cy="18" r="3" stroke="currentColor" stroke-width="2" fill="none"/><path d="M9 12h6M15 8l-6 4M15 16l-6-4" stroke="currentColor" stroke-width="2"/>' },
            { id: 'box',       svg: '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" stroke="currentColor" stroke-width="2" fill="none"/><polyline points="3.27 6.96 12 12.01 20.73 6.96" stroke="currentColor" stroke-width="2" fill="none"/><line x1="12" y1="22.08" x2="12" y2="12" stroke="currentColor" stroke-width="2"/>' },
            { id: 'tool',      svg: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'link',      svg: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" stroke="currentColor" stroke-width="2" fill="none"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'cloud',     svg: '<path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'lock',      svg: '<rect x="3" y="11" width="18" height="11" rx="2" stroke="currentColor" stroke-width="2" fill="none"/><path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'alert',     svg: '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="currentColor" stroke-width="2" fill="none"/><line x1="12" y1="9" x2="12" y2="13" stroke="currentColor" stroke-width="2"/><line x1="12" y1="17" x2="12.01" y2="17" stroke="currentColor" stroke-width="2"/>' },
            { id: 'bug',       svg: '<path d="M8 2l1.88 1.88M16 2l-1.88 1.88M9 7.13v-1a3.003 3.003 0 1 1 6 0v1" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/><path d="M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6z" stroke="currentColor" stroke-width="2" fill="none"/><path d="M12 20v-9M6.53 9C4.6 8.8 3 7.1 3 5M17.47 9c1.93-.2 3.53-1.9 3.53-4M6 13H2M22 13h-4M6 17H2M22 17h-4" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>' },
            { id: 'share',     svg: '<circle cx="18" cy="5" r="3" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="6" cy="12" r="3" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="18" cy="19" r="3" stroke="currentColor" stroke-width="2" fill="none"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49" stroke="currentColor" stroke-width="2"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49" stroke="currentColor" stroke-width="2"/>' },
            { id: 'git-branch',svg: '<line x1="6" y1="3" x2="6" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="18" cy="6" r="3" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="6" cy="18" r="3" stroke="currentColor" stroke-width="2" fill="none"/><path d="M18 9a9 9 0 0 1-9 9" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'activity',  svg: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>' },
            { id: 'terminal',  svg: '<polyline points="4 17 10 11 4 5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/><line x1="12" y1="19" x2="20" y2="19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' },
            { id: 'code',      svg: '<polyline points="16 18 22 12 16 6" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/><polyline points="8 6 2 12 8 18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>' },
            { id: 'database',  svg: '<ellipse cx="12" cy="5" rx="9" ry="3" stroke="currentColor" stroke-width="2" fill="none"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" stroke="currentColor" stroke-width="2" fill="none"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'book',      svg: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V2H6.5A2.5 2.5 0 0 0 4 4.5v15z" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/><path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5H6.5A2.5 2.5 0 0 0 4 19.5z" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>' },
            { id: 'flag',      svg: '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/><line x1="4" y1="22" x2="4" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' },
            { id: 'users',     svg: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="2" fill="none"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'target',    svg: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="12" cy="12" r="6" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="12" cy="12" r="2" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'compass',   svg: '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>' },
            { id: 'beaker',    svg: '<path d="M9 3h6v5l4 10a2 2 0 0 1-1.85 2.75H6.85A2 2 0 0 1 5 18l4-10V3z" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/><line x1="9" y1="3" x2="15" y2="3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M7 14h10" stroke="currentColor" stroke-width="2"/>' },
            { id: 'sparkles',  svg: '<path d="M12 3l1.88 4.66L18.5 9.5l-4.66 1.88L12 16l-1.88-4.62L5.5 9.5l4.62-1.84z" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/><path d="M19 15l.95 2.36L22.5 18l-2.55.66L19 21l-.95-2.34L15.5 18l2.55-.64z" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>' },
            { id: 'chart',     svg: '<polyline points="3 17 9 11 13 15 21 7" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/><polyline points="14 7 21 7 21 14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>' },
            { id: 'workflow',  svg: '<rect x="3" y="3" width="6" height="6" rx="1" stroke="currentColor" stroke-width="2" fill="none"/><rect x="15" y="3" width="6" height="6" rx="1" stroke="currentColor" stroke-width="2" fill="none"/><rect x="9" y="15" width="6" height="6" rx="1" stroke="currentColor" stroke-width="2" fill="none"/><path d="M6 9v1a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V9M12 12v3" stroke="currentColor" stroke-width="2" fill="none"/>' },
            { id: 'rocket',    svg: '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>' },
            { id: 'diamond',   svg: '<path d="M2.7 10.3L12 22l9.3-11.7a1 1 0 0 0 0-1.23L17.66 3.5a1 1 0 0 0-.79-.38H7.13a1 1 0 0 0-.79.38L2.7 9.07a1 1 0 0 0 0 1.23z" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/><path d="M2.7 10h18.6M12 22V3.12M7 3.12L12 10l-5 0M17 3.12L12 10l5 0" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>' },
            { id: 'hexagon',   svg: '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>' },
        ];
    },

    _sectionColors() {
        // Organized as rows of 6 for a grid layout. Palette covers:
        //   Row 1 -- classic brand primaries (blue/green/amber/red/violet/pink)
        //   Row 2 -- cyan + DriveNets orange + teal/indigo + rose/lime brights
        //   Row 3 -- deep, saturated accents (navy/forest/burgundy/plum/slate)
        //   Row 4 -- soft pastels + neutral greys for quieter domains
        //   Row 5 -- neon / electric shades for "hero" domains
        //   Row 6 -- earth tones + warm accents
        return [
            // Row 1 -- originals (keep first so existing domains don't remap)
            '#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899',
            // Row 2 -- originals cont.
            '#06b6d4', '#FF5E1F', '#14b8a6', '#6366f1', '#f472b6', '#a3e635',
            // Row 3 -- deep / saturated
            '#1e3a8a', '#0f766e', '#7f1d1d', '#581c87', '#334155', '#78350f',
            // Row 4 -- pastel / muted
            '#93c5fd', '#86efac', '#fde68a', '#fca5a5', '#c4b5fd', '#f9a8d4',
            // Row 5 -- neon / electric
            '#00d4ff', '#00ff88', '#ffee00', '#ff3860', '#d946ef', '#0ea5e9',
            // Row 6 -- earth / warm
            '#a16207', '#84cc16', '#dc2626', '#7c3aed', '#0891b2', '#be185d',
        ];
    },

    // --------------------------------------------------------------------------
    // Hue-based ordering for the Topologies dropdown
    // --------------------------------------------------------------------------
    // The user asked domains to be rendered in "color order" -- i.e. the pills
    // arranged along the visible spectrum (red -> orange -> yellow -> green ->
    // cyan -> blue -> purple -> magenta) regardless of creation order or any
    // previous drag-to-reorder choices. We compute the hue angle from each
    // section's accent hex and sort ascending by that. Low-saturation colors
    // (grays) fall to the end ordered by lightness; identically-hued domains
    // tie-break on name so the sort is stable and visually predictable.
    //
    // We only sort the DISPLAY. `editor._customSections` stays in whatever
    // order `/api/sections` returned, so drag-to-reorder still writes to
    // disk -- it just gets visually overridden by the spectrum sort on the
    // next render (which is exactly the behaviour the user asked for: "make
    // layers according to the color of the domain in the correct order").
    _hexToHsl(hex) {
        let h = String(hex == null ? '' : hex).trim().replace('#', '');
        if (h.length === 3) h = h.split('').map(c => c + c).join('');
        if (h.length !== 6 || /[^0-9a-fA-F]/.test(h)) return [0, 0, 0];
        const r = parseInt(h.slice(0, 2), 16) / 255;
        const g = parseInt(h.slice(2, 4), 16) / 255;
        const b = parseInt(h.slice(4, 6), 16) / 255;
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        const l = (max + min) / 2;
        let s = 0, hue = 0;
        if (max !== min) {
            const d = max - min;
            s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
            if (max === r)      hue = ((g - b) / d) + (g < b ? 6 : 0);
            else if (max === g) hue = ((b - r) / d) + 2;
            else                hue = ((r - g) / d) + 4;
            hue *= 60;
        }
        return [hue, s, l];
    },

    _sortSectionsByHue(sections) {
        // Sort spectrum-ascending on a COPY so we never mutate the caller.
        // Thresholds:
        //   - saturation < 0.12 -> treated as "gray", bucketed to the end.
        //     0.12 is chosen so muted pastels (#93c5fd ~ 0.95 sat, #fca5a5
        //     ~ 0.95 sat) still count as colored; only near-gray swatches
        //     like #334155 (slate) drop into the gray bucket.
        //   - Tie-break within a hue by lightness (darker first) then
        //     alphabetical name, so same-hue families read as a stable
        //     gradient instead of a random shuffle.
        const sections_copy = Array.isArray(sections) ? sections.slice() : [];
        return sections_copy.sort((a, b) => {
            const color_a = (a && a.color) || '#3b82f6';
            const color_b = (b && b.color) || '#3b82f6';
            const [ha, sa, la] = FileOps._hexToHsl(color_a);
            const [hb, sb, lb] = FileOps._hexToHsl(color_b);
            const gray_a = sa < 0.12;
            const gray_b = sb < 0.12;
            if (gray_a !== gray_b) return gray_a ? 1 : -1;
            if (!gray_a && !gray_b) {
                if (Math.abs(ha - hb) > 1e-3) return ha - hb;
            }
            if (Math.abs(la - lb) > 1e-3) return la - lb;
            const name_a = (a && a.name) || '';
            const name_b = (b && b.name) || '';
            return name_a.localeCompare(name_b);
        });
    },

    async loadCustomSections(editor) {
        if (window.TopologyAuth && typeof window.TopologyAuth.isAuthenticated === 'function'
            && !window.TopologyAuth.isAuthenticated()) {
            editor._customSections = editor._customSections || [];
            return;
        }
        try {
            const resp = await FileOps._authFetch('/api/sections');
            if (!resp.ok) throw new Error('sections unavailable');
            const data = await resp.json();
            editor._customSections = data.sections || [];
            await FileOps._refreshSharingCache().catch(() => {});
            FileOps._renderCustomSectionsInDropdown(editor);
            FileOps._updateTopoBtnIcon(editor);
        } catch (err) {
            editor._customSections = editor._customSections || [];
            if (editor.showToast) {
                editor.showToast('Topology domains temporarily unavailable; keeping the last known list.', 'warning');
            }
        }
    },

    // Shared state cache used to decorate domain + topology rows with
    // "shared-out" / "shared-in" badges. Pulled from window.TopologyDomains
    // (domain-level sharing) + /api/domains/share/files/* (per-file sharing).
    // TTL is short (30s) so freshly-revoked shares drop off without a reload.
    _sharingCache: { lastFetched: 0, outgoingFiles: [], incomingFiles: [] },
    _SHARING_CACHE_TTL_MS: 30 * 1000,

    async _refreshSharingCache(forceFresh) {
        const now = Date.now();
        if (!forceFresh && (now - FileOps._sharingCache.lastFetched) < FileOps._SHARING_CACHE_TTL_MS) {
            return FileOps._sharingCache;
        }
        try {
            const domainsP = (window.TopologyDomains && window.TopologyDomains.fetchDomains)
                ? window.TopologyDomains.fetchDomains() : Promise.resolve([]);
            const outP = (window.TopologyDomains && window.TopologyDomains.fetchOutgoingFileShares)
                ? window.TopologyDomains.fetchOutgoingFileShares() : Promise.resolve([]);
            const inP = (window.TopologyDomains && window.TopologyDomains.fetchIncomingFileShares)
                ? window.TopologyDomains.fetchIncomingFileShares() : Promise.resolve([]);
            const [domains, out, inc] = await Promise.all([domainsP, outP, inP]);
            FileOps._sharingCache = {
                lastFetched: now,
                domains: Array.isArray(domains) ? domains : [],
                outgoingFiles: Array.isArray(out) ? out : [],
                incomingFiles: Array.isArray(inc) ? inc : []
            };
        } catch (_) {
            // Keep the old cache; the absence of share info just means the
            // icon won't render -- better than blowing up the dropdown.
        }
        return FileOps._sharingCache;
    },

    // Legacy /api/sections save path sanitizes display names into
    // filenames with `[^A-Za-z0-9\-_]` -> `_`. The user_store stores the
    // original name, so to bridge the two we normalize both sides with the
    // same transform whenever we look files up by name.
    _sanitizeTopologyBasename(name) {
        return String(name || '').replace(/[^a-zA-Z0-9\-_]/g, '_');
    },

    // Build an in-memory index of sharing state keyed by domain name/id so
    // the render loop below can look each section up in O(1) without
    // reissuing HTTP calls for every row.
    _buildSharingIndex() {
        const byName = {};
        const byId = {};
        const domains = (window.TopologyDomains && window.TopologyDomains.getDomains)
            ? (window.TopologyDomains.getDomains() || []) : [];
        for (const d of domains) {
            const lc = String(d.name || '').toLowerCase();
            if (lc) byName[lc] = d;
            if (d.id) byId[d.id] = d;
        }
        // Per-file OUTGOING shares: keyed as `<domain_id>|<sanitized_basename>`
        // so callers can match using either the raw name from /api/domains or
        // the legacy filename from /api/sections (both converge after the
        // sanitization we do here).
        const outByKey = {};
        (FileOps._sharingCache.outgoingFiles || []).forEach(f => {
            if (!f || !f.domain_id) return;
            const sanitized = FileOps._sanitizeTopologyBasename(f.name || '');
            outByKey[f.domain_id + '|' + sanitized] = f;
        });
        // Per-file INCOMING shares: keyed by topology_id and composite_id
        // so the synthetic inbox row can render one row per share with
        // owner attribution.
        const incomingByTopoId = {};
        (FileOps._sharingCache.incomingFiles || []).forEach(f => {
            if (!f) return;
            if (f.id) incomingByTopoId[f.id] = f;
            if (f.composite_id) incomingByTopoId[f.composite_id] = f;
        });
        return {
            domains: domains,
            domainsByName: byName,
            domainsById: byId,
            outgoingFilesByKey: outByKey,
            incomingFiles: FileOps._sharingCache.incomingFiles || [],
            incomingFilesByTopoId: incomingByTopoId
        };
    },

    // Resolve the owning domain (if any) for a legacy `sec`, matched by
    // name (case-insensitive). Legacy /api/sections rows don't carry an
    // id that maps to the user_store domain id, but the share dialog has
    // always looked up by name -- we follow the same convention.
    _findOwnDomainForSection(sec, sharingIndex) {
        if (!sec || !sharingIndex) return null;
        const lc = String(sec.name || '').toLowerCase();
        if (!lc) return null;
        const d = sharingIndex.domainsByName[lc];
        // Only count OWN domains here; shared-in copies get a different
        // rendering path (virtual rows).
        if (d && !d.is_shared && !d.is_shared_with_me_domain) return d;
        return null;
    },

    // Legacy `/api/sections` and multi-user `/api/domains` are two parallel
    // stores. The sharing pipeline lives ONLY in the multi-user store, so
    // a legacy file that was never saved via a domain 404s on share with
    // "Topology not found". This helper makes the share flow transparent:
    //
    //   1. Find (or create) a multi-user domain whose name matches the
    //      legacy section name -- sanitize matching is case-insensitive.
    //   2. Look for an existing multi-user topology with the same name;
    //      if present, return it (we've already migrated this file).
    //   3. Otherwise read the legacy JSON from /api/sections and POST it
    //      to /api/domains/{did}/topologies so the backend assigns it a
    //      real UUID that share_topology can dereference.
    //
    // Returns { domain, topology, created } so callers can keep the
    // legacy dropdown row in sync (e.g. cache the multi-user id for
    // future mirror-on-save writes).
    async _ensureLegacyTopologyMigrated(editor, sectionId, section, topoFilename) {
        const topoName = String(topoFilename || '').replace(/\.json$/i, '');
        if (!topoName) throw new Error('Missing topology name');

        const sectionName = (section && section.name) || sectionId;
        if (!sectionName) throw new Error('Missing section name');

        if (!window.TopologyDomains || !window.TopologyDomains.fetchDomains) {
            throw new Error('Multi-user sharing not initialised');
        }

        // Refresh domains so we see the latest state (new user, freshly
        // created domain, ...). Returns the cached list on failure so we
        // don't lose access to already-fetched domains if the network
        // hiccups.
        try { await window.TopologyDomains.fetchDomains(); } catch (_) {}
        let domains = window.TopologyDomains.getDomains() || [];

        const sectionNameLc = String(sectionName).toLowerCase();
        let domain = domains.find(d => d && !d.is_shared && !d.is_shared_with_me_domain
            && String(d.name || '').toLowerCase() === sectionNameLc);

        if (!domain) {
            // Mirror the legacy section into a brand-new multi-user domain
            // before migrating the file. Safe if two users happen to have
            // identically-named legacy sections because each user's
            // domains live in their own DB.
            if (!window.TopologyDomains.createDomain) {
                throw new Error('Cannot create a multi-user domain in this build');
            }
            domain = await window.TopologyDomains.createDomain(
                sectionName,
                'Mirrored from legacy section for sharing'
            );
            // Re-fetch so subsequent lookups have the new domain.
            try { await window.TopologyDomains.fetchDomains(); } catch (_) {}
        }

        // See if this file was already migrated on a previous share
        // attempt -- matching by name (case-insensitive) avoids a
        // duplicate row.
        const listResp = await fetch('/api/domains/' + encodeURIComponent(domain.id) + '/topologies');
        if (!listResp.ok) {
            throw new Error('Cannot read multi-user topology list (HTTP ' + listResp.status + ')');
        }
        const topos = await listResp.json();
        const topoNameLc = topoName.toLowerCase();
        const existing = (topos || []).find(t => String(t.name || '').toLowerCase() === topoNameLc);
        if (existing) {
            return { domain: domain, topology: existing, created: false };
        }

        // Pull the legacy file's JSON body. The legacy save code writes
        // `<safe_name>.json` where `safe_name = [A-Za-z0-9_-]+`, so we
        // apply the same sanitization here. If the sanitized and the
        // original names diverge we try both -- old shares may have
        // been written under either.
        const fetchLegacy = async (fname) => {
            const url = '/api/sections/' + encodeURIComponent(sectionId)
                + '/topologies/' + encodeURIComponent(fname);
            try {
                const resp = await fetch(url);
                if (!resp.ok) return null;
                return await resp.json();
            } catch (_) { return null; }
        };

        const sanitized = FileOps._sanitizeTopologyBasename(topoName);
        let data = await fetchLegacy(topoName + '.json');
        if (!data && sanitized && sanitized !== topoName) {
            data = await fetchLegacy(sanitized + '.json');
        }
        if (!data) {
            throw new Error('Legacy file "' + topoName + '" not found in section ' + sectionName);
        }

        // POST creates a new row (no topology_id) and the server assigns
        // a UUID. saveTopology returns the full meta incl. the new id.
        const saved = await window.TopologyDomains.saveTopology(
            topoName, data, domain.id
        );
        return { domain: domain, topology: saved, created: true };
    },

    // SVG for the "shared-out" badge: three connected circles in the
    // section's own color. Tooltip ("title" attr) is set by the caller
    // with the recipient list. Kept visually close in weight to the
    // built-in lock icon so rows stay balanced.
    // Custom hover tooltip: renders immediately (no native `title`
    // 1.5s delay), auto-positions above the target, reads the `title`
    // attribute so we don't need a parallel data attribute.
    //
    // Used on every `.ta-btn` action icon AND on the inline share
    // surfaces (`.topo-owner-inline`, `.topo-recipients-inline`,
    // `.topo-shared-badge`) so the rich tooltip fires consistently
    // whichever pixel you hover.
    //
    // Opts:
    //   hoverBg   -- optional background color applied to the element
    //                while hovered (restored on mouseleave).
    //   restoreBg -- value to restore to when the mouse leaves. Default
    //                'none' matches the old button behavior.
    //   offset    -- extra pixels between the element top and the
    //                tooltip (default 5).
    //
    // We temporarily remove the native `title` attribute on mouseenter
    // so browsers don't render BOTH their own tooltip bubble and ours.
    // The original title is preserved in `dataset._savedTitle` and put
    // back on mouseleave so screen-readers and accessibility tools still
    // see the attribute on the idle element.
    _attachHoverTip(el, opts) {
        if (!el || el.dataset.hoverTipBound === '1') return;
        el.dataset.hoverTipBound = '1';
        const hoverBg = (opts && opts.hoverBg) || null;
        const restoreBg = (opts && typeof opts.restoreBg === 'string')
            ? opts.restoreBg : 'none';
        const offset = (opts && typeof opts.offset === 'number') ? opts.offset : 5;
        let tip = null;
        let svgTitleBackups = null;
        el.addEventListener('mouseenter', () => {
            if (hoverBg) el.style.background = hoverBg;
            const label = el.getAttribute('title')
                || el.getAttribute('data-hover-title');
            if (!label) return;
            if (el.hasAttribute('title')) {
                el.dataset._savedTitle = el.getAttribute('title');
                el.removeAttribute('title');
            }
            // SVG <title> children also trigger native browser tooltips.
            // Hide them while our custom bubble is visible so the user
            // never sees two "Shared with ..." labels stacked together.
            const svgTitles = el.querySelectorAll ? el.querySelectorAll('svg title') : [];
            svgTitleBackups = [];
            svgTitles.forEach((node) => {
                svgTitleBackups.push([node, node.textContent]);
                node.textContent = '';
            });
            const br = el.getBoundingClientRect();
            tip = document.createElement('div');
            tip.className = 'ta-btn-tip';
            tip.textContent = label;
            // Menu-bound tooltips follow the Topologies menu theme
            // (which is intentionally inverted vs. the body), so a
            // dark popover menu gets dark tooltips and a light popover
            // menu gets light tooltips even when the body is the
            // opposite mode. Every current caller attaches these tips
            // to elements inside the Topologies dropdown tree; if a
            // future caller needs body-themed tips, swap back to
            // document.body.classList.contains('dark-mode').
            const isDk = FileOps._menuDark();
            // Lift-in animation: start slightly below + transparent so
            // the bubble slides into place instead of popping in. Ease
            // the opacity+transform together on a short 140 ms curve so
            // "faster and smoother" means "shows up in 1 frame and glides
            // into final position" instead of a hard snap.
            tip.style.cssText = `
                position:fixed; z-index:100001; pointer-events:none;
                bottom:${window.innerHeight - br.top + offset}px;
                left:${br.left + br.width / 2}px;
                transform:translate(-50%, 4px);
                padding:3px 8px; border-radius:5px; white-space:nowrap;
                font-size:10px; font-weight:500; letter-spacing:0.2px;
                font-family:'Poppins',-apple-system,sans-serif;
                background:${isDk ? 'rgba(15,15,30,0.95)' : 'rgba(255,255,255,0.96)'};
                color:${isDk ? 'rgba(255,255,255,0.9)' : 'rgba(20,20,40,0.85)'};
                box-shadow:${isDk ? '0 3px 12px rgba(0,0,0,0.4)' : '0 3px 12px rgba(0,0,0,0.12)'};
                opacity:0;
                transition:opacity 140ms cubic-bezier(0.22, 0.61, 0.36, 1),
                           transform 140ms cubic-bezier(0.22, 0.61, 0.36, 1);
                max-width:320px; overflow:hidden; text-overflow:ellipsis;
                will-change: opacity, transform;
            `;
            document.body.appendChild(tip);
            requestAnimationFrame(() => {
                if (!tip) return;
                tip.style.opacity = '1';
                tip.style.transform = 'translate(-50%, 0)';
            });
        });
        el.addEventListener('mouseleave', () => {
            if (hoverBg) el.style.background = restoreBg;
            if (el.dataset._savedTitle) {
                el.setAttribute('title', el.dataset._savedTitle);
                delete el.dataset._savedTitle;
            }
            if (svgTitleBackups) {
                svgTitleBackups.forEach(([node, text]) => {
                    try { node.textContent = text; } catch (_) {}
                });
                svgTitleBackups = null;
            }
            if (tip) {
                // Graceful fade-out instead of an abrupt remove so the
                // bubble doesn't visually "snap off" when the cursor
                // glides between adjacent controls.
                const _t = tip;
                tip = null;
                _t.style.opacity = '0';
                _t.style.transform = 'translate(-50%, 4px)';
                setTimeout(() => { try { _t.remove(); } catch (_) {} }, 160);
            }
        });
    },

    _sharedOutIconHtml(color, tooltip) {
        const t = (tooltip || 'Shared with others').replace(/"/g, '&quot;');
        return `<svg class="dd-shared-out" viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                    style="color:${color || '#a78bfa'}; flex-shrink:0; opacity:0.95;"
                    aria-label="${t}"><title>${t}</title>
                    <circle cx="18" cy="5" r="3" stroke-width="2.3"/>
                    <circle cx="6" cy="12" r="3" stroke-width="2.3"/>
                    <circle cx="18" cy="19" r="3" stroke-width="2.3"/>
                    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" stroke-width="2"/>
                    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" stroke-width="2"/>
                </svg>`;
    },

    // Small CSS-rotated ring used to swap the share icon while the
    // migrate-on-share pipeline is running. Tinted with the section's
    // own color so the affordance is obvious without shouting. Reuses
    // the global `@keyframes spin` rule declared in topology/index.html
    // so no extra CSS injection is needed.
    _inlineSpinnerHtml(color) {
        const c = color || '#9ca3af';
        return `<svg class="dd-mini-spinner" viewBox="0 0 24 24" width="11" height="11" fill="none"
                    style="color:${c}; flex-shrink:0; animation: spin 0.9s linear infinite; transform-origin:50% 50%;">
                    <title>Preparing share...</title>
                    <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2.5" opacity="0.2"/>
                    <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                </svg>`;
    },

    // POST the legacy<->multi-user mapping to the server with a short
    // exponential backoff (150ms / 400ms / 1s). The mapping is how future
    // owner saves find the multi-user row to mirror into, so if we drop
    // it the share still works but propagation silently stops. Returns
    // true on any success, false if every attempt failed.
    async _mirrorRegisterWithRetry(sectionId, filename, domainId, topologyId) {
        const url = '/api/sections/' + encodeURIComponent(sectionId) + '/_mirror-register';
        const body = JSON.stringify({
            filename: filename, domain_id: domainId, topology_id: topologyId,
        });
        const delays = [150, 400, 1000];
        for (let i = 0; i <= delays.length; i++) {
            try {
                const resp = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body,
                });
                if (resp.ok) return true;
            } catch (_) { /* network glitch; retry */ }
            if (i < delays.length) {
                await new Promise(r => setTimeout(r, delays[i]));
            }
        }
        return false;
    },

    // ==== Share row action helpers ========================================
    //
    // These back the two new inline icons on file rows:
    //   - `.ta-unshare-all`  (owner's "stop sharing with everyone")
    //   - `.ta-remove-mine`  (recipient's "remove from my list")
    //
    // Both follow the same pattern: suspend the dropdown refresh while
    // hitting the API so the live row doesn't get re-rendered out from
    // under us, refresh the shared-files cache on success, then emit
    // `topology-domains:changed` so sibling UI (badge strip, domain
    // title pills, etc.) catches up on the next natural refresh.
    // ======================================================================

    async _unshareAllRecipientsForRow(editor, row, opts) {
        const filename = row.dataset.filename || '';
        const basename = String(filename || '').replace(/\.json$/i, '');
        const sanitized = FileOps._sanitizeTopologyBasename(basename);
        // Need the domain id + list of recipients from the cached
        // outgoing-share index. We intentionally re-read the cache
        // (rather than the DOM) so we pick up any last-second changes
        // made by the share popover before this click.
        const sharingIndex = FileOps._buildSharingIndex();
        let ownDomain = null;
        if (opts && opts.ownDomain) ownDomain = opts.ownDomain;
        else if (opts && opts.section) ownDomain = FileOps._findOwnDomainForSection(opts.section, sharingIndex);
        if (!ownDomain || !ownDomain.id) {
            editor.showToast('Cannot resolve the owning domain for this file', 'error');
            return;
        }
        const hit = sharingIndex.outgoingFilesByKey[ownDomain.id + '|' + sanitized];
        const recipients = (hit && Array.isArray(hit.recipients)) ? hit.recipients : [];
        if (recipients.length === 0) {
            editor.showToast('This file is not currently shared with anyone', 'info');
            return;
        }
        const compositeId = hit && hit.composite_id;
        const topologyId = (hit && hit.topology_id)
            || (compositeId ? compositeId.split(':')[2] : '');
        if (!topologyId) {
            editor.showToast('Cannot stop sharing: missing topology id mapping', 'error');
            return;
        }
        const authFetch = (window.TopologyAuth && window.TopologyAuth.authFetch)
            ? window.TopologyAuth.authFetch : (u, o) => fetch(u, o);
        FileOps._suspendDropdownRefresh = (FileOps._suspendDropdownRefresh || 0) + 1;
        let failures = 0;
        try {
            // Revoke serially so the audit log is ordered and we don't
            // flood the central DB with parallel writes on the same
            // composite_id row -- each call also bumps the `recipients
            // left` count which determines whether `shared_topologies`
            // self-destructs at the end.
            for (const r of recipients) {
                const username = r.username || r.user || r.name;
                if (!username) continue;
                try {
                    // Backend schema is UnshareRequest(target_user: str).
                    // Previously this used `{username: ...}` which Pydantic
                    // rejected with 422 ("Field required"), so every bulk
                    // "Stop sharing with everyone" click actually failed
                    // silently. Must match topology-domains.unshareTopology.
                    const resp = await authFetch(
                        '/api/domains/' + encodeURIComponent(ownDomain.id)
                        + '/topologies/' + encodeURIComponent(topologyId) + '/unshare',
                        {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ target_user: username }),
                        },
                    );
                    if (!resp.ok) {
                        failures += 1;
                        const detail = await resp.text().catch(() => '');
                        console.warn('[unshareAll] revoke failed',
                            { user: username, status: resp.status, body: detail });
                    }
                } catch (err) {
                    failures += 1;
                    console.warn('[unshareAll] revoke threw', username, err);
                }
            }
            // Prime the shared-files cache so the next dropdown render
            // paints the correct (empty) recipient list without a round
            // trip at paint time.
            await FileOps._refreshSharingCache(true).catch(() => {});
        } finally {
            FileOps._suspendDropdownRefresh = Math.max(
                0, (FileOps._suspendDropdownRefresh || 1) - 1,
            );
        }
        if (failures === 0) {
            editor.showToast(`Stopped sharing "${basename}" with ${recipients.length} user${recipients.length === 1 ? '' : 's'}`, 'success');
        } else if (failures < recipients.length) {
            editor.showToast(`Stopped sharing with ${recipients.length - failures}/${recipients.length} recipients (${failures} failed — try again)`, 'warning');
        } else {
            editor.showToast('Could not stop sharing — please try again', 'error');
        }
        // Let the rest of the UI catch up. Dropdown listeners pick this
        // up when the suspend counter drops to zero (already true here).
        document.dispatchEvent(new CustomEvent('topology-domains:changed', {
            detail: { source: 'unshare-all' },
        }));
    },

    async _removeIncomingShareForRow(editor, row, container, opts) {
        const section = opts && opts.section;
        const isInbox = !!(section && section._isInbox);
        let compositeId = (row.dataset.compositeId || '').trim();
        // For shared-in DOMAIN rows the row's id field is just the
        // topology UUID, not a composite. Synthesize one from the
        // section's owner + source_domain_id + topology_id so the
        // per-file remove endpoint can find the row.
        //
        // The source domain id is preferred from `_sourceDomainId`
        // (populated from `/api/domains/share/incoming.original_domain_id`),
        // but in practice `/api/domains` already resolves the shared-in
        // `section.id` down to the owner-local raw domain id too. So we
        // fall back to `section.id` when the explicit field is missing
        // -- previously the fallback was absent and the frontend showed
        // "Cannot remove this shared file individually" even though the
        // data was right there.
        if (!compositeId && !isInbox && section) {
            const owner = section._owner;
            const srcDomainId = section._sourceDomainId
                || section._originalDomainId
                || section.id;
            const topoId = row.dataset.topologyId || '';
            if (owner && srcDomainId && topoId) {
                compositeId = `${owner}:${srcDomainId}:${topoId}`;
            }
        }
        if (!compositeId) {
            editor.showToast('Cannot identify this shared file — try refreshing the dropdown', 'warning');
            return;
        }
        const authFetch = (window.TopologyAuth && window.TopologyAuth.authFetch)
            ? window.TopologyAuth.authFetch : (u, o) => fetch(u, o);
        FileOps._suspendDropdownRefresh = (FileOps._suspendDropdownRefresh || 0) + 1;
        try {
            const resp = await authFetch(
                '/api/domains/share/files/incoming/' + encodeURIComponent(compositeId) + '/remove',
                { method: 'POST' },
            );
            const body = await resp.json().catch(() => ({}));
            // Treat both HTTP errors AND 200-with-`removed:false` as
            // failures. The backend was patched to return 404 when
            // there's no matching inbox row, but we keep the body
            // check as belt-and-suspenders in case an older server
            // build is still in place after a partial restart.
            if (!resp.ok || body.removed === false) {
                editor.showToast(body.detail || 'Failed to remove shared file', 'error');
                return;
            }
            row.remove();
            const remaining = container.querySelectorAll('.domain-topo-row').length;
            if (remaining === 0) {
                container.innerHTML = `<div style="padding:4px 12px 6px;font-size:10px;color:#64748b;font-style:italic;">No shared topologies</div>`;
            }
            editor.showToast('Removed from your Shared-with-me list', 'success');
        } finally {
            FileOps._suspendDropdownRefresh = Math.max(
                0, (FileOps._suspendDropdownRefresh || 1) - 1,
            );
        }
        document.dispatchEvent(new CustomEvent('topology-domains:changed', {
            detail: { source: 'remove-own-share' },
        }));
    },

    async _removeIncomingDomainShare(editor, section) {
        // Companion helper used by the domain-header "remove shared
        // domain" pill. Same pattern as _removeIncomingShareForRow but
        // scoped to the whole inbox for that domain share.
        //
        // The backend share tables are keyed on the composite
        // `<owner>:<raw_domain_id>` (that's the PK of shared_domains /
        // domain_shares), but `/api/domains` rewrites `section.id` to
        // just the raw id so it matches the owner-side topologies DB.
        // So we reconstruct the composite here using `section._owner`
        // (always populated for shared-in virtual sections) -- the
        // router also accepts the raw form as a fallback, but sending
        // the composite is the canonical path.
        const sectionId = section && section.id;
        const sectionName = (section && section.name) || sectionId;
        if (!sectionId) {
            editor.showToast('Cannot identify this shared domain', 'error');
            return false;
        }
        let keyForApi = sectionId;
        if (section._owner && sectionId && !sectionId.includes(':')) {
            keyForApi = `${section._owner}:${sectionId}`;
        }
        const authFetch = (window.TopologyAuth && window.TopologyAuth.authFetch)
            ? window.TopologyAuth.authFetch : (u, o) => fetch(u, o);
        FileOps._suspendDropdownRefresh = (FileOps._suspendDropdownRefresh || 0) + 1;
        try {
            const resp = await authFetch(
                '/api/domains/share/incoming/' + encodeURIComponent(keyForApi) + '/remove',
                { method: 'POST' },
            );
            const body = await resp.json().catch(() => ({}));
            if (!resp.ok || body.removed === false) {
                editor.showToast(
                    body.detail || `Failed to remove "${sectionName}"`,
                    'error',
                );
                return false;
            }
            editor.showToast(
                `Removed "${sectionName}" from your Shared-with-me list`,
                'success',
            );
            return true;
        } finally {
            FileOps._suspendDropdownRefresh = Math.max(
                0, (FileOps._suspendDropdownRefresh || 1) - 1,
            );
            document.dispatchEvent(new CustomEvent('topology-domains:changed', {
                detail: { source: 'remove-own-domain-share' },
            }));
        }
    },

    // SVG for the "shared-in" badge used by the virtual rows (domains
    // + files someone else shared with me). Reuses the universal
    // 3-circle share glyph (same as `_sharedOutIconHtml`) so the
    // affordance unambiguously reads as "share" -- previously this was
    // a tray + down-arrow that read as inbox/dropbox, which confused
    // users ("what is this, download?"). The sender node is FILLED and
    // lives on the left; the two outlined nodes on the right represent
    // the recipients (one of which is you). Tinted purple so it stays
    // visually distinct from the outgoing variant at a glance.
    //
    // The `<title>` child + `aria-label` carry the sharing user's name
    // ("Shared by Alice (write)") so a native browser tooltip appears
    // on hover; `_attachHoverTip` promotes it to the app's rich bubble
    // when the badge is wired into a row (see topo-shared-badge).
    _sharedInIconHtml(color, tooltip) {
        const t = (tooltip || 'Shared with you').replace(/"/g, '&quot;');
        const c = color || '#a78bfa';
        return `<svg class="dd-shared-in" viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
                    style="color:${c}; flex-shrink:0; opacity:0.9;"
                    aria-label="${t}"><title>${t}</title>
                    <circle cx="6" cy="12" r="3" stroke-width="2.3" fill="currentColor"/>
                    <circle cx="18" cy="5" r="3" stroke-width="2.3"/>
                    <circle cx="18" cy="19" r="3" stroke-width="2.3"/>
                    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" stroke-width="2"/>
                    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" stroke-width="2"/>
                </svg>`;
    },

    _renderCustomSectionsInDropdown(editor) {
        const dropdown = document.getElementById('topologies-dropdown-menu');
        if (!dropdown) return;
        
        dropdown.querySelectorAll('.custom-section-category').forEach(el => el.remove());
        
        const anchor = document.getElementById('topology-domains-header');
        const insertAfter = anchor ? anchor.nextSibling : null;
        
        if (!editor._domainCollapsed) {
            editor._domainCollapsed = {};
            for (const s of (editor._customSections || [])) {
                editor._domainCollapsed[s.id] = true;
            }
        }

        // Pull sharing state for badge rendering. Built lazily from the
        // domains API (already cached by loadCustomSections()) so the
        // lookup below is an O(1) hash hit per section row.
        const sharingIndex = FileOps._buildSharingIndex();

        // Render in the saved manual order so drag-to-reorder remains
        // visible after refresh/reopen. The old hue-sorted copy defeated
        // the persisted order and made the feature feel broken.
        const sectionsForRender = editor._customSections || [];
        for (const sec of sectionsForRender) {
            // Hide the legacy AI built-in domain from the Topologies
            // dropdown. Users asked for it to go away now that the AI
            // flow asks "where do you want this topology to land?" on
            // every generation (see topology-ai.js :: _placePendingTopology).
            // The server still honours GET/save under `__ai` so any old
            // bookmarks / URLs keep resolving; we just don't advertise
            // it in the UI anymore.
            if (sec && sec.id === '__ai') continue;
            const div = document.createElement('div');
            div.className = 'menu-category custom-section-category';
            div.dataset.sectionId = sec.id;
            const isDkDomain = FileOps._menuDark(editor);
            // Chip tint (hex alpha): bumped from 22/28 (~13-16%) to 38/48
            // (~22-28%) so each domain's colour identity is clearly
            // readable against the new near-opaque dropdown background.
            //
            // Left accent stripe (2026-04-22): widened from 3px to 4px
            // and bumped to full-opacity. The previous 80/d0 alpha on
            // dark/light menus looked washed out next to the bold
            // outlined title, so the stripe now matches the title
            // colour 1:1 and reads as a proper category rim rather
            // than a faded hint.
            // 2026-04-23: accent colour also exposed as a CSS custom
            // property so the domain-row v2 rules in styles.css can
            // drive badges/buttons/quickedit via `color-mix(...)`
            // instead of the JS concatenating 4-character hex alphas.
            // Also mark the active-domain row (matches the currently-
            // loaded topology's sectionId) so the inner ring kicks in.
            let activeSectionId = null;
            try {
                const raw = localStorage.getItem('topo_active');
                if (raw) activeSectionId = (JSON.parse(raw) || {}).sectionId || null;
            } catch (_) {}
            const accent = sec.color || '#3b82f6';
            div.style.cssText = `background: ${accent}${isDkDomain ? '38' : '48'}; padding: 0; border-left: 4px solid ${accent}; --row-accent: ${accent};`;
            if (activeSectionId && sec.id === activeSectionId) {
                div.classList.add('is-active');
            }

            const icon = (FileOps._sectionIcons().find(i => i.id === sec.icon) || FileOps._sectionIcons()[0]).svg;
            const collapsed = editor._domainCollapsed[sec.id] || false;
            const bodyId = `domain-body-${sec.id}`;

            const btnColor = isDkDomain ? '#e2e8f0' : '#1e1e32';
            const sharedOutIconColor = isDkDomain ? '#ffffff' : '#000000';
            const isBuiltin = !!sec.builtin;
            const isBugsBuiltin = isBuiltin && sec.id === '__bugs';
            const handleSvg = isBuiltin
                ? `<svg class="dd-lock" viewBox="0 0 24 24" width="10" height="10" style="color:${sec.color}; flex-shrink:0; opacity:0.55;" title="Built-in domain"><rect x="5" y="11" width="14" height="9" rx="2" stroke="currentColor" stroke-width="2" fill="none"/><path d="M8 11V8a4 4 0 0 1 8 0v3" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/></svg>`
                : `<svg class="dd-grip" viewBox="0 0 24 24" width="10" height="10" style="color:${sec.color}; flex-shrink:0; opacity:0.45; cursor:grab;"><circle cx="9" cy="7" r="1.3" fill="currentColor"/><circle cx="15" cy="7" r="1.3" fill="currentColor"/><circle cx="9" cy="12" r="1.3" fill="currentColor"/><circle cx="15" cy="12" r="1.3" fill="currentColor"/><circle cx="9" cy="17" r="1.3" fill="currentColor"/><circle cx="15" cy="17" r="1.3" fill="currentColor"/></svg>`;
            // Outgoing domain-share indicator -- rendered next to the
            // built-in lock / drag handle, at the same visual slot the
            // user's screenshot pinned. Tooltip enumerates recipients so
            // hover always discloses "who you're sharing this with".
            const ownDomain = FileOps._findOwnDomainForSection(sec, sharingIndex);
            const sharedRecipients = (ownDomain && Array.isArray(ownDomain.shared_with))
                ? ownDomain.shared_with.filter(Boolean) : [];
            let sharedBadgeSvg = '';
            if (sharedRecipients.length > 0) {
                const list = sharedRecipients.length <= 6
                    ? sharedRecipients.join(', ')
                    : sharedRecipients.slice(0, 6).join(', ') + ' +' + (sharedRecipients.length - 6);
                sharedBadgeSvg = FileOps._sharedOutIconHtml(sharedOutIconColor, `Shared with ${list}`);
            }
            // "+ Bug" pill on the Bugs row header. Styling is class-based
            // (styles.css `.domain-newbug-btn`); only the dynamic accent
            // colour is threaded through as a CSS custom property so the
            // CSS can compute all the hover/focus/active/active-panel
            // derivatives without re-reading `sec.color` every time. The
            // container query on `.custom-section-category` lets the label
            // collapse to icon-only when the Topologies dropdown is narrow.
            const newBugBtn = isBugsBuiltin
                ? `<button class="domain-newbug-btn" data-action="new-bug" title="Create a bug topology from a Jira SW number" aria-label="Create bug topology"
                        style="--bug-accent:${sec.color};--bug-accent-bg:${sec.color}${isDkDomain ? '22' : '20'};--bug-accent-bg-hover:${sec.color}${isDkDomain ? '40' : '35'};--bug-accent-border:${sec.color}${isDkDomain ? '40' : '50'};--bug-accent-border-hover:${sec.color}${isDkDomain ? '70' : '80'};">
                        <svg class="domain-newbug-icon" viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                        <span class="domain-newbug-label">Bug</span>
                    </button>`
                : '';
            // Halo around the domain-name letters so a vivid-coloured
            // title stays readable on top of the SAME-hue pill tint.
            // Menus in this app invert the body theme (dark body ->
            // light menu, light body -> dark menu).
            //
            // Domain labels keep a super-thin vector rim for contrast on
            // pastel rows. Use text-stroke instead of shadow offsets so
            // normal-distance rendering stays crisp rather than smeared.
            const titleOutline = 'none';
            const titleStroke = isDkDomain
                ? '0.18px rgba(15,20,35,0.70)'
                : '0.18px rgba(255,255,255,0.82)';
            // NOTE: the dedicated reveal-on-hover "settings gear" that used to
            // live here has been retired. It rendered as a second cog right
            // next to the always-visible `.domain-knowledge-toggle` gear
            // from topology-domain-knowledge.js, so non-builtin rows kept
            // flashing two visually identical gears on hover (reported
            // 2026-04-22). The rename / icon / colour editor is now an
            // "Edit appearance" accordion inside the single knowledge
            // panel (see topology-domain-knowledge.js), and the legacy
            // `_openDomainQuickEdit` still works for any code that opens
            // the inline quickedit directly -- it just no longer has a
            // button of its own in the title bar.
            const safeSecName = (sec.name || 'domain').replace(/"/g, '&quot;');
            const settingsBtn = '';
            // Icon outline: previously a 4-direction 0.5px drop-shadow halo
            // (matching the domain title text outline) which read as a
            // visible "border" around each domain glyph. Per UX request
            // (2026-04-24f), the icons now paint with just their accent
            // stroke -- the title's text-shadow alone is enough contrast,
            // and the cleaner icon makes the row chip read as a single
            // calm pill instead of "stickered" badges. Kept the variable
            // around as `'none'` so the inline style stays declarative
            // and we can dial it back up to a super-thin halo without
            // touching the JSX.
            const iconOutlineFilter = 'none';
            div.innerHTML = `
                <div class="domain-title" id="domain-title-${sec.id}" role="button" tabindex="0"
                     aria-controls="${bodyId}" aria-expanded="${!collapsed}"
                     style="color: ${sec.color}; display: flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 780; letter-spacing: 0.12px; padding: 8px 12px; cursor: pointer; user-select: none;">
                    ${handleSvg}
                    ${sharedBadgeSvg}
                    <svg class="domain-row-icon" viewBox="0 0 24 24" width="17" height="17" style="color:${sec.color}; flex-shrink:0; filter:${iconOutlineFilter}; stroke-width:2.6;">${icon}</svg>
                    <span class="domain-title-name" style="flex:1; text-shadow: ${titleOutline}; -webkit-text-stroke: ${titleStroke}; paint-order: stroke fill;">${(sec.name || 'Untitled').toUpperCase()}</span>
                    <span class="domain-count-badge" data-count-for="${sec.id}" aria-label="Topology count"></span>
                    ${newBugBtn}
                    ${settingsBtn}
                    <svg class="domain-chevron" viewBox="0 0 24 24" width="12" height="12" style="color:${sec.color}; flex-shrink:0; opacity:0.6; transition: transform 0.2s; transform: rotate(${collapsed ? '-90deg' : '0deg'});">
                        <polyline points="6 9 12 15 18 9" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <div class="domain-body" id="${bodyId}" style="display: ${collapsed ? 'none' : 'block'}; padding: 0 0 6px;">
                    <div class="domain-actions">
                        <button data-action="save" class="domain-action-btn primary" type="button"
                                title="Save current canvas to ${safeSecName}" aria-label="Save to ${safeSecName}">
                            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                            <span class="domain-action-label">Save</span>
                        </button>
                        <button data-action="load-file" class="domain-action-btn" type="button"
                                title="Load a topology JSON into ${safeSecName}" aria-label="Load file into ${safeSecName}">
                            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                            <span class="domain-action-label">Load</span>
                        </button>
                        <button data-action="clean-domain" class="domain-action-btn domain-clean-btn" type="button"
                                title="Delete selected topologies from ${safeSecName}" aria-label="Clean topologies in ${safeSecName}">
                            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v5"/><path d="M14 11v5"/></svg>
                            <span class="domain-action-label">Clean</span>
                        </button>
                        <button data-action="share-domain" class="domain-action-btn" type="button"
                                title="Share this domain with other users" aria-label="Share ${safeSecName}">
                            <svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
                            <span class="domain-action-label">Share</span>
                        </button>
                    </div>
                    <div class="domain-quickedit-wrap"></div>
                    <div class="domain-save-form" style="display:none;padding:4px 10px 8px;"></div>
                    <div class="domain-share-form" style="display:none;"></div>
                    <div class="domain-topos-list" style="max-height:160px;overflow-y:auto;"></div>
                </div>
            `;

            const bodyEl = div.querySelector('.domain-body');
            const chevron = div.querySelector('.domain-chevron');
            const toposListEl = div.querySelector('.domain-topos-list');

            // Outgoing-share badge on own-domain title (the 3-circle SVG
            // next to the lock/grip handle). The SVG has a `<title>`
            // child for a11y only -- promote it to a `title` attribute
            // so `_attachHoverTip` surfaces the recipient list with the
            // same instant bubble style as the file-row badges.
            const outHandle = div.querySelector('.domain-title .dd-shared-out');
            if (outHandle && !outHandle.hasAttribute('title')) {
                const ariaLabel = outHandle.getAttribute('aria-label') || '';
                if (ariaLabel) outHandle.setAttribute('title', ariaLabel);
            }
            if (outHandle) FileOps._attachHoverTip(outHandle);

            // Hover / focus / pressed visuals are now entirely in styles.css
            // (`.domain-action-btn` + `.is-pressed`). No JS wiring needed --
            // --row-accent on the outer div drives all the colour-mix tints.

            const newBugBtnEl = div.querySelector('[data-action="new-bug"]');
            if (newBugBtnEl) {
                // Hover/active visuals are entirely in `styles.css .domain-newbug-btn`
                // (they read the `--bug-accent-*` custom properties on the element).
                // We only wire the click handler here; stopping mousedown keeps
                // the Bugs row chevron from toggling behind the button press.
                newBugBtnEl.addEventListener('mousedown', (e) => { e.stopPropagation(); });
                newBugBtnEl.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const anchorEl = e.currentTarget;
                    if (window.TopologyBugs && typeof window.TopologyBugs.open === 'function') {
                        window.TopologyBugs.open(anchorEl);
                    } else {
                        editor.showToast('Bug topology dialog is not available right now', 'warning');
                    }
                });
            }

            const shareDomainBtn = div.querySelector('[data-action="share-domain"]');
            if (shareDomainBtn) {
                shareDomainBtn.addEventListener('mousedown', (e) => { e.stopPropagation(); });
                shareDomainBtn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const anchorEl = e.currentTarget;
                    if (shareDomainBtn.dataset.working === '1') return;
                    if (window.TopologyShare && typeof window.TopologyShare.openForDomain === 'function') {
                        shareDomainBtn.dataset.working = '1';
                        shareDomainBtn.disabled = true;
                        const prevHtml = shareDomainBtn.innerHTML;
                        shareDomainBtn.innerHTML = FileOps._inlineSpinnerHtml(sec.color || '#9ca3af');
                        FileOps._suspendDropdownRefresh = (FileOps._suspendDropdownRefresh || 0) + 1;
                        let domainHint = sec.name;
                        let opened = false;
                        try {
                            // Domain sharing uses the multi-user domain DB.
                            // Legacy /api/sections rows must be mirrored first
                            // so "Share" grants access to the actual files,
                            // not an empty same-name domain.
                            if (!div.dataset.sharedIn && typeof FileOps._ensureLegacyTopologyMigrated === 'function') {
                                const resp = await FileOps._authFetch(
                                    `/api/sections/${encodeURIComponent(sec.id)}/topologies`,
                                );
                                const data = resp.ok ? await resp.json() : {};
                                const topos = Array.isArray(data.topologies) ? data.topologies : [];
                                let migratedDomain = null;
                                const failedMirrors = [];
                                for (const topo of topos) {
                                    const fileName = topo.filename || topo.name;
                                    if (!fileName) continue;
                                    try {
                                        const migrated = await FileOps._ensureLegacyTopologyMigrated(
                                            editor, sec.id, sec, fileName,
                                        );
                                        if (migrated && migrated.domain) migratedDomain = migrated.domain;
                                        if (migrated && migrated.domain && migrated.topology) {
                                            await FileOps._mirrorRegisterWithRetry(
                                                sec.id,
                                                fileName,
                                                migrated.domain.id,
                                                migrated.topology.id,
                                            );
                                        }
                                    } catch (err) {
                                        failedMirrors.push(fileName);
                                    }
                                }
                                if (migratedDomain && migratedDomain.id) domainHint = migratedDomain.id;
                                if (failedMirrors.length) {
                                    editor.showToast(
                                        'Share panel opened, but ' + failedMirrors.length +
                                        ' topology mirror sync failed. Re-save those files to include them.',
                                        'warning',
                                    );
                                }
                            }
                            await window.TopologyShare.openForDomain(domainHint, null, anchorEl);
                            opened = true;
                        } catch (err) {
                            const msg = (err && err.message) ? err.message : String(err);
                            editor.showToast('Cannot prepare domain sharing: ' + msg, 'error');
                        } finally {
                            shareDomainBtn.disabled = false;
                            shareDomainBtn.innerHTML = prevHtml;
                            delete shareDomainBtn.dataset.working;
                            FileOps._suspendDropdownRefresh = Math.max(
                                0, (FileOps._suspendDropdownRefresh || 1) - 1,
                            );
                            if (opened && FileOps._suspendDropdownRefresh === 0) {
                                FileOps._refreshSharingCache(true).catch(() => {});
                            }
                        }
                    } else if (window.TopologyShare && typeof window.TopologyShare.open === 'function') {
                        try {
                            await window.TopologyShare.open(anchorEl);
                        } catch (err) {
                            const msg = (err && err.message) ? err.message : String(err);
                            editor.showToast('Cannot open sharing: ' + msg, 'error');
                        }
                    } else {
                        editor.showToast('Share is not available right now', 'warning');
                    }
                });
                // Mirror the inline share form's `.open` state on the button
                // so the user gets visual confirmation that clicking the
                // Share button actually did something. User reported:
                // "sharing a whole domain button does not work, at least
                // visually" -- the form WAS opening below, but the button
                // never showed its pressed/active state so it felt dead.
                //
                // The share form DOM node is created on demand inside
                // .domain-body by topology-share.js:_ensureDomainShareHost,
                // so we watch the entire .domain-body subtree for either
                // its addition or for `.open` class toggles.
                const _syncSharePressed = () => {
                    const formEl = div.querySelector(':scope > .domain-body > .domain-share-form');
                    const on = !!(formEl && formEl.classList.contains('open'));
                    shareDomainBtn.classList.toggle('is-pressed', on);
                    if (on) shareDomainBtn.dataset.pressed = '1';
                    else delete shareDomainBtn.dataset.pressed;
                };
                const bodyEl = div.querySelector('.domain-body');
                if (bodyEl && typeof MutationObserver === 'function') {
                    const obs = new MutationObserver(_syncSharePressed);
                    obs.observe(bodyEl, {
                        attributes: true,
                        attributeFilter: ['class'],
                        subtree: true,
                        childList: true
                    });
                }
            }

            // The per-row settings gear wiring used to live here. It was
            // retired alongside the `.domain-settings-btn` markup above
            // (see the matching comment) to stop the double-gear render
            // on hover. `_openDomainQuickEdit` is still reachable for
            // programmatic use (e.g. the "Edit appearance" accordion in
            // the knowledge panel routes through the shared builder).

            const saveBtn = div.querySelector('[data-action="save"]');
            const loadFileBtn = div.querySelector('[data-action="load-file"]');
            const cleanDomainBtn = div.querySelector('[data-action="clean-domain"]');
            const saveForm = div.querySelector('.domain-save-form');
            const _setPressed = (btn, on) => {
                if (!btn) return;
                btn.classList.toggle('is-pressed', !!on);
                if (on) btn.dataset.pressed = '1';
                else delete btn.dataset.pressed;
            };
            saveBtn.onclick = (e) => {
                e.stopPropagation();
                if (editor.objects.length === 0) { editor.showToast('Nothing to save — canvas is empty', 'warning'); return; }
                const isOpen = saveForm.style.display !== 'none';
                saveForm.style.display = isOpen ? 'none' : 'block';
                _setPressed(saveBtn, !isOpen);
                if (!isOpen) {
                    const defaultName = 'topology_' + new Date().toISOString().slice(0, 10);
                    const isDk = FileOps._menuDark(editor);
                    saveForm.innerHTML = `
                        <div style="display:flex;gap:4px;align-items:center;">
                            <input class="domain-save-name" type="text" value="${defaultName}" placeholder="Topology name"
                                style="flex:1;padding:5px 8px;background:${isDk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.04)'};border:1px solid ${sec.color}55;
                                border-radius:5px;color:${isDk ? '#e2e8f0' : '#1e1e32'};font-size:11px;font-family:inherit;outline:none;"
                                onclick="event.stopPropagation();">
                            <button class="domain-save-confirm" style="padding:5px 10px;background:${sec.color};border:none;
                                border-radius:5px;color:#fff;font-size:11px;font-weight:600;cursor:pointer;font-family:inherit;white-space:nowrap;">Save</button>
                        </div>
                    `;
                    const input = saveForm.querySelector('.domain-save-name');
                    const confirmBtn = saveForm.querySelector('.domain-save-confirm');
                    input.focus();
                    input.select();
                    const doSave = async () => {
                        const name = input.value.trim();
                        if (!name) { editor.showToast('Enter a topology name', 'warning'); return; }
                        confirmBtn.textContent = '...';
                        confirmBtn.disabled = true;
                        try {
                            const result = await FileOps._sectionSaveWithConflict(
                                editor,
                                sec.id,
                                { name, topology: FileOps.generateTopologyData(editor) },
                                () => {
                                    FileOps.updateTopologyIndicator(name, sec.name, sec.color, sec.id);
                                    editor.showToast('Saved to ' + sec.name, 'success');
                                    FileOps._markTopologyClean(editor, 'domain-inline-save');
                                }
                            );
                            if (result && !result.error && !result.conflict && !result.quota) {
                                saveForm.style.display = 'none';
                                _setPressed(saveBtn, false);
                                FileOps._loadDomainTopologiesInline(editor, sec, div.querySelector('.domain-topos-list'));
                            }
                        } catch (err) { editor.showToast('Save failed: ' + err.message, 'error'); }
                        confirmBtn.textContent = 'Save';
                        confirmBtn.disabled = false;
                    };
                    confirmBtn.onclick = (ev) => { ev.stopPropagation(); doSave(); };
                    input.addEventListener('keydown', (ev) => { ev.stopPropagation(); if (ev.key === 'Enter') doSave(); if (ev.key === 'Escape') { saveForm.style.display = 'none'; _setPressed(saveBtn, false); } });
                }
            };

            loadFileBtn.onclick = (e) => {
                e.stopPropagation();
                _setPressed(loadFileBtn, true);
                const fileInput = document.createElement('input');
                fileInput.type = 'file';
                fileInput.accept = '.json';
                fileInput.onchange = async () => {
                    const file = fileInput.files[0];
                    if (!file) { _setPressed(loadFileBtn, false); return; }
                    try {
                        const text = await file.text();
                        const data = JSON.parse(text);
                        const name = file.name.replace(/\.json$/i, '');
                        const result = await FileOps._sectionSaveWithConflict(
                            editor,
                            sec.id,
                            { name, topology: data },
                            null,
                        );
                        if (result && (result.error || result.conflict || result.quota)) return;
                        FileOps._loadIntoEditor(editor, data, {
                            name,
                            domain: sec.name,
                            color: sec.color,
                            sectionId: sec.id,
                        });
                        editor.showToast(`Loaded and saved to ${sec.name}`, 'success');
                        FileOps._loadDomainTopologiesInline(editor, sec, div.querySelector('.domain-topos-list'));
                        const dropdown = document.getElementById('topologies-dropdown-menu');
                        if (dropdown) dropdown.style.display = 'none';
                    } catch (err) { editor.showToast('Failed to load file: ' + err.message, 'error'); }
                    _setPressed(loadFileBtn, false);
                };
                fileInput.addEventListener('cancel', () => _setPressed(loadFileBtn, false));
                fileInput.click();
            };

            if (cleanDomainBtn) {
                cleanDomainBtn.onclick = async (e) => {
                    e.stopPropagation();
                    _setPressed(cleanDomainBtn, true);
                    try {
                        await FileOps._openDomainCleanupPrompt(editor, sec, div.querySelector('.domain-topos-list'), {
                            reason: 'manual',
                        });
                    } finally {
                        _setPressed(cleanDomainBtn, false);
                    }
                };
            }
            
            const titleHandle = div.querySelector('.domain-title');
            titleHandle.addEventListener('mousedown', (e) => {
                if (e.button !== 0) return;
                if (isBuiltin) {
                    // Built-in domains (e.g. __bugs, __ai) are PINNED -- no
                    // drag/reorder -- but must still expand/collapse on click,
                    // otherwise users can't open the Bugs or AI sections. We
                    // short-circuit the drag machinery and just listen for
                    // mouseup to flip `domain-body` visibility + chevron.
                    // Child buttons (+ Bug, Save, Load, Share) stop propagation
                    // at their own mousedown so they won't reach this handler.
                    e.preventDefault();
                    const onBuiltinUp = (ev) => {
                        document.removeEventListener('mouseup', onBuiltinUp, true);
                        // Allow a small jitter tolerance (matches the 6px drag
                        // threshold used for custom domains) so tiny pointer
                        // movement during click still toggles.
                        if (Math.abs(ev.clientY - e.clientY) + Math.abs(ev.clientX - e.clientX) > 6) return;
                        const isCollapsed = bodyEl.style.display === 'none';
                        bodyEl.style.display = isCollapsed ? 'block' : 'none';
                        chevron.style.transform = isCollapsed ? 'rotate(0deg)' : 'rotate(-90deg)';
                        editor._domainCollapsed[sec.id] = !isCollapsed;
                        titleHandle.setAttribute('aria-expanded', String(isCollapsed));
                        if (isCollapsed) {
                            FileOps._ensureDomainTopologiesRendered(editor, sec, toposListEl);
                        }
                        // Collapsing narrows the widest-row set; expanding
                        // might reveal a row wider than anything currently
                        // shown. Either way, re-fit the dropdown to its
                        // new intrinsic content.
                        requestAnimationFrame(() => FileOps._fitDropdownToContent());
                    };
                    document.addEventListener('mouseup', onBuiltinUp, true);
                    return;
                }
                e.preventDefault();
                let startY = e.clientY;
                const startX = e.clientX;
                let dragging = false;
                let allDomains = [];
                let offsets = [];      // offsetTop relative to parent (scroll-proof)
                let heights = [];
                let slotYs = [];
                let currentOrder = [];
                let dragIdx = -1;
                const ease = 'cubic-bezier(0.22, 1, 0.36, 1)';

                const applyTransforms = () => {
                    for (let pos = 0; pos < currentOrder.length; pos++) {
                        const idx = currentOrder[pos];
                        if (idx === dragIdx) continue;
                        const dy = slotYs[pos] - offsets[idx];
                        allDomains[idx].style.transition = `transform 0.18s ${ease}`;
                        allDomains[idx].style.transform = dy ? `translateY(${dy}px)` : '';
                    }
                };

                let layoutReady = false;

                const recalcLayout = (resetOrder = true, preserveDrag = false) => {
                    allDomains.forEach((d, i) => {
                        if (preserveDrag && i === dragIdx) return;
                        d.style.transform = '';
                        d.style.transition = 'none';
                    });
                    offsets = allDomains.map(d => d.offsetTop);
                    heights = allDomains.map(d => d.offsetHeight);
                    if (resetOrder || !currentOrder.length) currentOrder = allDomains.map((_, i) => i);
                    slotYs = [];
                    let y = offsets[0];
                    for (let i = 0; i < allDomains.length; i++) {
                        slotYs.push(y);
                        if (i < allDomains.length - 1) {
                            const gap = offsets[i + 1] - (offsets[i] + heights[i]);
                            y += heights[i] + Math.max(gap, 0);
                        }
                    }
                    layoutReady = true;
                };

                const onMove = (ev) => {
                    if (!dragging && Math.abs(ev.clientY - startY) + Math.abs(ev.clientX - startX) < 6) return;

                    if (!dragging) {
                        allDomains = [...dropdown.querySelectorAll('.custom-section-category:not([data-shared-in="1"])')];
                        if (allDomains.length < 2) { cleanup(); return; }
                        dragIdx = allDomains.indexOf(div);
                        if (dragIdx < 0) { cleanup(); return; }
                        dragging = true;
                        editor._domainDragActive = true;

                        dropdown.style.overflowY = 'hidden';
                        dropdown.classList.add('is-domain-reordering');

                        recalcLayout(true);

                        let hasOpenBodies = false;
                        allDomains.forEach(d => {
                            const body = d.querySelector('.domain-body');
                            if (body && body.style.display !== 'none') {
                                hasOpenBodies = true;
                                body.dataset.wasOpen = 'true';
                                const h = body.scrollHeight;
                                body.style.maxHeight = h + 'px';
                                body.style.overflow = 'hidden';
                                body.style.transition = 'none';
                                body.offsetHeight;
                                body.style.transition = `max-height 0.25s ${ease}, opacity 0.2s ease`;
                                body.style.maxHeight = '0px';
                                body.style.opacity = '0';
                            }
                        });
                        if (hasOpenBodies) {
                            const oldDragOffset = div.offsetTop;
                            setTimeout(() => {
                                if (!editor._domainDragActive) return;
                                recalcLayout(false, true);
                                const newDragOffset = offsets[dragIdx];
                                startY += (newDragOffset - oldDragOffset);
                                applyTransforms();
                            }, 110);
                        }

                        allDomains.forEach((d, i) => {
                            d.style.position = 'relative';
                            if (i === dragIdx) {
                                d.classList.add('is-dragging');
                                d.style.zIndex = '100';
                                d.style.boxShadow = '0 8px 24px rgba(0,0,0,0.32)';
                                d.style.opacity = '0.95';
                                d.style.transition = 'box-shadow 0.15s, opacity 0.15s';
                            } else {
                                d.style.zIndex = '1';
                            }
                        });

                        document.body.style.cursor = 'grabbing';
                        titleHandle.style.cursor = 'grabbing';
                        const gripEl = div.querySelector('.dd-grip');
                        if (gripEl) gripEl.style.cursor = 'grabbing';
                    }

                    const dy = ev.clientY - startY;
                    div.style.transform = `translateY(${dy}px)`;
                    div.style.transition = 'none';

                    if (!layoutReady || !heights.length) return;

                    const dragMid = offsets[dragIdx] + dy + heights[dragIdx] / 2;
                    const dragPos = currentOrder.indexOf(dragIdx);

                    if (dragPos > 0) {
                        const aboveIdx = currentOrder[dragPos - 1];
                        const aboveMid = slotYs[dragPos - 1] + heights[aboveIdx] * 0.45;
                        if (dragMid < aboveMid) {
                            currentOrder.splice(dragPos, 1);
                            currentOrder.splice(dragPos - 1, 0, dragIdx);
                            applyTransforms();
                        }
                    }

                    if (dragPos < currentOrder.length - 1) {
                        const belowIdx = currentOrder[dragPos + 1];
                        const belowMid = slotYs[dragPos + 1] + heights[belowIdx] * 0.55;
                        if (dragMid > belowMid) {
                            currentOrder.splice(dragPos, 1);
                            currentOrder.splice(dragPos + 1, 0, dragIdx);
                            applyTransforms();
                        }
                    }
                };

                const cleanup = () => {
                    document.removeEventListener('mousemove', onMove);
                    document.removeEventListener('mouseup', onUp);
                    document.body.style.cursor = '';
                    titleHandle.style.cursor = '';
                    const gripEl = div.querySelector('.dd-grip');
                    if (gripEl) gripEl.style.cursor = 'grab';
                    dropdown.style.overflowY = '';
                    dropdown.classList.remove('is-domain-reordering');
                    editor._domainDragActive = false;
                    allDomains.forEach(d => d.classList.remove('is-dragging'));
                };

                const onUp = async () => {
                    cleanup();
                    if (!dragging) {
                        const isCollapsed = bodyEl.style.display === 'none';
                        bodyEl.style.display = isCollapsed ? 'block' : 'none';
                        chevron.style.transform = isCollapsed ? 'rotate(0deg)' : 'rotate(-90deg)';
                        editor._domainCollapsed[sec.id] = !isCollapsed;
                        titleHandle.setAttribute('aria-expanded', String(isCollapsed));
                        if (isCollapsed) {
                            FileOps._ensureDomainTopologiesRendered(editor, sec, toposListEl);
                        }
                        requestAnimationFrame(() => FileOps._fitDropdownToContent());
                        return;
                    }

                    const orderChanged = currentOrder.some((idx, pos) => idx !== pos);

                    const dragPos = currentOrder.indexOf(dragIdx);
                    const finalDy = layoutReady ? (slotYs[dragPos] - offsets[dragIdx]) : 0;
                    div.style.transition = `transform 0.18s ${ease}, box-shadow 0.18s, opacity 0.18s`;
                    div.style.transform = finalDy ? `translateY(${finalDy}px)` : '';
                    div.style.boxShadow = '';
                    div.style.opacity = '1';

                    setTimeout(async () => {
                        if (orderChanged) {
                            const frag = document.createDocumentFragment();
                            currentOrder.forEach(idx => frag.appendChild(allDomains[idx]));
                            const anchor = document.getElementById('topology-domains-header');
                            // When topology-share.js has split the dropdown into
                            // .dd-main-col + .dd-share-col, the header's parent is
                            // .dd-main-col -- insert the reordered fragment there so
                            // we don't trip DOMException "node not a child" by
                            // inserting into the outer dropdown.
                            const mount = (anchor && anchor.parentNode) || dropdown;
                            if (anchor && anchor.nextSibling) {
                                mount.insertBefore(frag, anchor.nextSibling);
                            } else {
                                mount.appendChild(frag);
                            }
                        }

                        allDomains.forEach(d => {
                            d.classList.remove('is-dragging');
                            d.style.transition = '';
                            d.style.transform = '';
                            d.style.position = '';
                            d.style.zIndex = '';
                            d.style.boxShadow = '';
                            d.style.opacity = '';
                        });

                        allDomains.forEach(d => {
                            const body = d.querySelector('.domain-body');
                            if (body && body.dataset.wasOpen === 'true') {
                                delete body.dataset.wasOpen;
                                body.style.display = 'block';
                                body.style.transition = 'none';
                                body.style.maxHeight = '0px';
                                body.style.opacity = '0';
                                body.style.overflow = 'hidden';
                                body.offsetHeight;
                                const targetH = body.scrollHeight || 200;
                                body.style.transition = `max-height 0.3s ${ease}, opacity 0.25s ease`;
                                body.style.maxHeight = targetH + 'px';
                                body.style.opacity = '1';
                                setTimeout(() => {
                                    body.style.maxHeight = '';
                                    body.style.height = '';
                                    body.style.opacity = '';
                                    body.style.overflow = '';
                                    body.style.transition = '';
                                }, 320);
                            }
                        });

                        if (!orderChanged) return;

                        const finalIds = currentOrder.map(i => allDomains[i].dataset.sectionId);
                        const sections = editor._customSections || [];
                        const renderedIds = new Set(finalIds);
                        const reordered = finalIds.map(id => sections.find(s => s.id === id)).filter(Boolean);

                        if (reordered.length !== finalIds.length) return;
                        sections.forEach(sec => {
                            if (sec && !renderedIds.has(sec.id)) reordered.push(sec);
                        });

                        editor._customSections = reordered;
                        FileOps._updateTopoBtnIcon(editor);
                        try {
                            await FileOps._authFetch('/api/sections/reorder', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ sections: reordered })
                            });
                        } catch (_) {}
                    }, 190);
                };

                document.addEventListener('mousemove', onMove);
                document.addEventListener('mouseup', onUp);
            });

            // Keyboard accessibility on the domain-title row.
            //   - Enter / Space      : toggle expand+collapse (same as a click)
            //   - ArrowDown / ArrowUp: move focus to the next / previous row
            //   - Home / End         : jump to the first / last row
            //   - Escape             : collapse this row when it is open
            // Mirrors every state update the mouse path does (display,
            // chevron rotation, `_domainCollapsed` cache, aria-expanded,
            // and the width re-fit) so screen reader / keyboard users
            // see the exact same visual + a11y result.
            titleHandle.addEventListener('keydown', (ev) => {
                const key = ev.key;
                const isToggle = (key === 'Enter' || key === ' ' || key === 'Spacebar');
                if (isToggle) {
                    ev.preventDefault();
                    const isCollapsed = bodyEl.style.display === 'none';
                    bodyEl.style.display = isCollapsed ? 'block' : 'none';
                    chevron.style.transform = isCollapsed ? 'rotate(0deg)' : 'rotate(-90deg)';
                    editor._domainCollapsed[sec.id] = !isCollapsed;
                    titleHandle.setAttribute('aria-expanded', String(isCollapsed));
                    if (isCollapsed) {
                        FileOps._ensureDomainTopologiesRendered(editor, sec, toposListEl);
                    }
                    requestAnimationFrame(() => FileOps._fitDropdownToContent());
                    return;
                }
                if (key === 'ArrowDown' || key === 'ArrowUp') {
                    ev.preventDefault();
                    const rows = [...dropdown.querySelectorAll('.custom-section-category .domain-title')];
                    const idx = rows.indexOf(titleHandle);
                    if (idx < 0) return;
                    const next = rows[key === 'ArrowDown' ? idx + 1 : idx - 1];
                    if (next) next.focus();
                    return;
                }
                if (key === 'Home') {
                    ev.preventDefault();
                    const rows = [...dropdown.querySelectorAll('.custom-section-category .domain-title')];
                    if (rows[0]) rows[0].focus();
                    return;
                }
                if (key === 'End') {
                    ev.preventDefault();
                    const rows = [...dropdown.querySelectorAll('.custom-section-category .domain-title')];
                    if (rows.length) rows[rows.length - 1].focus();
                    return;
                }
                if (key === 'Escape') {
                    if (bodyEl.style.display !== 'none') {
                        ev.preventDefault();
                        bodyEl.style.display = 'none';
                        chevron.style.transform = 'rotate(-90deg)';
                        editor._domainCollapsed[sec.id] = true;
                        titleHandle.setAttribute('aria-expanded', 'false');
                        requestAnimationFrame(() => FileOps._fitDropdownToContent());
                    }
                    return;
                }
            });

            // When topology-share.js has split the dropdown into columns,
            // the anchor (topology-domains-header) lives inside .dd-main-col
            // -- insert next to it in its real parent instead of on the
            // outer dropdown, otherwise DOM throws "node not a child".
            const mount = (insertAfter && insertAfter.parentNode) || (anchor && anchor.parentNode) || dropdown;
            if (insertAfter) mount.insertBefore(div, insertAfter);
            else if (anchor) anchor.after(div);
            else mount.appendChild(div);

            FileOps._loadDomainTopologiesInline(editor, sec, toposListEl);

            // Per-domain knowledge panel -- adds the small icon-button next
            // to the domain title and builds the collapsible "project
            // workspace" (branches, Jira, notes, CLI presets, ...) inside
            // `.domain-body`. Skipped for built-in sections (__bugs / __ai)
            // since those are synthetic and live outside the domain table.
            if (!sec.builtin
                && window.TopologyDomainKnowledge
                && typeof window.TopologyDomainKnowledge.mount === 'function') {
                try { window.TopologyDomainKnowledge.mount(div, sec); } catch (_) { /* best-effort */ }
            }
        }

        // Virtual rows for content shared WITH me (domains received from
        // other users + the synthetic per-file inbox). These aren't in
        // /api/sections -- they come from /api/domains -- so we stitch
        // them in here with the sharing icon + owner tooltip.
        FileOps._renderSharedInSectionsInDropdown(editor, sharingIndex);
    },

    // Produce a matching virtual "section" row for every domain shared
    // WITH the current user, plus one final row for the synthetic
    // `__shared_with_me` inbox whose entries are individual file shares
    // from possibly-many owners. Kept in a dedicated helper to keep the
    // main renderer readable; sits structurally below the user's own
    // sections so the ownership hierarchy stays obvious at a glance.
    _renderSharedInSectionsInDropdown(editor, sharingIndex) {
        const dropdown = document.getElementById('topologies-dropdown-menu');
        if (!dropdown) return;
        const anchor = document.getElementById('topology-domains-header');
        // `_renderCustomSectionsInDropdown` just inserted every legacy
        // row immediately after `anchor`, so anchor.nextSibling now
        // points at the FIRST legacy row, not the row we want to land
        // before. Walk past all legacy custom sections to find the
        // first unrelated element -- that's the correct insertion
        // point for our virtual shared-in rows.
        let insertAfter = anchor ? anchor.nextSibling : null;
        while (insertAfter
               && insertAfter.nodeType === 1
               && insertAfter.classList
               && insertAfter.classList.contains('custom-section-category')
               && !insertAfter.dataset.sharedIn) {
            insertAfter = insertAfter.nextSibling;
        }
        const mount = (insertAfter && insertAfter.parentNode) || (anchor && anchor.parentNode) || dropdown;

        const domains = sharingIndex && sharingIndex.domains ? sharingIndex.domains : [];
        const sharedInDomains = domains.filter(d => d && d.is_shared && !d.is_shared_with_me_domain);
        const inboxDomain = domains.find(d => d && d.is_shared_with_me_domain) || null;

        // Nothing received? Bail -- don't pollute the dropdown with
        // empty-state rows for users that haven't been shared anything.
        if (sharedInDomains.length === 0
            && (!inboxDomain || !inboxDomain.topology_count)) {
            return;
        }

        const virtualColor = '#a78bfa'; // consistent purple accent for
                                         // shared-in virtual rows

        const makeVirtualSection = (d, opts) => {
            const isInbox = !!(opts && opts.isInbox);
            const section = {
                id: d.id,
                name: isInbox ? 'Shared with me' : d.name,
                icon: isInbox ? 'folder' : 'network',
                color: virtualColor,
                builtin: false,
                _isSharedIn: true,
                _owner: d.owner || null,
                _ownerDisplayName: d.owner_display_name || d.owner || null,
                _permission: d.permission || (isInbox ? null : 'read'),
                _isInbox: isInbox,
                // Stash the owner's RAW domain id so per-file rows can
                // synthesize `<owner>:<raw_domain_id>:<topology_id>`
                // composites when the recipient clicks "Remove from my
                // list" on a file inside a whole-domain share (those
                // rows don't carry a composite_id from the backend).
                _sourceDomainId: d.original_domain_id || null,
                _composite: d.id,
            };
            return section;
        };

        const renderVirtualRow = (section, d, isInbox) => {
            if (!editor._domainCollapsed) editor._domainCollapsed = {};
            if (editor._domainCollapsed[section.id] === undefined) {
                // Named shared-in domains stay collapsed by default; the
                // synthetic inbox must start expanded so "Open a file below"
                // (and file rows) are visible without an extra click — the
                // v2.3 CSS also hides `.domain-body` until expanded.
                editor._domainCollapsed[section.id] = isInbox ? false : true;
            }
            const isDkDomain = FileOps._menuDark(editor);
            const div = document.createElement('div');
            div.className = 'menu-category custom-section-category shared-in-section';
            div.dataset.sectionId = section.id;
            div.dataset.sharedIn = '1';
            div.style.cssText = `background: ${section.color}${isDkDomain ? '38' : '48'}; padding: 0; border-left: 3px solid ${section.color}${isDkDomain ? '80' : 'd0'};`;

            const iconMeta = (FileOps._sectionIcons().find(i => i.id === section.icon)
                || FileOps._sectionIcons()[0]);
            const iconSvgInner = iconMeta ? iconMeta.svg : '';
            const collapsed = editor._domainCollapsed[section.id] || false;

            const ownerLabel = section._ownerDisplayName || section._owner || 'another user';
            const ownerLabelEsc = ownerLabel.replace(/</g, '&lt;').replace(/>/g, '&gt;');
            // User-facing permission label (View / Edit). Wire tokens
            // (read / write) are kept intact in section._permission for
            // downstream gating and backend posts. See
            // DEVELOPMENT_GUIDELINES.md -> "Shared Topology Permissions
            // -- View / Edit -- 2026-05-12".
            const _shareApi = (typeof window !== 'undefined') ? window.TopologyShare : null;
            const permLabelText = (_shareApi && typeof _shareApi.permissionLabel === 'function')
                ? _shareApi.permissionLabel(section._permission)
                : (section._permission === 'write' ? 'Edit' : (section._permission ? 'View' : ''));
            // Richer attribution: if we have both a display name AND a
            // distinct username/email, surface both on hover so the user
            // can disambiguate "which Alice?" without leaving the menu.
            const ownerDisplay = (section._ownerDisplayName || '').trim();
            const ownerUsername = (section._owner || '').trim();
            let ownerAttribution;
            if (ownerDisplay && ownerUsername && ownerDisplay.toLowerCase() !== ownerUsername.toLowerCase()) {
                const permTxt = permLabelText ? `, ${permLabelText}` : '';
                ownerAttribution = `${ownerDisplay} (${ownerUsername}${permTxt})`;
            } else {
                const who = ownerDisplay || ownerUsername || 'another user';
                const permTxt = permLabelText ? ` (${permLabelText})` : '';
                ownerAttribution = `${who}${permTxt}`;
            }
            const tooltipText = isInbox
                ? `Files shared with you by other users`
                : `Shared by ${ownerAttribution}`;
            // Inbox pill stays terse ("SHARED" -- it's a synthetic
            // multi-owner inbox) while named domain shares surface the
            // originator right in the pill text ("BY ALICE") so the
            // user doesn't have to hover to see who's behind it. The
            // `title` attribute is preserved on every pill for users
            // who still want the permission detail on hover.
            const sharedPillText = isInbox
                ? 'SHARED'
                : `BY ${ownerLabelEsc.toUpperCase()}`;
            const handleSvg = FileOps._sharedInIconHtml(section.color, tooltipText);
            // Per-domain View / Edit permission pill. Only rendered for
            // named domain shares (the synthetic inbox has heterogeneous
            // per-file permissions and would lie if it picked one).
            let permPillHtml = '';
            if (!isInbox && section._permission) {
                const _permClass = (section._permission === 'write') ? 'edit' : 'view';
                const _permTitle = (_shareApi && typeof _shareApi.permissionTitle === 'function')
                    ? _shareApi.permissionTitle(section._permission)
                    : (section._permission === 'write'
                        ? 'Edit: can open, modify, and save'
                        : 'View only: can open and inspect');
                const _whoLabel = ownerDisplay || ownerUsername || 'another user';
                const _permTip = `${_permTitle} -- shared by ${_whoLabel.replace(/"/g, '&quot;')}`;
                const _permIconSvg = (section._permission === 'write')
                    ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/></svg>'
                    : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
                permPillHtml = `<span class="shared-domain-perm-badge ${_permClass}" data-perm="${section._permission}" title="${_permTip.replace(/"/g, '&quot;')}">${_permIconSvg}${permLabelText}</span>`;
            }

            const btnColor = isDkDomain ? '#e2e8f0' : '#1e1e32';
            const baseBg = `${section.color}${isDkDomain ? '18' : '15'}`;
            const hoverBg = `${section.color}${isDkDomain ? '30' : '35'}`;
            const borderBg = `${section.color}${isDkDomain ? '30' : '40'}`;

            // Toolbar hint color is class-driven (styles.css `.ta-shared-toolbar-hint`)
            // so light/dark theme flips recompute without re-rendering this row.

            // Inbox has no meaningful "load domain from file" action so
            // we hide Load+Save for it; the per-file rows still work
            // individually. Regular shared-in domains support Load but
            // never Save (user doesn't own the target storage).
            const toolbarHtml = `
                <div style="display:flex;gap:4px;padding:2px 10px;align-items:center;">
                    <span class="ta-shared-toolbar-hint" style="flex:1;font-size:10px;font-weight:500;letter-spacing:0.3px;text-transform:uppercase;padding:3px 0;">
                        ${isInbox ? 'Open a file below' : 'Shared by ' + ownerLabel.replace(/</g, '&lt;')}
                    </span>
                </div>`;

            // Recipient-side "remove this shared domain" button. Only
            // surfaces on named domain shares (not on the synthetic
            // inbox, which is virtual and not actually a share row).
            // Clicking it posts to
            //   /api/domains/share/incoming/<composite>/remove
            // which drops the recipient's row from `domain_shares`
            // without touching the owner's domain or any other
            // recipient. Styled as a small pill to match the "SHARED"
            // badge so the affordance reads as a single button pair.
            const removeDomainBtnHtml = isInbox ? '' : `
                <button class="ta-remove-shared-domain"
                        title="Remove this shared domain from your list (does not affect the owner)"
                        style="background:transparent;border:1px solid ${section.color}55;border-radius:999px;padding:2px 7px 2px 6px;margin-left:4px;color:${section.color};font-size:9px;font-weight:700;letter-spacing:0.4px;text-transform:uppercase;display:inline-flex;align-items:center;gap:4px;cursor:pointer;flex-shrink:0;opacity:0.7;transition:opacity 0.15s, background 0.15s;">
                    <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><circle cx="12" cy="12" r="9"/></svg>
                    REMOVE
                </button>`;

            div.innerHTML = `
                <div class="domain-title" style="color: ${section.color}; display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 800; letter-spacing: 0.5px; padding: 8px 12px; cursor: default; user-select: none;">
                    ${handleSvg}
                    <svg viewBox="0 0 24 24" width="16" height="16" style="color:${section.color}; flex-shrink:0;">${iconSvgInner}</svg>
                    <span style="flex:1;display:flex;align-items:center;gap:6px;">
                        <span>${String(section.name || '').toUpperCase().replace(/</g, '&lt;')}</span>
                        <span title="${tooltipText.replace(/"/g, '&quot;')}"
                              style="font-size:9px;font-weight:700;letter-spacing:0.4px;color:${section.color};background:${section.color}1f;border:1px solid ${section.color}55;border-radius:999px;padding:2px 7px;text-transform:uppercase;display:inline-flex;align-items:center;gap:4px;flex-shrink:0;white-space:nowrap;max-width:160px;overflow:hidden;text-overflow:ellipsis;">
                            ${sharedPillText}
                        </span>
                        ${permPillHtml}
                        ${removeDomainBtnHtml}
                    </span>
                    <svg class="domain-chevron" viewBox="0 0 24 24" width="12" height="12" style="color:${section.color}; flex-shrink:0; opacity:0.6; transition: transform 0.2s; transform: rotate(${collapsed ? '-90deg' : '0deg'});">
                        <polyline points="6 9 12 15 18 9" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <div class="domain-body" style="display: ${collapsed ? 'none' : 'block'}; padding: 0 0 6px;">
                    ${toolbarHtml}
                    <div class="domain-topos-list" style="max-height:160px;overflow-y:auto;"></div>
                </div>
            `;

            // Native tooltip on the handle + SHARED pill is already
            // wired via the <title> SVG element and the `title` attribute.
            // The title row collapses on click, identical to legacy rows.
            const titleHandle = div.querySelector('.domain-title');
            const bodyEl = div.querySelector('.domain-body');
            const chevron = div.querySelector('.domain-chevron');
            titleHandle.addEventListener('click', (e) => {
                // The "Remove this shared domain" button lives inside
                // the title handle -- clicking it must NOT also toggle
                // the collapse, otherwise the user sees the body flicker
                // open while the confirm bar mounts.
                if (e.target && typeof e.target.closest === 'function'
                    && e.target.closest('.ta-remove-shared-domain')) {
                    return;
                }
                if (e.target && typeof e.target.closest === 'function'
                    && e.target.closest('.shared-domain-confirm-bar')) {
                    return;
                }
                e.stopPropagation();
                const open = bodyEl.style.display !== 'none';
                bodyEl.style.display = open ? 'none' : 'block';
                editor._domainCollapsed[section.id] = open;
                if (chevron) chevron.style.transform = `rotate(${open ? '-90deg' : '0deg'})`;
                if (!open) {
                    FileOps._loadDomainTopologiesInline(editor, section, div.querySelector('.domain-topos-list'));
                }
                // _loadDomainTopologiesInline re-fits once its own rows
                // paint, but collapse-only (open === true) has no row
                // render to hook onto, so trigger the fit here directly.
                if (open) requestAnimationFrame(() => FileOps._fitDropdownToContent());
            });

            // Domain-title share surfaces (handle SVG, "SHARED" / "BY X"
            // pill) also get the custom hover bubble so the user sees
            // permission + owner immediately -- no more 1.5s native
            // title-attr delay. The handle SVG has a `<title>` CHILD
            // element for accessibility but no `title` ATTRIBUTE, so
            // mirror the text onto the attribute where
            // `_attachHoverTip` reads it from.
            const handleEl = div.querySelector('.domain-title .dd-shared-in');
            if (handleEl && !handleEl.hasAttribute('title')) {
                handleEl.setAttribute('title', tooltipText);
            }
            if (handleEl) FileOps._attachHoverTip(handleEl);
            div.querySelectorAll('.domain-title [title]').forEach(pill => {
                if (pill !== handleEl) FileOps._attachHoverTip(pill);
            });

            const removeDomainBtn = div.querySelector('.ta-remove-shared-domain');
            if (removeDomainBtn) {
                FileOps._attachHoverTip(removeDomainBtn);
                removeDomainBtn.addEventListener('mouseenter', () => {
                    removeDomainBtn.style.opacity = '1';
                    removeDomainBtn.style.background = `${section.color}15`;
                });
                removeDomainBtn.addEventListener('mouseleave', () => {
                    removeDomainBtn.style.opacity = '0.7';
                    removeDomainBtn.style.background = 'transparent';
                });
                removeDomainBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    const existing = div.querySelector('.shared-domain-confirm-bar');
                    if (existing) existing.remove();
                    const bar = document.createElement('div');
                    bar.className = 'shared-domain-confirm-bar';
                    const isDark = FileOps._menuDark(editor);
                    bar.style.cssText = `display:flex;align-items:center;gap:6px;padding:6px 12px;margin:0 10px 6px;background:${isDark ? 'rgba(167,139,250,0.12)' : 'rgba(167,139,250,0.10)'};border-left:2px solid ${section.color};border-radius:4px;`;
                    const ownerDisp = (section._ownerDisplayName || section._owner || 'the owner')
                        .toString().replace(/</g, '&lt;');
                    const nameDisp = String(section.name || '').replace(/</g, '&lt;');
                    bar.innerHTML = `
                        <span style="flex:1;font-size:10.5px;color:${isDark ? 'rgba(226,232,240,0.9)' : '#1e1e32'};">
                            Remove "<b>${nameDisp}</b>" from your Shared-with-me list?<br/>
                            <span style="opacity:0.7;font-size:9.5px;">${ownerDisp} keeps the original — you can always be re-shared.</span>
                        </span>
                        <button class="sdc-yes" style="padding:4px 10px;background:${section.color};border:none;border-radius:4px;color:#fff;font-size:10px;font-weight:600;cursor:pointer;">Remove</button>
                        <button class="sdc-no" style="padding:4px 8px;background:${isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)'};border:1px solid ${isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.12)'};border-radius:4px;color:${isDark ? '#94a3b8' : '#475569'};font-size:10px;cursor:pointer;">Cancel</button>
                    `;
                    titleHandle.after(bar);
                    bar.querySelector('.sdc-no').onclick = (ev) => { ev.stopPropagation(); bar.remove(); };
                    bar.querySelector('.sdc-yes').onclick = async (ev) => {
                        ev.stopPropagation();
                        bar.remove();
                        const ok = await FileOps._removeIncomingDomainShare(editor, section);
                        if (ok) {
                            div.remove();
                        }
                    };
                });
            }

            if (insertAfter) mount.insertBefore(div, insertAfter);
            else if (anchor) anchor.after(div);
            else mount.appendChild(div);

            if (!collapsed) {
                FileOps._loadDomainTopologiesInline(editor, section, div.querySelector('.domain-topos-list'));
            }

            // Shared-in domains also get the knowledge workspace -- the
            // backend resolves the visibility scope automatically
            // (owner-public knowledge is readable, viewer-private annotations
            // are writable). The synthetic __shared_with_me inbox is NOT a
            // real domain, so it's skipped.
            if (!isInbox
                && section.id !== '__shared_with_me'
                && window.TopologyDomainKnowledge
                && typeof window.TopologyDomainKnowledge.mount === 'function') {
                try { window.TopologyDomainKnowledge.mount(div, section); } catch (_) { /* best-effort */ }
            }
        };

        // Render each shared-in domain (owner-attributed, whole-domain).
        sharedInDomains.forEach(d => {
            const sec = makeVirtualSection(d, { isInbox: false });
            renderVirtualRow(sec, d, false);
        });

        // Finally the synthetic per-file inbox. Only render when it
        // has content so the dropdown stays free of empty affordances.
        if (inboxDomain && inboxDomain.topology_count > 0) {
            const sec = makeVirtualSection(inboxDomain, { isInbox: true });
            renderVirtualRow(sec, inboxDomain, true);
        }
    },

    // Inline "quick edit" panel for a domain -- historically opened from
    // the per-row settings gear inside `.domain-body > .domain-quickedit-wrap`.
    // That gear was retired on 2026-04-22 to stop the double-cog render
    // (see `_renderCustomSectionsInDropdown`). The same form is now
    // reachable via the "Edit appearance" accordion in the unified
    // knowledge panel (topology-domain-knowledge.js), which routes
    // through the shared builder below.
    //
    // This wrapper stays exported for two reasons:
    //   1. Back-compat for any caller that still targets the quickedit-
    //      wrap slot (the `<div class="domain-quickedit-wrap">` slot
    //      remains in the row so programmatic callers keep working).
    //   2. It keeps the close-on-second-click + single-panel-at-a-time
    //      invariant that the old gear relied on.
    _openDomainQuickEdit(editor, sec, rowEl, settingsBtnEl) {
        const wrap = rowEl && rowEl.querySelector('.domain-quickedit-wrap');
        if (!wrap) return;

        // Clicking the gear while its panel is open should close it.
        const existing = wrap.querySelector('.domain-quickedit');
        if (existing) {
            existing.remove();
            if (settingsBtnEl) settingsBtnEl.classList.remove('is-open');
            return;
        }

        // One quickedit at a time, anywhere in the dropdown. Keeps the
        // focus on the thing the user last asked to edit.
        document.querySelectorAll('.domain-quickedit').forEach(el => el.remove());
        document.querySelectorAll('.domain-settings-btn.is-open')
            .forEach(b => b.classList.remove('is-open'));

        if (settingsBtnEl) settingsBtnEl.classList.add('is-open');

        const form = FileOps._buildDomainAppearanceForm(editor, sec, rowEl, {
            onClose: () => {
                if (settingsBtnEl) settingsBtnEl.classList.remove('is-open');
            },
        });
        if (!form) return;
        wrap.appendChild(form);
        // Autofocus the name input when the form is editable. The builder
        // intentionally doesn't autofocus so the knowledge-panel accordion
        // path doesn't steal focus from the tab row on first open.
        if (!sec.builtin) {
            const nameInput = form.querySelector('.dq-name');
            if (nameInput) {
                setTimeout(() => {
                    try { nameInput.focus({ preventScroll: true }); } catch (_) {}
                }, 0);
            }
        }
    },

    // Shared builder for the rename / icon / colour editor. Used by both
    // `_openDomainQuickEdit` (legacy inline slot) and the "Edit appearance"
    // accordion in the per-domain knowledge panel. Returns a detached
    // `<div class="domain-quickedit">` element with save/cancel/live-preview
    // wired; the caller is responsible for inserting it into the DOM.
    //
    // Options:
    //   onClose()     -- fired after the panel removes itself (save success,
    //                    cancel, or explicit close). Used by callers that
    //                    manage sibling UI (e.g. un-styling an open gear).
    //   showCancel    -- when false, hides the Cancel button. The accordion
    //                    in the knowledge panel doesn't need it because the
    //                    accordion head doubles as a collapse control.
    _buildDomainAppearanceForm(editor, sec, rowEl, opts) {
        if (!editor || !sec) return null;
        opts = opts || {};
        const showCancel = opts.showCancel !== false;
        const onClose = typeof opts.onClose === 'function' ? opts.onClose : null;
        // onPreview fires on every live-preview change (color/icon/name). The
        // knowledge drawer uses it to re-tint its own header because the
        // drawer is no longer a descendant of rowEl (so it can't inherit
        // `--row-accent` from the row element automatically).
        const onPreview = typeof opts.onPreview === 'function' ? opts.onPreview : null;

        const icons = FileOps._sectionIcons();
        const colors = FileOps._sectionColors();
        const lockedName = !!sec.builtin;

        let editIcon = sec.icon || (icons[0] && icons[0].id);
        let editColor = sec.color || (colors[0] || '#6366f1');

        const origName = sec.name || '';
        const origIcon = sec.icon || editIcon;
        const origColor = sec.color || editColor;

        // Live-preview DOM refs (computed once, reused on every change).
        const titleNameEl = rowEl.querySelector('.domain-title-name');
        const titleRootEl = rowEl.querySelector('.domain-title');
        const titleIconEl = rowEl.querySelector('.domain-title > .domain-row-icon')
            || rowEl.querySelector('.domain-title > svg[width="16"]')
            || rowEl.querySelector('.domain-title > svg[width="17"]');
        const chevronEl = rowEl.querySelector('.domain-chevron');

        const applyColorPreview = (color) => {
            rowEl.style.setProperty('--row-accent', color);
            rowEl.style.borderLeftColor = color;
            const isDk = FileOps._menuDark(editor);
            rowEl.style.background = `${color}${isDk ? '38' : '48'}`;
            if (titleNameEl) titleNameEl.style.color = color;
            if (titleRootEl) titleRootEl.style.color = color;
            if (titleIconEl) titleIconEl.style.color = color;
            if (chevronEl) chevronEl.style.color = color;
            if (onPreview) onPreview({ color, icon: editIcon, name: null });
        };
        const applyIconPreview = (iconId) => {
            const ic = icons.find(i => i.id === iconId) || icons[0];
            if (titleIconEl) titleIconEl.innerHTML = ic.svg;
            if (onPreview) onPreview({ color: null, icon: iconId, name: null });
        };
        const applyNamePreview = (name) => {
            if (titleNameEl) titleNameEl.textContent = (name || 'Untitled').toUpperCase();
            if (onPreview) onPreview({ color: null, icon: null, name });
        };

        const escName = (origName || '').replace(/"/g, '&quot;');
        const nameBlock = lockedName
            ? `<input class="dq-name" type="text" value="${escName}" readonly tabindex="-1" title="Built-in domain name cannot be changed">
                <div class="dq-hint" aria-hidden="true">
                    <svg viewBox="0 0 24 24" width="9" height="9" fill="none" stroke="currentColor" stroke-width="2.4"><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3" stroke-linecap="round"/></svg>
                    Built-in domain name is fixed. Icon and colour are editable.
                </div>`
            : `<input class="dq-name" type="text" value="${escName}" placeholder="Domain name" aria-label="Domain name" maxlength="60">`;

        const panel = document.createElement('div');
        panel.className = 'domain-quickedit';
        panel.onclick = (e) => e.stopPropagation();
        panel.onmousedown = (e) => e.stopPropagation();
        panel.innerHTML = `
            <div class="dq-label">Name</div>
            ${nameBlock}
            <div class="dq-label">Icon</div>
            <div class="dq-grid" role="listbox" aria-label="Domain icon">
                ${icons.map(ic => `<button type="button" class="dq-icon-btn${ic.id === editIcon ? ' is-active' : ''}" data-icon="${ic.id}" role="option" aria-selected="${ic.id === editIcon}" title="${ic.id}">
                    <svg viewBox="0 0 24 24" style="color: ${ic.id === editIcon ? editColor : 'currentColor'}; stroke: ${ic.id === editIcon ? editColor : 'currentColor'};">${ic.svg}</svg>
                </button>`).join('')}
            </div>
            <div class="dq-label">Colour</div>
            <div class="dq-grid" role="listbox" aria-label="Domain colour">
                ${colors.map(c => `<button type="button" class="dq-color-btn${c === editColor ? ' is-active' : ''}" data-color="${c}" role="option" aria-selected="${c === editColor}" style="background: ${c};" title="${c}"></button>`).join('')}
            </div>
            <div class="dq-footer">
                <button type="button" class="dq-save">Save changes</button>
                ${showCancel ? '<button type="button" class="dq-cancel">Cancel</button>' : ''}
            </div>
        `;

        const nameInput = panel.querySelector('.dq-name');
        if (!lockedName && nameInput) {
            nameInput.addEventListener('input', () => {
                applyNamePreview(nameInput.value);
            });
            nameInput.addEventListener('keydown', (ev) => {
                ev.stopPropagation();
                if (ev.key === 'Enter') {
                    ev.preventDefault();
                    const sBtn = panel.querySelector('.dq-save');
                    if (sBtn) sBtn.click();
                } else if (ev.key === 'Escape') {
                    ev.preventDefault();
                    const cBtn = panel.querySelector('.dq-cancel');
                    if (cBtn) cBtn.click();
                    else {
                        // No cancel button (host owns collapse UX) -- restore
                        // live-preview to the original values and notify the
                        // host so it can collapse / hide the form.
                        applyColorPreview(origColor);
                        applyIconPreview(origIcon);
                        applyNamePreview(origName);
                        panel.remove();
                        if (onClose) onClose('cancel');
                    }
                }
            });
        }

        const refreshIconActive = () => {
            panel.querySelectorAll('.dq-icon-btn').forEach(b => {
                const active = b.dataset.icon === editIcon;
                b.classList.toggle('is-active', active);
                b.setAttribute('aria-selected', String(active));
                const svg = b.querySelector('svg');
                if (svg) {
                    svg.style.color = active ? editColor : 'currentColor';
                    svg.style.stroke = active ? editColor : 'currentColor';
                }
            });
        };
        const refreshColorActive = () => {
            panel.querySelectorAll('.dq-color-btn').forEach(b => {
                const active = b.dataset.color === editColor;
                b.classList.toggle('is-active', active);
                b.setAttribute('aria-selected', String(active));
            });
        };

        panel.querySelectorAll('.dq-icon-btn').forEach(btn => {
            btn.addEventListener('click', (ev) => {
                ev.stopPropagation();
                editIcon = btn.dataset.icon;
                refreshIconActive();
                applyIconPreview(editIcon);
            });
        });
        panel.querySelectorAll('.dq-color-btn').forEach(btn => {
            btn.addEventListener('click', (ev) => {
                ev.stopPropagation();
                editColor = btn.dataset.color;
                refreshColorActive();
                refreshIconActive();
                applyColorPreview(editColor);
            });
        });

        const closePanel = (reason) => {
            panel.remove();
            if (onClose) onClose(reason || 'close');
        };

        const cancelBtn = panel.querySelector('.dq-cancel');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', (ev) => {
                ev.stopPropagation();
                applyColorPreview(origColor);
                applyIconPreview(origIcon);
                applyNamePreview(origName);
                closePanel('cancel');
            });
        }

        panel.querySelector('.dq-save').addEventListener('click', async (ev) => {
            ev.stopPropagation();
            const typedName = nameInput && !lockedName ? nameInput.value.trim() : sec.name;
            const newName = lockedName ? sec.name : typedName;
            if (!newName) { editor.showToast('Enter a domain name', 'warning'); return; }
            if (!lockedName) {
                if (newName.toLowerCase() === 'dnaas'
                    && (sec.name || '').toLowerCase() !== 'dnaas') {
                    editor.showToast('"DNAAS" is a reserved domain name', 'warning');
                    return;
                }
                const dup = (editor._customSections || []).some(s =>
                    s.id !== sec.id
                    && (s.name || '').toLowerCase() === newName.toLowerCase()
                );
                if (dup) {
                    editor.showToast(`Domain "${newName}" already exists`, 'warning');
                    return;
                }
            }
            const saveBtn = panel.querySelector('.dq-save');
            saveBtn.disabled = true;
            const origLabel = saveBtn.textContent;
            saveBtn.textContent = 'Saving...';
            try {
                const resp = await fetch('/api/sections/update', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: sec.id, name: newName, icon: editIcon, color: editColor })
                });
                // Some older deploys return 200 OK with {error: "..."};
                // newer ones return the updated section. Either way we
                // tolerate both shapes so the UI never silently stalls.
                let ok = resp.ok;
                let errMsg = '';
                try {
                    const body = await resp.json();
                    if (body && body.error) { ok = false; errMsg = body.error; }
                } catch (_) {}
                if (!ok) throw new Error(errMsg || ('HTTP ' + resp.status));
                await FileOps.loadCustomSections(editor);
                // The re-render replaces rowEl; after re-render, if the
                // current topology belongs to this domain, re-publish
                // the top-bar indicator with the new identity.
                try {
                    const raw = localStorage.getItem('topo_active');
                    if (raw) {
                        const d = JSON.parse(raw);
                        if (d && d.sectionId === sec.id && d.name) {
                            FileOps.updateTopologyIndicator(
                                d.name, newName, editColor, sec.id, d.shared || null,
                            );
                        }
                    }
                } catch (_) {}
                try {
                    document.dispatchEvent(new CustomEvent('topology-domains:changed', {
                        detail: { reason: 'domain-updated', domainId: sec.id, domainName: newName },
                    }));
                } catch (_) {}
                editor.showToast(`Domain "${newName}" updated`, 'success');
                // The re-render triggered above typically destroys this
                // panel, but when the host survives the re-render (e.g.
                // the panel is mounted outside the row being rebuilt)
                // we still want the form to collapse cleanly. onClose
                // is called last so the host can remove its accordion.
                if (onClose) {
                    try { onClose('saved'); } catch (_) {}
                }
            } catch (e) {
                editor.showToast('Update failed: ' + (e && e.message || e), 'error');
                saveBtn.disabled = false;
                saveBtn.textContent = origLabel;
            }
        });

        return panel;
    },

    // Writes the topology count into every `.domain-count-badge` that
    // pins itself to `sectionId`. Badges render empty (hidden by CSS)
    // when the domain has 0 topologies so empty rows stay uncluttered.
    // The tooltip spells out "N topologies" for users who pause on the
    // chip with their pointer. Safe to call with sectionId values that
    // no longer exist in the DOM -- the querySelectorAll just returns
    // an empty NodeList and the function bails silently.
    _setDomainCountBadge(sectionId, count) {
        if (!sectionId) return;
        const safe = (typeof CSS !== 'undefined' && CSS.escape)
            ? CSS.escape(sectionId)
            : String(sectionId).replace(/"/g, '\\"');
        const badges = document.querySelectorAll(
            `.domain-count-badge[data-count-for="${safe}"]`,
        );
        const n = Math.max(0, Number(count) || 0);
        badges.forEach(b => {
            if (n > 0) {
                b.textContent = String(n);
                b.setAttribute('title', `${n} ${n === 1 ? 'topology' : 'topologies'}`);
            } else {
                b.textContent = '';
                b.removeAttribute('title');
            }
        });
    },

    _ensureDomainTopologiesRendered(editor, section, container) {
        if (!editor || !section || !container) return;
        const key = String(section.id || '');
        if (!key) return;
        if (container.dataset.domainToposLoadingFor === key) return;
        if (container.dataset.domainToposLoadedFor === key
            && container.innerHTML.trim()) {
            return;
        }
        FileOps._loadDomainTopologiesInline(editor, section, container);
    },

    async _loadDomainTopologiesInline(editor, section, container) {
        // Virtual rows (shared-in domain from another user, or the synthetic
        // "Shared with me" inbox) live in user_store and must go through the
        // /api/domains/* endpoints -- /api/sections has no idea they exist.
        if (section && section._isSharedIn) {
            return FileOps._loadSharedInDomainTopologiesInline(editor, section, container);
        }
        if (!section || !container) return;
        const sectionKey = String(section.id || '');
        try {
            container.dataset.domainToposLoadingFor = sectionKey;
            delete container.dataset.domainToposFailed;
            if (!container.innerHTML.trim()) {
                container.innerHTML = `<div style="padding:4px 12px 6px;font-size:10px;color:#64748b;font-style:italic;">Loading topologies...</div>`;
            }
            const resp = await FileOps._authFetch(`/api/sections/${encodeURIComponent(section.id)}/topologies`);
            const data = await resp.json();
            const topos = data.topologies || [];
            if (!container.isConnected) return;
            container.dataset.domainToposLoadedFor = sectionKey;
            // Publish the count to the row header chip (domain-row v2).
            FileOps._setDomainCountBadge(section.id, topos.length);
            if (topos.length === 0) {
                container.innerHTML = `<div style="padding:4px 12px 6px;font-size:10px;color:#64748b;font-style:italic;">No topologies yet</div>`;
                return;
            }
            // Hand the sharing index + matched own-domain down so the file
            // rows can render "shared-out" badges for every file I've
            // published to other users. Cache is already primed by
            // loadCustomSections -- this is just a lookup.
            const sharingIndex = FileOps._buildSharingIndex();
            const ownDomain = FileOps._findOwnDomainForSection(section, sharingIndex);
            FileOps._renderTopoEntries(editor, container, topos, section.color, {
                sectionId: section.id,
                section: section,
                ownDomain: ownDomain,
                sharingIndex: sharingIndex,
                loadFn: async (filename) => {
                    const dropdown = document.getElementById('topologies-dropdown-menu');
                    if (dropdown) dropdown.style.display = 'none';
                    let loadToken = null;
                    try {
                        const topoName = filename.replace(/\.json$/i, '');
                        loadToken = FileOps._beginTopologyLoad(editor, {
                            name: topoName,
                            filename,
                            domain: section.name,
                            sectionId: section.id,
                        });
                        const r = await fetch(`/api/sections/${section.id}/topologies/${filename}`);
                        if (!FileOps._isTopologyLoadCurrent(editor, loadToken)) return;
                        const d = await r.json();
                        if (d.error) {
                            FileOps._cancelTopologyLoad(editor, loadToken);
                            editor.showToast(d.error, 'error');
                            return;
                        }
                        if (!FileOps._isTopologyLoadCurrent(editor, loadToken)) return;
                        const loaded = FileOps._loadIntoEditor(editor, d, {
                            name: topoName,
                            filename,
                            domain: section.name,
                            color: section.color,
                            sectionId: section.id,
                            loadToken,
                        });
                        if (!loaded) return;
                        // Best-effort registration with TopologySync so
                        // the owner also sees live updates when a write-
                        // permission recipient saves this topology. The
                        // multi-user row only exists if the file has been
                        // shared before -- otherwise the mapping is empty
                        // and we silently skip sync wiring (legacy SSE
                        // reload path still covers that case).
                        if (window.TopologySync && window.TopologySync.setActive) {
                            try {
                                const mr = await fetch('/api/sections/'
                                    + encodeURIComponent(section.id)
                                    + '/_mirror-map/'
                                    + encodeURIComponent(filename));
                                const mm = mr.ok ? await mr.json() : {};
                                if (mm && mm.mirrored && mm.topology_id) {
                                    const meUser = (window.TopologyAuth
                                        && window.TopologyAuth.getUser
                                        && window.TopologyAuth.getUser())
                                        || {};
                                    window.TopologySync.setActive({
                                        owner: meUser.username || '',
                                        domain_id: mm.domain_id,
                                        topology_id: mm.topology_id,
                                        name: topoName,
                                        updated_at: mm.updated_at || '',
                                        is_shared: false,
                                        permission: 'write',
                                        domain_name: section.name,
                                        section_id: section.id,
                                        color: section.color,
                                    });
                                } else {
                                    window.TopologySync.clearActive();
                                }
                            } catch (_) { /* sync is best-effort */ }
                        }
                        editor.showToast(`Loaded from ${section.name}`, 'success');
                    } catch (err) {
                        if (loadToken && !FileOps._isTopologyLoadCurrent(editor, loadToken)) return;
                        if (loadToken) FileOps._cancelTopologyLoad(editor, loadToken);
                        editor.showToast(err.message, 'error');
                    }
                },
                renameFn: async (oldFile, newName) => {
                    try {
                        const r = await fetch(`/api/sections/${section.id}/topologies/${oldFile}/rename`, {
                            method: 'POST', headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ name: newName })
                        });
                        const result = await r.json();
                        if (result.error) { editor.showToast('Rename failed: ' + result.error, 'error'); return; }
                        editor.showToast('Renamed', 'success');
                        FileOps._loadDomainTopologiesInline(editor, section, container);
                    } catch (e) { editor.showToast('Rename failed: ' + e.message, 'error'); }
                },
                deleteFn: async (filename) => {
                    // Snapshot whether the file we're about to delete
                    // is the topology the user is currently editing.
                    // Two signals are checked so we catch both load
                    // paths:
                    //   1. localStorage.topo_active -- written by every
                    //      `updateTopologyIndicator` call.
                    //   2. TopologySync.getActive() -- the multi-user
                    //      live-sync hub; set when a mirrored row
                    //      exists for this file.
                    // We compare against the deleted filename's basename
                    // and also against the sanitized form of the active
                    // name so renames + non-ascii characters don't slip
                    // past the check.
                    const baseDeleted = String(filename || '').replace(/\.json$/i, '');
                    let activeMeta = null;
                    try { activeMeta = JSON.parse(localStorage.getItem('topo_active')); } catch (_) {}
                    const sanitizedActiveName = (activeMeta && activeMeta.name)
                        ? FileOps._sanitizeTopologyBasename(activeMeta.name)
                        : '';
                    const localMatch = !!(activeMeta
                        && activeMeta.sectionId === section.id
                        && (activeMeta.name === baseDeleted
                            || sanitizedActiveName === baseDeleted));
                    let syncMatch = false;
                    try {
                        const sa = (window.TopologySync && window.TopologySync.getActive)
                            ? window.TopologySync.getActive() : null;
                        if (sa && sa.section_id === section.id) {
                            const saName = sa.name || '';
                            syncMatch = (saName === baseDeleted
                                || FileOps._sanitizeTopologyBasename(saName) === baseDeleted);
                        }
                    } catch (_) {}
                    const isCurrent = localMatch || syncMatch;

                    try {
                        const r = await fetch(`/api/sections/${section.id}/topologies/${filename}/delete-file`, { method: 'POST' });
                        const res = await r.json();
                        if (res.error) { editor.showToast('Delete failed: ' + res.error, 'error'); return; }
                        editor.showToast('Deleted', 'success');

                        // If the user just deleted the topology they
                        // were viewing, wipe the canvas and switch to
                        // the neutral General (no-domain) indicator
                        // so the next Save click opens the domain
                        // picker. Without this the canvas would keep
                        // showing the now-phantom topology and Quick
                        // Save would happily resurrect it under the
                        // same domain we just removed it from.
                        if (isCurrent) {
                            try { editor.performClearCanvas(); } catch (_) {}
                            try {
                                if (window.TopologySync && window.TopologySync.clearActive) {
                                    window.TopologySync.clearActive();
                                }
                            } catch (_) {}
                            FileOps.showGeneralTopologyIndicator('Untitled');
                            editor.showToast(
                                'Topology deleted -- canvas detached. Save to pick a new domain.',
                                'info',
                            );
                        }

                        FileOps._loadDomainTopologiesInline(editor, section, container);
                    } catch (e) { editor.showToast('Delete failed: ' + e.message, 'error'); }
                }
            });
        } catch (_) {
            if (container && container.isConnected) {
                container.dataset.domainToposFailed = '1';
                if (!container.innerHTML.trim()
                    || container.textContent.includes('Loading topologies')) {
                    container.innerHTML = `<div style="padding:4px 12px;font-size:10px;color:#ef4444;">Topology list temporarily unavailable. Existing topologies were not deleted.</div>`;
                }
            }
        } finally {
            if (container) delete container.dataset.domainToposLoadingFor;
        }
    },

    // Companion to _loadDomainTopologiesInline for virtual rows created by
    // _renderCustomSectionsInDropdown to surface shared-IN content. We hit
    // /api/domains/{id}/topologies because the files actually live in
    // user_store, NOT in /api/sections/<id>/topologies.
    async _loadSharedInDomainTopologiesInline(editor, section, container) {
        if (!section || !container) return;
        const sectionKey = String(section.id || '');
        try {
            container.dataset.domainToposLoadingFor = sectionKey;
            delete container.dataset.domainToposFailed;
            if (!container.innerHTML.trim()) {
                container.innerHTML = `<div style="padding:4px 12px 6px;font-size:10px;color:#64748b;font-style:italic;">Loading shared topologies...</div>`;
            }
            const authFetch = (window.TopologyAuth && window.TopologyAuth.authFetch)
                ? window.TopologyAuth.authFetch
                : (url, opts) => fetch(url, opts);
            const resp = await authFetch('/api/domains/' + encodeURIComponent(section.id) + '/topologies');
            if (!resp.ok) {
                container.dataset.domainToposFailed = '1';
                if (!container.innerHTML.trim()
                    || container.textContent.includes('Loading shared topologies')) {
                    container.innerHTML = `<div style="padding:4px 12px;font-size:10px;color:#ef4444;">Shared topology list temporarily unavailable. Nothing was deleted.</div>`;
                }
                return;
            }
            let topos = await resp.json();
            if (!container.isConnected) return;
            if (!Array.isArray(topos)) topos = [];
            container.dataset.domainToposLoadedFor = sectionKey;
            if (topos.length === 0) {
                container.innerHTML = `<div style="padding:4px 12px 6px;font-size:10px;color:#64748b;font-style:italic;">No shared topologies</div>`;
                return;
            }
            // The user_store returns topologies with `id` + `name` (no
            // filename). _renderTopoEntries expects filename so we
            // synthesize one using the legacy sanitization rule.
            topos = topos.map(t => ({
                name: t.name,
                filename: FileOps._sanitizeTopologyBasename(t.name) + '.json',
                modified: t.updated_at ? (new Date(t.updated_at).getTime() / 1000) : null,
                id: t.id,
                owner: t.owner || section._owner,
                owner_display_name: t.owner_display_name || section._ownerDisplayName,
                permission: t.permission || section._permission,
                is_shared_with_me: true,
                _raw: t
            }));
            FileOps._renderTopoEntries(editor, container, topos, section.color, {
                sectionId: section.id,
                section: section,
                isSharedIn: true,
                ownerLabel: section._ownerDisplayName || section._owner || 'another user',
                loadFn: async (filename, row) => {
                    const dropdown = document.getElementById('topologies-dropdown-menu');
                    if (dropdown) dropdown.style.display = 'none';
                    // Resolve topology id back from the synthesized
                    // filename (row.dataset.filename). The mapping is
                    // deterministic so this is safe.
                    const match = topos.find(x => x.filename === filename);
                    if (!match || !match.id) { editor.showToast('Shared topology not found', 'error'); return; }
                    const sharedInfo = {
                        isSharedIn: !!section._isSharedIn,
                        isInbox: !!section._isInbox,
                        owner: section._owner || null,
                        ownerDisplay: section._ownerDisplayName || null,
                        permission: section._permission || null
                    };
                    const loadToken = FileOps._beginTopologyLoad(editor, {
                        name: match.name,
                        filename,
                        domain: section.name,
                        sectionId: section.id,
                        topologyId: match.id,
                        shared: sharedInfo,
                    });
                    try {
                        const r = await authFetch('/api/domains/' + encodeURIComponent(section.id)
                            + '/topologies/' + encodeURIComponent(match.id));
                        if (!r.ok) {
                            const err = await r.json().catch(() => ({}));
                            FileOps._cancelTopologyLoad(editor, loadToken);
                            editor.showToast(err.detail || 'Failed to open shared topology', 'error');
                            return;
                        }
                        if (!FileOps._isTopologyLoadCurrent(editor, loadToken)) return;
                        const payload = await r.json();
                        const data = payload.data || payload;
                        if (!FileOps._isTopologyLoadCurrent(editor, loadToken)) return;
                        const loaded = FileOps._loadIntoEditor(editor, data, {
                            name: match.name,
                            filename,
                            domain: section.name,
                            color: section.color,
                            sectionId: section.id,
                            topologyId: match.id,
                            shared: sharedInfo,
                            loadToken,
                        });
                        if (!loaded) return;
                        // Register with the live-sync hub so WebSocket
                        // topology_event frames from other collaborators
                        // trigger a canvas reload + refreshed Activity Log.
                        // Without this, shared recipients never see the
                        // originator's edits without a manual F5.
                        if (window.TopologySync && window.TopologySync.setActive) {
                            try {
                                window.TopologySync.setActive({
                                    owner: section._owner || '',
                                    domain_id: section.id,
                                    topology_id: match.id,
                                    name: match.name,
                                    updated_at: (payload.updated_at
                                        || (payload.meta && payload.meta.updated_at)
                                        || (match._raw && match._raw.updated_at)
                                        || ''),
                                    is_shared: true,
                                    permission: match.permission || section._permission || 'read',
                                    domain_name: section.name,
                                    color: section.color,
                                });
                            } catch (_) { /* sync is best-effort */ }
                        }
                        editor.showToast(`Loaded ${match.name} (shared by ${section._ownerDisplayName || section._owner || 'user'})`, 'success');
                    } catch (err) {
                        if (!FileOps._isTopologyLoadCurrent(editor, loadToken)) return;
                        FileOps._cancelTopologyLoad(editor, loadToken);
                        editor.showToast(err.message, 'error');
                    }
                },
                // Rename / delete aren't permitted on shared-in content;
                // the backend rejects them. Provide no-ops that surface a
                // helpful toast so the UI affordances stay consistent.
                renameFn: async () => {
                    editor.showToast('Renaming is owner-only on shared topologies; ask the owner to rename it', 'warning');
                },
                deleteFn: async () => {
                    editor.showToast('You cannot delete topologies that were shared with you', 'warning');
                }
            });
        } catch (_) {
            if (container && container.isConnected) {
                container.dataset.domainToposFailed = '1';
                container.innerHTML = `<div style="padding:4px 12px;font-size:10px;color:#ef4444;">Failed to load shared topologies</div>`;
            }
        } finally {
            if (container) delete container.dataset.domainToposLoadingFor;
        }
    },

    async saveToSection(editor, section, topoName) {
        if (editor.objects.length === 0) { editor.showToast('Nothing to save', 'warning'); return; }
        const name = topoName || prompt(`Save to "${section.name}" as:`, 'topology_' + Date.now());
        if (!name) return;
        try {
            const result = await FileOps._sectionSaveWithConflict(
                editor,
                section.id,
                { name, topology: FileOps.generateTopologyData(editor) },
                null,
            );
            if (result && !result.error && !result.conflict && !result.quota) {
                editor.showToast(`Saved to ${section.name}`, 'success');
                FileOps._markTopologyClean(editor, 'save-to-section');
            }
        } catch (e) { editor.showToast('Save failed: ' + e.message, 'error'); }
    },

    async loadFromSection(editor, section) {
        try {
            const resp = await fetch(`/api/sections/${section.id}/topologies`);
            const data = await resp.json();
            const topos = data.topologies || [];
            if (topos.length === 0) { editor.showToast(`No topologies in domain "${section.name}"`, 'info'); return; }
            FileOps._showSectionTopologyPicker(editor, section, topos);
        } catch (e) { editor.showToast('Load failed: ' + e.message, 'error'); }
    },

    _showSectionTopologyPicker(editor, section, topos) {
        const existing = document.getElementById('section-topo-picker');
        if (existing) existing.remove();
        
        const div = document.createElement('div');
        div.id = 'section-topo-picker';
        div.className = 'liquid-glass-dropdown';
        div.onclick = (e) => e.stopPropagation();
        
        const anchor = document.getElementById('btn-topologies') || document.querySelector('.top-bar');
        const rect = anchor ? anchor.getBoundingClientRect() : { left: 120, bottom: 48 };
        div.style.cssText = `display:block;position:fixed;left:${rect.left}px;top:${rect.bottom+4}px;z-index:1000000;min-width:260px;max-height:380px;overflow-y:auto;`;
        
        let html = `<div style="font-size:10px;font-weight:600;padding:6px 12px 4px;text-transform:uppercase;letter-spacing:0.8px;color:${section.color};">${section.name}</div>`;
        topos.forEach(t => {
            html += `<button class="liquid-menu-item sec-topo-item" data-filename="${t.filename}" style="border-left:3px solid ${section.color};color:${section.color};">${t.name}</button>`;
        });
        div.innerHTML = html;
        
        div.querySelectorAll('.sec-topo-item').forEach(el => {
            el.onclick = async () => {
                div.remove(); closeHandler();
                const filename = el.dataset.filename;
                const topoName = filename.replace(/\.json$/i, '');
                const loadToken = FileOps._beginTopologyLoad(editor, {
                    name: topoName,
                    filename,
                    domain: section.name,
                    sectionId: section.id,
                });
                try {
                    const r = await fetch(`/api/sections/${section.id}/topologies/${filename}`);
                    if (!FileOps._isTopologyLoadCurrent(editor, loadToken)) return;
                    const d = await r.json();
                    if (d.error) {
                        FileOps._cancelTopologyLoad(editor, loadToken);
                        editor.showToast(d.error, 'error');
                        return;
                    }
                    if (!FileOps._isTopologyLoadCurrent(editor, loadToken)) return;
                    const loaded = FileOps._loadIntoEditor(editor, d, {
                        name: topoName,
                        filename,
                        domain: section.name,
                        color: section.color,
                        sectionId: section.id,
                        loadToken,
                    });
                    if (!loaded) return;
                    editor.showToast(`Loaded from ${section.name}`, 'success');
                } catch (e) {
                    if (!FileOps._isTopologyLoadCurrent(editor, loadToken)) return;
                    FileOps._cancelTopologyLoad(editor, loadToken);
                    editor.showToast(e.message, 'error');
                }
            };
        });
        
        document.body.appendChild(div);
        const closeHandler = (e) => {
            if (e && div.contains(e.target)) return;
            div.remove(); document.removeEventListener('click', closeHandler); document.removeEventListener('keydown', escHandler);
        };
        const escHandler = (e) => { if (e.key === 'Escape') closeHandler(); };
        setTimeout(() => { document.addEventListener('click', closeHandler); document.addEventListener('keydown', escHandler); }, 0);
    },

    showManageSections(editor) {
        const existing = document.getElementById('manage-sections-panel');
        if (existing) { existing.remove(); return; }

        const panel = document.createElement('div');
        panel.id = 'manage-sections-panel';
        panel.className = 'topo-menu-inverted';
        panel.onclick = (e) => e.stopPropagation();

        const anchor = document.getElementById('btn-topologies');
        const rect = anchor ? anchor.getBoundingClientRect() : { left: 120, bottom: 48 };

        const icons = FileOps._sectionIcons();
        const colors = FileOps._sectionColors();

        const render = () => {
            const dk = FileOps._topologyChromeDark(editor);
            const t = {
                bg: dk ? 'rgba(17, 25, 40, 0.78)' : 'rgba(255, 255, 255, 0.78)',
                border: dk ? 'rgba(255, 255, 255, 0.125)' : 'rgba(0, 0, 0, 0.08)',
                text: dk ? 'rgba(255, 255, 255, 0.9)' : 'rgba(0, 0, 0, 0.85)',
                muted: dk ? 'rgba(255, 255, 255, 0.45)' : 'rgba(0, 0, 0, 0.45)',
                card: dk ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.03)',
                cardBorder: dk ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)',
                input: dk ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.04)',
                inputBorder: dk ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.12)',
                iconStroke: dk ? 'rgba(255, 255, 255, 0.75)' : 'rgba(0, 0, 0, 0.5)',
                hover: dk ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.05)',
            };
            panel.style.cssText = `
            position: fixed; left: ${rect.left}px; top: ${rect.bottom + 6}px;
            width: 360px; max-height: 75vh; overflow-y: auto;
            background: ${t.bg};
            border: 1px solid ${t.border};
            border-radius: 16px; padding: 18px;
            z-index: 1000001;
            box-shadow: 0 8px 32px rgba(0, 0, 0, ${dk ? 0.5 : 0.15}), 0 0 0 1px ${t.border};
            font-family: 'Poppins', -apple-system, sans-serif;
            color: ${t.text};
            backdrop-filter: blur(16px) saturate(180%);
            -webkit-backdrop-filter: blur(16px) saturate(180%);
            animation: liquidDropdownFadeIn 0.2s ease-out;
        `;
            let html = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
                <div style="display:flex;align-items:center;gap:8px;">
                    <button id="ms-back" style="background:${t.hover};border:1px solid ${t.cardBorder};border-radius:6px;color:${t.text};cursor:pointer;padding:4px 6px;display:flex;align-items:center;justify-content:center;transition:all 0.15s;"
                        onmouseenter="this.style.background='${t.input}';this.style.borderColor='${t.muted}'" onmouseleave="this.style.background='${t.hover}';this.style.borderColor='${t.cardBorder}'" title="Back to Topologies">
                        <svg viewBox="0 0 24 24" width="16" height="16" style="stroke:currentColor;"><polyline points="15 18 9 12 15 6" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    </button>
                    <svg viewBox="0 0 24 24" width="18" height="18" style="stroke:${t.muted};">
                        <polygon points="12 2 2 7 12 12 22 7" stroke="currentColor" stroke-width="2" fill="none"/>
                        <polyline points="2 17 12 22 22 17" stroke="currentColor" stroke-width="2" fill="none"/>
                        <polyline points="2 12 12 17 22 12" stroke="currentColor" stroke-width="2" fill="none"/>
                    </svg>
                    <span style="font-size:14px;font-weight:600;">Topology Domains</span>
                </div>
                <button id="ms-close" style="background:none;border:none;color:${t.muted};cursor:pointer;font-size:16px;padding:2px 6px;border-radius:6px;transition:background 0.15s;"
                    onmouseenter="this.style.background='${t.hover}'" onmouseleave="this.style.background='none'">✕</button>
            </div>`;
            
            // Primary CTA up top: "Create new domain" toggles a collapsed
            // inline form. Moving the create flow above the list (instead
            // of the previous always-open bottom form) makes the list the
            // hero content while keeping add-a-new-domain one click away.
            // The form itself renders inline but display:none by default
            // so its input / icon-grid / colour-grid / Add-button handlers
            // further down still have DOM nodes to bind to on first render.
            html += `<div id="ms-create-zone" style="margin-bottom:14px;">
                <button id="ms-create-toggle" type="button"
                    style="width:100%;display:flex;align-items:center;justify-content:center;gap:6px;padding:9px 10px;background:${dk ? 'rgba(99,102,241,0.14)' : 'rgba(99,102,241,0.08)'};border:1px dashed ${dk ? 'rgba(99,102,241,0.55)' : 'rgba(99,102,241,0.4)'};border-radius:10px;color:${dk ? '#c7d2fe' : '#4338ca'};font-size:12px;font-weight:600;letter-spacing:0.2px;cursor:pointer;font-family:inherit;transition:all 0.15s;"
                    onmouseenter="this.style.background='${dk ? 'rgba(99,102,241,0.22)' : 'rgba(99,102,241,0.15)'}';this.style.borderColor='${dk ? 'rgba(99,102,241,0.75)' : 'rgba(99,102,241,0.6)'}'" onmouseleave="this.style.background='${dk ? 'rgba(99,102,241,0.14)' : 'rgba(99,102,241,0.08)'}';this.style.borderColor='${dk ? 'rgba(99,102,241,0.55)' : 'rgba(99,102,241,0.4)'}'"
                    aria-expanded="false" aria-controls="ms-create-form">
                    <svg id="ms-create-icon" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="transition:transform 0.25s cubic-bezier(0.22,1,0.36,1);"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    <span id="ms-create-label">Create new domain</span>
                </button>
                <div id="ms-create-form" style="display:none;padding:12px 12px 12px;margin-top:8px;background:${t.card};border:1px solid ${t.cardBorder};border-radius:10px;">
                    <input id="ms-name" placeholder="Domain name" maxlength="60"
                        style="width:100%;padding:8px 11px;background:${t.input};border:1px solid ${t.inputBorder};border-radius:8px;color:${t.text};font-size:12px;font-family:inherit;box-sizing:border-box;margin-bottom:10px;outline:none;transition:border-color 0.2s;"
                        onfocus="this.style.borderColor='#6366f1'" onblur="this.style.borderColor='${t.inputBorder}'">
                    <div style="font-size:9px;font-weight:700;color:${t.muted};margin-bottom:4px;text-transform:uppercase;letter-spacing:0.5px;">Icon</div>
                    <div id="ms-icons" style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px;">
                        ${icons.map(ic => `<button class="ms-icon-btn" data-icon="${ic.id}" type="button" style="width:28px;height:28px;padding:0;background:${t.input};border:1.5px solid ${t.inputBorder};border-radius:7px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.15s;"><svg viewBox="0 0 24 24" width="13" height="13" style="stroke:${t.iconStroke};color:${t.iconStroke};">${ic.svg}</svg></button>`).join('')}
                    </div>
                    <div style="font-size:9px;font-weight:700;color:${t.muted};margin-bottom:4px;text-transform:uppercase;letter-spacing:0.5px;">Colour</div>
                    <div id="ms-colors" style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:12px;">
                        ${colors.map(c => `<button class="ms-color-btn" data-color="${c}" type="button" style="width:22px;height:22px;background:${c};border:2px solid transparent;border-radius:50%;cursor:pointer;transition:all 0.15s;box-shadow:0 2px 6px ${c}40;"></button>`).join('')}
                    </div>
                    <div style="display:flex;gap:6px;">
                        <button id="ms-add" type="button"
                            style="flex:1;padding:9px;background:linear-gradient(135deg,rgba(99,102,241,0.85),rgba(79,70,229,0.95));border:1px solid rgba(99,102,241,0.45);border-radius:8px;color:#fff;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;transition:filter 0.15s, transform 0.08s;"
                            onmouseenter="this.style.filter='brightness(1.08)'" onmouseleave="this.style.filter=''">Create domain</button>
                        <button id="ms-create-cancel" type="button"
                            style="padding:9px 14px;background:${t.hover};border:1px solid ${t.cardBorder};border-radius:8px;color:${t.muted};font-size:11px;cursor:pointer;font-family:inherit;transition:all 0.15s;">Cancel</button>
                    </div>
                </div>
            </div>`;

            const sections = editor._customSections || [];
            if (sections.length === 0) {
                html += `<div style="text-align:center;padding:16px 0;color:${t.muted};font-size:12px;">No domains yet. Click "Create new domain" above to add one.</div>`;
            }
            
            sections.forEach(sec => {
                const iconSvg = (icons.find(i => i.id === sec.icon) || icons[0]).svg;
                const isBuiltin = !!sec.builtin;
                const handleHtml = isBuiltin
                    ? `<div class="ms-builtin-lock" style="flex-shrink:0;color:${sec.color};display:flex;align-items:center;padding:0 2px;opacity:0.7;" title="Built-in domain (cannot be deleted)">
                            <svg viewBox="0 0 24 24" width="14" height="14"><rect x="5" y="11" width="14" height="9" rx="2" stroke="currentColor" stroke-width="2" fill="none"/><path d="M8 11V8a4 4 0 0 1 8 0v3" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/></svg>
                        </div>`
                    : `<div class="ms-drag-handle" style="cursor:grab;flex-shrink:0;color:${t.muted};display:flex;align-items:center;padding:0 2px;" title="Drag to reorder">
                            <svg viewBox="0 0 24 24" width="14" height="14" style="color:inherit;"><circle cx="9" cy="6" r="1.5" fill="currentColor"/><circle cx="15" cy="6" r="1.5" fill="currentColor"/><circle cx="9" cy="12" r="1.5" fill="currentColor"/><circle cx="15" cy="12" r="1.5" fill="currentColor"/><circle cx="9" cy="18" r="1.5" fill="currentColor"/><circle cx="15" cy="18" r="1.5" fill="currentColor"/></svg>
                        </div>`;
                const builtinTagHtml = isBuiltin
                    ? `<span style="font-size:9px;font-weight:700;letter-spacing:0.4px;color:${sec.color};background:${sec.color}1a;border:1px solid ${sec.color}33;border-radius:999px;padding:2px 7px 2px 5px;text-transform:uppercase;display:inline-flex;align-items:center;gap:3px;flex-shrink:0;">
                            <svg viewBox="0 0 24 24" width="9" height="9" fill="none" stroke="currentColor" stroke-width="2.4"><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3" stroke-linecap="round"/></svg>
                            Built-in
                        </span>`
                    : '';
                const editTitle = isBuiltin ? 'Edit icon / color (name is fixed for built-ins)' : 'Edit';
                const editHtml = `<button class="ms-edit" data-id="${sec.id}" style="background:${t.hover};border:1px solid ${t.cardBorder};border-radius:6px;color:${t.muted};cursor:pointer;font-size:11px;padding:4px 8px;transition:all 0.15s;" title="${editTitle}">Edit</button>`;
                const delHtml = isBuiltin ? '' : `<button class="ms-del" data-id="${sec.id}" style="background:none;border:none;color:${t.muted};cursor:pointer;font-size:14px;padding:4px 6px;border-radius:6px;transition:background 0.15s;"
                            onmouseenter="this.style.background='rgba(239,68,68,0.15)';this.style.color='#ef4444'" onmouseleave="this.style.background='none';this.style.color='${t.muted}'" title="Delete">✕</button>`;
                html += `<div class="ms-domain-row${isBuiltin ? ' ms-builtin' : ''}" data-id="${sec.id}" style="margin-bottom:6px;background:${t.card};border:1px solid ${t.cardBorder};border-radius:10px;border-left:3px solid ${sec.color};">
                    <div style="display:flex;align-items:center;gap:10px;padding:10px 12px;">
                        ${handleHtml}
                        <div style="width:32px;height:32px;border-radius:8px;background:${sec.color}18;border:1px solid ${sec.color}30;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                            <svg viewBox="0 0 24 24" width="16" height="16" style="color:${sec.color};">${iconSvg}</svg>
                        </div>
                        <span style="flex:1;font-size:13px;font-weight:500;color:${t.text};display:flex;align-items:center;gap:6px;">${sec.name}${builtinTagHtml}</span>
                        ${editHtml}
                        ${delHtml}
                    </div>
                    <div class="ms-edit-form" data-id="${sec.id}" style="display:none;padding:8px 12px 12px;border-top:1px solid ${t.cardBorder};"></div>
                </div>`;
            });
            
            // (Previously: bottom "Add New Domain" block. Now replaced by
            //  the top #ms-create-zone above so the list stays the hero.)

            panel.innerHTML = html;
            panel.querySelector('#ms-close').onclick = () => { panel.remove(); cleanup(); };
            panel.querySelector('#ms-back').onclick = () => {
                panel.remove(); cleanup();
                FileOps._renderCustomSectionsInDropdown(editor);
                const dd = document.getElementById('topologies-dropdown-menu');
                const btn = document.getElementById('btn-topologies');
                if (dd && btn) {
                    dd.style.display = 'block';
                    const r = btn.getBoundingClientRect();
                    dd.style.position = 'fixed';
                    dd.style.left = FileOps._clampDropdownLeft(r.left) + 'px';
                    dd.style.top = (r.bottom + 4) + 'px';
                    btn.classList.add('topologies-open');
                }
            };
            
            // Collapsible "Create new domain" control up top. Clicking the
            // toggle rotates the + into an x and reveals the form below.
            // Enter in the name field triggers Create (handled on the
            // input keydown); Escape cancels. The Cancel button inside
            // the form is a redundant affordance for users who don't
            // think to click the toggle again.
            const createToggle = panel.querySelector('#ms-create-toggle');
            const createForm = panel.querySelector('#ms-create-form');
            const createIcon = panel.querySelector('#ms-create-icon');
            const createLabel = panel.querySelector('#ms-create-label');
            const createCancel = panel.querySelector('#ms-create-cancel');
            let createOpen = false;
            const setCreateOpen = (open) => {
                createOpen = !!open;
                if (createForm) createForm.style.display = createOpen ? 'block' : 'none';
                if (createIcon) createIcon.style.transform = createOpen ? 'rotate(45deg)' : '';
                if (createLabel) createLabel.textContent = createOpen ? 'Close' : 'Create new domain';
                if (createToggle) createToggle.setAttribute('aria-expanded', String(createOpen));
                if (createOpen) {
                    const ni = panel.querySelector('#ms-name');
                    if (ni) setTimeout(() => { try { ni.focus({ preventScroll: true }); } catch (_) {} }, 50);
                }
            };
            if (createToggle) createToggle.onclick = () => setCreateOpen(!createOpen);
            if (createCancel) createCancel.onclick = (e) => {
                e.stopPropagation();
                const ni = panel.querySelector('#ms-name'); if (ni) ni.value = '';
                setCreateOpen(false);
            };
            const createNameInput = panel.querySelector('#ms-name');
            if (createNameInput) {
                createNameInput.addEventListener('keydown', (ev) => {
                    if (ev.key === 'Enter') {
                        ev.preventDefault();
                        const addBtn = panel.querySelector('#ms-add');
                        if (addBtn) addBtn.click();
                    } else if (ev.key === 'Escape') {
                        ev.preventDefault();
                        if (createCancel) createCancel.click();
                    }
                });
            }

            let selectedIcon = icons[0].id;
            let selectedColor = colors[0];

            panel.querySelectorAll('.ms-icon-btn').forEach(btn => {
                if (btn.dataset.icon === selectedIcon) btn.style.borderColor = selectedColor;
                btn.onclick = () => {
                    panel.querySelectorAll('.ms-icon-btn').forEach(b => b.style.borderColor = t.inputBorder);
                    btn.style.borderColor = selectedColor;
                    selectedIcon = btn.dataset.icon;
                };
            });
            
            panel.querySelectorAll('.ms-color-btn').forEach(btn => {
                if (btn.dataset.color === selectedColor) btn.style.borderColor = dk ? '#fff' : '#333';
                btn.onclick = () => {
                    panel.querySelectorAll('.ms-color-btn').forEach(b => b.style.borderColor = 'transparent');
                    btn.style.borderColor = dk ? '#fff' : '#333';
                    selectedColor = btn.dataset.color;
                    panel.querySelectorAll('.ms-icon-btn').forEach(b => b.style.borderColor = t.inputBorder);
                    const activeIcon = panel.querySelector(`.ms-icon-btn[data-icon="${selectedIcon}"]`);
                    if (activeIcon) activeIcon.style.borderColor = selectedColor;
                };
            });
            
            panel.querySelector('#ms-add').onclick = async () => {
                const name = panel.querySelector('#ms-name').value.trim();
                if (!name) { editor.showToast('Enter a domain name', 'warning'); return; }
                if (name.toLowerCase() === 'dnaas') {
                    editor.showToast('"DNAAS" is a reserved domain name', 'warning');
                    return;
                }
                const exists = (editor._customSections || []).some(s =>
                    (s.name || '').toLowerCase() === name.toLowerCase()
                );
                if (exists) {
                    editor.showToast(`Domain "${name}" already exists`, 'warning');
                    return;
                }
                try {
                    const resp = await fetch('/api/sections', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, icon: selectedIcon, color: selectedColor }) });
                    const result = await resp.json();
                    if (result.ok) {
                        await FileOps.loadCustomSections(editor);
                        render();
                        // Tell the rest of the app (e.g. the New Topology
                        // picker, dropdown, share dialog) so they rerender
                        // without forcing the user to re-open them.
                        try {
                            document.dispatchEvent(new CustomEvent('topology-domains:changed', {
                                detail: { reason: 'domain-created', domainName: name },
                            }));
                        } catch (_) {}
                        editor.showToast(`Domain "${name}" created`, 'success');
                    }
                } catch (e) { editor.showToast(e.message, 'error'); }
            };
            
            panel.querySelectorAll('.ms-edit').forEach(btn => {
                btn.onclick = () => {
                    const id = btn.dataset.id;
                    const sec = (editor._customSections || []).find(s => s.id === id);
                    if (!sec) return;
                    const form = panel.querySelector(`.ms-edit-form[data-id="${id}"]`);
                    if (!form) return;
                    const isOpen = form.style.display !== 'none';
                    panel.querySelectorAll('.ms-edit-form').forEach(f => f.style.display = 'none');
                    if (isOpen) return;
                    form.style.display = 'block';
                    let editIcon = sec.icon || icons[0].id;
                    let editColor = sec.color || colors[0];
                    const origName = sec.name, origIcon = editIcon, origColor = editColor;

                    const row = btn.closest('.ms-domain-row');
                    const rowIconBox = row ? row.querySelector('div > div:nth-child(2)') : null;
                    const rowIconSvg = rowIconBox ? rowIconBox.querySelector('svg') : null;
                    const rowName = row ? row.querySelector('span') : null;

                    const livePreview = () => {
                        if (row) row.style.borderLeftColor = editColor;
                        if (rowIconBox) { rowIconBox.style.background = editColor + '18'; rowIconBox.style.borderColor = editColor + '30'; }
                        if (rowIconSvg) {
                            const ic = icons.find(i => i.id === editIcon) || icons[0];
                            rowIconSvg.innerHTML = ic.svg;
                            rowIconSvg.style.color = editColor;
                        }
                        const nameInput = form.querySelector('.edit-name');
                        if (rowName && nameInput) rowName.textContent = nameInput.value || origName;
                    };

                    const lockedName = !!sec.builtin;
                    const nameFieldHtml = lockedName
                        ? `<input class="edit-name" type="text" value="${sec.name}" readonly tabindex="-1" title="Built-in domain name cannot be changed" style="width:100%;padding:7px 10px;background:${t.input};border:1px solid ${t.inputBorder};border-radius:6px;color:${t.muted};font-size:11px;font-family:inherit;box-sizing:border-box;margin-bottom:4px;outline:none;opacity:0.65;cursor:not-allowed;">
                           <div style="font-size:9px;color:${t.muted};margin-bottom:8px;display:flex;align-items:center;gap:4px;">
                               <svg viewBox="0 0 24 24" width="9" height="9" fill="none" stroke="currentColor" stroke-width="2.4"><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3" stroke-linecap="round"/></svg>
                               Built-in name is fixed. Icon and color are editable.
                           </div>`
                        : `<input class="edit-name" type="text" value="${sec.name}" style="width:100%;padding:7px 10px;background:${t.input};border:1px solid ${t.inputBorder};border-radius:6px;color:${t.text};font-size:11px;font-family:inherit;box-sizing:border-box;margin-bottom:8px;outline:none;transition:border-color 0.15s;"
                            onfocus="this.style.borderColor='${editColor}'" onblur="this.style.borderColor='${t.inputBorder}'">`;
                    form.innerHTML = `
                        ${nameFieldHtml}
                        <div style="font-size:9px;color:${t.muted};margin-bottom:3px;">Icon</div>
                        <div class="edit-icons" style="display:flex;flex-wrap:wrap;gap:3px;margin-bottom:8px;">
                            ${icons.map(ic => `<button class="ei-btn" data-icon="${ic.id}" style="width:26px;height:26px;padding:0;background:${ic.id === editIcon ? editColor + '20' : t.input};border:1.5px solid ${ic.id === editIcon ? editColor : t.inputBorder};border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.12s;"><svg viewBox="0 0 24 24" width="12" height="12" style="stroke:${ic.id === editIcon ? editColor : t.iconStroke};color:${ic.id === editIcon ? editColor : t.iconStroke};transition:color 0.12s;">${ic.svg}</svg></button>`).join('')}
                        </div>
                        <div style="font-size:9px;color:${t.muted};margin-bottom:3px;">Color</div>
                        <div class="edit-colors" style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px;">
                            ${colors.map(c => `<button class="ec-btn" data-color="${c}" style="width:20px;height:20px;background:${c};border:2.5px solid ${c === editColor ? (dk?'#fff':'#333') : 'transparent'};border-radius:50%;cursor:pointer;transition:all 0.12s;box-shadow:${c === editColor ? '0 0 8px '+c+'60' : 'none'};transform:${c === editColor ? 'scale(1.15)' : 'scale(1)'};"></button>`).join('')}
                        </div>
                        <div style="display:flex;gap:6px;">
                            <button class="edit-save" style="flex:1;padding:7px;background:linear-gradient(135deg,rgba(59,130,246,0.8),rgba(37,99,235,0.8));border:none;border-radius:6px;color:#fff;font-size:11px;font-weight:600;cursor:pointer;font-family:inherit;transition:all 0.15s;">Save</button>
                            <button class="edit-cancel" style="padding:7px 14px;background:${t.hover};border:1px solid ${t.cardBorder};border-radius:6px;color:${t.muted};font-size:11px;cursor:pointer;font-family:inherit;transition:all 0.15s;">Cancel</button>
                        </div>
                    `;
                    form.querySelector('.edit-name').addEventListener('input', () => livePreview());
                    const refreshIconBtns = () => {
                        form.querySelectorAll('.ei-btn').forEach(b => {
                            const isActive = b.dataset.icon === editIcon;
                            b.style.borderColor = isActive ? editColor : t.inputBorder;
                            b.style.background = isActive ? editColor + '20' : t.input;
                            const svg = b.querySelector('svg');
                            if (svg) { svg.style.color = isActive ? editColor : t.iconStroke; svg.style.stroke = isActive ? editColor : t.iconStroke; }
                        });
                    };
                    const refreshColorBtns = () => {
                        form.querySelectorAll('.ec-btn').forEach(b => {
                            const isActive = b.dataset.color === editColor;
                            b.style.borderColor = isActive ? (dk?'#fff':'#333') : 'transparent';
                            b.style.boxShadow = isActive ? '0 0 8px '+editColor+'60' : 'none';
                            b.style.transform = isActive ? 'scale(1.15)' : 'scale(1)';
                        });
                    };
                    form.querySelectorAll('.ei-btn').forEach(b => {
                        b.onclick = (ev) => { ev.stopPropagation(); editIcon = b.dataset.icon; refreshIconBtns(); livePreview(); };
                    });
                    form.querySelectorAll('.ec-btn').forEach(b => {
                        b.onclick = (ev) => { ev.stopPropagation(); editColor = b.dataset.color; refreshColorBtns(); refreshIconBtns(); livePreview(); };
                    });
                    form.querySelector('.edit-cancel').onclick = (ev) => {
                        ev.stopPropagation(); form.style.display = 'none';
                        editIcon = origIcon; editColor = origColor;
                        if (row) row.style.borderLeftColor = origColor;
                        if (rowIconBox) { rowIconBox.style.background = origColor + '18'; rowIconBox.style.borderColor = origColor + '30'; }
                        if (rowIconSvg) { const ic = icons.find(i => i.id === origIcon) || icons[0]; rowIconSvg.innerHTML = ic.svg; rowIconSvg.style.color = origColor; }
                        if (rowName) rowName.textContent = origName;
                    };
                    form.querySelector('.edit-save').onclick = async (ev) => {
                        ev.stopPropagation();
                        const typedName = form.querySelector('.edit-name').value.trim();
                        // Built-in domains have a fixed name. Always send
                        // the canonical one on save so we can't drift even
                        // if the readonly input is DOM-tampered.
                        const newName = lockedName ? sec.name : typedName;
                        if (!newName) { editor.showToast('Enter a name', 'warning'); return; }
                        if (!lockedName) {
                            if (newName.toLowerCase() === 'dnaas' && sec.name.toLowerCase() !== 'dnaas') {
                                editor.showToast('"DNAAS" is a reserved domain name', 'warning');
                                return;
                            }
                            const dup = (editor._customSections || []).some(s =>
                                s.id !== sec.id && (s.name || '').toLowerCase() === newName.toLowerCase()
                            );
                            if (dup) {
                                editor.showToast(`Domain "${newName}" already exists`, 'warning');
                                return;
                            }
                        }
                        try {
                            await fetch('/api/sections/update', {
                                method: 'POST', headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ id: sec.id, name: newName, icon: editIcon, color: editColor })
                            });
                            await FileOps.loadCustomSections(editor);
                            render();
                            try {
                                document.dispatchEvent(new CustomEvent('topology-domains:changed', {
                                    detail: { reason: 'domain-updated', domainId: sec.id, domainName: newName },
                                }));
                            } catch (_) {}
                            editor.showToast(`Domain "${newName}" updated`, 'success');
                        } catch (e) { editor.showToast(e.message, 'error'); }
                    };
                };
            });
            
            panel.querySelectorAll('.ms-del').forEach(btn => {
                btn.onclick = () => {
                    const id = btn.dataset.id;
                    const sec = (editor._customSections || []).find(s => s.id === id);
                    const row = btn.closest('.ms-domain-row');
                    if (!row || !sec) return;
                    const existing = row.querySelector('.ms-confirm-bar');
                    if (existing) { existing.remove(); return; }
                    const bar = document.createElement('div');
                    bar.className = 'ms-confirm-bar';
                    bar.style.cssText = `display:flex;align-items:center;gap:8px;padding:8px 12px;border-top:1px solid rgba(239,68,68,0.2);background:rgba(239,68,68,0.06);`;
                    bar.innerHTML = `
                        <span style="flex:1;font-size:11px;color:#ef4444;">Delete empty domain "${sec.name}"? Move or delete individual topologies first.</span>
                        <button class="dc-yes" style="padding:4px 12px;background:#ef4444;border:none;border-radius:6px;color:#fff;font-size:11px;font-weight:600;cursor:pointer;">Delete</button>
                        <button class="dc-no" style="padding:4px 10px;background:${t.hover};border:1px solid ${t.cardBorder};border-radius:6px;color:${t.muted};font-size:11px;cursor:pointer;">Cancel</button>
                    `;
                    row.appendChild(bar);
                    bar.querySelector('.dc-no').onclick = (ev) => { ev.stopPropagation(); bar.remove(); };
                    bar.querySelector('.dc-yes').onclick = async (ev) => {
                        ev.stopPropagation();
                        try {
                            const resp = await FileOps._authFetch(`/api/sections/${encodeURIComponent(id)}/delete`, { method: 'POST' });
                            const result = await resp.json().catch(() => ({}));
                            if (!resp.ok || result.error) {
                                throw new Error(result.error || 'Delete failed');
                            }
                            await FileOps.loadCustomSections(editor);
                            render();
                            try {
                                document.dispatchEvent(new CustomEvent('topology-domains:changed', {
                                    detail: { reason: 'domain-deleted', domainId: id },
                                }));
                            } catch (_) {}
                            editor.showToast('Domain deleted', 'success');
                        } catch (e) { editor.showToast(e.message, 'error'); }
                    };
                };
            });

            panel.querySelectorAll('.ms-drag-handle').forEach(handle => {
                handle.addEventListener('mousedown', (e) => {
                    if (e.button !== 0) return;
                    e.preventDefault();
                    const row = handle.closest('.ms-domain-row');
                    const allRows = [...panel.querySelectorAll('.ms-domain-row')];
                    if (allRows.length < 2) return;
                    const srcIdx = allRows.indexOf(row);
                    if (srcIdx < 0) return;

                    const startY = e.clientY;
                    const startRect = row.getBoundingClientRect();
                    const domainColor = row.style.borderLeftColor || '#3b82f6';

                    const ghost = row.cloneNode(true);
                    ghost.style.cssText += `;position:fixed;left:${startRect.left}px;top:${startRect.top}px;width:${startRect.width}px;z-index:999999;opacity:0.92;pointer-events:none;box-shadow:0 8px 24px rgba(0,0,0,0.35);transition:none;`;
                    document.body.appendChild(ghost);
                    document.body.style.cursor = 'grabbing';
                    handle.style.cursor = 'grabbing';

                    row.style.opacity = '0.15';
                    row.style.transition = 'opacity 0.15s';
                    const placeholder = document.createElement('div');
                    placeholder.style.cssText = `height:${startRect.height}px;background:rgba(59,130,246,0.06);border:2px dashed rgba(59,130,246,0.35);border-radius:10px;margin-bottom:6px;transition:all 0.2s ease;`;
                    row.parentNode.insertBefore(placeholder, row);
                    row.style.display = 'none';

                    // Snapshot positions of visible rows (excluding the dragged row)
                    const visibleRows = [...panel.querySelectorAll('.ms-domain-row')].filter(r => r !== row);
                    let currentIdx = srcIdx;

                    const onMove = (ev) => {
                        const dy = ev.clientY - startY;
                        ghost.style.top = (startRect.top + dy) + 'px';

                        const ghostMid = startRect.top + dy + startRect.height / 2;

                        // Find target position among visible rows
                        let newIdx = visibleRows.length;
                        for (let i = 0; i < visibleRows.length; i++) {
                            const r = visibleRows[i].getBoundingClientRect();
                            const mid = r.top + r.height / 2;
                            if (ghostMid < mid) {
                                newIdx = i;
                                break;
                            }
                        }

                        // Convert visible-row index to real section index
                        let realIdx = newIdx;
                        if (newIdx >= srcIdx) realIdx = newIdx + 1;
                        if (realIdx > allRows.length) realIdx = allRows.length;
                        if (realIdx < 0) realIdx = 0;
                        // Normalize: final position after removal
                        const finalIdx = realIdx > srcIdx ? realIdx - 1 : realIdx;

                        if (finalIdx !== currentIdx) {
                            placeholder.remove();
                            if (newIdx >= visibleRows.length) {
                                visibleRows[visibleRows.length - 1].parentNode.insertBefore(placeholder, visibleRows[visibleRows.length - 1].nextSibling);
                            } else {
                                visibleRows[newIdx].parentNode.insertBefore(placeholder, visibleRows[newIdx]);
                            }
                            currentIdx = finalIdx;
                        }
                    };

                    const onUp = async () => {
                        document.removeEventListener('mousemove', onMove);
                        document.removeEventListener('mouseup', onUp);
                        document.body.style.cursor = '';
                        handle.style.cursor = 'grab';
                        ghost.remove();
                        placeholder.remove();
                        row.style.display = '';
                        row.style.opacity = '1';
                        row.style.transition = '';
                        if (currentIdx !== srcIdx) {
                            const sections = [...(editor._customSections || [])];
                            const [moved] = sections.splice(srcIdx, 1);
                            sections.splice(currentIdx, 0, moved);
                            editor._customSections = sections;
                            try {
                                await FileOps._authFetch('/api/sections/reorder', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sections }) });
                                FileOps._renderCustomSectionsInDropdown(editor);
                                FileOps._updateTopoBtnIcon(editor);
                            } catch (_) {}
                            render();
                        }
                    };
                    document.addEventListener('mousemove', onMove);
                    document.addEventListener('mouseup', onUp);
                });
            });
        };

        panel._msThemeRefresh = render;
        render();
        panel.addEventListener('keydown', (e) => { e.stopPropagation(); });
        panel.addEventListener('keyup', (e) => { e.stopPropagation(); });
        document.body.appendChild(panel);
        
        // Bug fix (2026-04-26): canvas mousedown handlers can call
        // stopPropagation in tool-specific paths, so a `click` listener on
        // document never fires for those clicks and the panel stays open
        // even though the user clearly clicked elsewhere. Switching to
        // `mousedown` in the capture phase (and also wiring `pointerdown`)
        // makes the close fire BEFORE any tool-side handler can swallow it.
        // We also exclude the topologies-dropdown menu so clicking the
        // overflow chevron inside the dropdown does not race-close the
        // panel.
        const isInsideTopologiesUI = (target) => {
            if (!target) return false;
            if (target.id === 'btn-topologies') return true;
            if (target.closest && target.closest('#topologies-dropdown-menu')) return true;
            return false;
        };
        const outsideHandler = (e) => {
            if (!panel.isConnected) { cleanup(); return; }
            if (panel.contains(e.target)) return;
            if (isInsideTopologiesUI(e.target)) return;
            panel.remove();
            cleanup();
        };
        const escHandler = (e) => { if (e.key === 'Escape') { panel.remove(); cleanup(); } };
        const cleanup = () => {
            document.removeEventListener('mousedown', outsideHandler, true);
            document.removeEventListener('pointerdown', outsideHandler, true);
            document.removeEventListener('keydown', escHandler);
        };
        setTimeout(() => {
            document.addEventListener('mousedown', outsideHandler, true);
            document.addEventListener('pointerdown', outsideHandler, true);
            document.addEventListener('keydown', escHandler);
        }, 0);
    },

    // ========================================================================
    // SEAMLESS THEME TRANSITION FOR OPEN DROPDOWN
    // ========================================================================

    _updateDropdownTheme(editor) {
        FileOps._refreshManageSectionsForTheme(editor);
        const dropdown = document.getElementById('topologies-dropdown-menu');
        if (!dropdown || dropdown.style.display === 'none') return;
        if (document.body && document.body.classList.contains('ui-skin-v2')) {
            if (editor && (editor._topoDragActive || editor._domainDragActive)) return;
            // ui-skin-v2+ owns dropdown colour via scoped CSS variables. The
            // legacy inline repaint below fights that layer and leaves stale
            // Save/Load/Share colours after light/dark flips, so clear only
            // colour-related inline declarations and let CSS animate the rest.
            dropdown.querySelectorAll([
                '.custom-section-category',
                '.domain-body',
                '.domain-actions',
                '.domain-action-btn',
                '.domain-newbug-btn',
                '.domain-topos-list',
                '.domain-topo-row',
                '.topo-entry-name',
                '.topo-time',
                '.ta-btn',
                '.domain-save-form input',
                '.domain-save-form button',
                '.rename-inline-form input',
                '.rename-inline-form button'
            ].join(',')).forEach(el => {
                el.style.removeProperty('background');
                el.style.removeProperty('background-color');
                el.style.removeProperty('background-image');
                el.style.removeProperty('color');
                el.style.removeProperty('border-color');
                el.style.removeProperty('box-shadow');
            });
            return;
        }
        const dk = FileOps._menuDark(editor);
        const txtColor = dk ? '#e2e8f0' : '#1e1e32';
        const iconOpColor = dk ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.5)';
        const dur = '0.4s';
        const transAll = `background ${dur}, color ${dur}, border-color ${dur}, box-shadow ${dur}`;

        dropdown.querySelectorAll('.custom-section-category').forEach(sec => {
            const sid = sec.dataset.sectionId;
            const secObj = (editor._customSections || []).find(s => s.id === sid);
            const c = secObj?.color || '#3b82f6';
            sec.style.transition = transAll;
            sec.style.background = `${c}${dk ? '38' : '48'}`;

            // Save / Load button text + background
            sec.querySelectorAll('[data-action="save"],[data-action="load-file"]').forEach(btn => {
                btn.style.transition = transAll;
                btn.style.color = txtColor;
                if (!btn.dataset.pressed) {
                    btn.style.background = `${c}18`;
                    btn.style.borderColor = `${c}30`;
                }
            });

            // Topology file rows
            sec.querySelectorAll('.domain-topo-row').forEach(row => {
                row.style.transition = transAll;
                const nameEl = row.querySelector('.topo-entry-name');
                if (nameEl) { nameEl.style.transition = `color ${dur}`; nameEl.style.color = txtColor; }
                row.querySelectorAll('svg').forEach(svg => {
                    svg.style.transition = `color ${dur}`;
                    svg.style.color = iconOpColor;
                });
                row.querySelectorAll('.ta-btn').forEach(btn => {
                    btn.style.transition = `color ${dur}`;
                    btn.style.color = iconOpColor;
                });
            });

            // Save form inputs if open
            sec.querySelectorAll('.domain-save-form input').forEach(inp => {
                inp.style.transition = transAll;
                inp.style.background = dk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.04)';
                inp.style.color = txtColor;
            });
            sec.querySelectorAll('.domain-save-form button').forEach(btn => {
                btn.style.transition = transAll;
            });

            // "No topologies yet" text
            sec.querySelectorAll('.domain-topos-list > div[style*="font-style"]').forEach(el => {
                el.style.transition = `color ${dur}`;
            });
        });

        // Delete confirm bars
        dropdown.querySelectorAll('.delete-confirm-bar').forEach(bar => {
            bar.style.transition = transAll;
            bar.style.background = dk ? 'rgba(239,68,68,0.1)' : 'rgba(239,68,68,0.08)';
            bar.querySelectorAll('.dc-no').forEach(btn => {
                btn.style.transition = transAll;
                btn.style.background = dk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)';
                btn.style.borderColor = dk ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.12)';
                btn.style.color = dk ? '#94a3b8' : '#475569';
            });
        });

        // Rename forms
        dropdown.querySelectorAll('.rename-inline-form input').forEach(inp => {
            inp.style.transition = transAll;
            inp.style.background = dk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.04)';
            inp.style.color = txtColor;
        });
        dropdown.querySelectorAll('.rename-inline-form button:last-child').forEach(btn => {
            btn.style.transition = transAll;
            btn.style.background = dk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)';
            btn.style.borderColor = dk ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.12)';
            btn.style.color = dk ? '#94a3b8' : '#475569';
        });
    },

    // ========================================================================
    // INJECT METHODS ONTO EDITOR
    // ========================================================================

    inject(editor) {
        const methods = [
            'confirmNewTopology', 'clearCanvas', 'showClearConfirmation', 'performClearCanvas',
            'generateTopologyData', 'quickSaveTopology', 'quickSaveToDomain', 'saveTopology', 'saveTopologyAs', 'exportTopologyJSON',
            'exportTopologyAsPNG', 'loadTopology',
            'saveAsDnaasTopology', 'loadDnaasTopology',
            'saveBugTopology', 'showDebugDnosTopologySelector', 'loadDebugDnosTopology', '_ensureBugsSection',
            'loadCustomSections', '_renderCustomSectionsInDropdown', '_updateDropdownTheme',
            'saveToSection', 'loadFromSection', '_showSectionTopologyPicker', 'showManageSections',
            '_sectionIcons', '_sectionColors', '_updateTopoBtnIcon'
        ];
        for (const name of methods) {
            if (FileOps[name]) {
                if (name === '_sectionIcons' || name === '_sectionColors') {
                    editor[name] = () => FileOps[name]();
                } else {
                    editor[name] = (...args) => FileOps[name](editor, ...args);
                }
            }
        }
    }
};

console.log('[topology-file-ops.js] FileOps loaded');

// Refresh the dropdown when the domain list changes (new share received,
// outgoing share revoked, shared-in domain permission upgraded, ...).
// We DON'T refetch /api/sections -- that data is already on the editor;
// we just rebuild the sharing index + re-run the renderer.
//
// `_sharingRefreshInFlight` breaks an obvious re-entry loop: our refresh
// calls `TopologyDomains.fetchDomains()` which itself emits the same
// `topology-domains:changed` event. Without the guard we'd loop forever.
var _sharingRefreshInFlight = false;
document.addEventListener('topology-domains:changed', function () {
    if (_sharingRefreshInFlight) return;
    try {
        var openingDropdown = document.getElementById('topologies-dropdown-menu');
        if (openingDropdown && (
            openingDropdown.classList.contains('is-preparing')
            || openingDropdown.classList.contains('is-opening')
            || openingDropdown.classList.contains('is-closing')
        )) {
            return;
        }
    } catch (_) {}
    // Callers in mid-flow (share-migrate-open, rename-commit, ...) set
    // this counter to keep the dropdown DOM stable. Their `finally` block
    // decrements + kicks one deferred refresh so we don't lose badge
    // updates; dropping the event here just skips the noisy intermediate
    // re-renders that orphan anchor elements.
    if (FileOps && (FileOps._suspendDropdownRefresh | 0) > 0) return;
    // Never rebuild the dropdown while a share inline form is mounted --
    // the popover lives inside the dropdown (either as a sibling of the
    // `.domain-topo-row` or as a child of the domain body), so a rebuild
    // would rip it out from under the user's typing. The popover will
    // trigger its own refresh via _refreshAll on close.
    try {
        if (document.querySelector(
            '#topologies-dropdown-menu .topo-share-form.open, ' +
            '#topologies-dropdown-menu .domain-share-form.open'
        )) {
            return;
        }
    } catch (_) {}
    try {
        var ed = window.topologyEditor;
        if (!ed) return;
        _sharingRefreshInFlight = true;
        FileOps._refreshSharingCache(true)
            .catch(function () {})
            .then(function () {
                _sharingRefreshInFlight = false;
                if (!ed._customSections) return;
                FileOps._renderCustomSectionsInDropdown(ed);
            });
    } catch (_) {
        _sharingRefreshInFlight = false;
    }
});

// ---------------------------------------------------------------------------
// SSE auto-refresh: subscribe to /api/topologies/events so shared recipients
// see owner edits (save / rename / delete) without pressing F5. The server
// publishes events from the legacy mirror-on-save path; when the current user
// is a recipient of the affected topology they get the ping and we force a
// domain+sharing refresh that cascades into the dropdown renderer.
//
// Reconnect uses exponential backoff (1s, 2s, 4s, capped at 30s) because
// EventSource's built-in reconnect is too aggressive when the server is down.
// ---------------------------------------------------------------------------
(function () {
    var _es = null;
    var _backoff = 1000;
    var _lastEventAt = 0;
    var _toastCooldownMs = 5000;
    var _lastToastAt = 0;
    var _reconnectTimer = null;
    var _loginListenerArmed = false;

    function _tokenQuery() {
        try {
            var tok = window.TopologyAuth && window.TopologyAuth.getToken && window.TopologyAuth.getToken();
            return tok ? '?token=' + encodeURIComponent(tok) : '';
        } catch (_) { return ''; }
    }

    function _hasToken() {
        try {
            return !!(window.TopologyAuth && window.TopologyAuth.getToken && window.TopologyAuth.getToken());
        } catch (_) { return false; }
    }

    function _clearReconnectTimer() {
        if (_reconnectTimer) {
            clearTimeout(_reconnectTimer);
            _reconnectTimer = null;
        }
    }

    function _closeEventSource() {
        if (_es) {
            try { _es.close(); } catch (_) {}
            _es = null;
        }
        try {
            if (window._topologyEventSource && window._topologyEventSource._topologyEventsOwner === 'file-ops') {
                window._topologyEventSource = null;
            }
        } catch (_) {}
    }

    function _connect() {
        _clearReconnectTimer();
        if (!_hasToken()) {
            _scheduleReconnect();
            return;
        }
        _closeEventSource();
        var url = '/api/topologies/events' + _tokenQuery();
        try {
            _es = new EventSource(url);
            _es._topologyEventsOwner = 'file-ops';
        } catch (_) {
            console.debug('[TopologyEvents] EventSource open failed; retrying without logging tokenized URL');
            _scheduleReconnect();
            return;
        }

        _es.addEventListener('topology-updated', function (ev) {
            _lastEventAt = Date.now();
            _backoff = 1000;
            var payload = {};
            try { payload = JSON.parse(ev.data || '{}'); } catch (_) {}
            _handleRemoteEvent(payload);
        });

        // Graceful-restart heads-up. Shared EventSource so the
        // GracefulRestart coordinator does not need its own connection
        // (the backend broadcasts to every active SSE subscriber).
        _es.addEventListener('service-restart', function (ev) {
            try {
                var payload = JSON.parse(ev.data || '{}');
                if (window.GracefulRestart && typeof window.GracefulRestart.markActive === 'function') {
                    var eta = Number(payload && payload.eta_seconds) || 15;
                    window.GracefulRestart.markActive(eta + 5, {
                        reason: payload && payload.reason,
                        source: payload && payload.source,
                        via: 'sse',
                        kind: payload && payload.kind,
                        announced_at: payload && payload.at,
                    });
                }
            } catch (_) { /* ignore */ }
        });

        // Expose the EventSource so the GracefulRestart coordinator (or
        // any other consumer) can attach extra listeners without opening
        // a second connection.
        try { window._topologyEventSource = _es; } catch (_) {}

        _es.onopen = function () { _backoff = 1000; };
        _es.onerror = function () {
            // Firefox closes the connection silently; Chrome keeps retrying.
            // Either way we close + back off manually so we control the rate.
            _closeEventSource();
            _scheduleReconnect();
        };
    }

    function _scheduleReconnect() {
        if (_reconnectTimer) return;
        var delay = Math.min(30000, _backoff);
        _backoff = Math.min(30000, _backoff * 2);
        // During an announced graceful restart, don't reconnect until
        // after the announced ETA. Reconnecting mid-restart fires a
        // visible ERR_CONNECTION_REFUSED in DevTools every attempt; the
        // GracefulRestart coordinator already polls /api/health and
        // will be cleared once the backend is back, at which point we
        // jump to a 1s reconnect.
        if (window.GracefulRestart && window.GracefulRestart.isInWindow()) {
            delay = Math.max(delay, (window.GracefulRestart.secondsRemaining() + 1) * 1000);
        }
        _reconnectTimer = setTimeout(function () {
            _reconnectTimer = null;
            if (!_hasToken()) {
                if (!_loginListenerArmed) {
                    _loginListenerArmed = true;
                    window.addEventListener('topology:auth-login', function () {
                        _loginListenerArmed = false;
                        _start();
                    }, { once: true });
                }
                return;
            }
            _connect();
        }, delay);
    }

    function _handleRemoteEvent(payload) {
        var kind = (payload && payload.kind) || 'save';
        var ed = window.topologyEditor;
        // Force-refresh the domain list + sharing cache so the dropdown
        // picks up the new state. The existing `topology-domains:changed`
        // listener already chains into the dropdown re-render.
        if (window.TopologyDomains && typeof window.TopologyDomains.fetchDomains === 'function') {
            try { window.TopologyDomains.fetchDomains(true); } catch (_) {}
        }
        // Forward to the live-sync hub. TopologySync decides whether to
        // hot-swap the canvas (clean) or show the "Reload" banner
        // (dirty). Keeps the SSE + WS event handling paths converged so
        // users see the same UX regardless of transport.
        if (window.TopologySync && typeof window.TopologySync._onEvent === 'function') {
            try {
                window.TopologySync._onEvent({ detail: {
                    owner: payload && payload.owner,
                    domain_id: payload && payload.domain_id,
                    topology_id: payload && payload.topology_id,
                    event_type: 'topology.' + kind,
                    actor_user: payload && payload.owner,
                    actor_display_name: payload && payload.owner,
                    summary: (payload && payload.name) ? ('Saved "' + payload.name + '"') : '',
                    created_at: payload && payload.at
                        ? new Date(payload.at * 1000).toISOString()
                        : '',
                }});
            } catch (_) { /* swallow */ }
        }
        // Subtle user-visible signal so the recipient knows why their list
        // just changed. Rate-limited so a burst (e.g. owner saves 5 times
        // in a row) shows only one toast. Skip the toast if TopologySync
        // already rendered a banner / auto-reload for the active topology.
        var active = (window.TopologySync && window.TopologySync.getActive
            && window.TopologySync.getActive()) || null;
        var activeMatches = active && payload && active.topology_id
            && active.topology_id === payload.topology_id;
        if (!activeMatches && ed && typeof ed.showToast === 'function'
                && Date.now() - _lastToastAt > _toastCooldownMs) {
            _lastToastAt = Date.now();
            var who = payload && payload.owner ? payload.owner : 'someone';
            var what = 'updated';
            if (kind === 'rename') what = 'renamed';
            else if (kind === 'delete') what = 'deleted';
            var label = payload && (payload.name || payload.new_name || payload.filename) ? (' "' + (payload.name || payload.new_name || payload.filename) + '"') : '';
            ed.showToast('Shared topology' + label + ' ' + what + ' by ' + who, 'info');
        }
    }

    function _start() {
        if (!window.EventSource) return;
        if (!window.TopologyAuth || !window.TopologyAuth.getToken) {
            // Auth module not loaded yet: retry shortly.
            setTimeout(_start, 500);
            return;
        }
        if (!_hasToken()) {
            // User not signed in; wait for login then start.
            if (!_loginListenerArmed) {
                _loginListenerArmed = true;
                window.addEventListener('topology:auth-login', function () {
                    _loginListenerArmed = false;
                    _start();
                }, { once: true });
            }
            return;
        }
        if (_es || _reconnectTimer) return;
        _connect();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _start);
    } else {
        _start();
    }

    window.addEventListener('topology:auth-logout', function () {
        _clearReconnectTimer();
        _closeEventSource();
        _backoff = 1000;
    });

    // Make the reconnect visible from the console for debugging.
    window._topologyEventsStatus = function () {
        return {
            connected: !!_es && _es.readyState === 1,
            readyState: _es ? _es.readyState : -1,
            lastEventAt: _lastEventAt,
            backoff: _backoff,
            reconnectScheduled: !!_reconnectTimer,
        };
    };
})();
