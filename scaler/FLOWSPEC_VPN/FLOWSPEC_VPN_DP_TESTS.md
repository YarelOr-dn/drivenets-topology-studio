# FlowSpec VPN - Data Plane (DP) Focused Test Plan

_Version: 1.3 | Updated: 2026-03-03 | All commands validated on RR-SA-2_
_Limits Source: limits.json + Confluence "(v25.2) Interface Scale & RNR" + Jira SW-182546, SW-206883_
_Bug Evidence: /home/dn/SCALER/FLOWSPEC_VPN/bug_evidence/_

---

## Platform Limits Reference

| Limit | Value | Source |
|-------|-------|--------|
| IPv4 TCAM per NCP | 12,000 | `show system npu-resources`, SW-139913 |
| IPv6 TCAM per NCP | 4,000 | `show system npu-resources`, SW-139913 |
| Max BGP routes total | 20,000 | SW-206883 |
| Max rules per VRF | 3,000 | limits.json |
| Max local policies per AFI | 20 | limits.json, YANG |
| Max local policies total | 40 | limits.json |
| Max match-classes IPv4 (YANG) | 8,000 | dn-flowspec-local-policies.yang |
| Max match-classes IPv6 (YANG) | 4,000 | dn-flowspec-local-policies.yang |
| Policies per forwarding-options | 1 | limits.json |
| Max FlowSpec interfaces | **8,000** (all L3 interfaces) | Confluence "(v25.2) Interface Scale & RNR" |
| Max VRFs with FlowSpec | **No FlowSpec-specific limit** -- follows platform VRF scale: 1.5k (v25.2) / 8k (v25.3+) | SW-182546, SW-206883, Confluence "VRF Scale Roadmap" |
| Max FlowSpec-VPN peers | 8 | limits.json |

> **Note on TCAM sharing:** DP resources (TCAM) are shared among ALL FlowSpec entries regardless of VRF (SW-182546). The 12K IPv4 / 4K IPv6 TCAM pool per NCP is the only hard DP constraint -- it applies across all VRFs and all interfaces.

---

## Prerequisites (Topology and Configuration)

### BGP Peering

| Requirement | Config / Verification |
|-------------|----------------------|
| BGP session to FlowSpec-VPN source | `protocols bgp <asn> neighbor <ip> address-family ipv4-flowspec-vpn admin-state enabled` |
| Address families enabled | `ipv4-flowspec-vpn` and/or `ipv6-flowspec-vpn` on the neighbor |
| Verify session | `show bgp ipv4 flowspec-vpn summary` -- State = Established, PfxAccepted = 0 |
| Route injector | ExaBGP, Arbor, or equivalent -- must advertise SAFI 133/134 |

### VRF with FlowSpec Import

| Requirement | Config / Verification |
|-------------|----------------------|
| At least 1 non-default VRF | `network-services vrf instance <name>` |
| IPv4 FlowSpec import RT | `address-family ipv4-flowspec import-vpn route-target <RT>` under VRF |
| IPv6 FlowSpec import RT (if IPv6 tests) | `address-family ipv6-flowspec import-vpn route-target <RT>` under VRF |
| RT match | ExaBGP/Arbor RT must match VRF import RT exactly |
| Verify RT config | `show config network-services vrf instance <name>` -- confirm import-vpn route-target |

### FlowSpec Interface Binding (for traffic enforcement tests)

_FlowSpec supports all 8,000 L3 interfaces (Confluence "(v25.2) Interface Scale & RNR")._
_Without `flowspec enabled` on the ingress interface, TCAM rules exist but do NOT match traffic (counter stays 0)._

| Requirement | Config / Verification |
|-------------|----------------------|
| FlowSpec enabled on ingress interfaces | `interfaces <intf> flowspec enabled` (under the interface hierarchy) |
| Verify which interfaces have FlowSpec | `show config interfaces \| include flowspec` |
| Verify specific interface | `show config interfaces <intf>` -- look for `flowspec enabled` |

### Local Policies (for Tests 13-16)

| Requirement | Config / Verification |
|-------------|----------------------|
| Clean local policy state | `show flowspec-local-policies policies` -- empty or baseline only |
| Policy application | `forwarding-options flowspec-local ipv4 apply-policy-to-flowspec <policy>` |
| Limit: 1 policy per forwarding-options | Only 1 policy can be applied at a time |

