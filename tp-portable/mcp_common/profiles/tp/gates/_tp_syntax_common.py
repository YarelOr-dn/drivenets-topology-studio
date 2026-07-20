#!/usr/bin/env python3
"""Shared helpers for /TP syntax source-of-truth binding (harvester, version, gate)."""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from _tp_paths import resolve_cache_dir, resolve_cheetah_glob
from typing import Any

TP_CACHE_DIR = resolve_cache_dir()
CHEETAH_GLOB = Path(resolve_cheetah_glob())

_FIX_VERSION = re.compile(r"\*Fix versions?:\*?\s*([^\n]+)", re.I)
_V_TAG = re.compile(r"\bv(\d+)[._](\d+)\b", re.I)
_SW_HEADER = re.compile(r"^##\s+(SW-\d+)\b", re.M)
_CMD_SYNTAX = re.compile(r"\*\*cmd syntax:\*\*\s*(.+?)(?:\n|$)", re.I)
_CMD_LEVEL = re.compile(r"\*\*cmd level:\s*(.+?)\*\*", re.I)
_RST_SYNTAX = re.compile(r"\*\*Command syntax:\s*(.+?)\*\*", re.I)
_META_SUFFIXES = (
    "; commit",
    "; commit check",
    "; rollback 0",
    " ; commit",
    " ; commit check",
    " ; rollback 0",
)


def atomic_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def parse_fix_versions(text: str) -> list[str]:
    m = _FIX_VERSION.search(text)
    if not m:
        return []
    raw = m.group(1)
    parts = [p.strip().strip(",") for p in re.split(r",\s*", raw) if p.strip()]
    return parts


def primary_dnos_version(fix_versions: list[str]) -> str | None:
    """Return first vMAJOR.MINOR token (e.g. v26.4) or None."""
    for fv in fix_versions:
        m = _V_TAG.search(fv)
        if m:
            return f"v{m.group(1)}.{m.group(2)}"
    return None


def version_tuple(tag: str) -> tuple[int, int] | None:
    m = _V_TAG.search(tag)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def normalize_cmd(cmd: str) -> str:
    """Lossy normalization for placeholder-aware command matching."""
    s = str(cmd or "").strip().lower()
    if not s:
        return ""
    # non-CLI probes (gNMI, etc.) — match by keyword stem only
    if s.startswith("(gnmi") or s.startswith("(netconf"):
        return s
    s = re.sub(r"//.*$", "", s, flags=re.M)
    s = re.split(r"\s*\|\s*include\b", s)[0].strip()
    s = re.split(r"\s*\|\s*", s)[0].strip()
    s = s.rstrip("?").strip()
    for suffix in _META_SUFFIXES:
        while s.endswith(suffix):
            s = s[: -len(suffix)].strip()
    s = re.sub(r"<[^>]+>", "<>", s)
    s = re.sub(r"\bsvc-[\w-]+", "<>", s)
    s = re.sub(r"\birb\w*", "<>", s)
    s = re.sub(r"\bpe-[\w-]+", "<>", s)
    s = re.sub(r"\b[a-z]+-if[\w-]*", "<>", s)
    s = re.sub(r"\bword\b", "<>", s)
    s = re.sub(r"\binstance\s+<>\s+instance\s+<>", "instance <>", s)
    s = re.sub(r"<enabled/disabled>", "<>", s, flags=re.I)
    s = re.sub(r"\benabled\b|\bdisabled\b", "<>", s)
    s = re.sub(r"\b\d+\b", "<n>", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def split_commands(cmd: str) -> list[str]:
    raw = str(cmd or "").strip()
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(";") if p.strip()]
    out: list[str] = []
    for p in parts:
        low = p.lower()
        if low in ("commit", "commit check", "rollback 0"):
            continue
        out.append(p)
    return out


def cmd_kind(cmd: str) -> str:
    low = cmd.strip().lower()
    if low.startswith("show ") or low.startswith("debug "):
        return "show"
    if low.startswith("configure ") or low.startswith("no ") or low.startswith("clear "):
        return "config"
    if low.startswith("load ") or low.startswith("rollback"):
        return "config"
    return "other"


def extract_tc_commands(full_result: dict) -> list[dict[str, str]]:
    """Flatten every command string from full_result test cases."""
    rows: list[dict[str, str]] = []
    for tc in full_result.get("test_cases") or []:
        tc_id = str(tc.get("id") or "")
        for step in tc.get("steps") or []:
            if not isinstance(step, dict):
                continue
            for part in split_commands(str(step.get("command") or "")):
                rows.append({"tc_id": tc_id, "command": part, "origin": "step"})
        for vc in tc.get("verification_commands") or []:
            if not isinstance(vc, dict):
                continue
            for part in split_commands(str(vc.get("command") or "")):
                rows.append({"tc_id": tc_id, "command": part, "origin": "verification"})
    return rows


