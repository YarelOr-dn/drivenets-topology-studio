/**
 * topology-link-autofill.js - Automatic Link Table enrichment.
 *
 * Applies discovery/monitor-generated link-table patches safely:
 * empty or auto-owned fields are filled, user-entered fields are preserved
 * and conflicting discovered values are stored as suggestions.
 */
'use strict';

(function () {
    const AUTO_OWNERS = new Set(['monitor', 'generated', 'autofill', 'lldp-monitor', 'existing-link']);
    const FIELD_ALIASES = {
        device1Interface: ['device1Interface', 'interface1'],
        device2Interface: ['device2Interface', 'interface2'],
        interface1: ['interface1', 'device1Interface'],
        interface2: ['interface2', 'device2Interface'],
        device1IpAddress: ['device1IpAddress'],
        device2IpAddress: ['device2IpAddress'],
        device1VlanId: ['device1VlanId'],
        device2VlanId: ['device2VlanId'],
        device1OuterTag: ['device1OuterTag'],
        device2OuterTag: ['device2OuterTag'],
        device1InnerTag: ['device1InnerTag'],
        device2InnerTag: ['device2InnerTag']
    };

    function authFetch(url, opts) {
        const auth = window.TopologyAuth;
        if (auth && typeof auth.authFetch === 'function') return auth.authFetch(url, opts);
        return fetch(url, opts);
    }

    function activeScope() {
        try {
            if (window.TopologySync && typeof window.TopologySync.getActive === 'function') {
                const a = window.TopologySync.getActive() || {};
                return { domain_id: a.domain_id || '', topology_id: a.topology_id || '' };
            }
        } catch (_) {}
        return { domain_id: '', topology_id: '' };
    }

    function devicePayload(device) {
        return {
            id: device.id || '',
            label: device.label || device.name || '',
            hostname: device.label || device.hostname || device.name || '',
            name: device.name || device.label || '',
            serial: device.deviceSerial || device.serial || '',
            ssh: device.sshConfig ? {
                host: device.sshConfig.host || '',
                hostBackup: device.sshConfig.hostBackup || ''
            } : null,
            _lldpData: device._lldpData || null,
            _monitorContext: device._monitorContext || null,
            context: device._monitorContext || null,
            config: device._monitorConfigFacts || null
        };
    }

    function linkPayload(link) {
        return {
            id: link.id || '',
            type: link.type || '',
            device1: link.device1 || '',
            device2: link.device2 || '',
            interface1: link.interface1 || link.device1Interface || '',
            interface2: link.interface2 || link.device2Interface || '',
            device1Interface: link.device1Interface || link.interface1 || '',
            device2Interface: link.device2Interface || link.interface2 || '',
            device1IpAddress: link.device1IpAddress || '',
            device2IpAddress: link.device2IpAddress || '',
            linkType: link.linkType || '',
            layer: link.layer || link._generatedLayer || '',
            protocol: (link.linkDetails && link.linkDetails.protocol) || link.protocol || link.linkType || '',
            peerIp: (link.linkDetails && link.linkDetails.peerIp) || link.peerIp || '',
            linkDetails: link.linkDetails || {}
        };
    }

    function collect(editor) {
        const objects = Array.isArray(editor && editor.objects) ? editor.objects : [];
        const devices = objects.filter(o => o && o.type === 'device').map(devicePayload);
        const links = objects
            .filter(o => o && (o.type === 'link' || o.type === 'unbound') && (o.device1 || o.device2))
            .map(linkPayload);
        const scope = activeScope();
        return { devices, links, domain_id: scope.domain_id, topology_id: scope.topology_id };
    }

    function ownerFor(link, field) {
        const src = link._linkTableSource || {};
        const entry = src[field] || {};
        return entry.owner || entry.source || '';
    }

    function setOwner(link, field, source, evidence) {
        link._linkTableSource = link._linkTableSource || {};
        link._linkTableSource[field] = {
            owner: source || 'autofill',
            updatedAt: new Date().toISOString(),
            evidence: evidence || null
        };
    }

    function shouldApply(link, field, nextValue) {
        if (nextValue == null || nextValue === '') return false;
        const aliases = FIELD_ALIASES[field] || [field];
        const existing = aliases.map(k => link[k]).find(v => v != null && String(v).trim() !== '');
        if (!existing) return true;
        const owner = ownerFor(link, field);
        return AUTO_OWNERS.has(owner);
    }

    function addSuggestion(link, field, value, source, evidence) {
        link.linkDetails = link.linkDetails || {};
        const suggestions = link.linkDetails.discoverySuggestions || {};
        suggestions[field] = {
            value,
            source: source || 'autofill',
            evidence: evidence || null,
            seenAt: new Date().toISOString()
        };
        link.linkDetails.discoverySuggestions = suggestions;
    }

    function setAliases(link, field, value) {
        const aliases = FIELD_ALIASES[field] || [field];
        aliases.forEach(k => { link[k] = value; });
    }

    function applyPatches(editor, patches) {
        if (!editor || !Array.isArray(editor.objects) || !Array.isArray(patches)) return 0;
        let changed = 0;
        for (const patch of patches) {
            const link = editor.objects.find(o => o && o.id === patch.linkId);
            if (!link) continue;
            const fields = patch.fields || {};
            const evidence = (patch.linkDetails && patch.linkDetails.discoveryEvidence) || [];
            for (const [field, value] of Object.entries(fields)) {
                if (shouldApply(link, field, value)) {
                    setAliases(link, field, value);
                    setOwner(link, field, patch.source || 'autofill', evidence);
                    changed++;
                } else if (String(link[field] || '') !== String(value || '')) {
                    addSuggestion(link, field, value, patch.source, evidence);
                }
            }
            link.linkDetails = Object.assign({}, link.linkDetails || {}, patch.linkDetails || {});
            link.linkDetails.discoveryEvidence = (link.linkDetails.discoveryEvidence || [])
                .concat((patch.linkDetails && patch.linkDetails.discoveryEvidence) || []);
            if (fields.device1Interface && typeof editor.createOrUpdateInterfaceTextBox === 'function') {
                editor.createOrUpdateInterfaceTextBox(link, 'device1', link.device1Interface || fields.device1Interface);
            }
            if (fields.device2Interface && typeof editor.createOrUpdateInterfaceTextBox === 'function') {
                editor.createOrUpdateInterfaceTextBox(link, 'device2', link.device2Interface || fields.device2Interface);
            }
        }
        if (changed) {
            if (typeof editor.requestDraw === 'function') editor.requestDraw();
            else if (typeof editor.draw === 'function') editor.draw();
            if (typeof editor.autoSave === 'function') editor.autoSave();
        }
        return changed;
    }

    const api = {
        _timer: null,
        _running: false,
        collect,
        applyPatches,
        schedule(editor, reason) {
            if (!editor || !Array.isArray(editor.objects)) return;
            clearTimeout(this._timer);
            this._timer = setTimeout(() => this.run(editor, reason || 'scheduled'), 900);
        },
        async run(editor, reason) {
            if (this._running || !editor || !Array.isArray(editor.objects)) return { ok: false, skipped: true };
            const payload = collect(editor);
            if (!payload.links.length || !payload.devices.length) return { ok: true, patches: [] };
            this._running = true;
            try {
                const resp = await authFetch('/api/topology-generator/enrich-link-tables', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-Best-Effort': 'link-table-autofill' },
                    body: JSON.stringify(Object.assign({ reason }, payload))
                });
                const data = await resp.json().catch(() => ({}));
                if (!resp.ok || data.error) throw new Error(data.error || data.detail || `HTTP ${resp.status}`);
                const changed = applyPatches(editor, data.patches || []);
                if (changed && editor.debugger) {
                    editor.debugger.logInfo(`Link-table autofill updated ${changed} field(s)`);
                }
                return data;
            } catch (e) {
                if (editor.debugger) editor.debugger.logInfo(`Link-table autofill skipped: ${e.message || e}`);
                return { ok: false, error: String(e.message || e) };
            } finally {
                this._running = false;
            }
        }
    };

    window.TopologyLinkAutofill = api;
})();

console.log('[topology-link-autofill.js] TopologyLinkAutofill loaded');
