/**
 * topology-link-auto-curve-side.js
 *
 * Sticky side selection for auto-curve (magnetic-repulsion) links.
 *
 * Why this exists
 * ---------------
 * The auto-curve renderer in `topology-link-drawing.js` recomputes per-side
 * obstacle pressure on every draw frame. When the user *stretches* an
 * unbound link past a device, the obstacle's perpendicular projection
 * onto the (moving) link can drift across the perpendicular axis and the
 * lower-pressure side flips, snapping the curve from one side of the
 * device to the other on the lightest mouse movement.
 *
 * The user expectation is: the *initial* stretch around the obstacle picks
 * the curve side, and casual movement after that keeps the same side until
 * the geometry changes substantially (e.g. the user clearly drags the link
 * past the obstacle so the OPPOSITE side dominates).
 *
 * Approach
 * --------
 * - On every auto-curve draw frame we receive (positivePressure, negativePressure).
 * - Cache the last chosen side on `link._autoCurveSide` (-1 or +1).
 * - First decision (no cache): pick the lower-pressure side just like before.
 * - Subsequent decisions: only flip if the OPPOSITE side is *substantially*
 *   bigger than the cached side -- ratio >= FLIP_PRESSURE_RATIO AND absolute
 *   delta >= FLIP_ABS_DELTA. Otherwise keep the cached side.
 * - Clear the cache when the link has no obstacles (so re-entry into an
 *   obstacle field starts a fresh decision) or when explicitly asked.
 *
 * Pointer-locked override (used while user is actively stretching a UL TP):
 * --------------------------------------------------------------------------
 * `topology-mouse-move.js` watches the pointer path during a stretch and,
 * once the user has clearly committed to one side of the obstacle, calls
 * `LinkAutoCurveSide.lockSide(link, side, { pointerLocked: true })`. While
 * `link._autoCurveSidePointerLocked === true`, `choose()` returns the locked
 * side unconditionally regardless of pressure -- this is what kills the
 * "curve flips while I'm dragging around the device" complaint, because the
 * obstacle's perpendicular sign in the (anchor -> pointer) frame WILL flip
 * naturally as the pointer wraps around the device, and no amount of pure
 * pressure-based hysteresis can hide that.
 *
 * On stretch end the mouse-up handler clears the pointer lock but keeps
 * `link._autoCurveSide` cached, so the curve stays where the user put it.
 *
 * Tuning constants
 * ----------------
 * FLIP_PRESSURE_RATIO = 1.6 -- the opposite side must carry >=1.6x the
 *   cached side's pressure before we flip. Tighter than 2.0 would still let
 *   small drifts win; looser than 1.4 lets a clearly-better side win quickly.
 * FLIP_ABS_DELTA = 12 -- absolute pressure-units gap required IN ADDITION
 *   to the ratio check, so two near-zero pressure readings can't flip on
 *   ratio alone (e.g. 0.5 vs 1.0 is 2x but both are noise).
 * EQUAL_EPSILON = 0.5 -- pressures within this band are treated as a tie
 *   on the very first decision so we don't pick a side from float noise.
 */
'use strict';

