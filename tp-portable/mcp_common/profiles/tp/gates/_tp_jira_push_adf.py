#!/usr/bin/env python3
"""
/TP-owned Jira Cloud ADF push tool.

Posts per-device test config as REAL collapsible Jira ADF `expand` nodes via the
Jira Cloud REST API v3, instead of the wiki `{expand}...{expand}` macro (which
renders as LITERAL TEXT on Jira Cloud) or the dn-mcp markdown path (which mangles
content, e.g. turns <vlan> into [vlan]).

The native Jira Cloud collapsible is the ADF `expand` node:

    {"type": "expand", "attrs": {"title": "..."}, "content": [ ...block nodes... ]}

wrapped in an ADF doc {"type": "doc", "version": 1, "content": [...]}.

Auth (reused, never invented):
  1. Env vars JIRA_USERNAME + JIRA_API_TOKEN (same contract as the existing
     push-tests-to-jira/create_jira_test_issues.py).
  2. Fallback: /home/dn/.cursor/mcp.json -> mcpServers.dn-mcp-server.headers
     -> X-Email-User + X-Atlassian-Token (the working Atlassian Cloud API token
     the dn-mcp server already uses).
  3. CLI overrides --email / --token.
Basic auth = base64(email:token) over https://drivenets.atlassian.net/rest/api/3.
Secrets are never printed.

CLI examples:
  # dry-run: build ADF and print it, do not touch Jira
  python3 _tp_jira_push_adf.py --demo --dry-run

  # prove on SW-284893: PUT the 2-device demo ADF to the description, then verify
  python3 _tp_jira_push_adf.py --issue SW-284893 --demo --push --verify

  # push per-device config from a JSON payload to any issue's description
  python3 _tp_jira_push_adf.py --issue SW-XXXXX --from-json payload.json --push --verify

  # build a real TC's per-device config straight from the epic manifest
  python3 _tp_jira_push_adf.py --epic SW-211037 --tc <id-or-substring> --dry-run
  python3 _tp_jira_push_adf.py --epic SW-211037 --tc <id> --issue SW-284893 --push --verify

  # standalone verify (GET the issue, count expand nodes)
  python3 _tp_jira_push_adf.py --issue SW-XXXXX --verify

No external deps beyond `requests` (optional) + stdlib (urllib fallback).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from typing import Any

# Optional dependency: prefer requests, fall back to urllib (stdlib only).
try:  # pragma: no cover - trivial import guard
    import requests  # type: ignore

    _HAVE_REQUESTS = True
except Exception:  # noqa: BLE001
    requests = None  # type: ignore
    _HAVE_REQUESTS = False

import urllib.error
import urllib.request

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

from _tp_paths import default_data_dir, resolve_jira_base_url

JIRA_BASE_URL = resolve_jira_base_url()
JIRA_API_V3 = f"{JIRA_BASE_URL}/rest/api/3"
MCP_JSON_PATH = os.path.expanduser("~/.cursor/mcp.json")


# ---------------------------------------------------------------------------
# Auth resolution (reuse existing creds; never invent, never print secrets)
# ---------------------------------------------------------------------------


def resolve_auth(
    email: str | None = None, token: str | None = None
) -> tuple[str, str, str]:
    """Resolve (email, token, source_label) without printing the secret.

    Precedence:
      1. Explicit args (--email / --token).
      2. Env vars JIRA_USERNAME + JIRA_API_TOKEN (existing push-tool contract).
      3. mcp.json dn-mcp-server headers (X-Email-User + X-Atlassian-Token).
    """
    if email and token:
        return email, token, "cli-args"

    env_user = os.environ.get("JIRA_USERNAME")
    env_token = os.environ.get("JIRA_API_TOKEN")
    if env_user and env_token:
        return env_user, env_token, "env:JIRA_USERNAME+JIRA_API_TOKEN"

    if os.path.isfile(MCP_JSON_PATH):
        try:
            mcp = json.load(open(MCP_JSON_PATH, encoding="utf-8"))
            headers = (
                mcp.get("mcpServers", {})
                .get("dn-mcp-server", {})
                .get("headers", {})
            )
            m_email = headers.get("X-Email-User")
            m_token = headers.get("X-Atlassian-Token")
            if m_email and m_token:
                return (
                    m_email,
                    m_token,
                    "mcp.json:dn-mcp-server(X-Email-User+X-Atlassian-Token)",
                )
        except Exception as exc:  # noqa: BLE001
            raise SystemExit(f"error: failed to read {MCP_JSON_PATH}: {exc}")

    raise SystemExit(
        "error: no Jira Cloud credentials found. Provide one of:\n"
        "  - env vars JIRA_USERNAME + JIRA_API_TOKEN, or\n"
        "  - --email <addr> --token <api_token>, or\n"
        "  - X-Email-User + X-Atlassian-Token in "
        f"{MCP_JSON_PATH} (dn-mcp-server headers).\n"
        "The token must be an Atlassian Cloud API token for "
        f"{JIRA_BASE_URL}."
    )


def _auth_header(email: str, token: str) -> str:
    cred = base64.b64encode(f"{email}:{token}".encode()).decode()
    return f"Basic {cred}"


# ---------------------------------------------------------------------------
# HTTP layer (requests if available, else urllib) - Basic auth REST v3
# ---------------------------------------------------------------------------


def _http(
    method: str,
    url: str,
    auth_header: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any] | None]:
    """Perform an HTTP request. Returns (status_code, parsed_json_or_None).

    Raises RuntimeError with the response body on a non-2xx status.
    """
    headers = {
        "Authorization": auth_header,
        "Accept": "application/json",
    }
    body_bytes: bytes | None = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    if _HAVE_REQUESTS:
        resp = requests.request(  # type: ignore[union-attr]
            method, url, headers=headers, data=body_bytes, timeout=60
        )
        status = resp.status_code
        text = resp.text
        if not (200 <= status < 300):
            raise RuntimeError(f"HTTP {status}: {text[:500]}")
        parsed: dict[str, Any] | None = None
        if text.strip():
            try:
                parsed = resp.json()
            except Exception:  # noqa: BLE001
                parsed = None
        return status, parsed

    req = urllib.request.Request(
        url, data=body_bytes, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode("utf-8")
            status = r.status
            parsed = json.loads(raw) if raw.strip() else None
            return status, parsed
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body[:500]}") from exc


# ---------------------------------------------------------------------------
# ADF node builders
# ---------------------------------------------------------------------------


def _text(s: str, em: bool = False, strong: bool = False) -> dict[str, Any]:
    node: dict[str, Any] = {"type": "text", "text": s}
    marks = []
    if em:
        marks.append({"type": "em"})
    if strong:
        marks.append({"type": "strong"})
    if marks:
        node["marks"] = marks
    return node


def _paragraph(*text_nodes: dict[str, Any]) -> dict[str, Any]:
    # A paragraph with no inline content is invalid ADF; guard with empty text.
    content = list(text_nodes) or [_text("")]
    return {"type": "paragraph", "content": content}


def _code_block(text: str, language: str = "text") -> dict[str, Any]:
    """ADF codeBlock: a single text node whose newlines render as line breaks.

    Content preserves literal characters (e.g. <vlan>) unlike the Markdown path.
    """
    # A codeBlock text node must be non-empty; substitute a space if blank.
    safe = text if text != "" else " "
    return {
        "type": "codeBlock",
        "attrs": {"language": language},
        "content": [{"type": "text", "text": safe}],
    }


def _expand(title: str, content_nodes: list[dict[str, Any]]) -> dict[str, Any]:
    # An expand node must have at least one block child.
    content = content_nodes or [_paragraph(_text(" "))]
    return {"type": "expand", "attrs": {"title": title}, "content": content}


def adf_doc(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    return {"type": "doc", "version": 1, "content": nodes}


# ---------------------------------------------------------------------------
# Core: per-device config -> ADF expand nodes
# ---------------------------------------------------------------------------


def _device_name(cfg: dict[str, Any]) -> str:
    for key in ("device", "dev", "name", "hostname"):
        val = cfg.get(key)
        if val:
            return str(val)
    return "device"


def _normalize_sections(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a list of {title, lines} sections for a per-device config.

    Accepts several shapes:
      - {"sections": [{"title": ..., "lines": [...]}, ...]}
      - {"config": "line\nline"} or {"lines": [...]} or {"text": "..."}  (raw)
    """
    sections = cfg.get("sections")
    if sections:
        norm: list[dict[str, Any]] = []
        for sec in sections:
            title = str(sec.get("title", "")).strip()
            lines = sec.get("lines")
            if lines is None:
                raw = sec.get("config") or sec.get("text") or ""
                lines = str(raw).splitlines()
            if isinstance(lines, str):
                lines = lines.splitlines()
            norm.append({"title": title, "lines": [str(x) for x in lines]})
        return norm

    raw = cfg.get("config") or cfg.get("lines") or cfg.get("text") or ""
    if isinstance(raw, str):
        raw_lines = raw.splitlines()
    else:
        raw_lines = [str(x) for x in raw]
    return [{"title": "", "lines": raw_lines}]


