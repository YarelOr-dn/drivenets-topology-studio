"""
Advanced Policy Creation Engine for the SCALER Wizard.

This module provides a comprehensive routing-policy management system including:
- PolicyManager: Central manager for all policy operations
- Building Block Classes: PrefixListBuilder, CommunityListBuilder, etc.
- PolicyBuilder: Full policy creation with rules, match, set, and control flow

DNOS 26.1 Policy Language Reference:
- Match conditions: ipv4/ipv6 prefix, as-path, as-path-length, community,
  extcommunity, large-community, med, tag, next-hop prefix-list,
  path-type (ebgp/ibgp), rpki, rib-has-route
- Set actions: local-preference, med, community, extcommunity, large-community,
  as-path prepend/exclude, next-hop, weight, atomic-aggregate, tag, ospf-metric,
  isis-metric, metric-type, aigp, path-mark, forwarding-action
- Control flow: on-match (next/goto/next-policy), call policy
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from .core import BackException, StepNavigator, TopException, show_breadcrumb, set_path

console = Console()


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class RuleAction(str, Enum):
    """Rule action types."""
    ALLOW = "allow"
    DENY = "deny"


class MatchType(str, Enum):
    """Match condition types (DNOS 26.1)."""
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
    RIB_HAS_ROUTE = "rib-has-route"
    PATH_MARK_COUNT = "path-mark-count"


class SetActionType(str, Enum):
    """Set action types (DNOS 26.1)."""
    LOCAL_PREFERENCE = "local-preference"
    MED = "med"
    COMMUNITY = "community"
    COMMUNITY_LIST = "community-list"
    EXTCOMMUNITY_RT = "extcommunity-rt"
    EXTCOMMUNITY_SOO = "extcommunity-soo"
    EXTCOMMUNITY_COLOR = "extcommunity-color"
    EXTCOMMUNITY_LIST = "extcommunity-list"
    LARGE_COMMUNITY = "large-community"
    LARGE_COMMUNITY_LIST = "large-community-list"
    AS_PATH_PREPEND = "as-path-prepend"
    AS_PATH_EXCLUDE = "as-path-exclude"
    IPV4_NEXT_HOP = "ipv4-next-hop"
    IPV6_NEXT_HOP = "ipv6-next-hop"
    WEIGHT = "weight"
    ATOMIC_AGGREGATE = "atomic-aggregate"
    TAG = "tag"
    OSPF_METRIC = "ospf-metric"
    ISIS_METRIC = "isis-metric"
    METRIC_TYPE = "metric-type"
    AIGP = "aigp"
    PATH_MARK = "path-mark"
    FORWARDING_ACTION = "forwarding-action"


class OnMatchAction(str, Enum):
    """On-match control flow actions."""
    NEXT = "next"
    GOTO = "goto"
    NEXT_POLICY = "next-policy"


class WellKnownCommunity(str, Enum):
    """Well-known BGP communities."""
    INTERNET = "internet"
    ACCEPT_OWN = "accept-own"
    LOCAL_AS = "local-AS"
    NO_EXPORT = "no-export"
    NO_ADVERTISE = "no-advertise"
    NO_LLGR = "no-LLGR"
    LLGR_STALE = "LLGR-stale"


class PathType(str, Enum):
    """BGP path types for matching."""
    EBGP = "ebgp"
    IBGP = "ibgp"


class RPKIState(str, Enum):
    """RPKI validation states."""
    VALID = "valid"
    INVALID = "invalid"
    NOT_FOUND = "not-found"


class MetricType(str, Enum):
    """OSPF metric types."""
    TYPE1 = "type1"
    TYPE2 = "type2"


class ListOperation(str, Enum):
    """Operations for community-list/extcommunity-list set actions."""
    DELETE = "delete"
    DELETE_NOT_IN = "delete-not-in"
    REPLACE = "replace"
    ADDITIVE = "additive"


# Rule ID limits
PREFIX_LIST_RULE_MAX = 299999
OTHER_RULE_MAX = 65534


# =============================================================================
# DATA CLASSES FOR BUILDING BLOCKS
# =============================================================================

@dataclass
class PrefixListRule:
    """A single rule in a prefix-list."""
    rule_id: int
    action: RuleAction
    prefix: str  # e.g., "10.0.0.0/8"
    ge: Optional[int] = None  # matching-len ge
    le: Optional[int] = None  # matching-len le
    eq: Optional[int] = None  # matching-len eq (mutually exclusive with ge/le)
    description: Optional[str] = None

    def to_dnos(self, indent: int = 4) -> str:
        """Generate DNOS config line.
        
        DNOS syntax:
        - rule <id> <action> <prefix> matching-len eq <N>
        - rule <id> <action> <prefix> matching-len ge <N>
        - rule <id> <action> <prefix> matching-len ge <N> le <M>
        - rule <id> <action> <prefix> matching-len le <M>
        """
        sp = " " * indent
        line = f"{sp}rule {self.rule_id} {self.action.value} {self.prefix}"
        if self.eq is not None:
            line += f" matching-len eq {self.eq}"
        elif self.ge is not None and self.le is not None:
            # Both ge and le specified
            line += f" matching-len ge {self.ge} le {self.le}"
        elif self.ge is not None:
            # Only ge specified
            line += f" matching-len ge {self.ge}"
        elif self.le is not None:
            # Only le specified
            line += f" matching-len le {self.le}"
        return line


@dataclass
class PrefixList:
    """IPv4 or IPv6 prefix-list."""
    name: str
    ip_version: str = "ipv4"  # "ipv4" or "ipv6"
    rules: List[PrefixListRule] = field(default_factory=list)
    description: Optional[str] = None

    def to_dnos(self, indent: int = 2) -> str:
        """Generate DNOS config block."""
        sp = " " * indent
        lines = [f"{sp}prefix-list {self.ip_version} {self.name}"]
        if self.description:
            lines.append(f"{sp}  description {self.description}")
        for rule in sorted(self.rules, key=lambda r: r.rule_id):
            lines.append(rule.to_dnos(indent + 2))
        lines.append(f"{sp}!")
        return "\n".join(lines)


@dataclass
class CommunityListRule:
    """A single rule in a community-list."""
    rule_id: int
    action: RuleAction
    match_type: str  # "value", "well-known", "regex"
    value: str  # The community value, well-known name, or regex pattern

    def to_dnos(self, indent: int = 4) -> str:
        """Generate DNOS config line."""
        sp = " " * indent
        if self.match_type == "value":
            return f"{sp}rule {self.rule_id} {self.action.value} value {self.value}"
        elif self.match_type == "well-known":
            return f"{sp}rule {self.rule_id} {self.action.value} well-known-community {self.value}"
        elif self.match_type == "regex":
            return f"{sp}rule {self.rule_id} {self.action.value} regex {self.value}"
        return ""


@dataclass
class CommunityList:
    """Standard BGP community-list."""
    name: str
    rules: List[CommunityListRule] = field(default_factory=list)
    description: Optional[str] = None

    def to_dnos(self, indent: int = 2) -> str:
        """Generate DNOS config block."""
        sp = " " * indent
        lines = [f"{sp}community-list {self.name}"]
        if self.description:
            lines.append(f"{sp}  description {self.description}")
        for rule in sorted(self.rules, key=lambda r: r.rule_id):
            lines.append(rule.to_dnos(indent + 2))
        lines.append(f"{sp}!")
        return "\n".join(lines)


@dataclass
class ExtCommunityListRule:
    """A single rule in an extcommunity-list."""
    rule_id: int
    action: RuleAction
    ext_type: str  # "rt" or "soo"
    match_type: str  # "value" or "regex" (regex removed in 17.0 but keep for parsing)
    value: str  # The extcommunity value or regex

    def to_dnos(self, indent: int = 4) -> str:
        """Generate DNOS config line."""
        sp = " " * indent
        if self.match_type == "value":
            return f"{sp}rule {self.rule_id} {self.action.value} {self.ext_type} value {self.value}"
        elif self.match_type == "regex":
            return f"{sp}rule {self.rule_id} {self.action.value} {self.ext_type} regex {self.value}"
        return ""


@dataclass
class ExtCommunityList:
    """Extended community-list (route-target, site-of-origin)."""
    name: str
    rules: List[ExtCommunityListRule] = field(default_factory=list)
    description: Optional[str] = None

    def to_dnos(self, indent: int = 2) -> str:
        """Generate DNOS config block."""
        sp = " " * indent
        lines = [f"{sp}extcommunity-list {self.name}"]
        if self.description:
            lines.append(f"{sp}  description {self.description}")
        for rule in sorted(self.rules, key=lambda r: r.rule_id):
            lines.append(rule.to_dnos(indent + 2))
        lines.append(f"{sp}!")
        return "\n".join(lines)


@dataclass
class LargeCommunityListRule:
    """A single rule in a large-community-list."""
    rule_id: int
    action: RuleAction
    match_type: str  # "value" or "regex"
    value: str  # Format: AS:ID1:ID2 or regex

    def to_dnos(self, indent: int = 4) -> str:
        """Generate DNOS config line."""
        sp = " " * indent
        if self.match_type == "value":
            return f"{sp}rule {self.rule_id} {self.action.value} value {self.value}"
        elif self.match_type == "regex":
            return f"{sp}rule {self.rule_id} {self.action.value} regex {self.value}"
        return ""


@dataclass
class LargeCommunityList:
    """Large BGP community-list (26.1+)."""
    name: str
    rules: List[LargeCommunityListRule] = field(default_factory=list)
    description: Optional[str] = None

    def to_dnos(self, indent: int = 2) -> str:
        """Generate DNOS config block."""
        sp = " " * indent
        lines = [f"{sp}large-community-list {self.name}"]
        if self.description:
            lines.append(f"{sp}  description {self.description}")
        for rule in sorted(self.rules, key=lambda r: r.rule_id):
            lines.append(rule.to_dnos(indent + 2))
        lines.append(f"{sp}!")
        return "\n".join(lines)


@dataclass
class AsPathListRule:
    """A single rule in an as-path-list."""
    rule_id: int
    action: RuleAction
    match_type: str  # "regex" or "passes-through"
    value: str  # Regex pattern or AS number

    def to_dnos(self, indent: int = 4) -> str:
        """Generate DNOS config line."""
        sp = " " * indent
        if self.match_type == "regex":
            return f"{sp}rule {self.rule_id} {self.action.value} regex {self.value}"
        elif self.match_type == "passes-through":
            return f"{sp}rule {self.rule_id} {self.action.value} passes-through {self.value}"
        return ""


@dataclass
class AsPathList:
    """AS-path access list."""
    name: str
    rules: List[AsPathListRule] = field(default_factory=list)
    description: Optional[str] = None

    def to_dnos(self, indent: int = 2) -> str:
        """Generate DNOS config block."""
        sp = " " * indent
        lines = [f"{sp}as-path-list {self.name}"]
        if self.description:
            lines.append(f"{sp}  description {self.description}")
        for rule in sorted(self.rules, key=lambda r: r.rule_id):
            lines.append(rule.to_dnos(indent + 2))
        lines.append(f"{sp}!")
        return "\n".join(lines)


# =============================================================================
# POLICY RULE DATA CLASSES
# =============================================================================

@dataclass
class MatchCondition:
    """A match condition in a policy rule."""
    match_type: MatchType
    value: str  # The list name or direct value
    extra: Optional[str] = None  # For additional params (e.g., ipv4/ipv6 for next-hop)

    def to_dnos(self, indent: int = 6) -> str:
        """Generate DNOS match config line."""
        sp = " " * indent
        if self.match_type == MatchType.IPV4_PREFIX:
            return f"{sp}match ipv4 prefix {self.value}"
        elif self.match_type == MatchType.IPV6_PREFIX:
            return f"{sp}match ipv6 prefix {self.value}"
        elif self.match_type == MatchType.AS_PATH:
            return f"{sp}match as-path {self.value}"
        elif self.match_type == MatchType.AS_PATH_LENGTH:
            return f"{sp}match as-path-length {self.value}"
        elif self.match_type == MatchType.COMMUNITY:
            return f"{sp}match community {self.value}"
        elif self.match_type == MatchType.EXTCOMMUNITY:
            return f"{sp}match extcommunity {self.value}"
        elif self.match_type == MatchType.LARGE_COMMUNITY:
            return f"{sp}match large-community {self.value}"
        elif self.match_type == MatchType.MED:
            return f"{sp}match med {self.value}"
        elif self.match_type == MatchType.TAG:
            return f"{sp}match tag {self.value}"
        elif self.match_type == MatchType.IPV4_NEXT_HOP:
            return f"{sp}match ipv4 next-hop prefix-list {self.value}"
        elif self.match_type == MatchType.IPV6_NEXT_HOP:
            return f"{sp}match ipv6 next-hop prefix-list {self.value}"
        elif self.match_type == MatchType.PATH_TYPE:
            return f"{sp}match path-type {self.value}"
        elif self.match_type == MatchType.RPKI:
            return f"{sp}match rpki {self.value}"
        elif self.match_type == MatchType.RIB_HAS_ROUTE:
            return f"{sp}match rib-has-route {self.value}"
        elif self.match_type == MatchType.PATH_MARK_COUNT:
            return f"{sp}match path-mark-count {self.value}"
        return ""


@dataclass
class SetAction:
    """A set action in a policy rule."""
    action_type: SetActionType
    value: str
    extra: Optional[str] = None  # For additional params (e.g., "additive")

    def to_dnos(self, indent: int = 6) -> str:
        """Generate DNOS set config line."""
        sp = " " * indent
        if self.action_type == SetActionType.LOCAL_PREFERENCE:
            return f"{sp}set local-preference {self.value}"
        elif self.action_type == SetActionType.MED:
            # Supports: value, igp-cost, relative ±value
            return f"{sp}set med {self.value}"
        elif self.action_type == SetActionType.COMMUNITY:
            if self.extra == "additive":
                return f"{sp}set community additive {self.value}"
            elif self.extra == "none":
                return f"{sp}set community none"
            else:
                return f"{sp}set community {self.value}"
        elif self.action_type == SetActionType.COMMUNITY_LIST:
            return f"{sp}set community-list {self.value} {self.extra or 'delete'}"
        elif self.action_type == SetActionType.EXTCOMMUNITY_RT:
            if self.extra == "additive":
                return f"{sp}set extcommunity route-target additive {self.value}"
            else:
                return f"{sp}set extcommunity route-target {self.value}"
        elif self.action_type == SetActionType.EXTCOMMUNITY_SOO:
            return f"{sp}set extcommunity soo {self.value}"
        elif self.action_type == SetActionType.EXTCOMMUNITY_COLOR:
            return f"{sp}set extcommunity color {self.value}"
        elif self.action_type == SetActionType.EXTCOMMUNITY_LIST:
            return f"{sp}set extcommunity-list {self.value} {self.extra or 'delete'}"
        elif self.action_type == SetActionType.LARGE_COMMUNITY:
            if self.extra == "additive":
                return f"{sp}set large-community additive {self.value}"
            elif self.extra == "none":
                return f"{sp}set large-community none"
            else:
                return f"{sp}set large-community {self.value}"
        elif self.action_type == SetActionType.LARGE_COMMUNITY_LIST:
            return f"{sp}set large-community-list {self.value} {self.extra or 'delete'}"
        elif self.action_type == SetActionType.AS_PATH_PREPEND:
            if self.extra == "last-as":
                return f"{sp}set as-path prepend last-as {self.value}"
            else:
                return f"{sp}set as-path prepend as-number {self.value}"
        elif self.action_type == SetActionType.AS_PATH_EXCLUDE:
            return f"{sp}set as-path exclude {self.value}"
        elif self.action_type == SetActionType.IPV4_NEXT_HOP:
            return f"{sp}set ipv4 next-hop {self.value}"
        elif self.action_type == SetActionType.IPV6_NEXT_HOP:
            return f"{sp}set ipv6 next-hop {self.value}"
        elif self.action_type == SetActionType.WEIGHT:
            return f"{sp}set weight {self.value}"
        elif self.action_type == SetActionType.ATOMIC_AGGREGATE:
            return f"{sp}set atomic-aggregate"
        elif self.action_type == SetActionType.TAG:
            return f"{sp}set tag {self.value}"
        elif self.action_type == SetActionType.OSPF_METRIC:
            return f"{sp}set ospf-metric {self.value}"
        elif self.action_type == SetActionType.ISIS_METRIC:
            return f"{sp}set isis-metric {self.value}"
        elif self.action_type == SetActionType.METRIC_TYPE:
            return f"{sp}set metric-type {self.value}"
        elif self.action_type == SetActionType.AIGP:
            return f"{sp}set aigp {self.value}"
        elif self.action_type == SetActionType.PATH_MARK:
            return f"{sp}set path-mark {self.value}"
        elif self.action_type == SetActionType.FORWARDING_ACTION:
            return f"{sp}set forwarding-action urpf-check ignore"
        return ""


@dataclass
class PolicyRule:
    """A single rule in a routing policy."""
    rule_id: int
    action: RuleAction
    match_conditions: List[MatchCondition] = field(default_factory=list)
    set_actions: List[SetAction] = field(default_factory=list)
    on_match: Optional[OnMatchAction] = None
    on_match_goto_rule: Optional[int] = None  # For goto action
    call_policy: Optional[str] = None
    description: Optional[str] = None

    def to_dnos(self, indent: int = 4) -> str:
        """Generate DNOS config block for this rule."""
        sp = " " * indent
        lines = [f"{sp}rule {self.rule_id} {self.action.value}"]
        
        if self.description:
            lines.append(f"{sp}  description {self.description}")
        
        # Match conditions (all must match - AND logic)
        for match in self.match_conditions:
            lines.append(match.to_dnos(indent + 2))
        
        # Set actions (only for allow rules)
        if self.action == RuleAction.ALLOW:
            for set_action in self.set_actions:
                lines.append(set_action.to_dnos(indent + 2))
        
        # Control flow
        if self.on_match:
            if self.on_match == OnMatchAction.NEXT:
                lines.append(f"{sp}  on-match next")
            elif self.on_match == OnMatchAction.GOTO and self.on_match_goto_rule:
                lines.append(f"{sp}  on-match goto {self.on_match_goto_rule}")
            elif self.on_match == OnMatchAction.NEXT_POLICY:
                lines.append(f"{sp}  on-match next-policy")
        
        if self.call_policy:
            lines.append(f"{sp}  call {self.call_policy}")
        
        lines.append(f"{sp}!")
        return "\n".join(lines)


@dataclass
class RoutingPolicy:
    """A complete routing policy definition."""
    name: str
    rules: List[PolicyRule] = field(default_factory=list)
    description: Optional[str] = None

    def to_dnos(self, indent: int = 2) -> str:
        """Generate DNOS config block."""
        sp = " " * indent
        lines = [f"{sp}policy {self.name}"]
        if self.description:
            lines.append(f"{sp}  description {self.description}")
        for rule in sorted(self.rules, key=lambda r: r.rule_id):
            lines.append(rule.to_dnos(indent + 2))
        lines.append(f"{sp}!")
        return "\n".join(lines)


# =============================================================================
# POLICY MANAGER
# =============================================================================

class PolicyManager:
    """
    Central manager for all routing-policy operations.
    
    Manages:
    - Prefix-lists (IPv4 and IPv6)
    - Community-lists
    - Extended community-lists
    - Large community-lists
    - AS-path-lists
    - Routing policies
    
    Provides:
    - Parsing from running config
    - Config generation
    - Dependency tracking
    - Session state storage
    """

    def __init__(self):
        """Initialize empty policy manager."""
        self.prefix_lists_v4: Dict[str, PrefixList] = {}
        self.prefix_lists_v6: Dict[str, PrefixList] = {}
        self.community_lists: Dict[str, CommunityList] = {}
        self.extcommunity_lists: Dict[str, ExtCommunityList] = {}
        self.large_community_lists: Dict[str, LargeCommunityList] = {}
        self.as_path_lists: Dict[str, AsPathList] = {}
        self.policies: Dict[str, RoutingPolicy] = {}
        self._dirty = False  # Track if changes were made

    def is_empty(self) -> bool:
        """Check if no policies are configured."""
        return (
            not self.prefix_lists_v4 and
            not self.prefix_lists_v6 and
            not self.community_lists and
            not self.extcommunity_lists and
            not self.large_community_lists and
            not self.as_path_lists and
            not self.policies
        )

    def get_all_policy_names(self) -> List[str]:
        """Get list of all policy names."""
        return list(self.policies.keys())

    def get_all_prefix_list_names(self, ip_version: str = None) -> List[str]:
        """Get list of all prefix-list names."""
        if ip_version == "ipv4":
            return list(self.prefix_lists_v4.keys())
        elif ip_version == "ipv6":
            return list(self.prefix_lists_v6.keys())
        else:
            return list(self.prefix_lists_v4.keys()) + list(self.prefix_lists_v6.keys())

    def get_all_community_list_names(self) -> List[str]:
        """Get list of all community-list names."""
        return list(self.community_lists.keys())

    def get_all_extcommunity_list_names(self) -> List[str]:
        """Get list of all extcommunity-list names."""
        return list(self.extcommunity_lists.keys())

    def get_all_large_community_list_names(self) -> List[str]:
        """Get list of all large-community-list names."""
        return list(self.large_community_lists.keys())

    def get_all_as_path_list_names(self) -> List[str]:
        """Get list of all as-path-list names."""
        return list(self.as_path_lists.keys())

    def add_prefix_list(self, prefix_list: PrefixList) -> None:
        """Add or update a prefix-list."""
        if prefix_list.ip_version == "ipv4":
            self.prefix_lists_v4[prefix_list.name] = prefix_list
        else:
            self.prefix_lists_v6[prefix_list.name] = prefix_list
        self._dirty = True

    def add_community_list(self, community_list: CommunityList) -> None:
        """Add or update a community-list."""
        self.community_lists[community_list.name] = community_list
        self._dirty = True

    def add_extcommunity_list(self, extcommunity_list: ExtCommunityList) -> None:
        """Add or update an extcommunity-list."""
        self.extcommunity_lists[extcommunity_list.name] = extcommunity_list
        self._dirty = True

    def add_large_community_list(self, large_community_list: LargeCommunityList) -> None:
        """Add or update a large-community-list."""
        self.large_community_lists[large_community_list.name] = large_community_list
        self._dirty = True

    def add_as_path_list(self, as_path_list: AsPathList) -> None:
        """Add or update an as-path-list."""
        self.as_path_lists[as_path_list.name] = as_path_list
        self._dirty = True

    def add_policy(self, policy: RoutingPolicy) -> None:
        """Add or update a routing policy."""
        self.policies[policy.name] = policy
        self._dirty = True

    def delete_prefix_list(self, name: str, ip_version: str = None) -> bool:
        """Delete a prefix-list by name."""
        if ip_version == "ipv4" and name in self.prefix_lists_v4:
            del self.prefix_lists_v4[name]
            self._dirty = True
            return True
        elif ip_version == "ipv6" and name in self.prefix_lists_v6:
            del self.prefix_lists_v6[name]
            self._dirty = True
            return True
        elif name in self.prefix_lists_v4:
            del self.prefix_lists_v4[name]
            self._dirty = True
            return True
        elif name in self.prefix_lists_v6:
            del self.prefix_lists_v6[name]
            self._dirty = True
            return True
        return False

    def delete_community_list(self, name: str) -> bool:
        """Delete a community-list by name."""
        if name in self.community_lists:
            del self.community_lists[name]
            self._dirty = True
            return True
        return False

    def delete_policy(self, name: str) -> bool:
        """Delete a policy by name."""
        if name in self.policies:
            del self.policies[name]
            self._dirty = True
            return True
        return False

    def get_dependencies(self, policy_name: str) -> Dict[str, List[str]]:
        """
        Get all dependencies for a policy.
        
        Returns:
            Dict with keys: prefix_lists, community_lists, extcommunity_lists,
                           large_community_lists, as_path_lists, called_policies
        """
        deps = {
            'prefix_lists': [],
            'community_lists': [],
            'extcommunity_lists': [],
            'large_community_lists': [],
            'as_path_lists': [],
            'called_policies': []
        }
        
        policy = self.policies.get(policy_name)
        if not policy:
            return deps
        
        for rule in policy.rules:
            for match in rule.match_conditions:
                if match.match_type in (MatchType.IPV4_PREFIX, MatchType.IPV6_PREFIX,
                                        MatchType.IPV4_NEXT_HOP, MatchType.IPV6_NEXT_HOP):
                    if match.value not in deps['prefix_lists']:
                        deps['prefix_lists'].append(match.value)
                elif match.match_type == MatchType.COMMUNITY:
                    if match.value not in deps['community_lists']:
                        deps['community_lists'].append(match.value)
                elif match.match_type == MatchType.EXTCOMMUNITY:
                    if match.value not in deps['extcommunity_lists']:
                        deps['extcommunity_lists'].append(match.value)
                elif match.match_type == MatchType.LARGE_COMMUNITY:
                    if match.value not in deps['large_community_lists']:
                        deps['large_community_lists'].append(match.value)
                elif match.match_type == MatchType.AS_PATH:
                    if match.value not in deps['as_path_lists']:
                        deps['as_path_lists'].append(match.value)
            
            # Check set actions for list references
            for set_action in rule.set_actions:
                if set_action.action_type == SetActionType.COMMUNITY_LIST:
                    if set_action.value not in deps['community_lists']:
                        deps['community_lists'].append(set_action.value)
                elif set_action.action_type == SetActionType.EXTCOMMUNITY_LIST:
                    if set_action.value not in deps['extcommunity_lists']:
                        deps['extcommunity_lists'].append(set_action.value)
                elif set_action.action_type == SetActionType.LARGE_COMMUNITY_LIST:
                    if set_action.value not in deps['large_community_lists']:
                        deps['large_community_lists'].append(set_action.value)
            
            # Check for called policies
            if rule.call_policy and rule.call_policy not in deps['called_policies']:
                deps['called_policies'].append(rule.call_policy)
        
        return deps

    def to_dnos(self) -> str:
        """
        Generate complete DNOS routing-policy configuration.
        
        Outputs all building blocks and policies in proper order:
        1. AS-path-lists
        2. Community-lists
        3. Extended community-lists
        4. Large community-lists
        5. Prefix-lists (IPv4)
        6. Prefix-lists (IPv6)
        7. Policies
        """
        if self.is_empty():
            return ""
        
        lines = ["routing-policy"]
        
        # AS-path-lists
        for name in sorted(self.as_path_lists.keys()):
            lines.append(self.as_path_lists[name].to_dnos(2))
        
        # Community-lists
        for name in sorted(self.community_lists.keys()):
            lines.append(self.community_lists[name].to_dnos(2))
        
        # Extended community-lists
        for name in sorted(self.extcommunity_lists.keys()):
            lines.append(self.extcommunity_lists[name].to_dnos(2))
        
        # Large community-lists
        for name in sorted(self.large_community_lists.keys()):
            lines.append(self.large_community_lists[name].to_dnos(2))
        
        # Prefix-lists IPv4
        for name in sorted(self.prefix_lists_v4.keys()):
            lines.append(self.prefix_lists_v4[name].to_dnos(2))
        
        # Prefix-lists IPv6
        for name in sorted(self.prefix_lists_v6.keys()):
            lines.append(self.prefix_lists_v6[name].to_dnos(2))
        
        # Policies
        for name in sorted(self.policies.keys()):
            lines.append(self.policies[name].to_dnos(2))
        
        lines.append("!")
        return "\n".join(lines)

    def get_summary(self) -> Dict[str, int]:
        """Get counts of all policy components."""
        return {
            'prefix_lists_v4': len(self.prefix_lists_v4),
            'prefix_lists_v6': len(self.prefix_lists_v6),
            'community_lists': len(self.community_lists),
            'extcommunity_lists': len(self.extcommunity_lists),
            'large_community_lists': len(self.large_community_lists),
            'as_path_lists': len(self.as_path_lists),
            'policies': len(self.policies),
            'total_rules': sum(len(p.rules) for p in self.policies.values())
        }

    def display_summary(self) -> None:
        """Display a summary table of all policy components."""
        summary = self.get_summary()
        
        table = Table(title="Routing Policy Summary", show_header=True)
        table.add_column("Component", style="cyan")
        table.add_column("Count", justify="right", style="green")
        
        table.add_row("Prefix-lists (IPv4)", str(summary['prefix_lists_v4']))
        table.add_row("Prefix-lists (IPv6)", str(summary['prefix_lists_v6']))
        table.add_row("Community-lists", str(summary['community_lists']))
        table.add_row("ExtCommunity-lists", str(summary['extcommunity_lists']))
        table.add_row("Large-Community-lists", str(summary['large_community_lists']))
        table.add_row("AS-Path-lists", str(summary['as_path_lists']))
        table.add_row("Policies", str(summary['policies']))
        table.add_row("Total Policy Rules", str(summary['total_rules']))
        
        console.print(table)


# =============================================================================
# BUILDER CLASSES FOR INTERACTIVE CONFIGURATION
# =============================================================================

class PrefixListBuilder:
    """Interactive builder for prefix-lists."""
    
    def __init__(self, name: str = None, ip_version: str = "ipv4"):
        self.name = name
        self.ip_version = ip_version
        self.rules: List[PrefixListRule] = []
        self.description: Optional[str] = None
    
    def add_rule(self, rule_id: int, action: RuleAction, prefix: str,
                 ge: int = None, le: int = None, eq: int = None) -> None:
        """Add a rule to the prefix-list."""
        rule = PrefixListRule(
            rule_id=rule_id,
            action=action,
            prefix=prefix,
            ge=ge,
            le=le,
            eq=eq
        )
        self.rules.append(rule)
    
    def build(self) -> PrefixList:
        """Build the final PrefixList object."""
        return PrefixList(
            name=self.name,
            ip_version=self.ip_version,
            rules=self.rules,
            description=self.description
        )
    
    @staticmethod
    def validate_prefix(prefix: str, ip_version: str) -> Tuple[bool, str]:
        """Validate prefix format."""
        if '/' not in prefix:
            return False, "Prefix must include mask length (e.g., 10.0.0.0/8)"
        
        parts = prefix.split('/')
        if len(parts) != 2:
            return False, "Invalid prefix format"
        
        try:
            mask = int(parts[1])
        except ValueError:
            return False, "Mask length must be an integer"
        
        if ip_version == "ipv4":
            if mask < 0 or mask > 32:
                return False, "IPv4 mask length must be 0-32"
            # Validate IPv4 address
            octets = parts[0].split('.')
            if len(octets) != 4:
                return False, "Invalid IPv4 address"
            for octet in octets:
                try:
                    val = int(octet)
                    if val < 0 or val > 255:
                        return False, "IPv4 octet must be 0-255"
                except ValueError:
                    return False, "Invalid IPv4 octet"
        else:  # ipv6
            if mask < 0 or mask > 128:
                return False, "IPv6 mask length must be 0-128"
            # Basic IPv6 validation - just check for valid chars
            addr = parts[0].replace(':', '')
            if not all(c in '0123456789abcdefABCDEF' for c in addr):
                return False, "Invalid IPv6 address"
        
        return True, ""


class CommunityListBuilder:
    """Interactive builder for community-lists."""
    
    def __init__(self, name: str = None):
        self.name = name
        self.rules: List[CommunityListRule] = []
        self.description: Optional[str] = None
    
    def add_rule(self, rule_id: int, action: RuleAction, match_type: str, value: str) -> None:
        """Add a rule to the community-list."""
        rule = CommunityListRule(
            rule_id=rule_id,
            action=action,
            match_type=match_type,
            value=value
        )
        self.rules.append(rule)
    
    def build(self) -> CommunityList:
        """Build the final CommunityList object."""
        return CommunityList(
            name=self.name,
            rules=self.rules,
            description=self.description
        )
    
    @staticmethod
    def validate_community(value: str) -> Tuple[bool, str]:
        """Validate standard community format (AS:ID or range)."""
        # Standard format: AS:ID where AS is 1-65535, ID is 0-65535
        # Range format: AS1-AS2:ID or AS:ID1-ID2
        if ':' not in value:
            return False, "Community must be in AS:ID format"
        
        parts = value.split(':')
        if len(parts) != 2:
            return False, "Community must be in AS:ID format"
        
        # Check for ranges
        as_part, id_part = parts
        
        # Validate AS part (may be range)
        if '-' in as_part:
            as_range = as_part.split('-')
            if len(as_range) != 2:
                return False, "Invalid AS range"
            try:
                as_start, as_end = int(as_range[0]), int(as_range[1])
                if as_start > as_end or as_start < 1 or as_end > 65535:
                    return False, "AS must be 1-65535"
            except ValueError:
                return False, "AS must be numeric"
        else:
            try:
                as_num = int(as_part)
                if as_num < 1 or as_num > 65535:
                    return False, "AS must be 1-65535"
            except ValueError:
                return False, "AS must be numeric"
        
        # Validate ID part (may be range)
        if '-' in id_part:
            id_range = id_part.split('-')
            if len(id_range) != 2:
                return False, "Invalid ID range"
            try:
                id_start, id_end = int(id_range[0]), int(id_range[1])
                if id_start > id_end or id_start < 0 or id_end > 65535:
                    return False, "ID must be 0-65535"
            except ValueError:
                return False, "ID must be numeric"
        else:
            try:
                id_num = int(id_part)
                if id_num < 0 or id_num > 65535:
                    return False, "ID must be 0-65535"
            except ValueError:
                return False, "ID must be numeric"
        
        return True, ""


class ExtCommunityListBuilder:
    """Interactive builder for extended community-lists."""
    
    def __init__(self, name: str = None):
        self.name = name
        self.rules: List[ExtCommunityListRule] = []
        self.description: Optional[str] = None
    
    def add_rule(self, rule_id: int, action: RuleAction, ext_type: str,
                 match_type: str, value: str) -> None:
        """Add a rule to the extcommunity-list."""
        rule = ExtCommunityListRule(
            rule_id=rule_id,
            action=action,
            ext_type=ext_type,
            match_type=match_type,
            value=value
        )
        self.rules.append(rule)
    
    def build(self) -> ExtCommunityList:
        """Build the final ExtCommunityList object."""
        return ExtCommunityList(
            name=self.name,
            rules=self.rules,
            description=self.description
        )


class LargeCommunityListBuilder:
    """Interactive builder for large community-lists."""
    
    def __init__(self, name: str = None):
        self.name = name
        self.rules: List[LargeCommunityListRule] = []
        self.description: Optional[str] = None
    
    def add_rule(self, rule_id: int, action: RuleAction, match_type: str, value: str) -> None:
        """Add a rule to the large-community-list."""
        rule = LargeCommunityListRule(
            rule_id=rule_id,
            action=action,
            match_type=match_type,
            value=value
        )
        self.rules.append(rule)
    
    def build(self) -> LargeCommunityList:
        """Build the final LargeCommunityList object."""
        return LargeCommunityList(
            name=self.name,
            rules=self.rules,
            description=self.description
        )
    
    @staticmethod
    def validate_large_community(value: str) -> Tuple[bool, str]:
        """Validate large community format (AS:ID1:ID2)."""
        parts = value.split(':')
        if len(parts) != 3:
            return False, "Large community must be in AS:ID1:ID2 format"
        
        try:
            as_num = int(parts[0])
            id1 = int(parts[1])
            id2 = int(parts[2])
            
            if as_num < 0 or as_num > 4294967295:
                return False, "AS must be 0-4294967295"
            if id1 < 0 or id1 > 4294967295:
                return False, "ID1 must be 0-4294967295"
            if id2 < 0 or id2 > 4294967295:
                return False, "ID2 must be 0-4294967295"
        except ValueError:
            return False, "All parts must be numeric"
        
        return True, ""


class AsPathListBuilder:
    """Interactive builder for as-path-lists."""
    
    def __init__(self, name: str = None):
        self.name = name
        self.rules: List[AsPathListRule] = []
        self.description: Optional[str] = None
    
    def add_rule(self, rule_id: int, action: RuleAction, match_type: str, value: str) -> None:
        """Add a rule to the as-path-list."""
        rule = AsPathListRule(
            rule_id=rule_id,
            action=action,
            match_type=match_type,
            value=value
        )
        self.rules.append(rule)
    
    def build(self) -> AsPathList:
        """Build the final AsPathList object."""
        return AsPathList(
            name=self.name,
            rules=self.rules,
            description=self.description
        )


class PolicyBuilder:
    """Interactive builder for routing policies."""
    
    def __init__(self, name: str = None):
        self.name = name
        self.rules: List[PolicyRule] = []
        self.description: Optional[str] = None
    
    def add_rule(self, rule: PolicyRule) -> None:
        """Add a rule to the policy."""
        self.rules.append(rule)
    
    def delete_rule(self, rule_id: int) -> bool:
        """Delete a rule by ID."""
        for i, rule in enumerate(self.rules):
            if rule.rule_id == rule_id:
                self.rules.pop(i)
                return True
        return False
    
    def get_rule(self, rule_id: int) -> Optional[PolicyRule]:
        """Get a rule by ID."""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None
    
    def build(self) -> RoutingPolicy:
        """Build the final RoutingPolicy object."""
        return RoutingPolicy(
            name=self.name,
            rules=self.rules,
            description=self.description
        )
    
    def get_next_rule_id(self, step: int = 10) -> int:
        """Get next available rule ID with given step."""
        if not self.rules:
            return step
        max_id = max(r.rule_id for r in self.rules)
        return ((max_id // step) + 1) * step


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def suggest_policy_name(prefix: str, existing_names: List[str]) -> str:
    """Suggest a unique policy name based on prefix."""
    if prefix not in existing_names:
        return prefix
    
    i = 1
    while f"{prefix}_{i}" in existing_names:
        i += 1
    return f"{prefix}_{i}"


def format_policy_for_display(policy: RoutingPolicy) -> str:
    """Format a policy for display in a summary."""
    rule_summaries = []
    for rule in sorted(policy.rules, key=lambda r: r.rule_id):
        match_summary = ", ".join(f"{m.match_type.value}:{m.value}" for m in rule.match_conditions) or "any"
        set_summary = ", ".join(f"{s.action_type.value}" for s in rule.set_actions) or "-"
        rule_summaries.append(f"  [{rule.rule_id}] {rule.action.value}: match({match_summary}) set({set_summary})")
    
    return f"{policy.name}:\n" + "\n".join(rule_summaries)


# =============================================================================
# POLICY SUGGESTER - Smart Policy Suggestions
# =============================================================================

class PolicySuggester:
    """
    Smart policy suggestion engine for the SCALER wizard.
    
    Provides context-aware policy suggestions throughout the wizard:
    - BGP neighbor policy in/out
    - Redistribution policies
    - Default-originate policies
    - EVPN import/export policies
    
    Suggestions are based on:
    - Existing policies in config
    - Policies created in current session
    - Available templates
    - Context (neighbor type, AFI, direction)
    """
    
    def __init__(self, manager: PolicyManager = None, device_config: str = None):
        """
        Initialize PolicySuggester.
        
        Args:
            manager: PolicyManager with current session policies
            device_config: Raw device configuration text for parsing existing policies
        """
        self.manager = manager or PolicyManager()
        self.device_config = device_config or ""
        self._cached_existing_policies: Optional[List[str]] = None
    
    def get_existing_policies(self) -> List[str]:
        """Get list of existing policy names from device config."""
        if self._cached_existing_policies is not None:
            return self._cached_existing_policies
        
        policies = []
        
        # Parse from device config
        if self.device_config:
            import re
            policy_matches = re.findall(r'^\s*policy\s+(\S+)', self.device_config, re.MULTILINE)
            policies.extend(policy_matches)
        
        # Add from current session
        policies.extend(self.manager.get_all_policy_names())
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for p in policies:
            if p not in seen:
                seen.add(p)
                unique.append(p)
        
        self._cached_existing_policies = unique
        return unique
    
    def suggest_for_bgp_neighbor(
        self,
        neighbor_ip: str,
        afi: str,
        direction: str,  # "in" or "out"
        remote_as: int = None,
        local_as: int = None,
        is_ibgp: bool = None
    ) -> List[Dict[str, str]]:
        """
        Suggest policies for a BGP neighbor.
        
        IMPORTANT: Only suggests policies that ACTUALLY EXIST in the config.
        Template suggestions are NOT included unless they exist, to avoid
        referencing non-existent policies in the config.
        
        Args:
            neighbor_ip: Neighbor IP address
            afi: Address family (ipv4-unicast, ipv6-unicast, etc.)
            direction: "in" for inbound, "out" for outbound
            remote_as: Remote AS number (optional)
            local_as: Local AS number (optional)
            is_ibgp: Whether this is an iBGP peer (optional)
        
        Returns:
            List of suggestion dicts with 'name', 'source', 'description'
        """
        suggestions = []
        existing = self.get_existing_policies()
        existing_lower = {p.lower(): p for p in existing}
        
        # Auto-detect iBGP vs eBGP
        if is_ibgp is None and remote_as is not None and local_as is not None:
            is_ibgp = (remote_as == local_as)
        
        # Inbound policy suggestions - ONLY existing policies
        if direction == "in":
            # Look for existing policies with matching patterns
            for pol_name in existing:
                name_lower = pol_name.lower()
                if any(kw in name_lower for kw in ['import', '_in', '-in', 'inbound', 'ingress']):
                    suggestions.append({
                        'name': pol_name,
                        'source': 'existing',
                        'description': 'Existing inbound policy'
                    })
            
            # Check if common template names actually exist
            template_names = ['IBGP_IMPORT', 'EBGP_IMPORT', 'DENY_BOGONS_V4', 'DENY_BOGONS_V6']
            for tmpl in template_names:
                if tmpl.lower() in existing_lower:
                    actual_name = existing_lower[tmpl.lower()]
                    if actual_name not in [s['name'] for s in suggestions]:
                        suggestions.append({
                            'name': actual_name,
                            'source': 'existing',
                            'description': f'{tmpl} policy'
                        })
        
        # Outbound policy suggestions - ONLY existing policies
        else:  # direction == "out"
            for pol_name in existing:
                name_lower = pol_name.lower()
                if any(kw in name_lower for kw in ['export', '_out', '-out', 'outbound', 'egress']):
                    suggestions.append({
                        'name': pol_name,
                        'source': 'existing',
                        'description': 'Existing outbound policy'
                    })
            
            # Check if common template names actually exist
            template_names = ['IBGP_EXPORT', 'EBGP_EXPORT']
            for tmpl in template_names:
                if tmpl.lower() in existing_lower:
                    actual_name = existing_lower[tmpl.lower()]
                    if actual_name not in [s['name'] for s in suggestions]:
                        suggestions.append({
                            'name': actual_name,
                            'source': 'existing',
                            'description': f'{tmpl} policy'
                        })
        
        # Also add any general routing policies that might be applicable
        for pol_name in existing:
            name_lower = pol_name.lower()
            # Skip already added
            if pol_name in [s['name'] for s in suggestions]:
                continue
            # Add policies that look like BGP policies
            if any(kw in name_lower for kw in ['bgp', 'peer', 'neighbor', 'policy', 'route']):
                suggestions.append({
                    'name': pol_name,
                    'source': 'existing',
                    'description': 'Existing routing policy'
                })
        
        # Remove duplicates
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s['name'] not in seen:
                seen.add(s['name'])
                unique_suggestions.append(s)
        
        return unique_suggestions[:10]  # Limit to 10 suggestions
    
    def suggest_for_redistribution(
        self,
        source_protocol: str,  # "connected", "static", "ospf", "isis"
        dest_protocol: str = "bgp"
    ) -> List[Dict[str, str]]:
        """
        Suggest policies for route redistribution.
        
        Args:
            source_protocol: Source routing protocol
            dest_protocol: Destination protocol (usually BGP)
        
        Returns:
            List of suggestion dicts
        """
        suggestions = []
        existing = self.get_existing_policies()
        
        # Look for existing redistribution policies
        for pol_name in existing:
            name_lower = pol_name.lower()
            if 'redist' in name_lower or source_protocol.lower() in name_lower:
                suggestions.append({
                    'name': pol_name,
                    'source': 'existing',
                    'description': f'Existing {source_protocol} redistribution policy'
                })
        
        # Suggest new policy name
        policy_name = f"REDIST_{source_protocol.upper()}_TO_{dest_protocol.upper()}"
        suggestions.append({
            'name': policy_name,
            'source': 'suggested',
            'description': f'Set attributes for redistributed {source_protocol} routes'
        })
        
        # Community tagging suggestion
        suggestions.append({
            'name': 'COMMUNITY_TAG',
            'source': 'template',
            'description': 'Tag redistributed routes with community'
        })
        
        return suggestions[:5]
    
    def suggest_for_default_originate(
        self,
        afi: str
    ) -> List[Dict[str, str]]:
        """
        Suggest policies for conditional default-originate.
        
        Args:
            afi: Address family
        
        Returns:
            List of suggestion dicts
        """
        suggestions = []
        existing = self.get_existing_policies()
        
        # Look for existing default-originate policies
        for pol_name in existing:
            name_lower = pol_name.lower()
            if 'default' in name_lower or 'originate' in name_lower:
                suggestions.append({
                    'name': pol_name,
                    'source': 'existing',
                    'description': 'Existing default-originate policy'
                })
        
        # Suggest based on AFI
        if 'ipv4' in afi:
            suggestions.append({
                'name': 'DEFAULT_ORIGINATE_V4',
                'source': 'suggested',
                'description': 'Conditional IPv4 default origination'
            })
        elif 'ipv6' in afi:
            suggestions.append({
                'name': 'DEFAULT_ORIGINATE_V6',
                'source': 'suggested',
                'description': 'Conditional IPv6 default origination'
            })
        
        return suggestions[:5]
    
    def suggest_for_evpn_import_export(
        self,
        service_type: str,  # "evpn-vpws", "evpn-vpws-fxc", "evpn-vpls"
        direction: str  # "import" or "export"
    ) -> List[Dict[str, str]]:
        """
        Suggest policies for EVPN service import/export.
        
        Args:
            service_type: Type of EVPN service
            direction: "import" or "export"
        
        Returns:
            List of suggestion dicts
        """
        suggestions = []
        existing = self.get_existing_policies()
        
        # Look for existing EVPN policies
        for pol_name in existing:
            name_lower = pol_name.lower()
            if 'evpn' in name_lower or 'l2vpn' in name_lower:
                if direction in name_lower:
                    suggestions.append({
                        'name': pol_name,
                        'source': 'existing',
                        'description': f'Existing EVPN {direction} policy'
                    })
        
        # Suggest RT filter
        suggestions.append({
            'name': 'RT_FILTER',
            'source': 'template',
            'description': f'Filter by route-target for {direction}'
        })
        
        return suggestions[:5]
    
    def display_suggestions(
        self,
        suggestions: List[Dict[str, str]],
        prompt_text: str = "Select policy"
    ) -> Optional[str]:
        """
        Display suggestions in a menu and get user selection.
        
        Args:
            suggestions: List of suggestion dicts
            prompt_text: Prompt text to display
        
        Returns:
            Selected policy name or None
        """
        if not suggestions:
            return None
        
        console.print(f"\n[bold]{prompt_text}:[/bold]")
        
        for i, sug in enumerate(suggestions, 1):
            source_tag = ""
            if sug['source'] == 'existing':
                source_tag = "[green](existing)[/green]"
            elif sug['source'] == 'template':
                source_tag = "[cyan](template)[/cyan]"
            else:
                source_tag = "[yellow](new)[/yellow]"
            
            console.print(f"  [{i}] {sug['name']} {source_tag}")
            console.print(f"      [dim]{sug['description']}[/dim]")
        
        console.print("  ────────────────────────────────────────")
        console.print("  [N] Create new policy")
        console.print("  [M] Enter policy name manually")
        console.print("  [S] Skip (no policy)")
        console.print("  [B] Back")
        
        valid_choices = [str(i) for i in range(1, len(suggestions) + 1)] + ["n", "N", "m", "M", "s", "S", "b", "B"]
        choice = Prompt.ask("Select", choices=valid_choices, default="s").lower()
        
        if choice == "b":
            from .core import BackException
            raise BackException()
        elif choice == "s":
            return None
        elif choice == "n":
            return "__NEW__"  # Signal to create new policy
        elif choice == "m":
            return Prompt.ask("  Enter policy name", default="")
        else:
            idx = int(choice) - 1
            if 0 <= idx < len(suggestions):
                return suggestions[idx]['name']
        
        return None
