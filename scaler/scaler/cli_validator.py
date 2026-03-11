"""
DNOS CLI Validator - Validates configurations against official DNOS CLI documentation.

This module parses the DNOS CLI PDF documentation and uses it to:
1. Validate configuration syntax
2. Check for missing required knobs
3. Verify hierarchy structure
4. Validate interface attachments
5. Provide recommendations for common issues
"""

import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    import fitz  # PyMuPDF for PDF parsing
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

from .cli_rules_db import (
    DNOS_HIERARCHY_RULES, COMMON_MISTAKES, DNOS_LIMITS,
    get_hierarchy_spec, check_common_mistake, get_limit
)


class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single validation issue."""
    severity: ValidationSeverity
    line_number: Optional[int]
    message: str
    suggestion: Optional[str] = None
    hierarchy: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings: int = 0
    errors: int = 0
    
    def add_issue(self, issue: ValidationIssue):
        self.issues.append(issue)
        if issue.severity == ValidationSeverity.ERROR:
            self.errors += 1
            self.is_valid = False
        elif issue.severity == ValidationSeverity.WARNING:
            self.warnings += 1


@dataclass
class HierarchyRule:
    """Rule for a configuration hierarchy."""
    name: str
    parent: Optional[str]
    required_children: List[str] = field(default_factory=list)
    optional_children: List[str] = field(default_factory=list)
    valid_values: Optional[List[str]] = None
    value_pattern: Optional[str] = None
    requires: List[str] = field(default_factory=list)  # Other hierarchies that must exist
    description: str = ""


class CLIValidator:
    """Validates DNOS configurations against CLI documentation."""
    
    # Cache directory for parsed rules
    CACHE_DIR = Path(__file__).parent.parent / "docs" / ".cache"
    
    # Known DNOS hierarchies and their rules (built-in defaults)
    DEFAULT_RULES: Dict[str, HierarchyRule] = {}
    
    def __init__(self, pdf_path: Optional[str] = None):
        """Initialize the CLI validator.
        
        Args:
            pdf_path: Path to DNOS CLI PDF documentation
        """
        self.pdf_path = Path(pdf_path) if pdf_path else self._find_cli_pdf()
        self.rules: Dict[str, HierarchyRule] = {}
        self.raw_text: str = ""
        
        # Initialize with built-in rules
        self._load_builtin_rules()
        
        # Try to load from PDF if available
        if self.pdf_path and self.pdf_path.exists():
            self._load_from_pdf()
    
    def _find_cli_pdf(self) -> Optional[Path]:
        """Find the DNOS CLI PDF in known locations."""
        search_paths = [
            Path(__file__).parent.parent / "docs",
            Path.home() / "Downloads",
            Path("/home/dn/SCALER/docs"),
        ]
        
        for path in search_paths:
            if path.exists():
                for pdf in path.glob("*CLI*.pdf"):
                    return pdf
                for pdf in path.glob("*DNOS*.pdf"):
                    return pdf
        
        return None
    
    def _load_builtin_rules(self):
        """Load built-in validation rules from the rules database."""
        
        # Load all rules from the comprehensive rules database
        for path, spec in DNOS_HIERARCHY_RULES.items():
            self.rules[path] = HierarchyRule(
                name=spec.path.split('.')[-1],
                parent=spec.parent,
                required_children=spec.required_children,
                optional_children=spec.optional_children,
                valid_values=spec.value_choices,
                value_pattern=spec.value_pattern,
                requires=spec.requires_peers,
                description=spec.description
            )
        
        # Keep limits for validation
        self.limits = DNOS_LIMITS
    
    def _load_from_pdf(self):
        """Load additional rules from DNOS CLI PDF."""
        if not HAS_PYMUPDF:
            return
        
        # Check cache first
        cache_file = self._get_cache_path()
        if cache_file and cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    # Add any cached rules
                    for name, rule_data in cached_data.get('rules', {}).items():
                        if name not in self.rules:
                            self.rules[name] = HierarchyRule(**rule_data)
                return
            except:
                pass
        
        # Parse PDF
        try:
            doc = fitz.open(str(self.pdf_path))
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            self.raw_text = "\n".join(text_parts)
            doc.close()
            
            # Parse CLI syntax from text
            self._parse_cli_syntax()
            
            # Cache the results
            self._save_cache()
        except Exception as e:
            print(f"Warning: Could not parse PDF: {e}")
    
    def _get_cache_path(self) -> Optional[Path]:
        """Get cache file path based on PDF hash."""
        if not self.pdf_path or not self.pdf_path.exists():
            return None
        
        # Create hash of PDF
        with open(self.pdf_path, 'rb') as f:
            pdf_hash = hashlib.md5(f.read()).hexdigest()[:12]
        
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        return self.CACHE_DIR / f"cli_rules_{pdf_hash}.json"
    
    def _parse_cli_syntax(self):
        """Parse CLI syntax from PDF text."""
        # Extract interface attributes and valid values
        self._extract_interface_attributes()
        
        # Extract protocol commands
        self._extract_protocol_commands()
        
        # Extract network service commands
        self._extract_service_commands()
        
        # Extract valid values for specific parameters
        self._extract_valid_values()
    
    def _extract_interface_attributes(self):
        """Extract interface attribute rules from PDF."""
        # Look for attribute tables with Description/Range/Default columns
        attr_pattern = re.compile(
            r'(admin-state|mtu|ipv4-address|ipv6-address|vlan-id|vlan-tags|'
            r'description|mpls|bundle-id|arp|ndp|access-list)\s+'
            r'([^\n]+?)\s+(\d+\.\.\d+|\w+/\w+|Enabled\s+Disabled|Free text|[^\n]+)',
            re.IGNORECASE
        )
        
        for match in attr_pattern.finditer(self.raw_text):
            attr_name = match.group(1).lower()
            description = match.group(2).strip()
            range_or_values = match.group(3).strip()
            
            # Update or create rule
            if attr_name not in self.rules:
                self.rules[f"interfaces.{attr_name}"] = HierarchyRule(
                    name=attr_name,
                    parent="interfaces.*",
                    description=description[:100]
                )
            
            # Parse ranges
            range_match = re.match(r'(\d+)\.\.(\d+)', range_or_values)
            if range_match:
                # Store range info in description
                self.rules[f"interfaces.{attr_name}"].description = (
                    f"{description} (range: {range_match.group(1)}-{range_match.group(2)})"
                )
    
    def _extract_protocol_commands(self):
        """Extract protocol command rules from PDF."""
        # Look for protocol configuration patterns
        proto_patterns = [
            (r'configure protocols bgp', 'protocols.bgp'),
            (r'configure protocols isis', 'protocols.isis'),
            (r'configure protocols ospf', 'protocols.ospf'),
            (r'configure protocols ldp', 'protocols.ldp'),
        ]
        
        for pattern, rule_key in proto_patterns:
            if re.search(pattern, self.raw_text, re.IGNORECASE):
                # Mark as found in PDF
                if rule_key in self.rules:
                    self.rules[rule_key].description += " [from PDF]"
    
    def _extract_service_commands(self):
        """Extract network service commands from PDF."""
        service_patterns = [
            (r'evpn-vpws-fxc', 'network-services.evpn-vpws-fxc'),
            (r'evpn-vpls', 'network-services.evpn-vpls'),
            (r'l3vpn', 'network-services.l3vpn'),
        ]
        
        for pattern, rule_key in service_patterns:
            if re.search(pattern, self.raw_text, re.IGNORECASE):
                if rule_key in self.rules:
                    self.rules[rule_key].description += " [from PDF]"
    
    def _extract_valid_values(self):
        """Extract valid values for parameters from PDF."""
        # Look for value enumerations
        value_patterns = [
            # admin-state values
            (r'admin-state\s+.*?(Enabled|Disabled)', ['enabled', 'disabled'], 'interfaces.admin-state'),
            # network-type values  
            (r'network-type\s+.*?(broadcast|point-to-point|point-to-multipoint|nbma)', 
             ['broadcast', 'point-to-point', 'point-to-multipoint', 'nbma'],
             'ospf.interface.network-type'),
            # ISIS level values (syntax: 'level level-2')
            (r'level\s+(level-1|level-2|level-1-2)',
             ['level-1', 'level-2', 'level-1-2'],
             'isis.instance.level'),
            # transport-protocol values for FXC (MPLS or SRv6, not VXLAN)
            (r'transport-protocol\s+.*?(mpls|srv6)',
             ['mpls', 'srv6'],
             'fxc.instance.transport-protocol'),
        ]
        
        for pattern, values, rule_key in value_patterns:
            if re.search(pattern, self.raw_text, re.IGNORECASE):
                if rule_key in self.rules:
                    self.rules[rule_key].valid_values = values
    
    def _save_cache(self):
        """Save parsed rules to cache."""
        cache_file = self._get_cache_path()
        if not cache_file:
            return
        
        try:
            cache_data = {
                'rules': {
                    name: {
                        'name': rule.name,
                        'parent': rule.parent,
                        'required_children': rule.required_children,
                        'optional_children': rule.optional_children,
                        'valid_values': rule.valid_values,
                        'value_pattern': rule.value_pattern,
                        'requires': rule.requires,
                        'description': rule.description
                    }
                    for name, rule in self.rules.items()
                }
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except:
            pass
    
    def validate_config(self, config_text: str) -> ValidationResult:
        """Validate a configuration against DNOS CLI rules.
        
        Args:
            config_text: Configuration text to validate
            
        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult(is_valid=True)
        lines = config_text.split('\n')
        
        # Track current hierarchy path
        hierarchy_stack = []
        current_indent = 0
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.rstrip()
            if not stripped or stripped == '!':
                if stripped == '!':
                    if hierarchy_stack:
                        hierarchy_stack.pop()
                continue
            
            # Calculate indentation
            indent = len(line) - len(line.lstrip())
            
            # Adjust hierarchy stack based on indent
            while hierarchy_stack and indent <= current_indent:
                hierarchy_stack.pop()
                current_indent = max(0, current_indent - 2)
            
            # Parse the line
            parts = stripped.split(None, 1)
            keyword = parts[0] if parts else ""
            value = parts[1] if len(parts) > 1 else ""
            
            # Build current path
            current_path = '.'.join(hierarchy_stack + [keyword])
            
            # Validate against rules
            self._validate_line(result, line_num, keyword, value, hierarchy_stack, current_path)
            
            # Update stack for next iteration
            if not stripped.endswith('!'):
                hierarchy_stack.append(keyword)
                current_indent = indent
        
        # Check for missing required elements
        self._check_required_elements(result, config_text)
        
        return result
    
    def _validate_line(
        self,
        result: ValidationResult,
        line_num: int,
        keyword: str,
        value: str,
        hierarchy: List[str],
        path: str
    ):
        """Validate a single configuration line."""
        
        # Check for common syntax errors
        
        # 1. Check for brace-style syntax (wrong)
        if '{' in value or '}' in value:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                line_number=line_num,
                message=f"Invalid syntax: braces '{{}}' not allowed in DNOS CLI",
                suggestion="Use indentation with '!' terminators instead",
                hierarchy=path
            ))
        
        # 2. Check for valid values if rule exists
        rule_key = None
        for key in [path, keyword, f"{hierarchy[-1]}.{keyword}" if hierarchy else keyword]:
            if key in self.rules:
                rule_key = key
                break
        
        if rule_key and self.rules[rule_key].valid_values:
            if value and value not in self.rules[rule_key].valid_values:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    line_number=line_num,
                    message=f"Unknown value '{value}' for {keyword}",
                    suggestion=f"Valid values: {', '.join(self.rules[rule_key].valid_values)}",
                    hierarchy=path
                ))
        
        # 3. Check value pattern if defined
        if rule_key and self.rules[rule_key].value_pattern:
            pattern = self.rules[rule_key].value_pattern
            if value and not re.match(pattern, value):
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    line_number=line_num,
                    message=f"Value '{value}' doesn't match expected pattern for {keyword}",
                    hierarchy=path
                ))
        
        # 4. Check common mistakes using the rules database
        mistake_correction = check_common_mistake(keyword)
        if mistake_correction:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                line_number=line_num,
                message=f"Possible incorrect syntax: '{keyword}'",
                suggestion=mistake_correction,
                hierarchy=path
            ))
        
        # 4b. Context-specific checks
        # Check for 'net' instead of 'iso-network' only in ISIS context
        if keyword == "net" and hierarchy and "isis" in hierarchy:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                line_number=line_num,
                message="Use 'iso-network' instead of 'net' for ISIS NET address",
                suggestion="Replace 'net' with 'iso-network'",
                hierarchy=path
            ))
        
        # 5. Check for standalone 'enabled'/'disabled' keywords
        if keyword == "enabled" and hierarchy:
            parent = hierarchy[-1] if hierarchy else ""
            if parent not in ["admin-state", "mpls", "segment-routing"]:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    line_number=line_num,
                    message="Consider using 'admin-state enabled' for clarity",
                    suggestion="Wrap in 'admin-state' hierarchy",
                    hierarchy=path
                ))
        
        # 6. Check for unknown top-level hierarchies
        if not hierarchy:  # Top level
            known_top_level = ["interfaces", "protocols", "network-services", 
                             "system", "class-of-service", "policy", "acl",
                             "routing-instances", "firewall", "routing-options"]
            if keyword not in known_top_level:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    line_number=line_num,
                    message=f"Unknown top-level hierarchy: '{keyword}'",
                    suggestion=f"Valid top-level: {', '.join(known_top_level)}",
                    hierarchy=keyword
                ))
        
        # 7. Check loopback IP prefix - must be /32
        if keyword == "ipv4-address" and hierarchy and "lo0" in hierarchy:
            # Check if the IP has a non-/32 prefix
            ip_match = re.match(r'(\d+\.\d+\.\d+\.\d+)/(\d+)', value)
            if ip_match:
                prefix = ip_match.group(2)
                if prefix != '32':
                    result.add_issue(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        line_number=line_num,
                        message=f"Loopback IP should use /32, not /{prefix}",
                        suggestion=f"Change to: ipv4-address {ip_match.group(1)}/32",
                        hierarchy=path
                    ))
    
    def _check_required_elements(self, result: ValidationResult, config_text: str):
        """Check for missing required configuration elements."""
        
        # Check for FXC services without interfaces
        if "evpn-vpws-fxc" in config_text and "instance" in config_text:
            if "interface" not in config_text:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    line_number=None,
                    message="FXC instances defined but no interfaces attached",
                    suggestion="Add 'interface <name>' to each FXC instance",
                    hierarchy="network-services.evpn-vpws-fxc"
                ))
        
        # Check for BGP neighbors without address families
        neighbor_count = config_text.count("neighbor ")
        af_count = config_text.count("address-family ")
        if neighbor_count > 0 and af_count < neighbor_count:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                line_number=None,
                message="Some BGP neighbors may be missing address-family configuration",
                suggestion="Add at least one address-family (e.g., l2vpn-evpn) per neighbor",
                hierarchy="protocols.bgp"
            ))
        
        # Check ISIS without interfaces
        if "isis" in config_text and "instance" in config_text:
            if config_text.count("interface ") < 1:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    line_number=None,
                    message="ISIS instance has no interfaces configured",
                    suggestion="Add at least one interface to the ISIS instance",
                    hierarchy="protocols.isis"
                ))
        
        # Check loopback prefix - must be /32
        # Find all loopback IP addresses and check their prefix
        lo0_pattern = re.compile(
            r'^\s*lo\d+\s*$.*?ipv4-address\s+(\d+\.\d+\.\d+\.\d+)/(\d+)',
            re.MULTILINE | re.DOTALL
        )
        for match in lo0_pattern.finditer(config_text):
            prefix = match.group(2)
            if prefix != '32':
                ip = match.group(1)
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    line_number=None,
                    message=f"Loopback IP {ip}/{prefix} should use /32",
                    suggestion=f"Loopbacks are host routes and must use /32 prefix",
                    hierarchy="interfaces.lo0"
                ))
    
    def get_hierarchy_help(self, hierarchy: str) -> Optional[str]:
        """Get help text for a hierarchy path.
        
        Args:
            hierarchy: Dot-separated hierarchy path (e.g., 'protocols.bgp.neighbor')
            
        Returns:
            Help text from documentation
        """
        if hierarchy in self.rules:
            rule = self.rules[hierarchy]
            help_lines = [f"**{rule.name}**"]
            if rule.description:
                help_lines.append(f"  {rule.description}")
            if rule.required_children:
                help_lines.append(f"  Required: {', '.join(rule.required_children)}")
            if rule.optional_children:
                help_lines.append(f"  Optional: {', '.join(rule.optional_children)}")
            if rule.valid_values:
                help_lines.append(f"  Values: {', '.join(rule.valid_values)}")
            return '\n'.join(help_lines)
        return None
    
    def suggest_completion(self, partial_config: str) -> List[str]:
        """Suggest possible completions for partial configuration.
        
        Args:
            partial_config: Partial configuration text
            
        Returns:
            List of suggested completions
        """
        suggestions = []
        
        # Parse current context
        lines = partial_config.strip().split('\n')
        if not lines:
            return ["interfaces", "protocols", "network-services", "system"]
        
        last_line = lines[-1].strip()
        
        # Determine current hierarchy
        hierarchy = []
        for line in lines:
            stripped = line.strip()
            if stripped == '!':
                if hierarchy:
                    hierarchy.pop()
            elif stripped:
                keyword = stripped.split()[0]
                if not stripped.endswith('!'):
                    hierarchy.append(keyword)
        
        current_path = '.'.join(hierarchy)
        
        # Find matching rules
        for rule_name, rule in self.rules.items():
            if rule.parent and current_path.endswith(rule.parent):
                suggestions.append(rule.name)
            elif not rule.parent and not hierarchy:
                suggestions.append(rule.name)
        
        # Add common children based on context
        if "bgp" in current_path:
            suggestions.extend(["neighbor", "router-id", "address-family"])
        elif "isis" in current_path:
            suggestions.extend(["interface", "iso-network", "address-family"])
        elif "interfaces" in current_path or current_path.startswith("interfaces"):
            suggestions.extend(["admin-state enabled", "description", "vlan-tags", "vlan-id"])
        
        return list(set(suggestions))


    def validate_interface_order(
        self, 
        config_text: str,
        auto_fix: bool = False
    ) -> Tuple[List[ValidationIssue], Optional[str]]:
        """Validate that interfaces are in correct order (parent before sub-interfaces).
        
        DNOS requires each parent interface to be immediately followed by all 
        its sub-interfaces before the next parent appears.
        
        Correct order:
          ph1 -> ph1.1 -> ph1.2 -> ph2 -> ph2.1 -> ph2.2
          
        Incorrect order:
          ph1 -> ph2 -> ph1.1 -> ph2.1 (parents separate from sub-ifs)
        
        Args:
            config_text: Configuration text to validate
            auto_fix: If True, return reordered config in second tuple element
            
        Returns:
            Tuple of (list of issues, optionally reordered config if auto_fix=True)
        """
        issues = []
        
        # Parse interface section
        lines = config_text.split('\n')
        in_interfaces = False
        interface_entries = []  # List of (name, start_line, end_line, content_lines)
        current_iface = None
        current_start = None
        current_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Detect interfaces block
            if stripped == "interfaces":
                in_interfaces = True
                continue
            
            # End of interfaces block (unindented or different hierarchy)
            if in_interfaces and stripped and not line.startswith(' ') and stripped != '!':
                in_interfaces = False
            
            if not in_interfaces:
                continue
            
            # Look for interface names (2-space indent)
            if line.startswith('  ') and not line.startswith('    '):
                # Check if this is an interface name (not a terminator)
                if stripped and stripped != '!':
                    # Save previous interface
                    if current_iface is not None:
                        interface_entries.append((current_iface, current_start, i - 1, current_lines))
                    
                    current_iface = stripped
                    current_start = i
                    current_lines = [line]
                elif stripped == '!' and current_iface is not None:
                    # Terminator for current interface
                    current_lines.append(line)
                    interface_entries.append((current_iface, current_start, i, current_lines))
                    current_iface = None
                    current_start = None
                    current_lines = []
            elif current_iface is not None:
                # Part of current interface block
                current_lines.append(line)
        
        # Save last interface if any
        if current_iface is not None:
            interface_entries.append((current_iface, current_start, len(lines) - 1, current_lines))
        
        # Check ordering: each sub-interface should appear after its parent
        # and before any other parent
        seen_parents = {}  # parent_name -> index
        seen_subifs_for_parent = {}  # parent_name -> list of subif indices
        
        for idx, (iface_name, start_line, end_line, _) in enumerate(interface_entries):
            if '.' in iface_name:
                # Sub-interface
                parent_name = iface_name.split('.')[0]
                
                # Check if parent exists
                if parent_name not in seen_parents:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        line_number=start_line + 1,
                        message=f"Sub-interface '{iface_name}' appears before its parent '{parent_name}'",
                        suggestion=f"Move '{parent_name}' before '{iface_name}'",
                        hierarchy="interfaces"
                    ))
                else:
                    parent_idx = seen_parents[parent_name]
                    
                    # Check if another parent appeared between this parent and sub-if
                    for other_parent, other_idx in seen_parents.items():
                        if other_parent != parent_name and other_idx > parent_idx and other_idx < idx:
                            issues.append(ValidationIssue(
                                severity=ValidationSeverity.WARNING,
                                line_number=start_line + 1,
                                message=f"Sub-interface '{iface_name}' is not grouped with parent '{parent_name}'",
                                suggestion=f"Move '{iface_name}' immediately after '{parent_name}' and its other sub-interfaces",
                                hierarchy="interfaces"
                            ))
                            break
                    
                    # Track this sub-interface
                    if parent_name not in seen_subifs_for_parent:
                        seen_subifs_for_parent[parent_name] = []
                    seen_subifs_for_parent[parent_name].append(idx)
            else:
                # Parent interface
                seen_parents[iface_name] = idx
        
        # Auto-fix: reorder if requested
        reordered_config = None
        if auto_fix and issues:
            reordered_config = self._reorder_interfaces(config_text, interface_entries)
        
        return issues, reordered_config
    
    def _reorder_interfaces(
        self, 
        config_text: str, 
        interface_entries: List[Tuple[str, int, int, List[str]]]
    ) -> str:
        """Reorder interfaces so each parent is followed by its sub-interfaces.
        
        Args:
            config_text: Original configuration
            interface_entries: Parsed interface entries
            
        Returns:
            Reordered configuration text
        """
        from collections import OrderedDict
        
        # Group interfaces by parent
        groups = OrderedDict()  # parent -> [(name, lines), ...]
        standalone = []  # Interfaces without sub-interfaces or that are not sub-interfaces
        
        for iface_name, start_line, end_line, content_lines in interface_entries:
            if '.' in iface_name:
                parent = iface_name.split('.')[0]
                if parent not in groups:
                    groups[parent] = []
                groups[parent].append((iface_name, content_lines))
            else:
                # Parent or standalone interface
                if iface_name not in groups:
                    groups[iface_name] = []
                # Insert parent at the beginning of its group
                groups[iface_name].insert(0, (iface_name, content_lines))
        
        # Build reordered interface section
        lines = config_text.split('\n')
        
        # Find interfaces section boundaries
        iface_start = None
        iface_end = None
        for i, line in enumerate(lines):
            if line.strip() == "interfaces":
                iface_start = i
            elif iface_start is not None and line.strip() and not line.startswith(' ') and line.strip() != '!':
                iface_end = i
                break
        
        if iface_start is None:
            return config_text
        
        if iface_end is None:
            # Find the closing '!' at column 0
            for i in range(iface_start + 1, len(lines)):
                if lines[i] == '!':
                    iface_end = i + 1
                    break
            if iface_end is None:
                iface_end = len(lines)
        
        # Build new interface section
        new_iface_lines = ["interfaces"]
        for parent, entries in groups.items():
            for iface_name, content_lines in entries:
                new_iface_lines.extend(content_lines)
        new_iface_lines.append("!")
        
        # Reconstruct full config
        result_lines = lines[:iface_start] + new_iface_lines + lines[iface_end:]
        return '\n'.join(result_lines)

    def validate_scale_limits(self, config_text: str) -> List[ValidationIssue]:
        """Validate configuration against DNOS scale limits.
        
        Args:
            config_text: Configuration text to check
            
        Returns:
            List of limit violation issues
        """
        issues = []
        
        # Count resources
        counts = {
            "physical_interfaces": 0,
            "bundle_interfaces": 0,
            "bundle_subinterfaces": 0,
            "pwhe_interfaces": 0,
            "irb_interfaces": 0,
            "loopback_interfaces": 0,
            "fxc_instances": 0,
            "evpn_vpls_instances": 0,
            "l3vpn_instances": 0,
            "bgp_peers": 0,
        }
        
        lines = config_text.split('\n')
        for line in lines:
            stripped = line.strip()
            
            # Count interfaces by type
            # DNOS physical interfaces: ge100-X/Y/Z, ge400-X/Y/Z, hundredGigE, tenGigE
            # Sub-interfaces have .N suffix (e.g., ge400-0/0/4.12) - do NOT count as physical
            if re.match(r'(ge\d+-|ge100-|ge400-|hundredGigE|tenGigE)', stripped):
                if '.' in stripped:
                    counts["bundle_subinterfaces"] += 1  # Physical sub-interface
                else:
                    counts["physical_interfaces"] += 1  # True physical interface (no .N)
            elif stripped.startswith('bundle'):
                if '.' in stripped:
                    counts["bundle_subinterfaces"] += 1
                else:
                    counts["bundle_interfaces"] += 1
            elif stripped.startswith('ph'):
                # PWHE interfaces - ph1, ph1.1, etc.
                if '.' in stripped:
                    counts["bundle_subinterfaces"] += 1  # PWHE sub-interface
                else:
                    counts["pwhe_interfaces"] += 1  # PWHE parent only
            elif stripped.startswith('irb'):
                counts["irb_interfaces"] += 1
            elif stripped.startswith('lo'):
                counts["loopback_interfaces"] += 1
            
            # Count services
            if 'evpn-vpws-fxc' in stripped and 'instance' in stripped:
                counts["fxc_instances"] += 1
            elif 'evpn-vpls' in stripped and 'instance' in stripped:
                counts["evpn_vpls_instances"] += 1
            elif 'l3vpn' in stripped and 'instance' in stripped:
                counts["l3vpn_instances"] += 1
            
            # Count BGP peers
            if 'neighbor' in stripped and re.search(r'\d+\.\d+\.\d+\.\d+', stripped):
                counts["bgp_peers"] += 1
        
        # Check against limits
        for resource, count in counts.items():
            limit_key = f"max_{resource}"
            limit = get_limit(limit_key)
            if limit and count > limit:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    line_number=None,
                    message=f"Limit exceeded: {count} {resource.replace('_', ' ')} (max: {limit})",
                    suggestion=f"Reduce the number of {resource.replace('_', ' ')} to {limit} or less",
                    hierarchy=None
                ))
            elif limit and count > limit * 0.9:  # Warn at 90%
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    line_number=None,
                    message=f"Approaching limit: {count}/{limit} {resource.replace('_', ' ')} (90%+)",
                    hierarchy=None
                ))
        
        return issues


