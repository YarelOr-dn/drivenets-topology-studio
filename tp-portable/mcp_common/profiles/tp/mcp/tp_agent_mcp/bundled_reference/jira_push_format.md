# Jira push format (Test Category + Testing Task)

Source skill: `cheetah/.ai/skills/qa/push-tests-to-jira/SKILL.md`

Script: `cheetah/.ai/skills/qa/push-tests-to-jira/scripts/create_jira_test_issues.py`

## Required inputs (operator must supply)

1. `test_plan` path — markdown with `### **TC-NNN:` blocks
2. `epic_id` — `SW-<digits>` only
3. Category names (ordered)
4. TC assignment string per category

## Dry-run first

```bash
python3 create_jira_test_issues.py <test_plan.md> --epic SW-NNNNN \
  --category "Sanity: TC-001-002" --dry-run
```

## Auth

`JIRA_USERNAME` and `JIRA_API_TOKEN` must be set in the environment for live push.
