/**
 * topology-packets.js -- Layered packet/frame topology objects.
 *
 * A "packet" is a compact card that lives ABOVE a link and explains, layer by
 * layer, what the wire actually carries in the scenario the topology is
 * describing. It is meant for /TOPOLOGY explanations and /debug-dnos bug
 * topologies, where words on the canvas should mostly come from the picture
 * (links, devices, badges) and the packet card adds the specific encap/L3/L4
 * details a reader cannot infer from shape alone.
 *
 * Schema (object pushed to `editor.objects`):
 *   {
 *     type: 'packet',
 *     id: 'packet_<n>',
 *     linkId: 'link_<n>' | null,        // attached link (preferred) or freestanding
 *     linkAttachT: 0..1,                 // parametric position along the link
 *     x, y,                              // updated every frame from the link
 *     width: number,                     // chip width (auto-grows to longest label)
     *     direction: 'forward'|'backward',   // arrow direction along the link
     *     side: 'above'|'below',             // which side of the cable to float on
 *     title: string,                     // top header (e.g. 'Frame', 'BUM', 'BGP UPDATE')
 *     collapsed: boolean,                // when true only the header is shown
 *     layers: [
 *       {
 *         id: 'l2'|'vlan'|'mpls'|'l3'|'l4'|'payload'|<custom>,
 *         name: string,                  // short layer name printed in the chip
 *         text: string,                  // one or two short lines describing this layer
 *         color: '#rrggbb',              // accent color of the row
 *         visible: boolean               // hide/show toggle
 *       }
 *     ],
 *     locked: boolean
 *   }
 *
 * Visual contract:
 *   - Compact: minimum 96px wide, capped at ~220px; row height 18px.
 *   - Sits above the cable midpoint (offset ~26px against the link normal).
 *   - Each visible layer is a stacked rounded card with a colored accent bar
 *     on the left (the layer color) and the layer name + one-line text.
 *   - Hidden layers are NOT drawn but are kept in the data so the user can
 *     re-enable them via the popup. There is also a "[+ N more]" footer hint
 *     when 1 or more layers are hidden.
 *   - When `collapsed` is true the packet renders as a single-row pill that
 *     keeps only the title, plus the footer hint that N layers are hidden.
 *
 * Multi-user: pure client-side object, persists inside the per-user topology
 * JSON (saved through the existing /api/sections + per-user MCP DB). No new
 * global state is introduced.
 */

'use strict';

