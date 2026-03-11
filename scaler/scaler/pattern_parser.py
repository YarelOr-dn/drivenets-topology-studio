"""Parse interface patterns like ge400-0/0/{1-4}.{1-100} for scaled expansion."""

import re
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class InterfaceExpansion:
    """Result of pattern expansion."""
    parents: List[str]
    subinterfaces: List[str]
    total_count: int
    parent_count: int
    subif_count: int
    vlan_type: str  # 'single', 'qinq', or 'none'
    outer_vlans: List[int]
    inner_vlans: List[int]


class PatternParser:
    """Parse and expand interface patterns for scaling."""
    
    # Pattern to match range expressions like {1-100} or {1-10,20-30}
    RANGE_PATTERN = re.compile(r'\{([^}]+)\}')
    
    # Interface type patterns
    INTERFACE_PATTERNS = {
        'physical': re.compile(r'^(ge\d+)-(\d+)/(\d+)/(\d+)'),
        'bundle': re.compile(r'^bundle(\d+)'),
        'pwhe': re.compile(r'^ph(\d+)'),
        'irb': re.compile(r'^irb'),
        'loopback': re.compile(r'^lo(\d+)'),
    }

    def parse_range(self, range_expr: str) -> List[int]:
        """
        Parse a range expression like '1-100' or '1-10,20-30,50' into a list of integers.
        
        Args:
            range_expr: Range expression (e.g., '1-100', '1,3,5', '1-10,20-30')
        
        Returns:
            List of integers in the range
        """
        result = []
        parts = range_expr.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                # Handle range like '1-100'
                range_parts = part.split('-')
                if len(range_parts) == 2:
                    try:
                        start = int(range_parts[0].strip())
                        end = int(range_parts[1].strip())
                        result.extend(range(start, end + 1))
                    except ValueError:
                        raise ValueError(f"Invalid range expression: {part}")
            else:
                # Handle single value like '5'
                try:
                    result.append(int(part))
                except ValueError:
                    raise ValueError(f"Invalid number in range: {part}")
        
        return sorted(set(result))  # Remove duplicates and sort

    def expand_pattern(self, pattern: str) -> List[str]:
        """
        Expand a pattern with range expressions into a list of interface names.
        
        Args:
            pattern: Pattern like 'ge400-0/0/{1-4}' or 'ph{1-10}.{1-100}'
        
        Returns:
            List of expanded interface names
        """
        # Find all range expressions in the pattern
        ranges = self.RANGE_PATTERN.findall(pattern)
        
        if not ranges:
            # No ranges, return pattern as-is
            return [pattern]
        
        # Parse each range into a list of values
        range_values = [self.parse_range(r) for r in ranges]
        
        # Generate all combinations
        from itertools import product
        combinations = list(product(*range_values))
        
        # Replace range expressions with actual values
        results = []
        for combo in combinations:
            result = pattern
            for i, value in enumerate(combo):
                # Replace the i-th range expression with the value
                result = self.RANGE_PATTERN.sub(str(value), result, count=1)
            results.append(result)
        
        return results

    def parse_interface_pattern(
        self,
        pattern: str,
        vlan_type: str = 'single',
        outer_vlan_range: Optional[str] = None,
        inner_vlan_range: Optional[str] = None
    ) -> InterfaceExpansion:
        """
        Parse an interface pattern and return expansion details.
        
        Args:
            pattern: Interface pattern like 'ph{1-10}.{1-100}' or 'ge400-0/0/{1-4}'
            vlan_type: 'single' (vlan-id), 'qinq' (outer/inner), or 'none'
            outer_vlan_range: Override outer VLAN range (e.g., '100-109')
            inner_vlan_range: Override inner VLAN range for QinQ (e.g., '1-100')
        
        Returns:
            InterfaceExpansion with all details
        """
        # Check if pattern includes sub-interface notation (e.g., ph1.100)
        if '.' in pattern:
            # Split into parent pattern and subif pattern
            parts = pattern.split('.', 1)
            parent_pattern = parts[0]
            subif_pattern = parts[1] if len(parts) > 1 else None
            
            # Expand parent interfaces
            parents = self.expand_pattern(parent_pattern)
            
            # Expand sub-interface numbers
            if subif_pattern and self.RANGE_PATTERN.search(subif_pattern):
                subif_numbers = self.parse_range(
                    self.RANGE_PATTERN.search(subif_pattern).group(1)
                )
            elif subif_pattern:
                try:
                    subif_numbers = [int(subif_pattern)]
                except ValueError:
                    subif_numbers = []
            else:
                subif_numbers = []
            
            # Generate all sub-interfaces
            subinterfaces = []
            for parent in parents:
                for subif_num in subif_numbers:
                    subinterfaces.append(f"{parent}.{subif_num}")
            
            # Determine VLANs
            outer_vlans = []
            inner_vlans = []
            
            if outer_vlan_range:
                outer_vlans = self.parse_range(outer_vlan_range)
            elif subif_numbers:
                # Use sub-interface numbers as outer VLANs by default
                outer_vlans = subif_numbers
            
            if vlan_type == 'qinq' and inner_vlan_range:
                inner_vlans = self.parse_range(inner_vlan_range)
            
            return InterfaceExpansion(
                parents=parents,
                subinterfaces=subinterfaces,
                total_count=len(parents) + len(subinterfaces),
                parent_count=len(parents),
                subif_count=len(subinterfaces),
                vlan_type=vlan_type,
                outer_vlans=outer_vlans,
                inner_vlans=inner_vlans
            )
        else:
            # No sub-interfaces, just parent pattern
            parents = self.expand_pattern(pattern)
            
            return InterfaceExpansion(
                parents=parents,
                subinterfaces=[],
                total_count=len(parents),
                parent_count=len(parents),
                subif_count=0,
                vlan_type='none',
                outer_vlans=[],
                inner_vlans=[]
            )

    def detect_interface_type(self, interface_name: str) -> str:
        """
        Detect the type of interface from its name.
        
        Args:
            interface_name: Interface name like 'ge400-0/0/1', 'ph1', 'bundle5'
        
        Returns:
            Interface type: 'physical', 'bundle', 'pwhe', 'irb', 'loopback', or 'unknown'
        """
        # Remove sub-interface suffix if present
        base_name = interface_name.split('.')[0]
        
        for iface_type, regex in self.INTERFACE_PATTERNS.items():
            if regex.match(base_name):
                return iface_type
        
        return 'unknown'

    def validate_pattern(self, pattern: str) -> Tuple[bool, str]:
        """
        Validate an interface pattern.
        
        Args:
            pattern: Pattern to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try to find all range expressions
            ranges = self.RANGE_PATTERN.findall(pattern)
            
            # Validate each range
            for range_expr in ranges:
                values = self.parse_range(range_expr)
                if not values:
                    return False, f"Empty range expression: {{{range_expr}}}"
                
                # Check for negative numbers
                if any(v < 0 for v in values):
                    return False, f"Negative values not allowed: {{{range_expr}}}"
                
                # Check for VLAN range (if this looks like a sub-interface)
                if '.' in pattern and any(v > 4094 for v in values):
                    return False, f"VLAN ID exceeds 4094: {{{range_expr}}}"
            
            # Try a test expansion
            expanded = self.expand_pattern(pattern)
            if not expanded:
                return False, "Pattern produces no interfaces"
            
            # Check expansion doesn't produce too many (sanity check)
            if len(expanded) > 500000:
                return False, f"Pattern produces too many interfaces: {len(expanded)}"
            
            return True, ""
            
        except Exception as e:
            return False, str(e)

    def estimate_count(self, pattern: str) -> Dict[str, int]:
        """
        Estimate the number of interfaces a pattern will produce without full expansion.
        
        Args:
            pattern: Interface pattern
        
        Returns:
            Dict with 'parents', 'subinterfaces', 'total' counts
        """
        ranges = self.RANGE_PATTERN.findall(pattern)
        
        if not ranges:
            # Single interface
            return {'parents': 1, 'subinterfaces': 0, 'total': 1}
        
        # Calculate product of all range sizes
        range_sizes = []
        for range_expr in ranges:
            values = self.parse_range(range_expr)
            range_sizes.append(len(values))
        
        total = 1
        for size in range_sizes:
            total *= size
        
        if '.' in pattern:
            # Has sub-interfaces
            # First range is typically parent, rest are subifs
            parts = pattern.split('.', 1)
            parent_ranges = self.RANGE_PATTERN.findall(parts[0])
            subif_ranges = self.RANGE_PATTERN.findall(parts[1]) if len(parts) > 1 else []
            
            parent_count = 1
            for range_expr in parent_ranges:
                parent_count *= len(self.parse_range(range_expr))
            
            subif_per_parent = 1
            for range_expr in subif_ranges:
                subif_per_parent *= len(self.parse_range(range_expr))
            
            subif_count = parent_count * subif_per_parent
            
            return {
                'parents': parent_count,
                'subinterfaces': subif_count,
                'total': parent_count + subif_count
            }
        else:
            return {'parents': total, 'subinterfaces': 0, 'total': total}

    def generate_physical_pattern(
        self,
        interface_type: str,
        slot: int,
        bay: int,
        port_range: str
    ) -> str:
        """
        Generate a physical interface pattern.
        
        Args:
            interface_type: 'ge100' or 'ge400'
            slot: Slot number
            bay: Bay number
            port_range: Port range like '1-4' or '0-7'
        
        Returns:
            Pattern like 'ge400-0/0/{0-7}'
        """
        return f"{interface_type}-{slot}/{bay}/{{{port_range}}}"

    def generate_subif_pattern(
        self,
        parent_pattern: str,
        vlan_range: str
    ) -> str:
        """
        Generate a sub-interface pattern from a parent pattern.
        
        Args:
            parent_pattern: Parent pattern like 'ph{1-10}'
            vlan_range: VLAN range like '1-100'
        
        Returns:
            Pattern like 'ph{1-10}.{1-100}'
        """
        return f"{parent_pattern}.{{{vlan_range}}}"


def parse_count_input(user_input: str) -> Tuple[int, int, int]:
    """
    Parse a count-based input like '100 starting from 1' or '50-150'.
    
    Args:
        user_input: User input string
    
    Returns:
        Tuple of (count, start, step)
    """
    # Try to match "N starting from M" pattern
    match = re.match(r'(\d+)\s+(?:starting\s+)?(?:from\s+)?(\d+)?', user_input, re.I)
    if match:
        count = int(match.group(1))
        start = int(match.group(2)) if match.group(2) else 1
        return count, start, 1
    
    # Try to match "N-M" range pattern
    match = re.match(r'(\d+)\s*-\s*(\d+)', user_input)
    if match:
        start = int(match.group(1))
        end = int(match.group(2))
        return end - start + 1, start, 1
    
    # Try plain number
    try:
        count = int(user_input.strip())
        return count, 1, 1
    except ValueError:
        raise ValueError(f"Cannot parse count input: {user_input}")














