# Manual Reproduction Steps

**Device:** PE-1
**Generated:** 2026-04-18T20:14:42+00:00

---

## SC01_ac_to_pw: Non-sticky: Local AC -> PW; withdraw RT-2; suppression counted

**Result:** PASS

### Step 1: Verify Prerequisites

- Check: `spirent_available` -- Fix via: `spirent_tool.py connect && reserve`
- Check: `label_pool_configured` -- Fix via: `auto_config`
- Check: `bgp_address_family` -- Fix via: `auto_config`
- Check: `evpn_instance_with_si_and_vpls_rt` -- Fix via: `Create EVPN instance PW_TEST_ELAN WITH seamless-integration. VPLS RTs MUST be under SI > protocols > bgp subtree.`
- Check: `isis_neighbor_up` -- Fix via: `spirent_vpls_provisioner.py provisions ISIS on DUT (P2P, area 49.0001) and Spirent (area converted to STC hex 490001)`
- Check: `igp_route_exists` -- Fix via: `N/A`
- Check: `ldp_neighbor_operational` -- Fix via: `N/A`
- Check: `bgp_vpls_session` -- Fix via: `spirent_tool.py bgp-peer --negotiate-afi l2vpn-vpls --vpls-rd {vpls_rd} --vpls-rt {vpls_rt} --vpls-ve-id {vpls_ve_id} --vpls-block-size 8 --vpls-nexthop 6.6.6.6`
- Check: `vpls_pw_installed` -- Fix via: `N/A`
- Check: `ingress_label_available` -- Fix via: `N/A`
- Check: `ac_interface_configured` -- Fix via: `N/A`

### Step 2: Capture Baseline (Before Trigger)

Run these commands and save output for comparison:

```
PE-1# show evpn mac-table instance {pw_test_evpn_name} mac {test_mac} | no-more
```

### Step 3: Trigger

**Action:** `move_ac_to_pw` (method: ``)

### Step 5: Verify

Run these verification commands:

```
PE-1# show evpn mac-table instance {pw_test_evpn_name} mac {test_mac} | no-more
```

**What to check in the output:**

- [ ] Flags ABSENT: F, D
- [ ] Forwarding state: forwarding
- [ ] No ghost MAC entries for this MAC

### Findings (automated test)

| Layer | Status | Detail |
|-------|--------|--------|
| bgp_session | WARN | 0/3 ESTABLISHED (not required for this test) |


## SC02_pw_to_ac: PW -> Local AC (non-sticky); advertise RT-2

**Result:** PASS

### Step 1: Verify Prerequisites

- Check: `spirent_available` -- Fix via: `spirent_tool.py connect && reserve`
- Check: `label_pool_configured` -- Fix via: `auto_config`
- Check: `bgp_address_family` -- Fix via: `auto_config`
- Check: `evpn_instance_with_si_and_vpls_rt` -- Fix via: `Create EVPN instance PW_TEST_ELAN WITH seamless-integration. VPLS RTs MUST be under SI > protocols > bgp subtree.`
- Check: `isis_neighbor_up` -- Fix via: `spirent_vpls_provisioner.py provisions ISIS on DUT (P2P, area 49.0001) and Spirent (area converted to STC hex 490001)`
- Check: `igp_route_exists` -- Fix via: `N/A`
- Check: `ldp_neighbor_operational` -- Fix via: `N/A`
- Check: `bgp_vpls_session` -- Fix via: `spirent_tool.py bgp-peer --negotiate-afi l2vpn-vpls --vpls-rd {vpls_rd} --vpls-rt {vpls_rt} --vpls-ve-id {vpls_ve_id} --vpls-block-size 8 --vpls-nexthop 6.6.6.6`
- Check: `vpls_pw_installed` -- Fix via: `N/A`
- Check: `ingress_label_available` -- Fix via: `N/A`
- Check: `ac_interface_configured` -- Fix via: `N/A`

### Step 3: Trigger

**Action:** `move_pw_to_ac` (method: ``)

### Step 5: Verify

Run these verification commands:

```
PE-1# show evpn mac-table instance {pw_test_evpn_name} mac {test_mac} | no-more
```

**What to check in the output:**