### Multi-VRF Tests (Tests 7, Stress 7)

| Requirement | Config / Verification |
|-------------|----------------------|
| Multiple VRFs configured | Each with unique `import-vpn route-target` under `ipv4-flowspec` |
| Per-VRF RTs | ExaBGP must tag routes with the correct per-VRF RT |

### Traffic Generator (for traffic enforcement tests)

| Requirement | Detail |
|-------------|--------|
| Generator | IXIA, Spirent, or software-based |
| Connectivity | Connected to DUT ingress interface(s) with FlowSpec enabled |
| Matching traffic | Able to generate traffic matching FlowSpec NLRI (dst-prefix, protocol, ports) |

### NCP ID Discovery

NCP IDs are device-specific (not always 0). Before any `show flowspec ncp <NCP-ID>` command:

```
show system npu-resources resource-type flowspec
```

The output table lists all valid NCP IDs (e.g. PE-4 has NCP 6 and NCP 18).

### xraycli Access (for HW-level verification steps)

Access NCP datapath shell:

```
run start shell ncp <NCP-ID> container datapath
```

Then use `xraycli /wb_agent/flowspec/hw_counters` and `xraycli /wb_agent/flowspec/info`.

---

## Show Commands Legend

| Command | What It Shows |
|---------|--------------|
| `show system npu-resources resource-type flowspec` | Per-NCP: Received / Installed / HW entries used/total (IPv4 + IPv6) |
| `show flowspec ncp <NCP-ID>` | Per-rule detail: NLRI, VRF, Actions, Status (Installed / Not Installed) |
| `show flowspec-local-policies ncp <NCP-ID>` | Same as above for local policies |
| `show flowspec instance vrf <vrf> ipv4` | Per-rule counters in specific VRF |
| `show flowspec-local-policies counters` | Per-match-class counters for local policies |
| `show bgp ipv4 flowspec-vpn summary` | BGP session state + PfxAccepted count |
| `show bgp ipv6 flowspec-vpn summary` | Same for IPv6 |
| `show config interfaces \| include flowspec` | Interfaces with `flowspec enabled` |
| NCC shell: `grep flowspec /var/log/messages` | Syslog: UNSUPPORTED_RULE, lack of resources (no CLI `show logging` in DNOS) |
| `xraycli /wb_agent/flowspec/hw_counters` | HW-level: hw_rules_write_fail, hw_rules_delete_fail |
| `xraycli /wb_agent/flowspec/info` | Internal state: ipv4_installed, ipv6_installed, table sizes |

---

## SCALE TESTS

_Parent Jira: SW-234480 (FlowSpec VPN | Scale)_

---

### Scale Test 4: Max IPv4 DP Rules (12K) + Traffic Enforcement

| Step | Action | Command | Expected |
|------|--------|---------|----------|
| 1 | Verify clean DP state | `show system npu-resources resource-type flowspec` | IPv4 HW = 0/12000 |
| 2 | Inject 12,000 IPv4 FlowSpec-VPN rules | ExaBGP / Arbor | 12K routes received |
| 3 | Verify BGP import | `show bgp ipv4 flowspec-vpn summary` | PfxAccepted = 12,000 |
| 4 | Verify DP installation | `show system npu-resources resource-type flowspec` | IPv4 Received = 12,000, Installed = 12,000, HW = 12000/12000 |
| 5 | Verify per-rule NCP status | `show flowspec ncp <NCP-ID>` | All rules show "Status: Installed" |
| 6 | Verify HW counters baseline | `xraycli /wb_agent/flowspec/hw_counters` | hw_rules_write_fail = 0 |
| 7 | Generate matching traffic | Traffic generator | Traffic flowing |
| 8 | Verify traffic enforcement | `show flowspec instance vrf <vrf> ipv4` | Counters increment |
| 9 | **Pass Criteria** | 12K installed AND enforced | HW = 12000/12000, write_fail = 0 |

---

### Scale Test 5: Max IPv6 DP Rules (4K)

