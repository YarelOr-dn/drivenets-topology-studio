# Complete Recovery Workflows - Corrected

## Overview

All recovery workflows are now **100% correct** based on how the System Restore wizard actually works.

---

## State Detection → Workflow Mapping

| Device State | Monitor Prompt | Wizard Launched | Automated Actions |
|--------------|----------------|-----------------|-------------------|
| **ONIE Rescue** | System Restore | System Restore | 1. Install BaseOS<br>2. Run dncli<br>3. Enter GI<br>4. Load images<br>5. Deploy DNOS |
| **BaseOS Shell** | System Restore | System Restore | 1. Run dncli<br>2. Enter GI<br>3. Load images<br>4. Deploy DNOS |
| **DN_RECOVERY** | System Restore | System Restore | 1. Factory reset<br>2. Enter GI<br>3. Load images<br>4. Deploy DNOS |
| **GI Mode** | Image Upgrade | Image Upgrade | 1. Load images<br>2. Deploy DNOS |
| **Standalone** | Manual | None | User must diagnose NCC failure |

---

## Complete Workflows

### 1. ONIE Rescue → DNOS (Full Recovery)

```
Monitor detects: ONIE Rescue
     ↓
Prompts: Launch System Restore? [Y/n]
     ↓
User: [Enter]
     ↓
System Restore Wizard:
  1. Connect to console
  2. Login (dn/drivenets)
  3. Check EEPROM (onie-syseeprom)
  4. Remove partition 3 if exists
  5. Install BaseOS (onie-nos-install)
  6. Wait for BaseOS Shell
  7. Run dncli
  8. Enter GI mode
  9. Call Image Upgrade wizard:
     - Load DNOS image
     - Load GI image
     - Load BaseOS image
 10. Deploy DNOS
     ↓
Device is now running DNOS!
```

**Time:** ~15-20 minutes (BaseOS install is slow)

---

### 2. BaseOS Shell → DNOS (Quick Recovery)

```
Monitor detects: BaseOS Shell (dn@hostname:~$)
     ↓
Prompts: Launch System Restore? [Y/n]
     ↓
User: [Enter]
     ↓
System Restore Wizard:
  1. Connect to console
  2. Already in BaseOS Shell
  3. Run dncli
  4. Enter GI mode
  5. Call Image Upgrade wizard:
     - Load DNOS image
     - Load GI image
     - Load BaseOS image
  6. Deploy DNOS
     ↓
Device is now running DNOS!
```

**Time:** ~5-8 minutes

---

### 3. DN_RECOVERY → DNOS (Standard Recovery)

```
Monitor detects: DN_RECOVERY (dnRouter(RECOVERY)#)
     ↓
Prompts: Launch System Restore? [Y/n]
     ↓
User: [Enter]
     ↓
System Restore Wizard:
  1. Connect to console (or SSH if available)
  2. Run: request system restore factory-default
  3. Confirm: yes
  4. Wait for reboot
  5. Enter GI mode
  6. Call Image Upgrade wizard:
     - Load DNOS image
     - Load GI image
     - Load BaseOS image
  7. Deploy DNOS
     ↓
Device is now running DNOS!
```

**Time:** ~10-15 minutes

---

### 4. GI Mode → DNOS (Fresh Deploy)

```
Monitor detects: GI Mode (GI#)
     ↓
Prompts: Launch Image Upgrade? [Y/n]
     ↓
User: [Enter]
     ↓
Image Upgrade Wizard:
  1. Already in GI mode
  2. Select image source (Jenkins/URL)
  3. Load DNOS image
  4. Load GI image
  5. Load BaseOS image
  6. Deploy DNOS
     ↓
Device is now running DNOS!
```

**Time:** ~5-8 minutes

---

## Key Points (CORRECTED)

### ✅ System Restore Wizard Does:
1. **Gets device to GI mode** (via factory reset, dncli, or BaseOS install)
2. **Automatically calls Image Upgrade wizard** after reaching GI
3. **Loads all images** (DNOS, GI, BaseOS) via Image Upgrade
4. **Deploys DNOS** via Image Upgrade
5. **Completes full recovery** in one wizard run

