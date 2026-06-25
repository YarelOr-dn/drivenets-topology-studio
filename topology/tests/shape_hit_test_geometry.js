#!/usr/bin/env node
/**
 * Static regression coverage for shape hit-test geometry.
 */

'use strict';

const assert = require('assert');
const path = require('path');

global.window = global;
require(path.join(__dirname, '..', 'topology-shape-methods.js'));

const editor = { zoom: 1 };

function hit(shape, x, y, options = {}) {
    return global.ShapeMethods.hitTestShape(editor, shape, x, y, options);
}

{
    const diamond = { type: 'shape', shapeType: 'diamond', x: 100, y: 100, width: 80, height: 80 };
    assert(hit(diamond, 100, 100), 'diamond center should hit');
    assert(hit(diamond, 100, 60), 'diamond top vertex should hit');
    assert(!hit(diamond, 68, 68, { screenTolerance: 2 }), 'diamond bounding-box corner should not hit');
}

{
    const triangle = { type: 'shape', shapeType: 'triangle', x: 100, y: 100, width: 80, height: 60 };
    assert(hit(triangle, 100, 102), 'triangle interior should hit');
    assert(!hit(triangle, 62, 72, { screenTolerance: 2 }), 'triangle upper bounding-box corner should not hit');
}

{
    const ellipse = { type: 'shape', shapeType: 'ellipse', x: 100, y: 100, width: 100, height: 40 };
    assert(hit(ellipse, 100, 100), 'ellipse center should hit');
    assert(!hit(ellipse, 55, 78, { screenTolerance: 2 }), 'ellipse bounding-box corner should not hit');
}

{
    const line = {
        type: 'shape',
        shapeType: 'line',
        x: 100,
        y: 100,
        width: 100,
        height: 2,
        fillEnabled: false,
        strokeWidth: 2
    };
    assert(hit(line, 120, 101), 'line body should hit near the stroke');
    assert(!hit(line, 120, 118, { screenTolerance: 3 }), 'line rectangular false-positive should not hit');
}

{
    const arrow = {
        type: 'shape',
        shapeType: 'arrow',
        x: 100,
        y: 100,
        width: 100,
        height: 30,
        fillEnabled: false,
        strokeWidth: 2
    };
    assert(hit(arrow, 75, 100), 'arrow shaft should hit');
    assert(!hit(arrow, 85, 113, { screenTolerance: 3 }), 'arrow empty bounding-box area should not hit');
}

console.log('[OK] shape hit-test geometry smoke passed');
