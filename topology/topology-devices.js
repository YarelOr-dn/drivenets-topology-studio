// ============================================================================
// TOPOLOGY DEVICE MANAGER MODULE
// ============================================================================
// Handles device creation, selection, styling, collision detection, and properties.
// This is a wrapper module that delegates to editor methods.
//
// Usage:
//   const deviceMgr = new DeviceManager(editor);
//   deviceMgr.add('SA-40C');
//   deviceMgr.addAtPosition('SA-40C', 100, 200);
// ============================================================================

(function (global) {
    'use strict';

    if (global.TopologyDeviceDefaults) return;

    global.TopologyDeviceDefaults = {
        createCanvasSshConfig() {
            return {
                user: 'dnroot',
                password: 'dnroot'
            };
        },

        createEmptyLldpData() {
            return {
                neighbors: [],
                lldp_neighbors: [],
                source: 'canvas-placeholder',
                placeholder: true,
                message: 'No LLDP neighbors discovered or configured yet.'
            };
        },

        createCanvasLldpFields() {
            return {
                _lldpData: this.createEmptyLldpData(),
                lldpDiscoveryComplete: false,
                lldpEnabled: false
            };
        },

        createCanvasMetadataFields() {
            return {
                _metadataDiscovered: false,
                _metadataReadiness: {},
                _stackData: null,
                _gitCommit: null,
                _gitCommitFetchedAt: null,
                _deviceMode: '',
                _modeRawState: ''
            };
        }
    };
})(window);

