# FSVPN-WIZARD v3.0 - FlowSpec VPN Diagnostic & Monitoring Wizard

## Overview

**FSVPN-WIZARD** is a comprehensive, wizard-style diagnostic tool for analyzing FlowSpec VPN rule installation from BGP reception through datapath TCAM programming.

### ✨ What's New in v3.0

| Feature | Description |
|---------|-------------|
| **IPv6 FlowSpec Support** | Full IPv6 local-policy and BGP FlowSpec checks parallel to IPv4 |
| **Dependency Detection** | Automatically detect missing or incomplete configuration with fix suggestions |
| **Multi-Device Analysis** | Analyze all devices in parallel using ThreadPoolExecutor |
| **Configuration Generator** | Interactive generator for missing FlowSpec configuration components |
| **Enhanced Menu** | New options [9], [A], [C] for the above features |

---

## 🔑 VRF-ID Semantics (CRITICAL)

> **From DP Team (Ehud) - Confirmed in code (`bcm_wrap.c`)**

| VRF-ID Value | Meaning | Notes |
|--------------|---------|-------|
| **VRF-ID = 0** | **Default VRF** | ✅ Valid - Not a bug! |
| **No VRF field** | **ALL VRFs** | Rule applies globally |
| **VRF-ID > 0** | **Specific VRF** | Non-default VRF |

## 🆚 Priority: Local Policies vs BGP FlowSpec

> **LOCAL POLICIES WIN** when both match the same traffic!
>
> In BCM/PMF TCAM: **Lower priority number = Higher precedence (matched first)**

| Source | Priority Range | Precedence |
|--------|---------------|------------|
| **Local Policies** | 0 - 1,999,999 | ✅ **WINS** (lower = first match) |
| **BGP FlowSpec** | 2,000,000 - 4,000,000 | ❌ Loses (higher = later match) |

**Code Evidence:**
```c
// From bcm_wrap_pmf.c
/* The lower the number - the higher the priority! */
```

### Shared TCAM Capacity

| Resource | IPv4 Limit | IPv6 Limit |
|----------|-----------|-----------|
| **Total TCAM** | 12,000 rules | 4,000 rules |
| **Shared by** | BGP + Local Policies | Combined |

> ⚠️ **CRITICAL: When TCAM is FULL, new policies will NOT be installed even if they have higher priority!**
> 
> This means first-installed rules take precedence when at capacity. Monitor with:
> ```bash
> # From NCP shell
> wbox-cli bcm diag field entry list group=24
> ```

## 🆕 VRF Match-Class Field (FlowSpec VPN Branch)

In the private branch (`easraf/flowspec_vpn/wbox_side`), Local Policies can now target specific VRFs:

```
routing-policy
  flowspec-local-policies
    ipv4
      match-class block-attack-in-customer-vrf
        vrf CUSTOMER-A                    ← NEW: Match traffic in this VRF!
        dest-ip 192.168.100.0/24
        protocol tcp(0x06)
        dest-ports 80
      !
      policy drop-in-customer-vrf
        match-class block-attack-in-customer-vrf
          action rate-limit 0             ← DROP
        !
      !
    !
  !
!
```

### Code Evidence

```c
// From src/wbox/src/sdk_wrap/bcm_wrap/jericho2/bcm_wrap.c
ingress_l3_interface.vrf = vrf_id;
if (vrf_id == 0)
{
    ingress_l3_interface.flags |= BCM_L3_INGRESS_GLOBAL_ROUTE;
}
```

---

## Quick Start

```bash
# Simply run the wizard - no arguments needed!
python3 /home/dn/SCALER/FLOWSPEC_VPN/fsvpn_wizard.py

# Or with alias:
alias fsvpn='python3 /home/dn/SCALER/FLOWSPEC_VPN/fsvpn_wizard.py'
fsvpn
```

---

## Features

### 🔍 Full Analysis
Complete FlowSpec VPN flow verification across all checkpoints (IPv4 + IPv6):

#### BGP FlowSpec IPv4 Checks

| Step | Component | Check |
|------|-----------|-------|
| SAFI-133 | BGP | IPv4-FlowSpec session status (default VRF) |
| SAFI-134 | BGP | IPv4-FlowSpec-VPN session status (VRF) |
| 2 | BGP | IPv4 routes received |
| 3 | VRF | IPv4-FlowSpec import via RT match |
| 4 | NCP | Datapath installation status |
| 5 | wb_agent | IPv4 TCAM table info |
| 6 | wb_agent | HW write counters |
| 7 | Counters | Traffic match verification |
| 8 | Interfaces | FlowSpec enabled check |

