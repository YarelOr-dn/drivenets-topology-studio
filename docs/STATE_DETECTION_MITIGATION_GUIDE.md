# Complete Device State Detection & Mitigation Guide

## Overview

SCALER Monitor now provides **comprehensive state detection** for all DriveNets devices with **automatic mitigation guidance** based on the detected state.

---

## State Detection Matrix

| State | Severity | Detection | Cause | Mitigation | Wizard Action |
|-------|:--------:|-----------|-------|------------|---------------|
| **DNOS** | ✅ Normal | `PE-2#` prompt | Healthy operation | None needed | Normal operations |
| **GI** | ℹ️ Info | `GI#` prompt | After factory reset | Deploy DNOS | [8] Image Upgrade |
| **BaseOS Shell** | ⚠️ Warning | `dn@hostname:~$` | GI not started | Run `dncli` | System Restore (auto) |
| **DN_RECOVERY** | 🔴 Critical | `dnRouter(RECOVERY)#` | DNOS boot failure | Factory reset | System Restore |
| **ONIE** | 🔴 Critical | `ONIE:/ #` | BaseOS missing | Install BaseOS | System Restore |
| **Standalone** | ⚠️ High | `NCC: 1/2 UP` | One NCC down | Investigate NCC | Manual diagnosis |
| **Unreachable** | 🔴 Critical | No connection | Network/hardware | Check connectivity | Manual intervention |

---

## Monitor Output Examples

### Example 1: ONIE Rescue Mode (With Automatic Mitigation Prompt)

```
═══════════════════════════════════════════════════════════════════════════════
📊 DEVICE STATE DETECTION SUMMARY
═══════════════════════════════════════════════════════════════════════════════

⚠️  PE-2: ONIE RESCUE MODE
   State: Lowest-level bootloader
   Cause: BaseOS missing or corrupted
   Access: Console at console-b15 port 13
   Fix: Run System Restore wizard (installs BaseOS)
        → scaler-wizard → Select device → System Restore

═══════════════════════════════════════════════════════════════════════════════

────────────────────────────────────────────────────────────────────────────────
🔧 AUTOMATIC MITIGATION AVAILABLE
────────────────────────────────────────────────────────────────────────────────

ONIE Rescue Mode Detected (1 device(s)):
  • PE-2 - Requires BaseOS installation

Mitigation: System Restore wizard (installs BaseOS → GI → DNOS)

Launch System Restore for these devices? [Y/n]: █
```

**What Happens:**
1. Monitor detects ONIE via console
2. Shows comprehensive state info
3. **Automatically prompts** to launch System Restore
4. User presses Enter (or 'y')
5. Wizard launches with device pre-selected
6. System Restore runs automatically

---

### Example 2: BaseOS Shell Mode (With Automatic Mitigation Prompt)

```
═══════════════════════════════════════════════════════════════════════════════
📊 DEVICE STATE DETECTION SUMMARY
═══════════════════════════════════════════════════════════════════════════════

⚠️  PE-2: BASEOS SHELL MODE
   State: Linux shell (GI not started)
   Cause: GI container not running or manual boot
   Access: Console at console-b15 port 13
   Credentials: dn / drivenets
   Fix: Run 'dncli' to enter GI mode, then deploy DNOS
        → scaler-wizard → Select device → System Restore (auto)

═══════════════════════════════════════════════════════════════════════════════

────────────────────────────────────────────────────────────────────────────────
🔧 AUTOMATIC MITIGATION AVAILABLE
────────────────────────────────────────────────────────────────────────────────

BaseOS Shell Mode Detected (1 device(s)):
  • PE-2 - Needs 'dncli' to enter GI

Mitigation: System Restore wizard (runs dncli → GI → DNOS)

Launch System Restore for these devices? [Y/n]: █
```

**What Happens:**
1. Monitor detects BaseOS Shell via console
2. Shows manual steps (dncli) **and** automatic option
3. **Automatically prompts** to launch System Restore
4. User accepts
5. Wizard runs `dncli` automatically via console
6. Transitions to GI mode and deploys DNOS

---

### Example 3: GI Mode (With Automatic Deployment Prompt)

