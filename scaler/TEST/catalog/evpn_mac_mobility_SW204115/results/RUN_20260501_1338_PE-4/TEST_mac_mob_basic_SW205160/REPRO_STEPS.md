# Manual Reproduction Steps

**Device:** PE-4
**Generated:** 2026-05-01T13:39:29+00:00

---

## SC01_L_local_ac: SC01: L> Local AC -- PE-4 learns MAC from its own untagged AC and advertises RT-2

**Result:** FAIL

### Step 1: Verify Prerequisites

- Check: `evpn_instance_exists` -- Fix via: `config_generator.build_minimal_si_evpn_snippet + dnos_atomic_commit`
- Check: `evpn_si_rt_classification` -- Fix via: `N/A`
- Check: `ac_interface_in_evpn_instance` -- Fix via: `N/A`
- Check: `bgp_l2vpn_evpn_established` -- Fix via: `N/A`
- Check: `vpls_pw_installed` -- Fix via: `N/A`
- Check: `mcp_dnaas_teach_plan` -- Fix via: `N/A`
- Check: `mcp_dnaas_teach_plan` -- Fix via: `N/A`
- Check: `mcp_dnaas_teach_plan` -- Fix via: `N/A`
- Check: `spirent_session_reachable` -- Fix via: `N/A`

### Step 2: Capture Baseline (Before Trigger)

Run these commands and save output for comparison:

```
PE-4# show evpn instance {evpn_name} detail | no-more
```

```
PE-4# show evpn mac-table mac 00:de:ad:00:01:01 | no-more
```

```
PE-4# show interfaces ge100-18/0/1 | no-more
```

### Step 3: Trigger

**Action:** `traffic_on_ac1` (method: `spirent_or_manual`)

### Step 5: Verify

Run these verification commands:

```
PE-4# show evpn mac-table mac 00:de:ad:00:01:01 | no-more
```

```
PE-4# show evpn mac-table detail instance {evpn_name} | no-more
```

```
PE-4# show bgp l2vpn evpn route-type 2 | include 00:de:ad:00:01:01 | no-more
```

```
PE-4# show evpn forwarding-table mac-address-table instance {evpn_name} mac 00:de:ad:00:01:01 | no-more
```

```
PE-4# show dnos-internal routing evpn instance {evpn_name} mac-table-ghost detail | no-more
```

```
PE-4# show interfaces ge100-18/0/1 | no-more
```

**What to check in the output:**

- [ ] Flags ABSENT: F, D
- [ ] Source is one of: ['L>', 'ge100-18/0/1']
- [ ] BGP Type-2 route exists for this MAC (`show bgp l2vpn evpn route-type 2 | include <MAC>` plus peer advertised/received routes)
- [ ] Forwarding state: forwarding
- [ ] No ghost MAC entries for this MAC
- [ ] No blackholed MACs in forwarding table

### Findings (automated test)

| Layer | Status | Detail |
|-------|--------|--------|
| preflight_smoke_test | FAIL | L2 path BROKEN: MAC 00:DE:AD:FF:FF:01 never appeared in EVPN_SI_VPLS_1 mac-table after 10.2s (10 polls). Check: DNAAS BD |


## SC02_B_remote_evpn: SC02: B> Remote EVPN -- PE-1 learns MAC locally; PE-4 receives via RT-2

**Result:** FAIL

### Step 1: Verify Prerequisites

- Check: `evpn_instance_exists` -- Fix via: `config_generator.build_minimal_si_evpn_snippet + dnos_atomic_commit`
- Check: `evpn_si_rt_classification` -- Fix via: `N/A`
- Check: `ac_interface_in_evpn_instance` -- Fix via: `N/A`
- Check: `bgp_l2vpn_evpn_established` -- Fix via: `N/A`
- Check: `vpls_pw_installed` -- Fix via: `N/A`
- Check: `mcp_dnaas_teach_plan` -- Fix via: `N/A`
- Check: `mcp_dnaas_teach_plan` -- Fix via: `N/A`
- Check: `mcp_dnaas_teach_plan` -- Fix via: `N/A`
- Check: `spirent_session_reachable` -- Fix via: `N/A`

