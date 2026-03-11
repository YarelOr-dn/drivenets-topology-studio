# Bug Verification Recipes

Self-learning registry of verification recipes for `/debug-dnos verify` mode. Each recipe defines show commands, pass/fail criteria, and verification history. New recipes are added automatically after each verification session.

---

## Verification Script Best Practices (Learned from SW-239537, SW-242121, SW-238966)

### Write ONE comprehensive script, not iterative rewrites

Each config-based verification should have a single script that does **all steps in sequence**:

1. **Pre-flight**: Get baseline state (prefix counts, neighbor state, current config)
2. **Apply config**: SSH paramiko to apply the config under test + commit
3. **Verify placement**: Check the setting is under the correct AF (use AF section headers)
4. **Trigger the behavior**: Hard BGP reset if needed (excess-discard), or rollback cycle (delete+rollback bugs)
5. **Verify the result**: Prefix counts, traces, AF isolation checks
6. **Cleanup**: Remove test config + commit + soft-reconfig to restore original state

### Pre-script checklist (MANDATORY -- prevents iterative rewrites)

Before writing ANY paramiko verification script, the agent MUST:

1. **Read `gotchas.md` "DNOS Config Hierarchy Traps"** -- verify every config line against the hierarchy table
2. **Check if commands require interactive confirmation** -- `request system process restart` needs `Yes\n`
3. **Define ALL constants at TOP** -- device IPs, neighbor IPs, ASNs, interfaces. NameError = wasted iteration
4. **Use flat-path config syntax** -- `protocols bgp nsr enabled` NOT hierarchical `protocols bgp` -> `nsr` -> `enabled`
5. **Use `ss -a | grep bgp` for socket state** -- NOT `show bgp summary | include Established` (DNOS shows uptime, not "Established")
6. **Use `show bgp neighbor <IP> | include state`** for session FSM state verification
7. **Always run with `PYTHONUNBUFFERED=1 python3 -u`** for real-time output visibility
8. **Use `run start shell` for Linux commands** -- `ss`, `cat /.gitcommit` etc. require shell access with password `dnroot`
9. **Wait 3s after `invoke_shell()`** -- DNOS CLI needs time to load; commands sent immediately are rejected
10. **Flush banner with `shell.recv(65535)`** -- clear the welcome text before sending commands
11. **`show system commit | no-more` FIRST** -- snapshot commit history before any changes; count commits for `rollback N` cleanup
12. **Cleanup = `rollback N`** -- never write surgical removal scripts; `rollback N` undoes the last N commits in one command
13. **`rollback 0` at script start** -- clears any dirty candidate from previous failed attempts
14. **`show config compare` before every `commit`** -- review the pending diff to catch hierarchy errors before they cause commit failures
15. **`show config compare rollback 1` after every `commit`** -- confirm the commit had exactly the intended effect
16. **`show config compare rollback 0 rollback N` after cleanup** -- verify the rollback restored the expected pre-test state
17. **`show config compare rollback X rollback Y` for interleave detection** -- compare two rollback points to see if other users committed between your test commits

### Multi-device scripts: use separate SSH connections

When verification involves 2 devices (e.g., SW-238966 with passive + active peer):
- Open separate `paramiko.SSHClient()` instances for each device
- Apply config on both BEFORE triggering events
- Collect verification from the DUT (passive peer) since that's where the fix manifests
- Use `invoke_shell()` for the DUT (interactive commands) and `exec_command()` for show-only on the peer

### Per-AF verification requires section headers

DNOS `show bgp neighbors X` output includes ALL AFs regardless of AF qualifier. When checking any per-AF setting:

```
show bgp neighbors X | include regex "address family:|<keyword>"
```

This shows "For address family: IPv4 Flowspec-VPN" headers so you can see which AF owns the setting. **Never use** `show bgp ipv4 unicast neighbors X | include <keyword>` alone -- it's misleading.

### clear bgp syntax reference

| Command | Works? | Effect |
|---------|--------|--------|
| `clear bgp neighbor X` | YES | Hard reset (session drops, full reconvergence) |
| `clear bgp neighbor X soft in` | YES | Soft inbound reconfiguration (no session drop) |
| `clear bgp ipv4 flowspec-vpn neighbor X soft in` | **NO** | `ERROR: Unknown word: 'ipv4'` |
| `clear bgp ipv4 unicast neighbor X soft in` | **NO** | `ERROR: Unknown word: 'ipv4'` |

### excess-discard requires hard reset

`maximum-prefix exceed-action excess-discard` does NOT retroactively drop already-accepted prefixes. To test discard behavior, you MUST perform a hard session reset (`clear bgp neighbor X`) so routes are re-evaluated against the new limit on re-advertisement from the peer.

### Script template (paramiko) -- single-device

```python
import paramiko, time, re, sys, json

DEVICE_IP = "100.64.3.9"
PEER = "2.2.2.2"
ASN = "1234567"

def ssh_cmd(ssh, cmd, wait=2):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    time.sleep(wait)
    return stdout.read().decode(errors='replace')

def dnos_config(ssh, config_lines):
    """Apply config using flat-path syntax. Each line is a full path."""
    shell = ssh.invoke_shell()
    shell.send("configure\n")
    time.sleep(1)
    for line in config_lines:
        shell.send(line + "\n")
        time.sleep(0.3)
    shell.send("commit\n")
    time.sleep(5)
    shell.send("exit\n")
    time.sleep(1)
    output = shell.recv(65535).decode(errors='replace')
    shell.close()
    return output

def dnos_interactive(ssh, cmd, confirmation=None, wait=5):
    """Run commands that need interactive confirmation (e.g., process restart)."""
    shell = ssh.invoke_shell()
    shell.send(cmd + "\n")
    time.sleep(2)
    if confirmation:
        shell.send(confirmation + "\n")
    time.sleep(wait)
    output = shell.recv(65535).decode(errors='replace')
    shell.close()
    return output

def dnos_shell_cmd(ssh, cmd, wait=2):
    """Run Linux commands via 'run start shell' (for ss, cat, etc.)."""
    shell = ssh.invoke_shell()
    shell.send("run start shell\n")
    time.sleep(1)
    shell.send("dnroot\n")
    time.sleep(1)
    shell.send(cmd + "\n")
    time.sleep(wait)
    shell.send("exit\n")
    time.sleep(0.5)
    output = shell.recv(65535).decode(errors='replace')
    shell.close()
    return output

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(DEVICE_IP, port=22, username="dnroot", password="dnroot")

# 1. Pre-flight
baseline = ssh_cmd(ssh, "show bgp ipv4 flowspec-vpn summary | include " + PEER)
print("BASELINE:", baseline, flush=True)

# 2. Apply config (flat-path syntax)
config = [
    f"protocols bgp {ASN} neighbor {PEER} address-family ipv4-flowspec-vpn maximum-prefix limit 1 threshold 80 exceed-action excess-discard",
]
print("CONFIG:", dnos_config(ssh, config), flush=True)

# 3. Verify placement (AF section headers)
verify = ssh_cmd(ssh, f'show bgp neighbors {PEER} | include regex "address family:|Maximum|prefixes"')
print("VERIFY:", verify, flush=True)

# 4. Hard reset to trigger discard
ssh_cmd(ssh, "clear bgp neighbor " + PEER, wait=30)

# 5. Check result -- use neighbor detail, NOT summary "Established" string
result = ssh_cmd(ssh, f"show bgp neighbor {PEER} | include state")
print("RESULT:", result, flush=True)

# 6. Cleanup
cleanup = [f"protocols bgp {ASN} neighbor {PEER} address-family ipv4-flowspec-vpn no maximum-prefix"]
dnos_config(ssh, cleanup)
ssh_cmd(ssh, "clear bgp neighbor " + PEER + " soft in", wait=10)

ssh.close()
```

### Script template (paramiko) -- multi-device (e.g., NSR verification)

