# Complete Device Recovery Workflows

## Overview

The SCALER system now provides **state-specific** recovery workflows with **automatic continuity** from recovery to deployment. Each device state has a tailored mitigation path that can flow seamlessly from detection → recovery → deployment.

---

## State-Specific Recovery Paths

### 1. ONIE RESCUE MODE

**Detection:**
- Lowest-level bootloader active
- BaseOS missing or corrupted
- Console shows: `ONIE:/ #`

**Automated Recovery Flow:**
```
Select device in ONIE state
  ↓
[1] Launch System Restore
  ↓
System Restore wizard:
  • Detects ONIE mode
  • Installs BaseOS via onie-nos-install
  • Reboots into BaseOS Shell
  • Runs dncli → GI mode
  • Auto-discovers mgmt IP
  ↓
✓ System Restore completed
  ↓
"Continue to Image Upgrade?" [Y/n]
  ↓
Image Upgrade wizard:
  • Load DNOS/GI/BaseOS images
  • Deploy DNOS
  ↓
✓ Device fully operational
```

**Manual Recovery Option:**
```
[2] Manual recovery instructions
  • Connect to console
  • Login: dn / drivenets
  • Check EEPROM: onie-syseeprom
  • Check partitions: parted -l
  • Remove Ubuntu partition if exists: parted /dev/sda rm 3
  • Install BaseOS: onie-nos-install <baseos-image>
  • Reboot and follow BaseOS Shell recovery
```

---

### 2. BASEOS SHELL MODE

**Detection:**
- Linux Ubuntu shell active
- GI container not running
- Console shows: `dn@WKY1BC7400002B2:~$`

**Automated Recovery Flow:**
```
Select device in BASEOS_SHELL state
  ↓
[1] Launch System Restore
  ↓
System Restore wizard:
  • Detects BaseOS Shell
  • Logs in with dn/drivenets
  • Runs: dncli (password: dnroot)
  • Waits for GI mode prompt: GI#
  • Auto-discovers mgmt IP from GI
  ↓
✓ System Restore completed - Device is now in GI mode
  ↓
"Continue to Image Upgrade?" [Y/n]
  ↓
Image Upgrade wizard:
  • Load DNOS/GI/BaseOS images
  • Deploy DNOS
  ↓
✓ Device fully operational
```

**Manual Recovery Option:**
```
[2] Manual recovery instructions
  • Connect to console
  • Login: dn / drivenets
  • Run: dncli (password: dnroot)
  • Verify GI mode: show system stack
  • Use Image Upgrade wizard to load images and deploy
```

---

### 3. DN_RECOVERY MODE

**Detection:**
- DNOS failed to boot
- All NCCs down (NCC: 0/2 UP)
- Uptime: N/A
- SSH may be available or console required

**Automated Recovery Flow:**
```
Select device in DN_RECOVERY state
  ↓
[1] Launch System Restore
  ↓
System Restore wizard:
  • Connects via console (if SSH unavailable)
  • Runs: request system restore factory-default
  • Device reboots into GI mode
  • Auto-discovers new mgmt IP from GI
  ↓
✓ System Restore completed - Device is now in GI mode
  ↓
"Continue to Image Upgrade?" [Y/n]
  ↓
Image Upgrade wizard:
  • Load DNOS/GI/BaseOS images
  • Deploy DNOS
  ↓
✓ Device fully operational
```

**Manual Recovery Option:**
```
[2] Manual recovery instructions
  • Connect via SSH or console
  • Login: dnroot / dnroot
  • Run: request system restore factory-default
  • Device will reboot into GI mode
  • Configure mgmt0 IP
  • Use Image Upgrade wizard to deploy DNOS
```

---

### 4. GI MODE (Golden Image)

**Detection:**
- Container orchestration active
- DNOS not deployed
- Console shows: `GI#` or `gicli`

**Automated Deployment Flow:**
```
Select device in GI state
  ↓
[1] Launch Image Upgrade wizard (recommended)
  ↓
Image Upgrade wizard:
  • Select Jenkins build or manual images
  • Load DNOS, GI, BaseOS images
  • Execute: request system deploy system-type <type> name <hostname> ncc-id <id>
  • Monitor deployment progress
  ↓
✓ Device fully operational
```

**This state is NOT a failure** - it's a clean starting point ready for deployment.

---

### 5. STANDALONE MODE

**Detection:**
- One NCC down (NCC: 1/2 UP)
- Reduced redundancy
- Device still operational

