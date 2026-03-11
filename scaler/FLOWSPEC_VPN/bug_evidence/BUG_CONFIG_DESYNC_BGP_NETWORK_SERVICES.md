# BGP Per-AFI Config Desync When Deleting BGP + Network-Services Simultaneously

**Device:** PE-1 / YOR_PE-1
**Image (discovered)**: `26.1.0.20_priv.easraf_flowspec_vpn_wbox_side_22` (build 22)
**Process:** `bgpd` in `routing_engine` container, config manager `dn2oc`
**Discovered:** 2026-02-17 ~19:08 IST
**Investigation method:** vtysh `show running-config` vs DNOS `show config protocols`, bgpd trace analysis

## Retest History

| Date | Image (full path) | Build | Result | Notes |
|------|-------------------|-------|--------|-------|
| 2026-02-17 | `26.1.0.20_priv.easraf_flowspec_vpn_wbox_side_22` | 22 | **BUG PRESENT** | Original discovery. Per-AF settings leak to ipv4-unicast after rollback+commit. |
| 2026-02-19 | `26.1.0.22_priv.easraf_flowspec_vpn_wbox_side_24` | 24 | **FIX CONFIRMED** | All AFs for neighbor 2.2.2.2 show correct settings: send-community both, allowas-in 1, soft-reconfig, TEST_OLD_DENY policy on flowspec-vpn. Zero vtysh_traces warnings. Fix by Amir Ben Avraham merged to routing feature branch. |

---

## One-Line Summary

When `protocols bgp` and `network-services` are deleted and re-committed simultaneously, the DNOS config manager (`dn2oc`) applies VPN address-family neighbor settings to `bgpd` in the **wrong vtysh context** (`config-router` instead of `config-router-af-*`), causing per-AF settings for `ipv4-vpn` and `ipv4-flowspec-vpn` to silently land on `ipv4-unicast` — breaking VPN route exchange while the DNOS running-config appears correct.

---

## Reproduction Steps

```
1. PE-1 has working BGP neighbor 2.2.2.2 (RR-SA-2) with per-AF settings:
   - ipv4-vpn: send-community both, allow-as-in, soft-reconfiguration inbound
   - ipv4-flowspec-vpn: send-community both, allow-as-in, DENY_ALL_FSVPN_OUT out, LLGR
2. User enters configure mode
3. Delete both "protocols bgp" and "network-services" sections simultaneously
4. Re-add/restore both sections and commit
5. DNOS CLI "show config protocols" shows all settings correctly
6. But bgpd internally has the VPN AF settings on the wrong address-family
7. VPN routes are broken: no RT communities sent, AS-loop rejection on received routes
```

---

## Symptoms

| Symptom | Explanation |
|---------|-------------|
| PE-1 sends VPN routes **without RT extended communities** to RR-2 | `send-community both` is NOT active on `ipv4-vpn` in bgpd |
| RR-2 cannot advertise PE-1's VPN routes to PE-4 (RT-Constrain) | Routes lack RT, so RT-Constrain filters them |
| PE-1 rejects PE-4's VPN routes (AS loop detection) | `allow-as-in` is NOT active on `ipv4-vpn` in bgpd |
| `DENY_ALL_FSVPN_OUT` blocks ipv4-unicast outbound | Policy leaked to ipv4-unicast instead of flowspec-vpn |
| `show config protocols` looks **completely normal** | DNOS config DB is correct; bug is in bgpd internal state |

---

## Evidence: vtysh vs DNOS Running-Config Comparison

### PE-1 DNOS Running-Config (LOOKS CORRECT)

```
neighbor 2.2.2.2
  address-family ipv4-vpn
    allow-as-in enabled
    send-community community-type both
    soft-reconfiguration inbound
  !
  address-family ipv4-flowspec-vpn
    allow-as-in enabled
    policy DENY_ALL_FSVPN_OUT() out
    send-community community-type both
    soft-reconfiguration inbound
    long-lived-graceful-restart
      admin-state enabled
      stalepath-time 5 units hours
    !
  !
```

