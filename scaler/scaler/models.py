"""Pydantic models for SCALER configuration and data structures."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import base64


class Platform(str, Enum):
    """DNOS hardware platforms (legacy enum -- kept for backward compat).
    New system types (CL-86, SA-40C, etc.) use the string field on Device.
    """
    NCP = "NCP"
    NCM = "NCM"
    NCP5 = "NCP5"


class ServiceType(str, Enum):
    """Network service types."""
    FXC = "evpn-vpws-fxc"
    VRF = "vrf"
    EVPN = "evpn"
    VPWS = "vpws"
    BRIDGE_DOMAIN = "bridge-domain"


class InterfaceType(str, Enum):
    """Interface types for scaling."""
    PH = "ph"
    GE100 = "ge100"
    GE400 = "ge400"
    BUNDLE = "bundle"


class RedundancyMode(str, Enum):
    """Multihoming redundancy modes."""
    ALL_ACTIVE = "all-active"
    SINGLE_ACTIVE = "single-active"


class FlowspecAddressFamily(str, Enum):
    """Flowspec address family types (SW-182545, SW-182546)."""
    IPV4_FLOWSPEC = "ipv4-flowspec"
    IPV6_FLOWSPEC = "ipv6-flowspec"


class FlowspecAction(str, Enum):
    """Flowspec action types.
    
    Reference: /home/dn/SCALER/dnos_cheetah_docs/Routing-policy/flowspec-local-policies/
    """
    DISCARD = "discard"
    RATE_LIMIT = "rate-limit"
    REDIRECT_IP = "redirect-to-ip"
    REDIRECT_VRF = "redirect-to-vrf"  # Not supported for redirect to different VRF


class FlowspecMatchCriteria(str, Enum):
    """Flowspec match criteria types.
    
    Reference: /home/dn/SCALER/dnos_cheetah_docs/Routing-policy/flowspec-local-policies/ipv4/mc-defns/
    """
    DEST_IP = "dest-ip"
    SOURCE_IP = "source-ip"
    DEST_PORT = "dest-port"
    SRC_PORT = "src-port"
    PROTOCOL = "protocol"
    DSCP = "dscp"
    PACKET_LENGTH = "packet-length"
    TCP_FLAG = "tcp-flag"
    FRAGMENTED = "fragmented"
    ICMP = "icmp"


class Device(BaseModel):
    """DNOS device configuration."""
    id: str = Field(..., description="Unique device identifier")
    hostname: str = Field(..., description="Device hostname")
    ip: str = Field(..., description="IP address or DNS name for SSH")
    username: str = Field(default="dnroot", description="SSH username")
    password: str = Field(..., description="SSH password (base64 encoded)")
    platform: str = Field(default="NCP", description="Hardware platform or system type (NCP, CL-86, SA-40C, etc.)")
    system_type: Optional[str] = Field(default=None, description="System type for deployment (CL-86, SA-36CD-S, SA-40C, etc.)")
    last_sync: Optional[datetime] = Field(default=None, description="Last config sync time")
    description: Optional[str] = Field(default=None, description="Device description")
    management_ip: Optional[str] = Field(default=None, description="Auto-discovered management IP (fallback)")
    connection_method: Optional[str] = Field(default=None, description="Connection method (SSH->MGMT, etc.)")

    @classmethod
    def encode_password(cls, plain_password: str) -> str:
        """Encode password to base64 for storage."""
        return base64.b64encode(plain_password.encode()).decode()

    @classmethod
    def decode_password(cls, encoded_password: str) -> str:
        """Decode password from base64."""
        return base64.b64decode(encoded_password.encode()).decode()

    def get_password(self) -> str:
        """Get decoded password."""
        return self.decode_password(self.password)
    
    def get_connection_addresses(self) -> List[str]:
        """Get list of addresses to try for connection (primary first, then fallback)."""
        addresses = [self.ip]
        if self.management_ip and self.management_ip != self.ip:
            addresses.append(self.management_ip)
        return addresses


class InterfaceScale(BaseModel):
    """Interface scaling configuration."""
    interface_type: InterfaceType = Field(..., description="Type of interface to create")
    start_number: int = Field(default=1, ge=1, description="Starting interface number")
    count: int = Field(..., ge=1, description="Number of interfaces to create")
    slot: int = Field(default=1, ge=1, le=16, description="Slot number for physical interfaces")
    bay: int = Field(default=0, ge=0, le=3, description="Bay number")
    port_start: int = Field(default=0, ge=0, description="Starting port number")
    
    # Sub-interface configuration
    create_subinterfaces: bool = Field(default=True, description="Create sub-interfaces")
    subif_vlan_start: int = Field(default=1, ge=1, le=4094, description="Starting VLAN ID")
    subif_vlan_step: int = Field(default=1, ge=1, description="VLAN ID increment step")
    subif_count_per_interface: int = Field(default=1, ge=1, description="Sub-interfaces per parent")
    
    # IP addressing for sub-interfaces
    enable_ip: bool = Field(default=False, description="Configure IP addresses")
    ip_start: Optional[str] = Field(default=None, description="Starting IP address (e.g., 10.0.0.1/24)")
    ip_step: int = Field(default=1, ge=1, description="IP address increment step")
    
    # L2 service binding
    bind_to_service: bool = Field(default=True, description="Bind to network service")

    @field_validator('subif_vlan_start')
    @classmethod
    def validate_vlan_start(cls, v: int) -> int:
        if v < 1 or v > 4094:
            raise ValueError("VLAN ID must be between 1 and 4094")
        return v


class ServiceScale(BaseModel):
    """Network service scaling configuration."""
    service_type: ServiceType = Field(..., description="Type of network service")
    name_prefix: str = Field(default="SVC_", description="Service name prefix")
    start_number: int = Field(default=1, ge=1, description="Starting service number")
    count: int = Field(..., ge=1, description="Number of services to create")
    
    # Route Distinguisher configuration
    rd_router_id: str = Field(..., description="Router ID for RD (e.g., 10.0.0.1)")
    rd_start: int = Field(default=1, ge=1, description="Starting RD value")
    rd_step: int = Field(default=1, ge=1, description="RD increment step")
    
    # Route Target configuration
    rt_asn: int = Field(..., ge=1, le=4294967295, description="AS number for RT")
    rt_start: int = Field(default=1, ge=1, description="Starting RT value")
    rt_step: int = Field(default=1, ge=1, description="RT increment step")
    rt_import_equals_export: bool = Field(default=True, description="Import RT equals Export RT")
    
    # FXC-specific options
    fxc_mode: str = Field(default="vlan-unaware", description="FXC mode: vlan-aware|vlan-unaware")
    
    # VRF-specific options
    vrf_address_family: List[str] = Field(
        default=["ipv4-unicast"],
        description="Address families for VRF"
    )
    
    # EVPN-specific options
    evpn_type: str = Field(default="mac-vrf", description="EVPN type: mac-vrf|evi")
    
    # Service admin state
    admin_state: str = Field(default="enabled", description="Admin state: enabled|disabled")
    
    # L2 MTU
    l2_mtu: Optional[int] = Field(default=None, ge=64, le=9216, description="L2 MTU size")


class MultihomingScale(BaseModel):
    """Multihoming (ESI) configuration for scaling."""
    enabled: bool = Field(default=False, description="Enable multihoming")
    esi_base: str = Field(
        default="00:01:02:03:04:05:06:07:08:00",
        description="Base ESI value (10 octets hex)"
    )
    esi_step_octet: int = Field(default=9, ge=0, le=9, description="Which octet to increment (0-9)")
    esi_step: int = Field(default=1, ge=1, description="ESI increment step")
    redundancy_mode: RedundancyMode = Field(
        default=RedundancyMode.ALL_ACTIVE,
        description="Redundancy mode"
    )
    df_election_wait_time: Optional[int] = Field(
        default=None,
        ge=1,
        le=600,
        description="DF election wait time in seconds"
    )

    @field_validator('esi_base')
    @classmethod
    def validate_esi_format(cls, v: str) -> str:
        """Validate ESI format (10 octets in hex, colon-separated)."""
        parts = v.split(':')
        if len(parts) != 10:
            raise ValueError("ESI must have exactly 10 octets (e.g., 00:01:02:03:04:05:06:07:08:00)")
        for part in parts:
            if len(part) != 2:
                raise ValueError("Each ESI octet must be 2 hex digits")
            try:
                int(part, 16)
            except ValueError:
                raise ValueError(f"Invalid hex value in ESI: {part}")
        return v


class BGPPeerScale(BaseModel):
    """BGP peer scaling configuration."""
    enabled: bool = Field(default=False, description="Enable BGP peer scaling")
    peer_ip_start: str = Field(..., description="Starting peer IP address")
    peer_ip_step: int = Field(default=1, ge=1, description="Peer IP increment step")
    count: int = Field(default=1, ge=1, description="Number of BGP peers to create")
    peer_as: int = Field(..., ge=1, le=4294967295, description="Peer AS number")
    description_prefix: str = Field(default="PEER_", description="Peer description prefix")
    address_family: List[str] = Field(
        default=["ipv4-unicast"],
        description="Address families to configure"
    )
    update_source: Optional[str] = Field(default=None, description="Update source interface")
    next_hop_self: bool = Field(default=False, description="Enable next-hop-self")
    send_community: bool = Field(default=True, description="Send community attributes")
    route_reflector_client: bool = Field(default=False, description="Configure as RR client")


class FlowspecMatchClass(BaseModel):
    """Flowspec match class definition (SW-182545, SW-182546).
    
    Reference: /home/dn/SCALER/dnos_cheetah_docs/Routing-policy/flowspec-local-policies/ipv4/mc-defns/
    """
    name: str = Field(..., description="Match class name (1-255 chars)")
    description: Optional[str] = Field(default=None, description="Match class description")
    dest_ip: Optional[str] = Field(default=None, description="Destination IP prefix (A.B.C.D/M)")
    source_ip: Optional[str] = Field(default=None, description="Source IP prefix (A.B.C.D/M)")
    dest_port: Optional[str] = Field(default=None, description="Destination port(s) with operators (= < > & |)")
    src_port: Optional[str] = Field(default=None, description="Source port(s) with operators")
    protocol: Optional[str] = Field(default=None, description="IP protocol (0-255, tcp=6, udp=17, icmp=1)")
    dscp: Optional[str] = Field(default=None, description="DSCP value (0-63)")
    packet_length: Optional[str] = Field(default=None, description="Packet length with operators (0-65535)")
    tcp_flag: Optional[str] = Field(default=None, description="TCP flags (syn, ack, fin, rst, psh, urg)")
    fragmented: Optional[bool] = Field(default=None, description="Match fragmented packets")
    icmp_type: Optional[int] = Field(default=None, ge=0, le=255, description="ICMP type")
    icmp_code: Optional[int] = Field(default=None, ge=0, le=255, description="ICMP code")


class FlowspecPolicy(BaseModel):
    """Flowspec local policy configuration (SW-182545, SW-182546).
    
    Reference: /home/dn/SCALER/dnos_cheetah_docs/Routing-policy/flowspec-local-policies/ipv4/policy/
    """
    name: str = Field(..., description="Policy name (1-255 chars)")
    description: Optional[str] = Field(default=None, description="Policy description")
    address_family: FlowspecAddressFamily = Field(
        default=FlowspecAddressFamily.IPV4_FLOWSPEC, 
        description="Address family (ipv4 or ipv6)"
    )
    match_classes: List[FlowspecMatchClass] = Field(
        default_factory=list, 
        description="List of match class definitions"
    )
    action: FlowspecAction = Field(
        default=FlowspecAction.DISCARD, 
        description="Action to take on matched traffic"
    )
    rate_limit_bps: Optional[int] = Field(
        default=None, 
        ge=0, 
        description="Rate limit in bits per second (for rate-limit action)"
    )
    redirect_ip: Optional[str] = Field(
        default=None, 
        description="Redirect IP address (for redirect-to-ip action)"
    )


class FlowspecScale(BaseModel):
    """Flowspec VPN scaling configuration (SW-182545, SW-182546).
    
    Reference: /home/dn/SCALER/dnos_cheetah_docs/Interfaces/interfaces flowspec.rst
    Reference: /home/dn/SCALER/dnos_cheetah_docs/Protocols/bgp/neighbor/address-family/
    """
    enabled: bool = Field(default=False, description="Enable Flowspec VPN")
    address_families: List[FlowspecAddressFamily] = Field(
        default_factory=lambda: [FlowspecAddressFamily.IPV4_FLOWSPEC],
        description="Flowspec address families to enable"
    )
    interfaces: List[str] = Field(
        default_factory=list, 
        description="Interfaces with flowspec admin-state enabled"
    )
    vrf_name: Optional[str] = Field(
        default=None, 
        description="VRF name (for VPN variant)"
    )
    bgp_neighbor: Optional[str] = Field(
        default=None, 
        description="BGP neighbor IP for flowspec AFI"
    )
    policies: List[FlowspecPolicy] = Field(
        default_factory=list, 
        description="Local flowspec policies"
    )
    max_rules: int = Field(
        default=3000, 
        ge=1, 
        le=10000, 
        description="Max flowspec rules per VRF"
    )

    @field_validator('interfaces')
    @classmethod
    def validate_interfaces(cls, v: List[str]) -> List[str]:
        """Validate that interfaces are flowspec-compatible types."""
        # Flowspec supports: Physical, Physical-VLAN, Bundle, Bundle-VLAN, IRB
        # Does NOT support: PWHE (ph*) 
        invalid = [i for i in v if i.startswith('ph')]
        if invalid:
            raise ValueError(f"PWHE interfaces not supported for Flowspec: {invalid[:3]}...")
        return v


class PreservedConfig(BaseModel):
    """Configuration elements to preserve from the running config."""
    wan_interfaces: List[str] = Field(default_factory=list, description="WAN interface names")
    protocols: Dict[str, Any] = Field(default_factory=dict, description="Full protocols hierarchy")
    system: Dict[str, Any] = Field(default_factory=dict, description="Full system hierarchy")
    routing_policy: Dict[str, Any] = Field(default_factory=dict, description="All routing policies")
    raw_text: str = Field(default="", description="Raw preserved config text")


class ScaleConfig(BaseModel):
    """Complete scaling configuration."""
    device_id: str = Field(..., description="Target device ID")
    
    # Scaling parameters
    interfaces: Optional[InterfaceScale] = Field(default=None, description="Interface scaling")
    services: Optional[ServiceScale] = Field(default=None, description="Service scaling")
    multihoming: Optional[MultihomingScale] = Field(default=None, description="Multihoming config")
    bgp_peers: Optional[BGPPeerScale] = Field(default=None, description="BGP peer scaling")
    flowspec: Optional[FlowspecScale] = Field(default=None, description="Flowspec VPN config (SW-182545, SW-182546)")
    
    # Preserved configuration
    preserved: Optional[PreservedConfig] = Field(default=None, description="Preserved config")
    
    # Generation metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    description: Optional[str] = Field(default=None, description="Scale configuration description")
    
    # Generated output
    generated_config: Optional[str] = Field(default=None, description="Generated config text")
    validation_passed: bool = Field(default=False, description="Validation status")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")


class DeviceConfig(BaseModel):
    """Stored device configuration."""
    device_id: str
    hostname: str
    extracted_at: datetime
    raw_config: str
    parsed_config: Dict[str, Any] = Field(default_factory=dict)
    wan_interfaces: List[str] = Field(default_factory=list)
    has_protocols: bool = False
    has_system: bool = False
    has_routing_policy: bool = False
    
    # Enhanced summary fields (from operational show commands)
    isis_summary: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="ISIS summary: {instances, levels, total_interfaces}"
    )
    ospf_summary: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="OSPF summary: {p2p_count, broadcast_count, dr_count, bdr_count}"
    )
    bgp_as: Optional[int] = Field(
        default=None, 
        description="Local BGP AS number"
    )
    vlan_range: Optional[str] = Field(
        default=None, 
        description="VLAN range string (e.g., '100-200, 300')"
    )
    interface_summary: Optional[Dict[str, int]] = Field(
        default=None, 
        description="Interface counts by type"
    )
    enhanced_summary: Optional[str] = Field(
        default=None, 
        description="Compact one-line enhanced summary"
    )


class ValidationResult(BaseModel):
    """Result of configuration validation."""
    passed: bool = True
    platform: Platform = Platform.NCP
    checks: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    
    def add_check(self, name: str, current: int, limit: int, passed: bool):
        """Add a validation check result."""
        self.checks.append({
            "name": name,
            "current": current,
            "limit": limit,
            "percentage": round((current / limit) * 100, 1) if limit > 0 else 0,
            "passed": passed
        })
        if not passed:
            self.passed = False
            self.errors.append(f"{name}: {current} exceeds limit of {limit}")


class HierarchyAction(str, Enum):
    """Action to take on a configuration hierarchy."""
    SKIP = "skip"
    ADD = "add"
    REPLACE = "replace"
    DELETE = "delete"  # Remove this section from configuration


class NamingFormat(str, Enum):
    """Naming format for auto-generated names."""
    SEQUENTIAL = "sequential"  # VRF-1, VRF-2, VRF-3
    PADDED = "padded"  # VRF-001, VRF-002, VRF-003
    TEMPLATE = "template"  # Custom template with variables


class VlanType(str, Enum):
    """VLAN encapsulation type."""
    SINGLE = "single"  # Single vlan-id (dot1q)
    QINQ = "qinq"  # Outer + inner VLAN tags
    NONE = "none"  # No VLAN tagging


class NamingPattern(BaseModel):
    """Naming pattern configuration for auto-generated names."""
    prefix: str = Field(default="", description="Name prefix (e.g., 'VRF-', 'FXC-')")
    format: NamingFormat = Field(default=NamingFormat.SEQUENTIAL, description="Numbering format")
    start_number: int = Field(default=1, ge=0, description="Starting number")
    padding: int = Field(default=0, ge=0, le=6, description="Zero-padding width (for PADDED format)")
    template: Optional[str] = Field(default=None, description="Custom template (for TEMPLATE format)")
    suffix: str = Field(default="", description="Name suffix")
    
    def generate_name(self, index: int) -> str:
        """Generate a name for the given index."""
        num = self.start_number + index
        
        if self.format == NamingFormat.PADDED and self.padding > 0:
            num_str = str(num).zfill(self.padding)
        else:
            num_str = str(num)
        
        if self.format == NamingFormat.TEMPLATE and self.template:
            return self.template.replace("{N}", num_str).replace("{n}", num_str)
        
        return f"{self.prefix}{num_str}{self.suffix}"
    
    def generate_names(self, count: int) -> List[str]:
        """Generate a list of names."""
        return [self.generate_name(i) for i in range(count)]


class HierarchyConfig(BaseModel):
    """Configuration for a single hierarchy in the wizard."""
    name: str = Field(..., description="Hierarchy name (e.g., 'interfaces', 'services')")
    action: HierarchyAction = Field(default=HierarchyAction.SKIP, description="Action to take")
    current_config: Optional[str] = Field(default=None, description="Current config text")
    new_config: Optional[str] = Field(default=None, description="New config to add/replace")
    naming: Optional[NamingPattern] = Field(default=None, description="Naming pattern")
    validated: bool = Field(default=False, description="Whether config has been validated")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")


class InterfaceScaleInput(BaseModel):
    """User input for interface scaling."""
    interface_type: str = Field(..., description="Type: physical, bundle, pwhe, irb, loopback")
    pattern: Optional[str] = Field(default=None, description="Pattern like 'ph{1-10}.{1-100}'")
    count: Optional[int] = Field(default=None, description="Simple count (alternative to pattern)")
    start_number: int = Field(default=1, ge=1, description="Starting number")
    vlan_type: VlanType = Field(default=VlanType.SINGLE, description="VLAN encapsulation type")
    outer_vlan_range: Optional[str] = Field(default=None, description="Outer VLAN range (e.g., '100-199')")
    inner_vlan_range: Optional[str] = Field(default=None, description="Inner VLAN range for QinQ")
    enable_ip: bool = Field(default=False, description="Configure IP addresses")
    ip_start: Optional[str] = Field(default=None, description="Starting IP (e.g., '10.0.0.1/24')")


class ServiceScaleInput(BaseModel):
    """User input for service scaling."""
    service_type: str = Field(..., description="Type: fxc, vrf, evpn, vpws")
    count: int = Field(..., ge=1, description="Number of services")
    naming: NamingPattern = Field(default_factory=NamingPattern, description="Naming pattern")
    rd_router_id: Optional[str] = Field(default=None, description="Router ID for RD")
    rd_start: int = Field(default=1, description="Starting RD value")
    rt_asn: Optional[int] = Field(default=None, description="AS number for RT")
    rt_start: int = Field(default=1, description="Starting RT value")
    bind_interfaces: bool = Field(default=True, description="Bind to interfaces")


class BGPScaleInput(BaseModel):
    """User input for BGP scaling."""
    count: int = Field(..., ge=1, description="Number of BGP peers")
    peer_ip_start: str = Field(..., description="Starting peer IP")
    peer_ip_step: int = Field(default=1, description="IP increment step")
    peer_as: int = Field(..., description="Peer AS number")
    address_families: List[str] = Field(
        default=["ipv4-unicast"],
        description="Address families to configure"
    )
    naming: NamingPattern = Field(default_factory=NamingPattern, description="Description naming")


class BatchScaleConfig(BaseModel):
    """Complete batch scaling configuration (for YAML/JSON input)."""
    device: str = Field(..., description="Target device ID or hostname")
    platform: Optional[Platform] = Field(default=None, description="Platform override")
    
    # Hierarchy configurations
    interfaces: Optional[InterfaceScaleInput] = Field(default=None, description="Interface scaling")
    services: Optional[ServiceScaleInput] = Field(default=None, description="Service scaling")
    bgp: Optional[BGPScaleInput] = Field(default=None, description="BGP peer scaling")
    
    # Options
    preserve_wan: bool = Field(default=True, description="Preserve WAN interfaces")
    preserve_protocols: bool = Field(default=True, description="Preserve protocols config")
    preserve_system: bool = Field(default=True, description="Preserve system config")
    
    # Execution options
    dry_run: bool = Field(default=True, description="Only run commit check, don't commit")
    verify_after: bool = Field(default=True, description="Run verification after commit")
    save_config: bool = Field(default=True, description="Save generated config to file")


class WizardState(BaseModel):
    """State of the interactive wizard."""
    device_id: Optional[str] = Field(default=None, description="Selected device ID")
    hostname: Optional[str] = Field(default=None, description="Device hostname")
    device_ip: Optional[str] = Field(default=None, description="Device IP address")
    platform: Platform = Field(default=Platform.NCP, description="Device platform")
    current_config: Optional[str] = Field(default=None, description="Current device config")
    
    # Hierarchy states
    hierarchies: Dict[str, HierarchyConfig] = Field(
        default_factory=dict,
        description="Configuration for each hierarchy"
    )
    
    # Created resources (for cross-hierarchy references)
    created_interfaces: List[str] = Field(
        default_factory=list,
        description="List of interface names created in this session"
    )
    
    # Kept interfaces from existing config (for filtering newly created vs kept)
    kept_interfaces: List[str] = Field(
        default_factory=list,
        description="List of interface names that were kept from existing config (not newly created)"
    )
    
    # L2-service enabled interfaces (for FXC/xconnect attachment)
    l2_service_interfaces: List[str] = Field(
        default_factory=list,
        description="List of interface names with l2-service enabled (can attach to FXC)"
    )
    
    # Flowspec-enabled interfaces (for DDoS protection)
    flowspec_interfaces: List[str] = Field(
        default_factory=list,
        description="List of interface names with flowspec enabled (DDoS filtering)"
    )
    
    # IP addressing info for summary
    ip_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="IP address configuration details (version, mode, ranges)"
    )
    
    # Section actions (keep/edit/delete/skip for each section)
    section_actions: Dict[str, str] = Field(
        default_factory=dict,
        description="Actions for each section: 'keep', 'edit', 'delete', 'skip'"
    )
    
    # Per-device actions for multi-device mode (section -> {hostname -> action})
    per_device_actions: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="Per-device section actions in multi-device mode: {section: {hostname: action}}"
    )
    
    # Imported template
    imported_template: Optional[str] = Field(
        default=None,
        description="Template configuration imported from file"
    )
    
    # Source file path for imported config
    imported_from_file: Optional[str] = Field(
        default=None,
        description="Path to the file the config was imported from"
    )
    
    # LACP configuration for kept bundle interfaces
    kept_lacp_config: Optional[str] = Field(
        default=None,
        description="LACP configuration for bundle interfaces that were kept"
    )
    
    # VRF attachment: knobs to remove from interfaces before attaching to VRF
    # When user attaches interfaces that have unsupported knobs (e.g. flowspec), we record
    # {no_command: [interfaces]} so generated config injects "no flowspec" (etc.) under those interfaces.
    vrf_attachment_remove_knobs: Optional[Dict[str, List[str]]] = Field(
        default=None,
        description="Knobs to remove for VRF-attached interfaces: {no_command: [interface_names]}"
    )
    
    # VRF interface mapping for advanced distribution strategies (round-robin, step, specific)
    # {vrf_index: [interface_names]} - used when interfaces_per_vrf is negative (special flag)
    vrf_interface_mapping: Optional[Dict[int, List[str]]] = Field(
        default=None,
        description="Custom VRF-to-interface mapping for non-uniform distribution"
    )
    
    # VRF step pattern for step-based distribution
    vrf_step_pattern: Optional[int] = Field(
        default=None,
        description="Step pattern for VRF interface attachment (e.g., every 2nd VRF)"
    )
    
    # Multihoming configuration
    multihoming_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Multihoming configuration details (ESI, redundancy mode, etc.)"
    )
    
    # Interface preferences (persisted during session)
    interface_prefs: Dict[str, Any] = Field(
        default_factory=lambda: {
            'vlan_manipulation': '0',  # Last used VLAN manipulation option
            'interface_mode': '1',     # Last used interface mode (1=L3, 2=L2)
            'ip_prefix_len': 30,       # Last used IP prefix length
        },
        description="Interface configuration preferences persisted during session"
    )
    
    # Generated output
    generated_config: Optional[str] = Field(default=None, description="Final generated config")
    validation_result: Optional[ValidationResult] = Field(default=None, description="Validation result")
    
    # Navigation path for breadcrumb display
    nav_path: List[str] = Field(
        default_factory=list,
        description="Current navigation path in the wizard (for breadcrumb display)"
    )
    
    # System config for two-phase commit (system must be committed before other hierarchies)
    system_config: Optional[str] = Field(
        default=None,
        description="System configuration for two-phase commit"
    )
    
    # Execution state
    config_pushed: bool = Field(default=False, description="Whether config was pushed")
    commit_check_passed: bool = Field(default=False, description="Whether commit check passed")
    committed: bool = Field(default=False, description="Whether config was committed")
    verified: bool = Field(default=False, description="Whether verification ran")


# =============================================================================
# CROSS-DEVICE CONTEXT AWARENESS
# =============================================================================

class ServiceRecord(BaseModel):
    """Record of a configured service."""
    service_type: str = Field(..., description="Service type: evpn-vpws-fxc, evpn-vpws, evpn, vrf, etc.")
    name_pattern: str = Field(..., description="Service naming pattern (e.g., FXC-{N})")
    count: int = Field(default=1, description="Number of services")
    start_index: int = Field(default=1, description="Starting index")
    rt_asn: Optional[int] = Field(default=None, description="RT ASN")
    rt_format: Optional[str] = Field(default=None, description="RT format (e.g., ASN:N)")
    rd_format: Optional[str] = Field(default=None, description="RD format (e.g., loopback:N)")
    rd_router_id: Optional[str] = Field(default=None, description="Router ID used for RD")
    evi_start: Optional[int] = Field(default=None, description="Starting EVI")
    interfaces: List[str] = Field(default_factory=list, description="Attached interfaces")
    parent_interfaces: List[str] = Field(default_factory=list, description="Parent interfaces used")
    transport: str = Field(default="mpls", description="Transport protocol")
    has_mh: bool = Field(default=False, description="Has multihoming ESI")
    mh_esi_prefix: Optional[str] = Field(default=None, description="ESI prefix if MH configured")
    flowspec_enabled: bool = Field(default=False, description="Flowspec-VPN enabled (for VRF)")
    
    # EVPN-VPWS specific fields
    vpws_service_id_start: Optional[int] = Field(default=None, description="Starting vpws-service-id")
    vpws_service_id_mode: str = Field(default="sequential", description="sequential or custom")
    control_word: bool = Field(default=True, description="Control word enabled")
    fat_label: bool = Field(default=False, description="FAT label enabled")


class VRFRecord(BaseModel):
    """Record of a configured VRF."""
    name: str = Field(..., description="VRF name")
    rd: str = Field(..., description="Route Distinguisher")
    rt_import: List[str] = Field(default_factory=list, description="Import RTs")
    rt_export: List[str] = Field(default_factory=list, description="Export RTs")
    flowspec_vpn: bool = Field(default=False, description="Flowspec-VPN enabled")
    interfaces: List[str] = Field(default_factory=list, description="Interfaces in VRF")


class InterfaceRecord(BaseModel):
    """Record of a configured interface."""
    name: str = Field(..., description="Interface name")
    iface_type: str = Field(..., description="Type: pwhe, l2-ac, irb, physical")
    parent: Optional[str] = Field(default=None, description="Parent interface for sub-ifs")
    outer_vlan: Optional[int] = Field(default=None, description="Outer VLAN tag")
    inner_vlan: Optional[int] = Field(default=None, description="Inner VLAN tag")
    l2_service: bool = Field(default=False, description="l2-service enabled")


class DeviceConfigRecord(BaseModel):
    """Record of what was configured on a device in current session."""
    hostname: str = Field(..., description="Device hostname")
    loopback_ip: Optional[str] = Field(default=None, description="Device loopback IP")
    bgp_asn: Optional[int] = Field(default=None, description="BGP ASN")
    
    # Configured items in this session
    configured_services: List[ServiceRecord] = Field(
        default_factory=list,
        description="Services configured in this session"
    )
    configured_vrfs: List[VRFRecord] = Field(
        default_factory=list,
        description="VRFs configured in this session"
    )
    configured_interfaces: List[InterfaceRecord] = Field(
        default_factory=list,
        description="Interfaces configured in this session"
    )
    
    # Multihoming config
    mh_esi_prefix: Optional[str] = Field(default=None, description="ESI prefix used")
    mh_interfaces: List[str] = Field(default_factory=list, description="MH interfaces")
    mh_mode: str = Field(default="single-active", description="MH redundancy mode")


class ConfigSuggestion(BaseModel):
    """A suggested configuration for a device based on other devices."""
    suggestion_type: str = Field(..., description="Type: matching_services, complementary, mh_pairing")
    source_device: str = Field(..., description="Device this suggestion is based on")
    target_device: str = Field(..., description="Device to apply suggestion to")
    
    # What is being suggested
    description: str = Field(..., description="Human-readable description")
    service_type: Optional[str] = Field(default=None, description="Service type if applicable")
    service_count: Optional[int] = Field(default=None, description="Number of services")
    
    # Adjustments needed for uniqueness
    rd_adjustment: Optional[str] = Field(default=None, description="New RD format (e.g., 2.2.2.2:N)")
    same_rt: bool = Field(default=True, description="Keep same RT for peering")
    same_esi: bool = Field(default=True, description="Keep same ESI for MH")
    
    # The generated config (populated when user requests it)
    generated_config: Optional[str] = Field(default=None, description="Generated DNOS config")
    
    # Complementary suggestions
    next_step_hint: Optional[str] = Field(default=None, description="Hint for next logical step")


class CrossDeviceContext(BaseModel):
    """
    Tracks configurations across all devices for smart suggestions.
    
    The wizard uses this to:
    1. Record what was configured on each device
    2. Generate suggestions for other devices based on what was configured
    3. Auto-adjust unique parameters (RD) while keeping peering params (RT, ESI) same
    """
    device_records: Dict[str, DeviceConfigRecord] = Field(
        default_factory=dict,
        description="Configuration records per device hostname"
    )
    
    def record_device_config(self, hostname: str, record: DeviceConfigRecord):
        """Store configuration record for a device."""
        self.device_records[hostname] = record
    
    def get_other_devices(self, hostname: str) -> List[str]:
        """Get list of other configured devices."""
        return [h for h in self.device_records.keys() if h != hostname]
    
    def has_suggestions_for(self, hostname: str) -> bool:
        """Check if there are suggestions available for this device."""
        other_devices = self.get_other_devices(hostname)
        for other_host in other_devices:
            record = self.device_records[other_host]
            if record.configured_services or record.configured_vrfs:
                return True
        return False
    
    def get_suggestions_for_device(
        self, 
        hostname: str, 
        target_loopback: str
    ) -> List[ConfigSuggestion]:
        """
        Analyze other devices and return suggestions for this device.
        
        Args:
            hostname: Target device hostname
            target_loopback: Target device's loopback IP (for RD generation)
            
        Returns:
            List of configuration suggestions
        """
        suggestions = []
        other_devices = self.get_other_devices(hostname)
        
        for source_host in other_devices:
            record = self.device_records[source_host]
            
            # Suggest matching services
            for svc in record.configured_services:
                suggestion = ConfigSuggestion(
                    suggestion_type="matching_services",
                    source_device=source_host,
                    target_device=hostname,
                    description=f"Match {svc.count} {svc.service_type} services from {source_host}",
                    service_type=svc.service_type,
                    service_count=svc.count,
                    rd_adjustment=f"{target_loopback}:N",  # Use target's loopback
                    same_rt=True,  # Keep RT for peering
                    same_esi=svc.has_mh,  # Keep ESI if MH
                )
                
                # Add next step hints based on service type
                if svc.service_type == "evpn-vpws-fxc":
                    suggestion.next_step_hint = "Configure L2-AC on remote PE for service termination"
                elif svc.service_type == "evpn":
                    suggestion.next_step_hint = "Configure Anycast IRB for L3 connectivity"
                
                suggestions.append(suggestion)
            
            # Suggest matching VRFs
            for vrf in record.configured_vrfs:
                suggestion = ConfigSuggestion(
                    suggestion_type="matching_vrfs",
                    source_device=source_host,
                    target_device=hostname,
                    description=f"Match VRF {vrf.name} from {source_host}" + 
                               (" with flowspec-vpn" if vrf.flowspec_vpn else ""),
                    rd_adjustment=f"{target_loopback}:{vrf.rd.split(':')[-1]}",
                    same_rt=True,
                )
                suggestions.append(suggestion)
            
            # Suggest MH pairing if source has MH
            if record.mh_esi_prefix and record.mh_interfaces:
                suggestion = ConfigSuggestion(
                    suggestion_type="mh_pairing",
                    source_device=source_host,
                    target_device=hostname,
                    description=f"Pair multihoming with {source_host} (ESI: {record.mh_esi_prefix})",
                    same_esi=True,
                    next_step_hint="Same ESI will be used for Ethernet Segment pairing",
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def get_vpws_peer_suggestion(
        self, 
        hostname: str, 
        target_loopback: str
    ) -> Optional[Dict]:
        """
        Get EVPN-VPWS specific suggestion for point-to-point pairing.
        
        For EVPN-VPWS, the remote PE should have:
        - Same service count and naming
        - Same vpws-service-id (local=remote on both ends for P2P)
        - Same RT (for BGP peering)
        - Different RD (unique per PE)
        - Different parent interface
        
        Returns:
            Dict with suggestion details or None if no VPWS from other PE
        """
        other_devices = self.get_other_devices(hostname)
        
        for source_host in other_devices:
            record = self.device_records[source_host]
            
            for svc in record.configured_services:
                if svc.service_type == "evpn-vpws":
                    return {
                        'source_device': source_host,
                        'source_loopback': record.loopback_ip,
                        'service_count': svc.count,
                        'name_pattern': svc.name_pattern,
                        'start_index': svc.start_index,
                        'rt_asn': svc.rt_asn,
                        'rt_format': svc.rt_format,
                        'vpws_service_id_start': svc.vpws_service_id_start or 1,
                        'vpws_service_id_mode': svc.vpws_service_id_mode,
                        'transport': svc.transport,
                        'control_word': svc.control_word,
                        'fat_label': svc.fat_label,
                        'source_interfaces': svc.interfaces,
                        'source_parents': svc.parent_interfaces,
                        'target_rd': f"{target_loopback}:N",  # Use target loopback
                    }
        
        return None


# =============================================================================
# ROUTING POLICY MODELS
# =============================================================================

class PolicyRuleAction(str, Enum):
    """Policy rule action types."""
    ALLOW = "allow"
    DENY = "deny"


class PolicyMatchType(str, Enum):
    """Policy match condition types (DNOS 26.1)."""
    IPV4_PREFIX = "ipv4-prefix"
    IPV6_PREFIX = "ipv6-prefix"
    AS_PATH = "as-path"
    AS_PATH_LENGTH = "as-path-length"
    COMMUNITY = "community"
    EXTCOMMUNITY = "extcommunity"
    LARGE_COMMUNITY = "large-community"
    MED = "med"
    TAG = "tag"
    IPV4_NEXT_HOP = "ipv4-next-hop"
    IPV6_NEXT_HOP = "ipv6-next-hop"
    PATH_TYPE = "path-type"
    RPKI = "rpki"


class PolicySetActionType(str, Enum):
    """Policy set action types (DNOS 26.1)."""
    LOCAL_PREFERENCE = "local-preference"
    MED = "med"
    COMMUNITY = "community"
    EXTCOMMUNITY_RT = "extcommunity-rt"
    EXTCOMMUNITY_SOO = "extcommunity-soo"
    LARGE_COMMUNITY = "large-community"
    AS_PATH_PREPEND = "as-path-prepend"
    AS_PATH_EXCLUDE = "as-path-exclude"
    IPV4_NEXT_HOP = "ipv4-next-hop"
    IPV6_NEXT_HOP = "ipv6-next-hop"
    WEIGHT = "weight"
    TAG = "tag"


class PrefixListRuleModel(BaseModel):
    """A single rule in a prefix-list."""
    rule_id: int = Field(..., ge=1, le=299999, description="Rule ID")
    action: PolicyRuleAction = Field(default=PolicyRuleAction.ALLOW, description="Allow or deny")
    prefix: str = Field(..., description="IP prefix in CIDR format")
    ge: Optional[int] = Field(default=None, description="Matching length ge value")
    le: Optional[int] = Field(default=None, description="Matching length le value")
    eq: Optional[int] = Field(default=None, description="Matching length eq value")


class PrefixListModel(BaseModel):
    """Prefix-list configuration."""
    name: str = Field(..., description="Prefix-list name")
    ip_version: str = Field(default="ipv4", description="IPv4 or IPv6")
    rules: List[PrefixListRuleModel] = Field(default_factory=list, description="Prefix-list rules")
    description: Optional[str] = Field(default=None, description="Description")


class CommunityListRuleModel(BaseModel):
    """A single rule in a community-list."""
    rule_id: int = Field(..., ge=1, le=65534, description="Rule ID")
    action: PolicyRuleAction = Field(default=PolicyRuleAction.ALLOW, description="Allow or deny")
    match_type: str = Field(default="value", description="value, well-known, or regex")
    value: str = Field(..., description="Community value, well-known name, or regex")


class CommunityListModel(BaseModel):
    """Community-list configuration."""
    name: str = Field(..., description="Community-list name")
    rules: List[CommunityListRuleModel] = Field(default_factory=list, description="Community-list rules")
    description: Optional[str] = Field(default=None, description="Description")


class PolicyMatchConditionModel(BaseModel):
    """A match condition in a policy rule."""
    match_type: PolicyMatchType = Field(..., description="Type of match condition")
    value: str = Field(..., description="Match value or list name")


class PolicySetActionModel(BaseModel):
    """A set action in a policy rule."""
    action_type: PolicySetActionType = Field(..., description="Type of set action")
    value: str = Field(..., description="Value to set")
    extra: Optional[str] = Field(default=None, description="Extra parameter (e.g., additive)")


class PolicyRuleModel(BaseModel):
    """A single rule in a routing policy."""
    rule_id: int = Field(..., ge=1, le=65534, description="Rule ID")
    action: PolicyRuleAction = Field(default=PolicyRuleAction.ALLOW, description="Allow or deny")
    match_conditions: List[PolicyMatchConditionModel] = Field(
        default_factory=list, description="Match conditions (all must match)"
    )
    set_actions: List[PolicySetActionModel] = Field(
        default_factory=list, description="Set actions (only for allow rules)"
    )
    on_match: Optional[str] = Field(default=None, description="next, goto <rule>, or next-policy")
    call_policy: Optional[str] = Field(default=None, description="Policy to call after match")
    description: Optional[str] = Field(default=None, description="Rule description")


class RoutingPolicyModel(BaseModel):
    """Complete routing policy configuration."""
    name: str = Field(..., description="Policy name")
    rules: List[PolicyRuleModel] = Field(default_factory=list, description="Policy rules")
    description: Optional[str] = Field(default=None, description="Policy description")


class RoutingPolicyConfig(BaseModel):
    """Complete routing-policy hierarchy configuration."""
    prefix_lists_v4: List[PrefixListModel] = Field(
        default_factory=list, description="IPv4 prefix-lists"
    )
    prefix_lists_v6: List[PrefixListModel] = Field(
        default_factory=list, description="IPv6 prefix-lists"
    )
    community_lists: List[CommunityListModel] = Field(
        default_factory=list, description="Community-lists"
    )
    policies: List[RoutingPolicyModel] = Field(
        default_factory=list, description="Routing policies"
    )
    
    def get_all_policy_names(self) -> List[str]:
        """Get list of all policy names."""
        return [p.name for p in self.policies]
    
    def get_all_prefix_list_names(self) -> List[str]:
        """Get list of all prefix-list names."""
        return [pl.name for pl in self.prefix_lists_v4 + self.prefix_lists_v6]
    
    def get_all_community_list_names(self) -> List[str]:
        """Get list of all community-list names."""
        return [cl.name for cl in self.community_lists]

