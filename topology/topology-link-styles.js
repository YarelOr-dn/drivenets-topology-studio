// ============================================================================
// TOPOLOGY LINK STYLES MODULE
// ============================================================================
// Maps link.linkType -> default color + style so protocol-tagged links render
// with industry-standard colors (BGP orange, OSPF green, ISIS purple, MPLS
// red, EVPN teal, ...) without forcing every caller to set link.color.
//
// Why this exists:
//   Before 2026-04-24, the AI assistant (topology-ai.js) would generate
//   links with `linkType: "ebgp"` but no `color`, and topology-link-drawing.js
//   only read `link.color`. Result: every AI-generated protocol topology
//   rendered in the default gray regardless of the stated protocol.
//
// Design rules:
//   * Explicit user/LLM-provided `link.color` ALWAYS wins. We only fall back
//     to a protocol color when the link has NO color OR its color equals the
//     editor's defaultLinkColor (meaning "nobody customised this, use the
//     protocol hint").
//   * All colors picked here are readable on both dark and light canvas
//     themes. adjustColorForMode() in topology-device-styles.js still runs
//     downstream for fine-tuning brightness.
//   * linkType values match the knowledge digest enum (bgp / ibgp / ebgp /
//     ospf / isis / mpls / ldp / sr-mpls / srv6 / evpn / vxlan / pw / vpws /
//     dnaas / bul / lag / default). Unknown values pass through untouched.
//
// Public surface (attached to window.TopologyLinkStyles):
//   colorFor(linkType, darkMode)      -> hex string or null
//   styleFor(linkType)                -> 'solid' | 'dashed' | 'arrow' | ...
//   widthFor(linkType, defaultWidth)  -> number
//   resolveColor(link, editor)        -> hex string (never null)
//   resolveStyle(link)                -> valid style string
//   resolveWidth(link, editor)        -> number
//   TYPE_COLORS                       -> raw table (for palette pickers)
// ============================================================================

