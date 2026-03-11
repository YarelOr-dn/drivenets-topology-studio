/**
 * topology-minimap-render.js - High-Fidelity Minimap Rendering
 * Renders a scaled-down replica of the main canvas with accurate device shapes,
 * link colors/curves/styles, and theme-matching background.
 */

'use strict';

window.MinimapRender = {

    DPR: 2,
    CSS_W: 188,
    CSS_H: 100,

    _topoCache: null,
    _topoCacheBounds: null,
    _topoCacheDark: null,
    _topoCacheHash: null,
    _pendingRAF: null,

    invalidateCache() {
        this._topoCacheHash = null;
    },

    _getTopoHash(editor) {
        const objs = editor.objects;
        let h = objs.length;
        for (let i = 0, len = objs.length; i < len; i++) {
            const o = objs[i];
            if (o.type === 'device') {
                h = (h * 31 + (o.x | 0)) | 0;
                h = (h * 31 + (o.y | 0)) | 0;
                h = (h * 31 + (o.radius | 0)) | 0;
            } else if (o.type === 'link' || o.type === 'unbound') {
                h = (h * 31 + (o.device1 || 0)) | 0;
                h = (h * 31 + (o.device2 || 0)) | 0;
            }
        }
        const sel = editor.selectedObject;
        h = (h * 31 + (sel ? (sel.id || 1) : 0)) | 0;
        h = (h * 31 + (editor.selectedObjects ? editor.selectedObjects.length : 0)) | 0;
        return h;
    },

    scheduleRender(editor) {
        if (this._pendingRAF) return;
        this._pendingRAF = requestAnimationFrame(() => {
            this._pendingRAF = null;
            this.renderMinimap(editor);
        });
    },

    renderMinimap(editor) {
        if (!editor.minimap || !editor.minimap.canvas) return;

        const canvas = editor.minimap.canvas;
        const dpr = this.DPR;
        const cssW = this.CSS_W;
        const cssH = this.CSS_H;
        const intW = cssW * dpr;
        const intH = cssH * dpr;

        if (canvas.width !== intW || canvas.height !== intH) {
            canvas.width = intW;
            canvas.height = intH;
        }

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const isDark = editor.darkMode;
        const bounds = editor.getMinimapBounds();
        if (!bounds || bounds.scale <= 0) return;

        const { minX, scale, offsetX, offsetY, viewLeft, viewTop, viewRight, viewBottom } = bounds;
        const minY = bounds.minY;

        const toMM = (wx, wy) => ({
            x: offsetX + (wx - minX) * scale,
            y: offsetY + (wy - minY) * scale
        });

        const topoHash = this._getTopoHash(editor);
        const boundsKey = `${minX|0},${minY|0},${scale.toFixed(4)},${offsetX.toFixed(2)},${offsetY.toFixed(2)}`;
        const needsTopoCacheRebuild = !this._topoCache
            || this._topoCacheHash !== topoHash
            || this._topoCacheDark !== isDark
            || this._topoCacheBounds !== boundsKey;

        if (needsTopoCacheRebuild) {
            this._rebuildTopoCache(editor, isDark, bounds, toMM, intW, intH, dpr, cssW, cssH);
            this._topoCacheHash = topoHash;
            this._topoCacheDark = isDark;
            this._topoCacheBounds = boundsKey;
        }

        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.clearRect(0, 0, intW, intH);

        if (this._topoCache) {
            ctx.drawImage(this._topoCache, 0, 0);
        }

        ctx.scale(dpr, dpr);
        this._drawViewport(ctx, isDark, cssW, cssH, toMM, viewLeft, viewTop, viewRight, viewBottom, editor);
        this._drawZoomIndicator(editor);
    },

    _rebuildTopoCache(editor, isDark, bounds, toMM, intW, intH, dpr, cssW, cssH) {
        if (!this._topoCache) {
            this._topoCache = document.createElement('canvas');
        }
        const offCanvas = this._topoCache;
        offCanvas.width = intW;
        offCanvas.height = intH;
        const ctx = offCanvas.getContext('2d');
        if (!ctx) return;

        const { scale } = bounds;

        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.clearRect(0, 0, intW, intH);
        ctx.scale(dpr, dpr);

        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';

        ctx.fillStyle = isDark ? '#1a1a1a' : '#F5F5F2';
        ctx.fillRect(0, 0, cssW, cssH);

        ctx.fillStyle = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
        const gs = 10;
        for (let gx = 0; gx < cssW; gx += gs) {
            for (let gy = 0; gy < cssH; gy += gs) {
                ctx.fillRect(gx, gy, 0.8, 0.8);
            }
        }

        const mmZoom = (editor.minimap && editor.minimap.zoom) || 1;
        const hiDetail = mmZoom >= 2;

        const defaultLinkFallback = editor.defaultLinkColor || (isDark ? '#ffffff' : '#666666');

        // ── Links ──
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        const selectedObjs = editor.selectedObjects || [];
        const selectedObj = editor.selectedObject;

        for (const obj of editor.objects) {
            if (obj.type !== 'link' && obj.type !== 'unbound') continue;
            const ep = editor.getLinkEndpoints(obj);
            if (!ep) continue;

            const p1 = toMM(ep.startX, ep.startY);
            const p2 = toMM(ep.endX, ep.endY);
            const rawColor = obj.color || defaultLinkFallback;
            const linkColor = editor.adjustColorForMode ? editor.adjustColorForMode(rawColor) : rawColor;
            const style = obj.style || 'solid';
            const isSelected = obj === selectedObj || selectedObjs.includes(obj);

            // Selection glow
            if (isSelected && hiDetail) {
                ctx.save();
                ctx.strokeStyle = '#3498db';
                ctx.lineWidth = Math.max(3, (obj.lineWidth || 2) * scale + 3);
                ctx.globalAlpha = 0.35;
                ctx.setLineDash([]);
                ctx.beginPath();
                if (obj._cp1 && obj._cp2) {
                    const cp1 = toMM(obj._cp1.x, obj._cp1.y);
                    const cp2 = toMM(obj._cp2.x, obj._cp2.y);
                    ctx.moveTo(p1.x, p1.y);
                    ctx.bezierCurveTo(cp1.x, cp1.y, cp2.x, cp2.y, p2.x, p2.y);
                } else {
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                }
                ctx.stroke();
                ctx.restore();
            }

            ctx.strokeStyle = linkColor;
            ctx.globalAlpha = 0.85;
            const baseW = (obj.lineWidth || 2) * scale;
            ctx.lineWidth = Math.max(0.8, Math.min(baseW, hiDetail ? 6 : 2.5));

            // Dash pattern scaled with zoom
            const dashScale = hiDetail ? 1.5 : 1;
            if (style.includes('dashed')) {
                ctx.setLineDash([4 * dashScale, 3 * dashScale]);
            } else if (style.includes('dotted')) {
                ctx.setLineDash([1.5 * dashScale, 2.5 * dashScale]);
            } else {
                ctx.setLineDash([]);
            }

            ctx.beginPath();
            if (obj._cp1 && obj._cp2) {
                const cp1 = toMM(obj._cp1.x, obj._cp1.y);
                const cp2 = toMM(obj._cp2.x, obj._cp2.y);
                ctx.moveTo(p1.x, p1.y);
                ctx.bezierCurveTo(cp1.x, cp1.y, cp2.x, cp2.y, p2.x, p2.y);
            } else {
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
            }
            ctx.stroke();

            // Arrow tips
            let arrowAtEnd = false, arrowAtStart = false;
            if (style.includes('arrow')) {
                const arrowSize = Math.max(3, Math.min(5 * scale * (obj.radius || 30), hiDetail ? 12 : 6));
                this._drawMiniArrow(ctx, p1, p2, obj._cp1 ? toMM(obj._cp2.x, obj._cp2.y) : null, arrowSize, linkColor);
                arrowAtEnd = true;
                if (style.includes('double')) {
                    this._drawMiniArrow(ctx, p2, p1, obj._cp1 ? toMM(obj._cp1.x, obj._cp1.y) : null, arrowSize, linkColor);
                    arrowAtStart = true;
                }
            }

            // Terminal points on unbound links — only at free endpoints, skip where arrow exists
            if (obj.type === 'unbound' && hiDetail) {
                const tpR = Math.max(1.5, Math.min(3 * scale * 10, 6));
                const startFree = !obj.device1 && !obj.mergedWith;
                const endFree = !obj.device2 && !obj.mergedInto;
                ctx.setLineDash([]);
                if (startFree && !arrowAtStart) {
                    ctx.beginPath();
                    ctx.arc(p1.x, p1.y, tpR, 0, Math.PI * 2);
                    ctx.fillStyle = isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.08)';
                    ctx.fill();
                    ctx.strokeStyle = linkColor;
                    ctx.lineWidth = 0.8;
                    ctx.stroke();
                }
                if (endFree && !arrowAtEnd) {
                    ctx.beginPath();
                    ctx.arc(p2.x, p2.y, tpR, 0, Math.PI * 2);
                    ctx.fillStyle = isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.08)';
                    ctx.fill();
                    ctx.strokeStyle = linkColor;
                    ctx.lineWidth = 0.8;
                    ctx.stroke();
                }
            }

            ctx.globalAlpha = 1;
            ctx.setLineDash([]);
        }

        // ── Devices ──
        for (const obj of editor.objects) {
            if (obj.type !== 'device') continue;
            const p = toMM(obj.x, obj.y);
            const r = Math.max(3, obj.radius * scale);
            const color = obj.color || '#3498db';
            const vs = obj.visualStyle || 'circle';
            const rot = (obj.rotation || 0) * Math.PI / 180;
            const isSelected = obj === selectedObj || selectedObjs.includes(obj);
            const border = isSelected ? '#3498db' : (isDark ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.5)');
            const detailed = r >= 8;

            // Selection glow behind device
            if (isSelected && r >= 4) {
                ctx.save();
                ctx.beginPath();
                ctx.arc(p.x, p.y, r + 3, 0, Math.PI * 2);
                ctx.strokeStyle = '#3498db';
                ctx.lineWidth = hiDetail ? 2 : 1.5;
                ctx.globalAlpha = 0.6;
                ctx.setLineDash([3, 2]);
                ctx.stroke();
                ctx.setLineDash([]);
                ctx.globalAlpha = 1;
                ctx.restore();
            }

            ctx.save();
            ctx.translate(p.x, p.y);
            ctx.rotate(rot);

            switch (vs) {
                case 'circle':
                    ctx.beginPath();
                    ctx.arc(0, 0, r, 0, Math.PI * 2);
                    ctx.fillStyle = color;
                    ctx.fill();
                    ctx.strokeStyle = border;
                    ctx.lineWidth = Math.min(1.5, r * 0.15);
                    ctx.stroke();
                    break;

                case 'hex': {
                    const hr = r * 0.85;
                    ctx.beginPath();
                    for (let i = 0; i < 6; i++) {
                        const a = Math.PI / 6 + i * Math.PI / 3;
                        const hx = Math.cos(a) * hr;
                        const hy = Math.sin(a) * hr;
                        i === 0 ? ctx.moveTo(hx, hy) : ctx.lineTo(hx, hy);
                    }
                    ctx.closePath();
                    if (detailed) {
                        const hGrad = ctx.createLinearGradient(-hr, -hr, hr, hr);
                        hGrad.addColorStop(0, this._lighten(color, 0.15));
                        hGrad.addColorStop(0.5, color);
                        hGrad.addColorStop(1, this._darken(color, 0.15));
                        ctx.fillStyle = hGrad;
                    } else {
                        ctx.fillStyle = color;
                    }
                    ctx.fill();
                    ctx.strokeStyle = border;
                    ctx.lineWidth = Math.min(1.5, r * 0.15);
                    ctx.stroke();
                    if (detailed) this._drawMiniCrossArrows(ctx, 0, 0, r * 0.35);
                    break;
                }

                case 'classic': {
                    const w = r * 1.6;
                    const topH = r * 0.4;
                    const bodyH = r * 0.6;

                    // Body
                    ctx.beginPath();
                    ctx.moveTo(-w / 2, -topH / 2);
                    ctx.lineTo(-w / 2, -topH / 2 + bodyH);
                    ctx.ellipse(0, -topH / 2 + bodyH, w / 2, topH / 2, 0, Math.PI, 0, true);
                    ctx.lineTo(w / 2, -topH / 2);
                    ctx.closePath();
                    if (detailed) {
                        const bGrad = ctx.createLinearGradient(-w / 2, 0, w / 2, 0);
                        bGrad.addColorStop(0, this._darken(color, 0.3));
                        bGrad.addColorStop(0.5, color);
                        bGrad.addColorStop(1, this._darken(color, 0.3));
                        ctx.fillStyle = bGrad;
                    } else {
                        ctx.fillStyle = color;
                    }
                    ctx.fill();
                    ctx.strokeStyle = border;
                    ctx.lineWidth = Math.min(1.5, r * 0.12);
                    ctx.stroke();

                    // Top ellipse
                    ctx.beginPath();
                    ctx.ellipse(0, -topH / 2, w / 2, topH / 2, 0, 0, Math.PI * 2);
                    ctx.fillStyle = this._lighten(color, 0.12);
                    ctx.fill();
                    ctx.strokeStyle = border;
                    ctx.stroke();

                    if (detailed) this._drawMiniCrossArrows(ctx, 0, -topH / 2, Math.min(w / 2 * 0.5, topH / 2 * 0.6), true);
                    break;
                }

                case 'server': {
                    const sw = r * 0.9;
                    const sh = r * 1.6;
                    const dep = r * 0.4;

                    if (detailed) {
                        // 3D right side
                        ctx.beginPath();
                        ctx.moveTo(sw / 2, -sh / 2 + dep);
                        ctx.lineTo(sw / 2 + dep * 0.7, -sh / 2);
                        ctx.lineTo(sw / 2 + dep * 0.7, sh / 2 - dep);
                        ctx.lineTo(sw / 2, sh / 2);
                        ctx.closePath();
                        ctx.fillStyle = this._darken(color, 0.45);
                        ctx.fill();
                        ctx.strokeStyle = border;
                        ctx.lineWidth = Math.min(1, r * 0.08);
                        ctx.stroke();

                        // 3D top
                        ctx.beginPath();
                        ctx.moveTo(-sw / 2, -sh / 2 + dep);
                        ctx.lineTo(-sw / 2 + dep * 0.7, -sh / 2);
                        ctx.lineTo(sw / 2 + dep * 0.7, -sh / 2);
                        ctx.lineTo(sw / 2, -sh / 2 + dep);
                        ctx.closePath();
                        ctx.fillStyle = this._darken(color, 0.25);
                        ctx.fill();
                        ctx.strokeStyle = border;
                        ctx.stroke();
                    }

                    // Front face
                    ctx.beginPath();
                    ctx.rect(-sw / 2, -sh / 2 + (detailed ? dep : 0), sw, sh - (detailed ? dep : 0));
                    if (detailed) {
                        const fGrad = ctx.createLinearGradient(0, -sh / 2 + dep, 0, sh / 2);
                        fGrad.addColorStop(0, this._lighten(color, 0.1));
                        fGrad.addColorStop(1, this._darken(color, 0.1));
                        ctx.fillStyle = fGrad;
                    } else {
                        ctx.fillStyle = color;
                    }
                    ctx.fill();
                    ctx.strokeStyle = border;
                    ctx.lineWidth = Math.min(1.5, r * 0.12);
                    ctx.stroke();

                    // Panel stripe
                    const panelTop = -sh / 2 + (detailed ? dep : 0) + sh * 0.06;
                    ctx.fillStyle = '#3a3a3a';
                    ctx.fillRect(-sw / 2 + sw * 0.15, panelTop, sw * 0.7, sh * 0.12);
                    // LEDs
                    if (detailed) {
                        ctx.beginPath();
                        ctx.arc(-sw / 2 + sw * 0.28, panelTop + sh * 0.06, r * 0.06, 0, Math.PI * 2);
                        ctx.fillStyle = '#2ecc71';
                        ctx.fill();
                        ctx.beginPath();
                        ctx.arc(-sw / 2 + sw * 0.42, panelTop + sh * 0.06, r * 0.06, 0, Math.PI * 2);
                        ctx.fillStyle = '#ff7a33';
                        ctx.fill();
                    }
                    break;
                }

                case 'simple': {
                    ctx.beginPath();
                    ctx.arc(0, 0, r, 0, Math.PI * 2);
                    ctx.fillStyle = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.85)';
                    ctx.fill();
                    ctx.strokeStyle = border;
                    ctx.lineWidth = Math.min(2, r * 0.15);
                    ctx.stroke();

                    // Center dot + cardinal arrows
                    ctx.beginPath();
                    ctx.arc(0, 0, r * 0.15, 0, Math.PI * 2);
                    ctx.fillStyle = border;
                    ctx.fill();

                    if (detailed) {
                        ctx.strokeStyle = border;
                        ctx.lineWidth = Math.min(1.5, r * 0.1);
                        const aLen = r * 0.65;
                        const aStart = r * 0.25;
                        [[0, -1], [1, 0], [0, 1], [-1, 0]].forEach(([dx, dy]) => {
                            ctx.beginPath();
                            ctx.moveTo(dx * aStart, dy * aStart);
                            ctx.lineTo(dx * aLen, dy * aLen);
                            ctx.stroke();
                            const hd = r * 0.15;
                            const ang = Math.atan2(dy, dx);
                            ctx.beginPath();
                            ctx.moveTo(dx * aLen, dy * aLen);
                            ctx.lineTo(dx * aLen - hd * Math.cos(ang - 0.5), dy * aLen - hd * Math.sin(ang - 0.5));
                            ctx.lineTo(dx * aLen - hd * Math.cos(ang + 0.5), dy * aLen - hd * Math.sin(ang + 0.5));
                            ctx.closePath();
                            ctx.fill();
                        });
                    }
                    break;
                }

                default:
                    ctx.beginPath();
                    ctx.arc(0, 0, r, 0, Math.PI * 2);
                    ctx.fillStyle = color;
                    ctx.fill();
                    break;
            }

            // Label — colors/position synced with main canvas
            if (r >= 5 && obj.label) {
                const fontSize = Math.max(3.5, Math.min(r * 0.55, hiDetail ? 14 : 10));
                const ff = obj.fontFamily || 'Arial';
                const fw = obj.fontWeight || 'bold';
                ctx.font = `${fw} ${fontSize}px ${ff}`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                let labelColor;
                if (vs === 'classic') {
                    labelColor = obj.labelColor || '#ffffff';
                } else {
                    labelColor = obj.labelColor || (isDark ? '#ECF0F1' : '#0d1b2a');
                }
                ctx.fillStyle = labelColor;
                ctx.globalAlpha = 0.9;
                let labelY = 0;
                if (vs === 'classic') labelY = r * 0.24;
                else if (vs === 'hex') labelY = r * 0.85;
                else if (vs === 'simple') labelY = r * 1.15;
                else if (vs === 'server') labelY = r * 1.05;
                ctx.fillText(obj.label, 0, labelY);
                ctx.globalAlpha = 1;
            }

            ctx.restore();
        }

        // ── Text objects ──
        for (const obj of editor.objects) {
            if (obj.type !== 'text') continue;
            const p = toMM(obj.x, obj.y);
            const textColor = obj.color || (isDark ? '#ccc' : '#333');
            const textScale = (obj.fontSize || 14) * scale;

            if (hiDetail && textScale >= 3 && obj.text) {
                ctx.save();
                ctx.translate(p.x, p.y);
                ctx.rotate((obj.rotation || 0) * Math.PI / 180);
                const maxFs = hiDetail ? 40 : 12;
                const fs = Math.max(3, Math.min(textScale, maxFs));
                const fontWeight = obj.bold ? 'bold' : 'normal';
                const fontStyle = obj.italic ? 'italic' : 'normal';
                ctx.font = `${fontStyle} ${fontWeight} ${fs}px ${obj.fontFamily || 'Arial'}`;
                ctx.textAlign = obj.textAlign || 'center';
                ctx.textBaseline = 'middle';

                const lines = obj.text.split('\n');
                const lineH = fs * 1.35;
                const startY = -(lines.length - 1) * lineH / 2;

                if (obj.showBackground && obj.backgroundColor) {
                    const maxW = lines.reduce((w, l) => Math.max(w, ctx.measureText(l).width), 0);
                    const totalH = lines.length * lineH;
                    const bgOpacity = obj.backgroundOpacity != null ? obj.backgroundOpacity : 0.6;
                    ctx.globalAlpha = bgOpacity;
                    ctx.fillStyle = obj.backgroundColor;
                    ctx.fillRect(-maxW / 2 - 4, startY - lineH / 2, maxW + 8, totalH + 4);
                    ctx.globalAlpha = 1;
                }

                ctx.fillStyle = textColor;
                ctx.globalAlpha = 0.9;
                lines.forEach((line, i) => {
                    ctx.fillText(line, 0, startY + i * lineH);
                });
                ctx.globalAlpha = 1;
                ctx.restore();
            } else {
                ctx.fillStyle = textColor;
                ctx.globalAlpha = 0.6;
                const sz = Math.max(1.5, 3 * scale * 30);
                ctx.fillRect(p.x - sz / 2, p.y - 1, sz, 2);
                ctx.globalAlpha = 1;
            }
        }

    },

    _drawViewport(ctx, isDark, cssW, cssH, toMM, viewLeft, viewTop, viewRight, viewBottom, editor) {
        const mmZoom = (editor.minimap && editor.minimap.zoom) || 1;
        const accent = isDark ? '#00d4ff' : '#0066fa';
        const accentRGB = isDark ? '0,212,255' : '0,102,250';

        if (mmZoom > 1) {
            this._drawZoomOverview(ctx, isDark, cssW, cssH, editor, accent, accentRGB);
        } else {
            const vpTL = toMM(viewLeft, viewTop);
            const vpBR = toMM(viewRight, viewBottom);
            let vpX = vpTL.x, vpY = vpTL.y;
            let vpW = vpBR.x - vpTL.x, vpH = vpBR.y - vpTL.y;

            if (vpW < 10) { vpX = (vpTL.x + vpBR.x) / 2 - 5; vpW = 10; }
            if (vpH < 10) { vpY = (vpTL.y + vpBR.y) / 2 - 5; vpH = 10; }

            ctx.strokeStyle = accent;
            ctx.lineWidth = 1.5;
            ctx.setLineDash([]);
            ctx.beginPath();
            ctx.roundRect(vpX, vpY, vpW, vpH, 3);
            ctx.stroke();

            const vpGrad = ctx.createLinearGradient(vpX, vpY, vpX, vpY + vpH);
            vpGrad.addColorStop(0, `rgba(${accentRGB}, 0.12)`);
            vpGrad.addColorStop(0.5, `rgba(${accentRGB}, 0.04)`);
            vpGrad.addColorStop(1, `rgba(${accentRGB}, 0.10)`);
            ctx.fillStyle = vpGrad;
            ctx.beginPath();
            ctx.roundRect(vpX, vpY, vpW, vpH, 3);
            ctx.fill();

            ctx.fillStyle = accent;
            const cd = 2;
            [[vpX, vpY], [vpX + vpW, vpY], [vpX, vpY + vpH], [vpX + vpW, vpY + vpH]].forEach(([cx, cy]) => {
                ctx.beginPath();
                ctx.arc(cx, cy, cd, 0, Math.PI * 2);
                ctx.fill();
            });
        }

        if (editor.marqueeActive && editor.selectionRectangle && !editor.csmsMode) {
            const bounds = editor.getMinimapBounds();
            if (bounds) {
                const sr = editor.selectionRectangle;
                const mmR = {
                    x: bounds.offsetX + (sr.x - bounds.minX) * bounds.scale,
                    y: bounds.offsetY + (sr.y - bounds.minY) * bounds.scale,
                    w: sr.width * bounds.scale,
                    h: sr.height * bounds.scale
                };
                if (mmR.x + mmR.w >= 0 && mmR.x <= cssW && mmR.y + mmR.h >= 0 && mmR.y <= cssH) {
                    const pulse = 0.7 + 0.3 * Math.sin(Date.now() / 400);
                    ctx.fillStyle = `rgba(52,152,219,${0.18 * pulse})`;
                    ctx.beginPath();
                    ctx.roundRect(mmR.x, mmR.y, mmR.w, mmR.h, 2);
                    ctx.fill();
                    ctx.strokeStyle = `rgba(52,152,219,${0.8 * pulse})`;
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }
            }
        }
    },

    _drawZoomOverview(ctx, isDark, cssW, cssH, editor, accent, accentRGB) {
        const bounds = editor.getMinimapBounds();
        if (!bounds || bounds.boundsWidth <= 0 || bounds.boundsHeight <= 0) return;

        const mmZoom = (editor.minimap && editor.minimap.zoom) || 1;
        const margin = 4;
        const overviewW = 46;
        const overviewH = Math.round(overviewW * cssH / cssW);
        const ox = cssW - overviewW - margin;
        const oy = cssH - overviewH - margin;

        ctx.save();

        ctx.fillStyle = isDark ? 'rgba(0,0,0,0.6)' : 'rgba(255,255,255,0.7)';
        ctx.beginPath();
        ctx.roundRect(ox - 1, oy - 1, overviewW + 2, overviewH + 2, 3);
        ctx.fill();
        ctx.strokeStyle = isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.15)';
        ctx.lineWidth = 0.5;
        ctx.stroke();

        const panX = editor.minimap.panX || 0;
        const panY = editor.minimap.panY || 0;
        const viewCX = (bounds.viewLeft + bounds.viewRight) / 2;
        const viewCY = (bounds.viewTop + bounds.viewBottom) / 2;
        const centerX = viewCX + panX;
        const centerY = viewCY + panY;

        const fracCX = (centerX - bounds.minX) / bounds.boundsWidth;
        const fracCY = (centerY - bounds.minY) / bounds.boundsHeight;

        const visWorldW = cssW / bounds.scale;
        const visWorldH = cssH / bounds.scale;
        const fracW = Math.min(1, visWorldW / bounds.boundsWidth);
        const fracH = Math.min(1, visWorldH / bounds.boundsHeight);

        const zoomW = fracW * overviewW;
        const zoomH = fracH * overviewH;
        let zoomX = ox + fracCX * overviewW - zoomW / 2;
        let zoomY = oy + fracCY * overviewH - zoomH / 2;

        zoomX = Math.max(ox, Math.min(zoomX, ox + overviewW - zoomW));
        zoomY = Math.max(oy, Math.min(zoomY, oy + overviewH - zoomH));

        ctx.beginPath();
        ctx.rect(ox, oy, overviewW, overviewH);
        ctx.clip();

        ctx.fillStyle = `rgba(${accentRGB}, 0.25)`;
        ctx.beginPath();
        ctx.roundRect(zoomX, zoomY, zoomW, zoomH, 1.5);
        ctx.fill();

        ctx.strokeStyle = accent;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(zoomX, zoomY, zoomW, zoomH, 1.5);
        ctx.stroke();

        const cd = 1.2;
        ctx.fillStyle = accent;
        [[zoomX, zoomY], [zoomX + zoomW, zoomY], [zoomX, zoomY + zoomH], [zoomX + zoomW, zoomY + zoomH]].forEach(([cx, cy]) => {
            ctx.beginPath();
            ctx.arc(cx, cy, cd, 0, Math.PI * 2);
            ctx.fill();
        });

        ctx.restore();
    },

    _drawZoomIndicator(editor) {
        const zi = document.getElementById('minimap-zoom-indicator');
        if (!zi) return;
        const pct = Math.round(editor.zoom * 100);
        zi.textContent = `${pct}%`;
        const isLight = document.body.classList.contains('light-mode');
        if (pct < 50) {
            zi.style.color = isLight ? '#fff' : 'rgba(255,150,100,0.9)';
            zi.style.borderColor = isLight ? 'rgba(255,180,120,0.4)' : 'rgba(255,150,100,0.3)';
            zi.style.background = isLight ? 'rgba(180,100,50,0.9)' : 'rgba(255,150,100,0.1)';
        } else if (pct > 150) {
            zi.style.color = isLight ? '#fff' : 'rgba(100,255,150,0.9)';
            zi.style.borderColor = isLight ? 'rgba(120,255,180,0.4)' : 'rgba(100,255,150,0.3)';
            zi.style.background = isLight ? 'rgba(50,140,80,0.9)' : 'rgba(100,255,150,0.1)';
        } else {
            zi.style.color = isLight ? '#fff' : 'rgba(100,200,255,0.8)';
            zi.style.borderColor = isLight ? 'rgba(255,255,255,0.25)' : 'rgba(100,200,255,0.2)';
            zi.style.background = isLight ? 'rgba(30,64,120,0.9)' : 'rgba(100,200,255,0.1)';
        }
        zi.style.boxShadow = isLight ? '0 2px 6px rgba(0,0,0,0.25)' : '';
    },

    _drawMiniArrow(ctx, from, to, cpBefore, size, color) {
        let angle;
        if (cpBefore) {
            angle = Math.atan2(to.y - cpBefore.y, to.x - cpBefore.x);
        } else {
            angle = Math.atan2(to.y - from.y, to.x - from.x);
        }
        const s = Math.min(size, 8);
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.moveTo(to.x, to.y);
        ctx.lineTo(to.x - s * Math.cos(angle - 0.45), to.y - s * Math.sin(angle - 0.45));
        ctx.lineTo(to.x - s * Math.cos(angle + 0.45), to.y - s * Math.sin(angle + 0.45));
        ctx.closePath();
        ctx.fill();
    },

    _drawMiniCrossArrows(ctx, cx, cy, size, elliptical) {
        ctx.save();
        ctx.translate(cx, cy);
        ctx.strokeStyle = 'rgba(255,255,255,0.8)';
        ctx.fillStyle = 'rgba(255,255,255,0.8)';
        ctx.lineWidth = Math.max(0.6, size * 0.12);
        const angles = [-Math.PI / 4, Math.PI / 4, 3 * Math.PI / 4, -3 * Math.PI / 4];
        const sx = elliptical ? 0.7 : 1;
        const sy = elliptical ? 0.5 : 1;
        angles.forEach(a => {
            const tx = Math.cos(a) * size * sx;
            const ty = Math.sin(a) * size * sy;
            ctx.beginPath();
            ctx.moveTo(0, 0);
            ctx.lineTo(tx, ty);
            ctx.stroke();
            const hd = size * 0.3;
            ctx.beginPath();
            ctx.moveTo(tx, ty);
            ctx.lineTo(tx - hd * Math.cos(a - 0.4) * sx, ty - hd * Math.sin(a - 0.4) * sy);
            ctx.lineTo(tx - hd * Math.cos(a + 0.4) * sx, ty - hd * Math.sin(a + 0.4) * sy);
            ctx.closePath();
            ctx.fill();
        });
        ctx.restore();
    },

    _darken(hex, amt) {
        if (!hex || hex[0] !== '#' || hex.length < 7) return hex || '#333';
        const r = Math.max(0, parseInt(hex.slice(1, 3), 16) * (1 - amt));
        const g = Math.max(0, parseInt(hex.slice(3, 5), 16) * (1 - amt));
        const b = Math.max(0, parseInt(hex.slice(5, 7), 16) * (1 - amt));
        return `rgb(${Math.round(r)},${Math.round(g)},${Math.round(b)})`;
    },

    _lighten(hex, amt) {
        if (!hex || hex[0] !== '#' || hex.length < 7) return hex || '#888';
        const r = Math.min(255, parseInt(hex.slice(1, 3), 16) + (255 - parseInt(hex.slice(1, 3), 16)) * amt);
        const g = Math.min(255, parseInt(hex.slice(3, 5), 16) + (255 - parseInt(hex.slice(3, 5), 16)) * amt);
        const b = Math.min(255, parseInt(hex.slice(5, 7), 16) + (255 - parseInt(hex.slice(5, 7), 16)) * amt);
        return `rgb(${Math.round(r)},${Math.round(g)},${Math.round(b)})`;
    }
};

console.log('[topology-minimap-render.js] MinimapRender loaded (high-fidelity)');
