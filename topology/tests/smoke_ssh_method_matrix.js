#!/usr/bin/env node
/**
 * Decision-matrix smoke test for `_pickLaunchMethod` / `_shouldUseWebTerminal`.
 *
 * Rebuilds the helpers in isolation (no DOM) by extracting the four relevant
 * methods from `topology-object-detection.js` and mounting them on a plain
 * object inside a VM context with mock `window` + `navigator` + `localStorage`.
 * Asserts every platform x pref x sticky combination yields the documented
 * decision. Run manually via:
 *   node /tmp/smoke_ssh_method_matrix.js
 */
'use strict';

const fs = require('fs');
const vm = require('vm');

const ROOT = '/home/dn/drivenets-topology-studio/topology/topology-object-detection.js';
const src = fs.readFileSync(ROOT, 'utf8');

function extractMethodBody(name) {
    // Match object-method-shorthand: "    name(args) {"
    const re = new RegExp(`\\n    ${name}\\((.*?)\\) \\{`);
    const match = src.match(re);
    if (!match) throw new Error(`cannot find ${name}() in ${ROOT}`);
    const argList = match[1];
    const startIdx = match.index + match[0].length - 1; // index of opening `{`
    let depth = 0;
    let i = startIdx;
    for (; i < src.length; i++) {
        const ch = src[i];
        if (ch === '{') depth++;
        else if (ch === '}') {
            depth--;
            if (depth === 0) { i++; break; }
        }
    }
    const body = src.slice(startIdx + 1, i - 1); // skip the outer { ... }
    return { argList, body };
}

function buildSnippet() {
    const methods = ['_getSshLaunchPref', '_isMacUA', '_pickLaunchMethod', '_shouldUseWebTerminal'];
    const assignments = methods.map((name) => {
        const { argList, body } = extractMethodBody(name);
        return `obj.${name} = function(${argList}) {${body}};`;
    });
    return `(() => {\n    const obj = {};\n    ${assignments.join('\n    ')}\n    return obj;\n})()`;
}

const snippet = buildSnippet();

function makeContext({ userAgent, platform = '', pref = null, hasTerminalPanel = true } = {}) {
    const storage = {};
    if (pref) storage['xdn_ssh_launch_pref'] = pref;
    const sandbox = {
        console,
        navigator: { userAgent, platform },
        localStorage: {
            getItem: (k) => (k in storage ? storage[k] : null),
            setItem: (k, v) => { storage[k] = String(v); },
            removeItem: (k) => { delete storage[k]; },
        },
        window: hasTerminalPanel ? { TerminalPanel: { open: () => {} } } : {},
    };
    vm.createContext(sandbox);
    return { sandbox };
}

function loadInstance(opts) {
    const { sandbox } = makeContext(opts);
    const script = new vm.Script(snippet);
    return script.runInContext(sandbox);
}

const pass = [];
const fail = [];
function expect(label, got, want) {
    const ok = got === want;
    (ok ? pass : fail).push(label);
    console.log(`${ok ? '[OK]  ' : '[FAIL]'} ${label}  got=${got} want=${want}`);
}

const macUA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36';
const iosUA = 'Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X)';
const linuxUA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36';
const winUA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)';

// 1. Auto mode: Mac -> iTerm, Linux/Win -> web
let obj = loadInstance({ userAgent: macUA, platform: 'MacIntel' });
expect('auto + mac UA + lab IP', obj._shouldUseWebTerminal('100.64.4.205', null), false);
expect('auto + mac UA + private IP', obj._shouldUseWebTerminal('10.0.0.1', null), false);

obj = loadInstance({ userAgent: linuxUA, platform: 'Linux x86_64' });
expect('auto + linux UA + lab IP', obj._shouldUseWebTerminal('100.64.4.205', null), true);
expect('auto + linux UA + public IP', obj._shouldUseWebTerminal('8.8.8.8', null), true);

obj = loadInstance({ userAgent: winUA, platform: 'Win32' });
expect('auto + windows UA', obj._shouldUseWebTerminal('100.64.4.205', null), true);

obj = loadInstance({ userAgent: iosUA, platform: 'iPad' });
expect('auto + ios UA', obj._shouldUseWebTerminal('100.64.4.205', null), false);

// 2. Global pref overrides everything
obj = loadInstance({ userAgent: linuxUA, pref: 'iterm' });
expect('global pref=iterm + linux', obj._shouldUseWebTerminal('100.64.4.205', null), false);

obj = loadInstance({ userAgent: macUA, pref: 'webterm' });
expect('global pref=webterm + mac', obj._shouldUseWebTerminal('100.64.4.205', null), true);

// 3. Per-device sticky wins over auto (but not over global explicit pref)
obj = loadInstance({ userAgent: linuxUA });
expect('auto + linux + device=iterm sticky',
    obj._shouldUseWebTerminal('100.64.4.205', { sshConfig: { preferredMethod: 'iterm' } }),
    false);

obj = loadInstance({ userAgent: macUA });
expect('auto + mac + device=webterm sticky',
    obj._shouldUseWebTerminal('100.64.4.205', { sshConfig: { preferredMethod: 'webterm' } }),
    true);

// 4. Global pref beats per-device sticky
obj = loadInstance({ userAgent: linuxUA, pref: 'iterm' });
expect('global=iterm overrides device=webterm',
    obj._shouldUseWebTerminal('100.64.4.205', { sshConfig: { preferredMethod: 'webterm' } }),
    false);

// 5. No TerminalPanel -> never pick web
obj = loadInstance({ userAgent: linuxUA, hasTerminalPanel: false });
expect('auto + linux + no TerminalPanel -> iTerm',
    obj._shouldUseWebTerminal('100.64.4.205', null), false);

// 6. Sticky "auto" behaves like no sticky
obj = loadInstance({ userAgent: macUA });
expect('device.preferredMethod=auto -> platform default (mac -> iterm)',
    obj._shouldUseWebTerminal('100.64.4.205', { sshConfig: { preferredMethod: 'auto' } }),
    false);

// 7. Empty sshConfig / null device
obj = loadInstance({ userAgent: macUA });
expect('mac + empty sshConfig', obj._shouldUseWebTerminal('100.64.4.205', { sshConfig: {} }), false);
expect('mac + null device', obj._shouldUseWebTerminal('100.64.4.205', null), false);
expect('mac + undefined device', obj._shouldUseWebTerminal('100.64.4.205'), false);

console.log();
console.log(`Results: PASS=${pass.length}  FAIL=${fail.length}`);
if (fail.length) {
    for (const f of fail) console.log(`  - ${f}`);
    process.exit(1);
}
console.log('All decision paths correct.');