(function () {
    'use strict';

    // Protocol -> hex color. Chosen to match Juniper NorthStar / Cisco EPNM
    // conventions where available and to stay visually distinct in both dark
    // and light canvas themes. Aliases (ibgp/ebgp -> bgp variants) keep the
    // knowledge digest vocabulary exact while sharing the same palette entry.
    var TYPE_COLORS = {
        // BGP family
        'bgp':      '#e67e22',   // orange -- generic/external BGP
        'ebgp':     '#e67e22',   // orange (matches NorthStar eBGP maroon spirit but readable on dark)
        'ibgp':     '#3498db',   // blue -- internal BGP logical overlay
        'bgp-lu':   '#d35400',   // dark orange -- labeled unicast
        'bgp-ls':   '#d35400',

        // IGPs
        'ospf':     '#27ae60',   // green
        'ospfv3':   '#27ae60',
        'isis':     '#9b59b6',   // purple
        'is-is':    '#9b59b6',

        // MPLS transport / LSPs
        'mpls':     '#e74c3c',   // red
        'ldp':      '#e74c3c',
        'rsvp':     '#c0392b',   // darker red for RSVP-TE
        'rsvp-te':  '#c0392b',

        // Segment routing
        'sr':       '#c0392b',
        'sr-mpls':  '#c0392b',
        'srv6':     '#a93226',
        'sr-te':    '#c0392b',

        // Overlays / services
        'evpn':     '#1abc9c',   // teal
        'vxlan':    '#8e44ad',   // brown-purple
        'pw':       '#16a085',   // dark teal (pseudowire)
        'vpws':     '#16a085',
        'vpls':     '#16a085',
        'l2vpn':    '#16a085',
        'l3vpn':    '#e74c3c',   // share MPLS palette since L3VPN rides MPLS

        // DriveNets-specific
        'dnaas':    '#00b4d8',   // cyan-teal (matches legacy DNAAS toolbar accent)
        'bul':      null,        // theme default, but width bumped
        'lag':      null,

        // Multicast family -- magenta palette so PIM / IGMP / MVPN / mLDP
        // stand out from the IGP/BGP/MPLS unicast links on the same canvas.
        // All four share the core hue; style differs (see TYPE_STYLES) so the
        // control-plane variant is still visually distinct.
        'multicast': '#ec4899',  // hot pink (generic multicast)
        'pim':       '#ec4899',
        'pim-sm':    '#ec4899',
        'pim-ssm':   '#ec4899',
        'pim-dm':    '#ec4899',
        'pim-bidir': '#ec4899',
        'igmp':      '#f472b6',  // lighter pink -- host<->router membership
        'mvpn':      '#db2777',  // deeper pink -- MVPN overlay on MPLS L3VPN
        'mldp':      '#be185d',  // darker pink -- mLDP P2MP LSP transport
        'p2mp':      '#be185d',

        // QoS -- amber palette so class-aware links / policer/shaper
        // boundaries are distinct from pure unicast.
        'qos':       '#f59e0b',  // amber
        'dscp':      '#f59e0b',
        'cos':       '#f59e0b',
        'policing':  '#d97706',  // darker amber
        'shaping':   '#d97706',
        'hqos':      '#b45309',

        // HA / failover -- emerald palette for redundancy / health-check
        // overlays.
        'vrrp':      '#10b981',  // emerald
        'hsrp':      '#10b981',
        'glbp':      '#10b981',
        'bfd':       '#06b6d4',  // cyan -- health-check ticks
        'ha':        '#10b981',

        // Site-to-site VPN -- indigo for encrypted tunnels
        'vpn':       '#6366f1',  // indigo
        'ipsec':     '#6366f1',
        'ike':       '#6366f1',
        'ikev2':     '#6366f1',
        'esp':       '#4f46e5',
        'gre':       '#818cf8',  // lighter indigo
        'dmvpn':     '#4338ca',  // darker indigo (multipoint)
        'sslvpn':    '#a5b4fc',
        'wireguard': '#818cf8',
        'l2tp':      '#a5b4fc',

        // L2VPN -- dark teal palette (shares with pw/vpws already set
        // above, but with new tokens); solid line differentiates from
        // EVPN overlay.
        'elan':      '#16a085',
        'epl':       '#16a085',
        'evpl':      '#16a085',
        'pseudowire':'#16a085',

        // Spanning-tree / L2 discovery
        'stp':       '#94a3b8',  // slate -- discovery/loop-prevention
        'rstp':      '#94a3b8',
        'mstp':      '#94a3b8',
        'lacp':      '#94a3b8',

        // Security / DDoS mitigation -- red palette
        'flowspec':  '#dc2626',  // red
        'rtbh':      '#991b1b',  // dark red
        'blackhole': '#991b1b',
        'acl':       '#dc2626',
        'firewall':  '#dc2626',
        'rpki':      '#f87171',  // lighter red for policy/validation

        // Broadband / subscriber
        'pppoe':     '#a855f7',  // purple
        'ipoe':      '#a855f7',
        'subscriber':'#a855f7',
        'radius':    '#c084fc',
        'ppp':       '#a855f7',

        // Mobile / xHaul
        'fronthaul': '#ef4444',  // red-orange (latency-sensitive)
        'midhaul':   '#f97316',
        'backhaul':  '#fb923c',
        'ecpri':     '#ef4444',
        'xhaul':     '#f97316',

        // NAT
        'nat':       '#eab308',  // yellow -- address translation boundary
        'cgnat':     '#ca8a04',
        'nat64':     '#eab308',

        // Telemetry -- sky-blue, low emphasis (out-of-band)
        'telemetry': '#38bdf8',
        'gnmi':      '#38bdf8',
        'netconf':   '#38bdf8',
        'snmp':      '#7dd3fc',
        'netflow':   '#7dd3fc',
        'sflow':     '#7dd3fc',

        // Generic / fallback
        'default':  null,
        '':         null
    };

    // Protocol -> default line style. iBGP is a logical overlay (dashed),
    // eBGP carries direction (arrow), EVPN is a widely-spaced dashed overlay,
    // pseudowires are direction-sensitive dashed-arrows, everything else
    // solid. Only applied when the link has NO explicit `style` set.
    var TYPE_STYLES = {
        'ibgp':         'dashed',
        'ebgp':         'arrow',
        'bgp':          'solid',

        'ospf':         'solid',
        'ospfv3':       'solid',
        'isis':         'solid',
        'is-is':        'solid',

        'mpls':         'solid',
        'ldp':          'solid',
        'rsvp':         'solid',
        'rsvp-te':      'solid',

        'sr':           'arrow',
        'sr-mpls':      'arrow',
        'srv6':         'arrow',
        'sr-te':        'arrow',

        'evpn':         'dashed-wide',
        'vxlan':        'dashed',
        'pw':           'dashed-arrow',
        'vpws':         'dashed-arrow',
        'vpls':         'dashed-arrow',
        'l2vpn':        'dashed',
        'l3vpn':        'solid',

        'dnaas':        'solid',
        'bul':          'solid',
        'lag':          'solid',

        // Multicast: PIM is source->RP->receiver directional (arrow),
        // IGMP membership is a dashed-arrow from host to router,
        // MVPN is dashed-wide to mirror its overlay nature (like EVPN),
        // mLDP is arrow (P2MP LSP direction matters).
        'multicast':    'arrow',
        'pim':          'arrow',
        'pim-sm':       'arrow',
        'pim-ssm':      'arrow',
        'pim-dm':       'arrow',
        'pim-bidir':    'dashed-arrow',
        'igmp':         'dashed-arrow',
        'mvpn':         'dashed-wide',
        'mldp':         'arrow',
        'p2mp':         'arrow',

        // QoS boundary markers are solid by default (traffic link with
        // class treatment) -- policer/shaper edges lean dashed to
        // signal "enforcement point" rather than pure data path.
        'qos':          'solid',
        'dscp':         'solid',
        'cos':          'solid',
        'policing':     'dashed',
        'shaping':      'dashed',
        'hqos':         'solid',

        // HA / failover: VRRP / HSRP / GLBP all carry hello arrows;
        // BFD is a short-dashed tick (fast-detection heartbeat).
        'vrrp':         'dashed-arrow',
        'hsrp':         'dashed-arrow',
        'glbp':         'dashed-arrow',
        'bfd':          'dashed',
        'ha':           'dashed',

        // VPN / encrypted tunnels -- dashed-wide reads as "overlay".
        'vpn':          'dashed-wide',
        'ipsec':        'dashed-wide',
        'ike':          'dashed',
        'ikev2':        'dashed',
        'esp':          'dashed-wide',
        'gre':          'dashed',
        'dmvpn':        'dashed-wide',
        'sslvpn':       'dashed-arrow',
        'wireguard':    'dashed-wide',
        'l2tp':         'dashed-arrow',

        // L2VPN: pseudowires are directional (dashed-arrow like
        // existing pw/vpws entry) so the service endpoints are clear.
        'elan':          'dashed',
        'epl':           'dashed-arrow',
        'evpl':          'dashed-arrow',
        'pseudowire':    'dashed-arrow',

        // Spanning-tree: BPDU flows are discovery-style (dashed).
        'stp':          'dashed',
        'rstp':         'dashed',
        'mstp':         'dashed',
        'lacp':         'dashed',

        // Security -- FlowSpec / RTBH are control-plane signalling so
        // they read dashed; ACL / firewall are policy boundaries (solid).
        'flowspec':     'dashed',
        'rtbh':         'dashed',
        'blackhole':    'dashed',
        'acl':          'solid',
        'firewall':     'solid',
        'rpki':         'dashed',

        // Broadband / subscriber
        'pppoe':        'arrow',
        'ipoe':         'solid',
        'subscriber':   'arrow',
        'radius':       'dashed',
        'ppp':          'arrow',

        // Mobile / xHaul -- the data plane is solid; stricter latency
        // budget on fronthaul is signalled via color (red-orange) +
        // width bump via the WIDTHS table below.
        'fronthaul':    'solid',
        'midhaul':      'solid',
        'backhaul':     'solid',
        'ecpri':        'solid',
        'xhaul':        'solid',

        // NAT: boundary link is solid; but NAT event edges read as
        // "transition" so we use arrow.
        'nat':          'arrow',
        'cgnat':        'arrow',
        'nat64':        'arrow',

        // Telemetry -- out-of-band, dashed so it never competes with
        // the data-plane story.
        'telemetry':    'dashed',
        'gnmi':         'dashed-arrow',
        'netconf':      'dashed-arrow',
        'snmp':         'dashed',
        'netflow':      'dashed',
        'sflow':        'dashed',

        'default':      'solid',
        '':             'solid'
    };

    // Protocol -> bandwidth/visual emphasis. BUL/LAG render thicker so they
    // read as bundled; normal links defer to the editor's default width.
    // Fronthaul is drawn thicker too because it carries high-rate eCPRI
    // and readers should immediately see it as "fat pipe".
    var TYPE_WIDTHS = {
        'bul': 4,
        'lag': 4,
        'fronthaul': 3,
        'ecpri': 3,
        'hqos': 3
    };

    function _norm(linkType) {
        if (typeof linkType !== 'string') return '';
        return linkType.trim().toLowerCase();
    }

    function colorFor(linkType, darkMode) {
        var key = _norm(linkType);
        if (!key) return null;
        if (!Object.prototype.hasOwnProperty.call(TYPE_COLORS, key)) return null;
        var val = TYPE_COLORS[key];
        return (typeof val === 'string' && val.length > 0) ? val : null;
    }

    function styleFor(linkType) {
        var key = _norm(linkType);
        if (!key || !Object.prototype.hasOwnProperty.call(TYPE_STYLES, key)) return null;
        return TYPE_STYLES[key] || 'solid';
    }

    function widthFor(linkType, defaultWidth) {
        var key = _norm(linkType);
        if (Object.prototype.hasOwnProperty.call(TYPE_WIDTHS, key)) {
            return TYPE_WIDTHS[key];
        }
        return (typeof defaultWidth === 'number') ? defaultWidth : undefined;
    }

    // Is the provided color "just the editor's default" (i.e. the user never
    // customised it)? We treat case-insensitive hex comparison so "#666666"
    // and "#666" both match, and tolerate the legacy default of '#666'.
    function _isDefaultColor(color, editor) {
        if (typeof color !== 'string' || color.length === 0) return true;
        var c = color.trim().toLowerCase();
        var def = editor && typeof editor.defaultLinkColor === 'string'
            ? editor.defaultLinkColor.trim().toLowerCase()
            : '';
        if (c === def) return true;
        // Expand shorthand #abc -> #aabbcc for comparison symmetry.
        var shortHex = /^#([0-9a-f])([0-9a-f])([0-9a-f])$/i;
        var m = c.match(shortHex);
        if (m) c = '#' + m[1] + m[1] + m[2] + m[2] + m[3] + m[3];
        var m2 = def.match(shortHex);
        if (m2) def = '#' + m2[1] + m2[1] + m2[2] + m2[2] + m2[3] + m2[3];
        return c === def;
    }

    function resolveColor(link, editor) {
        if (!link) return (editor && editor.defaultLinkColor) || '#666666';
        // Explicit non-default user color wins.
        if (typeof link.color === 'string' && link.color.length > 0
                && !_isDefaultColor(link.color, editor)) {
            return link.color;
        }
        // Fall back to protocol color if linkType is recognised.
        var byType = colorFor(link.linkType, editor && editor.darkMode);
        if (byType) return byType;
        // Final fallback: user color (even if default) -> editor default.
        if (typeof link.color === 'string' && link.color.length > 0) return link.color;
        return (editor && editor.defaultLinkColor)
            || (editor && editor.darkMode ? '#ffffff' : '#666666');
    }

    function resolveStyle(link) {
        if (!link) return 'solid';
        // Explicit user style wins.
        if (typeof link.style === 'string' && link.style.length > 0) return link.style;
        var s = styleFor(link.linkType);
        return s || 'solid';
    }

    function resolveWidth(link, editor) {
        if (!link) {
            return (editor && typeof editor.currentLinkWidth === 'number')
                ? editor.currentLinkWidth : 2;
        }
        if (typeof link.width === 'number') return link.width;
        var w = widthFor(link.linkType, undefined);
        if (typeof w === 'number') return w;
        return (editor && typeof editor.currentLinkWidth === 'number')
            ? editor.currentLinkWidth : 2;
    }

    window.TopologyLinkStyles = {
        TYPE_COLORS: TYPE_COLORS,
        TYPE_STYLES: TYPE_STYLES,
        TYPE_WIDTHS: TYPE_WIDTHS,
        colorFor: colorFor,
        styleFor: styleFor,
        widthFor: widthFor,
        resolveColor: resolveColor,
        resolveStyle: resolveStyle,
        resolveWidth: resolveWidth
    };
})();
