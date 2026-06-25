// ============================================================================
// TOPOLOGY GENERATOR MODULE
// ============================================================================
// Smart, multi-source topology generator that turns real device data into
// detailed canvas topologies. Sources include the existing canvas, live
// device context (SSH-backed), DNAAS discovery, the Network Mapper LLDP
// crawler, and offline imports. Each source feeds one normalized facts
// model, which the generator turns into canvas-ready objects (devices,
// links, text labels, grouping shapes) with link-table metadata, then
// shows a preview before applying.
//
// The Network Mapper module (NetworkMapperManager) keeps owning the
// LLDP-discovery sub-flow and its DOM IDs; this module wraps it as one
// adapter among several so we never regress that path.
//
// All mutating backend calls go through window.TopologyAuth.authFetch so
// JWT + per-user storage work end to end.
// ============================================================================

(function () {
    'use strict';

    const SOURCE_TABS = ['canvas', 'live', 'mapper', 'import'];

    // Editor resolver (2026-04-26b)
    // ----------------------------------------------------------------
    // The app exposes the live TopologyEditor instance as
    // ``window.topologyEditor`` (see topology.js init). Earlier revisions
    // of this module read ``window.editor`` only, so on first load
    // ``_waitForEditor`` would loop forever and ``setupPanel()`` never
    // ran -- the user saw the panel header + tabs but every tab pane
    // stayed ``display: none`` (intentional default in index.html).
    // Always resolve through this helper instead of touching the
    // global directly.
    function _editor() {
        return window.topologyEditor || window.editor || null;
    }

    // Multi-user JWT-aware fetch wrapper. Falls back to plain fetch only
    // for read paths if TopologyAuth is not yet attached -- the network
    // mapper's existing /api/network-mapper/* routes already accept the
    // unauthenticated fallback in dev profiles.
    function _authFetch(url, opts) {
        const auth = window.TopologyAuth;
        if (auth && typeof auth.authFetch === 'function') {
            return auth.authFetch(url, opts);
        }
        return fetch(url, opts);
    }

    // ------------------------------------------------------------------ utils

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = (str == null ? '' : String(str));
        return div.innerHTML;
    }

    function isDnaasDeviceName(name) {
        if (!name) return false;
        const u = String(name).toUpperCase();
        const patterns = [
            'DNAAS', 'LEAF', 'SPINE', 'FABRIC', 'TOR', 'AGGREGATION',
            'AGG-', 'CORE-', '-LEAF', '-SPINE', 'NCM', 'NCF', 'NCC',
            'SUPERSPINE'
        ];
        return patterns.some(p => u.includes(p));
    }

    function isExpectedDutDeviceName(name) {
        if (!name) return false;
        const u = String(name).toUpperCase();
        return /(^|[^A-Z0-9])PE[-_ ]?\d+([^A-Z0-9]|$)/.test(u)
            || /(^|[^A-Z0-9])CE[-_ ]?\d*([^A-Z0-9]|$)/.test(u)
            || /(^|[^A-Z0-9])RR[-_A-Z0-9]*\d*([^A-Z0-9]|$)/.test(u)
            || /(^|[^A-Z0-9])P[-_ ]?\d+([^A-Z0-9]|$)/.test(u);
    }

    function isCanvasDiscoveryExcludedDevice(editor, device) {
        if (!device) return true;
        if (device._isDnaas || device.isDnaas || device.dnaas || device.source === 'dnaas' || device._origin === 'dnaas-bd') {
            return true;
        }
        const identityCandidates = [
            device.label,
            device.name,
            device.id,
            device.hostname,
            device.deviceSerial
        ].filter(Boolean);
        const hasDutIdentity = identityCandidates.some(isExpectedDutDeviceName);
        if (hasDutIdentity && getCanvasSshTarget(device)) {
            // PE-4-style DUTs may SSH through an active NCC/SN host. The
            // transport host can look like fabric, but the canvas identity is
            // still a DUT and must be included in Generate.
            return false;
        }
        if (identityCandidates.some(isDnaasDeviceName)) return true;
        if (editor && typeof editor.isDnaasRouter === 'function' && identityCandidates.some(v => editor.isDnaasRouter(v))) {
            return true;
        }
        return false;
    }

    function getCanvasSshTarget(device) {
        const ssh = device && device.sshConfig;
        if (!ssh) return null;
        const host = String(
            ssh.host
            || ssh.hostBackup
            || ssh._userSavedHost
            || ssh._snVerifiedHost
            || ssh._activeNccHost
            || (ssh._virshInfo && ssh._virshInfo.activeNcc)
            || ''
        ).trim();
        if (!host) return null;
        return {
            host,
            user: ssh.user || ssh._userSavedUser || 'dnroot',
            password: ssh.password || ssh._userSavedPass || ''
        };
    }

    function hasFactSshTarget(device) {
        return !!(device && device.ssh && (device.ssh.host || device.ssh.hostBackup));
    }

    function clonePlain(value) {
        try { return JSON.parse(JSON.stringify(value)); } catch (_) { return value; }
    }

    /** POST collected facts to the per-user temp SQLite correlation engine. */
    async function correlateFactsRemote(facts, opts) {
        const active = (window.TopologySync && typeof window.TopologySync.getActive === 'function')
            ? window.TopologySync.getActive() : null;
        const resp = await _authFetch('/api/topology-generator/correlate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                facts,
                options: opts || {},
                domain_id: (active && active.domain_id) || '',
                topology_id: (active && active.topology_id) || ''
            })
        });
        const text = await resp.text();
        let data = {};
        try { data = JSON.parse(text); } catch (_) {}
        if (!resp.ok) {
            const detail = (data && (data.detail || data.message)) || text || ('HTTP ' + resp.status);
            throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
        }
        return data;
    }

    function isCanvasLiveSource(source) {
        return source === 'canvas' || source === 'selected';
    }

    function getTargetSshHost(target) {
        if (!target) return '';
        return String(
            target.host
            || (target.ssh && (target.ssh.host || target.ssh.hostBackup))
            || target._appSshHost
            || ''
        ).trim();
    }

    function findCanvasDeviceForTarget(editor, target) {
        const objs = (editor && Array.isArray(editor.objects)) ? editor.objects : [];
        if (!target) return null;
        if (target.canvasId) {
            const byId = objs.find(o => o && o.id === target.canvasId);
            if (byId) return byId;
        }
        const keys = [
            target.deviceId,
            target.hostname,
            target.label,
            target.serial,
            target.host,
            target._appSshHost
        ].filter(Boolean).map(v => String(v).toLowerCase());
        return objs.find(o => {
            if (!o || o.type !== 'device') return false;
            const ssh = o.sshConfig || {};
            const candidates = [
                o.id, o.label, o.name, o.deviceSerial,
                ssh.host, ssh.hostBackup, ssh._snVerifiedHost, ssh._activeNccHost,
                ssh._virshInfo && ssh._virshInfo.activeNcc
            ].filter(Boolean).map(v => String(v).toLowerCase());
            return keys.some(k => candidates.includes(k));
        }) || null;
    }

    function enrichTargetFromCanvas(editor, target) {
        const out = Object.assign({}, target || {});
        const canvasDevice = findCanvasDeviceForTarget(editor, out);
        if (!canvasDevice) return out;
        const sshTarget = getCanvasSshTarget(canvasDevice);
        if (sshTarget) {
            out._appSshHost = sshTarget.host;
            out.host = out.host || sshTarget.host;
            out.ssh = Object.assign({}, canvasDevice.sshConfig || {}, out.ssh || {}, {
                host: (out.ssh && out.ssh.host) || out.host || sshTarget.host,
                hostBackup: (out.ssh && out.ssh.hostBackup) || (canvasDevice.sshConfig && canvasDevice.sshConfig.hostBackup) || '',
                user: (out.ssh && out.ssh.user) || sshTarget.user || 'dnroot',
                password: (out.ssh && out.ssh.password) || sshTarget.password || 'dnroot'
            });
        }
        out.canvasId = out.canvasId || canvasDevice.id;
        out.label = out.label || canvasDevice.label || canvasDevice.name || canvasDevice.id;
        out.deviceId = out.deviceId || canvasDevice.label || canvasDevice.deviceSerial || canvasDevice.id;
        out.serial = out.serial || canvasDevice.deviceSerial || '';
        return out;
    }

    function compactLogicalLinks(links) {
        const groups = new Map();
        for (const L of (Array.isArray(links) ? links : [])) {
            if (!L || !L.fromDevice || !L.toDevice) continue;
            const pair = [L.fromDevice, L.toDevice].sort().join('|');
            const key = pair + '|' + (L.layer || 'routing') + '|' + (L.linkType || L.protocol || 'logical');
            if (!groups.has(key)) {
                groups.set(key, Object.assign({}, L, {
                    _protocols: [],
                    _mergedCount: 0
                }));
            }
            const g = groups.get(key);
            const proto = String(L.protocol || L.linkType || '').trim();
            if (proto && !g._protocols.includes(proto)) g._protocols.push(proto);
            g._mergedCount++;
        }
        return Array.from(groups.values()).map(g => {
            const protocols = g._protocols || [];
            if (protocols.length > 1) {
                const shown = protocols.slice(0, 3).join('\n');
                g.protocol = shown + (protocols.length > 3 ? `\n+${protocols.length - 3} more` : '');
            } else if (protocols.length === 1) {
                g.protocol = protocols[0];
            }
            if (g._mergedCount > 1) g._mergedOverlayCount = g._mergedCount;
            delete g._protocols;
            delete g._mergedCount;
            return g;
        });
    }

    const GENERATE_STYLE_PROFILE = {
        links: {
            physical: { color: '#38bdf8', style: 'solid', width: 2.4 },
            iBGP: { color: '#60a5fa', style: 'dashed', width: 1.75 },
            eBGP: { color: '#f59e0b', style: 'dashed', width: 1.9 },
            ISIS: { color: '#8e44ad', style: 'dotted', width: 1.35 },
            OSPF: { color: '#27ae60', style: 'dotted', width: 1.35 },
            VRF: { color: '#1abc9c', style: 'dotted', width: 1.15 },
            BD: { color: '#ff5e1f', style: 'dotted', width: 1.15 },
            'EVPN-RT': { color: '#f39c12', style: 'dashed', width: 1.15 },
            unmatched: { color: '#95a5a6', style: 'dotted', width: 1 }
        },
        shapes: {
            as: { fillOpacity: 0.055, padX: 42, padY: 42, cornerRadius: 18 },
            service: { fillOpacity: 0.105, padX: 28, padY: 20, cornerRadius: 16 },
            vrf: { fillOpacity: 0.045, padX: 34, padY: 30, cornerRadius: 16 },
            bd: { fillOpacity: 0.04, padX: 30, padY: 26, cornerRadius: 14 },
            unmatched: { fillOpacity: 0.035, padX: 28, padY: 24, cornerRadius: 14 }
        }
    };

    function styleForLinkType(linkType, layer) {
        const key = linkType || (layer === 'physical' ? 'physical' : 'unmatched');
        return GENERATE_STYLE_PROFILE.links[key] || GENERATE_STYLE_PROFILE.links[layer] || GENERATE_STYLE_PROFILE.links.unmatched;
    }

    function generatedConfidenceFromFact(fact, fallback = 'correlated') {
        const explicit = String((fact && (fact.confidenceClass || fact._confidenceClass)) || '').toLowerCase();
        if (['verified', 'correlated', 'inferred', 'missing'].includes(explicit)) return explicit;
        const source = String((fact && (fact.source || fact._source || fact.note)) || '').toLowerCase();
        if (/known-topology|verified|lldp|device-facts|live/.test(source)) return 'verified';
        if (/sqlite|correlat|bgp|service|route-target|rt/.test(source)) return 'correlated';
        if (/inferred|alias|fallback|compose/.test(source)) return 'inferred';
        if (/missing|unmatched|failed|skipped/.test(source)) return 'missing';
        return fallback;
    }

    function generatedSourceFromFact(fact, fallback = 'generated') {
        return String((fact && (fact.source || fact._source || fact.note)) || fallback);
    }

    function generatedEvidenceSummary(fact) {
        const evidence = [];
        const ld = (fact && fact.linkDetails) || {};
        const lt = (fact && fact.linkTable) || {};
        [
            fact && fact.protocol,
            fact && fact.linkType,
            fact && fact.fromInterface,
            fact && fact.toInterface,
            ld.peerIp,
            ld.routerIdA && ld.routerIdB ? `${ld.routerIdA}<->${ld.routerIdB}` : '',
            ld.ipAddressA && ld.ipAddressB ? `${ld.ipAddressA}<->${ld.ipAddressB}` : '',
            lt.device1Interface && lt.device2Interface ? `${lt.device1Interface}<->${lt.device2Interface}` : ''
        ].filter(Boolean).forEach(item => evidence.push(String(item)));
        return Array.from(new Set(evidence)).slice(0, 6);
    }

    function generatedPriorityForLayer(layer, kind) {
        if (layer === 'device') return 100;
        if (layer === 'physical' || layer === 'underlay') return 90;
        if (layer === 'routing' || layer === 'overlay') return 80;
        if (layer === 'service') return 75;
        if (kind === 'label' || layer === 'identity') return 45;
        if (layer === 'evidence') return 25;
        return 50;
    }

    function applyGeneratedSceneMeta(obj, opts = {}) {
        if (!obj) return obj;
        const layer = opts.layer || obj._generatedLayer || obj.layer || 'generated';
        const confidence = opts.confidence || obj._generatedConfidence || 'correlated';
        obj._generatedTopologyObject = true;
        obj._generatedLayer = layer;
        obj._generatedConfidence = confidence;
        obj._generatedSource = opts.source || obj._generatedSource || 'generated';
        obj._generatedEvidence = Array.isArray(opts.evidence) ? opts.evidence : (obj._generatedEvidence || []);
        obj._generatedDisplayPriority = opts.displayPriority != null
            ? opts.displayPriority
            : generatedPriorityForLayer(layer, opts.kind || obj.type);
        return obj;
    }

    function inferTopologyFamily(facts) {
        const devices = Array.isArray(facts.devices) ? facts.devices : [];
        const roles = new Set(devices.map(d => String(d.role || '').toLowerCase()));
        const hasRR = devices.some(d => /(^|[-_])rr($|[-_])|route.?reflector/i.test(d.hostname || '') || String(d.role || '').toLowerCase() === 'rr');
        const hasPE = devices.some(d => String(d.role || '').toLowerCase() === 'pe' || /(^|[-_])pe[-_0-9]/i.test(d.hostname || ''));
        const hasCE = devices.some(d => String(d.role || '').toLowerCase() === 'ce' || /(^|[-_])ce($|[-_0-9])/i.test(d.hostname || ''));
        if ((hasRR && hasPE) || (hasPE && hasCE)) return 'rr-pe-service';
        if (roles.has('spine') && roles.has('leaf')) return 'clos';
        if (roles.has('p') || roles.has('core') || roles.has('super-spine')) return 'backbone';
        if (devices.length <= 4) return 'small-mesh';
        return 'tiered';
    }

    function deviceRoleBucket(device) {
        const name = String(device.hostname || device.label || '').toLowerCase();
        const role = String(device.role || '').toLowerCase();
        if (role === 'rr' || name.includes('rr')) return 'rr';
        if (role === 'spine' || role === 'super-spine' || role === 'core' || name.includes('spine')) return 'core';
        if (role === 'pe' || /(^|[-_])pe[-_0-9]/i.test(name)) return 'pe';
        if (role === 'ce' || /(^|[-_])ce($|[-_0-9])/i.test(name)) return 'ce';
        if (role === 'external' || name.includes('server') || name.includes('spirent') || name.includes('ixia')) return 'external';
        return 'router';
    }

    function synthesizeRoleHints(facts) {
        const devices = Array.isArray(facts && facts.devices) ? facts.devices : [];
        const overlayLinks = []
            .concat((facts && facts.logicalLinks) || [])
            .filter(l => /bgp|overlay|evpn|vpn|rt-/i.test(String(l.linkType || l.protocol || '')));
        const overlayNeighbors = new Map();
        const addNeighbor = (a, b) => {
            if (!a || !b || a === b) return;
            if (!overlayNeighbors.has(a)) overlayNeighbors.set(a, new Set());
            overlayNeighbors.get(a).add(b);
        };
        overlayLinks.forEach(l => {
            addNeighbor(l.fromDevice, l.toDevice);
            addNeighbor(l.toDevice, l.fromDevice);
        });
        const asnCount = new Map();
        devices.forEach(d => {
            const asn = String(((d && d.config) || {}).asn || '').trim();
            if (asn) asnCount.set(asn, (asnCount.get(asn) || 0) + 1);
        });
        const hints = {};
        devices.forEach(d => {
            const id = d && d.id;
            if (!id) return;
            const explicit = String((d && d.role) || '').toLowerCase();
            if (['rr', 'pe', 'ce', 'core', 'router', 'leaf', 'spine', 'external'].includes(explicit)) {
                hints[id] = explicit;
                return;
            }
            const bucket = deviceRoleBucket(d);
            if (bucket && bucket !== 'router') {
                hints[id] = bucket;
                return;
            }
            const asn = String(((d && d.config) || {}).asn || '').trim();
            const peerCount = (overlayNeighbors.get(id) || new Set()).size;
            if (asn && peerCount >= 2) {
                const others = Array.from(asnCount.keys()).filter(a => a !== asn);
                if (others.length && (asnCount.get(asn) || 0) <= 1) {
                    hints[id] = 'rr';
                    return;
                }
            }
            hints[id] = peerCount >= 1 ? 'pe' : 'router';
        });
        return hints;
    }

    function placeHubSpokeTriangle(devices, hints, centerX, topY, radius) {
        centerX = centerX == null ? 720 : centerX;
        topY = topY == null ? 220 : topY;
        radius = radius == null ? 320 : radius;
        const positions = {};
        const sortByName = (a, b) => String(a.hostname || a.id).localeCompare(String(b.hostname || b.id));
        const coreDevices = devices.filter(d => !d._perimeter);
        const perimeterDevices = devices.filter(d => d._perimeter);
        const rrs = coreDevices.filter(d => hints[d.id] === 'rr').sort(sortByName);
        const pes = coreDevices.filter(d => ['pe', 'router', 'leaf', 'core'].includes(hints[d.id])).sort(sortByName);
        const externals = coreDevices.filter(d => ['ce', 'external'].includes(hints[d.id])).sort(sortByName);
        if (rrs.length) {
            const gap = 320;
            const start = centerX - ((rrs.length - 1) * gap) / 2;
            rrs.forEach((d, i) => {
                positions[d.id] = { x: Math.round(start + i * gap), y: topY };
            });
        }
        const spokeY = topY + 250;
        if (pes.length === 1) {
            positions[pes[0].id] = { x: centerX, y: spokeY };
        } else if (pes.length === 2) {
            positions[pes[0].id] = { x: centerX - 240, y: spokeY };
            positions[pes[1].id] = { x: centerX + 240, y: spokeY };
        } else if (pes.length > 2) {
            const span = Math.PI * 0.65;
            const startAng = Math.PI - (Math.PI - span) / 2;
            pes.forEach((d, i) => {
                const ang = startAng - (i * span / Math.max(pes.length - 1, 1));
                positions[d.id] = {
                    x: Math.round(centerX + Math.cos(ang) * radius),
                    y: Math.round(topY + 180 + Math.sin(ang) * radius * 0.55)
                };
            });
        }
        if (externals.length) {
            const extY = spokeY + 220;
            const gap = 240;
            const start = centerX - ((externals.length - 1) * gap) / 2;
            externals.forEach((d, i) => {
                positions[d.id] = { x: Math.round(start + i * gap), y: extY };
            });
        }
        const perByAnchor = new Map();
        perimeterDevices.forEach(d => {
            const anchor = d._anchorDevice;
            if (!anchor) return;
            if (!perByAnchor.has(anchor)) perByAnchor.set(anchor, []);
            perByAnchor.get(anchor).push(d);
        });
        perByAnchor.forEach((arr, anchor) => {
            const base = positions[anchor] || { x: centerX, y: spokeY };
            const direction = Math.abs(base.x - centerX) < 40 ? 0 : (base.x <= centerX ? -1 : 1);
            arr.sort((a, b) => String(a._perimeterKind || '').localeCompare(String(b._perimeterKind || ''))
                || String(a.hostname || a.id).localeCompare(String(b.hostname || b.id)));
            arr.forEach((d, i) => {
                let dx;
                let dy;
                if (d._perimeterKind === 'fabric') {
                    dx = (direction || -1) * 150;
                    dy = -75;
                } else if (d._perimeterKind === 'scale-fan') {
                    dx = (direction || 1) * 280;
                    dy = 190;
                } else {
                    dx = (direction || 1) * 245;
                    dy = Math.round((i - (arr.length - 1) / 2) * 68);
                }
                d.position = d.position || { x: Math.round(base.x + dx), y: Math.round(base.y + dy) };
                positions[d.id] = d.position;
            });
        });
        return positions;
    }

    function calculateArchitecturePositions(facts, learnedHints) {
        const devices = Array.isArray(facts.devices) ? facts.devices : [];
        const family = (learnedHints && learnedHints.layoutFamily) || inferTopologyFamily(facts);
        const hints = (learnedHints && learnedHints.roleHints && Object.keys(learnedHints.roleHints).length)
            ? Object.assign({}, learnedHints.roleHints)
            : synthesizeRoleHints(facts);
        const groups = {};
        devices.forEach(d => {
            const bucket = hints[d.id] || deviceRoleBucket(d);
            if (!groups[bucket]) groups[bucket] = [];
            groups[bucket].push(d);
        });
        Object.values(groups).forEach(arr => arr.sort((a, b) => String(a.hostname).localeCompare(String(b.hostname))));
        const positions = {};
        const placeRow = (arr, y, centerX, gap) => {
            if (!arr || arr.length === 0) return;
            const safeGap = Math.max(gap, arr.length > 4 ? 280 : gap);
            const start = centerX - ((arr.length - 1) * safeGap) / 2;
            arr.forEach((d, idx) => {
                positions[d.id] = { x: Math.round(start + idx * safeGap), y };
            });
        };
        let layoutMode = 'tiered-rows';
        const zones = {
            routing: { x: 260, y: 160, width: 920, height: 390 },
            access: { x: 220, y: 560, width: 1000, height: 190 },
            services: { x: 260, y: 720, width: 920, height: 170 },
            evidence: { x: 90, y: 120, width: 1260, height: 790 }
        };
        const coreCount = devices.filter(d => !d._perimeter).length;
        if (family === 'rr-pe-service' && (groups.rr || []).length >= 1 && coreCount <= 6) {
            const triangle = placeHubSpokeTriangle(devices, hints, 720, 220, 320);
            Object.assign(positions, triangle);
            layoutMode = 'hub-spoke-triangle';
        } else if (family === 'rr-pe-service') {
            placeRow([...(groups.rr || []), ...(groups.core || [])], 220, 720, 260);
            placeRow(groups.pe || [], 430, 720, 360);
            placeRow([...(groups.ce || []), ...(groups.external || [])], 650, 720, 280);
            placeRow(groups.router || [], 650, 720, 260);
        } else if (family === 'clos') {
            placeRow([...(groups.core || []), ...(groups.rr || [])], 220, 720, 240);
            placeRow([...(groups.pe || []), ...(groups.router || [])], 460, 720, 220);
            placeRow([...(groups.ce || []), ...(groups.external || [])], 680, 720, 220);
        } else if (family === 'backbone') {
            placeRow([...(groups.core || []), ...(groups.rr || [])], 300, 720, 250);
            placeRow([...(groups.pe || []), ...(groups.router || [])], 540, 720, 260);
            placeRow([...(groups.ce || []), ...(groups.external || [])], 720, 720, 220);
        } else {
            const sorted = devices.slice().sort((a, b) => String(a.hostname).localeCompare(String(b.hostname)));
            if (sorted.length <= 4) {
                const radius = 230, cx = 720, cy = 430;
                sorted.forEach((d, idx) => {
                    const angle = -Math.PI / 2 + (idx * 2 * Math.PI / Math.max(sorted.length, 1));
                    positions[d.id] = { x: Math.round(cx + Math.cos(angle) * radius), y: Math.round(cy + Math.sin(angle) * radius) };
                });
            } else {
                placeRow([...(groups.rr || []), ...(groups.core || [])], 220, 720, 260);
                placeRow([...(groups.pe || []), ...(groups.router || [])], 460, 720, 240);
                placeRow([...(groups.ce || []), ...(groups.external || [])], 680, 720, 220);
            }
        }
        const unmatched = devices.filter(d => !positions[d.id]);
        placeRow(unmatched, 820, 720, 220);
        return { positions, family, layoutMode, roleHints: hints, zones };
    }

    function createGeneratedScenePlanner(deviceObjs) {
        const labelBoxes = [];
        const deviceBoxes = (deviceObjs || []).map(d => {
            const r = (d.radius || 40) + 22;
            return { x: d.x - r, y: d.y - r, w: r * 2, h: r * 2, kind: 'device' };
        });
        const overlaps = (a, b, pad = 8) => !(
            a.x + a.w + pad < b.x || b.x + b.w + pad < a.x ||
            a.y + a.h + pad < b.y || b.y + b.h + pad < a.y
        );
        const estimateBox = (text, x, y, fontSize) => {
            const lines = String(text || '').split('\n');
            const maxChars = lines.reduce((m, line) => Math.max(m, line.length || 1), 1);
            const w = Math.min(Math.max(maxChars * (fontSize || 9) * 0.62 + 18, 64), 260);
            const h = lines.length * (fontSize || 9) * 1.35 + 14;
            return { x: x - w / 2, y: y - h / 2, w, h };
        };
        const pickLabelPoint = (candidates, text, fontSize) => {
            for (const pt of candidates) {
                const box = estimateBox(text, pt.x, pt.y, fontSize);
                const bad = deviceBoxes.some(d => overlaps(box, d, 10)) || labelBoxes.some(l => overlaps(box, l, 6));
                if (!bad) {
                    labelBoxes.push(box);
                    return { x: Math.round(pt.x), y: Math.round(pt.y), box, collided: false };
                }
            }
            const last = candidates[candidates.length - 1] || { x: 0, y: 0 };
            const box = estimateBox(text, last.x, last.y, fontSize);
            labelBoxes.push(box);
            return { x: Math.round(last.x), y: Math.round(last.y), box, collided: true };
        };
        const reserveBox = (box) => {
            if (box && Number.isFinite(box.x) && Number.isFinite(box.y)) {
                labelBoxes.push(Object.assign({ kind: 'reserved' }, box));
            }
        };
        return { labelBoxes, deviceBoxes, estimateBox, pickLabelPoint, reserveBox };
    }

    function layerLaneWeight(layer, linkType, overlayMode) {
        if (overlayMode === 'via-rr') return 4;
        if (layer === 'physical') return 0;
        if (layer === 'routing' && /bgp/i.test(String(linkType || ''))) return 1;
        if (layer === 'routing') return 2;
        if (layer === 'service') return 3;
        if (layer === 'evidence') return 5;
        return 2;
    }

    function buildLaneCandidates(aObj, bObj, laneIndex, layer) {
        const dx = bObj.x - aObj.x;
        const dy = bObj.y - aObj.y;
        const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
        const midX = (aObj.x + bObj.x) / 2;
        const midY = (aObj.y + bObj.y) / 2;
        const nx = -dy / dist;
        const ny = dx / dist;
        const sign = laneIndex % 2 === 0 ? 1 : -1;
        const magnitude = layer === 'physical'
            ? 22
            : 46 + Math.floor(laneIndex / 2) * 34;
        const baseX = midX + nx * sign * magnitude;
        const baseY = midY + ny * sign * magnitude;
        return [
            { x: baseX, y: baseY },
            { x: midX + nx * sign * (magnitude + 44), y: midY + ny * sign * (magnitude + 44) },
            { x: midX + dx * 0.12 + nx * sign * magnitude, y: midY + dy * 0.12 + ny * sign * magnitude },
            { x: midX - dx * 0.12 + nx * sign * magnitude, y: midY - dy * 0.12 + ny * sign * magnitude },
            { x: baseX + 0, y: baseY + 42 * sign }
        ];
    }

    function buildGenerationSignature(facts) {
        const devices = Array.isArray(facts.devices) ? facts.devices : [];
        const roles = devices.map(d => deviceRoleBucket(d)).sort();
        const asns = Array.from(new Set(devices.map(d => d.config && d.config.asn).filter(Boolean).map(String))).sort();
        const protocols = Array.from(new Set([]
            .concat(facts.links || [], facts.logicalLinks || [])
            .map(l => l.linkType || l.protocol || l.layer || '')
            .filter(Boolean)
            .map(String))).sort();
        const vrfs = Array.from(new Set(devices.flatMap(d => (d.config && d.config.vrfs) || []).map(String))).sort();
        return {
            key: `${roles.join(',')}|${protocols.join(',')}|${asns.join(',')}|${vrfs.join(',')}|${devices.length}`,
            roles, protocols, asns, vrfs, size: devices.length
        };
    }

    function deviceFactsSummary(device) {
        const cfg = device && device.config || {};
        const op = device && device.operational || {};
        const bgpPeers = Array.isArray(cfg.bgp_peers) ? cfg.bgp_peers.length : 0;
        const routeTargets = Array.isArray(cfg.route_targets) ? cfg.route_targets.length : 0;
        const vrfs = Array.isArray(cfg.vrfs) ? cfg.vrfs.length : 0;
        const lldp = Array.isArray(device && device._lldp) ? device._lldp.length : 0;
        const routeProtocols = op.route_summary && op.route_summary.protocols
            ? Object.keys(op.route_summary.protocols).length : 0;
        return { bgpPeers, routeTargets, vrfs, lldp, routeProtocols };
    }

    function inferredRidAliasesFromName(value) {
        const name = String(value || '').trim().toLowerCase();
        const m = /(?:^|[_-])(pe|rr|p|ce)[_-]?(\d+)(?:\b|[_-])/.exec(name);
        if (!m) return [];
        const n = parseInt(m[2], 10);
        if (!n || n < 1 || n > 254) return [];
        return [`${n}.${n}.${n}.${n}`];
    }

    function protocolStackLabel(config) {
        const cfg = config || {};
        const isisArea = (cfg.isis && cfg.isis.area) || cfg.isis_area || '';
        const ospfArea = (cfg.ospf && cfg.ospf.area) || cfg.ospf_area || '';
        const mpls = cfg.mpls || {};
        const base = isisArea ? 'ISIS' : (ospfArea ? 'OSPF' : '');
        if (!base) return null;
        let suffix = '';
        if (mpls.ldp && mpls.sr) suffix = '+LDP+SR';
        else if (mpls.ldp) suffix = '+LDP';
        else if (mpls.sr) suffix = '-SR';
        return {
            label: `${base}${suffix} area ${isisArea || ospfArea}`,
            linkType: `${base}${suffix}`,
            base,
            area: isisArea || ospfArea
        };
    }

    const AF_PALETTE = {
        'ipv4-unicast': { label: 'IPv4', group: 'unicast', color: '#5dade2' },
        'ipv6-unicast': { label: 'IPv6', group: 'unicast', color: '#85c1e9' },
        'ipv4-vpn': { label: 'VPNv4', group: 'vpn', color: '#1abc9c' },
        'ipv6-vpn': { label: 'VPNv6', group: 'vpn', color: '#16a085' },
        'ipv4-flowspec': { label: 'FSv4', group: 'flowspec', color: '#e67e22' },
        'ipv4-flowspec-vpn': { label: 'FS-VPN', group: 'flowspec', color: '#d35400' },
        'ipv6-flowspec': { label: 'FSv6', group: 'flowspec', color: '#f39c12' },
        'l2vpn-vpls': { label: 'VPLS', group: 'vpls', color: '#9b59b6' },
        'l2vpn-evpn': { label: 'EVPN', group: 'evpn', color: '#8e44ad' },
        'ipv4-rt-constrain': { label: 'RTC', group: 'rt-constrain', color: '#f1c40f' }
    };
    const AF_ORDER = Object.keys(AF_PALETTE);

    function normalizeAfTokens(value) {
        if (value == null) return [];
        const raw = Array.isArray(value) ? value : String(value).split(/[,;/|]+/);
        const aliases = {
            'ipv4 unicast': 'ipv4-unicast',
            'ipv4-unicast': 'ipv4-unicast',
            'ipv6 unicast': 'ipv6-unicast',
            'ipv6-unicast': 'ipv6-unicast',
            'ipv4 vpn': 'ipv4-vpn',
            'ipv4-vpn': 'ipv4-vpn',
            vpnv4: 'ipv4-vpn',
            'ipv6 vpn': 'ipv6-vpn',
            'ipv6-vpn': 'ipv6-vpn',
            vpnv6: 'ipv6-vpn',
            'ipv4 flowspec': 'ipv4-flowspec',
            'ipv4-flowspec': 'ipv4-flowspec',
            'ipv4 flowspec-vpn': 'ipv4-flowspec-vpn',
            'ipv4-flowspec-vpn': 'ipv4-flowspec-vpn',
            'ipv6 flowspec': 'ipv6-flowspec',
            'ipv6-flowspec': 'ipv6-flowspec',
            'l2vpn vpls': 'l2vpn-vpls',
            'l2vpn-vpls': 'l2vpn-vpls',
            vpls: 'l2vpn-vpls',
            'l2vpn evpn': 'l2vpn-evpn',
            'l2vpn-evpn': 'l2vpn-evpn',
            evpn: 'l2vpn-evpn',
            'ipv4 route target constrains': 'ipv4-rt-constrain',
            'ipv4 route target constraints': 'ipv4-rt-constrain',
            'ipv4-rt-constrain': 'ipv4-rt-constrain',
            'rt-constrain': 'ipv4-rt-constrain'
        };
        const out = [];
        raw.forEach(item => {
            const key = String(item || '').trim().toLowerCase().replace(/_/g, '-').replace(/\s+/g, ' ');
            const token = aliases[key] || aliases[key.replace(/-/g, ' ')] || aliases[key.replace(/\s+/g, '-')];
            if (token && !out.includes(token)) out.push(token);
        });
        return out.sort((a, b) => (AF_ORDER.indexOf(a) < 0 ? 999 : AF_ORDER.indexOf(a)) - (AF_ORDER.indexOf(b) < 0 ? 999 : AF_ORDER.indexOf(b)));
    }

    function addressFamiliesForDevices(a, b, peerIp) {
        const cfgA = (a && a.config) || {};
        const cfgB = (b && b.config) || {};
        const out = [];
        const add = (value) => normalizeAfTokens(value).forEach(af => { if (!out.includes(af)) out.push(af); });
        const peer = String(peerIp || '').split('/')[0];
        [cfgA, cfgB].forEach(cfg => {
            (cfg.bgp_peers || []).forEach(p => {
                if (peer && String(p.peer || '').split('/')[0] !== peer) return;
                add(p.address_families || p.addressFamilies || p.afi_safi || p.afiSafi || p.families);
            });
        });
        if ((cfgA.evpn && cfgA.evpn.enabled) || (cfgB.evpn && cfgB.evpn.enabled)
            || (cfgA.route_targets || []).length || (cfgB.route_targets || []).length) {
            if (!out.includes('l2vpn-evpn')) out.push('l2vpn-evpn');
        }
        if ((cfgA.vrfs || []).length || (cfgB.vrfs || []).length) {
            if (!out.includes('ipv4-vpn')) out.push('ipv4-vpn');
            if (!out.includes('ipv6-vpn')) out.push('ipv6-vpn');
        }
        return out.sort((a, b) => (AF_ORDER.indexOf(a) < 0 ? 999 : AF_ORDER.indexOf(a)) - (AF_ORDER.indexOf(b) < 0 ? 999 : AF_ORDER.indexOf(b)));
    }

    function buildAfChipsForLink(link) {
        const details = (link && (link.linkDetails || link.extra)) || {};
        return normalizeAfTokens(details.addressFamilies || details.address_families || link.addressFamilies)
            .map((token, idx, arr) => Object.assign({
                token,
                t: arr.length <= 1 ? 0.5 : 0.22 + (idx * (0.56 / Math.max(arr.length - 1, 1)))
            }, AF_PALETTE[token] || { label: token, group: 'other', color: '#95a5a6' }));
    }

    function buildViaRrSplineLinks(facts, roleHints) {
        const devices = Array.isArray(facts && facts.devices) ? facts.devices : [];
        const logical = Array.isArray(facts && facts.logicalLinks) ? facts.logicalLinks : [];
        const byId = new Map(devices.map(d => [d.id, d]));
        const rrIds = devices.filter(d => roleHints[d.id] === 'rr').map(d => d.id);
        const peIds = devices.filter(d => roleHints[d.id] === 'pe').map(d => d.id);
        const bgpLinks = logical.filter(l => /bgp/i.test(String(l.linkType || l.protocol || '')));
        const peersByRr = new Map();
        rrIds.forEach(rr => peersByRr.set(rr, new Set()));
        bgpLinks.forEach(l => {
            rrIds.forEach(rr => {
                if (l.fromDevice === rr && peIds.includes(l.toDevice)) peersByRr.get(rr).add(l.toDevice);
                if (l.toDevice === rr && peIds.includes(l.fromDevice)) peersByRr.get(rr).add(l.fromDevice);
            });
        });
        const direct = new Set(bgpLinks.map(l => [l.fromDevice, l.toDevice].sort().join(':')));
        const out = [];
        peersByRr.forEach((peSet, rr) => {
            const peers = Array.from(peSet).sort((a, b) => String((byId.get(a) || {}).hostname || a).localeCompare(String((byId.get(b) || {}).hostname || b)));
            for (let i = 0; i < peers.length; i++) {
                for (let j = i + 1; j < peers.length; j++) {
                    const a = peers[i];
                    const b = peers[j];
                    if (direct.has([a, b].sort().join(':'))) continue;
                    const afs = [];
                    bgpLinks.filter(l => (l.fromDevice === rr || l.toDevice === rr) && (l.fromDevice === a || l.toDevice === a || l.fromDevice === b || l.toDevice === b))
                        .forEach(l => normalizeAfTokens((l.linkDetails || {}).addressFamilies).forEach(af => { if (!afs.includes(af)) afs.push(af); }));
                    out.push({
                        fromDevice: a,
                        toDevice: b,
                        protocol: `BGP via ${((byId.get(rr) || {}).hostname) || rr}`,
                        linkType: 'BGP-via-RR',
                        layer: 'routing',
                        originType: 'QL',
                        style: { color: '#3498db', style: 'dotted', width: 1.3, opacity: 0.55 },
                        _overlayMode: 'via-rr',
                        _viaRr: rr,
                        linkDetails: {
                            routerIdA: ((byId.get(a) || {}).config || {}).router_id || '',
                            routerIdB: ((byId.get(b) || {}).config || {}).router_id || '',
                            viaRouterId: ((byId.get(rr) || {}).config || {}).router_id || '',
                            addressFamilies: afs
                        }
                    });
                }
            }
        });
        return out;
    }

    function inferUnmatchedReason(device) {
        const s = deviceFactsSummary(device);
        const sshHost = device && device.ssh && (device.ssh.host || device.ssh.hostBackup) || '';
        if (!device || !hasFactSshTarget(device)) return 'No app SSH/SN/active-NCC target';
        if (!device._factsStatus || !device._factsStatus.config) {
            return `No running-config facts from ${sshHost || 'SSH host'}; check credentials/reachability`;
        }
        if (!s.bgpPeers && !s.vrfs && !s.routeTargets && !s.lldp) {
            return 'Config fetched, but no BGP/VRF/RT/LLDP evidence matched';
        }
        return 'Facts collected, but no peer/service relation matched another DUT';
    }

    function summarizeServiceEvidence(service) {
        const lines = [];
        const rawName = String(service.name || service.label || '');
        const upper = rawName.toUpperCase();
        if (service.kind === 'evpn') {
            const modeName = /VPWS|AC_PW|PW/i.test(rawName) ? 'EVPN/VPWS' : (/VPLS/i.test(rawName) ? 'EVPN/VPLS' : 'EVPN');
            lines.push(`${modeName} ${service.name && service.name !== 'EVPN Service' ? service.name : 'Service'}`);
        }
            else if (service.kind === 'vrf') lines.push(`VRF ${service.name}`);
        else if (service.kind === 'bd') lines.push(`BD ${service.name}`);
        else if (service.kind === 'rt') lines.push(`RT ${service.name}`);
        else lines.push(service.label || service.name || 'Service');
        const members = service.memberNames || [];
        if (members.length) {
            lines.push(members.slice(0, 4).join(', ') + (members.length > 4 ? ` +${members.length - 4}` : ''));
        }
        const rts = service.routeTargets || [];
        if (rts.length && service.kind !== 'rt') {
            lines.push('RT ' + rts.slice(0, 3).join(', ') + (rts.length > 3 ? ` +${rts.length - 3}` : ''));
        }
        if (service.rds && typeof service.rds === 'object') {
            const vals = Object.values(service.rds).filter(Boolean);
            if (vals.length) lines.push('RD ' + vals.slice(0, 2).join(', ') + (vals.length > 2 ? ` +${vals.length - 2}` : ''));
        }
        if (service.mode) lines.push(`mode ${service.mode}`);
        const inner = service.inner_vlan || service.innerVlan;
        if (inner) lines.push(`inner ${inner}`);
        if (service.outer_vlan && typeof service.outer_vlan === 'object') {
            const outer = Array.from(new Set(Object.values(service.outer_vlan).filter(Boolean).map(String)));
            if (outer.length) lines.push(`outer ${outer.slice(0, 2).join('/')}`);
        }
        if (service.note) lines.push(service.note);
        return lines.join('\n');
    }

    function composeArchitectureFacts(facts, options) {
        options = options || {};
        const report = {
            includedDevices: [],
            unmatchedDevices: [],
            skippedDevices: [],
            topologyFamily: 'unknown',
            visualProfile: 'balanced-generated-v1',
            score: 100,
            warnings: []
        };
        if (!facts || !Array.isArray(facts.devices)) return facts;
        const originalDevices = facts.devices.slice();
        const skipped = [];
        const kept = [];
        for (const d of originalDevices) {
            if (d && d._perimeter) {
                kept.push(d);
                continue;
            }
            const excluded = isDnaasDeviceName(d.hostname || '') || d._origin === 'dnaas-bd';
            if (excluded) {
                skipped.push({ hostname: d.hostname, reason: 'DNAAS/fabric device excluded from Generate' });
                continue;
            }
            if (!hasFactSshTarget(d)) {
                skipped.push({ hostname: d.hostname, reason: 'No app SSH/SN/active-NCC target' });
                continue;
            }
            kept.push(d);
        }
        facts.devices = kept;
        const keptIds = new Set(kept.map(d => d.id));
        facts.links = (facts.links || []).filter(l => keptIds.has(l.fromDevice) && keptIds.has(l.toDevice));
        facts.physicalLinks = (facts.physicalLinks || []).filter(l => keptIds.has(l.fromDevice) && keptIds.has(l.toDevice));
        const perimLogical = (facts.logicalLinks || []).filter(l => keptIds.has(l.fromDevice) && keptIds.has(l.toDevice) && l.linkType === 'perimeter-evidence');
        const compactableLogical = (facts.logicalLinks || []).filter(l => keptIds.has(l.fromDevice) && keptIds.has(l.toDevice) && l.linkType !== 'perimeter-evidence');
        facts.logicalLinks = compactLogicalLinks(compactableLogical).concat(perimLogical);
        facts.services = Array.isArray(facts.services) ? facts.services : [];
        const devById = new Map(facts.devices.map(d => [d.id, d]));
        const serviceLinkTypes = new Set(['VRF', 'BD', 'EVPN-RT']);
        const routingLogical = [];
        const serviceByKey = new Map();
        for (const l of facts.logicalLinks) {
            if (!serviceLinkTypes.has(l.linkType)) {
                routingLogical.push(l);
                continue;
            }
            const a = devById.get(l.fromDevice);
            const b = devById.get(l.toDevice);
            if (!a || !b) continue;
            const kind = l.linkType === 'EVPN-RT' ? 'evpn' : String(l.linkType || 'service').toLowerCase();
            const name = String(l.protocol || l.bd || l.linkType || 'service').replace(/^(VRF|BD|RT)\s+/i, '');
            const key = kind === 'evpn'
                ? `${kind}:${[a.id, b.id].sort().join('+')}`
                : `${kind}:${name}`;
            if (!serviceByKey.has(key)) {
                serviceByKey.set(key, {
                    id: key,
                    kind,
                    name: kind === 'evpn' ? 'EVPN Service' : name,
                    label: kind === 'evpn' ? 'EVPN Service' : `${kind.toUpperCase()} ${name}`,
                    members: [],
                    memberNames: [],
                    routeTargets: kind === 'evpn' ? [name] : [],
                    color: (l.style && l.style.color) || (kind === 'evpn' ? '#f39c12' : '#1abc9c'),
                    layer: 'service',
                    note: kind === 'evpn' ? 'service with route-target evidence' : 'correlated service'
                });
            } else if (kind === 'evpn') {
                const rtList = serviceByKey.get(key).routeTargets || [];
                if (!rtList.includes(name)) rtList.push(name);
                serviceByKey.get(key).routeTargets = rtList;
            }
            const svc = serviceByKey.get(key);
            [a, b].forEach(d => {
                if (!svc.members.includes(d.id)) {
                    svc.members.push(d.id);
                    svc.memberNames.push(d.hostname || d.id);
                }
            });
        }
        facts.logicalLinks = routingLogical;
        serviceByKey.forEach(svc => {
            if (svc.members.length >= 2) facts.services.push(svc);
        });

        for (const d of facts.devices) {
            const hasAnyLink = [].concat(facts.links || [], facts.logicalLinks || [])
                .some(l => l.fromDevice === d.id || l.toDevice === d.id);
            const name = d.hostname || d.id;
            report.includedDevices.push(name);
            if (!hasAnyLink) {
                d._unmatchedReason = d._unmatchedReason || inferUnmatchedReason(d);
                report.unmatchedDevices.push({ hostname: name, reason: d._unmatchedReason });
            }
        }
        report.skippedDevices = skipped;
        const learnedHints = options.learnedHints || {};
        const placement = calculateArchitecturePositions(facts, learnedHints);
        report.topologyFamily = placement.family;
        report.layoutMode = placement.layoutMode;
        report.roleHints = placement.roleHints || {};
        report.layoutZones = placement.zones || {};
        facts.devices.forEach(d => {
            if (!options.keepPositions && placement.positions[d.id]) {
                d.position = placement.positions[d.id];
            }
            const hint = (placement.roleHints || {})[d.id];
            if (hint && !d.role) d.role = hint;
        });
        // Prefer compact service annotations over many equivalent service curves.
        facts.logicalLinks = facts.logicalLinks.map(l => {
            const style = styleForLinkType(l.linkType, l.layer);
            return Object.assign({}, l, { style: Object.assign({}, style, l.style || {}) });
        });
        facts.links = facts.links.map(l => {
            const style = styleForLinkType('physical', 'physical');
            return Object.assign({}, l, { style: Object.assign({}, style, l.style || {}) });
        });
        facts.groups = (facts.groups || []).filter(g => (g.members || []).filter(id => keptIds.has(id)).length >= 2)
            .map(g => Object.assign({}, g, { members: (g.members || []).filter(id => keptIds.has(id)) }));
        if (report.unmatchedDevices.length >= 2) {
            facts.groups.push({
                id: 'unmatched-duts',
                kind: 'unmatched',
                label: 'Unmatched DUTs',
                members: report.unmatchedDevices.map(x => {
                    const d = facts.devices.find(dev => dev.hostname === x.hostname);
                    return d && d.id;
                }).filter(Boolean),
                color: '#95a5a6'
            });
        }
        report.score -= Math.max(0, (facts.logicalLinks || []).length - facts.devices.length * 3) * 3;
        report.score -= report.unmatchedDevices.length * 5;
        facts.compositionReport = report;
        facts.generationSignature = buildGenerationSignature(facts);
        if (skipped.length) {
            facts.warnings.push(`Generate skipped ${skipped.length} device(s): ${skipped.map(s => `${s.hostname || '?'} (${s.reason})`).join(', ')}`);
        }
        if (report.unmatchedDevices.length) {
            facts.warnings.push(`Generate kept ${report.unmatchedDevices.length} unmatched DUT(s) in the topology.`);
        }
        return facts;
    }

    function roleClassification(name, hostname, sysType) {
        const _e = _editor();
        const ed = (_e && _e.networkMapper) || null;
        if (ed && typeof ed._classifyDevice === 'function') {
            return ed._classifyDevice({
                hostname: hostname || name || '',
                system_type: sysType || ''
            });
        }
        // Fallback if NetworkMapperManager is not loaded yet.
        const lower = (hostname || name || '').toLowerCase();
        if (lower.includes('spine')) return { role: 'spine', tier: 0, color: '#9b59b6', visualStyle: 'server', radius: 50 };
        if (lower.includes('leaf') || lower.includes('ncf')) return { role: 'leaf', tier: 1, color: '#3498db', visualStyle: 'classic', radius: 40 };
        if (lower.includes('rr') || lower.includes('ncc')) return { role: 'rr', tier: 0, color: '#9b59b6', visualStyle: 'classic', radius: 40 };
        if (lower.includes('pe') || lower.includes('p-')) return { role: 'pe', tier: 1, color: '#3498db', visualStyle: 'classic', radius: 40 };
        if (lower.includes('ce')) return { role: 'ce', tier: 2, color: '#2ecc71', visualStyle: 'simple', radius: 30 };
        if (lower.includes('exabgp') || lower.includes('ixia') || lower.includes('tester')) {
            return { role: 'external', tier: 2, color: '#e67e22', visualStyle: 'server', radius: 30 };
        }
        return { role: 'router', tier: 1, color: '#3498db', visualStyle: 'classic', radius: 40 };
    }

    // Layout helper: prefer the network mapper's hybrid layout when it is
    // loaded so the preview lines up with the existing LLDP topology look.
    function layoutDevices(deviceNames, links, classified) {
        const _e = _editor();
        const nm = (_e && _e.networkMapper) || null;
        if (nm && typeof nm._hybridLayout === 'function') {
            const fakeDevices = {};
            deviceNames.forEach(n => { fakeDevices[n] = { hostname: n }; });
            try {
                const pos = nm._hybridLayout(deviceNames, links, fakeDevices, classified);
                if (pos && Object.keys(pos).length === deviceNames.length) return pos;
            } catch (_) {}
        }
        // Tier-based fallback layout.
        const tiers = {};
        deviceNames.forEach(n => {
            const t = (classified[n] && typeof classified[n].tier === 'number') ? classified[n].tier : 1;
            if (!tiers[t]) tiers[t] = [];
            tiers[t].push(n);
        });
        const positions = {};
        const tierKeys = Object.keys(tiers).map(Number).sort();
        const tierY = {};
        tierKeys.forEach((t, i) => { tierY[t] = 250 + i * 280; });
        for (const t of tierKeys) {
            const arr = tiers[t];
            const cx = 600;
            const gap = 220;
            const start = cx - ((arr.length - 1) * gap) / 2;
            arr.forEach((name, i) => {
                positions[name] = { x: Math.round(start + i * gap), y: tierY[t] };
            });
        }
        return positions;
    }

    function shortenInterface(ifName) {
        const _e = _editor();
        const nm = (_e && _e.networkMapper) || null;
        if (nm && typeof nm._shortenInterface === 'function') {
            return nm._shortenInterface(ifName || '');
        }
        return (ifName || '');
    }

    function inferProtocol(link, fromCls, toCls) {
        const _e = _editor();
        const nm = (_e && _e.networkMapper) || null;
        if (nm && typeof nm._inferProtocol === 'function') {
            return nm._inferProtocol(link, fromCls, toCls);
        }
        return 'LLDP';
    }

    function getLinkStyleHints(link) {
        const _e = _editor();
        const nm = (_e && _e.networkMapper) || null;
        if (nm && typeof nm._getLinkStyle === 'function') {
            return nm._getLinkStyle(link, {});
        }
        return { color: '#85c1e9', style: 'solid', width: 2 };
    }

    // ------------------------------------------------------------------ facts

    /**
     * Normalized topology facts model. Every source adapter emits this
     * shape so the generator can render canvas objects without caring
     * which source produced them.
     *
     * facts = {
     *   provenance: { source, collectedAt, durationMs, notes[] },
     *   devices: [{
     *     id, hostname, role, tier,
     *     ip, mgmtIp, serial, system_type, dnos_version,
     *     visualStyle, color, radius,
     *     ssh: { host, hostBackup, user, password } | null,
     *     groups: [{ kind, label }],     // AS / area / VRF / BD / site / rack
     *     config: { asn, isis_area, vrfs: [], bgp: {}, isis: {}, mpls: {} },
     *     monitoring: { uptime, alarms, ... }
     *   }],
     *   links: [{
     *     fromDevice, toDevice, fromInterface, toInterface,
     *     vlan, bd, ipFrom, ipTo,
     *     protocol, linkType, originType ('QL'|'UL'|'BUL'),
     *     style: { color, style, width }
     *   }],
     *   groups: [{ id, kind, label, members:[deviceId,...], color }],
     *   warnings: [string]
     * }
     */
    function blankFacts(source) {
        return {
            provenance: { source: source || 'unknown', collectedAt: new Date().toISOString(), durationMs: 0, notes: [] },
            devices: [],
            links: [],
            // Layered link views: ``physicalLinks`` are LLDP / DNAAS BD
            // adjacency, ``logicalLinks`` are protocol overlays
            // (iBGP / eBGP / VRF / EVPN), ``services`` are higher-level
            // edges (BD memberships, L3VPN endpoints).
            physicalLinks: [],
            logicalLinks: [],
            services: [],
            groups: [],
            warnings: []
        };
    }

    // ----------------------------------------------------------- canvas helper

    function _readCanvas(editor) {
        const out = { devices: [], links: [] };
        const objs = (editor && editor.objects) ? editor.objects : [];
        for (const o of objs) {
            if (!o) continue;
            if (o.type === 'device') {
                out.devices.push({
                    id: o.id,
                    label: o.label || o.name || o.id,
                    name: o.name || o.label || o.id,
                    x: o.x, y: o.y,
                    ip: o.ip || (o.sshConfig && o.sshConfig.host) || '',
                    mgmtIp: (o.sshConfig && o.sshConfig.host) || '',
                    serial: o.deviceSerial || '',
                    sysType: o._lldpData?.system_type || o._systemType || '',
                    dnosVersion: o._lldpData?.dnos_version || '',
                    color: o.color, radius: o.radius, visualStyle: o.visualStyle,
                    ssh: o.sshConfig ? {
                        host: o.sshConfig.host || '',
                        hostBackup: o.sshConfig.hostBackup || '',
                        user: o.sshConfig.user || '',
                        password: o.sshConfig.password || ''
                    } : null
                });
            } else if (o.type === 'link' || o.type === 'unbound') {
                out.links.push({
                    id: o.id,
                    fromDeviceId: o.device1, toDeviceId: o.device2,
                    fromInterface: o.interface1 || '', toInterface: o.interface2 || '',
                    vlan: o.vlan || '', bd: o.bd || '',
                    color: o.color, style: o.style, width: o.width,
                    linkType: o.linkType || '',
                    originType: o.originType || (o.type === 'unbound' ? 'UL' : 'QL')
                });
            }
        }
        return out;
    }

    // -------------------------------------------------------- source adapters

    /**
     * CanvasSourceAdapter -- facts derived from the live in-memory
     * canvas objects without contacting any backend. Used to ENRICH an
     * existing diagram (add labels, role-based colors, grouping shapes,
     * link-table metadata) without rebuilding it.
     */
    function adapterCanvas(editor, opts) {
        const facts = blankFacts('canvas');
        const t0 = Date.now();
        const snap = _readCanvas(editor);
        if (snap.devices.length === 0) {
            facts.warnings.push('No devices on canvas');
            facts.provenance.durationMs = Date.now() - t0;
            return facts;
        }
        const nameToFact = new Map();
        for (const d of snap.devices) {
            const cls = roleClassification(d.name, d.label, d.sysType);
            const fd = {
                id: d.id,
                hostname: d.label,
                role: cls.role, tier: cls.tier,
                ip: d.ip, mgmtIp: d.mgmtIp, serial: d.serial,
                system_type: d.sysType, dnos_version: d.dnosVersion,
                color: d.color || cls.color,
                radius: d.radius || cls.radius,
                visualStyle: d.visualStyle || cls.visualStyle,
                ssh: d.ssh,
                position: { x: d.x, y: d.y },
                groups: [], config: {}, monitoring: {}
            };
            facts.devices.push(fd);
            nameToFact.set(d.id, fd);
        }
        for (const l of snap.links) {
            const a = nameToFact.get(l.fromDeviceId);
            const b = nameToFact.get(l.toDeviceId);
            if (!a || !b) continue;
            const styleHints = getLinkStyleHints({
                from_interface: l.fromInterface, to_interface: l.toInterface
            });
            facts.links.push({
                fromDevice: a.id, toDevice: b.id,
                fromInterface: l.fromInterface, toInterface: l.toInterface,
                vlan: l.vlan, bd: l.bd,
                protocol: inferProtocol(
                    { from_interface: l.fromInterface, to_interface: l.toInterface },
                    { role: a.role }, { role: b.role }
                ),
                linkType: l.linkType, originType: l.originType,
                style: { color: l.color || styleHints.color, style: l.style || styleHints.style, width: l.width || styleHints.width }
            });
        }
        // Tier grouping shapes (when more than one tier on canvas).
        if (opts && opts.includeShapes !== false) {
            const tiers = {};
            for (const d of facts.devices) {
                if (!tiers[d.tier]) tiers[d.tier] = [];
                tiers[d.tier].push(d);
            }
            const tierLabels = { 0: 'Core / Spine', 1: 'Aggregation', 2: 'Edge / Access' };
            const tierKeys = Object.keys(tiers).map(Number).sort();
            if (tierKeys.length > 1) {
                tierKeys.forEach(t => {
                    const members = tiers[t];
                    facts.groups.push({
                        id: `tier-${t}`,
                        kind: 'tier',
                        label: tierLabels[t] || `Tier ${t}`,
                        members: members.map(m => m.id),
                        color: t === 0 ? '#9b59b6' : (t === 1 ? '#3498db' : '#2ecc71')
                    });
                });
            }
        }
        facts.provenance.durationMs = Date.now() - t0;
        facts.provenance.notes.push(`canvas: ${facts.devices.length} devices, ${facts.links.length} links`);
        return facts;
    }

    /**
     * LiveDeviceSourceAdapter -- pulls live context for the operator's
     * DUT targets (manual entries + canvas SSH + selected) and merges
     * the result into a unified facts model. Treats DUT LLDP neighbors
     * as the *physical* topology source (non-DNAAS) and parsed config
     * facts as the *logical* topology source. Falls back gracefully
     * when ``/api/topology-generator/device-facts`` is unavailable for
     * a particular device.
     *
     * ``targets`` is the list returned by ``_collectLiveTargets``. When
     * empty we fall back to canvas-derived SSH targets so legacy users
     * who only had the auto-canvas behavior keep their flow.
     */
    async function adapterLive(editor, opts, log, targets) {
        opts = opts || {};
        const facts = blankFacts('live');
        facts.physicalLinks = [];
        facts.logicalLinks = [];
        facts.services = [];
        const t0 = Date.now();

        // Resolve which devices we're operating on. If the caller didn't
        // pre-resolve, peel them off the canvas.
        if (!Array.isArray(targets) || targets.length === 0) {
            const canvas = adapterCanvas(editor, { includeShapes: false });
            targets = canvas.devices.filter(d => d.ssh && (d.ssh.host || d.ssh.hostBackup))
                .map(d => ({
                    deviceId: d.serial || d.hostname,
                    host: (d.ssh && (d.ssh.host || d.ssh.hostBackup)) || '',
                    label: d.hostname,
                    ssh: d.ssh,
                    canvasId: d.id,
                    source: 'canvas',
                    hostname: d.hostname,
                    role: d.role, tier: d.tier, color: d.color, visualStyle: d.visualStyle, radius: d.radius
                }));
        }
        targets = targets.map(t => enrichTargetFromCanvas(editor, t));

        if (targets.length === 0) {
            facts.warnings.push('No DUT targets supplied. Type names/IPs into the textarea or check "Auto-include canvas devices".');
            facts.provenance.durationMs = Date.now() - t0;
            return facts;
        }

        const originalTargetCount = targets.length;
        targets = targets.filter(t => {
            const source = t && (t.source || '');
            if (!isCanvasLiveSource(source)) return true;
            return !!getTargetSshHost(t);
        });
        if (targets.length !== originalTargetCount) {
            facts.warnings.push(`Skipped ${originalTargetCount - targets.length} canvas/selected target(s) without SSH credentials.`);
        }
        if (targets.length === 0) {
            facts.warnings.push('No SSH-backed DUT targets remain after filtering canvas/selected devices.');
            facts.provenance.durationMs = Date.now() - t0;
            return facts;
        }

        // Prime facts.devices with one entry per target so we always
        // emit something, even when the device-facts API fails for it.
        const factDeviceByKey = new Map();
        let counter = 0;
        for (const t of targets) {
            const targetSshHost = getTargetSshHost(t);
            const name = t.hostname || t.label || t.deviceId || t.host || `dev_${++counter}`;
            const cls = roleClassification(name, name, t.system_type || '');
            const id = `live_${++counter}`;
            const fd = {
                id,
                hostname: name,
                role: t.role || cls.role, tier: cls.tier,
                ip: targetSshHost,
                mgmtIp: targetSshHost,
                serial: t.serial || (typeof t.deviceId === 'string' && /^[A-Z]{2}\d{8}/.test(t.deviceId) ? t.deviceId : ''),
                system_type: t.system_type || '',
                dnos_version: t.dnos_version || '',
                color: cls.color, radius: cls.radius, visualStyle: cls.visualStyle,
                ssh: t.ssh ? Object.assign({}, clonePlain(t.ssh), {
                    host: targetSshHost,
                    hostBackup: t.ssh.hostBackup || '',
                    user: t.ssh.user || 'dnroot',
                    password: t.ssh.password || 'dnroot'
                }) : null,
                groups: [], config: {}, monitoring: {},
                _targetRequest: { deviceId: t.deviceId || name, ssh_host: targetSshHost },
                _canvasId: t.canvasId || null,
                _origin: t.source || 'manual',
                _isGenerateDut: true
            };
            if (t.canvasId && editor && Array.isArray(editor.objects)) {
                const canvasObj = editor.objects.find(o => o && o.id === t.canvasId);
                if (canvasObj && typeof canvasObj.x === 'number' && typeof canvasObj.y === 'number') {
                    fd.position = { x: canvasObj.x, y: canvasObj.y };
                    fd.color = canvasObj.color || fd.color;
                    fd.radius = canvasObj.radius || fd.radius;
                    fd.visualStyle = canvasObj.visualStyle || fd.visualStyle;
                }
            }
            facts.devices.push(fd);
            factDeviceByKey.set((name || '').toLowerCase(), fd);
            if (fd.serial) factDeviceByKey.set(fd.serial.toLowerCase(), fd);
            if (fd.mgmtIp) factDeviceByKey.set(fd.mgmtIp.toLowerCase(), fd);
        }

        // Per-user / per-topology scope (mirrors device context API).
        const active = (window.TopologySync && typeof window.TopologySync.getActive === 'function')
            ? window.TopologySync.getActive() : null;
        const domainId = (active && active.domain_id) ? String(active.domain_id) : '';
        const topologyId = (active && active.topology_id) ? String(active.topology_id) : '';

        log(`Collecting live context for ${facts.devices.length} DUT(s)...`);
        const concurrency = 4;
        let i = 0;
        async function worker() {
            while (i < facts.devices.length) {
                const idx = i++;
                const d = facts.devices[idx];
                const did = (d._targetRequest && d._targetRequest.deviceId) || d.hostname;
                const ssh = (d._targetRequest && d._targetRequest.ssh_host) || (d.ssh && d.ssh.host) || '';
                if (!did) continue;
                if (!ssh) {
                    log(`  - ${d.hostname}: skipped (no SSH host)`);
                    facts.warnings.push(`${d.hostname}: skipped target without SSH host`);
                    continue;
                }
                try {
                    const url = `/api/topology-generator/device-facts?device_id=${encodeURIComponent(did)}`
                        + `&ssh_host=${encodeURIComponent(ssh)}`
                        + `&fetch_config=${opts.fetchConfig ? '1' : '0'}`
                        + `&live=${opts.live ? '1' : '0'}`
                        + (domainId ? `&domain_id=${encodeURIComponent(domainId)}` : '')
                        + (topologyId ? `&topology_id=${encodeURIComponent(topologyId)}` : '');
                    const resp = await _authFetch(url);
                    if (!resp.ok) {
                        log(`  - ${d.hostname}: HTTP ${resp.status}`);
                        facts.warnings.push(`${d.hostname}: device-facts HTTP ${resp.status}`);
                        continue;
                    }
                    const j = await resp.json();
                    if (j && j.context) {
                        d.system_type = j.context.system_type || d.system_type;
                        d.dnos_version = j.context.dnos_version || d.dnos_version;
                        d.mgmtIp = j.context.mgmt_ip || d.mgmtIp;
                        if (j.context.hostname) {
                            const newName = j.context.hostname;
                            if (newName && newName !== d.hostname) {
                                factDeviceByKey.delete((d.hostname || '').toLowerCase());
                                d.hostname = newName;
                                factDeviceByKey.set(newName.toLowerCase(), d);
                            }
                        }
                        if (j.context.role) d.role = j.context.role;
                        if (j.context.as_number) d._asn = j.context.as_number;
                        if (j.context.router_id) d._routerId = j.context.router_id;
                        if (j.context.loopback0_ip) d._loopback0 = j.context.loopback0_ip;
                    }
                    if (j && j.ssh && (j.ssh.host || j.ssh.hostBackup || j.ssh.user || j.ssh.password)) {
                        d.ssh = Object.assign({}, clonePlain(d.ssh || {}), clonePlain(j.ssh), {
                            host: j.ssh.host || d.mgmtIp || ssh || '',
                            hostBackup: j.ssh.hostBackup || (d.ssh && d.ssh.hostBackup) || '',
                            user: j.ssh.user || (d.ssh && d.ssh.user) || 'dnroot',
                            password: j.ssh.password || (d.ssh && d.ssh.password) || 'dnroot'
                        });
                    }
                    if (j && j.config_facts) {
                        d.config = Object.assign({}, d.config, j.config_facts);
                    }
                    if (j && j.operational_facts) {
                        d.operational = Object.assign({}, d.operational || {}, j.operational_facts);
                        const bgpSummary = j.operational_facts.bgp_summary || {};
                        if (Array.isArray(bgpSummary.peers) && bgpSummary.peers.length) {
                            d.config = Object.assign({}, d.config, {
                                bgp_peers: (d.config.bgp_peers || []).concat(bgpSummary.peers.map(p => ({
                                    peer: p.peer,
                                    remote_as: p.remote_as,
                                    state: p.state,
                                    source: 'show bgp summary'
                                })))
                            });
                        }
                    }
                    d._factsStatus = {
                        context: !!(j && j.context),
                        config: !!(j && j.config_facts),
                        operational: !!(j && j.operational_facts),
                        lldp: Array.isArray(j && j.lldp_neighbors) ? j.lldp_neighbors.length : 0,
                        bgpPeers: Array.isArray(d.config && d.config.bgp_peers) ? d.config.bgp_peers.length : 0,
                        vrfs: Array.isArray(d.config && d.config.vrfs) ? d.config.vrfs.length : 0,
                        routeTargets: Array.isArray(d.config && d.config.route_targets) ? d.config.route_targets.length : 0
                    };
                    if (j && Array.isArray(j.lldp_neighbors) && opts.includeLldp !== false) {
                        // Stash LLDP neighbors on the device; we'll
                        // build physical links after all probes finish
                        // so we can wire them across DUTs even when
                        // the worker order is non-deterministic.
                        d._lldp = j.lldp_neighbors;
                    }
                    if (j && Array.isArray(j.warnings)) {
                        for (const w of j.warnings) facts.warnings.push(`${d.hostname}: ${w}`);
                    }
                    log(`  + ${d.hostname}: ${d.system_type || '?'} ${d.dnos_version ? 'v' + d.dnos_version : ''}`);
                } catch (e) {
                    log(`  - ${d.hostname}: ${e.message || e}`);
                    facts.warnings.push(`${d.hostname}: ${e.message || e}`);
                }
            }
        }
        const workers = [];
        for (let w = 0; w < Math.min(concurrency, facts.devices.length); w++) workers.push(worker());
        await Promise.all(workers);

        // Generate output must stay scoped to SSH-backed DUTs. Discovery
        // evidence can mention neighbors, but non-SSH canvas nodes and DNAAS
        // fabric/service devices should not become generated topology nodes.
        const beforePrune = facts.devices.length;
        facts.devices = facts.devices.filter(d => {
            if (!hasFactSshTarget(d)) {
                d._unmatchedReason = 'No app SSH target after resolution';
                return d._isGenerateDut === true;
            }
            return !isCanvasDiscoveryExcludedDevice(editor, {
                label: d.hostname,
                name: d.hostname,
                id: d.id,
                deviceSerial: d.serial,
                sshConfig: d.ssh,
                _isDnaas: d._isDnaas,
                source: d._origin
            });
        });
        if (facts.devices.length !== beforePrune) {
            facts.warnings.push(`Generate skipped ${beforePrune - facts.devices.length} non-SSH or DNAAS/fabric device(s).`);
        }
        factDeviceByKey.clear();
        for (const d of facts.devices) {
            factDeviceByKey.set((d.hostname || '').toLowerCase(), d);
            if (d.serial) factDeviceByKey.set(d.serial.toLowerCase(), d);
            if (d.mgmtIp) factDeviceByKey.set(d.mgmtIp.toLowerCase(), d);
            if (d.ip) factDeviceByKey.set(d.ip.toLowerCase(), d);
        }

        // ---------------- physical links from DUT LLDP -----------------
        if (opts.includeLldp !== false) {
            const linkSeen = new Set();
            for (const d of facts.devices) {
                const neighbors = d._lldp || [];
                for (const n of neighbors) {
                    const peerName = (n.peer_hostname || '').trim();
                    if (!peerName) continue;
                    if (isDnaasDeviceName(peerName) || (editor && typeof editor.isDnaasRouter === 'function' && editor.isDnaasRouter(peerName))) {
                        continue;
                    }
                    let peer = factDeviceByKey.get(peerName.toLowerCase());
                    if (!peer) {
                        // Generate is a DUT topology builder. Unknown LLDP
                        // neighbors often include DNAAS fabric, servers, and
                        // tap devices; keep them as evidence only, not as
                        // generated canvas nodes.
                        continue;
                    }
                    if (!hasFactSshTarget(peer)) continue;
                    if (peer === d) continue;
                    const pairKey = [d.id, peer.id].sort().join('|') + ':' + (n.local_interface || '') + '<->' + (n.peer_interface || '');
                    if (linkSeen.has(pairKey)) continue;
                    linkSeen.add(pairKey);
                    const styleHints = getLinkStyleHints({
                        from_interface: n.local_interface, to_interface: n.peer_interface
                    });
                    const link = {
                        fromDevice: d.id, toDevice: peer.id,
                        fromInterface: n.local_interface || '', toInterface: n.peer_interface || '',
                        vlan: '', bd: '',
                        protocol: 'LLDP',
                        linkType: 'physical-lldp',
                        originType: 'QL',
                        layer: 'physical',
                        style: { color: styleHints.color || '#85c1e9', style: 'solid', width: 2 }
                    };
                    facts.links.push(link);
                    facts.physicalLinks.push(link);
                }
            }
        }

        // ---------------- logical links from BGP/IGP/EVPN --------------
        // Protocol correlation pass:
        //   * index loopbacks/router-ids/interface IPs so BGP neighbors
        //     resolve to real devices, not only hostname matches.
        //   * emit exact BGP session overlays first.
        //   * add bounded IGP/VRF/BD/RT overlays as service layers.
        // This is intentionally deterministic; live session-state can
        // deepen these edges later without changing the canvas model.
        try {
            const byAsn = {}, byVrf = {}, byBd = {}, byRt = {}, byIsis = {}, byOspf = {};
            const logicalSeen = new Set();
            const normalizeIp = (v) => String(v || '').trim().split('/')[0].toLowerCase();
            const addKey = (key, dev) => {
                const k = normalizeIp(key);
                if (k) factDeviceByKey.set(k, dev);
            };
            for (const d of facts.devices) {
                addKey(d._loopback0 || d.config?.loopback0_ip, d);
                addKey(d._routerId || d.config?.router_id, d);
                inferredRidAliasesFromName(d.hostname || d.label || d.name).forEach(alias => addKey(alias, d));
                (d.config?.interfaces || []).forEach(i => addKey(i.ip, d));
                (d.config?.subinterfaces || []).forEach(i => addKey(i.ip, d));
            }
            const pushLogical = (a, b, protocol, linkType, layer, style, meta = {}) => {
                if (!a || !b || a === b) return;
                const key = [a.id, b.id].sort().join('|') + '|' + linkType + '|' + protocol;
                if (logicalSeen.has(key)) return;
                logicalSeen.add(key);
                facts.logicalLinks.push(Object.assign({
                    fromDevice: a.id,
                    toDevice: b.id,
                    fromInterface: meta.fromInterface || '',
                    toInterface: meta.toInterface || '',
                    vlan: meta.vlan || '',
                    bd: meta.bd || '',
                    protocol,
                    linkType,
                    originType: 'QL',
                    layer: layer || 'logical',
                    style
                }, meta.extra || {}));
            };
            const pushService = (kind, name, members, color, extra = {}) => {
                const uniqueMembers = Array.from(new Map((members || [])
                    .filter(Boolean)
                    .map(d => [d.id, d])).values());
                if (uniqueMembers.length < 2) return;
                const serviceId = kind === 'evpn'
                    ? `${kind}:${uniqueMembers.map(d => d.id).sort().join('+')}`
                    : `${kind}:${name}`;
                const routeTargets = Array.from(new Set(uniqueMembers
                    .flatMap(d => (d.config && d.config.route_targets) || [])
                    .filter(Boolean)
                    .map(String)
                    .concat(extra.routeTargets || []))).sort();
                const existing = facts.services.find(s => s && s.id === serviceId);
                if (existing) {
                    existing.routeTargets = Array.from(new Set([].concat(existing.routeTargets || [], routeTargets))).sort();
                    existing.note = extra.note || existing.note;
                    return;
                }
                facts.services.push(Object.assign({
                    id: serviceId,
                    kind,
                    name,
                    label: extra.label || `${kind.toUpperCase()} ${name}`,
                    members: uniqueMembers.map(d => d.id),
                    memberNames: uniqueMembers.map(d => d.hostname || d.id),
                    routeTargets,
                    color,
                    layer: 'service'
                }, extra));
            };
            const connectGroup = (arr, protocol, linkType, layer, style, limit = 8) => {
                if (!arr || arr.length < 2) return;
                const members = arr.slice(0, limit);
                // Dense small groups; larger groups use first member as
                // a stable hub to keep topology readable.
                if (members.length <= 4) {
                    for (let a = 0; a < members.length; a++) {
                        for (let b = a + 1; b < members.length; b++) {
                            pushLogical(members[a], members[b], protocol, linkType, layer, style);
                        }
                    }
                } else {
                    for (let i2 = 1; i2 < members.length; i2++) {
                        pushLogical(members[0], members[i2], protocol, linkType, layer, style);
                    }
                }
            };
            for (const d of facts.devices) {
                const asn = d.config && d.config.asn;
                if (asn) {
                    const k = String(asn);
                    if (!byAsn[k]) byAsn[k] = [];
                    byAsn[k].push(d);
                }
                const vrfs = (d.config && d.config.vrfs) || [];
                for (const v of vrfs) {
                    if (!byVrf[v]) byVrf[v] = [];
                    byVrf[v].push(d);
                }
                const bds = (d.config && d.config.bridge_domains) || [];
                for (const bd of bds) {
                    if (!byBd[bd]) byBd[bd] = [];
                    byBd[bd].push(d);
                }
                const rts = (d.config && d.config.route_targets) || [];
                for (const rt of rts) {
                    if (!byRt[rt]) byRt[rt] = [];
                    byRt[rt].push(d);
                }
                const stack = protocolStackLabel(d.config);
                if (stack && stack.base === 'ISIS') {
                    if (!byIsis[stack.label]) byIsis[stack.label] = [];
                    byIsis[stack.label].push(d);
                }
                if (stack && stack.base === 'OSPF') {
                    if (!byOspf[stack.label]) byOspf[stack.label] = [];
                    byOspf[stack.label].push(d);
                }
            }

            // Exact BGP sessions from explicit neighbor entries.
            for (const d of facts.devices) {
                const peers = (d.config && d.config.bgp_peers) || [];
                for (const p of peers) {
                    if (!p || !p.peer) continue;
                    const peerDev = factDeviceByKey.get(normalizeIp(p.peer))
                        || factDeviceByKey.get(String(p.peer).toLowerCase());
                    if (!peerDev || peerDev === d) continue;
                    const localAs = d.config?.asn;
                    const remoteAs = p.remote_as;
                    const isExternal = !!(remoteAs && localAs && Number(remoteAs) !== Number(localAs));
                    pushLogical(
                        d,
                        peerDev,
                        isExternal ? `eBGP ${localAs || '?'}→${remoteAs}` : `iBGP AS${remoteAs || localAs || '?'}`,
                        isExternal ? 'eBGP' : 'iBGP',
                        'routing',
                        { color: isExternal ? '#e67e22' : '#3498db', style: 'dashed', width: 1.8 },
                        { extra: { peerIp: p.peer, localAs, remoteAs, linkDetails: { addressFamilies: addressFamiliesForDevices(d, peerDev, p.peer) } } }
                    );
                }
            }

            // iBGP overlay per ASN (bounded fallback when configs show
            // the AS but peer sessions did not resolve to known devices).
            Object.keys(byAsn).forEach(asn => {
                connectGroup(byAsn[asn], `iBGP AS${asn}`, 'iBGP', 'routing',
                    { color: '#3498db', style: 'dashed', width: 1.4 }, 6);
            });

            Object.keys(byIsis).forEach(label => {
                connectGroup(byIsis[label], label, label.replace(/\s+area\s+.*$/, ''), 'routing',
                    { color: '#8e44ad', style: 'dotted', width: 1.4 }, 8);
            });
            Object.keys(byOspf).forEach(label => {
                connectGroup(byOspf[label], label, label.replace(/\s+area\s+.*$/, ''), 'routing',
                    { color: '#27ae60', style: 'dotted', width: 1.4 }, 8);
            });
            Object.keys(byVrf).forEach(vrf => {
                pushService('vrf', vrf, byVrf[vrf], '#1abc9c', {
                    note: 'correlated service'
                });
            });
            Object.keys(byBd).forEach(bd => {
                pushService('bd', bd, byBd[bd], '#ff5e1f', {
                    note: 'bridge-domain service'
                });
            });
            Object.keys(byRt).forEach(rt => {
                pushService('evpn', 'EVPN Service', byRt[rt], '#f39c12', {
                    routeTargets: [rt],
                    label: 'EVPN Service',
                    note: 'service with route-target evidence'
                });
            });
            facts.logicalLinks = compactLogicalLinks(facts.logicalLinks);
        } catch (e) {
            facts.warnings.push('logical-link extraction failed: ' + (e.message || e));
        }

        // ---------------- grouping shapes (AS / VRF / BD) -------------
        if (opts.includeShapes) {
            const byAsn = {};
            for (const d of facts.devices) {
                const asn = d.config && d.config.asn;
                if (asn) {
                    const k = `AS${asn}`;
                    if (!byAsn[k]) byAsn[k] = [];
                    byAsn[k].push(d.id);
                }
            }
            Object.keys(byAsn).forEach(label => {
                if (byAsn[label].length >= 2) {
                    facts.groups.push({
                        id: `as-${label}`, kind: 'as', label, members: byAsn[label], color: '#9b59b6'
                    });
                }
            });
        }
        facts.provenance.durationMs = Date.now() - t0;
        facts.provenance.notes.push(
            `live: ${facts.devices.length} devices, ${facts.physicalLinks.length} physical, ${facts.logicalLinks.length} logical`
        );
        return facts;
    }

    /**
     * DnaasSourceAdapter -- builds facts from the latest DNAAS discovery
     * loaded in window.DnaasManager / topology-dnaas.js. Bridge domains
     * become labelled grouping shapes; per-link VLAN/BD metadata feeds
     * the link-table.
     */
    function adapterDnaas(editor, opts) {
        const facts = blankFacts('dnaas');
        facts.physicalLinks = [];
        facts.logicalLinks = [];
        facts.services = [];
        const t0 = Date.now();
        const dnaas = window.DnaasManager || window.dnaasManager || (editor && editor.dnaasManager);
        const data = dnaas && (dnaas.lastResult || dnaas._lastResult || dnaas.data) || null;
        if (!data || !data.devices) {
            facts.warnings.push('No DNAAS discovery loaded. Run a DNAAS discovery first.');
            facts.provenance.durationMs = Date.now() - t0;
            return facts;
        }
        const dlist = Array.isArray(data.devices) ? data.devices : Object.values(data.devices || {});
        const idByName = new Map();
        let counter = 0;
        for (const d of dlist) {
            const name = d.hostname || d.name || `dev_${++counter}`;
            const cls = roleClassification(name, d.hostname, d.system_type);
            const fd = {
                id: `gen_${++counter}`,
                hostname: name,
                role: cls.role, tier: cls.tier,
                ip: d.mgmt_ip || d.ip || '',
                mgmtIp: d.mgmt_ip || d.ip || '',
                serial: d.serial || '',
                system_type: d.system_type || '',
                dnos_version: d.dnos_version || '',
                color: cls.color, radius: cls.radius, visualStyle: cls.visualStyle,
                ssh: null,
                groups: [], config: {}, monitoring: {}
            };
            facts.devices.push(fd);
            idByName.set(name.toLowerCase(), fd);
        }
        const links = Array.isArray(data.links) ? data.links : [];
        for (const l of links) {
            const a = idByName.get((l.from_device || l.from || '').toLowerCase());
            const b = idByName.get((l.to_device || l.to || '').toLowerCase());
            if (!a || !b || a === b) continue;
            const styleHints = getLinkStyleHints({
                from_interface: l.from_interface || '', to_interface: l.to_interface || ''
            });
            const link = {
                fromDevice: a.id, toDevice: b.id,
                fromInterface: l.from_interface || '', toInterface: l.to_interface || '',
                vlan: l.vlan || '', bd: l.bridge_domain || l.bd || '',
                protocol: l.bridge_domain ? `BD ${l.bridge_domain}` : 'L2',
                linkType: 'physical-dnaas',
                originType: 'QL',
                layer: 'physical',
                style: { color: '#ff5e1f', style: styleHints.style || 'solid', width: 2 }
            };
            facts.links.push(link);
            facts.physicalLinks.push(link);
        }
        const bds = Array.isArray(data.bridge_domains) ? data.bridge_domains : (data.bridge_domains ? Object.values(data.bridge_domains) : []);
        if (opts && opts.bdShapes !== false) {
            for (const bd of bds) {
                const memberNames = (bd.devices || bd.members || []).map(s => (s || '').toLowerCase());
                const members = memberNames
                    .map(n => idByName.get(n))
                    .filter(Boolean)
                    .map(d => d.id);
                if (members.length >= 2) {
                    facts.groups.push({
                        id: `bd-${bd.name || bd.id || members.length}`,
                        kind: 'bd',
                        label: `BD ${bd.name || bd.vlan || ''}`.trim(),
                        members,
                        color: '#ff5e1f'
                    });
                }
            }
        }
        facts.provenance.durationMs = Date.now() - t0;
        facts.provenance.notes.push(`dnaas: ${facts.devices.length} devices, ${facts.links.length} links, ${bds.length} BDs`);
        return facts;
    }

    /**
     * MapperSourceAdapter -- consumes the existing Network Mapper's last
     * discovery payload (already produced by NetworkMapperManager) and
     * normalizes it into facts. Used so the LLDP tab can also pass
     * through the unified preview/apply flow when the user hits
     * "Generate Topology" after a discovery run.
     */
    function adapterMapper(editor, opts) {
        const facts = blankFacts('mapper');
        const t0 = Date.now();
        const nm = (editor && editor.networkMapper) || null;
        const data = nm && nm._lastDiscoveryData;
        if (!data || !data.devices) {
            facts.warnings.push('No LLDP discovery data yet. Use "Map All" or "Start Discovery" first.');
            facts.provenance.durationMs = Date.now() - t0;
            return facts;
        }
        const devices = data.devices;
        const links = data.links || [];
        const idByName = new Map();
        let i = 0;
        for (const name of Object.keys(devices)) {
            const d = devices[name];
            const cls = roleClassification(name, d.hostname, d.system_type);
            const fd = {
                id: `gen_${++i}`,
                hostname: d.hostname || name,
                role: cls.role, tier: cls.tier,
                ip: d.mgmt_ip || '', mgmtIp: d.mgmt_ip || '',
                serial: d.serial || '',
                system_type: d.system_type || '', dnos_version: d.dnos_version || '',
                color: cls.color, radius: cls.radius, visualStyle: cls.visualStyle,
                ssh: (d.mgmt_ip || d.serial) ? {
                    host: d.mgmt_ip || '',
                    hostBackup: d.serial || d.hostname || '',
                    user: 'dnroot', password: 'dnroot'
                } : null,
                groups: [], config: {}, monitoring: {}
            };
            facts.devices.push(fd);
            idByName.set(name.toLowerCase(), fd);
            if (d.hostname) idByName.set(String(d.hostname).toLowerCase(), fd);
        }
        for (const l of links) {
            const a = idByName.get((l.from_device || '').toLowerCase());
            const b = idByName.get((l.to_device || '').toLowerCase());
            if (!a || !b || a === b) continue;
            const styleHints = getLinkStyleHints(l);
            facts.links.push({
                fromDevice: a.id, toDevice: b.id,
                fromInterface: l.from_interface || '', toInterface: l.to_interface || '',
                vlan: '', bd: '',
                protocol: inferProtocol(l, { role: a.role }, { role: b.role }),
                linkType: '', originType: 'QL',
                style: { color: styleHints.color, style: styleHints.style, width: styleHints.width }
            });
        }
        facts.provenance.durationMs = Date.now() - t0;
        facts.provenance.notes.push(`mapper: ${facts.devices.length} devices, ${facts.links.length} links`);
        return facts;
    }

    /**
     * ImportSourceAdapter -- accepts (a) a saved topology JSON file,
     * (b) a Network Mapper export JSON, or (c) a pasted DNOS
     * running-config snapshot, and turns it into facts.
     */
    function adapterImport(payload) {
        const facts = blankFacts('import');
        const t0 = Date.now();
        if (!payload || (!payload.text && !payload.json)) {
            facts.warnings.push('Pick a file or paste content first.');
            facts.provenance.durationMs = Date.now() - t0;
            return facts;
        }
        let data = payload.json;
        if (!data && payload.text) {
            const txt = payload.text.trim();
            if (txt.startsWith('{') || txt.startsWith('[')) {
                try { data = JSON.parse(txt); } catch (e) { facts.warnings.push('Invalid JSON: ' + e.message); }
            }
        }
        // Topology JSON shape ({ objects: [...] }).
        if (data && Array.isArray(data.objects)) {
            const idByOld = new Map();
            let i = 0;
            for (const o of data.objects) {
                if (o && o.type === 'device') {
                    const cls = roleClassification(o.label, o.label, o._systemType);
                    const fd = {
                        id: `gen_${++i}`,
                        hostname: o.label || `dev${i}`,
                        role: o.role || cls.role,
                        tier: cls.tier,
                        ip: o.ip || '', mgmtIp: (o.sshConfig && o.sshConfig.host) || '',
                        serial: o.deviceSerial || '',
                        system_type: o._systemType || '', dnos_version: o._dnosVersion || '',
                        color: o.color || cls.color, radius: o.radius || cls.radius,
                        visualStyle: o.visualStyle || cls.visualStyle,
                        ssh: o.sshConfig || null,
                        groups: [], config: {}, monitoring: {}
                    };
                    facts.devices.push(fd);
                    idByOld.set(o.id, fd);
                }
            }
            for (const o of data.objects) {
                if (o && (o.type === 'link' || o.type === 'unbound')) {
                    const a = idByOld.get(o.device1);
                    const b = idByOld.get(o.device2);
                    if (!a || !b) continue;
                    facts.links.push({
                        fromDevice: a.id, toDevice: b.id,
                        fromInterface: o.interface1 || '', toInterface: o.interface2 || '',
                        vlan: o.vlan || '', bd: o.bd || '',
                        protocol: o.linkType || 'imported', linkType: o.linkType || '',
                        originType: o.originType || (o.type === 'unbound' ? 'UL' : 'QL'),
                        style: { color: o.color || '#85c1e9', style: o.style || 'solid', width: o.width || 2 }
                    });
                }
            }
        } else if (data && data.devices) {
            if (data.bridge_domains || data.dnaas || data.source === 'dnaas') {
                facts.warnings.push('DNAAS discovery exports are handled by the DNAAS panel, not Generate.');
                facts.provenance.durationMs = Date.now() - t0;
                return facts;
            }
            // Network Mapper-style export -- delegate to mapper-shape
            // by faking nm._lastDiscoveryData.
            const fakeNm = { _lastDiscoveryData: data };
            const tmp = adapterMapper({ networkMapper: fakeNm }, {});
            tmp.provenance.source = 'import';
            tmp.provenance.notes.push('parsed as discovery JSON');
            return tmp;
        } else if (payload.text) {
            // Best-effort running-config parse: pull hostname + interfaces.
            const hostMatch = /^\s*(?:hostname|system\s+name)\s+([\w.-]+)/im.exec(payload.text);
            const hostname = hostMatch ? hostMatch[1] : 'imported-device';
            const cls = roleClassification(hostname, hostname, '');
            const fd = {
                id: 'gen_1', hostname, role: cls.role, tier: cls.tier,
                ip: '', mgmtIp: '', serial: '',
                system_type: '', dnos_version: '',
                color: cls.color, radius: cls.radius, visualStyle: cls.visualStyle,
                ssh: null, groups: [], config: {}, monitoring: {}
            };
            facts.devices.push(fd);
            facts.warnings.push('Parsed running-config as a single device. Paste discovery JSON for multi-device imports.');
        }
        facts.provenance.durationMs = Date.now() - t0;
        facts.provenance.notes.push(`import: ${facts.devices.length} devices, ${facts.links.length} links`);
        return facts;
    }

    // -------------------------------------------------------- canvas generator

    /**
     * Turn normalized facts into a canvas-ready topology payload that
     * window.editor.loadTopologyFromData() understands. Emits devices,
     * links, text labels, AND grouping shapes. Includes link-table
     * metadata (interfaces, IPs, VLAN, BD) on each link object so the
     * built-in link-table popup picks it up.
     */
    function buildCanvasPayload(facts, options) {
        options = options || {};
        const objects = [];
        const meta = {};

        // Layout: pick coordinates per device unless fact already has them.
        const deviceNames = facts.devices.map(d => d.hostname);
        const linksForLayout = facts.links.map(L => {
            const fa = facts.devices.find(x => x.id === L.fromDevice);
            const fb = facts.devices.find(x => x.id === L.toDevice);
            return { from_device: fa ? fa.hostname : '', to_device: fb ? fb.hostname : '' };
        });
        const classified = {};
        facts.devices.forEach(d => {
            classified[d.hostname] = { role: d.role, tier: d.tier, color: d.color, visualStyle: d.visualStyle, radius: d.radius };
        });
        const positions = layoutDevices(deviceNames, linksForLayout, classified);

        // Translate facts -> canvas object IDs while remembering mapping.
        const realIdByFactId = new Map();
        let dCounter = 0, lCounter = 0, tCounter = 0, sCounter = 0;
        const deviceObjs = [];
        for (const d of facts.devices) {
            const pos = (d.position && typeof d.position.x === 'number' && typeof d.position.y === 'number')
                ? { x: d.position.x, y: d.position.y }
                : (positions[d.hostname] || { x: 600, y: 400 });
            const realId = `device_${dCounter++}`;
            realIdByFactId.set(d.id, realId);
            const dev = applyGeneratedSceneMeta({
                type: 'device',
                id: realId,
                deviceType: 'router',
                x: pos.x, y: pos.y,
                radius: d.radius || 40,
                rotation: 0,
                color: d.color || '#3498db',
                label: d.hostname,
                locked: false,
                visualStyle: d.visualStyle || 'classic',
                role: d.role || 'router',
                _generatedProtocol: 'device',
                _generatedGroupIds: ['layer:devices']
            }, {
                layer: 'device',
                confidence: generatedConfidenceFromFact(d, d._perimeter ? 'inferred' : 'verified'),
                source: generatedSourceFromFact(d, d._perimeter ? 'perimeter-evidence' : 'device-facts'),
                evidence: generatedEvidenceSummary(d),
                displayPriority: 100
            });
            if (d._perimeter) {
                dev.radius = d.radius || 24;
                dev.color = d.color || '#94a3b8';
                dev.opacity = 0.55;
                dev.visualStyle = 'simple';
                dev.nodeStyle = 'muted';
                dev._perimeter = true;
                dev._perimeterKind = d._perimeterKind || 'cpe';
                dev._anchorDevice = d._anchorDevice || '';
                dev._perimeterTooltip = (d._evidence || []).map(row => {
                    if (row.peers) return `${row.source || 'evidence'}: ${row.peers.join(', ')}`;
                    if (row.peer_subnet) return `${row.peer_subnet} x${row.count || '?'} AS${row.remote_as || '?'}`;
                    return [row.source, row.peer || row.representative || ''].filter(Boolean).join(': ');
                }).filter(Boolean).join('\n');
                dev._generatedLayer = 'evidence';
                dev._generatedProtocol = `perimeter:${dev._perimeterKind}`;
                dev._generatedGroupIds = ['layer:evidence', `perimeter:${dev._perimeterKind}`];
                dev._generatedConfidence = generatedConfidenceFromFact(d, 'inferred');
                dev._generatedSource = generatedSourceFromFact(d, 'perimeter-evidence');
                dev._hidden = true;
            }
            if (d.ip) dev.ip = d.ip;
            if (d.serial) dev.deviceSerial = d.serial;
            if (!d._perimeter && d.ssh && (d.ssh.host || d.ssh.hostBackup)) {
                // Verified cluster/SN preservation: if the canvas already had
                // this DUT with app-verified SSH metadata, copy the full
                // sshConfig forward. PE/CL devices often SSH through an active
                // NCC or virsh target; reducing them to host/user/password
                // makes the regenerated device look unverified/non-cluster.
                let _existingVerified = null;
                try {
                    const ed = _editor();
                    const existing = (ed && Array.isArray(ed.objects)) ? ed.objects : [];
                    const wantHost = String(d.hostname || '').toLowerCase();
                    const wantSerial = String(d.serial || '').toLowerCase();
                    const wantCanvasId = String(d._canvasId || '').toLowerCase();
                    for (const obj of existing) {
                        if (!obj || obj.type !== 'device' || !obj.sshConfig) continue;
                        const ssh = obj.sshConfig || {};
                        const verified = !!(
                            ssh._snVerified
                            || ssh._activeNccHost
                            || ssh._activeNccIp
                            || (ssh._virshInfo && ssh._virshInfo.activeNcc)
                            || ssh._verifiedAt
                        );
                        if (!verified) continue;
                        const lbl = String(obj.label || '').toLowerCase();
                        const ser = String(obj.deviceSerial || '').toLowerCase();
                        const oid = String(obj.id || '').toLowerCase();
                        if ((wantCanvasId && oid === wantCanvasId) || (wantHost && lbl === wantHost) || (wantSerial && ser === wantSerial)) {
                            _existingVerified = obj;
                            break;
                        }
                    }
                } catch (_) { _existingVerified = null; }

                if (_existingVerified && _existingVerified.sshConfig) {
                    dev.sshConfig = clonePlain(_existingVerified.sshConfig);
                    console.log(`[Generator] preserving verified cluster sshConfig for ${d.hostname} (activeNcc=${dev.sshConfig._activeNccHost || dev.sshConfig._activeNccIp || ''})`);
                } else {
                    dev.sshConfig = Object.assign({}, clonePlain(d.ssh), {
                        host: d.ssh.host || '',
                        hostBackup: d.ssh.hostBackup || '',
                        user: d.ssh.user || 'dnroot',
                        password: d.ssh.password || 'dnroot'
                    });
                }
                if (dev.sshConfig && (dev.sshConfig._activeNccHost || dev.sshConfig._activeNccIp || dev.sshConfig._virshInfo)) {
                    dev.subType = dev.subType || 'cluster';
                    dev._clusterVerified = true;
                }
            }
            objects.push(dev);
            deviceObjs.push(dev);
        }
        const scenePlanner = createGeneratedScenePlanner(deviceObjs);

        // Merge physical (DUT LLDP, DNAAS BD) and logical (iBGP/eBGP/
        // VRF/EVPN) links into a single rendering pass while keeping
        // their style hints distinct. ``facts.links`` already contains
        // the physical adjacency as the source-of-truth for the
        // adapter; ``facts.logicalLinks`` is appended afterwards so
        // overlays don't clobber physical interface names in the
        // link-table popup.
        const roleHintsForPayload = (facts.compositionReport && facts.compositionReport.roleHints) || synthesizeRoleHints(facts);
        const viaRrLinks = buildViaRrSplineLinks(facts, roleHintsForPayload);
        const allLinks = [].concat(
            Array.isArray(facts.links) ? facts.links : [],
            Array.isArray(facts.logicalLinks) ? facts.logicalLinks : [],
            viaRrLinks
        );

        // Links with link-table fields.
        const linkObjs = [];
        const linkPairSeen = new Set();
        const laneOrdinalByPair = new Map();
        const generatedProtocolGroups = new Map();
        const cleanGroupPart = (value) => String(value || 'unknown')
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '') || 'unknown';
        // Map a raw protocol token (e.g. "bgp", "ospf", "isis", "ldp",
        // "sr-mpls", "rsvp-te", "static", "lldp") to a top-level family
        // bucket so the side panel can render a clean Protocols tree
        // instead of one flat list. Families:
        //   bgp     -> BGP (parent of all AFI/SAFI sub-rows)
        //   igp     -> OSPF, ISIS, BGP-LS-IGP-bridge candidates
        //   mpls    -> LDP, SR-MPLS, RSVP-TE, label-switching evidence
        //   static  -> static routes / connected
        //   service -> generic logical
        //   physical-> LLDP, ethernet
        //   identity-> RID/AS markers
        //   other   -> anything else
        const protocolFamilyOf = (rawId, rawLabel, rawLayer) => {
            const norm = String(rawId || rawLabel || '').toLowerCase();
            if (/^protocol:af-/.test(norm)) return 'bgp';
            if (/(^|[^a-z])bgp([^a-z]|$)/.test(norm)) return 'bgp';
            if (/(ospf|isis|is-is|igp\b)/.test(norm)) return 'igp';
            if (/(ldp|sr-?mpls|sr\b|rsvp-?te|mpls)/.test(norm)) return 'mpls';
            if (/static|connected|direct/.test(norm)) return 'static';
            if (/(lldp|ethernet|physical)/.test(norm)) return 'physical';
            if (/(rid|router-id|as[-_ ]?number|identity)/.test(norm)) return 'identity';
            if (rawLayer === 'service') return 'service';
            return 'other';
        };
        const ensureGeneratedGroup = (id, label, kind, color, layer, extra) => {
            if (!generatedProtocolGroups.has(id)) {
                const entry = {
                    id,
                    label,
                    kind,
                    color: color || '#85c1e9',
                    layer: layer || ''
                };
                // Family + parent metadata for the panel tree. AF chips
                // declare their parent protocol explicitly via `extra`,
                // bare protocol groups derive it from the id/label.
                if (kind === 'af') {
                    entry.family = 'bgp';
                    entry.parentId = (extra && extra.parentId) || 'protocol:bgp';
                    entry.afToken = (extra && extra.afToken) || null;
                    entry.afGroup = (extra && extra.afGroup) || null;
                } else if (kind === 'protocol') {
                    entry.family = protocolFamilyOf(id, label, layer);
                }
                if (extra && extra.protocolToken) entry.protocolToken = extra.protocolToken;
                generatedProtocolGroups.set(id, entry);
            }
            return id;
        };
        const getGeneratedLinkGroups = (fact, layer, style) => {
            const ids = [];
            const groupLayer = layer || 'physical';
            ids.push(ensureGeneratedGroup(
                `layer:${cleanGroupPart(groupLayer)}`,
                groupLayer.charAt(0).toUpperCase() + groupLayer.slice(1),
                'layer',
                style.color,
                groupLayer
            ));
            if (groupLayer === 'physical') {
                ids.push(ensureGeneratedGroup('layer:underlay', 'Underlay', 'layer', style.color, 'underlay'));
            }
            if (groupLayer === 'routing') {
                ids.push(ensureGeneratedGroup('layer:overlay', 'Overlay', 'layer', style.color, 'overlay'));
            }
            if (groupLayer === 'evidence') {
                ids.push(ensureGeneratedGroup('layer:evidence', 'Evidence', 'layer', style.color, 'evidence'));
            }
            const protocolName = fact.linkType || fact.protocol || (groupLayer === 'physical' ? 'LLDP' : 'logical');
            ids.push(ensureGeneratedGroup(
                `protocol:${cleanGroupPart(protocolName)}`,
                protocolName,
                'protocol',
                style.color,
                groupLayer
            ));
            if (fact.bd) {
                ids.push(ensureGeneratedGroup(
                    `bd:${cleanGroupPart(fact.bd)}`,
                    `BD ${fact.bd}`,
                    'service',
                    style.color,
                    'service'
                ));
            }
            if (fact._perimeterKind) {
                ids.push(ensureGeneratedGroup(
                    `perimeter:${cleanGroupPart(fact._perimeterKind)}`,
                    `Perimeter ${fact._perimeterKind}`,
                    'perimeter',
                    style.color,
                    'evidence'
                ));
            }
            return Array.from(new Set(ids));
        };
        ensureGeneratedGroup('layer:devices', 'Devices', 'layer', '#3498db', 'device');
        ensureGeneratedGroup('layer:labels', 'Labels', 'layer', '#aeb6bf', 'label');
        ensureGeneratedGroup('layer:routing', 'Routing', 'layer', '#3498db', 'routing');
        ensureGeneratedGroup('layer:service', 'Service', 'layer', '#1abc9c', 'service');
        ensureGeneratedGroup('layer:services', 'Services', 'layer', '#1abc9c', 'service');
        ensureGeneratedGroup('layer:physical', 'Physical', 'layer', '#5dade2', 'physical');
        ensureGeneratedGroup('layer:underlay', 'Underlay', 'layer', '#5dade2', 'underlay');
        ensureGeneratedGroup('layer:overlay', 'Overlay', 'layer', '#3498db', 'overlay');
        ensureGeneratedGroup('layer:identity', 'Identity', 'layer', '#9b59b6', 'identity');
        ensureGeneratedGroup('layer:evidence', 'Evidence', 'layer', '#f1c40f', 'evidence');
        // Pre-seed an explicit parent BGP group so AF rows always have a
        // home in the side panel, even on topologies that don't carry a
        // bare BGP edge (e.g. RR-only collapsed view).
        ensureGeneratedGroup('protocol:bgp', 'BGP', 'protocol', '#3498db', 'routing');
        Object.entries(AF_PALETTE).forEach(([token, af]) => {
            // One AF row per AF_PALETTE *family* (unicast, vpn, flowspec,
            // vpls, evpn, rt-constrain) -- multiple AFI/SAFIs share the
            // same family bucket and color (matches the existing
            // generator behaviour). We attach the AF token list so the
            // panel can show fine-grained chips under each family.
            ensureGeneratedGroup(
                `protocol:af-${af.group}`,
                `AF ${af.group}`,
                'af',
                af.color,
                'overlay',
                { parentId: 'protocol:bgp', afToken: token, afGroup: af.group }
            );
        });
        ensureGeneratedGroup(
            'protocol:af-other',
            'AF other',
            'af',
            '#94a3b8',
            'overlay',
            { parentId: 'protocol:bgp', afGroup: 'other' }
        );
        ['fabric', 'cpe', 'tester', 'foreign-igp', 'scale-fan'].forEach(kind => {
            ensureGeneratedGroup(`perimeter:${kind}`, `Perimeter ${kind}`, 'perimeter', '#94a3b8', 'evidence');
        });
        for (const L of allLinks) {
            const aId = realIdByFactId.get(L.fromDevice);
            const bId = realIdByFactId.get(L.toDevice);
            if (!aId || !bId || aId === bId) continue;
            const layer = L.layer || 'physical';
            const linkType = L.linkType || '';
            const pairBase = [aId, bId].sort().join(':');
            const pairKey = pairBase
                + '|' + layer
                + '|' + linkType
                + '|' + (L.protocol || '')
                + '|' + (L.fromInterface || '') + ':' + (L.toInterface || '');
            if (linkPairSeen.has(pairKey)) continue;
            linkPairSeen.add(pairKey);
            const aObj = deviceObjs.find(x => x.id === aId);
            const bObj = deviceObjs.find(x => x.id === bId);
            const style = L.style || { color: '#85c1e9', style: 'solid', width: 2 };
            const generatedGroupIds = getGeneratedLinkGroups(L, layer, style);
            const ld = L.linkDetails || {};
            const lt = L.linkTable || {};
            const fromInterface = L.fromInterface || lt.device1Interface || ld.interfaceA || ld.physicalInterfaceA || '';
            const toInterface = L.toInterface || lt.device2Interface || ld.interfaceB || ld.physicalInterfaceB || '';
            const ipA = lt.device1IpAddress || ld.ipAddressA || '';
            const ipB = lt.device2IpAddress || ld.ipAddressB || '';
            const vlanA = lt.device1VlanId || ld.vlanIdA || '';
            const vlanB = lt.device2VlanId || ld.vlanIdB || '';
            const isUL = (L.originType === 'UL');
            const dx = bObj.x - aObj.x;
            const dy = bObj.y - aObj.y;
            const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
            const midX = (aObj.x + bObj.x) / 2;
            const midY = (aObj.y + bObj.y) / 2;
            const laneKey = pairBase + '|' + layer;
            const laneBase = laneOrdinalByPair.get(laneKey) || 0;
            const laneWeight = layerLaneWeight(layer, L.linkType || L.protocol, L._overlayMode);
            const laneIndex = laneBase + laneWeight;
            laneOrdinalByPair.set(laneKey, laneBase + 1);
            let labelX = midX;
            let labelY = midY;
            if (layer !== 'physical') {
                const candidates = buildLaneCandidates(aObj, bObj, laneIndex, layer);
                if (L._viaRr) {
                    const rrId = realIdByFactId.get(L._viaRr);
                    const rrObj = deviceObjs.find(x => x.id === rrId);
                    if (rrObj) {
                        candidates.unshift({ x: rrObj.x, y: rrObj.y + 82 });
                    }
                }
                const chosen = scenePlanner.pickLabelPoint(candidates, L.protocol || L.linkType || 'overlay', layer === 'service' ? 9 : 8);
                labelX = chosen.x;
                labelY = chosen.y;
            }
            const afChips = buildAfChipsForLink(Object.assign({}, L, { linkDetails: ld }));
            afChips.forEach(af => {
                generatedGroupIds.push(ensureGeneratedGroup(`protocol:af-${af.group}`, `AF ${af.group}`, 'af', af.color, 'overlay'));
            });
            const link = {
                type: isUL ? 'unbound' : 'link',
                id: `link_${lCounter++}`,
                originType: L.originType || 'QL',
                device1: aId,
                device2: bId,
                start: { x: aObj.x, y: aObj.y },
                end:   { x: bObj.x, y: bObj.y },
                color: style.color,
                style: style.style,
                width: style.width,
                interface1: fromInterface,
                interface2: toInterface,
                device1Interface: fromInterface,
                device2Interface: toInterface,
                device1IpAddress: ipA,
                device2IpAddress: ipB,
                device1VlanId: vlanA,
                device2VlanId: vlanB,
                device1OuterTag: lt.device1OuterTag || ld.vlanIdA || '',
                device2OuterTag: lt.device2OuterTag || ld.vlanIdB || '',
                device1InnerTag: lt.device1InnerTag || ld.innerVlanA || '',
                device2InnerTag: lt.device2InnerTag || ld.innerVlanB || '',
                _generatedGroupIds: generatedGroupIds,
                _generatedLayer: layer,
                _generatedProtocol: L.linkType || L.protocol || '',
                _generatedTopologyObject: true,
                _overlayMode: L._overlayMode || ((layer === 'routing' && /bgp/i.test(String(L.linkType || L.protocol || ''))) ? 'real-legs' : ''),
                _generatedLane: laneIndex,
                _generatedLaneLayer: layer,
                _generatedConfidence: generatedConfidenceFromFact(L, layer === 'physical' ? 'verified' : 'correlated'),
                _generatedSource: generatedSourceFromFact(L, layer === 'physical' ? 'physical-link' : 'logical-link'),
                _generatedEvidence: generatedEvidenceSummary(L),
                _generatedDisplayPriority: generatedPriorityForLayer(layer, 'link'),
                _perimeterKind: L._perimeterKind || '',
                _hidden: L._overlayMode === 'via-rr' || !!L._perimeterKind || layer === 'evidence',
                linkDetails: Object.assign({}, ld, {
                    interface1: fromInterface,
                    interface2: toInterface,
                    interfaceA: ld.interfaceA || fromInterface,
                    interfaceB: ld.interfaceB || toInterface,
                    ipAddressA: ipA,
                    ipAddressB: ipB,
                    vlan: L.vlan || ld.vlan || '',
                    bridgeDomain: L.bd || ld.bridgeDomain || '',
                    protocol: L.protocol || ld.protocol || '',
                    routerIdA: ld.routerIdA || '',
                    routerIdB: ld.routerIdB || '',
                    asnA: ld.asnA || '',
                    asnB: ld.asnB || '',
                    peerIp: L.peerIp || ld.peerIp || ''
                })
            };
            if (L.linkType) link.linkType = L.linkType;
            if (L.layer) link.layer = L.layer;
            if (layer !== 'physical') {
                // Native canvas behavior: manual links use the middle
                // attached TB as the editable curve control point.
                link.curveMode = 'manual';
                link.manualCurvePoint = { x: labelX, y: labelY };
                link._generatorOverlayIndex = laneIndex;
            }
            if (L.vlan) link.vlan = L.vlan;
            if (L.bd) link.bd = L.bd;
            objects.push(link);
            linkObjs.push({ link, fact: L, aObj, bObj, labelX, labelY, layer, laneIndex });
        }

        const serviceCardPlacements = new Map();
        if (Array.isArray(facts.services) && facts.services.length) {
            const serviceOrdinalByCenter = new Map();
            facts.services.forEach(svc => {
                const memberObjs = (svc.members || [])
                    .map(fid => realIdByFactId.get(fid))
                    .map(realId => deviceObjs.find(x => x.id === realId))
                    .filter(Boolean);
                if (memberObjs.length < 2) return;
                let cx = 0, cy = 0;
                memberObjs.forEach(m => { cx += m.x; cy += m.y; });
                cx /= memberObjs.length;
                cy /= memberObjs.length;
                const centerKey = `${Math.round(cx / 160)}:${Math.round(cy / 120)}`;
                const ordinal = serviceOrdinalByCenter.get(centerKey) || 0;
                serviceOrdinalByCenter.set(centerKey, ordinal + 1);
                const cardW = 210;
                const cardH = 78;
                const candidateYs = [
                    cy + 118 + Math.floor(ordinal / 2) * (cardH + 22),
                    cy - 118 - Math.floor(ordinal / 2) * (cardH + 22),
                    cy + 198 + Math.floor(ordinal / 2) * (cardH + 22)
                ];
                const cardX = Math.round(cx - cardW / 2 + (ordinal % 2 ? 125 : -125));
                const cardY = Math.round(candidateYs.find(y => y > 560) || candidateYs[0]);
                const placement = { x: cardX, y: cardY, width: cardW, height: cardH };
                serviceCardPlacements.set(svc.id || `${svc.kind}:${svc.name}`, placement);
                scenePlanner.reserveBox({ x: cardX - 10, y: cardY - 10, w: cardW + 20, h: cardH + 20, kind: 'service' });
            });
        }

        // Text labels: protocol on each link, IP under each device, system above.
        if (options.includeText !== false) {
            const addLinkTb = (link, text, position, x, y, color, opts = {}) => {
                if (!String(text || '').trim()) return;
                const isDetached = !!opts.detached;
                let labelX = x;
                let labelY = y;
                let labelPlacement = null;
                if (Array.isArray(opts.candidates) && opts.candidates.length) {
                    labelPlacement = scenePlanner.pickLabelPoint(opts.candidates, text, opts.fontSize || 9);
                    labelX = labelPlacement.x;
                    labelY = labelPlacement.y;
                }
                const groupIds = Array.isArray(link._generatedGroupIds) ? link._generatedGroupIds.slice() : [];
                if (Array.isArray(opts.extraGroupIds)) {
                    opts.extraGroupIds.forEach(gid => {
                        if (gid && !groupIds.includes(gid)) groupIds.push(gid);
                    });
                }
                const labelObj = {
                    type: 'text',
                    id: `text_${tCounter++}`,
                    x: labelX,
                    y: labelY,
                    text,
                    fontSize: opts.fontSize || 9,
                    fontWeight: opts.fontWeight || '700',
                    color: color || link.color,
                    position,
                    _onLinkLine: !isDetached && opts.onLine !== false,
                    _generatedTopologyLabel: true,
                    _generatedTopologyObject: true,
                    _generatedGroupIds: groupIds,
                    _generatedProtocol: link._generatedProtocol || '',
                    _generatedLayer: opts.layer || link.layer || 'physical',
                    _labelLayer: opts.layer || link.layer || 'physical',
                    _linkDataLabel: !!opts.linkDataLabel,
                    _afChip: !!opts.afChip,
                    _afToken: opts.afToken || '',
                    _afGroup: opts.afGroup || '',
                    _panelGroup: opts.panelGroup || '',
                    _overlayMode: opts.overlayMode || link._overlayMode || '',
                    _generatedLane: opts.laneIndex != null ? opts.laneIndex : link._generatedLane,
                    _generatedConfidence: opts.confidence || link._generatedConfidence || 'correlated',
                    _generatedSource: opts.source || link._generatedSource || 'generated-label',
                    _generatedEvidence: opts.evidence || link._generatedEvidence || [],
                    _generatedDisplayPriority: opts.displayPriority != null
                        ? opts.displayPriority
                        : generatedPriorityForLayer(opts.layer || link.layer || 'physical', 'label'),
                    _labelCollisionAdjusted: !!(labelPlacement && labelPlacement.collided),
                    _hidden: !!(opts.hidden || link._hidden),
                    showBackground: opts.showBackground !== false,
                    backgroundColor: opts.backgroundColor || 'rgba(17, 25, 40, 0.88)',
                    backgroundOpacity: opts.backgroundOpacity !== undefined ? opts.backgroundOpacity : 0.94,
                    backgroundPadding: opts.backgroundPadding || 5,
                    borderRadius: 5
                };
                if (!isDetached) {
                    labelObj.linkId = link.id;
                    labelObj.linkAttachT = opts.t !== undefined ? opts.t : 0.5;
                }
                objects.push(labelObj);
            };
            for (const { link, aObj, bObj, fact, labelX, labelY, layer, laneIndex } of linkObjs) {
                const ld = fact.linkDetails || link.linkDetails || {};
                const ifA = shortenInterface(fact.fromInterface || ld.interfaceA || link.device1Interface || '');
                const ifB = shortenInterface(fact.toInterface || ld.interfaceB || link.device2Interface || '');
                const ipA = ld.ipAddressA || link.device1IpAddress || '';
                const ipB = ld.ipAddressB || link.device2IpAddress || '';
                const ridA = ld.routerIdA || '';
                const ridB = ld.routerIdB || '';
                const peer = ld.peerIp || fact.peerIp || '';
                const afis = Array.isArray(ld.addressFamilies) ? ld.addressFamilies : [];
                const proto = fact.protocol || '';
                let text = proto;
                if (layer === 'physical') {
                    const endpoints = [];
                    if (ifA || ipA) endpoints.push(`${ifA}${ipA ? ' ' + ipA : ''}`.trim());
                    if (ifB || ipB) endpoints.push(`${ifB}${ipB ? ' ' + ipB : ''}`.trim());
                    if (endpoints.length) text = `${proto || 'LLDP'}\n${endpoints.join(' <-> ')}`;
                } else if (layer === 'routing') {
                    const routing = [];
                    if (ridA || ridB) routing.push(`RID ${ridA || '?'} <-> ${ridB || '?'}`);
                    if (peer) routing.push(`peer ${peer}`);
                    if (ld.asnA || ld.asnB) routing.push(`AS ${ld.asnA || '?'} / ${ld.asnB || '?'}`);
                    if (afis.length) routing.push(`AF ${afis.slice(0, 2).join(', ')}`);
                    text = [proto, ...routing].filter(Boolean).join('\n');
                } else if (ifA || ifB) {
                    text = `${proto}\n${ifA} <-> ${ifB}`;
                }
                addLinkTb(link, text, 'middle', labelX, labelY, link.color, {
                    t: 0.5,
                    layer,
                    laneIndex,
                    candidates: buildLaneCandidates(aObj, bObj, laneIndex, layer),
                    fontSize: layer === 'physical' ? 10 : 9,
                    fontWeight: '800',
                    linkDataLabel: true,
                    showBackground: true,
                    backgroundColor: layer === 'physical'
                        ? 'rgba(8, 15, 28, 0.82)'
                        : 'rgba(8, 15, 28, 0.92)'
                });
                if (layer === 'routing' && /bgp/i.test(String(link.linkType || link._generatedProtocol || text)) && afis.length) {
                    const allChips = buildAfChipsForLink({ linkDetails: { addressFamilies: afis } });
                    const chips = allChips.slice(0, 4);
                    if (allChips.length > chips.length) {
                        chips.push({
                            label: `+${allChips.length - chips.length}`,
                            token: 'more',
                            group: 'other',
                            color: '#94a3b8',
                            t: 0.5
                        });
                    }
                    const dx = bObj.x - aObj.x;
                    const dy = bObj.y - aObj.y;
                    const len = Math.max(1, Math.sqrt(dx * dx + dy * dy));
                    const nx = -dy / len;
                    const ny = dx / len;
                    const badgeBaseX = labelX + nx * 34;
                    const badgeBaseY = labelY + ny * 34;
                    chips.forEach((af, idx) => {
                        const rowOffset = (idx - (chips.length - 1) / 2) * 38;
                        const chipX = badgeBaseX + (dx / len) * rowOffset;
                        const chipY = badgeBaseY + (dy / len) * rowOffset;
                        addLinkTb(link, af.label, 'middle', chipX, chipY, af.color, {
                            detached: true,
                            onLine: false,
                            layer,
                            fontSize: 10,
                            afChip: true,
                            afToken: af.token,
                            afGroup: af.group,
                            panelGroup: `protocol:af-${af.group}`,
                            extraGroupIds: [`protocol:af-${af.group}`],
                            overlayMode: link._overlayMode || 'real-legs',
                            laneIndex,
                            showBackground: true,
                            backgroundColor: 'rgba(15, 23, 42, 0.86)',
                            backgroundPadding: 3
                        });
                    });
                }
                if (layer === 'physical' && (ifA || ipA)) {
                    addLinkTb(link, [ifA, ipA].filter(Boolean).join('\n'), 'device1', aObj.x * 0.85 + bObj.x * 0.15, aObj.y * 0.85 + bObj.y * 0.15, link.color, {
                        t: 0.15,
                        layer,
                        candidates: buildLaneCandidates(aObj, bObj, laneIndex + 6, layer),
                        fontSize: 8,
                        showBackground: true
                    });
                }
                if (layer === 'physical' && (ifB || ipB)) {
                    addLinkTb(link, [ifB, ipB].filter(Boolean).join('\n'), 'device2', aObj.x * 0.15 + bObj.x * 0.85, aObj.y * 0.15 + bObj.y * 0.85, link.color, {
                        t: 0.85,
                        layer,
                        candidates: buildLaneCandidates(bObj, aObj, laneIndex + 7, layer),
                        fontSize: 8,
                        showBackground: true
                    });
                }
            }
            for (const d of facts.devices) {
                const realId = realIdByFactId.get(d.id);
                const dev = deviceObjs.find(x => x.id === realId);
                if (!dev) continue;
                const ip = d.ip || d.mgmtIp || '';
                if (ip && /^\d/.test(ip)) {
                    objects.push({
                        type: 'text',
                        id: `text_${tCounter++}`,
                        x: dev.x,
                        y: dev.y + (dev.radius || 40) + 22,
                        text: ip,
                        fontSize: 10,
                        color: '#85929e',
                        showBackground: false,
                        _generatedTopologyObject: true,
                        _generatedGroupIds: ['layer:labels'],
                        _generatedLayer: 'label',
                        _generatedProtocol: 'device-label'
                    });
                }
                const sys = [];
                if (d.system_type) sys.push(d.system_type);
                if (d.dnos_version) {
                    const ver = String(d.dnos_version).replace(/^.*?(\d+\.\d+).*$/, '$1');
                    if (ver) sys.push('v' + ver);
                }
                if (sys.length) {
                    objects.push({
                        type: 'text',
                        id: `text_${tCounter++}`,
                        x: dev.x,
                        y: dev.y - (dev.radius || 40) - 20,
                        text: sys.join(' | '),
                        fontSize: 8,
                        color: '#aeb6bf',
                        showBackground: false,
                        _generatedTopologyObject: true,
                        _generatedGroupIds: ['layer:labels'],
                        _generatedLayer: 'label',
                        _generatedProtocol: 'device-label'
                    });
                }
                // AS / router-id callout to the side -- helps the
                // operator at a glance identify routing identity.
                const asn = (d.config && d.config.asn) || d._asn || '';
                const routerId = (d.config && d.config.router_id) || d._routerId || '';
                const callout = [];
                if (asn) callout.push(`AS${asn}`);
                if (routerId) callout.push(`RID ${routerId}`);
                if (callout.length) {
                    objects.push({
                        type: 'text',
                        id: `text_${tCounter++}`,
                        x: dev.x + (dev.radius || 40) + 30,
                        y: dev.y - 6,
                        text: callout.join('\n'),
                        fontSize: 9,
                        color: '#9b59b6',
                        showBackground: false,
                        _generatedTopologyObject: true,
                        _generatedGroupIds: ['layer:labels', 'layer:routing', 'layer:identity', 'layer:overlay'],
                        _generatedLayer: 'identity',
                        _generatedProtocol: 'identity-label'
                    });
                }
                // RD next to the AS callout when present (typical PE
                // shows up with VRF RDs we can advertise).
                const rds = (d.config && d.config.route_distinguishers) || [];
                if (rds.length) {
                    objects.push({
                        type: 'text',
                        id: `text_${tCounter++}`,
                        x: dev.x + (dev.radius || 40) + 30,
                        y: dev.y + 14,
                        text: 'RD ' + rds.slice(0, 2).join(', ') + (rds.length > 2 ? ` +${rds.length - 2}` : ''),
                        fontSize: 8,
                        color: '#1abc9c',
                        showBackground: false,
                        _generatedTopologyObject: true,
                        _generatedGroupIds: ['layer:labels', 'layer:service', 'layer:services'],
                        _generatedLayer: 'service',
                        _generatedProtocol: 'rd-label'
                    });
                }
                if (d._unmatchedReason) {
                    objects.push({
                        type: 'text',
                        id: `text_${tCounter++}`,
                        x: dev.x,
                        y: dev.y + (dev.radius || 40) + 42,
                        text: 'Unmatched DUT\n' + d._unmatchedReason,
                        fontSize: 8,
                        color: '#f1c40f',
                        showBackground: true,
                        backgroundColor: 'rgba(17, 25, 40, 0.88)',
                        backgroundOpacity: 0.88,
                        backgroundPadding: 5,
                        borderRadius: 6,
                        _generatedTopologyObject: true,
                        _generatedGroupIds: ['layer:labels', 'layer:evidence'],
                        _generatedLayer: 'evidence',
                        _generatedProtocol: 'unmatched-dut'
                    });
                }
            }
        }

        // Service correlation cards: RT/VRF/BD facts are visual services,
        // not extra protocol links. This keeps routing topology clean while
        // still showing which DUTs participate in the same service.
        if (options.includeText !== false && Array.isArray(facts.services) && facts.services.length) {
            for (const svc of facts.services) {
                const memberObjs = (svc.members || [])
                    .map(fid => realIdByFactId.get(fid))
                    .map(realId => deviceObjs.find(x => x.id === realId))
                    .filter(Boolean);
                if (memberObjs.length < 2) continue;
                let cx = 0, cy = 0;
                memberObjs.forEach(m => { cx += m.x; cy += m.y; });
                cx /= memberObjs.length;
                cy /= memberObjs.length;
                const fillColor = svc.color || '#1abc9c';
                const groupId = ensureGeneratedGroup(
                    `service:${cleanGroupPart(svc.kind || 'service')}:${cleanGroupPart(svc.name || svc.id || '')}`,
                    svc.label || svc.name || 'Service',
                    'service',
                    fillColor,
                    'service'
                );
                const placement = serviceCardPlacements.get(svc.id || `${svc.kind}:${svc.name}`) || {};
                const cardW = placement.width || 210;
                const cardH = placement.height || 78;
                const cardX = placement.x != null ? placement.x : Math.round(cx - cardW / 2);
                const cardY = placement.y != null ? placement.y : Math.round(cy + 118);
                objects.push({
                    type: 'shape',
                    id: `shape_${sCounter++}`,
                    shapeType: 'rectangle',
                    x: cardX,
                    y: cardY,
                    width: cardW,
                    height: cardH,
                    fillColor,
                    fillOpacity: GENERATE_STYLE_PROFILE.shapes.service.fillOpacity,
                    fillEnabled: true,
                    strokeColor: fillColor,
                    strokeWidth: 1.4,
                    strokeEnabled: true,
                    cornerRadius: GENERATE_STYLE_PROFILE.shapes.service.cornerRadius,
                    rotation: 0,
                    label: svc.label || '',
                    locked: false,
                    _generatedTopologyObject: true,
                    _generatedGroupIds: ['layer:service', groupId],
                    _generatedLayer: 'service',
                    _generatedProtocol: svc.kind || 'service',
                    _generatedConfidence: svc._confidenceClass || generatedConfidenceFromFact(svc, 'correlated'),
                    _generatedSource: generatedSourceFromFact(svc, 'service-correlation'),
                    _generatedEvidence: [].concat(svc.routeTargets || [], svc.rds ? Object.values(svc.rds) : [], svc.mode || '').filter(Boolean),
                    _generatedDisplayPriority: 85
                });
                objects.push({
                    type: 'text',
                    id: `text_${tCounter++}`,
                    x: cardX + cardW / 2,
                    y: cardY + cardH / 2,
                    text: summarizeServiceEvidence(svc),
                    fontSize: 10,
                    fontWeight: '800',
                    color: '#e2f8f4',
                    showBackground: true,
                    backgroundColor: 'rgba(8, 15, 28, 0.92)',
                    backgroundOpacity: 0.94,
                    backgroundPadding: 6,
                    borderRadius: 6,
                    _generatedTopologyObject: true,
                    _generatedGroupIds: ['layer:service', groupId],
                    _generatedLayer: 'service',
                    _generatedProtocol: svc.kind || 'service',
                    _generatedConfidence: svc._confidenceClass || generatedConfidenceFromFact(svc, 'correlated'),
                    _generatedSource: generatedSourceFromFact(svc, 'service-correlation'),
                    _generatedEvidence: [].concat(svc.routeTargets || [], svc.rds ? Object.values(svc.rds) : [], svc.mode || '').filter(Boolean),
                    _generatedDisplayPriority: 86,
                    _generatedServiceLabel: true
                });
            }
        }

        // Grouping shapes (rectangles around members).
        if (options.includeShapes !== false) {
            for (const g of facts.groups) {
                const memberObjs = g.members
                    .map(fid => realIdByFactId.get(fid))
                    .map(realId => deviceObjs.find(x => x.id === realId))
                    .filter(Boolean);
                if (memberObjs.length === 0) continue;
                let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                for (const m of memberObjs) {
                    const r = m.radius || 40;
                    minX = Math.min(minX, m.x - r);
                    minY = Math.min(minY, m.y - r);
                    maxX = Math.max(maxX, m.x + r);
                    maxY = Math.max(maxY, m.y + r);
                }
                const pad = 50;
                const fillColor = g.color || '#3498db';
                const shapeProfile = GENERATE_STYLE_PROFILE.shapes[g.kind] || GENERATE_STYLE_PROFILE.shapes.as;
                const padX = shapeProfile.padX || pad;
                const padY = shapeProfile.padY || pad;
                const shapeGroupId = ensureGeneratedGroup(
                    `shape:${cleanGroupPart(g.kind || 'group')}:${cleanGroupPart(g.label || g.id || '')}`,
                    g.label || g.kind || 'Group',
                    g.kind || 'shape',
                    fillColor,
                    g.kind === 'vrf' || g.kind === 'bd' ? 'service' : 'routing'
                );
                objects.push({
                    type: 'shape',
                    id: `shape_${sCounter++}`,
                    shapeType: 'rectangle',
                    x: minX - padX,
                    y: minY - padY,
                    width: (maxX - minX) + padX * 2,
                    height: (maxY - minY) + padY * 2,
                    fillColor,
                    fillOpacity: shapeProfile.fillOpacity || 0.055,
                    fillEnabled: true,
                    strokeColor: fillColor,
                    strokeWidth: 1.5,
                    strokeEnabled: true,
                    cornerRadius: shapeProfile.cornerRadius || 14,
                    rotation: 0,
                    label: g.label || '',
                    locked: false,
                    _generatedTopologyObject: true,
                    _generatedGroupIds: [shapeGroupId],
                    _generatedLayer: g.kind === 'vrf' || g.kind === 'bd' ? 'service' : 'routing',
                    _generatedProtocol: g.kind || 'shape'
                });
                if (g.label) {
                    objects.push({
                        type: 'text',
                        id: `text_${tCounter++}`,
                        x: (minX + maxX) / 2,
                        y: minY - padY - 8,
                        text: g.label,
                        fontSize: 12,
                        color: fillColor,
                        showBackground: true,
                        backgroundColor: 'rgba(17, 25, 40, 0.85)',
                        backgroundOpacity: 0.85,
                        backgroundPadding: 6,
                        _generatedTopologyObject: true,
                        _generatedGroupIds: [shapeGroupId],
                        _generatedLayer: g.kind === 'vrf' || g.kind === 'bd' ? 'service' : 'routing',
                        _generatedProtocol: g.kind || 'shape'
                    });
                }
            }
        }

        objects.forEach(obj => {
            if (!obj || !obj._generatedTopologyObject) return;
            const layer = obj._generatedLayer || obj.layer || (obj.type === 'device' ? 'device' : 'generated');
            applyGeneratedSceneMeta(obj, {
                layer,
                confidence: obj._generatedConfidence || (layer === 'device' || layer === 'physical' ? 'verified' : 'correlated'),
                source: obj._generatedSource || 'generated-payload',
                evidence: obj._generatedEvidence || [],
                displayPriority: obj._generatedDisplayPriority
            });
        });
        const confidenceCounts = objects.reduce((acc, obj) => {
            if (!obj || !obj._generatedTopologyObject) return acc;
            const key = obj._generatedConfidence || 'correlated';
            acc[key] = (acc[key] || 0) + 1;
            return acc;
        }, { verified: 0, correlated: 0, inferred: 0, missing: 0 });

        meta.deviceIdCounter = dCounter;
        meta.linkIdCounter = lCounter;
        meta.textIdCounter = tCounter;
        meta.shapeIdCounter = sCounter;
        meta.description = `Generated topology (${facts.provenance.source}): `
            + `${facts.devices.length} devices, ${facts.links.length} links, `
            + `${facts.logicalLinks ? facts.logicalLinks.length : 0} logical, `
            + `${facts.groups.length} groups`;
        meta.generator = {
            source: facts.provenance.source,
            collectedAt: facts.provenance.collectedAt,
            durationMs: facts.provenance.durationMs,
            notes: facts.provenance.notes
        };
        if (facts.compositionReport) meta.compositionReport = clonePlain(facts.compositionReport);
        if (facts.generationSignature) meta.generationSignature = clonePlain(facts.generationSignature);
        if (facts._correlationEvidence) meta.correlationEvidence = clonePlain(facts._correlationEvidence);
        if (facts.correlationLayout) meta.correlationLayout = clonePlain(facts.correlationLayout);
        meta.generatedOverlayModes = [
            { id: 'real-legs', label: 'Real Legs', visible: true },
            { id: 'via-rr', label: 'Via-RR Spline', visible: false },
            { id: 'both', label: 'Both', visible: false }
        ];
        meta.generatedOverlayDefaultMode = 'real-legs';
        meta.generatedSceneQuality = {
            confidenceCounts,
            requiredFields: ['layer', 'confidence', 'source', 'evidence', 'displayPriority'],
            laneCount: objects.filter(o => o && (o.type === 'link' || o.type === 'unbound') && o._generatedLane != null).length,
            labelBoxCount: scenePlanner.labelBoxes.length
        };
        meta.generatedAfGroups = Array.from(new Set(Object.values(AF_PALETTE).map(af => af.group))).map(group => ({
            id: `protocol:af-${group}`,
            label: `AF ${group}`,
            visible: true
        }));
        meta.generatedPerimeterKinds = ['fabric', 'cpe', 'tester', 'foreign-igp', 'scale-fan'].map(kind => ({
            id: `perimeter:${kind}`,
            label: `Perimeter ${kind}`,
            visible: false
        }));
        meta.generatedProtocolGroups = Array.from(generatedProtocolGroups.values())
            .map(group => {
                const groupObjects = objects
                    .filter(obj => Array.isArray(obj._generatedGroupIds) && obj._generatedGroupIds.includes(group.id));
                const objectIds = groupObjects.map(obj => obj.id);
                const visible = group.kind !== 'perimeter' && group.layer !== 'evidence';
                const confidenceCountsForGroup = groupObjects.reduce((acc, obj) => {
                    const key = obj._generatedConfidence || 'correlated';
                    acc[key] = (acc[key] || 0) + 1;
                    return acc;
                }, { verified: 0, correlated: 0, inferred: 0, missing: 0 });
                return {
                    ...group,
                    visible,
                    objectIds,
                    count: objectIds.length,
                    confidenceCounts: confidenceCountsForGroup,
                    warningCount: confidenceCountsForGroup.missing + confidenceCountsForGroup.inferred
                };
            })
            .filter(group => group.objectIds.length > 0 || group.id === 'layer:devices');
        // Surface fact->canvas id mapping for AI enrichment so the
        // model can target style/text edits at the exact rendered
        // objects without re-deriving them from labels.
        const idMap = {};
        for (const [factId, realId] of realIdByFactId) idMap[factId] = realId;
        meta.idMap = idMap;

        return { version: '1.0', objects, metadata: meta };
    }

    // -------------------------------------------------------------- manager

    class TopologyGeneratorManager {
        constructor(editor) {
            this.editor = editor;
            this._currentSource = 'live';
            this._lastFacts = null;
            this._lastPayload = null;
            this._cancelRequested = false;
            this._importPayload = null;
        }

        setupPanel() {
            const panel = document.getElementById('network-mapper-panel');
            if (!panel) {
                console.warn('[TopologyGenerator] Panel not found yet');
                return;
            }
            panel.__genManager = this;
            this._wireDelegatedPanelHandlers(panel);
            this._wireTabs(panel);
            this._wireCanvasTab();
            this._wireLiveTab();
            this._wireImportTab();
            this._wirePreviewActions();
            this._activateTab(this._currentSource);

            // Re-activate the tab whenever the panel becomes visible.
            // The Network Mapper module flips ``display`` between
            // ``none`` and ``block``; this MutationObserver keeps the
            // generator in sync so the active pane is always painted.
            try {
                if (!panel.__genObserver) {
                    const obs = new MutationObserver(() => {
                        const visible = panel.style.display === 'block';
                        const mgr = panel.__genManager || this;
                        if (visible) mgr._activateTab(mgr._currentSource || 'canvas');
                    });
                    obs.observe(panel, { attributes: true, attributeFilter: ['style'] });
                    panel.__genObserver = obs;
                }
            } catch (_) {}

            console.log('[OK] TopologyGeneratorManager panel setup complete');
        }

        _wireTabs(panel) {
            const btns = panel.querySelectorAll('.gen-tab-btn');
            btns.forEach(btn => {
                if (btn.__genTabWired) return;
                btn.__genTabWired = true;
                btn.addEventListener('click', () => {
                    const tab = btn.getAttribute('data-gen-tab');
                    if (!tab) return;
                    this._activeManager()._activateTab(tab);
                });
            });
        }

        _activeManager() {
            const panel = document.getElementById('network-mapper-panel');
            const mgr = (panel && panel.__genManager) || this;
            const ed = _editor();
            if (ed && mgr.editor !== ed) {
                mgr.editor = ed;
                ed.topologyGenerator = mgr;
                window.topologyGenerator = mgr;
            }
            return mgr;
        }

        _activateTab(tab) {
            if (!SOURCE_TABS.includes(tab)) tab = 'canvas';
            this._currentSource = tab;
            const panel = document.getElementById('network-mapper-panel');
            if (!panel) return;
            panel.querySelectorAll('.gen-tab-btn').forEach(b => {
                if (b.getAttribute('data-gen-tab') === tab) b.classList.add('active');
                else b.classList.remove('active');
            });
            panel.querySelectorAll('.gen-tab-pane').forEach(p => {
                p.style.display = (p.getAttribute('data-gen-pane') === tab) ? 'block' : 'none';
            });
            // Refresh per-tab dynamic summaries.
            if (tab === 'live') this._refreshLiveSummary();
        }

        _refreshLiveSummary() {
            const el = document.getElementById('gen-live-target-summary');
            if (!el) return;
            const collected = this._collectLiveTargets();
            const total = collected.targets.length;
            if (total === 0) {
                const skipped = [];
                if (collected.skippedNoSsh) skipped.push(`${collected.skippedNoSsh} canvas device(s) without SSH`);
                if (collected.skippedExcluded) skipped.push(`${collected.skippedExcluded} DNAAS/fabric device(s)`);
                el.innerHTML = 'No SSH-backed DUT targets yet. Type DUT names/IPs above, or check "Auto-include canvas devices".'
                    + (skipped.length ? ` <span style="color: rgba(255,255,255,0.55);">Skipped ${skipped.join(', ')}.</span>` : '');
                el.style.color = 'rgba(231, 76, 60, 0.85)';
                return;
            }
            const labels = collected.targets.slice(0, 6).map(t => escapeHtml(t.label || t.deviceId || t.host || '')).join(', ');
            el.innerHTML = `<strong>${total}</strong> target(s): ${labels}`
                + (total > 6 ? `, +${total - 6} more` : '')
                + ` <span style="color: rgba(255,255,255,0.5);">(${collected.fromManual} manual, ${collected.fromCanvas} SSH-canvas, ${collected.fromSelected} SSH-selected`
                + (collected.skippedNoSsh ? `, skipped ${collected.skippedNoSsh} no-SSH` : '')
                + (collected.skippedExcluded ? `, skipped ${collected.skippedExcluded} DNAAS/fabric` : '')
                + ')</span>';
            el.style.color = 'rgba(255, 255, 255, 0.78)';
        }

        // ---------------------------------------------- target collection

        /**
         * Parse the Live Devices tab inputs and return the merged list of
         * DUTs to operate on. Each target is a dict::
         *
         *     { deviceId, host, label, ssh: {host, user, password},
         *       source: 'manual' | 'canvas' | 'selected' | 'inventory' }
         *
         * Manual entries are validated (no whitespace inside the token);
         * IPs and serials are accepted. Canvas-derived entries reuse
         * the existing ``sshConfig`` so we don't ever drop credentials
         * the operator already typed in the SSH dialog.
         */
        _collectLiveTargets() {
            const out = {
                targets: [],
                fromManual: 0,
                fromCanvas: 0,
                fromSelected: 0,
                skippedNoSsh: 0,
                skippedExcluded: 0
            };
            const seen = new Map();
            const push = (t) => {
                const k = (t.deviceId || t.host || '').toLowerCase();
                if (!k) return;
                if (seen.has(k)) return;
                seen.set(k, t);
                out.targets.push(t);
            };

            // 1) manual textarea
            const ta = document.getElementById('gen-live-targets');
            const userI = document.getElementById('gen-live-ssh-user');
            const passI = document.getElementById('gen-live-ssh-pass');
            const sshUser = (userI && userI.value || '').trim() || 'dnroot';
            const sshPass = (passI && passI.value) || 'dnroot';
            if (ta && ta.value) {
                const tokens = ta.value.split(/[\s,]+/).map(s => s.trim()).filter(Boolean);
                for (const tok of tokens) {
                    const isIp = /^\d+\.\d+\.\d+\.\d+$/.test(tok);
                    push({
                        deviceId: tok, host: isIp ? tok : '', label: tok,
                        ssh: { host: isIp ? tok : '', user: sshUser, password: sshPass },
                        source: 'manual'
                    });
                    out.fromManual++;
                }
            }

            // 2) canvas-only-selected toggle wins over auto-include
            const useSelected = document.getElementById('gen-live-use-canvas-selected');
            const useCanvasSsh = document.getElementById('gen-live-use-canvas-ssh');
            const objs = (this.editor && this.editor.objects) || [];
            const selectedIds = new Set(((this.editor && this.editor.selectedObjects) || [])
                .map(o => o && o.id).filter(Boolean));
            const wantSelected = !!(useSelected && useSelected.checked);
            const wantCanvas = !wantSelected && !!(useCanvasSsh && useCanvasSsh.checked);

            if (wantSelected || wantCanvas) {
                for (const o of objs) {
                    if (!o || o.type !== 'device') continue;
                    if (wantSelected && !selectedIds.has(o.id)) continue;
                    if (isCanvasDiscoveryExcludedDevice(this.editor, o)) {
                        out.skippedExcluded++;
                        continue;
                    }
                    const sshTarget = getCanvasSshTarget(o);
                    if (!sshTarget) {
                        out.skippedNoSsh++;
                        continue;
                    }
                    const ssh = o.sshConfig || {};
                    const host = sshTarget.host;
                    const id = o.label || o.deviceSerial || o.id;
                    push({
                        deviceId: id,
                        host,
                        label: o.label || id,
                        ssh: {
                            host,
                            user: sshTarget.user || sshUser,
                            password: sshTarget.password || sshPass
                        },
                        source: wantSelected ? 'selected' : 'canvas',
                        canvasId: o.id
                    });
                    if (wantSelected) out.fromSelected++; else out.fromCanvas++;
                }
            }
            return out;
        }

        _refreshDnaasSummary() {
            const el = document.getElementById('gen-dnaas-summary');
            if (!el) return;
            const dnaas = window.DnaasManager || window.dnaasManager || (this.editor && this.editor.dnaasManager);
            const data = dnaas && (dnaas.lastResult || dnaas._lastResult || dnaas.data) || null;
            if (!data || !data.devices) {
                el.innerHTML = 'No DNAAS discovery loaded. Run a DNAAS scan from the DNAAS panel first.';
                el.style.color = 'rgba(231, 76, 60, 0.85)';
                return;
            }
            const dlist = Array.isArray(data.devices) ? data.devices : Object.values(data.devices || {});
            const bds = Array.isArray(data.bridge_domains) ? data.bridge_domains : (data.bridge_domains ? Object.values(data.bridge_domains) : []);
            el.innerHTML = `DNAAS data ready: <strong>${dlist.length}</strong> devices, <strong>${bds.length}</strong> bridge domain(s).`;
            el.style.color = 'rgba(255, 255, 255, 0.75)';
        }

        // ------------------------------------------------ tab wiring

        _wireDelegatedPanelHandlers(panel) {
            if (!panel || panel.__genDelegatedWired) return;
            panel.__genDelegatedWired = true;
            panel.addEventListener('click', (ev) => {
                const target = ev.target && ev.target.closest
                    ? ev.target.closest('[data-gen-tab], #gen-canvas-generate, #gen-live-generate, #gen-live-resolve, #gen-import-pick, #gen-import-generate, #gen-apply, #gen-save-domain, #gen-regenerate, #gen-enrich-ai, #gen-cancel-preview, #gen-cancel')
                    : null;
                if (!target || !panel.contains(target)) return;
                const tab = target.getAttribute('data-gen-tab');
                if (tab) {
                    if (target.__genTabWired) return;
                    ev.preventDefault();
                    this._activeManager()._activateTab(tab);
                    return;
                }
                if (target.__genWired) return;
                switch (target.id) {
                    case 'gen-canvas-generate':
                        ev.preventDefault();
                        this._activeManager()._generateFromCanvas();
                        break;
                    case 'gen-live-generate':
                        ev.preventDefault();
                        this._activeManager()._generateFromLive();
                        break;
                    case 'gen-live-resolve':
                        ev.preventDefault();
                        this._activeManager()._resolveAndMonitorLive();
                        break;
                    case 'gen-import-pick':
                        ev.preventDefault();
                        document.getElementById('gen-import-file')?.click();
                        break;
                    case 'gen-import-generate':
                        ev.preventDefault();
                        this._activeManager()._generateFromImport();
                        break;
                    case 'gen-apply':
                        ev.preventDefault();
                        this._activeManager()._applyPayload();
                        break;
                    case 'gen-save-domain':
                        ev.preventDefault();
                        this._activeManager()._saveToDomain();
                        break;
                    case 'gen-regenerate':
                        ev.preventDefault();
                        this._activeManager()._regenerate();
                        break;
                    case 'gen-enrich-ai':
                        ev.preventDefault();
                        this._activeManager()._enrichWithAi();
                        break;
                    case 'gen-cancel-preview':
                        ev.preventDefault();
                        this._activeManager()._discardPreview();
                        break;
                    case 'gen-cancel':
                        ev.preventDefault();
                        this._activeManager()._cancelRequested = true;
                        break;
                }
            });
        }

        _wireCanvasTab() {
            const btn = document.getElementById('gen-canvas-generate');
            if (btn && !btn.__genWired) {
                btn.__genWired = true;
                btn.addEventListener('click', () => this._activeManager()._generateFromCanvas());
            }
        }
        _wireLiveTab() {
            const btn = document.getElementById('gen-live-generate');
            if (btn && !btn.__genWired) {
                btn.__genWired = true;
                btn.addEventListener('click', () => this._activeManager()._generateFromLive());
            }
            const resolve = document.getElementById('gen-live-resolve');
            if (resolve && !resolve.__genWired) {
                resolve.__genWired = true;
                resolve.addEventListener('click', () => this._activeManager()._resolveAndMonitorLive());
            }

            // Live-update the target summary whenever the operator
            // types into the textarea or toggles a source checkbox.
            const ta = document.getElementById('gen-live-targets');
            if (ta && !ta.__genInputWired) {
                ta.__genInputWired = true;
                ta.addEventListener('input', () => this._activeManager()._refreshLiveSummary());
            }
            ['gen-live-use-canvas-ssh', 'gen-live-use-canvas-selected'].forEach(id => {
                const el = document.getElementById(id);
                if (el && !el.__genInputWired) {
                    el.__genInputWired = true;
                    el.addEventListener('change', () => this._activeManager()._refreshLiveSummary());
                }
            });
        }
        _wireImportTab() {
            const pick = document.getElementById('gen-import-pick');
            const file = document.getElementById('gen-import-file');
            const summary = document.getElementById('gen-import-summary');
            const paste = document.getElementById('gen-import-paste');
            const gen = document.getElementById('gen-import-generate');
            if (pick && file && !pick.__genWired) {
                pick.__genWired = true;
                pick.addEventListener('click', () => file.click());
            }
            if (file && !file.__genInputWired) {
                file.__genInputWired = true;
                file.addEventListener('change', () => {
                const f = file.files && file.files[0];
                if (!f) return;
                const reader = new FileReader();
                reader.onload = () => {
                    const text = String(reader.result || '');
                    let json = null;
                    if (f.name.toLowerCase().endsWith('.json')) {
                        try { json = JSON.parse(text); } catch (_) {}
                    }
                    this._importPayload = { text, json, name: f.name };
                    if (summary) summary.innerHTML = `Loaded <strong>${escapeHtml(f.name)}</strong> (${(text.length/1024).toFixed(1)} KB)`;
                };
                reader.readAsText(f);
                });
            }
            if (paste && !paste.__genInputWired) {
                paste.__genInputWired = true;
                paste.addEventListener('input', () => {
                const text = paste.value || '';
                let json = null;
                const trimmed = text.trim();
                if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
                    try { json = JSON.parse(trimmed); } catch (_) {}
                }
                this._importPayload = { text, json, name: 'pasted-content' };
                if (summary && trimmed) summary.innerHTML = `Pasted ${(text.length/1024).toFixed(1)} KB`;
                });
            }
            if (gen && !gen.__genWired) {
                gen.__genWired = true;
                gen.addEventListener('click', () => this._activeManager()._generateFromImport());
            }
        }
        _wirePreviewActions() {
            const apply = document.getElementById('gen-apply');
            const save = document.getElementById('gen-save-domain');
            const regen = document.getElementById('gen-regenerate');
            const enrich = document.getElementById('gen-enrich-ai');
            const cancel = document.getElementById('gen-cancel-preview');
            const cancelProgress = document.getElementById('gen-cancel');
            if (apply && !apply.__genWired) { apply.__genWired = true; apply.addEventListener('click', () => this._activeManager()._applyPayload()); }
            if (save && !save.__genWired) { save.__genWired = true; save.addEventListener('click', () => this._activeManager()._saveToDomain()); }
            if (regen && !regen.__genWired) { regen.__genWired = true; regen.addEventListener('click', () => this._activeManager()._regenerate()); }
            if (enrich && !enrich.__genWired) { enrich.__genWired = true; enrich.addEventListener('click', () => this._activeManager()._enrichWithAi()); }
            if (cancel && !cancel.__genWired) { cancel.__genWired = true; cancel.addEventListener('click', () => this._activeManager()._discardPreview()); }
            if (cancelProgress && !cancelProgress.__genWired) {
                cancelProgress.__genWired = true;
                cancelProgress.addEventListener('click', () => { this._activeManager()._cancelRequested = true; });
            }
        }

        // ------------------------------------------------ progress & log

        _showProgress(msg) {
            const p = document.getElementById('gen-progress');
            const t = document.getElementById('gen-progress-text');
            const log = document.getElementById('gen-log');
            const spinner = document.getElementById('gen-spinner');
            const cancel = document.getElementById('gen-cancel');
            const status = document.getElementById('nm-panel-status');
            if (p) p.style.display = 'block';
            if (t) t.textContent = msg || 'Working...';
            if (log) log.textContent = '';
            if (spinner) spinner.style.display = '';
            if (cancel) cancel.style.display = '';
            if (status) status.textContent = 'Running';
            this._cancelRequested = false;
        }
        _hideProgress() {
            const p = document.getElementById('gen-progress');
            const status = document.getElementById('nm-panel-status');
            if (p) p.style.display = 'none';
            if (status) status.textContent = 'Ready';
        }
        _finishProgress(msg) {
            const p = document.getElementById('gen-progress');
            const t = document.getElementById('gen-progress-text');
            const spinner = document.getElementById('gen-spinner');
            const cancel = document.getElementById('gen-cancel');
            const status = document.getElementById('nm-panel-status');
            if (p) p.style.display = 'block';
            if (t) t.textContent = msg || 'Preview ready';
            if (spinner) spinner.style.display = 'none';
            if (cancel) cancel.style.display = 'none';
            if (status) status.textContent = 'Ready';
        }
        _log(line) {
            const log = document.getElementById('gen-log');
            if (!log) return;
            log.textContent += (line + '\n');
            log.scrollTop = log.scrollHeight;
        }
        _setProgressText(msg) {
            const t = document.getElementById('gen-progress-text');
            if (t) t.textContent = msg;
        }

        // ------------------------------------------------ generators

        _showFactWarnings(facts) {
            (facts.warnings || []).forEach(w => this._log('warning: ' + w));
            const report = facts && facts.compositionReport;
            if (report) {
                this._log(`architecture: ${report.topologyFamily} (${report.visualProfile}), score ${report.score}`);
                if (report.unmatchedDevices && report.unmatchedDevices.length) {
                    report.unmatchedDevices.forEach(d => this._log(`  unmatched: ${d.hostname} - ${d.reason}`));
                }
            }
        }

        _learningEnabled() {
            const el = document.getElementById('gen-live-use-learning');
            return !el || el.checked !== false;
        }

        async _loadLearningHintsForFacts(facts) {
            if (!this._learningEnabled() || !facts) return {};
            try {
                const signature = buildGenerationSignature(facts);
                const resp = await _authFetch('/api/topology-generator/learning/match', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ signature })
                });
                if (!resp.ok) return {};
                const data = await resp.json();
                const hints = data && data.hints || {};
                if (data && data.matched) this._log(`learning: matched ${data.match_key || 'saved style'}`);
                return hints;
            } catch (e) {
                this._log('learning: unavailable (' + (e.message || e) + ')');
                return {};
            }
        }

        async _saveLearningFromCurrent(reason) {
            if (!this._learningEnabled() || !this._lastFacts || !this._lastPayload) return;
            try {
                const facts = this._lastFacts;
                const signature = facts.generationSignature || buildGenerationSignature(facts);
                const report = facts.compositionReport || {};
                const payload = this._lastPayload || {};
                const generated = (payload.objects || []).filter(o => o && o._generatedTopologyObject);
                const hints = {
                    layoutFamily: report.topologyFamily || inferTopologyFamily(facts),
                    visualProfile: report.visualProfile || 'balanced-generated-v1',
                    protocolGroups: payload.metadata && payload.metadata.generatedProtocolGroups || [],
                    objectSummary: {
                        devices: generated.filter(o => o.type === 'device').length,
                        links: generated.filter(o => o.type === 'link' || o.type === 'unbound').length,
                        texts: generated.filter(o => o.type === 'text').length,
                        shapes: generated.filter(o => o.type === 'shape').length
                    }
                };
                await _authFetch('/api/topology-generator/learning', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ signature, hints, reason: reason || 'accepted-generated-topology' })
                });
                this._log('learning: saved style for similar topology');
            } catch (e) {
                this._log('learning: save failed (' + (e.message || e) + ')');
            }
        }

        _generateFromCanvas() {
            const opts = {
                includeText: !!document.getElementById('gen-canvas-add-text')?.checked,
                includeShapes: !!document.getElementById('gen-canvas-add-shapes')?.checked,
                restyleLinks: !!document.getElementById('gen-canvas-restyle-links')?.checked,
                linkTable: !!document.getElementById('gen-canvas-link-table')?.checked
            };
            this._showProgress('Reading canvas...');
            this._log('source: canvas');
            const facts = adapterCanvas(this.editor, { includeShapes: opts.includeShapes });
            this._showFactWarnings(facts);
            this._lastFacts = facts;
            this._lastPayload = buildCanvasPayload(facts, {
                includeText: opts.includeText,
                includeShapes: opts.includeShapes
            });
            this._showPreview();
        }

        async _generateFromLive() {
            const opts = {
                fetchConfig: !!document.getElementById('gen-live-fetch-config')?.checked,
                includeShapes: !!document.getElementById('gen-live-include-shapes')?.checked,
                includeText: !!document.getElementById('gen-live-include-text')?.checked,
                includeLldp: document.getElementById('gen-live-include-lldp')?.checked !== false,
                monitor: document.getElementById('gen-live-monitor')?.checked !== false,
                live: true
            };
            this._showProgress('Resolving DUT targets...');
            this._log('source: live');

            const collected = this._collectLiveTargets();
            if (collected.targets.length === 0) {
                this._log('No targets supplied. Add device names/IPs or enable canvas SSH auto-include.');
                this._finishProgress('No targets');
                return;
            }
            try {
                const resolved = await this._resolveTargetsRemote(collected.targets);
                if (opts.monitor) {
                    this._registerMonitor(resolved.watch_ids || []);
                }
                this._setProgressText('Collecting live device facts...');
                const mergedTargets = this._mergeResolvedWithTargets(collected.targets, resolved.resolved || []);
                const liveTargets = mergedTargets.filter(t => {
                    if (getTargetSshHost(t)) return true;
                    this._log(`  - ${t.label || t.deviceId || 'target'}: skipped (no resolved SSH host)`);
                    return false;
                });
                if (liveTargets.length === 0) {
                    this._finishProgress('No SSH-backed DUTs');
                    return;
                }
                const facts = await adapterLive(this.editor, opts,
                    msg => this._log(msg),
                    liveTargets
                );
                const learnedHints = await this._loadLearningHintsForFacts(facts);
                let usedBackendCorrelation = false;
                try {
                    const cr = await correlateFactsRemote(facts, { learnedHints });
                    if (cr && cr.ok && cr.facts && Array.isArray(cr.facts.devices)) {
                        const ev = cr.correlationEvidence || {};
                        Object.assign(facts, cr.facts);
                        facts._correlationEvidence = ev;
                        facts.correlationLayout = ev.layout || null;
                        usedBackendCorrelation = true;
                        this._log('correlation: SQLite backend '
                            + `(${ev.topologyFamily || 'unknown'}, `
                            + `${(ev.logicalLinkCount != null ? ev.logicalLinkCount : 0)} logical, `
                            + `${(ev.serviceCount != null ? ev.serviceCount : 0)} services)`);
                    } else {
                        this._log('correlation: backend returned non-ok; using local compose');
                    }
                } catch (err) {
                    this._log('correlation API failed (' + (err.message || err) + '); using local compose');
                }
                if (!usedBackendCorrelation) {
                    composeArchitectureFacts(facts, {
                        keepPositions: false,
                        learnedHints
                    });
                } else {
                    facts.logicalLinks = (facts.logicalLinks || []).map(l => {
                        const style = styleForLinkType(l.linkType, l.layer);
                        return Object.assign({}, l, { style: Object.assign({}, style, l.style || {}) });
                    });
                    facts.links = (facts.links || []).map(l => {
                        const style = styleForLinkType('physical', 'physical');
                        return Object.assign({}, l, { style: Object.assign({}, style, l.style || {}) });
                    });
                }

                this._showFactWarnings(facts);
                this._lastFacts = facts;
                this._lastPayload = buildCanvasPayload(facts, {
                    includeText: opts.includeText,
                    includeShapes: opts.includeShapes
                });
                this._showPreview();
            } catch (e) {
                this._log('Live collection failed: ' + (e.message || e));
                this._finishProgress('Failed');
            }
        }

        async _resolveAndMonitorLive() {
            const collected = this._collectLiveTargets();
            if (collected.targets.length === 0) {
                if (this.editor && this.editor.showToast) {
                    this.editor.showToast('No DUT targets specified', 'warning');
                }
                return;
            }
            this._showProgress('Resolving DUT targets...');
            try {
                const resolved = await this._resolveTargetsRemote(collected.targets);
                const list = resolved.resolved || [];
                this._log(`Resolved ${list.length} target(s):`);
                for (const r of list) {
                    this._log(
                        `  - ${r.hostname || r.deviceId}`
                        + (r.mgmt_ip ? ` (${r.mgmt_ip})` : '')
                        + (r.system_type ? ` [${r.system_type}]` : '')
                        + (r.resolved_via ? `  via ${r.resolved_via}` : '')
                        + (r.warnings && r.warnings.length ? `  warn: ${r.warnings.join('; ')}` : '')
                    );
                }
                this._registerMonitor(resolved.watch_ids || []);
                this._finishProgress(`Resolved ${list.length} DUT(s)`);
                this._refreshLiveSummary();
                if (this.editor && this.editor.showToast) {
                    this.editor.showToast(`Monitoring ${list.length} DUT(s)`, 'success');
                }
            } catch (e) {
                this._log('Resolve failed: ' + (e.message || e));
                this._finishProgress('Failed');
            }
        }

        async _resolveTargetsRemote(targets) {
            const active = (window.TopologySync && typeof window.TopologySync.getActive === 'function')
                ? window.TopologySync.getActive() : null;
            const userI = document.getElementById('gen-live-ssh-user');
            const passI = document.getElementById('gen-live-ssh-pass');
            const body = {
                targets: targets.map(t => ({
                    deviceId: t.deviceId || t.label || '',
                    host: t.host || '',
                    label: t.label || '',
                    source: t.source || 'manual',
                    ssh: t.ssh || null
                })),
                credentials: {
                    user: (userI && userI.value || '').trim() || 'dnroot',
                    password: (passI && passI.value) || 'dnroot'
                },
                domain_id: (active && active.domain_id) || '',
                topology_id: (active && active.topology_id) || ''
            };
            const resp = await _authFetch('/api/topology-generator/resolve-targets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            if (!resp.ok) {
                const txt = await resp.text();
                throw new Error(`resolve HTTP ${resp.status}: ${txt.slice(0, 200)}`);
            }
            return await resp.json();
        }

        _mergeResolvedWithTargets(rawTargets, resolved) {
            // Fold backend-resolved metadata into the original target
            // dicts so the live adapter can use canonical hostname,
            // serial, and mgmt_ip without re-resolving.
            const out = [];
            for (const t of rawTargets) {
                const sourceTarget = enrichTargetFromCanvas(this.editor, t);
                const appHost = getTargetSshHost(sourceTarget);
                const k = (t.deviceId || t.label || t.host || '').toLowerCase();
                let r = resolved.find(x => (x.deviceId || '').toLowerCase() === k
                    || (x.hostname || '').toLowerCase() === k
                    || (x.mgmt_ip || '').toLowerCase() === k);
                if (!r) r = {};
                const resolvedHost = r.mgmt_ip || appHost || sourceTarget.host || '';
                const resolvedSsh = r.ssh || null;
                out.push(Object.assign({}, sourceTarget, {
                    deviceId: r.hostname || r.deviceId || sourceTarget.deviceId,
                    hostname: r.hostname || sourceTarget.label || sourceTarget.deviceId,
                    host: resolvedHost,
                    serial: r.serial || '',
                    system_type: r.system_type || '',
                    dnos_version: r.dnos_version || '',
                    role: r.role || '',
                    ssh: sourceTarget.ssh ? Object.assign({}, sourceTarget.ssh, clonePlain(resolvedSsh || {}), {
                        host: resolvedHost,
                        hostBackup: (resolvedSsh && resolvedSsh.hostBackup) || sourceTarget.ssh.hostBackup || '',
                        user: (resolvedSsh && resolvedSsh.user) || sourceTarget.ssh.user || r.ssh_user || 'dnroot',
                        password: (resolvedSsh && resolvedSsh.password) || sourceTarget.ssh.password || r.ssh_password || 'dnroot'
                    }) : (resolvedSsh || r.mgmt_ip ? {
                        host: (resolvedSsh && resolvedSsh.host) || r.mgmt_ip,
                        hostBackup: (resolvedSsh && resolvedSsh.hostBackup) || r.serial || '',
                        user: r.ssh_user || 'dnroot',
                        password: r.ssh_password || 'dnroot'
                    } : null)
                }));
            }
            return out;
        }

        _registerMonitor(watchIds) {
            const ids = (watchIds || []).filter(Boolean);
            if (!ids.length) return;
            try {
                if (window.TopologyDeviceEvents
                    && typeof window.TopologyDeviceEvents.setWatchedDevices === 'function') {
                    // Merge with existing canvas device watchers so
                    // we don't drop the user's running monitoring set
                    // when they trigger Resolve Only for a small
                    // subset of DUTs.
                    const existing = new Set();
                    const objs = (this.editor && this.editor.objects) || [];
                    objs.forEach(o => {
                        if (o.type === 'device' && o.label) existing.add(o.label);
                    });
                    ids.forEach(id => existing.add(id));
                    const active = window.TopologySync && typeof window.TopologySync.getActive === 'function'
                        ? window.TopologySync.getActive() : null;
                    window.TopologyDeviceEvents.setWatchedDevices(
                        Array.from(existing),
                        { topologyId: active && active.topology_id }
                    );
                    this._log(`Watching ${existing.size} device(s) (added ${ids.length}).`);
                }
            } catch (e) {
                this._log('Monitor registration failed: ' + (e.message || e));
            }
        }

        _materializeOnCanvas(resolvedList) {
            // Add each resolved DUT to the canvas if it isn't already
            // present. Existing devices are matched by hostname or
            // serial (case-insensitive) so re-resolving doesn't create
            // duplicates. New devices land at a small offset from the
            // current viewport center so they're easy to find.
            if (!this.editor || !Array.isArray(this.editor.objects)) return;
            const objs = this.editor.objects;
            const byKey = new Map();
            for (const o of objs) {
                if (o.type !== 'device') continue;
                const k = (o.label || '').toLowerCase();
                if (k) byKey.set(k, o);
                if (o.deviceSerial) byKey.set(o.deviceSerial.toLowerCase(), o);
                if (o.sshConfig && o.sshConfig.host) byKey.set(o.sshConfig.host.toLowerCase(), o);
            }
            const baseX = 600, baseY = 400, gap = 180;
            let added = 0;
            for (const r of resolvedList) {
                const key = (r.hostname || '').toLowerCase();
                const altKey = (r.serial || '').toLowerCase();
                const ipKey = (r.mgmt_ip || '').toLowerCase();
                if ((key && byKey.has(key)) || (altKey && byKey.has(altKey)) || (ipKey && byKey.has(ipKey))) {
                    // Update SSH credentials on the existing device.
                    const existing = byKey.get(key) || byKey.get(altKey) || byKey.get(ipKey);
                    if (existing && r.mgmt_ip) {
                        existing.sshConfig = existing.sshConfig || {};
                        // SN host-lock: never push a mgmt IP into a
                        // device that has already verified an SN-based
                        // path. Even if `host` is empty here (it almost
                        // never is post-load), filling it with a stale
                        // IP would defeat the lock the operator just
                        // earned. Credentials are still safe to refresh.
                        const _snLocked = !!existing.sshConfig._snVerified;
                        if (!existing.sshConfig.host && !_snLocked) existing.sshConfig.host = r.mgmt_ip;
                        if (r.ssh_user && !existing.sshConfig.user) existing.sshConfig.user = r.ssh_user;
                        if (r.ssh_password && !existing.sshConfig.password) existing.sshConfig.password = r.ssh_password;
                    }
                    continue;
                }
                const cls = roleClassification(r.hostname, r.hostname, r.system_type);
                const id = `device_live_${Date.now()}_${added}`;
                const newDev = {
                    type: 'device',
                    id,
                    deviceType: 'router',
                    label: r.hostname || r.deviceId,
                    x: baseX + (added % 4) * gap,
                    y: baseY + Math.floor(added / 4) * 140,
                    radius: cls.radius || 40,
                    rotation: 0,
                    color: cls.color || '#3498db',
                    visualStyle: cls.visualStyle || 'classic',
                    role: cls.role,
                    locked: false,
                    deviceSerial: r.serial || '',
                    ip: r.mgmt_ip || '',
                    sshConfig: {
                        host: r.mgmt_ip || '',
                        user: r.ssh_user || 'dnroot',
                        password: r.ssh_password || 'dnroot'
                    },
                    _lldpData: { system_type: r.system_type, dnos_version: r.dnos_version }
                };
                objs.push(newDev);
                added++;
            }
            if (added > 0) {
                if (typeof this.editor.scheduleRender === 'function') {
                    try { this.editor.scheduleRender(); } catch (_) {}
                }
                if (typeof this.editor.render === 'function') {
                    try { this.editor.render(); } catch (_) {}
                }
                if (typeof this.editor.saveState === 'function') {
                    try { this.editor.saveState(); } catch (_) {}
                }
                this._log(`Materialized ${added} new DUT(s) on canvas.`);
            }
        }

        _mergeDnaasIntoLive(facts, dn) {
            if (!dn || !dn.devices || !facts) return;
            const byName = new Map();
            facts.devices.forEach(d => byName.set((d.hostname || '').toLowerCase(), d));
            const dnaasIdToFact = new Map();
            for (const dd of dn.devices) {
                const k = (dd.hostname || '').toLowerCase();
                let target = byName.get(k);
                if (!target) {
                    const cls = roleClassification(dd.hostname, dd.hostname, dd.system_type);
                    target = {
                        id: `live_dnaas_${facts.devices.length + 1}`,
                        hostname: dd.hostname,
                        role: cls.role, tier: cls.tier,
                        ip: dd.ip || '', mgmtIp: dd.mgmtIp || '',
                        serial: dd.serial || '',
                        system_type: dd.system_type || '',
                        dnos_version: dd.dnos_version || '',
                        color: cls.color, radius: cls.radius, visualStyle: cls.visualStyle,
                        ssh: null, groups: [], config: {}, monitoring: {},
                        _origin: 'dnaas-bd'
                    };
                    facts.devices.push(target);
                    byName.set(k, target);
                }
                dnaasIdToFact.set(dd.id, target);
            }
            for (const L of dn.links || []) {
                const a = dnaasIdToFact.get(L.fromDevice);
                const b = dnaasIdToFact.get(L.toDevice);
                if (!a || !b || a === b) continue;
                const dup = facts.physicalLinks.some(P =>
                    (P.fromDevice === a.id && P.toDevice === b.id) ||
                    (P.fromDevice === b.id && P.toDevice === a.id)
                );
                if (dup) continue;
                const link = Object.assign({}, L, {
                    fromDevice: a.id, toDevice: b.id,
                    layer: 'physical',
                    linkType: 'physical-dnaas',
                    style: { color: '#ff5e1f', style: 'solid', width: 2.5 }
                });
                facts.links.push(link);
                facts.physicalLinks.push(link);
            }
            for (const g of dn.groups || []) {
                const mapped = (g.members || [])
                    .map(fid => dnaasIdToFact.get(fid))
                    .filter(Boolean)
                    .map(d => d.id);
                if (mapped.length >= 2) {
                    facts.groups.push(Object.assign({}, g, { members: mapped }));
                }
            }
        }

        _generateFromImport() {
            this._showProgress('Parsing imported content...');
            this._log('source: import');
            const facts = adapterImport(this._importPayload || {});
            this._showFactWarnings(facts);
            this._lastFacts = facts;
            this._lastPayload = buildCanvasPayload(facts, {});
            this._showPreview();
        }

        _generateFromMapper() {
            this._showProgress('Reading LLDP discovery data...');
            this._log('source: mapper');
            const facts = adapterMapper(this.editor, {});
            this._showFactWarnings(facts);
            this._lastFacts = facts;
            this._lastPayload = buildCanvasPayload(facts, {});
            this._showPreview();
        }

        // ------------------------------------------------ preview / apply

        _showPreview() {
            this._finishProgress('Preview ready');
            const p = document.getElementById('gen-preview');
            if (!p || !this._lastPayload) return;
            p.style.display = 'block';
            const summary = document.getElementById('gen-preview-summary');
            const counts = document.getElementById('gen-preview-counts');
            const objs = this._lastPayload.objects;
            const devCount = objs.filter(o => o.type === 'device').length;
            const linkCount = objs.filter(o => o.type === 'link').length;
            const ulCount = objs.filter(o => o.type === 'unbound').length;
            const textCount = objs.filter(o => o.type === 'text').length;
            const shapeCount = objs.filter(o => o.type === 'shape').length;
            const desc = (this._lastPayload.metadata && this._lastPayload.metadata.description) || 'Generated topology';
            if (summary) {
                const report = this._lastPayload.metadata && this._lastPayload.metadata.compositionReport;
                summary.textContent = report
                    ? `${desc} | ${report.topologyFamily || 'architecture'} | score ${report.score}`
                    : desc;
            }
            if (counts) {
                counts.innerHTML = '';
                const pills = [
                    ['Devices', devCount],
                    ['Links', linkCount],
                    ['Unbound', ulCount],
                    ['Text', textCount],
                    ['Shapes', shapeCount]
                ];
                for (const [label, n] of pills) {
                    if (n === 0 && label !== 'Devices' && label !== 'Links') continue;
                    const span = document.createElement('span');
                    span.className = 'gen-count-pill';
                    span.textContent = `${label}: ${n}`;
                    counts.appendChild(span);
                }
            }
        }

        async _applyPayload() {
            if (!this._lastPayload) {
                this.editor.showToast('Nothing to apply', 'warning');
                return;
            }
            try {
                const placed = await this._placeGeneratedTopology({ loadAfterSave: true, mergeIntoCanvas: true });
                if (!placed) return;
                this._showGeneratedProtocolPanel();
                this.editor.showToast(
                    `Generated topology saved and merged into canvas: ${placed.domainName} / ${placed.name}`,
                    'success'
                );
                this._hideProgress();
                const p = document.getElementById('gen-preview');
                if (p) p.style.display = 'none';
            } catch (e) {
                this.editor.showToast('Apply failed: ' + (e.message || e), 'error');
            }
        }

        async _saveToDomain() {
            if (!this._lastPayload) return;
            try {
                const placed = await this._placeGeneratedTopology({ loadAfterSave: false });
                if (!placed) return;
                this.editor.showToast(`Saved "${placed.name}" to ${placed.domainName}`, 'success');
            } catch (e) {
                this.editor.showToast('Save failed: ' + (e.message || e), 'error');
            }
        }

        async _placeGeneratedTopology(opts = {}) {
            const placement = await this._chooseGeneratedPlacement();
            if (!placement) return null;
            const payload = clonePlain(this._lastPayload);
            payload.metadata = payload.metadata || {};
            payload.metadata.name = placement.name;
            payload.metadata.generatedPlacement = {
                sectionId: placement.section.id,
                domainName: placement.section.name,
                placedAt: new Date().toISOString()
            };
            const resp = await _authFetch('/api/topology-generator/save-via-mcp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    section_id: placement.section.id,
                    domain_name: placement.section.name,
                    name: placement.name,
                    state_json: payload,
                    avoid_duplicate: true
                })
            });
            const result = await resp.json().catch(() => ({}));
            if (!resp.ok || result.error) throw new Error(result.error || `HTTP ${resp.status}`);
            const savedName = result.name || placement.name;
            payload.metadata.name = savedName;
            this._lastPayload = payload;
            await this._saveLearningFromCurrent(opts.loadAfterSave ? 'apply-placement' : 'save-placement');
            if (opts.loadAfterSave) {
                try {
                    if (typeof this.editor.saveState === 'function') this.editor.saveState();
                } catch (_) {}
                if (opts.mergeIntoCanvas) {
                    this._mergeGeneratedPayloadIntoCanvas(payload);
                } else {
                    this.editor.loadTopologyFromData(payload, { domain: placement.section.name });
                }
                if (window.FileOps && typeof window.FileOps.updateTopologyIndicator === 'function') {
                    window.FileOps.updateTopologyIndicator(
                        savedName,
                        placement.section.name,
                        placement.section.color || '#9b59b6',
                        placement.section.id
                    );
                }
            }
            if (this.editor && typeof this.editor.loadCustomSections === 'function') {
                try { this.editor.loadCustomSections(); } catch (_) {}
            }
            return {
                sectionId: placement.section.id,
                domainName: placement.section.name,
                name: savedName,
                filename: result.filename || ''
            };
        }

        _mergeGeneratedPayloadIntoCanvas(payload) {
            if (!payload || !Array.isArray(payload.objects) || !this.editor || !Array.isArray(this.editor.objects)) {
                return { added: 0 };
            }
            const existing = this.editor.objects;
            const incoming = clonePlain(payload.objects || []);
            const existingIds = new Set(existing.map(o => o && o.id).filter(Boolean));
            const idMap = new Map();
            const makeId = (oldId, type, index) => {
                const base = String(oldId || `${type || 'obj'}_${index}`).replace(/[^a-zA-Z0-9_-]/g, '_') || `${type || 'obj'}_${index}`;
                if (!existingIds.has(base)) {
                    existingIds.add(base);
                    idMap.set(oldId, base);
                    return base;
                }
                let suffix = 2;
                let candidate = `${base}_gen${suffix}`;
                while (existingIds.has(candidate)) {
                    suffix++;
                    candidate = `${base}_gen${suffix}`;
                }
                existingIds.add(candidate);
                idMap.set(oldId, candidate);
                return candidate;
            };

            incoming.forEach((obj, index) => {
                obj.id = makeId(obj.id, obj.type, index);
            });
            incoming.forEach(obj => {
                if (obj.device1 && idMap.has(obj.device1)) obj.device1 = idMap.get(obj.device1);
                if (obj.device2 && idMap.has(obj.device2)) obj.device2 = idMap.get(obj.device2);
                if (obj.source && idMap.has(obj.source)) obj.source = idMap.get(obj.source);
                if (obj.target && idMap.has(obj.target)) obj.target = idMap.get(obj.target);
                if (obj.linkId && idMap.has(obj.linkId)) obj.linkId = idMap.get(obj.linkId);
                if (obj.groupLeaderId && idMap.has(obj.groupLeaderId)) obj.groupLeaderId = idMap.get(obj.groupLeaderId);
                obj._generatedMergedToCanvas = true;
            });

            const boundsOf = (items) => {
                const points = [];
                items.forEach(obj => {
                    if (!obj) return;
                    if (typeof obj.x === 'number' && typeof obj.y === 'number') {
                        const halfW = obj.type === 'shape' ? (obj.width || 120) / 2 : (obj.radius || 40);
                        const halfH = obj.type === 'shape' ? (obj.height || 80) / 2 : (obj.radius || 40);
                        points.push([obj.x - halfW, obj.y - halfH], [obj.x + halfW, obj.y + halfH]);
                    }
                    if (obj.start) points.push([obj.start.x, obj.start.y]);
                    if (obj.end) points.push([obj.end.x, obj.end.y]);
                });
                if (!points.length) return null;
                return points.reduce((acc, p) => ({
                    minX: Math.min(acc.minX, p[0]),
                    minY: Math.min(acc.minY, p[1]),
                    maxX: Math.max(acc.maxX, p[0]),
                    maxY: Math.max(acc.maxY, p[1]),
                }), { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity });
            };
            const existingBounds = boundsOf(existing);
            const incomingBounds = boundsOf(incoming);
            let dx = 0;
            let dy = 0;
            if (existingBounds && incomingBounds && existing.length > 0) {
                const overlaps = !(incomingBounds.minX > existingBounds.maxX + 120
                    || incomingBounds.maxX < existingBounds.minX - 120
                    || incomingBounds.minY > existingBounds.maxY + 120
                    || incomingBounds.maxY < existingBounds.minY - 120);
                if (overlaps) {
                    dx = Math.round(existingBounds.maxX - incomingBounds.minX + 180);
                    dy = Math.round(existingBounds.minY - incomingBounds.minY);
                }
            }
            if (dx || dy) {
                incoming.forEach(obj => {
                    if (typeof obj.x === 'number') obj.x += dx;
                    if (typeof obj.y === 'number') obj.y += dy;
                    if (obj.start) { obj.start.x += dx; obj.start.y += dy; }
                    if (obj.end) { obj.end.x += dx; obj.end.y += dy; }
                    if (obj.manualCurvePoint) { obj.manualCurvePoint.x += dx; obj.manualCurvePoint.y += dy; }
                    if (obj.manualControlPoint) { obj.manualControlPoint.x += dx; obj.manualControlPoint.y += dy; }
                    if (obj._cp1) { obj._cp1.x += dx; obj._cp1.y += dy; }
                    if (obj._cp2) { obj._cp2.x += dx; obj._cp2.y += dy; }
                });
            }

            existing.push(...incoming);
            this.editor.currentTopologyMetadata = Object.assign(
                {},
                this.editor.currentTopologyMetadata || {},
                payload.metadata || {}
            );
            this.editor.deviceIdCounter = Math.max(this.editor.deviceIdCounter || 0, existing.filter(o => o.type === 'device').length);
            this.editor.linkIdCounter = Math.max(this.editor.linkIdCounter || 0, existing.filter(o => o.type === 'link' || o.type === 'unbound').length);
            this.editor.textIdCounter = Math.max(this.editor.textIdCounter || 0, existing.filter(o => o.type === 'text').length);
            if (this.editor.groups && typeof this.editor.groups.validate === 'function') this.editor.groups.validate();
            if (typeof this.editor.draw === 'function') this.editor.draw();
            if (typeof this.editor.autoSave === 'function') this.editor.autoSave({ force: true });
            this._log(`Merged ${incoming.length} generated object(s) into canvas, including ${incoming.filter(o => o.type === 'shape').length} shape panel(s).`);
            return { added: incoming.length, dx, dy };
        }

        async _chooseGeneratedPlacement() {
            const sections = await this._listGeneratorSections();
            const active = (window.TopologySync && typeof window.TopologySync.getActive === 'function')
                ? window.TopologySync.getActive() : null;
            const defaultDomainId = active && active.section_id || '';
            const defaultSection = sections.find(s => s.id === defaultDomainId) || sections[0] || null;
            const choice = await this._showGeneratedPlacementDialog(sections, defaultSection);
            if (!choice) return null;
            let section = choice.section || null;
            if (!section && choice.newDomainName) {
                section = await this._createGeneratedDomain(choice.newDomainName);
            }
            if (!section) return null;
            const name = String(choice.name || '').trim();
            if (!name) {
                if (this.editor && this.editor.showToast) this.editor.showToast('Topology name is required', 'warning');
                return null;
            }
            return { section, name };
        }

        _showGeneratedPlacementDialog(sections, defaultSection) {
            return new Promise(resolve => {
                const previous = document.getElementById('gen-placement-modal');
                if (previous) previous.remove();

                const isDk = window.FileOps && typeof window.FileOps._menuDark === 'function'
                    ? window.FileOps._menuDark(this.editor)
                    : !!document.body.classList.contains('dark-mode');
                const t = {
                    bg: isDk ? 'linear-gradient(135deg, rgba(15,15,25,0.92), rgba(10,10,18,0.96))' : 'linear-gradient(135deg, rgba(255,255,255,0.95), rgba(240,240,245,0.98))',
                    border: isDk ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.08)',
                    text: isDk ? '#e2e8f0' : '#1e293b',
                    muted: isDk ? '#94a3b8' : '#64748b',
                    accent: '#6366f1',
                    accentBg: isDk ? 'rgba(99,102,241,0.14)' : 'rgba(99,102,241,0.10)',
                    accentBorder: isDk ? 'rgba(99,102,241,0.38)' : 'rgba(99,102,241,0.40)'
                };
                const icons = window.FileOps && typeof window.FileOps._sectionIcons === 'function'
                    ? window.FileOps._sectionIcons()
                    : [{ id: 'folder', svg: '<path d="M3 7h7l2 2h9v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" fill="none" stroke="currentColor" stroke-width="2"/>' }];
                const iconFor = section => (icons.find(i => i.id === section.icon) || icons[0]).svg;

                const modal = document.createElement('div');
                modal.id = 'gen-placement-modal';
                modal.setAttribute('role', 'dialog');
                modal.setAttribute('aria-modal', 'true');
                // Generate/Discover panel is inline z-index:999999; placement
                // must sit above it so the domain picker is never hidden.
                modal.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);backdrop-filter:blur(6px);z-index:1000002;display:flex;align-items:center;justify-content:center;';

                const content = document.createElement('div');
                content.className = 'gen-placement-modal-card';
                content.style.cssText = `background:${t.bg};border:1px solid ${t.border};border-radius:14px;padding:20px;min-width:340px;max-width:400px;box-shadow:0 12px 48px rgba(0,0,0,0.3);backdrop-filter:blur(16px);font-family:'Poppins',-apple-system,sans-serif;`;

                const title = document.createElement('div');
                title.textContent = 'Place Generated Topology';
                title.style.cssText = `font-size:15px;font-weight:600;color:${t.text};margin-bottom:4px;`;
                const subtitle = document.createElement('div');
                subtitle.textContent = sections.length ? 'Select a domain for the generated topology' : 'You have no domains yet. Create one to continue.';
                subtitle.style.cssText = `font-size:11px;color:${t.muted};margin-bottom:14px;`;
                const domainsWrap = document.createElement('div');
                domainsWrap.style.cssText = 'display:flex;flex-direction:column;gap:6px;margin-bottom:10px;max-height:260px;overflow:auto;';

                let selectedSection = defaultSection || sections[0] || null;
                let newDomainMode = false;
                const rows = [];
                const setRowState = () => {
                    rows.forEach(({ btn, section }) => {
                        const color = section.color || '#6366f1';
                        const selected = !newDomainMode && selectedSection && selectedSection.id === section.id;
                        btn.style.background = selected ? `${color}1f` : `${color}0d`;
                        btn.style.borderColor = selected ? `${color}70` : `${color}30`;
                        btn.style.boxShadow = selected ? `0 0 0 1px ${color}55` : 'none';
                    });
                    newDomainBtn.style.boxShadow = newDomainMode ? `0 0 0 1px ${t.accent}` : 'none';
                    newDomainInput.style.display = newDomainMode ? 'block' : 'none';
                };

                sections.forEach(section => {
                    const color = section.color || '#6366f1';
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.style.cssText = `display:flex;align-items:center;gap:10px;padding:10px 12px;background:${color}0d;border:1px solid ${color}30;border-left:3px solid ${color};border-radius:8px;cursor:pointer;transition:all 0.15s;width:100%;text-align:left;`;
                    btn.innerHTML = `
                        <div style="width:28px;height:28px;border-radius:6px;background:${color}18;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                            <svg viewBox="0 0 24 24" width="14" height="14" style="stroke:${color};color:${color};">${iconFor(section)}</svg>
                        </div>
                        <span style="font-size:13px;font-weight:500;color:${t.text};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(section.name)}${defaultSection && section.id === defaultSection.id ? ' (current)' : ''}</span>
                    `;
                    btn.onclick = () => {
                        selectedSection = section;
                        newDomainMode = false;
                        setRowState();
                    };
                    btn.onmouseenter = () => {
                        if (!(selectedSection && selectedSection.id === section.id && !newDomainMode)) {
                            btn.style.background = `${color}1a`;
                            btn.style.borderColor = `${color}60`;
                        }
                    };
                    btn.onmouseleave = setRowState;
                    rows.push({ btn, section });
                    domainsWrap.appendChild(btn);
                });

                const newDomainBtn = document.createElement('button');
                newDomainBtn.type = 'button';
                newDomainBtn.title = 'Create a new topology domain';
                newDomainBtn.style.cssText = `display:flex;align-items:center;gap:10px;padding:10px 12px;width:100%;text-align:left;background:${t.accentBg};border:1px dashed ${t.accentBorder};border-left:3px solid ${t.accent};border-radius:8px;cursor:pointer;transition:all 0.15s ease;margin-bottom:10px;`;
                newDomainBtn.innerHTML = `
                    <div style="width:28px;height:28px;border-radius:6px;background:${isDk ? 'rgba(99,102,241,0.20)' : 'rgba(99,102,241,0.15)'};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                        <svg viewBox="0 0 24 24" width="14" height="14" style="stroke:${t.accent};color:${t.accent};" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="12" y1="5" x2="12" y2="19"></line>
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                        </svg>
                    </div>
                    <div style="flex:1;min-width:0;">
                        <div style="font-size:13px;font-weight:600;color:${t.accent};">New domain...</div>
                        <div style="font-size:10.5px;color:${t.muted};margin-top:1px;">Create and save generated topology there</div>
                    </div>
                `;

                const newDomainInput = document.createElement('input');
                newDomainInput.type = 'text';
                newDomainInput.placeholder = 'New domain name';
                newDomainInput.value = 'Generated Topologies';
                newDomainInput.style.cssText = `display:none;width:100%;box-sizing:border-box;margin:0 0 10px;padding:8px 10px;border:1px solid ${t.border};border-radius:8px;background:${isDk ? 'rgba(15,23,42,0.45)' : 'rgba(255,255,255,0.88)'};color:${t.text};font-size:12px;`;

                newDomainBtn.onclick = () => {
                    selectedSection = null;
                    newDomainMode = true;
                    setRowState();
                    newDomainInput.focus();
                    newDomainInput.select();
                };

                const nameWrap = document.createElement('label');
                nameWrap.style.cssText = 'display:flex;flex-direction:column;gap:5px;margin-bottom:10px;';
                const nameTitle = document.createElement('span');
                nameTitle.textContent = 'Topology name';
                nameTitle.style.cssText = `font-size:11px;font-weight:600;color:${t.muted};`;
                const nameInput = document.createElement('input');
                nameInput.type = 'text';
                nameInput.value = this._defaultGeneratedTopologyName((selectedSection && selectedSection.name) || newDomainInput.value);
                nameInput.style.cssText = `width:100%;box-sizing:border-box;padding:8px 10px;border:1px solid ${t.border};border-radius:8px;background:${isDk ? 'rgba(15,23,42,0.45)' : 'rgba(255,255,255,0.88)'};color:${t.text};font-size:12px;`;
                nameWrap.appendChild(nameTitle);
                nameWrap.appendChild(nameInput);

                const error = document.createElement('div');
                error.style.cssText = 'display:none;margin:0 0 10px;padding:8px 10px;border-radius:8px;background:rgba(244,63,94,0.12);border:1px solid rgba(244,63,94,0.28);color:#fca5a5;font-size:11px;';

                const footer = document.createElement('div');
                footer.style.cssText = 'display:flex;gap:8px;justify-content:flex-end;';
                const cancel = document.createElement('button');
                cancel.type = 'button';
                cancel.textContent = 'Cancel';
                cancel.style.cssText = `padding:7px 14px;background:transparent;border:1px solid ${t.border};border-radius:8px;color:${t.text};cursor:pointer;font-size:12px;`;
                const save = document.createElement('button');
                save.type = 'button';
                save.textContent = 'Save Topology';
                save.style.cssText = `padding:7px 14px;background:${t.accent};border:1px solid ${t.accent};border-radius:8px;color:#fff;cursor:pointer;font-size:12px;font-weight:600;`;
                footer.appendChild(cancel);
                footer.appendChild(save);

                content.appendChild(title);
                content.appendChild(subtitle);
                content.appendChild(domainsWrap);
                content.appendChild(newDomainBtn);
                content.appendChild(newDomainInput);
                content.appendChild(nameWrap);
                content.appendChild(error);
                content.appendChild(footer);
                modal.appendChild(content);
                document.body.appendChild(modal);
                setRowState();

                const cleanup = value => {
                    document.removeEventListener('keydown', onKey);
                    modal.remove();
                    resolve(value);
                };
                const showError = msg => {
                    error.textContent = msg;
                    error.style.display = 'block';
                };
                const submit = () => {
                    const topologyName = String(nameInput.value || '').trim();
                    if (!topologyName) {
                        showError('Topology name is required.');
                        nameInput.focus();
                        return;
                    }
                    if (newDomainMode) {
                        const newName = String(newDomainInput.value || '').trim();
                        if (!newName) {
                            showError('New domain name is required.');
                            newDomainInput.focus();
                            return;
                        }
                        cleanup({ section: null, newDomainName: newName, name: topologyName });
                        return;
                    }
                    if (!selectedSection) {
                        showError('Choose a destination domain.');
                        return;
                    }
                    cleanup({ section: selectedSection, name: topologyName });
                };
                const onKey = e => {
                    if (e.key === 'Escape') cleanup(null);
                    if ((e.key === 'Enter') && (e.ctrlKey || e.metaKey)) submit();
                };
                document.addEventListener('keydown', onKey);
                cancel.addEventListener('click', () => cleanup(null));
                save.addEventListener('click', submit);
                modal.addEventListener('click', e => {
                    if (e.target === modal) cleanup(null);
                });
                setTimeout(() => nameInput.focus(), 0);
            });
        }

        async _listGeneratorSections() {
            const resp = await _authFetch('/api/sections');
            const data = await resp.json().catch(() => ({}));
            if (!resp.ok || data.error) throw new Error(data.error || `sections HTTP ${resp.status}`);
            return (data.sections || []).filter(s => s && s.id && s.name && !s._isSharedIn && !s._isInbox);
        }

        _defaultGeneratedTopologyName(domainName) {
            const src = this._lastFacts && this._lastFacts.provenance && this._lastFacts.provenance.source || 'generator';
            const report = this._lastFacts && this._lastFacts.compositionReport || {};
            const family = report.topologyFamily || 'topology';
            const ts = new Date().toISOString().slice(0, 16).replace('T', ' ');
            return `Generated ${family} (${src}) - ${ts}`;
        }

        async _createGeneratedDomainPrompt(defaultName) {
            const suggested = defaultName || 'Generated Topologies';
            return await this._createGeneratedDomain(suggested);
        }

        async _createGeneratedDomain(name) {
            const cleanName = String(name || '').trim();
            if (!cleanName) {
                if (this.editor && this.editor.showToast) this.editor.showToast('Domain name is required', 'warning');
                return null;
            }
            return await this._ensureGeneratorSection(cleanName);
        }

        async _chooseSaveSection() {
            const active = (window.TopologySync && typeof window.TopologySync.getActive === 'function')
                ? window.TopologySync.getActive() : null;
            const sections = await this._listGeneratorSections();
            const defaultSection = sections.find(s => s.name === (active && active.domain_name))
                || sections.find(s => s.id === (active && active.section_id))
                || sections[0]
                || null;
            const placement = await this._showGeneratedPlacementDialog(sections, defaultSection);
            if (!placement) return null;
            const section = placement.section || await this._createGeneratedDomain(placement.newDomainName);
            return section && section.id;
        }

        async _ensureGeneratorSection(domainName) {
            try {
                const r = await _authFetch('/api/sections');
                const data = await r.json();
                const sections = data.sections || [];
                const wanted = String(domainName || 'Generated Topologies').trim() || 'Generated Topologies';
                const existing = sections.find(s => String(s.name || '').toLowerCase() === wanted.toLowerCase());
                if (existing) return existing;
                const cr = await _authFetch('/api/sections', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: wanted, color: '#9b59b6', icon: 'git-branch' })
                });
                const created = await cr.json();
                if (!cr.ok || created.error) throw new Error(created.error || `HTTP ${cr.status}`);
                if (this.editor.loadCustomSections) this.editor.loadCustomSections();
                return created.section || created;
            } catch (e) {
                throw new Error('Could not create generated topology domain: ' + e.message);
            }
        }

        _generatedVisibilityStorageKey() {
            const active = (window.TopologySync && typeof window.TopologySync.getActive === 'function')
                ? window.TopologySync.getActive() : null;
            const user = (window.TopologyAuth && window.TopologyAuth.currentUser && window.TopologyAuth.currentUser.username)
                || 'default';
            return `topology_generator_visibility_${user}_${(active && active.topology_id) || 'local'}`;
        }

        _loadGeneratedVisibilityState() {
            try { return JSON.parse(localStorage.getItem(this._generatedVisibilityStorageKey()) || '{}') || {}; }
            catch (_) { return {}; }
        }

        _saveGeneratedVisibilityState(state) {
            try { localStorage.setItem(this._generatedVisibilityStorageKey(), JSON.stringify(state || {})); } catch (_) {}
        }

        _refreshGeneratedVisibilityFromState(state) {
            if (!this.editor || !Array.isArray(this.editor.objects)) return;
            state = state || this._loadGeneratedVisibilityState();
            const meta = (this.editor.currentTopologyMetadata || (this._lastPayload && this._lastPayload.metadata) || {});
            const groups = meta.generatedProtocolGroups || [];
            const groupById = new Map(groups.map(g => [g.id, g]));
            const selectedMode = state.__bgpOverlayMode || meta.generatedOverlayDefaultMode || 'real-legs';
            const wantedModes = selectedMode === 'both' ? new Set(['real-legs', 'via-rr']) : new Set([selectedMode]);
            const confidenceState = state.__confidence || {};
            const defaultHiddenByGroup = id => {
                const g = groupById.get(id) || {};
                return g.visible === false || g.layer === 'evidence' || g.kind === 'perimeter' || String(id || '').startsWith('perimeter:');
            };
            this.editor.objects.forEach(obj => {
                if (!obj || !obj._generatedTopologyObject) return;
                const groupHidden = Array.isArray(obj._generatedGroupIds) && obj._generatedGroupIds.some(id => {
                    if (state[id] === true) return false;
                    if (state[id] === false) return true;
                    return defaultHiddenByGroup(id);
                });
                const conf = obj._generatedConfidence || 'correlated';
                const confidenceHidden = confidenceState[conf] === false;
                const overlayHidden = !!obj._overlayMode && !wantedModes.has(obj._overlayMode);
                obj._hidden = groupHidden || confidenceHidden || overlayHidden;
            });
            this.editor.objects.forEach(obj => {
                if (obj && obj.type === 'text' && obj.linkId) {
                    const parent = this.editor.objects.find(l => l.id === obj.linkId);
                    if (parent && parent._generatedTopologyObject) obj._hidden = !!parent._hidden || !!obj._hidden;
                }
            });
            if (typeof this.editor.draw === 'function') this.editor.draw();
        }

        _setGeneratedGroupVisibility(groupId, visible) {
            if (!this.editor || !Array.isArray(this.editor.objects)) return;
            const state = this._loadGeneratedVisibilityState();
            state[groupId] = !!visible;
            this._saveGeneratedVisibilityState(state);
            this._refreshGeneratedVisibilityFromState(state);
        }

        _setGeneratedOverlayMode(mode) {
            if (!this.editor || !Array.isArray(this.editor.objects)) return;
            const state = this._loadGeneratedVisibilityState();
            state.__bgpOverlayMode = mode || 'real-legs';
            this._saveGeneratedVisibilityState(state);
            this._refreshGeneratedVisibilityFromState(state);
        }

        _setGeneratedConfidenceVisibility(confidence, visible) {
            const state = this._loadGeneratedVisibilityState();
            state.__confidence = state.__confidence || {};
            state.__confidence[confidence] = !!visible;
            this._saveGeneratedVisibilityState(state);
            this._refreshGeneratedVisibilityFromState(state);
        }

        _applyGeneratedPreset(preset) {
            const meta = (this.editor && this.editor.currentTopologyMetadata) || (this._lastPayload && this._lastPayload.metadata) || {};
            const groups = meta.generatedProtocolGroups || [];
            const state = this._loadGeneratedVisibilityState();
            const allow = {
                clean: g => ['device', 'physical', 'underlay', 'service'].includes(g.layer) || g.id === 'layer:labels',
                routing: g => ['device', 'physical', 'underlay', 'routing', 'overlay', 'identity', 'service'].includes(g.layer) || g.id === 'layer:labels' || g.id === 'layer:services',
                services: g => ['device', 'physical', 'underlay', 'service'].includes(g.layer) || g.id === 'layer:labels',
                evidence: g => ['device', 'physical', 'underlay', 'routing', 'service', 'evidence'].includes(g.layer) || g.kind === 'perimeter' || g.id === 'layer:labels',
                full: () => true
            }[preset] || (() => true);
            groups.forEach(g => { state[g.id] = !!allow(g); });
            state.__confidence = {
                verified: true,
                correlated: true,
                inferred: preset !== 'clean',
                missing: preset === 'full'
            };
            if (preset === 'clean') state.__bgpOverlayMode = 'real-legs';
            if (preset === 'full') state.__bgpOverlayMode = 'both';
            this._saveGeneratedVisibilityState(state);
            this._refreshGeneratedVisibilityFromState(state);
            this._showGeneratedProtocolPanel();
        }

        _setGeneratedGroupsByKind(kind, visible) {
            const meta = (this.editor && this.editor.currentTopologyMetadata) || (this._lastPayload && this._lastPayload.metadata) || {};
            const groups = meta.generatedProtocolGroups || [];
            groups.filter(g => !kind || g.kind === kind || g.layer === kind).forEach(g => this._setGeneratedGroupVisibility(g.id, visible));
        }

        _showGeneratedProtocolPanel() {
            if (!this.editor || !this.editor.canvas || !Array.isArray(this.editor.objects)) return;
            const existing = document.getElementById('generated-protocol-panel');
            if (existing) existing.remove();
            const metadata = (this._lastPayload && this._lastPayload.metadata) || {};
            const groups = metadata.generatedProtocolGroups || [];
            if (!groups.length) return;
            this.editor.currentTopologyMetadata = Object.assign({}, this.editor.currentTopologyMetadata || {}, metadata, {
                generatedProtocolGroups: groups
            });
            // First-load default: if there's no saved visibility state
            // for this (user, topology_id) pair, auto-apply the
            // 'routing' preset so the panel opens with a sensible
            // de-cluttered view (Devices + Underlay + BGP + EVPN, hide
            // Evidence and Perimeter). The user can flip to Clean or
            // Full at any time and that choice persists.
            let state = this._loadGeneratedVisibilityState();
            if (!state || !Object.keys(state).length) {
                this._applyGeneratedPreset('routing');
                state = this._loadGeneratedVisibilityState();
            }
            const panel = document.createElement('div');
            panel.id = 'generated-protocol-panel';
            panel.className = 'generated-protocol-panel';
            const title = document.createElement('div');
            title.className = 'generated-protocol-panel__title';
            title.textContent = 'Generated Topology';
            panel.appendChild(title);
            const actions = document.createElement('div');
            actions.className = 'generated-protocol-panel__actions generated-protocol-panel__presets';
            const makeAction = (label, cls, cb) => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.textContent = label;
                btn.className = 'generated-protocol-panel__btn' + (cls ? (' ' + cls) : '');
                btn.onclick = cb;
                actions.appendChild(btn);
            };
            makeAction('Clean', '', () => this._applyGeneratedPreset('clean'));
            makeAction('Routing', 'generated-protocol-panel__btn--muted', () => this._applyGeneratedPreset('routing'));
            makeAction('Services', 'generated-protocol-panel__btn--muted', () => this._applyGeneratedPreset('services'));
            makeAction('Evidence', 'generated-protocol-panel__btn--muted', () => this._applyGeneratedPreset('evidence'));
            makeAction('Full', 'generated-protocol-panel__btn--muted', () => this._applyGeneratedPreset('full'));
            const evidenceBlock = document.createElement('div');
            evidenceBlock.className = 'generated-protocol-panel__evidence';
            const cr = metadata.correlationEvidence || {};
            const rep = metadata.compositionReport || {};
            const lines = [];
            if (cr.topologyFamily) lines.push(`Family: ${cr.topologyFamily}`);
            if (cr.logicalLinkCount != null) lines.push(`Logical links: ${cr.logicalLinkCount}`);
            if (cr.serviceCount != null) lines.push(`Services: ${cr.serviceCount}`);
            if (rep.skippedDevices && rep.skippedDevices.length) {
                lines.push(`Skipped: ${rep.skippedDevices.length}`);
            }
            if (rep.unmatchedDevices && rep.unmatchedDevices.length) {
                lines.push(`Unmatched DUTs: ${rep.unmatchedDevices.length}`);
            }
            evidenceBlock.textContent = lines.length ? lines.join(' · ') : 'Evidence: local compose (no backend metadata)';
            makeAction('Evidence Text', 'generated-protocol-panel__btn--toggle', () => {
                evidenceBlock.style.display = evidenceBlock.style.display === 'none' ? '' : 'none';
            });
            panel.appendChild(actions);
            const quality = metadata.generatedSceneQuality || {};
            const confCounts = quality.confidenceCounts || {};
            const confidenceRow = document.createElement('div');
            confidenceRow.className = 'generated-protocol-panel__confidence';
            ['verified', 'correlated', 'inferred', 'missing'].forEach(conf => {
                const label = document.createElement('label');
                label.className = `generated-protocol-panel__chip generated-protocol-panel__chip--${conf}`;
                const input = document.createElement('input');
                input.type = 'checkbox';
                input.checked = !state.__confidence || state.__confidence[conf] !== false;
                input.onchange = () => this._setGeneratedConfidenceVisibility(conf, input.checked);
                const span = document.createElement('span');
                span.textContent = `${conf} ${confCounts[conf] || 0}`;
                label.appendChild(input);
                label.appendChild(span);
                confidenceRow.appendChild(label);
            });
            panel.appendChild(confidenceRow);
            panel.appendChild(evidenceBlock);
            const overlayModes = metadata.generatedOverlayModes || [];
            if (overlayModes.length) {
                const title = document.createElement('div');
                title.className = 'generated-protocol-panel__subtitle';
                title.textContent = 'BGP Overlay';
                panel.appendChild(title);
                const overlayRow = document.createElement('div');
                overlayRow.className = 'generated-protocol-panel__bgp-overlay-radios';
                const selectedMode = state.__bgpOverlayMode || metadata.generatedOverlayDefaultMode || 'real-legs';
                overlayModes.forEach(mode => {
                    const label = document.createElement('label');
                    label.className = 'generated-protocol-panel__radio';
                    const input = document.createElement('input');
                    input.type = 'radio';
                    input.name = 'generated-bgp-overlay-mode';
                    input.value = mode.id;
                    input.checked = mode.id === selectedMode;
                    input.onchange = () => {
                        if (input.checked) this._setGeneratedOverlayMode(mode.id);
                    };
                    const span = document.createElement('span');
                    span.textContent = mode.label || mode.id;
                    label.appendChild(input);
                    label.appendChild(span);
                    overlayRow.appendChild(label);
                });
                panel.appendChild(overlayRow);
            }
            // -------------------------------------------------------------
            // Helpers: visibility resolution + row rendering
            // -------------------------------------------------------------
            const isVisible = (g) => Object.prototype.hasOwnProperty.call(state, g.id)
                ? state[g.id] !== false
                : g.visible !== false;

            const renderGroupRow = (group, target, opts) => {
                opts = opts || {};
                const row = document.createElement('label');
                row.className = 'generated-protocol-panel__row generated-protocol-panel__row--' + (group.kind || 'other');
                if (opts.indent) row.classList.add('generated-protocol-panel__row--child');
                const cb = document.createElement('input');
                cb.type = 'checkbox';
                cb.checked = isVisible(group);
                cb.style.accentColor = group.color || '#06b6d4';
                cb.onchange = () => this._setGeneratedGroupVisibility(group.id, cb.checked);
                const swatch = document.createElement('span');
                swatch.className = 'generated-protocol-panel__swatch';
                swatch.style.background = group.color || '#06b6d4';
                const txt = document.createElement('span');
                txt.className = 'generated-protocol-panel__row-label';
                const count = group.count || (group.objectIds || []).length || 0;
                const warnings = group.warningCount ? ` !${group.warningCount}` : '';
                txt.textContent = `${opts.labelOverride || group.label || group.id} (${count})${warnings}`;
                row.appendChild(cb);
                row.appendChild(swatch);
                row.appendChild(txt);
                (target || panel).appendChild(row);
                return row;
            };

            // Master "tri-state" row: a synthetic toggle that flips every
            // child group at once. It does NOT live in `state` itself
            // (children own the truth) but reflects whether ANY child is
            // visible, and toggles ALL children when clicked.
            const renderMasterRow = (label, color, children, target) => {
                if (!children.length) return null;
                const row = document.createElement('label');
                row.className = 'generated-protocol-panel__row generated-protocol-panel__row--master';
                const cb = document.createElement('input');
                cb.type = 'checkbox';
                const anyVisible = children.some(isVisible);
                cb.checked = anyVisible;
                cb.style.accentColor = color || '#06b6d4';
                cb.onchange = () => {
                    const turnOn = cb.checked;
                    children.forEach(c => this._setGeneratedGroupVisibility(c.id, turnOn));
                };
                const swatch = document.createElement('span');
                swatch.className = 'generated-protocol-panel__swatch';
                swatch.style.background = color || '#06b6d4';
                const txt = document.createElement('span');
                txt.className = 'generated-protocol-panel__row-label';
                const totalCount = children.reduce((s, g) => s + (g.count || (g.objectIds || []).length || 0), 0);
                txt.textContent = `${label} (${totalCount})`;
                row.appendChild(cb);
                row.appendChild(swatch);
                row.appendChild(txt);
                (target || panel).appendChild(row);
                return row;
            };

            // -------------------------------------------------------------
            // Group classification
            // -------------------------------------------------------------
            const layerGroups = groups
                .filter(g => g.kind === 'layer')
                .sort((a, b) => String(a.label || a.id).localeCompare(String(b.label || b.id)));
            const protocolGroups = groups.filter(g => g.kind === 'protocol');
            const afGroups = groups.filter(g => g.kind === 'af')
                .sort((a, b) => String(a.label || a.id).localeCompare(String(b.label || b.id)));
            const serviceGroups = groups.filter(g => g.kind === 'service')
                .sort((a, b) => String(a.label || a.id).localeCompare(String(b.label || b.id)));
            const perimeterGroups = groups.filter(g => g.kind === 'perimeter')
                .sort((a, b) => String(a.label || a.id).localeCompare(String(b.label || b.id)));
            const otherGroups = groups
                .filter(g => !['layer', 'protocol', 'af', 'service', 'perimeter'].includes(g.kind))
                .sort((a, b) => String(a.label || a.id).localeCompare(String(b.label || b.id)));

            const familyOf = (g) => g.family || 'other';
            const bgpProto = protocolGroups.filter(g => familyOf(g) === 'bgp');
            const igpProto = protocolGroups.filter(g => familyOf(g) === 'igp');
            const mplsProto = protocolGroups.filter(g => familyOf(g) === 'mpls');
            const physProto = protocolGroups.filter(g => familyOf(g) === 'physical');
            const staticProto = protocolGroups.filter(g => familyOf(g) === 'static');
            const identityProto = protocolGroups.filter(g => familyOf(g) === 'identity');
            const otherProto = protocolGroups.filter(g => !['bgp', 'igp', 'mpls', 'physical', 'static', 'identity'].includes(familyOf(g)));

            // -------------------------------------------------------------
            // Render: Layers
            // -------------------------------------------------------------
            if (layerGroups.length) {
                const sec = document.createElement('details');
                sec.className = 'generated-protocol-panel__accordion';
                sec.open = true;
                const sum = document.createElement('summary');
                sum.className = 'generated-protocol-panel__subtitle';
                const total = layerGroups.reduce((s, g) => s + (g.count || (g.objectIds || []).length || 0), 0);
                sum.textContent = `Layers (${total})`;
                sec.appendChild(sum);
                layerGroups.forEach(g => renderGroupRow(g, sec));
                panel.appendChild(sec);
            }

            // -------------------------------------------------------------
            // Render: Protocols (tree)
            //   Underlay master   -> IGP + MPLS + Static + Physical children
            //   BGP master        -> AFI/SAFI children
            //   Identity / Other  -> flat rows
            // -------------------------------------------------------------
            if (protocolGroups.length || afGroups.length) {
                const sec = document.createElement('details');
                sec.className = 'generated-protocol-panel__accordion';
                sec.open = true;
                const sum = document.createElement('summary');
                sum.className = 'generated-protocol-panel__subtitle';
                const total = (protocolGroups.length + afGroups.length);
                sum.textContent = `Protocols (${total})`;
                sec.appendChild(sum);

                // ----- Underlay master + children -----
                const underlayChildren = [...physProto, ...igpProto, ...mplsProto, ...staticProto];
                if (underlayChildren.length) {
                    const underlayBlock = document.createElement('div');
                    underlayBlock.className = 'generated-protocol-panel__group';
                    renderMasterRow('Underlay', '#5dade2', underlayChildren, underlayBlock);
                    // Sub-buckets so user can see what KIND of underlay
                    // edge each row is (IGP / MPLS / Static / Physical).
                    const renderSubBucket = (label, items) => {
                        if (!items.length) return;
                        const sub = document.createElement('div');
                        sub.className = 'generated-protocol-panel__subbucket';
                        const heading = document.createElement('div');
                        heading.className = 'generated-protocol-panel__subbucket-title';
                        heading.textContent = label;
                        sub.appendChild(heading);
                        items.sort((a, b) => String(a.label || a.id).localeCompare(String(b.label || b.id)));
                        items.forEach(g => renderGroupRow(g, sub, { indent: true }));
                        underlayBlock.appendChild(sub);
                    };
                    renderSubBucket('IGP', igpProto);
                    renderSubBucket('MPLS', mplsProto);
                    renderSubBucket('Static', staticProto);
                    renderSubBucket('Physical', physProto);
                    sec.appendChild(underlayBlock);
                }

                // ----- BGP master + AF children -----
                if (bgpProto.length || afGroups.length) {
                    const bgpBlock = document.createElement('div');
                    bgpBlock.className = 'generated-protocol-panel__group';
                    const bgpChildren = [...bgpProto, ...afGroups];
                    renderMasterRow('BGP', '#3498db', bgpChildren, bgpBlock);
                    // Render the bare BGP edges first (if any), then AFs.
                    if (bgpProto.length) {
                        bgpProto.sort((a, b) => String(a.label || a.id).localeCompare(String(b.label || b.id)));
                        bgpProto.forEach(g => renderGroupRow(g, bgpBlock, { indent: true }));
                    }
                    if (afGroups.length) {
                        const sub = document.createElement('div');
                        sub.className = 'generated-protocol-panel__subbucket';
                        const heading = document.createElement('div');
                        heading.className = 'generated-protocol-panel__subbucket-title';
                        heading.textContent = 'AFI/SAFI';
                        sub.appendChild(heading);
                        afGroups.forEach(g => renderGroupRow(g, sub, { indent: true }));
                        bgpBlock.appendChild(sub);
                    }
                    sec.appendChild(bgpBlock);
                }

                // ----- Identity / Other protocol rows (flat) -----
                if (identityProto.length) {
                    const block = document.createElement('div');
                    block.className = 'generated-protocol-panel__group';
                    const heading = document.createElement('div');
                    heading.className = 'generated-protocol-panel__subbucket-title';
                    heading.textContent = 'Identity';
                    block.appendChild(heading);
                    identityProto.sort((a, b) => String(a.label || a.id).localeCompare(String(b.label || b.id)));
                    identityProto.forEach(g => renderGroupRow(g, block));
                    sec.appendChild(block);
                }
                if (otherProto.length) {
                    const block = document.createElement('div');
                    block.className = 'generated-protocol-panel__group';
                    const heading = document.createElement('div');
                    heading.className = 'generated-protocol-panel__subbucket-title';
                    heading.textContent = 'Other';
                    block.appendChild(heading);
                    otherProto.sort((a, b) => String(a.label || a.id).localeCompare(String(b.label || b.id)));
                    otherProto.forEach(g => renderGroupRow(g, block));
                    sec.appendChild(block);
                }
                panel.appendChild(sec);
            }

            // -------------------------------------------------------------
            // Render: Services / Perimeter / Other (existing flat buckets)
            // -------------------------------------------------------------
            const renderFlatBucket = (title, items, openByDefault) => {
                if (!items.length) return;
                const sec = document.createElement('details');
                sec.className = 'generated-protocol-panel__accordion';
                sec.open = !!openByDefault;
                const sum = document.createElement('summary');
                sum.className = 'generated-protocol-panel__subtitle';
                const total = items.reduce((s, g) => s + (g.count || (g.objectIds || []).length || 0), 0);
                const warns = items.reduce((s, g) => s + (g.warningCount || 0), 0);
                sum.textContent = `${title} (${total})${warns ? ` warnings ${warns}` : ''}`;
                sec.appendChild(sum);
                items.forEach(g => renderGroupRow(g, sec));
                panel.appendChild(sec);
            };
            renderFlatBucket('Services', serviceGroups, true);
            renderFlatBucket('Perimeter', perimeterGroups, false);
            renderFlatBucket('Other', otherGroups, false);
            const container = this.editor.canvas.parentElement || document.body;
            container.appendChild(panel);
        }

        _regenerate() {
            switch (this._currentSource) {
                case 'canvas': return this._generateFromCanvas();
                case 'live': return this._generateFromLive();
                case 'mapper': return this._generateFromMapper();
                case 'import': return this._generateFromImport();
            }
        }

        async _enrichWithAi() {
            if (!this._lastPayload) return;
            this._setProgressText('Asking AI to enrich the preview...');
            this._showProgress('Asking AI to enrich the preview...');
            this._log('Applying preview to canvas before enrichment so AI can edit it in-place...');
            try {
                this._applyPayload();
            } catch (_) {}

            // Build the prompt the AI can act on. We ship the exact
            // facts the deterministic generator produced so the model
            // doesn't have to re-derive them from canvas labels: links
            // already carry interface names, VLAN ids, bridge domains,
            // and a protocol guess that the model can promote into
            // link-table fields.
            const summary = (this._lastPayload.metadata && this._lastPayload.metadata.description) || 'a generated topology';
            // Build the AI snippet with stable canvas object IDs so the
            // model can target ``style_link``/``add_text`` operations
            // at the *exact* devices and links we just rendered. The
            // ``id_map`` lets the model translate fact-side ids
            // (``live_3``, ``gen_4``, ...) into canvas ids
            // (``device_2``, ``link_5``, ...) without re-deriving them
            // from labels.
            const idMap = (this._lastPayload && this._lastPayload.metadata
                && this._lastPayload.metadata.idMap) || {};
            const factsSnippet = {
                devices: (this._lastFacts && this._lastFacts.devices || []).slice(0, 60).map(d => ({
                    id: d.id, canvasId: idMap[d.id] || null,
                    hostname: d.hostname, role: d.role, tier: d.tier,
                    ip: d.ip, mgmtIp: d.mgmtIp, system_type: d.system_type,
                    dnos_version: d.dnos_version,
                    config: d.config && {
                        asn: d.config.asn,
                        router_id: d.config.router_id,
                        loopback0_ip: d.config.loopback0_ip,
                        isis_area: (d.config.isis && d.config.isis.area) || d.config.isis_area || '',
                        ospf_area: (d.config.ospf && d.config.ospf.area) || '',
                        mpls: d.config.mpls || {},
                        evpn: d.config.evpn || {},
                        vrfs: d.config.vrfs,
                        bridge_domains: d.config.bridge_domains,
                        route_distinguishers: d.config.route_distinguishers,
                        bgp_peers: (d.config.bgp_peers || []).slice(0, 24)
                    }
                })),
                links: (this._lastFacts && this._lastFacts.links || []).slice(0, 120).map(L => ({
                    fromDevice: L.fromDevice, toDevice: L.toDevice,
                    fromCanvasId: idMap[L.fromDevice] || null,
                    toCanvasId: idMap[L.toDevice] || null,
                    fromInterface: L.fromInterface, toInterface: L.toInterface,
                    vlan: L.vlan, bd: L.bd, protocol: L.protocol,
                    linkType: L.linkType, originType: L.originType,
                    layer: L.layer || 'physical'
                })),
                logicalLinks: (this._lastFacts && this._lastFacts.logicalLinks || []).slice(0, 80).map(L => ({
                    fromDevice: L.fromDevice, toDevice: L.toDevice,
                    fromCanvasId: idMap[L.fromDevice] || null,
                    toCanvasId: idMap[L.toDevice] || null,
                    protocol: L.protocol, linkType: L.linkType
                })),
                groups: (this._lastFacts && this._lastFacts.groups || []),
                provenance: (this._lastFacts && this._lastFacts.provenance) || {}
            };

            const message = (
                'TOPOLOGY-ENRICH: I just clicked AI enrich after generating ' + summary + '. '
                + 'The canvas already holds the generated devices/links -- do NOT call create_topology. '
                + 'Emit ONE apply_canvas_edits batch that ADDS detail on top: '
                + 'style ops to assign protocol colors per linkType (iBGP blue dashed, eBGP orange arrow, '
                + 'OSPF green, ISIS purple, MPLS red, EVPN teal dashed-wide, DNAAS orange) and to stamp '
                + 'link-table fields interface1/interface2/vlan/bd/linkDetails on links that have real data; '
                + 'add_shape ops with fillOpacity 0.08 for AS / area / VRF / BD grouping; '
                + 'add_text ops for AS numbers, RD/RT, VRF, dual-stack callouts. '
                + 'Keep every existing device and link. Use the generator facts below as ground truth.\n\n'
                + 'GENERATOR_FACTS:\n```json\n' + JSON.stringify(factsSnippet) + '\n```'
            );

            try {
                let canvasSnapshot = {};
                try {
                    if (window.TopologyAI && typeof window.TopologyAI.collectCanvasSnapshot === 'function') {
                        canvasSnapshot = window.TopologyAI.collectCanvasSnapshot();
                    }
                } catch (_) {}
                const resp = await _authFetch('/api/ai/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        messages: [{ role: 'user', content: message }],
                        canvas: canvasSnapshot,
                        intent: 'topology-enrich'
                    })
                });
                if (!resp.ok) {
                    const text = await resp.text();
                    throw new Error(`HTTP ${resp.status}: ${text.slice(0, 200)}`);
                }
                const j = await resp.json();
                if (j && j.error) throw new Error(j.error);

                // The chat endpoint normalizes apply_canvas_edits into
                // a tool_call entry with status=='apply' and the raw
                // `edits` array directly on the entry. We pull it and
                // route through the AI module's applier so the
                // enrichment lands as ONE undoable step with a toast
                // -- exactly matching the chat-driven path.
                const toolCalls = (j && j.tool_calls) || [];
                let editsCall = toolCalls.find(tc =>
                    (tc.name || '') === 'apply_canvas_edits' && (tc.status || '') === 'apply'
                );
                if (!editsCall) {
                    editsCall = toolCalls.find(tc =>
                        (tc.name || '') === 'propose_canvas_edits' && (tc.status || '') === 'propose'
                    );
                }
                let counted = 0;
                if (editsCall && Array.isArray(editsCall.edits)) {
                    counted = editsCall.edits.length;
                    const editsArgs = { summary: editsCall.summary || '', edits: editsCall.edits };
                    if (window.TopologyAI && typeof window.TopologyAI.applyCanvasEdits === 'function') {
                        try { window.TopologyAI.applyCanvasEdits(editsArgs); }
                        catch (e) { this._log('applyCanvasEdits failed: ' + (e.message || e)); }
                    } else {
                        document.dispatchEvent(new CustomEvent('topology-ai:apply-edits', {
                            detail: editsArgs
                        }));
                    }
                }
                const text = (j && (j.text || j.reply)) || '';
                this._log('AI enrichment: ' + (counted ? counted + ' edit(s)' : '(no edit batch returned)')
                    + (text ? ' - ' + text.slice(0, 140) : ''));
                this._finishProgress(counted ? 'Enrichment applied' : 'No enrichment returned');
            } catch (e) {
                this._log('AI enrichment failed: ' + (e.message || e));
                this._finishProgress('AI enrichment failed');
            }
        }

        _discardPreview() {
            this._lastPayload = null;
            this._lastFacts = null;
            this._hideProgress();
            const p = document.getElementById('gen-preview');
            if (p) p.style.display = 'none';
        }
    }

    // Expose for setup. Hook into the existing topology-network-mapper
    // setup so the panel comes alive after the LLDP module wires its
    // own handlers, and so populateSuggestions still runs on open.
    window.TopologyGeneratorManager = TopologyGeneratorManager;
    window.TopologyGeneratorTestHooks = {
        composeArchitectureFacts,
        buildCanvasPayload,
        buildGenerationSignature,
        enrichTargetFromCanvas,
        correlateFactsRemote
    };

    function _waitForEditor(cb, attempts) {
        attempts = attempts || 0;
        const ed = _editor();
        const panel = document.getElementById('network-mapper-panel');
        if (ed && panel) { cb(ed); return; }
        if (attempts > 120) {
            // Editor never showed up. Still try to wire up the panel
            // so the user is not stuck with an empty body. Adapter
            // helpers tolerate a null editor.
            if (panel) {
                try {
                    const mgr = new TopologyGeneratorManager(null);
                    mgr.setupPanel();
                } catch (_) {}
            }
            return;
        }
        setTimeout(() => _waitForEditor(cb, attempts + 1), 250);
    }

    // Defensive default: if the panel is in the DOM but nothing has
    // activated a tab pane yet, surface the Live Devices tab body so
    // the primary flow is real device discovery, not canvas enrichment.
    // ``setupPanel()`` will normalize the active tab once the editor exists.
    function _showLiveTabFallback() {
        const panel = document.getElementById('network-mapper-panel');
        if (!panel) return;
        const panes = panel.querySelectorAll('.gen-tab-pane');
        let anyVisible = false;
        panes.forEach(p => {
            const disp = (p.style && p.style.display) || '';
            if (disp && disp !== 'none') anyVisible = true;
        });
        if (anyVisible) return;
        const livePane = panel.querySelector('.gen-tab-pane[data-gen-pane="live"]');
        if (livePane) livePane.style.display = 'block';
        const liveBtn = panel.querySelector('.gen-tab-btn[data-gen-tab="live"]');
        if (liveBtn) liveBtn.classList.add('active');
    }

    document.addEventListener('DOMContentLoaded', () => {
        // Surface the live discovery body immediately so the panel is
        // never empty -- setupPanel will refresh state once it runs.
        _showLiveTabFallback();
        _waitForEditor(ed => {
            try {
                const mgr = new TopologyGeneratorManager(ed);
                mgr.setupPanel();
                if (ed) ed.topologyGenerator = mgr;
                window.topologyGenerator = mgr;
            } catch (e) {
                console.warn('[TopologyGenerator] setup failed:', e);
            }
        });
    });
})();