```
═══════════════════════════════════════════════════════════════════════════════
📊 DEVICE STATE DETECTION SUMMARY
═══════════════════════════════════════════════════════════════════════════════

ℹ️  PE-2: GI MODE
   State: Golden Image (container orchestration)
   Cause: Clean state after factory reset or fresh install
   Ready: Load images and deploy DNOS
        → scaler-wizard → Select device → [8] Image Upgrade

═══════════════════════════════════════════════════════════════════════════════

────────────────────────────────────────────────────────────────────────────────
🔧 AUTOMATIC DEPLOYMENT AVAILABLE
────────────────────────────────────────────────────────────────────────────────

GI Mode Detected (1 device(s)):
  • PE-2 - Ready for DNOS deployment

Next Step: Image Upgrade wizard (load images → deploy DNOS)

Launch Image Upgrade for these devices? [Y/n]: █
```

**What Happens:**
1. Monitor detects GI mode (ready state)
2. Shows that device is clean and ready
3. **Automatically prompts** to launch Image Upgrade
4. User accepts
5. Wizard loads DNOS/GI/BaseOS images
6. Deploys DNOS with saved parameters

---

### Example 4: DN_RECOVERY Mode (With Automatic Mitigation Prompt)

```
═══════════════════════════════════════════════════════════════════════════════
📊 DEVICE STATE DETECTION SUMMARY
═══════════════════════════════════════════════════════════════════════════════

⚠️  PE-3: DN_RECOVERY MODE
   State: DNOS failed to boot
   Cause: Software corruption, upgrade failure, config error
   Access: Console at console-b16 port 5
   Fix: Factory reset to GI mode, then deploy DNOS
        → scaler-wizard → Select device → System Restore

═══════════════════════════════════════════════════════════════════════════════

────────────────────────────────────────────────────────────────────────────────
🔧 AUTOMATIC MITIGATION AVAILABLE
────────────────────────────────────────────────────────────────────────────────

DN_RECOVERY Mode Detected (1 device(s)):
  • PE-3 - DNOS failed to boot

Mitigation: System Restore wizard (factory reset → GI → DNOS)

Launch System Restore for these devices? [Y/n]: █
```

**What Happens:**
1. Monitor detects DN_RECOVERY via console
2. Shows failure cause and mitigation
3. **Automatically prompts** to launch System Restore
4. User accepts
5. Wizard runs `request system restore factory-default`
6. Device reboots to GI, then DNOS deployed

---

### Example 5: Standalone Mode (Manual Intervention)

```
═══════════════════════════════════════════════════════════════════════════════
📊 DEVICE STATE DETECTION SUMMARY
═══════════════════════════════════════════════════════════════════════════════

⚠️  PE-4: STANDALONE MODE
   State: One NCC down (reduced redundancy)
   Cause: Hardware failure, software crash, network issue
   Fix: Investigate NCC failure, restart or replace card
        → Check: show system, show ncc status

═══════════════════════════════════════════════════════════════════════════════

────────────────────────────────────────────────────────────────────────────────
⚠️  MANUAL INTERVENTION RECOMMENDED
────────────────────────────────────────────────────────────────────────────────

Standalone Mode Detected (1 device(s)):
  • PE-4 - One NCC down

Action Required: SSH to device and diagnose NCC failure
  Commands: show system, show ncc status
```

**What Happens:**
1. Monitor detects Standalone via config header
2. Shows diagnostic commands
3. **No automatic wizard** (requires manual diagnosis)
4. User must SSH and investigate NCC failure

---

### Example 6: Multiple Devices with Mixed States

