"""
Policy Validation Engine for the SCALER Wizard.

Provides comprehensive validation for routing-policy configurations:
- Reference Validation: Verify all referenced lists/policies exist
- Circular Dependency Detection: Detect policy call chains that loop
- Conflict Detection: Duplicate rule IDs, overlapping entries
- DNOS Syntax Validation: Rule ID ranges, community formats, regex patterns

DNOS 26.1 Limits Reference:
- Prefix-list rule IDs: 1-299999 (300000 is system default deny-any)
- Community-list rule IDs: 1-65534 (65535 is system default deny-any)
- ExtCommunity-list rule IDs: 1-65534
- Large-community-list rule IDs: 1-65534
- AS-path-list rule IDs: 1-65534
- Policy rule IDs: 1-65534
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"       # Must be fixed before commit
    WARNING = "warning"   # Should be fixed, may cause issues
    INFO = "info"         # Informational, no action required


@dataclass
class ValidationIssue:
    """A single validation issue found during policy validation."""
    severity: ValidationSeverity
    component: str  # e.g., "prefix-list PL_TEST", "policy POL_IMPORT"
    issue: str      # Description of the issue
    suggestion: Optional[str] = None  # How to fix it
    location: Optional[str] = None    # Line number or rule ID if applicable


@dataclass
class ValidationResult:
    """Complete validation result for a policy configuration."""
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    
    def add_error(self, component: str, issue: str, suggestion: str = None, location: str = None):
        """Add an error issue."""
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            component=component,
            issue=issue,
            suggestion=suggestion,
            location=location
        ))
        self.valid = False
    
    def add_warning(self, component: str, issue: str, suggestion: str = None, location: str = None):
        """Add a warning issue."""
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            component=component,
            issue=issue,
            suggestion=suggestion,
            location=location
        ))
    
    def add_info(self, component: str, issue: str, suggestion: str = None, location: str = None):
        """Add an info issue."""
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.INFO,
            component=component,
            issue=issue,
            suggestion=suggestion,
            location=location
        ))
    
    def get_errors(self) -> List[ValidationIssue]:
        """Get only error issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
    
    def get_warnings(self) -> List[ValidationIssue]:
        """Get only warning issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]
    
    def display(self) -> None:
        """Display validation results in a formatted table."""
        if not self.issues:
            console.print("[bold green]✓ Validation passed - no issues found[/bold green]")
            return
        
        # Summary
        errors = len(self.get_errors())
        warnings = len(self.get_warnings())
        infos = len([i for i in self.issues if i.severity == ValidationSeverity.INFO])
        
        if errors > 0:
            console.print(f"[bold red]✗ Validation failed: {errors} error(s), {warnings} warning(s)[/bold red]")
        else:
            console.print(f"[bold yellow]⚠ Validation passed with warnings: {warnings} warning(s)[/bold yellow]")
        
        # Issues table
        table = Table(show_header=True, header_style="bold")
        table.add_column("Severity", style="dim", width=8)
        table.add_column("Component", width=25)
        table.add_column("Issue", width=40)
        table.add_column("Suggestion", width=30)
        
        for issue in self.issues:
            if issue.severity == ValidationSeverity.ERROR:
                severity_str = "[red]ERROR[/red]"
            elif issue.severity == ValidationSeverity.WARNING:
                severity_str = "[yellow]WARN[/yellow]"
            else:
                severity_str = "[blue]INFO[/blue]"
            
            loc = f" (rule {issue.location})" if issue.location else ""
            table.add_row(
                severity_str,
                f"{issue.component}{loc}",
                issue.issue,
                issue.suggestion or "-"
            )
        
        console.print(table)


class PolicyValidator:
    """
    Comprehensive validator for routing-policy configurations.
    
    Validates:
    - Reference integrity (lists and policies referenced must exist)
    - Circular dependencies (policy call chains must not loop)
    - Duplicate rule IDs
    - Rule ID range validity
    - Community/prefix format validity
    - Regex pattern validity
    """
    
    # Rule ID limits from DNOS
    LIMITS = {
        'prefix_list': (1, 299999),
        'community_list': (1, 65534),
        'extcommunity_list': (1, 65534),
        'large_community_list': (1, 65534),
        'as_path_list': (1, 65534),
        'policy': (1, 65534)
    }
    
    def __init__(self, policy_manager: 'PolicyManager'):
        """
        Initialize validator with a PolicyManager instance.
        
        Args:
            policy_manager: The PolicyManager containing all policy configurations
        """
        self.manager = policy_manager
    
    def validate_all(self) -> ValidationResult:
        """
        Run all validation checks.
        
        Returns:
            ValidationResult with all issues found
        """
        result = ValidationResult(valid=True)
        
        # 1. Validate rule ID ranges
        self._validate_rule_ids(result)
        
        # 2. Validate duplicate rule IDs
        self._validate_duplicate_rule_ids(result)
        
        # 3. Validate prefix formats
        self._validate_prefix_formats(result)
        
        # 4. Validate community formats
        self._validate_community_formats(result)
        
        # 5. Validate reference integrity
        self._validate_references(result)
        
        # 6. Validate circular dependencies
        self._validate_circular_dependencies(result)
        
        # 7. Validate policy rule constraints
        self._validate_policy_rule_constraints(result)
        
        # 8. Validate regex patterns
        self._validate_regex_patterns(result)
        
        return result
    
    def _validate_rule_ids(self, result: ValidationResult) -> None:
        """Validate rule IDs are within DNOS limits."""
        # Prefix-lists IPv4
        for name, pl in self.manager.prefix_lists_v4.items():
            min_id, max_id = self.LIMITS['prefix_list']
            for rule in pl.rules:
                if rule.rule_id < min_id or rule.rule_id > max_id:
                    result.add_error(
                        f"prefix-list ipv4 {name}",
                        f"Rule ID {rule.rule_id} is out of range",
                        f"Rule ID must be {min_id}-{max_id}",
                        str(rule.rule_id)
                    )
        
        # Prefix-lists IPv6
        for name, pl in self.manager.prefix_lists_v6.items():
            min_id, max_id = self.LIMITS['prefix_list']
            for rule in pl.rules:
                if rule.rule_id < min_id or rule.rule_id > max_id:
                    result.add_error(
                        f"prefix-list ipv6 {name}",
                        f"Rule ID {rule.rule_id} is out of range",
                        f"Rule ID must be {min_id}-{max_id}",
                        str(rule.rule_id)
                    )
        
        # Community-lists
        for name, cl in self.manager.community_lists.items():
            min_id, max_id = self.LIMITS['community_list']
            for rule in cl.rules:
                if rule.rule_id < min_id or rule.rule_id > max_id:
                    result.add_error(
                        f"community-list {name}",
                        f"Rule ID {rule.rule_id} is out of range",
                        f"Rule ID must be {min_id}-{max_id}",
                        str(rule.rule_id)
                    )
        
        # ExtCommunity-lists
        for name, ecl in self.manager.extcommunity_lists.items():
            min_id, max_id = self.LIMITS['extcommunity_list']
            for rule in ecl.rules:
                if rule.rule_id < min_id or rule.rule_id > max_id:
                    result.add_error(
                        f"extcommunity-list {name}",
                        f"Rule ID {rule.rule_id} is out of range",
                        f"Rule ID must be {min_id}-{max_id}",
                        str(rule.rule_id)
                    )
        
        # Large-community-lists
        for name, lcl in self.manager.large_community_lists.items():
            min_id, max_id = self.LIMITS['large_community_list']
            for rule in lcl.rules:
                if rule.rule_id < min_id or rule.rule_id > max_id:
                    result.add_error(
                        f"large-community-list {name}",
                        f"Rule ID {rule.rule_id} is out of range",
                        f"Rule ID must be {min_id}-{max_id}",
                        str(rule.rule_id)
                    )
        
        # AS-path-lists
        for name, apl in self.manager.as_path_lists.items():
            min_id, max_id = self.LIMITS['as_path_list']
            for rule in apl.rules:
                if rule.rule_id < min_id or rule.rule_id > max_id:
                    result.add_error(
                        f"as-path-list {name}",
                        f"Rule ID {rule.rule_id} is out of range",
                        f"Rule ID must be {min_id}-{max_id}",
                        str(rule.rule_id)
                    )
        
        # Policies
        for name, pol in self.manager.policies.items():
            min_id, max_id = self.LIMITS['policy']
            for rule in pol.rules:
                if rule.rule_id < min_id or rule.rule_id > max_id:
                    result.add_error(
                        f"policy {name}",
                        f"Rule ID {rule.rule_id} is out of range",
                        f"Rule ID must be {min_id}-{max_id}",
                        str(rule.rule_id)
                    )
    
    def _validate_duplicate_rule_ids(self, result: ValidationResult) -> None:
        """Check for duplicate rule IDs within each list/policy."""
        # Check all list types
        for name, pl in {**self.manager.prefix_lists_v4, **self.manager.prefix_lists_v6}.items():
            seen_ids = set()
            for rule in pl.rules:
                if rule.rule_id in seen_ids:
                    result.add_error(
                        f"prefix-list {name}",
                        f"Duplicate rule ID {rule.rule_id}",
                        "Each rule must have a unique ID",
                        str(rule.rule_id)
                    )
                seen_ids.add(rule.rule_id)
        
        for name, cl in self.manager.community_lists.items():
            seen_ids = set()
            for rule in cl.rules:
                if rule.rule_id in seen_ids:
                    result.add_error(
                        f"community-list {name}",
                        f"Duplicate rule ID {rule.rule_id}",
                        "Each rule must have a unique ID",
                        str(rule.rule_id)
                    )
                seen_ids.add(rule.rule_id)
        
        for name, ecl in self.manager.extcommunity_lists.items():
            seen_ids = set()
            for rule in ecl.rules:
                if rule.rule_id in seen_ids:
                    result.add_error(
                        f"extcommunity-list {name}",
                        f"Duplicate rule ID {rule.rule_id}",
                        "Each rule must have a unique ID",
                        str(rule.rule_id)
                    )
                seen_ids.add(rule.rule_id)
        
        for name, lcl in self.manager.large_community_lists.items():
            seen_ids = set()
            for rule in lcl.rules:
                if rule.rule_id in seen_ids:
                    result.add_error(
                        f"large-community-list {name}",
                        f"Duplicate rule ID {rule.rule_id}",
                        "Each rule must have a unique ID",
                        str(rule.rule_id)
                    )
                seen_ids.add(rule.rule_id)
        
        for name, apl in self.manager.as_path_lists.items():
            seen_ids = set()
            for rule in apl.rules:
                if rule.rule_id in seen_ids:
                    result.add_error(
                        f"as-path-list {name}",
                        f"Duplicate rule ID {rule.rule_id}",
                        "Each rule must have a unique ID",
                        str(rule.rule_id)
                    )
                seen_ids.add(rule.rule_id)
        
        for name, pol in self.manager.policies.items():
            seen_ids = set()
            for rule in pol.rules:
                if rule.rule_id in seen_ids:
                    result.add_error(
                        f"policy {name}",
                        f"Duplicate rule ID {rule.rule_id}",
                        "Each rule must have a unique ID",
                        str(rule.rule_id)
                    )
                seen_ids.add(rule.rule_id)
    
    def _validate_prefix_formats(self, result: ValidationResult) -> None:
        """Validate prefix format in prefix-lists."""
        for name, pl in self.manager.prefix_lists_v4.items():
            for rule in pl.rules:
                valid, error = self._validate_ipv4_prefix(rule.prefix)
                if not valid:
                    result.add_error(
                        f"prefix-list ipv4 {name}",
                        f"Invalid IPv4 prefix: {error}",
                        "Use format: A.B.C.D/M (e.g., 10.0.0.0/8)",
                        str(rule.rule_id)
                    )
                # Validate matching-len constraints
                if rule.eq is not None and (rule.ge is not None or rule.le is not None):
                    result.add_error(
                        f"prefix-list ipv4 {name}",
                        "Cannot use 'eq' with 'ge' or 'le'",
                        "Use either 'eq' alone or 'ge/le' combination",
                        str(rule.rule_id)
                    )
        
        for name, pl in self.manager.prefix_lists_v6.items():
            for rule in pl.rules:
                valid, error = self._validate_ipv6_prefix(rule.prefix)
                if not valid:
                    result.add_error(
                        f"prefix-list ipv6 {name}",
                        f"Invalid IPv6 prefix: {error}",
                        "Use format: X:X:X::/M (e.g., 2001:db8::/32)",
                        str(rule.rule_id)
                    )
    
    def _validate_ipv4_prefix(self, prefix: str) -> Tuple[bool, str]:
        """Validate IPv4 prefix format."""
        if '/' not in prefix:
            return False, "Missing prefix length"
        
        parts = prefix.split('/')
        if len(parts) != 2:
            return False, "Invalid format"
        
        # Validate address
        addr_parts = parts[0].split('.')
        if len(addr_parts) != 4:
            return False, "IPv4 address must have 4 octets"
        
        for octet in addr_parts:
            try:
                val = int(octet)
                if val < 0 or val > 255:
                    return False, f"Octet {octet} out of range (0-255)"
            except ValueError:
                return False, f"Invalid octet: {octet}"
        
        # Validate prefix length
        try:
            plen = int(parts[1])
            if plen < 0 or plen > 32:
                return False, "Prefix length must be 0-32"
        except ValueError:
            return False, "Prefix length must be numeric"
        
        return True, ""
    
    def _validate_ipv6_prefix(self, prefix: str) -> Tuple[bool, str]:
        """Validate IPv6 prefix format (basic validation)."""
        if '/' not in prefix:
            return False, "Missing prefix length"
        
        parts = prefix.split('/')
        if len(parts) != 2:
            return False, "Invalid format"
        
        # Basic validation - just check prefix length
        try:
            plen = int(parts[1])
            if plen < 0 or plen > 128:
                return False, "Prefix length must be 0-128"
        except ValueError:
            return False, "Prefix length must be numeric"
        
        return True, ""
    
    def _validate_community_formats(self, result: ValidationResult) -> None:
        """Validate community formats in community-lists."""
        valid_well_known = {
            'internet', 'accept-own', 'local-AS', 'no-export',
            'no-advertise', 'no-LLGR', 'LLGR-stale'
        }
        
        for name, cl in self.manager.community_lists.items():
            for rule in cl.rules:
                if rule.match_type == 'well-known':
                    if rule.value not in valid_well_known:
                        result.add_error(
                            f"community-list {name}",
                            f"Unknown well-known community: {rule.value}",
                            f"Valid values: {', '.join(valid_well_known)}",
                            str(rule.rule_id)
                        )
                elif rule.match_type == 'value':
                    # Validate AS:ID format
                    if ':' not in rule.value:
                        result.add_error(
                            f"community-list {name}",
                            f"Invalid community format: {rule.value}",
                            "Use format: AS:ID (e.g., 65000:100)",
                            str(rule.rule_id)
                        )
    
    def _validate_references(self, result: ValidationResult) -> None:
        """Validate that all referenced lists/policies exist."""
        from .policies import MatchType, SetActionType
        
        # Collect all available names
        all_prefix_lists = (
            set(self.manager.prefix_lists_v4.keys()) |
            set(self.manager.prefix_lists_v6.keys())
        )
        all_community_lists = set(self.manager.community_lists.keys())
        all_extcommunity_lists = set(self.manager.extcommunity_lists.keys())
        all_large_community_lists = set(self.manager.large_community_lists.keys())
        all_as_path_lists = set(self.manager.as_path_lists.keys())
        all_policies = set(self.manager.policies.keys())
        
        # Check references in policies
        for name, pol in self.manager.policies.items():
            for rule in pol.rules:
                # Check match conditions
                for match in rule.match_conditions:
                    if match.match_type in (MatchType.IPV4_PREFIX, MatchType.IPV6_PREFIX,
                                            MatchType.IPV4_NEXT_HOP, MatchType.IPV6_NEXT_HOP):
                        if match.value not in all_prefix_lists:
                            result.add_error(
                                f"policy {name}",
                                f"Referenced prefix-list '{match.value}' does not exist",
                                "Create the prefix-list or correct the name",
                                str(rule.rule_id)
                            )
                    elif match.match_type == MatchType.COMMUNITY:
                        if match.value not in all_community_lists:
                            result.add_error(
                                f"policy {name}",
                                f"Referenced community-list '{match.value}' does not exist",
                                "Create the community-list or correct the name",
                                str(rule.rule_id)
                            )
                    elif match.match_type == MatchType.EXTCOMMUNITY:
                        if match.value not in all_extcommunity_lists:
                            result.add_error(
                                f"policy {name}",
                                f"Referenced extcommunity-list '{match.value}' does not exist",
                                "Create the extcommunity-list or correct the name",
                                str(rule.rule_id)
                            )
                    elif match.match_type == MatchType.LARGE_COMMUNITY:
                        if match.value not in all_large_community_lists:
                            result.add_error(
                                f"policy {name}",
                                f"Referenced large-community-list '{match.value}' does not exist",
                                "Create the large-community-list or correct the name",
                                str(rule.rule_id)
                            )
                    elif match.match_type == MatchType.AS_PATH:
                        if match.value not in all_as_path_lists:
                            result.add_error(
                                f"policy {name}",
                                f"Referenced as-path-list '{match.value}' does not exist",
                                "Create the as-path-list or correct the name",
                                str(rule.rule_id)
                            )
                
                # Check set actions that reference lists
                for set_action in rule.set_actions:
                    if set_action.action_type == SetActionType.COMMUNITY_LIST:
                        if set_action.value not in all_community_lists:
                            result.add_error(
                                f"policy {name}",
                                f"Referenced community-list '{set_action.value}' does not exist",
                                "Create the community-list or correct the name",
                                str(rule.rule_id)
                            )
                    elif set_action.action_type == SetActionType.EXTCOMMUNITY_LIST:
                        if set_action.value not in all_extcommunity_lists:
                            result.add_error(
                                f"policy {name}",
                                f"Referenced extcommunity-list '{set_action.value}' does not exist",
                                "Create the extcommunity-list or correct the name",
                                str(rule.rule_id)
                            )
                    elif set_action.action_type == SetActionType.LARGE_COMMUNITY_LIST:
                        if set_action.value not in all_large_community_lists:
                            result.add_error(
                                f"policy {name}",
                                f"Referenced large-community-list '{set_action.value}' does not exist",
                                "Create the large-community-list or correct the name",
                                str(rule.rule_id)
                            )
                
                # Check called policies
                if rule.call_policy:
                    if rule.call_policy not in all_policies:
                        result.add_error(
                            f"policy {name}",
                            f"Called policy '{rule.call_policy}' does not exist",
                            "Create the policy or correct the name",
                            str(rule.rule_id)
                        )
    
    def _validate_circular_dependencies(self, result: ValidationResult) -> None:
        """Detect circular dependencies in policy call chains."""
        # Build call graph
        call_graph: Dict[str, Set[str]] = {}
        for name, pol in self.manager.policies.items():
            call_graph[name] = set()
            for rule in pol.rules:
                if rule.call_policy:
                    call_graph[name].add(rule.call_policy)
        
        # Check for cycles using DFS
        def has_cycle(node: str, visited: Set[str], rec_stack: Set[str], path: List[str]) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in call_graph.get(node, set()):
                if neighbor not in visited:
                    cycle_path = has_cycle(neighbor, visited, rec_stack, path)
                    if cycle_path:
                        return cycle_path
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]
            
            path.pop()
            rec_stack.remove(node)
            return None
        
        visited: Set[str] = set()
        for policy_name in call_graph:
            if policy_name not in visited:
                cycle = has_cycle(policy_name, visited, set(), [])
                if cycle:
                    cycle_str = " -> ".join(cycle)
                    result.add_error(
                        f"policy {policy_name}",
                        f"Circular dependency detected: {cycle_str}",
                        "Remove or modify 'call' statements to break the cycle"
                    )
                    break  # Report only one cycle to avoid noise
    
    def _validate_policy_rule_constraints(self, result: ValidationResult) -> None:
        """Validate policy rule constraints."""
        from .policies import RuleAction, OnMatchAction
        
        for name, pol in self.manager.policies.items():
            for rule in pol.rules:
                # Cannot have set actions in deny rules
                if rule.action == RuleAction.DENY and rule.set_actions:
                    result.add_error(
                        f"policy {name}",
                        "Cannot configure set actions under deny rules",
                        "Remove set actions or change rule to 'allow'",
                        str(rule.rule_id)
                    )
                
                # on-match goto must reference higher rule ID
                if rule.on_match == OnMatchAction.GOTO and rule.on_match_goto_rule:
                    if rule.on_match_goto_rule <= rule.rule_id:
                        result.add_error(
                            f"policy {name}",
                            f"on-match goto {rule.on_match_goto_rule} must be higher than current rule {rule.rule_id}",
                            "Use a higher rule ID for goto target",
                            str(rule.rule_id)
                        )
                    
                    # Check if target rule exists
                    target_exists = any(r.rule_id == rule.on_match_goto_rule for r in pol.rules)
                    if not target_exists:
                        result.add_warning(
                            f"policy {name}",
                            f"on-match goto target rule {rule.on_match_goto_rule} does not exist",
                            "Create the target rule or update the goto",
                            str(rule.rule_id)
                        )
    
    def _validate_regex_patterns(self, result: ValidationResult) -> None:
        """Validate regex patterns are syntactically correct."""
        # Community-lists with regex
        for name, cl in self.manager.community_lists.items():
            for rule in cl.rules:
                if rule.match_type == 'regex':
                    try:
                        re.compile(rule.value)
                    except re.error as e:
                        result.add_error(
                            f"community-list {name}",
                            f"Invalid regex pattern: {e}",
                            "Fix the regex syntax",
                            str(rule.rule_id)
                        )
        
        # Large-community-lists with regex
        for name, lcl in self.manager.large_community_lists.items():
            for rule in lcl.rules:
                if rule.match_type == 'regex':
                    try:
                        re.compile(rule.value)
                    except re.error as e:
                        result.add_error(
                            f"large-community-list {name}",
                            f"Invalid regex pattern: {e}",
                            "Fix the regex syntax",
                            str(rule.rule_id)
                        )
        
        # AS-path-lists with regex
        for name, apl in self.manager.as_path_lists.items():
            for rule in apl.rules:
                if rule.match_type == 'regex':
                    try:
                        re.compile(rule.value)
                    except re.error as e:
                        result.add_error(
                            f"as-path-list {name}",
                            f"Invalid regex pattern: {e}",
                            "Fix the regex syntax",
                            str(rule.rule_id)
                        )


def validate_policy_manager(manager: 'PolicyManager') -> ValidationResult:
    """
    Convenience function to validate a PolicyManager.
    
    Args:
        manager: PolicyManager instance to validate
        
    Returns:
        ValidationResult with all issues found
    """
    validator = PolicyValidator(manager)
    return validator.validate_all()


def validate_and_display(manager: 'PolicyManager') -> bool:
    """
    Validate a PolicyManager and display results.
    
    Args:
        manager: PolicyManager instance to validate
        
    Returns:
        True if validation passed (no errors), False otherwise
    """
    result = validate_policy_manager(manager)
    result.display()
    return result.valid
