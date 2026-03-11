# Mirror Config: IGP/LDP Interface Mapping Issue 🔴 CRITICAL

## Problem Statement

**User Question:**  
> "How will it handle IGP + LDP interfaces? will it prompt user to change to according WAN interface?"

**Answer:** Currently **IT DOES NOT!** This is a **CRITICAL BUG** ❌

### The Issue

When you mirror config from PE-4 to PE-2 and **remap WAN interfaces** in the wizard:
- ✅ WAN interface section updates correctly (ge100-18/0/0.14 → ge400-0/0/0)
- ❌ **IGP (IS-IS) interface references NOT updated!**
- ❌ **LDP interface references NOT updated!**
- ❌ **OSPF interface references NOT updated!**

### Example Scenario

**Source (PE-4) Config:**
```
interfaces
  ge100-18/0/0.14
    ipv4-address 14.14.14.4/29
  !
!

protocols
  isis
    instance IGP
      interface ge100-18/0/0.14  ← Source WAN interface
        admin-state enabled
      !
    !
  !
  ldp
    interface ge100-18/0/0.14    ← Source WAN interface
      admin-state enabled
    !
  !
!
```

**User Action in Mirror Wizard:**
```
WAN Mapping:
  ge100-18/0/0.14 (14.14.14.4/29) → ge400-0/0/0 (new IP: 14.14.14.2/29)
```

**Expected Result:**
```
interfaces
  ge400-0/0/0                     ← Mapped correctly ✅
    ipv4-address 14.14.14.2/29
  !
!

protocols
  isis
    instance IGP
      interface ge400-0/0/0       ← Should use mapped interface ✅
        admin-state enabled
      !
    !
  !
  ldp
    interface ge400-0/0/0         ← Should use mapped interface ✅
      admin-state enabled
    !
  !
!
```

**Actual Result (Current Bug):**
```
interfaces
  ge400-0/0/0                     ← Mapped correctly ✅
    ipv4-address 14.14.14.2/29
  !
!

protocols
  isis
    instance IGP
      interface ge100-18/0/0.14   ← ❌ WRONG! Still source interface!
        admin-state enabled
      !
    !
  !
  ldp
    interface ge100-18/0/0.14     ← ❌ WRONG! Still source interface!
      admin-state enabled
    !
  !
!
```

---

## Root Cause Analysis

### Code Flow

**File:** `scaler/wizard/mirror_config.py`

#### 1. WAN Interface Detection (Line 2302, 4747)
```python
# ConfigMirror.__init__()
self.target_wan = self._get_igp_interfaces(target_config)  # Gets target's ORIGINAL interfaces

# Later in _merge_wan_protocol_interfaces()
wan_ifaces = set(self.target_wan)  # Uses ORIGINAL target interfaces, NOT mapped ones!
```

#### 2. Protocol Interface Generation (Line 4814, 4781)
```python
# Generate ISIS interfaces
wan_isis_config = self._generate_wan_isis_interfaces(wan_ifaces)

# Generate LDP interfaces
wan_ldp_config = self._generate_wan_ldp_interfaces(wan_ifaces)
```

**Problem:** `wan_ifaces` contains **target's original interfaces**, NOT the **remapped interfaces from WAN mapping wizard!**

#### 3. WAN Mapping Wizard Result Storage

When user completes WAN mapping wizard (line 8566):
```python
mapping_result = wan_interface_mapping_wizard(mini_state, source_wans)

if mapping_result:
    selections[key] = {'action': 'map', 'mapping': mapping_result}
```

**Problem:** The `mapping_result` is stored in `selections['wan']` but **never passed to** `_merge_wan_protocol_interfaces()` or `_generate_wan_isis_interfaces()`!

---

## The Missing Link

### What Should Happen

1. ✅ User completes WAN mapping wizard
2. ✅ Mappings stored: `{source_if: target_if, IP transformations}`
3. ❌ **MISSING:** Pass mappings to protocol interface generator
4. ❌ **MISSING:** Replace source interface refs with target interface refs in ISIS/LDP/OSPF

### Current Data Flow

```
WAN Mapping Wizard
  ↓
  mappings = {
    'ge100-18/0/0.14': {
      'target': 'ge400-0/0/0',
      'ip_transformations': {'14.14.14.4/29': '14.14.14.2/29'}
    }
  }
  ↓
  selections['wan'] = {'action': 'map', 'mapping': mappings}
  ↓
  [CONFIG GENERATION]
  ↓
  _merge_wan_protocol_interfaces()
    ↓
    wan_ifaces = self.target_wan  ← ❌ Uses target's ORIGINAL interfaces!
    ↓
    _generate_wan_isis_interfaces(wan_ifaces)  ← ❌ Generates with WRONG interfaces!
```

