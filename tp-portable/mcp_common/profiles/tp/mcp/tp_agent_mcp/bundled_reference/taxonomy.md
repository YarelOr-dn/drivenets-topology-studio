# TP Category Taxonomy and Scenario Coverage (run #1 defaults)

Canonical category spine for `/TP` generation. Every epic adapts labels to its
feature, but these structural rules apply on **run #1** (no retrofit pass).

## Category spine (default order)

1. **Basic Functionality** — split by topology/use-case when paths differ (anycast
   IRB distributed vs centralized, no-IRB, simulate-BD, single-homed).
2. **Advanced Functionality** — multihoming, control-plane edge cases, oper-DB.
3. **CLI** — show/config/clear, rollback, routing-policy match extensions.
4. **Negative BGP & Malformation** — **auto-add** whenever the HLD/RFC source
   has a Negative / RFC-7606 / malformed-NLRI group (do NOT bury negatives in
   Advanced).
5. **HA** — process restart, NCC switchover, GR/NSF (not NSR/LLGR unless epic
   requires).
6. **Scale / Stress** — when epic has scale knobs or churn/soak requirements.
7. **Interoperability** — per named vendor + DN-to-DN baseline.
8. **Netconf / GNMI** — native YANG only; OpenConfig only when epic requires.
9. **Topology Scenarios** — use-cases, IRB lifecycle, destructive ops.

## Readable TC IDs (mandatory on run #1)

Pattern: `TC-<FEAT>-<CAT>-<slug-from-name>`

Examples:

- `TC-IGMP-SAN-basic-snoop-selective-forwarding-flood`
- `TC-IGMP-CP-rt6-version-flag-malformations-treat-as-withdraw`

Rules:

- `<FEAT>` = short feature token (IGMP, EVPN-SI, FSPEC, …).
- `<CAT>` = category abbreviation (SAN, CP, MH, CLI, HA, NC, INTEROP, …).
- `<slug>` = kebab-case from the human test name (no sequential TC-001).

## Per-category functional Prerequisites (SW-265228 style)

Every **category section** in the rendered markdown MUST open with a
**Prerequisites** block before the TC summary table:

```markdown
### Prerequisites (Advanced Functionality)

1. Build T5 multihoming topology: ...
2. Enable IGMP snooping/proxy on SVC-IGMP: ...
3. Verify baseline: `show bgp neighbors` — RR Established; multicast-db empty.
```

Requirements:

- Numbered **build + verify** steps (DNOS config blocks + one show each).
- Topology reference (T1–T8 or epic-specific) named explicitly.
- Shared across TCs in the category; TC-level prereq stays minimal deltas only.

## Procedure table — Action column (mandatory)

Rich TC anatomy uses a **node-scoped** procedure table:

| Step | Dev | Action | Command | Expected |
|------|-----|--------|---------|----------|

- **Dev** = acting node (`#1 PE-X`, `#2 PE-Y`, `all`, `datapath`) — never bare `-`.
- **Action** = short human verb phrase (stimulus vs verify split).
- **Command** = DNOS show/config or `-` for pure stimulus rows.

## Scenario inventory + coverage closure (Stage 1e — deterministic + agent)

Two-pass hybrid: deterministic backbone, bounded agent review.

**Pass A (deterministic, no LLM):**

1. Run `_tp_scenario_extract.py --epic <EPIC>` → `scenario_inventory.json`.
   Sources merged: HLD groups/flows/use-cases, `must_requirements.json`
   (RFC + epic clauses), first-class **user stories** (`US-<key>` from
   `jira_user_stories.json` + `source_story` provenance), Jira children.
2. It also emits `scenario_audit_<EPIC>.json` + a `[REVIEW]` list of HLD
   headings that yielded ZERO scenarios (potential blind spots).

**Pass B (agent, bounded + validated):**

3. Read the `[REVIEW]` blind-spot list; open each flagged HLD heading; add any
   genuinely-missed scenario to `scenario_inventory_agent.json` (required:
   `scenario_id`, `text`, `kind`; waived needs `waive_reason`). The extractor
   forces `source="agent"`, schema-validates (exit 3 on error), re-merges.
4. Use `scenario_inventory_overrides.json` for explicit waive/patch/remove.
5. Re-run Pass A until audit shows 0 blind spots and the gate closes.

**Closure:**

6. Each TC object carries `covers_scenarios: ["A1", "MUST-014", "US-SW-261643"]`.
7. Post-write: `_tp_scenario_coverage_gate.py` + parity check **8** must PASS.
8. Waive only with explicit `waive_reason` (TBD / out of scope).

HLD is optional — inventory falls back to Jira + `must_requirements.json` and
never false-fails for "no HLD".

## Negative category trigger

Create **Negative BGP & Malformation** when ANY source contains:

- HLD Group G (malformed NLRI / treat-as-withdraw)
- RFC 7606 negative handling requirements
- Checklist id **Negative Testing** selected for the epic

Negative TC names MUST include `Negative` in the title.
