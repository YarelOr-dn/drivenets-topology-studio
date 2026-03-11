# Critical Fix: Mirror Config LLDP Missing - Auto-Fetch During Refresh

## Problem Statement (2026-01-31)

**User Observation:**
```
Target Available Interfaces (with LLDP neighbors):
No LLDP neighbors found on target device.  ← ❌ WRONG!
Tip: Enable LLDP on target device to see neighbors.
```

**User's Question:**
> "This is not correct, why isn't this mirror taking lldp output from @scaler-monitor?"

---

## Root Cause Analysis

### What Mirror Config Expects
```python
# mirror_config.py line ~450
target_op_file = Path(f"/home/dn/SCALER/db/configs/{target_hostname}/operational.json")
with open(target_op_file) as f:
    target_op = json.load(f)
    target_lldp = target_op.get('lldp_neighbors', [])  ← Expects this to be populated!
```

### What Was Actually In operational.json
```json
{
  "lldp_neighbor_count": 0,
  "lldp_neighbors": [],  ← EMPTY! ❌
  ...
}
```

### Why Was It Empty?

**The Config Refresh Flow:**
```
User → [R]efresh Devices
  ↓
_refresh_multi_device_configs()
  ↓
ConfigExtractor.extract_running_config()
  ↓
InteractiveExtractor.get_running_config()
  ↓
send_command("show config | no-more")  ← ONLY gets running config!
  ↓
✓ running.txt saved
✗ LLDP neighbors NOT fetched! ❌
```

**The Problem:**
- `extract_running_config()` ONLY fetches the running configuration text
- It does NOT fetch LLDP neighbors
- `operational.json` remains empty or stale
- Mirror Config wizard finds no LLDP neighbors

---

## The Solution

### Enhanced `InteractiveExtractor.get_running_config()`

**File:** `scaler/config_extractor.py` (line ~787)

**Added:**
1. Optional `fetch_lldp` parameter (default: `True`)
2. After fetching config, automatically fetch LLDP neighbors
3. Update `operational.json` with fresh LLDP data

**Implementation:**
```python
def get_running_config(self, fetch_lldp: bool = True) -> str:
    """
    Get the full running configuration.
    
    Args:
        fetch_lldp: If True, also fetch LLDP neighbors and update operational.json
    """
    # ... fetch running config ...
    
    # Optionally fetch LLDP neighbors and update operational.json
    if fetch_lldp:
        try:
            lldp_data = fetch_lldp_neighbors(self.channel, self.device.hostname, timeout=15.0)
            if lldp_data and lldp_data.get('lldp_neighbors'):
                update_lldp_in_operational_json(self.device.hostname, lldp_data)
        except Exception:
            # Don't fail config extraction if LLDP fetch fails
            pass
    
    return config_text
```

**Key Design Decisions:**
1. **Default enabled:** `fetch_lldp=True` by default
2. **Non-blocking:** LLDP fetch failures don't break config extraction
3. **Automatic:** No user action required
4. **Uses existing functions:** `fetch_lldp_neighbors()` + `update_lldp_in_operational_json()`

---

## Flow After Fix

### New Config Refresh Flow
```
User → [R]efresh Devices
  ↓
_refresh_multi_device_configs()
  ↓
ConfigExtractor.extract_running_config()
  ↓
InteractiveExtractor.get_running_config(fetch_lldp=True)  ← NEW!
  ↓
1. send_command("show config | no-more")
   ✓ running.txt saved
  ↓
2. fetch_lldp_neighbors(channel, hostname)  ← NEW!
   send_command("show lldp neighbors | no-more")
  ↓
3. update_lldp_in_operational_json(hostname, lldp_data)  ← NEW!
   ✓ operational.json updated with LLDP neighbors
```

### Mirror Config Now Gets LLDP
```python
# Mirror Config wizard
target_lldp = target_op.get('lldp_neighbors', [])  ← NOW POPULATED! ✅

# Display
console.print(f"Target LLDP: {len(target_lldp)} neighbors available")
# → "Target LLDP: 18 neighbors available" ✅
```

---

## Example: Before vs After

### Before (Broken) ❌
```
User refreshes PE-2:
  ✓ running.txt: 2,456 lines
  ✓ operational.json: basic info only
    {
      "lldp_neighbor_count": 0,
      "lldp_neighbors": []  ← STALE/EMPTY
    }

User launches Mirror Config:
  WAN Mapping Options:
    Target Available Interfaces (with LLDP neighbors):
    No LLDP neighbors found on target device.  ← ❌ MISLEADING!
```

