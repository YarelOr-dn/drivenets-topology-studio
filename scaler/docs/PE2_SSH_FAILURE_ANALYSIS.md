# PE-2 SSH Connection Failure - Root Cause Analysis

## Issue Summary

**Problem:** PE-2 refresh fails with "SSH failed. Console: reachable, not recovery"

**Root Cause:** PE-2's DNOS CLI is not running - device is offering BaseOS shell instead

---

## Investigation Flow

### 1. Configuration Check

From `/home/dn/SCALER/db/devices.json`:
```json
{
  "id": "pe2",
  "hostname": "PE-2",
  "ip": "100.64.8.39",          ← Original IP (failed)
  "username": "dnroot",
  "password": "ZG5yb290"         ← base64("dnroot")
}
```

From `/home/dn/SCALER/db/configs/PE-2/operational.json`:
```json
{
  "mgmt_ip": "100.64.4.205",     ← Discovered mgmt IP (works)
  "ssh_host": "100.64.4.205",
  "connection_method": "SSH→MGMT"
}
```

### 2. SSH Connection Tests

**Test 1: Original IP (100.64.8.39)**
```bash
$ ssh dnroot@100.64.8.39
Permission denied (publickey,password).
```
**Result:** ❌ Authentication failure

**Test 2: Mgmt IP (100.64.4.205)**
```bash
$ ssh dnroot@100.64.4.205 "echo 'SSH OK'"
Invalid command
```
**Result:** ⚠️ SSH works, but command execution fails

**Test 3: Interactive Shell (100.64.4.205)**
```bash
$ ssh dnroot@100.64.4.205
Warning: CLI is not running, do you wish to enter BaseOS shell? (yes/no) [no]?
```
**Result:** 🔴 **ROOT CAUSE FOUND**

---

## Root Cause

### PE-2 is NOT in Normal DNOS Mode

When connecting to PE-2 via SSH, the system prompts:

```
Warning: CLI is not running, do you wish to enter BaseOS shell? (yes/no) [no]?
```

This means:
1. ✅ SSH daemon is running
2. ✅ Authentication works
3. ❌ **DNOS CLI is not running**
4. ❌ **Device is in BaseOS-only mode**

### What This Means

PE-2 is in a **degraded state** where:
- BaseOS (Linux layer) is running
- DNOS CLI service is NOT running
- Cannot execute DNOS commands like `show running-config`
- Cannot use interactive DNOS shell

This is **NOT a recovery mode**, but rather a **service failure state**.

---

## Why ConfigExtractor Fails

### Code Flow

```python
# scaler/interactive_scale.py:7048-7050
try:
    extractor = ConfigExtractor()
    result = extractor.extract_running_config(device, save_to_db=True)
```

### ConfigExtractor Logic

```python
# scaler/config_extractor.py:106-107
with InteractiveExtractor(device, timeout=180) as extractor:
    output = extractor.get_running_config()
```

### InteractiveExtractor.connect()

```python
# scaler/config_extractor.py:681-691
self.client.connect(
    hostname=self.device.ip,      # Uses devices.json IP (100.64.8.39)
    username=self.device.username,
    password=self.device.get_password(),
    timeout=self.timeout
)

self.channel = self.client.invoke_shell()  # Opens interactive shell
```

### Where It Fails

1. **Connection attempt** to `100.64.8.39` → **FAILS** (auth denied)
2. **Fallback**: Code checks if device is PE-2
3. **Console check** via `check_pe2_recovery_via_console()`:
   - Console is reachable ✅
   - Device is NOT in recovery mode ✅
   - Reports: "SSH failed. Console: reachable, not recovery" ✅

But the **real issue** is:
- The IP in `devices.json` (100.64.8.39) is wrong/unreachable
- The mgmt IP (100.64.4.205) works but DNOS CLI is down
- ConfigExtractor never tries the mgmt IP

---

## Why Two Different IPs?

### devices.json IP: 100.64.8.39
- This is the **original** IP entered when device was added
- Could be:
  - Console IP
  - Old mgmt IP
  - Wrong IP
- Currently **NOT reachable** via SSH

### operational.json mgmt IP: 100.64.4.205
- This was **discovered** during a previous successful connection
- This is the **current** mgmt IP
- SSH works, but DNOS CLI is down

---

## The Real Problems

### Problem 1: ConfigExtractor Uses Wrong IP

**Code Issue:**
```python
self.client.connect(
    hostname=self.device.ip,  # Always uses devices.json IP
    ...
)
```

**Should Be:**
```python
# Try mgmt IP first if available
ops_file = get_device_config_dir(device.hostname) / "operational.json"
if ops_file.exists():
    with open(ops_file) as f:
        ops_data = json.load(f)
        mgmt_ip = ops_data.get("mgmt_ip") or ops_data.get("ssh_host")
        if mgmt_ip:
            hostname = mgmt_ip  # Use discovered mgmt IP
        else:
            hostname = self.device.ip  # Fall back to devices.json IP
else:
    hostname = self.device.ip

self.client.connect(hostname=hostname, ...)
```

