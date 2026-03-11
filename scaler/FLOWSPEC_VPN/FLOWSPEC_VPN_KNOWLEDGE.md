# FlowSpec VPN in DriveNets DNOS - Knowledge Document

## 1. Introduction - What is FlowSpec?
FlowSpec (Flow Specification) is originally defined in **RFC 5575**. It provides a way to distribute traffic filtering rules using BGP NLRI encoding. Instead of configuring ACLs manually on every router, a central controller (like Arbor or a scrubbing center) can advertise FlowSpec rules via BGP to mitigate DDoS attacks across the network.
* **SAFI 133 (FlowSpec)**: This is the standard FlowSpec address family. It originally applied only to the global/default VRF.
* **Mechanism**: BGP distributes the match fields (e.g., Destination IP, Source IP, Protocol, Ports, Packet Length) and actions (e.g., Drop, Rate-Limit, Redirect) which are then programmed directly into the router's hardware TCAM.

## 2. FlowSpec-VPN - The VPN Extension
**FlowSpec-VPN (SAFI 134)** extends standard FlowSpec to work within MPLS VPN environments (combining **RFC 8955** and **RFC 4364** concepts). 
* **VRF Context**: It adds a Route Distinguisher (RD) to the NLRI to ensure uniqueness across different customers using the same IP space.
* **VRF Import**: It uses Route Target (RT) extended communities to control which VRFs import the rules.
* **No MPLS Labels**: Unlike L3VPN (SAFI 128), FlowSpec-VPN routes do **not** carry MPLS labels. The rules are not forwarded along a label-switched path; they are programmed as TCAM filters on the ingress NCP to act on incoming traffic.
* **Validation**: DNOS does **not** enforce the strict RFC 8955 Section 6 validation or NH reachability checks for FlowSpec-VPN routes.

## 3. DNOS Implementation Specifics (Deviations from RFC)
DriveNets DNOS implements FlowSpec-VPN with several specific deviations from RFC 8955 (implemented under parent epic **SW-182545** and DP enabler **SW-182546**):

| RFC 8955 Standard | DNOS Implementation |
|-------------------|---------------------|
| VPN label in NLRI | **No VPN label** for FlowSpec-VPN NLRI |
| NH reachability check required | **No NH reachability check** needed |
| Validation flow per Section 6 | **Validation NOT required** |
| Redirect-IP via `draft-ietf-idr-flowspec-redirect-ip` (0x0c) | **NOT supported** (Rejected by DP) |
| Redirect-IP via `draft-simpson-idr-flowspec-redirect-02` (0x08) | **Supported** (Uses MP_REACH_NLRI next-hop) |
| Redirect-IP Copy bit (C=0/C=1) | **Only C=0 supported** |
| Multiple VRFs import same RT | **First alphabetically** wins |
| Redirect from non-default VRF to default VRF | **NOT supported** |

## 4. BGP Address Families
* **Global BGP (PE-PE or PE-RR sessions)**: Uses `ipv4-flowspec-vpn` and `ipv6-flowspec-vpn` (SAFI 134). This carries the RD and RT across the network.
* **VRF BGP (VRF-internal context)**: Uses `ipv4-flowspec` and `ipv6-flowspec` (SAFI 133). 
* **Importing**: To pull a FlowSpec-VPN route into a VRF, you configure `import-vpn route-target <rt>` under the VRF's BGP `ipv4-flowspec` address family.

## 5. Configuration Example (DNOS Syntax)
RD must be unique per PE. RT must be shared across the VPN.

```text
! Global BGP Session (PE to RR)
protocols bgp 65001
 neighbor 3.3.3.3
  address-family ipv4-flowspec-vpn
   admin-state enabled
  !
 !
!
! VRF Definition and Interface Attachment
network-services
 vrf instance CUST-A
  protocols bgp 65001
   address-family ipv4-flowspec
    import-vpn route-target 65001:100
    export-vpn route-target 65001:100
   !
   route-distinguisher 65001:100
  !
 !
!
! Interface configuration
interfaces
 ge400-0/0/1.100
  network-services vrf instance CUST-A
  flowspec enabled
 !
!
```

## 6. Control Plane Pipeline (Happy Flow)
When a FlowSpec rule is received, it follows this path through the DNOS architecture:

```text
bgpd --> zebra (rib-manager) --> fib-manager --> NCP wb_agent --> BCM TCAM
```

1. **`bgpd`**: Receives the BGP UPDATE, decodes the NLRI and extended communities. Evaluates the RT import policies. If matched, it passes the rule to zebra.
2. **`zebra` (rib-manager)**: Tracks the route in the FlowSpec DB tracking table and resolves next-hops.
3. **`fib-manager`**: Generates a protobuf message (`FLOWSPEC_RULE_ADD` / `FLOWSPEC_RULE_DELETE`) and sends it to the NCP.
4. **`NCP` (wb_agent)**: In `FlowspecManager.cpp:AddRuleInternal()`, the datapath validates the actions, assigns priority, and reserves qualifiers.
5. **`BCM TCAM`**: The rule is successfully written to the hardware TCAM.