#### BGP FlowSpec IPv6 Checks (NEW in v3.0)

| Step | Component | Check |
|------|-----------|-------|
| v6-SAFI-133 | BGP-IPv6 | IPv6-FlowSpec session status (default VRF) |
| v6-SAFI-134 | BGP-IPv6 | IPv6-FlowSpec-VPN session status (VRF) |
| v6-2 | BGP-IPv6 | IPv6 routes received |
| v6-5 | wb_agent-IPv6 | IPv6 TCAM table info |

#### Local Policies Checks (IPv4 + IPv6)

| Step | Component | Check |
|------|-----------|-------|
| LP-1 | LocalPolicies | IPv4 configured policies count |
| LP-2 | LocalPolicies | IPv4 match-classes (incl. VRF filter) |
| LP-3 | LocalPolicies | IPv4 NCP installation status |
| LP-4 | LocalPolicies | IPv4 xray table info (TCAM errors) |
| LP-5 | LocalPolicies | IPv4 traffic counters |
| LP6-1 | LocalPolicies-IPv6 | IPv6 match-classes (NEW) |
| LP6-2 | LocalPolicies-IPv6 | IPv6 policies (NEW) |
| LP6-3 | LocalPolicies-IPv6 | IPv6 xray table info (NEW) |

#### VRF FlowSpec Address-Family Check (NEW)

| Step | Component | Check |
|------|-----------|-------|
| VRF4 | VRF | VRFs with ipv4-flowspec address-family |
| VRF6 | VRF | VRFs with ipv6-flowspec address-family |

#### Capacity & Hardware Checks

| Step | Component | Check | Details |
|------|-----------|-------|---------|
| CAP4 | TCAM | IPv4 Capacity | 12K limit (BGP + LP combined) |
| CAP6 | TCAM | IPv6 Capacity | 4K limit (BGP + LP combined) |
| BCM | Hardware | BCM TCAM Entries | `wbox-cli bcm diag field entry list group=24` |
| PRI | Priority | Conflict Analysis | Detects BGP vs LP priority conflicts |
| RNG | Priority | Range Validation | Validates priority ranges |

### 📊 Quick Check
Fast status overview - just the essentials.

### 📋 Rule Details
Detailed inspection of all FlowSpec rules including:
- NLRI details
- VRF scope (default/specific/all)
- Actions (drop, rate-limit, redirect)
- Match counters

### 📜 Extract Traces
Pull FlowSpec-related traces from containers:
- `bgpd` (NCC0) - BGP processing
- `rib-manager` (NCC0) - Route management
- `fib-manager` (NCC0) - FIB updates
- `wb_agent` (NCP0) - Datapath programming

### 🔬 Deep Dive
Analyze a specific NLRI across all verification points.

### 💾 Save Report
Export analysis to JSON for later review or comparison.

### 📚 SAFI 133/134 Guide
Educational guide explaining the difference between:
- **SAFI 133** (flowspec): Default VRF / GRT only, no RD/RT required
- **SAFI 134** (flowspec-vpn): VPN/VRF contexts, RD/RT required

### 🔧 Dependency Check (NEW in v3.0)
Automatically detect missing or incomplete FlowSpec configuration:

| Check | Detection | Severity |
|-------|-----------|----------|
| BGP FlowSpec AF | No ipv4-flowspec or ipv6-flowspec on neighbors | 🔴 Critical |
| Interface FlowSpec | No interfaces with `flowspec enabled` | 🔴 Critical |
| VRF FlowSpec AF | VRFs missing flowspec address-family | 🟡 Warning |
| Local Policy Match-Class | Missing mandatory dest-ip or source-ip | 🔴 Critical |
| Local Policy Apply | Policies defined but not applied | 🔴 Critical |

Each issue includes a **fix suggestion** with correct DNOS configuration syntax.

### 🌐 Multi-Device Analysis (NEW in v3.0)
Analyze all devices in parallel using `ThreadPoolExecutor`:

- Parallel execution (up to 4 devices simultaneously)
- Side-by-side comparison table
- Cross-device validation (RT matching, config consistency)
- Aggregate problem detection

### 📝 Configuration Generator (NEW in v3.0)
Interactive generator for FlowSpec configuration components:

