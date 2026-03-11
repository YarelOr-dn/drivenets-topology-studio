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

---

## DNOS Version Compatibility System

### Architecture

The wizard has a data-driven version compatibility system that warns about config
incompatibilities before upgrades and automatically sanitizes config during restore.

| File | Purpose |
|------|---------|
| `db/dnos_version_compat.json` | Knowledge base: maps CLI commands to the version they were introduced (from RST Command History sections) |
| `scaler/version_compat.py` | Python module: reads the KB, computes incompatibilities, sanitizes config, formats reports |
| `scaler/interactive_scale.py` | Integration: pre-upgrade report + auto-sanitize on restore |

### How It Works

1. **Before upgrade**: When a major version jump is detected (e.g. 25.4 -> 19.2), the wizard
   shows a **Version Compatibility Report** listing all config features that exist in the
   source version but not in the target.

2. **During config restore**: `sanitize_config_for_version()` reads the knowledge base and
   strips incompatible lines/blocks before pushing config to the device. Version info is
   stored in `operational.json` (`pre_upgrade_version`, `target_upgrade_version`).

3. **Fallback**: If the JSON DB is missing or corrupt, the sanitizer falls back to hardcoded
   patterns (the original 25.4->19.2 incompatibilities discovered on 2026-03-10).

### Adding New Incompatibilities

When `load override` fails with "Unknown word" for a command not in the DB:

```python
from scaler.version_compat import add_discovered_incompatibility

add_discovered_incompatibility(
    feature_id="system.new_feature",
    config_path="system new-feature",
    added_in="26.1",
    description="New feature added in 26.1",
    match_type="single_line",           # or "block" for multi-line blocks
    match_pattern=r"^\s+new-feature\s",
    discovered_via="load override failed on PE-1, 26.1->25.4"
)
```

Or manually edit `db/dnos_version_compat.json` and add to the `features` section.

### Key Functions

```python
from scaler.version_compat import (
    build_compatibility_report,   # Full report: source_ver, target_ver -> dict
    format_report_for_terminal,   # Rich-formatted terminal output
    get_incompatible_features,    # List of features source has but target doesn't
    is_feature_available,         # Check if feature X exists in version Y
    sanitize_config,              # Data-driven config cleaner
    add_discovered_incompatibility  # Grow the KB from runtime discoveries
)
```

### Version Data Sources

The knowledge base is populated from:
- **RST Command History sections**: Each DNOS CLI RST doc has a "Command History" table
  showing `| Release | Modification |`. Use `search_cli_docs("command name")` then
  `get_cli_doc_section(doc, "command name")` to read the full entry including version info.
- **Live device testing**: When a `load override` fails, the error message tells you which
  command is incompatible. Test on the target version to confirm.
- **Upgrade history**: `db/upgrade_sources_history.json` records all version pairs the
  wizard has processed.

### Rules

- Upgrades (old -> new) do NOT need sanitization. New DNOS accepts old config.
- Downgrades (new -> old) need sanitization. Features added after the target version are stripped.
- Patch upgrades (25.4.x -> 25.4.y) have no incompatibilities.
- Portability-flagged features (e.g. encrypted passwords, BGP NSR format) are only stripped
  on downgrades where the major version differs.
- The `collapsible_parents` list controls which empty blocks are cleaned up after stripping.

*Last updated: March 2026*













