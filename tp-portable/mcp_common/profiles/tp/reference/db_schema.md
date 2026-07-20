# TP Knowledge DB Schema

The merged `/TP` pipeline uses a SQLite-first local DB at:

`~/.cursor/tp-reference/db/tp_knowledge.sqlite`

The DB is a normalized local search layer. Markdown and JSON exports are written
to `~/.cursor/tp-reference/generated/` so agents can read compact context without
re-parsing every source file.

## Tables

| Table | Purpose |
|---|---|
| `source_documents` | Jira epics/stories, Confluence pages, RFCs, local skills, local rules, generated TP artifacts |
| `rubric_rules` | Costake requirements, TP checklist categories, feature-specific rules |
| `command_catalog` | DNOS show/config/clear/debug commands by feature, category, and verification status |
| `flow_catalog` | Reusable setup, trigger, traffic, HA, and verification patterns |
| `test_case_catalog` | Normalized TC objects before markdown/Jira rendering |
| `dedup_fingerprints` | Duplicate and near-duplicate signatures |
| `coverage_links` | Many-to-many traceability from TCs to epics, stories, categories, rubric rules, commands |

## Provenance Status

| Status | Meaning |
|---|---|
| `JIRA_SPEC` | Requirement or behavior came from Jira |
| `CONFLUENCE_CANONICAL` | Canonical Confluence spec or QA plan |
| `COSTAKE_RUBRIC` | Alexandru Costake `test_plan_requirements.md` |
| `TP_CHECKLIST` | Local `/TP` checklist category |
| `LOCAL_SKILL` | Local Cursor skill knowledge |
| `CHEATSHEET_DEBUG` | Debug-only command from a cheat sheet; useful, not a behavioral spec |
| `LIVE_VALIDATED` | Verified on a live DNOS device |
| `EXPECTED_LIVE_VALIDATE` | Expected from design/spec but not live-validated yet |
| `LOCAL_GENERATED` | Generated TP artifact |

## Commands

Every command catalog row must include:

- `command_text`
- `command_type`: `show`, `config`, `clear`, `debug`, or `other`
- `feature`
- `verification_status`
- `source_key`

Do not promote `CHEATSHEET_DEBUG` or `EXPECTED_LIVE_VALIDATE` commands to
`LIVE_VALIDATED` without a captured device transcript.

## Standard Operations

```bash
python3 ~/.cursor/tools/tp_knowledge_db.py init
python3 ~/.cursor/tools/tp_knowledge_db.py seed-core
python3 ~/.cursor/tools/tp_knowledge_db.py ingest-sources --tp-dir ~/SCALER/TEST/tp/SW-228552
python3 ~/.cursor/tools/tp_knowledge_db.py export
python3 ~/.cursor/tools/tp_knowledge_db.py integrity
```
