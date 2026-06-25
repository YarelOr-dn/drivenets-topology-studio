/**
 * topology-share.js -- "Share Topology" top-bar button + simplified dialog.
 *
 * Single-view layout (no tabs, no wizard steps):
 *   - My Domains: list with per-row inline expansion to recipients + share form
 *   - Shared with Me: list with owner attribution; entire row opens the domain
 *   - Recent Activity: collapsible <details> at bottom
 *
 * Accordion behavior: only one domain expanded at a time so the eye stays
 * focused on the row currently being managed.
 *
 * Targeted DOM updates for in-form interactions: search-typing and
 * click-to-select feel smooth (no flicker, no focus loss). Full re-render
 * only happens on data changes (share, revoke, perm-change, create-domain)
 * or accordion toggle.
 *
 * Backend (unchanged):
 *   GET    /api/domains
 *   GET    /api/domains/share/overview
 *   GET    /api/domains/share/targets
 *   GET    /api/domains/share/outgoing
 *   GET    /api/domains/share/incoming
 *   GET    /api/domains/share/activity
 *   POST   /api/domains/{id}/share
 *   POST   /api/domains/{id}/unshare
 *   POST   /api/domains
 *
 * Depends on: window.TopologyAuth (authFetch, getCurrentUser),
 *             window.TopologyDomains (state + selectDomain + share/unshare/createDomain).
 */
