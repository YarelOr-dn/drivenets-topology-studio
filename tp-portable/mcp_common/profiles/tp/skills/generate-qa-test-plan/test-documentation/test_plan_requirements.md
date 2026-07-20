# Test Item Requirements
Refer to this section to ensure the generated tests remain within the specified guidelines and boundaries.

## Test General Guidelines
- Define the overall validation strategy and applicable primary directions.
- Ensure each User Story has at least one test case. This is a mandatory requirement.
- Prioritize User Story tests first, then expand coverage using the TP Checklist Guide (Confluence page ID `3934912829`) as the authoritative category reference. See [Category Coverage Requirements](#category-coverage-requirements) below.
- Identify regression domains and impacted functional areas that require coverage.
- Keep all content grounded in DriveNets' cloud-native, disaggregated, distributed routing architecture.
- Translate the feature into test objectives, preconditions/setup, step-by-step procedures, expected results, negative paths, scale/soak, performance/resiliency, upgrade/rollback, observability/telemetry, interoperability, and regression impacts.
- When information is missing, infer plausible assumptions but label them explicitly as "Assumption".
- Aim for the strongest possible first draft under ambiguity; do not block.
- Use concise technical language, no marketing tone; never invent real IPs, credentials, or partner names (use placeholders like IP_A, USER_X, PARTNER_Y). Cite which docs you relied on when possible (e.g., "Based on Section 3.2 of the feature spec").
- When summarizing test cases using the template, follow it exactly: one-to-one Test Step to Pass Criteria, include "Negative" in the Test Name for negative scenarios, and keep Variants as light modifications of the same test.
- If the user request does not specify whether they want specific tests, ask: Do you want specific tests, or a comprehensive test plan? Clarify this before gathering the content if it is not clear.
- If the user requests specific tests, answer only that request, but keep in mind all the constraints and guidelines.
- If the user prompt does not provide an Epic ID, reject the request with exactly: Missing Epic ID. Provide a valid Epic ID to continue. 
- Focus strictly on QA and test design activities. Do not expand beyond the provided context.
- **Variants are NOT coverage.** If a scenario is important enough to appear in manual QA tests, it must be a standalone test case — not a variant of another test. Variants are only for trivial parameter substitutions (e.g., IPv4 vs. IPv6 of the same test). If the variant changes the topology, the trigger event, the process being restarted, or the data-plane behavior, promote it to a dedicated test case.
- **Flow chaining over duplicated setup.** When 3+ TCs in the same category share the same initial setup steps, use flow chaining: the first TC has the full setup, and subsequent TCs reference the prior TC's end-state in their **Preconditions** field instead of repeating the same steps. See the SKILL.md "Test Flow Chaining" section for rules and constraints.
- **DNOS CLI syntax only.** All CLI commands in Test Steps MUST use DNOS syntax as defined in the RST documentation provided in the epic documentation's `### DNOS CLI Reference (from RST)` section. Do NOT use Cisco IOS/IOS-XR/NX-OS syntax. When the DNOS CLI Reference section is present, cross-reference every CLI command in test steps against it. If a command does not appear in the reference, use the DNOS CLI patterns observed in the reference (e.g., `protocols ospf instance CORE` not `router ospf 1`; `show route table ipv4-unicast` not `show ip route`; `system logging syslog server` not `logging host`). When no RST reference is available, still avoid Cisco-style syntax — use DNOS hierarchical CLI patterns (`protocols`, `network-services`, `system`, `interfaces`).

---

## Category Coverage Requirements

The TP Checklist Guide (Confluence page ID `3934912829`) defines 85 test categories. Every generated test plan must systematically walk through them as described below.

### Standard Categories

All categories are **decision-based**. Evaluate each category's trigger condition against the epic under test. Generate at least one test case for every category whose trigger condition is met. Categories that are not applicable are simply omitted from the test plan — they do not appear in the Test Summary or Test Cases sections. **Do not silently skip any category** — the Stage 2 TC proposal is the explicit record of which categories were included and excluded.

| # | Category | Trigger Condition |
|---|----------|-------------------|
| 2 | Sanity | Always — every feature requires basic sanity validation |
| 3 | CLI (rollback, load override, commit variants, help lines, tab completion, no-command, show config) | Feature adds or modifies CLI configuration or operational commands |
| 4 | Negative Testing | Feature accepts user input or configuration that can be invalid |
| 6 | System Resources Exhaustion | Feature allocates finite system resources (memory, FDs, table entries, sessions) |
| 10 | Error Handling | Feature has failure modes (bad input, unreachable peers, resource exhaustion, timeouts) |
| 17 | High Availability | Feature has state that must survive process restart, container restart, NCC switchover, or failover |
| 24 | Memory & CPU Footprint | Feature adds processes, daemons, or data structures with measurable resource usage |
| 25 | Scale | Feature has documented scale limits or is a table/entry-based resource |
| 27 | Load + Stress | Feature handles sustained traffic, high-rate events, or large configuration loads |
| 28 | Upgrade / Downgrade | Feature has persistent state or configuration that must survive version changes |
| 29 | Input Validations | Feature has YANG constraints, CLI range checks, or API input validation |
| 30 | Defaults | Feature has default configuration values that affect behavior when no explicit knobs are set |
| 34 | Documentation (RST verification) | Feature adds or modifies CLI commands that need RST/help-text verification |
| 42 | CLI — Show Commands (all permutations, pipes, monitor interval) | Feature adds or modifies show commands with filterable/pipeable output |
| 44 | Setup Integrity | Feature has state that must be consistent after topology changes, cluster operations, or config sync |
| 50 | Logs Monitoring | Feature generates specific log messages, system events, or syslog entries |
| 52 | Feature After Delete + Rollback | Feature has configuration that can be deleted and rolled back |
| 57 | Tech-Support | Feature has dedicated data collected in tech-support bundles |
| 75 | Sanitizer | Feature modifies memory-critical C/C++ code paths (not Python-only features); may be deferred to end-of-cycle per team agreement |
| 1 | Interface Types / Services | Feature interacts with network interfaces |
| 5 | Various RIBs | Feature affects routing tables or forwarding |
| 8 | IPv4 / IPv6 | Feature involves IP addressing or address families |
| 11 | Counters | Feature exposes counters (CLI, gNMI, NETCONF, SNMP) |
| 15 | Traps | Feature generates SNMP traps |
| 18 | SNMP | Feature exposes SNMP MIBs |
| 19 | System Events | Feature generates system events |
| 20 | NETCONF | Feature has YANG-modelled config or oper data |
| 21 | gNMI | Feature has gNMI-exposed config or oper data |
| 22 | Extreme Cases | Feature has scale boundaries or throughput limits |
| 37 | Security / Authentication | Feature involves protocol peering, sessions, or access control |
| 45–48 | VRF Testing | Feature supported in non-default VRF |
| 49 | Log Rotation | Feature has log/trace files |
| 51 | Protocol TCP/UDP Port Check | New protocol introduced |
| 60 | Timers | Feature has configurable timer parameters |
| 67 | BGP Neighbor Groups | BGP feature with neighbor-groups |
| 68 | Unsupported NLRI/TLVs | Interop scenarios with 3rd-party peers |
| 77 | YANG Changes | Feature modifies YANG models |
| 84 | Config Groups | Feature with repetitive config (v25.3+) |
| 85 | NSR/GR VRF Consistency | Adding VRF support for a protocol |

Key conditional categories beyond this list exist in the full checklist guide (all 85). Evaluate any additional categories that may apply to the specific feature.

---

## Test Depth Guidelines

### HA Decomposition

For High Availability (category 17), do not generate a single broad HA test. Decompose into **separate, standalone test cases** (not variants) for each relevant sub-dimension:

1. Process restart (graceful and non-graceful) — **one test per distinct process** (e.g., isisd, zebra, wb_agent, rib-manager are each separate tests, not variants of a single "process restart" test)
2. Container restart (routing, DP, infra) — one test per container type
3. NCC switchover and failover — separate tests for graceful switchover vs. ungraceful failover
4. Full device / system restart (cold and warm) — separate tests for cold vs. warm
5. NCE restarts (NCM, NCF, NCP, NCC)
6. Power off/on via PDU
7. GR restarter scenarios (success, each exit condition)
8. GR helper scenarios (entry conditions, each exit condition)
9. NSR scenarios
10. Combined scenarios (GR + NSR, GR helper during NSR, new adjacency during NSR)
11. Oper-state verification before, during, and after convergence

Generate at least one **dedicated test case** per sub-dimension that is relevant to the feature. Do not collapse multiple processes or restart types into variants of the same test.

### Topology and Deployment Variant Coverage

Identify all topology variants, peering models, and deployment scenarios supported by the feature (e.g., iBGP vs. eBGP, physical vs. IRB vs. sub-interface, single-area vs. multi-area, SA vs. CL, different interface types). Generate at least one dedicated test case or variant per topology/deployment model. Do not assume a single topology covers all cases.

### Documentation / RST Verification (Category 34)

When the epic documentation contains a `### DNOS CLI Reference (from RST)` section, Category 34 TCs MUST be concrete and cite actual RST content:

- **Cite the specific RST file path** in the test description (e.g., `dnos_cli/Show Commands/show ospf interfaces.rst`).
- **Include expected fields/output** from the RST file's parameter table in pass criteria — do not use generic "verify documentation matches behavior" language.
- **Verify on-device help text** (`?` output at the CLI prompt) matches the RST documentation's command syntax, parameter descriptions, and valid ranges.
- **Verify parameter ranges and defaults** match the RST documentation — test boundary values if ranges are specified.
- **Verify removing configuration** syntax (`no` form) matches the RST documentation.

When no RST reference section is present in the epic documentation, Category 34 TCs should still be generated if the trigger condition is met, but may use the generic approach (verify help text is present and accurate without citing specific RST paths).

### Protocol-Specific Data-Plane and Forwarding Mechanics

For routing/forwarding features, generate dedicated test cases for each distinct data-plane behavior the feature interacts with. Do not assume a single functional test covers all forwarding modes. Specifically:

- **ECMP:** If the feature affects path computation or nexthop installation, generate a dedicated ECMP test verifying behavior when multiple equal-cost paths exist.
- **Encapsulation modes:** If the feature involves segment routing (SR-MPLS or SRv6), generate tests for each relevant encapsulation mode (e.g., H.Insert, H.Insert.RED, H.Encaps, H.Encaps.RED). Do not assume one mode covers all.
- **SID/label types:** If the feature involves SIDs or labels, generate tests covering each distinct SID type the feature interacts with (e.g., END, END.X, END.DX4, END.DX6, END.DT4, END.DT6 for SRv6; prefix-SID, adjacency-SID for SR-MPLS).
- **Heterogeneous configurations:** If nodes in the topology can have different configurations for the same feature parameter (e.g., different uSID block sizes, different locator lengths, different algorithm definitions), generate a test with heterogeneous values across nodes.
- **Summarization/aggregation interaction:** If the feature operates on prefixes that can be summarized or aggregated, generate a test verifying behavior with summarized prefixes.
- **Multi-topology (MT) vs. multi-instance:** These are distinct concepts. Multi-topology uses different topologies within the same ISIS instance (via MT TLVs). Multi-instance uses separate ISIS instances. If both are relevant, generate separate tests for each — do not treat them as interchangeable.

### Feature Dependency and Dynamic State Changes

Generate dedicated test cases for scenarios where the feature's prerequisites or dependencies change dynamically during operation:

- **Dynamic enable/disable of the parent feature:** If the feature depends on another feature being enabled (e.g., uLoop depends on SRv6 being enabled), generate a test that toggles the parent feature on/off while the dependent feature is configured.
- **Dynamic modification of shared resources:** If the feature uses shared resources (e.g., locators, policies, route-targets), generate a test that modifies those resources while the feature is active.
- **Service overlay interaction:** If the feature is used as a transport for overlay services (e.g., EVPN-VPWS over SRv6 locators), generate a dedicated test validating the overlay service behavior — not just using the service as a traffic verification tool.

### Concurrent and Simultaneous Event Testing

Generate at least one test case for simultaneous/concurrent events when the feature can be affected by multiple topology changes at once:

- **Simultaneous multi-link failures:** If the feature reacts to link events, test what happens when 2+ links change state in the same commit or within the same convergence window.
- **Concurrent HA + topology events:** Test what happens when an HA event (process restart, switchover) occurs simultaneously with a topology change.

### Traffic Loss Threshold Testing

When the epic or user stories specify convergence time requirements or traffic loss thresholds (e.g., "<50ms with TI-LFA", "convergence in up to 10 minutes"), generate a dedicated test case that measures and validates the specific threshold — not just "verify traffic resumes". Include the measurement method in the test steps.

### Customer-Specific Topology and Use Cases

If the epic references a specific customer deployment (e.g., "Bell Canada", "AT&T Artemis"), generate at least one test case that replicates the customer's topology or use case as described in the epic. Use placeholder names (CUSTOMER_A) but match the topology structure, scale, and service configuration described.

### Manual Test Category Alignment

When Jira Test Categories linked to the epic contain subtasks (Testing Tasks), compare the manual test inventory to the generated plan. For each manual test that has no corresponding generated TC (or only a weak partial match), add a **dedicated TC** covering that scenario. Common patterns in manual sanity tests that are often missed:

- **Protocol combinations:** Protocol + BFD (e.g., OSPF+BFD), protocol + RSVP-TE, protocol + SR-TE, protocol + TI-LFA, protocol + Uloop, protocol + SRMS.
- **HA variants:** NSR (distinct from NCC switchover), GR restarter/helper, process/container restarts per protocol.
- **Feature + GR/NSR:** When manual tests list "Feature basic function - GR", "Feature basic function - GR helper", "Feature basic function - NSR", "Feature scale - GR", "Feature scale - NSR", and "Sub-feature (e.g. MoFRR) basic/scale - GR/NSR", generate **dedicated TCs per scenario** — do not assume process/container restart covers GR/NSR.
- **Log/trace rotation (Cat 49):** When manual tests list "logs rotation" or "traces rotation" as separate subtasks, generate **dedicated TCs** for log rotation and traces rotation — do not assume general logs monitoring covers rotation behavior.
- **Multi-vendor interop:** Juniper/Cisco as ABR, non-ABR/ASBR, SRMS enable/disable on third-party peers.
- **Transport/area variants:** SR areas vs. non-SR areas, RSVP-TE primary/backup/bypass, link-flap on bundle-links.
- **Longevity:** TOD (Time-of-Day) overnight/weekend runs.
- **Config retention per channel:** When manual tests list Config retention FTP, SCP, and DNOR as separate tasks, generate a **dedicated TC for each** — do not assume one config persistence test covers all transfer methods. Each channel (FTP, SCP, DNOR) exercises different serialization/transfer paths.
- **Config-block / validation enablers:** When the epic blocks unsupported configurations (e.g., platform validation, CLI/NETCONF block), generate **one TC per blocked config path** covering both CLI and NETCONF rejection. For features with default and non-default VRF (e.g., PIM, static next-table, BGP leak), include dedicated TCs for each VRF context. Include upgrade scenario: existing forbidden config persists; operator can only delete (not modify). Cover all always-required categories (Sanity, CLI, Negative, HA, etc.) even for validation-only features.
- **Additional sanity triggers/integrations:** When the manual sanity category explicitly lists other features that trigger or integrate with the feature under test (e.g., Tracking-policy, EVPN-IRB Centralized, route tracking enablers, routing enablers), generate a **dedicated TC per listed integration** — do not assume the primary feature TC covers all triggers. Each integration exercises a different code path or message flow.
- **IGP summarization and locator propagation:** When manual tests list IGP summary route scenarios (e.g., summary with local L1 locator as only contributor, exact prefix match to local locator, anycast flag interaction with level-assigned locators), generate **dedicated TCs** — do not treat as variants of generic propagation sanity. Each scenario exercises different summarization and TLV logic.
- **BGP L2VPN/EVPN migration (seamless integration):** When manual tests list VPLS NH-unchanged (eBGP), VE-preference/local-preference combinations, RTC for VPLS, down-bit in NLRI, label allocation failure/OOR, inter-AS VPLS, accept-own removal (inverse negative), RFC7606 malformed NLRIs, BGP AS update, site-id config change, admin-state down, scale-limit system events, or zebra checkpoint — generate **dedicated TCs** per scenario. Do not collapse into generic sanity.
- **BGP syslog / scale-limit system events:** When manual tests list BGP maximum-routes or scale-limit syslog events with per peer-type (v4/v6 peering) × address-family (ipv4-uc/ipv6-uc) × scenario (REACHED, CLEARED, limit-change REACHED, limit-change CLEARED, CLEARED NOT triggered, REACHED not re-triggered) decomposition, generate **dedicated TCs per peer-type × AF × scenario** — do not treat v4 vs v6 peering or ipv4-uc vs ipv6-uc as variants of one TC. Each combination exercises different syslog/event code paths. Include "System events present in log file" as standalone TC per peer-type when manual lists it.
- **RestCONF when NETCONF category present:** When manual tests include "NetCONF + RestCONF" with RestCONF as a separate subtask, generate a **dedicated TC for RestCONF** — do not assume NETCONF covers it. RestCONF uses HTTP/JSON.
- **NETCONF/gNMI/RestConf when manual category present:** When manual Test Categories include "gNMI & NETCONF & RestConf Tests", generate **dedicated TCs per management protocol** (config get/set via NETCONF, config get/set via gNMI, RestConf/ODL, oper-items via gNMI/NETCONF) — even if epic states "no OpenConfig". DNOS may expose feature via proprietary YANG models.
- **S-BFD/SR-TE policy-type and discriminator decomposition:** When manual tests list S-BFD or SR-TE scenarios across policy types (static, auto-policy, flex-algo) and discriminator sources (IGP, remote-map, remote-reflector-discriminator), generate **dedicated TCs per policy-type × discriminator combination** — do not assume one generic S-BFD TC covers all. Each combination exercises different instantiation and resolution paths. Include path-type change (SL↔dynamic) and path-priority scenarios as dedicated TCs.
- **BGP RR reflection and EC stripping:** When the feature adds BGP extended communities (e.g., RPKI state), generate **dedicated TCs** for RR reflection of the attribute and EC stripping on eBGP advertisement per RFC.
- **BGP-LS SR-TE S-BFD/BFD down and multi-instance:** When manual tests list S-BFD/BFD down handling or multi-instance admin change for BGP-LS SR-TE policy distribution, generate **dedicated TCs** — do not assume BGP peer-down or scale tests cover them. Each scenario exercises different NLRI withdrawal and registration paths.
- **Scale epic load override swap:** When manual tests list "load override which changes N by N different config" (e.g., 16k↔16k swap), generate a **dedicated TC** — this exercises full config replace/reload at scale, not just generic load override/stress.
- **BGP redistribute + route-policy change stress:** When manual tests list "bgp redistribute + route-policy - policy change (1uc) - stress test" at VRF def or VRF scale, generate **dedicated TCs** — policy change under scale exercises different BGP redistribution and policy re-evaluation paths.
- **IGP redistribute per VRF def/scale:** When manual tests list OSPF/OSPFv3/ISIS redistribute separately for VRF default and VRF scale, generate **dedicated TCs per IGP × VRF context** — each redistributes into different IGP instances.
- **NH reach IP-SLA/BFD per VRF:** When manual tests list "nh reach - vrf def/scale - ip sla" or "nh reach - vrf def/scale - bfd" as separate tasks, generate **dedicated TCs** — IP-SLA and BFD NH tracking at scale exercise different resolution and state paths.
- **Sub-bundle scale:** When manual tests list "nh - reach - scale of sub-bundle" as a separate task, promote to a **standalone TC** — do not leave as variant of generic interface-type test.
- **ISIS/IGP TLV in every LSP fragment:** When manual tests list "TLV in every LSP fragment" or "TLV in all fragments", generate a **dedicated TC** verifying TLV presence in every fragment — do not assume generic sanity covers fragment-level verification.
- **LSP fragmentation size / PDU growth:** When manual tests specify TLV size impact on PDU (e.g., "6 bytes per fragment when TLV added"), generate a **dedicated TC** verifying encoding correctness and PDU size growth.
- **Multiple CSNP/PSNP:** When manual tests list "multiple CSNP" or "multiple PSNP" as a separate task, generate a **dedicated TC** — each PDU type exercises different code paths.
- **Validation disabled / honoring scenarios:** When manual tests list "validation disabled" or "honoring when disabled" or "instance isolation" scenarios for protocol features, generate **dedicated TCs** — even if epic scope is signaling-only, manual tests may cover implemented honoring/validation behavior.
- **BGP color NHT / Flex-Algo resolution decomposition:** When the feature involves BGP nexthop resolution via color-mpls-nh (Flex-Algo, SR-TE policies with color), generate **dedicated TCs per resolution-source combination** — do not assume one generic color-resolution TC covers all. Include: (a) ECMP with 1 NH by flex-algo and 1 NH by SR-TE policy (mixed resolution); (b) ECMP with 1 NH in color-mpls-nh and 1 NH in mpls-nh (algo 0); (c) multiple color extended communities — verify only highest color used for resolution; (d) color set by routing-policy (vs received EC); (e) resolve-nexthop-in &lt;vrf-name&gt; for NH recursion in VRF context (regression). Each combination exercises different NHT and RIB resolution paths.

Generate dedicated TCs when the manual inventory explicitly lists these — do not treat them as variants of generic sanity. **Justification:** Manual QA consistently decomposes these scenarios; collapsing them causes low coverage when comparing generated vs. manual plans.

### Protocol Mechanics and Timers

For protocol features with configurable timers (category 60), generate **dedicated test cases** (not just variants) covering:
- Boundary values: min, max, default, and at least one invalid value
- Timer mismatch between peers
- **Dynamic timer changes while the timer is actively counting down** — this must be a standalone test case, not a variant. Verify whether the change takes effect immediately, on the next trigger, or is rejected.
- Convergence and recovery timing

For protocol state machines, generate tests for key lifecycle events (e.g., LSA aging/refresh/retransmission for OSPF, UPDATE processing for BGP, adjacency state progression).

### Negative Testing — Both Directions

Negative testing (category 4) must cover both patterns:
- **Traditional negative:** Invalid or unsupported configurations are rejected; malformed packets are handled gracefully without crash.
- **Inverse negative:** When a restriction was considered but explicitly not implemented (e.g., a rejected user story), verify the non-restricted behavior still works correctly. When a feature coexists with another feature that might be expected to conflict, verify coexistence.

Include "Negative" in the Test Name for both patterns.

### Combined Persistence and Cross-Event Testing

For features with persistent state or auto-generated configuration, include at least one test that validates persistence across a combined sequence of events:
- Configure → reboot → verify → upgrade → verify
- Configure → switchover → verify → process restart → verify

Do not rely on separate reboot and upgrade tests to implicitly cover the combined case.

### Protection Path Role Decomposition

For features that compute repair/backup paths (e.g., TI-LFA, FRR, RSVP bypass), decompose tests by the **role of the DUT in the repair path**:

- **PLR (Point of Local Repair):** DUT initiates the backup path.
- **PQ-node:** DUT is the merge point where backup rejoins the post-convergence path.
- **Transit node:** DUT is a mid-point in the backup tunnel.
- **Protected prefix / destination:** DUT is the endpoint being protected.

Generate at least one dedicated test case per relevant role, combined with the feature's constraint dimensions (e.g., metric types, affinity constraints, SRLG groups). Do not collapse all roles into a single protection test.

### IGP Interaction Features

When the feature operates within an IGP (IS-IS, OSPF), generate dedicated test cases for interaction with IGP-level mechanisms that affect path computation:

- **Max-metric:** Verify feature behavior when max-metric is configured on a node in the topology.
- **Overload bit:** Verify feature behavior when the overload bit is set on a node.
- **Route leaking / redistribution:** If the feature's routes can be leaked between levels or redistributed, test the interaction.

These are standalone tests, not variants — each mechanism changes the topology's effective metric space.

### Protocol TLV and Attribute Testing

When the feature relies on or interacts with specific protocol TLVs, attributes, or options (e.g., ASLA TLV for IS-IS, extended communities for BGP, ddmap/pad TLV for MPLS OAM), generate **dedicated test cases for each significant TLV/attribute** that the feature supports — not a single high-level "verify TLVs" test. Each TLV/attribute category exercises different parsing, storage, and advertisement code paths. Specifically:

- The TLV/attribute is correctly advertised and received.
- The feature correctly processes the TLV/attribute in its computation.
- Interop with peers that advertise the TLV/attribute differently (or not at all).
- **Per-TLV-category granularity:** When the protocol defines multiple distinct TLV types or NLRI types (e.g., BGP-LS Node/Link/Prefix NLRIs, IS-IS TLVs, OSPF LSA types), generate dedicated TCs for each major category — node-level attributes, link-level attributes, and prefix-level attributes.
- **Per-option completeness:** For OAM/diagnostic features, test each reply mode, each TLV type (ddmap, pad, timestamp, vendor), and each FEC stack configuration. For routing protocol features, test each optional TLV/attribute that the feature can generate or process.

When manual QA tests decompose by TLV type, the generated plan must match that granularity. A single sanity test that mentions "SR TLVs" does not cover per-category correctness.

### Data-Plane Technology Coexistence

When the feature operates on one data-plane technology (e.g., SRv6) but the same protocol can simultaneously use another data-plane technology (e.g., SR-MPLS), generate a dedicated test verifying both technologies operate correctly at the same time without interference.

### Long-Duration Stress Testing

For features that react to topology events (link flaps, route changes), generate at least one test with **extended duration** (hours, not minutes) of continuous event injection:

- Continuous link flap on the primary path for an extended period (e.g., 10 hours).
- Continuous link flap on the alternate/backup path for an extended period.
- Monitor for memory leaks, counter overflows, log rotation issues, and gradual degradation.

This is distinct from short-duration stress tests (category 27) which focus on bulk changes in single commits.

### Stress Scenario Decomposition (Category 27)

When manual QA tests decompose stress testing into multiple dedicated scenarios (e.g., high-volume IPv4 rule injection, high-volume IPv6, mixed AF, rapid rule updates/withdrawals, rapid Route-Target changes, counter clearing under load, BGP session flap under high load, rapid BGP flaps, multi-VRF high rule count), generate **dedicated test cases per distinct stress scenario** — not a single generic stress test. Each scenario exercises different resource consumption, state-machine, and recovery code paths. Do not collapse "IPv4 stress" and "IPv6 stress" into variants of one test when manual tests list them as separate tasks.

### Flowspec/VPN Redirect and Dynamic Re-evaluation

When the feature involves flowspec redirect actions (e.g., redirect-to-VRF, redirect-ip-nh) or dynamic VRF/RT changes, generate **dedicated test cases** for:

- **Redirect re-evaluation:** When unicast import RT is added/removed — verify redirect target re-evaluation.
- **VRF delete and recreate:** Verify redirect rules correctly handle VRF deletion and recreation.
- **New VRF as redirect target:** When a new VRF becomes the redirect target.
- **Redirect-ip-nh nexthop resolution in non-default VRF:** Verify nexthop resolution for redirect-ip-nh action in NDVRF context.

These exercise different event-handling and re-evaluation code paths than static redirect configuration.

### Scale + HA Combined Testing

Generate at least one test that combines **maximum scale** with **HA events**. Do not assume that separate scale tests and HA tests implicitly cover the combined case:

- At maximum scale, perform process restarts, switchovers, and system restarts.
- At maximum scale, perform topology changes (link failures, node additions/removals).
- Measure convergence time and resource consumption at scale during HA events.

### HA Mode Transition Resource Impact

When the feature interacts with HA mechanisms (GR, NSR), generate dedicated CPU and memory footprint test cases for **HA mode transitions**, not just steady-state HA events:

- **GR-specific resource measurement:** Measure CPU and memory consumption specifically during GR restarter and GR helper scenarios. Do not rely on a general CPU/memory test to cover GR-specific resource behavior.
- **NSR-specific resource measurement:** Measure CPU and memory consumption specifically during NSR scenarios (state synchronization, switchover).
- **HA mode change (GR → NSR or NSR → GR):** Generate a dedicated test that changes the HA mode while the feature is configured and active, and measures the resource impact of the transition itself (memory reallocation, state resynchronization).

These are standalone tests — each HA mode has different state management and resource characteristics.

### Upgrade/Downgrade Method Decomposition

When testing upgrade and downgrade (category 28), generate **separate dedicated test cases per upgrade method** — not a single generic upgrade test:

- **DNOR-managed upgrade:** Upgrade → revert → re-upgrade cycle via DNOR. Verify feature configuration and operational state are preserved through each transition.
- **GI/CLI-managed upgrade:** Upgrade → revert → re-upgrade cycle via GI/CLI. Verify feature configuration and operational state are preserved through each transition.
- **ISSU (if supported):** In-service upgrade with traffic verification. Verify feature configuration and operational state are preserved with minimal traffic disruption.

Each upgrade method exercises a different code path for config save/restore and image management. Do not assume one method covers the other.

### Tiebreak and Path Selection Behavior

When the feature involves path selection between multiple candidates (e.g., protected vs. unprotected paths, paths with different SID types), generate a dedicated test verifying the tiebreak logic:

- Verify the feature prefers the expected candidate (e.g., protected adjacency SID over unprotected).
- Verify behavior when tiebreak conditions change dynamically.

### Path Availability × Preference Matrix Testing

When the feature involves path selection with configurable preference (e.g., administrative distance) AND the availability of path types can vary (e.g., some nexthop types may or may not exist in a given domain), generate **dedicated test cases for each distinct combination** of path availability × preference setting — not a single test per preference value with availability as a variant. Each combination exercises a different selection code path:

- **Both path types available + prefer type A:** Verify type A is selected.
- **Both path types available + prefer type B:** Verify type B is selected.
- **Only type A available + prefer type A:** Verify type A is used.
- **Only type A available + prefer type B:** Verify fallback to type A.
- **Only type B available + prefer type A:** Verify fallback to type B.
- **Only type B available + prefer type B:** Verify type B is used.

When a third path type exists (e.g., IGP-shortcut via tunnel), extend the matrix to include combinations where the tunnel is enabled/disabled and the underlying domain has/lacks specific path types. Each cell in the matrix is a standalone test — do not collapse "no path type X in domain Y" into a variant of "both types available."

### BGP Router Role Decomposition

When the feature changes BGP route attributes (e.g., next-hop, communities, entropy label capabilities), decompose tests by the **role of the DUT in the BGP path**:

- **Egress LSR / Originator:** DUT originates routes with the feature's attributes.
- **Transit LSR / Re-advertiser:** DUT receives and re-advertises routes. Test each combination of: NH change type (self, specific IP, no change) × feature knobs (enabled/disabled for each) × attribute version received.
- **Ingress LSR / Consumer:** DUT receives routes and uses the attributes for data-plane decisions. Test each combination of attribute version received × feature knobs.
- **Route Reflector:** DUT reflects routes. Verify the feature's attributes are correctly reflected without modification (unless policy applies). Test with ECMP paths at the RR.

Do not assume a single "transit" test covers all NH change and config combinations — each combination may have different behavior. Generate at least one dedicated test per distinct combination that the feature specification defines.

### BGP attribute-unchanged Interaction

When the feature modifies or adds BGP attributes, generate dedicated test cases for interaction with `attribute-unchanged` and `attribute-unchanged next-hop`:

- Verify behavior when `attribute-unchanged` is configured and the feature's attributes should/should not be modified.
- Verify behavior when `attribute-unchanged next-hop` is configured but NH is changed by policy or neighbor command.
- These are standalone tests, not variants — `attribute-unchanged` fundamentally changes how attributes are propagated.

### BGP Policy Chaining and Precedence

When the feature adds policy options (e.g., `set` commands in routing-policy), generate dedicated test cases for:

- **Policy chaining:** Multiple policies applied sequentially that affect the feature's attributes. Verify the combined effect.
- **Policy vs. neighbor command precedence:** When both a policy and a neighbor-level command affect the same attribute (e.g., NH), verify which takes precedence.
- **Policy on IN vs. OUT direction:** Verify the feature's policy options work correctly on the expected direction and are ignored on the other direction.
- **NH change by policy IN:** If the feature's attributes contain a nexthop, verify behavior when an IN policy changes the route NH (the feature's attribute NH may become mismatched).

