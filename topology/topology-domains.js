/**
 * topology-domains.js -- Domain management for multi-user Topology Creator.
 *
 * Provides: domain selector, sharing dialog, topology save/load through domains API.
 * Depends on: window.TopologyAuth (authFetch, getCurrentUser)
 */
(function () {
    'use strict';

    var DOMAINS_API = '/api/domains';
    // Synthetic, server-injected, undeletable per-user inbox. Mirrored from
    // SHARED_WITH_ME_DOMAIN_ID in topology/api/auth/user_store.py.
    var SHARED_WITH_ME_DOMAIN_ID = '__shared_with_me';
    var _domains = [];
    var _activeDomain = null;

    function _authFetch(url, opts) {
        if (window.TopologyAuth && window.TopologyAuth.authFetch) {
            return window.TopologyAuth.authFetch(url, opts);
        }
        return fetch(url, opts);
    }

    function _currentUser() {
        return (window.TopologyAuth && window.TopologyAuth.getCurrentUser()) || null;
    }

    // ----------------------------------------------------------------
    // Domain CRUD
    // ----------------------------------------------------------------
    async function fetchDomains() {
        try {
            var resp = await _authFetch(DOMAINS_API);
            if (!resp.ok) return _domains;
            _domains = await resp.json();
            // Keep the current active domain pointer in sync with the
            // refreshed list (object identity is reset by the fetch).
            if (_activeDomain) {
                _activeDomain = _domains.find(function (d) {
                    return d.id === _activeDomain.id;
                }) || _activeDomain;
            }
            // Broadcast so downstream consumers (share toolbar, topology
            // dropdown's shared-in virtual rows, ...) can re-render
            // without having to re-poll the API themselves.
            _emitChange();
            return _domains;
        } catch {
            return _domains;
        }
    }

    async function createDomain(name, description) {
        var resp = await _authFetch(DOMAINS_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, description: description || '' })
        });
        if (!resp.ok) throw new Error('Failed to create domain');
        var domain = await resp.json();
        _domains.push(domain);
        return domain;
    }

    async function deleteDomain(domainId) {
        var resp = await _authFetch(DOMAINS_API + '/' + domainId, { method: 'DELETE' });
        if (!resp.ok) {
            var err = await resp.json().catch(function () { return {}; });
            throw new Error(err.detail || 'Failed to delete domain');
        }
        _domains = _domains.filter(function (d) { return d.id !== domainId; });
        if (_activeDomain && _activeDomain.id === domainId) {
            _activeDomain = _domains[0] || null;
        }
    }

    // ----------------------------------------------------------------
    // Sharing
    // ----------------------------------------------------------------
    async function shareDomain(domainId, targetUsers, permission) {
        var resp = await _authFetch(DOMAINS_API + '/' + domainId + '/share', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_users: targetUsers, permission: permission || 'read' })
        });
        if (!resp.ok) {
            var err = await resp.json();
            throw new Error(err.detail || 'Share failed');
        }
        return await resp.json();
    }

    async function unshareDomain(domainId, targetUser) {
        var resp = await _authFetch(DOMAINS_API + '/' + domainId + '/unshare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_user: targetUser })
        });
        if (!resp.ok) throw new Error('Unshare failed');
    }

    // ----------------------------------------------------------------
    // Per-file (per-topology) sharing
    // ----------------------------------------------------------------
    async function shareTopology(domainId, topologyId, targetUsers, permission) {
        var resp = await _authFetch(
            DOMAINS_API + '/' + domainId + '/topologies/' + topologyId + '/share',
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    target_users: targetUsers,
                    permission: permission || 'read'
                })
            }
        );
        if (!resp.ok) {
            var err = await resp.json().catch(function () { return {}; });
            throw new Error(err.detail || 'Share failed');
        }
        return await resp.json();
    }

    async function unshareTopology(domainId, topologyId, targetUser) {
        var resp = await _authFetch(
            DOMAINS_API + '/' + domainId + '/topologies/' + topologyId + '/unshare',
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_user: targetUser })
            }
        );
        if (!resp.ok) {
            var err = await resp.json().catch(function () { return {}; });
            throw new Error(err.detail || 'Unshare failed');
        }
    }

    async function listTopologyShares(domainId, topologyId) {
        var resp = await _authFetch(
            DOMAINS_API + '/' + domainId + '/topologies/' + topologyId + '/shares'
        );
        if (!resp.ok) return [];
        return await resp.json();
    }

    async function fetchOutgoingFileShares() {
        var resp = await _authFetch(DOMAINS_API + '/share/files/outgoing');
        return resp.ok ? await resp.json() : [];
    }

    async function fetchIncomingFileShares() {
        var resp = await _authFetch(DOMAINS_API + '/share/files/incoming');
        return resp.ok ? await resp.json() : [];
    }

    function isSharedWithMeDomainId(domainId) {
        return domainId === SHARED_WITH_ME_DOMAIN_ID;
    }

    function getSharedWithMeDomain() {
        return _domains.find(function (d) {
            return d.id === SHARED_WITH_ME_DOMAIN_ID || d.is_shared_with_me_domain;
        }) || null;
    }

    // ----------------------------------------------------------------
    // Topologies within domain
    // ----------------------------------------------------------------
    async function listTopologies(domainId) {
        var id = domainId || (_activeDomain && _activeDomain.id) || 'default';
        var resp = await _authFetch(DOMAINS_API + '/' + id + '/topologies');
        if (!resp.ok) return [];
        return await resp.json();
    }

    async function saveTopology(name, data, domainId, topologyId) {
        var id = domainId || (_activeDomain && _activeDomain.id) || 'default';
        var url = DOMAINS_API + '/' + id + '/topologies';
        var method = 'POST';
        if (topologyId) {
            url += '/' + topologyId;
            method = 'PUT';
        }
        var resp = await _authFetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, data: data })
        });
        if (!resp.ok) throw new Error('Save failed');
        return await resp.json();
    }

    async function loadTopology(domainId, topologyId) {
        var id = domainId || (_activeDomain && _activeDomain.id) || 'default';
        var resp = await _authFetch(DOMAINS_API + '/' + id + '/topologies/' + topologyId);
        if (!resp.ok) throw new Error('Load failed');
        return await resp.json();
    }

    async function deleteTopology(domainId, topologyId) {
        var id = domainId || (_activeDomain && _activeDomain.id) || 'default';
        var resp = await _authFetch(DOMAINS_API + '/' + id + '/topologies/' + topologyId, {
            method: 'DELETE'
        });
        if (!resp.ok) throw new Error('Delete failed');
    }

    // ----------------------------------------------------------------
    // Active domain selection (no UI -- the top-bar UI now lives in
    // topology-share.js, this module only manages state + APIs)
    // ----------------------------------------------------------------
    function selectDomain(domainId) {
        _activeDomain = _domains.find(function (d) { return d.id === domainId; }) || _domains[0];
        try { localStorage.setItem('topology_active_domain', domainId); } catch {}
        _emitChange();
    }

    function _emitChange() {
        try {
            document.dispatchEvent(new CustomEvent('topology-domains:changed', {
                detail: { domains: _domains, active: _activeDomain }
            }));
        } catch {}
    }

    function _hideLegacyDomainPill() {
        var legacy = document.getElementById('auth-domain-selector');
        if (legacy) {
            legacy.style.display = 'none';
            legacy.setAttribute('hidden', '');
        }
    }

    // ----------------------------------------------------------------
    // Live-refresh on WS share/unshare events.
    //
    // Previously the dropdown + Shared-with-me list only updated after
    // an explicit ``fetchDomains()`` call (a few file-ops paths did it;
    // the WS channel did not). Meaning: when someone shared a new
    // domain or a new file with you, your UI was stuck on stale state
    // until you manually reloaded or opened the share dialog. Fixed
    // 2026-04-24d alongside the router now emitting ``domain.shared``
    // / ``domain.unshared`` WS frames.
    // ----------------------------------------------------------------
    var _wsRefreshTimer = null;
    function _scheduleWsRefresh() {
        if (_wsRefreshTimer) return;
        _wsRefreshTimer = setTimeout(function () {
            _wsRefreshTimer = null;
            fetchDomains().catch(function () {});
        }, 150);
    }

    function _onTopologyEventWs(ev) {
        var env = (ev && ev.detail) || {};
        var t = (env && env.event_type) || '';
        if (t === 'topology.shared' ||
            t === 'topology.unshared' ||
            t === 'topology.permission_changed' ||
            t === 'domain.shared' ||
            t === 'domain.unshared' ||
            t === 'topology.deleted' ||
            t === 'topology.renamed') {
            _scheduleWsRefresh();
        }
    }
    try { window.addEventListener('topology:event:topology_event', _onTopologyEventWs); } catch (_) {}
    // Legacy alias used by some older file-ops paths.
    try { window.addEventListener('topology:event:share_domain', _onTopologyEventWs); } catch (_) {}

    // ----------------------------------------------------------------
    // Init
    // ----------------------------------------------------------------
    async function init() {
        _hideLegacyDomainPill();
        await fetchDomains();
        var savedId = null;
        try { savedId = localStorage.getItem('topology_active_domain'); } catch {}
        if (savedId) {
            _activeDomain = _domains.find(function (d) { return d.id === savedId; });
        }
        if (!_activeDomain && _domains.length > 0) {
            _activeDomain = _domains.find(function (d) { return d.id === 'default'; }) || _domains[0];
        }
        _emitChange();
        if (window.TopologyShare && typeof window.TopologyShare.init === 'function') {
            window.TopologyShare.init();
        }
    }

    // ----------------------------------------------------------------
    // Public API
    // ----------------------------------------------------------------
    window.TopologyDomains = {
        init: init,
        fetchDomains: fetchDomains,
        createDomain: createDomain,
        deleteDomain: deleteDomain,
        shareDomain: shareDomain,
        unshareDomain: unshareDomain,
        shareTopology: shareTopology,
        unshareTopology: unshareTopology,
        listTopologyShares: listTopologyShares,
        fetchOutgoingFileShares: fetchOutgoingFileShares,
        fetchIncomingFileShares: fetchIncomingFileShares,
        isSharedWithMeDomainId: isSharedWithMeDomainId,
        getSharedWithMeDomain: getSharedWithMeDomain,
        SHARED_WITH_ME_DOMAIN_ID: SHARED_WITH_ME_DOMAIN_ID,
        selectDomain: selectDomain,
        getCurrentDomain: function () { return _activeDomain; },
        getDomains: function () { return _domains; },
        listTopologies: listTopologies,
        saveTopology: saveTopology,
        loadTopology: loadTopology,
        deleteTopology: deleteTopology
    };
})();
