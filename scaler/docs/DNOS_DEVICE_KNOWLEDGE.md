# DNOS Device Knowledge Base
## Accumulated knowledge from Drivenets device interactions

---

## 🔌 SSH Connection Methods

### Method 1: Direct CLI (Preferred)
```bash
sshpass -p 'dnroot' ssh -o StrictHostKeyChecking=no dnroot@<device>
```
- Connects directly to DNOS CLI
- Prompt format: `HOSTNAME(timestamp)#` or `HOSTNAME#`

### Method 2: If "CLI is not running"
```bash
ssh dnroot@<device>
# Answer "yes" to enter BaseOS shell
# Then use vtysh for CLI commands:
vtysh -c "show evpn-vpws-fxc"
```

### Method 3: Shell Mode from CLI
```
run start shell
Password: dnroot
# Now in Linux shell, use vtysh -c for CLI commands
```

---

## 🖥️ Device Hostnames/IPs

| Device | Hostname | IP/FQDN | Loopback | Credentials |
|--------|----------|---------|----------|-------------|
| PE-1 | YOR_PE-1 | wk31d7vv00023 | 1.1.1.1 | dnroot/dnroot |
| PE-2 | YOR_PE-2 | 100.64.0.220 | 2.2.2.2 | dnroot/dnroot |
| PE-4 | YOR_PE-4 | kvm108-cl408d-ncc0 | 4.4.4.4 | dnroot/dnroot |

---

## 📋 DNOS CLI Syntax Reference

### Show Commands (CORRECT)
```
show config interfaces                    # View interface config
show config network-services              # View network services
show config network-services evpn-vpws-fxc instance FXC-1
show evpn-vpws-fxc                       # Operational state
show evpn-vpws-fxc instance FXC-901      # Specific service
show evpn-vpws-fxc | no-more             # Disable paging
show evpn-vpws-fxc | include "FXC-90"    # Filter output
show evpn-vpws-fxc | count               # Count lines
show interfaces ph901.1                   # Interface status
show bgp l2vpn evpn summary              # BGP EVPN neighbors
show ethernet-segment                     # MH ES status
```

### Show Commands (WRONG - Don't use)
```
show running-config      # WRONG - use "show config"
show configuration       # WRONG - use "show config"
terminal length 0        # WRONG - use "| no-more" suffix
```

### Configuration Mode
```
configure                                 # Enter config mode
interfaces                               # Enter interfaces hierarchy
  ph901                                  # Parent interface (2-space indent)
    admin-state enabled
  !
  ph901.1                                # Sub-interface (sibling, not child!)
    admin-state enabled
    ipv4-address 100.100.200.0/31
    vlan-tags outer-tag 1 inner-tag 901 outer-tpid 0x8100
  !
!
network-services
  evpn-vpws-fxc
    instance FXC-901
      protocols
        bgp 1234567
          export-l2vpn-evpn route-target 1234567:901
          import-l2vpn-evpn route-target 1234567:901
          route-distinguisher 1.1.1.1:901
        !
      !
      transport-protocol
        mpls
          control-word enabled
        !
      !
      admin-state enabled
      interface ph901.1
      !
    !
  !
  multihoming
    interface ph901.1
      esi arbitrary value 00:99:01:00:00:00:00:00:01
      redundancy-mode single-active
      designated-forwarder
        algorithm highest-preference value 100
      !
    !
  !
!
commit
```

### Delete Syntax
```
configure
no interfaces ph901.1                    # Delete sub-interface
no interfaces ph901                      # Delete parent
no network-services evpn-vpws-fxc instance FXC-901
no network-services multihoming interface ph901.1
commit
```

---

## 📊 FXC Service Output Format

```
| Instance name | State | Time in state | Local AC | AC state | Actual local homing type | Normalized-VID | Neighbors |
|---------------|-------|---------------|----------|----------|--------------------------|----------------|-----------|
| FXC-901       | down  | 0:00:00       | ph901.1  | down (disabled) / blocking-all | multi-homed-single-active | outer: 1 inner: 901 | 4.4.4.4(C/V2/M1) |
```

### AC State Meanings
| AC State | Meaning |
|----------|---------|
| `down (disabled)` | admin-state disabled |
| `down / blocking-all` | NDF state (not designated forwarder) |
| `up / forwarding-all` | DF state (designated forwarder, forwarding traffic) |