```
═══════════════════════════════════════════════════════════════════════════════
📊 DEVICE STATE DETECTION SUMMARY
═══════════════════════════════════════════════════════════════════════════════

⚠️  PE-2: BASEOS SHELL MODE
   State: Linux shell (GI not started)
   Cause: GI container not running or manual boot
   Access: Console at console-b15 port 13
   Credentials: dn / drivenets
   Fix: Run 'dncli' to enter GI mode, then deploy DNOS
        → scaler-wizard → Select device → System Restore (auto)

⚠️  PE-3: DN_RECOVERY MODE
   State: DNOS failed to boot
   Cause: Software corruption, upgrade failure, config error
   Access: Console at console-b16 port 5
   Fix: Factory reset to GI mode, then deploy DNOS
        → scaler-wizard → Select device → System Restore

ℹ️  PE-5: GI MODE
   State: Golden Image (container orchestration)
   Cause: Clean state after factory reset or fresh install
   Ready: Load images and deploy DNOS
        → scaler-wizard → Select device → [8] Image Upgrade

═══════════════════════════════════════════════════════════════════════════════

────────────────────────────────────────────────────────────────────────────────
🔧 AUTOMATIC MITIGATION AVAILABLE
────────────────────────────────────────────────────────────────────────────────

BaseOS Shell Mode Detected (1 device(s)):
  • PE-2 - Needs 'dncli' to enter GI

Mitigation: System Restore wizard (runs dncli → GI → DNOS)

Launch System Restore for these devices? [Y/n]: y

────────────────────────────────────────────────────────────────────────────────
🔧 AUTOMATIC MITIGATION AVAILABLE
────────────────────────────────────────────────────────────────────────────────

DN_RECOVERY Mode Detected (1 device(s)):
  • PE-3 - DNOS failed to boot

Mitigation: System Restore wizard (factory reset → GI → DNOS)

Launch System Restore for these devices? [Y/n]: y

────────────────────────────────────────────────────────────────────────────────
🔧 AUTOMATIC DEPLOYMENT AVAILABLE
────────────────────────────────────────────────────────────────────────────────

GI Mode Detected (1 device(s)):
  • PE-5 - Ready for DNOS deployment

Next Step: Image Upgrade wizard (load images → deploy DNOS)

Launch Image Upgrade for these devices? [Y/n]: n

Launching SCALER wizard...
System Restore will be offered for: PE-2, PE-3
```

**What Happens:**
1. Monitor detects multiple devices with different states
2. Shows comprehensive info for each
3. **Prompts separately** for each mitigation type
4. User can accept/decline for each group
5. Wizard launches with all accepted devices pre-selected
6. Appropriate workflow runs for each device

---

## State Transition Flows

### Flow 1: ONIE → DNOS (Complete Recovery)

```
┌─────────────┐
│ ONIE Rescue │ ← Monitor detects
└──────┬──────┘
       │ System Restore wizard
       │ 1. Check EEPROM
       │ 2. Remove partition 3
       │ 3. Install BaseOS
       │ 4. Reboot
       ↓
┌─────────────┐
│  BaseOS     │ ← Monitor detects
│   Shell     │
└──────┬──────┘
       │ System Restore wizard
       │ 1. Run 'dncli'
       ↓
┌─────────────┐
│  GI Mode    │ ← Monitor detects
└──────┬──────┘
       │ Image Upgrade wizard
       │ 1. Load DNOS/GI/BaseOS
       │ 2. Deploy DNOS
       ↓
┌─────────────┐
│ DNOS OK     │ ← Monitor detects
└─────────────┘
```

---

### Flow 2: DN_RECOVERY → DNOS

```
┌─────────────┐
│DN_RECOVERY  │ ← Monitor detects
└──────┬──────┘
       │ System Restore wizard
       │ 1. request system restore factory-default
       │ 2. Wait for reboot
       ↓
┌─────────────┐
│  GI Mode    │ ← Monitor detects
└──────┬──────┘
       │ Image Upgrade wizard
       │ 1. Load images
       │ 2. Deploy DNOS
       ↓
┌─────────────┐
│ DNOS OK     │ ← Monitor detects
└─────────────┘
```

---

### Flow 3: BaseOS Shell → DNOS

```
┌─────────────┐
│BaseOS Shell │ ← Monitor detects
└──────┬──────┘
       │ Option 1: Manual
       │ → Login (dn/drivenets)
       │ → Run 'dncli'
       │ → Enter password (dnroot)
       │
       │ Option 2: Automatic
       │ → System Restore wizard
       ↓
┌─────────────┐
│  GI Mode    │ ← Monitor detects
└──────┬──────┘
       │ Image Upgrade wizard
       ↓
┌─────────────┐
│ DNOS OK     │ ← Monitor detects
└─────────────┘
```

---

## Mitigation Command Reference

### For Each State

#### ONIE Rescue
```bash
# Monitor Detection:
# - Console connection successful
# - Prompt: "ONIE:/ #"
# - Commands: onie-syseeprom available

# Manual Mitigation:
onie-syseeprom  # Check EEPROM
parted -l       # Check partitions
parted /dev/sda rm 3  # Remove if UBUNTU partition exists
onie-nos-install http://minio.../drivenets_baseos_*.tar

# Automatic Mitigation:
scaler-wizard → Select device → System Restore
```

