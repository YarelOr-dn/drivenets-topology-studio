"""
New Route-Policy Language Module for DNOS (EPIC SW-181332)

This module implements the NEW programming-like route-policy language
that replaces the old rule-based policy syntax.

NEW Syntax (SW-181332):
```
routing-policy
  route-policy policy_name($param1, $param2) {
    if (condition) {
      set attribute value
      return allow|deny
    }
    return allow|deny
  }
```

Key Features:
- if/else-if/else blocks with curly braces
- Parameters with $ prefix
- Operators: ==, !=, <, >, <=, >=, and, or, not
- return allow|deny statements
- set attribute actions
- exec-policy calls with parameters
- Wildcard policy calls: exec-policy POLICY*

Author: SCALER Wizard
Reference: https://drivenets.atlassian.net/browse/SW-181332
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
from rich.syntax import Syntax

console = Console()


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class ReturnAction(str, Enum):
    """Return action types for route-policy."""
    ALLOW = "allow"
    DENY = "deny"
    NO_MATCH = "no-match"  # Continue to next policy in chain
    NONE = ""  # Just 'return' without explicit action


class Operator(str, Enum):
    """Comparison operators for conditions."""
    EQ = "=="
    NE = "!="
    LT = "<"
    GT = ">"
    LE = "<="
    GE = ">="
    # Text aliases (converted to symbols during generation)
    EQ_TEXT = "eq"
    NE_TEXT = "ne"
    LT_TEXT = "lt"
    GT_TEXT = "gt"
    LE_TEXT = "le"
    GE_TEXT = "ge"
    # List operators for matching against lists
    IN = "in"  # community in [list] or community in $param
    NOT_IN = "not in"  # negated list match


class LogicalOperator(str, Enum):
    """Logical operators for combining conditions."""
    AND = "and"
    OR = "or"
    NOT = "not"
    AND_NOT = "and not"
    OR_NOT = "or not"


class MatchAttribute(str, Enum):
    """Attributes that can be matched in conditions."""
    MED = "med"
    WEIGHT = "weight"
    LOCAL_PREFERENCE = "local-preference"
    AS_PATH = "as-path"
    AS_PATH_LENGTH = "as-path-length"
    COMMUNITY = "community"
    PREFIX_IPV4 = "prefix-ipv4"  # IPv4 prefix matching
    PREFIX_IPV6 = "prefix-ipv6"  # IPv6 prefix matching
    NEXTHOP = "nexthop"
    ORIGIN = "origin"
    TAG = "tag"
    RPKI = "rpki"  # RPKI validation state: valid, invalid, not-found
    EXTCOMMUNITY = "extcommunity"
    LARGE_COMMUNITY = "large-community"
    

class SetAttribute(str, Enum):
    """Attributes that can be set in actions."""
    MED = "med"
    WEIGHT = "weight"
    LOCAL_PREFERENCE = "local-preference"
    NEXTHOP = "nexthop"
    ORIGIN = "origin"
    TAG = "tag"
    COMMUNITY = "community"
    AS_PATH = "as-path"
    RPKI = "rpki"  # set rpki valid|invalid|not-found
    SR_LABEL_INDEX = "sr-label-index"  # set sr-label-index <value>
    EXTCOMMUNITY_RT = "extcommunity rt"  # set extcommunity rt <value>
    EXTCOMMUNITY_SOO = "extcommunity soo"
    EXTCOMMUNITY_COLOR = "extcommunity color"
    LARGE_COMMUNITY = "large-community"


class SetOperation(str, Enum):
    """Operations for set actions."""
    SET = ""  # Simple set
    ADD = "add"
    REMOVE = "remove"
    PREPEND = "prepend"
    EXCLUDE = "exclude"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Condition:
    """A single condition in an if statement.
    
    Examples:
        - med > 100
        - community == "65000:100"
        - as-path-length <= 5
        - nexthop == "192.168.1.1"
    """
    attribute: MatchAttribute
    operator: Operator
    value: str  # The comparison value (quoted for strings)
    
    def to_dnos(self) -> str:
        """Generate DNOS condition string."""
        op = self.operator.value
        # Convert text aliases to symbols
        if self.operator in (Operator.EQ_TEXT,):
            op = "=="
        elif self.operator in (Operator.NE_TEXT,):
            op = "!="
        elif self.operator in (Operator.LT_TEXT,):
            op = "<"
        elif self.operator in (Operator.GT_TEXT,):
            op = ">"
        elif self.operator in (Operator.LE_TEXT,):
            op = "<="
        elif self.operator in (Operator.GE_TEXT,):
            op = ">="
        
        val = self.value
        
        # Handle 'in' and 'not in' operators - value should be a list or variable
        if self.operator in (Operator.IN, Operator.NOT_IN):
            # If value starts with $, it's a parameter reference
            if val.startswith('$'):
                return f"{self.attribute.value} {op} {val}"
            # If value is a list name (alphanumeric), use as-is
            elif val.isidentifier():
                return f"{self.attribute.value} {op} {val}"
            # Otherwise, it should be an inline list like [val1, val2]
            elif val.startswith('[') and val.endswith(']'):
                return f"{self.attribute.value} {op} {val}"
            else:
                # Wrap in brackets for inline list
                return f"{self.attribute.value} {op} [{val}]"
        
        # Quote string values if not already quoted for certain attributes
        if self.attribute in (MatchAttribute.AS_PATH, MatchAttribute.COMMUNITY, 
                             MatchAttribute.NEXTHOP, MatchAttribute.PREFIX_IPV4,
                             MatchAttribute.PREFIX_IPV6, MatchAttribute.EXTCOMMUNITY,
                             MatchAttribute.LARGE_COMMUNITY):
            if not (val.startswith('"') and val.endswith('"')) and not val.startswith('$'):
                # Don't quote if it's a parameter variable
                if not val.startswith('['):  # Don't quote inline lists
                    val = f'"{val}"' if ' ' in val or ':' in val else val
        
        return f"{self.attribute.value} {op} {val}"


@dataclass
class CompoundCondition:
    """A compound condition with logical operators.
    
    Examples:
        - (med > 100) and (weight < 50)
        - not (as-path-length > 10)
        - (community == "65000:100") or (community == "65000:200")
    """
    conditions: List[Union[Condition, 'CompoundCondition']]
    operators: List[LogicalOperator]  # One less than conditions
    negate: bool = False  # Wrap entire thing in 'not'
    
    def to_dnos(self) -> str:
        """Generate DNOS condition string."""
        if len(self.conditions) == 1:
            inner = self.conditions[0].to_dnos()
            if self.negate:
                return f"not ({inner})"
            return inner
        
        parts = []
        for i, cond in enumerate(self.conditions):
            cond_str = cond.to_dnos()
            # Wrap in parens if compound
            if isinstance(cond, CompoundCondition) and len(cond.conditions) > 1:
                cond_str = f"({cond_str})"
            parts.append(cond_str)
            if i < len(self.conditions) - 1:
                # Use operator if available, default to "and"
                if i < len(self.operators):
                    parts.append(self.operators[i].value)
                else:
                    parts.append("and")  # Default to "and" if not specified
        
        result = " ".join(parts)
        if self.negate:
            return f"not ({result})"
        return result


@dataclass
class SetAction:
    """A set action in a route-policy.
    
    DNOS New Syntax Examples:
        - set med 100
        - set weight 50
        - add community 65000:200  (not 'set community add')
        - set as-path prepend as-number 65000
        - set as-path prepend last-as 3
        - set rpki valid|invalid|not-found
        - set sr-label-index <value>
        - set extcommunity rt <value> [additive]
    """
    attribute: SetAttribute
    value: str
    operation: SetOperation = SetOperation.SET
    extra: Optional[str] = None  # For as-path prepend: "as-number" or "last-as", for extcommunity: "additive"
    
    def to_dnos(self, indent: int = 4) -> str:
        """Generate DNOS set statement."""
        sp = " " * indent
        
        if self.attribute == SetAttribute.COMMUNITY:
            if self.operation == SetOperation.ADD:
                # DNOS new syntax: 'add community' not 'set community add'
                return f"{sp}add community {self.value}"
            elif self.operation == SetOperation.REMOVE:
                return f"{sp}remove community {self.value}"
            else:
                return f"{sp}set community {self.value}"
        
        elif self.attribute == SetAttribute.AS_PATH:
            if self.operation == SetOperation.PREPEND:
                if self.extra == "last-as":
                    return f"{sp}set as-path prepend last-as {self.value}"
                else:
                    return f"{sp}set as-path prepend as-number {self.value}"
            elif self.operation == SetOperation.EXCLUDE:
                if self.extra == "range":
                    # value should be "start to end"
                    return f"{sp}set as-path exclude from {self.value}"
                else:
                    return f"{sp}set as-path exclude {self.value}"
            else:
                return f"{sp}set as-path {self.value}"
        
        elif self.attribute == SetAttribute.RPKI:
            # set rpki valid|invalid|not-found
            return f"{sp}set rpki {self.value}"
        
        elif self.attribute == SetAttribute.SR_LABEL_INDEX:
            # set sr-label-index <value> [global-block-origination]
            if self.extra == "global-block-origination":
                return f"{sp}set sr-label-index {self.value} global-block-origination"
            return f"{sp}set sr-label-index {self.value}"
        
        elif self.attribute == SetAttribute.EXTCOMMUNITY_RT:
            if self.extra == "additive":
                return f"{sp}set extcommunity rt {self.value} additive"
            return f"{sp}set extcommunity rt {self.value}"
        
        elif self.attribute == SetAttribute.EXTCOMMUNITY_SOO:
            return f"{sp}set extcommunity soo {self.value}"
        
        elif self.attribute == SetAttribute.EXTCOMMUNITY_COLOR:
            return f"{sp}set extcommunity color {self.value}"
        
        elif self.attribute == SetAttribute.LARGE_COMMUNITY:
            if self.operation == SetOperation.ADD:
                return f"{sp}add large-community {self.value}"
            elif self.operation == SetOperation.REMOVE:
                return f"{sp}remove large-community {self.value}"
            return f"{sp}set large-community {self.value}"
        
        else:
            val = self.value
            # Quote string values if needed for nexthop
            if self.attribute == SetAttribute.NEXTHOP:
                if not (val.startswith('"') and val.endswith('"')) and not val.startswith('$'):
                    val = f'"{val}"'
            return f"{sp}set {self.attribute.value} {val}"


@dataclass
class SetResultStatement:
    """A set allow/deny statement that sets result without returning.
    
    DNOS Syntax:
        - set allow  (sets result to allow, continues execution)
        - set deny   (sets result to deny, continues execution)
    
    When 'return' is called without a value, this result is used.
    """
    result: ReturnAction  # ALLOW or DENY
    
    def to_dnos(self, indent: int = 4) -> str:
        """Generate DNOS set result statement."""
        sp = " " * indent
        return f"{sp}set {self.result.value}"


@dataclass
class ReturnStatement:
    """A return statement in a route-policy.
    
    DNOS Syntax:
        - return allow    - Permits the route and stops policy evaluation
        - return deny     - Denies the route and stops policy evaluation
        - return no-match - Continue to next policy in chain
        - return          - Stops and uses previous 'set allow/deny' result
    """
    action: ReturnAction = ReturnAction.NONE
    
    def to_dnos(self, indent: int = 4) -> str:
        """Generate DNOS return statement."""
        sp = " " * indent
        if self.action == ReturnAction.NONE:
            return f"{sp}return"
        return f"{sp}return {self.action.value}"


@dataclass
class ExecPolicy:
    """An exec-policy call to another policy.
    
    Examples:
        - exec-policy MY_POLICY
        - exec-policy MY_POLICY($community_value)
        - exec-policy POLICY*  (wildcard call)
    """
    policy_name: str
    parameters: List[str] = field(default_factory=list)  # Parameters passed to the policy
    
    def to_dnos(self, indent: int = 4) -> str:
        """Generate DNOS exec-policy statement."""
        sp = " " * indent
        if self.parameters:
            params = ", ".join(self.parameters)
            return f"{sp}exec-policy {self.policy_name}({params})"
        return f"{sp}exec-policy {self.policy_name}"


@dataclass
class IfBlock:
    """An if/elif/else block in a route-policy.
    
    DNOS New Syntax Structure:
        if (condition) {
            // actions
        }
        elif (condition) {
            // actions
        }
        else {
            // actions
        }
    
    Note: DNOS uses 'elif' (not 'else if') for else-if blocks.
    """
    condition: Union[Condition, CompoundCondition]
    actions: List[Union[SetAction, ReturnStatement, ExecPolicy, 'IfBlock']]
    else_if_blocks: List['IfBlock'] = field(default_factory=list)  # elif blocks
    else_actions: List[Union[SetAction, ReturnStatement, ExecPolicy]] = field(default_factory=list)
    
    def to_dnos(self, indent: int = 4) -> str:
        """Generate DNOS if block."""
        sp = " " * indent
        lines = []
        
        # if condition
        cond_str = self.condition.to_dnos()
        lines.append(f"{sp}if ({cond_str}) {{")
        
        # if actions
        for action in self.actions:
            lines.append(action.to_dnos(indent + 2))
        
        lines.append(f"{sp}}}")
        
        # elif blocks (DNOS uses 'elif', not 'else if')
        for else_if in self.else_if_blocks:
            lines.append(f"{sp}elif ({else_if.condition.to_dnos()}) {{")
            for action in else_if.actions:
                lines.append(action.to_dnos(indent + 2))
            lines.append(f"{sp}}}")
        
        # else block
        if self.else_actions:
            lines.append(f"{sp}else {{")
            for action in self.else_actions:
                lines.append(action.to_dnos(indent + 2))
            lines.append(f"{sp}}}")
        
        return "\n".join(lines)


@dataclass
class RoutePolicy:
    """A complete route-policy definition using new syntax.
    
    Structure:
        route-policy policy_name($param1, $param2) {
            // statements (if blocks, set actions, return, exec-policy)
        }
    """
    name: str
    parameters: List[str] = field(default_factory=list)  # Parameter names (without $)
    statements: List[Union[IfBlock, SetAction, ReturnStatement, ExecPolicy]] = field(default_factory=list)
    description: Optional[str] = None
    
    def to_dnos(self, indent: int = 2) -> str:
        """Generate DNOS route-policy config."""
        sp = " " * indent
        lines = []
        
        # Policy header
        if self.parameters:
            params = ", ".join(f"${p}" for p in self.parameters)
            lines.append(f"{sp}route-policy {self.name}({params}) {{")
        else:
            lines.append(f"{sp}route-policy {self.name} {{")
        
        # Description as comment (if new syntax supports it)
        if self.description:
            lines.append(f"{sp}  // {self.description}")
        
        # Statements
        for stmt in self.statements:
            lines.append(stmt.to_dnos(indent + 2))
        
        lines.append(f"{sp}}}")
        return "\n".join(lines)
    
    def get_called_policies(self) -> List[str]:
        """Get list of policies called by this policy."""
        called = []
        
        def extract_from_actions(actions):
            for action in actions:
                if isinstance(action, ExecPolicy):
                    called.append(action.policy_name)
                elif isinstance(action, IfBlock):
                    extract_from_actions(action.actions)
                    for else_if in action.else_if_blocks:
                        extract_from_actions(else_if.actions)
                    extract_from_actions(action.else_actions)
        
        extract_from_actions(self.statements)
        return called


# =============================================================================
# ROUTE POLICY MANAGER (NEW SYNTAX)
# =============================================================================

class RoutePolicyManager:
    """
    Manager for the NEW route-policy language.
    
    Stores and manages route-policies using the new programming-like syntax.
    """
    
    def __init__(self):
        """Initialize empty policy manager."""
        self.policies: Dict[str, RoutePolicy] = {}
        self._dirty = False
    
    def is_empty(self) -> bool:
        """Check if no policies are configured."""
        return not self.policies
    
    def get_all_policy_names(self) -> List[str]:
        """Get list of all policy names."""
        return list(self.policies.keys())
    
    def add_policy(self, policy: RoutePolicy) -> None:
        """Add or update a route-policy."""
        self.policies[policy.name] = policy
        self._dirty = True
    
    def get_policy(self, name: str) -> Optional[RoutePolicy]:
        """Get a policy by name."""
        return self.policies.get(name)
    
    def delete_policy(self, name: str) -> bool:
        """Delete a policy by name."""
        if name in self.policies:
            del self.policies[name]
            self._dirty = True
            return True
        return False
    
    def to_dnos(self) -> str:
        """Generate complete DNOS routing-policy configuration."""
        if self.is_empty():
            return ""
        
        lines = ["routing-policy"]
        for name in sorted(self.policies.keys()):
            lines.append(self.policies[name].to_dnos(2))
        lines.append("!")
        return "\n".join(lines)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all policies."""
        total_statements = 0
        total_if_blocks = 0
        total_params = 0
        
        for policy in self.policies.values():
            total_params += len(policy.parameters)
            for stmt in policy.statements:
                if isinstance(stmt, IfBlock):
                    total_if_blocks += 1
                total_statements += 1
        
        return {
            'policies': len(self.policies),
            'total_statements': total_statements,
            'total_if_blocks': total_if_blocks,
            'total_params': total_params
        }
    
    def display_summary(self) -> None:
        """Display a summary table of all policies."""
        summary = self.get_summary()
        
        table = Table(title="Route Policy Summary (New Syntax)", show_header=True)
        table.add_column("Component", style="cyan")
        table.add_column("Count", justify="right", style="green")
        
        table.add_row("Route Policies", str(summary['policies']))
        table.add_row("Total Statements", str(summary['total_statements']))
        table.add_row("If Blocks", str(summary['total_if_blocks']))
        table.add_row("Parameters Used", str(summary['total_params']))
        
        console.print(table)
    
    def validate_dependencies(self) -> Tuple[bool, List[str]]:
        """
        Validate policy dependencies.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        all_policy_names = set(self.policies.keys())
        
        for policy in self.policies.values():
            called = policy.get_called_policies()
            for called_name in called:
                # Check for wildcard calls
                if '*' in called_name:
                    pattern = called_name.replace('*', '.*')
                    matching = [p for p in all_policy_names if re.match(pattern, p)]
                    if not matching:
                        errors.append(f"Policy '{policy.name}': exec-policy '{called_name}' matches no policies")
                else:
                    if called_name not in all_policy_names:
                        errors.append(f"Policy '{policy.name}': calls undefined policy '{called_name}'")
        
        return (len(errors) == 0, errors)


# =============================================================================
# INTERACTIVE BUILDERS
# =============================================================================

class ConditionBuilder:
    """Interactive builder for creating conditions."""
    
    @staticmethod
    def build_simple() -> Optional[Condition]:
        """Build a simple condition interactively."""
        from .core import BackException
        
        console.print("\n[bold]Build Condition:[/bold]")
        console.print("  Available attributes:")
        for i, attr in enumerate(MatchAttribute, 1):
            console.print(f"    [{i}] {attr.value}")
        console.print("  [B] Back")
        
        choices = [str(i) for i in range(1, len(MatchAttribute) + 1)] + ["b", "B"]
        choice = Prompt.ask("Select attribute", choices=choices).lower()
        
        if choice == "b":
            raise BackException()
        
        attr = list(MatchAttribute)[int(choice) - 1]
        
        # Operator
        console.print("\n  Operators: ==, !=, <, >, <=, >=")
        op_str = Prompt.ask("Operator", default="==")
        
        try:
            operator = Operator(op_str)
        except ValueError:
            console.print(f"[red]Invalid operator: {op_str}[/red]")
            return None
        
        # Value
        if attr in (MatchAttribute.MED, MatchAttribute.WEIGHT, 
                   MatchAttribute.LOCAL_PREFERENCE, MatchAttribute.AS_PATH_LENGTH,
                   MatchAttribute.TAG):
            value = Prompt.ask("Value (number)")
        else:
            value = Prompt.ask("Value (string, will be quoted)")
        
        return Condition(attribute=attr, operator=operator, value=value)
    
    @staticmethod
    def build_compound(existing: List[Condition] = None) -> Optional[CompoundCondition]:
        """Build a compound condition with multiple conditions."""
        from .core import BackException
        
        conditions = existing or []
        operators = []
        
        if not conditions:
            cond = ConditionBuilder.build_simple()
            if cond:
                conditions.append(cond)
            else:
                return None
        
        while True:
            console.print("\n[bold]Current condition:[/bold]")
            temp = CompoundCondition(conditions=conditions, operators=operators)
            console.print(f"  {temp.to_dnos()}")
            
            console.print("\n  [1] Add 'and' condition")
            console.print("  [2] Add 'or' condition")
            console.print("  [3] Negate entire condition (wrap in 'not')")
            console.print("  [D] Done")
            console.print("  [B] Back")
            
            choice = Prompt.ask("Select", choices=["1", "2", "3", "d", "D", "b", "B"]).lower()
            
            if choice == "b":
                if len(conditions) <= 1:
                    raise BackException()
                conditions.pop()
                if operators:
                    operators.pop()
            elif choice == "d":
                break
            elif choice == "1":
                operators.append(LogicalOperator.AND)
                cond = ConditionBuilder.build_simple()
                if cond:
                    conditions.append(cond)
                else:
                    operators.pop()
            elif choice == "2":
                operators.append(LogicalOperator.OR)
                cond = ConditionBuilder.build_simple()
                if cond:
                    conditions.append(cond)
                else:
                    operators.pop()
            elif choice == "3":
                return CompoundCondition(conditions=conditions, operators=operators, negate=True)
        
        return CompoundCondition(conditions=conditions, operators=operators)


class ActionBuilder:
    """Interactive builder for set actions and other statements."""
    
    @staticmethod
    def build_set_action() -> Optional[SetAction]:
        """Build a set action interactively."""
        from .core import BackException
        
        console.print("\n[bold]Build Set Action:[/bold]")
        console.print("  Attributes:")
        for i, attr in enumerate(SetAttribute, 1):
            console.print(f"    [{i}] {attr.value}")
        console.print("  [B] Back")
        
        choices = [str(i) for i in range(1, len(SetAttribute) + 1)] + ["b", "B"]
        choice = Prompt.ask("Select attribute", choices=choices).lower()
        
        if choice == "b":
            raise BackException()
        
        attr = list(SetAttribute)[int(choice) - 1]
        
        # Handle special cases
        if attr == SetAttribute.COMMUNITY:
            console.print("\n  [1] Set (replace)")
            console.print("  [2] Add")
            console.print("  [3] Remove")
            op_choice = Prompt.ask("Operation", choices=["1", "2", "3"], default="1")
            
            if op_choice == "1":
                operation = SetOperation.SET
            elif op_choice == "2":
                operation = SetOperation.ADD
            else:
                operation = SetOperation.REMOVE
            
            value = Prompt.ask("Community value (e.g., 65000:100)")
            return SetAction(attribute=attr, value=value, operation=operation)
        
        elif attr == SetAttribute.AS_PATH:
            console.print("\n  [1] Prepend AS number")
            console.print("  [2] Prepend last-as (repeat N times)")
            console.print("  [3] Exclude AS")
            op_choice = Prompt.ask("Operation", choices=["1", "2", "3"], default="1")
            
            if op_choice == "1":
                value = Prompt.ask("AS number to prepend")
                return SetAction(attribute=attr, value=value, operation=SetOperation.PREPEND, extra="as-number")
            elif op_choice == "2":
                value = Prompt.ask("Number of times to repeat last AS (1-9)")
                return SetAction(attribute=attr, value=value, operation=SetOperation.PREPEND, extra="last-as")
            else:
                value = Prompt.ask("AS number to exclude")
                return SetAction(attribute=attr, value=value, operation=SetOperation.EXCLUDE)
        
        else:
            value = Prompt.ask(f"Value for {attr.value}")
            return SetAction(attribute=attr, value=value)


class RoutePolicyBuilder:
    """Interactive builder for creating route-policies."""
    
    def __init__(self, name: str = None):
        self.name = name
        self.parameters: List[str] = []
        self.statements: List[Union[IfBlock, SetAction, ReturnStatement, ExecPolicy]] = []
        self.description: Optional[str] = None
    
    def build_interactive(self) -> Optional[RoutePolicy]:
        """Build a route-policy interactively."""
        from .core import BackException, TopException
        
        # Policy name
        if not self.name:
            self.name = Prompt.ask("Policy name (e.g., MY_POLICY)")
            if not self.name:
                return None
        
        console.print(f"\n[bold]Building route-policy: {self.name}[/bold]")
        
        # Parameters
        if Confirm.ask("Add parameters ($param1, $param2, ...)?", default=False):
            params_str = Prompt.ask("Parameters (comma-separated, without $)")
            self.parameters = [p.strip() for p in params_str.split(",") if p.strip()]
        
        # Statements
        while True:
            console.print(f"\n[bold]Policy: {self.name}[/bold]")
            console.print(f"  Parameters: {', '.join(f'${p}' for p in self.parameters) or 'none'}")
            console.print(f"  Statements: {len(self.statements)}")
            
            console.print("\n  Add statement:")
            console.print("    [1] if block")
            console.print("    [2] set action")
            console.print("    [3] return statement")
            console.print("    [4] exec-policy (call another policy)")
            console.print("  ────────────────────────────────────────")
            console.print("    [V] View current policy")
            console.print("    [D] Done")
            console.print("    [B] Back")
            
            choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "v", "V", "d", "D", "b", "B"]).lower()
            
            if choice == "b":
                if self.statements:
                    self.statements.pop()
                else:
                    raise BackException()
            
            elif choice == "d":
                if not self.statements:
                    console.print("[yellow]Warning: Policy has no statements[/yellow]")
                    if not Confirm.ask("Create empty policy?", default=False):
                        continue
                break
            
            elif choice == "v":
                policy = RoutePolicy(
                    name=self.name,
                    parameters=self.parameters,
                    statements=self.statements,
                    description=self.description
                )
                console.print("\n[bold cyan]Preview:[/bold cyan]")
                console.print(Panel(policy.to_dnos(), title=f"route-policy {self.name}", border_style="cyan"))
            
            elif choice == "1":
                # if block
                if_block = self._build_if_block()
                if if_block:
                    self.statements.append(if_block)
            
            elif choice == "2":
                # set action
                action = ActionBuilder.build_set_action()
                if action:
                    self.statements.append(action)
            
            elif choice == "3":
                # return statement
                console.print("\n  [1] return allow")
                console.print("  [2] return deny")
                console.print("  [3] return (use previous set result)")
                ret_choice = Prompt.ask("Select", choices=["1", "2", "3"], default="1")
                
                if ret_choice == "1":
                    self.statements.append(ReturnStatement(ReturnAction.ALLOW))
                elif ret_choice == "2":
                    self.statements.append(ReturnStatement(ReturnAction.DENY))
                else:
                    self.statements.append(ReturnStatement(ReturnAction.NONE))
            
            elif choice == "4":
                # exec-policy
                exec_pol = self._build_exec_policy()
                if exec_pol:
                    self.statements.append(exec_pol)
        
        return RoutePolicy(
            name=self.name,
            parameters=self.parameters,
            statements=self.statements,
            description=self.description
        )
    
    def _build_if_block(self) -> Optional[IfBlock]:
        """Build an if block interactively."""
        from .core import BackException
        
        console.print("\n[bold]Build if block:[/bold]")
        
        # Condition
        try:
            condition = ConditionBuilder.build_compound()
            if not condition:
                return None
        except BackException:
            return None
        
        # Actions
        actions = []
        console.print("\n[bold]Add actions for 'if' block:[/bold]")
        while True:
            console.print(f"  Actions: {len(actions)}")
            console.print("    [1] set action")
            console.print("    [2] return statement")
            console.print("    [3] exec-policy")
            console.print("    [4] nested if block")
            console.print("    [D] Done with if block")
            console.print("    [B] Back (remove last action)")
            
            choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "d", "D", "b", "B"]).lower()
            
            if choice == "b":
                if actions:
                    actions.pop()
                else:
                    return None
            elif choice == "d":
                break
            elif choice == "1":
                action = ActionBuilder.build_set_action()
                if action:
                    actions.append(action)
            elif choice == "2":
                console.print("  [1] return allow  [2] return deny  [3] return")
                ret_choice = Prompt.ask("Select", choices=["1", "2", "3"], default="1")
                if ret_choice == "1":
                    actions.append(ReturnStatement(ReturnAction.ALLOW))
                elif ret_choice == "2":
                    actions.append(ReturnStatement(ReturnAction.DENY))
                else:
                    actions.append(ReturnStatement(ReturnAction.NONE))
            elif choice == "3":
                exec_pol = self._build_exec_policy()
                if exec_pol:
                    actions.append(exec_pol)
            elif choice == "4":
                nested = self._build_if_block()
                if nested:
                    actions.append(nested)
        
        # else-if blocks
        else_if_blocks = []
        while Confirm.ask("Add 'else if' block?", default=False):
            console.print("\n[bold]Build else-if condition:[/bold]")
            try:
                else_cond = ConditionBuilder.build_compound()
                if not else_cond:
                    continue
            except BackException:
                continue
            
            else_actions = []
            console.print("\n[bold]Add actions for 'else if' block:[/bold]")
            # Simplified action collection for else-if
            while True:
                console.print("    [1] set  [2] return  [D] Done")
                ch = Prompt.ask("Select", choices=["1", "2", "d", "D"]).lower()
                if ch == "d":
                    break
                elif ch == "1":
                    action = ActionBuilder.build_set_action()
                    if action:
                        else_actions.append(action)
                elif ch == "2":
                    ret = Prompt.ask("  [1] allow  [2] deny  [3] plain", choices=["1", "2", "3"], default="1")
                    if ret == "1":
                        else_actions.append(ReturnStatement(ReturnAction.ALLOW))
                    elif ret == "2":
                        else_actions.append(ReturnStatement(ReturnAction.DENY))
                    else:
                        else_actions.append(ReturnStatement(ReturnAction.NONE))
            
            else_if_blocks.append(IfBlock(condition=else_cond, actions=else_actions))
        
        # else block
        else_actions = []
        if Confirm.ask("Add 'else' block?", default=False):
            console.print("\n[bold]Add actions for 'else' block:[/bold]")
            while True:
                console.print("    [1] set  [2] return  [D] Done")
                ch = Prompt.ask("Select", choices=["1", "2", "d", "D"]).lower()
                if ch == "d":
                    break
                elif ch == "1":
                    action = ActionBuilder.build_set_action()
                    if action:
                        else_actions.append(action)
                elif ch == "2":
                    ret = Prompt.ask("  [1] allow  [2] deny  [3] plain", choices=["1", "2", "3"], default="1")
                    if ret == "1":
                        else_actions.append(ReturnStatement(ReturnAction.ALLOW))
                    elif ret == "2":
                        else_actions.append(ReturnStatement(ReturnAction.DENY))
                    else:
                        else_actions.append(ReturnStatement(ReturnAction.NONE))
        
        return IfBlock(
            condition=condition,
            actions=actions,
            else_if_blocks=else_if_blocks,
            else_actions=else_actions
        )
    
    def _build_exec_policy(self) -> Optional[ExecPolicy]:
        """Build an exec-policy call interactively."""
        policy_name = Prompt.ask("Policy name to call (use * for wildcard)")
        if not policy_name:
            return None
        
        params = []
        if Confirm.ask("Pass parameters?", default=False):
            params_str = Prompt.ask("Parameters (comma-separated, can use $param variables)")
            params = [p.strip() for p in params_str.split(",") if p.strip()]
        
        return ExecPolicy(policy_name=policy_name, parameters=params)


# =============================================================================
# TEMPLATE POLICIES
# =============================================================================

def create_template_deny_private(name: str = "DENY_PRIVATE") -> RoutePolicy:
    """Create a template policy that denies private prefixes (RFC1918)."""
    return RoutePolicy(
        name=name,
        parameters=[],
        statements=[
            IfBlock(
                condition=Condition(MatchAttribute.PREFIX_IPV4, Operator.EQ, "10.0.0.0/8"),
                actions=[ReturnStatement(ReturnAction.DENY)],
                else_if_blocks=[
                    IfBlock(
                        condition=Condition(MatchAttribute.PREFIX_IPV4, Operator.EQ, "172.16.0.0/12"),
                        actions=[ReturnStatement(ReturnAction.DENY)]
                    ),
                    IfBlock(
                        condition=Condition(MatchAttribute.PREFIX_IPV4, Operator.EQ, "192.168.0.0/16"),
                        actions=[ReturnStatement(ReturnAction.DENY)]
                    )
                ]
            ),
            ReturnStatement(ReturnAction.ALLOW)
        ],
        description="Deny RFC1918 private address space"
    )


def create_template_set_localpref(name: str = "SET_LOCALPREF", default_value: int = 200) -> RoutePolicy:
    """Create a template policy that sets local preference."""
    return RoutePolicy(
        name=name,
        parameters=["lpref_value"],
        statements=[
            SetAction(SetAttribute.LOCAL_PREFERENCE, "$lpref_value"),
            ReturnStatement(ReturnAction.ALLOW)
        ],
        description=f"Set local-preference (default: {default_value})"
    )


def create_template_med_filter(name: str = "MED_FILTER", threshold: int = 100) -> RoutePolicy:
    """Create a template policy that filters based on MED."""
    return RoutePolicy(
        name=name,
        parameters=[],
        statements=[
            IfBlock(
                condition=Condition(MatchAttribute.MED, Operator.GT, str(threshold)),
                actions=[
                    SetAction(SetAttribute.MED, str(threshold)),
                    ReturnStatement(ReturnAction.ALLOW)
                ],
                else_actions=[ReturnStatement(ReturnAction.ALLOW)]
            )
        ],
        description=f"Cap MED at {threshold}"
    )


def create_template_community_tag(name: str = "COMMUNITY_TAG") -> RoutePolicy:
    """Create a template policy that adds community tags."""
    return RoutePolicy(
        name=name,
        parameters=["community_value"],
        statements=[
            SetAction(SetAttribute.COMMUNITY, "$community_value", SetOperation.ADD),
            ReturnStatement(ReturnAction.ALLOW)
        ],
        description="Add community tag to routes"
    )


def get_available_templates() -> Dict[str, callable]:
    """Get dictionary of available template generators."""
    return {
        "DENY_PRIVATE": create_template_deny_private,
        "SET_LOCALPREF": create_template_set_localpref,
        "MED_FILTER": create_template_med_filter,
        "COMMUNITY_TAG": create_template_community_tag,
    }