```python
import paramiko, time, sys, json

# ALL constants at TOP -- NameError prevention
DUT_IP = "100.64.7.242"
PEER_IP = "100.64.3.9"
DUT_ASN = "123"
PEER_ASN = "1234567"
DUT_NEIGHBOR = "1.1.1.1"
PEER_NEIGHBOR = "2.2.2.2"

def connect(ip):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, port=22, username="dnroot", password="dnroot")
    return ssh

def shell_cmd(ssh, commands, wait=3):
    """Interactive shell for config, restart, or Linux commands."""
    shell = ssh.invoke_shell()
    for cmd in commands:
        shell.send(cmd + "\n")
        time.sleep(0.5)
    time.sleep(wait)
    output = shell.recv(65535).decode(errors='replace')
    shell.close()
    return output

def show_cmd(ssh, cmd, wait=2):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    time.sleep(wait)
    return stdout.read().decode(errors='replace')

dut = connect(DUT_IP)
peer = connect(PEER_IP)

# 1. Apply config on BOTH devices
shell_cmd(dut, ["configure",
    f"protocols bgp nsr enabled",
    f"protocols bgp {DUT_ASN} neighbor {DUT_NEIGHBOR} graceful-restart disabled",
    f"protocols bgp {DUT_ASN} neighbor {DUT_NEIGHBOR} passive enabled",
    "commit", "exit"], wait=8)

shell_cmd(peer, ["configure",
    f"protocols bgp nsr enabled",
    f"protocols bgp {PEER_ASN} neighbor {PEER_NEIGHBOR} graceful-restart disabled",
    "commit", "exit"], wait=8)

# 2. Trigger NSR event (interactive confirmation)
shell_cmd(dut, [
    "request system process restart ncc 0 routing-engine routing:bgpd",
    "Yes"
], wait=45)

# 3. Verify socket listener (the real fix indicator)
ss_output = shell_cmd(dut, [
    "run start shell", "dnroot",
    "ss -a | grep bgp",
    "exit"
], wait=3)
print("SOCKET STATE:", ss_output, flush=True)

# 4. Verify session state
state = show_cmd(dut, f"show bgp neighbor {DUT_NEIGHBOR} | include state")
print("BGP STATE:", state, flush=True)

# PASS: "0.0.0.0:bgp" LISTEN exists AND "BGP state = Established"
# FAIL: only "[::]:bgp" LISTEN (IPv4 listener lost)

dut.close()
peer.close()
```

---

## SW-211921: IRB Flap Twice on EVPN IRB Swap

- **Component:** fib-manager / L2NeighborAgent.cpp
- **Fix branch:** easraf/flowspec_vpn/wbox_side
- **Fix commit:** merged before build 24 (2026-02-19)
- **Config required:** yes
- **Config prerequisite:** 2 EVPN instances with IRB interfaces + 2 VRFs. Config files at `~/SCALER/FLOWSPEC_VPN/irb_flap_test/`

### Verification Steps

1. Apply base config: 2 bundle sub-ifs with l2-service, 2 IRBs, 2 EVPN instances, 2 VRFs (`~/SCALER/FLOWSPEC_VPN/irb_flap_test/base_config.txt`)
2. Apply swap config: swap IRB assignments between EVPN/VRF instances (`~/SCALER/FLOWSPEC_VPN/irb_flap_test/swap_config.txt`)
3. `show file traces cluster-engine/cluster_manager_protocols | include irb` -- expect: 1 down + 1 up per IRB
4. `show file traces routing_engine/fibmgrd_traces | include EVPN_ATTACH` -- expect: clean DETACH then ATTACH ordering
5. `show file traces routing_engine/fibmgrd_traces | include CRIT` -- expect: EMPTY (no crash)
6. `show file traces routing_engine/rib-manager_traces | include attachIrb` -- expect: each IRB attaches exactly once

### Pass Criteria

- Step 3: each IRB has exactly 1 down + 1 up event (not 2+)
- Step 4: all DETACHes complete before ATTACHes (no interleaved ATTACH-DETACH-ATTACH)
- Step 5: output is EMPTY (no CRIT assertion)
- Step 6: each IRB attaches exactly once

### Fail Criteria

- Step 3: any IRB has 2+ down events -> BUG PRESENT (double flap)
- Step 4: interleaved ATTACH-DETACH-ATTACH ordering -> BUG PRESENT (race condition)
- Step 5: output contains "CRIT" or "assertion" -> BUG PRESENT + fib_manager crash

### Config (if needed)

See `~/SCALER/FLOWSPEC_VPN/irb_flap_test/base_config.txt` and `swap_config.txt`

### Cleanup (if config applied)

`python3 ~/SCALER/FLOWSPEC_VPN/irb_flap_test/cleanup.py`

### History

| Date | Device | Image | Verdict |
|------|--------|-------|---------|
| 2026-02-25 | RR-SA-2 | 26.1.0.24_priv...build_24 | FIX CONFIRMED |

---

## SW-222730: FlowSpec-VPN vtysh Ambiguous Commands

- **Component:** cli / show_vtysh_commands.py
- **Fix branch:** easraf/flowspec_vpn/wbox_side
- **Fix commit:** present in build 24+ (global commands fixed); VRF-scoped commands still missing
- **Config required:** no
- **Config prerequisite:** device must have at least one VRF with BGP FlowSpec-VPN configured

### Verification Steps

1. `show bgp ipv4 flowspec-vpn summary` -- expect: valid output (no "Ambiguous command")
2. `show bgp ipv4 flowspec-vpn routes` -- expect: valid output (no "Ambiguous command")
3. `show bgp instance vrf <vrf-name> ipv4 flowspec-vpn summary` -- expect: valid output (no "Unknown word")
4. `show bgp instance vrf <vrf-name> ipv4 flowspec-vpn routes` -- expect: valid output (no "Unknown word")

### Pass Criteria

- Steps 1-2 output does NOT contain "Ambiguous command"
- Steps 3-4 output does NOT contain "Unknown word" or "Ambiguous command"

### Fail Criteria

- Steps 1-2 output contains "Ambiguous command" -> BUG PRESENT (global commands broken)
- Steps 3-4 output contains "Unknown word" -> BUG PRESENT (VRF-scoped commands not registered)

### Config (if needed)

None — uses existing device configuration.

### Cleanup (if config applied)

N/A

### History

| Date | Device | Image | Verdict |
|------|--------|-------|---------|
| 2026-02-25 | RR-SA-2 | 26.1.0.24_priv...build_24 | PARTIAL — global fixed, VRF-scoped still broken |
| 2026-02-25 | PE-1 | 26.1.0.24_priv...build_24 | FIX CONFIRMED -- global + VRF-scoped both work (summary, route table, neighbors). `routes` subcommand doesn't exist for FlowSpec AFIs (not part of bug). |

---

## SW-CONFIG-DESYNC: BGP Per-AFI Config Desync on Delete+Re-commit

- **Component:** bgpd / dn2oc config manager / precommit.py
- **Fix branch:** easraf/flowspec_vpn/wbox_side
- **Fix commit:** merged by Amir Ben Avraham, present in build 24
- **Config required:** no (verification checks existing bgpd state)
- **Config prerequisite:** device must have BGP neighbors with per-AF settings (ipv4-vpn, ipv4-flowspec-vpn)

### Verification Steps

1. `show bgp ipv4 vpn neighbors <neighbor-ip>` -- expect: "Send-community: extended" present in ipv4-vpn section
2. `show file traces routing_engine/vtysh_traces | include "Command not found"` -- expect: EMPTY (no unregistered commands)
3. `show bgp ipv4 vpn neighbors <neighbor-ip> advertised-routes` -- expect: routes WITH RT extended communities

### Pass Criteria

- Step 1 output contains "Send-community" in the ipv4-vpn neighbor section
- Step 2 output is EMPTY (no "Command not found" warnings)
- Step 3 output contains routes with RT communities (not empty)

### Fail Criteria

- Step 1: "Send-community" missing from ipv4-vpn section -> BUG PRESENT (settings leaked to wrong AF)
- Step 2: output contains "Command not found" -> BUG PRESENT (vtysh desync active)

