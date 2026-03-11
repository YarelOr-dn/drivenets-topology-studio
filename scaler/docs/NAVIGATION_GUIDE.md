# SCALER Wizard Navigation Guide

## Navigation Patterns

### Standard [B] Back Navigation

All prompts in the SCALER wizard support **[B] Back** navigation for consistency:

```python
from scaler.interactive_scale import NavigablePrompt, BackException

# Simple prompt with auto [B]ack hint
result = NavigablePrompt.ask("Enter value", default="100")
if result == NavigablePrompt.BACK:
    raise BackException()  # Return to previous step

# Integer prompt with validation
count = NavigablePrompt.ask_int("How many VRFs?", default=10, min_value=1, max_value=1000)
if count == NavigablePrompt.BACK:
    raise BackException()

# Prompt with choices (B auto-added to choices)
choice = NavigablePrompt.ask("Select option", choices=["1", "2", "3"], default="1")
if choice == NavigablePrompt.BACK:
    raise BackException()
```

### Multi-Step Wizards with Redo Support

For complex wizards (like VRF configuration), use the step loop pattern:

```python
while True:  # Outer loop for Step 1 + Step 2
    # Step 1: Basic config
    console.print("\n[bold]Step 1: Configuration[/bold]")
    value = NavigablePrompt.ask("Enter value", default="100")
    if value == NavigablePrompt.BACK:
        continue  # Restart Step 1
    
    # Step 2: Interface selection
    console.print("\n[bold]Step 2: Interfaces[/bold]")
    iface_choice = NavigablePrompt.ask("Select", choices=["y", "n"], default="y")
    if iface_choice == NavigablePrompt.BACK:
        continue  # Return to Step 1
    
    break  # Both steps completed, exit loop

# Step 3: Advanced options (outside loop)
console.print("\n[bold]Step 3: Advanced[/bold]")
bgp_as = NavigablePrompt.ask_int("BGP AS", default=65000)
if bgp_as == NavigablePrompt.BACK:
    # Goes back to Step 2 via outer try/except BackException
    raise BackException()
```

## Current Implementation

### VRF Wizard Navigation Flow

```
Step 1: VRF Instances
  ├─ VRF count [B]ack → Exit wizard
  ├─ VRF prefix [B]ack → Re-enter count
  └─ Description [B]ack → Re-enter prefix

Step 2: Interface Attachment  
  ├─ Attach? [Y/N/B] → [B] returns to Step 1
  ├─ Interface selection [B]ack → Re-ask attach
  └─ Distribution strategy [B]ack → Re-select interfaces

        [Step 1+2 loop breaks here]

Step 3: BGP Protocol
  ├─ BGP AS [B]ack → Returns to Step 2 (via BackException)
  ├─ Router ID [B]ack → Returns to Step 2
  └─ RD format [B]ack → Returns to Step 2

Step 4: Address Families
  └─ AFI selection [B]ack → Returns to Step 3

... (additional steps)
```

## Best Practices

### 1. Always Check for BACK

```python
result = NavigablePrompt.ask("Prompt", default="value")
if result == NavigablePrompt.BACK:
    raise BackException()  # Or continue/break depending on loop
```

### 2. Use Try/Except for BackException

```python
while hierarchy_idx < len(hierarchies):
    try:
        config = configure_vrf_services(state, limits, multi_ctx)
        hierarchy_idx += 1
    except BackException:
        if hierarchy_idx > 0:
            hierarchy_idx -= 1  # Go back to previous hierarchy
            console.print(f"[yellow]← Returning to {hierarchies[hierarchy_idx]}[/yellow]")
```

### 3. Nested Loops for Multi-Step Wizards

When steps need to reference each other (like VRF count affects interface distribution), wrap them in a loop:

```python
while True:  # Step 1 + Step 2 loop
    # Step 1
    vrf_count = NavigablePrompt.ask_int("VRF count", default=1)
    if vrf_count == NavigablePrompt.BACK:
        return None  # Exit wizard
    
    # Step 2 (uses vrf_count from Step 1)
    if interface_list < vrf_count:
        strategy = NavigablePrompt.ask("Distribution", choices=["1", "2", "3"])
        if strategy == NavigablePrompt.BACK:
            continue  # Return to Step 1
    
    break  # Both steps completed

# Step 3 (independent)
bgp_as = NavigablePrompt.ask_int("BGP AS", default=65000)
if bgp_as == NavigablePrompt.BACK:
    raise BackException()  # Caught by outer loop, returns to Step 2
```

## Future Enhancements

### Arrow Key Support (Optional)

While `NavigablePrompt` is designed for [B] navigation (terminal-compatible), arrow key support could be added:

```python
# Note: Requires additional terminal library (e.g., readchar, keyboard)
import sys, tty, termios

def get_key():
    """Read a single keypress."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        if ch == '\x1b':  # Escape sequence
            ch += sys.stdin.read(2)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

# In prompt:
key = get_key()
if key == '\x1b[D':  # Left arrow
    return NavigablePrompt.BACK
```

**Decision:** Arrow keys are NOT currently implemented because:
- Not all terminals support them reliably
- SSH sessions may have escape sequence conflicts
- [B] is more explicit and universally supported

## Redo Functionality

To add per-hierarchy redo (e.g., "Redo interfaces" after completing):

```python
class HierarchyStep:
    def __init__(self, name, config_fn, result):
        self.name = name
        self.config_fn = config_fn
        self.result = result
    
    def redo(self, state, limits, multi_ctx):
        console.print(f"[yellow]↻ Redoing {self.name}...[/yellow]")
        return self.config_fn(state, limits, multi_ctx)

# After each hierarchy:
steps = []
config = configure_interfaces(state, limits, multi_ctx)
steps.append(HierarchyStep("Interfaces", configure_interfaces, config))

# Offer redo
console.print("\n[bold green]✓ Interfaces completed[/bold green]")
console.print("  [C] Continue  [R] Redo  [B] Back")
action = Prompt.ask("Select", choices=["c", "r", "b"], default="c")
if action == 'r':
    config = steps[-1].redo(state, limits, multi_ctx)
elif action == 'b':
    raise BackException()
```

## Summary

- **[B] Back** is the primary navigation mechanism (consistent, terminal-agnostic)
- **Arrow keys** are NOT implemented (terminal compatibility issues)
- **Redo** can be added per-hierarchy with [C]ontinue/[R]edo/[B]ack menu
- **NavigablePrompt** provides uniform prompt handling with auto [B]ack hints
- **BackException** is caught by outer loops to return to previous steps
