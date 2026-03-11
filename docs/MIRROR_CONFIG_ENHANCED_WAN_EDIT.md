# Mirror Config: Enhanced WAN Edit Experience

## Problem Statement

**User Complaint (2026-01-31):**
```
WAN Interfaces (4 interfaces)
  Action [k/K/e/E/s/S/b/B] (k): e

Edit not yet implemented for WAN Interfaces  ← ❌ WHAT THE HELL?!
Defaulting to [K]eep (use source)
```

**Comparison to Loopback Editor (Good Experience):**
```
Custom Loopback IP
  Source lo0: 4.4.4.4/32
  Target lo0: N/A
  Suggestions:
    [1] 4.4.4.4/32 (use source)
    [3] 4.4.4.5/32 (next IP)
  Enter loopback IP/mask [B]ack (4.4.4.4/32): 2.2.2.2/32
  ✓ Custom loopback: 2.2.2.2/32
```

**User's Request:**
> "enhance the editing experience with knowledge you have from other parts of the scaler-wizard logics..."

---

## Root Causes

### Issue 1: Old Python Process ❌
- User was running wizard with old code (before WAN handler was added)
- Changes to `mirror_config.py` don't take effect until wizard restart
- **Solution:** User must `Ctrl+C` → restart `./run.sh`

### Issue 2: Poor WAN Edit UX ❌
Even with the fix, the WAN edit just launched the full mapping wizard immediately:
- No quick summary of what's changing
- No smart suggestions like loopback editor
- No quick "keep target" or "copy source" shortcuts
- Forces user through multi-step wizard even for simple choices

---

## Solution: Quick WAN Edit with Smart Options

### New Enhanced Flow

**1. When user presses [E]dit on WAN:**
```
WAN Interface Configuration
  Source: 4 WAN interfaces
    • ge100-18/0/0.14 (14.14.14.4/29)
    • ge100-18/0/0.24 (24.24.24.4/29)
    • ge100-18/0/0.34 (34.34.34.4/29)
    • ge100-18/0/0.45 (45.45.45.4/29)
  Target: 0 WAN interfaces
  Target LLDP: 18 neighbors available

  Quick Options:
    [1] Copy source WANs as-is (4 interfaces) (recommended)
    [2] Map source WANs to target interfaces (using LLDP)
    [S] Skip WAN configuration
  Select [B]ack (1):
```

**If target already has WANs:**
```
WAN Interface Configuration
  Source: 4 WAN interfaces
    • ge100-18/0/0.14 (14.14.14.4/29)
    ...
  Target: 6 WAN interfaces
  Target LLDP: 18 neighbors available

  Quick Options:
    [1] Keep target's WAN config (6 interfaces) (recommended)
    [2] Copy source WANs as-is (4 interfaces)
    [3] Map source WANs to target interfaces (using LLDP)
    [S] Skip WAN configuration
  Select [B]ack (1):
```

**2. User Can Choose:**
- **[1] Keep target's** → Fast selection, no wizard
- **[2] Copy source** → Fast selection, no wizard
- **[3] Map (LLDP)** → Launches full mapping wizard
- **[S] Skip** → Exclude WAN from mirror

**3. Immediate Feedback:**
```
Select (1): 2⏎
  ✓ Copy 4 source WAN interfaces
```

---

## Implementation Details

### File: `scaler/wizard/mirror_config.py`

**Location:** Line ~8653 (`elif action == 'e':` → `if key == 'wan':`)

**Key Features:**

1. **Parse Source WAN Details:**
   ```python
   source_wans = get_wan_interfaces(mirror.source_config)
   source_wan_ips = {}
   for wan in source_wans:
       ip_match = re.search(...)
       source_wan_ips[wan] = ip_match.group(1)
   ```

2. **Load Target Context:**
   ```python
   target_wans = get_wan_interfaces(mirror.target_config)
   target_lldp_count = len(target_op.get('lldp_neighbors', []))
   ```