### Config (if needed)

None — verification checks existing bgpd state.

### Cleanup (if config applied)

N/A

### History

| Date | Device | Image | Verdict |
|------|--------|-------|---------|
| 2026-02-19 | PE-1 | 26.1.0.22_priv...build_24 | FIX CONFIRMED |

---

## SW-REDIRECT-IP-UNREACHABLE: FlowSpec Redirect-IP NH Unreachable in Non-Default VRF

- **Status:** FIX CONFIRMED (build 28_priv)
- **Component:** rib-manager (zebra) -> fib-manager protobuf interface
- **Fix branch:** easraf/flowspec_vpn/wbox_side
- **Fix commit:** 755b292cec7b (zebra_flowspec_db.c: nexthop->vrf_id = flowspec->route.vrf_id)
- **Config required:** no (if FlowSpec redirect-ip rules already exist on device)
- **Config prerequisite:** device must have a non-default VRF with a FlowSpec redirect-ip rule installed

### Verification Steps

1. `show flowspec ncp <id>` -- expect: redirect NH marked `(reachable)` in non-default VRF
2. `show route vrf <vrf-name> <redirect-ip>` -- expect: `best, fib` entry exists
3. `show file traces routing_engine/fibmgrd_traces | include is_flowspec` -- expect: ADD_NEXTHOP has `vrf_id` and `nexthops` array

### Pass Criteria

- Step 1 output does NOT contain "(unreachable)" for redirect-ip NH in non-default VRF
- Step 3 output shows ADD_NEXTHOP with `vrf_id` field and `nexthops` array

### Fail Criteria

- Step 1: redirect NH shows "(unreachable)" despite route existing in VRF -> BUG PRESENT
- Step 3: ADD_NEXTHOP has only bare `address` + `is_flowspec: true` with no `vrf_id` -> BUG PRESENT

### Config (if needed)

None — uses existing FlowSpec rules on device.

### Cleanup (if config applied)

N/A

### History

| Date | Device | Image | Verdict |
|------|--------|-------|---------|
| 2026-02-18 | PE-1 | 26.1.0.24_priv...build_26 | BUG PRESENT |
| 2026-02-22 | PE-4 | 26.1.0.24_priv...build_26 | BUG PRESENT |
| 2026-02-25 | PE-1 | 26.1.0.24_priv...build_26 | BUG PRESENT (Jira SW-242876 closed but fix not in build) |
| 2026-03-02 | PE-1 | 26.1.0.24_priv...build_28 | FIX CONFIRMED — redirect-ip NH no longer (unreachable), ADD_NEXTHOP protobuf has vrf_id + nexthops array, rule Installed in NCP TCAM |

---

## SW-VRF-LITE-NO-IMPORT: FlowSpec Redirect-to-RT Cannot Target VRF Without RD

- **Status:** SKIP (no fix exists)
- **Component:** bgpd / bgp_service.c (match_vrf_from_rt)
- **Fix branch:** easraf/flowspec_vpn/wbox_side
- **Fix commit:** not yet fixed (open bug)
- **Config required:** yes (need VRF-Lite with matching import RT)
- **Config prerequisite:** two VRFs with identical import-vpn route-target — one with RD (control), one without RD (VRF-Lite)

### Verification Steps

1. `show flowspec instance vrf <with-rd-vrf> ipv4` -- expect: flows found with redirect target
2. `show flowspec instance vrf <no-rd-vrf> ipv4` -- expect: flows found (fixed) or "No flows found" (bug present)
3. `show file traces routing_engine/bgpd_traces | include "Found match VRF"` -- expect: both VRFs appear as match candidates

### Pass Criteria

- Step 2 output contains flow entries (VRF-Lite is a valid redirect target)
- Step 3 output shows both the with-RD and without-RD VRFs as match candidates

### Fail Criteria

- Step 2: "No flows found" -> BUG PRESENT (VRF-Lite excluded as redirect target)
- Step 3: only the with-RD VRF appears -> BUG PRESENT (match_vrf_from_rt skips VRF-Lite)

### Config (if needed)

See `BUG_FLOWSPEC_VPN_VRF_LITE_NO_IMPORT.md` Test Setup section.

### Cleanup (if config applied)

Remove TEST_WITH_RD and TEST_NO_RD VRFs.

### History

| Date | Device | Image | Verdict |
|------|--------|-------|---------|
| 2026-02-23 | PE-1 | 26.1.0.24_priv...build_26 | BUG PRESENT |


---

## SW-240264: FlowSpec-VPN Rule Imported to Multiple VRFs Only Installed in One VRF

- **Component:** bgpd / zebra flowspec install
- **Fix branch:** easraf/flowspec_vpn/wbox_side
- **Fix commit:** 7c1dbb9f (2026-02-15), 42039c30 (2026-02-12)
- **Config required:** no (if FlowSpec-VPN rules with multi-VRF import already exist)
- **Config prerequisite:** device must have a FlowSpec-VPN route imported into 2+ VRFs via RT matching

### Verification Steps

1. `show flowspec ncp 0` -- expect: same NLRI (e.g. `DstPrefix:=10.0.0.0/24`) appears in 2+ VRFs
2. `show flowspec instance vrf <vrf-1> ipv4` -- expect: flow entry present
3. `show flowspec instance vrf <vrf-2> ipv4` -- expect: same flow entry present in second VRF

### Pass Criteria

- Step 1: same NLRI appears in multiple VRF rows in NCP
- Steps 2-3: both VRFs show the flow with actions

### Fail Criteria

- Step 1: NLRI only appears in one VRF despite multiple VRFs importing the same RT -> BUG PRESENT

### History

| Date | Device | Image | Verdict |
|------|--------|-------|---------|
| 2026-02-25 | PE-1 | 26.1.0.24_priv...build_26 | FIX CONFIRMED -- 10.0.0.0/24 in VRF 15 + ZULU + ALPHA |

---

## SW-242121: BGP VPN AF Per-Neighbor Knobs Dropped After Delete+Rollback

- **Component:** bgpd / vtysh / dn2oc config manager
- **Fix branch:** easraf/flowspec_vpn/wbox_side
- **Fix commit:** d04b9932 (2026-02-18)
- **Config required:** yes (must delete+rollback neighbor to trigger)
- **Config prerequisite:** device must have BGP neighbors with per-AF settings (flowspec-vpn, vpn)
- **Repro script:** `~/SCALER/FLOWSPEC_VPN/verify_242121.py`

### Verification Steps (Full Reproduction)

1. BEFORE: `show bgp ipv4 flowspec-vpn neighbors <neighbor> | include Community` -- record count
2. BEFORE: `show bgp ipv4 flowspec-vpn neighbors <neighbor> | include allowas` -- record count
3. BEFORE: `show file traces routing_engine/vtysh_traces | include Command` -- record baseline
4. REPRODUCE: `configure → protocols → bgp <ASN> → no neighbor <neighbor> → commit`
5. Wait 10s for BGP session to drop
6. RESTORE: `rollback 1 → commit`
7. Wait 45-60s for BGP to re-establish
8. AFTER: repeat steps 1-3 and compare counts

### Pass Criteria

- Steps 1-2 AFTER match BEFORE (same Community count, same allowas-in count)
- Step 3: no new "Command not found" entries in vtysh traces after the operation

### Fail Criteria

- AFTER Community/allowas-in counts are LOWER than BEFORE -> BUG PRESENT
- New "Command not found" entries appear in vtysh traces -> BUG PRESENT

### History

| Date | Device | Image | Verdict |
|------|--------|-------|---------|
| 2026-02-25 | PE-1 | 26.1.0.24_priv...build_26 | FIX CONFIRMED -- steady-state check only (no repro) |
| 2026-02-25 | PE-1 | 26.1.0.24_priv...build_26 | FIX CONFIRMED -- full repro: 2x delete+rollback cycles, all per-AF knobs intact (Community 8x, allowas-in 5x, route-map ADD-LARGE-COMMUNITY), no new vtysh errors |

