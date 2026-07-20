---
name: generate-qa-test-plan
description: "Generate comprehensive test plans from Jira epics using a 4-stage pipeline: extract epic documentation, propose TCs for user review, generate test cases against requirements, and self-review for gap analysis. Use when the user asks to generate a test plan, create test cases, build QA coverage for a Jira epic key, or mentions test plan generation."
---

# Test Plan Generation Pipeline

> **Prerequisites:** DN MCP setup — Jira access. See `docs/ai/getting-started/mcp-setup.md`.

> **DriveNets `/TP` wrapper:** In Cursor lab workflows, use `/TP <EPIC>` as the
> epic-agnostic entry point. `/TP` embeds this 4-stage pipeline and adds:
> Jira-category presentation (not FlowSpec-specific), Interoperability per-vendor
> TCs, IPv4/IPv6 per-category AF classification, MUST/RFC/HLD ingestion,
> command-owned category grounding (NETCONF via `/NETCONF`, HA via `/HA` MCP,
> Scale via `/SCALE` MCP), and non-deterministic role/IP/MAC rendering.
> Artifacts: `~/SCALER/TEST/tp/<EPIC>/`. Rule: `~/.cursor/rules/tp-generator-command.mdc`.

## Goal

Generate a comprehensive, requirements-driven test plan from a Jira epic through a 4-stage pipeline of documentation extraction, TC proposal review, test case generation, and self-review.

## Workflow

Generated artifacts are stored under `test_plans/<EPIC_KEY>/` at the repository root. Before writing any file, verify the target directory exists (`mkdir -p`).

### File versioning

All artifacts in a single pipeline run share the same version number. Determine the version once at the start of Stage 1 and use it consistently across all stages.

1. **Determine the run version** — scan `test_plans/<EPIC_KEY>/` AND `test_plans/.cache/<EPIC_KEY>/` for all existing files (epic doc, test plan, approved TC list). Find the highest version number N across ALL artifacts in either directory. The current run's version is `N+1`. If no files exist, this is Run 1 (no suffix). If only unversioned base files exist, this is `_v2`. Do not special-case incomplete prior runs — always increment.
2. **Apply the version to all artifacts** — every file written in this run uses the same version suffix: `epic_documentation_<EPIC_KEY>[_vN].md`, `test_plan_<EPIC_KEY>[_vN].md`, `approved_tcs_<EPIC_KEY>[_vN].md`, `tp_checklist_cache.md` (shared across epics in `test_plans/.cache/`, no version, subject to 7-day TTL — reused from cache if fresh).
3. **Use the versioned filename throughout** — Stage 3 reads the epic documentation with the current run's version, Stage 4 reads/updates the test plan with the same version.

Example progression:
```
Run 1 → epic_documentation_SW-184289.md   + approved_tcs_SW-184289.md   + test_plan_SW-184289.md
Run 2 → epic_documentation_SW-184289_v2.md + approved_tcs_SW-184289_v2.md + test_plan_SW-184289_v2.md
Run 3 → epic_documentation_SW-184289_v3.md + approved_tcs_SW-184289_v3.md + test_plan_SW-184289_v3.md
```

Do not overthink versioning. Find highest N, use N+1, move on.

### Multi-epic input

The pipeline accepts a single epic key OR a comma-separated list of epic keys (e.g., `SW-184289, SW-157758`).

- **Single epic:** behaves exactly as before — directory is `test_plans/<EPIC_KEY>/`, filenames use `<EPIC_KEY>`.
- **Multiple epics:** the combined key is formed by joining the individual keys with `_` (e.g., `SW-184289_SW-157758`). All artifacts go under `test_plans/<COMBINED_KEY>/` and filenames use `<COMBINED_KEY>`.
- File versioning applies to combined filenames the same way as single-epic filenames.

Throughout this document, `<EPIC_KEY>` refers to either a single key or a combined key, depending on the input.

**Version namespace note:** The combined key (e.g., `SW-184289_SW-157758`) is a separate version namespace from the individual epic keys. A combined run starts at `_v1` (no suffix) even if `SW-184289` or `SW-157758` have been run independently before — the context of "two epics together" is treated as a distinct artifact line.

Reference files:
- `test-documentation/test_plan_requirements.md` — shared generation rules (path relative to this skill)
- TP Checklist Guide — Confluence page ID `3934912829` (fetched at runtime)

