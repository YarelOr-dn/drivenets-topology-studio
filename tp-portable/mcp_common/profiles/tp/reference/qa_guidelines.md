# QA Guidelines for Test Plan Generation

Test Template:
1. **Test Name:** <INSERT Test Name>
2. **Test Description:** <INSERT Test Description in few sentences>
3. **Test Steps:** <INSERT Test Steps in Numbered List (1. 2. 3. ...)>
4. **Pass Criteria:** <INSERT Pass Criteria in Numbered List (1. 2. 3. ...)>
5. **Variants:** <INSERT Variants in Bulleted List>

CRITICAL DNOS SYNTAX RULES:
- Use ONLY Drivenets DNOS CLI syntax - NO Cisco, Juniper, Nokia, or other vendor syntax!
- Use 2-space indentation per level (NOT tabs)
- Interfaces are FLAT hierarchy (sub-interfaces are siblings)
- All config blocks end with "!" at content indentation level
- NLRI strings MUST be quoted with double quotes ("")
- FlowSpec enable: "flowspec enabled" under interface
- MPLS enable: "mpls enabled" under interface
- VRF config: "network-services vrf instance <NAME>"
- BGP config: "protocols bgp <ASN>"

ADMIN-STATE CONTEXT RULES (CRITICAL):
- "admin-state disabled/enabled" is valid on: interfaces, BGP neighbors, protocols (ISIS, LDP, RSVP)
- "admin-state disabled" is NOT valid under BGP address-family blocks!
- BGP address-families use "admin-state enabled" to activate; to deactivate, use "no address-family <name>"
- DNOS address-family name for Segment Routing TE is "ipv4-sr-te" / "ipv6-sr-te" (NOT "sre" or "sr-te")

NETCONF/gNMI TEST RULES (CRITICAL):
- NETCONF: SSH port 830, uses candidate datastore, edit-config + commit workflow, all operations safe
- NETCONF edit-config replace is SUBTREE-SCOPED (safe) — unlike gNMI replace
- gNMI: gRPC port 50051, Set Update and Set Delete are SAFE, Set Replace is DANGEROUS (wipes entire config)
- gNMI Set Replace runs LOFD (Load Override Factory Default) — NEVER generate tests using it
- gNMI Set requires TLS — without TLS, gNMI is read-only only
- Cannot mix DN YANG (/drivenets-top) and OpenConfig (/interfaces, /network-instances) in one gNMI SetRequest
- Use correct YANG path: /drivenets-top/network-services/vrfs/vrf[vrf-name=X]/protocols/bgp[as-number=Y]
- WRONG path: /drivenets-top/instances/vrfs/vrf (does NOT exist)
- SNMP Set is NOT production-ready (SW-209493) — only test GET, Walk, Traps

DNOS Show Commands (use EXACT syntax):
- show bgp ipv4 flowspec-vpn summary
- show bgp ipv4 flowspec-vpn neighbors <IP> received-routes
- show bgp instance vrf <VRF> ipv4 flowspec nlri "<NLRI>"
- show flowspec ncp
- show flowspec-local-policies counters
- clear flowspec counters

NETCONF/gNMI Show Commands:
- show system netconf / show system netconf sessions
- show system grpc / show system grpc sessions / show system grpc subscriptions
- show config system netconf / show config system grpc

General Guidelines:
- For each Test Step, include an equivalent item in the Pass Criteria section (no more or less than the number of Test Steps!). Always write a pass criteria for each test step.
- If the generated test is a negative scenario, make sure to include 'Negative' in the 'Test Name'.
- Keep Variants generation very light. Variants suggestions should modify or extend the current test slightly (do NOT produce a separate one):
    - (IPv4 - IPv6, default VRF - non-default VRF, inband - out-of-band, different interface types [physical, sub-physical, bundle, sub-bundle, loopback]).
    - OSPFv2 is a different protocol than OSPFv3. Do NOT suggest OSPFv3 variant when OSPFv2 is used (same thing for the other way around)! Whenever OSPF is referenced, default to OSPFv2.
    - In DNOS, the non-default VRF is supported only for BGP, EVPN, static and VRRP protocols. OSPF does not support non-default VRF.

---

## User story test additional instructions

LEARN FROM TICKET: Use CLI syntax, commands, and parameters from the EPIC description and User Stories.
Use DNOS RST documentation and epic-mentioned syntax for validation.

If a specific scenario is requested, make sure to cover all items described in the scenario.
If one test is not enough for a good coverage, generate multiple tests (Test 1, Test 2, etc.).

============================================================
MANDATORY OUTPUT FORMAT: Confluence Wiki Markup (ADF/Jira)
============================================================

Your output MUST follow this EXACT structure (adapt commands to the feature):