### Required Data Flow

```
WAN Mapping Wizard
  ↓
  mappings = {
    'ge100-18/0/0.14': 'ge400-0/0/0',
    ...
  }
  ↓
  selections['wan'] = {'action': 'map', 'mapping': mappings}
  ↓
  [CONFIG GENERATION]
  ↓
  _build_final_config(sections, selections)  ← Pass selections here!
    ↓
    Extract WAN mappings from selections['wan']
    ↓
    mapped_interfaces = mappings.values()  ← Use MAPPED interfaces!
    ↓
    _merge_wan_protocol_interfaces(mapped_interfaces)
      ↓
      _generate_wan_isis_interfaces(mapped_interfaces)  ← ✅ Use mapped interfaces!
```

---

## Solution Design

### Phase 1: Pass WAN Mappings to Protocol Generator

**Modify:** `_merge_wan_protocol_interfaces()` signature

```python
def _merge_wan_protocol_interfaces(
    self, 
    source_protocols: str, 
    target_wan_protocols: Dict[str, str],
    wan_mappings: Optional[Dict[str, str]] = None  # NEW parameter
) -> str:
    """
    Add target's WAN interfaces to source's routing protocols.
    
    Args:
        wan_mappings: Optional dict of {source_if: target_if} from WAN wizard
                     If provided, use mapped interfaces instead of self.target_wan
    """
    # Use mapped interfaces if provided, otherwise fall back to target_wan
    if wan_mappings:
        # Extract target interfaces from mappings
        wan_ifaces = set(wan_mappings.values())
    else:
        wan_ifaces = set(self.target_wan)
    
    # ... rest of function
```

### Phase 2: Extract Mappings from Selections

**Add helper function:**

```python
def _extract_wan_mappings(selections: dict) -> Optional[Dict[str, str]]:
    """
    Extract WAN interface mappings from section selections.
    
    Returns:
        Dict of {source_interface: target_interface} or None
    """
    wan_selection = selections.get('wan')
    if not wan_selection or not isinstance(wan_selection, dict):
        return None
    
    if wan_selection.get('action') != 'map':
        return None
    
    mapping_result = wan_selection.get('mapping')
    if not mapping_result:
        return None
    
    # Extract actual mappings
    # mapping_result is a SectionResult with items_selected containing the map
    if hasattr(mapping_result, 'items_selected'):
        return mapping_result.items_selected
    elif isinstance(mapping_result, dict):
        return mapping_result.get('mappings', {})
    
    return None
```

### Phase 3: Update Build Flow

**Modify:** `build_final_config()` or wherever protocols section is built

```python
def build_protocols_section(
    self,
    include_protocols: bool,
    selections: dict
) -> str:
    """
    Build protocols section with WAN interface mappings applied.
    """
    # Extract source protocols
    source_protocols = self._extract_protocols_section(self.source_config)
    
    # Get target's WAN protocol config
    target_wan_protocols = self._extract_target_wan_protocol_config()
    
    # Extract WAN mappings from selections
    wan_mappings = _extract_wan_mappings(selections)
    
    # Merge with WAN mappings applied
    merged_protocols = self._merge_wan_protocol_interfaces(
        source_protocols,
        target_wan_protocols,
        wan_mappings=wan_mappings  # NEW: Pass mappings!
    )
    
    return merged_protocols
```

### Phase 4: Update Interface Name Replacement

**Enhance:** `_generate_wan_isis_interfaces()`, `_generate_wan_ldp_interfaces()`

These functions already take `wan_ifaces` set, so if we pass the correct mapped interfaces, they should work!

**BUT:** We also need to handle cases where source config has ISIS/LDP entries for source interfaces that need to be replaced:

```python
def _apply_interface_mappings_to_protocols(
    self,
    protocols: str,
    interface_mappings: Dict[str, str]
) -> str:
    """
    Replace source interface names with target interface names in protocol config.
    
    Args:
        protocols: Protocol config text
        interface_mappings: {source_if: target_if}
    
    Returns:
        Updated protocol config with mapped interface names
    """
    result = protocols
    
    for source_if, target_if in interface_mappings.items():
        # Pattern: interface <source_if>
        pattern = rf'(interface\s+){re.escape(source_if)}(\s|$)'
        replacement = rf'\g<1>{target_if}\g<2>'
        result = re.sub(pattern, replacement, result, flags=re.MULTILINE)
    
    return result
```

---

## Implementation Steps