#### BaseOS Shell
```bash
# Monitor Detection:
# - Console connection successful
# - Prompt: "dn@hostname:~$"
# - Credentials: dn/drivenets

# Manual Mitigation:
dncli  # Enter GI mode
# Password: dnroot

# Automatic Mitigation:
scaler-wizard → Select device → System Restore (runs dncli automatically)
```

#### GI Mode
```bash
# Monitor Detection:
# - SSH or console connection
# - Prompt: "GI#" or "GI(...)"
# - Credentials: dnroot/dnroot

# No Mitigation Needed:
# Device is ready for DNOS deployment

# Next Step:
scaler-wizard → Select device → [8] Image Upgrade
# Then:
request system target-stack load <dnos_url>
request system deploy system-type <type> name <hostname> ncc-id 0
```

#### DN_RECOVERY
```bash
# Monitor Detection:
# - Console connection (SSH usually fails)
# - Prompt: "dnRouter(RECOVERY)#"
# - show system fails

# Mitigation:
request system restore factory-default
yes  # Confirm
# Device reboots to GI mode

# Or Automatic:
scaler-wizard → Select device → System Restore
```

#### Standalone
```bash
# Monitor Detection:
# - SSH connection successful
# - running.txt header: "NCC: 1/2 UP"
# - One NCC marked as down

# Diagnosis:
show system
show ncc status
show system stack

# Mitigation:
# 1. Check NCC logs
# 2. Restart NCC service if software issue
# 3. Replace NCC card if hardware failure
```

---

## Integration Flow

```
┌──────────────────────────────────────────────────────────┐
│                   SCALER Monitor                         │
│                                                          │
│  1. Try SSH extraction (extract_configs.sh)             │
│  2. If SSH fails → Multi-path connection strategy       │
│     ├─ Try SSH to management IP                         │
│     ├─ Try Console server                               │
│     └─ Try SSH to loopback IP                           │
│  3. Detect state from prompt/output                     │
│  4. Update operational.json with:                       │
│     - recovery_mode_detected: true/false                │
│     - recovery_type: "ONIE", "BASEOS_SHELL", "GI", etc. │
│  5. Display comprehensive summary with:                 │
│     - Current state                                     │
│     - Root cause                                        │
│     - Mitigation steps                                  │
│     - Console access info                               │
│     - Wizard command                                    │
└──────────────────────────────────────────────────────────┘
                            │
                            │ operational.json updated
                            ↓
┌──────────────────────────────────────────────────────────┐
│                  SCALER Wizard                           │
│                                                          │
│  1. Read operational.json for each device               │
│  2. Display device status:                              │
│     - OK (DNOS running)                                 │
│     - GI_MODE (ready for deploy)                        │
│     - BASEOS_SHELL (need dncli)                         │
│     - DN_RECOVERY (need factory reset)                  │
│     - ONIE (need BaseOS install)                        │
│     - STANDALONE (degraded)                             │
│  3. When device selected:                               │
│     - Show state-specific prompt                        │
│     - Offer appropriate wizard:                         │
│       * GI → Image Upgrade                              │
│       * BaseOS Shell → System Restore (dncli)           │
│       * Recovery/ONIE → System Restore (full)           │
│  4. Execute automated recovery workflow                 │
└──────────────────────────────────────────────────────────┘
```

---

## Configuration: Add Console Access

To enable console detection for any device, edit:
`/home/dn/SCALER/scaler/connection_strategy.py`

```python
CONSOLE_MAPPINGS = {
    "PE-2": {
        'host': 'console-b15',
        'port': 13,
        'user': 'dn',
        'password': 'drive1234'
    },
    "PE-3": {  # Add new device
        'host': 'console-b16',
        'port': 5,
        'user': 'dn',
        'password': 'drive1234'
    },
    # Add more devices as needed
}
```

---

## Benefits

### Before Enhancement
```
📡 Device Status
  PE-1    OK
  PE-2    DN_RECOVERY  ← Generic, cached status
  PE-4    OK

⚠️ USER ALERT: PE-2 is in RECOVERY MODE
```
**Problems:**
- Generic "RECOVERY" doesn't distinguish states
- No mitigation guidance
- User must figure out next steps
- Only PE-2 has console fallback

---