(function (global) {
    'use strict';

    if (global.TopologyDeviceIdentity) return;

    const GENERATED_CANVAS_LABEL_RE = /^(NCP|NCP-\d+|S|S\d+)$/i;
    const IPV4_RE = /^(?:\d{1,3}\.){3}\d{1,3}$/;
    const SERIAL_LIKE_RE = /^[A-Z0-9]{8,}$/i;

    const clean = value => String(value || '').trim();
    const key = value => clean(value).toLowerCase();

    function isGeneratedCanvasLabel(value) {
        return GENERATED_CANVAS_LABEL_RE.test(clean(value));
    }

    function isIp(value) {
        return IPV4_RE.test(clean(value));
    }

    function isSerialLike(value) {
        const v = clean(value);
        return !!v && !isIp(v) && SERIAL_LIKE_RE.test(v);
    }

    function isGiMode(device, opts = {}) {
        const values = [
            opts.deviceState,
            opts.mode,
            device?._deviceMode,
            device?._modeRawState,
            device?._monitorContext?.device_state,
            device?._identity?.device_state,
            device?.sshConfig?._deviceState,
        ].map(v => clean(v).toUpperCase()).filter(Boolean);
        return values.some(v => v === 'GI' || v === 'BASEOS_SHELL' || v.includes('GI_MODE'));
    }

    function createUnknownLldpData(message = 'Device identity changed. Run probe/discover to refresh LLDP for the current SN.') {
        if (global.TopologyDeviceDefaults?.createEmptyLldpData) {
            return {
                ...global.TopologyDeviceDefaults.createEmptyLldpData(),
                message
            };
        }
        return {
            neighbors: [],
            lldp_neighbors: [],
            source: 'canvas-placeholder',
            placeholder: true,
            message
        };
    }

    function currentHost(device, overrideHost = '') {
        const cfg = device?.sshConfig || {};
        return clean(
            overrideHost
            || device?._registeredMgmtIp
            || device?._monitorContext?.management_ip
            || device?._monitorContext?.resolved_ip
            || device?._monitorContext?.mgmt_ip
            || cfg._registeredMgmtIp
            || cfg._enrichedMgmtIp
            || cfg._mgmtIp
            || cfg._activeNccIp
            || cfg._nccMgmtIp
            || cfg._userSavedHost
            || cfg.host
            || cfg.hostBackup
            || device?.deviceAddress
            || device?.deviceSerial
            || device?.serial
            || cfg._snVerifiedHost
            || ''
        );
    }

    function normalizeDeviceName(value) {
        return key(value).replace(/[^a-z0-9]/g, '');
    }

    function namesLookRelated(a, b) {
        const aa = normalizeDeviceName(a);
        const bb = normalizeDeviceName(b);
        if (!aa || !bb) return false;
        return aa === bb || aa.endsWith(bb) || bb.endsWith(aa);
    }

    function isDeviceLikeName(value) {
        const v = clean(value);
        return !!v && !isIp(v) && !isSerialLike(v) && /\b(PE|RR|SA|CL|NCC|NCP|NCM|NCF|LEAF|SPINE|DUT|YOR|BGW)\b/i.test(v);
    }

    function resolveIdentity(device, opts = {}) {
        const cfg = device?.sshConfig || {};
        const add = (bucket, value) => {
            const v = clean(value);
            if (v) bucket.push(v);
        };
        const label = clean(opts.label || device?.label || device?.name || '');
        const selectedLooksReal = label && !isGeneratedCanvasLabel(label);
        const identity = device?._identity || {};
        const scalerIds = Array.isArray(identity.scaler_ids) ? identity.scaler_ids : [];
        const inventoryKeys = Array.isArray(identity.inventory_keys) ? identity.inventory_keys : [];
        const rawIds = [];

        [
            device?._registeredDeviceId,
            device?._registeredHostname,
            device?._monitorContext?.device_id,
            device?._monitorContext?.hostname,
            device?._monitorContext?.resolved_device_id,
            identity.device_id,
            identity.hostname,
            ...scalerIds,
            ...inventoryKeys,
            device?.device_id,
            device?.hostname,
            device?._registeredMgmtIp,
            device?._monitorContext?.management_ip,
            device?._monitorContext?.resolved_ip,
            cfg._registeredMgmtIp,
            device?._registeredSerialNumber,
            device?.deviceSerial,
            device?.serial,
            opts.deviceId,
            selectedLooksReal ? label : ''
        ].forEach(v => add(rawIds, v));

        const ids = [];
        const seenIds = new Set();
        rawIds.forEach((candidate) => {
            const v = clean(candidate);
            if (!v || isGeneratedCanvasLabel(v)) return;
            if (
                selectedLooksReal
                && isDeviceLikeName(v)
                && isDeviceLikeName(label)
                && !namesLookRelated(v, label)
                && !opts.allowConflictingRegistered
            ) {
                return;
            }
            const k = key(v);
            if (!seenIds.has(k)) {
                seenIds.add(k);
                ids.push(v);
            }
        });

        const rawHosts = [];
        [
            device?._registeredMgmtIp,
            device?._monitorContext?.management_ip,
            device?._monitorContext?.resolved_ip,
            device?._monitorContext?.mgmt_ip,
            identity.mgmt_ip,
            cfg._registeredMgmtIp,
            cfg._enrichedMgmtIp,
            cfg._mgmtIp,
            opts.host,
            cfg._activeNccIp,
            cfg._nccMgmtIp,
            cfg.hostBackup,
            cfg.host,
            cfg._snVerifiedHost
        ].forEach(v => add(rawHosts, v));
        const hosts = [];
        const seenHosts = new Set();
        rawHosts.forEach((candidate) => {
            const v = clean(candidate);
            if (!v || isGeneratedCanvasLabel(v)) return;
            const k = key(v);
            if (!seenHosts.has(k)) {
                seenHosts.add(k);
                hosts.push(v);
            }
        });

        return {
            deviceId: ids[0] || '',
            host: hosts[0] || currentHost(device, opts.host || ''),
            candidates: ids,
            hosts,
            selectedLabel: label,
            signature: signature(device, hosts[0] || opts.host || '')
        };
    }

    function signature(device, overrideHost = '') {
        const cfg = device?.sshConfig || {};
        return [
            device?.id,
            device?.label,
            currentHost(device, overrideHost),
            cfg._userSavedHost,
            cfg.host,
            device?.deviceSerial,
            device?.serial,
            device?._registeredSerialNumber,
            device?._registeredDeviceId,
            device?._registeredHostname,
            device?._registeredMgmtIp,
            device?._monitoredKey
        ].map(key).join('|');
    }

    function makeRequestToken(device, opts = {}) {
        const host = clean(opts.host);
        const deviceId = clean(opts.deviceId);
        return {
            id: `${Date.now()}:${Math.random().toString(36).slice(2)}`,
            host,
            hostKey: key(host),
            deviceId,
            deviceIdKey: key(deviceId),
            signature: signature(device, host),
        };
    }

    function isRequestCurrent(device, token, opts = {}) {
        if (!device || !token) return false;
        const currentInputHost = clean(opts.currentHost);
        if (currentInputHost && key(currentInputHost) !== token.hostKey) return false;
        if (device._identityRequestToken && device._identityRequestToken !== token.id) return false;
        return signature(device, currentInputHost || token.host) === token.signature;
    }

    function valuesFromResponse(result = {}, ctx = null) {
        const canonical = result.device_context?.canonical || result.device_context?.identity || {};
        const identity = ctx?.identity || result.identity || {};
        const add = (bucket, value) => {
            const v = clean(value);
            if (v) bucket.add(v);
        };
        const serials = new Set();
        const hostnames = new Set();
        const deviceIds = new Set();
        const mgmtIps = new Set();

        [
            result.serial_number, result.serial, canonical.serial_number,
            canonical.serial, ctx?.serial_number, ctx?.serial, identity.serial_number,
            identity.serial
        ].forEach(v => add(serials, v));
        [
            result.hostname, canonical.hostname, ctx?.hostname,
            identity.hostname
        ].forEach(v => add(hostnames, v));
        [
            result.registered_device_id, result.device_id, canonical.device_id,
            ctx?.device_id, identity.device_id,
            ...(Array.isArray(identity.scaler_ids) ? identity.scaler_ids : []),
            ...(Array.isArray(identity.inventory_keys) ? identity.inventory_keys : [])
        ].forEach(v => add(deviceIds, v));
        [
            result.management_ip, result.mgmt_ip, canonical.management_ip,
            canonical.mgmt_ip, ctx?.resolved_ip, ctx?.mgmt_ip, ctx?.ip,
            identity.mgmt_ip
        ].forEach(v => add(mgmtIps, v));

        return {
            serials: Array.from(serials),
            hostnames: Array.from(hostnames),
            deviceIds: Array.from(deviceIds),
            mgmtIps: Array.from(mgmtIps),
        };
    }

    function validateResponseForDevice(device, result = {}, token = null, opts = {}) {
        const host = clean(opts.host || token?.host || currentHost(device));
        const ids = valuesFromResponse(result, opts.ctx || null);
        const serialHost = isSerialLike(host) ? key(host) : '';
        if (serialHost && ids.serials.length && !ids.serials.some(v => key(v) === serialHost)) {
            return {
                ok: false,
                reason: `Backend returned serial ${ids.serials.join(', ')} for current SN ${host}.`
            };
        }

        const returnedMgmtIps = ids.mgmtIps
            .map(v => clean(v).split('/')[0])
            .filter(v => isIp(v));
        if (isIp(host) && returnedMgmtIps.length && !returnedMgmtIps.some(v => key(v) === key(host))) {
            return {
                ok: false,
                reason: `Backend returned management IP ${returnedMgmtIps.join(', ')} for current host ${host}.`
            };
        }

        const expectedId = clean(token?.deviceId || opts.deviceId || '');
        if (expectedId && !isGeneratedCanvasLabel(expectedId) && !serialHost && !isIp(expectedId)) {
            const returnedIds = ids.deviceIds.map(key);
            const returnedHosts = ids.hostnames.map(key);
            const returnedNames = returnedIds.concat(returnedHosts);
            if (returnedNames.length && !returnedNames.includes(key(expectedId))) {
                return {
                    ok: false,
                    reason: `Backend returned identity ${ids.deviceIds.concat(ids.hostnames).join(', ')} for current device ${expectedId}.`
                };
            }
        }

        return { ok: true, identities: ids };
    }

    function hasVerifiedMetadataIdentity(device, opts = {}) {
        if (!device) return false;
        const host = clean(opts.host || currentHost(device));
        const strongRegistered = !!(
            device._registeredDeviceId
            || device._registeredHostname
            || device._registeredMgmtIp
            || device._registeredSerialNumber
            || device._monitoredKey
        );
        if (device._monitorRegistered && strongRegistered) return true;
        if (strongRegistered) return true;
        if (device._metadataDiscovered && host && !isGeneratedCanvasLabel(host)) return true;
        if (device._sshReachable && host && !isGeneratedCanvasLabel(host)) return true;
        return false;
    }

    function hasKnownMetadataIdentity(device, opts = {}) {
        if (!device) return false;
        const host = clean(opts.host || currentHost(device));
        const strongRegistered = !!(
            device._registeredDeviceId
            || device._registeredHostname
            || device._registeredMgmtIp
            || device._registeredSerialNumber
            || device._monitoredKey
        );
        const identity = device._identity || {};
        const hasIdentityContext = !!(
            identity.mgmt_ip
            || identity.serial
            || (Array.isArray(identity.scaler_ids) && identity.scaler_ids.length)
            || (Array.isArray(identity.inventory_keys) && identity.inventory_keys.length)
        );
        const hasMonitorContext = !!(
            device._monitorRegistered
            || device._monitorContext
            || device._monitorCapabilities
            || device._monitoringOptions
        );
        if (strongRegistered || hasIdentityContext || hasMonitorContext || device._metadataDiscovered) {
            return true;
        }
        return !!(device._sshReachable && host && !isGeneratedCanvasLabel(host));
    }

    function metadataSignature(device, opts = {}) {
        return signature(device, opts.host || currentHost(device));
    }

    function markMetadataReady(device, kind, opts = {}) {
        if (!device || !kind) return null;
        const readiness = device._metadataReadiness || {};
        const host = clean(opts.host || currentHost(device));
        const deviceId = clean(opts.deviceId || '');
        const stamp = {
            status: opts.status || 'ready',
            signature: metadataSignature(device, { host }),
            host,
            deviceId,
            source: clean(opts.source || opts.data?.source || ''),
            updatedAt: opts.updatedAt || Date.now()
        };
        readiness[kind] = stamp;
        device._metadataReadiness = readiness;
        device._metadataDiscovered = true;
        if (opts.data && typeof opts.data === 'object') {
            opts.data._metadataIdentity = { ...stamp };
        }
        return stamp;
    }

    function markMetadataLoading(device, kind, opts = {}) {
        if (!device || !kind) return null;
        const readiness = device._metadataReadiness || {};
        const host = clean(opts.host || currentHost(device));
        const stamp = {
            status: 'loading',
            signature: metadataSignature(device, { host }),
            host,
            deviceId: clean(opts.deviceId || ''),
            source: clean(opts.source || ''),
            updatedAt: Date.now()
        };
        readiness[kind] = stamp;
        device._metadataReadiness = readiness;
        return stamp;
    }

    function metadataState(device, kind, opts = {}) {
        if (!device || !kind) {
            return { ready: false, loading: false, status: 'unknown', reason: 'no_device' };
        }
        const host = clean(opts.host || currentHost(device));
        if (!hasVerifiedMetadataIdentity(device, { host })) {
            if (hasKnownMetadataIdentity(device, { host }) && host && !isGeneratedCanvasLabel(host)) {
                return { ready: false, loading: false, status: 'unknown', reason: 'not_fetched' };
            }
            return { ready: false, loading: false, status: 'unknown', reason: 'identity_unverified' };
        }
        const stamp = device._metadataReadiness?.[kind] || opts.data?._metadataIdentity || null;
        if (!stamp) {
            return { ready: false, loading: false, status: 'unknown', reason: 'not_fetched' };
        }
        const currentSig = metadataSignature(device, { host });
        if (stamp.signature !== currentSig) {
            return { ready: false, loading: false, status: 'stale', reason: 'identity_changed' };
        }
        if (stamp.status === 'loading') {
            return { ready: false, loading: true, status: 'loading', reason: 'fetching', stamp };
        }
        if (stamp.status !== 'ready') {
            return { ready: false, loading: false, status: stamp.status || 'unknown', reason: 'not_ready', stamp };
        }
        return { ready: true, loading: false, status: 'ready', reason: '', stamp };
    }

    function isMetadataReady(device, kind, opts = {}) {
        return metadataState(device, kind, opts).ready;
    }

    function applyHostnameCanvasMismatch(device, configHostname, opts = {}) {
        if (!device || device.type !== 'device') {
            return { applied: false, mismatch: false, reason: 'not_device' };
        }

        const cfgHost = clean(configHostname);
        if (!cfgHost) {
            return { applied: false, mismatch: false, reason: 'missing_config_hostname' };
        }

        const currentLabel = clean(device.label);
        const prevCfgHost = device._identity?.config_hostname || device._configHostname || '';
        let mismatch = cfgHost !== '' && currentLabel !== '' && cfgHost !== currentLabel;
        const giSerialIdentity = mismatch && isGiMode(device, opts) && isSerialLike(cfgHost);

        if (giSerialIdentity) {
            mismatch = false;
        }

        if (mismatch) {
            const inv = global._deviceInventory || global.deviceInventory;
            if (inv?.devices) {
                for (const info of Object.values(inv.devices)) {
                    const hn = clean(info?.hostname).replace(/,$/, '').trim();
                    if (hn && hn === currentLabel) {
                        mismatch = false;
                        break;
                    }
                }
            }
        }

        device._identity = {
            ...(device._identity || {}),
            config_hostname: cfgHost,
            hostname_mismatch: mismatch,
            canvas_label: currentLabel,
            gi_serial_identity: giSerialIdentity || false,
            device_state: clean(opts.deviceState || opts.mode || device?._identity?.device_state || device?._modeRawState || device?._deviceMode || ''),
        };
        device._configHostname = cfgHost;
        device._hostnameMismatch = mismatch;

        const editor = opts.editor || global.topologyEditor || null;
        const deviceId = opts.deviceId || device._registeredDeviceId || device._registeredHostname || device.deviceSerial || device.serial || device.label || '';
        const shouldAutoRepair = typeof opts.shouldAutoRepairLabel === 'function'
            ? opts.shouldAutoRepairLabel(currentLabel, cfgHost)
            : false;

        if (mismatch && shouldAutoRepair) {
            device.label = cfgHost;
            device._hostnameMismatch = false;
            device._identity.hostname_mismatch = false;
            device._identity.canvas_label = cfgHost;
            device._mismatchDismissed = false;
            device._badgeWorlds = null;
            if (editor?.autoSave) editor.autoSave();
            if (editor?.showNotification) {
                editor.showNotification(
                    `[INFO] Repaired device label: "${currentLabel}" -> "${cfgHost}"`,
                    'info', 6000
                );
            }
            if (editor?.requestDraw) editor.requestDraw();
            else if (editor?.drawing?.draw) editor.drawing.draw();
            return { applied: true, mismatch: false, repaired: true, configHostname: cfgHost, canvasLabel: cfgHost };
        }

        if (mismatch) {
            if (prevCfgHost !== cfgHost) {
                device._mismatchDismissed = false;
            }
            try {
                global.dispatchEvent(new CustomEvent('device:identity-mismatch', {
                    detail: {
                        deviceId,
                        device,
                        configHostname: cfgHost,
                        canvasLabel: currentLabel,
                        source: opts.source || 'device-identity',
                    }
                }));
            } catch (_) {
                // Non-browser unit checks may not provide CustomEvent.
            }
        } else {
            device._mismatchDismissed = false;
            device._badgeWorlds = null;
        }

        if (editor?.requestDraw) editor.requestDraw();
        else if (editor?.drawing?.draw) editor.drawing.draw();
        return { applied: true, mismatch, repaired: false, configHostname: cfgHost, canvasLabel: currentLabel };
    }

    function invalidateIdentityBoundMetadata(device, newHost = '', opts = {}) {
        if (!device) return false;
        const cfg = device.sshConfig || {};
        const nextHost = clean(newHost);
        const oldKeys = [
            cfg._userSavedHost,
            cfg.host,
            device.deviceSerial,
            device.serial,
            device._registeredSerialNumber,
            device._registeredDeviceId,
            device._registeredHostname,
            device._registeredMgmtIp,
            device._monitoredKey
        ].map(key).filter(Boolean);
        const nextKey = key(nextHost);
        const force = !!opts.force;
        const previousHostKey = key(opts.previousHost || '');
        const changed = force
            || (!!previousHostKey && previousHostKey !== nextKey)
            || (!!nextKey && oldKeys.length > 0 && !oldKeys.includes(nextKey));
        if (!changed) return false;

        delete device._registeredDeviceId;
        delete device._registeredHostname;
        delete device._registeredMgmtIp;
        delete device._registeredSerialNumber;
        delete device.registeredDeviceId;
        delete device.registeredHostname;
        delete device.registeredSerialNumber;
        delete device._monitoredKey;
        delete device._monitorRegistered;
        delete device._monitorCapabilities;
        delete device._monitoringOptions;
        delete device._monitoredSubsystems;
        delete device._monitorContext;
        delete device._monitorConfigFacts;
        delete device._monitorReferenceTotal;
        delete device._monitorReferenceUserCount;
        delete device._monitoredReferenceTotal;
        delete device._monitoredReferenceUserCount;
        delete device._onboardingPhase;
        delete device._onboarding;
        delete device._identity;
        delete device._configHostname;
        device._hostnameMismatch = false;
        device._metadataDiscovered = false;
        device._metadataReadiness = {};
        device._stackData = null;
        delete device._stackCachedAt;
        device._gitCommit = null;
        device._gitCommitFetchedAt = null;
        delete device._gitCommitFailed;
        device._deviceMode = '';
        device._modeRawState = '';
        delete device._modeFetchedAt;
        device._sshReachable = false;
        delete device._sshReachableAt;
        device._lldpData = createUnknownLldpData();
        device.lldpDiscoveryComplete = false;
        device.lldpEnabled = false;
        device._lldpNewResults = false;
        delete device._lldpCompletedAt;

        device.sshConfig = cfg;
        [
            '_registeredDeviceId', '_registeredHostname', '_registeredMgmtIp',
            '_registeredSerialNumber', '_enrichedMgmtIp', '_mgmtIp',
            '_nccMgmtIp', '_activeNccHost', '_activeNccIp', '_activeNccVm',
            '_nccVms', '_virshInfo'
        ].forEach(field => { delete cfg[field]; });

        if (isSerialLike(nextHost)) {
            device.deviceSerial = nextHost;
            device.serial = nextHost;
        }
        device._identityInvalidatedAt = Date.now();
        device._identityInvalidatedReason = opts.reason || 'host_changed';
        return true;
    }

    global.TopologyDeviceIdentity = {
        clean,
        key,
        isIp,
        isSerialLike,
        isGeneratedCanvasLabel,
        currentHost,
        resolveIdentity,
        signature,
        makeRequestToken,
        isRequestCurrent,
        valuesFromResponse,
        validateResponseForDevice,
        invalidateIdentityBoundMetadata,
        createUnknownLldpData,
        hasVerifiedMetadataIdentity,
        hasKnownMetadataIdentity,
        metadataSignature,
        markMetadataReady,
        markMetadataLoading,
        metadataState,
        isMetadataReady,
        isSerialLike,
        isGiMode,
        applyHostnameCanvasMismatch,
    };
})(window);