| Option | Generates |
|--------|-----------|
| [1] BGP FlowSpec AF | SAFI 133 + 134 for IPv4 and IPv6 |
| [2] VRF FlowSpec | VRF address-family with RT import/export |
| [3] Interface FlowSpec | `flowspec enabled` on interfaces |
| [4] Local Policy | Complete match-class + policy + apply-policy |
| [5] Complete Setup | All of the above |

Generated config can be saved to file.

---

## Menu Navigation

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           FSVPN-WIZARD v3.0                                    ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  Main Menu                                                                     ║
║                                                                                 ║
║  [1] 🔍 Full Analysis         - Complete FlowSpec VPN flow analysis (IPv4+IPv6)║
║  [2] 📊 Quick Check           - Fast status overview                           ║
║  [3] 📋 Rule Details          - Detailed rule inspection                       ║
║  [4] 📜 Extract Traces        - Get traces from containers                     ║
║  [5] 🔬 Deep Dive             - Analyze specific NLRI                          ║
║  [6] ⚙️  Change Device         - Select different device                        ║
║  [7] 💾 Save Report           - Save analysis to file                          ║
║  [8] 📚 SAFI 133/134 Guide    - Explain FlowSpec vs FlowSpec-VPN              ║
║  [9] 🔧 Dependency Check (NEW)- Find missing configuration                     ║
║  [A] 🌐 Multi-Device (NEW)    - Analyze all devices in parallel                ║
║  [C] 📝 Config Generator (NEW)- Generate missing FlowSpec config               ║
║                                                                                 ║
║  [B] ← Back to device selection                                               ║
║  [Q] Exit wizard                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## Output Example

### Analysis Summary Table

```
┌──────┬────────────┬────────────────────────────────┬────────┬────────────────────────┬────────────────────────┐
│ Step │ Component  │ Check                          │ Status │ Expected               │ Actual                 │
├──────┼────────────┼────────────────────────────────┼────────┼────────────────────────┼────────────────────────┤
│ 1    │ BGP        │ FlowSpec-VPN Sessions          │   ✓    │ ≥1 session Established │ 2/2 Established        │
│ 2    │ BGP        │ FlowSpec-VPN Routes            │   ✓    │ ≥1 FlowSpec route      │ 5 routes received      │
│ 3    │ VRF        │ Import to 'INTERNET-VRF'       │   ✓    │ Routes via RT match    │ 5 routes imported      │
│ 4    │ NCP        │ Datapath Installation          │   ✓    │ All rules 'Installed'  │ Installed: 5, Failed: 0│
│ 5    │ wb_agent   │ TCAM Status                    │   ✓    │ tcam_errors = 0        │ entries: 5, errors: 0  │
│ 6    │ wb_agent   │ HW Counters                    │   ✓    │ write_fail = 0         │ writes OK: 5, fails: 0 │
│ 7    │ Counters   │ Traffic Match                  │   ✓    │ Counters incrementing  │ 3 rules matched        │
│ 8    │ Interfaces │ FlowSpec Enabled               │   ✓    │ ≥1 interface           │ 2 interfaces           │
└──────┴────────────┴────────────────────────────────┴────────┴────────────────────────┴────────────────────────┘
```

### Flow Diagram

```
FlowSpec VPN Flow - YOR_PE-1
├── BGP
│   ├── ✓ FlowSpec-VPN Sessions
│   └── ✓ FlowSpec-VPN Routes
├── VRF
│   └── ✓ Import to 'INTERNET-VRF'
├── NCP
│   └── ✓ Datapath Installation
├── wb_agent
│   ├── ✓ TCAM Status
│   └── ✓ HW Counters
├── Counters
│   └── ✓ Traffic Match
└── Interfaces
    └── ✓ FlowSpec Enabled
```

---

## Commands Executed

The wizard runs these commands (per check):

### BGP FlowSpec-VPN Commands

| Check | Container | Command |
|-------|-----------|---------|
| BGP Sessions | CLI | `show bgp ipv4 flowspec-vpn summary` |
| BGP Routes | CLI | `show bgp ipv4 flowspec-vpn routes` |
| VRF Import | CLI | `show bgp instance vrf {vrf} ipv4 flowspec routes` |
| NCP Status | CLI | `show flowspec ncp 0` |
| xray Info | NCP0 | `xraycli /wb_agent/flowspec/bgp/ipv4/info` |
| HW Counters | NCP0 | `xraycli /wb_agent/flowspec/hw_counters` |
| Counters | CLI | `show flowspec` |
| Interfaces | CLI | `show running-config | include 'flowspec enabled'` |

### Local Policies Commands

