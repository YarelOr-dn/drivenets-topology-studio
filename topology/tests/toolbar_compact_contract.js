#!/usr/bin/env node
/**
 * Static contract checks for the compact left toolbar.
 */

'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const css = fs.readFileSync(path.join(root, 'styles.css'), 'utf8');

assert(
    /id="left-toolbar"[^>]*tool-rail-mode|tool-rail-mode[^>]*id="left-toolbar"/.test(html),
    'left toolbar should use compact tool-rail mode'
);

assert(
    /<nav class="tool-rail"[^>]*aria-label="Canvas tools"/.test(html),
    'left toolbar should expose a canvas tool rail'
);

['select', 'link', 'device', 'shape', 'text', 'laser', 'settings'].forEach(tool => {
    assert(
        new RegExp(`data-tool="${tool}"`).test(html),
        `tool rail should expose ${tool} button`
    );
});

assert(
    /Compact Openable Left Toolbar v4/.test(css),
    'compact openable toolbar cascade should be present'
);

assert(
    /\.tool-side-panel \.nested-subsection-content[\s\S]*display:\s*none !important/.test(css)
        && /\.tool-side-panel \.nested-subsection\.expanded \.nested-subsection-content[\s\S]*display:\s*block !important/.test(css),
    'tool flyouts should keep nested option cards collapsed until opened'
);

assert(
    /\.tool-side-panel \.toolbar-section-chevron,\s*\.tool-side-panel \.nested-chevron[\s\S]*display:\s*inline-flex !important/.test(css),
    'tool flyouts should expose openable nested panel chevrons'
);

assert(
    /aria-expanded/.test(fs.readFileSync(path.join(root, 'topology-toolbar.js'), 'utf8')),
    'tool rail buttons should expose open panel state'
);

console.log('[OK] toolbar compact openable contract smoke passed');