## 7. TCAM Priority and Capacity
Local policies and BGP FlowSpec rules share the same hardware TCAM, but **Local Policies always win over BGP**.

**Priority Ranges** (Lower number = higher precedence):
* **Local Policies**: `0` -- `1,999,999`
* **BGP Rules**: `2,000,000` -- `4,000,000`

**Capacity per NCP** (SW-139913):
* **IPv4**: 12,000 HW entries 
* **IPv6**: 4,000 HW entries
* Note: A single complex rule (especially one with `packet-length` ranges) can consume hundreds or thousands of TCAM entries.
* **Eviction**: Under contention, if the TCAM is full of BGP rules and a local policy is added, BGP rules will be evicted to make room.

## 8. Supported Actions (SAFI 134)
DNOS supports the following actions for FlowSpec VPN:
* **Traffic-rate**: Rate-limit traffic, or Drop when rate=0.
* **RT-Redirect**: Redirect traffic to another VRF via a Route Target.
* **Redirect-IP**: Redirect traffic via a specific IP next-hop (must use Simpson draft, via MP_REACH_NLRI).

**Action Combination Rules**:
| Combination | Result in DNOS |
|-------------|----------------|
| **Traffic-rate (>0) + RT-Redirect** | Both apply |
| **Traffic-rate (>0) + Redirect-IP** | Both apply |
| **Traffic-rate 0 (Drop) + RT-Redirect** | Unsupported (Rule rejected by DP) |
| **Traffic-rate 0 (Drop) + Redirect-IP** | Drop wins |
| **RT-Redirect + Redirect-IP** | RT-Redirect wins, Redirect-IP ignored |
| **Multiple conflicting actions** | Rejected by DP |

*Unsupported Actions*: IETF redirect-ip (0x0c), Traffic-Action sample/terminal, DSCP marking.

## 9. Redirect Behavior Deep Dive
* **RT-Redirect**: If multiple VRFs import the same RT, the **first VRF alphabetically** wins the redirect.
* **Redirect-IP to MPLS Next-Hop**: If the target IP resolves via an MPLS-recursive next-hop (label-switched path), the NCP skips the redirect action **by design**. (`Action 4 skipped, probably because it is unreachable`).
* **Cross-VRF limits**: Redirecting from a non-default VRF into the default VRF is **not supported**.

## 10. Verification Commands
Use this sequence for health checks and debugging:

1. **TCAM Usage**: `show system npu-resources resource-type flowspec`
2. **BGP Rules in DP**: `show flowspec ncp <id>`
3. **Local Rules in DP**: `show flowspec-local-policies ncp <id>`
4. **VRF Datapath View**: `show flowspec instance vrf <VRF> ipv4|ipv6`
5. **Control Plane Sessions**: `show bgp ipv4 flowspec-vpn summary`
6. **Zebra FlowSpec DB**: `show dnos-internal routing rib-manager database flowspec`

**xraycli paths** (Datapath verification):
* `/wb_agent/flowspec/hw_counters` (check `hw_rules_write_fail`)
* `/wb_agent/flowspec/bgp/ipv4/rules`

## 11. Known Bugs and Limitations (Verified)
| Jira | Description | Status / Note |
|------|-------------|---------------|
| **SW-41148** | Redirect-IP skipped for MPLS NH | **BY DESIGN** |
| **SW-206876** | Combined redirect-ip + redirect-to-rt rejected entirely | **SPEC GAP** (bgpd should strip IP) |
| **SW-48486** | Drop + RT-redirect combined is rejected by NCP | Known Limitation |
| **SW-242876** | Redirect-IP NH unreachable in non-default VRF | **FIXED** (rib-manager protobuf updated) |
| - | TCAM leak on priority reshuffle | Bug (m_reserved leak) |
| - | Local-policy resource leak on create/delete cycles | Bug |
| - | IPv4 FlowSpec-VPN import RT bitmap not populated | Bug |

## 12. Platform Limits
Limits verified against platform definitions (`limits.json`):

| Metric | Limit |
|--------|-------|
| Max rules per VRF | 3,000 |
| Max rules total | 20,000 |
| Max FlowSpec-VPN peers | 8 |
| Max local policies | 40 (20 per AFI) |
| Max match-classes (YANG config limit) | 8,000 IPv4 / 4,000 IPv6 |
| Max interfaces with flowspec | 8,000 |
| HW TCAM entries per NCP | 12,000 IPv4 / 4,000 IPv6 |

## 13. RFC and Draft References
* **RFC 5575**: Dissemination of Flow Specification Rules (Base protocol)
* **RFC 4364**: BGP/MPLS IP VPNs (Foundation for VPN routing)
* **RFC 8955**: Dissemination of Flow Specification Rules for IPv4 (Updates 5575)
* **RFC 8956**: Dissemination of Flow Specification Rules for IPv6
* **RFC 5668**: 4-Byte AS Specific BGP Extended Community
* **RFC 7674**: Clarification of the Flowspec Redirect Extended Community
* **draft-simpson-idr-flowspec-redirect-02**: Supported redirect-IP format in DNOS
* **draft-ietf-idr-flowspec-redirect-ip**: **NOT** supported in DNOS
