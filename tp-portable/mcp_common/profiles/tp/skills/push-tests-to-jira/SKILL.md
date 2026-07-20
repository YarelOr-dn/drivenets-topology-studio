---
name: push-tests-to-jira
description: Push test cases from a markdown test plan into Jira as Test Category and Testing Task issues under an SW-project epic. Uses create_jira_test_issues.py for all Jira operations. Triggers on push tests to Jira, sync test plan to Jira, create Jira test items, or push TCs to Jira. Requires four inputs from the user or the skill stops and asks.
---

# Push Test Plan to Jira

## Goal

Create Jira Test Category and Testing Task issues from a markdown test plan by running `create_jira_test_issues.py` with user-supplied inputs. The script handles all parsing, validation, API calls, and reporting.

## Required inputs

The user **must** supply all four. If any is missing or ambiguous, **stop and ask**.

| # | Input | Description | Example |
|---|---|---|---|
| 1 | **test_plan** | Path to a markdown test plan (TC-NNN format from `generate-qa-test-plan`). | `test_plans/SW-211690/test_plan_SW-211690.md` |
| 2 | **epic_id** | Jira SW epic key. **Only** `SW-<digits>`. No other project. | `SW-211690` |
| 3 | **categories** | Ordered list of Test Category names. | `Sanity, HA, Scale` |
| 4 | **tc_assignments** | Mapping of TCs to categories. Ranges (`TC-001-015`), singles (`TC-035`), or mixed. Each TC in exactly one category. | `Sanity: TC-001-002, TC-008; HA: TC-009-016` |

## Script

**Path:** `.ai/skills/qa/push-tests-to-jira/scripts/create_jira_test_issues.py`

The script is Python 3 stdlib-only (no pip). It handles:
- Markdown parsing (positional section extraction — tolerates misnumbered or misnamed sections)
- TC range expansion and overlap/existence validation
- Jira wiki markup generation for `customfield_11772` (Test Description)
- REST API calls to create Test Category and Testing Task issues
- Hierarchical parent linking (Epic → Test Category → Testing Task)

**CLI interface:**

```
python3 .ai/skills/qa/push-tests-to-jira/scripts/create_jira_test_issues.py \
  <test_plan_path> \
  --epic <SW-NNNNN> \
  --category "CategoryName: TC-NNN-NNN, TC-NNN" \
  [--category "AnotherCat: TC-NNN-NNN"] \
  [--priority Medium|High|Low] \
  [--link-covers] [--link-type Relates] \
  [--dry-run]
```

**Key flags:**
- `--category` — repeatable; format is `"Name: TC-NNN-NNN, TC-NNN"` (name + colon + TC list).
- `--priority` — optional, default Medium. Accepts Highest, High, Medium, Low, Lowest.
- `--dry-run` — parse and validate only, no Jira API calls.
- `--link-covers` — **OPT-IN, OFF by default.** After creating each Testing Task,
  add a Jira issue link (default type `Relates`) from that task to every
  `SW-<digits>` story the TC *Covers* — resolved from the TC block's provenance
  lines (Covers / Stories / source_story / enabler_epic). The parent epic and
  self-links are skipped and keys are de-duplicated. A single link failure prints
  a WARNING and the push continues (it never aborts). With `--dry-run`, the plan
  preview shows the would-be links per TC. When the flag is omitted, behavior is
  unchanged (hierarchical parent linking only; provenance stays plain text).
- `--link-type` — optional link-type name for `--link-covers` (default `Relates`).

**Auth:** Requires `JIRA_USERNAME` and `JIRA_API_TOKEN` environment variables. The script will exit with an error if either is missing.

## Workflow

### Stage 1: Collect and validate inputs

1. Parse the user's request for the four required inputs.
2. If any input is missing, list what is missing and ask. **Do not proceed.**
3. Validate `epic_id` matches `^SW-\d+$`. If not, **stop** with rejection reason.
4. Verify the test plan file exists at the given path.
5. Translate the user's category and TC assignment into `--category` arguments for the script. Each `--category` is `"Name: TC-list"`.
6. If the user provides categories and assignments separately, combine them. If the user gives a natural-language description, map it to the structured format.
7. If TCs are intentionally excluded, confirm the exclusion list with the user.

**Gate:** All four inputs present; epic is `SW-<digits>`; test plan file exists; category-to-TC mapping is unambiguous with no overlaps.

### Stage 2: Dry-run validation

1. Run the script with `--dry-run` to validate parsing and TC assignments without creating issues:

```bash
python3 .ai/skills/qa/push-tests-to-jira/scripts/create_jira_test_issues.py \
  <test_plan> --epic <epic_id> \
  --category "Cat1: TC-001-005" \
  --category "Cat2: TC-006-010" \
  --dry-run
```

2. Check the output for:
   - All TCs found and parsed (no `0 test cases`).
   - No errors about missing TCs or overlaps.
   - The plan summary matches what the user asked for.
   - Any WARNING about unassigned TCs — show this to the user and confirm whether to proceed or add them.
3. If the dry-run fails (non-zero exit code or error output), show the full error to the user and ask how to proceed. Common failures:
   - `error: epic must be SW-<digits>` — wrong project key.
   - `error: TC-NNN not found in test plan` — TC does not exist in the file.
   - `error: TC-NNN assigned to both X and Y` — overlapping assignments.

**Gate:** Dry-run exits 0; plan summary shown to user; unassigned-TC warnings addressed (user confirms skip or adds them).

### Stage 3: Execute

1. Run the script **without** `--dry-run`:

```bash
python3 .ai/skills/qa/push-tests-to-jira/scripts/create_jira_test_issues.py \
  <test_plan> --epic <epic_id> \
  --category "Cat1: TC-001-005" \
  --category "Cat2: TC-006-010" \
  [--priority Medium]
```

2. Monitor output. The script prints each created issue key and URL as it goes.
3. If the script fails mid-run (API error, auth failure, network issue):
   - Show the full error output to the user.
   - Report which issues were already created (the script prints them before failure).
   - Do **not** retry automatically — ask the user whether to retry, skip the failing item, or abort.
4. If the script exits 0, proceed to Stage 4.

**Gate:** Script exits 0 with all issues created, OR user has been informed of partial failure and decided next steps.

### Stage 4: Report results

1. Present the script's RESULTS section to the user in a clear table:
   - Epic key
   - Each Test Category key + name + Jira URL
   - Each Testing Task key + TC-NNN + Jira URL, nested under its category
2. If any TCs were not pushed, list them with the reason.
3. Suggest the user spot-check one Testing Task in Jira to verify `customfield_11772` (Test Description) renders with proper headings and lists.

**Gate:** Results table presented; user informed of any gaps.

## Output format

1. **Input validation summary** — parsed inputs and their values.
2. **Dry-run output** — script plan preview (categories, TC counts, summaries).
3. **Execution log** — real-time script output showing created issue keys.
4. **Results table** — final mapping: category → Test Category key; TC-NNN → Testing Task key + URL.

## Quality bar (self-check)

[ ] All four required inputs were collected before running the script; skill stopped and asked when inputs were missing.
[ ] `epic_id` is `SW-<digits>` only; skill rejected non-SW keys.
[ ] Dry-run was executed first; any warnings were surfaced to the user.
[ ] Script was invoked via `create_jira_test_issues.py` for all Jira operations — no MCP calls, no ad-hoc API requests.
[ ] Script errors were shown to the user with full context, not silently swallowed.
[ ] Results table includes every created issue key and URL, or lists skipped TCs with reason.
[ ] User was advised to spot-check at least one issue in Jira for proper formatting.
