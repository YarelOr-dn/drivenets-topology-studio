# Topology Creator - Development Guidelines
# ==========================================
# These guidelines document the codebase patterns and rules for development.
# Agents MUST read this file before making changes and UPDATE it after fixes.

## /TEST -> /XRAY -> /debug-dnos Packet-Proof Contract -- 2026-06-21

Packet proof is now a first-class TEST/debug evidence path in
`/home/dn/mcp_common/command_profiles.py`:

- XRAY tools share `_xray_filter_contract(...)` and return `capture_contract`
  / `xray_evidence` envelopes with plane, capture point, BPF/display filters,
  expected fields, pcap path/size, packet count, and verdict.
- `xray_arrival_compare` decodes pcaps with bounded `tshark` output and returns
  `ARRIVAL_MATCH`, `ARRIVAL_MISMATCH`, `ARRIVAL_INCONCLUSIVE`,
  `NO_MATCHING_PACKETS`, or `ANALYZE_FAILED`; missing/empty pcaps never PASS.
- `/TEST` recipes can set `evidence_contract.packet_capture_required=true`.
  Compile emits `xray_capture_plan -> xray_verify_spirent_arrival ->
  xray_capture_cp/dp -> xray_arrival_compare` when expected fields exist. The
  XRAY phases are timing-sensitive and excluded from parallel read-only batches.
- After ambiguous `spirent_loss_verify` results, `test_run_gated` escalates to
  the same XRAY packet-proof chain before verdict finalization when packet proof
  is enabled. `packet_proof_chain_enabled=false` remains the rollback switch.
- SW-265293 recipes now require packet proof and strict RT-2/mobility surfaces:
  internal route-type 2 detail, `Number of moved events`, fib-manager per-MAC
  origin, and explicit rejection of empty `mobility-history` as a pass gate.
- `debug_evidence_plan`, `debug_repro_minimizer`, and
  `debug_bug_description` understand packet captures, XRAY analysis, and arrival
  compare sections, so Jira-grade bug descriptions can include pcap artifacts.

## SW-194912 VPLS-PW ARP/NDP/Proxy-ARP Contract -- 2026-06-23

Jira `SW-194912` ("ARP/NDP/ISIS/Proxy-ARP with VPLS PWs") is now captured in
the shared feature cache
`~/.cursor/knowledge_base/sw194912_vpls_pw_arp_ndp_proxy_arp_irb/` and the TEST
catalog recipe
`/home/dn/SCALER/TEST/catalog/TEST_SW-194912_TC-PW-ARP-NDP-IRB-DP-ROUTING-01_001/recipe.json`.

Behavior contract:
- **No IRB:** ARP/NDP requests and responses arriving from a VPLS PW are
  flood/forward-only to local ACs. They must not create Routing ARP/NDP state,
  EVPN MAC-IP state, or generated proxy replies.
- **IRB present:** PW-side ARP/NDP is still flooded/forwarded to ACs and is
  also punted to Routing. In-subnet MAC/IP entries must appear in Routing
  ARP/NDP and EVPN MAC-IP tables.
- **Direction guard:** Proxy ARP/NDP may answer AC-side requests when the PW
  host is known, but must never send generated proxy replies toward the VPLS
  PW. Only actual host responses may go toward the PW.
- TEST proof must span packet/traffic, DP classification, proxy-reply TX
  suppression, Routing ARP/NDP, EVPN ARP/NDP/MAC-IP, fib-manager internal DB
  plus `routing_engine/fibmgrd_traces`, `routing_engine/rib-manager_traces`,
  forwarding-table ownership, BGP RT-2 non-advertisement for PW-source MAC-IP,
  and CPRL contamination checks.

PE-1 is currently a known lab blocker for this recipe. Before running the recipe
with PE-1 as the IRB PE, recover/redeploy PE-1. The corrected power method is
console-first PDU recycle: attach `console-d16.dev.drivenets.net` port `1`
first, then drive `pdu-d15-1` outlet `44` through `zkeiserman-dev` using the
interactive PDU shell (`dev outlet 1 44 off|on|get status`). Do not use direct
SSH exec or passive `:2222` polling as the primary recovery method; those miss
the GRUB/host recovery window.

## /SPIRENT MCP Umbrella + Legacy Alias Contract -- 2026-06-21

`/home/dn/mcp_common/command_profiles.py` now exposes primary umbrella tools for
new manual `/SPIRENT` routing while keeping every legacy tool callable for
`/TEST`, saved recipes, and operator muscle memory:

- Preferred umbrellas: `spirent_session`, `spirent_inspect`, `spirent_stream`,
  `spirent_traffic`, `spirent_device`, `spirent_protocol`, `spirent_bgp`,
  `spirent_routes`, and `spirent_dut`.
- Frozen TEST names remain first-class and must not be renamed:
  `spirent_ensure_ready`, `spirent_prune_test_scope`, `spirent_create_stream`,
  `spirent_start`, `spirent_stats_poll`, `spirent_loss_verify`,
  `spirent_create_device`, `spirent_protocol_start`,
  `spirent_create_modifier_stream`, `spirent_scale_stream_plan`, and
  `spirent_set_stream_active`.
- Umbrellas dispatch losslessly to existing handlers; they must preserve
  verdicts, `command_preview`, `suggested_next_call`, `effective_command`, and
  `execute`/`confirm` semantics. `spirent_loss_verify` remains the authoritative
  no-loss verdict; `spirent_stats_poll` remains supporting TX/tagged-traffic
  evidence only.
- Every added MCP profile tool needs a registered `HANDLERS` entry and a JSON
  descriptor under the bound Cursor MCP tools directory, or
  `test_contract.py` descriptor parity fails. Mutating/destructive umbrellas
  must also be listed in the contract test's execute/confirm sets.
- `SPIRENT_USE_DAEMON=1` is the opt-in speed path. When the warm
  `spirent_daemon.py` runner is healthy, MCP can route Spirent CLI calls through
  it; otherwise it automatically falls back to the existing subprocess path.
- `spirent_l2_discover` no longer shells to the stale missing `l2-discover`
  subcommand; it collects read-only DNOS L2/config evidence and suggests
  `dnos_dnaas_spirent_preflight` for exact frame recipes.

## /debug-dnos Routing VTYSH/Zebra Proof Contract -- 2026-06-21

When a routing owner asks for "zebra" proof, do not substitute DNOS CLI
`show file ... zebra` logs or `cmd search zebra`. The intended evidence path is:
DNOS CLI -> `run start shell` into the routing-engine shell -> `vtysh -c
"show ..."` FRR/zebra commands.

Implementation:
- `dnos-config` exposes `dnos_routing_vtysh_exec`, which enters the
  routing-engine shell, opens one interactive `vtysh` session, answers the
  password prompt when present, and runs only read-only `show ...` commands
  inside that session. Compatibility inputs in the old `vtysh -c "show ..."`
  form are normalized to the inner show command. Config mode, shell chaining,
  redirection, packet capture, process control, and mutating commands are
  blocked before SSH. `% Unknown command` / `% Ambiguous command` output is
  treated as failure even when FRR returns success.
- `/debug-dnos` exposes `debug_routing_vtysh_bundle`, combining routing-engine
  vtysh/FRR/zebra views with DNOS-side BGP, fib-manager, rib-manager traces,
  fibmgrd traces, and bgpd traces for the same `mac`/`ip`/`evi_id`/RD/timestamp
  filters. The default profile is fast and skips broad route-table dumps; set
  `include_routing_table=true` or `vtysh_profile="full"` only when route-table
  evidence is specifically needed.
- `debug_show_bundle` now adds targeted fib-manager backing-state checks and
  `routing_engine/rib-manager_traces` when EVPN/VPLS/VPWS symptoms include
  MAC/IP/EVI details.
- `/TEST` vtysh-parity phases now route through `debug_routing_vtysh_bundle`
  instead of using DNOS CLI internal show commands as a proxy for backend vtysh.

## /debug-dnos Bug Description Readability Contract -- 2026-06-21

`debug_bug_description` in `/home/dn/mcp_common/command_profiles.py` now returns
the full Jira-grade bug description in chat by default, not a compact summary.
The same full markdown is still saved to `artifact_path` for Jira copy/paste.

Renderer rules:
- The title is followed by visually separated proof sections; every major
  observable block is split with `---` so developers can quickly distinguish
  topology, environment, issue summary, before state, operation, after state,
  traces/shell DB evidence, expected/actual results, reproduction steps, and
  verdict.
- `Environment Details` extracts non-empty Serial Number values from the
  `show system` component table and prints `ssh dnroot@<serial>` above the raw
  `show system` block.
- `chat_compact=true` is opt-in only. Use it only when the operator explicitly
  asks for a compact index; normal bug-description delivery is full inline
  `summary_markdown` after the MCP call.

## /UPGRADE Auto-Selects Delete+Deploy on Branch-Lineage Change -- 2026-06-18

`routes.upgrade._run_device_upgrade` auto-escalation previously only forced
`delete_deploy` on a major-version jump (v25->v26) or GI/RECOVERY state. A jump
within the SAME train but across branch lineages (e.g. a private feature build
`26.2.0.9_priv.usirota_evpn_vpls_irb_9` -> mainline `26.2.0.543_dev.dev_v26_2_1402`)
wrongly stayed `normal`. Private branches fork off an older base with a different
package/stack set, so an in-DNOS `target-stack load + install` across lineages
mixes incompatible packages (partial install / DN_RECOVERY risk). Fix:
- New helper `_dnos_url_to_version_label()` turns the DNOS artifact URL into the
  branch-bearing version label.
- `_run_device_upgrade` now calls `StackManager.detect_branch_switch(cur, tgt, "")`
  -- the SAME function the GUI planner `image_upgrade_plan` uses -- and forces
  `delete_deploy` when the lineage differs. Same-branch build bumps stay `normal`;
  unparseable labels are conservative (no escalation).
- Headless driver `.cursor/skills/upgrade/scripts/upgrade_device.py` mirrors this
  in `--check`, logging `Branch-lineage change ... AUTO selects DELETE+DEPLOY`.
- Docs: rule `dnos-upgrade-runbook.mdc` (the /UPGRADE methodology; formerly the
  `upgrade` skill) + rule `dnos-upgrade-flow.mdc` (section 0).
Reuse-not-reinvent: consolidated on `StackManager.detect_branch_switch` rather
than a parallel parser, so planner + runtime + driver agree. Synced
`topology/routes/upgrade.py` -> `/home/dn/CURSOR/routes/upgrade.py`.

## /TEST Run Speed: Fast-By-Default Without Losing Accuracy -- 2026-06-18

A single Advanced-Functionality TC was costing ~505s ("8.5 min"). Root cause was
NOT the authoritative work (traffic loss verification) but wasted overhead in the
gated runner (`_test_run_gated` / `_test_phase_run` in
`/home/dn/mcp_common/command_profiles.py`). Three verdict-safe optimizations,
all on by default:

1. **Run-scoped topology memo** (`_test_ro_memo_key`, `_TEST_RO_MEMOIZABLE_TOOLS`).
   Config-derived DNAAS path tools (`dnos_dnaas_teach_plan`, `inverse_path`,
   `path`, `walk_from_dut`) are memoized within one run. Recipes call the SAME
   teach_plan once per `tp_step` (interleaved with Spirent setup); the 2nd/3rd
   identical probe now replays in ~0ms (`memoized=True`) instead of a 30-45s SSH
   round-trip. The memo is wiped ONLY on a `config_mutation` (flap/commit) -- a
   `traffic_mutation` cannot change running-config, so it survives Spirent phases.
   `dnos_dnaas_spirent_preflight` is EXCLUDED (it is a live oper-state readiness
   gate and must always re-probe fresh). Verified: 3x teach_plan (105s) -> 1 live
   + 2 memo hits (35s).

2. **Trace-evidence budget cap** (`_test_phase_timeout`). `debug_trace_bundle` /
   `debug_trace_grep` are read-only, NON-authoritative for the verdict and
   already degrade gracefully to `INFRASTRUCTURE_WARN` on timeout. Capped to 50s
   (tunable `trace_evidence_timeout_sec`). A single proxy-arp bundle that took
   102s now caps at 50s. Cannot hide a real failure -- traffic + show-state gates
   decide the verdict.

3. **Parallel read-only batching** (phase loop in `_test_run_gated`). Consecutive
   `read_only` phases (DNAAS probes, show bundles, trace/xray evidence) are
   INDEPENDENT live reads -- they neither mutate state nor depend on each other,
   and the verdict layer aggregates `phase_results` by content, not arrival
   order. A contiguous read-only run is dispatched concurrently
   (`ThreadPoolExecutor`, default 4 workers). Mutation/traffic phases are NEVER
   batched: each runs solo, in strict order, so Spirent setup, flaps, commits and
   the loss verdict stay fully sequential and deterministic. Each parallel
   `with`-block is a join barrier, so setup reads finish before the traffic phase
   that needs them. Kill-switch: `parallel_read_only=false` (or `no_parallel=true`);
   worker count: `parallel_read_only_workers`. Verified: 13 overlapping phase
   pairs, ~194s of read-only work now runs concurrently.

Proof (same PASS verdict, accuracy preserved): IPv6 TC-ANYCAST-IRB-IPV6-01 with
stable traffic went 310-327s -> 240s. The remaining wall time is dominated by the
LEGITIMATE, authoritative `spirent_loss_verify` (the no-loss proof), which is
left untouched and varies run-to-run by convergence (20s-139s). That variance --
not engine overhead -- now dominates per-TC time. Do NOT shorten loss_verify to
chase a faster number; it is the reliability the operator asked to keep.

## MCP Usage Uplift -- 2026-06-17

Local command MCPs should return compact, parse-safe results by default. Shared
backend calls that wrap `dnos_mcp.py` must never silently treat truncated stdout
as a parsed payload: truncation or JSON parse failure is an explicit structured
error with `truncated` and `raw_excerpt`. Evidence-heavy tools such as
`debug_show_bundle`, `debug_trace_bundle`, trace greps, and `handoff_latest`
default to `format=text` and summarize commands/results instead of inlining
large device output.

For repeated read-only live gates, use the shared short-TTL show cache with a
`refresh=true` escape hatch. Do not cache mutating actions, traffic starts, or
write/commit tools. MCP routing rules should map natural-language intent to one
primary tool first, using `suggested_next_call` for cross-server handoff rather
than broad fan-out.

### Reusable NETCONF/gNMI Scenario Runner -- 2026-06-21

Use `/home/dn/netconf_test/scenario_runner.py` for feature workflows that need
multiple NETCONF/gNMI steps (service create, attach/detach IRB, cleanup, etc.).
Do not create a fresh one-off Python harness per Jira unless the reusable
runner cannot express the scenario. Add a `Scenario` definition with target
parameters and phase XML builders, then run:

```bash
python3 -m netconf_test.scenario_runner --scenario <scenario-id> --target <device|all>
python3 -m netconf_test.scenario_runner --scenario <scenario-id> --target <device|all> --execute
```

Default mode is non-committing: NETCONF `edit-config` to candidate, `validate`,
`get-config candidate`, then one final `discard-changes`. `--execute` commits
each phase and the runner performs dedicated-object cleanup unless `--no-cleanup`
is passed. gNMI remains read-only (`capabilities` and post-commit `get`); never
use gNMI Set Replace on DNOS.

SW-265310 scenarios now live in this runner:
- `sw265310-service-validate`: validates the full EVPN SI test service on PE-1
  and RR-SA-2.
- `sw265310-si-irb-add-remove`: commits PE-1 base SI service, commits IRB add,
  commits IRB remove, then cleanup-removes the dedicated service/interfaces.

Committed result on 2026-06-21: `sw265310-si-irb-add-remove --target PE-1
--execute` passed with 3 commits and cleanup OK. Evidence:
`/home/dn/netconf_test/sw265310_sw265310-si-irb-add-remove_report.md` and
`/home/dn/netconf_test/sw265310_sw265310-si-irb-add-remove_evidence/`.
Final native `dnos_run_show_commands` confirmed the dedicated service
`EVPN_SI_SW265310_4010`, `ge400-0/0/5.4010`, and `irb4010` were absent after
cleanup.

### /TEST Smart Script Detection -- 2026-06-21

Before creating a new Python test harness, `/TEST` should try the smart script
detector:

```json
{"tool": "test_script_detect", "args": {"recipe_path": "<recipe.json>", "mode": "observe"}}
```

The detector indexes trusted reusable runner IDs under
`/home/dn/SCALER/TEST/_shared/script_detection.py`, nested catalog recipes,
suite manifests, and `/home/dn/netconf_test/scenario_runner.py` scenarios. It
writes compact metadata under `metadata.script_detection` and, when confidence is
high enough, `metadata.runner_ref`. Default behavior is observe-only; existing
phase compilation and execution remain authoritative unless an operator or
canary explicitly uses `detector_mode=execute_capable`.

Rules:
- New tests add manifests, scenario IDs, and parameters first. Add a new script
  only when the registry cannot express the reusable primitive.
- Runner selection is by stable allowlisted `runner_id`, never arbitrary file
  path.
- Low confidence, missing parameters, timeout, registry error, or detector
  exception falls back to the existing `/TEST` compiler.
- `compiled_phases[].script_call` is allowed only for trusted registry entries;
  runtime still requires `execute=true`, and mutating calls require
  `confirm=true` plus rollback/cleanup evidence.
- Keep canaries in observe-only, then suggest-only, then execute-capable order
  before enabling any new runner family automatically.

### /TEST Compact MCP Responses -- 2026-06-21

Heavy TEST tools now compact large MCP responses before returning to chat:
`test_run_gated`, `test_category_run`, `test_category_status`,
`test_phase_compile`, prerequisite/syntax gates, `test_report`, and
`test_proof_path`. The full JSON is still authoritative and is saved either in
the run directory (`<run_path>/result.json`) or under
`/home/dn/SCALER/TEST/_shared/mcp_large_results/` for dry-runs and standalone
large tool calls.

Rules:
- Keep inline responses small: verdict, blockers, phase summaries, failed
  layers, timings, suggested next call, and full-result path.
- Do not inline full nested `compile`, `syntax`, `prerequisites`,
  `phase_results`, or raw device outputs in chat unless explicitly debugging a
  small payload.
- Use `test_proof_path` or the saved full JSON artifact for audit-grade detail.
- Subprocess wrappers now classify `COMMAND_PASS`, `COMMAND_FAILED`,
  `COMMAND_TIMEOUT`, and `COMMAND_EXCEPTION`, with stdout/stderr truncation
  metadata, so timeout/crash handling can be reasoned about instead of guessed.

YANG shape notes:
- Top EVPN `protocols/bgp` is keyed; include direct child
  `<as-number>...</as-number>` as well as `config-items/as-number`.
- `seamless-integration/protocols/bgp` is not keyed; do not include
  `as-number` there, or DNOS returns `Unknown element 'as_number'`.
- In CLI dry-runs, avoid a bare `transport-protocol mpls` line for this service;
  use explicit leaf lines such as `transport-protocol mpls control-word enabled`
  and `transport-protocol mpls fat-label disabled`.

## /TEST Knowledge-First Syntax Memory -- 2026-06-17

`/TEST`, `/TP`, `/CCIE`, and `/debug-dnos` must treat Jira/Confluence/TP text as
requirements, not executable DNOS syntax. Before live `cmd search` or device
probes, TEST now routes commands through the knowledge-first resolver:

1. saved catalog recipe memory (`metadata.syntax_validation`,
   `metadata.knowledge_resolution`, `compiled_phases`);
2. global corrections (`~/.cursor/test_knowledge/corrections.json`);
3. shared TEST syntax cache (`~/SCALER/TEST/_shared/knowledge/by_protocol/*`);
4. feature knowledge (`~/.cursor/knowledge_base/<feature_id>/`, accepting both
   legacy `command` and canonical `cmd` rows);
5. dnos-config / documented command knowledge;
6. live dnos-config MCP fallback.

When live validation proves a correction, persist it atomically so the next chat
or category run does not rediscover the same error. TP/Jira imports should save
the original text under `original_command` and the executable form under
`command`, with `syntax_status`, `syntax_source`, and `syntax_proof`.

Convergence waits should use `test_dnos_live_wait` / condition polling with
millisecond timing, poll counts, and explicit success conditions instead of
blind sleeps.

### Response-Driven Polling -- 2026-06-17

`/TEST` waits must pace themselves from the actual response time of the device
or tool, not from guessed sleep intervals. The loop is:

1. probe;
2. wait until the probe returns output or hits its per-probe timeout;
3. evaluate immediately;
4. if not successful, schedule the next probe from the observed response
   latency/output change with only a small guard delay when needed.

Every wait result should report `wait_strategy=response_driven_probe`,
`poll_count`, `per_probe_response_ms`, `first_reaction_ms`,
`first_success_ms`, `last_output_digest`, and the exact condition checked.

Fixed sleeps are allowed only for named physical collection windows (for
example, an XRAY packet-capture duration) or explicit operator-requested settle
time, and must be surfaced as such in result timing.

### Native MCP Traffic Order And Host Binding -- 2026-06-17

For TEST traffic workflows, native MCP order is mandatory:

1. `user-test-mcp` compile/syntax/prereq gates.
2. knowledge-first resolver (recipe memory, corrections, shared syntax,
   feature knowledge).
3. `dnos-config` DNAAS inverse/preflight and show verification.
4. `user-spirent-mcp` readiness/create/start, with `spirent_loss_verify` as the
   primary no-loss verdict.
5. `user-xray-mcp` only for explicit packet proof or ambiguous counter proof.
6. `user-debug-dnos-mcp` only after TEST proves infrastructure is clean.

`spirent_loss_verify` is the authoritative traffic verdict because it compares
Spirent port TX delta with DNOS AC RX/drop deltas. `spirent_stats_poll` is
supporting evidence only.

Parity/debug phases must not bake generic or stale expected hosts (`host1`,
`host2`, `expected-host`, `remote-host`, etc.). Expected MAC/IP/interface values
must bind from the current recipe, DNAAS preflight, Spirent stream metadata, or
live learned counters. If binding fails, block as `UNRESOLVED_EXPECTED_HOST`.

## /debug-dnos Bug Description Raw Blocks -- 2026-05-14

`debug_bug_description` must render every raw proof as a self-contained fenced
device block. Each block starts with `# timestamp: <device-local timestamp>`
and `# target: <device>`, then prints the exact command/prompt immediately
above its matching raw output. Timestamp-only bullet metadata outside the block
is not sufficient for Jira-grade evidence.

For long Jira-grade descriptions, use `render_mode="jira_fast"` or
`fast_render=true`. This preserves the required chronological raw device blocks
and in-block timestamps while skipping duplicate `steps[]` evidence reprints
and repeated surrounding metadata, so the description prints faster without
losing proof quality.

Aggregate before/after snapshots may carry `expected`, `observed`, and
`verdict` on each `command_outputs[]` item instead of duplicating those fields
at the snapshot top level. The renderer must treat that as complete evidence
and must not print false `EXPECTED MISSING` / `OBSERVED MISSING` labels.

### Chat-Safe Bug Description Rendering -- 2026-06-21

`debug_bug_description` now separates the durable Jira artifact from the chat
response. Every call renders the full chronological raw markdown and writes it
atomically under `~/SCALER/TEST/_shared/debug_bug_descriptions/`, returning the
path as `artifact_path`. Normal `text` / `both` calls return a compact inline
summary with topology, evidence indexes, decisive clipped raw blocks, expected /
actual results, repro steps, and the artifact path; this avoids MCP spill files
and repeated 40KB chat payloads while preserving the raw proof. Use
`inline_full=true` or `render_mode="full"` only when the operator explicitly
asks for the entire raw artifact inline. A complete before/operation/after
chronology is accepted as proof without forcing duplicate `steps[]` evidence,
so the renderer no longer emits false `no proof steps supplied` warnings for
well-formed chronological payloads.

Trace evidence must identify its source above the raw trace block even in
`jira_fast` mode. Render process/container/file context such as
`process=fibmgrd, container=routing-engine, trace_file=routing_engine/fibmgrd_traces`
so the Jira reader knows exactly where each trace snippet came from.

### One-Shot Evidence Fetch Before Rendering -- 2026-05-14

`/debug-dnos` must collect the full bug path through native MCP tools before
calling `debug_bug_description`. The renderer is not allowed to compensate for
missing collection. For EVPN/VPLS/VPWS service bugs this means:

1. `debug_show_bundle` with `service_name`, `ac_interfaces`, and
   `irb_interfaces` to fetch raw service config/state plus AC/IRB config/state.
2. `dnos_run_show_commands` for the exact before and after assertions. For
   MAC/MAC-IP/ARP bugs, this includes raw `show evpn mac-table`,
   `show evpn mac-ip-table`, `show arp interface <irb>`, and the relevant
   `show dnos-internal routing fib-manager ... local-mac` and `neighbor`
   commands.
3. The mutating trigger through the owning MCP tool
   (`dnos_operational_clear` for EVPN clear commands) with explicit execution
   confirmation.
4. `debug_trace_grep` for every proof-bearing container. For the SW-266901
   PE-1 MAC-IP suppression repro, `routing-engine/fibmgrd_traces` proved the
   propagation drop from `NM:1 NCP:1 Zebra:1` to `NM:0 NCP:0 Zebra:0`, CLI
   traces proved the clear command, and `bgpd_traces` was checked and empty.

When the user asks for a bug description, the first rendered answer must include
the topology, raw service/interface config, before raw tables, trigger output,
after raw tables, trace proof, 1-sentence expected, 1-sentence actual, and
minimal general repro steps. If any of those are missing, do not render a
polished description; fetch the missing evidence or print a warning.

## dnos-config NCP Recovery Tool -- 2026-05-14

For CL/cluster NCP recovery, use `dnos_ncp_recovery` from the `dnos-config`
MCP instead of manual CLI wait loops or ad-hoc console scripts. The tool
detects disconnected/recovery NCP state from the active NCC, resolves the
NCP data-plane console mapping, checks `show system stack`, and builds the
ONIE/BaseOS reinstall plan. It is dry-run first and only executes with
`execute=true`, `dry_run=false`, and `confirm=RECOVER_NCP`.

Important learned behavior from the NCP6 recovery on `YOR_CL_PE-4`: the NCP
console is `console-b10.dev.drivenets.net` port `5`; this is the data-plane
serial console, not the NCC/KVM brain. ONIE must install a raw
`noble-nos-installer-*.sh` URL, not a `drivenets_baseos_*.tar` target-stack
package. The validated ONIE recovery network defaults are `100.64.8.85/20`
with gateway `100.64.15.254`.

## /TEST Live Syntax And Traffic Gates -- 2026-05-14

When running TP-derived `/TEST` recipes, `test_run_gated` and
`test_syntax_validate_live` must resolve the target device from
`device_requirements.primary_device` when no explicit device is passed. Do not
force a source-role device such as `PE-4` onto a PE-1 target-service recipe;
PE-4/RR-SA-2 should be used by compiled source/traffic phases only.

## /CCIE Fast Prerequisite Blueprint -- 2026-06-16

Use `/home/dn/.cursor/skills/ccie-topology-architect/SKILL.md` before expensive
topology-sensitive `/TEST` work. `/CCIE` builds a cached blueprint under
`~/.cursor/ccie/` with device roles, minimum DNOS config deltas, DNAAS frame
recipes, half-deterministic traffic, and per-step show/flag notes.

For multi-recipe or category runs, call `test_prerequisites_batch` first so
shared device/service/VLAN/BGP/Spirent checks are batched instead of rediscovered
per recipe. `test_run_gated` and `test_prerequisites_live_check` may reuse a
fresh `/CCIE` blueprint when the recipe hash matches; if the blueprint is stale
or absent, they must fall back to the existing live prerequisite flow.

Traffic-learning tests must keep the winning stream active through learning
verification. A single ARP or a capture after traffic has stopped is not enough
evidence. For EVPN-SI-VPLS, receiver proof must include the mac-table because
valid remote state can appear as `v>` with next-hop loopback rather than a pure
route-type 2 row on the receiver.

## /TEST Accuracy: Commit + Output Truthing -- 2026-06-16

`test_phase_run` now fails a phase when the device output does not support a
pass, closing a false-PASS gap found on SW-265047
(`TC-IRB-VRF-EVPN-RT-CHANGE-01`), where the run reported PASS while a commit
timed out, another commit was rejected (`ERROR: Unknown word: 'default'`), and
remote-PE steps were proven with local PE-1 output.

- `_dnos_commit_failed`: `dnos_atomic_commit` / `dnos_multi_device_commit`
  phases fail (verdict `DNOS_COMMIT_FAILED`) on `Overall: ERROR`,
  `TimeoutError`, `paste_failed`, `ERROR: Unknown word`, or embedded
  `"ok": false`. CLI bridge exit 0 is not proof of commit success.
- `_tp_step_expected_contradiction`: a TP show step whose own `expected` says
  the route/entry is absent/removed/"not in table" but whose observed output
  shows it present/installed fails (verdict `OUTPUT_CONTRADICTS_EXPECTED`).

When asked for `/TEST` proof or outputs, render RAW device evidence
(`<run>/evidence/<NN_phase>/dnos_result.txt` and `result.json`) and re-judge,
exactly as `/CCIE` (skill `ccie-topology-architect`) and `/debug-dnos` do. Never
report PASS from summary/verdict tables alone.

Strict traffic recipes that require side-to-side Spirent proof must compile two
explicit forward/reverse stream phases before execution. For legacy SW-228552
imports that declared traffic mandatory but omitted `bidirectional_flows`, the
TEST compiler synthesizes those flows from the same PW-source context used by
DNAAS/Spirent host creation, preserving the MCP-owned VLAN/inner matching.
Empty feature-knowledge show-command placeholders must not be treated as syntax
items; only concrete non-empty commands can participate in live validation.
Required-config prerequisite probes must distinguish evidence from transport:
a DNOS show timeout is `PREREQUISITES_INCONCLUSIVE` with no commit target, not
`MISSING_REQUIRED_CONFIG_SECTIONS`. Only successful show output that lacks the
required tokens/patterns may produce an approval-gated commit dry-run.

Traffic measurement has two distinct verdict layers. The first runnable traffic
gate is `traffic_tagged_tx`: created streams must carry the expected DNAAS
outer/inner tagging and Spirent stats must prove those named streams actually
transmitted frames (`TX >= 1`). RX/loss evidence is collected as
`traffic_loss_measurement` after TX is proven, and it is a real no-loss gate:
the same named stream(s) must show RX and `max_loss_pct` must be `0.0` unless
the recipe explicitly declares a higher accepted loss threshold. Packet loss is
never downgraded to a blanket `WARN`; loss is a TEST failure, while unrelated
trace/MCP transport problems are classified separately as infrastructure
warnings.

For SW-228552 IRB/PW traffic, "bidirectional" means two role-correct
`/SPIRENT` streams, not one PW-side stream with reversed IPs. The compiler must
create:

1. `pw_to_irb`: ingress through the PW/source AC (currently RR-SA-2
   `bundle-100.2001`, fabric VLAN 215 inner 3001) with Ethernet destination set
   to the IRB anycast MAC and IP destination set to the PE-1 local AC host.
2. `irb_to_pw`: ingress through the PE-1 local AC (`ge400-0/0/5.4001`, fabric
   VLAN 214 inner 4001) with Ethernet destination set to the IRB anycast MAC and
   IP destination set to the PW host.

After the tagged-TX gate passes, `/TEST` must run a separate bounded
`traffic_loss_observation` stats poll with `rx_min >= 1`, `require_rx=true`,
`expected_direction_count`, and `max_loss_pct=0.0` by default. Strict
bidirectional proofs should TX-gate each direction in isolation (`exclusive`
stream start), then no-loss gate that same named StreamBlock before moving to
the other direction; this prevents stale active StreamBlocks or the Spirent port
scheduler from hiding a silent reverse path. `/TEST` must also compile a
read-only `dnos_dnaas_spirent_preflight` phase before each
`spirent_create_stream`, and `/SPIRENT` must refuse DUT-bound stream creation
unless that DNAAS preflight returns a parsed `READY` payload.
Spirent stats gates are live-polled, not blind sleeps: the default gate window is
60 seconds with 3-second polling so STC has time to expose a newly recreated
StreamBlock, while successful named-stream TX/RX evidence exits early.
When a TEST phase expects specific StreamBlock names, `/SPIRENT` stats must use
targeted per-stream stats (`stats --stream-name <name>`) instead of scanning the
whole long-lived session. This avoids wasting time on stale StreamBlocks and
prevents false zero-TX verdicts while unrelated streams/devices remain in
`dn_spirent_main`.
Before the first traffic setup phase, `/TEST` must run
`spirent_prune_test_scope` after Spirent readiness and before creating streams.
The prune phase removes stale TEST-owned StreamBlocks whose names do not include
the current `test_id`, while preserving manual/non-TEST objects and current-test
streams. This keeps `/SPIRENT stats` fast and prevents unrelated historical
streams from affecting verdicts.
Debug trace collection is a diagnostic layer for these traffic tests. If
`debug_trace_bundle` / `debug_trace_grep` fails because the MCP/SSE transport
drops (`incomplete chunked read`, stale binding, `Not connected`) or bounded
trace-file collection times out, record an infrastructure warning and keep the
traffic/no-loss and show-state verdicts authoritative. Do not relabel a
transport failure as a DNOS dataplane failure.

`/TEST` trace phases must call `/debug-dnos` with
`trace_backend=isolated_ssh_cli`. Each trace command opens a throwaway read-only
SSH CLI session to the DUT and closes it after the bounded command window. Never
run slow `show file traces ...` collection through the shared dnos-config
persistent session used for prerequisites, syntax validation, or service-state
checks; a hung trace pager can contaminate later show output and create false
TEST failures.

For device-side convergence and CLI behavior, `/TEST` must use dnos-config live
polling instead of fixed sleeps. Compile TP steps that declare `wait_for`,
`max_wait_sec`, `convergence_time_seconds`, `convergence_budget_seconds`,
`poll_interval_sec`, or an explicit `live_wait` block into
`test_dnos_live_wait`. That tool polls `dnos_run_show_commands` through
dnos-config DNOSSession and returns as soon as the expected tokens/regexes are
present and forbidden tokens are absent. Use bounded stats/capture windows only
for traffic counters and packet capture, where time is the measurement itself.

## Layered Packet/Frame Object -- 2026-05-14

A new canvas object type `packet` was added to make scenarios self-explanatory
above the link they ride. Use it whenever the agent (or operator) wants to
teach what bytes flow over a connection without burying the answer in a long
text block.

### Schema (per `topology-packets.js`)

```jsonc
{
  "id": "packet_0",
  "type": "packet",
  "linkId": "link_3",            // optional; null = freestanding
  "linkAttachT": 0.5,            // 0..1 parametric position along the link
  "x": 0, "y": 0,                // recomputed every frame when linkId is set
  "title": "Frame",              // chip header
  "summary": "BGP UPD",           // optional 2-3 word pill below chip
  "direction": "forward",        // "forward" | "backward"
  "userWidth": 180,               // optional manual width from E/W handles
  "collapsed": false,            // when true, only the chip header is drawn
  "locked": false,
  "layers": [
    {"id": "L2",      "label": "L2",      "text": "...", "color": "#5dade2", "visible": true, "freeText": false},
    {"id": "VLAN",    "label": "VLAN",    "text": "...", "color": "#48c9b0", "visible": true},
    {"id": "MPLS",    "label": "MPLS",    "text": "...", "color": "#bb8fce", "visible": true},
    {"id": "L3",      "label": "L3",      "text": "...", "color": "#f5b041", "visible": true},
    {"id": "L4",      "label": "L4",      "text": "...", "color": "#e59866", "visible": true},
    {"id": "PAYLOAD", "label": "Payload", "text": "...", "color": "#85c1e9", "visible": true}
  ]
}
```

The packet ID counter is persisted via `metadata.packetIdCounter` (mirroring
`shapeIdCounter`), and `topology-files.js` / `topology-file-ops.js` already
include `packet` in the saved counters block.

### How it renders

* Chip is drawn ABOVE the canvas mid-line of its link using `chip height / 2`
  plus a fixed clearance gap, so the chip never overlaps the cable even when
  extra rows are visible. The popup can flip the chip below the link by setting
  `side: "below"`; default remains `side: "above"`.
* Hidden layers (`visible=false`) are summarized as `+N hidden` so the chip
  stays compact.
* A small summary pill is drawn below the card. The left side shows a 2-3 word
  label (`summary`, or a derived value from `title`); the right arrow flips
  `direction` without opening the full popup. Direction is rendered as a
  link-angle-aware arrow in both the header and on the wire anchor; `forward`
  follows link start->end and `backward` reverses it.
* Selecting a packet draws E/W stretch handles (tall grab-bars, not 6px dots).
  Dragging either handle writes `userWidth`; double-clicking the handle resets
  the chip to auto width. The packet popup also exposes `Reset width`,
  `Move above/below`, and a `Detach`/`Re-attach` toggle.
* Two width clamps (2026-06-14, reveal-on-stretch fix):
  - `PacketMethods.clampPacketWidth(w)` (`PACKET_MIN_WIDTH`..`PACKET_MAX_WIDTH`,
    92..360) is the **auto** cap used by `getPacketBounds` for content sizing.
  - `PacketMethods.clampPacketUserWidth(w)` (`PACKET_MIN_USER_WIDTH`..
    `PACKET_MAX_USER_WIDTH`, 80..480) is the **manual stretch** range used by the
    `topology-mouse-move.js` resize-drag path. The drag previously reused the
    360 auto cap, so long address lines (full MAC / IPv6 / Q-in-Q) could never be
    fully revealed by stretching even though `getPacketBounds` allowed up to 480.
    Dragging now reaches 480 and `textMaxW = bounds.w - 22 - nameW` grows with it,
    so stretching reveals the full address. Do NOT collapse these two clamps back
    into one -- auto sizing and manual stretch intentionally have different caps.
* Multi-select highlight (2026-06-14): `drawPacket` highlighted only
  `editor.selectedObject === packet`, so a packet grabbed by a marquee (in
  `editor.selectedObjects` but not the primary) drew with no border/glow.
  Added `isHighlighted = isSelected || isMultiSelected` driving the card shadow
  + border; the single-select-only affordances (stretch handles, chevron box)
  stay gated on `isSelected`.
* Stretch feel (2026-06-14): the resize start now records `attached` + the
  pinned `oppositeEdgeX`. FREESTANDING packets resize with the opposite edge
  pinned (grabbed edge tracks the cursor 1:1, width changes 1:1 with the hand,
  `packet.x` re-centered) -- the standard smooth/proportional handle feel.
  ATTACHED packets keep symmetric growth about the link anchor (`delta * 2`,
  no `packet.x` change) because `topology-draw.js` re-centers them on the cable
  every frame via `updatePacketPosition`; shifting `x` there would fight that
  pass and jitter. Do NOT apply the freestanding anchored-edge math to attached
  packets.
* Marquee / multi-select (2026-06-14, "MS does not select the Packet box" fix):
  `findObjectsInRectangle` in `topology.js` had branches for device/text/link/
  shape but NONE for `packet`, so rubber-band selection silently skipped packet
  chips. Added a `packet` bbox-overlap branch that resolves the live hitbox via
  `PacketMethods.getPacketBounds` (honours collapsed state + manual stretch
  width). When adding any new selectable object type, update BOTH
  `findObjectAt` (single-click) AND `findObjectsInRectangle` (marquee).
* Legacy address placeholders (2026-06-14): old packets stored abbreviated layer
  text like `src 00:..:01` / `src ---` which read like a *truncated* address on
  the chip and confused users ("addresses not revealed"). `makeDefaultLayers`
  now seeds full readable values (`src 00:00:00:00:00:01`, `src 10.0.0.1`,
  `outer=100\ninner=200`) and `drawPacket` calls `_upgradeLegacyLayers(packet)`
  which rewrites ONLY exact legacy placeholder strings (`_LEGACY_TEXT_UPGRADES`)
  to the full form. User-entered values never match the table, so they are never
  touched. This was a content/placeholder issue, NOT a width/ellipsize issue.
* Re-attach (2026-06-14): a detached/freestanding packet can be re-attached two
  ways. (1) Popup `Re-attach` button -> `PacketMethods.attachPacketToNearestLink
  (editor, packet, Infinity)` snaps to the closest link anywhere. (2) Drag-drop:
  `topology-mouse-up.js` calls `attachPacketToNearestLink(editor, packet, 70)`
  when a real drag of a freestanding packet ends within 70 world-px of a wire.
  Both go through `findNearestLink` (40-sample projection per link, same math as
  `projectCursorToLinkT`) then `attachPacketToLink`. Outside the snap radius the
  packet stays freestanding so free placement is preserved.
* The header chevron (`\u25B8`/`\u25BE`) is a real canvas hit target
  (`findPacketChevronHit`) -- clicking it toggles `collapsed` directly on the
  chip without opening the popup.
* GOTCHA (fixed 2026-06-14): both the chevron-collapse and the stretch handles
  are gated by `obj._mouseReleasedAfterSelection === true` (the same arm-after-
  release guard devices/shapes use). `packet` was missing from BOTH the
  mouse-down "set false on select" list (`topology-mouse-down.js`) and the
  mouse-up "set true on release" list (`topology-mouse-up.js`), so a packet
  selected by clicking its body never armed and collapse/stretch did nothing.
  When adding a new selectable object type with handles, add it to BOTH lists.
* Compact-but-readable sizing (2026-06-14): `ROW_HEIGHT=16`, `HEADER_HEIGHT=16`,
  per-line advance `LINE_STEP=11`, tighter paddings. Layer-name and text font
  measurement (`8.5`/`9.5`) is kept in sync between `getPacketBounds` (width
  calc) and `drawPacket` (render) so ellipsizing never disagrees with the box.
* Grouped packets use the existing group metadata (`groupId`, `groupColor`)
  and show the group color on the chip border.
* Selecting a packet opens a floating popup (`topology-packet-popup.js`)
  with per-layer toggles, title rename, collapse/expand, direction switch,
  and delete.
* Hit-test priority is `packet (5) > text (4) > device (3) > link (2) > shape (1)`,
  so the chip always wins when overlapping a label.

### How operators add one

1. Click the link to open its toolbar.
2. Click the new "Add Packet" button (layered icon) next to "Add Text".
3. The chip appears centred on the link with sensible default rows
   (`L2 Ethernet` filled, every other row pre-collapsed). Open the popup
   and toggle/edit rows.

### Validation and edit behavior

Packet popup edits redraw immediately but debounce `saveState()` so typing does
not create a noisy undo stack. Layer text is strict by default:

| Layer | Default validation |
|-------|--------------------|
| `L2` | MAC-style hex, colons, dots, arrows, `src` / `dst` text |
| `VLAN` | VLAN words, digits, equals, commas, dashes |
| `MPLS` | Label/stack text, alphanumerics, dashes, commas |
| `L3` | IPv4/IPv6-ish addresses, slashes, arrows, `src` / `dst` text |
| `L4` | Protocol/port/key-value text |
| `Payload` | Printable ASCII |

**Structured per-layer field editor (2026-06-14).** Instead of one freeform
textarea, recognised layers render dedicated, self-validating inputs defined by
`LAYER_FIELD_SCHEMAS` in `topology-packet-popup.js`:

| Layer | Fields (key -> input) | Composed `layer.text` |
|-------|-----------------------|------------------------|
| `L2`   | Src MAC, Dst MAC | `src <mac>` / `dst <mac>` |
| `VLAN` | Outer, Inner     | `outer=<n>` / `inner=<n>` |
| `MPLS` | Label, Stack     | `label <n>` / `stack <n>` |
| `L3`   | Src IP, Dst IP   | `src <ip>` / `dst <ip>` |
| `L4`   | Proto, Flags     | `<proto>` / `<flags>` |

Each input filters keystrokes by `kind` (`FIELD_KIND_FILTERS`: mac/ip/vlan/num/
l4). Raw values are stored on `layer.fields` (round-trips exactly on reopen) and
`_composeLayerText(layer)` rebuilds `layer.text` (what the chip renders) on every
edit. `_deriveFields(layer)` best-effort parses an existing `layer.text` into
fields the first time the editor opens, so older packets keep their data.

The per-row toggle is now schema-aware:
* Schema layers: button reads `raw` / `fields` and flips `freeText` to swap the
  detail area between the structured inputs and the legacy textarea (the escape
  hatch for anything the fields can't express). Flipping to raw clears
  `layer.fields` so a later flip back re-parses cleanly.
* Non-schema layers (`Payload`, `L1`): button stays `abc`; `freeText=true`
  disables strict textarea filtering while still capping two short lines.

Canvas rendering ellipsizes long layer names and text lines inside the card
instead of allowing overflow into adjacent devices or links.

### How auto-generation works

* `serve.py:_build_bug_topology_json` -- when `route` (dst/src/action) or any
  `vrfs` are provided, it emits exactly one packet attached to the link
  approaching `failure_device`. Empty layer rows are pre-collapsed so the
  chip stays compact, `direction` points toward the failure device by default
  (or follows explicit route source/destination device hints), `summary` is
  derived from the protocol/action (`BGP UPD`, `FLOWSPEC`, `VPLS PW`, `EVPN RT-2`,
  etc.), and `metadata.packetIdCounter` is set so subsequent edits do not
  collide with `packet_0`.
* `mcp/tools/imports.py:_attach_packets_to_links` -- exposed to all three
  preview tools (`topology_plan_from_network_mapper`,
  `topology_plan_from_dnos_json`, `topology_plan_from_image`) via the new
  `attach_packets: bool = false` argument. When true, every link with a
  `protocol` / `vrf` / `bd` / `fromInterface` / `toInterface` / `label`
  gets a packet chip with the corresponding rows populated plus an auto
  `summary` and `direction`. Empty rows are pre-collapsed.

Use `attach_packets=true` for "explain this scenario" diagrams (image
imports of a service flow, DNAAS path imports). Skip it for plain
inventory diagrams where the chips would just be visual noise.

### Files touched

| File | Purpose |
|------|---------|
| `topology/topology-packets.js` (new) | Object schema, defaults, create/draw/hit-test/layer-toggle, link follow |
| `topology/topology-packet-popup.js` (new) | Floating per-layer toggle/edit popup |
| `topology/topology-draw.js` | Adds `packet` to per-frame position update + sort/draw passes |
| `topology/topology-object-detection.js` | Adds packet hit detection (highest priority) |
| `topology/topology.js` | `packetIdCounter`, `createPacket/drawPacket/find/show` wrappers, save/load metadata round-trip |
| `topology/topology-link-toolbar.js` | "Add Packet" button next to "Add Text" |
| `topology/topology-mouse-down.js` | Opens packet popup on click |
| `topology/topology-files.js` + `topology-file-ops.js` | Persists/restores `packetIdCounter` |
| `topology/serve.py` | Auto-emits packet from `_build_bug_topology_json` route hint |
| `topology/mcp/tools/imports.py` | `_attach_packets_to_links` + `attach_packets` arg on the 3 plan tools |
| `topology/mcp/server.py` | `attach_packets` exposed on the 3 plan-from-* MCP tools |
| `topology/index.html` | New `ico-packet` SVG symbol; loads the two new modules; bumps cache busters |

### Anti-patterns to avoid

* Do NOT hand-roll a new "frame chip" object type for one-off bug topologies;
  always reuse the `packet` schema so the popup, save/load, hit-test, and
  multi-user persistence all keep working.
* Do NOT default `attach_packets=true` on inventory imports -- chips are for
  scenario teaching, not for every link in a full-fabric diagram.
* Do NOT bump `packetIdCounter` manually outside `createPacket(...)` or the
  load path; it is the only mechanism that prevents ID collisions on undo.

### Packet UX polish -- 2026-06-14

Visual + responsiveness pass on the packet object (`?v=20260614a-packet-ux`):

* `topology-packet-popup.js`
  * One-time scoped stylesheet (`#packet-popup-style`) gives every popup
    control consistent feedback: button press (`:active` transform), hover
    brightness, `:focus-visible` outline, input/textarea focus glow, and a
    `.12s` popup entrance animation. The stylesheet only adds transform +
    outline + filter so it never fights the per-button inline backgrounds
    (e.g. the red Delete button keeps its color).
  * The `Collapse/Expand`, `Reverse`, and `Move above/below` toggles now
    update their own label in place instead of calling `show(editor, packet)`
    again. The previous full re-show tore down and rebuilt the whole popup on
    every click, which flickered and dropped input focus. Detach still
    re-shows because its footer link-status text changes.
  * Checkboxes get a `.packet-checkbox` class (press scale) and layer rows a
    `.packet-layer-row` class (hover inset ring).
* `topology-packets.js` (`drawPacket`)
  * The chip now has a soft drop shadow (depth) that becomes a cyan glow when
    selected, plus a subtle vertical gradient fill. The shadow is applied only
    to the card fill (wrapped in its own `save/restore`) so the border and
    text stay crisp. Drag/position math is unchanged.

Anti-patterns: do NOT route per-button hover/active backgrounds through the
shared stylesheet (it would clobber the Delete button's red); keep background
state inline and let the stylesheet own only transform/outline/filter. Do NOT
re-`show()` the popup for simple in-place toggles -- it regresses the flicker
and focus-loss this pass fixed.

### Packet collapse + stretch responsiveness -- 2026-06-14 (b)

Follow-up after the UX pass: collapse/expand and the stretch handles were not
fully working.

* `getPacketBounds` now treats a manual `userWidth` as **authoritative**
  (`totalWidth = userWidth ?? autoWidth`). The old `Math.max(autoWidth,
  userWidth)` silently ignored any attempt to drag the chip NARROWER than its
  content, so the stretch handle appeared dead on shrink. Text/labels ellipsize
  via `_fitCanvasText`, so a narrow chip is still readable. Width stays clamped
  to `[MIN_USER_WIDTH=80, MAX_USER_WIDTH=480]`, matching the drag clamp in
  `topology-mouse-move.js`.
* Resize handles are now tall vertical grab-bars (`getPacketHandles` returns
  `{w,h}`; `h` scales with chip height, 14-26 px) with grip lines, and
  `findPacketResizeHandle` uses a generous, zoom-compensated hit zone
  (`padX = 7 + 4/zoom`). The previous 6 px square was very hard to grab.
* New `findPacketChevronHit(editor, packet, x, y)` makes the header chevron
  (top-right) a real click target. `topology-mouse-down.js` toggles
  `packet.collapsed` on the canvas when an already-selected packet's chevron is
  clicked, and re-shows the popup only if it is currently open (to keep the
  Collapse/Expand label in sync). Gated on `_mouseReleasedAfterSelection` so the
  first selecting click never accidentally collapses.

Anti-patterns: do NOT reintroduce `Math.max(autoWidth, userWidth)` -- it breaks
shrink. Do NOT make the chevron toggle on the first (selecting) click; gate it on
`_mouseReleasedAfterSelection` like the resize handles.

## /TOPOLOGY Domain Picker + Image-To-Topology -- 2026-05-14

Two contracts were added to the `/TOPOLOGY` slash command and Topology MCP:

### 1. Domain Picker (mandatory for every CREATE)

Every flow that produces a NEW topology -- mesh/star/chain helpers,
`topology_create_from_plan`, `topology_create_topology`, `topology_create_mesh`,
plan-from-network-mapper, plan-from-dnos, plan-from-image, duplicate -- MUST
ask the user where to save it via the `AskQuestion` tool, listing every
writable domain plus a final `Create new domain...` option. The agent must
NOT silently default to "the first domain" or to a hardcoded "default" name.

If the user picks `Create new domain...`, the agent calls `AskQuestion`
again for the new domain name (and optional description), then
`topology_create_domain(name=..., description=...)` and uses the returned
`domain.id` for the create call.

The only exemption is `topology_create_bug_topology`, because bug topologies
always save into the per-user `__bugs` domain.

After save, list topologies in the destination and confirm the new row is
present; call `topology_repair_legacy_visibility` if the app dropdown still
hides it (the app reads `/api/sections` files, the MCP writes the multi-user
DB plus mirrors).

### 2. `topology_plan_from_image` MCP tool

New READ-ONLY MCP tool added in `topology/mcp/tools/imports.py`:

```
topology_plan_from_image(
    image_extraction_json: Dict[str, Any],
    name: str = "Image Import",
    auto_group_by: str = "",
    auto_layout: bool = False,
) -> Dict[str, Any]
```

Use case: the user attaches a network diagram in chat (PNG/JPEG/screenshot)
and asks for an editable canvas version of it. The MCP server itself never
sees the image. The agent reads the diagram with its own multimodal vision
capability, then emits a payload in the standard import shape:

```
{
  "devices": [
    {"label": "PE-1", "deviceType": "PE", "role": "PE", "x": 220, "y": 220},
    ...
  ],
  "links": [
    {"source": "PE-1", "target": "P-1", "label": "ge-0/0/0"},
    ...
  ],
  "groups": [
    {"name": "Provider Edge", "members": ["PE-1", "PE-2"]}
  ]
}
```

Defaults differ from `topology_plan_from_network_mapper` /
`topology_plan_from_dnos_json`:

* `auto_layout=False` -- preserve the X/Y the agent extracted from the image
  so the saved canvas matches the diagram exactly.
* `auto_group_by=""` -- do not synthesize role/site groups; the agent should
  emit explicit `groups: [...]` only when the diagram visually clusters
  devices.

2026-05-14 follow-up: image payloads may also include explicit `groups`,
`shapes`/`panels`, and `texts`/`annotations`. The importer now preserves these
as canvas group membership, rectangle/text objects, and label callouts so
service screenshots such as EVPN/VPLS SI IRB keep their visual panels and IRB
notes instead of collapsing to bare devices and links.

2026-05-14 style follow-up: image imports now preserve visual styling for
devices and links. Device rows may use flat keys or nested `style: {...}` with
`visualStyle`/`deviceStyle`, `color`/`fillColor`, `radius`/`size`, `rotation`,
`labelColor`, `labelSize`, `fontFamily`, and `fontWeight`. When no style is
provided, the importer infers `classic` for router/PE/RR devices, `server` for
CE/host/server/Spirent endpoints, and `hex` for switch/leaf/spine/fabric
devices. Link rows preserve `style`/`lineStyle`/`linkStyle`,
`color`/`strokeColor`, `width`/`strokeWidth`, and optional `curveOverride`.

Cursor MCP clients may probe `/.well-known/oauth-protected-resource` before
using the configured bearer header. `serve.py` and `scaler_bridge.py` must
return JSON metadata for that probe; do not let it fall through to an HTML 404.

Implementation detail: `_build_plan` in `topology/mcp/tools/imports.py` now
takes an `auto_layout: bool = True` parameter. Network Mapper and DNOS
importers keep the default (always run `_apply_clean_layout`); the new
image tool passes `auto_layout=False` to skip the row layout and preserve
the agent's coordinates. Existing imports' behavior is unchanged.

The tool is registered via `@server.tool()` in `topology/mcp/server.py` and
listed in `READ_ONLY_TOOLS` in `topology/mcp/dispatcher.py`. After server
restart the JSON descriptor under
`~/.cursor/projects/<workspace>/mcps/<server>/tools/topology_plan_from_image.json`
is auto-generated by Cursor's MCP loader.

### Anti-patterns to avoid

* Writing a custom Python script that imports
  `topology.mcp.tools.imports._build_plan` to "do the parse server-side".
  The agent's vision is the only image reader; the MCP server never accepts
  raw image bytes.
* Calling `topology_create_from_plan` immediately after
  `topology_plan_from_image` without showing the plan summary / warnings /
  validation issues to the user.
* Skipping the Domain Picker because the user said "save it". "Save it
  where?" is the missing question; ask it via `AskQuestion`.

### Files touched

* `topology/mcp/tools/imports.py` -- added `auto_layout` flag + new tool.
* `topology/mcp/server.py` -- new `@server.tool()` wrapper.
* `topology/mcp/dispatcher.py` -- added to `READ_ONLY_TOOLS`.
* `topology/mcp/skill_bundle/tools.md` + `workflows.md` -- documented new
  tool and "Choose A Destination Domain" workflow.
* `.cursor/commands/TOPOLOGY.md` -- added IMAGE mode + Domain Picker
  contract + Do-Not entries.
* `.cursor/skills/topology/SKILL.md` -- added Domain Picker + Image-To-Topology
  pattern sections.
* `topology/tests/test_topology_mcp_unit.py` -- smoke for the new tool.

## Debug-DNOS Minimal Repro Workflow -- 2026-05-14

`/debug-dnos` now has a `debug_repro_minimizer` planner for turning one good
and one bad assertion set into a short repro recipe. It is intentionally
read-only: it emits reset steps, the smallest trigger, post-trigger assertions,
trace filters, and negative controls. Any suggested operational clear still
must be executed separately through `dnos_operational_clear` with
`execute=true` and `confirm=true`.

Validated PE-1 EVPN MAC-IP suppression pattern:

1. Reset to healthy with broad PE-1 `clear evpn mac-table`, then
   `run ping 10.214.40.10 count 3`.
2. Confirm healthy state: PE-1 has VPLS-PW MAC `00:fe:11:00:40:fe`, MAC-IP
   `10.214.40.10`, ARP reachable on `irb4001`, fib-manager
   `neighbor_keys_size=1`, and L2-neighbor REACHABLE.
3. Minimal trigger:
   `clear evpn mac-table instance EVPN_SI_VPLS_1 mac 00:fe:11:00:40:fe`.
4. Bug state: MAC table, ARP, fib-manager local-mac neighbor key, and
   L2-neighbor stay present/reachable, but EVPN MAC-IP loses the remote
   `v>` MAC/IP row.
5. Trace fingerprint: fibmgrd logs `EvpnLocalMacRemove`, `entry has L2 1
   neighbors`, `dont trigger entry, instead do probe`, then duplicate
   L2-neighbor updates with `NM: 0, NCP: 0, Zebra: 0`; rib-manager has no
   matching `EVPN local neighbor` line for the bad trigger minute.

Negative controls proven during isolation: RR-SA-2 `clear evpn mac-ip-table`
alone and RR-SA-2 `clear evpn mac-table` alone did not reproduce; extra PE-1
IRB pings after the targeted clear keep ARP reachable but do not restore the
missing MAC-IP row.

## Debug-DNOS Bug Description Evidence Contract -- 2026-05-14

`/debug-dnos debug_bug_description` must render Jira-grade bug descriptions in
strict chronological order. The default structure is:

1. topology and service context,
2. a short issue summary,
3. baseline raw command inputs/outputs with device-local timestamps, where each
   command line is printed immediately above its matching output in the same
   raw device block,
4. operational command inputs/outputs (`clear`, `request`, config mutation,
   rollback, ping trigger, or traffic start) with timestamps,
5. post-operation raw command inputs/outputs,
6. trace and shell/DB evidence,
7. `Expected Results` and `Actual Results` as concise 1-2 sentence paragraphs,
   plus general `Minimal Steps To Reproduce` with short topology/traffic
   prerequisites, at the bottom before the final verdict.

Raw command proof is mandatory. Summaries alone are not enough: every evidence
entry must preserve the exact target, timestamp, command or raw input, raw
output, expected result, observed result, and verdict. If any field is missing,
the renderer must warn explicitly instead of silently hiding the gap. The Jira
format pattern follows the structure used in SW-266543.

### Topology Section (mandatory, structured sub-tables)

The `topology` payload is rendered as a first-class section with dedicated
sub-tables -- it is NOT a flat key-value blob. Renderer
(`mcp_common.command_profiles._render_topology_section`) splits the payload
into four readable sub-tables so a reader can understand the setup without
prior lab context:

1. **Devices** -- `topology.devices` is a list of dicts; each dict produces one
   row with columns `Device | Role | Loopback / Peers | Notes`. Recognised
   per-device keys: `name`/`device`/`hostname`, `role`/`function`,
   `loopback`/`loopback_ip`/`router_id`/`peer`/`peers`. Any remaining keys
   (management IP, image, platform, etc.) become `key=value` entries in the
   `Notes` column. A bare string `devices` is rendered as a single
   `**Devices:** ...` narrative line, never iterated character-by-character.
2. **Interfaces (AC / IRB)** -- `topology.interfaces` is a dict (or list of
   dicts) where each entry maps an interface role label to a concrete
   interface name + VLAN/IP. A bare string form is rendered as a single
   narrative line.
3. **EVPN / Service Identifiers** -- `topology.ids` is a dict for service
   identifiers (`service`, `evi_id`, `rd`, `rt`, `site_id`, `peer_site_id`,
   any feature-specific ID). Each becomes one row in the IDs table.
4. **Additional Topology Notes** -- everything else (`traffic`, `pw_status`,
   etc.) is rendered as a final notes table.

The renderer reports missing topology fields as structured warnings so that
agents are nudged to include them: `topology.devices missing`,
`topology.interfaces missing`, `topology.ids missing`, and an overarching
`topology summary missing` when the whole payload is empty. Submit a populated
topology block on every bug description; never let the section render as raw
Python `repr`.

## TEST SW-228552 ESI Prerequisites -- 2026-05-14

SW-228552 `/TEST` recipes must not treat implicit single-homed ESI-zero ACs as
ready for Sanity execution. Before running traffic, the TEST MCP prerequisite
gate requires every EVPN VPLS seamless-integration site-interface AC in the live
lab to have:

1. A concrete `site-id <id> site-interface <ac>` binding under the EVPN SI
   service.
2. A distinct explicit ESI payload under
   `network-services multihoming interface <ac> esi arbitrary value <9-octet>`.
3. `network-services multihoming interface <ac> redundancy-mode single-active`
   for genuinely single-homed lab ACs, unless the recipe explicitly models an
   all-active multihoming scenario.

The validated DNOS syntax is `site-interface`, not `interface`, and
`esi arbitrary value` takes the 9-octet arbitrary payload because DNOS supplies
the leading type-0 ESI byte.

## Strict TEST Evidence Contract -- 2026-05-14

EVPN-SI and IP mobility `/TEST` recipes must not PASS from command success or a
single shallow show output. Strict recipes compile mandatory phases for:

1. topology and operational prerequisites before any traffic or mutation,
2. `/debug-dnos` show bundles before and after the trigger,
3. cross-show learning consistency across EVPN summary/detail, MAC, MAC-IP,
   ARP/NDP, BGP RT-2, forwarding-table, mobility/counter, and VPLS-PW surfaces,
4. frontend/internal parity via `show dnos-internal routing ...`, and
5. bidirectional service/VRF traffic through `/SPIRENT`, plus loss evidence.

For strict recipes, skipped required evidence layers are failures. Verdict
layers include `topology_minimum`, `oper_minimum`, `learning_consistency`,
`learning_cross_show_parity`, `internal_parity`, `debug_show_bundle`,
`trace_bundle`, `datapath_shell_xraycli`, `bidirectional_spirent_traffic`, and
`traffic_loss_measurement`.

Any traffic-relevant strict recipe must declare two explicit Spirent flows
(`traffic_contract.bidirectional_flows`) over the tested service/VRF. The
forward and reverse streams must each have concrete source/destination
IP/MAC, VLAN/inner-VLAN or DNAAS preflight binding, and a stream name. Phase
compile must return `NEEDS_PHASE_WIRING` if either direction is missing, and
`spirent_stats_poll` must require two passing per-direction stream results with
`max_loss_pct=0` unless the recipe explicitly documents a different allowed
loss threshold.

PW-to-PW last-wins tests must declare an `assertion_contract` with the expected
MAC/IP, two PW source events, final winning PW peer/next-hop, losing peer tokens,
required `v>` source semantics, and forbidden local/self-originated RT-2
behavior. The dedicated learning parity phase must prove the same final owner
across MAC table, MAC-IP table, BGP RT-2, forwarding-table, VPLS-PW evidence,
internal DBs, and debug traces before PASS is allowed.

## Bug Topology JSON Compatibility -- 2026-05-13

Generated bug topologies should keep canvas objects conservative so they load
reliably across the current GUI and older cached frontend bundles:

1. Use `deviceType: "router"` or `deviceType: "switch"` only. Represent hosts,
   Spirent, servers, and external endpoints with `visualStyle: "server"` or
   `visualStyle: "simple"`, not a new `deviceType`.
2. Keep simplified repro topologies small enough to inspect manually: prefer a
   few devices, a few links, and short text panels over dense evidence maps.
3. Prefer centered left-to-right symmetric layouts with `style: "arrow"` links
   for the main packet/control flow. Keep link captions to one or two words.
4. Validate every generated link's `device1` / `device2` and every text
   `linkId` before saving. Orphaned references may load partially or render in
   surprising positions.
5. When repairing a user topology JSON under `~/.topology_users`, keep a
   sibling backup and write the replacement atomically.

## MCP Output Formatting -- 2026-05-13

Operator-facing MCP calls should show the useful text first in the Cursor
`CallMcpTool` result:

1. dnos-config tools that run device CLI, component shell, datapath shell, core
   analysis, or config commit workflows default to `format=text`. Their
   Markdown renderers must preserve raw device output in fenced blocks and keep
   structured JSON available only when the caller explicitly asks for
   `format=json` or `format=both`.
2. Spirent MCP tools default to `format=text`. Their summaries should parse
   JSON stdout into human-readable status/tables instead of showing raw JSON as
   the primary result. Exact structured payloads remain opt-in via
   `format=json` or `format=both`.
3. Suggested follow-up calls to Spirent tools should use `format=text` unless a
   machine parser explicitly needs JSON.
4. `/debug-dnos` bug descriptions must render multi-command evidence as
   command/output pairs. Do not print all commands first and all outputs later;
   each command must be immediately followed by its matching raw output when the
   evidence payload supplies `command_outputs` or can be safely split.
5. For EVPN VPLS SI IPv6 proxy-NDP issues, include neighbor-manager context in
   the evidence layer: `show ndp`, EVPN `ndp-table`, fib-manager EVPN
   `l2-neighbor`, `show dnos-internal routing fib-manager database neighbor
   address <ip>`, and neighbor-manager traces under
   `routing_engine/neighbour_manager_*`. Do not use the hidden vty-only
   `show fib-manager fpm queues neighbor-manager` from source tests; it is not
   exposed in DNOS CLI on PE-1. A dynamic `NEIGHBOUR_MANAGER` update ignored
   as "not permanent" is expected generic-NDP behavior, not the successful
   datapath proxy-NDP raw-update path.

## Cluster SSH Target Selection -- 2026-05-13

For every cluster terminal launch, for every user and topology, the target
address must be the active NCC identity (for example `kvm108-cl408d-ncc1`).
Do not use chassis/NCP serials (`WDY...-P3`, `WK...`, etc.) and do not silently
replace the target with cached per-NCC IPs such as stale `100.64.11.96`.

1. `topology-ssh-target.js` is the shared selector. For cluster devices,
   `_activeNccHost` / `_virshInfo.activeNcc` / monitor `active_ncc_vm` win
   before chassis serials and cached IPs (`hostBackup`, `_activeNccIp`,
   `_nccMgmtIp`, `_registeredMgmtIp`).
2. Do not auto-open `TerminalPanel` just because the target is a serial. Keep
   the SN as the launch target and let the user's selected connection
   preference (`iTerm`, `Web`, or `Auto`) decide the transport.
3. Active-NCC cache pairs are trusted only when `_activeNccHost` and
   `_activeNccIp` agree with `_activeNccDnsMap`; otherwise discard the stale IP
   and re-resolve before launch.
4. Regression gate: run both `python3 topology/tests/test_ssh_target_priority.py`
   and `node topology/tests/smoke_ssh_target_picker.js` after changing SSH
   target selection. The Node smoke test executes the real picker across
   multiple generic cluster records and fails if any cluster resolves to a
   chassis serial or cached IP instead of the active NCC hostname.
5. After editing SSH JS, bump `?v=` in `index.html` and sync all touched
   topology files to `/home/dn/CURSOR/`.

## Groups Panel Theme + Live Refresh -- 2026-05-12

`topology-groups-panel.js` owns its runtime CSS. Keep the Groups panel theme
explicit:

1. `body.dark-mode` must render the dark liquid-glass panel.
2. `body:not(.dark-mode)` must render the light variation.
3. The panel should refresh dynamically while open when topology/group state
   changes. It uses a small signature watcher instead of repainting on every
   canvas draw, so it catches topology loads, generated merges, grouping,
   ungrouping, deletion, recolor, rename, and theme changes without adding
   broad global canvas hooks.
4. After editing this JS file, bump its `?v=` in `index.html` and sync both
   files to `/home/dn/CURSOR/`.

## XRAY DP Loop Capture -- Local Upload Endpoint -- 2026-05-12

`/XRAY xray_capture_dp` loop captures must keep the dropped-packets workflow
local to the current server:

1. Mirror the requested DUT source interface into the detected loop pair.
2. Capture in the DUT datapath shell with `wbox-cli debug dropped_packets`.
3. Upload the pcap back through XRAY's one-shot local HTTP endpoint on this
   server. Do not use Zohar's dev machine, `/home/dn/capture`, hard-coded
   capture-server passwords, or an interactive SCP prompt.
4. After a successful upload, remove the DUT-side `/var/tmp/...pcap` and
   `/core/logs/...pcap` copies, then remove the temporary port-mirroring
   session.
5. Treat `EXECUTED_VIA_LOOP` as proof only when the local pcap exists and is
   non-empty. If the DUT generated a pcap but upload failed, report
   `EXECUTED_VIA_LOOP_PCAP_FETCH_FAILED`; if the DUT-side pcap is empty/header
   only, report `EXECUTED_VIA_LOOP_NO_PACKET_OUTPUT`.
6. Loop auto-detection should use live LLDP first with canonical
   `show lldp neighbors`. A transient LLDP/auth failure must not hide a known
   DUT-local loop, but the registry is only a fallback after one canonical LLDP
   retry and after confirming both loop ports are currently `enabled/up` with
   `show interfaces description | no-more`. PE-1's validated loop is
   `ge400-0/0/12` -> `ge400-0/0/13` and was proven by the SW-228552 DP pcap
   capture on 2026-05-13.

## REPAIR Skill -- Latest Valid Config Restore Before Upgrade -- 2026-05-12

Use the project skill `.cursor/skills/repair/` when a DNOS device or NCC VM
must be repaired before an upgrade. Trigger phrases include `/REPAIR`,
`REPAIR`, "repair config", "restore latest config", "last valid config", and
"repair before upgrade".

The required workflow is:

1. Target the exact alias the user names. For PE-4 active NCC repair, use
   `kvm108-cl408d-ncc1` (`100.64.4.122`), not the broad `PE-4` cluster alias,
   unless the user explicitly asks for the cluster alias.
2. Read live state first: `show config compare | no-more`,
   `show config | no-more`, `show system | no-more`, and
   `show system stack | no-more`.
3. If live `show config` is stripped or clearly smaller than the cache, select
   the latest valid config from `/home/dn/SCALER/db/configs/<device>/`.
   Default priority is `running.txt`, then newest `pre_delete_backup_*.txt`,
   then newest `pre_upgrade_backup_*.txt`.
4. Dry-run before committing:

```bash
python3 .cursor/skills/repair/scripts/repair_latest_config.py \
  --target kvm108-cl408d-ncc1 \
  --config-device YOR_CL_PE-4
```

5. Execute only after approval or when the user clearly asked to repair now:

```bash
python3 .cursor/skills/repair/scripts/repair_latest_config.py \
  --target kvm108-cl408d-ncc1 \
  --config-device YOR_CL_PE-4 \
  --execute
```

The script uses the existing SCALER `ConfigPusher` file-upload path for large
configs because MCP JSON arguments can exceed the OS argument limit. It still
uses the safe sequence: upload config, `rollback 0`, `load override`,
`commit check`, then `commit` only with `--execute`. It snapshots live-before
and selected candidate config under the device config directory before loading.

The GUI upgrade repair path uses the same candidate principle. The restore
selector in `topology/routes/upgrade.py` scores `running.txt`, registered
`pre_delete_backup`, timestamped pre-delete/pre-upgrade backups, and
`pre_delete_config.txt` by meaningful config line count. It prefers a
significantly fuller valid candidate even when `operational.json` points at a
partial pre-delete snapshot. This is mandatory for PE-4 because a failed
Drain+Deploy attempt can leave the registered snapshot partial while the latest
monitor cache still contains the full last-valid config.

## Link Arrow Tip Visual -- 2026-05-12

Unbound link arrow tips are endpoint handles, not device-edge arrows. Keep them
slimmer than normal quick-link arrowheads:

- Use `LinkDrawing._arrowHeadGeometry(renderLinkWidth, 'unbound')`.
- Prefer color-matched strokes over heavy black outlines.
- Preserve `_arrowTipStart` / `_arrowTipEnd` and `_arrowLength` metadata because
  hit detection depends on it.
- After changing any `topology/*.js` drawing module, bump the matching
  `?v=` cache-buster in `topology/index.html` and sync both files to
  `/home/dn/CURSOR/`.

## Topology MCP Server + Cursor Install Skill -- 2026-05-12

### Purpose

Topology Studio now exposes a shared, authenticated MCP surface so each user's
Cursor can operate their own topology domains, topology files, canvas objects,
bulk/generated topologies, discovery workflow markers, and dry-run wizard plans
directly from chat.

### Architecture

| Layer | Files | Contract |
|---|---|---|
| MCP package | `topology/mcp/*` | Tool registry, bearer-token resolution, per-user dispatch, access helpers, and skill bundle. |
| Bridge mount | `topology/scaler_bridge.py` | Mounts the MCP ASGI app at `/mcp` and the install router at `/api/integration/cursor/*`. |
| Browser-facing proxy | `topology/serve.py` | Proxies `/mcp/sse`, `/mcp/messages/*`, and `/api/integration/cursor/*` to the bridge so users only need the normal Topology Studio host. |
| Install UI | `topology/topology-cursor-install.js` + `.css` | Adds the top-bar **Cursor** button, token generate/rotate/revoke, and copy-prompt flow. |
| Skill bundle | `topology/mcp/skill_bundle/*` | Served as `skill.tar.gz` and installed into `~/.cursor/skills/topology/`. |

### Per-user invariants

1. Every MCP request must resolve a bearer token to a username before any tool
   runs. Tokens can be normal web JWTs or per-user Cursor MCP tokens.
2. Cursor MCP tokens are issued by `user_store.issue_cursor_token(username)`,
   stored only as SHA-256 digests at
   `user_store.user_cursor_token_path(username)`, and written with mode `0600`.
   The raw token is shown once in the install prompt.
3. All tool dispatch enters through `topology/mcp/dispatcher.py`, which calls
   `current_username()` first and role-gates non-read-only tools with
   `user_store.has_role_or_higher(username, "engineer")`.
4. Domain/topology visibility is resolved through existing
   `user_store.list_domains`, `list_topologies`, `load_topology`, and
   `save_topology` behavior. Shared access uses the existing
   `shared_domains` / `shared_topologies` tables only.
5. Mutations require both a global app role (`engineer` or higher) and resource
   write permission (`owner` or `write` share). View-only shares return
   `"permission denied"` without leaking owner-only data.
6. Wizard MCP tools are dry-run by default. Live execution is refused unless
   the caller passes `dry_run=false`, `execute=true`, and the exact
   `confirm_phrase`: `I understand this is destructive on <device-name>`.
7. The MCP package path intentionally extends the upstream Python `mcp` package
   path so `mcp.server.fastmcp` remains importable even though the local plan
   directory is named `topology/mcp`.

### Tool surface

The first-class Cursor tools are:

* `topology_health`
* `topology_list_tools`
* `topology_call_tool`
* `topology_list_domains`
* `topology_list_topologies`
* `topology_get_topology`
* `topology_create_domain`
* `topology_create_topology`
* `topology_save_topology`
* `topology_add_device`
* `topology_batch_update_objects`
* `topology_summarize_topology`
* `topology_validate_topology`
* `topology_list_groups`
* `topology_create_group`
* `topology_set_group_members`
* `topology_disband_group`
* `topology_auto_group`
* `topology_create_mesh`
* `topology_clean_layout`
* `topology_plan_from_network_mapper`
* `topology_plan_from_dnos_json`
* `topology_create_from_plan`
* `topology_run_image_upgrade`

`topology_call_tool` reaches the full v1 registry, including:
read-only inspect, domain/topology CRUD, object CRUD, mesh/chain/star/spec
generation, deterministic layout, manual groups, validation/summarization,
preview-only import planning from already-fetched Network Mapper or dnos-config
JSON, discovery workflow markers, and dry-run wizard proxies.

Import tools intentionally do not call Network Mapper or dnos-config themselves.
The slash command or installed skill should call the source MCP first, pass the
returned JSON into `topology_plan_from_network_mapper` or
`topology_plan_from_dnos_json`, review validation/warnings, and save only with
`topology_create_from_plan` after the preview is accepted.

### Install flow

1. User opens the web app and clicks **Cursor** in the top bar.
2. The modal calls `POST /api/integration/cursor/token` via
   `window.TopologyAuth.authFetch`.
3. The backend rotates the per-user token and returns a copy-paste prompt.
4. The prompt instructs Cursor to add the `topology` SSE MCP server at
   `/mcp/sse`, download `/api/integration/cursor/skill.tar.gz`, reload Cursor,
   and verify with `topology_health`.

### Slash command and auth routing

The repo-level slash command is `.cursor/commands/TOPOLOGY.md`, backed by the
project skill `.cursor/skills/topology/SKILL.md`. `/TOPOLOGY` is the operator
entry point for checking whether the MCP mount is alive, why Cursor does not see
the server, and how to install the per-user token safely.

`scaler_bridge.py` must not run its JWT-only middleware in front of `/mcp/*` or
`/api/integration/cursor/*`. Those paths intentionally accept both normal app
JWTs and per-user Cursor MCP tokens through `TopologyMcpAuthMiddleware` or the
integration route dependency. If unauthenticated `/mcp/sse` returns `401`, the
server is alive and protected. If it returns `404`, the bridge mount or
browser-facing `serve.py` proxy is stale or missing.

### MCP SSE stability -- 2026-05-13

Do not use Starlette/FastAPI `BaseHTTPMiddleware` or `@app.middleware("http")`
around the mounted Topology MCP app. The MCP SSE transport is a mounted
streaming ASGI app; `BaseHTTPMiddleware` can corrupt the ASGI message ordering
and crash uvicorn with:

```text
AssertionError: Unexpected message: {'type': 'http.response.start', ...}
```

`topology/mcp/auth.py::TopologyMcpAuthMiddleware` and
`topology/scaler_bridge.py::JwtAuthMiddleware` are plain ASGI middleware for
this reason. Keep them plain ASGI.

`serve.py` supervision must probe child health endpoints with `GET`, not `HEAD`.
`discovery_api.py` does not implement `HEAD`, and earlier `HEAD` probes also
misclassified protected/healthy bridge endpoints as dead, causing repeated
`Address already in use` restart loops that made `/mcp/sse` look like it was
crashing.

### MCP-created topology visibility -- 2026-05-12

The Topologies dropdown still lists owner-domain topologies through the legacy
`/api/sections/<section_id>/topologies` file tree, while the Topology MCP writes
the canonical multi-user SQLite domain/topology rows via `user_store`. To keep
MCP-created diagrams visible immediately after browser refresh, `mcp.access`
mirrors every owner-side MCP save into the matching per-user section file and
updates the `_multiuser_mirror__<section>.json` mapping atomically. If an older
MCP-created topology exists only in SQLite, run
`topology_repair_legacy_visibility` through `topology_call_tool` (or the
one-off repair script in `topology/scripts/repair_topology_mcp_visibility.py`)
to backfill the legacy-visible file.

### Verification

Run:

```bash
cd /home/dn/drivenets-topology-studio
PYTHONPATH=topology python3 topology/tests/test_topology_mcp_unit.py
PYTHONPATH=topology python3 -m py_compile topology/api/auth/user_store.py topology/mcp/__init__.py topology/mcp/auth.py topology/mcp/access.py topology/mcp/dispatcher.py topology/mcp/server.py topology/mcp/tools/*.py topology/routes/integration_cursor.py topology/scaler_bridge.py topology/serve.py topology/tests/test_topology_mcp_unit.py
```

PR-gate grep checklist:

```bash
cd /home/dn/drivenets-topology-studio/topology
grep -rn 'expanduser("~/\.topology' mcp/ routes/integration_cursor.py
grep -rn 'open("/tmp/' mcp/ routes/integration_cursor.py
grep -rn 'TOPOLOGY_USERS_BASE' mcp/ routes/integration_cursor.py
grep -rnE 'config_path|config_file' mcp/ routes/integration_cursor.py
```

All four should be empty for new MCP code.

## Canonical delete+deploy flow -- delete -> load 3 tarballs (GI) -> deploy -- 2026-06-14

**The one true DNOS delete+deploy order is:**

```
1. request system delete            (wipes DNOS, reboots into GI)
2. <reboot, reconnect in GI mode>
3. request system target-stack load <DNOS url>     (in GI)
   request system target-stack load <GI url>       (in GI)
   request system target-stack load <BaseOS url>   (in GI)
4. request system deploy system-type <T> name <N> ncc-id <id>
```

**Images are NEVER loaded before `request system delete`.** `request system
delete` wipes the DNOS target stack, so any pre-delete `target-stack load` is
wasted work and contradicts the documented flow. Every location must follow
delete -> load -> deploy:

| Location | Status |
|---|---|
| `routes/upgrade.py` `_run_delete_deploy_upgrade` (GUI backend) | Phase 4 delete -> Phase 5 wait GI -> Phase 6 load -> Phase 6b verify -> Phase 7 deploy. **Phase 3.5 pre-delete push REMOVED 2026-06-14.** |
| `interactive_scale.py` wizard (CLI) | Already delete -> load -> deploy (main + fallback flows). |
| `device_upgrade.py` `DeviceUpgrader` | `upgrade_stack()` is IN-PLACE only. For wipe upgrades use `delete_dnos()` then load then `deploy_from_gi()` -- never load before delete. |
| `scaler-gui-upgrade.js` | Operator labels read `delete -> load 3 tarballs (GI) -> deploy`. |

**Why the 2026-05-12 pre-delete push was removed without losing safety:** the
two goals it served are both preserved by other gates --

* *Empty url_list abort* -> enforced at Phase 1 by `_assert_url_list_in_job`
  (hard-fail BEFORE delete if there are no images to push).
* *Stale-image redeploy guard* -> enforced at Phase 6b: after the GI load,
  `show system stack` + `_verify_stack_targets_for_urls` RAISE (blocking the
  Phase 7 deploy) if any selected component is missing/mismatched in the
  Target column. A stale target can therefore never reach `request system
  deploy`; the worst case is a safe blocked deploy the operator retries.

The 2026-05-12 section below is retained as historical context for the
post-reboot active-NCC re-detection fix (still in force); only the
*pre-delete target-image push* (Phase 3.5 / Bug 0/1) is superseded.

### GI-mode NCC access -- PREFER DIRECT SSH (2026-06-14, live PE-4 recovery)

The single biggest reliability win for cluster (KVM-NCC) upgrades: **reach the
GI CLI by SSHing DIRECTLY to the active NCC VM**, not via the KVM hypervisor +
`virsh console` + `dncli` chain.

```bash
ssh dnroot@kvm108-cl408d-ncc1      # NCC VM hostname -> DNS -> 100.64.4.122
# -> lands STRAIGHT in:  GI(<date>)#     (dnroot/dnroot)
GI# show system        # -> "Active NCC: kvm108-cl408d-ncc1"
```

Traps proven live during the PE-4 build#8 recovery, and the fixes now in code:

1. **`dncli` from an NCC's own bash returns a BOGUS** `Connection failure:
   either you are trying to connect to the standby NCC or Drivenets' CLI is
   N/A` **on BOTH NCCs.** It is NOT a reliable active/standby signal. Use
   `show system` over a direct SSH to find `Active NCC:` instead.
2. **`_looks_like_kvm_host_shell_output` regex false-matched NCC VM prompts**
   (`dn@kvm108-cl408d-ncc1:~$`) because they start with `kvm108`. A standby-NCC
   error was misread as a KVM-host-shell error, so the active-NCC pivot never
   fired. FIXED: exclude any prompt host containing `ncc`.
3. **The standby pivot couldn't disambiguate** when both NCC VMs run (the
   probe returns `running[0]`). FIXED: `_dncli_pivot_after_standby_error` now
   derives the current NCC from operational.json and toggles to the other half
   of the 2-NCC cluster; `_seed_active_ncc_hint` pins the reconnect to it.
4. **Delete-reboot ROTATES the NCC host key.** A strict-host-key direct SSH
   fails (you must `ssh-keygen -R <ncc>`); use paramiko `AutoAddPolicy` without
   `load_system_host_keys()`.
5. **Stale `virsh console` sessions** (left by a prior run that closed SSH
   without `Ctrl+]`) hold the console lock, so a new `virsh console` silently
   stays at the **KVM host shell** -> every GI command runs on the hypervisor
   and fails. `sudo pkill -f 'virsh console'` on the KVM host, or just use
   direct SSH.

**Pre-delete is TAKE-ONLY (2026-06-14):**
`_maybe_repair_stripped_config_before_delete` now ONLY selects the best config
to save as `pre_delete_backup` -- it NEVER pushes/commits to the live device
before delete (that was a multi-minute stall committing a config `request
system delete` immediately wipes). Restore happens POST-deploy from the backup
file via `_post_deploy_restore_from_file` (ConfigPusher over direct SSH).

Full routing + lab specifics: `.cursor/rules/dnos-upgrade-flow.mdc`.

## Image Upgrade Wizard -- Drain+Deploy Target-Image Push + Post-Reboot Re-detection Fix -- 2026-05-12

> **SUPERSEDED (2026-06-14):** the "pre-delete target-image push" / Phase 3.5
> described in this section has been REMOVED. See "Canonical delete+deploy
> flow" above. The post-reboot active-NCC re-detection fix in this section
> remains in force.

### Symptom (live incident, 2026-05-12 12:55 -> 12:57 UTC)

The Image Upgrade Wizard's Drain+Deploy (D+D) path for `YOR_CL_PE-4`
(CL-86 cluster, mgmt IP `100.64.10.22`) crashed mid-flight with:

```
[WARN] dncli attempted from KVM host shell, not NCC shell:
       Connection failure: either you are trying to connect to the standby NCC
       or Drivenets CLI is N/A
[ERROR] GI CLI unavailable and NCC bash could not be verified;
        refusing to send target-stack commands on an unclassified channel
```

The device was left in GI mode with the GI target stack showing the
STALE image `26.2.0.4_priv.usirota_evpn_vpls_irb_4` (a leftover from a
previous provisioning -- NOT what the operator selected in the wizard).
Recovery required the operator to manually SSH to the active NCC,
run `request system target-stack load <URL>` for each component, verify
`show system stack`, then `request system deploy ...`.

### Four independent bugs stacked

0. **(CRITICAL) Target-image push step was MISSING from the D+D state
   machine.** Today's log went from "Config backup saved" straight to
   "Device input: request system delete" with NO
   `request system target-stack load <url>` step in between. When the
   device came back in GI mode, `show system stack` showed the STALE
   pre-existing image as both Current AND Target (REPLICATED). The
   only image push happened POST-delete in Phase 6, but if the post-
   reboot dncli flow failed (Bugs 2/3 below), Phase 6 never ran and
   the device sat in GI with a stale target. A subsequent
   `request system deploy ...` would have redeployed the OLD image
   verbatim. This is the root cause of "the wizard deployed the wrong
   image" complaints.

1. **Hardcoded `ncc_id=1` for PE-4** in `topology/routes/upgrade.py
   :_normalize_deploy_params` (legacy `pe4_deploy_default` branch). The
   guard's intent was to backfill the CL-86 deploy contract, but
   `ncc_id` is NOT immutable -- `request system delete` reboots the
   currently-active NCC and the cluster fails over to the other one.
   Hardcoding `ncc_id=1` meant the script kept targeting NCC-1 after
   the cluster had already failed over to NCC-0.

2. **No trust gate at Execute time.** The wizard accepted Execute
   with `active_ncc_source='pe4_deploy_default'` -- a legacy sentinel
   that is NOT in `_TRUSTED_ACTIVE_NCC_SOURCES`. Without a fresh
   trusted probe, the deploy path could not know which NCC was
   actually active.

3. **Shell-context mis-classification.** `_ensure_ncc_bash` returned
   True when the channel was actually at the KVM host shell
   (`kvm108`), not the NCC bash shell. `_probe_ncc_bash` only checks
   that the channel answers a `printf` probe; both NCC bash and the
   KVM host bash answer it identically. The next `dncli` invocation
   ran on the host instead of the NCC -- producing the "standby NCC"
   message that misled the operator into thinking the cluster was
   broken when in fact the channel was on the wrong machine.

### Fixes (`topology/routes/upgrade.py` + `topology/routes/bridge_helpers.py` + `topology/scaler-gui-upgrade.js`)

| # | Layer | Change |
|---|---|---|
| 1 | backend | `_normalize_deploy_params` no longer hardcodes `ncc_id=1` for PE-4. The CL-86 system_type and YOR_CL_PE-4 deploy_name guards are kept (they are immutable cluster facts); `ncc_id` is left to whatever the trusted upstream probe established. |
| 2 | backend | New `_assert_active_ncc_trusted_for_destructive_op(device_id, plan, scaler_hostname)` helper raises `HTTPException(412)` from `image_upgrade_execute` when a cluster device's plan does NOT carry an `active_ncc_source` in `_TRUSTED_ACTIVE_NCC_SOURCES`. The error message explicitly says "Click Re-detect in the upgrade wizard to refresh the live NCC probe and then retry Execute." |
| 3 | backend | New `_ncc_bash_fingerprint_via_hostname(chan)` probe runs `printf '<MARKER>_%s\\n' "$(hostname)"` and asserts the hostname matches `*-ncc[01]`. The KVM host's hostname is `kvm108` (no `-ncc` suffix) so the host-shell case is now caught. `_ensure_ncc_bash` calls this AFTER `_probe_ncc_bash` succeeds; if the hostname is wrong, it falls through to the exit-and-retry path and ultimately returns False so the caller refuses to send `dncli`/`target-stack` commands. |
| 4 | backend | New `_probe_libvirt_active_ncc_post_reboot(scaler_hostname)` re-probes libvirt via SSH to the KVM host once GI mode is confirmed after `request system delete`. The function returns `(active_ncc_vm, source, ncc_id)` and stamps `active_ncc_source="post_reboot_virsh_probe"` into `operational.json`. Wired into `_run_delete_deploy_upgrade` between "GI confirmed" and "Phase 5b preflight" so every subsequent `dncli` / `request system deploy` call targets the live active NCC, not the pre-delete one. |
| 5 | backend | `_TRUSTED_ACTIVE_NCC_SOURCES` extended with `"post_reboot_virsh_probe"` so the post-reboot re-detection writes a trusted source value. |
| 6 | frontend | The Execute click handler in `scaler-gui-upgrade.js` runs a client-side mirror of the trust gate before `ScalerAPI.imageUpgrade`. Same prefix list as the backend. Operator sees an immediate "Click Re-detect ..." toast instead of a round-trip 412. |
| 7 | frontend | The Wait & Upgrade click handler has the same client-side trust gate. |
| 8 | frontend | The Wait & Upgrade silent fill `ncc_id=1` + `active_ncc_source='pe4_deploy_default'` was REMOVED. Only the immutable cluster facts (CL-86 / YOR_CL_PE-4) are still backfilled. |
| 9 | frontend | The cached-context fallback `else { ncc_id = 1; active_ncc_source = 'pe4_deploy_default'; }` was replaced with `active_ncc_source = 'untrusted_no_probe'` so the trust gate fires deterministically. |
| 10 | backend (NEW, Bug 0) | New `_push_target_image_to_dnos_stack_pre_delete(job_id, device_id, chan, url_list, stage_times, _log, replicate_timeout=600, poll_interval=15)` in `routes/upgrade.py`. Calls `_load_images_on_channel(..., ensure_gi_cli=False)` (DNOS-mode push -- dncli is still up), then polls `show system stack | no-more` via `_verify_stack_targets_for_urls` until every selected component shows in the Target column. The active NCC auto-replicates to the standby NCC and all NCPs / NCFs (per `~/SCALER/dnos_cheetah_docs/Request Commands/request system target-stack load.rst` line 28). Raises `RuntimeError` after `replicate_timeout` (default 10 min) if any component still missing -- caller MUST treat as abort and skip `request system delete`. |
| 11 | backend (NEW, Bug 0) | Phase 3.5 wired into `_run_delete_deploy_upgrade` BETWEEN Phase 3 (`_detect_deploy_params`) and the `operational.json` `_delete_pending` quarantine stamp. Order is critical: the on-disk delete marker is NOT written if the pre-delete push aborts, so a failed push leaves the device in DNOS with its old target intact and the wizard's recovery logic does not see a phantom in-progress delete. |
| 12 | backend (NEW, rule d) | New `_assert_both_nccs_reachable_for_destructive_op(device_id, scaler_hostname)` helper. Calls the existing `_cluster_preflight_check` (libvirt enum of NCC VMs) and raises `HTTPException(412)` if fewer than `len(vms_defined)` VMs are `running`. Wired into `image_upgrade_execute` alongside the trust gate. Refuses the destructive command when the standby NCC is already shut off -- otherwise the delete-reboot would take the whole device offline. |
| 13 | backend (NEW, auto-pivot) | `_enter_dncli_from_bash(chan, _log, signals=None)` now detects the "either you are trying to connect to the standby NCC" / "Drivenets CLI is N/A" pattern via the module-level `_STANDBY_NCC_ERROR_RE` and `_looks_like_standby_ncc_error(text)` predicate. When detected it stamps a clear `STANDBY_NCC_REDIRECT_REQUIRED` WARN and sets `signals["standby_redirect"] = True` so callers can react. New `_dncli_pivot_after_standby_error(scaler_hostname, current_ncc_id, _log)` helper re-probes libvirt and returns `(needs_pivot, new_ncc_id)`. `_preflight_gi_health` wires the auto-pivot at TWO sites (the bash-direct branch and the gi-manager-healthy retry branch); both share the existing `_reconnect_attempted` guard so the retry is bounded to "at most once". |
| 14 | frontend (NEW) | Trust-prefix arrays at line ~3322 (`_NCC_TRUST_PREFIXES_R`) and line ~3865 (`_NCC_TRUST_PREFIXES`) now include `post_reboot_virsh_probe` -- previously only the Execute-gate array at line ~4316 (`_UPG_TRUST_PREFIXES`) had it. All three frontend arrays + the backend `_TRUSTED_ACTIVE_NCC_SOURCES` tuple are now in lockstep. |

### D+D State machine (post-fix, 2026-05-12)

```
Phase 1: connect_for_upgrade (SSH/console/virsh) ............... routes/upgrade.py:4449
Phase 2: pre-delete config snapshot ............................ routes/upgrade.py:4490..
Phase 3: detect deploy_params (system_type/name/ncc_id) ........ routes/upgrade.py:4607
Phase 3.5 (NEW): _push_target_image_to_dnos_stack_pre_delete ... routes/upgrade.py:4625
   -> load each selected URL via `request system target-stack
      load <url>` while still in DNOS mode (active NCC owns the
      replicate). Poll `show system stack | no-more` until
      _verify_stack_targets_for_urls reports zero missing. ABORT
      if missing after replicate_timeout (default 600s); never
      reach Phase 4.
Phase 4: request system delete (reboots NCC, cluster failover) . routes/upgrade.py:~4720
Phase 5: wait for GI mode (~10 min) ............................ routes/upgrade.py:~4830
Phase 5a-post: _probe_libvirt_active_ncc_post_reboot ........... routes/upgrade.py:4828
Phase 5b: _preflight_gi_health (auto-pivot on standby error) ... routes/upgrade.py:5884
Phase 6: _load_images_on_channel(..., ensure_gi_cli=True) ...... routes/upgrade.py:~4870
Phase 6b: _verify_stack_targets_for_urls in GI .................. routes/upgrade.py:~4882
Phase 7: request system deploy ................................. routes/upgrade.py:~4946
Phase 8: wait for DNOS reboot + verify versions ................. routes/upgrade.py:~5050+
```

### Pre-flight gate (4 hard-fail rules, enforced in `image_upgrade_execute`)

Before any destructive command goes out, the API surface refuses with
`HTTPException(412)` (visible to the wizard as an immediate red toast
with "Click Re-detect and retry") on ANY of:

| Rule | Helper | Where |
|---|---|---|
| (a) Selected image not on device | `_assert_url_list_for_dd_upgrade` (URL validation via HEAD 200) + `_assert_url_list_in_job` (in-job defense-in-depth) | `image_upgrade_execute` + `_run_delete_deploy_upgrade` Phase 1 |
| (b) GI stack target NOT confirmed-updated | `_push_target_image_to_dnos_stack_pre_delete` raises `RuntimeError` mid-job; outer caller turns it into the wizard's "FAILED: pre-delete target-image push did not confirm REPLICATED" device-state message | `_run_delete_deploy_upgrade` Phase 3.5 |
| (c) `active_ncc_source` untrusted | `_assert_active_ncc_trusted_for_destructive_op` | `image_upgrade_execute` |
| (d) Both NCCs reachable pre-delete | `_assert_both_nccs_reachable_for_destructive_op` | `image_upgrade_execute` |

(a) and (c) and (d) are API-boundary gates; (b) is necessarily in-job
because the push happens AFTER deploy_params detection.

### Auto-pivot retry contract

* Trigger: any `_enter_dncli_from_bash(chan, _log, signals=s)` call
  where `s.get("standby_redirect")` is True.
* Reaction: caller invokes `_dncli_pivot_after_standby_error(
  scaler_hostname, current_ncc_id, _log)` which re-probes libvirt
  via `_probe_libvirt_active_ncc_post_reboot`.
* If the probe returns `(needs_pivot=True, new_ncc_id in (0, 1))`,
  the caller closes the current SSH and calls
  `connect_for_upgrade(scaler_hostname, timeout=60)` (which discovers
  the active NCC anew via its own libvirt + dncli health gates),
  then RETRIES the dncli entry ONCE on the new channel.
* If the probe says `needs_pivot=False` (same NCC, or libvirt can't
  see any running NCC), no pivot is attempted -- the caller surfaces
  a clear "GI CLI unreachable" error to the operator instead of
  looping.
* The retry-once guarantee is enforced by `_reconnect_attempted`
  inside `_preflight_gi_health`. A second standby-redirect after the
  pivot raises `RuntimeError` immediately.

### Recovery cheat-sheet (kept here for future repeats)

The operator-facing cheat-sheet for an in-progress D+D crash that
left the device in GI with a stale target stack is:

1. SSH to the KVM host of the cluster (e.g. `dn@kvm108`).
2. `sudo virsh list --all` -- find which `*-ncc0` / `*-ncc1` VM is
   `running`. After a `request system delete` of NCC-1, the active
   NCC is almost always NCC-0.
3. `sudo virsh console <vm>` -- log in as `dn` / `drivenets`. Confirm
   hostname ends in `-ncc0` or `-ncc1` via `hostname`.
4. `dncli` -- log in as `dnroot` / `dnroot`. If you see "Connection
   failure: either you are trying to connect to the standby NCC",
   ESC out, ctrl-] to leave the virsh console, and console the OTHER
   NCC VM.
5. From the GI prompt: `show system stack | no-more` to confirm the
   current vs target images.
6. For each component the operator wanted to push, run:
   `request system target-stack load <URL>` and answer `yes`.
   Poll with `show system target-stack load`.
7. Re-verify with `show system stack` -- Target column must show
   the NEW image, sync status `REPLICATED`.
8. Launch: `request system deploy system-type CL-86 name YOR_CL_PE-4 ncc-id <0|1>`.
9. Wait ~10 min for DNOS to come back; verify via `show system version`.

The cheat-sheet is intentionally not embedded in the wizard error
text because most fields are dynamic; the wizard error directs the
operator back to the Re-detect button which is always sufficient
when the agent has not yet started destructive ops.

Post 2026-05-12 hardening: steps 5-7 are now performed by Phase 3.5
BEFORE the delete, so an operator hitting this path manually should
be rare. The cheat-sheet remains for ops who need to recover from a
pre-fix incident.

### Multi-user contract preserved

* No new global storage. `_push_target_image_to_dnos_stack_pre_delete`
  writes only to the per-device push-job `device_state` dict (already
  per-job in `_push_jobs` and per-user via JWT-scoped `_get_request_user`)
  and to the per-device `operational.json` via the existing atomic
  `_update_ops_dd` mutator. No new SQLite, no new global JSON.
* `_TRUSTED_ACTIVE_NCC_SOURCES` lives in `bridge_helpers.py` and is
  shared by every helper; the frontend prefix list mirrors it
  verbatim in THREE sites (line ~3322 `_NCC_TRUST_PREFIXES_R`,
  line ~3865 `_NCC_TRUST_PREFIXES`, line ~4316 `_UPG_TRUST_PREFIXES`).
  If the whitelist is ever extended again, update all FOUR places
  (one Python tuple, three JavaScript arrays) in the same commit.
* `_assert_both_nccs_reachable_for_destructive_op` reuses the existing
  `_cluster_preflight_check` libvirt probe; no new credentials, no new
  SSH paths.
* No new MCP servers. No new SQLite DBs.

### PR-gate grep checklist (all clean as of this commit)

```bash
cd /home/dn/drivenets-topology-studio/topology
grep -n 'expanduser("~/\.' routes/upgrade.py routes/bridge_helpers.py
grep -n 'open("/tmp/' routes/upgrade.py routes/bridge_helpers.py
grep -nE 'config_path|config_file' routes/upgrade.py routes/bridge_helpers.py | grep -v user_
grep -n 'def _require_auth' serve.py
```

Nothing new flagged; the trust gate, pre-delete push, NCC-reachable
gate and auto-pivot add no new per-user paths and no new globals.

### Canonical D+D command reference (proven on PE-4 manual recovery)

From `~/SCALER/dnos_cheetah_docs/Request Commands/request system
target-stack load.rst` (the DNOS-mode push, line 28: "In a cluster,
the active NCC replicates a target stack to the standby NCC") and
`~/SCALER/scaler/interactive_scale.py::_load_images_on_channel`
(the implementation the new helper wraps):

```
# Phase 3.5 (pre-delete, DNOS mode, on active NCC)
request system target-stack load <url-dnos>
request system target-stack load <url-gi>
request system target-stack load <url-baseos>
# answer yes for each, then Ctrl+C to background the download

# Verify -- poll until every selected component shows in Target column
show system stack | no-more

# Phase 4 (only after every component verified in target)
request system delete
yes

# Phase 5 / 5a / 5b: wait for GI mode, re-probe libvirt for active
# NCC, pivot virsh console if needed (handled automatically by the
# orchestrator).

# Phase 6 (post-GI re-push; idempotent because the target survives
# the delete-reboot, so this is usually a no-op)
request system target-stack load <url-dnos>
request system target-stack load <url-gi>
request system target-stack load <url-baseos>

# Phase 7 (final deploy)
request system deploy system-type CL-86 name YOR_CL_PE-4 ncc-id <0|1>
```

Note: there is no `set system stack target <image>` config-mode
command in the DNOS canonical syntax for this flow; the operator-
selected images are pushed via the operational
`request system target-stack load <url>` per-URL form. The MCP
`dnos_cmd_search` and the `dnos_cheetah_docs` corpus both confirm
this. If you find a future doc that introduces `set system stack
target`, verify on the live device first before adopting -- it would
likely supersede the `request system target-stack load` flow.

## Image Upgrade Wizard -- PE-4 / CL-86 Cluster Detection Fix -- 2026-05-12

### Symptom

At Step 5 (Upgrade Plan) of the Image Upgrade Wizard, `YOR_CL_PE-4` rendered
with `Mode = ?`, `DNOS = -`, `GI = -`, `BASEOS = -`, `Status = Unknown`. The
Upgrade Plan table showed `Current = -`. The Deploy NCC dropdown printed
`NCC-1 (default -- verify!)` and the wizard fired the orange warning
"Active NCC not detected -- click Re-detect or verify manually before
Execute." PE-1 (single-NCP) and RR-SA-2 (cluster) both detected correctly,
so the regression was scoped to PE-4's specific resolver path.

### Root cause (one paragraph)

PE-4's `~/SCALER/db/configs/YOR_CL_PE-4/operational.json` held a stale
`mgmt_ip = 100.64.4.98` (an older lab-deploy address). The DNAAS-authoritative
IP for PE-4 is `100.64.10.22` (`dnos_list_devices` MCP tool). The scaler ops
index (`_build_scaler_ops_index`) ingests each per-device `operational.json`
and is the **primary** source consulted by `_resolve_mgmt_ip` -- the
`device_inventory.json` cache only wins at step 7 (fallback). The cluster
inventory entry for PE-4 has `mgmt_ip = ""` because DNAAS does not publish a
device-level mgmt IP for multi-NCC clusters (each NCC has its own VIP). So
`_resolve_mgmt_ip` returned `100.64.4.98`, the SSH probe in
`_check_single_device_status` failed (then cascaded into a slow virsh-console
fallback that timed out under the wizard's 45-second budget), and the
exception path returned a stub row with empty fields. Compounding the
problem, the frontend hardcoded `active_ncc_source = 'pe4_deploy_default'`
whenever the entry was a PE-4 deploy target, **even if the backend had already
surfaced a trusted `active_ncc_source` value from operational.json** --
`pe4_deploy_default` is not in the NCC-trust prefix list, so the wizard fired
the orange "Active NCC not detected" warning even when the cluster had a
fully-verified active NCC sitting in cache.

### Fixes (minimal, targeted)

| Layer | File | Change |
|---|---|---|
| Operational cache | `~/SCALER/db/configs/YOR_CL_PE-4/operational.json` | Atomic write -- `mgmt_ip` corrected from stale `100.64.4.98` to authoritative `100.64.10.22`. Preserved `active_ncc_vm`, `active_ncc_source`, `system_type`, `dnos_version`, `gi_version`, `baseos_version` etc. |
| Bridge route | `topology/routes/upgrade.py` (`image_upgrade_plan`) | When `_check_single_device_status` returns an empty mode + empty current_version pair (i.e. SSH timed out), fall back to fresh operational.json data (`active_ncc_vm`, `active_ncc_source`, `system_type`, `dnos_version` etc.) instead of stamping the "Unknown" stub. Continues to surface `active_ncc_vm` and `active_ncc_source` in `deploy_params` so the frontend trust list can evaluate them. |
| Frontend wizard | `topology/scaler-gui-upgrade.js` (Step 5 PE-4 fallback block) | Softened the PE-4 `pe4_deploy_default` hardcode: only stamps it when the backend gave us **neither** `active_ncc_vm` **nor** `active_ncc_source`. If the backend already populated either field, the wizard mirrors the backend's value into `deploy_params.ncc_id` (parsed from the `kvm108-cl408d-nccN` VM name) and respects the trusted source tag. Cluster + sys-type stamps untouched -- they remain a safety net for legacy backends. |
| Frontend timeout | `topology/scaler-gui-upgrade.js` (verifyPlan / `_planTimeout`) | Extended the wizard-side abort timeout from 45s to 90s. A cluster device whose mgmt SSH password auth fails falls through to the virsh-console fallback in `connect_for_upgrade`, which alone can spend 20-30s per device. With multiple devices in flight the 45s budget reliably tripped, painting the "current = -" stub. The server-side per-step timeouts in `_check_single_device_status` remain unchanged and still bail far sooner than 90s when the device is genuinely unreachable -- the 90s budget only allows the virsh fallback to land. |
| Cache buster | `topology/index.html` | Bumped `scaler-gui-upgrade.js?v=20260512m-pe4-cluster-detection`. |

### Active-NCC detection contract (going forward)

The frontend's NCC trust whitelist now lives at TWO matched declarations
(`_NCC_TRUST_PREFIXES_R` near line 3260 and `_NCC_TRUST_PREFIXES` near line
3796). Both MUST stay in sync. The current list:

```
['kvm_', 'virsh_console_verified',
 'pre_upgrade_snapshot', 'pre_upgrade_backup',
 'scaler_db_cache', 'topology_virsh_probe',
 'upgrade_start_snapshot']
```

Any source not in this list (including `context_unverified`,
`pe4_deploy_default`, scaler-raw-write dumps that dropped provenance) renders
the active-NCC tag as `(unverified)` or `(default -- verify!)` and DOES fire
the orange warning. New code paths that surface an NCC value MUST stamp the
source with a string starting with one of those prefixes (preferred:
`kvm_virsh_probe` for fresh signals, `upgrade_start_snapshot` for frozen
snapshots taken at Step 5 entry). The backend `routes/upgrade.py` route
forwards both `active_ncc_vm` and `active_ncc_source` from operational.json
verbatim -- it does not synthesise either field.

### Resolver doctrine for cluster devices

The cluster mgmt IP resolver follows this precedence today (see
`_resolve_mgmt_ip` in `topology/routes/bridge_helpers.py` ~line 908):

1. `ssh_host` is a live IP in the ops index -> use it.
2. `ssh_host` is a stale IP -> stash as last-resort fallback, continue.
3. `ssh_host` as serial/hostname -> ops index lookup.
4. **`device_id` exact match in ops index** (this is the primary cluster path).
5. Current user's monitored backend registry.
6. Discovery API `_resolve_device(device_id)`.
7. `device_inventory.json` fuzzy match (DNAAS cache; empty for clusters).
8. Partial name match in ops index.
9. Stale `ssh_host` fallback.

Because cluster entries in `device_inventory.json` have `mgmt_ip = ""`, the
ops index is the only authoritative source for cluster mgmt IPs. The fix
contract is therefore: **operational.json MUST be kept in sync with DNAAS
MCP `dnos_list_devices`**. When divergence is detected (the ops index returns
an IP but the SSH probe fails and the DNAAS MCP can be reached), the
correction is to atomically rewrite `~/SCALER/db/configs/<DEVICE>/operational.json`
with the authoritative IP, NOT to override the resolver chain. The
`_resolve_mgmt_ip` chain itself is correct -- it's the cache feeding it that
was stale.

### Live device evidence (PE-4, captured 2026-05-12 via dnos-config MCP)

```
dnos_list_devices:
  yor_cl_pe_4 -> PE-4 ip=100.64.10.22 platform=NCC alias=[YOR_CL_PE-4, PE-4]

operational.json (post-fix):
  mgmt_ip: 100.64.10.22
  active_ncc_vm: kvm108-cl408d-ncc1
  active_ncc_source: upgrade_start_snapshot
  system_type: CL-86
  dnos_version: 26.2.0.4_priv.u
```

`active_ncc_source = upgrade_start_snapshot` IS in the trust list, so the
wizard now renders `(pre-upgrade)` next to NCC-1 and does NOT show the
orange "Active NCC not detected" banner.

### Regression check (mental trace)

| Device | Path through `_resolve_mgmt_ip` | Outcome |
|---|---|---|
| PE-1 (single NCP, `100.64.4.200`) | ops index step 4 -> `100.64.4.200` | SSH probe succeeds in ~2s; mode/dnos/gi/baseos populate; status `verified_via_ssh`. No regression. |
| PE-4 (CL-86 cluster, `100.64.10.22`) | ops index step 4 -> `100.64.10.22` (post-fix) | SSH probe lands; or, if it times out, the new cached-fallback in `image_upgrade_plan` returns `system_type=CL-86`, `dnos_version=26.2.0.4_priv.u`, `active_ncc_vm=kvm108-cl408d-ncc1`. Status badge `verified_via_ssh` or `cached`. The orange NCC warning does not fire because `upgrade_start_snapshot` is trusted. |
| RR-SA-2 (cluster, `100.64.10.211`) | ops index step 4 -> `100.64.10.211` | Already correct -- no change required; the cluster code path in `_check_single_device_status` was never broken for RR-SA-2 because its operational.json was kept in sync. No regression. |

### What NOT to do next time

- Do NOT bypass the resolver chain for "cluster preference" -- the resolver
  is correct. The bug was a stale cache feeding it.
- Do NOT add a new resolver-side override that reads `device_inventory.json`
  first for cluster devices -- DNAAS does not populate `mgmt_ip` there for
  clusters and you will get an empty string.
- Do NOT widen the NCC trust prefix list to accept `pe4_deploy_default` or
  any other generic "default" tag -- the trust list is the contract that
  prevents the wizard from quietly committing the wrong NCC.
- Do NOT shorten the 90s frontend timeout back to 45s -- the virsh-console
  fallback genuinely needs the wider budget. The real fix is making sure the
  primary SSH path works (correct mgmt_ip), so 90s becomes a buffer rather
  than a normal-path requirement.
- Do NOT swallow SSH probe exceptions silently in the upgrade plan -- always
  surface `_planError` in the wizard chrome so the operator sees WHY a row
  is empty.

## Text-box Edge-Stretch + Reflow -- 2026-05-12

### What changed

Text boxes now resize from the bounding-box **edges** the same way a DOM
textarea or an OS window resizes -- there are NO visible dot-handles. The
prior interrupt that added eight shape-style dots to text boxes has been
withdrawn after user feedback ("the model is closer to how a DOM textarea
or a window-resize edge works -- no small visible dot-handles required").
Shapes are unaffected; their 8-handle resize affordance still ships
unchanged from `topology-shape-drawing.js`.

The redesign also enforces a hard containment invariant: rendered text
inside a text box is **always** visually contained within the box's
filled rectangle / hitbox bounds, in every state (display, mid-resize,
post-resize, post-edit, post-zoom, post-font-change). The screenshot bug
that triggered this work -- an "IRB" box with `IP=`, `100.10`, `0.100.1`
spilling outside the dark-navy fill -- is now physically impossible by
construction.

### How it works

| Concern | Implementation |
|---|---|
| **Edge-zone hit detection** | `ObjectDetection.findTextHandle` builds a 5-screen-px band hugging each side / corner of the bbox in the text's local frame (rotation-corrected). Inside that band the function returns `{type:'resize', handle:'n'/'s'/'e'/'w'/'nw'/'ne'/'sw'/'se', cursor:...}`. Outside the band but inside the bbox, it returns `null` so body drag-to-move keeps working. The band width is clamped to at most 45 % of the smaller dimension so tiny boxes still have a body region. |
| **Cursor mapping** | Mouse-move's hover branch passes the handle id through `MouseMoveHandler._rotatedCursor` (already used by shapes) so a 90deg-rotated box reads `nesw` on its visually-NW corner, etc. |
| **Active-edge highlight** | `CanvasDrawing.drawText` paints a 1-px `--dn-cyan` stroke on the side currently being dragged (only while `editor.resizingText && editor.selectedObject === text`). The dashed selection halo stays as the resting affordance. |
| **Width-only drag (`w`/`e`)** | `topology-mouse-move.js` writes ONLY `text.width`. `text.height` is NEVER touched on this path and `_heightLocked` stays false. |
| **Vertical / corner drag** | Writes BOTH `text.width` AND `text.height`, and sets `text._heightLocked = true`. From then on the box honours the user's height. |
| **Auto-grow height (default)** | When `text.width` is set and `_heightLocked` is false, `drawText` recomputes `h = wrapped_lines * lineHeight` on every paint. The bg rect grows in lockstep with content. Adding more text via the inline editor never causes overflow. |
| **Locked height + clip** | When `_heightLocked` is true and the wrapped content overflows, `drawText` slices the visible lines and replaces the last one via `_truncateToWidthWithEllipsis` (greedy backward shrink + Unicode ellipsis). A small `--dn-cyan` chevron at the inside bottom-right corner indicates content was elided. |
| **Word wrap** | `_wrapTextLinesToWidth` already supported `pre-wrap; word-wrap: break-word` semantics (split on `\n`, greedy whitespace tokens, character-break on lone overflowing words). Reused as-is on every paint frame. |
| **Hit-test parity** | `ObjectDetection.getTextEffectiveBounds` calls into `CanvasDrawing._wrapTextLinesToWidth` so the dashed halo, edge zone, and rotation handle land exactly on the same rectangle the renderer paints. |
| **Legacy backward compat** | A text box with no `text.width` set is "auto-size" -- the legacy `split('\n')` path still runs, untouched. The first edge-stretch drag converts the box to manual-width with auto-height. Existing text boxes that have BOTH `text.width` and `text.height` set from earlier code paths but lack `_heightLocked` immediately auto-grow on next render -- this is exactly what fixes the screenshot bug retroactively. |

### Why auto-grow + manual-width is the default

The user's primary use case is "make the box wider so my IP/MAC/AS-path
fits on one line", a horizontal stretch. After that, content is the
height authority -- typing more text grows the box downward instead of
spilling. The vertical edges and corners exist for the rare case where
the operator wants to crop content (e.g., to keep a multi-line note from
dominating the canvas), and that intent is communicated explicitly by
dragging a vertical edge / corner.

### Files touched

| File | Change |
|---|---|
| `topology/topology-canvas-drawing.js` | Replaced 8-handle drawing with: rotation handle (kept) + active-edge cyan highlight (new). Replaced `h = text.height` in manual branch with auto-grow / locked-clip math. Added `_truncateToWidthWithEllipsis` helper. Added clip-chevron in selection block. |
| `topology/topology-object-detection.js` | Replaced 8 dot-handle hit-tests in `findTextHandle` with edge-zone band hit-test (`TEXT_EDGE_ZONE_PX = 5`). Updated `getTextEffectiveBounds` to mirror the auto-grow + locked semantics so hit-test stays in sync with paint. |
| `topology/topology-mouse-move.js` | Resize math now branches by handle id: `w`/`e` writes only `text.width`; `n`/`s`/corners write both AND set `_heightLocked = true`. |
| `topology/topology-mouse-down.js` | Snapshot start state already uses `getTextEffectiveBounds` -- automatically picks up the new auto-grown height. No changes needed in this round. |
| `topology/topology-mouse-up.js` | Already clears `resizingText` + `textResizeHandle` + `_textResizeStart` in the unified handler. No changes needed in this round. |
| `topology/topology-device-toolbar.js` | Groups button rewired to `window.GroupsPanel.toggle(editor)` (see "Device-toolbar Groups button" subsection below). |
| `topology/index.html` | Cache-buster bumped to `20260512j-textbox-edge-stretch` for canvas-drawing, object-detection, mouse-move; and `20260512j-groups-canonical` for device-toolbar. |

### Verification trace -- screenshot case is fixed

Input: a manually-resized text box at `text.width=80, text.height=20`,
content `"IRB\nIP=100.100.100.1"`, with `_heightLocked` UNSET (because
the legacy resize set both dimensions before the new lock semantics
existed).

1. `drawText` enters the manual-width branch (`hasManualWidth=true`).
2. `_wrapTextLinesToWidth(ctx, "IRB\nIP=100.100.100.1", 80)` returns
   approximately `["IRB", "IP=", "100.10", "0.100.1"]` (4 lines).
3. `naturalH = 4 * lineHeight ~= 4 * 18 = 72 px`.
4. `_heightLocked === undefined`, so the locked branch is skipped.
5. `h = naturalH = 72`. The rect is painted at `72 + padding*2`.
6. Text loop paints 4 lines at `startY = -h/2 + lineHeight/2`, all
   inside the bg rect. **No spill.**

Verified mentally end-to-end. The rect grows in lockstep with the
content. After this fix, even if the user types more lines into the
inline editor, the same path runs again and the rect grows again.

### Zoom-out sub-pixel safety

The cyan edge highlight uses
`Math.max(1 * zoomScale, 1 / (editor.zoom * (editor.dpr || 1)))` so the
stroke is always at least one physical pixel wide. The clip chevron
scales with `zoomScale = 1 / editor.zoom` so it stays the same size on
screen. The rect itself is rasterised by the existing
`_paintTextScreenContent` path at zoom <= 1.05 (already DPR-aware) so no
new sub-pixel artifacts are introduced at extreme zoom-out.

### Object-toolbar Groups button -- 2026-05-12 routing fix

The Groups button on the object selection toolbars previously called
`window.ObjectGroupPopover.toggleFor(editor, anchor)`, which opens a
small per-object micro-popover (add to existing group / create new
group from N selection). The user reported this as broken -- the
expectation is that the toolbar button opens the canonical Groups panel
(the floating draggable panel reachable from the top-bar
`#btn-groups-panel` and the `g` keyboard shortcut).

The fix routes the device, link, text, and shape toolbar buttons to
`window.GroupsPanel.toggle(editor)`, matching the rest of the app. The
`aria-label` and `title` attributes read "Open Groups panel" / "Groups
panel" so screen readers and tooltips don't say "Group" (singular, the
popover verb) anymore. `ObjectGroupPopover` remains available only for
non-toolbar object-assignment flows.

### Manual group UX and generated topology cleanup -- 2026-05-12

Manual group membership must not hijack object selection. A normal click
or drag on a grouped device, link, text box, or shape selects/moves that
object only. Whole-group selection is still available through the Groups
panel's explicit "select members" action.

The Groups panel row is the display/no-display target: clicking the row
or its eye checkbox toggles visibility. Rename, select members, color,
and dissolve are dedicated controls so row click never accidentally
selects the full group. The color action opens the same liquid-glass
Quick Colors palette family as device coloring (pinned/recent colors,
compact swatches, custom picker), not a raw hex prompt. Canvas group
dots/badges are intentionally not drawn; group identity lives in the
panel and object metadata.

Generated topology readability rules: generated physical-link endpoint
TBs must use the same label-placement planner as overlay labels, and MCP
import plans should group links with their endpoint group when both
endpoints share one. Generated devices may inherit per-user SSH
credentials only through confident hostname, serial, management IP,
label, or registered-device matches; never overwrite verified SN/cluster
SSH metadata.

Generated topology persistence must go through the MCP-backed backend save
route (`/api/topology-generator/save-via-mcp`) rather than direct
`/api/sections/<id>/save`. The route resolves the selected legacy section
to the canonical Topology MCP domain, validates the state through
`topology_validate_topology`, saves through the MCP dispatcher, and repairs
the legacy mirror so the dropdown and MCP DB cannot drift again.
The preview's primary action is "Save + Merge to Canvas": generated
devices, links, text, and shape panels are inserted into the current canvas
with ID remapping and collision offsetting, rather than replacing the
canvas through a full `loadTopologyFromData()` reload. Keep this behavior
for generated layouts so shape-backed group panels become real canvas
objects immediately and existing work is not discarded.

### Hitbox parity with stretch -- 2026-05-12

#### What broke

After the edge-stretch landing above, the **visible rectangle** of a
stretched text box grew correctly (auto-grow / locked-height paths
were exercised by the renderer), but **three independent hit-test
paths still re-measured the raw `obj.text` glyphs at the live font**
instead of resolving through `getTextEffectiveBounds`. Concretely:

| File | Function | Stale code |
|---|---|---|
| `topology-object-detection.js` | `findObjectAt` (text branch, lines ~55-102) | Built its own font + `measureText` and computed `w = maxLineWidth, h = lines * lineHeight`. Ignored `text.width` / `text.height` / `_heightLocked`. |
| `topology-mouse-down.js` | `handleDoubleClick` permissive fallback (lines ~2887-2918) | Did its own `measureText(obj.text || 'Text')` with a hard-coded `Arial` font and `w + 10, h + 10` padding. Ignored `text.width` / `text.height`. |
| `topology-mouse-down.js` | TB-vs-link-CP arbitration in `handleMouseDown` (lines ~138-180) | Same pattern: own font + `measureText`, ignored stretched dimensions. |
| `topology-mouse-move.js` | TB-vs-CP cursor decision when curve handle overlaps a TB (lines ~278-308) | Same pattern as above. |

When the user stretched a text box from width=100 to width=300, the
visible rectangle painted at width=300 but every above hit-test still
reported "click landed inside roughly width=100". A double-click in
the new visible region (e.g. at `x = origCenterX + 120`, well outside
the old glyph box but well inside the new rectangle) fell through
`findObjectAt` AND through the permissive double-click fallback,
landing in the `if (!clickedObject)` branch in
`handleDoubleClick`. That branch is the canonical "background
double-click creates a new unbound link" path -- so the user saw a
phantom UL pop up over their just-stretched text box.

#### What we did

Every hit-test path that consumes a text-box bounding box now reads
through `ObjectDetection.getTextEffectiveBounds(editor, textObj)`,
which is the single source of truth shared with the renderer
(`CanvasDrawing.drawText`), the dashed selection halo, the rotation
handle, and the edge-stretch zones (`findTextHandle`).

`getTextEffectiveBounds` already implements the full resolution:

* `text.width > 0 && _heightLocked === true && text.height > 0` ->
  `{w: text.width, h: max(20, text.height)}` (locked-clip mode).
* `text.width > 0 && _heightLocked` falsy ->
  `{w: text.width, h: max(20, wrappedLines * lineHeight)}` (manual
  width + auto-grow height -- the default after a horizontal stretch).
* No `text.width` -> legacy auto-size from font + content (split on
  `\n`, max line width via `measureText`, height from line count).

#### Hit-test paths that NOW resolve through `getTextEffectiveBounds`

| Path | Where | Hit consumer |
|---|---|---|
| Single-click selection | `ObjectDetection.findObjectAt` text branch | Selects the TB, opens the floating selection toolbar |
| Single-click selection (fallback) | `ObjectDetection.findTextAt` | Already on this contract from the previous round; unchanged |
| Edge-zone resize | `ObjectDetection.findTextHandle` | Already on this contract (it IS the helper that publishes the bounds); unchanged |
| Double-click permissive fallback | `MouseDownHandler.handleDoubleClick` -> now delegates to `editor.findTextAt` | Enters inline edit mode |
| Mouse-down TB-vs-link-CP arbitration | `MouseDownHandler.handleMouseDown` text-priority branch | Decides whether the click selects the TB or starts a curve-control-point drag |
| Hover cursor when TB and CP overlap | `MouseMoveHandler` curve-handle hover branch | Picks `move` (TB) vs `grab` (CP) cursor |

#### Paths that are intentionally unchanged

* `findRotationHandle`'s text branch is dead code under the current
  call sites (text rotation flows through `findTextHandle`); leaving
  the legacy text branch alone avoids touching shapes / devices that
  also call this helper.
* `findObjectsInRectangle` (rubber-band marquee) selects text boxes
  by **center-point containment**. The center is a single point that
  also moves correctly when the resize math anchors on the opposite
  edge, so center-point semantics already work after a stretch.
* `CanvasDrawing.drawLinkGapForText` and the angle-meter label are
  RENDER helpers, not hit-test, and they apply only to TBs that are
  attached to links / mid-rotation -- neither flow is reachable
  through the user-stretch path.

#### The invariant

> Every hit-test on a text box reads through
> `ObjectDetection.getTextEffectiveBounds`. No path reads raw
> `text.width` / `text.height` directly.

This is the contract that guarantees the hitbox always tracks the
visible rectangle in every state -- after a stretch, after a font
change, after typing more text into the auto-grow box, after a zoom
in/out, and after rotation.

#### Mental trace -- the bug is fixed

1. User stretches a text box from `width=100` to `width=300` via the
   `e` edge-zone (`text.width = 300`, `_heightLocked` stays false,
   `text.height` stays whatever the renderer auto-grew it to).
2. User double-clicks at `x = obj.x + 120, y = obj.y` (well outside
   the original glyph width, well inside the new 300-wide rectangle).
3. `InputManager.handleDoubleClick` -> `MouseDownHandler.handleDoubleClick`.
4. `editor.findObjectAt(120 offset)` runs the text branch with
   `getTextEffectiveBounds`, which returns `{w: 300, h: <auto>}`.
5. `Math.abs(rx) <= w/2 + padding` -> `120 <= 150 + padding`. **Hit.**
   Returns the text box.
6. `clickedObject.type === 'text'` -> falls through the permissive
   fallback (still re-fetches via `findTextAt` for safety, also
   bound-correct now).
7. The double-click on a text object branch enters inline edit mode
   (existing code path -- not changed in this round).
8. The `if (!clickedObject)` background-double-click branch is NEVER
   reached. No phantom unbound link is created.

#### Files touched (this round)

| File | Change |
|---|---|
| `topology/topology-object-detection.js` | `findObjectAt` text branch now calls `this.getTextEffectiveBounds(editor, obj)` instead of doing its own `measureText` of `obj.text`. Result: stretched TBs match clicks across their full visible rectangle. |
| `topology/topology-mouse-down.js` | Replaced inline `measureText` fallback in `handleDoubleClick` with a delegation to `editor.findTextAt(pos.x, pos.y)` -- which already resolves through `getTextEffectiveBounds`. Replaced the inline `measureText` in the TB-vs-link-CP arbitration in `handleMouseDown` with a `getTextEffectiveBounds` lookup. Both branches now use `editor.getEffectiveTextRotation(textAtPos)` for rotation parity. |
| `topology/topology-mouse-move.js` | The "curve handle overlaps TB -- pick a cursor" branch now reads bounds through `ObjectDetection.getTextEffectiveBounds` and rotation through `editor.getEffectiveTextRotation`. Result: a stretched TB no longer "yields" the cursor to a CP that's geometrically inside the new rectangle. |
| `topology/index.html` | Cache-busters bumped to `20260512k-textbox-hitbox-parity` for the three JS files above. |

#### What we did NOT touch

* Persistence: `text.width`, `text.height`, and `_heightLocked` are
  already serialised through `FileOps.generateTopologyData` (the
  spread `{ ...obj }` keeps them; only an explicit transient delete
  list strips `_*` fields, and `_heightLocked` is not in that list).
  Stretched boxes therefore reload at their stretched size with the
  correct mode -- no save-path change needed.
* The selection halo (dashed outline) and active-edge cyan highlight
  are already painted from the same `getTextEffectiveBounds` /
  `_paintTextScreenContent` code in `CanvasDrawing.drawText`. They
  follow the stretched rectangle automatically.

#### Why this is non-regressive

All three replaced code blocks were doing **exactly the same math**
as `getTextEffectiveBounds` for the case `text.width === undefined`
(the legacy auto-size path). For non-stretched text boxes, the
behaviour is byte-for-byte identical -- same font, same `measureText`,
same `lineHeight = fontSize * 1.3`, same multi-line accumulation.
The only behavioural delta is that for stretched boxes, the helper
now correctly returns the manual width and the wrapped/locked
height. Background double-click for empty canvas still creates an
unbound link -- it just stops accidentally firing over a stretched
text box.

### Resize Handles -- BOTH dots AND edge-zone -- 2026-05-12

#### What changed (Correction 1)

The user reversed the earlier "no visible dots" direction. Visible
8 dot-handles are back -- but **the edge-zone band stays**. Both
affordances coexist:

* **Visible dot-handles** (4 corners + 4 edge-midpoints) painted by
  `CanvasDrawing._drawTextResizeDots` in the rotated text local
  frame. Square fills for corners, circle fills for edges, brand
  blue (`#3498db`) with white stroke + soft blue glow. Sizes are
  zoom-corrected (`12 * (1 / editor.zoom)` world units) so dots stay
  the same CSS-pixel size at any zoom. Style mirrors shape resize
  handles in `topology-shape-drawing.js` exactly so multi-select
  with shapes + text reads consistently.
* **Edge-zone band** (existing 5-px world-space band hugging each
  side of the bbox) untouched as the forgiving fallback. Lets the
  user grab the border anywhere along its length instead of needing
  pixel-perfect aim on a tiny dot.

#### Hit-detect priority (top-down)

```
findTextHandle (topology-object-detection.js)
  1. ROTATION handle (top-right outside, green)
  2. VISIBLE DOT-HANDLES   <-- NEW priority slot
       2a. corners first   (20-CSS-px square hit-box)
       2b. edge-midpoints  (18-CSS-px circle hit-box)
  3. EDGE-ZONE band        (5-CSS-px band on each side / corner)
  4. null                  (body drag-to-move, or outside the bbox)
```

The dot hit-boxes match the shape resize-handle hit-boxes
(`findShapeResizeHandle`'s 20/18-px values) so dragging a
text-box dot has the same click feel as dragging a shape dot. The
returned `cursor` field is a passive default; mouse-move overrides
it with `_rotatedCursor(handle, effRot)` whenever a `handle` is
present, so rotated text boxes still get rotation-corrected
cursors (e.g., a 90deg rotated box reads `nesw-resize` on its
visually-NW corner).

#### Why both coexist

* **Dots = discoverability.** The user SEES the dot and knows the
  box is resizable. Without dots the dashed halo alone was a weak
  affordance for some users.
* **Edge-zone = fluidity.** A 1-px-wide visual dot would be
  punishing on a trackpad. The edge band gives the same
  "drag-anywhere-on-the-border" feel that DOM textareas / OS
  windows have.
* **Same drag handler for both.** Once `findTextHandle` returns
  `{handle: 'nw'/.../'e'}`, the rest of the resize math
  (mouse-move + mouse-up) doesn't know or care whether the click
  landed on a dot or in the edge band.

#### Style sharing with shapes

The dots are factored as `_drawTextResizeDots(ctx, halfW, halfH, zoomScale)`
inside `CanvasDrawing`. The shape draw helper
(`drawShapeSelectionHandles`) is structurally analogous (loops over
handle positions, picks square or circle by `isCorner`, same colors
and zoom-correction). The two helpers were intentionally NOT folded
into one shared function because the shape helper handles
non-rectangle geometries (triangle / diamond / hexagon /
checkmark / line) via `_shapeLocalHandlePoint` -- text boxes are
always rectangles so the loop is tiny and copying it kept the
shape draw path untouched. Anyone changing the shape handle style
should mirror the change here so the two affordances stay in
visual lockstep.

### Font-Size Control on the Selected Text Box -- 2026-05-12

#### The bug (Correction 2)

The user reported: "the text inside the text box cannot be enlarged
now when it actually should be." Investigation traced the symptom
to a missing UI affordance, not a broken renderer:

* The renderer (`drawText`) and hit-test (`getTextEffectiveBounds`)
  both correctly read `text.fontSize` and produce the right glyph
  size + bounding box at any value 8-72.
* The `default-text-size` slider in the left sidebar's "Default
  Text" panel correctly writes through `applyFontToSelectedText`
  to the selected text-box's `fontSize` field with `saveState +
  requestDraw + scheduleAutoSave`.
* But the floating text-selection toolbar (the popover that appears
  when a text box is selected) only had a **Font** button -- which
  opens a font-FAMILY selector. There was NO size control reachable
  from the text-box selection context.

So the user could change family from the toolbar, change color from
the toolbar, change background, rotation, layer -- but to change
the SIZE they had to either (a) hunt for the slider in the left
sidebar, (b) right-click and pick the legacy "Edit Text Properties"
modal, or (c) know the keyboard shortcut for `cycleTextSize`. None
of those is discoverable from where the user is interacting.

This is **Interpretation A** from the prompt: the font-size control
was effectively missing. **Interpretation B** (font scales with box
stretch) was inspected and explicitly rejected -- the renderer
honours `text.fontSize` regardless of `text.width`, and that's the
intended behaviour for the edge-stretch + reflow model.

#### The fix

Added a **Size** button to the floating text toolbar
(`topology-text-toolbar.js`) right after the existing **Font**
button, plus a sibling popup `showTextSizeSelector` in
`topology-text-popups.js` that mirrors the `showTextFontSelector`
pattern. The size popup ships:

* 5 preset buttons: S / M / L / XL / XXL (10 / 14 / 18 / 24 / 32 px).
* A custom range slider 8-72 with live `Npx` badge.

Both routes call the same `applySize(numeric)` helper, which:

1. **Containment guard**: when `text._heightLocked === true` AND
   the new font size would clip ALL wrapped lines, expand
   `text.height` just enough to fit the wrapped content. Uses the
   same `_wrapTextLinesToWidth` helper the renderer uses, so the
   guard math is identical to what `drawText` will do on the next
   paint. Auto-grow boxes (no `_heightLocked`) need no help -- their
   height re-derives from wrapped lines on the next paint.
2. Calls `editor.applyFontToSelectedText(null, numeric)` -- the
   existing helper that writes through `saveState +
   requestDraw + scheduleAutoSave` and applies to single + multi
   selection. Defensive fallback writes `textObj.fontSize` and
   `requestDraw` directly if the helper is absent.
3. Repositions the floating toolbar so it stays anchored to the
   newly-sized text box.

#### Inline editor: canonical fontWeight + fontStyle, honour text.width

While auditing the font-size flow, the inline-edit overlay
(`topology-text-editor.js -> showInline`) was also corrected:

* Now reads canonical `text.fontWeight` and `text.fontStyle`
  strings, with the legacy `text.bold` / `text.italic` booleans
  as a fallback. Previously it read only the booleans, so bold or
  italic text reverted to regular while in inline edit.
* When `text.width` is set (the user has edge-stretched the box),
  the textarea LOCKS its width to the matching screen-pixel value
  and grows only the height. Wrapping in the textarea now mirrors
  what `drawText` will paint after commit -- no more visual jump
  when the user clicks away from a long line.

#### Why this is non-regressive

* `applyFontToSelectedText` was already wired to
  `saveState + requestDraw + scheduleAutoSave` for the left-sidebar
  slider. Routing the floating-toolbar Size selector through the
  same helper inherits the same undo / autosave / multi-select
  behaviour -- no new state machinery.
* The containment guard only ever **grows** `text.height`; it
  never shrinks the box. Users who deliberately locked a smaller
  height keep it whenever the new font still fits.
* The legacy text editor modal's `editor-font-size` input continues
  to work unchanged (its live-preview handler in
  `topology-text-editor.js` still writes `editingText.fontSize`
  directly).

#### Files touched (this round)

| File | Change |
|---|---|
| `topology/topology-canvas-drawing.js` | Added `_drawTextResizeDots(ctx, halfW, halfH, zoomScale)` helper. Called from drawText's selected block, between the rotation handle and the cyan active-edge highlight. Updated drawText comment block to document dots+edge-zone coexistence. |
| `topology/topology-object-detection.js` | Added `TEXT_DOT_CORNER_HIT_PX = 20` / `TEXT_DOT_EDGE_HIT_PX = 18` and an 8-dot hit-test in `findTextHandle` (corners first, edges second), inserted between the rotation-handle check and the edge-zone band check. Updated `findRotationHandle`'s text branch to resolve through `getTextEffectiveBounds` (defensive -- still dead code under current call sites). |
| `topology/topology-text-toolbar.js` | Added a `Size` button after the existing `Font` button. Uses `ico-text-size` icon (the small-A / big-A glyph already in the icon set). |
| `topology/topology-text-popups.js` | New `showTextSizeSelector(editor, textObj)` function: 5 size presets + custom slider, containment guard via `_wrapTextLinesToWidth`, writes through `applyFontToSelectedText`. Exported on `window.showTextSizeSelector`. |
| `topology/topology-text-editor.js` | `showInline` now reads canonical `fontWeight` / `fontStyle` (legacy booleans as fallback). When `text.width` is set, the textarea width is locked so wrapping mirrors the rendered TB. |
| `topology/topology.js` | Thin delegator method `showTextSizeSelector(textObj)` that calls into `window.showTextSizeSelector`. |
| `topology/index.html` | Cache-busters bumped to `20260512l-text-size-btn` (text-toolbar), `20260512l-text-size-popup` (text-popups), `20260512l-textbox-dots-coexist` (canvas-drawing), `20260512l-textbox-dot-hit-first` (object-detection), `20260512l-inline-canonical-style` (text-editor), `20260512l-text-size-selector-wire` (topology.js). |

#### QA matrix updates (cumulative through this pass)

Items in the original QA matrix that NOW interact with both dot-handles
AND edge-zone are listed below with the input methods verified mentally:

| Cell | What | Dot input | Edge-zone input | Notes |
|---|---|---|---|---|
| A.1 | Stretch right (e) | dot at right midpoint | drag right edge band | Both write only `text.width` |
| A.2 | Stretch bottom (s) | dot at bottom midpoint | drag bottom edge band | Both set `_heightLocked=true` + write `text.height` |
| A.3 | Stretch SE corner | corner dot | corner band | Both write width + height |
| A.4 | Min size enforced | dot drag clamps via mouse-move | edge drag clamps via mouse-move | Single guard, both paths |
| A.5 | Cursor on hover | dot hit returns handle id | edge hit returns handle id | `_rotatedCursor` rotates both |
| A.6 | 90deg rotated stretch | dot inverse-rotation -> NW dot reads as NE | edge inverse-rotation -> right edge reads as bottom | Same local-frame math for both |
| B.1 | Font-size from toolbar | Size button -> popup preset | Size button -> popup slider | Both call `applyFontToSelectedText` |
| B.2 | Font-size on locked box | Containment guard expands `text.height` if needed | Same guard | Auto-grow boxes need no guard |
| B.3 | Font-style preservation in edit | Inline editor reads canonical fontWeight/fontStyle | Same | Legacy booleans still work as fallback |
| B.4 | Edited width preserved | Inline editor textarea locks width when `text.width` is set | Same | No visual jump on commit |

### Inline-edit Polish -- Smooth and Predictable -- 2026-05-12

#### Symptom

The user reported the text-box edit experience felt clunky:
> "The text box is clunky when trying to edit it. Please fix the
> [mouse / drag] down behavior and text editing and correct
> [the] behavior."

Audit covered the full lifecycle: enter edit mode, type / wrap / scroll,
exit edit mode, mouse-down handling, and visual continuity between the
canvas-painted glyphs and the textarea overlay.

#### Root cause (the biggest jump)

The textarea overlay's font model did NOT match the canvas font model
exactly. Three accumulated mismatches caused the text to visibly "jump"
on every enter/exit edit transition:

1. **Line-height mismatch** -- canvas uses `lineHeight = fontSize * 1.3`
   in `drawText`; the textarea CSS used `1.35`. Multi-line content stacked
   at a different vertical pitch, so wrapped lines re-flowed and the
   visible height changed when the textarea appeared / disappeared.
2. **Padding model mismatch** -- the canvas paints the background block
   at `(w + 2P) x (h + 2P)` where `P = text.backgroundPadding ?? 8`,
   with the GLYPH BLOCK at `w x h`. The textarea used a hard-coded
   `padding: 4px 8px` AND a 2-px border, so the visible OUTER box was
   `+4 px` wider than the canvas background AND the inner content area
   was `-20 px` narrower than the canvas glyph block. This made wrap
   columns shift between the live editor and the rendered text.
3. **Width math off-by-4** -- `lockedScreenWidth = text.width * zoom + 16`
   only accounted for padding (8 + 8) and ignored the 2 + 2 px of border,
   so even when the user manually edge-stretched the box the live editor
   was 4 px narrower than the rendered TB.

Combined effect: every double-click to edit caused a visible re-flow,
and the user perceived the editor as "jumping" / "clunky".

#### Fixes -- canvas-aligned overlay model

The overlay now mirrors the canvas paint contract exactly. New invariants
inside `showInline`:

* `line-height: 1.3` (was 1.35) -- byte-for-byte match with `drawText`'s
  `lineHeight = fontSize * 1.3`.
* `border: 0` -- the visible blue ring is now a `box-shadow:
  0 0 0 2px #3498db, 0 4px 16px rgba(52, 152, 219, 0.25)` outside the
  content area, so it never consumes layout space (no wrap shift).
* `padding: ${text.backgroundPadding * editor.zoom}px` -- mirrors the
  canvas background-block margin precisely. Default 8 world-units;
  link-attached labels use 4. Both honoured.
* `width = (text.width * zoom) + 2 * paddingPx` with `box-sizing:
  border-box` -- outer box equals the canvas background block,
  inner content area equals the canvas glyph block. Wrap columns
  match exactly.
* `letter-spacing: 0` declared explicitly (matches canvas implicit 0).
* `overflow: auto` only when `_heightLocked === true`; otherwise
  `overflow: hidden` so auto-grow textareas don't show scrollbars.

The same canvas-aligned style is now ALSO applied by
`updateInlinePosition` on every pan/zoom tick, so the overlay continues
to match even if the user changes color/background/font via toolbar
mid-edit (defensive -- the toolbar is currently hidden during edit).

#### Other clunkiness fixes (per-step verdicts)

| Step | Issue | Fix | Verdict |
|---|---|---|---|
| 1.1 | Caret jumped to "select all" on every double-click of existing text -- typing replaced everything | `showInline` now accepts `{selectAll: false}`. Double-click on existing text passes `false` -> caret goes to end of text. Empty / placeholder "Text" boxes auto-select-all so first keystroke replaces the dummy content | fixed |
| 1.4 | Newly-placed text box required a separate double-click to start typing | `topology-mouse-up.js` text-placement branch now auto-opens the inline editor with `{selectAll: true}` immediately after creation -> first keystroke replaces "Text" placeholder | fixed |
| 1.5 | Selection halo / resize dots disappeared while editing | Verified that `drawText` early-returns on `_editing === true`, AND the textarea's box-shadow ring provides the same brand-blue outline -- the user still sees a clear selection affordance | verified-correct |
| 2.6 | Arrow keys could trigger canvas pan while typing in textarea | Verified `topology-keyboard.js` `_isEditableShortcutTarget` already gates ALL canvas shortcuts (arrows, Delete, Cmd-Z, Cmd-A, Cmd-X/C/V) when focus is on a TEXTAREA. No extra fix needed for arrow nav | verified-correct |
| 2.8 | Cmd-Z fired canvas undo while typing | Same gate as 2.6 -- canvas undo is suppressed; textarea native undo wins | verified-correct |
| 3.5 | hideInline always called `editor.saveState()`, polluting undo history with no-op edits | hideInline now snapshots `text.text` at entry (`_inlineEditorOriginalText`) and only saves state + autosaves when the value actually changed | fixed |
| 3.4 | Clicking a resize dot right after exiting edit mode required a second click to "arm" the handle | hideInline now sets `textObj._mouseReleasedAfterSelection = true`, so the very next mouse-down on a dot or edge-zone band starts the resize directly | fixed |
| 4 | Visual continuity between canvas paint and textarea overlay was lossy (the root cause above) | Canvas-aligned overlay model -- line-height 1.3, padding=`backgroundPadding*zoom`, no border, box-shadow ring, exact width math | fixed |
| 5 | Mouse-down on already-selected text body did NOT enter edit mode (single-click is select, double-click is edit) | Verified at `topology-mouse-down.js` lines 1498 / 1601 / 3056-3070 -- single-click only selects + opens floating toolbar (after delay), double-click branch is the only one that calls `showInlineTextEditor` | verified-correct |
| 5 | Mouse-down on inline editor's own textarea correctly keeps caret control | Verified `_inlineEditorClickOutside` only commits when `e.target !== editor._inlineTextEditor` | verified-correct |
| 6 | Typing space inside textarea silently armed canvas pan-on-drag (`spacePressed = true`) for the next mouse interaction | `topology-keyboard.js` keydown / keyup for space now only flip `editor.spacePressed` when `!_isEditableShortcutTarget(e.target)` -- pan-mode is no longer triggered by spaces typed inside the textarea | fixed |
| 6 | New box auto-edit (no caret blink, manual double-click required) | Same as 1.4 -- auto-open with `{selectAll: true}` after placement | fixed |
| 6 | Caret visible against any background | `caret-color: #3498db` (brand blue) explicitly set on the textarea -- visible against light, dark, and custom backgrounds | verified-correct |
| 6 | Locked-height boxes scroll past the visible area while typing | `overflow: auto` is now set on the textarea when `_heightLocked === true`. The user can keep typing past the visible area; the renderer clips with ellipsis on the next paint after commit | fixed |

#### Files touched (this round)

| File | Change |
|---|---|
| `topology/topology-text-editor.js` | Rewrote `showInline` with canvas-aligned overlay model: line-height 1.3, padding=`backgroundPadding*zoom`, no border + box-shadow ring, width = `(text.width * zoom) + 2 * paddingPx`, locked-height honoured with `overflow: auto`, `selectAll` option (defaults to true for empty / placeholder boxes), original-text snapshot for change-detected `saveState`, `_mouseReleasedAfterSelection = true` on hideInline. Rewrote `updateInlinePosition` to refresh ALL canonical paint props (font/color/bg/padding/line-height) so style stays canvas-aligned through pan/zoom and mid-edit changes. |
| `topology/topology-mouse-down.js` | Double-click text-body branch (line 3056-3074) passes `{selectAll: false}` so caret lands at end-of-text on existing content. |
| `topology/topology-mouse-up.js` | Single-text-placement branch auto-opens the inline editor with `{selectAll: true}` after creating the new TB so the user types immediately. Continuous-placement mode is unchanged (boxes stay un-edited so the user can keep placing). |
| `topology/topology.js` | `showInlineTextEditor(textObj, event, options)` thin delegator now forwards the `options` arg through to the module. |
| `topology/topology-keyboard.js` | Space keydown / keyup gated on `_isEditableShortcutTarget(e.target)` so typing space in the textarea (or any sidebar input) doesn't arm canvas pan-on-drag. |
| `topology/index.html` | Cache-busters bumped to letter `m`: `topology-keyboard.js?v=20260512m-space-edit-gate`, `topology-mouse-down.js?v=20260512m-dblclick-caret-end`, `topology-mouse-up.js?v=20260512m-fresh-tb-autoedit`, `topology-text-editor.js?v=20260512m-inline-edit-polish`, `topology.js?v=20260512m-inline-options`. |

#### Visual continuity trace -- pixel alignment

After the fix, the entering / exiting edit-mode transition is visually
indistinguishable for these properties:

| Property | Canvas (`drawText`) | Inline overlay | Match |
|---|---|---|---|
| `font-style` | `text.fontStyle` | `text.fontStyle` (canonical, booleans fallback) | yes |
| `font-weight` | `text.fontWeight` | `text.fontWeight` (canonical, booleans fallback) | yes |
| `font-size` | `text.fontSize * snap-correction` | `text.fontSize * editor.zoom` | yes (snap is sub-CSS-pixel) |
| `font-family` | `text.fontFamily \|\| 'Arial, sans-serif'` | same | yes |
| `text-align` | `'center'` | `text.textAlign \|\| 'center'` | yes |
| `line-height` | `fontSize * 1.3` | `1.3` | yes |
| `letter-spacing` | implicit `0` | explicit `0` | yes |
| `padding` (background block margin) | `backgroundPadding ?? 8` world | `backgroundPadding * editor.zoom` px | yes |
| Inner glyph block width | `text.width` (when set) | `text.width * editor.zoom` (border-box: outer = inner + 2*padding) | yes |
| Outer background block width | `text.width + 2*P` | `text.width * zoom + 2 * paddingPx` | yes |
| Visible outline | none on canvas (selection halo drawn separately) | `box-shadow` ring outside content (no layout shift) | n/a (deliberate brand affordance) |
| `color` | `text.color` | same | yes |
| `background` | computed with opacity blend | same computation | yes |

The only pixel that moves on enter/exit is the **box-shadow ring**
(2-px brand blue outside the content) -- which is intentional UX
feedback that the user is now in edit mode, and never overlaps the
glyphs themselves.

### Smoothness Refinement Pass -- 2026-05-12

Final tactile polish after the inline-edit canvas-aligned overlay
landed. Goal: eliminate the last micro-jank during typing, drag
resize, and the enter/exit edit-mode transition. Three minimal
targeted fixes; everything else verified-correct.

#### Per-category verdicts (A-J)

| Cat | Area | Verdict | Note |
|---|---|---|---|
| A | Frame-rate / drag smoothness | improved | Drag-resize, drag-move, multi-select drag, pan, zoom were already on `editor.scheduleDraw()` (RAF-coalesced). The ONE remaining sync-paint loop was the inline-edit input handler -- now also RAF-coalesced. Auto-grow re-flow during typing is now batched with the canvas paint into a single RAF tick. |
| B | Cursor transitions | verified-correct | `topology-mouse-move.js` lines 161-183 update `editor.canvas.style.cursor` synchronously on every hover frame, with a follow-up `editor.updateCursor()` reset when leaving the handle zone. No flicker -- cursor swaps in the same event loop tick as the hover boundary cross. Selected vs unselected gating is correct (handles only hit-test when `_mouseReleasedAfterSelection === true`). |
| C | Selection halo + dots animation | improved (sub-pixel) | Halo dashed stroke now uses `lineCap = 'square'` to prevent dash-rim feathering at non-integer zoom (e.g. 0.83x). No marching-ants animation added -- would force a continuous RAF redraw loop with no other state changing, hurting battery life and CPU for marginal aesthetic gain. No dot hover scale-up -- would require per-frame paints on cursor-over-dot, same trade-off. |
| D | Mouse-down -> drag start latency | verified-correct | Resize handle drag starts on the same `mousedown` event that hits the dot or edge-zone (no threshold delay). Body drag starts on first move >= 1 px (no artificial deferral). |
| E | Inline-edit micro-interactions | verified-correct | Snap in / snap out -- chosen over a partial fade so the user never perceives "is the editor responding yet?" lag on the first keystroke. Caret placement at click position confirmed. Box-shadow ring is static (no pulse) -- intentional, matches brand convention for input focus. |
| F | Click-feel (dots vs edge-zone) | improved | Edge-zone HIT widened from 5 to 8 screen-px while keeping `TEXT_EDGE_ZONE_PX = 5` as the documented VISUAL semantic. Trackpad / coarse-mouse users now land on the edge reliably. Dot hit-box stays at 20 (corner) / 18 (edge) -- matches shape handles for cross-element click parity. The `Math.min(halfW, halfH) * 0.45` clamp keeps tiny boxes from becoming all-edge. |
| G | Multi-line typing / wrapping | verified-correct | Box auto-grow is INSTANT (no animation) -- already correct. Word-wrap point switching: the textarea uses native browser wrapping (`overflow-wrap: break-word`), the canvas uses `_wrapTextLinesToWidth` -- both compute identical break columns thanks to the canvas-aligned overlay (line-height 1.3, padding = `backgroundPadding * zoom`, `box-sizing: border-box`). |
| H | Save / load roundtrip | verified-correct | First paint already has correct dimensions: `getTextEffectiveBounds` runs `_wrapTextLinesToWidth` for boxes with `text.width`, so wrap is computed before the first `drawText` call. No "pop" reflow visible on topology load. |
| I | Visual rough edges | improved (halo crispness) | `lineCap = 'square'` on the dashed selection halo (above). 1-px box minimum visible width: not modified -- existing `MIN_BOX = 20` world units in resize math + `Math.max(MIN_BOX, ...)` clamps prevent degenerate box collapse. Halo + dots + (future cyan edge-highlight) layer cleanly thanks to the order of operations in `drawText` (background, glyph block, halo, then dots last). |
| J | Edge cases | verified-correct | Rotated GROUP text rotates with group transform (uses `getEffectiveTextRotation`). Multi-select group resize: text box scales width/height (no font-scale -- consistent with shapes). Paste: lands at sensible coords with intact font props. Duplicate (Cmd-D): supported via existing `cloneObjectWithOffset` path -- offset is set in that helper, content is intact. Right-click on textarea while editing: browser-native context menu wins (the canvas context menu is suppressed by the textarea grabbing the event first). |

#### The single biggest perceived-smoothness improvement

**RAF-coalescing the inline-edit input handler** (`topology-text-editor.js`
line 523-537). Before this change, every keystroke fired a synchronous
`editor.draw()` -- which on a topology with 50+ devices / links / shapes
re-paints the entire canvas at 16+ ms per frame. Burst typing (~6
keystrokes in one RAF tick at 100 wpm) used to chain 6 sync paints =
~96 ms of main-thread monopolisation, visible as auto-grow re-flow
"chunkiness" and dropped frames on the dashed halo.

After: `editor.scheduleDraw()` folds all pending paints into ONE per
RAF tick. The textarea itself updates instantly via the browser's
native input handling, so users see characters with zero perceptible
latency, and the canvas re-paints once per 16 ms regardless of typing
speed. Net: typing feels native (like a real text input) instead of
"there's a canvas chugging behind this".

Secondary win: `hideInline` final paint moved to
`editor.requestDraw()`. Previously `editor.draw()` ran synchronously
between the textarea-removal DOM mutation and the next browser repaint,
leaving a 1-frame gap where neither the overlay nor the freshly-painted
canvas glyphs were visible (a flash of background colour). Now both
mutations land in the same RAF tick.

#### Files changed (and exact line ranges)

| File | Lines | Change |
|---|---|---|
| `topology/topology-text-editor.js` | 523-537 | `input` handler: `editor.draw()` -> `editor.scheduleDraw ? editor.scheduleDraw() : editor.draw()` with explanatory comment. |
| `topology/topology-text-editor.js` | 682-693 | `hideInline` final paint: `editor.draw()` -> `editor.requestDraw ? editor.requestDraw() : editor.draw()` with explanatory comment. |
| `topology/topology-object-detection.js` | 648-660 | Added `TEXT_EDGE_ZONE_HIT_PX: 8` constant; expanded docstring distinguishing VISUAL semantic (`TEXT_EDGE_ZONE_PX = 5`) from HIT target. |
| `topology/topology-object-detection.js` | 700-712 | `findTextHandle` now uses `TEXT_EDGE_ZONE_HIT_PX` (8) for the bbox-expansion `desired` calc instead of `TEXT_EDGE_ZONE_PX` (5). |
| `topology/topology-canvas-drawing.js` | 1752-1779 | Halo dashed stroke now wrapped by `_prevCap = ctx.lineCap; ctx.lineCap = 'square'; ... ctx.lineCap = _prevCap;` to crisp dashes at non-integer zoom. |
| `topology/index.html` | 4720, 4723, 4754 | Cache-busters bumped m/l -> n: `topology-canvas-drawing.js?v=20260512n-halo-linecap-square`, `topology-object-detection.js?v=20260512n-edge-hit-zone-8px`, `topology-text-editor.js?v=20260512n-raf-coalesce-typing`. |

#### RAF coalescing -- pre-existing surface confirmed

Verified that `scheduleDraw()` (delegates to `DrawModule.scheduleDraw`)
is the canonical RAF-coalesced paint scheduler used everywhere in
`topology-mouse-move.js` for drag operations:

* Pan: line 96 (`editor.scheduleDraw()`)
* Laser pointer trail: line 114
* Curve handle drag: line 264
* Link stretch: line 714
* Shape rotate: line 1363
* Shape resize: line 1431
* Shape drag (multi-select container): line 1474
* Text rotate: line 1625
* Text resize (the new edge-stretch path): line 1818
* Multi-select drag: line 2137
* Selection box marquee: line 2187
* Many more (15 total `scheduleDraw` calls in mouse-move alone)

`requestDraw()` (RAF-coalesced via `_drawRafId` in `topology.js` lines
12043-12049) is the alternate name used in non-mouse paths (zoom,
panOffset save, theme swap, undo/redo). Both converge on a single
`requestAnimationFrame` and a single `editor.draw()` call per RAF tick.

After this pass, the ONLY remaining synchronous `editor.draw()` calls
in the text-edit lifecycle are inside the live-preview handlers in the
modal text editor (`_setupLivePreview`, lines 173-213) -- those are
fine because the modal has only ONE input field changing at a time and
the user is operating sliders/colour pickers, not burst-typing.

#### What was deliberately NOT added

Documented here so future agents don't re-investigate:

* **Marching ants animation** on the selection halo. Would require a
  continuous RAF loop redrawing the halo with an offset every frame
  even when nothing else is changing. Hurts battery life on laptops.
  Static dashed halo is the canonical app style.
* **Hover scale-up on dots** (1.0 -> 1.15). Would require tracking
  `_hoveredDotId` and a paint per cursor-move-into-dot. Same battery
  trade-off, marginal aesthetic gain.
* **Cyan edge-highlight fade-in/out** during active resize. Hard to
  tween smoothly without a real animation library; the snap is fine.
* **Textarea fade-in transition** on enter edit mode. Tested -- a
  120 ms fade made the first keystroke feel laggy ("did it register?").
  Snap in is the right choice.

#### Cache-buster, sync, lints, PR-gate

* Cache-buster letter: **n** (next free after `m`).
* Files synced to `/home/dn/CURSOR/`: `topology-text-editor.js`,
  `topology-object-detection.js`, `topology-canvas-drawing.js`,
  `index.html`. All four `diff --brief` identical against the worktree.
* `ReadLints` clean on all four files.
* PR-gate greps clean (this pass touched only frontend JS -- no
  backend Python -- so multi-user surface is unaffected).

## TEST/SPIRENT Recipe Reliability Guardrails -- 2026-05-12

### What was fixed

The TEST phase compiler and Spirent recipe path were hardened after SW-228552
IPv6 NDP/CLI category runs exposed avoidable automation errors:

* TP prose containing backend/vtysh actions such as `request routing-shell ...`
  must NOT be mined into frontend `dnos_run_show_commands` payloads. Vtysh
  parity is compiled through the dedicated `vtysh_parity_show_commands` phase;
  backend-only snippets like `show evpn vni` / `show evpn rmac-vni` are filtered
  out of generic read-only frontend command extraction.
* Generic TP syntax hints like `cmd search / CLI docs / commit-check ...` must
  normalize to useful one-token `dnos_cmd_search` keywords (`commit`,
  `rollback`, `mac-ip-table`, etc.), never `/`, `cli`, or `docs`.
* Every compiled MCP call now passes a compile-quality gate before execution:
  no null args, required `device_name` for DNOS tools, non-empty cmd-search
  keywords, runnable frontend show commands only, and explicit stream names for
  `spirent_create_stream`.
* Generic `/TEST` traffic phases that create a Spirent stream now auto-append a
  paired `spirent_start` phase for the same stream name, so recipes do not
  silently create traffic without transmitting it.
* Generated Spirent stream calls default to `reuse_policy=replace`, matching the
  fixed `/SPIRENT` behavior that prevents stale StreamBlock reuse from hiding
  packet encoding changes.

### Validation performed

* `python3 -m py_compile /home/dn/mcp_common/command_profiles.py
  /home/dn/SCALER/SPIRENT/spirent_tool.py`
* Native MCP `test_phase_compile` on
  `TEST_SW-228552_TC-CLEAR-MACIP-01_020/recipe.json`: `PHASES_COMPILED`,
  `missing_phase_wiring=[]`, no extracted backend `request routing-shell`
  frontend commands, and no `/` cmd-search keyword.
* Native MCP `test_phase_compile` on
  `TEST_SW-228552_TC-IPV6-NDP-BASIC-01_013/recipe.json`: `PHASES_COMPILED`,
  `missing_phase_wiring=[]`, explicit `icmpv6-na` streams keep
  `reuse_policy=replace` and paired `spirent_start` phases.

### Future rule

When improving `/TEST` or `/SPIRENT`, prefer compile-time rejection or
auto-wiring over learning failures during a live run. A recipe is not trusted
until phase compile proves MCP argument shape, command syntax surface, stream
lifecycle, and traffic readiness are coherent.

## Light-mode Contrast Sweep -- 2026-05-12

### The bug

In **light mode** the Link Editor and Device Editor modals (`#link-editor-
modal`, `#device-editor-modal`) rendered every `<label>` text white-on-white
and were unreadable. Other surfaces flagged by the user (canvas top bar,
left toolbar, AI drawer, DNAAS panel, scaler panel, color picker popup,
share dialog) were audited and either were already correct or were fixed
in earlier 2026-05-12 passes.

### Light-mode signal selector (THE ONE TO USE)

`body:not(.dark-mode) .selector { ... }`

Light mode is the DEFAULT (no body class). Dark mode is signalled by
`body.dark-mode`. Earlier code in the repo references `body.light-mode`
selectors but the JS toggle (`topology.js -> toggleTheme()`) only adds /
removes `dark-mode`, so `.light-mode` selectors never apply. Always scope
new light-mode rules with `body:not(.dark-mode)`.

### The convention (REVISED 2026-05-12i)

**Toolbar icons + text follow the theme: dark in light mode, white in
dark mode. Only true intentional-dark panels (the user-pinned floating
chrome surfaces) keep white text in both modes.**

This SUPERSEDES the earlier "dark-bg toolbars keep white text in both
modes" convention. The reason: the main app toolbar (`.top-bar`) and the
left toolbar rail (`.toolbar`) actually flip their backgrounds in light
mode under the `ui-skin-v2` skin (which every user runs by default --
`<body class="ui-skin-v2">` in `index.html`). The v2.3 "Editorial Light"
sub-skin paints those bars solid white (`#ffffff`) in light mode, so any
nominal "white text" is white-on-white. Earlier 2026-05-12 audit rounds
classified those bars as "already-OK / intentionally dark in both modes"
based on the legacy `.top-bar { background: blue-gradient }` rule at
line 243 of `styles.css` -- but v2.3 (line 19818) overrides that with
`!important`, so the legacy classification was wrong.

The corrected breakdown:

1. **Theme-following surfaces** (`.top-bar`, `.toolbar`, `.tool-rail`,
   `.top-bar-btn`, `.tool-btn`, `.toolbar-section-header`, the DriveNets
   logo, every chip and section header inside the bars). These flip from
   white bg + navy ink in light mode to deep-slate (`#0f172a`) bg +
   near-white ink in dark mode. The v2.3 + v2.3.1 + v2.3.17 blocks under
   `body.ui-skin-v2(.dark-mode | :not(.dark-mode))` handle every chip /
   text element. SVG icons inside these chips inherit `currentColor`
   so they follow the same flip automatically.

2. **True intentional-dark surfaces** (AI drawer, DNAAS Discovery panel,
   Network Mapper panel, Scaler panel, Grid HUD bottom-right,
   topo-active-bar, AI launcher pill). These surfaces use a hard
   DriveNets blue gradient or deep navy that does NOT flip in light
   mode (no `:not(.dark-mode)` override paints them light). White text /
   white icons on those panels is correct in BOTH themes. Do NOT add
   light-mode overrides that flip them to light bg.

3. **Light-surface modals** (`.modal-content`, `.shortcut-section-
   content`, `.share-dialog`, `.color-popup`). White bg in light mode +
   dark-glass in dark mode (via `body.dark-mode .modal-content`). Inline
   `color: #ecf0f1` labels need `body:not(.dark-mode)` `!important`
   overrides to flip back to navy in light mode.

4. **Brand-accent buttons** (`#btn-dnaas`, `#btn-network-mapper`,
   `#btn-scaler-config`). These keep their saturated orange / blue
   gradient / white cloud backgrounds in BOTH modes and the white (or
   cloud-navy) text on them stays correct in BOTH modes. v2.3.17
   exempts them explicitly from the toolbar `:not(.dark-mode)` flip.

### Conflicting inline styles

The Link/Device editor modal labels are authored with inline
`style="color: #ecf0f1"`. Inline styles win over regular CSS selectors,
so the light-mode override MUST use `!important` to override them. This
is the one place we use `!important` in the light-mode sweep -- everywhere
else, source order + cascade is enough.

Future agents writing new modals should AVOID inline `color: #ecf0f1`
and rely on `body.dark-mode .modal-body label` (already in styles.css at
line ~5322) to provide the dark-mode text colour. Light mode then inherits
from `body` which is dark text on white.

### Surfaces audited (verdict per surface)

| Surface | Light-mode verdict |
|---|---|
| Top bar (`.top-bar`) | **Fixed in 2026-05-12i** -- earlier "blue-gradient/already-OK" verdict was wrong; v2.3 flips it to solid white bg, so icons + text must follow the theme. Final-defense override added under v2.3.17 |
| Left toolbar (`.toolbar` 200px expanded rail) | **Fixed in 2026-05-12i** -- same v2.3 flip; v2.3.1 already handled most chips, v2.3.17 adds hardcoded-white SVG attribute-selector defense |
| Left tool-rail (`.toolbar.tool-rail-mode .tool-rail` 54px collapsed icon rail) | **Fixed in 2026-05-12i** -- existing `body:not(.dark-mode) .tool-rail-button { color: rgba(13,27,42,.78) }` plus v2.3.17 attribute-selector defense for any hardcoded white in tool-rail SVGs |
| Top-bar buttons (`.top-bar-btn`) | **Fixed in 2026-05-12i** -- text + icons forced to `var(--skin-v23-text)` in light mode, `text-shadow` cleared, dark drop-shadow filter neutralised |
| DriveNets logo (`.dn-brand-logo svg`) | **Fixed in 2026-05-12i** -- v2.3 already handled `rect` + `line`, v2.3.17 adds catch-all `[fill="white"]` / `[stroke="white"]` attribute-selector |
| Shape selection toolbar (`#shape-selection-toolbar`) | **Fixed in 2026-05-12j** -- v2.3.18 block. Floating panel rendered dynamically by `topology-shape-toolbar.js` (`createIconBtn` -> `_createIconSvg(... 'rgba(255,255,255,0.8)')` baked hardcoded-white into every icon's inline SVG `style="color: ..."`). v2.3.17 missed it because the toolbar is `position: fixed` appended directly to `document.body` -- it inherits from none of v2.3.17's `.top-bar` / `.toolbar` / `.tool-rail-button` selectors. v2.3.18 forces `svg { color: var(--skin-v23-text) !important; }` on `#shape-selection-toolbar` in light mode (defeats the inline white and lets `currentColor` cascade to navy in referenced `<symbol>`s), adds the 5-hex-variant white `fill`/`stroke` attribute-selector defense, flips inline-styled labels / inputs / `[id$="-val"]` slider value badges to navy via `!important`, and tints `.shape-toolbar-btn` / `.layer-badge` to a faint navy-on-white card with brand-cyan hover. The sibling `#shape-color-palette-popup` and layer-dropdown menu are intentional-dark surfaces in BOTH modes and are deliberately exempt. |
| `#btn-dnaas` (DNAAS top-bar button) | Exempt -- accent button, keeps orange gradient bg + white icons + white text in BOTH modes (explicit v2.3.17 exemption) |
| `#btn-network-mapper` (Mapper top-bar button) | Exempt -- accent button, keeps cyan/blue gradient bg + white text in BOTH modes |
| `#btn-scaler-config` (CONFIG cloud) | Exempt -- intentional white cloud surface with `#1e3a5f` navy ink in BOTH modes |
| `#btn-groups-panel` (Groups) | Follows top-bar theme -- cyan accent border in both modes, ink follows v2.3.17 invariant |
| AI launcher pill (`.ai-chat-launcher`) | Already OK -- cyan/blue gradient bg, intentionally dark in both modes |
| AI drawer (`.ai-drawer`) | Already OK -- pinned dark navy gradient, `color-scheme: dark` set explicitly |
| DNAAS Discovery panel (`#dnaas-panel`) | Already OK -- translucent dark navy bg, intentional-dark surface |
| Network Mapper panel (`#nm-panel`) | Already OK -- same dark-glass pattern as DNAAS panel |
| Scaler panel (`.scaler-panel`) | Already OK -- translucent dark navy bg, white text correct in both modes |
| Grid Controls (`#grid-controls` bottom-right) | Already OK -- DriveNets blue gradient bg, intentional-dark surface |
| topo-active-bar (bottom-left topology pill) | Already OK -- dark gradient bg, intentionally dark in both modes |
| Canvas top zoom HUD (`.hud-btn`) | Already OK -- lives inside `#grid-controls` blue gradient |
| Color picker popup (`.color-popup-*`) | Fixed in 2026-05-12h (earlier in this sweep) |
| Share dialog sub-elements (`.share-*`) | Fixed in 2026-05-12h (earlier in this sweep) |
| Tooltips (`.app-tooltip`) | Already OK -- has explicit `body:not(.dark-mode)` block at styles.css:559 |
| Notification panel (`#notification-center-panel`) | Already OK -- per-mode rules injected by topology-notifications.js |
| `.modal-content` base | Already OK -- white bg in light mode, dark glass in dark mode |
| `.modal-header h2` / `.modal-close` / `.modal-body small` | Already OK -- dark text in light mode (`#333`, `#999`, `#666`) |
| `.shortcut-section-header` (blue gradient) | Already OK -- white text on blue, correct in both modes |
| `.shortcut-key` / `.shortcut-desc` | Already OK -- dark text in light mode |
| Topologies dropdown menu (`#topologies-dropdown-menu`) | Already OK -- `body.ui-skin-v2:not(.dark-mode)` block at styles.css:19656 |
| Link Editor modal labels (`#link-editor-modal .modal-body label`) | **Fixed in 2026-05-12h** -- inline `#ecf0f1` overridden to navy |
| Device Editor modal labels (`#device-editor-modal .modal-body label`) | **Fixed in 2026-05-12h** -- same override |
| Lock Current Curve sub-panel (`#editor-keep-curve-section label`) | **Fixed in 2026-05-12h** -- pastel purple bg, label was white-on-pastel |
| Form controls inside the editor modals (`<select>`, `<input>`) | Already OK -- have their own dark backgrounds (#2d3748 / #34495e) hard-coded, white text correct on dark control |

### Defensive catch-all rule

Added a tightly scoped attribute selector that catches any FUTURE inline
`style*="ecf0f1"` on `<label>` or `<span>` inside `.modal-body`:

```css
body:not(.dark-mode) .modal-body label[style*="ecf0f1"],
body:not(.dark-mode) .modal-body span[style*="ecf0f1"] {
    color: var(--dn-navy-deep, #0D1B2A) !important;
}
```

The selector is scoped to `.modal-body` specifically so it does NOT touch
purpose-dark surfaces (scaler panel, DNAAS panel, top bar, etc.) -- those
keep their white text in light mode.

### Files changed

* `topology/styles.css` -- appended the v2.3.17 "toolbar icon/text
  contrast follows theme" block at the end of the file (~190 lines).
  Earlier 2026-05-12h appends (color-popup, share-dialog, editor modal
  labels, `[style*="ecf0f1"]` catch-all) are untouched. Later in the day,
  the v2.3.18 follow-up block was appended after v2.3.17 (~110 lines)
  for `#shape-selection-toolbar`.
* `topology/index.html` -- cache-buster trail today:
  `?v=20260512h-light-contrast` -> `?v=20260512i-toolbar-icon-contrast`
  -> `?v=20260512j-shape-toolbar-contrast`.
* `topology/DEVELOPMENT_GUIDELINES.md` -- this section was revised to
  flip the `.top-bar` / `.toolbar` verdicts from "already-OK" to
  "fixed in 2026-05-12i" and document the new "toolbar icons + text
  follow the theme" invariant. The follow-up subsection below covers
  v2.3.18 (shape-selection toolbar, 2026-05-12j).

### How the v2.3.17 override block is structured

The block is scoped strictly under
`body.ui-skin-v2:not(.dark-mode) <selector>` so that dark mode is never
touched. The minimum it does:

1. Force `.top-bar`, `.top-bar-btn`, and `.cloud-glass-btn .glass-layer`
   to `color: var(--skin-v23-text)` (navy in light mode) and clear the
   legacy `text-shadow: 0 1px 3px rgba(0,0,0,0.3)` that was meant for
   the blue-gradient bar.
2. Force SVG `color` + `stroke` + clear `filter` / `opacity` on every
   `.top-bar-btn svg` so `currentColor` and explicit stroke values
   resolve to navy. `fill` is intentionally NOT set on the `<svg>`
   element to preserve outline icons (`fill="none"` on the wrapper +
   `stroke="currentColor"` on children -- e.g. Topologies, Groups).
3. Attribute-selector catch-all: `.top-bar svg [fill="white"|"#fff"|...]`
   -> `fill: var(--skin-v23-text) !important;` (and same for stroke).
   This is the defensive layer for any future SVG authored with literal
   white fills/strokes.
4. Exempt `#btn-dnaas`, `#btn-network-mapper` from the flip -- they
   keep `color: #fff` + `stroke: #fff` + `fill: #fff` in light mode
   because their backgrounds are saturated orange / blue gradients.
   `#btn-scaler-config` is exempt by virtue of v2.3 already painting
   it as a white cloud surface with `#1e3a5f` ink in both modes.
5. Hover state in light mode: navy-tinted soft bg + blue accent border
   + blue accent icon (uses `--skin-v23-accent` = `#2563eb`). The legacy
   white-on-white hover style is overridden so the affordance is
   visible against the white bar.
6. Repeat steps (3) and (4) for `.toolbar` (200px expanded rail) and
   `.tool-rail-button` (54px collapsed icon rail).

### Regression check (mental trace)

In **dark mode** (`body.ui-skin-v2.dark-mode`):

* v2.3 sets `--skin-v23-bar-bg: #0f172a`, `--skin-v23-text:
  rgba(245, 248, 255, 0.95)`.
* v2.3 rules at lines 19818 / 19850 / 19872 apply (no `:not(.dark-mode)`
  scope), so the bar bg is deep slate, the chip text is near-white,
  and the chip svg stroke is near-white.
* v2.3.17 (`:not(.dark-mode)` scoped) does NOT apply -> dark mode keeps
  the v2.3 behavior. White icons, white text, dark bg. Correct.

In **light mode** (`body.ui-skin-v2` only, no `.dark-mode` class):

* v2.3 sets bar bg to `#ffffff`, chip text + svg stroke to `#0f172a`.
* v2.3.17 layers on top with `!important` to also force the SVG
  `currentColor` + cover hardcoded white fills/strokes. Final result:
  white bg, navy text, navy icons. The previously-white-on-white
  DriveNets logo bars / inline SVGs flip to navy via the attribute
  selectors.

### v2.3.18 follow-up: shape-selection toolbar (cache-buster `j`, 2026-05-12)

The v2.3.17 sweep missed one floating surface: `#shape-selection-toolbar`.
It is built dynamically by `topology/topology-shape-toolbar.js` and
appended directly to `document.body` (`position: fixed; z-index: 99999`),
so it inherits from NONE of the v2.3.17 selectors (`.top-bar`,
`.toolbar`, `.tool-rail-button`). Every icon button is built by
`createIconBtn(...)` -> `editor._createIconSvg(iconId, 15, iconColor)`
with `iconColor = 'rgba(255,255,255,0.8)'` HARDCODED at module line ~529
regardless of theme. `_createIconSvg` (topology.js:6131) emits:

```
<svg style="color: rgba(255,255,255,0.8); pointer-events: none;">
    <use href="#ico-..."/>
</svg>
```

Because the referenced `<symbol>` paths declare `stroke="currentColor"`
or `fill="currentColor"`, the inline `color: rgba(255,255,255,0.8)` wins
the cascade and every icon renders white. In light mode the toolbar bg
is `rgba(255,255,255,0.25)` (frosted-glass over a near-white canvas), so
the white icons disappear.

The v2.3.18 block at the very end of `styles.css` adds:

1. `body.ui-skin-v2:not(.dark-mode) #shape-selection-toolbar svg { color:
   var(--skin-v23-text) !important; }` -- the `!important` defeats the
   inline `style="color: rgba(...)"` (CSS spec: `!important` author wins
   over normal-author inline styles), so `currentColor` resolves to navy
   in light mode and every icon flips automatically.
2. 5-hex-variant attribute-selector defense (`[fill="white"|"#fff"|
   "#FFF"|"#ffffff"|"#FFFFFF"]` and same for `[stroke="..."]`) on SVG
   children. Same idiom as v2.3.17 -- no hardcoded literal white today
   but covers regressions.
3. `!important` color override on `.shape-toolbar-label`,
   `.shape-toolbar-input`, `input`, `span`, and `[id$="-val"]` (slider
   value badges) inside the toolbar. The module sets these statically on
   render (theme-aware at creation time) but the values go stale if the
   user toggles theme while the toolbar is open; `!important` keeps them
   readable regardless.
4. Bg/border tint on `.shape-toolbar-btn` and `.layer-badge`
   (`rgba(15,23,42,0.05)` / `rgba(15,23,42,0.12)`) so the now-navy icons
   sit on a faint navy-on-white card with visible button affordance.
5. Hover state with `--skin-v23-accent` (brand blue) border + light blue
   tint bg, mirroring the v2.3.17 hover affordance on `.top-bar-btn`.

Exempt by design (intentional-dark in BOTH modes, like AI drawer / Mapper
panel):

* `#shape-color-palette-popup` -- module line 39 hardcodes
  `linear-gradient(rgba(30,30,40,0.95), rgba(20,20,30,0.98))` and white
  text. NOT touched by v2.3.18.
* The layer-dropdown menu -- module line 491 hardcodes
  `background: rgba(15,15,25,0.85)` with white items. NOT touched.

Dark-mode regression trace: the entire block sits under
`body.ui-skin-v2:not(.dark-mode)`, so when `body.dark-mode` is present
NONE of v2.3.18 applies. The dark-mode path of `topology-shape-toolbar.js`
(white icons, `rgba(15,15,25,0.25)` bg, white labels) is untouched.

### Conflicts with other in-flight workers

* Top-bar pill worker (`topology-file-ops.js`, `topology-share.js`):
  edits JS only, not CSS. No collision.
* Text-box edge-stretch worker (canvas drawing files): no toolbar / CSS
  edits.
* Other workers may also bump the `index.html` cache-buster letter
  today. Before editing `index.html`, this worker grepped the current
  letter (`h`) and incremented to `i`. If a later worker also bumps
  to `i` simultaneously, their commit will win the merge -- they should
  pick the next free letter then.

### Files NOT touched (deliberately)

* In-flight Top-bar pill worker's selectors (`shared-by-segment`,
  `shared-by-popover`) -- not in styles.css yet, the other worker will
  ship its own light-mode overrides.
* Shipped View/Edit badges (`.ta-perm-badge`, `.share-perm-pill`,
  `.shared-domain-perm-badge`) -- already have correct light-mode
  contrast.
* Split-color seam + picker CSS classes (`.color-popup-split-*`) -- already
  have light-mode overrides from the earlier 2026-05-12h pass.
* New-Topology wizard inline styles -- theme is JS-applied based on the
  current darkMode flag, no CSS override needed.
* Copy-style CSS -- already audited in 2026-05-12c.

### Dark-mode regression check

Every new rule is scoped under `body:not(.dark-mode)`. The default rules
that were already in `styles.css` (which cover dark mode through `body
.dark-mode .selector` selectors) are unchanged. Manually traced each of
the new selectors:

* `body:not(.dark-mode) #link-editor-modal .modal-body label` -- only
  applies when `body` lacks `.dark-mode`. In dark mode, the inline
  `style="color: #ecf0f1"` continues to take effect (dark glass modal +
  near-white label, readable). NO regression.
* Same for `#device-editor-modal` and `#editor-keep-curve-section`.
* The `[style*="ecf0f1"]` attribute selector ALSO scoped to
  `body:not(.dark-mode) .modal-body` -- no effect in dark mode. NO
  regression.

### How to extend this sweep

If a future agent adds a modal/dialog/popup that uses white text in dark
mode:

1. Choose the surface pattern first: intentionally dark in both modes (use
   a brand-blue / navy gradient bg, leave white text alone) OR light in
   light mode + dark in dark mode (add a `body.dark-mode` rule for the
   dark surface AND a corresponding light-mode default).
2. Avoid inline `style="color: #ecf0f1"` / `style="color: #fff"` on text
   that lives over an unknown background. Let CSS do the work.
3. When you must use an inline color and the surface flips per-mode, add
   a `body:not(.dark-mode) .your-selector { color: ... !important; }`
   rule alongside the inline style.
4. Bump the cache-buster on `topology/styles.css` in `topology/index.html`
   (today's letter sequence: `?v=20260512<a-z>-<purpose>`).
5. Sync `styles.css` + `index.html` to `/home/dn/CURSOR/`.
6. Update this section's "Surfaces audited" table.

## New Topology + Create Domain Wizard -- 2026-05-12

### What shipped

Replaced the "New Topology" flow's split UX (domain picker -> jumps out to a
separate Manage Domains panel -> user has to retrigger New Topology to name
the topology) with one continuous in-overlay wizard that creates a brand-new
domain inline when needed and immediately transitions to the topology-name
step in the same dialog.

### File + function

- `topology/topology-file-ops.js` -- the entire `_showNewTopologyDomainPicker(editor)`
  function was rewritten. Lookup by name to find the new implementation; it
  replaces the prior single-pane domain picker that called
  `_openSectionsManager` for "Create new domain".

### Step machine

```
[1] domain-step  ->  user picks a domain  ->  [3] topology-step  ->  canvas opens
                |
                +->  "+ Create new domain" clicked
                       |
                       v
                     [2] create-domain inline pane (name + icon + color)
                       |   Create
                       v
                     [3] topology-step (pre-selected to the new domain)
```

If the user has zero owned non-built-in domains at open time, the wizard
opens directly at `[2] create-domain inline pane` (first-time onboarding).

### Cancel-mid-flow semantics

1. **Cancel BEFORE creating any domain** (still on `[1]` or `[2]` with no
   POST yet): wizard closes, nothing persists, no toast.
2. **Cancel AFTER the new domain was POSTed but BEFORE the topology was
   POSTed** (closed mid-`[3]`): the domain stays -- it was created via the
   per-user backend route and is now visible in the sections sidebar. We
   surface a toast: `Domain "<name>" created. Add a topology when you're
   ready.` (NOT an emoji; plain `[INFO]`-style toast text).
3. **Successful flow**: NO double success modals. The canvas opening with
   the brand-new topology is the only success signal. We dispatch
   `topology-domains:changed` so other components (sidebar, topology
   dropdown) re-render.

### Multi-user contract preserved

- All section + topology API calls go through `window.TopologyAuth.authFetch`.
- Section creation hits the existing `POST /api/sections` route (already
  `_require_auth()`-gated, atomic-write per `user_store.user_data_path`).
- Topology creation hits the existing `POST /api/sections/<id>/save` route
  (same auth gate, same atomic write).
- Built-in / shared-in domain IDs are excluded from the "first-time onboarding"
  zero-domain check so a user whose only domains are shared-in still gets the
  domain picker, not the create-domain shortcut.

### Keyboard polish

- Enter on the domain-name input submits the create-domain step.
- Enter on the topology-name input submits the topology-create step.
- Escape closes the overlay (with the "domain stays, add a topology later"
  toast iff a domain was already created in this session).
- Tab traversal follows visual order; the active step's primary input is
  focused on pane switch.

### Optional breadcrumb

A tiny `Domain -> Topology` breadcrumb sits at the top of the overlay. Steps
already completed render in `--dn-cloud`, the current step in `--dn-cyan`,
upcoming steps in the secondary text color. No icons, no emojis -- text only.

### What MUST stay untouched

- `_openSectionsManager` (Manage Domains panel) -- the "+ Create new domain"
  button there is a separate entry point used outside the New Topology
  wizard and still works independently.
- Existing section + topology load/save paths.
- Shared-domain rendering, share-permission badges, "Shared with me" list.
- Canvas drawing, split-colour popups, device editor.

### Cache-buster

`topology/index.html` -> `topology-file-ops.js?v=20260512e-new-topo-flow`.
The cache-buster check in `tests/test_domain_dropdown_render_unit.py` was
relaxed to "any date >= 20260506" so future bumps on the same file no longer
require touching that test.

### Test pinning

`tests/test_new_topology_picker_unit.py` is the static guard for this flow.
It asserts:

- The three-pane wizard structure exists (domain / create-domain / topology).
- The create-domain pane reaches `POST /api/sections` via `authFetch`.
- The topology pane reaches `POST /api/sections/<id>/save` via `authFetch`.
- The cancel-after-domain-create toast text is present.
- Enter/Escape keyboard handlers are wired.
- The breadcrumb element is rendered with the `Domain` and `Topology` labels.
- The cache-buster in `index.html` for `topology-file-ops.js` is `>= today`.

### Why this was broken before

The old `_showNewTopologyDomainPicker` had a `+ Create new domain` button
whose click handler did `closeOverlay(); FileOps._openSectionsManager(editor);`
-- it tore down the wizard and handed off to the standalone Manage Domains
panel. The user landed in a different surface with no pending-topology-name
state preserved, which is why naming the topology required re-triggering New
Topology after the domain was created.

The fix folds the create-domain step into the same overlay (a second `<div>`
inside the same card swapped via display toggling, NOT a new modal stack)
and explicitly preserves a `pendingTopologyName` between steps so the user's
typed topology name (if any) survives the domain-creation pane.

## Shared Topology Permissions -- View / Edit -- 2026-05-12

### What shipped

User-facing rename of the share permission tokens, plus per-row visibility
of the effective permission on every shared topology row and shared-in
domain header.

1. **User-facing terminology rename**: `read` -> "View", `write` -> "Edit".
2. **Per-row permission badge** on every topology row that is shared INTO
   this user from another user, plus the shared-in domain header.
3. **Edit-affordance gating** on view-only rows: Rename / Share / Unshare /
   Delete are hidden; only Open + Duplicate (copy into your own section) +
   Remove-from-my-list survive.

### Rename strategy decision: FRONTEND-ONLY

**Decision:** keep the wire tokens `read` / `write` in the backend. Rename
only what the user reads on the screen.

**Why:**
* Backend tokens are validated by a Pydantic regex `^(read|write)$` in
  `ShareDomainRequest` and `ShareTopologyRequest`, are joined against
  `domain_shares.permission` and `topology_shares.permission` SQLite columns
  on every user's DB (638+ seeded users), and are gated in 30+ places in
  `user_store.py` and `routes/router.py` via `permission == "write"` /
  `permission == "read"` string compares.
* A schema migration would have to (a) rewrite every existing row in
  `_users.db` `domain_shares` and `topology_shares`, (b) update every
  Pydantic regex, (c) add backward-compat readers for any inflight grant
  that still carries the legacy token. None of that buys a user any UX
  improvement -- the only thing the user sees is the badge text.
* The wire tokens are never user-facing today: they appear in audit log
  rows we already labelled with friendly action names (`share_topology`,
  `permission_change_topology`), and in REST bodies that the user never
  inspects directly.

**Implementation:** a single helper in `topology-share.js` does the
translation:

```js
window.TopologyShare.permissionLabel(perm) -> 'View' | 'Edit' | ''
window.TopologyShare.permissionTitle(perm) -> 'Can open and inspect' |
                                              'Can open, modify, and save'
```

Every UI surface that previously rendered `r.permission` (the raw `'read'`
/ `'write'` token) goes through this helper. The token CSS classes
(`.share-perm-pill.read`, `.share-perm-pill.write`) stay -- they're keyed
by the wire token because the helper only changes the visible TEXT, not
the colour family. The same applies to `.share-perm-mini-dot.read` /
`.write`.

### Badge contract

The frontend badge takes two flavours:

1. **Topology row badge** (`.ta-perm-badge.view` / `.ta-perm-badge.edit`)
   on every row inside a shared-in section AND inside the
   "Shared with me" inbox. Sits to the LEFT of the time-ago column, with
   an inline eye SVG (View) or pencil SVG (Edit) and the text label.

2. **Domain header badge** (`.shared-domain-perm-badge.view` /
   `.shared-domain-perm-badge.edit`) on the shared-in domain title row,
   next to the existing "BY <owner>" pill. Tooltip: `Shared by <owner>
   (View only)` or `Shared by <owner> (Edit access)`.

The badge is purely a READ-OUT. Source of truth is the `permission`
field already returned by:

* `GET /api/domains/<id>/topologies` -> each `TopologyMeta.permission`
  for rows inside the synthetic "Shared with me" inbox.
* `GET /api/domains/` -> each `TopologyDomainInfo.permission` for
  shared-in named domains.

No new endpoint was added; the existing list response already carries
`permission`. The shared-in topologies inside a named shared-in domain
inherit the domain-level permission (`section._permission`); rows in
the synthetic inbox use the per-file permission from `TopologyMeta`.

### Edit-affordance gating (NEW)

When the row's effective permission is `read`, the dropdown action bar
hides Rename / Share / Unshare / Delete. The previous policy already hid
Rename / Share / Delete on shared-in rows; we now additionally:

* Disable the load-into-edit save path: the backend already rejects
  `PUT /api/domains/__shared_with_me/topologies/<id>` with
  `PermissionError("You only have read access to this shared topology")`,
  so we surface that with a toast BEFORE the network round-trip when the
  user tries to save a topology whose source share is view-only.

`topology-file-ops.js` already gates per-row affordances by `isSharedIn`.
This change ADDS a sub-check on `rowPermission`: when the row is shared-in
AND the permission is `read` (=> view-only), the Duplicate button still
shows (we want users to be able to copy the topology into their own
section), but the row's tooltip surfaces "View-only -- ask the owner for
edit access" when the user hovers the row name (not the share badge).

The save-path guard lives at `topology-file-ops.js::_requestTopologySave`
where we now check `editor._activeSharedPermission === 'read'` before
firing the save request.

### Invariants for the next agent

1. **Never invent a new permission token.** The only legal wire values
   are `read` and `write`. If you need a third level (e.g. "manage"),
   extend the Pydantic regex AND the SQLite migration AND the badge
   helper in one PR.
2. **Always go through `TopologyShare.permissionLabel()`** to display a
   permission. Do not hard-code "View" / "Edit" elsewhere; if you need
   the string, call the helper. This keeps the rename a one-liner if a
   future product decision swaps the terminology again.
3. **Tooltip attribution** stays "Shared by <owner-display> (<View|Edit>)"
   on shared-in topology rows. Both the eye-SVG badge and the row's hover
   tooltip must read the SAME label so users don't see drift between
   "View" in the badge and "read" in the hover bubble.
4. **CSS class semantics are wire-token-based** (`.read` / `.write`),
   not user-facing-label-based. Do NOT add `.view` / `.edit` selectors
   that target the dot-coloured pill; only the new badge has
   `.ta-perm-badge.view` / `.ta-perm-badge.edit` because it's a new
   element with no legacy callers.
5. **No backend changes** in this rename. If you change anything in
   `user_store.py`, `api/domains/router.py`, or `api/schemas.py` because
   of this work, you are violating this invariant and the PR-gate greps
   should catch it.

### Files changed

| Layer | File | What |
|-------|------|------|
| CSS | `topology/styles.css` | `.ta-perm-badge.view` / `.edit` + `.shared-domain-perm-badge` |
| JS | `topology/topology-share.js` | `permissionLabel()` / `permissionTitle()` helpers; rename "Read" -> "View", "Read & Write" -> "Edit" in 4 places |
| JS | `topology/topology-file-ops.js` | Render `.ta-perm-badge` on shared-in / inbox rows; render `.shared-domain-perm-badge` in `renderVirtualRow`; save-path view-only guard |
| HTML | `topology/index.html` | Cache-buster bumps for the three files above |

### Cache busters

* `styles.css?v=20260512d-share-permissions`
* `topology-share.js?v=20260512d-share-permissions`
* `topology-file-ops.js?v=20260512d-share-permissions`

### Multi-user PR-gate confirmation

Ran the five greps from `.cursor/rules/multiuser-by-default.mdc` after
edits -- no new global-path violations. The `permission` field comes
through the existing JWT-protected `/api/domains/...` routes; no new
endpoints, no new SQLite tables, no new `/tmp/*` files.

---

## Spirent IPv6 NDP Encoding + Ping-Seed Cheat -- 2026-05-12

### What shipped

Three cohesive fixes that make TC-IPV6-NDP-BASIC-01 (test 013) deterministically
learn the Spirent IPv6 host into PE-1's EVPN/L3 NDP tables, and prevent the
malformed-frame + silent-stream-reuse failure modes that bit this session.

1. **icmpv6-na default dst_mac is now derived from the IPv6 destination**
   (`/home/dn/SCALER/SPIRENT/spirent_tool.py:_safe_icmpv6_dst_mac`). The old
   default fell back to `ff:ff:ff:ff:ff:ff` when `dst_ip` was a unicast IPv6 --
   that yields an L2 broadcast frame which every modern router (including DNOS
   NDP punt) silently drops. The new helper enforces:
   * `dst_ip = ff02::1` -> `33:33:00:00:00:01` (canonical unsolicited NA)
   * `dst_ip = ff02::1:ff..` -> `33:33:ff:XX:XX:XX` (solicited-node)
   * other multicast -> `33:33:LL:LL:LL:LL` (low 32 bits)
   * unicast `dst_ip` -> derive solicited-node MAC AND warn the caller that an
     unsolicited NA SHOULD use `ff02::1`. L2 broadcast is now refused with a
     hard error and an actionable hint.

2. **`spirent create-stream` no longer silently reuses an existing same-named
   stream.** The old behaviour was a footgun: when the new args differed from
   what was already on the wire, the encoding was silently ignored. Default is
   now `--reuse-policy error` (fail with a clear remediation message); callers
   can opt into `reuse` or `replace` explicitly. The MCP descriptor exposes
   `reuse_policy` so /SPIRENT `spirent_create_stream` callers see the option
   without reading the CLI. `cmd_status` (and therefore `spirent_status`) now
   flags `DUPLICATE_STREAM_NAME`, `DUPLICATE_DEVICE_NAME`, `MALFORMED_ICMPV6_NA`
   (L2 broadcast), and `SUSPECT_ICMPV6_NA` (unicast `dst_ip` + non-multicast
   `dst_mac`) as part of the normal anomalies list -- so the next agent does
   not need to re-discover the dupe/encoding problems we wasted an hour on.

3. **Test 013 recipe gained an `ndp_seed_from_irb` phase that runs `run ping
   <global_ipv6> source-interface <irb_interface>` from PE-1** between stream
   setup and verification. Clarification from the later PW repro: the ping is
   only the Neighbor Solicitation trigger. The packet that proves the PE-1 IRB
   solicit/response path is the fake host's solicited Neighbor Advertisement
   (`S=1/O=1/R=0`, unicast back to the NS requester, TLLA present). The
   all-nodes unsolicited NA form (`S=0/O=1`, `dst_ip=ff02::1`,
   `dst_mac=33:33:00:00:00:01`) remains a valid negative/control packet for
   gratuitous NA coverage, but it must not be treated as proof of PW-side
   EVPN MAC-IP / L2-neighbor promotion.

### Live evidence (PE-1, 2026-05-12)

Before ping seed, with Spirent stream `TEST_NDP_VERIFY_FIX` active and correctly
encoded (`dst_mac=33:33:00:00:00:01`):

```
show ndp interface irb4001        -> table empty
show evpn ndp-table instance EVPN_SI_VPLS_1 -> only local-irb row
```

After `run ping 2001:214:4001::2 count 5 interval 1 source-interface irb4001`:

```
show ndp interface irb4001:
  2001:214:4001::2 | 00:fe:11:00:60:01 | evpn | reachable | irb4001 | Host
show evpn ndp-table instance EVPN_SI_VPLS_1:
  2001:214:4001::2 | 00:fe:11:00:60:01 | dynamic | ge400-0/0/5.4001
show evpn mac-ip-table instance EVPN_SI_VPLS_1:
  L> | 00:fe:11:00:60:01 | 2001:214:4001::2 | ge400-0/0/5.4001
```

Local AC learn + EVPN MAC-IP eligible for RT-2 = exactly the TP pass criterion.

### Test prereq fix that unblocked the CLI category

`_test_ipv6_irb_live_check` in `/home/dn/mcp_common/command_profiles.py` used
to trigger whenever `device_requirements.requires.ipv6 = true`, which fires
on every IPv6 mobility / clear / scale / log / CLI / HA recipe even though
those tests rebuild the IRB during their own phases and do NOT need a host
subnet preflight. It also returned `FAILED` (not `SKIPPED`) when the recipe
had no `irb_interface` field, and built device-bound dnos commands with
`device or recipe.get("device")` -- which collapsed to `None` for recipes
that only declare `device_requirements.primary_device`. The fix:

* `_recipe_requires_ipv6_irb` now requires BOTH an IPv6 hint AND a recipe-level
  IRB binding AND an "IPv6 learning" intent in name/type/source_tc -- so only
  IPv6 NDP learning / advanced IPv6 recipes fire the preflight.
* `_test_ipv6_irb_live_check` resolves the device through
  `device or recipe.get("device") or device_requirements.device or
  device_requirements.primary_device` and returns `SKIPPED` (not `FAILED`)
  when an IRB binding or primary device is missing.

### Why this matters

Combined effect: a /TEST CLI category run can no longer be derailed by a
mobility/clear recipe whose only IPv6 footprint is a `requires.ipv6=true`
flag, and a /SPIRENT IPv6 NDP stream can no longer be created in a malformed
state nor silently inherit stale encoding from a same-named survivor. The
ping-seed phase is the documented way to create the NS precondition; a PASS
requires the corresponding solicited NA response from the service AC host, not
just any in-flight unsolicited NA packet.

## SW-228552 PE-1 PW-Side IPv6 NA MAC-IP Repro -- 2026-05-12

### What the debug proved

For `EVPN_SI_VPLS_1`, a PW-side IPv6 NA source
`00:fe:11:00:60:03 / 2001:214:4001::3` can be learned correctly on RR-SA-2
but fail to become EVPN MAC-IP / EVPN L2-neighbor state on PE-1.

The minimal failing tuple is:

| Layer | Expected / observed |
|---|---|
| RR-SA-2 source AC | `00:fe:11:00:60:03` local on `bundle-100.2001`; internal `local-mac` has `neighbor_keys_size=1` and `neighbor_key=2001:214:4001::3`. |
| PE-1 PW receive | Standard EVPN MAC table can show `v>` via `2.2.2.2`, proving MAC-only propagation over the VPLS PW. |
| PE-1 generic NDP | `show ndp vrf default ipv6-address 2001:214:4001::3` can show reachable on `irb4001`. This is NOT a pass criterion. |
| PE-1 EVPN MAC-IP | `show evpn instance EVPN_SI_VPLS_1 mac-ip-table mac 00:fe:11:00:60:03` and `... ip 2001:214:4001::3` are empty. |
| PE-1 internal L2 neighbor | `show dnos-internal routing fib-manager database evpn evi-id 1 l2-neighbor ip 2001:214:4001::3` returns not found. |

Reference runbook:
`/home/dn/SCALER/FLOWSPEC_VPN/debug_sessions/REPRO_SW-228552_PE1_IPV6_NA_PW_MACIP_MISMATCH.md`.

### Internal command filter gotcha

Do not treat FIB-manager `local-mac` as equivalent to "AC-local" learning.
During this debug, PE-1 standard EVPN CLI marked the MAC as VPLS PW (`v>`),
while the internal command showed the same MAC under `local-mac` with
`pw_address=2.2.2.2` and `neighbor_keys_size=0`.

Commands that need a PW/local origin filter or clearer output:

```text
show dnos-internal routing fib-manager database evpn local-mac
show dnos-internal routing fib-manager database evpn local-mac service-instance <service_name>
show dnos-internal routing fib-manager database evpn evi-id <evi_id> local-mac
show dnos-internal routing fib-manager database evpn evi-id <evi_id> local-mac mac <mac_address>
```

Secondary candidates: `remote-mac` should clarify whether it excludes VPLS-PW
objects, `global-mac-neigh` should expose origin / `pw_address` correlation,
and `l2-neighbor` / `l2-maintained-neighbors` should show source origin when
debugging NDP punt or MAC-IP promotion failures.

### Clear/relearn behavior to track separately

The service-scoped clears below did not crash `routing:fibmgrd` in the
13:02-13:06 run, but the post-clear relearn behavior changed:

```text
clear evpn mac-ip-table instance EVPN_SI_VPLS_1
clear evpn mac-table instance EVPN_SI_VPLS_1
```

After clear, RR-SA-2 relearned only the MAC from the low-rate NA stream, while
MAC-IP / L2-neighbor stayed empty. Keep this separate from the original PE-1
PW MAC-IP promotion bug, because a clean-state clear can remove the RR-SA-2
source-side proof until the local MAC-IP path is re-seeded.

### CPRL gate added after the 13:53 repro

NDP CPRL can fully invalidate the IPv6 NA / MAC-IP punt result. The required
cross-check is now:

```text
show system cprl
show config system cprl
show system logging system-events CPRL_RATE_LIMIT_CROSSED
```

Use the `NDP` row before and after traffic. If `Policer Drops` or `Total Drops`
increase, mark the run CPRL-contaminated and do not remove/re-add EVPN service
yet.

Validated operational/config syntax:

```text
clear system cprl counters [ncp <id>]

system
  cprl
    ndp
      rate 50000
      burst 50000
```

The NDP rate/burst override passed `commit check` on both PE-1 and RR-SA-2 on
12-May-2026 via `dnos_atomic_commit(dry_run=true)` and was rolled back. Use it
only as a temporary, explicitly approved test-epic override, then restore the
default config.

Live 13:53 observation after RR-SA-2 CPRL reset:

* Before pulse: RR-SA-2 `NDP` CPRL counters were `0 / 0 / 0`.
* After the `TEST_SW-228552_TC-IPV6-NDP-BASIC-01_013_RRSA2_PW_TEACH` pulse:
  `RX=19608`, `Policer Drops=13462`, `Total Drops=13462`.
* RR-SA-2 learned the MAC at `13:53:44` but still had empty MAC-IP and
  `l2-neighbor` for `00:fe:11:00:60:03 / 2001:214:4001::3`.
* `fibmgrd_traces` had `EvpnLocalMacAdd` for the MAC and no matching `NDP` or
  `EvpnL2Neighbor` trace lines. This is evidence that the post-clear run is
  CPRL-confounded, not a clean PE-1 PW MAC-IP punt verdict.

Live 13:59 clean CPRL follow-up:

* Permanent `system cprl ndp rate 50000` / `burst 50000` was committed on
  RR-SA-2 and PE-1, then `clear system cprl counters` was run on both.
* The same RR-SA-2 PW teach stream ran from device-local `13:59:49` to
  `14:00:13`.
* RR-SA-2 `NDP` CPRL became `RX=20131`, `Policer Drops=0`, `Total Drops=0`;
  PE-1 `NDP` stayed `0 / 0 / 0`.
* RR-SA-2 still learned only the MAC at `13:59:49`; MAC-IP and
  `l2-neighbor` stayed empty, and `fibmgrd_traces` showed `EvpnLocalMacAdd`
  with no `NDP` or `EvpnL2Neighbor`.
* This removes CPRL as the immediate root cause for the post-clear source-side
  failure. The bug remains MAC-only learning without MAC-IP/L2-neighbor
  promotion. Do not remove/re-add EVPN service until the service config is
  captured and a dry-run rollback plan is prepared.

Live 14:33-14:36 service lifecycle workaround follow-up:

* A user-approved service-only delete/re-add of `EVPN_SI_VPLS_1` on PE-1 and
  RR-SA-2 restored the service and both VPLS PWs without a new `routing:fibmgrd`
  crash. This is documented as a workaround attempt for the post-clear
  MAC-IP relearn bug, not as the original PE-1 PW-side NA mismatch proof.
* Bare `rollback 1` from the operational prompt returned `ERROR: Unknown word:
  'rollback'`; use config mode (`configure`, `rollback 1`, `commit`) when using
  commit-history rollback.
* Delete/re-add changed dynamic EVI IDs (`PE-1` became `2`, `RR-SA-2` became
  `208`). Re-discover EVI IDs before running internal `fib-manager database evpn
  evi-id <id>` evidence commands after any service lifecycle operation.
* The post-workaround low-rate RR-SA-2 PW teach pulse stayed CPRL-clean
  (`RR-SA-2 NDP RX=20616 Drops=0`, `PE-1 NDP=0/0/0`) but still learned only
  MAC `00:fe:11:00:60:03` on RR-SA-2. MAC-IP and `l2-neighbor` remained empty
  on RR-SA-2, and PE-1 had no matching MAC/MAC-IP/L2-neighbor tuple.
* XRAY arrival attempt at 14:40-14:52 exposed capture blockers rather than a
  pcap: auto DP capture cannot map `RR-SA-2 bundle-100.2001` because the
  DUT-facing wire tag is `outer=4 inner=3001`; explicit DNAAS capture on
  `DNAAS-LEAF-B14 ge100-0/0/15` returned `ERROR: Unauthorized to execute the
  command`; RR-SA-2 CP capture on `bundle-100.2001` returned only `Password:`.
  Path resolution still proved the AC route:
  `RR-SA-2 bundle-100.2001 -> DNAAS-LEAF-B15 ge100-0/0/6/bundle-100.215
  -> DNAAS-SPINE-B09 -> DNAAS-LEAF-B14`, with swap to fabric VLAN `215` and
  opaque inner `3001`. Fallback arrival proof from the same run: RR-SA-2
  `show system cprl` NDP `RX=151878`, drops `0/0`; MAC
  `00:fe:11:00:60:03` relearned on `bundle-100.2001` at `14:48:35`;
  `fibmgrd_traces` showed `EvpnLocalMacAdd`/`LocalMacInstall`, but no NDP or
  `EvpnL2Neighbor` trace and MAC-IP/L2-neighbor stayed empty.

### XRAY NDP/NA control-plane capture fix -- 2026-05-12

`/XRAY` now classifies IPv6 NDP / ICMPv6 Neighbor Advertisement and Solicitation
traffic as control-plane traffic by default. `xray_capture_plan` routes filters,
handoffs, or stream metadata containing `icmp6`, `icmpv6`, `ndp`, `icmpv6-na`,
`icmpv6-ns`, `ff02::`, or multicast MAC `33:33:*` to `xray_capture_cp` instead
of trying DP/DNAAS first. An explicit `plane=dp` still wins.

`xray_capture_cp execute=true` now uses the interactive SSH packet-capture path,
feeds the DNOS `Password:` prompt, and no longer gets stuck behind
`dnos_run_show_commands`. Low-numbered transport/MPLS sub-interfaces are
captured exactly, for example `ge400-0/0/4.12` stays
`ge400-0/0/4.12`. When the caller names a high-numbered service sub-interface
such as `ge400-0/0/5.4001`, XRAY first captures on the parent interface
(`ge400-0/0/5`). If DNOS rejects that target with
`ERROR: Unable to capture, interface is l2-service enabled`, XRAY retries the
inferred IRB interface (`irb4001`). The IRB fallback rewrites Ethernet MAC BPF
clauses out of the filter because it is no longer tied to a physical Ethernet
interface. Do not use `interface any` for this path: DNOS can emit
`ERROR: data link type LINUX_SLL2` after printing valid packet lines, which
makes XRAY mark an otherwise useful capture as failed. Also do not use bare
`run packet-capture ncc count ...`: live `cmd search packet-capture` on PE-1
shows DNOS requires either `interface <if>` or `in-band-vrf <vrf>` after
`run packet-capture ncc`.

Follow-up from the PE-1 `irb4001` IPv6 NDP repro (2026-05-13): if DNOS
`run packet-capture ncc interface <if>` fails or is blind to packets the
routing-engine shell can see, `/XRAY xray_capture_cp` supports
`capture_backend=routing_shell_tcpdump`. That backend enters
`run start shell`, runs `tcpdump -ni <interface>`, and attaches the
dnos-config counter snapshot `show interfaces counters <interface> | no-more`.
Routing-shell Linux interface names are not always DNOS names: IRBs may exist
as `irb4001`, but DNOS sub-interfaces such as `ge400-0/0/4.12` and bundle
sub-interfaces such as `bundle-100.12` must be translated from
`ip -o link show` aliases (for example to `g00004.000c` or `b-100.12`)
before tcpdump. Use `show interfaces counters <if>` for packet-rate evidence;
do not rely on utilization percent because tens of kpps of 86-byte packets can
round to `0%` on 100G links.

XRAY DP/PW/MPLS capture reform follow-up:

* `xray_capture_dp` no longer treats one narrow BPF as the proof path. Loop
  mirror capture uses a broad-first ladder by default: first run a no-filter
  capture on the resolved capture interface without a forced `count`, then run
  the requested `filter-expression` only after the broad capture proves the
  surface is seeing packets. XRAY sends Ctrl-C after an idle/window timeout and
  preserves the DNOS summary (`N packets captured`). Callers can force bounded
  behavior with `count_mode=fixed` or `count_mode=unlimited`.
* `xray_capture_cp` and `xray_capture_dp` support DNOS `file-name` captures via
  `save_pcap=true`. XRAY writes to a DUT-side pcap, SFTP-fetches it to
  `/home/dn/.xray_captures/mcp/` (or `local_pcap_path`), optionally deletes the
  remote pcap, and can reuse the topology XRAY Mac delivery helper with
  `deliver_to_mac=true`.
* DP captures that execute successfully but see no packet lines now return
  `EXECUTED_VIA_LOOP_NO_PACKET_OUTPUT`; a `Listening on ...` banner or command
  success alone is not evidence that PW/MPLS traffic arrived.

Live validation on RR-SA-2 showed the new behavior:

* Plan for `bundle-100.2001` with `ether src 00:fe:11:00:60:03 or icmp6`
  returned `plane=cp` and suggested `xray_capture_cp`.
* CP capture fed the password prompt, first hit the expected l2-service AC
  rejection, then retried the inferred IRB with `run packet-capture ncc
  interface irb4001 count 6 filter-expression "icmp6"`.
* No-interface NCC capture can still return zero packet output for a short repro
  window; XRAY preserves that as evidence instead of treating a `Listening on`
  banner as packet proof. Fallback arrival proof remains CPRL `NDP` RX plus MAC
  relearn timestamps until a pcap path with visible packet lines is enabled.

### Solicited-NA / IRB ping-seed validation -- 2026-05-12 15:54

The earlier `/TEST` Basic Functionality behavior was confirmed to depend on
the recipe's PE-1 IRB ping-seed / fallback-host phases. Correct framing: the
PE-1 ping is only the NS/solicitation trigger. The decisive packet is the
fake host solicited NA sent from the RR-SA-2 service AC (`bundle-100.2001`) in
response. The saved TEST proof for `RUN_20260512_092103_PE-1` shows Step 2
PASS included
`tp_step_02_ipv6_nd_seed_from_irb` and `tp_step_02_ipv6_nd_fallback_protocol_start`,
while Step 4 still failed at `tp_step_04_pe1_pw_source_installation_verify`
because PE-1 did not install EVPN MAC-IP VPLS-source evidence for
`2001:214:4001::3 / 00:fe:11:00:60:03`.

Live validation after the service delete/re-add:

* Baseline had no PE-1 generic NDP and no PE-1 EVPN MAC-IP for
  `2001:214:4001::3`; RR-SA-2 MAC/MAC-IP was also empty.
* DNOS syntax was validated by `cmd search ping`:
  `run ping <dest_ip6> ... [source-interface <src_interface>]`.
* `run ping 2001:214:4001::3 count 3 source-interface irb4001` from PE-1
  returned `3 packets transmitted, 0 received`, but the NS plus the fake host
  solicited NA response still created PE-1 generic NDP
  `2001:214:4001::3 -> 00:fe:11:00:60:03` on `irb4001` and PE-1 MAC-only VPLS
  state via `PW address: 2.2.2.2`.
* RR-SA-2 simultaneously learned the host as local on `bundle-100.2001` and
  created local MAC-IP for `2001:214:4001::3`.
* A second PE-1 ping after NDP was reachable still returned 100% loss, and
  PE-1 EVPN MAC-IP plus internal `global-mac-neigh` / `l2-maintained-neighbors`
  remained empty.

Conclusion: the PE-1 IRB ping seed is valid only when paired with a service-AC
host response. It proves that NS crossed toward RR-SA-2 and that a solicited NA
from the RR-SA-2 AC traversed back far enough to drive NDP resolution and
MAC-only PW learning. It does not prove ICMP echo forwarding or PE-1 EVPN
MAC-IP/L2-neighbor promotion for the PW host. Keep this as a separate
validation path from the pure unsolicited-NA-over-PW bug. If the fake solicited
NA from the RR-SA-2 AC is present and RR-SA-2/PE-1 do not update the expected
MAC-IP/NDP tables, classify the missing promotion as the bug.

Code-backed packet contract:

* The solicit/response repro requires a solicited NA from the RR-SA-2 service
  AC host: ICMPv6 type `136`, `S=1`, `O=1`, `R=0` for a host, valid Target
  Address, TLLA option type `2` carrying the host MAC, hop-limit `255`, and a
  unicast IPv6/Ethernet destination back to the requester. It is not the same
  as an all-nodes gratuitous/unsolicited NA.
* `ProxyArpPacketAnalyzer.cpp` rejects solicited NA (`S=1`) sent to multicast
  IPv6 destinations, validates the Target Address and TLLA MAC, and only then
  sets `shouldSendUpwards`.
* `ArpNdpCodec.cpp` parses NA by using the Target Address as `srcIp` and TLLA
  as `srcMac`, then `MessageParserUtils::CreateL2NeighborUpdateFromRawMessage`
  creates a local L2-neighbor update from that parsed source tuple.
* Existing `dn_spirent_main` native `icmpv6-na` streams are `S=0/O=1`,
  `dst_ip=ff02::1`, `dst_mac=33:33:00:00:00:01`; that is the unsolicited
  packet form. It is valid for local-AC gratuitous learning coverage, but it is
  not proof of the PE-1-NS / RR-SA-2-host solicited-NA path.

## Device Split Colouring + Recent-Colours Polish -- 2026-05-12

### What shipped

Two cohesive UI changes ship together because they share the device colour
pipeline:

1. **Recent-colours polish** (`topology/topology.js` + `topology/topology-color-popups.js`).
2. **Device split colouring** (`device.colorLeft` + `device.colorRight`).

### Recent-colours contract

- Cap: `DEFAULT_RECENT_COLORS_LIMIT = 8` (was 4). Defined once at the top of
  `topology.js`; do NOT hard-code 4 or 8 elsewhere.
- Per-user persistence: `localStorage` keys `recentColors` and `pinnedColors`
  are scoped by `topology-auth.js` so two operators on the same machine never
  share swatches. NO server round-trip -- the multi-user contract is satisfied
  by the username-prefixed `localStorage` key.
- MRU semantics: `editor.addRecentColor(hex)` dedupes, normalises to lowercase
  `#rrggbb`, and re-orders the touched entry to the front. Pinned colours are
  never displaced.
- Pinned colours: `editor.togglePinnedColor(hex)` and `editor.isColorPinned(hex)`.
  Pinned colours render in a dedicated "Pinned" row above the recents row and
  carry a small `--dn-orange` dot indicator. Right-click on any swatch opens
  a context menu (`color-swatch-context-menu`) with Pin / Unpin / Remove.
- Keyboard: every swatch is `tabindex="0"` with Enter / Space binding to
  `pick(color)`. Focus state uses `--dn-cyan` outline; active state uses
  `--dn-orange` border (see `.color-popup-swatch:focus-visible` /
  `.color-popup-swatch.is-active` in `topology/styles.css`).
- NO EMOJIS anywhere in the popup. Use the inline SVG icons defined inside
  `topology-color-popups.js` (`<svg width="14" height="14"><path .../></svg>`)
  and the `--dn-orange` / `--dn-cyan` / `--dn-cloud` brand variables.

### Split-colour data model

- Storage: a device is in **split** mode when BOTH `device.colorLeft` AND
  `device.colorRight` are present, non-empty strings. Otherwise it is **solid**
  and `device.color` is the single fill (legacy behaviour).
- This is intentionally additive -- legacy topologies with only `device.color`
  load, save, and render unchanged. New topologies serialise the split fields
  only when both are populated. The cleanup loop in `topology-file-ops.js`
  ::generateTopologyData strips `_renderColorOverride` (the rendering-pass
  transient) but preserves `colorLeft` / `colorRight` automatically.
- Decision rationale (vs. an object-typed `color`): adding two flat sibling
  fields was the simpler migration. It keeps `device.color` as the canonical
  solid fallback for every legacy code path (link-end shading, badges,
  Spirent-fabric tag colour, etc.) and adds two new fields that are
  transparently ignored by anything that has not been split-color-aware.

### Split-colour rendering

- `topology/topology-canvas-drawing.js` :: `drawDevice` detects split mode and
  performs TWO clipped render passes:
  1. Save canvas state, translate to the device centre, apply the device
     rotation, clip to the LEFT half-plane in local coordinates, set
     `device._renderColorOverride = device.colorLeft`, call the existing
     `_drawDeviceBody(...)` pipeline, restore.
  2. Same pattern for the right half with `device._renderColorOverride =
     device.colorRight`.
- `topology/topology-device-styles.js` :: `_safeDeviceColor(device)` is the
  single hook that propagates the override into gradient stops, label strokes,
  and 3D depth shading. All per-shape renderers (circle, classic, simple,
  hex, server) read fill colour through this helper, so every device style
  (router glyph, server tower, hex router, etc.) gets clean half-painting
  for free -- no per-style code duplication.
- Borders, labels, selection halo, and the device icon are drawn AFTER the
  two clipped passes (single, full-frame draw), so the seam is invisible and
  the label / selection ring straddle the midline cleanly.
- Non-rectangular shapes: the clip is to the device's local **bounding-box**
  half-plane (x < 0 vs. x > 0 in local-space, post-rotation). Filled glyphs
  (hex router, cloud) therefore get their painted area split along the
  vertical midline of the bounding box -- borders and stroked outlines are
  drawn in the post-pass and so are NOT duplicated.
- `device._renderColorOverride` is ALWAYS deleted after the second pass. It
  must never persist; `topology-file-ops.js` defensively strips it during
  save as a belt-and-suspenders measure.

### Split-colour picker UX

- The popup (`topology-color-popups.js`) gains a `Solid / Split` segmented
  toggle when the target object is a device. Switching modes is non-destructive:
  - Solid -> Split: seeds `colorLeft` = `colorRight` = current `device.color`.
  - Split -> Solid (`setDeviceColorMode(device, 'solid', { keepSide })`):
    `device.color` becomes the chosen side; the other side is cleared.
- Split layout: a 2-column grid (`color-popup-split-grid`) with one column per
  half. Each column has its own header (Left / Right), live hex readout,
  6x4 palette of curated colours, and a custom `<input type="color">`. Below
  the columns sits a footer with **Swap sides** and **Revert to solid (keep
  left|right)** buttons.
- Suggestion chips: at the top of each Split column we may render a
  `color-popup-suggested` chip (>= 50% dominant) or up to two
  `color-popup-suggested-hint` chips (mixed neighbourhood). Clicking applies
  the suggested colour to that side ONLY. The suggestion is never auto-applied.
- Device editor modal (`topology-device-editor.js`): the modal stays a
  "simple" entry point. If a device is in split mode and the user opens the
  modal, an inline `[INFO]` hint appears below the colour input with an
  "Edit halves" button that closes the modal and opens the canvas Split
  picker. Editing the modal's colour reverts the device to solid (this is
  the documented contract; the hint warns the operator).

### Neighbour-suggestion algorithm

For a device `D` and a side `side in {'left','right'}`:

1. Enumerate links connected to `D` via `editor.getConnectedDevicesAndLinks`
   (already used elsewhere; reuse, do not re-implement).
2. For each link `L`, determine which side `L` exits `D` by anchor x vs.
   `D.x` (`anchor.x > D.x` -> right; `anchor.x < D.x` -> left). If `L` uses
   a custom anchor or bundle port, prefer the resolved anchor canvas x;
   otherwise use the neighbour device's centre x (the existing
   `_resolveLinkAnchor` helpers already produce the right value).
3. Keep only links on `side`. For each kept link, fetch the **far** device `N`.
   - If `N` is split-coloured, use `N`'s FACING side (i.e. when `N` is to the
     right of `D`, use `N.colorLeft` because that's the half facing `D`,
     and vice versa).
   - If `N` is solid, use `N.color`.
4. Tally colour frequencies. The dominant colour is the most common value
   whose share is `>= 0.5` of the side's neighbour count. If no colour
   reaches >=50% the function returns a `hints` array of the top two
   candidates instead, and the popup renders them as small hint chips.
5. Zero neighbours on a side -> `null` (no chip rendered).
6. Implementation: `editor.getNeighborColorSuggestion(device, side)` in
   `topology.js` (idempotent, no caching). Recomputed every time the popup
   opens, so neighbour edits are picked up next time without any cache
   invalidation logic.

### Files touched (for the next agent)

| File | Lines | Why |
|---|---|---|
| `topology/topology.js` | ~10840-11200, ~10854-10995 | recents/pinned MRU helpers; split-mode state mutators; neighbour suggestion |
| `topology/topology-color-popups.js` | full rewrite (~530 lines, v2.0.0) | new popup markup, mode toggle, split columns, suggestion chips, swatch context menu |
| `topology/topology-canvas-drawing.js` | `drawDevice` ~40-150 | two-pass clipped render for split mode |
| `topology/topology-device-styles.js` | `_safeDeviceColor` ~587-594 | honour `device._renderColorOverride` |
| `topology/topology-device-editor.js` | `_renderSplitColorHint` + `updateDeviceEditorProperty` | modal split-hint + revert-on-solid-edit |
| `topology/topology-file-ops.js` | `generateTopologyData` ~1893 | strip `_renderColorOverride` on save |
| `topology/styles.css` | ~26079-26488 | popup, swatch, split-grid, context-menu styles |
| `topology/index.html` | toolbar `?v=` cache busters | force-reload after refresh |

Cache buster suffix: `?v=20260512a-split-color`.

### Invariants future agents must preserve

- Legacy single-colour devices (only `device.color` set) MUST render and save
  identically to pre-2026-05-12 behaviour. Add a quick regression test by
  loading any pre-this-date topology and saving it; the JSON `objects[].color`
  field must be byte-identical for devices that never entered split mode.
- `device.colorLeft` / `device.colorRight` only appear in the JSON when BOTH
  are populated; do NOT serialise empty / null halves.
- `_safeDeviceColor` is the only place that reads `_renderColorOverride`.
  Adding a new device-style renderer that reads `device.color` directly will
  silently skip split-mode painting. Always go through `_safeDeviceColor`.
- The neighbour-suggestion threshold is 50%. If a future feature wants to
  tune this, add a `editor.dominantThreshold` const at the top of
  `topology.js` and reference it from `getNeighborColorSuggestion` -- do not
  inline a magic number.

### Polish pass II -- 2026-05-12c (visual refinements + copy-style)

A follow-up pass tightens the visual rendering and brings copy-style up to
parity with split mode. Three things landed together:

#### 1. Seam treatment: paper-fold bevel

The vertical midline between the two halves is now drawn as a subtle 2-pixel
"paper-fold" bevel (1px lighter line on the left, 1px darker on the right).
Implementation lives in `topology-canvas-drawing.js` :: `_paintSplitSeamBevel`
and runs AFTER the two clipped fill passes but BEFORE borders / glyphs /
labels.

**Why paper-fold over the alternatives:**

| Option | Verdict | Why |
|---|---|---|
| Thin neutral 1px stroke in `--dn-cloud` | rejected | reads as a hard divider, fights the brand's "elegant" feel |
| 2-3px alpha-blended gradient blend | rejected | dilutes the two-colour message; halves look "muddy" at small zooms |
| **Paper-fold (light/dark bevel)** | **picked** | reads as an intentional surface fold; works across zoom levels and across light/dark fill luminances because the asymmetric pair always produces visible contrast against at least one half |

The bevel is clipped exactly to the device shape (circle / hex / rect /
classic). Lines are `lineWidth = 1`, `lineCap = 'butt'`, with `globalAlpha`
0.35 (light side) / 0.30 (dark side) so it never overpowers the fill. The
helper iterates the same shape path used by `_drawDeviceBody`, so when a new
device-style ships its outline (e.g. a future "diamond" shape) the seam
bevel automatically follows.

#### 2. Label legibility backdrop

When a device is in split mode AND its label sits ON TOP of the device body
(centred label, not below-device label), `drawDeviceLabel` now paints a
faint rounded-rect backdrop behind the label text. The backdrop is:

- Only drawn when `device.colorLeft && device.colorRight` (split mode).
- Only drawn for `labelPosition === 'center'` or default (label-over-body).
  Below-device labels do not need a backdrop because they don't straddle
  the seam.
- Backdrop colour picks `--dn-navy-deep` if the label text is light
  (luminance > 0.6) and `--dn-cloud` if the label text is dark. Alpha is
  `0.55` -- visible enough to suppress the seam contrast but transparent
  enough to keep the halves readable.
- Corner radius `4px`, padding `3px` horizontal / `1px` vertical.

Implementation: `topology-canvas-drawing.js` :: `drawDeviceLabel` after the
font metric measurement and before the per-letter outline stroke pass.

#### 3. Selection halo, icon centring, per-half shading

Audit confirmed (no code changes required):

- **Selection halo** in `drawDevice` is drawn from the post-pass shape path
  (single full-frame stroke), so it crosses the seam cleanly without
  doubling.
- **Glyph centring**: all `_drawDeviceBody*` renderers (circle, classic,
  simple, hex, server, router, cloud) draw the centre glyph in the
  post-pass, using `iconColor` (typically white or `--dn-cloud`) which is
  NOT routed through `_safeDeviceColor`. The glyph therefore renders once
  in a single colour regardless of which half it overlays.
- **Per-half shading**: every gradient / 3D depth helper reads its base
  colour through `_safeDeviceColor(device)`, which honours
  `device._renderColorOverride` set by the two clip passes. Each half
  derives its shading from its OWN base colour. Verified visually on
  router, server, hex, and classic styles.

#### 4. Picker UX polish (split mode)

`topology-color-popups.js` got a small batch of polish edits inside the
`renderSplitMode()` helper. CSS lives in `topology/styles.css` under the
`/* Split-mode picker polish 2026-05-12c */` block.

| Element | Polish |
|---|---|
| Left / Right column header | Small-caps brand tag (`.split-col-header-tag`) with `--dn-orange` text on a pale pill background. Replaces plain label text. |
| Grid divider | A `1px` vertical inset between the two columns drawn via a CSS `background-image: linear-gradient(...)` on the grid container, so it tracks the grid gap automatically. |
| Suggestion chip chevron | Directional chevron SVG appended to each `.color-popup-suggested` / `.color-popup-suggested-hint` chip pointing LEFT or RIGHT depending on which column the chip is in. Uses `--dn-cyan` accent. |
| Swap button icon | Replaced the text "Swap" with a new `<symbol id="ico-swap-horizontal">` (two opposing arrows) defined in `index.html`. Title attribute reads "Swap left <-> right halves" for accessibility. |
| Revert buttons | Pulse-confirm animation (`@keyframes split-revert-pulse`) plays on click for 320ms so the user gets immediate feedback. Inline `[INFO]` note above the footer explains "Revert to solid keeps the chosen side and clears the other" so the operator knows what's about to happen. |

#### 5. Copy-style integration contract

`topology-context-menu-handlers.js` :: `copyObjectStyle` and
`_applyStyleToObject` are now split-aware. Behaviour matrix:

| Source state | Target state | Paste result | Notes |
|---|---|---|---|
| solid | solid | target.color := source.color | unchanged from pre-2026-05-12 |
| solid | split | target reverts to solid (clear `colorLeft`/`colorRight`); target.color := source.color | same contract as device-editor modal "edit reverts to solid" |
| split | solid | target enters split mode; target.colorLeft := source.colorLeft, target.colorRight := source.colorRight, target.color := source.colorLeft (fallback for legacy code) | one paste makes the target split |
| split | split | target.colorLeft := source.colorLeft, target.colorRight := source.colorRight, target.color := source.colorLeft | both halves overwritten |
| split source -> link / shape / text-block | n/a | target.color := source.color (effective fill, which is `colorLeft`); `colorLeft`/`colorRight` are NOT copied to non-device targets | flat colour fallback, no schema pollution |
| text-block / shape / link -> split device | reverts to solid | target.color := source colour; `colorLeft`/`colorRight` cleared | matches "edit reverts to solid" contract |

The full list of fields that `copyObjectStyle` captures from a device source
(unchanged pre-fields, plus the two new ones):

```
color, colorLeft, colorRight, isSplit (transient signal),
labelColor, labelSize, fontFamily, fontWeight, fontStyle,
shape, size, badges (icons/badges array),
labelPosition, showLabel, opacity, borderColor, borderWidth
```

`isSplit` is a transient flag set on the in-memory `copiedStyle` object so
that `_applyStyleToObject` can distinguish "source had a split" from
"source happened to have a stale `colorLeft` from a previous edit"; it is
NOT a serialised field on any device.

The CS-MS (Copy Style + Multi-Select) batch path delegates per-object to
the same `_applyStyleToObject`, so multi-select paste respects the
split/solid transitions automatically.

#### 6. Files touched (this pass)

| File | Region | Why |
|---|---|---|
| `topology/topology-canvas-drawing.js` | `drawDevice` (seam bevel post-pass), `_paintSplitSeamBevel` (new helper), `drawDeviceLabel` (split-mode backdrop) | paper-fold seam + label backdrop |
| `topology/topology-color-popups.js` | `renderSplitMode` (column headers, swap icon, INFO note, suggestion chevrons) | picker polish |
| `topology/topology-context-menu-handlers.js` | `copyObjectStyle` (capture split fields), `_applyStyleToObject` (split-aware paste, cross-type revert) | copy-style integration |
| `topology/index.html` | `<symbol id="ico-swap-horizontal">` added; `ctx-copy-style` tooltip mentions split support; cache busters bumped | new icon + UX |
| `topology/styles.css` | `/* Split-mode picker polish 2026-05-12c */` block: grid divider, header tag, suggestion chevron, INFO note, pulse keyframes | picker styles |

Cache buster suffix: `?v=20260512c-split-refine`.

#### 7. Regression invariants (in addition to v1)

- The seam bevel MUST be clipped to the device shape. If a future device
  style adds a new shape (e.g. diamond), it must register its path with
  `_paintSplitSeamBevel`'s shape switch, otherwise the bevel will draw
  outside the visual bounds.
- The label backdrop is ONLY drawn in split mode. Solid-colour devices
  must look pixel-identical to pre-this-pass behaviour. Confirm by
  toggling a device to split, then reverting; the label region should
  re-render cleanly with no backdrop residue.
- The `isSplit` flag on `copiedStyle` is a runtime-only signal. It MUST
  NOT be serialised onto a device or persisted in localStorage as part
  of a clipboard payload.
- `_applyStyleToObject` cross-type branches (text-to-device,
  shape-to-device) MUST clear `colorLeft`/`colorRight` on the target when
  the source is not a device, otherwise a target previously in split
  mode will keep stale halves.

## Name Mismatch Prompt Auto-Repair Gate -- 2026-05-12

- `DeviceMonitor._shouldAutoRepairLabel(currentLabel, cfgHostname)` in
  `topology/topology-device-monitor.js` is the silent-rename gate consumed by
  the SSH dialog Save path (via the `shouldAutoRepairLabel` opt passed to
  `applyHostnameCanvasMismatch`) AND by the background monitor refresh. Both
  paths now require `currentLabel` to be a generated canvas placeholder
  (`NCP`, `NCP-<n>`, `S`, `S<n>`) before silently aligning the canvas label
  to the live config hostname.
- Any user-defined label -- even one that happens to look like a DNOS hostname
  (e.g. `PE-7`, `Router-A`, `EDGE-PE-1`) -- must always defer to the explicit
  mismatch popup (`CanvasDrawing._showMismatchPopup`) so the operator can
  choose Rename-canvas / Change-device-hostname / Dismiss. Before this fix the
  DNOS regex (`\b(PE|RR|SA|CL|NCC|NCP|NCM|NCF|LEAF|SPINE|DUT|CDNOS|YOR|BGW)\b`)
  applied to `cfgHostname` alone would silently overwrite the operator's
  intentional canvas label and the post-save 120ms `showCanvasHostnameMismatchPrompt`
  timer would short-circuit because `_hostnameMismatch` had already been cleared.
- Regression coverage lives in
  `topology/tests/test_device_onboarding_frontend_unit.py::test_auto_repair_label_only_replaces_generated_canvas_labels`.
  Keep the `isGeneratedCanvasLabel` guard and the `if (!isGeneratedLabel) return false`
  early-return when refactoring; both phrases are asserted.
- Existing protections that must NOT regress:
  - GI-serial suppression (`giSerialIdentity`) in `applyHostnameCanvasMismatch`.
  - Inventory-label precedence loop (`global._deviceInventory`) that clears
    `mismatch` when the canvas label is an inventory hostname.
  - Backend case-insensitive `hostname_mismatch` flag in
    `routes/bridge_helpers.py` (informational; the frontend remains the source
    of truth for popping the prompt).

## DEBUG Crash/Core Analysis -- 2026-05-11

- `/debug-dnos` crash investigations must use `debug_core_analyze` for
  `SIGABRT`, `sig-6`, assertion, `core-fibmgrd`, or process-failed symptoms
  before declaring the trigger understood. The wrapper calls dnos-config
  `dnos_core_analyze` so core handling remains MCP-backed rather than ad-hoc
  shell work in chat.
- Routing-engine core packages live under
  `/core/core_dumps/containers/routing_engine/`. The tar contains a nested
  `routing_engine/core-<process>...lz4.gz`; GDB cannot read this directly.
  The required sequence is: extract tar, gunzip to `.lz4`, run `unlz4` to
  produce the raw core, then run batch `gdb -nx -batch -ex bt <process> <core>`.
- Core evidence must capture `process.info`, `gitcommit`, GDB backtrace frames,
  and extracted process traces (for fibmgrd, at minimum
  `L2NeighborAgeMonitor` and the crashing address/MAC filter). The crash key
  from the core/trace, not the last repro traffic MAC, determines what traffic
  pattern to reconstruct.
- `/debug-dnos` config-history checks must use DNOS rollback-aware show syntax:
  `show config compare rollback <id>`,
  `show config compare rollback <id> rollback <id>`, and `show rollback <id>`.
  `show config rollback <id>` is invalid and should not be generated by tools
  or agents.
- Debug-driven Spirent repro traffic must default to low rate. `spirent_create_stream`
  and modifier stream creation block `rate_mbps >= 10` unless the caller
  explicitly supplies `allow_high_rate=true`. The CLI default for ordinary
  `create-stream` is 1 Mbps.
- For EVPN VPLS SI `L2NeighborAgeMonitor::ProcessBatch` crashes, the working
  repro is ownership history plus natural probe failure: learn MAC/IP via the
  PW side first, then learn the same MAC/IP locally, then remove all Spirent
  responders so L2 maintainer probes fail. Operator clear alone is insufficient
  unless it preserves a stale `m_EvpnDB` entry. Always document internal
  l2-neighbor DB, l2-maintained-neighbors, probe raw traces, delete conversion,
  assertion, system-events, and core backtrace.
- EVPN/VPLS/VPWS `/debug-dnos` investigations must include a service snapshot
  layer: `show config network-services evpn instance <service>`, AC/IRB
  interface config when known, `show evpn instance <service> detail`, internal
  local/remote MAC DB, `show dnos-internal routing fib-manager database
  global-mac-neigh` (prints `L2EvpnLocalMacToNeighbor`, the `m_EvpnDB` side
  index), EVPN L2-neighbor DB, and L2-maintained-neighbors. Bug descriptions
  should present this as network/service evidence, without code internals.
- Ticket-style `/debug-dnos` bug descriptions must start with topology and
  service context before proof: participating devices, loopbacks/peers,
  EVI/RD/RT/site IDs, AC/IRB interfaces, VPLS PW status, and raw config/service
  snippets. A Jira reader should understand the lab topology before reading the
  failure traces.
- Chat-facing `/debug-dnos bug description` requests must route through
  `debug_bug_description`, not freehand summaries. The payload must include
  topology/service context, a 2-3 sentence observed-bug summary, step-by-step
  expected-vs-observed proof, exact prompt/command input, timestamped raw output,
  and optional trace/container/shell DB tables when relevant. Missing timestamps,
  commands, or raw outputs must be printed as warnings in the answer.
- `/debug-dnos bug description` now treats raw before/after service and
  interface configuration as first-class required evidence. Repro collection
  should pass `service_name`, `ac_interfaces`, and `irb_interfaces` to
  `debug_show_bundle` before and after the trigger so the final description can
  render paired raw outputs for `show config network-services evpn instance
  <service>`, `show evpn instance <service> detail`, `show config interfaces
  <AC/IRB>`, and `show interfaces <AC/IRB>`. If those snapshots are absent, the
  renderer must warn instead of silently summarizing.
- `/debug-dnos` Jira-grade show bundles must include device-local timestamps in
  the raw evidence, captured in the same bundle before the proof commands when
  possible. Session-log wall-clock headings are useful but not sufficient by
  themselves; if an older run missed per-command device timestamps, the write-up
  must say so and use only timestamps embedded in config output, trace lines,
  process history, or core filenames.
- `/debug-dnos` proof blocks must preserve the actual device prompt/command
  input line together with the raw output body. A raw output excerpt without the
  command that produced it is not sufficient for Jira-grade evidence.
- Empty raw output is valid evidence for negative lookups such as
  `show evpn mac-ip-table ... ip <addr>` and must render explicitly as
  `(empty output)`, not as `RAW OUTPUT MISSING`. Missing means the command was
  not captured; empty means the device returned no rows.
- `/debug-dnos` table proof blocks must preserve the table headers in the raw
  output, not just the matching data rows. For trace proof, every block must
  state the process/component and source trace file (for example
  `fibmgrd` from `routing_engine/fibmgrd_traces` or `wb_agent` from
  `datapath/wb_agent*`) so the reader can identify which pipeline layer saw or
  missed the event.

## Canvas Toolbar, Shape Hitboxes, Laser Strokes -- 2026-05-10

- The left canvas toolbar is a compact icon rail plus a small active-tool
  flyout. Do not reintroduce the old bulky stacked accordion UX for primary
  tool selection; preserve the `tool-rail-mode` / `.tool-side-panel`
  contract, keep the rail narrow, and use openable nested option cards inside
  the flyout for dense tool settings on low-height screens.
- Shape selection hit-testing must follow the rendered geometry, not the
  rectangular bounding box. Route canvas shape picking through
  `ShapeMethods.hitTestShape(...)` so circles/ellipses, diamonds, triangles,
  line-like shapes, arrows, and merged-background borders avoid large empty
  false-positive regions.
- Laser pointer trails are transient UI state split by explicit stroke ids.
  A new mouse-down begins a new laser stroke with a render break; mouse-move
  and mouse-up may extend only that active stroke. Separate clicks must never
  interpolate or draw a bridge segment between old and new click locations.

## Device Monitor Identity / Topology Events Noise -- 2026-05-11

- `TopologyDeviceIdentity.validateResponseForDevice()` must compare management
  IPs only when the backend returned IP-like values. Some cluster identity
  payloads can carry hostnames in management fields; those should not create a
  false IP mismatch against a valid canvas host IP.
- `DeviceMonitor` still drops stale/mismatched context responses, but identical
  mismatch reasons warn only once per session and later repeats are debug-level
  with a counter. The dropped result is stamped on
  `device._monitorLastIgnoredContext` for diagnosis and cleared after the next
  accepted context.
- `/api/topologies/events` uses a single app-managed EventSource from
  `topology-file-ops.js`. Reconnects are timer-deduped, cleared on logout, and
  app logs must never print the tokenized EventSource URL. Browser DevTools may
  still show the native URL because EventSource cannot attach Authorization
  headers, but application logs should use sanitized status only.

## Groups UX Visibility Contract -- 2026-05-10

- Manual group colors are persistent topology presentation state. New groups get
  a deterministic palette color from `GroupManager.colorForGroupId(...)`, and
  `GroupManager.ensureGroupColor(...)` repairs older groups without overriding
  an existing `groupColor`.
- Manual group visibility is runtime per-user UI state, stored in the
  `groups_panel_state_<username>` localStorage record under
  `manualGroupVisibility`. It is intentionally not saved into topology objects
  or undo snapshots.
- History restore, undo, and redo must reapply `editor._groupVisibility` through
  `GroupManager.applyVisibility()` after object snapshots are restored. This
  prevents Ctrl/Cmd+Z from making hidden groups reappear unless the operator
  explicitly uses the Groups panel visibility controls.
- Persistence paths must strip `_hiddenByGroup` and the group-owned `_hidden`
  flag before saving/exporting/recovery snapshots. Keep actual group identity
  fields (`groupId`, `groupLeaderId`, offsets, `groupName`, `groupColor`) intact.
- The top-bar Groups button and per-object device toolbar Group button are
  intentionally stronger visual affordances because they now affect canvas
  visibility, selection, and interaction state, not just cosmetic grouping.
- The Groups panel should follow the modern Topologies/domain-row visual
  language: rounded frosted panel, compact uppercase labels, color-accented
  cards, strong color chips, and pill-style actions. Keep future visual edits
  in that family rather than reverting to legacy flat toolbar rows.
- Creating a manual group from the Groups panel must not require a canvas
  selection. Empty groups are valid panel-created group definitions and should
  remain available for later object assignment through the existing Group
  object actions. If two or more objects are already selected, the same New
  action may still group that selection immediately.

## TEST Compiled Recipe Validation -- 2026-05-10

- TEST recipes can declare mandatory related hierarchy/service/section config in
  `required_config`, `required_config_sections`, `required_hierarchies`,
  `metadata.required_config*`, or prerequisite entries with checks like
  `required_config` / `config_sections`. Entries should carry `device`,
  `hierarchy` or `show_command`, optional `must_contain`, and optional
  `config_text`. `test_prerequisites_check` lists these as live prerequisites;
  `test_prerequisites_live_check` verifies them with `dnos_run_show_commands`
  before execution and returns `PREREQUISITES_FAILED` plus an approval-gated
  `dnos_atomic_commit` or `dnos_multi_device_commit` dry-run payload when they
  are missing. `test_run_gated` must stop on this blocker rather than running a
  test whose prerequisite service hierarchy is only partially present.
- Shared MCP responses must remain compact enough for Cursor's native MCP client
  to keep its SSE session alive. `mcp_common.render.format_mcp_response` spills
  oversized structured payloads to `~/SCALER/TEST/_shared/mcp_large_results/`
  and returns a path plus top-level key index instead of inlining huge JSON.
  TEST tools should still prefer compact status payloads and artifact paths for
  category/background polling.
- `dnos-config` must not let one corrupt monitor record in
  `~/SCALER/db/devices.json` break all `dnos_run_show_commands` calls. The
  resolver strips invalid JSON control bytes and salvages valid top-level
  device records, skipping only the malformed device object.
- MCP subprocess timeouts must kill the full process group, not just the direct
  child. TEST often calls `mcp_cli.py`, which then calls tools like
  `spirent_tool.py`; leaving grandchildren alive after timeout makes native MCP
  status look crashed or wedged. `mcp_common.crashguard.run_command` is the
  canonical subprocess wrapper and starts children in their own session for this
  reason.
- TEST background category jobs must expose phase-level progress. `test_run_gated`
  receives `_job_id` from `test_category_run` and updates `current_phase`,
  `current_phase_tool`, and `last_phase_result` so `test_category_status` can
  show live progress while long Spirent/DNAAS phases run.
- `test_run_gated` must run a recipe logic/order audit before execution. If a
  recipe schedules semantic assertions before their trigger/teach phase, or
  wires traffic before a required readiness gate, classify it as a TEST
  automation issue instead of a DNOS product failure.
- The phase compiler injects a `spirent_ensure_ready` gate before the first
  Spirent traffic mutation phase (`spirent_create_device`,
  `spirent_protocol_start`, stream creation, etc.) when no readiness/reservation
  phase already exists. This prevents "port not reserved" from being discovered
  after traffic starts.
- Verdict layers include `recipe_logic_order` and `test_automation`. Any
  blocking logic-order defect or phase failure caused by TEST harness readiness
  (for example Spirent "port not reserved") must produce top-level
  `AUTOMATION_BUG` so the harness is fixed before rerunning.
- Global assertion surfaces are not enough to fail every show phase. The
  VPLS-PW selected MAC/IP assertion (`v>` evidence) is only valid on MAC-IP
  evidence phases that explicitly verify a PW-source teach path after the
  source trigger has been compiled. Likewise, IPv6 PW-source NDP/MAC-IP
  assertions for `pw_global_ipv6` must not run during local-AC NDP phases such
  as `tp_step_03`; those phases assert only the local host
  `global_ipv6`/`src_mac` cache and EVPN install evidence.
- `test_run_gated` live syntax validation must validate the in-memory compiled
  recipe phases, not a freshly reloaded on-disk recipe, so topology-aware
  phases like RR-SA-2 PW-source wiring and mandatory IRB evidence checks cannot
  be dropped between compile and validation.
- `user-test-mcp` hot-reloads `mcp_common.command_profiles` on tool list/call.
  After ordinary TEST compiler/profile edits, run `py_compile` and call a
  harmless TEST tool to load the change; do not restart `user-test-mcp.service`
  unless `user_test_mcp/server.py` or `user_test_mcp/tools.py` itself changed.
  Restarting the service invalidates Cursor's long-lived native MCP SSE
  session and can cause "Failed to reinitialize MCP session" until Cursor
  reconnects.
- DNAAS local-loop-prevention (LLP) shutdown is an infrastructure blocker, not
  a DNOS feature verdict. If `dnos_dnaas_teach_plan`,
  `dnos_dnaas_spirent_preflight`, or diagnose evidence reports
  `Local Loop Detected Shutdown-AC` / `LOCAL_LOOP_SHUTDOWN`, TEST must stop at
  that phase, return `INFRASTRUCTURE_BLOCKED`, and include an
  `llp_repair` approval payload. The only suggested recovery is the
  dnos-config `dnos_dnaas_clear_llp` dry-run first, then `dry_run=false` with
  `confirm=true` only after user approval. `dnos_dnaas_clear_llp` must return
  after targeted verification confirms the affected member is fixed; full
  post-diagnose is opt-in (`include_post_diagnose=true`) so recovery does not
  hang on an unconditional delay. Never disable LLP globally or run broad
  bridge-domain clears from TEST automation.
- Historical DNAAS LLP/link-down events alone are not enough to block a TEST
  run. If a teach/preflight result has `overall_verdict=pass`, no
  `active_faults`, no down BD members, and `dnos_dnaas_clear_llp` has no target,
  classify it as stale history and continue. Block only on actionable active
  faults, down members, mac-learning-disabled BDs, failed hops, or explicit
  blocked/fail verdicts.
- TEST evidence phases for EVPN SI IRB must include `show evpn irb irb4001`
  and `show evpn irb-summary` alongside MAC, MAC-IP, ARP, forwarding, BGP, and
  vtysh parity evidence.
- Imported TP recipes can contain a stale or truncated top-level `steps` copy.
  The compiler must compare it with `tp_case.steps` and recover missing numbered
  rows from the Jira/TP `test_flow` table before compiling. Missing movers must
  be treated as a TEST automation defect, not as uncovered DNOS behavior.
- EVPN SI IRB Basic Functionality source roles are topology-specific:
  PE-1 local AC learn uses Spirent host protocol start on the PE-1 AC, PE-4 is
  the remote RT-2 MAC-IP source for mobility checks, and RR-SA-2 is the
  VPLS-PW peer/source only. `/TEST` must compile these as distinct source-role
  phases and never collapse remote RT-2 and PW-source traffic into one generic
  stream.
- For SW-228552 `EVPN_SI_VPLS_1`, live lab evidence binds the PW-source role to
  `RR-SA-2` (`bundle-100.2001`, fabric VLAN 215, inner 3001). If imported TP
  prose mentions PE-4 as a PW peer but PE-4 does not host `EVPN_SI_VPLS_1`, the
  recipe/compiler must use the RR-SA-2 shared-service AC or explicit recipe
  `metadata.pw_source` override instead of querying nonexistent PE-4 service
  state.
- SW-228552 remote RT-2 source phases must keep the PE-1 target service name
  separate from the off-DUT source role and must bind DNAAS to the source
  service under test, not just any VLAN-compatible PE-4 sub-interface. Current
  live PE-4 source role is `EVPN_PW_S001` on `ge100-18/0/0.3101` (fabric VLAN
  219, service inner 3101, Spirent wire tag 3101 with `--no-qinq`). The older
  `ge100-18/0/0.4002` interface is `Network-Service: VRF (default)` and must
  not be accepted for this EVPN source-role test even though it is up and shares
  transport VLAN 219.
- PW-source teach detection must handle both IPv4 ARP and IPv6 unsolicited-NA
  steps from RR-SA-2 shared-service ACs, preserving protocol-specific evidence
  (`show arp ...` for IPv4, `show ndp ...` for IPv6) instead of degrading them
  into generic local Spirent hosts.
- SW-228552 remote RT-2 mobility phases must prove the full source-to-target
  chain before PASS: PE-4 source AC/precheck, PE-4 RT-2 advertisement, PE-1
  RT-2 receiver evidence, PE-1 EVPN MAC-IP/forwarding-table installation, and
  the expected PE-1 ARP table result. These phases carry
  `rt2_evidence_contract` metadata and `test_verdict_layers` exposes an
  `rt2_source_receiver_install` layer so a generic successful show command is
  not enough to pass.
- IPv6 NDP Basic Functionality traffic steps must prefer an explicit
  `/SPIRENT` `protocol=icmpv6-na` stream. The stream encodes ICMPv6 Neighbor
  Advertisement type 136 with Target Link-Layer Address option using STC
  `FrameConfig` plus a custom IPv6/ICMPv6 payload. TEST must distinguish
  unsolicited NA (`S=0/O=1`, multicast, gratuitous/control) from solicited NA
  (`S=1/O=1/R=0`, unicast response to PE-1's NS, required for the PW-side
  MAC-IP/L2-neighbor repro). TEST also compiles a labeled
  `ipv6_host_protocol_fallback` host/protocol path for cases where raw NA
  encoding is unavailable or inconclusive. PASS proof summaries include packet
  and RT-2 evidence contracts, and verdict layers include `ipv6_packet_method`.
- MCP bridge exit status is not enough for TEST verdicts. `mcp_cli.py` can exit
  cleanly while the nested tool payload reports `Status FAIL`; `test_phase_run`
  must convert that to a failing phase. ARP/NDP proof assertions must match the
  exact expected IP/MAC for the source role, not just any `evpn` row or any
  command that returned `OK`.
- `test_run_gated` must produce `step_results` for every canonical TP step. A
  top-level PASS is allowed only when every TP step compiled at least one phase,
  every phase for that step executed, and every phase returned PASS. Missing
  wiring, missing phase execution, or a failed nested MCP payload marks the TP
  step FAIL and forces the `tp_substeps` / `phase_execution` verdict layers to
  FAIL. Never infer a test passed from a later successful verification phase.
- `/TEST` contract smoke must stay green before live repro work. The 2026-05-12
  contract fix restored: import-hinted recipes compile with stable default
  device/stream bindings, `test_run_gated execute=true` blocks traffic phases
  at `PHASE_REQUIRES_CONFIRM` unless `confirm=true`, and
  `test_verdict_layers` returns the documented 14-layer model.
- `/TEST proof` / evidence-display requests should use `test_proof_path`, not
  raw `test_report`, when the user asks why a test passed or failed. The proof
  path must show each TP step, each compiled phase/component, owning MCP tool,
  show/trace/config commands used, verdict, and artifact/evidence paths so a
  PASS can be audited component by component.
- `/TEST` may hand off to `/debug-dnos` only through the DUT-bug confidence gate.
  The gate requires complete phase wiring, clean logic-order audit, live
  syntax validation, clean live prerequisites, clean prior phases, clean Spirent
  readiness/traffic phases when traffic is involved, and exactly one failing
  read-only DNOS evidence phase with an `EXPECTED_ASSERTION_FAIL`. Infrastructure,
  MCP transport, syntax, unresolved binding, nested tool, or Spirent failures
  must not be labeled DUT bugs; fix TEST/SPIRENT first.
- IPv6/NDP Basic Functionality recipes must hard-gate on the DUT IRB IPv6
  configuration before any Spirent IPv6 traffic runs. `test_prerequisites_live_check`
  must verify the recipe IRB (for example `irb4001`) has a global IPv6 address
  in the expected host subnet/gateway from the recipe; if the IRB only has IPv4
  or reports `IPv6 global unicast address(es): N/A`, the top-level
  `test_run_gated` verdict is `PREREQUISITES_FAILED`, not PASS and not a DNOS
  product failure. This check runs before expensive syntax prewarm in the
  prerequisite path and returns an approval-gated `dnos_atomic_commit` dry-run
  payload for the missing IRB IPv6 config. Gated runs pass
  `skip_syntax_prewarm=true` into prerequisites because syntax validation already
  ran once, and failed prerequisites must not acquire a TEST session lock.
- SW-228552 IPv6/NDP imported recipes may rely on compile-time defaults rather
  than explicit recipe keys. The prerequisite gate must reuse the same binding
  resolver as phase compile for `irb_interface`, `ipv6_host`, `ipv6`, and
  `ipv6_prefix`; otherwise live prerequisites can falsely fail with "no IRB
  binding" even though the compiled phases correctly target `irb4001`.
- SW-228552 PE-4 mobility/Appudo checks must keep source roles separate:
  PE-1/RR-SA-2 use `EVPN_SI_VPLS_1` and `EVPN_SI_VPLS_2`, while PE-4 uses
  `EVPN_PW_S001`/`EVPN_PW_S002` toward RR-SA-2. A PE-4 check that queries
  `EVPN_SI_VPLS_1` or `EVPN_SI_VPLS_2` is a TEST binding bug, not evidence
  that PE-4 participates in the PE-1 service.
- Test-local infrastructure skips must be explicit recipe metadata, not global
  behavior. For example, when PE-4 is in upgrade mode, only the affected recipe
  may set `metadata.skip_prerequisite_checks` with check
  `remote_rt2_source_service`, a reason, and a matching reduced active device
  scope; the live prerequisite gate should report `SKIPPED` and must not query
  the excluded device.
- TEST phases that are about to hand traffic to DNAAS (`dnos_dnaas_teach_plan`
  for RR-SA-2 PW-source or PE-4 remote RT-2 source) must pass
  `freshness="fresh"` so a recently cleared LLP or admin/oper state does not
  reuse stale teach-plan/path cache and falsely block the run.
- TP prose may describe route summary in a human order (`show route vrf
  <vrf> summary`), but DNOS live syntax is `show route summary vrf <vrf>`.
  The TEST command binder normalizes this before syntax validation/execution so
  imported Basic Functionality recipes fail only on real behavior, not stale TP
  command ordering.
- TP/imported recipes may also contain the invalid hybrid form
  `show route summary instance <vrf>`; the binder must normalize it to
  authoritative DNOS syntax `show route summary vrf <vrf>` before syntax
  validation and phase execution.
- SW-228552 TP prose may mention `show evpn instance <service> mobility-history`,
  but current DNOS syntax does not expose that subtree. The TEST binder must
  normalize it to the live-validated evidence surface
  `show evpn instance <service> mac-table detail` so mobility evidence uses a
  real DNOS command.
- The IPv6 IRB prerequisite detector must not match metadata keys such as
  `requires_ipv6: false`; it gates only when recipe requirements explicitly set
  IPv6 true or when user-facing protocol/test text contains `IPv6`/`NDP`.
- Category execution belongs inside `user-test-mcp` via `test_category_run`.
  Do not drive category runs from chat with shell loops that parse markdown.
  `test_category_run` resolves the category with `test_category_find`, invokes
  `test_run_gated` directly for each recipe, stores compact structured
  per-test verdicts under `~/SCALER/TEST/_shared/jobs/`, and releases the
  per-device lock on automation exceptions.
- Executing category runs must default to background job semantics:
  `test_category_run` returns `verdict=RUNNING` plus `job_id` immediately, and
  callers poll by calling the same registered `test_category_run` tool with
  `operation=status` and `job_id`. Do not depend on brand-new MCP tool names
  appearing in Cursor without a reload. Never keep Cursor native MCP or
  `mcp_cli.py` SSE open for a full category run; that creates fetch/read-timeout
  orphans while the server keeps running traffic/config phases invisibly.
- TEST background status responses must be compact by default: return
  `job_id`, status/verdict, current test, compact per-test results, and the
  durable detail path only when `include_details=true`. Do not embed full
  compiled recipes or phase payloads in every polling response.
- When a category job reports a PASS test, `test_category_status` must include
  a proof summary in the active polling response without stopping the background
  job: TP steps passed/compiled, phase count, PASS/skipped verdict layers,
  tools exercised, run path, and a `test_proof_path` call for full evidence.
  For older job records, it may lazily reconstruct this compact proof from the
  saved `result.json` under the run directory.
- TEST category execution must keep total/test timeout and phase timeout
  separate. A caller-level `timeout_sec` is not allowed to become a
  30-minute timeout for each live dnos-config readiness phase; use
  `phase_timeout_sec` and cap DNAAS readiness checks such as
  `dnos_dnaas_teach_plan` / `dnos_dnaas_spirent_preflight` so a single stale
  live probe cannot wedge the whole category.
- Long-running TEST MCP CLI calls must use the sanctioned `mcp_cli.py`
  transport with an SSE read timeout long enough for category runs
  (`MCP_CLI_SSE_READ_TIMEOUT`, default 1800 seconds). A 5-minute MCP client
  read timeout is an automation transport failure, not a DNOS verdict.
- DNAAS DUT walk for `/SPIRENT` must use scoped arguments when the target is
  known: `port_or_subif`/`ac_interface` plus `fabric_vlan` or `outer_vlan`.
  This prunes DUT ACs before LLDP/BD walking and avoids full-device walks when
  the user asks for one interface/VLAN path.
- DNAAS DUT walk `fresh` mode should stay fast: resolve path shape from local
  SCALER config/LLDP cache, then live-verify only the selected path interfaces
  in parallel across DUT/DNAAS devices. Use `force_live_logic=true` only for
  explicit full config scrape debugging, not normal `/SPIRENT` preflight.
- `/debug-dnos` Proxy ARP investigations must compare at least these
  live-validated surfaces before producing a product verdict: `show arp vrf
  <vrf>`, `show evpn arp-table instance <service>`, EVPN `evpn-only` /
  `vpls-only` ARP views, `show evpn mac-ip-table`, fib-manager neighbor DB,
  fib-manager L2-maintained neighbor DB, and fib-manager EVPN local/remote MAC
  DB. Shell-only Linux/DP commands are not permanent recipe evidence until they
  are separately live-validated from a component shell.
- Component shell observability goes through `dnos-config` tool
  `dnos_component_shell_exec`, not ad-hoc SSH from chat. Default method is
  DNOS CLI `run start shell <ncp|ncc|ncf|ncm> <id> [container <name>]` with a
  read-only shell command allowlist and automatic component-id discovery from
  `show system`. `method=ssh_port_2222` is explicit/experimental and must be
  reported as validated or failed per device; do not assume port 2222 works or
  hard-code container names from memory.
- `/debug-dnos` may call `debug_component_shell_bundle` for Proxy ARP Linux/DP
  neighbor-state evidence after first-pass show bundles. Container-specific
  Neighbor Manager or datapath shell commands require company-doc or live
  validation before becoming default test evidence.

## DNOS DNFTP Upload From Component Shells -- 2026-05-10

- Prefer native `dnos-config` MCP tool `dnos_usirota_dnftp_upload` for
  `/usirota-dnftp-upload <device>` requests. It stages `/techsupport/usirota_*`
  from the NCP shell, uploads to `dn@dnftp:Yarel/`, validates with dnftp SSH,
  and returns the verified `dnftp_path`.
- When files are found inside `run start shell ncp/ncc/ncm/ncf`, do not assume
  that shell can reach `dnftp`. Stage files into a DNOS CLI-visible repository
  first, then upload from operational CLI with `request file upload`.
- For NCP datapath files, use `run start shell ncp <id>`. Bare
  `run start shell` opens the routing-engine shell and will not see datapath
  `/techsupport` files.
- For NCP datapath shell `/techsupport` artifacts, archive them into
  `/core/traces/datapath/`; DNOS exposes that location as
  `show file ncp <id> traces list` with filenames under `datapath/...`.
- If `request file upload ... datapath/u` autocomplete does not show the staged
  archive, verify with `show file ncp <id> traces list` and re-check the same
  component shell with `ls -l /core/traces/datapath/<file>`; the usual cause is
  staging on a different device/NCP or a failed archive command.
- For `dnftp`, the verified working destination is directory form:
  `dn@dnftp:Yarel/ out-of-band`. Avoid `dn@dnftp://Yarel/<file> protocol scp`
  for this workflow; it failed by appending the filename twice on `dnftp`.
- Do not persist `dnftp` passwords in skills, rules, scripts, or command
  examples. The operator enters the password interactively. After upload,
  validate the final artifact with `ssh dn@dnftp "ls -lh Yarel/<archive>"` and
  report the verified path as `dn@dnftp:Yarel/<archive>`.

## Git Commit Popup Device Context -- 2026-05-10

- The System Stack submenu's Git Commit popup must render the selected device
  identity directly in the header (`Git Commit - <device>`), preferring verified
  metadata such as `_registeredHostname` over generated canvas labels.
- Keep the commit hash display labeled and copyable, with refresh preserving
  the same device-aware header instead of falling back to a generic title.
- Git commit refresh should hit the lightweight `GET /api/devices/{id}/git-commit`
  endpoint with a bounded 10-second frontend timeout. The endpoint must check
  canonical/alias `operational.json` cache entries first (`device_id`, SSH host,
  and scaler ops index matches) before paying the live SSH/virsh cost.

## SSH Dialog Save Identity Guard -- 2026-05-10

- Save-time onboarding verification uses a scoped identity request token
  (`scope="save"`). Probe/discover requests may still run while the dialog is
  open, but their tokens must not invalidate a valid Save response for the same
  SN/host.
- After verified onboarding stamps a hostname mismatch (`_hostnameMismatch`),
  the dialog should close normally and then show the existing canvas mismatch
  popup near the device so the operator can rename the canvas label or device
  hostname immediately.

## Topology Switch Dirty Prompt -- 2026-05-10

- Opening a different topology from the Topologies menu must route through
  `FileOps._requestTopologySwitch(...)`. It compares a stable generated
  topology signature against the last load/save baseline and shows
  Save / Discard / Cancel only when real canvas or persisted device identity
  state changed.
- Backend onboarding identity and credential fields are persisted topology
  state: `device.sshConfig`, `_registeredDeviceId`, `_registeredHostname`,
  `_registeredMgmtIp`, `_monitoredKey`, and related saved identity fields must
  dirty the topology until saved. Runtime probes such as `_sshReachableAt`,
  onboarding progress, LLDP/stack/git caches, and UI timestamps must not dirty
  the topology by themselves.

## Topologies Dropdown Drag Targets -- 2026-05-10

- Topology row drag/drop must resolve target domains by `.domain-title`
  rectangles before considering expanded `.domain-body` rectangles. This keeps
  collapsed domains below a long open domain precise and prevents expanded
  topology rows from stealing the hover/move target.
- The Topologies dropdown itself owns viewport scrolling (`max-height` +
  `overflow-y:auto`). Individual expanded domain lists may still scroll their
  file rows, but multiple open domains must remain reachable through the parent
  panel.

## XRAY Canvas Capture Halo State -- 2026-05-10

- Packet capture/XRAY link halos are runtime UI state. The renderer must only
  draw them when `editor._xrayCapturing` names the link or the live
  `XrayPopup.isOpenForLink(editor, link)` owns it; never trust a saved
  `_xrayCaptureActive` flag by itself.
- Save/load/history/recovery paths must strip `_xrayCaptureActive` from link
  and unbound-link objects. Old autosaves may contain that field, so topology
  load/reset also clears it before drawing.
- The XRAY halo must follow the actual rendered link path (including curved
  links) and use screen-stable stroke/dash widths so it remains sharp across
  DPR, browser zoom, and app zoom.

## XRAY DNAAS-DP Capture Targeting -- 2026-05-11

- DP (DNAAS) capture must resolve DNAAS leaf and spine SSH targets on the
  backend before launching `live_capture.py`. The popup may send canvas labels
  such as `DNAAS-LEAF-B10` plus the source port from LLDP or from the selected
  canvas link; `serve.py` resolves those through the SCALER device inventory
  and pins `--dnaas-leaf-host`, `--dnaas-spine-host`, and
  `--dnaas-mirror-uplink` for the helper.
- The backend preflight owns the final mirror/spine decision and uses documented
  DNOS LLDP detail syntax: `show lldp neighbors <interface>`. Do not re-add the
  invalid `show lldp neighbors interface <interface>` form. Capture config and
  pcaps remain per-user, while the shared SCALER inventory is read-only target
  resolution input.
- DNAAS-DP cleanup is two-layered: `live_capture.py` removes the leaf
  port-mirroring session and any `/var/tmp/xray_dnaas_*.pcap` on the spine,
  and the topology server still applies the non-Yarel ephemeral server-side pcap
  retention policy after delivery/download.

## Backend-Validated Onboarding Name Checks -- 2026-05-07

- Cluster active-NCC onboarding must treat a typed IP as a transport target,
  not as proof that the SCALER ops-index owner for that IP is the same device.
  `/api/devices/verify-and-register` may mirror LLDP, stack, git, or context
  data only after the cached owner matches the verified hostname, serial, or
  registry identity. Same-IP cache owners that do not match are conflict
  diagnostics, never metadata sources.
- Generated canvas labels such as `NCP-1` / `S1` are weak identities. When
  onboarding from those labels, backend metadata must require a stronger serial
  or hostname match before `_stackData`, `_lldpData`, `_gitCommit`, or
  `_monitorContext` are stamped onto the canvas device. If validation returns
  `unknown` or `conflict`, the frontend must clear stale identity-bound cache
  and show a retryable metadata state.
- For cluster devices, registering through an active-NCC member IP must reuse
  the existing monitored registry row when that IP is already listed in
  `cluster_ncc_ips`; preserve the chassis `management_ip` and merge member IPs
  instead of creating a duplicate per-NCC row.
- Successful backend-first device onboarding must immediately compare the live
  device hostname returned by `/api/devices/verify-and-register` with the
  current canvas device label. Apply the existing per-device mismatch UX
  (`_hostnameMismatch`, badge/toolbar warning, and inventory-label precedence)
  before the SSH dialog closes so newly onboarded devices behave like monitored
  refreshes for every authenticated user.
- GI-mode onboarding/name refresh must suppress hostname mismatch when the live
  identity is a serial/NCP identifier (for example `AAF1944AAAJ`) rather than a
  DNOS hostname. Preserve the serial as identity context, but do not set
  `_hostnameMismatch` or offer rename/correct-hostname for canvas labels such as
  `YOR_CL_PE-4`.
- The SSH dialog must never use a serial/KVM console string as an `ssh_host`
  probe hint. Probe hints are IPv4-only; Save verification should reuse a
  reachable direct SSH host from the last probe when available, and GI Auto
  connect should prefer the web/virsh terminal path unless the operator
  explicitly selects iTerm.

## Upgrade Post-Deploy Repair Gates -- 2026-05-10

- After delete+deploy or GI deploy returns to DNOS mode, config repair must
  poll `show system | no-more` until the output contains real system/node
  fields before loading or restoring configuration. DNOS prompt detection alone
  is not enough; a partially initialized CLI can accept SSH while config load is
  still unsafe.
- DNOS readiness and config-restore SSH/auth readiness are separate gates. A
  successful `show system` probe only proves the CLI is usable on the current
  channel; file restore still opens a fresh SSH/SCP path, so authentication or
  transient SSH failures must be treated as retryable post-deploy repair
  pending, not as immediate upgrade failure.
- Post-deploy file restore must try existing credential sources in order:
  saved per-user/device credentials, canonical hostname credentials, then the
  bridge lab credential chain (`dut`, `dnaas`, `arista` profiles). Do not add
  ad-hoc password guesses. Log the credential source and username only, never
  the password.
- Manual `/api/operations/image-upgrade/restore-config` must reuse the same
  file-based post-deploy restore helper as automatic repair. It must bind the
  request user with `app_user_context`, preserve the resolved active-NCC
  `mgmt_ip` as `mgmt_ip_hint`, and let the shared helper pick credentials and
  backup files so old restore buttons cannot diverge from upgrade recovery.
- If config repair reports retryable SSH/auth/transport failure, leave
  `config_repair_completed_at` and `upgrade_completed_at` unset, set
  `config_repair_pending` / `config_repair_retryable`, and continue bounded
  retries inside the post-deploy verification budget. Only version/syntax
  incompatibility after an actual restore/rollback attempt should be terminal.
- `/api/operations/jobs` must tolerate legacy/recovery job rows that use `id`
  instead of `job_id` or contain non-JSON helper values. A browser refresh must
  not mark the bridge/probe service unavailable because one old job snapshot has
  an older schema.
- GI deploy/delete-deploy flows must prove the channel is still at GI CLI
  immediately before every GI target-stack/deploy command. A stale successful
  `_preflight_gi_health` result is not enough because KVM/virsh channels can
  drift back to NCC bash after prompt transitions; if `show system stack`
  returns Linux shell output or `Command 'request' not found`, re-enter `dncli`
  before retrying the same component.
- `show system stack` Target column is authoritative for image-load skip
  decisions. If the selected DNOS/GI/BaseOS URL already matches the component's
  Target value, skip that component and continue loading only missing or
  mismatched targets; never fail or reload just because another selected
  component is already present.
- Pre-deploy verification must also compare each selected image URL to the
  component's Target value. A non-empty Target for the wrong build is still a
  blocker; do not send `request system deploy` until every selected component
  either matched and was skipped or was loaded into the matching Target slot.
- PE-4 GUI/backend deploy plans use the lab-known CL contract:
  `system_type=CL-86`, `deploy_name=YOR_CL_PE-4`, `ncc_id=1`. Stale SA chassis
  readings from cached inventory must not propagate into the deploy command.
- Upgrade terminal log display uses explicit UTC+3 wall-clock timestamps via
  `_upgrade_terminal_timestamp()`. Keep stored job/phase ISO fields in UTC with
  their `Z` suffix for programmatic ordering; only human terminal lines should
  render UTC+3.
- GI deploy loads may call `_load_images_on_channel()` one component at a time.
  Operator messages must say "selected images for this load phase" when a
  single component is skipped, so DNOS already loaded does not imply GI/BaseOS
  are also loaded. The final pre-deploy verifier is the only global "all
  selected images verified" gate.
- If a virsh-backed CL upgrade sees a prompt like `dn@kvm108:~$`, the channel is
  at the outer KVM host shell, not the NCC VM shell. Do not run `dncli` there;
  reconnect the virsh console and re-probe GI CLI before sending any
  `request system target-stack ...` command.
- During long GI/BaseOS target-stack loads, a `show system target-stack load`
  status poll may find that the virsh-backed channel reset to the KVM host
  shell. Reconnect GI CLI and resume polling the existing load task with a
  bounded retry counter; do not blindly restart the same component load loop.
- GI health preflight must distinguish KVM host shell, NCC bash, and GI CLI.
  A generic `dn@kvm...` prompt is not "host shell" in the NCC sense and must
  trigger virsh reconnection, not direct `dncli`. `_probe_ncc_bash()` must reject
  KVM host prompts even though `printf` works there.
- gi-manager health has three states: healthy, needs recovery, and unverified.
  Only `healthy=True` may log "gi-manager healthy" and attempt `dncli`; an
  unverified Docker service list must block or reconnect instead of being
  treated as healthy.
- Progress panels that pre-populate upgrade history from `/api/operations/jobs`
  must open the SSE stream with a terminal offset and append only unseen
  `terminal_full` lines on completion. Otherwise a browser refresh can render
  the same per-device upgrade block twice.
- The Image Upgrade Wizard Upgrade Plan table keeps device controls, version
  cells, and long cached/verification notes visually separate. Do not place a
  long warning/error/status string directly into a narrow Current/Target cell;
  render a compact cell value with the full text as a row-level note or tooltip.
- The Image Upgrade Wizard Source step uses a per-user `Recent Activity`
  history, not branch-only localStorage. Browse branches, manually entered
  branch names, Jenkins build URLs, and Direct Images URL sets should all be
  saved as reusable typed entries, deduped newest-first, while Release/Dev/
  Feature browse categories remain unchanged.
- URL-tab Jenkins inputs are live wizard state. Input/paste/change handlers must
  preserve `_sourceUrl` across Source-step re-renders and write a pending URL
  Recent Activity draft before the operator clicks Update; successful URL
  resolution updates that same normalized URL entry with build/component
  metadata.

## TP Sanity Normal EVPN + IRB Baseline -- 2026-05-09

- SW-228552/SW-241473 TP Sanity coverage includes
  `TC-SANITY-EVPN-IRB-NORMAL-01` for a normal EVPN service with IRB and no
  VPLS/PW dependency. Keep this as a fast smoke test: service/IRB up, local AC
  MAC-IP/ARP learning, RT-2 MAC+IP advertisement, IRB forwarding, datapath
  agreement, and explicit absence of `vpls-only` / PW-sourced state.
- Do not collapse this Sanity TC into
  `TC-REG-NORMAL-EVPN-MACIP-MOBILITY-01`; that regression remains the deeper
  MAC/IP mobility flow. The Sanity task is only the baseline "normal EVPN + IRB
  works without VPLS/PW" check.

## TP /TEST CLI, Clear, and Lifecycle Taxonomy -- 2026-05-09

- SW-228552/SW-241473 no longer uses `Clear / Recovery` or
  `Service Lifecycle / CLI` as primary execution categories. Clear/recovery TCs
  belong under `CLI`; only `TC-CLI-01` (`IRB lifecycle CLI`) stays under `CLI`
  from the lifecycle family; the remaining lifecycle commit / rollback / cycle
  tests belong under `Load + Stress`.
- Future `/TEST create from TP` flows MUST set `vtysh_parity_required=true` for
  any CLI, lifecycle-cycle, commit/rollback, or rollback-loop recipe. The
  verifier must compare backend routing-shell / vtysh EVPN/IRB state against
  DNOS frontend CLI output before marking the test PASS.

## TEST MCP TP Import Scaling -- 2026-05-10

- `test_create_from_tp` must default to all local TP cases, not the first 20
  markdown matches. For SW-228552/SW-241473 this means one native MCP call must
  resolve and save all 124 TP cases without chunking.
- TP import reruns must dedupe by `(source_epic, source_tc)`. If a recipe for
  the same TP case already exists, `save` skips it and `overwrite=true` refreshes
  that existing recipe instead of creating another catalog directory.
- TP-derived traffic recipes must carry concrete topology bindings at recipe
  level (`vlan`, `inner_vlan`, `src_mac`, `src_ip`, `dst_ip`, `stream_name`,
  service/AC/IRB names). TEST phase compilation must pass those values through
  to `/SPIRENT`; otherwise traffic phases silently compile as `vlan=null` and
  show-command phases may execute literal placeholders such as `<name>`.
- For SW-228552 B11-style EVPN SI IRB tests, a bare L2 stream only proves MAC
  learning. Passing Basic Functionality requires an active IRB/router-interface,
  normal EVPN `export-l2vpn-evpn` route-targets, an emulated IPv4 host that
  triggers ARP/MAC-IP learning, and advertised RT-2 proof from both the EVI
  route table and neighbor `advertised-routes`.
- TEST phase compilation must treat ARP/MAC-IP/IRB "teach" traffic as a
  Spirent emulated-host workflow (`spirent_create_device` followed by
  `spirent_protocol_start`), not as a generic L2/L3 stream plan. Generic stream
  planning is still correct for pure frame-forwarding and scale/modifier tests.
- Recipe-level bindings are mandatory gates. Commands with unresolved
  placeholders such as `<name>` or `<service_name>` must fail as
  `NEEDS_PHASE_WIRING`/`UNVALIDATED` instead of executing literally.
- Live syntax validation must inspect DNOS output bodies, not just transport
  `ok=true`. Output containing `Unknown word`, `Incomplete command`,
  `does not exist`, `ERROR`, or unresolved placeholders is a failed validation.
- `/SPIRENT detach` is operator-facing shorthand for manual GUI handoff. It
  must release the reserved automation port and stop traffic while preserving
  `dn_spirent_main`; raw Lab Server detach alone is insufficient because it
  leaves the port reserved.
- `/TEST` category questions such as "what Basic Functionality tests can we run"
  must use `test_category_find` against the local catalog/TP index before any
  broad epic similarity search. Filter by `category`/`tp_case.category`,
  `source_tc`, Jira Test Category/Task keys, and device first; only use Jira
  lookup as a suggested fallback when local metadata has no match.
- When TP artifacts omit recipe-level execution hints, the TEST MCP importer
  must derive verification commands from TP step commands and normalize safety
  hints: multi-op implies atomic commit, atomic commit implies rollback proof,
  and CLI/lifecycle/rollback/atomic cases require `vtysh_parity_required=true`.
- `test_create_from_tp` result payloads must stay compact by default. Return
  `manifest_summary` and per-TC selector reasons, not the full TP manifest or
  every selector match reason inside every saved recipe. Full artifacts require
  an explicit `include_artifacts=true`.
- Saved TP-derived recipes must carry concrete prerequisite classes from import
  hints: `ssh_reachable` per known DUT, `bgp_l2vpn_evpn_session` for EVPN/SI
  tests, and `topology_binding` when DNAAS or Spirent is required. The
  `before_snapshot` and `verify` phases should be populated from extracted
  read-only DNOS commands, not left as empty `show_commands`.
- Phase compilation must classify `show bgp ...` as dnos-config read-only
  verification before generic BGP tooling. HA routing must match `HA` as a word
  (or explicit failover/switchover), not substrings such as `attach`.
- `test_topology_brief` must return compact summaries by default. Full DNAAS
  DUT walks are available only through `include_details=true`; otherwise large
  walks such as RR-SA-2's 200+ AC list overwhelm MCP output and hide the actual
  blocker.

## TP IP Mobility AFI Parity -- 2026-05-10

- SW-228552/SW-241473 `IP Mobility - IPv4` and `IP Mobility - IPv6` must stay
  AFI-parallel before Jira push. IPv6 cannot be represented by one broad NDP
  sweep when IPv4 has standalone sequence-arbitration, sticky-priority,
  lifecycle move, VRF move, and normal-EVPN mobility tests.
- The Jira IP Mobility category is `SW-265292`, with child Testing Tasks
  `SW-265293` for IPv4 and `SW-265294` for IPv6. Current TP parity is 12 IPv4
  TCs and 12 IPv6 TCs; future additions to one AFI should either add the
  counterpart AFI TC or document why the behavior is AFI-independent.

## TP Stress Jira Split -- 2026-05-10

- SW-228552/SW-241473 stress coverage is pushed under Jira Test Category
  `SW-265295` (`EVPN-VPLS SI IRB | Stress`), not `Load + Stress`, per user
  naming. Child Testing Tasks are `SW-265296` (lifecycle and atomic commit),
  `SW-265297` (scale and config churn), and `SW-265298` (traffic, soak, and
  memory).
- Keep lifecycle commit/rollback tests in the stress category unless the user
  explicitly reclassifies them again. They are stress tests because they prove
  all-or-nothing commits, rollback loops, vtysh parity, and FibMgr/zebra/wb
  stability under repeated lifecycle churn.

## TP Scale 3,500-Service IRB+AC+PW Coverage -- 2026-05-10

- SW-228552/SW-241473 Scale coverage now includes explicit 3,500-service
  tests: `TC-SCALE-3500-SVC-IRB-PW-LEARNING-01` and
  `TC-SCALE-3500-SVC-BASIC-MOVE-01`. Each service must have one IRB, one AC,
  and one VPLS PW between two DUTs.
- The 3,500-service scale matrix must prove PW-side MAC/IP learning through
  the IRB-enabled service, aggregate and sampled control-plane/DP count
  correctness, and a basic PW->AC then AC->PW ownership move across the same
  matrix. Keep `scale_axis.service_count=3500`, `irb_count=3500`,
  `ac_count=3500`, and `pw_count=3500` in `/TEST` import hints.
- Scale coverage also includes
  `TC-SCALE-3500-SVC-MULTI-PW-FANOUT-ARP-01` for mixed multi-PW fanout:
  every service has at least 2 valid PWs, selected services have tens to
  hundreds of valid PWs, and ARP from every generated PW source must be
  learned into IRB MAC-IP state with PW/`v` semantics, no proxy reply toward
  PW, no local RT-2 advertisement, and stable PW-to-PW source updates.
- The Jira Scale category is `SW-265301` (`EVPN-VPLS SI IRB | Scale`). Child
  Testing Tasks are `SW-265303` (IRB lifecycle and bulk move), `SW-265302`
  (PW learning and mobility, including 3,500-service and multi-PW fanout
  cases), and `SW-265304` (matrix, cleanup, and EVI delete).

## TP HA Sticky/Static/PW-Learned IRB Coverage -- 2026-05-10

- SW-228552/SW-241473 HA coverage includes 11 TCs. In addition to bgpd,
  wb_agent, routing-engine, fibmgrd, NCC switchover, backup NCC, NCP, and NCF
  events, it now explicitly covers sticky MAC / sticky-interface ownership,
  static IPv4 ARP, static IPv6 NDP, PW-learned MAC-IP/NDP, and IRB state
  preservation.
- HA topology prerequisites must use the three-DUT profile: `PE-1` as local
  AC/IRB owner, `PE-4` as VPLS-PW peer or SI observer, `RR-SA-2` as RT-2/RR
  role, plus Spirent/DNAAS for traffic, teach, and packet proof. PASS requires
  four-layer evidence: control-plane, datapath, traffic, and packet.
- The Jira HA category is `SW-265305` (`EVPN-VPLS SI IRB | HA`). Child Testing
  Tasks are `SW-265306` (routing and process restart), `SW-265307` (cluster
  and datapath failover), and `SW-265308` (sticky, static, and PW-learned
  state).

## TP Remaining Jira Categories -- 2026-05-10

- SW-228552/SW-241473 remaining tail categories are now pushed to Jira:
  `SW-265312` (`EVPN-VPLS SI IRB | Negative Testing`), `SW-265310`
  (`EVPN-VPLS SI IRB | NETCONF / gNMI / RestCONF`), and `SW-265311`
  (`EVPN-VPLS SI IRB | Upgrade / Downgrade`).
- Negative Testing has child Testing Tasks: `SW-265315` for PW-source / DGW /
  Anycast / sticky prohibitions, `SW-265313` for IRB and VRF policy guards,
  and `SW-265314` for service isolation and invalid topology guards.
- The remaining-category TP stamp script is
  `~/SCALER/TEST/tp/SW-228552/_apply_remaining_jira_keys.py`. It maps the
  10 Negative TCs to their child Testing Tasks, and maps `TC-MGMT-01` and
  `TC-UPGRADE-01` directly to their single-TC Test Categories.

## DNOS cmd_search + cmd_help Paired Evidence -- 2026-05-08

- Whenever a TP, recipe, slash command, or agent step introduces a DNOS
  configure / show / clear command whose syntax is not already in cache, the
  evidence MUST be a paired `cmd search` + `cmd help` capture, not just one
  of them. `cmd search <keyword>` proves the templates exist on the device;
  `cmd help <concrete_command>` proves the parameter semantics are
  understood. Recording only `cmd search` is incomplete.
- DNOS rejects placeholders in `cmd help`. `/TEST` and any orchestrator MUST
  resolve `<interface>`, `<service>`, `<mac>`, etc. to concrete values from
  the live device before issuing `cmd help`. TP metadata may keep the
  placeholder template, but it MUST also record a `runtime_substitution`
  hint so the orchestrator knows what to fill in at runtime.
- TP manifests carry the rule via the
  `tp:dnos-cmd-search-help-paired-evidence` rule_anchor. Every TC that
  introduces new DNOS syntax MUST list this anchor in
  `covers_rubric_rules` and carry a `command_evidence` block with both
  `cmd_search` and `cmd_help` sub-fields.
- The MCP surfaces this pair via `dnos_cmd_search` (template discovery,
  ~0.1s) and live `dnos_run_show_commands` calling `cmd help <concrete>`
  on the chosen device. There is no aggregate `dnos_cmd_search_and_help`
  tool yet; the open enhancement is to add one that returns
  `{search_templates, help_for_each_template, raw_device_output}` in a
  single round-trip and surfaces the BYTE-FOR-BYTE device CLI output
  (not just Markdown) so agents and humans both see the canonical form.

## DNOS MCP Output Format -- Human-Readable First -- 2026-05-08

- All `dnos_run_show_commands` results are already byte-for-byte 1:1 with
  the device CLI and wrapped in fenced code blocks; this is the canonical
  form for show-command output and MUST stay that way.
- `dnos_cmd_search` currently returns Markdown summaries of templates plus
  optional JSON. The pending enhancement is to add a `format="device_raw"`
  mode that issues the actual `cmd search <kw>` on the device over SSH and
  returns the raw CLI output (the same text a user would see in a DNOS
  prompt). The Markdown summary stays available for token-efficient agent
  use; `device_raw` is for users and for `/TEST` runtime live-validation.
- Until `format="device_raw"` ships, agents MUST NOT pretend that the
  Markdown summary IS the device output. Recipes that need device-format
  evidence MUST run `dnos_run_show_commands` with the explicit
  `cmd search <kw>` and `cmd help <concrete>` strings to capture the raw
  output; the Markdown summary is only a search result, not a live-device
  proof.
- New MCP tools that wrap DNOS CLI surfaces MUST expose `format="text"`
  returning the device CLI output verbatim (line-for-line, including
  prompts and continuation markers) inside a fenced code block. JSON is
  for agents that programmatically parse fields; humans get the raw
  device CLI form.

## EVPN-SI IRB TP Prerequisites -- 2026-05-08

- Advanced EVPN-SI IRB TP prerequisites must list both control planes when
  PW/SI source behavior is tested: `l2vpn-evpn` SAFI 70 for RT-2/RT-5 evidence
  and EVPN-VPLS / `l2vpn-vpls` SAFI 65 plus installed VPLS PW state for PW-side
  source behavior. EVPN RT evidence alone is not sufficient proof for tests
  that depend on VPLS/PW forwarding.
- Single-homed ACs in SW-228552/SW-241473 TP coverage use explicit configured
  SH ESI values. Do not describe SH AC ownership as `ESI=0`; reserve `ESI=0`
  only for route fields where DNOS/EVPN semantics explicitly require it.
- SW-228552/SW-241473 TP artifacts use a dedicated `Proxy ARP/NDP` category
  for actual proxy behavior: proxy reply/no-reply, PW reply suppression,
  subnet-scoped ARP/NDP filtering, link-local Proxy-NDP, and PW-LIF source
  context that gates proxy behavior. Do not move generic ARP/NDP table
  evidence tests into that category when ARP/NDP is only a verification layer
  for another feature.
- The old standalone `Observability / Logs / Traces` TP category is folded
  into `CLI` for SW-228552/SW-241473. Source-specific show/trace evidence is
  CLI verification unless it is actual Proxy ARP/NDP behavior/debug proof,
  which belongs in `Proxy ARP/NDP`.
- Keep the SW-228552/SW-241473 `Advanced Functionality - IPv6 Scenarios`
  category when IPv6 parity exists for non-proxy Advanced IPv4 behavior. IPv6
  Anycast IRB, host-route `/128` FIB, RT-5 withdraw/origination over MPLS or
  VXLAN, and PW-label + ND-over-VPLS tests belong there, while Proxy-NDP
  reply/no-reply behavior remains in `Proxy ARP/NDP`.

## Command MCP Gap Closure -- 2026-05-08

- Command MCP capability belongs in `/home/dn/mcp_common/command_profiles.py`
  with matching descriptors under Cursor's MCP cache. Slash command files stay
  thin routers and must not re-grow old prompt logic.
- Every new command MCP tool must expose `format`, use structured verdicts, and
  return `summary_markdown` for `text` / `both`. Mutating, traffic, recovery,
  or cleanup tools default to dry-run and require `execute=true`; destructive
  tools also require `confirm=true`.
- Cross-command workflows must pass compact typed handoffs with
  `schema_version`, `source_command`, `device`, `interfaces`, `vlans`,
  `streams`, `sessions`, `artifacts`, `next_actions`, and `safety_notes`
  instead of reloading large slash prompts or reconstructing state in chat.
- `/SPIRENT` supports readiness (`connect`, `reserve`, `ensure_ready`), scoped
  traffic control, session repair, route/protocol lifecycle wrappers, and
  RangeModifier scale streams. Prefer `spirent_scale_stream_plan` before
  creating many per-host StreamBlocks.
- `/TEST` should use MCP-native phase planning/execution and live prerequisite
  gates first. Recipes without `orchestrator.py` can still run MCP-executable
  phases through `test_phase_run`, collect artifacts through
  `test_result_collect`, and package Jira evidence through `test_jira_package`.
- `/TEST` TP imports must be compiled through `test_phase_compile` before they
  are called runnable. Imported TP steps, verification commands, and
  `test_import_hints` should become concrete `mcp_call` phase metadata or fail
  clearly as `NEEDS_PHASE_WIRING`.
- `/TEST` execution should default to `test_run_gated`: acquire the per-device
  lock, compile phases, validate DNOS syntax with explicit
  `LIVE_VALIDATED` / `DRY_RUN_VALIDATED` / `UNVALIDATED` states, run live
  prerequisites, then execute only approved safe phases. Traffic/config phases
  require `execute=true` and phase confirmation.
- `/TEST` TP steps that express `config ; ... ; commit check ; commit` must
  compile into `dnos_atomic_commit` phases, not stay as manual review, once
  placeholders are bound. SW-228552 Basic Functionality recipes require
  concrete PE-1 bindings (`EVPN_SI_VPLS_1`, `irb4001`,
  `ge400-0/0/5.4001`, VLAN 214 / inner 4001) before gated execution.
  Placeholder aliases such as `<vrf-name>` and `<irb_interface>` must resolve
  from the same canonical recipe fields as `vrf` and `irb`; IPv6 recipes must
  also expose `<ipv6_address>`, `<global_ipv6>`, and `<pw_global_ipv6>` from
  their concrete traffic binding.
- `/TEST` TP `cmd search <keyword>` steps should route to `dnos_cmd_search`.
  Do not pass `cmd search` / `cmd help` strings through `dnos_run_show_commands`;
  if there is no dedicated `cmd help` MCP tool, keep only the validated
  `cmd search` proof in runnable recipes.
- `/TEST` evidence should flow through `test_evidence_collect`,
  `test_verdict_layers`, `test_jira_package`, and `test_jira_publish_plan` so
  debug/Jira handoffs include layered verdicts, artifacts, and approval-gated
  external posting plans instead of loose chat notes.
- `/XRAY`, `/HA`, `/BGP`, and `/debug-dnos` now provide explicit plan/evidence
  tools (`xray_capture_plan`, `ha_scenario_plan`, `exabgp_preflight`,
  `debug_evidence_plan`) so agents should route to those tools rather than
  inventing ad-hoc command sequences.
- After MCP profile changes, regenerate descriptors and run
  `/home/dn/mcp_common/tests/test_contract.py` before declaring the work done.
- Hostname mismatch state is transient canvas-object state. Do not persist or
  cache mismatch state globally; stale onboarding/probe responses after SN/host
  edits must be ignored instead of warning on the wrong device.

## Shape Resize Handles -- 2026-05-07

- Shape resize handles must be generated from the visible shape border/path,
  not from a generic bounding-box circle/square unless the shape itself is a
  rectangle. Keep handle IDs (`n`, `s`, `e`, `w`, `nw`, `ne`, `sw`, `se`)
  stable so existing resize semantics, undo/redo, save/load, zoom/pan, and
  rotation continue to work.
- `topology-shape-methods.js` owns shape-specific handle geometry. Drawing and
  hit-testing must consume that shared geometry so visual handles and click
  targets stay aligned for rectangles, circles, ellipses, polygons, cloud, line,
  arrow, checkmark, and cross shapes.

## Object Toolbar Sub-Section Lifecycle -- 2026-05-07

- Object toolbar sub-sections are mutually exclusive at the top level. Opening
  Style, Color, Label Style, Layer, Width, Curve, LLDP, or Stack must close
  sibling popups through the shared toolbar-popup cleanup path.
- Inner option clicks inside the active sub-section must apply the mutation and
  keep that sub-section open so users can try multiple styles/colors without
  reopening the toolbar. Close only on outside click, Escape/global cleanup, or
  clicking the same top-level button again.
- The link toolbar Style menu must stay in parity with the global link style
  variants (`solid`, dashed/dotted variants, and arrow variants) and expose arrow
  direction flipping without detaching endpoints or losing link metadata.

## Serial Onboarding Validity -- 2026-05-07

- Device onboarding is backend-first. `/api/devices/verify-and-register` must
  return an explicit backend-validated metadata envelope for identity-bound
  LLDP, System Stack, Git, and mode data. The frontend may mirror those fields
  only when the envelope is reliable for the current serial/hostname/IP; if the
  backend returns unknown, not reliable, or conflict, the frontend must keep
  metadata unknown/disabled and must not hydrate from generated canvas labels or
  stale cached context lookups.
- Editing a canvas device SN/SSH identity is an identity boundary. Clear
  identity-bound metadata (registered device id/hostname/mgmt IP/serial,
  onboarding/monitor context, LLDP, stack, git commit, reachability, mode) unless
  the new SN/host has just been verified by the onboarding response.
- Probe, console discovery, onboarding, monitor, LLDP, stack, and git responses
  must be applied only if they still match the current device identity. If the
  user changes SN/host while a request is in flight, ignore the stale response
  and show a warning/status rather than attaching data from another device.
- Response identity fields are evidence. If returned serial, hostname,
  `device_id`, or management IP conflicts with the current SN/host, do not
  hydrate toolbar metadata or cache it on the canvas object. Leave the UI in an
  unknown/not-discovered state until a fresh, matching refresh succeeds.
- LLDP, System Stack, and Git toolbar actions are identity-bound metadata
  surfaces. Keep their buttons disabled/loading until current-device validated
  data is stamped for the active serial/hostname/management IP/request
  signature. Never render LLDP/git/stack data from generated canvas labels,
  malformed placeholder rows, or a prior device response.
- The System Stack dialog must treat disk cache as identity-bound, not
  IP-bound. Initial open and normal Refresh must pass the current identity guard
  to `/api/devices/{id}/context` and `/api/devices/{id}/stack-fast`; if the
  backend reports `cache_owner_conflicts`, or the selected device is still only
  a generated label (`NCP-*` / `S*`) with no matching serial/hostname evidence,
  show loading/unknown instead of rendering cached stack rows. Live stack-fast
  data may be written under the current safe identity, but stale same-IP SCALER
  cache from another owner is never a valid table source.
- Deep-refresh SSH probe is not an onboarding substitute. The SSH dialog must
  re-resolve the backend device identity at call time and must not auto-probe
  `/api/ssh/probe` with a generated canvas label such as `NCP-2` before
  backend registration has stamped a real identity. If probe returns 501/502/503
  or the bridge is still starting, mark LLDP/stack/git readiness as unknown and
  show a bounded "probe service unavailable" state; do not hydrate metadata or
  persist credentials against the stale generated label.

## New Canvas Device LLDP Defaults -- 2026-05-07

- Newly placed regular canvas devices must start with a placeholder LLDP model:
  empty `neighbors` / `lldp_neighbors`, `source: "canvas-placeholder"`, and a
  readable message. The LLDP table must render that as an empty table state and
  must not query backend LLDP APIs until the device has SSH, serial, registered,
  or discovered identity.
- Discovered, imported, onboarded, and DNAAS devices keep their real LLDP data.
  Placeholder defaults are only for fresh canvas devices and must not overwrite
  `ScalerAPI.getDeviceContext(...)`, discovery API, monitor, or onboarding LLDP
  results.
- Newly placed devices must also start with explicit unknown metadata for
  system stack, git commit, and device mode. Do not invent stack rows, git
  hashes, LLDP neighbors, or a DNOS badge from the canvas type/label/defaults.
  Render actual probe/discovery/monitor/onboarding data, or show an explicit
  "Not discovered yet" / "Run probe/discover" state. Canvas-generated labels
  such as `NCP-1` / `S1` are display labels only and must not be used as
  backend LLDP/stack/git lookup identities until a real device identity,
  management IP, serial, hostname, or registered device reference exists.

## Existing Device Metadata Reveal Gate -- 2026-05-08

- The LLDP, System Stack, Git, and device metadata toolbar prompt to
  "Run probe/discover" is only for completely new canvas devices that have no
  registered, monitored, discovery, or backend context identity. Existing DB
  devices such as `YOR_CL_PE-4` / PE-4 must be treated as known identities:
  show cached metadata when current-identity stamps are present, otherwise show
  a loading/unknown backend-context state without the probe-to-reveal affordance.
- Keep the Serial Onboarding Validity guard intact: known identity may come from
  `_registeredDeviceId`, `_registeredHostname`, `_registeredMgmtIp`,
  `_registeredSerialNumber`, `_monitoredKey`, monitor context, or a successful
  `ScalerAPI.getDeviceContext(...)` response. Do not treat generated canvas
  labels like `NCP-1` / `S1` as DB identity, and do not hydrate LLDP/stack/git
  from stale responses or placeholder rows.
- Known DB/registered/discovered/monitor-backed devices must still expose LLDP
  and System Stack table actions even before the current table data is hydrated.
  Opening the action should fetch/load or render the existing unknown/loading
  state; only brand-new generated canvas identities should be blocked with the
  probe/discover prompt.
- The System Stack table DNOS row owns a small copy control for the active
  DNOS version. Copy only the version string, use the shared clipboard helper,
  and show the existing toast-style success/failure feedback without copying the
  whole row or table.
- Selected-device monitoring must resolve through
  `TopologyDeviceIdentity.resolveIdentity(...)` before any monitor/context,
  LLDP, System Stack, Active NCC, or Git request. The resolver keeps backend
  device identity separate from SSH transport host, rejects generated canvas
  labels as lookup IDs, and filters stale/conflicting registered names so a
  selected `YOR_CL_PE-4` cannot silently poll PE-1.
- Async metadata responses must be applied only after request-signature and
  returned-identity checks pass. Stale or wrong-device stack/git/LLDP/context
  responses should be ignored with an expected-vs-returned identity status,
  not rendered onto the selected canvas object.
- Active NCC rendering is conservative across backend shapes:
  `active_ncc_node`, `active_ncc_host`, `active_ncc_vm`, and
  `active_ncc_ip` are equivalent evidence fields for the selected cluster.
  Git commit rendering must accept equivalent commit fields
  (`git_commit`, `gitCommit`, `git_hash`, `commit_hash`, etc.) while keeping a
  true unknown state when no commit is returned.
- System Stack copy controls are per image/version row. DNOS, GI, BASEOS, and
  future image rows each copy only that row's current version string.

## GI-Mode LLDP Snapshot Label -- 2026-05-10

- When a selected device is in GI, RECOVERY, or BASEOS_SHELL mode, the LLDP
  neighbors modal may still render the cached table from the last DNOS run.
  Keep that table and its DNAAS/Mirror/Loop counts visible, but show a subdued
  body warning that the device is in pre-DNOS mode and the LLDP neighbors are
  from the previous DNOS snapshot.
- The LLDP modal must derive pre-DNOS mode from all frontend mode evidence
  fields (`_deviceMode`, `_modeRawState`, monitor context, identity state, and
  SSH state), not only the canvas monitor cache. DNOS/current telemetry must not
  show the snapshot warning.

## Toolbar QuickAccess Shortcuts -- 2026-05-07

- Pointer clicks on the left tool rail open the existing per-tool side panel in
  its normal rail-adjacent location. Do not route click handlers through
  QuickAccess positioning.
- Bare tool shortcuts (`1` through `6`, plus `0` for Settings) call
  `ToolbarManager.activateTool(..., { quickAccess: true })`. The same
  `.tool-side-panel` content is reused, but it is temporarily positioned near
  the most recent canvas pointer location and clamped inside the canvas and
  viewport. If no canvas pointer is known, fall back to canvas center.
- QuickAccess panel opens are UI lifecycle boundaries: hide selected-object
  toolbars before showing the floating panel, and close the panel on Escape or
  outside pointer down through the existing `closeToolPanel()` cleanup path.

## Browser Refresh Shortcut Boundary -- 2026-05-10

- Topology keyboard handlers must never intercept browser-native refresh
  shortcuts: `Ctrl+R`, `Cmd+R`, `Ctrl+Shift+R`, `Cmd+Shift+R`, and `F5` pass
  through without `preventDefault()`.
- The app-owned refresh shortcut is only plain unmodified `R` / physical
  `KeyR`, and only when focus is outside editable text inputs, textareas,
  selects, or contenteditable regions. Repeated keydown events are ignored so
  one key hold cannot issue duplicate reloads.
- Modal/dialog guards still block editor shortcuts while interactive dialogs
  are open; typing `R` in dialog text fields must enter text, not refresh.

## Canvas Device Default Credentials -- 2026-05-07

- Newly placed regular canvas devices must initialize `sshConfig.user` and
  `sshConfig.password` to `dnroot` / `dnroot` at creation time so SSH dialogs
  and toolbar actions do not start from an empty password.
- DNAAS-imported/discovered devices keep their dedicated credential flow and
  must not be overwritten by the regular canvas default.

## Canvas Delete And Toolbar Lifecycle -- 2026-05-07

- Intentional canvas deletes must mark the pending object-count drop before
  mutation and explicitly schedule a post-delete autosave. The autosave
  mass-loss guard should still block accidental wipes, but it must allow a
  time-scoped delete initiated through `deleteSelected()` so refresh reloads
  the same canvas the user just drew.
- Delete handlers must snapshot undo history before mutation and remove single
  objects by stable `id`, not by an array index captured before connected-link
  filtering. This preserves undo/redo and avoids deleting the wrong neighbor
  object when a device deletion also removes attached links.
- Opening canvas-side panels or the Topologies dropdown is a UI lifecycle
  boundary. Call `hideAllSelectionToolbars()` through the existing editor
  helper before showing those panels, and also hide toolbars at the start of a
  topology switch/load.
- A selected object and its floating toolbar are separate UI state. If an object
  remains selected but its toolbar was hidden by a panel/topology transition,
  clicking the same object again should re-run the normal toolbar show path
  after the drag threshold guard, without changing the selection or breaking
  re-grab/drag behavior.

## Topology Switch Isolation -- 2026-05-06

- Loading a topology is a session boundary. `TopologyEditor.beginTopologySwitch(...)`
  assigns a generation token, cancels pending autosave/link-table/debounce work,
  clears transient canvas state, and lets stale async loads/saves self-ignore.
- `loadTopologyFromData(...)` must reset history with
  `resetHistoryForTopologyLoad(...)`; do not call `saveState()` during a load.
  Undo after a switch must start from exactly one baseline for the newly loaded
  topology, so Cmd/Ctrl+Z cannot resurrect objects from the previous canvas.
- FileOps load paths should call `_beginTopologyLoad(...)` before async fetches,
  check `_isTopologyLoadCurrent(...)` after every await, and use
  `_loadIntoEditor(...)` so the indicator identity is written before the canvas
  and autosave baseline are replaced.
- LLDP table rendering, refresh failures, modal close, and topology switches
  must abort stale LLDP requests and stop device scan animation flags. A visible
  LLDP table with returned or cached data is not a scanning state.
- LLDP neighbor rows expose a compact Connect action only after the neighbor
  resolves through `ScalerAPI.getDeviceContext(...)` to a known backend target.
  The click uses the existing native SSH/iTerm path via `editor._openSshUrl(...)`
  with the canonical `ObjectDetection` pending-device context and never launches
  the web terminal from the LLDP action. Password staging, when available, must
  continue to use the existing safe clipboard pattern rather than LLDP-specific
  credential handling.

## Slash Commands To Local MCP Migration -- 2026-05-06

- `/SPIRENT`, `/HA`, `/debug-dnos`, `/BGP`, `/XRAY`, and `/TEST` are thin
  routers to dedicated local MCP servers: `user-spirent-mcp`, `user-ha-mcp`,
  `user-debug-dnos-mcp`, `user-exabgp-mcp`, `user-xray-mcp`, and
  `user-test-mcp`.
- `/TEST` now uses `user-test-mcp` on port 9306 for catalog, create, run,
  verify, report, learn, prerequisite gates, topology brief, TP import,
  session locks, syntax prewarm, recipe skeletons, and deterministic similar
  test lookup. The original 49 KB slash prompt is preserved as
  `.cursor/commands/TEST.md.bak_mcp_migration`; the active router is about
  2.5 KB.
- TP imports can be persisted with `test_create_from_tp(save=true)` /
  `/TEST create from TP <EPIC> --save`, which writes runnable catalog recipes
  under `~/SCALER/TEST/catalog/<test-id>/recipe.json` for subsequent
  `/TEST run <test-id>` calls.
- TP-to-TEST imports must preserve detailed TP case fields (`steps`,
  `pass_criteria`, `verification_commands`, and `test_import_hints`) in the
  generated recipe. For EVPN VPLS IRB, legacy clear ARP/NDP user-story
  coverage is a negative test: removed clear ARP/NDP forms must be rejected or
  absent and must not mutate EVPN MAC-IP / ARP / NDP state; valid mutation goes
  through scoped `clear evpn mac-ip-table` forms only.
- EVPN VPLS IRB `SW-226293` clear MAC-IP coverage requires standalone
  permutations: global `clear evpn mac-ip-table` clears all EVIs including
  VPLS-PW MAC-IP entries; VRF-filtered clear affects only IRB services in the
  selected VRF and preserves other services; local/EVPN-only scoped clear must
  not clear VPLS-PW entries and VPLS/PW scoped clear must not clear local
  entries.
- VPLS IRB TP category sections must use the FlowSpec-VPN advanced-functionality
  presentation style: category-local `Topology Prerequisite Steps`, then a
  compact `Test Task Matrix` with `# / Test Task / Test ID / Purpose / Primary
  Verification / Pass Criteria`, then detailed per-TC Jira-wiki step tables.
  Do not bury topology prerequisites only in a global section. Topology
  prerequisites must be detailed but generic: use `PE-X`, `PE-Y`, `RR-X`,
  `AC-IF-*`, `IRB-IF-*`, `PW-IF-*`, and service roles such as
  `SVC-EVPN-LOCAL`, `SVC-EVPN-SI`, and `SVC-REMOTE` instead of hard-coded
  lab device names. Explain the minimum devices, service relationships,
  interface roles, protocol gates, and intentional variables so a future tester
  can map the plan to a different lab. Render topology prerequisites as
  numbered text steps, not tables; only per-test task procedures use table
  format. When showing TP categories in chat,
  mirror this official structure and keep detailed steps, verifier commands,
  and pass criteria visible unless the user explicitly asks for a summary. A
  requested category detail view must render each test task as its own titled
  block (`TC-ID - name`) with a `Step / Action / Command / Expected Result`
  table followed by `Pass Criteria` bullets, matching the review-table style
  used in the official TP output. TP
  command cells are DNOS CLI procedures, not shell commands: use `;` for
  sequential DNOS commands, never shell `&&`, expand `sh` to `show`, and
  validate show/config command surfaces with `dnos_cmd_search` or CLI docs
  before rendering. For mobility or MAC/IP origin tests, traffic generation
  must be described as a learning sequence: where the MAC/IP is learned first,
  where the same MAC/IP moves next, and the expected post-move behavior
  (RT-2 advertised/withdrawn, PW-sourced `v>` retained, remote path wins, or
  proxy-ARP reply suppressed). Do not use generic "generate scenario traffic"
  wording as a standalone step. For Basic IPv4 IRB-in-service coverage, include
  normal VRF ARP verification with `show arp vrf <vrf-name>` in addition to
  `show evpn arp-table instance <service_name>`: the plan must prove that
  IRB-subnet hosts learned from both local AC / local RT-2 and PW / EVPN-SI
  source appear in the normal ARP table and agree with EVPN + datapath state.
  Basic must also include a minimal IRB attach baseline for one EVPN VPLS SI
  service: attach one `router-interface <irb_interface>`, prove service detail
  shows exactly one router-interface owner, prove the VPLS PW remains installed,
  then prove one local AC host through normal VRF ARP, EVPN ARP, RT-2, and
  datapath. Keep heavier per-VRF isolation, RT-5 origination/reception, policy
  chains, rollback loops, and multi-service IRB moves out of Basic.
  Do not duplicate the same TC across multiple categories: each TC has one
  primary `category` and one matching `covers_categories` value. If a behavior
  has secondary relevance to another category, preserve that as metadata
  (`secondary_coverage_categories`, rubric rules, or coverage tags), not as a
  second category placement or second Jira testing task.
- Keep command methodology in MCP tool descriptors and shared reference docs,
  not in large slash-command prompt files. This preserves token budget and
  reduces stale duplicate logic.
- New command MCP tools must use `/home/dn/mcp_common` for SSE, `/health`,
  `format=json/text/both`, `summary_markdown`, collapsible JSON, timeout/error
  envelopes, and handoff redaction.
- Mutating or disruptive MCP actions must default to dry-run and require
  explicit execution/confirmation fields. BGP stop/start protection remains
  mandatory.
- DNOS config write MCPs are explicitly guarded: `dnos_atomic_commit` defaults
  `dry_run=true` and requires `execute=true` with `dry_run=false`;
  `dnos_multi_device_commit` defaults `mode=dry_run` and requires
  `execute=true` for `all_or_nothing` / `best_effort`.
- Cache-wide invalidation is a write-like operation. `dnos_dnaas_cache_invalidate`
  may invalidate a single key directly, but full-cache invalidation requires
  `confirm_all=true`.
- Nested command MCP calls into `dnos_run_show_commands` must pass singular
  `device_name`, not `device_names`; the dnos-config show runner is a
  single-device persistent-session tool.
- Cross-command orchestration should use compact handoff state and
  `suggested_next_call`, not full command reloads or ad hoc glue scripts.
- MCP triggering is intent-first, not keyword-first. A prompt that mentions
  several lab domains must select one primary MCP server/tool first; call a
  second MCP only when the first result returns `suggested_next_call`, exposes
  a concrete blocker owned by another command, or the user explicitly asked for
  a multi-phase workflow.
- Native Cursor MCP calls are the default and must be visible as MCP tool
  invocations in chat. CLI bridges (`dnos_mcp.py`, `mcp_cli.py`, direct command
  scripts) are temporary fallback only after native MCP returns `Not connected`
  or `Tool not found`, and that native failure must be reported to the user.
- Local lab MCP servers (`dnos-config`, `user-spirent-mcp`, `user-ha-mcp`,
  `user-debug-dnos-mcp`, `user-exabgp-mcp`, `user-xray-mcp`, `user-test-mcp`)
  belong in the workspace `.cursor/mcp.json` only. Do not also register them in
  `~/.cursor/mcp.json`; double registration creates duplicate `user-user-*`
  and `project-0-*` tool sets in Cursor. Keep global `~/.cursor/mcp.json` for
  truly global servers such as DN MCP, Network Mapper, and TP agent.
- Prefer cheap/read-only routing before live validation: path discovery before
  Spirent preflight, command search before config attempts, and one
  device/VLAN scope before any batch. Do not sweep live preflight/diagnose
  tools from broad wording alone.
- MCP JSON-RPC `tools/call` responses must set `isError=true` whenever the
  structured tool payload has `ok=false`; callers use this envelope to
  distinguish expected tool failures from successful read-only answers.
- Markdown summary tables emitted by MCP renderers must escape pipe
  characters and collapse multiline table cells to `<br>` so device output,
  command previews, URLs, and error messages cannot corrupt the operator view.

## Device Onboarding Backend Source Of Truth -- 2026-05-05

- The SSH dialog Save path must prefer `ScalerAPI.verifyAndRegister(...)`, which
  posts to `/api/devices/verify-and-register`; clicking outside a changed SSH
  dialog is also a save and must run the same verification/onboarding gate.
- Onboarding UX is a product contract: the dialog must show clear progress for
  verify -> backend register -> DB reference -> ready-for-APIs. Do not show a
  green success when SSH verified but backend registration failed. Existing DB
  devices reused for the current user are success, not duplicate errors.
- Device onboarding is idempotent by stable identity. The monitored registry
  must merge an already-known device by serial number or real hostname even if
  the latest Save path used a different active-NCC hostname/SN target. Do not
  create a second registry row or fail the dialog with "already exists" for a
  device that is already in the DB.
- Serial-number onboarding must hydrate the whole app device contract, not only
  SSH credentials. `/api/devices/verify-and-register` returns
  `device_context.canonical`, `capabilities`, and `monitoring_options`; the
  frontend must apply those fields before firing `device:context-updated`.
  Required fields include `_registeredDeviceId`, `_registeredHostname`,
  `_registeredMgmtIp`, `_registeredSerialNumber`, `_monitorCapabilities`,
  `_monitoringOptions`, and `_onboardingPhase`.
- The device toolbar must render safely during partial onboarding states. If
  registration is complete but live context/LLDP/stack data is still hydrating,
  toolbar actions show preparing/unavailable states and must not throw. Route
  toolbar/LLDP/Stack targets through `TopologySshTarget.pick(...)`, which
  prefers `_registeredMgmtIp` over the typed serial string.
- Onboarding errors must be actionable: unauthenticated session, insufficient
  role, backend/proxy unavailable, bad credentials, invalid/stale host, port
  closed/timeout, and offline save must be visibly distinct. Offline/unverified
  saves are allowed only as explicit user actions and must stay marked as such.
- Scaler frontend code must route protected `/api/*` calls through `ScalerAPI`
  or `window.TopologyAuth.authFetch(...)`. `ScalerAPI._fetch(...)` is the
  canonical wrapper and is required for explicit `ScalerAPI.baseUrl` deployments
  where the global same-origin fetch interceptor cannot see a leading `/api/`.
- After successful onboarding, backend resolution should consult the current
  user's monitored registry before falling back to discovery/inventory caches.
  `_resolve_mgmt_ip(...)` now accepts `monitored_registry:<key>` as a fresh
  source so SSH probe, config/context, upgrade, and push APIs resolve the same
  registered device identity instead of returning stale 404/503-style misses.
- SSH dialog API calls, console discovery, and web-terminal session identity
  must prefer `_registeredDeviceId` / `_registeredHostname` over the mutable
  canvas label. `ScalerAPI.probeConnection(deviceId, sshHost)` must pass
  `sshHost=""` when the visible host field contains a serial/hostname instead
  of a dotted IPv4 address, so the bridge resolver can use the canonical
  monitored-registry/device DB context.
- LLDP reads for existing DB devices must use `ScalerAPI.getDeviceContext(...)`
  first, because that route resolves through the monitored registry and per-user
  credentials. Discovery API LLDP endpoints remain compatibility fallbacks only.
  Link details, XRAY DP prerequisites, and the LLDP table must include
  `_registeredDeviceId`, `_registeredHostname`, and `_registeredMgmtIp` in their
  lookup candidates.
- Mutating monitored-device routes (`verify-and-register`, attach, detach)
  require engineer-or-higher role in addition to JWT auth. Reads stay
  per-user-scoped by reference ownership.

## /debug-dnos Raw Evidence And Repro Cleanup -- 2026-05-05

- `/debug-dnos` INVESTIGATE and VERIFY sessions must log exact raw show output
  for every tested device at every before/after step. A summarized statement
  such as "PE-4 stayed vpls" is not Jira-grade proof unless the session log also
  contains the command text and raw device output that produced it.
- If raw per-step output is missing, the agent must admit the gap and rerun the
  repro instead of fabricating a bug description from summaries.
- A newer repro of the same bug must clean or archive stale temporary artifacts:
  dedicated old Spirent streams, `/tmp` pcaps, and superseded scratch outputs.
  Keep the canonical `BUG_*.md`, topology JSON, and latest final session log.
- Prefer native `dnos-config` MCP show/path/preflight tools for `/debug-dnos`
  when they make collection faster, but the resulting raw show output must still
  be persisted in the session log.

## Labels Toggle Controls Link Interface TBs -- 2026-05-05

- The top-bar `#btn-link-type-labels` is the canvas Labels toggle. It still
  controls QL/UL/BUL debug labels, MP indicators, and existing lock/container
  badges, and now also controls auto-generated interface text boxes marked with
  `_interfaceLabel === true` on link-attached TB objects.
- Do not hide DNAAS/interface labels by deleting text objects or mutating saved
  topology data. `topology-draw.js`, `topology-link-drawing.js`, and PNG export
  in `topology-file-ops.js` decide visibility at render time from
  `editor.showLinkTypeLabels`; `editor.showLinkAttachments` remains the broader
  Text panel control for all link-attached text.
- After changing Labels behavior, keep `window.syncLinkLabelsToolbarButton(...)`
  in `topology-toolbar-setup.js` and the `loadTopologyFromData(...)` restore
  path in sync so topology switches and DNAAS imports refresh the button state
  before redraw.
- Clearing the contents of a TB editor is not a delete operation. The
  `TextEditorModule._setTextValue(...)` helper preserves the existing text
  object and its attachment metadata when the value is `""`; only explicit
  canvas delete/backspace actions should remove TB objects.
- DNAAS saved/discovered topologies live under the per-user built-in `__dnaas`
  section. The DNAAS domain itself is protected like other built-ins, but
  topology rows inside it use the normal delete confirmation and
  `/api/sections/<id>/topologies/<file>/delete-file` flow.

## Spirent Port Release Semantics -- 2026-05-05

- `/SPIRENT release` must call `spirent_tool.py release`, not `cleanup`, when
  the user wants manual Windows Spirent GUI access. Cleanup ends the Lab Server
  session; release preserves `dn_spirent_main`.
- `ReleasePortCommand` is the required STC primitive for freeing ownership of
  `//100.64.3.238/6/13`. `DetachPorts` alone can leave the GUI showing the
  port owned by the automation session.
- `spirent_tool.py reserve` reuses the existing Port object after a release
  instead of creating duplicate Port objects in the preserved session.

## Topologies Dropdown Domain Expansion -- 2026-05-05

- Domain rows in `topology-file-ops.js` must not rely only on the async preload
  kicked off during `_renderCustomSectionsInDropdown()`. Every expand path
  (mouse, built-in row, and keyboard) must call
  `_ensureDomainTopologiesRendered(...)` so switching topologies or rebuilding
  the dropdown cannot leave an expanded domain body blank.
- Inline topology child containers track `data-domain-topos-loading-for` /
  `data-domain-topos-loaded-for` and render explicit loading, empty, and error
  states. Preserve those markers when touching `_loadDomainTopologiesInline` or
  `_loadSharedInDomainTopologiesInline`.
- For auth-protected section/domain topology list reads in this dropdown, use
  `FileOps._authFetch(...)` or `window.TopologyAuth.authFetch(...)`; do not add
  raw `fetch()` calls to new dropdown code paths.
- `FileOps._domainTopoCache` stores topology entry objects
  (`{name, filename, id?, shared?}`), not strings. Navigation helpers such as
  `navigateTopoByOffset(...)` must derive the display key from
  `entry.name || entry.filename`.

## dnos-config MCP Auto Triggers And Readable Results -- 2026-05-05

- Natural-language lab prompts must route to the native `dnos-config` MCP tools
  automatically. Users should not need to type the exact tool name: DNAAS path,
  Spirent teach/preflight, DNOS syntax, show-command polling, commit, and
  handoff intents are covered by `.cursor/rules/dnos-mcp-no-bypass.mdc`.
- Slash commands and skills, especially `/TEST`, inherit the same trigger
  contract. If a prerequisite or phase asks a DNAAS/Spirent/DNOS question, call
  the matching MCP tool directly instead of printing a hint or reimplementing
  the lookup in SSH/Python.
- Operator-facing MCP calls should prefer `format="text"` or `format="both"` so
  Cursor's collapsible MCP result starts with human-readable Markdown. Use
  `format="json"` only when the agent is parsing fields programmatically.
- `dnos_run_show_commands` defaults to `format="text"` in
  `~/dnos_config_mcp/dnos_config_mcp/tools.py` because live show output is
  operator evidence first. Agents that need fields for parsing must pass
  `format="json"` explicitly and should avoid doing so for user-visible proof.
- If native Cursor MCP calls to `user-dnos-config` return `Not connected`, fix
  the local MCP immediately before continuing: clean-restart
  `dnos-config-mcp`, verify `http://localhost:9300/health` returns `ok`, retry
  the native call once, and only then use `~/.cursor/tools/dnos_mcp.py` as a
  temporary bridge if Cursor still needs a window reload.
- `~/dnos_config_mcp/dnos_config_mcp/rendering.py` now has dedicated renderers
  for the full dnos-config tool surface: DNAAS discovery/diagnose/fix planning,
  cache tools, command search, show-command knowledge, commits, device list,
  live show output, and agent handoffs. New MCP tools must add a renderer before
  being treated as operator-ready.

## DNAAS Discovery MCP Backend Contract -- 2026-05-05

- Topology DNAAS discovery should prefer `dnos-config` MCP for DUT-rooted
  forwarding/path semantics. The backend adapter calls the documented
  `~/.cursor/tools/dnos_mcp.py dnos_dnaas_walk_from_dut` boundary and converts
  the result into the existing `objects[]` plus `metadata.bridge_domains` /
  `metadata.device_bd_mapping` UI contract. Do not import `dnos_config_mcp.*`
  or scrape DNAAS config files from topology code.
- Network Mapper remains the right source for broad device inventory,
  onboarding, LLDP-only physical maps, management-IP resolution, and DNAAS
  device cache refresh. It does not replace `dnos-config` for BD logic because
  BD names and sub-interface suffixes are labels, not forwarding facts.
- `/api/dnaas/discovery/start` and `/api/dnaas/multi-bd/start` try the
  dnos-config adapter first for single-DUT requests and fall back to the legacy
  `dnaas_path_discovery.py` flow when the MCP has no route/AC data or when the
  caller explicitly passes `backend: "legacy"` / `use_dnos_mcp: false`.
- New DNAAS discovery adapters must keep per-user output isolation by writing
  only under the caller bucket from `discovery_api._user_output_dir(owner)`.
  Do not add global caches; rely on the dnos-config MCP cache/freshness policy.
- Frontend DNAAS helper fallbacks are still protected API calls. If `ScalerAPI`
  is unavailable, call the local `_authFetch(...)` shim for `/api/dnaas/*`,
  `/api/sections/*`, and `/api/xray/config`; never add a bare
  `fetch('/api/...')` fallback that drops JWT auth.

## Unified TP To /TEST Refinement -- 2026-05-05

- Chat triggers `/TP improve <EPIC>`, `/TP imrove <EPIC>` (accepted typo alias),
  `/TP refine <EPIC>`, `improve the TP`, `align TP with /TEST`, and
  `TP -> /TEST` mean: load the existing TP artifacts, improve the requested
  section, and keep markdown, `manifest.json`, `full_result.json`,
  `quality_audit.md`, TP reference docs, and `/TEST` import guidance in sync.
- TP test case headings must be short human-readable intent names. Preserve
  stable `TC-*` IDs as adjacent `_Test ID: ..._` metadata for automation,
  traceability, and parity gates; do not put the full proof narrative in the
  visible heading.
- EVPN IRB hierarchy coverage is behavioral. The TP must not stop at CLI parser
  acceptance for `router-interface`, `default-gateway`, `host-routes`, or
  `irb-mac-ip`: `/TEST create` validates syntax with commit-check and rollback,
  while `/TEST run` must prove the option's live EVPN/BD/VRF behavior.
- IRB service lifecycle TP coverage must include add, remove, and move between
  services with exactly one final owner. Keep this CLI lifecycle test independent
  from PW/VPLS-source MAC-IP mobility unless the user explicitly asks for PW logic.
- EVPN VPLS SI with IRB MAC/IP mobility TP coverage uses the B.11 design-doc
  scenario rows as canonical base tests and stores permutation axes in
  `mobility_permutation_model`. Do not duplicate the same behavior under every
  category; pack counters/logs/traces/scale only when the same traffic event and
  verifier surfaces prove them. Required mobility surfaces are MAC table,
  MAC-IP table, BGP RT-2, forwarding table, mobility history, AC probe evidence,
  and no-proxy-ARP-to-PW invariants.
- SW-228552/SW-241473 TP refinements must support the constrained three-device
  lab: `PE-1`, `PE-4`, and `RR-SA-2`. Section-level topology prerequisites must
  not require a fourth PE. MAC/IP mobility owner movement is SA-only between
  `PE-1` and `RR-SA-2`; `PE-4` is the CL/cluster EVPN-SI, PW-side, HA, or
  observability peer and must not be used as the mobility owner.
- For SW-228552/SW-241473 and similar TP work, render category sections in the
  FlowSpec-VPN advanced-functionality style for task organization, but keep
  topology prerequisites as numbered readiness steps, not a table. The section
  order is: topology prerequisite steps, category-level `Test Task Matrix`, then
  detailed per-TC step tables. This keeps the TP readable for review while
  preserving stable `TC-*` IDs for `/TEST` parity.
- `/TP improve` for SW-228552/SW-241473 must also run the EVPN Proxy-ARP /
  EVPN VPLS SI bug-derived flow sweep before Stage 3 self-review. Mine local
  bug evidence and reusable catalogs for remote-withdraw/clear sequence
  regressions, DP `is_pw` PW LIF marking, no-proxy-ARP-to-PW, file-loaded scale
  matrices, and scale config deltas. Promote only flows that fit the IRB routing
  component or SW-241473 datapath enabler.
- When DN MCP Jira/Confluence access is available, `/TP improve` must also write
  `company_knowledge_gap_sweep.json` and consider previous EVPN Proxy-ARP,
  EVPN IRB, and EVPN VPLS SI bugs for source-specific PW filters, IRB
  subnet/prefix filtering, clear MAC-IP operations, Anycast IRB, IPv6
  link-local Proxy-NDP, backup NCC ARP preservation, host-route FIB correctness,
  large EVI delete with MAC-IP scale, stale PW labels / ARP over VPLS, and
  sub-interface move or AC shutdown under SI scale.
- Relevant sweep findings must be promoted immediately into the main TP
  markdown, epic documentation, `manifest.json`, `full_result.json`,
  `quality_audit.md`, and `/TEST` import hints. The sweep JSON is provenance,
  not a substitute for updating the primary artifacts.
- `TC-CLI-01` for SW-228552/SW-241473 is the reference pattern: it packs `CLI`,
  `Sanity`, and `Defaults` only because each hierarchy option has explicit pass
  criteria and separate CREATE-vs-RUN assertions.

## Floating left tool rail -- 2026-05-05

- `#left-toolbar` now uses a compact `.tool-rail-mode` layout: the left rail
  stays narrow and the old accordion sections are shown inside one contextual
  `.tool-side-panel`. Keep existing button IDs intact when editing this area,
  because `topology-toolbar.js`, `topology-toolbar-setup.js`, and older modules
  still bind to IDs like `btn-link`, `btn-link-curve`, `device-styles-box`, and
  `xray-save-config`.
- Bare number keys are canvas tool shortcuts: `1` select, `2` link, `3`
  device panel, `4` shape, `5` text, `6` laser, and `0` settings. Topology
  quick-jump moved to Cmd/Ctrl+`1..9`; `Alt+Left/Right` remains the previous
  and next topology shortcut.
- Packet-capture workstation settings and Helpers live under the rail Settings
  panel. Do not add them back as first-class rail tools unless the UI direction
  changes.
- Laser pointer is a non-persistent canvas mode. Its trail lives only in
  `editor._laserTrail`, is rendered by `topology-draw.js`, and must never be
  added to `editor.objects[]` or saved topology JSON.
- Laser panel color and fade duration are client UI preferences only:
  `laserPointerColor` and `laserPointerFadeMs` in `localStorage` initialize
  `editor._laserColor` / `editor._laserFadeMs`. They control transient trail
  rendering and must not become topology object fields or backend state.
- Text rail activation and bare key `5` must enter Place TBs immediately:
  `ToolbarManager.activateTool('text')` routes through
  `enterTextPlacementMode()`, turns `continuousTextPlacement` on, and syncs
  `#btn-place-tbs` / `#place-tbs-status`. Do not regress this back to merely
  opening the text panel.
- Laser drawing remains non-persistent and uses hold-to-draw for live movement.
  `topology-laser.js` owns transient trail appends: left-button down/move/up
  call `TopologyLaser.appendTrailPoint(...)`, which prunes faded points,
  interpolates bounded intermediate points between the last visible spot and the
  new spot, and caps trail length so click-to-click laser movement draws a
  continuous fading segment instead of jumping. Mouse move still appends only
  while `_laserPointerActive` is true, mouseup clears that active flag, and
  leaving laser mode clears active trail state.
- The contextual side panel is intentionally content-sized with a `max-height`,
  not a full-height sheet. Link and text color pickers share the synchronized
  `lastUsedColors` model and show up to eight recent colors; keep future color
  controls on that same recent-color store instead of adding per-tool histories.
- **v2.4 submenu design contract:** left-rail panels use a scoped
  `body.ui-skin-v2 .tool-side-panel` command-card layer in `styles.css`.
  Preserve the compact popover geometry, solid premium panel surfaces, nested
  card sections with a thin accent strip, visible `:focus-visible` rings, and
  consistent option-row/toggle/swatches styling across Link, Device, Shape,
  Text, Laser, and Settings. Future refinements should extend this CSS layer
  without changing toolbar IDs, inline behavior hooks, or the rail activation
  mechanism.

## Auto-curve sticky side (no flicker on UL stretch) — 2026-05-05

The auto-curve direction (`curveDir`) used by the magnetic-repulsion renderer
in `topology-link-drawing.js` is decided through `window.LinkAutoCurveSide`
(`topology-link-auto-curve-side.js`). Two cooperating mechanisms keep the
curve from flipping while the user stretches a UL past a device.

### Mechanism 1 — pressure-side hysteresis (always on)

`LinkAutoCurveSide.choose(link, posPressure, negPressure)` caches the chosen
side on `link._autoCurveSide` and only flips when the OPPOSITE perpendicular
side carries substantially more pressure than the cached side
(ratio ≥ `FLIP_PRESSURE_RATIO=1.6` AND absolute delta ≥ `FLIP_ABS_DELTA=12`).
This handles ambient flicker — small obstacle drift, multi-link parallel
offset wiggle, magnetic-field tweaks — without any user-input signal.

Both repulsion sites (connected `drawLink` and `drawUnboundLink` UL path)
call `choose()`; the no-obstacle and curve-disabled branches all call
`LinkAutoCurveSide.clear(link)` so re-entering an obstacle field starts a
fresh decision rather than inheriting a stale one.

### Mechanism 2 — pointer-path lock during stretch (the user-reported fix)

Pure pressure hysteresis cannot kill the flicker the user sees while
*stretching* a UL TP around a device, because the (anchor → pointer) axis
itself rotates as the pointer orbits the obstacle, so the obstacle's
perpendicular sign flips naturally — no amount of pressure smoothing can
hide that geometry.

The fix: while a stretch is active, the user's pointer path is the source of
truth. Wired in `topology-mouse-move.js` and `topology-mouse-up.js`:

1. `LinkAutoCurveSide.beginStretch(link, anchorX, anchorY, pointerStartX, pointerStartY)`
   is called the moment `_pendingStretch` exceeds threshold. It freezes the
   `(anchor → pointerStart)` axis on the link as `_stretchPointerSide`.
2. Every `mousemove` while stretching, `LinkAutoCurveSide.updateStretch(link, pos.x, pos.y)`
   accumulates the pointer's signed perpendicular travel against the *frozen*
   axis. Once travel on one side exceeds `POINTER_COMMIT_PX=18`, the helper
   calls `lockSide(link, side, { pointerLocked: true })`. While
   `link._autoCurveSidePointerLocked === true`, `choose()` returns the locked
   side unconditionally regardless of pressure.
3. `LinkAutoCurveSide.endStretch(link)` is called on `mouseup`. It releases
   the pointer lock but KEEPS `_autoCurveSide` cached, so the curve stays
   where the user put it after release.

`updateStretch` MUST be fed the RAW pointer (`pos.x`, `pos.y`) BEFORE the
sticky-snap pull, otherwise stickiness drags the signal toward the device
and erodes the side decision. The unit test pins this verbatim.

### Load order, sync, tests

`topology-link-auto-curve-side.js` MUST load before `topology-link-drawing.js`
in `index.html` (already wired). When tuning the constants, bump the cache
buster on the helper file AND on `topology-link-drawing.js`,
`topology-mouse-move.js`, and `topology-mouse-up.js` whenever any of them are
edited.

Tests: `topology/tests/test_link_auto_curve_side_unit.py` pins both the
static wiring (helper exists, drawing module + mouse modules reference it at
every branch, HTML loads it first) and the runtime contract via Node:
- small drift never flips
- decisive opposite-side dominance does flip
- `clear()` resets
- pointer commit locks the side AND pressure cannot override the lock
- `endStretch` releases the lock but keeps the side
- uncommitted stretches do NOT overwrite an existing cached side

Run `python3 tests/test_link_auto_curve_side_unit.py` after touching any of
these files.

## DN Command Pack — 2026-05-04

- Reusable Cursor command packaging lives at `~/.cursor/dn-command-pack/`.
  Use `install.sh --project <repo> --mode symlink --with-mcp` to bootstrap a
  project with the DriveNets slash commands, reusable skills, rules, reference
  docs, tools, and the safe local `dnos-config` MCP entry.
- The pack is a pointer pack by default: commands, skills, rules, references,
  tools, `~/SCALER`, and `~/dnos_config_mcp` are symlinked so updates stay
  centralized. Use `--mode copy` only when a project needs a frozen snapshot.
- Portable GitHub source lives at `https://github.com/YarelOr-dn/dn-command-pack`
  as a private repo. New machines/projects can clone it to
  `~/.cursor/dn-command-pack` and run `install.sh --project <repo> --mode symlink
  --with-mcp`. The portable repo vendors safe Cursor assets and the
  `dnos_config_mcp` source, while keeping `~/SCALER`, `~/cheetah`, and
  `~/cheetah_26_1` as external environment-driven roots.
- No secrets belong in the pack. `mcp/mcp.example.json` must keep placeholder
  tokens only, and project `.cursor/mcp.json` files are backed up before the
  safe `dnos-config` entry is merged.
- Cheetah roots are readonly inputs. Use `CHEETAH_ROOT` and
  `CHEETAH_FALLBACK_ROOT`; installers and healthchecks must not fetch, checkout,
  reset, or update Cheetah source trees.
- Lab migration profiles live in the command pack under `lab-profiles/`.
  Install with `install.sh --profile current|houston --profile-scope user|project`.
  Lab-sensitive commands must load `active.env` before using SCALER, Spirent,
  DNAAS, Network Mapper, MCP endpoints, or default DUT assumptions.
- Houston migration references live under `reference/lab-migration/` in the
  command pack: hardcoded-assumption audit, Houston inventory checklist, and
  parallel smoke tests. Keep current lab as default until Houston smoke tests
  pass.

## 📁 Key File Locations

| Purpose | Location |
|---------|----------|
| Main topology logic | `topology.js` |
| Styles | `styles.css` |
| HTML entry point | `index.html` |
| Debugger panel | `debugger.js` |
| DNAAS discovery | `dnaas_path_discovery.py` |
| Scaler bridge API | `scaler_bridge.py` (port 8766) |
| Momentum physics | `topology-momentum.js` |
| History/undo | `topology-history.js` |

### Ultimate Generate topology pipeline — 2026-04-28

- **Frontend owner:** `topology-generator.js` treats live Generate as an architecture composition pipeline. After `adapterLive(...)`, `_generateFromLive()` calls **`POST /api/topology-generator/correlate`** with collected facts; the backend builds a **per-user temporary SQLite** file under `user_store.user_data_path(username, "tmp/topology_generator/correlate_<run>.db")`, runs BGP/LLDP/VRF/BD/RT cross-reference + symmetric layout, returns enriched `facts`, then **always unlinks** that DB in `finally`. On HTTP/`ok:false` failure the UI logs a warning and falls back to **`composeArchitectureFacts(...)`** (in-browser prune/correlate) before `buildCanvasPayload(...)`.
- **DUT inclusion rule:** generated live topology renders SSH-backed DUTs only. DNAAS/fabric/non-SSH devices must not become generated canvas devices. Expected app-resolvable devices such as `PE-4` must be preserved when canvas SSH evidence exists through `sshConfig.host`, `hostBackup`, `_snVerifiedHost`, `_activeNccHost`, or `_virshInfo.activeNcc`.
- **DNAAS exclusion nuance:** classify DNAAS/fabric by the canvas device identity (`label`, `name`, `hostname`, serial), not by the SSH transport host. PE DUTs may legitimately connect through an active NCC/SN host, so a `NCC` transport string must not cause `YOR_CL_PE-4`/`PE-*` to be skipped.
- **PE-4/app resolution rule:** never overwrite a working canvas/app SSH host with an empty or missing `/resolve-targets` result. `getCanvasSshTarget(...)`, `enrichTargetFromCanvas(...)`, and `_mergeResolvedWithTargets(...)` are the guard path for SN-verified / active-NCC devices.
- **Native rendering rule:** protocol labels must be native text boxes attached to links (`linkId`, `linkAttachT`, `_onLinkLine`, `_linkDataLabel`). Logical overlays use `curveMode: "manual"` and `manualCurvePoint`; do not generate transient `manualControlPoint` state.
- **Service visual rule:** RT/VRF/BD correlations are service facts, not topology links. Do not render RTs as dashed link overlays. Render correlated services as generated service cards/callouts with member DUTs and RT summaries, while keeping physical/BGP/IGP as the primary link topology.
- **Unmatched DUT rule:** a preserved DUT with no correlated edges must display a generated reason label (for example no running-config facts, no BGP/VRF/RT/LLDP evidence, or no matched peer). Do not leave devices like `PE-4` isolated without an explanation.
- **Generated visibility groups:** generated links, attached TBs, shapes, and labels carry `_generatedGroupIds`, `_generatedLayer`, `_generatedProtocol`, and `_generatedTopologyObject`. The generated layer panel follows the Bridge Domain visibility pattern by setting `_hidden` on grouped objects and propagating parent link visibility to attached TBs.
- **Generated Topology V2 scene model:** generated objects also carry `_generatedConfidence`, `_generatedSource`, `_generatedEvidence`, `_generatedDisplayPriority`, and deterministic `_generatedLane` on links. Confidence values are exactly `verified`, `correlated`, `inferred`, or `missing`; keep live/LLDP data verified, sqlite/BGP/service joins correlated, perimeter/alias/fallback data inferred, and unmatched failures missing.
- **Generated label/layout V2:** layout reserves routing, access, service, and evidence zones. Service cards are reserved before link label placement so labels choose candidate slots away from devices/cards instead of stacking at the same midpoint.
- **Generated panel V2:** the panel should stay compact with Clean/Routing/Services/Evidence/Full presets, BGP overlay mode, confidence chips, and count-bearing layer accordions. Evidence, perimeter, and via-RR overlays remain hidden by default.
- **Learning storage:** per-user Generate learning is backend-backed through `/api/topology-generator/learning*` and `user_store.user_data_path(username, "topology_generator_learning.json")`. Do not store learned topology style globally or in unscoped localStorage. Learning must stay inspectable/resettable and should only learn accepted generated output.
- **Placement rule:** applying or saving a generated preview must use the in-app **`#gen-placement-modal`** placement dialog, never browser-native `prompt()` / `confirm()`. The modal asks for destination domain (existing or newly created) and topology name, sits above the Generate/Discover panel (`z-index` must exceed the panel's inline `999999`), then the apply path saves through `/api/sections/<section_id>/save` first, loads the saved payload, and updates the active topology indicator.
- **DNOS operational facts:** `device-facts?live=1` and scaler monitor context may collect verified show commands only. Current verified protocol commands are `show bgp summary`, `show isis neighbors`, `show ospf neighbors`, and `show ldp neighbors detail`; Generate may also use `show route summary`. Consult DNOS CLI docs before adding any new command.
- **Share revoke safety:** `topology-sync.js` may force-close an active topology on `topology.unshared` / `domain.unshared` only for the actual revoked `target_user` (or legacy shared-in viewers when no target is present). The owner/originator must only refresh sharing UI, never see "Your access was revoked" for their own topology.
- **Regression coverage:** `topology-tests.js` has a golden Generate fixture that verifies PE-style SSH DUT preservation, DNAAS/non-SSH pruning, attached TBs, manual logical curves, and generated visibility metadata. Update that fixture when changing generated object contracts.

### Live Link Telemetry — 2026-04-30

- **Purpose:** Link Tables can auto-fill from actual DUT data. Frontend owner is
  `topology-link-telemetry.js` plus the existing `topology-link-table.js`,
  `topology-link-details.js`, `topology-link-drawer.js`, and
  `topology-xray-popup.js`. Backend owner is `topology/routes/link_telemetry.py`
  with provider/parsing code under `topology/telemetry/`.
- **Transport rule:** Phase 1 uses DNOS SSH/CLI through
  `routes._device_comm.DeviceCommHelper` so per-user credentials, per-user SSH
  pool keying, and existing SSH resolution are reused. `gnmi_provider.py` is a
  Phase-2 stub behind the same provider contract; do not add raw pygnmi calls in
  frontend code or route handlers.
- **Validated DNOS commands:** `show interfaces`, `show interfaces description`,
  `show interfaces counters`, `show lldp neighbors`, `show lacp interfaces`,
  `show config | flatten`, `show config defaults interfaces`,
  `show bgp summary`, and `show isis neighbors`. MTU is sourced from
  interface config/defaults instead of table descriptions. Protocol-state
  refresh may also use documented `show ospf neighbors` and
  `show ldp neighbors detail`. Do not use `show interfaces brief`,
  `show lldp neighbors detail`, or `show isis adjacency`; the documented LLDP
  detail path is `show lldp neighbors <interface>`.
- **Config and operational source of truth:** Service attachment, bundle
  membership, sub-interface parents, IP addresses, and protocol configuration
  come from `show config | flatten` via `telemetry/config_parser.py`. Actual
  admin/oper state, MTU, and displayed VLAN stack come from `show interfaces`
  because DNOS exposes translated stacks such as `219, 3101(i)` there. Config
  VLAN values may fill missing data only when they are scalar VLAN IDs; never let
  config/default values like `list` overwrite an operational VLAN stack. Do not
  infer forwarding VLANs from sub-interface suffixes or `show interfaces
  description` when the operational table has a VLAN column. If live config is
  unavailable, `ssh_provider.py` may fall back to SCALER DB cached `running.txt`
  through `routes.bridge_helpers._get_cached_config()` and flatten the
  hierarchical config before parsing. Descriptions may be displayed as
  hints/tooltips only.
- **DNAAS BD naming rule:** Bridge-domain names and sub-interface suffixes are
  labels, not the forwarding contract. For example, PE-4 user VLAN 219 traffic
  may legitimately traverse DNAAS fabric sub-interface `.213` when BD membership
  and VLAN push/pop logic translate it. Test gates must validate live BD logic,
  interface VLAN selectors, and expected DUT AC readiness instead of requiring
  literal suffix matches such as `.219` on every DNAAS hop.
- **DNAAS port-mode AC rule (2026-05-05):** PE-4 `ge100-18/0/1` for fabric
  VLAN 211 is a true untagged/port-mode landing. `dnos-config` DNAAS inverse
  path and Spirent preflight must infer that from the reachability map when
  DUT config has no `vlan-id`/`vlan-tags`; do not convert the Spirent recipe
  back to `--vlan 211`, and do not treat the missing synthetic
  `DNAAS-LEAF-B10 ge100-0/0/4.211` probe as a path blocker.
  If the user names the DUT AC/interface, callers must pass `port_or_subif`
  (or `ac_interface`) to `dnos_dnaas_teach_plan` /
  `dnos_dnaas_spirent_preflight`; the MCP resolves that AC through
  `dnos_dnaas_inverse_path` first and lets the resolved AC override guessed
  `vlan` / `inner_vlan` inputs. This is what prevents the bad
  `--vlan 3101 --no-qinq` style recipe for PE-4 port-mode traffic.
  Live proof on 2026-05-05: a 1 Mbps untagged L2 stream with source MAC
  `00:de:ad:00:21:11` arrived on PE-4 `ge100-18/0/1` at ~0.865 Mbps and
  learned as `Local` in `EVPN_SI_VPLS_1`. For renderer/evidence purposes,
  model the B10 egress as physical port-mode endpoint `ge100-0/0/4` in
  BD `g_yor_v211_STC-TO-CL_port-mode`; the absence of `ge100-0/0/4.211`
  is expected and must not be displayed as a missing egress path.
- **DNAAS LLDP enable first-run rule:** The "Enable LLDP" button must send
  `ssh_host` only when the canvas device already has an explicit SSH host. Do
  not fall back to the device label/serial in the `ssh_host` field: that makes
  `discovery_api.py` trust the label as a direct host and skip its resolver,
  which breaks the first click before SSH facts are initialized. The backend
  LLDP enabler must use documented DNOS syntax (`protocols lldp admin-state
  enabled`, `protocols lldp interface <physical>`, `show lldp neighbors`) and
  treat commit errors as job failures. Physical interface discovery must cover
  `ge`, `xe`, `et`, `hu`, `ce`, and `qsfp` prefixes. Keep `discovery_api.py`
  POST handler imports module-scoped; a later local `import re` inside
  `_do_POST_inner()` shadows the module import and turns LLDP job submission into
  HTTP 500 before the async job starts. When no explicit `ssh_host` is sent,
  `_enable_lldp_on_device()` must call `_resolve_serial_to_host(serial)` before
  SSH; direct DNS-only fallback makes labels like `RR-SA-2` fail with
  `Name or service not known`. Inventory entries whose key or `serial` is an IP
  (for example `100.64.4.205` with hostname `RR-SA-2`) are valid resolver hits.
- **DNAAS job hardening rule (2026-05-04):** LLDP enable, DNAAS discovery, and
  Multi-BD discovery jobs must persist per-user job snapshots in
  `user_store.user_data_path(username, "discovery_jobs.db")` (anonymous legacy
  callers use the isolated global output bucket). Active jobs restored after a
  `discovery_api.py` restart must surface as `interrupted`, not raw 404. LLDP
  is mutating DNOS config: normalize the resolved target as the device key,
  run SSH reachability preflight before starting, and return a watch/queue
  conflict response instead of launching concurrent commits for the same
  device. Read-only Stack/Git/DNAAS fetches stay outside LLDP mutation locks.
- **Shared SSH target picker rule (2026-05-04):** Frontend callers that need an
  SSH transport target must use `topology-ssh-target.js`
  (`window.TopologySshTarget.pick(...)`). Do not copy hostname/`hostBackup`
  precedence logic into Stack, Git Commit, terminal, LLDP, or DNAAS modules.
  Verified IP fields such as `hostBackup`, `_activeNccIp`, and enriched
  management IPs must beat display names/labels.
- **Cluster console NCP label rule (2026-05-04):** Console discovery for CL
  clusters often reaches a data-plane NCP serial port, while NCC access goes
  through KVM/virsh. A serial suffix like `WDY19C7M00013-P3` is only a
  console-board serial hint; render it as `NCP data-plane (serial P3)`, not
  `NCP-3`. Only explicit mapping metadata (`ncp_id`, `console_ncp`,
  description saying `NCP-18`, etc.) may render a precise `NCP-<id>` label.
- **Stack dialog active NCC rule (2026-05-04):** Cluster stack cached data must
  preserve `active_ncc_node` / active NCC metadata when `DeviceMonitor` writes
  `device._stackData`. `topology-stack-dialog.js` must render the Active NCC
  badge/banner from any available source (`_virshInfo.activeNcc`,
  `_activeNccVm`, `_activeNccHost`, or cached `active_ncc_node`) so opening a
  cached Stack table still shows which NCC is active.
- **DNAAS MCP suffix-blocker rule (2026-05-04):** `dnos_dnaas_*` tools must not
  emit `FABRIC_HOP_SUBIF_MISSING` for a template interface like
  `bundle-60000.219` when the live BD logic index already found a matching
  endpoint on the same physical/bundle parent (for example `.213`) whose VLAN
  selector/manipulation carries the requested transport. The MCP and `/TEST`
  both corroborate suffix-derived blockers with expected DUT AC readiness.
- **dnos-config MCP native health rule (2026-05-04):** The local
  `dnos-config-mcp` service is the native Cursor MCP surface for transactional
  DNOS reads/writes and DNAAS logic at `http://127.0.0.1:9300/sse`. Keep the
  Cursor MCP config pinned to `127.0.0.1` instead of `localhost` so
  restart/reconnect uses a fresh local session. The same `/sse` URL accepts
  Cursor's direct HTTP JSON-RPC POSTs for `initialize`, `tools/list`,
  `tools/call`, and `ping`, while still serving legacy SSE clients. If native
  `CallMcpTool` reports `Not connected`, verify the service first with an SDK
  SSE client, then restart/reload Cursor MCP; do not silently downgrade
  `/TEST` or `/SPIRENT` logic to embedded Python when native MCP is reachable.
  The exported descriptor set must include every live server tool, including
  `dnos_atomic_commit`.
- **Auto-fill rule:** Live telemetry is the owner of normal Link Table refresh.
  It stores results under `link.linkDetails.live` and updates Dynamic Link Table
  values from live device data unless the user edited a field during the
  current modal session. When a protected user-edited field differs from live,
  show a "use live" action instead of overwriting it. The Dynamic tab must show
  an Interface-to-Interface selector for Side A and Side B; selections are
  auto-picked from live facts until the user changes either side, then that side
  stays pinned for the modal session. If one side's live rows are still loading
  or empty, the selector must still show fallback choices from correlation
  candidates and current Link Table/canvas hints. Candidate selection is keyed
  by the detected pair (`kind/ifA/subA/ifB/subB`), not by array index; auto
  selections stay sticky for that pair across refreshes so the UI does not jump
  between interfaces when live rows arrive in a different order.
- **SSH target priority rule (2026-05-04):** Stack Table, Git Commit, LLDP, and
  terminal launchers must not let a canvas display hostname/label override a
  verified transport address. Prefer IP-bearing targets such as
  `_activeNccIp`, `hostBackup`, `host`, `_enrichedMgmtIp`, and `_nccMgmtIp`
  before non-IP labels. Only use a hostname when it is a verified SN/active-NCC
  host or there is no IP fallback. This prevents labels like `RR-SA-2` from
  shadowing reachable targets such as `100.64.4.205`. Git Commit fetches are
  valid when sourced from `/.gitcommit`; fallback code may try relative
  `.gitcommit` only after the absolute path fails.
- **Correlation order:** Interface-to-interface matching is scored, not a single
  hard-coded fallback: LLDP exact peer evidence wins, then same subnet, same
  QinQ VLAN stack, operational protocol adjacency (`ISIS`, `OSPF`, `LDP`), exact
  logical unit/service identity, and finally canvas hints. QinQ requires both
  outer and inner VLANs to match when either side has an inner tag; never
  collapse `outer.inner` sub-interface names to only the last tag. Service
  attachment on both sides is supporting evidence only; it must not by itself
  match different outer/inner VLAN rows such as a DNAAS bridge-domain AC to an
  unrelated RR sub-interface. The response must include `correlation.kind` as
  `physical`, `bundle`, `sub-bundle`, `sub-interface`, or `none`, plus a ranked
  `correlation.candidates[]` list for the Dynamic tab selector. `none` renders
  an explicit "no live link detected" state instead of guessing.
- **Logical interface resolution:** LLDP may identify only the physical LACP
  member. The correlator must map that member through `BundleRow.members` and
  `members_config` to the owning `bundle-*`, then upgrade to `bundle-*.vlan`
  when VLAN, service attachment, IP subnet, or protocol evidence proves the
  sub-bundle is the communicating interface. Canvas interface labels use
  `correlation.logicalIfA/logicalIfB`; physical member evidence should remain in
  telemetry/debug context and Live Telemetry, not as duplicate Dynamic rows.
- **Down-but-expected links:** Admin/oper state is health evidence, not identity
  evidence. Configured LACP membership, sub-interface parentage, service
  attachment, protocol config, and cached/last LLDP can identify the intended
  peer even when either side is down. Such candidates must return both POV state
  (`stateA/stateB`, `memberStateA/memberStateB`) and a status such as
  `verified-up`, `expected-down`, or `configured-only` so the UI can show the
  intended connection and its live failure state together.
- **Refresh triggers:** Refresh can run from link modal open, link create/endpoint
  change detection, the Align with devices button (bulk `refreshAll`), and a
  15-second modal auto-refresh timer backed by a 15-second per-user device
  batch cache. On modal open, render cached
  `link.linkDetails.live` immediately when present, then refresh live in the
  background. Side A and Side B device fetches run in parallel in
  `routes/link_telemetry.py`; do not reintroduce serial per-side refresh. Stop
  the timer when Link Table closes.
- **Dynamic field visibility:** The normal Dynamic table view must be a compact
  evidence table, not per-side POV summary cards or debug dumps. Show the
  selected interface, parent/logical unit, state+MTU, outer VLAN, inner VLAN,
  TPID, related same-parent QinQ rows, IP, service attachment, protocols, and
  evidence rows directly. Keep outer/inner VLANs and ingress/egress VLAN
  manipulation as separate rows so the table can be scanned vertically. Rows
  must be readable without zooming: labels around 11px and evidence cells around
  12px with at least 36px row height. A
  sub-interface suffix
  such as `bundle-100.215` is the logical unit/service VLAN, not proof of an
  operational inner tag; show it separately from the live outer/inner stack.
  VLAN manipulation must
  prefer live `vlan-manipulation egress-mapping action ...` from `show config |
  flatten` and fall back to saved Link Table ingress/egress fields only when
  live config is absent. Live sub-interface VLAN discovery must also switch the
  static Link Table VLAN mode to `vlan-tags` so `lt-outer-tag-*` and
  `lt-inner-tag-*` become visible and keep the stored link fields in sync.
  Bundle member tables belong in Live Telemetry; the Dynamic table should stay
  compact, sharp, and avoid duplicate member rows. Protocol details must be a
  collapsible table. Use a subdued, consistent dark palette for Link Table
  evidence cells; avoid mixing high-saturation VLAN colors with light and dark
  field backgrounds.
- **Link Table resize/member contract (2026-05-04):** The active modal resize
  helper must maintain both `data-width` and `data-height`; tall mode reveals
  diagnostic rows, and wide mode shows both Live Telemetry POV panes side by
  side. Sub-bundle selections such as `bundle-100.215` must resolve their parent
  `bundle-100` before rendering LACP mode and MTU fallback. DNOS bundle
  membership commonly appears as `interfaces <physical>
  bundle-id <N>` in flattened config, so `telemetry/config_parser.py` must parse
  that form into `BundleRow.members_config`; do not rely only on legacy
  `interfaces bundle-N member <if>` lines. Dynamic telemetry cells are evidence,
  not editing controls: render them as read-only text/details and keep edits in
  the normal Link Table fields.
- **LLDP + VLAN logical match contract (2026-05-04):** LLDP reports physical
  ports, but Link Tables must prefer the logical service endpoint when
  sub-interface evidence exists. `telemetry/lldp_correlator.py` should promote
  an LLDP physical pair to a matching sub-interface pair by outer/inner VLAN, IP
  subnet, protocol, or service attachment. When multiple sub-bundle pairs score
  similarly, prefer exact logical-unit suffix/name matches and matching inner
  VLAN evidence over first-seen same-outer-VLAN pairs. If only one side exposes
  the sub-interface, infer the peer name as `<lldp-parent>.<outer>[.<inner>]`
  and include `outerVlanA/B` + `innerVlanA/B` in the candidate so the frontend
  still fills VLAN-aware fields. The frontend selector must preserve these
  inferred tags in fallback rows, expose QinQ rows under the detected bundle
  parent, and prefer inferred sub-interface candidates before falling back to
  physical rows. If the selected row has no inner VLAN but same-parent,
  same-outer QinQ rows exist, keep the selected row stable and show those
  related QinQ rows explicitly instead of silently changing the interface.
- **Resizable modal fill contract (2026-05-04):** Do not cap
  `.link-table-scroll` at a fixed `max-height`; it must flex to the available
  modal height with `min-height: 0` so a user resize reveals Dynamic diagnostics
  instead of leaving blank space below the action buttons.
- **XRAY integration:** Packet capture launched from a live telemetry row passes
  `srcRow` context into `XrayPopup.show(...)`. POV, source interface, VLAN/IP
  auto-filter toggles, and direction must stay tied to the selected row. XRAY
  launched from the link toolbar must ask `LinkTelemetry.getXrayContextForLink`
  for both current Dynamic selector rows and pass `srcRows` into the popup, so
  switching POV changes the source interface to the selected row for that side.
  The XRAY popup's "Use selected POV interface" checkbox is the escape hatch for
  a general device capture: when unchecked, the request sends `interface: any`
  and suppresses row-derived VLAN/IP filters.
- **XRAY completion semantics:** A capture is not successful just because the
  helper process exits. CP/DP helpers must exit non-zero on fatal exceptions,
  and the backend must reject a clean process exit that happens before the
  requested duration. For Mac outputs, the frontend can show success only when
  `mac_delivery_status == delivered`; completed-but-unconfirmed delivery with a
  saved server pcap must render a neutral retry/download prompt, not a stale
  "waiting" banner and not a hard "Mac delivery failed" warning. Reserve
  `failed` for explicit `MAC_DELIVERY_FAILED` markers or missing pcap data.
  XRAY mode detection must be cache-first (existing monitor/canvas LLDP), then refresh
  live in the background; never block the popup on live LLDP fetches before
  enabling DP/DNAAS buttons from cached facts. When selected-link context captures
  on a VLAN sub-interface (for example `bundle-100.12`), show the VLAN in the UI
  but do not add `vlan 12` to BPF; the tag is usually stripped at that capture
  point and the filter can produce empty pcaps. Live Capture (Arista/DP) uses the
  clicked row's parent interface for mirroring while CP capture can use the exact
  clicked sub-interface. Detection must treat Arista/EOS/veos LLDP neighbors as
  Live Capture targets and DN-LEAF/DN-SPINE/DNAAS/fabric neighbors as DNAAS-DP
  targets; one failed side's live context refresh must not disable both buttons
  when the other side has usable cached or live LLDP.
- **POV-safe capture filters:** Row-derived VLAN/IP filters only apply when the
  clicked telemetry row belongs to the currently active capture POV. If the user
  switches POV after opening XRAY, keep the capture interface on the active POV
  and suppress the clicked row's VLAN/IP BPF predicates so the filter cannot
  target the opposite side's interface/IP by accident.
- **XRAY DUT target resolution:** CP capture may use the exact selected
  sub-interface (for example `bundle-100.215`), but SSH must still target the
  resolved DUT management address. `topology-xray-popup.js` must use
  `window.TopologySshTarget.pick(...)` and must not send canvas labels such as
  `RR-SA-2` as `dut_host`. If the picker only has a serial/label, omit
  `dut_host` and let `serve.py::_xray_resolve_dut_host()` resolve it through
  inventory before launching `live_capture.py`.
- **Mac delivery guard:** XRAY Mac delivery must not SCP/open header-only pcaps.
  A classic empty pcap is 24 bytes; treat it as `MAC_DELIVERY_FAILED:
  empty_pcap`, leave the file on the server, and tell the user the capture
  produced zero packets instead of opening Wireshark on a useless file. The XRAY
  sidebar settings must use `TopologyAuth.authFetch` for `/api/xray/config`
  reads/writes so each user's saved Mac IP/password is the one used by capture.
  The delivery helper in `/home/dn/xray/common.py` must use Paramiko SSH/SFTP
  for Mac copy/open instead of shell-string `sshpass scp` commands; this keeps
  Mac paths with spaces safe and lets `/Applications/Wireshark.app/Contents/MacOS/Wireshark`
  launch directly with `-r <pcap>` instead of the broken `open -a <binary>` form.
- **Delivery status source of truth:** The browser must not invent a fixed
  "Mac delivery timed out" failure after the capture duration expires. DNAAS-DP
  and large DP pcaps can spend more than 45 seconds collecting from the leaf/spine
  path, compressing, SCPing, and opening Wireshark. Keep polling
  `/api/xray/status/<id>` until the backend returns `completed` or `error`; only
  backend `MAC_DELIVERY_FAILED` markers should render the retry/download prompt.
  If status polling itself fails repeatedly, surface that as "XRAY status lost"
  instead of silently leaving the popup in an infinite "Delivering..." state.
  For `mac` / `mac-live` output, `/api/xray/status/<id>` must include
  `mac_delivery_status` and the popup must not render green completion until that
  value is `delivered`. A capture process that exits 0 without a Mac delivery
  confirmation but leaves a valid pcap should use `unconfirmed` so the user can
  retry delivery or download; do not tell the user the capture failed.
- **XRAY PCAP retention policy (2026-05-05):** Only Yarel's accounts
  (`yarel`, `yor`, and direct aliases) may retain server-side PCAP files.
  Every other authenticated user is ephemeral: captures are written only under
  that user's `user_store.user_captures_dir(username)` workspace, then deleted
  after confirmed Mac delivery, after browser download, after redelivery
  attempts, or after failed capture completion. If a non-Yarel capture needs a
  browser download because Mac delivery is unconfirmed, it gets bounded
  temporary retention and a cleanup timer; do not add new paths that persist
  non-Yarel PCAPs in `/home/dn/CURSOR`, `topology/`, `/tmp`, or a shared global
  directory.
- **DNAAS-DP mirror setup:** DNAAS leaf mirror setup can fail before any pcap is
  created if the auto-selected `port_mirroring` destination interface has
  sub-interfaces. `live_capture.py` must return non-zero on fatal DNAAS setup
  errors so `/api/xray/status` shows `error`, and the DNAAS mirror picker should
  try all discovered `port_mirroring` destination candidates before failing.
  The XRAY popup must not enable or suggest DP(DNAAS) from LLDP alone; it must
  first run the authenticated `/api/xray/dnaas-mirror-preflight` check, which
  reads `show interfaces description`, `show services port-mirroring sessions`,
  and `show config interfaces | flatten` on the DNAAS leaf and only enables the
  button when a physical mirror destination is free and has no sub-interfaces.
- **Telemetry table UX:** The Live Telemetry table is row-selectable but must not
  force modal tab changes. Clicking a row pins that side in the Dynamic selector;
  clicking `PCAP` first pins the same row and then opens XRAY with the normalized
  `srcRow` for that exact row. Keep the table compact and symmetric across Side
  A/B cards: PCAP, interface, state, VLAN, attachment, and detail columns. Each
  POV card can expose sub-options for all, sub-interface, bundle, and physical
  rows without changing the selected Dynamic tab side. Live admin/oper state
  from the selected row must persist into `link.linkDetails` and update the
  visible interface field styling immediately after refresh or row selection.
  The collapsible Dynamic selector must offer only interfaces that belong to
  detected correlation candidates for this link: direct physical LLDP peers,
  LACP-promoted bundles, and sub-interfaces/sub-bundles proven by VLAN, service,
  IP, or protocol evidence. Do not repopulate that selector with every interface
  on the device. Bundle rows must show a members column/row that joins configured
  and live LACP members with each member's physical admin/oper state so the user
  can see why a bundle is valid or down-but-expected.
- **Attached interface labels:** Auto-generated interface text boxes
  (`_interfaceLabel`, `_onLinkLine`) must follow the same visual path that
  `drawLink()` rendered. Prefer `link._renderedEndpoints` plus `_cp1/_cp2`; if
  they are unavailable or their device-position anchor is stale, mirror
  `drawLink()`'s shape-aware endpoint and dynamic parallel-link offset
  calculation. Do not position labels from a simple center-to-center device
  radius line or a stale `link.linkIndex`.
- **Link Table stale-render guard (2026-05-05):** Link Table DOM fields are
  persistent across modal opens, so validation/autosave listeners must be
  idempotent (`bindFieldListener`) instead of adding duplicates on every open.
  Live telemetry refreshes must carry a per-link request sequence and endpoint
  signature; late responses from an older topology/link switch are ignored, and
  `_lastByLink` cache reads are allowed only when the stored signature still
  matches the current link/device endpoints. When opening a link without a
  usable cache, clear the Live/Dynamic panels to a loading state before the
  async refresh starts so stale rows from the previous link are not shown.
- **Debug ingest no-spam guard (2026-05-11):** The local agent debug collector
  at `127.0.0.1:7449` is optional and must not create browser console/network
  spam during telemetry auto-refresh. `topology-link-telemetry.js::agentDebugLog`
  probes once, mutes failed local ingest posts with exponential cooldown, logs a
  single warning per outage, and resets automatically after a successful probe
  so debug logging resumes when the collector is started later.
- **Selection toolbars while panning:** Device/link/text/shape toolbars must hide
  immediately when canvas panning starts, but the selected object stays selected.
  `beginCanvasPanInteraction()` also temporary-hides an active XRAY popup, and
  mouse-move defensively calls it on the first actual pan frame in case the pan
  began through a path that skipped mousedown setup. On mouse or keyboard pan
  release, restore the relevant toolbar through
  `restoreToolbarAfterCanvasPan()` so it is anchored to the object's new screen
  position. Do not require the user to click the object again after panning.
- **Multi-user cache:** Telemetry cache lives at
  `user_store.user_data_path(username, "link_telemetry_cache.sqlite")`, uses the
  shared `_open_db()` WAL + `busy_timeout=5000` pattern, and is safe to evict per
  user/device only.

### DNOS testing MCP verification — 2026-04-28

- **`~/dnos_config_mcp`** hosts the local `dnos-config` MCP service on `localhost:9300`.
  It exposes transactional config (`dnos_atomic_commit`, `dnos_multi_device_commit`),
  persistent reads (`dnos_run_show_commands`), device lookup, the `dnos_dnaas_*` DNAAS
  path-finding family, and **`dnos_agent_handoff`** for compact cross-agent/session
  handoffs (intent, next actions, evidence paths only; no transcripts). Handoffs persist
  under `~/.cursor/agent-handoffs/` (`DNOS_CONFIG_MCP_HANDOFF_DIR` overrides). Run
  `python3 ~/dnos_config_mcp/verify_handoff.py` to verify the handoff tool without lab devices;
  `python3 ~/dnos_config_mcp/verify_dynamic_handoff.py` exercises milestone-style saves (AGENT/TEST/SPIRENT/debug-dnos), generic `/AGENT` routed-command supervision, overload counter snapshots, `latest`/`resume_context`, and reruns the core verifier.
  **Dynamic workflow:** slash-command docs (`drivenets-topology-studio/.cursor/commands/*.md` and `~/.cursor/commands/*.md`) plus `memory-protocol.md` Section **2.4** tell agents **when** to call `save`/`append` (not background observers). `/AGENT` is the universal handoff supervisor: before routing/focusing any slash command, it checks `latest source_command=<command>` + `resume_context`, or seeds a command-scoped handoff if none exists. Same-chat dedupe is allowed after a resume, but an explicit user phrase like `resume latest`, `latest handoff`, or a specific handoff topic forces a fresh `latest` lookup. Keep `~/SCALER/TEST/active_test_session.json` as the live `/TEST` run pointer; MCP handoff is the cross-chat resume bundle. If Cursor's MCP descriptor cache is stale and `dnos_agent_handoff` is not visible, agents must use `python3 /home/dn/dnos_config_mcp/dnos_agent_handoff_cli.py` as the local fallback before loading heavy command context.
  After changing MCP code, `systemctl --user restart dnos-config-mcp` and confirm
  `curl -s http://localhost:9300/health` lists `dnos_agent_handoff`.
  Cursor's MCP UI rejects `tools/list` if optional `_meta` is present as
  `null`; omit `_meta` entirely unless it is a real object. A green
  `dnos-config` entry with "No tools, prompts, or resources" usually means
  Cursor connected but rejected discovery schema validation. Check
  `~/.cursor-server/data/logs/*/anysphere.cursor-mcp/MCP user-dnos-config.log`.
- **Cursor MCP registration:** `dnos-config` is registered both in user config
  (`~/.cursor/mcp.json`) and workspace config (`.cursor/mcp.json`). If descriptor files exist
  but agents still run `dnos_agent_handoff_cli.py`, the active Cursor runtime did not load the
  MCP server; reload the Cursor window or restart Cursor, then verify native tool availability.
  Native calls use server identifier `user-dnos-config` and the tool name from
  `mcps/user-dnos-config/tools/*.json`; reading a descriptor is only schema verification and
  must be followed by an actual MCP call. Agents should not shell out to Python
  `handle_tool_call(...)` for one-shot dnos-config reads/writes when the native MCP tool is
  visible. Python orchestrators may use the in-process dispatcher only for long-running loops
  that cannot access Cursor's native tool surface, and those loops must prefer aggregate MCP
  tools over hundreds of repeated per-service calls.
  Agents should trigger this automatically for normal continuation prompts (`continue`,
  `resume`, `handoff`, `last run`, `what failed`, `where were we`) when the prompt also names a
  slash command or known saved-work topic such as `AC<->PW`, `30 moves`, `EVPN VPLS SI`, or
  `MAC mobility`; users should not need to say `native MCP`.
- **Verification evidence:** `~/dnos_config_mcp/verification_2026-04-28.md` and
  `~/dnos_config_mcp/verification_2026-04-28.json` are the latest full-pass evidence.
  Buckets covered read-only DNAAS/path tools, single-device commit + rollback, PE-1 +
  RR-SA-2 all-or-nothing multi-device commit/revert, validate-fails-first behavior, and
  systemd service-down/restart recovery.
- **Known live lab finding:** `dnos_dnaas_diagnose(vlan=213)` currently returns
  `overall_verdict=fail` with `LINK_DOWN_STICKY`, while `vlan=214` returns `pass`.
  Treat VLAN 213 as a useful fault-shape test case, not as a healthy-path assumption.
- **DNAAS frame recipe canonical source:** `dnos_dnaas_teach_plan(vlan, dut, test_mac?)`
  returns the exact Spirent `frame_recipe` for DUT MAC teaching: encapsulation
  (`untagged`, `single-tagged`, `double-tagged`, or `unknown`), outer/inner VLAN,
  deterministic source MAC, `spirent_flags`, `ownership_tag`, `dut_target`, and
  `verification_plan.learn_commands`. `/SPIRENT`, `/debug-dnos` Phase 0g, and
  `/TEST` prerequisite gates must consume this output before creating traffic.
  `recipe_blockers != []` means stop as an infrastructure blocker instead of
  inventing VLAN/Q-in-Q flags from raw `bd_logic`.
- **DNAAS descriptions are metadata only (2026-05-03):** do not choose a BD, leaf AC,
  DUT AC, capture port, VLAN, or verdict from `Description:` strings. Live forwarding
  comes only from BD membership, interface `vlan_selector`, and `vlan-manipulation`.
  `dnos_dnaas_teach_plan.frame_recipe.selection_trace.description_used_for_selection`
  must be `false`, and `frame_recipe.landing_matrix.entries[]` is the canonical way to
  distinguish where single-tag versus Q-in-Q Spirent traffic lands (for example
  RR-SA-2 fabric 215: single-tag outer 215 -> `bundle-100.215`, Q-in-Q outer 215
  inner 3001 -> `bundle-100.2001`).
- **/TEST no-guessing contract (2026-05-03):** passed traffic tests must persist
  compact last-known-good evidence before future recipe generation reuses them:
  topology anchor, device/source roles, `dnos_dnaas_teach_plan` args/results,
  `frame_recipe.spirent_flags`, forbidden flags, validated DNOS show commands,
  verdict layers, and result paths. Future `/TEST CREATE` flows must start from
  that pattern but revalidate it live. A declared `mcp_dnaas_teach_plan`
  prerequisite is strict: MCP unavailable, malformed output, unresolved VLAN/AC,
  `recipe_blockers`, or failure to write `active_test_session.expected_traffic`
  is a prerequisite failure. Do not fall back to guessed Spirent VLANs, inner
  tags, ACs, or DNOS syntax.
- **/TEST DNAAS preflight scaling (2026-05-04):** large PW-scale recipes must not
  run full DNAAS path discovery once per service unless explicitly in exhaustive debug mode.
  Default gates use smart aggregate validation: validate each unique DUT/transport VLAN path
  with representative live `dnos_dnaas_spirent_preflight` calls, verify all expected inner
  VLANs through `dnos_dnaas_inner_vlan_plan`, and reserve `dnaas_preflight_mode=full` for
  root-cause debugging when one specific service needs byte-for-byte path evidence.
- **/TEST HA traffic-loss gate (updated 2026-05-04):** HA recipes that start
  Spirent traffic must poll `spirent_tool.py stats --json` during the HA event,
  not only before and after. Verdicts must compare aggregate `loss.frames`,
  `rx.dropped_frames`, and per-stream `dropped` deltas against the pre-event
  baseline, but EVPN-SI VPLS NCC switchover has a special scoring rule:
  `loss.frames` is TX total minus RX total and may show a recovered mid-window
  counter gap during the switchover grace/reconnect window. Mark traffic `FAIL`
  only if final post-convergence loss, `rx.dropped_frames`, per-stream dropped
  counters, unrecovered RX rate, or CP/DP state checks fail. If PWs and MACs
  recover and final loss delta is zero, classify the traffic layer as
  `PASS WITH WARNING` / `EXPECTED_TRANSIENT_DROP` and record the max transient
  delta.
- **/TEST HA switchover confirmation rule (2026-05-04):** Recipe-driven
  `request system ncc switchover` triggers must send `set cli-no-confirm` first.
  Otherwise DNOS can wait at the confirmation prompt while the local HA
  orchestrator appears hung and no switchover occurs. A read-only `show system`
  check must confirm the switchover actually happened before Spirent loss and
  PW/MAC recovery are interpreted.
- **PW scale service stepping (2026-05-03):** EVPN-SI VPLS scale recipes must
  generate every collision-sensitive service value from a global service index
  and validate the full matrix before rendering config. Inner VLANs must stay in
  the valid `1..4094` tag range; the SW-204115 PE-4/RR-SA-2 200-service recipe
  uses default inner VLANs `3101..3300`, RT/EVI/RD keyed by that inner VLAN,
  PE-4 site IDs `10001..10200`, RR-SA-2 site IDs `20001..20200`, and
  `label-block-size 8` with a unique per-service label-block ordinal/budget
  metadata. Do not reuse local loop indexes for service names, stream names,
  MACs, or ownership tags when `service_offset` is non-zero. Before bulk
  creation, scan live flattened config on both DUTs and abort if any generated
  service name or AC already exists for the requested `scale`/`service_offset`.
  For PW MAC teaching, route-targets must be generated only under
  `seamless-integration protocols bgp` as `export/import-l2vpn-vpls`; do not
  generate native `export/import-l2vpn-evpn` RTs for these scale services,
  because they advertise learned MACs as EVPN RT-2 instead of PW-learned MACs.
  MAC-learning verification for this recipe must reject `B>`/BGP remote MACs
  and pass only on source-qualified `v>` / VPLS PW evidence for remote learning.
  The prerequisite gate must also verify active bgp-vpls label capacity:
  `scale * label-block-size` labels are required per DUT. A pool of only
  `128`/`130` labels cannot support a 200-service run with `label-block-size 8`;
  that state produces local `L>` MACs only and empty VPLS PW tables.
  The same prerequisite gate must parse both `In use` and `Configured` rows in
  `show mpls label-allocation tables`: if `Configured` is large enough but
  `In use` remains smaller, or DNOS prints `Configured values differ from current
  in use values, restart system to apply new values`, block the run as
  `bgp_vpls_label_pool_restart_required` with SW-253359 remediation. A bgpd
  restart, routing-engine/container restart, NCC switchover, or single-NCC
  restart is not an accepted fix for this gate; require the documented full cold
  `request system restart` path and re-check `In use` after boot. The same gate
  must enforce the zero-pool bug check (`bgp-vpls: 0 labels, N/A`), standby HA
  readiness when HA is enabled, and DNAAS preflight for both PE-4 (`outer=219`)
  and RR-SA-2 (`Spirent outer=215`, DUT wire outer=4`). After config is
  committed, run DNAAS preflight again and require `READY` before creating any
  Spirent StreamBlock.
- **PW scale PW readiness verification (2026-05-04):** `show evpn vpls-pw`
  output is not a pass just because each service name is printed. The verifier
  must require every generated service to have a `VPLS PWs` row with `Status`
  `Installed` on both DUTs. A section that says `VPLS PW table is empty` is a
  hard prerequisite failure even when the EVI/AC is up and local MAC learning
  works; do not start HA on that state.
- **PW scale bgp-vpls label budget (2026-05-04):** EVPN-SI VPLS scale runs must
  budget two bgp-vpls label-block routes per service, not one. Live proof from
  `show bgp l2vpn vpls rd ...` shows each service exports local-site and
  remote-site offset routes; with `label-block-size 8`, 200 services need at
  least `200 * 8 * 2 = 3200` bgp-vpls labels per DUT, plus existing non-target
  SI services. A 2048-label pool can be active and still fail with bgpd traces
  such as `Failed to allocate label on BGP ... L2VPN VSI, abort export`, which
  leaves missing BGP L2VPN-VPLS prefixes and empty VPLS PW tables.
- **PW scale DNAAS preflight execution (2026-05-04):** full 200-service runs
  issue 400 `dnos_dnaas_spirent_preflight` checks. Because the dnos-config MCP
  dispatcher is imported in-process by this orchestrator, protect dispatch with
  a process-local lock and run checks in bounded batches. Keep heartbeat records
  in `progress.json`, `progress.jsonl`, and `EXECUTION_LOG.md` at batch/check
  boundaries so a stalled or killed run is visible before any config push. Do
  not run a separate `dnos_dnaas_diagnose(refresh=True)` for every acceptable
  `NEEDS_AC` result; reserve diagnosis for real blockers and accept direct
  `dut_target` AC readiness evidence for known DNAAS suffix mismatches. Before
  config is pushed, `NO_DUT_AC`, `INNER_VLAN_PIN_NOT_FOUND`, and
  `FABRIC_HOP_SUBIF_MISSING` may be downgraded to `NEEDS_AC`; after config,
  `READY` is still required. The DNAAS persistent cache writer must use unique
  per-process temporary files before atomic replace; a shared `.tmp` name races
  when Cursor MCP calls and in-process orchestrator calls overlap.
- **PW scale Spirent StreamBlock strategy (2026-05-04):** STC enforces a hard
  high-speed result-analysis limit of 64 StreamBlocks per port instance, so the
  SW-204115 200-service recipe must default to two aggregate L2 Q-in-Q
  StreamBlocks with synchronized `RangeModifier`s instead of one StreamBlock per
  service direction. PE-4 uses fixed outer VLAN 219 with inner VLAN and MAC
  ranges stepped across the service window; RR-SA-2 uses fixed Spirent outer VLAN
  215 with the same inner window and its own MAC ranges. Keep per-flow result
  tracking disabled by default (`EnableStream=FALSE`) and prove scale with DNOS
  MAC-table verification plus aggregate Spirent port loss counters. Preserve the
  old per-service stream mode only as an explicit debug fallback. The 2026-05-04
  `RUN_modifier_stream_200_PE4_RRSA2` proof passed with 2 StreamBlocks, 400
  logical flows, and 200/200 services MAC-learned on both sides.
- **PW scale mass MAC mobility phase (2026-05-04):** Before advanced HA restarts
  on the SW-204115 PW-scale recipe, use the controlled `mass_mobility` phase to
  invert MAC ownership with two additional aggregate modifier streams. RR-SA-2
  sends the PE-4 source MAC range `00:de:ad:01:00:01..00:de:ad:01:00:c8` on
  transport VLAN 215; PE-4 sends the RR-SA-2 source MAC range
  `00:de:be:01:00:01..00:de:be:01:00:c8` on transport VLAN 219. The reverse
  streams must use fresh unknown-unicast destination ranges
  `02:aa:fa:01:00:01..02:aa:fa:01:00:c8` and
  `02:aa:fb:01:00:01..02:aa:fb:01:00:c8`, deactivate the baseline streams, and
  pass only when source-qualified MAC-table evidence shows every moved MAC local
  on the opposite DUT and VPLS-PW remote on its original DUT.
- **PW scale repeated mobility before HA (2026-05-04):** For stress before HA,
  run `multi_mobility` instead of hand-toggling StreamBlocks. Each cycle flips
  the two baseline aggregate streams back to original ownership, verifies
  source-qualified baseline MAC state on both DUTs, then flips the two reverse
  aggregate streams back to moved ownership and verifies source-qualified moved
  MAC state. The phase intentionally ends in `moved`; follow-up HA must pass
  `--expected-mac-state moved`. Use `--ha-mode safe_no_bgp` for NCC switchover
  plus datapath container restart without intentionally restarting `routing:bgpd`.
- **DNOS command validation is docs OR live-pass evidence (2026-05-03):** CLI docs
  are the primary discovery source, but absence from `search_cli_docs` does not
  invalidate a command that has passed on a live DNOS device. Once a command runs
  successfully on a device, record it as live-validated for that DNOS version or
  lab image and keep using it for that version. For PW scale EVPN-SI testing,
  `show evpn vpls-pw`, `show evpn instance <name> detail`, `show evpn instance
  <name> vpls-pw`, `show bgp l2vpn vpls summary`, `show system alarms`, and
  `show config routing-options` are live-validated on PE-4 and RR-SA-2
  (2026-05-03, DNOS 19.2.13.x lab image) even though some searches return no
  CLI-doc hit.
- **/TEST operational no-more guard (2026-05-03):** `unset logging terminal`
  is valid DNOS operational syntax, but it fails if an automation wrapper
  appends `| no-more`. Keep `unset ` in `DNOSSession._CFG_PREFIXES` together
  with `set `, `clear `, `request `, and `run ` so operational cleanup
  commands are sent exactly as authored.
- **/TEST report status rendering (2026-05-03):** full-report renderers must
  preserve neutral verdicts (`SKIP`, `WARN`) instead of mapping every non-`PASS`
  layer to `FAIL`. Summary and full report output must agree so a skipped trace
  optimization does not look like a failed layer.
- **DNAAS freshness contract (2026-05-03):** every `dnos_dnaas_*` tool now
  accepts `caller_intent` and `freshness` arguments. The contract is:

  | Caller | Pass | Effect |
  |---|---|---|
  | `/TEST CREATE`/`RUN`, `/HA`, recipe-driven flows | `caller_intent="test_recipe"` | cache window expanded to 10min, prefer cache |
  | `/SPIRENT stream`/`l2`/`bgp`/`ecmp`/`dnaas` | `caller_intent="spirent_stream"` | path/teach/diagnose forced LIVE; bd_logic/find_path stay cached |
  | `/debug-dnos` deep diagnose | `caller_intent="diagnostic"` | always LIVE on every state-volatile tool |
  | (no caller_intent) | -- | default `prefer_cached`, 5min TTL (today's behavior) |

  Explicit `freshness="cached"|"prefer_cached"|"prefer_fresh"|"fresh"` always
  wins over `caller_intent`. `max_age_sec=N` overrides the TTL window. Legacy
  `refresh: true` still works (translates to `freshness="fresh"`).

  New tools introduced for the contract:

  - `dnos_dnaas_spirent_preflight(vlan, dut, inner_vlan?, test_mac?)` -- ONE
    call, <2s wall time, fresh DUT state, returns flat verdict `READY` /
    `NEEDS_AC` / `BLOCKED` plus `frame_recipe.spirent_flags`,
    `inner_vlan_plan` (live), `down_subifs`, `needs_ac_config` (suggested
    config + next step), and `verification_plan`. `/SPIRENT stream` PHASE 1.6
    uses this instead of chaining teach_plan + path + inner_vlan_plan
    manually.
  - `dnos_dnaas_cache_audit(dut?, vlan?, expected_duts?, expected_vlans?)` --
    operator visibility into the cache: every hot+cold key with age, TTL,
    freshness verdict (fresh / stale / very_stale), per-category roll-up,
    and a list of blind spots (DUT/VLAN combinations not yet cached). Use
    before a /SPIRENT or /TEST run to decide whether to force-refresh.

  Self-tests (`tests/test_rendering_smoke.py`): 58 PASS / 0 FAIL covering
  byte preservation, swap-aware hop chains, format=json/text/both, parallel
  4-call concurrency, freshness policy enforcement (test_recipe hits cache
  in <100ms, spirent_stream forces live), and spirent_preflight wall time
  <3s on warm hop topology.
- **DNAAS fast path before live diagnose:** for path discovery, start with cold-cache
  `dnos_dnaas_inverse_path`, `dnos_dnaas_find_path`, `dnos_dnaas_bd_logic`, or
  `dnos_dnaas_cross_bd_lookup`; reserve live `dnos_dnaas_diagnose` for one
  already-resolved path that needs oper/fault proof. Never sweep VLANs 210-219 with
  `diagnose`. Transport/fabric VLAN is derived from actual `vlan_selector` and
  `vlan-manipulation` push/pop config, not from bridge-domain names. For port-mode
  ACs such as PE-4 `ge100-18/0/1`, pass `fabric_vlan=211` explicitly to
  `dnos_dnaas_inverse_path`, then let `teach_plan` produce the untagged Spirent
  recipe (`--no-qinq`, no `--vlan`).
- **DNAAS fabric + DUT description walk MUST be cache-first (2026-04-30):** the
  per-host description sync used by `/SPIRENT mark-dnos` (both `--fabric-vlan`
  and `--dut`) and `/TEST` SPIRENT-SYNC reads each host's `interfaces` /
  `protocols bgp` config to compare expected description vs actual. The legacy
  implementation opened a paramiko SSH session per host (sequential ~5 minutes
  for fabric, plus an additional 30-90s for the DUT). The new path reads
  `~/SCALER/db/configs/<host>/running.txt` (refreshed every 5 minutes by
  `extract_configs.sh` cron) via `~/SCALER/SPIRENT/_dnaas_cache.py`. Wall times
  observed in production:

  | Path | Pre-fix | Cache hit | --no-cache (forced live SSH) |
  |---|---|---|---|
  | Fabric walk (5 hops) | ~5 min seq / ~10s parallel | 0.0s wall (in-process) | 10.2s |
  | DUT-side mark-dnos | 4-90s (variable; FortiGate-prone) | 1.3s | 3.2s |
  | /TEST SPIRENT-SYNC end-to-end | minutes (often WARN) | 2.6s PASS | 14.7s PASS |

  Plumbing layout:
    - `_dnaas_cache.py` exposes `get_subif_description(...)` (per-subif desc, used
      by fabric walk) and `get_dut_running_config(...)` (full DUT config blob,
      used by `_dnos_parse_subif_map` and `_dnos_parse_bgp_neighbors`).
    - `_dnos_parse_subif_map(cfg)` and `_dnos_parse_bgp_neighbors(cfg)` are
      now PURE parsers (no SSH). The legacy `_dnos_fetch_*` names remain as
      thin SSH wrappers for callers that already hold a live `DNOSSession`.
    - `cmd_mark_dnos` reads from cache when fresh (default 600s) and falls
      through to live SSH transparently on `cache:miss` / `cache:stale` /
      `--no-cache`. Same plumbing applied to `_mark_fabric_hops_plan`.
    - `spirent_sync.run_full_sync(no_cache=...)` propagates to both DUT and
      fabric branches; CLI flag `--no-cache` exposes it.
    - The same logic is exposed as MCP tool `dnos_dnaas_describe_path`
      (`max_age_seconds` default 600, accepts `no_cache=true`) so cross-agent
      callers (Cursor agents, /debug-dnos, /TEST harness) can request a
      fabric description walk without spawning Python.

  Freshness contract (Phase 4):
    - Default freshness window is **600 seconds** (10 min, 2 cron cycles)
      across spirent_tool, spirent_sync, and the MCP. A reading made just
      before a cron tick still wins.
    - Stale (> max_age) is auto-bypassed: caller falls through to live SSH
      without operator intervention.
    - `--no-cache` is for the rare case where /TEST or /SPIRENT just pushed
      config and needs a same-second re-read before the next monitor tick.
      You do NOT need it for stale or missing-cache cases.

  Banner format in /TEST log:
    - `[sync_descriptions_fabric(v214)] PASS -- already in sync (5c/0s read)`
       fabric walk; `Nc/Ms read` = cache-hits / ssh-fallbacks
    - `[sync_descriptions_dut(YOR_PE-1)] PASS -- already in sync` -- DUT-side
       no longer prints WARN paramiko TimeoutError when FortiGate IDS
       quarantines management; the cache-first read avoids the round-trip.

  STC handle leak fix (companion change, 2026-04-30): `cmd_remove_stream` no
  longer aborts with `sys.exit(1)` when STC reports `invalid handle ... should
  have been obtained using create or get`. That happens whenever the Lab Server
  BLL session was rotated since the local `dn_spirent_main.json` was written.
  We now treat that response as "STC already does not have this stream" and
  still scrub the local JSON record (with an audit-log entry). This unblocks
  /TEST PREFLIGHT smoke tests when a prior crashed run left a stream with a
  stale handle in the session JSON.
- **DNAAS fault-first workflow:** When traffic is sent by Spirent but no packets reach
  the DUT, call `dnos_dnaas_diagnose(vlan=<transport>, dut=<DUT>, refresh=true)` first.
  The `dut` argument is mandatory for non-PE-1 paths (for example `dut=PE-4` scopes the
  chain to B-14 -> B-09 -> B-10). Read `fault_summary.first_blocking_hop`,
  `failed_hops`, `dut_validation`, and `root_cause` before requesting
  `dnos_dnaas_stabilize_plan`. `dut_validation` checks the DUT receiver side by
  matching the transport VLAN against DUT `vlan-id`, `vlan-tags outer-tag`, or
  `match-criteria outer-vlan` config, then reading `show interfaces` for those
  candidate interfaces. A fabric path can be clean while `dut_validation.verdict=fail`;
  fix that DUT sub-interface/service state before treating the failure as a DNAAS
  fabric fault or a DNOS protocol bug. Stabilize plans should be generated with the
  same `dut` argument and remain user-approved only; the MCP never commits DNAAS
  fixes by itself.
- **Operational rule:** For `/TEST` and `/SPIRENT`, use `dnos_dnaas_path`,
  `dnos_dnaas_inverse_path`, `dnos_dnaas_inner_vlan_plan`, `dnos_dnaas_bd_logic`,
  `dnos_dnaas_find_path`, and `dnos_dnaas_explain_mismatch` for DNAAS discovery instead
  of re-walking leaves with ad-hoc paramiko. Bridge-domain names are labels only; forwarding
  comes from parsed BD member interfaces, VLAN selectors, port-mode, and VLAN manipulation.
  Before creating Spirent streams, use the logic/explain tools to catch mismatches such as
  Q-in-Q 219/4001 requested while the live path is port-mode fabric 211. Use
  `dnos_dnaas_stabilize_plan` only to produce a user-approved plan; actual commits must go
  through `dnos_multi_device_commit`.
- **`/TEST` EVPN MAC mobility DNAAS gate:** The
  `evpn_mac_mobility_SW204115` suite's `spirent_sync.py` must call
  `dnos_dnaas_diagnose(vlan, dut, refresh=true)` for fabric health and
  `dnos_dnaas_teach_plan(vlan, dut, test_mac?)` for Spirent frame recipe / ownership-tag
  correlation; it must pass the DUT name, not only the management IP, so MCP can select
  the correct path. The legacy
  `spirent_tool.py dnaas-fix` path is not allowed as an automatic prerequisite fix; failed
  MCP diagnoses are infrastructure blockers until a user-approved `dnos_dnaas_clear_llp`
  or `dnos_dnaas_stabilize_plan` flow resolves them. Description tagging may still use the
  management IP through `spirent_tool.py mark-dnos`.
- **`/TEST` MCP observability:** When a Python test runner calls dnos-config through a CLI
  fallback (for example `~/.cursor/tools/dnos_mcp.py`), the runner must print the exact
  `[MCP-CALL] <tool> <args>` and `[MCP-RESULT]` lines. Otherwise Cursor will not show native
  MCP tool cards, and the operator cannot tell that `dnos_dnaas_*` gates really executed.
- **`/TEST` DNOS show-command enforcement:** A DNOS show command that returns `ERROR:`,
  `Unknown word`, or `Incomplete command` is a test infrastructure failure, not an empty
  route/table verdict. For EVPN RT-2 checks, use live-validated BGP evidence:
  `show bgp l2vpn evpn route-type 2 | include <mac>` plus peer
  `advertised-routes` for local-owner proof or `received-routes` / `routes` for remote-owner
  proof. Do not use `show bgp l2vpn evpn mac-address <mac>` or
  `show bgp l2vpn evpn route mac-address <mac>`; PE-1 rejected both on 2026-04-30.
  Also do not use bare `show bridge-domain instance`; it is incomplete on PE-1. Use
  `show bridge-domain summary` for global BD status, or `show bridge-domain instance all`
  / `show bridge-domain instance <bd-name>` when a concrete BD exists.
- **`/TEST` pre-DUT command guard (2026-05-01):** The EVPN MAC mobility suite must route
  every DUT-facing command through `shared.command_guard` at the `device_runner.run_show`
  choke point before MCP/SSH. The guard blocks unresolved recipe placeholders (for example
  `{evpn_name}`), bare `show config protocols bgp`, trace forms like
  `show file traces ... last 50`, and invalid cleanup such as `no set logging terminal`.
  DNOS pipe limits are `| leading <N>` and `| trailing <N>`; never generate Linux-style
  `| head <N>` or `| tail <N>` in recipes, debug hints, trace collectors, or learned
  command suggestions.
  Recipe pre-validation must treat these as `orchestrator_bug` blockers and refuse
  `--execute`; the command must not reach DNOS and must not appear as a DNOS rejection.
  Generic engines must render recipe parameters before running counters or config baselines:
  counter commands use the scenario `sub_params`, BGP config baseline sections use
  `protocols bgp {asn}`, and terminal logging cleanup uses `unset logging terminal`.
- **`dnos-config` read-session behavior:** `dnos_run_show_commands` must reuse a cached
  `DNOSSession` per device/user for read-only show commands. Opening a fresh SSH session
  per command caused intermittent PE-1 `TimeoutError` on valid commands such as
  `show system` and `show evpn summary`, while subsequent commands succeeded. Treat
  MCP transport timeouts as infrastructure failures, not DNOS syntax failures; do not
  fall back to raw SSH silently when MCP is healthy.
- **`/TEST` scenario_runner trigger error-handling:** When the trigger executor runs an
  HA / clear / config CLI command on the device, the resulting `trigger` verdict layer
  MUST flip to FAIL when the device output contains `ERROR:`, `Unknown word`,
  `Incomplete command`, or `Invalid input`. Returning unconditional PASS for the trigger
  layer turned syntactically broken HA / clear scenarios into false-positive runs (fixed
  on 2026-04-30 in `orchestration/scenario_runner.py` for the `ha_cli_command`,
  `ha_command`, and `clear_command` branches; `_show_command_error()` is the
  source-of-truth detector). Any new trigger branch added later MUST run the same
  detector before returning a PASS verdict.
- **`/TEST` recipe lint loader (`tools/lint_recipes.py`):** The `ACTION_TRIGGER_MAP`
  source-of-truth lives in `orchestration/constants.py` since the 2026-04 split. The
  linter MUST source-parse that file first and only fall back to the legacy
  `mac_mobility_orchestrator.py` location for backward compatibility. Without this fix
  the linter silently warns "could not extract ACTION_TRIGGER_MAP keys" and skips
  trigger.action validation across the entire suite, masking SKIPped scenarios.
- **`/TEST` ac_ac trigger mappings:** `sanction_ac_ac_rapid_flap` -> `spirent_sanction_flap`,
  `subsecond_rapid_flap_ac_ac` -> `rapid_flap`, `sh_sh_coverage_flap` -> `rapid_flap`,
  `clear_with_assertion` -> `clear_command` are all aliases that route to existing
  handlers. `admin_flap_during_move` (ac_ac SC10) and the `setup_trigger` /
  `poll_convergence` phase keys (clear_operations / scale_64k) remain unimplemented and
  must be wired up or the affected scenarios marked `experimental` before they can
  produce trustworthy verdicts.
- **`/TEST` EVPN MAC mobility port-mode traffic:** For port-mode ACs, the scenario trigger
  and `shared.mac_trigger.spirent_create_l2_stream()` must omit `--vlan` entirely and send
  `--no-qinq` untagged L2 frames. `dnos_dnaas_teach_plan.frame_recipe.encapsulation=untagged`
  is not "single-tagged fabric VLAN"; using `--vlan <fabric_vlan>` is an orchestrator bug.
  The trigger layer must fail if the smoke MAC is not learned within `smoke_poll_timeout_sec`
  instead of reporting PASS with a zero-second poll.
- **`/TEST` EVPN MAC mobility teach-plan contract:** The prerequisite engine must enforce
  `mcp_dnaas_teach_plan.pass_when` for frame encapsulation, not just `recipe_blockers == []`.
  As of 2026-05-02 the live MCP truth for `basic_learning` is PE-4/L = untagged fabric 211,
  PE-1/B = Q-in-Q 214/4001, RR-SA-2/v = Q-in-Q 215/3001 to `bundle-100.2001`
  (DUT wire outer 4 / inner 3001 after DNAAS swap). For port-mode DUT receivers,
  still synthesize traffic from the Spirent-ingress DNAAS endpoint selector; a tagged
  ingress endpoint means Spirent must send the selector tag even if a different DUT
  side appears untagged.
- **`/TEST` cross-layer checks are read-only:** `shared.cross_layer_check.SHOW_COMMAND_MATRIX`
  may document `RESET_*` cleanup commands for other flows, but `collect_all_layers()` must
  skip every `RESET_*` entry. Running cleanup during cross-layer verification erases the
  learned MAC and invalidates counter windows.
- **`/TEST` stateful MAC source suites:** For `basic_learning`, SC04 is only meaningful if
  SC01/SC02/SC03 source MACs coexist. Use full MAC-table cleanup only for the first scenario;
  subsequent scenarios must use per-test-MAC cleanup (`clear evpn mac-table instance <EVI> mac <MAC>`)
  so earlier source evidence remains present for SC04.
- **`/TEST` AC<->PW move suites:** For real mobility tests such as
  `TEST_mac_mob_ac_pw_single_move_SW205198`, the move scenario must preserve the previous
  MAC source before triggering the next source (`cleanup_scope="preserve"`). Clearing the
  MAC first turns the case into fresh learning and invalidates Local->PW / PW->Local proof.
- **`/TEST` trace notification gates:** BGP NOTIFICATION checks must be scoped to the current
  run timestamp and current date. A raw `show file traces ... | include NOTIFICATION` scans
  days of historical lab noise and creates false failures. When a scenario validates a specific
  EVPN/VPLS service, filter notifications to the relevant BGP neighbors; unrelated lab peers
  such as ExaBGP default-neighbor noise must not fail an EVPN MAC mobility verdict. If a
  neighbor allow-list is present, a NOTIFICATION line without an explicit matching neighbor
  is not verdict evidence for that service.
- **DNAAS LLP clear syntax:** Live B-10 validation on 2026-04-29 showed the correct inspect
  command is `show bridge-domain loop-prevention instance <exact-bd-name>`, while the
  targeted recovery clears are `clear bridge-domain instance <exact-bd-name> ac-suppression`,
  `ac-history`, and `ac-restore-cycles`. Do not suggest `clear bridge-domain loop-prevention ...`
  because that form is invalid on this DNAAS build. Do not suggest broad
  `clear bridge-domain ac-suppression` for targeted recovery. Always use the exact BD service
  name from live output, for example `g_yor_v211_STC-TO-CL_port-mode`, not a shortened
  VLAN-derived name.
- **DNAAS LLP recovery MCP:** User-approved "fix the BD" requests must use
  `dnos_dnaas_clear_llp`, not ad-hoc local SSH. The tool requires `confirm=true` unless
  `dry_run=true`, resolves the exact down BD member from `vlan+dut` diagnose or explicit
  `hostname+bd_name`, runs only scoped operator clears, verifies
  `show bridge-domain loop-prevention instance <bd> interface <if>` plus
  `show bridge-domain instance <bd>`, waits for stability by default, and reports
  `fixed`, `still_down`, or `retriggered_by_active_loop` with LLP MAC-move evidence.
  It must never disable LLP or change config; use a separate approved stabilize/commit
  flow for LLP tuning or disable.
- **DNAAS BD member state rule:** For DNAAS path health, `show bridge-domain instance <bd>`
  is the service-level truth for local AC forwarding. If its member table shows an AC such as
  `ge100-0/0/4` as `Down`, treat the underlay as failed even if `show interfaces` is flapping
  or only contains historical last-down reasons. `dnos_dnaas_diagnose` must parse this table
  and return `BD_MEMBER_DOWN` before `/TEST` runs DUT MAC mobility assertions.
- **Bug-first testing rule:** Once `/TEST` has proven traffic infrastructure is correct
  (Spirent isolation, DNAAS path, DUT service state, source-qualified verifier, and
  validated DNOS syntax), any remaining DNOS-facing assertion failure is a bug candidate.
  Stop the scenario/move loop and invoke `/debug-dnos` before proposing any workaround,
  clear command, state flush, timer extension, retry loop, or alternate assertion. A workaround
  may be used only after `/debug-dnos` captures evidence and writes/updates a `BUG_*.md` file,
  and it must be labeled debug-only, operator-approved, or spec-approved.
- **`/debug-dnos` trace execution rule:** Read-only trace searches (`show file ... | include ...`,
  `show evpn ...`, `show bgp ...`) should run through Network Mapper `run_show_command` /
  `run_show_commands` in parent-agent batches. Enable required DNOS debug flags before the clean
  reproduction only through validated config/execute paths with user approval, then collect trace
  files via Network Mapper and clean up debug config before concluding.

### AI Clarify Router (topology preflight) — 2026-04-28

- **`POST /api/ai/chat`** (`serve.py::_handle_ai_chat`): After DNOS grounded-intent handling and **before** the LLM call, `_ai_topology_preflight_handle` may short-circuit:
  - **Broad new-topology asks** (e.g. “generate a BGP topology” with no scale/style) → immediate `ask_user_question` tool card (`stop_reason: topology_clarify_preflight`). Chips use human-readable **kind** values where possible; **instant standard labs** use values prefixed with `__AI_TOPO__/default/<family>` (e.g. `__AI_TOPO__/default/bgp`).
  - **Instant defaults**: That prefix loads a fixed blueprint from `topology/ai/blueprints/` via `load_blueprint` → `create_topology` **`pending_placement`** (`stop_reason: preflight_instant_blueprint`) — no Gemini round-trip.
  - **Specific prompts** (counts, RR/mesh/transit wording, AS numbers, etc.) skip preflight and use the existing tool-calling path.
- **Blueprints wired for instant defaults:** `bgp` → `ibgp-rr-hub-spoke-6`, `evpn` → `2spine-4leaf-anycast-gw`, `mpls` → `2pe-1ce-basic`, `ospf` → `single-area-5`, `isis` → `pure-l2-backbone`, `clos` → `3stage-2x4`.
- **Frontend** (`topology-ai.js`): Loading bubble starts with **“Checking topology intent…”** then swaps to the provider-specific label (~650ms) so fast preflight turns still feel responsive.
- **Shared-in toolbar hint** (`topology-file-ops.js` + `styles.css`): “Open a file below” / “Shared by …” use class **`ta-shared-toolbar-hint`** (no inline `color`) so **`body.dark-mode`** toggles pick up **`rgba(248, 250, 252, 0.9)`** in dark mode instead of a frozen light-theme gray.
- **Manage Topology Domains panel** (`showManageSections`): Under **`body.ui-skin-v2`**, chrome darkness follows **`editor.darkMode` / `body.dark-mode`** via **`_topologyChromeDark`** (not **`_menuDark`** inversion). **`panel._msThemeRefresh`** re-runs full render on theme change (`toggleTheme` → **`_refreshManageSectionsForTheme`**, and **`_updateDropdownTheme`** when the Topologies dropdown path runs).
- **Activity Log / notification center** (`topology-notifications.js`): Injected **`#notif-center-styles`** rules are scoped with **`body.dark-mode` / `body:not(.dark-mode)`** so tabs/inputs/logs track theme after the first open. **`restyleOpenCenter()`** runs from **`toggleTheme`** to refresh the panel shell and re-render the active tab when the center is open.
- **Shared-in hint contrast** (`styles.css`): **`.ta-shared-toolbar-hint`** uses explicit **`rgba(15,23,42,0.72)`** in light mode and near-white in dark under **`.domain-body`** so it stays legible on white expanded bodies.
- **Shared-with-me inbox default** (`topology-file-ops.js` `renderVirtualRow`): The synthetic inbox row starts **expanded** (`_domainCollapsed` **false** on first paint). Named shared-in domains still default collapsed. Otherwise v2.3 CSS hides **`.domain-body`** until the user clicks the header, so **“Open a file below”** never appears.
- **Model schema** (`ai/context.py` `ASK_USER_QUESTION_TOOL_SCHEMA`): Description reminds the model to use clarifying chips for vague **new topology** asks, not only destructive/disambiguation cases.

### Toolbar UI skin v2 (`body.ui-skin-v2`) — preservation contract — 2026-04-28

Visual reskin rules live **only** under `body.ui-skin-v2` in `styles.css` (append block). Do **not** remove or rename toolbar IDs, inline `onclick` hooks, or state classes used by JS/CSS.

**Structural IDs (event wiring / DOM queries):** `btn-topologies`, `btn-clear-top`, `btn-shortcuts-top`, `btn-link-type-labels`, `btn-dnaas`, `btn-network-mapper`, `btn-refresh-page`, `btn-theme-toggle`, `left-toolbar`, `toolbar-toggle`, `top-bar-toggle`, `device-styles-box`, `topologies-dropdown-menu`, `minimap-container`, `minimap-canvas`, `minimap-zoom-*`, `topo-bottom-left-bar`, `topo-active-indicator`, `grid-controls`, and every `*-tool-section` / section container the toolbar uses.

**Inline behavior hooks in `index.html`:** `activateToolSection(...)`, `toggleToolbarSection(...)`, refresh/theme handlers on their buttons — must stay on the same elements.

**Classes / state selectors:** `top-bar`, `toolbar`, `collapsed`, `expanded`, `active`, `topologies-open`, `dnaas-panel-open`, `dnaas-loading`, `dnaas-complete`, `dnaas-error`, `toolbar-section`, `toolbar-section-header`, `toolbar-section-content`, `tool-section`, `fixed-section`, `style-btn`, `style-label`, `top-bar-btn`, `cloud-glass-btn`, `liquid-glass-dropdown`, `sub-option-box`, `toolbar-collapsed`, `top-bar-collapsed`, `top-bar-collapsed` on body, etc.

**JS owners (do not rewrite for skin):** `topology-toolbar-setup.js` (delegation `.style-btn`, XRAY, sections), `topology-file-ops.js` (Topologies dropdown), `topology-dnaas*.js` (DNAAS panel classes), `scaler-gui*.js` / `scaler-api.js` (CONFIG/Generate).

**Adding/changing skin:** Prefer new rules under `body.ui-skin-v2 …` with explicit parents; avoid global `button { }` or unscoped `.style-btn` overrides.

**2026-04-28 v2.2 refinement:** The toolbar skin should stay smooth and frosted, not a heavy black command rail. Use soft translucent surfaces, calm shadows, readable light-mode text, and restrained accent fills. Light-mode Topologies domain rows should keep per-domain colour as the left accent and icon colour, not as low-contrast text/background wash. Active rows (for example blue `AI`) must render with white title/count text under `body.ui-skin-v2:not(.dark-mode) #topologies-dropdown-menu ...`.

**2026-04-28 v2.3 Editorial Light (current):** Replaces the v2.0 + v2.2 frosted look with a crisp Editorial-Light feel that mirrors exactly between light and dark mode. Rules live at the end of `styles.css` under `body.ui-skin-v2 ... /* UI Skin v2.3 */`. Key invariants:
- **Solid bar backgrounds, NO blur on bars/rails.** Bars use `--skin-v23-bar-bg` (white in light, deep slate `#0f172a` in dark). Crisp `1.5px` borders. Calm soft shadows only.
- **Bolder typography:** chip buttons `font-weight: 700`, brand wordmark + section headers `font-weight: 800`, section labels uppercase + 0.06em tracking.
- **Active section state:** `2.5px` solid blue (`#2563eb`) left strip on `body.ui-skin-v2 .toolbar-section.expanded > .toolbar-section-header` with very-soft blue tint background `--skin-v23-card-active`.
- **Accent action buttons keep gradients:** `#btn-dnaas` orange gradient `#FF5E1F → #FF8E4C`, `#btn-network-mapper` blue→cyan gradient `#2563EB → #14B8D4`, both with `font-weight: 800` and bright white text/SVG.
- **Topologies cloud-glass-btn (`#btn-topologies`):** keeps existing 3-puff cloud silhouette + the layered `<svg id="topo-btn-icon">` exactly as built. JS-driven icon swaps (`_updateTopoBtnIcon`) must keep working — never touch the SVG markup from CSS.
- **CONFIG cloud (`#btn-scaler-config`) stays WHITE in BOTH light AND dark mode.** The 5 puffs + cloud-base are forced to white/`#1e3a5f` text via `body.ui-skin-v2 #btn-scaler-config .cloud-puff` and `... .cloud-base` rules. Dark mode only changes the drop-shadow (no colour change). This is intentional per spec.
- **Dropdowns + floating panels (Topologies / DNAAS / Network Mapper / Minimap / HUD / topo-active-bar):** plain `#ffffff` in light, `#131c2e` in dark, same `1.5px` border + soft shadow, no blur.
- **Domain row chrome from v2.2 stays intact** — per-row `--row-accent` + 4px coloured left strip + readable dark/bright title text + active row gradient with white text. v2.3 must not override `.custom-section-category` styles.
- **v2.3.1 contrast repair:** Added a follow-up scoped layer because v2.3 only styled the outer cards and several older rules still controlled inner `h3`, `.section-icon`, `.toolbar-section-chevron`, `.tool-btn::before`, `.tool-btn::after`, disabled button opacity, theme-toggle internals, and Topologies dropdown action buttons. Do not remove this layer unless replacing those inner selectors explicitly.
- **v2.3.2 expanded domain body readability:** Active/accent colour must not paint the entire expanded Topologies domain body. Keep accent on the domain left strip, icon, count badge, and active header only; `.domain-body`, `.domain-actions`, `.domain-topos-list`, `.domain-topo-row`, `.topo-entry-name`, `.topo-time`, and `.ta-btn` must use neutral light/dark readable surfaces and explicit text colours.
- **v2.3.3 all-domain headers + smooth switching:** Every Topologies domain header gets the same colored readable treatment, not only `.is-active`. Accent colour is applied to `.custom-section-category > .domain-title` with white text/icons/counts; `.is-active` only adds a stronger focus ring. Light/dark switching should transition on chrome surfaces (`top-bar`, `toolbar`, dropdown rows, HUD, minimap, theme toggle) using `--skin-v233-theme-ease`; do not apply these transitions to canvas objects.
- **v2.3.4 open Topologies transition + active topology colour:** When the Topologies dropdown is open during light/dark switching, mode-changing surfaces must animate via `background-color` / `border-color` / `box-shadow`, not gradient `background` images. The v2.3.4 layer sets `background-image: none` on neutral dropdown surfaces and keeps domain headers colourful with filter/box-shadow transitions. `topology-file-ops.js:updateTopologyIndicator()` sets `--topo-active-domain-color` on the bottom-left active topology indicator; CSS uses it for `#topo-active-inner` and `#topo-active-domain` so the current topology pill follows the current domain colour.
- **v2.3.5 stable Topologies panel + option buttons:** `_fitDropdownToContent()` must grow the Topologies panel while open but not shrink it on every domain expand/collapse (`dropdown.dataset.stableWidth`). `_updateDropdownTheme()` must not repaint inline colours under `body.ui-skin-v2`; it only clears stale inline colour/background/border styles and lets CSS variables drive the transition. The v2.3.5 CSS layer gives Save/Load/Share and per-topology action buttons explicit `background-color`, `color`, and `border-color` rules so they flip reliably between modes.
- **v2.3.6 manual reorder restore:** Topologies dropdown domain rows must render in persisted manual `_customSections` order, not hue-sorted copies. Hidden/virtual rows (`__ai`, shared-in sections) must not make `/api/sections/reorder` abort; preserve them after rendered rows when saving. Per-domain topology row order is now saved per user through `/api/sections/<sid>/topologies/reorder` into the authenticated user's sections workspace, and move-to-domain can include a `target_order` based on the visible drop ghost. Drag feedback uses `.is-dragging`, `.is-drag-target`, and `.drop-ghost` scoped under `body.ui-skin-v2`.
- **v2.3.7 smooth theme + Topologies toggle:** Topologies dropdown open/close is stateful now (`.is-preparing`, `.is-opening`, `.is-open`, `.is-closing`). `_toggleTopologiesFromIndicator()` must measure/fit/place while hidden, then reveal on the next frame; do not set `display:block` visibly before `_fitDropdownToContent()` and `_placeTopologiesDropdown()` run. Light/dark transitions use `--skin-v237-theme-ease` and should animate paint-only properties; avoid animating width/height/top/left for dropdown theme changes.
- **v2.3.8 expanded-domain no-flap:** Opening Topologies must not rebuild visible expanded domain rows while the panel is revealing. `_toggleTopologiesFromIndicator()` increments `_suspendDropdownRefresh` around the open-time `_refreshSharingCache(true)` and the global `topology-domains:changed` listener must skip `.is-preparing`, `.is-opening`, and `.is-closing` dropdowns. CSS freezes `.domain-body` / `.domain-topos-list` transitions during those states.
- **v2.3.9 domain share open fix:** Domain-level Share buttons must prepare the legacy section before opening the inline share form. `topology-file-ops.js` mirrors each legacy topology into the multi-user domain DB, registers the mirror mapping, and suspends dropdown refresh while the clicked row is still live. `topology-share.js` also suspends refresh during its pre-open `_refreshAll()` pass and re-finds the row if a stale anchor was detached, so the form cannot mount into an invisible orphan subtree.
- **v2.3.10 active-topology pill placement:** The bottom-left active-topology pill is only a shortcut trigger for the Topologies dropdown. `_toggleTopologiesFromIndicator()` must position the dropdown from `#btn-topologies`, not from `#topo-active-inner`; anchoring to the bottom HUD makes the full panel float mid-canvas and cover the topology.
- **v2.3.11 smooth reorder drag:** Domain reorder must feel immediate: `_renderCustomSectionsInDropdown()` measures the current layout at drag start, collapses expanded domain bodies in parallel, then refreshes compact slot measurements without delaying the grab. Topology file drag uses `.is-topo-row-dragging`, `.is-drag-source-body`, and `.is-drag-source` to release dropdown/list overflow with `!important`, so a row stays visible when dragged out of its source domain. Keep drag feedback class-driven and scoped under `body.ui-skin-v2`.
- **v2.3.12 pill/share/transition polish:** The active topology indicator is text-first and theme-aware under CSS: neutral light/dark pill surface, `#topo-active-domain` as the domain-coloured text chip, no visible colour-dot in `body.ui-skin-v2`. `topology-file-ops.js:updateTopologyIndicator()` must clear legacy inline `background` / `border-color` when `body.ui-skin-v2` is active so theme transitions are CSS-driven. Topology row share actions (`.ta-share`, `.ta-unshare-all`, `.ta-remove-mine`) must override generic `.ta-btn` muted colour with a high-contrast light/dark share palette. Reorder slot transitions are intentionally short (roughly 170-190ms) to keep alignment responsive.
- **v2.3.13 smooth theme switching:** `topology.js::toggleTheme()` adds `body.theme-transitioning` for ~460ms around dark/light flips, defers noncritical BD/minimap/dropdown repaint work by two animation frames, and must not rebuild the closed Topologies dropdown during the toggle. `topology-file-ops.js::_updateDropdownTheme()` must clear stale inline paint without removing CSS transitions. The v2.3.13 CSS layer limits theme-switch animation to paint properties (`background-color`, `color`, `border-color`, `box-shadow`, `opacity`) on UI chrome so filter/layout/transform work does not make the mode flip look laggy.
- **v2.3.14 left toolbar toggle orientation:** The left toolbar collapse handle sits on the toolbar's right edge, so `body.ui-skin-v2 .toolbar-toggle` must keep its flat edge on the left (`border-left: none`) and rounded corners on the canvas side (`border-radius: 0 12px 12px 0`). Do not reuse right-side drawer handle geometry here; it makes the hide control look flipped.
- **v2.3.15 active topology pill refinement:** Keep `.topo-active-bar` itself transparent and style only `#topo-active-inner` as the visible capsule. The refined order is domain chip -> topology name -> save action, with `#topo-active-sep` hidden. The domain chip stays uppercase and domain-coloured, the topology name remains the main readable text, and the save button is a trailing affordance so the pill reads as one compact current-topology control.
- **v2.3.16 shared-with badge contrast:** Topology row shared-out badges (`.topo-shared-badge .dd-shared-out`) are generated with inline colours, so CSS must override them with `!important` under `body.ui-skin-v2`: white in `body.dark-mode`, dark navy in light mode. Keep this scoped to `.domain-topo-row` so domain header shared badges can keep their existing accent treatment.
- **Index script integrity:** Every `<script defer src="...">` entry in `index.html` must include an explicit closing `</script>`. A missing close tag after `topology-file-ops.js` prevents the later core scripts from loading normally and makes the app appear to hang during startup.
- **Logs strip / toolbar rail** (`styles.css`): Under **`body.ui-skin-v2`**, **`#toolbar-notification-section`** uses solid **`--skin-v23-rail-bg`** (no legacy blue gradient). **Negative side margins** on **`.toolbar > #toolbar-notification-section`** are reset to **0** so the row uses the same horizontal inset as other toolbar sections (legacy full-bleed made it look like a separate band). Inner **`.toolbar-section-content`** stays transparent with **`margin: 0 6px 6px`** to line up with **`body.ui-skin-v2 .toolbar-section-content`**; **`padding-top: 0`** overrides the inline spacer on the wrapper.
- **Auth user pill (light + v2.3)** (`styles.css`): **`body.ui-skin-v2:not(.dark-mode) .auth-user-pill`** uses the same **card / border / shadow** language as top-bar chips (**`--skin-v23-*`**), **no backdrop blur** (removes odd tint hairlines). **`.auth-user-pill__halo`** is a **neutral slate** wash instead of saturated **`data-palette`** colours; **`.auth-role-badge`** uses **muted** fills (engineer → indigo, not **`#00d4ff`** on cyan).
- **Generate Topology DNAAS boundary** (`index.html` + `topology-generator.js`): The **Generate** panel is for current/inserted DUTs, live running-config/LLDP, current canvas cleanup, Network Mapper exports, and pasted configs. DNAAS topology mapping stays in the **DNAAS** button/panel. Do **not** expose a DNAAS tab or “merge DNAAS” option under Generate; `_collectLiveTargets()` skips DNAAS/fabric-named canvas devices, and import rejects DNAAS discovery exports with a warning. Canvas auto-detect is intentionally strict: selected/auto-included canvas devices require a real SSH target from `sshConfig.host`, `hostBackup`, verified SN host, or active NCC host; label/serial/id alone must not become a Generate DUT target.
- **Generate Topology clean DUT architecture** (`topology-generator.js`): Live generation must not materialize unknown LLDP neighbors as canvas devices. LLDP is evidence for physical links only when both ends are already SSH-backed DUT targets. After live context collection, prune facts to non-DNAAS devices with real SSH targets before links/groups are built. Service/routing overlays should be compacted per device-pair/layer/linkType so multiple route-target or VRF matches become one readable architecture label instead of many parallel hairball links.
- **Generate Topology empty-SSH guard + groups** (`topology-generator.js`): No live Generate path may call `/api/topology-generator/device-facts` with an empty `ssh_host`. `_generateFromLive()` filters unresolved live targets after `/resolve-targets`, and `adapterLive()` skips any remaining target without an SSH host before creating the request URL. Generated links, attached TBs, and grouping shapes carry `_generatedGroupIds`, `_generatedLayer`, `_generatedProtocol`, and `_generatedTopologyObject`, and `metadata.generatedProtocolGroups` lists those groups so the next BD-style visibility panel can toggle whole protocol/layer groups.
- **Generate Topology protocol correlation** (`topology-generator.js` + `routes/topology_generator_correlate.py`): Live generation indexes **loopback0**, **router-id**, and interface/subinterface IPs so BGP neighbor IPs resolve to DUTs, emits **iBGP/eBGP** overlays, LLDP-backed physical logicals when no native link exists, and **VRF/BD/RT** intersections as **`facts.services`** (not RT-as-links). The FastAPI **`/api/topology-generator/correlate`** path mirrors this in SQLite for one request lifetime; saved previews carry **`metadata.correlationEvidence`** / **`metadata.correlationLayout`** when present. The in-browser **`composeArchitectureFacts`** path remains the **offline fallback** if the correlate API fails. Generated links carry **`layer: physical | routing | service`**, **`linkType`**, protocol labels, and style hints. Do not regress this back to “same ASN only”.
- **Generate Topology native canvas overlays** (`topology-generator.js`): Generated logical overlays must use existing canvas primitives, not side-channel metadata. Keep multiple logical links between the same device pair distinct by including **layer/linkType/protocol** in de-dupe keys. Routing/service overlays use **manual curved links** plus a native **middle attached TB** (`linkId`, `position: "middle"`, `linkAttachT: 0.5`) so the label also acts as the editable curve/control point. Physical links also emit native endpoint TBs (`position: "device1" / "device2"`) for interface names. Generate Live defaults **shapes** and **text labels** on so AS/area/VRF/BD group shapes and link TBs appear immediately on the canvas.
- **Generated layers / evidence panel** (`styles.css` + `topology-generator.js`): The floating **`#generated-protocol-panel`** uses theme-scoped classes (**`.generated-protocol-panel`**, `__title`, `__actions`, `__btn`, `__evidence`, `__row`, `__swatch`) under **`body.ui-skin-v2`** with **`--skin-v23-*`** tokens (not hard-coded `editor.darkMode` panel fills). The placement dialog must visually match **`topology-file-ops.js::_showNewTopologyDomainPicker()`**: same compact centered card, colored domain rows, left accents, icon tiles, and footer scale. Actions: **All / None / Physical / Routing / Services** plus **Evidence** (toggles the compact correlation summary). Keep attached TB visibility tied to parent links as today.
- **Drivenets-style generated topology and link tables** (`topology-generator.js`, `topology-link-autofill.js`, `topology-device-monitor.js`, `routes/topology_generator*.py`): Generated physical links must carry per-side `device1Interface/device2Interface`, `device1IpAddress/device2IpAddress`, VLAN/subinterface fields, and `linkDetails.discoveryEvidence`. Routing overlays must include router IDs, peer IP, ASNs, and protocol evidence. DeviceMonitor stores scoped `_monitorContext` on devices and schedules `TopologyLinkAutofill`, which calls **`POST /api/topology-generator/enrich-link-tables`** and applies patches only to empty or auto-owned link-table fields. Manual user values are preserved; conflicts go to `link.linkDetails.discoverySuggestions` and are displayed in the Link Table modal.
- **Generated visibility actions:** The generated protocol panel now includes **All / None / Underlay / Overlay / Routing / Services / Identity / Evidence**. Generated objects should use `layer:underlay`, `layer:overlay`, `layer:identity`, and `layer:evidence` group ids in addition to protocol-specific groups so links, attached TBs, service cards, and evidence callouts toggle together.
- **PE/RR partial evidence correlation:** If a preserved PE/RR DUT has working app SSH evidence but live auth/config collection fails, Generate may infer a conservative `N.N.N.N` router-id alias from labels such as `PE-4` / `YOR_CL_PE-4` / `RR-2` solely for BGP peer-IP matching. This keeps PE-4 in the correlated topology when another DUT advertises peer `4.4.4.4`, without inventing config, services, or DNOS commands for that device.
- **Protocol stack rendering:** IGP overlays should render protocol-stack labels, not generic IGP labels: `ISIS+LDP`, `ISIS-SR`, `ISIS+LDP+SR`, or `OSPF-SR` based on parsed running-config MPLS/SR facts. BGP overlay labels should show router IDs, peer IP, ASNs, and AFI/SAFI evidence such as `l2vpn-evpn` / `vpnv4/vpnv6` when available.
- **Service cards over RT callouts:** Shared RTs are evidence under a service card. Prefer VRF/BD/EVPN service labels with `routeTargets[]`; do not render standalone `kind: rt` cards or RT links as the primary visual object.
- **SCALER CONFIG topology switch safety** (`scaler-gui.js`): `_setupTopologyChangeListener()` clears local `_deviceContexts`, `_wizardBatch`, and `_wizardChangeLog` on `topology:loaded`, `topology:active-changed`, and `topology:auth-logout`, then closes the Scaler panel stack with the normal animation. This prevents wizard context/device matches from the prior topology leaking into the newly active topology; correctness still comes from `DeviceState` scope isolation.
- **Cache buster:** bumped to `styles.css?v=20260429e-generated-protocol-polish`, `topology-share.js?v=20260428a-domain-share-open-fix`, `topology-file-ops.js?v=20260428z-shared-inbox-expanded-default`, `topology-generator.js?v=20260429e-generated-protocol-polish`, `topology-link-autofill.js?v=20260429d-drivenets-topology`, `topology-device-monitor.js?v=20260429d-drivenets-topology`, `topology-link-table.js?v=20260429d-drivenets-topology`, `topology-tests.js?v=20260429e-generated-protocol-polish`, `scaler-gui.js?v=20260428a-scope-reset`, `topology-ai.js?v=20260428v-ai-clarify-router`, `topology-notifications.js?v=20260428y-activity-log-theme-sync`, and `topology.js?v=20260428y-activity-log-theme-sync` — bump again on any CSS/JS edit.

When extending v2.3, append rules with `body.ui-skin-v2 ...` parents, never global element selectors. Use the v2.3 CSS variables (`--skin-v23-*`) so light/dark mirror automatically.

### Auth lifecycle (multi-user) — 2026-04-28

- `topology-auth.js` dispatches **`topology:auth-login`** and **`topology:auth-logout`** on `window`. Subsystems that must stop on logout must subscribe to these events (legacy `auth:login` / `auth:logout` were not emitted by TopologyAuth).
- **DeviceMonitor** (`topology-device-monitor.js`): listens for `topology:auth-*` (and keeps legacy names), calls `stop()` + `DeviceState.abortAll` on logout; **`_tick`** returns early when `TopologyAuth.isAuthenticated()` is false.
- **DeviceState** (`topology-device-state.js`): `abortAll` on `topology:auth-logout` (plus legacy listeners).
- **Startup noise:** `scaler-gui-upgrade.js` `_checkRunningUpgrades`, `topology-file-ops.js` `loadCustomSections`, and `topology-ai.js` `_probeAiConfig` skip authenticated `/api/*` calls when the user is not logged in, avoiding 401 spam after logout or on an unauthenticated first paint.

### Topologies dropdown sharing/domain UI — 2026-04-28

- Share-related topology row actions (`Share`, `Stop sharing`, remove from Shared-with-me) and outgoing "Shared with ..." badges use high-contrast white/black instead of domain accent color so they remain readable on every domain tint.
- `FileOps._attachHoverTip` suppresses nested SVG `<title>` text while the custom tooltip is visible; this prevents duplicate native + custom “Shared with ...” bubbles.
- The Topologies button layer-stack icon must include one purple shared-in layer when any shared-in domain or "Shared with me" inbox topology exists. Shared-in content is virtual (from domain sharing cache), not part of `/api/sections`, so `_updateTopoBtnIcon` adds it explicitly. `_refreshSharingCache` must retain the fetched `domains` list or the icon cannot see shared-in layers.
- The per-domain gear in `topology-domain-knowledge.js` is intentionally narrowed to **feature/image branch monitoring** only. Appearance editing stays in Manage Topology Domains; non-branch knowledge kinds may still exist in the backend but are filtered out of this compact drawer.
- Device style previews live inside `.device-style-grid`; their canvases must override the global dark-mode `canvas` background with `background: transparent !important`, and the grid stays two columns so labels/previews do not collide in the left toolbar.

### EVPN MAC mobility / AC↔PW (PE-1, RR-SA-2, PE-4) — /TEST context (2026-04-27)

- **What the catalog already proves:** `~/SCALER/TEST/catalog/evpn_mac_mobility_SW204115` recipe `ac_pw` targets **PE-1** as DUT with **`spirent_vpls_cp`** (Spirent = VPLS BGP peer, PW data plane on `PW_TEST_ELAN`, AC on the DNAAS-connected sub-if, e.g. `ge400-0/0/5.1010`). That path **passed** (e.g. `RUN_20260411` — PW→AC scenarios). Prerequisites and blocked groups when PW is BNI are in `scaler/TEST/catalog/evpn_mac_mobility_SW204115/shared/infrastructure_modes.json`.
- **Why “PW→AC on the current topology” is not the same as “run `ac_pw` on PE-1”:** A separate attempt used **RR-SA-2** as the DUT for AC↔PW. **Phase A** must show the test MAC as **Local** on the DUT from **AC ingress** before PW moves mean anything. On RR, Phase A still showed the MAC via **VPLS / PW** (e.g. toward `1.1.1.1`) instead of Local on the AC — i.e. the control plane still attributed learning to the **PE-1 → RR PW path**, not to Spirent on RR’s `bundle-100.4001` (outer 214 / inner 4001). Until AC ingress is proven, **Automated AC↔PW verdicts on RR are blocked** (wrong learning source).
- **Unicast “destination anchor” (PE-1 / PE-4):** A v4 idea (broadcast keepalive + unicast TRK→DST across PEs) did not show the expected TRK on DUTs: one Spirent leg + lab fabric behavior (short path, unknown-unicast, same-port learning) is not a guaranteed simple L2 bridge for that signal.
- **DNAAS vs DUTs:** **Default to DUT evidence** — `show evpn mac-table`, AC vs PW / interface, counters on the right IF — first. **DNAAS bridge domains** (e.g. leaf B15 `bundle-60000.214` + `bundle-100.214` into RR) are only for explaining **“frames never hit the AC”** *after* the DUT shows the MAC is not learned as Local on that AC. Do not spend lab time on DNAAS before the DUT proves whether traffic reached the expected interface.
- **Progress visibility preference:** During live `/TEST` and `/SPIRENT` runs, use occasional large visual markers in chat updates (for example discovery, test running, fix, blocker, pass, stop, results) so the operator can scan long troubleshooting sessions quickly. Keep exact commands/config/evidence text plain.
- **2026-04-28 AC↔PW blocker cleanup:** PE-1 `EVPN_SI_VPLS_1` residual `sticky-interface enabled` on `ge400-0/0/5.4001` was removed with `commit check` + `commit`; `EVPN_SI_VPLS_1` MAC tables are empty on PE-1/RR-SA-2/PE-4 and LLP shutdown tables are empty. The stale Spirent objects (`pw_test_v4001`, `pw_test_s_v4001`, `acpw_learn_v4001`, `pwac_learn_v4001`, `vpls_pw_label_1032295`) were removed; session `dn_spirent_main` remains reserved and idle.
- **2026-04-28 AC↔PW harness guardrail:** Do not accept Spirent TX counters as PW-trigger proof. `scenario_runner.py` now requires `show evpn mac-table ... require_source="pw"` for PW phase and `require_source="local"` for AC phase; missing source-qualified PW proof is `FAIL`, not `WARN`. `set-stream-active` is only a best-effort noise reducer and must not be trusted for verdicts.
- **2026-05-02 `mac-table-ghost` verifier semantics:** `show dnos-internal routing evpn instance <EVI> mac-table-ghost detail` is an "also include ghosts" diagnostic view (`alsoGhost=true` in zebra), not a ghost-only table. Active selected `L>`, `B>`, and `v>` MACs may appear there. `/TEST` must count only real ghost/suppression/stale/no-bestpath entries, not every `MAC address:` line.
- **2026-05-02 SC04 source-coexistence verifier:** `basic_learning` SC04 is trustworthy only when the runner emits an executable `all_sources_present` verdict layer. The recipe must declare `source_mac_flags` with the exact SC01/SC02/SC03 MAC-to-source mapping (`00:de:ad:00:01:01` -> `L>/local`, `00:de:ad:00:02:01` -> `B>/bgp`, `00:de:ad:00:03:01` -> `v>/pw`). A documented `step_table` alone is not enough; missing or mismatched source-qualified state, forbidden `F/D` flags on those MACs, or a missing VPLS BGP session must produce a real FAIL layer so the bug-finding guard and `/debug-dnos` path can trigger.
- **2026-04-28 AC↔PW Spirent prep:** The helper source streams `acpw_pe1_ac_src_214_4001` (outer `214`, inner `4001`) and `acpw_pe4_pw_src_219_4001` (outer `219`, inner `4001`) were validated as the correct L2/Q-in-Q shape, then removed before retest because the generator starts every StreamBlock. A clean retest must start with zero Spirent streams/devices so the orchestrator creates only its own phase streams. `test_runner.py` was fixed so pre-created `pw_test_v<inner>` / `pw_test_s_v<inner>` use Q-in-Q when `pw_outer_vlan` is known instead of wrongly creating single-tagged VLAN `<inner>`.
- **Open next steps for /TEST:** (1) Fix **tagging / bridge-domain** so Spirent VLAN 214 actually presents on RR’s **bundle-100.4001** as AC traffic, then re-check Phase A = Local on RR; or (2) **accept PE-1 as the only DUT** for `ac_pw` in this lab and document RR as out-of-scope until the path is clean; (3) dual-PE recipes that need a second PE still depend on a real **PE-4 DNAAS** path per `dual_pe_mode` in `infrastructure_modes.json`.
- **AC L2 smoke (orchestrator):** `python3 scaler/TEST/catalog/evpn_mac_mobility_SW204115/mac_mobility_orchestrator.py --device <DUT> --ac-smoke --evpn-name <instance> --inner-vlan <n> [--outer-vlan <n>] [--ac-interface <if>] [--ac-smoke-keep-macs]` — uses `smoke_test_l2_path` (Spirent `create-stream` + poll `show evpn mac-table`). Exit 0 when the smoke MAC appears. Default clears EVPN MAC table after; add `--ac-smoke-keep-macs` to leave table intact for inspection. **Full runs:** `mac_mobility_orchestrator.py --run <TEST_ID> --execute` already invokes this same smoke **automatically** in `orchestration/test_runner.py` preflight (`spirent_run_preflight` → `smoke_test_l2_path`); the standalone `--ac-smoke` flag is only for ad-hoc / debugging without loading a recipe.

### EVPN MAC mobility / live service map (PE-1, RR-SA-2, PE-4) — discovered 2026-04-28

- **Lab no longer uses `PW_TEST_ELAN`.** Catalog `ac_pw` recipe defaults are stale (`pw_test_evpn_name=PW_TEST_ELAN`, `pw_test_ac=ge400-0/0/5.1010`). Replace with the discovered EVIs below or override at runtime via `pw_test_evpn_name`/`_pw_ac_interface`.
- **AS numbering:** PE-1 and PE-4 are AS `1234567`; RR-SA-2 is AS `123` (eBGP between RR and PEs). All three PE-to-RR sessions are Established with `l2vpn-evpn` and `l2vpn-vpls` AFs (PE-1↔RR, PE-4↔RR; PE-1 and PE-4 do not peer directly).
- **Loopbacks / router-IDs:** PE-1 `1.1.1.1`, RR-SA-2 `2.2.2.2`, PE-4 `4.4.4.4`. RR is the VPLS hub for PE-1↔PE-4.
- **Per-device EVPN service inventory:**

| EVI name | EVI ID PE-1 | EVI ID RR-SA-2 | EVI ID PE-4 | RT (l2vpn-vpls / l2vpn-evpn) | PE-1 AC | RR-SA-2 AC | PE-4 AC | PW status |
|---|---|---|---|---|---|---|---|---|
| `EVPN_SI_VPLS_1` | 2 | 1 | 2 | `1234567:2001` | `ge400-0/0/5.4001` (outer 214 / inner 4001) | `bundle-100.4001` (outer 214 / inner 4001) | `ge100-18/0/0.4001` (outer 219 / inner 4001) | PE-1↔RR Installed; RR↔PE-4 Installed (real 3-site) |
| `EVPN_SI_VPLS_2` | 3 | 2 | 4 | `1234567:2002` (PE-1 also has `import/export-l2vpn-evpn 1234567:2002`; PE-4 only has the EVPN RT, **no** SI/VPLS RT) | `ge400-0/0/5.4002` (214/4002) | `bundle-100.4002` (214/4002) | `ge100-18/0/0.4002` (219/4002) "HYBRID-EVPN-REMOTE / mode=EVPN-only" | PE-1↔RR Installed; PE-4 EVI is **non-SI EVPN-only** (no PW) |
| `EVPN_SI_VPLS_3..5` | 4..6 | 3..5 | n/a | `1234567:2003..2005` (VPLS-only) | `ge400-0/0/5.4003..4005` | `bundle-100.4003..4005` | none | PE-1↔RR Installed only |
| `EVPN_SI_AC_PW_test` | 7 | n/a | 3 | `1234567:2006` (VPLS) | `ge400-0/0/5.4006` (214/4006) "AC<->PW MAC mobility direct PE-1<->PE-4" | **missing** on RR | `ge100-18/0/0.4006` (219/4006) | PW table empty everywhere — instance was provisioned for direct PE-1↔PE-4 PW but neither side currently has it Installed |
| `HA_TEST_ELAN` | 1 | n/a | n/a | (description-only stub) | none | none | none | empty placeholder |
| `VPLS_SI-1` | n/a | n/a | 1 | (no RT exported) | n/a | n/a | `ge100-18/0/0.102` (single-tagged) | empty |

- **Service-pairing summary for AC↔PW with PE-1 as DUT:**
  - **Best fit (real 3-site):** `EVPN_SI_VPLS_1` on PE-1 + RR-SA-2 + PE-4. Real PE-1↔RR PW Installed (`ingress 1032295`), real RR↔PE-4 PW Installed (`ingress 1032335` from RR side / `1032269` from PE-4 side). PE-1 sees one peer (`2.2.2.2/2001`); PE-4 sees one peer (`2.2.2.2/2001`); RR sees both peers in the same EVI. With Spirent on PE-4’s AC `ge100-18/0/0.4001` (outer 219 / inner 4001), PE-4 learns `Local`, advertises VPLS into RR, RR forwards over PW into PE-1; **PE-1 then learns the test MAC as PW-source** (`v>` flag from `2.2.2.2`). With Spirent on PE-1’s AC `ge400-0/0/5.4001` (outer 214 / inner 4001), PE-1 learns `Local` and advertises into RR. This is the cleanest AC↔PW path that actually exists.
  - **Hybrid AC↔PW + EVPN observer:** `EVPN_SI_VPLS_2` is the only EVI where PE-4 carries the EVPN RT (`1234567:2002` import+export l2vpn-evpn) without a PW. PE-1 carries both the VPLS RT (PW into RR) and the EVPN RT, so PE-1 advertises RT-2 for any local AC MAC, and PE-4 will import that RT-2 as the EVPN observer. Use this EVI when the test wants `AC↔PW (PE-1↔RR) + RT-2 observer (PE-4)`.
  - **Direct PE-1↔PE-4 (deferred):** `EVPN_SI_AC_PW_test` is provisioned on PE-1 and PE-4 only. It has no PE-1↔PE-4 PW today and RR does not carry the EVI at all, so it cannot be used as a real AC↔PW path until either (a) a PE-1↔PE-4 VPLS PW is brought up, or (b) the EVI is added on RR.
  - **Avoid:** `HA_TEST_ELAN`, `VPLS_SI-1`, RR `bundle-100.215` — none are tied to a working PW/EVPN pairing for this test.

- **Expected MAC source per role for AC↔PW on `EVPN_SI_VPLS_1`:**
  - PE-1 AC phase: PE-1 `Local` on `ge400-0/0/5.4001`; RR sees RT-2 from `1.1.1.1`; PE-4 sees RT-2 from `1.1.1.1`.
  - PE-4 AC phase (acts as the “PW side” for PE-1): PE-4 `Local` on `ge100-18/0/0.4001`; RR sees RT-2 from `4.4.4.4` and forwards data plane over its PW to PE-1; **PE-1 learns the MAC as `v>` via PW** with nexthop `2.2.2.2`.
  - Spirent is **never** the BGP peer in this design — the lab’s real PWs and BGP sessions carry the move.

- **DNAAS reminder:** Spirent port is on B-14 (outer 214), PE-4 sub-if `4001` uses outer 219, RR `bundle-100` is on B-15. Existing learned mapping (per spirent learned rules) shows fabric `213` carries user VLAN 219 between B14 and PE-4’s leaf, and outer 214 reaches PE-1’s leaf. The RR-side AC (B-15) only matters when we want to drive Spirent traffic toward RR directly — for the recommended path (PE-4 AC ingress) we only need outer 219 / inner 4001.

### EVPN MAC mobility / `pe1_dut_30moves` runner — 2026-04-28

- **Why a new dedicated runner:** the catalog `ac_pw` recipe still references the deleted `PW_TEST_ELAN` instance and `ge400-0/0/5.1010`, and uses Spirent-emulated VPLS as the PW source. The user explicitly asked for ≥30 PE-1-recorded MAC moves on the live `EVPN_SI_VPLS_1` service using the lab’s real PWs; the catalog runner cannot drive that without code changes. New self-contained runner lives under `~/SCALER/TEST/catalog/evpn_mac_mobility_SW204115/tests/pe1_dut_30moves/` (recipe.json + `run_pe1_dut_30moves.py`).
- **Topology blocker confirmed (B-14 outer-214 only reaches PE-1):** B-14 BD `g_yor_v214_PE-1-evpn` ties `ge100-0/0/15.214` to fabric 214 → D-16 → PE-1 only. B-15 has its own `g_yor_v214_RR-SA-2-evpn` BD, but **no AC on `ge100-0/0/6.214`**, so Spirent outer-214 frames never reach RR-SA-2 today. Don’t plan tests that depend on Spirent driving RR’s `bundle-100.4001` directly until that AC is added.
- **Dual-source test design (no DNAAS changes needed):** Two Q-in-Q L2 streams from the same Spirent port, sharing one source MAC `00:DE:AD:00:DA:01` and broadcast destination, alternated by `spirent_tool.py set-stream-active`:
  - `mm_pe1_ac_v214_4001` — outer 214 / inner 4001 → B-14 → fabric 214 → D-16 → PE-1 `ge400-0/0/5.4001` ⇒ PE-1 sees the MAC as **Local**.
  - `mm_pe4_ac_v219_4001` — outer 219 / inner 4001 → B-14 → fabric 213 (existing READY path) → B-10 → PE-4 `ge100-18/0/0.4001` ⇒ PE-4 learns Local, advertises VPLS to RR-SA-2, RR forwards over its installed PW to PE-1 ⇒ PE-1 sees the same MAC as **`v>` from `2.2.2.2`** (PW source). One src MAC + flag toggle = one MAC move, no NPU race because only one stream is `Active=TRUE` at a time.
- **30-move loop safety:** Default 4s dwell + 2s breather every 5 moves, classifier polls PE-1 `show evpn mac-table instance EVPN_SI_VPLS_1` every 0.4s until `Local`/`v>` observed (or dwell deadline). Strict per-move verdict; runner exits non-zero if any move fails. Mobility threshold should not damp because EVPN_SI_VPLS_1 has no `mac-handling` overrides and we keep ≤2 moves/8s on average.
- **Description tagging on DUTs (committed by the runner):** PE-1 `ge400-0/0/5.4001`, PE-4 `ge100-18/0/0.4001`, RR-SA-2 `bundle-100.4001` all get `TEST=mac_mobility_30moves_2026-04-28` appended along with `ROLE=PE1-DUT-AC` / `ROLE=PW-source-for-PE1` / `ROLE=hub-PW`. Description-only edits (no L2/RT/RD/site changes). Each device runs `commit check` → `commit`; if check fails the runner aborts with a `rollback 0`.
- **Post-test policy:** stop both Spirent streams, leave them in `dn_spirent_main` with `Active=FALSE` for trivial re-runs; no MAC-table clear (PE-1 retains last `Local`/`v>` for inspection). Use `--skip-tagging` on subsequent re-runs to avoid re-committing identical descriptions.
- **2026-04-28 /TEST deep-debug layer rule:** EVPN VPLS SI / AC↔PW test recipes must include `debug_layers` in addition to normal CLI assertions. Before building trace plans, `/debug-dnos` must bootstrap from `/search-company-knowledge` using the EVPN ELAN SI epic/HLD (`SW-178648`, DP enabler `SW-183400`, DV HLD/design, QA v26.2 behavior page) and map the internal path `BGP l2vpn-vpls/evpn → zebra/EVPN manager → fib-manager → NCP wb_agent → MAC table/PW labels`. Default deep-debug mode is `on_fail`; use `always` for first-run/new infrastructure or user-requested "all layers". AC phase requires source-qualified `Local`; PW phase requires source-qualified `v>` / VPLS PW. If a layer contradicts the CLI verdict, mark the run `INCONCLUSIVE`/`FAIL` and invoke `/debug-dnos` with EVI, MAC, AC, PW peer, move direction, expected source, and timestamp.
- **2026-04-30 basic-learning rerun rule:** `TEST_mac_mob_basic_SW205160`
  was rewritten to treat old passes as insufficient unless rerun with MCP DNAAS
  diagnose + teach-plan gates and the full per-step evidence cascade. AC scenarios
  must collect source-qualified MAC detail, BGP RT-2, forwarding-table, and ghost-MAC
  evidence; the PW scenario must substitute `{evpn_name}` to the discovered PW EVI
  before running show commands. Recipe `stop_on_fail=true` must halt on the first
  functional FAIL/ERROR so the next step is `/debug-dnos`, not another scenario.

### Cursor /XDN (unified topology + scaler context)

- **Skill:** `~/.cursor/skills/xdn-topology-mastery/` (`SKILL.md`, `architecture-reference.md`, `api-reference.md`, `bul-reference.md`, `editing-patterns.md`, `learning.md`).
- **Slash command:** `/XDN` in Cursor (also under repo `.cursor/commands/XDN.md` when using this workspace).
- **Learning:** `~/.topology_learning.json` -- after substantive topology/scaler sessions or `/XDN learn`, run `python3 ~/.cursor/tools/prune_learning.py --command xdn --sync-only` so `learned_index.md` stays current.

### Scaler Bridge API (scaler_bridge.py, port 8766)

The bridge wraps scaler-wizard modules for the topology app. serve.py proxies `/api/config/*`, `/api/operations/*`, `/api/devices/discover`, `/api/devices/{id}/test`, `/api/devices/{id}/context`, `/api/ssh/probe`, `/api/ssh/check-port`, `/api/ssh/discover-ncc-mgmt`, and related `/api/ssh/*` helpers to it.

**DNOS device communication (SSH):** Shared library `scaler/scaler/dnos_session.py` provides `DNOSSession` (prompt-based show commands, optional `SSHConnectionPool` reuse via `client=`, `config_mode` / `commit` / `send_config_set`). Bridge routes use `topology/routes/_device_comm.py` (`DeviceCommHelper`: `run_show`, `run_show_batch`, `fetch_running_config`, `get_session`). Optional `scaler/scaler/dnos_netmiko.py` wraps Netmiko `generic` for one-off commands. Raw WebSocket terminal, upgrade flows, and `connection_strategy.py` stay on paramiko as documented in the Netmiko integration plan.

**Terminal-to-GUI parity (documented in `~/.cursor/skills/xdn-topology-mastery/SKILL.md` section "Scaler: five-layer parity"; run `/XDN` in Cursor to load):** Every new API endpoint MUST have a corresponding `ScalerAPI.js` method and a scaler GUI entry point (see `scaler-gui*.js` bundles). No terminal-only or GUI-only features. Full chain: `config_builders.py` -> terminal wizard -> `scaler_bridge.py` -> `scaler-api.js` -> `scaler-gui.js` (+ domain modules as needed).

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/devices/{id}/context` | GET | Unified device context for wizard suggestions. Returns: interfaces (physical, bundle, subinterface, pwhe, free_physical), lldp, config_summary, wan_interfaces, igp, services (fxc_count, vrf_count, next_evi), loopbacks, vrfs, bridge_domains, flowspec_policies, routing_policies, bgp_peers, multihoming, platform_limits. Query `?live=true` for live fetch. |
| `/api/devices/{id}/test` | POST | Test SSH connection to device |
| `/api/config/{id}/running` | GET | Cached or live running config |
| `/api/config/{id}/summary` | GET | Parsed config summary (AS, RTs, EVPN, etc.) |
| `/api/config/{id}/sync` | POST | Fetch and cache config from device |
| `/api/config/{id}/interfaces` | GET | Parsed interface list |
| `/api/config/{id}/diff` | GET | Cached vs live diff, in_sync status |
| `/api/config/compare` | POST | Compare two device configs (device_ids) |
| `/api/config/generate/interfaces` | POST | Generate interface config |
| `/api/config/generate/services` | POST | Generate service config |
| `/api/config/generate/bgp` | POST | Generate BGP peer config |
| `/api/config/generate/igp` | POST | Generate IGP (ISIS/OSPF) config |
| `/api/config/generate/batch` | POST | Batch generate from multiple hierarchies (items: [{hierarchy, params}]) |
| `/api/config/preview-diff` | POST | Preview diff of proposed config vs running (device_id, config) |
| `/api/operations/validate` | POST | Validate DNOS config (config, hierarchy, check_limits, check_interface_order). Returns valid, errors, warnings, suggestions. |
| `/api/config/templates` | GET | List policy templates |
| `/api/config/templates/generate` | POST | Generate from template |
| `/api/config/delete-hierarchy-options` | GET | List hierarchies for Delete Hierarchy GUI (display, command, warning). |
| `/api/config/flowspec-dependency-check` | POST | FlowSpec dependency check. Body: `{ device_id, ssh_host }`. Returns `{ issues: [{ component, issue, severity, fix_command, fix_description }], passed }`. |
| `/api/config/scan-ips` | POST | Scan device config for used IPv4/IPv6. Body: `{ device_id, ssh_host, parent_interface?, ipv4_prefix?, ipv6_prefix?, count?, check_ipv4?, check_ipv6? }`. Returns `used_ips`, `suggestion`, `overlap_check` (when check params provided). Used by interface wizard IP collision detection. |
| `/api/config/push/estimate` | POST | Get push time estimates. Body: `{ config?, device_id?, ssh_host? }`. Returns estimates for terminal_paste, file_upload, lofd from timing_history.json. |
| `/api/operations/delete-hierarchy` | POST | Delete config hierarchy (dry_run). Body: `{ device_id, hierarchy, dry_run, ssh_host?, sub_path? }`. |
| `/api/operations/push` | POST | Push config. Body: `{ device_id, config, dry_run, push_method: "terminal_paste"|"file_upload", load_mode: "merge"|"override", ssh_host?, job_name? }`. Returns job_id. |
| `/api/config/push/progress/{job_id}` | GET | SSE stream for push progress (phase, percent, terminal lines, elapsed_seconds, estimated_remaining_seconds, done, success, awaiting_decision) |
| `/api/operations/{job_id}/cancel` | POST | Cancel push job (mid-paste abort or discard held). Sets _cancel_requested for running jobs; calls cancel_held_session for awaiting_decision. |
| `/api/operations/push/{job_id}/commit` | POST | Commit held config on same SSH session (after dry_run when check passed) |
| `/api/operations/push/{job_id}/cancel` | POST | Cancel held config (discard candidate) and close SSH session |
| `/api/operations/push/{job_id}/cleanup` | POST | Cleanup dirty candidate on device after failed commit check (connects fresh) |
| `/api/operations/jobs` | GET | List all jobs (active + recent history) |
| `/api/operations/jobs/{job_id}` | GET | Full job state including all terminal output |
| `/api/operations/jobs/{job_id}/retry` | POST | Re-submit same config. Returns new job_id. |
| `/api/operations/jobs/{job_id}` | DELETE | Remove job from history |
| `/api/config/limits/{device_id}` | GET | Platform limits (max_subifs) from limits.json |
| `/api/devices/discover` | POST | SSH discover device by IP, add to inventory |
| `/api/devices/{id}/resolve` | GET | Resolve device to mgmt_ip (scaler_bridge fallback when discovery_api down) |
| `/api/ssh/probe` | POST | Probe connection methods (TCP reachability). Body: `{ device_id, ssh_host? }`. Returns `{ methods, recommended, device_state }`. |
| `/api/ssh/discover-console` | POST | Discover console path via Zohar's CSV DB (primary, ~700 devices) or Device42 API (fallback). Body: `{ device_id, serial_number?, ssh_host? }`. Returns `{ console_server, port, pdu_entries, source, serial_no }`. Auto-saves to console_mappings.json. |
| `/api/ssh/pdu-power` | POST | PDU power action via Zohar's PDU mapping. Body: `{ serial_number?, device_id?, action: reboot\|off\|on\|status, pdu_host?, outlet? }`. Looks up PDU from Zohar's DB if host/outlet not given. |
| `/api/ssh-pool/evict` | POST | Evict pooled SSH client(s). Body: `{ ip, device_id? }`. Pool is keyed by mgmt IPv4; when `ip` is not dotted IPv4, optional `device_id` (canvas label) is used with `_resolve_mgmt_ip` to evict the resolved IP. Returns `evicted`, `evicted_keys`. |
| WebSocket `/api/terminal/ws` | WS | In-browser terminal. Params: `device_id`, `ssh_host`, `method`. Browser builds URL via `ScalerAPI.getBridgeWebSocketOrigin()` which returns same-origin (`ws://<page-host>:<page-port>`) unless an explicit `baseUrl` is set. serve.py proxies the upgrade to scaler_bridge:8766 so this works on remote-access deployments where only 8080 is exposed. Streams stdin/stdout via paramiko. |
| `/api/config/scan-existing` | POST | Scan device for existing sub-ids, VRFs, EVIs, L3 conflicts. Body: `{ device_id, ssh_host, scan_type: "interfaces"\|"services"\|"vrfs"\|"all" }`. Returns `existing_sub_ids`, `l3_conflicts`, `l2_sub_ids`, `outer_inner_map` (QinQ), `sub_id_details`, `next_free`, `config_fetched_at`. Used by interface wizard collision check and encap overlap detection. |
| `/api/config/detect-pattern` | POST | Detect interface pattern (dot1q/qinq, stepping_tag, last_vlan, last_sub_id, suggested_next_vlan) from device config. Body: `{ device_id, ssh_host, parent_interface }`. Used for auto-fill in subif flow. |
| `/api/mirror/analyze` | POST | Analyze source vs target config for mirror. Body: `{ source_device_id, target_device_id, ssh_hosts?: [src_ip, tgt_ip], lldp_neighbors?: [] }`. Returns `source_summary`, `target_summary`, `smart_diff`, `interface_map`, `smart_suggestions` (bgp_neighbors, wan_ips, service_ips, lldp_mapping). |
| `/api/mirror/generate` | POST | Generate mirrored config. Body: `{ source_device_id, target_device_id, ssh_hosts, interface_map, ip_mapping?: { source_ip: target_ip }, section_selection?, section_actions?, output_mode: "full"\|"diff_only" }`. Returns `config`, `summary`, `line_count`, `diff_stats`. |
| `/api/mirror/preview-diff` | POST | Preview diff of proposed mirrored config vs target running. Body: `{ target_device_id, config, ssh_host }`. Returns `diff_text`, `lines_added`, `lines_removed`. |
| `/api/operations/image-upgrade/branches` | POST | List dev/release branches from Jenkins. Body: `{ type: "dev"|"release"|"all" }`. Returns `{ branches: [{name, url}], type }`. |
| `/api/operations/image-upgrade/branch-switch` | POST | Detect branch switch (e.g. dev_v25 -> dev_v26). Body: `{ current_version, target_version }`. Returns `{ is_switch, current_branch, target_branch, requires_delete_deploy }`. |
| `/api/operations/image-upgrade/compat` | POST | Version compatibility report. Body: `{ source_version, target_version, config_text? }`. Returns `{ severity, incompatible_count, recommendation, ... }`. |
| `/api/operations/image-upgrade/builds` | POST | List recent builds with image artifacts for a branch. Body: `{ branch, limit?, max_results?, include_failed? }`. When `include_failed=false` (default), only SUCCESS builds. When `include_failed=true`, includes FAILED builds with valid DNOS/GI/BaseOS artifacts. Returns `{ branch, builds: [...] }`. |
| `/api/operations/image-upgrade/resolve-url` | POST | Resolve Jenkins URL to build info. Body: `{ url }`. Returns `{ branch, build_number, dnos_url, gi_url, baseos_url, is_sanitizer, is_expired, result }`. |
| `/api/operations/image-upgrade/stack` | POST | Get stack URLs for branch + build. Body: `{ branch, build_number }`. Returns `{ dnos_url, gi_url, baseos_url, is_sanitizer, is_expired }`. |
| `/api/operations/image-upgrade/plan` | POST | Per-device upgrade plan. Body: `{ device_ids, ssh_hosts, target_branch?, target_build_number?, target_version?, dnos_url? }`. SSHs to each device, detects mode (DNOS/GI/RECOVERY), current version, upgrade_type (normal/delete_deploy/gi_deploy/blocked). Returns `{ devices: { id: { mode, current_version, target_version, upgrade_type, reason, warnings, components } } }`. |
| `/api/operations/image-upgrade` | POST | Execute image upgrade. Body: `{ device_ids, ssh_hosts, branch, build_number, components, upgrade_type, device_plans?, max_concurrent?, dnos_url, gi_url, baseos_url, ... }`. Supports per-device plans and parallel execution (ThreadPoolExecutor). Returns `{ job_id }`. |
| `/api/config/{device_id}/save` | POST | Save generated config for later push. Body: `{ config }`. Writes to device config dir as wizard_*.txt. |
| `/api/config/generate/undo` | POST | Generate undo config from pushed config. Body: `{ config_text }` or `{ job_id }`. Returns `{ config }`. |
| `/api/operations/image-upgrade/build-status/{job_id}` | GET | Poll build status. Query `?latest=true` for lastBuild (trigger monitoring). |
| `/api/operations/image-upgrade/build-log/{branch}` | GET | Get Jenkins console log. Query `?build_number=N` (optional). |

**Config generation**: All `generate/*` endpoints use `scaler.wizard.config_builders` (pure DNOS generators). No frontend DNOS string construction. GUI previews always call backend API with full params. The terminal wizard (`interactive_scale.py`) also calls `config_builders.build_from_expansion()` for config generation, ensuring terminal and GUI produce identical DNOS output.

**Sub-interface-only policy**: Both CLI and GUI wizards only create sub-interfaces on existing physical/bundle parents. Physical interface creation is not supported (hardware-defined). Legacy types (bundle, ph, irb, loopback) are retained in `config_builders.py` for backward compatibility but are not exposed in any menu or wizard.

**Config push**: `POST /api/operations/push` uses `ConfigPusher` from scaler. Progress streamed via SSE at `GET /api/config/push/progress/{job_id}`. The SSE stream includes `terminal` (new SSH output lines since last poll) via `live_output_callback` piped from ConfigPusher. ScalerAPI.connectPushProgress uses EventSource for real-time progress and terminal streaming. For upgrade jobs, SSE also includes `device_state` (per-device status, phase, percent, error); `onDeviceState` callback renders per-device progress rows.

**Push methods**: `push_method` (terminal_paste | file_upload) and `load_mode` (merge | override). Terminal paste: SSH paste + commit. File upload: SCP to /config/ + `load merge` or `load override` + commit. Best for large configs.

**Cancel button**: High-visibility (white text, X icon). During paste: `POST /api/operations/{job_id}/cancel` sets _cancel_requested; paste loop aborts, sends `cancel`+`exit` on device to discard candidate. During held state: same endpoint calls cancel_held_session. Candidate config is always cleaned on device.

**Hold-and-commit flow** (dry_run): When `dry_run=true`, backend uses `push_config_terminal_check_and_hold()` which pastes config, runs commit check, and keeps SSH session alive. Job enters `awaiting_decision` state. Frontend shows Commit Now / Cancel (discard) buttons in the progress panel. User clicks Commit -> `POST /api/operations/push/{job_id}/commit` sends commit on same session. User clicks Cancel -> `POST /api/operations/push/{job_id}/cancel` sends cancel+exit. No second push job. When commit check fails, Cleanup button calls `POST /api/operations/push/{job_id}/cleanup` to connect fresh and run cancel on device.

**Timing learning**: On push completion, `save_timing_record()` writes to `scaler/db/timing_history.json`. `get_accurate_push_estimates()` uses this for per-method estimates. SSE stream includes `elapsed_seconds` and `estimated_remaining_seconds`.

**IP awareness**: `scan_used_ips()` and `suggest_next_ip_range()` in config_builders.py. Interface wizard IP step calls `ScalerAPI.scanIPs()` for used IPs and overlap check. Collision banner + "Use suggested" button (like VLAN encap).

**Running Commits Panel**: `ScalerGUI.openCommitsPanel()` opens a persistent panel that polls `GET /api/operations/jobs` every 2s. Shows job cards with status dot (gray=pending, cyan=running, green=completed, red=failed), progress bar, and expand/minimize. Expanded cards show a live terminal view with SSH output. For upgrade jobs, per-device rows (device_state) shown above terminal. Error lines highlighted red; DNOS errors parsed with `suggestErrorFix()` (patterns: "already exists", "limit exceeded", "Hook failed"). Retry button re-submits via `POST /api/operations/jobs/{job_id}/retry`. Accessible via "Commits" button in Scaler CONFIG menu with active-job badge. Job history persisted to `~/.scaler_push_history.json` (max 50 jobs, terminal truncated to 200 lines on completion).

**Push parity**: All wizards (Interface, Service, VRF, Bridge Domain, FlowSpec, Routing Policy, BGP, IGP) share the same push flow: Review step (generates config, shows preview, validation, optional diff) -> Push step (dry_run / merge / replace / clipboard+SSH). All route through `ScalerAPI.pushConfig()` -> `ScalerGUI.showProgress()` -> commits panel. `ssh_host` is included in all push calls from `deviceContext.mgmt_ip`.

**Wizard Run History** (Phase 2): `recordWizardChange(deviceId, changeType, details, options)` stores full run records with `generatedConfig`, `params`, `pushMode`, `jobId`, `success`. Persisted to `localStorage` key `scaler_wizard_history` (max 100 entries). `updateWizardRunResult(jobId, success)` updates history when push completes. Per-wizard "Last Run" card shows at top of each wizard when history exists for that wizard+device. Global "Wizard Run History" panel in CONFIG menu shows chronological list grouped by date. "Re-run with same params" pre-fills wizard; "Re-run on different device" opens Mirror Wizard with source=history device, target=user-selected device.

**Re-run on different device** (Phase 4c): Both per-wizard Last Run card and global History panel wire "Re-run on different device" to `openMirrorWizard(sourceId)`. User selects target device; Mirror Wizard runs analyze -> generate -> diff vs target -> push. Uses ConfigMirror from `mirror_config.py` for device-agnostic config adaptation.

**Mirror Config Wizard**: `openMirrorWizard(prefillSourceId?, prefillTargetId?)` uses WizardController with 4 steps: (1) Devices -- source + target dropdowns, (2) Smart Mapping -- auto-runs `ScalerAPI.mirrorAnalyze()`, shows editable tables for interface mapping, BGP neighbor IPs, WAN IPs, service IPs, LLDP mapping from `smart_suggestions`, (3) Analyze -- stat cards (add/modify/delete/identical) and per-section action selects (keep/edit/skip/delete), (4) Review -- auto-generates config via `mirrorGenerate()` with `ip_mapping`, shows preview + optional diff toggle via `mirrorPreviewDiff()`. Push on complete via `ScalerAPI.pushConfig()`. When prefilled, device dropdowns are pre-selected. **WizardController fix**: `renderNavigation()` uses `nav.querySelector()` instead of `document.getElementById()` to bind Next/Back/Skip, avoiding stale panel button binding when multiple wizards exist in DOM.

**Multihoming ESI Wizard**: `openMultihomingWizard()` uses WizardController with 3 steps: (1) Device Pair -- checkbox select exactly 2, ESI prefix input, redundancy mode (single-active/all-active), RT matching toggle, (2) Compare -- auto-runs `ScalerAPI.compareMultihoming()`, shows matching/device1-only/device2-only stat cards with re-compare button, (3) Sync -- review summary with key-value rows, push via `ScalerAPI.syncMultihoming()`. Backend uses correct DNOS format (`esi arbitrary value {value}`).

**Collision check** (Phase 3b): Interface wizard encap step and review step, when `interfaceType === 'subif'` and parent exists, call `ScalerAPI.scanExisting()`. Encap step shows early overlap banner with Continue/Skip/Override. Review step shows final safety-net warning. Options: Skip conflicts (passes `skip_vlans` to generate), Start after existing (auto-sets vlanStart), Override. `config_builders.build_interface_config` accepts `skip_vlans` to skip conflicting VLAN IDs during generation (terminal-style vlan_offset).

**Reusable step components** (Phase 4A): `ScalerGUI._buildPushStep(opts)` returns a Push step with configurable `radioName`, `includeClipboard`, `infoText`. `_buildDecisionStep(opts)` returns a Decision step (Save for Later / Push Config / Next Section) with `wizardType` and `getCreatedData`. `_buildReviewStep(opts)`, `_buildInterfaceSelector(opts)`, `_buildAddressFamilySelector(opts)` provide shared HTML/collectData for wizard steps. Interface, BGP, IGP wizards insert Decision step before Push. VRF, Bridge Domain, FlowSpec, Routing Policy, and Service wizards use `_buildPushStep`.

**Config Push Quality Fixes** (2026): (1) **API baseUrl**: All `fetch('/api/...')` in scaler-api.js use `ScalerAPI._api(path)` for remote server access. (2) **Time-based progress**: config_pusher.py progress percentages are phase-time-proportional (connect, paste, commit-check, commit) with 2s tick during long phases. (3) **QinQ naming**: build_interface_config uses inner VLAN as sub-if suffix when outer_step=0. (4) **Undo config**: `build_undo_config()` parses pushed config and emits delete commands; Undo button in push result dialog. (5) **Save for Later**: `POST /api/config/{device_id}/save` stores config to device dir; Decision step "Save for Later" option.

**Scaler menu order** (Phase 4C): Configuration Wizards: Interface, Service, VRF, Bridge Domain, BGP, IGP, FlowSpec, Routing Policy, Multihoming (matches terminal wizard hierarchy order).

**Scaler GUI Overhaul** (2026): Upgrade, Scale, and Multihoming wizards use topology canvas devices only (`_getWizardDeviceList()`). `window.ScalerGUI` is set so the device toolbar "Upgrade Stack" button can call `openUpgradeWizard()`. `_getWizardDeviceList` returns `ssh_host` for fast backend resolution. Upgrade wizard: 5-step WizardController (Devices, Source, Build, Compare, Execute) with branch browse, Jenkins URL, version comparison, branch-switch detection, compatibility report. Scale wizard: 3-step (Devices, Scale, Review) with scale suggestions in header. Multihoming wizard: 3-step (Device Pair, Compare, Sync). All multi-device wizards have context panels with Refresh and stale indicator (>5 min). Wired APIs: `wizardSuggestions` (What's Next), `detectBGPNeighbors` (BGP wizard), `detectScaleSuggestions` (Scale wizard), `validatePolicy` (Routing Policy), `getSmartDefaults` (BGP prefill).

**Upgrade wizard instant load** (Mar 2026): Eliminated the blocking `getDeviceContext()` loop that fetched full device context (config, interfaces, VRFs, etc.) over SSH for each device. The upgrade wizard only needs stack versions and mode, which DeviceMonitor already caches as `device._stackData`. New flow: (1) Wizard opens instantly using `_stackData` from DeviceMonitor cache + ScalerGUI `_deviceContexts` cache. `deviceStatus` is pre-populated from `_parseStackVersions(_stackData.components)`. (2) Phase 1 background: `getUpgradeDeviceStatus(ids, sshHosts, cachedOnly=true)` reads from `operational.json` server-side (~10ms/device, no SSH) to fill in mode and validate versions. (3) Phase 2 background: `getUpgradeDeviceStatus(ids, sshHosts, false)` does live SSH for definitive mode + install status. Refresh button unchanged (full SSH). Backend: `GET /api/operations/image-upgrade/device-status?cached_only=true` reads `operational.json` stack_components, dnos_url, device_state -- no SSH connection. Result: wizard opens in <200ms vs previous 10+ seconds blocking.

**Upgrade wizard Jenkins URL mode fix (2026-04-28):** URL tab must resolve pasted Jenkins build URLs through `ScalerAPI.resolveJenkinsUrl()` before any regex branch fallback. Do not parse a URL into only a branch first, because that drops the build number/artifact URLs and falls back to latest branch builds. URL mode also clears stale `selectedBuild` / `builds` state when a new URL is submitted. Raw build-status fetches should use `ScalerAPI._api(...)` for remote deployments.

**Cross-wizard dependency warnings** (Phase 4D): `_getWizardDependencyWarnings(wizardType, data)` returns context-based warnings (e.g. VRF needs sub-interfaces, FlowSpec name conflict, Multihoming ESI). `_renderDependencyWarnings(warnings)` displays them. VRF Interface Attachment step shows when no sub-interfaces exist.

**Validation**: Review steps call `ScalerAPI.validateConfig({ config, hierarchy })` after generating config. Errors and warnings displayed in `scaler-validation-box`. Uses `CLIValidator.validate_generated_config()` (syntax, scale limits, interface order).

**Diff preview**: Interface wizard Review step has "Show diff vs running" button. Calls `ScalerAPI.previewConfigDiff(deviceId, config, sshHost)` to show proposed-vs-running unified diff.

**Platform limits**: The sub-interfaces step validates total count against `GET /api/config/limits/{device_id}` (sources `limits.json` vlan_pool max_capacity, default 20480). Warning shown if `count * subifCount > max_subifs`.

ScalerAPI (scaler-api.js) methods: getDevices, getDevice, getDeviceContext, testConnection, syncDevice, syncConfig, generateInterfaces, generateServices, generateBGP, generateIGP, batchGenerate, previewConfigDiff, validateConfig, compareConfigs, getConfigDiff, getInterfaces, getTemplates, generateTemplate, discoverDevice, getDeleteHierarchyOptions, deleteHierarchyOp, flowspecDependencyCheck, getPushEstimate, pushConfig, commitHeldJob, cancelHeldJob, cancelOperation, cleanupHeldJob, connectPushProgress (supports onDeviceState for upgrade jobs), getJobs, getJob, retryJob, deleteJob, getLimits, scanExisting, scanIPs, detectPattern, mirrorAnalyze, mirrorGenerate, mirrorPreviewDiff, getBuildsForBranch, resolveJenkinsUrl, getBuildStack, getUpgradePlan, imageUpgrade (accepts device_plans, max_concurrent).

### Smart Wizard Suggestions (DeviceContextCache)

Wizards (Interface, Service, VRF, BGP, IGP) use a cached-then-live device context for smart suggestions:

- **Device resolution by SSH**: Canvas labels are NOT backend device IDs. Resolution uses `sshConfig.host` (which may be an IP, hostname, or serial number) as the primary key. `_resolveDeviceId(label)` extracts SSH credentials from the canvas device object. `ScalerAPI.getDeviceContext(deviceId, live, sshHost)` passes `ssh_host` to the backend.
- **Central IP resolution** (`_resolve_mgmt_ip(device_id, ssh_host)` in `scaler_bridge.py`): ALL endpoints use this single function. Uses cached `_build_scaler_ops_index()` (60s TTL) that indexes all `operational.json` files by serial, hostname, mgmt_ip, and dir name. Chain: 1) `ssh_host` is IP -> direct match in index; 2) `ssh_host` is serial/hostname -> match in index; 3) `device_id` exact match in index; 4) discovery API `_resolve_device`; 5) `device_inventory.json` fuzzy match; 6) partial name match (e.g. `PE-1` matches `YOR_PE-1`). Returns `(mgmt_ip, scaler_device_id, resolved_via)`. Results cached for 120s in `_resolve_cache`. Raises 503 if all fail.
- **NEVER add `_resolve_device()` calls directly in endpoints** -- always use `_resolve_mgmt_ip`. The discovery API frequently returns empty `mgmt_ip`; the central function handles all fallbacks.
- **Context builder** (`_get_device_context`): Uses `_resolve_mgmt_ip` first, then tries `_get_cached_config(scaler_device_id)`. Falls back to `_get_cached_config(device_id)` and `_get_cached_config(hostname)`. Reads stack and git_commit from `operational.json`. When `live=True` and stack/git_commit are missing, fetches via SSH (`show system stack | no-more`, `run start shell` + `cat .gitcommit`) and writes back to operational.json for caching. Returns `resolved_ip` field so frontend shows the actual IP.
- **DeviceContextCache**: `ScalerGUI.getDeviceContext(deviceId)` returns cached context if fresh (<60s), else fetches. `refreshDeviceContextLive(deviceId)` fetches live and updates cache. `invalidateDeviceContext(deviceId)` clears cache.
- **Instant wizard loading**: All wizards (Interface, Service, VRF, BGP, IGP) open instantly with cached data. If no fresh cache exists, the wizard renders immediately with a "Loading..." state, then fetches context in the background and re-renders when ready.
- **Cross-wizard awareness**: `recordWizardChange(deviceId, changeType, details)` logs wizard changes to `_wizardChangeLog`. `getDeviceContext()` merges pending changes into the returned context so the next wizard sees updated free interfaces, next EVI/bundle numbers, etc. Changes persist for 5 minutes. Devices with pending changes show a "changed" badge in the device selector.
- **Context panel**: Collapsible panel at top of each wizard. Compact visual bar for interface counts (phys, bundle, lo, sub-if), LLDP chips with neighbor tooltips, color-coded status (green=has data, orange=partial, red=no SSH). System line: `System | AS | RID`. "Refresh Live" fetches over SSH.

### VRF / L3VPN Wizard (5 Steps)

The VRF wizard creates L3VPN VRF instances via `build_service_config(service_type='vrf')` which delegates to `_generate_vrf_config` from interactive_scale. Steps: VRF Naming (prefix, start, count, description) -> Interface Attachment (optional, sub-interfaces from context) -> BGP & Route Targets (enable BGP, AS, router-id, RT mode same_as_rd/custom) -> Review (config preview, validation) -> Push. Uses `POST /api/config/generate/services` with `service_type: 'vrf'` and params: `attach_interfaces`, `interface_list`, `interfaces_per_vrf`, `enable_bgp`, `bgp_config`, `rt_config`.
- **DNAAS device handling**: DNAAS devices (NCM/NCF/NCC/LEAF/SPINE) are excluded from wizard device selectors. If a DNAAS device does appear in a wizard, LLDP suggestions are disabled (`ctx._isDnaas = true`).
- **Suggestion chips**: `ScalerGUI.renderSuggestionChips(items, { type, onSelect })` renders clickable chips. Types: `lldp` (cyan), `free` (green), `config` (orange), `smart` (purple). Items may have `target` for routing onSelect (e.g. `target: 'evi'` or `target: 'asn'`). Bundle member chips use toggle mode: click to add/remove, `.chip-selected` for selected state.

### Interface Wizard Architecture (7 Steps)

The Interface Wizard creates sub-interfaces on existing physical/bundle parent interfaces. Only `subif` type is exposed in CLI and GUI (physical interface creation is not supported -- they are hardware-defined). Steps use `stepBuilder` for dynamic composition:

| Type | Steps (in order) | Count |
|------|-------------------|-------|
| **Sub-interface** | Type → Parent Selection → Mode & Features → Encap → Review → Decision → Push | 7 |
| **GE100/GE400/GE10** | Type → Location → Mode & Features → Encap → Review → Push | 6 |

When the user changes the type in Step 0 and clicks Next, the WizardController calls `stepBuilder(data)` to recompose the step array, dependencies, and keys. The step indicator re-renders with only the relevant dots.

**Mode & Features step** (sub-interface): Interface Mode selector (L2 vs L3). L2 mode: l2-service enabled, hides IP/L3 features. L3 mode: IP addressing (IPv4/IPv6/dual, multiple step modes), MPLS, Flowspec, BFD, MTU, Description.

**Dual-stack IP**: When `ipVersion=dual`, separate IPv4 and IPv6 start/prefix fields. Params: `ip_start`, `ip_prefix` (IPv4), `ipv6_start`, `ipv6_prefix` (IPv6).

**Backend parameter contract** (`POST /api/config/generate/interfaces`): `interface_type`, `start_number`, `count`, `create_subinterfaces`, `subif_vlan_start`, `vlan_mode` (single/qinq), `outer_vlan_start`, `inner_vlan_start`, `l2_service` (physical only), `ip_enabled`, `ip_version`, `ip_start`, `ip_prefix`, `ipv6_start`, `ipv6_prefix`, `ip_mode` (per_subif/per_parent/unique_subnet), `mpls_enabled` (physical only), `flowspec_enabled` (physical only), `bundle_members`, `lacp_mode` (active/passive/static), `slot`, `bay`, `port_start`, `mtu` (physical only), `bfd` (physical only), `description`.

**Step re-editing**: `WizardController` supports `stepDependencies`, `stepKeys`, and `skipIf`. When going back and changing a step, dependent steps are invalidated (their collected keys cleared). The "Next" button shows "Update" when re-visiting a prior step. Steps with `skipIf: (data) => bool` are auto-skipped during forward/backward navigation.
- **Device selector alignment**: `openDeviceSelector` uses `_getCanvasDeviceObjects()` to get canvas devices with their SSH credentials. Devices with SSH configured appear first; devices without SSH appear greyed out with "Set SSH first". DNAAS devices are excluded.

---

## 🧩 Modular Architecture

The topology editor uses a modular architecture with wrapper modules that provide clean APIs.

### Module Overview

#### Foundation Layer (load first)
| Module | Class | Property | Purpose |
|--------|-------|----------|---------|
| `topology-errors.js` | ErrorBoundary | `window.ErrorBoundary` | Crash protection & recovery |
| `topology-clipboard-utils.js` | (IIFE) | `window.safeClipboardWrite` | Safe clipboard for HTTP (non-secure) contexts; use instead of `navigator.clipboard` when app is accessed via server IP |
| `topology-registry.js` | TopologyRegistry | `window.TopologyRegistry` | **Feature routing - check first!** |
| `topology-events.js` | TopologyEventBus | `editor.events` | Event pub-sub system |
| `topology-geometry.js` | TopologyGeometry | `window.TopologyGeometry` | Math/geometry utilities |
| `topology-platform-data.js` | PlatformData | `editor.platformData` | Platforms & transceivers |

#### Core Layer
| Module | Class | Property | Purpose |
|--------|-------|----------|---------|
| `topology-input.js` | InputManager | `editor.input` | Input state machine |
| `topology-files.js` | FileManager | `editor.files` | Auto-save, crash recovery, session tracking |
| `topology-file-ops.js` | FileOps | `window.FileOps` | Save/load/export, bug topologies, custom sections, clear canvas |
| `topology-drawing.js` | DrawingManager | `editor.drawing` | Canvas rendering |
| `topology-history.js` | HistoryManager | `editor.history` | Undo/redo |

#### Object Managers
| Module | Class | Property | Purpose |
|--------|-------|----------|---------|
| `topology-text.js` | TextManager | `editor.text` | Text handling |
| `topology-shapes.js` | ShapeManager | `editor.shapes` | Shape handling |
| `topology-devices.js` | DeviceManager | `editor.devices` | Device management |
| `topology-links.js` | LinkManager | `editor.links` | Links & BUL chains |

#### UI Layer
| Module | Class | Property | Purpose |
|--------|-------|----------|---------|
| `topology-ui.js` | UIManager | `editor.ui` | Toolbars & panels |
| `topology-menus.js` | MenuManager | `editor.menus` | Context menus |
| `topology-minimap.js` | MinimapManager | `editor.minimapMgr` | Minimap display |
| `topology-link-editor.js` | LinkEditorModal | `editor.linkEditor` | Link details modal |
| `topology-groups.js` | GroupManager | `editor.groups` | Object grouping |
| `topology-toolbar.js` | ToolbarManager | `editor.toolbarMgr` | Toolbar setup |
| `topology-dnaas.js` | DnaasManager | `editor.dnaas` | DNAAS discovery |
| `topology-network-mapper.js` | NetworkMapperManager | `editor.networkMapper` | Recursive LLDP network discovery + auto-layout |

#### Extracted Handlers (Feb 2026 decomposition)
| Module | Global | Purpose |
|--------|--------|---------|
| `topology-context-menu-handlers.js` | `window.ContextMenuHandlers` | Context menus, curve submenus, copy/paste style, layers/device-style submenus |
| `topology-link-details.js` | `window.LinkDetailsHandlers` | Link editor modal, VLAN validation, link details table |
| `topology-shape-methods.js` | `window.ShapeMethods` | Shape creation, hit detection, resize handles, toolbar |
| `topology-selection-popups.js` | `window.SelectionPopups` | Device style palette, link width/style/curve options, LLDP submenu |
| `topology-device-monitor.js` | `window.DeviceMonitor` | Background poll: immediate _tick(false) on init (disk cache), then 5-min _tick(true) (live SSH); populates _stackData, _lldpData, _gitCommit; active NCC resolution for clusters; fires device:context-updated |
| `topology-link-geometry.js` | `window.LinkGeometry` | Link hit detection, distance calculations, BUL chain analysis |
| `topology-text-attachment.js` | `window.TextAttachment` | Text-to-link attachment, nearest link, adjacent text |

#### Mouse Handlers (Feb 2026 decomposition)
| Module | Global | Purpose |
|--------|--------|---------|
| `topology-mouse.js` | `window.MouseHandler` | Thin coordinator - delegates to down/move/up handlers |
| `topology-mouse-down.js` | `window.MouseDownHandler` | Click handling, selection, drag setup, double-tap |
| `topology-mouse-move.js` | `window.MouseMoveHandler` | Drag, link stretch, cursor feedback, collision |
| `topology-mouse-up.js` | `window.MouseUpHandler` | Drag release, link creation, placement, cleanup |

#### Testing
| Module | Class | Property | Purpose |
|--------|-------|----------|---------|
| `topology-tests.js` | TopologyTests | `window.TopologyTests` | Automated test suite |

#### Scaler GUI (modular bundles, 2026-03-23)

The scaler UI is split from the former monolith (`scaler-gui.js.bak` backup). **Core** defines `const ScalerGUI = { ... }` and assigns `window.ScalerGUI`; extension scripts call `Object.assign(window.ScalerGUI, { ... })` inside an IIFE. **`scaler-gui-init.js`** runs last and registers `DOMContentLoaded` -> `ScalerGUI.init()`.

| Script (load order) | Role |
|----------------------|------|
| `scaler-gui.js` | State, shared utilities, `WizardController`, device-context cache + shared step builders (`_buildPushStep`, `_buildDecisionStep`, ...), panels, main menu, `handleMenuAction`, `showNotification`, `escapeHtml` |
| `scaler-gui-history.js` | Wizard run history panel, commits panel |
| `scaler-gui-devices.js` | Canvas device list helpers (`_getWizardDeviceList`, ...), device manager, device selector, sync-all, quick-load, compare/sync/delete/batch/templates/add-device |
| `scaler-gui-wizards-network.js` | Interface, service, VRF, bridge-domain, multihoming wizards |
| `scaler-gui-wizards-routing.js` | Routing policy, BGP, IGP wizards |
| `scaler-gui-wizards-security.js` | XRAY settings, FlowSpec, FlowSpec VPN, system config, mirror wizards |
| `scaler-gui-progress.js` | `showProgress` (WebSocket job UI), `_analyzeCommitError` |
| `scaler-gui-upgrade.js` | Upgrade failure/active banners, `_checkRunningUpgrades`, image upgrade / scale / stag wizards, `ScalerAPI.imageUpgrade` / `stagCheck` / `scaleUpDown` patches |
| `scaler-gui-init.js` | `DOMContentLoaded` -> `ScalerGUI.init()` |

**Load order matters**: `scaler-gui-progress.js` must load before `scaler-gui-upgrade.js` because `init()` calls `_checkRunningUpgrades()` which uses `showProgress`. Wizard bundles: `wizards-network` then `wizards-routing` then `wizards-security` (all extend `window.ScalerGUI`).

#### Scaler bridge backend (FastAPI routers, 2026-03-23)

`topology/scaler_bridge.py` is a thin app factory; route handlers live under `topology/routes/`:

| Module | Role |
|--------|------|
| `routes/bridge_helpers.py` | Shared helpers (device resolution, SSH, config summaries, push job persistence, device context for wizards) |
| `routes/_state.py` | `_push_jobs`, `_push_jobs_lock` |
| `routes/ssh.py` | `/api/ssh*`, `/api/ssh-pool/*`, WebSocket `/api/terminal/ws` |
| `routes/config.py` | `/api/config/*`, `/api/mirror/*`, delete-hierarchy options |
| `routes/operations.py` | validate, push, jobs, multihoming, stag, scale |
| `routes/upgrade.py` | `/api/operations/image-upgrade/*`, cancel job, startup recovery (`_recover_active_*`) |
| `routes/devices.py` | `/api/devices/*`, `/api/wizard/suggestions` |
| `routes/operations_stub.py` | Catch-all 501 for unimplemented `/api/operations/*` (mounted **last**) |

Regenerate from monolith backup: `python3 topology/scripts/split_scaler_bridge.py` (reads `scaler_bridge.py.bak_split` or `scaler_bridge.py`).

**Regenerate splits** (after editing `scaler-gui.js.bak`): `python3 topology/scripts/split_scaler_gui.py` (writes `scaler-gui.js` and the bundle files).

**Adding a new wizard**: implement `openFooWizard` on `ScalerGUI` in the appropriate bundle (or `scaler-gui-wizards-<domain>.js`), add a `data-action` / `handleMenuAction` entry in core, and bump `?v=` in `index.html` for every touched JS/CSS file.

### Using Modules

All modules use constructor injection and delegate to the main editor:

```javascript
// Modules receive the editor instance
class DeviceManager {
    constructor(editor) {
        this.editor = editor;
    }
    
    // Methods delegate to editor
    getAll() {
        return this.editor.objects?.filter(obj => obj.type === 'device') || [];
    }
}
```

### Accessing Modules

```javascript
// From editor instance
const editor = window.topologyEditor;

// Device operations
editor.devices.getAll();
editor.devices.addAtPosition('SA-40C', 100, 200);
editor.devices.getById('device-1');

// Link operations
editor.links.getAll();
editor.links.analyzeBULChain(link);
editor.links.isHead(link);

// UI operations
editor.ui.showDeviceToolbar(device);
editor.ui.hideAllToolbars();

// Menu operations
editor.menus.showContextMenu(x, y, obj);
```

### Script Load Order

Modules must load BEFORE `topology.js`:

```html
<!-- Foundation -->
<script src="topology-events.js"></script>
<script src="topology-geometry.js"></script>
<script src="topology-platform-data.js"></script>

<!-- Core Services -->
<script src="topology-files.js"></script>
<script src="topology-file-ops.js"></script>
<script src="topology-drawing.js"></script>

<!-- Object Managers -->
<script src="topology-text.js"></script>
<script src="topology-shapes.js"></script>
<script src="topology-devices.js"></script>
<script src="topology-links.js"></script>

<!-- UI Layer -->
<script src="topology-ui.js"></script>
<script src="topology-menus.js"></script>
<script src="topology-minimap.js"></script>
<script src="topology-link-editor.js"></script>
<script src="topology-groups.js"></script>
<script src="topology-toolbar.js"></script>
<script src="topology-dnaas.js"></script>

<!-- Main (loads last, uses all modules) -->
<script src="topology.js"></script>

<!-- Tests (optional) -->
<script src="topology-tests.js"></script>
```

### Running Tests

```javascript
// Run all tests
TopologyTests.runAll();

// Run specific module tests
TopologyTests.runModule('devices');
TopologyTests.runModule('links');
TopologyTests.runModule('ui');
TopologyTests.runModule('linkeditor');
TopologyTests.runModule('stats');

// View module diagnostics
ModuleStats.print();          // Print formatted stats table
ModuleStats.getSummary();     // Get stats object
ModuleStats.getHealth();      // Get 'healthy', 'degraded', or 'critical'
```

---

## 🔗 BUL (Bound Unbound Link) Chain System

### Core Concepts

**UL (Unbound Link)**: A link not attached to devices at both ends. Has two endpoints: `start` and `end`.

**BUL (Bound Unbound Link)**: Multiple ULs merged together into a chain.

**TP (Terminal Point)**: A FREE endpoint - not attached to device AND not connected to another link.

**MP (Merge Point)**: Where two ULs connect - the shared point between parent and child.

### Merge Relationships

Each link can have:
- `mergedWith`: Points to CHILD link (this link is parent)
- `mergedInto`: Points to PARENT link (this link is child)

**A link can only have ONE child (one `mergedWith`)!**

```
Chain: HEAD -- MP1 -- MIDDLE -- MP2 -- TAIL

HEAD:   mergedWith → MIDDLE,  mergedInto = null
MIDDLE: mergedWith → TAIL,    mergedInto → HEAD  
TAIL:   mergedWith = null,    mergedInto → MIDDLE
```

### Key Properties in mergedWith

```javascript
mergedWith = {
    linkId: 'link_123',           // Child link ID
    connectionPoint: {x, y},       // MP position (CLONED, not shared!)
    connectionEndpoint: 'start',   // Which endpoint of PARENT connects to child
    childConnectionEndpoint: 'end', // Which endpoint of CHILD connects to parent
    parentFreeEnd: 'end',          // Which endpoint of PARENT is FREE
    childFreeEnd: 'start',         // Which endpoint of CHILD is FREE
    mpNumber: 1                    // MP number in chain (MP-1, MP-2, etc.)
}
```

### CRITICAL: Endpoint Detection

Use `isEndpointConnected(link, endpoint)` to check if an endpoint is connected:
- Checks BOTH `mergedWith.connectionEndpoint` AND `mergedInto.childEndpoint`
- Returns `true` if endpoint is an MP (connected to another link)
- Returns `false` if endpoint is a TP (free)

**NEVER use only `device1`/`device2` checks - must also check merge connections!**

```javascript
// CORRECT: Check device AND merge connection
const isStartFree = !link.device1 && !this.isEndpointConnected(link, 'start');

// WRONG: Only checks device
const isStartFree = !link.device1;  // Missing merge check!
```

### Extending from TP (Link-from-TP Mode)

When user clicks a TP to extend the chain:

1. **APPEND** (sourceLink has no child): sourceLink becomes parent of newUL
   - `sourceLink.mergedWith → newUL`
   - `newUL.mergedInto → sourceLink`

2. **PREPEND** (sourceLink already has a child): newUL becomes parent (new HEAD)
   - `newUL.mergedWith → sourceLink`
   - `sourceLink.mergedInto → newUL`

**NEVER overwrite existing `mergedWith` - it breaks the chain!**

### Finding All Links in Chain

```javascript
const allLinks = this.getAllMergedLinks(link);
// Traverses both mergedWith (children) and mergedInto (parents)
// Returns array of all connected links
```

---

## 🎯 Hitbox & Selection Rules

### Link Hit Detection

Use `_checkLinkHit(x, y, obj)` which:
- Calculates visual link width based on zoom
- Uses screen-pixel tolerance for consistent feel
- Returns distance to link (-1 if not hit)

**For BUL chains**: TAIL/MIDDLE links delegate hit detection to HEAD.

### Finding Closest Object

`findObjectAt(x, y)` accumulates ALL links within clicking distance and returns the **closest** one, not just the first found.

### Selection Priority (Visual = Hitbox)

Objects are selected based on visual stacking order: higher-layer objects have priority over lower-layer ones. Within the same layer, priority is: text > device > link > shape. Only `mergedToBackground` shapes are always lowest priority. This ensures "what you see is what you click."

---

## 🎨 UI/Style Conventions

### Global Single-Overlay Mutex (`topology-panel-mutex.js`, 2026-04-22)

Problem: the AI Assistant drawer (right), the Scaler CONFIG stack (right), the in-browser terminal (bottom), the debugger panel, BD legend etc. each knew how to open/close *themselves* but had no awareness of one another. Opening AI + Scaler + Terminal all at once produced an unreadable stack of overlapping panels.

`topology-panel-mutex.js` is a tiny coordinator that exposes:

```js
window.TopoPanelMutex.register(name, { close, isOpen? }); // once at module load
window.TopoPanelMutex.markOpen(name);   // call AT START of a panel's open()
window.TopoPanelMutex.markClosed(name); // call when a panel finishes closing
window.TopoPanelMutex.closeAll(except?);// force-release
window.TopoPanelMutex.getActive();      // current slot name or null
```

Semantics: **one slot at a time**. `markOpen('ai')` iterates the registry and calls every other registered panel's `close()` before recording `'ai'` as the active slot. `close()` callers are wrapped in `try/catch` so one panel's bug cannot freeze the others. `isOpen` is used to skip the close() call when a panel is already dormant (cheap no-op).

Wired participants (as of 2026-04-22):

| Slot name   | Module                 | `isOpen()` predicate                                | `close()` action                              |
|-------------|------------------------|-----------------------------------------------------|-----------------------------------------------|
| `ai`        | `topology-ai.js`       | drawer has `.open` class                            | `classList.remove('open')` + launcher reset   |
| `scaler`    | `scaler-gui.js`        | `state.activePanels` non-empty                      | `closeAllPanels()` on the Scaler stack         |
| `terminal`  | `topology-terminal.js` | panel element exists and not minimized              | `close()` (closes every tab)                  |
| `debugger`  | `debugger.js`          | `instance.enabled === true`                         | `instance.hide()`                             |

Existing pairwise mutex logic (AI ↔ Bugs ↔ Share, DNAAS ↔ NetMapper ↔ Topologies) is untouched — it runs BEFORE the global mutex and stays authoritative for those dropdowns. The global mutex only adds awareness **across** the big right/bottom overlays. This means opening Scaler CONFIG now closes the AI drawer; opening the AI drawer closes every Scaler panel; opening the terminal closes both; opening the debugger closes all three.

Registration order in `index.html` is critical: `topology-panel-mutex.js` **must** load before every participant (AI, Scaler, Terminal, Debugger) or `register()` calls silently become no-ops. It is the first script after the layer-0 foundation line.

Cache bust: `?v=20260422c` on `topology-panel-mutex.js`, `topology-ai.js`, `scaler-gui.js`, `topology-terminal.js`, `debugger.js`, and `index.html` (flat-copied to `/home/dn/CURSOR/`). No Python restart needed -- pure JS.

### Device Style Buttons
- Active state: **GREEN** gradient (like "Place Device" button)
- Labels: `white-space: nowrap` - no truncation

### Link Style Buttons  
- Active state: **CYAN** gradient

### Button Text
- "Place Device" (not "Add Device")

### Selection Toolbars (Liquid Glass Design)

**Single left-click** on objects shows floating toolbars (no right-click needed):

| Object | Function | Toolbar ID | Trigger |
|--------|----------|------------|---------|
| Text | `showTextSelectionToolbar(textObj)` | `text-selection-toolbar` | Left-click to select |
| Device | `showDeviceSelectionToolbar(device)` | `device-selection-toolbar` | Left-click to select |
| Link | `showLinkSelectionToolbar(link, clickPos?)` | `link-selection-toolbar` | Left-click to select |
| Shape | `showShapeSelectionToolbar(shape)` | `shape-selection-toolbar` | Left-click to select |

**Toolbar Behavior:**
- Appears 150ms after selection (prevents showing during drag)
- Hidden when: dragging starts, clicking empty space, returning to base mode
- **Re-appears after drag ends** at the new object position
- Call `hideAllSelectionToolbars()` to hide all toolbars programmatically

**Toolbar Positioning:**
- **Device**: Below the device center (like text toolbar)
- **Link**: At the click location (where user clicked on the link)
- **Text**: Below the text center

**Toolbar Design Pattern:**
```javascript
toolbar.style.cssText = `
    position: fixed;
    background: rgba(0, 0, 0, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 5px 8px;
    backdrop-filter: blur(20px) saturate(150%);
    display: flex;
    gap: 2px;
`;
```

**Hide All Toolbars:**
```javascript
this.hideAllSelectionToolbars(); // Hides text, device, and link toolbars
```

**Device Toolbar Options:** SSH, Rename, Color, Style, Duplicate, Lock, Layer, Delete
- SSH → Click: always opens SSH dialog (`showSSHAddressDialog`) for credentials, probe methods, and settings. The small terminal button drawn on the canvas device (top-left when selected) calls `openTerminalToDevice(device)` for direct iTerm connect.
- Rename → `showRenamePopup(device)`
- Color → `showColorPalettePopup(device, 'device')`
- Style → `showDeviceStylePalette(device)`
- Duplicate → `duplicateSelected()`
- Lock → toggle `device.locked`
- Layer → Layer widget (down/up arrows, badge with dropdown: Bring to Front, Move Forward, Move Backward, Send to Back, Reset to Default). Uses `editor.getObjectLayer`, `editor.moveObjectForward/Backward`, `editor.moveObjectToFront/ToBack`, `editor.resetObjectLayer`. Same widget in device, link, shape, text toolbars.
- Delete → `deleteSelected()`

**Device Toolbar Tables (LLDP, Stack, Git Commit) and DeviceMonitor (Mar 2026)**

Device toolbar submenu (Stack button) opens LLDP Table, Stack Table, and Git Commit. All use cache-first open for instant display when data exists on the device object.

- **Cache-first open**: Stack dialog checks `device._stackData`; LLDP checks `device._lldpData`; Git Commit checks `device._gitCommit`. If present, render immediately with timestamp (no toast). "Refresh" fetches fresh data via fallback chain (cache first, then SSH). Refresh button toasts: success only; errors toast on load failure.
- **DeviceMonitor** (`topology-device-monitor.js`): Singleton that polls all canvas devices with SSH credentials. On init: runs `_tick(false)` after 2s delay (reads from operational.json, ~50ms/device). Then every 5 min: `_tick(true)` (live SSH via `ScalerAPI.getDeviceContext`). Stores results on `device._stackData`, `device._lldpData`, `device._gitCommit` with timestamps. For cluster devices (subType cluster, nccN pattern): uses `_resolveActiveNcc(device)` via `DnaasHelpers._findActiveNcc` to target active NCC IP. Batches: 5 devices concurrent, 2s delay between batches (scales to 1000+ devices). Fires `device:context-updated` CustomEvent so open dialogs auto-refresh.
- **AbortController**: Stack and LLDP dialogs use `AbortController` when switching devices; in-flight fetches are aborted to avoid stale data.
- **Git Commit**: Cursor-style code-block popup with SVG copy icon (#ico-copy), checkmark feedback on copy, `safeClipboardWrite`. Handles 502 with "Discovery API unavailable". Caches `device._gitCommit` and `device._gitCommitFetchedAt`.
- **serve.py**: `/api/dnaas/device-gitcommit` proxy timeout 15s (was 300s). Startup health check logs discovery_api and scaler_bridge reachability. 502 responses include upstream path in detail.
- **topology-notifications.js**: `_FRIENDLY_502_EXACT` includes `/api/dnaas/device-gitcommit` so 502 from this endpoint does not show raw error toast (caller shows friendly message).

**Link Toolbar Options:** Add Text, Color, Width, Style, Curve, Duplicate, Delete
- Add Text → `showAdjacentTextMenu(link)`
- Color → `showColorPalettePopup(link, 'link')`
- Width → `showLinkWidthSlider(link)`
- Style → `showLinkStyleOptions(link)`
- Curve → `showLinkCurveOptions(link)`
- Duplicate → `duplicateSelected()`
- Delete → `deleteSelected()`

---

## ✅ Before Making Changes

1. Read this file
2. `grep` for existing patterns in codebase
3. Check related `.md` files for context
4. Read the specific code section before modifying

## ✅ After Making Changes

1. Verify braces are balanced:
   ```bash
   python3 -c "js=open('topology.js').read(); print('✓' if js.count('{')==js.count('}') else '❌')"
   ```
2. Test the change in browser
3. Update this file with new patterns/fixes

---

## Concurrency Hardening (Waves 1-5, Apr 2026)

Full multi-user concurrency + observability overhaul landed across 15 subtasks in 5
waves. Goal: let 8+ users each operate on 10+ devices simultaneously without cross-
contamination, shared SSH sessions, blocked WebSocket broadcasts, or resource
exhaustion. Validated by `/tmp/device_concurrency_smoke.py` (160 jobs, 0 errors,
p99 acquire 24 ms, 0 invariant violations).

### Wave 2-3: Per-device serialization + frontend backoff
- `routes/_device_scheduler.py` -- `DeviceOpScheduler` with per-`mgmt_ip` exclusive
  lock; `exclusive()` context manager also wraps push + upgrade critical sections.
  Queue-position reporting via the `on_progress` callback (Wave 4.3) surfaces
  `queue N/M (waiting Ns)` terminal lines while callers are blocked.
- `routes/_live_coalescer.py` -- `LiveCoalescer` (90 s default TTL) merges
  simultaneous `get(key, fetch)` callers so only ONE upstream fetch runs per key
  per TTL window. Wired into `_get_device_context` for show-command coalescing.
- `topology-device-monitor.js` -- honours `Retry-After`, pauses on
  `visibilitychange` (hidden tab), exponential backoff on 429/503.
- `routes/ssh.py` -- terminal WS read loop rewritten from 30 ms polling to a
  dedicated background thread blocking on `select()`, feeding an `asyncio.Queue`
  (drop-oldest on overflow).
- `api/event_bus.py` -- per-WS bounded `asyncio.Queue(128)` + dedicated writer
  task. Slow clients never block publishers or other subscribers on the same user.
- WebSocket keepalive: server pings every 20 s, disconnects after 2 missed pongs.
  Client code in `topology-device-events.js` + `topology-terminal.js` responds
  with pong frames.

### Wave 4: Global concurrency cap + observability
- `DeviceOpScheduler.global_upgrade_slot()` -- global `threading.Semaphore` caps
  concurrent upgrades across ALL devices. Env `TP_GLOBAL_UPGRADE_SLOTS` (default
  4). Callers nest this outside the per-device lock.
- `GET /api/health/concurrency` -- aggregated snapshot (scheduler state, live
  coalescer metrics, event-bus queue depth per WS, push/upgrade job counts by
  status + type, event-bus backend kind). Exempt from JWT auth so monitoring
  agents can poll anonymously.

### Wave 5: Pluggable backends + per-user pool keying
- `api/event_bus_backend.py` -- `EventBusBackend` interface with
  `InProcessBackend` (default no-op) and `RedisPubsubBackend` (stub). Env
  `TP_EVENT_BUS_BACKEND=redis` + `TP_REDIS_URL` enables cross-worker fan-out;
  publishers tag events with a per-process `ORIGIN_ID` so they ignore their own
  echo. Gracefully degrades to no-op if `redis` package or broker unavailable.
- `routes/_job_store.py` -- `JobStore` interface with `InMemoryJobStore` facade
  over the existing `_push_jobs` dict + lock. `_push_jobs_lock` upgraded
  `Lock` -> `RLock` so compound `with store.lock():` blocks can safely call
  facade methods. `FileSnapshotJobStore` stub periodically dumps to disk. Env
  `TP_JOB_STORE` selects the backend. All existing `_push_jobs[...]` call sites
  keep working unchanged -- facade shares the same dict + lock.
- `routes/_device_comm.py` -- every helper (`run_show`, `run_show_ip`,
  `run_show_batch`, `fetch_running_config`, `get_session`) now resolves
  `app_user` from the `current_app_user` ContextVar and threads it into
  `_ssh_pool.get_client(...)` and `_ssh_pool.release(...)`. Prevents two users
  from riding on a pooled SSH client authenticated with the other's credentials.

### Wave 6: Scale to 100+ concurrent users (Apr 19 2026)
Wave 6 hardens the stack against burst loads of 100+ simultaneous users by
adding admission controls, bounded workers, and observability. Concrete
numbers from `/tmp/wave6_100user_storm.py` (100 users / 100 devices):
**p50 444ms, p99 738ms** with a 20-slot global cap, zero invariant breaches,
50-worker executor instead of 100+ raw threads.

- **Wave 6.1 -- Global push slot semaphore.** `DeviceOpScheduler.global_push_slot()`
  parallels the upgrade cap. Env `TP_GLOBAL_PUSH_SLOTS` (default 20) caps total
  simultaneous SSH/commit sessions across ALL devices. Acquired OUTSIDE the
  per-device lock so a burst across 100 different devices still throttles
  through the configured slot count. Held for the full dry_run -> commit/cancel
  round-trip (stashed in `_push_slot_handle` inside the job dict and released
  by `push_commit`/`push_cancel`/`delete_job`/finally-safety-net).
- **Wave 6.2 -- Bounded push/upgrade executors.** `routes/_worker_pool.py`
  replaces per-job `Thread(..., daemon=True).start()` with two purpose-built
  `ThreadPoolExecutor` pools. Env `TP_PUSH_EXECUTOR_SIZE` (default 50) and
  `TP_UPGRADE_EXECUTOR_SIZE` (default 10). Wrappers preserve the `app_user`
  ContextVar so `_get_credentials()` sees the right user on reused workers.
  Back-pressure is enforced upstream by Wave 6.1/6.4/6.5, so the pool's
  internal queue only holds already-admitted jobs.
- **Wave 6.3 -- SSH pool capacity.** `SSHConnectionPool._max_connections` is
  env-tunable via `TP_SSH_POOL_MAX` (default 200, up from 50). At 100 users
  each touching 1-2 devices, the old 50-entry LRU thrashed and cost ~1-2s
  per reconnect. `health_stats()` method surfaces capacity / fill /
  per-user / per-IP for monitoring.
- **Wave 6.4 -- Per-user push cap.** `scheduler.reserve_user_push(owner)` /
  `release_user_push(owner)` counter; raises `PerUserLimitError` beyond
  `TP_PER_USER_PUSH_MAX` (default 5). HTTP layer converts this to
  `429 Too Many Requests` + `Retry-After` header. Counter is released in
  the worker's finally block unless the job is still `awaiting_decision`
  (dry_run path), in which case commit/cancel endpoints release it.
- **Wave 6.5 -- Pre-queue rejection.** `scheduler.check_device_queue_capacity(mgmt_ip)`
  raises `DeviceBusyError` if the per-device queue is >= `TP_DEVICE_QUEUE_MAX`
  (default 10). HTTP layer converts to `503 Service Unavailable` +
  `Retry-After` (dynamic: `max(30, min(300, depth * 15))`). Check happens
  BEFORE job row creation so clients fail fast instead of silently queuing
  for minutes.
- **Wave 6.6 -- Observability.** `/api/health/concurrency` snapshot now
  exposes `global_pushes`, `per_user_pushes`, `device_queue`,
  `worker_pools`, and `ssh_pool` sub-objects with caps, in-flight, peak,
  rejections, and per-user/per-ip breakdowns.

#### Wave 6 env knobs (summary)
| Env var | Default | Purpose |
|---------|---------|---------|
| `TP_GLOBAL_PUSH_SLOTS` | 20 | Max simultaneous SSH+commit sessions |
| `TP_PER_USER_PUSH_MAX` | 5 | Max in-flight pushes per authenticated user |
| `TP_DEVICE_QUEUE_MAX` | 10 | Max waiters per device before 503 |
| `TP_PUSH_EXECUTOR_SIZE` | 50 | Bounded push worker pool size |
| `TP_UPGRADE_EXECUTOR_SIZE` | 10 | Bounded upgrade worker pool size |
| `TP_SSH_POOL_MAX` | 200 | Paramiko connection cache capacity |
| `TP_UPGRADE_MAX_CONCURRENT` | 4 | (Wave 4) global cap on upgrades |

Set any env to `0` to disable the corresponding cap (not recommended in
production; only use for diagnosing whether a cap is the cause of a slowdown).

### Cross-cutting invariants (enforced by `topology/tests/concurrency/*`)
1. No two concurrent critical sections for the SAME mgmt_ip.
2. Active critical sections <= global upgrade slot cap.
3. Active SSH+commit sessions <= `TP_GLOBAL_PUSH_SLOTS` (Wave 6.1).
4. Per-user in-flight pushes <= `TP_PER_USER_PUSH_MAX` (Wave 6.4).
5. Per-device queue depth <= `TP_DEVICE_QUEUE_MAX` (Wave 6.5).
6. LiveCoalescer serves `fetch` at most once per device per TTL window.
7. Executor threads alive <= `TP_PUSH_EXECUTOR_SIZE` (Wave 6.2).
8. No exceptions leak from worker threads.
9. p99 scheduler acquire wait <= 5 s (typically <50 ms).
10. p99 end-to-end push wait <= 3 s at 100 users with default caps (Wave 6.7
    measured 738 ms).
11. Owner identity propagation is whitespace-normalised but case-preserved;
    scheduler counters, SSH pool keys, audit log owner field, and job dict
    owner all funnel through `normalize_owner*` (Wave 7.2).
12. Dry-run held sessions never outlive `TP_DRYRUN_TTL_S` (default 600 s);
    the reaper releases all four primitives + SSH channel on timeout and
    marks the row `status=reaped` so commit/cancel 410 cleanly (Wave 7.1).
13. `/api/operations/push` requires a non-empty owner and a write-role
    (`user` or `admin`) whenever the bridge's `_multiuser_available` flag
    or `TP_AUTH_ENFORCE=always` is set; viewers/unauthenticated get
    401/403 with audit log entries (Wave 7.6).
14. Per-user rows in `_push_jobs` <= `TP_PER_USER_JOB_MAX` (Wave 7.4);
    eviction targets oldest-COMPLETED rows, 429s only if every slot is in
    flight.
15. `SSHConnectionPool._evict_lru()` and the keepalive loop NEVER remove
    an entry with `in_use > 0`; when the pool is full and all entries are
    busy it grows past the cap rather than killing an in-flight command
    (Wave 7.7).

### Wave 7: Multi-user hardening (Apr 22 2026)
Wave 7 closes the gaps revealed by the Wave 6 storm test and a deep
audit for owner-identity propagation, resource leaks, and race
conditions. Validated by the four-suite `topology/tests/concurrency/`
regression (85 checks total, all green). Summary:

- **Wave 7.1 - Stale dry-run reaper.** `routes/_reaper.py` daemon
  scans `_push_jobs` every `TP_REAPER_INTERVAL_S` (60 s). Any job with
  `awaiting_decision=True` older than `TP_DRYRUN_TTL_S` (600 s) is
  flipped to `status=reaped`, its SSH channel is `abort`-ed and
  closed, and scheduler token / global slot / per-user counter are
  released. `push_commit` / `push_cancel` on a reaped job return
  HTTP 410 `session_reaped`. Two-pass scan (Wave 7.12) keeps lock
  hold time O(stale) instead of O(N).
- **Wave 7.2 - Canonical owner normalisation.** `_state.normalize_owner`
  (strict) / `normalize_owner_lax` (fallback to `default`) funnel
  every owner string through a single canon. Whitespace trimmed, case
  preserved (security decision: `Admin` != `admin`). Scheduler
  counters, SSH pool keys, and audit log all use the same form, so
  ` alice `, `alice`, and `alice ` share one per-user cap bucket.
- **Wave 7.3 - submit_push rollback.** If `_worker_pool.submit_push()`
  raises (pool shut down, queue saturated), we drop the job row and
  release the per-user reservation before returning 503, instead of
  leaking a phantom job that will never run.
- **Wave 7.4 - Per-user job quota.** `_enforce_per_user_job_quota(owner)`
  caps `_push_jobs` rows per owner at `TP_PER_USER_JOB_MAX` (100).
  Evicts oldest-DONE rows; 429s only if every slot is a live in-flight
  job.
- **Wave 7.5 - Append-only audit log.** `routes/_audit_log.py` writes
  JSONL to `~/.topology_audit.log` with automatic rotation at 100 MB.
  Deep-redacts `password`/`token`/`secret`/`pwd`/`auth*`/`api_key`
  fields in nested dicts. Records: `push_start`, `push_complete`,
  `push_failed`, `push_rejected`, `push_commit`, `push_cancel`,
  `push_delete`, `push_reaped`, plus the matching `_rejected` events
  with owner, role, device_id, mgmt_ip, job_id.
- **Wave 7.6 - Pre-queue authorization.** `routes/_authz.authorize_push`
  runs BEFORE any scheduler reservation. Unauthenticated -> 401
  (mode-aware), viewer -> 403, unknown device -> 404, then the queue
  caps. Mode probe order (Wave 7.11): `TP_AUTH_ENFORCE` env (`always`
  / `never`) -> `scaler_bridge._multiuser_available` flag ->
  `api.auth.service` import probe. Fixes the prior hole where any
  authenticated caller could push to ANY device_id.
- **Wave 7.7 - SSH pool in-use refcount.** Each pool entry gains
  `in_use` counter incremented by `get_client` / decremented by
  `release`. `_evict_lru` considers only idle entries; keepalive loop
  skips in-use entries; health snapshot exposes `in_use_total` and
  `in_use_by_user`. Prevents LRU from tearing down a client mid-
  paramiko command under pool pressure.
- **Wave 7.8 - Exception-path cleanup.** If a dry_run worker raises
  after stashing resources in the job dict, the exception handler
  re-claims `_sched_token` / `_push_slot_handle` / `_user_push_reserved`
  so the finally block releases them canonically instead of leaving
  them dangling as if the user were still deciding.
- **Wave 7.9 - Integration regression suite.** `topology/tests/
  concurrency/test_wave7_integration.py` runs the whole admission
  chain (authz -> device-queue cap -> per-user cap -> job quota ->
  scheduler -> worker pool -> reaper) via a FastAPI `TestClient` with
  a micro middleware simulating JWT. 25 checks. Runner
  `topology/tests/concurrency/run_all.sh` stitches Wave 2 / Wave 6 /
  Wave 7 / Wave 7.9 (85 checks).
- **Wave 7.12 - Audit-ordering / defensive-pop / mgmt-ip drift /
  reaper lock.** (a) `push_start` audit event now emitted BEFORE
  `submit_push()` so the log is always ordered start -> complete.
  (b) `push_commit` / `push_cancel` use `.pop(key, None)` instead of
  `del job[key]` so a racing reaper can't `KeyError` the commit path.
  (c) `_run_push()` reuses the pre-queue mgmt_ip snapshot -- authz
  and Wave 6 caps now decide against the SAME IP the worker will
  target, even if DNS/DB churns in the gap. (d) Reaper scan uses a
  two-pass design (cheap snapshot + per-stale-row flip) so the
  push-jobs lock is held for O(stale) writes instead of O(N) reads.

#### Wave 7 env knobs (summary)
| Env var | Default | Purpose |
|---------|---------|---------|
| `TP_DRYRUN_TTL_S` | 600 | Reaper abandonment threshold (seconds) |
| `TP_REAPER_INTERVAL_S` | 60 | Reaper scan period (seconds) |
| `TP_REAPER_ENABLED` | 1 | Set to 0 to disable reaper daemon |
| `TP_PER_USER_JOB_MAX` | 100 | Max `_push_jobs` rows per owner |
| `TP_AUTH_ENFORCE` | auto | `always`/`never`/`auto` authz mode |
| `TP_AUDIT_LOG_ENABLED` | 1 | Set to 0 to disable audit log writes |
| `TP_AUDIT_LOG_MAX_BYTES` | 100 MB | Rotate log at this size |
| `TP_AUDIT_LOG_MAX_FILES` | 5 | Max rotated generations to keep |

`/api/health/concurrency` now exposes `reaper`, `audit`, and per-user
`ssh_pool.in_use_by_user` to make all four Wave 7 primitives
observable.

---

## Recent Fixes (Jan 2026)

### Honest stack timestamps + remote-access SSH fallback + stale reachability (Apr 20 2026)

**Problem**: User reported that the System Stack popup showed `Last fetched: Apr 20 16:06:31` (looking fresh) while the SSH button failed to open a terminal, with the data in the stack being outdated. Two separate bugs conflated:

1. `topology-stack-dialog.js::updateContent()` set `device._stackCachedAt = Date.now()` unconditionally when the frontend received the response, even when the response was served from the bridge's on-disk `operational.json` cache (which could be hours or days old). The UI thus lied about freshness.
2. `topology-object-detection.js::_openSshUrl()` always dispatched an `ssh://` URL via anchor-click, which invokes the **user's OS SSH handler** (iTerm on macOS). When the topology app is accessed remotely (`http://<server-ip>:8080/`), the user's machine typically cannot route to lab-internal 100.64.x.x / RFC1918 IPs, so the handler silently fails. The server-side stack fetch succeeded via the bridge's SSH pool; the user's Mac could not replicate that path.
3. `topology-device-monitor.js::_refreshOneInner()` set `device._sshReachable = true` whenever `/api/devices/{id}/context` returned 200, even when the bridge internally fell back to cached operational.json because the live SSH failed. The green "SSH OK" indicator on the canvas never aged into stale/unknown.

**Fixes**:

- **(A) Backend: real `stack_fetched_at` timestamp.** `routes/bridge_helpers.py::_get_device_context()` now writes `stack_fetched_at` / `git_commit_fetched_at` into the per-device `operational.json` whenever a live SSH fetch produces fresh stack/git data. When callers use `live=false`, the bridge surfaces the previously-written `stack_fetched_at` (falling back to `connection_probe_at` and then `operational.json` mtime) so the frontend receives the honest device-query time.
- **(A) Frontend: honest timestamp.** `topology-stack-dialog.js::updateContent()` parses `data.stack_fetched_at` and uses it for `device._stackCachedAt` instead of `Date.now()`. The "Queried" row in the dialog now shows the real device-query timestamp with an age suffix (`Apr 8 20:44:35 (12d ago)`).
- **(B) Frontend: loud CACHED badge.** `buildTimestampRow()` renders a yellow `CACHED (age)` pill when `source='cached'`, and a red pill when the age exceeds 10 minutes. Source column is relabeled `cached (disk)` vs `live SSH` with matching colors (amber vs green).
- **(C) Frontend: background live refresh on open.** When the stack dialog opens with cached data and the cached timestamp is older than 5 minutes (or marked as `source=cached`), the dialog immediately fires a background `ScalerAPI.getDeviceContext(live=true, ...)` and updates the table if live SSH succeeds. If live SSH fails, a small amber note is appended to the dialog ("Live refresh failed -- device may be unreachable right now. Showing last cached snapshot.") without blocking or error-toasting.
- **(D) Frontend: remote-access SSH fallback.** `topology-object-detection.js::_openSshUrl()` now detects remote-access deployments and auto-routes to the in-browser web terminal. The helper `_shouldUseWebTerminal(host)` returns true when the browser hostname is NOT localhost AND the target is an RFC1918/CGNAT IP (10/8, 172.16/12, 192.168/16, 100.64/10). In that case `window.TerminalPanel.open({ method: 'ssh_mgmt', ... })` is used instead of the `ssh://` URL handler. A per-user override is persisted under `localStorage['xdn_ssh_launch_pref']` with values `auto` (default), `iterm`, or `webterm`.
- **(E) Frontend: stale reachability indicator.** `topology-device-toolbar.js` now classifies `_sshReachable` into fresh (green outline, <10 min), stale (amber outline, 10 min - 2h), and expired (no outline, >2h). `topology-device-monitor.js::_refreshOneInner()` only flips `_sshReachable = true` when the bridge actually produced fresh stack data (`stack_fetched_at` within 2 minutes) under `live=true`; otherwise the previous state is preserved so it ages into stale.

**Files**:
- Backend: `topology/routes/bridge_helpers.py`
- Frontend: `topology/topology-stack-dialog.js`, `topology/topology-object-detection.js`, `topology/topology-device-toolbar.js`, `topology/topology-device-monitor.js`
- Cache busters: `topology/index.html` -> `?v=20260420a` for all four updated JS files

**Deploy**: mirror all five files to `/home/dn/CURSOR/` (same relative paths); uvicorn's `--reload` picks up the Python change on save.

### SSH method selection + per-user credential persistence + regression guards (Apr 20 2026 — late)

**User complaint**: "RR-SA-2 opens web terminal when iTerm is preferred, PE-4 still won't launch iTerm, credentials aren't persisted per-user+per-token, UI is cluttered."

**Problems** (root cause):

1. `_shouldUseWebTerminal(host)` in `topology-object-detection.js` treated every CGNAT/RFC1918 IP as "remote-access" and routed it to the web terminal, regardless of whether the user's browser was actually on a Mac where iTerm works. On a Mac accessing the lab directly (VPN / on-site), the code still forced web terminal -- exactly opposite of what the user wanted.
2. Credential persistence was **frontend-only**: `saveAddress()` wrote to `device.sshConfig` inside the topology JSON, but there was NO backend endpoint to persist credentials per-user. The bridge's `_get_credentials()` already knew how to read `~/.topology_users/<u>/devices.json`, but nothing wrote to it from the UI. Every operation that used `_get_credentials()` (discovery, LLDP, config push) fell back to `dnroot/dnroot`.
3. The Connect buttons on auto-discovered probe rows only **launched** the terminal -- they never persisted the user's typed credentials. Only the "Save" button did, so any user who clicked "Connect" (the common path) silently lost their credentials on the next operation.

**Fixes**:

- **(A) Platform-aware method selection.** `topology-object-detection.js::_pickLaunchMethod(host, device)` now layers three signals:
 1. Per-device sticky `device.sshConfig.preferredMethod` (highest)
 2. Global user pref `localStorage['xdn_ssh_launch_pref']` (`auto` / `iterm` / `webterm`)
 3. Platform default: Mac/iOS UA -> iTerm, everything else -> web terminal.
 Every decision logs `[SSH] method decision: host=<ip> web=<bool> reason=<why>` to the console so you can see why a given device opened the method it did. `_openSshUrl()` now accepts a `_pendingDevice` hint and consults it via `_pickLaunchMethod` before dispatching the `ssh://` URL.
- **(B) Per-user credential CRUD API.** `topology/api/auth/router.py` adds:
 - `GET /api/auth/me/device-credentials` (list, password redacted as `has_password: bool`)
 - `GET /api/auth/me/device-credentials/{device_id}` (single, password redacted)
 - `PUT /api/auth/me/device-credentials/{device_id}` body `{user, password}` (write)
 - `DELETE /api/auth/me/device-credentials/{device_id}` (remove)
 All four endpoints require JWT auth, scope to the logged-in user, and write atomically (rename-in-place) to `~/.topology_users/<user>/devices.json` with `0600` permissions. `routes/bridge_helpers._get_credentials()` already reads this file, so credentials persist across restarts and propagate to every SSH operation (discovery, config push, LLDP probe, upgrade).
- **(C) SSH dialog calls the new API.** `topology-ssh-dialog.js::saveAddress()` calls `ScalerAPI.saveDeviceCredentials(deviceId, user, password)` after updating the local topology JSON, and shows a `[OK] creds saved` hint inline when the save succeeds. `ScalerAPI.saveDeviceCredentials / getDeviceCredential / deleteDeviceCredential / listDeviceCredentials` helpers in `scaler-api.js` wrap the new endpoints with automatic JWT attachment.
- **(D) Connect buttons auto-persist.** `doConnect()` now silently pushes newly-typed credentials to the backend **before** launching the terminal when the user clicks any per-method Connect button (not just Save). This closes the regression path where users typed creds + clicked Connect and the creds never reached the persistent store.
- **(E) "Connect via" picker in the SSH dialog.** A compact 3-button toggle (Auto / iTerm / Web) writes `device.sshConfig.preferredMethod` and persists it with `editor.saveState()`. Picking `auto` clears the sticky preference and falls back to platform default. Tooltips explain what each option does.

**Regression guards** (run these on every PR that touches SSH or credentials):

- `topology/tests/smoke_ssh_method_matrix.js` -- 16 decision-matrix cases verifying `_pickLaunchMethod` across Mac/iOS/Linux/Windows UAs x auto/iterm/webterm global pref x per-device sticky x TerminalPanel availability. Pure Node.js VM, no network. `node topology/tests/smoke_ssh_method_matrix.js`.
- `topology/tests/smoke_per_user_ssh.py` -- 15-check end-to-end API round-trip over the live proxy on :8080. Covers 401 auth, PUT/GET/list/DELETE, password redaction, 0600 perms, on-disk integrity, user isolation, and the bridge `_get_credentials` lookup. `python3 topology/tests/smoke_per_user_ssh.py`.
- `topology/scripts/audit_topology_state.py` -- persistent-state auditor. Validates the shared SQLite (`~/.topology_shared/_device_state.db`) schema, per-user `devices.json` permissions + schema, and cross-references. Exit 0 on clean, exit 1 on `[CRIT]`. Run periodically or after migrations.

**Files**:
- Backend: `topology/api/auth/router.py`, `topology/scripts/audit_topology_state.py`
- Frontend: `topology/topology-object-detection.js`, `topology/topology-ssh-dialog.js`, `topology/scaler-api.js`
- Tests: `topology/tests/smoke_ssh_method_matrix.js`, `topology/tests/smoke_per_user_ssh.py`, `topology/tests/README.md`
- Cache busters: `topology/index.html` -> `?v=20260420d` for object-detection + scaler-api; `?v=20260420e` for ssh-dialog.

**Deploy**: mirror every edited file to `/home/dn/CURSOR/` (same relative paths, plus new `/home/dn/CURSOR/scripts/` and `/home/dn/CURSOR/tests/` dirs). uvicorn's `--reload` picks up the auth-router change on save.

### Push-progress SSE leak + stuck upgrade-failure badge (Apr 2026)
**Problems**:
1. `[ScalerAPI] SSE reconnect attempt N/5` spam against `/api/config/push/progress/<jobId>` (with 502 responses) appeared whenever the user closed an upgrade/push progress popup. Root cause: `ScalerGUI.closePanel()` removed the DOM panel but never closed the `EventSource` returned by `ScalerAPI.connectProgress(jobId, ...)`, so the orphan SSE kept reconnecting in the background. Once the bridge cleared the job (or restarted), the proxy in `serve.py::_proxy_sse_stream` caught any upstream error and **always** returned 502, masking 401/404 etc. and triggering 5 retries (1+2+4+8+10s).
2. Upgrade-failure red badge stayed on PE4 forever and reappeared right after clicking it. Root cause: `topology-canvas-drawing.js::_startJobWatcher` iterates *all* failed upgrade jobs and overwrites `failedDevMap[did]` per iteration, while `_openFailedUpgradeDetails` only adds **one** `${jobId}:${label}` entry to `scaler_dismissed_upgrade_failures`. PE4 with multiple historical failed jobs always had another non-dismissed one to surface on the next 3s poll.

**Fixes**:
- `scaler-gui-progress.js`: after `connectProgress(...)` register the handle on the panel: `panel._sseHandle = ws; panel.dataset.jobId = jobId`.
- `scaler-gui.js::closePanel()`: before the close animation, call `panel._sseHandle.close()` and clear `state.jobs[jobId]` so the EventSource is torn down with the panel.
- `serve.py::_proxy_sse_stream()`: catch `urllib.error.HTTPError` separately and forward the upstream status (401/403/404 etc.) verbatim instead of always emitting 502; transport-level failures now return 503 (bridge unavailable) for accurate diagnostics.
- `topology-canvas-drawing.js::_startJobWatcher()`: build `editor._failedUpgradeJobsByDevice = { label: [{jobId,...}, ...] }` listing **every** currently-failed upgrade per device.
- `topology-canvas-drawing.js::_openFailedUpgradeDetails()`: when the user clicks the red badge, dismiss every known failed jobId for that device label (union with the visible job), so retried/historical failures stop reappearing.

**Files**: topology/scaler-gui-progress.js, topology/scaler-gui.js, topology/serve.py, topology/topology-canvas-drawing.js.

### SSH Dialog UX Overhaul (Mar 2026)
**Problem**: SSH dialog had broken Discover Console (display-only), connection methods hidden behind Auto-Switch, Open in-browser terminal ignoring selected method, Virsh Console only copying command, password in toasts, recovery modal calling non-existent `openSshDialog`.
**Fix**: Redesigned `topology-ssh-dialog.js`: compact credential row, methods section always visible with auto-probe on open and debounced re-probe on host change. Per-method Connect buttons open external terminal directly. Discover Console results inject clickable method rows with Connect. Removed Auto-Switch checkbox and in-browser terminal button. Toolbar SSH button: click=connect if configured, right-click=settings. Recovery modal fixed to call `showSSHAddressDialog`. Removed password from toasts; replaced emojis with [OK]/[WARN]/[INFO] prefixes.
**Files**: topology-ssh-dialog.js, topology-object-detection.js, topology-device-toolbar.js, index.html.

**Fast-connect always-probe (Mar 2026):** The toolbar SSH button (`openTerminalToDevice`) always probes via `ScalerAPI.probeConnection()` before connecting -- no `autoSwitch` flag required. The probe auto-discovers the best method and updates `sshConfig.host` if the saved host is stale. For non-cluster devices it prefers a reachable IP-based method (for iTerm), falling back to serial/hostname (web terminal). For clusters it auto-selects `virsh_console` with KVM credentials and the running NCC VM. The saved `sshConfig.host` is persisted when the probe finds a different reachable IP, so subsequent connections go to the correct address.

**Cursor /XDN deep reference (Mar 2026):** For agents, full SSH-GUI flow (probe method keys, IPv4 vs non-IP connect split, WebSocket origin, cluster NCP vs NCC console, pool eviction, troubleshooting) lives in `~/.cursor/skills/xdn-topology-mastery/ssh-reference.md`. Load with `/XDN ssh` or read `SKILL.md` section 7 in that folder.

**SSH pool evict + terminal WS (Mar 2026):** `POST /api/ssh-pool/evict` accepts optional `device_id` and resolves non-IPv4 `ip` to mgmt IP before evicting. `ScalerAPI.evictSSHPoolConnection(ip, deviceId)` and SSH dialog save / device delete pass the canvas label. `ScalerAPI.getBridgeWebSocketOrigin()` + `topology-terminal.js` align WebSocket with `ScalerAPI.baseUrl` for remote-bridge setups.

**Web terminal multi-tab (Mar 2026):** `window.TerminalPanel` manages multiple sessions in one bottom panel. VS Code-style tab strip (scrollable): each tab has status dot, device label, method badge, and close (X). `TerminalPanel.open(opts)` dedupes by tab key (`deviceId|method|host` or virsh `deviceId|method|kvmHost|ncc`). Same key focuses existing tab; new key adds a tab. Per-tab: xterm instance, WebSocket, heartbeat, SearchAddon. Shared: font size (localStorage), panel height, drag-resize. Minimize collapses to tab strip + toolbar only (tabs stay clickable). Context menu: Close Tab, Close Other Tabs, Reconnect Tab. Panel X closes all tabs.

**Web terminal responsive shell (May 2026):** `topology-terminal.js` owns the terminal panel shell and must clamp stored/dragged heights to the current viewport before applying them. Keep the `.terminal-panel` CSS hook on `#terminal-panel`; `styles.css` owns responsive header wrapping, low-height compaction, xterm card polish, and terminal scrollbars. Any open, restore, viewport resize, body resize, or successful WebSocket connect must refit the active xterm before sending resize dimensions, without changing `/api/terminal/ws` params or LLDP/native-iTerm launch semantics.

**Terminal reliability (Mar 2026):** Auto-reconnect on abnormal WebSocket close with exponential backoff (1s, 2s, 4s, max 3 attempts). Server-initiated close ('eof'/'closed' message) sets `_noAutoReconnect` to prevent reconnect loops. Heartbeat pong timeout (25s): if no pong after ping, force-close and trigger reconnect. Connection timeout (30s): if WebSocket not OPEN by deadline, close with error. `onerror` calls `ws.close()` for consistent cleanup. Debounced resize handler (100ms). Tab close picks left neighbor. Ctrl+Tab / Ctrl+Shift+Tab cycles tabs. Search bar closed on tab switch.

**DNOS iTerm preference (Mar 2026):** The canvas terminal button (top-left on selected device) calls `openTerminalToDevice` which routes to iTerm when the host is an IP and the device is NOT in GI/RECOVERY mode. This applies to **both standalone and cluster** devices. The non-GI/RECOVERY override is the first check in `openTerminalToDevice` (before cluster/standalone branching). Virsh console and web terminal are only used for GI/RECOVERY mode (pre-DNOS boot) or when no IP is available. The **toolbar SSH button** always opens the SSH dialog for credentials and settings. Host classification: IPs -> iTerm; serials -> web terminal (bridge resolves).

**Connect button fixes (Mar 2026):** SSH dialog per-method Connect button now updates `hostInput.value` to the row's host before calling `doConnect` (prevents stale host in sshConfig). Double-click protection via opacity + pointerEvents. Clipboard write uses `.then()`/`.catch()` for accurate success/fail feedback ("Password copied" vs "Paste password manually"). Stale `_lastProbeResult` cleared when host input is emptied. Probe returns 0 reachable methods -> returns early with warning (no longer attempts connection to unreachable host). Probe failure shows user-facing notification.

### Remote Access via Server IP (Mar 2026)
**Problem**: When the app is accessed via `http://<server-ip>:8080/` instead of localhost, `navigator.clipboard.writeText()` fails (requires HTTPS or localhost). Copy-to-clipboard features (config push, link table, SSH command, debugger) silently failed.
**Fix**: Added `topology-clipboard-utils.js` with `window.safeClipboardWrite(text)` that falls back to `document.execCommand('copy')` when the modern API fails. Replaced all raw `navigator.clipboard.writeText()` calls across 10+ JS files. Added CORS headers to `serve.py` `end_headers()` and `do_OPTIONS` handler. Fixed `bundle.js` hardcoded `localhost:8765` to use `/api/dnaas` proxy path.
**Files**: topology-clipboard-utils.js (new), index.html, topology-*.js, scaler-gui.js, debugger.js, bundle.js, serve.py.

### Wizard Smart Features (Mar 2026)

**Phase 1 - Sub-interface count bug**: Step invalidation only when `interfaceType` changes (preserves `subifCount`). `isLoopback` computed inside `updateLimitsWarning` from `data.interfaceType`. Debug logging in review step and `onComplete`.

**Phase 2 - Wizard history**: `recordWizardChange` extended with `generatedConfig`, `params`, `pushMode`, `jobId`. Persisted to `localStorage` (`scaler_wizard_history`, max 100). Per-wizard Last Run card and global History panel. Re-run / Re-run on other device.

**Phase 3 - Skip-existing**: `POST /api/config/scan-existing`, `POST /api/config/detect-pattern`. Interface wizard review step collision check with Skip/Start-after/Override options.

**Phase 4 - Mirror**: `POST /api/mirror/analyze`, `/generate`, `/preview-diff`. Mirror Config wizard (source/target, analyze, generate, diff, push). "Re-run on different device" wired to Mirror Wizard flow.

**Files**: scaler-gui.js, scaler-api.js, scaler_bridge.py, styles.css, scale_operations.py, mirror_config.py.

### Arrow Tips Drawn On Top of Devices (Mar 1)
**Problem**: Link arrowheads were drawn during the link pass (before devices), so device fills covered the arrow tips, making them invisible.
**Fix**: Arrow geometry/styling is now computed in `drawLink`/`drawUnboundLink` and stored on the link object (`_arrowTipEnd`, `_arrowEndAngle`, `_arrowLength`, `_arrowAngleSpread`, `_arrowFillColor`, etc.). A new `drawLinkArrows()` function in `topology-link-drawing.js` renders them in a dedicated "ARROW TIPS PASS" in `topology-draw.js` that runs after devices and labels.
**Files**: `topology-link-drawing.js`, `topology-draw.js`, `topology.js` (delegation stub).

### Layer-Based Selection Priority (Mar 1)
**Problem**: Objects on higher visual layers were not selected with priority — shapes were always forced to lowest selection priority regardless of layer.
**Fix**: `findObjectAt` in `topology-object-detection.js` now sorts candidates by `layer` (descending) first, then by `typeOrder` (text > device > link > shape) within the same layer. Only `mergedToBackground` shapes retain bottom priority.
**Files**: `topology-object-detection.js`.

### Modular Decomposition (Feb 12)
**Change**: Extracted ~11,000 lines from `topology.js` (17K -> 13.4K) and split `topology-mouse.js` (7.5K -> 33 lines coordinator + 3 handler files).
**New modules**: `topology-context-menu-handlers.js` (1605 lines), `topology-link-details.js` (671), `topology-shape-methods.js` (464), `topology-selection-popups.js` (522), `topology-link-geometry.js` (523), `topology-text-attachment.js` (337), `topology-mouse-down.js` (2538), `topology-mouse-move.js` (2775), `topology-mouse-up.js` (1985).
**Pattern**: Each extracted method receives `editor` as first parameter instead of using `this`. Stubs in topology.js delegate via `if (window.ModuleName) return window.ModuleName.method(this, ...args);`
**Load order**: New modules load BEFORE `topology.js` via `<script>` tags in `index.html`.

### Seamless Object-to-Object Toolbar Transition (Feb 12)
**Problem**: Clicking from one device to another caused the old toolbar to linger for 150ms before being replaced, making transitions feel janky.
**Root cause**: `hideAllSelectionToolbars()` was only called when clicking empty grid, not when clicking a different object. The 150ms toolbar delay was the same for first selection and transitions.
**Fix (topology-mouse.js)**:
1. Added `editor.hideAllSelectionToolbars()` immediately in the `!alreadySelected` path (line ~1230), so the old toolbar disappears instantly when clicking a new object.
2. Introduced `hadPreviousSelection` flag to use a shorter toolbar delay (50ms) when transitioning between objects vs. first selection from empty (150ms).
**Result**: Old toolbar vanishes instantly → 50ms pause → new toolbar appears. All object types (device, link, text, shape) benefit.

### Syntax Error in topology-mouse.js (Feb 12)
**Problem**: Duplicate closing code (lines 7515-7520) caused `SyntaxError: Unexpected token '}'`, preventing `window.MouseHandler` from loading. All canvas clicks silently failed.
**Fix**: Removed the duplicate `}`, `},`, `};`, and `console.log` lines at the end of the file.

### TB+Shape Group Jump, Copy Style from TB, CS Cancel (Feb 10)
**TB+Shape jump**: When text box and shape are grouped and dragged, they jumped. Root cause: momentum was not stopped before capturing positions when expanding group selection. Fix: Call momentum.stopAll() and reset() in the group expand path (topology-mouse.js, topology-groups.js) before building multiSelectInitialPositions.

**Copy Style from TB**: Text toolbar Copy Style only set copiedStyle but never pasteStyleMode=true, so click-to-paste didn't work. Fix: Call editor.copyObjectStyle(textObj) instead of manually setting copiedStyle.

**Copy Style cancel**: Added toast on paste-mode entry: "Click objects to paste. Press Escape to cancel." Added toast on exit: "Copy Style cancelled". Escape already cancelled; now it's discoverable.

**Copy Style cross-type rules** (in `_applyStyleToObject`):
| Source → Target | Color mapping | Other |
|---|---|---|
| Device → TB | device.color → TB bg (if has bg) or text; device.labelColor → TB text | font props |
| TB → Device | TB bg → device.color; TB text → device.labelColor | font props |
| TB → Link | TB bg → link.color (if has bg); else TB text → link.color | TB borderStyle → link style; TB borderWidth → link width |
| Link → TB | link.color → TB bg (if has bg) or text | link style → TB borderStyle |
| TB → Shape | TB bg → shape.fill; TB border/text → shape.stroke (if has bg); else text → both | TB borderWidth → stroke width |
| Shape → TB | shape.fill → TB bg (if has bg) or text; shape.stroke → TB border | shape strokeWidth → TB borderWidth |
| Same-type | full property copy | all applicable props |

**Per-TB `alwaysFaceUser`**: Link-attached TBs can toggle `alwaysFaceUser = true` to stay horizontal (readable) regardless of link angle. The drawing code (`topology-canvas-drawing.js` line ~725) checks `text.alwaysFaceUser === true` and forces 0° rotation. This property is preserved in Copy Style (TB→TB) and shown as an eye/eye-off button in the text selection toolbar for link-attached TBs.

### Group Drag: Jump Fix + BUL Restriction (Feb 10, refined Feb 11)
**Problem**: Grouped objects (TB+shape) jump when grabbed and moved.
**Root cause (FINAL)**: Normal selection path in handleMouseDown did NOT expand groups causing dragStart offset/absolute mismatch. Also stale positions and pointer+mouse double events.
**Fix (3 layers)**: (a) ALL mousedown paths expand groups with isMultiSelect. (b) Threshold handler re-captures FRESH positions. (c) Safety net in handleMouseMove fixes dragStart. 8ms dedup timer.
**RULE**: dragStart for multi-select = ABSOLUTE mouse pos. For single-object = OFFSET. Never mix.

**Problem 2**: Merged (BUL) shapes grouped with devices/shapes - moving fails silently.
**Fix**: Before starting group/multi-select drag, check if selection has both BUL links and other objects (device, shape, text). If so, block drag and show toast: "BUL chains grouped with devices/shapes cannot be moved together. Ungroup first, or move each separately."

### Left-Click Selection Toolbars (Jan 12)
**Change**: Toolbars now appear on **single left-click** (selection), not just right-click.

**Trigger:** Left-click to select any object → toolbar appears after 150ms delay
**Hidden when:** Dragging, clicking empty space, or returning to base mode

**Positioning:**
- Device toolbar: Below device center
- Link toolbar: At click location (passed via `clickPos` parameter)
- Text toolbar: Below text center

**Code Pattern:**
```javascript
// In handleMouseDown - after selection:
setTimeout(() => {
    if (this.selectedObject === clickedObject && !this.dragging) {
        if (clickedObject.type === 'text' && !this._inlineTextEditor) {
            this.showTextSelectionToolbar(clickedObject);
        } else if (clickedObject.type === 'device') {
            this.showDeviceSelectionToolbar(clickedObject);
        } else if (clickedObject.type === 'link' || clickedObject.type === 'unbound') {
            this.showLinkSelectionToolbar(clickedObject);
        }
    }
}, 150);
```

### Selection Toolbars - Liquid Glass Design (Jan 12)
**Change**: Replaced traditional right-click context menus with floating liquid glass toolbars.

**New Functions:**
- `showDeviceSelectionToolbar(device)` - SSH, Rename, Color, Style, Lock, Delete
- `showLinkSelectionToolbar(link)` - Add Text, Color, Width, Style, Curve, Delete
- `hideAllSelectionToolbars()` - Hides all toolbars at once

### BUL Extension from TP Bug (Fixed)
**Problem**: Clicking TP to extend chain would create duplicate TP at MP location.

**Root Causes**:
1. `isFreeTP` only checked device attachment, not merge connections
2. Code overwrote `mergedWith` when extending, breaking existing chain

**Fix**:
1. Use `isEndpointConnected()` in `isFreeTP` check
2. Implement PREPEND vs APPEND logic - if sourceLink has child, new link becomes HEAD

### Device Style Button Names (Fixed)
**Problem**: Names truncated ("Cl...", "C...", etc.)

**Fix**: Added `white-space: nowrap; overflow: visible` to `.style-label`

### Refresh Shortcuts (R / Cmd+R / Ctrl+R)
**Rule**: Browser-native refresh shortcuts must stay browser-native. `topology-keyboard.js`
may handle plain unmodified **R** as an in-app convenience refresh, but it must not call
`preventDefault()` for `Cmd+R`, `Ctrl+R`, `Shift+R`, or other modified refresh keys. Use
`window.location.reload()` for plain **R** only; do not use deprecated
`window.location.reload(true)` or delayed timers.

**Files**: `topology-keyboard.js`, `index.html`. Static guard:
`topology/tests/test_toolbar_pan_restore_unit.py::test_refresh_shortcut_preserves_browser_reload_keys`.

---

## 🚫 NEVER DO

1. ❌ Set `mergedWith` without checking if link already has a child
2. ❌ Check only `device1`/`device2` for free endpoint (must also check merges)
3. ❌ Share `connectionPoint` objects between mergedWith and mergedInto (CLONE them!)
4. ❌ Modify code without reading it first
5. ❌ Forget to update this file after fixes
6. ❌ Add a `beforeunload` handler that prompts or forces save on refresh (causes "Leave site?" / save-as suggestion)

## ✅ ALWAYS DO

1. ✅ Use `isEndpointConnected()` to check if endpoint is free
2. ✅ Clone connection points: `{ x: point.x, y: point.y }`
3. ✅ Handle both PREPEND and APPEND scenarios for chain extension
4. ✅ Verify braces balance after edits
5. ✅ Update DEVELOPMENT_GUIDELINES.md after successful fixes
6. ✅ Check `TopologyRegistry.whereDoesThisBelong()` before adding new features
7. ✅ Wrap critical operations with `ErrorBoundary`
8. ✅ Run `TopologyTests.runAll()` after changes

---

## 📋 Feature Templates

### Using the Registry

Before adding new features, check the registry:

```javascript
// In browser console:
TopologyRegistry.whereDoesThisBelong("add alignment tool")
// Returns: { action: 'edit', file: 'topology-input.js', module: 'input', reason: '...' }

// Generate code template:
TopologyRegistry.generateTemplate('objectManager', 'Annotation')
TopologyRegistry.generateTemplate('modal', 'Settings')
TopologyRegistry.generateTemplate('integration', 'Monitor')
```

### Template: New Object Manager```javascript
// topology-{thing}.js
class {Thing}Manager {
    constructor(editor) {
        this.editor = editor;
        this.items = [];
        console.log('{Thing}Manager initialized');
    }
    
    // CRUD operations
    create(options) {
        const item = { id: Date.now(), type: '{thing}', ...options };
        this.items.push(item);
        this.editor.events?.emit('{thing}:created', item);
        this.editor.saveState?.();
        return item;
    }
    
    getAll() { return this.items; }
    getById(id) { return this.items.find(i => i.id === id); }
    remove(id) {
        this.items = this.items.filter(i => i.id !== id);
        this.editor.events?.emit('{thing}:removed', { id });
    }
    
    // Spatial query
    findAt(x, y) {
        return this.items.find(item => /* hit test */);
    }
    
    // Drawing
    draw(ctx, item) {
        // Render the item
    }
}

window.{Thing}Manager = {Thing}Manager;
window.create{Thing}Manager = (editor) => new {Thing}Manager(editor);
```

### Template: New Input State

```javascript
// Add to topology-input.js
class {Mode}Handler extends InputStateHandler {
    constructor(editor, inputManager) {
        super(editor, inputManager);
        this.name = '{mode}';
    }
    
    enter(context = {}) {
        super.enter(context);
        this.editor.canvas.style.cursor = 'crosshair';
    }
    
    exit() {
        this.editor.canvas.style.cursor = 'default';
        super.exit();
    }
    
    onMouseDown(e) { return null; } // null = stay, 'idle' = exit
    onMouseMove(e) { return null; }
    onMouseUp(e) { return 'idle'; }
    onKeyDown(e) { if (e.key === 'Escape') return 'idle'; return null; }
}

// Register: inputManager.registerState('{mode}', new {Mode}Handler(editor, inputManager));
```

### Template: New Modal

```javascript
// topology-{name}-modal.js
class {Name}Modal {
    constructor(editor) {
        this.editor = editor;
        this.element = null;
        this.isVisible = false;
    }
    
    show(data = {}) {
        this.data = data;
        this.createModal();
        this.populateFields();
        this.isVisible = true;
    }
    
    hide() {
        if (this.element) {
            this.element.remove();
            this.element = null;
        }
        this.isVisible = false;
    }
    
    createModal() {
        this.element = document.createElement('div');
        this.element.className = '{name}-modal-overlay';
        this.element.innerHTML = `
            <div class="{name}-modal">
                <div class="modal-header"><h2>{Name}</h2><button class="close">&times;</button></div>
                <div class="modal-body"><!-- fields --></div>
                <div class="modal-footer"><button class="cancel">Cancel</button><button class="save">Save</button></div>
            </div>
        `;
        document.body.appendChild(this.element);
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        this.element.querySelector('.close')?.addEventListener('click', () => this.hide());
        this.element.querySelector('.cancel')?.addEventListener('click', () => this.hide());
        this.element.querySelector('.save')?.addEventListener('click', () => this.save());
    }
    
    save() { /* validate and save */ this.hide(); }
}

window.{Name}Modal = {Name}Modal;
```

---

## 🛡️ Error Handling Patterns

### Wrapping Event Handlers

```javascript
// Use ErrorBoundary for crash protection
const safeHandler = ErrorBoundary.wrapEventHandler(
    (e) => this.handleClick(e),
    this,
    'click'
);
this.canvas.addEventListener('click', safeHandler);
```

### Safe Module Initialization

```javascript
// In topology.js constructor
this.myModule = ErrorBoundary.safeModuleInit('ModuleName',
    () => new MyModule(this),
    () => ({ /* fallback object */ })
);
```

### Auto-Save and Crash Recovery

```javascript
// Enable auto-save (30 second interval)
this.files.enableAutoSave();

// Check for recovery on startup
this.files.checkForRecovery();
```

**Recovery skip conditions** (won't show dialog):
1. Previous session closed cleanly (`beforeunload` → `markSessionClosed()`)
2. Recovery data matches **any** of:
   - `topology_current` (Quick Save target)
   - `topology_autosave_v2` (debounced auto-save -- what the editor loaded on boot)
   - the **live** `editor.objects` (what's on screen RIGHT NOW after the auto-loader ran)
3. Live canvas already has ≥ as many objects as the recovery snapshot (recovery would regress state)
4. `topology_suppress_recovery_until` timestamp is in the future (set automatically when the user clicks "Start Fresh" -- suppresses for 10 min)
5. `quickSaveTopology()` syncs recovery data session ID to current session

**Why this matters (2026-04-22 fix):** the old check only compared against `topology_current`,
which is ONLY written by explicit Quick Save. The normal auto-save path writes to
`topology_autosave_v2` and re-hydrates `editor.objects` on boot, so the prompt fired on almost
every refresh asking to "recover" content that was already on the canvas. New logic compares
against the LIVE canvas too, so the dialog only appears when there's genuinely lost work.

### AI Assistant -- Gemini-only UI (2026-04-22)

The AI drawer is locked to Google Gemini in the UI. Other providers (Anthropic, OpenAI, Groq,
Ollama) are deliberately hidden from `PROVIDER_PRESETS` in `topology-ai.js`. The backend
(`ai/service.py`) still contains the other client classes as a dormant safety net -- removing
them entirely would break any stored per-user configs that haven't been migrated yet.

**Migration path:** `_probeAiConfig` detects legacy provider names (`groq` / `openai` /
`anthropic` / `ollama`) in the user's stored config and silently rewrites the config to
`gemini` via `PUT /api/users/me/ai-config`. The old API key (which is the wrong prefix for
Gemini anyway) is wiped; the user is prompted for an `AIza...` key, or if the operator has
exported `GEMINI_API_KEY` on the server the shared key is used automatically.

**To add another provider back to the UI:** re-add it to `PROVIDER_PRESETS` in
`topology-ai.js` (the backend dispatcher lights up automatically because the config handler
in `serve.py` still accepts `anthropic / openai / groq / ollama / gemini` in `_ALLOWED`).

### AI Assistant -- `apply_canvas_edits` tool (2026-04-22)

A second AI tool was added alongside `create_topology`. Where `create_topology` produces a
FULL topology and saves it to disk (user clicks "Load" to bring it onto the canvas),
`apply_canvas_edits` MUTATES the live canvas in place with a list of granular edits:
`add_device`, `add_link`, `add_text`, `remove`, `move`, `relabel`.

**System-prompt routing:**
- "build a leaf-spine fabric" → `create_topology`
- "add a spine to my canvas" → `apply_canvas_edits`
- "connect spine1 to leaf3" → `apply_canvas_edits`

**Files:**
- `ai/context.py` : `CANVAS_EDITS_TOOL_SCHEMA` (declarative JSON schema).
- `serve.py` : `_handle_ai_chat` advertises both tools, emits `status: "apply"` with the
  edits passed through to the client.
- `topology-ai.js` : `_applyCanvasEdits(tool)` walks the edits and calls the editor's native
  APIs (`editor.devices.addAtPosition`, `editor.createLink`, `editor.createText`,
  `editor.objects.filter` for removal). A single `editor.saveState()` at the top makes
  Ctrl+Z (or the tool-card "Undo" button) revert the whole batch.

**Smart placement:** `add_device` / `add_text` edits can omit `x` / `y`. The executor picks
coords from the device's `role` field:
- `spine` devices land in the spine row (same Y as existing spines, next X slot to the right)
- `leaf` devices land in the leaf row below
- SP-backbone roles (`pe` / `p` / `rr` / `ce` / `core`) stack on their canonical tiers
- Unknown role → stacked to the right of the rightmost existing device

Tier Y bands are seeded at `originY + tier * tierGap` (defaults: 250, 300, 550, 850, ...) so
a fresh canvas gets the same layout as one with existing peers.

**Undo:** the tool card renders an "Undo" button that calls `editor.undo()`. Because the
executor wraps the whole batch in a single `saveState()`, a single Ctrl+Z reverts every edit
in the batch atomically.

### AI Assistant -- terminology, unbound-link op, and 429 auto-retry (2026-04-22j)

Three problems showed up in a single user session:

1. **"Add a UL above Spine-2nd-br" was rejected by the model** -- `apply_canvas_edits`
   advertised only `add_device` / `add_link` / `add_text` / `remove` / `move` / `relabel`.
   Unbound links (UL) have no device endpoints, so the only link op the model could pick
   was `add_link`, which needs both `from` and `to`, and it asked the user for the second
   endpoint instead of dropping a free-ended link.
2. **Gemini did not know app shorthands** (`UL`, `BUL`, `QL`, `DNAAS`, `NCF`/`NCM`/`NCC`/
   `NCP`, ...). `knowledge.md` mentioned `unbound-link` and `BUL` only in passing; no
   glossary, no mapping from the user's typed shorthand to the canonical term.
3. **Rate-limit 429 produced a hard error card** instead of a transparent retry. The user
   had to click the `Retry` button manually after every `try again in 1.6s` from Gemini's
   free tier.

**Fixes (files):**

- `ai/context.py` -- `CANVAS_EDITS_TOOL_SCHEMA`:
  - New `add_unbound_link` op in the enum.
  - New `anchor` + `anchor_position` fields (above/below/left/right) usable on
    `add_unbound_link`. Schema description includes an **App Terminology** mapping so the
    model maps `UL` / `unbound` / `unbounded link` / `free link` directly to the op.
  - New `x1` / `y1` / `x2` / `y2` / `length` / `orientation` for explicit UL endpoints.
- `ai/knowledge.md` -- prepended a full **glossary** section (link kinds, device role
  tags, DriveNets chassis codes, protocols, feature names, position shorthands). The
  glossary lives near the top of the digest so it's still in the model's attention even
  for long conversations. An explicit "DO NOT ASK THE USER TO CLARIFY THESE" directive
  is included so Gemini does not second-guess UL/BUL/QL again.
- `topology-ai.js` -- `_applyCanvasEdits`:
  - New `add_unbound_link` branch. Placement resolution priority is:
    1. Explicit `x1/y1/x2/y2`.
    2. `anchor` + `anchor_position` (computes endpoints relative to the anchor device's
       `x,y` with a gap of `max(60, anchor.radius + 36)`).
    3. Explicit `x`/`y` center (spread by `length` + `orientation`).
    4. Fallback to `editor.createUnboundLink()` which has built-in Y-collision avoidance.
  - Builds the same `{type:'unbound', originType:'UL', start:{x,y}, end:{x,y},
    device1:null, device2:null, connectedStart:null, connectedEnd:null, ...}` shape as
    the manual toolbar button, so hit-testing / BUL merging / save-load all treat it
    identically.
- `serve.py`:
  - New `Handler._ai_chat_with_rate_retry(client, messages, **kwargs)` wraps `client.chat`.
    On `LlmError(kind='rate_limited')` it parses the provider's "try again in Ns" hint
    (Groq + OpenAI pattern) out of the error body, sleeps
    `clamp(hint + 0.25s, MIN=1s, MAX=10s)`, and retries **exactly once**. Unit-verified
    with both transient (1 fail + 1 success) and persistent (2 fails -> bubble) cases.
    No infinite loop is possible. The second call's `timeout` is trimmed by the sleep so
    the total wall-clock does not exceed the original user-facing budget.
  - Returns `(raw, retry_info|None)`. `_handle_ai_chat` and `_handle_ai_topology_generate`
    both unpack the tuple; chat adds `resp["retried"] = retry_info` to the JSON response.
  - `_record_audit("ai_rate_retry", ...)` logs every retry with wait_s + provider so the
    owner audit panel can see how often the free tier is getting hit.
- `topology-ai.js` -- new `.ai-msg__retry-chip` pill renders as a small amber tag under
  the successful assistant reply when `json.retried` is present. Tooltip explains the
  retry. Zero impact when the first call succeeds (the field is simply absent).

**Testing:**

1. `python3 -m py_compile ai/context.py serve.py` -- both clean.
2. `_parse_retry_after_seconds` unit-tested on four bodies (OpenAI JSON with `1.615s`,
   Groq plaintext with `45 seconds`, empty, unrelated) -- all expected values returned.
3. `_ai_chat_with_rate_retry` integration test with a fake client that 429s once then
   succeeds: waited 2.25s (hint 2.0 + safety 0.25), attempted twice, `retry_info`
   correctly populated.
4. Persistent-429 test: attempted twice only, then raised the original `LlmError`
   unchanged (kind=`rate_limited`, status=429) -- no infinite loop.
5. `load_knowledge_digest()` confirmed all 13 glossary anchors (UL, BUL, QL, DNAAS,
   NCF, NCM, NCC, NCP, "Unbound Link", "add_unbound_link", "anchor_position",
   "glossary", "terminology") are present in the deployed digest.

**Cache busters bumped:** `topology-ai.js?v=20260422i` in `index.html`.

**Files touched + synced to `/home/dn/CURSOR/`:**

- `topology/ai/context.py` -> `CURSOR/ai/context.py`
- `topology/ai/knowledge.md` -> `CURSOR/ai/knowledge.md`
- `topology/serve.py` -> `CURSOR/serve.py`
- `topology/topology-ai.js` -> `CURSOR/topology-ai.js`
- `topology/index.html` -> `CURSOR/index.html`

### AI Assistant -- per-user multi-conversation persistence (2026-04-22j)

Before this change the AI drawer's `_messages` array lived only in the current
browser tab's RAM: F5 wiped it, a second tab couldn't see it, and there was no
way to resume a chat from yesterday. Users asked for "full conversations", i.e.
durable, per-user, multi-chat memory with an admin-auditable back-end. This
change delivers that without breaking any existing AI flow.

**Storage (server-side source of truth):**

- New per-user SQLite DB under `~/.topology_users/<user>/ai.db`, created on
  first use. Path + WAL pragmas mirror `api/auth/user_store.py` exactly so
  concurrent writes from multiple tabs / the knowledge poller / serve.py
  itself behave the same.
- Schema (`topology/ai/conversation_store.py`):
  - `conversations(id TEXT PRIMARY KEY, title, topology_domain, topology_id,`
    `provider, model, created_at, updated_at, archived, pinned, turn_count)`
  - `messages(id INTEGER PRIMARY KEY AUTOINCREMENT, conv_id REFERENCES`
    `conversations(id) ON DELETE CASCADE, role, content, tool_calls_json,`
    `retry_info_json, created_at)`
  - Indexes: `idx_conv_updated(archived, updated_at DESC)`,
    `idx_conv_topology(topology_domain, topology_id, updated_at DESC)`,
    `idx_msg_conv(conv_id, created_at)`.
- Soft caps that can't be hit under legitimate use (`10,000` convs per user,
  `40,000` msgs per conv, `1 MB` per message) to keep a runaway client
  from blowing through disk.

**REST endpoints (all require auth; admin ones gated by `_require_admin`):**

| Method | Path | Body / Query | Purpose |
| - | - | - | - |
| GET | `/api/ai/conversations` | `?archived=1` to include archived; `?topology_domain&topology_id` for per-topology filter | List own |
| POST | `/api/ai/conversations` | `{title?, topology_domain?, topology_id?, provider?, model?}` | Create empty conv |
| GET | `/api/ai/conversations/{id}` | -- | Fetch with full transcript |
| PATCH | `/api/ai/conversations/{id}` | `{title?, archived?, pinned?, topology_domain?, topology_id?}` | Partial update |
| DELETE | `/api/ai/conversations/{id}` | -- | Remove + cascade messages |
| GET | `/api/admin/ai/conversations?user=X` | `?archived=0` to exclude archived | Admin list any user's chats |
| GET | `/api/admin/ai/conversations/{id}?user=X` | -- | Admin read full transcript |

Admin endpoints emit `_record_audit("ai_admin_list_conversations", ...)` and
`_record_audit("ai_admin_read_conversation", ...)` so every cross-user read
is traceable.

**/api/ai/chat integration:**

- Accepts optional `conversation_id` in the request body.
- If absent OR the id is not found on disk (stale localStorage), a fresh
  conversation is auto-created with a title derived from the user's first
  message (truncated at a word boundary, capped at 120 chars, default
  "New chat" when the message is empty).
- The last user message in `messages[]` is persisted BEFORE the LLM call.
- The assistant's reply (text + tool_calls + retry_info) is persisted AFTER
  the LLM call. Failures in the persistence layer NEVER abort the chat --
  they are logged and the response still ships (graceful degradation).
- Response echoes back `conversation_id` plus a `{id, title,
  topology_domain, topology_id, turn_count, updated_at}` snapshot so the
  client can wire up a just-created id on the first turn without a
  follow-up GET.

**Frontend (`topology-ai.js`):**

- New state: `_currentConvId`, `_currentConvTitle`, `_conversations[]`,
  `_convListOpen`, `_convListSyncing`.
- `localStorage` cache keyed `ai-conversations:v1:<username>`, capped at 10
  conversation rows + last 200 messages of the current chat. Used for
  instant paint on drawer-open; background `GET /api/ai/conversations`
  reconciles within seconds.
- Drawer header additions: conversation-title chip next to "AI Assistant",
  History button (list/clock icon), New-chat button (pencil-plus icon).
  The old Clear button's semantics shifted from destructive to
  non-destructive -- it now archives the current conversation (stays in
  history, filtered out of the default list) and opens a fresh chat.
- New slide-down conversation-list panel (`data-role="conv-list"`) inside
  the drawer body. Rows show title + turn count + relative time, with
  per-row Rename (prompt) and Delete (confirm) buttons. "show archived"
  checkbox flips `?archived=1` on the refresh call.
- `_sendUserMessage` sends `conversation_id` on every turn and captures
  the server-echoed `conversation_id` + title on first-turn creation,
  updating the sidebar + chip optimistically then reconciling via a
  delayed `_refreshConvListFromServer`.

**Smoke test (captured 2026-04-22j with live server):**

1. `GET /api/ai/conversations` for fresh admin -> `{conversations: []}`.
2. `POST /api/ai/conversations {title:"Smoke test", provider:"gemini", model:"gemini-2.5-flash"}` -> 201 with the created row.
3. `GET /api/ai/conversations` -> count=1, row matches.
4. `PATCH /api/ai/conversations/<id> {title:"Smoke test renamed"}` -> 200, title updated.
5. `GET /api/ai/conversations/<id>` -> `title="Smoke test renamed"` turns=0 msgs=0.
6. `PATCH {archived:true}` -> `archived=True`; default list count=0; `?archived=1` count=1.
7. `GET /api/admin/ai/conversations?user=admin` -> stats={conversations:1, active_conversations:0, messages:0, last_activity:<ms>}.
8. `GET /api/admin/ai/conversations/<id>?user=admin` -> full transcript, admin-audit event logged.
9. `GET /api/admin/ai/conversations` as non-admin engineer token -> HTTP 403 "Admin role required".
10. `DELETE /api/ai/conversations/<id>` -> 200, list count=0.
11. `POST /api/ai/chat` with no provider configured -> HTTP 401 code=not-configured, DB conversations table row count=0 (no stub conversations on failed turns).

Unit-level sanity (`python3 -c "from ai.conversation_store import ConversationStore..."`):

- Create + append user/assistant turns + fetch full w/ tool_calls + retry_info decoded -> ok.
- User isolation: bob cannot see alice's conversation or list her store -> ok.
- Archive hides from default list but appears with `include_archived=True` -> ok.
- `auto_title()` truncates at word boundary + appends horizontal ellipsis -> ok.
- Delete cascades messages -> `get_conversation` returns None -> ok.

**Failure modes handled:**

- Stale `conversation_id` in localStorage (DB deleted / different device):
  silently creates a new conversation on the next turn instead of 404.
- Store import error at boot: `_conversation_store()` returns `None`,
  every endpoint returns HTTP 503 "conversation store unavailable" and
  `/api/ai/chat` still works but doesn't persist.
- localStorage quota exceeded: `_saveConvCache` swallows the error and
  continues (server remains the source of truth).
- Message cap per conversation (`MAX_MESSAGES_PER_CONVERSATION=40000`):
  `append_message` raises, caller catches, user sees "Start a new chat"
  prompt; the LLM reply still renders.

**Cache busters bumped:** `topology-ai.js?v=20260422j` in `index.html`.

**Files touched + synced to `/home/dn/CURSOR/`:**

- NEW  `topology/ai/conversation_store.py` -> `CURSOR/ai/conversation_store.py`
- EDIT `topology/serve.py`                  -> `CURSOR/serve.py` (store singleton + 7 endpoints + chat integration + PATCH/DELETE routing)
- EDIT `topology/topology-ai.js`            -> `CURSOR/topology-ai.js` (state, cache, UI, events, CSS, chat-wire)
- EDIT `topology/index.html`                -> `CURSOR/index.html` (cache buster)

### File Menu

The File button (`#btn-file-menu`) in the top bar opens `#file-dropdown-menu` positioned
directly below the button (not centered). Wired in `topology-toolbar-setup.js`.
Close handlers: outside-click + Escape (inline script in `index.html`).

### File Upload

`loadTopology(event)` in `topology.js` reads via `FileReader`, handles wrapped formats
(`{topology: {objects}}`, bare arrays), and resets the file input for re-selection.

---

## 🧪 Testing Checklist

After any code change:

```javascript
// Run all tests
TopologyTests.runAll()

// Run specific module tests
TopologyTests.runModule('devices')
TopologyTests.runModule('links')
TopologyTests.runModule('input')
```

Manual testing:
- [ ] Feature works as expected
- [ ] Selection still works
- [ ] Undo/Redo still works
- [ ] Save/Load still works
- [ ] No console errors
- [ ] Plain `R` can refresh through `handleKeyDown`; browser `Cmd+R` / `Ctrl+R` remains unhandled by app code.

---

## Console Discovery & PDU Power (Zohar's DB)

The topology app integrates Zohar Keiserman's lab console database for device recovery operations.

### Data Sources (hosted on `zkeiserman-dev`)

| File | Path on server | Local cache | Purpose |
|------|---------------|-------------|---------|
| Console CSV | `/home/dn/console_db/console_devices.csv` | `/tmp/console_devices_cache.csv` | Serial -> Console Server + Port (~700 devices) |
| PDU Mapping | `/home/dn/console_db/pdu_mapping.json` | `/tmp/pdu_mapping_cache.json` | Serial -> PDU host + outlet (power cycling) |
| PDU CLI Config | `/home/dn/console_db/pdu_cli_config.json` | `/tmp/pdu_cli_config_cache.json` | PDU host -> CLI type (dev_outlet vs ol) |

### Discovery Priority Chain

1. **Zohar's CSV DB** (primary) -- fetched via SFTP from `zkeiserman-dev`, cached 1 hour
2. **Device42 API** (fallback) -- requires `~/.device42_config.json`
3. **console_mappings.json** (cached results) -- auto-saved after any discovery

### Connection Strategy Integration (`connection_strategy.py`)

`get_console_config_for_device(hostname)` resolution order:
1. `console_mappings.json` multi-server format
2. `console_mappings.json` legacy single-server format
3. `console_mappings.json` device_to_console lookup
4. Zohar's CSV (by serial from `operational.json`)

### Frontend Flow

1. SSH dialog "Discover Console" button -> `ScalerAPI.discoverConsole()` -> `POST /api/ssh/discover-console`
2. Results show console server, port, PDU info in the SSH dialog
3. If PDU entries found, "PDU Reboot" appears. This is a hard lab power
   action (PDU outlet off/on), not a DNOS command; require user confirmation
   and keep the UI warning explicit.
4. Power cycle -> `ScalerAPI.pduPower()` -> `POST /api/ssh/pdu-power`
5. Auto-switch probe includes console as a viable method when discovered

For cluster devices, the console row must say which data-plane NCP it reaches
when known. Prefer explicit console mapping metadata, then infer `NCP-N` from
serial suffixes like `-P3`; otherwise render `NCP data-plane (exact node not
mapped)` rather than implying the path reaches an NCC.

---

## Debug-DNOS Topology Integration

The topology app integrates with `/debug-dnos` bug evidence system:

### Backend (`serve.py`)

- `GET /debug-dnos-topologies/list.json` — scans `~/SCALER/FLOWSPEC_VPN/bug_evidence/*.topology.json` and returns a JSON list
- `GET /debug-dnos-topologies/<filename>` — serves a specific `.topology.json` file

### Frontend (`topology.js` + `index.html`)

- "Topologies" dropdown has a "Debug-DNOS Topologies" section (red accent)
- `showDebugDnosTopologiesSubmenu()` fetches the list
- `showDebugDnosTopologySelector(topologies)` shows a modal picker
- `loadDebugDnosTopology(filename)` fetches and loads into the canvas

### Topology JSON Visual Standards (for generated files)

**Pre-creation checklist (mandatory):**

- Identify the PRIMARY bug (not secondary effects). Re-read the `.md` Expected/Actual sections first.
- VRF panel text must use `show` command language (e.g., "Redirect target: selected"), NOT code internals (e.g., "BGP_CONFIG_RD not set").
- For comparison bugs: both panels show what differs and the result from the user's perspective.
- Scan JSON for code-level leakage (function names, file names, protobuf fields) — remove any.

**Visual rules:**

1. Device labels = name only; IP as separate TB below (`y = device_y + radius + 30`)
2. Every link has a transparent protocol label at midpoint (`_onLinkLine: true`)
3. VRF info uses rectangle shapes as containers with text on top
4. Route info box near ExaBGP with "Route Injected:" header
5. No "BUG:" labels, no code-level details
6. Z-order: Devices → Links → Container shapes → Text → Marker shapes (cross/checkmark LAST)

---

## UI / Branding Notes (Feb 2026)

### Left Toolbar
- **TEXT ACTIVE hidden**: `#text-mode-indicator` is hidden via CSS (user request). Tool mode indicators for Device/Shape/Link remain visible.
- **Shape Type Grid**: `.shape-type-grid` and `.shape-type-btn` provide scalable, aligned layout for the SHAPER section. Use `minmax(0, 1fr)` for responsive columns.
- **Section alignment**: Toolbar section headers use `min-height: 40px`, `gap: 8px`. Nested subsection headers use `min-height: 28px`. Device/link/font grids use `minmax(0, 1fr)` for equal column sizing.

### XRAY GUI Integration (Feb 2026, updated Mar 2026)

**Overview**: Links between two devices show a magnifying glass icon when selected. Clicking opens an XRAY Capture popup for DP/CP/DNAAS-DP traffic capture, with results delivered to Mac Wireshark.

**Key files:**
- `topology-xray-popup.js` — XRAY popup UI (liquid glass style, mode CP/DP (Arista)/DP (DNAAS), duration, direction, protocol filters, output, POV, SSH prompt when device has no SSH)
- `topology-link-toolbar.js` — Packet Capture button in the link toolbar (first button, only for device-to-device links)
- `topology-mouse-down.js` — Opens link toolbar on link click; calls `XrayPopup.temporaryHide()` when panning starts
- `topology-mouse-up.js` — Calls `XrayPopup.temporaryShow()` when panning ends
- `topology-toolbar-setup.js` — XRAY Settings section handlers (load/save config, Verify Mac)
- `index.html` — XRAY Settings section in left toolbar (Mac IP, user, password, Wireshark path, pcap dir)
- `serve.py` — `/api/xray/run`, `/api/xray/status/{id}`, `/api/xray/stop/{id}`, `/api/xray/config`, `/api/xray/verify-mac`
- `topology-link-details.js` — `autoFillFromLldp()` cross-references LLDP to auto-bind interfaces

**Data flow:**
1. Link selected between 2 devices -> Packet Capture button appears as first button in link toolbar
2. Click button -> `XrayPopup.show()` opens floating popup (positioned below link toolbar center, with notch)
3. If device has no SSH config -> SSH prompt (host, user, pass) shown; user must fill before Start
4. User picks mode/duration/direction/protocol filters/output/POV -> "Start Capture"
5. `POST /api/xray/run` with device, mode, interface, duration, output, direction, capture_filter, dut_host
6. Popup polls `GET /api/xray/status/{id}` for progress
7. Mac delivery: SCP pcap + SSH open Wireshark (credentials from `~/.xray_config.json`)

**Popup features:** Liquid glass styling (matches device/link toolbar), positioned below link toolbar with upward notch. Mode buttons: CP (Control Plane), DP (Arista), DP (DNAAS) with connectivity dots and inline hints when unavailable. Direction (Ingress/Egress/Both), Quick filters (BGP, OSPF, ISIS, LDP, LLDP, BFD multi-select), Exclude DNOS internal traffic (CP only), interface from link table or auto-detect, SSH prompt when device has no `sshConfig.host`. SSH credentials set in popup are stored on device and trigger `editor.saveState()`.

**DP/DNAAS LLDP normalization (Apr 2026):** LLDP payloads can arrive with different key names depending on source (`neighbor`/`neighbor_name`/`neighbor_device`, `remote`/`remote_port`/`neighbor_port`/`neighbor_interface`/`remote_interface`, `local`/`interface`/`local_interface`). `topology-xray-popup.js` must normalize these before deciding whether Arista Live Capture or DP (DNAAS) is available, and should consult `device._lldpData.neighbors` first before slow live API calls. PE-4 has a valid Arista neighbor (`DN-LEAF1.dev.drivenets.net` on remote `Ethernet8/5/1`) plus DNAAS leaves; do not disable Live Capture just because a payload used `neighbor_port` or `remote` instead of `remote_port`.

**DNAAS capture alignment:** The Confluence workflow `DNAAS - Capture automation solution` documents the temporary dropped-packets path: configure a DNAAS Leaf port-mirroring session from the DUT-facing leaf port into the dedicated mirror uplink, then collect dropped-packets pcap on the DNAAS Spine. The app's `dnaas-dp` path must pass the leaf host and DUT-facing leaf source port from LLDP, let the capture engine discover the mirror uplink unless explicitly supplied, and use a per-capture session name (`XRAY_<capture_id>`) instead of a fixed shared session name so cleanup targets the right mirror session.

**Capture lifecycle:** Capture continues when popup is closed (toast on completion). Re-opening XRAY for same link while capture runs restores Stop/status UI. Panning (middle-mouse or space+drag) calls `temporaryHide()`; on pan end `temporaryShow()` repositions popup from link midpoint.

**Editor state:**
- `editor._xrayCapturing` — link ID with active capture (button turns orange)

**Settings:** Left toolbar Packet-Capture section (collapsible) — Mac IP, Mac user, Mac password, Wireshark path, pcap directory. Save writes via `POST /api/xray/config`. Verify Mac tests SSH via `POST /api/xray/verify-mac`.

**Mac-verification gate (Apr 2026)** — mandatory two-tier lockout for mac/mac-live captures:

Cursor `/XRAY` command preflight:
- Every `/XRAY` invocation must start `python3 ~/.cursor/tools/xray_mac_preflight.py` in parallel with its initial learning/cache/config reads. This is an SSH-auth identity check against the last known Mac IP, not ping.
- If the preflight fails/refuses/times out, the agent must AskQuestion immediately for `Enter current Mac IP` / `Use server-only for this run` / `Cancel` before starting the capture or Mac upload/open.
- A cached verified IP is only the next candidate to test. It must not be treated as valid without the per-invocation SSH preflight.

Contract:
1. `POST /api/xray/verify-mac` **must succeed for the current `mac.ip_vpn`** before any mac/mac-live capture can start. On success, the server persists `mac.verified_ip`, `mac.verified_at`, `mac.verified_by` in the caller's per-user `~/.topology_users/<u>/xray.json`.
2. `POST /api/xray/run` reads those fields and **refuses** the request (returns `{error: "Mac workstation not verified ..."}`) unless `verified_ip == mac.ip_vpn` **and** `verified_at` is within `_XRAY_MAC_VERIFY_TTL_SECONDS` (30 min). This is **backend defense-in-depth**; never rely on frontend gating alone.
3. `POST /api/xray/config` that changes `mac.ip_vpn` automatically clears `verified_*` so the user is forced to re-verify after any IP update.
4. Failed `POST /api/xray/verify-mac` responses must include a user-facing `error` plus a machine-readable `cause` (`auth_failed`, `ssh_refused`, `ssh_timeout`, etc.) so the toolbar and popup can tell the operator whether this is a wrong Mac password, Remote Login disabled, missing dependency, or reachability issue.

Frontend (`topology-xray-popup.js`):
- On popup open (and whenever mode/output change to something that needs Mac delivery), `_evaluateMacGate()` reads `/api/xray/config` and caches the verification state. If not valid, Start Capture is **disabled** (`data-mac-locked="1"`, tooltip `Verify Mac workstation before starting capture`) and an inline verify panel is rendered into `#xray-status` with an IP input + **Verify** + **Use pcap** buttons.
- The `Use pcap` button flips `_state.output = 'pcap'` so the user can still capture without a Mac round-trip.
- On a successful in-popup verify, the module fires `window.dispatchEvent(new CustomEvent('xray-mac-verified', { detail: { ip, at } }))` so any other open surface (e.g. the toolbar Verify Workstation button) picks up the new state.
- On `/api/xray/run` returning a Mac-verification error, the popup re-locks the button and re-renders the verify panel instead of showing a generic error.
- **Never** silently proceed on a verify-mac exception -- the pre-Apr-2026 `catch (verr) { console.warn; proceed }` bug is the anti-pattern that motivated this gate. A failing verify keeps the button locked.

Toolbar (`topology-toolbar-setup.js`):
- The "Verify Workstation" button dispatches `xray-mac-verified` on success so an already-open XRAY popup unlocks immediately.
- Saving a new `mac.ip_vpn` dispatches `xray-mac-ip-changed` so the popup re-evaluates (backend has already cleared the verification, so the popup will render the verify panel).

Regression test vectors: (a) open XRAY popup with stale cached IP -> Start Capture must be disabled until Verify succeeds; (b) curl `/api/xray/run` with mac output and no verification -> must return error, not start a capture; (c) change IP in settings after verifying -> Start Capture must re-lock without a page refresh; (d) verify, wait 31 minutes, click Start Capture -> gate must re-lock and require re-verify.

### Brand Assets
- **LingoApp**: Official DriveNets brandbook is at https://www.lingoapp.com/110100/k/d5jKxQ — requires LingoApp login to download. Cannot be fetched programmatically.
- **Local branding**: Use `CURSOR/branding/` PDFs (fetched from Mac) for color/logo reference. Extracted logos in `branding/extracted/`.

### Brand Integration (DriveNets)
- **Logo**: Top-bar SVG in `index.html` — three horizontal capsule bars + diagonal slash (DriveNets symbol). Favicon: `branding/extracted/OUR_LOGO_p1_i5_180x180.png`.
- **Icon mapping** (SVG symbols in `index.html`):
  - `ico-router` — DriveNets Routers (rounded rect with 4 crossing arrows + arrowhead tips). Used: Device section header, context menus, Place Device.
  - `ico-dn-switch` — DriveNets Network Switch (rect with converging lines/arrows).
  - `ico-dn-chassis` — DriveNets Network Chassis (rect with vertical slots).
  - `ico-dn-cloud` — DriveNets Cloud (cloud outline).
  - `ico-dn-server` — DriveNets Server/Storage (stacked rack units with indicator dots + stand).
  - `ico-dn-tower` — DriveNets Cell Tower (tower with signal arcs).
  - `ico-dn-firewall` — DriveNets Firewall (shield with grid lines).
  - `ico-globe` — Wireframe globe. Used: curve mode "Use Global Setting".
  - `ico-discover` — Network Operations (cloud with nodes). Used: DNAAS discovery.
  - `ico-network` — Branch (building with peaked roof). Used: network-related UI.
- **Topologies button icon**: `#topo-btn-icon` — layer stack SVG updated dynamically by `FileOps._updateTopoBtnIcon()` to show domain colors on each layer.
- **Button active states**: DNAAS (`.dnaas-panel-open`), Network Mapper (`.nm-panel-open`), and Topologies (`.topologies-open`) buttons retain their base glass appearance with only a highlighted outline glow when open.
- **Topology indicator transitions**: `updateTopologyIndicator()` uses fade+slide animation when switching between topologies.
- **Extraction scripts**:
  - `branding/extract_images.py` — extract images from all brand PDFs.
  - `branding/extract_icon_svgs.py` — crop individual icon PNGs from Drivenets Icons PDF (grid crop) and export full-page SVGs for pages 2–3. Run: `python3 extract_icon_svgs.py`. Output: `branding/extracted/icons/` (300 PNGs), `branding/extracted/icons_page*_full.svg`.

### Backend API Reliability (Mar 2026)

**Request chain**: Browser JS -> serve.py:8080 (proxy) -> discovery_api.py:8765 -> NetworkMapperClient (SSE) -> MCP Server

**Improvements:**
- **LLDP proxy**: `topology-lldp-dialog.js` routes via `/api/dnaas/*` (relative URLs) so it works when deployed to h263; no direct port 8765 calls.
- **MCP session reuse**: `network_mapper_client.py` caches SSE sessions (120s TTL) to avoid 5s handshake per tool call.
- **MCP singleton**: `discovery_api.py` uses `_get_mcp_client()` instead of per-request `NetworkMapperClient()`.
- **MCP single-worker-task architecture (Mar 2026)**: Root-cause fix for the `RuntimeError: Attempted to exit cancel scope in a different task` crash. `NetworkMapperClient` now runs a single persistent asyncio Task on a dedicated daemon thread. All MCP calls from any thread are submitted to this worker via `asyncio.Queue`. The worker owns the SSE session exclusively -- context managers are always entered and exited in the same Task, which is what `anyio` requires. Old design used `ThreadPoolExecutor` + `asyncio.run()` per request, creating separate event loops and Tasks that triggered the cross-task crash during session cleanup/GC.
- **MCP auto-reset**: `_mcp_call()` wrapper in `discovery_api.py` retries with client reset on network failures. Now simplified since the root cause (cross-task SSE) is eliminated.
- **Health endpoint**: `GET /api/health` on discovery_api.py returns `{status, mcp_client, uptime_s}`. `serve.py` probes this on 502 to give the UI a specific error (API running but MCP broken vs API not responding).
- **Proxy retry**: `serve.py` uses 30s timeout for GET, 300s for POST; 1 retry with 2s backoff on connection errors; 502 includes endpoint and detail from health probe.
- **XRAY hint clarity**: XRAY popup distinguishes 502 (API down, shows detail from health probe) from network error (server not running) from LLDP-not-found (no neighbors).
- **Job cleanup**: `_nm_cleanup_old_jobs()` and `_cleanup_old_discovery_jobs()` remove completed jobs older than 30 minutes.
- **Error feedback**: LLDP dialog shows API/SSH/MCP-specific errors; Network Mapper shows toast after 3 poll failures; DNAAS distinguishes API-down vs SSH vs timeout.
- **CP direction BPF fix (Mar 2026)**: `cp_capture.py` now injects `outbound`/`inbound` BPF primitives into the filter expression when direction is egress/ingress. Previously direction was only used for analysis labeling, not filtering -- CP captures always grabbed both directions regardless of the panel setting.

### Service Orchestration (Mar 2026)

**serve.py as orchestrator**: When started, serve.py auto-launches `discovery_api.py` (port 8765) and `scaler_bridge.py` (port 8766) as child processes if not already running. A background monitor thread health-checks both every 15s and restarts on crash or after 3 consecutive health failures. Crash-loop protection: stops restarts if a service crashes 5+ times within 2 minutes.

**Auto-reload**:
- `scaler_bridge.py`: Started with uvicorn `--reload` — auto-restarts when its Python files change.
- `discovery_api.py`: Monitor thread checks mtime of `discovery_api.py`; if changed since last start, restarts the process.

**start.sh**: One-command launcher at project root. `./start.sh` kills any existing instances on 8080/8765/8766, optionally starts Network Mapper MCP if `~/network-mapper` exists, then runs `python3 serve.py`. `./start.sh --stop` stops all. `./start.sh --watch` monitors `serve.py` for changes and restarts the full stack when it changes.

**Health endpoint**: `GET /api/health` returns aggregated status: `{ serve, discovery_api, scaler_bridge }` with `status`, `port`, `pid`, `uptime_s` for managed services; `managed: false` when a service was already running before serve.py started.

### 503 Errors and Scaler Bridge Resilience (Mar 2026)

**Root causes of 503 on scaler_bridge-dependent endpoints** (`/api/config/*`, `/api/operations/*`, `/api/devices/{id}/test`):

| Cause | Source | Detail | Fix |
|-------|--------|--------|-----|
| Bridge not running | serve.py proxy | "Scaler bridge unavailable: Connection refused" | Auto-fixed: on-demand restart in proxy + monitor thread |
| Device resolution failed | scaler_bridge | "Could not resolve IP for 'X'. Set SSH address on canvas device." | Right-click device > Set SSH (IP or serial) |
| SSH failed | scaler_bridge | "SSH to X failed: ..." | Check credentials, network, device reachability |

**Root cause bugs fixed (Mar 10 2026):**
1. **Monitor ignored unmanaged services**: `_service_monitor()` wrapped health checks in `if proc is not None:` -- services not started by serve.py (or where startup returned None) were never monitored or restarted. Fixed: monitor always health-checks both services regardless of proc handle.
2. **Health endpoint reported "dead" not "down"**: When a managed proc died, `_handle_health()` reported `"status": "dead"` instead of probing the actual port. Frontend `checkHealth()` only checked for `=== 'ok'`, so "dead" was treated as down forever. Fixed: health endpoint now probes the port directly when proc is dead/absent.
3. **No on-demand restart**: When the proxy hit a connection error, it returned 503 and waited for the 15s monitor cycle. Fixed: proxy now attempts an on-demand bridge start on first failure, retries the request if startup succeeds.
4. **404 triggered false bridge-down**: `getLimits()` treated 404 (device not found) same as 503 (bridge down), putting the bridge in a 60s cooldown. Fixed: 404 returns default limits without touching bridge state.
5. **60s cooldown too long**: With auto-restart in place, bridge recovers in ~2s. Cooldown reduced from 60s to 15s.

**Auto-recovery mechanisms (serve.py):**
- **On-demand restart**: When a proxy request fails with connection error, serve.py starts the bridge immediately and retries the request (single retry).
- **Monitor thread**: Every 15s, checks if bridge proc is dead or health-check fails 3x in a row. Auto-restarts with crash-loop protection (max 5 restarts per 2min window).
- **Startup**: `_start_scaler_bridge()` checks if bridge is already responding before starting a new one. If it can't connect, starts uvicorn subprocess.

**Frontend resilience** (scaler-api.js):
- `_bridgeUp` / `_bridgeRetryAfter`: When 503 contains "Scaler bridge unavailable", skip requests for 15s and show friendly message.
- `testConnection`, `getJobs`, `getLimits`: Check bridge state before requesting; on cooldown, try `checkHealth()` to recover.
- `checkHealth()`: If `scaler_bridge.status === 'ok'`, resets `_bridgeUp` so subsequent requests proceed.

**Silent 503 paths** (topology-notifications.js): `/api/config/`, `/api/operations/`, `/api/devices/` — no toast for 503 (user sees error in ScalerGUI notification). Red console line is browser-built-in and cannot be suppressed.

**Debugging**: Run `curl http://localhost:8080/api/health` to see bridge status. If `scaler_bridge.status` is "down", check `journalctl --user -u topology-app.service` for startup errors.

### Graceful-Restart Announcement (Apr 2026)

Intentional backend restarts (auto-recovery from the external monitor, manual deploys) used to leave the user staring at a wall of red `ERR_CONNECTION_REFUSED` lines in DevTools while the app came back up. The graceful-restart announcement turns that ~5s window into a calm "Backend restarting..." chip in the bottom-right corner with no visible errors.

**Backend pieces:**
- `_sse_publish_all(event)` in `serve.py` -- fans an event to every active SSE subscriber, used for service-wide signals. The existing per-user `_sse_publish` is unchanged.
- The SSE writer honors a `_event_name` payload key (popped before serialization), so a single SSE channel multiplexes both `topology-updated` and `service-restart` events without breaking older `topology-updated`-only listeners.
- `POST /api/monitor/announce-restart` (`_handle_announce_restart`) -- loopback-only, no JWT. Body: `{reason, eta_seconds, source}`. Updates `_RESTART_ANNOUNCE` and broadcasts a `service-restart` event with `{kind: "imminent", reason, eta_seconds, source, at}`.
- `GET /api/monitor/health` includes `restart_announce: {announced_at, reason, eta_seconds, source, age_s, recent}` so a tab that loaded mid-restart still sees the heads-up via snapshot polling.
- **Important:** `do_POST` already drains the request body and forwards it to handlers. New POST handlers MUST accept the body as a parameter -- do NOT re-read `self.rfile`, that will block the worker waiting for data that's already been consumed.

**Health-monitor pieces:**
- `_announce_restart(reason, eta_seconds, source, settle_s=1.5)` POSTs the announce, sleeps `settle_s` so the SSE event flushes, then returns. Best-effort -- failure to announce never blocks the actual restart.
- `_do_restart(unit, dry_run, reason)` calls `_announce_restart(...)` first, then runs `systemctl --user restart`.
- `--announce REASON --announce-eta N --announce-source LABEL` -- standalone CLI for manual deploys: announce, then run `systemctl --user restart topology-app.service` yourself. Does NOT restart anything on its own.

**Frontend pieces (load order matters: `topology-graceful-restart.js` MUST come before any module that opens a WS/SSE/poll):**
- `topology-graceful-restart.js` -- defines `window.GracefulRestart` with `isInWindow()`, `secondsRemaining()`, `markActive()`, `applySnapshotHint()`, `onChange()`. On boot it polls `/api/monitor/health` once to consume any in-flight announce, then attaches a listener for `service-restart` to the existing `window._topologyEventSource` (or opens its own if one isn't shared yet). Renders a self-cleaning bottom-right chip and dispatches `topology:graceful-restart-active` / `...-cleared` events.
- `topology-file-ops.js` exposes its EventSource as `window._topologyEventSource` and registers the `service-restart` listener directly. Also defers SSE auto-reconnect until the announced window expires.
- `topology-canvas-drawing.js` job-watcher skips `ScalerAPI.getJobs()` while in the window.
- `topology-device-events.js` defers WS reconnect while in the window.
- The window auto-clears as soon as `/api/health` reports `serve/discovery_api/scaler_bridge` all `ok` again.

**Why a window and not just "until the next event":** the announced ETA gives every consumer a hard upper bound. If the backend never comes back (worst case), the window times out and modules resume normal loud reconnects -- we never trade availability for quiet.

### Dialog Keyboard Isolation & AutoSave Safeguards (Mar 2026)

**Critical bug found and fixed:** The global keyboard handler (`topology-keyboard.js`) is
attached to `document` in capture phase, meaning ALL keystrokes site-wide are processed --
even when floating dialogs (Stack, LLDP, XRAY) are open. This caused accidental object
deletion when the user pressed Delete/Backspace, and full canvas wipe via Ctrl+X, while
interacting with a dialog. The Stack dialog's refresh button (which fetches SSH data for
5-10 seconds) was the trigger point -- during the async wait, any keystroke was processed
by the canvas editor.

**Fixes applied (6+ files):**
- `topology-keyboard.js`: Dialog guard at top of `handleKeyDown` uses `document.querySelector`
  to check for interactive modal/overlay elements by ID. Covers: enable-LLDP overlay, DNAAS
  dialogs, save/export pickers, style palettes, width/curve/style popups, text/link/device
  editor modals (`.show` qualifier), recovery modal, shortcuts modal. All popup elements are
  created dynamically and removed on close, so DOM existence = visible. **Read-only panels
  (Stack, LLDP, XRAY, git-commit) are intentionally excluded** so canvas shortcuts work while
  viewing reference data -- those panels use defense-in-depth via `stopPropagation` on their
  own keydown/keyup handlers. Also added confirmation prompt to Ctrl+X (clear canvas).
- `index.html`: Canvas element has `tabindex="0"` so it can receive keyboard focus. Required
  for remote access (server IP URL) where the browser may not auto-focus the page content.
- `topology.js`: `canvas.focus()` called after editor construction to grab keyboard focus.
- `topology-mouse-down.js`: `canvas.focus({ preventScroll: true })` on every mousedown to
  maintain keyboard focus after clicking the canvas.
- `styles.css`: `#topology-canvas { outline: none; }` suppresses browser focus outline.
- `topology-stack-dialog.js`: Added keyboard event isolation (`stopPropagation` on keydown
  and keyup). Set `tabindex=-1` and auto-focus on open. Defense in depth.
- `topology-lldp-dialog.js`: Same keyboard isolation pattern.
- `topology-xray-popup.js`: Same keyboard isolation pattern.
- `topology.js` (`autoSave`): Added object count sanity check -- refuses to save if object
  count dropped by more than 70% from last save. Added rotating backup (`topology_autosave_backup`
  key in localStorage). Added `recoverTopology()` console command for emergency recovery.
- `topology-files.js` (`saveRecoveryPoint`): Added empty-state guard and same 70% drop check.

**Rule for ALL new dialogs/modals:** Every floating dialog MUST include:
1. `dialog.addEventListener('keydown', (e) => { e.stopPropagation(); });`
2. `dialog.addEventListener('keyup', (e) => { e.stopPropagation(); });`
3. `dialog.tabIndex = -1;` (allows focus)
4. `dialog.focus();` after appending to document.body
5. An `id` attribute that matches the selector list in the keyboard handler's dialog guard (for interactive modals that should block canvas shortcuts).

**Recovery commands (browser console):**
- `checkAutoSave()` -- shows all backup sources with object counts and timestamps
- `recoverTopology()` -- restores from the backup with the most objects

### LLDP Animation & Dialog Fixes (Mar 2026)

**Root causes fixed:**
- **TB disappearing during LLDP enable**: `_drawCanvasWaveDots` and `_drawPulsingGlow` had no delegation in `topology.js` and used `editor` as a free variable. The TypeError crashed inside `ctx.save()` without `ctx.restore()`, corrupting canvas state and hiding all subsequent objects (TBs, text). Fixed by adding delegations and passing `editor` as first parameter.
- **No link animation**: Same root cause -- wave dots along connected links never rendered because `editor._drawCanvasWaveDots()` was undefined. Fixed with the delegation.
- **Table format inconsistency**: Initial LLDP load used 300+ lines of inline table HTML while refresh used `_buildLldpTableHtml`. These drifted apart (different grouping, colors, field name priorities). Fixed by unifying both paths through `updateLldpContent` -> `_buildLldpTableHtml`. Also added missing Port Mirror and Snake group support to `_buildLldpTableHtml`.
- **Safety**: Added try-catch around `_drawLldpEffects` in canvas drawing to prevent canvas corruption on future errors.
- **SSH host resolution gap (Mar 2026)**: Multiple flows passed only `serial` (device label like "P-SA-2") to APIs without the device's management IP. When the label does not resolve via DNS or Scaler DB, SSH failed silently. Comprehensive fix across all 8 affected call sites:

**Backend (`discovery_api.py`):**
- `_fetch_lldp_neighbors(serial, ssh_host=None)` -- uses `ssh_host` directly when provided, skipping DNS resolution.
- `_enable_lldp_on_device(serial, ..., ssh_host=None)` -- same pattern, uses mgmt IP when frontend provides it.
- `_resolve_serial_to_host(serial)` -- now checks `device_inventory.json` `mgmt_ip` as final fallback after DNS and Scaler DB.
- `GET /api/device/{serial}/lldp` -- accepts `?ssh_host=IP` query param for SSH fallback.
- `POST /api/enable-lldp` -- reads `ssh_host` from body and passes to `_enable_lldp_on_device`.
- `POST /api/lldp-neighbors` -- reads `ssh_host` from body and passes to `_fetch_lldp_neighbors`.
- `POST /api/lldp-neighbors-live` -- reads `ssh_host` from body and passes to `_fetch_lldp_neighbors`.

**Frontend (JS files):**
- `topology-lldp-dialog.js`: `_fetchLldpNeighbors(serial, device)` and `_fetchLldpNeighborsLive(serial, device)` pass `device.sshConfig.host` as `ssh_host`.
- `topology-xray-popup.js`: `_fetchLldpForDevice` and `_fetchDeviceInterfaces` append `?ssh_host=` from `device.sshConfig.host`.
- `topology-link-details.js`: `autoFillFromLldp` passes `device1.sshConfig.host` as `?ssh_host=`.
- `topology-dnaas-helpers.js`: `_showNoLldpDialog` enable-LLDP button resolves the device from canvas and passes `sshConfig`.
- `bundle.js`: `_enableLldpOnDevice(serial, sshConfig)` and `showEnableLldpDialog(serial, sshConfig)` accept and forward `sshConfig`.

**Bridge (`scaler_bridge.py`):**
- `_build_device_context` LLDP fallback now appends `?ssh_host={mgmt_ip}` when calling discovery_api.

**Resolution priority (unified):** NetworkMapper MCP > Scaler DB > device_inventory.json > `ssh_host` param > DNS with domain suffixes > direct serial.

### Network Mapper (Mar 2026)

**Overview**: Recursive LLDP-based network discovery that auto-generates debug-dnos-quality topology diagrams from live devices. Supports up to 200 devices with hybrid hierarchical/force-directed auto-layout.

**Key files:**
- `topology-network-mapper.js` — Frontend module: panel UI, discovery control, hybrid layout, rich topology generation, save to domain
- `discovery_api.py` — Backend: `_nm_bfs_crawl()` BFS engine with DNAAS/canvas-aware resolution, MCP enrichment, `/api/network-mapper/start|status|stop` endpoints
- `serve.py` — Proxy `/api/network-mapper/*` to discovery_api.py

**Data flow:**
1. User opens Mapper panel (top-bar button or `N` key), enters seed device IP(s)
2. Frontend collects canvas devices with SSH config as `known_devices`
3. "Start Discovery" → `POST /api/network-mapper/start` with seeds, credentials, limits, known_devices
4. Backend resolves neighbors using known_devices first (DNAAS-aware), then DNS/SCALER DB/inventory
5. MCP path enriches with `get_device_system_info` + `get_device_interfaces_detail` (system_type, version, serial, interface speeds)
6. SSH path collects hostname, serial, system_type, DNOS version, LLDP, mgmt IP, interface brief
7. Frontend polls `GET /api/network-mapper/status?job_id=X` every 2s for live progress
8. On completion, "Generate Topology" creates debug-dnos-quality topology with:
   - Properly styled devices (visualStyle: classic/server/simple, role-based colors)
   - IP address labels below each device
   - System info panels above devices (system_type, version, serial)
   - Color-coded links by interface type (bundle-ether green, ge400 blue, hu400 orange)
   - Interface labels on-link in debug-dnos style
   - SSH config embedded for immediate SCALER use
9. "Save" stores to "Network Mapper" domain (auto-created section, color `#06b6d4`, icon `wifi`)

**Discovery sources (priority order):**
1. Canvas/DNAAS known devices — used for neighbor resolution and credentials
2. Network Mapper MCP (`get_device_lldp` + `get_device_system_info` + `get_device_interfaces_detail`) — enriched
3. SSH (`show system`, `show lldp neighbors`, `show interfaces management`, `show interfaces brief`) — full fallback
4. Device inventory / SCALER DB — for hostname-to-IP resolution

**Device classification (tier → visual):**
| Role | Tier | visualStyle | Color | Radius |
|------|------|-------------|-------|--------|
| NCM/superspine | 0 (top) | server | #c0392b | 50 |
| spine/NCC/RR | 0 (top) | server/classic | #9b59b6 | 50/40 |
| NCF/PE/router | 1 (mid) | classic | #3498db | 40 |
| CE/customer | 2 (bot) | simple | #2ecc71 | 30 |
| external/tester | 2 (bot) | server | #e67e22 | 30 |

**Link styling:**
| Interface | Color | Width | Style |
|-----------|-------|-------|-------|
| bundle-ether | #2ecc71 | 3 | solid |
| hu400/ce400 | #e67e22 | 2 | solid |
| ge400 | #85c1e9 | 2 | solid |
| mgmt | #95a5a6 | 1 | dashed |

**Auto-layout (hybrid):**
- Tier detection from `system_type` and hostname patterns
- If 2+ tiers: hierarchical Y by tier (250px spacing), force-directed X within tier
- If 1 tier: pure force-directed (repulsion + attraction + gravity, 500 max iterations)
- Minimum device spacing: 150px within tier, 180px in force-directed

**Editor state:**
- `editor.networkMapper` — NetworkMapperManager instance
- `editor.networkMapper._jobId` — active discovery job
- `editor.networkMapper._lastDiscoveryData` — latest discovery result (devices with interfaces, links)
- `editor.networkMapper._discoveryCredentials` — {username, password} used for SSH config on generated devices

**Panel UI:**
- Button: `#btn-network-mapper`, keyboard shortcut `N`
- Panel: `#network-mapper-panel` (liquid glass, cyan accent `#06b6d4`)
- Mutual exclusion with DNAAS panel and Topologies dropdown
- States: `.nm-panel-open`, `.nm-running` (spinning icon + pulse), `.nm-complete` (checkmark badge)

---

## Slash Command Knowledge Stores

For Cursor slash-command docs and learning stores in `~/.cursor/commands/`, `~/.cursor/*-reference/`,
`~/.cursor/*-docs/`, and `~/.cursor/skills/`:

- **Agent-facing knowledge should be tiered Markdown**:
  - `learned_index.md` = always-read compact summary (includes `Last synced:` timestamp)
  - `learned_rules.md` = detailed rules, read matching sections only
- **JSON remains the machine-compatible backing store** for tools and scripts. Do not break existing JSON readers unless you are also updating the tooling.
- **Staleness detection** (MANDATORY before reading any index):
  - Run `python3 ~/.cursor/tools/prune_learning.py --command <name> --check`
  - Exit code 0 = fresh, exit code 1 = stale (JSON is newer than mirror)
  - If stale, run `--sync-only` BEFORE trusting the index content
- **After any JSON write-back**, sync is MANDATORY (not optional):
  - `python3 ~/.cursor/tools/prune_learning.py --command <name> --sync-only`
  - Skipping this means subsequent reads use outdated rules
- **Auto-sync mode** for bulk operations:
  - `python3 ~/.cursor/tools/prune_learning.py --command all --auto-sync` syncs only stale stores
- **Backup-before-repair**: if a JSON file is malformed, the tool writes a `.bak` copy before
  attempting regex repair, then writes the repaired JSON back. No silent data loss.
- **Large methodology docs must be split** into:
  - a small TOC / quick-reference `SKILL.md` with a Learning Routing Table
  - targeted `sections/*.md` files loaded on demand
- **Command specs must follow the same reading protocol**:
  - always check freshness first (`--check`)
  - read the compact index / TOC
  - then load only the matching detail sections for the current mode or symptom
- **Self-learning has two paths**:
  - JSON-backed commands (BGP, XRAY, SPIRENT, HA, NETCONF): write to JSON, then MANDATORY sync
  - Direct-Markdown commands (/debug-dnos): edit the correct section file per the Learning Routing Table in SKILL.md

## DNOS CLI Syntax Corrections (Validated via MCP run_show_command on PE-4, 2026-03-09)

All commands below were tested live on YOR_CL_PE-4 (25.4.13.146_dev) using the Network Mapper
MCP `run_show_command` tool plus `search_cli_docs` for documentation cross-reference.

| Wrong (was in specs) | Correct (validated) | Files fixed |
|---|---|---|
| `show bgp ipv4 flowspec-vpn summary` | `show bgp ipv4 flowspec summary` | HA.md, BGP.md, debug-dnos.md, feature-ha-mapping.md, known-behaviors.md, learned_rules.md, route-injection.md, phase-procedures.md, debug-dnos.mdc |
| `show mpls lsp` | `show mpls route` or `show mpls forwarding-table` | HA.md, feature-ha-mapping.md, health-check.md |
| `show interfaces brief` | `show interfaces description` (Admin + Oper + Description) | HA.md, dnos-cli-discoveries.mdc |
| `show system process bgpd` | `show system process routing:bgpd` (container-prefixed) | HA.md, snapshots.md, cross-command-integration.mdc, dnos-cli-discoveries.mdc |
| `show system process isisd/fibmgrd` | `show system process routing:isisd` / `routing:fibmgrd` | Same as above |
| `show system process wb_agent ncp <id>` | `show system process wb_agent` (no `ncp` suffix -- shows all NCPs) | Same as above |
| `show system process interface-manager` | Not a valid name. Use `mgmt_interface_manager` or `ctrl_interface_agent` | Same as above |

**Process monitoring approach:** Process names in DNOS use container-prefixed syntax for
`show system process <name>` (e.g., `routing:bgpd`, `routing:fibmgrd`). The short names
(bgpd, isisd) are NOT valid arguments. Discover valid names via `search_cli_docs('show system process')`
or CLI `?` completion on device. Full process name list cached in
`~/.cursor/dnos-cli-completions.json`. Alternative: use container-scoped queries like
`show system ncc <id> container routing-engine` for all routing processes.

**CLI discovery protocol (search first, ask device second):**
1. `search_cli_docs(keyword)` -- PRIMARY. Searches 469+ DNOS commands. No SSH needed.
2. `get_cli_doc_section(doc_name, term)` -- full syntax details when search returns snippets.
3. `~/.cursor/dnos-cli-completions.json` -- cached dynamic values (process names, VRF names).
4. `run_show_command` on device -- only for uncached dynamic arguments.
Rule: `~/.cursor/rules/dnos-cli-completion-protocol.mdc`

## Lab recovery runbook (2026-03-20)

Reference: PE-4 cluster GI stack stuck (`gi-manager` 0/0), RR-SA-2 / PE-1 pre-delete config restore.

### PE-4 (YOR_CL_PE-4) NCC1 -- GI stack repair

1. From KVM: `ssh dn@100.64.6.6` (lab password), `sudo virsh console --force kvm108-cl408d-ncc1`.
2. Serial login: `dn` / `drivenets` when at `login:`.
3. If `gi-manager` is 0/0 and `docker service ps` shows `Rejected` / placement errors, run the **full cleaner** from Confluence QA page *Deployed SA Instead of Cluster - How to Recover Cluster* (docker swarm leave, prune, clear `ncc_id` / `cluster_id` / deploy-plans, `node_flavor`, reboot). Option A (`docker swarm leave --force` only) was not enough in this incident.
4. After reboot, confirm `docker service ls`: `gi-agent` and `gi-manager` both **1/1**.
5. DNOS deploy: `POST /api/operations/image-upgrade` with `upgrade_type` `gi_deploy`, URLs from `SCALER/db/configs/YOR_CL_PE-4/operational.json`, and `device_plans["YOR_CL_PE-4"].deploy_params` including `system_type` **CL-86**, `deploy_name` **YOR_CL_PE-4**, `ncc_id` **1** (active NCC1; do not rely on standby NCC0 for image pull per cluster behavior).

### Config restore via `/api/operations/push`

| Device | Source file | Notes |
|--------|-------------|--------|
| RR-SA-2 | `SCALER/db/configs/RR-SA-2/pre_delete_backup_sanitized.txt` | `push_method`: `file_upload`, `load_mode`: `merge`. Job completed with merge + commit. |
| YOR_PE-1 | `SCALER/db/configs/PE-1/pre_delete_backup_20260313_114931.txt` | Use config body from **line 55** onward (strip header comments). Push with `ssh_host` **100.64.4.200** when that is the live MGMT IP. |

### Push / IP resolution fixes (same serial, two config dirs)

When both `PE-1/` and `YOR_PE-1/` exist with the same `serial_number`, `operational.json` can disagree on `mgmt_ip`. Fixes applied:

- **`scaler_bridge._resolve_mgmt_ip`**: If `ssh_host` is an IPv4, always use that literal address for TCP; still resolve `scaler_id` from the ops index when the IP is a key (`ssh_ip_literal:`).
- **`scaler.utils.get_ssh_hostname`**: If `device.ip` (IPv4) differs from `mgmt_ip` in the ops file loaded by `device.hostname`, prefer **`device.ip`** so API-requested targets are not overridden by stale ops.

After changing these modules, sync live paths (`CURSOR/scaler_bridge.py`, `SCALER/scaler/utils.py`) and let uvicorn reload (or restart the bridge).

## Image Upgrade Wizard: DNOS vs GI mismatch (2026-03-21)

**Cause:** `operational.json` `device_state` values **`UPGRADING`** and **`DEPLOYING`** were classified as **GI** (same bucket as `GI`, `BASEOS_SHELL`). After an image job finished, a stale `UPGRADING`/`DEPLOYING` left in ops made the wizard and canvas show **GI** while the device was already on **DNOS**.

**Fix:**

- **`scaler/connection_strategy.py`**: `UPGRADING` / `DEPLOYING` return `""` from `classify_device_state`; removed from `GI_STATES`.
- **`scaler_bridge._device_status_from_cache`**: If mode is still empty but `dnos_ver` is present and `upgrade_in_progress` is false, set mode **DNOS**.
- **`scaler-gui.js`**: Wizard merge no longer overwrites **canvas DNOS** with cached GI-like modes; `_classifyDeviceState` aligned with Python.
- **`topology-device-monitor.js`**: Transient `UPGRADING`/`DEPLOYING` from context API do not force **GI** on the canvas (preserve prior mode or `unknown`).

## Cluster NCC management IP discovery (2026-03-21)

For KVM-backed clusters, DNOS CLI is reached reliably via **virsh console** from the KVM host. A **second** SSH session (background) can run `show interfaces management | no-more` on that console path, parse the IPv4, verify **dnroot/dnroot** SSH to that IP, then persist `ncc_mgmt_ip` and `ncc_mgmt_verified_at` in `SCALER/db/configs/<scaler_id>/operational.json`.

| Piece | Location |
|-------|----------|
| Discovery (blocking worker) | `scaler_bridge._discover_ncc_mgmt_ip_sync`, shared virsh setup `_open_virsh_ncc_shell_channel` |
| API | `POST /api/ssh/discover-ncc-mgmt`, `GET /api/ssh/check-port` |
| Proxy (serve.py) | Same pattern as `/api/ssh/probe` |
| Probe enrichment | `probe_connection` adds `ncc_mgmt_ip` / `ncc_mgmt_verified_at` when present in ops |
| GUI | `ScalerAPI.discoverNccMgmtIp`, `ScalerAPI.checkPort`; `topology-object-detection.js` opens **iTerm to cached `_nccMgmtIp`** when port 22 is reachable, else web virsh + background discovery |

`topology-object-detection.js` calls `_fireBackgroundNccDiscovery` after opening the virsh web terminal so the user session is not blocked.

## KVM cluster: dynamic `operational.json` + normal image upgrade (2026-03-21)

**Problem:** For `ncc_type: kvm`, `mgmt_ip` was often the **KVM host** (e.g. `100.64.6.6`). `_run_normal_upgrade` used `_ssh_connect_basic(mgmt_ip)`, which lands on BaseOS/Ubuntu, not DNOS CLI. `delete_deploy` / `gi_deploy` already used `connect_for_upgrade` (virsh-capable).

**Behavior now:**

| Trigger | `operational.json` updates |
|---------|----------------------------|
| `POST /api/ssh/discover-ncc-mgmt` (verified NCC IP) | `ncc_mgmt_ip`, `ncc_mgmt_verified_at`, and **`mgmt_ip` / `ssh_host`** set to that NCC IPv4 |
| `POST /api/ssh/probe` for `ncc_type == kvm` | First reachable **`ssh_mgmt` or `ssh_ncc`** IPv4 in probe results updates **`mgmt_ip` / `ssh_host`** if different (atomic write with `last_working_method` when applicable) |

**Normal upgrade (`_run_device_upgrade`, `upgrade_type == normal`):**

- If `ncc_type == kvm` (after console_mappings merge + re-read of `operational.json`): use cached **`ncc_mgmt_ip`** with **dnroot/dnroot** for `_run_normal_upgrade`.
- If KVM cluster but **no** `ncc_mgmt_ip`: **`connect_for_upgrade`** then `_run_normal_upgrade(..., pre_connected=(ssh, channel))`.

**GUI:** `_getWizardDeviceList` sets `ssh_host` / `ip` from **`sshConfig._nccMgmtIp`** when `_isCluster` so the Image Upgrade wizard passes the NCC target in `ssh_hosts`.

**Code:** `scaler_bridge.py` (`probe_connection`, `discover_ncc_mgmt_ip_endpoint`, `_run_normal_upgrade`, `_run_device_upgrade`); `scaler-gui.js` (`_getCanvasDeviceObjects`, `_getWizardDeviceList`).

## Major version jump detection -- forced delete_deploy (2026-03-20)

**CRITICAL RULE:** When the target DNOS major version differs from the current DNOS major version (e.g. v25.x -> v26.x), the upgrade MUST use `delete_deploy`, NEVER `normal` (target-stack load + install). Loading v26 images into a v25 BaseOS causes crashes and DNOS recovery mode.

**Detection points (all three must agree):**

| Layer | How it detects | Location |
|-------|---------------|----------|
| **Frontend (Plan step)** | Compares `curMaj` vs `tgtMaj` from parsed stack versions. Shows "MAJOR JUMP" badge in Compare step. Forces `upgrade_type: 'delete_deploy'` in device plan. | `scaler-gui.js`, Upgrade Plan step render |
| **Backend (`_run_device_upgrade`)** | Reads `dnos_version` from `operational.json`, extracts major from target DNOS URL via `_extract_version_from_dnos_url`. If majors differ, overrides `upgrade_type` to `delete_deploy`. | `scaler_bridge.py`, `_run_device_upgrade` |
| **Backend (`wait_and_upgrade` auto-plan)** | Same comparison during auto-plan generation. Logs `[WARN] Major version jump` and sets `_ut = "delete_deploy"`. | `scaler_bridge.py`, `_wait_then_upgrade` |

**Cluster upgrade with direct SSH auth fallback (2026-03-20):**

When upgrading KVM cluster devices via direct SSH to the NCC mgmt IP, the code now tests SSH auth before committing. If `dnroot/dnroot` fails (e.g. post-deploy VIP credentials not set), it falls back to `connect_for_upgrade` (virsh console through KVM host).

**Cluster operational fetch: virsh console fallback (2026-03-23):**

`_fetch_all_operational_via_ssh` now accepts `scaler_device_id` and falls back to `_fetch_ops_via_virsh_fallback` when direct SSH auth fails (common on KVM clusters where NCCs don't accept password SSH). The fallback:
1. Reads cluster info from `operational.json` (kvm_host, kvm_host_credentials, ncc_vms, active_ncc_vm)
2. Tries each NCC VM in order (stored active first, then others), connecting via `_open_virsh_ncc_shell_channel`
3. Detects standby NCCs (bash `$` prompt after dncli fails) and skips to next
4. Sends `show system stack | no-more` and `show lldp neighbors | no-more` through the virsh channel
5. Enters shell (`run start shell` + password) and runs `cat /.gitcommit` to get the git commit hash
6. Updates `active_ncc_vm` in operational.json when the stored value was stale
This also required fixing `_open_virsh_ncc_shell_channel` to handle the dncli sudo password prompt (sends `dnroot` / `drivenets` / `drive1234!`).
Root cause: PE-4's NCC at 100.64.4.98 rejects password SSH entirely; only virsh console from KVM host works.
`_fetch_git_commit_via_ssh` and `get_device_git_commit` endpoint also fall back to virsh for cluster devices.
The `_send_and_recv` channel helper was fixed to check the FULL accumulated output for the CLI prompt (last line ending with `#` or `>`), not individual chunks -- checking individual chunks would falsely match the command echo containing the hostname prompt.
Also fixed: `routes/ssh.py` was missing top-level `import time, json, os, re` causing probe_connection to crash with NameError (HTTP 500).

**Stack-live and git-commit performance (2026-03-23):**

Added `POST /api/devices/{id}/stack-live` endpoint in `routes/devices.py` -- calls `_fetch_all_operational_via_ssh` (with virsh fallback) instead of discovery_api's direct paramiko SSH. The frontend `_fetchStackLive` tries this scaler_bridge endpoint first, falling back to discovery_api only if needed.
The `get_device_git_commit` endpoint now checks `operational.json` cache before SSH/virsh. After the first virsh fetch, git_commit is cached and subsequent calls return in <5ms. The git commit popup in `topology-selection-popups.js` was also optimized: removed the slow `DeviceMonitor.refreshDevice` call from the fetch chain and goes straight to the fast `ScalerAPI.getDeviceGitCommit` endpoint.

**WARNING -- uvicorn --reload kills background jobs:**

The `_push_jobs` dictionary is in-memory. If `scaler_bridge.py` is modified while a `wait_and_upgrade` background thread is running, uvicorn's `--reload` restarts the process and kills the thread. NEVER sync `scaler_bridge.py` to the live path while a Wait & Upgrade job is active.

## Install prompt handling -- `_send_install_command` (2026-03-21)

**Problem:** `_run_normal_upgrade` used `_send_wait("request system target-stack install", 15)` which does NOT detect or answer the `Do you want to continue? (yes/no)` confirmation prompt. The device would time out waiting for "yes" and the install never happened. This caused upgrades to report "complete" without actually installing new images.

**Fix:** New `_send_install_command(chan, _log)` function (modeled after `_send_deploy_command`):

- Clears channel buffer before sending
- Polls every 0.5s for `yes/no`, `y/n`, `do you want`, or `continue` in output
- Sends `yes\n` when prompt detected
- Handles socket close (expected -- device reboots after install)
- 60s timeout (120 iterations x 0.5s)

**Post-install verification:** New `_post_install_verify` function runs after `_run_normal_upgrade`:

- Waits 60s initial (device rebooting)
- Reconnects via SSH every 20s (timeout 600s)
- Runs `show system install | no-more`
- Verifies each component version from URL appears in install output
- Logs PASS/FAIL per component (observational -- does not raise)

| Function | Purpose | Prompt handling |
|----------|---------|----------------|
| `_make_send_wait` | Generic send-and-wait for `#`/`>` prompt | NO -- bare `_send_wait` never answers yes/no |
| `_send_deploy_command` | `request system deploy` with yes/no | YES -- polls + auto-answers |
| `_send_install_command` | `request system target-stack install` with yes/no | YES -- polls + auto-answers |
| `_send_load_cmd` (in `_load_images_on_channel`) | `request system target-stack load` with overwrite prompt | YES -- checks `continue?`, `(yes/no)`, `overwrite` + Ctrl+C to background |

**RULE:** Any DNOS command that can prompt the user (`delete`, `deploy`, `install`, `load`) must use a prompt-aware sender, NOT `_send_wait`.

## Image loading in GI mode -- Ctrl+C background + proper progress polling (2026-03-22)

**Problem:** `_send_load_cmd` sent `request system target-stack load <url>` and answered `yes`, but in GI mode this command shows inline download progress and blocks the terminal prompt until download completes. The code never sent Ctrl+C to background the download, so all subsequent polling commands (`show system stack`) received garbage output or timed out. Additionally, `_poll_load_progress` used `show system stack` (which only shows images AFTER download+untar is complete) instead of `show system target-stack load | no-more` (which shows real-time `Progress: XX%`).

**Fix (two parts):**

1. `_send_load_cmd`: After answering `yes` and detecting `"Download in progress"` or `"started target-stack load"`, sends `\x03` (Ctrl+C) to background the download and return the `#` prompt. The download continues in the background per DNOS docs.

2. `_poll_load_progress`: Now uses `show system target-stack load | no-more` as PRIMARY source -- parses `Task status: in-progress/complete/failed` and `Progress: XX%`. Falls back to `show system stack` Target column only for final confirmation.

**Monitoring commands (correct usage):**

| Command | What it shows | When to use |
|---------|--------------|-------------|
| `show system target-stack load \| no-more` | Active download progress, Task status, Progress % | During download polling |
| `show system target-stack load history` | Completed/failed load tasks | After download for history |
| `show system stack` | Current + Target stack versions | After download complete to verify |

**Timeouts:** `max_wait` increased from 300s to 600s (large images), `stall_threshold` from 120s to 180s (network latency). Stall detection now tracks time since last progress change, not absolute elapsed time.

## Pre-deploy image verification and config repair (2026-03-21)

### Pre-deploy image verification

Before `request system deploy`, the flow now verifies that ALL expected images are present in the target-stack:

- Parses `show system stack` output for components with non-empty Target column
- Compares against the URL list (DNOS, GI, BaseOS)
- **BLOCKS deploy** with `RuntimeError` if any expected component is missing

This prevents the previous failure mode where deploy was sent with empty target-stack, and the device deployed with old/no images.

### Smart config repair after delete+deploy

`_post_deploy_config_repair` was rewritten to handle version-incompatible config:

1. **Full rollback attempt**: `rollback 1` + `commit`
2. **If commit fails**: Parse error output for specific failure patterns:
   - `configuration item 'X' is not supported` -- hierarchy removed
   - `Unknown word 'X'` -- keyword renamed
   - `invalid value` / `invalid keyword` -- syntax changed
3. **Partial repair**: Load rollback, `delete` each failed hierarchy, commit remainder
4. **Report to GUI**: Each failed hierarchy includes path, reason, and category

Config repair failure categories for user-friendly reporting:

| Category | Meaning |
|----------|---------|
| FlowSpec | FlowSpec syntax may differ between versions |
| BGP | Neighbor/AF structure changed |
| Interface | Interface naming differs |
| VRF/Services | Hierarchy restructured |
| Routing Policy | New vs old policy language |
| IGP/MPLS | Protocol config syntax changed |
| System | System-level config changed |

### Automatic gi-manager recovery (stuck deploy detection)

Added to `_post_deploy_verify` -- automatically detects and recovers from stuck gi-manager after a failed deploy. This handles the scenario where:

- Deploy was sent (e.g. v25 GI trying to deploy v26 images)
- Device reboots but comes back with old GI still running
- gi-manager Docker service is stuck at 0/0 replicas
- `gicli` is not available, `dncli` fails with "CLI is N/A"

**Pre-flight detection** (before loading images -- handles devices ALREADY stuck from a previous attempt):

- `_preflight_gi_health(job_id, device_id, chan, ssh, scaler_hostname, _log)` runs in both `_run_gi_deploy_upgrade` and `_run_delete_deploy_upgrade` (already-in-GI path)
- Tests GI CLI by running `show system stack | no-more` -- if the response doesn't contain table markers, GI CLI is broken
- If broken: navigates to bash, checks gi-manager, runs cleaner if stuck, waits for reboot, reconnects
- Returns new `(ssh, chan, ncc_id, recovered)` tuple so callers use the fresh connection

**Post-deploy detection** (in the post-deploy verify loop):

1. Track how long the device has been in GI mode (`gi_first_seen_at`)
2. After 10 minutes (`GI_STALL_THRESHOLD = 600s`) with no install progress:
   - Navigate to NCC bash shell via `_ensure_ncc_bash` (echo probe to distinguish bash from CLI)
   - Run `_check_gi_manager_health`: checks `docker service ls` for gi-manager replicas and `docker ps` for container version
   - If gi-manager is stuck (0/0 or missing): trigger automatic recovery

**Recovery steps** (`_run_gi_manager_recovery` -- full Confluence cleaner):

1. `sudo docker swarm leave --force`
2. `sudo docker system prune -a -f --volumes`
3. `sudo rm -f /etc/drivenets/ncc_id /etc/drivenets/cluster_id /etc/drivenets/deploy-plans /etc/drivenets/node_flavor`
4. `sudo reboot`

**Post-recovery retry** (back in the verify loop):

1. Wait for NCC to come back in GI mode (fresh gi-manager)
2. Reload all images via `_load_images_on_channel`
3. Re-send `request system deploy`
4. Continue waiting for DNOS mode (timeout reset for the retry)

**Safety**: Recovery is attempted only once per deploy (`gi_recovery_attempted` flag). Only triggers when `url_list` and `deploy_params` are provided (both `_run_gi_deploy_upgrade` and `_run_delete_deploy_upgrade` pass these).

**GUI phases**: `gi-recovery` (cleanup + reboot) and `gi-recovery-reload` (reloading images after recovery) are shown in the progress panel.

**Source**: Confluence QA "Deployed SA Instead of Cluster" recovery procedure. Validated on PE-4 (2026-03-20).

### KVM cluster GI preflight -- preserve virsh channel after failed dncli (2026-05-10)

PE-4 delete+deploy failed after `request system delete` because the GUI reached
the NCC host shell via `virsh->NCC`, tried `dncli`, failed to see a GI prompt,
then sent a blind `exit` even though the channel was already back at
`kvm108-cl408d-ncc1:~$`. On a KVM virsh console that closes the reusable
channel, so the next gi-manager health check fails with `Socket is closed`
instead of diagnosing/recovering gi-manager.

Rules for `_enter_dncli_from_bash` / `_preflight_gi_health`:

- After a failed `dncli` attempt, first probe for NCC bash with `_probe_ncc_bash`
  and return to the health-check path if bash is reachable.
- Do not send `exit` from a confirmed bash prompt; only use it when still stuck
  in a CLI layer.
- If the channel is already closed, reconnect with `connect_for_upgrade` before
  checking gi-manager health.
- Keep this path regression-covered by
  `topology/tests/test_upgrade_crash_recovery_unit.py`.

### Upgrade terminal per-device timestamp format (2026-05-10)

Per-device upgrade terminal lines must keep the frontend parser shape:

```
[LEVEL] DEVICE_ID: [HH:MM:SS] message
```

The timestamp intentionally lives after `DEVICE_ID:` because
`topology/scaler-gui-progress.js` routes lines to device cards by matching
`[LEVEL] device: message`. Use `_format_upgrade_terminal_line(level, msg,
device_id)` for new image-upgrade log lines instead of hand-building
`[INFO] <device>:` strings.

### Image Upgrade Wizard -- config hint (plan step)

Short orange info lines (not a wall of text):

- **GI deploy:** Clarifies no full system delete; config re-apply after DNOS; failures in log.
- **Delete + deploy:** Back up before delete, restore after DNOS; CLI mismatches in log.

Do not use the old single block that said "system delete + deploy" for GI-only plans (incorrect).

### Upgrade failure dismiss (canvas red badge)

When an image upgrade job fails, devices show a red **upgrade failed** badge. Dismiss is persisted in `localStorage` under `scaler_dismissed_upgrade_failures` as keys `jobId:deviceLabel` so the job watcher does not re-apply the badge. Actions: **Dismiss** / **New upgrade** on the bottom failure banner, and **Dismiss alert** / **New upgrade** on the completed failure progress panel.

### GUI device mode states

The upgrade wizard now supports these device mode badges (not just DNOS/GI):

| State | Badge color | When shown |
|-------|-------------|------------|
| DNOS | Green | Normal operation |
| GI | Cyan | GI/BASEOS_SHELL/ONIE |
| RECOVERY | Red | DN_RECOVERY |
| DEPLOYING | Orange (pulsing) | Deploy in progress |
| INSTALLING | Orange (pulsing) | Image install in progress |
| UPGRADING | Cyan (pulsing) | Upgrade flow active |
| BOOT | Purple (pulsing) | Device booting |
| FAILED/ERROR | Red (bold) | Operation failed |
| UNREACHABLE | Light red | SSH timeout/failure |
| CONFIG_REPAIR | Yellow (pulsing) | Config restoration in progress |

## Cluster post-upgrade recovery: NCP/NCF stuck disconnected (2026-03-22)

After `request system delete` + fresh DNOS deploy on a CL-86 cluster, only the active NCC
gets DNOS. All NCPs, NCFs, standby NCC, NCM remain `disconnected` if their GI agents fail
to register with the CMC on the new NCC. Full investigation methodology and remediation
steps are documented in `CLUSTER_POST_UPGRADE_RECOVERY.md`.

**Quick diagnosis checklist**:
1. `show system` -- NCPs/NCFs show `disconnected`, zero uptime, empty serial
2. `show system install` -- only NCC tasks completed, zero NCP/NCF tasks
3. `show system backplane` -- NCM ctrl ports UP but nodes show `unavailable-node`
4. `run start shell ncc <id>` then `ip netns exec host_ns ip neigh show` -- NCPs have ctrl-bond IPs but refuse SSH on port 22
5. CMC log (`cluster_manager_supervisor.log`) shows `CMC_SYS_EVENT_ACTIVE_DOWNSTREAM_EVENT` looping to `disconnected_nces`

**Root cause**: NCP GI agents are not running after system delete. The NCPs have network
connectivity (BaseOS level) but SSH/GI agent containers have not started.

**BGP flapping** (ACTIVE -> CONNECT every 10s) is a symptom: no NCP = no data plane
interfaces = no BGP peering possible with external neighbors.

**Remediation**: Console access to NCP (via IPMI or console server), then restart GI agent
or power-cycle. See `CLUSTER_POST_UPGRADE_RECOVERY.md` for full procedure.

## Legacy cluster deploy rule: ncc-id is autodetected by GI (2026-03-22)

For legacy clusters (CL-* system types with NCM + NCC, no NCCM):
- **NCM port 49 = NCC-0**, **NCM port 50 = NCC-1** (hardcoded in NCC ID allocation)
- The GI CLI **autodetects the ncc-id** via NCM LLDP at boot. The `ncc-id` parameter in
  `request system deploy` **MUST match the autodetected ID** or GI rejects with:
  `Cannot deploy with ncc id that doesn't match the auto detected id`
- Example: `kvm108-cl408d-ncc1` is connected to NCM port 50, so GI autodetects it as NCC-1.
  Deploying with `ncc-id 0` is REJECTED. Must use `ncc-id 1`.

**Key learning (2026-03-22)**: The earlier assumption that "always deploy with ncc-id 0"
was wrong. GI validates ncc-id against hardware detection. The cluster instability
(NCPs/NCFs disconnected) was NOT caused by ncc-id mismatch -- GI rejects mismatches outright.
The NCP/NCF disconnect is a separate issue (physical hardware not joining Docker Swarm).

**GUI behavior** (Image Upgrade Wizard):
- `scaler-gui.js`: upgrade plan builder tags CL-* devices with `is_cluster: true`, `system_type`.
  CLI preview shows `ncc-id autodetected by GI (NCM LLDP)` for deploy/delete-deploy.
  The `ncc_id` field is set to `'autodetect'` -- actual value must come from the device.
- `topology-ssh-dialog.js`: Cluster Components section shows NCM port mapping info.
- `devices.json`: PE-4 platform corrected from "NCP" to "CL-86" with `system_type: "CL-86"`.

**Source**: Confluence "NCC ID allocation post G.I." (page 2291892416) confirms the port mapping.

## Cluster preflight checks for upgrade wizard (2026-03-22)

Before deploying a cluster device, the upgrade wizard backend runs a preflight check:
1. Detects cluster devices by `system_type` starting with `CL-`
2. SSHes to the KVM host (from `connection_strategy` console config)
3. Runs `virsh list --all` to check all NCC VMs
4. If any NCC VM is **shut off**, the deployment is **BLOCKED** with a clear error

**Why this matters (incident 2026-03-22):**
- PE-4 deployment failed because `kvm108-cl408d-ncc0` VM was shut off (autostart=disabled)
- Only NCC-1 was running, so deploy went with `ncc-id 1` (autodetected by GI)
- Starting NCC-0 later (with old BaseOS 2.2610019013 vs NCC-1's 2.2620259017) caused
  a version mismatch that crashed DNOS on NCC-1 (routing_engine container went down)
- Both NCCs ended up in GI mode with no DNOS running

**Implementation:**
- `scaler_bridge.py`: `_cluster_preflight_check(scaler_id)` function, called from
  `image_upgrade_plan` endpoint's `_check_device`. Returns VM states, blocks if shut off.
- `scaler-gui.js`: Renders `upgrade-plan-preflight-fail` div with red alert showing which
  VMs are shut off and which KVM host to fix them on.
- `styles.css`: `.upgrade-plan-row--preflight-fail` and `.upgrade-plan-preflight-fail` classes.

**What the preflight checks:**
| Check | Blocked if |
|-------|-----------|
| All NCC VMs running | Any VM is shut off |
| VM count vs expected | Fewer running than expected (warning only) |
| KVM host reachable | Cannot connect to KVM (warning, not block) |

## NCC selector in upgrade wizard (2026-03-22)

For cluster devices (CL-*), the upgrade wizard now shows an **NCC selector dropdown**
in the upgrade plan table. This lets the user choose which NCC VM the deployment will
target and what `ncc-id` value to use in the `request system deploy` command.

**How it works:**
1. The `_cluster_preflight_check` backend function discovers running NCC VMs via
   `virsh list --all` on the KVM host.
2. It infers each VM's NCC ID from the VM name convention (e.g., `*-ncc0` -> NCC-0,
   `*-ncc1` -> NCC-1). This matches the GI autodetection from NCM LLDP port mapping.
3. The preflight result includes `ncc_options[]` -- an array of running NCC VMs with
   their inferred `ncc_id`, `vm_name`, and display `label`.
4. The frontend (`scaler-gui.js`) renders a `<select>` dropdown for cluster devices
   showing these NCC options. The user's selection updates `device_plans[did].deploy_params.ncc_id`.
5. The backend respects the frontend-provided `ncc_id` -- it only falls back to
   `operational.json` values when no `ncc_id` was provided by the frontend.

**Data flow:**
- Preflight: `_cluster_preflight_check` -> `cluster_preflight.ncc_options[]`
- Frontend: user selects NCC -> `plan.devices[did].deploy_params.ncc_id = N`
- Execution: `_do_one(did)` -> `plan.get("deploy_params", {})` -> `_run_device_upgrade`
- Deploy: `_send_deploy_command(chan, sys_type, d_name, ncc_id, _log)`

**CLI preview:** Shows the selected NCC-ID and VM name in the Execute step
(e.g., `PE-4: delete + deploy (full wipe | ncc-id 0 (kvm108-cl408d-ncc0))`).

**Fallback:** If no NCC selector data is available (preflight failed or not a cluster),
the deploy command falls back to the existing `ncc_id` from `operational.json` or
defaults to 0, with the GI retry logic flipping to `1 - ncc_id` on mismatch.

## Upgrade wizard: system_type source priority and GI Compare (2026-03-22)

**Problem:** `device_inventory.json` (DNAAS cache) can hold stale `system_type` strings
such as `SA-40C8CD, Family: NCR` for a cluster device, while `operational.json` under
`~/SCALER/db/configs/<device_id>/` has the correct value (e.g. `CL-86`).

**Fix (`serve.py` `/api/devices/`):** When merging `operational.json`, always apply
`system_type` / `deploy_system_type` onto the device entry so scaler cache wins over
inventory noise.

**Frontend (`scaler-gui.js`):**
- `_sanitizeWizardSystemType()` strips comma/`Family:` garbage and only keeps values
  that match `_WIZARD_KNOWN_SYS_TYPES` (GI CLI system-type list).
- `_getWizardDeviceListSync()` + `_mergeWizardDeviceListFromApi()` let the Image
  Upgrade Wizard open immediately; `GET /api/devices/` runs in the background to
  fill `platform` / mgmt IP.
- Compare step: if **all** selected devices are GI mode, branch-switch and
  compatibility alerts are hidden; the GI banner includes system type (when known),
  NCC hint for CL-* clusters, and a sample `request system deploy system-type ... name ...` line.

## Wrong system type deploy prevention (2026-03-22)

**Problem**: Deploying a device (especially a cluster) with the wrong `system_type` causes
catastrophic persistent contamination. On clusters, ALL NCEs (NCPs, NCFs, standby NCC)
keep the wrong `cluster_type` in `/golden_data/cm/cluster_type`. They refuse to join the
new cluster. Recovery requires running the cleaner script on every affected NCE manually.

**Root cause from PE-4 incident (2026-03-22)**: NCPs had `cluster_type=SA-36CD-S` from
an old deploy while the NCC was redeployed as CL-86. NCPs refused to join, showed
`disconnected` with zero uptime/serial. Fix: ran Confluence cleaner on both NCPs via
SSH -p 2222 (dn/drivenets). Source: [Deployed SA Instead of Cluster - How to Recover Cluster](https://drivenets.atlassian.net/wiki/spaces/QA/pages/5186093236).

**Detection (3 layers)**:

1. **GUI Wizard** (`scaler-gui.js`):
   - `_buildClientPlan()` tracks `previous_system_type` from `deviceContexts` and detects
     SA<->CL category changes. Sets `system_type_changed` and `system_type_category_change`.
   - Upgrade Plan table row shows red `upgrade-plan-systype-warn--critical` banner for
     SA<->CL changes with guidance about the cleaner script.
   - `collectData` blocks SA<->CL changes with "click Next again to confirm" pattern
     (`_sysTypeChangeAcknowledged` flag).

2. **Backend** (`scaler_bridge.py`):
   - `_check_system_type_change()` called before every deploy in `_run_delete_deploy_upgrade`
     and `_run_gi_deploy_upgrade`.
   - Compares `deploy_params.system_type` with `operational.json`'s stored type.
   - Logs `[CRITICAL]` warning for SA<->CL changes with recovery instructions and Confluence link.
   - Persists `previous_system_type`, `system_type_change_detected`, `system_type_change_at`
     to `operational.json`.

3. **Post-deploy monitoring**: If NCPs stay `disconnected` for >15min after NCC is `active-up`,
   the progress terminal output suggests the cleaner script.

**Key persistent files on NCEs** that cause wrong type:
- `/golden_data/cm/cluster_type` -- deployed type (SA-36CD-S vs CL-86)
- `/run/lock/nce_id`, `/var/opt/.ncc_id`, `/var/opt/.element_id` -- identity
- `/etc/cluster_id`, `/etc/node_flavor` -- cluster binding
- `/var/tmp/deploy-plans/*` -- cached plans

**Cursor rule**: `~/.cursor/rules/wrong-system-type-deploy-prevention.mdc` has the full
cleaner script, access methods, symptom matrix, and recovery procedure.

**CSS classes**: `.upgrade-plan-systype-warn`, `.upgrade-plan-systype-warn--critical`,
`.upgrade-plan-row--systype-critical` in `styles.css`.

## Platform model accepts any system type string (2026-03-22)

**Problem**: The `Platform` enum in `scaler/scaler/models.py` only had `NCP`, `NCM`, `NCP5`.
Devices with `platform: "CL-86"` (like PE-4) failed Pydantic validation silently in
`DeviceManager.list_devices()`, making them invisible in the scaler CLI and wizard.

**Fix**: Changed `Device.platform` from `Platform` enum to `str` field. Added `system_type`
and `connection_method` fields to the `Device` model. The `Platform` enum is kept for backward
compatibility with `WizardState` and `ValidationResult` internal models only.

**Key changes**:
- `scaler/scaler/models.py`: `Device.platform` is now `str`, added `system_type` and
  `connection_method` optional fields
- `scaler/scaler/device_manager.py`: `add_device()` and `update_device()` accept string
  platform and new fields
- `scaler/scaler/interactive_scale.py`: References to `Platform.DNOS` (which never existed)
  and `Platform.NCP` replaced with string `"NCP"`. WizardState creation gracefully handles
  non-enum platform values.
- `topology/scaler_bridge.py`: `_get_device_context()` now falls back to `operational.json`
  for `system_type` when device inventory doesn't have it
- `topology/topology-device-monitor.js`: Caches `system_type` from device context on
  `device._systemType` for instant wizard access

## Share Topology button + observability dialog (2026-04-19)

**Replaced** the legacy "My Topologies" domain pill in the top toolbar with a single
**Share Topology** button (`#auth-share-toolbar`). The legacy `#auth-domain-selector` div
is kept (hidden) so any older code paths that query it don't crash, but no longer renders.

**Module split:**
- `topology-domains.js` -- now state + API only, no DOM. Emits `topology-domains:changed`
  CustomEvent so other modules (the new share button) re-render. Hides
  `#auth-domain-selector` on init. Calls `TopologyShare.init()` after first fetch.
- `topology-share.js` (NEW) -- top-bar button + 4-tab modal:
  1. **Share** -- pick own domain card -> pick a topology (or whole domain) -> pick
     recipient users (search, multi-select, shows existing share badge) -> pick read/write.
  2. **Shared by Me** -- per-domain card with per-recipient table (avatar, role, permission
     badge, granted timestamp + relative time, granted_by). Per-row "Grant write" /
     "Make read-only" toggle and "Revoke" button. Per-card "Revoke all". Collapsible list
     of all topology files covered by the share.
  3. **Shared with Me** -- per-domain card with owner avatar, permission badge, "since"
     timer, granted-by/granted-at, collapsible topology file list, and an "Open" button
     that calls `TopologyDomains.selectDomain(compositeId)`.
  4. **Activity** -- audit log filtered by scope (`involving` / `owned` / `received`) with
     colored icons per action (`share`, `unshare`, `permission_change`).

**Backend additions** (all under `/api/domains/`):
| Method | Path | Purpose |
|---|---|---|
| GET | `/share/overview` | Counters for the dialog header (4 stat cards) |
| GET | `/share/targets` | Other active users -- visible to every authenticated user |
| GET | `/share/outgoing` | All my owned domains that are shared, with recipients + topologies |
| GET | `/share/incoming` | All domains shared with me, with owner + topologies |
| GET | `/share/activity?scope=...&limit=...` | Audit log entries (`scope` = `owned`/`received`/`involving`/`domain`) |
| GET | `/{domain_id}/shares` | Recipients of a specific owned domain |

**Schema changes** (`topology/api/auth/user_store.py`):
- New table `share_activity (id, ts, action, domain_id, domain_name, owner, actor,
  target_user, permission, notes)` indexed on ts/domain/owner/target.
- `share_domain()` and `unshare_domain()` write to `share_activity`. Actions:
  `share`, `reshare`, `permission_change`, `unshare`.
- `unshare_domain()` now auto-removes the `shared_domains` row when the last recipient is
  revoked, so `domains_shared_out` accurately reflects active shares.

**Schemas** (`topology/api/schemas.py`): `OutgoingShareInfo`, `IncomingShareInfo`,
`ShareRecipient`, `ShareActivityEntry`, `ShareOverview`, `ShareTargetUser`, `TopologyMetaLite`.

**CSS:** New rules in `styles.css` (search `Share Topology --` block) for the toolbar
button (`.share-topology-btn`), modal overlay (`.share-dialog-overlay`), tabs, stat cards,
permission badges (`.share-perm-read`, `.share-perm-write`), recipient tables, and the
audit-log feed (`.share-activity-row` with `--accent` per action).

**Cache busters bumped:** `styles.css?v=20260419a`, `topology-domains.js?v=20260419a`,
`topology-share.js?v=20260419a`. Updated in `index.html` AND synced to `/home/dn/CURSOR/`.

**End-to-end test (verified):** admin user shared `default` domain with `abishek` ->
upgraded to write -> revoked. The audit log captured all three actions, `share/overview`
returned correct counters at each step, and after the final unshare the `shared_domains`
row was auto-cleaned (counters back to 0).

## Per-User XRAY + API Hardening (2026-04-19)

Made the entire XRAY (Wireshark) capture pipeline and supporting device-discovery APIs
multi-user safe. Every authenticated user now sees only their own captures, credentials,
and workstation profile, and every layer (FastAPI bridge + the legacy threaded `serve.py`)
enforces JWT.

**Per-user storage layout** (`~/.topology_users/<username>/`):
| File | Purpose |
|---|---|
| `xray.json` | Per-user XRAY config (`mac`, `credentials`, `client.host_os`) -- replaces global `~/.xray_config.json` for authenticated users |
| `devices.json` | Per-user device credential overrides (highest priority in `_get_credentials`) |
| `captures/<device>__<ts>__<id>.pcap` | Per-user pcap output -- never shared between users |
| `client.json` | Workstation profile (`host_os` from `navigator.platform`, `user_agent`, `last_seen_at`) |

Helper: `api/auth/user_store.py` exposes `user_xray_config_path()`, `user_captures_dir()`,
`user_devices_credentials_path()`, `user_client_profile_path()`, all idempotent and rooted
at `Settings.user_data_root` (env override `TOPOLOGY_USER_DATA_ROOT`).

**Settings env-vars** (`api/config.py`):
| Var | Default | Purpose |
|---|---|---|
| `TOPOLOGY_DEVICE_INVENTORY` | `/home/dn/CURSOR/device_inventory.json` (fallback to `topology/device_inventory.json`) | Device inventory JSON path -- replaces all hardcoded `/home/dn/CURSOR/...` references |
| `TOPOLOGY_USER_DATA_ROOT` | `~/.topology_users` | Root for per-user JSON + captures |
| `XRAY_GLOBAL_CONFIG` | `~/.xray_config.json` | Legacy fallback used only when no JWT is present (admin tools, scripts) |

**Hardened endpoints:**
| Endpoint | Change |
|---|---|
| `GET /api/device/{name}/management-interfaces` | NEW. Returns structured `{interfaces:[{name, ipv4, mgmt_ip}]}`. XRAY needed it to resolve mgmt IPs; previously 404. Falls back to inventory when MCP is unavailable. |
| `GET /api/devices` (FastAPI) | Redacts `password`, `device_password`, `ssh_password`, `secret`, and `username` for non-admin roles via `_redact_device()`. Admin sees full record. |
| `GET /api/devices/{name}` | Same redaction. |
| `GET /api/device/inventory` (legacy `serve.py`) | Reads via `_inventory_path()` -- no more hardcoded `/home/dn/CURSOR/device_inventory.json`. |
| `GET/POST /api/xray/config` | JWT-required. POSTed body merges into the per-user `xray.json`; `client.host_os` field is preserved verbatim so future sessions can pick OS-correct defaults. |
| `POST /api/xray/start-capture` | JWT-required. Owner stamped onto the in-memory capture entry; pcap is written to `~/.topology_users/<user>/captures/<device>__<ts>__<id>.pcap` via `live_capture.py -f <path>`. |
| `GET /api/xray/captures` | Returns only entries where `_owner == current_user` (admin sees all). |
| `POST /api/xray/stop-capture` / `download` / `redeliver` | Reject when caller is not owner (and not admin). |

**`_get_credentials()` lookup order** (`routes/bridge_helpers.py`):
1. `~/.topology_users/<user>/devices.json[<device_name>]` -- explicit per-user override.
2. `~/.topology_users/<user>/xray.json["credentials"]` -- per-user defaults.
3. Global legacy `~/.xray_config.json["credentials"]` -- backward compatibility.
4. Hardcoded sane default (`dnroot/dnroot`).

The current JWT username is propagated transparently via `contextvars.ContextVar`
(`_current_user_ctx`) set by the JWT middleware in `scaler_bridge.py`, so existing
callers of `_get_credentials(device_name)` automatically become per-user-aware
without signature changes.

**Frontend OS-aware defaults** (`topology-toolbar-setup.js`,
`scaler-gui-wizards-security.js`):
- Detects OS from `navigator.platform` + `userAgent` (`macos` / `linux` / `windows` /
  `unknown`).
- Pre-fills `Wireshark Path` and `pcap Directory` with OS-specific defaults when the
  per-user value is empty:
  | OS | Wireshark | pcap dir |
  |---|---|---|
  | macOS | `/Applications/Wireshark.app/Contents/MacOS/Wireshark` | `~/Desktop/Packet-captures` |
  | Linux | `/usr/bin/wireshark` | `~/Packet-captures` |
  | Windows | `C:\Program Files\Wireshark\Wireshark.exe` | `%USERPROFILE%\Documents\Packet-captures` |
- Saves `client = { host_os, user_agent, last_seen_at }` alongside `mac` on every save
  -- the backend writes it into the per-user `xray.json`.
- `index.html` placeholders are now `auto-detected`; the JS swaps them to OS-correct
  hints once the config loads.

**Cache busters bumped:** `topology-toolbar-setup.js?v=20260419a`,
`scaler-gui-wizards-security.js?v=20260419a` in `index.html` AND synced to
`/home/dn/CURSOR/`.

**Files touched + synced to `/home/dn/CURSOR/`:**
`serve.py`, `discovery_api.py`, `scaler_bridge.py`, `api/config.py`, `api/main.py`,
`api/auth/user_store.py`, `api/routes/devices.py`, `routes/bridge_helpers.py`,
`topology-toolbar-setup.js`, `scaler-gui-wizards-security.js`, `index.html`.

**Validation:**
- `python3 -c "import api.config, api.auth.user_store, api.main, api.routes.devices,
  discovery_api, routes.bridge_helpers, scaler_bridge"` -- all OK.
- `python3 -m py_compile serve.py` -- OK.
- `node --check topology-toolbar-setup.js scaler-gui-wizards-security.js` -- OK.
- `ReadLints` on all touched files -- zero errors.

**Backward compatibility:**
- Existing single-user installs keep working: when no JWT is present, `serve.py` and
  `_get_credentials()` fall back to the legacy global `~/.xray_config.json`.
- The legacy `device_inventory.json` location is still tried as a final fallback if the
  env-var override is unset and `/home/dn/CURSOR/device_inventory.json` is missing.
- No DB schema migration is needed -- per-user JSON files are created lazily on first
  write.

## Shared Popover Docking (`window.TopologyPopover.position`) -- 2026-04-19

Both the Share Topology dialog and the Create Bug Topology dialog grow out of the same
topologies dropdown (`#topologies-dropdown-menu`). To avoid the two popovers implementing
drift-prone variants of the same math, `topology-share.js` now owns a single
**shared docking helper** and publishes it on the window:

```js
window.TopologyPopover.position(innerEl, anchorEl);
// innerEl  -- the .share-dialog-shaped inner panel (MUST carry class
//             `share-dialog` so the attached-left / attached-right / fade
//             styles in styles.css apply)
// anchorEl -- the element the user clicked (the dropdown pill / toolbar btn);
//             used as a positional fallback when the dropdown isn't visible
```

**Behavior contract (both popovers must match):**
| Scenario                                         | Where the popover lands                                                               |
|--------------------------------------------------|----------------------------------------------------------------------------------------|
| Dropdown is visible AND right-side has room      | Docks flush to the dropdown's right edge (zero gap), adds `.attached-left`             |
| Dropdown is visible AND only left side has room  | Docks flush to the dropdown's left edge, adds `.attached-right`                        |
| Dropdown is visible BUT no side has room         | Falls through to anchor-below (rare; viewport narrower than dropdown + popover)        |
| Dropdown not visible, anchorEl provided          | Anchor-below with right-edge clamp + `transform-origin` matching the anchor side       |
| No dropdown and no anchor                        | Top-right of the viewport (last-resort)                                                |

**Why this rule matters:** the `.attached-left` / `.attached-right` classes share a seam
with the dropdown by flattening the joined border-radius and removing one inner border.
If either popover forgets to add those classes (or picks a non-zero gap), the joined
edges stop reading as "one continuous surface" and revert to looking like an overlay.

**Load order** (enforced in `index.html`): `topology-share.js` is loaded before
`topology-bugs.js`, both with `defer`, so by the time `topology-bugs.js` opens a popover,
`window.TopologyPopover.position` already exists. The bug dialog keeps a small
self-contained fallback for defensive purposes but the shared helper should always win.

**Close animation parity:** both dialogs reuse the `.share-dialog.closing` +
`@keyframes shareDialogOut` styles in `styles.css`. `topology-bugs.js` now mirrors the
same close lifecycle as `topology-share.js`:
1. Set `dataset.closing='1'` on the overlay (re-entrancy guard)
2. Add `.closing` to the inner panel to start the 180ms fade+scale
3. On `animationend` (with a 300ms `setTimeout` safety net), remove `.open`, `.closing`,
   and the `closing` dataset marker
4. `open()` calls `_cancelPendingClose()` first so re-clicking the pill mid-close snaps
   instantly back to open

**When to reuse:** any future popover that should feel like an extension of the
topologies dropdown (e.g. "New Topology Wizard", "Domain Settings", "Upload Topology")
should use `window.TopologyPopover.position(inner, anchor)` and wrap its inner panel in
a `.share-dialog`-classed div, so the visual + docking + animation contract is free.

**Cache busters bumped:** `topology-share.js?v=20260419k`, `topology-bugs.js?v=20260419d`.

**Files touched + synced to `/home/dn/CURSOR/`:** `topology-share.js`, `topology-bugs.js`,
`index.html`.

## Per-Row Inline Share Forms (domain + per-file) -- 2026-04-20

**User-facing change:** the previous iteration rendered a single inline share form
under the domain title that re-listed every topology inside the domain -- but those
topology names were already visible in the domain's file list right below, so the
re-listing read as duplication. The icon for "share domain" also lived in the
title row, separate from the Save/Load actions, which felt inconsistent.

The current design has TWO compact inline surfaces (one at a time on screen):

1. **Domain-level share** -- opened by a third "Share" button in the Save/Load
   action row. No scope picker. No file list. Just the current recipients +
   chip-input for the whole domain.
2. **Per-topology share** -- opened by the share icon on an individual topology
   row. Inserts a sibling form DIRECTLY AFTER that row so the form visually
   belongs to the file it shares.

The previous "scope picker" (Whole domain / Specific files) is gone: the two
scopes are now chosen by WHICH button the user clicks. The topology list inside
the share surface is gone: it was redundant with the dropdown's own file list.

**DOM layout** (per domain row, with both share surfaces shown):

```
.custom-section-category[data-section-id=...]
├── .domain-title        (name + chevron -- NO share icon here anymore)
└── .domain-body
    ├── <button row>  [Save] [Load] [Share]     <-- three equal flex buttons
    ├── .domain-save-form                       (toggles via Save click)
    ├── .domain-share-form[.open]               <-- DOMAIN-LEVEL form
    │   ├── .dsf-head  (title + close button)
    │   └── .dsf-body
    │       └── .share-domain-item.expanded[data-domain-id=<d.id>]
    │           └── .share-domain-detail
    │               ├── _renderDomainRecipients(recipients)
    │               └── _renderShareForm(domain, recipients)   (chip input)
    └── .domain-topos-list
        ├── .domain-topo-row[data-filename=...]
        │   └── .topo-actions
        │       └── .ta-share  (per-file share icon, shows on row hover)
        └── .topo-share-form[.open]             <-- PER-TOPOLOGY form (transient)
            ├── .dsf-head
            └── .dsf-body
                └── .share-file-item.expanded[data-domain-id][data-topology-id]
                    └── .share-file-detail
                        ├── _renderTopologyRecipients(d, t, recipients)
                        └── _renderTopologyShareForm(d, t, recipients)
```

Only ONE inline form is visible at a time. Opening any other share button closes
whichever form is currently active, so the dropdown never stacks multiple share
panels.

**Key JS (in `topology-share.js`):**

| Function                      | Role |
|-------------------------------|------|
| `_getDropdown()`              | `document.getElementById('topologies-dropdown-menu')` shim |
| `_openTopologiesDropdown()`   | Opens + anchors the dropdown if closed |
| `_findDomainRow(domain, anchorEl)` | Locates the rendered `.custom-section-category`: (1) `anchorEl.closest('.custom-section-category')`, (2) `data-section-id` match, (3) title text match |
| `_ensureDomainShareHost(row)` | Lazily creates `.domain-share-form` inside `row > .domain-body`, inserted BEFORE `.domain-topos-list` so it appears between the buttons and the files |
| `_ensureTopoShareHost(topoRow)` | Lazily creates `.topo-share-form` as the immediate next sibling of a `.domain-topo-row` |
| `_cleanupOrphanTopoForms()`   | Removes any `.topo-share-form` that isn't the active one (guards against leftover sibling forms after list re-renders) |
| `_renderInlineSkeleton(host, title)` | First paint for EITHER surface: title + close button + skeleton body |
| `_renderDomainShareBody(host, d)` | Final paint for the domain form: wraps `_renderDomainRecipients + _renderShareForm` in `.share-domain-item.expanded[data-domain-id]` so `_attachHandlers` + targeted refresh helpers (`_refreshChipInput`, `_refreshTypeahead`, `_updateShareFooter`) work unchanged. Forces `draft.scope='domain'` since the scope picker isn't rendered. |
| `_renderTopoShareBody(host, d, t)` | Final paint for the per-file form: wraps `_renderTopologyRecipients + _renderTopologyShareForm` in `.share-file-item.expanded[data-domain-id][data-topology-id]` so per-file handlers (`submit-share-topo`, `revoke-topo`, `perm-toggle-topo`, `toggle-perm-topo`, `focus-input-topo`, `remove-chip-topo`) work unchanged. |
| `_openDomainShareAt(domain, row)` | Toggle + open for the domain form |
| `_openTopoShareAt(d, t, topoRow)` | Toggle + open for the per-file form |
| `_lookupTopology(domainId, idOrName)` | Resolves a topology from the cache by id, then by name |
| `_findTopoRow(domainRow, name)` | Finds the `.domain-topo-row` inside a domain by `.topo-entry-name` text or `data-filename` |
| `_refreshInlineForm()`        | Re-renders the ACTIVE form (domain OR topo) after a share/revoke/perm change |
| `_renderBody()`               | Alias for `_refreshInlineForm` (kept so every legacy action handler keeps working) |
| `_closeInline()` / `closeDialog()` | Removes `.open`, hides the form, clears `_activeInline`; for per-topology forms also removes the host node so it doesn't linger as a stray sibling |
| `openDialog(anchorEl)`        | Toolbar share pill entry: opens dropdown, picks active domain, opens domain form |
| `openForDomain(hint, topoName, anchor)` | Dispatches: `topoName` given -> per-topology form (finds row via `anchor.closest('.domain-topo-row')` or name match); otherwise -> domain form |

**State (module-level):**

- `_activeInline = { kind: 'domain'|'topo', row, domainId, host, topoRow?, topoId? }` -- the
  currently-active inline form, or `null`.
- `_refreshAll()` populates `_users`, `_outgoing`, `_outgoingFiles`, `_domainTopologyCache`,
  etc. so recipients + chip input always have fresh data.

**CSS contract (in `styles.css`, search `Two inline share surfaces`):**

- `.domain-share-form` and `.topo-share-form` share identical visual DNA
  (translucent surface `rgba(15, 22, 38, 0.55)` dark / `rgba(245, 248, 255, 0.85)`
  light, matching the liquid-glass panel language).
- `.topo-share-form` is indented (`margin-left: 22px`) to align with the topology
  row's text column, so it reads as a child of the row above.
- Fade + translate-Y animation via `opacity` + `transform: translateY(-4px) -> 0`
  when `.open` is added.
- `.dsf-head` holds the title + close button, with a 1px divider underneath.
- `.dsf-body` applies `font-size: 12px` so the shared `.share-form`,
  `.share-chip-input`, `.share-recipient-row` CSS renders compactly.
- Recipient rows and labels are slightly compressed (`padding: 4px 2px` on
  `.share-recipient-row`, `font-size: 10.5px` on `.share-detail-label`).

**Removed:**

- `.domain-share-btn` icon in the domain title row (replaced by the third
  `[data-action="share-domain"]` button in the Save/Load row).
- `_ensureShareFormIn`, `_openInlineAt`, `_activeInlineRow`, `_activeInlineDomainId`
  (replaced by `_ensureDomainShareHost`, `_ensureTopoShareHost`, `_openDomainShareAt`,
  `_openTopoShareAt`, `_activeInline`).
- `_renderInlineDomainBody` (split into `_renderDomainShareBody` +
  `_renderTopoShareBody`).
- Scope picker + file-list inside the share surface (now chosen by which button
  the user clicks).

**Public API unchanged:**

```js
window.TopologyShare.open(anchorEl);                         // toolbar pill -> domain form
window.TopologyShare.openForDomain(domainHint, null, anchor);   // domain form
window.TopologyShare.openForDomain(domainHint, topoName, anchor); // per-file form
window.TopologyShare.close();                                // close active inline form
window.TopologyShare.refresh();                              // refetch + re-render
```

**CloudAvatar helper (cross-module, unchanged):** `topology-share.js` still
publishes:

```js
window.CloudAvatar.svg(seed, sizePx);   // inline SVG markup
window.CloudAvatar.html(seed, sizePx);  // <span class="cloud-avatar">...</span>
```

`topology-auth.js` consumes it via a local `_avatarHtml(user, sizePx)` helper for
the top-bar user pill, auth dropdown header, and admin user list. Falls back to
initials when the helper isn't loaded.

**Bug dialog interop (unchanged):** `topology-bugs.js` still uses
`window.TopologyPopover.position(inner, anchor)` for its Create Bug Topology
popover. The share refactor did not touch that helper.

**Cache busters bumped:** `topology-share.js?v=20260420a`, `styles.css?v=20260420a`.

**Files touched + synced to `/home/dn/CURSOR/`:** `topology-share.js`, `styles.css`,
`index.html`.

## Inline Create-Bug Panel (Topologies dropdown) -- 2026-04-20

**User-facing change:** the "+ Bug" pill on the Bugs domain row used to open a
floating modal anchored beneath the pill (`.share-dialog-overlay` + popover
docking via `TopologyPopover.position`). It now opens an **inline connected
panel inside the Bugs row's `.domain-body`**, same visual DNA as the domain /
per-file share forms (`.dsf-head` + `.dsf-body` on a rounded translucent
surface). This keeps the user anchored to the Bugs domain they are writing
into and removes the floating-overlay context switch.

**One-at-a-time rule** is now enforced across **both** inline panels:

| User action                      | Effect |
|----------------------------------|--------|
| Open `+ Bug`                     | `TopologyShare.closeDialog()` first, then mount bug panel |
| Open any Share inline form       | `TopologyBugs.close()` first, then mount share panel |
| `+ Bug` while bug panel already up for Bugs row | Toggle -- closes the panel |

**DOM layout (Bugs row with the panel open):**

```
.custom-section-category[data-section-id="__bugs"]
├── .domain-title        (name + "+ Bug" pill + chevron)
└── .domain-body
    ├── <button row>   [Save] [Load] [Share]
    ├── .domain-save-form       (toggles via Save click)
    ├── .domain-share-form[.open]  (if share is active -- evicted on + Bug)
    ├── .domain-bug-form[.open]    (the new Create-Bug inline panel)
    │   ├── .dsf-head      (bug icon + "Create bug topology" + close X)
    │   └── .dsf-body
    │       ├── .bug-section.bug-main       (SW input + Jira status)
    │       ├── .bug-section.bug-jira-config (Set up / Edit credentials)
    │       ├── <details class="bug-advanced">  (manual overrides)
    │       ├── .bug-fetch-status / .bug-preview / .bug-not-a-bug
    │       └── .share-form-footer   (Create topology primary button)
    └── .domain-topos-list  (existing bug topologies)
```

**Key JS (in `topology-bugs.js`):**

| Function                | Role |
|-------------------------|------|
| `_getTopologiesDropdown()` | `document.getElementById('topologies-dropdown-menu')` shim |
| `_findBugsRow(anchorEl)`   | `anchorEl.closest('.custom-section-category')` first, then `[data-section-id="__bugs"]` |
| `_expandDomainBody(row)`   | Un-collapses the Bugs row if user had it closed |
| `_ensureInlineHost(row)`   | Removes any previous host, builds a fresh `.domain-bug-form` inside `.domain-body` before `.domain-topos-list`, wires events once |
| `_renderInlineHTML()`      | All the existing `.bug-section` / `.bug-jira-*` / `.bug-preview` / `.bug-not-a-bug` markup, now wrapped in `.dsf-head` + `.dsf-body` instead of `.share-dialog-overlay` + `.share-dialog` |
| `open(anchorEl)`           | Toggle-off if panel already mounted on this row; otherwise mount inline, reset fields, `_probeJiraConfig()`, focus SW input |
| `closeDialog()`            | Remove the `.open` class, then DOM-remove the host after 180ms fade |

**State (module-level):**

- `_jiraConfigured: null | true | false` -- probed once per open via
  `/api/users/me/jira-config`. Drives "Set up" vs "Edit credentials" visibility.
- No longer tracks `_activeAnchor` or popover positioning -- docking math is
  implicit in the row-embedded layout.

**CSS contract (in `styles.css`, same block as the share form):**

- `.domain-bug-form` is now part of the same `.domain-share-form, .topo-share-form, .domain-bug-form` selector list for frame, background, open-state fade.
- Bugs-specific accents only:
  - `inset 3px 0 0 rgba(231, 76, 60, 0.45)` -- subtle red left-stripe on the host.
  - `.domain-bug-form .dsf-head` color shifted to `#fca5a5` (dark) / `#b91c1c` (light).
- `.domain-bug-form .dsf-body` extends the shared rule with
  `display: flex; flex-direction: column; gap: 10px; max-height: min(60vh, 460px); overflow-y: auto` so the taller form (Jira creds + advanced + preview + "Not a bug" + hint + create footer) caps at a comfortable height instead of pushing the Topologies dropdown off-screen.

**Mutual exclusion hooks:**

- `topology-share.js`: `_openDomainShareAt()` and `_openTopoShareAt()` each
  call `window.TopologyBugs.close()` (best-effort) right after `_closeInline()`
  so reopening a share form evicts the bug panel too.
- `topology-bugs.js`: `open()` calls `window.TopologyShare.closeDialog()`
  before mounting.
- Both hooks are defensive (`try/catch`), so older builds where one of the
  modules isn't loaded still work.

**Public API unchanged:**

```js
window.TopologyBugs.open(anchorEl);  // "+ Bug" click -> inline panel on Bugs row
window.TopologyBugs.close();         // close active bug panel
```

**Removed (no longer exported or used):**

- `.share-dialog-overlay` / `.share-dialog.bug-topology-dialog` markup in
  `topology-bugs.js` (replaced by `.domain-bug-form` with `.dsf-head`/`.dsf-body`).
- `_positionDialog`, `_cancelPendingClose` (not needed -- no floating dock math,
  no out-animation state).

**Cache busters bumped:** `topology-bugs.js?v=20260420c`,
`topology-share.js?v=20260420c`, `styles.css?v=20260420d`.

**Files touched + synced to `/home/dn/CURSOR/`:** `topology-bugs.js`,
`topology-share.js`, `styles.css`, `index.html`.

## Bug Topology Panel -- Slimmed Layout (simplification pass, 2026-04-20f)

User feedback on the first inline Bug panel: "new bug panel should be
simplified more". The panel still surfaced five row-worth of chrome for a
workflow that is really just "paste SW-ID, press Enter". The simplification
pass removed every element that was not essential to that core path and
collapsed the remaining controls into the input row where possible.

### What was removed

| Element (before) | Why it is gone |
|---|---|
| `<span class="bug-label">Jira ticket</span>` | The `placeholder="SW-243977"` already tells the user what belongs in the input. Redundant label row removed. |
| Dedicated `.bug-jira-status` row with full text ("Checking Jira credentials...", "Jira: email@domain", "Jira not configured", "Jira config unreachable") | Replaced by a compact status chip docked inside the SW input's trailing padding. A colored 8px dot encodes state + `title` attribute carries the full text on hover. |
| `.bug-section-hint` inside `.bug-jira-config` ("Atlassian Cloud only. Token is stored per-user on this server...") | Moved to a `?` help icon tooltip next to the "Jira credentials" title. |
| `.bug-help-link` under the API token input (block-level "Create one in Atlassian ->") | Inlined into the "API token" label as `get one ->`, dimmer styling. |
| `.bug-hint` at the bottom ("Saved into your built-in Bugs domain.") | Merged into the Create button's `title` tooltip -- one less always-visible row. |
| `.share-form-hint` in the footer ("Press Enter to create") | Merged into the Create button's `title` tooltip. |
| `<summary>Manual overrides (skip Jira fetch)</summary>` | Shortened to `<summary>Advanced</summary>`; the "skip Jira" detail moves to the internal "Placeholder only (skip Jira)" checkbox label. |
| `"Create topology"` button label | Shortened to `Create` -- the panel header already says "Create bug topology". |

### New minimal DOM inside `.dsf-body`

```
.bug-section.bug-main
  └── .bug-sw-wrap            (relative; hosts input + chip)
       ├── .bug-sw            (padding-right: 72px for chip room)
       └── .bug-jira-status   (absolute; top/right)
            ├── .bug-jira-state[data-state]   (8px colored dot)
            ├── .bug-jira-setup  (hidden unless state = missing | error)
            └── .bug-jira-edit   (hidden unless state = ready)

.bug-section.bug-jira-config[hidden]
  ├── .bug-section-title "Jira credentials ?"  (? opens tooltip)
  ├── Site URL / Email / API token inputs
  └── .bug-jc-actions                 Cancel | Forget | Save

<details class="bug-advanced"><summary>Advanced</summary> ... </details>

.bug-fetch-status[hidden] | .bug-preview[hidden] | .bug-not-a-bug[hidden]
.bug-error[hidden]

.share-form-footer.bug-form-footer      (justify-content: flex-end)
  └── .bug-create[title="Press Enter..."]  "Create"
```

### JS side changes (`topology-bugs.js`)

- `_setJiraStatus(state, label)` now writes the **short** label into a
  `title` tooltip on the state dot, the setup button, and the edit button.
  The state dot's textContent is empty for `ready`/`missing`/`error`
  (colour encodes everything) and `'...'` only during the initial probe.
  Callers still pass the full sentence ("Jira: you@drivenets.com"),
  so the hover tooltip remains informative -- we just do not print it
  into the panel body as a standalone row.
- `_probeJiraConfig` and `_clearJiraConfig` updated their labels to
  include `-- click Set up` / `-- click Set up to retry` so the tooltip
  tells the user exactly what to do next.
- Submit-failure 401/403 hint renamed from `"Edit credentials"` to `"Edit"`
  to match the new button label.

### CSS side changes (`styles.css`)

- New `.bug-sw-wrap` (`position: relative`) + `.bug-sw-wrap .bug-sw`
  (`padding-right: 72px`) so the chip sits inside the input without
  overlapping text.
- `.bug-jira-status` now `position: absolute; right: 6px; top: 50%;`
  with tight `gap: 4px` and `font-size: 10.5px`.
- `.bug-jira-state` became an 8px colored dot (`font-size: 0` for
  non-`unknown` states; `min-width: 8px; height: 8px; border-radius: 50%`).
  Keeps the existing per-state color rules.
- `.bug-jira-link` font-size tightened to 10.5px; font-weight 600 for the
  "Set up" / "Edit" chip button.
- New `.bug-sec-help` (`?` pill, 14px, help cursor) used next to section
  titles to carry ex-hint paragraphs in a `title` tooltip.
- `.bug-help-link` restyled for inline placement next to the "API token"
  label (9.5px, left margin 6px, no `margin-top` block shift).
- `.domain-bug-form .dsf-body` gap tightened from 10px to 8px.
- New `.domain-bug-form .bug-section.bug-main { gap: 0; }` so the absolute
  chip does not inherit a stray flex-item row worth of whitespace.
- New `.domain-bug-form .share-form-footer.bug-form-footer
  { justify-content: flex-end; padding-top: 6px; margin-top: 0; }` so the
  "Create" button stays right-aligned after the hint text was removed.

### What users see now (per state)

| State | Visible chip contents | Tooltip (hover) |
|---|---|---|
| unknown (probing) | `...` | "Jira credentials state" |
| ready (configured) | green dot + `Edit` | "Jira: you@drivenets.com" |
| missing (no creds) | amber dot + `Set up` | "Jira not configured -- click Set up" |
| error (API unreachable) | red dot + `Set up` | "Jira config unreachable -- click Set up to retry" |

### Regression guard

- `_setJiraStatus` still toggles the exact same `.bug-jira-setup` /
  `.bug-jira-edit` buttons that were wired in `_wireEvents`, so all click
  handlers (`_openJiraConfig`) keep firing.
- The bug-jira-config sub-form HTML is unchanged except for: removed
  `.bug-section-hint` and relocated API-token help link. Every `.bug-jc-*`
  selector still resolves.
- The advanced section still exposes `.bug-title`, `.bug-summary`,
  `.bug-devices`, `.bug-force-placeholder` for `_submit` to read.
- The `.bug-create` button keeps its `.ready` / `.busy` classes and the
  inline spinner replacement in `_submit` -- only the button `innerHTML`
  changed from "Create topology" to "Create".

### Cache busters bumped (2026-04-20f)

`topology-bugs.js?v=20260420f`, `styles.css?v=20260420f`.

**Files touched + synced to `/home/dn/CURSOR/`:** `topology-bugs.js`,
`styles.css`, `index.html`.

## Bug Topology Panel -- "API Token Is Not Saved" False Alarm (2026-04-20g)

User report: "API TOKEN IS NOT SAVED FOR SOME REASON". Reality (verified
against disk): `~/.topology_users/yarel/jira_config.json` existed, was
mode 600, contained a valid 192-char ATATT token. The save had worked
every time. The symptom was a **UX communication failure**, not a data
bug:

1. User opens Create Bug panel -> green `Edit` chip (state=ready).
2. User clicks `Edit` -> credentials sub-form opens, URL + email pre-fill
   from the backend, **but the token input renders empty** because the
   backend deliberately never echoes the secret back (correct security
   design).
3. User stares at the blank token field -> concludes "my token is gone".
4. User retypes the full token into the blank field and hits `Save`.
5. Save succeeds, but the sub-form closes silently -- the only visual
   confirmation is the green `Edit` chip that was *already* green from
   step 1, so the user still cannot tell whether the new value stuck.

### What was changed to kill the confusion permanently

**Backend (`serve.py`):**

- `_handle_jira_config_get` now returns three extra non-sensitive fields
  whenever `configured=True`:
  - `token_hint` -- first 4 chars + `...` + last 4 chars of the saved
    token, e.g. `"ATAT...xPq9"`. Enough to let the user recognise
    *which* token is stored without leaking it.
  - `token_len` -- integer length of the stored token. The UI shows
    "192 chars" so the user can verify the expected token is on disk.
  - `saved_at` -- Unix timestamp of the last successful write. The UI
    renders a short relative age: "just now" / "12m ago" / "3h ago" /
    "2d ago" / ISO date.
- `_handle_jira_config_put` now accepts a PUT with the `api_token` field
  blank (or omitted). When the token is missing, the backend reads the
  existing on-disk config and reuses the stored token so the user can
  edit URL / email without retyping the long ATATT string. If there is
  no prior config AND the caller sent no token, the request still rejects
  with HTTP 400 ("all required").
- PUT now returns the same extended shape as GET (`token_hint`,
  `token_len`, `saved_at`), so the UI can refresh the "Token saved" chip
  in-place without a second roundtrip.

**Frontend (`topology-bugs.js`):**

- New element `.bug-jc-saved` inside `.bug-jira-config`. Hidden by default.
  Rendered by `_renderJiraConfigSavedState(panel, cfg)` whenever the
  server reports `configured=true`. Contains:
  1. A check-mark SVG icon.
  2. "Token saved" label (bold).
  3. `<code>` pill with the masked hint ("ATAT...xPq9").
  4. "192 chars" meta.
  5. Relative age meta ("3h ago").
- `_openJiraConfig` now calls `_renderJiraConfigSavedState` once with
  `null` (reset) immediately and again with the GET payload after it
  lands. This guarantees the chip shape matches the latest server state
  even if the user closes + reopens the form rapidly.
- When `cfg.configured` is true, the token input's `placeholder` switches
  from `"ATATT3x..."` to `"Leave blank to keep current token"` and the
  field gets a `data-keep-existing="1"` dataset flag.
- `_saveJiraConfig`:
  - Validates URL + email as required (unchanged).
  - Only requires the token input to be non-empty when
    `data-keep-existing` is not set, i.e. on the first setup or after a
    Forget. On re-save of existing config, an empty token is allowed.
  - Omits the `api_token` key from the PUT payload when the user left the
    input blank, triggering the backend's keep-existing path.
  - After a successful save, calls `_renderJiraConfigSavedState(panel,
    json)` with the PUT response so the chip reflects the new state
    (timestamp updates to "just now", hint rematches if the user rotated
    the token).
- `_closeJiraConfig` clears the `data-keep-existing` flag so a subsequent
  `Set up` after a `Forget` does not silently reuse the previous token.

**CSS (`styles.css`):**

- New `.bug-jc-saved` rule set: green-tinted background (`rgba(46, 204,
  113, 0.09)`), 1px rounded border, flex row with check icon + label +
  hint code + age meta.
- `.bug-jc-saved-hint` uses a monospace stack with a dark translucent
  background so the masked token pill reads as a terminal-style artifact,
  distinct from the surrounding form inputs.
- Light-mode parity rules (`body:not(.dark-mode) .bug-jc-saved`) so the
  chip stays legible in the light theme.

### Why this fixes the report for good

- The chip answers the "is it saved?" question **before** the user
  inspects any form field, so no one looks at the empty password input
  and jumps to the wrong conclusion again.
- The masked hint gives the user a stable identifier for the stored
  token. If they rotate it in Jira and re-save here, the hint changes,
  giving them positive confirmation that the new value stuck.
- The "Leave blank to keep current token" placeholder removes the
  ambiguity of the password input. A blank field now *means something*:
  "keep what you have". A typed field still means "replace".
- The backend is strict: the keep-existing path only triggers when a
  token is already on disk. A brand-new config without a token still
  fails loudly with 400 instead of silently creating a half-valid entry.

### Regression guard

- `_jira_config_read` still returns `None` when any required field is
  missing, so the GET path continues to report `configured=false` for
  legacy half-written files.
- The existing "Forget" button still deletes the whole config; afterward
  the saved chip hides and the token input goes back to the
  `"ATATT3x..."` placeholder.
- `_setJiraStatus('ready'|'missing'|'error')` and the dot-colour CSS are
  untouched; the new chip is additive and sits inside the sub-form only.
- The backend smoke test against `/rest/api/3/myself` still runs unless
  the caller explicitly sends `skip_validate: true` (only the smoke
  tests do that). Saving with an invalid token still returns 401 and the
  file on disk is not overwritten.
- Verified via smoke test on `smoketest_1776704325`:
  - PUT with `api_token` -> full extended payload returned.
  - PUT without `api_token` after prior save -> 200, email updated, hint
    unchanged, file on disk untouched in the token byte.
  - PUT with `api_token: ""` after prior save -> same as above.
  - PUT without prior config + no token -> correctly 400.

### Cache busters bumped (2026-04-20g)

`topology-bugs.js?v=20260420g`, `styles.css?v=20260420g`.

**Files touched + synced:** `topology/topology-bugs.js`,
`topology/styles.css`, `topology/index.html`, `topology/serve.py` ->
`/home/dn/CURSOR/`. `serve.py` change required a
`systemctl --user restart topology-app` (no hot reload).

## Bug panel + `+ Bug` button -- refined + responsive (2026-04-20h)

User request: "refine and enhance all and the bug+ button to be
responsive". The Create-Bug-Topology pill on the Bugs domain row was
previously styled with dozens of inline `style="..."` attributes
generated at render time, which made it impossible to adapt to narrow
Topologies dropdowns or to add proper keyboard focus / active-panel
visuals. The inline panel body had only a single viewport media query.

### JS side changes (`topology-file-ops.js`, `topology-bugs.js`)

**`topology-file-ops.js` -- newBugBtn rendering:**

- Removed all layout-related inline CSS from the `<button>` markup.
  Only the dynamic accent colour is threaded through as four CSS custom
  properties: `--bug-accent`, `--bug-accent-bg`,
  `--bug-accent-bg-hover`, `--bug-accent-border`,
  `--bug-accent-border-hover`. Everything else (padding, font, radius,
  transition curve, pressed state, focus ring, container-query
  collapse) now lives in `styles.css .domain-newbug-btn`.
- Dropped the JS-wired `mouseenter`/`mouseleave` handlers; CSS `:hover`
  drives the colour shift from the same custom properties the base
  state reads, so the hover/active transitions are consistent with
  focus-visible and panel-active states.
- The `+` icon is rendered as `.domain-newbug-icon` and the "Bug"
  label as `.domain-newbug-label` so the container query can collapse
  the label in a single rule instead of duplicating padding overrides.

**`topology-bugs.js` -- active-panel visual:**

- `open(anchorEl)` now calls `_setNewBugBtnActive(row, true)` after
  mounting the panel. The helper adds `.active` to the `+ Bug` pill
  in the Bugs row, which the CSS uses to tint the background, draw an
  inset ring, and rotate the `+` icon to `x` (telegraphing that clicking
  again will close the panel).
- `closeDialog()` walks back up to the Bugs row and clears `.active`
  BEFORE the fade-out timer removes the host, so the toggle state is
  always in sync with the panel lifetime.
- `_saveJiraConfig()` now triggers a one-shot `.pulse` class on the
  `.bug-jc-saved` chip immediately after the backend confirms the
  write, then delays `_closeJiraConfig()` by 560ms so the pulse has
  screen-time before the sub-form collapses. This answers the
  "did my token actually save?" question visually on every save.

### CSS side changes (`styles.css`)

**Button -- `.domain-newbug-btn`:**

- Full class-based styling using the `--bug-accent-*` custom properties
  set by the JS. Hover, active (pressed), focus-visible, and `.active`
  (panel-open) are all covered and theme-agnostic.
- `:focus-visible` renders a 4px accent outline so keyboard users get
  clear feedback; `:hover`/`:active` stay subtle for mouse users.
- `.active` toggle rotates the `+` icon 45deg and tints the background
  so the pill reads as a pressed-down toggle while the panel is open.

**Responsive layout:**

- `.custom-section-category { container-type: inline-size; container-name: domain-row; }`
  turns every domain row into a CSS container. This lets the Bugs row
  adapt to its real width, not the viewport's -- so narrow Topologies
  dropdowns collapse the `+ Bug` pill to icon-only and tighten the
  inline panel without affecting any other domain.
- `@container domain-row (max-width: 260px)` collapses the pill label
  to icon-only. The 260px threshold keeps the default 300px-wide
  Topologies dropdown rendering the full "Bug" label, and only
  collapses on narrower configurations.
- `@container domain-row (max-width: 280px)` tightens the inline bug
  panel: narrower margins, wrapping `.bug-jc-actions`, stacked
  `.bug-preview-line` key/value pairs, and reduced chip padding.
- `@media (max-width: 420px)` further shrinks the Jira status chip to
  icon-only (Set up / Edit become symbol glyphs) and trims the input
  padding-right from 72px -> 44px.
- `@media (max-width: 768px)` now also stretches the Create button
  full-width inside the footer and widens the panel's `max-height` to
  70vh for long preview states.

**Micro-interactions:**

- `.bug-section.bug-jira-config`, `.bug-preview:not([hidden])`,
  `.bug-fetch-status:not([hidden])`, `.bug-not-a-bug:not([hidden])`,
  and `.bug-jc-saved:not([hidden])` share a `bugSectionFadeIn` 200ms
  ease-out so state changes glide in instead of jumping.
- `.bug-jc-saved.pulse` runs a 900ms green-ring pulse once, triggered
  by JS after a successful save.
- `.bug-jira-state[data-state="missing"]` and `[data-state="error"]`
  run a gentle 1.6s box-shadow pulse so the Set up / Retry affordance
  catches the user's eye without becoming visual noise.

**Focus rings (bug panel scope only):**

- `.domain-bug-form .share-btn-primary:focus-visible`,
  `.share-btn-secondary:focus-visible`, `.dsf-close:focus-visible`,
  `.bug-jira-link:focus-visible`, and the two themed Jira-config
  variants (`bug-jira-config ...:focus-visible`) all get 3px shadow
  rings coloured to match their surrounding accent.
- `.bug-input:focus` now also draws a 3px soft shadow (red for the
  main panel, blue for the Jira-config sub-form) so the focused field
  is unambiguous on both themes.
- `.bug-input:hover:not(:focus)` adds a faint border lift so the
  hover target area is discoverable without stealing the focus
  treatment.

**Accessibility:**

- All new animations (bugSectionFadeIn, bugSavedPulse, bugDotAttention,
  bugDotAttentionError, the `+ Bug` icon rotation, and the reusable
  bugSpin spinner) are disabled under `@media (prefers-reduced-motion: reduce)`.

### Files touched + synced (2026-04-20h)

`topology/topology-file-ops.js`, `topology/topology-bugs.js`,
`topology/styles.css`, `topology/index.html` -> `/home/dn/CURSOR/`.
Cache busters: `topology-bugs.js?v=20260420h`, `styles.css?v=20260420h`,
`topology-file-ops.js?v=20260420j`. No backend / Python changes, so
no `systemctl restart topology-app` required; browser hard-refresh is
sufficient.

## Stale-save 409 banner -- refined + responsive (2026-04-20i)

User report: browser devtools was logging
`POST /api/sections/<sid>/save 409 (Conflict)` even though the
stale-save banner ("Someone else edited this topology") was correctly
appearing. The 409 itself is legitimate (the backend's mtime-vs-mirror
guard fired because a peer or another tab of ours wrote newer data),
but two things needed attention: (a) the banner was the last bit of
chrome still built with giant inline-style strings, so it didn't match
the refined UI conventions we just rolled out for the bug panel, and
(b) the console was silent on our side, leaving the browser's red 409
line with no developer context.

### JS changes (`topology-file-ops.js`)

- `_sectionSaveWithConflict` now logs a `console.info(...)` with the
  section id and `current_updated_at` when it catches the 409. This
  pairs the unavoidable browser HTTP-status log with a friendly
  explanation: "showing reload/overwrite banner. Not an error.".
- `_showStaleSaveBanner` was fully rewritten:
  - All inline `style="..."` strings replaced with semantic classes
    (`.topology-stale-save-banner`, `.ssb-icon`, `.ssb-body`,
    `.ssb-title`, `.ssb-age`, `.ssb-msg`, `.ssb-actions`, `.ssb-btn`,
    `.ssb-btn-primary/secondary`, `.ssb-close`). The JS now only builds
    the DOM structure and wires event handlers.
  - `role="alertdialog"`, `aria-live="assertive"`, and
    `aria-labelledby="topology-stale-save-title"` for screen readers.
  - Button titles spell out the consequence ("Discard local edits and
    reload the latest version" / "Overwrite the server copy with your
    local edits") so the ambiguous "Reload" / "Save anyway" pair
    can't be misread.
  - Single teardown helper runs the dismiss animation (`.dismissing`)
    before removing the node, guarded against double-invocation from
    competing action paths.
  - `document.addEventListener('keydown', onEsc, true)` so Escape
    dismisses the banner without firing Reload or Force. The listener
    is removed in the teardown path.
  - `reloadBtn.focus()` on insert so keyboard users can act immediately
    with Enter on the safer option; Tab cycles to Save-anyway.

### CSS changes (`styles.css`)

- `.topology-stale-save-banner` owns all the geometry, colour, shadow,
  and motion. Theme is automatic via `body:not(.dark-mode) ...`.
  Backdrop blur + saturate matches the liquid-glass dropdowns used
  elsewhere in the shell.
- `@keyframes staleSaveSlideIn` / `staleSaveSlideOut` drive the
  entry/exit on wide viewports (anchored via `translateX(-50%)`).
  `staleSaveSlideInNarrow` / `staleSaveSlideOutNarrow` are declared at
  top-level and activated inside `@media (max-width: 640px)` where the
  banner switches to `left: 12px; right: 12px; transform: none` so the
  keyframes can't step on each other.
- `@media (max-width: 640px)` wraps the actions below the body text,
  stretches each `.ssb-btn` to `flex: 1 1 auto`, and reorders the icon
  to the top of the stack. `padding-right` still reserves space for the
  absolute close button so it never overlaps Save-anyway.
- Full set of `:focus-visible` rings (secondary, primary, close) tuned
  to the red accent. Primary button lifts `translateY(-1px)` on hover
  and presses back on `:active`; identical rhythm to `.share-btn-primary`.
- `prefers-reduced-motion: reduce` disables the slide animations and
  pins the banner at `opacity: 1`. A second scoped block restores
  `transform: translateY(0)` on narrow viewports so the reduced-motion
  !important doesn't re-introduce `translateX(-50%)` there.

### Why the 409 fires in the first place

The backend stale-save guard lives at
`/api/sections/<sid>/save`: if the file has a multi-user mirror row
AND the DB `updated_at` is more than 5 seconds newer than the on-disk
mtime, it returns `409 {conflict: true, current_updated_at: ISO}`.
The mirror is updated by any write path (owner's legacy save OR a
share recipient's `/api/domains/.../topologies` PUT), but ONLY the
legacy save path touches disk. So the 409 is the correct response
when someone else wrote after our last local save, or when we loaded
from the mirror without touching disk and then tried to save.

The 5s tolerance absorbs the normal mirror-save-lag race (our own
previous save updates the DB a few hundred ms after the disk write).
If 409s start appearing without a legitimate peer edit, suspect clock
drift between the Python host and the filesystem (unlikely on one box)
or a deployment where disk writes are delayed by more than 5s.

### Files touched + synced (2026-04-20i)

`topology/topology-file-ops.js`, `topology/styles.css`,
`topology/index.html` -> `/home/dn/CURSOR/`. Cache busters:
`styles.css?v=20260420i`, `topology-file-ops.js?v=20260420k`. No
backend changes; browser hard-refresh is sufficient.

## New Topology picker -- "+ New domain" shortcut (2026-04-21a)

User pain point (screenshot): the "New Topology" domain picker listed
existing domains + a "No domain" / "Cancel" footer, with no way to
create a new domain from there. If the only domain was "Bugs" and the
user wanted a different one, they had to cancel, open the Topologies
dropdown, click Manage Topology Domains, create the domain, then
re-open the New Topology flow. Four clicks + context-switching for
what should be inline.

### Change (`_showNewTopologyDomainPicker` in `topology-file-ops.js`)

- Added a dashed, indigo-accented "+ New domain..." action rendered
  BELOW the domain list and ABOVE the footer buttons. Clicking it:
  1. Dismisses the picker overlay.
  2. Calls `editor.showManageSections()` -- the same entry point used
     by the "Manage Topology Domains" item in the Topologies dropdown.
  3. Falls back to clicking `#btn-topologies` and showing a toast if
     the method is ever unavailable (defensive).
- Indigo `#6366f1` matches the "Manage Topology Domains" header in
  `index.html` so the visual language connects the two surfaces.
- Dashed border (instead of solid) distinguishes this button from the
  list of existing domains: it's a creation affordance, not a pick.
  Chevron on the right hints at the hand-off to the management panel.
- The empty-list early-return was replaced: if the user has no domains
  yet, the picker still opens with the subtitle "You have no domains
  yet. Create one to continue." and the "+ New domain" button front
  and centre. Previously a dismissive toast dead-ended the flow.
- Hover state shifts the background + border colour by one tier and
  nudges the button `translateX(1px)` so the chevron leads the eye
  toward the next surface.
- `title="Open Topology Domain management to create a new domain"` so
  hovering clarifies that this opens a secondary panel rather than
  creating a domain inline.

### Auto-refresh wire-up (2026-04-21b)

Instead of making the user re-open the picker after creating a
domain, the picker now stays alive behind the Manage Topology Domains
panel and re-renders its list in place the moment the domain list
changes. Mechanics:

- All three CRUD paths in `showManageSections` (create, update,
  delete) now dispatch a `CustomEvent('topology-domains:changed')`
  with `detail = { reason, domainId, domainName }`. The create
  path is the critical one for this flow, but the update + delete
  paths also fire so other surfaces (dropdown badges, share dialog)
  stay in sync without bespoke hooks.
- `_showNewTopologyDomainPicker` now extracts its list render into
  a local `renderDomainList(highlightIds)` function. On open, the
  picker registers a document-level listener for
  `topology-domains:changed`; that listener diffs the ids it knew
  about against `editor._customSections`, builds the set of newly
  appeared ids, and calls `renderDomainList(appeared)`.
- Newly appeared (or explicitly-updated) rows get a ~0.9 s ring
  pulse -- `box-shadow: 0 0 0 2px <color>, 0 6px 18px <color>60`
  fading to zero -- so the user sees *which* row just landed
  instead of hunting for it alphabetically.
- Clicking "+ New domain..." no longer destroys the picker. It
  hides the overlay (`display: none`) and mounts the manage panel.
  A `MutationObserver` on `document.body` watches for the manage
  panel to be removed; when it is, the picker re-appears with the
  refreshed list already rendered.
- Escape is ignored while the picker is hidden so the manage panel
  can eat the keystroke (otherwise we'd silently close the picker
  the user can't see).
- All listeners (Escape, `topology-domains:changed`, overlay click)
  are detached by a single `closeOverlay()` path so the picker has
  no zombie listeners after the user cancels or picks a domain.

### Shared-in icon redesign + richer owner tooltip (2026-04-21b)

User feedback: the badge on "shared with me" topologies looked like
a Dropbox / inbox-download icon (a tray with an arrow pointing into
it). People didn't recognise it as a share affordance, and the
tooltip that *does* carry the owner name wasn't getting hovered.

- `_sharedInIconHtml` in `topology-file-ops.js` now renders the
  universal 3-circle share glyph (same shape as the outgoing
  `_sharedOutIconHtml`) -- but with the left node FILLED to read
  as "someone else is the sender" and the two outlined nodes on
  the right as "recipients (you)". Tinted purple
  (`SHARED_IN_ACCENT`) to stay visually distinct from the outgoing
  green-accented variant at a glance.
- Tooltip attribution is richer. When the shared-in row has both
  a display name AND a distinct username / email, the hover now
  reads `Shared by Alice Smith (alice@example.com, write)`. When
  only one is available we fall back to `Shared by alice (write)`.
  This works on BOTH surfaces that render the icon: file rows
  (`topo-shared-badge`) and shared-in domain headers
  (`.domain-title .dd-shared-in`). Both paths share the same
  `_attachHoverTip` rich bubble plumbing -- no 1.5 s native-title
  delay.
- The icon change is a drop-in: callers still pass `(color, tooltip)`
  and `_sharedInIconHtml` still emits `<title>` + `aria-label` for
  accessibility. `_attachHoverTip` continues to promote the
  wrapper's `title` attribute to the custom bubble.

### Files touched + synced (2026-04-21b)

`topology/topology-file-ops.js`, `topology/index.html` ->
`/home/dn/CURSOR/`. Cache buster: `topology-file-ops.js?v=20260421b`.
No backend / CSS changes; browser hard-refresh is sufficient.

## Active-topology bar: compact domain pill + hover-marquee long names (2026-04-21c)

User feedback: the bottom-left active-topology pill truncated long
names with an ellipsis ("BUG_FLOWSPEC_REDIRECT_IP_UNRE...") which
hid the meaningful tail (the bug ID suffix). The "Shared with me"
domain pill also read slightly too heavy next to the name.

### Changes (`topology/index.html` styles + `_showNewTopologyDomainPicker`
is unrelated; this edits `updateTopologyIndicator`)

- **Domain pill shrunk.** `#topo-active-domain` now uses `font-size:
  10.5px` (was 12px), `padding: 1px 7px` (was `2px 8px`),
  `border-radius: 5px` (was 6px), `max-width: 150px` (was 180px),
  `letter-spacing: 0.25px`. Visually a tier smaller than the name,
  matching the "secondary metadata" role it plays.
- **Name is now hover-scrollable instead of ellipsised.** Wrapped
  `#topo-active-name` in a new `#topo-active-name-wrap` container
  that:
  - Caps width at 280 px and clips overflow.
  - Applies a right-edge mask fade (`mask-image: linear-gradient(to
    right, #000 calc(100% - 16px), transparent)`) as the new
    "there's more" affordance (replaces the `text-overflow:
    ellipsis`). When the name fits, JS adds a `.no-fade` class to
    kill the gradient so short names render crisply.
  - On hover, if and only if the text overflows, a CSS keyframe
    (`@keyframes topo-active-marquee`) translates the name left
    across ~76% of the cycle with small pauses at each end (0-12%
    and 88-100% hold, 12-88% scrolls) so the reader can actually
    read the start and the end before the loop restarts.
- **Distance + speed measured in JS.** After writing the name,
  `updateTopologyIndicator` runs a `requestAnimationFrame` callback
  that reads `scrollWidth - clientWidth`. If positive, it sets two
  CSS variables on the wrapper:
  - `--marquee-shift` = `-(overflow + 24 px)` so the last letter
    clears the right edge before the loop restarts.
  - `--marquee-duration` = `max(4s, shift / 60)` -- constant-speed
    ~60 px/sec so a 400 px overflow gets ~6.7 s and a 60 px
    overflow gets the 4 s floor (prevents jittery snapping on
    near-fitting names).
  It also toggles `.overflowing` on the wrapper so the hover rule
  only mounts the animation when there's something to reveal.
- **Reduced-motion respected.** `@media (prefers-reduced-motion:
  reduce)` disables the marquee; the full name still surfaces via
  the wrapper's `title` attribute (added in `applyContent`), which
  also works as a fallback for users who want to read without
  hovering the full duration.
- **Gentle snap-back.** `transition: transform 0.35s ease-out` on
  the inner name means when the user hovers away mid-scroll, the
  text eases back to position 0 instead of snapping.

### Files touched + synced (2026-04-21c)

`topology/topology-file-ops.js`, `topology/index.html` ->
`/home/dn/CURSOR/`. Cache buster: `topology-file-ops.js?v=20260421c`.
No backend changes; browser hard-refresh is sufficient.

## Top-bar "My Topologies" share pill removed (2026-04-21d)

User flagged the top-bar `[folder] My Topologies [N] [share-icon]`
pill as dead weight: it did nothing the Topologies dropdown didn't
already cover (every row has its own share icon + per-domain share
form, and the dropdown itself is the single source of truth for
domain management). The pill's whole surface opened
`TopologyShare.open(anchorEl)` -- a duplicate entry point to an
affordance that already ships inline on every shareable row.

### Change (`_renderToolbar` in `topology/topology-share.js`)

- `_renderToolbar()` is now a no-op: it hides + empties the
  `#auth-share-toolbar` container and returns, regardless of auth
  state. No HTML is produced, no listeners are wired.
- The function is kept (not deleted) because `DOMContentLoaded` and
  `topology-domains:changed` both call it; removing it would force
  edits in two event listeners for zero behavioural win.
- `TopologyShare.open(anchorEl)` is UNTOUCHED -- per-topology share
  buttons in the Topologies dropdown still call it via
  `topology-file-ops.js` (lines ~1616, 1684, 3138). The pill was
  just one of several entry points; removing it doesn't affect the
  others.
- The `#auth-share-toolbar` div + its styles (`styles.css` /
  `.topology-domain-pill`) are left in place as cold-code in case
  the pill is ever revived. Zero runtime cost since the container
  is `display:none`.

### Files touched + synced (2026-04-21d)

`topology/topology-share.js`, `topology/index.html` ->
`/home/dn/CURSOR/`. Cache buster: `topology-share.js?v=20260421d`.
No backend / CSS changes; browser hard-refresh is sufficient.

## Share popover: badges update immediately on close (2026-04-21j-b)

### Symptom (user report)

"After sharing a topology it does not visually reflect or add the
shared/stop sharing icons immediately, only after a refresh." Users
had to press F5 to see the purple outgoing-share badge + "Stop
sharing with everyone" icon appear on a row they had just shared.

### Root cause

The existing architecture already had the right infrastructure --
`TopologyDomains.fetchDomains()` dispatches `topology-domains:changed`
at the end of `_refreshAll()`, and the global listener in
`topology-file-ops.js` (line ~4749) rebuilds the dropdown in
response. But there's a guard that **skips** the rebuild while a
share inline form is mounted:

```js
if (document.querySelector(
    '#topologies-dropdown-menu .topo-share-form.open, ' +
    '#topologies-dropdown-menu .domain-share-form.open'
)) {
    return;  // don't tear out the live popover
}
```

The guard exists for a good reason: the popover lives inside the
dropdown DOM, so a rebuild while it's open would rip it out mid-
typing. The old code-comment promised "the popover will trigger its
own refresh via _refreshAll on close" -- but `_closeInline()` in
`topology-share.js` never actually triggered one. The end result:

1. User clicks Share on a row, picks a recipient, clicks confirm.
2. POST succeeds. `_refreshAll()` fetches fresh domains and fires
   `topology-domains:changed`.
3. Global listener sees the open form and returns (correct).
4. `_renderBody()` re-renders the popover's internal recipient list
   (so the user sees success INSIDE the popover).
5. User closes the popover.
6. **No rebuild is triggered.** Every row outside the popover still
   renders with the stale sharing state cached at open time.
7. Only a hard refresh (F5) fixes it.

### Fix (frontend only)

`topology/topology-share.js`:

1. New module-level `_inlineDirty` flag. Starts false on each popover
   open.
2. All six mutation handlers set it to true on success:
   - `_onSubmitShareClick`    (domain-level share)
   - `_onRevokeClick`         (domain-level revoke one user)
   - `_onPermChangeClick`     (domain-level read <-> write toggle)
   - `_onTopoSubmitShareClick` (per-file share)
   - `_onTopoRevokeClick`     (per-file revoke one user)
   - `_onTopoPermChangeClick` (per-file read <-> write toggle)
3. `_closeInline()` checks the flag. If dirty, it dispatches a fresh
   `topology-domains:changed` event after the popover is removed from
   the DOM. The global listener's guard is now clear, so it rebuilds
   the dropdown using the cache that was already primed by
   `_refreshAll()` during the mutation.

### Why this is the minimal fix

Alternative approaches considered and rejected:

- **Rebuild while popover is open**: would require preserving the
  popover's DOM through the rebuild (it's mounted under a row that
  gets replaced). Complex and fragile.
- **Selective badge-only update**: would require a new code path that
  only updates `.topo-shared-badge` / action-button visibility without
  rebuilding rows. Duplicate rendering logic, high drift risk.
- **Remove the guard in the listener**: would rip the popover out
  mid-interaction. User experience regression.

The flag-on-close approach reuses the existing rebuild pipeline,
honors the existing guard, and introduces one deterministic trigger
exactly when the DOM is safe to rebuild.

### Files touched + synced (2026-04-21j-b)

- `topology/topology-share.js` -> `/home/dn/CURSOR/topology-share.js`
- `topology/index.html` -> `/home/dn/CURSOR/index.html`
  (cache buster: `topology-share.js?v=20260421j`)

### Verification

Manual test flow (once user hard-refreshes to pick up the new JS):

1. Open topologies dropdown, pick any topology the user owns.
2. Click the Share icon on the row. Popover opens.
3. Pick a user, click "Share file".
4. **Popover internal state updates** (recipient chip appears).
5. Close popover via `×`.
6. **Expected now**: the row immediately shows the purple outgoing-
   share badge on the left + the crossed-out "Stop sharing with
   everyone" icon on the right, without F5.

No server-side changes required for this fix.

## Active-topology pill: swap domain and name positions (2026-04-21l)

### Symptom (user request)

"Switch domain with current topology name locations." The bottom-left
active-topology pill previously rendered as
`[save] [name] | [domain pill] [dots]`
(e.g. `Test | Bugs`), but the user wanted the domain pill to lead and
the name to follow:
`[save] [domain pill] | [name] [dots]` (e.g. `Bugs | Test`).

### Root cause

Pure DOM ordering in `topology/index.html`. The children of
`#topo-active-inner` were declared in "name -> separator -> domain"
order. No CSS or JS assumes a specific order (every element is
accessed by id, not by sibling position, and `updateTopologyIndicator`
only toggles each id's `display`/`textContent`).

### Fix (frontend only, DOM reorder)

Swapped two siblings inside `#topo-active-inner`:

```html
<!-- was -->
<span id="topo-active-name-wrap">...</span>
<span id="topo-active-sep">|</span>
<span id="topo-active-domain"></span>

<!-- now -->
<span id="topo-active-domain"></span>
<span id="topo-active-sep">|</span>
<span id="topo-active-name-wrap">...</span>
```

The separator sits between them in both orders. Its "hide when no
domain" branch in `updateTopologyIndicator` still zeros both the sep
and the domain pill, so a topology without a domain still reads as
`[save] [name] [dots]` -- identical to the old behavior.

### Side effects verified (all benign)

- The name wrap's right-edge fade mask still signals "more text",
  because overflow still spills to the right regardless of the name's
  horizontal position in the flex row.
- The dots container has `margin-left: 4px` and still sits to the
  right of the name wrap -- unchanged in the new order.
- The color dot and save button stay at the left of the pill.
- `updateTopologyIndicator`, `clearTopologyIndicator`, and
  `restoreTopologyIndicator` all use `getElementById` for every child,
  so reordering is invisible to them.
- No JS traversal (e.g. `nextSibling`, `children[i]`) references the
  old order.

### Files touched + synced (2026-04-21l)

- `topology/index.html` -> `/home/dn/CURSOR/index.html`

No CSS / JS / backend changes. No cache-buster bumps needed (the
change is inline HTML; next page load picks it up).

## Topologies dropdown: adapts to longest topology name (2026-04-21k + 2026-04-21m)

### Symptom (user report)

"It seems that the panel doesn't expand according to the longest
topology name opened ..." Followed by a stronger restatement: "The
longest topology file name should affect the length of the whole
topologies panel ... in order to see full names." Long topology
filenames were rendered with ellipsis truncation
(`DriveNets_T...`, `RR-SA-2_dn...`, `BUG_...`) even though there was
plenty of unused horizontal space to the right of the dropdown.

### Root causes (two, fixed in sequence)

**Root cause #1 (fixed in 2026-04-21k):** the dropdown was pinned at
`min-width: 300px` inline on `#topologies-dropdown-menu`. Even when
the browser computed a larger intrinsic content, the explicit width
constraint kept the dropdown at 300px.

**Root cause #2 (fixed in 2026-04-21m):** even after adding
`width: max-content`, the dropdown STILL didn't widen. The
`.topo-entry-name` span was rendered with `flex:1` (CSS shorthand for
`flex: 1 1 0%`). The `flex-basis: 0%` part means the name's INTRINSIC
size is treated as 0 when the browser calculates the flex row's
max-content. So the row's max-content reported as
`icon + badge + time + actions + padding` (~260px) -- the full text
width of the filename contributed NOTHING. `width: max-content` on
the parent dropdown was seeing the wrong intrinsic width and staying
at ~300px.

### Fix part 1 -- Dropdown growth bounds (`topology/index.html`)

```html
<div id="topologies-dropdown-menu" ... style="...
    min-width: 300px;
    width: max-content;
    max-width: min(720px, calc(100vw - 40px));">
```

- `min-width: 300px` -- unchanged floor so domains with only short
  names still render at a stable width and the
  `@container domain-row (max-width: 260px)` Bugs-pill collapse rule
  still behaves as before.
- `width: max-content` -- browser sizes the dropdown to its widest
  intrinsic row.
- `max-width: min(720px, calc(100vw - 40px))` -- caps the growth so
  the dropdown never takes over the screen AND never spills past the
  viewport's right edge. The original cap was 560px (2026-04-21k) but
  real bug names in the wild reach ~40-50 chars
  (`BUG_FLOWSPEC_LOCAL_POLICY_RESOURCE_LEAK`) which needed ~580-640px
  of total dropdown width. 720px fits those cleanly while still
  keeping a reasonable ceiling for outlier 100+ char names (e.g. the
  SW-227884 PWHE bug) which fall back to ellipsis.

### Fix part 2 -- Name span contributes intrinsic width (`topology-file-ops.js`)

```js
// before:
<span class="topo-entry-name" style="flex:1;overflow:hidden;...">

// after:
<span class="topo-entry-name" style="flex:1 1 auto;min-width:0;overflow:hidden;...">
```

Why both properties are required:

- `flex: 1 1 auto` -- `flex-basis: auto` resolves to the item's
  intrinsic content size (the full filename text width, since
  `white-space: nowrap` keeps it on one line). This is what `width:
  max-content` on the ancestor dropdown reads to calculate the row's
  max-content width.
- `min-width: 0` -- by default, flex items have `min-width: auto`
  which equals intrinsic content size. Without overriding it, the
  item refuses to shrink below the full text width, which would
  break the ellipsis fallback when the dropdown hits its max-width
  cap. Setting `min-width: 0` lets the span shrink-to-zero when
  constrained, so ellipsis kicks in for the rare pathological name.

The combination says:
- "Start at intrinsic width (for max-content calculation upstream)."
- "Grow/shrink freely in the flex row (for normal layout)."
- "Allow shrinking below intrinsic when forced (for ellipsis)."

### Why the `flex:1` vs `flex:1 1 auto` distinction mattered

`flex: 1` is a shorthand that expands differently than most people
expect. Per spec:

| Shorthand    | grow | shrink | basis  | max-content contribution |
|--------------|------|--------|--------|--------------------------|
| `flex: 1`    | 1    | 1      | `0%`   | **zero** (basis is 0)    |
| `flex: 1 1 auto` | 1 | 1   | `auto` | intrinsic content width  |
| `flex: auto` | 1    | 1      | `auto` | intrinsic content width  |

For layouts where the flex item should fill available space AND
contribute to the container's intrinsic size, use `flex: 1 1 auto`
(or the equivalent `flex: auto`), not `flex: 1`. The latter is for
"pure slot"-style layouts where you actively WANT the item's content
to not affect parent sizing.

**Root cause #3 (fixed in 2026-04-21n):** even after fix #2, the
dropdown still only grew a little. Two layered CSS scroll containers
sabotage `width: max-content` propagation all the way up:

1. `.liquid-glass-dropdown { overflow: hidden; ... }` in
   `topology/index.html` (line 87) creates a scroll container on
   BOTH axes (the shorthand `overflow: hidden` sets `overflow-x` AND
   `overflow-y` to `hidden`). Inline `overflow-y: auto` overrides
   the Y component but leaves `overflow-x: hidden` intact.
2. `.domain-topos-list { overflow-y: auto; ... }` creates its own
   scroll container, and per CSS spec, when one overflow axis is
   not `visible`, the other is coerced to a non-`visible` value at
   the used-value stage, so this is a two-axis scroll container too.

Per CSS spec on flex container intrinsic sizes: scroll containers
MUST be at least as wide as their content, but browsers in practice
clamp max-content propagation through them. The dropdown's
`width: max-content` was seeing only the un-clipped chrome widths,
not the filename span's true intrinsic text width, so the dropdown
settled at a wrong (too-small) value.

### Fix part 3 -- JS-measured explicit width (`topology-file-ops.js`, `topology.js`)

Instead of fighting CSS scroll containers, measure the actual
content after render and assign `dropdown.style.width` directly:

```js
// New helper in FileOps, called after every row render and on
// domain collapse/expand. scrollWidth returns the FULL intrinsic
// text width of a span even when overflow:hidden is set, which
// is exactly what we need for the filename.
_fitDropdownToContent() {
    const dropdown = document.getElementById('topologies-dropdown-menu');
    if (!dropdown || dropdown.style.display === 'none') return;
    let widestRow = 0;
    dropdown.querySelectorAll('.domain-topo-row').forEach(row => {
        if (row.offsetParent === null) return; // collapsed domain
        let total = 0;
        for (const child of row.children) {
            const cs = getComputedStyle(child);
            const ml = parseFloat(cs.marginLeft) || 0;
            const mr = parseFloat(cs.marginRight) || 0;
            total += Math.max(child.scrollWidth, child.offsetWidth) + ml + mr;
        }
        // + row padding + row margin
        if (total > widestRow) widestRow = total;
    });
    const target = Math.max(300, Math.min(
        widestRow + 8,
        Math.min(720, window.innerWidth - 40)
    ));
    dropdown.style.width = target + 'px';
}
```

Call sites:

- After `container.innerHTML = html` in `_renderTopoEntries` (the
  row-render path). Wrapped in `requestAnimationFrame` so measurement
  runs on fully-painted DOM.
- After every domain collapse/expand (all three toggle sites:
  built-in domain handler, custom domain drag/click handler, and
  shared-in domain handler).
- After dropdown first opens in `topology.js`, so remembered-open
  domains get sized correctly on reopen.

Why this works where pure CSS failed: `scrollWidth` bypasses the
scroll-container clamp. It reads the un-clipped layout width of the
filename span even though `.topo-entry-name` has `overflow: hidden;
text-overflow: ellipsis`. Summing per-row and writing to
`dropdown.style.width` replaces the browser's unreliable
max-content computation with a deterministic measurement.

Ellipsis fallback still works: when a filename is so long that
`widestRow + chrome > 720`, we cap at 720 and the name span (with
`flex: 1 1 auto; min-width: 0`) shrinks below intrinsic, engaging
`text-overflow: ellipsis`.

### Alternatives considered and rejected

- **Just bump `min-width` to 420/480px**: doesn't adapt -- still
  truncates 40+ character bug names, and wastes horizontal space
  when all names in the visible domains are short.
- **Strip `overflow:hidden; text-overflow:ellipsis` from the name
  span**: would cause rows to overflow horizontally for outlier
  100+ char names (SW-227884 PWHE bug), breaking the dropdown's
  clean column layout.
- **Set `width: 720px` flat**: removes adaptive behavior and looks
  visually heavy for small domains that have one short entry.
- **Remove `overflow: hidden` from `.liquid-glass-dropdown`**: the
  rule is shared with every dropdown (Create New, Export, Manage
  Topology Domains, etc.). Removing it would allow those dropdowns
  to render transparent corners past their rounded 12px border
  radius on non-blink engines. Not worth the cross-dropdown
  regression risk to fix a single-dropdown width issue.
- **Use a ResizeObserver instead of hooks on toggle/render**: the
  observer would fire on scroll-induced layout shifts too, causing
  needless re-measurements. Explicit hooks on the three mutation
  points are deterministic and cheap.

### Files touched + synced (combined 2026-04-21k + 2026-04-21m + 2026-04-21n)

- `topology/index.html` -> `/home/dn/CURSOR/index.html`
  - Dropdown inline style: `min-width: 300px; max-width: min(720px, calc(100vw - 40px))`
    (the `width: max-content` hint was removed in 2026-04-21n because
    JS now sets `width` explicitly; leaving `max-content` alongside
    was redundant and slightly confusing to read).
  - Cache-busters bumped: `topology-file-ops.js?v=20260421n`,
    `topology.js?v=20260421b`.
- `topology/topology-file-ops.js` -> `/home/dn/CURSOR/topology-file-ops.js`
  - Added `_fitDropdownToContent()` helper (after `_menuDark`).
  - Hooks: post-`innerHTML` in `_renderTopoEntries`; three
    domain-collapse toggle points.
  - The `flex:1 1 auto;min-width:0` on the name span stays -- it's
    still needed for the ellipsis fallback path when the dropdown
    hits its 720px cap.
- `topology/topology.js` -> `/home/dn/CURSOR/topology.js`
  - Added a `requestAnimationFrame(() => _fitDropdownToContent())`
    call on `Topologies` button first-open.

### Verification

Manual test flow:

1. Hard-refresh the app (`Ctrl+Shift+R`) so the browser picks up both
   `topology-file-ops.js?v=20260421m` and the new inline HTML style.
2. Click the Topologies button. Dropdown opens at its natural width.
3. Expand a domain containing long names (e.g. BUGS with
   `BUG_FLOWSPEC_LOCAL_POLICY_RESOURCE_LEAK`).
4. Expected: the dropdown widens to fit the full name (up to ~720px).
5. Collapse that domain and expand one with short names (e.g. a
   section with `Test.json` only). Expected: the dropdown contracts
   back toward 300px. Content-dependent width is symmetric.
6. For pathological outliers (>100 char names), verify the row still
   ellipsis-truncates cleanly AND the native title tooltip on hover
   discloses the full name. The 720px cap does its job.
7. On a narrow viewport (window < 760px wide), verify the dropdown
   stays on-screen thanks to the `calc(100vw - 40px)` cap.

## BUGS domain cross-user leak fix: stop auto-migrating bug_evidence at startup (2026-04-21j)

### Symptom (user report)

"All users see same bugs it seems for some reason, only yarel saved bug
topologies though ...". Every user who logged in saw the same six
BUG_FLOWSPEC_* entries in the `BUGS` row of the Topologies dropdown,
even though only the founder (`yarel`) had ever explicitly saved bug
topologies.

### Root cause

`topology.js` (line ~13006) ran `FileOps._ensureBugsSection()` during
editor init. The legacy `_ensureBugsSection()` implementation did two
things in sequence:

1. Resolve the `__bugs` section id via `/api/sections`.
2. **POST to `/api/migrate-bug-topologies` on every call** (regardless
   of whether the section already had content or the user had ever
   opted in).

The backend endpoint `_migrate_bug_topologies(body)` in `serve.py`
copied every file in the **shared, global** directory
`~/SCALER/FLOWSPEC_VPN/bug_evidence/*.topology.json` into the
**calling user's** per-user `__bugs/` folder. The target path used
`self._section_dir(user, "__bugs")`, which correctly writes into
`~/.topology_users/<user>/sections/__bugs/`, but the **source** was a
fixed global path owned by `yarel` (the FLOWSPEC-VPN bug evidence
catalog). So every user who opened the app ended up with six
identical bug-replica topology files that appeared to belong to them,
with no visible trail back to the auto-migration.

This pattern silently violated the "Multi-user is the default" rule in
this document: state created by an authenticated action must live in
`~/.topology_users/<user>/...` and must originate from the user's own
write, not from a startup side effect that pulls from another user's
catalog.

### Evidence

- `slava` was the only non-`yarel` user who had already opened the app
  since the auto-migrator was last active. Their `__bugs/` folder
  contained exactly the six `BUG_FLOWSPEC_*.json` files, byte-identical
  (MD5 match) to the canonical sources in `bug_evidence/`.
- `adi.karolitsky` had an empty `__bugs/` folder -- they had never
  opened the app, so the frontend had never triggered
  `/api/migrate-bug-topologies` on their behalf.
- The direct REST path (`GET /api/sections/__bugs/topologies`) was
  already correctly per-user scoped; the leak happened through the
  implicit WRITE side channel in `_ensureBugsSection`.

### Fix (frontend)

1. `topology/topology.js` -- replaced the startup
   `window.FileOps._ensureBugsSection().catch(() => {}).then(() =>
   editor.loadCustomSections())` with a plain
   `editor.loadCustomSections()`. The backend injects `__bugs` and
   `__ai` into every user's `/api/sections` response via
   `BUILTIN_SECTIONS` (`serve.py` line 85+), so the frontend does not
   need to "ensure" them. A detailed comment records why the previous
   call was removed.
2. `topology/topology-file-ops.js` -- kept `_ensureBugsSection` as a
   thin id resolver (legacy `saveBugTopology` / `loadDebugDnosTopology`
   still reference it) but **removed both `/api/migrate-bug-topologies`
   fetches** from the body. It now just reads `/api/sections`, finds
   the builtin row (by `id === '__bugs'` OR `name === 'Bugs'`) and
   returns the id. Function cache-field `_bugsSectionId` unchanged.

### Fix (backend)

`topology/serve.py::_migrate_bug_topologies` now refuses the request
for anyone except `LEGACY_SECTIONS_OWNER` (default `yarel`). The
endpoint stays in place so the owner can manually re-seed the
bug_evidence catalog into their own `__bugs/` if needed, but it
returns HTTP 403 with a descriptive error for every other user. This
is a defense-in-depth layer in case a future frontend change
inadvertently re-wires a call site.

### Cleanup (one-off)

A Python script walked every `~/.topology_users/<user>/sections/__bugs/`
tree and **deleted files whose content was byte-identical (MD5 match)
to the source in `bug_evidence/`**. Files that had been modified by
the user, files that did not match a known source name (e.g. real
`SW-XXXXX_*.json` bug topologies the user authored via Create Bug),
and the `yarel` tree (owner) were left untouched. Result: 6 files
deleted from 1 user (`slava`). All other users had clean trees
already.

### Files touched + synced (2026-04-21j)

- `topology/topology.js` -> `/home/dn/CURSOR/topology.js`
- `topology/topology-file-ops.js` -> `/home/dn/CURSOR/topology-file-ops.js`
- `topology/serve.py` -> `/home/dn/CURSOR/serve.py` (requires
  server restart to take effect; `serve.py` does NOT auto-reload like
  `scaler_bridge.py` does)
- `topology/index.html` -> `/home/dn/CURSOR/index.html` (cache busters
  bumped: `topology-file-ops.js?v=20260421j`,
  `topology.js?v=20260421a`)

### Verification

```
# yarel (LEGACY_SECTIONS_OWNER): still sees their 8 authored bugs,
# manual migration still works for them.
yarel: 8 bug topologies
migrate -> {"ok": true, "migrated": 0}

# adi.karolitsky: sees 0 bugs (empty __bugs/), migrate refused.
adi.karolitsky: 0 bug topologies
migrate -> HTTP 403 {"ok": false, "error": "bug_evidence
  auto-migration is disabled for non-owner users..."}

# slava: __bugs/ cleaned; next login will fetch 0 topologies via
# the frontend and the migrate endpoint will refuse any attempt.
```

### Prevention rule

Whenever you see a "built-in" or "system" catalog being copied into
per-user state at startup, treat it as a multi-user leak until proven
otherwise. The correct pattern is one of:

- **Read-only catalog**: serve the global catalog through a dedicated
  endpoint (e.g. `/debug-dnos-topologies/list.json` + per-file GET)
  and let the user explicitly load files into their own workspace.
- **Explicit opt-in import**: expose an "Import example bugs" button
  under the user's Topologies menu that POSTs the migrate endpoint
  with an `{ confirmed: true }` body; default is never to run.
- **Owner-only seed**: gate the auto-migrator to the
  `LEGACY_SECTIONS_OWNER` user and document why, as done here.

Never run a blanket copy-on-startup from a global path into
`~/.topology_users/<caller>/` with no user opt-in.

## Bugs built-in domain: Edit re-enabled + default icon flipped (2026-04-21e-a)

Two linked fixes for the `__bugs` built-in Topologies section:

1. **Icon customization was blocked** -- the Manage Topology Domains
   panel hid the `Edit` button for any row flagged `builtin: true`.
   Users couldn't change the icon or color of `Bugs` (or `AI`) even
   though the backend at `/api/sections/update` happily accepts icon
   and color changes on builtins -- it just rejects renames.
2. **Default icon was misleading** -- the `__bugs` built-in seeded
   with the generic `alert` triangle icon, which reads as "warning /
   notification" rather than "bug report". Users asked for the
   dedicated `bug` icon (already defined in `FileOps._sectionIcons()`
   since the redesign) to be the default.

### Change (`topology/serve.py`)

- `BUILTIN_SECTIONS[__bugs].icon` now defaults to `"bug"` (was
  `"alert"`).
- `_inject_builtin_sections()` adds a **one-time conservative
  migration**: if an existing user's `__bugs` section has the exact
  old default icon `"alert"`, flip it to `"bug"` on next read. Users
  who later customize to any other icon are untouched because the
  check fires only on the exact old default value. New users get
  `bug` immediately.

### Change (`topology/topology-file-ops.js` -- `showManageSections`)

- The `Edit` button now renders for every domain row, including
  built-ins. Tooltip text differs so users know what's editable:
  `"Edit icon / color (name is fixed for built-ins)"` vs the
  non-builtin `"Edit"`.
- The edit form detects `sec.builtin` as `lockedName` and renders the
  name input as `readonly tabindex="-1"` with a subtle lock-icon
  helper row: `"Built-in name is fixed. Icon and color are editable."`
  Icon and color pickers remain fully interactive.
- The save handler always sends the **canonical** name for built-ins
  (`newName = lockedName ? sec.name : typedName`), so DOM tampering
  on the readonly input can't sneak a rename past the client-side
  guard. The backend also enforces the canonical name as a second
  line of defense (see `/api/sections/update` rejection).
- Delete button stays hidden for built-ins (`delHtml = isBuiltin ? ''
  : ...`) -- the spec is "editable, not deletable".

### Files touched + synced (2026-04-21e-a)

`topology/serve.py`, `topology/topology-file-ops.js`,
`topology/index.html` -> `/home/dn/CURSOR/`. Cache buster:
`topology-file-ops.js?v=20260421d` (pre-inversion bump). The running
`serve.py` keeps the old BUILTIN_SECTIONS default until restarted;
users can flip the icon manually via the now-unlocked Edit button
without waiting for a backend reload.

## Topologies menus render inverted vs body theme (2026-04-21e)

User asked the Topologies dropdown and its sub-menus (Manage
Topology Domains, New Topology domain picker, quick-save domain
picker, inline rename/duplicate forms, confirm bars, hover tooltips)
to render with the OPPOSITE theme of the body: dark menus on a light
canvas, light menus on a dark canvas. This sharpens the popover's
visual separation from the canvas regardless of the active mode.

### Helper (single source of truth)

`FileOps._menuDark(editor)` in `topology/topology-file-ops.js` is
the one function every menu-render path now calls instead of reading
`document.body.classList.contains('dark-mode')` or
`editor.darkMode` directly. It returns the INVERTED flag:

```
_menuDark(editor) {
    if (editor && typeof editor.darkMode === 'boolean') return !editor.darkMode;
    return !document.body.classList.contains('dark-mode');
}
```

If the inversion ever needs to be toggled back to body-matching (or
made configurable per user), flipping this one helper is the single
edit required.

### Call sites updated (all in topology-file-ops.js)

- `_showNewTopologyDomainPicker` (line ~407) -- picker overlay
- `quickSaveToDomain` (line ~910) -- quick-save domain picker
- `_renderTopoEntries` (line ~1413) + 7 inner sites (hover-bg, 3
  confirm bars, drag highlight, 2 cleanup-drag re-themes)
- `_showRenameInput` (line ~2183) -- inline rename form
- `_showDuplicatePicker` (line ~2214) -- duplicate-to-domain popup
- `_attachHoverTip` (line ~2688) -- menu-row hover tooltips
- `_renderCustomSectionsInDropdown` (line ~3033) -- domain category
  row background + (line ~3177) save-form input
- `_renderSharedInSectionsInDropdown` (line ~3583) + (line ~3743)
  remove-domain confirm bar
- `showManageSections` (line ~4008) -- whole Manage panel theme
- `_updateDropdownTheme` (line ~4470) -- per-row re-theme helper
  fired on body theme changes

Explicitly NOT inverted (kept body-themed):

- `_showPNGExportDialog` (~line 1047) and `_renderPNGExport` (~line
  1227) -- the PNG export dialog is NOT part of the Topologies
  popover tree; users export from the Save menu and the canvas
  frame should match the page theme for WYSIWYG.

### CSS overrides (`topology/styles.css` section after line 766)

The main dropdown uses `.liquid-glass-dropdown` whose background /
border / box-shadow / text color come from CSS. JS-side inversion
wouldn't reach those properties. New rules add a
`topo-menu-inverted` modifier class to the dropdown that swaps
which body state paints which chrome:

- `body.dark-mode .liquid-glass-dropdown.topo-menu-inverted` ->
  mirror of the original `body:not(.dark-mode) .liquid-glass-dropdown`
  (light popover on dark body).
- `body:not(.dark-mode) .liquid-glass-dropdown.topo-menu-inverted` ->
  mirror of the original base `.liquid-glass-dropdown` (dark popover
  on light body).

The Manage panel builds its surface via inline styles from
`_menuDark` so the main flip is JS-side; the matching
`#manage-sections-panel.topo-menu-inverted` CSS block only tweaks
shadow strength per effective theme so the panel doesn't look
washed-out against whichever canvas is behind it.

### Class wiring

- `#topologies-dropdown-menu` in `topology/index.html` now carries
  the `topo-menu-inverted` class alongside `liquid-glass-dropdown`.
  Static markup since the inversion rule is permanent for this
  surface.
- `#manage-sections-panel` gets `panel.className = 'topo-menu-inverted'`
  assigned in `showManageSections` before appending to the DOM so the
  CSS shadow rules take effect.
- The domain picker overlays (`#new-topo-domain-picker`,
  `#quick-save-domain-picker`, `#duplicate-picker-popup`) build their
  chrome from inline styles driven by `_menuDark`, so they already
  render inverted without needing the CSS class. Adding the class
  would be a no-op today and was omitted for cleanliness.

### Tooltip inversion caveat

`_attachHoverTip` was included in the inversion because every
current caller attaches tooltips to elements inside the Topologies
dropdown tree -- matching the menu theme keeps the tip visually
coherent with the surface it originated from, even though the tip
itself is appended to `document.body`. If a future caller needs a
body-themed tooltip (e.g. for a tooltip anchored to the canvas), add
an opt-in param to `_attachHoverTip` rather than reverting the
menu-theming decision.

### Files touched + synced (2026-04-21e)

`topology/topology-file-ops.js`, `topology/styles.css`,
`topology/index.html` -> `/home/dn/CURSOR/`. Cache busters:
`topology-file-ops.js?v=20260421e`, `styles.css?v=20260421e`.
No backend changes; browser hard-refresh is sufficient.

## Topologies Dropdown Readability Refinement -- 2026-04-21h

User feedback on the Topologies dropdown: "should be refined to be more
clear, contrasted from the canvas and readable." The liquid-glass look
was fine in isolation but bled into busy canvases -- domain chip
colours at ~13-16% alpha on a 45-50% opaque popover over a colourful
topology produced washed-out labels and low contrast.

### What changed

1. **`.liquid-glass-dropdown.topo-menu-inverted` popover opacity** in
   `topology/styles.css` (both body-light and body-dark variants):
   `0.5 / 0.45` -> `0.94 / 0.96`. Backdrop blur still applies and gives
   the liquid feel, but canvas objects no longer project through the
   menu. Shadows and border alpha tightened for crisper lift-off.

2. **Domain chip tint + accent stripe** in `topology-file-ops.js`:
   `${color}22/28` -> `${color}38/48` (roughly 13-16% -> 22-28% alpha)
   for the chip background, and `${color}55/90` -> `${color}80/d0` for
   the 3px left accent. Applied in ALL four spots that paint this:
   - main render (`custom-section-category` loop)
   - legacy/shared render
   - drag-over reset
   - theme-refresh repaint
   Drag-hover gradient was also bumped (`30/35` -> `55/60`, `15/18` ->
   `28/32`, shadow stroke `80` -> `a0`) so it stays clearly brighter
   than the new baseline during reorder operations.

3. **Inverted-menu text contrast** added as new CSS block in
   `topology/styles.css`:
   - `body.dark-mode .liquid-glass-dropdown.topo-menu-inverted
     .liquid-menu-item` paints dark text (menu is light).
   - `body:not(.dark-mode) .liquid-glass-dropdown.topo-menu-inverted
     .liquid-menu-item` paints light text (menu is dark).
   - `.category-label`, `.menu-desc`, `.liquid-shortcut`,
     `.menu-category` border, and `.liquid-menu-divider` all get
     matching contrast overrides so the File / Export sections, the
     "FILE" / "EXPORT" labels, the `⌘S` shortcut chip, and the between-
     section separator lines read correctly regardless of body theme.
   - `:hover` and `:active` backgrounds flip to cool-blue tints that
     match whichever inverted surface is behind them.

Before this fix, a dark-body / light-popover Topologies dropdown was
rendering base `rgba(255,255,255,0.9)` item text (white-on-white). The
default `body:not(.dark-mode) .liquid-menu-item` override only kicked
in when the BODY was light, but the popover is intentionally inverted
from the body -- so the existing rule set missed the inverted case
entirely. The new rules target `.topo-menu-inverted` descendants
directly, independent of body state.

### Files touched + synced (2026-04-21h)

`topology/styles.css`, `topology/topology-file-ops.js`,
`topology/index.html` -> `/home/dn/CURSOR/`. Cache busters bumped to
`styles.css?v=20260421h` and `topology-file-ops.js?v=20260421h`. No
backend changes; browser hard-refresh is sufficient.

### Follow-up fix (2026-04-21i): built-in domains didn't expand

User reported the `BUGS` (`__bugs`) and `AI` (`__ai`) rows wouldn't
open when clicked. Root cause: the domain-title mousedown handler in
`FileOps._renderCustomSections` (around line 3384) had an early return
for `isBuiltin`:

    if (isBuiltin) return; // built-in domains are pinned, not reorderable

This killed the entire handler -- including the collapse-toggle that
runs on mouseup when no drag happened. The comment's intent (no
reorder/drag) was correct, but the implementation also blocked the
click-to-expand behaviour.

Fix: for `isBuiltin` rows we now attach a lightweight mouseup listener
that flips `domain-body` display + rotates the chevron + updates
`editor._domainCollapsed`, with a 6px jitter tolerance matching the
drag threshold used for custom domains. The drag/reorder machinery
stays disabled for these rows. Child buttons (`+ Bug`, `Save`, `Load`,
`Share`) already call `e.stopPropagation()` on their own mousedown so
they continue to bypass this handler.

Also bumped the `.domain-title` inline `cursor` from `default` to
`pointer` for built-in rows -- previously the title had no visual
affordance of being clickable (the `.dd-grip` icon gave draggable rows
a `grab` cursor hint; built-ins had neither).

Files touched: `topology/topology-file-ops.js`,
`topology/index.html`. Cache buster bumped to
`topology-file-ops.js?v=20260421i`.

### How to verify

1. Hard-refresh the app. Open the Topologies dropdown over a busy
   canvas (colourful nodes, VRF labels, etc).
2. Each domain chip should have a clearly readable tinted background
   and a bright 3px accent stripe on the left matching its colour.
3. The "FILE" / "EXPORT" category labels should be readable (dark-grey
   on light menu, light-grey on dark menu) -- not invisible.
4. Menu items like "New Topology", "Load from File...", "Quick Save"
   should have clearly visible text and icons, with a subtle blue hover
   tint.
5. Repeat after toggling body theme (Dark/Light mode). The menu is
   still intentionally opposite to the body but both variants must be
   legible.
6. Click on the `BUGS` row and on the `AI` row -- both must expand to
   show their Save/Load/Share buttons and topology list (they did
   NOT expand before the 2026-04-21i follow-up fix). Clicking the
   `+ Bug` pill on the `BUGS` row header must open the Create Bug
   panel WITHOUT expanding the row.

## Multi-User is the Default (every new feature + every new database) -- 2026-04-20

**Hard rule (added per user directive on 2026-04-20, /XDN):**

> Every new feature, endpoint, state file, or database in this application
> MUST be designed as multi-user from the first commit. "Multi-user" means
> JWT-authenticated, per-user isolated state by default. Adding a new global
> state file (e.g. `~/.something.json`, an unscoped SQLite table, a server-
> side in-memory dict keyed on nothing, a `localStorage` key without the
> username scope) now requires explicit justification in the PR / commit
> message, a fallback plan, and a follow-up ticket to migrate it into the
> per-user layout.

### Why this rule exists

1. The app is already deployed multi-user (638+ seeded users). Any feature
   that writes to a global file causes inter-user contamination on the
   shared lab server (`~/.xray_config.json` got cross-polluted three times
   before we moved XRAY to per-user -- see "Per-User XRAY + API Hardening").
2. Auditability: per-user writes are easy to attribute, easy to reset, easy
   to back up. Global state hides the actor and leaves forensic gaps.
3. Security: JWT-gated per-user endpoints inherit the role system
   (`viewer < engineer < team_leader < manager < admin`) automatically;
   global endpoints force us to reimplement authorization each time.
4. Parity with DNOR: the surrounding organisation already treats per-user
   isolation as table-stakes (see `multiuser-rbac-alignment-dnor` and
   `multiuser-topomap-alignment` learned rules).

### Canonical per-user layout

All user-owned state lives under **`~/.topology_users/<username>/`**. The
single source of truth for path construction is
`topology/api/auth/user_store.py::UserStore`. No other module may hand-roll
a path to this directory.

| Path                                              | Owner in `UserStore` | What it stores |
|---------------------------------------------------|----------------------|----------------|
| `~/.topology_users/<user>/topologies.db`          | `user_db_path()`     | SQLite: `domains` + `topologies` (WAL mode, 5s busy timeout) |
| `~/.topology_users/<user>/sections/<sec_id>/*.json` | `serve.py BUILTIN_SECTIONS` | Legacy per-user sections (Bugs `__bugs`, etc.) |
| `~/.topology_users/<user>/xray.json`              | `user_xray_config_path()` | XRAY config (Mac IP, Wireshark path, DUT creds) |
| `~/.topology_users/<user>/client.json`            | `user_client_profile_path()` | Workstation profile (host OS, hostname, last IP) |
| `~/.topology_users/<user>/devices.json`           | `user_devices_db_path()` | Per-user SSH credential overrides |
| `~/.topology_users/<user>/captures/`              | `user_captures_dir()` | Server-side pcap files |
| `~/.topology_users/<user>/jira_config.json`       | `user_jira_config_path()` (NEW, wraps `user_data_path`) | Jira Cloud credentials (mode 0600) |
| `~/.topology_users/<user>/<any_new_json>`         | `user_data_path(filename)` (NEW -- use this) | **Escape hatch for every new feature** |

Central registry + cross-user sharing state lives in
`~/.topology_users/_users.db` (the `_users` prefix keeps it out of the
per-user directory listing). Schema is owned by `UserStore._ensure_central_db`:

- `users` -- credentials, display name, role, last login
- `shared_domains` + `domain_shares` + `share_activity` -- per-domain sharing
- `shared_topologies` + `topology_shares` -- per-file sharing
- `*_activity` indices on `ts`, `domain_id`, `owner`, `target_user`

Shared topology data (the blobs themselves) stays in the **owner's** user DB;
the central tables only index who has access. This avoids data duplication
and keeps edits atomic.

### The seven rules for anything you add from now on

1. **No global JSON/DB.** If you need server-side state, use `UserStore` paths.
   Use `user_store.user_data_path(username, "<your_feature>.json")` for any
   new per-user JSON blob; do not hand-roll `Path.home() / ".topology_users" / ...`.
2. **Route must require JWT.** Every mutating endpoint (`POST`, `PUT`, `DELETE`)
   and every endpoint that returns user-specific data must depend on the
   current user via the existing FastAPI dependency (see
   `topology/routes/*.py` for examples).
3. **SQLite = WAL + busy_timeout.** If you add a new SQLite DB, use the
   `_open_db()` context manager pattern in `user_store.py`:
   ```python
   with _open_db(db_path) as conn:
       conn.execute("PRAGMA journal_mode=WAL")
       conn.execute("PRAGMA busy_timeout=5000")
   ```
   Never open a raw `sqlite3.connect()` without these pragmas or you WILL
   get "database is locked" errors under concurrent users.
4. **Respect role hierarchy.** Use `user_store.has_role_or_higher(username, min_role)`
   for authorization checks instead of string comparisons.
5. **Shareable state goes through the existing `shared_*` tables.** Do not
   invent a new "share" mechanism; extend `shared_domains` / `shared_topologies`
   or add a new table with the same composite-id convention
   (`<owner>:<resource_id>` / `<owner>:<domain_id>:<topology_id>`).
6. **Frontend must use `authFetch`.** In JS, every fetch to `/api/...` goes
   through `window.TopologyAuth.authFetch(url, opts)` so the JWT is attached.
   Never write `fetch('/api/...')` directly in new code.
7. **`localStorage` keys are scoped by username when user-specific.** If you
   cache user-specific data client-side, use `localStorage[\`xdn_<feature>_${username}\`]`,
   NOT a flat key. Anonymous / truly global prefs (e.g. theme) may keep a flat
   key, but the default must be scoped.

### Global state files still pending migration (audit snapshot 2026-04-20)

These are **legacy globals** to be migrated as each feature is next touched.
New code must not add to this list; it should shrink over time.

| File / state            | Owner today                      | Migration target                                    | Priority |
|-------------------------|----------------------------------|-----------------------------------------------------|----------|
| `~/.scaler_push_history.json` | `scaler-gui.js` commits panel  | Per-user `push_history.json` via `user_data_path`   | High (commits show cross-user jobs today) |
| `~/.xray_config.json`   | XRAY helpers (legacy fallback)   | Already migrated; keep only as admin-only fallback  | Done (kept as fallback for CLI scripts) |
| `~/.device42_config.json` | Device42 credential lookup     | Per-user or admin-sealed central; usually read-only | Low |
| `console_mappings.json` | Console discovery cache          | Keep central (lab-global catalog), but gate writes  | Medium |
| `~/.cursor/dnos-cli-completions.json` | Dev-only completion cache | Leave global (dev assist, not user data)       | N/A |
| `localStorage['xdn_ssh_launch_pref']` | SSH launch preference     | Rename to `xdn_ssh_launch_pref_<username>`          | Low |
| Server-side job dicts (`_active_jobs`, `_push_jobs`, etc.) in `scaler_bridge` | process-global | Key every dict by `username` (cheap refactor)  | Medium |

**Every new PR that touches an item above should migrate it while it's open
(don't leave the list stale). Every new feature/DB starts at the "Done"
multi-user layout from day one.**

### Reusable helper: `user_store.user_data_path(username, filename)`

Added 2026-04-20. One-liner for any new per-user JSON / small DB file so new
code does not hand-roll the path:

```python
from api.auth.user_store import user_store

path = user_store.user_data_path(current_user["username"], "my_feature.json")
path.write_text(json.dumps(payload))
path.chmod(0o600)  # if the payload is a secret, e.g. API token
```

- Creates `~/.topology_users/<username>/` if it doesn't exist (idempotent).
- Never returns a path outside the user's directory (filename is
  `Path`-joined; any `..` traversal attempt raises `ValueError`).
- Use for JSON blobs, small SQLite DBs, caches, logs -- anything that is
  state-bearing and user-specific.
- For shareable data (visible to other users), go through
  `share_domain` / `share_topology` + the existing central tables instead.

### Cross-reference

- `topology-auth.js` -- login overlay, `authFetch`, user menu.
- `topology/api/auth/user_store.py` -- DB schema + all path construction.
- `topology/api/auth/identity.py` -- single source of truth for the
  username regex, the company-domain check, and the
  `derive_username_from_email` helper used by both the seed tool and
  the rename migration. Touch this file (and `api/schemas.py` if the
  regex changes) instead of hand-rolling validation in new code.
- `topology/api/seed_users.py` -- bulk seed of ~640 lab users. The
  preferred mode is `--from-email-cache PATH`, which derives every
  username from a verified `@drivenets.com` email local part. The
  legacy first/last-name mode is kept only for greenfield demos.
- `topology/api/migrations/` -- one-off migration helpers:
  - `email_resolver.py` queries Confluence with the operator's existing
    Jira credentials and writes `~/.topology_users/username_email_cache.json`.
  - `rename_to_email_local.py` is the dry-run / apply / rollback driver
    that re-keys the live multi-user state to email-local usernames
    (see "Username = email local part" below).
- `topology/api/migrate.py` -- one-shot legacy `~/.topology_sections/` ->
  per-user SQLite migration.
- Learned rules (from `~/.topology_learning.json`, synced to
  `~/.cursor/skills/xdn-topology-mastery/learned_index.md`):
  `multiuser-auth-system`, `multiuser-domain-model`, `multiuser-frontend-modules`,
  `multiuser-jwt-persistence`, `multiuser-migration`, `multiuser-rate-limiting`,
  `multiuser-rbac-alignment-dnor`, `multiuser-security-patterns`,
  `multiuser-sqlite-wal`, `multiuser-topomap-alignment`, `multiuser-user-seeding`.

## Username = email local part (DriveNets identity rule) -- 2026-04-26

**Hard rule (added per user directive on 2026-04-26):**

> Every topology username must be the local part of the worker's verified
> `@drivenets.com` email. Two distinct people may never share a username.
> The bootstrap `admin` account and the deployment owner `yor` are the
> only legacy exceptions, and `yor` is itself the post-migration
> identity (`yor@drivenets.com`) for the human formerly seeded as `yarel`.

The username doubles as:

- the primary key of `_users.db`,
- the directory name under `~/.topology_users/`,
- the JWT `sub` claim,
- the leading segment of every `<owner>:<domain_id>` and
  `<owner>:<domain_id>:<topology_id>` composite key in the share tables,
- the actor / target column in the device-state event log.

Tying it to a verified email keeps the identity stable across humans
with similar names ("Adi Offer" vs "Adi Offer-Smith"), prevents the
silent collision that the pre-2026-04-26 first/last-name seed could
produce, and lets us answer "who is this username?" by looking at one
file (`username_email_cache.json`) instead of grepping a wall of
display names.

### How the rule is enforced

- `api/auth/identity.py` is the single validator. New code that needs
  to construct or check a username must call
  `validate_username(...)` (regex + length) and, when an email is
  involved, `derive_username_from_email(...)`. Both raise
  `InvalidIdentityError` on bad input. The companion regex in
  `api/schemas.py` is intentionally identical -- if you ever loosen one
  you must loosen both.
- `api/seed_users.py --from-email-cache` is the preferred seed entry
  point. It loads the resolver cache, derives the username via
  `derive_username_from_email`, refuses to seed if any two cache rows
  collide on the same target username, and stores the email in the
  `users.email` column so future audits don't have to re-query
  Confluence.
- `api/migrations/rename_to_email_local.py` is the only sanctioned way
  to rewrite an existing live database. Operators run it offline (with
  the topology server stopped) using `--dry-run` first, then
  `--apply`. It refuses to start when the plan reports any
  collisions, duplicates, or invalid local parts; only `--allow-unsafe`
  bypasses that, and the rule is "don't".

### What the rename migration touches

When `rename_to_email_local.py --apply` runs it rewrites, atomically
per database, every place a username appears:

- `_users.db` central tables (`users`, `shared_domains`,
  `domain_shares`, `shared_topologies`, `topology_shares`,
  `share_activity`) including the leading owner segment of every
  composite primary / foreign key.
- The per-user filesystem -- `~/.topology_users/<old>/` is renamed to
  `~/.topology_users/<new>/` so `user_dir(...)`, `user_data_path(...)`,
  and every cached path returned by `UserStore` keep working.
- Each per-user `topologies.db` -- `topology_events.actor_user`, the
  free-form `details_json`, and any `domain_knowledge.payload` JSON
  that mentions another username.
- The cross-user `~/.topology_shared/_device_state.db` --
  `device_watchers.username`, `device_events.actor_user` (+ payload
  JSON), and `user_device_prefs.username`.

Every touched DB is copied into a timestamped backup directory under
`~/.topology_users/_migration_backups/<ts>/` before the first write,
and a manifest (`~/.topology_users/_migration_manifests/manifest_<ts>.json`)
records the full rename map plus the path of every backup. Re-running
the same script with `--rollback MANIFEST` restores the byte-for-byte
state.

JWTs encode `sub = old_username`, so every active token expires
naturally on the first 401 after a rename. Users log in again with the
new email-local username; the password is unchanged.

### Owner identity preservation

The deployment owner is recognised in two places --
`api/auth/service.py::is_owner_user` and the mirror helper
`serve.py::_is_owner_user` (the legacy stdlib HTTP handler). Both
canonical-username sets include `yor`, `yarel`, `yarel-or`, `yarelor`
so the owner-tier UI (reset-configs / restart-server / impersonate)
works before *and* after the rename without touching the
`OWNER_USERNAME` env var. The legacy section / discovery-output
inheritor (`LEGACY_SECTIONS_OWNERS`, `LEGACY_OUTPUT_OWNERS`) accepts
both names by default for the same reason.

### Operating procedure (live deployment)

1. `python3 -m api.migrations.email_resolver --operator <your_username>`
   -- generates / refreshes `~/.topology_users/username_email_cache.json`
   from Confluence using the per-user `jira_config.json` already on
   disk for the operator. The script never invents emails; users with
   missing or ambiguous Atlassian profiles are reported and skipped.
2. `python3 -m api.migrations.rename_to_email_local --dry-run` -- prints
   the plan summary and writes the human-readable report to
   `~/.topology_users/username_migration_report.json`. The plan is
   safe iff `collisions = duplicates = invalid = 0`.
3. Stop the topology server (`deploy_topology.sh stop` or equivalent).
4. `python3 -m api.migrations.rename_to_email_local --apply` --
   creates the backup set + manifest and rewrites every DB / directory.
5. Restart the server. Users see a 401 on next request and log in with
   the new username (their email local part). Display names, roles,
   shares, and per-user data are unchanged.
6. If anything looks wrong, run
   `python3 -m api.migrations.rename_to_email_local --rollback <manifest_path>`
   while the server is still stopped and restart again.

### Cross-reference

- Migration plan that drove this section:
  `.cursor/plans/email_username_migration_769dea6b.plan.md`
- Resolver cache + reports:
  `~/.topology_users/username_email_cache.json`,
  `~/.topology_users/username_migration_report.json`,
  `~/.topology_users/_migration_backups/`,
  `~/.topology_users/_migration_manifests/`.

## Ghost-IP Reaper (post-upgrade IP release) -- 2026-04-20

**The bug.** After a device is upgraded / re-imaged the lab's management
network may release its old IP, and DHCP / inventory rotation can reassign
that same IP to a completely different DUT. Our scaler DB and canvas
`device.sshConfig.host` both kept the stale IP, so clicking SSH on PE-4
silently opened a shell on whoever now answered at `100.64.11.118`
(we hit `R7-Natan_SIT` in practice). This is the "ghost IP" class.

**The fix.** Four cooperating layers:

1. **Identity guard in `/api/terminal/ws`** (`topology/routes/ssh.py`,
   `_extract_remote_hostname`, `_identity_matches`, `_expected_hostname_for_device`).
   After the SSH shell is opened and the initial banner/prompt is captured,
   we parse the remote hostname out of DNOS CLI prompts (`YOR_PE-1#`,
   `PE-4(cfg)#`) and bash prompts (`dn@kvm108:~$`). If the hostname has no
   substring overlap with the canvas device id (fuzzy, normalized to
   `[a-z0-9]+`), the identity check fails. The WS closes with a
   `ghost_ip_detected` message and a human-readable red banner in the
   terminal. This only runs for direct-SSH methods (`ssh_mgmt`, `ssh_sn`,
   `ssh_ncc`, `ssh_loopback`) -- `console` and `virsh_console` pass the
   KVM host first so the prompt cannot be trusted for identity.

2. **Reaper `_mark_device_ip_stale(scaler_id, stale_ip, reason, actual_hostname)`**
   (`topology/routes/bridge_helpers.py`). The single source of truth for
   "this IP is no longer reliable for this device". It:
   - writes `_stale=true`, `_stale_reason`, `_stale_at`, `_stale_last_mgmt_ip`,
     `_stale_last_ssh_host`, `_stale_remote_hostname` into the scaler
     `operational.json`; clears the live `mgmt_ip` / `ssh_host` fields;
   - evicts pooled SSH clients for the stale IP;
   - invalidates the scaler-ops index + resolve cache (`_invalidate_scaler_ops_cache`);
   - prunes the legacy `scaler/db/devices.json` row so the CLI library
     does not keep dialling the ghost host either.
   Returns a machine-readable summary for the UI.

3. **`_build_scaler_ops_index` honours `_stale`** -- stale operational
   entries are still indexed under their scaler_id (so config / context
   lookups keep working for the upgraded device) but with `ip=""`, so
   every subsequent `_resolve_mgmt_ip` path returns `HTTPException(503)`
   ("Could not resolve IP... Set SSH address on the canvas") instead of
   silently returning the ghost IP. The resolver falls through
   scaler-index -> discovery -> inventory -> partial-name match; all
   sources that publish an IP are given a chance before giving up.

4. **Frontend reaction.**
   - `topology/topology-terminal.js :: TerminalPanel._handleGhostIp(session, msg)`
     renders the red banner, sets `_noAutoReconnect`, dispatches a global
     `ssh:ghost-ip-detected` `CustomEvent`, and fires the app toast.
   - `topology/topology-ssh-dialog.js` installs a one-time global
     listener (`installGhostIpHandler`) that walks `editor.objects`, finds
     every device whose label/serial or cached `sshConfig.host` matches
     the reaped identity, and clears `device.sshConfig.host` +
     `device.deviceAddress`, stashing the old value under
     `sshConfig._ghostHost` / `_ghostClearedAt` / `_ghostActualHostname`.
     A history snapshot + `saveToLocalStorage` run so undo/restore are
     consistent. Next SSH click opens the dialog fresh and re-discovers.

**Explicit cleanup endpoint:** `POST /api/ssh/clear-ghost-ip`
(`routes/ssh.py :: clear_ghost_ip`). Body:
```json
{"device_id": "...", "ip": "...", "actual_hostname": "...", "reason": "..."}
```
Proxied by `serve.py`. Client helper: `ScalerAPI.clearGhostIp(deviceId, opts)`
in `topology/scaler-api.js`. Idempotent -- calling twice on an already-reaped
device just confirms the state.

**Pre-flight identity check (2026-04-20 follow-up).** The WS terminal
identity guard only fires on the *web terminal* path. When the fast path
in `openTerminalToDevice()` opens **native iTerm**, the user would still
land on the ghost IP because iTerm is out-of-band. We now block this:

- **`POST /api/ssh/verify-identity`** (`routes/ssh.py :: verify_ssh_identity`)
  opens a 3-4s SSH, drains the banner + prompt (with a single newline
  nudge if silent), extracts the hostname, compares via `_identity_matches`
  (with a `_GENERIC_PROMPT_HOSTS` allow-list for `GI`/`RECOVERY`/`BASEOS`
  so cluster devices mid-upgrade don't false-alarm), and **auto-reaps**
  on a hard mismatch. Returns `{reachable, identity_verified, actual_hostname,
  expected_hostname, generic_prompt?, reason?, reaped?}`.
- **`ScalerAPI.verifyDeviceIdentity(deviceId, ip, opts)`** (scaler-api.js)
  is the client wrapper. Called from `openTerminalToDevice()` right after
  `checkPort` (TCP reachable) succeeds. On `reason === 'ghost_ip'`:
  dispatches `ssh:ghost-ip-detected` globally, shows a warning toast, and
  opens the SSH dialog instead of iTerm. `generic_prompt` is logged but
  proceeds (GI mode is legit).
- **Probe graceful-degrade** (`probe_connection`). When the resolver
  raises 503 for a reaped device, the probe falls back to reading
  `operational.json` directly -- so `virsh_console` + `ssh_ncc` targets
  still appear in the SSH dialog. The user sees `recommended: virsh_console`
  with both NCC VMs running, and can recover via KVM without needing the
  mgmt IP. Returns `stale_note` so the dialog can show *"Management IP
  released (was X, reason: Y). Use virsh console ..."*.
- **`_mark_device_ip_stale` also reaps `ncc_mgmt_ip`** when it equals
  the stale IP. Previously only `mgmt_ip` + `ssh_host` were cleared, so
  a stale `ncc_mgmt_ip` could re-introduce the ghost via the cached
  NCC iTerm path in `openTerminalToDevice()`.
- **Ghost-IP canvas handler** (`topology-ssh-dialog.js :: installGhostIpHandler`)
  now clears every IP-bearing slot: `host`, `_userSavedHost`, `hostBackup`,
  `_enrichedMgmtIp`, `_nccMgmtIp`, `_candidateMgmtIp`, `deviceAddress`.
  Stashes the previous values under `sshConfig._ghostCleared` for
  forensics. Without this, `openTerminalToDevice`'s fallback chain would
  silently resurrect the ghost from a cached slot.

**Cache busters bumped:** `topology-ssh-dialog.js?v=20260420b`,
`topology-terminal.js?v=20260419g`, `topology-object-detection.js?v=20260420b`,
`scaler-api.js?v=20260420b`.

### 2026-04-21b Correction: GI / recovery uses SN-iTerm (pre-upgrade canonical path)

**Correction from the operator.** The primary iTerm path for a cluster
device in GI / BASEOS_SHELL / RECOVERY / post-upgrade is **SSH to the
serial-number hostname**, not the virsh console. That is the way the
operator connected to the active NCC BEFORE the system was deleted --
lab DNS (on the Mac via VPN) maps the SN (e.g. `WDY1A17E00011-P3`) to
the NCC's current recovery IP, and this identifier is stable across
upgrades, reinstalls, and ghost-IP reaps. Virsh console is the fallback
when SN DNS is not reachable from the operator's workstation.

**Backend** (`topology/routes/bridge_helpers.py :: _get_device_context`).
`identity.serial` is now populated on every call, including when
`mgmt_ip` is empty (the ghost-IP-reaped state). The lookup order:

1. `_build_scaler_ops_index()` keyed by `mgmt_ip` if present.
2. Same index keyed by `scaler_device_id.lower()` or `device_id.lower()`.
3. Last-resort: read `operational.json` directly off `SCALER_ROOT`
   and use `serial_number` / `serial`.

Previously this block ran only when `resolved_via != "failed"`, so a
device with no resolvable mgmt IP (exactly the case for a post-upgrade
cluster) got `identity.serial = ""` even though the scaler ops cache
still had the SN. Confirmed fix: PE-4 now returns
`identity.serial = "WDY1A17E00011-P3"` with `identity.mgmt_ip = ""`.

**Frontend** (`topology/topology-object-detection.js`):

- **New helper `_getDeviceSerial(device)`** resolves the SN with
  three cascading sources: `device.sshConfig._serial` cache ->
  `ScalerAPI.getDeviceContext().identity.serial` ->
  `ScalerAPI.probeConnection()` `methods[ssh_sn].host`. Caches the
  result on `device.sshConfig._serial` so subsequent clicks are instant.
- **New helper `_tryOpenSnIterm(editor, device, {user, password, modeLabel})`**
  fires `editor._openSshUrl('ssh://dnroot@<SN>')` via the existing
  iTerm dispatch path (no TCP pre-flight -- the SN may not resolve
  from the topology server but resolves from the operator's Mac).
  Uses `_openSshUrl`'s built-in "Web Terminal" fallback button, so if
  the user's Mac cannot resolve the SN they have a one-click escape
  to the virsh console. Returns `true` on launch, `false` when no
  serial can be discovered (non-recovery path continues with IP
  fallbacks).
- **GI / BASEOS_SHELL / RECOVERY block** now tries `_tryOpenSnIterm`
  FIRST. Only on failure does it fall through to the prior order:
  sticky `preferredMethod='iterm'` -> NCC mgmt IP, virsh console in
  the web terminal, unreachable modal.
- **Ghost-IP verification branch** now also tries `_tryOpenSnIterm`
  first for cluster devices before attempting the virsh-console
  recovery. The ghost-IP warning banner now reads
  *"Launching iTerm to serial <SN>"*.

**Why this order is safer for the operator's mental model.** Non-cluster
devices and healthy DNOS clusters continue to use the IP-based iTerm
fast-path (no behaviour change). Only clusters that the backend marks
as GI/BASEOS_SHELL/RECOVERY or reaped-mgmt-IP now prefer SN iTerm --
the exact set of devices where the IP is UNTRUSTWORTHY. The existing
iTerm toast's "Web Terminal" fallback button means an SN that doesn't
resolve on the Mac is one click away from a guaranteed virsh path.

**Cache busters bumped:** `topology-object-detection.js?v=20260421i`.

**Files touched + synced:** `topology/routes/bridge_helpers.py` ->
`/home/dn/CURSOR/routes/bridge_helpers.py`,
`topology/topology-object-detection.js` + `topology/index.html` ->
`/home/dn/CURSOR/`.

### 2026-04-21j Correction: GI/recovery iTerm targets the **active NCC hostname**, not the chassis SN

**Operator report:** iTerm was landing on the *NCP*, not the active NCC.
On PE-4 the operational cache held `serial_number = "WDY1A17E00011-P3"`.
The `-P3` suffix is the **NCP position** in the chassis, so iTerm was
opening `ssh://dnroot@WDY1A17E00011-P3` -- a line card, not the active
NCC (NCC-1 for this cluster). The user's request: "why to the NCP in
the cluster and not to the NCC active one? (NCC-1 for this cluster)".

**Root cause.** For a KVM cluster, the canonical recovery-mode target is
the DNS hostname of the NCC that currently owns the cluster mgmt IP
(e.g. `kvm108-cl408d-ncc1`). Each NCC VM resolves to its own per-node
IP; only the active NCC's hostname matches `ncc_mgmt_ip`. Relying on
`active_ncc_vm` from `operational.json` is wrong because it goes stale
after every mastership flip -- on PE-4 the cache still said `ncc0`
while DNS proved NCC-1 was the one answering.

**Fix -- backend** (`topology/routes/bridge_helpers.py`):

- New helper `_resolve_active_ncc_host(ncc_hosts, ncc_mgmt_ip, cached_active_ncc)`.
  DNS-resolves every NCC host, matches resolved IP against `ncc_mgmt_ip`,
  returns a dict: `active_ncc_host`, `active_ncc_ip`, `dns_map`, `source`
  (`dns_match` | `cached` | `fallback`). Never raises.
- `_get_device_context` now populates `ctx["active_ncc_host"]` (and
  `active_ncc_source`, `active_ncc_ip`) for KVM clusters by calling the
  helper; falls through gracefully when DNS is unavailable.

**Fix -- backend** (`topology/routes/ssh.py :: probe_connection`):

- Calls `_resolve_active_ncc_host` BEFORE the ops-write gate so a stale
  `active_ncc_vm` is self-healed on every probe (PE-4 operational.json
  now reads `active_ncc_vm = kvm108-cl408d-ncc1`, was `ncc0`).
- Reorders `cluster.ncc_hosts` so the DNS-detected active NCC is first
  (frontend uses `[0]` as primary).
- Overrides the `ssh_ncc` probe entry's `host` field with the
  DNS-resolved active NCC, and tags it `active_ncc_source`. The
  DeviceConnector ordered targets by the cached `active_ncc_vm` so
  its `ssh_ncc.host` was pointing at the standby NCC until this
  rewrite.
- Emits `cluster.active_ncc_host`, `active_ncc_ip`,
  `active_ncc_source`, and `ncc_dns_map` in the probe response.

**Fix -- frontend** (`topology/topology-object-detection.js`):

- Removed `_getDeviceSerial` / `_tryOpenSnIterm` (chassis-SN-based).
- New `_getActiveNccHost(device)` cascades: `sshConfig._activeNccHost`
  cache -> probe `cluster.active_ncc_host` -> probe `ssh_ncc.host` ->
  probe `cluster.ncc_hosts[0]` (already ordered active-first) ->
  context `active_ncc_node`.
- New `_tryOpenActiveNccIterm(editor, device, {user, password, modeLabel})`
  fires `ssh://dnroot@<active-ncc-host>` through `editor._openSshUrl`.
  Caches the resolved host and emits a log line tagged with the
  resolution source (`dns_match` / `ssh_ncc_probe` / ...).
- GI / BASEOS_SHELL / RECOVERY block and the ghost-IP verification
  branch now call `_tryOpenActiveNccIterm` FIRST. Fall-through order
  for both: active-NCC iTerm -> NCC mgmt IP iTerm (sticky pref) ->
  virsh console in the web terminal -> unreachable modal.
- Ghost-IP banner now reads *"Launching iTerm to active NCC
  kvm108-cl408d-nccN"*.

**Verification on PE-4 (2026-04-21):**

- `POST /api/ssh/probe` -> `cluster.active_ncc_host = "kvm108-cl408d-ncc1"`,
  `active_ncc_source = "dns_match"`, `ncc_hosts[0] = "kvm108-cl408d-ncc1"`,
  `methods[ssh_ncc].host = "kvm108-cl408d-ncc1"`.
- `operational.json` self-healed: `active_ncc_vm = "kvm108-cl408d-ncc1"`.
- `/api/devices/YOR_CL_PE-4/context` -> `active_ncc_host =
  "kvm108-cl408d-ncc1"`, `active_ncc_source = "dns_match"`.

**Cache busters bumped:** `topology-object-detection.js?v=20260421j`.

**Files touched + synced:** `topology/routes/bridge_helpers.py`,
`topology/routes/ssh.py`, `topology/topology-object-detection.js`,
`topology/index.html` -> `/home/dn/CURSOR/`.

### 2026-04-21k Correction: GI/RECOVERY iTerm path now bypasses sticky webterm preference

**Operator report:** "Why does it work via web and not via iTerm?". The
console log proved the `-> iTerm via active NCC` line fired correctly,
but the very next log was `method decision: host=kvm108-cl408d-ncc1
web=true reason=device-sticky=webterm` -- the per-device
`sshConfig.preferredMethod = 'webterm'` from a previous SSH-dialog
picker choice flipped the launch to the web terminal at the last
mile inside `_openSshUrl :: _shouldUseWebTerminal`.

**Root cause.** `_pickLaunchMethod` ordering was: device-sticky >
global-pref > platform default. GI/RECOVERY callers (`_tryOpenActiveNccIterm`)
expressed explicit recovery intent but had no way to signal
"this launch is intentional, ignore the sticky". The result was
technically correct (user asked for web, they got web), but wrong
for the recovery context -- the active-NCC hostname path is the
only way to reach a cluster when the management IP was reaped;
sending it to the web terminal anyway hides the intent.

**Fix** (`topology/topology-object-detection.js`):

- `_tryOpenActiveNccIterm(editor, device, opts)` now accepts
  `opts.forceIterm` (defaults to `true`). When set, it raises
  `this._forceItermOnce = true` right before dispatching the
  ssh:// URL.
- `_shouldUseWebTerminal(host, device)` checks `this._forceItermOnce`
  first and, if set, returns `false` and consumes the flag:

```text
[SSH] method decision: host=<ncc> web=false reason=force-iterm-once (recovery-intent bypass)
```

- The flag is ONE-SHOT. It's consumed on the first decision check
  so unrelated future clicks still respect the sticky preference.
- Defensively cleared in the `_openSshUrl` catch branch so an
  exception cannot leak the flag into the next launch.

**What users still see / can do.** The sticky stays persisted --
the operator's earlier "always Web for this device" choice is not
overwritten. Only GI/RECOVERY recovery-intent launches override it.
To change the sticky itself, use the SSH dialog's "Connect via"
3-button picker (Auto / iTerm / Web).

**Cache busters bumped:** `topology-object-detection.js?v=20260421k`.

### 2026-04-21l Correction: Active-NCC iTerm uses IP, not hostname (Mac lacks lab DNS)

**Operator report:** "Why iTerm to PE-1 works but for PE-4 in GI mode not?".
Live probe data from the same session:

| Device | Type | iTerm target (prior to this fix) |
|---|---|---|
| PE-1 | standalone DNOS | `ssh://dnroot@100.64.4.200` (IPv4 mgmt IP) |
| PE-4 | KVM cluster, GI | `ssh://dnroot@kvm108-cl408d-ncc1` (DNS hostname) |

**Root cause.** The operator's Mac has lab *routing* via VPN (which is
why PE-1's IPv4 target succeeds -- 100.64.4.200 is directly reachable)
but it does NOT have lab *DNS* (the VPN config typically doesn't push
`dev.drivenets.net` resolvers). When iTerm runs
`ssh dnroot@kvm108-cl408d-ncc1`, macOS resolves the hostname and gets
nothing, so ssh aborts with `Could not resolve hostname` before any
TCP connect. iTerm then closes the tab (default behaviour on non-zero
exit when launched from a URL handler), so the operator sees nothing
and assumes the launch never happened.

The backend probe already DNS-resolved the hostname (`ncc_dns_map`
field in the response), so the IP is already known on the frontend --
we were just throwing it away.

**Fix** (`topology/topology-object-detection.js`):

- `_getActiveNccHost(device)` -> `_getActiveNccTarget(device)`.
  The new method returns `{host, ip, source}`, populating both from
  probe `cluster.active_ncc_host` / `cluster.active_ncc_ip` (with
  `ncc_dns_map[host]` as a fallback when `active_ncc_ip` is missing).
  Caches `_activeNccHost` + `_activeNccIp` on `sshConfig` so repeat
  clicks are instant. `_getActiveNccHost` is kept as a thin
  backward-compat wrapper returning just the host string.
- `_tryOpenActiveNccIterm` accepts `opts.preferIp` (default `true`).
  When true, the ssh:// URL uses the backend-resolved IPv4 instead of
  the DNS hostname, sidestepping Mac DNS entirely. Console logs both
  values for debugging:

```text
[SSH] -> iTerm via active NCC: ssh://dnroot@100.64.4.122 (host=kvm108-cl408d-ncc1 ip=100.64.4.122) [RECOVERY] [src=dns_match] [using-ip] [force-iterm]
```

- Notification toast shows both forms so the operator still knows
  which logical NCC they landed on: `[OK] iTerm -> kvm108-cl408d-ncc1 (100.64.4.122) (RECOVERY)`.
- Operators who have `/etc/hosts` entries or Tailscale MagicDNS can
  pass `opts.preferIp = false` to get the hostname form back.

**Why this matches PE-1 behaviour.** PE-1's iTerm already uses
`sshConfig.host = '100.64.4.200'` (IPv4 mgmt IP). This fix makes PE-4
in GI mode follow the same pattern: backend resolves the DNS name,
frontend hands the IP to iTerm.

**Cache busters bumped:** `topology-object-detection.js?v=20260421l`.

### 2026-04-21m Final root cause: stale SSH host keys on operator's Mac after cluster re-deploy

**Operator report (end of the thread):** "I cleared host key from the App and
this is what shows when I run it manually:"

```text
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
...
Offending ED25519 key in /Users/yarelor/.ssh/known_hosts:158
Host key for kvm108-cl408d-ncc1 has changed and you have requested strict checking.
Host key verification failed.
```

**What this is telling us.** Every earlier "iTerm opened a tab and it
closed immediately" report in this session was NOT a DNS failure and
NOT a routing failure. It was a host-key collision. When PE-4 was
re-deployed in GI mode, the NCC got brand-new ED25519 host keys.
The operator's `~/.ssh/known_hosts:158` still held the old key, so
`ssh` exited with `Host key verification failed` before any auth
happened. Because `ssh` was invoked from the `ssh://` URL handler,
iTerm closed the tab on non-zero exit and the operator saw nothing.

**Why the existing `Clear host key` checkbox in the SSH dialog did NOT help.**
The endpoint `/api/ssh/clear-hostkey` took a single host string. Callers
passed only the NCC DNS hostname, but `known_hosts` stores the key under
BOTH the hostname and the IP (whichever form the user first connected
with). The IP stayed stale, `ssh` still failed, iTerm still exited
silently. On top of that the flow needed the operator's Mac VPN IP to
be current in XRAY settings -- when stale (the screenshot showed
`10.312.104.36`, an invalid octet), the clear silently no-op'd and the
user never knew.

**Fix -- three layers:**

1. **Backend `/api/ssh/clear-hostkey` now batch-clears every alias.**
   Accepts `{hosts: [...]}` (list) alongside the legacy `{host: "..."}`
   form. Dedupes, validates each entry, runs `ssh-keygen -R` once for
   every alias both on the server and on the Mac (chained in a single
   SSH connection to avoid handshake-per-host latency). Returns
   per-target result objects plus a `copy_command` string
   (e.g. `ssh-keygen -R kvm108-cl408d-ncc1 && ssh-keygen -R 100.64.4.122`)
   so the UI has a ready-to-paste fallback when the Mac itself is
   unreachable.

2. **Frontend collects every plausible alias and pre-clears BEFORE
   launching iTerm.** New helper
   `_collectStaleHostKeyTargets(device, resolvedTarget)` gathers:
   - `_activeNccHost` + `_activeNccIp` (resolved or cached)
   - every entry in `sshConfig._activeNccDnsMap` (all NCC hostnames AND
     their resolved IPs, because another NCC may have been active
     last time)
   - `sshConfig.host` (the cluster mgmt IP -- often follows the active
     NCC across a re-deploy)
   - `_nccMgmtIp`, `_virshInfo.nccMgmtIp`, `_virshInfo.nccVms[*]`,
     `_virshInfo.activeNcc`
   - short-name forms of every hostname (token before the first `.`)
     because some `known_hosts` entries are stored that way.

   Companion helper `_clearStaleHostKeysOnMac(editor, device, targets)`
   POSTs the list and handles three UX branches:
   - **All cleared on Mac:** small success toast (`[OK] Cleared stale
     host keys on Mac (N aliases)`), then iTerm launches.
   - **Mac SSH failed (stale VPN IP / Remote Login off / unreachable):**
     auto-copies the `copy_command` to the operator's clipboard via
     `_safeClipboardWrite` and shows a warning toast telling them to
     paste it in their Mac Terminal then retry. Zero extra clicks.
   - **Endpoint error (server down):** simple warning toast, launch
     still proceeds so the behaviour is no worse than before.

3. **`_tryOpenActiveNccIterm` now defaults `clearStaleHostKeys: true`.**
   The pre-clear `await` runs right before `_openSshUrl(...)`, so
   iTerm always sees a clean `known_hosts` for the target. Callers can
   opt out with `opts.clearStaleHostKeys = false` for non-recovery
   launches (none exist today -- both current callers are the GI /
   BASEOS_SHELL / RECOVERY and ghost-IP paths, exactly where the NCC
   keys are guaranteed to have rotated).

**Key code references:**

- `topology/serve.py` handler at `if path == "/api/ssh/clear-hostkey":`
  (batch loop + `copy_command` field).
- `topology/topology-object-detection.js :: _collectStaleHostKeyTargets`
  -- alias harvester.
- `topology/topology-object-detection.js :: _clearStaleHostKeysOnMac`
  -- batch + clipboard fallback.
- `topology/topology-object-detection.js :: _tryOpenActiveNccIterm`
  -- new `clearStaleHostKeys` opt (default true), pre-clear before
  `_openSshUrl`. Log line now includes `[clear-stale-keys]`.

**Why this survives future re-deploys.** The alias list is rebuilt
fresh from `sshConfig` + the probe's DNS map on every recovery launch.
Any NCC alias the operator's Mac may have cached -- even ones never
targeted by this app -- is harvested from the `ncc_dns_map` returned
by `/api/ssh/probe`, so the clear is effectively exhaustive for the
cluster.

**Operator guidance when Mac VPN IP is stale.** The clipboard-fallback
path is the fastest recovery. Open iTerm, paste, Enter, click iTerm
again on the device -- done. No need to update XRAY settings first.

**Cache busters bumped:** `topology-object-detection.js?v=20260421m`.

### 2026-04-21n Follow-up: Grey screen + persistent "auto-clear on connect" intent

**Operator report.** "When issuing host key checkbox and save, a grey screen
appears, and the next SSH connection to the device doesn't run the host-key
clear on the Macbook."

**Bug A -- grey screen.** `_showMacIpPrompt` in `topology-ssh-dialog.js` was
doing:

```js
overlay.style.cssText = 'position:absolute;left:0;right:0;bottom:0;...';
panel.style.position = 'relative';   // <-- clobbers panel's position:fixed
panel.appendChild(overlay);
```

The SSH dialog panel is declared `position: fixed` with viewport-coordinate
`left` / `top` / `transform: translateX(-50%)`. Changing `panel.style.position`
to `'relative'` overrode just that property while leaving the rest of the
cssText intact. Under `relative` those coordinates are reinterpreted as flow
offsets instead of viewport offsets, so the dialog jumped to a random spot
on screen (often off-canvas) and its `backdrop-filter: blur()` no longer
matched its new geometry -- what the operator saw as a "grey screen".

`position: fixed` already qualifies the panel as a positioning context for
absolutely-positioned descendants, so the whole line was unnecessary.

**Bug B -- next connect doesn't clear.** The "Clear host key" checkbox was a
one-shot side-effect on Save. Even on a successful clear, no per-device
state was persisted. The next iTerm launch (whether via the active-NCC
recovery path or the plain IP launch for a healthy device) hit the same
`~/.ssh/known_hosts` entry and failed identically.

**Fix A (`topology/topology-ssh-dialog.js`):**

1. Remove `panel.style.position = 'relative'`. Document why in the inline
   comment so no future edit re-introduces it.
2. Before appending, drop any existing `._mac-ip-overlay` inside the panel
   -- guarantees the prompt never stacks on top of itself.
3. Add a `&times;` close button (upper-right of the overlay) plus two new
   action buttons:
   - **Copy command** -- writes `ssh-keygen -R h1 && ssh-keygen -R h2 && ...`
     to the clipboard via `editor._safeClipboardWrite` (HTTP-safe) and shows
     a success toast. Lets the operator paste in their Mac Terminal in one
     step when the Mac VPN IP is stale (the common case).
   - **Skip & connect** -- dispatches the ssh:// URL immediately. Operator
     accepts responsibility for clearing manually; no second save click.
4. The "Update & Clear" retry now uses the new batch form
   `{hosts: aliases, host: aliases[0]}` and pre-fills with every alias the
   device could be cached under.

**Fix B (`topology/topology-ssh-dialog.js`):**

The checkbox is re-labelled "Auto-clear host key on connect" and its state
is now **persisted per device** in `sshConfig._autoClearHostKeys`. On
dialog open, the checkbox is pre-checked when the flag is true. On save,
`sshConfig._autoClearHostKeys = !!clearHostKey` is written regardless of
whether the immediate clear succeeds -- so the operator's intent survives
even if the Mac is unreachable right now.

When the checkbox is checked at Save time, the dialog now collects every
alias via `window.ObjectDetection._collectStaleHostKeyTargets(device, {...})`
and POSTs them all in one call rather than clearing only the user-typed host.

**Fix C (`topology/topology-object-detection.js` :: `_openSshUrl`):**

`_openSshUrl` is the single dispatch point for every iTerm launch. A new
pre-step reads `device.sshConfig._autoClearHostKeys`, and when true:

1. Collects the alias list from `_collectStaleHostKeyTargets(device, ...)`
   plus the exact `host` extracted from the `ssh://` URL.
2. Checks `this._lastHostKeyClearAt` -- if a clear for a superset of these
   targets fired within the last 4s (e.g. the GI/RECOVERY path already did
   it in `_tryOpenActiveNccIterm`), skip and dispatch immediately.
3. Otherwise `await _clearStaleHostKeysOnMac(editor, device, targets)` and
   only then dispatch the ssh:// URL. Without the `await` the browser would
   race the ssh-keygen request against the iTerm handoff.

The dispatch itself is refactored into a local `dispatchIterm()` closure
so both the immediate-launch and the post-clear-launch paths share a
single code path (anchor click + password copy + toast).

`_clearStaleHostKeysOnMac` now records `this._lastHostKeyClearAt` +
`this._lastHostKeyClearTargets` so the dedup in `_openSshUrl` can reason
about "was this just cleared?".

**User-visible result.**

- Check "Auto-clear host key on connect" once -> every future iTerm
  launch for that device clears stale entries first, no matter the mode
  (healthy DNOS, GI, BASEOS, RECOVERY, ghost-IP, NCC mgmt iTerm).
- If the Mac is unreachable, the overlay offers a one-click Copy
  command -- no need to hunt for the right `ssh-keygen -R` invocation.
- Uncheck the box and Save to opt out. Persisted per device; one
  device's preference does not affect another.

**Cache busters bumped:** `topology-ssh-dialog.js?v=20260421n` +
`topology-object-detection.js?v=20260421n`.

---

### 2026-04-19 Post-delete host-key hint (upgrade flow <-> SSH credentials panel)

**Operator report.** "After system delete on a device from upgrade flow, the
SSH credentials panel should automatically suggest clear host key-check on the
correct NCC that was active before the system delete from the upgrade flow."

**Why.** `request system delete` wipes the running DNOS instance, reboots the
active NCC into GI, and deploys a fresh install. The deployed NCC generates a
new SSH host key; the operator's Mac still trusts the previous one. The next
SSH attempt trips the `REMOTE HOST IDENTIFICATION HAS CHANGED` warning unless
`ssh-keygen -R <alias>` was run first. The agent already knows which NCC was
active right before the delete (from `connect_for_upgrade`), so the panel can
pre-suggest clearing *that* NCC's host key.

**Data path.**

1. **Backend** -- `topology/routes/upgrade.py :: _run_delete_deploy_upgrade`:
   - After `connect_for_upgrade(...)` returns, capture
     `pre_delete_active_ncc_vm` (e.g. `cfg1`), `pre_delete_active_ncc_id`
     (0/1), and `pre_delete_mgmt_ip` (connected IP).
   - Persist them into `operational.json` alongside `delete_initiated`.
   - BEFORE sending `chan.send("request system delete\n")`, call
     `_update_device_state(job_id, device_id, suggest_clear_host_key=True,
     pre_delete_active_ncc_vm=..., pre_delete_active_ncc_id=...,
     pre_delete_mgmt_ip=..., delete_initiated_at=<ISO>)`.
   - The push-job `_push_jobs[...]` stream carries these fields through to
     the frontend SSE channel.

2. **Frontend progress handler** -- `topology/scaler-gui-progress.js`:
   - `_stampPostDeleteSuggestion(did, s)` runs inside `renderDeviceState`
     for every SSE frame. On first sight of `s.suggest_clear_host_key`, it
     finds the canvas device by `label/serial/id` and stamps:
     - `device.sshConfig._postDeleteClearHostKey = true`
     - `device.sshConfig._postDeleteActiveNccVm`
     - `device.sshConfig._postDeleteActiveNccId`
     - `device.sshConfig._postDeleteMgmtIp`
     - `device.sshConfig._postDeleteAtIso`
     - `device.sshConfig._postDeleteJobId`
   - A `_postDeleteStamped` `Set` de-dupes across the ~2 Hz SSE frames so
     `editor.saveState()` fires once per device per job.
   - Calls `window.refreshSSHDialogPostDeleteHint(device)` so an already-open
     SSH dialog re-renders without a close/reopen cycle.

3. **SSH credentials panel** -- `topology/topology-ssh-dialog.js`:
   - New amber banner `#ssh-post-delete-banner` above the "Auto-clear host
     key on connect" row. Shown only when
     `sshConfig._postDeleteClearHostKey === true` AND the timestamp is within
     a 4 h TTL.
   - Banner copy spells out which NCC was active, when the delete ran, and
     announces that the auto-clear checkbox has been enabled.
   - `_renderPostDeleteHint()` auto-checks `#ssh-clear-hostkey` and frames
     the checkbox in amber; it tracks this with
     `panel._postDelHintAppliedAutoCheck` so a later `_dismissPostDeleteHint`
     reverts the checkbox if the operator never confirmed with Save.
   - Dismiss (the `&times;` button) clears the `_postDelete*` fields and
     reverts the checkbox to the saved `_autoClearHostKeys` value.
   - After the cluster probe renders the NCC rows, the dialog finds the row
     matching `_postDeleteActiveNccId` (with VM-name fallback) and
     highlights it in amber + sets `panel._selectedMethod = 'ssh_ncc'`. The
     `ssh-probe-method` rows now carry `data-ncc-index` + `data-ncc-vm` to
     make this match robust.
   - `saveAddress()` folds `_postDeleteMgmtIp` + `_postDeleteActiveNccVm`
     into the alias set passed to `/api/ssh/clear-hostkey`, then on a
     successful clear calls `_dismissPostDeleteHint({persistAutoCheck:true})`
     so the hint doesn't resurrect on the next panel open.

**Scope guard.** Only `delete_deploy` upgrades set `suggest_clear_host_key`.
`gi_deploy` and `normal` paths don't wipe the host key, so they don't stamp
the hint.

**User-visible result.**

- Start a delete+deploy upgrade on a cluster device. The moment the backend
  begins `request system delete`, the device's SSH credentials panel (whether
  currently open or opened later) shows an amber banner naming the exact
  NCC whose host key will rotate. The auto-clear checkbox is pre-ticked.
- Open the panel, hit Save -> `ssh-keygen -R` runs for every alias (user
  host, `_activeNccHost`, `_activeNccIp`, ...plus the pre-delete mgmt IP and
  NCC VM name). Connection proceeds without the stale-key warning.
- Click Dismiss on the banner if the operator wants to accept the stale
  warning manually; checkbox reverts, flag clears, no mystery state carries
  over.

**Files touched:**

- `topology/routes/upgrade.py` -- capture + publish pre-delete NCC
- `topology/scaler-gui-progress.js` -- stamp `sshConfig._postDelete*` in
  `renderDeviceState`; expose `window.refreshSSHDialogPostDeleteHint`
- `topology/topology-ssh-dialog.js` -- banner markup, renderer, dismiss,
  alias fold-in, NCC row pre-select, `data-ncc-index` / `data-ncc-vm`

**Cache busters bumped:** `topology-ssh-dialog.js?v=20260419a` +
`scaler-gui-progress.js?v=20260419a`.

---

### 2026-04-21 Follow-up: SSH credentials dialog viewport clamping + scroll polish

**Operator report.** "The SSH panel from the credentials button (not the
connection button) is partially out of screen and should be scrollable for
better UX."

**Root cause.** The SSH credentials dialog is anchored to the canvas device
it was opened on -- `left: deviceScreenX`, `top: deviceScreenY + radius + 20`,
`transform: translateX(-50%)`. The pre-existing positioning code had two
holes:

1. The vertical fallback `const _dialogTop = Math.min(deviceScreenY +
   deviceRadius + 20, window.innerHeight - 80)` clamped only the **top**
   to 80 px off the bottom edge, but the panel itself can grow up to
   `100vh - 40px` tall. A panel whose top sits at `innerHeight - 80`
   therefore extends hundreds of pixels below the viewport.
2. The horizontal anchor (centre-on-device) never checked that
   `deviceScreenX ± halfWidth` actually fit inside the viewport.
   Right/left-edge devices rendered dialogs partly off-screen.
3. The existing post-render `requestAnimationFrame` correction handled
   the common below/right overflow but had no final hard clamp -- a
   device panned outside the viewport (negative or >innerHeight device
   coordinates) could still yield an off-screen top even after the
   "try above" branch.

**Fix (`topology/topology-ssh-dialog.js`):**

1. **Pre-render estimate block.** Before the fade-in animation starts,
   compute a conservative first guess using `_estWidth = 420` (matches
   `max-width`) and `_estHeight = min(640, innerHeight - 24)`. Horizontal
   clamp keeps the panel's visual centre within
   `[halfW+pad, innerWidth-halfW-pad]` so `translateX(-50%)` produces a
   left edge inside the viewport. Vertical logic prefers below the
   device, falls back to above, then to the top margin, and finally
   runs a hard `Math.max(pad, Math.min(top, innerHeight - height - pad))`
   clamp -- so even a device panned above or below the viewport still
   spawns the dialog on-screen.
2. **Panel `max-height` tightened** from `calc(100vh - 40px)` to
   `calc(100vh - 24px)` to match the new viewport padding. Added
   `overscroll-behavior: contain` so scroll wheel inside the panel
   never bubbles out to the canvas.
3. **Post-render clamp refactored** into a named helper
   `clampPanelToViewport()` that measures the actual panel rect and:
   - re-clamps `left` horizontally using the real half-width;
   - shrinks `max-height` if the panel is taller than
     `innerHeight - 2*padding`;
   - re-applies the below -> above -> top-margin fallback;
   - **ends with a hard `min/max` clamp** so no branch can leave the
     panel off-screen.
4. **Window resize listener.** `_onResize = () => clampPanelToViewport()`
   is attached to `window` and removed by the existing
   `_cleanupListeners` (the single teardown path, wired to the close
   button, outside-click, and Escape-key handlers). Resize the browser
   while the dialog is open and it re-settles inside the viewport.

**User-visible result.**

- The SSH credentials panel always fits fully inside the viewport on
  both axes, regardless of where the device lives on the canvas.
- When content exceeds the viewport height, internal scroll engages
  (`overflow-y: auto`) with the existing thin custom scrollbar.
- Resizing the browser window while the panel is open keeps it on
  screen (snaps to the closest valid position).

**Bug also fixed in the same bump.** `topology-ssh-dialog.js?v=20260421g`
threw `ReferenceError: device is not defined` inside `_showMacIpPrompt`
because the function signature never declared `device` but the retry
handler referenced it. The 2026-04-21n refactor made it a proper
parameter (`targetDevice`) and the call sites pass `device` explicitly;
the user hit the error because their browser was still caching the old
file.

**Cache buster bumped:** `topology-ssh-dialog.js?v=20260421o`.

---

### 2026-04-21 Follow-up: Ghost-IP cluster recovery fallback + mgmt-IP staleness detection

**The gap.** After the 2026-04-20 reaper fired for `YOR_CL_PE-4`, subsequent
SSH clicks produced a ghost-IP warning + an SSH dialog asking the user to
re-discover the mgmt IP. But the device was a cluster in deep recovery
(NCC0 sitting in baseos bash shell -- no DNOS, no mgmt0 interface at all).
The user had no way to know any new IP. The only working path was the
virsh console via the KVM host, but the ghost-IP branch never offered it.

**The fix (`topology/topology-object-detection.js :: openTerminalToDevice`)**:

1. **Mgmt-IP-reaped detection.** After `getDeviceContext()` returns, we
   also check `ctx.identity.mgmt_ip`. If it's empty on a cluster device, we
   set `_mgmtIpReaped = true`. The existing `_isGiOrShell` gate now also
   fires on this flag, so the code takes the existing virsh-console path
   instead of the iTerm fast-path -- even when `device_state` is the stale
   cached `"DNOS"`. This unblocks the whole chain before we ever hit
   `verifyDeviceIdentity`.

2. **Ghost-IP cluster fallback.** The ghost-IP branch inside
   `verifyDeviceIdentity` handling now:
   - Reuses `sshConfig._virshInfo` if present.
   - Otherwise calls `ScalerAPI.probeConnection(device.label, '')` to
     rediscover the virsh entry (the probe resolver gracefully degrades
     on reaped devices and still returns virsh + NCC creds).
   - Opens `window.TerminalPanel` with `method: 'virsh_console'`, passing
     `kvmHost`, `kvmUser`, `kvmPass`, `nccVms`, `activeNcc`.
   - Fires `_fireBackgroundNccDiscovery` so the backend keeps polling for
     a new mgmt IP while the user works in the console.
   - Shows a warning toast: `[GHOST IP] <device>: <ip> now belongs to
     "<actual>". Opened virsh console on <kvmHost> (NCC <ncc0>).`
   - Only falls back to the legacy SSH dialog when no virsh info can be
     discovered (non-cluster or fully unreachable KVM).

**Why this works for PE-4 and similar.** Even if every IP in the scaler
DB is stale, as long as we know the KVM host serial or IP and the NCC VM
name (both come from `connection_strategy._derive_kvm_host` + the scaler
inventory), virsh console rides the same HTTPS channel the user is
already using. The operator can watch the install finish, start DNOS
manually, or verify state without chasing IPs.

**Cache busters bumped:** `topology-object-detection.js?v=20260421h`.

**Files touched + synced to `/home/dn/CURSOR/`:**
`topology/topology-object-detection.js`, `topology/index.html`.

**Files touched + synced to `/home/dn/CURSOR/`:** `topology-ssh-dialog.js`,
`topology-terminal.js`, `topology-object-detection.js`, `scaler-api.js`,
`serve.py`, `index.html`, `routes/ssh.py`, `routes/bridge_helpers.py`.

**Operational note.** After editing `serve.py` proxy rules the running
process must be restarted (it has no hot-reload). `scaler_bridge` runs
under `uvicorn --reload` and picks up route changes automatically.

**Self-test coverage.** `_identity_matches` covers the PE-4 vs
R7-Natan_SIT case, aliased hostnames (`PE-1` vs `YOR_PE-1`),
cfg-mode prompt tails (`PE-1(cfg)#`), KVM hosts (`dn@kvm108:~$`), the
tricky `PE-14 != PE-4` boundary, and the empty-actual-hostname case
(no false alarm). See the test block in commit / session notes.

**Operator-facing behaviour.**
- After an upgrade releases the IP, the very first SSH click triggers the
  guard, closes the bogus session, wipes the stale record on disk,
  clears the canvas `sshConfig.host`, and shows a warning toast.
- The second SSH click opens the SSH dialog fresh with no host pre-filled,
  so the user is nudged into re-discovery (Probe / Discover Console) or
  into typing the new IP.
- The scaler CLI library sees the reaped `devices.json` row and also
  re-discovers instead of dialling the ghost host.

## Per-User Device Maintenance + Shared Event Bus (2026-04-20)

**What changed.** Device maintenance (ghost-IP reaps, mgmt-ip updates,
cluster-state changes, manual notes) used to be a single-user, fire-and-
forget affair. Now it is explicitly **per-user** with a **shared event
bus** so multiple users watching the same device see each other's
actions in real time -- without leaking private state between users.

**Architecture (backend).**
- **`api/device_state.py`** -- SQLite store at
  `~/.topology_users/_device_state.db` with three tables:
  - `watchers`: `(device_id, username, topology_id, canvas_ip,
    last_seen_at)`. A row means "user X has this device on their
    current canvas". Rows older than `WATCHER_IDLE_TTL_SECONDS`
    are pruned on the next heartbeat or read.
  - `events`: append-only audit trail of every maintenance action
    (type, device_id, actor_user, payload JSON, timestamp).
  - `user_prefs`: per-user per-device JSON blob, shallow-merged on
    write so partial updates don't clobber unrelated keys.
- **`api/event_bus.py`** -- in-process async WebSocket broker.
  `subscribe(username, ws)` joins the user's channel; `publish_to_
  device_watchers(device_id, event_type, payload)` fans an event to
  every currently-subscribed watcher. `publish_to_device_watchers_
  sync()` is the thread-safe variant used from uvicorn's sync
  threadpool (the main loop is captured on the first subscribe so
  `run_coroutine_threadsafe` works from worker threads).
- **`routes/events.py`** -- the HTTP + WebSocket surface:
  - `POST /api/devices/{id}/watch` -- explicit register.
  - `POST /api/devices/{id}/unwatch` -- explicit deregister.
  - `POST /api/devices/watch-heartbeat` -- bulk refresh (body
    `{device_ids: [...]}`); returns `{added, kept, pruned,
    active_count}`.
  - `GET  /api/devices/{id}/watchers` -- who else is watching this
    device (social info -- any authenticated user can read).
  - `GET  /api/devices/watched` -- my own watcher rows.
  - `GET  /api/devices/{id}/events` -- polling fallback for the WS.
  - `GET  /api/devices/events/recent` -- cross-device activity feed
    scoped to devices the caller watches.
  - `GET/PUT /api/devices/{id}/user-prefs` -- per-user per-device
    JSON blob.
  - `WS /api/events/ws?token=<JWT>` -- long-lived bus for the user.
  - `GET /api/events/status` -- admin-visible diagnostic snapshot
    (total connections, connected users, recent events).
- **`routes/bridge_helpers.py :: _mark_device_ip_stale`** now takes
  `acting_user=<str>`, writes an audit row under the canonical
  device id, and calls `event_bus.publish_to_device_watchers_sync()`
  for every known alias of the device (canvas label + canonical
  scaler hostname) so watchers keyed on different names all receive
  the broadcast.
- **`routes/ssh.py :: /api/ssh/clear-ghost-ip`** enforces the
  permission rule: **only admins OR active watchers of the device
  may trigger a reap.** Non-admin non-watchers get HTTP 403. The
  acting username is threaded through from `request.state.user`.
- **`scaler_bridge.py`** startup hook captures the main asyncio loop
  and passes it to `event_bus.attach_loop()` so thread-safe
  broadcasts work even before the first WS subscribe.

**Architecture (frontend).**
- **`topology-device-events.js`** (new) -- per-user WS client.
  Auto-starts on `topology:auth-login`, stops on
  `topology:auth-logout`. Exposes `window.TopologyDeviceEvents`:
  - `start() / stop() / status()` -- WS lifecycle.
  - `setWatchedDevices(ids, {topologyId})` -- replace the watcher
    set. First non-empty flush is synchronous (closes the race
    between canvas load and first user click); subsequent flushes
    are debounced at 500ms. 30s HTTP + WS heartbeat keeps rows
    fresh.
  - `addWatchedDevice(id) / removeWatchedDevice(id)` -- delta
    updates wired into canvas mutations (create / delete / drag).
  - Incoming `{type: "event", event: {...}}` frames are
    re-dispatched as `window` `CustomEvent`s:
    - `topology:event` (generic)
    - `topology:event:<type>` (specific, e.g.
      `topology:event:ghost_ip_reaped`)
    - `ssh:ghost-ip-detected` (legacy field-name shim so existing
      listeners keep working -- includes `deviceId, ip, actual,
      actorUser` and `source: 'broadcast'`).
  - Coexists with the in-app `TopologyEventBus` from
    `topology-events.js` -- they are two different buses: one for
    module-to-module pub/sub inside a single tab, one for cross-
    user device state. `window.TopologyEvents` is an alias that
    layers the watcher helpers onto whichever instance loaded first.
- **`topology.js :: _syncCanvasWatchers()`** -- called after
  topology load, device add, and device delete. Walks
  `editor.objects`, extracts device-like labels, and calls
  `TopologyDeviceEvents.setWatchedDevices(ids, {topologyId})`.
  This is the only place a user gets auto-registered as a watcher.
- **`topology-ssh-dialog.js`** -- legacy `ssh:ghost-ip-detected`
  handler enhanced to accept `source: 'broadcast'` events (reaps
  done by *other* users on devices I watch). Maps the new payload
  shape to the legacy field names, clears canvas sshConfig slots as
  before, and shows a distinct toast ("<actor> cleared ghost IP on
  <device>") so the user knows it was somebody else.

**Permission matrix.**

| Action | viewer | engineer | team_leader | admin |
|---|:-:|:-:|:-:|:-:|
| See own watched devices | yes | yes | yes | yes |
| See who else watches a device | yes | yes | yes | yes |
| Reap ghost IP on a device I watch | yes | yes | yes | yes |
| Reap ghost IP on a device I do NOT watch | no | no | no | yes |
| See all connections / recent events | no | no | no | yes |
| Read another user's per-user prefs | no | no | no | no |

**Event payload shape (on-the-wire WS frame):**
```
{
  "type": "event",
  "event": {
    "type": "ghost_ip_reaped",
    "device_id": "PE-1",
    "payload": {
      "scaler_id": "PE-1",
      "cleared_ip": "10.0.0.9",
      "actual_hostname": "R7-Natan_SIT",
      "reason": "ghost_ip",
      "marked_stale_at": "2026-04-20T16:40:12Z",
      "actor_user": "ido.koren",
      "event_id": 42,
      "aliases": ["PE-1", "YOR_CL_PE-1"]
    }
  }
}
```
Frontend reads `event.payload.actor_user` to distinguish
"self-initiated" from "another user did this on my canvas".

**Migration.** No data migration is needed -- the new tables start
empty and populate on demand. Existing single-user flows still work
unchanged because:
- `_get_request_user()` returns `"default"` when the JWT middleware
  is bypassed (`multiuser_enabled=False` mode), so watcher
  endpoints keep functioning in dev.
- `_mark_device_ip_stale(acting_user="")` silently falls back to
  `"system"` -- the reap still happens, the audit row is still
  written, broadcast goes to all watchers without an actor echo.
- The ghost-IP handler in `topology-ssh-dialog.js` accepts both
  old (local `CustomEvent`) and new (WS-broadcast) shapes via
  field-name fallbacks.

**Cache busters bumped:** `topology.js?v=20260420d`,
`topology-ssh-dialog.js?v=20260420c`,
`topology-device-events.js?v=20260420a`,
`scaler-api.js?v=20260420c`, `styles.css?v=20260420d`.

**Files touched + synced to `/home/dn/CURSOR/`:**
- JS/HTML: `topology-device-events.js` (new), `topology.js`,
  `topology-ssh-dialog.js`, `scaler-api.js`, `index.html`,
  `styles.css`.
- Python (backend): `api/device_state.py` (new),
  `api/event_bus.py` (new), `routes/events.py` (new),
  `routes/bridge_helpers.py`, `routes/ssh.py`, `scaler_bridge.py`,
  `serve.py` (proxy rules).

**Operational notes.**
- `serve.py` (port 8080) has no hot-reload; restart the
  `topology-app.service` systemd unit after touching proxy rules.
  `scaler_bridge` (port 8766) runs under `uvicorn --reload`.
- The **browser WS** connects **same-origin through serve.py** (port
  8080) via `ScalerAPI.getBridgeWebSocketOrigin()`, which now returns
  `ws://<page-host>:<page-port>`. serve.py then tunnels the upgrade
  to `scaler_bridge:8766`. This works on both localhost and CGNAT
  remote-access (where port 8766 is firewalled off).
  - Proxy helper: `HttpRequestHandler._proxy_websocket(host, port)` +
    `_is_websocket_upgrade()` in `serve.py`. The dispatch in `do_GET`
    matches three upstream WS paths before any other routing:
    `/api/events/ws`, `/api/terminal/ws`, `/ws/progress/<job_id>`.
  - Handshake is forwarded verbatim (`Host` rewritten); afterwards
    `select()` shuffles raw frames bidirectionally until either side
    closes. `ThreadedHTTPServer` keeps each tunnel in its own daemon
    thread so idle loops never block other clients.
  - Client retry cap (2026-04-22): `topology-device-events.js` stops
    reconnecting after 5 consecutive failed attempts, logs one line,
    and exposes `window.TopologyDeviceEvents.resume()` as the manual
    re-arm. Prevents devtools spam when the server is unreachable.
  - Legacy direct `:8766` access still works if you explicitly set
    `ScalerAPI.baseUrl = "http://host:8766"` -- the resolution order
    is: explicit baseUrl wins, else same-origin.
- `~/.topology_users/_device_state.db` is the single shared store.
  Back it up if you need to preserve audit history across rebuilds;
  otherwise it is safe to `rm` -- watcher rows are recreated via
  heartbeats and events lose their history but not their effect.

**Self-test coverage.** `/tmp/ws_smoke_final.py` runs 10 checks
across two real users (`admin` + `ido.koren`):
1. Both users register as watchers via the proxy API.
2. Admin WS receives `ghost_ip_reaped` broadcast.
3. Actor's own WS receives the echo.
4. Event carries `actor_user` in payload.
5. Polling fallback `/events` returns the reap.
6. Non-watcher reap is forbidden (HTTP 403) for non-admins.
7. Admin override reap succeeds without a watcher row.
8. Per-user prefs isolation: admin sees own note.
9. Per-user prefs isolation: non-admin does NOT see admin's note.
10. `/unwatch` drops the row from the watcher list.

## Shared Indicator in the Topologies Dropdown (2026-04-20)

Extended the existing "Topologies" dropdown (`#topologies-dropdown-menu`,
rendered in `topology-file-ops.js`) with **share-state icons** mirroring the
look-and-feel of the lock badge already shown on the `BUGS` domain. Two
distinct visuals:

| Icon                                    | Meaning                                    | Tooltip pattern                          |
|-----------------------------------------|--------------------------------------------|------------------------------------------|
| Three-circle "broadcast" badge          | I own this and shared it OUT               | `Shared with <user1>, <user2>, ...`      |
| Downward-arrow "inbox" badge + `SHARED` | Owned by someone else, shared IN with me   | `Shared by <owner>(read|write)`          |

**Data sources.** Legacy `/api/sections` (per-user local sections) has no
sharing metadata, and multi-user `/api/domains` has all of it. The dropdown
must render both in one list, so `FileOps` keeps a TTL-cached **sharing
index** built from `window.TopologyDomains.getDomains()` plus
`/api/domains/share/files/outgoing`:

- `_refreshSharingCache(force)` -- TTL-guarded fetch (15s window, bypassed with
  `force=true`). Swallows errors and keeps the last good snapshot.
- `_buildSharingIndex()` -- returns `{ domains, domainsByName, domainsById,
  outgoingFilesByKey, incomingFiles, incomingFilesByTopoId }`. `outgoingFilesByKey`
  is keyed by `${domainId}|${sanitizedFilename}` so per-file shared-out badges
  are a single hash lookup during row render.
- `_sanitizeTopologyBasename(name)` -- normalises legacy display names to
  match stored filenames (lowercase + strip weird characters).
- `_findOwnDomainForSection(sec, sharingIndex)` -- bridges legacy section
  names to their multi-user domain counterparts (case-insensitive).

**Render hooks** (all in `topology-file-ops.js`):
- `_renderCustomSectionsInDropdown()` adds the shared-out badge next to
  **own** sections when the matched domain has a non-empty `shared_with[]`.
- `_renderTopoEntries()` adds either the shared-out badge (when
  `outgoingFilesByKey` returns a hit for `<domainId>|<sanitizedFile>`) or
  the shared-in badge (when the row was received via a shared-in domain or
  the per-file inbox).
- `_renderSharedInSectionsInDropdown()` (NEW) appends one virtual row per
  domain shared WITH me (`is_shared && !is_shared_with_me_domain`) plus one
  extra virtual row for the synthetic `__shared_with_me` per-file inbox
  (only when it has content). Both rows carry a purple accent (`#a78bfa`),
  a `SHARED` pill, and their own owner tooltip, and load their topologies
  via `/api/domains/{id}/topologies` through
  `_loadSharedInDomainTopologiesInline()`.

**Write-protection on shared-in rows.** Rename and delete are disabled on
shared-in topologies with a toast warning; this prevents `403` responses
from `/api/domains/.../topologies/{file}` (the domain owner keeps exclusive
rename/delete rights).

**Refresh lifecycle.**
- `loadCustomSections(editor)` now awaits `_refreshSharingCache()` before
  calling `_renderCustomSectionsInDropdown()`, so the first open after sign-in
  already has the right badges.
- Opening the dropdown (`#btn-topologies` handler in `topology.js`) kicks a
  background `TopologyDomains.fetchDomains()` + `_refreshSharingCache(true)`;
  the dropdown re-renders asynchronously when the cache settles.
- `TopologyDomains.fetchDomains()` now emits `topology-domains:changed`
  (previously only `selectDomain/init` did). `topology-file-ops.js` has a
  module-level listener that re-refreshes its sharing cache and re-renders,
  so sharing actions from the Share Topology dialog update the Topologies
  dropdown without a page reload.

**SVG helpers.** `_sharedOutIconHtml(color, tooltip)` draws three connected
nodes with an outgoing arrow; `_sharedInIconHtml(color, tooltip)` draws the
same three nodes with an incoming arrow. Both accept any hex tint so the
badge blends with the section's accent colour while staying contrast-safe
in dark mode.

**Cache busters bumped:** `topology-domains.js?v=20260420c`,
`topology-file-ops.js?v=20260420c`, `topology.js?v=20260420c`. Updated in
`topology/index.html` AND synced to `/home/dn/CURSOR/`.

**Files touched + synced to `/home/dn/CURSOR/`:** `topology-file-ops.js`,
`topology-domains.js`, `topology.js`, `index.html`.

## Legacy <-> Multi-user Bridge for Shared Topologies (2026-04-20)

Problem solved: clicking "Share" on a topology that lives only in the legacy
`/api/sections/<sid>/<file>.json` store returned **404 "Topology not found"**
because the share endpoint
(`/api/domains/<domain_id>/topologies/<topology_id>/share`) only knows about
rows in the multi-user SQLite DB -- it rejects bare legacy filenames. We now
migrate the file into the multi-user DB on first share and mirror every
subsequent owner write so recipients always see the latest.

### Architecture summary

- **Canonical copy = multi-user DB.** After the first share, the shared view
  is backed by a row in the owner's `~/.topology_users/<owner>/topologies.db`
  `topologies` table. Legacy files stay on disk but are a convenience mirror
  for the owner's local UI.
- **Write permission enforcement stays where it was** --
  `user_store.save_topology` still raises `PermissionError` for recipients
  without `write`, see
  [topology/api/auth/user_store.py](topology/api/auth/user_store.py) ~line
  526. Mirror-on-save runs as the OWNER, so it always succeeds.
- **Per-user, per-section mapping file:**
  `~/.topology_users/<user>/sections/_multiuser_mirror__<section_id>.json`
  maps `<filename.json>` -> `{domain_id, topology_id}`. Best-effort:
  missing/corrupt falls back to legacy-only behaviour silently.

### Frontend: migrate-on-share

`FileOps._ensureLegacyTopologyMigrated(editor, sectionId, section, topoFilename)`
in [topology/topology-file-ops.js](topology/topology-file-ops.js):

1. Refresh domains, look for a multi-user domain whose name matches the
   legacy section name. Create it via `TopologyDomains.createDomain` if
   absent.
2. `GET /api/domains/<did>/topologies`, return early if a topology with the
   same name is already there (idempotent on repeat share).
3. Read the legacy JSON (`/api/sections/<sid>/topologies/<safe>.json`, tries
   both the raw and sanitized filename) and `POST` it via
   `TopologyDomains.saveTopology(name, data, domain.id)` -- the server
   assigns a UUID.
4. Returns `{ domain, topology, created }`.

The `.ta-share` click handler in `_renderTopoEntries()` now:

```js
const migrated = await FileOps._ensureLegacyTopologyMigrated(
    editor, opts.sectionId, opts.section, topoFilename
);
await window.TopologyDomains.fetchDomains(true);
await fetch('/api/sections/<sid>/_mirror-register', {
    method: 'POST',
    body: JSON.stringify({
        filename: topoFilename,
        domain_id: migrated.domain.id,
        topology_id: migrated.topology.id,
    }),
});
window.TopologyShare.openForDomain(migrated.domain.id, migrated.topology.name, anchorEl);
```

The mandatory refresh lets `_findDomainByHint` + `_lookupTopology` in
`topology-share.js` resolve to the real UUID pair, so the subsequent share
POST hits a valid row (no more 404).

### Backend: mirror helpers + endpoints

All in [topology/serve.py](topology/serve.py):

- `_mirror_map_path / _mirror_read_all / _mirror_write_all / _mirror_get /
  _mirror_set / _mirror_clear / _mirror_clear_section` -- file-level
  primitives.
- `_mirror_user_store()` -- lazy-imports the `UserStore` singleton so
  `serve.py` stays importable if the api package fails.
- `POST /api/sections/<sid>/_mirror-register {filename, domain_id,
  topology_id}` -- called by the frontend after migration.
- `POST /api/sections/<sid>/save` -- after writing the JSON file, does
  `user_store.save_topology(user, m.domain_id, name, topo,
  topology_id=m.topology_id)` when a mapping exists.
- `POST /api/sections/<sid>/topologies/<fname>/rename` -- clears old
  mapping, re-registers under the new filename, calls
  `user_store.rename_topology`.
- `POST /api/sections/<sid>/topologies/<fname>/delete-file` -- calls
  `user_store.delete_topology` (cascades share rows) + `_mirror_clear`.
- `POST /api/sections/<sid>/delete` -- iterates the mapping, deletes each
  mirrored topology, then deletes the multi-user domain if it was
  auto-created AND has no remaining topologies, then removes the mapping
  file.

### New user_store method

[topology/api/auth/user_store.py](topology/api/auth/user_store.py) now has
`rename_topology(username, domain_id, topology_id, new_name)` -- a
single `UPDATE topologies SET name=?, updated_at=? WHERE id=? AND
domain_id=?`. Refuses renames of the synthetic "Shared with me" domain.

### What this does NOT do

- **No true realtime collab.** Multiple users still can't drag the same
  device at the same time; there's no Yjs/CRDT/WebSocket-push layer.
  Recipients see the owner's changes on their NEXT fetch (page reload,
  dropdown open -> refresh). If push-without-reload is needed later, layer
  it on top of this mirror (poke open tabs to pull, no data-model change).
- **No conflict resolution.** Owner's legacy save always overwrites the
  mirror. Recipient writes go through `/api/domains/.../save` which is the
  canonical path -- those take effect immediately on the owner's view too.

### Cache buster bumped

`topology-file-ops.js?v=20260420d` in `topology/index.html`.

### Files touched + synced to `/home/dn/CURSOR/`

- `topology-file-ops.js` (migrate-on-share wiring, register POST call)
- `index.html` (cache buster)
- `serve.py` (mirror helpers + mirror-on-save/rename/delete/delete-section
  + `_mirror-register` endpoint)
- `api/auth/user_store.py` (new `rename_topology` method)

---

## Legacy<->Multi-user Bridge: Responsive UX Polish (2026-04-20 pt.2)

The base bridge above works end-to-end but the share button had silent
waits, no double-click guard, no conflict detection, no realtime push to
recipients, and stale-badge TTL made outgoing share icons appear up to 30 s
after a share. This pass addresses all five gaps so the flow feels smooth
across any-to-any share paths.

### 1. Share button spinner + double-click guard

`topology/topology-file-ops.js` in the `.ta-share` click handler:

- `shareTopoBtn.dataset.working === '1'` short-circuits repeat clicks.
- Swap the three-circle SVG for `FileOps._inlineSpinnerHtml(color)` (reuses
  the global `@keyframes spin` already declared in `topology/index.html`).
- `finally {}` restores the original icon and re-enables the button
  regardless of success, error, or migration path early-return.

This kills the 200 ms - 2 s silent wait on first share of a legacy file
(three migration roundtrips) and prevents a parallel second click from
spawning a second migration.

### 2. Immediate badge refresh (no 30 s TTL wait)

Post-migration the click handler explicitly calls
`FileOps._refreshSharingCache(true)` and re-runs
`FileOps._renderCustomSectionsInDropdown(editor)` so the outgoing-share
icon appears instantly on the owner's Topologies dropdown. The existing
`topology-domains:changed` listener (file-ops.js ~line 3696) already
force-refreshes downstream whenever `fetchDomains()` runs, so the second
half of the chain was already in place.

### 3. Mirror-register retry + operator toast

`FileOps._mirrorRegisterWithRetry(sectionId, filename, domainId,
topologyId)` retries the POST with 150 ms / 400 ms / 1 s backoff (3
attempts). If all three fail the click handler shows a warning toast:

> Share will work, but save-sync is offline (mapping could not be saved
> server-side). Re-share this file to retry.

This is critical because `_mirror-register` persistence is load-bearing:
without it, future owner saves wouldn't know to mirror, and recipients
would silently stop getting updates.

### 4. Stale-save detection (409 + reload-prompt)

Backend (`serve.py`, `POST /api/sections/<sid>/save`): when the file has
a mirror mapping, look up the multi-user row's `updated_at` via the new
`user_store.get_topology_meta(user, domain_id, topology_id)` (returns
`{id, name, updated_at, object_count, ...}` without the full JSON blob).
Compare with the local disk `mtime` (5 s skew tolerance for the tick
between our own disk write and our own mirror-save). If the DB is
meaningfully newer, refuse the save with `409` and a body of:

```json
{
  "error": "This topology was updated by another user ...",
  "conflict": true,
  "current_updated_at": "2026-04-20T...",
  "filename": "foo.json"
}
```

The client opts out with `{"force": true}` in the request body to
overwrite intentionally. The save response now also carries
`mirror_updated_at` so clients can track freshness.

Frontend: `FileOps._sectionSaveWithConflict(editor, sectionId, body,
onSuccess)` wraps `/api/sections/<sid>/save` and renders
`FileOps._showStaleSaveBanner` on 409 -- a sticky top banner with a
warning triangle, the relative "updated Xs ago" timestamp, and three
buttons: **Reload**, **Save anyway** (re-issues with `force: true`), and
a close X. Wired into `FileOps._cmdSave` which is the primary Ctrl+S
path. Other save call sites still show the generic toast on failure;
that's acceptable because they're rare edge cases.

### 5. SSE realtime push for recipients

New long-lived event stream so recipients see owner edits without F5:

- **Module-level pub-sub in `serve.py`**: `_sse_subscribers: Dict[str,
  List[queue.Queue]]`, guarded by `_sse_lock`. Each open tab gets its
  own `queue.Queue(maxsize=64)` keyed by username. Full queues drop
  events (the client self-heals on reconnect).
- **Endpoint**: `GET /api/topologies/events` (handled by
  `_handle_sse_topology_events`). Accepts auth via `Authorization:
  Bearer` OR the query-string `?token=<jwt>` fallback (because
  EventSource can't send custom headers). Streams `event:
  topology-updated\ndata: <json>\n\n` frames with 15 s heartbeat
  comments to keep intermediaries from timing out.
- **Publisher helper**: `_sse_publish_mirror_event(owner, mapping, kind,
  extra)` resolves recipients via the new
  `user_store.list_topology_recipients(owner, domain_id, topology_id)`
  method and fans out to the owner plus every recipient. Invoked from
  mirror-on-save, mirror-on-rename, mirror-on-delete-file, and
  mirror-on-delete-section (the delete-section path publishes BEFORE
  calling `delete_topology` so the share rows still exist when we
  resolve recipients).
- **Event payload**: `{kind, owner, domain_id, topology_id, at, ...}`
  plus kind-specific extras (`name`, `new_filename`, etc).

Frontend (`topology-file-ops.js`, IIFE appended after the
`topology-domains:changed` listener):

- Opens `EventSource('/api/topologies/events?token=<jwt>')` on login.
- On `topology-updated`, force-refreshes domains
  (`fetchDomains(true)`) which cascades into the dropdown re-render via
  the existing listener chain.
- Rate-limited toast (1 per 5 s) so a burst of saves doesn't spam the
  recipient:

  > Shared topology "foo.json" updated by yarel

- Exponential backoff reconnect (1s, 2s, 4s, capped at 30s).
- `window._topologyEventsStatus()` debug helper returns current state.

**Known gap (intentional):** recipient writes via the FastAPI
`/api/domains/.../topologies/...` path run in the scaler_bridge process,
which has its own memory space, so those writes do NOT currently reach
serve.py's `_sse_subscribers`. The main flow the bridge cares about
(owner-legacy -> recipient) is fully covered. If recipient->owner
realtime is needed later, the cheapest fix is a thin webhook: add
`POST /api/_internal/topologies/event` on serve.py (localhost-only),
and have scaler_bridge fire-and-forget POST to it from its save /
rename / delete handlers.

### Files touched + synced to `/home/dn/CURSOR/`

- `topology-file-ops.js` -- spinner, retry helper, stale-save wrapper +
  banner, SSE client IIFE.
- `serve.py` -- stale-save guard, SSE pub-sub infrastructure,
  `/api/topologies/events` endpoint, `_sse_publish_mirror_event` calls
  in every mirror-on-\* path.
- `api/auth/user_store.py` -- new `get_topology_meta` and
  `list_topology_recipients` methods.
- `index.html` -- cache buster bumped `20260420d` -> `20260420e` on
  `styles.css`, `topology-file-ops.js`, `topology.js`.

### Running verification

```bash
# health still ok
curl -s http://localhost:8080/api/health

# SSE endpoint rejects unauth (expected) with our new body
curl -s -X GET http://localhost:8080/api/topologies/events
# -> {"detail": "Authentication required for event stream"}

# stale-save: POST /api/sections/<sid>/save with
# {name, topology, force: false} after a recipient has written to the
# mirror returns HTTP 409 with {conflict: true, current_updated_at}.
# force: true overrides.
```

### Debugging tips

- Open the browser console and type `_topologyEventsStatus()` to see
  `{connected, readyState, lastEventAt, backoff}`.
- Server logs for SSE publish failures print with
  `[sse] list_topology_recipients failed: ...` -- safe to ignore if the
  share row was just deleted.
- Stale-save false positives are guarded by 5 s skew; if you see them
  on single-user use cases, check your system clock drift.

## 2026-04-20 F — Share click "flap" fix (cache buster e -> f)

**Symptom:** clicking the per-file Share icon made the topologies
dropdown visibly flap (contents rebuilt multiple times) and the share
popover never appeared.

**Root cause:** legacy -> multi-user migration fires `fetchDomains()`
2-4 times during the share click (once inside
`_ensureLegacyTopologyMigrated`, once in the click handler's old extra
refresh, and at least once inside `openForDomain`'s `_refreshAll`).
Each emit drives `topology-domains:changed`, whose listener calls
`_renderCustomSectionsInDropdown(editor)` -- which **replaces the
dropdown DOM**. The click-handler's `anchorEl` (and the legacy topo
row around it) gets detached between the await and `openForDomain`,
so `_findDomainRow` / `_findTopoRow` resolve to orphan nodes.
`_openTopoShareAt` then mounts the popover inside that detached
subtree and the user sees nothing.

**Fix (frontend only):**

- `FileOps._suspendDropdownRefresh` counter -- incremented in the
  share-click handler, decremented in `finally`.
- The `topology-domains:changed` listener in
  `topology-file-ops.js` skips re-rendering while the counter is
  non-zero, and also skips whenever a `.topo-share-form.open` or
  `.domain-share-form.open` element exists inside
  `#topologies-dropdown-menu` (protects the popover while the user
  is interacting with it).
- The click handler no longer calls `fetchDomains(true)` or
  `_refreshSharingCache(true).then(_renderCustomSectionsInDropdown)`
  eagerly; it only kicks one background `_refreshSharingCache(true)`
  in `finally` so the badge cache is warm the next time the
  dropdown rebuilds naturally (no DOM churn while the popover is
  open).

**Files:**

- `topology/topology-file-ops.js` -- click handler + listener guard.
- `topology/index.html` -- `topology-file-ops.js` cache buster
  bumped `20260420e` -> `20260420f`.

**Verification:**

1. Hard-refresh the topology page (Ctrl+Shift+R).
2. Open the topologies dropdown, hover a legacy file row.
3. Click the three-dot Share icon:
   - Spinner briefly replaces the icon, popover appears inline
     under the row within ~300 ms.
   - Dropdown no longer flashes.
   - Adding a recipient inside the popover does not close or
     rebuild the dropdown.
4. Closing the popover lets the next natural refresh (hover, open)
   redraw the outgoing-share badge.

---

## Topology sharing UX round 2 -- owner attribution, one-click stop-sharing, recipient self-removal, custom tooltips (Apr 20, 2026)

**Problem reported:**

1. The domain-level "SHARED" badge on shared-in copies was ambiguous --
   you couldn't see WHO shared a topology without hovering.
2. Own + shared-in domain rows drifted in color: some shared-in files
   rendered with the owner's original color, others with the purple
   shared-in accent.
3. No fast way for the owner to "stop sharing with everyone" -- they
   had to open the share popover and revoke user by user.
4. No way for the recipient to remove a received share from their own
   dropdown. Revoking had to go through the owner, even when the
   recipient just wanted to tidy up their own list.
5. All tooltips used the native `title` attribute, which has a ~1.5 s
   hover delay and no dark-mode styling.

**Fix:**

### Backend -- new recipient-self-removal endpoints

Added two idempotent POST routes so a target user can evict a share
from THEIR incoming view without touching the owner or any other
recipient:

- `POST /api/domains/share/files/incoming/{composite_id}/remove`
  deletes a single row from `topology_shares` where
  `composite_id = ? AND username = ?`. Leaves `shared_topologies`
  untouched so other recipients keep working, and so the owner can
  always re-share to the same user.
- `POST /api/domains/share/incoming/{domain_id}/remove` does the
  same for `domain_shares`, scoped to one whole shared-in domain.

Both call into new `user_store.remove_own_incoming_topology_share` /
`remove_own_incoming_domain_share` methods. Audit rows are written to
`share_activity` with `action = "remove_own_topology_share"` /
`"remove_own_domain_share"` so the owner can see in the history that
"alice removed her own access".

`TopologyMeta` and `_topology_meta_from_share` now expose
`composite_id` on inbox rows so the UI doesn't need to re-synthesize it
from `<owner>:<domain_id>:<topology_id>`.

### Frontend -- inline owner attribution, consistent colors

`_renderTopoEntries` in `topology-file-ops.js` now computes per-row
share state (isSharedIn, isSharedOut, owner, recipients, composite_id,
permission) ONCE, then:

- Shared-in rows render a small inline `by <owner>` span in purple
  next to the filename. Long display names truncate with ellipsis.
  Tooltip (both native + custom) preserves full "Shared by <display>
  (read) -- @username" text.
- Shared-out rows render a small inline `→ <recipient list>` span in
  the domain's color. Hover reveals the full list.
- Every shared-in row's border-left and badge color is locked to the
  single purple accent `#a78bfa`. Own domains keep their own color.
- File rows carry `data-*` attributes (`is-shared-in`, `is-shared-out`,
  `owner-username`, `owner-display`, `permission`, `composite-id`,
  `topology-id`) so downstream handlers don't have to re-query the
  sharing index.

Action-button set now branches on the share state:

- Owner + NOT shared -> Open, Rename, Duplicate, Share, Delete.
- Owner + shared-out -> adds an "unshare everyone" (`.ta-unshare-all`)
  button between Share and Delete. Confirms inline, then iterates
  every current recipient calling
  `POST /api/domains/<id>/topologies/<id>/unshare` serially so the
  audit log stays ordered.
- Recipient (shared-in) -> Open, Duplicate (copy into your own
  section), "Remove from my list" (`.ta-remove-mine`). Rename /
  Share / Delete are hidden because the backend rejects them.

### Frontend -- domain-level controls

Shared-in virtual domain titles (non-inbox) render a small `REMOVE`
pill next to the `SHARED` pill. Click shows an inline confirm bar
with a dark-mode-aware palette, then calls
`_removeIncomingDomainShare(section.id)` which posts to
`/api/domains/share/incoming/<id>/remove` and drops the virtual
section from the dropdown. The synthetic "Shared with me" inbox is
NOT removable (it's a virtual parent, not a share row).

The "SHARED" pill on shared-in domains is replaced with `BY <owner>`
so the originator is visible without hover. Inbox keeps `SHARED`
(multi-owner, so naming one would be misleading).

### Frontend -- custom hover tooltip helper

Factored the per-action-button tooltip code into a reusable
`FileOps._attachHoverTip(el, opts)` static. It:

- Reads either the `title` attribute OR `data-hover-title`.
- Temporarily removes `title` during hover so browsers don't render
  BOTH the native bubble and our styled one (double-tooltip glitch).
- Restores `title` on mouseleave so a11y tools still see it on the
  idle element.
- Skips re-binding (`dataset.hoverTipBound`) so calling it multiple
  times on the same node is safe.

Applied to:

- All `.ta-btn` action icons on file rows.
- `.topo-owner-inline` / `.topo-recipients-inline` inline texts.
- `.topo-shared-badge` wrapper around the shared-in/out SVG.
- `.dd-shared-in` handle SVG on shared-in domain titles.
- `.dd-shared-out` 3-circle SVG on own-domain titles.
- The `SHARED` / `BY X` pill + the `REMOVE` pill in shared-in titles.

For SVG badges the helper promotes the `aria-label` (or explicit text)
onto a `title` attribute since the `<title>` child doesn't work for
JS-driven tooltips.

**Files:**

- `topology/api/auth/user_store.py` -- new
  `remove_own_incoming_topology_share` /
  `remove_own_incoming_domain_share`.
- `topology/api/domains/router.py` -- new
  `/api/domains/share/files/incoming/.../remove` and
  `/api/domains/share/incoming/.../remove`, plus expose
  `composite_id` on inbox `TopologyMeta` payloads.
- `topology/api/schemas.py` -- added `composite_id: Optional[str]`
  to `TopologyMeta`.
- `topology/topology-file-ops.js` -- per-row share state,
  conditional action buttons, inline owner / recipient text,
  `_attachHoverTip` helper, `_unshareAllRecipientsForRow`,
  `_removeIncomingShareForRow`, `_removeIncomingDomainShare`,
  shared-in domain REMOVE pill + confirm bar, `BY <owner>` pill.
- `topology/index.html` -- `topology-file-ops.js` cache buster
  bumped `20260420f` -> `20260420h`.

**Verification:**

1. Hard-refresh the topology page.
2. As user A, share `topologyX` in domain `DomA` with user B.
3. As user B, open the topologies dropdown:
   - `DomA` renders under "Shared with me", purple border/accent.
   - Header says `BY ALICE` (pill) + `REMOVE` pill.
   - `topologyX` row shows the purple receive icon, the filename,
     inline `by Alice` text, "• 2s ago" timestamp.
   - Hover the "by Alice" text -- custom tooltip bubble appears
     immediately with "Shared by Alice (read) -- @alice".
   - Row actions on hover: Open + Duplicate + Remove-from-list only.
4. Click "Remove from my list" -> inline purple confirm -> Remove.
   Row disappears; if the section is now empty, "No shared
   topologies" placeholder shows.
5. As user A, on your OWN `DomA` dropdown row, a file shared with
   someone now shows the three-circle shared-out icon AND a new
   purple-X "Stop sharing" icon in the row actions. Click it ->
   confirm -> toast "Stopped sharing <file> with N users". Re-open
   the row; inline `→ bob` text is gone.
6. As user B, click `REMOVE` pill next to the `BY ALICE` title ->
   confirm -> virtual section vanishes from the dropdown.
7. Hover the outgoing-share 3-circle SVG on your own-domain title or
   the purple receive SVG on a shared-in title -> immediate styled
   bubble (not the 1.5 s native tooltip).

---

## Topology sharing UX round 2.1 -- drop inline owner text, fix recipient self-removal (Apr 20, 2026)

**Problem reported:**

1. The inline `by <user>` / `-> <recipient>` texts introduced in round 2
   were too chatty and pushed the timestamp + action buttons off-screen
   on narrow dropdowns. The badge icon + its tooltip is enough.
2. "Remove from my list" on a per-file row inside a shared-in domain
   (non-inbox) silently failed: the row briefly disappeared, then came
   back after the natural refresh. Same for "Remove this shared domain"
   on the domain header.

**Root cause:**

`/api/domains` rewrites shared-in `d.id` from the composite
`<owner>:<raw>` to just `<raw>` (so it matches the owner-side
topologies DB). But the central `shared_domains` / `domain_shares`
tables are keyed on the composite. The frontend was sending the raw
`section.id` to
`/api/domains/share/incoming/{id}/remove`, which never matched any
`domain_shares.domain_id` row. The endpoint returned
`{removed: false}` with a 200 status, so the frontend treated it as
success and dispatched a refresh. The refresh re-fetched the still-
present share from the server and the domain reappeared.

Per-file remove had the same class of bug: the synthesis fallback
(`section._sourceDomainId`) relied on
`/api/domains/share/incoming.original_domain_id` -- a field that
`TopologyDomainInfo` was dropping on the floor. So inside shared-in
domain sections `srcDomainId` was always null and
`_removeIncomingShareForRow` bailed with the "use the domain header
instead" toast.

**Fix:**

### Backend

- `TopologyDomainInfo` now exposes `original_domain_id: Optional[str]`
  (`topology/api/schemas.py`). `list_domains` in the router passes it
  through so shared-in rows carry both the raw id (`id`) and the
  original (`original_domain_id`) -- frontend can reconstruct the
  composite without a second roundtrip.
- `POST /api/domains/share/incoming/{id}/remove` now accepts EITHER
  the composite `<owner>:<raw>` OR the raw `<raw>`. If the raw form
  comes in the router looks at the caller's `list_incoming_shares()`
  and resolves a single `domain_id` match; if there are multiple (two
  owners sharing a domain with the same raw id to the same user) it
  returns 409 with a "pass the composite form" error.
- Both recipient-side remove endpoints now raise `404` when no share
  row matched the caller. Previously they returned 200 with
  `{removed: false}`, which the old frontend treated as success. The
  new, honest status code drives the real "Failed to remove" toast.

### Frontend

- `topology-file-ops.js::_renderTopoEntries` no longer renders the
  inline `by <owner>` / `-> <recipient>` spans. The share badge icon
  + its hover tooltip covers attribution; rows stay tight.
- `_removeIncomingShareForRow` falls back to `section.id` when
  `_sourceDomainId` / `_originalDomainId` are absent, so the composite
  synthesis works for both `/api/domains/share/incoming` and
  `/api/domains` (which set `id` and `original_domain_id` to the same
  value for shared-in rows). It also now checks the response body's
  `removed` flag alongside `resp.ok`, belt-and-suspenders for servers
  that haven't picked up the router change yet.
- `_removeIncomingDomainShare` takes the full `section` object
  instead of just `(sectionId, sectionName)`. It synthesizes
  `<owner>:<sectionId>` before posting, so the backend's central
  share tables find the row immediately. Honest error surfacing via
  the same `resp.ok || body.removed === false` check.

**Files:**

- `topology/api/schemas.py` -- `TopologyDomainInfo.original_domain_id`.
- `topology/api/domains/router.py` -- pass `original_domain_id` in
  `list_domains`; accept composite-or-raw in
  `remove_own_incoming_domain_share`; raise 404 on not-found.
- `topology/topology-file-ops.js` -- drop inline spans; fallback to
  `section.id` in per-file synthesis; reconstruct composite in
  `_removeIncomingDomainShare`; check `body.removed` on 200s.
- `topology/index.html` -- cache buster bumped `20260420h` ->
  `20260420i`.

**Verification:**

1. Hard-refresh as user B (a recipient).
2. Open the topologies dropdown. Shared-in rows show only the
   filename + share badge; no inline "by Alice" clutter.
3. Hover the purple receive badge -> custom tooltip reads "Shared by
   Alice (read) -- @alice".
4. Click "Remove from my list" on a file row inside a shared-in
   domain (NOT the inbox) -> confirm -> row disappears AND stays gone
   after the natural refresh fires.
5. Click the `REMOVE` pill on the shared-in domain title -> confirm
   -> whole virtual section vanishes and stays gone.
6. As user A, re-share the topology to user B. User B sees the row
   come back (confirms the owner side was untouched).

## Bug Topology -- Post-Create Canvas Sync + Visual Pass (2026-04-21a)

User-visible symptoms reported:

1. "The bug generation opens a new topology immediately, but the
   canvas of the previous one remains until switching to a third
   topology and then back."
2. "Topology generated should be visually descriptive without much
   text, only when absolutely needed."
3. "A background for the TB would be nice since it's a bit
   unreadable."

### Root cause of (1) -- wrong global reference

`topology-bugs.js::_openCreatedTopology()` gated its canvas load on
`window.editor`, but `topology.js` only publishes the editor as
`window.topologyEditor`. The old check therefore always evaluated
to `false`, the `loadTopologyFromData(...)` call never ran, and the
canvas kept whatever topology the user previously had on it. Only
when the user later opened the Topologies dropdown and clicked the
bug file did the *legacy* `loadFn` (in `topology-file-ops.js`,
which resolves `window.topologyEditor || window.editor`) actually
swap the canvas. That's why it "took switching twice".

Fix:

- Added an `_editor()` helper in `topology-bugs.js` that returns
  `window.topologyEditor || window.editor || null`. All call sites
  (`_toast`, `_openCreatedTopology`, the section-list refresh path)
  now resolve through this helper.
- `_openCreatedTopology` additionally retries once after 150 ms if
  the editor isn't attached yet, so a boot race (dropdown opened
  before `topology.js` finished constructing) can't strand the
  user on a stale canvas either.

### Visual / readability changes (addresses 2 + 3)

Rewrote `serve.py::_build_bug_topology_json` to move meaning out
of words and into the picture. Summary of the deltas:

| Element | Before | After |
|---|---|---|
| Header ("BUG SW-XXXXX + title") | Bare red text over the dark grid, no background -- low contrast. | Solid dark-red panel with a matching red border and white text. Auto-contrasts via `_contrastColorForBg`. Title trimmed to 82 chars on a single line. |
| Ticket URL | Bare blue text. | Dark slate chip with a blue border directly under the header. |
| Link labels | Every link stamped with the literal word "iBGP". | Dropped. Link color alone carries the iBGP meaning; the context boxes explain it once. |
| Summary card | Two labels ("Bug Summary:" and "Issue Summary:") plus the full paragraph, up to 360 chars. | Single chip titled "Symptom" with one sentence, max ~160 chars. Full body still in `metadata.bug_summary`. |
| Route card | Titled "Route under test:" with `dst ...` etc. | Titled "Route"; column-aligned `dst / src / act` lines. |
| VRF chip | Three lines ("VRF name", "RD x", "RT y") with faint violet border. | Two lines ("VRF name" on top, "RD x  RT y" aligned below) on an opaque violet panel. Reads like a badge. |
| Device IP labels | Bare grey text under the device. | Dark chip so the IP stays readable against the canvas grid. |
| Role coloring | Generic blue/green/purple by index. | Label-aware: `CE*` / `Spirent` / `ExaBGP` green, `RR*` purple, `PE*` blue. Meaning travels in the color. |
| Failure marker | Single red cross at device corner. | Soft red halo circle around the failing device **plus** the red cross at the corner. The halo is a `shape` so z-order keeps it below the device; only the outer ring shows. |
| Text over grid | `showBackground: False` on nearly everything -- unreadable. | All on-canvas text chips use `showBackground: True` with ~0.88-0.92 alpha, explicit `backgroundPadding`, and a tinted border. |

Shape-geometry note: shapes in this codebase use `(x, y)` as their
CENTER (see `topology-shape-drawing.js` -- `ctx.arc(x, y, w/2, ...)`).
An earlier version of the halo treated `(x, y)` as top-left and
drew the halo offset by one radius; corrected in this pass.

### Files touched + synced to `/home/dn/CURSOR/`

- `topology/topology-bugs.js` -- `_editor()` helper, uses
  `window.topologyEditor` everywhere, retry-once fallback in
  `_openCreatedTopology`, and a regression note in the docblock
  explaining why `window.editor` is poisoned.
- `topology/serve.py` -- rewritten `_build_bug_topology_json` with
  the visual pass above. Panel colors centralized at the top of
  the function for future tweaks.
- `topology/index.html` -- cache buster bumped
  `topology-bugs.js?v=20260420h` -> `?v=20260421a`.

Backend restart: `systemctl --user restart topology-app.service`
(the process runs without `--reload` for `serve.py`).

### Verification

1. User A is on any topology (e.g. a regular saved one). Open the
   Topologies dropdown, click the orange `+ Bug` pill on the Bugs
   row, enter a SW id, press Create.
2. The canvas MUST flip to the new bug topology immediately (no
   second navigation needed). Previous topology's devices / links
   must be gone.
3. The header text is a clearly readable red panel with the SW id
   and title. The ticket URL sits on a slate chip beneath it.
4. The Symptom card shows at most two visible lines. If the Jira
   description was longer, it ends with "..." and the full body
   is preserved in `metadata.bug_summary`.
5. If the parser found a PE-1 device, it is blue and its VRF (if
   any) floats as a violet badge above it. The failing device
   carries a faint red halo plus the red cross at its corner.
6. No link has the word "iBGP" stamped on it.

### Quick smoke-test (no browser)

```bash
python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('serve', '/home/dn/CURSOR/serve.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
topo = m.Handler._build_bug_topology_json(
    'SW-999',
    title='Example',
    summary='Long prose ...',
    devices=[{'label':'CE-1'},{'label':'PE-1'},{'label':'RR'},{'label':'PE-2'}],
    failure_device='PE-1')
print([o['type'] for o in topo['objects']])
"
```

Expect: header + URL chip + 4 devices + 4 IP chips + 3 links +
Symptom card + failure halo + cross. No iBGP text nodes.

## AI Minichat -- per-user architecture (2026-04-21b)

### What shipped

An in-app AI assistant drawer anchored to a persistent launcher pill in the
bottom-left bar next to the current-topology indicator. Users describe a
topology in plain English, the assistant generates it with an LLM, and the
result is saved under a new built-in `__ai` domain and optionally loaded
straight onto the canvas. The same drawer also answers questions about the
app itself via a static knowledge digest, and always has a live snapshot of
the user's current canvas (devices + links + counts).

Hard rules enforced from day one (see `~/.cursor/rules/multiuser-by-default.mdc`):

- **Per-user credentials, always.** Each user has their own
  `~/.topology_users/<user>/ai_config.json` (mode 0600). The API key is never
  echoed back through `GET /api/users/me/ai-config` -- only `configured`,
  `provider`, `model`, and a masked `token_hint`.
- **Per-user generated topologies.** AI-generated topologies land in the
  user's built-in `__ai` domain under `sections/__ai/<name>.json` via the
  existing sections helpers. No cross-user leakage.
- **JWT-gated routes.** `GET/PUT/DELETE /api/users/me/ai-config`,
  `POST /api/ai/chat`, `POST /api/ai/topology/generate` all call
  `_require_auth()` first.
- **Tool-use contract.** The LLM can only emit the `create_topology` tool.
  Server normalizes the payload (`ai.context.normalize_topology_payload`)
  before writing it. Unsupported tools are reported as preview cards with
  no side effects.

### File layout

```
topology/
  ai/
    __init__.py          # public surface: service + context
    knowledge.md         # static app knowledge digest (~5 KB)
    service.py           # LlmClient + AnthropicClient + OpenAiClient
    context.py           # TOPOLOGY_TOOL_SCHEMA + build_live_context + normalize_topology_payload
  serve.py               # _handle_ai_config_* + _handle_ai_chat + _handle_ai_topology_generate
  topology-ai.js         # drawer + launcher + config panel + tool-card render
  index.html             # #topo-bottom-left-bar wrapper + #ai-chat-launcher pill + drawer styles
```

### Backend flow (per request)

1. `self._require_auth()` -> `username`.
2. `resolve_client_for_user(username)` reads
   `user_store.user_ai_config_path(username)` and returns an `AnthropicClient`
   or `OpenAiClient` (or raises `LlmError(401)` -> `code: not-configured`).
3. `_build_ai_system_prompt(username, canvas)` assembles:
     a. `load_knowledge_digest()` -- cached on mtime, re-read on file change.
     b. `build_live_context(username, canvas)` -- per-user + per-canvas
        JSON snapshot, capped at ~6 KB.
     c. hard rules block for tool use.
4. `client.chat(messages, tools=[TOPOLOGY_TOOL_SCHEMA])` -> normalized
   `{text, tool_calls, usage, model, provider, stop_reason}`.
5. For each `create_topology` tool call: `normalize_topology_payload(args)`
   validates + fills defaults, then `_ai_save_generated_topology(username, topology)`
   writes it to `sections/__ai/<safe_name>.json`.

### Frontend flow (per drawer session)

1. Boot: `_initLauncher()` binds the always-on `#ai-chat-launcher` pill.
   `_probeAiConfig()` hits `GET /api/users/me/ai-config` and toggles the
   `needs-setup` pulse state when `configured: false`.
2. Open: `window.TopologyAI.open()` (via click, the `A` key pressed
   outside any text field, or last-state restoration from localStorage)
   slides the right-side drawer in. Strict
   mutex: closes `TopologyBugs` + `TopologyShare` inline panels before
   opening, and both of those reciprocate by calling
   `window.TopologyAI.close()` on their own open paths.
3. Config: if the user hasn't set up a key, the inline config panel opens
   automatically. Provider presets (Claude / OpenAI) + model + API key +
   optional base URL. Blank key keeps current (server re-uses existing on
   PUT when `api_key` is empty).
4. Chat: composer supports multi-line (`Shift+Enter`), sends history (last
   ~20 turns) + live canvas snapshot on each turn.
5. Tool card: `create_topology` tool calls render as a preview card with
   two actions -- `Keep in AI domain only` (already saved server-side) and
   `Save + Load on canvas` (re-fetches via `/api/sections/__ai/<file>` and
   pushes through `editor.loadTopologyFromData`, identical to the Bugs
   flow).

### Keyboard shortcuts + UX

- `Alt+A` toggles the drawer anywhere. Not `Cmd+A` / `Ctrl+A` -- those
  collide with canvas "select all".
- `Escape` closes only when focus is inside the drawer, so wizard modals
  don't accidentally kill the drawer.
- Drawer is floating + resizable 320-720 px. The canvas stays interactive
  underneath. Open/closed state + width persist in `localStorage`
  (`tpai.drawer.*` keys).

### Known gaps (Phase B)

- No persistent chat history yet. `user_store.user_ai_chats_db_path()` and
  the SQLite layout are already defined; the drawer holds messages only
  in-memory for Phase A.
- Only `create_topology` tool is wired. `edit_canvas`, `focus`, and
  `ask_user` are drafted in the knowledge digest but not yet implemented;
  the drawer renders unsupported tool calls as a benign notice.
- No streaming responses. `_post_json` in `ai/service.py` waits for the
  full reply (60 s timeout for chat, 90 s for topology generation). Phase
  B will switch to SSE when we introduce the edit tools.

### Free providers: Groq + Ollama (2026-04-21f)

The app used to force users to have an Anthropic or OpenAI key -- both
cost money and the "ChatGPT Enterprise does not include API credits"
thing bit at least one user in the face. Two free providers are now
built in, and the same request path speaks to them because both talk
the OpenAI `/v1/chat/completions` wire protocol.

| Provider  | Free?                        | Auth        | Speed on this host         | Where it runs                          |
| --------- | ---------------------------- | ----------- | -------------------------- | -------------------------------------- |
| anthropic | No (pay-as-you-go)           | `sk-ant-`   | Very fast                  | console.anthropic.com                  |
| openai    | No (pay-as-you-go)           | `sk-`       | Very fast                  | api.openai.com                         |
| **groq**  | **Yes (free tier)**          | `gsk_`      | Fastest hosted (LPU)       | api.groq.com/openai                    |
| **ollama**| **Yes (forever)**            | none        | Slow on 4-core CPU host    | localhost:11434 on the topology-app VM |

#### Backend wiring (`ai/service.py`)

Groq and Ollama both reuse `OpenAiClient` -- only the `base_url` and the
effective `provider_name` differ. `_OPENAI_COMPAT_PROVIDERS` holds the
preset table and `resolve_client_for_user` stamps
`client.provider_name = "groq"` (or `"ollama"`) after construction so
the classified error cards read "Groq quota exhausted" instead of
"OpenAI quota exhausted".

Ollama has no real auth -- the HTTP handler ignores the `Authorization`
header entirely. We still send `Bearer ollama` so the header is
well-formed; if the user leaves the UI key field blank, the PUT handler
in `serve.py` (`_handle_ai_config_put`) stashes the placeholder
`"ollama"` so downstream code never sees an empty string. The rest of
the providers remain strict: `api_key is required`.

`PROVIDER_DEFAULTS` keeps the per-provider `model`, `base_url`, and
`key_prefix` used for the mismatch banner and default-model fallback.
New entries: `groq` with `gsk_` prefix and `llama-3.3-70b-versatile`,
`ollama` with empty prefix (disables the banner) and
`qwen2.5:7b-instruct`.

#### Frontend wiring (`topology-ai.js`)

Two new entries in `PROVIDER_PRESETS`:

- `groq` -- curated models: `llama-3.3-70b-versatile` (default),
  `llama-3.1-8b-instant`, `qwen-2.5-32b`,
  `deepseek-r1-distill-llama-70b`.
- `ollama` -- curated models: `qwen2.5:7b-instruct` (default),
  `qwen2.5:3b-instruct`, `llama3.1:8b-instruct`,
  `llama3.3:70b-instruct`. Flagged with `key_optional: true` and
  `default_base_url: 'http://localhost:11434'`.

Three UI consequences of `key_optional`:

1. The sub-label next to the "API key" field reads
   **"(not required for Ollama)"** instead of
   **"(leave blank to keep current)"**. Implemented via
   `_keySubLabel(preset, current)` + a `data-role="cfg-key-sub"` span
   that the provider-change handler rewrites at runtime.
2. The prefix-mismatch banner is suppressed: `_refreshMismatch` returns
   early when the active preset has `key_optional`, because there's no
   known prefix to compare against and any pasted sk-/gsk-/etc. key
   would produce a spurious warning.
3. The Base URL placeholder is populated from `preset.default_base_url`
   on provider change, so first-time Ollama users see
   `http://localhost:11434` as a hint. We set the placeholder, not the
   value -- this preserves custom overrides (e.g. a remote Ollama box).

Key detection in `_detectProviderFromKey` now also recognizes `gsk_*`
-> `groq`, so pasting a Groq key into the Claude-selected panel
triggers the normal "Switch to Groq" banner.

#### Ollama install (one-time, host-side)

```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable --now ollama
ollama pull qwen2.5:7b-instruct   # ~4.7 GB, 32k context
ollama pull qwen2.5:3b-instruct   # ~1.9 GB, CPU-friendlier
```

Ollama 0.21 binds to `127.0.0.1:11434` by default -- the topology-app
process lives on the same host so no firewall work is needed. If you
later move Ollama to a GPU box, set `OLLAMA_HOST=0.0.0.0` in
`/etc/systemd/system/ollama.service` and point the UI's Base URL field
at that box.

**Known issue on CPU-only hosts**: on the current 4-core lab VM the
first generation often takes minutes because llama.cpp is CPU-bound
and the model has to be paged in. For interactive use on CPU-only
hosts, prefer `qwen2.5:3b-instruct` or switch to Groq.

#### Verify

```bash
# Check resolver stamps provider_name correctly
python3 -c "
import sys; sys.path.insert(0, 'topology')
from ai.service import resolve_client_for_user
import ai.service as s
s._read_ai_config = lambda u: {'provider':'groq','api_key':'gsk_test','model':'','base_url':''}
c = resolve_client_for_user('x'); print(c.provider_name, c.base_url, c.model)
"
# -> groq https://api.groq.com/openai llama-3.3-70b-versatile

# Ollama local endpoint (expect empty list until models are pulled)
curl -s http://localhost:11434/api/tags | python3 -m json.tool
```

#### Live Ollama model inventory + quick-start (2026-04-21g)

Problem: the Ollama dropdown was a hardcoded list (`llama3.1:8b-instruct`,
`llama3.3:70b-instruct`, ...). If the admin hadn't run `ollama pull` for
the exact tag the user picked, the first chat message failed with
`model "X" not found` and required a round-trip back to Credentials.

Fix has three parts:

1. **Backend** `GET /api/ai/ollama/models` (serve.py::
   `_handle_ai_ollama_models`) proxies `localhost:11434/api/tags`,
   returns `{ok:true, installed:true, models:[{id,size_mb,family,
   parameter_size,quantization_level}], count}`. Auth-gated. Returns
   `{ok:false, installed:false, error:"..."}` when Ollama is down (no
   500 -- the UI branches on `installed`).

2. **Frontend** (`topology-ai.js::_loadOllamaInstalledModels`) fires on
   provider-change AND on initial render when saved provider is
   `ollama`. Rebuilds the `<select>` with ONLY real on-disk tags
   (formatted as `qwen2.5:7b-instruct -- 4683 MB on disk`). Empty
   install produces a single `Custom model name...` option + hint
   `"No Ollama models installed on this server. Ask an admin to run:
   ollama pull qwen2.5:7b-instruct"`. Previous pick is preserved if
   still installed, so mid-edit users don't get a surprise reset.

3. **Quick-start hero**: when the user is `!current.configured`, a
   primary gradient card renders above the provider dropdown with
   a single **"Use local AI now"** button. On click it:
   - `GET /api/ai/ollama/models` to find the first installed tag
     (falls back to `preset.models[0].id` if empty)
   - Saves `{provider:'ollama', model:<tag>, base_url:'', api_key:''}`
     via the standard `_saveAiConfig` path (server injects the
     `"ollama"` placeholder key, see `_handle_ai_config_put`)
   - Toasts `"Local AI ready -- model: <tag>"` and closes the panel.

   Zero typing, zero dropdown navigation. For users who already have a
   config the hero is hidden to avoid visual noise.

Base URL field moved behind an `<details class="ai-config-advanced">`
toggle -- the common path never needs it, and the panel is noticeably
shorter now. Existing overrides are preserved on the hidden input so
toggling Advanced open round-trips correctly.

#### Thinking-forever bug fix + CPU-inference realism (2026-04-21h)

Symptom reported: "Thinking..." bubble never flipped to an answer on
`qwen2.5:3b-instruct`. Logs showed:

```
ollama ... "truncating input prompt" limit=4096 prompt=4144 keep=4 new=4096
ollama ... POST "/v1/chat/completions" 500 | 1m0s
serve.py ... "POST /api/ai/chat HTTP/1.1" 504
```

Three independent issues stacked on top of the raw CPU cost:

1. **60s timeout was too aggressive for local CPU inference**.
   Raised `_handle_ai_chat` to 240s and `_handle_ai_topology_generate`
   to 300s when `client.provider_name == "ollama"`. Hosted providers
   keep the tight 60s/90s ceilings to surface real network issues.

2. **Ollama's default 4096-token context was shorter than our system
   prompt**. Created systemd drop-in
   `/etc/systemd/system/ollama.service.d/override.conf` with:

   ```
   Environment="OLLAMA_CONTEXT_LENGTH=8192"
   Environment="OLLAMA_KEEP_ALIVE=30m"
   ```

   8192 costs ~288 MB KV cache for qwen2.5:7b Q4_K_M -- fine on the
   386 GB RAM host. 30m keep-alive avoids the 2-3s cold-load penalty
   on follow-up questions.

3. **Frontend loading bubble was static** -- no elapsed time, no way
   to abort. Rewrote the loading bubble to:
   - Show a live `Xs` counter that ticks every second in place
     (patch-only, no full re-render to avoid flicker).
   - Splice in a helper hint after 12s:
     `"Local CPU models can take 1-3 min for the first answer. For
     fast responses, switch to Groq in settings."`
   - Expose a **Stop** button that calls `_currentAbort.abort()` on
     the underlying `AbortController`. The aborted request is rendered
     as `"Request cancelled."` (notice variant) and the composer
     returns to idle.

**Reality check for CPU hosts**: these changes make Ollama's slow path
*survivable* (clear progress, recoverable), not *fast*. The physics
don't change: `qwen2.5:3b` at ~8-12 tok/s on 4 CPU cores produces a
300-token answer in ~30-45s, plus 5-15s prompt processing, plus a
full extra round-trip when the model emits a `get_topology_context`
tool call (most canvas-related questions do). For truly interactive
use, point users at **Groq** (free hosted, 500+ tok/s) via the
provider dropdown -- `llama-3.3-70b-versatile` is a drop-in
replacement for local qwen2.5.

#### Cloudflare bot-block on Groq fixed via User-Agent (2026-04-21i)

Symptom: Groq calls failed with `Upstream HTTP 403` + `error code: 1010`
while the **exact same key + URL succeeded from curl** in 443 ms:

```bash
$ curl -X POST https://api.groq.com/openai/v1/chat/completions ...
HTTP/2 200
server: cloudflare
cf-ray: 9efb942ac8338e45-TLV
... "Hello is nice."
```

Cause: Python's `urllib` sends `User-Agent: Python-urllib/3.10` by
default, which Cloudflare's Bot Management flags as automated
traffic. The challenge body (HTML) contains `error code: 1010` --
the "browser signature banned" family -- and looks superficially like
an auth error but isn't.

Fix in `ai/service.py::LlmClient._post_json`: inject a polite
identifiable UA on every upstream request, and send `Accept:
application/json` so a challenge page (HTML) would at least be
obviously wrong instead of passing content-type sniffing:

```python
merged_headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "DriveNets-Topology-Studio/1.0 (+https://drivenets.com)",
    **headers,
}
```

Also classified the 1010 family in `_classify_upstream_error` as a
new `cf_bot_blocked` kind (mapped to HTTP 503 -- it IS transient) with
a dedicated frontend card titled *"Blocked by upstream CDN"* that
correctly does NOT nudge the user to re-enter their perfectly valid
key.

Verification:

```python
# Python path via our own LlmClient, no curl:
>>> client = resolve_client_for_user('yarel')
>>> client.chat([{'role':'user','content':'Reply with READY only.'}], tools=None)
{'text': 'READY', 'stop_reason': 'stop', 'model': 'llama-3.3-70b-versatile'}
```

#### IPv6 stall on Cloudflare-fronted providers fixed by IPv4-only DNS (2026-04-21j)

Symptom: user reported *"Thinking... 40s"* on Groq -- and the
canvas-explain question took the full 40 s before returning an
answer. The misleading part: tok/s in the Groq response body was
278-969 (perfect, matches Groq's public benchmarks), yet wall time
was 40+ s. Curl on the same host at the same second returned in
443 ms for the same payload.

Root cause: `socket.getaddrinfo("api.groq.com", 443)` on this host
returns IPv6 results **first**:

```
['2606:4700:4405::6812:26ec', '2606:4700:4405::ac40:9514',
 '104.18.38.236', '172.64.149.20']
```

Python's `urllib.request` iterates them in order and tries IPv6
first. This host's IPv6 path to Cloudflare is broken -- the TCP
handshake doesn't cleanly fail, it just stalls until Python's
internal socket deadline fires, at which point urllib falls back to
the next IP (v4) and the POST succeeds. Net effect: a 30-40 s
"tax" on every single upstream call.

curl doesn't see this because it implements RFC 8305 Happy Eyeballs
(v4 + v6 dialled in parallel, whichever connects first wins, typical
fallback window ~250 ms). Python's stdlib does not.

Measured impact on the same host/key/payload:

| client                | wall time    | body  |
|-----------------------|--------------|-------|
| dual-stack `urllib`   | 40 670 ms    | empty |
| curl (happy-eyeballs) |    443 ms    | ok    |
| IPv4-only `urllib`    |    211 ms    | ok    |

Fix in `ai/service.py`: added a scoped `_force_ipv4()` context
manager that swaps `socket.getaddrinfo` for an `AF_INET`-only
variant for the lifetime of the `urllib.request.urlopen` call, then
restores the original. Scoped rather than process-wide because
other code paths (discovery, MCP, etc.) might legitimately want
v6. When the host's v6 routing to Cloudflare is fixed, drop the
wrapper -- no other changes needed.

```python
@contextlib.contextmanager
def _force_ipv4():
    socket.getaddrinfo = _ipv4_only_getaddrinfo
    try:
        yield
    finally:
        socket.getaddrinfo = _ORIG_GETADDRINFO

# in _post_json:
with _force_ipv4(), urllib.request.urlopen(req, timeout=timeout) as resp:
    ...
```

End-to-end verification via our real backend path:

```
provider=groq model=openai/gpt-oss-120b
call 1: wall=0.27s
call 2: wall=0.42s
call 3: wall=0.32s
```

#### Refreshed Groq model lineup based on measured speed (2026-04-21j)

Benchmarked the live Groq catalog from this host on 2026-04-21.
Tok/s is server-side `completion_time`; wall is end-to-end through
`OpenAiClient` (includes TLS, prompt, generation).

| Model                                     | tok/s | wall (20 tok) | Tool use | Verdict                    |
|-------------------------------------------|-------|---------------|----------|----------------------------|
| `openai/gpt-oss-20b`                      |  916  |   0.44 s      | Strong   | Fastest                    |
| `openai/gpt-oss-120b`                     |  484  |   0.46 s      | Best     | **New default (best balance)** |
| `qwen/qwen3-32b`                          |  498  |   ~0.5 s      | Good     | Strong JSON output         |
| `meta-llama/llama-4-scout-17b-16e-instruct`|  442  |   ~0.5 s      | Good     | MoE, newest Llama          |
| `llama-3.1-8b-instant`                    |  393  |   0.48 s      | Basic    | Smallest                   |
| `llama-3.3-70b-versatile`                 |  278  |   0.51 s      | Good     | Old default, no longer top |

Changes:

- `ai/service.py` `PROVIDER_DEFAULTS["groq"]["default_model"]`
  changed from `llama-3.3-70b-versatile` to `openai/gpt-oss-120b`.
- `topology-ai.js` `PROVIDER_PRESETS.groq.models[]` reordered so
  `openai/gpt-oss-120b` is first with "Recommended -- best tool
  calling" and `openai/gpt-oss-20b` is second with "Fastest".
- Removed `qwen-2.5-32b` (no longer in catalog), added live-verified
  `qwen/qwen3-32b` and `meta-llama/llama-4-scout-17b-16e-instruct`.

#### Zombie serve.py / scaler_bridge must be killed before restart

Symptom: `systemctl --user restart topology-app.service` succeeds,
the unit reports `active (running)`, but requests hang for 30-60 s
because the NEW serve.py failed to bind 8080 and a ZOMBIE serve.py
from hours/days ago is still listening. Look for `restart counter
is at 1840` in the journal -- that means the unit has been
crash-looping silently.

Detect:
```bash
sudo ss -lntp | grep -E ":8080|:8766"
ps -eo pid,etime,cmd | grep -E "serve.py|scaler_bridge"
```

If the PID of the process holding 8080 is **not** the systemd
`MainPID` reported by `systemctl --user status`, it's a zombie.

Fix:
```bash
# Kill every python3 holding 8080 / 8766 / their children, then
# let systemd do a clean restart.
sudo kill -9 <zombie_pids>
systemctl --user restart topology-app.service
systemctl --user reset-failed topology-app.service  # clear crash counter
```

Happens when an earlier run of serve.py was backgrounded outside
of systemd (manual `python3 serve.py &`) and outlived its wrapper.
Always prefer `systemctl --user restart` over manual launch.

#### Provider-aware slow-path hint (2026-04-21j)

The "Local CPU models can take 1-3 min for the first answer. For
fast responses, switch to Groq in settings." hint incorrectly
appeared when the user was **already on Groq**, making the UX feel
broken when a stall was happening for any other reason (zombie
server, IPv6 hang, CDN block). Fixed in `topology-ai.js`:

- Hint is Ollama-only for the 12 s threshold.
- Hosted providers get a different hint at 8 s ("try GPT-OSS 120B
  on Groq") which is actionable regardless of who they're on.
- Both renderers (the bubble re-render in `_renderMessage` and the
  incremental splice in the 1-second tick interval) were updated
  symmetrically; keep them in sync if you change the copy.

**This host specifically is worse than a generic 4-core box.** Check:

```
$ grep -oE "isolcpus=[^ ]*" /proc/cmdline
isolcpus=2-43,46-87

$ nproc
4
```

The machine has **88 logical CPUs** (2×Xeon Gold 6152), but the
kernel command line reserves 84 of them (`isolcpus=2-43,46-87` +
`nohz_full=...` + `rcu_nocbs=...`) for DPDK / DriveNets router
simulation. Ollama is pinned to the remaining 4 CPUs (0-1, 44-45),
and those 4 are also contended by all other non-router workloads --
including the topology-app itself (`systemd show ollama -p
ControlGroup` -> `/system.slice/ollama.service`, `Cpus_allowed_list:
0-1,44-45`).

Do NOT `taskset` Ollama onto the isolated cores -- they belong to
the router simulation workloads and yanking them causes DPDK drops.
If local inference is a hard requirement, the correct fix is to
expand `isolcpus` to carve out a dedicated block (kernel cmdline
change + reboot) or to host Ollama on a different VM with a GPU.
Until then, **Groq is the answer** for interactive use on this host.

### Classified upstream error cards (2026-04-21e)

The old failure path dumped the raw provider JSON into a red bubble
(`"AI provider quota or rate limit reached: Provider quota / rate limit:
{ "error": { ... } }"`). That was ugly and left the user no next step.

**Now**: `ai/service.py::_classify_upstream_error(status, body_txt)`
parses the OpenAI / Anthropic error envelope and returns a stable
`(kind, friendly_message)`. `LlmError` carries `kind` + `details` (raw
body, ≤ 2 KB) + `provider`. `serve.py` forwards all three in the JSON
response (`code: "upstream"`, `kind`, `details`, `provider`).

Known `kind` values (keep frontend in sync if you add one):

| kind                 | When                                  | UI behaviour                     |
| -------------------- | ------------------------------------- | -------------------------------- |
| `insufficient_quota` | OpenAI `insufficient_quota` / billing | Card with "Open \<provider\> billing" (new tab) + "Switch provider" |
| `rate_limited`       | HTTP 429 / `rate_limit_exceeded`      | Card with "Retry" + "Open settings" |
| `api_key_rejected`   | HTTP 401 / `authentication_error`     | Card with "Open settings"; auto-opens config panel |
| `model_not_found`    | `model_not_found` / "model ... not found" | Card with "Open settings" |
| `context_overflow`   | `context_length_exceeded`             | Card with "Clear conversation" + "Open settings" |
| `timeout`            | `urllib TimeoutError`                 | Card with "Retry" |
| `unreachable`        | `urllib URLError`                     | Card with "Retry" + "Open settings" |
| `upstream_error`     | fallback                              | Card with "Retry" |

Frontend renderer: `topology-ai.js::_renderChatErrorCard(kind, message, details, provider)`.
Each card shows **title + hint + provider's own one-liner + action buttons + collapsible "Technical details"** (raw body, pre-wrapped, max-height 200 px). CSS
lives under `.ai-msg.error-card` / `.ai-err-card__*`.

The `_sendUserMessage` branch now tracks `_lastUserMessage` so the "Retry"
button resends the original prompt without the user retyping; it also
removes the error card before resending so the log stays clean on success.
`_clearConversation` resets `_lastUserMessage`.

Delegated click handlers in `_wireDrawerEvents` dispatch `data-action`
values `ai-error-retry`, `ai-error-settings`, `ai-error-clear`. External
links (billing URLs) use `<a target="_blank" rel="noopener noreferrer">`
with a trailing `↗` glyph; they sit inside the same flexbox as the
buttons so the visual rhythm matches.

Classifier unit-smoke (no browser):

```bash
python3 -c "from ai.service import _classify_upstream_error; \
import json; \
print(_classify_upstream_error(429, json.dumps({'error':{'code':'insufficient_quota','message':'You exceeded your current quota...'}})))"
# -> ('insufficient_quota', 'You exceeded your current quota...')
```

### Testing checklist

- [ ] Log in as user A, set an Anthropic key via the drawer. Verify
      `ls -l ~/.topology_users/A/ai_config.json` shows mode `-rw-------`.
- [ ] Log in as user B in a different browser session. Verify
      `GET /api/users/me/ai-config` returns `{configured: false}` for B.
- [ ] Ask for "a 4-leaf 2-spine Clos". Confirm a topology lands under
      `sections/__ai/` for A only, not B.
- [ ] Pressing `A` on the canvas toggles the drawer. Pressing `A` inside
      a wizard text field types "a" normally (never swallowed). Click the
      "Share" icon on any domain -- the AI drawer closes. Open AI again
      -- the share form closes.
- [ ] Paste an `sk-...` (OpenAI) key while provider is Claude. Verify the
      mismatch banner appears, "Switch to OpenAI" flips the dropdown +
      resets the model, and "Use anyway" dismisses for the session.
- [ ] Refresh browser with drawer open -- it restores to the same width
      and open state.


## Active-Topology Indicator: Shared-In Attribution + Multi-Topology Toggles

The bottom-left "active topology" indicator (`#topo-active-indicator` in
`index.html`, wired from `topology-file-ops.js` `updateTopologyIndicator`)
was originally built for OWN domains only. When a user loaded a file
shared with them (either via a whole-domain share or the "Shared with me"
inbox), two UX gaps showed up:

1. The "Shared with me" / `BY ALICE` pill had no tooltip -- you couldn't
   tell who shared it without opening the Topologies menu.
2. The multi-topology dots (`#topo-active-dots`) disappeared, because
   `_refreshDomainDots` only knew about `/api/sections/{id}/topologies`.
   Shared-in sections live in `user_store` and are only reachable via
   `/api/domains/{id}/topologies`, so the fetch returned empty and the
   dots were hidden even when multiple shared topologies existed.

Both are fixed by threading a single optional `sharedInfo` payload
through the indicator pipeline. Shape:

```
{ isSharedIn: bool, isInbox: bool, owner, ownerDisplay, permission }
```

### Call-graph changes

- `updateTopologyIndicator(name, domainName, domainColor, sectionId, sharedInfo?)`
  - Sets a native `title` on `#topo-active-domain` like
    `Shared by Alice Smith (alice, read)` when `sharedInfo` is present.
    Clears it on own topologies so stale attributions never stick.
  - Persists `shared: sharedInfo || null` into `localStorage.topo_active`
    so the pill tooltip survives page reloads.
  - Forwards `sharedInfo` to `_refreshDomainDots`.
- `_refreshDomainDots(sectionId, currentName, sharedInfo?)`
  - If `sharedInfo.isSharedIn || sharedInfo.isInbox`, fetches
    `/api/domains/{id}/topologies` (same endpoint as
    `_loadSharedInDomainTopologiesInline`), mapping each entry to
    `{ name, filename (sanitized), id, shared: true }`.
  - Otherwise, fetches `/api/sections/{id}/topologies` as before.
  - Caches the resolved list + section + shared flag in
    `FileOps._domainTopoCache`, `_domainTopoCacheId`, `_domainTopoCacheShared`
    so dot clicks know which endpoint to use.
- `_navigateToTopology(index)`
  - Reads the cached shared flag and, when present, loads via
    `/api/domains/{id}/topologies/{topology_id}` (by id, not filename)
    and unwraps `payload.data || payload` -- mirroring the menu click
    path in `_loadSharedInDomainTopologiesInline`.
  - Replays the same `sharedInfo` back through `updateTopologyIndicator`
    so the pill tooltip + inverted CSS stay coherent after navigation.
- `restoreTopologyIndicator()` hydrates `d.shared` from localStorage so
  the indicator + dots survive reloads on shared-in topologies.
- `_loadSharedInDomainTopologiesInline(...).loadFn` now passes the
  shared-section attribution (`owner`, `ownerDisplay`, `permission`,
  `isSharedIn`, `isInbox`) into `updateTopologyIndicator`. Own-domain
  callers continue to omit the 5th arg (no behavior change).

### Why the inbox uses the same endpoint

`/api/domains/{id}/topologies` already handles both "regular shared-in
domain" (owner's id) AND the synthetic "Shared with me" inbox
(`is_shared_with_me_domain=true`). We picked that endpoint deliberately
for both so the dots list exactly matches what the Topologies dropdown
renders inline -- no drift, no surprises.

### Files touched

- `topology/topology-file-ops.js` (indicator + dots + nav + restore + shared-in loadFn)
- `topology/index.html` (cache buster `topology-file-ops.js?v=20260421f`)

No CSS changes needed -- the existing `#topo-active-domain` rules
render the pill correctly and the native `title` attribute gives us
the tooltip without a custom overlay.

### Active-Topology Pill Click Behavior (Apr 26, 2026)

The bottom-left active-topology pill must remain interactive. `topo-active-save`
is the quick-save target and stops event propagation; clicking the rest of
`#topo-active-inner` opens the main Topologies dropdown by forwarding to
`#btn-topologies`. Keep `_initIndicatorPillBtn()` wired from
`updateTopologyIndicator()` so newly loaded topologies get the click handler
even when there was no restored `topo_active` entry at page boot. Also keep
`updateTopologyIndicator(name, domainName, domainColor, sectionId, sharedInfo)`
call order exact; `topology-network-mapper.js` had a regression where it passed
the editor as the first argument, breaking the current-topology pill state.

---

## SSH: cluster GI-mode reliability + iTerm fallback toast (Apr 2026)

**User complaint**: "Why this message pops when clicking the SSH connect
button of a device, and when allowing iTerm opens without a connection?
Fix the device connections. Specifically for PE-4, fix that right now.
PE-4 and devices like it should have a valid way to connect to when in
GI mode as well."

### Root cause

Two independent failures stacked on top of each other:

1. **Cluster + GI/BASEOS_SHELL/RECOVERY mode -> unreliable iTerm path.**
   `openTerminalToDevice` in `topology/topology-object-detection.js`
   tried `_tryOpenClusterNccMgmtIterm` FIRST in GI mode. The backend
   `ScalerAPI.checkPort` returns `reachable: true` whenever SSH port 22
   answers from the bridge's vantage point -- but in GI mode the NCC SSH
   daemon is unreliable (credentials may not work, sessions hang
   mid-handshake) and even if it accepts connections the user's Mac
   often cannot reach lab CGNAT IPs (100.64/10) directly. Result:
   iTerm opens via `ssh://dnroot@100.64.7.197` but never connects.

2. **iTerm dispatch had no fallback for remote-Mac users.** `_openSshUrl`
   dispatched `ssh://` via anchor click and showed a success toast --
   but there was no easy recovery if the iTerm connection failed
   silently (no route, wrong scheme handler, SSH agent missing key,
   etc.). The user had to manually open the SSH dialog and pick "Web
   Terminal" on each attempt.

### Fix

#### (A) GI-mode cluster -> virsh console via web terminal (primary)

In `openTerminalToDevice` the `_isGiOrShell` branch (lines ~874-960)
now prefers web terminal over iTerm:

1. **If user explicitly set `preferredMethod='iterm'` on the device**
   (via the SSH dialog "Connect via" picker) OR global launch pref is
   `iterm`: try `_tryOpenClusterNccMgmtIterm` first -- the user knows
   their network reach and wants iTerm.
2. **Otherwise** (default, auto, or `webterm`): use virsh console via
   `TerminalPanel.open({ method: 'virsh_console', ... })`. This rides
   the same HTTP/WebSocket channel the user already has to the topology
   server, so it works whenever the topology server itself is
   reachable -- including remote-access Mac users on port-forwarded
   tunnels.
3. **If `sshConfig._virshInfo` is missing** (first visit to cluster in
   GI mode, or sshConfig was wiped): probe via
   `ScalerAPI.probeConnection(deviceId, host)`, find the `virsh_console`
   method entry, and populate `_virshInfo` (kvmHost, kvmUser, kvmPass,
   activeNcc, nccVms) from the probe response before opening the
   terminal.
4. **Last resort fallback**: if virsh discovery fails, try
   `_tryOpenClusterNccMgmtIterm` anyway (in case the user's network can
   reach NCC mgmt), then the `_showSshUnreachableNotification` modal
   with virsh/iTerm/settings buttons.

The rationale: **web terminal is always reachable when the topology
server is reachable**, while iTerm requires local network routing to
the target. For GI mode clusters specifically, NCC SSH is operationally
unreliable even when the port answers, so web terminal is both safer
AND more reliable.

#### (B) `_showItermOpenedToast` -- iTerm fallback toast with action button

New method `_showItermOpenedToast(editor, device, user, host, password, messageBody)`
in `topology/topology-object-detection.js` (~line 1590). Called from
the iTerm dispatch branch of `_openSshUrl` instead of
`editor.showNotification`. It renders a glass toast with:

- Icon (green checkmark)
- Two-line text: primary "[OK] iTerm: ssh user@host..." + secondary
  hint "Not connecting? Use the Web Terminal fallback (bridge-proxied)."
- **"Web Terminal" action button** (blue outlined). Click opens
  `TerminalPanel.open({ method: 'ssh_mgmt', host, user, password, ...})`
  to the same target -- the one reliable fallback when iTerm fails
  silently.
- Dismiss button (X)
- 9-second auto-dismiss with progress bar

The toast has its own id (`topology-iterm-fallback-toast`) and style
group (`iterm-fallback-toast-styles`) so it coexists with the main
notification system but replaces `topology-notification` when it
renders (so the user sees ONE authoritative toast).

#### (C) SSH dialog stops duplicating iTerm notifications

The `doConnect` function in `topology/topology-ssh-dialog.js` (~line
527) previously dispatched `editor._openSshUrl` AND called
`editor.showNotification` with its own "iTerm opened" message. After
(B), `_openSshUrl` owns the notification (with fallback button), so
the dialog just seeds `_pendingDevice`/`_pendingPassword` and calls
`_openSshUrl`. No more dual toasts.

### Why the web terminal fallback is safe

The web terminal proxies SSH server-side via the scaler bridge (same
backend the Network Mapper and scaler GUI use). Credentials flow
through the WebSocket connection to the bridge, which SSHes to the
target from inside the lab. This works for ANY topology-server user
because they're already authenticated to the bridge by the browser
session. No new security surface; same trust boundary as the existing
discovery/config-push flows.

### Files touched

- `topology/topology-object-detection.js` -- GI-mode virsh default,
  probe-on-missing-virshInfo, `_showItermOpenedToast` helper
- `topology/topology-ssh-dialog.js` -- remove duplicate iTerm
  notifications in `doConnect`
- `topology/index.html` -- cache busters `topology-object-detection.js?v=20260421g`
  and `topology-ssh-dialog.js?v=20260421g`

### Verification (user's scenario: PE-4)

PE-4 is YOR_CL_PE-4, a CL-86 cluster at 100.64.7.197. On first click
of the green SSH terminal button:

| Device state | Expected behaviour |
|---|---|
| DNOS (normal) | iTerm dispatch to `ssh://dnroot@100.64.7.197` + toast with "Web Terminal" button. If iTerm fails to connect, click the button -> web terminal via bridge (reliable). |
| GI / BASEOS_SHELL / RECOVERY | Direct web terminal virsh console to KVM host with `sudo virsh console --force <activeNcc>`. No iTerm dialog at all. If `_virshInfo` missing, auto-probe populates it from the backend. |
| preferredMethod='iterm' + GI | Still tries iTerm to NCC mgmt first (user's explicit override), falls through to web terminal if iTerm dispatch unreachable. |

#### AI canvas context "no devices, no links" bug fixed (2026-04-21k)

Symptom: user asked "Explain what is currently on my canvas" on a
topology with 7 visible devices + 5 links. AI answered *"There are
no devices, links, or VRFs on your canvas. The device count, link
count, text count, and shape count are all 0."* Not a hallucination
-- the AI was correctly reading an all-zero context block that the
backend was feeding it.

Root cause: the frontend `topology-ai.js::_collectCanvasSnapshot`
sends a **pre-bucketed** payload:

```javascript
{
  topology: { name, domain, section_id },
  counts:   { devices, links, shapes, texts },
  devices:  [{id,name,dnos,role,vrfs}, ...],
  links:    [{from,to,speed}, ...]
}
```

but the backend `ai/context.py::_canvas_block` only understood a
**flat typed** list:

```python
objects = snapshot.get("objects") or []  # always []
for obj in objects:
    if obj.get("type") == "device": ...
```

`objects` was never in the wire format, so every turn got
`device_count=0` regardless of canvas state.

Fix: `_canvas_block` now accepts BOTH shapes. First tries `objects`
(flat-typed, used by save/load code), falls back to
`{devices:[],links:[],counts:{}}` (pre-bucketed, used by the chat
endpoint). No frontend change -- wire format stays the same.

Verification:

```
device_count: 7
link_count:   5
answer: "Your canvas shows seven devices -- a spine (Spine-Arbor),
         three leaves (COMUS-NS1, CLFR, CLFR-A), one PE (pe1), ..."
```

#### Groq 429 rate-limit misclassified as "quota exhausted" (2026-04-21k)

Symptom: after a burst of chat turns, the user got a big red
*"Groq quota exhausted"* card nudging them to *"Top it up, or switch
provider"*. The key was fine, the account had full free-tier quota,
and curl against the same endpoint worked moments later -- so the
classification was wrong.

Root cause: Groq's 429 rate-limit body contains

```json
{
  "error": {
    "message": "Rate limit reached ... Please try again in 1.615s.
                Need more tokens? Upgrade to Dev Tier today at
                https://console.groq.com/settings/billing",
    "code": "rate_limit_exceeded",
    "type": "tokens"
  }
}
```

`ai/service.py::_classify_upstream_error` had a loose heuristic
`"billing" in msg.lower()` in the **insufficient_quota** branch that
came BEFORE the rate-limit branch. The substring matched the
billing URL in the body, so every Groq 429 was classified as quota
exhaustion. Complicating factor: OpenAI returns 429 for BOTH real
rate-limits AND real quota exhaustion, so naive "429 => rate_limit"
doesn't work either.

Fix: rewrote the classifier to require **explicit** quota signals
(typed `code=="insufficient_quota"`, `type=="insufficient_quota"`,
or well-known messages `"exceeded your current quota"` /
`"account is out of credits"`) before falling through to rate-limit
on HTTP 429 / `code=="rate_limit_exceeded"` / `"rate limit" in msg`.
Dropped the `"billing"` substring match.

Also polished the UI side: the rate-limit card now extracts
`"Please try again in N.Ns"` from the body and shows an actual
seconds-to-wait, plus suggests GPT-OSS 120B/20B as faster models
that use fewer tokens per turn (helps stay under the TPM budget).

Unit-test matrix (all 5 now pass):

| body                               | status | expected kind         |
|------------------------------------|--------|-----------------------|
| groq 429 "rate limit reached ..."  | 429    | rate_limited          |
| openai 429 "exceeded your quota"   | 429    | insufficient_quota    |
| openai 401 "incorrect api key"     | 401    | api_key_rejected      |
| groq 401 "invalid api key"         | 401    | api_key_rejected      |
| openai 404 "model gpt-6 not found" | 404    | model_not_found       |


## Draw loop crash -- `Cannot read properties of undefined (reading 'replace')` in `getLinkSelectionColors` (2026-04-21n)

### Symptom

On a topology loaded from autosave (65 objects), every wheel scroll and
every popup close flooded the console with the same unhandled error:

```
topology-device-styles.js:522 Uncaught TypeError: Cannot read properties of undefined (reading 'replace')
    at Object.getLinkSelectionColors (topology-device-styles.js:522:25)
    at TopologyEditor.getLinkSelectionColors (topology.js:11287:40)
    at Object.drawLink (topology-link-drawing.js:545:40)
    ...
    at Object.draw (topology-draw.js:459:23)
    at TopologyEditor.draw (topology.js:11211:38)
    at topology.js:2003:22
```

Dozens of identical stacks per frame (every link with bad data crashed
in the `sortedObjects.forEach(obj => { ... drawLink(obj) ... })` loop).

### Root cause

At least one link in the autosaved topology had `link.color === undefined`
(legacy shape). The flow was:

1. `drawLink(link)` read `link.color` into `linkColor` (undefined).
2. `editor.adjustColorForMode(undefined)` returned `undefined` (its
   early-return `if (!hex || typeof hex !== 'string') return hex`).
3. `editor.getLinkSelectionColors(undefined)` ran
   `linkColor.replace('#', '')` at
   `topology-device-styles.js:522` -> `TypeError`.
4. The exception escaped the per-link draw callback and was caught by
   the global `ErrorBoundary`, which `console.error`'d the stack.
5. Every `requestAnimationFrame` redraw reran the loop, so a single
   wheel scroll logged the same error per bad link per frame.

The same latent bug existed in `darkenColor`/`lightenColor` (both did
`color.replace('#', '')` without a guard), so a device with missing
`device.color` would have crashed the shape renderer the same way.

### Fix (layered defence)

1. `topology/topology-device-styles.js`:
   - `getLinkSelectionColors(editor, linkColor)` -- if `linkColor` is
     not a non-empty string, fall back to
     `editor.defaultLinkColor || (editor.darkMode ? '#ffffff' : '#666666')`
     before the `.replace()`.
   - `darkenColor(color, factor)` / `lightenColor(color, factor)` --
     return a neutral `rgb(102,102,102)` / `rgb(170,170,170)` when
     `color` is missing instead of crashing.
2. `topology/topology-link-drawing.js` (both `drawLink` code paths,
   ~line 529 and ~line 1240): coerce `link.color` up-front:
   ```js
   let rawLinkColor = (typeof link.color === 'string' && link.color.length > 0)
       ? link.color
       : (editor.defaultLinkColor || (editor.darkMode ? '#ffffff' : '#666666'));
   let linkColor = rawLinkColor;
   if (!isSelected) linkColor = editor.adjustColorForMode(rawLinkColor) || rawLinkColor;
   ```
3. `topology/topology-links.js` -- `LinkUtils.repairCorruptedLinks`
   extended with a color-heal pass: any `link`/`unbound` object whose
   `color` is missing or non-string gets
   `editor.defaultLinkColor || (theme default)` written back and a
   `[LinkRepair] Healed N link(s) with missing color -> <color>` log.
   The existing repair flow already calls `editor.saveTopology()`, so
   the autosave on disk becomes clean and the crash cannot reappear
   after a reload.

### Cache-buster bumps

All three files served as static assets, so `topology/index.html` was
updated (and mirrored to `/home/dn/CURSOR/index.html`):

- `topology-device-styles.js?v=20260204`   -> `?v=20260421n`
- `topology-link-drawing.js?v=20260310a`   -> `?v=20260421n`
- `topology-links.js?v=20260317d`          -> `?v=20260421n`

### Verification steps

After hard-refresh (Ctrl+Shift+R):
1. Scroll-zoom the canvas -- console stays clean (no `TypeError`
   from `getLinkSelectionColors`).
2. Open DevTools console, run `TopologyEditor` draw manually or drag a
   device -- no crash spam.
3. The auto-repair logs
   `[LinkRepair] Healed N link(s) with missing color -> #xxxxxx` on
   the first load that encounters a legacy link; subsequent loads show
   `[OK] No corrupted links found`.

### Rule of thumb

Any helper that ends up inside `draw()` / `sortedObjects.forEach(...)`
must be crash-proof. A single bad object should degrade gracefully,
not take down the entire frame. Prefer:

- `if (typeof x !== 'string' || !x) x = <safe default>` before any
  `x.replace(...) / x.startsWith(...) / x.match(...)`.
- Keep the `ErrorBoundary` as a last-resort safety net, not the
  happy path.

---

## Topologies dropdown ↔ "Manage Topology Domains" panel -- unified chrome

### Symptom / request

Stacking the "Manage Topology Domains" popover (`#manage-sections-panel`) on
top of the main Topologies dropdown (`#topologies-dropdown-menu`) showed two
different whites: the parent was a cool blue-tinted near-opaque
`rgba(252,253,255,0.94)` gradient, the child was a warmer true-white
`rgba(255,255,255,0.78)` with a visible frosted-glass grain. The two surfaces
read as "different materials" even though they belong to the same menu chain.

### Source of truth

The `Manage Topology Domains` panel is the one users specifically asked to
match. It carries inline JS-computed styles from
`FileOps.showManageSections` in `topology-file-ops.js` (≈ line 4244+):

- Light chrome (dark body): `background: rgba(255, 255, 255, 0.78)`
- Dark chrome (light body): `background: rgba(17, 25, 40, 0.78)`
- Both variants: `backdrop-filter: blur(16px) saturate(180%)`

### Fix

`styles.css` rules for `body.dark-mode .liquid-glass-dropdown.topo-menu-inverted`
and `body:not(.dark-mode) .liquid-glass-dropdown.topo-menu-inverted` were
rewritten to use the SAME solid colour + blur/saturate filter as the Domains
panel. Border / shadow colours were aligned to the Domains panel as well so
the two popovers are byte-identical chrome.

Do NOT reintroduce the `linear-gradient(135deg, rgba(252,253,255,…))` here --
that blue-tinted gradient is the regression the user flagged.

### Files touched

- `topology/styles.css` -- `.liquid-glass-dropdown.topo-menu-inverted` rules
  for both body modes.
- `topology/index.html` -- bumped `styles.css?v=` cache-buster to `20260421i`.
- Mirrored to `/home/dn/CURSOR/styles.css` + `/home/dn/CURSOR/index.html`.

### Rule of thumb

When two popovers share a menu chain (parent dropdown + a child panel that
slides in from it), keep their background colour + `backdrop-filter` recipe
identical. If one side uses `rgba(…,0.78) + blur(16px) saturate(180%)`, the
other must too, otherwise the chrome feels "broken" when the child sits on
top of the parent.

---

## Adding a new OpenAI-compatible free provider (Gemini pattern)

### Why this exists

Groq's free tier caps at ~12k TPM on `llama-3.3-70b-versatile`, which a
single `create_topology` turn can exhaust (see the 2026-04-21 "Rate limit
hit on Groq" screenshot thread). The cleanest long-term answer is to keep
several parallel free-tier providers plugged into the drawer so users can
jump laterally instead of waiting out the retry-after window. Google
Gemini was the first such addition (2026-04-21) and as of 2026-04-22 it
is the **primary default provider** for the whole deployment: first entry
in `_OPENAI_COMPAT_PROVIDERS`, first entry in `PROVIDER_DEFAULTS`, first
entry in `PROVIDER_PRESETS`, and (when `GEMINI_API_KEY` is exported in
the server environment) the target of the Quick-start hero button. The
procedure below is the template for the next addition; see
"Deploy-wide shared AI key" lower in this file for the shared-key knob.

### The three-place recipe

Any OpenAI `/v1/chat/completions`-compatible provider drops in with
zero new client code -- the existing `OpenAiClient` in
[topology/ai/service.py](topology/ai/service.py) handles the wire protocol.
You only need to register it in three places:

1. Backend runtime registry --
   `_OPENAI_COMPAT_PROVIDERS` in `topology/ai/service.py`. Keyed by
   internal provider id (`"gemini"`, `"groq"`, `"ollama"`, ...). Carries
   `base_url` and `default_model`.

2. Backend UI-facing convenience map --
   `PROVIDER_DEFAULTS` in the same file. Carries `model`, `base_url`,
   and the canonical **`key_prefix`** (Gemini = `"AIza"`, Groq = `"gsk_"`,
   Anthropic = `"sk-ant-"`). The prefix is used by the frontend's
   `_detectProviderFromKey` to nudge users who paste a key into the
   wrong slot.

3. Frontend preset --
   `PROVIDER_PRESETS` in `topology/topology-ai.js`. This is the source
   of truth for the dropdown label, the "Get a key" link, the curated
   model list shown in the settings panel, and the placeholder /
   tokens-hint copy. Add the prefix to `_detectProviderFromKey` in
   the same file so the mismatch warning covers the new provider.

Do NOT add a new `LlmClient` subclass for an OpenAI-compat provider.
`resolve_client_for_user` at the top of `ai/service.py` already sends any
provider registered in `_OPENAI_COMPAT_PROVIDERS` through `OpenAiClient`
and stamps `client.provider_name` so error cards say "Gemini" or "Groq"
instead of "OpenAI".

### Error-card provider nudges

When a specific provider is known to hit 429s often, the
`rate_limited` branch of `_renderChatErrorCard` in
`topology/topology-ai.js` can add a **tertiary** action that suggests
the friendly parallel provider. Today: if the current provider is
`groq`, the card offers "Or try Gemini (free, separate quota)" which
opens the settings panel on click. The tertiary slot uses the ghost
tiny-button style so it reads as a subtle nudge and doesn't compete
with the primary Retry button. Add more nudges as the matrix grows
(e.g. Gemini 429 -> suggest Cerebras once that's added).

### Key-prefix detector

`_detectProviderFromKey` in `topology-ai.js` must list the most-
specific prefix first. `sk-ant-` is a strict subset of `sk-`, so
Anthropic must come before OpenAI. `AIza` / `gsk_` are unambiguous,
they can go in any order relative to the `sk-` family.

### Files to bump on every addition

- `topology/ai/service.py` (both tables)
- `topology/topology-ai.js` (preset + prefix detector)
- `topology/index.html` (`topology-ai.js?v=` cache-buster)
- `/home/dn/CURSOR/*` mirrors of all three
- This file (document the provider-specific quirks)

### Verification

1. Open AI drawer -> provider dropdown lists the new provider with
   its curated model list.
2. Paste a correctly-prefixed key into the wrong provider slot ->
   settings panel surfaces the "Switch to X?" nudge.
3. Send a prompt -> reply arrives; model badge says the new model;
   if the provider 429s, the error card says "Rate limit hit on
   \<provider\>" (not "Rate limit hit on OpenAI").

## Canvas link drawing: overlap-boundary rim

**Problem:** When two links share (a) the same colour and (b) (nearly)
the same geometry -- the common case is a pair of iBGP or eBGP links
between the same two devices -- the second link paints directly over
the first and the pair becomes visually indistinguishable. The user
sees one fat stroke where they actually have two parallel links.

**Solution:** In `drawLink()` in `topology/topology-link-drawing.js`
(both the bound-link and unbound-link code paths carry a copy; keep
them in sync), stroke a slightly wider **rim** in a darkened version
of the link's own colour BEFORE the main stroke. When a second link
is drawn on top, its rim overpaints the first link's body on the
outer edge, leaving a thin darker band that reads as the seam between
the two. Isolated (non-overlapping) links just get a subtle darker
outline which actually improves definition on busy canvases.

```js
// Pre-main-stroke rim:
if (isSolidStyle && !isSelected && !skipHighlight && !link._xrayCaptureActive) {
    editor.ctx.save();
    editor.ctx.strokeStyle = darkenColor(linkColor, 0.35);
    editor.ctx.lineWidth = linkWidth + 1.4;
    editor.ctx.shadowBlur = 0;
    editor.ctx.stroke();
    editor.ctx.restore();
    editor.ctx.strokeStyle = linkColor;  // re-assert, restore() rolled them back
    editor.ctx.lineWidth = linkWidth;
}
editor.ctx.stroke(); // existing main stroke
```

### Opt-out matrix (WHY each branch is excluded)

| State                      | Why no rim                                        |
| -------------------------- | ------------------------------------------------- |
| `isSelected`               | Already has a glow + thicker selection stroke.    |
| `skipHighlight` (in-edit)  | User is previewing actual colour -- no decoration.|
| `link._xrayCaptureActive`  | Already wears the cyan dashed x-ray halo.         |
| `linkStyle = 'dashed'/'dotted'/'dashed-wide'` | Rim blurs the dash rhythm. |
| `dashed-arrow` etc.        | Same as dashed.                                   |

### Colour choice

We reuse the module-level `darkenColor(hex, 0.35)` helper exported from
`topology-device-styles.js` (same ratio used for device body shading).
This gives a rim that stays in the link's hue family so it reads as a
"slightly deeper" version of the line rather than a stranger-colour
outline. `darkenColor` is already hardened against `undefined` inputs
(from the 2026-04-21 crash-storm fix) so no extra guard needed.

### Width choice

`linkWidth + 1.4` (a 0.7px rim on each side) is the sweet spot in our
bench: visible enough to make overlap seams readable even at 50% zoom
(where canvas sub-pixel rounding collapses anything thinner), subtle
enough that a single isolated link doesn't look "outlined". Scale stays
correct because ctx is already in world coordinates when `drawLink` runs.

### Verification

1. Create two BGP links between the same pair of devices with the same
   colour -> they show a visible dark seam where they overlap.
2. Select one of them -> the rim disappears for that link and the
   selection glow takes over; the OTHER link still has its rim.
3. Switch a link to dashed -> rim disappears (no muddy gaps between
   dashes).
4. Zoom to 300% and back to 50% -> rim stays at a consistent visual
   weight (it's stroked in world coords).
5. Toggle x-ray on a link -> cyan halo owns the decoration; the rim
   steps aside.

## Deploy-wide shared AI key: `GEMINI_API_KEY` (force-override mode)

Per-user AI keys (each user pastes their own `AIza...` into the GUI)
always work, but when the operator exports `GEMINI_API_KEY=AIza...` in
the topology-app server environment, the deployment enters
**force-override mode**: every user sees and uses Gemini, regardless
of what's stored in their per-user `ai_config.json`. This solves the
"I set GEMINI_API_KEY but my users still see their old Groq/Llama
config" problem that the reorder alone did not fix (reordering only
affects the dropdown default for users who have never saved a config).

### What the override actually does

1. **Resolver** (`ai/service.py::resolve_client_for_user`). When
   `GEMINI_API_KEY` is set, the resolver returns a Gemini
   `OpenAiClient` regardless of `cfg["provider"]`. The stored
   `cfg["model"]` is preserved **only** when it's already a Gemini
   model id (so users who picked `gemini-2.5-pro` keep it); otherwise
   we fall back to the canonical `gemini-2.5-flash`. A user's personal
   `AIza...` key (stored config with `provider=gemini` + non-placeholder
   api_key) is the single exception and continues to take precedence
   over the shared key.

2. **Config GET** (`serve.py::_handle_ai_config_get`). Mirrors the
   resolver's decision so the GUI display stays consistent with the
   actual LLM calls. Returns
   `{provider: "gemini", model: "gemini-2.5-flash", token_hint:
   "(shared server key)", shared_gemini: true, forced: true}` when
   override applies. No `configured: false` state is ever returned
   under force mode -- the Gemini provider is always configured via
   the shared key, even for first-time users, so the "Quick-start"
   hero stays out of the way.

3. **Config PUT** (`serve.py::_handle_ai_config_put`). Rejects
   non-Gemini saves with HTTP 409 and an explanatory error so users
   see "Locked to Gemini by server admin" in the config panel's
   error box instead of a silent override. Gemini saves (including
   picking a specific Gemini model or pasting a personal AIza key)
   always succeed.

4. **Frontend** (`topology-ai.js`). Mirrors the `forced` flag into
   `_aiConfig.forced`. When true, `_renderConfigPanel` renders a
   small blue info banner at the top of the drawer ("This deployment
   is locked to Google Gemini via a shared server key...") and adds
   `disabled` to the provider `<select>` so users can't even try to
   pick Anthropic / OpenAI / Groq / Ollama. The model `<select>`
   stays enabled so users can still switch between Gemini variants.

### The config stored on disk is never rewritten

The override is deliberately read-only from the per-user config's
perspective: if a user had `provider=groq, api_key=gsk_...` saved
before the admin exported `GEMINI_API_KEY`, their file keeps that
content. Removing the env var and restarting the service instantly
restores their old Groq config without a migration step. This is a
feature, not an oversight -- it lets admins try force-override mode
and roll back cleanly.

### Config PUT is still useful under force mode

- User picks a different Gemini model (`gemini-2.5-pro` etc.) and
  saves -> works, their stored `cfg["model"]` is what the resolver
  uses next call.
- User pastes their own `AIza...` key -> works, they now use their
  personal quota instead of the shared one. The resolver's
  "preserve personal Gemini config" exception fires.
- User tries to save Anthropic -> HTTP 409, error card explains.

### Fallbacks / edge cases

- User's stored provider is already `gemini` with empty key +
  `GEMINI_API_KEY` removed later -> resolver returns empty key,
  OpenAiClient issues a clean 401 from Google, the error card
  prompts "paste your own AIza key".
- `"__server_shared__"` placeholder is stripped in the resolver
  before being sent as a Bearer token, so Google never sees a
  bogus header.
- `_ai_mask_key` in `serve.py` renders "(shared server key)" for
  the placeholder so the GUI's "Current:" banner reads naturally
  instead of `__se...red__`.

### Files involved when wiring this for a second provider (e.g.
### Cerebras)

The same force-override pattern can be applied to any future
free-tier provider; rename `GEMINI_API_KEY` -> `CEREBRAS_API_KEY`
and `"gemini"` -> `"cerebras"` throughout the following touchpoints:

- `topology/ai/service.py::resolve_client_for_user` -- the
  `shared_gemini` branch at the top, plus the placeholder-stripping
  inside the `_OPENAI_COMPAT_PROVIDERS` fallback.
- `topology/ai/service.py::_read_ai_config` -- allow empty
  `api_key` when the provider's shared-key env var is set.
- `topology/serve.py::_handle_ai_config_get` -- the `forced` +
  `shared_gemini` response fields.
- `topology/serve.py::_handle_ai_config_put` -- accept empty
  `api_key`, reject non-target-provider saves with 409.
- `topology/serve.py::_ai_mask_key` -- render
  "(shared server key)" for the `"__server_shared__"` placeholder.
- `topology/topology-ai.js::_probeAiConfig/_saveAiConfig/_deleteAiConfig`
  -- mirror the flag.
- `topology/topology-ai.js::_renderConfigPanel` -- render the lock
  banner and disable the provider select when `forced=true`.

### Files touched when adding a new shared-key provider

- `topology/ai/service.py`
  - `_read_ai_config` -- allow empty `api_key` when the provider's
    shared-key env var is set.
  - `resolve_client_for_user` -- swap placeholder / empty for the
    env-var key.
- `topology/serve.py`
  - `_handle_ai_config_put` -- accept empty `api_key` and stash the
    `"__server_shared__"` placeholder.
  - `_handle_ai_config_get` / PUT response -- expose the `"shared_X"`
    boolean so the GUI can pick its hero variant.
  - `_ai_mask_key` -- render "(shared server key)" for the
    placeholder.
- `topology/topology-ai.js`
  - `_probeAiConfig` + `_saveAiConfig` + `_deleteAiConfig` -- mirror
    `shared_X` into `_aiConfig`.
  - `_renderConfigPanel` -- emit a new quick-start variant.
  - Quick-start click handler -- save with empty `api_key`.

### Verification

1. `unset GEMINI_API_KEY; systemctl restart topology-app` ->
   `/api/users/me/ai-config` returns `shared_gemini: false`, GUI
   shows the Ollama hero.
2. `export GEMINI_API_KEY=AIza_real_key; systemctl restart topology-app`
   -> endpoint returns `shared_gemini: true`, GUI shows
   "Use Gemini now" hero.
3. Click it -> config saves without a key, toast "Gemini ready",
   next prompt returns a real Gemini response (check `provider_name`
   in the server log).
4. `unset GEMINI_API_KEY; systemctl restart topology-app` again --
   same user now gets a 401 error card with "Paste your Google
   Gemini key" instead of a silent "not configured" banner.
5. Paste a personal `AIza...` key -> the personal key wins even if
   `GEMINI_API_KEY` is later re-exported.

## AI topology generation -- smart auto-layout + blueprint library (2026-04-21p)

### Problem

Users reported: "AI topologies are not that consistent with loading the
newly created topologies, also the topology spread should be better
with more real-life or professional scenarios creation."

Investigation of `/home/dn/.topology_users/<user>/sections/__ai/*.json`
showed the root cause: LLMs (Groq/OpenAI/Anthropic/Gemini) frequently
emit the `create_topology` tool call with devices that have only
`id` + `label` + `type` -- no `x` / `y` at all, or (0, 0) as a "don't
know" marker.

Loaded onto the canvas, `loadTopologyFromData` falls back to a dumb
5-wide linear grid (`200 + index*150`), which produces unreadable
layouts where spines are mixed with leaves in the same row, rings look
like paths, and hub-spoke looks like a line. Every `Save + Load`
produced a fresh mess that appeared random because different LLMs emit
different (missing) coordinate sets.

### Fix (five layers)

1. **Server-side smart auto-layout** in `topology/ai/context.py`
   (`_apply_layout` + helpers). When the LLM omits coordinates, the
   backend detects the topology shape from:
   - **Explicit `layout_hint`** in the tool call (winning signal).
   - **Role labels** on devices: `super-spine`, `spine`, `leaf`, `rr`,
     `p`, `pe`, `ce`, `core`, `dist`, `access`, `border`.
   - **Graph shape**: ring (every node degree 2 + single cycle),
     simple path, hub-and-spoke (one node has N-1 edges), bipartite
     (CLOS-3-stage fallback).
   - Order of detection matters: specific shapes (ring, path, star)
     beat role-based tiering (otherwise a PE-P-P-PE chain renders as
     CLOS-3 because the labels say so).

   Layouts available:
   - `clos-3-stage` -- 2 rows (spines top, leaves below)
   - `clos-5-stage` -- 3 rows (super-spines / spines / leaves)
   - `sp-backbone` -- 4 rows (RR / P / PE / CE)
   - `campus` -- 3 rows (core / dist / access)
   - `dual-homed` -- 2 rows (PEs on top, CE(s) below)
   - `hub-spoke` -- hub in centre, spokes on a circle
   - `ring` -- devices on a circle
   - `path` -- horizontal left-to-right line
   - `tree` -- BFS-layered from highest-degree root
   - `mesh` -- circle (every peer equidistant)
   - `metro-ring` -- alias of ring
   - `auto` -- detect from graph

   Hand-placed devices are preserved; only `x`/`y`-less or (0,0)
   devices are auto-positioned. When some are hand-placed and some
   are not, the unplaced group is gridded BELOW the existing cluster
   so they don't overlap.

2. **Tool schema tightening** (`TOPOLOGY_TOOL_SCHEMA` in
   `topology/ai/context.py`):
   - Added `layout_hint` enum (12 values) with a clear description of
     what each one does.
   - Added `realism_scale` enum (small/medium/large/enterprise) for
     device-count scaling.
   - Added `role` field on devices so the LLM can tier them.
   - Clarified `x`/`y` descriptions (canvas world coords, 100..2400 x,
     100..1400 y, >= 180 px spacing).
   - Tightened top-level description: stacking everything at (0,0) is
     treated as "unpositioned".

3. **Knowledge digest rewrite** (`topology/ai/knowledge.md`):
   Added a comprehensive "Topology blueprint library" section with 12
   professional scenarios: CLOS 3-stage / 5-stage DC fabric, SP MPLS
   backbone with route reflectors, EVPN-VPLS multihoming with ESI,
   EVPN-VPWS seamless integration, dual-homed CPE, IXP peering fabric,
   metro Ethernet ring (G.8032), campus hierarchy, DCI, remote PoP
   with diverse uplinks, 4-PE protection ring.

   Each blueprint lists: roles, label patterns, link types, recommended
   `layout_hint`, and scale guide (small -> enterprise device counts).

   Also updated "Answering rules" to require `role` on every device,
   labels that match real-operator conventions (`PE-1` not `router1`),
   and professional link labels (`"100G /31 ebgp"`).

4. **Post-load canvas centring** in `topology/topology-ai.js`
   (`_loadSavedTopology`). After `loadTopologyFromData`, call
   `editor.centerOnDevices()` so the freshly-loaded topology is framed
   in the viewport -- without this, the user's pan/zoom from the last
   canvas leaves the new topology off-screen, which feels exactly like
   "the topology didn't load".

5. **Dropdown refresh** in `topology/topology-ai.js`
   (`_loadSavedTopology`). Replaced the bespoke `/api/sections` +
   `_renderCustomSectionsInDropdown` shim with
   `FileOps.loadCustomSections(editor)` so the AI domain's
   `topology_count` updates immediately and the new AI file appears in
   the Topologies menu without a browser reload.

### Files touched

- `topology/ai/context.py` -- `_apply_layout` + 12 helper layouts,
  `TOPOLOGY_TOOL_SCHEMA` (added `layout_hint`, `realism_scale`,
  `role`), `normalize_topology_payload` (calls `_apply_layout`).
- `topology/ai/knowledge.md` -- Layout section + Blueprint library.
- `topology/topology-ai.js` -- `_loadSavedTopology` now centres the
  view and uses `FileOps.loadCustomSections`.
- `topology/index.html` -- cache-buster `topology-ai.js?v=20260421p`.

### Verification

1. Ask the AI drawer: `"build me a 4-leaf 2-spine Clos"` -- the
   resulting `__ai/*.json` now has every device placed on two neat
   rows (spines y=200, leaves y=520) with 288 px gaps.
2. Ask for a metro ring of 6 switches -- devices render on a circle
   centred at (860, 600) with radius 260.
3. Ask for an SP backbone -- RRs on top, P routers one tier down, PEs
   below, CEs at the bottom. All four tiers centred on the widest.
4. Check `/home/dn/.topology_users/<user>/sections/__ai/<file>.json`
   -- every device has a numeric `x` and `y`, no (0, 0) stacks.
5. After `Save + Load`, canvas is centred on the new topology; the
   Topologies dropdown shows the new AI file immediately.

### Process restart required

Because `serve.py` imports `TOPOLOGY_TOOL_SCHEMA` and
`normalize_topology_payload` once (and Python caches modules in
`sys.modules`), the running backend keeps the old schema/layout until
`serve.py` is restarted:

```bash
pkill -f '/home/dn/CURSOR/serve.py'
cd /home/dn/CURSOR && python3 serve.py &
```

The knowledge digest re-reads on mtime change -- that alone takes
effect without a restart, but the tool schema does not.

### Pill-vs-canvas desync after loading a smaller topology (2026-04-22)

**Symptom.** User loads an AI-generated topology (e.g. "Two_Routers",
3 objects) on top of a larger canvas (15+ objects). Canvas
immediately shows the new topology; pill at bottom-left updates to
"Two_Routers". They refresh the browser. After the refresh, the
**canvas shows the OLD 15-object topology but the pill still reads
"Two_Routers"**. Same bug reproduces on any "Load" operation that
pulls in a smaller topology: AI-tool-card load, Topologies dropdown
navigation, shared-in inbox open, uploaded JSON.

**Root cause.** Two independent `localStorage` keys must stay in
sync, but only one was being updated on explicit loads.

| Key | What it stores | Updated by |
|---|---|---|
| `topo_active` | `{name, domain, color, sectionId}` -- drives the pill on refresh via `FileOps.restoreTopologyIndicator` | `FileOps.updateTopologyIndicator`, called directly by every load path |
| `topology_autosave` | `{objects, metadata}` -- drives local crash recovery via `TopologyEditor.loadAutoSave` | `TopologyEditor.autoSave`, called via debounced `scheduleAutoSave` after every `saveState` |
| Active server topology | Canonical per-user/domain topology row, including shared-write topologies | `FileOps._schedulePersistentAutoSave(...)`, triggered from `TopologyEditor.autoSave` and routed through `TopologySync.saveActive(...)` or `_sectionSaveWithConflict(...)` |

**Persistent autosave contract (2026-05-13):** localStorage autosave is not
enough for normal topology editing because refresh/dropdown reloads often pull
from the backend row. Every editor autosave must schedule a debounced persistent
save for the active topology when the user has a write target. Use the same
conflict-safe paths as the Save button (`TopologySync.saveActive` for
multi-user rows, `_sectionSaveWithConflict` for legacy section files). On
conflict, stop background autosaves and show the stale-save banner; never
silently force-overwrite a collaborator or another tab.

**Self-save echo guard (2026-05-13):** live-sync events from the SSE/WS bus echo
back to the tab that saved. `TopologySync` must identify the current user through
`TopologyAuth.getCurrentUser().username` and treat matching `actor_user` events
as self echoes: update only the base `updated_at`, never reload the canvas or
toast "`updated -- canvas refreshed`". Otherwise autosave can see its own save as
a collaborator update and enter a save -> event -> reload loop.

**Supervisor child-log guard (2026-05-13):** `serve.py` must not launch
long-running child services (`discovery_api.py`, `scaler_bridge.py` / uvicorn)
with `stderr=subprocess.PIPE` unless a reader thread drains that pipe for the
life of the process. Uvicorn writes operational logs to stderr; an unread pipe
can fill, block the bridge, and make `/api/domains` time out so the UI looks as
if topologies disappeared even though the per-user stores are intact. Redirect
child stdout/stderr to append-only log files instead.

**Topology MCP no-reload guard (2026-05-13):** the live `scaler_bridge` process
must not run uvicorn with `--reload`. `/mcp/sse` is a long-lived Cursor MCP
transport; uvicorn reload drops the child process whenever watched files change,
which disconnects Cursor and makes the Topology MCP appear to move down. The
`serve.py` monitor handles crash recovery, and deployments must restart the app
explicitly after syncing code.

**Topology MCP bug-topology tool (2026-05-13):** simplified Jira bug explanation
diagrams are created through the first-class `topology_create_bug_topology` MCP
tool. The tool must delegate to the existing per-user `/api/bugs/from-jira`
backend path so the GUI `+ Bug` flow and MCP flow share Jira parsing,
bug-issue-type gating, filename suffixing, and `__bugs` domain persistence. Do
not add a second bug-topology JSON writer or bypass per-user auth.

**Topology read fallback guard (2026-05-13):** the browser-facing `serve.py`
proxy must degrade read-only topology APIs locally when `scaler_bridge` is down
or slow. `GET /api/domains`, `GET /api/domains/{id}/topologies`, and
`GET /api/domains/{id}/topologies/{id}` can be answered from the same per-user
`user_store` SQLite files, so an auxiliary service outage must never make a
user's domains or topologies render as deleted.

**No bulk domain delete (2026-05-13):** deleting a domain/section that still
contains topology files is forbidden at every layer (`user_store`,
`/api/domains`, legacy `/api/sections`). Users must move or delete individual
topologies first. Domain deletion is for empty containers only; it must never
cascade-delete all topology rows as a convenience feature.

**Domain topology quota + cleanup (2026-05-13):** every per-user domain is
limited to 15 topology files. New saves/imports/bug-topology creation/moves
must return `code="domain-topology-limit"` with the current topology list when
the target domain is full. The only bulk deletion affordance is the explicit
"Clean" topology cleanup flow (`/topologies/cleanup`) that asks the user which
topology files to delete; it must not delete the domain container itself and
must keep mirror/share cleanup behavior equivalent to one-by-one topology
deletes.

**Frontend stale-list guard (2026-05-13):** domain/topology list refresh errors
must preserve the last known `editor._customSections` / `TopologyDomains` cache
and show a temporary-unavailable warning. Never replace a failed refresh with
`[]`, "No topologies", or a destructive-looking empty state.

**Topology transition contract (2026-05-13):** switching topologies or domains
must flush the currently opened topology to its own write target before the new
load token is created. Owned and write-shared topologies auto-save through
`_saveCurrentTopologyBeforeSwitch`; untargeted canvases still show the
Save/Discard prompt. Read-only shared-in topologies must never fall back to
legacy `/api/sections` saves.

**Current-topology clear contract (2026-05-13):** the top-bar Clear action is
scoped to the currently opened topology only. It preserves `topo_active`, clears
the canvas, then persists an empty snapshot with `allowEmpty`/`force` so a
refresh does not resurrect the old canvas. Clear must not delete, rewrite, or
detach any other topology in the same domain or in other users' domains.

**Destructive shortcut contract (2026-05-14):** `Cmd/Ctrl+X` is the
clear-current-topology shortcut. It is selection-agnostic and ALWAYS routes
through `editor.clearCanvas()` -- which delegates to
`FileOps._clearCurrentTopologyOnly(editor)` for the common case (an active
topology row is open). That helper:

1. Shows a `window.confirm("Clear \"<name>\" only? ...")` dialog whose body
   explicitly states "Other topologies and domains are untouched."
2. On accept, wipes the canvas, then writes an empty snapshot to ONLY the
   currently opened topology row (autosave + section save with
   `allowEmpty: true`). Other topologies, other domains, and shared-with-me
   views are not touched.
3. Pairs with the `_intentionalObjectCountDrop` window so the 70%-loss guard
   in `autoSave` does not block the empty save.

The shortcut handler in `topology-keyboard.js` MUST NOT duplicate the prompt
or call `performClearCanvas()` directly -- that bypasses the per-row save and
the user-visible scope warning. It also MUST NOT short-circuit when nothing
is selected (the previous "Select objects before cutting" toast was the bug
this contract replaces). The static check is in
`tests/test_device_onboarding_frontend_unit.py::test_cmd_x_clears_current_topology_with_confirmation`.

**History-restore minimap invalidation (2026-05-14):** any code path that
swaps `editor.objects` wholesale (undo/redo, history `restoreState`, topology
load) MUST drop the minimap render cache before scheduling the redraw:

```js
if (window.MinimapRender && typeof window.MinimapRender.invalidateCache === 'function') {
    window.MinimapRender.invalidateCache();
}
if (this.minimap) delete this.minimap._cachedBase;  // also reset zoom-anchored bounds
```

The minimap render layer (`topology-minimap-render.js`) keys its offscreen
canvas by a content hash + bounds key + dark-mode flag. In theory the hash
catches array swaps, but in practice undo can land on a hash that matches a
recently rendered state (especially when the only change between two history
steps is the count of one object class), and the cached offscreen canvas
gets reused. Forcing `_topoCacheHash = null` on every history restore makes
the next `renderMinimap` rebuild from scratch, which keeps the minimap in
sync with the main canvas after Cmd+Z / Cmd+Y.

**Topology switch error-path guard (2026-05-13):** every async topology-load
handler that calls `_beginTopologyLoad(...)` must declare its `loadToken` outside
the `try` block before any awaited fetch. The `catch` path must tolerate a null
token (`if (loadToken && ...)`) so failed own-domain loads do not throw
`ReferenceError: loadToken is not defined` and leave the previous canvas visible.

**Active indicator helper completeness (2026-05-13):** `FileOps.updateTopologyIndicator`
is on the critical topology-load path. Any helper it calls must be defined in the
same shipped `topology-file-ops.js` bundle and covered by a static regression
test. A missing optional UI helper (for example shared-by / View/Edit segments)
must not throw before `loadTopologyFromData` finishes replacing the canvas.

`loadTopologyFromData` (single entry point for all explicit loads)
did two things:
1. Replaced `this.objects` with the loaded data.
2. Called `this.saveState()` at the end, which triggers a debounced
   `scheduleAutoSave -> autoSave` after 100 ms.

`autoSave` has a 70%-loss guard at `topology.js::autoSave` that was
added (March 2026) to protect against accidental Ctrl+X / Delete
mass-deletion:

```js
const prevCount = this._lastSavedObjectCount || 0;
if (prevCount >= 5 && this.objects.length < Math.ceil(prevCount * 0.3)) {
    console.warn('[AutoSave] BLOCKED: object count dropped ...');
    return;
}
```

With `_lastSavedObjectCount = 15` (from the previous canvas) and a
new `this.objects.length = 3` (AI-generated 2-router topology),
the guard fires and `autoSave` returns without writing. So:

- `topology_autosave` keeps the old 15-object canvas.
- `topo_active` updates to `Two_Routers`.
- Refresh -> `loadAutoSave` restores the 15-object canvas,
  `restoreTopologyIndicator` restores the `Two_Routers` pill.
- Pill and canvas disagree. User sees "a different topology after
  refresh".

**Fix.** Re-baseline `this._lastSavedObjectCount` to the new
`this.objects.length` inside `loadTopologyFromData`, immediately
after the `this.objects = data.objects || []` assignment. The
debounced `autoSave` fires 100 ms later and now sees `prevCount =
newCount`, so the guard condition
`newCount < ceil(newCount * 0.3)` is always false and the save
proceeds. The guard still catches real mass-deletions performed
AFTER the load because every subsequent edit compares against the
fresh baseline we just set.

**File touched.** `topology/topology.js::loadTopologyFromData`,
plus the `topology.js` cache-buster in `topology/index.html`
(`?v=20260422a`). Mirrored to `/home/dn/CURSOR/`.

**Why not relax the guard instead?** The guard is correct for
edit-time mass deletions (its original purpose). Disabling it, or
lowering the 70% threshold, would re-introduce the data-loss class
the March 2026 fix closed. Re-baselining on explicit load is the
surgical fix: it preserves the guard for its actual threat model
while letting wholesale topology replacement write through.

**Verification.**

1. In Chrome DevTools -> Application -> Local Storage, copy the
   raw `topology_autosave` value (the "before" snapshot).
2. Build any 10+ object canvas (e.g. ask the AI for a "6-leaf
   2-spine Clos"). Hard-refresh and confirm both pill and canvas
   show that topology.
3. Ask the AI: `"build me a 2-router topology called Two_Routers"`.
   Click **Save + Load** on the tool card.
4. Hard-refresh (Ctrl+Shift+R so `?v=20260422a` is picked up).
5. Verify: pill reads "Two_Routers" AND canvas shows exactly two
   routers with the AI-generated link. No desync.
6. `localStorage.getItem('topology_autosave')` now reflects the
   2-router topology (objects.length === 3). The guard still
   blocks if you then delete the routers: in DevTools console run
   `for (const id of editor.objects.map(o=>o.id)) editor.deleteObject(id)`
   and watch the `[AutoSave] BLOCKED ...` warning in the console.

---

## 2026-04-20 – Cuter cloud avatars, liquid-glass user menu, tiered owner/admin actions

**Context.** User wanted cuter cloud-profile avatars, a prettier
"liquid glass" user dropdown, and extra capabilities for
**Yarel Or** (owner tier) that other users don't see.

### Cloud avatar pack (`topology-share.js`)

- `CLOUD_PALETTES` was widened to 14 pastel + dark-mode-tuned
  gradients (`lavender`, `peach`, `mint`, `sky`, `rose`, `sage`,
  `butter`, `periwinkle`, …) picked deterministically from a
  hashed username so the same user always gets the same cloud.
- The cloud silhouette was re-shaped from a 4-bump puff to a
  softer 7-bump form with a gentle underline shadow.
- Seven new face variants were added on top of the originals:
  `wink`, `uwu`, `giggle`, `starry-eyes`, `sleepy`,
  `cool-shades`, `kiss`, each with blush dots and a tiny eye
  sparkle highlight.
- `_cloudAvatarSVG(name, { sparkle, bounce, breathing })`
  now emits extra SVG layers and CSS-animation classes; all
  motion is gated behind `prefers-reduced-motion: reduce`.

### Liquid-glass dropdown (`styles.css`)

- `.auth-user-dropdown` is now a 26px `backdrop-filter: blur()`
  + `saturate(200%)` panel with a 1px rim highlight (`::before`
  gradient) and a soft outer glow (`::after`), a role-colored
  left accent stripe (owner/admin/manager/user), and a
  scale+fade open animation.
- Dropdown header uses the bigger animated avatar, an
  online-status dot, and role-themed glow.
- Menu items have a hover sheen (translating gradient), icon
  bounce, and focus rings for keyboard nav.

### Role flags end-to-end

- `api/auth/service.py` now exports `is_owner_user(username,
  display_name)` which matches the literal `yarel`, a
  display-name of `Yarel Or`, **or** whatever is set in the
  `OWNER_USERNAME` env var. It's also marked True for the
  built-in single-user default identity so local dev keeps
  full access.
- `require_owner()` FastAPI dependency gates owner endpoints.
- `api/auth/schemas.py` extends `LoginResponse` + `UserInfo`
  with `is_admin` and `is_owner`; `router.py` fills them on
  `/login` and `/me`.
- Frontend `topology-auth.js` stores `_currentUser.is_admin` /
  `is_owner` and uses them to render menu tiers.

### Menu tiers (`topology-auth.js`)

Regular user sees Profile / Settings / Theme / Sign out.
**Admin** additionally gets:

- Server Diagnostics (GET `/api/admin/diagnostics`)
- AI Shared-Key Status (GET `/api/admin/shared-key-status`)
- Recent Activity / Audit Log (GET `/api/admin/audit`)
- Broadcast Announcement (POST `/api/admin/broadcast`)
- Feature Flags (GET + PUT `/api/admin/feature-flags`)
- Reload AI Knowledge (POST `/api/admin/reload-knowledge`)

**Owner (Yarel Or)** additionally gets:

- Impersonate / View-as (cosmetic only – updates the
  in-memory `_currentUser` view but the backend still sees
  the real JWT identity)
- Reset All AI Configs (POST `/api/owner/reset-configs` – wipes
  persisted AI knowledge and resets feature flags to defaults)
- Restart Server (POST `/api/owner/restart`, env-gated by
  `ALLOW_OWNER_RESTART=1` so a random click can't kill prod)

Keyboard nav: Enter opens, Esc closes, Up/Down cycles, and
first item is focused on open. All items have `role="menuitem"`
and the panel is `role="menu"`.

### Backend plumbing (`serve.py`)

- New thread-safe in-memory `_ADMIN_AUDIT_RING` (last 500
  events) plus a persisted `feature-flags.json` sidecar.
- Helpers `_require_auth`, `_require_admin`, `_require_owner`,
  and `_record_audit(event, username, meta)` on the `Handler`.
- Every new admin/owner call is audited with the actor's
  username so the audit log is the source of truth for
  who-did-what.
- `_is_owner_user()` mirrors the API logic so HTTP-only paths
  (legacy fetches) still honor the owner rules.

### Announcement broadcast flow

- `POST /api/admin/broadcast { title, message, level }` appends
  to the shared list (max 50 kept).
- Every logged-in client long-polls `GET /api/admin/announcements`
  every 30s, deduplicates by announcement `id`, and shows a
  toast. New messages reach every connected browser within
  one polling window.

### Cache-buster + mirror

- `index.html` bumped `topology-auth.js`, `topology-share.js`,
  and `styles.css` to `?v=20260420a`.
- All eight changed files (`serve.py`, `api/auth/service.py`,
  `api/auth/router.py`, `api/schemas.py`, `topology-auth.js`,
  `topology-share.js`, `styles.css`, `index.html`) were
  mirrored to `/home/dn/CURSOR/` so the deployed copy stays
  in lock-step with the working tree (per the project
  `worktree-deploy-sync` rule).

### Verification checklist

1. Hard-refresh (`Ctrl+Shift+R`) and confirm the user button
   now shows a cute animated cloud with a pastel gradient
   and sparkles (unless `prefers-reduced-motion`).
2. Click it – the panel should fade/scale in with a glassy
   blur and a role-colored stripe on the left.
3. Sign in as **Yarel Or** and confirm three sections are
   visible in the dropdown: user / admin / owner (with the
   Impersonate, Reset Configs, Restart Server entries).
4. Sign in as any other user and confirm only the user
   section shows.
5. Open an incognito window signed in as user B; as admin
   click **Broadcast Announcement**, send a message, and
   verify user B sees a toast within 30s.
6. `tail -f` the server log while clicking each admin/owner
   action; every call should log an audit entry like
   `audit: broadcast user=yarel`.

## Domain Knowledge -- Per-Domain Project Workspace (2026-04-19)

A topology domain used to be just a folder of topology files. The domain
knowledge layer turns each domain into a small project workspace that can
attach feature branches to monitor, Jira EPICs, CLI presets, test-suite
links, notes, and more. Every addition is per-user, with a hybrid-sharing
model so some knowledge "travels" with a domain share and some stays
private to the viewer.

### Files

| Layer | Path |
|---|---|
| Backend storage | `topology/api/auth/user_store.py` -- `domain_knowledge` table + hybrid CRUD (`resolve_domain_scope`, `list_domain_knowledge`, `upsert_domain_knowledge`, `delete_domain_knowledge`, `list_all_public_knowledge_rows`, `update_public_knowledge_payload`, `domain_viewers`) |
| Kind registry | `topology/api/domains/knowledge.py` -- 10 kinds with validators / key extractors / live fetchers |
| REST router | `topology/api/domains/knowledge_router.py` -- mounted under `/api/domains/{domain_id}/knowledge` |
| Background poller | `topology/api/domains/knowledge_poller.py` -- async task per live kind, dedup by natural key |
| Frontend module | `topology/topology-domain-knowledge.js` -- inline expand-on-demand panel mounted in each domain row |
| Frontend wiring | `topology/topology-file-ops.js` `_renderCustomSectionsInDropdown` + `_renderSharedInSectionsInDropdown` (calls `TopologyDomainKnowledge.mount`) |
| Styling | `topology/styles.css` `/* Domain Knowledge Panel */` block near EOF |

### Registered Kinds

| Kind | Live | Key | Purpose |
|---|---|---|---|
| `branch` | yes (Jenkins) | `branch_name` | Monitor feature/dev/release branches -- build status, sanitizer flag |
| `jira_epic` | yes (Jira) | `issue_key` | Pin a Jira EPIC or ticket; summary/status/assignee live |
| `test_suite` | yes (fs scan) | `suite_path` | Link into `scaler/TEST/catalog/<suite>/`; shows last 5 RUN_* results |
| `spirent` | yes (fs scan) | `session_path` | Spirent session file; stream/device counts |
| `device` | no | `device_id` | Explicit device roster for the domain |
| `note` | no | custom | Markdown runbook / scratchpad |
| `confluence` | no | `url` | External / Confluence spec URL |
| `cli_preset` | no | `query` | Pinned DNOS `search_cli_docs` query or show command |
| `bugs_scope` | no | (single) | Scope the `__bugs` built-in section to this domain |
| `ai_scope` | no | (single) | Pinned AI prompt + chat ids for this domain |

### Hybrid Sharing Model

Each row carries a `visibility` flag:

- `public` -- stored in the **owner's** DB. Travels with the domain share.
  Recipients READ them by default, WRITE them only with `permission='write'`.
- `private` -- stored in the **viewer's** DB, keyed with a composite
  `<owner>:<domain_id>` so the viewer's annotations on someone else's
  domain never collide with a same-id domain in the viewer's own workspace.

`user_store.resolve_domain_scope(viewer, domain_id)` returns the full
scope (owner, permission, which DB to read/write for each visibility).
The knowledge router calls it before every operation so the UI never has
to know which DB the row actually lives in.

### REST API

```
GET    /api/domains/knowledge/kinds                           # discovery
GET    /api/domains/{domain_id}/knowledge                     # merged list
POST   /api/domains/{domain_id}/knowledge                     # add
PUT    /api/domains/{domain_id}/knowledge/{kind}/{key}        # update
DELETE /api/domains/{domain_id}/knowledge/{kind}/{key}        # delete
POST   /api/domains/{domain_id}/knowledge/reorder             # bulk reorder
POST   /api/domains/{domain_id}/knowledge/{kind}/{key}/refresh# force live fetch
POST   /api/domains/{domain_id}/knowledge/refresh-all         # refresh all live rows
```

### Background Poller

`knowledge_poller.KnowledgePoller` runs one asyncio task per enabled kind
(see `DEFAULT_INTERVALS`: branch=180s, jira=300s, test_suite=120s,
spirent=300s). Polling is dedup'd by natural key across all users so
five users attaching the same branch still cause one Jenkins call.
When a delta is detected, the new payload is written back to every
owner's DB and a WebSocket event is fanned to every viewer of every
domain that holds the row.

Disable with `KNOWLEDGE_POLLER_KINDS=none`, or restrict to a subset:
`KNOWLEDGE_POLLER_KINDS=branch,jira_epic`.

### WebSocket Event Contract

Live updates are published as:
```json
{
  "type": "domain.knowledge.updated",
  "domain_id": "<owner's raw id>",
  "kind": "branch",
  "key": "feature/dev_v26_2/foo",
  "visibility": "public",
  "payload": { ... refreshed ... },
  "source": "poller" | "router"
}
```

`topology-device-events.js` forwards all typed events as
`topology:event:domain.knowledge.updated` custom events; the frontend
module listens and reloads the affected panel.

### Frontend UX

Each domain row in the Topologies dropdown gets a small "knowledge"
icon-button slotted between the `+ Bug` button (when present) and the
chevron. Clicking it expands an inline settings-bar with tabs per kind,
an "add new" form at the bottom, and per-row refresh/delete actions.
The bar is designed to stay compact -- heavy editors (markdown notes)
expand vertically but never push into a separate modal.

Hybrid sharing is surfaced in the UI:

- Rows authored by the domain owner on a shared-in domain show a
  `shared` pill; the viewer's own annotations show a `private` pill.
- When the viewer has read-only share permission, the "add item"
  visibility select auto-defaults to `private` with a disabled
  `public` option and a tooltip explaining why.

### Cache-Buster Discipline

- `topology-domain-knowledge.js` -> `?v=20260419a` (new)
- `topology-file-ops.js` -> `?v=20260419a` (bumped for dropdown-wiring change)
- `styles.css` -> `?v=20260419a` (bumped for panel CSS block)

### When Extending

To add a new kind:

1. In `knowledge.py`, write a `_validate_<kind>` and optional
   `_fetch_<kind>_status`, then `register(KnowledgeKindSpec(...))`.
2. In `topology-domain-knowledge.js`, add a renderer to the `R` table
   with `renderItem`, `renderNew`, `readForm`, and an icon in
   `_kindIcon`.
3. If the kind is live, add its interval to
   `knowledge_poller.DEFAULT_INTERVALS` and a delta signature in
   `_delta_signature`.
4. If the kind is single-row per domain (like `bugs_scope`), add it to
   the `allows_multiple=False` branch in `knowledge_router.add_knowledge`
   and set `allowsMultiple: false` on the frontend renderer.
5. Bump all three cache-busters, sync to `/home/dn/CURSOR/`,
   verify with `curl http://localhost:8766/api/domains/knowledge/kinds`.

---

## 2026-04-22 hotfix – user menu polish + `_require_auth` shadow bug

**Symptoms reported.**

1. Console spam from `:8080/api/admin/announcements` returning `404`
   every 30 s on every client.
2. User pill in the top-right "doesn't look good before opening —
   should reflect the icon inside better".
3. AI badge still shows `groq / llama-3.3-70b-versatile` even though
   Gemini is supposed to be the deploy default.

**Root causes.**

1. `serve.py` defined a NEW `_require_auth(self)` at line 3604 that
   returned `(username, role)`; the LEGACY `_require_auth(self)` at
   line 979 returns a bare `username` string and is used by ~20
   callers. Python keeps only the last definition on a class, so
   every legacy caller was broken. In addition, the running server
   at `/home/dn/CURSOR/serve.py` was started before the new
   `/api/admin/*` + `/api/owner/*` routes were merged — hence the
   404 spam.
2. `_updateUserMenu` double-wrapped the pill avatar: it took the
   `<span class="cloud-avatar">` emitted by `CloudAvatar.html` and
   stuffed it inside an extra `<div class="auth-avatar
   auth-avatar-cloud">`, which collided with the nested-svg CSS
   and clipped the hover-bounce transform.
3. User's per-user config `~/.topology_users/yarel/ai_config.json`
   was stored as `{provider: "groq", model: "llama-3.3-70b-versatile",
   …}`. The shared-Gemini override in `ai/service.py`
   `resolve_client_for_user` only force-switches when
   `GEMINI_API_KEY` is exported in the server env, and that env
   var wasn't set.

**Fixes.**

- Renamed the new helper to `_require_auth_role()` so it no longer
  shadows the legacy `_require_auth()`; updated the three internal
  callsites (`_require_admin`, `_require_owner`,
  `_handle_announcements_get`). Do NOT unify the two without
  auditing every legacy caller first — see the leading comment
  at `serve.py:~3590`.
- In `_updateUserMenu`, stopped wrapping `CloudAvatar.html()` in
  an outer `<div class="auth-avatar">`; added a sibling
  `.auth-user-pill__halo` span behind the avatar; and switched
  the avatar opts to `{ bounce: true, breathing: true }` so the
  closed-state avatar breathes while idle.
- New CSS block in `styles.css` (2026-04-22 comment) reworks
  `.auth-user-pill`:
  - Rounded capsule with glassy gradient + `backdrop-filter:
    blur(10px) saturate(140%)`.
  - `data-palette` attribute maps to a per-palette radial-gradient
    halo (one rule per `CLOUD_PALETTES.name`) so every user's pill
    glows in the same pastel as their cloud.
  - `data-role` attribute drives the `--auth-pill-role-rgb`
    custom property used by the `:focus-visible` ring, so keyboard
    users see a role-coloured highlight (gold for owner, red for
    admin, etc.).
  - `aria-expanded="true"` lifts the pill's background so it reads
    as "active" while the dropdown is open.
- In `topology-auth.js`, `_pollAnnouncementsOnce` now checks for
  HTTP 404 and self-disables the polling interval on first 404.
  The setInterval is cleared, so if a client connects to a legacy
  server it logs one `404` and then never re-queries, keeping
  devtools quiet.
- Rewrote `~/.topology_users/yarel/ai_config.json` to
  `{provider: gemini, model: gemini-2.5-flash, api_key: ""}` (old
  groq config saved to a timestamped `.bak-before-gemini-swap-*`
  file in the same directory). A blank api_key drops the user
  back into the Quick-start hero — if `GEMINI_API_KEY` is ever
  exported, the shared-key path kicks in automatically.
- Bumped `styles.css` / `topology-auth.js` / `topology-share.js`
  cache-busters from `?v=20260422a` / `?v=20260419a` (for css)
  to `?v=20260422b`, mirrored everything to `/home/dn/CURSOR/`,
  killed the stale PID 3054637 and relaunched.

**Verification (what a fresh `Ctrl+Shift+R` should now show).**

1. `curl -s http://127.0.0.1:8080/api/admin/announcements` returns
   `401 {"error":"Authentication required"}` — NOT 404.
2. The top-right user pill has a pastel halo matching the cloud
   avatar and breathes subtly while idle; hover bumps the avatar
   and lifts the pill 1px; keyboard `Tab` shows a role-coloured
   focus ring; clicking opens the glass dropdown.
3. AI Assistant badge in the chat side-panel reads `Gemini /
   gemini-2.5-flash` (or prompts you to paste an `AIza…` key if
   `GEMINI_API_KEY` isn't exported).
4. No red `404` lines in devtools → Network for
   `/api/admin/announcements`; one-shot probe from a legacy server
   silently disables further polling instead of spamming.

## 2026-04-22 — Leader menu contrast + admin dialog audit + real view-as

**User pain.** The leader dropdown read like "peach black" because
legacy inline `color:#fff` / `opacity:0.65` styles cumulatively
darkened the text on the glass panel. Admin dialogs had the same
issue, plus "View as user" was cosmetic-only (pill swap) — it did
not actually let the leader see what another user sees.

**Edits (workspace → live).**

- `topology/styles.css`:
  - New `.auth-admin-card` scope with dark- and light-mode
    contrast floors so every admin dialog body text stays
    ≥ WCAG AA regardless of legacy inline color/opacity.
  - Semantic helper classes `auth-admin-status-ok`, `…-warn`,
    `…-err`, `.auth-admin-muted`, `.auth-admin-note`,
    `.auth-admin-label`, `.auth-admin-ghost`, `.auth-admin-toolbar`,
    `.auth-admin-search`, `.auth-admin-search-count` — all
    dark/light-mode aware. The JS dialogs use these instead of
    inline `style="color:#fff;opacity:.65"`.
  - `.auth-viewas-layout` + `.auth-viewas-pane{, -head, -body}` +
    `.auth-viewas-item` + `.auth-viewas-topo-row` +
    `.auth-viewas-banner` for the new workspace-browser dialog
    and the red view-only banner that sits on the canvas.
  - Light-mode overrides for `.auth-dropdown-section-label--admin`,
    `--owner`, `.auth-dropdown-danger`, `.auth-dropdown-owner`
    and their icons, so the leader dropdown is readable on the
    white card too.

- `topology/topology-auth.js`:
  - All admin dialogs (Server Diagnostics, AI Shared-Key Status,
    Recent Activity, Broadcast Announcement, Feature Flags,
    Reload AI Knowledge, Reset All AI Configs, Restart Server)
    moved to a shared `_openDialogShell(title, html, {id, width})`
    helper that emits `.auth-login-card.auth-admin-card` + a
    pill-shaped close button + Esc-to-close. Each dialog uses
    the new `_adminLoading(label)` / `_adminError(msg)` /
    `_adminToolbar(left, right)` / `_adminGhostBtn(id, label)`
    helpers so every "Refresh" / "Dismiss" / "Copy" button is
    theme-aware and consistent.
  - User Management dialog now has a live **search bar**
    (`#auth-users-search`) filtering by username, display name,
    email, or role; `.auth-admin-search-count` shows
    `<matched>/<total>`. The dialog state (`_usersDialogState`)
    holds the loaded users and current filter so search is
    purely client-side and instant.
  - New owner-only **"View"** button in the users table
    (visible only to the deployment owner) closes the users
    dialog and opens the workspace browser pre-selected to
    that user in 60 ms.
  - **View-as dialog** (`_showImpersonateDialog`) completely
    rebuilt as a two-pane workspace browser:
    - Left: searchable user list with cloud avatars.
    - Right on select: user dossier (role, joined, last seen,
      domain/topology counts), **Cosmetic preview** button
      (legacy pill swap), domains list, topologies list with
      a **Load (view-only)** button per topology.
    - Loading a topology posts to the new backend endpoint,
      clears the canvas, and shows a red `.auth-viewas-banner`
      with "Exit view-only" that resets the canvas.
    - State lives on `_viewAsState = { users, filter, selected,
      selectedUser, domains, activeDomain, topologies }`.

- `topology/serve.py`:
  - Owner-only GET endpoints under `/api/owner/view-as/` —
    gated by `_require_owner()` (same gate as Reset / Restart /
    Feature-Flag writes), every call is recorded via
    `_record_audit("view_as", ...)`:
    - `/api/owner/view-as/<user>/summary`
    - `/api/owner/view-as/<user>/domains`
    - `/api/owner/view-as/<user>/domains/<domain_id>/topologies`
    - `/api/owner/view-as/<user>/domains/<domain_id>/topologies/<topology_id>`
  - Route parser `_view_as_parse` blocks empty usernames,
    traversal sequences, and 404s unknown users up-front by
    consulting `user_store.get_user`.
  - Handlers delegate to `api.auth.user_store.user_store`
    methods (`list_domains`, `list_topologies`, `load_topology`)
    so the payload shape matches what
    `/api/domains/*` already returns for the signed-in user;
    the frontend reuses the same renderer code.

- `topology/index.html`: bumped `styles.css` + `topology-auth.js`
  cache-busters to `?v=20260422e` so browsers pull the fresh
  CSS + JS on next load.

**Deploy + verify (executed this session).**

1. `python3 -c "ast.parse(open('topology/serve.py').read())"` →
   `serve.py: OK`.
2. `node --check topology/topology-auth.js` → OK.
3. CSS brace balance (`{` vs `}`) → 2745 / 2745, diff 0.
4. Mirrored all four files to `/home/dn/CURSOR/` and confirmed
   `diff -q` is clean for each.
5. `systemctl --user restart topology-app.service` cleanly
   restarted serve.py + discovery_api + scaler_bridge; health
   endpoint returns `status=ok` for all three on ports 8080 /
   8765 / 8766.
6. Anonymous smoke test of the four new owner endpoints each
   returns `401 {"error":"Authentication required"}` — proving
   the routes are registered and the owner gate fires BEFORE
   any user-data handler runs.
7. Existing admin GETs (diagnostics, shared-key-status, audit,
   feature-flags, announcements) still return 401 unauth (i.e.
   no regression).

**Files touched this session:**

- `topology/styles.css` → `/home/dn/CURSOR/styles.css`
- `topology/topology-auth.js` → `/home/dn/CURSOR/topology-auth.js`
- `topology/serve.py` → `/home/dn/CURSOR/serve.py`
- `topology/index.html` → `/home/dn/CURSOR/index.html`

## 2026-04-23 — Domain row v2 + Manage-panel refactor

**Goal.** Refine "Domain control and settings per domain" across the
Topologies dropdown and the Manage Topology Domains panel: cleaner
chrome, direct-inline quick-edit, responsive sizing, active-row
indicator, topology-count badges, keyboard/ARIA nav, and a simpler
Add-New flow.

**What changed.**

- `topology/styles.css` — new `Domain row v2` block (ctrl-F
  "Domain row v2 -- redesigned per-row controls (2026-04-23)"):
  - Single `--row-accent` custom property per row (set by JS from
    `sec.color`) drives the entire palette: count badge tint,
    gear-button fill, quickedit border, action-button hover, and
    the `is-active` inner ring. No more JS hex-alpha concatenations
    for the common chrome.
  - `.domain-count-badge` (pill after the name; filled lazily by
    `_loadDomainTopologiesInline` with the topology count, hidden
    via `:empty` until the count resolves so there's no "0" flash).
  - `.domain-settings-btn` (reveal-on-hover gear; non-builtin only);
    `.is-open` holds the button in its hover state while its
    quickedit panel is mounted.
  - `.domain-quickedit` (inline name/icon/colour editor; same
    control grammar as the Manage-panel edit form).
  - `.domain-actions` / `.domain-action-btn` — Save/Load/Share
    restyled via CSS class states (`.is-pressed`) instead of inline
    JS onmouseenter/leave stanzas.
  - `.custom-section-category.is-active` — accent inner ring on the
    row whose sectionId matches the currently loaded topology.
  - `.domain-title:focus-visible` — accent outline for keyboard nav.
  - Container-query / media-query breakpoints (same pattern used by
    `.domain-newbug-btn`) collapse the action-button labels to
    icon-only when the dropdown is dragged narrow.

- `topology/topology-file-ops.js`:
  - `_renderCustomSectionsInDropdown` — row template rewritten:
    - Title becomes an accessible pseudo-button: `role="button"`,
      `tabindex="0"`, `aria-controls=domain-body-<id>`,
      `aria-expanded=<!collapsed>`.
    - Adds `.domain-count-badge`, `.domain-settings-btn` (gear; non-
      builtin), and keeps `.domain-newbug-btn` on the Bugs row.
    - Emits `.domain-actions` with three semantic buttons (Save /
      Load / Share) whose hover/press visuals are class-based.
    - Mouse toggle paths now also flip `aria-expanded` so screen
      readers stay in sync with visual state.
    - New `keydown` handler on the title: Enter / Space toggle,
      ArrowUp / ArrowDown move focus between rows, Home / End jump
      to the first / last row, Escape collapses the current row.
      All paths hit the same display / chevron / `_domainCollapsed`
      / `aria-expanded` / `_fitDropdownToContent` update the mouse
      path does.
  - `_openDomainQuickEdit(editor, sec, rowEl, settingsBtnEl)` — new:
    mounts an inline editor inside `.domain-body` for the row's
    name, icon, and colour, with live preview on the row chrome
    (left accent stripe, icon box, title) while the user types.
    Built-in domains keep name locked (same rule as Manage panel).
    Saves via `PATCH /api/sections/update` and refreshes the row
    without closing the dropdown.
  - `_loadDomainTopologiesInline` — after the topology list
    resolves, it also writes the count into
    `.domain-count-badge[data-count-for="<sec.id>"]`.
  - `_markActiveDomainRow(sectionId)` — helper that toggles
    `.is-active` on the matching dropdown row; called from
    `updateTopologyIndicator` / `clearTopologyIndicator` so the
    top-bar pill and the dropdown stay in sync.
  - `showManageSections` — the old always-open bottom "Add New
    Domain" form is replaced with a collapsible `+ Create new
    domain` toggle at the TOP of the panel. Rotating + → × icon,
    dedicated Cancel button, Enter submits, Escape cancels. Post-
    create, `render()` re-renders the panel so the form auto-
    collapses again.

- `topology/index.html` — cache-busters bumped to `?v=20260423a`
  for both `styles.css` and `topology-file-ops.js`.

**Deploy + verify (executed this session).**

1. `node -e "new Function(fs.readFileSync('/home/dn/CURSOR/topology-file-ops.js','utf8'))"` → clean (syntax OK).
2. CSS brace balance → 2809 / 2809, diff 0.
3. `cp` mirrored `topology-file-ops.js`, `styles.css`, `index.html`
   to `/home/dn/CURSOR/`; `diff --brief` reported identical for
   each.
4. `curl http://localhost:8080/` → 200; served HTML advertises
   `styles.css?v=20260423a` and `topology-file-ops.js?v=20260423a`
   (no stale buster leaks).
5. `curl http://localhost:8080/topology-file-ops.js?v=20260423a` →
   200; `styles.css?v=20260423a` → 200.
6. No service restart required — static frontend only. Browser
   hard-refresh picks up the new busters.

**Files touched this session:**

- `topology/styles.css` → `/home/dn/CURSOR/styles.css`
- `topology/topology-file-ops.js` → `/home/dn/CURSOR/topology-file-ops.js`
- `topology/index.html` → `/home/dn/CURSOR/index.html`

## 2026-04-23 — Supervisor false-positive: `bridge: down` even though :8766 was up

**Symptom.** Server Diagnostics card showed `bridge: down, pid <old>`
for ~1 h, and the browser flooded `WebSocket connection ... /api/events/ws failed`
errors. `/api/health` agreed: `scaler_bridge.status = down`. Yet
`ss -ltnp` said :8766 was listening and `curl http://localhost:8766/api/health`
returned 200 `{"status":"ok","service":"scaler-bridge","users_total":640}`.

**Root cause.** The bridge gained an auth middleware and `/docs` started
returning `401`. Two code paths in `serve.py` still probed `/docs`:

1. `_service_monitor._health_ok()` used `urllib.urlopen`, which raises
   `HTTPError` on any 4xx -- `except Exception: return False`. The
   monitor therefore saw "bridge unhealthy" every 15 s, tripped the
   3-fail threshold, called `_restart_bridge()`:
   - `_child_procs["bridge"].terminate()` targeted whatever Popen
     handle we had; the **actually listening** uvicorn parent stayed
     alive and kept holding :8766.
   - `_start_scaler_bridge()` spawned a new uvicorn that immediately
     died with `[Errno 98] Address already in use` (journalctl flood
     every 15 s).
   - `_child_procs["bridge"]` ended up pointing at a dead Popen while
     the real listening uvicorn ran untracked.
2. `_handle_api_health()` also fell back to `GET /docs` → 401 →
   reported `status: down` in `/api/health` and in the Diagnostics
   card.

**Fix (`topology/serve.py`).**

- `_health_ok(url)`: now catches `urllib.error.HTTPError` separately.
  Any 4xx response is treated as "alive but restricted" (the process
  is answering HTTP, which is what we actually want to verify). 5xx
  and connection errors still count as dead.
- All four `SCALER_BRIDGE_API + "/docs"` probes (monitor, startup
  echo, `_start_scaler_bridge` pre-check, `/api/health` aggregator)
  are now `SCALER_BRIDGE_API + "/api/health"` -- an unauth,
  semantic endpoint returning 200 `{"status":"ok", ...}`.
- Restarted `topology-app.service` once so the fresh serve.py owns a
  real Popen handle for :8766 and the old zombie supervision state
  is discarded.

**Deploy + verify (executed this session).**

1. `python3 -c "ast.parse(open('topology/serve.py').read())"` → OK.
2. `cp topology/serve.py /home/dn/CURSOR/serve.py` → `diff --brief`
   reports identical.
3. `systemctl --user restart topology-app.service` → serve.py 3957185,
   discovery 3957248, uvicorn 3957302. No `EADDRINUSE` in the new
   service journal.
4. `curl http://localhost:8080/api/health` →
   `scaler_bridge: {status: "ok", pid: 3957302, uptime_s: 9}` --
   pid matches `ss -ltnp`, confirming the Popen handle now tracks the
   real listening process.
5. `curl http://localhost:8766/api/health` → 200 with expected JSON.

**Guard for next time.** If a future endpoint is locked down, the new
`_health_ok()` will shrug at 401/403 instead of triggering a restart
loop. If the bridge adds `/api/health` auth, pick a different public
probe URL -- don't revert `_health_ok` to the old strict behaviour.

---

### Topologies dropdown no longer overlaps left sidebar + share panel refresh (2026-04-24)

**What users reported.** Two adjacent annoyances in the same
screenshot: (1) the Topologies dropdown opened at the
`btn-topologies.getBoundingClientRect().left` anchor, but that anchor
was only ~16-20px from the viewport edge, and the 200px left toolbar
sidebar ended up with the dropdown clipping a few pixels into it.
(2) the inline share panel (`Share DriveNets_Topology_...`) looked
dense and a little flat next to the polished domain rows we shipped
in the previous session, and the title + close X felt cramped.

**What we changed.**

- `topology/styles.css` `.top-bar` padding `0 16px` -> `0 16px 0 28px`.
  Small visible shift right for every top-bar element (DriveNets logo,
  Topologies, New, Shortcuts, Labels, ...). Buys the dropdown ~12px of
  breathing room without eating much from the scrollable button row.
- `topology/topology-file-ops.js` now exposes
  `FileOps._clampDropdownLeft(leftPx)`. It looks at
  `.toolbar.getBoundingClientRect()` and, when the sidebar is actually
  present at the left edge (`width >= 20`, `left <= 10`), returns
  `max(leftPx, toolbar.right + 6)`. Otherwise returns the caller's
  value unchanged -- safe default so no behaviour changes when the
  sidebar is collapsed / hidden / moved.
- Wired the clamp into the three call sites that position
  `#topologies-dropdown-menu`:
    * `topology.js` main open path (line ~13083).
    * `topology-file-ops.js` Manage-panel back-button re-show path
      (line ~4902).
    * `topology-share.js` `_openTopologiesDropdown()` for share
      deeplinks (line ~855).
  Each call site checks `window.FileOps && typeof
  FileOps._clampDropdownLeft === 'function'` before using it so the
  early-load share deeplink path can still place the dropdown even if
  `FileOps` hasn't been defined yet (falls back to the raw rect.left).
- Share panel (`topology/styles.css`, `.domain-share-form` and
  `.topo-share-form` families) polish:
    * Wrapper `padding: 8px 10px 10px` -> `10px 12px 12px`, radius 9 -> 11,
      a soft 180deg gradient instead of a flat fill, slightly richer
      border + shadow.
    * `.dsf-head`: 13px icon -> 14px, title weight 600 -> 700 and size
      11.5 -> 12.5. `.dsf-close` now has a visible-at-rest 24px frame
      (was transparent 20px) so the X doesn't disappear next to the
      title; hover scales + tints to the existing red-coral palette.
    * Chip input: `min-height: 38px`, border-radius 9 -> 10, added a
      hover state so the box breathes before focus. Chip + remove
      button grew slightly for better hit area.
    * Typeahead panel: rounder corners, richer shadow stack, rows now
      7px top/bottom with a 3px accent bar on the `.active` row so the
      user always sees where their arrow keys are.
    * Permission pill (`.share-perm-mini`) picks up the DN cyan accent
      on hover instead of plain white -- makes the "Read"/"Write"
      toggle read as a drop selector not a status badge.
    * Primary Send button uses a gentle gradient + inner highlight so
      it feels like a polished CTA rather than a flat cyan square.

**Cache bust.** `index.html`:
`styles.css`, `topology-share.js`, `topology-file-ops.js`,
`topology.js` all -> `?v=20260424a`. Mirrored the five files
(`styles.css`, `index.html`, `topology.js`, `topology-share.js`,
`topology-file-ops.js`) to `/home/dn/CURSOR/`. Pure CSS/JS change -- no
Python restart needed. Verified via `curl` that every asset returns
200 and `/api/health` still reports `serve: ok` + `scaler_bridge: ok`.

**Guard for next time.** If someone adds a new surface that opens
anchored to `#btn-topologies`, route its `style.left` through
`FileOps._clampDropdownLeft(...)` instead of raw `rect.left`. Keeping
a single helper means the next sidebar-width / top-bar-padding tweak
only has to happen in one place.

---

## 2026-04-22 -- Live collaborative sync + per-topology Activity Log

### Problem

Shared-write topologies were **silently divergent**. A recipient with
write permission could save edits, but the owner (and every other
shared recipient) kept staring at the stale view they loaded hours
earlier. Refresh did not help because the legacy Topologies dropdown
loads from `localStorage`, not the server. Worst case a second user
with their own stale copy would save and clobber the edits entirely
because the legacy `/api/sections/<sid>/save` endpoint had no
conflict detection.

Separately, the bottom-left `Logs` button opened the old
**Notification Center** which only knew about the current browser
session's toasts -- there was no per-topology, per-user audit trail.

### Architecture

Three cooperating layers:

1. **Event bus + per-topology log (backend).**
   `api/auth/user_store.py` owns a new `topology_events` table keyed
   on `(owner, domain_id, topology_id)`. Every save / create /
   rename / delete / share / unshare / permission-change records one
   row with actor, summary, JSON details and (optionally) an attached
   `micro_events` array sent from the client. After writing the row,
   the store fans a `topology_event` frame through
   `event_bus.publish_to_users_sync(...)` to the owner **and** every
   recipient of that file, which the existing WebSocket layer pushes
   into the browser.

2. **Conflict guard on save (backend).**
   The multi-user `PUT /api/domains/{did}/topologies/{tid}` now
   accepts a `base_updated_at` query parameter and raises
   `TopologyConflictError` when the on-disk row is newer, surfaced
   as `HTTP 409` with `{current_updated_at, last_actor,
   last_actor_display_name}`. The legacy
   `/api/sections/<sid>/save` path uses the same guard via the
   mirror table so old clients can't clobber new edits either.

3. **Unified sync hub (frontend).**
   `topology-sync.js` is installed as `window.TopologySync` and:
   - Keeps a `_active = { owner, domain_id, topology_id,
     updated_at }` cache persisted to `localStorage` under
     `topology.sync.active.v1`.
   - On boot, refetches the active topology and overwrites the local
     copy if the server's `updated_at` is newer (`_bootRefetch`).
   - Listens to `window.addEventListener('topology:event:
     topology_event', ...)` for WS frames and to SSE `topology-
     updated` forwarded from `topology-file-ops.js`.
   - Polls `/api/domains/{did}/topologies/{tid}` every 20 s as a
     fallback when the WS drops.
   - If the canvas is clean it silently reloads; if dirty it shows
     a non-blocking banner with **Reload** / **Keep mine**.
   - Exposes `saveActive(name, data)` that attaches
     `base_updated_at` and transforms a 409 into
     `{conflict: true, ...}` so callers render a **Reload theirs /
     Save anyway / Cancel** resolution strip.
   - Exposes `recordOp(kind, fields)` so canvas code can push
     fine-grained edit descriptors (`device.added`,
     `device.renamed`, `link.added`, `objects.deleted`, ...) into
     a buffer that gets spliced into the next save under
     `data.__micro_events`. The server strips that key before
     writing the file and copies it into the event row's
     `details.micro_events` so the Activity Log can render e.g.
     _"Saved 'lab7' | +1 device | +2 links | R7 -> R7-spine"_.

### Frontend surfaces

- **Activity Log panel.** `topology-notifications.js` was refactored
  into a tabbed overlay opened by the existing bottom-left `Logs`
  button. The **Topology** tab renders
  `/api/domains/{did}/topologies/{tid}/events` with a search box,
  actor + event-type facets, date-range pickers, pagination and JSON
  / CSV export buttons. The **Session** tab keeps the old transient
  toast history so nothing was lost. The panel listens for
  `topology:event:topology_event` frames to refresh live while open.

- **Save-button plumbing.** `topology-file-ops.js` calls
  `TopologySync.saveActive(...)` whenever an active multi-user
  topology is registered, and falls back to the legacy `save` path
  otherwise. On share-load or mirror-resolve it calls
  `TopologySync.setActive(...)`. Legacy SSE frames are forwarded to
  `TopologySync._onEvent` so both transports drive the same UX.

- **Canvas micro-op hooks.** `topology.js`
  (`addDevice`, `createLink`, `deleteSelected`) and
  `topology-device-rename.js` (`applyRename`) now call
  `window.TopologySync.recordOp(...)` with lightweight descriptors.
  Every hook is wrapped in `try/catch` so a missing / failing sync
  hub can never break an edit.

### Legacy mirror bridge

Recipients who open a shared file through the legacy
`/api/sections/<sid>/load` path now get a deterministic mapping back
to the multi-user ids via `GET /api/sections/{sid}/_mirror-map`
(optionally `?filename=foo.json`). The frontend uses this to
`setActive(...)` the sync hub for legacy-opened files so they still
participate in the WS broadcast / 409 guard.

### Files touched (copied to `/home/dn/CURSOR/`)

- `topology/api/auth/user_store.py`
- `topology/api/domains/router.py`
- `topology/serve.py` (also fixed three pre-existing indentation
  bugs that prevented `ast.parse`)
- `topology/topology-sync.js` (new)
- `topology/topology-notifications.js`
- `topology/topology-file-ops.js`
- `topology/topology-device-rename.js`
- `topology/topology.js`
- `topology/index.html` (script tag + cache-busters `?v=20260424b`)

### Verification

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8080/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"drivenets"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')
AUTH="Authorization: Bearer $TOKEN"

# 2. Create + save with a micro-op + rename + list events + export
TID=$(curl -s -X POST -H "$AUTH" -H 'Content-Type: application/json' \
  http://localhost:8080/api/domains/default/topologies \
  -d '{"name":"sync-smoke","data":{"objects":[]}}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
curl -s -X PUT -H "$AUTH" -H 'Content-Type: application/json' \
  "http://localhost:8080/api/domains/default/topologies/$TID" \
  -d '{"name":"sync-smoke","data":{"objects":[{"id":"d1","type":"device","label":"R1"}],"__micro_events":[{"kind":"device.added","device_id":"d1","label":"R1"}]}}' >/dev/null
curl -s -H "$AUTH" \
  "http://localhost:8080/api/domains/default/topologies/$TID/events" \
  | python3 -m json.tool | head -20

# 3. Conflict
curl -s -X PUT -H "$AUTH" -H 'Content-Type: application/json' \
  "http://localhost:8080/api/domains/default/topologies/$TID?base_updated_at=2025-01-01T00:00:00%2B00:00" \
  -d '{"name":"sync-smoke","data":{"objects":[]}}' -w "\nhttp=%{http_code}\n"
# -> http=409 with {error: "conflict", current_updated_at, last_actor, ...}

# 4. CSV export
curl -s -H "$AUTH" \
  "http://localhost:8080/api/domains/default/topologies/$TID/events/export?format=csv" \
  | head -3

# 5. Cleanup
curl -s -X DELETE -H "$AUTH" \
  "http://localhost:8080/api/domains/default/topologies/$TID"
```

Confirmed end-to-end: `topology.created` + `topology.saved` rows
get recorded with `details.micro_events`, CSV/JSON export returns
the same data, stale `base_updated_at` triggers `409`, delete works,
and the event bus pushes `topology_event` frames to every recipient.

### Guardrails for future edits

- **Any** new "save" / mutation path that touches a topology MUST
  call `UserStore.record_topology_event(...)` (or go through
  `save_topology` / `delete_topology` which do it for you). If it
  doesn't, the Activity Log will quietly miss the change and the
  collaborators won't see a WS frame.
- When adding a new fine-grained canvas edit that a user would
  notice (move, style change, bulk paste, ...), add exactly one
  `window.TopologySync.recordOp('<dotted.kind>', { ...fields })`
  call at the end of the operation. Keep fields tiny -- ids and
  labels only -- so the event row stays under a few KB.
- The sync hub MUST stay optional: every call site that uses it is
  wrapped in `if (window.TopologySync && TopologySync.xxx)` so the
  app still works if the script failed to load.
- Cache-bust (`?v=YYYYMMDDx`) every file you touch in
  `index.html`; otherwise the browser will serve the old JS and the
  user will see "my changes don't appear" regressions.

## 2026-04-24c -- LLDP per-user isolation + restart-resilient client + simpler Activity Log search

### Symptom

Multiple users reported `Enable LLDP` appearing to "stop working":
the topology canvas would show the LLDP wave animation indefinitely
and DevTools showed a long stream of:

```
GET /api/dnaas/enable-lldp/status?job_id=lldp_<ms> 502 (Bad Gateway)
GET /api/dnaas/enable-lldp/status?job_id=lldp_<ms> 404 (Not Found)
GET /api/dnaas/enable-lldp/status?job_id=lldp_<ms> 404 (Not Found)
...
[LLDP Enable] Error: LLDP job not found on server (discovery API may have restarted). Try again.
```

### Root cause (three stacked issues)

1. **LLDP jobs lived in a module-level `jobs = {}` dict in
   `discovery_api.py`.** `discovery_api.py` is spawned as a child of
   `serve.py`, so any `serve.py` restart (deploy, OOM, manual kill)
   wipes every in-flight job. The client kept polling job ids that
   no longer existed, hit the 10 × 404 ceiling, and threw "Try again".
2. **No per-user isolation on LLDP jobs.** Discovery / multi-bd /
   network-mapper jobs all stamped `'owner'` from `_request_owner(self)`
   and enforced an owner check on status/cancel; LLDP did neither, and
   its job_id was just `lldp_<ms>` -- two users clicking in the same
   millisecond got the same id and could see each other's job state.
3. **Client gave up after 5 s of 404s with no recovery path.** Even
   though re-POSTing the same body would have succeeded immediately
   (the upstream is idempotent), the client just threw.

### Fix

#### `discovery_api.py` -- per-user LLDP jobs + reconnect endpoint

- `/api/enable-lldp` now stamps `'owner': _request_owner(self)` and
  builds a user-scoped, collision-proof id:
  `job_id = f"lldp_{safe_owner}_{int(time.time() * 1000)}"` with a
  `_<n>` suffix in the rare same-ms tie.
- `/api/enable-lldp/status` and `/api/enable-lldp/cancel` now compare
  `job.get('owner', 'global')` against `_request_owner(self)` and
  return 404 (never leak existence) on a mismatch -- matches the
  pattern already used by `/api/discovery/status`,
  `/api/multi-bd/status`, and `/api/network-mapper/status`.
- New `GET /api/enable-lldp/find?serial=<X>` returns the most recent
  LLDP job for `(this user, this serial)` so the client can reattach
  to an in-flight job on tab refresh / reconnect.

#### `topology-dnaas-helpers.js` -- restart-resilient `_enableLldpOnDevice`

- POST is wrapped in `submitJob()` which retries up to 3 times on
  network errors / 5xx (1 s backoff) and only surfaces 4xx errors.
- Before submitting, the client first tries `/api/enable-lldp/find`
  to **reattach** to an existing running job for this `(user, serial)`
  -- handles tab refresh, page navigation, and the "I clicked twice"
  case for free.
- Status polling now keeps three independent counters (`consecutive404`,
  `consecutive5xx`, `consecutiveNetErr`) so a transient upstream blip
  doesn't poison the 404 budget reserved for "the job is truly gone".
- On `MAX_404` (10 × 500 ms = 5 s of 404s), the client **transparently
  resubmits the POST once** and continues polling with the new
  `job_id` instead of throwing. A single "Reconnecting to LLDP job..."
  toast is shown so the user knows what happened. This is the key
  resilience win: a `serve.py` restart mid-LLDP-enable is now
  invisible to the user.

#### `topology-notifications.js` -- simpler Activity Log search

- Replaced the 2 × 2 picker grid (search + actor + type + since/until)
  with a **single unified search box** that supports smart tokens:
  - `@username` -> actor filter
  - `#topology.saved` or `#saved` (shorthand) -> event type filter
  - `>24h` / `>2d` / `>90m` -> "since N units ago" filter
  - everything else -> free-text query (same as before)
- Added a row of **quick-filter chips**: `All`, `Mine`, `Saves`,
  `Last 24h`. The active chip is highlighted based on effective state.
- All the original detail pickers (actor dropdown, type dropdown,
  since / until datetime) still exist but are hidden under an
  `Advanced` toggle. They auto-open if any of those filters were
  carried over from a previous session.
- The state object passed to `TopologySync.listEvents()` is identical
  to before, so the server-side facets / actor-display-name plumbing
  keep working unchanged.

### Files touched

| File | Change |
|---|---|
| `discovery_api.py` | LLDP owner stamping; owner check on status/cancel; new `/api/enable-lldp/find` |
| `topology-dnaas-helpers.js` | `submitJob()` helper, `find` reconnect, transparent re-POST on 404, separate 5xx counter |
| `topology-notifications.js` | Unified search box, smart-token parser, chip presets, `Advanced` collapsible |
| `index.html` | Cache-bust both JS files to `?v=20260424c` |

### Smoke test (after deploy + serve.py restart)

1. `Enable LLDP` on a device -- should run end-to-end, animation
   stops, success toast.
2. While it's mid-run, `pkill -f serve.py && python3 serve.py &` to
   simulate a restart. The browser should briefly show "Reconnecting
   to LLDP job..." and continue without the user clicking anything.
3. As **user-A** click `Enable LLDP` on device-1; as **user-B** in a
   second browser click `Enable LLDP` on device-2 simultaneously.
   Both should complete independently. Neither should see the other's
   `output_lines`. `curl -H 'X-User: alice'
   /api/enable-lldp/status?job_id=<bob's id>` should return 404.
4. Open the **Activity Log** panel. The filter row should now have a
   single search box + 4 chips + an `Advanced` toggle. Typing
   `@alice #saved >1d` into the search should filter to alice's saves
   in the last day.

### Permissions-Policy 'browsing-topics' warning

Chrome's DevTools console emits `Error with Permissions-Policy
header: Unrecognized feature: 'browsing-topics'` on every page load
served over plain HTTP (e.g. our `http://100.64.6.134:8080`). This
is **not** something we send -- a grep for `Permissions-Policy`
across `topology/` returns no matches. `browsing-topics` is a
secure-context-only Topics API feature; Chrome warns about it on any
non-HTTPS origin. Cosmetic, ignorable. Switching the deploy to HTTPS
silences it. We chose **not** to inject our own Permissions-Policy
header to suppress it because that would mask other legitimate
warnings.

### Guardrails for future job-based endpoints

Every new endpoint that creates a job (`/api/<thing>/start`) MUST:

1. Read `owner = _request_owner(self) or 'global'` at job creation
   and store it as `jobs[job_id]['owner'] = owner`.
2. Build the `job_id` with the owner in it
   (`f"<thing>_{safe_owner}_<ms>"`) so concurrent users can't
   collide.
3. The matching `/api/<thing>/status` and `/api/<thing>/cancel` MUST
   compare `job.get('owner', 'global')` against
   `_request_owner(self)` and return 404 on a mismatch -- never
   leak existence.
4. If the work the job represents is idempotent and short, expose a
   `/api/<thing>/find?...` endpoint so the client can transparently
   reattach across `discovery_api` restarts. The client side should
   call `find` before `start`.

These four together give us "always works for any user at any time,
even simultaneously" semantics on top of the in-memory job dict
without needing persistent storage.

---

## Ultimate TP planning + `/TEST` import (2026-04-28)

- **TP Agent MCP** (`qa_automation/ai_test_plan/tp_agent_mcp/`): Jira prefetch bundle (epic + comments + user stories + links), file queue under `~/SCALER/TEST/tp/.queue/`, outputs under `~/SCALER/TEST/tp/<EPIC_KEY>/` (`manifest.json`, `full_result.json`, `test_plan_<EPIC>.md`, staged `epic_documentation_*.md` sidecars).
- **MCP tools:** `tp_get_context` (bundled fallbacks in `tp_agent_mcp/bundled_reference/`), `tp_submit_stage_result`, `tp_validate_plan`, `tp_submit_result` (schema_version≥2 with `quality_gate` + `artifacts`; optional `strict`).
- **`/TEST`:** See `.cursor/commands/TEST.md` — CREATE may **import** an MCP-generated TP from that folder before building recipes; recipes should set `traceability` (`source_tp`, `source_tc`, `source_user_story`, `source_epic`, `linked_epics`, `quality_gate_id`).
- **Rollback:** If MCP schema changes break agents, revert `mcp_tools.py` / `queue_manager.py` and keep reading legacy `manifest.json` fields (`categories`, `test_count`). If `/TEST` import regresses, disable import path in `TEST.md` only; TP generation can stay on.

---

## Drivenets-style Generate canvas: hub-spoke triangle + roleHints (2026-04-29)

- Live correlation on PE-1 (1.1.1.1, AS 1234567), RR-SA-2 (2.2.2.2, AS 123) and PE-4 (4.4.4.4, AS 1234567) confirmed the canonical Drivenets resemblance graph: a full ISIS+LDP triangle on /29 sub-interfaces, MP-eBGP from each PE to the RR (RR-SA-2), and EVPN/VPLS service families (`EVPN_SI_VPLS_1..5`, `EVPN_SI_AC_PW_test`) with RTs aggregated under the parent service card. The verified evidence is persisted at `topology/data/correlations/known_topologies.json` so the Generate flow has a reference even when a DUT auth fails.
- `topology/routes/topology_generator_correlate.py` now emits `correlationEvidence.roleHints` per device (rr / pe / ce / router) using BGP AS asymmetry + name heuristics, and switches to a hub-spoke triangle layout (`_hub_spoke_triangle_positions`) for `rr-pe-service` topologies of ≤6 DUTs. The chosen mode is exposed as `correlationEvidence.layout.mode` (`hub-spoke-triangle` or `tiered-rows`).
- `topology/topology-generator.js` mirrors the same logic in `synthesizeRoleHints` + `placeHubSpokeTriangle`, used when `family === 'rr-pe-service'` AND there is at least one RR AND `devices.length <= 6`. The generated `compositionReport` records `layoutMode` and `roleHints` so future canvas tooling can lock those decisions in.
- Tests:
  - `topology/tests/test_topology_generator_integration.py` covers the trio (`PE-1 / RR-SA-2 / PE-4`): `layout.mode === "hub-spoke-triangle"`, RR placed above PEs, PEs flanking the RR, role hints populated.
  - `topology/topology-tests.js` adds an in-browser fixture mirroring the trio and asserting `compositionReport.layoutMode` + role hints.
- Cache buster: `topology-generator.js?v=20260429f-hub-spoke-triangle`, `topology-tests.js?v=20260429f-hub-spoke-triangle`.
- Rollback: keep the old `_symmetric_positions` and `calculateArchitecturePositions` row layout — both still trigger when the family is not `rr-pe-service` or when more than six DUTs are involved. Removing the new helpers reverts cleanly without changing any other Generate behavior.

---

## Drivenets-style BGP overlay AF chips + perimeter cluster (2026-04-29 g)

- Generate now renders MP-BGP evidence on top of the RR/PE hub-spoke layout with per-AF chips. Canonical AF tokens are: `ipv4-unicast`, `ipv4-vpn`, `ipv4-flowspec`, `ipv4-flowspec-vpn`, `ipv4-rt-constrain`, `ipv6-unicast`, `ipv6-vpn`, `ipv6-flowspec`, `l2vpn-vpls`, `l2vpn-evpn`. The frontend maps them into grouped panel toggles: Unicast, VPN, Flowspec, RT-Constrain, VPLS, EVPN.
- BGP overlay mode metadata is emitted as `generatedOverlayModes`: `real-legs`, `via-rr`, `both`. `real-legs` is the default and shows only true BGP adjacencies (PE-1<->RR-SA-2 and RR-SA-2<->PE-4). `via-rr` renders an auxiliary dotted PE-to-PE reflective path tagged `_overlayMode="via-rr"` and hidden by default. `both` enables both sets.
- Backend perimeter synthesis (`topology/routes/topology_generator_correlate.py`) adds muted non-DUT evidence nodes after core correlation:
  - LLDP names containing DNAAS/fabric/leaf/spine are grouped into one `fabric` perimeter node per anchor DUT.
  - eBGP non-DUT peers remain `cpe` / `tester` nodes unless compacted.
  - `spirent`, `ixia`, `exabgp`, `100.64.6.134`, and `100.64.6.135` classify as `tester`.
  - ISIS neighbors whose advertised areas do not match the local area become `foreign-igp` perimeter nodes.
  - Scale fan threshold: >=10 BGP peers in the same `/24` with the same remote AS collapse into one `scale-fan` node labelled `<subnet> x<count> eBGP AS<asn>`.
- Perimeter nodes carry `_perimeter`, `_perimeterKind`, `_anchorDevice`, `_evidence`, and muted canvas styling. Links to anchors use `linkType="perimeter-evidence"` and `layer="evidence"` so the protocol panel can hide/show Fabric, CPE, Tester, Foreign IGP, and Scale fans independently.
- The PE-1/RR-SA-2/PE-4 knowledge pack at `topology/data/correlations/known_topologies.json` now records `bgp_overlay_default_mode`, `bgp_overlay_modes`, per-leg `address_families`, and explicit `perimeter_layout` slots for Junos, DNAAS, ExaBGP, Spirent, and the `10.99.101.0/24` scale fan.
- Tests:
  - `topology/tests/test_topology_generator_integration.py` verifies scale-fan compaction, fabric grouping, foreign-IGP perimeter evidence, overlay modes, and AF passthrough including `ipv4-rt-constrain`.
  - `topology/topology-tests.js` verifies AF chip canvas labels, hidden default via-RR spline, overlay-mode metadata, and muted perimeter nodes for ExaBGP and scale-fan fixtures.
- Cache buster: `styles.css?v=20260429g-bgp-af-perimeter`, `topology-generator.js?v=20260429g-bgp-af-perimeter`, `topology-tests.js?v=20260429g-bgp-af-perimeter`.
- Rollback: remove `_synthesize_perimeter_nodes` and the perimeter call site in `correlate_topology_facts`; remove `AF_PALETTE`, `buildAfChipsForLink`, and `buildViaRrSplineLinks` in `topology-generator.js`; remove the BGP overlay radio / AF / perimeter panel additions and CSS classes. The existing hub-spoke triangle remains intact.

## Readable generated topology defaults (2026-04-29 h)

- Do not attach multiple generated text boxes to the same link center. Each generated link may have one center `linkDataLabel`; AFI/SAFI labels are detached badges (`_afChip`, no `linkId`) offset from the link path and still controlled by AF group toggles.
- Perimeter/evidence nodes and links remain available but are hidden by default. Generated Layers must omit zero-count groups and should open with core devices, underlay/routing, and service cards visible; users can opt into Perimeter, Evidence, and Via-RR.
- Service labels should prefer verified service names and modes over generic RT callouts. The PE-1/RR-SA-2/PE-4 known topology pack is merged during backend correlation when the live DUT names match, producing EVPN/VPLS/VPWS/VRF service cards with RT/RD, VLAN, and mode details where known.
- Cache buster: `styles.css?v=20260429h-readable-generated`, `topology-generator.js?v=20260429h-readable-generated`, `topology-tests.js?v=20260429h-readable-generated`.

## Crisp canvas rendering root cause fix (2026-04-29 i)

- Main canvas sizing must use `getBoundingClientRect().width/height`, not integer `clientWidth/clientHeight`. CSS grid columns can land on fractional CSS pixels; using integer sizing forces Chrome to resample the canvas bitmap and makes links/text look soft.
- `#topology-canvas` must not use GPU-promotion transforms (`translateZ(0)`) or nonstandard `image-rendering: high-quality` hints. Keep `image-rendering: auto` and let the DPR backing store plus canvas rasterizer control sharpness.
- `TopologyEditor.canvasW/canvasH` now return the stored fractional CSS dimensions from `resizeCanvas()`. Drawing code should continue using these logical CSS dimensions instead of raw backing-store pixels.
- Cache buster: `styles.css?v=20260429i-crisp-canvas`, `topology.js?v=20260429i-crisp-canvas`.

## Generated topology readable-distance mode (2026-04-29 j)

- Generated topologies must auto-fit small graphs upward on load. `centerOnDevices({ fitSmall: true, maxZoom: 1.25, minZoom: 0.85 })` is used for generated payloads so 3-node service maps do not stay at an old 60-70% zoom and render as blurry thumbnails.
- Device centering should ignore hidden devices by default. Hidden perimeter/evidence nodes must not expand the viewport bounds or shrink the core RR/PE graph.
- Do not strip `_hidden` from generated links during load. Legacy hidden link repair may clear `_hidden` only for non-generated objects.
- Low-zoom generated LOD: hide generated AF/detail/endpoint/identity micro-labels below moderate zoom and keep generated links at a stronger minimum screen stroke. This keeps the distant view clean and sharp while preserving details when the user zooms in.
- Cache buster: `topology.js?v=20260429j-generated-readable-distance`, `topology-link-drawing.js?v=20260429j-generated-readable-distance`, `topology-canvas-drawing.js?v=20260429j-generated-readable-distance`.

## Generate preserves verified cluster SSH context (2026-04-29 k)

- Live Generate must preserve the full verified `sshConfig` from the source canvas device for PE/CL cluster DUTs. Do not reduce regenerated devices to `{host, hostBackup, user, password}` when `_activeNccHost`, `_activeNccIp`, `_virshInfo`, `_snVerified`, or `_verifiedAt` exists.
- A regenerated DUT with active NCC/virsh metadata should keep `subType: "cluster"` and `_clusterVerified: true` so DeviceMonitor, SSH dialog, and git-commit/device-context probes keep using the active NCC path instead of treating the device as an unverified standalone router.
- Cache buster: `topology-generator.js?v=20260429k-cluster-preserve`, `topology-tests.js?v=20260429k-cluster-preserve`.

## Visual sharpness polish (2026-04-29 l)

- Grid rendering must use the same `getSharpPanOffset()` as objects and draw as DPR-aware physical-pixel hairlines (`lineWidth = 1 / dpr`, positions snapped with `(round(px*dpr)+0.5)/dpr`). This keeps the background grid from looking soft during pan/zoom and prevents the grid/object layers from drifting by a fractional pixel.
- Generated micro-label LOD is intentionally stricter: AF chips, endpoint labels, and identity/detail labels hide below ~95% zoom, while non-service link-data labels hide below ~72%. The goal is a clean distant architecture view; detailed link evidence appears again as the user zooms in.
- Generated topology load-fit uses tighter padding and allows a little more zoom-in (`maxZoom: 1.4`) so small RR/PE service maps open closer and sharper instead of as thumbnails.
- Cache buster: `topology-drawing.js?v=20260429l-visual-sharpness`, `topology-canvas-drawing.js?v=20260429l-visual-sharpness`, `topology.js?v=20260429l-visual-sharpness`.

## Pixel-sharp text at low zoom (2026-04-29 m)

- Text boxes and low-zoom device labels must not be drawn by resizing an offscreen text bitmap through the world transform. Below ~105% zoom, paint glyphs directly in screen/DPR space: reset the canvas transform to the DPR backing store, translate to `getSharpPanOffset() + world * zoom`, snap that screen position to physical pixels, and use CSS-pixel font/stroke sizes already multiplied by zoom.
- Keep the existing high-DPI preraster/vector path for close zoom and selected text geometry. The screen-space low-zoom path is a paint-only pass; object positions, hit testing, link gaps, and selection handles still use world coordinates.
- Cache buster: `topology-canvas-drawing.js?v=20260429m-pixel-text`.

## Generated labels readable from default zoom (2026-04-29 n)

- Generated topology labels use a generated-only screen-size floor, separate from user text boxes. Link-data labels target roughly 12 screen px, service labels 13 px, AF chips 10 px, and other generated labels 11 px, capped at 3x world font-size so they stay readable without exploding.
- Generated labels default to `fontWeight: 700`, stronger dark label backgrounds (`backgroundOpacity` default 0.94), and 5px padding. This is intentional because screenshots/readable architecture views need label text to be legible at the generated topology's default zoom.
- Cache buster: `topology-generator.js?v=20260429n-readable-labels`, `topology-canvas-drawing.js?v=20260429n-readable-labels`.

## Unified Groups Panel + per-object Group button (2026-04-30)

User-visible refactor of how on-canvas groups are managed. Driver: the BD
legend panel disappeared after refresh; the control surface for grouping
felt unfinished compared to the rest of the topology UI.

### What shipped
- New module `topology-groups-panel.js` (`window.GroupsPanel`,
  `window.ObjectGroupPopover`). Floating draggable card listing **manual
  groups** (`groupId`/`groupLeaderId` on objects -- see
  `topology-groups.js`) and **BD-derived groups** (`_multiBDMetadata`/
  `_bdVisibility`) in two collapsible sections.
- Per-row affordances: colour swatch, name (rename inline), member count,
  Select-all / Recolor / Dissolve actions for manual groups; Eye toggle
  for BD groups; section "All / None" for BD bulk visibility.
- Top-toolbar **Groups** button (`#btn-groups-panel`, after Labels). Same
  glass styling as the other `.top-bar-btn` controls.
- Keyboard: **G** = Groups panel toggle (was grid lines). Grid lines
  toggle relocated to **Cmd/Ctrl+Shift+G**. **B** still opens the legacy
  BD legend for back-compat.
- Per-object **Group** button on the device, shape, link, and text
  toolbars. Opens `ObjectGroupPopover` -- a smart popover whose content
  adapts to the selection: multi-select shows `Group these N objects`
  with name input + existing-group list; single object NOT in a group
  shows existing-group list + a hint to multi-select first; single
  object IN a group shows current group + Move-to list + Remove from
  group.
- New SVG icon `#ico-group` registered in `index.html`.
- New CSS section in `styles.css` (search `GROUPS PANEL`).

### Multi-user discipline
- Panel state localStorage key is **`groups_panel_state_<username>`**
  (built via `_storageKey()` reading `window.TopologyAuth.getCurrentUser()`).
- BD legend state moved to **`bd_panel_state_<username>`** with one-shot
  migration from the legacy global `bd_panel_state` key. Single source
  of truth: `topology-bd-legend.js::_saveBDPanelState` /
  `_loadBDPanelState` -- the duplicate writer in
  `topology-dnaas-operations.js` (which used a different key
  `topology_bd_panel_state` and races on every refresh) is replaced
  with thin shims that delegate to the editor binding.

### Why the panel "disappeared after refresh"
Two parallel writers existed for `_saveBDPanelState`. The DNAAS-ops
writer used the wrong key and wrote `panelOpen: false` whenever DNAAS
mutated visibility; on reload, `restoreBDPanelIfNeeded` saw
`bd_panel_state.visible === undefined`, defaulted to closed, and the
panel never restored. Now there is one writer + one key + per-user
suffix.

### Cache busters (sync to /home/dn/CURSOR alongside)
- `styles.css?v=20260430a-groups-panel`
- `topology-groups-panel.js?v=20260430a-init` (new)
- `topology-bd-legend.js?v=20260430a-user-scoped`
- `topology-dnaas-operations.js?v=20260430a-dedupe-bd-save`
- `topology-device-toolbar.js?v=20260430a-group-btn`
- `topology-link-toolbar.js?v=20260430a-group-btn`
- `topology-text-toolbar.js?v=20260430a-group-btn`
- `topology-shape-toolbar.js?v=20260430a-group-btn`
- `topology-toolbar-setup.js?v=20260430b-groups-btn-fix`
- `topology-keyboard.js?v=20260430a-g-groups`

### Public API for downstream code
- `window.GroupsPanel.toggle(editor)`, `.show(editor)`, `.hide(editor)`,
  `.refresh(editor)`, `.restoreIfNeeded(editor)`,
  `.groupSelectionWithPrompt(editor, defaultName)`,
  `.addObjectToGroup(editor, obj, groupId)`,
  `.removeObjectFromGroup(editor, obj)`,
  `.listManualGroups(editor)`.
- `window.ObjectGroupPopover.open(editor, anchorEl)`, `.toggleFor(editor, anchorEl)`.
- New per-object fields: `groupName: string`, `groupColor: string` (hex).
  Existing `groupId`/`groupLeaderId`/`groupOffsetX`/`groupOffsetY`
  semantics are unchanged.

### 2026-04-30 hotfix notes
- The first Groups button wiring guarded the listener with
  `if (groupsPanelBtn && window.GroupsPanel)`. If `GroupsPanel` was not
  registered at setup time, the button got no click listener and appeared
  dead. The fixed pattern always binds the listener and resolves
  `window.GroupsPanel` lazily inside the click handler.
- Bottom-right Grid button tooltip and the Shortcuts helper text must show
  **Cmd/Ctrl+Shift+G** for Grid; plain **G** is now Groups.
- Follow-up hardening: `#btn-groups-panel` also has an inline fallback
  calling `window.toggleGroupsPanelFromToolbar(event)`, and
  `topology-groups-panel.js` installs a delegated capture listener on
  `document`. Sync both `/home/dn/CURSOR/index.html` and the nested
  `/home/dn/CURSOR/topology/index.html`; the nested copy can otherwise
  keep serving stale shortcut/button code when the browser URL is `/topology/`.
- Second hotfix: because the inline fallback, delegated fallback, and
  ToolbarSetup listener can all observe the same browser click, the toggle
  event must be marked with `event.__groupsPanelHandled`. Without that guard,
  the panel can open and immediately close, making it look like a visual/grid
  obstruction. `GroupsPanel.show()` also clamps saved top/left/width/height
  into the viewport so old localStorage cannot open the panel off-screen.
- Runtime evidence showed the panel was appended
  with `display:block`, `visibility:visible`, and `opacity:1`, but computed
  `z-index:auto` and `elementFromPoint` returned other UI (`app-splash` /
  status toolbar). Served `styles.css` did not contain `.groups-panel`.
  `topology-groups-panel.js` now injects a compact runtime stylesheet
  (`#groups-panel-runtime-styles`) before showing/restoring the panel so the
  floating card has its critical z-index/layout styles even when the global
  stylesheet is stale or missing the appended section.
- Scope correction after user review: the Groups panel must manage **manual
  object groups only**. Bridge Domains belong to the BD legend / BD hierarchy
  UI and must not be listed or controlled by `GroupsPanel`; otherwise the
  Groups button feels like it "steals" the BD panel. `GroupsPanel` now renders
  only the Manual groups section. It also clamps its left position to stay out of the
  left app control/sidebar area when old localStorage contains `left:16`.
- Group creation hotfix: `editor.showInputDialog` is callback-based
  (`showInputDialog(title, placeholder, callback, defaultValue)`), not a
  Promise API. Calling it as `showInputDialog('Group name', oldName)` caused
  `topology-dialogs.js:111 TypeError: callback is not a function` when the
  user pressed OK. `GroupsPanel._promptName` now wraps the existing dialog in
  a Promise. Runtime styling now
  mirrors the Topologies / Topology Domains inverted glass recipe: dark canvas
  gets a light frosted panel, light canvas gets a dark frosted panel.
- Manual group visibility correction: the multi-select context menu's global
  `Group (N)` action must call `GroupsPanel.groupSelectionWithPrompt(...)`
  instead of the legacy unnamed `editor.groups.groupSelected()` path. Otherwise
  users can group selected objects but the Groups panel may stay empty/stale
  until reopened. `topology-multiselect-menu.js` now awaits the named Groups
  flow and refreshes the panel when open.