### Step 1: Add wan_mappings Parameter ✅
```python
# In _merge_wan_protocol_interfaces()
def _merge_wan_protocol_interfaces(
    self, 
    source_protocols: str, 
    target_wan_protocols: Dict[str, str],
    wan_mappings: Optional[Dict[str, str]] = None
) -> str:
```

### Step 2: Extract Mappings from Selections ✅
```python
def _extract_wan_mappings(selections: dict) -> Optional[Dict[str, str]]:
    # ... implementation
```

### Step 3: Apply Mappings in Protocol Generation ✅
```python
if wan_mappings:
    wan_ifaces = set(wan_mappings.values())
    # Also replace source interface refs in copied protocol config
    source_protocols = self._apply_interface_mappings_to_protocols(
        source_protocols,
        wan_mappings
    )
else:
    wan_ifaces = set(self.target_wan)
```

### Step 4: Add Interface Replacement Function ✅
```python
def _apply_interface_mappings_to_protocols(
    self,
    protocols: str,
    interface_mappings: Dict[str, str]
) -> str:
    # ... implementation
```

### Step 5: Update All Call Sites ✅
- Find where `_merge_wan_protocol_interfaces()` is called
- Pass `wan_mappings` extracted from selections
- Test with real mirror scenario

---

## Testing Scenario

### Test Case 1: WAN Remap with IS-IS

**Setup:**
- Source: PE-4 with ge100-18/0/0.14 in IS-IS
- Target: PE-2 (map to ge400-0/0/0)

**Steps:**
1. Run Mirror Config wizard
2. Select [E]dit for SYSTEM (to configure hostname)
3. Select [K]eep for INTERFACES → Launch WAN mapping wizard
4. Map ge100-18/0/0.14 → ge400-0/0/0
5. Select [K]eep for PROTOCOLS
6. Generate config
7. **Verify:** IS-IS has `interface ge400-0/0/0` NOT `interface ge100-18/0/0.14`

### Test Case 2: Multiple WANs with IS-IS + LDP

**Setup:**
- Source: 4 WANs with IS-IS and LDP
- Target: Map each to different ge400 interfaces

**Expected:**
- IS-IS: All 4 target interfaces
- LDP: All 4 target interfaces
- NO source interface names in protocol section

### Test Case 3: No WAN Mapping (Keep Target's)

**Setup:**
- User selects [T]arget for WAN interfaces

**Expected:**
- IS-IS/LDP use target's existing WAN interfaces
- No change to target's protocol config
- ✅ This already works (uses `self.target_wan`)

---

## Priority & Impact

**Priority:** 🔴 **CRITICAL**

**Impact:**
- **Broken config** if user remaps WAN interfaces
- **Routing protocols won't work** (interfaces don't exist)
- **Silent failure** (no error shown, but config is invalid)
- **User must manually fix** after push

**Risk Level:** HIGH
- Most Mirror Config users will remap WAN interfaces
- This is core functionality, not an edge case

**Workaround (Current):**
1. Complete Mirror wizard
2. Before pushing, manually search-replace interface names in protocol section
3. Push corrected config

---

## Related Issues

### Issue 1: Bundle Interface Mapping
If source has bundles and user remaps bundle members, the bundle interface names in IS-IS/LDP also need updating.

### Issue 2: LACP Interface References
Similar issue: LACP protocol section references interfaces that may be remapped.

### Issue 3: BFD Interface References
BFD protocol may reference remapped WAN interfaces.

---

## Files to Modify

| File | Function | Change |
|------|----------|--------|
| `mirror_config.py` | `_merge_wan_protocol_interfaces()` | Add `wan_mappings` param |
| `mirror_config.py` | `_extract_wan_mappings()` | NEW: Extract from selections |
| `mirror_config.py` | `_apply_interface_mappings_to_protocols()` | NEW: Replace interface refs |
| `mirror_config.py` | `build_final_config()` or caller | Pass wan_mappings |

---

## Summary

**Current State:** ❌ WAN mapping wizard updates WAN interfaces but NOT protocol references

**Required Fix:** ✅ Extract WAN mappings → Pass to protocol generator → Replace interface names

**User Impact:** 🔴 CRITICAL - Generated config has invalid interface references

**Fix Complexity:** Medium (need to thread mappings through call chain)

**Testing:** Required before release (real PE-4 → PE-2 mirror scenario)

---

*Document Date: 2026-01-31*  
*Issue: IGP/LDP interfaces not updated when WAN interfaces remapped*  
*Status: 🔴 **BUG IDENTIFIED - FIX REQUIRED***