### After Enhancement
```
📡 Device Status
  PE-1    OK
  PE-2    GI_MODE      ← Specific, real-time status
  PE-4    OK

═══════════════════════════════════════════════════════════════════════════════
📊 DEVICE STATE DETECTION SUMMARY
═══════════════════════════════════════════════════════════════════════════════

ℹ️  PE-2: GI MODE
   State: Golden Image (container orchestration)
   Cause: Clean state after factory reset or fresh install
   Ready: Load images and deploy DNOS
        → scaler-wizard → Select device → [8] Image Upgrade

═══════════════════════════════════════════════════════════════════════════════
```
**Benefits:**
- ✅ Specific state detection (ONIE, BaseOS, GI, Recovery)
- ✅ Clear cause explanation
- ✅ Exact mitigation steps
- ✅ Console access info
- ✅ Direct wizard command
- ✅ Works for ALL devices (extensible)

---

## Testing

### Test Scenario 1: PE-2 in GI Mode (With Automatic Prompt)

```bash
scaler-monitor

# Expected output:
📊 DEVICE STATE DETECTION SUMMARY

ℹ️  PE-2: GI MODE
   State: Golden Image
   Ready: Load images and deploy DNOS
        → scaler-wizard → Select device → [8] Image Upgrade

────────────────────────────────────────────────────────────────────────────────
🔧 AUTOMATIC DEPLOYMENT AVAILABLE
────────────────────────────────────────────────────────────────────────────────

GI Mode Detected (1 device(s)):
  • PE-2 - Ready for DNOS deployment

Next Step: Image Upgrade wizard (load images → deploy DNOS)

Launch Image Upgrade for these devices? [Y/n]: █  # Press Enter to accept!

Launching SCALER wizard...
Image Upgrade will be offered for: PE-2
```

---

### Test Scenario 2: PE-2 in BaseOS Shell (With Automatic Prompt)

```bash
scaler-monitor

# Expected output:
📊 DEVICE STATE DETECTION SUMMARY

⚠️  PE-2: BASEOS SHELL MODE
   State: Linux shell (GI not started)
   Fix: Run 'dncli' to enter GI mode
        → scaler-wizard → Select device → System Restore (auto)

────────────────────────────────────────────────────────────────────────────────
🔧 AUTOMATIC MITIGATION AVAILABLE
────────────────────────────────────────────────────────────────────────────────

BaseOS Shell Mode Detected (1 device(s)):
  • PE-2 - Needs 'dncli' to enter GI

Mitigation: System Restore wizard (runs dncli → GI → DNOS)

Launch System Restore for these devices? [Y/n]: █  # Press Enter!

Launching SCALER wizard...
System Restore will be offered for: PE-2

# Wizard will automatically run dncli and deploy DNOS
```

---

### Test Scenario 3: Decline Automatic Mitigation

```bash
scaler-monitor

# Expected output with prompt:
Launch System Restore for these devices? [Y/n]: n  # Decline

# Monitor exits normally, no wizard launch
# User can manually run scaler-wizard later if needed
```

---

## Benefits Summary

| Feature | Before | After |
|---------|--------|-------|
| **State detection** | Generic "RECOVERY" | 7 specific states |
| **Cause analysis** | None | Automatic |
| **Console fallback** | PE-2 only | All devices (extensible) |
| **Mitigation guidance** | None | Comprehensive |
| **Automatic prompts** | None | **State-specific prompts** |
| **Wizard launch** | Manual | **One-click from monitor** |
| **Multi-device support** | Limited | Full with grouped prompts |
| **Documentation** | Scattered | Complete guides |

---

## Automatic Mitigation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    User Runs Monitor                        │
│                   scaler-monitor                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ├─ Detect device states (ONIE, BaseOS, GI, Recovery, etc.)
                        │
                        ├─ Show comprehensive state summary
                        │
                        └─ GROUP DEVICES by mitigation type:
                           │
                           ├─ ONIE devices → Prompt: "Launch System Restore? [Y/n]"
                           │  User accepts → Add to devices_to_restore[]
                           │
                           ├─ BaseOS Shell → Prompt: "Launch System Restore? [Y/n]"
                           │  User accepts → Add to devices_to_restore[]
                           │
                           ├─ DN_RECOVERY → Prompt: "Launch System Restore? [Y/n]"
                           │  User accepts → Add to devices_to_restore[]
                           │
                           ├─ GI Mode → Prompt: "Launch Image Upgrade? [Y/n]"
                           │  User accepts → Add to devices_to_deploy[]
                           │
                           └─ Standalone → Info only (manual intervention)
                           
                        ↓ If any devices accepted
                        
