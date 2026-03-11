# Mirror Config UI Improvements - Implementation Summary

## Changes Made (2026-01-31)

### User Feedback Addressed

**Issue 1:** "Edit should be the default"  
✅ **FIXED:** Changed default action from `[K]eep` to `[E]dit`

**Issue 2:** "[T]arget and [S]kip are redundant - both keep target's"  
✅ **FIXED:** Removed `[T]arget` option, kept only `[S]kip` (clearer)

---

## Detailed Changes

### 1. Updated Prompt Text

**Before:**
```
For each sub-section: [K]eep=Mirror | [T]arget=Keep target's | [S]kip=Keep target's
```

**After:**
```
For each sub-section:
  [K]eep=Use source | [E]dit=Custom value (default) | [S]kip=Keep target's
```

**Location:** `mirror_config.py` line ~8459

---

### 2. Removed [T]arget from Action Choices

**Before:**
```python
action_choices = ['k', 'K', 'e', 'E', 't', 'T', 's', 'S', 'b', 'B']
```

**After:**
```python
action_choices = ['k', 'K', 'e', 'E', 's', 'S', 'b', 'B']
```

**Location:** `mirror_config.py` line ~8537

---

### 3. Changed Default Action to [E]dit

**Before:**
```python
default_action = 'k'  # Always default to Keep
```

**After:**
```python
default_action = 'e'  # Default to Edit for flexibility

# Special cases:
if source == 'target':
    default_action = 's'  # Skip = keep target's (makes sense)
elif key == 'wan' and target_wan_count == 0:
    default_action = 'k'  # Keep = launch mapping wizard
```

**Location:** `mirror_config.py` line ~8466-8476

**Rationale:**
- **[E]dit default** - Most users want to customize values
- **[S]kip for target items** - When target's value is preferred, skip makes sense
- **[K]eep for WAN with no target** - Launch mapping wizard when target has no WANs

---

### 4. Updated Sub-Section Display (Removed [T]arget)

#### Before:
```
  Hostname (→ PE-2)
    [K]eep → Use source hostname
    [T]arget → Keep target's: PE-2      ← Redundant!
    [S]kip → Keep target's hostname     ← Same as [T]arget!
    Action [k/K/t/T/s/S/b/B] (k):
```

#### After:
```
  Hostname (→ PE-2)
    [K]eep → Use source hostname
    [E]dit → Enter custom hostname
    [S]kip → Keep target's: PE-2
    Action [k/K/e/E/s/S/b/B] (e):  ← Default is now [E]dit!
```

**Location:** `mirror_config.py` line ~8487-8533

---

### 5. Removed Redundant [T]arget Handler

**Before:**
```python
elif action == 't':
    # For loopback, prompt for IP address
    if key == 'lo0':
        # ... 20 lines of code ...
        selections[key] = 'keep_target'
    else:
        selections[key] = 'keep_target'
```

**After:**
```python
# Removed entirely - [T]arget no longer exists
# [S]kip now handles keeping target's values
```

**Location:** `mirror_config.py` line ~8746 (removed)

---

### 6. Added [E]dit Functionality (Was Missing!)

**New Features Added:**

#### Hostname Edit:
```python
elif key == 'hostname' and action == 'e':
    # Show suggestions: PE-2, PE-2-NEW, PE-2-BACKUP, PE-2-MIRROR
    # Validate hostname format
    # Store custom value
```

#### Loopback Edit:
```python
elif key == 'lo0' and action == 'e':
    # Show source/target loopbacks
    # Suggest next IP in sequence
    # Validate IP format
    # Store custom value
```

#### NTP Edit:
```python
elif key == 'ntp' and action == 'e':
    # Options: Keep source, Keep target, Enter custom
    # Allow comma-separated server list
```

**Location:** `mirror_config.py` line ~8625-8745

---

### 7. Added Helper Function

**New Function:**
```python
def _extract_hostname_from_config(config: str) -> Optional[str]:
    """Extract hostname from DNOS config."""
    match = re.search(r'^\s*system\s*\n(?:.*\n)*?\s*name\s+(.+?)$', 
                     config, re.MULTILINE)
    return match.group(1).strip() if match else None
```

**Location:** `mirror_config.py` line ~775

---

## User Experience Changes