def validate_generated_config(
    config_text: str, 
    check_limits: bool = True,
    check_interface_order: bool = True
) -> ValidationResult:
    """Convenience function to validate generated configuration.
    
    Args:
        config_text: Configuration text to validate
        check_limits: Whether to also check scale limits
        check_interface_order: Whether to check interface ordering
        
    Returns:
        ValidationResult with any issues
    """
    validator = CLIValidator()
    result = validator.validate_config(config_text)
    
    if check_limits:
        limit_issues = validator.validate_scale_limits(config_text)
        for issue in limit_issues:
            result.add_issue(issue)
    
    if check_interface_order:
        order_issues, _ = validator.validate_interface_order(config_text, auto_fix=False)
        for issue in order_issues:
            result.add_issue(issue)
    
    return result


def validate_and_fix_interface_order(config_text: str) -> Tuple[bool, str, List[ValidationIssue]]:
    """Validate and optionally fix interface ordering.
    
    Args:
        config_text: Configuration to validate
        
    Returns:
        Tuple of (had_issues, fixed_config, list_of_issues)
    """
    validator = CLIValidator()
    issues, fixed_config = validator.validate_interface_order(config_text, auto_fix=True)
    
    had_issues = len(issues) > 0
    result_config = fixed_config if fixed_config else config_text
    
    return had_issues, result_config, issues


