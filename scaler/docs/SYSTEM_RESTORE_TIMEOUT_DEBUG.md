# System Restore Timeout Troubleshooting

## Issue: "Timeout waiting for GI mode"

### Root Causes

#### 1. Console Reconnection Failed
**Symptom:**
```
[16:35:20] ✓ Restore command sent
[16:35:22] ⏳ Waiting for GI mode (device rebooting)...
[16:35:40] Monitoring console for GI mode...
[16:35:42] ✗ Console reconnect failed: [error]
```

**Fix:** Check console-b15 connectivity
```bash
ssh dn@console-b15
# Should work without errors
```

**Solution in code:** Now fails immediately with clear error message

---

#### 2. Device Still Booting (Normal)
**Symptom:**
```
[16:48:14] ⏳ Waiting for GI prompt... (9m 59s)
[16:48:36] ⏳ Waiting for GI prompt... (10m 21s)
[16:49:58] ⏳ Waiting for GI prompt... (11m 43s)
```

**Expected:** PE-2 can take 10-15 minutes to reach GI mode after factory reset

**Solution:** Increase timeout or wait patiently

---

#### 3. GI Prompt Not Detected
**Symptom:**
```
[16:52:00] >> some console output here
[16:52:22] >> more console output here
[16:53:00] ✗ Timeout waiting for GI mode
```

**Cause:** Console is connected, receiving output, but not recognizing GI prompt

**Patterns we detect:**
- `GI#` - Main GI prompt
- `GI(` - GI with context
- `gicli` - GI CLI mention
- `gi mode` - Text mention

**Fix:** Check what prompt PE-2 actually shows in GI mode

---

#### 4. Console Channel Lost
**Symptom:**
```
[16:40:15] ✓ Reconnected to console
[16:42:20] ⏳ Console check: 'NoneType' object (10m 5s)
[16:44:42] ⏳ Console check: timeout (12m 27s)
```

**Cause:** Paramiko channel disconnected or timed out

**Solution in new code:**
- Set `console_channel.settimeout(30)`
- Better exception handling
- Show actual error messages

---

## Enhanced Debug Output

### What You'll See Now:

**Before (not helpful):**
```
[16:48:14] ⏳ Booting... (9m 59s)
[16:48:36] ⏳ Booting... (10m 21s)
```

**After (shows actual console output):**
```
[16:48:14] >> Starting DNOS services...
[16:48:15] >> Loading kernel modules...
[16:48:16] ⏳ Waiting for GI prompt... (9m 59s)
[16:48:38] >> Checking network interfaces...
[16:48:39] >> System ready
[16:48:40] >> GI#                              <- This triggers success!
[16:48:41] ✓ GI mode reached after 10m 25s
```

---

## Manual Verification

If timeout occurs, **manually check** PE-2 console:

```bash
# Connect to console
ssh dn@console-b15

# Select port access
[Main Menu]
Selection: 3

# Select PE-2
Port: 13

# Login
Username: dnroot
Password: dnroot

# Check prompt - should see:
GI#  ← This is what we're looking for!
```

**If you see `GI#`:**
- Device IS in GI mode
- Wizard detection failed
- Report the exact prompt pattern to developer

**If you see boot messages:**
- Device still booting
- Wizard should continue waiting
- Check if boot is stuck

**If you see `dnRouter(RECOVERY)#`:**
- Factory reset didn't trigger
- Need to run manually:
  ```
  request system restore factory-default
  yes
  ```

---

## Testing the Enhanced Version

### Run It:
```bash
# Exit current wizard
# Restart to load new code
scaler-wizard
```

### What to Look For:

1. **Console connection messages:**
   ```
   PE-2 in recovery - connecting via console...
   Connecting to console-b15...
   Connected to console server
   Selecting port 13 (PE-2)...
   ✓ Connected to PE-2 via console
   ```

2. **Restore execution:**
   ```
   ✓ RECOVERY mode confirmed
   Executing: request system restore factory-default
   ✓ Restore command sent
   ```

3. **Console reconnection:**
   ```
   Monitoring console for GI mode...
   Reconnecting to console server...
   Navigating to PE-2 console port...
   ✓ Reconnected to console
   ```

4. **Polling with debug output:**
   ```
   >> [actual console output line 1]
   >> [actual console output line 2]
   ⏳ Waiting for GI prompt... (Xm Ys)
   ```

5. **Success detection:**
   ```
   >> GI#
   ✓ GI mode reached after Xm Ys
   Reading mgmt0 IP address...
   ✓ New mgmt0 IP: 100.64.8.XX
   ```

---

## Key Improvements in New Version

| Issue | Before | After |
|-------|--------|-------|
| **Console reconnect fails** | Continues anyway → timeout | Fails immediately with error |
| **No visibility** | "Booting..." forever | Shows actual console output |
| **Timeout too short** | 900s (15 min) | Still 15 min but better progress |
| **GI detection** | Only `GI` text | Multiple patterns (GI#, gicli, etc) |
| **Channel errors** | Silent failure | Shows exception in output |

---

## If It Still Times Out

**Collect this info:**

1. **Was console reconnection successful?**
   - Look for "✓ Reconnected to console"

2. **What console output did you see?**
   - Look for `>> ...` lines

3. **How long did it take?**
   - Check elapsed time

4. **Manual console check:**
   - What prompt do you see?
   - Is device in GI mode?

**Report to developer with:**
- Full terminal output
- Exact console prompt from manual check
- Time elapsed

---

**Status:** ✅ Enhanced with better debugging  
**Date:** 2026-01-27  
**Next:** Test with real PE-2 restore operation
