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

---

## Category Coverage Requirements

The TP Checklist Guide (Confluence page ID `3934912829`) defines 85 test categories. Every generated test plan must systematically walk through them as described below.

### Always Required Categories

The following categories apply to **every feature**. Generate at least one test case (or explicit variant) for each. If a category is genuinely not applicable, include a one-line justification (e.g., "Sanitizer: N/A — deferred to end-of-cycle testing per team agreement"). **Do not silently skip any of these.**

| # | Category |
|---|----------|
| 2 | Sanity |
| 3 | CLI (rollback, load override, commit variants, help lines, tab completion, no-command, show config) |
| 4 | Negative Testing |
| 6 | System Resources Exhaustion |
| 10 | Error Handling |
| 17 | High Availability |
| 24 | Memory & CPU Footprint |
| 25 | Scale |
| 27 | Load + Stress |
| 28 | Upgrade / Downgrade |
| 29 | Input Validations |
| 30 | Defaults |
| 34 | Documentation (RST verification) |
| 42 | CLI — Show Commands (all permutations, pipes, monitor interval) |
| 44 | Setup Integrity |
| 50 | Logs Monitoring |
| 52 | Feature After Delete + Rollback |
| 57 | Tech-Support |
| 75 | Sanitizer |

### Conditionally Required Categories

Evaluate each of the following against the feature under test. For every category whose trigger condition is met, generate at least one dedicated test case. For categories that are not applicable, include a one-line justification in a "Skipped Categories" section at the end of the test plan.

Key conditional categories (non-exhaustive — see the full checklist guide for all 85):

| # | Category | Trigger Condition |
|---|----------|-------------------|
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

### Protocol-Specific Data-Plane and Forwarding Mechanics

For routing/forwarding features, generate dedicated test cases for each distinct data-plane behavior the feature interacts with. Do not assume a single functional test covers all forwarding modes. Specifically:

- **ECMP:** If the feature affects path computation or nexthop installation, generate a dedicated ECMP test verifying behavior when multiple equal-cost paths exist.
- **Encapsulation modes:** If the feature involves segment routing (SR-MPLS or SRv6), generate tests for each relevant encapsulation mode (e.g., H.Insert, H.Insert.RED, H.Encaps, H.Encaps.RED). Do not assume one mode covers all.
- **SID/label types:** If the feature involves SIDs or labels, generate tests covering each distinct SID type the feature interacts with (e.g., END, END.X, END.DX4, END.DX6, END.DT4, END.DT6 for SRv6; prefix-SID, adjacency-SID for SR-MPLS).
- **Heterogeneous configurations:** If nodes in the topology can have different configurations for the same feature parameter (e.g., different uSID block sizes, different locator lengths, different algorithm definitions), generate a test with heterogeneous values across nodes.
- **Summarization/aggregation interaction:** If the feature operates on prefixes that can be summarized or aggregated, generate a test verifying behavior with summarized prefixes.
- **Multi-topology (MT) vs. multi-instance:** These are distinct concepts. Multi-topology uses different topologies within the same ISIS instance (via MT TLVs). Multi-instance uses separate ISIS instances. If both are relevant, generate separate tests for each — do not treat them as interchangeable.


---

*Truncated excerpt. See cheetah path in test_plan_requirements_pointer.md for the full document.*