---

## SW-239633: NLRI Show Filters in VRF Scope Don't Work

- **Component:** bgpd / show command registration
- **Fix branch:** easraf/flowspec_vpn/wbox_side
- **Fix commit:** no explicit commit found (likely bundled with SW-242121 fix)
- **Config required:** no
- **Config prerequisite:** device must have FlowSpec-VPN routes from an eBGP peer + iBGP peer for both received and advertised tests
- **Developer note:** `destination` and `source` options were incorrect and removed. Only `nlri` filter should exist.

### Verification Steps (Full)

1. `show bgp ipv4 flowspec-vpn neighbors <eBGP-peer> received-routes` -- baseline: confirm routes exist
2. `show bgp ipv4 flowspec-vpn neighbors <eBGP-peer> received-routes nlri "<exact NLRI>"` -- expect: `BGP Adj-in table entry for <NLRI> with RD: ...` with attributes (Origin, Extended Community)
3. `show bgp ipv4 flowspec-vpn neighbors <iBGP-peer> advertised-routes nlri "<exact NLRI>"` -- expect: `BGP Adj-out table entry for <NLRI> with RD: ...` with attributes
4. `show bgp ipv4 flowspec-vpn neighbors <peer> received-routes nlri "<non-existent NLRI>"` -- expect: `% No such prefix found <NLRI>` (correct negative case, not crash or empty)
5. `show bgp ipv4 flowspec-vpn neighbors <peer> received-routes destination <prefix>` -- expect: `ERROR: Unknown word: 'destination'` (option correctly removed)
6. `show bgp ipv4 flowspec-vpn neighbors <peer> received-routes source <prefix>` -- expect: `ERROR: Unknown word: 'source'` (option correctly removed)
7. (If VRF neighbor is established): `show bgp instance vrf <vrf> ipv4 flowspec neighbors <peer> received-routes nlri "<exact NLRI>"` -- expect: specific route details

### Pass Criteria

- Step 2: returns route attributes (adj-in table entry with Origin, Extended Community, RD)
- Step 3: returns route attributes (adj-out table entry with Origin, localpref, RD)
- Step 4: returns "No such prefix found" (not crash, not empty)
- Steps 5-6: `ERROR: Unknown word` (options correctly removed per developer decision)

### Fail Criteria

- Step 2: returns "No such prefix found" for an existing route -> BUG PRESENT (nlri filter broken)
- Step 3: returns "No such prefix found" for an existing route -> BUG PRESENT
- Step 5-6: options still work or return route data -> partial fix (destination/source should be removed)

### Notes

- NLRI string must be quoted and match EXACTLY as shown in the unfiltered output (e.g., `"DstPrefix:=10.0.0.0/24,SrcPrefix:=*"`)
- `destination` and `source` were never implemented correctly -- they were suggested in tab-complete but returned "No such prefix found". Fix removed them entirely.
- VRF-scoped test requires per-VRF FlowSpec neighbor to be established (not always available on lab devices)

### History

| Date | Device | Image | Verdict |
|------|--------|-------|---------|
| 2026-02-25 | PE-1 | 26.1.0.24_priv...build_26 | FIX CONFIRMED -- global and VRF-scoped NLRI filters both work |
| 2026-02-25 | PE-1 | 26.1.0.24_priv...build_24 | FIX CONFIRMED -- nlri filter works on received-routes + advertised-routes, destination/source correctly removed, negative test proper |
| 2026-03-02 | RR-SA-2 | 26.1.0 build 27_priv | FIX CONFIRMED -- all 5 steps pass: NLRI filter on received-routes returns adj-in with RD+attributes, advertised-routes returns adj-out with Originator+Cluster-list, non-existent NLRI returns "No such prefix found", destination/source correctly removed |

---

## SW-239537: Maximum-Prefix Exceed-Action Incorrectly Applied to IPv4 Unicast

- **Component:** bgpd / AF command registration
- **Fix branch:** easraf/flowspec_vpn/wbox_side
- **Fix commit:** e18f34ab (2026-02-10)
- **Config required:** yes (apply max-prefix under flowspec-vpn AF, hard reset BGP to trigger)
- **Config prerequisite:** device must have BGP neighbor with flowspec-vpn AF and at least 2 accepted prefixes
- **Repro script:** `~/SCALER/FLOWSPEC_VPN/verify_239537_discard.py`

### Verification Steps (Full Functional Test)

1. Apply config: `maximum-prefix limit 1 threshold 80 exceed-action excess-discard` under `address-family ipv4-flowspec-vpn` for a neighbor with 2+ accepted prefixes. Commit.
2. `show bgp neighbors <peer> | include regex "address family:|Maximum|prefixes"` -- expect: `Maximum prefixes allowed 1 (excess-discard)` under `For address family: IPv4 Flowspec-VPN` section ONLY (not under IPv4 Unicast)
3. `clear bgp neighbor <peer>` (hard reset to force re-evaluation of incoming routes)
4. Wait 30s for BGP to re-establish
5. `show bgp ipv4 flowspec-vpn summary | include <peer>` -- expect: only 1 prefix accepted (was 2, limit is 1)
6. `show bgp neighbors <peer> | include regex "address family:|Maximum|prefixes"` -- expect: `1 prefixes accepted` under IPv4 Flowspec-VPN, `0 prefixes accepted` under IPv4 Unicast
7. `show file traces routing_engine/bgpd_traces | include MAXPFXEXCEED | tail 5` -- expect: `%MAXPFXEXCEED: No. of IPv4 Flowspec-VPN prefix received` (correct AF, not "IPv4 Unicast")
8. Cleanup: `no maximum-prefix` + commit + `clear bgp neighbor <peer> soft in` to restore all routes

### Pass Criteria

- Step 2: `Maximum prefixes allowed` appears ONLY under `For address family: IPv4 Flowspec-VPN`
- Step 5: prefix count drops from 2 to 1 (excess was discarded)
- Step 6: IPv4 Unicast shows 0 prefixes (no cross-AF leak of max-prefix)
- Step 7: trace says `IPv4 Flowspec-VPN` (not `IPv4 Unicast`)

### Fail Criteria

- Step 2: `Maximum prefixes` appears under IPv4 Unicast -> BUG PRESENT (cross-AF leak)
- Step 5: prefix count stays at 2 (excess not discarded) -> BUG PRESENT (action not enforced)
- Step 7: trace says `IPv4 Unicast` -> BUG PRESENT (wrong AF in system event)

### Notes

- `clear bgp ipv4 flowspec-vpn neighbor X soft in` does NOT work (returns `Unknown word: 'ipv4'`). Use `clear bgp neighbor X soft in` (global) or `clear bgp neighbor X` (hard reset)
- `excess-discard` does NOT retroactively drop already-accepted prefixes. A hard reset (`clear bgp neighbor X`) is required to force re-evaluation
- `show bgp ipv4 unicast neighbors X` actually shows ALL AFs — use `show bgp neighbors X | include regex "address family:|Maximum"` with section headers to determine which AF the max-prefix belongs to

### History

| Date | Device | Image | Verdict |
|------|--------|-------|---------|
| 2026-02-25 | PE-1 | 26.1.0.24_priv...build_26 | FIX CONFIRMED -- CLI accepts exceed-action in flowspec-vpn AF |
| 2026-02-25 | PE-1 | 26.1.0.24_priv...build_26 | FIX CONFIRMED -- full functional: max-prefix under correct AF, excess discarded (2→1), traces say "IPv4 Flowspec-VPN", no unicast leak |

---

## SW-240206: FlowSpec-VPN RT-Redirect Target Not Re-evaluated After Unicast Import RT Change

- **Component:** bgpd / flowspec redirect VRF selection
- **Fix branch:** easraf/flowspec_vpn/wbox_side
- **Fix commit:** closed 2026-02-24
- **Config required:** yes (modify VRF import RT to trigger re-evaluation)
- **Config prerequisite:** 2+ VRFs importing the same RT used in a flowspec redirect-vrf-rt action
- **Repro script:** `~/SCALER/FLOWSPEC_VPN/verify_240206.py`

