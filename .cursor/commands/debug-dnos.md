 ---
description: DNOS bug investigation and verification (MCP-backed)
---
# /debug-dnos - MCP Router

Use `user-debug-dnos-mcp` for symptom classification, known-bug matching, trace collection, evidence handoff, and Jira verification comments.

## Native MCP Invocation Contract

- First choice is always native MCP: `CallMcpTool(server="project-0-drivenets-topology-studio-user-debug-dnos-mcp", toolName="<tool>", arguments=...)`.
- Do not run debug scripts or `~/.cursor/tools/mcp_cli.py` directly unless native MCP returns `Not connected` / `Tool not found`.
- If native MCP is stale, tell the user to reload Cursor to rebind MCP, then use the CLI bridge only as a temporary fallback.
- Call one primary debug-dnos MCP tool per user intent. Follow `suggested_next_call` for cross-MCP handoff instead of fan-out.

## Routing

| User intent | MCP tool | Notes |
|---|---|---|
| investigate / diagnose | `debug_diagnose_symptom` | Returns hypothesis table + next call |
| evidence plan | `debug_evidence_plan` | Builds show, trace, packet, known-bug, and Jira proof plan |
| isolate/minimize repro steps | `debug_repro_minimizer` | Emits the smallest trigger recipe, reset path, assertions, trace filters, and negative controls; it does not execute mutating steps |
| show bundle | `debug_show_bundle` | Runs feature-aware show bundle through dnos-config |
| core crash / SIGABRT / core dump | `debug_core_analyze` | Locates routing-engine core tar, decodes `.lz4.gz`, runs GDB `bt`, and maps traces to a reproducible trigger |
| config history / rollback diff | `debug_config_history` | Uses `show config compare rollback X`, `show config compare rollback X rollback Y`, and `show rollback X` |
| trace bundle | `debug_trace_bundle` | Timestamp-centered trace bundle with standard filters |
| trace grep | `debug_trace_grep` | Uses dnos-config `dnos_run_show_commands` |
| known bug check | `debug_known_bugs_match` | Matches local known bug catalog |
| bug description in chat | `debug_bug_description` | Unified topology + timestamped raw-output bug description for chat |
| Jira verification comment | `debug_jira_verify_format` | Raw Jira wiki markup |
| collect evidence | `debug_collect_evidence` | Saves compact handoff |
| resume | `debug_session_resume` | Loads latest debug handoff |
| capture feature knowledge (after `/search-company-knowledge`) | `debug_knowledge_capture` | Parses Confluence/Jira pages into the shared cache at `~/.cursor/knowledge_base/<feature_id>/`; live-validates show commands against a primary device |
| read expected behavior | `debug_knowledge_lookup` | Returns cached expected behavior (manifest/sources/config_paths/show_commands/xraycli_paths/trace_patterns/interactions/bugs/expected_behavior_md) |
| live-revalidate cached commands | `debug_knowledge_validate` | Re-runs every cached show command via `dnos_run_show_commands` and updates LIVE_VALIDATED / LIVE_REJECTED / LIVE_EMPTY |
| mark feature stale | `debug_knowledge_refresh` | Forces the next lookup to trigger fresh capture |
| grade observed vs expected | `debug_knowledge_compare` | Per-bucket scorecard (match/miss/anti/unknown) of show_text + trace_text + xray_text against the cache |

## Feature-Knowledge Auto-Behavior

The four diagnose / evidence-plan / known-bugs / compare tools now auto-consult
the shared knowledge cache. When a symptom maps to a cached feature_id:

- `debug_diagnose_symptom` returns `verdict="EXPECTED_BEHAVIOR_KNOWN"` and
  suggests `debug_knowledge_compare` as the next call.
- `debug_evidence_plan` inserts a `feature_knowledge_expected_behavior` proof
  as proof #0 (cached shows + traces + xraycli surfaces).
- `debug_known_bugs_match` merges cached `bugs.json` entries into the match
  set using token-overlap.