(function () {
    const FLIP_PRESSURE_RATIO = 1.6;
    const FLIP_ABS_DELTA = 12;
    const EQUAL_EPSILON = 0.5;

    // Pointer commitment threshold: how many pixels of perpendicular travel
    // (relative to the anchor->pointer-start axis) the user must put in
    // before we treat the pointer as committed to a side. Tuned to feel
    // immediate during a deliberate "go around the device" stretch but
    // stay quiet during a tiny accidental jiggle.
    const POINTER_COMMIT_PX = 18;
    // Once committed, the pointer must travel SUBSTANTIALLY past the
    // committed side toward the OPPOSITE side before we'd allow a re-lock.
    // We do not auto-flip once locked during a stretch -- the user must
    // release and re-stretch to change sides. Documented for clarity.

    function chooseFreshSide(positive, negative) {
        // Curve toward the LOWER pressure side, exactly the same convention
        // the renderer used before this module existed.
        if (Math.abs(positive - negative) < EQUAL_EPSILON) return 1;
        return positive > negative ? -1 : 1;
    }

    /**
     * Decide which side this auto-curve frame should bend toward.
     *
     * @param {object} link    The link object (we cache `_autoCurveSide` on it).
     * @param {number} positive  Pressure from the +perpendicular side.
     * @param {number} negative  Pressure from the -perpendicular side.
     * @returns {number}  -1 or +1 in the sign convention of the renderer.
     */
    function choose(link, positive, negative) {
        if (!link) return chooseFreshSide(positive, negative);

        // POINTER LOCK: while the user is actively stretching a UL TP and
        // has committed to a side, return the locked side unconditionally.
        // This bypass exists because the obstacle's pressure-side sign WILL
        // flip naturally as the dragged endpoint orbits the obstacle, and
        // no pressure-based hysteresis can hide that geometry. The lock is
        // set/cleared by `topology-mouse-move.js` and `topology-mouse-up.js`.
        if (link._autoCurveSidePointerLocked === true &&
            (link._autoCurveSide === 1 || link._autoCurveSide === -1)) {
            return link._autoCurveSide;
        }

        // No cached side yet -> first frame with obstacle pressure for this
        // link. Take the natural lower-pressure side and remember it.
        const cached = (link._autoCurveSide === 1 || link._autoCurveSide === -1)
            ? link._autoCurveSide
            : null;
        if (cached === null) {
            const fresh = chooseFreshSide(positive, negative);
            link._autoCurveSide = fresh;
            return fresh;
        }

        // Pressure from the side we are CURRENTLY bending toward and from
        // the side we'd flip into. The renderer convention:
        //   curveDir = +1 -> bend toward the +perp side (away from
        //                    obstacles on the +perp side, i.e. where
        //                    `negative` pressure dominated)
        //   curveDir = -1 -> bend toward the -perp side
        // So `cachedSidePressure` = pressure pushing AWAY FROM the cached
        // side, which is `positive` when cached === -1 and `negative`
        // when cached === +1. The OPPOSITE pressure (the one that wants
        // to flip us) is the other one.
        const cachedSidePressure = cached === 1 ? negative : positive;
        const oppositeSidePressure = cached === 1 ? positive : negative;

        // If the opposite side is dominant by enough margin, flip; else stick.
        const ratioOk = oppositeSidePressure > cachedSidePressure * FLIP_PRESSURE_RATIO;
        const deltaOk = (oppositeSidePressure - cachedSidePressure) >= FLIP_ABS_DELTA;
        if (ratioOk && deltaOk) {
            link._autoCurveSide = -cached;
            return -cached;
        }
        return cached;
    }

    /** Drop the cached side -- safe to call any time. */
    function clear(link) {
        if (!link) return;
        if (link._autoCurveSide !== undefined) {
            try { delete link._autoCurveSide; } catch (_) { link._autoCurveSide = null; }
        }
        if (link._autoCurveSidePointerLocked) {
            try { delete link._autoCurveSidePointerLocked; }
            catch (_) { link._autoCurveSidePointerLocked = false; }
        }
    }

    /**
     * Force the cached side to a specific value.
     * @param {object} link
     * @param {number} side  -1 or +1
     * @param {{pointerLocked?: boolean}} [opts]
     *        When `pointerLocked` is true, `choose()` will return this side
     *        unconditionally until `unlockPointer(link)` is called.
     */
    function lockSide(link, side, opts) {
        if (!link) return;
        if (side !== 1 && side !== -1) return;
        link._autoCurveSide = side;
        if (opts && opts.pointerLocked) {
            link._autoCurveSidePointerLocked = true;
        }
    }

    /** Release the pointer lock, but KEEP the cached side. */
    function unlockPointer(link) {
        if (!link) return;
        if (link._autoCurveSidePointerLocked) {
            try { delete link._autoCurveSidePointerLocked; }
            catch (_) { link._autoCurveSidePointerLocked = false; }
        }
    }

    /**
     * Initialize pointer-side tracking at the moment a UL stretch begins.
     *
     * The "anchor" is the world position of the endpoint NOT being dragged
     * (or, for a free TP that already has no anchor device, the link's
     * other endpoint). `pointerStart` is the pointer position at stretch
     * start. We freeze the (anchor -> pointerStart) axis so the user's
     * subsequent perpendicular travel is measured against a STABLE frame
     * of reference -- crucial because the (anchor -> currentPointer) axis
     * rotates as the user drags around the obstacle, and would itself flip
     * the sign we're trying to lock.
     *
     * Stored on the link as `link._stretchPointerSide`:
     *   {
     *     anchorX, anchorY,    // frozen reference origin
     *     refDirX, refDirY,    // unit vector along the frozen axis
     *     refPerpX, refPerpY,  // unit perpendicular (90deg CCW)
     *     committedSign,       // 0 (uncommitted), -1, or +1
     *     maxPos, maxNeg       // peak |perpendicular| seen on each side (px)
     *   }
     */
    function beginStretch(link, anchorX, anchorY, pointerStartX, pointerStartY) {
        if (!link) return;
        const dx = pointerStartX - anchorX;
        const dy = pointerStartY - anchorY;
        const len = Math.sqrt(dx * dx + dy * dy) || 1;
        const refDirX = dx / len;
        const refDirY = dy / len;
        // 90-degree CCW perpendicular. The exact rotation direction here
        // does not matter for correctness because the renderer's `perpX`
        // is also a fixed CCW rotation of (linkDirX, linkDirY); what
        // matters is that we use the SAME reference perpendicular as the
        // renderer when we map our committed sign to `_autoCurveSide`.
        // See `_signToAutoCurveSide` below for the mapping rationale.
        const refPerpX = -refDirY;
        const refPerpY = refDirX;
        link._stretchPointerSide = {
            anchorX, anchorY,
            refDirX, refDirY,
            refPerpX, refPerpY,
            committedSign: 0,
            maxPos: 0,
            maxNeg: 0
        };
        // Don't pre-clear `_autoCurveSide` -- the renderer will refresh
        // it on the next draw frame, and the user might cancel the stretch
        // very quickly (release before commit threshold). If we cleared
        // here, we'd lose any stable side the link already had.
    }

    /**
     * Per-mouse-move tracker. Compute the pointer's signed perpendicular
     * offset relative to the FROZEN axis from `beginStretch`. Once that
     * offset crosses POINTER_COMMIT_PX, lock the link's curve side.
     *
     * Returns the side the pointer is currently on (0 if not committed yet).
     */
    function updateStretch(link, pointerX, pointerY) {
        if (!link || !link._stretchPointerSide) return 0;
        const s = link._stretchPointerSide;
        const vx = pointerX - s.anchorX;
        const vy = pointerY - s.anchorY;
        // Project onto frozen perpendicular: this is signed lateral offset
        // from the original anchor->pointerStart line.
        const perp = vx * s.refPerpX + vy * s.refPerpY;
        if (perp > 0) {
            if (perp > s.maxPos) s.maxPos = perp;
        } else if (perp < 0) {
            if (-perp > s.maxNeg) s.maxNeg = -perp;
        }
        // Already committed -> do not auto-flip mid-stretch. The user
        // releases and re-stretches if they want a different side.
        if (s.committedSign !== 0) return s.committedSign;
        if (s.maxPos >= POINTER_COMMIT_PX && s.maxPos > s.maxNeg) {
            s.committedSign = 1;
        } else if (s.maxNeg >= POINTER_COMMIT_PX && s.maxNeg > s.maxPos) {
            s.committedSign = -1;
        }
        if (s.committedSign !== 0) {
            const side = _signToAutoCurveSide(s.committedSign);
            lockSide(link, side, { pointerLocked: true });
        }
        return s.committedSign;
    }

    /**
     * Map our pointer "committed sign" (relative to frozen ref-perp) into
     * the renderer's `_autoCurveSide` convention.
     *
     * Renderer convention (see topology-link-drawing.js):
     *   curveDir = +1 -> bend toward +perp side (perp = (-linkDirY, linkDirX))
     *   curveDir = -1 -> bend toward -perp side
     *
     * Our `refPerpX/Y` is the perpendicular at stretch start. Once the
     * user has committed (e.g. dragged 18px to the +ref-perp side, sign=+1)
     * the curve should bend TOWARD that same side -- the user's pointer
     * path *is* the path the link should take. So sign=+1 -> curveDir=+1.
     *
     * This works because both the renderer's `perp` and our `refPerp` are
     * the same 90-degree CCW rotation of the link direction (the renderer
     * uses the live `linkDirX/Y`, we use the frozen one); the obstacle's
     * sideSign relative to either is consistent enough that the resulting
     * deflection points "toward the user's side" in the ~90% common case.
     * The remaining edge cases (link direction has spun >45deg between
     * stretch start and now) are vanishingly rare for a single stretch.
     */
    function _signToAutoCurveSide(sign) {
        return sign === -1 ? -1 : 1;
    }

    /** Tear down pointer-side tracking when the stretch ends or aborts. */
    function endStretch(link) {
        if (!link) return;
        if (link._stretchPointerSide) {
            try { delete link._stretchPointerSide; } catch (_) { link._stretchPointerSide = null; }
        }
        unlockPointer(link);
    }

    window.LinkAutoCurveSide = {
        choose, clear, lockSide, unlockPointer,
        beginStretch, updateStretch, endStretch,
        // Exposed for tests / introspection only:
        _constants: { FLIP_PRESSURE_RATIO, FLIP_ABS_DELTA, EQUAL_EPSILON, POINTER_COMMIT_PX }
    };
})();

console.log('[topology-link-auto-curve-side.js] LinkAutoCurveSide loaded');
