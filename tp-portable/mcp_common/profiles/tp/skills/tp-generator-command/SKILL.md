---
name: tp-generator-command
description: "/TP generate DNOS test plans from Jira EPICs"
---

# /TP -- Unified Test Plan Generator Command

Generates comprehensive DNOS test plans from Jira EPICs by combining:

- The `/TP` orchestration surface: GUI queue, MCP request lifecycle, Jira dedup,
  Jira-wiki rendering, manifest generation, and `/TEST` handoff.
- Alexandru Costake's `generate-qa-test-plan` three-stage pipeline: epic
  documentation, requirements-driven draft, and self-review/gap closure.
- A local SQLite-first knowledge DB for reusable flows, command catalog entries,
  rubric rules, dedup fingerprints, and source provenance.

`/TP` is the single entry point. Do NOT run `/generate-qa-test-plan` as a separate
terminal flow unless explicitly requested for comparison. The Costake pipeline is
now the content engine inside `/TP`.

## Modes

### Mode 1: Process (pull from GUI queue)
Triggered by: `/TP process` or `/TP queue`

Pull pending requests submitted by the Streamlit GUI through the tp-agent-mcp server.

1. Call MCP tool `tp_get_pending_requests` (server: tp-agent-mcp)
2. If no pending requests: tell user "No pending TP requests in queue"
3. For each pending request:
   a. Call `tp_claim_request` with the request_id
   b. Extract params: epic_id, categories, max_tasks_per_category, checklist_tasks
   c. Check `additional_instructions` for mode signals:
      - If contains "MODE: /TEST import-tp --full": this is an automation creation request.
        After generating the TP (Step 5), automatically chain to Step 6 Full Automation Mode
        for the specified categories. Do NOT ask -- the user already chose this in the GUI.
      - Otherwise: standard TP generation only (Steps 1-5), then offer Step 6.
   d. Generate tests using the agent's model (see Generation Protocol below)
   e. Call `tp_submit_result` with the completed test plan
   f. If automation mode: also include the created test_ids and catalog paths in the result
4. Report completion to user

### Mode 2: Direct Generate
Triggered by: `/TP <EPIC_ID>` or `/TP <EPIC_ID> <categories...>`

Generate test plan directly without the GUI queue.

Examples:
- `/TP SW-182545` -- all categories
- `/TP SW-182545 CLI HA Scale` -- specific categories only
- `/TP SW-228552 --linked SW-241473` -- joint dual-epic plan
- `/TP SW-182545 --push` -- generate and push to Jira
- `/TP SW-182545 --limit 5` -- max 5 tasks per category

1. Parse the EPIC ID and optional category filters
2. Parse optional linked epics (`--linked SW-XXXXX`, repeated or comma-separated)
3. Load active lab profile when the TP may later feed `/TEST`
4. Present category selection to user via AskQuestion (with "All" option)
5. Generate tests through the merged three-stage pipeline below
6. Save output to `~/SCALER/TEST/tp/<EPIC_ID>/`
7. Optionally push to Jira if `--push` flag

### Mode 3: Improve Existing TP and /TEST Handoff
Triggered by: `/TP improve <EPIC_ID>`, `/TP imrove <EPIC_ID>` (common typo),
`/TP refine <EPIC_ID>`, `improve the TP`, `align TP with /TEST`,
`TP -> /TEST`, or user text that asks to improve both the test plan and
`/TEST` import behavior.

1. Load `~/SCALER/TEST/tp/<EPIC_ID>/test_plan_<EPIC_ID>.md`,
   `manifest.json`, `full_result.json`, and `quality_audit.md`.
2. Identify the target section or TC from the user text. If ambiguous, use
   AskQuestion with multi-select options plus `All`.
3. Update all TP artifacts together: markdown, manifest, full_result, quality
   audit, and relevant `~/.cursor/tp-reference/*` mapping docs.
4. Preserve existing test IDs unless the user explicitly asks to split/rename
   them in Jira.
5. When the change affects automation behavior, update `/TEST` command guidance
   or `/TEST` import hints in the manifest in the same turn.
6. Do not push to Jira and do not run `/TEST create` unless explicitly asked.

## Merged Generation Protocol

### Step 0: Load Context and Knowledge DB

Always read these files from `~/.cursor/tp-reference/`:

- `tp_checklist.json` -- 24 TP checklist categories (incl. Interoperability); keys `jira_category` and `reference_jira_key` (epic-agnostic; resolve Jira keys per-epic at push time)
- `qa_guidelines.md` -- QA process rules
- `topology_reference.md` -- network topology diagrams
- `dnos_syntax_rules.md` -- local DNOS syntax reference
- `test_format_template.md` -- Jira wiki markup templates
- `test_examples.md` -- example test plans from past EPICs
- `manifest_schema.json` -- TP-to-`/TEST` handoff schema
- `tp_to_test_mapping.md` -- category to `/TEST` automation mapping
- `db_schema.md` -- local TP knowledge DB schema
- `merged_tp_workflow.md` -- exact stage ordering
- `dedup_and_packing.md` -- duplicate and multi-category packing rules

Also read Costake's rubric:

- `~/.cursor/skills/generate-qa-test-plan/test-documentation/test_plan_requirements.md`

When feature-specific skills match the epic, read them before generation. Example:

- `~/.cursor/skills/evpn-si-irb-mobility/SKILL.md`

Initialize or refresh the local TP knowledge DB:

```bash
python3 ~/.cursor/tools/tp_knowledge_db.py init
python3 ~/.cursor/tools/tp_knowledge_db.py seed-core
python3 ~/.cursor/tools/tp_knowledge_db.py export
```

### Step 1: Source Collection and Joint Epic Documentation

Use Costake Stage 1 as the source-collection contract, extended for dual epics.

For every primary or linked epic:

1. Fetch the epic issue with fields, comments, issue links, labels, fix versions,
   parent, customer, attachments list, and status.
2. Fetch non-rejected User Stories:
   - `parent = <EPIC_KEY> AND issuetype = "User story" AND status not in (Reject, Rejected)`
   - fallback: `"Epic Link" = <EPIC_KEY> AND issuetype = "User story" AND status not in (Reject, Rejected)`
3. Fetch linked epics:
   - `issue in linkedIssues(<EPIC_KEY>) AND issuetype = Epic`
4. Fetch referenced parity, scale, parent, SIT/E2E, and design-doc tickets named in
   descriptions or comments.