### ✅ Image Upgrade Wizard Does:
1. **Assumes device is already in GI mode**
2. **Loads images** (DNOS, GI, BaseOS)
3. **Deploys DNOS**

### ✅ Workflow Rules:
- **ONIE/BaseOS/DN_RECOVERY** → **System Restore** (handles getting to GI + images + deploy)
- **Already in GI** → **Image Upgrade** (just images + deploy)
- **System Restore = Complete end-to-end recovery**
- **Image Upgrade = Images + deploy only (expects GI mode)**

---

## Monitor Output (CORRECTED)

### BaseOS Shell Mode

```
═══════════════════════════════════════════════════════════════════════════════
📊 DEVICE STATE DETECTION SUMMARY
═══════════════════════════════════════════════════════════════════════════════

⚠️  PE-2: BASEOS SHELL MODE
   State: Linux shell (GI not started)
   Cause: GI container not running or manual boot
   Access: Console at console-b15 port 13
   Credentials: dn / drivenets
   Fix: System Restore (dncli → GI → load images → deploy)
        → scaler-wizard → Select device → System Restore

═══════════════════════════════════════════════════════════════════════════════

────────────────────────────────────────────────────────────────────────────────
🔧 AUTOMATIC MITIGATION AVAILABLE
────────────────────────────────────────────────────────────────────────────────

BaseOS Shell Mode Detected (1 device(s)):
  • PE-2 - Needs dncli → load images → deploy

Mitigation: System Restore wizard (runs dncli → GI → loads images → deploys)

Launch System Restore for these devices? [Y/n]: █
```

---

### GI Mode (Ready)

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

---

## Wizard Selection (CORRECTED)

### When User Selects Device in Wizard:

**BaseOS Shell:**
```
⚠ PE-2 is in BASEOS SHELL mode
  System Restore will: dncli → GI mode → load images → deploy DNOS

📡 Console: ssh dn@console-b15, port 13, login: dn/drivenets
Manual: dncli (password: dnroot), then use Image Upgrade
Automatic: System Restore handles everything

System Restore automates: dncli → GI mode → Image Upgrade (load + deploy)

Launch System Restore wizard? [Y/n]: █
```

**GI Mode:**
```
ℹ️ PE-2 is in GI MODE
  Device is ready for image loading and deployment

You can either:
  • Continue to main menu and select [8] Image Upgrade
  • Or launch Image Upgrade wizard now

Launch Image Upgrade wizard now? [Y/n]: █
```

---

## System Restore Wizard Flow (Internal)

```python
def run_system_restore_wizard(device, multi_ctx):
    # Step 1-5: Get device info, plan, confirm
    
    # Step 6: Restore to GI mode
    if is_onie:
        install_baseos()
        wait_for_baseos_shell()
    
    if is_baseos_shell:
        run_dncli()
        wait_for_gi_mode()
    
    if is_dn_recovery:
        run_factory_reset()
        wait_for_gi_mode()
    
    # Device is now in GI mode!
    
    # Step 7: Call Image Upgrade wizard
    if not skip_images:
        run_image_upgrade_wizard(multi_ctx)
        # Image Upgrade handles:
        # - Load DNOS image
        # - Load GI image
        # - Load BaseOS image
        # - Deploy DNOS
    
    return True
```

---

## Summary

### The Truth:
- **System Restore = Complete recovery wizard** (get to GI + load images + deploy)
- **Image Upgrade = Images + deploy wizard** (expects GI mode already)
- **BaseOS Shell → System Restore** (NOT Image Upgrade)
- **System Restore calls Image Upgrade internally** after reaching GI

### Why This Matters:
- User only needs to run **ONE wizard** for complete recovery
- No manual image loading after System Restore
- No separate Image Upgrade step needed
- Everything is automated from any state → DNOS

---

**Status:** ✅ Fully Corrected  
**Date:** 2026-01-27  
**Correction:** BaseOS Shell → System Restore (which includes dncli + Image Upgrade internally)