class DeviceManager {
    constructor(editor) {
        this.editor = editor;
    }

    // ========================================================================
    // ACCESSORS
    // ========================================================================
    
    get objects() { return this.editor.objects || []; }
    get deviceCounters() { return this.editor.deviceCounters || { router: 0, switch: 0 }; }
    get deviceNumbering() { return this.editor.deviceNumbering !== false; } // Default true

    // ========== CREATION ==========
    
    /**
     * Add a device (prompts for placement)
     * @param {string} type - Device type (e.g., 'SA-40C')
     * @returns {object|null} Created device or null
     */
    add(type) {
        if (this.editor.addDevice) {
            return this.editor.addDevice(type);
        }
        return null;
    }

    /**
     * Add a device at specific position
     * Contains the actual implementation for device creation
     * @param {string} type - Device type
     * @param {number} x - World X coordinate
     * @param {number} y - World Y coordinate
     * @returns {object|null} Created device or null
     */
    addAtPosition(type, x, y) {
        const editor = this.editor;
        
        // Snap position to grid
        const clickedWorld = { x, y };
        const clickedGrid = editor.worldToGrid(clickedWorld);
        const snappedGrid = {
            x: Math.round(clickedGrid.x),
            y: Math.round(clickedGrid.y)
        };
        const snappedWorld = editor.gridToWorld(snappedGrid);
        
        // Validate
        if (!isFinite(snappedWorld.x) || !isFinite(snappedWorld.y)) {
            snappedWorld.x = x;
            snappedWorld.y = y;
        }
        
        const label = this.getNextLabel(type);
        
        // Validate uniqueness
        if (editor.deviceNumbering && !this.isNameUnique(label)) {
            alert(`Device name "${label}" already exists.`);
            return null;
        }

        // Default colors
        const colorPickerEl = document.getElementById('color-picker');
        const defaultColor = type === 'router' ? '#5B9BD5' : (colorPickerEl ? colorPickerEl.value : '#4CAF50');
        
        const device = {
            id: `device_${editor.deviceIdCounter++}`,
            type: 'device',
            deviceType: type,
            x: snappedWorld.x,
            y: snappedWorld.y,
            radius: 50,
            rotation: 0,
            color: defaultColor,
            label: label,
            locked: false,
            visualStyle: editor.defaultDeviceStyle || 'circle',
            sshConfig: window.TopologyDeviceDefaults.createCanvasSshConfig(),
            ...window.TopologyDeviceDefaults.createCanvasLldpFields(),
            ...window.TopologyDeviceDefaults.createCanvasMetadataFields()
        };
        
        editor.saveState();
        editor.objects.push(device);
        editor.events?.emit('topology:loaded', {});
        editor.selectedObject = device;
        editor.selectedObjects = [device];
        editor.updateDeviceProperties();
        editor.draw();
        editor.lastClickPos = null;
        
        return device;
    }