### Step 2: Capture Baseline (Before Trigger)

Run these commands and save output for comparison:

```
PE-4# show evpn instance {evpn_name} detail | no-more
```

```
PE-4# show bgp l2vpn evpn summary | no-more
```

```
PE-4# show bgp l2vpn evpn route-type 2 | include 00:de:ad:00:02:01 | no-more
```

```
PE-4# show evpn mac-table mac 00:de:ad:00:02:01 | no-more
```

### Step 3: Trigger

**Action:** `remote_pe_traffic` (method: ``)

### Step 5: Verify

Run these verification commands:

```
PE-4# show evpn mac-table mac 00:de:ad:00:02:01 | no-more
```

```
PE-4# show evpn mac-table detail instance {evpn_name} | no-more
```

```
PE-4# show bgp l2vpn evpn route-type 2 | include 00:de:ad:00:02:01 | no-more
```

```
PE-4# show evpn forwarding-table mac-address-table instance {evpn_name} mac 00:de:ad:00:02:01 | no-more
```

```
PE-4# show dnos-internal routing evpn instance {evpn_name} mac-table-ghost detail | no-more
```

**What to check in the output:**

- [ ] Flags ABSENT: F, D, L>, v>
- [ ] Source is one of: ['B>', '1.1.1.1']
- [ ] BGP Type-2 route exists for this MAC (`show bgp l2vpn evpn route-type 2 | include <MAC>` plus peer advertised/received routes)
- [ ] Forwarding state: forwarding
- [ ] No ghost MAC entries for this MAC
- [ ] No blackholed MACs in forwarding table

### Findings (automated test)

| Layer | Status | Detail |
|-------|--------|--------|
| preflight_smoke_test | FAIL | L2 path BROKEN: MAC 00:DE:AD:FF:FF:01 never appeared in EVPN_SI_VPLS_1 mac-table after 10.2s (10 polls). Check: DNAAS BD |


## SC03_v_pw_via_rrsa2_ac: SC03: v> VPLS PW -- RR-SA-2 learns MAC locally on its AC; PE-4 sees it via VPLS PW (label 1032269)

**Result:** FAIL

### Step 1: Verify Prerequisites

- Check: `evpn_instance_exists` -- Fix via: `config_generator.build_minimal_si_evpn_snippet + dnos_atomic_commit`
- Check: `evpn_si_rt_classification` -- Fix via: `N/A`
- Check: `ac_interface_in_evpn_instance` -- Fix via: `N/A`
- Check: `bgp_l2vpn_evpn_established` -- Fix via: `N/A`
- Check: `vpls_pw_installed` -- Fix via: `N/A`
- Check: `mcp_dnaas_teach_plan` -- Fix via: `N/A`
- Check: `mcp_dnaas_teach_plan` -- Fix via: `N/A`
- Check: `mcp_dnaas_teach_plan` -- Fix via: `N/A`
- Check: `spirent_session_reachable` -- Fix via: `N/A`

### Step 2: Capture Baseline (Before Trigger)

Run these commands and save output for comparison:

```
PE-4# show evpn instance {evpn_name} vpls-pw | no-more
```

```
PE-4# show evpn instance {evpn_name} detail | no-more
```

```
PE-4# show bgp l2vpn vpls summary | no-more
```

```
PE-4# show evpn mac-table mac 00:de:ad:00:03:01 | no-more
```

### Step 3: Trigger

**Action:** `remote_pe_traffic` (method: ``)

### Step 5: Verify

Run these verification commands:

```
PE-4# show evpn mac-table mac 00:de:ad:00:03:01 | no-more
```

```
PE-4# show evpn mac-table detail instance {evpn_name} | no-more
```

```
PE-4# show evpn instance {evpn_name} vpls-pw | no-more
```

