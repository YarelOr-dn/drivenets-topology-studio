# ONIE Rescue Mode - Complete Guide

## What is ONIE Rescue Mode?

**ONIE (Open Network Install Environment)** is the **lowest level bootloader** in the DriveNets stack hierarchy:

```
┌─────────────────────────────────────────────────────────────────┐
│                      STACK HIERARCHY                            │
├─────────┬─────────┬─────────┬─────────┬─────────────────────────┤
│  ONIE   │Firmware │ BaseOS  │   GI    │         DNOS            │
│  ◄──────┴─────────┴─────────┴─────────┴─────────────────────────┤
│ Lowest  │         │         │         │       Highest           │
│ Level   │         │         │         │       Level             │
└─────────┴─────────┴─────────┴─────────┴─────────────────────────┘
```

### When Does ONIE Rescue Activate?

ONIE rescue mode activates when:
1. **BaseOS is corrupted or missing**
2. **Factory reset executed** (sometimes drops to ONIE instead of GI)
3. **Partition table issues**
4. **Manual ONIE rescue entry** (from GRUB menu)

**In your case:** `request system restore factory-default` triggered ONIE rescue mode instead of GI mode, indicating BaseOS needs reinstallation.

---

## ONIE Rescue Mode Characteristics

### Access Credentials
```
Username: dn
Password: drivenets
```

**⚠️ CRITICAL:** These are **different** from:
- GI mode: `dnroot / dnroot`
- DNOS mode: `dnroot / dnroot`
- Console server: `dn / drive1234`

### Console Prompt
```
ONIE:/ # ← You're at the root shell
```

### Available Commands
```bash
onie-syseeprom   # Check hardware EEPROM (serial, MAC, etc.)
onie-nos-install # Install a network OS
parted           # Partition management
fdisk            # Disk partitioning
mount            # Mount filesystems
```

---

## ONIE Rescue Recovery Procedure

### Step 1: Verify Hardware EEPROM

**Purpose:** Ensure hardware identity is intact

```bash
ONIE:/ # onie-syseeprom
```

**Expected output:**
```
TlvInfo Header:
   Id String:    TlvInfo
   Version:      1
   Total Length: 191
TLV Name             Code Len Value
-------------------- ---- --- -----
Product Name         0x21  17 SA-36CD-S
Part Number          0x22  14 DNP-SA-36CD-S
Serial Number        0x23  14 WKY1BC7400002B2  ← Should match PE-2
Base MAC Address     0x24   6 00:1B:21:D4:00:02
Manufacture Date     0x25  19 2024-01-15T00:00:00
Device Version       0x26   1 1
Label Revision       0x27   4 A01
Platform Name        0x28  13 x86_64-accton
ONIE Version         0x29  14 2022.05-V2.0.3
...
```

**✅ Valid:** Serial number matches PE-2, MAC address present  
**❌ Invalid:** Missing serial, corrupted data → Hardware issue, contact support

---

### Step 2: Check Partition Table

**Purpose:** Identify problematic partitions that block BaseOS installation

```bash
ONIE:/ # parted -l
```

**Example output:**
```
Model: ATA INTEL SSDSC2KB01 (scsi)
Disk /dev/sda: 1000GB
Sector size (logical/physical): 512B/512B
Partition Table: gpt

Number  Start   End     Size    File system  Name                  Flags
 1      1049kB  524MB   523MB   ext4         ONIE-BOOT             boot
 2      524MB   50GB    49.5GB  ext4         ONIE-RESCUE
 3      50GB    500GB   450GB   ext4         UBUNTU                ← PROBLEM!
 4      500GB   1000GB  500GB   ext4         BASEOS
```

**Problem partition:** `#3 UBUNTU` - leftover from previous BaseOS  
**Why it's a problem:** Conflicts with new BaseOS installation

---

### Step 3: Remove Problematic Partition

**⚠️ CRITICAL:** Only remove partition 3 if it's labeled "UBUNTU"

