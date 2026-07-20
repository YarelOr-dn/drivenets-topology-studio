# Portable `/TP` — one-prompt install

This directory vendors the portable DNOS **Test Plan generator** (`/TP`) so any
teammate who clones `drivenets-topology-studio` can install it with one command.

## Give your agent this prompt

> Install the portable /TP tool from this repo: run
> `bash tp-portable/mcp_common/profiles/tp/install-tp.sh` from the repo root,
> then run `tp doctor` and tell me if `go` is true. If Jira credentials are
> missing, tell me to export `JIRA_USER_EMAIL` and `JIRA_API_TOKEN`.

## Or install it yourself (one command, from the repo root)

```bash
bash tp-portable/mcp_common/profiles/tp/install-tp.sh
```

What it does (idempotent, safe):

- Puts a `tp` CLI on your PATH (`~/.local/bin/tp`).
- Seeds `~/.cursor/tp-reference` + `~/.cursor/knowledge_base` (6 feature seeds).
- Registers the `tp-agent-mcp` server in `~/.cursor/mcp.json` (backs it up first;
  skips if port `:9200` is already in use).
- Writes `~/.cursor/tp_config.json` (chmod 600).
- Runs `tp doctor` as a self-check.

## After install

1. Set your **own** Jira credentials (per-user secrets, never committed):

   ```bash
   export JIRA_USER_EMAIL="you@drivenets.com"
   export JIRA_API_TOKEN="<your-atlassian-api-token>"
   # or edit ~/.cursor/tp_config.json  ->  {"jira": {...}}
   ```

2. Reload Cursor (so the new `mcp.json` entry binds).
3. Verify: `tp doctor`  (expect `"go": true`).
4. Use it:

   ```bash
   tp ingest SW-XXXXX                 # pull epic + enabler epics from Jira
   tp generate SW-XXXXX --agent cursor  # author in Cursor with the /TP skill
   tp generate SW-XXXXX --agent sdk     # hand to the /SDK headless runner
   tp generate SW-XXXXX --agent none    # deterministic ingest + gates only
   tp selfcheck SW-XXXXX && tp parity SW-XXXXX
   tp review SW-XXXXX --tc <id> --format chat
   tp push SW-XXXXX --category "CLI" --dry-run
   ```

## Upgrade

Pull the latest `drivenets-topology-studio`, then re-run the installer:

```bash
git pull && bash tp-portable/mcp_common/profiles/tp/install-tp.sh
```

Full details: `tp-portable/mcp_common/profiles/tp/TP_PORTABILITY.md`.
