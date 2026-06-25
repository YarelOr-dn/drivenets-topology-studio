#!/usr/bin/env node
/**
 * Smoke test for transient laser trail interpolation.
 */

'use strict';

const assert = require('assert');
const path = require('path');

const laser = require(path.join(__dirname, '..', 'topology-laser.js'));

function makeEditor(overrides = {}) {
    return {
        _laserTrail: [],
        _laserFadeMs: 850,
        zoom: 1,
        objects: [],
        ...overrides
    };
}

{
    const editor = makeEditor();
    laser.appendTrailPoint(editor, { x: 0, y: 0 }, 100);
    assert.strictEqual(editor._laserTrail.length, 1, 'first laser point should be stored');
    assert.deepStrictEqual(editor.objects, [], 'laser must not create saved objects');
}

{
    const editor = makeEditor();
    laser.appendTrailPoint(editor, { x: 0, y: 0 }, 100, { stepScreenPx: 10 });
    laser.appendTrailPoint(editor, { x: 100, y: 0 }, 140, { stepScreenPx: 10 });

    assert(editor._laserTrail.length > 2, 'far clicks should interpolate intermediate trail points');
    const lastPoint = editor._laserTrail[editor._laserTrail.length - 1];
    assert.strictEqual(lastPoint.x, 100, 'last point should use the requested x position');
    assert.strictEqual(lastPoint.y, 0, 'last point should use the requested y position');
    assert.strictEqual(lastPoint.t, 140, 'last point should use the requested timestamp');
    for (let i = 1; i < editor._laserTrail.length; i++) {
        assert(editor._laserTrail[i].x >= editor._laserTrail[i - 1].x, 'interpolated points should progress along the segment');
    }
}

{
    const editor = makeEditor();
    laser.beginTrailStroke(editor, { x: 0, y: 0 }, 100, { stepScreenPx: 10 });
    laser.endTrailStroke(editor);
    laser.beginTrailStroke(editor, { x: 100, y: 0 }, 180, { stepScreenPx: 10 });

    assert.strictEqual(editor._laserTrail.length, 2, 'separate laser clicks should not interpolate a bridge segment');
    assert.notStrictEqual(
        editor._laserTrail[0].strokeId,
        editor._laserTrail[1].strokeId,
        'separate laser strokes should carry different stroke ids'
    );
    assert.strictEqual(editor._laserTrail[1].breakBefore, true, 'new stroke head should mark a render break');
}

{
    const editor = makeEditor();
    laser.appendTrailPoint(editor, { x: 0, y: 0 }, 100);
    laser.appendTrailPoint(editor, { x: 1000, y: 0 }, 120, { maxInterpolatedPoints: 5 });
    assert.strictEqual(editor._laserTrail.length, 7, 'interpolation should be capped to avoid heavy draw loops');
}

{
    const editor = makeEditor({ _laserFadeMs: 500 });
    laser.appendTrailPoint(editor, { x: 0, y: 0 }, 0);
    laser.appendTrailPoint(editor, { x: 100, y: 0 }, 1000);
    assert.strictEqual(editor._laserTrail.length, 1, 'expired points should not create stale bridge segments');
    assert.strictEqual(editor._laserTrail[0].x, 100, 'new point should remain after stale trail is pruned');
}

console.log('[OK] laser trail continuity smoke passed');
