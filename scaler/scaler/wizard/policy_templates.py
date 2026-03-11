"""
Policy Templates for the SCALER Wizard.

Pre-built policy templates with smart value suggestions for common use cases:
- BGP filtering (bogons, customer routes, peer routes)
- Community tagging and manipulation
- Local-preference and MED manipulation
- AS-path prepending
- Route-target filtering
- Blackhole/RTBH routing

Templates auto-populate values from:
- Current device config (ASN, router-id, prefix ranges)
- Wizard session state (previously configured values)
- Multi-device context (peer device configurations)
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from .policies import (
    PolicyManager, PrefixList, PrefixListRule, CommunityList, CommunityListRule,
    ExtCommunityList, ExtCommunityListRule, LargeCommunityList, LargeCommunityListRule,
    AsPathList, AsPathListRule, RoutingPolicy, PolicyRule, MatchCondition, SetAction,
    RuleAction, MatchType, SetActionType, OnMatchAction, WellKnownCommunity
)

console = Console()


@dataclass
class TemplateVariable:
    """A variable in a policy template that can be customized."""
    name: str
    description: str
    default_value: Any
    value_type: str  # "string", "int", "asn", "prefix", "community", "prefix_list"
    required: bool = True
    validator: Optional[Callable[[Any], Tuple[bool, str]]] = None


@dataclass
class PolicyTemplate:
    """A pre-built policy template."""
    name: str
    description: str
    use_case: str
    variables: List[TemplateVariable] = field(default_factory=list)
    builds_prefix_lists: bool = False
    builds_community_lists: bool = False
    builds_extcommunity_lists: bool = False
    builds_as_path_lists: bool = False
    builds_policies: bool = True
    
    def get_variable(self, var_name: str) -> Optional[TemplateVariable]:
        """Get a variable by name."""
        for var in self.variables:
            if var.name == var_name:
                return var
        return None
    
    def set_variable_default(self, var_name: str, value: Any) -> None:
        """Set a variable's default value (for smart suggestions)."""
        var = self.get_variable(var_name)
        if var:
            var.default_value = value


