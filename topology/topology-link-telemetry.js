/**
 * topology-link-telemetry.js - Live Link Table telemetry client.
 */

'use strict';

(function () {
    const FIELD_MAP = {
        interfaceA: 'lt-interface-a',
        interfaceB: 'lt-interface-b',
        transceiverA: 'lt-transceiver-a',
        transceiverB: 'lt-transceiver-b',
        vlanModeA: 'lt-vlan-mode-a',
        vlanModeB: 'lt-vlan-mode-b',
        outerTagA: 'lt-outer-tag-a',
        outerTagB: 'lt-outer-tag-b',
        innerTagA: 'lt-inner-tag-a',
        innerTagB: 'lt-inner-tag-b',
        ipAddressA: 'lt-ip-addr-a',
        ipAddressB: 'lt-ip-addr-b',
        subInterfaceA: 'lt-subinterface-a',
        subInterfaceB: 'lt-subinterface-b',
        bundleA: 'lt-bundle-a',
        bundleB: 'lt-bundle-b'
    };

    function authFetch(url, options) {
        if (window.TopologyAuth && typeof window.TopologyAuth.authFetch === 'function') {
            return window.TopologyAuth.authFetch(url, options);
        }
        return fetch(url, options);
    }

    function bridgeUrl(path) {
        if (window.ScalerAPI && typeof window.ScalerAPI._api === 'function') {
            return window.ScalerAPI._api(path);
        }
        const host = window.location.hostname || 'localhost';
        return `${window.location.protocol}//${host}:8766${path}`;
    }

    // #region agent log
    const DEBUG_INGEST_URL = 'http://127.0.0.1:7449/ingest/0813e26e-edca-45e6-98af-9764fe45867c';
    const DEBUG_INGEST_SESSION_ID = '92c7a8';
    const DEBUG_INGEST_RUN_ID = 'linktable-inner-vlan-pre';
    const DEBUG_INGEST_BASE_BACKOFF_MS = 15000;
    const DEBUG_INGEST_MAX_BACKOFF_MS = 120000;
    const DEBUG_INGEST_MAX_PENDING = 25;
    const debugIngestState = {
        healthy: null,
        probeInFlight: false,
        mutedUntil: 0,
        failures: 0,
        warnedUnavailable: false,
        pending: []
    };

    function buildAgentDebugPayload(hypothesisId, message, data) {
        return {
            sessionId: DEBUG_INGEST_SESSION_ID,
            runId: DEBUG_INGEST_RUN_ID,
            hypothesisId,
            location: 'topology-link-telemetry.js',
            message,
            data,
            timestamp: Date.now()
        };
    }

    function postAgentDebugPayload(payload) {
        return fetch(DEBUG_INGEST_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': DEBUG_INGEST_SESSION_ID },
            body: JSON.stringify(payload)
        });
    }

    function markDebugIngestAvailable() {
        debugIngestState.healthy = true;
        debugIngestState.probeInFlight = false;
        debugIngestState.mutedUntil = 0;
        debugIngestState.failures = 0;
        debugIngestState.warnedUnavailable = false;
    }

    function markDebugIngestUnavailable() {
        debugIngestState.healthy = false;
        debugIngestState.probeInFlight = false;
        debugIngestState.pending.length = 0;
        debugIngestState.failures += 1;
        const backoff = Math.min(
            DEBUG_INGEST_MAX_BACKOFF_MS,
            DEBUG_INGEST_BASE_BACKOFF_MS * Math.pow(2, Math.max(0, debugIngestState.failures - 1))
        );
        debugIngestState.mutedUntil = Date.now() + backoff;
        if (!debugIngestState.warnedUnavailable) {
            debugIngestState.warnedUnavailable = true;
            console.warn('[LinkTelemetry] Local debug ingest is unavailable; muting debug posts temporarily.');
        }
    }

    function flushPendingDebugLogs() {
        const pending = debugIngestState.pending.splice(0);
        pending.forEach(payload => {
            postAgentDebugPayload(payload).catch(() => markDebugIngestUnavailable());
        });
    }

    function agentDebugLog(hypothesisId, message, data = {}) {
        const now = Date.now();
        if (debugIngestState.healthy === false && now < debugIngestState.mutedUntil) {
            return;
        }

        const payload = buildAgentDebugPayload(hypothesisId, message, data);

        if (debugIngestState.probeInFlight) {
            if (debugIngestState.healthy === null && debugIngestState.pending.length < DEBUG_INGEST_MAX_PENDING) {
                debugIngestState.pending.push(payload);
            }
            return;
        }

        if (debugIngestState.healthy !== true) {
            debugIngestState.probeInFlight = true;
            postAgentDebugPayload(payload)
                .then(() => {
                    markDebugIngestAvailable();
                    flushPendingDebugLogs();
                })
                .catch(() => markDebugIngestUnavailable());
            return;
        }

        postAgentDebugPayload(payload).catch(() => markDebugIngestUnavailable());
    }
    // #endregion

    function cloneOptionsWithAuth(options = {}) {
        const out = { ...options };
        out.headers = { ...(options.headers || {}) };
        const token = window.TopologyAuth?.getToken?.();
        if (token && !out.headers.Authorization) {
            out.headers.Authorization = `Bearer ${token}`;
        }
        return out;
    }

    async function telemetryFetch(path, options) {
        let resp;
        try {
            resp = await authFetch(path, options);
        } catch (err) {
            return authFetch(bridgeUrl(path), cloneOptionsWithAuth(options));
        }
        if (![404, 502, 503].includes(resp.status)) return resp;
        // Compatibility fallback for sessions where serve.py was already
        // running before the same-origin proxy branch was added, or where
        // its bridge proxy is stale/unhealthy.
        return authFetch(bridgeUrl(path), cloneOptionsWithAuth(options));
    }

    function devicePayload(editor, id) {
        const dev = editor?.objects?.find(o => o && o.id === id) || {};
        const ssh = dev.sshConfig || {};
        return {
            id: dev.id || id || '',
            device_id: dev.label || dev.name || dev.hostname || dev.id || id || '',
            label: dev.label || dev.name || dev.hostname || dev.id || id || '',
            ssh_host: ssh.host || dev.host || dev.mgmt_ip || dev.managementIp || '',
            sshConfig: ssh,
            gnmiConfig: dev.gnmiConfig || null
        };
    }

    function firstRow(rows) {
        return Array.isArray(rows) && rows.length ? rows[0] : null;
    }

    function asRows(rows) {
        return Array.isArray(rows) ? rows : [];
    }

    function findByName(rows, name) {
        if (!Array.isArray(rows) || !name) return null;
        return rows.find(row => row && row.name === name) || null;
    }

    function bestPhysical(side, lldpIf) {
        return findByName(side?.physical, lldpIf) || firstRow(side?.physical);
    }

    function bestSub(side, parent) {
        if (!Array.isArray(side?.subifs)) return null;
        return side.subifs.find(row => row.parent === parent) || firstRow(side.subifs);
    }

    function bestBundle(side, ifName) {
        if (!Array.isArray(side?.bundles)) return null;
        if (ifName && ifName.startsWith('bundle-')) {
            return findByName(side.bundles, ifName.split('.')[0]);
        }
        return firstRow(side.bundles);
    }

    function isFieldUserEdited(el) {
        return el && el.dataset && el.dataset.liveUserEdited === '1';
    }

    function showLiveDiffPill(el, liveValue) {
        const holder = el.closest('.link-table-field') || el.parentElement;
        if (!holder || holder.querySelector('.lt-live-diff-pill')) return;
        const pill = document.createElement('button');
        pill.type = 'button';
        pill.className = 'lt-live-diff-pill';
        pill.textContent = 'use live';
        pill.title = `Live value: ${liveValue}`;
        pill.onclick = (event) => {
            event.preventDefault();
            event.stopPropagation();
            ensureSelectOption(el, liveValue);
            el.value = liveValue;
            el.dataset.liveFilled = '1';
            el.dataset.liveUserEdited = '';
            el.classList.remove('lt-live-differs');
            pill.remove();
            el._liveApplying = true;
            el.dispatchEvent(new Event('change', { bubbles: true }));
            el._liveApplying = false;
        };
        holder.appendChild(pill);
    }

    function ensureSelectOption(el, value) {
        if (!el || el.tagName !== 'SELECT' || !value) return;
        const exists = Array.from(el.options || []).some(opt => opt.value === value);
        if (!exists) {
            const opt = document.createElement('option');
            opt.value = value;
            opt.textContent = value;
            opt.dataset.liveTelemetry = '1';
            el.appendChild(opt);
        }
    }

    function setLiveValue(fieldId, value, link, propName, options = {}) {
        const clean = value === undefined || value === null ? '' : String(value).trim();
        if (!clean) return false;
        const el = document.getElementById(fieldId);
        if (!el || (isFieldUserEdited(el) && !options.forceUserSelection)) return false;
        const current = String(el.value || '').trim();
        if (current) {
            if (current !== clean) {
                if (options.overwriteExisting) {
                    ensureSelectOption(el, clean);
                    el.value = clean;
                    el.dataset.liveFilled = '1';
                    el.dataset.liveDiffers = '';
                    el.classList.remove('lt-live-differs');
                    if (link && propName) link[propName] = clean;
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }
                el.dataset.liveDiffers = clean;
                el.classList.add('lt-live-differs');
                    showLiveDiffPill(el, clean);
            }
            return false;
        }
        ensureSelectOption(el, clean);
        el.value = clean;
        el.dataset.liveFilled = '1';
        if (link && propName) link[propName] = clean;
        el._liveApplying = true;
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el._liveApplying = false;
        return true;
    }

    function markEditableFields() {
        Object.values(FIELD_MAP).forEach(id => {
            const el = document.getElementById(id);
            if (!el || el._liveTelemetryEditHook) return;
            el._liveTelemetryEditHook = true;
            el.addEventListener('input', () => {
                if (!el._liveApplying) el.dataset.liveUserEdited = '1';
            });
            el.addEventListener('change', () => {
                if (!el._liveApplying) el.dataset.liveUserEdited = '1';
            });
        });
    }

    function normalizeResult(payload) {
        const results = payload?.results || [];
        return Array.isArray(results) ? results[0] || null : null;
    }

    function rowForCapture(link, sideKey, kind, row) {
        const side = sideKey === 'A' ? 'A' : 'B';
        const ifName = rowName(row);
        return {
            side,
            kind,
            ifName,
            vlanOuter: row?.outer_vlan || row?.outerVlan || '',
            vlanInner: row?.inner_vlan || row?.innerVlan || '',
            ip: row?.ip || row?.ip_address || '',
            parent: row?.parent || '',
            adminState: row?.admin_state || row?.adminState || '',
            operState: row?.oper_state || row?.operState || '',
            linkId: link?.id || ''
        };
    }

    function parseRowAttr(value) {
        try {
            return JSON.parse(value || '{}') || {};
        } catch (err) {
            console.warn('[LinkTelemetry] failed to parse telemetry row context:', err);
            return {};
        }
    }

    function rowKey(row, side, kind) {
        return `${side}:${kind}:${row?.name || row?.interface || ''}`;
    }

    function statusClass(value) {
        const state = String(value || '').trim().toLowerCase();
        if (['up', 'enabled', 'running', 'active', 'synchronized'].includes(state)) return 'up';
        if (['down', 'disabled', 'failed', 'blocked', 'inactive'].some(token => state.includes(token))) return 'down';
        if (!state || state === '--') return 'empty';
        return 'unknown';
    }

    function statusBadge(value, label) {
        const clean = String(value || '').trim();
        const cls = statusClass(clean);
        return `<span class="lt-state lt-state-${cls}" title="${escapeHtml(label || '')}: ${escapeHtml(clean || 'unknown')}">${escapeHtml(clean || '--')}</span>`;
    }

    function statePairBadge(state, labelPrefix) {
        const admin = state?.admin || state?.admin_state || state?.adminState || '';
        const oper = state?.oper || state?.oper_state || state?.operState || '';
        return `${statusBadge(admin, `${labelPrefix} admin`)}${statusBadge(oper, `${labelPrefix} oper`)}`;
    }

    function memberLacpState(state) {
        return [
            state?.role ? `role ${state.role}` : '',
            state?.port ? `port ${state.port}` : '',
            state?.protocol ? `protocol ${state.protocol}` : '',
            state?.flags ? `flags ${state.flags}` : ''
        ].filter(Boolean).join(' / ');
    }

    function rowState(row) {
        return {
            admin: String(row?.admin_state || row?.adminState || '').trim(),
            oper: String(row?.oper_state || row?.operState || '').trim()
        };
    }

    function persistSideState(link, suffix, row) {
        if (!link || !row) return;
        const state = rowState(row);
        link.linkDetails = link.linkDetails || {};
        link.linkDetails[`adminState${suffix}`] = state.admin;
        link.linkDetails[`operState${suffix}`] = state.oper;
        link.linkDetails[`speed${suffix}`] = rowSpeed(row);
        link.linkDetails[`mtu${suffix}`] = rowMtu(row);
        link.linkDetails[`fec${suffix}`] = rowValue(row, ['fec']);
    }

    function updateInterfaceStateField(fieldId, row) {
        const el = document.getElementById(fieldId);
        if (!el || !row) return;
        const state = rowState(row);
        el.dataset.liveAdminState = state.admin;
        el.dataset.liveOperState = state.oper;
        const originalTitle = el.dataset.liveBaseTitle || el.title || '';
        if (!el.dataset.liveBaseTitle) el.dataset.liveBaseTitle = originalTitle;
        const titleParts = [
            originalTitle,
            state.admin ? `Admin: ${state.admin}` : '',
            state.oper ? `Oper: ${state.oper}` : ''
        ].filter(Boolean);
        el.title = titleParts.join(' | ');
        const operClass = statusClass(state.oper);
        el.style.borderColor = operClass === 'up'
            ? '#27ae60'
            : (operClass === 'down' ? '#e74c3c' : '');
    }

    function vlanSummary(row) {
        const outer = rowOuterVlan(row);
        const inner = rowInnerVlan(row);
        const tpid = rowTpid(row);
        if (outer && inner) return `${outer}/${inner}${tpid ? ' ' + tpid : ''}`;
        if (outer) return `${outer}${tpid ? ' ' + tpid : ''}`;
        return '';
    }

    function vlanChipHtml(label, value, tone = '') {
        const clean = String(value === undefined || value === null ? '' : value).trim();
        return `<span class="lt-vlan-chip ${tone ? `lt-vlan-chip-${escapeHtml(tone)}` : ''}">
            <span>${escapeHtml(label)}</span><b>${escapeHtml(clean || 'none')}</b>
        </span>`;
    }

    function vlanChipsHtml(row, options = {}) {
        const outer = rowOuterVlan(row);
        const inner = rowInnerVlan(row);
        const tpid = rowTpid(row);
        if (!outer && !inner && !tpid && !options.unit && !options.relatedHtml) return '';
        return `<div class="lt-vlan-card${options.compact ? ' lt-vlan-card-compact' : ''}">
            <div class="lt-vlan-chip-row">
                ${vlanChipHtml('Outer', outer || 'untagged', outer ? 'outer' : 'empty')}
                ${vlanChipHtml('Inner', inner || 'none', inner ? 'inner' : 'empty')}
                ${tpid ? vlanChipHtml('TPID', tpid, 'tpid') : ''}
                ${options.unit ? vlanChipHtml('Unit', options.unit, 'unit') : ''}
            </div>
            ${options.relatedHtml || ''}
        </div>`;
    }

    function sameVlanStack(rowA, rowB) {
        const outerA = rowOuterVlan(rowA);
        const outerB = rowOuterVlan(rowB);
        const innerA = rowInnerVlan(rowA);
        const innerB = rowInnerVlan(rowB);
        if (!outerA || outerA !== outerB) return false;
        return (innerA || innerB) ? innerA === innerB : true;
    }

    function candidateLabel(candidate = {}) {
        const a = candidate.logicalIfA || candidate.subA || candidate.ifA || '--';
        const b = candidate.logicalIfB || candidate.subB || candidate.ifB || '--';
        const outer = candidate.outerVlanA || candidate.outerVlanB || '';
        const inner = candidate.innerVlanA || candidate.innerVlanB || '';
        const vlan = outer ? ` VLAN ${outer}${inner ? '/' + inner : ''}` : '';
        return `${candidate.kind || 'link'}: ${a} <-> ${b}${vlan}`;
    }

    function refreshButton(label = 'Refresh live') {
        return `<span class="lt-refresh-spinner" aria-hidden="true"></span><span class="lt-refresh-label">${escapeHtml(label)}</span>`;
    }

    function setRefreshBusy(btn, busy, label = 'Refresh live') {
        if (!btn) return;
        btn.disabled = !!busy;
        btn.classList.toggle('is-refreshing', !!busy);
        const labelNode = btn.querySelector('.lt-refresh-label');
        if (labelNode) {
            labelNode.textContent = busy ? 'Refreshing...' : label;
        } else {
            btn.textContent = busy ? 'Refreshing...' : label;
        }
    }

    function speedMtuSummary(row) {
        const speed = rowSpeed(row);
        const mtu = rowMtu(row);
        return [speed, mtu ? `MTU ${mtu}` : ''].filter(Boolean).join(' / ');
    }

    function selectableRows(side, extraRows = []) {
        const rows = [];
        const push = (kind, row) => {
            const name = rowName(row);
            if (!row || !name) return;
            const normalizedRow = row.name ? row : { ...row, name };
            const vlan = vlanSummary(normalizedRow);
            const state = [normalizedRow.admin_state, normalizedRow.oper_state].filter(Boolean).join('/');
            rows.push({
                kind,
                row: normalizedRow,
                key: `${kind}:${name}`,
                label: `${name}${vlan ? '  VLAN ' + vlan : ''}`,
                detail: [state, vlan ? `VLAN ${vlan}` : '', attachmentSummary(normalizedRow, kind), speedMtuSummary(normalizedRow)].filter(Boolean).join(' / ')
            });
        };
        asRows(side?.subifs).forEach(row => push('sub', row));
        asRows(side?.bundles).forEach(row => push('bundle', row));
        asRows(side?.physical).forEach(row => push('physical', row));
        asRows(extraRows).forEach(item => push(item.kind, item.row));
        const unique = [];
        const seen = new Set();
        rows.forEach(item => {
            if (seen.has(item.key)) return;
            seen.add(item.key);
            unique.push(item);
        });
        return unique.sort((a, b) => {
            const score = (item) => {
                const row = item.row || {};
                const oper = String(row.oper_state || '').toLowerCase();
                const hasService = !!(row.bridge_domain || row.ip || rowOuterVlan(row) || rowInnerVlan(row) || (row.attachment && row.attachment.kind && row.attachment.kind !== 'none'));
                if (item.kind === 'sub' && hasService && oper === 'up') return 0;
                if (item.kind === 'sub') return 1;
                if (item.kind === 'bundle' && oper === 'up') return 2;
                if (item.kind === 'physical' && (row.lldp_neighbor || oper === 'up')) return 3;
                return 7;
            };
            const delta = score(a) - score(b);
            return delta || a.label.localeCompare(b.label);
        });
    }

    function selectionToDynamicSide(selection) {
        const kind = selection?.kind || 'physical';
        const row = selection?.row || {};
        return {
            kind,
            sub: kind === 'sub' ? row : null,
            bundle: kind === 'bundle' ? row : null,
            physical: kind === 'physical' ? row : null,
            ifName: row.name || row.interface || '',
            row,
            key: selection?.key || '',
            detail: selection?.detail || ''
        };
    }

    function dynamicKindForSelections(selA, selB) {
        const kinds = [selA?.kind, selB?.kind];
        if (kinds.includes('sub')) {
            const parentA = selA?.row?.parent || '';
            const parentB = selB?.row?.parent || '';
            return parentA.startsWith('bundle-') || parentB.startsWith('bundle-') ? 'sub-bundle' : 'sub-interface';
        }
        if (kinds.includes('bundle')) return 'bundle';
        return 'physical';
    }

    function attachmentSummary(row, kind) {
        if (!row) return '';
        const att = row.attachment || {};
        if (att.kind && att.kind !== 'none') {
            return [
                att.kind,
                att.service_name || att.serviceName,
                att.vrf ? `VRF ${att.vrf}` : '',
                att.bridge_domain || att.bridgeDomain ? `BD ${att.bridge_domain || att.bridgeDomain}` : '',
                att.evi ? `EVI ${att.evi}` : ''
            ].filter(Boolean).join(' / ');
        }
        if (kind === 'sub') {
            return row.bridge_domain || row.ip || '';
        }
        if (kind === 'bundle') {
            const members = Array.isArray(row.members) ? row.members.map(m => m.interface).filter(Boolean) : [];
            const configMembers = Array.isArray(row.members_config) ? row.members_config.map(m => m.interface).filter(Boolean) : [];
            return configMembers.length ? configMembers.join(', ') : (members.length ? members.join(', ') : (row.lacp_system_id || ''));
        }
        if (row.lldp_neighbor) {
            return `${row.lldp_neighbor}${row.lldp_neighbor_interface ? ' / ' + row.lldp_neighbor_interface : ''}`;
        }
        return '';
    }

    function protocolSummary(row) {
        const proto = row?.protocols || {};
        const parts = [];
        if (Array.isArray(proto.bgp_neighbors) && proto.bgp_neighbors.length) {
            proto.bgp_neighbors.forEach(n => parts.push(`BGP ${n.peer || ''} ${n.state || 'configured'}`.trim()));
        }
        if (proto.isis) parts.push(`ISIS ${proto.isis}`);
        if (proto.ldp) parts.push(`LDP ${proto.ldp}`);
        if (proto.ospf) parts.push(`OSPF ${proto.ospf}`);
        return parts.join(' | ');
    }

    function protocolDetailsHtml(row) {
        const proto = row?.protocols || {};
        const summary = protocolSummary(row);
        if (!summary) return 'not configured';
        const rows = [];
        if (Array.isArray(proto.bgp_neighbors)) {
            proto.bgp_neighbors.forEach(n => {
                rows.push(['BGP', n.peer || '--', n.state || 'configured', n.afi || '', n.remote_as ? `remote-as ${n.remote_as}` : '']);
            });
        }
        if (proto.isis) rows.push(['ISIS', rowName(row), proto.isis, '', '']);
        if (proto.ospf) rows.push(['OSPF', rowName(row), proto.ospf, '', '']);
        if (proto.ldp) rows.push(['LDP', rowName(row), proto.ldp, '', '']);
        const body = rows.map(cells => `<tr>${cells.map(cell => `<td>${escapeHtml(cell || '--')}</td>`).join('')}</tr>`).join('');
        return `<details class="lt-protocol-details">
            <summary><span>Configured protocols</span><b>${rows.length}</b></summary>
            <table>
                <thead><tr><th>Protocol</th><th>Peer/If</th><th>State</th><th>AFI</th><th>Extra</th></tr></thead>
                <tbody>${body}</tbody>
            </table>
        </details>`;
    }

    function telemetryDetail(row, kind, side) {
        return [
            speedMtuSummary(row),
            kind === 'bundle' ? bundleMemberSummary(row, side) : '',
            row?.transceiver || row?.lacp_system_id || row?.fec || '',
            protocolSummary(row)
        ].filter(Boolean).join(' / ');
    }

    function val(value, fallback = '--') {
        const clean = String(value === undefined || value === null ? '' : value).trim();
        return clean || fallback;
    }

    function attachmentDetail(row) {
        const att = row?.attachment || {};
        if (!att.kind || att.kind === 'none') return 'not attached';
        return [
            att.kind,
            att.service_name || att.serviceName,
            att.vrf ? `vrf=${att.vrf}` : '',
            att.bridge_domain || att.bridgeDomain ? `bd=${att.bridge_domain || att.bridgeDomain}` : '',
            att.evi ? `evi=${att.evi}` : '',
            att.rd ? `rd=${att.rd}` : '',
            att.rt ? `rt=${att.rt}` : ''
        ].filter(Boolean).join(' | ');
    }

    function rowRawValue(row, keys) {
        const raw = row?.raw || {};
        for (const key of keys) {
            if (raw[key]) return raw[key];
            if (raw.config && raw.config[key]) return raw.config[key];
            if (raw.counters && raw.counters[key]) return raw.counters[key];
        }
        return '';
    }

    function rowValue(row, keys) {
        if (!row) return '';
        for (const key of keys) {
            if (row[key]) return String(row[key]).trim();
        }
        return String(rowRawValue(row, keys) || '').trim();
    }

    function rowOuterVlan(row) {
        return rowValue(row, ['outer_vlan', 'outerVlan', 'vlan', 'vlan_id', 'vlanId', 'dot1q']);
    }

    function rowInnerVlan(row) {
        return rowValue(row, ['inner_vlan', 'innerVlan', 'second_dot1q', 'secondDot1q']);
    }

    function rowTpid(row) {
        return rowValue(row, ['tpid', 'vlan_tpid', 'vlanTpid', 'ethertype']);
    }

    function rowVlanManipulation(row) {
        return rowValue(row, ['vlan_manipulation_egress', 'vlanManipulationEgress', 'egress_mapping', 'egressMapping']);
    }

    function rowMtu(row) {
        return rowValue(row, ['mtu', 'l2_mtu', 'l2Mtu', 'l3_mtu', 'l3Mtu', 'max_frame_size', 'maxFrameSize', 'max-frame-size']);
    }

    function rowSpeed(row) {
        return rowValue(row, ['speed', 'speed_sum', 'speedSum', 'bandwidth']);
    }

    function rowName(row) {
        return String(row?.name || row?.interface || row?.ifName || '').trim();
    }

    function findRowByName(rows, name) {
        if (!Array.isArray(rows) || !name) return null;
        const wanted = String(name || '').trim();
        return rows.find(row => row && rowName(row) === wanted) || null;
    }

    function memberSummaryLine(member, physical) {
        const name = String(member?.interface || '').trim();
        if (!name) return '';
        const state = physical ? rowState(physical) : {};
        const lacp = memberLacpState({
            role: member?.role || '',
            port: member?.port_state || '',
            protocol: member?.protocol_state || '',
            flags: member?.flags || '',
        });
        const liveState = [state.admin ? `admin ${state.admin}` : '', state.oper ? `oper ${state.oper}` : '']
            .filter(Boolean)
            .join('/');
        return [name, liveState, lacp].filter(Boolean).join(' | ');
    }

    function bundleMemberSummary(bundle, side) {
        if (!bundle) return '';
        const byName = new Map();
        asRows(bundle.members_config).forEach(member => {
            const name = String(member?.interface || '').trim();
            if (!name) return;
            byName.set(name, { ...member, _configured: true });
        });
        asRows(bundle.members).forEach(member => {
            const name = String(member?.interface || '').trim();
            if (!name) return;
            byName.set(name, { ...(byName.get(name) || {}), ...member, _live: true });
        });
        return Array.from(byName.values()).map(member => {
            const physical = findRowByName(side?.physical, member.interface);
            const line = memberSummaryLine(member, physical);
            if (!line) return '';
            return member._live ? line : `${line} | configured-only`;
        }).filter(Boolean).join('; ');
    }

    function bundleMemberTable(bundle, side) {
        if (!bundle) return '';
        const byName = new Map();
        asRows(bundle.members_config).forEach(member => {
            const name = String(member?.interface || '').trim();
            if (name) byName.set(name, { ...member, _configured: true });
        });
        asRows(bundle.members).forEach(member => {
            const name = String(member?.interface || '').trim();
            if (name) byName.set(name, { ...(byName.get(name) || {}), ...member, _live: true });
        });
        const rows = Array.from(byName.values()).map(member => {
            const physical = findRowByName(side?.physical, member.interface);
            const state = physical ? rowState(physical) : {};
            const lacp = memberLacpState({
                role: member?.role || '',
                port: member?.port_state || '',
                protocol: member?.protocol_state || '',
                flags: member?.flags || '',
            }) || (member._live ? 'live' : 'configured');
            return `<tr>
                <td>${escapeHtml(member.interface || '')}</td>
                <td>${escapeHtml([state.admin, state.oper].filter(Boolean).join('/') || 'not reported')}</td>
                <td>${escapeHtml(lacp)}</td>
                <td>${escapeHtml(member._live ? 'live+config' : 'configured-only')}</td>
            </tr>`;
        }).join('');
        if (!rows) return '';
        return `<table class="lt-member-mini-table">
            <thead><tr><th>Member</th><th>Physical</th><th>LACP</th><th>Source</th></tr></thead>
            <tbody>${rows}</tbody>
        </table>`;
    }

    function candidateKey(candidate = {}) {
        return [
            candidate.kind || '',
            candidate.ifA || '',
            candidate.parentA || '',
            candidate.subA || '',
            candidate.ifB || '',
            candidate.parentB || '',
            candidate.subB || ''
        ].join('|');
    }

    function buildLogicalCandidates(result) {
        const sideA = result?.side_a || result?.sideA || {};
        const sideB = result?.side_b || result?.sideB || {};
        const current = result?.correlation || result?.lldp || {};
        const seen = new Set();
        const out = [];
        const push = (candidate) => {
            const key = `${candidate.kind}:${candidate.ifA}:${candidate.ifB}:${candidate.subA}:${candidate.subB}`;
            if (seen.has(key)) return;
            seen.add(key);
            out.push(candidate);
        };
        asRows(current.candidates).forEach(push);
        if (current.kind && current.kind !== 'none') push(current);
        asRows(sideA.subifs).forEach(subA => {
            asRows(sideB.subifs).forEach(subB => {
                if (!sameVlanStack(subA, subB)) return;
                const parentA = subA.parent || String(subA.name || '').split('.')[0];
                const parentB = subB.parent || String(subB.name || '').split('.')[0];
                push({
                    kind: parentA.startsWith('bundle-') || parentB.startsWith('bundle-') ? 'sub-bundle' : 'sub-interface',
                    ifA: parentA,
                    ifB: parentB,
                    parentA,
                    parentB,
                    subA: subA.name,
                    subB: subB.name,
                    evidence: `VLAN ${subA.outer_vlan}${subA.inner_vlan ? '/' + subA.inner_vlan : ''}`,
                    confidence: 'inferred',
                    source: 'candidate'
                });
            });
        });
        if (!out.length) out.push({ ...current, kind: current.kind || 'none' });
        return out;
    }

    function activeCorrelation(link, result) {
        const candidates = buildLogicalCandidates(result);
        const selectedKey = link?.linkDetails?.liveCandidateKey;
        if (selectedKey) {
            const byKey = candidates.find(candidate => candidateKey(candidate) === selectedKey);
            if (byKey) return byKey;
        }
        const idx = Math.max(0, Math.min(Number(link?.linkDetails?.liveCandidateIndex || 0), candidates.length - 1));
        return candidates[idx] || candidates[0] || {};
    }

    function selectedRowsForCorrelation(link, result) {
        const sideA = result?.side_a || result?.sideA || {};
        const sideB = result?.side_b || result?.sideB || {};
        const corr = activeCorrelation(link, result);
        const pick = (side, suffix) => {
            const logicalName = corr[`logicalIf${suffix}`] || corr[`sub${suffix}`] || corr[`if${suffix}`] || corr[`parent${suffix}`] || '';
            const parentName = corr[`parent${suffix}`] || String(logicalName).split('.')[0] || '';
            const memberName = corr[`member${suffix}`] || '';
            const sub = findRowByName(side.subifs, corr[`sub${suffix}`] || logicalName);
            const bundle = findRowByName(side.bundles, parentName) || findRowByName(side.bundles, logicalName);
            const physical = findRowByName(side.physical, memberName) || findRowByName(side.physical, logicalName) || findRowByName(side.physical, parentName);
            return { sub, bundle, physical, ifName: logicalName || parentName };
        };
        return { A: pick(sideA, 'A'), B: pick(sideB, 'B') };
    }

    function escapeHtml(value) {
        return String(value === undefined || value === null ? '' : value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function encodeRowAttr(row) {
        return escapeHtml(JSON.stringify(row || {}));
    }

    window.LinkTelemetry = {
        _lastByLink: new Map(),
        _lastSignatureByLink: new Map(),
        _refreshSeq: new Map(),
        _subscribers: new Map(),
        _modalTimer: null,
        _canvasWatcher: null,
        _lastLinkSignature: '',

        async refreshLink(editor, link, options = {}) {
            if (!editor || !link || !link.device1 || !link.device2) return null;
            this.installAutoCorrelation(editor);
            markEditableFields();
            const requestSignature = this._linkSignature(editor, link);
            const requestSeq = (this._refreshSeq.get(link.id) || 0) + 1;
            this._refreshSeq.set(link.id, requestSeq);
            const body = {
                force: !!options.force,
                links: [{
                    linkId: link.id,
                    deviceA: devicePayload(editor, link.device1),
                    deviceB: devicePayload(editor, link.device2),
                    hintIfA: link.device1Interface || link.linkDetails?.interfaceA || '',
                    hintIfB: link.device2Interface || link.linkDetails?.interfaceB || '',
                    previousCorrelation: link.linkDetails?.live?.correlation || link.linkDetails?.live?.lldp || null,
                    force: !!options.force
                }]
            };
            const resp = await telemetryFetch('/api/link-telemetry/refresh', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            if (!resp.ok) throw new Error(`Link telemetry refresh failed: HTTP ${resp.status}`);
            const payload = await resp.json();
            const result = normalizeResult(payload);
            if (!result) return null;
            if (!this._isFreshRefresh(editor, link, requestSignature, requestSeq)) {
                console.debug('[LinkTelemetry] ignored stale refresh for link:', link.id);
                return null;
            }
            link.linkDetails = link.linkDetails || {};
            link.linkDetails.live = result;
            this._lastByLink.set(link.id, result);
            this._lastSignatureByLink.set(link.id, requestSignature);
            this.applyAutoFill(editor, link, result, { overwriteExisting: options.overwriteExisting !== false });
            if (options.render !== false && this._modalStillEditing(editor, link)) {
                this.renderTelemetry(link, result);
            }
            window.LinkLiveDrawer?.update(link, result);
            return result;
        },

        async correlateAcrossCanvas(editor, options = {}) {
            const devices = (editor?.objects || [])
                .filter(o => o && o.type === 'device')
                .map(o => devicePayload(editor, o.id));
            if (!devices.length) return [];
            const resp = await telemetryFetch('/api/link-telemetry/correlate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ devices, force: !!options.force })
            });
            if (!resp.ok) throw new Error(`LLDP correlate failed: HTTP ${resp.status}`);
            const payload = await resp.json();
            return payload.edges || [];
        },

        async refreshAll(editor, links = null, options = {}) {
            const rows = (Array.isArray(links) ? links : (editor?.objects || []).filter(o => o && o.type === 'link'))
                .filter(link => link && link.device1 && link.device2);
            const out = [];
            for (const link of rows) {
                try {
                    out.push(await this.refreshLink(editor, link, options));
                } catch (err) {
                    console.warn('[LinkTelemetry] refreshAll failed for link:', link.id, err);
                }
            }
            return out;
        },

        startModalAutoRefresh(editor, link, intervalMs = 15000) {
            this.stopModalAutoRefresh();
            if (!editor || !link?.id) return;
            this._modalTimer = window.setInterval(() => {
                const modal = document.getElementById('link-details-modal');
                if (!modal || !modal.classList.contains('show')) {
                    this.stopModalAutoRefresh();
                    return;
                }
                this.refreshLink(editor, link).catch(err => console.warn('[LinkTelemetry] modal auto-refresh failed:', err));
            }, Math.max(12000, intervalMs));
        },

        stopModalAutoRefresh() {
            if (this._modalTimer) window.clearInterval(this._modalTimer);
            this._modalTimer = null;
        },

        _linkSignature(editor, link) {
            if (!link) return '';
            const deviceA = (editor?.objects || []).find(o => o && o.id === link.device1) || {};
            const deviceB = (editor?.objects || []).find(o => o && o.id === link.device2) || {};
            const nameFor = device => device.label || device.name || device.hostname || device.id || '';
            const hostFor = device => device.sshConfig?.host || device.host || device.mgmt_ip || device.managementIp || '';
            return [
                link.id || '',
                link.device1 || '',
                link.device2 || '',
                link.device1Interface || link.linkDetails?.interfaceA || '',
                link.device2Interface || link.linkDetails?.interfaceB || '',
                nameFor(deviceA),
                nameFor(deviceB),
                hostFor(deviceA),
                hostFor(deviceB)
            ].join('|');
        },

        _isFreshRefresh(editor, link, requestSignature, requestSeq) {
            if (!link?.id || this._refreshSeq.get(link.id) !== requestSeq) return false;
            const liveLink = (editor?.objects || []).find(o => o && o.id === link.id);
            if (!liveLink) return false;
            return this._linkSignature(editor, liveLink) === requestSignature;
        },

        _modalStillEditing(editor, link) {
            const modal = document.getElementById('link-details-modal');
            if (!modal || !modal.classList.contains('show')) return false;
            const current = editor?.editingLink || window.topologyEditor?.editingLink;
            return !!(current && link && current.id === link.id);
        },

        getCachedResult(link, editor = window.topologyEditor || null) {
            if (!link?.id) return null;
            const result = this._lastByLink.get(link.id);
            if (!result) return null;
            const expected = this._lastSignatureByLink.get(link.id);
            const current = this._linkSignature(editor, link);
            return expected && current && expected === current ? result : null;
        },

        renderLoading(link, message = 'Refreshing live telemetry...') {
            if (link && !this._modalStillEditing(window.topologyEditor || null, link)) return;
            const live = document.getElementById('lt-live-telemetry-panel');
            if (live) {
                live.innerHTML = `<div class="lt-live-empty">${escapeHtml(message)}</div>`;
            }
            this.renderDynamicLinkTable(link || {}, {});
        },

        installAutoCorrelation(editor) {
            if (!editor || this._canvasWatcher) return;
            const signature = () => (editor.objects || [])
                .filter(o => o && o.type === 'link')
                .map(o => `${o.id}:${o.device1 || ''}:${o.device2 || ''}`)
                .sort()
                .join('|');
            this._lastLinkSignature = signature();
            this._canvasWatcher = window.setInterval(() => {
                const next = signature();
                if (next === this._lastLinkSignature) return;
                this._lastLinkSignature = next;
                const links = (editor.objects || []).filter(o => o && o.type === 'link' && o.device1 && o.device2);
                this.refreshAll(editor, links, { hint: 'canvas-change' }).catch(err => console.warn('[LinkTelemetry] canvas correlation failed:', err));
            }, 1500);
        },

        subscribeAutoRefresh(editor, link, intervalMs = 15000) {
            if (!link?.id) return;
            this.unsubscribeAutoRefresh(link.id);
            const timer = window.setInterval(() => {
                this.refreshLink(editor, link).catch(err => console.warn('[LinkTelemetry] auto-refresh failed:', err));
            }, Math.max(8000, intervalMs));
            this._subscribers.set(link.id, timer);
        },

        unsubscribeAutoRefresh(linkId) {
            const timer = this._subscribers.get(linkId);
            if (timer) window.clearInterval(timer);
            this._subscribers.delete(linkId);
        },

        applyAutoFill(editor, link, result, options = {}) {
            const sideA = result.side_a || result.sideA || {};
            const sideB = result.side_b || result.sideB || {};
            const lldp = activeCorrelation(link, result);
            const ifA = bestPhysical(sideA, lldp.memberA || lldp.ifA);
            const ifB = bestPhysical(sideB, lldp.memberB || lldp.ifB);
            const subA = findRowByName(sideA.subifs, lldp.subA) || bestSub(sideA, ifA?.name || lldp.parentA);
            const subB = findRowByName(sideB.subifs, lldp.subB) || bestSub(sideB, ifB?.name || lldp.parentB);
            const bundleA = findRowByName(sideA.bundles, lldp.parentA || lldp.ifA) || bestBundle(sideA, ifA?.name || lldp.ifA);
            const bundleB = findRowByName(sideB.bundles, lldp.parentB || lldp.ifB) || bestBundle(sideB, ifB?.name || lldp.ifB);
            const fill = (fieldId, value, prop) => setLiveValue(fieldId, value, link, prop, options);
            const selections = this._currentSelections(link, result);
            const selectedA = selections.A?.row || {};
            const selectedB = selections.B?.row || {};
            const selectedIfA = selectedA.name || selectedA.interface || ifA?.name || lldp.ifA;
            const selectedIfB = selectedB.name || selectedB.interface || ifB?.name || lldp.ifB;
            const logicalIfA = lldp.logicalIfA || (selections.A?.kind === 'sub' ? selectedIfA : (selectedA.parent || selectedIfA));
            const logicalIfB = lldp.logicalIfB || (selections.B?.kind === 'sub' ? selectedIfB : (selectedB.parent || selectedIfB));
            fill(FIELD_MAP.interfaceA, logicalIfA, 'device1Interface');
            fill(FIELD_MAP.interfaceB, logicalIfB, 'device2Interface');
            fill(FIELD_MAP.transceiverA, ifA?.transceiver, 'device1Transceiver');
            fill(FIELD_MAP.transceiverB, ifB?.transceiver, 'device2Transceiver');
            const effectiveSubA = selections.A?.kind === 'sub' ? selectedA : subA;
            const effectiveSubB = selections.B?.kind === 'sub' ? selectedB : subB;
            const effectiveBundleA = selections.A?.kind === 'bundle' ? selectedA : bundleA;
            const effectiveBundleB = selections.B?.kind === 'bundle' ? selectedB : bundleB;
            const stateRowA = selectedA && rowName(selectedA) ? selectedA : (effectiveSubA || effectiveBundleA || ifA);
            const stateRowB = selectedB && rowName(selectedB) ? selectedB : (effectiveSubB || effectiveBundleB || ifB);
            const outerA = rowOuterVlan(effectiveSubA);
            const outerB = rowOuterVlan(effectiveSubB);
            const innerA = rowInnerVlan(effectiveSubA);
            const innerB = rowInnerVlan(effectiveSubB);
            // #region agent log
            agentDebugLog('H3', 'applyAutoFill VLAN source rows', {
                linkId: link?.id || '',
                corr: {
                    kind: lldp.kind,
                    ifA: lldp.ifA,
                    ifB: lldp.ifB,
                    subA: lldp.subA,
                    subB: lldp.subB,
                    outerVlanA: lldp.outerVlanA,
                    innerVlanA: lldp.innerVlanA,
                    outerVlanB: lldp.outerVlanB,
                    innerVlanB: lldp.innerVlanB,
                    evidence: lldp.evidence,
                },
                selections: {
                    A: { kind: selections.A?.kind, name: rowName(selectedA), outer: rowOuterVlan(selectedA), inner: rowInnerVlan(selectedA) },
                    B: { kind: selections.B?.kind, name: rowName(selectedB), outer: rowOuterVlan(selectedB), inner: rowInnerVlan(selectedB) },
                },
                effective: {
                    A: { name: rowName(effectiveSubA), parent: effectiveSubA?.parent, outer: outerA, inner: innerA },
                    B: { name: rowName(effectiveSubB), parent: effectiveSubB?.parent, outer: outerB, inner: innerB },
                },
                savedLinkTags: {
                    device1OuterTag: link?.device1OuterTag,
                    device1InnerTag: link?.device1InnerTag,
                    device2OuterTag: link?.device2OuterTag,
                    device2InnerTag: link?.device2InnerTag,
                }
            });
            // #endregion
            fill(FIELD_MAP.subInterfaceA, effectiveSubA?.name, null);
            fill(FIELD_MAP.subInterfaceB, effectiveSubB?.name, null);
            fill(FIELD_MAP.bundleA, effectiveBundleA?.name, null);
            fill(FIELD_MAP.bundleB, effectiveBundleB?.name, null);
            if (outerA || innerA) fill(FIELD_MAP.vlanModeA, 'vlan-tags', 'device1VlanMode');
            if (outerB || innerB) fill(FIELD_MAP.vlanModeB, 'vlan-tags', 'device2VlanMode');
            fill(FIELD_MAP.outerTagA, outerA, 'device1OuterTag');
            fill(FIELD_MAP.outerTagB, outerB, 'device2OuterTag');
            fill(FIELD_MAP.innerTagA, innerA, 'device1InnerTag');
            fill(FIELD_MAP.innerTagB, innerB, 'device2InnerTag');
            fill(FIELD_MAP.ipAddressA, effectiveSubA?.ip || selectedA.ip || ifA?.ip, 'device1IpAddress');
            fill(FIELD_MAP.ipAddressB, effectiveSubB?.ip || selectedB.ip || ifB?.ip, 'device2IpAddress');
            persistSideState(link, 'A', stateRowA);
            persistSideState(link, 'B', stateRowB);
            updateInterfaceStateField(FIELD_MAP.interfaceA, stateRowA);
            updateInterfaceStateField(FIELD_MAP.interfaceB, stateRowB);
            this._refreshInterfaceLabels(editor, link, logicalIfA, logicalIfB);
            if (editor?.history?.saveState) editor.history.saveState();
            if (editor?.drawing?.draw) editor.drawing.draw();
        },

        applyRowSelection(editor, link, side, kind, row, options = {}) {
            if (!link || !row) return false;
            const suffix = side === 'B' ? 'B' : 'A';
            const isA = suffix === 'A';
            const set = (fieldId, value, prop) => setLiveValue(fieldId, value, link, prop, {
                overwriteExisting: true,
                forceUserSelection: !!options.forceUserSelection,
                ...options,
            });
            const ifaceName = row.name || row.interface || '';
            if (kind === 'sub') {
                set(isA ? FIELD_MAP.subInterfaceA : FIELD_MAP.subInterfaceB, ifaceName, null);
                set(isA ? FIELD_MAP.interfaceA : FIELD_MAP.interfaceB, ifaceName, isA ? 'device1Interface' : 'device2Interface');
                if (rowOuterVlan(row) || rowInnerVlan(row)) set(isA ? FIELD_MAP.vlanModeA : FIELD_MAP.vlanModeB, 'vlan-tags', isA ? 'device1VlanMode' : 'device2VlanMode');
                set(isA ? FIELD_MAP.outerTagA : FIELD_MAP.outerTagB, rowOuterVlan(row), isA ? 'device1OuterTag' : 'device2OuterTag');
                set(isA ? FIELD_MAP.innerTagA : FIELD_MAP.innerTagB, rowInnerVlan(row), isA ? 'device1InnerTag' : 'device2InnerTag');
                set(isA ? FIELD_MAP.ipAddressA : FIELD_MAP.ipAddressB, row.ip || row.ip_address, isA ? 'device1IpAddress' : 'device2IpAddress');
            } else if (kind === 'bundle') {
                set(isA ? FIELD_MAP.bundleA : FIELD_MAP.bundleB, ifaceName, null);
                set(isA ? FIELD_MAP.interfaceA : FIELD_MAP.interfaceB, ifaceName, isA ? 'device1Interface' : 'device2Interface');
            } else {
                set(isA ? FIELD_MAP.interfaceA : FIELD_MAP.interfaceB, ifaceName, isA ? 'device1Interface' : 'device2Interface');
                set(isA ? FIELD_MAP.transceiverA : FIELD_MAP.transceiverB, row.transceiver, isA ? 'device1Transceiver' : 'device2Transceiver');
            }
            link.linkDetails = link.linkDetails || {};
            persistSideState(link, suffix, row);
            updateInterfaceStateField(isA ? FIELD_MAP.interfaceA : FIELD_MAP.interfaceB, row);
            link.linkDetails[`liveSelected${suffix}`] = { kind, row };
            this._refreshInterfaceLabels(editor, link, isA ? ifaceName : null, isA ? null : ifaceName);
            if (options.manual !== false) {
                link.linkDetails.liveSelectionManual = link.linkDetails.liveSelectionManual || {};
                link.linkDetails.liveSelectionManual[suffix] = true;
            }
            if (editor?.history?.saveState) editor.history.saveState();
            if (editor?.drawing?.draw) editor.drawing.draw();
            return true;
        },

        getXrayContextForLink(link, preferredPov = '') {
            if (!link) return {};
            const result = link.id ? this._lastByLink.get(link.id) : null;
            let selections = {};
            if (result) {
                selections = this._currentSelections(link, result) || {};
            } else {
                const details = link.linkDetails || {};
                selections = {
                    A: details.liveSelectedA,
                    B: details.liveSelectedB
                };
            }
            const rowA = selections.A?.row ? rowForCapture(link, 'A', selections.A.kind || 'physical', selections.A.row) : null;
            const rowB = selections.B?.row ? rowForCapture(link, 'B', selections.B.kind || 'physical', selections.B.row) : null;
            const srcRows = {
                device1: rowA,
                device2: rowB
            };
            const pov = preferredPov === 'device2' ? 'device2' : 'device1';
            const srcRow = srcRows[pov] || rowA || rowB || null;
            return srcRow ? { srcRow, srcRows, preferredPov: pov } : {};
        },

        _refreshInterfaceLabels(editor, link, ifA, ifB) {
            if (!editor || !link || typeof editor.createOrUpdateInterfaceTextBox !== 'function') return;
            const labelA = String(ifA || link.device1Interface || link.linkDetails?.interfaceA || '').trim();
            const labelB = String(ifB || link.device2Interface || link.linkDetails?.interfaceB || '').trim();
            if (labelA) editor.createOrUpdateInterfaceTextBox(link, 'device1', labelA);
            if (labelB) editor.createOrUpdateInterfaceTextBox(link, 'device2', labelB);
        },

        _fallbackSelectableRows(link, result, suffix) {
            const out = [];
            const seen = new Set();
            const add = (kind, name, extras = {}) => {
                const clean = String(name || '').trim();
                if (!clean) return;
                const key = `${kind}:${clean}`;
                if (seen.has(key)) return;
                seen.add(key);
                out.push({
                    kind,
                    row: {
                        name: clean,
                        parent: extras.parent || (clean.includes('.') ? clean.split('.')[0] : ''),
                        outer_vlan: extras.outer_vlan || extras.outerVlan || '',
                        inner_vlan: extras.inner_vlan || extras.innerVlan || '',
                        ip: extras.ip || '',
                        admin_state: extras.admin_state || '',
                        oper_state: extras.oper_state || '',
                        description: extras.description || 'fallback from correlation/canvas'
                    }
                });
            };
            const sideKey = suffix === 'B' ? 'B' : 'A';
            const corr = result?.correlation || result?.lldp || {};
            const fromCandidate = (candidate) => {
                const subName = candidate[`sub${sideKey}`] || '';
                const ifName = candidate[`if${sideKey}`] || candidate[`parent${sideKey}`] || '';
                const parent = candidate[`parent${sideKey}`] || ifName;
                const vlanExtras = {
                    outer_vlan: candidate[`outerVlan${sideKey}`] || candidate[`outer_vlan_${sideKey.toLowerCase()}`] || '',
                    inner_vlan: candidate[`innerVlan${sideKey}`] || candidate[`inner_vlan_${sideKey.toLowerCase()}`] || '',
                };
                if (subName) {
                    add('sub', subName, { parent, ...vlanExtras, description: candidate.evidence || 'correlation candidate' });
                } else if (String(ifName).startsWith('bundle-')) {
                    add('bundle', ifName, { description: candidate.evidence || 'correlation candidate' });
                } else {
                    add('physical', ifName, { description: candidate.evidence || 'correlation candidate' });
                }
            };
            asRows(corr.candidates).forEach(fromCandidate);
            fromCandidate(corr);
            const details = link?.linkDetails || {};
            if (sideKey === 'A') {
                add('sub', details.subInterfaceA, { parent: details.interfaceA || link?.device1Interface });
                add('bundle', details.bundleA);
                add('physical', link?.device1Interface || details.interfaceA);
            } else {
                add('sub', details.subInterfaceB, { parent: details.interfaceB || link?.device2Interface });
                add('bundle', details.bundleB);
                add('physical', link?.device2Interface || details.interfaceB);
            }
            return out;
        },

        _candidateScopedRows(link, result, suffix) {
            const sideKey = suffix === 'B' ? 'B' : 'A';
            const side = sideKey === 'B' ? (result?.side_b || result?.sideB || {}) : (result?.side_a || result?.sideA || {});
            const corr = result?.correlation || result?.lldp || {};
            const rows = [];
            const seen = new Set();
            const addResolved = (kind, name, candidate = {}, extras = {}) => {
                const clean = String(name || '').trim();
                if (!clean) return;
                const key = `${kind}:${clean}`;
                if (seen.has(key)) return;
                let row = null;
                if (kind === 'sub') row = findRowByName(side.subifs, clean);
                else if (kind === 'bundle') row = findRowByName(side.bundles, clean.split('.')[0]);
                else row = findRowByName(side.physical, clean);
                const fallback = {
                    name: kind === 'bundle' ? clean.split('.')[0] : clean,
                    parent: extras.parent || candidate[`parent${sideKey}`] || (clean.includes('.') ? clean.split('.')[0] : ''),
                    outer_vlan: extras.outer_vlan || extras.outerVlan || candidate[`outerVlan${sideKey}`] || candidate[`outer_vlan_${sideKey.toLowerCase()}`] || '',
                    inner_vlan: extras.inner_vlan || extras.innerVlan || candidate[`innerVlan${sideKey}`] || candidate[`inner_vlan_${sideKey.toLowerCase()}`] || '',
                    ip: extras.ip || '',
                    admin_state: extras.admin_state || candidate[`state${sideKey}`]?.admin || '',
                    oper_state: extras.oper_state || candidate[`state${sideKey}`]?.oper || '',
                    description: extras.description || candidate.evidence || 'correlation candidate'
                };
                seen.add(key);
                rows.push({ kind, row: row || fallback });
            };
            const addCandidate = (candidate = {}) => {
                if (!candidate || candidate.kind === 'none') return;
                const subName = candidate[`sub${sideKey}`] || '';
                const logicalName = candidate[`logicalIf${sideKey}`] || '';
                const ifName = candidate[`if${sideKey}`] || '';
                const parentName = candidate[`parent${sideKey}`] || (subName ? subName.split('.')[0] : '');
                const memberName = candidate[`member${sideKey}`] || '';
                if (subName) {
                    addResolved('sub', subName, candidate, { parent: parentName || logicalName || ifName });
                }
                const logicalBase = String(logicalName || ifName || parentName || '').split('.')[0];
                if (logicalBase.startsWith('bundle-')) {
                    addResolved('bundle', logicalBase, candidate);
                } else if (!subName && logicalBase) {
                    addResolved('physical', logicalBase, candidate);
                }
                if (memberName) {
                    addResolved('physical', memberName, candidate, {
                        admin_state: candidate[`memberState${sideKey}`]?.admin || '',
                        oper_state: candidate[`memberState${sideKey}`]?.oper || '',
                        description: candidate.memberEvidence || candidate.evidence || 'LACP member evidence'
                    });
                }
            };
            asRows(corr.candidates).forEach(addCandidate);
            addCandidate(corr);
            const activeParents = new Set(rows
                .map(item => item?.row?.parent || (rowName(item?.row).includes('.') ? rowName(item?.row).split('.')[0] : rowName(item?.row)))
                .filter(parent => parent && parent.startsWith('bundle-')));
            asRows(side.subifs).forEach(subif => {
                const parent = subif?.parent || (rowName(subif).includes('.') ? rowName(subif).split('.')[0] : '');
                if (activeParents.has(parent) && rowInnerVlan(subif)) {
                    addResolved('sub', rowName(subif), {}, { parent, description: 'same bundle parent QinQ sub-interface' });
                }
            });

            // If correlation has no candidates yet, fall back only to explicit
            // link hints, not to every live row on the device.
            if (!rows.length) {
                return this._fallbackSelectableRows(link, result, suffix);
            }
            return rows;
        },

        _selectorRowsForSide(link, result, suffix) {
            return selectableRows({}, this._candidateScopedRows(link, result, suffix));
        },

        _findSelectable(link, result, suffix, kind, name) {
            return this._selectorRowsForSide(link, result, suffix)
                .find(item => item.kind === kind && item.row?.name === name) || null;
        },

        _autoSelectionForSide(link, result, suffix) {
            const correlated = selectedRowsForCorrelation(link, result)[suffix === 'B' ? 'B' : 'A'];
            const candidates = this._selectorRowsForSide(link, result, suffix);
            const sideKey = suffix === 'B' ? 'B' : 'A';
            const corr = activeCorrelation(link, result);
            const corrSub = corr[`sub${sideKey}`] || (String(corr[`logicalIf${sideKey}`] || '').includes('.') ? corr[`logicalIf${sideKey}`] : '');
            if (corrSub) {
                const inferredSub = this._findSelectable(link, result, suffix, 'sub', corrSub);
                if (inferredSub) return inferredSub;
            }
            const correlatedItems = [
                correlated.sub ? { kind: 'sub', row: correlated.sub } : null,
                correlated.bundle ? { kind: 'bundle', row: correlated.bundle } : null,
                correlated.physical ? { kind: 'physical', row: correlated.physical } : null,
            ].filter(Boolean);
            for (const item of correlatedItems) {
                const match = this._findSelectable(link, result, suffix, item.kind, item.row?.name);
                if (match) return match;
            }
            return candidates[0] || null;
        },

        _currentSelections(link, result) {
            link.linkDetails = link.linkDetails || {};
            const manual = link.linkDetails.liveSelectionManual || {};
            const corr = activeCorrelation(link, result);
            const autoCandidateKey = candidateKey(corr);
            const sameAutoCandidate = link.linkDetails.liveAutoCandidateKey === autoCandidateKey;
            const out = {};
            ['A', 'B'].forEach(suffix => {
                const saved = link.linkDetails[`liveSelected${suffix}`] || {};
                const savedName = saved.row?.name || saved.row?.interface || '';
                const savedMatch = this._findSelectable(link, result, suffix, saved.kind, savedName);
                const sideKey = suffix === 'B' ? 'B' : 'A';
                const corrSub = corr[`sub${sideKey}`] || (String(corr[`logicalIf${sideKey}`] || '').includes('.') ? corr[`logicalIf${sideKey}`] : '');
                const corrMatch = corrSub ? this._findSelectable(link, result, suffix, 'sub', corrSub) : null;
                if (manual[suffix] && !sameAutoCandidate && corrMatch && savedName !== corrSub) {
                    manual[suffix] = false;
                }
                if (manual[suffix]) {
                    out[suffix] = savedMatch || this._autoSelectionForSide(link, result, suffix);
                    if (!savedMatch) {
                        manual[suffix] = false;
                    }
                } else if (sameAutoCandidate && savedMatch) {
                    out[suffix] = savedMatch;
                } else {
                    out[suffix] = this._autoSelectionForSide(link, result, suffix) || savedMatch;
                }
                if (out[suffix] && !manual[suffix]) {
                    link.linkDetails[`liveSelected${suffix}`] = { kind: out[suffix].kind, row: out[suffix].row };
                }
            });
            link.linkDetails.liveAutoCandidateKey = autoCandidateKey;
            link.linkDetails.liveSelectionManual = manual;
            return out;
        },

        renderDynamicLinkTable(link, result) {
            const root = document.getElementById('lt-dynamic-link-table');
            if (!root) return;
            try {
                const safeResult = result || {};
                root.innerHTML = this.renderDynamicLinkTableHtml(link, safeResult);
                this.wireDynamicTable(root, link, safeResult);
            } catch (err) {
                console.error('[LinkTelemetry] dynamic table render failed:', err);
                root.innerHTML = `<div class="lt-live-error">Dynamic Link Table render failed: ${escapeHtml(err.message || err)}</div>`;
            }
        },

        renderDynamicLinkTableHtml(link, result) {
            result = result || {};
            const candidates = buildLogicalCandidates(result);
            const corr = activeCorrelation(link, result);
            const selections = this._currentSelections(link, result);
            const selected = {
                A: selectionToDynamicSide(selections.A),
                B: selectionToDynamicSide(selections.B)
            };
            const kind = dynamicKindForSelections(selections.A, selections.B);
            const selector = this._interfaceSelectorHtml(link, result, selections);
            const menu = candidates.length > 1
                ? `<div class="lt-candidate-menu">
                    <label>Detected link</label>
                    <select id="lt-live-candidate-select">${candidates.map((candidate, idx) => {
                        const selectedAttr = candidateKey(candidate) === candidateKey(corr) ? ' selected' : '';
                        return `<option value="${idx}"${selectedAttr}>${escapeHtml(candidateLabel(candidate))}</option>`;
                    }).join('')}</select>
                </div>`
                : '';
            const labelByKind = {
                physical: 'Physical Link',
                bundle: 'Bundle Link',
                'sub-bundle': 'Sub-bundle Link',
                'sub-interface': 'Sub-interface Link',
            };
            const rows = this._dynamicRowsForKind(kind, selected, corr, result, link);
            // #region agent log
            agentDebugLog('H6,H7,H8', 'Dynamic selector QinQ option state', {
                linkId: link?.id || '',
                scriptVersion: '20260504l-inner-selector',
                active: {
                    subA: corr.subA,
                    subB: corr.subB,
                    logicalIfA: corr.logicalIfA,
                    logicalIfB: corr.logicalIfB,
                },
                selected: {
                    A: { name: rowName(selections.A?.row), outer: rowOuterVlan(selections.A?.row), inner: rowInnerVlan(selections.A?.row) },
                    B: { name: rowName(selections.B?.row), outer: rowOuterVlan(selections.B?.row), inner: rowInnerVlan(selections.B?.row) },
                },
                compactMemberRows: true,
                options: {
                    A: this._selectorRowsForSide(link, result, 'A').map(item => ({ kind: item.kind, name: rowName(item.row), outer: rowOuterVlan(item.row), inner: rowInnerVlan(item.row) })).slice(0, 80),
                    B: this._selectorRowsForSide(link, result, 'B').map(item => ({ kind: item.kind, name: rowName(item.row), outer: rowOuterVlan(item.row), inner: rowInnerVlan(item.row) })).slice(0, 80),
                },
            });
            // #endregion
            // #region agent log
            const modalContent = document.querySelector('#link-details-modal .link-table-modal');
            agentDebugLog('H2,H3,H4', 'Dynamic Link Table render state', {
                linkId: link?.id || '',
                candidateCount: candidates.length,
                candidates: candidates.slice(0, 10).map(candidate => ({
                    kind: candidate.kind,
                    ifA: candidate.ifA,
                    ifB: candidate.ifB,
                    subA: candidate.subA,
                    subB: candidate.subB,
                    logicalIfA: candidate.logicalIfA,
                    logicalIfB: candidate.logicalIfB,
                    outerVlanA: candidate.outerVlanA,
                    innerVlanA: candidate.innerVlanA,
                    outerVlanB: candidate.outerVlanB,
                    innerVlanB: candidate.innerVlanB,
                    evidence: candidate.evidence,
                    score: candidate.score,
                    source: candidate.source,
                })),
                activeCorrelation: {
                    kind: corr.kind,
                    ifA: corr.ifA,
                    ifB: corr.ifB,
                    subA: corr.subA,
                    subB: corr.subB,
                    logicalIfA: corr.logicalIfA,
                    logicalIfB: corr.logicalIfB,
                    outerVlanA: corr.outerVlanA,
                    innerVlanA: corr.innerVlanA,
                    outerVlanB: corr.outerVlanB,
                    innerVlanB: corr.innerVlanB,
                    evidence: corr.evidence,
                    logicalReason: corr.logicalReason,
                },
                selectedRows: {
                    A: { kind: selections.A?.kind, name: rowName(selections.A?.row), parent: selections.A?.row?.parent, outer: rowOuterVlan(selections.A?.row), inner: rowInnerVlan(selections.A?.row) },
                    B: { kind: selections.B?.kind, name: rowName(selections.B?.row), parent: selections.B?.row?.parent, outer: rowOuterVlan(selections.B?.row), inner: rowInnerVlan(selections.B?.row) },
                },
                rowLabels: rows.map(row => ({ label: row.label, advanced: !!row.advanced, html: !!row.html })).slice(0, 40),
                modal: {
                    width: modalContent?.offsetWidth,
                    height: modalContent?.offsetHeight,
                    dataWidth: modalContent?.dataset?.width,
                    dataHeight: modalContent?.dataset?.height,
                }
            });
            // #endregion
            return `${selector}${menu}
                <div class="link-table-section-header lt-dynamic-header">
                    <span>${escapeHtml(labelByKind[kind] || 'Dynamic Link')}</span>
                    <button type="button" class="lt-refresh-button lt-refresh-button-inline" data-lt-dynamic-action="refresh">${refreshButton('Refresh devices')}</button>
                </div>
                ${rows.map(row => this._dynamicRow(row)).join('')}`;
        },

        _interfaceSelectorHtml(link, result, selections) {
            const manual = link?.linkDetails?.liveSelectionManual || {};
            const renderOptions = (selected, suffix) => {
                const rows = this._selectorRowsForSide(link, result, suffix);
                if (!rows.length) return '<option value="">No interfaces yet</option>';
                return rows.map(item => {
                const selectedAttr = item.key === selected?.key ? ' selected' : '';
                return `<option value="${escapeHtml(item.key)}"${selectedAttr}>${escapeHtml(item.label)}</option>`;
                }).join('');
            };
            const selectedDetail = (selected) => selected?.detail
                ? `<div class="lt-interface-selected-detail">${escapeHtml(selected.detail)}</div>`
                : '<div class="lt-interface-selected-detail">No live details yet</div>';
            return `<div class="lt-interface-selector">
                <div class="lt-interface-selector-title">
                    <span>Interface to Interface</span>
                    <small>auto-selected until you change a side</small>
                </div>
                <div class="lt-interface-selector-grid">
                    <label>
                        <span>Side A ${manual.A ? '<b>manual</b>' : '<b>auto</b>'}</span>
                        <select data-lt-interface-select="A">${renderOptions(selections.A, 'A')}</select>
                        ${selectedDetail(selections.A)}
                    </label>
                    <div class="lt-interface-link-arrow">to</div>
                    <label>
                        <span>Side B ${manual.B ? '<b>manual</b>' : '<b>auto</b>'}</span>
                        <select data-lt-interface-select="B">${renderOptions(selections.B, 'B')}</select>
                        ${selectedDetail(selections.B)}
                    </label>
                </div>
            </div>`;
        },

        _dynamicRowsForKind(kind, selected, corr = {}, result = {}, link = {}) {
            const sideA = result?.side_a || result?.sideA || {};
            const sideB = result?.side_b || result?.sideB || {};
            const a = selected.A;
            const b = selected.B;
            const mainA = a.sub || a.bundle || a.physical || {};
            const mainB = b.sub || b.bundle || b.physical || {};
            const parentBundle = (selectedSide, sideData, row) => {
                if (selectedSide?.bundle) return selectedSide.bundle;
                const name = rowName(row);
                const parent = row?.parent || (name.includes('.') ? name.split('.')[0] : '');
                return parent && parent.startsWith('bundle-') ? findRowByName(sideData.bundles, parent) : null;
            };
            const parentPhysical = (sideData, row, memberName = '') => {
                const name = memberName || rowName(row);
                return findRowByName(sideData.physical, name) || null;
            };
            const bundleA = parentBundle(a, sideA, mainA);
            const bundleB = parentBundle(b, sideB, mainB);
            const physicalA = parentPhysical(sideA, mainA, corr.memberA);
            const physicalB = parentPhysical(sideB, mainB, corr.memberB);
            const mtuFor = (row, suffix, bundle, physical) => {
                const idx = suffix === 'A' ? '1' : '2';
                return rowMtu(row)
                    || rowMtu(bundle)
                    || rowMtu(physical)
                    || link?.linkDetails?.[`mtu${suffix}`]
                    || link?.[`device${idx}Mtu`]
                    || '';
            };
            const vlanPart = (row, suffix, part) => {
                const idx = suffix === 'A' ? '1' : '2';
                if (part === 'outer') return rowOuterVlan(row) || link?.[`device${idx}OuterTag`] || '';
                if (part === 'inner') return rowInnerVlan(row) || link?.[`device${idx}InnerTag`] || '';
                return rowTpid(row) || link?.[`device${idx}VlanTpid`] || '';
            };
            const subifUnit = (row) => {
                const name = rowName(row);
                const match = name.match(/\.([^.]+)$/);
                return match ? match[1] : '';
            };
            const stateDetail = (row, suffix, bundle, physical) => [
                statusBadge(row.admin_state || corr[`state${suffix}`]?.admin, 'Admin'),
                statusBadge(row.oper_state || corr[`state${suffix}`]?.oper, 'Oper'),
                `MTU ${val(mtuFor(row, suffix, bundle, physical), 'not reported')}`
            ].filter(Boolean).join(' ');
            const qinqSiblingRows = (sideData, row) => {
                const name = rowName(row);
                const parent = row?.parent || (name.includes('.') ? name.split('.')[0] : '');
                const outer = rowOuterVlan(row);
                if (!parent || !outer) return [];
                return asRows(sideData?.subifs)
                    .filter(candidate => rowName(candidate) !== name
                        && (candidate.parent || '').trim() === parent
                        && rowOuterVlan(candidate) === outer
                        && rowInnerVlan(candidate))
                    .sort((left, right) => rowName(left).localeCompare(rowName(right)));
            };
            const qinqSummaryText = (matches) => {
                if (!matches.length) return 'none found for same parent + outer VLAN';
                const preview = matches.slice(0, 4).map(candidate => `${rowName(candidate)} inner ${rowInnerVlan(candidate)}`).join(', ');
                return matches.length > 4 ? `${preview}, +${matches.length - 4} more` : preview;
            };
            const lacpDetail = (bundle) => {
                const row = bundle || {};
                return [
                    val(row.lacp_mode || row.mode, 'mode not configured'),
                    `period ${val(row.lacp_period, 'default')}`,
                    `min ${val(row.min_links, 'default')}`,
                    row.lacp_system_id ? `system ${row.lacp_system_id}` : ''
                ].filter(Boolean).join(' / ');
            };
            const manipulationParts = (suffix) => {
                const row = suffix === 'A' ? mainA : mainB;
                const liveEgress = rowVlanManipulation(row);
                const idx = suffix === 'A' ? '1' : '2';
                const ingress = link?.[`device${idx}IngressAction`] || document.getElementById(`lt-ingress-${suffix.toLowerCase()}`)?.value || '';
                const egress = link?.[`device${idx}EgressAction`] || document.getElementById(`lt-egress-${suffix.toLowerCase()}`)?.value || '';
                return {
                    ingress: ingress || 'none configured',
                    egress: liveEgress ? `${liveEgress} (live config)` : (egress || 'none configured')
                };
            };
            const manipulationA = manipulationParts('A');
            const manipulationB = manipulationParts('B');
            const rows = [
                { label: 'Correlation status', a: val(corr.correlationStatus, 'unknown'), b: val(corr.logicalReason, corr.evidence || 'no evidence') },
                { label: 'Interface', a: mainA.name || a.ifName, b: mainB.name || b.ifName },
                { label: 'Parent / unit', a: [mainA.parent, subifUnit(mainA) ? `unit ${subifUnit(mainA)}` : ''].filter(Boolean).join(' / ') || 'not applicable', b: [mainB.parent, subifUnit(mainB) ? `unit ${subifUnit(mainB)}` : ''].filter(Boolean).join(' / ') || 'not applicable' },
                { label: 'State / MTU', a: stateDetail(mainA, 'A', bundleA, physicalA), b: stateDetail(mainB, 'B', bundleB, physicalB) },
                { label: 'Outer VLAN', a: val(vlanPart(mainA, 'A', 'outer'), 'untagged/not found'), b: val(vlanPart(mainB, 'B', 'outer'), 'untagged/not found') },
                { label: 'Inner VLAN', a: val(vlanPart(mainA, 'A', 'inner'), 'none'), b: val(vlanPart(mainB, 'B', 'inner'), 'none') },
                { label: 'TPID', a: val(vlanPart(mainA, 'A', 'tpid'), 'default'), b: val(vlanPart(mainB, 'B', 'tpid'), 'default') },
                { label: 'Related QinQ', a: qinqSummaryText(qinqSiblingRows(sideA, mainA)), b: qinqSummaryText(qinqSiblingRows(sideB, mainB)) },
                { label: 'Ingress manipulation', a: manipulationA.ingress, b: manipulationB.ingress },
                { label: 'Egress manipulation', a: manipulationA.egress, b: manipulationB.egress },
                { label: 'Service attachment', a: attachmentDetail(mainA), b: attachmentDetail(mainB) },
            ];
            if (kind === 'bundle' || kind === 'sub-bundle') {
                rows.push({ label: 'LACP', a: lacpDetail(bundleA), b: lacpDetail(bundleB) });
            }
            if (kind === 'sub-interface' || kind === 'sub-bundle') {
                rows.push(
                    { label: 'IP address', a: val(mainA.ip, 'not configured'), b: val(mainB.ip, 'not configured') },
                    { label: 'Bridge domain', a: val(mainA.bridge_domain, 'none'), b: val(mainB.bridge_domain, 'none') }
                );
            } else {
                rows.push(
                    { label: 'Speed', a: val(rowSpeed(mainA), 'not reported'), b: val(rowSpeed(mainB), 'not reported') },
                    { label: 'Transceiver', a: val(mainA.transceiver, 'not reported'), b: val(mainB.transceiver, 'not reported') },
                    { label: 'FEC', a: val(mainA.fec, 'not reported'), b: val(mainB.fec, 'not reported') },
                    { label: 'LLDP peer', a: val(mainA.lldp_neighbor_interface || mainA.lldp_neighbor, 'no LLDP peer'), b: val(mainB.lldp_neighbor_interface || mainB.lldp_neighbor, 'no LLDP peer') }
                );
            }
            rows.push({ label: 'Protocols', a: protocolDetailsHtml(mainA), b: protocolDetailsHtml(mainB), html: true });
            rows.push(
                { label: 'Errors', a: val(mainA.errors, 'none reported'), b: val(mainB.errors, 'none reported') },
                { label: 'Evidence source', a: val(a.ifName || mainA.name, 'not found'), b: val(b.ifName || mainB.name, 'not found') }
            );
            // #region agent log
            agentDebugLog('H9,H10,H11', 'Dynamic compact rows and VLAN interpretation', {
                linkId: link?.id || '',
                selected: {
                    A: { name: rowName(mainA), unit: subifUnit(mainA), parent: mainA.parent || '', outer: vlanPart(mainA, 'A', 'outer'), inner: vlanPart(mainA, 'A', 'inner'), relatedQinq: qinqSummaryText(qinqSiblingRows(sideA, mainA)) },
                    B: { name: rowName(mainB), unit: subifUnit(mainB), parent: mainB.parent || '', outer: vlanPart(mainB, 'B', 'outer'), inner: vlanPart(mainB, 'B', 'inner'), relatedQinq: qinqSummaryText(qinqSiblingRows(sideB, mainB)) }
                },
                rowLabels: rows.map(row => row.label)
            });
            // #endregion
            // #region agent log
            agentDebugLog('H12,H13,H14,H15', 'Structured VLAN rows prepared', {
                linkId: link?.id || '',
                selected: {
                    A: { name: rowName(mainA), outer: vlanPart(mainA, 'A', 'outer'), inner: vlanPart(mainA, 'A', 'inner'), qinqRelatedCount: qinqSiblingRows(sideA, mainA).length },
                    B: { name: rowName(mainB), outer: vlanPart(mainB, 'B', 'outer'), inner: vlanPart(mainB, 'B', 'inner'), qinqRelatedCount: qinqSiblingRows(sideB, mainB).length }
                },
                rowBasedVlan: true
            });
            // #endregion
            return rows;
        },

        _memberList(members) {
            if (!Array.isArray(members) || !members.length) return '';
            return members.map(m => [m.interface, m.port_state || m.protocol_state].filter(Boolean).join(' ')).join(', ');
        },

        _dynamicRow(rowOrLabel, a, b, advanced = false) {
            const row = typeof rowOrLabel === 'object'
                ? rowOrLabel
                : { label: rowOrLabel, a, b, advanced };
            return `<div class="link-table-row lt-dynamic-row${row.advanced ? ' lt-wide-only' : ''}${row.html ? ' lt-dynamic-html-row' : ''}">
                <div class="link-table-label">${escapeHtml(row.label)}</div>
                <div class="link-table-field">${this._editableCell(row.label, 'A', row.a, { html: row.html })}</div>
                <div class="link-table-field">${this._editableCell(row.label, 'B', row.b, { html: row.html })}</div>
            </div>`;
        },

        _editableCell(label, side, value, options = {}) {
            if (options.html) {
                return `<div class="lt-dynamic-html-cell" data-label="${escapeHtml(label)}" data-side="${side}">${value || '--'}</div>`;
            }
            const raw = String(value === undefined || value === null ? '' : value);
            if (raw.includes('<span class="lt-state')) {
                return `<div class="lt-dynamic-readonly-cell" data-label="${escapeHtml(label)}" data-side="${side}">${raw}</div>`;
            }
            return `<div class="lt-dynamic-readonly-cell" data-live-value="${escapeHtml(raw)}" data-label="${escapeHtml(label)}" data-side="${side}" title="${escapeHtml(raw)}">${escapeHtml(raw || '--')}</div>`;
        },

        wireDynamicTable(root, link, result) {
            root.querySelectorAll('[data-lt-interface-select]').forEach(select => {
                select.addEventListener('change', () => {
                    const suffix = select.dataset.ltInterfaceSelect === 'B' ? 'B' : 'A';
                    const [kind, ...nameParts] = String(select.value || '').split(':');
                    const name = nameParts.join(':');
                    if (!kind || !name) return;
                    const match = this._findSelectable(link, result, suffix, kind, name);
                    if (!match) return;
                    this.applyRowSelection(window.topologyEditor || null, link, suffix, match.kind, match.row, {
                        overwriteExisting: true,
                        forceUserSelection: true,
                        manual: true
                    });
                    this.applyAutoFill(window.topologyEditor || null, link, result, {
                        overwriteExisting: true,
                        forceUserSelection: true
                    });
                    this.renderDynamicLinkTable(link, result);
                });
            });
            const candidateSelect = root.querySelector('#lt-live-candidate-select');
            if (candidateSelect) {
                candidateSelect.addEventListener('change', () => {
                    link.linkDetails = link.linkDetails || {};
                    const candidates = buildLogicalCandidates(result);
                    const idx = Number(candidateSelect.value || 0);
                    const candidate = candidates[idx] || candidates[0] || {};
                    link.linkDetails.liveCandidateIndex = idx;
                    link.linkDetails.liveCandidateKey = candidateKey(candidate);
                    link.linkDetails.liveAutoCandidateKey = '';
                    link.linkDetails.liveSelectionManual = {};
                    this.renderDynamicLinkTable(link, result);
                    this.applyAutoFill(window.topologyEditor || null, link, {
                        ...result,
                        correlation: activeCorrelation(link, result),
                    }, { overwriteExisting: true });
                });
            }
            root.querySelectorAll('[data-lt-dynamic-action="refresh"]').forEach(btn => {
                btn.addEventListener('click', event => {
                    event.preventDefault();
                    setRefreshBusy(btn, true, 'Refresh devices');
                    this.refreshLink(window.topologyEditor || null, link, { force: true })
                        .catch(err => {
                            console.warn('[LinkTelemetry] dynamic refresh failed:', err);
                            root.insertAdjacentHTML('afterbegin', `<div class="lt-live-error">Refresh failed: ${escapeHtml(err.message || err)}</div>`);
                        })
                        .finally(() => {
                            setRefreshBusy(btn, false, 'Refresh devices');
                        });
                });
            });
            root.querySelectorAll('[data-lt-dynamic-action="use-hints"]').forEach(btn => {
                btn.addEventListener('click', event => {
                    event.preventDefault();
                    this.applyAutoFill(window.topologyEditor || null, link, result, { overwriteExisting: true });
                });
            });
            root.querySelectorAll('.lt-dynamic-input').forEach(input => {
                input.addEventListener('change', () => {
                    const liveValue = input.dataset.liveValue || '';
                    if (input.value !== liveValue && !window.confirm("Your edit doesn't match the device. Save anyway?")) {
                        input.value = liveValue;
                        return;
                    }
                    input.classList.toggle('lt-live-differs', input.value !== liveValue);
                    link.linkDetails = link.linkDetails || {};
                    link.linkDetails.dynamicOverrides = link.linkDetails.dynamicOverrides || {};
                    link.linkDetails.dynamicOverrides[`${input.dataset.side}:${input.dataset.label}`] = input.value;
                });
            });
        },

        renderTelemetry(link, result) {
            const root = document.getElementById('lt-live-telemetry-panel');
            if (!root) return;
            try {
                const safeResult = result || {};
                root.innerHTML = this.renderTelemetryHtml(link, safeResult);
                this.wireTelemetryActions(root, link, safeResult);
                this.renderDynamicLinkTable(link, safeResult);
            } catch (err) {
                console.error('[LinkTelemetry] render failed:', err);
                root.innerHTML = `<div class="lt-live-error">Live telemetry render failed: ${escapeHtml(err.message || err)}</div>`;
                this.renderDynamicLinkTable(link, result || {});
            }
        },

        renderTelemetryHtml(link, result) {
            result = result || {};
            const sideA = result.side_a || result.sideA || {};
            const sideB = result.side_b || result.sideB || {};
            const stamp = new Date().toLocaleTimeString();
            const selectedA = link?.linkDetails?.liveSelectedA || {};
            const selectedB = link?.linkDetails?.liveSelectedB || {};
            const rankRow = (row, kind) => {
                if (!row) return 9;
                const oper = String(row.oper_state || '').toLowerCase();
                const admin = String(row.admin_state || '').toLowerCase();
                const hasAttachment = row.attachment && row.attachment.kind && row.attachment.kind !== 'none';
                const hasService = !!(hasAttachment || row.bridge_domain || row.ip || row.outer_vlan || row.inner_vlan);
                if (kind === 'sub' || hasService) return oper === 'up' ? 0 : 1;
                if (kind === 'bundle') return oper === 'up' ? 2 : 3;
                if (row.lldp_neighbor || (oper === 'up' && admin !== 'disabled')) return 4;
                return 7;
            };
            const sortRows = (rows, kind) => (Array.isArray(rows) ? [...rows] : []).sort((a, b) => {
                const rank = rankRow(a, kind) - rankRow(b, kind);
                if (rank !== 0) return rank;
                return rowName(a).localeCompare(rowName(b));
            });
            const renderRows = (rows, side, kind, sideData) => sortRows(rows, kind).map(row => {
                const src = rowForCapture(link, side, kind, row);
                const name = rowName(row);
                const selected = side === 'A'
                    ? selectedA.kind === kind && rowName(selectedA.row) === name
                    : selectedB.kind === kind && rowName(selectedB.row) === name;
                const attachment = attachmentSummary(row, kind);
                const parent = row?.parent && row.parent !== name ? `parent ${row.parent}` : '';
                const detail = telemetryDetail(row, kind, sideData);
                const title = `Click to select ${name || kind} for Side ${side}. PCAP opens XRAY using this exact row.`;
                return `<tr class="lt-live-row${selected ? ' selected' : ''}" data-side="${side}" data-kind="${kind}" data-row="${encodeRowAttr(row)}" data-src-row="${encodeRowAttr(src)}" title="${escapeHtml(title)}">
                    <td class="lt-live-interface-cell">
                        <strong>${escapeHtml(name || '--')}</strong>
                        <small>${escapeHtml([kind, parent].filter(Boolean).join(' / '))}</small>
                        <button class="lt-live-capture-btn" type="button" aria-label="Packet capture ${escapeHtml(name || kind)}">PCAP</button>
                    </td>
                    <td class="lt-live-state-cell">${statusBadge(row.admin_state, 'Admin')}${statusBadge(row.oper_state, 'Oper')}</td>
                    <td class="lt-live-vlan-cell">${vlanChipsHtml(row, { compact: true }) || '--'}</td>
                    <td>${escapeHtml(attachment || '--')}</td>
                    <td>${escapeHtml(detail || '--')}</td>
                </tr>`;
            }).join('');
            // #region agent log
            agentDebugLog('H11', 'Live telemetry compact table shape', {
                linkId: link?.id || '',
                columns: ['Interface', 'State', 'VLAN', 'Service / Attachment', 'Details'],
                sideA: { subifs: asRows(sideA.subifs).length, bundles: asRows(sideA.bundles).length, physical: asRows(sideA.physical).length },
                sideB: { subifs: asRows(sideB.subifs).length, bundles: asRows(sideB.bundles).length, physical: asRows(sideB.physical).length }
            });
            // #endregion
            return `
                <div class="lt-live-header">
                    <span>Live Telemetry <small>click a row to fill the Dynamic Link Table side</small></span>
                    <span class="lt-live-stamp">updated ${stamp}</span>
                    <button id="lt-live-refresh-current" class="lt-refresh-button" type="button">${refreshButton('Refresh live')}</button>
                </div>
                <div class="lt-live-pov-grid">
                    <div class="lt-live-pov">
                        <h3>Side A POV</h3>
                        ${this._povControls('A', sideA)}
                        ${this._table('A Sub-interfaces', renderRows(sideA.subifs, 'A', 'sub', sideA), 'sub')}
                        ${this._table('A Bundle Interfaces', renderRows(sideA.bundles, 'A', 'bundle', sideA), 'bundle')}
                        ${this._table('A Physical Interfaces', renderRows(sideA.physical, 'A', 'physical', sideA), 'physical')}
                    </div>
                    <div class="lt-live-pov">
                        <h3>Side B POV</h3>
                        ${this._povControls('B', sideB)}
                        ${this._table('B Sub-interfaces', renderRows(sideB.subifs, 'B', 'sub', sideB), 'sub')}
                        ${this._table('B Bundle Interfaces', renderRows(sideB.bundles, 'B', 'bundle', sideB), 'bundle')}
                        ${this._table('B Physical Interfaces', renderRows(sideB.physical, 'B', 'physical', sideB), 'physical')}
                    </div>
                </div>
            `;
        },

        _povControls(side, sideData) {
            const counts = {
                all: asRows(sideData?.subifs).length + asRows(sideData?.bundles).length + asRows(sideData?.physical).length,
                sub: asRows(sideData?.subifs).length,
                bundle: asRows(sideData?.bundles).length,
                physical: asRows(sideData?.physical).length
            };
            const labels = [
                ['all', 'All'],
                ['sub', 'Sub-ifs'],
                ['bundle', 'Bundles'],
                ['physical', 'Physical']
            ];
            return `<div class="lt-pov-suboptions" data-lt-pov-controls="${escapeHtml(side)}">
                ${labels.map(([key, label], idx) => `<button type="button" class="${idx === 0 ? 'active' : ''}" data-lt-pov-filter="${key}">${escapeHtml(label)} <b>${counts[key]}</b></button>`).join('')}
            </div>`;
        },

        wireTelemetryActions(root, link, result) {
            if (!root) return;
            root.dataset.linkId = link?.id || '';
            root.querySelectorAll('.lt-live-capture-btn').forEach(btn => {
                btn.addEventListener('click', event => {
                    event.preventDefault();
                    event.stopPropagation();
                    const tr = btn.closest('tr');
                    const row = parseRowAttr(tr?.dataset?.row);
                    const srcRow = parseRowAttr(tr?.dataset?.srcRow);
                    const side = tr?.dataset?.side || srcRow.side || 'A';
                    const kind = tr?.dataset?.kind || srcRow.kind || 'physical';
                    if (rowName(row)) {
                        this.applyRowSelection(window.topologyEditor || null, link, side, kind, row, {
                            overwriteExisting: true,
                            forceUserSelection: true,
                            manual: true
                        });
                        this.renderDynamicLinkTable(link, this._lastByLink.get(link.id) || result);
                    }
                    const rect = btn.getBoundingClientRect();
                    window.XrayPopup?.show(window.topologyEditor || null, link, { x: rect.left, y: rect.bottom, anchor: 'center' }, { srcRow });
                });
            });
            root.querySelectorAll('.lt-live-row').forEach(rowEl => {
                rowEl.addEventListener('click', event => {
                    if (event.target.closest('.lt-live-capture-btn')) return;
                    const row = parseRowAttr(rowEl.dataset.row);
                    const side = rowEl.dataset.side || 'A';
                    const kind = rowEl.dataset.kind || 'physical';
                    this.applyRowSelection(window.topologyEditor || null, link, side, kind, row);
                    this.renderTelemetry(link, this._lastByLink.get(link.id) || result);
                });
            });
            const refreshBtn = root.querySelector('#lt-live-refresh-current');
            if (refreshBtn) {
                refreshBtn.onclick = () => {
                    setRefreshBusy(refreshBtn, true, 'Refresh live');
                    this.refreshLink(window.topologyEditor || null, link, { force: true })
                        .catch(err => {
                            console.warn('[LinkTelemetry] manual refresh failed:', err);
                            root.insertAdjacentHTML('afterbegin', `<div class="lt-live-error">Refresh failed: ${escapeHtml(err.message || err)}</div>`);
                        })
                        .finally(() => {
                            setRefreshBusy(refreshBtn, false, 'Refresh live');
                        });
                };
            }
            root.querySelectorAll('[data-lt-pov-filter]').forEach(btn => {
                btn.addEventListener('click', event => {
                    event.preventDefault();
                    const filter = btn.dataset.ltPovFilter || 'all';
                    const pov = btn.closest('.lt-live-pov');
                    if (!pov) return;
                    pov.querySelectorAll('[data-lt-pov-filter]').forEach(other => other.classList.toggle('active', other === btn));
                    pov.querySelectorAll('.lt-live-section[data-lt-section-kind]').forEach(section => {
                        section.hidden = filter !== 'all' && section.dataset.ltSectionKind !== filter;
                    });
                });
            });
        },

        _table(title, body, kind = '') {
            return `<section class="lt-live-section" data-lt-section-kind="${escapeHtml(kind)}">
                <h4>${title}</h4>
                <table class="lt-live-table">
                    <thead><tr><th>Interface</th><th>State</th><th>VLAN</th><th>Service / Attachment</th><th>Details</th></tr></thead>
                    <tbody>${body || '<tr><td colspan="5" class="lt-live-empty">No live rows yet</td></tr>'}</tbody>
                </table>
            </section>`;
        }
    };
})();