### PE-1 vtysh `show running-config` (ACTUAL bgpd STATE - BROKEN)

```
 address-family ipv4 vpn
 neighbor 2.2.2.2 activate
 exit-address-family                        <-- ONLY activate, nothing else!

 address-family ipv4 flowspec-vpn
 neighbor 2.2.2.2 activate
 neighbor 2.2.2.2 soft-reconfiguration inbound   <-- partial, missing most settings
 exit-address-family

 [global section - applies to ipv4-unicast]
 neighbor 2.2.2.2 send-community extended   <-- LEAKED from ipv4-vpn
 neighbor 2.2.2.2 send-community            <-- LEAKED from ipv4-vpn
 neighbor 2.2.2.2 allowas-in 1              <-- LEAKED from ipv4-vpn
 neighbor 2.2.2.2 route-policy out DENY_ALL_FSVPN_OUT  <-- LEAKED from flowspec-vpn
 neighbor 2.2.2.2 long-lived-graceful-restart enable stale-time 18000  <-- LEAKED
```

### PE-4 vtysh `show running-config` (CORRECT - for comparison)

```
 address-family ipv4 vpn
 neighbor 2.2.2.2 activate
 neighbor 2.2.2.2 send-community extended   <-- correctly placed
 neighbor 2.2.2.2 send-community            <-- correctly placed
 neighbor 2.2.2.2 soft-reconfiguration inbound
 neighbor 2.2.2.2 allowas-in 1              <-- correctly placed
 neighbor 2.2.2.2 as-loop-check enabled
 neighbor 2.2.2.2 dampening enabled
 exit-address-family

 address-family ipv4 flowspec-vpn
 neighbor 2.2.2.2 activate
 neighbor 2.2.2.2 send-community extended   <-- correctly placed
 neighbor 2.2.2.2 send-community            <-- correctly placed
 neighbor 2.2.2.2 long-lived-graceful-restart enable stale-time 18000
 neighbor 2.2.2.2 soft-reconfiguration inbound
 neighbor 2.2.2.2 allowas-in 1              <-- correctly placed
 exit-address-family
```

### Mismatch Table

| Setting | DNOS Config Says | bgpd Has It Under | Correct AF |
|---------|-----------------|-------------------|------------|
| `send-community both` | ipv4-vpn | **global (ipv4-unicast)** | ipv4-vpn |
| `allow-as-in 1` | ipv4-vpn | **global (ipv4-unicast)** | ipv4-vpn |
| `soft-reconfiguration inbound` | ipv4-vpn | **MISSING** | ipv4-vpn |
| `DENY_ALL_FSVPN_OUT out` | ipv4-flowspec-vpn | **global (ipv4-unicast)** | flowspec-vpn |
| `LLGR stale-time 18000` | ipv4-flowspec-vpn | **global (ipv4-unicast)** | flowspec-vpn |
| `allow-as-in 1` | ipv4-flowspec-vpn | **global (ipv4-unicast)** | flowspec-vpn |
| `send-community both` | ipv4-flowspec-vpn | **MISSING** | flowspec-vpn |

---

## Evidence: bgpd Trace (Smoking Gun)

**Timestamp:** `2026-02-17T19:08:45` — the exact moment dn2oc re-applied config to bgpd.

### ipv4-flowspec (CORRECT - settings inside AF context)

```
19:08:45.490820  (config-router)#                address-family ipv4 flowspec
19:08:45.491742  (config-router-af-ipv4-fls)#    neighbor 2.2.2.2 allowas-in 1        OK
19:08:45.492413  (config-router-af-ipv4-fls)#    neighbor 2.2.2.2 send-community both  OK
19:08:45.494658  (config-router-af-ipv4-fls)#    exit
```

### ipv4-flowspec-vpn (BROKEN - exits AF prematurely, remaining settings leak)

