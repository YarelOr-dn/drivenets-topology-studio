# /TP Portability

Portable `/TP` ships as `mcp_common/profiles/tp/` on the same fetch/upgrade channel as `/SDK`.

## One-command install

```bash
bash mcp_common/profiles/tp/install-tp.sh
```

Or fetch from the delivery repo (any new user, no local mcp_common needed):

```bash
TP_INSTALL_REPO=<mcp_common-git-url> bash install-tp.sh
```

The delivery repo MUST have `mcp_common/` as a top-level directory (the installer
clones it and uses `<clone>/mcp_common`). A reference bare repo built from this
tree lives at `/home/dn/tp-delivery.git` on the origin box; publish/push it to a
network remote (GitHub/internal) and point `TP_INSTALL_REPO` at that URL. Rebuild
it after landing new gate logic:

```bash
STAGE=$(mktemp -d); mkdir -p "$STAGE/mcp_common"
git -C <mcp_common> archive HEAD -- __init__.py profiles/__init__.py profiles/tp \
  | tar -x -C "$STAGE/mcp_common"
git -C "$STAGE" init -q && git -C "$STAGE" add -A \
  && git -C "$STAGE" -c user.email=tp@local -c user.name=tp commit -qm "TP delivery"
rm -rf /home/dn/tp-delivery.git && git clone -q --bare "$STAGE" /home/dn/tp-delivery.git
```

**Upgrade:** re-run `install-tp.sh` (git pull + re-copy reference/skills).

## CLI

```bash
tp doctor
tp knowledge import
tp ingest SW-211037
tp generate SW-211037 --agent none    # deterministic ingest + gates
tp generate SW-211037 --agent cursor  # writes generation_brief.json
tp generate SW-211037 --agent sdk       # hands to /SDK headless runner
tp selfcheck SW-211037
tp parity SW-211037
tp refine SW-211037
tp review SW-211037 --tc TC-... --format chat
tp push SW-211037 --category "Basic Functionality" --dry-run
```

## Configuration

Precedence: `TP_*` env vars -> `~/.cursor/tp_config.json` -> bundled defaults.

| Key | Purpose |
|-----|---------|
| `TP_ROOT` | Epic artifact root (default `~/SCALER/TEST/tp`) |
| `TP_REFERENCE_DIR` | Rubric/checklist (default bundled `reference/`) |
| `TP_KNOWLEDGE_DIR` | Feature knowledge cache (default `~/.cursor/knowledge_base`) |
| `TP_JIRA_MODE` | `auto` \| `rest` \| `plugin` \| `dn-mcp` |
| `TP_STRICT_KNOWLEDGE` | `1` blocks when feature not cached |
| `JIRA_BASE_URL` | Jira Cloud base URL |
| `JIRA_USER_EMAIL` / `JIRA_API_TOKEN` | REST push + ingest |

## Jira backends (auto-fallback)

1. **REST token** — self-contained CLI/CI (`JIRA_*` env or `tp_config.json`)
2. **Atlassian Cursor plugin** — OAuth in IDE (`TP_JIRA_PLUGIN_AVAILABLE=1`)
3. **dn-mcp-server** — lab network `http://ai-server:8000/mcp`

## Knowledge modes

- **Degraded (default):** uncached epic warns; unvalidated syntax tagged `DESIGN` / `EXPECTED_LIVE_VALIDATE`
- **Strict:** `--strict-knowledge` or `TP_STRICT_KNOWLEDGE=1` — requires cached feature knowledge

Seed: `tp knowledge import` copies bundled `knowledge_seed/` (6 features).

## Safety

- Origin `~/SCALER/TEST/tp` scripts are **never modified** — profile uses copies under `profiles/tp/gates/`
- `install-tp.sh` backs up `~/.cursor/mcp.json` before registering `tp-agent-mcp`
- Skips mcp registration if port `:9200` already in use (origin box)
- `--uninstall` restores latest `mcp.json.bak.*`

## MCP packaged

- `tp-agent-mcp` vendored under `profiles/tp/mcp/tp-agent-mcp/`
- `dn-mcp-server` not packaged (remote); use REST token off-lab

## Push guardrails

- Push requires explicit `tp push` (default `--dry-run`)
- Category ownership: never push into Test Categories created by another user (see `/TP` command doc)

## Tests

```bash
bash mcp_common/profiles/tp/tests/run_tests.sh
```
