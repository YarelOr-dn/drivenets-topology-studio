"""
DNOS CLI Rules Database - Comprehensive DNOS configuration rules.

This module contains detailed rules for DNOS configuration validation,
derived from the official DNOS CLI documentation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class HierarchySpec:
    """Specification for a configuration hierarchy."""
    path: str  # Dot-separated hierarchy path
    description: str
    required_children: List[str] = field(default_factory=list)
    optional_children: List[str] = field(default_factory=list)
    value_type: Optional[str] = None  # 'string', 'integer', 'ip', 'cidr', etc.
    value_pattern: Optional[str] = None  # Regex pattern for value
    value_choices: Optional[List[str]] = None  # Valid choices
    value_range: Optional[tuple] = None  # (min, max) for integers
    parent: Optional[str] = None
    requires_peers: List[str] = field(default_factory=list)  # Other hierarchies that must exist
    conflicts_with: List[str] = field(default_factory=list)  # Mutually exclusive
    deprecated: bool = False
    deprecated_alternative: Optional[str] = None


# Comprehensive DNOS CLI rules
DNOS_HIERARCHY_RULES: Dict[str, HierarchySpec] = {
    # =====================================================================
    # INTERFACES
    # =====================================================================
    "interfaces": HierarchySpec(
        path="interfaces",
        description="Interface configuration container",
        optional_children=[
            "ge", "xe", "et", "bundle", "irb", "lo", "ph",
            "management", "null"
        ]
    ),
    
    "interfaces.ge": HierarchySpec(
        path="interfaces.ge*",
        description="Gigabit Ethernet interface",
        required_children=["admin-state"],
        optional_children=[
            "description", "mtu", "speed", "fec", "mpls",
            "ipv4-address", "ipv6-address", "vlan-id", "vlan-tags"
        ],
        value_pattern=r"ge\d+-\d+/\d+/\d+(\.\d+)?",
    ),
    
    "interfaces.xe": HierarchySpec(
        path="interfaces.xe*",
        description="10 Gigabit Ethernet interface",
        required_children=["admin-state"],
        optional_children=[
            "description", "mtu", "speed", "fec", "mpls",
            "ipv4-address", "ipv6-address", "vlan-id", "vlan-tags"
        ],
        value_pattern=r"xe\d+-\d+/\d+/\d+(\.\d+)?",
    ),
    
    "interfaces.et": HierarchySpec(
        path="interfaces.et*",
        description="Ethernet interface (25G/40G/100G/400G)",
        required_children=["admin-state"],
        optional_children=[
            "description", "mtu", "speed", "fec", "mpls",
            "ipv4-address", "ipv6-address", "vlan-id", "vlan-tags",
            "bundle-membership"
        ],
        value_pattern=r"et\d+-\d+/\d+/\d+(\.\d+)?",
    ),
    
    "interfaces.bundle": HierarchySpec(
        path="interfaces.bundle*",
        description="Bundle/LAG interface",
        required_children=["admin-state"],
        optional_children=[
            "description", "mtu", "mpls",
            "ipv4-address", "ipv6-address", "vlan-id", "vlan-tags",
            "lacp-mode", "minimum-links", "max-active-links"
        ],
        value_pattern=r"bundle\d+(\.\d+)?",
    ),
    
    "interfaces.irb": HierarchySpec(
        path="interfaces.irb*",
        description="Integrated Routing and Bridging interface",
        required_children=["admin-state"],
        optional_children=[
            "description", "mtu", "ipv4-address", "ipv6-address"
        ],
        value_pattern=r"irb\d+",
    ),
    
    "interfaces.lo": HierarchySpec(
        path="interfaces.lo*",
        description="Loopback interface",
        required_children=["admin-state"],
        optional_children=[
            "description", "ipv4-address", "ipv6-address"
        ],
        value_pattern=r"lo\d+",
    ),
    
    "interfaces.ph": HierarchySpec(
        path="interfaces.ph*",
        description="PWHE (Pseudowire Headend) interface",
        required_children=["admin-state"],
        optional_children=[
            "description", "mtu", "mpls",
            "vlan-id", "vlan-tags", "generic-interface-list"
        ],
        value_pattern=r"ph\d+(\.\d+)?",
    ),
    
    "interfaces.admin-state": HierarchySpec(
        path="interfaces.*.admin-state",
        description="Administrative state",
        value_choices=["enabled", "disabled"],
        parent="interfaces.*"
    ),
    
    "interfaces.vlan-id": HierarchySpec(
        path="interfaces.*.vlan-id",
        description="Single VLAN encapsulation",
        value_type="integer",
        value_range=(1, 4094),
        conflicts_with=["vlan-tags"],
        parent="interfaces.*"
    ),
    
    "interfaces.vlan-tags": HierarchySpec(
        path="interfaces.*.vlan-tags",
        description="QinQ VLAN encapsulation",
        required_children=["outer-tag", "inner-tag"],
        optional_children=["outer-tpid"],
        conflicts_with=["vlan-id"],
        parent="interfaces.*"
    ),
    
    "interfaces.vlan-tags.outer-tag": HierarchySpec(
        path="interfaces.*.vlan-tags.outer-tag",
        description="Outer VLAN tag (S-tag)",
        required_children=["vlan-id"],
        optional_children=["tpid"],
        parent="interfaces.*.vlan-tags"
    ),
    
    "interfaces.vlan-tags.inner-tag": HierarchySpec(
        path="interfaces.*.vlan-tags.inner-tag",
        description="Inner VLAN tag (C-tag)",
        required_children=["vlan-id"],
        optional_children=["tpid"],
        parent="interfaces.*.vlan-tags"
    ),
    
    "interfaces.mpls": HierarchySpec(
        path="interfaces.*.mpls",
        description="MPLS on interface",
        required_children=["admin-state"],
        parent="interfaces.*"
    ),
    
    # Flowspec Interface Configuration (SW-182545, SW-182546)
    # Reference: /home/dn/SCALER/dnos_cheetah_docs/Interfaces/interfaces flowspec.rst
    # Note: Enables ingress flow filtering per BGP Flowspec rules
    # Supported: Physical, Physical-VLAN, Bundle, Bundle-VLAN, IRB
    "interfaces.flowspec": HierarchySpec(
        path="interfaces.*.flowspec",
        description="BGP Flowspec filtering on interface (DDoS mitigation)",
        optional_children=["admin-state"],
        parent="interfaces.*"
    ),
    
    # Flowspec admin-state: Default disabled. When enabled, ingress filtering per BGP FlowSpec rules
    "interfaces.flowspec.admin-state": HierarchySpec(
        path="interfaces.*.flowspec.admin-state",
        description="Flowspec administrative state",
        value_choices=["enabled", "disabled"],
        parent="interfaces.*.flowspec"
    ),
    
    "interfaces.ipv4-address": HierarchySpec(
        path="interfaces.*.ipv4-address",
        description="IPv4 address configuration",
        value_pattern=r"\d+\.\d+\.\d+\.\d+/\d+",
        parent="interfaces.*"
    ),
    
    "interfaces.ipv6-address": HierarchySpec(
        path="interfaces.*.ipv6-address",
        description="IPv6 address configuration",
        value_pattern=r"[0-9a-fA-F:]+/\d+",
        parent="interfaces.*"
    ),
    
    # =====================================================================
    # PROTOCOLS - BGP
    # =====================================================================
    "protocols": HierarchySpec(
        path="protocols",
        description="Protocol configuration container",
        optional_children=["bgp", "isis", "ospf", "ldp", "static"]
    ),
    
    "protocols.bgp": HierarchySpec(
        path="protocols.bgp",
        description="BGP protocol configuration",
        required_children=["router-id"],
        optional_children=[
            "neighbor", "peer-group", "address-family",
            "graceful-restart", "route-reflector"
        ],
        value_type="integer",  # AS number
        value_range=(1, 4294967295)
    ),
    
    "protocols.bgp.router-id": HierarchySpec(
        path="protocols.bgp.router-id",
        description="BGP router ID",
        value_pattern=r"\d+\.\d+\.\d+\.\d+",
        parent="protocols.bgp"
    ),
    
    "protocols.bgp.neighbor": HierarchySpec(
        path="protocols.bgp.neighbor",
        description="BGP neighbor configuration",
        required_children=["remote-as"],
        optional_children=[
            "description", "update-source", "ebgp-multihop",
            "local-as", "password", "peer-group", "address-family",
            "admin-state", "hold-time", "keepalive-interval"
        ],
        value_pattern=r"\d+\.\d+\.\d+\.\d+",  # IP address
        parent="protocols.bgp"
    ),
    
    "protocols.bgp.neighbor.remote-as": HierarchySpec(
        path="protocols.bgp.neighbor.remote-as",
        description="Remote AS number",
        value_type="integer",
        value_range=(1, 4294967295),
        parent="protocols.bgp.neighbor"
    ),
    
    "protocols.bgp.neighbor.address-family": HierarchySpec(
        path="protocols.bgp.neighbor.address-family",
        description="BGP address family",
        # Valid DNOS CLI AFI/SAFI values (from DNOS CLI documentation)
        value_choices=[
            "ipv4-unicast", "ipv6-unicast",
            "ipv4-vpn", "ipv6-vpn",  # NOT vpnv4-unicast/vpnv6-unicast!
            "l2vpn-evpn", "link-state",
            "ipv4-flowspec", "ipv6-flowspec",
            "ipv4-rt-constrains", "ipv4-multicast",
            "ipv4-labeled-unicast", "ipv6-labeled-unicast",  # BGP-LU (Labeled Unicast)
            "ipv4-flowspec-vpn", "ipv6-flowspec-vpn"  # Flowspec VPN SAFI 134
        ],
        optional_children=[
            "send-community", "route-policy-in", "route-policy-out",
            "next-hop-self", "soft-reconfiguration", "activate",
            "add-path", "aigp", "allow-as-in", "as-override",
            "maximum-prefix", "route-reflector-client"
        ],
        parent="protocols.bgp.neighbor"
    ),
    
    "protocols.bgp.neighbor.address-family.send-community": HierarchySpec(
        path="protocols.bgp.neighbor.address-family.send-community",
        description="Send BGP communities",
        optional_children=["community-type"],
        parent="protocols.bgp.neighbor.address-family"
    ),
    
    "protocols.bgp.peer-group": HierarchySpec(
        path="protocols.bgp.peer-group",
        description="BGP peer group template",
        optional_children=[
            "remote-as", "update-source", "address-family",
            "local-as", "ebgp-multihop"
        ],
        value_type="string",
        parent="protocols.bgp"
    ),
    
    # =====================================================================
    # PROTOCOLS - ISIS
    # =====================================================================
    "protocols.isis": HierarchySpec(
        path="protocols.isis",
        description="IS-IS protocol configuration",
        required_children=["instance"],
        parent="protocols"
    ),
    
    "protocols.isis.instance": HierarchySpec(
        path="protocols.isis.instance",
        description="IS-IS instance",
        required_children=["iso-network"],
        optional_children=[
            "address-family", "interface", "segment-routing",
            "level", "authentication", "lsp-refresh-interval",
            "max-lsp-lifetime", "overload", "reference-bandwidth"
        ],
        value_type="string",  # Instance name
        parent="protocols.isis"
    ),
    
    "protocols.isis.instance.iso-network": HierarchySpec(
        path="protocols.isis.instance.iso-network",
        description="IS-IS NET (Network Entity Title)",
        value_pattern=r"\d+\.\d{4}\.\d{4}\.\d{4}\.00",
        parent="protocols.isis.instance"
    ),
    
    "protocols.isis.instance.level": HierarchySpec(
        path="protocols.isis.instance.level",
        description="IS-IS level (level-1, level-2, or level-1-2)",
        value_choices=["level-1", "level-2", "level-1-2"],
        parent="protocols.isis.instance"
    ),
    
    "protocols.isis.instance.interface": HierarchySpec(
        path="protocols.isis.instance.interface",
        description="IS-IS interface",
        required_children=["admin-state"],
        optional_children=[
            "address-family", "circuit-type", "metric", "priority",
            "hello-interval", "hello-multiplier", "passive", "bfd"
        ],
        value_type="string",  # Interface name
        parent="protocols.isis.instance"
    ),
    
    "protocols.isis.instance.interface.circuit-type": HierarchySpec(
        path="protocols.isis.instance.interface.circuit-type",
        description="IS-IS circuit type",
        value_choices=["level-1", "level-2", "level-1-2"],
        parent="protocols.isis.instance.interface"
    ),
    
    "protocols.isis.instance.segment-routing": HierarchySpec(
        path="protocols.isis.instance.segment-routing",
        description="Segment Routing configuration",
        required_children=["global-block"],
        optional_children=["admin-state"],
        parent="protocols.isis.instance"
    ),
    
    "protocols.isis.instance.segment-routing.global-block": HierarchySpec(
        path="protocols.isis.instance.segment-routing.global-block",
        description="SRGB (Segment Routing Global Block)",
        required_children=["start-label", "range"],
        parent="protocols.isis.instance.segment-routing"
    ),
    
    # =====================================================================
    # PROTOCOLS - OSPF
    # =====================================================================
    "protocols.ospf": HierarchySpec(
        path="protocols.ospf",
        description="OSPF protocol configuration",
        required_children=["instance"],
        parent="protocols"
    ),
    
    "protocols.ospf.instance": HierarchySpec(
        path="protocols.ospf.instance",
        description="OSPF instance",
        required_children=["router-id"],
        optional_children=[
            "area", "address-family", "segment-routing",
            "reference-bandwidth", "auto-cost"
        ],
        value_type="string",  # Instance name
        parent="protocols.ospf"
    ),
    
    "protocols.ospf.instance.area": HierarchySpec(
        path="protocols.ospf.instance.area",
        description="OSPF area",
        optional_children=["interface", "area-type", "stub"],
        value_pattern=r"\d+\.\d+\.\d+\.\d+|\d+",  # IP or integer
        parent="protocols.ospf.instance"
    ),
    
    "protocols.ospf.instance.area.interface": HierarchySpec(
        path="protocols.ospf.instance.area.interface",
        description="OSPF interface in area",
        required_children=["admin-state"],
        optional_children=[
            "network-type", "priority", "cost", "hello-interval",
            "dead-interval", "passive", "bfd"
        ],
        value_type="string",  # Interface name
        parent="protocols.ospf.instance.area"
    ),
    
    "protocols.ospf.instance.area.interface.network-type": HierarchySpec(
        path="protocols.ospf.instance.area.interface.network-type",
        description="OSPF network type",
        value_choices=["broadcast", "point-to-point", "point-to-multipoint", "nbma"],
        parent="protocols.ospf.instance.area.interface"
    ),
    
    # =====================================================================
    # PROTOCOLS - LDP
    # =====================================================================
    "protocols.ldp": HierarchySpec(
        path="protocols.ldp",
        description="LDP protocol configuration",
        required_children=["router-id", "admin-state"],
        optional_children=["address-family", "interface"],
        parent="protocols"
    ),
    
    "protocols.ldp.interface": HierarchySpec(
        path="protocols.ldp.interface",
        description="LDP interface",
        required_children=["admin-state"],
        value_type="string",  # Interface name
        parent="protocols.ldp"
    ),
    
    # =====================================================================
    # NETWORK SERVICES
    # =====================================================================
    "network-services": HierarchySpec(
        path="network-services",
        description="Network services container",
        optional_children=[
            "evpn-vpws-fxc", "evpn-vpls", "vpls", "l3vpn", "bridge-domain"
        ]
    ),
    
    "network-services.evpn-vpws-fxc": HierarchySpec(
        path="network-services.evpn-vpws-fxc",
        description="EVPN-VPWS Flexible Cross-Connect service",
        required_children=["instance"],
        parent="network-services"
    ),
    
    "network-services.evpn-vpws-fxc.instance": HierarchySpec(
        path="network-services.evpn-vpws-fxc.instance",
        description="FXC service instance",
        required_children=["admin-state", "protocols", "transport-protocol"],
        optional_children=[
            "interface", "evi", "service-id", "ethernet-segment",
            "source-address", "destination-address"
        ],
        value_type="string",  # Instance name
        parent="network-services.evpn-vpws-fxc"
    ),
    
    "network-services.evpn-vpws-fxc.instance.protocols": HierarchySpec(
        path="network-services.evpn-vpws-fxc.instance.protocols",
        description="FXC protocol configuration",
        required_children=["bgp"],
        parent="network-services.evpn-vpws-fxc.instance"
    ),
    
    "network-services.evpn-vpws-fxc.instance.protocols.bgp": HierarchySpec(
        path="network-services.evpn-vpws-fxc.instance.protocols.bgp",
        description="FXC BGP signaling",
        required_children=[
            "route-distinguisher", "export-l2vpn-evpn", "import-l2vpn-evpn"
        ],
        value_type="integer",  # AS number
        parent="network-services.evpn-vpws-fxc.instance.protocols"
    ),
    
    "network-services.evpn-vpws-fxc.instance.transport-protocol": HierarchySpec(
        path="network-services.evpn-vpws-fxc.instance.transport-protocol",
        description="Transport protocol for FXC (MPLS or SRv6)",
        value_choices=["mpls", "srv6"],
        optional_children=["control-word", "fat-label", "locator"],
        parent="network-services.evpn-vpws-fxc.instance"
    ),
    
    "network-services.evpn-vpws-fxc.instance.transport-protocol.mpls.control-word": HierarchySpec(
        path="network-services.evpn-vpws-fxc.instance.transport-protocol.mpls.control-word",
        description="Control Word - adds 4-byte header for proper sequencing",
        value_choices=["enabled", "disabled"],
        parent="network-services.evpn-vpws-fxc.instance.transport-protocol.mpls"
    ),
    
    "network-services.evpn-vpws-fxc.instance.transport-protocol.mpls.fat-label": HierarchySpec(
        path="network-services.evpn-vpws-fxc.instance.transport-protocol.mpls.fat-label",
        description="FAT Label - enables ECMP load balancing across multiple paths",
        value_choices=["enabled", "disabled"],
        parent="network-services.evpn-vpws-fxc.instance.transport-protocol.mpls"
    ),
    
    "network-services.evpn-vpws-fxc.instance.l2-mtu": HierarchySpec(
        path="network-services.evpn-vpws-fxc.instance.l2-mtu",
        description="L2 MTU - maximum frame size for the service",
        value_type="integer",
        value_range=(64, 65535),
        parent="network-services.evpn-vpws-fxc.instance"
    ),
    
    "network-services.evpn-vpws-fxc.instance.interface": HierarchySpec(
        path="network-services.evpn-vpws-fxc.instance.interface",
        description="FXC service attachment interface",
        optional_children=["service-point-id"],
        value_type="string",  # Interface name
        parent="network-services.evpn-vpws-fxc.instance"
    ),
    
    # L3VPN
    "network-services.l3vpn": HierarchySpec(
        path="network-services.l3vpn",
        description="Layer 3 VPN service",
        required_children=["instance"],
        parent="network-services"
    ),
    
    "network-services.l3vpn.instance": HierarchySpec(
        path="network-services.l3vpn.instance",
        description="L3VPN instance (VRF)",
        required_children=["admin-state", "route-distinguisher"],
        optional_children=[
            "interface", "export-route-target", "import-route-target",
            "protocols", "address-family"
        ],
        value_type="string",  # Instance name
        parent="network-services.l3vpn"
    ),
    
    # EVPN-VPLS
    "network-services.evpn-vpls": HierarchySpec(
        path="network-services.evpn-vpls",
        description="EVPN-VPLS service",
        required_children=["instance"],
        parent="network-services"
    ),
    
    "network-services.evpn-vpls.instance": HierarchySpec(
        path="network-services.evpn-vpls.instance",
        description="EVPN-VPLS instance",
        required_children=["admin-state", "protocols", "evi"],
        optional_children=[
            "interface", "bridge-domain", "ethernet-segment",
            "transport-protocol"
        ],
        value_type="string",
        parent="network-services.evpn-vpls"
    ),
}


# Common DNOS CLI syntax mistakes and their corrections
# Keys are EXACT matches only (not substrings) to avoid false positives
COMMON_MISTAKES_EXACT: Dict[str, str] = {
    "peer-as": "Use 'remote-as' instead of 'peer-as'",
    "neighbor-address": "Use 'neighbor <ip>' instead of 'neighbor-address'",
    "as-number": "Specify AS number after 'bgp' keyword: 'protocols bgp <as>'",
    "area-id": "Use 'area <id>' without 'area-id' keyword",
    "enable": "Use 'admin-state enabled' instead of 'enable'",
    "disable": "Use 'admin-state disabled' instead of 'disable'",
    "interface-name": "Use 'interface <name>' without 'interface-name'",
}

# Pattern-based mistakes (checked with regex)
COMMON_MISTAKES_PATTERN: Dict[str, tuple] = {
    r"^no\s+": ("DNOS doesn't use 'no' prefix - use 'delete' or remove config", True),
    r"^network-type\s+p2p$": ("Use 'network-type point-to-point'", True),
    r"^network-type\s+bcast$": ("Use 'network-type broadcast'", True),
}

# Deprecated - keep for backward compatibility
COMMON_MISTAKES: Dict[str, str] = COMMON_MISTAKES_EXACT


# Interface ordering rules - DNOS requires specific order
INTERFACE_ORDER_RULES = {
    "parent_before_subif": {
        "description": "Parent interface must appear before its sub-interfaces",
        "severity": "error",
        "example_correct": "ph1 -> ph1.1 -> ph1.2",
        "example_incorrect": "ph1.1 -> ph1",
    },
    "subifs_grouped": {
        "description": "Sub-interfaces must be grouped under their parent (not split by other parents)",
        "severity": "warning",
        "example_correct": "ph1 -> ph1.1 -> ph1.2 -> ph2 -> ph2.1",
        "example_incorrect": "ph1 -> ph2 -> ph1.1 -> ph2.1",
    },
    "no_orphan_subifs": {
        "description": "Sub-interfaces must have a parent interface defined",
        "severity": "error",
        "example_correct": "ph1 (parent exists) -> ph1.1",
        "example_incorrect": "ph1.1 (no ph1 parent)",
    },
}


# DNOS configuration limits (from Release Notes)
DNOS_LIMITS: Dict[str, int] = {
    "max_physical_interfaces": 512,
    "max_bundle_interfaces": 128,
    "max_bundle_subinterfaces": 4096,
    "max_pwhe_interfaces": 8192,
    "max_irb_interfaces": 4096,
    "max_loopback_interfaces": 64,
    "max_fxc_instances": 32000,
    "max_evpn_vpls_instances": 4096,
    "max_l3vpn_instances": 4096,
    "max_bgp_peers": 1024,
    "max_isis_interfaces": 512,
    "max_ospf_interfaces": 512,
    "max_ldp_interfaces": 256,
    "max_static_routes": 100000,
    "max_acl_entries": 10000,
    "max_policy_maps": 1024,
    # Flowspec VPN limits (SW-182545, SW-182546) - flowspec-local from dn-flowspec-local-policies.yang
    # HW TCAM: 12000 IPv4 + 4000 IPv6 per NCP (show system npu-resources resource-type flowspec)
    # YANG max-elements: 8000 IPv4 MC defs, 4000 IPv6 MC defs, 20 policies per AFI
    "max_flowspec_rules_per_vrf": 3000,
    "max_flowspec_rules_total": 20000,
    "max_flowspec_interfaces": 1000,
    "max_flowspec_local_policies": 40,
    "max_flowspec_match_classes": 12000,
    "max_flowspec_hw_entries_ipv4": 12000,
    "max_flowspec_hw_entries_ipv6": 4000,
}


def get_hierarchy_spec(path: str) -> Optional[HierarchySpec]:
    """Get hierarchy specification for a path."""
    # Try exact match first
    if path in DNOS_HIERARCHY_RULES:
        return DNOS_HIERARCHY_RULES[path]
    
    # Try wildcard matches
    for rule_path, spec in DNOS_HIERARCHY_RULES.items():
        if '*' in rule_path:
            # Convert wildcard to regex
            pattern = rule_path.replace('.', r'\.').replace('*', r'[^.]+')
            import re
            if re.match(f'^{pattern}$', path):
                return spec
    
    return None


def check_common_mistake(keyword: str) -> Optional[str]:
    """Check if a keyword is a common mistake and return correction.
    
    Uses exact matching for most rules to avoid false positives.
    """
    import re
    
    # Check exact matches first
    lower_keyword = keyword.lower().strip()
    if lower_keyword in COMMON_MISTAKES_EXACT:
        return COMMON_MISTAKES_EXACT[lower_keyword]
    
    # Check pattern matches
    for pattern, (correction, is_error) in COMMON_MISTAKES_PATTERN.items():
        if re.match(pattern, lower_keyword):
            return correction
    
    return None


def get_limit(resource: str) -> Optional[int]:
    """Get the DNOS limit for a resource type."""
    return DNOS_LIMITS.get(resource)