    // ========== FINDING ==========
    
    /**
     * Find device at world coordinates
     * @param {number} x - World X
     * @param {number} y - World Y
     * @returns {object|null} Device object or null
     */
    findAt(x, y) {
        if (this.editor.findDeviceAt) {
            return this.editor.findDeviceAt(x, y);
        }
        return null;
    }

    /**
     * Get all devices
     * @returns {array} Array of device objects
     */
    getAll() {
        return this.editor.objects?.filter(obj => obj.type === 'device') || [];
    }

    /**
     * Get selected devices
     * @returns {array} Array of selected devices
     */
    getSelected() {
        return this.editor.selectedObjects?.filter(obj => obj.type === 'device') || [];
    }

    /**
     * Get device by ID
     * @param {string} id - Device ID
     * @returns {object|null} Device or null
     */
    getById(id) {
        return this.getAll().find(d => d.id === id) || null;
    }

    /**
     * Get device by label/name
     * @param {string} label - Device label
     * @returns {object|null} Device or null
     */
    getByLabel(label) {
        return this.getAll().find(d => d.label === label || d.name === label) || null;
    }

    // ========== NAMING (MIGRATED) ==========
    
    /**
     * Get next available device label
     * MIGRATED from topology.js getNextDeviceLabel()
     * @param {string} deviceType - 'router' or 'switch'
     * @returns {string} Next label
     */
    getNextLabel(deviceType) {
        // If numbering is disabled, always return base name
        if (!this.deviceNumbering) {
            return deviceType === 'router' ? 'NCP' : 'S';
        }
        
        // Numbering enabled - increment counter
        const counters = this.editor.deviceCounters || { router: 0, switch: 0 };
        counters[deviceType] = (counters[deviceType] || 0) + 1;
        this.editor.deviceCounters = counters;
        
        const count = counters[deviceType];
        
        if (count === 1) {
            return deviceType === 'router' ? 'NCP' : 'S';
        } else {
            return deviceType === 'router' ? `NCP-${count}` : `S${count}`;
        }
    }