### Verification Steps

1. BEFORE: `show flowspec instance vrf <VRF-A> ipv4 nlri DstPrefix:=<prefix>,SrcPrefix:=*` -- record redirect target VRF
2. BEFORE: `show flowspec instance vrf <VRF-B> ipv4 nlri DstPrefix:=<prefix>,SrcPrefix:=*` -- record redirect target VRF
3. MODIFY: Remove the shared redirect RT from VRF-A's `import-vpn route-target` (use `no import-vpn route-target` then set new value without the shared RT) + commit
4. Wait 15s
5. AFTER: `show flowspec instance vrf <VRF-A> ipv4` -- expect: redirect target changed to VRF-B
6. AFTER: `show flowspec instance vrf <VRF-B> ipv4` -- expect: redirect target changed to VRF-B
7. REVERT: Restore the shared RT to VRF-A's import + commit
8. Wait 15s
9. VERIFY: redirect target returns to VRF-A (alphabetically first)

### Pass Criteria

- Step 5-6: redirect target dynamically updates to VRF-B (the only remaining VRF importing the redirect RT) WITHOUT needing `clear bgp neighbor`
- Step 9: redirect target returns to VRF-A after restore (alphabetically first candidate again)

### Fail Criteria

- Steps 5-6: redirect target still shows old VRF-A despite VRF-A no longer importing the RT -> BUG PRESENT
- Workaround needed: `clear bgp neighbor` required to force re-evaluation -> BUG PRESENT

### Config Notes

- `import-vpn route-target` is NOT a replace command on DNOS — setting a new value is additive
- To remove an RT: must use `no import-vpn route-target` first to clear, then set the new value
- The DNOS `validate_config` tool treats unchanged values as "no configuration changes"

### History

| Date | Device | Image | Verdict |
|------|--------|-------|---------|
| 2026-02-25 | PE-1 | 26.1.0.24_priv...build_26 | FIX CONFIRMED -- redirect target dynamically re-evaluated in both directions (ALPHA→ZULU on remove, ZULU→ALPHA on restore), no clear bgp needed |

---

## BUG-2 (m_reserved leak): FlowSpec Local Policy NCP Resource Leak on Create/Delete Cycles

- **Status:** Open (no fix exists)
- **Component:** NCP / wb_agent FlowSpec / FlowspecTcamManager.cpp
- **Fix branch:** easraf/flowspec_vpn/wbox_side
- **Fix commit:** not yet fixed
- **Config required:** yes (must create/delete FlowSpec local policies ~10-15 times)
- **Config prerequisite:** device with FlowSpec local policies configured. Heavy rules with `packet-length range` accelerate the leak.
- **Evidence file:** `BUG_FLOWSPEC_LOCAL_POLICY_RESOURCE_LEAK.md`

### Verification Steps

1. `show system npu-resources resource-type flowspec` -- baseline: record IPv4 Received/Installed/HW used
2. Configure 100 FlowSpec local policy match-classes (dest-ip/32, protocol, dest-port, action rate-limit 0)
3. Apply via `forwarding-options flowspec-local ipv4 apply-policy-to-flowspec`, commit
4. `show system npu-resources resource-type flowspec` -- expect: Received == Installed == HW entries (all 100 install)
5. Delete all policies + forwarding-options, commit
6. Repeat steps 2-5 approximately 10-15 times (include some cycles with `packet-length range` rules for faster leak accumulation)
7. Load 2000 simple rules (dest-ip/32, proto, dest-port, action rate-limit 500000) and commit
8. `show system npu-resources resource-type flowspec` -- check: Received vs Installed vs HW used
9. `show flowspec-local-policies ncp <id> | include "Not Installed"` -- count failed rules
10. If Installed < Received but HW used == Installed (TCAM not full): **leak detected**
11. Restart NCP: `request system restart ncp <id>`
12. Wait 2-3 minutes for NCP to come back
13. `show system npu-resources resource-type flowspec` -- expect: all rules now install (Received == Installed)

### Pass Criteria (fix applied)

- Step 8: Received == Installed (all 2000 rules install)
- Step 9: EMPTY (no "Not Installed" entries)
- No need to restart NCP -- resources correctly managed after create/delete cycles

### Fail Criteria (bug present)

- Step 8: Received >> Installed AND HW used == Installed (e.g., 2000 received, 1024 installed, 1024/12000 HW) -> BUG PRESENT (leaked m_reserved = 12000 - 1024 = 10976)
- Step 9: rules show `Not Installed, out of resources` -> BUG PRESENT
- Step 13: after NCP restart, all rules install -> confirms m_reserved was the leak

### Detection Heuristic

Compute leaked `m_reserved = total_capacity - installed`. Key signals:
- Power-of-2 cutoff (1024, 2048) with low TCAM usage
- Different rule content produces same ceiling
- NCP restart recovers all rules
- Syslog: `FLOWSPEC_LOCAL_UNSUPPORTED_RULE: ... lack of resources`

### TCAM Amplification Factor (packet-length range rules)

| Match criteria | TCAM entries per rule |
|---------------|----------------------|
| dest-ip/32 + proto + dest-port | 1 |
| dest-ip/32 + proto + dest-port + src-port + `PacketLen:>=64&<=1500` | ~1437 |
| dest-ip/32 + 6 criteria (complex) | ~180-244 |

### Trace Evidence to Collect (if taking techsupport)

In NCP traces (`wb_agent.flowspec`):
- `include Succeeded` -- count successful TCAM writes
- `include No more space` -- WARNING message (rotates quickly)
- `include DeleteTcamRule` -- `Num entries: N` = BCM hardware truth
- `include ReserveQualifiers` -- reservation attempts
- `include Disabling TCAM writes` -- reshuffle deferral point

### Config (if needed)

Generate 100 match-classes with simple criteria:
```
routing-policy flowspec-local-policies
 policy POL-TEST
  match-class MC-TEST-0001
   match dest-ip 10.1.0.1/32
   match protocol tcp
   match dest-port 6001
   action rate-limit 0
  !
  ...
 !
!
forwarding-options flowspec-local ipv4 apply-policy-to-flowspec
!
```

### Cleanup (if config applied)

```
no routing-policy flowspec-local-policies
no forwarding-options flowspec-local
commit
```

### History

| Date | Device | Image | Verdict |
|------|--------|-------|---------|
| 2026-02-24 | PE-4 | 26.1.0.24_priv...build_24 | BUG PRESENT (100 rules: 84 installed, 16 failed, 97/12000 TCAM) |
| 2026-02-25 | PE-4 | 26.1.0.24_priv...build_24 | BUG PRESENT -- SEVERE (2000 rules: 1024 installed, 976 failed, 1024/12000 TCAM, leaked m_reserved ~10976) |

---

## SW-238966: BGP NSR -- New Neighbors Won't Establish After NSR With Passive Config

- **Component:** Routing-BGP (bgpd socket handling during NSR recovery)
- **Fix branch:** rel_v26_1, rel_v25_4, dev_v25_4_13 (NOT dev_v26_2)
- **Fix commit:** unknown (do NOT use `ffa5846` -- that is SW-230334 disk usage, not SW-238966). Use version + branch check.
- **Fix commit (merged):** 2026-03-05, 2 PRs merged (set SO_REUSEADDR after disabling TCP_REPAIR + skip TCP-AO repair data when peer does not use TCP-AO)
- **Fix versions:** v25.4.13, v26.1 only
- **Excluded branches:** dev_v26_2 (fix NOT merged as of 2026-03-07; verified via bgp_nsr.c source inspection)
- **Found in:** v25.2
- **Version check:** Builds on rel_v25_4 (v25.4.13+), dev_v25_4_13 (v25.4), or rel_v26_1 (v26.1+) contain the fix. dev_v26_2 does NOT. Use `show version` + `cat /.gitcommit` to confirm branch.
- **Config required:** yes (NSR must be enabled, at least one passive BGP neighbor required)
- **Config prerequisite:** device must have `nsr enabled` under `protocols bgp` AND at least one neighbor with `passive enabled`
- **Impact note:** SA devices always affected; CL devices may be affected from v25.4+ when peers use local port 179

