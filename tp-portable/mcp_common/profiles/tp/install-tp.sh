#!/usr/bin/env bash
# install-tp.sh — one-shot /TP portable installer (mcp_common profile).
# Usage:
#   bash mcp_common/profiles/tp/install-tp.sh
#   bash install-tp.sh --mcp-common /path/to/mcp_common
set -euo pipefail

HOME_DIR="${HOME:?HOME not set}"
BASE_DIR="${TP_INSTALL_DIR:-$HOME_DIR/tp-runner}"
MCP_COMMON_SRC=""
DRY_RUN=0
UNINSTALL=0
JIRA_EMAIL="${JIRA_USER_EMAIL:-${JIRA_USERNAME:-}}"
JIRA_TOKEN="${JIRA_API_TOKEN:-}"

usage() {
  cat <<'EOF'
install-tp.sh — install portable /TP on this machine

Options:
  --base DIR           Install root (default: ~/tp-runner)
  --mcp-common PATH    Path to mcp_common tree (or set TP_MCP_COMMON_SRC)
  --email EMAIL        Jira user email (or JIRA_USER_EMAIL)
  --token TOKEN        Jira API token (or JIRA_API_TOKEN)
  --dry-run            Print actions only
  --uninstall          Remove tp wrapper + restore mcp.json from latest .bak
  -h, --help           This help

After install:
  - CLI: tp doctor | tp ingest SW-XXXXX | tp generate SW-XXXXX --agent none
  - Upgrade: re-run this script (pulls mcp_common if cloned)

Env:
  TP_INSTALL_REPO      git clone URL for bundle (optional)
EOF
}

log() { printf '[TP-INSTALL] %s\n' "$*"; }
die() { printf '[TP-INSTALL][ERROR] %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base) BASE_DIR="$2"; shift 2 ;;
    --mcp-common) MCP_COMMON_SRC="$2"; shift 2 ;;
    --email) JIRA_EMAIL="$2"; shift 2 ;;
    --token) JIRA_TOKEN="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --uninstall) UNINSTALL=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown arg: $1" ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_COMMON_SRC="${MCP_COMMON_SRC:-${TP_MCP_COMMON_SRC:-}}"

if [[ -z "$MCP_COMMON_SRC" ]]; then
  if [[ -f "$SCRIPT_DIR/tp_env.py" ]]; then
    MCP_COMMON_SRC="$(cd "$SCRIPT_DIR/../.." && pwd)"
  elif [[ -d "$HOME_DIR/mcp_common" ]]; then
    MCP_COMMON_SRC="$HOME_DIR/mcp_common"
  fi
fi

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[dry-run] $*"
  else
    "$@"
  fi
}

atomic_write_json() {
  local path="$1" content="$2"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[dry-run] atomic write $path"
    return
  fi
  python3 - <<PY
import os, tempfile, json
from pathlib import Path
path = Path(${path@Q})
obj = json.loads(${content@Q})
path.parent.mkdir(parents=True, exist_ok=True)
data = json.dumps(obj, indent=2) + "\n"
fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".", suffix=".tmp")
with os.fdopen(fd, "w") as f:
    f.write(data)
    f.flush()
    os.fsync(f.fileno())
os.chmod(tmp, 0o600)
os.replace(tmp, path)
PY
}

backup_mcp_json() {
  local target="$1"
  [[ -f "$target" ]] || return 0
  local ts
  ts="$(date +%Y%m%d_%H%M%S)"
  run cp -a "$target" "${target}.bak.${ts}"
  log "backed up $target -> ${target}.bak.${ts}"
}

if [[ "$UNINSTALL" -eq 1 ]]; then
  log "=== /TP uninstall ==="
  run rm -f "$HOME_DIR/.local/bin/tp"
  latest_bak="$(ls -t "$HOME_DIR/.cursor/mcp.json.bak."* 2>/dev/null | head -1 || true)"
  if [[ -n "$latest_bak" ]]; then
    run cp -a "$latest_bak" "$HOME_DIR/.cursor/mcp.json"
    log "restored mcp.json from $latest_bak"
  fi
  exit 0
fi

log "=== /TP install ==="
log "base=$BASE_DIR user=$(whoami)"