    /**
     * Check if device name is unique
     * MIGRATED from topology.js isDeviceNameUnique()
     * @param {string} name - Name to check
     * @returns {boolean} True if unique
     */
    isNameUnique(name) {
        const existing = this.objects.find(obj => 
            obj.type === 'device' && obj.label === name
        );
        return !existing;
    }
    
    /**
     * Update device counters based on existing devices
     * MIGRATED from topology.js updateDeviceCounters()
     */
    updateCounters() {
        const counters = { router: 0, switch: 0 };
        
        this.objects.forEach(obj => {
            if (obj.type === 'device') {
                const label = obj.label || '';
                
                if (obj.deviceType === 'router') {
                    if (label === 'NCP' || label === 'R') {
                        counters.router = Math.max(counters.router, 1);
                    } else {
                        const matchNCP = label.match(/^NCP-(\d+)$/);
                        const matchR = label.match(/^R(\d+)$/);
                        if (matchNCP) {
                            counters.router = Math.max(counters.router, parseInt(matchNCP[1]));
                        } else if (matchR) {
                            counters.router = Math.max(counters.router, parseInt(matchR[1]));
                        }
                    }
                } else if (obj.deviceType === 'switch') {
                    if (label === 'S') {
                        counters.switch = Math.max(counters.switch, 1);
                    } else {
                        const match = label.match(/^S(\d+)$/);
                        if (match) {
                            counters.switch = Math.max(counters.switch, parseInt(match[1]));
                        }
                    }
                }
            }
        });
        
        this.editor.deviceCounters = counters;
        return counters;
    }