Pipeline overview:
```
Stage 1  Epic Key(s) ──> epic_documentation_<EPIC_KEY>.md
              ↓
Stage 2  epic_documentation + requirements + TP Checklist ──> TC proposal (user reviews)
                                                           ──> approved_tcs_<EPIC_KEY>.md
              ↓
Stage 3  epic_documentation + requirements + approved_tcs  ──> test_plan_<EPIC_KEY>.md
              ↓
Stage 4  test_plan + requirements + epic_documentation + approved_tcs ──> test_plan_<EPIC_KEY>.md (updated)
```

### Flags

- `--auto-tc-list` — skip the Stage 2 interactive pause and automatically approve all proposed TCs. The pipeline runs end-to-end without user intervention. Detect this flag anywhere in the user's invocation message (e.g., "generate test plan for SW-184289 --auto-tc-list").

### Stage 1: Extract epic documentation

Gather all relevant Jira information into a single LLM-optimized markdown document.

Input: One or more Epic Keys (e.g., `SW-184289` or `SW-184289, SW-157758`). If no Epic Key is provided, reject with: *Missing Epic ID. Provide a valid Epic ID to continue.*

**For each epic key in the input**, perform steps 1–3:

1. **Fetch the epic issue:**
   ```
   atlassian_jira_get_issue(issue_key=<EPIC_KEY>, fields="*all", comment_limit=50)
   ```
   Extract: summary, description, status, priority, components, fix versions, labels, parent, customer, comments, issue links, attachments list.

   If the epic issue fetch fails or returns no description, **stop the pipeline immediately** — there is no value in proceeding without the epic description.

   **Fetch images and attachments:** Call `atlassian_jira_get_issue_images` and `atlassian_jira_download_attachments` for the epic:
   ```
   atlassian_jira_get_issue_images(issue_key=<EPIC_KEY>)
   atlassian_jira_download_attachments(issue_key=<EPIC_KEY>)
   ```
   Include any diagrams, architecture images, or specification documents found in the attachments in the epic documentation. Reference images by filename and describe their content. For non-image attachments (e.g., PDFs, spreadsheets), extract and summarize relevant textual content. If either call fails or the tool is not available, continue without attachments — they are supplementary, but should always be attempted.