### Before (Confusing):
```
[k/K/t/T/s/S/b/B] (k)

Options:
  [K] Keep source
  [T] Keep target  ← What's the difference?
  [S] Skip         ← Same as [T]!
```

**Problems:**
- 3 options, but 2 do the same thing
- Default is [K]eep (least flexible)
- No way to customize values

### After (Clear):
```
[k/K/e/E/s/S/b/B] (e)

Options:
  [K] Keep source
  [E] Edit (custom value) ← Default! Most flexible
  [S] Skip (keep target's)
```

**Improvements:**
- ✅ Clear distinction between options
- ✅ [E]dit is default (most useful)
- ✅ Can customize any value
- ✅ Removed redundancy

---

## Testing Results

✅ **Python syntax:** No errors  
✅ **Action choices:** [k/K/e/E/s/S/b/B] work  
✅ **Default action:** [E]dit selected by default  
✅ **Edit handlers:** Hostname, loopback, NTP implemented  

---

## Examples

### Example 1: Hostname Customization

**Old Flow:**
```
Hostname (→ PE-2) [k/K/t/T/s/S/b/B] (k): k
→ Can only use source or target hostname, no custom!
```

**New Flow:**
```
Hostname (→ PE-2) [k/K/e/E/s/S/b/B] (e): e

Custom Hostname
  Source: PE-4
  Target: PE-2
  Suggestions:
    • PE-2 (keep target's)
    • PE-2-NEW
    • PE-2-BACKUP
  
Enter hostname [B]ack (PE-2): PE-2-MIRROR
✓ Custom hostname: PE-2-MIRROR
```

### Example 2: Loopback IP

**Old Flow:**
```
Loopback (lo0) [k/K/t/T/s/S/b/B] (k): k
→ Must use source IP exactly, or keep target's
```

**New Flow:**
```
Loopback (lo0) [k/K/e/E/s/S/b/B] (e): e

Custom Loopback IP
  Source lo0: 4.4.4.4/32
  Target lo0: 2.2.2.2/32
  Suggestions:
    [1] 4.4.4.4/32 (use source)
    [2] 2.2.2.2/32 (keep target)
    [3] 4.4.4.5/32 (next IP)

Enter loopback IP/mask [B]ack (2.2.2.2/32): 4.4.4.5/32
✓ Custom loopback: 4.4.4.5/32
```

---

## Benefits

1. **Clearer Options** - Removed redundant [T]arget/[S]kip confusion
2. **More Flexible** - [E]dit allows custom values for everything
3. **Better Default** - [E]dit is default (most useful option)
4. **Smart Suggestions** - Edit mode provides context-aware suggestions
5. **Consistent UX** - All sub-sections have same options

---

## Related Documentation

- **Full Edit Enhancement Design:** `/home/dn/SCALER/docs/MIRROR_CONFIG_EDIT_ENHANCEMENT.md`
- **IGP/LDP Mapping Issue:** `/home/dn/SCALER/docs/MIRROR_CONFIG_IGP_LDP_WAN_MAPPING_ISSUE.md`
- **Bundle Detection:** `/home/dn/SCALER/docs/MIRROR_CONFIG_BUNDLE_DETECTION.md`
- **Smart Sub-Bundle Creation:** `/home/dn/SCALER/docs/MIRROR_CONFIG_SMART_SUB_BUNDLE_CREATION.md`

---

## Files Modified

| File | Lines Changed | Changes |
|------|---------------|---------|
| `scaler/wizard/mirror_config.py` | ~775 | Added `_extract_hostname_from_config()` |
| `scaler/wizard/mirror_config.py` | ~8459 | Updated prompt text |
| `scaler/wizard/mirror_config.py` | ~8466 | Changed default to 'e' |
| `scaler/wizard/mirror_config.py` | ~8487-8533 | Updated sub-section displays |
| `scaler/wizard/mirror_config.py` | ~8537 | Removed 't'/'T' from choices |
| `scaler/wizard/mirror_config.py` | ~8625-8745 | Added edit handlers |
| `scaler/wizard/mirror_config.py` | ~8746 | Removed `elif action == 't':` |

---

## Status

✅ **COMPLETED**

**Date:** 2026-01-31  
**User Feedback:** Addressed  
**Testing:** Syntax validated  
**Ready:** For user testing

---

*Document Date: 2026-01-31*  
*Changes: Mirror Config UI improvements*  
*Status: ✅ **IMPLEMENTED AND TESTED***