```
19:08:45.494987  (config-router)#                     address-family ipv4 flowspec-vpn
19:08:45.495342  (config-router-af-ipv4-fls-vpn)#     neighbor 2.2.2.2 dampening         OK
19:08:45.495634  (config-router-af-ipv4-fls-vpn)#     neighbor 2.2.2.2 soft-reconfig      OK
19:08:45.496564  (config-router-af-ipv4-fls-vpn)#     exit-address-family               <-- EXITS TOO EARLY!
19:08:45.496621  (config-router)#  neighbor 2.2.2.2 route-policy out DENY_ALL_FSVPN_OUT  LEAKED
19:08:45.497569  (config-router)#  neighbor 2.2.2.2 allowas-in 1                          LEAKED
19:08:45.498183  (config-router)#  neighbor 2.2.2.2 LLGR enable stale-time 18000          LEAKED
19:08:45.498794  (config-router)#  neighbor 2.2.2.2 send-community both                   LEAKED
19:08:45.499613  (config-router)#  neighbor 2.2.2.2 as-loop-check enabled                 LEAKED
```

### ROUTE-POLICY debug confirms wrong attach point

```
[ROUTE-POLICY] [ATTACH-POINT] updateCache for '1:peer-out:2.2.2.2:afi-ipv4:safi-unicast'
                                                                            ^^^^^^^^^^^^
                                              Should be safi-flowspec-vpn, NOT safi-unicast!
```

---

## Root Cause Analysis

### What Happened

When `protocols bgp` and `network-services` are deleted and re-committed simultaneously:

1. **Network-services removed** — VRF definitions (RD, RT import/export) deleted from the system
2. **BGP config re-applied to bgpd** — dn2oc generates vtysh commands to reconstruct BGP
3. **VPN AFs depend on VRF context** — `ipv4-vpn`, `ipv6-vpn`, `flowspec-vpn` need VRF route-targets
4. **dn2oc hits dependency issue** — when applying per-AF neighbor settings for VPN SAFIs, VRF context isn't ready
5. **dn2oc exits the AF prematurely** — runs `exit-address-family` after only partial settings
6. **Remaining settings applied at `(config-router)` level** — bgpd interprets them as ipv4-unicast (the default AF)

### Why It's Insidious

- **DNOS `show config` looks 100% correct** — the config DB has the right data
- **`show bgp ipv4 vpn neighbors` hints at the problem** — operational state doesn't match config
- **Only `vtysh show running-config` reveals the truth** — shows what bgpd actually has internally
- **`clear bgp neighbor` does NOT fix it** — the bgpd internal config remains wrong

### Why Non-VPN AFs Were Not Affected

Non-VPN address-families (`ipv4-flowspec`, `ipv6-flowspec`, `ipv4-unicast`, `ipv6-unicast`) don't depend on VRF/network-services definitions, so their per-AF settings were applied correctly inside the proper vtysh context.

---

## Component Ownership

| Component | Role | Bug? |
|-----------|------|------|
| **dn2oc (config manager)** | Translates DNOS config to bgpd vtysh commands | **YES - root cause** |
| **bgpd** | Processes vtysh commands as given | No - behaves correctly for the commands it receives |
| **DNOS config DB** | Stores the intended configuration | No - config DB is correct |

---

## Fix Options

| Option | Description | Persistence | Risk |
|--------|-------------|-------------|------|
| **A: vtysh direct fix** | Enter vtysh, manually apply per-AF settings under correct AFs | Survives until bgpd restart | Low - targeted |
| **B: Re-commit AF config** | Delete + re-add neighbor 2.2.2.2 AF configs (ensure network-services committed first) | Persistent | Medium - session disruption |
| **C: Restart bgpd** | `request system process restart bgpd` to force full config reload | Persistent | High - all BGP sessions bounce |

### Recommended Fix

**Option B** — In DNOS CLI:
1. Ensure `network-services` is committed and stable
2. Delete the neighbor 2.2.2.2 address-family sections for ipv4-vpn and ipv4-flowspec-vpn
3. Commit (this removes the bad state from bgpd)
4. Re-add the address-family sections with all settings
5. Commit again (this applies them in correct AF context since VRFs now exist)
6. Verify via `vtysh -c "show running-config"` that settings are under the correct AFs

