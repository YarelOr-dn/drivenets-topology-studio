# Test Case Format Template for TP Generation

This template aligns with the test-generation prompts in `qa_automation/ai_test_plan/openai_v3/source/test_plan_ui.py` (task_prompt around lines 3009--3037) and `USER_STORY_TEST_ADDITIONAL_INSTRUCTIONS` in `qa_automation/ai_test_plan/openai_v3/source/utils/globals.py`.

**Run #1 defaults (2026):** readable slug IDs (`TC-<FEAT>-<CAT>-<slug>`), per-category
**Prerequisites** blocks (SW-265228 style), rich anatomy with **Action** column, and
auto **Negative BGP & Malformation** category when HLD/RFC negatives exist — see
`taxonomy.md`.

---

## Format C: Rich Markdown (preferred for new `/TP` epics)

Used by hand-authored generators (`_gen_<EPIC>.py`) and parity gate check 7.

### TC ID and heading

```markdown
#### TC-IGMP-CP-sending-rt-6-smet-first-interest-duplicate - Sending RT-6 SMET on first interest

_Test ID: `TC-IGMP-CP-sending-rt-6-smet-first-interest-duplicate`_
```

### Category-level Prerequisites (before the category summary table)

```markdown
### Prerequisites (Control Plane)

1. Build T1 single-homed 2-PE topology (PE-X + PE-Y + RR-X).
2. Enable IGMP snooping/proxy on `SVC-IGMP`.
3. Verify: `show bgp neighbors` — l2vpn-evpn session Established.
```

### Rich anatomy sections (per TC)

- **What this tests** — one crisp observable outcome sentence.
- **Purpose** — one sentence why/risk.
- **Devices under test** — numbered role table.
- **Traffic actors** / **Topology diagram** / **Topology notes** (when traffic moves).
- **Procedure** — table with **Action** column:

```markdown
| Step | Dev | Action | Command | Expected |
|------|-----|--------|---------|----------|
| 1 | #1 PE-X | Stimulus: IGMPv2 join for G on AC-IF-X | - | (verified next) |
| 2 | #1 PE-X | Verify RT-6 originated | `show bgp l2vpn evpn route-type 6` | SMET for G present |
```

- **Pass criteria** — bullet list, gradeable.

### Structured JSON fields (full_result.json)

Each TC object MUST include:

- `covers_scenarios[]` — HLD group ids (A1, B5, …), MUST ids, operational-flow ids.
- `covers_rubric_rules[]`, `covers_user_stories[]`, `covers_epics[]`.
- `rich: true`, node-scoped `steps[]` with `dev`, `action`, `command`, `expected`.

---

## Format A: Table Format (for CLI, HA, Scale, Advanced tests)

Use **Jira / Confluence wiki markup** (not Markdown tables in Jira).

### Table header (exact)

```text
||*Step*||*Action*||*Command*||*Expected Result*||
```

### Row pattern

Each data row uses single pipes:

```text
|1|Short action label|{{show bgp summary \| no-more}}|Expected output described|
|2|...|{{...}}|...|
```

- **Step** column: numbered integers (`1`, `2`, `3`, ...).
- **Command** column: wrap DNOS commands in **double braces** `{{...}}` (Jira inline monospace). Escape literal pipe inside the command as needed for Jira (often written as `\|` inside the braces when the command itself contains `|`).

### Document structure (wiki markup)

Suggested skeleton matching the mandatory structure in `globals.py`:

```text
h1. +*_Test Steps:_*+

* NOTE: all ipv4 tests should be tested with IPv6 as well (when applicable)

h2. Prerequisites (All Tests)

h3. Topology Requirements
* DUT connected to external peer(s)
* IXIA traffic generator connected (if traffic tests)
* Relevant protocol sessions pre-established

h3. DUT Configuration Requirements
* Feature-specific config from EPIC/User Stories, e.g. {{protocols bgp 65000}}

----

h2. Test 1: [Descriptive Test Name]

*Objective:* [One sentence describing what this test validates.]

||*Step*||*Action*||*Command*||*Expected Result*||
|1|Configure feature|{{config example from EPIC}}|Config accepted|
|2|Verify state|{{show example \| no-more}}|Expected output|

----

h2. Test 2: [Another Test Name]

*Objective:* [...]

||*Step*||*Action*||*Command*||*Expected Result*||
|1|...|{{...}}|...|
```