def git_short_sha(repo: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return (out.stdout or "").strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def git_branches(repo: Path) -> set[str]:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "branch", "-a"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        branches: set[str] = set()
        for line in (out.stdout or "").splitlines():
            b = line.strip().lstrip("* ").strip()
            if b.startswith("remotes/origin/"):
                b = b.split("remotes/origin/", 1)[1]
            if b and "HEAD" not in b:
                branches.add(b)
        return branches
    except (OSError, subprocess.SubprocessError):
        return set()


def read_version_file(repo: Path) -> str | None:
    vf = repo / "VERSION"
    if vf.is_file():
        return vf.read_text(encoding="utf-8").strip().splitlines()[0].strip()
    return None


def cheetah_checkouts() -> list[Path]:
    home = Path.home()
    dirs = sorted(home.glob("cheetah*"))
    return [d for d in dirs if d.is_dir() and (d / ".git").is_dir()]


def dev_branch_for_version(ver: str) -> str:
    vt = version_tuple(ver)
    if not vt:
        return ""
    major, minor = vt
    return f"dev_v{major}_{minor}"


def worktree_add_cmd(ver: str, base: Path | None = None) -> str:
    vt = version_tuple(ver)
    base = base or (Path.home() / "cheetah")
    if not vt:
        return ""
    major, minor = vt
    dest = Path.home() / f"cheetah_{major}_{minor}"
    branch = f"dev_v{major}_{minor}"
    return f"git -C {base} worktree add {dest} origin/{branch}"


def resolve_cheetah_for_version(ver: str) -> dict[str, Any]:
    """Map vMAJOR.MINOR to a local cheetah checkout (git branch/dir match). No tip fallback."""
    vt = version_tuple(ver)
    if not vt:
        return {
            "fix_version": ver,
            "matched": False,
            "repo": None,
            "rst_root": None,
            "branch": None,
            "sha": None,
            "blocker": {"message": f"Unparseable fix version: {ver}"},
        }
    major, minor = vt
    want_branch = f"dev_v{major}_{minor}"
    want_dir = Path.home() / f"cheetah_{major}_{minor}"
    candidates: list[tuple[int, Path, str]] = []

    for repo in cheetah_checkouts():
        branches = git_branches(repo)
        score = 0
        if repo == want_dir:
            score += 100
        if repo.name == f"cheetah_{major}_{minor}":
            score += 50
        if want_branch in branches:
            score += 30
        if f"remotes/origin/{want_branch}" in {f"remotes/origin/{b}" for b in branches}:
            score += 20
        ver_file = read_version_file(repo)
        if ver_file:
            vm = re.match(r"(\d+)\.(\d+)", ver_file)
            if vm and int(vm.group(1)) == major and int(vm.group(2)) == minor:
                score += 10
        if score > 0:
            candidates.append((score, repo, want_branch if want_branch in branches else ""))

    if not candidates:
        return {
            "fix_version": ver,
            "matched": False,
            "repo": None,
            "rst_root": None,
            "branch": want_branch,
            "sha": None,
            "blocker": {
                "message": f"[BLOCKER] no cheetah checkout for {ver}",
                "suggested_cmd": worktree_add_cmd(ver),
            },
        }

    candidates.sort(key=lambda x: (-x[0], str(x[1])))
    repo = candidates[0][1]
    rst_root = repo / "prod" / "dnos_monolith" / "dnos_cli"
    return {
        "fix_version": ver,
        "matched": True,
        "repo": str(repo),
        "rst_root": str(rst_root) if rst_root.is_dir() else None,
        "branch": candidates[0][2] or want_branch,
        "sha": git_short_sha(repo),
        "blocker": None,
    }


def parse_story_cmd_blocks(text: str) -> list[dict[str, str]]:
    """Parse user_story_bodies.md into cmd inventory rows."""
    entries: list[dict[str, str]] = []
    sections = re.split(r"(?=^##\s+SW-\d+)", text, flags=re.M)
    for sec in sections:
        hm = _SW_HEADER.search(sec)
        if not hm:
            continue
        sw_key = hm.group(1)
        syntax_m = _CMD_SYNTAX.search(sec)
        if syntax_m:
            syntax = syntax_m.group(1).strip()
            level_m = _CMD_LEVEL.search(sec)
            level = level_m.group(1).strip() if level_m else ""
            full = f"{level} {syntax}".strip() if level else syntax
            entries.append({
                "sw_key": sw_key,
                "syntax": syntax,
                "level": level,
                "full": full,
                "raw": syntax,
            })
        for m in re.finditer(r"^dnRouter#\s+(.+)$", sec, re.M):
            cmd = m.group(1).strip()
            if cmd.lower().startswith(("show ", "debug ", "configure ", "clear ")):
                entries.append({
                    "sw_key": sw_key,
                    "syntax": cmd,
                    "level": "",
                    "full": cmd,
                    "raw": cmd,
                })
        for m in re.finditer(r"`((?:show|debug|configure|clear) [^`]+)`", sec, re.I):
            cmd = m.group(1).strip()
            entries.append({
                "sw_key": sw_key,
                "syntax": cmd,
                "level": "",
                "full": cmd,
                "raw": cmd,
            })
    return entries


def parse_rst_syntax(text: str, rel_path: str) -> list[str]:
    return [m.group(1).strip() for m in _RST_SYNTAX.finditer(text)]


def commands_match(tc_norm: str, spec_norm: str) -> bool:
    if not tc_norm or not spec_norm:
        return False
    if tc_norm == spec_norm:
        return True
    if spec_norm in tc_norm or tc_norm in spec_norm:
        return True
    tc_tokens = set(tc_norm.split())
    spec_tokens = set(spec_norm.split())
    if len(spec_tokens) >= 3 and spec_tokens.issubset(tc_tokens):
        return True
    return False