### Interop Breadth — Multi-Vendor and Legacy Versions

When the feature involves interoperability (especially with deprecated or legacy protocols), generate dedicated test cases for:

- **Each supported vendor:** If the feature is designed for interop with specific vendors (e.g., Juniper, Cisco), generate a separate test per vendor.
- **Legacy DNOS versions:** If the feature changes wire-format or attribute encoding, test interop with at least one older DNOS version where the feature is not supported (verify graceful handling).
- **Transit through non-supporting devices:** Test the feature when intermediate devices do not understand the feature's attributes and treat them as unknown/opaque.

### Platform Variant Testing

If the feature is supported on multiple platform variants (e.g., SA, CL, cDNOS/containerized), generate at least one **dedicated test case per platform variant** — not just a variant of an existing test. When manual QA tests have a dedicated platform-specific category (e.g., "Functionality - CDNOS"), the generated plan must produce corresponding dedicated TCs for that platform. cDNOS has different networking stack behavior and may exercise different code paths; generate at least one test per distinct DUT role (e.g., DR, BDR, DR-Other) on cDNOS. Do not assume SA testing covers CL or cDNOS behavior.

### Cluster Enabler Epics (B2B, CL-4, J2C)

When the epic is a cluster/routing enabler (e.g., CL-4 B2B, J2C two-node) with Test Categories (BGP, RIB, FIB) containing scale and HA subtasks, generate **dedicated TCs** for each manual test: BGP Neighbor Scale, BGP Route Scale, Graceful Restart, RIB Routes Scale, FIB HA. Include integration TCs for Infra/Datapath and FIB-Manager resource allocation when linked User Stories exist. Do not collapse scale or HA scenarios into variants of a single sanity test.

### Recursive and Special Nexthop Scenarios

When the feature involves route installation with nexthops that can be recursive, generate dedicated test cases for:

- **Recursive nexthop resolution:** If a route's nexthop is resolved via another route (not directly connected), test that the feature correctly handles recursive resolution, including when the resolution path changes.
- **Recursive nexthop across VRFs:** If routes can be leaked or imported between VRFs, test recursive nexthop resolution where the resolving route is in a different VRF than the leaked route.
- **Recursive loop detection:** Test that the system correctly detects and handles recursive nexthop loops (e.g., route A resolves via route B which resolves via route A).
- **Special nexthop types:** If the feature supports routes with special nexthops (e.g., Null0/discard, next-table/VRF lookup), generate a dedicated test for each special nexthop type to verify correct behavior when the feature processes them.

Do not assume that a test with a directly-connected nexthop covers recursive nexthop behavior — these are fundamentally different resolution paths.

### Route Overlap and Sharing Edge Cases

When the feature installs or manipulates routes across multiple contexts (VRFs, tables, instances), generate dedicated test cases for:

- **Same prefix from multiple sources:** If the same prefix can arrive from different VRFs or sources, test the tiebreak and coexistence behavior.
- **Multiple routes sharing the same nexthop:** If multiple routes can share the same nexthop and interface, test that changes to the shared nexthop correctly update all dependent routes.
- **Moving routes between contexts:** If a route can be moved from one VRF/source to another, generate a dedicated test verifying the route is correctly withdrawn from the old context and installed in the new one, including during the transition.

### Cross-Protocol Route Leak Testing

When the feature involves route leaking or redistribution between VRFs, do not test only the primary route type. Generate dedicated test cases for each route type that can be leaked:

- **Static routes** (primary)
- **Connected routes** (verify behavior, even if different from static)
- **IGP routes** (OSPF, OSPFv3, ISIS — each as a separate test if applicable)
- **BGP-originated routes** (network statement, aggregate)

Each route type may have different nexthop resolution behavior when leaked. Do not assume one route type's behavior covers another.

### HA Process Granularity — All Affected Processes

When decomposing HA tests, include **every process in the feature's data path**, not just the obvious ones. Common processes that are often missed:

- **fib_manager (fibmgrd):** If the feature installs routes into FIB, test fib_manager restart.
- **isisd:** If the feature interacts with IS-IS (even indirectly via redistribution), test isisd restart.
- **Routing Engine (RE) restart:** Test the full routing engine container restart, not just individual process restarts.
- **LOFD (Link-Order Failure Detection):** If the feature reacts to link events, test LOFD scenarios where link failure order matters.

### BGP Update-Group Behavior

When the feature modifies BGP attributes that affect update-group formation (e.g., per-neighbor policy differences, NH changes), generate at least one test verifying:

- Neighbors in the same update-group receive the same attributes.
- Neighbors in different update-groups (due to different feature config) receive different attributes.
- Changes to the feature's config correctly trigger update-group re-evaluation.

### Mixed Capability Paths for Same Prefix

When the feature introduces a capability that may or may not be present on different paths to the same prefix, generate a dedicated test for:

- **Same prefix, mixed capability paths:** One path has the capability, another does not. Verify correct best-path selection and data-plane behavior (e.g., whether the capability is used depends on the selected best path).
- This is distinct from ECMP testing — it covers the single best-path case where multiple candidates exist.

### Configuration Persistence and Retention Testing

When the feature introduces new configuration knobs (especially leaflists or scaled configuration), generate **dedicated test cases for each configuration retention/transfer method** — not a single config persistence test. Each method exercises a different serialization, transfer, and deserialization path and may truncate or mishandle large configurations differently:

- **FTP:** Save config to an FTP server, clear config on device, restore from FTP, verify feature state and operation.
- **SCP:** Save config via SCP, clear config on device, restore from SCP, verify feature state and operation.
- **DNOR:** Save config to DNOR, remove it from the device, restore from DNOR, verify feature state and operation.
- **Config file load:** Verify the feature's configuration can be loaded from a saved configuration file (load override, load merge).

Do not assume that CLI rollback or load-override tests cover config retention — FTP/SCP/DNOR transfer methods serialize and deserialize configuration differently.

### Route Reflector and Special Peering Roles

When the feature modifies BGP path selection, advertisement, or installation behavior, generate dedicated test cases for each special peering role:

- **Route Reflector (RR):** Verify the feature's behavior when the DUT is an RR and the affected paths are reflected to clients. Verify the feature's behavior when the DUT is an RR client.
- **Confederation peers:** If applicable, verify the feature's behavior across confederation boundaries.

Do not assume that standard iBGP/eBGP tests cover RR behavior — RR has different path advertisement rules.

### Mixed Protocol Type Testing

When the feature can operate on both iBGP and eBGP sessions simultaneously, generate at least one dedicated test with a **mixed topology** where both iBGP and eBGP peers are present and the feature is applied to both. Do not rely on separate iBGP-only and eBGP-only tests to implicitly cover the mixed case — interaction between the two may reveal issues.

### Dynamic Peer Membership Changes

When the feature involves group-based configuration (e.g., neighbor-groups, peer-groups, policy-groups), generate dedicated test cases for **moving entities between groups** while the feature is active:

- Move a peer from standalone to a group (and vice versa).
- Move a peer from one group to another group.
- Verify the feature's behavior is immediately updated to reflect the new group membership.

### Bidirectional VRF Leak Testing

When the feature involves VRF route leaking or cross-VRF path evaluation, generate dedicated test cases for **both directions** of the leak:

- **Default VRF → Non-default VRF:** Verify the feature's behavior for paths leaked from default to non-default VRF.
- **Non-default VRF → Default VRF:** Verify the feature's behavior for paths leaked from non-default to default VRF.
- **Non-default VRF → Another Non-default VRF:** If applicable, verify cross-VRF leak between two non-default VRFs.
- **Combined local + imported ECMP:** When a VRF has both locally received paths and imported paths for the same prefix, verify the feature correctly handles the combined ECMP evaluation.

Do not assume that testing one direction of VRF leak covers the other — the path resolution and attribute handling may differ.

### Per-Protocol Test Decomposition

When the feature affects multiple routing protocols (e.g., BGP, IS-IS, OSPFv3, static routes), generate **dedicated test cases per protocol** — not a single "routing" test that mentions all protocols. Each protocol has different adjacency formation, route advertisement, redistribution, and convergence behavior. Specifically:

- **Adjacency/session establishment:** One test per protocol verifying the feature works with that protocol's session/adjacency mechanism.
- **Redistribution:** If the feature's routes can be redistributed into or from a protocol, generate a dedicated redistribution test per protocol.
- **ECMP:** If the feature affects path computation, generate a dedicated ECMP test per protocol.
- **Convergence:** If the feature affects convergence, generate a dedicated convergence/timing test per protocol.
- **Scale:** Generate a dedicated scale test per protocol, not just one combined scale test.

Do not assume that testing the feature with one protocol covers behavior with another.

### Per-AFI-SAFI BGP Testing

When the feature involves BGP peering or route exchange, generate dedicated test cases for each relevant AFI-SAFI (address family), not just IPv6 unicast. Common AFI-SAFIs to consider:

- IPv6 unicast, IPv4 unicast
- VPNv4, VPNv6
- IPv4/IPv6 Labeled-Unicast (LU)
- L2VPN-EVPN, L2VPN-VPLS
- IPv4/IPv6 Flowspec
- IPv4 Multicast
- RT-Constraints

Each AFI-SAFI may have different next-hop handling, attribute propagation, and session behavior. Do not assume one AFI-SAFI covers another.

### GRT vs. VRF as Separate Tests

When the feature operates in both default VRF (GRT) and non-default VRF, generate **separate dedicated test cases** for GRT and VRF — not a single test with VRF as a variant. VRF introduces different route table isolation, interface binding, and potentially different protocol behavior. This applies to:

- Functional tests (sanity, adjacency, route exchange)
- Scale tests
- HA tests
- Negative tests

### IGP Redistribution, Default-Originate, and Source Decomposition

When the feature modifies interface addressing, route installation, or IGP behavior, generate **dedicated test cases per redistribution source × per aspect** — not a single redistribution test that covers all sources in one TC. Each source has different route characteristics, metric handling, and prefix-set interaction. Specifically:

- **Per source:** Generate a separate basic redistribution test for each source (connected→IGP, static→IGP, BGP→IGP, IGP→IGP).
- **Per aspect per source:** For each source, generate separate tests for: metric assignment (type-1/type-2), prefix-set filtering, communication/traffic impact of prefix-set changes, and maximum redistributed prefix limit.
- **Route policy interaction:** Verify route policies can match and modify redistributed routes from feature-affected interfaces.
- **Route tagging:** If the feature supports assigning tags to redistributed routes, generate a dedicated test for route tagging per source.
- **DAD interaction with redistribution:** If the feature involves address validation (e.g., DAD), verify that routes for addresses that fail validation are NOT redistributed.
- **Default-originate:** If the feature supports default-information originate, generate a dedicated test covering both with and without the `always` option. Verify default route origination works correctly with the feature active.

Do not collapse multiple redistribution sources into a single test — each source exercises different code paths for route selection, metric calculation, and LSA generation.

### Interface-Type CLI Decomposition

When the feature applies to multiple interface types (physical, sub-interface, bundle, sub-bundle, IRB), generate **dedicated CLI test cases per interface type** — not a single CLI test that covers all types. Each interface type may have different configuration hierarchy, commit validation, and operational behavior.

When the feature operates on in-band interfaces, include **breakout and sub-breakout port types** in the interface type decomposition — not just physical, bundle, sub-interface, and IRB. Breakout ports have different port naming, speed characteristics, and parent-child relationships that may affect feature behavior. Generate at least one dedicated test case covering the feature on a breakout port if the platform supports breakout interfaces.

### Interoperability Per Protocol

When the feature involves protocol interaction with third-party devices, generate dedicated interoperability test cases **per protocol** (e.g., IS-IS interop, OSPFv3 interop, BGP interop). Each protocol has different wire-format, TLV/attribute handling, and adjacency behavior that may differ across vendors. Include at least Cisco and Juniper as interop targets.

### Router Advertisement and NDP Interaction

When the feature modifies IPv6 addressing on interfaces, generate dedicated test cases for:

- **Router Advertisement (RA) server:** Verify RA correctly advertises all configured prefixes.
- **RA prefix filtering:** Verify RA prefix filtering works correctly with multiple addresses.
- **Static NDP entries:** Verify static NDP entries work correctly on interfaces with multiple addresses.
- **RA scale:** Verify RA behavior at maximum address scale.

### ECMP Decomposition — Recursive vs. Non-Recursive

When the feature affects ECMP path installation, decompose ECMP tests into:

- **Same-interface ECMP (recursive):** Multiple equal-cost paths with next-hops on the same interface, resolved recursively.
- **Same-interface ECMP (non-recursive):** Multiple equal-cost paths with directly-connected next-hops on the same interface.
- **Cross-interface ECMP:** Equal-cost paths with next-hops on different interfaces.

Do not assume one ECMP topology covers all cases — recursive and non-recursive resolution paths are fundamentally different. See also: ECMP Recursive Route Scenarios, ECMP Decomposition by Protection Type, ECMP/LFA with Mixed Path Types, and Multi-Node ECMP Decomposition for additional ECMP dimensions.

### Protocol-Specific HA Decomposition

When the feature involves multiple routing protocols, decompose HA tests by **protocol × HA event type** — not just by HA event type alone. Each protocol may have different GR/NSR behavior, different convergence characteristics, and different state recovery:

- BGP HA: process restart, container restart, device restart, NCC switchover
- IS-IS HA: process restart, container restart, device restart, NCC switchover
- OSPFv3 HA: process restart, container restart, device restart, NCC switchover

Do not assume that testing HA with one protocol covers HA behavior with another.

### Policy-Language Feature Testing

When the feature extends or modifies a policy language (e.g., route-policy, prefix-list matching, community matching), generate dedicated test cases for:

- **Policy compilation/cache interaction:** If the policy engine uses shared caches or compiled representations, test that the new feature works correctly when multiple neighbors share the same policy and when different neighbors use different policies with the feature.
- **Policy parameter passing:** If the feature supports parameterized values ($variable), test with parameters for all variable positions (prefix, operator values, thresholds).
- **Policy nesting/chaining:** If the feature can be used in policies that are called from other policies (exec-policy, apply), test the feature in nested policy contexts.
- **Editor/IDE integration:** If the feature includes editor support (syntax highlighting, auto-complete), verify the editor correctly handles the new syntax.
- **Action ordering within a single rule:** If the feature defines a deterministic processing order between multiple actions that modify the same attribute (e.g., list-based operations before direct-set operations), generate a **dedicated test case per attribute type per action combination** verifying the correct order. Do not assume that testing one combination covers all — each list-option variant (delete, delete-not-in, replace, additive) combined with each direct-set variant (with/without additive) may produce different results. Include verification that `show config` output reflects the processing order.
- **Policy rule with no match criteria vs. empty match resource:** When the feature adds a new match criterion (e.g., prefix-list match), generate a **dedicated test case** distinguishing between (a) a policy rule with no match statement at all (which matches everything) and (b) a policy rule that references an empty match resource (e.g., empty prefix-list). These are semantically different: "no match criteria" means the rule applies to all routes unconditionally, while "empty resource" may have feature-specific behavior (e.g., DNOS empty prefix-list returns "match"). Do not assume one test covers both cases.
- **Policy editor (VIM/IDE) workflow:** When the feature includes an editor for policy configuration (e.g., `edit routing-policy route-policy <name>`), generate a **dedicated test case** covering: (a) open existing policy in editor, modify, save (:wq!), apply; (b) create new policy via editor; (c) syntax validation on apply (reject invalid syntax); (d) copy-paste applied configuration. Do not assume CLI config tests cover the editor path — the editor exercises different serialization and validation flows.
- **Show inline / expanded policy:** When the feature supports a show command that expands named objects (lists, variables, nested policies) inline (e.g., `show route-policy inline [depth N]`), generate a **dedicated test case** covering: (a) list expansion (prefix-list, community-list, as-path-list); (b) nested policy expansion with depth parameter; (c) global variable expansion; (d) error handling for missing lists/variables. Each expansion type exercises different resolution logic.
- **Inline match with length constraints:** When the feature supports inline prefix match with mask-length constraints (e.g., `prefix-ipv4 in [10.0.0.0/8 matching-len ge 24 le 32]`), generate a **dedicated test case** covering: (a) ge/le/gt/lt/eq operators; (b) range notation; (c) boundary values; (d) that `==` operator remains exact-match only (no matching-len). Do not assume a generic prefix-match test covers length constraints.
- **Route-map vs route-policy disambiguation on upgrade:** When a new policy language (e.g., RPL) coexists with legacy route-maps and the attachment point interpretation changes (e.g., comma in parentheses, round brackets), generate **dedicated upgrade test cases** for: (a) upgrade from pre-change version with non-compliant route-map names; (b) _is_route_map / _is_route_policy disambiguation behavior; (c) mixed attachment (route-map list vs route-policy with params). Manual QA consistently tests these; collapsing causes low coverage.