    /**
     * Update device label
     * @param {string} label - New label
     */
    updateLabel(label) {
        if (this.editor.updateDeviceLabel) {
            this.editor.updateDeviceLabel(label);
        }
    }

    /**
     * Apply device label to selection
     */
    applyLabel() {
        if (this.editor.applyDeviceLabel) {
            this.editor.applyDeviceLabel();
        }
    }

    // ========== MODES ==========
    
    /**
     * Set device placement mode
     * @param {string} deviceType - Type of device to place
     */
    setPlacementMode(deviceType) {
        if (this.editor.setDevicePlacementMode) {
            this.editor.setDevicePlacementMode(deviceType);
        }
    }

    /**
     * Toggle device placement mode
     * @param {string} deviceType - Device type
     */
    togglePlacementMode(deviceType) {
        if (this.editor.toggleDevicePlacementMode) {
            this.editor.toggleDevicePlacementMode(deviceType);
        }
    }

    // ========== STYLING ==========
    
    /**
     * Set device visual style
     * @param {string} style - Style name
     */
    setStyle(style) {
        if (this.editor.setDeviceStyle) {
            this.editor.setDeviceStyle(style);
        }
    }

    /**
     * Set device visual style (alternative)
     * @param {string} style - Style name
     */
    setVisualStyle(style) {
        if (this.editor.setDeviceVisualStyle) {
            this.editor.setDeviceVisualStyle(style);
        }
    }

    /**
     * Update device properties
     */
    updateProperties() {
        if (this.editor.updateDeviceProperties) {
            this.editor.updateDeviceProperties();
        }
    }

    /**
     * Update device radius
     * @param {number} radius - New radius
     */
    updateRadius(radius) {
        if (this.editor.updateDeviceRadius) {
            this.editor.updateDeviceRadius(radius);
        }
    }

    /**
     * Apply radius to selection
     */
    applyRadius() {
        if (this.editor.applyDeviceRadius) {
            this.editor.applyDeviceRadius();
        }
    }

    // ========== COLLISION ==========
    
    /**
     * Check device collision
     * @param {object} movingDevice - Device being moved
     * @param {number} proposedX - Proposed X position
     * @param {number} proposedY - Proposed Y position
     * @returns {object|null} Collision result
     */
    checkCollision(movingDevice, proposedX, proposedY) {
        if (this.editor.checkDeviceCollision) {
            return this.editor.checkDeviceCollision(movingDevice, proposedX, proposedY);
        }
        return null;
    }

    /**
     * Get device collision radius
     * @param {object} device - Device object
     * @returns {number} Collision radius
     */
    getCollisionRadius(device) {
        if (this.editor.getDeviceCollisionRadius) {
            return this.editor.getDeviceCollisionRadius(device);
        }
        return device.radius || 30;
    }

    /**
     * Get device visual bounds
     * @param {object} device - Device object
     * @returns {object} Bounds {x, y, width, height}
     */
    getVisualBounds(device) {
        if (this.editor.getDeviceVisualBounds) {
            return this.editor.getDeviceVisualBounds(device);
        }
        return { x: device.x, y: device.y, width: 60, height: 60 };
    }

    /**
     * Toggle collision detection
     */
    toggleCollision() {
        if (this.editor.toggleDeviceCollision) {
            this.editor.toggleDeviceCollision();
        }
    }

    // ========== TOOLBAR ==========
    
    /**
     * Show device selection toolbar
     * @param {object} device - Selected device
     */
    showToolbar(device) {
        if (this.editor.showDeviceSelectionToolbar) {
            this.editor.showDeviceSelectionToolbar(device);
        }
    }