class PolicyTemplateEngine:
    """
    Engine for managing and applying policy templates.
    
    Provides:
    - Template catalog with all available templates
    - Smart value suggestion based on device config
    - Interactive template customization
    - Policy generation from templates
    """
    
    def __init__(self, device_asn: int = None, device_router_id: str = None):
        """
        Initialize template engine with optional device context.
        
        Args:
            device_asn: Device's BGP AS number (for smart defaults)
            device_router_id: Device's router ID (for smart defaults)
        """
        self.device_asn = device_asn
        self.device_router_id = device_router_id
        self.templates = self._build_template_catalog()
    
    def _build_template_catalog(self) -> Dict[str, PolicyTemplate]:
        """Build the catalog of available templates."""
        templates = {}
        
        # 1. DENY_BOGONS_V4 - Filter RFC1918 and bogon prefixes
        templates['DENY_BOGONS_V4'] = PolicyTemplate(
            name="DENY_BOGONS_V4",
            description="Filter IPv4 bogons and RFC1918 private addresses",
            use_case="Prevent bogon routes from entering your network",
            variables=[
                TemplateVariable("prefix_list_name", "Prefix-list name", "PL_BOGONS_V4", "string"),
                TemplateVariable("policy_name", "Policy name", "DENY_BOGONS_V4", "string"),
            ],
            builds_prefix_lists=True,
            builds_policies=True
        )
        
        # 2. DENY_BOGONS_V6 - Filter IPv6 bogons
        templates['DENY_BOGONS_V6'] = PolicyTemplate(
            name="DENY_BOGONS_V6",
            description="Filter IPv6 bogon and documentation prefixes",
            use_case="Prevent IPv6 bogon routes from entering your network",
            variables=[
                TemplateVariable("prefix_list_name", "Prefix-list name", "PL_BOGONS_V6", "string"),
                TemplateVariable("policy_name", "Policy name", "DENY_BOGONS_V6", "string"),
            ],
            builds_prefix_lists=True,
            builds_policies=True
        )
        
        # 3. CUSTOMER_IMPORT - Accept routes from customer
        templates['CUSTOMER_IMPORT'] = PolicyTemplate(
            name="CUSTOMER_IMPORT",
            description="Accept and tag routes from a customer BGP peer",
            use_case="Inbound policy for customer BGP sessions",
            variables=[
                TemplateVariable("customer_name", "Customer identifier", "CUST1", "string"),
                TemplateVariable("customer_asn", "Customer ASN", 65001, "asn"),
                TemplateVariable("customer_prefixes", "Customer prefix (CIDR)", "10.0.0.0/8", "prefix"),
                TemplateVariable("local_pref", "Local preference to set", 100, "int"),
                TemplateVariable("tag_community", "Community tag to add", None, "community"),
            ],
            builds_prefix_lists=True,
            builds_community_lists=True,
            builds_as_path_lists=True,
            builds_policies=True
        )
        
        # 4. CUSTOMER_EXPORT - Advertise routes to customer
        templates['CUSTOMER_EXPORT'] = PolicyTemplate(
            name="CUSTOMER_EXPORT",
            description="Advertise selected routes to a customer BGP peer",
            use_case="Outbound policy for customer BGP sessions",
            variables=[
                TemplateVariable("customer_name", "Customer identifier", "CUST1", "string"),
                TemplateVariable("advertise_default", "Advertise default route", True, "bool"),
                TemplateVariable("advertise_summary", "Advertise summary routes only", True, "bool"),
            ],
            builds_prefix_lists=True,
            builds_policies=True
        )
        
        # 5. PEER_IMPORT - Accept routes from peering partner
        templates['PEER_IMPORT'] = PolicyTemplate(
            name="PEER_IMPORT",
            description="Accept routes from a peering partner with AS-path filtering",
            use_case="Inbound policy for peering BGP sessions",
            variables=[
                TemplateVariable("peer_name", "Peer identifier", "PEER1", "string"),
                TemplateVariable("peer_asn", "Peer ASN", 65002, "asn"),
                TemplateVariable("local_pref", "Local preference to set", 80, "int"),
                TemplateVariable("max_prefix_len", "Maximum prefix length to accept", 24, "int"),
            ],
            builds_as_path_lists=True,
            builds_policies=True
        )
        
        # 6. PEER_EXPORT - Advertise routes to peering partner
        templates['PEER_EXPORT'] = PolicyTemplate(
            name="PEER_EXPORT",
            description="Advertise routes to a peering partner",
            use_case="Outbound policy for peering BGP sessions",
            variables=[
                TemplateVariable("peer_name", "Peer identifier", "PEER1", "string"),
                TemplateVariable("export_community", "Community to match for export", None, "community"),
            ],
            builds_community_lists=True,
            builds_policies=True
        )
        
        # 7. TRANSIT_IMPORT - Accept routes from transit provider
        templates['TRANSIT_IMPORT'] = PolicyTemplate(
            name="TRANSIT_IMPORT",
            description="Accept routes from a transit provider",
            use_case="Inbound policy for transit BGP sessions",
            variables=[
                TemplateVariable("transit_name", "Transit provider identifier", "TRANSIT1", "string"),
                TemplateVariable("transit_asn", "Transit ASN", 65003, "asn"),
                TemplateVariable("local_pref", "Local preference to set", 50, "int"),
            ],
            builds_as_path_lists=True,
            builds_policies=True
        )
        
        # 8. TRANSIT_EXPORT - Advertise routes to transit provider
        templates['TRANSIT_EXPORT'] = PolicyTemplate(
            name="TRANSIT_EXPORT",
            description="Advertise routes to a transit provider",
            use_case="Outbound policy for transit BGP sessions",
            variables=[
                TemplateVariable("transit_name", "Transit provider identifier", "TRANSIT1", "string"),
                TemplateVariable("prepend_count", "AS-path prepend count", 0, "int"),
            ],
            builds_community_lists=True,
            builds_policies=True
        )
        
        # 9. LOCAL_PREF_BY_COMMUNITY - Set local-pref based on community
        templates['LOCAL_PREF_BY_COMMUNITY'] = PolicyTemplate(
            name="LOCAL_PREF_BY_COMMUNITY",
            description="Set local-preference based on incoming community",
            use_case="Implement community-based traffic engineering",
            variables=[
                TemplateVariable("high_pref_community", "Community for high preference", "65000:100", "community"),
                TemplateVariable("high_pref_value", "High local-preference value", 150, "int"),
                TemplateVariable("low_pref_community", "Community for low preference", "65000:50", "community"),
                TemplateVariable("low_pref_value", "Low local-preference value", 50, "int"),
            ],
            builds_community_lists=True,
            builds_policies=True
        )
        
        # 10. MED_MANIPULATION - Set/modify MED values
        templates['MED_MANIPULATION'] = PolicyTemplate(
            name="MED_MANIPULATION",
            description="Set or modify MED for outbound routes",
            use_case="Control inbound traffic from external peers",
            variables=[
                TemplateVariable("policy_name", "Policy name", "SET_MED", "string"),
                TemplateVariable("med_value", "MED value to set", 100, "int"),
                TemplateVariable("use_igp_cost", "Use IGP cost as MED", False, "bool"),
            ],
            builds_policies=True
        )
        
        # 11. AS_PREPEND - AS-path prepending
        templates['AS_PREPEND'] = PolicyTemplate(
            name="AS_PREPEND",
            description="Prepend AS-path for traffic engineering",
            use_case="Control inbound traffic by making path longer",
            variables=[
                TemplateVariable("policy_name", "Policy name", "AS_PREPEND", "string"),
                TemplateVariable("prepend_count", "Number of times to prepend", 2, "int"),
                TemplateVariable("match_community", "Community to match (optional)", None, "community"),
            ],
            builds_community_lists=True,
            builds_policies=True
        )
        
        # 12. COMMUNITY_TAG - Tag routes with community
        templates['COMMUNITY_TAG'] = PolicyTemplate(
            name="COMMUNITY_TAG",
            description="Tag all routes with a specific community",
            use_case="Mark routes for downstream processing",
            variables=[
                TemplateVariable("policy_name", "Policy name", "TAG_ROUTES", "string"),
                TemplateVariable("community_value", "Community to add", "65000:1000", "community"),
                TemplateVariable("additive", "Add to existing communities", True, "bool"),
            ],
            builds_policies=True
        )
        
        # 13. RT_FILTER - Filter by route-target
        templates['RT_FILTER'] = PolicyTemplate(
            name="RT_FILTER",
            description="Filter routes based on route-target extended community",
            use_case="Control VRF route import/export",
            variables=[
                TemplateVariable("policy_name", "Policy name", "RT_FILTER", "string"),
                TemplateVariable("route_target", "Route-target to match", "65000:100", "community"),
                TemplateVariable("action", "Action (allow/deny)", "allow", "string"),
            ],
            builds_extcommunity_lists=True,
            builds_policies=True
        )
        
        # 14. BLACKHOLE - Blackhole/RTBH routing
        templates['BLACKHOLE'] = PolicyTemplate(
            name="BLACKHOLE",
            description="Remote Triggered Blackhole (RTBH) policy",
            use_case="DDoS mitigation via BGP blackholing",
            variables=[
                TemplateVariable("policy_name", "Policy name", "RTBH", "string"),
                TemplateVariable("blackhole_community", "Blackhole community", "65535:666", "community"),
                TemplateVariable("blackhole_next_hop", "Blackhole next-hop", "192.0.2.1", "string"),
            ],
            builds_community_lists=True,
            builds_policies=True
        )
        
        return templates
    
    def list_templates(self) -> None:
        """Display all available templates in a table."""
        table = Table(title="Available Policy Templates", show_header=True)
        table.add_column("Name", style="cyan", width=25)
        table.add_column("Description", width=40)
        table.add_column("Use Case", width=35)
        
        for name, template in sorted(self.templates.items()):
            table.add_row(name, template.description, template.use_case)
        
        console.print(table)
    
    def get_template(self, name: str) -> Optional[PolicyTemplate]:
        """Get a template by name."""
        return self.templates.get(name)
    
    def apply_smart_defaults(self, template: PolicyTemplate, 
                             device_config: str = None,
                             wizard_state: Any = None) -> None:
        """
        Apply smart defaults to template variables based on context.
        
        Args:
            template: The template to update
            device_config: Raw device configuration text
            wizard_state: WizardState object with session data
        """
        # Apply device ASN if available
        if self.device_asn:
            for var in template.variables:
                if var.value_type == "community" and var.default_value:
                    # Update ASN in community defaults
                    if ':' in str(var.default_value):
                        parts = str(var.default_value).split(':')
                        if parts[0].isdigit():
                            var.default_value = f"{self.device_asn}:{parts[1]}"
        
        # Extract ASN from device config if not provided
        if device_config and not self.device_asn:
            import re
            asn_match = re.search(r'bgp\s+(\d+)', device_config)
            if asn_match:
                self.device_asn = int(asn_match.group(1))
    
    def customize_template(self, template: PolicyTemplate) -> Dict[str, Any]:
        """
        Interactively customize template variables.
        
        Args:
            template: The template to customize
            
        Returns:
            Dict of variable name -> customized value
        """
        console.print(f"\n[bold cyan]Template: {template.name}[/bold cyan]")
        console.print(f"[dim]{template.description}[/dim]\n")
        
        values = {}
        for var in template.variables:
            # Build prompt with type hint
            type_hint = ""
            if var.value_type == "asn":
                type_hint = " (AS number)"
            elif var.value_type == "prefix":
                type_hint = " (CIDR format)"
            elif var.value_type == "community":
                type_hint = " (AS:ID format)"
            elif var.value_type == "int":
                type_hint = " (number)"
            
            prompt_text = f"  {var.description}{type_hint}"
            
            if var.value_type == "bool":
                value = Confirm.ask(prompt_text, default=var.default_value)
            else:
                default_str = str(var.default_value) if var.default_value is not None else ""
                value = Prompt.ask(prompt_text, default=default_str)
                
                # Convert to appropriate type
                if var.value_type == "int" or var.value_type == "asn":
                    try:
                        value = int(value) if value else var.default_value
                    except ValueError:
                        value = var.default_value
            
            values[var.name] = value
        
        return values
    
    def generate_from_template(self, template_name: str, 
                               values: Dict[str, Any] = None) -> PolicyManager:
        """
        Generate policies from a template.
        
        Args:
            template_name: Name of the template to use
            values: Customized variable values
            
        Returns:
            PolicyManager with generated policies
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        manager = PolicyManager()
        
        # Use default values if not provided
        if values is None:
            values = {var.name: var.default_value for var in template.variables}
        
        # Generate based on template type
        if template_name == 'DENY_BOGONS_V4':
            self._generate_deny_bogons_v4(manager, values)
        elif template_name == 'DENY_BOGONS_V6':
            self._generate_deny_bogons_v6(manager, values)
        elif template_name == 'CUSTOMER_IMPORT':
            self._generate_customer_import(manager, values)
        elif template_name == 'CUSTOMER_EXPORT':
            self._generate_customer_export(manager, values)
        elif template_name == 'PEER_IMPORT':
            self._generate_peer_import(manager, values)
        elif template_name == 'PEER_EXPORT':
            self._generate_peer_export(manager, values)
        elif template_name == 'TRANSIT_IMPORT':
            self._generate_transit_import(manager, values)
        elif template_name == 'TRANSIT_EXPORT':
            self._generate_transit_export(manager, values)
        elif template_name == 'LOCAL_PREF_BY_COMMUNITY':
            self._generate_local_pref_by_community(manager, values)
        elif template_name == 'MED_MANIPULATION':
            self._generate_med_manipulation(manager, values)
        elif template_name == 'AS_PREPEND':
            self._generate_as_prepend(manager, values)
        elif template_name == 'COMMUNITY_TAG':
            self._generate_community_tag(manager, values)
        elif template_name == 'RT_FILTER':
            self._generate_rt_filter(manager, values)
        elif template_name == 'BLACKHOLE':
            self._generate_blackhole(manager, values)
        
        return manager
    
    def _generate_deny_bogons_v4(self, manager: PolicyManager, values: Dict[str, Any]) -> None:
        """Generate DENY_BOGONS_V4 template."""
        pl_name = values.get('prefix_list_name', 'PL_BOGONS_V4')
        pol_name = values.get('policy_name', 'DENY_BOGONS_V4')
        
        # Common IPv4 bogons
        bogons = [
            ("0.0.0.0/8", None, None),          # "This" network
            ("10.0.0.0/8", None, None),         # RFC1918
            ("100.64.0.0/10", None, None),      # Shared address space
            ("127.0.0.0/8", None, None),        # Loopback
            ("169.254.0.0/16", None, None),     # Link-local
            ("172.16.0.0/12", None, None),      # RFC1918
            ("192.0.0.0/24", None, None),       # IETF Protocol
            ("192.0.2.0/24", None, None),       # TEST-NET-1
            ("192.168.0.0/16", None, None),     # RFC1918
            ("198.18.0.0/15", None, None),      # Benchmarking
            ("198.51.100.0/24", None, None),    # TEST-NET-2
            ("203.0.113.0/24", None, None),     # TEST-NET-3
            ("224.0.0.0/4", None, None),        # Multicast
            ("240.0.0.0/4", None, None),        # Reserved
        ]
        
        # Create prefix-list
        rules = []
        for i, (prefix, ge, le) in enumerate(bogons, start=1):
            rules.append(PrefixListRule(
                rule_id=i * 10,
                action=RuleAction.ALLOW,
                prefix=prefix,
                ge=ge,
                le=le
            ))
        
        manager.add_prefix_list(PrefixList(
            name=pl_name,
            ip_version="ipv4",
            rules=rules,
            description="IPv4 bogon and RFC1918 prefixes"
        ))
        
        # Create policy
        manager.add_policy(RoutingPolicy(
            name=pol_name,
            rules=[
                PolicyRule(
                    rule_id=10,
                    action=RuleAction.DENY,
                    match_conditions=[
                        MatchCondition(match_type=MatchType.IPV4_PREFIX, value=pl_name)
                    ],
                    description="Deny bogon prefixes"
                ),
                PolicyRule(
                    rule_id=20,
                    action=RuleAction.ALLOW,
                    description="Allow everything else"
                )
            ],
            description="Deny IPv4 bogon prefixes"
        ))
    
    def _generate_deny_bogons_v6(self, manager: PolicyManager, values: Dict[str, Any]) -> None:
        """Generate DENY_BOGONS_V6 template."""
        pl_name = values.get('prefix_list_name', 'PL_BOGONS_V6')
        pol_name = values.get('policy_name', 'DENY_BOGONS_V6')
        
        # Common IPv6 bogons
        bogons = [
            ("::/8", None, None),               # Loopback, unspecified, v4-compat
            ("100::/64", None, None),           # Discard-only
            ("2001:2::/48", None, None),        # Benchmarking
            ("2001:10::/28", None, None),       # ORCHID
            ("2001:db8::/32", None, None),      # Documentation
            ("fc00::/7", None, None),           # Unique local
            ("fe80::/10", None, None),          # Link-local
            ("fec0::/10", None, None),          # Site-local (deprecated)
            ("ff00::/8", None, None),           # Multicast
        ]
        
        # Create prefix-list
        rules = []
        for i, (prefix, ge, le) in enumerate(bogons, start=1):
            rules.append(PrefixListRule(
                rule_id=i * 10,
                action=RuleAction.ALLOW,
                prefix=prefix,
                ge=ge,
                le=le
            ))
        
        manager.add_prefix_list(PrefixList(
            name=pl_name,
            ip_version="ipv6",
            rules=rules,
            description="IPv6 bogon and documentation prefixes"
        ))
        
        # Create policy
        manager.add_policy(RoutingPolicy(
            name=pol_name,
            rules=[
                PolicyRule(
                    rule_id=10,
                    action=RuleAction.DENY,
                    match_conditions=[
                        MatchCondition(match_type=MatchType.IPV6_PREFIX, value=pl_name)
                    ],
                    description="Deny bogon prefixes"
                ),
                PolicyRule(
                    rule_id=20,
                    action=RuleAction.ALLOW,
                    description="Allow everything else"
                )
            ],
            description="Deny IPv6 bogon prefixes"
        ))
    
    def _generate_customer_import(self, manager: PolicyManager, values: Dict[str, Any]) -> None:
        """Generate CUSTOMER_IMPORT template."""
        customer_name = values.get('customer_name', 'CUST1')
        customer_asn = values.get('customer_asn', 65001)
        customer_prefix = values.get('customer_prefixes', '10.0.0.0/8')
        local_pref = values.get('local_pref', 100)
        tag_community = values.get('tag_community')
        
        pl_name = f"PL_{customer_name}_V4"
        asp_name = f"ASP_{customer_name}"
        pol_name = f"IMPORT_{customer_name}"
        
        # Create prefix-list for customer routes
        manager.add_prefix_list(PrefixList(
            name=pl_name,
            ip_version="ipv4",
            rules=[
                PrefixListRule(
                    rule_id=10,
                    action=RuleAction.ALLOW,
                    prefix=customer_prefix,
                    ge=8,
                    le=24
                )
            ],
            description=f"Allowed prefixes for customer {customer_name}"
        ))
        
        # Create AS-path list to match customer origin
        manager.add_as_path_list(AsPathList(
            name=asp_name,
            rules=[
                AsPathListRule(
                    rule_id=10,
                    action=RuleAction.ALLOW,
                    match_type="regex",
                    value=f"^{customer_asn}_"
                )
            ],
            description=f"Match routes originated by AS{customer_asn}"
        ))
        
        # Build set actions
        set_actions = [
            SetAction(action_type=SetActionType.LOCAL_PREFERENCE, value=str(local_pref))
        ]
        if tag_community:
            set_actions.append(SetAction(
                action_type=SetActionType.COMMUNITY,
                value=tag_community,
                extra="additive"
            ))
        
        # Create policy
        manager.add_policy(RoutingPolicy(
            name=pol_name,
            rules=[
                PolicyRule(
                    rule_id=10,
                    action=RuleAction.ALLOW,
                    match_conditions=[
                        MatchCondition(match_type=MatchType.IPV4_PREFIX, value=pl_name),
                        MatchCondition(match_type=MatchType.AS_PATH, value=asp_name)
                    ],
                    set_actions=set_actions,
                    description=f"Accept routes from customer {customer_name}"
                ),
                PolicyRule(
                    rule_id=100,
                    action=RuleAction.DENY,
                    description="Deny all other routes"
                )
            ],
            description=f"Import policy for customer {customer_name}"
        ))
    
    def _generate_customer_export(self, manager: PolicyManager, values: Dict[str, Any]) -> None:
        """Generate CUSTOMER_EXPORT template."""
        customer_name = values.get('customer_name', 'CUST1')
        advertise_default = values.get('advertise_default', True)
        advertise_summary = values.get('advertise_summary', True)
        
        pol_name = f"EXPORT_{customer_name}"
        
        rules = []
        rule_id = 10
        
        if advertise_default:
            # Use default-originate at neighbor level, not in policy
            pass
        
        # Allow all (or use more restrictive export)
        rules.append(PolicyRule(
            rule_id=rule_id,
            action=RuleAction.ALLOW,
            description=f"Advertise routes to customer {customer_name}"
        ))
        
        manager.add_policy(RoutingPolicy(
            name=pol_name,
            rules=rules,
            description=f"Export policy for customer {customer_name}"
        ))
    
    def _generate_peer_import(self, manager: PolicyManager, values: Dict[str, Any]) -> None:
        """Generate PEER_IMPORT template."""
        peer_name = values.get('peer_name', 'PEER1')
        peer_asn = values.get('peer_asn', 65002)
        local_pref = values.get('local_pref', 80)
        max_prefix_len = values.get('max_prefix_len', 24)
        
        asp_name = f"ASP_{peer_name}"
        pol_name = f"IMPORT_{peer_name}"
        
        # Create AS-path list
        manager.add_as_path_list(AsPathList(
            name=asp_name,
            rules=[
                AsPathListRule(
                    rule_id=10,
                    action=RuleAction.ALLOW,
                    match_type="passes-through",
                    value=str(peer_asn)
                )
            ],
            description=f"Match routes passing through AS{peer_asn}"
        ))
        
        # Create policy
        manager.add_policy(RoutingPolicy(
            name=pol_name,
            rules=[
                PolicyRule(
                    rule_id=10,
                    action=RuleAction.ALLOW,
                    match_conditions=[
                        MatchCondition(match_type=MatchType.AS_PATH, value=asp_name)
                    ],
                    set_actions=[
                        SetAction(action_type=SetActionType.LOCAL_PREFERENCE, value=str(local_pref))
                    ],
                    description=f"Accept routes from peer {peer_name}"
                ),
                PolicyRule(
                    rule_id=100,
                    action=RuleAction.DENY,
                    description="Deny routes not from peer AS"
                )
            ],
            description=f"Import policy for peer {peer_name}"
        ))
    
    def _generate_peer_export(self, manager: PolicyManager, values: Dict[str, Any]) -> None:
        """Generate PEER_EXPORT template."""
        peer_name = values.get('peer_name', 'PEER1')
        export_community = values.get('export_community')
        
        pol_name = f"EXPORT_{peer_name}"
        
        rules = []
        
        if export_community:
            cl_name = f"CL_EXPORT_{peer_name}"
            manager.add_community_list(CommunityList(
                name=cl_name,
                rules=[
                    CommunityListRule(
                        rule_id=10,
                        action=RuleAction.ALLOW,
                        match_type="value",
                        value=export_community
                    )
                ],
                description=f"Match routes to export to peer {peer_name}"
            ))
            
            rules.append(PolicyRule(
                rule_id=10,
                action=RuleAction.ALLOW,
                match_conditions=[
                    MatchCondition(match_type=MatchType.COMMUNITY, value=cl_name)
                ],
                description=f"Export tagged routes to peer {peer_name}"
            ))
            rules.append(PolicyRule(
                rule_id=100,
                action=RuleAction.DENY,
                description="Deny all other routes"
            ))
        else:
            rules.append(PolicyRule(
                rule_id=10,
                action=RuleAction.ALLOW,
                description=f"Export routes to peer {peer_name}"
            ))
        
        manager.add_policy(RoutingPolicy(
            name=pol_name,
            rules=rules,
            description=f"Export policy for peer {peer_name}"
        ))
    
    def _generate_transit_import(self, manager: PolicyManager, values: Dict[str, Any]) -> None:
        """Generate TRANSIT_IMPORT template."""
        transit_name = values.get('transit_name', 'TRANSIT1')
        transit_asn = values.get('transit_asn', 65003)
        local_pref = values.get('local_pref', 50)
        
        asp_name = f"ASP_{transit_name}"
        pol_name = f"IMPORT_{transit_name}"
        
        # Create AS-path list
        manager.add_as_path_list(AsPathList(
            name=asp_name,
            rules=[
                AsPathListRule(
                    rule_id=10,
                    action=RuleAction.ALLOW,
                    match_type="regex",
                    value=f"^{transit_asn}_"
                )
            ],
            description=f"Match routes from transit AS{transit_asn}"
        ))
        
        # Create policy
        manager.add_policy(RoutingPolicy(
            name=pol_name,
            rules=[
                PolicyRule(
                    rule_id=10,
                    action=RuleAction.ALLOW,
                    set_actions=[
                        SetAction(action_type=SetActionType.LOCAL_PREFERENCE, value=str(local_pref))
                    ],
                    description=f"Accept all routes from transit {transit_name}"
                )
            ],
            description=f"Import policy for transit {transit_name}"
        ))
    
    def _generate_transit_export(self, manager: PolicyManager, values: Dict[str, Any]) -> None:
        """Generate TRANSIT_EXPORT template."""
        transit_name = values.get('transit_name', 'TRANSIT1')
        prepend_count = values.get('prepend_count', 0)
        
        pol_name = f"EXPORT_{transit_name}"
        
        set_actions = []
        if prepend_count and prepend_count > 0:
            set_actions.append(SetAction(
                action_type=SetActionType.AS_PATH_PREPEND,
                value=str(prepend_count),
                extra="last-as"
            ))
        
        manager.add_policy(RoutingPolicy(
            name=pol_name,
            rules=[
                PolicyRule(
                    rule_id=10,
                    action=RuleAction.ALLOW,
                    set_actions=set_actions,
                    description=f"Export routes to transit {transit_name}"
                )
            ],
            description=f"Export policy for transit {transit_name}"
        ))
    
    def _generate_local_pref_by_community(self, manager: PolicyManager, values: Dict[str, Any]) -> None:
        """Generate LOCAL_PREF_BY_COMMUNITY template."""
        high_comm = values.get('high_pref_community', '65000:100')
        high_pref = values.get('high_pref_value', 150)
        low_comm = values.get('low_pref_community', '65000:50')
        low_pref = values.get('low_pref_value', 50)
        
        # Create community lists
        manager.add_community_list(CommunityList(
            name="CL_HIGH_PREF",
            rules=[
                CommunityListRule(rule_id=10, action=RuleAction.ALLOW, match_type="value", value=high_comm)
            ],
            description="Match high preference community"
        ))
        
        manager.add_community_list(CommunityList(
            name="CL_LOW_PREF",
            rules=[
                CommunityListRule(rule_id=10, action=RuleAction.ALLOW, match_type="value", value=low_comm)
            ],
            description="Match low preference community"
        ))
        
        # Create policy
        manager.add_policy(RoutingPolicy(
            name="LOCAL_PREF_BY_COMMUNITY",
            rules=[
                PolicyRule(
                    rule_id=10,
                    action=RuleAction.ALLOW,
                    match_conditions=[
                        MatchCondition(match_type=MatchType.COMMUNITY, value="CL_HIGH_PREF")
                    ],
                    set_actions=[
                        SetAction(action_type=SetActionType.LOCAL_PREFERENCE, value=str(high_pref))
                    ],
                    on_match=OnMatchAction.NEXT,
                    description="Set high local-pref for tagged routes"
                ),
                PolicyRule(
                    rule_id=20,
                    action=RuleAction.ALLOW,
                    match_conditions=[
                        MatchCondition(match_type=MatchType.COMMUNITY, value="CL_LOW_PREF")
                    ],
                    set_actions=[
                        SetAction(action_type=SetActionType.LOCAL_PREFERENCE, value=str(low_pref))
                    ],
                    description="Set low local-pref for tagged routes"
                ),
                PolicyRule(
                    rule_id=100,
                    action=RuleAction.ALLOW,
                    description="Allow remaining routes"
                )
            ],
            description="Set local-preference based on community"
        ))
    
    def _generate_med_manipulation(self, manager: PolicyManager, values: Dict[str, Any]) -> None:
        """Generate MED_MANIPULATION template."""
        pol_name = values.get('policy_name', 'SET_MED')
        med_value = values.get('med_value', 100)
        use_igp = values.get('use_igp_cost', False)
        
        if use_igp:
            med_set = SetAction(action_type=SetActionType.MED, value="igp-cost")
        else:
            med_set = SetAction(action_type=SetActionType.MED, value=str(med_value))
        
        manager.add_policy(RoutingPolicy(
            name=pol_name,
            rules=[
                PolicyRule(
                    rule_id=10,
                    action=RuleAction.ALLOW,
                    set_actions=[med_set],
                    description="Set MED on all routes"
                )
            ],
            description="Set MED for outbound routes"
        ))
    
    def _generate_as_prepend(self, manager: PolicyManager, values: Dict[str, Any]) -> None:
        """Generate AS_PREPEND template."""
        pol_name = values.get('policy_name', 'AS_PREPEND')
        prepend_count = values.get('prepend_count', 2)
        match_community = values.get('match_community')
        
        match_conditions = []
        
        if match_community:
            cl_name = "CL_PREPEND"
            manager.add_community_list(CommunityList(
                name=cl_name,
                rules=[
                    CommunityListRule(rule_id=10, action=RuleAction.ALLOW, match_type="value", value=match_community)
                ],
                description="Match routes for AS prepend"
            ))
            match_conditions.append(MatchCondition(match_type=MatchType.COMMUNITY, value=cl_name))
        
        manager.add_policy(RoutingPolicy(
            name=pol_name,
            rules=[
                PolicyRule(
                    rule_id=10,
                    action=RuleAction.ALLOW,
                    match_conditions=match_conditions,
                    set_actions=[
                        SetAction(
                            action_type=SetActionType.AS_PATH_PREPEND,
                            value=str(prepend_count),
                            extra="last-as"
                        )
                    ],
                    description=f"Prepend AS {prepend_count} times"
                )
            ],
            description="AS-path prepending policy"
        ))
    
    def _generate_community_tag(self, manager: PolicyManager, values: Dict[str, Any]) -> None:
        """Generate COMMUNITY_TAG template."""
        pol_name = values.get('policy_name', 'TAG_ROUTES')
        community = values.get('community_value', '65000:1000')
        additive = values.get('additive', True)
        
        manager.add_policy(RoutingPolicy(
            name=pol_name,
            rules=[
                PolicyRule(
                    rule_id=10,
                    action=RuleAction.ALLOW,
                    set_actions=[
                        SetAction(
                            action_type=SetActionType.COMMUNITY,
                            value=community,
                            extra="additive" if additive else None
                        )
                    ],
                    description=f"Tag routes with community {community}"
                )
            ],
            description="Tag all routes with community"
        ))
    
    def _generate_rt_filter(self, manager: PolicyManager, values: Dict[str, Any]) -> None:
        """Generate RT_FILTER template."""
        pol_name = values.get('policy_name', 'RT_FILTER')
        route_target = values.get('route_target', '65000:100')
        action = values.get('action', 'allow')
        
        ecl_name = "ECL_RT_FILTER"
        manager.add_extcommunity_list(ExtCommunityList(
            name=ecl_name,
            rules=[
                ExtCommunityListRule(
                    rule_id=10,
                    action=RuleAction.ALLOW,
                    ext_type="rt",
                    match_type="value",
                    value=route_target
                )
            ],
            description=f"Match route-target {route_target}"
        ))
        
        if action.lower() == 'allow':
            rules = [
                PolicyRule(
                    rule_id=10,
                    action=RuleAction.ALLOW,
                    match_conditions=[
                        MatchCondition(match_type=MatchType.EXTCOMMUNITY, value=ecl_name)
                    ],
                    description=f"Allow routes with RT {route_target}"
                ),
                PolicyRule(
                    rule_id=100,
                    action=RuleAction.DENY,
                    description="Deny all other routes"
                )
            ]
        else:
            rules = [
                PolicyRule(
                    rule_id=10,
                    action=RuleAction.DENY,
                    match_conditions=[
                        MatchCondition(match_type=MatchType.EXTCOMMUNITY, value=ecl_name)
                    ],
                    description=f"Deny routes with RT {route_target}"
                ),
                PolicyRule(
                    rule_id=100,
                    action=RuleAction.ALLOW,
                    description="Allow all other routes"
                )
            ]
        
        manager.add_policy(RoutingPolicy(
            name=pol_name,
            rules=rules,
            description=f"Filter routes by route-target {route_target}"
        ))
    
    def _generate_blackhole(self, manager: PolicyManager, values: Dict[str, Any]) -> None:
        """Generate BLACKHOLE template."""
        pol_name = values.get('policy_name', 'RTBH')
        blackhole_comm = values.get('blackhole_community', '65535:666')
        blackhole_nh = values.get('blackhole_next_hop', '192.0.2.1')
        
        cl_name = "CL_BLACKHOLE"
        manager.add_community_list(CommunityList(
            name=cl_name,
            rules=[
                CommunityListRule(
                    rule_id=10,
                    action=RuleAction.ALLOW,
                    match_type="value",
                    value=blackhole_comm
                )
            ],
            description="Match blackhole community"
        ))
        
        manager.add_policy(RoutingPolicy(
            name=pol_name,
            rules=[
                PolicyRule(
                    rule_id=10,
                    action=RuleAction.ALLOW,
                    match_conditions=[
                        MatchCondition(match_type=MatchType.COMMUNITY, value=cl_name)
                    ],
                    set_actions=[
                        SetAction(action_type=SetActionType.IPV4_NEXT_HOP, value=blackhole_nh),
                        SetAction(action_type=SetActionType.LOCAL_PREFERENCE, value="999999")
                    ],
                    description="Apply blackhole treatment"
                ),
                PolicyRule(
                    rule_id=100,
                    action=RuleAction.ALLOW,
                    description="Allow normal routes"
                )
            ],
            description="Remote Triggered Blackhole (RTBH) policy"
        ))