if [[ -n "${TP_INSTALL_REPO:-}" && ! -d "$MCP_COMMON_SRC" ]]; then
  log "cloning $TP_INSTALL_REPO"
  run mkdir -p "$BASE_DIR"
  run git clone --depth 1 ${TP_INSTALL_BRANCH:+-b "$TP_INSTALL_BRANCH"} "$TP_INSTALL_REPO" "$BASE_DIR/repo"
  MCP_COMMON_SRC="$BASE_DIR/repo/mcp_common"
elif [[ -d "$MCP_COMMON_SRC/.git" ]]; then
  log "upgrading mcp_common at $MCP_COMMON_SRC"
  run git -C "$MCP_COMMON_SRC" pull --ff-only || log "WARN: git pull failed; using existing tree"
fi

[[ -d "$MCP_COMMON_SRC" ]] || die "mcp_common not found; pass --mcp-common or set TP_INSTALL_REPO"

MCP_COMMON_SRC="$(readlink -f "$MCP_COMMON_SRC")"
PROFILE_DIR="$MCP_COMMON_SRC/profiles/tp"
[[ -d "$PROFILE_DIR" ]] || die "profiles/tp missing under $MCP_COMMON_SRC"

PYTHONPATH_ROOT="$(dirname "$MCP_COMMON_SRC")"
export PYTHONPATH="$PYTHONPATH_ROOT:$MCP_COMMON_SRC:${PYTHONPATH:-}"

log "python deps (optional — gates are stdlib-first)"
# The gates/CLI run on the stdlib; requirements.txt is only for the optional
# tp-agent-mcp server. Never HANG an install on pip: skip when deps already
# import, when offline, or when TP_SKIP_PIP=1. Cap pip with a hard timeout.
if [[ "$DRY_RUN" -eq 0 && "${TP_SKIP_PIP:-0}" != "1" ]]; then
  if python3 -c "import requests, httpx" >/dev/null 2>&1; then
    log "core deps already present — skipping pip"
  elif ! timeout 5 python3 - <<'PY' >/dev/null 2>&1
import socket; socket.setdefaulttimeout(4); socket.create_connection(("pypi.org", 443))
PY
  then
    log "WARN: no PyPI network — skipping pip (set TP_SKIP_PIP=1 to silence; gates still work offline)"
  else
    timeout 120 python3 -m pip install --user -q -r "$PROFILE_DIR/requirements.txt" 2>/dev/null || \
      timeout 120 python3 -m pip install -q -r "$PROFILE_DIR/requirements.txt" 2>/dev/null || \
      log "WARN: pip install failed/timed out — continuing (deps optional for gates+CLI)"
  fi
fi

# tp_config.json
TP_CONFIG="$HOME_DIR/.cursor/tp_config.json"
if [[ "$DRY_RUN" -eq 0 ]]; then
  cfg='{}'
  if [[ -f "$TP_CONFIG" ]]; then
    cfg="$(cat "$TP_CONFIG")"
  fi
  python3 - <<PY
import json
from pathlib import Path
cfg = json.loads(${cfg@Q})
if ${JIRA_EMAIL@Q}:
    cfg.setdefault("jira", {})["user_email"] = ${JIRA_EMAIL@Q}
if ${JIRA_TOKEN@Q}:
    cfg.setdefault("jira", {})["api_token"] = ${JIRA_TOKEN@Q}
cfg.setdefault("reference_dir", str(Path(${PROFILE_DIR@Q}) / "reference"))
cfg.setdefault("tp_root", str(Path.home() / "SCALER" / "TEST" / "tp"))
path = Path.home() / ".cursor" / "tp_config.json"
path.parent.mkdir(parents=True, exist_ok=True)
import os, tempfile
data = json.dumps(cfg, indent=2) + "\n"
fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".", suffix=".tmp")
with os.fdopen(fd, "w") as f:
    f.write(data); f.flush(); os.fsync(f.fileno())
os.chmod(tmp, 0o600); os.replace(tmp, path)
print(path)
PY
  log "wrote $TP_CONFIG"
fi

