#!/usr/bin/env node
/**
 * Static/runtime regression coverage for packet callout objects.
 */

'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

global.window = global;
require(path.join(__dirname, '..', 'topology-packets.js'));

function makeCtx() {
    return {
        save() {},
        restore() {},
        beginPath() {},
        moveTo() {},
        lineTo() {},
        quadraticCurveTo() {},
        closePath() {},
        fill() {},
        stroke() {},
        setLineDash() {},
        translate() {},
        rotate() {},
        fillText() {},
        measureText(text) {
            return { width: String(text || '').length * 6 };
        }
    };
}

const editor = {
    ctx: makeCtx(),
    zoom: 1,
    objects: [
        {
            type: 'link',
            id: 'link_1',
            start: { x: 0, y: 0 },
            end: { x: 100, y: 0 }
        }
    ],
    saveState() {},
    draw() {}
};

{
    const packet = global.PacketMethods.createPacket(editor, {
        linkId: 'link_1',
        linkAttachT: 0.5,
        title: 'Very long packet title that should fit safely',
        presetLayers: { l2: 'src 00:11:22:33:44:55\ndst aa:bb:cc:dd:ee:ff', l3: 'src 10.0.0.1\ndst 10.0.0.2' }
    });
    assert(packet.y < 0, 'default packet side should float above a horizontal link');

    packet.side = 'below';
    global.PacketMethods.updatePacketPosition(editor, packet);
    assert(packet.y > 0, 'below-side packet should float below a horizontal link');

    packet.direction = 'backward';
    assert.strictEqual(
        global.PacketMethods.findPacketSummaryHit(editor, packet, packet.x, packet.y + packet._renderedHeight || packet.y),
        null,
        'summary hit test should tolerate missing rendered height without throwing'
    );
}

{
    const popupSource = fs.readFileSync(path.join(__dirname, '..', 'topology-packet-popup.js'), 'utf8');
    assert(
        /packet\.x \* editor\.zoom \+ pan\.x/.test(popupSource),
        'packet popup position should apply pan after zoom, not multiply pan by zoom'
    );
    assert(
        /\(bounds\.x - bounds\.w \/ 2\) \* zoom \+ pan\.x/.test(popupSource),
        'summary editor position should apply pan after zoom'
    );
    assert(
        /Move below|Move above/.test(popupSource),
        'packet popup should expose side switching for link callouts'
    );
}

console.log('[OK] packet object contract smoke passed');