| Step | Action | Command | Expected |
|------|--------|---------|----------|
| 1 | Verify clean DP state | `show system npu-resources resource-type flowspec` | IPv6 HW = 0/4000 |
| 2 | Inject 4,000 IPv6 FlowSpec-VPN rules | ExaBGP / Arbor (RT must match VRF ipv6-flowspec import) | 4K routes received |
| 3 | Verify DP installation | `show system npu-resources resource-type flowspec` | IPv6 Received = 4,000, Installed = 4,000, HW = 4000/4000 |
| 4 | Verify per-rule NCP status | `show flowspec ncp <NCP-ID>` | All IPv6 rules "Status: Installed" |
| 5 | Verify HW counters | `xraycli /wb_agent/flowspec/hw_counters` | hw_rules_write_fail = 0 |
| 6 | Generate matching IPv6 traffic | Traffic generator | Traffic flowing |
| 7 | Verify traffic enforcement | `show flowspec instance vrf <vrf> ipv6` | Counters increment |
| 8 | **Pass Criteria** | 4K IPv6 installed AND enforced | HW = 4000/4000, write_fail = 0 |

---

### Scale Test 6: Mixed IPv4 + IPv6 (12K + 4K)

| Step | Action | Command | Expected |
|------|--------|---------|----------|
| 1 | Inject 12,000 IPv4 FlowSpec-VPN rules | ExaBGP with IPv4 flowspec RT | 12K received |
| 2 | Inject 4,000 IPv6 FlowSpec-VPN rules | ExaBGP with IPv6 flowspec RT | 4K received |
| 3 | Verify combined DP | `show system npu-resources resource-type flowspec` | IPv4: 12000/12000, IPv6: 4000/4000 |
| 4 | Verify NCP rule status | `show flowspec ncp <NCP-ID>` | All rules "Status: Installed" across both AFs |
| 5 | Verify HW counters | `xraycli /wb_agent/flowspec/hw_counters` | hw_rules_write_fail = 0 |
| 6 | Verify FlowSpec info | `xraycli /wb_agent/flowspec/info` | ipv4_installed = 12000, ipv6_installed = 4000 |
| 7 | Generate mixed traffic | Traffic generator | IPv4 + IPv6 traffic |
| 8 | Verify both enforced | `show flowspec instance vrf <vrf> ipv4` / `ipv6` | Both counter sets increment |
| 9 | **Pass Criteria** | Separate IPv4/IPv6 TCAM pools coexist | No pool collision, write_fail = 0 |

---

### Scale Test 7: DP Across Multiple VRFs (4 VRFs x 3K)

_VRF scale: platform supports 1.5k VRFs (v25.2) / 8k (v25.3+). FlowSpec has no separate VRF limit (SW-182546). This test uses 4 VRFs to validate shared TCAM isolation._

| Step | Action | Command | Expected |
|------|--------|---------|----------|
| 1 | Configure 4 VRFs with FlowSpec import | VRF config with per-VRF RTs | 4 VRFs ready |
| 2 | Inject 3,000 rules per VRF | ExaBGP with per-VRF RTs | 12K total |
| 3 | Verify DP | `show system npu-resources resource-type flowspec` | IPv4: 12000/12000 |
| 4 | Verify NCP per-VRF rules | `show flowspec ncp <NCP-ID>` | Rules show correct VRF per entry |
| 5 | Verify HW counters | `xraycli /wb_agent/flowspec/hw_counters` | hw_rules_write_fail = 0 |
| 6 | Generate traffic per VRF | Traffic generator | Traffic to all 4 VRFs |
| 7 | Verify per-VRF counters | `show flowspec instance vrf <each> ipv4` | Counters isolated per VRF |
| 8 | **Pass Criteria** | 4 VRFs at per-VRF max (3K), shared DP pool | VRF isolation maintained |

---

### Scale Test 8: Exceed DP Limit Incremental (14K)

| Step | Action | Command | Expected |
|------|--------|---------|----------|
| 1 | Inject 12,000 IPv4 rules | ExaBGP incremental | 12K received |
| 2 | Verify DP full | `show system npu-resources resource-type flowspec` | IPv4: 12000/12000 |
| 3 | Inject 2,000 more | ExaBGP keep previous | 14K total in BGP |
| 4 | Verify DP capped | `show system npu-resources resource-type flowspec` | Received = 14,000, Installed = 12,000 |
| 5 | Verify NCP overflow status | `show flowspec ncp <NCP-ID> \| include "not installed"` | 2,000 rules "Not Installed, out of resources" |
| 6 | Verify HW write failures | `xraycli /wb_agent/flowspec/hw_counters` | hw_rules_write_fail > 0 |
| 7 | Verify syslog (from NCC shell) | `grep UNSUPPORTED_RULE /var/log/messages \| tail -5` | `BGP_FLOWSPEC_UNSUPPORTED_RULE: lack of resources` |
| 8 | Withdraw 2,000 excess | ExaBGP withdraw | Back to 12K BGP |
| 9 | Verify DP intact | `show system npu-resources resource-type flowspec` | IPv4: 12000/12000, no gaps |
| 10 | **Pass Criteria** | DP caps gracefully, syslog warning logged | No crash, no leak |