```
h1. +*_Test Steps:_*+

* NOTE: all ipv4 tests should be tested with IPv6 as well (when applicable)

h2. Prerequisites (All Tests)

h3. Topology Requirements
* DUT connected to external peer(s)
* IXIA traffic generator connected (if traffic tests)
* Relevant protocol sessions pre-established

h3. DUT Configuration Requirements
* Use commands from EPIC/User Stories - e.g. {{protocols bgp 65000}} or feature-specific config

----

h2. Test 1: [Descriptive Test Name]

*Objective:* [ONE sentence describing what this test validates]

||*Step*||*Action*||*Command*||*Expected Result*||
|1|Configure feature|{{<use syntax from EPIC>}}|Config accepted|
|2|Verify state|{{show <command from EPIC/RST>}}|Expected output|
|...|...|{{...}}|...|

----
```

============================================================
CRITICAL FORMAT RULES (MUST FOLLOW):
============================================================

1. TABLE FORMAT MANDATORY:
   - ALWAYS use: ||*Step*||*Action*||*Command*||*Expected Result*||
   - Each row: |N|action|{{command}}|expected|
   - Commands MUST be wrapped in {{double braces}}

2. STRUCTURE:
   - h1. +*_Test Steps:_*+ = Main header
   - h2. Prerequisites = Prerequisites section
   - h3. = Sub-sections (Topology, DUT Config)
   - h2. Test N: = Each test section
   - ---- = Horizontal separator between tests

3. REQUIRED ELEMENTS PER TEST:
   - *Objective:* line (bold, one sentence)
   - 4-column table with numbered steps
   - Verification steps using DNOS show commands from EPIC/RST

4. COMMAND FORMATTING:
   - Use DNOS syntax from EPIC description, User Stories, and RST docs
   - NO backticks - use {{double braces}} only

5. CATEGORIES DETERMINE COMPLEXITY:
   - Basic Functionality: 3-5 steps, simpler
   - Advanced Functionality: 7-10 steps, prerequisites, multiple tests
   - Scale/Stress: Include load parameters, counters
   - HA: Include process restart/failover steps

6. IPv6 COVERAGE:
   - For Advanced/Scale/HA: Add "* NOTE: all ipv4 tests should be tested with IPv6 as well"
   - OR create separate Test N+1 for IPv6 variant (when feature supports IPv6)

7. COUNTER VERIFICATION:
   - Include counter check step when feature has counters
   - Use show commands from EPIC or DNOS documentation

---

## CLI test additional instructions

For CLI specific tests, include NETCONF and gNMI variants where applicable:

NETCONF variant rules:
- Use SSH port 830, candidate datastore, edit-config + commit workflow
- Use correct DN YANG path: /drivenets-top/network-services/vrfs/vrf[vrf-name=X]/protocols/...
- Verify via get-config AND via CLI show commands (CLI parity check)
- Include session setup (connect, hello exchange) and cleanup

gNMI variant rules:
- Use gRPC port 50051, gnmic or pygnmi client
- ONLY use Set Update and Set Delete for write operations
- NEVER use gNMI Set Replace (it wipes ENTIRE device config via LOFD — by design)
- gNMI Set requires TLS — if no TLS, mark write tests as SKIP (not FAIL)
- Without TLS, gNMI is read-only (Get and Subscribe only)
- Cannot mix DN and OpenConfig YANG trees in the same SetRequest
- gNMI has no candidate datastore — commits are immediate
- gNMI has no rollback — use CLI 'rollback <N>' for recovery

SNMP variant rules (if applicable):
- ONLY test SNMP GET, Walk, and Traps — SNMP Set is NOT production-ready (SW-209493)
- Not all features have SNMP MIBs (e.g., no FlowSpec MIB exists)
- Use correct community string and VRF context

For CLI specific tests, do not include Interoperability tests.

---

## Run #1 completeness (scenario coverage + format defaults)

Before declaring a `/TP` run complete:

1. **Stage 1e** — build `scenario_inventory.json` via `_tp_scenario_extract.py`.
2. Every TC carries **`covers_scenarios[]`** mapping to inventory ids (or waived).
3. **Readable TC IDs** — `TC-<FEAT>-<CAT>-<slug>` (see `taxonomy.md`).
4. **Per-category Prerequisites** — numbered build+verify block before each category.
5. **Negative category** — when HLD Group G / RFC-7606 negatives exist, use dedicated
   **Negative BGP & Malformation** category (not buried in Advanced).
6. Post-write gates (all must PASS):
   - `_tp_scenario_coverage_gate.py`
   - `_tp_must_coverage_gate.py`
   - `_tp_parity_gate.py` (check 8 = scenario coverage closed)
   - `tp_validate_plan` (MCP; scenario_coverage WARN-first)
7. Self-check: `_tp_self_check.py --epic <EPIC>` after artifact write.