3. **Display Summary:**
   ```python
   console.print("Source: 4 WAN interfaces")
   for wan in source_wans[:4]:
       console.print(f"  • {wan} ({source_wan_ips[wan]})")
   console.print("Target: 0 WAN interfaces")
   console.print("Target LLDP: 18 neighbors available")
   ```

4. **Context-Aware Options:**
   ```python
   if target_wans:
       # Offer "Keep target's" first (recommended)
       choices_map['1'] = 'keep_target'
   
   # Always offer copy source
   choices_map[str(choice_num)] = 'copy_source'
   
   if target_lldp_count > 0:
       # Offer full mapping wizard
       choices_map[str(choice_num)] = 'full_wizard'
   ```

5. **Quick Actions:**
   ```python
   if choice == 'keep_target':
       selections[key] = 'keep_target'
       console.print("✓ Keep target's X WAN interfaces")
   elif choice == 'copy_source':
       selections[key] = 'mirror'
       console.print("✓ Copy X source WAN interfaces")
   elif choice == 'full_wizard':
       # Launch wan_interface_mapping_wizard()
   ```

---

## Comparison: Before vs After

### Before (Frustrating) ❌

```
WAN Interfaces [k/K/e/E/s/S/b/B] (k): e

Edit not yet implemented for WAN Interfaces
Defaulting to [K]eep (use source)
Press Enter to continue ():
```

**Problems:**
- ❌ Error message (even after fix, old process still running)
- ❌ No visibility into what's changing
- ❌ No quick options
- ❌ Forces wizard or nothing

### After (Smooth) ✅

```
WAN Interfaces [k/K/e/E/s/S/b/B] (e): e

WAN Interface Configuration
  Source: 4 WAN interfaces
    • ge100-18/0/0.14 (14.14.14.4/29)
    • ge100-18/0/0.24 (24.24.24.4/29)
    • ge100-18/0/0.34 (34.34.34.4/29)
    • ge100-18/0/0.45 (45.45.45.4/29)
  Target: 0 WAN interfaces
  Target LLDP: 18 neighbors available

  Quick Options:
    [1] Copy source WANs as-is (4 interfaces) (recommended)
    [2] Map source WANs to target interfaces (using LLDP)
    [S] Skip WAN configuration
  Select [B]ack (1): ⏎

  ✓ Copy 4 source WAN interfaces
```

**Benefits:**
- ✅ Clear summary of source/target state
- ✅ Smart context-aware suggestions
- ✅ Quick 1-key decisions
- ✅ Optional full wizard for advanced mapping
- ✅ Consistent with loopback editor UX
- ✅ Shows actual interface names and IPs

---

## Pattern: Quick Edit for All Sub-Sections

This pattern can be applied to other sub-sections:

### Pattern Template:
```python
elif key == 'some_key':
    # 1. Parse source/target data
    source_data = extract_from_config(mirror.source_config)
    target_data = extract_from_config(mirror.target_config)
    
    # 2. Show summary
    console.print("Summary:")
    console.print(f"  Source: {source_data}")
    console.print(f"  Target: {target_data}")
    
    # 3. Context-aware suggestions
    console.print("Quick Options:")
    console.print("  [1] Keep target's (recommended)")
    console.print("  [2] Use source")
    console.print("  [3] Custom edit (advanced)")
    
    # 4. Fast selection
    choice = Prompt.ask("Select", choices=['1','2','3','b','B'], default='1')
    
    # 5. Handle choice
    if choice == '1':
        selections[key] = 'keep_target'
        console.print("✓ Keep target's config")
    elif choice == '2':
        selections[key] = 'mirror'
        console.print("✓ Use source config")
    elif choice == '3':
        # Launch advanced wizard
        result = advanced_wizard(...)
        selections[key] = result
```

**Apply to:**
- ✅ WAN interfaces (DONE)
- ✅ Loopback (DONE)
- ✅ Hostname (DONE)
- ✅ NTP (DONE)
- 🔲 Service interfaces (pwhe, l2ac, bundles)
- 🔲 Protocols (ISIS, BGP, LDP)
- 🔲 Network services (FXC, VPWS, VPLS)

---