### Reverted Restriction and Upgrade Script Testing

When the feature reverts a previously-added restriction or validation (e.g., a CLI validation that blocked a configuration combination in an earlier version), generate dedicated test cases for:

- **Inverse negative (restriction removal):** Verify the previously-blocked configuration is now accepted without error.
- **Upgrade from restricted version:** Verify that upgrading from the version with the restriction to the version without it correctly handles existing configurations (no data loss, no silent deletion of config by upgrade scripts).
- **Downgrade to restricted version:** Verify that downgrading back to the restricted version handles the now-allowed configuration gracefully (either blocks it or preserves what it can).
- **Cross-version config portability:** If the feature changes how configuration is stored or displayed (e.g., show config ordering), verify that config saved on the new version can be loaded on the old version and vice versa.

### Per-Transport-Type Decomposition for Multi-Transport Features

When the feature operates across multiple transport types (e.g., RSVP tunnels, MPLS LDP, SR-TE policies, IGP/connected routes, static routes), generate **dedicated test cases per transport type** for both basic functionality and scale:

- **Basic install/verify per transport:** If the feature installs routes or nexthops that can use different transport types, generate a separate basic test for each transport type verifying correct installation in RIB/FIB. Do not assume a single generic test covers all transport types — each has different label allocation, tunnel state management, and forwarding behavior.
- **ECMP per transport:** If the feature supports ECMP, generate a dedicated ECMP test per transport type (e.g., RSVP-only ECMP, MPLS LDP ECMP, IGP ECMP).
- **Scale per transport:** If the feature has scale tests, generate a dedicated scale test per transport type. Each transport type has different resource consumption and convergence characteristics at scale.
- **Mixed transport permutations:** When the feature supports mixing transport types in the same forwarding group (e.g., MPLS + IGP, SR-TE + Static), generate dedicated tests for each supported permutation — not a single "mixed" test. Each permutation exercises different path selection and NHOID construction logic.

### Protocol Disable/Enable Per-Protocol Testing

When the feature depends on multiple underlying protocols (e.g., IGP, MPLS LDP, RSVP, SR-TE, BGP), generate **dedicated test cases for disabling/re-enabling each protocol individually** while the feature is active:

- **Per-protocol disable/rollback:** For each protocol the feature depends on, generate a standalone test that disables that protocol, verifies the feature degrades gracefully, then re-enables it (or rolls back) and verifies recovery.
- **Simultaneous disable of all protocols:** Generate a test that disables all dependent protocols at once and verifies graceful degradation, then re-enables them.
- **Sequential disable one-at-a-time:** Generate a test that disables each protocol one at a time in sequence, verifying the feature's behavior at each step.

Do not collapse all protocol disable scenarios into a single generic "delete + rollback" test — each protocol's removal exercises a different code path for route withdrawal and nexthop resolution.

### ASBR/Peer Device Restart and BFD Interaction

When the feature involves route resolution through intermediate devices (e.g., ASBRs, route reflectors, PE routers), generate dedicated test cases for:

- **Primary peer device restart:** Verify the feature correctly handles restart of the primary path's intermediate device, with and without BFD enabled.
- **Alternate/backup peer device restart:** Verify the feature correctly handles restart of the alternate/backup path's intermediate device, with and without BFD enabled.
- **BGP neighborship flap:** Verify the feature correctly handles BGP session flaps (clear, reset) without device restart.
- **Alternate path failure and recalculation:** Verify that when the alternate/backup path itself fails, the feature correctly recalculates and installs a new alternate if one is available.

### Multi-Area/Multi-Level/Multi-Instance IGP Testing

When the feature relies on IGP for path resolution and the IGP supports multi-area (OSPF), multi-level (IS-IS), or multi-instance configurations, generate dedicated test cases for:

- **Multi-area OSPF:** Verify the feature works correctly when IGP paths traverse multiple OSPF areas.
- **Multi-level IS-IS:** Verify the feature works correctly when IGP paths traverse multiple IS-IS levels.
- **Mixed IGP protocols:** If both OSPF and IS-IS can provide paths for the feature, generate a test with both configured simultaneously.
- **Multi-instance IGP:** If the feature can use paths from different IGP instances, generate a test verifying correct behavior when the default instance changes or when a primary instance is deleted. Multiple instances may share resources, compete for label space, or interact through redistribution — do not assume that testing with a single instance covers multi-instance behavior.

### Automation Traceability

If the epic or its subtasks reference existing automated test files or test names, include an **Automation Reference** field in the relevant test cases mapping them to the corresponding test file and function name. Format: `test_file.py::test_function_name`.

### CLI Command Decomposition

When the feature introduces CLI commands (operational or configuration) with multiple sub-commands or variants, generate **separate CLI test cases** for each distinct command or sub-command, not a single consolidated CLI test. This applies to both operational (`run`) commands and configuration commands. Specifically:

- **Command availability + description:** One test per command/sub-command verifying the command is available, tab-completable, and help text is correct.
- **Valid-value-only acceptance:** One test per command/sub-command verifying that only valid parameter values are accepted and invalid values are rejected with appropriate errors.
- **Sub-command decomposition:** When a feature introduces a parent command with multiple sub-commands (e.g., `reflector <name>` with sub-commands `admin-state`, `description`, `local-discriminator`, `source-address`), generate a separate CLI test for each sub-command — do not consolidate into a single "reflector CLI" test.

For example, if a feature adds `protocols bfd seamless-bfd reflector <name>` with sub-commands for admin-state, description, local-discriminator, sbfd-local-state, and source-address, generate separate CLI tests for each sub-command. Manual QA consistently tests each command and sub-command independently.

### OAM/Diagnostic Feature Role Decomposition

When the feature involves diagnostic operations where the DUT can play different roles (e.g., head/originator, transit, tail/egress), generate **separate dedicated test cases per role per operation type**. Do not combine ping and traceroute into a single test — each operation type has different packet handling and response behavior. Specifically:

- For each FEC type × operation (ping/traceroute) × role (head/transit/tail), generate a dedicated test case.
- Do not use one role as a variant of another — each role exercises fundamentally different code paths.

### Interface State-Dependent Protocol Interaction

When a feature triggers interface state changes (e.g., laser-off/on, admin-down/up), generate **dedicated test cases** for each protocol that reacts to interface state changes. Common protocols to test:

- **VRRP:** If the feature can bring down an interface that carries a VRRP group, generate a dedicated test verifying VRRP failover behavior when the feature triggers interface down.
- **BFD:** If the feature can bring down an interface with BFD sessions, generate a dedicated test verifying BFD session behavior.
- **LACP:** If the feature can bring down bundle members, generate a dedicated test verifying LACP bundle behavior.
- **STP/RSTP:** If the feature can bring down bridge ports, generate a dedicated test verifying spanning tree reconvergence.

Do not assume that testing the feature's interface action in isolation covers protocol interaction — each protocol has different detection and convergence behavior when an interface state changes.

### Scale Trigger Enumeration

When testing a feature at scale, do not use a single generic trigger. Enumerate and test each distinct trigger type that can cause state transitions at scale:

- **Interface-based triggers:** Interface disable, link failure, bundle member removal.
- **Routing-based triggers:** Clear BGP, disable IGP interface, disable BGP neighbor, withdraw routes.
- **Service-based triggers:** Disable SRTE/RSVP, remove service configuration.
- **HA-based triggers at scale:** Process restart, container restart, NCC switchover — each combined with maximum scale.

Generate at least one dedicated scale test per trigger category, not a single "scale test" with trigger as a variant.

### VRF Lifecycle During HA

When the feature operates in VRF context, generate a **dedicated test case** (not a variant) for VRF removal and re-addition during HA events:

- Remove the VRF while an HA event (process restart, switchover) is in progress. Verify the feature handles the VRF removal gracefully without crashes.
- Re-add the VRF after the HA event completes. Verify the feature re-initializes correctly in the restored VRF.

This is a standalone test — VRF lifecycle changes during HA exercise different code paths than steady-state HA or steady-state VRF operations.

### Multi-Instance Service Sharing

When the feature operates on service instances (e.g., EVIs, VPN instances) that can share a common resource (e.g., Ethernet Segment Identifier, route-target, policy), generate a **dedicated test case** for the scenario where multiple service instances share the same resource:

- **Multiple service instances per shared resource:** If multiple EVIs can share the same ESI (multi-homing), or multiple VPN instances can share the same route-target, generate a test with multiple instances sharing the resource and verify each instance operates correctly and independently.
- **Per-instance policy differentiation:** If each instance can have a different policy (e.g., different colors per EVI on the same ESI), generate a test verifying that per-instance policies are applied correctly even when the underlying resource is shared.
- **Instance addition/removal with shared resource:** Generate a test that adds and removes service instances while the shared resource remains active, verifying no disruption to other instances.

Do not assume that testing a single service instance covers the multi-instance sharing case — shared resources introduce contention and ordering dependencies.

### MAC Mobility and Role/State Transition Testing

When the feature assigns per-MAC or per-AC attributes (e.g., role designations, flags, labels, service qualifiers) that affect forwarding behavior, generate **dedicated test cases** for MAC mobility events that change those attributes:

- **MAC move between different-role ACs:** If a MAC moves from an AC with one role/attribute to an AC with a different role/attribute (e.g., from a restricted AC to an unrestricted AC, or vice versa), generate a dedicated test verifying the attribute is correctly updated and forwarding behavior changes accordingly.
- **MAC move between local and remote PEs with different attributes:** Generate a test where a MAC moves from a local AC to a remote PE (or vice versa) and the attribute changes. Verify the forwarding decision is updated on all PEs.
- **Rapid MAC flapping between different-attribute ACs:** Generate a test with rapid MAC moves between ACs with different attributes. Verify the system converges to the correct attribute and no stale forwarding state remains.

Do not assume that a general MAC table verification test covers MAC mobility with attribute transitions — the attribute update path during MAC moves exercises different code than initial MAC learning.

### Generic vs. Specific Identifier Testing

When a feature supports multiple identifier types or FEC types for the same operation (e.g., specific BGP-LU FEC vs. generic IPv6 prefix FEC, specific SR prefix-SID vs. generic prefix FEC), generate **dedicated test cases for each identifier type** — not just the primary one. Each identifier type may exercise different validation logic, different TLV encoding, and different response handling. If a "generic" variant exists alongside a "specific" variant, test both explicitly.

### Route/State Changes During Active Operations

When the feature performs long-running or multi-step operations (e.g., MPLS traceroute with multiple hops, bulk OAM probes, path computation), generate a **dedicated test case** for route or forwarding state changes that occur **during** the active operation:

- Withdraw/change the target route while a ping/traceroute is in progress.
- Change the ECMP path set while a multipath discovery is in progress.
- Change label bindings while an OAM probe is in flight.

This is distinct from testing route changes before or after the operation — mid-operation changes exercise different error handling and state machine transitions.

### Address/Interface Removal Impact on Dependent Features

When a feature depends on interface addressing (e.g., IPv6 global address for OAM source selection, loopback address for router-id), generate a **dedicated test case** for removing or changing the address while the feature is active:

- Remove the global IPv6 address from the interface used by the feature. Verify the feature handles the address removal gracefully (no crash, appropriate error).
- Change the address to a different value. Verify the feature adapts to the new address.
- Re-add the original address. Verify the feature resumes normal operation.

Do not assume that testing feature deletion/rollback covers address removal — address changes affect the underlying transport without removing the feature configuration.

### BGP Feature Regression Breadth

When the feature changes how BGP processes, selects, or advertises routes (e.g., new SAFI, new attribute, new path selection rule), generate **dedicated regression test cases** for each existing BGP feature that interacts with route processing. Do not assume that a single "sanity" test covers all feature interactions. Specifically, generate at least one standalone TC for each of the following BGP features when they are relevant to the feature under test:

- **Per-neighbor features:** allow-as-in, as-override, as-loop-check, remove-private-as, send-community (standard/extended/both/large), maximum-prefix, ORF, soft-reconfiguration inbound
- **Path manipulation features:** route-policy (in/out), prefix-list, attribute-unchanged (AS-path/MED/NH), nexthop (self/unchanged/specific)
- **Path selection features:** bestpath, FRR, ECMP, add-path, rib-install policy, NH tracking policy
- **Route origination features:** network command, aggregate-route, default-originate, redistribution
- **Advanced features:** dampening, bgp-leak, RPKI/announce-rpki-state, BMP, entropy label, label-allocation, advertise-best-external, extended-next-hop capability

Each feature may behave differently with the new capability (e.g., a new SAFI changes how attributes are propagated). Do not collapse multiple feature regressions into a single "BGP regression" test — each feature exercises different code paths.

### BGP Installation Exclusion and FIB-ACK Interaction

When the feature excludes routes from RIB installation or FIB-ACK logic (e.g., rib-install filter, selective route download), generate **dedicated test cases** for: (a) filtered routes excluded from FIB-ACK and not pending for advertisement; (b) ILM handling when filtered unicast coexists with LU/VPN adj-out nexthop-self (ILM not filtered); (c) nexthop-self forced + installation-filter interaction — verify no routes stuck in Pending (regression for advertisement stuck scenarios). Do not assume sanity covers these — each exercises different code paths for ack bypass and advertisement flow.

### Route Propagation Matrix Testing

When the feature introduces a new route propagation ruleset (e.g., different behavior based on best-path SAFI × next-hop type × neighbor type), generate **dedicated test cases for each distinct cell** in the propagation matrix, not a single test that covers one cell with others as variants. Each combination of best-path source × NH handling × destination SAFI may exercise different code paths and produce different wire-format output.

### Optional Dependency Testing (With and Without)

When the feature has an optional dependency (e.g., S-BFD for liveness detection, TI-LFA for local repair, PCEP for path computation), generate **separate dedicated test cases** for the feature operating **with** and **without** the optional dependency enabled. Do not assume that testing with the dependency covers the without case — the feature's state machine, failover behavior, and convergence characteristics may differ significantly when the optional dependency is absent.

### IS-IS Level Decomposition

When the feature operates within IS-IS and can function at different levels (level-1, level-2, level-1-2), generate **dedicated test cases per IS-IS level type** — not a single test with level as a variant. Each level type has different flooding scope, route leaking behavior, and adjacency characteristics:

- **Level-1 only:** All nodes in a single L1 area.
- **Level-2 only:** All nodes in L2 backbone.
- **Level-1-2 (mixed):** Nodes with both L1 and L2 adjacencies.
- **Multi-level (inter-level):** Paths crossing L1/L2 boundaries.

### Label Type Interaction Testing

When the feature uses MPLS labels (prefix-SID, adjacency-SID, binding-SID, etc.), generate dedicated test cases for interaction with special label modes:

- **Explicit-null:** If the feature uses prefix-SIDs, test with explicit-null enabled on those SIDs. Explicit-null changes the label stack depth and penultimate-hop behavior.
- **Implicit-null (PHP):** Test behavior when the penultimate hop pops the label.
- **Binding-SID forwarding:** If the feature installs routes with a binding-SID, generate a dedicated test verifying traffic forwarded via the binding-SID (not just direct policy match).

### Reoptimization and Convergence Timer Testing

When the feature has a reoptimization or convergence timer that triggers periodic re-evaluation (e.g., SR-TE reoptimization timer, BGP best-path timer), generate **dedicated test cases** for:

- **Timer value changes:** Modify the timer value and verify the new interval takes effect.
- **Post-event reoptimization:** After a failover or state change, verify the reoptimization timer triggers re-evaluation and potentially restores the original state.
- **Timer interaction with lock/hold-down:** If the feature has both a reoptimization timer and a lock/hold-down timer, test the interaction between them.

### Time-of-Day (ToD) Testing

When the feature involves path computation, failover, convergence, timers, detection windows, or periodic operations, generate at least one **dedicated test case** for Time-of-Day (ToD) runs — executing the feature's critical operations at different times of day, and continuously overnight or over a weekend, to detect timing-dependent issues (e.g., timer wraparound, timer drift, log rotation interference, scheduled task conflicts, and gradual resource degradation).

### Cross-IGP Feature Interoperability

When the same feature is supported on multiple IGPs (e.g., SR-TE E2E protection on both IS-IS and OSPF), generate a **dedicated test case** verifying the feature operates correctly when both IGPs are running simultaneously on the same device, each with its own policies using the feature. Do not assume that testing on each IGP independently covers the coexistence case.

### Protection Mechanism Interaction as Dedicated TC

When the feature interacts with a protection mechanism (e.g., TI-LFA, FRR, RSVP bypass), generate a **dedicated test case** for the interaction — not just a variant or sub-step of another test. The protection mechanism changes the label stack, the forwarding path, and the convergence behavior. Specifically:

- Test that the feature correctly leverages the protection mechanism (e.g., TI-LFA alternate paths are installed for each segment in the segment-list).
- Test failover behavior when both the feature's own protection (e.g., E2E backup path) and the underlying protection mechanism (e.g., TI-LFA) are active simultaneously.

At maximum scale, generate **dedicated scale test cases** combining the feature with each protection mechanism — not just functional-level protection tests. Protection mechanisms at scale exercise different resource consumption, convergence timing, and label stack depth:

- **Feature at max scale + TI-LFA enabled:** Verify the feature operates correctly at maximum scale with TI-LFA protection active on all relevant paths.
- **Feature at max scale + Microloop avoidance enabled:** Verify the feature operates correctly at maximum scale with Microloop avoidance active.
- **Feature at max scale + TI-LFA + Microloop combined:** If both mechanisms can be active simultaneously, verify the combined behavior at scale.

These are standalone scale tests, not variants of a functional protection test.

### IGP Area/Level Topology Decomposition at Scale

When the feature operates within an IGP that supports multiple area types or levels (e.g., OSPF intra-area vs. inter-area, IS-IS level-1 vs. level-2), generate **dedicated scale test cases per area/level topology** — not a single generic scale test. Each area type has different route advertisement scope, path computation behavior, and label resolution:

- **Intra-area destination:** DUT and destination are in the same OSPF area or IS-IS level. Path computation uses intra-area routes only.
- **Inter-area destination:** DUT and destination are in different OSPF areas or IS-IS levels. Path computation crosses area/level boundaries (ABR/L1L2 nodes involved).
- **Mixed topology:** Some destinations are intra-area, others are inter-area. Verify the feature handles both correctly in the same configuration.

Do not assume that testing with one area topology covers another — inter-area paths involve different SPF computation, different label resolution, and potentially different forwarding behavior.

### Feature Knob State Matrix at Scale

When the feature has binary or multi-valued configuration knobs that change its operational behavior (e.g., external knob set/unset, strict/loose mode, explicit/dynamic computation), generate **dedicated scale test cases for each significant knob state** — not a single test with the knob as a variant. Each knob state may exercise different code paths for path computation, route installation, or label allocation at scale. Specifically:

- For each binary knob: test at full scale with knob enabled AND with knob disabled as separate TCs.
- For multi-valued knobs: test at full scale with at least two distinct values as separate TCs.
- If the feature has multiple independent knobs, test the most common combinations as dedicated TCs.

### Feature-Specific TLV/Attribute Encoding Boundaries

When a feature encodes a new TLV or attribute into a protocol message (e.g., ISIS LSP, BGP UPDATE, OSPF LSA), generate **dedicated test cases** for the encoding boundaries and exclusion rules:

- **Fragment/message scope:** If the TLV/attribute is only encoded in specific fragments or message types (e.g., fragment 0 only, non-purged messages only), generate a test verifying it is present where expected and absent where excluded.
- **Encoding under special conditions:** If the feature has conditions where the TLV/attribute should NOT be encoded (e.g., purged LSPs, withdrawn routes, expired timers), generate a dedicated test for each exclusion condition.
- **False positive detection:** If the feature detects anomalies based on TLV presence/absence (e.g., duplicate detection, capability mismatch), generate a dedicated test for known false-positive scenarios (e.g., database clear, configuration change, process restart) to document expected behavior.

### Service Type, Attachment, and Instance Decomposition

When the feature involves interfaces that can be attached to different service types or operates on multiple service instance types (e.g., VPWS, Bridge Domain, EVPN, EVPN-VPWS, EVPN-FXC, cross-connect, VRF), generate **dedicated test cases for each service type** — not a single service test with other services as variants. Each service type has different control-plane signaling, configuration hierarchy, forwarding behavior, and state management. Specifically:

- **One functional TC per service type:** Verify the feature works correctly when the interface is attached to each supported service type. Generate separate sanity, parameter modification, HA, scale, and system event TCs for each.
- **Service type switching:** If an interface can be moved from one service type to another (e.g., BD to VPWS), generate a dedicated TC for the transition while the interface is active.
- **Per-parameter modification per service type:** If the feature has configurable parameters, generate a dedicated "modify parameter X" TC for each service type, not just for the primary type.
- **HA per service type:** Generate separate process restart and system restart TCs for each service type. Do not assume a generic HA test with mixed services covers per-service-type HA behavior.
- **State transition tests per service type:** If the feature involves state transitions (e.g., moving between configuration modes, enabling/disabling), generate a dedicated transition test per service type.
- **Validation tests per service type:** If commit validations behave differently per service type, generate dedicated validation tests per type.

Do not assume that testing with one service type covers another — each service exercises different code paths for interface binding, configuration, traffic forwarding, state management, and event generation. This is distinct from per-protocol decomposition — it applies when the same feature is configured under different service hierarchies that share similar but not identical behavior.

### VLAN Operation Testing

When the feature operates on interfaces that support VLAN tagging, generate **dedicated test cases** for each distinct VLAN operation:

- **VLAN ID assignment:** Verify the feature works with different VLAN IDs (including boundary values).
- **VLAN tagging modes:** If the interface supports single-tag and double-tag (QinQ), generate separate tests for each mode.
- **VLAN manipulation:** If the interface supports VLAN push/pop/swap operations, generate a dedicated test for each manipulation type.

These are standalone tests — each VLAN operation changes the packet format and may affect forwarding behavior differently.

### Tracking Policy Interaction

When the feature modifies interface state or creates new interface types, generate **dedicated test cases** for interaction with tracking policies:

- **Interface as tracking target:** Verify that tracking policies correctly monitor the feature's interfaces and trigger actions when the interface state changes.
- **Tracking policy on feature interface:** Verify that tracking policies can be configured on the feature's interfaces and that they function correctly.

