# SSH Connection Fix for PE-2 and Other Devices

## Problem Summary

**Issue:** PE-2 (and potentially other devices) failed to refresh config with error:
```
SSH failed. Console: reachable, not recovery
```

**Root Cause:** ConfigExtractor and other SSH-based operations were using the IP from `devices.json` instead of the discovered mgmt IP stored in `operational.json`.

---

## The Issue in Detail

### Device IP vs Mgmt IP

Devices in SCALER have **two potential IPs**:

1. **`devices.json` IP** (`device.ip`)
   - Original IP entered when device was added
   - Could be:
     - Console IP
     - Old/incorrect mgmt IP
     - Hostname that needs resolution
   - **May become stale or unreachable**

2. **`operational.json` mgmt IP** (`mgmt_ip` or `ssh_host`)
   - Discovered during successful connections
   - **Current, working mgmt IP**
   - Actively maintained by SCALER operations
   - **Should be preferred for SSH**

### Example: PE-2

```json
// devices.json
{
  "ip": "100.64.8.39"  ← ❌ Unreachable (auth fails)
}

// operational.json
{
  "mgmt_ip": "100.64.4.205",  ← ✅ Works perfectly
  "ssh_host": "100.64.4.205"
}
```

### What Was Happening

**Before Fix:**
```python
# config_extractor.py, line 682
self.client.connect(
    hostname=self.device.ip,  # ← Always used devices.json IP
    ...
)
```

**Result:**
1. ConfigExtractor tries `100.64.8.39` → **Auth fails**
2. Falls back to console check → Console OK, not in recovery
3. Reports: "SSH failed. Console: reachable, not recovery"
4. **Never tries the working mgmt IP `100.64.4.205`**

---

## The Solution

### New Helper Function: `get_ssh_hostname()`

Created in `scaler/utils.py`:

```python
def get_ssh_hostname(device, fallback_to_device_ip: bool = True) -> str:
    """Get the best SSH hostname/IP for a device.
    
    Prefers mgmt IP from operational.json over devices.json IP.
    """
    # Try operational.json first
    ops_file = get_device_config_dir(device.hostname) / "operational.json"
    if ops_file.exists():
        ops_data = json.load(open(ops_file))
        mgmt_ip = ops_data.get("mgmt_ip") or ops_data.get("ssh_host")
        if mgmt_ip and mgmt_ip != "N/A":
            return mgmt_ip  # ✓ Use discovered mgmt IP
    
    # Fall back to devices.json IP
    return device.ip
```

### Priority Logic

```
1. Try operational.json → mgmt_ip     (highest priority)
2. Try operational.json → ssh_host
3. Fall back to devices.json → ip     (lowest priority)
```

---

## Files Modified

### 1. `scaler/utils.py`

**Added:**
- `get_ssh_hostname(device)` - Helper to get best SSH IP

**Location:** Line ~103

### 2. `scaler/config_extractor.py`

**Modified:**
- `ConfigExtractor.connect_to_device()` (line ~49)
- `InteractiveExtractor.connect()` (line ~676)

**Changed from:**
```python
client.connect(hostname=device.ip, ...)
```

**Changed to:**
```python
from .utils import get_ssh_hostname
hostname = get_ssh_hostname(device)
client.connect(hostname=hostname, ...)
```

---

## Testing

### Manual Test

```bash
cd /home/dn/SCALER

# Test the new helper function
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from scaler.models import Device
from scaler.utils import get_ssh_hostname

pe2 = Device(
    id='pe2',
    hostname='PE-2',
    ip='100.64.8.39',  # Old/wrong IP
    username='dnroot',
    password='ZG5yb290',
    platform='NCP'
)

hostname = get_ssh_hostname(pe2)
print(f"devices.json IP: {pe2.ip}")
print(f"Best SSH IP: {hostname}")
print(f"Expected: 100.64.4.205")
EOF
```

**Expected Output:**
```
devices.json IP: 100.64.8.39
Best SSH IP: 100.64.4.205
Expected: 100.64.4.205
```

### Full Connection Test

