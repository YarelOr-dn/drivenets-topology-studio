# Multi-Device Recovery Protection

## Overview

When entering **Multi-Device Configuration Mode**, devices in **non-operational recovery states** are now **automatically greyed out** and **cannot be selected** until they are fixed.

---

## What's Protected

### ❌ **Non-Configurable States** (Greyed Out)
These devices **cannot** be selected in multi-device mode:

1. **ONIE** - Lowest-level bootloader, BaseOS missing
2. **BASEOS_SHELL** - Linux shell, GI not running
3. **DN_RECOVERY** - DNOS failed to boot

**Why?** These devices have no running DNOS and cannot receive configuration.

### ✅ **Semi-Operational States** (Selectable)
These devices **can** be selected in multi-device mode:

1. **GI_MODE** - Golden Image ready, can deploy DNOS
2. **STANDALONE** - One NCC down, but still operational
3. **OK** - Fully operational

**Why?** These devices can still receive and apply configuration.

---

## Visual Indicators

### Multi-Device Selection Table

**Before (no protection):**
```
╭───┬─────┬──────────┬───────────┬────────────┬──────────────╮
│ # │ ID  │ Hostname │ Loopback  │ Type       │ Status       │
├───┼─────┼──────────┼───────────┼────────────┼──────────────┤
│ 1 │ pe1 │ PE-1     │ 10.0.0.1  │ SA-36CD-S  │ OK           │
│ 2 │ pe2 │ PE-2     │ N/A       │ SA-36CD-S  │ RECOVERY     │ ← Could select!
│ 3 │ pe4 │ PE-4     │ 10.0.0.4  │ CL-86      │ OK           │
╰───┴─────┴──────────┴───────────┴────────────┴──────────────╯
```

**After (with protection):**
```
╭───┬─────┬──────────┬───────────┬────────────┬───────────────────╮
│ # │ ID  │ Hostname │ Loopback  │ Type       │ Status            │
├───┼─────┼──────────┼───────────┼────────────┼───────────────────┤
│ 1 │ pe1 │ PE-1     │ 10.0.0.1  │ SA-36CD-S  │ OK                │
│ 2 │ pe2 │ PE-2     │ N/A       │ SA-36CD-S  │ BASEOS_SHELL      │ ← Greyed!
│ 3 │ pe4 │ PE-4     │ 10.0.0.4  │ CL-86      │ OK                │
╰───┴─────┴──────────┴───────────┴────────────┴───────────────────╯

Note: Greyed devices are in recovery mode and cannot be configured.
      Fix them first using System Restore wizard (single device mode).
```

- **Greyed text:** Entire row dimmed
- **Strikethrough:** Hostname has strikethrough
- **Specific status:** Shows exact recovery type (not generic "RECOVERY")
- **Helper note:** Explains what to do

---

## Selection Protection

### User Tries to Select Recovery Device

```
Select devices: 1,2

✗ Cannot select devices in recovery mode:
  • PE-2 (BASEOS_SHELL)

Fix these devices first:
  1. Exit multi-device mode ([B]ack)
  2. Select device in single-device mode
  3. Run System Restore wizard
  4. Return to multi-device mode

Press Enter to continue:
```

### "All" Option Auto-Filters

```
Select devices: all

✓ Selected 2 devices:
  • PE-1 (10.0.0.1)
  • PE-4 (10.0.0.4)
  
Note: PE-2 excluded (BASEOS_SHELL - not configurable)
```

The `all` option automatically **excludes non-configurable devices**.

---

## Complete Flow Example

### Scenario: User tries multi-device with PE-2 in BASEOS_SHELL

```
1. User selects [2] Multi-device synchronized mode
   ↓
2. Device table shows:
   • PE-1: OK (normal display)
   • PE-2: BASEOS_SHELL (greyed out, strikethrough)
   • PE-4: OK (normal display)
   ↓
3. Note displayed:
   "Greyed devices are in recovery mode and cannot be configured"
   ↓
4. User tries to select: 1,2,3
   ↓
5. Error displayed:
   "✗ Cannot select devices in recovery mode: PE-2 (BASEOS_SHELL)"
   ↓
6. Instructions shown:
   "Fix these devices first: Exit → Single-device mode → System Restore"
   ↓
7. User presses Enter, returns to selection
   ↓
8. User selects: 1,3 (only OK devices)
   ↓
9. ✓ Multi-device mode proceeds with PE-1 and PE-4
```

---

## Implementation Details

### Helper Functions

```python
def _is_device_in_recovery(dev: Device) -> bool:
    """Check if device is in recovery mode."""
    # Reads operational.json and checks recovery_mode_detected
    
def _is_device_configurable(dev: Device) -> bool:
    """Check if device can be configured."""
    # Returns True for: GI, STANDALONE, or not in recovery
    # Returns False for: ONIE, BASEOS_SHELL, DN_RECOVERY
```

### Display Logic

```python
# Get recovery status
in_recovery = op_data.get('recovery_mode_detected')
recovery_type = op_data.get('recovery_type', '')

# Determine if configurable
configurable_states = ['GI', 'STANDALONE', '']
is_configurable = not in_recovery or recovery_type in configurable_states

# Grey out if not configurable
if not is_configurable:
    table.add_row(
        f"[dim]{i}[/dim]",
        f"[dim]{dev.id}[/dim]",
        f"[dim strike]{dev.hostname}[/dim]",  # Strikethrough!
        f"[dim]{loopback}[/dim]",
        f"[dim]{system_type}[/dim]",
        f"[dim]{status_str}[/dim]"
    )
```

### Validation Logic

```python
# Filter out non-configurable devices
invalid_devices = [
    d for d in selected 
    if _is_device_in_recovery(d) and not _is_device_configurable(d)
]

if invalid_devices:
    # Show error with device names and recovery types
    # Show fix instructions
    # Return to selection
```

---

## Benefits

1. **Prevents Configuration Errors:**
   - Can't push config to devices with no DNOS
   - Avoids failed operations

2. **Clear Visual Feedback:**
   - Greyed out = not selectable
   - Specific status = know exactly what's wrong

3. **Helpful Guidance:**
   - Instructions on how to fix
   - Step-by-step recovery path

4. **Smart Defaults:**
   - "all" auto-excludes problematic devices
   - Only selectable devices included

5. **Consistent Experience:**
   - Same recovery types as single-device mode
   - Same colors, same labels

---

## Testing Checklist

- [ ] **Visual Display:**
  - Recovery devices shown greyed out
  - Strikethrough on hostname
  - Specific recovery type displayed
  - Helper note visible

- [ ] **Selection Validation:**
  - Cannot manually select recovery device
  - Clear error message shown
  - Fix instructions displayed
  - Returns to selection after error

- [ ] **"All" Option:**
  - Auto-excludes recovery devices
  - Shows which devices excluded
  - Proceeds with only OK devices

- [ ] **State Boundary:**
  - GI and STANDALONE remain selectable
  - ONIE, BASEOS_SHELL, DN_RECOVERY blocked
  - OK devices always selectable

---

## Related Documentation

- `RECOVERY_WORKFLOW_COMPLETE.md` - Complete recovery workflows
- `STATE_DETECTION_MITIGATION_GUIDE.md` - State detection details
- `RECOVERY_ENHANCEMENT_SUMMARY.md` - Overall recovery system