## User Flow (Complete)

**Scenario:** Mirror PE-4 → PE-2 (PE-2 has no WANs)

### Step 1: Launch Mirror Config
```
cd /home/dn/SCALER
./run.sh
→ Multi-Device Management
→ Mirror Configuration
→ Select source: PE-4 ✓
```

### Step 2: See Preview
```
Transformation Preview:
  WAN Interfaces: 4 in source
    • ge100-18/0/0.14 (14.14.14.4/29)  ← Shows actual interfaces!
    • ge100-18/0/0.24 (24.24.24.4/29)
    • ge100-18/0/0.34 (34.34.34.4/29)
    • ge100-18/0/0.45 (45.45.45.4/29)
  → Map to target (18 LLDP neighbors available)
```

### Step 3: Select Sections
```
INTERFACES [k/K/e/E/d/D/s/S/b/B/t/T] (e): ⏎
```

### Step 4: Edit WAN (NEW EXPERIENCE!)
```
WAN Interfaces [k/K/e/E/s/S/b/B] (e): ⏎

WAN Interface Configuration
  Source: 4 WAN interfaces
    • ge100-18/0/0.14 (14.14.14.4/29)
    • ge100-18/0/0.24 (24.24.24.4/29)
    • ge100-18/0/0.34 (34.34.34.4/29)
    • ge100-18/0/0.45 (45.45.45.4/29)
  Target: 0 WAN interfaces
  Target LLDP: 18 neighbors available

  Quick Options:
    [1] Copy source WANs as-is (4 interfaces) (recommended)
    [2] Map source WANs to target interfaces (using LLDP)
    [S] Skip WAN configuration
  Select [B]ack (1): 1⏎

  ✓ Copy 4 source WAN interfaces
```

### Step 5: Continue with Other Sections
```
Loopback (lo0) [k/K/e/E/s/S/b/B] (e): e

Custom Loopback IP
  Source lo0: 4.4.4.4/32
  Target lo0: N/A
  Suggestions:
    [1] 4.4.4.4/32 (use source)
    [3] 4.4.4.5/32 (next IP)
  Enter loopback IP/mask [B]ack (4.4.4.4/32): 2.2.2.2/32⏎

  ✓ Custom loopback: 2.2.2.2/32
```

**Result:** Fast, intuitive, consistent editing experience! ✅

---

## Testing

```bash
cd /home/dn/SCALER
python3 -m py_compile scaler/wizard/mirror_config.py
# ✅ Exit code: 0 (No errors)
```

**To Test:**
1. Exit current wizard (`Ctrl+C` or Back to top)
2. Restart: `./run.sh`
3. Multi-Device → Mirror Config
4. Select source device
5. Choose INTERFACES → Edit
6. Select WAN → Edit
7. **You'll see the new Quick Options menu!** ✅

---

## Files Modified

**Single File:** `/home/dn/SCALER/scaler/wizard/mirror_config.py`

**Changes:**
1. Line ~8653: Replaced simple WAN edit handler with **Quick WAN Edit** experience
   - Parses source WAN IPs
   - Loads target WAN + LLDP context
   - Shows summary with actual interfaces
   - Offers context-aware quick options
   - Provides instant feedback
   - Still offers full wizard as option [3]

---

## Status

✅ **IMPLEMENTED**

**Next Steps:**
1. **User must restart wizard** to load new code
2. Test the new WAN edit experience
3. Consider applying same pattern to other sub-sections

---

## Design Principles Applied

1. **Progressive Disclosure:** Show quick options first, advanced wizard as option
2. **Context-Aware Defaults:** Recommend based on target state
3. **Immediate Feedback:** Confirm action with ✓ message
4. **Consistency:** Match loopback/hostname editor UX
5. **Visibility:** Show what's changing (interface names, IPs)
6. **Escape Hatches:** Always offer [B]ack and [S]kip

---

*Implementation Date: 2026-01-31*  
*Status: ✅ **ENHANCED WAN EDIT COMPLETE***  
*User Action Required: **RESTART WIZARD** to load changes*
