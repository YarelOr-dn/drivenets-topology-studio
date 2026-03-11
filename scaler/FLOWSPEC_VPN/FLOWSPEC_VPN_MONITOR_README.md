# FlowSpec VPN Monitor - DEPRECATED

> ⚠️ **This script has been replaced by [FSVPN-WIZARD](./fsvpn_wizard.py)**
>
> Please use: `python3 /home/dn/SCALER/FLOWSPEC_VPN/fsvpn_wizard.py`
>
> See: [FSVPN_WIZARD_README.md](./FSVPN_WIZARD_README.md)

---

# (Legacy) FlowSpec VPN Monitor - Comprehensive Diagnostic Tool

## Overview

The **FlowSpec VPN Monitor** is a comprehensive diagnostic and bug detection tool for analyzing FlowSpec VPN rule installation in Drivenets DNOS. It traces the complete flow from BGP route reception to hardware TCAM programming.

## Features

### 🔍 Complete Flow Analysis
- Traces rules through: **BGP → Zebra → FPM → wb_agent → TCAM**
- Visual flow chart showing installation path
- Per-step ✓/✗ status indicators
- Expected vs Actual comparison columns

### 📊 Multi-Level Command Support
| Level | Commands Used |
|-------|---------------|
| **CLI** | `show bgp`, `show flowspec`, `show running-config` |
| **vtysh** | `show bgp flowspec`, `show ip route` |
| **xraycli** | `/wb_agent/flowspec/bgp/ipv4/rules`, `/wb_agent/flowspec/hw_counters` |
| **Internal** | `show dnos-internal routing rib-manager database flowspec` |

### 🐛 Bug Detection
- VRF-ID = 0 detection (VPN isolation broken!)
- TCAM write failures
- HW programming errors
- Unsupported NLRI/actions
- Missing flowspec-enabled interfaces
- RT import mismatches

### 📈 Monitoring Modes
1. **Wizard Mode** - Interactive guided analysis
2. **Single Analysis** - One-shot device check
3. **Daemon Mode** - Continuous monitoring every N minutes
4. **Baseline Compare** - Before/after upgrade verification

---

## Installation

```bash
# The script is self-contained, but requires 'rich' for beautiful output
pip install rich

# Make executable
chmod +x /home/dn/SCALER/FLOWSPEC_VPN/flowspec_vpn_monitor.py
```

---

## Usage

### Wizard Mode (Recommended)

Interactive wizard that guides you through device selection and analysis:

```bash
python3 flowspec_vpn_monitor.py wizard
```

### Single Device Analysis

Analyze a specific device by hostname or IP:

```bash
python3 flowspec_vpn_monitor.py analyze PE-1
python3 flowspec_vpn_monitor.py analyze 10.0.0.1
```

### Daemon Mode (Continuous Monitoring)

Start background monitoring that runs every 2 minutes:

```bash
# Start daemon
python3 flowspec_vpn_monitor.py start

# Check status
python3 flowspec_vpn_monitor.py status

# Stop daemon
python3 flowspec_vpn_monitor.py stop
```

### Baseline Comparison (Upgrade Testing)

```bash
# Before upgrade - save baseline
python3 flowspec_vpn_monitor.py baseline

# After upgrade - compare with baseline
python3 flowspec_vpn_monitor.py compare
```

---

## Output Examples

### Summary Table

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│               FlowSpec VPN Analysis - PE-1                                        │
├──────┬──────────────┬───────────────────────────────────┬────────┬───────────────┤
│ Step │ Component    │ Check                             │ Status │ Expected      │
├──────┼──────────────┼───────────────────────────────────┼────────┼───────────────┤
│ 1    │ BGP          │ FlowSpec-VPN Sessions             │   ✓    │ ≥1 Established│
│ 2    │ BGP          │ FlowSpec-VPN Routes Received      │   ✓    │ ≥1 routes     │
│ 3    │ VRF          │ FlowSpec Import to VRF 'CUST-A'   │   ✓    │ RT match      │
│ 4    │ Zebra        │ RIB Manager FlowSpec DB           │   ✓    │ In flowspec_db│
│ 5    │ FPM          │ NCP FlowSpec Installation         │   ✓    │ Installed     │
│ 6    │ wb_agent     │ FlowSpec BGP Rules (xray)         │   ✓    │ vrf_id ≠ 0    │
│ 7    │ wb_agent     │ FlowSpec Table Info               │   ✓    │ tcam_errors=0 │
│ 8    │ wb_agent     │ Hardware Write Counters           │   ✓    │ write_fail=0  │
│ 9    │ Counters     │ FlowSpec Match Counters           │   ✓    │ Incrementing  │
│ 10   │ Interfaces   │ FlowSpec Enabled Interfaces       │   ✓    │ ≥1 interface  │
└──────┴──────────────┴───────────────────────────────────┴────────┴───────────────┘
```

### Flow Diagram

```
FlowSpec VPN Flow - PE-1
├── BGP
│   ├── ✓ FlowSpec-VPN Sessions
│   └── ✓ FlowSpec-VPN Routes Received
├── VRF
│   └── ✓ FlowSpec Import to VRF 'CUST-A'
├── Zebra
│   └── ✓ RIB Manager FlowSpec DB
├── FPM
│   └── ✓ NCP FlowSpec Installation
├── wb_agent
│   ├── ✓ FlowSpec BGP Rules (xray)
│   ├── ✓ FlowSpec Table Info
│   └── ✓ Hardware Write Counters
├── Counters
│   └── ✓ FlowSpec Match Counters
└── Interfaces
    └── ✓ FlowSpec Enabled Interfaces
