"""
Core Navigation and Exception Classes for the SCALER Wizard.

This module contains:
- BackException: Signal to go back one step
- TopException: Signal to restart entire wizard
- StepNavigator: Helper class for step-based navigation
- Breadcrumb/path functions for navigation display
"""

from typing import Any, List, Optional

from rich.console import Console
from rich.prompt import Prompt

# Local console for this module
console = Console()


def int_prompt_nav(prompt_text: str, default: int = None, min_val: int = None, max_val: int = None) -> int:
    """Integer prompt with Back/Top navigation support.
    
    Drop-in replacement for IntPrompt.ask() that supports 'b' for back and 't' for top.
    
    Args:
        prompt_text: The prompt message
        default: Default integer value
        min_val: Minimum allowed value (optional)
        max_val: Maximum allowed value (optional)
        
    Returns:
        Integer value entered by user
        
    Raises:
        BackException: When user enters 'b' or 'B'
        TopException: When user enters 't' or 'T'
    """
    while True:
        # Build prompt with default
        default_str = f" ({default})" if default is not None else ""
        full_prompt = f"{prompt_text}{default_str}"
        
        result = Prompt.ask(full_prompt, default=str(default) if default is not None else None)
        
        # Check for navigation
        if result.strip().lower() == 'b':
            raise BackException()
        if result.strip().lower() == 't':
            raise TopException()
        
        # Try to parse as integer
        try:
            value = int(result)
            
            # Validate range if specified
            if min_val is not None and value < min_val:
                console.print(f"[red]Value must be at least {min_val}[/red]")
                continue
            if max_val is not None and value > max_val:
                console.print(f"[red]Value must be at most {max_val}[/red]")
                continue
            
            return value
        except ValueError:
            console.print("[red]Please enter a valid integer (or 'b' to go back)[/red]")
            continue


def str_prompt_nav(prompt_text: str, default: str = None, allow_empty: bool = False) -> str:
    """String prompt with Back/Top navigation support.
    
    Drop-in replacement for Prompt.ask() that supports 'b' for back and 't' for top.
    
    Args:
        prompt_text: The prompt message
        default: Default string value
        allow_empty: Whether to allow empty input
        
    Returns:
        String value entered by user
        
    Raises:
        BackException: When user enters 'b' or 'B' (only if no other content)
        TopException: When user enters 't' or 'T' (only if no other content)
    """
    while True:
        result = Prompt.ask(prompt_text, default=default if default is not None else None)
        
        # Check for navigation (only when input is exactly 'b' or 't')
        if result.strip().lower() == 'b':
            raise BackException()
        if result.strip().lower() == 't':
            raise TopException()
        
        # Check for empty input
        if not result.strip() and not allow_empty:
            console.print("[red]Please enter a value (or 'b' to go back)[/red]")
            continue
        
        return result


# Global state reference for breadcrumb access
_current_state: Optional[Any] = None


def set_wizard_state(state: Any):
    """Set the global wizard state for breadcrumb access."""
    global _current_state
    _current_state = state


def get_wizard_state() -> Optional[Any]:
    """Get the current wizard state."""
    return _current_state


class BackException(Exception):
    """Exception to signal going back one step within a section."""
    pass


class TopException(Exception):
    """Exception to signal returning to the start of the wizard (all hierarchies)."""
    pass


class StepNavigator:
    """
    Helper class to implement step-based navigation within a configuration section.
    
    Usage:
        nav = StepNavigator()
        
        while not nav.done:
            try:
                if nav.step == 0:
                    # First prompt
                    name = prompt_with_nav("Enter name")
                    nav.set_value('name', name)
                    nav.next()
                elif nav.step == 1:
                    # Second prompt
                    count = prompt_with_nav("Enter count", is_int=True)
                    nav.set_value('count', count)
                    nav.next()
                elif nav.step == 2:
                    nav.finish()
            except BackException:
                nav.back()
            except TopException:
                raise  # Propagate to restart wizard
        
        # Access values
        name = nav.get('name')
        count = nav.get('count')
    """
    
    def __init__(self, total_steps: int = 100):
        self.step = 0
        self.max_step = 0
        self.total_steps = total_steps
        self.values = {}
        self.done = False
    
    def next(self):
        """Move to next step."""
        self.step += 1
        self.max_step = max(self.max_step, self.step)
    
    def back(self):
        """Go back one step. Returns False if already at step 0."""
        if self.step > 0:
            self.step -= 1
            console.print(f"[yellow]← Going back...[/yellow]")
            return True
        return False
    
    def finish(self):
        """Mark navigation as complete."""
        self.done = True
    
    def set_value(self, key: str, value: Any):
        """Store a value for later retrieval."""
        self.values[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a stored value."""
        return self.values.get(key, default)
    
    def has(self, key: str) -> bool:
        """Check if a value is stored."""
        return key in self.values
    
    def get_default(self, key: str, fallback: Any = None) -> Any:
        """Get stored value for use as a default (shows previous input when going back)."""
        return self.values.get(key, fallback)


def show_breadcrumb(path: List[str] = None):
    """Display the current navigation path as a breadcrumb.
    
    Args:
        path: Optional path to display. If None, uses global state.
    """
    if path is None and _current_state is not None:
        path = _current_state.nav_path
    
    if not path:
        return
    
    # Build breadcrumb string with styling
    breadcrumb_parts = []
    for i, part in enumerate(path):
        if i == len(path) - 1:
            # Current location (highlighted)
            breadcrumb_parts.append(f"[bold cyan]{part}[/bold cyan]")
        else:
            # Parent path (dim)
            breadcrumb_parts.append(f"[dim]{part}[/dim]")
    
    breadcrumb = " › ".join(breadcrumb_parts)
    console.print(f"\n[dim]📍[/dim] {breadcrumb}")


def push_path(segment: str):
    """Add a segment to the navigation path."""
    if _current_state is not None:
        _current_state.nav_path.append(segment)


def pop_path():
    """Remove the last segment from the navigation path."""
    if _current_state is not None and _current_state.nav_path:
        _current_state.nav_path.pop()


def set_path(path: List[str]):
    """Set the entire navigation path."""
    if _current_state is not None:
        _current_state.nav_path = path.copy()