```bash
ONIE:/ # parted /dev/sda rm 3
Information: You may need to update /etc/fstab.
```

**Verify removal:**
```bash
ONIE:/ # parted -l
```

**Expected:** Partition 3 should be gone:
```
Number  Start   End     Size    File system  Name                  Flags
 1      1049kB  524MB   523MB   ext4         ONIE-BOOT             boot
 2      524MB   50GB    49.5GB  ext4         ONIE-RESCUE
 4      500GB   1000GB  500GB   ext4         BASEOS
```

---

### Step 4: Install BaseOS

**Prerequisites:**
- Partition 3 removed (if it existed)
- EEPROM valid
- BaseOS package URL ready

#### Option A: Install via HTTP (Recommended)

```bash
ONIE:/ # onie-nos-install http://minio-ssd.dev.drivenets.net:9000/dnpkg-60days/drivenets_baseos_2.25104397329.tar
```

**Progress:**
```
Downloading BaseOS...
[####################] 100%
Extracting archive...
Installing to /dev/sda4...
Syncing filesystems...
Installation complete.
Rebooting to BaseOS...
```

#### Option B: Install via USB

1. Download BaseOS tarball to USB drive
2. Mount USB in ONIE:
   ```bash
   ONIE:/ # mkdir /mnt/usb
   ONIE:/ # mount /dev/sdb1 /mnt/usb
   ONIE:/ # onie-nos-install /mnt/usb/drivenets_baseos_2.25104397329.tar
   ```

#### Option C: Install via TFTP

```bash
ONIE:/ # onie-nos-install tftp://10.0.0.1/baseos/drivenets_baseos_2.25104397329.tar
```

---

### Step 5: Verify Boot to BaseOS/GI

After `onie-nos-install` completes, the device **reboots automatically**.

**Expected boot sequence:**
```
ONIE -> BaseOS -> GI Mode
```

**Console output after reboot:**
```
Ubuntu 20.04.3 LTS drivenets ttyS0

drivenets login: dnroot
Password: dnroot

dnroot@drivenets:~$ gicli
GI# ← Success! You're in GI mode
```

---

## Recovery Decision Tree

```
┌──────────────────────────────┐
│ PE-2 in ONIE Rescue Mode?    │
└────────────┬─────────────────┘
             │
             ├─ Check EEPROM (onie-syseeprom)
             │  ├─ Valid? → Continue
             │  └─ Invalid? → Contact support
             │
             ├─ Check Partitions (parted -l)
             │  ├─ Partition 3 "UBUNTU" exists?
             │  │  └─ Yes → Remove it (parted /dev/sda rm 3)
             │  └─ No → Continue
             │
             ├─ Install BaseOS (onie-nos-install <URL>)
             │  ├─ HTTP URL (minio server)
             │  ├─ USB drive
             │  └─ TFTP server
             │
             ├─ Device reboots automatically
             │
             └─ Expected: Boot to GI mode
                 ├─ Success → Proceed with DNOS deployment
                 └─ Failed → Check logs, retry
```

---

## Common Issues in ONIE Rescue

### 1. Network Not Working
```bash
# Check interfaces
ONIE:/ # ifconfig -a

# Bring up management interface
ONIE:/ # ifconfig eth0 up

# Set IP manually if DHCP fails
ONIE:/ # ifconfig eth0 100.64.8.39 netmask 255.255.255.0
ONIE:/ # route add default gw 100.64.8.1
```

### 2. Cannot Reach Minio Server
```bash
# Test connectivity
ONIE:/ # ping -c 3 minio-ssd.dev.drivenets.net

# Check DNS
ONIE:/ # cat /etc/resolv.conf
ONIE:/ # echo "nameserver 8.8.8.8" >> /etc/resolv.conf
```

### 3. Partition Removal Fails
```bash
# Force unmount if mounted
ONIE:/ # umount /dev/sda3

# Check if partition is in use
ONIE:/ # lsof | grep sda3

# Retry removal
ONIE:/ # parted /dev/sda rm 3
```