def build_config_adf(config_suggestions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """For each per-device config, emit ONE ADF `expand` node titled `Config: <dev>`.

    Each expand's content is, per section: a paragraph with an emphasized (em)
    label, then a codeBlock (language "text") whose text is the joined config
    lines. Sections without a title emit just the codeBlock.
    """
    nodes: list[dict[str, Any]] = []
    for cfg in config_suggestions or []:
        dev = _device_name(cfg)
        sections = _normalize_sections(cfg)
        content: list[dict[str, Any]] = []
        for sec in sections:
            title = sec.get("title", "")
            lines = sec.get("lines", [])
            if title:
                content.append(_paragraph(_text(title, em=True)))
            content.append(_code_block("\n".join(lines), language="text"))
        nodes.append(_expand(f"Config: {dev}", content))
    return nodes


def build_tc_description_adf(tc: dict[str, Any]) -> dict[str, Any]:
    """Wrap intro paragraph(s) + per-device config expand nodes into an ADF doc.

    `tc` may carry:
      - "intro" (str) or "intro_lines" (list[str]) or "description"/"summary"
      - "config_suggestions" (list) -> collapsible per-device config expands
    The collapsible config is the point; the intro is minimal.
    """
    nodes: list[dict[str, Any]] = []

    intro_lines: list[str] = []
    if tc.get("intro_lines"):
        intro_lines = [str(x) for x in tc["intro_lines"]]
    elif tc.get("intro"):
        intro_lines = str(tc["intro"]).splitlines() or [str(tc["intro"])]
    elif tc.get("description"):
        intro_lines = str(tc["description"]).splitlines()
    elif tc.get("summary"):
        intro_lines = [str(tc["summary"])]

    for line in intro_lines:
        nodes.append(_paragraph(_text(line)))

    nodes.extend(build_config_adf(tc.get("config_suggestions", [])))
    return adf_doc(nodes)


# ---------------------------------------------------------------------------
# Manifest-sourced per-TC config (per-TC-from-manifest path)
# ---------------------------------------------------------------------------

TP_DATA_ROOT = default_data_dir()

# A per-device Minimum-Configuration block as stored in a manifest TC's
# jira_wiki_body: `{expand:title=Config: <dev>} ... {expand}` (wiki markup).
_WIKI_CONFIG_EXPAND_RE = re.compile(
    r"\{expand:title=Config:\s*(?P<dev>[^}]*)\}(?P<body>.*?)\{expand\}",
    re.DOTALL,
)


def _manifest_path(epic: str) -> str:
    return os.path.join(TP_DATA_ROOT, epic.strip().upper(), "manifest.json")


def load_manifest(epic: str) -> dict[str, Any]:
    """Load an epic's /TP manifest.json (the per-TC source of truth)."""
    path = _manifest_path(epic)
    if not os.path.isfile(path):
        raise SystemExit(f"error: manifest not found for {epic}: {path}")
    return json.load(open(path, encoding="utf-8"))


def find_manifest_tc(manifest: dict[str, Any], tc_query: str) -> dict[str, Any]:
    """Resolve a TC by exact id, then unique id-substring, then unique name-substring."""
    tcs = manifest.get("test_cases", []) or []
    q = (tc_query or "").strip()
    for tc in tcs:
        if str(tc.get("id", "")) == q:
            return tc
    ql = q.lower()
    id_hits = [tc for tc in tcs if ql and ql in str(tc.get("id", "")).lower()]
    if len(id_hits) == 1:
        return id_hits[0]
    if len(id_hits) > 1:
        ids = ", ".join(str(t.get("id")) for t in id_hits[:8])
        raise SystemExit(
            f"error: --tc {tc_query!r} matched {len(id_hits)} TC ids: {ids}"
            + (" ..." if len(id_hits) > 8 else "")
        )
    name_hits = [tc for tc in tcs if ql and ql in str(tc.get("name", "")).lower()]
    if len(name_hits) == 1:
        return name_hits[0]
    raise SystemExit(
        f"error: --tc {tc_query!r} matched no TC in "
        f"{manifest.get('epic', '<epic>')} ({len(tcs)} TCs total)"
    )


def _parse_wiki_sections(block: str) -> list[dict[str, Any]]:
    """Parse one device expand body into [{title, lines}] sections.

    Section title = an emphasis line `_Label:_`; code lines = the content between
    a `{noformat}` / `{noformat}` fence. A fence with no preceding label => title "".
    """
    sections: list[dict[str, Any]] = []
    cur_title = ""
    lines = block.split("\n")
    i, n = 0, len(lines)
    while i < n:
        stripped = lines[i].strip()
        if stripped == "{noformat}":
            code: list[str] = []
            i += 1
            while i < n and lines[i].strip() != "{noformat}":
                code.append(lines[i])
                i += 1
            sections.append({"title": cur_title, "lines": code})
            cur_title = ""
            i += 1
            continue
        em = re.match(r"^_(.+?)_$", stripped)
        if em:
            cur_title = em.group(1).strip().rstrip(":").strip()
        i += 1
    return sections


def parse_wiki_config_expands(wiki_body: str) -> list[dict[str, Any]]:
    """Extract per-device config from a manifest TC's jira_wiki_body.

    Returns config_suggestions [{dev, sections:[{title, lines[]}]}] in device
    order - one entry per `{expand:title=Config: <dev>}` block.
    """
    out: list[dict[str, Any]] = []
    for m in _WIKI_CONFIG_EXPAND_RE.finditer(wiki_body or ""):
        dev = (m.group("dev") or "").strip() or "device"
        out.append({"dev": dev, "sections": _parse_wiki_sections(m.group("body"))})
    return out


def config_suggestions_from_tc(tc: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a TC's per-device config_suggestions.

    Prefers a structured `config_suggestions` field if a manifest carries one;
    otherwise parses the `{expand:title=Config: <dev>}` blocks embedded in the
    TC's jira_wiki_body (the current SW-211037 shape).
    """
    cs = tc.get("config_suggestions")
    if cs:
        return cs
    body = tc.get("jira_wiki_body") or tc.get("wiki_markup") or ""
    return parse_wiki_config_expands(body)


def build_manifest_tc_adf(tc: dict[str, Any]) -> dict[str, Any]:
    """Build an ADF doc = intro paragraph (TC id + name) + one `Config: <dev>`
    expand per device from THIS TC's config, in device order. If the TC has no
    per-device config, emit a single note paragraph (no fake expands)."""
    tc_id = str(tc.get("id", "TC")).strip() or "TC"
    name = str(tc.get("name", "")).strip()
    intro = f"{tc_id} - {name}" if name else tc_id
    nodes: list[dict[str, Any]] = [_paragraph(_text(intro, strong=True))]
    cs = config_suggestions_from_tc(tc)
    if cs:
        nodes.extend(build_config_adf(cs))
    else:
        nodes.append(
            _paragraph(
                _text("No per-device configuration is defined for this test case.")
            )
        )
    return adf_doc(nodes)


def push_tc_config_adf(
    epic: str,
    tc_query: str,
    issue_key: str,
    email: str | None = None,
    token: str | None = None,
    verify: bool = True,
) -> tuple[bool, int, list[str]]:
    """Reusable entry point for the /TP push path.

    Loads the epic manifest, resolves the TC, builds its per-device config ADF,
    and PUTs it as the issue description via REST v3. Returns
    (ok, expand_count, expand_titles). When verify=True, `ok` reflects the v3
    read (stored expand count == device count). Never prints secrets.
    """
    manifest = load_manifest(epic)
    tc = find_manifest_tc(manifest, tc_query)
    document = build_manifest_tc_adf(tc)
    expands = collect_expand_nodes(document)
    titles = [e.get("attrs", {}).get("title", "") for e in expands]
    r_email, r_token, _src = resolve_auth(email, token)
    auth_header = _auth_header(r_email, r_token)
    if not put_description_adf(issue_key, document, auth_header):
        return False, len(expands), titles
    if verify:
        ok, live_titles = verify_expand(issue_key, auth_header, expected=len(expands))
        return ok, len(expands), live_titles
    return True, len(expands), titles


# ---------------------------------------------------------------------------
# FULL Test-Case body: Jira WIKI markup -> ADF converter (build_full_tc_adf)
#
# Renders a WHOLE TC jira_wiki_body faithfully on Jira Cloud:
#   h1./h2./h3.            -> heading (level 1/2/3, clamped 1-6)
#   {noformat}...{noformat}-> codeBlock (language "text"), newlines/literals kept
#   {expand:title=T}...    -> expand node (attrs.title=T), inner recursively
#     ...{expand}             converted (per-device config codeBlocks live inside)
#   ||h||h||  +  |c|c| rows-> table (tableHeader row then tableCell rows); a
#                             malformed table degrades to paragraphs (never 400)
#   inline  *x* _x_ {{x}}  -> strong / em / code marks; bare line -> paragraph
#   "# "  line-start       -> orderedList items; "* " (not "**") -> bulletList
# Literals like <vlan>/<as>/<lo-x> are preserved verbatim (ADF text, no Markdown).
# ---------------------------------------------------------------------------

# Placeholder for pipes protected inside {{...}} / `...` spans while splitting
# table cells (a pipe inside inline code is content, not a column separator).
_PIPE_GUARD = "\x00"

_INLINE_CODE_RE = re.compile(r"\{\{(.+?)\}\}")
_INLINE_STRONG_RE = re.compile(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])")
_INLINE_EM_RE = re.compile(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])")
_HEADING_RE = re.compile(r"^h([1-6])\.\s+(.*)$")
_EXPAND_OPEN_RE = re.compile(r"^\{expand:title=(?P<title>.*)\}$")
_ORDERED_RE = re.compile(r"^#\s+(.*)$")
_BULLET_RE = re.compile(r"^\*\s+(.*)$")
# A Jira issue key referenced in prose. Linkified to a real clickable Jira issue
# via an ADF inlineCard smartlink (anchor: tp:jira-key-inlinecard) - so
# "stories SW-259571, SW-248136" / "parity with SW-172381" render as the ACTUAL
# user-story chip, not plain text. Only applied to prose runs
# (paragraphs/headings/table cells); NEVER inside a codeBlock or inline {{code}}.
# Restricted to REAL Jira project keys (SW-<digits>, the DNOS project); MUST NOT
# match route-types (RT-6/7/8), actor labels (RCVR-1), or interfaces - those are
# NOT Jira issues. Extend the prefix alternation if other real projects appear.
_SW_KEY_RE = re.compile(r"\b(SW-\d+)\b")


def _inline_card(key: str) -> dict[str, Any]:
    """COMPACT clickable Jira issue reference: the bare key as a hyperlink
    (`text` + `link` mark), e.g. a small blue `SW-172381`. Deliberately NOT an
    ADF `inlineCard` smartlink - that resolves to a big chip (key + full issue
    title + status badge) which clutters prose. A link-marked key stays smooth
    and inline while remaining one-click to the issue (anchor:
    tp:jira-key-inlinecard)."""
    url = f"{JIRA_BASE_URL.rstrip('/')}/browse/{key}"
    return {"type": "text", "text": key, "marks": [{"type": "link", "attrs": {"href": url}}]}


def _text_code(s: str) -> dict[str, Any]:
    """A text node carrying the inline `code` mark (never empty)."""
    return {"type": "text", "text": s if s else " ", "marks": [{"type": "code"}]}


def _inline_to_nodes(text: str) -> list[dict[str, Any]]:
    """Convert one span of wiki inline markup into ADF text nodes.

    Handles {{code}}, *strong*, _em_ (with word-boundary guards so underscores
    inside identifiers like EXPECTED_LIVE_VALIDATE are NOT italicised). All other
    characters - including literals like <vlan> - pass through verbatim. Never
    emits an empty text node (empty input -> a single space).
    """
    text = text or ""
    if text == "":
        return [_text(" ")]
    nodes: list[dict[str, Any]] = []

    def _emit_plain(s: str) -> None:
        if not s:
            return
        # Split each plain run on Jira issue keys; emit the key as an inlineCard
        # smartlink (the real, clickable user-story chip) and the rest as text.
        last = 0
        for mk in _SW_KEY_RE.finditer(s):
            if mk.start() > last:
                nodes.append(_text(s[last:mk.start()]))
            nodes.append(_inline_card(mk.group(1)))
            last = mk.end()
        if last < len(s):
            nodes.append(_text(s[last:]))

    pos, n = 0, len(text)
    while pos < n:
        candidates: list[tuple[int, str, Any]] = []
        for kind, rx in (
            ("code", _INLINE_CODE_RE),
            ("strong", _INLINE_STRONG_RE),
            ("em", _INLINE_EM_RE),
        ):
            m = rx.search(text, pos)
            if m:
                candidates.append((m.start(), kind, m))
        if not candidates:
            _emit_plain(text[pos:])
            break
        candidates.sort(key=lambda c: c[0])
        start, kind, m = candidates[0]
        if start > pos:
            _emit_plain(text[pos:start])
        inner = m.group(1)
        if kind == "code":
            nodes.append(_text_code(inner))
        elif kind == "strong":
            nodes.append(_text(inner, strong=True))
        else:
            nodes.append(_text(inner, em=True))
        pos = m.end()

    return nodes or [_text(" ")]


def _para(text: str) -> dict[str, Any]:
    """A paragraph whose content is the inline-converted text (never empty)."""
    return {"type": "paragraph", "content": _inline_to_nodes(text)}


def _list_node(kind: str, items: list[str]) -> dict[str, Any]:
    """Build an orderedList/bulletList; each item -> listItem>paragraph."""
    li = [{"type": "listItem", "content": [_para(it)]} for it in items if items]
    node: dict[str, Any] = {"type": kind, "content": li or [{"type": "listItem", "content": [_para(" ")]}]}
    if kind == "orderedList":
        node["attrs"] = {"order": 1}
    return node


def _protect_pipes(line: str) -> str:
    """Replace `|` characters INSIDE {{...}} and `...` spans with a guard char so
    they are not mistaken for table-cell separators when splitting."""
    def _guard(m: "re.Match[str]") -> str:
        return m.group(0).replace("|", _PIPE_GUARD)

    line = re.sub(r"\{\{.*?\}\}", _guard, line)
    line = re.sub(r"`[^`]*`", _guard, line)
    return line


def _restore_pipes(s: str) -> str:
    return s.replace(_PIPE_GUARD, "|")


def _split_header_cells(line: str) -> list[str]:
    parts = _protect_pipes(line).split("||")
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return [_restore_pipes(p).strip() for p in parts]


def _split_data_cells(line: str) -> list[str]:
    parts = _protect_pipes(line).split("|")
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return [_restore_pipes(p).strip() for p in parts]


def _normalize_cells(cells: list[str], ncol: int) -> list[str]:
    """Force a row to exactly `ncol` cells: pad short rows with empties; merge any
    overflow (rare stray pipes) back into the last cell so ADF stays valid."""
    if len(cells) < ncol:
        return cells + [""] * (ncol - len(cells))
    if len(cells) > ncol:
        return cells[: ncol - 1] + ["|".join(cells[ncol - 1:])]
    return cells


def _table_from_block(block_lines: list[str]) -> Any:
    """Build an ADF table from a run of `|`/`||` lines. Returns a table node, or
    None to signal the caller should degrade the block to paragraphs."""
    rows: list[tuple[str, list[str]]] = []
    for ln in block_lines:
        s = ln.strip()
        if s.startswith("||"):
            rows.append(("h", _split_header_cells(s)))
        else:
            rows.append(("d", _split_data_cells(s)))
    header_idx = next((i for i, (t, _) in enumerate(rows) if t == "h"), None)
    if header_idx is not None:
        ncol = len(rows[header_idx][1])
    else:
        ncol = max((len(c) for _, c in rows), default=0)
    if ncol <= 0:
        return None
    content: list[dict[str, Any]] = []
    for t, cells in rows:
        norm = _normalize_cells(cells, ncol)
        cell_type = "tableHeader" if t == "h" else "tableCell"
        cell_nodes = [
            {"type": cell_type, "attrs": {}, "content": [_para(c)]} for c in norm
        ]
        content.append({"type": "tableRow", "content": cell_nodes})
    return {
        "type": "table",
        "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
        "content": content,
    }


def _wiki_blocks(text: str) -> list[dict[str, Any]]:
    """Convert a block of Jira WIKI markup into a list of ADF block nodes.

    Recurses for {expand} inner content, so per-device config codeBlocks live
    inside their collapsible expand node.
    """
    lines = (text or "").split("\n")
    nodes: list[dict[str, Any]] = []
    i, n = 0, len(lines)
    while i < n:
        s = lines[i].strip()
        if s == "":
            i += 1
            continue

        me = _EXPAND_OPEN_RE.match(s)
        if me:
            title = me.group("title").strip()
            inner: list[str] = []
            i += 1
            while i < n and lines[i].strip() != "{expand}":
                inner.append(lines[i])
                i += 1
            i += 1  # consume the closing {expand}
            nodes.append(_expand(title, _wiki_blocks("\n".join(inner))))
            continue

        if s == "{noformat}":
            code: list[str] = []
            i += 1
            while i < n and lines[i].strip() != "{noformat}":
                code.append(lines[i])
                i += 1
            i += 1  # consume the closing {noformat}
            nodes.append(_code_block("\n".join(code), language="text"))
            continue

        mh = _HEADING_RE.match(s)
        if mh:
            level = min(int(mh.group(1)), 6)
            nodes.append(
                {
                    "type": "heading",
                    "attrs": {"level": level},
                    "content": _inline_to_nodes(mh.group(2).strip()),
                }
            )
            i += 1
            continue

        if s.startswith("|"):
            block: list[str] = []
            while i < n and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            tbl = _table_from_block(block)
            if tbl is None:
                nodes.extend(_para(bl.strip()) for bl in block)
            else:
                nodes.append(tbl)
            continue

        if _ORDERED_RE.match(s):
            items: list[str] = []
            while i < n:
                mm = _ORDERED_RE.match(lines[i].strip())
                if not mm:
                    break
                items.append(mm.group(1))
                i += 1
            nodes.append(_list_node("orderedList", items))
            continue

        if _BULLET_RE.match(s) and not s.startswith("**"):
            items = []
            while i < n:
                ss = lines[i].strip()
                mm = _BULLET_RE.match(ss)
                if not mm or ss.startswith("**"):
                    break
                items.append(mm.group(1))
                i += 1
            nodes.append(_list_node("bulletList", items))
            continue

        nodes.append(_para(s))
        i += 1
    return nodes


def validate_adf(doc: Any) -> list[str]:
    """Return a list of well-formedness problems ([] == valid ADF).

    Catches the mistakes Jira rejects with HTTP 400: wrong root, empty text
    nodes, non-list content, empty required containers, malformed marks.
    """
    errs: list[str] = []
    if not isinstance(doc, dict):
        return ["root is not a dict"]
    if doc.get("type") != "doc":
        errs.append("root type != 'doc'")
    if doc.get("version") != 1:
        errs.append("version != 1")
    if not isinstance(doc.get("content"), list):
        errs.append("root content is not a list")
        return errs
    if not doc["content"]:
        errs.append("root content is empty")

    non_empty_containers = {
        "doc", "bulletList", "orderedList", "listItem", "table",
        "tableRow", "tableCell", "tableHeader", "expand", "codeBlock",
    }

    def _walk(node: Any, path: str) -> None:
        if isinstance(node, list):
            for idx, c in enumerate(node):
                _walk(c, f"{path}[{idx}]")
            return
        if not isinstance(node, dict):
            errs.append(f"{path}: node is not a dict")
            return
        t = node.get("type")
        if not isinstance(t, str) or not t:
            errs.append(f"{path}: missing/invalid 'type'")
            return
        if t == "text":
            tx = node.get("text")
            if not isinstance(tx, str) or tx == "":
                errs.append(f"{path}: empty/invalid text node")
            marks = node.get("marks")
            if marks is not None:
                if not isinstance(marks, list):
                    errs.append(f"{path}: marks not a list")
                else:
                    for mi, mk in enumerate(marks):
                        if not isinstance(mk, dict) or not mk.get("type"):
                            errs.append(f"{path}.marks[{mi}]: bad mark")
            return
        content = node.get("content")
        if content is not None:
            if not isinstance(content, list):
                errs.append(f"{path}/{t}: content is not a list")
            else:
                if t in non_empty_containers and not content:
                    errs.append(f"{path}/{t}: empty content")
                _walk(content, f"{path}/{t}")
        elif t in non_empty_containers:
            errs.append(f"{path}/{t}: missing content")

    _walk(doc["content"], "content")
    return errs


def build_full_tc_adf(tc: dict[str, Any]) -> dict[str, Any]:
    """Convert a manifest TC's WHOLE `jira_wiki_body` into one validated ADF doc.

    Every wiki construct maps to its native ADF node (headings, tables,
    codeBlocks, and per-device `Config: <dev>` expand collapsibles). Raises
    ValueError if the produced ADF is not well-formed (so we never PUT a doc
    Jira would reject with 400).
    """
    body = tc.get("jira_wiki_body") or tc.get("wiki_markup") or ""
    nodes = _wiki_blocks(body)
    if not nodes:
        tc_id = str(tc.get("id", "TC")).strip() or "TC"
        nodes = [_para(tc_id)]
    document = adf_doc(nodes)
    errors = validate_adf(document)
    if errors:
        raise ValueError("ADF validation failed: " + "; ".join(errors[:10]))
    return document


def count_node_types(adf: Any) -> dict[str, int]:
    """Count every node `type` in an ADF tree (recursive)."""
    counts: dict[str, int] = {}

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            t = node.get("type")
            if isinstance(t, str):
                counts[t] = counts.get(t, 0) + 1
            for child in node.get("content", []) or []:
                _walk(child)
            for mk in node.get("marks", []) or []:
                _walk(mk)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(adf)
    return counts


def top_level_types(adf: Any) -> list[str]:
    """The ordered list of top-level node types under the doc `content`."""
    if not isinstance(adf, dict):
        return []
    return [
        c.get("type", "?")
        for c in adf.get("content", []) or []
        if isinstance(c, dict)
    ]


# ---------------------------------------------------------------------------
# REST v3 write / read
# ---------------------------------------------------------------------------


def put_description_adf(
    issue_key: str, adf_document: dict[str, Any], auth_header: str
) -> bool:
    """PUT /rest/api/3/issue/{key} with {"fields": {"description": <adf>}}.

    Returns True on success (Jira returns 204 No Content).
    """
    url = f"{JIRA_API_V3}/issue/{issue_key}"
    status, _ = _http(
        "PUT", url, auth_header, payload={"fields": {"description": adf_document}}
    )
    return 200 <= status < 300


def add_comment_adf(
    issue_key: str, adf_document: dict[str, Any], auth_header: str
) -> dict[str, Any] | None:
    """POST /rest/api/3/issue/{key}/comment with {"body": <adf>}. Returns the comment JSON."""
    url = f"{JIRA_API_V3}/issue/{issue_key}/comment"
    _, parsed = _http("POST", url, auth_header, payload={"body": adf_document})
    return parsed


def get_description_adf(issue_key: str, auth_header: str) -> dict[str, Any] | None:
    """GET the issue's stored description ADF (fields.description)."""
    url = f"{JIRA_API_V3}/issue/{issue_key}?fields=description"
    _, parsed = _http("GET", url, auth_header)
    if not parsed:
        return None
    return parsed.get("fields", {}).get("description")


def collect_expand_nodes(adf: Any) -> list[dict[str, Any]]:
    """Recursively collect every node with type == 'expand' from an ADF tree."""
    found: list[dict[str, Any]] = []

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "expand":
                found.append(node)
            for child in node.get("content", []) or []:
                _walk(child)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(adf)
    return found


def verify_expand(
    issue_key: str, auth_header: str, expected: int | None = None
) -> tuple[bool, list[str]]:
    """GET the issue description ADF and confirm real `expand` nodes are present.

    Returns (ok, [expand titles]). If `expected` is set, ok requires the count to match.
    """
    desc = get_description_adf(issue_key, auth_header)
    expands = collect_expand_nodes(desc)
    titles = [e.get("attrs", {}).get("title", "") for e in expands]
    ok = len(expands) > 0
    if expected is not None:
        ok = len(expands) == expected
    return ok, titles


# ---------------------------------------------------------------------------
# Demo payload (TASK 3: SW-284893 proof) - representative EVPN-IGMP config
# ---------------------------------------------------------------------------


def demo_tc() -> dict[str, Any]:
    """The SW-284893 proof payload: intro + two per-device config expands.

    Config lines are representative (proof of the collapsible), not a device push.
    <vlan> is intentionally left literal to prove ADF codeBlock preserves it.
    """
    return {
        "intro": "Collapsible per-device config - /TP ADF push proof",
        "config_suggestions": [
            {
                "device": "PE-X - #1 proxy DUT (L2 + snoop)",
                "sections": [
                    {
                        "title": "Interfaces",
                        "lines": [
                            "interfaces AC-IF-X admin-state enabled "
                            "l2-service enabled vlan-id <vlan>",
                        ],
                    },
                    {
                        "title": "BGP (l2vpn-evpn)",
                        "lines": [
                            "protocols bgp neighbor 10.0.0.2 remote-as 65000",
                            "protocols bgp neighbor 10.0.0.2 "
                            "address-family l2vpn-evpn",
                            "protocols bgp address-family l2vpn-evpn",
                        ],
                    },
                    {
                        "title": "EVPN service (IGMP snooping)",
                        "lines": [
                            "network-services evpn instance SVC-IGMP "
                            "protocols igmp-snooping admin-state enabled",
                        ],
                    },
                ],
            },
            {
                "device": "PE-Y - #2 remote peer",
                "sections": [
                    {
                        "title": "Interfaces",
                        "lines": [
                            "interfaces AC-IF-Y admin-state enabled "
                            "l2-service enabled vlan-id <vlan>",
                        ],
                    },
                    {
                        "title": "EVPN service (IGMP snooping)",
                        "lines": [
                            "network-services evpn instance SVC-IGMP "
                            "protocols igmp-snooping admin-state enabled",
                        ],
                    },
                ],
            },
        ],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _load_payload(path: str) -> dict[str, Any]:
    """Load a JSON payload: either a TC dict ({intro, config_suggestions}) or a
    bare list of config_suggestions."""
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, list):
        return {"config_suggestions": data}
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Push per-device test config as REAL collapsible Jira ADF "
        "expand nodes (REST v3).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--issue", help="Target issue key (e.g. SW-284893)")
    ap.add_argument(
        "--from-json",
        dest="from_json",
        help="Path to a JSON payload (TC dict or a list of config_suggestions)",
    )
    ap.add_argument(
        "--demo",
        action="store_true",
        help="Use the built-in SW-284893 two-device proof payload",
    )
    ap.add_argument(
        "--epic",
        help="Load per-TC config from ~/SCALER/TEST/tp/<EPIC>/manifest.json "
        "(use with --tc)",
    )
    ap.add_argument(
        "--tc",
        help="TC id or unique substring within --epic's manifest; its per-device "
        "config becomes the ADF expand collapsibles",
    )
    ap.add_argument(
        "--mode",
        choices=["description", "comment"],
        default="description",
        help="Write target: issue description (default) or a new comment",
    )
    ap.add_argument(
        "--push",
        action="store_true",
        help="Actually write to Jira. Without it, this is a dry run (print ADF).",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Force dry run: build and print ADF, never touch Jira.",
    )
    ap.add_argument(
        "--full",
        action="store_true",
        help="Render the WHOLE TC jira_wiki_body as ADF (headings + procedure "
        "table + per-device config collapsibles). Default is config-only.",
    )
    ap.add_argument(
        "--verify",
        action="store_true",
        help="After push (or standalone), GET the issue and confirm expand nodes.",
    )
    ap.add_argument("--email", help="Override Jira account email")
    ap.add_argument("--token", help="Override Jira API token (not printed)")
    args = ap.parse_args(argv)

    have_manifest_tc = bool(args.epic and args.tc)
    if bool(args.epic) ^ bool(args.tc):
        ap.error("--epic and --tc must be used together")

    # Build the ADF document (unless we are only verifying).
    build_only_verify = args.verify and not (
        args.demo or args.from_json or have_manifest_tc
    )

    document: dict[str, Any] | None = None
    if not build_only_verify:
        if have_manifest_tc:
            manifest = load_manifest(args.epic)
            tc = find_manifest_tc(manifest, args.tc)
            if args.full:
                document = build_full_tc_adf(tc)
            else:
                document = build_manifest_tc_adf(tc)
            print(f"[INFO] Manifest TC: {tc.get('id')} "
                  f"({args.epic.strip().upper()}) "
                  f"[{'full body' if args.full else 'config-only'}]")
        elif args.demo:
            payload = demo_tc()
            document = (
                build_full_tc_adf(payload)
                if args.full and payload.get("jira_wiki_body")
                else build_tc_description_adf(payload)
            )
        elif args.from_json:
            payload = _load_payload(args.from_json)
            document = (
                build_full_tc_adf(payload)
                if args.full and payload.get("jira_wiki_body")
                else build_tc_description_adf(payload)
            )
        else:
            ap.error(
                "provide --epic SW-XXXXX --tc <id>, --demo, --from-json PATH, "
                "or --verify (with --issue)"
            )
        expands = collect_expand_nodes(document)
        print(f"[INFO] Built ADF doc: {len(document['content'])} top-level nodes, "
              f"{len(expands)} expand node(s):")
        if args.full:
            counts = count_node_types(document)
            summary = ", ".join(
                f"{k}={counts[k]}"
                for k in ("heading", "table", "expand", "codeBlock",
                          "bulletList", "orderedList", "paragraph")
                if counts.get(k)
            )
            print(f"[INFO] ADF node counts: {summary}")
            print(f"[INFO] ADF well-formed: {'yes' if not validate_adf(document) else 'NO'}")
        for e in expands:
            print(f"  - expand title: {e['attrs']['title']} "
                  f"({len(e.get('content', []))} child block(s))")

    do_push = args.push and not args.dry_run

    if not do_push and not args.verify:
        if document is not None:
            print("\n[INFO] Dry run (no --push). ADF document follows:\n")
            print(json.dumps(document, ensure_ascii=False, indent=2))
        print("\n[INFO] Dry run complete. Re-run with --push to write to Jira.")
        return 0

    email, token, source = resolve_auth(args.email, args.token)
    print(f"[INFO] Auth source: {source} (secret not printed)")
    auth_header = _auth_header(email, token)

    if not args.issue:
        ap.error("--issue is required for --push / --verify")
    issue = args.issue.strip().upper()

    if do_push and document is not None:
        if args.mode == "description":
            ok = put_description_adf(issue, document, auth_header)
            print(f"[{'OK' if ok else 'ERROR'}] PUT description -> {issue} "
                  f"({JIRA_BASE_URL}/browse/{issue})")
        else:
            resp = add_comment_adf(issue, document, auth_header)
            cid = (resp or {}).get("id", "?")
            print(f"[OK] POST comment -> {issue} (comment id {cid})")

    if args.verify:
        expected = None
        if document is not None:
            expected = len(collect_expand_nodes(document))
        ok, titles = verify_expand(issue, auth_header, expected=expected)
        print(f"[{'OK' if ok else 'ERROR'}] Verify {issue}: found "
              f"{len(titles)} expand node(s) in stored description ADF"
              + (f" (expected {expected})" if expected is not None else ""))
        for t in titles:
            print(f"  - expand title: {t}")

        if args.full:
            live = get_description_adf(issue, auth_header)
            counts = count_node_types(live)
            print("[INFO] v3 read-back top-level node types: "
                  + ", ".join(top_level_types(live)))
            summary = ", ".join(
                f"{k}={counts[k]}"
                for k in ("heading", "table", "expand", "codeBlock",
                          "bulletList", "orderedList", "paragraph")
                if counts.get(k)
            )
            print(f"[INFO] v3 read-back node counts: {summary}")
            blob = json.dumps(live, ensure_ascii=False)
            for lit in ("<vlan>", "<as>"):
                present = lit in blob
                print(f"[{'OK' if present else 'WARN'}] literal {lit} "
                      f"preserved: {present}")
            if "[vlan]" in blob:
                print("[WARN] found Markdown-mangled [vlan] in stored ADF")

        if not ok:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