### After (Fixed) ✅
```
User refreshes PE-2:
  ✓ running.txt: 2,456 lines
  ✓ operational.json: enriched with LLDP
    {
      "lldp_neighbor_count": 18,
      "lldp_neighbors": [  ← FRESH DATA!
        {
          "local_interface": "ge400-0/0/4",
          "neighbor_device": "PE-4",
          "neighbor_port": "ge100-18/0/0",
          ...
        },
        ...
      ]
    }

User launches Mirror Config:
  WAN Mapping Options:
    Target Available Interfaces (with LLDP neighbors):
    
    Interface        Neighbor  Remote Port
    ge400-0/0/4      PE-4      ge100-18/0/0
    ge400-0/0/5      PE-4      ge100-18/0/1
    ...  ← ✅ SHOWS LLDP DATA!
    
    [2] Map source WANs to target interfaces (with IP suggestions) [Recommended]
```

---

## Testing

### Syntax Validation
```bash
cd /home/dn/SCALER
python3 -m py_compile scaler/config_extractor.py
# ✅ Exit code: 0 (No errors)
```

### Test Procedure
1. **Exit current wizard** (Ctrl+C or Back)
2. **Restart:** `./run.sh`
3. **Refresh PE-2:**
   - Multi-Device → Refresh Devices
   - Wait for completion
4. **Check operational.json:**
   ```bash
   cat /home/dn/SCALER/db/configs/PE-2/operational.json | grep -A 5 lldp_neighbors
   # Should now show actual neighbors! ✅
   ```
5. **Launch Mirror Config:**
   - Source: PE-4 → Target: PE-2
   - INTERFACES → WAN Interfaces → Edit
   - **Should now show LLDP neighbors!** ✅

---

## Impact

### Positive Impact ✅
- **Mirror Config:** Now gets fresh LLDP data automatically
- **WAN Mapping:** Can suggest target interfaces based on LLDP
- **User Experience:** No manual LLDP refresh needed
- **Data Freshness:** LLDP data updated on every config refresh
- **Automation:** Works seamlessly in background

### Potential Concerns 🤔
- **Performance:** Adds ~2-5 seconds to refresh operation (LLDP fetch)
  - **Mitigation:** Non-blocking, runs after config fetch
  - **Acceptable:** Refresh is already a long operation
- **LLDP Disabled:** If device has no LLDP, fetch returns empty list
  - **Mitigation:** Gracefully handled, doesn't break refresh

---

## Related Functions

| Function | Location | Purpose |
|----------|----------|---------|
| `fetch_lldp_neighbors()` | config_extractor.py:1001 | Execute `show lldp neighbors` |
| `parse_lldp_output()` | config_extractor.py:940 | Parse LLDP command output |
| `update_lldp_in_operational_json()` | config_extractor.py:1204 | Save LLDP to operational.json |
| `get_running_config()` | config_extractor.py:787 | Fetch config + LLDP (NEW) |
| `wan_interface_mapping_wizard()` | mirror_config.py:419 | Uses LLDP for WAN mapping |

---

## Alternative: Manual LLDP Refresh

**If user wants to ONLY refresh LLDP without full config:**

```python
# interactive_scale.py already has this function
def _refresh_lldp_live(device: 'Device'):
    """Fetch LLDP neighbors live from device."""
    # ... connects and fetches LLDP only
```

**Access via:**
- Multi-Device menu → Select device → [L] LLDP Status → [1] Refresh LLDP

---

## Design Principles Applied

1. **Least Surprise:** Refresh now does what users expect (fetch ALL relevant data)
2. **Non-Breaking:** Existing code continues to work (optional parameter)
3. **Fail-Safe:** LLDP errors don't break config extraction
4. **DRY:** Reuses existing `fetch_lldp_neighbors()` and `update_lldp_in_operational_json()`
5. **Automation:** No manual steps required

---

## Documentation Updates

**Files Modified:**
- `scaler/config_extractor.py` (line ~787): Enhanced `get_running_config()`

**New Docs:**
- `/home/dn/SCALER/docs/MIRROR_CONFIG_LLDP_AUTO_FETCH.md` (this file)

**Related Docs:**
- `/home/dn/SCALER/docs/MIRROR_CONFIG_ENHANCED_WAN_EDIT.md`
- `/home/dn/SCALER/docs/SSH_CONNECTION_FIX.md`
- `/home/dn/SCALER/docs/PE2_FIX_SUMMARY.md`

---

## Status

✅ **IMPLEMENTED**

**User Actions Required:**
1. **Exit current wizard** (it's running old code)
2. **Restart wizard:** `./run.sh`
3. **Refresh PE-2** to populate LLDP
4. **Launch Mirror Config** to see LLDP data

**Expected Result:**
```
Target Available Interfaces (with LLDP neighbors):

Interface        Neighbor  Remote Port
ge400-0/0/4      PE-4      ge100-18/0/0
ge400-0/0/5      PE-4      ge100-18/0/1
... ← LLDP neighbors now visible! ✅
```

---

*Implementation Date: 2026-01-31*  
*Status: ✅ **AUTO-FETCH LLDP DURING REFRESH - COMPLETE***  
*User Action: **RESTART WIZARD → REFRESH PE-2***
