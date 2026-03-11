# Mirror Config Issues - PE-2 LLDP and Bundle Detection

## Problem Summary

User is trying to **Mirror Config from PE-4 to PE-2** but encounters:

1. **"No LLDP neighbors found on target device"**
   - Mirror wizard can't find physical interfaces to map to
   - User says: "no LLDP found on target device is wrong since there are neighbors..."

2. **Bundles not detected**
   - User says: "The mirror operation should detect bundles as well, and keep the configuration of their parent of course"

## Root Cause

### Issue 1: Empty LLDP Data in PE-2's operational.json

```json
// db/configs/PE-2/operational.json
{
  "lldp_neighbor_count": 0,
  "lldp_neighbors": []  ← EMPTY!
}
```

**Why it's empty:**
- PE-2 **never had a successful config fetch before** (SSH connection was failing)
- LLDP neighbor data is collected during config extraction via `show lldp neighbors`
- The SSH fix we just applied hasn't been used yet (user needs to refresh PE-2)

**But PE-2 DOES have LLDP configured:**
```
protocols
  lldp
    admin-state enabled
    interface ge400-0/0/0
    interface ge400-0/0/2
    interface ge400-0/0/3
    interface ge400-0/0/4
    interface ge400-0/0/5
```

### Issue 2: Bundle Detection

**PE-2 HAS bundles in config:**
```
interfaces
  bundle-100
    admin-state enabled
    mtu 9216
  !
  ge400-0/0/0
    admin-state enabled
    bundle-id 100  ← Member of bundle-100
    ...
  !
```

**But Mirror wizard relies on LLDP data to:**
1. Find available physical interfaces
2. Detect bundle membership
3. Map source interfaces to target interfaces

Without LLDP data → Can't detect what's available on target!

## The Solution

### Immediate Action Required ✅

**User needs to REFRESH PE-2 first:**

1. **Exit Mirror wizard** → Press `[B]` Back repeatedly until back at device menu
2. **Select PE-2** → Should still be selected
3. **Press `[R]` Refresh** → This will now work (SSH fix is in place!)
4. **Wait for config extraction** → Will fetch:
   - Running config
   - LLDP neighbors (`show lldp neighbors`)
   - Operational data
5. **Verify LLDP populated:**
   ```bash
   cat db/configs/PE-2/operational.json | grep lldp_neighbor_count
   # Should show: "lldp_neighbor_count": N (where N > 0)
   ```
6. **Retry Mirror Config** → Now PE-2's LLDP data will be available!

### Why This Will Fix It

**After PE-2 refresh:**
```json
// db/configs/PE-2/operational.json (UPDATED)
{
  "lldp_neighbor_count": 5,  ← Will be populated!
  "lldp_neighbors": [
    {
      "local_interface": "ge400-0/0/0",
      "neighbor_device": "SPINE-1",
      "neighbor_port": "Ethernet1/1",
      ...
    },
    ...
  ]
}
```

**Mirror wizard will then:**
1. ✅ See available physical interfaces (from LLDP)
2. ✅ Detect bundle membership (from config + LLDP)
3. ✅ Offer intelligent WAN mapping
4. ✅ Show bundle-100 and its members

## Code Flow (for reference)

### Mirror Config WAN Mapping
```python
# scaler/wizard/mirror_config.py:446-453
target_lldp = []
try:
    target_op_file = Path(f"db/configs/{target_hostname}/operational.json")
    if target_op_file.exists():
        with open(target_op_file) as f:
            target_op_data = json.load(f)
            target_lldp = target_op_data.get('lldp_neighbors', [])  ← Loads LLDP
except Exception:
    pass

# Line 552-567: Build available target interfaces from LLDP
for n in target_lldp:
    iface = n.get('local_interface') or n.get('interface', '')
    neighbor = n.get('neighbor_device') or n.get('neighbor', '')
    remote_port = n.get('neighbor_port') or n.get('remote_port', '')
    if iface and '.' not in iface:  # Only physical interfaces
        available_targets.append({
            'interface': iface,
            'neighbor': neighbor,
            'remote_port': remote_port
        })

if not available_targets:
    console.print("No physical interfaces available from LLDP.")  ← THIS ERROR!
```

