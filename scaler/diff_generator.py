"""Generate diff-style configuration previews showing additions with + prefix."""

from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


class DiffType(str, Enum):
    """Type of diff entry."""
    ADD = "+"
    REMOVE = "-"
    CONTEXT = " "
    HEADER = "@"


class DiffGenerator:
    """Generate diff-style configuration previews."""

    def __init__(self, context_lines: int = 2):
        """
        Initialize the diff generator.
        
        Args:
            context_lines: Number of context lines to show around changes
        """
        self.context_lines = context_lines

    def generate_add_diff(self, config_text: str, header: Optional[str] = None) -> str:
        """
        Generate a diff showing all lines as additions (+ prefix).
        
        Args:
            config_text: Configuration text to show as additions
            header: Optional header for the diff
        
        Returns:
            Diff-formatted string with + prefix on all lines
        """
        lines = config_text.split('\n')
        result = []
        
        if header:
            result.append(f"@@ {header} @@")
        
        for line in lines:
            if line.strip():  # Skip empty lines in output
                result.append(f"+ {line}")
            else:
                result.append("+")
        
        return '\n'.join(result)

    def generate_remove_diff(self, config_text: str, header: Optional[str] = None) -> str:
        """
        Generate a diff showing all lines as removals (- prefix).
        
        Args:
            config_text: Configuration text to show as removals
            header: Optional header for the diff
        
        Returns:
            Diff-formatted string with - prefix on all lines
        """
        lines = config_text.split('\n')
        result = []
        
        if header:
            result.append(f"@@ {header} @@")
        
        for line in lines:
            if line.strip():
                result.append(f"- {line}")
            else:
                result.append("-")
        
        return '\n'.join(result)

    def generate_unified_diff(
        self,
        old_config: str,
        new_config: str,
        old_label: str = "current",
        new_label: str = "new"
    ) -> str:
        """
        Generate a unified diff between two configurations.
        
        Args:
            old_config: Original configuration
            new_config: New/modified configuration
            old_label: Label for old config
            new_label: Label for new config
        
        Returns:
            Unified diff format string
        """
        import difflib
        
        old_lines = old_config.splitlines(keepends=True)
        new_lines = new_config.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=old_label,
            tofile=new_label,
            lineterm=''
        )
        
        return ''.join(diff)

    def generate_section_diff(
        self,
        sections: Dict[str, Tuple[str, str, str]]
    ) -> str:
        """
        Generate a diff for multiple configuration sections.
        
        Args:
            sections: Dict of section_name -> (action, old_config, new_config)
                     action is 'add', 'remove', 'replace', or 'keep'
        
        Returns:
            Combined diff string
        """
        result = []
        
        for section_name, (action, old_config, new_config) in sections.items():
            result.append(f"\n@@ {section_name} ({action}) @@")
            
            if action == 'add':
                if new_config:
                    for line in new_config.split('\n'):
                        if line.strip():
                            result.append(f"+ {line}")
            
            elif action == 'remove':
                if old_config:
                    for line in old_config.split('\n'):
                        if line.strip():
                            result.append(f"- {line}")
            
            elif action == 'replace':
                if old_config:
                    for line in old_config.split('\n'):
                        if line.strip():
                            result.append(f"- {line}")
                if new_config:
                    for line in new_config.split('\n'):
                        if line.strip():
                            result.append(f"+ {line}")
            
            elif action == 'keep':
                result.append("  (unchanged)")
        
        return '\n'.join(result)

    def format_config_preview(
        self,
        config_text: str,
        show_line_numbers: bool = False,
        max_lines: Optional[int] = None,
        highlight_pattern: Optional[str] = None
    ) -> str:
        """
        Format configuration text for preview display.
        
        Args:
            config_text: Configuration text
            show_line_numbers: Whether to show line numbers
            max_lines: Maximum lines to show (None for all)
            highlight_pattern: Regex pattern to highlight
        
        Returns:
            Formatted preview string
        """
        lines = config_text.split('\n')
        
        if max_lines and len(lines) > max_lines:
            lines = lines[:max_lines]
            lines.append(f"  ... ({len(config_text.split(chr(10))) - max_lines} more lines)")
        
        result = []
        for i, line in enumerate(lines, 1):
            if show_line_numbers:
                result.append(f"{i:4d} | {line}")
            else:
                result.append(line)
        
        return '\n'.join(result)

    def generate_hierarchy_preview(
        self,
        hierarchy_name: str,
        current_config: Optional[str],
        new_config: str,
        action: str
    ) -> str:
        """
        Generate a preview for a single hierarchy with action context.
        
        Args:
            hierarchy_name: Name of the hierarchy (e.g., 'interfaces')
            current_config: Current configuration (if any)
            new_config: New configuration to add/replace
            action: Action being taken ('add', 'replace', 'skip')
        
        Returns:
            Formatted preview string
        """
        lines = []
        
        # Header
        lines.append("=" * 70)
        lines.append(f" {hierarchy_name.upper()} - Action: {action.upper()}")
        lines.append("=" * 70)
        
        if action == 'skip':
            lines.append("  (keeping current configuration unchanged)")
            return '\n'.join(lines)
        
        if action == 'replace' and current_config:
            lines.append("")
            lines.append("Removing:")
            lines.append("-" * 40)
            for line in current_config.split('\n')[:10]:
                if line.strip():
                    lines.append(f"- {line}")
            if len(current_config.split('\n')) > 10:
                lines.append(f"  ... ({len(current_config.split(chr(10))) - 10} more lines)")
            lines.append("")
        
        lines.append("Adding:" if action == 'add' else "New configuration:")
        lines.append("-" * 40)
        
        new_lines = new_config.split('\n')
        for line in new_lines[:50]:
            if line.strip():
                lines.append(f"+ {line}")
        
        if len(new_lines) > 50:
            lines.append(f"  ... ({len(new_lines) - 50} more lines)")
        
        return '\n'.join(lines)

    def generate_summary_table(
        self,
        changes: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Generate a summary table of all changes.
        
        Args:
            changes: Dict of hierarchy -> {action, add_count, remove_count, scale_info, ...}
                     scale_info: Optional dict with 'count' and 'type' (e.g., {'count': 3100, 'type': 'ph sub-ifs'})
        
        Returns:
            Formatted summary table
        """
        lines = []
        lines.append("")
        
        # Check if any scale info is present
        has_scale = any('scale_info' in info for info in changes.values())
        
        if has_scale:
            # Extended table with Scale column
            # | Hierarchy (16) | Action (10) | Add (8) | Remove (8) | Lines (8) | Scale (25) |
            separator = "+" + "-" * 91 + "+"
            
            lines.append(separator)
            lines.append(f"| {'Hierarchy':<16} | {'Action':<10} | {'Add':>8} | {'Remove':>8} | {'Lines':>8} | {'Scale':<25} |")
            lines.append(separator)
            
            total_add = 0
            total_remove = 0
            
            for hierarchy, info in changes.items():
                action = info.get('action', 'skip')
                add_count = info.get('add_count', 0)
                remove_count = info.get('remove_count', 0)
                
                # Scale info
                scale_info = info.get('scale_info', {})
                if scale_info:
                    scale_count = scale_info.get('count', '')
                    scale_type = scale_info.get('type', '')
                    # If count is empty or 0, just show type; otherwise show "count type"
                    if scale_count:
                        scale_str = f"{scale_count} {scale_type}"[:25]
                    else:
                        scale_str = scale_type[:25] if scale_type else "-"
                else:
                    scale_str = "-"
                
                total_add += add_count
                total_remove += remove_count
                
                lines.append(
                    f"| {hierarchy:<16} | {action:<10} | {add_count:>8} | {remove_count:>8} | {add_count + remove_count:>8} | {scale_str:<25} |"
                )
            
            lines.append(separator)
            lines.append(
                f"| {'TOTAL':<16} | {'':<10} | {total_add:>8} | {total_remove:>8} | {total_add + total_remove:>8} | {'':<25} |"
            )
            lines.append(separator)
        else:
            # Standard table without Scale column
            separator = "+" + "-" * 72 + "+"
            
            lines.append(separator)
            lines.append(f"| {'Hierarchy':<20} | {'Action':<12} | {'Add':>8} | {'Remove':>8} | {'Total':>10} |")
            lines.append(separator)
            
            total_add = 0
            total_remove = 0
            
            for hierarchy, info in changes.items():
                action = info.get('action', 'skip')
                add_count = info.get('add_count', 0)
                remove_count = info.get('remove_count', 0)
                
                total_add += add_count
                total_remove += remove_count
                
                lines.append(
                    f"| {hierarchy:<20} | {action:<12} | {add_count:>8} | {remove_count:>8} | {add_count + remove_count:>10} |"
                )
            
            lines.append(separator)
            lines.append(
                f"| {'TOTAL':<20} | {'':<12} | {total_add:>8} | {total_remove:>8} | {total_add + total_remove:>10} |"
            )
            lines.append(separator)
        
        return '\n'.join(lines)

    def colorize_diff(self, diff_text: str, use_rich: bool = True) -> str:
        """
        Add Rich markup for colorized diff output.
        
        Args:
            diff_text: Diff text with +/- prefixes
            use_rich: Whether to use Rich markup
        
        Returns:
            Colorized diff text (with Rich markup if enabled)
        """
        if not use_rich:
            return diff_text
        
        lines = diff_text.split('\n')
        result = []
        
        for line in lines:
            if line.startswith('+ '):
                result.append(f"[green]{line}[/green]")
            elif line.startswith('- '):
                result.append(f"[red]{line}[/red]")
            elif line.startswith('@@ '):
                result.append(f"[cyan bold]{line}[/cyan bold]")
            elif line.startswith('='):
                result.append(f"[bold]{line}[/bold]")
            else:
                result.append(line)
        
        return '\n'.join(result)


def generate_config_diff(
    hierarchy: str,
    action: str,
    current: Optional[str],
    new: str
) -> str:
    """
    Convenience function to generate a diff for a hierarchy change.
    
    Args:
        hierarchy: Hierarchy name
        action: 'add', 'replace', or 'skip'
        current: Current config (for replace)
        new: New config
    
    Returns:
        Diff string
    """
    gen = DiffGenerator()
    return gen.generate_hierarchy_preview(hierarchy, current, new, action)