After any `/search-company-knowledge` run that produces feature-level
documentation, follow `feature-knowledge-auto-capture.mdc`: call
`debug_knowledge_capture` with the parsed payload AND `live_validate=true` so
the cache reflects live device state.

## Bug Description One-Shot Evidence Contract

When the user asks for a bug description, do **not** render from memory,
summaries, or partial payloads. First force the raw evidence path through
native MCP tools, then call `debug_bug_description` only after all mandatory
blocks are populated.

Required call order for EVPN/VPLS/VPWS service bugs:

1. `debug_show_bundle` with `service_name`, `ac_interfaces`, and
   `irb_interfaces` to fetch service config/state plus AC/IRB config/state.
2. `dnos_run_show_commands` via dnos-config for the exact before and after
   service assertions. For MAC/MAC-IP/ARP bugs this must include, before and
   after the trigger:
   - `show evpn mac-table instance <service> | no-more`
   - `show evpn mac-ip-table instance <service> | no-more`
   - `show arp interface <irb> | no-more`
   - `show dnos-internal routing fib-manager database evpn evi-id <evi> local-mac mac <mac> | no-more`
   - `show dnos-internal routing fib-manager database neighbor address <ip> | no-more`
3. Execute mutating operational triggers only through the owning MCP tool
   (`dnos_operational_clear` for EVPN clear commands) with explicit
   `execute=true` and `confirm=true`.
4. `debug_trace_grep` for every process/container needed by the proof. For
   EVPN MAC-IP suppression, always include `fibmgrd` and CLI clear evidence;
   check `bgpd` when RT/PW advertisement could be relevant. If a checked trace
   has no output, state that explicitly.
5. `debug_bug_description` only after the payload contains the complete
   topology, before-state, operations, after-state, traces, expected result,
   actual result, general repro prerequisites, and minimal repro steps. The
   tool defaults to the full Jira-grade markdown in chat and also saves the
   same text to `artifact_path`. Use `chat_compact=true` only when the operator
   explicitly asks for a compact index instead of the full description.

For bug descriptions, the rendered proof must lead with the bug path, not a
prose summary: topology -> raw service/interface config -> **before raw tables**
-> trigger raw output -> **after raw tables** -> traces -> expected/actual ->
general repro. The before/after raw tables are the reader's proof and must be
printed in full on the first response. Major sections must be visually separated
with `---` so the dev can distinguish topology, environment, before state,
operation, after state, traces, expected/actual, repro, and verdict at a glance.

## Hard Rules

- Ticket-style bug descriptions must begin with a topology and service summary before root cause or proof. Include the participating devices, loopbacks/peers, EVI/RD/RT/site IDs, AC/IRB interfaces, PW status, and the raw `show config` / `show evpn instance ... detail` snippets needed for a reader to understand the setup without prior lab context.
- When the user asks for “bug description”, “give me the bug description”, “description with outputs and steps”, or similar, execute the Bug Description One-Shot Evidence Contract above, then call `debug_bug_description` and render its `summary_markdown`. Do not freehand a compressed prose-only answer and do not call the renderer before the raw dnos-config/debug evidence has been fetched.
- `debug_bug_description` output must follow the SW-266543-style chronology by default: topology/service context, a 1-2 sentence issue summary, baseline raw outputs, operational command input/output with timestamp, post-operation raw outputs, traces/shell DB evidence, then 1-2 sentence `Expected Results`, 1-2 sentence `Actual Results`, general `Minimal Steps To Reproduce`, and final verdict at the bottom.
- Environment Details must include `ssh dnroot@<Serial Number>` above the raw `show system` table for every non-empty serial extracted from the table.
- `debug_bug_description` input must follow the unified raw-evidence schema:
  - `topology`: devices, roles, loopbacks/peers, AC/IRB interfaces, EVI/RD/RT/site IDs, PW status.
  - `before_state` and `after_state`: raw baseline/post-trigger snapshots with `command_outputs[]` for `show config network-services evpn instance <service>`, `show evpn instance <service> detail`, `show config interfaces <AC/IRB>`, and `show interfaces <AC/IRB>`. These are mandatory for service/interface bugs; missing snapshots must render as warnings.
  - `summary`: two or three sentences describing the observed bug, expected behavior, actual behavior, and impact.
  - `operations[]`: every mutating or stimulus command between before/after snapshots, including `clear`, `request`, config mutations, rollback operations, pings used as triggers, and traffic starts. Each operation must include `target`, `timestamp`, exact `command` or `raw_input`, `raw_output`, `expected`, `observed`, and `verdict`.
  - `steps[]`: each step has `action`, `explanation` or `traffic_flow`, `expected`, `observed`, `verdict`, and `evidence[]`.
  - each `evidence[]` entry has `target`, `timestamp`, exact `raw_input` or `command`, `raw_output`, `expected`, `observed`, and `verdict`.
  - when one proof has multiple commands, prefer `command_outputs[]` entries (`command` + `raw_output`) so the rendered bug description prints each command immediately followed by its matching output. Do not put all commands in one block and all outputs in a second combined block.
  - optional `traces[]` and `shell_db_tables[]` use the same timestamped raw-evidence fields.
  - optional `expected_results[]`, `actual_results[]`, `repro_prerequisites[]`, and `minimal_repro_steps[]` override the derived bottom sections. Expected and actual results are rendered as 1-2 sentences max. Repro steps are rendered as general steps with topology/traffic prerequisites, not device-specific lab transcript commands.
  - if a timestamp/input/output is missing, say so explicitly; never hide the gap.