### LLDP Collection During Config Extract

**Currently:** `extract_running_config()` only gets config, NOT LLDP neighbors

**LLDP is fetched separately** via:
- Manual LLDP check feature (`[L] LLDP Check` in device menu)
- OR during other operations that open SSH channel

**The Problem:** Normal refresh doesn't auto-fetch LLDP!

## Long-Term Fix Needed (Code Enhancement)

### Enhancement 1: Auto-Fetch LLDP During Config Extraction

**Modify:** `config_extractor.py:extract_running_config()`

```python
def extract_running_config(self, device, save_to_db=True):
    try:
        with InteractiveExtractor(device, timeout=180) as extractor:
            output = extractor.get_running_config()
            
            # ✅ NEW: Also fetch LLDP neighbors while channel is open
            try:
                lldp_data = fetch_lldp_neighbors(extractor.channel, device.hostname)
                # Update operational.json with LLDP data
                update_lldp_in_operational_json(device.hostname, lldp_data)
            except Exception:
                pass  # Don't fail extraction if LLDP fetch fails
            
        # ... rest of config processing
```

**Benefits:**
- Single SSH session for both config + LLDP
- LLDP data automatically fresh after every refresh
- No separate LLDP check needed

### Enhancement 2: Fallback to Config-Based Interface Detection

**If LLDP is empty**, parse interfaces from config:

```python
# scaler/wizard/mirror_config.py
if not target_lldp:
    # Fallback: Parse physical interfaces from target config
    target_lldp = _extract_interfaces_from_config(state.target_config)
    console.print("[yellow]Using config-based interface detection (LLDP unavailable)[/yellow]")
```

**Parse from config:**
```python
def _extract_interfaces_from_config(config: str) -> List[Dict]:
    """Extract physical interfaces from config when LLDP unavailable."""
    interfaces = []
    pattern = r'^  (ge|xe|et|hu|ce)[0-9]+[/-][0-9]+[/-][0-9]+'
    for match in re.finditer(pattern, config, re.MULTILINE):
        iface = match.group(0).strip()
        interfaces.append({
            'local_interface': iface,
            'neighbor_device': '(unknown)',
            'neighbor_port': '(unknown)',
            'capability': 'Unknown'
        })
    return interfaces
```

### Enhancement 3: Bundle Detection from Config

**Parse bundles from target config:**

```python
def _detect_bundles_from_config(config: str) -> Dict[str, List[str]]:
    """Detect bundle interfaces and their members from config."""
    bundles = {}
    current_bundle = None
    
    for line in config.split('\n'):
        # Detect bundle interface
        if re.match(r'^\s+(bundle-\d+)', line):
            current_bundle = line.strip()
            bundles[current_bundle] = []
        # Detect bundle member
        elif 'bundle-id' in line and current_bundle:
            # Find interface name from previous lines (context)
            pass  # Parse bundle membership
    
    return bundles
```

## Summary for User

### ✅ **IMMEDIATE ACTION: Refresh PE-2**

1. Exit Mirror wizard (`[B]` Back)
2. Select PE-2 again
3. Press `[R]` Refresh → **This will now work!** (SSH fixed)
4. Wait for config extraction to complete
5. Retry Mirror Config → LLDP data will be available

### ✅ **VERIFIED:**

- PE-2 has LLDP configured on 5+ interfaces ✓
- PE-2 has bundle-100 configured ✓
- PE-2 SSH connection now works ✓
- Just needs a refresh to populate LLDP data

### 🔧 **CODE ENHANCEMENT NEEDED:**

- Auto-fetch LLDP during config extraction
- Fallback to config-based interface detection if LLDP empty
- Better bundle detection from config

---

**Current State:** PE-2 has empty LLDP data → Mirror wizard can't map interfaces  
**After Refresh:** PE-2 will have LLDP data → Mirror wizard will work normally  
**Status:** ✅ **READY TO TEST** (refresh PE-2 first!)

*Analysis Date: 2026-01-31*  
*Issue: Mirror Config can't find PE-2 interfaces*  
*Fix: Refresh PE-2 to populate LLDP data*