    /**
     * Hide device selection toolbar
     */
    hideToolbar() {
        if (this.editor.hideDeviceSelectionToolbar) {
            this.editor.hideDeviceSelectionToolbar();
        }
    }

    /**
     * Show device style palette
     * @param {object} device - Device object
     */
    showStylePalette(device) {
        if (this.editor.showDeviceStylePalette) {
            this.editor.showDeviceStylePalette(device);
        }
    }

    // ========== EDITOR ==========
    
    /**
     * Show device editor panel
     * @param {object} device - Device to edit
     */
    showEditor(device) {
        if (this.editor.showDeviceEditor) {
            this.editor.showDeviceEditor(device);
        }
    }

    /**
     * Hide device editor panel
     */
    hideEditor() {
        if (this.editor.hideDeviceEditor) {
            this.editor.hideDeviceEditor();
        }
    }

    /**
     * Update device editor property
     * @param {string} property - Property name
     * @param {*} value - Property value
     */
    updateEditorProperty(property, value) {
        if (this.editor.updateDeviceEditorProperty) {
            this.editor.updateDeviceEditorProperty(property, value);
        }
    }

    // ========== INLINE RENAME ==========
    
    /**
     * Show inline device rename
     * @param {object} device - Device to rename
     */
    showInlineRename(device) {
        if (this.editor.showInlineDeviceRename) {
            this.editor.showInlineDeviceRename(device);
        }
    }

    /**
     * Hide inline device rename
     */
    hideInlineRename() {
        if (this.editor.hideInlineDeviceRename) {
            this.editor.hideInlineDeviceRename();
        }
    }

    // ========== DISPLAY OPTIONS ==========
    
    /**
     * Toggle device numbering display
     */
    toggleNumbering() {
        if (this.editor.toggleDeviceNumbering) {
            this.editor.toggleDeviceNumbering();
        }
    }

    /**
     * Toggle movable devices mode
     */
    toggleMovable() {
        if (this.editor.toggleMovableDevices) {
            this.editor.toggleMovableDevices();
        }
    }

    // ========== NAVIGATION ==========
    
    /**
     * Center view on all devices
     */
    centerOnAll() {
        if (this.editor.centerOnDevices) {
            this.editor.centerOnDevices();
        }
    }

    // ========== CONNECTIONS ==========
    
    /**
     * Get all devices connected to a link
     * @param {object} link - Link object
     * @returns {array} Connected devices
     */
    getConnectedToLink(link) {
        if (this.editor.getAllConnectedDevices) {
            return this.editor.getAllConnectedDevices(link);
        }
        return [];
    }

    /**
     * Get BUL endpoint devices
     * @param {object} link - Link object
     * @returns {array} Endpoint devices
     */
    getBULEndpoints(link) {
        if (this.editor.getBULEndpointDevices) {
            return this.editor.getBULEndpointDevices(link);
        }
        return [];
    }

    // ========== MODEL DETECTION ==========
    
    /**
     * Detect model from device name
     * @param {string} deviceName - Device name
     * @returns {string|null} Detected model
     */
    detectModel(deviceName) {
        if (this.editor.detectModelFromDeviceName) {
            return this.editor.detectModelFromDeviceName(deviceName);
        }
        return null;
    }

    // ========== COUNTERS ==========
    
    /**
     * Update device counters
     */
    updateCounters() {
        if (this.editor.updateDeviceCounters) {
            this.editor.updateDeviceCounters();
        }
    }

    // ========== UTILITY ==========
    
    /**
     * Get count of devices
     * @returns {number} Count
     */
    getCount() {
        return this.getAll().length;
    }

    /**
     * Delete a device
     * @param {object} device - Device to delete
     */
    delete(device) {
        if (device && this.editor.objects) {
            const idx = this.editor.objects.indexOf(device);
            if (idx !== -1) {
                this.editor.objects.splice(idx, 1);
                try {
                    if (window.MonitoredCache && typeof window.MonitoredCache.detachOnDelete === 'function') {
                        window.MonitoredCache.detachOnDelete(device);
                    }
                } catch (_) {}
                this.editor.events?.emit('topology:loaded', {});
                this.editor.draw();
                this.editor.saveState();
            }
        }
    }

    /**
     * Get device categories from platform data
     * @returns {array} Category names
     */
    getCategories() {
        if (this.editor.platformData) {
            return this.editor.platformData.getCategories();
        }
        return ['SA', 'CL', 'NC-AI', 'DNAAS'];
    }

    /**
     * Get platforms for a category
     * @param {string} category - Category name
     * @returns {array} Platform objects
     */
    getPlatforms(category) {
        if (this.editor.platformData) {
            return this.editor.platformData.getPlatformsByCategory(category);
        }
        return [];
    }
}

// Export for module loading
window.DeviceManager = DeviceManager;
window.createDeviceManager = function(editor) {
    return new DeviceManager(editor);
};

console.log('[topology-devices.js] DeviceManager with naming functions loaded');