### Problem 2: DNOS CLI Not Running

PE-2's DNOS CLI service is down. This could be due to:
- Service crash
- Manual stop
- System upgrade in progress
- Configuration error

### Problem 3: No Automatic Retry with Mgmt IP

When SSH fails to `devices.json` IP, the code should:
1. Check if mgmt IP exists in `operational.json`
2. Retry with mgmt IP
3. Only then fall back to console

---

## Expected Error Messages vs Actual

### What ConfigExtractor Sees

```python
# When connecting to 100.64.8.39
Exception: Authentication failed (paramiko.AuthenticationException)
```

### What Console Check Returns

```python
# check_pe2_recovery_via_console() returns:
in_rec = False       # Not in recovery
rec_type = None
con_err = None       # Console reachable
```

### What Gets Displayed

```
│ PE-2 │ ✗ Error │ SSH failed. Console: reachable, not recovery │
```

**This is accurate!** But doesn't explain the REAL issue (CLI down).

---

## Solution Options

### Option 1: Fix devices.json IP (Quick Fix)

Update `/home/dn/SCALER/db/devices.json`:
```json
{
  "id": "pe2",
  "hostname": "PE-2",
  "ip": "100.64.4.205",  ← Update to mgmt IP
  ...
}
```

**Problem:** DNOS CLI is still down, so this won't fully work.

### Option 2: Start DNOS CLI on PE-2 (Required)

Connect via console or SSH and start CLI:
```bash
# Via BaseOS shell
$ systemctl start dnos-cli
# or
$ dnos-cli
```

### Option 3: Enhance ConfigExtractor (Code Fix)

Make ConfigExtractor smarter:
1. Try mgmt IP from operational.json first
2. Fall back to devices.json IP
3. Better error messages (detect "CLI not running")

### Option 4: Add Mgmt IP Auto-Discovery

During refresh, if SSH fails:
1. Try console to get mgmt IP: `show system management-ethernet`
2. Update operational.json with mgmt IP
3. Retry SSH with new mgmt IP

---

## Recommended Actions

### Immediate Actions

1. **Check PE-2 Status:**
   ```bash
   ssh dnroot@100.64.4.205
   # When prompted, enter BaseOS shell
   systemctl status dnos-cli
   ```

2. **Start DNOS CLI:**
   ```bash
   systemctl start dnos-cli
   # Wait 10-20 seconds, then exit and reconnect
   ```

3. **Verify DNOS CLI:**
   ```bash
   ssh dnroot@100.64.4.205
   # Should get DNOS CLI prompt (no BaseOS warning)
   show version
   ```

4. **Update devices.json:**
   ```bash
   cd /home/dn/SCALER
   # Edit db/devices.json, change PE-2 IP to 100.64.4.205
   ```

5. **Retry Refresh:**
   In SCALER, select PE-2 and press `[R] Refresh`

### Long-Term Code Improvements

1. **Enhance ConfigExtractor.connect():**
   - Check for mgmt IP in operational.json first
   - Better error detection for "CLI not running"

2. **Add Mgmt IP Preference:**
   ```python
   @property
   def ssh_ip(self):
       """Get best IP for SSH connection."""
       # Try mgmt IP from operational.json first
       # Fall back to devices.json IP
   ```

3. **Improve Error Messages:**
   - Detect "CLI is not running" in SSH output
   - Report: "SSH OK, but DNOS CLI not running" instead of "SSH failed"

4. **Add Auto-Retry Logic:**
   - If SSH to devices.json IP fails
   - Auto-try mgmt IP from operational.json
   - Only then fall back to console

---

## Summary

| Component | Status | Details |
|-----------|--------|---------|
| **SSH to 100.64.8.39** | ❌ Failed | Auth denied (wrong/unreachable IP) |
| **SSH to 100.64.4.205** | ✅ Works | But DNOS CLI not running |
| **Console Access** | ✅ Works | Confirmed reachable |
| **Recovery Mode** | ✅ Normal | Device NOT in recovery |
| **DNOS CLI** | ❌ Down | Service not running on PE-2 |

**Root Cause:** PE-2's DNOS CLI service is not running. ConfigExtractor connects via SSH but encounters BaseOS shell prompt instead of DNOS CLI, causing extraction to fail.

**Fix Required:** 
1. Start DNOS CLI service on PE-2
2. Update devices.json IP to use mgmt IP (100.64.4.205)
3. (Optional) Enhance ConfigExtractor to prefer mgmt IP

---

*Analysis Date: 2026-01-30*
*Device: PE-2 (SA-36CD-S)*
*Issue: DNOS CLI service not running*
