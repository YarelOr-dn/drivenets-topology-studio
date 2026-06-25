# Manual Reproduction Steps

**Device:** PE-1
**Generated:** 2026-04-18T20:21:05+00:00

---

## SC01_evpn_to_pw: Non-sticky: remote EVPN -> PW; no RT change; not counted

**Result:** WARN

### Step 1: Verify Prerequisites

- Check: `spirent_available` -- Fix via: `spirent_tool.py connect && reserve`
- Check: `label_pool_configured` -- Fix via: `auto_config`
- Check: `bgp_address_family` -- Fix via: `auto_config`
- Check: `evpn_instance_with_si_and_vpls_rt` -- Fix via: `spirent_vpls_provisioner.py auto-creates SI instance with VPLS RTs under SI subtree`
- Check: `isis_neighbor_up` -- Fix via: `N/A`
- Check: `igp_route_exists` -- Fix via: `N/A`
- Check: `ldp_neighbor_operational` -- Fix via: `N/A`
- Check: `bgp_vpls_session` -- Fix via: `spirent_tool.py bgp-peer --negotiate-afi l2vpn-vpls --vpls-block-size 8 --vpls-nexthop 6.6.6.6`
- Check: `bgp_evpn_session` -- Fix via: `spirent_tool.py bgp-peer --negotiate-afi l2vpn-evpn (same or separate device)`
- Check: `vpls_pw_installed` -- Fix via: `N/A`
- Check: `ingress_label_available` -- Fix via: `N/A`

### Step 2: Capture Baseline (Before Trigger)

Run these commands and save output for comparison:

```
PE-1# show evpn mac-table instance {pw_test_evpn_name} mac {test_mac} | no-more
```

### Step 3: Trigger

**Action:** `move_evpn_to_pw` (method: ``)

### Step 5: Verify

Run these verification commands:

```
PE-1# show evpn mac-table instance {pw_test_evpn_name} mac {test_mac} | no-more
```

**What to check in the output:**

- [ ] Flags ABSENT: F, D
- [ ] Forwarding state: forwarding
- [ ] No ghost MAC entries for this MAC
- [ ] MAC mobility counter incremented

### Findings (automated test)

| Layer | Status | Detail |
|-------|--------|--------|
| mobility_counter | WARN | Mobility counter 1 -> 1 (delta 0) |


## SC02_pw_to_evpn: PW -> EVPN; accept; static entry

**Result:** PASS

### Step 1: Verify Prerequisites

- Check: `spirent_available` -- Fix via: `spirent_tool.py connect && reserve`
- Check: `label_pool_configured` -- Fix via: `auto_config`
- Check: `bgp_address_family` -- Fix via: `auto_config`
- Check: `evpn_instance_with_si_and_vpls_rt` -- Fix via: `spirent_vpls_provisioner.py auto-creates SI instance with VPLS RTs under SI subtree`
- Check: `isis_neighbor_up` -- Fix via: `N/A`
- Check: `igp_route_exists` -- Fix via: `N/A`
- Check: `ldp_neighbor_operational` -- Fix via: `N/A`
- Check: `bgp_vpls_session` -- Fix via: `spirent_tool.py bgp-peer --negotiate-afi l2vpn-vpls --vpls-block-size 8 --vpls-nexthop 6.6.6.6`
- Check: `bgp_evpn_session` -- Fix via: `spirent_tool.py bgp-peer --negotiate-afi l2vpn-evpn (same or separate device)`
- Check: `vpls_pw_installed` -- Fix via: `N/A`
- Check: `ingress_label_available` -- Fix via: `N/A`

### Step 3: Trigger

**Action:** `move_pw_to_evpn` (method: ``)

### Step 5: Verify

Run these verification commands:

```
PE-1# show evpn mac-table instance {pw_test_evpn_name} mac {test_mac} | no-more
```

**What to check in the output:**

- [ ] Flags ABSENT: F, D
- [ ] Forwarding state: forwarding
- [ ] No ghost MAC entries for this MAC


## SC03_sticky_evpn_to_pw: Sticky EVPN RT-2 -> PW; IGNORE move (blackholing risk)

**Result:** FAIL

### Step 1: Verify Prerequisites

- Check: `spirent_available` -- Fix via: `spirent_tool.py connect && reserve`
- Check: `label_pool_configured` -- Fix via: `auto_config`
- Check: `bgp_address_family` -- Fix via: `auto_config`
- Check: `evpn_instance_with_si_and_vpls_rt` -- Fix via: `spirent_vpls_provisioner.py auto-creates SI instance with VPLS RTs under SI subtree`
- Check: `isis_neighbor_up` -- Fix via: `N/A`
- Check: `igp_route_exists` -- Fix via: `N/A`
- Check: `ldp_neighbor_operational` -- Fix via: `N/A`
- Check: `bgp_vpls_session` -- Fix via: `spirent_tool.py bgp-peer --negotiate-afi l2vpn-vpls --vpls-block-size 8 --vpls-nexthop 6.6.6.6`
- Check: `bgp_evpn_session` -- Fix via: `spirent_tool.py bgp-peer --negotiate-afi l2vpn-evpn (same or separate device)`
- Check: `vpls_pw_installed` -- Fix via: `N/A`
- Check: `ingress_label_available` -- Fix via: `N/A`

### Step 3: Trigger

**Action:** `move_evpn_to_pw` (method: ``)

### Step 5: Verify

**What to check in the output:**

- [ ] Forwarding state: forwarding
- [ ] No ghost MAC entries for this MAC

### Findings (automated test)

| Layer | Status | Detail |
|-------|--------|--------|
| bgp_session | FAIL | 0/3 ESTABLISHED |
| timing | WARN | 110.60s > 90.0s (within 2x) |


## SC04_pw_to_sticky_evpn: PW -> Sticky EVPN; accept; datapath static sticky

**Result:** FAIL

### Step 1: Verify Prerequisites

- Check: `spirent_available` -- Fix via: `spirent_tool.py connect && reserve`
- Check: `label_pool_configured` -- Fix via: `auto_config`
- Check: `bgp_address_family` -- Fix via: `auto_config`
- Check: `evpn_instance_with_si_and_vpls_rt` -- Fix via: `spirent_vpls_provisioner.py auto-creates SI instance with VPLS RTs under SI subtree`
- Check: `isis_neighbor_up` -- Fix via: `N/A`
- Check: `igp_route_exists` -- Fix via: `N/A`
- Check: `ldp_neighbor_operational` -- Fix via: `N/A`
- Check: `bgp_vpls_session` -- Fix via: `spirent_tool.py bgp-peer --negotiate-afi l2vpn-vpls --vpls-block-size 8 --vpls-nexthop 6.6.6.6`
- Check: `bgp_evpn_session` -- Fix via: `spirent_tool.py bgp-peer --negotiate-afi l2vpn-evpn (same or separate device)`
- Check: `vpls_pw_installed` -- Fix via: `N/A`
- Check: `ingress_label_available` -- Fix via: `N/A`

### Step 3: Trigger

**Action:** `move_pw_to_evpn` (method: ``)

### Step 5: Verify

**What to check in the output:**

- [ ] Forwarding state: forwarding
- [ ] No ghost MAC entries for this MAC

### Findings (automated test)

| Layer | Status | Detail |
|-------|--------|--------|
| trigger | FAIL | EVPN BGP peer 19.19.19.2 not ESTABLISHED -- cannot inject RT-2. Run: spirent_tool.py protocol-start --device-name EVPN_R |

---

_Generated by /TEST MAC Mobility Orchestrator_