(function () {
    const ROW_HEIGHT = 16;
    const LINE_STEP = 11;       // vertical advance per wrapped text line
    const HEADER_HEIGHT = 16;
    const FOOTER_HEIGHT = 13;
    const HORIZONTAL_PADDING = 7;
    const ACCENT_BAR_WIDTH = 3;
    const MIN_WIDTH = 92;
    const MAX_WIDTH = 360;
    const MIN_USER_WIDTH = 80;
    const MAX_USER_WIDTH = 480;
    const ATTACH_OFFSET = 28;       // legacy additional push from the cable
    const LINK_CLEARANCE_GAP = 12;  // visible gap between card bottom and cable
    const MIN_CENTER_OFFSET = 22;
    const HIT_PADDING = 4;          // extra hit padding around the bbox (world px)
    const HANDLE_SIZE = 6;
    const SUMMARY_PILL_GAP = 8;
    const SUMMARY_PILL_HEIGHT = 16;
    const SUMMARY_ARROW_WIDTH = 16;

    const LAYER_PRESETS = {
        l1: { name: 'L1', color: '#7f8c8d', text: '', visible: false },
        l2: { name: 'L2', color: '#3498db', text: '', visible: true },
        vlan: { name: 'VLAN', color: '#9b59b6', text: '', visible: true },
        mpls: { name: 'MPLS', color: '#16a085', text: '', visible: false },
        l3: { name: 'L3', color: '#e67e22', text: '', visible: true },
        l4: { name: 'L4', color: '#e74c3c', text: '', visible: false },
        payload: { name: 'Payload', color: '#2ecc71', text: '', visible: false }
    };

    function _makeLayer(id, overrides) {
        const preset = LAYER_PRESETS[id] || LAYER_PRESETS.l2;
        return Object.assign({ id }, preset, overrides || {});
    }

    // Legacy placeholder strings used by older packets. They were abbreviated
    // (e.g. "src 00:..:01") which read like a truncated address on the chip.
    // Any layer whose text EXACTLY matches a legacy placeholder is upgraded to
    // a full, readable default on the next draw. Only exact matches are touched,
    // so user-entered values are never rewritten.
    const _LEGACY_TEXT_UPGRADES = {
        'src 00:..:01\ndst 00:..:02': 'src 00:00:00:00:00:01\ndst 00:00:00:00:00:02',
        'src ---\ndst ---': 'src 10.0.0.1\ndst 10.0.0.2',
        'outer=---\ninner=---': 'outer=100\ninner=200'
    };

    function _upgradeLegacyLayers(packet) {
        if (!packet || !Array.isArray(packet.layers)) return;
        for (const layer of packet.layers) {
            if (layer && typeof layer.text === 'string' &&
                Object.prototype.hasOwnProperty.call(_LEGACY_TEXT_UPGRADES, layer.text)) {
                layer.text = _LEGACY_TEXT_UPGRADES[layer.text];
            }
        }
    }

    function makeDefaultLayers(opts) {
        opts = opts || {};
        const defaults = [];
        defaults.push(_makeLayer('l2', {
            text: opts.l2 || 'src 00:00:00:00:00:01\ndst 00:00:00:00:00:02'
        }));
        defaults.push(_makeLayer('vlan', {
            text: opts.vlan || 'outer=100\ninner=200',
            visible: opts.vlan !== undefined ? true : false
        }));
        defaults.push(_makeLayer('mpls', {
            text: opts.mpls || '',
            visible: !!opts.mpls
        }));
        defaults.push(_makeLayer('l3', {
            text: opts.l3 || 'src 10.0.0.1\ndst 10.0.0.2'
        }));
        defaults.push(_makeLayer('l4', {
            text: opts.l4 || '',
            visible: !!opts.l4
        }));
        defaults.push(_makeLayer('payload', {
            text: opts.payload || '',
            visible: !!opts.payload
        }));
        return defaults;
    }

    function _isPacket(obj) {
        return obj && obj.type === 'packet';
    }

    function _clamp(value, min, max) {
        return Math.max(min, Math.min(max, value));
    }

    function _getLinkGeometry(editor, link) {
        if (!editor || !link) return null;
        let startX, startY, endX, endY;
        if (link._renderedEndpoints &&
            [link._renderedEndpoints.startX, link._renderedEndpoints.startY,
             link._renderedEndpoints.endX, link._renderedEndpoints.endY]
                .every(v => typeof v === 'number' && isFinite(v))) {
            startX = link._renderedEndpoints.startX;
            startY = link._renderedEndpoints.startY;
            endX = link._renderedEndpoints.endX;
            endY = link._renderedEndpoints.endY;
        } else if (link.start && link.end) {
            startX = link.start.x;
            startY = link.start.y;
            endX = link.end.x;
            endY = link.end.y;
        } else if (link.device1 && link.device2) {
            const d1 = editor.objects.find(o => o.id === link.device1);
            const d2 = editor.objects.find(o => o.id === link.device2);
            if (!d1 || !d2) return null;
            startX = d1.x; startY = d1.y;
            endX = d2.x; endY = d2.y;
        } else {
            return null;
        }
        return { startX, startY, endX, endY };
    }

    function _sampleLinkPoint(link, geometry, t) {
        const startX = geometry.startX;
        const startY = geometry.startY;
        const endX = geometry.endX;
        const endY = geometry.endY;
        let pointX, pointY, tangentX, tangentY;
        if (link._cp1 && link._cp2 &&
            typeof link._cp1.x === 'number' && typeof link._cp1.y === 'number' &&
            typeof link._cp2.x === 'number' && typeof link._cp2.y === 'number') {
            const u = 1 - t;
            const u2 = u * u, t2 = t * t;
            pointX = u2 * u * startX + 3 * u2 * t * link._cp1.x + 3 * u * t2 * link._cp2.x + t2 * t * endX;
            pointY = u2 * u * startY + 3 * u2 * t * link._cp1.y + 3 * u * t2 * link._cp2.y + t2 * t * endY;
            tangentX = 3 * u2 * (link._cp1.x - startX) + 6 * u * t * (link._cp2.x - link._cp1.x) + 3 * t2 * (endX - link._cp2.x);
            tangentY = 3 * u2 * (link._cp1.y - startY) + 6 * u * t * (link._cp2.y - link._cp1.y) + 3 * t2 * (endY - link._cp2.y);
        } else {
            pointX = startX + (endX - startX) * t;
            pointY = startY + (endY - startY) * t;
            tangentX = endX - startX;
            tangentY = endY - startY;
        }
        return { pointX, pointY, tangentX, tangentY };
    }

    function projectCursorToLinkT(editor, link, mx, my) {
        const geometry = _getLinkGeometry(editor, link);
        if (!geometry) return 0.5;
        let bestT = 0.5;
        let bestD = Infinity;
        for (let i = 0; i <= 40; i++) {
            const t = 0.05 + (i / 40) * 0.90;
            const sample = _sampleLinkPoint(link, geometry, t);
            const dx = sample.pointX - mx;
            const dy = sample.pointY - my;
            const d = dx * dx + dy * dy;
            if (d < bestD) {
                bestD = d;
                bestT = t;
            }
        }
        return _clamp(bestT, 0.05, 0.95);
    }

    function _measureTextWidth(ctx, text, fontPx) {
        if (!text) return 0;
        ctx.save();
        ctx.font = `${fontPx}px Arial, sans-serif`;
        const lines = String(text).split('\n');
        let max = 0;
        for (const l of lines) {
            const w = ctx.measureText(l).width;
            if (w > max) max = w;
        }
        ctx.restore();
        return max;
    }

    function _fitCanvasText(ctx, text, maxWidth) {
        const value = String(text || '');
        if (!ctx || !Number.isFinite(maxWidth) || maxWidth <= 8) return '';
        if (ctx.measureText(value).width <= maxWidth) return value;
        const suffix = '...';
        const suffixW = ctx.measureText(suffix).width;
        if (suffixW >= maxWidth) return '';
        let lo = 0;
        let hi = value.length;
        while (lo < hi) {
            const mid = Math.ceil((lo + hi) / 2);
            if (ctx.measureText(value.slice(0, mid)).width + suffixW <= maxWidth) {
                lo = mid;
            } else {
                hi = mid - 1;
            }
        }
        return value.slice(0, lo).trimEnd() + suffix;
    }

    function getPacketBounds(editor, packet) {
        if (!editor || !editor.ctx || !packet) {
            return { x: packet ? packet.x : 0, y: packet ? packet.y : 0, w: MIN_WIDTH, h: HEADER_HEIGHT };
        }
        const ctx = editor.ctx;
        const visibleLayers = (packet.layers || []).filter(l => l && l.visible !== false);
        const hiddenCount = (packet.layers || []).length - visibleLayers.length;

        // Compute width from longest single line (title or any visible layer line).
        let widest = _measureTextWidth(ctx, packet.title || 'Frame', 11) + 16;
        for (const layer of visibleLayers) {
            const labelW = _measureTextWidth(ctx, layer.name || '', 8.5) + 5;
            const textW = _measureTextWidth(ctx, layer.text || '', 9.5);
            widest = Math.max(widest, labelW + textW);
        }
        if (hiddenCount > 0) {
            widest = Math.max(widest, _measureTextWidth(ctx, `+ ${hiddenCount} hidden`, 9) + 12);
        }
        const autoWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, widest + HORIZONTAL_PADDING * 2 + ACCENT_BAR_WIDTH));
        // When the user has manually stretched the chip, that width is
        // authoritative -- it may be NARROWER than the auto/content width (text
        // ellipsizes via _fitCanvasText) or wider. Previously we did
        // Math.max(autoWidth, userWidth), which silently ignored any attempt to
        // drag the chip smaller, so the stretch handle felt broken on shrink.
        const userWidth = Number.isFinite(packet.userWidth)
            ? _clamp(packet.userWidth, MIN_USER_WIDTH, MAX_USER_WIDTH)
            : null;
        const totalWidth = userWidth != null ? userWidth : autoWidth;

        // Per-layer height grows with line count of the visible text.
        let bodyHeight = 0;
        if (!packet.collapsed) {
            for (const layer of visibleLayers) {
                const lines = Math.max(1, String(layer.text || '').split('\n').length);
                bodyHeight += ROW_HEIGHT + (lines - 1) * LINE_STEP;
            }
            if (hiddenCount > 0) bodyHeight += FOOTER_HEIGHT;
        } else if (hiddenCount > 0) {
            bodyHeight = FOOTER_HEIGHT;
        }
        const totalHeight = HEADER_HEIGHT + bodyHeight + 3;

        return {
            x: packet.x,
            y: packet.y,
            w: totalWidth,
            h: totalHeight,
            visibleLayers,
            hiddenCount
        };
    }

    function hitTestPacket(editor, packet, x, y) {
        if (!_isPacket(packet)) return false;
        const b = getPacketBounds(editor, packet);
        const left = b.x - b.w / 2 - HIT_PADDING;
        const right = b.x + b.w / 2 + HIT_PADDING;
        const top = b.y - b.h / 2 - HIT_PADDING;
        const bottom = b.y + b.h / 2 + HIT_PADDING;
        if (x >= left && x <= right && y >= top && y <= bottom) return true;
        return !!findPacketSummaryHit(editor, packet, x, y);
    }

    function findPacketAt(editor, x, y) {
        if (!editor || !editor.objects) return null;
        for (let i = editor.objects.length - 1; i >= 0; i--) {
            const obj = editor.objects[i];
            if (!_isPacket(obj) || obj._hidden) continue;
            if (hitTestPacket(editor, obj, x, y)) return obj;
        }
        return null;
    }

    /**
     * Recompute (x, y) for a link-attached packet so it floats above the
     * cable at the requested parametric position. This mirrors the pattern
     * used by `editor.updateAdjacentTextPosition` for text labels: prefer
     * `link._renderedEndpoints` when available (already accounts for shape
     * connection points + parallel link offset + curve), fall back to the
     * straight-line midpoint computed from the device centers.
     */
    function updatePacketPosition(editor, packet) {
        if (!_isPacket(packet) || !packet.linkId) return;
        const link = editor.objects.find(o => o.id === packet.linkId);
        if (!link) {
            // Link was deleted -- detach the packet but keep its last position.
            packet.linkId = null;
            return;
        }
        const t = (typeof packet.linkAttachT === 'number') ? packet.linkAttachT : 0.5;

        const geometry = _getLinkGeometry(editor, link);
        if (!geometry) return;
        const sample = _sampleLinkPoint(link, geometry, t);
        const pointX = sample.pointX;
        const pointY = sample.pointY;
        const tangentX = sample.tangentX;
        const tangentY = sample.tangentY;

        const len = Math.hypot(tangentX, tangentY) || 1;
        // Perpendicular unit vector. We always offset to the "above" side
        // (negative Y in canvas space) so packets read like a callout above
        // the wire. When the link is more vertical than horizontal we keep
        // pushing them along the same perpendicular for consistency.
        let nx = -tangentY / len;
        let ny = tangentX / len;
        if (ny > 0) { nx = -nx; ny = -ny; }
        if (packet.side === 'below') {
            nx = -nx;
            ny = -ny;
        }

        const bounds = getPacketBounds(editor, packet);
        const extraOffset = (typeof packet.attachOffset === 'number' && isFinite(packet.attachOffset))
            ? Math.max(0, packet.attachOffset)
            : 0;
        const offset = Math.max(MIN_CENTER_OFFSET, bounds.h / 2 + LINK_CLEARANCE_GAP + extraOffset);
        packet.x = pointX + nx * offset;
        packet.y = pointY + ny * offset;
        packet._linkAngle = Math.atan2(tangentY, tangentX);
        packet._linkAnchorX = pointX;
        packet._linkAnchorY = pointY;
    }

    function attachPacketToLink(editor, packet, link, t) {
        if (!_isPacket(packet) || !link) return;
        if (typeof t !== 'number' || !isFinite(t)) t = 0.5;
        packet.linkId = link.id;
        packet.linkAttachT = Math.max(0.05, Math.min(0.95, t));
        updatePacketPosition(editor, packet);
    }

    function detachPacket(editor, packet) {
        if (!_isPacket(packet)) return;
        packet.linkId = null;
        packet.linkAttachT = undefined;
    }

    /**
     * Find the link (or unbound link) whose body passes closest to the packet's
     * current center. Returns { link, t, dist, pointX, pointY } or null. When
     * `maxDist` is given, links farther than that (world px) are ignored -- used
     * by drag-to-reattach so a drop only snaps when intentionally near a wire.
     */
    function findNearestLink(editor, packet, maxDist) {
        if (!_isPacket(packet) || !editor || !Array.isArray(editor.objects)) return null;
        let best = null;
        for (const link of editor.objects) {
            if (!link || (link.type !== 'link' && link.type !== 'unbound')) continue;
            const geometry = _getLinkGeometry(editor, link);
            if (!geometry) continue;
            let bestT = 0.5, bestD = Infinity, bx = 0, by = 0;
            for (let i = 0; i <= 40; i++) {
                const t = 0.05 + (i / 40) * 0.90;
                const s = _sampleLinkPoint(link, geometry, t);
                const dx = s.pointX - packet.x;
                const dy = s.pointY - packet.y;
                const d = dx * dx + dy * dy;
                if (d < bestD) { bestD = d; bestT = t; bx = s.pointX; by = s.pointY; }
            }
            const dist = Math.sqrt(bestD);
            if (!best || dist < best.dist) {
                best = { link, t: bestT, dist, pointX: bx, pointY: by };
            }
        }
        if (!best) return null;
        if (typeof maxDist === 'number' && best.dist > maxDist) return null;
        return best;
    }

    function attachPacketToNearestLink(editor, packet, maxDist) {
        const near = findNearestLink(editor, packet, maxDist);
        if (!near) return null;
        attachPacketToLink(editor, packet, near.link, near.t);
        return near.link;
    }

    /**
     * Create a new packet object. When `link` is provided the packet attaches
     * to that link; otherwise it is freestanding at (x, y).
     *
     * `options` may contain:
     *   - layers: pre-built layer array (overrides the defaults)
     *   - presetLayers: object passed to makeDefaultLayers() to fill text per id
     *   - title: chip title (default 'Frame')
     *   - direction: 'forward'|'backward'
     *   - linkAttachT: parametric position along the link (default 0.5)
     */
    function createPacket(editor, x, y, options) {
        // Normalize call shapes:
        //   createPacket(editor, x, y, options)      -- explicit canvas-coord placement
        //   createPacket(editor, optionsObj)         -- options-only (e.g. { linkId, link, ... })
        //   editor.createPacket({ linkId: ... })     -- via wrapper, becomes (editor, opts, undef, undef)
        if (x !== null && typeof x === 'object' && options === undefined) {
            options = x;
            x = undefined;
            y = undefined;
        }
        options = options || {};
        if (!editor.packetIdCounter) editor.packetIdCounter = 0;
        const id = `packet_${editor.packetIdCounter++}`;
        // Resolve link object: prefer explicit object, else look up by linkId.
        let linkObj = options.link || null;
        if (!linkObj && options.linkId && Array.isArray(editor.objects)) {
            linkObj = editor.objects.find((o) => o && o.id === options.linkId &&
                (o.type === 'link' || o.type === 'unbound')) || null;
        }
        const packet = {
            type: 'packet',
            id,
            linkId: linkObj ? linkObj.id : (options.linkId || null),
            linkAttachT: options.linkAttachT,
            x: typeof x === 'number' ? x : 0,
            y: typeof y === 'number' ? y : 0,
            width: 0, // recomputed every frame
            title: options.title || 'Frame',
            summary: options.summary || '',
            direction: options.direction || 'forward',
            side: options.side === 'below' ? 'below' : 'above',
            collapsed: !!options.collapsed,
            layers: options.layers || makeDefaultLayers(options.presetLayers || {}),
            locked: false
        };
        editor.objects.push(packet);
        if (linkObj) {
            attachPacketToLink(editor, packet, linkObj, options.linkAttachT);
        } else if (typeof x === 'number' && typeof y === 'number') {
            packet.x = x;
            packet.y = y;
        }
        if (typeof editor.saveState === 'function') editor.saveState();
        if (typeof editor.draw === 'function') editor.draw();
        return packet;
    }

    function toggleLayer(packet, layerId) {
        if (!_isPacket(packet)) return;
        for (const layer of packet.layers || []) {
            if (layer.id === layerId) {
                layer.visible = layer.visible === false ? true : false;
                return layer.visible;
            }
        }
        return null;
    }

    function setLayerVisibility(packet, layerId, visible) {
        if (!_isPacket(packet)) return;
        for (const layer of packet.layers || []) {
            if (layer.id === layerId) {
                layer.visible = !!visible;
                return;
            }
        }
    }

    function _drawRoundedRect(ctx, x, y, w, h, r) {
        const rr = Math.min(r, w / 2, h / 2);
        ctx.beginPath();
        ctx.moveTo(x + rr, y);
        ctx.lineTo(x + w - rr, y);
        ctx.quadraticCurveTo(x + w, y, x + w, y + rr);
        ctx.lineTo(x + w, y + h - rr);
        ctx.quadraticCurveTo(x + w, y + h, x + w - rr, y + h);
        ctx.lineTo(x + rr, y + h);
        ctx.quadraticCurveTo(x, y + h, x, y + h - rr);
        ctx.lineTo(x, y + rr);
        ctx.quadraticCurveTo(x, y, x + rr, y);
        ctx.closePath();
    }

    function _drawArrowHead(ctx, x, y, angle, size) {
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(
            x - Math.cos(angle - Math.PI / 6) * size,
            y - Math.sin(angle - Math.PI / 6) * size
        );
        ctx.lineTo(
            x - Math.cos(angle + Math.PI / 6) * size,
            y - Math.sin(angle + Math.PI / 6) * size
        );
        ctx.closePath();
        ctx.fill();
    }

    function _packetDirectionAngle(packet) {
        const base = Number.isFinite(packet._linkAngle) ? packet._linkAngle : 0;
        return packet.direction === 'backward' ? base + Math.PI : base;
    }

    function _drawDirectionBadge(ctx, packet, x, y, selected) {
        const angle = _packetDirectionAngle(packet);
        const len = 18;
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(angle);
        ctx.strokeStyle = selected ? 'rgba(0, 220, 255, 0.95)' : 'rgba(158, 234, 255, 0.9)';
        ctx.fillStyle = selected ? 'rgba(0, 220, 255, 0.95)' : 'rgba(158, 234, 255, 0.9)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(-len / 2, 0);
        ctx.lineTo(len / 2 - 3, 0);
        ctx.stroke();
        _drawArrowHead(ctx, len / 2, 0, 0, 4);
        ctx.restore();
    }

    function getPacketSummary(packet) {
        const raw = String(packet && packet.summary ? packet.summary : (packet && packet.title ? packet.title : 'Frame'))
            .replace(/[^\x20-\x7E]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
        const words = (raw || 'Frame').split(' ').filter(Boolean).slice(0, 3);
        return (words.join(' ') || 'Frame').slice(0, 18);
    }

    function getPacketSummaryBounds(editor, packet) {
        if (!_isPacket(packet) || !editor || !editor.ctx) return null;
        const bounds = getPacketBounds(editor, packet);
        const summary = getPacketSummary(packet);
        const ctx = editor.ctx;
        const labelW = _measureTextWidth(ctx, summary, 9);
        const width = Math.max(54, Math.min(120, labelW + SUMMARY_ARROW_WIDTH + 16));
        return {
            x: packet.x,
            y: packet.y + bounds.h / 2 + SUMMARY_PILL_GAP + SUMMARY_PILL_HEIGHT / 2,
            w: width,
            h: SUMMARY_PILL_HEIGHT,
            textW: width - SUMMARY_ARROW_WIDTH,
            arrowW: SUMMARY_ARROW_WIDTH,
            summary
        };
    }

    function findPacketSummaryHit(editor, packet, x, y) {
        const b = getPacketSummaryBounds(editor, packet);
        if (!b) return null;
        const left = b.x - b.w / 2;
        const top = b.y - b.h / 2;
        if (x < left - HIT_PADDING || x > left + b.w + HIT_PADDING ||
            y < top - HIT_PADDING || y > top + b.h + HIT_PADDING) {
            return null;
        }
        return x >= left + b.textW ? 'arrow' : 'text';
    }

    // Hit-test the header chevron (top-right) so a single click on it toggles
    // collapse/expand directly on the canvas -- the chevron always looked
    // clickable but previously did nothing on its own.
    function findPacketChevronHit(editor, packet, x, y) {
        if (!_isPacket(packet) || !editor || !editor.ctx) return false;
        const b = getPacketBounds(editor, packet);
        const left = packet.x - b.w / 2;
        const top = packet.y - b.h / 2;
        const zone = 24;
        const zx = left + b.w - zone;
        const right = left + b.w + HIT_PADDING;
        return (x >= zx && x <= right &&
                y >= top - HIT_PADDING && y <= top + HEADER_HEIGHT + 2);
    }

    function getPacketHandles(editor, packet) {
        if (!_isPacket(packet) || !editor || editor.selectedObject !== packet) return [];
        const b = getPacketBounds(editor, packet);
        // Tall vertical grab-bars are far easier to hit than a 6px square,
        // which is what made the stretch handles feel unresponsive.
        const barH = _clamp(b.h - 6, 14, 26);
        return [
            { dir: 'w', x: packet.x - b.w / 2, y: packet.y, w: HANDLE_SIZE, h: barH },
            { dir: 'e', x: packet.x + b.w / 2, y: packet.y, w: HANDLE_SIZE, h: barH }
        ];
    }

    function findPacketResizeHandle(editor, packet, x, y) {
        const handles = getPacketHandles(editor, packet);
        // Generous hit zone: ~7 world px + a zoom-compensated pad so the bar is
        // grabbable even when zoomed out. The horizontal zone is intentionally
        // wide because the bar sits exactly on the card edge.
        const zoom = (editor && editor.zoom) ? editor.zoom : 1;
        const padX = 7 + 4 / zoom;
        const padY = 4 / zoom;
        for (const handle of handles) {
            const halfW = handle.w / 2 + padX;
            const halfH = handle.h / 2 + padY;
            if (x >= handle.x - halfW && x <= handle.x + halfW &&
                y >= handle.y - halfH && y <= handle.y + halfH) {
                return handle.dir;
            }
        }
        return null;
    }

    function drawPacket(editor, packet) {
        if (!_isPacket(packet) || packet._hidden) return;
        const ctx = editor.ctx;
        if (!ctx) return;
        _upgradeLegacyLayers(packet);
        const bounds = getPacketBounds(editor, packet);
        const visibleLayers = bounds.visibleLayers || [];
        const hiddenCount = bounds.hiddenCount || 0;
        packet.width = bounds.w;
        packet._renderedHeight = bounds.h;

        const left = packet.x - bounds.w / 2;
        const top = packet.y - bounds.h / 2;
        const isSelected = editor.selectedObject === packet;
        // A packet picked up by a marquee / multi-select is part of
        // editor.selectedObjects but is NOT the primary editor.selectedObject.
        // It still needs a visible highlight (border + glow) so the user can see
        // what the rubber-band grabbed; the single-select-only affordances
        // (stretch handles, chevron box) stay gated on isSelected.
        const isMultiSelected = !isSelected && Array.isArray(editor.selectedObjects) &&
            editor.selectedObjects.indexOf(packet) !== -1;
        const isHighlighted = isSelected || isMultiSelected;

        ctx.save();
        // Outer card: dark glass background with a soft drop shadow for depth.
        // The shadow turns into a cyan glow when the chip is selected so the
        // active packet reads clearly without a heavy border.
        ctx.save();
        ctx.shadowColor = isHighlighted ? 'rgba(0, 220, 255, 0.50)' : 'rgba(0, 0, 0, 0.40)';
        ctx.shadowBlur = isHighlighted ? 14 : 8;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = isHighlighted ? 0 : 2;
        const cardGrad = ctx.createLinearGradient(0, top, 0, top + bounds.h);
        cardGrad.addColorStop(0, 'rgba(28, 37, 54, 0.94)');
        cardGrad.addColorStop(1, 'rgba(15, 20, 31, 0.94)');
        ctx.fillStyle = cardGrad;
        _drawRoundedRect(ctx, left, top, bounds.w, bounds.h, 7);
        ctx.fill();
        ctx.restore(); // shadow applies to the fill only, not the stroke/contents

        // Thin border (no shadow so it stays crisp).
        ctx.strokeStyle = isHighlighted
            ? 'rgba(0, 220, 255, 0.95)'
            : (packet.groupColor || 'rgba(255, 255, 255, 0.20)');
        ctx.lineWidth = isHighlighted ? 1.6 : (packet.groupColor ? 1.4 : 1);
        _drawRoundedRect(ctx, left, top, bounds.w, bounds.h, 7);
        ctx.stroke();

        if (packet.groupId && packet.groupColor) {
            ctx.fillStyle = packet.groupColor;
            _drawRoundedRect(ctx, left + bounds.w - 14, top + 4, 6, 6, 2);
            ctx.fill();
        }

        // Header row: title centered.
        ctx.fillStyle = '#e6edf3';
        ctx.font = '600 11px Arial, sans-serif';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        const titleX = left + HORIZONTAL_PADDING + 24;
        const titleMaxW = bounds.w - HORIZONTAL_PADDING * 2 - 44;
        _drawDirectionBadge(ctx, packet, left + HORIZONTAL_PADDING + 9, top + HEADER_HEIGHT / 2, isSelected);
        ctx.fillText(_fitCanvasText(ctx, packet.title || 'Frame', titleMaxW),
            titleX, top + HEADER_HEIGHT / 2);
        // Collapse/expand chevron on the right (clickable on canvas).
        const chevCx = left + bounds.w - HORIZONTAL_PADDING - 2;
        if (isSelected) {
            ctx.fillStyle = 'rgba(0, 220, 255, 0.16)';
            _drawRoundedRect(ctx, left + bounds.w - 18, top + 2, 16, HEADER_HEIGHT - 4, 3);
            ctx.fill();
        }
        ctx.fillStyle = isSelected ? 'rgba(180, 240, 255, 0.95)' : 'rgba(255,255,255,0.6)';
        ctx.font = '11px Arial, sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(packet.collapsed ? '\u25B8' : '\u25BE',
            chevCx, top + HEADER_HEIGHT / 2);

        // Header underline.
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.10)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(left + 2, top + HEADER_HEIGHT);
        ctx.lineTo(left + bounds.w - 2, top + HEADER_HEIGHT);
        ctx.stroke();

        if (!packet.collapsed) {
            let cursorY = top + HEADER_HEIGHT + 2;
            for (const layer of visibleLayers) {
                const lines = String(layer.text || '').split('\n');
                const rowH = ROW_HEIGHT + (lines.length - 1) * LINE_STEP;
                // Accent bar (left side, layer color).
                ctx.fillStyle = layer.color || '#3498db';
                _drawRoundedRect(ctx, left + 2, cursorY + 2, ACCENT_BAR_WIDTH, rowH - 4, 1.5);
                ctx.fill();
                // Layer name (small, faded).
                ctx.fillStyle = 'rgba(255, 255, 255, 0.55)';
                ctx.font = '600 8.5px Arial, sans-serif';
                ctx.textAlign = 'left';
                ctx.textBaseline = 'middle';
                const nameX = left + 3 + ACCENT_BAR_WIDTH + 4;
                const layerName = (layer.name || '').toUpperCase();
                const nameMaxW = Math.min(46, Math.max(20, bounds.w * 0.24));
                const nameText = _fitCanvasText(ctx, layerName, nameMaxW);
                const nameW = Math.min(nameMaxW, _measureTextWidth(ctx, nameText, 8.5));
                ctx.fillText(nameText, nameX, cursorY + rowH / 2);
                // Layer text (multi-line allowed).
                ctx.fillStyle = '#dfe7ef';
                ctx.font = '9.5px Arial, sans-serif';
                let textX = nameX + nameW + 5;
                let textY = cursorY + (rowH - lines.length * LINE_STEP) / 2 + LINE_STEP / 2;
                const textMaxW = Math.max(12, left + bounds.w - HORIZONTAL_PADDING - textX);
                for (const line of lines) {
                    ctx.fillText(_fitCanvasText(ctx, line, textMaxW), textX, textY);
                    textY += LINE_STEP;
                }
                cursorY += rowH;
            }
            if (hiddenCount > 0) {
                ctx.fillStyle = 'rgba(255, 255, 255, 0.45)';
                ctx.font = 'italic 9px Arial, sans-serif';
                ctx.textAlign = 'left';
                ctx.textBaseline = 'middle';
                ctx.fillText(`+ ${hiddenCount} layer${hiddenCount === 1 ? '' : 's'} hidden`,
                    left + HORIZONTAL_PADDING, cursorY + FOOTER_HEIGHT / 2);
            }
        } else if (hiddenCount > 0) {
            const cursorY = top + HEADER_HEIGHT + 2;
            ctx.fillStyle = 'rgba(255, 255, 255, 0.45)';
            ctx.font = 'italic 9px Arial, sans-serif';
            ctx.textAlign = 'left';
            ctx.textBaseline = 'middle';
            ctx.fillText(`${(packet.layers || []).filter(l => l.visible !== false).length} visible \u00B7 ${hiddenCount} hidden`,
                left + HORIZONTAL_PADDING, cursorY + FOOTER_HEIGHT / 2);
        }

        // Tail line that hints which link this packet belongs to.
        if (packet.linkId && typeof packet._linkAngle === 'number') {
            const link = editor.objects.find(o => o.id === packet.linkId);
            if (link) {
                let anchorX, anchorY;
                if (link._renderedEndpoints) {
                    const t = (typeof packet.linkAttachT === 'number') ? packet.linkAttachT : 0.5;
                    anchorX = link._renderedEndpoints.startX + (link._renderedEndpoints.endX - link._renderedEndpoints.startX) * t;
                    anchorY = link._renderedEndpoints.startY + (link._renderedEndpoints.endY - link._renderedEndpoints.startY) * t;
                } else if (link.start && link.end) {
                    const t = (typeof packet.linkAttachT === 'number') ? packet.linkAttachT : 0.5;
                    anchorX = link.start.x + (link.end.x - link.start.x) * t;
                    anchorY = link.start.y + (link.end.y - link.start.y) * t;
                }
                if (typeof packet._linkAnchorX === 'number') {
                    anchorX = packet._linkAnchorX;
                    anchorY = packet._linkAnchorY;
                }
                if (typeof anchorX === 'number') {
                    ctx.strokeStyle = 'rgba(0, 200, 255, 0.45)';
                    ctx.lineWidth = 1;
                    ctx.setLineDash([3, 3]);
                    ctx.beginPath();
                    const dx = packet.x - anchorX;
                    const dy = (packet.y + bounds.h / 2 - 3) - anchorY;
                    const len = Math.hypot(dx, dy) || 1;
                    ctx.moveTo(anchorX + (dx / len) * 2, anchorY + (dy / len) * 2);
                    ctx.lineTo(packet.x, packet.y + bounds.h / 2 - 1);
                    ctx.stroke();
                    ctx.setLineDash([]);

                    // Direction cue on the actual wire anchor. This makes it clear
                    // whether "forward" means link start->end or the reverse.
                    const wireAngle = _packetDirectionAngle(packet);
                    const wireLen = 28;
                    const sx = anchorX - Math.cos(wireAngle) * wireLen / 2;
                    const sy = anchorY - Math.sin(wireAngle) * wireLen / 2;
                    const ex = anchorX + Math.cos(wireAngle) * wireLen / 2;
                    const ey = anchorY + Math.sin(wireAngle) * wireLen / 2;
                    ctx.strokeStyle = isSelected ? 'rgba(0, 220, 255, 0.85)' : 'rgba(0, 200, 255, 0.55)';
                    ctx.fillStyle = ctx.strokeStyle;
                    ctx.lineWidth = isSelected ? 1.8 : 1.3;
                    ctx.beginPath();
                    ctx.moveTo(sx, sy);
                    ctx.lineTo(ex, ey);
                    ctx.stroke();
                    _drawArrowHead(ctx, ex, ey, wireAngle, 5);
                }
            }
        }

        const pill = getPacketSummaryBounds(editor, packet);
        if (pill) {
            const pillLeft = pill.x - pill.w / 2;
            const pillTop = pill.y - pill.h / 2;
            ctx.fillStyle = 'rgba(7, 15, 26, 0.78)';
            ctx.strokeStyle = isSelected ? 'rgba(0, 220, 255, 0.7)' : 'rgba(255, 255, 255, 0.18)';
            ctx.lineWidth = 1;
            _drawRoundedRect(ctx, pillLeft, pillTop, pill.w, pill.h, 5);
            ctx.fill();
            ctx.stroke();

            ctx.fillStyle = '#dfe7ef';
            ctx.font = '600 9px Arial, sans-serif';
            ctx.textAlign = 'left';
            ctx.textBaseline = 'middle';
            ctx.fillText(pill.summary.toUpperCase(), pillLeft + 6, pill.y);

            ctx.strokeStyle = 'rgba(255,255,255,0.14)';
            ctx.beginPath();
            ctx.moveTo(pillLeft + pill.textW, pillTop + 3);
            ctx.lineTo(pillLeft + pill.textW, pillTop + pill.h - 3);
            ctx.stroke();

            const arrowCenterX = pillLeft + pill.textW + SUMMARY_ARROW_WIDTH / 2;
            _drawDirectionBadge(ctx, packet, arrowCenterX, pill.y, isSelected);
        }

        if (isSelected) {
            ctx.fillStyle = 'rgba(0, 220, 255, 0.95)';
            ctx.strokeStyle = 'rgba(5, 15, 26, 0.9)';
            ctx.lineWidth = 1;
            for (const handle of getPacketHandles(editor, packet)) {
                const hw = handle.w || HANDLE_SIZE;
                const hh = handle.h || HANDLE_SIZE;
                _drawRoundedRect(ctx, handle.x - hw / 2, handle.y - hh / 2, hw, hh, hw / 2);
                ctx.fill();
                ctx.stroke();
                // Two faint grip lines so the bar reads as a drag affordance.
                ctx.save();
                ctx.strokeStyle = 'rgba(5, 15, 26, 0.55)';
                ctx.lineWidth = 0.8;
                ctx.beginPath();
                ctx.moveTo(handle.x - 1, handle.y - hh / 2 + 3);
                ctx.lineTo(handle.x - 1, handle.y + hh / 2 - 3);
                ctx.moveTo(handle.x + 1, handle.y - hh / 2 + 3);
                ctx.lineTo(handle.x + 1, handle.y + hh / 2 - 3);
                ctx.stroke();
                ctx.restore();
            }
        }
        ctx.restore();
    }

    window.PacketMethods = {
        ROW_HEIGHT, HEADER_HEIGHT, FOOTER_HEIGHT, ATTACH_OFFSET,
        LAYER_PRESETS,
        makeDefaultLayers,
        createPacket,
        drawPacket,
        updatePacketPosition,
        projectCursorToLinkT,
        attachPacketToLink,
        detachPacket,
        findNearestLink,
        attachPacketToNearestLink,
        hitTestPacket,
        findPacketAt,
        findPacketChevronHit,
        getPacketHandles,
        findPacketResizeHandle,
        clampPacketWidth: (w) => _clamp(Number(w) || MIN_WIDTH, MIN_WIDTH, MAX_WIDTH),
        // Stretch range used while dragging a grab-bar. Allows the chip to grow
        // wider than the auto cap so long address lines (full MAC / IPv6 / QinQ)
        // can be fully revealed by stretching.
        clampPacketUserWidth: (w) => _clamp(Number(w) || MIN_USER_WIDTH, MIN_USER_WIDTH, MAX_USER_WIDTH),
        PACKET_MIN_WIDTH: MIN_WIDTH,
        PACKET_MAX_WIDTH: MAX_WIDTH,
        PACKET_MIN_USER_WIDTH: MIN_USER_WIDTH,
        PACKET_MAX_USER_WIDTH: MAX_USER_WIDTH,
        findPacketSummaryHit,
        getPacketSummaryBounds,
        getPacketSummary,
        getPacketBounds,
        toggleLayer,
        setLayerVisibility
    };
})();