```bash
cd /home/dn/SCALER

python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from scaler.models import Device
from scaler.config_extractor import InteractiveExtractor

pe2 = Device(
    id='pe2',
    hostname='PE-2',
    ip='100.64.8.39',
    username='dnroot',
    password='ZG5yb290',
    platform='NCP'
)

print("Testing InteractiveExtractor with new logic...")
with InteractiveExtractor(pe2, timeout=10) as extractor:
    print("✓ Connected successfully!")
    config = extractor.get_running_config()
    print(f"✓ Retrieved config: {len(config)} bytes")
    if 'config-start' in config:
        print("✓ Config has valid markers")
EOF
```

**Expected Output:**
```
Testing InteractiveExtractor with new logic...
✓ Connected successfully!
✓ Retrieved config: 5187 bytes
✓ Config has valid markers
```

---

## Impact on Other Modules

### Modules Still Using `device.ip` Directly

Found 10 occurrences in:
- `scaler/config_pusher.py` (8 locations)
- `scaler/interactive_scale.py` (1 location)

### Should These Be Updated?

**Yes, for consistency**, but with **lower priority** because:

1. **ConfigExtractor is the critical path** for refresh operations ✅ **FIXED**
2. `config_pusher.py` operations:
   - Often have user supervision
   - May use console fallback
   - User can intervene if SSH fails
3. Most push operations happen **after** a successful refresh, which discovers mgmt IP

### Recommended Next Steps

1. **Test PE-2 refresh now** ✅ **Should work**
2. Monitor other devices for similar issues
3. **Phase 2:** Update `config_pusher.py` to use `get_ssh_hostname()`
4. **Phase 3:** Update `interactive_scale.py` SSH connections

---

## Verification Checklist

After this fix:

- [ ] PE-2 refresh works without errors
- [ ] ConfigExtractor uses mgmt IP (100.64.4.205)
- [ ] Fallback to devices.json IP still works for devices without operational.json
- [ ] No regression for other devices (PE-1, PE-4, eCdnos-RR)

---

## Future Improvements

### 1. Auto-Update devices.json

When mgmt IP is discovered, update `devices.json`:

```python
if hostname != device.ip:
    # Update devices.json with working mgmt IP
    update_device_ip(device.id, hostname)
```

### 2. Better Error Messages

Distinguish between:
- ❌ "SSH failed: Connection refused" (port/firewall)
- ❌ "SSH failed: Auth denied" (wrong credentials/IP)
- ❌ "SSH OK, but DNOS CLI not running" (service down)

### 3. Parallel IP Attempts

Try multiple IPs in parallel:
```python
ips_to_try = [
    get_ssh_hostname(device),  # mgmt IP
    device.ip,                 # devices.json IP
]
# Try all, use first success
```

### 4. Discovery via Console

If SSH fails, try console to discover mgmt IP:
```bash
show system management-ethernet
```

---

## Related Files

| File | Purpose | Modified |
|------|---------|----------|
| `scaler/utils.py` | Helper functions | ✅ Added `get_ssh_hostname()` |
| `scaler/config_extractor.py` | Config extraction | ✅ Updated 2 connect() methods |
| `scaler/config_pusher.py` | Config push operations | ⏳ TODO (8 locations) |
| `scaler/interactive_scale.py` | Main wizard | ⏳ TODO (1 location) |
| `db/devices.json` | Device registry | No change |
| `db/configs/PE-2/operational.json` | Runtime device data | No change |

---

## Summary

**Problem:** SSH to PE-2 failed because ConfigExtractor used stale IP from `devices.json` instead of working mgmt IP from `operational.json`.

**Solution:** Created `get_ssh_hostname()` helper that **prefers operational mgmt IP** over devices.json IP.

**Result:** PE-2 refresh should now work correctly using the discovered mgmt IP (100.64.4.205).

**Next:** Test PE-2 refresh to verify fix, then optionally update config_pusher.py for consistency.

---

*Fix Date: 2026-01-30*  
*Issue: PE-2 SSH connection failure during refresh*  
*Root Cause: Wrong IP preference (devices.json over operational.json)*