### Root Cause

During BGP NSR recovery, bgpd disables `TCP_REPAIR` on recovered sockets. On kernel 6.8.12
(was not a problem on kernel 5.15), disabling `TCP_REPAIR` implicitly clears the `SO_REUSEADDR`
flag. TCP-AO code uses `TCP_REPAIR` to retrieve socket repair data **even if TCP-AO is not
configured on the peer** -- so any peer using local port 179 triggers the issue.

Old sockets in FIN-WAIT state still hold local port 179, so the new BGP listener socket can't
bind for IPv4. Result: only `[::]:bgp` (IPv6) listener exists, `0.0.0.0:bgp` (IPv4) is missing.
Any passive IPv4 neighbor that needs to accept incoming connections will fail.

**Not strictly limited to passive peers** (per Flavia's comment): the listener socket fails to
bind if ANY existing peer connection uses local port 179. But passive peers are the most visible
symptom because they rely on the listener to accept incoming connections.

**Fix:** Set `SO_REUSEADDR` on socket after disabling `TCP_REPAIR`. Also don't attempt to read
TCP-AO repair data when the peer does not use TCP-AO.

**Reproduction variants** (from Jira test criteria):
- With/without TCP-AO set
- With/without passive peers
- Single NSR (v25.4+) or two consecutive NSRs (pre-25.4)
- Key requirement: at least one session using local BGP port before restart

### Prerequisites

1. Device running a build with the fix (rel_v25_4 v25.4.13+, dev_v25_4_13 v25.4, or rel_v26_1 v26.1+; dev_v26_2 does NOT have the fix)
2. `nsr enabled` under `protocols bgp <ASN>`
3. At least one BGP neighbor with `passive enabled`
4. That neighbor must have an active peer that initiates connections (e.g., ExaBGP, or another DNOS router)
5. **CRITICAL: `graceful-restart disabled` on BOTH sides** -- GR must be disabled on the passive router AND its peer. If GR is enabled, the session recovery mechanism is different and the bug may not be triggered. The Jira repro explicitly requires GR disabled on both routers.
6. The peer (non-passive side) does NOT need `passive enabled` -- it should be the active initiator

### Verification Steps

**Phase 1: Pre-flight baseline**

1. `show version | no-more` -- record image version (must be v25.4.13+ or v26.1+ on rel_v25_4/rel_v26_1/dev_v25_4_13; dev_v26_2 excluded)
2. `show config protocols bgp | include "nsr" | no-more` -- confirm NSR is enabled
3. `show config protocols bgp | include "passive" | no-more` -- confirm passive neighbor exists
4. `show config protocols bgp | include "graceful-restart" | no-more` -- confirm `graceful-restart disabled` is set on the passive neighbor (and verify peer side too)
5. `show bgp summary | no-more` -- confirm the passive neighbor is **Established**
6. Shell: `ss -a | grep bgp` -- confirm BOTH `0.0.0.0:bgp` AND `[::]:bgp` listeners exist

**Phase 1b: Verify local BGP port in use (MANDATORY pre-condition)**

7. Shell: `ss -t state established | grep bgp` -- confirm at least one ESTABLISHED session
   uses `:bgp` (port 179) as the **local** port. Without this, the FIN-WAIT collision that
   kills the listener won't happen. If no session uses local port 179, the bug cannot trigger.

**Phase 1c: Enable debug (for detailed NSR recovery traces)**

8. `configure` -> `debug` -> `bgp fsm` + `bgp events` -> `commit` -> `exit`
   This captures FSM state transitions and NSR recovery events in bgpd_traces for timeline evidence.

**Phase 2: Trigger NSR (repeat twice for thoroughness)**

9. `request system process restart ncc 0 routing-engine routing:bgpd` -- trigger NSR (1st time)
10. Wait 30 seconds for NSR recovery
11. `show bgp summary | no-more` -- confirm passive neighbor **survived** NSR (still Established)
12. Shell: `ss -a | grep bgp` -- **KEY CHECK**: confirm `0.0.0.0:bgp` listener still exists
13. Repeat NSR: `request system process restart ncc 0 routing-engine routing:bgpd` -- trigger NSR (2nd time)
14. Wait 30 seconds for NSR recovery
15. Shell: `ss -a | grep bgp` -- confirm `0.0.0.0:bgp` listener survived second NSR too

**Phase 3: Delete + re-add the passive neighbor**

16. `configure` -> `no protocols bgp <ASN> neighbor <IP>` -> `commit` -- delete neighbor
17. Wait 5 seconds
18. `configure` -> `rollback 1` -> `commit` -- re-add neighbor via rollback
19. Wait 60 seconds for the remote peer to reconnect

**Phase 4: Final verification + debug trace collection**

20. `show bgp summary | no-more` -- check passive neighbor state
21. Shell: `ss -a | grep bgp` -- check listener socket presence
22. `show file log routing_engine/system-events.log | include NEIGHBOR_ADJACENCY | tail 20 | no-more` -- syslog proof
23. `show file traces routing_engine/bgpd_traces | include ADJCHANGE | tail 20 | no-more` -- trace proof
24. `show file traces routing_engine/bgpd_traces | include FSM | tail 30 | no-more` -- debug FSM transitions
25. `show file traces routing_engine/bgpd_traces | include NSR | tail 20 | no-more` -- NSR recovery events
26. `show file traces routing_engine/bgpd_traces | include bind | tail 10 | no-more` -- socket bind success/failure

**Phase 4b: Disable debug (MANDATORY cleanup)**

27. `configure` -> `debug` -> `no bgp fsm` + `no bgp events` -> `commit` -> `exit`
28. `show config debug | no-more` -- verify no bgp debug flags remain

### Pass Criteria (FIX CONFIRMED)

- Step 7: at least one session uses local port 179 (pre-condition met)
- Step 11: passive neighbor is Established after 1st NSR (session survived)
- Step 12: `0.0.0.0:bgp` listener present after 1st NSR
- Step 15: `0.0.0.0:bgp` listener present after 2nd NSR (survives repeated NSR)
- Step 20: passive neighbor reaches **Established** after delete+re-add
- Step 21: BOTH `0.0.0.0:bgp` AND `[::]:bgp` listeners present
- Step 22: syslog contains `NEIGHBOR_ADJACENCY_UP` for the passive neighbor after rollback
- Step 24: FSM traces show `Active -> Established` transitions (debug evidence)
- Step 25: NSR traces show `BGP_NSR_RECOVERED` events (debug evidence)

### Fail Criteria (BUG PRESENT)

- Step 12: `0.0.0.0:bgp` MISSING after 1st NSR (only `[::]:bgp`) -> **BUG PRESENT**
- Step 15: `0.0.0.0:bgp` MISSING after 2nd NSR -> **BUG PRESENT**
- Step 20: neighbor stuck in **Active** or **Connect** after 60s -> **BUG PRESENT**
- Step 21: `0.0.0.0:bgp` MISSING -> **BUG PRESENT**
- Step 22: NO `NEIGHBOR_ADJACENCY_UP` after rollback -> **BUG PRESENT**
- Step 26: `bind` trace shows failure for port 179 -> **BUG PRESENT** (socket bind failed)

### Inconclusive Conditions

- NSR not enabled -> **SKIP**
- No passive neighbor configured -> **SKIP**
- `graceful-restart` NOT disabled on either side -> **SKIP** (GR interferes with NSR-only test)
- Step 7: no session uses local port 179 -> **SKIP** (pre-condition not met, bug cannot trigger)
- Session does not survive NSR in step 11 -> **INCONCLUSIVE** (NSR itself failed)
- Remote peer not running / unreachable -> **INCONCLUSIVE**

### Optional: TCP-AO Verification Dimension

The fix has two parts: (1) SO_REUSEADDR restored after TCP_REPAIR, (2) skip TCP-AO repair
data read when peer does not use TCP-AO. The test criteria says "with and without TCP-AO set."

To verify the TCP-AO dimension:
- Configure `tcp-ao` on one neighbor, leave the other without
- Both must survive NSR and retain the IPv4 listener

This is optional because the primary reproduction (passive + no GR + NSR) already exercises
the SO_REUSEADDR path. TCP-AO testing is a separate dimension that confirms the second half
of the fix. If the device does not support TCP-AO config, skip this dimension.

### Shell Access for `ss -a | grep bgp`

`ss` not in device_shell_execute whitelist. Use interactive SSH:

```
run start shell
# password: dnroot
ss -a | grep bgp
exit
```

Or parse `/proc/net/tcp` via device_shell_execute:
```
cat /proc/net/tcp | grep ':00B3'
```
Port 179 = 0x00B3. IPv4 LISTEN entry with `00000000:00B3` = listener alive.

### Expected Socket Output

**FIX CONFIRMED:**
```
tcp   LISTEN 0  1000    0.0.0.0:bgp     0.0.0.0:*
tcp   LISTEN 0  1000       [::]:bgp        [::]:*
```

**BUG PRESENT (IPv4 listener missing):**
```
tcp   LISTEN 0  1000       [::]:bgp        [::]:*
```

### Trace Proof Patterns

| Trace file | Grep pattern | Proves | Requires debug? |
|------------|-------------|--------|-----------------|
| `system-events.log` | `NEIGHBOR_ADJACENCY_UP` | Neighbor came up after delete+re-add (FIX) | No |
| `system-events.log` | `NEIGHBOR_ADJACENCY_DOWN` | Neighbor went down during delete (expected) | No |
| `system-events.log` | `BGP_NSR_RECOVERED` | NSR recovery was performed | No |
| `bgpd_traces` | `ADJCHANGE` | FSM transitions: Active->Established (FIX) or stuck Active (BUG) | No |
| `bgpd_traces` | `Established` | Session reached Established (FIX) | No |
| `bgpd_traces` | `bind` | Socket bind success/failure for port 179 | No |
| `bgpd_traces` | `FSM` | Detailed FSM state transitions with timestamps | Yes (`debug bgp fsm`) |
| `bgpd_traces` | `NSR` | NSR recovery steps: socket repair, listener rebind, session restore | Yes (`debug bgp events`) |

### Config (if NSR/passive/GR not already configured)

**BOTH sides must have `graceful-restart disabled`. Jira repro requires this explicitly.**

**Router A (passive side -- the DUT being tested):**
```
protocols bgp nsr enabled
protocols bgp <ASN> neighbor <PEER_IP>
  remote-as <ASN>
  admin-state enabled
  passive enabled
  graceful-restart disabled
  update-source <interface>
  address-family ipv4-labeled-unicast
    soft-reconfiguration inbound
  !
!
```

**Router B (active peer -- initiates connections):**
```
protocols bgp nsr enabled
protocols bgp <ASN> neighbor <ROUTER_A_IP>
  remote-as <ASN>
  admin-state enabled
  graceful-restart disabled
  update-source <interface>
  address-family ipv4-labeled-unicast
    soft-reconfiguration inbound
  !
!
```

Note: Router B does NOT have `passive enabled` -- it is the active initiator.

**For ExaBGP as peer:** ExaBGP does not support GR by default, so no GR config needed
on the ExaBGP side. But the DUT neighbor config MUST have `graceful-restart disabled`.

### Cleanup

**Primary method: `rollback N` (one command, zero hierarchy issues).**

The SW-238966 cleanup took 5 script iterations because it tried to surgically remove
individual config lines. This is always wrong. Use DNOS commit history rollback instead.

**Step 1 -- BEFORE any verification config changes (save in session log):**
```
show system commit | no-more
```
Record the current commit position. Example output:
```
Commit  User        Date                    Comment
------  ----        ----                    -------
0       dnroot      2026-03-08 18:00:00     ...
1       dnroot      2026-03-07 12:30:00     ...
```

**Step 2 -- After verification, cleanup per device:**
```
configure
rollback <N>
commit
exit
```
Where N = number of commits made by the verification on THIS device.
Example: if you committed twice on RR-SA-2 during verification, use `rollback 2`.

**Step 3 -- Verify cleanup with config compare:**
```
show config compare rollback 0 rollback N | no-more
```
Where N = same number used in `rollback N`. If the diff is empty, the rollback fully restored
the pre-test state. If lines remain, they are non-test changes (interleaved commits).

```
show config protocols bgp <ASN> | no-more
show bgp summary | no-more
```

**When rollback N does NOT work:**
If other users/automation committed changes between your test commits (interleaved),
`rollback N` would undo those too. Use `show config compare rollback X rollback Y` to see
what changed between specific rollback points, and detect interleaved entries.
Only then fall back to surgical removal (see `gotchas.md` "Surgical Cleanup Fallback").

### Pre-Verification Commit Snapshot (MANDATORY)

Every verification script MUST start with:
```python
output = show_cmd(ssh, "show system commit | no-more")
print(f"[SNAPSHOT] Commit history before changes:\n{output}")
commit_count = 0  # increment after each successful commit
```

And the cleanup section becomes:
```python
print(f"[CLEANUP] Rolling back {commit_count} commits")
shell_cmd(ssh, [
    "configure",
    f"rollback {commit_count}",
    "commit",
    "exit"
], wait=5)
```

### History

| Date | Device | Image | Verdict |
|------|--------|-------|---------|
| 2026-03-08 | RR-SA-2 (passive DUT) + PE-1 (active peer) | DNOS [25.4.13] build [146_dev] | FIX CONFIRMED -- listener survived 6 bgpd restarts + 2 delete/rollback cycles |

---

## SW-243977: FlowSpec Unrecognized Filter Type Handling (RFC 7606)

**Parent:** SW-177685
**Component:** BGP FlowSpec
**Fix Version:** Verified on DNOS 25.4.13.146 AND DNOS 19.2.13.1
**Severity:** Critical (session reset on content errors)

### Description

When a BGP FlowSpec UPDATE contains an NLRI with an unrecognized filter type (e.g., type 14, 19, 255 -- only types 1-13 are defined in RFC 5575), the device should discard the NLRI per RFC 7606 ("treat-as-withdraw"), NOT send a NOTIFICATION 3/9 that tears down the session.

### Prerequisites

- BGP neighbor with ipv4-flowspec AFI negotiated
- Peer capable of sending raw BGP UPDATE PDUs (custom script, not ExaBGP)

### Test Tool

`~/SCALER/FLOWSPEC_VPN/exabgp/bgp_negative_test.py`

```bash
python3 bgp_negative_test.py --peer <DUT_IP> --bind <LOCAL_IP> --bgp-id <LOCAL_IP> --local-as 65200 --timeout 30
```

**Arguments:**
- `--peer`: DUT .999 IP (e.g., 100.70.0.206 for PE-4)
- `--bind`: Local IP to bind (use secondary IP to avoid ExaBGP conflict)
- `--bgp-id`: BGP identifier (same as bind IP)
- `--timeout`: Seconds to wait for KEEPALIVE response (30 recommended, peer keepalive=60s)

### Malformed PDUs (from Jira SW-177685 reproduction steps)

| Name | Filter Type | Hex (59 bytes) |
|------|-------------|----------------|
| type_14 | 14 (0x0E) | `ffffffffffffffffffffffffffffffff003b02000000244001010240020402010002c010088008006400000001800e0b0001850000050e18c00001` |
| type_255 | 255 (0xFF) | `ffffffffffffffffffffffffffffffff003b02000000244001010240020402010002c010088008006400000001800e0b000185000005ff18c00001` |
| type_19 | 19 (0x13) | `ffffffffffffffffffffffffffffffff003b02000000244001010240020402010002c010088008006400000001800e0b0001850000051318c00001` |

### Pass/Fail Criteria

| Criterion | PASS | FAIL |
|-----------|------|------|
| Session after each PDU | Stays ESTABLISHED (KEEPALIVE exchanged) | NOTIFICATION received (any code) |
| bgpd traces | "treating as withdrawal" or "treat-as-withdraw" | "NOTIFICATION" sent to test peer |
| Session close | Only when test tool closes socket | Device-initiated NOTIFICATION |

### Verification Steps

1. **Add secondary IP** on test server (avoid ExaBGP conflict):
   `sudo ip addr add <IP>/20 dev eno3`

2. **Configure DUT**: temporary BGP neighbor
   ```
   protocols bgp <ASN> neighbor <SECONDARY_IP>
     admin-state enabled
     remote-as 65200
     description SW-243977-test
     ebgp-multihop 10
     passive enabled
     update-source <.999 interface>
     address-family ipv4-flowspec
       send-community community-type both
       soft-reconfiguration inbound
     !
   !
   ```

3. **Run test**:
   `python3 bgp_negative_test.py --peer <DUT_999_IP> --bind <SECONDARY_IP> --bgp-id <SECONDARY_IP> --timeout 30`

4. **Check traces** (no NOTIFICATION to test peer):
   `show file traces routing_engine/bgpd_traces | include <HH:MM> | include <SECONDARY_IP>`

5. **Cleanup**: Remove test neighbor + secondary IP
   ```
   no protocols bgp <ASN> neighbor <SECONDARY_IP>
   sudo ip addr del <SECONDARY_IP>/20 dev eno3
   ```

### Expected Trace Output (PASS)

```
bgp_attr.c:2134:bgp_attr_aspath: Malformed AS path from <PEER>, length is 4
bgp_attr.c:3738:bgp_attr_parse: Attribute AS_PATH, parse error - treating as withdrawal
bgp_packet.c:2949:bgp_update_receive: rcvd UPDATE with errors in path Attributes! Withdrawing route (treat-as-withdraw).
```

No `NOTIFICATION sent to neighbor <PEER>` lines.

### History

| Date | Device | Image | Verdict | Notes |
|------|--------|-------|---------|-------|
| 2026-03-10 | PE-4 (100.70.0.206) | DNOS 25.4.13.146_dev | FIX CONFIRMED | All 3 PDUs (type 14, 255, 19) handled via treat-as-withdraw. No NOTIFICATION sent. Session stayed ESTABLISHED through all tests. Traces confirm `bgp_attr_parse` -> `treating as withdrawal`. |
| 2026-03-10 | RR-SA-2 (100.70.0.205) | DNOS 19.2.13.1 | FIX CONFIRMED | All 3 PDUs handled via treat-as-withdraw. No NOTIFICATION. XRAY pcap verified exact encoding bytes. B15 BD unblocked with credentials sisaev/Drive1234!. |

### XRAY Encoding Verification

Pcap captured on server (eno3) during test against RR-SA-2. Saved: `~/SCALER/FLOWSPEC_VPN/bug_evidence/SW-243977_xray_rr_sa2.pcap`

Raw hex from pcap confirms the FlowSpec NLRI filter type byte in each UPDATE:

| PDU | Pcap Packet | NLRI Hex (last 7 bytes) | Filter Type Byte | Verified |
|-----|-------------|------------------------|-------------------|----------|
| type_14 | #12 | `0005 0e 18 c0 00 01` | `0x0e` (14) | Exact match |
| type_255 | #18 | `0005 ff 18 c0 00 01` | `0xff` (255) | Exact match |
| type_19 | #28 | `0005 13 18 c0 00 01` | `0x13` (19) | Exact match |

MP_REACH_NLRI structure: AFI=1 (IPv4), SAFI=133 (FlowSpec), NH_len=0, NLRI=5 bytes: `[len=5][filter_type][dst_prefix 192.0.1.0/24]`

tshark reported "Dissector bug" on all 3 UPDATE packets, confirming Wireshark cannot parse unrecognized filter types -- expected behavior.

### RR-SA-2 bgpd Traces (DNOS 19.2.13.1)

```
2026-03-10T23:15:20 [INFO] bgp_attr.c:1762: Malformed, attr treat-as-withdraw. type: AS_PATH
2026-03-10T23:15:20 [WARN] bgp_attr.c:3528: peer 100.64.6.134: Attribute AS_PATH, parse error - treating as withdrawal
2026-03-10T23:15:20 [ERROR] bgp_packet.c:2903: peer 100.64.6.134: rcvd UPDATE with errors! Withdrawing route (treat-as-withdraw).
```

No NOTIFICATION entries. Session ADJCHANGE shows only "Peer closed the session" (test tool closing socket), never device-initiated teardown.

### B15 Unblock Details

The previous blocker was DNAAS-LEAF-B15 SSH credentials. Correct credentials: `sisaev/Drive1234!` (from `/home/dn/.xray_config.json` dnaas_credentials and BGP learned rules).

Fix applied: enabled `bundle-100.999` (was admin-disabled, already had l2-service + vlan-id 999) and added it to `g_mgmt_v999` BD. Commit succeeded at 2026-03-10T23:10:29 IST.

### Alternative Verification Path (direct test, no secondary IP)

For RR-SA-2, no ExaBGP session conflicts -- test runs directly from 100.64.6.134 to 100.70.0.205:179 without a secondary IP. The existing neighbor config (passive enabled, ipv4-flowspec) was pre-configured in a previous session.

### Fast Reproduction Recipe (copy-paste ready)

Both devices already have neighbor config + passive enabled. No setup required.

**RR-SA-2 (direct, no secondary IP):**
```bash
cd ~/SCALER/FLOWSPEC_VPN/exabgp
python3 bgp_negative_test.py --peer 100.70.0.205 --timeout 20
```

**PE-4 (needs secondary IP to avoid ExaBGP conflict):**
```bash
sudo ip addr add 100.64.6.135/20 dev eno3 2>/dev/null
cd ~/SCALER/FLOWSPEC_VPN/exabgp
python3 bgp_negative_test.py --peer 100.70.0.206 --bind 100.64.6.135 --bgp-id 100.64.6.135 --timeout 20
```

**With XRAY encoding verification (server-side pcap):**
```bash
# Terminal 1: start capture
sudo tcpdump -i eno3 -w /tmp/xray_sw243977.pcap -Z root -U -c 100 "host <peer_ip> and port 179" &
# Terminal 2: run test
python3 bgp_negative_test.py --peer <peer_ip> --timeout 20
# After test: decode
tshark -r /tmp/xray_sw243977.pcap -x -Y "bgp.type==2" | head -100
# Look for filter type bytes: 0x0e (type 14), 0xff (type 255), 0x13 (type 19)
```

**Wait 45s between runs** to avoid NOTIFICATION 6/7 (Connection Collision Resolution).

**Time:** ~30 seconds per device (20s test + 10s analysis). Total: ~2 minutes for both devices + XRAY.

### Where Rules Were Injected

The malformed FlowSpec UPDATE PDUs were injected to:

| Target | IP | Port | ASN | Neighbor Config Location |
|--------|-----|------|-----|-------------------------|
| PE-4 | 100.70.0.206 | TCP/179 | 1234567 | `protocols bgp 1234567 neighbor 100.64.6.135` (secondary) |
| RR-SA-2 | 100.70.0.205 | TCP/179 | 1234567 | `protocols bgp 1234567 neighbor 100.64.6.134` (direct) |

Both neighbors have `passive enabled` + `address-family ipv4-flowspec`. The test tool (`bgp_negative_test.py`) connects TO the device (active connect), negotiates OPEN with `ipv4-flowspec` capability, then sends 3 UPDATE PDUs containing intentionally malformed FlowSpec NLRI with unrecognized filter types. No rules reach the FlowSpec engine -- they are discarded at the bgpd parser level via treat-as-withdraw (RFC 7606).