---

### Scale Test 9: Exceed DP Limit Bulk (15K)

| Step | Action | Command | Expected |
|------|--------|---------|----------|
| 1 | Inject 15,000 rules in single burst | ExaBGP stress mode | 15K advertised |
| 2 | Verify DP capped | `show system npu-resources resource-type flowspec` | Installed = 12,000 |
| 3 | Verify NCP overflow count | `show flowspec ncp <NCP-ID> \| include "not installed"` | ~3,000 lines showing "Not Installed" |
| 4 | Verify HW write failures | `xraycli /wb_agent/flowspec/hw_counters` | hw_rules_write_fail > 0 |
| 5 | Withdraw all | ExaBGP withdraw | 0 routes |
| 6 | Verify DP cleaned | `show system npu-resources resource-type flowspec` | 0/12000 |
| 7 | Verify NCP empty | `show flowspec ncp <NCP-ID>` | No rules listed |
| 8 | **Pass Criteria** | Bulk overflow handled | No crash, TCAM cleaned on withdraw |

---

### Scale Test 11: Sustained Traffic at Scale (30 min)

| Step | Action | Command | Expected |
|------|--------|---------|----------|
| 1 | Install 12,000 rules | ExaBGP / Arbor | 12K installed |
| 2 | Verify DP | `show system npu-resources resource-type flowspec` | 12000/12000 |
| 3 | Verify NCP baseline | `show system npu-resources resource-type flowspec` | Installed = 12,000 |
| 4 | Generate line-rate matching traffic | Traffic generator | Sustained 30 min |
| 5 | Monitor counters every 5 min | `show flowspec instance vrf <vrf> ipv4` | Counters consistently incrementing |
| 6 | Verify NCP after 30 min | `show system npu-resources resource-type flowspec` | Installed still = 12,000 |
| 7 | Verify HW health after 30 min | `xraycli /wb_agent/flowspec/hw_counters` | hw_rules_write_fail unchanged from baseline |
| 8 | **Pass Criteria** | 30 min sustained DP enforcement | No degradation, no rule loss |

---

### Scale Test 13: Max Local Policies (20 per AFI)

| Step | Action | Command | Expected |
|------|--------|---------|----------|
| 1 | Verify clean state | `show flowspec-local-policies policies` | Empty |
| 2 | Configure 20 IPv4 policies | Each with unique match-classes, drop action | Commit success |
| 3 | Apply 1 policy via forwarding-options | `forwarding-options flowspec-local ipv4 apply-policy-to-flowspec <policy>` | Commit success |
| 4 | Verify policies exist | `show flowspec-local-policies policies` | 20 policies listed |
| 5 | Verify NCP installation | `show flowspec-local-policies ncp <NCP-ID>` | All match-classes "Installed" |
| 6 | Verify HW counters | `xraycli /wb_agent/flowspec/hw_counters` | hw_rules_write_fail = 0 |
| 7 | Send traffic to match-classes | Matching traffic | Traffic flowing |
| 8 | Verify DP enforcement | `show flowspec-local-policies counters` | Counters > 0 |
| 9 | **Pass Criteria** | 20 IPv4 policies (max per AFI) | All installed, write_fail = 0 |

---

### Scale Test 14: Max Match-Classes (8,000 IPv4)

