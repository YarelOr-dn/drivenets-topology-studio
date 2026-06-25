/**
 * topology-laser.js - transient laser pointer trail helpers.
 *
 * The laser trail is UI-only state. Keep it in editor._laserTrail and never
 * add laser points to editor.objects or topology JSON.
 */

'use strict';

(function initTopologyLaser(root) {
    const DEFAULT_MAX_TRAIL_POINTS = 160;
    const DEFAULT_STEP_SCREEN_PX = 14;
    const DEFAULT_MAX_INTERPOLATED_POINTS = 28;

    function nowMs() {
        return (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
    }

    function getFadeMs(editor) {
        const configuredFadeMs = parseInt(editor && editor._laserFadeMs, 10);
        return Number.isFinite(configuredFadeMs) && configuredFadeMs >= 250 && configuredFadeMs <= 3000
            ? configuredFadeMs
            : 850;
    }

    function trimTrail(trail, maxPoints) {
        if (trail.length > maxPoints) {
            trail.splice(0, trail.length - maxPoints);
        }
    }

    function pruneExpiredTrail(editor, timestamp, fadeMs) {
        if (!Array.isArray(editor._laserTrail)) {
            editor._laserTrail = [];
            return editor._laserTrail;
        }
        editor._laserTrail = editor._laserTrail.filter(point => (
            point &&
            Number.isFinite(point.x) &&
            Number.isFinite(point.y) &&
            Number.isFinite(point.t) &&
            (timestamp - point.t) < fadeMs
        ));
        return editor._laserTrail;
    }

    function nextStrokeId(editor) {
        const current = Number.isFinite(editor._laserStrokeId) ? editor._laserStrokeId : 0;
        editor._laserStrokeId = current + 1;
        editor._laserActiveStrokeId = editor._laserStrokeId;
        return editor._laserActiveStrokeId;
    }

    function appendTrailPoint(editor, pos, timestamp = nowMs(), options = {}) {
        if (!editor || !pos) return [];

        const x = Number(pos.x);
        const y = Number(pos.y);
        if (!Number.isFinite(x) || !Number.isFinite(y)) {
            return Array.isArray(editor._laserTrail) ? editor._laserTrail : [];
        }

        const fadeMs = Number.isFinite(options.fadeMs) ? options.fadeMs : getFadeMs(editor);
        const maxPoints = Number.isFinite(options.maxPoints) ? Math.max(1, options.maxPoints) : DEFAULT_MAX_TRAIL_POINTS;
        const trail = pruneExpiredTrail(editor, timestamp, fadeMs);
        const last = trail.length > 0 ? trail[trail.length - 1] : null;
        const strokeId = Number.isFinite(options.strokeId)
            ? options.strokeId
            : (Number.isFinite(editor._laserActiveStrokeId) ? editor._laserActiveStrokeId : 0);
        const startsNewStroke = !!options.startNewStroke;

        if (last && !startsNewStroke && last.strokeId === strokeId) {
            const dx = x - last.x;
            const dy = y - last.y;
            const distance = Math.hypot(dx, dy);

            if (distance < 0.01) {
                last.t = timestamp;
                trimTrail(trail, maxPoints);
                return trail;
            }

            const zoom = Number.isFinite(editor.zoom) && editor.zoom > 0 ? editor.zoom : 1;
            const stepScreenPx = Number.isFinite(options.stepScreenPx) ? Math.max(4, options.stepScreenPx) : DEFAULT_STEP_SCREEN_PX;
            const stepWorldPx = Math.max(2, stepScreenPx / zoom);
            const desiredIntermediatePoints = Math.max(0, Math.floor(distance / stepWorldPx));
            const maxInterpolatedPoints = Number.isFinite(options.maxInterpolatedPoints)
                ? Math.max(0, options.maxInterpolatedPoints)
                : DEFAULT_MAX_INTERPOLATED_POINTS;
            const intermediatePoints = Math.min(maxInterpolatedPoints, desiredIntermediatePoints);

            for (let i = 1; i <= intermediatePoints; i++) {
                const ratio = i / (intermediatePoints + 1);
                const pointTime = Number.isFinite(last.t)
                    ? last.t + ((timestamp - last.t) * ratio)
                    : timestamp;
                trail.push({
                    x: last.x + (dx * ratio),
                    y: last.y + (dy * ratio),
                    t: pointTime,
                    strokeId
                });
            }
        }

        trail.push({ x, y, t: timestamp, strokeId, breakBefore: startsNewStroke });
        trimTrail(trail, maxPoints);
        return trail;
    }

    function beginTrailStroke(editor, pos, timestamp = nowMs(), options = {}) {
        if (!editor) return [];
        const strokeId = nextStrokeId(editor);
        return appendTrailPoint(editor, pos, timestamp, {
            ...options,
            strokeId,
            startNewStroke: true
        });
    }

    function endTrailStroke(editor) {
        if (!editor) return;
        editor._laserActiveStrokeId = null;
    }

    const api = {
        appendTrailPoint,
        beginTrailStroke,
        endTrailStroke,
        pruneExpiredTrail,
        getFadeMs
    };

    root.TopologyLaser = api;
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = api;
    }
})(typeof window !== 'undefined' ? window : globalThis);