### 4. BaseOS Install Hangs
```bash
# Check download progress
ONIE:/ # ps aux | grep wget
ONIE:/ # tail -f /var/log/onie.log

# If stuck, kill and retry
ONIE:/ # killall wget
ONIE:/ # onie-nos-install <URL>
```

---

## Integration with System Restore Wizard

### Detection Logic

When wizard connects to PE-2 via console and sees:
```
ONIE:/ #  ← ONIE prompt detected
```

**Action:** Wizard should:
1. Detect ONIE rescue mode
2. Display ONIE recovery plan
3. Offer automated or manual ONIE recovery

### Automated ONIE Recovery Flow

```python
if detected_mode == "ONIE_RESCUE":
    # Step 1: Check EEPROM
    channel.send("onie-syseeprom\n")
    output = read_output()
    if "Serial Number" not in output:
        show_error("EEPROM invalid - contact support")
        return
    
    # Step 2: Check partitions
    channel.send("parted -l\n")
    output = read_output()
    if "UBUNTU" in output:
        # Remove partition 3
        channel.send("parted /dev/sda rm 3\n")
        time.sleep(2)
    
    # Step 3: Install BaseOS
    baseos_url = get_baseos_url_from_knowledge(device)
    channel.send(f"onie-nos-install {baseos_url}\n")
    
    # Step 4: Wait for reboot to GI
    wait_for_gi_mode(timeout=1200)  # 20 minutes
```

---

## BaseOS Version Selection

### From Previous Knowledge
If PE-2 was previously running DNOS v25.1:
```json
"previous_baseos_version": "2.25104397329",
"baseos_url": "http://minio-ssd.dev.drivenets.net:9000/dnpkg-60days/drivenets_baseos_2.25104397329.tar"
```

**Use this URL** for BaseOS installation in ONIE.

### If No Previous Knowledge
Use **latest stable** for the target DNOS version:
- DNOS v25.1 → BaseOS 2.25104397329
- DNOS v19.3 → BaseOS 2.19xxxxx

**Minio bucket priority:**
1. `dnos-rel` (permanent, stable)
2. `dnpkg-60days` (QA tested)
3. `dnpkg-30days` (recent dev)

---

## Manual ONIE Recovery (Console-Based)

If wizard automation isn't available:

### Step-by-Step Manual Procedure

1. **Connect to PE-2 console:**
   ```bash
   ssh dn@console-b15
   # Select: [3] Port access
   # Port: [13] PE-2
   ```

2. **Login to ONIE:**
   ```
   Username: dn
   Password: drivenets
   ```

3. **Verify EEPROM:**
   ```bash
   ONIE:/ # onie-syseeprom | grep -E "Serial|Product"
   Product Name         0x21  17 SA-36CD-S
   Serial Number        0x23  14 WKY1BC7400002B2
   ```

4. **Check and fix partitions:**
   ```bash
   ONIE:/ # parted -l
   # If partition 3 "UBUNTU" exists:
   ONIE:/ # parted /dev/sda rm 3
   ```

5. **Install BaseOS:**
   ```bash
   ONIE:/ # onie-nos-install http://minio-ssd.dev.drivenets.net:9000/dnpkg-60days/drivenets_baseos_2.25104397329.tar
   # Wait 10-20 minutes for download + install + reboot
   ```

6. **Verify GI mode:**
   ```
   # After reboot, login:
   Username: dnroot
   Password: dnroot
   
   dnroot@drivenets:~$ gicli
   GI# ← Success!
   ```

---

## Credentials Reference Card

