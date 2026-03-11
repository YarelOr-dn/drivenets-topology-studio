# Automatic Mitigation Prompts - Quick Reference

## Overview

**SCALER Monitor** now automatically offers to fix detected device issues with **one-click mitigation prompts**.

---

## How It Works

```
Run: scaler-monitor
     ↓
Detects device states
     ↓
Shows comprehensive summary
     ↓
Groups devices by state type
     ↓
Prompts for each group:
  • ONIE Rescue → "Launch System Restore? [Y/n]"
  • BaseOS Shell → "Launch System Restore? [Y/n]"
  • DN_RECOVERY → "Launch System Restore? [Y/n]"
  • GI Mode → "Launch Image Upgrade? [Y/n]"
  • Standalone → Info only (manual)
     ↓
User presses Enter or 'y'
     ↓
Wizard launches automatically
     ↓
Automated workflow executes
```

---

## Prompt Types

### 1. ONIE Rescue Mode

```
────────────────────────────────────────────────────────────────────────────────
🔧 AUTOMATIC MITIGATION AVAILABLE
────────────────────────────────────────────────────────────────────────────────

ONIE Rescue Mode Detected (1 device(s)):
  • PE-2 - Requires BaseOS installation

Mitigation: System Restore wizard (installs BaseOS → GI → DNOS)

Launch System Restore for these devices? [Y/n]: █
```

**What Happens:**
- Press Enter → System Restore wizard launches
- Wizard connects via console
- Automatically installs BaseOS
- Runs `dncli` to enter GI
- Deploys DNOS
- **All automated!**

---

### 2. BaseOS Shell Mode

```
────────────────────────────────────────────────────────────────────────────────
🔧 AUTOMATIC MITIGATION AVAILABLE
────────────────────────────────────────────────────────────────────────────────

BaseOS Shell Mode Detected (1 device(s)):
  • PE-2 - Needs 'dncli' to enter GI

Mitigation: System Restore wizard (runs dncli → GI → DNOS)

Launch System Restore for these devices? [Y/n]: █
```

**What Happens:**
- Press Enter → System Restore wizard launches
- Wizard connects via console
- Automatically runs `dncli`
- Enters GI mode
- Deploys DNOS
- **No manual console access needed!**

---

### 3. DN_RECOVERY Mode

```
────────────────────────────────────────────────────────────────────────────────
🔧 AUTOMATIC MITIGATION AVAILABLE
────────────────────────────────────────────────────────────────────────────────

DN_RECOVERY Mode Detected (1 device(s)):
  • PE-3 - DNOS failed to boot

Mitigation: System Restore wizard (factory reset → GI → DNOS)

Launch System Restore for these devices? [Y/n]: █
```

**What Happens:**
- Press Enter → System Restore wizard launches
- Wizard connects via console
- Runs `request system restore factory-default`
- Waits for GI mode
- Deploys DNOS
- **Fully automated recovery!**

---

### 4. GI Mode (Ready for Deploy)

```
────────────────────────────────────────────────────────────────────────────────
🔧 AUTOMATIC DEPLOYMENT AVAILABLE
────────────────────────────────────────────────────────────────────────────────

GI Mode Detected (1 device(s)):
  • PE-2 - Ready for DNOS deployment

Next Step: Image Upgrade wizard (load images → deploy DNOS)

Launch Image Upgrade for these devices? [Y/n]: █
```

**What Happens:**
- Press Enter → Image Upgrade wizard launches
- Wizard loads DNOS/GI/BaseOS images
- Runs `request system deploy`
- Device boots to DNOS
- **Ready for configuration!**

---

### 5. Standalone Mode (Manual)

```
────────────────────────────────────────────────────────────────────────────────
⚠️  MANUAL INTERVENTION RECOMMENDED
────────────────────────────────────────────────────────────────────────────────

Standalone Mode Detected (1 device(s)):
  • PE-4 - One NCC down

Action Required: SSH to device and diagnose NCC failure
  Commands: show system, show ncc status
```

**What Happens:**
- No automatic prompt
- User must manually SSH to device
- Run diagnostic commands
- Fix NCC issue (restart service or replace card)

---

## Multi-Device Handling

**When multiple devices have different states:**

```
🔧 ONIE Rescue (PE-2):
Launch System Restore? [Y/n]: y  ✓

🔧 DN_RECOVERY (PE-3):
Launch System Restore? [Y/n]: y  ✓

🔧 GI Mode (PE-5):
Launch Image Upgrade? [Y/n]: n  ✗ (declined)

Launching SCALER wizard...
System Restore will be offered for: PE-2, PE-3
```