(function () {
    'use strict';

    var DOMAINS_API = '/api/domains';
    var SHARED_WITH_ME_DOMAIN_ID = '__shared_with_me';
    var _users = [];
    var _outgoing = [];
    var _incoming = [];
    var _outgoingFiles = []; // per-file shares I sent
    var _incomingFiles = []; // per-file shares I received (mirrors the synthetic domain)
    var _activity = [];
    var _overview = null;
    var _expandedDomains = {};   // accordion: {domainId: true}
    var _expandedTopologies = {}; // {domainId: {topologyId: true}} for per-file share rows
    var _shareDrafts = {};       // per-domain draft: {domainId: {scope, targets, perm, search, fileTargets}}
    var _topologyDrafts = {};    // per-file draft: {composite: {targets, perm, search, focused, activeIdx}}
    var _domainTopologyCache = {}; // {domainId: [topologyMeta...]}
    var _loading = false;
    var _firstOpen = true;
    var _pendingContext = null;  // {domainHint, topologyName} from openForDomain()
    // Marks the inline share form as "dirty" when a successful share /
    // unshare / perm-change mutation happened during its lifetime. The
    // global `topology-domains:changed` listener in topology-file-ops.js
    // skips the dropdown rebuild while a share form is mounted (otherwise
    // the popover gets torn out of the DOM mid-typing). _closeInline()
    // re-emits the event after the form is gone so the previously-
    // skipped rebuild runs and every row picks up its new badge +
    // action-button set WITHOUT needing a page refresh.
    var _inlineDirty = false;
    var _activeAnchor = null;    // element the popover is anchored to (for positioning)
    var _resizeBound = false;    // ensure window resize listener is attached only once

    function _authFetch(url, opts) {
        if (window.TopologyAuth && window.TopologyAuth.authFetch) {
            return window.TopologyAuth.authFetch(url, opts);
        }
        return fetch(url, opts);
    }

    function _currentUser() {
        return (window.TopologyAuth && window.TopologyAuth.getCurrentUser()) || null;
    }

    function _domains() {
        return (window.TopologyDomains && window.TopologyDomains.getDomains()) || [];
    }

    function _activeDomain() {
        return window.TopologyDomains && window.TopologyDomains.getCurrentDomain();
    }

    function _esc(s) {
        if (s === null || s === undefined) return '';
        return String(s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    // Thin wrapper around the editor's showToast so share actions give
    // visible feedback ("Shared with bob", "Access revoked", ...) --
    // previously the dialog just re-rendered silently after success
    // which felt broken to users who expected a confirmation ping.
    function _toast(msg, type) {
        try {
            var editor = window.topologyEditor || window.editor;
            if (editor && typeof editor.showToast === 'function') {
                editor.showToast(msg, type || 'info');
                return;
            }
        } catch (_) { /* swallow */ }
    }

    // ----------------------------------------------------------------
    // Permission label helpers -- frontend rename of wire tokens
    // ----------------------------------------------------------------
    // The wire tokens stay 'read' and 'write' (validated by Pydantic
    // regex on the backend and stored as-is in the central
    // domain_shares / topology_shares SQLite columns). Only the
    // user-facing label changes.
    //
    // See DEVELOPMENT_GUIDELINES.md -> "Shared Topology Permissions --
    // View / Edit -- 2026-05-12" for the full rationale + invariants.
    //
    // Helpers:
    //   permissionLabel('read')  -> 'View'
    //   permissionLabel('write') -> 'Edit'
    //   permissionLabel('') / null / unknown -> ''
    //   permissionTitle(perm)    -> hover-tooltip helper text
    //   permissionVerb(perm)     -> sentence-friendly form ('view' / 'edit')
    function permissionLabel(perm) {
        if (perm === 'read') return 'View';
        if (perm === 'write') return 'Edit';
        return '';
    }
    function permissionTitle(perm) {
        if (perm === 'read') return 'View only: can open and inspect';
        if (perm === 'write') return 'Edit: can open, modify, and save';
        return '';
    }
    function permissionVerb(perm) {
        if (perm === 'read') return 'view';
        if (perm === 'write') return 'edit';
        return '';
    }

    // ----------------------------------------------------------------
    // Shared popover positioning
    // ----------------------------------------------------------------
    // Docks a .share-dialog-shaped popover beside the topologies dropdown
    // when that dropdown is open, so the two panels visually merge into
    // one continuous surface (no overlap, no floating cloud). Falls back
    // to a clamped anchor-below layout when the dropdown isn't showing.
    //
    // Exposed via window.TopologyPopover.position so sibling popovers (the
    // Create Bug Topology dialog, any future dropdown-triggered surfaces)
    // dock identically without re-implementing the math. The `inner`
    // element is expected to carry the `.share-dialog` visual class, which
    // brings along the attached-left / attached-right / shareDialogIn*
    // animations defined in styles.css.
    function _positionPopover(inner, anchorEl) {
        if (!inner) return;

        var pw = inner.offsetWidth || 420;
        var ph = inner.offsetHeight || 460;
        var vw = window.innerWidth;
        var vh = window.innerHeight;
        var margin = 8;

        inner.classList.remove('attached-right', 'attached-left', 'attached-top');

        var dropdown = document.getElementById('topologies-dropdown-menu');
        var dropdownVisible = dropdown &&
            dropdown.style.display !== 'none' &&
            dropdown.offsetParent !== null;

        var top, left;
        var attached = false;

        if (dropdownVisible) {
            var dropRect = dropdown.getBoundingClientRect();
            // Share the dropdown's top so both panels read as one band.
            top = Math.max(margin, dropRect.top);
            var gap = 0;
            if (dropRect.right + gap + pw + margin <= vw) {
                left = dropRect.right + gap;
                inner.style.transformOrigin = 'top left';
                inner.classList.add('attached-left');
                attached = true;
            } else if (dropRect.left - gap - pw - margin >= 0) {
                left = dropRect.left - gap - pw;
                inner.style.transformOrigin = 'top right';
                inner.classList.add('attached-right');
                attached = true;
            }
        }

        if (!attached) {
            if (anchorEl && anchorEl.getBoundingClientRect) {
                var aRect = anchorEl.getBoundingClientRect();
                top = aRect.bottom + 6;
                left = aRect.left;
                if (aRect.left + pw > vw - margin) {
                    left = Math.max(margin, aRect.right - pw);
                    inner.style.transformOrigin = 'top right';
                } else {
                    inner.style.transformOrigin = 'top left';
                }
            } else {
                top = 56;
                left = vw - pw - margin;
                inner.style.transformOrigin = 'top right';
            }
        }

        if (left + pw > vw - margin) left = vw - pw - margin;
        if (left < margin) left = margin;
        if (top + ph > vh - margin) top = Math.max(margin, vh - ph - margin);
        if (top < margin) top = margin;

        inner.style.top = top + 'px';
        inner.style.left = left + 'px';
        inner.style.right = 'auto';
    }

    // Published as a sibling-popover helper so topology-bugs.js (and any
    // future dropdown-attached surface) dock with identical math.
    window.TopologyPopover = window.TopologyPopover || {};
    window.TopologyPopover.position = _positionPopover;

    function _fmtTime(iso) {
        if (!iso) return '';
        try {
            var d = new Date(iso);
            if (isNaN(d.getTime())) return iso;
            return d.toLocaleString();
        } catch { return iso; }
    }

    function _ago(iso) {
        if (!iso) return '';
        try {
            var d = new Date(iso).getTime();
            if (isNaN(d)) return '';
            var diff = Math.max(0, Date.now() - d);
            var s = Math.floor(diff / 1000);
            if (s < 60) return s + 's ago';
            var m = Math.floor(s / 60);
            if (m < 60) return m + 'm ago';
            var h = Math.floor(m / 60);
            if (h < 24) return h + 'h ago';
            var dd = Math.floor(h / 24);
            return dd + 'd ago';
        } catch { return ''; }
    }

    function _initial(name) {
        return _esc(String(name || '?').slice(0, 1).toUpperCase());
    }

    // ----------------------------------------------------------------
    // Cloud-face avatar generator (2026-04-22 "extra cute" refresh)
    // ----------------------------------------------------------------
    // Deterministically picks one of (14 face variants) x (14 cloud color
    // palettes) for a given username, so each user keeps the same little
    // cloud-creature across the whole dialog while still being visually
    // distinct from their teammates.
    //
    // Design goals for the refresh:
    //   - More pastel palettes (lavender / peach / mint / sky / rose /
    //     sage / butter / periwinkle plus the original 8) so running a
    //     medium-sized team shows real variety.
    //   - Softer, rounder silhouette (7-bump cloud vs the old 4) so the
    //     creature reads as "plushie" at 20px and "character" at 80px.
    //   - Richer face expressions (wink, uwu, giggle, starry-eyes,
    //     sleepy zzz, cool shades, kiss) on top of the original set,
    //     each with an eye-shine highlight and rosy cheek blushes.
    //   - Optional sparkle-ring layer (enabled by `opts.sparkle`) that
    //     CSS animates with a slow drift; `prefers-reduced-motion`
    //     users get the static form.
    //
    // Returns inline SVG markup (no external resources, no <img>, no
    // network calls) so it embeds cleanly inside chips, recipient rows,
    // typeahead suggestions, and the top-bar user pill.
    var CLOUD_PALETTES = [
        { body: '#e0f2fe', edge: '#7dd3fc', face: '#0c4a6e', cheek: '#f9a8d4', name: 'sky'        },
        { body: '#fce7f3', edge: '#f9a8d4', face: '#831843', cheek: '#fb7185', name: 'rose'       },
        { body: '#dcfce7', edge: '#86efac', face: '#14532d', cheek: '#fca5a5', name: 'mint'       },
        { body: '#fef9c3', edge: '#fde047', face: '#713f12', cheek: '#f9a8d4', name: 'butter'     },
        { body: '#ede9fe', edge: '#c4b5fd', face: '#4c1d95', cheek: '#f9a8d4', name: 'lavender'   },
        { body: '#ffedd5', edge: '#fdba74', face: '#7c2d12', cheek: '#fb7185', name: 'peach'      },
        { body: '#fee2e2', edge: '#fca5a5', face: '#7f1d1d', cheek: '#fda4af', name: 'blossom'    },
        { body: '#cffafe', edge: '#67e8f9', face: '#155e75', cheek: '#f9a8d4', name: 'aqua'       },
        { body: '#e0e7ff', edge: '#a5b4fc', face: '#312e81', cheek: '#f9a8d4', name: 'periwinkle' },
        { body: '#f0fdf4', edge: '#bbf7d0', face: '#166534', cheek: '#fda4af', name: 'sage'       },
        { body: '#fef3c7', edge: '#fcd34d', face: '#78350f', cheek: '#fda4af', name: 'honey'      },
        { body: '#fdf2f8', edge: '#fbcfe8', face: '#9d174d', cheek: '#fb7185', name: 'petal'      },
        { body: '#ecfeff', edge: '#a5f3fc', face: '#164e63', cheek: '#f9a8d4', name: 'mist'       },
        { body: '#fafaf9', edge: '#d6d3d1', face: '#44403c', cheek: '#fda4af', name: 'cloud'      }
    ];
    // Each face: [eyeShapeId, mouthShapeId, accessoryId].
    // eyeShapeId:
    //   0=normal, 1=happy, 2=closed, 3=star, 4=wink, 5=sparkle, 6=sleepy, 7=shades
    // mouthShapeId:
    //   0=smile, 1=tiny, 2=open-o, 3=line, 4=uwu, 5=giggle, 6=kiss, 7=smirk
    // accessoryId:
    //   0=none, 1=zzz (sleepy), 2=tiny-heart-above-head
    var CLOUD_FACES = [
        [0, 0, 0], [1, 0, 0], [2, 1, 0], [0, 2, 0],
        [3, 0, 2], [1, 1, 0], [2, 0, 0], [0, 3, 0],
        [4, 7, 0], [5, 4, 0], [1, 5, 0], [6, 1, 1],
        [7, 0, 0], [3, 6, 2]
    ];

    function _hashStr(s) {
        var h = 5381;
        s = String(s || '');
        for (var i = 0; i < s.length; i++) {
            h = ((h << 5) + h) + s.charCodeAt(i);
            h = h & h;
        }
        return Math.abs(h);
    }

    function _cloudFaceParts(faceId, palette, scale) {
        // Back-compat shim: original callers passed a faceId; the new
        // override-aware generator calls _cloudFacePartsFromSpec with a
        // pre-mutated spec. Both funnel through the shared renderer so
        // there's one place the SVG shapes live.
        var spec = CLOUD_FACES[faceId] || CLOUD_FACES[0];
        return _cloudFacePartsFromSpec(spec, palette, scale);
    }

    function _cloudFacePartsFromSpec(spec, palette, scale) {
        // Coordinate space: 64x64 viewBox. The cloud body sits at y=22..52.
        var face = palette.face;
        var cheek = palette.cheek || palette.edge;
        spec = spec || CLOUD_FACES[0];
        var eyeKind = spec[0];
        var mouthKind = spec[1];
        var accessory = spec[2] || 0;
        var lEyeX = 24, rEyeX = 40, eyeY = 34;

        // Eye-shine highlight: a tiny off-white dot on pupil-based eyes
        // (kinds 0, 3, 5). Skipped on line/arc eyes because there's no
        // filled circle to sit on top of.
        var shine = function (cx, cy) {
            return '<circle cx="' + (cx - 0.7) + '" cy="' + (cy - 0.8) + '" r="0.7" fill="#ffffff" opacity="0.9"/>';
        };

        var eyes = '';
        if (eyeKind === 0) {
            eyes =
                '<circle cx="' + lEyeX + '" cy="' + eyeY + '" r="2.4" fill="' + face + '"/>' +
                '<circle cx="' + rEyeX + '" cy="' + eyeY + '" r="2.4" fill="' + face + '"/>' +
                shine(lEyeX, eyeY) + shine(rEyeX, eyeY);
        } else if (eyeKind === 1) {
            // happy: upward arcs (^_^)
            eyes =
                '<path d="M' + (lEyeX - 3) + ' ' + (eyeY + 1) + ' Q' + lEyeX + ' ' + (eyeY - 3.5) + ' ' + (lEyeX + 3) + ' ' + (eyeY + 1) + '" stroke="' + face + '" stroke-width="2" fill="none" stroke-linecap="round"/>' +
                '<path d="M' + (rEyeX - 3) + ' ' + (eyeY + 1) + ' Q' + rEyeX + ' ' + (eyeY - 3.5) + ' ' + (rEyeX + 3) + ' ' + (eyeY + 1) + '" stroke="' + face + '" stroke-width="2" fill="none" stroke-linecap="round"/>';
        } else if (eyeKind === 2) {
            // closed: downward arcs (-_-)
            eyes =
                '<path d="M' + (lEyeX - 3) + ' ' + (eyeY - 1) + ' Q' + lEyeX + ' ' + (eyeY + 2.5) + ' ' + (lEyeX + 3) + ' ' + (eyeY - 1) + '" stroke="' + face + '" stroke-width="2" fill="none" stroke-linecap="round"/>' +
                '<path d="M' + (rEyeX - 3) + ' ' + (eyeY - 1) + ' Q' + rEyeX + ' ' + (eyeY + 2.5) + ' ' + (rEyeX + 3) + ' ' + (eyeY - 1) + '" stroke="' + face + '" stroke-width="2" fill="none" stroke-linecap="round"/>';
        } else if (eyeKind === 3) {
            // sparkly star eyes
            var star = function (cx, cy) {
                return '<path d="M' + cx + ' ' + (cy - 3) + ' L' + (cx + 0.9) + ' ' + (cy - 0.9) + ' L' + (cx + 3) + ' ' + cy + ' L' + (cx + 0.9) + ' ' + (cy + 0.9) + ' L' + cx + ' ' + (cy + 3) + ' L' + (cx - 0.9) + ' ' + (cy + 0.9) + ' L' + (cx - 3) + ' ' + cy + ' L' + (cx - 0.9) + ' ' + (cy - 0.9) + ' Z" fill="' + face + '"/>';
            };
            eyes = star(lEyeX, eyeY) + star(rEyeX, eyeY);
        } else if (eyeKind === 4) {
            // wink: left closed, right open with shine
            eyes =
                '<path d="M' + (lEyeX - 3) + ' ' + (eyeY - 1) + ' Q' + lEyeX + ' ' + (eyeY + 2.5) + ' ' + (lEyeX + 3) + ' ' + (eyeY - 1) + '" stroke="' + face + '" stroke-width="2" fill="none" stroke-linecap="round"/>' +
                '<circle cx="' + rEyeX + '" cy="' + eyeY + '" r="2.4" fill="' + face + '"/>' +
                shine(rEyeX, eyeY);
        } else if (eyeKind === 5) {
            // sparkle: pupils plus a tiny 4-point spark above the right eye
            eyes =
                '<circle cx="' + lEyeX + '" cy="' + eyeY + '" r="2.2" fill="' + face + '"/>' +
                '<circle cx="' + rEyeX + '" cy="' + eyeY + '" r="2.2" fill="' + face + '"/>' +
                shine(lEyeX, eyeY) + shine(rEyeX, eyeY) +
                '<path d="M' + (rEyeX + 4) + ' ' + (eyeY - 4) + ' L' + (rEyeX + 5.4) + ' ' + (eyeY - 2.8) + ' L' + (rEyeX + 7) + ' ' + (eyeY - 4) + ' L' + (rEyeX + 5.4) + ' ' + (eyeY - 5.2) + ' Z" fill="' + face + '" opacity="0.9"/>';
        } else if (eyeKind === 6) {
            // sleepy: half-lidded (> <)
            eyes =
                '<path d="M' + (lEyeX - 3) + ' ' + eyeY + ' Q' + lEyeX + ' ' + (eyeY - 1.5) + ' ' + (lEyeX + 3) + ' ' + eyeY + '" stroke="' + face + '" stroke-width="2.2" fill="none" stroke-linecap="round"/>' +
                '<path d="M' + (rEyeX - 3) + ' ' + eyeY + ' Q' + rEyeX + ' ' + (eyeY - 1.5) + ' ' + (rEyeX + 3) + ' ' + eyeY + '" stroke="' + face + '" stroke-width="2.2" fill="none" stroke-linecap="round"/>';
        } else {
            // shades: single wide sunglasses
            eyes =
                '<rect x="' + (lEyeX - 3.5) + '" y="' + (eyeY - 2.8) + '" width="7" height="4.2" rx="1.4" fill="' + face + '"/>' +
                '<rect x="' + (rEyeX - 3.5) + '" y="' + (eyeY - 2.8) + '" width="7" height="4.2" rx="1.4" fill="' + face + '"/>' +
                '<line x1="' + (lEyeX + 3.5) + '" y1="' + (eyeY - 1) + '" x2="' + (rEyeX - 3.5) + '" y2="' + (eyeY - 1) + '" stroke="' + face + '" stroke-width="1.4"/>' +
                '<circle cx="' + (lEyeX + 1) + '" cy="' + (eyeY - 1.5) + '" r="0.8" fill="#ffffff" opacity="0.75"/>' +
                '<circle cx="' + (rEyeX + 1) + '" cy="' + (eyeY - 1.5) + '" r="0.8" fill="#ffffff" opacity="0.75"/>';
        }

        var mouth = '';
        var mY = 42;
        if (mouthKind === 0) {
            // smile
            mouth = '<path d="M28 ' + mY + ' Q32 ' + (mY + 4) + ' 36 ' + mY + '" stroke="' + face + '" stroke-width="2" fill="none" stroke-linecap="round"/>';
        } else if (mouthKind === 1) {
            // tiny smile
            mouth = '<path d="M30 ' + (mY + 1) + ' Q32 ' + (mY + 3) + ' 34 ' + (mY + 1) + '" stroke="' + face + '" stroke-width="1.8" fill="none" stroke-linecap="round"/>';
        } else if (mouthKind === 2) {
            // little O mouth
            mouth = '<ellipse cx="32" cy="' + (mY + 2) + '" rx="2" ry="2.4" fill="' + face + '"/>';
        } else if (mouthKind === 3) {
            // neutral line
            mouth = '<line x1="29" y1="' + (mY + 2) + '" x2="35" y2="' + (mY + 2) + '" stroke="' + face + '" stroke-width="2" stroke-linecap="round"/>';
        } else if (mouthKind === 4) {
            // uwu: two tiny arcs
            mouth =
                '<path d="M28 ' + (mY + 1) + ' Q30 ' + (mY + 3.4) + ' 32 ' + (mY + 1) + '" stroke="' + face + '" stroke-width="1.8" fill="none" stroke-linecap="round"/>' +
                '<path d="M32 ' + (mY + 1) + ' Q34 ' + (mY + 3.4) + ' 36 ' + (mY + 1) + '" stroke="' + face + '" stroke-width="1.8" fill="none" stroke-linecap="round"/>';
        } else if (mouthKind === 5) {
            // giggle: wide open smile with a tooth hint
            mouth =
                '<path d="M27 ' + (mY + 0.5) + ' Q32 ' + (mY + 5.5) + ' 37 ' + (mY + 0.5) + ' Z" fill="' + face + '" opacity="0.85"/>' +
                '<rect x="30.6" y="' + (mY + 1) + '" width="2.8" height="1.3" fill="#ffffff" opacity="0.85" rx="0.3"/>';
        } else if (mouthKind === 6) {
            // kiss: heart-mouth
            mouth =
                '<path d="M32 ' + (mY + 4) + ' C 29 ' + (mY + 1.5) + ' 27 ' + (mY + 3) + ' 32 ' + (mY + 5.5) + ' C 37 ' + (mY + 3) + ' 35 ' + (mY + 1.5) + ' 32 ' + (mY + 4) + ' Z" fill="#fb7185" stroke="' + face + '" stroke-width="0.8"/>';
        } else {
            // smirk: slightly lopsided arc
            mouth = '<path d="M28 ' + (mY + 1) + ' Q32 ' + (mY + 3) + ' 36 ' + (mY - 0.5) + '" stroke="' + face + '" stroke-width="2" fill="none" stroke-linecap="round"/>';
        }

        // Rosy cheek blushes either side of the mouth. Slightly bigger
        // than before and with a soft radial feel thanks to a double
        // circle (the outer one is mostly transparent).
        var blush =
            '<circle cx="21" cy="' + (mY - 1) + '" r="2.6" fill="' + cheek + '" opacity="0.22"/>' +
            '<circle cx="21" cy="' + (mY - 1) + '" r="1.6" fill="' + cheek + '" opacity="0.65"/>' +
            '<circle cx="43" cy="' + (mY - 1) + '" r="2.6" fill="' + cheek + '" opacity="0.22"/>' +
            '<circle cx="43" cy="' + (mY - 1) + '" r="1.6" fill="' + cheek + '" opacity="0.65"/>';

        // Optional accessory rendered ABOVE the cloud body (y<22).
        // Originally only 3 slots (none / zzz / heart) hardcoded into
        // CLOUD_FACES. Customise-Cloud introduced 7 more so users have
        // something to actually pick from; the catalogue IDs are kept
        // stable so profile_prefs.json stays readable across redeploys.
        var accessoryMarkup = _cloudAccessoryMarkup(accessory, face, palette);

        return eyes + mouth + blush + accessoryMarkup;
    }

    // Accessory catalogue. ID -> { label, build(faceColour, palette) -> svg }.
    // Rendered above the cloud body at y<22 so it reads as "perched on
    // top" rather than inline with the face. Kept as a lookup so the
    // customise-cloud dialog can iterate for the picker and so adding
    // a new accessory is a single table entry.
    var CLOUD_ACCESSORIES = {
        0: {
            label: 'None',
            emoji: '\u2715',
            build: function () { return ''; }
        },
        1: {
            label: 'Sleepy',
            emoji: 'z\u200A',
            build: function (face) {
                return '<text x="48" y="20" font-size="7" font-weight="700" font-family="sans-serif" fill="' + face + '" opacity="0.9">z</text>' +
                       '<text x="53" y="14" font-size="5" font-weight="700" font-family="sans-serif" fill="' + face + '" opacity="0.65">z</text>';
            }
        },
        2: {
            label: 'Heart',
            emoji: '\u2665',
            build: function () {
                return '<path d="M50 14 C 48 11 45 13 48 16 C 51 13 52 11 50 14 Z" fill="#fb7185" stroke="#be123c" stroke-width="0.6" opacity="0.95"/>';
            }
        },
        3: {
            label: 'Star',
            emoji: '\u2605',
            build: function (face) {
                // Tiny 5-point gold star hanging top-right.
                var star = '<path d="M50 10 L51.4 13.2 L55 13.6 L52.3 16 L53 19.5 L50 17.8 L47 19.5 L47.7 16 L45 13.6 L48.6 13.2 Z" fill="#fcd34d" stroke="#b45309" stroke-width="0.5" opacity="0.95"/>';
                return star;
            }
        },
        4: {
            label: 'Crown',
            emoji: '\u265A',
            build: function () {
                // A jagged mini-crown above the cloud's head bump.
                return '<path d="M25 18 L28 12 L30 16 L32 11 L34 16 L36 12 L39 18 Z" fill="#fbbf24" stroke="#92400e" stroke-width="0.6" opacity="0.95"/>' +
                       '<circle cx="28" cy="13" r="0.9" fill="#fca5a5"/>' +
                       '<circle cx="36" cy="13" r="0.9" fill="#60a5fa"/>' +
                       '<circle cx="32" cy="12" r="1.0" fill="#f472b6"/>';
            }
        },
        5: {
            label: 'Bow',
            emoji: '\u2767',
            build: function () {
                // Pink ribbon bow perched on the top-left of the cloud.
                return '<path d="M18 14 C 14 10 11 14 14 17 C 11 18 13 21 16 20 Z" fill="#fb7185" stroke="#be123c" stroke-width="0.5" opacity="0.95"/>' +
                       '<path d="M20 17 C 24 13 27 17 24 20 C 27 21 25 24 22 23 Z" fill="#fb7185" stroke="#be123c" stroke-width="0.5" opacity="0.95"/>' +
                       '<circle cx="19.5" cy="17" r="1.4" fill="#fbcfe8" stroke="#be123c" stroke-width="0.4"/>';
            }
        },
        6: {
            label: 'Halo',
            emoji: '\u26AA',
            build: function () {
                // Floating yellow halo ring above the cloud.
                return '<ellipse cx="32" cy="12" rx="11" ry="2.4" fill="none" stroke="#fde047" stroke-width="1.6" opacity="0.9"/>' +
                       '<ellipse cx="32" cy="12" rx="11" ry="2.4" fill="none" stroke="#fffbeb" stroke-width="0.6" opacity="0.8"/>';
            }
        },
        7: {
            label: 'Sparkle',
            emoji: '\u2728',
            build: function (face, palette) {
                var col = (palette && palette.edge) || '#c4b5fd';
                // Four sparkle bursts arranged around the top.
                var spark = function (cx, cy, r) {
                    return '<path d="M' + cx + ' ' + (cy - r) + ' L' + (cx + r * 0.4) + ' ' + (cy - r * 0.4) + ' L' + (cx + r) + ' ' + cy + ' L' + (cx + r * 0.4) + ' ' + (cy + r * 0.4) + ' L' + cx + ' ' + (cy + r) + ' L' + (cx - r * 0.4) + ' ' + (cy + r * 0.4) + ' L' + (cx - r) + ' ' + cy + ' L' + (cx - r * 0.4) + ' ' + (cy - r * 0.4) + ' Z" fill="' + col + '" opacity="0.92"/>';
                };
                return spark(52, 14, 2.2) + spark(18, 12, 1.6) + spark(44, 8, 1.2) + spark(26, 6, 1.0);
            }
        },
        8: {
            label: 'Flower',
            emoji: '\u2740',
            build: function () {
                // Five-petal flower on top-right.
                var petal = function (cx, cy) { return '<circle cx="' + cx + '" cy="' + cy + '" r="2.2" fill="#fda4af" stroke="#be123c" stroke-width="0.4" opacity="0.95"/>'; };
                return petal(50, 10) + petal(54, 13) + petal(52, 17) + petal(48, 17) + petal(46, 13) +
                       '<circle cx="50" cy="13.4" r="1.3" fill="#fde047" stroke="#92400e" stroke-width="0.4"/>';
            }
        },
        9: {
            label: 'Leaf',
            emoji: '\u2618',
            build: function () {
                // Two mint-green leaves that look like a headband.
                return '<path d="M22 16 Q 16 10 14 18 Q 18 20 22 16 Z" fill="#86efac" stroke="#166534" stroke-width="0.5" opacity="0.95"/>' +
                       '<path d="M42 16 Q 48 10 50 18 Q 46 20 42 16 Z" fill="#86efac" stroke="#166534" stroke-width="0.5" opacity="0.95"/>' +
                       '<line x1="14" y1="18" x2="22" y2="16" stroke="#166534" stroke-width="0.4" opacity="0.7"/>' +
                       '<line x1="42" y1="16" x2="50" y2="18" stroke="#166534" stroke-width="0.4" opacity="0.7"/>';
            }
        }
    };

    function _cloudAccessoryMarkup(accessoryId, face, palette) {
        var spec = CLOUD_ACCESSORIES[accessoryId];
        if (!spec || typeof spec.build !== 'function') return '';
        try { return spec.build(face, palette) || ''; } catch (_) { return ''; }
    }

    // Per-seed override store, populated from profile_prefs.json via
    // CloudAvatar.setOverrides() once the /api/auth/me/profile request
    // resolves. Without an override the hashing logic below still
    // produces a deterministic, pleasant default -- so the first
    // paint before prefs arrive is still a good-looking avatar.
    var _AVATAR_OVERRIDES = {};

    function _resolveAvatarParts(seed, opts) {
        var overrides = _AVATAR_OVERRIDES[seed] || {};
        var hash = _hashStr(seed);
        var palette = CLOUD_PALETTES[hash % CLOUD_PALETTES.length];
        // Palette override: explicit per-call opt wins over the stored
        // user preference, which wins over the hashed default. The same
        // precedence applies to face and accessory below.
        var paletteName = (opts && opts.palette) || overrides.palette;
        if (paletteName) {
            for (var pi = 0; pi < CLOUD_PALETTES.length; pi++) {
                if (CLOUD_PALETTES[pi].name === paletteName) { palette = CLOUD_PALETTES[pi]; break; }
            }
        }
        var faceId = (Math.floor(hash / CLOUD_PALETTES.length)) % CLOUD_FACES.length;
        var faceOverride = (opts && opts.face !== undefined && opts.face !== null) ? opts.face
                         : (overrides.face !== undefined && overrides.face !== null ? overrides.face : null);
        if (typeof faceOverride === 'number' && faceOverride >= 0 && faceOverride < CLOUD_FACES.length) {
            faceId = faceOverride;
        }
        var accessoryOverride = (opts && opts.accessory !== undefined && opts.accessory !== null) ? opts.accessory
                              : (overrides.accessory !== undefined && overrides.accessory !== null ? overrides.accessory : null);
        return { palette: palette, faceId: faceId, accessoryOverride: accessoryOverride };
    }

    function _cloudAvatarSVG(seed, sizePx, opts) {
        var size = sizePx || 28;
        var resolved = _resolveAvatarParts(seed, opts);
        var palette = resolved.palette;
        var faceId = resolved.faceId;
        // When the caller / stored preference overrides the accessory we
        // swap the CLOUD_FACES entry on a per-render copy so the face's
        // baked-in accessory is replaced rather than stacked on top of.
        var faceSpec = CLOUD_FACES[faceId] || CLOUD_FACES[0];
        if (resolved.accessoryOverride !== null) {
            faceSpec = [faceSpec[0], faceSpec[1], resolved.accessoryOverride];
        }
        var inner = _cloudFacePartsFromSpec(faceSpec, palette, size / 64);

        // Fluffier 7-bump silhouette. Replaces the old 4-bump cloud
        // with a plusher, more plushie-like outline that still fits
        // inside the 64x64 viewBox with 2px of padding on every side.
        // The feet (y=44) now curve back upward for a "tuft" look
        // instead of the old flat L-segment, which reads as softer
        // at 20px and more character-like at 80px.
        var body =
            '<path d="' +
                'M14 42 ' +
                'C 6 42 6 26 16 24 ' +
                'C 16 18 22 12 28 18 ' +
                'C 30 14 36 14 38 18 ' +
                'C 44 12 50 18 50 24 ' +
                'C 60 26 60 42 52 42 ' +
                'C 50 48 42 48 40 44 ' +
                'C 36 48 28 48 24 44 ' +
                'C 22 48 14 48 14 42 Z' +
            '" fill="' + palette.body + '" stroke="' + palette.edge + '" stroke-width="2.2" stroke-linejoin="round"/>';

        // Soft inner highlight arc on the top-left of the cloud so it
        // reads as having a light source, giving the creature gentle
        // depth without shadows or gradients.
        var highlight =
            '<path d="M18 24 Q18 18 24 18" stroke="#ffffff" stroke-width="1.6" stroke-linecap="round" fill="none" opacity="0.55"/>';

        // Optional sparkle ring: 6 tiny dots around the cloud body,
        // each at a different distance, hashed per-seed so everyone's
        // ring looks a touch different. CSS can animate the parent
        // `<g class="cloud-sparkles">` with a slow drift (see
        // styles.css .cloud-sparkles { animation: cloud-drift ... }).
        var sparkleHTML = '';
        var wantSparkle = opts && opts.sparkle;
        if (wantSparkle) {
            var sparkleSpecs = [
                { cx: 8,  cy: 16, r: 1.0 },
                { cx: 56, cy: 18, r: 1.2 },
                { cx: 4,  cy: 36, r: 0.9 },
                { cx: 60, cy: 38, r: 1.0 },
                { cx: 12, cy: 54, r: 1.2 },
                { cx: 52, cy: 54, r: 1.0 }
            ];
            sparkleHTML = '<g class="cloud-sparkles" fill="' + palette.edge + '" opacity="0.75">';
            for (var si = 0; si < sparkleSpecs.length; si++) {
                var s = sparkleSpecs[si];
                sparkleHTML +=
                    '<circle cx="' + s.cx + '" cy="' + s.cy + '" r="' + s.r + '" style="animation-delay:' + ((si * 0.35) % 2.1).toFixed(2) + 's"/>';
            }
            sparkleHTML += '</g>';
        }

        return '' +
            '<svg viewBox="0 0 64 64" width="' + size + '" height="' + size + '" ' +
                 'class="cloud-avatar-svg" data-cloud-palette="' + palette.name + '" aria-hidden="true">' +
                sparkleHTML + body + highlight + inner +
            '</svg>';
    }

    function _cloudAvatar(seed, sizePx, extraClassOrOpts) {
        // Back-compat shim: the third arg used to be a simple string
        // (extraClass). It can now be an options bag
        // `{ extraClass, sparkle, bounce }`. Detect both forms.
        var extraClass = '';
        var opts = {};
        if (typeof extraClassOrOpts === 'string') {
            extraClass = extraClassOrOpts;
        } else if (extraClassOrOpts && typeof extraClassOrOpts === 'object') {
            extraClass = extraClassOrOpts.extraClass || '';
            opts = extraClassOrOpts;
        }
        var cls = 'cloud-avatar' + (extraClass ? ' ' + extraClass : '');
        if (opts.sparkle)  cls += ' cloud-avatar--sparkle';
        if (opts.bounce)   cls += ' cloud-avatar--bounce';
        if (opts.breathing) cls += ' cloud-avatar--breathing';
        return '<span class="' + cls + '" title="' + _esc(seed) + '">' +
                   _cloudAvatarSVG(seed, sizePx, opts) +
               '</span>';
    }

    // Publish the cloud-face avatar generator so other modules (topology-auth.js
    // top-bar pill, future presence indicators, etc.) render the exact same
    // friendly creature for a given user across the whole app. Keeping a
    // single source of truth means the username hashing -> palette/face
    // mapping is identical everywhere, so a teammate's avatar is recognisable
    // whether you see it in the share dialog, the top-right user pill, or
    // any future "who's online" UI.
    //   window.CloudAvatar.svg(seed, sizePx, opts?)   -> raw inline <svg> markup
    //   window.CloudAvatar.html(seed, sizePx, opts?)  -> <span class="cloud-avatar"><svg></span>
    // opts (all optional): { sparkle:true, bounce:true, breathing:true, extraClass:'...' }
    window.CloudAvatar = window.CloudAvatar || {};
    window.CloudAvatar.svg = _cloudAvatarSVG;
    window.CloudAvatar.html = _cloudAvatar;
    // paletteNames lets the auth dropdown show a hint like "lavender" next
    // to the user's avatar for a tiny fun-fact; never user-visible-critical.
    window.CloudAvatar.paletteFor = function (seed) {
        var overrides = _AVATAR_OVERRIDES[seed];
        if (overrides && overrides.palette) return overrides.palette;
        var h = _hashStr(seed);
        return (CLOUD_PALETTES[h % CLOUD_PALETTES.length] || {}).name || '';
    };
    // Customise-Cloud hooks. setOverrides persists per-seed so subsequent
    // SVG renders reflect the user's choice without every call-site
    // needing to know it. clearOverrides reverts to the deterministic
    // hash. The catalogue methods feed the picker UI.
    window.CloudAvatar.setOverrides = function (seed, overrides) {
        if (!seed) return;
        if (!overrides) { delete _AVATAR_OVERRIDES[seed]; return; }
        _AVATAR_OVERRIDES[seed] = {
            palette: overrides.palette || null,
            face: (overrides.face === undefined ? null : overrides.face),
            accessory: (overrides.accessory === undefined ? null : overrides.accessory)
        };
        // Clean up keys that are null so a later "get" returns a tight
        // blob with only the fields the user actually customised.
        var stored = _AVATAR_OVERRIDES[seed];
        Object.keys(stored).forEach(function (k) {
            if (stored[k] === null || stored[k] === undefined) delete stored[k];
        });
        if (!Object.keys(stored).length) delete _AVATAR_OVERRIDES[seed];
        // Let listeners (top-bar pill, share dialog) refresh themselves.
        try {
            window.dispatchEvent(new CustomEvent('cloudavatar:changed', { detail: { seed: seed } }));
        } catch (_) {}
    };
    window.CloudAvatar.getOverrides = function (seed) {
        return Object.assign({}, _AVATAR_OVERRIDES[seed] || {});
    };
    window.CloudAvatar.clearOverrides = function (seed) {
        delete _AVATAR_OVERRIDES[seed];
        try {
            window.dispatchEvent(new CustomEvent('cloudavatar:changed', { detail: { seed: seed } }));
        } catch (_) {}
    };
    window.CloudAvatar.catalogue = function () {
        return {
            palettes: CLOUD_PALETTES.map(function (p) { return { name: p.name, body: p.body, edge: p.edge, face: p.face, cheek: p.cheek }; }),
            faces: CLOUD_FACES.map(function (f, i) { return { id: i, eyes: f[0], mouth: f[1] }; }),
            accessories: Object.keys(CLOUD_ACCESSORIES).map(function (k) {
                return { id: parseInt(k, 10), label: CLOUD_ACCESSORIES[k].label, emoji: CLOUD_ACCESSORIES[k].emoji };
            }).sort(function (a, b) { return a.id - b.id; })
        };
    };

    var SVG = {
        folder: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>',
        plus: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
        share: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>',
        chev: '<svg class="share-chev" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 6 15 12 9 18"/></svg>',
        search: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
        x: '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
        clock: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/></svg>',
        file: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
        lock: '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="11" width="16" height="10" rx="2" ry="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>',
        // Cute cloud (matches the cloud-face avatar palette so the synthetic
        // domain header reads as part of the same family).
        cloud: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19a4.5 4.5 0 1 0-1.4-8.78 6 6 0 0 0-11.6 2.28A4 4 0 0 0 6 19h11.5z"/></svg>'
    };

    // Shimmering placeholder rendered while the popover fetches its data.
    // Mirrors the eventual layout (section header + 3 rows + 2nd header + 2 rows)
    // so the user's eye doesn't have to re-anchor when real content arrives.
    function _skeletonHTML() {
        var row = '<div class="share-skel-row">' +
                      '<div class="share-skel-icon"></div>' +
                      '<div class="share-skel-line"></div>' +
                      '<div class="share-skel-line short"></div>' +
                  '</div>';
        var rowSlim = '<div class="share-skel-row">' +
                          '<div class="share-skel-icon"></div>' +
                          '<div class="share-skel-line"></div>' +
                      '</div>';
        return '<div class="share-skeleton" aria-hidden="true">' +
                   '<div class="share-skel-line title"></div>' +
                   row + row + row +
                   '<div class="share-skel-line title"></div>' +
                   rowSlim + rowSlim +
               '</div>';
    }

    // ----------------------------------------------------------------
    // Backend
    // ----------------------------------------------------------------
    async function _fetchOverview() {
        var resp = await _authFetch(DOMAINS_API + '/share/overview');
        return resp.ok ? await resp.json() : null;
    }
    async function _fetchTargets() {
        var resp = await _authFetch(DOMAINS_API + '/share/targets');
        return resp.ok ? await resp.json() : [];
    }
    async function _fetchOutgoing() {
        var resp = await _authFetch(DOMAINS_API + '/share/outgoing');
        return resp.ok ? await resp.json() : [];
    }
    async function _fetchIncoming() {
        var resp = await _authFetch(DOMAINS_API + '/share/incoming');
        return resp.ok ? await resp.json() : [];
    }
    async function _fetchActivity() {
        var resp = await _authFetch(DOMAINS_API + '/share/activity?scope=involving&limit=50');
        return resp.ok ? await resp.json() : [];
    }
    async function _fetchOutgoingFiles() {
        var resp = await _authFetch(DOMAINS_API + '/share/files/outgoing');
        return resp.ok ? await resp.json() : [];
    }
    async function _fetchIncomingFiles() {
        var resp = await _authFetch(DOMAINS_API + '/share/files/incoming');
        return resp.ok ? await resp.json() : [];
    }
    async function _fetchTopologiesForDomain(domainId) {
        if (_domainTopologyCache[domainId]) return _domainTopologyCache[domainId];
        var resp = await _authFetch(DOMAINS_API + '/' + domainId + '/topologies');
        if (!resp.ok) return [];
        var rows = await resp.json();
        _domainTopologyCache[domainId] = rows;
        return rows;
    }
    function _invalidateDomainTopologyCache(domainId) {
        if (domainId) delete _domainTopologyCache[domainId];
        else _domainTopologyCache = {};
    }
    async function _createDomain(name, description) {
        if (window.TopologyDomains && window.TopologyDomains.createDomain) {
            return window.TopologyDomains.createDomain(name, description);
        }
        var resp = await _authFetch(DOMAINS_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, description: description || '' })
        });
        if (!resp.ok) throw new Error('Could not create domain');
        return resp.json();
    }

    // ----------------------------------------------------------------
    // Top-bar share pill -- REMOVED (2026-04-21d)
    //
    // Used to render a "My Topologies [5] [share-icon]" pill in the
    // top toolbar whose whole surface was the share-dialog entry
    // point. Killed on user request because it duplicated an
    // affordance that already lives on every row in the Topologies
    // dropdown (per-file share icon, per-domain share form) and on
    // the domain header. The pill itself did nothing the dropdown
    // didn't already cover, so it was visual noise.
    //
    // Kept as a no-op (rather than deleted) because:
    //   - `topology-domains:changed` and `DOMContentLoaded` still
    //     fire this function; ripping it out would require editing
    //     two event listeners for zero behavioural gain.
    //   - `TopologyShare.open(anchorEl)` is still called from
    //     `topology-file-ops.js` (per-topology share button path);
    //     that code is unaffected -- it never went through the pill.
    //
    // The `#auth-share-toolbar` container is hidden + emptied
    // defensively so no stale markup lingers across page reloads.
    // ----------------------------------------------------------------
    function _renderToolbar() {
        var host = document.getElementById('auth-share-toolbar');
        if (!host) return;
        host.style.display = 'none';
        host.innerHTML = '';
    }

    // ----------------------------------------------------------------
    // Inline share forms
    // ----------------------------------------------------------------
    // Two separate inline surfaces, depending on WHAT the user wants to share:
    //
    // 1) Domain-level share: opened by the third "Share" button in the
    //    Save/Load row. Renders a compact form into .domain-share-form
    //    inside the clicked .domain-body. The form contains ONLY the
    //    recipients + chip-input for the whole domain -- no scope picker,
    //    no re-listed file list, since the dropdown already shows the
    //    domain's file list right below it.
    //
    // 2) Per-topology share: opened by the share icon on an individual
    //    topology row. Inserts a .topo-share-form element as the IMMEDIATE
    //    NEXT SIBLING of that topology row, so the form visually sits
    //    right under the file it shares. Same compact shape as the domain
    //    form, but scoped to that one topology.
    //
    // Only ONE inline form is open at any time across the whole dropdown.
    // Opening another share button closes whichever one is currently
    // active, so the dropdown never stacks multiple share panels.

    var _activeInline = null;
    // Shape: { kind: 'domain'|'topo', row: Element, domainId: string,
    //          topoRow?: Element, topoId?: string, host: Element }

    function _getDropdown() {
        return document.getElementById('topologies-dropdown-menu');
    }

    function _getTopologiesBtn() {
        return document.getElementById('btn-topologies');
    }

    // If the topologies dropdown isn't already open, show it anchored to
    // the toolbar Topologies button (mirrors the positioning code used
    // by toolbar-setup + topology.js). Returns true on success.
    function _openTopologiesDropdown() {
        var dd = _getDropdown();
        if (!dd) return false;
        if (dd.style.display === 'block') return true;

        var btn = _getTopologiesBtn();
        dd.style.display = 'block';
        if (btn) {
            try {
                var r = btn.getBoundingClientRect();
                dd.style.position = 'fixed';
                // Keep the dropdown off the left toolbar sidebar --
                // FileOps._clampDropdownLeft does the math. Fall back to
                // the raw button edge if FileOps isn't loaded yet (very
                // early share-link deeplinks), so we still position
                // something instead of nothing.
                var leftPx = r.left;
                if (window.FileOps && typeof window.FileOps._clampDropdownLeft === 'function') {
                    leftPx = window.FileOps._clampDropdownLeft(r.left);
                }
                dd.style.left = leftPx + 'px';
                dd.style.top = (r.bottom + 4) + 'px';
                btn.classList.add('topologies-open');
            } catch (_) { /* best-effort positioning */ }
        }
        return true;
    }

    // Resolve the rendered .custom-section-category element for a domain.
    // Three lookup strategies (in priority order):
    //   1. anchorEl inside the row -> closest('.custom-section-category')
    //   2. match by section id on the row's data-section-id (when the
    //      custom-section id happens to equal the domain id)
    //   3. match by domain name against the visible title text in each row
    function _findDomainRow(domain, anchorEl) {
        if (anchorEl && anchorEl.closest) {
            var row = anchorEl.closest('.custom-section-category');
            if (row) return row;
        }
        var dd = _getDropdown();
        if (!dd || !domain) return null;

        var byId = dd.querySelector('.custom-section-category[data-section-id="' +
            (domain.id || '').replace(/"/g, '\\"') + '"]');
        if (byId) return byId;

        var rows = dd.querySelectorAll('.custom-section-category');
        var want = String(domain.name || '').toLowerCase();
        for (var i = 0; i < rows.length; i++) {
            var title = rows[i].querySelector('.domain-title span');
            if (title && title.textContent.trim().toLowerCase() === want) return rows[i];
        }
        return null;
    }

    // Host slot for the domain-level share form lives in .domain-body, BEFORE
    // the topology list so it appears between the button row and the files.
    function _ensureDomainShareHost(row) {
        if (!row) return null;
        var host = row.querySelector(':scope > .domain-body > .domain-share-form');
        if (host) return host;
        var body = row.querySelector(':scope > .domain-body');
        if (!body) return null;
        host = document.createElement('div');
        host.className = 'domain-share-form';
        host.style.display = 'none';
        var toposList = body.querySelector(':scope > .domain-topos-list');
        if (toposList) body.insertBefore(host, toposList);
        else body.appendChild(host);
        return host;
    }

    // Host slot for the per-topology share form is a fresh sibling inserted
    // immediately after the topology row, so it visually belongs to that file.
    function _ensureTopoShareHost(topoRow) {
        if (!topoRow) return null;
        var next = topoRow.nextElementSibling;
        if (next && next.classList && next.classList.contains('topo-share-form')) return next;
        var host = document.createElement('div');
        host.className = 'topo-share-form';
        host.style.display = 'none';
        topoRow.parentNode.insertBefore(host, topoRow.nextSibling);
        return host;
    }

    // Remove any .topo-share-form node that isn't the active one (in case
    // a previous row was refreshed while the form was mounted and now
    // looks like a phantom leftover).
    function _cleanupOrphanTopoForms() {
        var dd = _getDropdown();
        if (!dd) return;
        dd.querySelectorAll('.topo-share-form').forEach(function (el) {
            if (_activeInline && _activeInline.host === el) return;
            el.remove();
        });
    }

    // Render the compact domain-only share body: recipients list + chip
    // input. No scope picker, no file list (the dropdown already shows it).
    function _renderDomainShareBody(host, domain) {
        var meta = _outgoing.find(function (x) { return x.domain_id === domain.id; });
        var recipients = (meta && meta.recipients) || [];
        var body = host.querySelector('.dsf-body');
        if (!body) return;
        // Force scope to 'domain' so the shared _renderShareForm builds
        // the right wiring, even though the picker isn't visible.
        var draft = _ensureDraft(domain.id);
        draft.scope = 'domain';
        body.innerHTML =
            '<div class="share-domain-item expanded" data-domain-id="' + _esc(domain.id) + '">' +
                '<div class="share-domain-detail">' +
                    _renderDomainRecipients(recipients) +
                    _renderShareForm(domain, recipients) +
                '</div>' +
            '</div>';
        _attachHandlers(body);
    }

    // Render the compact per-topology share body.
    function _renderTopoShareBody(host, domain, topology) {
        var existing = _outgoingFiles.find(function (f) {
            return f.domain_id === domain.id && f.topology_id === topology.id;
        });
        var recipients = (existing && existing.recipients) || [];
        var body = host.querySelector('.dsf-body');
        if (!body) return;
        body.innerHTML =
            '<div class="share-file-item expanded" data-domain-id="' + _esc(domain.id) +
                '" data-topology-id="' + _esc(topology.id) + '">' +
                '<div class="share-file-detail">' +
                    _renderTopologyRecipients(domain, topology, recipients) +
                    _renderTopologyShareForm(domain, topology, recipients) +
                '</div>' +
            '</div>';
        _attachHandlers(body);
    }

    function _renderInlineSkeleton(host, titleText) {
        host.innerHTML =
            '<div class="dsf-head">' +
                SVG.share +
                '<span class="dsf-title">' + _esc(titleText) + '</span>' +
                '<button type="button" class="dsf-close" aria-label="Close share panel">&times;</button>' +
            '</div>' +
            '<div class="dsf-body">' + _skeletonHTML() + '</div>';
        var closeBtn = host.querySelector('.dsf-close');
        if (closeBtn) closeBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            _closeInline();
        });
    }

    // Re-render only the currently-open inline form. Called after share /
    // revoke / perm-change actions so the recipient list + chip state
    // stay in sync with server truth.
    function _refreshInlineForm() {
        if (!_activeInline) return;
        var a = _activeInline;
        if (!a.host || !document.body.contains(a.host)) { _closeInline(); return; }
        var domain = _ownDomains().find(function (d) { return d.id === a.domainId; });
        if (!domain) { _closeInline(); return; }
        if (a.kind === 'domain') {
            _renderDomainShareBody(a.host, domain);
        } else if (a.kind === 'topo') {
            var topo = _lookupTopology(domain.id, a.topoId);
            if (!topo) { _closeInline(); return; }
            _renderTopoShareBody(a.host, domain, topo);
        }
    }

    // Backward-compatible alias: every internal handler that used to call
    // _renderBody() (the full-dialog rebuild) now just re-renders the
    // currently-active inline form.
    function _renderBody() { _refreshInlineForm(); }

    function _closeInline() {
        if (!_activeInline) return;
        var a = _activeInline;
        if (a.host) {
            a.host.classList.remove('open');
            a.host.style.display = 'none';
            if (a.kind === 'topo' && a.host.parentNode) {
                // Per-topology slot is transient -- drop it so it doesn't
                // linger as an empty sibling under the topology row.
                a.host.remove();
            }
        }
        _activeInline = null;
        _pendingContext = null;
        _activeAnchor = null;
        // If a share/unshare/perm-change happened while this form was
        // open, the global `topology-domains:changed` listener skipped
        // its rebuild (the `.topo-share-form.open` / `.domain-share-form
        // .open` guard in topology-file-ops.js avoids ripping the live
        // popover out of the DOM). Now that the form is gone, re-emit
        // the event so the listener can run the rebuild it previously
        // skipped -- that's what makes the outgoing-share badge + "Stop
        // sharing with everyone" icon appear immediately, without the
        // user having to F5.
        if (_inlineDirty) {
            _inlineDirty = false;
            try {
                document.dispatchEvent(new CustomEvent('topology-domains:changed', {
                    detail: { source: 'share-inline-closed' }
                }));
            } catch (_) { /* best-effort */ }
        }
    }

    // Open the domain-level compact share form under a given domain row.
    async function _openDomainShareAt(domain, row) {
        if (!domain || !row) return;
        // Toggle: clicking the same row's Share button again closes it.
        if (_activeInline && _activeInline.kind === 'domain' &&
            _activeInline.row === row && _activeInline.domainId === domain.id) {
            _closeInline();
            return;
        }
        if (_activeInline) _closeInline();
        // Mutual exclusion with the Create-Bug inline panel: only one
        // inline panel may live in the Topologies dropdown at a time.
        try {
            if (window.TopologyBugs && typeof window.TopologyBugs.close === 'function') {
                window.TopologyBugs.close();
            }
        } catch (_) { /* best-effort */ }
        // Mutual exclusion with the AI drawer: opening a share form
        // closes the AI drawer so the user never has two side panels
        // competing for space (mirrors the reverse hook in topology-ai.js).
        try {
            if (window.TopologyAI && typeof window.TopologyAI.close === 'function') {
                window.TopologyAI.close();
            }
        } catch (_) { /* best-effort */ }

        var host = _ensureDomainShareHost(row);
        if (!host) return;

        // Make sure the row's body is expanded so the user sees the form.
        var bodyEl = row.querySelector(':scope > .domain-body');
        if (bodyEl && bodyEl.style.display === 'none') {
            bodyEl.style.display = 'block';
            var chev = row.querySelector('.domain-chevron');
            if (chev) chev.style.transform = 'rotate(0deg)';
            try {
                var editor = window.topologyEditor;
                if (editor && editor._domainCollapsed) {
                    var sid = row.dataset.sectionId;
                    if (sid) editor._domainCollapsed[sid] = false;
                }
            } catch (_) { /* best-effort */ }
        }

        _activeInline = { kind: 'domain', row: row, domainId: domain.id, host: host };
        _renderInlineSkeleton(host, 'Share ' + domain.name);
        host.style.display = 'block';
        void host.offsetHeight;
        host.classList.add('open');

        await _refreshAll();
        if (!_activeInline || _activeInline.host !== host) return;
        _renderDomainShareBody(host, domain);
        try { host.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); } catch (_) {}
    }

    // Open the per-topology compact share form under a given topology row.
    async function _openTopoShareAt(domain, topology, topoRow) {
        if (!domain || !topology || !topoRow) return;
        // Toggle: clicking the same topology's share icon closes it.
        if (_activeInline && _activeInline.kind === 'topo' &&
            _activeInline.topoRow === topoRow && _activeInline.topoId === topology.id) {
            _closeInline();
            return;
        }
        if (_activeInline) _closeInline();
        // Mutual exclusion with the Create-Bug inline panel (see
        // _openDomainShareAt for rationale).
        try {
            if (window.TopologyBugs && typeof window.TopologyBugs.close === 'function') {
                window.TopologyBugs.close();
            }
        } catch (_) { /* best-effort */ }
        // Mutual exclusion with the AI drawer (see _openDomainShareAt).
        try {
            if (window.TopologyAI && typeof window.TopologyAI.close === 'function') {
                window.TopologyAI.close();
            }
        } catch (_) { /* best-effort */ }
        _cleanupOrphanTopoForms();

        var host = _ensureTopoShareHost(topoRow);
        if (!host) return;

        _activeInline = {
            kind: 'topo',
            row: topoRow.closest('.custom-section-category'),
            topoRow: topoRow,
            domainId: domain.id,
            topoId: topology.id,
            host: host
        };
        _renderInlineSkeleton(host, 'Share ' + topology.name);
        host.style.display = 'block';
        void host.offsetHeight;
        host.classList.add('open');

        await _refreshAll();
        if (!_activeInline || _activeInline.host !== host) return;
        _renderTopoShareBody(host, domain, topology);
        try { host.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); } catch (_) {}
    }

    // Resolve a topology by id (preferred) or name within a domain.
    function _lookupTopology(domainId, topoIdOrName) {
        var topos = _domainTopologyCache[domainId] || [];
        var target = String(topoIdOrName || '').toLowerCase();
        var byId = topos.find(function (t) { return String(t.id).toLowerCase() === target; });
        if (byId) return byId;
        return topos.find(function (t) { return String(t.name || '').toLowerCase() === target; }) || null;
    }

    // Find the .domain-topo-row for a topology by filename/name (which is
    // what file-ops puts in data-filename for legacy-API rows).
    function _findTopoRow(domainRow, topoName) {
        if (!domainRow || !topoName) return null;
        var want = String(topoName).toLowerCase();
        var rows = domainRow.querySelectorAll(':scope > .domain-body > .domain-topos-list .domain-topo-row');
        for (var i = 0; i < rows.length; i++) {
            var nameEl = rows[i].querySelector('.topo-entry-name');
            if (nameEl && nameEl.textContent.trim().toLowerCase() === want) return rows[i];
            var fn = (rows[i].dataset.filename || '').replace(/\.json$/i, '').toLowerCase();
            if (fn === want) return rows[i];
        }
        return null;
    }

    // Public entry point: toolbar share pill (`#share-topology-btn`).
    // Opens the domain-level share form for the currently active domain.
    async function openDialog(anchorEl) {
        if (!_openTopologiesDropdown()) return;
        await _refreshAllStableForInlineOpen();
        var active = _activeDomain();
        var domain = (active && !active.is_shared) ? active : _ownDomains()[0];
        if (!domain) {
            _toast('No shareable domain is available yet', 'warning');
            return;
        }
        var row = _findDomainRow(domain, anchorEl);
        if (!row || !document.body.contains(row)) row = _findDomainRow(domain, null);
        if (!row) {
            _toast('Could not find this domain row in the Topologies panel', 'warning');
            return;
        }
        await _openDomainShareAt(domain, row);
    }

    // Deep link: open the inline share form for a specific domain or file.
    //   openForDomain('FLOWSPEC-VPN', null, btn)          -> whole-domain form
    //   openForDomain('FLOWSPEC-VPN', 'my_topo', btn)     -> per-file form under that row
    async function openForDomain(domainHint, topologyName, anchorEl) {
        if (!_openTopologiesDropdown()) return;
        await _refreshAllStableForInlineOpen();
        _pendingContext = { domainHint: domainHint || '', topologyName: topologyName || '' };
        var domain = _findDomainByHint(domainHint);
        if (!domain && domainHint && !topologyName) {
            try {
                domain = await _createDomain(
                    String(domainHint),
                    'Mirrored from Topologies dropdown for domain sharing'
                );
                await _refreshAllStableForInlineOpen();
                domain = _findDomainByHint((domain && domain.id) || domainHint);
            } catch (_) {
                await _refreshAllStableForInlineOpen();
                domain = _findDomainByHint(domainHint);
            }
        }
        if (!domain) {
            _toast('Could not prepare this domain for sharing', 'warning');
            return;
        }
        var row = _findDomainRow(domain, anchorEl);
        if (!row || !document.body.contains(row)) row = _findDomainRow(domain, null);
        if (!row && anchorEl && anchorEl.closest) row = anchorEl.closest('.custom-section-category');
        if (!row) {
            _toast('Could not find this domain row in the Topologies panel', 'warning');
            return;
        }

        if (!topologyName) {
            await _openDomainShareAt(domain, row);
            return;
        }

        // Per-topology: prefer the exact row under the anchor (handles the
        // case where two domains happen to share a topology name).
        var topoRow = anchorEl && anchorEl.closest ? anchorEl.closest('.domain-topo-row') : null;
        if (!topoRow) topoRow = _findTopoRow(row, topologyName);
        if (!topoRow) return;

        // Resolve topology metadata from the share cache; fetch on demand.
        if (!_domainTopologyCache[domain.id]) {
            try { await _fetchTopologiesForDomain(domain.id); } catch (_) {}
        }
        var topology = _lookupTopology(domain.id, topologyName);
        if (!topology) {
            // Server-side name mismatch: synthesize a minimal record so
            // the form still opens; recipients will just be empty.
            topology = { id: topologyName, name: topologyName };
        }
        await _openTopoShareAt(domain, topology, topoRow);
    }

    function _findDomainByHint(hint) {
        if (!hint) return null;
        var h = String(hint).toLowerCase();
        var owns = _ownDomains();
        var byId = owns.find(function (d) { return String(d.id).toLowerCase() === h; });
        if (byId) return byId;
        return owns.find(function (d) { return String(d.name || '').toLowerCase() === h; }) || null;
    }

    // Close the active inline form, if any. (Public alias for _closeInline.)
    function closeDialog() { _closeInline(); }

    async function _refreshAll() {
        if (_loading) return;
        _loading = true;
        try {
            // Per-file share endpoints are NEW -- if the backend hasn't been
            // restarted yet, swallow their failures so the rest of the dialog
            // keeps working with the per-domain data.
            var results = await Promise.all([
                _fetchOverview(),
                _fetchTargets(),
                _fetchOutgoing(),
                _fetchIncoming(),
                _fetchActivity(),
                _fetchOutgoingFiles().catch(function () { return []; }),
                _fetchIncomingFiles().catch(function () { return []; }),
                window.TopologyDomains && window.TopologyDomains.fetchDomains
                    ? window.TopologyDomains.fetchDomains() : Promise.resolve([])
            ]);
            _overview = results[0];
            _users = results[1] || [];
            _outgoing = results[2] || [];
            _incoming = results[3] || [];
            _activity = results[4] || [];
            _outgoingFiles = results[5] || [];
            _incomingFiles = results[6] || [];
            _invalidateDomainTopologyCache();
            _renderToolbar();
        } finally {
            _loading = false;
        }
    }

    async function _refreshAllStableForInlineOpen() {
        if (window.FileOps) {
            window.FileOps._suspendDropdownRefresh = (window.FileOps._suspendDropdownRefresh || 0) + 1;
        }
        try {
            await _refreshAll();
        } finally {
            if (window.FileOps) {
                window.FileOps._suspendDropdownRefresh = Math.max(
                    0, (window.FileOps._suspendDropdownRefresh || 1) - 1,
                );
            }
        }
    }

    // ----------------------------------------------------------------
    // Single-view rendering
    // ----------------------------------------------------------------
    function _ownDomains() {
        // The synthetic "Shared with me" inbox is technically tagged as
        // shared (not owned) -- already excluded by !d.is_shared. We belt-and-
        // brace it here too so future schema changes don't accidentally
        // surface it in the "My domains" section of the dialog.
        return _domains().filter(function (d) {
            return !d.is_shared && !d.is_shared_with_me_domain;
        });
    }

    function _isSharedWithMeDomain(d) {
        return d && (d.id === SHARED_WITH_ME_DOMAIN_ID || d.is_shared_with_me_domain);
    }

    function _ensureDraft(domainId) {
        if (!_shareDrafts[domainId]) {
            _shareDrafts[domainId] = {
                scope: 'domain',  // 'domain' (whole) or 'files' (specific topology files)
                targets: {},      // {username: true} -- selected chip set (whole-domain mode)
                fileTargets: {},  // {topologyId: true} -- which files to share when scope=files
                perm: 'read',     // permission for new grants
                search: '',       // current input text (typeahead query)
                activeIdx: -1,    // keyboard-focused suggestion row
                focused: false    // whether the chip-input has focus -> show typeahead
            };
        }
        return _shareDrafts[domainId];
    }

    // Per-topology share draft state. Keyed by composite "domainId:topologyId"
    // so each file gets its own typeahead state and chip set.
    function _topoKey(domainId, topologyId) {
        return domainId + '|' + topologyId;
    }
    function _ensureTopoDraft(domainId, topologyId) {
        var key = _topoKey(domainId, topologyId);
        if (!_topologyDrafts[key]) {
            _topologyDrafts[key] = {
                targets: {}, perm: 'read', search: '',
                activeIdx: -1, focused: false
            };
        }
        return _topologyDrafts[key];
    }

    // NOTE: the earlier full-dialog renderers (_renderBody / _renderMySection
    // / _renderMyDomain / _renderIncomingSection / _renderActivitySection /
    // _renderActivitySummary) were removed when the share surface moved
    // inline under the domain row. _renderBody is now defined earlier in
    // this file as an alias for _refreshInlineForm so every action handler
    // that used to re-render the whole dialog keeps working. Only the
    // per-domain scope + form renderers below are still used, plus the
    // per-file (topology-scoped) share surface reached via the "Specific
    // files" scope button.

    // The scope toggle lets the user choose between sharing the WHOLE domain
    // (every topology inside, plus future ones) and sharing INDIVIDUAL files.
    // Whole-domain mode is the historical default and is selected first.
    function _renderScopePicker(d) {
        var draft = _ensureDraft(d.id);
        return '<div class="share-scope-picker" role="tablist" aria-label="Sharing scope">' +
                   '<button class="share-scope-btn' + (draft.scope === 'domain' ? ' active' : '') + '" ' +
                       'data-action="set-scope" data-scope="domain" data-domain-id="' + _esc(d.id) + '" role="tab">' +
                       SVG.folder + '<span>Whole domain</span>' +
                   '</button>' +
                   '<button class="share-scope-btn' + (draft.scope === 'files' ? ' active' : '') + '" ' +
                       'data-action="set-scope" data-scope="files" data-domain-id="' + _esc(d.id) + '" role="tab">' +
                       SVG.file + '<span>Specific files</span>' +
                   '</button>' +
               '</div>';
    }

    function _renderScopeBody(d, recipients) {
        var draft = _ensureDraft(d.id);
        if (draft.scope === 'files') {
            return _renderFilesScope(d);
        }
        return _renderDomainRecipients(recipients) + _renderShareForm(d, recipients);
    }

    // Files scope: list each topology inside the domain. Each row is a
    // collapsible mini-share-card with its own recipients + chip-input form.
    // We resolve topology metadata lazily (cached) so opening a domain with
    // dozens of files doesn't hammer the server.
    function _renderFilesScope(d) {
        var topos = _domainTopologyCache[d.id];
        if (!topos) {
            // Trigger fetch + re-render once it lands.
            _fetchTopologiesForDomain(d.id).then(function () {
                _renderBody();
            }).catch(function () {});
            return '<div class="share-files-loading">' + _skeletonHTML() + '</div>';
        }
        if (topos.length === 0) {
            return '<div class="share-empty">' +
                       'No topology files yet -- save a topology to this domain first, ' +
                       'or share the whole domain instead.' +
                   '</div>';
        }
        var html = '<div class="share-files-list">';
        topos.forEach(function (t) {
            html += _renderTopologyShareItem(d, t);
        });
        html += '</div>';
        return html;
    }

    function _renderTopologyShareItem(d, t) {
        var key = _topoKey(d.id, t.id);
        var expanded = _expandedTopologies[d.id] && _expandedTopologies[d.id][t.id];
        // Outgoing per-file shares for this exact topology
        var existing = _outgoingFiles.find(function (f) {
            return f.domain_id === d.id && f.topology_id === t.id;
        });
        var recipients = (existing && existing.recipients) || [];
        var summary;
        if (recipients.length === 0) {
            summary = 'private';
        } else {
            var names = recipients.slice(0, 2).map(function (r) { return r.display_name || r.username; });
            summary = 'shared with ' + names.join(', ');
            if (recipients.length > 2) summary += ' +' + (recipients.length - 2);
        }
        var html = '<div class="share-file-item' + (expanded ? ' expanded' : '') + '" data-domain-id="' + _esc(d.id) + '" data-topology-id="' + _esc(t.id) + '">';
        html +=
            '<div class="share-row share-file-header" data-action="toggle-topology">' +
                SVG.file +
                '<span class="share-row-name">' + _esc(t.name) + '</span>' +
                '<span class="share-row-sub">' + _esc(summary) + '</span>' +
                (recipients.length > 0
                    ? '<span class="share-row-count" title="' + recipients.length + ' recipient' + (recipients.length === 1 ? '' : 's') + '">' + recipients.length + '</span>'
                    : '') +
                SVG.chev +
            '</div>';
        if (expanded) {
            html +=
                '<div class="share-file-detail">' +
                    _renderTopologyRecipients(d, t, recipients) +
                    _renderTopologyShareForm(d, t, recipients) +
                '</div>';
        }
        html += '</div>';
        return html;
    }

    function _renderDomainRecipients(recipients) {
        if (recipients.length === 0) return '';
        var html = '<div class="share-detail-block">';
        html += '<div class="share-detail-label">People with access (' + recipients.length + ')</div>';
        recipients.forEach(function (r) {
            var permClass = (r.permission === 'write') ? 'write' : 'read';
            var nextPerm = (r.permission === 'read') ? 'write' : 'read';
            // permClass stays wire-token-based ('read' / 'write') so the
            // existing CSS in styles.css picks up the colour family.
            // The label text the user reads gets translated to View / Edit.
            var permTextLabel = permissionLabel(r.permission) || _esc(r.permission);
            var nextPermLabel = permissionLabel(nextPerm) || _esc(nextPerm);
            html +=
                '<div class="share-recipient-row">' +
                    _cloudAvatar(r.username, 32) +
                    '<div class="share-recipient-info">' +
                        '<div class="share-recipient-name">' + _esc(r.display_name || r.username) + '</div>' +
                        '<div class="share-recipient-meta">@' + _esc(r.username) + ' &middot; ' + _esc(_ago(r.granted_at)) + '</div>' +
                    '</div>' +
                    '<button class="share-mini-btn share-perm-pill ' + permClass + '" data-action="perm-toggle" data-target="' + _esc(r.username) + '" data-current-perm="' + _esc(r.permission) + '" title="Click to switch to ' + _esc(nextPermLabel) + '">' + _esc(permTextLabel) + '</button>' +
                    '<button class="share-mini-btn danger" data-action="revoke" data-target="' + _esc(r.username) + '" title="Revoke access">' + SVG.x + '</button>' +
                '</div>';
        });
        html += '</div>';
        return html;
    }

    // Per-file recipients block. Mirrors the per-domain one but every action
    // carries the topology id too so handlers can hit the per-file API.
    function _renderTopologyRecipients(d, t, recipients) {
        if (recipients.length === 0) return '';
        var html = '<div class="share-detail-block">';
        html += '<div class="share-detail-label">People with access to this file (' + recipients.length + ')</div>';
        recipients.forEach(function (r) {
            var permClass = (r.permission === 'write') ? 'write' : 'read';
            var nextPerm = (r.permission === 'read') ? 'write' : 'read';
            var permTextLabel = permissionLabel(r.permission) || _esc(r.permission);
            var nextPermLabel = permissionLabel(nextPerm) || _esc(nextPerm);
            html +=
                '<div class="share-recipient-row">' +
                    _cloudAvatar(r.username, 32) +
                    '<div class="share-recipient-info">' +
                        '<div class="share-recipient-name">' + _esc(r.display_name || r.username) + '</div>' +
                        '<div class="share-recipient-meta">@' + _esc(r.username) + ' &middot; ' + _esc(_ago(r.granted_at)) + '</div>' +
                    '</div>' +
                    '<button class="share-mini-btn share-perm-pill ' + permClass + '" ' +
                        'data-action="perm-toggle-topo" ' +
                        'data-domain-id="' + _esc(d.id) + '" data-topology-id="' + _esc(t.id) + '" ' +
                        'data-target="' + _esc(r.username) + '" data-current-perm="' + _esc(r.permission) + '" ' +
                        'title="Click to switch to ' + _esc(nextPermLabel) + '">' + _esc(permTextLabel) + '</button>' +
                    '<button class="share-mini-btn danger" data-action="revoke-topo" ' +
                        'data-domain-id="' + _esc(d.id) + '" data-topology-id="' + _esc(t.id) + '" ' +
                        'data-target="' + _esc(r.username) + '" title="Revoke access">' + SVG.x + '</button>' +
                '</div>';
        });
        html += '</div>';
        return html;
    }

    // Compact chip-input share form.
    // Layout (vertically):
    //   [Send to:                                       Read v]
    //   [ [chip][chip] |--input--|                            ]
    //   [ floating typeahead dropdown (only when focused/typing) ]
    //   [                                              [Share] ]
    //
    // The chip-input is a single visual field where selected users live as
    // removable pills and typing happens at the trailing input. Suggestions
    // are positioned just below as a soft floating panel so the eye lands
    // naturally between input and pick.
    function _renderShareForm(d, recipients) {
        var draft = _ensureDraft(d.id);
        var existingByUsername = {};
        recipients.forEach(function (r) { existingByUsername[r.username] = r; });

        var picks = Object.keys(draft.targets);
        var label = recipients.length > 0 ? 'Add more people' : 'Share with someone';
        // User-facing label (View / Edit) -- wire tokens stay read/write.
        var permLabel = permissionLabel(draft.perm) || 'View';

        var html = '<div class="share-form share-form-typeahead">';
        html +=
            '<div class="share-form-row">' +
                '<div class="share-detail-label share-form-label">' + label + '</div>' +
                '<div class="share-perm-mini" data-action="toggle-perm" data-perm="' + _esc(draft.perm) + '" title="Click to switch permission">' +
                    '<span class="share-perm-mini-dot ' + (draft.perm === 'write' ? 'write' : 'read') + '"></span>' +
                    '<span class="share-perm-mini-label">' + _esc(permLabel) + '</span>' +
                    SVG.chev +
                '</div>' +
            '</div>';

        html += '<div class="share-chip-input' + (draft.focused ? ' is-focused' : '') + '" data-action="focus-input">';
        picks.forEach(function (username) {
            var u = _users.find(function (x) { return x.username === username; }) || { username: username, display_name: username };
            html +=
                '<span class="share-chip" data-username="' + _esc(username) + '">' +
                    _cloudAvatar(u.username, 20, 'share-chip-avatar') +
                    '<span class="share-chip-name">' + _esc(u.display_name || u.username) + '</span>' +
                    '<button type="button" class="share-chip-remove" data-action="remove-chip" data-username="' + _esc(username) + '" title="Remove" tabindex="-1">' + SVG.x + '</button>' +
                '</span>';
        });
        var placeholder = picks.length === 0 ? 'Type a name or username...' : 'Add another...';
        html +=
            '<input type="text" class="share-chip-text" placeholder="' + placeholder + '" ' +
                'value="' + _esc(draft.search) + '" autocomplete="off" spellcheck="false" />';
        html += '</div>';

        html += '<div class="share-typeahead-wrap">' + _renderTypeahead(d.id, existingByUsername) + '</div>';

        html +=
            '<div class="share-form-footer">' +
                '<div class="share-form-hint">' +
                    (picks.length === 0
                        ? 'Tip: arrow keys to navigate, enter to add, backspace to remove'
                        : (picks.length + ' selected')) +
                '</div>' +
                _renderShareSubmit(d.id) +
            '</div>';
        html += '</div>';
        return html;
    }

    // Floating suggestions list (only when input is focused or has text and
    // there is something to show). Selected chips are excluded from the list
    // because they already live in the chip area above.
    function _renderTypeahead(domainId, existingByUsername) {
        var draft = _ensureDraft(domainId);
        var show = draft.focused || (draft.search || '').length > 0;
        if (!show) return '';
        var f = (draft.search || '').toLowerCase().trim();
        var filtered = _users.filter(function (u) {
            if (draft.targets[u.username]) return false; // already chipped
            if (!f) return true;
            return (u.username || '').toLowerCase().indexOf(f) !== -1
                || (u.display_name || '').toLowerCase().indexOf(f) !== -1;
        }).slice(0, 8); // cap so the panel never feels heavy

        if (!filtered.length) {
            var msg = f
                ? 'No users match "' + _esc(draft.search) + '"'
                : 'No more users to add';
            return '<div class="share-typeahead share-typeahead-empty">' +
                       '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>' +
                       '<span>' + msg + '</span>' +
                   '</div>';
        }

        // Clamp activeIdx so it always points to a real row.
        if (draft.activeIdx < 0 || draft.activeIdx >= filtered.length) draft.activeIdx = 0;

        var rows = filtered.map(function (u, i) {
            var existing = existingByUsername[u.username];
            var existingTag = existing
                ? '<span class="share-row-tag ' + (existing.permission === 'write' ? 'write' : 'read') + '" title="Already has ' + _esc(permissionLabel(existing.permission)) + ' access since ' + _esc(_fmtTime(existing.granted_at)) + '">already</span>'
                : '';
            var roleSub = u.role ? ' &middot; ' + _esc(u.role) : '';
            var matchStart = -1;
            if (f) {
                var name = (u.display_name || u.username || '').toLowerCase();
                matchStart = name.indexOf(f);
            }
            // Highlight the matched substring inside the display name for a
            // subtle "I see what you typed" cue.
            var displayName = u.display_name || u.username;
            var nameHtml;
            if (matchStart >= 0 && f) {
                nameHtml = _esc(displayName.slice(0, matchStart))
                    + '<mark>' + _esc(displayName.slice(matchStart, matchStart + f.length)) + '</mark>'
                    + _esc(displayName.slice(matchStart + f.length));
            } else {
                nameHtml = _esc(displayName);
            }
            return '<div class="share-typeahead-row' + (i === draft.activeIdx ? ' active' : '') + '" data-action="add-chip" data-username="' + _esc(u.username) + '" data-idx="' + i + '">' +
                _cloudAvatar(u.username, 26) +
                '<span class="share-typeahead-name">' + nameHtml + '</span>' +
                '<span class="share-typeahead-meta">@' + _esc(u.username) + roleSub + '</span>' +
                existingTag +
            '</div>';
        }).join('');
        return '<div class="share-typeahead">' + rows + '</div>';
    }

    function _renderShareSubmit(domainId) {
        var draft = _ensureDraft(domainId);
        var picks = Object.keys(draft.targets);
        var label;
        if (picks.length === 0) label = 'Share';
        else if (picks.length === 1) label = 'Send to 1 person';
        else label = 'Send to ' + picks.length + ' people';
        return '<button class="share-btn-primary" data-action="submit-share"' + (picks.length === 0 ? ' disabled' : '') + '>' +
                '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>' +
                '<span>' + label + '</span>' +
            '</button>';
    }

    // ----------------------------------------------------------------
    // Per-file share form (mirrors the per-domain one but scoped to a
    // single topology). Same chip-input UX, separate draft state so
    // selections in one file don't leak into another.
    // ----------------------------------------------------------------
    function _renderTopologyShareForm(d, t, recipients) {
        var draft = _ensureTopoDraft(d.id, t.id);
        var existingByUsername = {};
        recipients.forEach(function (r) { existingByUsername[r.username] = r; });

        var picks = Object.keys(draft.targets);
        var label = recipients.length > 0 ? 'Add more people to this file' : 'Share this file with someone';
        // User-facing label (View / Edit) -- wire tokens stay read/write.
        var permLabel = permissionLabel(draft.perm) || 'View';

        var html = '<div class="share-form share-form-typeahead share-form-topo" ' +
                       'data-domain-id="' + _esc(d.id) + '" data-topology-id="' + _esc(t.id) + '">';
        html +=
            '<div class="share-form-row">' +
                '<div class="share-detail-label share-form-label">' + label + '</div>' +
                '<div class="share-perm-mini" data-action="toggle-perm-topo" ' +
                    'data-domain-id="' + _esc(d.id) + '" data-topology-id="' + _esc(t.id) + '" ' +
                    'data-perm="' + _esc(draft.perm) + '" title="Click to switch permission">' +
                    '<span class="share-perm-mini-dot ' + (draft.perm === 'write' ? 'write' : 'read') + '"></span>' +
                    '<span class="share-perm-mini-label">' + _esc(permLabel) + '</span>' +
                    SVG.chev +
                '</div>' +
            '</div>';

        html += '<div class="share-chip-input' + (draft.focused ? ' is-focused' : '') + '" ' +
                'data-action="focus-input-topo" ' +
                'data-domain-id="' + _esc(d.id) + '" data-topology-id="' + _esc(t.id) + '">';
        picks.forEach(function (username) {
            var u = _users.find(function (x) { return x.username === username; }) || { username: username, display_name: username };
            html +=
                '<span class="share-chip" data-username="' + _esc(username) + '">' +
                    _cloudAvatar(u.username, 20, 'share-chip-avatar') +
                    '<span class="share-chip-name">' + _esc(u.display_name || u.username) + '</span>' +
                    '<button type="button" class="share-chip-remove" data-action="remove-chip-topo" ' +
                        'data-domain-id="' + _esc(d.id) + '" data-topology-id="' + _esc(t.id) + '" ' +
                        'data-username="' + _esc(username) + '" title="Remove" tabindex="-1">' + SVG.x + '</button>' +
                '</span>';
        });
        var placeholder = picks.length === 0 ? 'Type a name or username...' : 'Add another...';
        html +=
            '<input type="text" class="share-chip-text-topo" placeholder="' + placeholder + '" ' +
                'value="' + _esc(draft.search) + '" autocomplete="off" spellcheck="false" ' +
                'data-domain-id="' + _esc(d.id) + '" data-topology-id="' + _esc(t.id) + '" />';
        html += '</div>';

        html += '<div class="share-typeahead-wrap-topo">' + _renderTopologyTypeahead(d, t, existingByUsername) + '</div>';

        html +=
            '<div class="share-form-footer">' +
                '<div class="share-form-hint">' +
                    (picks.length === 0
                        ? 'Sharing only this file -- the rest of the domain stays private'
                        : (picks.length + ' selected')) +
                '</div>' +
                _renderTopologyShareSubmit(d, t) +
            '</div>';
        html += '</div>';
        return html;
    }

    function _renderTopologyTypeahead(d, t, existingByUsername) {
        var draft = _ensureTopoDraft(d.id, t.id);
        var show = draft.focused || (draft.search || '').length > 0;
        if (!show) return '';
        var f = (draft.search || '').toLowerCase().trim();
        var filtered = _users.filter(function (u) {
            if (draft.targets[u.username]) return false;
            if (!f) return true;
            return (u.username || '').toLowerCase().indexOf(f) !== -1
                || (u.display_name || '').toLowerCase().indexOf(f) !== -1;
        }).slice(0, 8);

        if (!filtered.length) {
            var msg = f
                ? 'No users match "' + _esc(draft.search) + '"'
                : 'No more users to add';
            return '<div class="share-typeahead share-typeahead-empty">' +
                       '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>' +
                       '<span>' + msg + '</span>' +
                   '</div>';
        }
        if (draft.activeIdx < 0 || draft.activeIdx >= filtered.length) draft.activeIdx = 0;

        var rows = filtered.map(function (u, i) {
            var existing = existingByUsername[u.username];
            var existingTag = existing
                ? '<span class="share-row-tag ' + (existing.permission === 'write' ? 'write' : 'read') + '" title="Already has ' + _esc(permissionLabel(existing.permission)) + ' access">already</span>'
                : '';
            var roleSub = u.role ? ' &middot; ' + _esc(u.role) : '';
            var matchStart = -1;
            if (f) {
                var name = (u.display_name || u.username || '').toLowerCase();
                matchStart = name.indexOf(f);
            }
            var displayName = u.display_name || u.username;
            var nameHtml;
            if (matchStart >= 0 && f) {
                nameHtml = _esc(displayName.slice(0, matchStart))
                    + '<mark>' + _esc(displayName.slice(matchStart, matchStart + f.length)) + '</mark>'
                    + _esc(displayName.slice(matchStart + f.length));
            } else {
                nameHtml = _esc(displayName);
            }
            return '<div class="share-typeahead-row' + (i === draft.activeIdx ? ' active' : '') + '" ' +
                       'data-action="add-chip-topo" ' +
                       'data-domain-id="' + _esc(d.id) + '" data-topology-id="' + _esc(t.id) + '" ' +
                       'data-username="' + _esc(u.username) + '" data-idx="' + i + '">' +
                _cloudAvatar(u.username, 26) +
                '<span class="share-typeahead-name">' + nameHtml + '</span>' +
                '<span class="share-typeahead-meta">@' + _esc(u.username) + roleSub + '</span>' +
                existingTag +
            '</div>';
        }).join('');
        return '<div class="share-typeahead">' + rows + '</div>';
    }

    function _renderTopologyShareSubmit(d, t) {
        var draft = _ensureTopoDraft(d.id, t.id);
        var picks = Object.keys(draft.targets);
        var label;
        if (picks.length === 0) label = 'Share file';
        else if (picks.length === 1) label = 'Share with 1 person';
        else label = 'Share with ' + picks.length + ' people';
        return '<button class="share-btn-primary" data-action="submit-share-topo" ' +
                   'data-domain-id="' + _esc(d.id) + '" data-topology-id="' + _esc(t.id) + '"' +
                   (picks.length === 0 ? ' disabled' : '') + '>' +
                '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>' +
                '<span>' + label + '</span>' +
            '</button>';
    }

    // The legacy "Shared with me" and "Recent activity" sections are no
    // longer rendered -- they duplicated information the topologies
    // dropdown already surfaces (shared domains appear under their own
    // section in the dropdown; activity is ambient context, not a direct
    // action surface). If a future feature needs them, _fetchIncoming /
    // _fetchIncomingFiles / _fetchActivity still populate _incoming,
    // _incomingFiles, _activity so nothing else has to change.

    // ----------------------------------------------------------------
    // Handlers
    // ----------------------------------------------------------------
    function _attachHandlers(body) {
        body.querySelectorAll('[data-action="toggle-domain"]').forEach(function (el) {
            el.addEventListener('click', function () {
                _onToggleDomain(el.closest('[data-domain-id]'));
            });
        });
        body.querySelectorAll('[data-action="set-scope"]').forEach(function (el) {
            el.addEventListener('click', function (e) { e.stopPropagation(); _onSetScope(el); });
        });
        body.querySelectorAll('[data-action="toggle-topology"]').forEach(function (el) {
            el.addEventListener('click', function () {
                _onToggleTopology(el.closest('[data-topology-id]'));
            });
        });
        body.querySelectorAll('[data-action="create-domain"]').forEach(function (el) {
            el.addEventListener('click', _onCreateDomainClick);
        });

        // Domain-level chip input
        body.querySelectorAll('[data-action="focus-input"]').forEach(function (el) {
            el.addEventListener('mousedown', function (e) {
                if (e.target.closest('[data-action="remove-chip"]')) return;
                if (e.target.tagName === 'INPUT') return;
                e.preventDefault();
                var inp = el.querySelector('.share-chip-text');
                if (inp) inp.focus();
            });
        });
        body.querySelectorAll('.share-chip-text').forEach(function (el) {
            el.addEventListener('input', function () { _onChipInput(el); });
            el.addEventListener('focus', function () { _onChipFocus(el, true); });
            el.addEventListener('blur', function () { _onChipFocus(el, false); });
            el.addEventListener('keydown', function (e) { _onChipKeydown(el, e); });
            el.addEventListener('click', function (e) { e.stopPropagation(); });
        });
        body.querySelectorAll('[data-action="add-chip"]').forEach(function (el) {
            el.addEventListener('mousedown', function (e) { e.preventDefault(); _onAddChip(el); });
        });
        body.querySelectorAll('[data-action="remove-chip"]').forEach(function (el) {
            el.addEventListener('click', function (e) { e.stopPropagation(); _onRemoveChip(el); });
        });
        body.querySelectorAll('[data-action="toggle-perm"]').forEach(function (el) {
            el.addEventListener('click', function (e) { e.stopPropagation(); _onTogglePerm(el); });
        });

        body.querySelectorAll('[data-action="submit-share"]').forEach(function (el) {
            el.addEventListener('click', function (e) { e.stopPropagation(); _onSubmitShareClick(el); });
        });
        body.querySelectorAll('[data-action="revoke"]').forEach(function (el) {
            el.addEventListener('click', function (e) { e.stopPropagation(); _onRevokeClick(el); });
        });
        body.querySelectorAll('[data-action="perm-toggle"]').forEach(function (el) {
            el.addEventListener('click', function (e) { e.stopPropagation(); _onPermChangeClick(el); });
        });

        // Topology-level (per-file) chip input + actions -- mirrors the
        // domain-level wiring above, just routed to the per-file handlers.
        body.querySelectorAll('[data-action="focus-input-topo"]').forEach(function (el) {
            el.addEventListener('mousedown', function (e) {
                if (e.target.closest('[data-action="remove-chip-topo"]')) return;
                if (e.target.tagName === 'INPUT') return;
                e.preventDefault();
                var inp = el.querySelector('.share-chip-text-topo');
                if (inp) inp.focus();
            });
        });
        body.querySelectorAll('.share-chip-text-topo').forEach(function (el) {
            el.addEventListener('input', function () { _onTopoChipInput(el); });
            el.addEventListener('focus', function () { _onTopoChipFocus(el, true); });
            el.addEventListener('blur', function () { _onTopoChipFocus(el, false); });
            el.addEventListener('keydown', function (e) { _onTopoChipKeydown(el, e); });
            el.addEventListener('click', function (e) { e.stopPropagation(); });
        });
        body.querySelectorAll('[data-action="add-chip-topo"]').forEach(function (el) {
            el.addEventListener('mousedown', function (e) { e.preventDefault(); _onTopoAddChip(el); });
        });
        body.querySelectorAll('[data-action="remove-chip-topo"]').forEach(function (el) {
            el.addEventListener('click', function (e) { e.stopPropagation(); _onTopoRemoveChip(el); });
        });
        body.querySelectorAll('[data-action="toggle-perm-topo"]').forEach(function (el) {
            el.addEventListener('click', function (e) { e.stopPropagation(); _onTopoTogglePerm(el); });
        });
        body.querySelectorAll('[data-action="submit-share-topo"]').forEach(function (el) {
            el.addEventListener('click', function (e) { e.stopPropagation(); _onTopoSubmitShareClick(el); });
        });
        body.querySelectorAll('[data-action="revoke-topo"]').forEach(function (el) {
            el.addEventListener('click', function (e) { e.stopPropagation(); _onTopoRevokeClick(el); });
        });
        body.querySelectorAll('[data-action="perm-toggle-topo"]').forEach(function (el) {
            el.addEventListener('click', function (e) { e.stopPropagation(); _onTopoPermChangeClick(el); });
        });

        body.querySelectorAll('[data-action="open-incoming"]').forEach(function (el) {
            el.addEventListener('click', function () { _onOpenIncoming(el); });
        });
        body.querySelectorAll('[data-action="open-incoming-file"]').forEach(function (el) {
            el.addEventListener('click', function () { _onOpenIncomingFile(el); });
        });
    }

    // Accordion: expanding one collapses the others. Full re-render is fine
    // here because the expanded-row content (recipients + form) only exists
    // when expanded, so we need to add/remove those nodes.
    function _onToggleDomain(item) {
        var id = item.getAttribute('data-domain-id');
        var was = !!_expandedDomains[id];
        _expandedDomains = {};
        if (!was) _expandedDomains[id] = true;
        _renderBody();
    }

    // ----------------------------------------------------------------
    // Chip-input typeahead -- focused, autocomplete-style sharing
    // ----------------------------------------------------------------
    // Targeted re-render of the typeahead ONLY (the chip input itself stays
    // in-place so focus and caret are preserved while typing).
    function _onChipInput(input) {
        var item = input.closest('[data-domain-id]');
        var id = item.getAttribute('data-domain-id');
        var draft = _ensureDraft(id);
        draft.search = input.value;
        draft.activeIdx = 0;
        _refreshTypeahead(item);
    }

    function _onChipFocus(input, focused) {
        var item = input.closest('[data-domain-id]');
        var id = item.getAttribute('data-domain-id');
        var draft = _ensureDraft(id);
        if (focused) {
            draft.focused = true;
            var wrap = item.querySelector('.share-chip-input');
            if (wrap) wrap.classList.add('is-focused');
            _refreshTypeahead(item);
        } else {
            // Defer the close by one tick so a click on a suggestion (which
            // fires *after* blur) can still be picked up by the mousedown
            // handler before the panel disappears.
            setTimeout(function () {
                if (document.activeElement === input) return;
                draft.focused = false;
                var wrap = item.querySelector('.share-chip-input');
                if (wrap) wrap.classList.remove('is-focused');
                _refreshTypeahead(item);
            }, 120);
        }
    }

    // Keyboard navigation:
    //   ArrowDown / ArrowUp -- move active suggestion (visual highlight)
    //   Enter               -- add the active suggestion as a chip
    //   Escape              -- close typeahead, blur the input
    //   Backspace (empty)   -- remove the last chip
    //   Tab                 -- accept active suggestion if dropdown is showing
    function _onChipKeydown(input, event) {
        var item = input.closest('[data-domain-id]');
        var id = item.getAttribute('data-domain-id');
        var draft = _ensureDraft(id);
        var typeahead = item.querySelector('.share-typeahead');
        var rows = typeahead ? typeahead.querySelectorAll('[data-action="add-chip"]') : [];

        if (event.key === 'ArrowDown') {
            if (!rows.length) return;
            event.preventDefault();
            draft.activeIdx = Math.min(rows.length - 1, (draft.activeIdx < 0 ? 0 : draft.activeIdx + 1));
            _highlightActive(item);
        } else if (event.key === 'ArrowUp') {
            if (!rows.length) return;
            event.preventDefault();
            draft.activeIdx = Math.max(0, draft.activeIdx - 1);
            _highlightActive(item);
        } else if (event.key === 'Enter') {
            if (!rows.length || draft.activeIdx < 0) return;
            event.preventDefault();
            var row = rows[draft.activeIdx];
            if (row) _onAddChip(row);
        } else if (event.key === 'Escape') {
            event.preventDefault();
            input.blur();
        } else if (event.key === 'Backspace' && !input.value) {
            // Remove the last chip when the input is already empty.
            var picks = Object.keys(draft.targets);
            if (picks.length > 0) {
                event.preventDefault();
                delete draft.targets[picks[picks.length - 1]];
                _refreshChipInput(item);
            }
        } else if (event.key === 'Tab' && rows.length && draft.activeIdx >= 0) {
            event.preventDefault();
            var rowT = rows[draft.activeIdx];
            if (rowT) _onAddChip(rowT);
        }
    }

    function _onAddChip(row) {
        var item = row.closest('[data-domain-id]');
        var id = item.getAttribute('data-domain-id');
        var username = row.getAttribute('data-username');
        var draft = _ensureDraft(id);
        if (draft.targets[username]) return;
        draft.targets[username] = true;
        draft.search = '';
        draft.activeIdx = 0;
        _refreshChipInput(item, /* keepFocus */ true);
    }

    function _onRemoveChip(btn) {
        var item = btn.closest('[data-domain-id]');
        var id = item.getAttribute('data-domain-id');
        var username = btn.getAttribute('data-username');
        var draft = _ensureDraft(id);
        if (!draft.targets[username]) return;
        delete draft.targets[username];
        _refreshChipInput(item, /* keepFocus */ true);
    }

    function _onTogglePerm(badge) {
        var item = badge.closest('[data-domain-id]');
        var id = item.getAttribute('data-domain-id');
        var draft = _ensureDraft(id);
        draft.perm = (draft.perm === 'read') ? 'write' : 'read';
        // Update the visual badge in-place (no full re-render needed).
        badge.setAttribute('data-perm', draft.perm);
        var dot = badge.querySelector('.share-perm-mini-dot');
        if (dot) {
            dot.classList.toggle('write', draft.perm === 'write');
            dot.classList.toggle('read', draft.perm === 'read');
        }
        var lbl = badge.querySelector('.share-perm-mini-label');
        if (lbl) lbl.textContent = permissionLabel(draft.perm) || 'View';
    }

    // Re-render the chip input + typeahead together (e.g. after a chip add
    // or remove). Restores focus/caret to the input so typing flow is
    // uninterrupted. We only swap the inner HTML of .share-form so the
    // surrounding accordion / scroll position is preserved.
    function _refreshChipInput(item, keepFocus) {
        var id = item.getAttribute('data-domain-id');
        var meta = _outgoing.find(function (x) { return x.domain_id === id; });
        var recipients = (meta && meta.recipients) || [];
        var domain = _ownDomains().find(function (x) { return x.id === id; });
        if (!domain) return;
        var formEl = item.querySelector('.share-form');
        if (!formEl) return;
        var newFormHTML = _renderShareForm(domain, recipients);
        // Replace the form content; re-attach handlers scoped to the form.
        var tmp = document.createElement('div');
        tmp.innerHTML = newFormHTML;
        var newForm = tmp.firstChild;
        formEl.parentNode.replaceChild(newForm, formEl);
        _attachHandlers(newForm);
        if (keepFocus) {
            var inp = newForm.querySelector('.share-chip-text');
            if (inp) {
                inp.focus();
                // Place caret at end.
                var v = inp.value; inp.value = ''; inp.value = v;
            }
        }
    }

    // Re-render only the typeahead panel (when typing). Input stays mounted
    // so caret + selection are preserved character-by-character.
    function _refreshTypeahead(item) {
        var id = item.getAttribute('data-domain-id');
        var meta = _outgoing.find(function (x) { return x.domain_id === id; });
        var existingByUsername = {};
        if (meta && meta.recipients) meta.recipients.forEach(function (r) { existingByUsername[r.username] = r; });
        var wrap = item.querySelector('.share-typeahead-wrap');
        if (!wrap) return;
        wrap.innerHTML = _renderTypeahead(id, existingByUsername);
        wrap.querySelectorAll('[data-action="add-chip"]').forEach(function (el) {
            el.addEventListener('mousedown', function (e) { e.preventDefault(); _onAddChip(el); });
        });
        // Update footer hint count + submit button without a full form rebuild.
        _updateShareFooter(item);
    }

    function _highlightActive(item) {
        var typeahead = item.querySelector('.share-typeahead');
        if (!typeahead) return;
        var id = item.getAttribute('data-domain-id');
        var idx = _ensureDraft(id).activeIdx;
        var rows = typeahead.querySelectorAll('[data-action="add-chip"]');
        rows.forEach(function (r, i) {
            r.classList.toggle('active', i === idx);
            if (i === idx && r.scrollIntoView) {
                r.scrollIntoView({ block: 'nearest' });
            }
        });
    }

    function _updateShareFooter(item) {
        var id = item.getAttribute('data-domain-id');
        var draft = _ensureDraft(id);
        var picks = Object.keys(draft.targets);
        var hint = item.querySelector('.share-form-hint');
        if (hint) {
            hint.textContent = picks.length === 0
                ? 'Tip: arrow keys to navigate, enter to add, backspace to remove'
                : (picks.length + ' selected');
        }
        var btn = item.querySelector('[data-action="submit-share"] span');
        var btnEl = item.querySelector('[data-action="submit-share"]');
        if (btnEl) btnEl.disabled = picks.length === 0;
        if (btn) {
            if (picks.length === 0) btn.textContent = 'Share';
            else if (picks.length === 1) btn.textContent = 'Send to 1 person';
            else btn.textContent = 'Send to ' + picks.length + ' people';
        }
    }

    async function _onSubmitShareClick(btn) {
        var item = btn.closest('[data-domain-id]');
        var id = item.getAttribute('data-domain-id');
        var draft = _ensureDraft(id);
        var picks = Object.keys(draft.targets);
        if (!picks.length) return;
        btn.disabled = true;
        var span = btn.querySelector('span');
        if (span) span.textContent = 'Sharing...';
        else btn.textContent = 'Sharing...';
        try {
            await window.TopologyDomains.shareDomain(id, picks, draft.perm);
            _inlineDirty = true;
            _shareDrafts[id] = { targets: {}, perm: 'read', search: '', activeIdx: -1, focused: false };
            await _refreshAll();
            _renderBody();
            _toast(
                picks.length === 1
                    ? 'Shared with ' + picks[0]
                    : 'Shared with ' + picks.length + ' people',
                'info'
            );
        } catch (err) {
            alert('Share failed: ' + (err && err.message ? err.message : err));
            btn.disabled = false;
            _updateShareFooter(item);
        }
    }

    async function _onRevokeClick(btn) {
        var item = btn.closest('[data-domain-id]');
        var id = item.getAttribute('data-domain-id');
        var username = btn.getAttribute('data-target');
        if (!confirm('Revoke ' + username + '\'s access?')) return;
        btn.disabled = true;
        try {
            await window.TopologyDomains.unshareDomain(id, username);
            _inlineDirty = true;
            await _refreshAll();
            _renderBody();
            _toast('Stopped sharing with ' + username, 'info');
        } catch (err) {
            alert('Failed: ' + (err && err.message ? err.message : err));
            btn.disabled = false;
        }
    }

    async function _onPermChangeClick(btn) {
        var item = btn.closest('[data-domain-id]');
        var id = item.getAttribute('data-domain-id');
        var username = btn.getAttribute('data-target');
        var currentPerm = btn.getAttribute('data-current-perm');
        var newPerm = (currentPerm === 'read') ? 'write' : 'read';
        btn.disabled = true;
        try {
            await window.TopologyDomains.shareDomain(id, [username], newPerm);
            _inlineDirty = true;
            await _refreshAll();
            _renderBody();
            _toast(username + ' now has ' + permissionVerb(newPerm) + ' access', 'info');
        } catch (err) {
            alert('Failed: ' + (err && err.message ? err.message : err));
            btn.disabled = false;
        }
    }

    function _onOpenIncoming(row) {
        var compositeId = row.getAttribute('data-domain');
        if (window.TopologyDomains && window.TopologyDomains.selectDomain) {
            window.TopologyDomains.selectDomain(compositeId);
        }
        closeDialog();
    }

    // Per-file deep link: jump to the synthetic "Shared with me" domain and
    // (best-effort) load the composite topology so the user lands on the
    // exact file someone shared with them.
    function _onOpenIncomingFile(row) {
        var composite = row.getAttribute('data-composite');
        if (window.TopologyDomains && window.TopologyDomains.selectDomain) {
            window.TopologyDomains.selectDomain(SHARED_WITH_ME_DOMAIN_ID);
        }
        if (window.TopologyDomains && window.TopologyDomains.loadTopology && composite) {
            try { window.TopologyDomains.loadTopology(composite); } catch (e) { /* best-effort */ }
        }
        closeDialog();
    }

    // ----------------------------------------------------------------
    // Scope picker + per-file accordion
    // ----------------------------------------------------------------
    function _onSetScope(btn) {
        var item = btn.closest('[data-domain-id]');
        if (!item) return;
        var id = item.getAttribute('data-domain-id');
        var scope = btn.getAttribute('data-scope');
        var draft = _ensureDraft(id);
        if (draft.scope === scope) return;
        draft.scope = scope;
        // Pre-fetch the topologies for this domain so the user doesn't see
        // the skeleton blip; on the second render cache will be warm.
        if (scope === 'files') {
            _fetchTopologiesForDomain(id).catch(function () {});
        }
        _renderBody();
    }

    function _onToggleTopology(item) {
        if (!item) return;
        var did = item.getAttribute('data-domain-id');
        var tid = item.getAttribute('data-topology-id');
        if (!_expandedTopologies[did]) _expandedTopologies[did] = {};
        var was = !!_expandedTopologies[did][tid];
        // Accordion within a domain: only one file expanded at a time.
        _expandedTopologies[did] = {};
        if (!was) _expandedTopologies[did][tid] = true;
        _renderBody();
    }

    // ----------------------------------------------------------------
    // Per-topology chip-input handlers (mirror the per-domain ones above
    // but route through _ensureTopoDraft and the per-file refresh paths).
    // ----------------------------------------------------------------
    function _onTopoChipInput(input) {
        var did = input.getAttribute('data-domain-id');
        var tid = input.getAttribute('data-topology-id');
        var draft = _ensureTopoDraft(did, tid);
        draft.search = input.value;
        draft.activeIdx = 0;
        _refreshTopoTypeahead(did, tid);
    }

    function _onTopoChipFocus(input, focused) {
        var did = input.getAttribute('data-domain-id');
        var tid = input.getAttribute('data-topology-id');
        var draft = _ensureTopoDraft(did, tid);
        if (focused) {
            draft.focused = true;
            var wrap = _findTopoFormEl(did, tid);
            if (wrap) {
                var chip = wrap.querySelector('.share-chip-input');
                if (chip) chip.classList.add('is-focused');
            }
            _refreshTopoTypeahead(did, tid);
        } else {
            setTimeout(function () {
                if (document.activeElement === input) return;
                draft.focused = false;
                var wrap = _findTopoFormEl(did, tid);
                if (wrap) {
                    var chip = wrap.querySelector('.share-chip-input');
                    if (chip) chip.classList.remove('is-focused');
                }
                _refreshTopoTypeahead(did, tid);
            }, 90);
        }
    }

    function _onTopoChipKeydown(input, event) {
        var did = input.getAttribute('data-domain-id');
        var tid = input.getAttribute('data-topology-id');
        var draft = _ensureTopoDraft(did, tid);
        var formEl = _findTopoFormEl(did, tid);
        var typeahead = formEl ? formEl.querySelector('.share-typeahead') : null;
        var rows = typeahead ? typeahead.querySelectorAll('[data-action="add-chip-topo"]') : [];

        if (event.key === 'ArrowDown') {
            if (!rows.length) return;
            event.preventDefault();
            draft.activeIdx = Math.min(rows.length - 1, (draft.activeIdx < 0 ? 0 : draft.activeIdx + 1));
            _highlightTopoActive(did, tid);
        } else if (event.key === 'ArrowUp') {
            if (!rows.length) return;
            event.preventDefault();
            draft.activeIdx = Math.max(0, draft.activeIdx - 1);
            _highlightTopoActive(did, tid);
        } else if (event.key === 'Enter') {
            if (!rows.length || draft.activeIdx < 0) return;
            event.preventDefault();
            var row = rows[draft.activeIdx];
            if (row) _onTopoAddChip(row);
        } else if (event.key === 'Escape') {
            event.preventDefault();
            input.blur();
        } else if (event.key === 'Backspace' && !input.value) {
            var picks = Object.keys(draft.targets);
            if (picks.length > 0) {
                event.preventDefault();
                delete draft.targets[picks[picks.length - 1]];
                _refreshTopoChipInput(did, tid, /* keepFocus */ true);
            }
        } else if (event.key === 'Tab' && rows.length && draft.activeIdx >= 0) {
            event.preventDefault();
            var rowT = rows[draft.activeIdx];
            if (rowT) _onTopoAddChip(rowT);
        }
    }

    function _onTopoAddChip(row) {
        var did = row.getAttribute('data-domain-id');
        var tid = row.getAttribute('data-topology-id');
        var username = row.getAttribute('data-username');
        var draft = _ensureTopoDraft(did, tid);
        if (draft.targets[username]) return;
        draft.targets[username] = true;
        draft.search = '';
        draft.activeIdx = 0;
        _refreshTopoChipInput(did, tid, /* keepFocus */ true);
    }

    function _onTopoRemoveChip(btn) {
        var did = btn.getAttribute('data-domain-id');
        var tid = btn.getAttribute('data-topology-id');
        var username = btn.getAttribute('data-username');
        var draft = _ensureTopoDraft(did, tid);
        if (!draft.targets[username]) return;
        delete draft.targets[username];
        _refreshTopoChipInput(did, tid, /* keepFocus */ true);
    }

    function _onTopoTogglePerm(badge) {
        var did = badge.getAttribute('data-domain-id');
        var tid = badge.getAttribute('data-topology-id');
        var draft = _ensureTopoDraft(did, tid);
        draft.perm = (draft.perm === 'read') ? 'write' : 'read';
        badge.setAttribute('data-perm', draft.perm);
        var dot = badge.querySelector('.share-perm-mini-dot');
        if (dot) {
            dot.classList.toggle('write', draft.perm === 'write');
            dot.classList.toggle('read', draft.perm === 'read');
        }
        var lbl = badge.querySelector('.share-perm-mini-label');
        if (lbl) lbl.textContent = permissionLabel(draft.perm) || 'View';
    }

    function _findTopoFormEl(did, tid) {
        return document.querySelector(
            '.share-form-topo[data-domain-id="' + did + '"][data-topology-id="' + tid + '"]'
        );
    }

    function _refreshTopoChipInput(did, tid, keepFocus) {
        var formEl = _findTopoFormEl(did, tid);
        if (!formEl) return;
        var meta = _outgoingFiles.find(function (f) {
            return f.domain_id === did && f.topology_id === tid;
        });
        var recipients = (meta && meta.recipients) || [];
        var domain = _ownDomains().find(function (x) { return x.id === did; });
        var topo = (_domainTopologyCache[did] || []).find(function (t) { return t.id === tid; })
                  || { id: tid, name: tid };
        if (!domain) return;
        var newFormHTML = _renderTopologyShareForm(domain, topo, recipients);
        var tmp = document.createElement('div');
        tmp.innerHTML = newFormHTML;
        var newForm = tmp.firstChild;
        formEl.parentNode.replaceChild(newForm, formEl);
        _attachHandlers(newForm);
        if (keepFocus) {
            var inp = newForm.querySelector('.share-chip-text-topo');
            if (inp) {
                inp.focus();
                var v = inp.value; inp.value = ''; inp.value = v;
            }
        }
    }

    function _refreshTopoTypeahead(did, tid) {
        var formEl = _findTopoFormEl(did, tid);
        if (!formEl) return;
        var meta = _outgoingFiles.find(function (f) {
            return f.domain_id === did && f.topology_id === tid;
        });
        var existingByUsername = {};
        if (meta && meta.recipients) meta.recipients.forEach(function (r) { existingByUsername[r.username] = r; });
        var domain = _ownDomains().find(function (x) { return x.id === did; });
        var topo = (_domainTopologyCache[did] || []).find(function (t) { return t.id === tid; })
                  || { id: tid, name: tid };
        if (!domain) return;
        var wrap = formEl.querySelector('.share-typeahead-wrap-topo');
        if (!wrap) return;
        wrap.innerHTML = _renderTopologyTypeahead(domain, topo, existingByUsername);
        wrap.querySelectorAll('[data-action="add-chip-topo"]').forEach(function (el) {
            el.addEventListener('mousedown', function (e) { e.preventDefault(); _onTopoAddChip(el); });
        });
        _updateTopoShareFooter(did, tid);
    }

    function _highlightTopoActive(did, tid) {
        var formEl = _findTopoFormEl(did, tid);
        if (!formEl) return;
        var idx = _ensureTopoDraft(did, tid).activeIdx;
        var rows = formEl.querySelectorAll('[data-action="add-chip-topo"]');
        rows.forEach(function (r, i) {
            r.classList.toggle('active', i === idx);
            if (i === idx && r.scrollIntoView) r.scrollIntoView({ block: 'nearest' });
        });
    }

    function _updateTopoShareFooter(did, tid) {
        var formEl = _findTopoFormEl(did, tid);
        if (!formEl) return;
        var draft = _ensureTopoDraft(did, tid);
        var picks = Object.keys(draft.targets);
        var hint = formEl.querySelector('.share-form-hint');
        if (hint) {
            hint.textContent = picks.length === 0
                ? 'Sharing only this file -- the rest of the domain stays private'
                : (picks.length + ' selected');
        }
        var btnEl = formEl.querySelector('[data-action="submit-share-topo"]');
        var btn = btnEl ? btnEl.querySelector('span') : null;
        if (btnEl) btnEl.disabled = picks.length === 0;
        if (btn) {
            if (picks.length === 0) btn.textContent = 'Share file';
            else if (picks.length === 1) btn.textContent = 'Share with 1 person';
            else btn.textContent = 'Share with ' + picks.length + ' people';
        }
    }

    async function _onTopoSubmitShareClick(btn) {
        var did = btn.getAttribute('data-domain-id');
        var tid = btn.getAttribute('data-topology-id');
        var draft = _ensureTopoDraft(did, tid);
        var picks = Object.keys(draft.targets);
        if (!picks.length) return;
        if (!window.TopologyDomains || !window.TopologyDomains.shareTopology) {
            alert('Per-file sharing requires a newer backend version.');
            return;
        }
        btn.disabled = true;
        var span = btn.querySelector('span');
        if (span) span.textContent = 'Sharing...';
        else btn.textContent = 'Sharing...';
        try {
            await window.TopologyDomains.shareTopology(did, tid, picks, draft.perm);
            _inlineDirty = true;
            _topologyDrafts[_topoKey(did, tid)] = {
                targets: {}, perm: 'read', search: '', activeIdx: -1, focused: false
            };
            await _refreshAll();
            _renderBody();
            _toast(
                picks.length === 1
                    ? 'Shared file with ' + picks[0]
                    : 'Shared file with ' + picks.length + ' people',
                'info'
            );
        } catch (err) {
            alert('Share failed: ' + (err && err.message ? err.message : err));
            btn.disabled = false;
            _updateTopoShareFooter(did, tid);
        }
    }

    async function _onTopoRevokeClick(btn) {
        var did = btn.getAttribute('data-domain-id');
        var tid = btn.getAttribute('data-topology-id');
        var username = btn.getAttribute('data-target');
        if (!confirm('Revoke ' + username + '\'s access to this file?')) return;
        if (!window.TopologyDomains || !window.TopologyDomains.unshareTopology) {
            alert('Per-file sharing requires a newer backend version.');
            return;
        }
        btn.disabled = true;
        try {
            await window.TopologyDomains.unshareTopology(did, tid, username);
            _inlineDirty = true;
            await _refreshAll();
            _renderBody();
            _toast('Stopped sharing file with ' + username, 'info');
        } catch (err) {
            alert('Failed: ' + (err && err.message ? err.message : err));
            btn.disabled = false;
        }
    }

    async function _onTopoPermChangeClick(btn) {
        var did = btn.getAttribute('data-domain-id');
        var tid = btn.getAttribute('data-topology-id');
        var username = btn.getAttribute('data-target');
        var currentPerm = btn.getAttribute('data-current-perm');
        var newPerm = (currentPerm === 'read') ? 'write' : 'read';
        if (!window.TopologyDomains || !window.TopologyDomains.shareTopology) {
            alert('Per-file sharing requires a newer backend version.');
            return;
        }
        btn.disabled = true;
        try {
            await window.TopologyDomains.shareTopology(did, tid, [username], newPerm);
            _inlineDirty = true;
            await _refreshAll();
            _renderBody();
            _toast(username + ' now has ' + permissionVerb(newPerm) + ' access to this file', 'info');
        } catch (err) {
            alert('Failed: ' + (err && err.message ? err.message : err));
            btn.disabled = false;
        }
    }

    async function _onCreateDomainClick() {
        var name = window.prompt('New domain name:');
        if (!name) return;
        name = name.trim();
        if (!name) return;
        var description = window.prompt('Description (optional):') || '';
        try {
            var d = await _createDomain(name, description.trim());
            await _refreshAll();
            if (d && d.id) {
                _expandedDomains = {};
                _expandedDomains[d.id] = true;
            }
            _renderBody();
        } catch (err) {
            alert('Could not create domain: ' + (err && err.message ? err.message : err));
        }
    }

    // ----------------------------------------------------------------
    // Init
    // ----------------------------------------------------------------
    async function init() {
        _overview = await _fetchOverview();
        _renderToolbar();
    }

    document.addEventListener('topology-domains:changed', _renderToolbar);

    // Live-refresh the OPEN share dialog when a share-family WS event
    // arrives so:
    //   - chip list updates when a peer grants themselves access via
    //     another tab
    //   - revoked chip disappears without the user having to close +
    //     reopen the form
    //   - the recipient whose access was revoked gets a toast (handled
    //     in topology-sync.js); the owner still sees their chip row
    //     evaporate here.
    // Debounced so a bulk share of many users produces one re-render.
    var _wsShareTimer = null;
    function _scheduleDialogRefresh() {
        if (_wsShareTimer) return;
        _wsShareTimer = setTimeout(function () {
            _wsShareTimer = null;
            if (!_activeInline) return;
            _refreshAll().then(function () {
                _refreshInlineForm();
            }).catch(function () { /* swallow */ });
        }, 200);
    }
    function _onShareWsEvent(ev) {
        var env = (ev && ev.detail) || {};
        var t = (env && env.event_type) || '';
        if (t === 'topology.shared' ||
            t === 'topology.unshared' ||
            t === 'topology.permission_changed' ||
            t === 'domain.shared' ||
            t === 'domain.unshared') {
            _scheduleDialogRefresh();
        }
    }
    try {
        window.addEventListener('topology:event:topology_event', _onShareWsEvent);
        window.addEventListener('topology:event:share_domain', _onShareWsEvent);
    } catch (_) { /* swallow */ }

    document.addEventListener('DOMContentLoaded', function () {
        if (_currentUser()) init();
        else _renderToolbar();
    });

    window.TopologyShare = {
        init: init,
        open: openDialog,
        openForDomain: openForDomain,
        close: closeDialog,
        refresh: _refreshAll,
        // Permission label translation helpers. Frontend-only rename
        // of wire tokens read/write -> View/Edit. See
        // DEVELOPMENT_GUIDELINES.md -> "Shared Topology Permissions --
        // View / Edit -- 2026-05-12".
        permissionLabel: permissionLabel,
        permissionTitle: permissionTitle,
        permissionVerb: permissionVerb
    };
})();