# seed reference + knowledge (idempotent copy)
REF_DEST="$HOME_DIR/.cursor/tp-reference"
KNOW_DEST="$HOME_DIR/.cursor/knowledge_base"
run mkdir -p "$REF_DEST" "$KNOW_DEST"
if [[ "$DRY_RUN" -eq 0 ]]; then
  cp -a "$PROFILE_DIR/reference/." "$REF_DEST/"
  for d in "$PROFILE_DIR/knowledge_seed"/*; do
    [[ -d "$d" ]] || continue
    name="$(basename "$d")"
    [[ -d "$KNOW_DEST/$name" ]] || cp -a "$d" "$KNOW_DEST/"
  done
fi

# skills
SKILLS_HOME="$HOME_DIR/.claude/skills"
run mkdir -p "$SKILLS_HOME"
if [[ "$DRY_RUN" -eq 0 ]]; then
  for s in "$PROFILE_DIR/skills"/*; do
    [[ -d "$s" ]] || continue
    name="$(basename "$s")"
    rm -rf "$SKILLS_HOME/$name"
    cp -a "$s" "$SKILLS_HOME/$name"
  done
fi

# mcp.json — register tp-agent-mcp only if not already on :9200
merge_tp_mcp() {
  local target="$1"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[dry-run] would merge tp-agent-mcp into $target"
    return
  fi
  if ss -ltn 2>/dev/null | grep -q ':9200 '; then
    log "port 9200 already in use — skipping tp-agent-mcp registration (origin box safe)"
    return
  fi
  backup_mcp_json "$target"
  run mkdir -p "$(dirname "$target")"
  python3 - <<PY
import json
from pathlib import Path
target = Path(${target@Q})
mcp_root = Path(${PROFILE_DIR@Q}) / "mcp" / "tp_agent_mcp"
py_parent = str(mcp_root.parent)
entry = {
    "tp-agent-mcp": {
        "command": "python3",
        "args": ["-m", "tp_agent_mcp.server"],
        "env": {"PYTHONPATH": py_parent},
    }
}
data = {}
if target.is_file():
    try:
        data = json.loads(target.read_text())
    except Exception:
        data = {}
servers = data.setdefault("mcpServers", data.setdefault("mcp_servers", {}))
if "mcp_servers" in data and "mcpServers" not in data:
    servers = data["mcp_servers"]
if "tp-agent-mcp" not in servers:
    servers["tp-agent-mcp"] = entry["tp-agent-mcp"]
target.write_text(json.dumps(data, indent=2) + "\n")
print("updated", target)
PY
}

merge_tp_mcp "$HOME_DIR/.cursor/mcp.json"

# tp on PATH
BIN_DIR="$HOME_DIR/.local/bin"
run mkdir -p "$BIN_DIR"
if [[ "$DRY_RUN" -eq 0 ]]; then
  cat > "$BIN_DIR/tp" <<WRAP
#!/usr/bin/env bash
export PYTHONPATH="${PYTHONPATH_ROOT}:${MCP_COMMON_SRC}:\${PYTHONPATH:-}"
exec python3 -m mcp_common.profiles.tp.tp_cli "\$@"
WRAP
  chmod +x "$BIN_DIR/tp"
fi

log "=== self-check ==="
if [[ "$DRY_RUN" -eq 0 ]]; then
  if ! python3 -m mcp_common.profiles.tp.tp_cli doctor; then
    log "WARN: doctor reported issues — see remediation (Jira creds may be missing until configured)"
  else
    log "[OK] doctor passed"
  fi
fi

cat <<SUMMARY

[OK] /TP installed

  Profile:     $PROFILE_DIR
  CLI:         tp doctor | tp ingest SW-XXXXX | tp generate SW-XXXXX --agent none
  Config:      ~/.cursor/tp_config.json (chmod 600)
  Reference:   ~/.cursor/tp-reference
  Knowledge:   ~/.cursor/knowledge_base (seed copied if absent)
  Upgrade:     re-run install-tp.sh

Next:
  1. Set JIRA_USER_EMAIL + JIRA_API_TOKEN (or edit ~/.cursor/tp_config.json)
  2. Reload Cursor after mcp.json change
  3. tp doctor
  4. tp generate SW-XXXXX --agent cursor|sdk|none
SUMMARY