**Features:**
- ✅ Separate prompt for each state type
- ✅ Accept/decline each independently
- ✅ Only accepted devices go to wizard
- ✅ Wizard shows appropriate workflow for each

---

## User Actions

### Accept Mitigation

```
Launch System Restore for these devices? [Y/n]: y
# or just press Enter (default is Yes)
```

→ Wizard launches automatically

---

### Decline Mitigation

```
Launch System Restore for these devices? [Y/n]: n
```

→ Monitor exits normally
→ User can run `scaler-wizard` manually later

---

### Cancel Prompt

```
Launch System Restore for these devices? [Y/n]: ^C
```

→ Monitor exits
→ No wizard launched

---

## Examples

### Example 1: Quick Fix - Single Device

```bash
$ scaler-monitor

⚠️  PE-2: BASEOS SHELL MODE
   Fix: Run 'dncli' to enter GI mode

🔧 AUTOMATIC MITIGATION AVAILABLE
Launch System Restore? [Y/n]: ▊  # Press Enter

Launching SCALER wizard...
# Wizard runs, device fixed automatically!
```

**Time saved:** ~10 minutes of manual console work

---

### Example 2: Batch Recovery - Multiple Devices

```bash
$ scaler-monitor

⚠️  PE-2: ONIE RESCUE MODE
⚠️  PE-3: DN_RECOVERY MODE
ℹ️  PE-5: GI MODE

🔧 ONIE devices:
Launch System Restore? [Y/n]: y

🔧 DN_RECOVERY devices:
Launch System Restore? [Y/n]: y

🔧 GI devices:
Launch Image Upgrade? [Y/n]: y

Launching SCALER wizard...
# All 3 devices handled automatically!
```

**Time saved:** ~30 minutes of manual work per device = **1.5 hours total!**

---

### Example 3: Selective Recovery

```bash
$ scaler-monitor

⚠️  PE-2: BASEOS SHELL MODE
⚠️  PE-3: DN_RECOVERY MODE

🔧 BaseOS Shell devices:
Launch System Restore? [Y/n]: n  # Not now

🔧 DN_RECOVERY devices:
Launch System Restore? [Y/n]: y  # Fix this one

Launching SCALER wizard...
System Restore: PE-3 only
```

**Flexibility:** Choose which devices to fix now

---

## Benefits

| Feature | Manual Process | Automatic Prompts |
|---------|---------------|-------------------|
| **Detection** | Run monitor, read logs | Automatic |
| **Diagnosis** | Figure out what's wrong | Shows state + cause |
| **Console access** | Look up console details | Shown automatically |
| **Wizard selection** | Remember which wizard | Offered automatically |
| **Workflow** | Navigate wizard menus | Launches directly |
| **Time to fix** | 10-30 min per device | **1 keypress** |
| **Multi-device** | Repeat for each | **Batch prompts** |

---

## Configuration

### Enable Console Access for More Devices

Edit: `/home/dn/SCALER/scaler/connection_strategy.py`

```python
CONSOLE_MAPPINGS = {
    "PE-2": {
        'host': 'console-b15',
        'port': 13,
        'user': 'dn',
        'password': 'drive1234'
    },
    "PE-3": {  # Add more devices here
        'host': 'console-b16',
        'port': 5,
        'user': 'dn',
        'password': 'drive1234'
    },
}
```

→ Monitor will automatically detect these devices via console if SSH fails

---

## Troubleshooting

### Prompt Doesn't Appear

**Possible causes:**
1. Device state is "OK" (no mitigation needed)
2. Running in continuous mode (`-c` flag)
3. Connection strategy not available

**Solution:**
- Run one-time mode: `scaler-monitor` (no flags)
- Check device status in table

---

### Wizard Doesn't Launch

**Possible causes:**
1. User declined all prompts (pressed 'n')
2. Wizard binary not in PATH

**Solution:**
- Check: `/home/dn/bin/scaler-wizard` exists
- Accept at least one prompt

---

### Wrong Workflow Offered

**Possible causes:**
1. Stale `operational.json`
2. State detection issue

**Solution:**
1. Run monitor again (fresh detection)
2. Or use `[R] Refresh` in wizard

---

## Summary

**One command, one keypress, automatic recovery!**

```
$ scaler-monitor
  ↓
Press Enter at prompt
  ↓
Device fixed!
```

**No more:**
- ❌ Manual console access
- ❌ Looking up credentials
- ❌ Figuring out which wizard to use
- ❌ Navigating menus
- ❌ Typing recovery commands

**Just:**
- ✅ Run monitor
- ✅ Press Enter
- ✅ Done!

---

**Status:** ✅ Complete  
**Date:** 2026-01-27  
**Impact:** Reduces recovery time from 10-30 minutes to **1 keypress** per device!
