# DNAAS Discovery - Credential & Styling Issues

## Problem Analysis

### Issue 1: DNAAS Device Credentials Missing ❌

**Current State:**
- PE devices (PE-1, PE-4) are in scaler-monitor → Have cached LLDP data ✅
- DNAAS fabric devices (DNAAS-LEAF-D16, DNAAS-SPINE-X) are NOT monitored → No cached data ❌
- Hybrid script needs to SSH to DNAAS devices → **Needs credentials!**

**Current credential storage:**
```javascript
// In topology.js, devices store SSH config
device.sshConfig = {
    host: "100.64.0.220",
    user: "dnroot", 
    password: "dnroot"
}
```

**Problem:**
When you add a DNAAS device to topology (e.g., DNAAS-LEAF-D16), its SSH config is stored in the topology. But the hybrid discovery script doesn't know about it!

### Issue 2: DNAAS Panel Styling 🎨

Current DNAAS panel has basic liquid glass but needs enhancement to match LLDP table quality.

## Solutions

### Solution 1A: Use Device Inventory File (Recommended)

**Create:** `/home/dn/CURSOR/device_credentials.json`

```json
{
  "PE-1": {
    "hostname": "PE-1",
    "mgmt_ip": "100.64.0.210",
    "user": "dnroot",
    "password": "dnroot",
    "device_type": "PE"
  },
  "PE-4": {
    "hostname": "PE-4",
    "mgmt_ip": "100.64.0.240",
    "user": "dnroot",
    "password": "dnroot",
    "device_type": "PE"
  },
  "DNAAS-LEAF-D16": {
    "hostname": "DNAAS-LEAF-D16",
    "mgmt_ip": "<ASK_USER_FOR_IP>",
    "user": "sisaev",
    "password": "Drive1234!",
    "device_type": "DNAAS-LEAF"
  },
  "DNAAS-SPINE-X": {
    "hostname": "DNAAS-SPINE-X",
    "mgmt_ip": "<ASK_USER_FOR_IP>",
    "user": "sisaev",
    "password": "Drive1234!",
    "device_type": "DNAAS-SPINE"
  }
}
```

**Then update `dnaas_discovery_hybrid.py` to read this file.**

### Solution 1B: Export from Topology Canvas (Smart!)

**Add button:** "Export Device Credentials" in topology
- Scans all devices on canvas
- Exports their `sshConfig` to `device_credentials.json`
- Discovery script reads this file

**Pros:**
✅ User-friendly - no manual JSON editing
✅ Auto-updates when devices are added
✅ One-click export

### Solution 2: Enhanced DNAAS Panel Styling

Update `/home/dn/CURSOR/index.html` DNAAS panel section with:

**Enhanced Features:**
- Better transparency & blur
- Animated gradient borders
- Smooth transitions
- Status indicator improvements
- Better output terminal styling

## Implementation Priority

### High Priority (Blocking Discovery):
1. **Get DNAAS device credentials from user:**
   - What are the management IPs for DNAAS-LEAF-D16, DNAAS-SPINE-X, etc.?
   - Confirm credentials: `sisaev` / `Drive1234!`

2. **Create device_credentials.json** with all devices

3. **Update hybrid script** to read credentials from file

### Medium Priority (UX):
4. Add "Export Credentials" button to topology
5. Auto-generate device_credentials.json from canvas

### Low Priority (Polish):
6. Enhance DNAAS panel styling to match LLDP table

## Questions for User

To fix the discovery, I need:

1. **DNAAS Device List:**
   - What DNAAS fabric devices exist? (LEAF, SPINE names)
   - What are their management IPs?

2. **Credentials:**
   - Confirm DNAAS credentials: `sisaev` / `Drive1234!` ?
   - Are PE credentials: `dnroot` / `dnroot` ?

3. **Alternative:**
   - Should I add an "Export Credentials" button to topology UI?
   - This would let you add devices to canvas with SSH info, then export to JSON

## Temporary Workaround

**For now, you can manually create:**

`/home/dn/CURSOR/device_credentials.json`

```json
{
  "DNAAS-LEAF-D16": {
    "hostname": "DNAAS-LEAF-D16",
    "mgmt_ip": "192.168.1.100",  ← UPDATE THIS
    "user": "sisaev",
    "password": "Drive1234!",
    "device_type": "DNAAS"
  }
}
```

Then run:
```bash
cd /home/dn/CURSOR
python3 dnaas_discovery_hybrid.py PE-1 PE-4
```

---

**Key Insight:** The hybrid discovery can't SSH to DNAAS devices without credentials. We need either:
- A) Manual device_credentials.json file
- B) Export button from topology canvas
- C) Add DNAAS devices to scaler-monitor (your original suggestion)

Which approach do you prefer? 🤔