| Check | Container | Command |
|-------|-----------|---------|
| Policies Config | CLI | `show flowspec-local-policies policies` |
| Match Classes | CLI | `show flowspec-local-policies match-classes` |
| LP NCP Status | CLI | `show flowspec-local-policies ncp 0` |
| LP xray Info | NCP0 | `xraycli /wb_agent/flowspec/local_policies/ipv4/info` |
| LP Counters | CLI | `show flowspec-local-policies counters` |

### Hardware & Capacity Commands

| Check | Container | Command | Notes |
|-------|-----------|---------|-------|
| IPv4 Capacity | NCP0 | `xraycli /wb_agent/flowspec/bgp/ipv4/info` + `local_policies` | Combined |
| IPv6 Capacity | NCP0 | `xraycli /wb_agent/flowspec/bgp/ipv6/info` + `local_policies` | Combined |
| BCM TCAM | NCP0 | `wbox-cli bcm diag field entry list group=24` | Actual HW entries |
| Overlap Check | NCP0 | `xraycli /wb_agent/flowspec/*/rules` | Compare NLRIs |

### Trace Commands

| Container | Log File |
|-----------|----------|
| bgpd (NCC0) | `/var/log/bgpd_traces` |
| rib-manager (NCC0) | `/var/log/rib-manager_traces` |
| fib-manager (NCC0) | `/var/log/fib-manager_traces` |
| wb_agent (NCP0) | `/var/log/wb_agent_traces` |

---

## Problem Detection

The wizard detects and reports:

| Issue | Severity | Detection |
|-------|----------|-----------|
| No BGP sessions | 🔴 CRITICAL | 0 Established sessions |
| No routes received | 🟡 WARNING | 0 FlowSpec-VPN routes |
| No VRFs configured | 🟡 WARNING | No VRFs with ipv4-flowspec |
| NCP install failed | 🔴 CRITICAL | Status: "Not installed" |
| TCAM errors | 🔴 CRITICAL | num_tcam_errors > 0 |
| HW write failures | 🔴 CRITICAL | hw_rules_write_fail > 0 |
| No flowspec interfaces | 🟡 WARNING | 0 interfaces with flowspec enabled |
| **TCAM FULL** | 🔴 CRITICAL | Capacity ≥100% - new rules blocked! |
| TCAM approaching limit | 🟡 WARNING | Capacity >75% |
| Priority conflicts | 🟡 WARNING | BGP & LP rules overlap (LP wins!) |
| BCM errors | 🟡 WARNING | Errors in `wbox-cli bcm diag` output |
| LP TCAM errors | 🔴 CRITICAL | Local Policy rules failed to install |

---

## Requirements

```bash
# Required
pip install rich pexpect

# Optional (for enhanced output)
pip install paramiko
```

---

## File Locations

| File | Purpose |
|------|---------|
| `/home/dn/SCALER/FLOWSPEC_VPN/fsvpn_wizard.py` | Main wizard script |
| `/home/dn/SCALER/FLOWSPEC_VPN/wizard_data/` | Logs and snapshots |
| `/home/dn/SCALER/db/devices.json` | Device inventory |

---

## Branch Reference

- **Code Branch**: `easraf/flowspec_vpn/wbox_side`
- **Jenkins**: [Build Link](https://jenkins.dev.drivenets.net/job/drivenets/job/cheetah/job/easraf%252Fflowspec_vpn%252Fwbox_side/)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| **3.0.0** | **2026-01-18** | **IPv6 support, Dependency Detection, Multi-Device Analysis, Config Generator** |
| 2.0.0 | 2026-01-14 | Complete rewrite as wizard, fixed VRF-ID semantics |
| 1.0.0 | 2026-01-13 | Initial version with command-line interface |

### v3.0.0 Detailed Changes

- **IPv6 FlowSpec Support**: Added parallel checks for IPv6 BGP FlowSpec sessions, routes, and local policies
- **Dependency Detection**: New [9] menu option to detect missing configuration with fix suggestions
- **Multi-Device Analysis**: New [A] menu option to analyze all devices in parallel using ThreadPoolExecutor
- **Configuration Generator**: New [C] menu option to generate DNOS FlowSpec configuration
- **Enhanced Summary**: Summary display now shows IPv4 and IPv6 statistics separately
- **VRF FlowSpec AF Check**: New check to verify VRFs have FlowSpec address-family configured
- **Updated Menu**: Added options [8] SAFI Guide, [9] Dependency Check, [A] Multi-Device, [C] Config Generator

---

## Author

FlowSpec VPN Diagnostic Tool - SCALER Project