| Step | Action | Command | Expected |
|------|--------|---------|----------|
| 1 | Configure 8,000 IPv4 match-classes | Unique dst-prefix/32 each, simple rules (1 TCAM entry) | Commit success |
| 2 | Associate with 1 policy | All 8,000 match-classes under 1 policy | Commit success |
| 3 | Apply policy | `forwarding-options flowspec-local ipv4 apply-policy-to-flowspec <policy>` | Commit success |
| 4 | Verify match-classes | `show flowspec-local-policies match-classes` | ~8,000 listed |
| 5 | Verify NCP installation | `show system npu-resources resource-type flowspec` | IPv4 Received = 8000, Installed = 8000, HW = 8000/12000 |
| 6 | Verify per-rule NCP status | `show flowspec-local-policies ncp <NCP-ID> \| include Installed` | All 8,000 show "Installed" |
| 7 | Verify HW counters | `xraycli /wb_agent/flowspec/hw_counters` | hw_rules_write_fail = 0 |
| 8 | Verify FlowSpec info | `xraycli /wb_agent/flowspec/info` | ipv4_installed = 8000 |
| 9 | Send traffic to 50 match-classes | Matching traffic | Traffic flowing |
| 10 | Verify DP enforcement | `show flowspec-local-policies counters` | 50 counters > 0 |
| 11 | **Pass Criteria** | 8,000 simple match-classes installed | 4K TCAM headroom, write_fail = 0 |

---

### Scale Test 15: Local Policy + BGP Combined DP Share

| Step | Action | Command | Expected |
|------|--------|---------|----------|
| 1 | Configure 100 local match-classes (1 policy) | Drop action, unique prefixes | Commit success |
| 2 | Verify local in DP | `show flowspec-local-policies ncp <NCP-ID>` | 100 installed |
| 3 | Verify DP baseline | `show system npu-resources resource-type flowspec` | IPv4: HW = 100/12000 |
| 4 | Verify FlowSpec info baseline | `xraycli /wb_agent/flowspec/info` | ipv4_installed = 100 |
| 5 | Inject 11,900 BGP rules | ExaBGP / Arbor to VRF | 11,900 received |
| 6 | Verify combined DP | `show system npu-resources resource-type flowspec` | IPv4: HW = 12000/12000 |
| 7 | Verify local still installed | `show flowspec-local-policies ncp <NCP-ID>` | 100 still "Installed" |
| 8 | Verify combined NCP | `show system npu-resources resource-type flowspec` | Installed = 12,000 |
| 9 | Verify HW counters | `xraycli /wb_agent/flowspec/hw_counters` | hw_rules_write_fail = 0 |
| 10 | Inject 500 more BGP rules | Exceed combined limit | 12,400 total in CP |
| 11 | Verify DP capped | `show system npu-resources resource-type flowspec` | Received > 12000, Installed = 12000 |
| 12 | **Pass Criteria** | Local + BGP share TCAM pool | Shared 12K limit enforced |

---

### Scale Test 16: Local Policy Priority Over BGP (DP Contention)

| Step | Action | Command | Expected |
|------|--------|---------|----------|
| 1 | Inject 12,000 BGP rules | Fill DP entirely | HW = 12000/12000 |
| 2 | Verify DP full | `show system npu-resources resource-type flowspec` | 12000/12000 |
| 3 | Verify NCP all BGP | `show system npu-resources resource-type flowspec` | Installed = 12,000 |
| 4 | Configure 100 local match-classes (1 policy) | New prefixes, drop action | Commit success |
| 5 | Verify local installed | `show flowspec-local-policies ncp <NCP-ID>` | 100 "Installed" |
| 6 | Check total DP | `show system npu-resources resource-type flowspec` | Installed = 12,000 (100 local + 11,900 BGP) |
| 7 | Verify BGP eviction in NCP | `show flowspec ncp <NCP-ID> \| include "not installed"` | ~100 BGP rules show "Not Installed" |
| 8 | Verify HW counters | `xraycli /wb_agent/flowspec/hw_counters` | hw_rules_write_fail = 0 (eviction is not a failure) |
| 9 | Send traffic to local policy | Matching prefix | Traffic flowing |
| 10 | Verify local enforces | `show flowspec-local-policies counters` | Counter > 0 |
| 11 | **Pass Criteria** | Local policies take priority | BGP evicted to make room |

---

## HA TESTS (DP Component Restarts)

_Parent Jira: SW-236398 (FlowSpec VPN | HA)_
_Only tests where DP/NCP is the component under test._

---

### HA Test 3: wb_agent Process Restart

