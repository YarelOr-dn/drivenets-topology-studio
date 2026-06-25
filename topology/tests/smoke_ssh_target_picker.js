#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const repoRoot = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(repoRoot, 'topology-ssh-target.js'), 'utf8');

const sandbox = { window: {} };
vm.createContext(sandbox);
vm.runInContext(source, sandbox, { filename: 'topology-ssh-target.js' });

const picker = sandbox.window.TopologySshTarget;

function assert(condition, message) {
    if (!condition) {
        console.error(`FAIL: ${message}`);
        process.exit(1);
    }
    console.log(`ok: ${message}`);
}

function pick(device, options) {
    return picker.pick(device, options || {});
}

console.log('=== SSH Target Picker Regression Matrix ===');

function assertClusterUsesActiveNcc(name, device, expectedHost, forbiddenTargets) {
    const result = pick(device);
    assert(result.host === expectedHost,
        `${name}: cluster uses active NCC host ${expectedHost}, got ${result.host}`);
    assert(result.source === 'active-ncc-host',
        `${name}: cluster source marks active NCC host, got ${result.source}`);
    forbiddenTargets.forEach((target) => {
        assert(result.host !== target, `${name}: cluster does not use forbidden target ${target}`);
    });
}

[
    {
        name: 'PE-4 activeNccHost',
        expected: 'kvm108-cl408d-ncc1',
        forbidden: ['WDY19C7M00013-P3', '100.64.11.96', '100.64.4.122'],
        device: {
            label: 'YOR_CL_PE-4',
            deviceSerial: 'WDY19C7M00013-P3',
            sshConfig: {
                _isCluster: true,
                _userSavedHost: 'WDY19C7M00013-P3',
                _snVerifiedHost: 'WDY19C7M00013-P3',
                _activeNccHost: 'kvm108-cl408d-ncc1',
                _activeNccIp: '100.64.11.96',
                _nccMgmtIp: '100.64.4.122',
                hostBackup: '100.64.11.96',
                host: 'WDY19C7M00013-P3',
            },
        },
    },
    {
        name: 'generic cluster virshInfo.activeNcc',
        expected: 'kvm200-cl999-ncc0',
        forbidden: ['GENERICCLUSTER01-P3', '100.64.55.10', '100.64.55.11'],
        device: {
            label: 'USER_A_CLUSTER',
            deviceSerial: 'GENERICCLUSTER01-P3',
            sshConfig: {
                _isCluster: true,
                _virshInfo: {
                    activeNcc: 'kvm200-cl999-ncc0',
                    nccVms: ['kvm200-cl999-ncc0', 'kvm200-cl999-ncc1'],
                },
                _activeNccIp: '100.64.55.10',
                _nccMgmtIp: '100.64.55.11',
                hostBackup: '100.64.55.10',
            },
        },
    },
    {
        name: 'monitor-derived active_ncc_vm',
        expected: 'kvm300-cl777-ncc1',
        forbidden: ['MONITORCLUSTER02-P3', '100.64.77.20'],
        device: {
            label: 'TENANT_B_CLUSTER',
            deviceSerial: 'MONITORCLUSTER02-P3',
            _monitorContext: {
                is_cluster: true,
                active_ncc_vm: 'kvm300-cl777-ncc1',
            },
            sshConfig: {
                host: 'MONITORCLUSTER02-P3',
                hostBackup: '100.64.77.20',
            },
        },
    },
    {
        name: 'identity-derived active_ncc_vm',
        expected: 'kvm400-cl123-ncc0',
        forbidden: ['IDENTITYCLUSTER03-P3', '100.64.88.30'],
        device: {
            label: 'ANY_USER_CLUSTER',
            deviceSerial: 'IDENTITYCLUSTER03-P3',
            _isCluster: true,
            _identity: {
                active_ncc_vm: 'kvm400-cl123-ncc0',
            },
            sshConfig: {
                _userSavedHost: 'IDENTITYCLUSTER03-P3',
                _activeNccIp: '100.64.88.30',
            },
        },
    },
].forEach((entry) => assertClusterUsesActiveNcc(
    entry.name, entry.device, entry.expected, entry.forbidden,
));

const singleNcp = {
    label: 'PE-1',
    deviceSerial: 'WK31D7VV00023',
    sshConfig: {
        hostBackup: '100.64.4.200',
        host: 'WK31D7VV00023',
    },
};

let result = pick(singleNcp);
assert(result.host === '100.64.4.200',
    `single-NCP devices still prefer verified IP, got ${result.host}`);

console.log('\nAll SSH target picker regression checks passed');