| Mode | Username | Password | Prompt | Access GI |
|------|----------|----------|--------|-----------|
| **ONIE Rescue** | `dn` | `drivenets` | `ONIE:/ #` | Install BaseOS first |
| **BaseOS Shell** | `dn` | `drivenets` | `dn@WKY1BC7400002B2:~$` | Run `dncli` |
| **GI Mode** | `dnroot` | `dnroot` | `GI#` | Already there |
| **DNOS Mode** | `dnroot` | `dnroot` | `PE-2#` | N/A |
| **DNOS Recovery** | `dnroot` | `dnroot` | `dnRouter(RECOVERY)#` | Factory reset first |
| **Console Server** | `dn` | `drive1234` | `[Console-B15]>` | N/A |

**IMPORTANT:** BaseOS Shell uses the same credentials as ONIE (`dn` / `drivenets`), NOT the DNOS/GI credentials (`dnroot` / `dnroot`)!

---

## Time Estimates

| Operation | Duration | Notes |
|-----------|----------|-------|
| EEPROM check | 5 sec | Instant |
| Partition check | 10 sec | Instant |
| Partition removal | 5 sec | Instant |
| BaseOS download | 5-10 min | Depends on network |
| BaseOS extraction | 2-5 min | Disk I/O intensive |
| BaseOS install | 5-10 min | Partition formatting + copy |
| Reboot to GI | 5-10 min | Hardware init + OS boot |
| **Total ONIE Recovery** | **20-40 min** | End-to-end |

---

## Troubleshooting ONIE Rescue

### Issue: Stuck in ONIE, won't boot BaseOS

**Symptom:** After `onie-nos-install`, device reboots back to ONIE

**Causes:**
1. BaseOS install failed silently
2. GRUB boot order wrong
3. Partition table corrupted

**Fix:**
```bash
# Check install log
ONIE:/ # cat /var/log/onie.log

# Manual GRUB check
ONIE:/ # fdisk -l /dev/sda
# Look for bootable flag on BaseOS partition

# Retry install with verbose
ONIE:/ # onie-nos-install -v <URL>
```

---

### Issue: "No space left on device"

**Symptom:** BaseOS install fails with disk space error

**Cause:** Partition 3 not removed, taking up space

**Fix:**
```bash
ONIE:/ # df -h
ONIE:/ # parted -l
ONIE:/ # parted /dev/sda rm 3
ONIE:/ # parted /dev/sda print free  # Verify free space
```

---

### Issue: Download fails

**Symptom:** `onie-nos-install` can't download from Minio

**Causes:**
1. Network not configured
2. Minio URL expired (>60 days for QA bucket)
3. DNS not working

**Fix:**
```bash
# Test network
ONIE:/ # ping -c 3 8.8.8.8  # Test internet
ONIE:/ # ping -c 3 minio-ssd.dev.drivenets.net  # Test Minio

# If ping fails, configure manually:
ONIE:/ # ifconfig eth0 100.64.8.39 netmask 255.255.255.0
ONIE:/ # route add default gw 100.64.8.1
ONIE:/ # echo "nameserver 8.8.8.8" > /etc/resolv.conf

# Retry download
ONIE:/ # onie-nos-install <URL>
```

---

## BaseOS Shell Mode

### What is BaseOS Shell?

**BaseOS Shell** is the **Linux Ubuntu shell** that runs **before entering GI mode**. It's an intermediate state in the boot sequence:

```
ONIE → BaseOS → BaseOS Shell → (run dncli) → GI Mode → DNOS
              └─ dn@hostname:~$ ◄── YOU ARE HERE
```

### Characteristics

**Prompt:**
```bash
dn@WKY1BC7400002B2:~$  ← Bash shell prompt
```

**Credentials:**
```
Username: dn          (same as ONIE!)
Password: drivenets   (same as ONIE!)
```

**Available Commands:**
- Standard Linux commands: `ls`, `cd`, `cat`, `ps`, `df`, etc.
- `dncli` - **Enter GI mode** (most important!)
- `gicli` - Alternative command to enter GI mode
- Docker commands: `docker ps`, `docker logs`
- System utilities: `systemctl`, `journalctl`

### When Does This Occur?

