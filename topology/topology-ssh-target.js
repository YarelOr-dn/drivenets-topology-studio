/**
 * topology-ssh-target.js - Shared SSH target selection helpers.
 *
 * Keeps LLDP, DNAAS, Stack, Git Commit, and terminal launchers aligned so a
 * canvas display label never overrides a verified transport address.
 */

'use strict';

window.TopologySshTarget = {
    clean(value) {
        return String(value || '').trim();
    },

    isIp(value) {
        return /^\d+\.\d+\.\d+\.\d+$/.test(this.clean(value));
    },

    looksLikeSerial(value) {
        const v = this.clean(value);
        return !!v && !this.isIp(v) && /^[A-Z0-9]{8,}(?:-[A-Z0-9]+)?$/.test(v);
    },

    looksLikeNccTarget(value) {
        return /(^|[-_.])ncc\d+(\.|$)/i.test(this.clean(value));
    },

    _deviceAddressHost(device) {
        const addr = this.clean(device?.deviceAddress);
        return addr.includes('@') ? addr.split('@').pop() : addr;
    },

    _deviceAddressUser(device) {
        const addr = this.clean(device?.deviceAddress);
        return addr.includes('@') ? addr.split('@')[0] : '';
    },

    _displayNames(device, serial, cfg) {
        return new Set([
            device?.label,
            device?.name,
            device?.hostname,
            cfg?.nmHostname,
            serial,
        ].map(v => this.clean(v).toLowerCase()).filter(Boolean));
    },

    pick(device, options = {}) {
        const cfg = options.sshConfig || device?.sshConfig || {};
        const serial = this.clean(options.serial || device?.deviceSerial || device?.serial || '');
        const displayNames = this._displayNames(device, serial, cfg);
        const snHost = this.clean(cfg._snVerifiedHost);
        const userSavedHost = this.clean(cfg._userSavedHost);
        const isCluster = !!(cfg._isCluster || cfg._virshInfo || device?._isCluster || device?._monitorContext?.is_cluster);
        const activeNccHost = [
            cfg._activeNccHost,
            cfg._virshInfo?.activeNcc,
            device?._monitorContext?.active_ncc_host,
            device?._monitorContext?.active_ncc_vm,
            device?._identity?.active_ncc_host,
            device?._identity?.active_ncc_vm,
        ].map(v => this.clean(v)).find(v => v && !this.isIp(v) && this.looksLikeNccTarget(v));
        const lockedSnHost = [userSavedHost, snHost]
            .find(v => this.looksLikeSerial(v));
        const isDisplayName = (value) => {
            const v = this.clean(value).toLowerCase();
            return v && !this.isIp(v) && displayNames.has(v);
        };
        const addrHost = this._deviceAddressHost(device);

        if (isCluster && activeNccHost) {
            return {
                host: activeNccHost,
                addrUser: this._deviceAddressUser(device),
                source: 'active-ncc-host',
            };
        }

        if (lockedSnHost && (isCluster || snHost || userSavedHost)) {
            return {
                host: lockedSnHost,
                addrUser: this._deviceAddressUser(device),
                source: 'serial-locked',
            };
        }

        const preferredIp = [
            device?._registeredMgmtIp,
            device?._monitorContext?.management_ip,
            device?._monitorContext?.resolved_ip,
            cfg._registeredMgmtIp,
            cfg._enrichedMgmtIp,
            cfg._mgmtIp,
            isCluster ? '' : cfg._activeNccIp,
            isCluster ? '' : cfg._nccMgmtIp,
            cfg.hostBackup,
            cfg.host,
            addrHost,
        ].map(v => this.clean(v)).find(v => this.isIp(v));

        const host = preferredIp || [
            cfg._snVerifiedHost,
            cfg._activeNccHost,
            device?._registeredHostname,
            device?._registeredDeviceId,
            cfg._userSavedHost,
            cfg.host,
            cfg.hostBackup,
            addrHost,
            serial,
        ].map(v => this.clean(v)).find(v => v && !isDisplayName(v)) || serial;

        return {
            host,
            addrUser: this._deviceAddressUser(device),
            source: preferredIp ? 'verified-ip' : (host && !isDisplayName(host) ? 'verified-host' : 'serial'),
        };
    },
};