- Raw show command input and output are Jira-grade evidence; summaries alone are not enough. Every proof block must show the capture timestamp inside the same fenced device block, then the exact device prompt/command line immediately above the matching raw output. The timestamp must not live only in bullet metadata outside the block.
- For long bug descriptions, still return the full rendered description in chat.
  `debug_bug_description` writes the same full markdown to `artifact_path` for
  Jira copy/paste. `chat_compact=true` is an explicit opt-in escape hatch only.
  `jira_fast` / `fast_render=true` remain available to compact repeated metadata
  inside raw evidence while keeping the full sectioned description.
- Every raw show bundle used for Jira proof must include a device-local timestamp captured in the same bundle, preferably immediately before the evidence commands (`show system | include "System Name|Version"` plus a timestamp-bearing command output such as `show config compare | no-more`, or an explicit timestamp command when supported). If a past run missed per-command timestamps, state the gap clearly and use only timestamps embedded in the raw device output/traces.
- Prefer `debug_evidence_plan` before ad-hoc trace/show collection for new symptoms.
- When the user asks to isolate a bug into minimum repro steps, call `debug_repro_minimizer` after at least one good and one bad assertion set is known. A valid minimized repro must state the passing baseline, reset path, one smallest trigger, post-trigger pass/fail assertions, trace fingerprints, and negative controls for candidate triggers that did not reproduce.
- `debug_repro_minimizer` is a planner, not an executor. If it recommends an operational clear, run that clear only through `dnos_operational_clear` with `execute=true` and `confirm=true`; do not hide mutation inside the minimizer.
- EVPN MAC-IP suppression pattern proven on 2026-05-14: if PE-1 has a healthy VPLS-PW MAC-IP row, `clear evpn mac-table instance EVPN_SI_VPLS_1 mac 00:fe:11:00:40:fe` is the smallest trigger that removes the MAC-IP row while MAC table, ARP, fib-manager `neighbor_keys_size=1`, and L2-neighbor remain reachable. Negative controls: RR-SA-2 clears alone did not reproduce; broad PE-1 `clear evpn mac-table` plus IRB ping resets to healthy.
- For EVPN/VPLS/VPWS symptoms, collect service snapshot layers before and after the trigger. Pass `service_name`, `ac_interfaces`, and `irb_interfaces` to `debug_show_bundle` so it automatically fetches `show config network-services evpn instance <service>`, `show evpn instance <service> detail`, `show config interfaces <AC/IRB>`, `show interfaces <AC/IRB>`, internal local/remote MAC DB, `show dnos-internal routing fib-manager database global-mac-neigh` (prints `L2EvpnLocalMacToNeighbor` / `m_EvpnDB`), L2-neighbor DB, and L2-maintained-neighbors.
- For IPv6 NDP / EVPN MAC-IP punt symptoms, collect CPRL before and after traffic: `show system cprl`, `show config system cprl`, and `show system logging system-events CPRL_RATE_LIMIT_CROSSED`. Track the `NDP` row RX / Policer Drops / Total Drops. If NDP drops increase during the repro window, mark the run CPRL-contaminated before claiming an EVPN punt bug.
- For IPv6 NDP / EVPN MAC-IP punt symptoms, include neighbor-manager evidence as a separate layer: `show ndp vrf <vrf> ipv6-address <ip> | no-more`, `show evpn ndp-table instance <service> ip <ip>`, `show dnos-internal routing fib-manager database evpn evi-id <evi_id> l2-neighbor ip <ip> | no-more`, `show dnos-internal routing fib-manager database neighbor address <ip> | no-more`, `show file traces routing_engine/neighbour_manager_oob_ns | include <HH:MM> | include <ip>`, `show file traces routing_engine/neighbour_manager_inband_ns | include <HH:MM> | include <ip>`, and `fibmgrd` traces. If fibmgr logs `Ignoring update from NEIGHBOUR_MANAGER ... - not permanent`, report that as generic dynamic NDP behavior and continue proving whether the expected `wb_agent` proxy-NDP `UPDATE_RAW` path reached fibmgr. Do not use the hidden source-only `show fib-manager fpm queues neighbor-manager` command from fibmgr vty; it is not exposed in PE-1 DNOS CLI.
- For the EVPN-SI IPv6 VPLS-PW NA repro, prove the packet contract before judging DNOS behavior: PE-1 IRB ping is only the Neighbor Solicitation trigger, and the decisive packet is a fake RR-SA-2 service-AC host solicited Neighbor Advertisement crossing the PW back to PE-1 (`type=136`, `S=1/O=1/R=0`, unicast to the NS requester, Target Link-Layer Address option present). Unsolicited NA (`S=0`, all-nodes multicast) is a separate negative/control case and must not be treated as proof of PW-side MAC-IP/L2-neighbor learning.
- Validated CPRL operational/config syntax: `clear system cprl counters [ncp <id>]`; `system cprl ndp rate <pps>` and `system cprl ndp burst <packets>`. Use `dnos_atomic_commit` dry-run first for any rate/burst increase and require explicit user approval before commit.
- Do not remove/re-add an EVPN service to refresh state while CPRL NDP drops are still increasing. First clear CPRL counters or temporarily raise NDP rate/burst, rerun the low-rate traffic, and prove drops remain unchanged.
- For crash-class symptoms, collect core evidence with `debug_core_analyze` before declaring the trigger understood. A `.lz4.gz` core inside the tar must be gunzipped to `.lz4`, then decoded with `unlz4`, before GDB can read it.
- For config-history checks, use rollback-aware show commands: `show config compare rollback <id>`, `show config compare rollback <id> rollback <id>`, and `show rollback <id>`. Do not use invalid `show config rollback <id>`.
- Do not create or run 10 Mbps or higher Spirent streams from `/debug-dnos` unless the current user message explicitly asks for that rate.
- Always validate unfamiliar DNOS syntax before running show/config commands.
- Known bug matches should be surfaced early to avoid wasting lab time.
- When `/debug-dnos create bug topology` (or `/TOPOLOGY bug SW-XXXXX`) generates a bug topology and the agent has any route hint or VRF context, the saved canvas now auto-emits a layered packet/frame chip attached to the link entering `failure_device`. The chip exposes L2/VLAN/MPLS/L3/L4/Payload rows with empty rows pre-collapsed, a 2-3 word summary pill, and an auto direction arrow pointing toward the failure device unless explicit route source/destination device hints say otherwise. Operators can toggle layers, rename fields, stretch width, flip direction, or delete it via the in-canvas packet popup. See `topology/DEVELOPMENT_GUIDELINES.md` -> "Layered Packet/Frame Object" for the schema.