### Separators and objectives

- **Between tests:** a horizontal rule line `----` on its own line (as in `globals.py`).
- **Per test:** include an **`*Objective:*`** line (bold label in Jira) before that test’s table.
- **Multiple tests:** label sections `h2. Test 1: ...`, `h2. Test 2: ...`, etc.

### Commands in wiki

- Use **`{{double braces}}`** for commands in Jira; do **not** use Markdown backticks for Jira-published content.
- Config snippets in cells can use the same `{{...}}` form for short lines; multi-line config blocks may use `{noformat}...{noformat}` per your Jira comment standards (see project rules).

---

## Format B: Numbered List Format (for Basic / Sanity tests)

Use when the generator or category calls for **Basic Functionality** (simpler coverage).

### Structure

1. **Test Objective** -- short paragraph or one sentence.
2. **Prerequisites** (if needed) -- Topology Requirements and DUT Configuration Requirements as bullets (`*` in Jira wiki).
3. **Test Steps** -- numbered list:
   - `1. First step`
   - `2. Second step`
   - `3. Third step`
4. **Pass criteria** -- bullet points; each step should map to a pass criterion when using the QA guideline style (one pass criterion per step where applicable).
5. **Verification Commands** -- DNOS `show` commands (with `| no-more` where applicable), listed clearly; in Jira paste, prefer `{{command}}` for inline commands.

### Example (plain Markdown / draft; adapt to Jira wiki when publishing)

1. Configure the feature under test on the DUT.
2. Apply traffic or control-plane stimulus as required.
3. Collect show output and compare to expected state.

**Pass criteria:**

- Configuration commits without error.
- Protocol or feature state matches the expected outcome.
- No unexpected alarms or session drops.

---

## Required Sections (Both Formats)

| Section | Purpose |
|--------|---------|
| 1. Test Objective | What is validated (table format: `*Objective:*` line per test; list format: opening objective). |
| 2. Prerequisites | **Topology Requirements** and **DUT Configuration Requirements** (shared or per-test as needed). |
| 3. Test Steps | Table (`||*Step*||...||`) or numbered list (`1. 2. 3.`). |
| 4. Expected Results | Column in table, or Pass criteria in list format. |
| 5. Verification Commands | DNOS show commands (from EPIC, RST, or `QA_GUIDELINE` in `globals.py`). |

---

## DNOS Command Formatting Rules

- **Jira wiki:** Use **`{{double braces}}`** for inline commands -- **no backticks** in the Jira-published test body (per `globals.py` CRITICAL FORMAT RULES).
- **Config blocks:** Follow DNOS style from `QA_GUIDELINE` in `globals.py` -- e.g. 2-space indentation per level, `!` line endings where required, flat interface hierarchy, correct feature keywords (`protocols bgp <ASN>`, `network-services vrf instance <NAME>`, etc.).
- **Show commands:** Prefer **` \| no-more`** at the end of operational show commands so output is not truncated in interactive sessions (e.g. `{{show route \| no-more}}`).
- **Syntax:** Use only **DriveNets DNOS** CLI syntax (not other vendors).

---

## Reference: Source Prompt Summary

**From `test_plan_ui.py` (FlowSpec VPN EPIC pattern):**

- Basic: numbered steps or bullets; prerequisites if needed.
- Advanced / Scale / HA / CLI: table with `||*Step*||*Action*||*Command*||*Expected Result*||`, Prerequisites with Topology and Configuration Requirements, tests separated by `----`, each test with `*Objective:*`, commands in wiki code form.

**From `globals.py` (`USER_STORY_TEST_ADDITIONAL_INSTRUCTIONS`):**

- Mandatory wiki structure with `h1. +*_Test Steps:_*+`, Prerequisites subsections, tests as `h2. Test N:`, `----` between tests, four-column table, `{{command}}` wrapping, IPv6 note where applicable.