| Step | Action | Command | Expected |
|------|--------|---------|----------|
| 1 | Inject 200 FlowSpec-VPN rules | BGP peer | 200 received |
| 2 | Verify DP installed | `show flowspec ncp <NCP-ID>` | 200 "Installed" |
| 3 | Verify HW counters pre-restart | `xraycli /wb_agent/flowspec/hw_counters` | hw_rules_write_fail = 0 |
| 4 | Discover NCP ID | `show system npu-resources resource-type flowspec` | NCP ID identified from table |
| 5 | Restart wb_agent | `request system process restart ncp <NCP-ID> datapath wb_agent` | wb_agent restarts |
| 6 | Verify rules survive restart | `show flowspec ncp <NCP-ID>` | 200 still installed |
| 7 | Verify HW counters post-restart | `xraycli /wb_agent/flowspec/hw_counters` | hw_rules_write_fail = 0 |
| 8 | Verify traffic still enforced | `show flowspec instance vrf <vrf> ipv4` | Counters increment |
| 9 | **Pass Criteria** | wb_agent restart | DP rules persist, write_fail = 0 |

---

### HA Test 5: NCP Container Restart

| Step | Action | Command | Expected |
|------|--------|---------|----------|
| 1 | Inject 200 FlowSpec-VPN rules | BGP peer | 200 received |
| 2 | Verify DP installed | `show flowspec ncp <NCP-ID>` | 200 "Installed" |
| 3 | Verify HW counters pre-restart | `xraycli /wb_agent/flowspec/hw_counters` | hw_rules_write_fail = 0 |
| 4 | Restart NCP container | `request system container restart ncp <NCP-ID> datapath` | NCP datapath restarts |
| 5 | Verify rules re-installed | `show flowspec ncp <NCP-ID>` | 200 re-installed |
| 6 | Verify HW counters post-restart | `xraycli /wb_agent/flowspec/hw_counters` | hw_rules_write_fail = 0 (clean re-program) |
| 7 | Verify FlowSpec info | `xraycli /wb_agent/flowspec/info` | ipv4_installed = 200 |
| 8 | Verify traffic still enforced | `show flowspec instance vrf <vrf> ipv4` | Counters increment |
| 9 | **Pass Criteria** | NCP container restart | DP rules re-programmed, write_fail = 0 |

---

### HA Test 10: NCE Force Restart

| Step | Action | Command | Expected |
|------|--------|---------|----------|
| 1 | Inject 200 FlowSpec-VPN rules | BGP peer | 200 received |
| 2 | Verify DP distributed | `show flowspec ncp <NCP-ID>` | Rules across NCPs |
| 3 | Force restart one NCP | `request system restart ncp <NCP-ID> force` | NCP goes down |
| 4 | Verify other NCPs keep rules | `show flowspec ncp <surviving-NCP-ID>` | Rules on surviving NCPs |
| 5 | Wait for NCP recovery | `show system npu-resources resource-type flowspec` | Restarted NCP reappears in table |
| 6 | Verify recovered NCP gets rules | `show flowspec ncp <recovered-NCP-ID>` | Rules re-programmed |
| 7 | Verify HW counters on recovered NCP | `xraycli /wb_agent/flowspec/hw_counters` (on recovered NCP) | hw_rules_write_fail = 0 |
| 8 | Verify FlowSpec info on recovered NCP | `xraycli /wb_agent/flowspec/info` (on recovered NCP) | ipv4_installed = 200 |
| 9 | **Pass Criteria** | NCP force restart | DP rules redistributed, clean re-program |

---

## STRESS TESTS (DP Counter Operations)

_Parent Jira: SW-236385..SW-236394 (FlowSpec VPN | Stress)_

---

### Stress Test 6: Rapid Counter Clearing Under Load

| Step | Action | Command | Expected |
|------|--------|---------|----------|
| 1 | Inject 500 FlowSpec-VPN rules | BGP peer | 500 received |
| 2 | Verify NCP status | `show system npu-resources resource-type flowspec` | Installed = 500 |
| 3 | Generate continuous matching traffic | Traffic generator | Traffic flowing |
| 4 | Verify DP counters incrementing | `show flowspec instance vrf <vrf> ipv4` | Counters > 0 |
| 5 | Clear counters | `clear flowspec counters` | Success |
| 6 | Verify counters reset | `show flowspec instance vrf <vrf> ipv4` | Counters = 0 |
| 7 | Wait 10s, verify re-increment | `show flowspec instance vrf <vrf> ipv4` | Counters > 0 |
| 8 | Repeat clear 50 times | `clear flowspec counters` x50 | All 50 succeed |
| 9 | Verify no rule loss | `show system npu-resources resource-type flowspec` | Installed still = 500 |
| 10 | Verify HW health after clears | `xraycli /wb_agent/flowspec/hw_counters` | hw_rules_write_fail = 0 |
| 11 | Verify DP still enforcing | `show flowspec instance vrf <vrf> ipv4` | Counters increment after clear |
| 12 | **Pass Criteria** | 50 rapid counter clears | No rule loss, no DP corruption |

