#!/usr/bin/env node
/**
 * Static contract checks for empty manual groups in the Groups panel.
 */

'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const panel = fs.readFileSync(path.join(root, 'topology-groups-panel.js'), 'utf8');
const groups = fs.readFileSync(path.join(root, 'topology-groups.js'), 'utf8');

assert(
    /function _createEmptyManualGroup/.test(panel),
    'Groups panel should support creating a manual group without selected objects'
);

assert(
    /!selected \|\| selected\.length < 2[\s\S]*return _createEmptyManualGroup/.test(panel),
    'new group flow should not block when fewer than two objects are selected'
);

assert(
    /emptyManualGroups/.test(panel) && /emptyManualGroups/.test(groups),
    'empty group metadata should be registered and respected by validation'
);

assert(
    /target\.members\.find[\s\S]*\|\| target\.members\[0\] \|\| obj/.test(panel),
    'adding the first object to an empty group should make that object the leader'
);

assert(
    /Create an empty group here, then add objects later/.test(panel),
    'empty Groups panel copy should invite empty group creation'
);

console.log('[OK] groups empty group contract smoke passed');
