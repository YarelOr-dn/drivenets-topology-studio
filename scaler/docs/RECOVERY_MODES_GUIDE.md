# DriveNets DNOS Recovery Modes Guide
## Complete troubleshooting and recovery procedures

**Last Updated:** 2026-01-27  
**Source:** Field experience, SCALER implementation, DNOS device observations

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Recovery Mode Types](#recovery-mode-types)
3. [Detection Methods](#detection-methods)
4. [Root Causes](#root-causes)
5. [Recovery Procedures](#recovery-procedures)
6. [Prevention](#prevention)

---

## Overview

DriveNets devices can enter various recovery states when critical failures occur. This guide documents the different recovery modes, their causes, detection methods, and recovery procedures based on field experience with SCALER automation.

---

## Recovery Mode Types

### 1. **RECOVERY Mode** (Boot Failure)
**Severity:** 🔴 Critical  
**System State:** Device failed to boot DNOS properly

**Indicators:**
- CLI prompt shows: `dnRouter(RECOVERY)#` or contains `RECOVERY`
- All NCCs down: `NCC: 0/X UP`
- Uptime: `N/A`
- All interfaces: `0 UP`
- No routing protocols active

**What's Running:**
- Minimal boot environment
- Basic CLI available
- Configuration preserved (usually)
- No data plane functionality

**Typical Scenarios:**
- DNOS image corruption
- Failed upgrade/downgrade
- Critical software crash during boot
- Incompatible version combination (DNOS/GI/BaseOS mismatch)

---

### 2. **GI Mode** (Golden Image)
**Severity:** 🟡 Warning  
**System State:** Container orchestration layer running, DNOS not deployed

**Indicators:**
- CLI prompt shows: `GI(system-type)#` or `GI>`
- NCCs may be partially up
- DNOS not loaded
- Configuration not active

**What's Running:**
- Container orchestration (Kubernetes-based)
- System management
- Image loading capability
- No routing/forwarding

**Typical Scenarios:**
- Clean system after factory reset
- Waiting for DNOS deployment
- Intentional state during upgrade
- DNOS failed to deploy

---

### 3. **BaseOS Shell Mode** (Intermediate State)
**Severity:** 🟡 Warning  
**System State:** Linux Ubuntu shell running, GI container not started or accessible

**Indicators:**
- CLI prompt shows: `dn@WKY1BC7400002B2:~$` (bash shell)
- Credentials: `dn` / `drivenets` (same as ONIE!)
- Standard Linux commands available
- Need to run `dncli` to enter GI mode

**What's Running:**
- BaseOS (Ubuntu Linux)
- Docker containers (may or may not include GI)
- System services
- No DNOS routing/forwarding

**Typical Scenarios:**
- Immediately after BaseOS installation from ONIE
- GI container failed to start automatically
- Manual boot to Ubuntu from GRUB menu
- Debugging/troubleshooting mode

**How to Proceed:**
```bash
dn@WKY1BC7400002B2:~$ dncli
dnroot@0.0.0.0's password: dnroot
GI# ← Now in GI mode
```

---

### 4. **ONIE Rescue Mode** (Bootloader Level)
**Severity:** 🔴 Critical  
**System State:** Open Network Install Environment - lowest level recovery

**Indicators:**
- CLI prompt shows: `ONIE:/ #`
- Credentials: `dn` / `drivenets`
- ONIE commands available: `onie-syseeprom`, `onie-nos-install`, `parted`
- Only accessible via console

**What's Running:**
- ONIE bootloader
- Basic Linux environment
- Partition management tools
- Network OS installation capability

**Typical Scenarios:**
- BaseOS corrupted or deleted
- Factory reset dropped to ONIE instead of GI
- Partition table issues
- Manual ONIE rescue entry

**How to Proceed:**
1. Check EEPROM: `onie-syseeprom`
2. Check partitions: `parted -l`
3. Remove partition 3 if "UBUNTU": `parted /dev/sda rm 3`
4. Install BaseOS: `onie-nos-install http://minio.../drivenets_baseos_*.tar`
5. Wait 20-40 minutes for install + reboot to GI mode

---

### 5. **Standalone Mode** (NCC Failure)
**Severity:** 🟠 High  
**System State:** System running but with reduced redundancy

**Indicators:**
- `NCC: 1/2 UP (Standalone)` - One NCC failed
- `NCC: 0/2 UP` - All NCCs failed (escalates to RECOVERY)
- Uptime may show
- Some interfaces may be up (depending on failure)

**What's Running:**
- Surviving NCC handles all control plane
- Data plane may be partially functional
- No control plane redundancy
- Risk of full outage if remaining NCC fails

**Typical Scenarios:**
- Hardware failure (NCC card)
- Software crash on one NCC
- Configuration error affecting NCC
- Network connectivity loss to NCC

---

### 4. **Partial Failure** (Service Degradation)
**Severity:** 🟡 Warning  
**System State:** System booted but not fully functional

**Indicators:**
- All NCCs up: `NCC: 2/2 UP`
- Uptime shows normal
- Some interfaces down: `Total: 2004 configured / 50 UP`
- Services partially UP: `FXC: 100/1000 UP`

**What's Running:**
- DNOS fully loaded
- Control plane active
- Partial data plane functionality
- Configuration applied

**Typical Scenarios:**
- Physical connectivity issues
- Configuration errors (specific services)
- License limitations
- Resource exhaustion (memory, CPU)

---

## Detection Methods

### Automatic Detection in SCALER

#### 1. **running.txt Header Parsing**
The monitor automatically detects recovery from config header:

```python
# From monitor.py - _detect_recovery_from_config()

# Check 1: All NCCs down
if "NCC: 0/1 UP" or "NCC: 0/2 UP":
    → RECOVERY MODE

# Check 2: No uptime + all interfaces down
if "Uptime: N/A" AND "Total: X configured / 0 UP":
    → LIKELY RECOVERY MODE
```

**Files Updated:**
- `operational.json`: Sets `recovery_mode_detected: true`
- Monitor table: Shows status as `[bold red]RECOVERY[/bold red]`
- Wizard table: Shows status as `[bold red]RECOVERY[/bold red]`

#### 2. **SSH Prompt Detection**
When connecting via SSH, the wizard checks the prompt:

```python
# From interactive_scale.py - _check_single_device_status()

if 'RECOVERY' in ssh_prompt:
    → RECOVERY MODE
    
if 'GI(' in ssh_prompt or 'GI#' in ssh_prompt:
    → GI MODE
```

#### 3. **Console Detection** (PE-2 Specific)
For devices with console access, direct serial connection:

```python
# From monitor.py - check_pe2_recovery_via_console()

# Connects to console server
# Reads serial output
if 'recovery' in console_output:
    → RECOVERY MODE DETECTED
```

**Trigger Conditions:**
- Normal SSH connection fails
- Config extraction failed
- Config stale (>15 minutes old)
- No `running.txt` exists

---

## Root Causes

### Hardware Failures

| Issue | Symptoms | Recovery Method |
|-------|----------|-----------------|
| **NCC card failure** | `NCC: 0/X UP` or `Standalone` | RMA hardware, restore from backup |
| **Power supply failure** | NCCs cycling, random reboots | Replace PSU |
| **Memory failure** | Boot loops, kernel panics | RMA hardware |
| **Disk corruption** | File system errors, read-only FS | Factory reset + reload |

### Software Issues

| Issue | Symptoms | Recovery Method |
|-------|----------|-----------------|
| **Version mismatch** | Boot stuck, RECOVERY mode | Load compatible versions |
| **Image corruption** | RECOVERY mode, boot failure | Reload images from scratch |
| **Config syntax error** | Services won't start, partial up | `rollback 0`, fix config |
| **Memory leak** | Services crash, OOM kills | Reboot, upgrade to fixed version |
| **Failed upgrade** | Stuck in GI mode | Complete upgrade or rollback |

### Configuration Errors

| Issue | Symptoms | Recovery Method |
|-------|----------|-----------------|
| **Too many interfaces** | Commit fails, timeout | Factory reset + load override |
| **Invalid BGP config** | BGP won't start, neighbors down | `rollback 0`, fix config |
| **Loop in config** | Hangs during load | Factory reset, fix offline |
| **Resource exhaustion** | Services won't deploy | Reduce scale, reboot |

### Operational Errors

| Issue | Symptoms | Recovery Method |
|-------|----------|-----------------|
| **Wrong load command** | Config wiped, empty system | Restore from backup |
| **Accidental delete** | Services missing, interfaces down | Restore from backup |
| **Network isolation** | Can't reach device, no updates | Console access, fix network |
| **Wrong credentials** | Can't log in | Console access, reset password |

---

## Recovery Procedures

### Procedure 1: RECOVERY Mode → GI Mode → DNOS

**Use Case:** Device in RECOVERY mode, need to restore to operational state

**Prerequisites:**
- Console or SSH access
- Image URLs (DNOS, GI, BaseOS) from Jenkins or known-good versions
- Device knowledge (system_type, hostname, ncc-id)

**SCALER Wizard Path:**
```
Main Menu → [3] Configure Device → [S] 🔧 System Restore
```

**Manual Steps:**

```bash
# Step 1: Confirm you're in RECOVERY mode
dnRouter(RECOVERY)# show system info
# Verify prompt and state

# Step 2: Factory reset to GI mode
dnRouter(RECOVERY)# request system restore factory-default
This will erase all configuration and return to GI mode.
Continue? [yes/no]: yes
# Wait 2-10 minutes for GI mode

# Step 3: Confirm GI mode
GI(SA-36CD-S)# show system info
# Prompt should show GI

# Step 4: Load images (if needed)
GI# request system target-stack load http://jenkins.example.com/dnos_26.1.0.1.tar
GI# request system target-stack load http://jenkins.example.com/gi_26.1.0.59.tar
GI# request system target-stack load http://jenkins.example.com/baseos_2.26.tar
# Wait for downloads and validation

# Step 5: Deploy DNOS
GI# request system deploy system-type SA-36CD-S name YOR_PE-2 ncc-id 0
# Wait 15-60 minutes for full deployment

# Step 6: Verify DNOS mode
YOR_PE-2# show system info
YOR_PE-2# show system stack
# Confirm all NCCs up, versions match

# Step 7: Restore configuration
YOR_PE-2# configure
YOR_PE-2(cfg)# load override /path/to/backup_config.txt
YOR_PE-2(cfg)# commit check
YOR_PE-2(cfg)# commit
```

**SCALER Automated Flow:**
- Wizard detects recovery from `operational.json`
- Loads previous device knowledge (system_type, hostname, versions)
- Prompts for confirmation
- Executes `request system restore factory-default`
- Redirects to Image Upgrade wizard
- User selects Jenkins branch + artifacts
- Wizard deploys DNOS with saved parameters
- Offers to restore configuration from backup

---

### Procedure 2: Standalone Mode (NCC Failure) → Normal

**Use Case:** One NCC failed, system running in standalone

**Detection:**
```
# SYSTEM section in running.txt
#   • NCC: 1/2 UP (Standalone)
```

**Recovery:**

**Option A: Soft Recovery (Configuration Issue)**
```bash
# Check NCC status
show system ncc status

# Check for config errors
show logging | include ERROR
show logging | include NCC

# Try reload NCC service (if software issue)
request system ncc reload ncc-id 1

# Wait and verify
show system ncc status
# Should show: NCC: 2/2 UP
```

**Option B: Hard Recovery (Hardware Issue)**
```bash
# Identify failed NCC
show system ncc status
show system hardware

# Power cycle the NCC card (if accessible)
request system power-cycle ncc-id 1

# If still failed → RMA required
# Document: serial number, failure symptoms, logs
# Contact DriveNets support for RMA process
```

---

### Procedure 3: Partial Failure → Full Operational

**Use Case:** System booted but many services/interfaces down

**Diagnosis:**
```bash
# Check system health
show system info
show system stack
show logging | include ERROR | count

# Check specific failures
show interfaces summary | include down
show evpn-vpws-fxc summary
show bgp l2vpn evpn summary
```

**Common Fixes:**

**Configuration Errors:**
```bash
# Roll back to last good config
configure
rollback 1
commit check
commit
```

**Service Restart:**
```bash
# Restart specific services (via DNOR/console if available)
request system service restart <service-name>
```

**Full Reboot:**
```bash
# Last resort: reboot device
request system reboot
Reboot in 0:05:00 ? [yes/no]: yes
```

---

### Procedure 4: Failed Upgrade → Rollback or Complete

**Use Case:** Upgrade started but device stuck in GI mode or RECOVERY

**Option A: Complete the Upgrade**
```bash
# If in GI mode with images loaded
GI# show system software
# Verify images are loaded

GI# request system deploy system-type <type> name <hostname> ncc-id <id>
# Wait for deployment
```

**Option B: Rollback to Previous Version**
```bash
# If in GI mode
GI# show system software
# Note previous version images

GI# request system software delete <unwanted-version>
GI# request system deploy <previous-version>
```

**Option C: Full Recovery**
```bash
# If stuck in RECOVERY
# Follow Procedure 1 (RECOVERY → GI → DNOS)
# Use known-good version from operational.json backup
```

---

### Procedure 5: Configuration Restore from Backup

**Use Case:** Need to restore configuration after factory reset or corruption

**SCALER Automated:**
```
Main Menu → Select Device → [1] Saved Configs → Select backup → [2] Push
```

**Manual:**
```bash
# Copy config to device (from workstation)
scp /path/to/backup_config.txt dnroot@device:/tmp/

# Load on device
ssh dnroot@device
configure
load override /tmp/backup_config.txt
commit check  # Always check first!
commit
```

**Partial Restore (Specific Hierarchy):**
```bash
configure
load merge /tmp/backup_config.txt
# Restores only new sections, doesn't delete existing
commit check
commit
```

---

## Prevention

### Pre-Upgrade Checklist

- [ ] **Backup current config:** `show config | no-more > backup_$(date +%Y%m%d).txt`
- [ ] **Verify version compatibility:** DNOS/GI/BaseOS major versions match
- [ ] **Check disk space:** Sufficient for new images
- [ ] **Test in lab:** Upgrade procedure on identical hardware
- [ ] **Document rollback plan:** Keep previous image URLs
- [ ] **Schedule maintenance window:** Expect 30-60 minute downtime

### Configuration Best Practices

- [ ] **Always use commit check:** Validates syntax before applying
- [ ] **Save before major changes:** Config backups in SCALER or externally
- [ ] **Test on one device first:** Multi-device configs tested on PE-1 before PE-2
- [ ] **Use rollback feature:** `rollback 1` to undo last commit
- [ ] **Monitor after changes:** Watch logs for 15-30 minutes post-change
- [ ] **Document changes:** Track what was changed and why

### Monitoring and Alerting

- [ ] **SCALER monitor running:** Detects config changes and failures
- [ ] **Recovery detection active:** Monitor checks operational.json
- [ ] **Console access configured:** PE-2 console for out-of-band access
- [ ] **Alert on NCC down:** Immediate notification if `NCC: X/Y UP` changes
- [ ] **Config drift detection:** Alert if running differs from backup

### Maintenance

- [ ] **Regular backups:** Daily automated config extraction
- [ ] **Version tracking:** Document DNOS/GI/BaseOS versions in use
- [ ] **Test recovery procedures:** Quarterly test of backup restore
- [ ] **Hardware monitoring:** Check NCC status, temperatures, power
- [ ] **Software updates:** Stay current with bug fix releases

---

## Quick Reference

### Detection Patterns

| Pattern | Meaning | Severity |
|---------|---------|----------|
| `NCC: 0/X UP` | All NCCs down | 🔴 RECOVERY |
| `NCC: 1/2 UP (Standalone)` | One NCC down | 🟠 Warning |
| `Uptime: N/A` + `0 UP` | Boot failure | 🔴 RECOVERY |
| `GI(type)#` prompt | GI mode | 🟡 Not deployed |
| `RECOVERY` in prompt | Recovery mode | 🔴 Boot failed |

### Recovery Commands

| Command | Purpose | Mode |
|---------|---------|------|
| `request system restore factory-default` | RECOVERY → GI | RECOVERY |
| `request system deploy system-type <type> name <name> ncc-id <id>` | GI → DNOS | GI |
| `request system target-stack load <url>` | Load image | GI |
| `rollback 0` | Clear dirty candidate | Config |
| `rollback 1` | Undo last commit | Config |
| `commit check` | Validate config | Config |
| `load override <file>` | Replace config | Config |

### SCALER Wizard Paths

| Task | Path |
|------|------|
| System Restore | Main → Device → [S] System Restore |
| Image Upgrade | Main → Device → [6] Image Upgrade |
| Config Restore | Main → Device → [1] Saved Configs |
| Delete/Reset | Main → Device → [4] Delete Hierarchy |

---

## Troubleshooting Matrix

| Symptom | Check | Likely Cause | Fix |
|---------|-------|--------------|-----|
| Can't SSH to device | Ping, console access | Network issue, device down | Console recovery, check network |
| Prompt shows RECOVERY | `show system info` | Boot failure | Factory reset → reload images |
| NCC: 0/X UP | `show system ncc status` | NCC failure | Reload NCC, RMA if HW |
| All interfaces down | `show interfaces summary` | Config error, boot issue | Check logs, rollback config |
| Services won't start | `show logging` | Config syntax, resources | Commit check, reduce scale |
| Upgrade stuck in GI | `show system software` | Deploy not triggered | Run deploy command |
| Commit fails | `commit check` | Syntax error, scale limit | Fix syntax, use factory reset |
| Memory issues | `show system resources` | Leak, too many services | Reboot, reduce scale |

---

## Support Contacts

For issues not covered in this guide:

1. **SCALER Issues:** Check `docs/DEVELOPMENT_GUIDELINES.md`
2. **DriveNets Support:** Contact TAC with device serial, logs, and symptoms
3. **Emergency:** Use console access, factory reset if necessary

---

**Document Version:** 1.0  
**Author:** SCALER Project  
**Based on:** Field experience with PE-1, PE-2, PE-4 (SA-36CD-S, CL-86 platforms)