**Investigation Required:**
```
Select device in STANDALONE state
  ↓
[1] View diagnostic commands
  ↓
Diagnostic Commands:
  • show system
  • show ncc status
  • show logging | match NCC
  • show system stack
  ↓
SSH to device and investigate
  • Hardware failure? Replace NCC card
  • Software crash? Restart NCC
  • Network issue? Check connectivity
```

**No automated recovery** - requires manual investigation and hardware/software intervention.

---

## Workflow Continuity Features

### Automatic Transition to Image Upgrade

After any System Restore operation completes successfully:

1. **Success Confirmation:**
   ```
   ✓ System Restore completed - Device is now in GI mode
   ```

2. **Continuation Prompt:**
   ```
   Continue to Image Upgrade to load images and deploy DNOS? [Y/n]
   ```

3. **Seamless Handoff:**
   - If user confirms [Y], Image Upgrade wizard launches immediately
   - Device object is passed to Image Upgrade context
   - User can select Jenkins build or manual images
   - Deployment executes automatically

4. **User Control:**
   - User can decline [n] and return to main menu
   - Option [8] Image Upgrade is always available in main menu
   - Can manually launch Image Upgrade later

---

## State-Specific Prompts

### ONIE Mode
```
Select action:
  [1] 🔧 Launch System Restore (BaseOS install → dncli → GI → images → deploy)
  [2] 📖 Manual recovery instructions
  [3] Continue to main menu
  [B] Back to device selection
```

### BASEOS SHELL Mode
```
Select action:
  [1] 🔧 Launch System Restore (dncli → GI → images → deploy)
  [2] 📖 Manual recovery instructions
  [3] Continue to main menu
  [B] Back to device selection
```

### DN_RECOVERY Mode
```
Select action:
  [1] 🔧 Launch System Restore (factory reset → GI → images → deploy)
  [2] 📖 Manual recovery instructions
  [3] Continue to main menu
  [B] Back to device selection
```

### GI Mode
```
Select action:
  [1] 🚀 Launch Image Upgrade wizard (recommended)
  [2] Continue to main menu
  [B] Back to device selection
```

### STANDALONE Mode
```
Select action:
  [1] 📖 View diagnostic commands
  [2] Continue to main menu
  [B] Back to device selection
```

---

## Benefits

1. **State-Specific Guidance:**
   - Each recovery state shows its specific cause and recovery path
   - Users understand exactly what's wrong and what will be done

2. **Automated Continuity:**
   - No need to remember to run Image Upgrade after System Restore
   - Seamless flow from recovery to deployment
   - Reduces manual steps and errors

3. **Manual Override:**
   - Manual instructions available for every state
   - Users can choose to handle recovery manually
   - Diagnostic commands provided for investigation

4. **Flexible Navigation:**
   - Can always go [B]ack to device selection
   - Can skip to main menu if needed
   - Can decline automatic transitions

5. **Complete Recovery:**
   - Single workflow from ONIE → BaseOS → GI → DNOS
   - Or from DN_RECOVERY → GI → DNOS
   - Or from BASEOS_SHELL → GI → DNOS
   - End result: fully operational device

---

## Example: Complete ONIE Recovery

```
1. Monitor detects device in ONIE mode
   └─ Status: ⚠ ONIE

2. User runs: scaler-wizard
   └─ Table shows: PE-2 | ONIE

3. User selects PE-2
   └─ Panel: "⚠ ONIE RESCUE MODE"
   └─ Cause: BaseOS missing or corrupted
   └─ Recovery path: BaseOS install → dncli → GI → images → deploy

4. User selects: [1] Launch System Restore
   └─ System Restore wizard starts
   └─ Connects to console
   └─ Installs BaseOS via ONIE
   └─ Reboots into BaseOS Shell
   └─ Runs dncli → enters GI mode
   └─ Discovers mgmt IP: 100.64.8.39

5. System Restore completes
   └─ ✓ System Restore completed - Device is now in GI mode
   └─ Prompt: Continue to Image Upgrade? [Y]

6. User confirms: Y
   └─ Image Upgrade wizard launches
   └─ User selects Jenkins build
   └─ Images loaded: DNOS, GI, BaseOS
   └─ Deploy executes: request system deploy...

7. Deployment completes
   └─ ✓ Device fully operational
   └─ Status: ✓ OK
```

---

## Implementation Notes

- **Console credentials stored:** dn/drivenets for ONIE and BaseOS Shell
- **SSH credentials:** dnroot/dnroot for DNOS and GI
- **Console paths configurable:** Per-device console server and port
- **Error handling:** Graceful fallback if Image Upgrade fails
- **State persistence:** operational.json updated throughout process
- **Monitor integration:** Status updates reflected immediately