---

## Verification Commands

```bash
# Check if bug exists (from Linux shell on the device):
vtysh -c "show running-config" 2>/dev/null | grep -A 10 "address-family ipv4 vpn"
# Should show send-community, allowas-in, soft-reconfiguration under ipv4 vpn
# If only "activate" is present → bug is active

# Check from DNOS CLI:
show bgp ipv4 vpn neighbors 2.2.2.2
# Look for "Send-community: extended" in ipv4-vpn section
# If missing → bug is active

# After fix, verify:
show bgp ipv4 vpn neighbors 2.2.2.2 advertised-routes
# Should show routes WITH RT extended communities
```

---

## Code Analysis (Branch: easraf/flowspec_vpn/wbox_side)

### Key Files Changed

| File | Change | Impact |
|------|--------|--------|
| `routing_manager/handlers/bgp/precommit.py` | `_get_af_hierarchy`: `split('-')` → `replace('-', ' ', 1)` | Fixes AF name for flowspec-vpn (was broken in old code) |
| `precommit.py` | `af_command`: `'ipv4-flowspec' in path` substring check | Matches `ipv4-flowspec-vpn` incorrectly → maps to `ipv4 flowspec` instead of `ipv4 flowspec-vpn` |
| `precommit.py` | `bgp_soo`: early return for flowspec AFs | Skips `add-path-receive` for flowspec (intentional but cuts flow) |
| `precommit.py` | New `bgp_import_export_vpn_afx` handler | Handles afx-level VPN config (new path) |
| `orm_hooks/bgp/set_hooks.py` | `_deduplicate_policy_fields_only` added | Policy deduplication during edit_config stage |
| `orm_hooks/bgp/set_hooks.py` | `set_route_distinguisher_private_value` new path for afx | RD handling for default VRF flowspec-vpn |

### `af_command` Substring Bug

```python
# Line 123 in precommit.py — matches 'ipv4-flowspec-vpn' too!
elif 'ipv4-flowspec' in path:
    hierarchy_cmd.append(f'address-family ipv4 flowspec')  # WRONG for flowspec-vpn!
```

Should check for `'ipv4-flowspec-vpn'` BEFORE `'ipv4-flowspec'` or use exact matching.

### Transaction System Behavior During Rollback

The per-AF neighbor settings are split across separate precommit handlers registered for different sub-paths:
- `config-items` → dampening, soft-reconfiguration, policy (applied correctly inside AF)
- `config-items/send-community` → send-community (MISSING for VPN AFs during rollback)
- `config-items/allow-as-in` → allow-as-in (MISSING for VPN AFs during rollback)
- `config-items/llgr` → LLGR (MISSING for VPN AFs during rollback)

During delete + rollback + commit, the transaction system generates top-level `config-items` items for flowspec-vpn AF (enabling dampening, soft-reconfig) but NOT the sub-path items. The sub-path items are only generated for ipv4-unicast, causing the appearance of "leaked" settings.

### Corrected Reproduction Steps

```
1. PE-1 has working BGP + network-services config
2. configure
3. Delete "protocols bgp" and "network-services"
4. rollback <N>    ← rollback to the original config
5. commit           ← this triggers the bug
6. show config looks correct but bgpd internal state is wrong
```

---

## Related

- **Previous bug:** FlowSpec-VPN Redirect-IP MP_REACH_NLRI Encoding Bug (`BUG_SUMMARY.md`)
- **Affected devices:** Any PE running DNOS 26.1.0.22 on `easraf/flowspec_vpn/wbox_side` branch where bgp + network-services are modified via rollback
- **Branch:** `easraf/flowspec_vpn/wbox_side` (commit `adfded05693f`)
- **Jira:** TBD — file under config-manager / routing_manager component
- **Suspect code:** Transaction system item generation for new flowspec-vpn AF sub-paths during rollback; also `af_command` substring matching bug