```

### Problems Panel

```
╭─────────────────── Problems Detected ───────────────────╮
│ ✗ CRITICAL: 3 rules have vrf_id=0 (VPN isolation broken!)│
│ ✗ TCAM ERRORS: 2 rules failed to write to hardware!     │
│ ✗ HW WRITE FAILURE: 1 rule failed BCM programming!      │
╰──────────────────────────────────────────────────────────╯
```

---

## Checks Performed

### Step 1: BGP FlowSpec-VPN Sessions
**Command:** `show bgp ipv4 flowspec-vpn summary`

Verifies that FlowSpec-VPN BGP sessions are established with peers (Arbor, RR, other PEs).

### Step 2: FlowSpec-VPN Routes Received
**Command:** `show bgp ipv4 flowspec-vpn routes`

Checks that FlowSpec rules are being received via BGP with proper Route Targets.

### Step 3: VRF FlowSpec Import
**Command:** `show bgp instance vrf <vrf> ipv4 flowspec routes`

Verifies that FlowSpec rules are imported to the correct VRFs via RT matching.

### Step 4: Zebra RIB Manager
**Command:** `show dnos-internal routing rib-manager database flowspec`

Checks that routes are stored in Zebra's flowspec_db with correct VRF association.

### Step 5: FPM NCP Installation
**Command:** `show flowspec ncp 0`

Verifies that rules are sent to NCP and show "Status: Installed".

### Step 6: xray FlowSpec Rules
**Command:** `xraycli /wb_agent/flowspec/bgp/ipv4/rules`

**CRITICAL CHECK:** Verifies that:
- Rules are received in wb_agent
- `vrf_id ≠ 0` for VPN rules (isolation requirement)
- `support: 0` (NLRI/action supported)

### Step 7: xray Table Info
**Command:** `xraycli /wb_agent/flowspec/bgp/ipv4/info`

Checks for:
- `num_tcam_errors = 0` (no TCAM write failures)
- `num_unsupported = 0` (all rules supported)

### Step 8: Hardware Counters
**Command:** `xraycli /wb_agent/flowspec/hw_counters`

Verifies:
- `hw_rules_write_fail = 0`
- `hw_policers_write_fail = 0`

### Step 9: Match Counters
**Command:** `show flowspec`

Checks that "Match packet counter" is incrementing for active rules.

### Step 10: FlowSpec Interfaces
**Command:** `show running-config | include 'flowspec enabled'`

Verifies that at least one interface has `flowspec enabled` for rules to apply.

---

## Known Issues Detected

| Issue | Severity | Symptom | Solution |
|-------|----------|---------|----------|
| VRF-ID = 0 | 🔴 CRITICAL | VPN isolation broken | Check RT import, VRF config |
| TCAM Errors | 🔴 CRITICAL | Rules not filtering | Check capacity, NLRI support |
| HW Write Fail | 🔴 CRITICAL | Rules not in hardware | Check BCM logs |
| No Sessions | 🟡 HIGH | No routes received | Check BGP config |
| No VRF Import | 🟡 HIGH | Routes not in VRF | Check RT matching |
| Unsupported NLRI | 🟠 MEDIUM | Rule partially works | Simplify NLRI |
| No Counters | 🟢 LOW | May be no traffic | Verify traffic flow |

---

## File Locations

| File | Purpose |
|------|---------|
| `/home/dn/SCALER/FLOWSPEC_VPN/monitor_data/` | Monitor data directory |
| `monitor_data/daemon.pid` | Daemon PID file |
| `monitor_data/monitor.log` | Daemon log file |
| `monitor_data/latest.json` | Latest analysis results |
| `monitor_data/baseline_<host>.json` | Baseline snapshots |
| `monitor_data/snapshots/` | Historical analysis snapshots |

---

## Extending the Tool

### Adding New Checks

Add new check methods following this pattern:

```python
def check_something(self, conn: SSHConnection, analysis: DeviceAnalysis) -> List[FlowCheckResult]:
    results = []
    
    cmd = "show something"
    success, output = conn.run_cli_command(cmd)
    
    if success:
        # Parse output and determine status
        status = CheckStatus.PASS if condition else CheckStatus.FAIL
        
        results.append(FlowCheckResult(
            step="11",
            component="Component",
            check_name="Check Name",
            status=status,
            expected="Expected value",
            actual=f"Actual value",
            command=cmd,
            raw_output=output
        ))
        
        if status == CheckStatus.FAIL:
            analysis.problems.append("Problem description")
    
    return results
```

Then add to `run_full_analysis()`:
```python
check_methods = [
    # ... existing checks ...
    self.check_something,
]
```

---

## Troubleshooting

### Script Errors

```bash
# Check Python version (requires 3.7+)
python3 --version

# Install dependencies
pip install rich pexpect

# Check if pexpect is available
python3 -c "import pexpect; print('OK')"
```

### Connection Issues

```bash
# Test SSH manually
ssh dnroot@10.0.0.1

# Check device is reachable
ping 10.0.0.1
```

### No Devices Found

Edit `/home/dn/SCALER/db/devices.json`:
```json
[
    {
        "hostname": "PE-1",
        "ip": "10.0.0.1",
        "username": "dnroot",
        "password": "dnroot"
    }
]
```

---

## Related Documentation

- [FlowSpec VPN How It Works](FLOWSPEC_VPN_HOW_IT_WORKS.md)
- [FlowSpec VPN Debugging Commands](FLOWSPEC_VPN_DEBUGGING.md)
- [FlowSpec VPN Full Flow Verification](FLOWSPEC_VPN_FULL_FLOW_VERIFICATION.md)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Jan 2026 | Initial release |

---

*Author: FlowSpec VPN Diagnostic Tool*  
*Last Updated: January 2026*