1b. **DNOS CLI Reference Lookup (RST):**

   After extracting the epic content from step 1, perform a targeted lookup of DNOS CLI RST documentation to ground all CLI commands in actual DNOS syntax. **Do NOT use the Jira `Component` field** for this — it is unreliable.

   1. **Extract keywords** — scan the epic `summary`, `description`, and any CLI configuration or show command sections for protocol/feature keywords. Match case-insensitively against the keys in the [DNOS CLI RST Reference — Component-to-Path Mapping](#dnos-cli-rst-reference--component-to-path-mapping) table at the end of this document.
   2. **Fallback for unmapped commands** — if the epic references CLI command paths not in the mapping (e.g., `system logging syslog`), extract the CLI command prefix tokens and glob-search `prod/dnos_monolith/dnos_cli/` for directories/files matching those path segments.
   3. **Glob for matching RST files** — using the mapped paths, glob for `.rst` files. Apply this selection priority:
      1. RST files whose command path appears literally in the epic description (highest priority)
      2. The parent overview RST in the matched directory (e.g., `Protocols/bgp/bgp.rst`)
      3. Show command RSTs matching the keyword (e.g., `Show Commands/show bgp.rst`)
      4. RST files for specific sub-commands mentioned in the epic
   4. **Cap at 5–10 files.** If more than 10 files match, keep only those whose commands are explicitly mentioned in the epic plus the parent overview. Drop everything else.
   5. **Read each selected RST file** and extract: command syntax (from `**Command syntax:**`), parameter table (names, descriptions, ranges, defaults), command mode, hierarchy, and removing configuration syntax.
   6. **Compile into the `### DNOS CLI Reference (from RST)` section** of the epic documentation (see template below).

   If no keywords match and the fallback glob finds nothing, skip this step — the section is omitted and the pipeline proceeds without RST grounding.

2. **Fetch User Stories** (non-rejected children):
   ```
   JQL: parent = <EPIC_KEY> AND issuetype = "User story" AND status not in (Reject, Rejected)
   ```
   If the query returns zero results, that is expected — some epics have no User Stories. Do NOT attempt fallback queries, alternative JQL, or broader searches. Accept zero User Stories and proceed to step 3.

   For each user story, fetch: summary, description, status, priority, comments. Also call `atlassian_jira_get_issue_images` and `atlassian_jira_download_attachments` for each user story — sequence diagrams, topology images, and specification attachments are often on the US rather than the epic. If either call fails or the tool is not available, continue without that US's attachments.

3. **Fetch linked epics:**
   ```
   JQL: issue in linkedIssues(<EPIC_KEY>) AND issuetype = Epic
   ```
   For each, fetch: summary, description, status, link type. Also fetch any referenced issues from the epic description (parity epics, scale requirement tickets).

3b. **Fetch Base Test Plan (optional):** If the user provides a reference epic key for baseline tests (e.g., "use SW-XXXXX as base test plan", "get tests from SW-XXXXX as baseline", "use tests from epic SW-XXXXX as inspiration"), capture it as `<BASE_EPIC_KEY>` and perform a two-level fetch:

   First, fetch the base epic summary:
   ```
   atlassian_jira_get_issue(issue_key=<BASE_EPIC_KEY>, fields="summary")
   ```

   Then fetch all non-rejected Test Categories under the base epic:
   ```
   JQL: parent = <BASE_EPIC_KEY> AND issuetype = "Test Category" AND status not in (Reject, Rejected)
   ```

   For each Test Category returned, fetch its non-rejected Testing Tasks:
   ```
   JQL: parent = <TEST_CATEGORY_KEY> AND issuetype = "Testing Task" AND status not in (Reject, Rejected)
   ```

   For each Testing Task, extract: `summary` (test name), `key`, `status`.

   Compile the results into a `### Base Test Plan` section in the epic documentation (placed after `### Key Discussion Points from Comments` and before `### RFC References`):

   ```markdown
   ### Base Test Plan

   **Source Epic:** <BASE_EPIC_KEY> — <BASE_EPIC_SUMMARY>

   | Category | TC Key | Test Name | Status |
   |---|---|---|---|
   | <Test Category summary> | SW-XXXXX | <Testing Task summary> | <status> |
   | ... | ... | ... | ... |
   ```

   This step is skipped entirely if the user does not provide a base epic key.

4. **Compile the documentation** into `test_plans/<EPIC_KEY>/epic_documentation_<EPIC_KEY>.md`. Each input epic gets its own `## Epic:` block with all sub-sections. Use this structure:

   ```markdown
   # Epic Documentation for Test Plan Generation

   **Generated:** <TIMESTAMP>
   **Total Epics:** <N>
   **Status:** Verified and LLM-optimized

   ---

   ## Epic: <SUMMARY>

   **Key:** <EPIC_KEY>
   **Status:** <STATUS>
   **Priority:** <PRIORITY>
   **Component:** <COMPONENT>
   **Fix Versions:** <VERSIONS>
   **Labels:** <LABELS>
   **Parent Initiative:** <PARENT_KEY> - <PARENT_SUMMARY>
   **Customer:** <CUSTOMER>

   ### Description
   <EPIC_DESCRIPTION — cleaned of Jira markup, converted to markdown>

   ### Functional Overview
   <Extracted from description — concepts, architecture, behavior>

   ### Requirements
   #### Functional Requirements
   <Numbered list of MUST/SHOULD requirements>

   #### Scale Requirements
   <If referenced in epic or linked tickets>

   #### HA Requirements
   <If specified>

   ### CLI Configuration
   <CLI hierarchy from epic description>

   ### Show Commands
   <Show command examples from epic description>

   ### DNOS CLI Reference (from RST)

   **Matched keywords:** <comma-separated list of matched keywords>
   **RST files read:** <count>

   #### Configure Commands

   **`<command path>`** (from `dnos_cli/<relative RST path>`)
   - Syntax: `<command syntax from RST>`
   - Mode: <config | operational>
   - Hierarchy: <hierarchy paths>
   - Parameters: <parameter name — description, range, default>
   - Removing: `<no-form syntax>`

   #### Show Commands

   **`<show command>`** (from `dnos_cli/Show Commands/<filename>.rst`)
   - Syntax: `<full syntax with optional args>`
   - Mode: operational
   - Output fields: <key fields from parameter table>

   <If no RST files were found, omit this entire section>

   ### Related Epics and Links
   | Key | Summary | Type | Status |
   |---|---|---|---|

   ### User Stories
   #### US-001 - <SUMMARY>
   **Key:** <KEY>
   **Status:** <STATUS>
   <DESCRIPTION>

   ---

   ### Testing Guidance
   <Extracted from epic description, comments, and linked docs>

   ### Key Discussion Points from Comments
   <Numbered list of significant decisions from comments>

   ### RFC References
   <If applicable>
   ```

   **When multiple epics are provided**, repeat the `## Epic:` block for each epic, then append a final section:

   ```markdown
   ---

   ## Cross-Epic Requirements

   ### Overlapping Features
   <Features or components that appear in more than one input epic>

   ### Shared Components
   <Components, services, or subsystems touched by multiple epics>

   ### Interaction Points
   <Scenarios where behavior from one epic affects or depends on the other epic(s)>

   ### Contradictions or Gaps
   <Any conflicting requirements or gaps between the epics — label as "Assumption" if resolved by inference>
   ```

5. **Exclusions** — do NOT include: Bug items, Test Category items, Testing Task items, dev implementation tasks, or QA effort/planning items.

   **Exception:** When the user provides a reference epic for a Base Test Plan (step 3b), Test Category and Testing Task items from that reference epic ARE fetched and included in the `### Base Test Plan` section. The exclusion applies only to the *target* epic's own Test Category / Testing Task items.

**Gate:** `test_plans/<EPIC_KEY>/epic_documentation_<EPIC_KEY>.md` exists and passes validation: every User Story from **every** input epic appears in the document, each epic's description is fully captured (no truncation), linked epic descriptions are included, comments with technical decisions are captured, no QA sub-task items are included (except the Base Test Plan section if a reference epic was provided), (for multi-epic input) the Cross-Epic Requirements section is present, and if RST files were found and read in step 1b, the `### DNOS CLI Reference (from RST)` section is present and non-empty.

### Stage 2: TC Proposal (interactive)

Analyze the epic documentation against the requirements and present a proposed TC list for user review before generating full test cases.

Input:
- `test_plans/<EPIC_KEY>/epic_documentation_<EPIC_KEY>.md`
- **Read now:** `.ai/skills/qa/generate-qa-test-plan/test-documentation/test_plan_requirements.md`
- **TP Checklist (cache-first):** Check whether `test_plans/.cache/tp_checklist_cache.md` already exists. If it does, read the `<!-- Fetched: <TIMESTAMP> -->` header line and compare the timestamp to the current date. **If the file exists and was fetched within the last 7 days, read from cache — do NOT fetch from Confluence.** Only fetch from Confluence (page ID `3934912829`) when the file does not exist or the cached timestamp is older than 7 days. When fetching, create the directory (`mkdir -p`) if needed, write the content with a `<!-- Fetched: <TIMESTAMP> -->` header line, then read from the newly written file.

1. **Analyze the epic** against the requirements and checklist. Identify all test cases that should be generated based on:
   - User Story coverage (at least one TC per US)
   - Standard categories — evaluate each category's trigger condition against the epic; propose TCs only for applicable categories
   - HA decomposition, protocol-specific mechanics, negative testing, etc.
   - **Base Test Plan coverage** (if present in epic documentation): review every entry in the Base Test Plan table. For each test that represents a scenario relevant to the *new* epic's requirements, propose a corresponding TC in the TC list. The base tests serve as *inspiration*, not as a 1:1 copy — adapt test names and scopes to the new epic's feature set. Flag any base tests that are clearly inapplicable to the new epic (different protocol, irrelevant feature) and exclude them.

2. **Present the TC proposal** as a compact list grouped by category. Keep it minimal — no explanations, no filler text. Format:

   ```
   **Sanity**
   - TC-001: SW-212169 — <short title>
   - TC-002: SW-212173 — <short title>

   **HA**
   - TC-003: <short title>
   - TC-004: <short title>

   **Negative**
   - TC-005: <short title>
   ```

   Rules for the proposal format:
   - Category as bold text, no heading markup
   - Each test as a bullet: `TC-NNN:` prefix, coverage reference + short title (under 10 words)
   - Use the real Jira key of the User Story (e.g., `SW-212169`), not the generic `US-NNN` alias from the epic documentation
   - No checkboxes, no descriptions between categories
   - End with a separator and action prompt:
     ```
     ---
     **ACTION REQUIRED:** Pipeline is paused. Please review the test list above and approve to proceed. You can remove items, add new ones, or reply "approved" to continue.
     ```

3. **If `--auto-tc-list` is set:** skip the action prompt, auto-approve all proposed TCs, and proceed directly to Stage 3. Still present the TC list (for the record) but replace the action prompt with: `**Auto-approved — proceeding to generation.**`

4. **Otherwise, wait for user response.** The user can:
   - Remove items (strike through, delete, or say "remove X")
   - Ask for additions — re-present the **full** updated list with new items appended
   - Approve to proceed

   The loop repeats until the user explicitly approves.

5. **Only items in the final approved list proceed to Stage 3.** Removed items are skipped entirely.

6. **Persist the approved list to disk.** Write the final approved TC list to `test_plans/.cache/<EPIC_KEY>/approved_tcs_<EPIC_KEY>[_vN].md`. Create the directory (`mkdir -p`) if it does not exist. Use the same compact category-grouped format presented to the user, preceded by a metadata header:

   ```markdown
   # Approved TC List
   **Epic:** <EPIC_KEY>
   **Approved:** <TIMESTAMP>
   **Run version:** [_vN or "1 (initial)"]

   **Sanity**
   - TC-001: SW-212169 — <short title>
   ...
   ```

   This file is the **single source of truth** for which TCs were approved. Stages 3 and 4 read it from disk — they do NOT rely on conversation context for the approved list.

**Gate:** The user has explicitly approved the final TC list (or `--auto-tc-list` was set) AND `test_plans/.cache/<EPIC_KEY>/approved_tcs_<EPIC_KEY>[_vN].md` exists on disk.

### Stage 3: Generate test plan

Generate a comprehensive test plan from the epic documentation, following the test plan requirements and constrained to the user-approved TC list from Stage 2.

Input:
- `test_plans/<EPIC_KEY>/epic_documentation_<EPIC_KEY>.md`
- **Read now:** `.ai/skills/qa/generate-qa-test-plan/test-documentation/test_plan_requirements.md`
- **Read from cache:** `test_plans/.cache/tp_checklist_cache.md` (written by Stage 2). Do NOT re-fetch from Confluence.
- **Read from disk:** `test_plans/.cache/<EPIC_KEY>/approved_tcs_<EPIC_KEY>[_vN].md` (written by Stage 2). This is the single source of truth for the approved TC list — do NOT rely on conversation context.

**Scope constraint:** Generate TCs ONLY for items in the approved list file. Do NOT generate TCs for items the user removed. If the user added new items during the Stage 2 review loop, they are already captured in the persisted file.

1. **Apply all requirements from `test_plan_requirements.md`** to the approved items:
   1. User Story coverage first — at least one TC per User Story from **each** input epic.
   2. Standard categories — evaluate each category's trigger condition against the epic; generate TCs only for applicable categories.
   3. HA decomposition — one TC per distinct process, container, restart type.
   4. Variants are NOT coverage — promote significant scenarios to standalone TCs.
   5. Protocol-specific mechanics — ECMP, encapsulation modes, SID types, heterogeneous configs, summarization, MT vs. multi-instance.
   6. Feature dependency tests — dynamic enable/disable, shared resource modification, overlay service interaction.
   7. Concurrent event tests — simultaneous multi-link failures, concurrent HA + topology events.
   8. Traffic loss threshold tests — if thresholds are specified in the epic.
   9. Customer-specific topology — if a customer is referenced in the epic.
   10. Timer tests — boundary values, dynamic change while active (standalone TC).
   11. Negative testing — traditional + inverse negative.
   12. Combined persistence — configure, reboot, upgrade, switchover sequence.
   13. **Cross-epic interaction** (multi-epic input only) — at least one TC per interaction point identified in the Cross-Epic Requirements section. Tag these TCs as `Coverage for Cross-Epic Interaction`.

2. **Write the test plan incrementally** to prevent data loss. Never write more than 300 lines in a single operation. Follow this batch sequence:
   - **Batch 1:** Header + `## Test Summary` (category-grouped TOC with anchor links) + `## Test Cases` heading.
   - **Batch 2-N:** Append one category at a time (bold category label + its TCs + `---` separator).
   - **Final:** After all TCs are written, re-read the file and verify every anchor link in the Test Summary resolves to an actual TC header.

   Each batch: read end of file to find insertion point, append, verify file is valid.

3. **Test plan structure:**
   ```
   # Header + metadata
   ## Test Summary

   **Sanity** (3 TCs)
   | TC | Test Name | Link |
   |---|---|---|
   | TC-001 | <short name> | [TC-001](#tc-001-coverage-for-) |
   | TC-002 | <short name> | [TC-002](#tc-002-coverage-for-) |
   | TC-003 | <short name> | [TC-003](#tc-003-coverage-for-) |

   **HA** (2 TCs)
   | TC | Test Name | Link |
   |---|---|---|
   | TC-004 | <short name> | [TC-004](#tc-004-coverage-for-) |
   | TC-005 | <short name> | [TC-005](#tc-005-coverage-for-) |

   **Negative** (1 TC)
   | TC | Test Name | Link |
   |---|---|---|
   | TC-006 | <short name> | [TC-006](#tc-006-coverage-for-) |

   ---

   ## Test Cases

   **Sanity**

   ### **TC-001: ...**
   ### **TC-002: ...**

   ---

   **HA**

   ### **TC-004: ...**
   ### **TC-005: ...**

   ---

   **Negative**

   ### **TC-006: ...**
   ```

   **Test Summary rules:**
   - One table per category, preceded by the category name in bold and TC count in parentheses.
   - Each row: TC number, the Test Name from field 1 of the TC (shortened to fit), and a markdown anchor link.
   - Anchor format: lowercase the full TC header, replace spaces with `-`, strip `*` and `:`. E.g., `### **TC-001: Coverage for SW-212169 — Basic config**` → `#tc-001-coverage-for-sw-212169--basic-config`.
   - Categories appear in the same order as in the `## Test Cases` section below.

   Group TCs by the same categories used in the Stage 2 proposal. Use bold text (not heading markup) for category labels and `---` separators between categories. TC headers stay at `###` level. **Multi-epic merging:** when multiple epics contribute TCs to the same category, emit a single combined category block (e.g., one **Sanity** block), not separate per-epic blocks. TCs from all epics are interleaved within the category in TC-NNN order. The coverage reference in each TC header identifies which epic the TC belongs to (e.g., `Coverage for SW-184289/SW-212169`).

4. **TC template** (follow exactly):
   ```
   ### **TC-NNN: Coverage for <US-ID or Category>**
   1. **Test Name:**
   2. **Test Description:**
   3. **Preconditions:** (required setup, topology, services, or prior state before step 1)
   4. **Test Steps:** (numbered, max 15)
   5. **Pass Criteria:** (numbered, 1:1 with steps)
   6. **Variants:** (bulleted, trivial substitutions only)
   7. **Automation Reference:**
   ```

   **TC numbering:** Every TC MUST use the `TC-NNN` format — a zero-padded three-digit number (e.g., `TC-001`, `TC-012`, `TC-100`). This exact format is required by the `/push-tests-to-jira` script for parsing and Jira issue creation. Do NOT use un-padded numbers (`TC-1`), letter suffixes (`TC-001A`), or any other numbering scheme. Only plain `TC-NNN` is valid.

   For multi-epic input, prefix the Jira key with its epic key (e.g., `Coverage for SW-184289/SW-212169`). Use `Coverage for Cross-Epic Interaction` for TCs that cover interaction points between epics.

5. **Test Flow Chaining** — when 3+ TCs in the same category share 3+ identical initial setup steps, use flow chaining to eliminate redundant setup:
   - The first TC in the chain has the full setup in its Test Steps.
   - Subsequent TCs reference the prior TC's end-state in the **Preconditions** field using the format: `Continues from TC-NNN end-state: <brief description of the assumed system state>.`
   - The continued TC skips the shared setup steps and begins directly with its unique action.
   - **Within-category only:** A TC may only continue from a TC in the same category. Cross-category chaining is not allowed.
   - **Self-contained description:** The Preconditions field must describe the assumed state, not just reference TC-NNN. A reader must understand the precondition without looking up the referenced TC.
   - **Max chain depth: 3.** A chain of A → B → C is allowed. A → B → C → D is not. This prevents cascading failures from making large portions of the test plan unrunnable.

**Gate:** `test_plans/<EPIC_KEY>/test_plan_<EPIC_KEY>.md` exists and passes validation: every approved TC from Stage 2 has been generated, all negative TCs have "Negative" in the Test Name, all TCs have 15 or fewer steps, Pass Criteria count matches Test Steps count (1:1), no scenario that changes topology/trigger/process/data-plane is listed as a variant, and (for multi-epic input) every approved cross-epic interaction point has at least one TC.

### Stage 4: Self-review against requirements

Review the generated test plan for quality issues **within the scope approved by the user in Stage 2**. The user-approved TC list from Stage 2 is the source of truth for what should exist. Do NOT add TCs for items the user excluded.

Input:
- `test_plans/<EPIC_KEY>/test_plan_<EPIC_KEY>.md` (from Stage 3)
- **Re-read now:** `.ai/skills/qa/generate-qa-test-plan/test-documentation/test_plan_requirements.md` (full document, top to bottom)
- `test_plans/<EPIC_KEY>/epic_documentation_<EPIC_KEY>.md`
- **Read from cache:** `test_plans/.cache/tp_checklist_cache.md` (written by Stage 2). Do NOT re-fetch from Confluence.
- **Read from disk:** `test_plans/.cache/<EPIC_KEY>/approved_tcs_<EPIC_KEY>[_vN].md` (written by Stage 2). This is the single source of truth for the approved TC list.

**Scope rule:** The persisted approved TC list is authoritative. If a User Story, category, or scenario is not in the approved list file, do NOT flag it as a gap and do NOT generate a TC for it. Only audit and fix issues within the approved scope. **Stage 4 must not add, remove, merge, renumber, or promote TCs. The approved TC list and the final test plan must map 1:1 — TC-NNN in the approved list is TC-NNN in the test plan.**

1. **Audit within approved scope** — for each generated TC, evaluate quality:

   | Quality Check | Status | Finding |
   |---|---|---|
   | TC template compliance | Pass / Fail | Steps at most 15? 1:1 pass criteria? |
   | Variants are NOT coverage | Pass / Fail | Which variants should be standalone TCs? |
   | Negative TCs have "Negative" in name | Pass / Fail | Which TCs are missing the label? |
   | Test steps are specific and actionable | Pass / Fail | Which TCs have vague steps? |
   | Pass criteria are measurable | Pass / Fail | Which criteria are non-verifiable? |

2. **Cross-reference epic documentation** (within approved scope only):
   1. Every approved TC accurately reflects the epic's requirements.
   2. Scale numbers (if specified and approved) validated by exact-number TCs.
   3. CLI commands referenced in approved TCs use correct syntax.
   4. Testing guidance from epic/comments reflected in approved TCs.
   5. If a Base Test Plan section exists, verify that every applicable base test has a corresponding TC or is explicitly excluded with justification.

3. **Compile internal gap list** (not written to file), organized by:
   1. Variants that should be standalone TCs — flag these for the user; do NOT promote them in this run.
   2. Weak TCs — existing TCs needing additional steps or pass criteria.
   3. Template violations — TCs exceeding 15 steps, mismatched pass criteria, missing "Negative" label.

4. **Update the test plan in place** — edit directly, never rewrite from scratch. Apply in batches of 3-5 TCs:
   1. Fix template violations in existing TCs.
   2. Strengthen weak TCs with additional steps or pass criteria.

5. **Header sanity check** — verify that every TC header in the test plan exactly matches the format `### **TC-NNN: <title>**`. Specifically:
   1. Every TC header matches `### **TC-NNN: <title>**` exactly.
   2. NNN is exactly three digits with NO letter suffix (e.g., `TC-001` is valid; `TC-1`, `TC-01`, `TC-001A`, `TC-100B` are all invalid — fail the gate).
   3. The title contains no `*` characters.
   4. The line ends with `**`.

   If any header fails these checks, fix it before declaring the gate passed. The push-tests-to-jira script requires the plain `TC-NNN` format with no suffix.

**Gate:** All quality issues from the self-review are fixed. The updated test plan passes the full validation checklist in the Quality bar below (evaluated only against the user-approved scope from Stage 2).

## Output format

| Artifact | Path | Created By |
|---|---|---|
| Epic documentation | `test_plans/<EPIC_KEY>/epic_documentation_<EPIC_KEY>[_vN].md` | Stage 1 |
| Approved TC list | `test_plans/.cache/<EPIC_KEY>/approved_tcs_<EPIC_KEY>[_vN].md` | Stage 2 |
| Test plan | `test_plans/<EPIC_KEY>/test_plan_<EPIC_KEY>[_vN].md` | Stage 3, updated by Stage 4 |

Epic documentation and test plans live in `test_plans/<EPIC_KEY>/`. The approved TC list lives in `test_plans/.cache/<EPIC_KEY>/` to keep pipeline intermediates separate from deliverables. When multiple epics are provided, `<EPIC_KEY>` is the combined key (e.g., `SW-184289_SW-157758`). The `[_vN]` suffix is omitted on the first run and incremented on subsequent runs (see [File versioning](#file-versioning)).

## Quality bar (self-check)

All checks are evaluated **only against the user-approved list from Stage 2**.

[ ] Every item in the Stage 2 approved list has a corresponding generated TC.
[ ] All negative TCs have "Negative" in the Test Name.
[ ] All TCs have 15 or fewer steps.
[ ] Pass Criteria count matches Test Steps count (1:1) for every TC.
[ ] No scenario that changes topology/trigger/process/data-plane is listed as a variant.
[ ] HA tests (if approved) are decomposed per process/container/restart type (not lumped together).
[ ] Timer tests (if approved) include boundary values AND dynamic change while active.
[ ] Negative testing (if approved) includes both traditional and inverse negative scenarios.
[ ] Scale requirements (if approved) have TCs with exact scale numbers.
[ ] TC numbering is sequential with no gaps.
[ ] Approved TC list and final test plan map 1:1 — no TCs added, removed, merged, or renumbered in Stage 4.
[ ] Base Test Plan coverage (if provided) — every applicable base test has a corresponding TC or documented exclusion.

---

## Quick-Start Prompt

```
Build an epic documentation for <EPIC_KEY>, gather all epic
description and epic User Stories items. Then propose a TC list for
my review. After I approve, generate a test plan using
test_plan_requirements.md. Then self-review the generated test plan
against the full test_plan_requirements.md and the epic
documentation — update existing TCs and add missing scenarios
directly in the test plan file.
```

---

## File Reference

| File | Purpose | Updated By |
|---|---|---|
| `.ai/skills/qa/generate-qa-test-plan/test-documentation/test_plan_requirements.md` | Shared generation rules | Manual |
| TP Checklist Guide (Confluence page ID `3934912829`) | 85-category checklist — fetched at runtime | Confluence |
| `.ai/skills/qa/generate-qa-test-plan/SKILL.md` | This document — pipeline definition | Manual |
| `test_plans/<EPIC_KEY>/epic_documentation_<EPIC_KEY>[_vN].md` | Epic input — versioned per run | Stage 1 |
| `test_plans/.cache/<EPIC_KEY>/approved_tcs_<EPIC_KEY>[_vN].md` | Persisted approved TC list — versioned per run | Stage 2 |
| `test_plans/<EPIC_KEY>/test_plan_<EPIC_KEY>[_vN].md` | Generated test plan — versioned per run, updated in place by Stage 4 | Stages 3, 4 |

---

## DNOS CLI RST Reference — Component-to-Path Mapping

This mapping drives the Step 1b RST lookup. Keys are matched case-insensitively against the epic summary, description, CLI sections, and User Story content. **Do NOT use the Jira `Component` field** — it is unreliable.

RST root: `prod/dnos_monolith/dnos_cli/`

| Keyword | Configure RST Path | Show RST Glob |
|---|---|---|
| bgp | `Protocols/bgp/` | `Show Commands/show bgp*.rst` |
| bgp_graceful-shutdown | `Protocols/bgp_graceful-shutdown/` | — |
| ospf | `Protocols/ospf/` | `Show Commands/show ospf*.rst` |
| ospfv3 | `Protocols/ospfv3/` | `Show Commands/show ospfv3*.rst` |
| isis | `Protocols/isis/` | `Show Commands/show isis*.rst` |
| ldp | `Protocols/ldp/` | `Show Commands/show ldp*.rst` |
| mpls | `Protocols/mpls/` | `Show Commands/show mpls*.rst` |
| rsvp | `Protocols/rsvp/` | `Show Commands/show rsvp*.rst` |
| bfd | `Protocols/bfd/`, `BFD/` | `Show Commands/show bfd*.rst` |
| lacp | `Protocols/lacp/` | `Show Commands/show lacp*.rst` |
| lldp | `Protocols/lldp/` | `Show Commands/show lldp*.rst` |
| pim | `Protocols/pim/` | `Show Commands/show pim*.rst` |
| msdp | `Protocols/msdp/` | `Show Commands/show msdp*.rst` |
| igmp | `Protocols/igmp/` | `Show Commands/show igmp*.rst` |
| dhcp | `Protocols/dhcp/` | `Show Commands/show dhcp*.rst` |
| vrrp | `Protocols/vrrp/` | `Show Commands/show vrrp*.rst` |
| segment-routing | `Protocols/segment-routing/`, `Segment-routing/` | `Show Commands/show segment-routing*.rst` |
| static | `Protocols/static/` | `Show Commands/show static*.rst` |
| evpn | `Network-services/evpn/` | `Show Commands/show evpn*.rst` |
| evpn-vpws | `Network-services/evpn-vpws/` | `Show Commands/show evpn-vpws*.rst` |
| bridge-domain | `Network-services/bridge-domain/` | `Show Commands/show bridge-domain*.rst` |
| vpws | `Network-services/vpws/` | `Show Commands/show vpws*.rst` |
| vrf | `Network-services/vrf/` | `Show Commands/show vrf*.rst` |
| multihoming | `Network-services/multihoming/` | — |
| interfaces | `Interfaces/` | `Show Commands/show interfaces*.rst` |
| system | `System/` | `Show Commands/show system*.rst` |
| qos | `QoS/` | `Show Commands/show qos*.rst` |
| routing-policy | `Routing-policy/` | `Show Commands/show routing-policy*.rst` |
| routing-options | `Routing-options/` | `Show Commands/show routing-options*.rst` |
| access-list | `Access-lists/`, `access-list/` | `Show Commands/show access-list*.rst` |
| forwarding-options | `forwarding-options/` | `Show Commands/show forwarding-options*.rst` |
| services | `Services/` | `Show Commands/show services*.rst` |
| high-availability | `High-availability/` | `Show Commands/show high-availability*.rst` |
| tracking-policy | `tracking-policy/` | `Show Commands/show tracking-policy*.rst` |