// =========================================================================
// AUTO-MONITOR (Phase 2 MVP) -- smooth-ZTP hydrate cache.
// =========================================================================
//
// On every `topology:loaded` event, fetch the caller's monitored-device
// list from the backend ONCE and stamp `_sshReachable=true` on every
// canvas device whose IP appears in the registry. This means PE-1 /
// PE-4 / RR-SA-2 (and any device a previous user attached) get the
// full toolbar button set on FIRST paint, not on the next selection
// toggle. Without the cache the toolbar would briefly show the
// truncated set, then upgrade after the first SSH probe -- a flicker
// the user explicitly called out as a regression risk in OQ-7.
//
// The cache is module-level (one instance per browser tab) and keyed
// by IP. Stale data is harmless because the tooltip says "[OK]" /
// "[stale]" / "[unknown]" based on `_sshReachableAt` age in
// `topology-device-toolbar.js` (lines 314-316).
//
// See topology/docs/AUTO_MONITOR_ON_ATTACH.md Section 7.
(function (global) {
    'use strict';
    const MAX_AGE_MS = 60 * 1000;   // refetch when older than 60s
    const FRESHNESS_FALLBACK = 12 * 60 * 60 * 1000;  // 12 h max horizon
    let _byIp = null;       // Map<ip, record>
    let _fetchedAt = 0;
    let _inFlight = null;

    async function refresh(force = false) {
        if (!global.ScalerAPI || typeof global.ScalerAPI.listMonitored !== 'function') {
            return null;
        }
        const now = Date.now();
        if (!force && _byIp && (now - _fetchedAt) < MAX_AGE_MS) return _byIp;
        if (_inFlight) return _inFlight;
        _inFlight = (async () => {
            try {
                const resp = await global.ScalerAPI.listMonitored();
                const map = new Map();
                for (const d of (resp && resp.devices) || []) {
                    if (d && d.management_ip) map.set(d.management_ip, d);
                    if (d && Array.isArray(d.cluster_ncc_ips)) {
                        for (const ncc of d.cluster_ncc_ips) {
                            if (ncc) map.set(ncc, d);
                        }
                    }
                }
                _byIp = map;
                _fetchedAt = Date.now();
                return _byIp;
            } catch (err) {
                console.warn('[MonitoredCache] refresh failed:', err && err.message);
                return _byIp;
            } finally {
                _inFlight = null;
            }
        })();
        return _inFlight;
    }

    function getByIp(ip) {
        if (!_byIp || !ip) return null;
        return _byIp.get(String(ip).trim()) || null;
    }

    function _isFresh(record) {
        if (!record || !record.last_seen_ok) return false;
        const t = Date.parse(record.last_seen_ok);
        if (!Number.isFinite(t)) return false;
        return (Date.now() - t) < FRESHNESS_FALLBACK;
    }

    function applyTo(device) {
        if (!device) return false;
        const ip = (device.sshConfig && device.sshConfig.host) || device.deviceAddress || '';
        const record = getByIp((ip || '').trim());
        if (!record) return false;
        if (!_isFresh(record)) return false;
        // Any in-session decision (from topology-device-monitor.js or the
        // SSH save handler) within MAX_AGE_MS is authoritative -- whether
        // it is true OR false. The cache only fills the cold-start gap.
        const sessionAge = device._sshReachableAt
            ? (Date.now() - device._sshReachableAt) : Infinity;
        if (sessionAge < MAX_AGE_MS) return false;
        device._sshReachable = true;
        device._sshReachableAt = Date.parse(record.last_seen_ok) || Date.now();
        device._monitorRegistered = true;
        if (record.key) device._monitoredKey = record.key;
        if (typeof record.references_count_total === 'number') {
            device._monitoredReferenceTotal = record.references_count_total;
        }
        if (typeof record.references_user_count === 'number') {
            device._monitoredReferenceUserCount = record.references_user_count;
        }
        return true;
    }

    async function hydrateCanvas() {
        await refresh();
        const editor = global.topologyEditor;
        if (!editor || !Array.isArray(editor.objects)) return 0;
        let stamped = 0;
        for (const obj of editor.objects) {
            if (obj && obj.type === 'device' && applyTo(obj)) stamped += 1;
        }
        if (stamped > 0) {
            try {
                if (typeof editor.draw === 'function') editor.draw();
            } catch (_) {}
        }
        return stamped;
    }

    async function detachOnDelete(device) {
        if (!device || !device._monitorRegistered) return null;
        const ip = (device.sshConfig && device.sshConfig.host) || device.deviceAddress || '';
        if (!ip || !global.ScalerAPI || typeof global.ScalerAPI.detachReference !== 'function') {
            return null;
        }
        try {
            const resp = await global.ScalerAPI.detachReference(ip.trim(), {});
            // Spec OQ-7-style hook: if the response says the registry
            // is now refcount=0, future Phase-3 work surfaces a modal.
            // For Phase 2 MVP this is a silent detach -- we just log so
            // the UI dev can confirm the contract end-to-end.
            try {
                if (resp && resp.would_stop_monitoring) {
                    console.info('[MonitoredCache] detach: would_stop_monitoring=true for', ip);
                }
            } catch (_) {}
            // Drop the cache entry so the next paint doesn't re-stamp.
            try { if (_byIp) _byIp.delete(ip.trim()); } catch (_) {}
            return resp;
        } catch (err) {
            console.warn('[MonitoredCache] detach failed for', ip, err && err.message);
            return null;
        }
    }

    global.MonitoredCache = {
        refresh,
        getByIp,
        applyTo,
        hydrateCanvas,
        detachOnDelete,
        // Expose the underlying map for tests / debugging only.
        _peek: () => ({ byIp: _byIp ? Array.from(_byIp.keys()) : [], fetchedAt: _fetchedAt }),
    };

    // Auto-hydrate on every topology load. Uses a small delay so the
    // initial draw has finished before we stamp + redraw -- this gives
    // the user the immediate "topology painted" feedback, then a
    // sub-second upgrade as the registry response lands.
    if (typeof global.addEventListener === 'function') {
        global.addEventListener('topology:loaded', () => {
            setTimeout(() => {
                hydrateCanvas().catch(() => {});
            }, 50);
        });
    }
})(window);
