# SCALER Coding Standards & Reminders

## ⚠️ CRITICAL: Always Add Back/Navigation Options

### Rule: Every Menu, Prompt, and Hierarchy MUST Have Navigation Options

When adding any new menu, prompt, or interactive hierarchy to the SCALER application:

1. **ALWAYS include `[B] Back` option** in every menu
2. **ALWAYS handle `b` and `B` inputs** to go back to previous menu
3. **ALWAYS handle `t` and `T` inputs** to return to top (where applicable)
4. **For text prompts**, check if input is `b` or `back` before processing

### Bad Example ❌
```python
# Missing back option!
sub_path = Prompt.ask("Enter sub-path (e.g., 'evpn-vpws-fxc instance FXC-100')")
```

### Good Example ✅
```python
sub_path = Prompt.ask("Enter sub-path (or 'b' to go back)")
if sub_path.lower() in ('b', 'back', ''):
    return None, None  # Go back
```

### Checklist for New Menus

- [ ] Back option (`[B]`) displayed in menu
- [ ] `b` and `B` in valid choices
- [ ] Handler for back returns to previous menu
- [ ] Top option (`[T]`) if deep in hierarchy
- [ ] Empty input (`Enter`) has sensible default (usually back or cancel)
- [ ] `Confirm.ask()` prompts should NOT trap user (provide escape)

### Where to Apply

Apply to ALL of:
- Main wizard menus
- Service configuration
- Hierarchy selection
- Delete menus (single and multi-device)
- Sub-path/granular selection prompts
- Any `Prompt.ask()` or `Confirm.ask()` that could trap user

---

## Navigation Pattern Reference

### Standard Menu Pattern
```python
console.print("  [1] Option 1")
console.print("  [2] Option 2")
console.print("  [B] Back")
console.print("  [T] Top (return to start)")

choice = Prompt.ask("Select", choices=["1", "2", "b", "B", "t", "T"], default="b")

if choice.lower() == 'b':
    return None  # or raise BackException()
if choice.lower() == 't':
    raise TopException()
```

### Text Input with Back
```python
value = Prompt.ask("Enter value (or 'b' to go back)", default="b")
if value.lower() in ('b', 'back', ''):
    return None  # Go back
```

### Confirm with Escape
```python
# BAD - traps user!
if not Confirm.ask("Continue?", default=False):
    # Still continues to next step...

# GOOD - allow escape
proceed = Confirm.ask("Continue? (Ctrl+C to cancel)", default=False)
if not proceed:
    console.print("[dim]Cancelled.[/dim]")
    return None
```

---

## Reference Files

When implementing new features, check these for patterns:
- `/home/dn/SCALER/scaler/interactive_scale.py` - Main wizard with navigation
- `/home/dn/SCALER/scaler/wizard/push.py` - Delete hierarchy menus
- `/home/dn/SCALER/scaler/wizard/core.py` - `BackException`, `TopException`

---

*Last updated: December 2025*