def manage_cli_pdf():
    """Interactive CLI to manage DNOS CLI PDF documentation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage DNOS CLI PDF documentation")
    parser.add_argument('action', choices=['status', 'path', 'validate', 'search'],
                       help='Action to perform')
    parser.add_argument('--pdf', '-p', help='Path to PDF file')
    parser.add_argument('--query', '-q', help='Search query for PDF content')
    parser.add_argument('--config', '-c', help='Config file to validate')
    
    args = parser.parse_args()
    
    validator = CLIValidator(pdf_path=args.pdf)
    
    if args.action == 'status':
        if validator.pdf_path and validator.pdf_path.exists():
            print(f"✓ PDF found: {validator.pdf_path}")
            print(f"  Loaded {len(validator.rules)} validation rules")
            if HAS_PYMUPDF:
                print("  PyMuPDF is available for PDF parsing")
            else:
                print("  ⚠ PyMuPDF not installed - using built-in rules only")
        else:
            print("✗ No DNOS CLI PDF found")
            print("\nTo add the PDF:")
            print("  1. Download the DNOS CLI PDF from DriveNets documentation")
            print("  2. Copy it to: /home/dn/SCALER/docs/")
            print("  3. Or specify path: scaler-validate --pdf /path/to/DNOS_CLI.pdf")
    
    elif args.action == 'path':
        print(validator.pdf_path or "Not set")
    
    elif args.action == 'validate':
        if not args.config:
            print("Error: --config required for validate action")
            return 1
        
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Error: Config file not found: {args.config}")
            return 1
        
        with open(config_path) as f:
            config_text = f.read()
        
        result = validate_generated_config(config_text)
        
        if result.is_valid:
            print(f"✓ Configuration is valid ({len(result.issues)} warnings)")
        else:
            print(f"✗ Configuration has {result.errors} error(s), {result.warnings} warning(s)")
        
        for issue in result.issues:
            prefix = {"error": "✗", "warning": "⚠", "info": "ℹ"}.get(issue.severity.value, "•")
            line = f" [line {issue.line_number}]" if issue.line_number else ""
            print(f"  {prefix}{line} {issue.message}")
            if issue.suggestion:
                print(f"      → {issue.suggestion}")
    
    elif args.action == 'search':
        if not args.query:
            print("Error: --query required for search action")
            return 1
        
        if not validator.raw_text:
            print("Error: PDF not loaded or not readable")
            return 1
        
        # Search in PDF content
        query = args.query.lower()
        matches = []
        for i, line in enumerate(validator.raw_text.split('\n')):
            if query in line.lower():
                matches.append((i, line.strip()))
        
        print(f"Found {len(matches)} matches for '{args.query}':")
        for line_num, text in matches[:20]:
            print(f"  [{line_num}] {text[:100]}...")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(manage_cli_pdf())