Do not assume that basic interface state testing covers tracking policy interaction — tracking policies have their own state machines and may react differently to state changes from different sources.

### ARP/NDP Behavior on Feature-Affected Interfaces

When the feature changes how interfaces are created, managed, or classified (e.g., L2 vs. L3 separation), generate a **dedicated test case** for ARP/NDP behavior on the feature's interfaces. Verify that ARP (IPv4) and NDP (IPv6) resolution works correctly on interfaces affected by the feature, especially when the interface type or management path changes.

### MTU and Packet Size Testing

When the feature introduces new interface types, changes interface management, or operates on interfaces where MTU affects protocol behavior (e.g., OSPF DBD exchange, IS-IS LSP fragmentation), generate **dedicated test cases** for MTU behavior:

- **MTU configuration:** Verify MTU can be configured on the feature's interfaces.
- **MTU with traffic:** Verify traffic at MTU boundary (max-size frames) works correctly on the feature's interfaces.
- **MTU change while active:** Verify MTU changes take effect on active interfaces without disruption.
- **MTU mismatch between peers:** Verify the feature handles MTU mismatch correctly (adjacency should not form unless MTU-ignore is configured).
- **Packet fragmentation:** If the feature generates protocol packets that can exceed MTU, verify correct fragmentation behavior.

Do not assume that generic interface MTU testing covers the feature's interfaces — different interface management paths may handle MTU differently.

### Complex Combined Commit Testing

When the feature introduces configuration that can be added and removed in bulk, generate a **dedicated test case** for complex combined commits where multiple instances of the same resource are added, removed, and re-added within a single commit. This exercises the configuration engine's ability to process conflicting operations atomically and is distinct from simple add/remove tests.

### Topology Type Decomposition

When the feature's behavior depends on the physical topology between the DUT and the target node (e.g., single link vs. parallel/ECMP links), generate **dedicated test cases per topology type** — not a single test with topology as a variant. Each topology type changes the path computation, protection availability, and failover behavior:

- **Single-link topology:** Only one link connects the DUT to the target node. Protection must use an alternate multi-hop path.
- **Parallel-link topology:** Multiple links connect the DUT to the same target node. Protection may use a parallel link or a multi-hop path.

When the feature also has multiple operational modes (e.g., different protection modes, different strictness levels), generate the topology decomposition **per mode** — each mode × topology combination may exercise different code paths. Do not assume that testing one topology covers the other.

### SR-TE Policy Nexthop Interaction

When the feature modifies how adjacency-SIDs, prefix-SIDs, or labels are protected or resolved, generate **dedicated test cases** for the feature's interaction with SR-TE policies that use the affected SIDs/labels as nexthops:

- **Adj-SID as SR-TE policy nexthop:** If the feature changes adj-SID protection, generate a test where the adj-SID is used as a nexthop in an SR-TE policy segment-list. Verify the policy's data-plane behavior when the adj-SID's protection path changes.
- **ECMP between P and Q nodes with SR-TE nexthop:** If the feature affects ECMP path selection for protection, generate a test where the SR-TE policy traverses nodes with ECMP between the P-node and Q-node of the protection path.

Do not assume that testing the feature in isolation covers its interaction with SR-TE policies — SR-TE policies impose additional constraints on label stacks and forwarding behavior.

### Flex-Algo Topology Interaction

When the feature operates within an IGP that supports Flexible Algorithm (Flex-Algo), generate **dedicated test cases** for the feature operating in a Flex-Algo topology:

- **Feature with Flex-Algo constraints:** Verify the feature works correctly when Flex-Algo constraints (affinity, SRLG, metric-type) are applied to the topology.
- **Feature with multiple Flex-Algos:** If the feature can operate on multiple Flex-Algo instances simultaneously, verify correct behavior per algorithm.

Flex-Algo changes the effective topology and path computation, which may affect the feature's behavior differently than the default algorithm. Do not assume default-algorithm testing covers Flex-Algo behavior.

### Interface Configuration Change Impact

When the feature depends on interface configuration (e.g., IP addresses, SRLG values, metric values), generate **dedicated test cases** for dynamic interface configuration changes while the feature is active:

- **IPv4 interface configuration changes:** Add/remove/modify IPv4 addresses on feature-affected interfaces. Verify the feature recalculates correctly.
- **IPv6 interface configuration changes:** Add/remove/modify IPv6 addresses on feature-affected interfaces. Verify the feature recalculates correctly.
- **IGP interface passive toggle:** If the feature operates on IGP interfaces (ISIS or OSPF), generate a test toggling the interface between active and passive mode while the feature is configured. Verify that feature-specific state (e.g., adjacency-SIDs, TI-LFA protection paths) is correctly withdrawn when the interface becomes passive and restored when it becomes active.
- **New neighbor discovery on configured interface:** If the feature allocates per-adjacency resources (e.g., adjacency-SIDs, per-neighbor state), generate a dedicated test for a new neighbor appearing on an interface where the feature is already configured. Verify the feature correctly allocates resources for the new adjacency without affecting existing ones.
- **Interface IP address change while feature is active:** If the feature is configured on an interface and depends on the interface's IP address (directly or indirectly via adjacency formation), generate a dedicated test for changing the interface IP address while the feature is active. Verify the feature correctly re-establishes state with the new address.

These are standalone tests — each configuration change triggers different recalculation paths and may expose race conditions or stale state.

### Protection Mode Switching

When the feature supports multiple protection or operational modes that can be switched dynamically (e.g., TI-LFA ↔ LFA, link protection ↔ node protection), generate a **dedicated test case** for switching between modes while the feature is active. Verify that the feature correctly transitions from one mode to another without stale protection paths, incorrect flags, or traffic loss.

### IGP Metric Change Impact on Dependent Features

When the feature modifies IGP metric values (globally or per-interface), generate **dedicated test cases** for each dependent feature that uses IGP metrics as input for its own computation or behavior. Do not assume that verifying the metric in LSPs is sufficient — downstream features may react differently to metric changes. Specifically:

- **Multicast RPF check:** If the feature changes IGP metrics that affect the Reverse Path Forwarding (RPF) lookup for multicast routing, generate a dedicated test verifying that multicast RPF correctly recalculates when the metric changes.
- **LDP-sync interaction:** If the feature changes IGP metrics on interfaces where LDP-sync is configured, generate a dedicated test verifying that LDP-sync behavior (metric inflation/restoration) interacts correctly with the feature's metric changes.
- **SR-TE path computation:** If the feature changes IGP metrics that affect SR-TE policy path computation (including Flex-Algo constrained paths), generate a dedicated test verifying that SR-TE policies reoptimize correctly when the metric changes.
- **Overload/max-metric interaction:** If the feature coexists with overload-bit or max-metric configuration, generate a dedicated test verifying the precedence and interaction between the feature's metric and overload/max-metric.

Each dependent feature has its own metric consumption path and recalculation trigger — do not assume that testing the metric advertisement alone covers all downstream effects.

### NCE Upgrade Testing

When the feature's configuration must persist across upgrades, generate a **dedicated test case for NCE (Network Compute Element) upgrade** in addition to DNOR and CLI upgrade tests. NCE upgrades exercise a different upgrade path (per-node rolling upgrade) that may handle configuration differently than full-system upgrades. Verify the feature's configuration and operational state are preserved before and after the NCE upgrade.

### Per-Knob Valid-Value Acceptance Testing

When the feature introduces multiple independent configuration knobs under the same hierarchy (e.g., `advertise`, `receive`, `preference` under a mapping-server), generate **separate valid-value acceptance test cases per knob** — not a single consolidated "valid values" test. Each knob may have different value ranges, default behaviors, and commit-time validations. Manual QA consistently tests each knob's valid-value acceptance independently. Specifically:

- For each knob: verify that all valid values within the documented range are accepted.
- For each knob: verify that values outside the range are rejected with appropriate error messages.
- For each knob: verify the default value is applied when no explicit value is configured.

### Protocol Database Show Command Verification

When the feature modifies protocol database entries (e.g., ISIS LSP database TLVs, OSPF LSA types, BGP UPDATE attributes), generate a **dedicated show command test case** for the protocol database view — not just the feature-specific show commands. The protocol database view (e.g., `show isis database detail`, `show ospf database`, `show bgp update-group`) reveals the raw TLV/attribute encoding and is critical for interop debugging. Do not assume that feature-specific show commands cover the protocol database view.

### Known-Limitation Interop Documentation

When the feature has known interoperability limitations with specific vendors (e.g., vendor does not support a required TLV or capability), generate a **dedicated test case** that documents the known limitation by verifying the expected failure behavior. This ensures the limitation is tracked, the DUT does not crash or misbehave, and the behavior is consistent across releases. Include the vendor name (using placeholder if needed) and the specific limitation in the test description.

### Tiebreaker and Equal-Value Election Testing

When the feature involves a selection or election mechanism with a primary criterion (e.g., preference value, metric, priority), generate a **dedicated test case** for the scenario where the primary criterion is **equal** across candidates and a secondary criterion (e.g., a flag bit, node ID, timestamp) determines the outcome. Do not assume that testing with distinct primary values covers the tiebreaker path — equal-value scenarios exercise different comparison logic and may reveal off-by-one or precedence bugs. Specifically:

- Test with all candidates having identical primary values and verify the secondary tiebreaker produces the correct and deterministic result.
- If the feature introduces a new flag or bit that participates in tiebreaking, test the flag in both states (set/unset) with equal primary values.

### Asymmetric Feature Configuration Testing

When the feature can be independently enabled or disabled on different nodes in a multi-node topology (e.g., multi-homing PEs, BGP peers, IGP neighbors), generate **dedicated test cases** for asymmetric configurations where some nodes have the feature enabled and others do not. Do not assume that testing with the feature enabled on all nodes covers the mixed case — asymmetric configurations may produce different protocol behavior, different advertisement content, and different election/selection outcomes. Specifically:

- **Feature enabled on one node, disabled on peer:** Verify the interaction between a node with the feature enabled and a peer without it.
- **Feature enabled on a subset of nodes:** In multi-node topologies (3+ nodes), verify behavior when only a subset has the feature enabled.
- **Dynamic asymmetry:** Enable the feature on one node while peers are already operational without it, and verify the transition is handled correctly.

### BGP-LS Redistribution of IGP-Learned Attributes

When the feature adds new TLVs or sub-TLVs to an IGP (IS-IS or OSPF) that carry information consumed by other protocols (e.g., S-BFD discriminators, Flex-Algo definitions, SID attributes), generate a **dedicated test case** verifying that the new TLV/attribute is correctly redistributed into BGP-LS. BGP-LS redistribution exercises a different code path than IGP-internal processing and may have different encoding rules. Do not assume that verifying the TLV in the IGP database covers BGP-LS redistribution.

### IGP Topology Mode Decomposition (Single-Topology vs Multi-Topology)

When the feature operates within IS-IS and the deployment supports both single-topology and multi-topology modes, generate **dedicated test cases per topology mode** — not a single test with topology mode as a variant. Single-topology and multi-topology have fundamentally different TLV encoding, flooding scope, and address-family handling:

- **Single-topology:** All address families share the same topology. TLVs are encoded in the common topology.
- **Multi-topology:** Each address family can have its own topology. TLVs may be encoded per-topology.

Do not assume that testing in one topology mode covers the other — the feature's TLV placement and processing may differ between modes.

### LSP/LSA Fragmentation with Feature TLVs

When the feature adds new TLVs or sub-TLVs to IGP protocol messages (IS-IS LSPs, OSPF LSAs), generate a **dedicated test case** for the scenario where the feature's TLVs span multiple LSP fragments or LSA fragments. At scale, a single LSP/LSA may not have enough space for all TLVs, forcing fragmentation. Verify:

- The feature's TLVs are correctly distributed across fragments.
- Receiving nodes correctly reassemble and process TLVs from multiple fragments.
- Adding/removing the feature's TLVs correctly triggers LSP/LSA regeneration and reflooding.

Do not assume that testing with a single fragment covers the multi-fragment case — fragmentation introduces ordering, size-limit, and reassembly logic.

### Discriminator/Identifier Constraint Testing

When the feature enforces uniqueness or cardinality constraints on identifiers (e.g., one discriminator per IP, one IP per SID, one label per prefix), generate **dedicated test cases** for each constraint:

- **Uniqueness violation:** Attempt to assign the same identifier to two different entities — verify rejection or correct override behavior.
- **Cardinality:** Verify the documented maximum number of identifiers per entity and the behavior when the limit is reached.
- **Inverse cardinality:** If one identifier can map to multiple entities (e.g., one discriminator to multiple IPs), generate a dedicated test verifying correct behavior.

Do not assume that basic functional tests cover constraint enforcement — constraints are often tested separately by manual QA.

### Real-World Scenario Testing

When the feature detects or prevents a network condition (e.g., loop detection, duplicate detection, anomaly detection), generate at least one **dedicated test case** that creates the actual network condition physically (e.g., physical loop, actual duplicate source) rather than only simulating it via traffic generators. Real-world conditions may trigger different timing, packet ordering, and detection behavior than simulated scenarios.

### Data-Plane Traffic Verification on State Changes

When the feature changes interface forwarding state (e.g., blocking, shutdown, unblocking), generate **dedicated test cases** verifying that data-plane traffic is actually blocked and unblocked correctly on each affected interface type (physical, sub-interface, bundle sub-interface). Do not assume that control-plane state changes (show commands) imply correct data-plane behavior — verify with actual traffic.

### IRB and Overlay Service Interaction

When the feature operates on L2 service instances that have IRB (Integrated Routing and Bridging) interfaces, generate a **dedicated test case** for the interaction between the feature and IRB-associated routes (MAC/IP routes). Verify that the feature's actions (e.g., AC shutdown) correctly affect IRB route advertisement and withdrawal.

### Dependent Nexthop and Forwarding State Cleanup

When the feature can cause a forwarding entry (e.g., SR-TE policy, tunnel, LSP) to transition from Up to Down, generate a **dedicated test case** verifying that all dependent forwarding state is correctly cleaned up:

- **IGP shortcut nexthop removal:** If the feature's forwarding entry is used as an IGP shortcut nexthop, verify that the shortcut nexthop is removed from the routing table when the entry goes Down.
- **Service overlay nexthop cleanup:** If the feature's forwarding entry is used by overlay services (EVPN, L3VPN, etc.), verify that the overlay service correctly reacts to the entry going Down.
- **Recursive nexthop invalidation:** If other routes resolve recursively through the feature's forwarding entry, verify they are correctly invalidated or re-resolved.

Do not assume that testing the feature's own state transition covers dependent forwarding state — each dependent consumer has its own state machine and cleanup logic.

### Manual Operational Command Interaction

When the feature changes the state machine or status of a protocol object (e.g., policy, session, adjacency), generate a **dedicated test case** for each manual operational command that can trigger re-evaluation or state refresh:

- **Manual reoptimization:** If the feature affects SR-TE policies, verify that manually triggering a reoptimization command does not produce incorrect status or validation errors for the feature's objects.
- **Clear/reset commands:** If the feature has associated clear or reset commands (e.g., `clear bgp`, `clear ospf process`), verify the feature's state is correctly restored after the command.
- **Debug/trace toggle:** If the feature has debug or trace commands, verify that enabling/disabling them does not affect the feature's operational state.

Do not assume that automated state transitions cover manual command interactions — manual commands may bypass normal state machine transitions.

### Underlying Resource Removal Testing

When the feature depends on an underlying resource (e.g., a SID, a label, a route, an interface address) for its operation, generate a **dedicated test case** for the scenario where the underlying resource is removed while the feature is active:

- **SID/label removal:** If the feature uses a prefix-SID or adjacency-SID, verify the feature's behavior when the SID is removed from the advertising node (e.g., by removing the SR configuration on the remote node).
- **Route withdrawal:** If the feature depends on a specific route being present, verify the feature's behavior when that route is withdrawn.
- **Interface address removal:** If the feature depends on an interface address (e.g., loopback used as policy destination), verify the feature's behavior when the address is removed.

This is distinct from testing the feature's own configuration removal — underlying resource removal exercises different detection and cleanup code paths.

### SR-TE Segment-List SID Type Decomposition

When the feature operates on SR-TE policies with segment-lists, generate **dedicated test cases per SID type** used in the segment-list — not a single test with SID type as a variant. Each SID type has different resolution logic, different label encoding, and different failure modes:

- **Prefix-SID only:** Segment-list composed entirely of prefix-SIDs.
- **Adjacency-SID only:** Segment-list composed entirely of adjacency-SIDs.
- **Absolute labels only:** Segment-list composed entirely of absolute (static) MPLS labels.
- **Mixed SID types:** Segment-list with a combination of prefix-SIDs, adjacency-SIDs, and/or absolute labels.

Do not assume that testing with one SID type covers another — each type exercises different SID resolution, validation, and forwarding code paths.

### Global vs. Per-Instance Configuration Inheritance

When a feature supports configuration at both a global level and a per-instance level (e.g., global EVPN transport settings overridable per EVI, global BGP settings overridable per neighbor-group), generate **dedicated test cases** for the configuration inheritance behavior:

- **Global-only:** Verify all instances inherit the global value when no per-instance override is configured.
- **Per-instance override:** Verify a per-instance value overrides the global value for that instance only, while other instances still inherit the global.
- **Mixed:** Verify correct behavior when some instances have per-instance overrides and others inherit global, simultaneously.
- **Global change with existing per-instance overrides:** Verify that changing the global value updates instances that inherit it, without affecting instances with per-instance overrides.
- **Per-instance removal:** Verify that removing a per-instance override causes the instance to fall back to the current global value.

Do not assume that testing at one level covers the other — global and per-instance configuration paths may have different commit-time validation, different operational state propagation, and different interaction with HA events.

### Default Value Change Across Versions

When a feature changes a configuration knob's **default value** between versions (e.g., a boolean default flips from disabled to enabled), generate **dedicated test cases** for the version-transition behavior — not just the new default in isolation:

