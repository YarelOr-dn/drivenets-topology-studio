# QA TP pipeline (Alexandru-style)

Use this staged flow for every SW epic test plan:

## Stage 1 — Epic documentation

- Input: primary `SW-NNNNN` plus optional related epics (DP/Infra/NM enablers).
- Pull Jira: epic fields, full description, attachments list, issue links, epic comments, User Stories with descriptions and comments.
- Output artifact: `epic_documentation_<EPIC>.md` (or `tp_submit_stage` with stage `epic_documentation`).
- Gate: every non-rejected User Story appears; linked epics and enabler guesses captured; key comment decisions summarized.

## Stage 2 — Test plan

- Inputs: Stage 1 doc + `test_plan_requirements` context + Confluence TP Checklist Guide page ID `3934912829`.
- Output: `test_plan_<EPIC>.md` with Applicable Checklist Categories tables, `## Test Cases`, `## Skipped Categories`.
- Gates: one TC per User Story; 18 always-required categories covered or explicitly skipped with one-line justification; conditional categories evaluated; variants are not coverage.

## Stage 3 — Self-review

- Re-read requirements and Stage 1; update TCs in place; close gaps.
- Output: updated `test_plan_<EPIC>.md` + optional `quality_gate` record.

## Stage 4 — Optional Jira push

- Use `push-tests-to-jira` / `create_jira_test_issues.py` with dry-run first.
- Never auto-push without explicit operator approval.

## Stage 5 — /TEST import

- Read `~/SCALER/TEST/tp/<EPIC>/manifest.json` and `test_plan_<EPIC>.md`.
- Map selected TCs to `recipe.json` with `traceability` fields for automation.