---

### Stress Test 7: Counter Clearing Multi-VRF

| Step | Action | Command | Expected |
|------|--------|---------|----------|
| 1 | Configure 5 VRFs with FlowSpec rules | VRF config + rule injection | 5 VRFs active |
| 2 | Verify NCP per-VRF | `show flowspec ncp <NCP-ID>` | Rules show correct VRF per entry |
| 3 | Generate traffic to all 5 VRFs | Traffic generator | Traffic flowing |
| 4 | Verify per-VRF counters | `show flowspec instance vrf VRF1..5 ipv4` | All counters > 0 |
| 5 | Clear counters globally | `clear flowspec counters` | Success |
| 6 | Verify all VRF counters reset | `show flowspec instance vrf VRF1..5 ipv4` | All = 0 |
| 7 | Repeat 20 times | `clear flowspec counters` x20 | All succeed |
| 8 | Verify no cross-VRF leakage | `show flowspec instance vrf <each> ipv4` | Counters isolated per VRF |
| 9 | Verify NCP intact | `show system npu-resources resource-type flowspec` | Installed count unchanged |
| 10 | Verify HW health | `xraycli /wb_agent/flowspec/hw_counters` | hw_rules_write_fail = 0 |
| 11 | **Pass Criteria** | Multi-VRF counter clearing | VRF isolation preserved, no rule loss |

---

## WBOX TESTS (NCP Direct)

_Parent Jira: SW-230651 (Test the feature, under SW-182546 DP enabler)_
_File: wbox/tests/test_flowspec.py_

| Jira Key | Test Name | DP Focus |
|----------|-----------|----------|
| SW-232509 | test_flowspec_vrf_rule_added | BGP FlowSpec rule programmed into NCP with VRF qualifier |
| SW-232510 | test_flowspec_local_policies_vrf_qualifier | Local policy NCP installation with VRF qualifier |
| SW-232511 | test_flowspec_local_policies_vrf_separate_counters | Per-VRF counter isolation in NCP |
| SW-232512 | test_flowspec_local_policies_any_vrf_priority | VRF priority ordering in NCP TCAM |
| SW-232513 | test_flowspec_capacity_with_vrf | TCAM capacity with VRF rules (extended) |
| SW-232514 | test_flowspec_capacity_without_vrf | TCAM capacity without VRF rules (extended) |
| SW-232515 | test_flowspec_capacity_mixed_vrf | TCAM capacity mixed VRF/non-VRF (extended) |

---

## KNOWN DP BUGS (Affecting Scale Tests)

| Bug | Title | Impact on Tests | Status |
|-----|-------|-----------------|--------|
| TCAM_RESERVED_LEAK_BURST | m_reserved leak during bulk injection | Tests 4, 5, 9: burst injection may install fewer rules than expected | Open |
| TCAM_OVERFLOW_NO_RECOVERY | No auto-recovery after TCAM overflow clears | Test 8, 9: after withdrawing blocking rules, overflow rules stay uninstalled | Open |
| LOCAL_POLICY_RESOURCE_LEAK | m_reserved leak on create/delete cycles | Tests 13, 14: after repeated create/delete, rules fail "out of resources" | Open |

_Full evidence: ~/SCALER/FLOWSPEC_VPN/bug_evidence/BUG_*.md_

---

## TCAM Amplification Reference

_Complex match-classes consume multiple TCAM entries per rule._

| Rule Complexity | TCAM Entries Per Rule | Max Rules at 12K TCAM |
|----------------|----------------------|----------------------|
| Simple (dst-ip only) | 1 | 12,000 |
| Medium (3 criteria) | ~2-5 | ~2,400-6,000 |
| Heavy (6 criteria) | ~23x | ~512 |
| packet-length range (>=64 and <=1500) | ~1,437 | ~8 |

_Source: BUG_FLOWSPEC_LOCAL_POLICY_RESOURCE_LEAK.md stress test evidence (PE-4, 2026-02-25)_