┌─────────────────────────────────────────────────────────────┐
│              Wizard Launches Automatically                  │
│                                                             │
│  • Reads operational.json for each device                  │
│  • Shows state-specific workflow for each                  │
│  • User proceeds through wizard                            │
│  • Automated recovery/deployment executes                  │
└─────────────────────────────────────────────────────────────┘
```

---

## User Experience Comparison

### Scenario 1: PE-2 in ONIE Rescue Mode

**Before Enhancement:**
```bash
$ scaler-monitor
PE-2: RECOVERY  # Generic, no details

$ scaler-wizard
# User must:
# 1. Know PE-2 is in trouble
# 2. Remember console access details
# 3. Manually navigate to System Restore
# 4. Hope the wizard handles ONIE correctly
```

**After Enhancement:**
```bash
$ scaler-monitor

📊 DEVICE STATE DETECTION SUMMARY
═══════════════════════════════════════════════════════════════════════════════

⚠️  PE-2: ONIE RESCUE MODE
   State: Lowest-level bootloader
   Cause: BaseOS missing or corrupted
   Access: Console at console-b15 port 13
   Fix: Run System Restore wizard (installs BaseOS)

═══════════════════════════════════════════════════════════════════════════════

🔧 AUTOMATIC MITIGATION AVAILABLE
────────────────────────────────────────────────────────────────────────────────

ONIE Rescue Mode Detected (1 device):
  • PE-2 - Requires BaseOS installation

Mitigation: System Restore wizard (installs BaseOS → GI → DNOS)

Launch System Restore for these devices? [Y/n]: ▊  # Just press Enter!

Launching SCALER wizard...
System Restore will be offered for: PE-2

# Wizard automatically:
# 1. Connects via console
# 2. Checks EEPROM
# 3. Removes partition 3
# 4. Installs BaseOS
# 5. Waits for BaseOS Shell
# 6. Runs dncli
# 7. Enters GI mode
# 8. Deploys DNOS
# ALL AUTOMATED WITH ONE KEYPRESS!
```

---

### Scenario 2: Multiple Devices in Different States

**Before Enhancement:**
```bash
$ scaler-monitor
PE-2: RECOVERY
PE-3: RECOVERY
PE-5: OK?  # Not clear what "OK" means

# User confused: What type of recovery? What's the difference?
# Manual workflow for each device
```

**After Enhancement:**
```bash
$ scaler-monitor

📊 DEVICE STATE DETECTION SUMMARY
═══════════════════════════════════════════════════════════════════════════════

⚠️  PE-2: BASEOS SHELL MODE
   Fix: Run 'dncli' to enter GI mode

⚠️  PE-3: DN_RECOVERY MODE
   Fix: Factory reset to GI mode

ℹ️  PE-5: GI MODE
   Ready: Load images and deploy DNOS

═══════════════════════════════════════════════════════════════════════════════

# Three separate prompts (user can accept/decline each):

🔧 BaseOS Shell Mode (PE-2):
Launch System Restore? [Y/n]: y  ✓

🔧 DN_RECOVERY Mode (PE-3):
Launch System Restore? [Y/n]: y  ✓

🔧 GI Mode (PE-5):
Launch Image Upgrade? [Y/n]: y  ✓

Launching SCALER wizard...
System Restore: PE-2, PE-3
Image Upgrade: PE-5

# All three devices handled appropriately, automatically!
```

---

## State Persistence

All state information is persisted to `operational.json`:

```json
{
  "recovery_mode_detected": true,
  "recovery_type": "GI",
  "recovery_mode_detected_at": "2026-01-27T19:45:00"
}
```

**Wizard reads this** to show accurate status and offer appropriate actions.

---

**Status:** ✅ Complete  
**Date:** 2026-01-27  
**Enhancement:** Automatic prompted mitigations added!  
**Impact:** Monitor now provides comprehensive state detection with **automatic mitigation prompts** that launch the appropriate wizard with one keypress. Users get grouped prompts for each state type (ONIE, BaseOS Shell, DN_RECOVERY, GI) and can accept/decline each group. Wizard launches automatically with all accepted devices pre-selected for the correct workflow.