5. Fetch relevant Confluence pages and RFC references.
6. **MUST/required extraction** -- scan epic, User Stories, comments, RFC clauses,
   and HLD for every MUST/SHALL/required/mandatory statement. Persist to
   `must_requirements.json` under `~/SCALER/TEST/tp/<PRIMARY>/` with provenance
   (`source_epic`, `source_story`, `source_rfc`, `source_page`, `source_hld`).
   **Mine each User-Story BODY (not just its key)** for negative acceptance
   criteria -- commit-validations, mutual-exclusions ("X and Y are mutually
   exclusive", "a commit validation shall check/reject"), defaults, ranges, and
   "not allowed together" rules -- and register EACH as its own MUST + scenario.
   Rationale: story-KEY-level coverage marks a story "covered" by any TC that
   references it, so a validation buried in the body slips through the closure
   gate (this is exactly how the SW-253861 VPLS-SI x igmp-snooping mutual-
   exclusion was missed). Dump the fetched story descriptions to
   `user_story_bodies.md` so `_tp_scenario_extract.py` can mine `VAL-*`
   commit-validation scenarios deterministically.
7. **RFC ingestion** -- when an RFC is referenced, run
   `python3 ~/.cursor/tools/tp_rfc_ingest.py --epic <PRIMARY> --rfc <num>`
   to fetch normative clauses, diff epic-claimed scope vs full-RFC scope, and
   merge in-scope clauses into `must_requirements.json`. Store
   `rfc_<num>_clauses.json` in the TP dir.
8. **HLD / related Confluence discovery** -- search Confluence via Atlassian MCP
   (`search-company-knowledge` or Jira-linked design docs) for the epic's HLD
   and related design pages (by epic key, summary, component). Ingest into
   `epic_documentation_<PRIMARY>.md` under `### HLD and Related Design Documents`
   with `source_page:` provenance. If none found, record `no HLD found`.

9. **Stage 1e — Scenario inventory extraction (MANDATORY, deterministic + agent
   hybrid).** Build `scenario_inventory.json` under `~/SCALER/TEST/tp/<PRIMARY>/`
   in a bounded two-pass loop — the deterministic parser is the backbone; the
   agent only fills flagged blind spots.

   **Pass A — deterministic extract + self-audit:**

```bash
python3 ~/SCALER/TEST/tp/_tp_scenario_extract.py --epic <PRIMARY>
```

   Merges ALL authoritative sources (source-agnostic, no LLM):
   - **HLD** markdown (explicit `--hld-file` or the `### HLD` section of
     `epic_documentation_<PRIMARY>.md`): Group A–N items, operational flows,
     use-cases, MUST/SHALL lines.
   - **RFC + user-story + epic clauses** from `must_requirements.json`
     (`tp_rfc_ingest.py` already merged RFC clauses here).
   - **First-class user stories**: `US-<key>` items from `jira_user_stories.json`
     and from `must_requirements` `source_story` provenance (non-rejected only;
     out-of-scope stories auto-waived).
   - **Jira children** (`jira_children.json`) when present.
   Every item is `needs-coverage` or `waived{reason}` (auto-waive on
   TBD / no-need / out-of-scope / LLGR markers). Emits `source_breakdown`,
   `hld_audit`, and `scenario_audit_<PRIMARY>.json`.

   **Pass B — agent blind-spot review (the "understand the HLD" step):**
   Read the `[REVIEW]` list (zero-yield HLD headings) that Pass A printed and
   `scenario_audit_<PRIMARY>.json`. For each flagged heading, READ that HLD
   section and decide if it holds a testable scenario the regex missed. Add any
   real misses to `scenario_inventory_agent.json` (agent-authored, validated):

```json
{ "scenarios": [
  { "scenario_id": "N3", "kind": "hld_group_item", "group": "N",
    "text": "External mrouter DF FAILOVER: new DF replays on failure...",
    "status": "needs-coverage" }
] }
```

   Required per item: `scenario_id`, `text`, `kind`. A `waived` item MUST carry
   `waive_reason`. The extractor forces `source="agent"`, validates the schema
   (exit 3 on any violation — fix and re-run), and re-merges. Use
   `scenario_inventory_overrides.json` only for explicit waive/patch/remove of
   auto-extracted items (e.g. mark an HLD `H1 (*,*) SMET` TBD as waived).
   Re-run Pass A after editing either file until the audit shows 0 blind spots
   AND the coverage gate closes.

10. **First-run sweeps (before drafting TCs)** — run once per epic on run #1:
    - Component **bug-history** + analog sibling-feature bugs (e.g. Proxy-ARP →
      IGMP proxy via feature skill).
    - Pull the **best-formatted sibling Testing Task** as the format exemplar
      (`tp_get_context test_format` + `taxonomy`).
    - `tp_knowledge_lookup` for expected behavior; if `NOT_CACHED`, capture via
      `/debug-dnos` before writing TC prose.

Write `epic_documentation_<PRIMARY>[_<LINKED...>].md` under
`~/SCALER/TEST/tp/<PRIMARY>/`. For dual epics, every requirement must carry
provenance tags such as:

- `source_epic: SW-228552`
- `linked_epic: SW-241473`
- `source_story: SW-194912`
- `source_page: confluence:5485461507`

### Step 2: Normalize Sources into SQLite

Before drafting test cases, normalize the source facts into
`~/.cursor/tp-reference/db/tp_knowledge.sqlite`:

- `source_documents`: Jira issues, Confluence pages, RFCs, local rules, local skills
- `rubric_rules`: Costake rules, TP checklist categories, feature-specific rules
- `command_catalog`: show/config/clear/debug commands with category, feature, and provenance
- `flow_catalog`: reusable setup, traffic, HA, CLI, and verification flows
- `test_case_catalog`: normalized TC objects before rendering
- `dedup_fingerprints`: normalized signatures used to collapse duplicate TCs
- `coverage_links`: many-to-many traceability from TCs to epics/stories/categories/rules

Run:

```bash
python3 ~/.cursor/tools/tp_knowledge_db.py ingest-sources --tp-dir ~/SCALER/TEST/tp/<PRIMARY>
python3 ~/.cursor/tools/tp_knowledge_db.py export
```

### Step 2.5: Address-Family Treatment Classification

Before generating TC objects, classify each category for IPv4 vs IPv6 treatment
(anchor: `tp:address-family-treatment-classification`):

1. For every category, decide whether IPv4 and IPv6 exercise **different code
   paths** (ARP vs NDP, RT-2 MAC-IP, NS/NA packet types, prefix-length behavior,
   separate BGP AFI/SAFI, distinct show surfaces).
2. If different -> emit **standalone TCs per address family** (not variants).
3. If identical -> one AF-agnostic TC with an explicit note in the description.
4. Record the classification in `quality_audit.md` under `AF treatment map`.

Reference Costake `test_plan_requirements.md` AF-decomposition rules. Example:
EVPN VPLS SI + IRB requires separate IPv4 ARP and IPv6 NDP/NA TCs when mobility
or proxy-ARP/NDP behavior differs per AF.

### Step 3: Generate Normalized TC Objects

Generate TCs as structured objects first, not markdown. Apply all rubrics in this order:

1. User Story coverage -- every non-rejected User Story gets at least one TC.
2. Costake always-required categories.
3. Costake conditionally-required categories.
4. TP 24-category checklist as a coverage filter (incl. Interoperability).
5. Feature-specific skill scenario matrix and anti-scenarios.
6. Lab/topology constraints and `/TEST` automation feasibility.

Each TC object must include:

- `test_id`, `name`, `description`
- `steps[]` and `pass_criteria[]` with one-to-one mapping
- `covers_epics[]`, `covers_user_stories[]`, `covers_categories[]`
- `covers_rubric_rules[]`, `source_documents[]`, `source_skill_refs[]`
- `covers_scenarios[]` — ids from `scenario_inventory.json` (HLD A1…, MUST-NNN, OP-*)
- `verification_commands[]` with provenance status
- `automation_type` and `/TEST` recipe hints
- `dedup_fingerprint`

### Step 4: Dedup and Multi-Category Packing

Use `~/.cursor/tp-reference/dedup_and_packing.md`.

Rules:

- Same trigger + same expected behavior + same verification surface = one TC with
  multiple category tags.
- Different topology, source role, data-plane behavior, HA trigger, process,
  scale dimension, failure mode, or management interface = separate TC.
- A packed TC may cover multiple categories only if each category has explicit
  pass criteria and traceability in the manifest.
- Do not hide important scenarios in `Variants`. Costake's rule wins:
  topology/trigger/process/data-plane changes become standalone TCs.

### EVPN IRB Hierarchy Option Rule

When sources or user instructions mention EVPN as IRB, IRB hierarchy options,
`router-interface`, `default-gateway`, `host-routes`, or `irb-mac-ip`, the TP
must produce behavioral coverage, not parser-only CLI coverage:

- `/TEST create` validates syntax using `cmd search`/CLI docs and
  `commit check && rollback 0`; it does not commit.
- `/TEST run` proves each option does its job with live EVPN/BD/VRF evidence.
- If the request is about adding, removing, rebinding, or moving IRB between
  services, keep this as a pure EVPN IRB service lifecycle test. Do not couple
  the CLI lifecycle TC to PW/VPLS-source MAC-IP mobility or datapath enabler
  logic unless the user explicitly asks for PW behavior.
- IRB lifecycle coverage must include add IRB to service A, remove IRB from
  service A, move IRB from service A to service B, and prove exactly one final
  owner for the IRB.
- `default-gateway` must prove default-gateway extended-community presence when
  enabled and absence when disabled.
- `host-routes` must prove associated VRF label/RT host-route context when
  enabled and absence when disabled.
- `irb-mac-ip` must prove local IRB MAC-IP route generation/advertisement when
  enabled and absence when disabled.
- Illegal duplicate IRB ownership, option without `router-interface` parent,
  invalid enabled/disabled enum, non-existent IRB, and wrong hierarchy placement
  must be negative guards with clean rejection and no dirty candidate.

This can be packed into one TC covering `CLI`, `Sanity`, and `Defaults` only if
each hierarchy option has its own pass criterion and `/TEST` import hints keep
CREATE validation separate from RUN behavioral proof.

### EVPN IRB Service / VRF Lifecycle Permutations Rule

Anchor: `tp:irb-service-vrf-lifecycle-permutations`. When the TP includes any
EVPN IRB service (SI or EVPN-only), `/TP` MUST emit standalone behavioral TCs
covering the lifecycle permutation axes below. The single TC-CLI-01 add /
remove / move-between-services case is NOT enough -- those axes are real
lifecycle dimensions and have produced bugs (FibMgr crash on rollback, stale
PW state on SI<->EVPN move, host-route leakage across VRFs). Every TC in this
section enforces atomic semantics (all-or-nothing per commit), rollback safety
(byte-for-byte baseline restoration), and FibMgr stability.

Required axes (one TC per axis at minimum):

- IRB attached to distinct VRFs (per-VRF host-route + RT-5 + IP-VRF label
  isolation; no cross-VRF leakage).
- IRB moved between VRFs in one commit (atomic transfer; rollback restores
  baseline).
- IRB moved between two VPLS services in one commit (single-owner; no flap on
  unrelated PW peers; no label churn on unrelated peers).
- IRB moved between EVPN-SI and EVPN-only services (dual-control-plane
  transition: SI signals BOTH l2vpn-vpls SAFI 65 + l2vpn-evpn SAFI 70;
  EVPN-only signals only SAFI 70; reverse move restores SI dual signaling).
- Multiple IRB lifecycle ops bundled in the SAME commit (atomic-multi-op:
  ALL succeed or NONE applied; the failure variant proves no partial apply).
- Per-op rollback safety using BOTH `rollback 0` (uncommitted candidate) AND
  `rollback 1` (committed change); FibMgr MUST NOT crash; MAC-IP entries
  restored where retention is expected.
- Bulk move of N IRBs (target N=50) between VRFs/services in one commit
  (atomic-at-scale; commit elapsed bound asserted; FibMgr/zebra no crash;
  parallel bulk-move on a second DUT covers the load dimension).

Each TC MUST include source-qualified verification surfaces:

- `show route vrf <vrf>` per-VRF host-route counts (before/after).
- `show bgp l2vpn evpn route-type 5` for IP-Prefix per VRF.
- `show bgp l2vpn evpn route-type 2` for the IRB MAC.
- `show bgp l2vpn vpls` for SI-only signaling delta.
- `show evpn instance <name> detail` for router-interface ownership.
- `show evpn vpls-pw` for PW state on UNRELATED peers (must not flap on move).
- `show mpls label-allocation tables` for IP-VRF labels and bgp-vpls labels.
- `show evpn mac-ip-table` for MAC-IP entry retention/rebind.
- `show system process routing:fibmgrd` (and `routing:zebrad` for bulk) for
  no-NEW-core-file evidence.
- `show config compare` for byte-for-byte baseline restoration after rollback.

Negative invariants per TC:

- `no_cross_vrf_host_route_leakage`
- `no_orphan_host_route_in_old_vrf` / `no_missing_host_route_in_new_vrf`
- `no_unrelated_pw_flap_on_irb_move` / `no_label_churn_on_unrelated_pws`
- `no_duplicate_irb_ownership_after_move` (single-owner invariant)
- `si_to_evpn_stops_l2vpn_vpls_advertisement` /
  `evpn_to_si_resumes_l2vpn_vpls_advertisement` /
  `no_stale_vpls_pw_state_after_si_to_evpn`
- `no_partial_apply_on_multi_op_failure` /
  `rollback_reverts_all_ops_atomically` /
  `commit_check_detects_any_failed_op`
- `rollback_does_not_crash_fibmgr` / `rollback_0_and_rollback_1_both_clean`
- `no_partial_apply_on_bulk_move` / `no_fib_mgr_crash_at_scale` /
  `commit_time_within_bound`

`/TEST` import hints for these TCs MUST set:
`requires_atomic_commit=true`, `requires_rollback_proof=true`,
`requires_fibmgr_stability_check=true`, and
`requires_multi_op_commit=true` for atomic-multi-op + bulk-move TCs.
Debug layers MUST include `evpn-si-irb`, `fibmgrd`, `zebra`, and `wb_agent`
so a `/TEST run` failure can correlate the user-visible verdict against
the inner FibMgr / zebra path.

This rule is mandatory for any TP touching EVPN IRB. If the user explicitly
asks for a leaner scope, `/TP` MUST present the lifecycle-permutation TC list
via `AskQuestion` (multi-select + All) before dropping any axis from the plan.

### EVPN VPLS SI With IRB MAC/IP Mobility Permutation Rule

When refining SW-228552/SW-241473, use the B.11 MAC-IP handling matrix as the
canonical base and add permutation axes instead of flattening duplicates into
separate category copies.

Required axes:

- Service mode: no IRB, IRB attached, IRB removed, IRB moved between services.
- Existing state: none, local AC, VPLS PW, remote EVPN RT-2, local+remote,
  PW+remote, DGW sticky, AC link down.
- New event source: local AC, VPLS PW, remote EVPN RT-2, refresh, AC link down.
- Message type: ARP request, ARP reply, gratuitous ARP, IPv6 NS/NA, refresh probe.
- Mobility direction: AC->PW, PW->AC, PW->PW, remote->PW, remote->AC, AC refresh,
  PW refresh, AC link down.
- Option state: `default-gateway`, `host-routes`, and `irb-mac-ip`
  enabled/disabled.
- Scale/topology: single EVI, multi-EVI, multi-PW peer, PE role pair, AC
  interface variant.

Every mobility TC must require MAC table flags, MAC-IP table source/`v` flag,
BGP RT-2 advertise/withdraw/absence, forwarding-table selected path,
mobility-history event order, broadcast probe evidence for AC<->PW moves, and
proxy-ARP/NDP no-reply-to-PW invariants. Missing a required surface is
`INCONCLUSIVE`.

Basic IPv4 IRB-in-service coverage is mandatory for SW-228552/SW-241473 and
similar EVPN VPLS SI IRB plans. At least one Basic Functionality TC must prove
that normal DNOS ARP output (`show arp vrf <vrf-name>`) contains IRB-subnet
hosts learned through both local AC / local RT-2 and PW / EVPN-SI source logic,
and must cross-check the same hosts with
`show evpn arp-table instance <service_name>`, RT-2 state, and datapath owner.
Do not treat EVPN MAC-IP or EVPN ARP tables alone as sufficient Basic IPv4 IRB
service proof.

Basic must also include a minimal IRB attach baseline for one EVPN VPLS SI
service: attach one `router-interface <irb_interface>`, prove service detail
shows exactly one router-interface owner, prove the VPLS PW remains installed,
then prove one local AC host through normal VRF ARP, EVPN ARP, RT-2, and
datapath. Keep heavier per-VRF isolation, RT-5 origination/reception, policy
chains, rollback loops, and multi-service IRB moves out of Basic.

Category ownership is single-primary. A TC must appear in exactly one review
category: `category` is the owner, and `covers_categories` must contain only
that same category. If one traffic event also gives evidence for Counters,
Logs/Traces, Sanity, or Advanced behavior, record that as
`secondary_coverage_categories`, `coverage_tags`, pass criteria, or import
hints. Do not duplicate the same procedure into multiple category sections or
multiple Jira testing tasks.

Dedup fingerprint:
`existing_state + new_event_source + message_type + service_mode + expected DB/BGP/FIB outcome`.

Use Confluence `5485461507` Proxy-ARP Debug tools as `DEBUG-CHEATSHEET` evidence
only until live-validated.

### EVPN Proxy-ARP / EVPN VPLS SI Bug-Derived Flow Sweep

When refining SW-228552/SW-241473, `/TP` must run a bug-pattern sweep before
Stage 3 self-review. Search Jira/Confluence through `user-dn-mcp-server`
when MCP is available, save the compact sweep artifact under
`~/SCALER/TEST/tp/<EPIC>/company_knowledge_gap_sweep.json`, and always mine
local evidence/catalogs:

- `~/SCALER/FLOWSPEC_VPN/bug_evidence/*EVPN*SI*.md`
- `~/SCALER/TEST/catalog/evpn_mac_mobility_SW204115/`
- `~/SCALER/TEST/catalog/pw_scale_200_mobility_ha_SW204115/`
- `~/.cursor/skills/evpn-si-irb-mobility/sections/code-risk-points.md`
- `~/.cursor/skills/evpn-si-irb-mobility/sections/lab-appendix.md`

Only promote bug-derived flows that still fit the IRB routing component or
SW-241473 datapath enabler. Required automatic checks:

- Remote withdraw / `clear evpn mac-table` fallback must preserve monotonic MAC
  mobility sequence and MAC-IP/BGP/FIB consistency.
- PW-source L2N must carry `is_pw` from DP to FibMgr/Zebra; no-IRB PW packets
  remain flood-only, IRB PW packets get `v>` MAC-IP, and no PW MAC-IP RT-2 is
  advertised.
- Proxy-ARP/NDP must never reply toward VPLS PW; cheat-sheet xray/fib-manager
  commands stay `CHEATSHEET_DEBUG` until live-validated.
- Company-knowledge bug families must be considered explicitly: PW neighbor
  address/source-specific filters (`SW-252208`, `SW-228450`), IRB subnet and
  prefix-change scoping (`SW-252206`, `SW-252207`), `clear evpn mac-ip-table`
  and async clear scale (`SW-258817`, `SW-218372`), Anycast IRB / A-GW
  precedence (`SW-198381`, `SW-202894`), IPv6 link-local Proxy-NDP
  solicited-node multicast (`SW-234957`), backup NCC ARP preservation
  (`SW-238888`), host-routes FIB correctness (`SW-219658`), large EVI delete
  with MAC-IP scale (`SW-213490`), stale PW ingress labels / ARP over VPLS /
  down-bit correctness (`SW-253442`, `SW-244979`, `SW-253527`), and SI
  sub-interface move or AC shutdown under scale (`SW-262603`, `SW-263925`).
- Scale plans must support loading a service/IRB/PW matrix from file, service
  offsets, chunked dry-run commits, smart DNAAS preflight, and modifier/range
  Spirent streams.
- Scale config changes must cover scale-up, scale-down, IRB option toggles, and
  service-window moves while learned MAC-IP state exists, then prove no stale
  MAC-IP, RT-2, FIB, dirty candidate, or proxy-ARP state remains.

Promotion rule: relevant findings from the sweep must be injected into the
primary TP artifacts in the same run. Do not leave them only in
`company_knowledge_gap_sweep.json`. Update the markdown source summary, epic
documentation, normalized TC objects, `manifest.json`, `full_result.json`,
`quality_audit.md`, and `/TEST` import hints immediately.

Dedup rule for this sweep: promote a bug-derived case to a standalone TC when
the topology, trigger, datapath behavior, scale dimension, management surface,
or failure mode differs from an existing B.11/anti-scenario TC. Otherwise attach
it as `bug_derived_multipliers` on the existing normalized TC.

### Step 5: Stage 3 Self-Review and Gap Closure

Re-read:

- Costake `test_plan_requirements.md`
- `tp_checklist.json`
- feature-specific skills
- generated epic documentation
- dedup/packing report

Build an internal gap list and update TC objects in place until all mandatory
coverage passes. Save `quality_audit.md` with:

- covered user stories
- covered Costake rules
- covered TP checklist categories
- feature-specific scenario matrix coverage
- skipped categories with justification
- duplicate/packed TC report
- commands that are only `EXPECTED_LIVE_VALIDATE` or `CHEATSHEET_DEBUG`
- **MUST coverage** -- every entry in `must_requirements.json` mapped to >=1 TC;
  list unmapped MUSTs as FAIL items
- **AF treatment map** -- per-category IPv4/IPv6 classification

Run the MUST traceability gate before declaring success:

```bash
python3 ~/SCALER/TEST/tp/_tp_must_coverage_gate.py --epic <PRIMARY>
python3 ~/SCALER/TEST/tp/_tp_scenario_coverage_gate.py --epic <PRIMARY>
```

**Story-requirement depth audit (a user story often hides MANY tests).** Because
coverage is credited at story-KEY level, a rich story body can hide multiple
discrete requirements that a single covering TC masks. Dump story descriptions to
`user_story_bodies.md` and run:

```bash
python3 ~/SCALER/TEST/tp/_tp_story_requirement_audit.py --epic <PRIMARY>
```

Clear every `[GAP] ZERO`-coverage behavior/CLI story (add a TC or credit the
covering TC via `covers_user_stories`) and review every `[WARN] thin` story for
hidden sub-requirements. This is wired into `_tp_self_check.py`.

**Self-check loop (while building AND after final render)** — after each TC batch
and before declaring done, run:

```bash
python3 ~/SCALER/TEST/tp/_tp_self_check.py --epic <PRIMARY>
```

Block success until scenario coverage = 100% mapped-or-waived, MUST gate green,
and parity check 8 passes. Fix gaps in TC objects (`covers_scenarios[]`) — do NOT
hand-wave missing HLD scenarios.

Regression: tooling tests must pass before trusting gates as hard-fail in MCP:

```bash
bash ~/SCALER/TEST/tp/tests/run_tests.sh
```

### Step 6: Render Output

Render all normalized TCs to:

1. Human markdown: `test_plan_<PRIMARY>.md`
2. Jira-wiki task bodies embedded in `manifest.json`
3. `full_result.json` for `/TEST create/import`

For Jira wiki output:

- Basic/Sanity tests may use numbered steps.
- CLI/HA/Scale/Advanced tests use:
  `||*Step*||*Action*||*Command*||*Expected Result*||`
- Commands use `{{inline-code}}` or `{noformat}` for multi-line CLI.
- Keep Description concise; full test body lives in task content.

### Category Presentation Style (Jira Categories -- epic-agnostic)

For **every epic**, every main category section must follow the **Jira Categories
presentation style** (not FlowSpec-VPN or EVPN-IRB specific):

1. Start with `#### Topology Prerequisite Steps`, numbered by the **minimal**
   lab readiness for that category only. Use role names (`PE-X`, `PE-Y`, `RR-X`,
   `P-X`, `CE-X`, `AC-IF-X`, `IRB-IF-X`, `NCC-ACTIVE`, `NCC-STANDBY`, `NCP-X`)
   instead of hard-coded lab devices. State the minimum device count and which
   roles differ between scenarios (e.g., "2 PEs: PE-1 with IRB, PE-2 EVI-only").
2. Then render `#### Test Task Matrix` before detailed TC procedures, using:
   `| # | Test Task | Test ID | Purpose | Primary Verification | Pass Criteria |`.
3. Then render each TC with Jira-wiki style procedure tables:
   `||*Step*||*Action*||*Command*||*Expected Result*||`.
4. Do not hide topology prerequisites globally at the top of the TP. Repeat
   category-specific prerequisites where the category starts so `/TEST create
   from TP` imports correct lab assumptions per category.
5. Preserve this style in chat output unless the user explicitly asks for a summary.
6. Topology prerequisites are **numbered text steps**, not tables. Only test-task
   procedures use the Step / Action / Command / Expected Result table format.
7. For traffic or mobility tests, state where MAC/IP is learned first, where it
   moves next, and expected control/data-plane outcome. Traffic-generation wording
   belongs inside that learning/move description, not as an ambiguous separate step.
8. Command cells are DNOS CLI procedures, not shell snippets. Never use `&&`.
   Validate every show/config surface with `dnos_cmd_search` or `search_cli_docs`.
8. Command cells are DNOS CLI procedures, not shell snippets. Never use `&&`.
   Use `;` for sequential DNOS commands in one cell, or split into separate rows.
   Expand aliases such as `sh` to `show`. Validate every show/config surface with
   `dnos_cmd_search` or `search_cli_docs` before rendering.

#### EVPN VPLS SI + IRB example (scoped, not default)

When the epic is EVPN VPLS SI with IRB, additionally apply these rules (do **not**
apply to non-EVPN epics):

- Service names in topology prereqs: `SVC-EVPN-LOCAL`, `SVC-EVPN-SI`, `SVC-REMOTE`,
  `SVC-MOBILITY`, `SVC-HA-BASELINE`, or category-specific equivalents.
- Mobility learn/move sequencing with explicit RT-2/BGP/FIB outcomes.
- **Pair `cmd search` + `cmd help` evidence** (anchor: `tp:dnos-cmd-search-help-paired-evidence`)
  for every new DNOS command not already in cache.
- **DNOS L3 ARP/NDP cache alongside EVPN shows** (anchor: `tp:irb-l3-arp-ndp-cache-required`)
  when IRB is attached and hosts are learned from AC or PW.

### Human-POV Readability Contract (epic-agnostic, MANDATORY)

Anchor: `tp:human-pov-readability`. Every TP `test_plan_<PRIMARY>.md` MUST be
readable cold by an engineer who has never seen the epic. Emit these document
elements for **every** epic (not just EVPN/IGMP):

1. **Conventions, Role Map & Glossary** section near the top: a role map (every
   `PE-X`/`RR-Y`/`AC-IF-X`/`IRB-IF`/`ESI-n` role mapped to its meaning -- and
   ONLY its meaning; no internal/design-group alias columns, see
   `tp:no-internal-jargon-in-render`), a placeholder legend (`SVC-*`, `G/S`,
   `IP-X`, `<ms>`, scale `N`), and a glossary of feature acronyms.
2. **Reference Topologies & Addressing Plan** section: one named ASCII topology
   (`T1`, `T2`, ...) per distinct lab shape the TCs need, each with an example
   addressing line (placeholders/example values, never real lab hostnames).
3. **Base Setup** block: the canonical starting state all TCs build on, with the
   LIVE vs DESIGN/EXPECTED_LIVE_VALIDATE split called out.
4. **Stimulus & Tooling Conventions** table: how each event is *generated*
   (Spirent/host/`/HA`/`/NETCONF`/fuzzer) since the procedure `Command` column is
   the *verify* surface, plus traffic pass/fail thresholds and scale targets.
5. **Per-TC** every TC MUST carry: a `*Stimulus / tooling:*` line (how to drive
   it), a `*Teardown / restore baseline:*` line, and an explicit
   **`Topology: T#`** reference to the reference topology it uses.
6. **Step shape:** a step whose `Command` is not a device command MUST be labeled
   `META (no device command)` with a `META:` prefixed command cell. Traffic steps
   MUST state explicit source-role -> destination-role.

Validate with `~/SCALER/TEST/tp/_tp_render_lib.py` (readability lint) before
rendering. A TP missing role map, reference topologies, base setup, per-TC
stimulus/teardown, or per-TC topology link is INCOMPLETE.

### Generator Is the Single Source of Truth (epic-agnostic)

Anchor: `tp:generator-sot`. The per-epic generator/orchestrator that emits
`test_plan_*.md` + `manifest.json` + `full_result.json` is authoritative. NEVER
hand-edit the rendered markdown or manifest out-of-band: a later regen silently
destroys the edit and drifts the artifacts. All enrichment (including everything
in the Human-POV Readability Contract) MUST be implemented in the
generator/render path so a clean re-run reproduces it byte-for-stable. If drift
is detected (markdown richer than the generator output), reconcile by folding the
content back into the generator before any further regeneration.

### Protocol / Version Sub-Categorization (epic-agnostic)

Anchor: `tp:protocol-version-subcategories`. Generalizes Step 2.5
(Address-Family classification) to protocol versions. When a feature has multiple
on-the-wire versions whose code paths differ (IGMP v2/v3, MLD v1/v2, OSPFv2/v3,
BGP AFIs, etc.), each category section MUST render per-version sub-categories and
emit standalone per-version permutation TCs where the path differs (and a single
version-agnostic bucket where it does not). Tag each TC with its `version` and
render a version column in the Test Task Matrix. Out-of-scope versions (e.g. MLD
for an IGMP-only epic) are recorded as out-of-scope, not silently dropped.

### Clear / No-Form Always in CLI (epic-agnostic)

Anchor: `tp:cli-clear-noform`. Every CLI category MUST include the feature's
`clear` commands (relearn / counter reset) and `no`-form/rollback coverage, with
an explicit assertion of what the clear affects vs preserves (e.g. clears
locally-learned state but not peer-learned/remote state). Discover the exact
clear syntax via dnos-config `cmd search` / CLI docs; never invent it.

### Positive-Activates + Negative/No-Harm Per Config TC (epic-agnostic)

Anchor: `tp:positive-activates-negative-noharm`. Every config-mutating TC (any
TC that runs `configure` / `commit` / `no` / `rollback` -- i.e. CLI, Defaults,
Negative, and clear-category tests) MUST contain BOTH of the following, not just
"apply config and show the same config back":

1. A **positive expected-behavior** step that proves the knob actually DOES
   something observable, not merely that the config parses/commits. Pair the
   mutating step with an oper-state verify whose result DIFFERS from the
   pre-config baseline (e.g. "a host report is ignored before enable and is
   learned after enable" -- the knob takes effect).
2. A **negative / no-harm** guard with two parts: (a) a malformed/invalid form
   is cleanly rejected by `commit check` with no dirty candidate and a clean
   `rollback 0` (no crash, no partial apply); and (b) an unrelated sibling
   object (a second service / instance / VRF) is proven UNCHANGED by the
   operation (per-object isolation -- "nothing else breaks").

A config TC that only commits config and shows it back is INCOMPLETE. Validate
with `~/SCALER/TEST/tp/_tp_render_lib.py:validate_tc_positive_negative` before
rendering. For a NEW TP this is a hard failure; for an existing TP it is
reported as an INFO backlog by the generator until the TCs are refined. The
positive step's expected result MUST be grounded in the Feature-Knowledge
cache / dnos-config `cmd search` (never an invented "takes effect" claim), and
the negative reject syntax MUST be discovered, not guessed
(`tp:cli-clear-noform` + `dnos-cli-completion-protocol`).

### Zero-to-Hero Rendering Contract (epic-agnostic, MANDATORY)

These four anchors make every `/TP` plan readable and executable from zero by an
engineer who has never seen the epic. They are enforced by
`~/SCALER/TEST/tp/_tp_render_lib.py` and reported by every generator's
`validate_readability`. For a NEW TP they are hard failures; for an existing TP
the generator clears them via deterministic build-time augmentation passes
(see `tp:generator-sot` -- the passes live in the generator, never in the
rendered markdown).

#### No Internal Jargon in the Rendered Plan

Anchor: `tp:no-internal-jargon-in-render`. The human-facing `test_plan_*.md`
MUST contain NO internal/design-group jargon: no `HLD` tokens, no "HLD alias"
role-map column, and no `HLD use-case 1:` / `HLD B2/I2:`-style prefixes in TC
purpose prose. Design-group tags stay in `manifest.json` only (e.g. the
`hld_group` field) for traceability. Implement the strip at RENDER time
(`_tp_render_lib.strip_internal_jargon`) so the generator data may keep the tag
while the rendered prose never shows it. Validate with
`_tp_render_lib.validate_no_internal_jargon(md_text)` -- a render-level reject:
any `HLD`/`design-group` token in the rendered plan is a failure.

#### Topology Prerequisite Steps Are an Executable DNOS Build Sequence

Anchor: `tp:topology-build-steps`. Each category's "Topology Prerequisite
Steps" MUST be a NUMBERED DNOS build sequence -- not prose -- that takes a bare
lab to the topology under test, in dependency order:
loopback/underlay/IGP -> iBGP to RR with the service address-family (e.g.
`l2vpn-evpn`) -> service instance + RD/RT + transport -> AC sub-interface ->
IRB/anycast + L3 IGMP/PIM (when the use case needs L3) -> ESI for multihoming
(MH scenarios only) -> feature enable (e.g. snooping/proxy) -> baseline capture.
EVERY build step is paired with a verify `show` so the builder can confirm each
layer before the next.

Rendering rules (so the plan reads like a human wrote it):

1. **Configuration is a fenced BLOCK, never inline mid-sentence.** Represent
   each build step as a structured object (title, one-line "why", a real DNOS
   hierarchical `config` block, and `verify` shows). The renderer emits the
   config as a fenced code block followed by a `commit`. NEVER jam
   `configure ... ; commit` into prose -- the lint flags inline-config-in-prose.
2. **DNOS syntax only -- no other-vendor CLI.** Every command MUST be authentic
   DNOS, grounded byte-for-byte on a real device's running config + dnos-config
   `cmd search`. Do NOT emit Cisco/Juniper/Arista forms (`lo0.0`,
   `address-family ... activate`, `evi <n>` as a leaf when DNOS uses
   `route-distinguisher`/`route-target`, `ip igmp`/`ip pim` IOS style, `set
   protocols ...`, `switchport`, `| save file`). When in doubt, pull the block
   from the live device (`show config <path> | no-more`) and copy its shape
   (hierarchical, 2-space indent, `!` terminators).
3. **LIVE vs DESIGN.** Tag each surface `LIVE` (on the build today) vs
   `DESIGN/EXPECTED_LIVE_VALIDATE`. For surfaces not yet on the live build, take
   the syntax from the epic's CLI user-stories (the epic `cli-reference.md`),
   not from another vendor.

Validate with `_tp_render_lib.validate_category_build_steps(steps)` (accepts
structured build-step dicts; flags inline-config-in-prose and missing verify).

#### Every TC Walks the Full Zero-to-Hero Ladder

Anchor: `tp:zero-to-hero-steps`. Every functional TC MUST walk the full ladder
with no half-steps: preconditions/baseline shows -> stimulus -> control-plane
(BGP RT-3/6/7/8) -> RIB/oper-db -> datapath/forwarding -> counters ->
negative/no-harm -> teardown/restore. A TC that jumps straight to a verify
without a baseline, or proves control-plane without a datapath/forwarding check
(or vice-versa), is INCOMPLETE. Validate with
`_tp_render_lib.validate_tc_zero_to_hero(tc)`, which returns the missing ladder
phases; the generator augmentation inserts the missing baseline/datapath
bookends deterministically.

#### Control-Plane Show Required on Every Functional TC

Anchor: `tp:control-plane-show-required`. Every functional TC (Basic
Functionality / Sanity, Topology, Control-Plane/RIBs, Multihoming) MUST carry
at least one `show bgp l2vpn evpn ...` (or the feature's equivalent control-plane
route show) -- even in Basic Functionality -- so the control plane is proven, not
only the datapath. Validate with
`_tp_render_lib.validate_tc_control_plane_show(tc)`.

### TC Rich Anatomy (epic-agnostic, MANDATORY)

Anchor: `tp:tc-rich-anatomy`. Every rendered TC MUST use the expanded,
human-readable anatomy (in this exact order):

1. **What this tests** -- one sentence: the single behavior the TC proves.
2. **Purpose** -- the why / context (the remainder after the one-liner; omit if
   the one-liner already says it all). NOTE: this is the objective, NOT the
   topology. Keep topology prose in *Topology notes*, never conflate the two.
3. **Devices under test** -- a NUMBERED table (`#1/#2/#3 ...`) of role tokens
   (`PE-X`, `PE-GW`, `R1`, `RR-X`, ...) with per-device placeholder
   loopback/RD and a short note. Numbers are referenced by the step `Dev` column.
4. **Traffic actors** -- bulleted (one dot per actor): the receiver (`R1`), the
   source (`S`), the group (`G`, stated as ASM `(*,G)` or SSM `(S,G)`), any
   external querier/mrouter. Omit for pure-config TCs with no traffic.
5. **Topology** -- a fenced ASCII diagram for the TC's topology ref (T1, T2, ...).
6. **Topology notes** -- bulleted; how the roles relate (NOT the objective).
7. **Procedure** -- a table `| Step | Dev | Action | Command(s) | Expected Result |`.
   Steps are node-scoped (the `Dev` column names which device runs the step),
   stimulus steps are separated from verification steps, and the Expected column
   is specific (the exact token/state to look for).
8. **Pass criteria** -- bulleted, concise.

Rules for the anatomy:

- **Non-deterministic addressing.** Use placeholder tokens (`<lo-x>`, `IP-X`,
  `G`, `S`, `AC-IF-X`, `irbX`) in TC steps. A concrete literal is allowed ONLY
  when the test logic depends on that exact value -- for EVPN-IGMP the known
  literals are `224.0.0.X` (RFC 4541 non-IGMP flood exception) and `0.0.0.0`
  (default querier source). Real example values live once in the Reference-
  Topology addressing plan, never scattered in steps. Soft-checked by
  `quality_validator.check_placeholder_addresses`.
- **Operational language, no code identifiers** (anchor:
  `tp:no-code-identifiers`). Component/process names are fine and encouraged
  (FIBMGR, Zebra, EVPN-MNG, BGP, PIM, DataPath). Internal struct/DB/enum/library
  identifiers are forbidden in TC prose (`mrt_hold`, `block_mode`, `libigmp`,
  `BLOCK_NONE/BUM/ALL`, `*Db`, `EvpnMc*`, ...). Use plain words ("DF block-state",
  "the IGMP engine", "group-membership timer"). HARD-checked by
  `quality_validator.check_no_code_identifiers`.
- **A timer claim must name its owner.** When a TC asserts a timer (e.g. RT-6
  validity on leave), name the owning component and the show that exposes the
  countdown -- RT-6 has no timer of its own; it is withdrawn when the FIBMGR
  group-membership timer expires (`show evpn igmp-snooping multicast-db` shows
  the countdown). Do not attribute a timer to BGP/the route.

Implementation (epic-agnostic engine, SHARED): the renderer + derivation live in
`~/SCALER/TEST/tp/_tp_render_lib.py`:
`render_rich_tc(tc, L, clean, topo_titles)` and
`derive_rich_presentation(tcs, topo_meta, clean)`. Each epic generator supplies
its own `topo_meta` (devices/tokenmap/diagram/notes/actors keyed by its topology
refs) and calls the shared engine -- it does NOT re-implement the renderer. A TC
may be hand-curated (deeper, node-scoped steps + curated objective/devices) via a
per-epic `RICH_TC` registry that overrides the derived defaults. Soft-checked
(presence) by `quality_validator.check_rich_anatomy`.

### Shared MCP Validator Is the Gate (epic-agnostic, MANDATORY)

Anchor: `tp:mcp-validator-is-the-gate`. The framework rules are enforced by the
SHARED validator in the TP MCP, not by any per-epic generator. Source of truth:
`/home/dn/qa_automation/ai_test_plan/tp_agent_mcp/quality_validator.py`, exposed
as the `tp_validate_plan` and `tp_validate_syntax` MCP tools (server
`user-tp-agent-mcp`). Every `/TP` run MUST, before declaring success, call:

1. `tp_validate_plan` with the rendered markdown (+ `design_terms` from the
   epic CLI user-stories). It runs: no-internal-jargon, config-as-block, DNOS
   syntax shape, full service config hierarchy, concise pass-criteria, enough
   steps, control-plane show, no-code-identifiers, and (soft) rich-anatomy
   presence + placeholder-addresses. Hard-fail categories: jargon, inline-config,
   vendor-syntax, suspect-CLI, **code-identifier** (`mrt_hold`/`block_mode`/
   `BLOCK_*`/`*Db`/... in TC prose). Soft (reported, not fail): rich-anatomy,
   placeholder-addresses.
2. `tp_validate_syntax` with the markdown. It classifies every configure/show/
   clear command as ok | design | suspect. ZERO `suspect` commands may ship.

Do NOT re-implement these checks in a per-epic `_gen_*.py`/`_tp_render_lib.py`
copy as the source of truth; if a new check is needed, add it to the shared
`quality_validator.py` so every epic inherits it. (A thin epic-local mirror that
delegates to the shared lib is fine for fast local runs.)

### DNOS Syntax Must Be Validated, Never Invented (epic-agnostic)

Anchor: `tp:dnos-syntax-validated`. No CLI in a plan may be guessed or copied
from another vendor. For every configure/show/clear command:

1. Confirm LIVE syntax via dnos-config `cmd search` (and pull the real shape
   from a device's running config, `show config <path> | no-more`).
2. For surfaces not yet on the live build, take the syntax from the EPIC's CLI
   user-stories / `cli-reference.md` and tag it `DESIGN/EXPECTED_LIVE_VALIDATE`.
   Pass those tokens to `tp_validate_syntax` as `design_terms` so they are
   classified DESIGN, not suspect. Prefer the DNOS-native shape even for DESIGN
   commands (e.g. `clear evpn instance <svc> igmp-snooping`, NOT IOS
   `clear ip igmp snooping`).
3. `tp_validate_syntax` returning any `suspect` command is a hard fail.

#### Pre-Release Epic: Syntax Comes From the Epic User-Stories

Anchor: `tp:pre-release-syntax-from-epic`. A `/TP` is very often written BEFORE
the epic ships, so the feature's CLI/show/clear commands are NOT yet on any live
build and dnos-config `cmd search` returns nothing for them. In that case the
authoritative source is the EPIC itself, not the device:

1. Pull the feature CLI from the epic user-stories / `cli-reference.md` (Jira
   `getJiraIssue` on the epic + its CLI stories, or the cached
   `~/.cursor/knowledge_base/<feature_id>/`). Base/underlay surfaces
   (loopback, IGP, BGP, EVPN instance, RD/RT, transport) are still
   `cmd search`-confirmed LIVE; only the feature surfaces are DESIGN.
2. Pass that raw epic text to the gate as **`epic_cli_text`** (preferred) or as
   explicit `design_terms`. The validator auto-derives the DESIGN tokens
   (`quality_validator.extract_epic_cli_terms`) and classifies the not-yet-live
   feature commands as DESIGN instead of suspect - no hand-typing.
3. Tag every such command `DESIGN/EXPECTED_LIVE_VALIDATE` in the rendered plan.
   When the build ships the feature, re-run the gate WITHOUT `epic_cli_text` and
   re-confirm each DESIGN command via `cmd search` (DESIGN -> LIVE).
4. Use the DNOS-native shape even for DESIGN commands (e.g.
   `clear evpn instance <svc> igmp-snooping`, never IOS `clear ip igmp snooping`).
   A `suspect` (other-vendor) shape is a hard fail even when epic-sourced.

### Full Service Config Hierarchy in Topology Blocks (epic-agnostic)

Anchor: `tp:service-config-full-hierarchy`. When a topology/build step shows a
service config block, it MUST include the complete hierarchy, not a stub. For an
EVPN instance under `protocols bgp` that means `route-distinguisher` AND both
`export-l2vpn-evpn route-target` + `import-l2vpn-evpn route-target` (plus the
`transport-protocol` block). Validated by
`quality_validator.check_service_config_hierarchy`.

### Concise Pass-Criteria + Enough Steps (epic-agnostic)

Anchor: `tp:concise-pass-criteria` / `tp:enough-steps`. Pass criteria are crisp
one-liners (<= ~110 chars each), one per asserted outcome - not paragraphs. TC
procedure tables carry enough steps for clear end-to-end flow (target >= 4:
baseline -> stimulus -> control-plane -> datapath/verify), so a reader can run
the test top-to-bottom without guessing. Validated by
`quality_validator.check_concise_pass_criteria` + `check_enough_steps`.

### Align to Existing Jira Test Categories / Tasks (epic-agnostic)

Anchor: `tp:align-existing-jira-tests`. Before finalizing, query Jira for
issues already under the epic with issuetype in (`Test`, `Test Category`,
`Testing Task`, Zephyr tests) and any HLD "testing groups" (e.g. groups A-N).
Map each generated TC to the matching existing category/task (store
`jira_test_category` + an `hld_group` tag), reuse the established naming/grouping,
and dedup against them (extends Step 7 Jira Dedup). Do not invent a parallel
taxonomy when the epic already defines one.

### Interoperability Category Rule

Anchor: `tp:interoperability-per-vendor`. When the epic or any User Story names a
third-party vendor (Cisco, Juniper, Arista, Nokia, etc.):

1. Emit **one interop TC per named vendor** under the `Interoperability` checklist
   category (not buried as a Sanity sub-task).
2. Topology is **device-non-deterministic** but **vendor-deterministic**: role names
   carry the vendor (`CE-CISCO-X`, `PE-JUNIPER-Y`, `RR-ARISTA-Z`).
3. Cover wire-format/TLV/attribute handling, adjacency formation, and traffic/control
   exchange with that vendor's expected behavior.
4. Include a **known-limitation negative TC** per vendor when the epic or company
   knowledge documents a vendor-specific gap.
5. Use minimal topology: only the roles required for that vendor interop scenario.

### Non-Deterministic Rendering and Permutations

Anchor: `tp:non-deterministic-rendering`. All TC prose must be reproducible in any
lab without hard-coded device names or addresses:

1. **Device names** -- role-deterministic only (`PE-X`, `RR-Y`, `P-Z`, `CE-A`,
   `NCC-ACTIVE`, `NCC-STANDBY`, `NCP-X`). Never `PE-1`, `PE-4`, or lab hostnames.
2. **Addresses** -- placeholders: `IP-X`, `IP-Y`, `IP-SUBNET-X/Y`, `MAC-X`, `MAC-Y`.
3. **Traffic** -- every traffic step states explicit **source role -> destination
   role** (e.g., "Spirent host on AC-IF-X sends to IRB-IF-Y on PE-X").
4. **Config + verify pairing** -- every mutating step has a matching verification
   command; no missing knobs. Validate DNOS syntax via dnos-config MCP
   (`dnos_cmd_search`, `dnos_show_command_knowledge`, `dnos_run_show_commands`)
   and Feature-Knowledge cache before rendering.
5. **Layered show commands** -- add deeper show/trace surfaces when behavior needs
   proof beyond the primary show (control plane -> RIB -> datapath -> counters).
6. **Permutation matrix** -- complex TCs (multi-axis lifecycle, mobility, scale)
   MUST list a `permutations[]` block suggesting distinct standalone scenarios
   (not variants) for axes that change topology, trigger, or data-plane behavior.
7. Use `~/SCALER/TEST/tp/_tp_render_lib.py` for placeholder validation and
   step-shape checks before rendering.

### Category Source-of-Truth Grounding

Generalizes the Feature-Knowledge rule: command-owned categories are populated
from their owner's read-only planning/detection tools -- **never invented**.

| Category surface | Owner | Source |
|---|---|---|
| show/config/clear/behavior | Feature-Knowledge + dnos-config MCP | `~/.cursor/knowledge_base/<feature_id>/` |
| NETCONF / GNMI / SNMP / Traps | `/NETCONF` | `~/.netconf_learning.json` `epic_leafs[EPIC]`, `snmp-epic-mibs.json`, `epic_detector.py` |
| HA / System Events | `/HA` MCP | `ha_epic_plan`, `ha_scenario_plan`, `ha_prerequisites_check` |
| Scale / Load+Stress | `/SCALE` MCP | `scale_limits_lookup`, `scale_headroom_plan`, `scale_compatibility_check` |

#### (a) NETCONF / gNMI / SNMP / Traps (anchor: `tp:netconf-grounding`)

- NEVER invent YANG paths, leafs, or OIDs.
- Resolve from `epic_leafs[EPIC]` in `~/.netconf_learning.json`. If absent, run
  `/NETCONF` epic auto-detection (`~/netconf_test/epic_detector.py`: Jira -> YANG
  `cheetah_26_1/prod/dnos_monolith/yangs/*.yang` -> OpenConfig) then re-read.
- SNMP/Traps from `~/.cursor/netconf-docs/snmp-epic-mibs.json[EPIC]`; `no_mib:true`
  -> skip SNMP/Traps with justification in Skipped Categories.
- gNMI Set Replace is LOFD-destructive (`gnmi_operations_safety_matrix`) -> **negative/blocked TC only**.
- SNMP Set not production-ready (`snmp_support`) -> GET/Walk/Traps only.
- No surface -> mark `NEEDS_NETCONF_DETECTION`; do not fabricate.
- Provenance: `source: netconf_learning:epic_leafs[EPIC]` or `source: snmp-epic-mibs`.

#### (b) HA / System Events (anchor: `tp:ha-grounding`)

- In `/TP` context, HA **always assumes a basic DriveNets cluster** (active NCC +
  standby NCC + NCPs, NCM/NCF where relevant).
- Call `ha_epic_plan(epic=, feature=)` for scenario set; `ha_scenario_plan(device=,
  scenario=, feature=)` for safety gates, expected states, stop conditions;
  `ha_prerequisites_check` for prerequisites.
- Decompose per Costake HA rules (one TC per process/container/restart type/NCC
  switchover vs failover/cold vs warm/PDU) using `/HA` output -- not invented triggers.
- Cluster roles: `NCC-ACTIVE`, `NCC-STANDBY`, `NCP-X`, `NCM`, `NCF`. Concrete device
  resolved at `/TEST` run.
- Each HA TC: gate + stop-condition + guaranteed-baseline-rollback discipline.
- Provenance: `source: ha_epic_plan` / `source: ha_scenario_plan`.
- `/HA` MCP unavailable -> `NEEDS_HA_PLAN`.

#### (c) Scale / Load+Stress (anchor: `tp:scale-grounding`)

- Only when the feature maps to a **canonical limit key** in `scale_limits.json`.
- Call `scale_limits_lookup(feature=, ncp=)` for reconciled max (source + confidence
  + disagreement flags); `scale_headroom_plan(device=<role>, service=, add=N)` for
  over-limit / max-safe-add.
- Scale TCs MUST use these real numbers; record `source`+`confidence`; note disagreements.
- No mapped limit -> "no scale limit applies"; `/SCALE` unavailable -> `NEEDS_SCALE_LIMITS`.
- Provenance: `source: scale_limits_lookup`.
- Never invent scale numbers (e.g. hardcoded N=3500 without lookup).

### Step 7: Jira Dedup

Before marking a TC as `new_generated`, search Jira for existing category/task
matches under the primary and linked epics. Dedup must check exact and near
matches:

- normalized summary
- source user story
- trigger type
- expected behavior
- verification command surface

If found, mark `found_in_jira` with `jira_key` and preserve coverage links.

### Step 8: Save Output

Save to `~/SCALER/TEST/tp/<EPIC_ID>/`:

- `epic_documentation_<PRIMARY>[_<LINKED...>].md`
- `test_plan_<PRIMARY>.md`
- `manifest.json`
- `full_result.json`
- `quality_audit.md`

**Jira push is NEVER automatic.** Only create Jira tasks if the user explicitly
requested `--push` / `push_to_jira: true` in the request or asks after review.

### Step 6: Create /TEST automation (agent-driven, per test case)

After Step 5, use **AskQuestion**:

- **Prompt:** "TP saved with N tests across M categories. Create runnable automation recipes?"
- **Options:**
  - `[Full automation (agent-driven)]` -- agent runs /TEST CREATE logic per test (RECOMMENDED)
  - `[Quick scaffold only]` -- runs `tp_automation_builder.py` for stub recipes (offline/fast)
  - `[Select categories first]` -- pick categories, then full or scaffold
  - `[Skip]` -- user runs `/TEST import-tp` later

#### Full Automation Mode (RECOMMENDED)

For each test case in the manifest, the agent does what `/TEST create` does:

1. **Read the test_flow** from the manifest -- extract steps, commands, pass criteria
2. **Resolve target device** -- AskQuestion or use topology from request
   - If user's request specified a device: use it
   - Otherwise: use Network Mapper `list_devices` or `~/SCALER/db/devices.json`
3. **Device discovery** -- parallel MCP calls:
   - `get_device_config(device)` -- current running config
   - `get_device_interfaces(device)` -- interface list and states
   - `run_show_command(device, "show system | no-more")` -- node table, NCP IDs
4. **Prerequisite analysis** -- from `prerequisite-engine.md` for this test type:
   - For HA tests: standby NCC ready, BGP sessions established, traffic path exists
   - For CLI tests: device reachable, CLI responsive, no pending commits
   - For traffic tests: interfaces up, VLANs provisioned, counters clearable
   - For scale tests: baseline resource measurements captured
5. **DNOS syntax validation** (MANDATORY) -- for every command in the test:
   - `search_cli_docs(keyword)` for each show command
   - `validate_config(device, config_text)` for config blocks
   - Container-prefixed process names from `~/.cursor/dnos-cli-completions.json`
6. **Generate recipe.json** -- full recipe with:
   - Validated show commands in `before_snapshot` and `after_snapshot`
   - Real prerequisite checks with `fix_via` sub-commands
   - Device-specific HA trigger commands (resolved NCC IDs)
   - Pass criteria extracted from TP test_flow
7. **Generate orchestrator.py** -- from `orchestrator-patterns.md` template:
   - HA tests: 14-layer verdict, poll_recovery, crash detection
   - CLI tests: config apply/verify/rollback cycle
   - Traffic tests: Spirent stream setup, counter verification
   - Show-compare tests: before/after diff with expected values
8. **Save to catalog** -- `~/SCALER/TEST/catalog/TEST_<epic>_<cat>_<idx>/`
   - `recipe.json`, `orchestrator.py`, `README.md`
9. **Report summary** per test: test_id, type, device, prerequisites (pass/fail), warnings

**If device is not available** (general mode):
- Generate recipes with `device: "any"` and placeholder NCP/interface values
- Mark prerequisites as "to-be-resolved" with notes on what discovery is needed
- The recipes are still structurally complete -- just need device resolution at run time

#### Quick Scaffold Mode (offline fallback)

Runs `tp_automation_builder.py` which creates stub recipes without device validation.
Useful when MCP/devices are unavailable or for batch scaffolding.

```bash
python3 ~/SCALER/TEST/tools/tp_automation_builder.py <EPIC> --mode smart_default
```

## Jira Push Protocol
When pushing to Jira (only when user explicitly requested):
1. For each category: create a "Test" issue under the EPIC (or find existing)
2. For each task: create a sub-task under the category issue
3. Description format: Jira wiki markup (h1, h2, ||table||, {{code}}, {noformat})
4. Set labels: ["AI-Generated-TP", "TP-Checklist"]
5. Set QA owner if provided

## Integration with /TEST

After full automation (Step 6), the agent has already created production-ready recipes.
Tell the user:
"Created N automation recipes in ~/SCALER/TEST/catalog/. Run `/TEST run <test-id> on <device>`
to execute, or `/TEST` to see the full catalog."

If user chose scaffold-only or skipped Step 6, tell them:
"TP manifest saved to ~/SCALER/TEST/tp/<EPIC_ID>/manifest.json. Run `/TEST import-tp <EPIC_ID> --full`
in Cursor for agent-driven automation creation, or `--scaffold` for quick stubs."

## Error Handling
- If EPIC fetch fails: warn user, continue with manual input
- If a task generation fails: log error, continue with next task
- If Jira push fails: save locally, report which tasks failed to push
- Never stop the entire generation for a single task failure

## Canonical Category Taxonomy + Deterministic Classifier (epic-agnostic, MANDATORY)

Anchor: `tp:canonical-category-taxonomy`. Every `/TP` plan MUST use ONE fixed
category spine with fixed names and fixed order, so any two epics come out the
same shape. Do NOT improvise per-epic category names (that is how the
"Basic functionality + Topology" / "Advanced Functionality / Various RIBs"
drift happened). The only per-epic variation is WHICH topologies appear under
Basic Functionality and WHICH conditional categories are in scope.

### Fixed spine (always present, in this order)

1. **Basic Functionality** -- "does the feature work at all?": basic/reference
   topology + happy-flow validation of the core behavior + one simple negative.
   Emitted as ONE sub-category PER required deployment topology the epic
   defines (never a single lumped bucket). Topology-agnostic feature basics
   (per-service enable/disable, version learning smoke, etc.) live in the
   base/single-node topology sub-category.
2. **Topology Scenarios** -- deeper full-path / HLD use-case walks and
   multi-node (3+ device) variants, per topology. A DISTINCT category, never
   merged into Basic Functionality.
3. **Advanced Functionality** -- ONE category for protocol correctness beyond
   happy flow: control-plane / RIB objects and flows, protocol/version state
   machines, multihoming, special forwarding (mrouter / RFC forwarding
   exceptions), summarization, and negative-protocol (fuzzer / RFC 7606
   robustness). Control-plane / RIBs and Multihoming are SUB-GROUPS inside
   Advanced Functionality -- they are NOT their own top-level categories.
4. **CLI** -- the management CLI surface (see the CLI Category System below).
5. **Scale** -- max / limit dimensions with real numbers.
6. **Stress** -- load + churn + soak (repeat / toggle / move under load), with
   the full sub-task spine + six oracles of the Stress Category System below
   (`tp:stress-category-system`). ALWAYS a separate category from Scale.
7. **HA** -- process restarts, NCC switchover / failover, GR / NSF recovery.
8. **Interoperability** -- vendor-AGNOSTIC category; one vendor-SPECIFIC
   testing task per named vendor, each placed in a vendor-tagged topology
   (role `PE-VENDOR-Y`). When the epic/HLD names the scenario a vendor task
   exercises, map that task to it (e.g. a Juniper task -> HLD group
   "G -- Negative BGP / RFC 7606" for cross-vendor malformed-route handling).
   Keep a same-vendor (DN-to-DN) baseline task as the control reference.
9. **Netconf / GNMI** -- programmatic management surface (YANG / OpenConfig /
   gNMI).

**Sanity == Basic Functionality.** There is NO standalone "Sanity" category;
the classic checklist "Sanity" IS the Basic Functionality (happy-flow) layer.

### Conditional categories (emit only when the epic exposes the surface)

Counters, Logs/Traces, Traps/SNMP, System Events, Upgrade/Downgrade, Defaults,
VRF Testing, IPv4/IPv6, Interface Types/Services, Negative Testing, System
Resources, DNOR, Logs Rotation, Sanitizer. If a surface does not apply, record
it under Skipped Categories with a one-line justification -- never silently
drop it.

### Deterministic classifier (first match wins)

Classify every TC by this fixed decision order so placement is reproducible:

1. Management CLI surface (configure / show / clear / help / rollback /
   commit-negative)? -> **CLI**.
2. Programmatic management (YANG / gNMI) or SNMP / Traps? -> **Netconf/GNMI**
   (or Traps/SNMP).
3. Scale-limit test? -> **Scale**. Load / churn / soak test? -> **Stress**.
4. Resiliency (process restart / switchover / GR)? -> **HA**.
5. Cross-vendor? -> **Interoperability**.
6. Pure happy-flow "feature works on this topology" + simple negative?
   -> **Basic Functionality** (matching topology sub-category).
7. Deeper per-topology full-path / use-case walk? -> **Topology Scenarios**.
8. Otherwise (control-plane objects, FSMs, multihoming, mrouter, summarization,
   negative-protocol) -> **Advanced Functionality**.

## CLI Category System (epic-agnostic, MANDATORY)

Anchor: `tp:cli-category-system`. Source template: the DriveNets CLI Test
Category (e.g. SW-191709 "EVPN Proxy ARP/NDP | CLI"). The CLI category is
STRUCTURED into testing-task sub-categories, each emitted ONLY if the epic has
that surface:

- **1. Configuration**
- **2. Show commands**
- **3. Clear command**

**Enumeration rule.** The Configuration sub-category MUST enumerate EVERY new
config option the epic introduces (discovered from the epic `cli-reference` /
CLI user-stories), not only the obvious ones -- each option gets its own knob
TC running the A-H matrix. This explicitly includes non-obvious enablers such
as adding an interface into a protocol (e.g. adding an IRB into IGMP and PIM:
`protocols igmp interface <irb>` + `protocols pim address-family ipv4 interface
<irb>`). A knob exercised only indirectly by another category is NOT covered.

**Prerequisite rule (Show / Clear).** Before testing a Show or Clear command, a
prerequisite step MUST first establish AND verify the real populated state the
command operates on -- never test show/clear against empty or broken state.

### Per-knob Configuration matrix (A-H) -- run for EACH new CLI option

- **A. Value-space** -- each value class: valid nominal, min, max,
  just-out-of-range (reject), impossible / wrong-type (e.g. MAC where IP is
  expected, string where an enum is expected), zero / empty, and any special
  sentinel (e.g. `0.0.0.0` / default). Valid values accepted (positive
  takes-effect); invalid / out-of-range / impossible cleanly rejected by
  `commit check` with no dirty candidate.
- **B. Hierarchy + precedence** -- where applicable configure under the global
  hierarchy AND under the specific (per-instance / per-EVI / per-interface)
  hierarchy; set conflicting values at both levels and verify the SPECIFIC
  level wins.
- **C. Delete + rollback** -- `no`-form + `rollback 1` from EACH enclosing
  hierarchy level of the knob (leaf option -> instance -> section ->
  `network-services` -> feature section); baseline restored byte-for-byte at
  every level.
- **D. Change / re-bind** -- change the option's value; change / re-point the
  referenced object it binds (routing-interface / IRB / VRF / target); verify
  the change takes effect and the old binding is cleanly released.
- **E. Datastore replace** -- `lofd` (load-override factory-default -- the
  command that WIPES the entire configuration DB) + `rollback 1` restores the
  committed feature config; and load-from-file (merge / override); baseline
  restored, no stale knob.
- **F. Persistence** -- system restart: the committed knob persists across
  reboot and oper-state re-derives.
- **G. Config-during-restart** -- change config WHILE the feature's owning
  daemons restart (generalize SW-191709 "Zebra / cmc / em" to the epic's
  daemons); no crash, no half-applied config, datastore == oper-state after
  recovery.
- **H. Verify sync to vtysh** -- after each change / commit, confirm the knob
  propagated into the bgpd / zebra vtysh running-config in the correct context
  / address-family; no NETCONF/CLI-datastore vs vtysh divergence and no
  cross-AFI / cross-context leak (ref `dnos-vtysh-traces-config-leak`).

Every config-mutating knob also keeps the positive-activates + negative/no-harm
contract (`tp:positive-activates-negative-noharm`).

### Show commands sub-category

Enumerate EVERY show surface the feature exposes (from `cli-reference` and the
union of all TC verification surfaces). For each: prerequisite populate + verify
real state, then run ALL permutations and ALL pipe filters
(`include` / `exclude` / `find` / `count` / `no-more` / `flatten` / `detail` +
instance / route-type / group selectors) and assert NO ANOMALIES (no crash /
hang / truncation; consistent counts; correct fields across every filter and
permutation). A show that appears only as a verification step inside a
functional TC is NOT considered covered by the Show sub-category.

### Clear command sub-category

Enumerate every `clear` the feature provides. Prerequisite: establish learned
state; run the clear; assert exactly WHAT IS CLEARED vs PRESERVED (e.g.
locally-learned cleared, peer-learned / remote preserved), that relearn works,
and that no stale state remains (`tp:cli-clear-noform`).

## Stress Category System (epic-agnostic, MANDATORY)

Anchor: `tp:stress-category-system`. Source templates: the DriveNets Stress
Test Categories that already PASSED on comparable features -- EVPN-VPLS SI IRB
| Stress (SW-265295: sub-tasks Traffic/Soak/Memory, Scale & Config Churn,
Lifecycle & Atomic Commit), EVPN-ELAN SI | Stress (SW-204180, TOD overnight
churn), EVPN-VPWS | Stress (SW-189719/SW-235545), and the BGP stress families
(Flowspec rapid session-flap-under-load SW-236392/3, BGP-BMP SW-229674, BGP
restart under high route churn ART-12352). Stress is NOT "Scale with a bigger
number"; Scale proves a static limit, Stress proves stability over TIME, CHURN,
and CONCURRENCY. Stress is ALWAYS its own category, never merged into Scale.

### Fixed Stress sub-task spine (emit each sub-task the epic can support)

- **1. Traffic, Soak & Memory** -- the feature runs under sustained real
  traffic for a stated LONG duration and a high-rate event loop, and process
  memory is proven leak-free.
- **2. Scale & Config Churn** -- repeated add/move/remove of the feature's
  scaled objects (interfaces / services / sessions / routes / groups) in
  batched commits, single-DUT and (where a lab exists) multi-DUT concurrently.
- **3. Lifecycle & Atomic-Commit under load** -- enable/disable, re-bind, and
  move the feature's objects WHILE traffic + churn run, using atomic
  all-or-nothing commits with `rollback 0` and `rollback 1` proof.

### Six mandatory Stress oracles (every Stress TC asserts the applicable set)

1. **Traffic + bounded loss.** Stress without traffic is not stress. Drive real
   traffic (Spirent/DNAAS -- always preflight, record stream ids/rates/sizes/
   tags/expected egress) continuously or sampled, and assert loss stays within
   an explicit bound with the correct final forwarding owner, monotonic
   sequence numbers, and no duplicate table rows.
2. **Soak + duration gate.** Run for the stated duration or cycle count (e.g.
   24 h soak, 30 min event loop). Early stop = FAIL unless an external lab
   outage. No drift / no unexpected reconvergence across the window.
3. **Memory-leak / RSS trend.** Run a long add/remove cycle loop (e.g. 1000
   cycles) and prove the owning daemons' RSS returns to a plateau (no unbounded
   growth), backed by the `process_abnormal_memory_usage` /
   `process_memory_*_level` monitoring events.
4. **Process stability / no new core.** Baseline the owning daemons and core
   counters; after the run assert NO restart and NO new core for the feature's
   processes (generalize the epic's daemons -- e.g. fibmgrd/zebra/bgpd/
   wb_agent/neighbor-manager). Watch `system_process_restart` /
   `system_process_failed`.
5. **Baseline -> periodic -> final compare.** Capture a full baseline, take
   PERIODIC snapshots during the run, and compare final vs baseline
   byte-for-byte (config compare clean, control-plane + datapath converged,
   no residual/stale object).
6. **Frontend/backend parity.** After churn the backend routing-shell / vtysh
   view MUST match the DNOS frontend CLI before PASS (no datastore vs oper
   divergence; ref `dnos-vtysh-traces-config-leak`).

### Concrete-parameter rule (no hand-wavy stress)

Every Stress TC MUST state concrete, measurable parameters -- rate
(events/min), volume (total events), duration (h/min), cycle count, object
count, and traffic rate -- so the run is repeatable and gradeable. "Repeatedly"
/ "under load" with no numbers is a defect. Prefer the proven anchors: 60
events/min x 30 min = 1800 events; 24 h soak; 1000 add/remove memory cycles;
N-object churn x M cycles; concurrent multi-DUT (e.g. 50 objects/DUT).

### TOD overnight driver + mixed concurrent churn

Where the feature supports it, drive an overnight Time-of-Day (TOD) permutation
sweep (config change / migrate back-and-forth / mobility / clear protocol /
shut+move access / clear counters / LOFD + `rollback 1` / HA switchover /
restart / identity switch such as site-id or DF re-election), and include at
least one MIXED-concurrent-churn TC that runs several churn classes
SIMULTANEOUSLY while traffic flows (not one-knob-at-a-time). `/TEST` import
hints for the Stress category MUST set `requires_traffic=true`,
`requires_soak_duration`, `requires_memory_trend_check=true`,
`requires_process_stability_check=true`, and (for the atomic sub-task)
`requires_atomic_commit=true` + `requires_rollback_proof=true`.

## Every TC is RICH-anatomy (epic-agnostic, MANDATORY)

Anchor: `tp:every-tc-rich-anatomy`. `/TP` MUST ALWAYS write tests in the RICH_TC
format. EVERY test case in a `/TP` plan -- in every category, for every epic --
MUST be authored in the curated RICH_TC style. The generic auto-derived fallback
(single generic device row, `Dev` = `-`, one command per step) is NOT acceptable
for a finished TP. A finished TC MUST carry:

- **Objective + Purpose** -- ONE crisp sentence each (headline only): "What
  this tests" = the observable outcome; "Purpose" = the why/risk. Keep them
  tight; the detail belongs in the Procedure + Pass criteria, not in these two
  lines. The renderer enforces this with a lead-clause concision
  (`tp:concise-what-purpose` in `_tp_render_lib._concise`) -- full text is kept
  in the structured artifacts, only the rendered headline is trimmed.
- **Devices under test** -- a numbered role table (per-TC, or inherited from the
  topology map when the scenario matches it exactly).
- **Traffic actors + Topology diagram + notes** -- for any TC that moves traffic.
- **Node-scoped Procedure** -- every step's `Dev` column names the acting node
  (`#1 PE-X`, `#2 PE-Y`, `datapath`, `all`), NOT a bare `-`.
- **Stimulus-vs-verify split** -- stimulus steps are explicit (a `-` command,
  "verified next"); verify steps carry the show/verify command(s).
- **Feature-accurate, multi-command steps** -- each verify step lists the real
  DNOS command(s) (multiple where a single check needs them) with a detailed,
  feature-specific Expected Result -- not a paraphrase.
- **Pass criteria** -- explicit, gradeable bullets.

Reference exemplar: the SAN-05 (centralized anycast IRB) curated entry. New TCs
inherit shared per-topology device/diagram/notes maps and carry the deep
curation (objective + node-scoped steps + pass criteria).

**Enforced in two always-on places (do not skip):**
- Per-generator: `_gen_*.py` `validate_readability` -> `every-tc-rich-anatomy`
  FAILs the run for any TC not hand-curated in `RICH_TC`.
- Shared post-write gate (runs for EVERY epic): `_tp_parity_gate.py` checks 7
  ("Rich anatomy") and **check 8 ("Scenario coverage closed")** FAIL when any
  needs-coverage inventory item is unmapped; INFO-skip when no inventory file.
  The reusable contract is `_tp_render_lib.validate_tc_rich_anatomy(tc)` and
  `_tp_scenario_coverage_gate.run_gate()`. Legacy plans with no rich signal
  degrade to INFO-skip - regenerate them with the RICH_TC template to bring
  them into compliance.

**Mandatory Post-Write Gate list (every epic, run #1):**

1. `_tp_scenario_extract.py --epic <EPIC>` (refresh inventory if sources changed)
2. `_tp_scenario_coverage_gate.py --epic <EPIC>` — exit 0 required
3. `_tp_must_coverage_gate.py --epic <EPIC>` — exit 0 required
4. `_tp_parity_gate.py --epic <EPIC>` — 8/8 checks (check 8 INFO if no inventory)
5. `tp_validate_plan` (MCP) — `scenario_coverage` WARN-first until rollout
6. `_tp_self_check.py --epic <EPIC>` — combined loop

Auto-derivation is a stopgap while drafting, never the shipped shape.

### Syntax source-of-truth ladder (spec-binding gate)

1. **Pre-implementation:** user story `**cmd syntax:**` blocks (`SPEC_USER_STORY`) + version-matched cheetah CLI RSTs (`SPEC_RST`) from git-resolved checkout (no silent tip fallback; missing checkout = `BLOCKER` with `git worktree add` cmd).
2. **Post-implementation (`shipped_in_lab`):** `dnos_cmd_search` then `?`-completion on active lab device; `?`-completion wins when cmd-search is stale; both null -> `UNBOUND_LIVE`.
3. **Drift:** live != SPEC -> `DRIFT` (developer bug); file Jira comment, do not rewrite TP.

Auto-runs in `_tp_self_check.py` (strict-refine default): `_tp_epic_version.py` -> `_tp_cli_spec_harvester.py` -> `_tp_spec_binding_gate.py --strict`.

#### System-architect CLI story = syntax source of truth + AUTO-NOTE divergences (epic-agnostic, MANDATORY)

Anchor: `tp:sa-syntax-sot-and-divergence-capture`. Applies to EVERY epic, automatically -- no user prompt needed.

1. **The system-architect who OWNS the CLI user story is the source of truth for CLI syntax (the spec).**
   - For every `configure` / `show` / `clear` command a TP asserts, bind its syntax to the CLI user story that defines it (the `**cmd syntax:**` / `**cmd level:**` block), and record that story's key + its SA owner (resolve via the Jira story `reporter`, else `assignee`). CLI user stories describe the INTENDED/planned syntax even for not-yet-shipped behavior.
   - Precedence: **SA CLI story governs the TP's intended syntax pre-live** (mark such commands `EXPECTED_LIVE_VALIDATE`). **Live-validated syntax (device / knowledge cache) wins for a runnable `/TEST`.** Merged-code CLI (RST/VTY on the version-matched checkout) is corroborating evidence, NOT authority over the SA story.
   - Never silently rewrite a TP away from the SA-story syntax because code differs -- record the divergence (next point) and keep the SA syntax as the spec until live proves otherwise.

2. **When the agent finds a syntax divergence, it MUST auto-note it (no prompt).** A divergence = any mismatch among the three sources for the same command: `SPEC_USER_STORY` (SA story) vs `SPEC_CODE` (branch RST/VTY/autogen) vs `LIVE` (device / cache). On detection, append a record to `~/SCALER/TEST/tp/<EPIC>/syntax_divergences.json` (atomic write) AND push it into the feature knowledge cache via `debug_knowledge_capture` (so `/debug-dnos` and future `/TP` runs inherit it). Each record carries:
   - `command_role` (e.g. "snoop-DB show"), `story_value` + `story_key` + `sa_owner`, `code_value` + `branch` + `commit`, `live_value` (or `UNKNOWN`),
   - `status`: `STORY_ONLY` (in story, absent in code) | `CODE_RENAMED` (code differs from story) | `LIVE_CONFIRMED_STORY` | `LIVE_CONFIRMED_CODE` | `UNRESOLVED`,
   - `first_build_action`: the exact command(s) to run on the first lab build to resolve it (run all candidates; whichever the CLI accepts is truth -> cache it),
   - `blast_radius`: count of TCs referencing the disputed token.
   - Also surface a one-line summary in `quality_audit.md` under a "Syntax divergences (verify on first build)" heading so a human sees it without opening JSON.

3. **Resolution flow (deterministic):** pre-live -> keep SA-story syntax, TC verification marked `EXPECTED_LIVE_VALIDATE`, divergence recorded. First lab build -> run each divergence's `first_build_action`; on live result, update the cache to the accepted form and run `/TP improve <EPIC>` to bind the accepted syntax byte-for-byte. If the box rejects the SA-story syntax AND accepts nothing equivalent, that is a real find (CLI-not-implemented or late rename) -> raise it (Jira comment on the CLI story, cc the SA owner), do not quietly "fix" the TP to match code.

Canonical helper: `_tp_syntax_divergence.py record|list|render --epic SW-XXXXX` (atomic JSON, feeds `quality_audit.md`). The spec-binding gate emits divergences into this store rather than only failing.

## TC Authoring Rigor (epic-agnostic, MANDATORY)

Anchor: `tp:tc-authoring-rigor`. A RICH_TC is not "done" just because it has the
anatomy shape. Every TC MUST also satisfy these EIGHT content contracts. All of
them stay NON-DETERMINISTIC (role/placeholder tokens) so `/TEST` binds them to
the real lab; the TP says WHAT, `/TEST` supplies the concrete HOW.

1. **Complete per-DUT configuration suggestions (incl. the IRB itself).** Every
   TC that configures or depends on built state MUST show the actual DNOS config
   each DUT needs, in the `Configuration suggestions (per DUT)` block, FLATTEN
   one-liners preferred. This is the WHOLE delta the TC needs, not just the
   feature knob: the EVPN instance / AC, AND -- for any IRB/anycast TC -- the IRB
   interface itself and its binding, e.g.
   `interfaces irbX ipv4-address <anycast-gw-ip>/<len>` +
   `network-services evpn instance SVC-IGMP router-interface irbX` +
   `network-services evpn instance SVC-IGMP router-interface irbX default-gateway <default-gateway>`
   (note "same anycast IP/MAC on every anycast PE"), then the feature knob
   (`... protocols igmp-snooping admin-state enabled`, `protocols igmp/pim
   interface irbX admin-state enabled`). If a step says "enable X", the config
   for X on the right DUT is shown. Placeholders only (`<anycast-gw-ip>`,
   `<len>`, `<default-gateway>`) -- never lab-specific values.
2. **Real, validated syntax only (no invented commands).** Every configure /
   show / clear MUST be discovered via `dnos_cmd_search` / cli-reference before
   use; never guessed. Known traps: `show network-services evpn` / bare
   `show network-services` are NOT operational -- use `show evpn instance <svc>`
   / `show evpn instance <svc> detail` and `show config network-services evpn
   instance <svc>`. A BAD_COMMANDS guard in the generator FAILs on known-invalid
   forms.
3. **Progressive re-verification (re-check prior-step state).** After a change,
   RE-OBSERVE how earlier-established objects evolve -- e.g. after enabling
   igmp-snooping + first RT-6, re-check that the RT-3 IMET now carries the
   Multicast-Flags EC (I-bit) absent in the pre-enable baseline. Each TC folds at
   least one delta-recheck of a previously-captured object.
4. **Cross-device observability.** Verification spans EVERY relevant DUT -- the
   originator PE, the remote/peer PE(s) that import the route, and the RR where
   applicable -- not just the acting node. A control-plane change is proven only
   when sender AND receiver views agree. The `Dev` column names the acting node
   for every step (`#1 PE-X`, `#2 PE-Y`, `datapath`, `all`).
4b. **Verification must PROVE the Expected** (anchor: `tp:verification-relevance`,
   TP-wide). Each step's Verification command(s) must surface evidence for that
   step's Expected. Standing gate: `_tp_verify_relevance_lint.py --epic SW-XXXXX`
   (MED+ must be 0 after every regen). Fix DETERMINISTICALLY via an
   `apply_verification_relevance()` pass (after `apply_rich()`): CONFIG-DEFAULT ->
   `show config ... | flatten` (knob absent) + `show evpn instance <svc> detail`
   (effective value), NOT a runtime group-DB show, and do not match feature names
   containing "default"; RT-ORIGINATION -> append `show bgp l2vpn evpn route-type N`
   (additive; not for receive/schedule/hold/treat-as-withdraw);    ON-WIRE query/report
   emission -> TX counter block in `show evpn instance <svc> detail` (capture-free,
   tool-agnostic); EMPTY verify with a positive assertion -> fill with the proving
   show (skip benign driver/"verified next" rows).
4c. **BGP feature -> full BGP show surface** (anchor: `tp:bgp-feature-show-coverage`,
   TP-wide). Any epic introducing/affecting a BGP route-type or AFI must, in the CLI
   category, exercise the full surface for the new route-types - not just the
   route-type list. Discover the live subtree first (`dnos_cmd_search` for AFI /
   `route-type` / `neighbors` / `nlri` / `prefix-counts` / `maximum-prefix` on a real
   PE), then cover: L1 route-type list; L2 neighbor advertised-routes/received-routes;
   L3 single-NLRI full attrs (RT + Multicast-Flags EC / EVI-RT EC / PMSI); RD-scoped
   `rd <rd>`; per-neighbor `prefix-counts` + per-RT `received-routes | include type:=N`;
   `bestpath-compare` (MH RT-7/8); PMSI (RT-3 IMET); and a `maximum-prefix` guardrail TC
   (limit/threshold/exceed-action/restart-interval; the new RTs count toward the cap;
   may live in Scale). Exclude general shows not changed by the epic (dampened-routes,
   flap-statistics; summary reflects RTs only in the aggregate). Standing gate:
   `_tp_bgp_show_coverage_lint.py --epic SW-XXXXX` (in `_tp_self_check.py`; no-op PASS for
   non-BGP epics). Write any newly-discovered live syntax back to both dnos-cli-discoveries twins.
4d. **Counter feature -> counter contract** (anchor: `tp:counter-coverage`, TP-wide).
   Any epic introducing/affecting counters/statistics must prove the counter MOVES and
   RESETS, not just renders: DELTA (after-minus-before == the driven events, not merely
   "non-zero"); CLEAR (`clear ... counters` -> zero, no stale/negative); SCOPE
   (per-instance and/or per-neighbor/per-interface/per-port, whichever the feature
   exposes); and, if counters are opt-in, ENABLE (enable-then-count / off-then-frozen).
   Discover the counter show/clear/enable syntax live (`dnos_cmd_search`) - never guess.
   Standing gate: `_tp_counter_coverage_lint.py --epic SW-XXXXX` (in `_tp_self_check.py`;
   no-op PASS for non-counter epics).
4e. **Per-TC Traffic Flow accuracy** (anchor: `tp:per-tc-traffic-flow`, TP-wide,
   MANDATORY). The per-TC `*Traffic Flow (ingress -> egress)*` block MUST be accurate
   for THAT TC - never a blanket per-topology data-plane paste on a TC that forwards
   nothing. Derive it DETERMINISTICALLY (never hand-edit per TC): real FORWARDING TCs
   (carry `requires_traffic` / drive a stream) keep the per-topology data-plane flow
   (source -> interested-OIFs + the named dark ports at 0 frames); CLI / observability /
   control-plane show TCs that measure NO data plane (no `requires_traffic`) OVERRIDE
   the pasted sentence with a CONTROL-STIMULUS-accurate line - the learning stimulus
   that populates the surface -> the resulting RT/state -> what the show renders -
   ending with "No data-plane forwarding is measured in this TC (control/CLI
   observability)." Implement as an `apply_per_tc_traffic_flow()` pass that runs AFTER
   `apply_flatten_config()` (which sets the per-topology flow), flips only the
   no-data-plane TCs (stimulus/RT/render text derived from the TC's own show surface),
   and prints the annotated count. A `show bgp ... route-type 6` TC proves an NLRI
   renders - it forwards nothing - so its Traffic Flow reads as control-stimulus, not
   "source S -> receiver R1".
5. **Non-deterministic traffic description (NOT encap specifics).** When a step
   asserts a forwarding/coexistence property it MUST describe the traffic by
   SOURCE, DESTINATION, INGRESS (which PE + its AC), and EGRESS (target PE + AC /
   OIF), plus direction and class (unicast / multicast / BUM), and pair it with a
   loss/delivery expectation. Do NOT bake in rate / packet-size / VLAN /
   protocol-encap -- those are `/TEST`'s job via `dnos_dnaas_spirent_preflight`.
   For coexistence claims, state BOTH the unicast flow (src->dst, ingress/egress
   AC) AND the multicast flow (src->group, ingress AC -> interested OIFs)
   together.
6. **Traffic generator is a first-class device + integrated traffic steps.** The
   tester is a numbered row in the Devices table (with its port roles), and
   traffic is INTEGRATED numbered procedure steps -- preflight/arm the flow, start
   the described source->dest flow(s) on the named ingress AC, then verify no
   loss at the egress AC (egress-AC counters: source TX vs DNOS AC RX / drops) --
   NOT a single opaque token. Non-deterministic: name the flow by role/interface;
   the concrete rate/size/encap are chosen at run time.
7. **Topology illustration per TC.** Every TC carries a diagram that shows the
   participating DUTs, the RR, the tester ports, and the source->receiver + AC /
   IRB wiring for THIS scenario (not a generic category picture).
8. **Tool-agnostic output (network language only).** The rendered TP MUST read
   as plain, vendor/tool-neutral network language and MUST NEVER name a skill,
   MCP server, or tool -- no `/SPIRENT`, `/TEST`, `/HA`, `/NETCONF`, `/SCALE`,
   `Spirent`, `DNAAS`, `dnos_dnaas_*`, `ha_test_run`, MCP tool names, etc.
   Describe the intent ("emulated host sends an IGMP report", "traffic generator
   streams source S->G", "verify no loss at the egress AC", "restart the process
   via the lab's controlled method"); `/TEST` maps that intent to the actual
   tools at run time. This is machine-guarded in the generator
   (`validate_readability` -> `tool-agnostic`), which FAILs the run on any tool
   token in the rendered plan.

These are enforced at author time; (2) and (8) are machine-guarded and
(4)/(6)/(7) are checkable in the rendered anatomy. Treat a TC that violates any
of the eight as unfinished. Reference exemplars: SAN-01 (single-PE config),
TOPO-12 (multi-PE anycast IRB with tester + IRB config + integrated,
tool-agnostic, non-deterministic traffic).

## TP Checklist Categories (24 total)
Interface Types/Services, Sanity, CLI, Negative Testing, Various RIBs,
System Resources, DNOR, IPv4/IPv6, Counters, Logs/Traces, Traps, HA,
SNMP, System Events, Netconf, GNMI, Scale, Load + Stress,
Upgrade/Downgrade, Defaults, VRF Testing, Logs Rotation, Sanitizer,
Interoperability