- [ ] MAC is now on the new AC interface (different from baseline)
- [ ] Flags ABSENT: F, D
- [ ] Forwarding state: forwarding
- [ ] No ghost MAC entries for this MAC

### Findings (automated test)

| Layer | Status | Detail |
|-------|--------|--------|
| bgp_session | WARN | 0/3 ESTABLISHED (not required for this test) |


## SC03_sticky_ac_to_pw: Sticky AC -> PW: IGNORE move (SW-194578)

**Result:** PASS

### Step 1: Verify Prerequisites

- Check: `spirent_available` -- Fix via: `spirent_tool.py connect && reserve`
- Check: `label_pool_configured` -- Fix via: `auto_config`
- Check: `bgp_address_family` -- Fix via: `auto_config`
- Check: `evpn_instance_with_si_and_vpls_rt` -- Fix via: `Create EVPN instance PW_TEST_ELAN WITH seamless-integration. VPLS RTs MUST be under SI > protocols > bgp subtree.`
- Check: `isis_neighbor_up` -- Fix via: `spirent_vpls_provisioner.py provisions ISIS on DUT (P2P, area 49.0001) and Spirent (area converted to STC hex 490001)`
- Check: `igp_route_exists` -- Fix via: `N/A`
- Check: `ldp_neighbor_operational` -- Fix via: `N/A`
- Check: `bgp_vpls_session` -- Fix via: `spirent_tool.py bgp-peer --negotiate-afi l2vpn-vpls --vpls-rd {vpls_rd} --vpls-rt {vpls_rt} --vpls-ve-id {vpls_ve_id} --vpls-block-size 8 --vpls-nexthop 6.6.6.6`
- Check: `vpls_pw_installed` -- Fix via: `N/A`
- Check: `ingress_label_available` -- Fix via: `N/A`
- Check: `ac_interface_configured` -- Fix via: `N/A`

### Step 3: Trigger

**Action:** `move_ac_to_pw` (method: ``)

### Step 5: Verify

**What to check in the output:**

- [ ] Forwarding state: forwarding
- [ ] No ghost MAC entries for this MAC
- [ ] Sticky MAC stays on original AC, remote move rejected

### Findings (automated test)

| Layer | Status | Detail |
|-------|--------|--------|
| bgp_session | WARN | 0/3 ESTABLISHED (not required for this test) |


## SC04_pw_to_sticky_ac: PW -> Sticky AC: prefer sticky AC; advertise RT-2

**Result:** SKIP

### Step 1: Verify Prerequisites

- Check: `spirent_available` -- Fix via: `spirent_tool.py connect && reserve`
- Check: `label_pool_configured` -- Fix via: `auto_config`
- Check: `bgp_address_family` -- Fix via: `auto_config`
- Check: `evpn_instance_with_si_and_vpls_rt` -- Fix via: `Create EVPN instance PW_TEST_ELAN WITH seamless-integration. VPLS RTs MUST be under SI > protocols > bgp subtree.`
- Check: `isis_neighbor_up` -- Fix via: `spirent_vpls_provisioner.py provisions ISIS on DUT (P2P, area 49.0001) and Spirent (area converted to STC hex 490001)`
- Check: `igp_route_exists` -- Fix via: `N/A`
- Check: `ldp_neighbor_operational` -- Fix via: `N/A`
- Check: `bgp_vpls_session` -- Fix via: `spirent_tool.py bgp-peer --negotiate-afi l2vpn-vpls --vpls-rd {vpls_rd} --vpls-rt {vpls_rt} --vpls-ve-id {vpls_ve_id} --vpls-block-size 8 --vpls-nexthop 6.6.6.6`
- Check: `vpls_pw_installed` -- Fix via: `N/A`
- Check: `ingress_label_available` -- Fix via: `N/A`
- Check: `ac_interface_configured` -- Fix via: `N/A`

### Step 3: Trigger

**Action:** `learn_on_pw_then_configure_sticky` (method: ``)

### Step 5: Verify

**What to check in the output:**

- [ ] MAC is now on the new AC interface (different from baseline)
- [ ] Forwarding state: forwarding
- [ ] No ghost MAC entries for this MAC
- [ ] Sticky MAC stays on original AC, remote move rejected

---

_Generated by /TEST MAC Mobility Orchestrator_