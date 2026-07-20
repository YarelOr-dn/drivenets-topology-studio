# Merged /TP Workflow

This is the canonical order for the merged `/TP` command.

## Workflow

1. **Parse request**
   - Primary epic: required.
   - Linked epics: optional, via `--linked` or GUI request metadata.
   - Categories: optional filter; `All` remains available.

2. **Load lab profile**
   - Use `python3 ~/.cursor/tools/lab_profile.py show --profile active` for
     `/TEST`-bound plans.
   - Do not write config or emit traffic during TP generation.

3. **Load local context**
   - `/TP` references: checklist, QA guidelines, topology reference, DNOS syntax,
     examples, manifest schema, TP-to-TEST mapping.
   - Costake rubric: `~/.cursor/skills/generate-qa-test-plan/test-documentation/test_plan_requirements.md`.
   - Feature skills, such as `~/.cursor/skills/evpn-si-irb-mobility/`.

4. **Collect source documents**
   - Fetch epics, non-rejected User Stories, linked epics, parent epics, SIT/E2E
     stories, comments, key Confluence pages, and RFC references.
   - **Enabler auto-discovery (always-on, no `--linked` needed):** classify linked
     Epics as ENABLERS (summary contains `Enabler`; dependency link type; or shared
     feature stem with an `Enabler`/`PIM`/`Datapath`/`Control-Plane`/`FIB` suffix),
     then RECURSE into each — fetch its description + non-rejected **User story**
     children ONLY (`parent in (<ENABLER_KEYS>) AND issuetype = "User story"`, page
     past 100; exclude Story/Task/Test-Category noise) and mine their bodies for
     CLI knobs, MUST/SHALL, mutual-exclusions, ranges, scale/datapath behavior.
     Merge with provenance `enabler_epic:`/`source_story:` and persist
     `enabler_sweep.json` (empty `enablers: []` if none). Gate:
     `_tp_source_completeness.py`. Rationale: the primary epic often delegates the
     bulk of CLI/datapath/PIM behavior to enabler epics (e.g. SW-211037 → SW-241377
     PIM = 43 + SW-241487 Datapath = 18 = 61 user stories) that a primary-only
     sweep drops.
   - Persist one joint `epic_documentation_<PRIMARY>_<LINKED>.md`.

5. **Normalize into SQLite**
   - Seed core rules and commands.
   - Ingest TP artifacts.
   - Export compact JSON and Markdown views.

6. **Generate normalized TC objects**
   - TCs are structured objects first.
   - Do not render markdown until dedup, packing, and Stage 3 review are complete.

7. **Dedup and pack**
   - Collapse true duplicates.
   - Allow one TC to cover multiple categories only when each category remains
     explicitly traceable and has pass criteria.

8. **Self-review**
   - Re-read Costake rubric, TP checklist, feature skill, source docs, and packed TC list.
   - Add missing TCs, promote invalid variants, and fix pass-criteria gaps.

9. **Render**
   - Markdown TP.
   - Jira-wiki test bodies.
   - Manifest JSON.
   - Full result JSON.
   - Quality audit.

10. **Review gate**
    - Stop for user review.
    - Do not push to Jira and do not invoke `/TEST create` without explicit approval.

## Dual-Epic Rule

For dual epics, the primary epic owns the output folder. Linked epics remain
first-class coverage targets in `manifest.json` and `full_result.json`.

Example:

```text
primary_epic: SW-228552
linked_epics: [SW-241473]
output_dir: ~/SCALER/TEST/tp/SW-228552/
```

Every TC must expose whether it covers routing, datapath, or both.