- **Fresh install with new default:** Verify the new default is active on a clean installation of the new version.
- **Upgrade with no explicit config (using old default):** Verify that upgrading from the old version changes the effective behavior to the new default when no explicit configuration was set.
- **Upgrade with explicit old-default value:** Verify that upgrading retains the explicitly configured value even if it matches the old default (the user's intent was explicit).
- **Downgrade after default change:** Verify that downgrading reverts the default to the old value and handles any configuration that relied on the new default.
- **Interop between old and new default:** If the default affects wire-format or protocol negotiation (e.g., a control-word flag, an encapsulation mode), generate a dedicated interop test between a node running the old default and a node running the new default.
- **Release Notes / documentation verification:** Verify the default change is documented in release notes with the rationale and upgrade impact.

Do not assume that testing the new default value in isolation covers the version-transition cases — upgrade paths exercise different config migration, inheritance resolution, and protocol negotiation code paths.

### Resource Limit Clear/Reset Scenario Decomposition

When the feature enforces a resource limit (e.g., maximum routes, maximum entries, maximum sessions) and tracks failures when the limit is exceeded, generate **dedicated test cases** for each distinct "clear limit" or "resource recovery" scenario — not a single recovery test with other scenarios as variants. Each combination of resource type and recovery method may exercise different code paths. Specifically:

- **Per-resource-type recovery:** If the feature tracks failures for multiple resource types (e.g., routes vs. standby interfaces, primary vs. backup entries), generate a dedicated recovery test for each resource type.
- **Combined resource recovery:** Generate a dedicated test for the scenario where multiple resource types recover simultaneously (e.g., both a route and a standby interface become installable at the same time).
- **Limit configuration change vs. resource freeing:** Generate separate tests for (a) recovering by freeing resources (removing existing entries) and (b) recovering by increasing the limit configuration. These exercise different code paths.

Do not assume that testing recovery for one resource type covers another — each type may have different auto-recovery vs. manual-recovery behavior.

### Multicast Group Range and Filter Decomposition

When the feature operates on multicast groups that can be filtered or categorized by group ranges (e.g., SSM ranges, protected groups, ASM groups), generate **dedicated test cases per group range type** — not a single test with other range types as variants. Each range type may have different PIM behavior, different RPF handling, and different interaction with the feature.

### Deprecated/Removed CLI Command Verification

When the feature removes or deprecates a CLI command (e.g., removing a vtysh command, deprecating a configuration knob), generate a **dedicated test case** verifying:

- The removed command is no longer available (not tab-completable, returns appropriate error).
- Existing configurations that used the removed command are handled gracefully during upgrade.
- The removal does not affect related commands that remain supported.

### IGP Feature Attachment Point Matrix Decomposition

When a feature can be attached at multiple IGP configuration dimensions simultaneously (e.g., per-level, per-address-family, per-interface-type), and the feature's behavior depends on the combination of these dimensions, generate **dedicated test cases for the most common combinations** — not a single test with all other combinations as variants. Specifically:

- **Per-level × per-topology:** If the feature operates at specific ISIS levels (L1, L2, L1-2) and supports both single-topology and multi-topology, generate at least one dedicated TC per level type × topology mode combination. Each combination has different flooding scope, TLV encoding, and metric derivation behavior.
- **Per-interface-type:** If the feature applies to different interface types (loopback, physical, sub-interface, bundle), generate at least one dedicated TC per interface type — not a single test with interface type as a variant. Each interface type has different prefix advertisement behavior and different operational semantics.
- **Negative level mismatch:** If the feature is configured at a specific level but the interface operates at a different level, generate a dedicated negative test verifying the feature is correctly ignored or rejected.

Do not assume that testing one combination covers another — each combination exercises different code paths for TLV generation, policy evaluation, and state management.

### IGP Default-Originate Interaction

When the feature modifies IGP route advertisement behavior (e.g., conditional advertisement, route suppression, metric manipulation), generate **dedicated test cases** for the interaction with default-originate:

- **Feature + default-originate on same interface:** Verify the feature's behavior when default-originate is also configured on the same interface or instance.
- **Feature affecting default-originate condition:** If the feature's condition (e.g., rib-has-route) can also affect default-originate behavior, verify the interaction.
- **Multi-instance with default-originate:** If the feature operates in multi-instance mode, verify the interaction with default-originate per instance.

Do not assume that testing the feature in isolation covers default-originate interaction — default-originate has its own policy evaluation and advertisement logic that may interact with the feature.

### Multiple Attachment Points for Same Feature

When a feature can be attached to the same entity at multiple configuration points (e.g., multiple policy attachment levels on the same interface, multiple conditional configurations per address-family), generate **dedicated test cases** for:

- **Multiple attachment points on same entity:** Verify the feature works correctly when attached at multiple points on the same interface (e.g., conditional-adv at level-1 AND level-2 on the same interface).
- **Same policy on multiple entities:** Verify the feature works correctly when the same policy is applied to multiple interfaces simultaneously.
- **Multiple policies on same entity:** Verify the feature works correctly when different policies are applied to different attachment points on the same interface.

Each combination exercises different policy evaluation ordering and state management. Do not assume that testing a single attachment point covers the multi-attachment case.

### Policy Logic Decomposition (AND/OR/Multiple Rules)

When the feature uses routing policies with match conditions, generate **dedicated test cases** for each distinct policy logic pattern:

- **Single match condition:** Basic case with one match rule.
- **Multiple AND conditions:** Multiple conditions that must all be true (e.g., multiple rib-has-route prefixes that must all be present).
- **Multiple OR conditions:** Multiple conditions where any one being true is sufficient.
- **Mixed rules with feature condition:** Multiple rules in the policy where the feature's condition (e.g., rib-has-route) is not the only rule — verify interaction with other rules.
- **Policy modification in same commit as match state change:** Modify the policy (add/remove match conditions) in the same commit as the tracked state changes.

Do not assume that testing a single match condition covers the multi-condition case — AND/OR logic and multi-rule evaluation exercise different code paths.

### Show Command Topology Mode Decomposition

When the feature modifies show command output and the feature behaves differently in different topology modes (e.g., single-topology vs. multi-topology), generate **dedicated show command test cases per topology mode** — not a single show test. Each topology mode may display different fields, different metric derivation, and different TLV content in database views.

### Show Command Source/Destination Node Decomposition

When the feature involves route synchronization or advertisement between nodes (e.g., distributed clusters, route reflectors, multi-node BGP topologies), generate **dedicated show command test cases per node role** — not a single consolidated show command test. Each node role (source/originator vs. destination/receiver) may display different information:

- **Source node show commands:** Verify show commands on the node that originates/advertises the routes. Check that locally originated routes appear with correct attributes, metadata, and encoding.
- **Destination node show commands:** Verify show commands on the node that receives/installs the routes. Check that received routes appear with correct decoded attributes, NH type, and resolution.
- **Per-command decomposition:** If manual QA tests each show command variant separately (e.g., `show route`, `show bgp`, `show route <prefix>`), generate separate TCs per command per node role.

Do not assume that testing show commands on one node covers the other — source and destination nodes display different route attributes and state.

### Fabric/Internal Interface HA Decomposition

When the feature operates in a disaggregated or distributed architecture with both external-facing interfaces (NIFs) and internal fabric interfaces (FIFs, ICE), generate **dedicated HA test cases for each interface type** — not just external interfaces. Fabric interface failures exercise different recovery paths:

- **NIF (Network Interface Function) HA:** Test route behavior when external-facing interfaces fail.
- **FIF (Fabric Interface Function) HA:** Test route behavior when internal fabric interfaces fail. Fabric failures affect inter-node connectivity and may cause different convergence behavior than external interface failures.

Do not assume that testing NIF HA covers FIF HA — each interface type has different failure detection, convergence characteristics, and impact scope.

### Deadlock Prevention Testing

When a feature can trigger a state change on both ends of a connection (e.g., both PEs in a service can shut down their local ports based on remote state), generate a **dedicated test case** verifying the deadlock prevention mechanism:

- **Mutual shutdown prevention:** Configure the feature on both ends and trigger a failure on one end. Verify that the non-failing end takes the protective action (e.g., laser-off) while continuing to advertise its own state, so the failing end does not also trigger the protective action.
- **Asymmetric configuration:** Test with the feature enabled on one end and disabled on the other. Verify correct behavior in both directions.

Do not assume that testing the feature on a single node covers the mutual-shutdown scenario — the interaction between two feature-enabled nodes exercises different state machine transitions.

### Admin-State Override of Feature-Triggered Actions

When a feature triggers an operational state change on an interface or service (e.g., laser-off, port-shutdown, route withdrawal), generate **dedicated test cases** for the interaction between admin-state changes and the feature-triggered action:

- **Admin-down while feature action is active:** Verify that admin-down overrides the feature-triggered action (e.g., laser-off is released when admin-down is configured, because admin-down implies the operator intentionally took the interface down).
- **Admin-up after admin-down with pending feature action:** Verify that when admin-up is restored, the feature re-evaluates the condition and re-triggers the action if the condition is still met.
- **Service admin-down vs. interface admin-down:** If the feature operates at a service level that has both service-level and interface-level admin-state, generate separate tests for each admin-state level.

These are standalone tests — admin-state interactions with feature-triggered actions exercise different code paths than normal feature operation.

### Route-Type Combination Decomposition for Limit/Threshold Features

When the feature enforces a limit or threshold that applies across multiple route types (e.g., connected, static, BGP, IGP), and the feature treats some route types differently from others (e.g., always installing connected/static but blocking dynamic routes), generate **dedicated test cases for each distinct route-type combination** — not a single test that covers only the most complex combination. Specifically:

- **Route type A only:** Test with only the always-installed route type (e.g., connected-only) to verify the feature correctly counts these routes and handles the case where the limit is reached entirely by always-installed routes.
- **Route type A + B only:** Test with two route types (e.g., connected + static) to verify counting and enforcement when no dynamic routes are present.
- **Route type A + C only:** Test with the always-installed type plus the enforceable type (e.g., connected + BGP) to verify enforcement applies only to the dynamic type.
- **All route types combined:** Test with all route types together to verify the combined counting and enforcement behavior.

Each combination exercises different enforcement logic — the case where the limit is reached entirely by always-installed routes is fundamentally different from the case where dynamic routes push the count over the limit. Do not assume that testing the most complex combination covers simpler ones.

### Per-Algorithm × Per-Level × Per-Packet-Type Decomposition

When a feature supports multiple cryptographic algorithms (e.g., MD5, HMAC-SHA-1, HMAC-SHA-256) and operates at multiple protocol levels or scopes (e.g., IS-IS level-1, level-2, level-1-2), generate **dedicated test cases per algorithm per level** — not a single test with algorithm or level as a variant. Each algorithm has different TLV encoding, key derivation, and interop behavior. Similarly, when authentication applies to different packet types within the same protocol (e.g., Hello packets vs. LSP/SNP packets), generate **separate test cases per packet type** — each packet type exercises different authentication code paths and may have different failure modes.

Do not assume that testing one algorithm covers another, or that testing Hello authentication covers LSP/SNP authentication.

### Time-Based Feature Edge Cases

When a feature involves time-based state transitions (e.g., key lifetimes, timer-based activation/deactivation, scheduled operations), generate **dedicated test cases** for each time-related edge case:

- **NTP synchronization during transition:** Verify behavior when an NTP sync event occurs during a time-based state transition (e.g., key rollover). NTP sync can shift the system clock forward or backward, potentially invalidating or prematurely activating time-based state.
- **Manual time/date change during active operation:** Verify behavior when the operator manually changes the system time/date while time-based features are active.
- **Mixed time references within the same entity:** If the feature allows different time references (e.g., UTC vs. local timezone) for different sub-elements within the same configuration entity, generate a dedicated test with mixed time references and verify correct independent evaluation.

These are standalone tests — each time-related edge case exercises different clock-handling and state-reevaluation code paths.

### Fallback/Default Mechanism Edge Case Decomposition

When a feature has a fallback or default mechanism (e.g., default-send-key, fallback route, backup policy), generate **dedicated test cases for each distinct edge case** of the fallback mechanism — not a single fallback test. Specifically:

- **Fallback with expired primary and active fallback:** Verify the fallback activates when the primary expires.
- **Fallback with expired primary and expired fallback:** Verify behavior when both primary and fallback are expired/unavailable.
- **Fallback with expired primary and pending fallback:** Verify behavior when the primary expires but the fallback has not yet become active (gap scenario).
- **Transition from fallback back to primary:** Verify the system correctly transitions from fallback back to a newly available primary without disruption.

Each edge case exercises different state machine transitions. Do not assume that testing the basic fallback activation covers all edge cases.

### SNMP Trap, Syslog, and System Event Decomposition

When a feature generates SNMP traps, syslog messages, or system events for different operational scenarios, generate **dedicated test cases per scenario, per variant, and per trigger condition** — not a single "verify traps are generated" test. Each scenario may generate different trap types, different severity levels, different trap OIDs, different syslog message formats, and different information elements. Specifically:

- **Per-scenario triggers:** Generate one test per distinct event trigger (e.g., per-algorithm authentication failure, key lifecycle start/end, unauthenticated neighbor detection). Verify both the trap/event content and the trap/event timing.
- **Per-algorithm/mode variants:** If the feature supports multiple algorithms or modes, generate a dedicated SNMP/syslog test for each algorithm/mode.
- **Per-failure-type:** If the feature distinguishes between different failure types (e.g., type mismatch vs. authentication failure vs. key-id mismatch), generate a dedicated test for each failure type.
- **Per-error-type decomposition:** If the trap/event has an enumerated error type field (e.g., ospfConfigErrorType with values like areaMismatch, duplicateRouterId, helloMismatch, MTUMismatch), generate a dedicated TC for each error type value.
- **Per-authentication-type combination:** If the trap/event is triggered by authentication mismatches, generate dedicated TCs for each relevant combination of authentication types between DUT and peer (e.g., none vs. simple, none vs. MD5, simple vs. MD5, MD5 key mismatch, keychain mismatch).
- **Cross-auth-type:** If the feature can detect mismatches between different authentication types (e.g., keychain vs. static, authenticated vs. unauthenticated), generate dedicated tests for each cross-type scenario.
- **Per-packet-type verification:** If the trap/event can be triggered by different protocol packet types (Hello, DBD, LSU, LSAck, LSR), generate dedicated TCs verifying the trap correctly identifies the packet type in each case.
- **Syslog event CLI configuration:** When a feature introduces new syslog events, generate dedicated TCs for the CLI commands that configure/enable/disable each syslog event (e.g., `system logging syslog event <EVENT_NAME>`), verifying the event can be individually controlled.
- **Feature interaction:** Include scenarios where the feature interacts with other features that also generate traps (e.g., authentication failure + adjacency down).

### Transient State During HA Transitions

When the feature triggers interface or service state changes (e.g., shutdown, blocking, oper-down), generate a **dedicated test case** for transient state during HA transitions (switchover, failover, process restart). During HA transitions, there may be a brief window where the interface or service temporarily returns to its pre-feature state before the feature re-asserts control. Verify:

- **No transient oper-up during switchover:** If the feature keeps an interface in oper-down, verify the interface does not briefly become oper-up during NCC switchover or process restart before the feature re-asserts the shutdown.
- **No traffic "slip" during transition:** If the feature blocks traffic, verify no traffic leaks through during the HA transition window.

These are standalone tests — transient state issues are race conditions that are distinct from steady-state HA preservation tests.

### Show Command Display Accuracy and Formatting

When the feature adds new fields or columns to existing show commands, generate **dedicated test cases** for show command display accuracy:

- **Counter display after config changes:** If the feature displays counters (cycle count, timer values), verify the counter display remains correct and in the proper column/row after configuration changes (e.g., adding/removing services, changing parameters).
- **False-positive display:** If the feature displays status indicators (e.g., "shutdown", "suppressed"), verify these indicators do NOT appear when the feature has not been triggered (no false positives in show output).
- **Timer display accuracy:** If the feature displays countdown timers, verify the timer shows the remaining time (not the current system time or other incorrect value).

Do not assume that basic show command testing covers display accuracy — formatting and counter display issues are common regression areas.

### Operational Commands at Scale

When the feature introduces operational commands (clear, reset, show), generate **dedicated test cases** for these commands at maximum scale — not just at functional scale. Operational commands at scale exercise different code paths (bulk iteration, memory allocation for large output, timeout handling):

- **Clear commands at scale:** If the feature has clear/reset commands, execute them when the maximum number of entities are in the affected state. Verify all entities are correctly cleared and no partial state remains.
- **Show commands at scale:** Verify show commands complete within acceptable time at maximum scale and produce correct output.

### Crash Recovery and State Consistency

When the feature manages state across multiple processes or components (e.g., routing process manages detection, infra process manages interface state), generate **dedicated test cases** for crash recovery scenarios:

- **Process crash during active feature state:** If a process crashes while the feature's action is active (e.g., interface is shut down), verify the remaining processes handle the crash gracefully and the feature state is consistent after the crashed process restarts.
- **Process crash during state transition:** If a process crashes during a state transition (e.g., during timer expiry and interface restoration), verify the system recovers to a consistent state — either the action is re-applied or the restoration completes.

These are standalone tests — crash recovery exercises different code paths than graceful restart.

### Inter-Component Communication Path Testing

When the feature requires communication between different system components (e.g., routing process sends interface-down instruction to infra, control plane sends state to data plane), generate **dedicated test cases** for each communication path:

- **Forward path (trigger → action):** Verify the instruction from the triggering component reaches the executing component and the action is performed correctly.
- **Reverse path (release → restore):** Verify the release instruction from the triggering component reaches the executing component and the restoration is performed correctly.
- **Communication failure:** Verify behavior when the communication path is disrupted (e.g., component restart during instruction delivery).

Do not assume that testing the feature's end-to-end behavior covers the inter-component communication path — each path may have different serialization, queueing, and error handling.

---

### Gateway/Transit Mode Without Local Endpoints

When the feature can operate in a pure gateway or transit mode (i.e., without local endpoints/ACs attached), generate a **dedicated test case** for the feature operating without any local endpoints. This mode exercises different code paths for route advertisement, flooding, and state management:

- **No local ACs/endpoints:** Verify the feature works correctly as a pure gateway/transit node with no locally attached endpoints. Verify route stitching/re-advertisement still functions.
- **Adding first local endpoint:** Verify the feature correctly transitions from gateway-only mode to gateway + local endpoint mode when the first endpoint is attached.

Do not assume that testing with local endpoints covers the no-endpoint case — the absence of local endpoints may change flooding behavior, route generation (e.g., no Type-3 routes without ACs), and state machine transitions.

### Remote Service Attribute Interaction

When the feature operates on a service instance that can interact with remote service attributes (e.g., remote e-tree-leaf designation, remote split-horizon labels, remote service flags), generate **dedicated test cases** for each remote service attribute that the feature must process:

- **Remote attribute from same domain:** Verify the feature correctly processes remote service attributes received from peers in the same domain.
- **Remote attribute from cross-domain (stitched):** If the feature stitches between domains, verify remote service attributes are correctly handled when they cross the domain boundary (e.g., e-tree-leaf designation from MPLS domain affecting VXLAN domain behavior).

Do not assume that testing local service attributes covers remote attribute handling — remote attributes arrive via different signaling paths and may have different encoding or semantics.

### MAC Learning Mode Interaction

When the feature operates on L2 services that support different MAC learning modes (e.g., dynamic learning, sticky MAC, static MAC), generate **dedicated test cases for each MAC learning mode** — not a single test with learning mode as a variant. Each mode has different persistence, mobility, and aging behavior:

- **Dynamic MAC:** Standard data-plane learning with aging.
- **Sticky MAC:** MACs persist across restarts and are not subject to mobility.
- **Static MAC:** Manually configured MACs that override dynamic learning.

If the feature involves MAC re-advertisement or stitching between domains, verify each learning mode's behavior when MACs cross domain boundaries.

### Dynamic BGP Parameter Changes on Active Service

When the feature creates BGP instances or sessions as part of a service (e.g., per-service BGP configuration for EVPN, VPN), generate **dedicated test cases** for dynamically changing BGP parameters while the service is active and carrying traffic:

- **RD change:** Change the route-distinguisher while the service is active. Verify routes are re-advertised with the new RD.
- **RT change:** Change import/export route-targets while the service is active. Verify route import/export behavior updates correctly.
- **BGP AS change:** If applicable, change the BGP AS number. Verify sessions re-establish.
- **Policy change:** Add, modify, or remove export/import policies. Verify route filtering updates.

These are standalone tests — each parameter change exercises different BGP update and session management code paths. Do not assume that initial configuration testing covers dynamic parameter changes.

### Distributed Cluster Node-Role HA Decomposition

When the feature operates in a distributed cluster architecture with multiple node types (e.g., NCP, NCF, NCC), generate **dedicated HA test cases per node type and per restart method**:

- **Per node type:** Each node type (compute, fabric, control) has different roles in the feature's operation. A restart of a compute node may affect sessions differently than a restart of a fabric node.
- **Per restart method per node type:** Cold restart and warm restart exercise different recovery paths. Generate separate tests for cold vs. warm restart for each relevant node type.
- **Per process per node type:** If the feature runs processes on multiple node types, generate per-process restart tests for each node type where the process runs (e.g., BGP process restart on NCP-0 vs. NCP-1 are separate tests when the NCPs have different roles).

Do not collapse different node types into variants of a single HA test — each node type has different failure domains and recovery characteristics.

### Per-Parameter Dynamic Configuration Change Testing

When the feature introduces multiple configurable parameters (e.g., VNI, route-targets, source-interface, policies, encapsulation type), generate **dedicated test cases for changing each parameter individually while the feature is active with traffic flowing**. Do not assume that initial configuration testing covers dynamic parameter changes — changing a parameter on an active service exercises different state management paths (route withdrawal, re-advertisement, tunnel teardown/rebuild, nexthop update).

For each configurable parameter:
- Change the parameter while traffic is flowing; verify routes are updated and traffic recovers.
- Verify the old value is fully cleaned up (no stale routes, tunnels, or forwarding entries).
- Verify the new value is fully operational.

These are standalone tests, not variants — each parameter change may trigger different internal state transitions.

### Feature Interaction with Adjacent Protocols and Mechanisms

When the feature operates alongside or depends on adjacent protocol mechanisms (e.g., BGP leak, Route Target Constraint, FRR/LFA, route aggregation), generate **dedicated test cases for each interaction**:

- **Route leaking interaction:** If the feature's routes can be leaked between VRFs via BGP leak, generate a dedicated test verifying the leaked routes maintain correct attributes and forwarding behavior.
- **Route Target Constraint (RTC):** If the feature uses route-targets, generate a dedicated test verifying RTC correctly filters route advertisements to only interested peers.
- **FRR/LFA interaction:** If the feature's traffic can use FRR/LFA backup paths (e.g., when the primary underlay path fails), generate a dedicated test verifying traffic correctly switches to the backup path and returns when the primary recovers.
- **RT5 withdraw behavior:** Generate a dedicated test for explicit route withdrawal scenarios (not just interface-down triggered withdrawals) — verify the withdraw is propagated correctly and forwarding entries are cleaned up.

Do not assume that testing the feature in isolation covers these interactions — each adjacent mechanism can affect route selection, advertisement, and forwarding differently.

### Traffic To/From DUT Itself (Control-Plane Traffic in VRF Context)

When the feature creates overlay tunnels or VRF-based forwarding, generate a dedicated test for **traffic destined to or originated from the DUT itself** within the VRF context (e.g., ping from VRF, BGP peering over the overlay tunnel, management traffic within VRF). This is distinct from transit traffic — locally-terminated traffic exercises different forwarding paths (punt to CPU, local delivery, source address selection).

### Route Segment Decomposition

When the feature involves route stitching or re-advertisement between different protocol domains (e.g., EVPN to VPN, VPN to unicast), generate **dedicated test cases per route segment**:

- **Local segment:** Routes originated locally (connected, static, redistributed) — verify they are correctly advertised into the stitching domain.
- **VPN segment:** Routes received from the VPN/MPLS domain — verify they are correctly installed and re-advertised.
- **Overlay segment:** Routes received from the overlay domain (e.g., EVPN Type-5) — verify they are correctly installed and re-advertised.

Each segment exercises different route import/export paths and may have different nexthop resolution behavior.

### New Routing Policy Match Condition Testing

When the feature introduces new routing policy match conditions (e.g., match on route-type, match on encapsulation community), generate a **dedicated test case** for the new match condition:

- Verify the match condition correctly identifies matching routes.
- Verify the match condition correctly excludes non-matching routes.
- Verify the match condition works in both import and export policy directions.
- Verify interaction with other match conditions in the same policy rule.

### Dynamic Interface Membership Changes on Active Service

When the feature supports attaching/detaching interfaces (ACs, endpoints) to a service instance, generate **dedicated test cases** for dynamic interface membership changes while the service is active:

- **Add interface to active service:** Verify the new interface is correctly integrated (MAC learning starts, routes are updated, traffic flows).
- **Remove interface from active service:** Verify the interface is cleanly detached (MACs withdrawn, routes updated, no traffic blackholing).
- **Move interface between services:** If an interface can be moved from one service instance to another, verify the transition is clean (old service withdraws, new service advertises).

Do not assume that testing with a static set of interfaces covers dynamic membership changes — adding/removing interfaces while the service is active exercises different state management and notification paths.

### Distributed/Multi-Node Route Sharing Features

When the feature involves sharing or synchronizing routes between multiple nodes in a distributed system (e.g., multi-NCP clusters, distributed chassis), generate **dedicated test cases** for each distinct route sharing scenario:

- **Originating node vs. receiving node perspective:** Generate separate tests verifying behavior on the node that originates/configures the route AND on the remote node that learns it. Do not assume that testing on one node covers the other — the originating node has local state, while the receiving node has recursive/indirect state.
- **Multi-node ECMP:** When the same route is originated by multiple nodes, generate a dedicated test verifying ECMP installation on receiving nodes, including dynamic addition/removal of originating nodes.
- **Route attribute preservation across nodes:** When a route is shared between nodes, generate a dedicated test verifying which attributes are preserved (e.g., metric → MED) and which are NOT propagated (e.g., tag). Each attribute may have different propagation rules.
- **Recursive nexthop depth:** When shared routes are installed as recursive routes on receiving nodes, generate a dedicated test for multi-level recursion (route resolved via another shared route) to verify system stability and correct forwarding.

### All Attachment Points for the Same Feature

When a feature applies to multiple attachment points within the same protocol or service (e.g., export-vpn, import-vpn, bgp-leak import-from, redistribute), generate **dedicated test cases for each attachment point** — not a single test with other attachment points as variants. Each attachment point may have different evaluation order, different attribute handling, and different interaction with the feature's configuration. Specifically:

- **One functional TC per attachment point:** If the feature supports policy chains on export-vpn, import-vpn, and bgp-leak import-from, generate separate TCs for each.
- **Per-attachment-point scale:** If the feature has a maximum chain length, generate a dedicated scale TC per attachment point verifying the maximum is enforced independently.

Do not assume that testing one attachment point covers another — each attachment point exercises different code paths for policy evaluation, attribute modification, and route processing.

### Incremental Chain/List Modification Testing

When a feature supports ordered lists or chains (e.g., policy chains, segment-lists, ACL rules), generate **dedicated test cases** for incremental modification of the chain while the feature is active:

- **Add one element at the end:** Add a single element to the end of an existing chain and verify the chain is correctly extended.
- **Add one element in the middle:** Insert a single element in the middle of an existing chain and verify the chain is correctly reordered.
- **Remove one element from the chain:** Remove a single element and verify the remaining chain operates correctly.
- **Same-commit vs. different-commit modifications:** Generate separate tests for adding/removing elements in a single commit vs. across multiple commits — each exercises different commit-time processing and may produce different intermediate states.

Do not assume that testing the full chain creation covers incremental modification — adding/removing individual elements exercises different delta-processing code paths.

### Import vs. Export Direction Decomposition

When a feature operates on both import and export directions of a protocol or service (e.g., import-vpn policy and export-vpn policy), generate **separate dedicated test cases per direction** — not a single test covering both directions. Each direction has different evaluation order, different attribute handling, and different performance characteristics:

- **Export direction:** Generate dedicated TCs for export-specific behavior (e.g., policy runs before RT addition).
- **Import direction:** Generate dedicated TCs for import-specific behavior (e.g., RT match before policy evaluation).
- **Per-direction scale:** Generate separate scale TCs per direction (e.g., max 20 export policies AND max 20 import policies as separate TCs).

Do not assume that testing one direction covers the other — import and export paths exercise fundamentally different code paths.

### NETCONF/gNMI Oper-Items as Separate from Config

When the feature exposes both configuration and operational data via NETCONF/gNMI, generate **separate dedicated test cases** for configuration verification and operational-items verification — not a single consolidated NETCONF test. Configuration and operational data use different YANG containers, different retrieval mechanisms, and may have different update timing:

- **Config verification:** Verify edit-config and get-config for the feature's configuration.
- **Oper-items verification:** Verify get (operational) returns correct runtime state, counters, and status for the feature.

---

### Topology Bring-Up and Setup Procedure Testing

When the feature requires a specific topology or environment setup (e.g., cluster installation, fabric bring-up, inter-node connectivity configuration), generate **dedicated test cases** for the setup procedure itself — not just a "Setup Integrity" validation. Manual QA consistently tests the setup steps as independent test cases because setup failures are a common source of issues. Specifically:

- **Installation/provisioning:** If the feature requires a specific system type or cluster mode (e.g., AI cluster, CL cluster), generate a dedicated TC for the installation and initial provisioning of that environment.
- **Inter-node connectivity setup:** If the feature depends on inter-node links or control-plane sessions (e.g., ICE interfaces, iBGP mesh), generate a dedicated TC for configuring and validating those prerequisites.
- **Base protocol configuration:** If the feature builds on top of another protocol's configuration (e.g., eBGP on top of iBGP mesh), generate a dedicated TC for the base protocol configuration and validation.

Do not assume that setup is merely a precondition — setup steps exercise different code paths (config-sync, element discovery, session establishment) and are independently testable.

---

### TTL and Packet Header Boundary Testing for For-Us / Punt-to-CPU Features

When the feature involves forwarding packets to a remote node's CPU (for-us / punt-to-CPU traffic), generate dedicated test cases for packet header boundary conditions:

- **TTL boundary values:** Test with TTL values at the boundary of forwarding decisions (e.g., TTL=1 where the packet should be consumed at ingress, TTL=2 where the packet may expire before reaching the remote CPU, TTL=3+ where normal forwarding applies). Each TTL boundary is a standalone test — not a variant — because different TTL values exercise different forwarding decisions.
- **Invalid or unexpected TTL:** Generate a negative test for TTL values that should cause the packet to be dropped or generate an ICMP TTL-exceeded message before reaching the intended destination.

### ECMP Recursive Route Scenarios

When the feature supports ECMP and routes can be resolved recursively (e.g., a static route with a nexthop that resolves via a BGP route pointing to a remote ICE/tunnel interface), generate a dedicated test for **recursive ECMP** scenarios:

- **Recursive route over ECMP base routes:** Configure a route whose nexthop resolves via multiple equal-cost paths, each pointing to different remote endpoints. Verify traffic is load-balanced across all paths.
- **ECMP path failure with recursive resolution:** Remove one of the ECMP base paths and verify the recursive route correctly converges to the remaining paths.

This is distinct from direct ECMP testing — recursive resolution adds an additional layer of nexthop resolution that may behave differently.

### Port-Active / Operational Mode Show Verification

When the feature supports different operational modes that affect interface or service forwarding state (e.g., port-active mode in EVPN multihoming, active-standby mode, all-active mode), generate **dedicated show command test cases per operational mode** — not a single show test with mode as a variant. Each mode produces different forwarding state, different DF election behavior, and different show command output. Specifically:

- **Port-active mode:** If the feature supports port-active (where only the DF forwards traffic), generate a dedicated TC verifying show commands correctly display port-active state, DF/BDF roles, and forwarding state per AC.
- **All-active mode:** If the feature supports all-active (where all PEs forward traffic), generate a dedicated TC verifying show commands correctly display the all-active state.

Do not assume that testing one operational mode covers another — each mode exercises different forwarding state management and show command output paths.

### Service State and Parameter Change Show Verification

When the feature involves services with configurable state and identifiers (e.g., EVPN instances, VPWS services, bridge domains), generate **dedicated show command test cases for service state and parameter changes** — not just initial configuration verification. Specifically:

- **Service state transitions:** Generate a dedicated TC for each service state transition (admin-up → admin-down → admin-up, operational-up → operational-down → operational-up) and verify show commands correctly reflect each state.
- **Service identifier changes:** If the service supports changing identifiers (e.g., service ID, EVI ID, VNI) while the service exists, generate a dedicated TC verifying show commands correctly update to reflect the new identifier.

Each state transition exercises different OperDB update paths and may reveal stale state in show commands.

### Route-Type-Specific Show Command Verification

When the feature involves multiple EVPN route types (Type-1 ESI, Type-2 MAC/IP, Type-3 Inclusive Multicast, Type-4 ES, Type-5 IP Prefix), generate **dedicated show command test cases per route type for route change events** — not a single consolidated route test. Each route type has different fields, different lifecycle events, and different show command display. Specifically:

- **Per-route-type change events:** For each route type, generate a dedicated TC verifying show commands correctly reflect route add, route update (e.g., MAC move for Type-2), and route withdrawal.
- **Route type interaction:** If multiple route types interact (e.g., Type-1 ESI route affecting Type-2 MAC forwarding state), generate a dedicated TC verifying show commands correctly display the interaction.

Do not assume that testing one route type covers another — each route type has different attributes, different aging/withdrawal behavior, and different show command fields.

### ESI Lifecycle Event Show Verification

When the feature involves Ethernet Segments (ESIs) that can be dynamically added, removed, or modified, generate **dedicated show command test cases for ESI lifecycle events** — not just steady-state ESI verification. Specifically:

- **ESI addition:** Generate a dedicated TC for adding a new ESI and verifying show commands immediately reflect the new ESI with correct initial state.
- **ESI removal:** Generate a dedicated TC for removing an ESI and verifying show commands correctly remove all ESI-related entries (no stale data).
- **ESI modification:** Generate a dedicated TC for modifying ESI parameters (e.g., changing the ESI value, changing the DF election algorithm) and verifying show commands correctly update.
- **Remote ESI events:** Generate a dedicated TC for remote ESI events (remote PE joins/leaves the ESI) and verifying show commands correctly reflect the remote PE changes.

Each ESI lifecycle event exercises different OperDB update and cleanup paths.

### Companion Protocol Feature Interaction (Enabled vs. Disabled)

When the feature's output or behavior is enhanced by a companion protocol feature that can be independently enabled or disabled (e.g., dynamic hostname enhances TLV output with hostnames, BFD enhances adjacency detection), generate **dedicated test cases for the feature operating with the companion feature disabled** — not just as a variant. The companion feature's absence may change the TLV/attribute content, the show command output format, or the operational behavior. Specifically:

- **Companion feature disabled:** Verify the feature operates correctly and its output is well-formed when the companion feature is disabled (e.g., POI TLV without hostname when dynamic-hostname is disabled).
- **Companion feature toggled while active:** Verify the feature adapts correctly when the companion feature is enabled or disabled while the feature is already active.

Do not assume that testing with the companion feature enabled covers the disabled case — each state may produce different protocol messages, different show output, and different interop behavior.

### Physical Interface Shutdown vs. Protocol/Feature Disable Interaction

When the feature introduces a protocol-level or feature-level disable/admin-state knob that operates independently from physical interface admin-down, generate **dedicated test cases** for the interaction between physical interface shutdown and the feature's disable knob:

- **Physical shutdown then feature disable:** Shut down the physical interface first, then disable the feature on that interface. Verify the feature correctly handles the already-down interface.
- **Feature disable then physical shutdown:** Disable the feature first, then shut down the physical interface. Verify no double-down or conflicting state.
- **Feature re-enable while physical is down:** Re-enable the feature while the physical interface remains shut down. Verify the feature does not attempt to form sessions/adjacencies on a down interface.
- **Physical re-enable while feature is disabled:** Bring the physical interface back up while the feature remains disabled. Verify the feature does not form sessions/adjacencies despite the interface being up.

These are standalone tests — the interaction between two independent disable mechanisms exercises different state machine transitions than either mechanism alone.

### Configuration Changes While Feature/Protocol is Disabled

When the feature introduces a disable/admin-state knob, generate **dedicated test cases** for making configuration changes while the feature is disabled:

- **Add new sub-resources while disabled:** Add new interfaces, instances, or sub-configurations to a disabled feature/protocol. Verify the new resources are correctly configured but not operationally active until the feature is re-enabled.
- **Modify existing configuration while disabled:** Change parameters (metrics, timers, authentication) while the feature is disabled. Verify the changes take effect when the feature is re-enabled without requiring reconfiguration.
- **Remove sub-resources while disabled:** Remove interfaces or sub-configurations while the feature is disabled. Verify the removal is clean and does not cause errors when the feature is re-enabled.

Do not assume that testing configuration changes in the enabled state covers the disabled state — the feature's state machine may handle configuration differently when disabled (e.g., no operational recalculation, no session teardown).

### Per-Hierarchy CLI Rollback and Factory-Default Decomposition

When the feature introduces configuration knobs at multiple hierarchy levels (e.g., instance level, interface level, protocol level), generate **separate CLI rollback and factory-default test cases per hierarchy level** — not a single consolidated rollback test. Each hierarchy level may have different rollback behavior, different factory-default handling, and different interaction with parent/child configuration:

- **Per-hierarchy rollback:** Generate a dedicated rollback TC for each hierarchy level (e.g., instance-level rollback, interface-level rollback, protocol-level rollback).
- **Per-hierarchy factory-default + rollback:** Generate a dedicated TC for `load factory-default` followed by rollback at each hierarchy level.

Do not assume that testing rollback at one hierarchy level covers another — each level may have different config restoration behavior.

### Protocol Authentication PDU-Type Decomposition

When the feature authenticates multiple protocol PDU types (e.g., IS-IS Hello/IIH, LSP, CSNP, PSNP; OSPF Hello, DBD, LSU, LSAck), generate **separate dedicated test cases per PDU type** — not a single "authentication" test that implicitly covers all PDU types. Each PDU type may have different authentication TLV placement, different processing rules, and different failure modes:

- **Per-PDU-type × per-algorithm:** If the feature supports multiple authentication algorithms, generate tests for each algorithm on each PDU type that is independently configurable.
- **Per-PDU-type × per-level/area:** If authentication can be configured per level or area, generate tests for each PDU type at each level/area.

Do not assume that testing authentication on Hello PDUs covers LSP or SNP authentication — each PDU type exercises different code paths for TLV insertion, validation, and error handling.

### HA Mode × Overlay Scenario Matrix

When the feature involves HA mechanisms (GR, NSR) that apply to multiple routing protocols, and those protocols interact with overlay features (BFD, LFA, RLFA, SR-TE, TI-LFA, Flex-Algo, S-BFD, RSVP FRR), generate **dedicated test cases for each HA mode × overlay scenario combination** — not a single HA test with overlay scenarios as variants. Each overlay feature changes the forwarding path, label stack, or convergence behavior during HA events:

- **Per-protocol × per-HA-mode:** If the feature supports both GR and NSR for a protocol (e.g., ISIS GR, ISIS NSR), generate separate TCs for each HA mode. Do not combine GR and NSR into a single TC.
- **Per-overlay-scenario:** For each HA mode, generate dedicated TCs for each overlay scenario the protocol supports (e.g., plain protocol, BFD, LFA, RLFA, SR-TE, TI-LFA, Flex-Algo, S-BFD). Each overlay changes the state that must be preserved or recovered during HA.
- **IGP × protocol combinations:** When the feature's protocol depends on an underlying IGP (e.g., LDP over ISIS, LDP over OSPF, BGP over ISIS, BGP over OSPF), generate separate TCs for each IGP underlay. Different IGPs have different convergence and HA behavior.

Do not assume that testing one HA mode covers the other, or that testing one overlay scenario covers another — each combination exercises different state preservation and recovery code paths.

### Service Overlay Preservation During HA Events

When the feature involves HA events that affect the routing/transport layer (e.g., container restart, process restart, switchover), and the device carries service overlays (VPWS, EVPN-VPWS, L3VPN, Bridge Domain) over the affected transport, generate **dedicated test cases for each service overlay type × transport combination**:

- **VPWS over LDP** with underlying IGP GR/NSR
- **VPWS over RSVP** with underlying IGP GR/NSR
- **VPWS over SR-TE** with underlying IGP GR/NSR
- **EVPN-VPWS** with underlying IGP GR/NSR

Each service overlay has different signaling (targeted LDP, RSVP-TE, BGP), different forwarding (MPLS, SRv6), and different state that must be preserved during HA events. Do not assume that testing the transport protocol alone covers service overlay behavior — the service layer adds additional state (pseudowire labels, service routes, MAC tables) that must survive the HA event.

### L2VPN Service-Layer Routing Mechanics

When the feature is an L2VPN service (e.g., EVPN, EVPN-VPWS, EVPN-VPWS FXC) that relies on BGP route exchange for service establishment, generate a **dedicated routing mechanics test case** covering the BGP control-plane behavior specific to the service type:

- **Route advertisement and withdrawal sequences:** Verify the correct EVPN route types are advertised (e.g., Type-1 EVI, Type-1 ESI, Type-3 IM) and withdrawn in the correct order during service lifecycle events (AC add/remove, service delete, interface shutdown).
- **Route selection and best-path:** Verify the service correctly selects the best path when multiple remote PEs advertise routes for the same service, including tiebreak behavior.
- **Route filtering by service attributes:** If the service filters routes based on attributes (e.g., eth-tag matching, extended community flags), generate a dedicated test verifying the filtering logic — not just the end-to-end traffic result.
- **Route convergence timing:** Measure the time from route advertisement to service establishment and from route withdrawal to service teardown.

This is a standalone test — do not rely on sanity or traffic tests to implicitly cover routing mechanics. Manual QA consistently tests routing behavior as a separate category.

### Cluster vs. Standalone Deployment Testing

When the feature operates on both standalone (SA) and cluster (CL) deployments, generate at least one **dedicated test case for cluster deployment** — not just a variant of the SA test. Cluster deployments involve inter-NCP communication, distributed state, and different failure domains that may affect the feature differently than SA.

### Vtysh and Internal Configuration Verification

When the feature introduces new CLI configuration, generate a **dedicated test case** for vtysh configuration verification:

- Verify the feature's configuration is correctly saved and displayed in vtysh.
- Verify numerical values entered in different bases (decimal, hexadecimal) are handled correctly — either rejected as duplicates or stored consistently.
- This is a standalone test — vtysh exercises a different config serialization path than the standard CLI.

### Internal Diagnostic and Debug Show Command Decomposition

When the feature introduces new internal diagnostic or debug show commands (e.g., `show route-queue`, `show coroutine <feature>`, `show <process> internal`, `show <feature> queue`), generate **separate dedicated test cases per show command** — not a single consolidated "show commands" test. Each internal show command exposes different internal state (queue depth, coroutine status, internal counters) and exercises different code paths. Specifically:

- **Per-command verification:** Generate a dedicated TC for each new internal show command verifying it displays correct information in both idle and active states.
- **Show command during active processing:** If the feature has internal queues or coroutines, generate a dedicated TC verifying the show command output during active processing (e.g., while the queue is draining, while a coroutine is running).
- **Show command after state transitions:** Verify the show command correctly updates after state transitions (e.g., queue empties, coroutine completes, process restarts).

Do not assume that a generic "show commands" test covers all internal diagnostic commands — each command reveals different internal state and may have different update timing.

### Route-Level Operational Sequence Testing

When the feature introduces a configuration knob that changes how routes are installed, counted, or processed (e.g., enabling/disabling per-route counters, changing route attributes, modifying installation behavior), generate **dedicated test cases for each distinct route-level operation** while the feature is in each configuration state. Do not assume that a single "enable/disable" test covers all route operations. Specifically:

- **Add route while feature is disabled/enabled:** Generate a dedicated TC for adding new routes (e.g., adding a new IS-IS neighbor, advertising new prefixes) while the feature knob is in the non-default state. Verify the new routes reflect the current feature setting.
- **Remove route while feature is disabled/enabled:** Generate a dedicated TC for removing routes (e.g., withdrawing prefixes, removing adjacencies) while the feature knob is in the non-default state. Verify cleanup is correct.
- **Combined add and remove routes:** Generate a dedicated TC for simultaneously adding and removing routes while the feature is in the non-default state. Verify both operations are handled correctly.
- **Clear protocol (graceful):** Generate a dedicated TC for clearing the routing protocol (e.g., `clear isis`, `clear ldp`) while the feature is in the non-default state. Verify routes are re-learned with the current feature setting applied.
- **Kill protocol (ungraceful):** Generate a dedicated TC for ungracefully killing the routing protocol process (e.g., `kill -9 isisd`) while the feature is in the non-default state. This is distinct from graceful restart — ungraceful kill exercises different recovery paths.
- **Remove and re-add protocol configuration:** Generate a dedicated TC for removing the entire protocol configuration and re-adding it while the feature knob remains in the non-default state. Verify routes are re-established with the correct feature behavior.
- **Enable feature then clear protocol:** Generate a dedicated TC for enabling the feature (switching from non-default to default state) and then clearing the protocol to trigger route re-installation. Verify routes reflect the newly enabled state.
- **Sequence: remove route → change feature state → add route back:** Generate a dedicated TC for the specific sequence where routes are removed first, then the feature state is changed, then routes are added back. This verifies the feature state is correctly applied to routes that are added after the state change, not just existing routes.
- **Clear counters/statistics command:** If the feature involves counters or statistics, generate a dedicated TC for the clear counters command (e.g., `clear mpls forwarding-table counters`) while the feature is in each state. Verify the clear command behaves correctly in both enabled and disabled states.

Each route-level operation exercises different code paths for route installation, withdrawal, and state management. Manual QA consistently tests each operation independently.

### HA State Store Extension Testing (NSR/GR)

When a feature extends the HA state synchronization store (e.g., adding new fields to a Redis table, extending GR/NSR state data), generate **dedicated test cases** for the state store extension itself, beyond the functional HA tests:

- **Encoding/decoding correctness:** Verify the new fields are correctly encoded into the state store and decoded after recovery. Do not assume that functional HA tests implicitly cover encoding correctness — a field could be incorrectly encoded but produce a "close enough" result that passes functional checks.
- **Backward compatibility (upgrade):** Verify that upgrading from a version without the new fields to a version with them handles the missing fields gracefully (default values applied, no crash, no decode failure).
- **Forward compatibility (downgrade):** Verify that downgrading from a version with the new fields to a version without them handles the unknown fields gracefully (fields ignored, no crash, no decode failure).
- **Clock-independent state representation:** If the new fields involve timestamps or durations, verify that the state store uses relative time (e.g., uptime-based) rather than absolute timestamps, to avoid discrepancies between HA peers that may have different boot times or clock skew.
- **State store memory impact at scale:** Verify that the additional fields do not cause excessive memory consumption in the state store at maximum scale (max adjacencies, max instances, max sessions).

These are standalone tests — each exercises a different aspect of the state store extension that functional HA tests may not cover.

---

### Per-AFI/SAFI Functional Mode Decomposition

When the feature changes BGP behavior per address-family (e.g., GR/LLGR, add-path, route-refresh), generate **dedicated test cases for each relevant AFI/SAFI × functional mode combination** — not a single test with AFI/SAFI as variants. Functional modes include restarter, helper, best-path selection, and any mode-specific behavior. Manual QA consistently tests each AFI/SAFI independently for each functional mode because each AFI/SAFI has different route types, next-hop handling, and label/attribute behavior. Specifically:

- For each supported AFI/SAFI (IPv4/IPv6 unicast, VPNv4/v6, LU, Flowspec, Link-state, L2VPN-EVPN, IPv4-multicast, VRF unicast), generate a dedicated TC per functional mode.
- If the feature has a Route Reflector role, generate dedicated RR TCs per AFI/SAFI — RR behavior differs across AFI/SAFIs due to different reflection rules and attribute handling.

This strengthens the existing "Per-AFI-SAFI BGP Testing" rule by requiring mode × AFI/SAFI cross-product decomposition, not just AFI/SAFI-level tests.

### BGP Capability Edge Cases on Session Re-Establishment

When the feature introduces a BGP capability that is negotiated during session establishment (e.g., GR, LLGR, add-path, extended-NH), generate **dedicated test cases for capability changes on session re-establishment**:

- **Capability missing on re-establishment:** Peer re-establishes without the previously-negotiated capability. Verify stale/retained state is correctly cleaned up.
- **AFI/SAFI missing from capability:** Peer re-establishes with the capability but without a previously-present AFI/SAFI. Verify per-AFI/SAFI state is correctly cleaned up.
- **Capability flag changes:** If the capability has per-AFI flags (e.g., F-bit for forwarding state), test re-establishment with the flag changed. Verify the feature reacts to the flag change.
- **Capability added on re-establishment:** Peer re-establishes with a new capability not present before. Verify the feature activates correctly.

These are standalone tests — each capability change scenario exercises different cleanup and activation code paths.

### Session Detection Mechanism Interaction with HA Features

When the feature involves HA mechanisms that depend on session state (e.g., GR, LLGR, NSR), generate **dedicated test cases for interaction with each session detection mechanism**:

- **BFD-triggered session down:** If BFD is configured on the session, verify whether the HA mechanism (GR/LLGR helper) activates or not when BFD brings the session down (as opposed to TCP timeout). BFD-triggered downs may bypass GR/LLGR helper activation because BFD indicates the peer is unreachable, not restarting.
- **Hold-timer expiry:** Verify HA mechanism behavior when the session goes down due to hold-timer expiry.
- **TCP reset:** Verify HA mechanism behavior when the session goes down due to TCP RST.
- **NOTIFICATION message:** Verify HA mechanism behavior when the session goes down due to a NOTIFICATION message.

Each detection mechanism may trigger different HA behavior. Do not assume that testing one session-down trigger covers all.

### Cascading Failure During Active HA Recovery

When the feature involves HA recovery that takes extended time (e.g., LLGR stale retention, long GR timers), generate a **dedicated test case for a second failure occurring during active recovery**:

- **Helper failure during active helper state:** If the DUT is acting as a helper (retaining stale routes) and the DUT itself fails, verify the cascading failure behavior — are the stale routes from the original failure preserved or lost?
- **Second peer failure during active recovery:** If the DUT is recovering from one peer failure and a second peer fails, verify both recoveries proceed correctly without interference.
- **HA event during active recovery:** If the DUT is in HA recovery (e.g., LLGR helper) and an HA event occurs (process restart, switchover), verify the interaction.

These are standalone tests — cascading failures exercise different state management than single failures.

### ECMP Interaction with Degraded/Stale Routes

When the feature can mark routes as degraded or stale (e.g., LLGR stale, dampened, community-marked), generate a **dedicated test case for ECMP behavior with mixed stale and non-stale paths**:

- **Stale path removal from ECMP:** If one of multiple ECMP paths becomes stale/degraded, verify it is removed from the ECMP set and traffic shifts to non-stale paths.
- **All paths stale:** If all ECMP paths become stale, verify traffic continues on stale paths (as least-preferred but still valid).
- **Stale path recovery in ECMP:** When a stale path is refreshed, verify it is re-added to the ECMP set.

Do not assume that a single best-path test covers ECMP behavior — ECMP path sets have different selection and installation logic than single best-path.

### BGP Route Origination Feature Interaction

When the feature changes how BGP processes or retains routes (e.g., GR/LLGR stale retention, dampening), generate **dedicated test cases for interaction with each route origination method**:

- **Aggregate-route:** Verify the feature's behavior with BGP aggregate routes (summary routes). Aggregates have different withdrawal behavior than individual routes.
- **Default-originate:** Verify the feature's behavior with default route origination.
- **Network statement:** Verify the feature's behavior with routes originated via network statement.
- **Redistribution:** Verify the feature's behavior with redistributed routes.

Each origination method has different lifecycle management. Do not assume that testing with one origination method covers all.

### Cross-Protocol Feature State Interaction

When a feature can be independently enabled or disabled across multiple routing protocols (e.g., SR can be enabled under OSPF and ISIS independently), generate a **dedicated test case for cross-protocol state combinations**:

- Feature enabled in Protocol A, disabled in Protocol B (and vice versa).
- Feature enabled in both protocols simultaneously.
- Toggle the feature in one protocol while the other protocol's feature remains active.

These are standalone tests — each protocol has independent state management, and cross-protocol interactions (e.g., shared SRDB, shared label space) may reveal conflicts.

### Scale-Specific Operational Scenarios

When the feature operates under scale (large number of prefixes, peers, LSAs, etc.), generate dedicated test cases for **operational actions under scale**, not just "verify at maximum scale":

- **Partial state removal under scale:** Remove a subset of the scaled state (e.g., remove some prefixes, shut down some peers) and verify correct cleanup without affecting remaining state.
- **Full config removal and re-add under scale:** Remove the entire feature configuration while at scale, then re-add it. Verify correct state rebuild.
- **Single-commit bulk configuration under scale:** Apply the feature configuration together with large-scale topology configuration in a single commit. Verify correct initialization order and state consistency.

These scenarios test different code paths than steady-state scale verification — they exercise cleanup, rebuild, and initialization logic under resource pressure.

---

### Per-Entity Maximum Scale Testing

When the feature supports a maximum number of sub-entities per parent entity (e.g., maximum BGP peers per VRF, maximum routes per table, maximum interfaces per bundle) or multiple sub-resources per entity (e.g., multiple paths per policy, multiple segment-lists per path, multiple SIDs per segment-list), generate a **dedicated scale test case** for the per-entity maximum — in addition to the overall system-wide scale test. A single VRF with 2,000 BGP peers exercises different code paths than 1,500 VRFs with a few peers each; similarly, a single policy with 16 paths exercises different code paths than 16 policies with 1 path each. Specifically:

- **Single-entity max scale:** Configure the maximum number of sub-entities or sub-resources on a single parent entity and verify correct operation.
- **Over-scale per entity:** Attempt to exceed the per-entity maximum and verify rejection or graceful handling.

Do not assume that system-wide scale tests cover per-entity maximum behavior — per-entity limits may have different enforcement mechanisms and resource constraints.

---

### Container-Level HA Decomposition

When decomposing HA tests, include **container-level restarts** (routing container, DP container, infra container) as **separate dedicated test cases** in addition to individual process restarts. A container restart exercises different recovery paths than individual process restarts — it restarts all processes within the container simultaneously and tests the container orchestration and initialization ordering. Do not assume that testing individual process restarts within a container covers the container restart case.

---

### Per-RIB Table Show Command Decomposition

When the feature installs routes or backup paths that are visible in multiple RIB tables (e.g., IPv4 unicast, MPLS NH, color-MPLS-NH, protocol-specific tables), generate **dedicated test cases per RIB table** — not a single consolidated show-command test that checks all tables as steps. Each RIB table has unique fields, flags, and verification needs. Manual QA teams typically create one test per RIB table. Consolidating them into a single TC causes partial coverage scoring.

---

### Protection Mode × SRLG Mode Full Decomposition

When a feature has multiple orthogonal configuration dimensions (e.g., protection type × strictness mode × path scope), generate **dedicated test cases for each significant combination** — not just one TC per dimension. Specifically:

- If the feature has N protection modes and M strictness/scope modes, generate dedicated TCs for each combination that produces different backup path selection behavior.
- Do not assume that testing protection-mode=link with strict and protection-mode=node with loose implicitly covers protection-mode=node with strict.
- When manual QA tests decompose by combination (e.g., link+strict, node+strict, link+loose+full-path, node+loose+full-path), the generated plan must match that decomposition.

---

### SR-TE and Labeled Route Protection Testing

When the feature provides backup path protection (e.g., TI-LFA, FRR), generate a **dedicated test case** for protection of SR-TE policy routes and labeled routes, not just IGP unicast routes. SR-TE routes have different label stack construction and may have different backup path constraints. Include:

- Backup path for SR-TE policy routes
- Max label stack depth exceeded scenario — verify graceful handling when the repair tunnel label stack exceeds the platform maximum

---

### ECMP Decomposition by Protection Type

When the feature supports multiple protection types (e.g., link protection, node protection) and the feature interacts with ECMP, generate **separate ECMP test cases per protection type**. ECMP with link protection and ECMP with node protection exercise different backup path computation logic. Do not consolidate into a single ECMP TC.

---

### Flex-Algo Decomposition by Protection Type

When the feature supports Flex-Algo and multiple protection types, generate **separate Flex-Algo test cases per protection type** (e.g., flex-algo with link protection, flex-algo with node protection). Each combination may have different constraint satisfaction behavior during backup path computation.

---

### Platform × Mode Cross-Product Decomposition

When the feature has multiple operational modes (e.g., SRLG modes: strict, loose, strict-full-path, loose-full-path) and is tested on multiple platforms (e.g., SA, cDNOS), generate **dedicated test cases for each platform × mode combination** when manual QA decomposes platform tests by mode. Do not consolidate multiple modes into a single platform TC with other modes as variants — each mode may exercise different backup path computation, different label stack construction, or different fallback behavior on the platform.

---

### Sub-Feature Scenario Decomposition for Area/Topology Enhancements

When the feature includes a sub-feature or enhancement that operates across multiple topology scenarios (e.g., preferred area enhancement with single segment-list, multiple segment-lists from same area, multiple segment-lists from different areas, dynamic paths, metric types), generate **dedicated test cases per scenario** — not a single TC with scenarios as variants. Each scenario exercises different path resolution, area selection, and metric computation logic. Specifically:

- **Per-segment-list-composition:** If the sub-feature behavior depends on how segment-lists are composed (e.g., all adj-SIDs from same area vs. each from different areas vs. mixed), generate a dedicated TC per composition.
- **Per-path-type:** If the sub-feature supports both static and dynamic paths, generate separate TCs for each.
- **Per-metric-type:** If the sub-feature's behavior differs based on metric type (TE vs. IGP, equal vs. unequal cost), generate separate TCs.
- **HA interaction:** If the sub-feature has HA implications (e.g., process restart affecting area resolution), generate a dedicated HA TC for the sub-feature.

Do not assume that testing one scenario covers another — each composition, path type, and metric type exercises different resolution and selection code paths.

---

### Topology Role × Mode Full Cross-Product

When the feature operates on a specific topology role (e.g., ABR, PE, RR) and has multiple operational modes, generate **dedicated test cases for each topology role × mode combination** — not a single topology-role TC with modes as variants. Each mode changes the backup path computation, protection availability, or fallback behavior at that topology role. When manual QA tests decompose by role × mode (e.g., ABR+loose, ABR+strict, ABR+loose-full-path, ABR+strict-full-path), the generated plan must match that decomposition.

### Unsupported Attachment Point / Condition Handling

When the feature extends a policy condition or match criterion with new qualifiers (e.g., adding a `protocol` qualifier to an existing `rib-has-route` condition), generate **dedicated negative test cases** for each attachment point where the new qualifier is NOT supported:

- **Unsupported attachment point behavior:** Verify that when the new qualifier is applied to an unsupported attachment point, the system handles it gracefully — either ignoring the qualifier and falling back to the base condition, or treating the condition as unsupported (no tracking, no crash). The expected behavior should match the feature specification.
- **Supported vs. unsupported attachment point matrix:** If the feature supports the qualifier on some attachment points but not others, generate a dedicated TC for each unsupported attachment point verifying the graceful handling.

Do not assume that testing on supported attachment points covers the unsupported case — unsupported attachment points exercise different code paths for condition evaluation and may expose crashes or incorrect behavior.

### Route Qualifier and Best-Path Selection Testing

When the feature adds qualifiers to route matching conditions (e.g., matching by source protocol, matching by route type, matching by community), generate **dedicated test cases** verifying that the qualifier applies only to the selected/best route:

- **Best route matches qualifier:** Verify the condition is MET when the best route matches the qualifier.
- **Best route does NOT match qualifier, but backup route does:** Verify the condition is NOT MET — the qualifier must evaluate against the selected best route only, not backup routes.
- **Best route changes dynamically:** Verify the condition re-evaluates correctly when the best route changes (e.g., due to preference changes, route withdrawal, or new route advertisement).

These are standalone tests — each scenario exercises different evaluation paths in the route tracking logic.

### Scale: Feature Parameter Variation at Scale

When the feature has configurable parameters that affect evaluation logic (e.g., operation modes, threshold types, monitoring modes, mask matching behavior), generate **dedicated scale test cases** for each significant parameter variation at scale — not just a single "max scale" test. Each parameter variation exercises different evaluation paths at scale and may reveal different performance or correctness issues:

- **Evaluation mode at scale:** If the feature supports multiple evaluation modes (e.g., AND vs. OR, weight-threshold vs. number-of-failed-objects), generate a dedicated scale test per evaluation mode.
- **Feature toggle at scale:** If the feature has a toggle that changes behavior (e.g., invert-monitoring, ignore-default-route), generate a dedicated scale test with the toggle enabled and verify correct behavior at scale.
- **Parameter boundary at scale:** If the feature has parameters with boundary values that affect matching or evaluation (e.g., prefix mask lengths, threshold values), generate a dedicated scale test exercising boundary values at scale.

Do not assume that a single scale test with default parameters covers all parameter variations — each variation may exercise different code paths at scale.

### Scale: Monitor/Target Unavailability at Scale

When the feature monitors external targets (e.g., interfaces, route-reachability prefixes, BFD sessions, tracked objects), generate **dedicated scale test cases** for the scenario where monitored targets become unavailable at scale:

- **All targets unavailable simultaneously:** At maximum scale, make all monitored targets unavailable at once. Verify the feature correctly evaluates all monitors and transitions to the expected state without crash or excessive resource consumption.
- **Partial target unavailability:** At maximum scale, make a subset of monitored targets unavailable. Verify the feature correctly evaluates only the affected monitors and the overall state reflects the partial failure.

This is distinct from simply configuring scale — target unavailability at scale exercises the failure detection and state transition paths under load, which may reveal different issues than steady-state scale testing.

### Multi-VRF Scenario Decomposition

When the feature operates in VRF context, generate **dedicated test cases** for multi-VRF scenarios — not just a single non-default VRF test:

- **Single non-default VRF:** Feature operates in one non-default VRF (basic VRF test).
- **Multiple non-default VRFs simultaneously:** Feature operates in 2+ non-default VRFs simultaneously. Verify each VRF's feature state is independent and correct.
- **Default VRF + non-default VRF simultaneously:** Feature operates in both default and non-default VRF at the same time. Verify no cross-VRF interference.

Do not assume that testing in a single non-default VRF covers multi-VRF behavior — multiple VRFs may share resources or compete for state, revealing issues not visible with a single VRF.

### Kernel/Netlink-Learned State Testing

When the feature learns state from the Linux kernel via netlink (e.g., addresses, routes, interface state), generate **dedicated test cases** for netlink-specific scenarios:

- **Protocol filtering:** If the feature filters netlink messages by protocol type (e.g., RTPROT_DHCP, RTPROT_RA, RTPROT_STATIC), generate a dedicated test verifying that only the expected protocol types are learned and others are correctly ignored.
- **Netlink listener restart:** Generate a dedicated test for the scenario where the process listening to netlink (e.g., zebra) restarts — verify all kernel-learned state is re-acquired from netlink after recovery.
- **Stale state cleanup:** If the feature marks kernel-learned state as stale on component disconnect (e.g., NCP/FibManager disconnect), generate a dedicated test verifying stale state is correctly cleaned up after timeout and refreshed on reconnect.
- **Flag-based detection:** If the feature uses netlink message flags (e.g., non-permanent flag for DHCP addresses) to classify state, generate a dedicated test verifying correct classification and that state with different flags is not misclassified.

Do not assume that testing the feature's functional behavior covers netlink-specific edge cases — netlink communication has its own failure modes, filtering logic, and recovery paths.

### Route Source Preference and Coexistence Testing

When the feature introduces a new route type or source with specific metric/preference values (e.g., DHCP routes with max metric and low preference), generate **dedicated test cases** for route source coexistence and preference:

- **Preference ordering:** Generate a test with multiple route sources (static, IGP, the new source) for the same prefix, verifying the correct preference ordering.
- **Dynamic source addition/removal:** Generate a test where higher-preference route sources are added and removed while the feature's route is present, verifying correct failover and failback behavior.
- **Route overwrite protection:** If the feature's route can coexist with routes from other VRFs or sources, generate a dedicated test verifying the feature's route is not incorrectly overwritten (especially in cross-VRF scenarios).

Do not assume that a single functional test covers route preference behavior — each route source combination exercises different best-path selection logic.

---

### PIC/FRR Failover Feature Testing

When the feature involves Prefix Independent Convergence (PIC), Fast Reroute (FRR), or similar failover mechanisms that switch traffic between pre-installed primary and alternate paths, generate **dedicated test cases for each distinct underlay type** that the feature supports:

- **IGP-resolved nexthop:** Test failover when the BGP nexthop is resolved via IGP (IS-IS, OSPF).
- **RSVP-resolved nexthop:** Test failover when the BGP nexthop is resolved via RSVP tunnel.
- **SR-TE-resolved nexthop:** Test failover when the BGP nexthop is resolved via SR-TE policy.
- **Static-resolved nexthop:** Test failover when the nexthop is a static route.
- **Recursive BGP nexthop:** Test failover when the BGP nexthop is itself resolved via another BGP route.

Each underlay type has different failure detection, resolution, and convergence characteristics. Do not assume that testing with one underlay covers another.

Additionally, for PIC/FRR features, generate dedicated test cases for each **NHOID role**:
- **Primary in ECMP:** Verify removal from ECMP group when unreachable.
- **Single primary with alternate:** Verify failover to alternate.
- **Single primary without alternate:** Verify expected traffic loss (no action).
- **Alternate unreachable:** Verify no action on primary traffic.

### Overlay Service Nexthop Failover

When the feature affects nexthop resolution for overlay services (EVPN, VPWS, FLOWSPEC, L3VPN), generate **dedicated test cases per overlay service type** — not a single "overlay" test with other services as variants. Each overlay service has different control-plane signaling, different nexthop resolution, and different data-plane behavior during failover.

### TCP/Socket Buffer Testing at Scale

When the feature increases the scale of protocol sessions (e.g., BGP peers, RSVP tunnels, LDP sessions) that use TCP or socket-based communication, generate a **dedicated test case** for socket buffer behavior at the new scale limit:

- **Tx socket buffer exhaustion:** At maximum session scale, generate large protocol messages (e.g., BGP UPDATEs with many prefixes) and verify no messages are dropped due to Tx buffer exhaustion.
- **Socket buffer after HA events:** After switchover or process restart at scale, verify socket buffers are correctly allocated on the new active and no sessions reset due to socket issues.

Do not assume that functional scale tests cover socket buffer behavior — buffer exhaustion manifests only under specific message-size × session-count combinations.

---

### Subnet/Prefix-Length Variation Testing

When the feature operates on routes or addresses that can have different prefix lengths (e.g., /24, /27, /30, /31 for IPv4; /64, /120, /127 for IPv6), generate **dedicated test cases for prefix-length boundary values** — not a single test with one prefix length. Different prefix lengths exercise different forwarding table entries, different broadcast domain behavior, and different address allocation logic:

- **Common IPv4 prefix lengths:** /31 (point-to-point), /30 (legacy P2P), /27 (small subnet), /24 (standard subnet).
- **Common IPv6 prefix lengths:** /127 (point-to-point), /120 (small subnet), /64 (standard subnet).

Do not assume that testing with one prefix length covers another — each prefix length may produce different route installation, forwarding table entries, and ARP/NDP behavior.

### Duplicate and Overlapping Address Handling

When the feature installs or manages routes that can have duplicate or overlapping prefixes (e.g., the same prefix learned from multiple sources, overlapping subnets on different interfaces), generate **dedicated test cases** for:

- **Duplicate prefix from multiple sources:** Verify the feature correctly handles the same prefix arriving from different sources or interfaces. Verify tiebreak/preference behavior.
- **Overlapping subnets:** Verify the feature correctly handles overlapping subnets (e.g., /24 and /27 within the same /24) on different interfaces or from different sources. Verify longest-prefix-match forwarding is correct.

Do not assume that basic functional tests cover duplicate/overlapping address scenarios — these edge cases exercise different route comparison, installation, and forwarding logic.

### Multi-Node ECMP Decomposition in Distributed Architectures

When the feature supports ECMP and operates in a distributed or multi-node architecture (e.g., multi-NCP cluster, multi-PE topology), generate **dedicated ECMP test cases per node topology** — not a single ECMP test:

- **ECMP on local node only:** All ECMP paths terminate on the local node's interfaces.
- **ECMP on remote node only:** All ECMP paths are learned from or terminate on a remote node.
- **ECMP across multiple nodes:** ECMP paths span multiple nodes (e.g., some paths via NCP-0, others via NCP-1).

Each node topology exercises different forwarding path resolution, different inter-node communication, and different failure domain behavior. Do not assume that testing ECMP on a single node covers the multi-node case.

### Show Command Default Output Mode Change

When a feature changes the default output mode of an existing show command (e.g., from detailed to brief, from verbose to summary), generate **dedicated test cases** for the output mode transition:

- **New default verification:** Verify the new default output mode is active on a fresh installation with the new version.
- **Detail/verbose keyword verification:** Verify the keyword to access the previous default output (e.g., `detail`, `verbose`) is available, tab-completable, and produces the full output.
- **Upgrade behavior:** Verify that upgrading from a version with the old default to the new version correctly changes the default output mode. No explicit configuration should be required.
- **Downgrade behavior:** Verify that downgrading reverts the default output mode to the old behavior.
- **Pipe compatibility:** Verify all pipe operations (`count`, `include`, `exclude`, `find`, `no-more`, `tail`, `monitor interval`) work correctly with both the new default output and the keyword-accessed output.
- **Scale output:** Verify both output modes handle maximum scale (e.g., maximum interfaces, maximum entries) without truncation, corruption, or excessive execution time.

Do not assume that testing the new default output covers the keyword-accessed output — each output mode may exercise different formatting, data collection, and rendering code paths.

---

### Per-Command CLI Verification for CLI Migration Epics

When the feature is a CLI infrastructure migration (e.g., migrating commands from manual CLI to auto-generated CLI), generate **dedicated test cases per individual CLI command or sub-command** — not a single grouped test per protocol or command hierarchy. Each CLI command has its own YANG leaf, its own range validation, its own auto-complete behavior, and its own `no` form. Manual QA consistently tests each command independently. Specifically:

- **One TC per CLI command:** For each migrated command (e.g., `protocols ldp admin-state`, `protocols ldp administrative-distance`, `protocols ldp class-of-service`), generate a dedicated TC that configures the command, verifies it in `show config`, verifies the value is applied in the backend (vtysh or operational state), and removes it with `no`.
- **Do not group commands into protocol-level TCs:** A single "LDP CLI Sanity" test that configures a few representative LDP commands does NOT cover all individual commands. Each command may have different YANG type, different range, different default, and different commit-time validation.
- **Debug sub-commands as standalone TCs:** When the feature migrates debug commands with multiple protocol options (e.g., `debug arp`, `debug bgp`, `debug isis`), generate a dedicated TC per debug protocol option — not a single "Debug Sanity" test with individual protocols as variants.

This rule applies specifically to CLI migration epics where the primary deliverable is command-by-command parity between old and new CLI infrastructure.

---

### Per-Attribute-Type Decomposition for Multi-Type Features

When a feature supports multiple attribute types that share the same syntax but operate on different data (e.g., community-list, extended-community-list, large-community-list; or IPv4 prefix-list, IPv6 prefix-list), generate **dedicated test cases per attribute type** — not a single test with other types as variants. Each attribute type may have different encoding, different matching logic, different scale limits, and different interaction with other features. Specifically:

- **One functional TC per attribute type:** If the feature works on community-list, extended-community-list, and large-community-list, generate separate sanity, modification, scale, HA, and evaluation-order TCs for each type.
- **Per-type scale TC:** Each attribute type may have different scale characteristics. Generate a dedicated scale test per type.
- **Per-type HA TC:** Generate separate system restart and process restart TCs per attribute type to verify each type's state is correctly preserved.

Do not assume that testing with one attribute type covers another — each type exercises different parsing, storage, and evaluation code paths.

---

### Coexisting Commands in Same Rule/Hierarchy

When a feature introduces a new command variant that coexists with an existing command in the same configuration hierarchy (e.g., `set community` coexists with `set community-list` in the same rule), generate a **dedicated test case** for the coexistence scenario:

- **Both commands in same rule:** Verify that both the existing command and the new command can be configured in the same rule simultaneously, and that the combined effect is correct.
- **Interaction and precedence:** Verify the processing order when both commands affect the same attribute (e.g., `set community additive` and `set community-list ... delete` in the same rule).
- **Removal of one while other remains:** Verify that removing one command does not affect the other.

Do not assume that testing each command independently covers the coexistence case — combined commands may have interaction effects.

---

### Control Plane Rate Limiting (CPRL) Interaction

When the feature sends or receives protocol packets that are subject to Control Plane Rate Limiting (CPRL) — such as ICMP, BFD, LLDP, or any protocol using raw sockets — generate a **dedicated test case** verifying the feature's behavior under CPRL constraints:

- **CPRL counters:** Verify CPRL counters for the relevant protocol category (e.g., ICMP/ICMPv6) increment correctly when the feature sends/receives packets.
- **CPRL rate limiting impact:** At high scale (many sessions or high probe rate), verify the feature's packets are not excessively rate-limited by CPRL, causing false loss or timeout reports.
- **CPRL category verification:** Verify the feature's packets are classified into the correct CPRL category.

Do not assume that basic functional testing covers CPRL interaction — CPRL rate limiting only manifests at scale or high packet rates and can cause subtle accuracy issues.

### OAM/Diagnostic Feature Destination Type Decomposition

When an OAM or diagnostic feature (e.g., IP SLA, ping, traceroute, BFD) supports probing destinations that can be reached via different route types, generate **dedicated test cases per destination route type** — not a single test with route type as a variant. Each route type exercises different forwarding path selection and may have different reachability behavior:

- **Directly connected destination:** Destination is on a directly connected interface.
- **IGP-learned destination:** Destination is learned via an IGP (IS-IS, OSPF).
- **BGP-learned destination:** Destination is learned via BGP.
- **Static route destination:** Destination is reachable via a static route.

Do not assume that testing with one route type covers another — each route type has different nexthop resolution and may affect probe source selection differently.

### Feature Coexistence with Sibling Features

When the feature is one of multiple features sharing the same infrastructure or process (e.g., IP SLA ICMP Echo and STAMP sharing the OAM daemon, BFD single-hop and BFD multi-hop sharing the BFD process), generate a **dedicated test case** verifying coexistence:

- **Both features active simultaneously:** Configure and enable both the feature under test and its sibling feature. Verify both operate correctly without interference.
- **Shared resource contention:** If both features share a resource (e.g., session table, socket pool, process memory), verify that maximum scale of one feature does not degrade the other.
- **Shared process restart:** Verify that restarting the shared process correctly recovers both features.

Do not assume that testing the feature in isolation covers the coexistence case — shared infrastructure introduces contention and ordering dependencies.

### Dynamic Service Reconfiguration and Migration Testing

When the feature attaches to or operates within a service instance (e.g., an EVPN EVI, a bridge domain, a VPN instance), generate **dedicated test cases** for dynamic reconfiguration scenarios where the feature's service association changes while the feature is active:

- **Move feature between service instances:** If the feature can be moved from one service instance to another (e.g., IRB moved between EVIs, interface moved between VRFs), generate a dedicated test verifying the move completes correctly, the feature detaches cleanly from the old instance and attaches to the new one, and traffic/state updates accordingly.
- **Transport protocol change:** If the service instance supports multiple transport protocols (e.g., MPLS vs. VXLAN), generate a dedicated test for changing the transport protocol while the feature is attached. Verify the feature adapts to the new transport without requiring manual re-configuration.
- **Feature entity creation/deletion cycles:** Generate a dedicated test for repeated creation and deletion of the feature entity (e.g., IRB interface, tunnel, policy) while the parent service is active. Verify no resource leaks or stale state after multiple cycles.
- **Feature attribute modification while active:** If the feature has attributes that can be changed at runtime (e.g., MAC address, IP address, VNI), generate a dedicated test for modifying each attribute while traffic is flowing. Verify the change takes effect without requiring a service restart.

Do not assume that initial configuration tests cover dynamic reconfiguration — the code paths for create, modify, and move are often different and may have different error handling.

### Control-Plane "For-Us" Traffic Testing

When the feature introduces or modifies an interface that can be a destination for control-plane traffic (e.g., IRB interface, loopback, tunnel endpoint), generate **dedicated test cases** for "for-us" (locally-terminated) traffic scenarios:

- **Ping/traceroute to feature interface:** Verify the DUT responds to ICMP echo requests (ping) and traceroute directed at the feature's interface IP address, from both local and remote sources.
- **Management protocols via feature interface:** If the feature's interface can serve as a source or destination for management protocols (SSH, SNMP, NTP, syslog), generate a dedicated test verifying management connectivity through the feature's interface.
- **Protocol packets to feature interface:** If the feature's interface participates in protocol exchanges (ARP, NDP, BFD, VRRP), generate dedicated tests for each protocol verifying correct handling of protocol packets destined to the feature's interface.

Do not assume that data-plane forwarding tests cover control-plane "for-us" traffic — these packets follow different processing paths (punt to CPU, local delivery) and may have different rate-limiting and priority handling.

### Code Refactoring Epic Testing

When the epic is a code refactoring (internal restructuring with no new user-facing features), generate a **regression-focused test plan** that covers all existing functionality affected by the refactoring. Specifically:

- **Per-service-type/per-entity regression:** If the refactoring separates previously-shared code into per-type implementations (e.g., service types, protocol variants), generate **dedicated regression test cases for each type/entity** — not a single generic regression test. Each type may exercise different code paths in the refactored implementation.
- **Service type dispatch verification:** If the refactoring introduces a dispatch mechanism (e.g., factory pattern, service map, type registry), generate a dedicated test verifying correct dispatch to each type, including creation, modification, deletion, and type-specific operations.
- **Cross-type interference testing:** Generate a dedicated test verifying that operations on one type do not interfere with other types — especially when multiple types are active simultaneously.
- **Interface/resource migration between types:** If an entity (e.g., interface, route-target) can be moved from one type to another, generate a dedicated test for the migration path, verifying no stale state from the previous type.
- **HA per refactored type:** Generate separate HA tests (process restart, container restart, switchover) with all refactored types active simultaneously, verifying each type recovers correctly.
- **Upgrade from pre-refactor to post-refactor version:** Generate a dedicated upgrade test verifying that configurations created on the pre-refactor version are correctly handled by the post-refactor code, including any internal data structure migration.

Do not assume that a single "sanity" test covers all refactored types — each type exercises different code paths in the new implementation and may reveal type-specific regressions.

### EVPN Multi-Homing Port-Active and ESI Change Decomposition

When the feature involves EVPN multi-homing (MH) across multiple service types (EVPN, EVPN-VPWS, EVPN-VPWS FXC), generate **dedicated test cases per service type** for each MH-specific operation:

- **Port-active behavior:** Generate a separate TC per service type verifying port-active (single-active / all-active) behavior, including traffic forwarding when the active port changes. Do not collapse port-active testing across service types into a single TC — each service type may have different forwarding behavior when the active port changes.
- **ESI changes (local + remote):** Generate a separate TC per service type verifying ESI add/remove/modify behavior, including both local ESI changes (on the DUT) and remote ESI changes (on the peer PE). Each service type may handle ESI state differently in the refactored code.
- **Service-specific identifier changes:** When a service type has a unique identifier (e.g., NVID for FXC, service-id for VPWS), generate a dedicated TC for modifying that identifier while the service is active. Do not assume that generic eth-tag modification tests cover service-specific identifier changes.

### Service State and Identifier Modification Testing

When the feature involves services with configurable state and identifiers (e.g., admin-state, service-id, NVID, VLAN-id), generate **dedicated test cases** for modifying each identifier while the service is operationally active:

- **Service state toggle:** Verify the service correctly transitions between admin-enabled and admin-disabled states, and that traffic stops/resumes accordingly.
- **Service identifier change:** Verify the service correctly re-establishes with a new identifier (e.g., new EVI, new NVID) without requiring full service deletion and re-creation.
- **AC (Attachment Circuit) changes:** Generate a dedicated TC per service type for AC add/remove/modify operations. Each service type may have different AC binding behavior.

Do not assume that basic sanity tests cover service state and identifier modification — the modification code path is often different from the creation code path.

### Service Payload Type Decomposition

When the feature adds MPLS labels, entropy labels, or other encapsulation elements that apply across multiple service/payload types (e.g., IPv4 unicast, IPv6 unicast, L3VPN, EVPN, EVPN-VPWS, EVPN-VPWS-FXC), generate **dedicated test cases per payload type** — not a single generic "data plane" test. Each payload type may have different:

- Label stack structure (number of labels, position of entropy/FAT labels)
- Control-word behavior (present/absent, interaction with entropy label)
- ECMP hashing behavior (different header fields used for hashing)
- Load balancing on LAG members

Also generate a dedicated test for **interaction between the feature and related encapsulation features** (e.g., entropy label vs. FAT label priority, entropy label vs. control-word).

### ECMP/LFA with Mixed Path Types

When the feature's behavior depends on whether all paths share a common capability (e.g., all ECMP paths must have entropy label for EL to be added), generate dedicated test cases for **mixed path type scenarios**:

- **Mixed labeled-unicast (LU) + unicast (UC) paths:** When ECMP or LFA paths include both LU and UC nexthops, verify the feature correctly evaluates capability across the mixed set.
- **Combined ECMP + LFA:** When both ECMP and LFA backup paths exist, verify the feature evaluates capability across all paths (primary ECMP + LFA backup).
- **Negative mixed case:** When one path in the set lacks the capability, verify the feature correctly disables the capability for the entire set.

Do not assume that a test with homogeneous path types covers the mixed case — mixed paths exercise different evaluation logic.

### Transit and Penultimate Hop Popping (PHP) Scenarios

When the feature involves MPLS label operations that differ based on the router's role in the LSP (ingress, transit, penultimate hop, egress), generate **dedicated test cases per role**:

- **Transit label-to-label:** Verify the feature's behavior when the router swaps labels (does not pop to IP).
- **Penultimate Hop Pop (PHP):** Verify the feature's behavior when the router pops the transport label and forwards based on the next label or IP header.
- **Egress:** Verify the feature's behavior when the router is the final label disposition point.

Each role has different forwarding behavior and may handle the feature's labels/attributes differently. Do not collapse all roles into a single "transit" test.

### Link Identification Mechanism Changes

When a feature changes how links are identified in the topology (e.g., from IP addresses to numeric link IDs, or from GUA to link-local addresses), generate **dedicated test cases for every consumer of link identification**. Each consumer uses link identity differently and may have distinct code paths for the new identification mechanism:

- **TI-LFA:** Verify backup path computation correctly uses the new link identification (e.g., link IDs instead of IP addresses) for link/node/SRLG protection.
- **Microloop (uLoop) avoidance:** Verify uLoop avoidance correctly computes micro-loop-free paths using the new link identification. Generate separate TCs for each event type (local link event, remote link event, local metric event, remote metric event, multiple events) and each route type (IGP unicast routes, SR routes, Flex-Algo routes).
- **SR-TE dynamic path:** Verify SR-TE dynamic path computation correctly uses the new link identification for constraint-based path calculation, topology change updates, and topology mode transitions.
- **Flex-Algo:** Verify Flex-Algo constraint evaluation and path computation correctly use the new link identification.

Do not assume that basic adjacency and reachability testing covers these consumers — each has independent path computation logic that must be validated with the new link identification mechanism.

### Infrastructure Enabler Per-Container Restart Decomposition

When the feature is an infrastructure enabler that introduces or modifies a container (e.g., inband-engine, management-engine, policy-executor) or changes how existing containers interact with shared resources (namespaces, VRFs, persistent state), generate **dedicated HA restart test cases for every container that interacts with the feature** — not just the feature's own container. Each container has different restart behavior, different dependencies on the shared resource, and different recovery paths:

- **Per-NCC container restart:** If the feature's shared resource is consumed by NCC-level containers (e.g., routing-engine, management-engine, dnos-agent, ncc-conductor, node-manager, policy-executor, cluster-engine, inband-engine), generate a separate restart test for each container that depends on or interacts with the feature's resource.
- **Per-NCP container restart:** If the feature affects NCP-level containers (e.g., datapath), generate a separate restart test for each affected NCP container.
- **Per-process restart within the feature's container:** If the feature's container runs multiple processes, generate a test that restarts each process individually (not just the entire container).

Do not collapse all container restarts into a single "container restart" test or list them as variants — each container has different initialization sequences, dependency ordering, and failure modes.

### Infrastructure Enabler Per-Protocol Regression Testing

When the feature is an infrastructure enabler that affects the runtime environment of routing protocols (e.g., namespace management, interface management, VRF persistence, container lifecycle), generate **dedicated per-protocol functional regression tests** for each routing protocol that runs in the affected environment:

- Generate a separate test for each major routing protocol (ISIS, OSPF, BGP, MPLS/LDP, RSVP, SR/SR-TE, Static, VRRP, PIM) verifying that the protocol's basic functionality (adjacency formation, route exchange, traffic forwarding) works correctly after the infrastructure change.
- Generate a dedicated test for ARP/NDP functionality, as these are critical for L3 interface operation and may be affected by namespace or interface management changes.
- Generate a dedicated test for interface configuration/operation changes (add/remove/modify interfaces, change interface types) while the infrastructure feature is active.

Do not assume that a single "sanity" test with one protocol covers all protocols — each protocol has different process dependencies, namespace interactions, and recovery behaviors.

### Load Override Factory-Default + Rollback at Scale

When the feature involves persistent state or operates at interface/VRF scale, generate a **dedicated test case** for `load override factory-default` followed by rollback at the feature's target scale. This is a distinct scenario from normal rollback because:

- Factory-default removes all configuration in one commit, exercising bulk-delete code paths
- Rollback after factory-default re-applies the entire configuration, exercising bulk-create code paths
- At scale, these bulk operations stress different code paths than incremental add/remove

Do not assume that normal rollback tests cover the factory-default + rollback case — the volume of changes in a single commit is fundamentally different.

### Protocol Constraint Mode Decomposition

When a feature supports multiple constraint or exclusion modes (e.g., strict/avoid/ignore for SRLG exclusion, mandatory/optional for path constraints, hard/soft for preemption), generate **dedicated test cases per mode** — not a single test with modes as variants. Each mode exercises different path computation logic and produces different behavior when the constraint cannot be satisfied:

- **Strict mode:** The constraint must be satisfied; path computation fails if it cannot.
- **Relaxed/avoid mode:** The constraint is preferred but not mandatory; an alternate path may be selected.
- **Ignore mode:** The constraint is not considered; verify the feature operates without the constraint.

Do not collapse modes into variants — each mode has distinct pass/fail criteria and exercises different code paths in the path computation engine.

### Protection Type Decomposition for MPLS-TE

When a feature affects RSVP-TE or MPLS-TE protection mechanisms, generate **dedicated test cases per protection type**:

- **Secondary LSP:** Verify the feature's behavior with pre-computed secondary (standby) LSPs.
- **Manual bypass:** Verify the feature's behavior with explicitly configured bypass tunnels.
- **Auto-bypass:** Verify the feature's behavior with dynamically computed bypass tunnels.

Each protection type has different tunnel setup, path computation, and failover behavior. Do not collapse all protection types into a single "protection" test or list them as variants.

### Interface Flapping Resilience Testing

When the feature configures state on interfaces (e.g., SRLG values, TE attributes, protocol parameters), generate a **dedicated test case for interface flapping** — rapidly toggling the interface up/down multiple times while the feature is active. Verify:

- The feature's state is correctly maintained after flapping stops.
- No stale state or resource leaks from repeated up/down transitions.
- Protocol reconvergence completes correctly after each flap.
- No core files or crashes during rapid flapping.

Do not assume that a single link-failure test covers flapping — flapping exercises different timing-dependent code paths (rapid state machine transitions, timer interactions, queued event processing).

### Next-Hop Address Type Decomposition

When a feature supports multiple next-hop address types (e.g., IPv4 vs IPv6, GUA vs link-local, labeled vs unlabeled), generate **dedicated test cases per next-hop type** — not a single test with NH types as variants. Each next-hop type exercises different:

- Address resolution logic (GUA resolved via routing table, LLA resolved via interface/update-source)
- Forwarding behavior (different encapsulation, different FIB programming)
- Capability negotiation (extended-nexthop for IPv6 NH with IPv4 NLRI)
- Policy matching (different match conditions for different NH types)

When the feature also supports multiple SAFIs (e.g., IPv4 unicast, MPLS-labeled unicast, VPNv4), generate the NH type decomposition **per SAFI** — each SAFI may handle the next-hop type differently.

### BGP Route Redistribution with Non-Standard Next-Hops

When the feature introduces non-standard next-hop types for BGP routes (e.g., IPv6 NH for IPv4 routes), generate **dedicated test cases for route redistribution** between BGP and other protocols (OSPF, ISIS, static). The redistribution path may not preserve the non-standard NH type, and the receiving protocol may not support it. Verify:

- Redistribution from BGP to IGP with non-standard NH — verify NH is translated or route is rejected
- Redistribution from IGP to BGP — verify non-standard NH can be applied via policy
- Route aggregation with mixed NH types — verify aggregate NH selection

### BGP Graceful Shutdown with Feature-Specific State

When the feature adds new BGP capabilities or route attributes, generate a **dedicated test case for BGP graceful shutdown** (GSHUT community) verifying that the feature's state is correctly handled during the shutdown sequence. The GSHUT mechanism changes route preference, which may interact with feature-specific path selection logic.

### Scale Transition During Active Operation

When the feature increases a configuration scale limit (e.g., from N to M entries), generate **dedicated test cases for transitioning between the old and new scale limits while the feature is operationally active**:

- **Low-to-high transition:** Configure at the old limit, then increase to the new limit while traffic is flowing and protection paths are active. Verify the feature correctly handles the scale increase without disrupting active sessions.
- **High-to-low transition:** Configure at the new limit, then reduce back to the old limit. Verify the feature correctly handles the scale decrease.

Do not assume that configuring at the new limit from scratch covers the transition case — the transition exercises different code paths (incremental update vs. initial setup).

### IGP Protocol Operational Commands Testing

When the feature operates within an IGP (OSPF, OSPFv3, IS-IS), generate **dedicated test cases** for each operational clear command that affects the feature's state:

- **Clear neighbor:** Verify the feature recovers correctly after clearing specific neighbors or all neighbors.
- **Clear process:** Verify the feature recovers correctly after clearing the protocol process.
- **Clear routes:** Verify the feature's routes are correctly reinstalled after clearing routes.

Each clear command exercises a different state reset path. Do not assume that HA restart tests cover clear command behavior — clear commands are user-initiated and may have different recovery semantics.

### IGP Throttle and Timer Interaction Testing

When the feature operates within an IGP that has configurable throttle timers (SPF throttle, LSA throttle, LSA generation throttle), generate **dedicated test cases** for each throttle type:

- **SPF throttle:** Verify the feature's convergence behavior with different SPF throttle values (initial, hold, max-wait).
- **LSA throttle:** Verify the feature's LSA flooding behavior with different LSA throttle values.
- **Max-age LSA handling:** Verify the feature correctly handles LSAs reaching max-age and being flushed.

These are standalone tests — each throttle type affects different aspects of protocol convergence.

### SNMP Trap Testing for Protocol State Changes

When the feature involves protocol state changes (neighbor state, interface state, adjacency formation), generate **dedicated test cases** for each SNMP trap that the protocol defines for those state changes. Do not skip SNMP traps just because the feature does not "introduce new MIBs" — existing MIBs may generate traps for the feature's state transitions.

### Dynamic External State Change Testing

When a feature's behavior depends on external state that can change independently of the DUT's configuration (e.g., RPKI ROA validity changing at the cache server, BFD session state changing due to remote peer, route-policy evaluation changing due to prefix-list update, certificate expiry), generate **dedicated test cases for each distinct external state transition** while the feature is active:

- **State transition to restrictive:** Generate a test where the external state changes to a more restrictive value (e.g., route becomes RPKI-invalid, BFD session goes down, certificate expires) while the feature is actively using the affected resource. Verify the feature reacts correctly and within expected time.
- **State transition to permissive:** Generate a test where the external state changes to a less restrictive value (e.g., route becomes RPKI-valid, BFD session recovers, new certificate is installed) while the feature has already reacted to the restrictive state. Verify the feature correctly restores the affected resource.
- **Per-configuration-combination:** Generate the above transitions for each relevant combination of the feature's configuration knobs — do not assume that testing one knob combination covers all. Each combination may have different reaction behavior to the same external state change.

Do not rely on static-state tests (where the external state is set before the feature processes it) to cover dynamic transitions — the dynamic case exercises different event-handling and convergence code paths.

### Show Command Output Format Backward Compatibility

When a feature modifies existing CLI commands or adds new configuration knobs that could affect existing show command output, generate **dedicated test cases** verifying that existing show command output format is not changed:

- **Existing show command structure:** Verify that the output format, column layout, and field ordering of existing show commands (e.g., `show bgp`, `show bgp route`, `show route`) remain unchanged after the feature is configured.
- **New fields in existing output:** If the feature adds new fields to existing show commands, verify the new fields are appended or inserted without disrupting existing field positions.
- **Backward compatibility for scripts:** Verify that automation scripts or monitoring tools that parse existing show command output would not break due to format changes.

These are standalone tests — show command format stability is a separate concern from functional correctness.


### Per-Flag/Bit Attribute Propagation Testing

When a feature propagates or re-advertises protocol TLVs or attributes between domains, levels, or areas (e.g., IS-IS inter-level propagation, BGP route reflection, OSPF inter-area), generate **dedicated test cases for each distinct flag or bit** that the feature is expected to carry, set, or clear during propagation:

- **Per-flag verification:** For each flag or bit in the propagated TLV (e.g., D flag, R flag, N flag, anycast bit, Prefix Attribute Flags), generate a dedicated test verifying the flag is correctly set/cleared/preserved during propagation.
- **Flag interaction with summarization:** If the feature summarizes multiple TLVs into one, generate a dedicated test verifying how flags from contributing TLVs are combined or resolved in the summary TLV.
- **Flag-dependent forwarding:** If a flag affects forwarding behavior (e.g., anycast bit, down bit), generate a dedicated test verifying the forwarding impact of the propagated flag.

Do not assume that a single "verify TLV content" test covers all flags — each flag may have different propagation rules and different impact on downstream consumers.

### SPF/Path-Computation Feature — IGP Operational Scenario Coverage

When a feature modifies or aligns SPF (Shortest Path First) computation, path selection, or route installation behavior, generate **dedicated test cases for each distinct IGP operational scenario** that exercises different SPF code paths:

- **Local vs. remote topology events:** Generate separate TCs for local events (metric change, link down on DUT) and remote events (metric change, link down on a remote router). Local events trigger LSP generation + SPF, while remote events trigger SPF only — these exercise different code paths.
- **Multi-level propagation:** Generate separate TCs for L1→L2 and L2→L1 route propagation, verifying the feature's behavior at each propagation direction.
- **DUT router roles:** Generate separate TCs for the DUT acting as ABR (Area Border Router), ASBR (Autonomous System Border Router), and leaf router. Each role exercises different SPF graph construction and route advertisement logic.
- **IGP feature interactions:** Generate dedicated TCs for the feature's interaction with default-originate, conditional advertisements, multi-homed routes, and route summarization — each of these modifies the SPF graph or route selection in ways that may interact with the feature.
- **Show command verification per event type:** Generate dedicated TCs verifying `show isis topology`, `show isis route`, and `show route` output after each distinct event type (local metric change, remote metric change, link up, link down).

Do not assume that testing one event type or one router role covers all SPF code paths — each combination exercises different graph construction, metric calculation, and route installation logic.

### Cross-Area/Cross-Level Transit Path Testing

When a feature operates at an ABR or ASBR that connects multiple areas or levels, generate **dedicated test cases for transit paths that cross through the backbone** between different non-backbone areas/levels:

- **Area-X → Backbone → Area-Y:** Verify the feature works correctly when the path traverses from one non-backbone area through the backbone to a different non-backbone area (e.g., IS-IS L1-area-A → L2 → L1-area-B, or OSPF Area 1 → Area 0 → Area 2).
- **Multiple ABRs on the transit path:** Verify the feature works correctly when the transit path crosses multiple ABRs.
- **Combined propagation and summarization on transit path:** If the feature supports both propagation and summarization, verify the combined behavior on the transit path (e.g., propagated in one direction, summarized in another).

Do not assume that testing single-direction propagation (L1→L2 or L2→L1) covers the full transit path — the transit case exercises different metric accumulation, flag handling, and loop prevention logic.

### Policy/Protocol Origin × IGP × Control-Plane Mode Matrix

When a feature applies across multiple policy origins (static, dynamic/auto, PCE-initiated/delegated) AND multiple IGP instances (ISIS, OSPF) AND multiple control-plane modes (local, PCEP delegation), generate **dedicated standalone test cases for each active combination** — not a single test with the other dimensions as variants. Each combination exercises a different code path for path computation, validation, and installation:

- **Static policy × each IGP:** Separate TCs for static policy with ISIS vs. OSPF.
- **Auto/dynamic policy × each IGP:** Separate TCs for auto-policy with ISIS vs. OSPF.
- **PCEP-delegated/initiated × each IGP:** Separate TCs for PCEP policies with ISIS vs. OSPF.
- **PCEP auto-policy vs. PCEP static policy:** These are distinct — PCEP delegation on a static policy vs. PCEP initiation of a dynamic policy exercise different state machines.

If the manual QA test matrix has a dedicated test per combination, the generated plan must match with standalone TCs. Do not collapse PCEP auto-policy into a variant of PCEP static policy.

### Hotpatch and Patch Installation Testing

When the feature is deployed on systems that support hotpatch or patch installation (RE patches, ME patches), generate **dedicated test cases** for patch installation scenarios:

- **Hotpatch install → verify feature → revert → verify feature:** Verify the feature works correctly after hotpatch installation and after hotpatch revert.
- **Platform variants:** If the feature is tested on both SA and CL (cluster), generate separate hotpatch tests for each platform variant.

Do not assume that upgrade/downgrade tests cover hotpatch scenarios — hotpatch exercises a different code path for binary replacement and state preservation.

### Bug Regression Testing on Related Protocols

When the epic references bugs found in a related protocol version (e.g., OSPFv2 bugs to be retested on OSPFv3, IS-IS bugs to be retested on OSPFv3), generate a **dedicated regression test case** that explicitly retests the bug scenarios on the target protocol. Reference the original bug IDs and verify the fix applies to the target protocol. Do not assume that general functional tests cover bug regression — specific bug scenarios may exercise edge cases not covered by standard tests.

---

## Test Constraints
- Use only DriveNets (DNOS) commands.
- Do not include commands that are not supported by the feature.
- If one test is insufficient, generate multiple tests.
- Each test must have no more than 15 steps.
- If the test is negative, include "Negative" in the Test Name.
- Pass Criteria must contain exactly one item per Test Step.

---

## Test Template (ALWAYS keep it)

The canonical TC template is defined in the pipeline SKILL.md (`Stage 3 → 4. TC template`). The template below must stay in sync with it.

### **TC-NNN: Coverage for <INSERT User Story ID and Summary or Specific Case from 'TP Checklist'>**
1. **Test Name:** <INSERT Test Name>
2. **Test Description:** <INSERT Test Description in few sentences>
3. **Preconditions:** <INSERT required setup, topology, services, or prior state before step 1>
4. **Test Steps:** <INSERT Test Steps in Numbered List (1. 2. 3. ...)>
5. **Pass Criteria:** <INSERT Pass Criteria in Numbered List (1. 2. 3. ...)>
6. **Variants:** <INSERT Variants in Bulleted List>
    - Keep variants light; only small modifications or extensions of the same test.
7. **Automation Reference:** <INSERT test_file.py::test_function_name if available, otherwise "None">