### Neighbor Flags
| Flag | Meaning |
|------|---------|
| C | Control-word enabled |
| V1 | Single-VID normalization |
| V2 | Double-VID normalization |
| M1 | VLAN Aware FXC |
| M2 | Default FXC |

---

## 🔍 xraycli Commands (Shell Mode)

```bash
# In shell mode:
xraycli query interface list | grep "^ph"

# Output format:
# interface_name  UBFD_STATE  EFM_STATE  BER_STATE  LINK_STATE  evpn_vpws_fxc  evpn_vpws_fxc_state
# ph1.1  UBFD_FSM_S_DISABLED  EFM_FSM_S_ADMIN_CMC_UP  BER_FSM_S_ADMIN_DOWN  LINK_FSM_S_SYNCED  1  UP
```

### CMC Listening Detection
- `evpn_vpws_fxc=1` → CMC IS listening for FXC events
- `evpn_vpws_fxc=0` → CMC NOT listening (SW-224670 bug if service configured)

---

## 🐛 Known Issues

### pexpect Connection Issues
1. **ANSI escape codes** - Use regex to clean: `re.sub(r'\x1b\[[0-9;]*m', '', output)`
2. **"-- More --" paging** - Always use `| no-more` suffix
3. **Command overlap** - Add `time.sleep(2-3)` between commands
4. **Prompt detection** - Use `#` as prompt marker, handle timestamps

### SSH Timeouts
- Default timeout: 15-30 seconds
- For large outputs (1000+ interfaces): 60+ seconds
- For `show evpn-vpws-fxc`: 15-20 seconds

---

## 📁 File Locations on Devices

| Path | Content |
|------|---------|
| `/core/traces/routing_engine/rib-manager_traces-*` | RIB manager traces |
| `/core/traces/cluster_manager/cluster_manager_protocols-*` | CMC traces |
| `/tmp/` | Temp files (can write here) |

---

## 🔧 Automation Tips

### Python pexpect Pattern
```python
import pexpect
import time
import re

child = pexpect.spawn('ssh -o StrictHostKeyChecking=no dnroot@device', 
                      timeout=60, encoding='utf-8', maxread=2000000)

# Handle password
i = child.expect(['password:', 'yes/no', pexpect.TIMEOUT], timeout=15)
if i == 1:
    child.sendline('yes')
    child.expect('password:')
child.sendline('dnroot')

# Wait for prompt
child.expect('#', timeout=20)

# Run command with no-more
child.sendline('show evpn-vpws-fxc | no-more')
time.sleep(5)
child.expect('#', timeout=30)

# Clean output
output = child.before
clean = re.sub(r'\x1b\[[0-9;]*m', '', output)

child.sendline('exit')
child.close()
```

### Shell Mode for grep
```python
# Enter shell
child.sendline('run start shell')
child.expect(['Password:', 'password:'], timeout=10)
child.sendline('dnroot')
child.expect(['\\$', '#'], timeout=10)

# Run vtysh with grep
child.sendline('vtysh -c "show evpn-vpws-fxc" | grep "FXC-901"')
child.expect(['\\$', '#'], timeout=30)
```

---

## 📊 Test Scenario Summary (ph901-ph911)

| # | Interface | PE-1 Config | PE-2 Config | Expected State |
|---|-----------|-------------|-------------|----------------|
| 1 | ph901.1 | admin-disabled | admin-disabled | DOWN |
| 2 | ph902.1 | sub-if admin-disabled | sub-if admin-disabled | DOWN |
| 3 | ph903.1 | no IP | no IP | DOWN |
| 4 | ph904.1 | FXC admin-disabled | FXC admin-disabled | DOWN |
| 5 | ph905.1 | mismatched RT | normal RT | PE-1 DOWN, PE-2 UP |
| 6 | ph906.1 | low DF pref (50) | high DF pref (100) | PE-1 DOWN (NDF), PE-2 UP (DF) |
| 7 | ph907.1 | single-homed | N/A | UP |
| 8 | ph908.1 | high DF pref (100) | low DF pref (50) | PE-1 UP (DF), PE-2 DOWN (NDF) |
| 9 | ph909.1 | normal | normal | DOWN (no PE-4 service) |
| 10 | ph910.1 | not attached to FXC | N/A | DOWN |
| 11 | ph911.1 | all valid | all valid | UP |

---

## 🔄 Version: Updated 2026-01-07