```
PE-4# show bgp l2vpn evpn route-type 2 | include 00:de:ad:00:03:01 | no-more
```

```
PE-4# show evpn forwarding-table mac-address-table instance {evpn_name} mac 00:de:ad:00:03:01 | no-more
```

```
PE-4# show dnos-internal routing evpn instance {evpn_name} mac-table-ghost detail | no-more
```

**What to check in the output:**

- [ ] Flags ABSENT: F, D, L>, B>
- [ ] Source is one of: ['v>', '2.2.2.2']
- [ ] Forwarding state: forwarding
- [ ] No ghost MAC entries for this MAC
- [ ] No blackholed MACs in forwarding table

### Findings (automated test)

| Layer | Status | Detail |
|-------|--------|--------|
| preflight_smoke_test | FAIL | L2 path BROKEN: MAC 00:DE:AD:FF:FF:01 never appeared in EVPN_SI_VPLS_1 mac-table after 10.2s (10 polls). Check: DNAAS BD |


## SC04_counts_and_stability: SC04: Counts + stability -- all three sources coexist (L+B+v), no suppression, no ghosts, BGP stable

**Result:** FAIL

### Step 1: Verify Prerequisites

- Check: `evpn_instance_exists` -- Fix via: `config_generator.build_minimal_si_evpn_snippet + dnos_atomic_commit`
- Check: `evpn_si_rt_classification` -- Fix via: `N/A`
- Check: `ac_interface_in_evpn_instance` -- Fix via: `N/A`
- Check: `bgp_l2vpn_evpn_established` -- Fix via: `N/A`
- Check: `vpls_pw_installed` -- Fix via: `N/A`
- Check: `mcp_dnaas_teach_plan` -- Fix via: `N/A`
- Check: `mcp_dnaas_teach_plan` -- Fix via: `N/A`
- Check: `mcp_dnaas_teach_plan` -- Fix via: `N/A`
- Check: `spirent_session_reachable` -- Fix via: `N/A`

### Step 2: Capture Baseline (Before Trigger)

Run these commands and save output for comparison:

```
PE-4# show evpn mac-table detail instance {evpn_name} | no-more
```

```
PE-4# show evpn mac-table instance {evpn_name} | no-more
```

```
PE-4# show evpn instance {evpn_name} detail | no-more
```

```
PE-4# show dnos-internal routing evpn instance {evpn_name} mac-table-ghost detail | no-more
```

```
PE-4# show bgp l2vpn evpn summary | no-more
```

```
PE-4# show bgp l2vpn vpls summary | no-more
```

### Step 5: Verify

Run these verification commands:

```
PE-4# show evpn summary | no-more
```

```
PE-4# show evpn instance {evpn_name} detail | no-more
```

```
PE-4# show evpn mac-table detail instance {evpn_name} | no-more
```

```
PE-4# show evpn mac-table instance {evpn_name} | no-more
```

```
PE-4# show evpn forwarding-table mac-address-table instance {evpn_name} | no-more
```

```
PE-4# show dnos-internal routing evpn instance {evpn_name} mac-table-ghost detail | no-more
```

```
PE-4# show bgp l2vpn evpn summary | no-more
```

```
PE-4# show bgp l2vpn vpls summary | no-more
```

```
PE-4# show file traces routing_engine/bgpd_traces | include NOTIFICATION | no-more
```

**What to check in the output:**

- [ ] Flags ABSENT: F, D
- [ ] Forwarding state: forwarding
- [ ] No ghost MAC entries for this MAC
- [ ] No blackholed MACs in forwarding table

### Findings (automated test)

| Layer | Status | Detail |
|-------|--------|--------|
| preflight_smoke_test | FAIL | L2 path BROKEN: MAC 00:DE:AD:FF:FF:01 never appeared in EVPN_SI_VPLS_1 mac-table after 10.2s (10 polls). Check: DNAAS BD |

---

_Generated by /TEST MAC Mobility Orchestrator_