BaseOS Shell appears when:
1. **After BaseOS installation** (from ONIE) before GI starts
2. **GI container not running** - BaseOS booted but GI failed to start
3. **Manual boot interruption** - Selected "Ubuntu" from GRUB
4. **Debugging mode** - Intentionally accessing BaseOS for troubleshooting

### How to Enter GI Mode

**Simple method:**
```bash
dn@WKY1BC7400002B2:~$ dncli
Warning: Permanently added '0.0.0.0' (ED25519) to the list of known hosts.
dnroot@0.0.0.0's password: [type: dnroot]
GI# ← Success! Now in GI mode
```

**Alternative method:**
```bash
dn@WKY1BC7400002B2:~$ gicli
GI# ← Also works
```

### Wizard Handling

**System Restore wizard now detects BaseOS Shell and automatically:**
1. Detects prompt: `dn@....:~$`
2. Runs `dncli` command
3. Waits for GI prompt
4. Proceeds with DNOS deployment

**Example output:**
```
[17:20:14] ⚠ BaseOS Shell detected - entering GI mode...
[17:20:15] ✓ Entered GI mode successfully!
```

### Troubleshooting BaseOS Shell

#### Issue: `dncli` command not found

**Symptom:**
```bash
dn@WKY1BC7400002B2:~$ dncli
-bash: dncli: command not found
```

**Cause:** GI container not installed or not in PATH

**Fix:**
```bash
# Check if GI container is running
docker ps | grep gi

# If not running, check logs
journalctl -u gi-manager

# Manually start GI (if needed)
systemctl start gi-manager
```

---

#### Issue: `dncli` prompts for password but fails

**Symptom:**
```bash
dn@WKY1BC7400002B2:~$ dncli
dnroot@0.0.0.0's password:
Permission denied, please try again.
```

**Cause:** Wrong password (GI uses `dnroot` / `dnroot`)

**Fix:**
```bash
# Password is: dnroot (not drivenets!)
dn@WKY1BC7400002B2:~$ dncli
dnroot@0.0.0.0's password: dnroot
GI# ← Success
```

---

#### Issue: Stuck in BaseOS Shell, can't access GI

**Symptom:** `dncli` command doesn't exist, GI container not running

**Cause:** GI not installed in target stack

**Fix:**
```bash
# Check stack
dn@WKY1BC7400002B2:~$ sudo -i
root@WKY1BC7400002B2:~# cd /var/dnos/
root@WKY1BC7400002B2:/var/dnos# ls
# Should see: target-stack, current-stack

# Check if GI is loaded
cat target-stack/gi_version.txt

# If empty, load GI from Minio:
# (This requires manual intervention or use wizard)
```

---

## Post-ONIE Recovery: GI to DNOS Deployment

After ONIE recovery completes and device reaches **GI mode**, proceed with **standard DNOS deployment**:

### From GI Mode:

1. **Load DNOS image:**
   ```bash
   GI# request system target-stack load http://minio.../drivenets_dnos_25.1.0.464_dev.tar
   ```

2. **Deploy DNOS:**
   ```bash
   GI# request system deploy system-type SA-36CD-S name PE-2 ncc-id 0
   ```

3. **Monitor deployment:**
   ```bash
   GI# show system install
   ```

4. **After deployment completes:**
   ```
   GI# ← Will disconnect
   # Wait 10-15 minutes for DNOS to boot
   # Reconnect - should see:
   PE-2# ← DNOS mode!
   ```

---

## References

- **DNOS Version Stack:** `/home/dn/SCALER/docs/DNOS_VERSION_STACK.md`
- **System Restore Guide:** `/home/dn/SCALER/docs/RECOVERY_MODES_GUIDE.md`
- **ONIE Official Docs:** https://opencomputeproject.github.io/onie/
- **DriveNets Confluence:** [Search for "ONIE" or "BaseOS installation"]

---

**Status:** ✅ Complete ONIE Rescue Guide  
**Date:** 2026-01-27  
**Next:** Integrate ONIE detection into System Restore wizard
