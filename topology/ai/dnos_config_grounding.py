"""DNOS configuration grounding -- evidence search for AI chat answers.

When the AI assistant is asked to produce DNOS configuration syntax we
must NOT let the model invent commands. This module provides backend
evidence retrieval that mirrors what Scaler GUI does (Scaler GUI calls
``config_builders`` on the backend; the AI chat needs an equivalent
authoritative source for hierarchies that the builders do not cover).

Two evidence sources are consulted, in order:

1. **Local RST search** over ``scaler/dnos_cheetah_docs/`` -- deterministic,
   fast (~4,200 files indexed by filename + path), always available on
   this host.  This is the primary source.
2. **Network Mapper ``search_cli_docs``** -- secondary signal when the
   running ``NetworkMapperClient`` MCP session is healthy.  Best-effort:
   any failure (MCP not installed, SSE down, timeout) is swallowed and
   we keep the local results.

The output is a small evidence bundle (list of snippets) with source
attribution that ``serve.py`` injects into the system prompt and echoes
back to the frontend as a ``dnos_sources`` chip card.

Public surface (used by ``serve.py``):

  - ``search_dnos_docs(query, limit=...)`` -> list[Evidence]
  - ``format_evidence_for_prompt(items)`` -> str (markdown block)
  - ``serialize_sources(items)`` -> list[dict] for the wire response
  - ``RST_ROOT`` -- absolute Path of the RST tree used (for diagnostics)

Per the multi-user doctrine: this module is **stateless** and
**read-only**, so it does not need per-user paths.  The RST tree
ships with the repo; the MCP session is owned by ``discovery_api``.
"""

from __future__ import annotations

import os
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ---------------------------------------------------------------------------
# RST tree location.
# ---------------------------------------------------------------------------
# The tree is at ``<repo>/scaler/dnos_cheetah_docs``.  This file lives at
# ``<repo>/topology/ai/dnos_config_grounding.py``, so the relative path
# is ``../../scaler/dnos_cheetah_docs``.  We resolve it once at import.
_THIS_FILE = Path(__file__).resolve()
RST_ROOT = (_THIS_FILE.parent.parent.parent / "scaler" / "dnos_cheetah_docs").resolve()


# ---------------------------------------------------------------------------
# Evidence dataclass.
# ---------------------------------------------------------------------------
@dataclass
class Evidence:
    """A single DNOS doc snippet that grounds part of a config answer."""

    source: str               # 'rst' or 'mcp'
    doc_name: str             # short label, e.g. 'evpn-vpws-fxc'
    category: str             # top-level dir, e.g. 'Network-services'
    path: str                 # relative path from RST_ROOT
    snippet: str              # 600-1200 char excerpt (truncated)
    score: float = 0.0
    matched_terms: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Lazy index over the RST tree.
# ---------------------------------------------------------------------------
# We build a single in-process index on first call: filename + path tokens
# for every .rst file.  The full file body is read on demand only for the
# top-K candidates of each query, so a typical search is O(index lookup)
# + a handful of small file reads.  Index rebuilds when the tree mtime
# changes (cheap to detect via os.stat on the root dir).
_INDEX_LOCK = threading.Lock()
_INDEX_STATE: Dict[str, Any] = {
    "built_at": 0.0,
    "root_mtime": 0.0,
    # token -> set of file_id
    "by_token": {},
    # file_id -> {path, name, category, tokens}
    "files": [],
    # original order is preserved by file_id (== list index)
}

# Words that match a lot of files but are useless as discriminators.
_STOPWORDS = frozenset({
    "the", "a", "an", "is", "of", "to", "and", "or", "for", "on", "in",
    "with", "without", "show", "configure", "config", "configuration",
    "command", "commands", "syntax", "example", "examples",
    "how", "what", "where", "when", "why", "do", "does",
    "i", "me", "my", "we", "us", "our", "you", "your",
    "give", "make", "build", "create", "generate", "write",
    "please", "need", "want", "would", "should",
    "rst",
})


def _tokenize(text: str) -> List[str]:
    """Lowercase + split on non-word characters, drop stopwords/short tokens."""
    if not text:
        return []
    # Hyphens stay (they're meaningful in DNOS hierarchy names like
    # ``evpn-vpws-fxc``); split on whitespace + most punctuation.
    parts = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-_]*", text.lower())
    out: List[str] = []
    seen = set()
    for p in parts:
        if len(p) < 2:
            continue
        if p in _STOPWORDS:
            continue
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def _category_of(rel_path: str) -> str:
    """Top-level dir under RST_ROOT, e.g. 'Network-services' or 'tracking-policy'."""
    parts = rel_path.split(os.sep)
    return parts[0] if parts else ""


def _doc_name_of(rel_path: str) -> str:
    """File stem without the .rst suffix."""
    base = os.path.basename(rel_path)
    if base.endswith(".rst"):
        base = base[: -len(".rst")]
    return base


def _build_index_locked() -> None:
    """Walk RST_ROOT and rebuild the token index.  Caller holds _INDEX_LOCK."""
    files: List[Dict[str, Any]] = []
    by_token: Dict[str, set] = {}
    if not RST_ROOT.exists():
        _INDEX_STATE["built_at"] = time.monotonic()
        _INDEX_STATE["root_mtime"] = 0.0
        _INDEX_STATE["files"] = files
        _INDEX_STATE["by_token"] = by_token
        return

    for dirpath, dirnames, filenames in os.walk(RST_ROOT):
        # Skip hidden dirs and version-control droppings.
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if not name.endswith(".rst"):
                continue
            full = os.path.join(dirpath, name)
            try:
                rel = os.path.relpath(full, RST_ROOT)
            except ValueError:
                continue
            doc_name = _doc_name_of(rel)
            category = _category_of(rel)
            # Tokens come from the doc_name and the path segments. We
            # deliberately do NOT read the body here -- that happens on
            # demand for the top candidates so index build stays cheap
            # even on a tree with 4K+ files.
            path_tokens = _tokenize(rel.replace(os.sep, " "))
            tokens = list(dict.fromkeys(path_tokens))  # dedupe, keep order
            file_id = len(files)
            files.append({
                "path": rel,
                "name": doc_name,
                "category": category,
                "tokens": tokens,
            })
            for tok in tokens:
                bucket = by_token.get(tok)
                if bucket is None:
                    bucket = set()
                    by_token[tok] = bucket
                bucket.add(file_id)

    _INDEX_STATE["built_at"] = time.monotonic()
    try:
        _INDEX_STATE["root_mtime"] = RST_ROOT.stat().st_mtime
    except OSError:
        _INDEX_STATE["root_mtime"] = 0.0
    _INDEX_STATE["files"] = files
    _INDEX_STATE["by_token"] = by_token


def _ensure_index() -> None:
    """Build the index once, or rebuild if RST_ROOT mtime changed."""
    with _INDEX_LOCK:
        if not _INDEX_STATE["files"]:
            _build_index_locked()
            return
        try:
            current_mtime = RST_ROOT.stat().st_mtime
        except OSError:
            current_mtime = 0.0
        if current_mtime and current_mtime != _INDEX_STATE["root_mtime"]:
            _build_index_locked()


# ---------------------------------------------------------------------------
# Local RST search.
# ---------------------------------------------------------------------------
def _read_snippet(rel_path: str, query_tokens: Iterable[str], max_chars: int = 1200) -> str:
    """Read the file and return a short excerpt centered on the first
    matching token, or the head of the file when nothing matches.
    """
    full = RST_ROOT / rel_path
    try:
        text = full.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if not text:
        return ""
    # Strip trailing whitespace lines so the snippet is dense.
    text = text.strip()
    lower = text.lower()
    pos = -1
    for tok in query_tokens:
        if not tok:
            continue
        i = lower.find(tok)
        if i != -1:
            pos = i
            break
    if pos < 0:
        snippet = text[:max_chars]
    else:
        # Include some leading context but bias toward the match.
        start = max(0, pos - 200)
        end = min(len(text), start + max_chars)
        snippet = text[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
    return snippet.strip()


def _score_file(file_entry: Dict[str, Any], query_tokens: List[str]) -> Tuple[float, List[str]]:
    """Score how well a file matches the query tokens.

    Heuristic: each query token that appears in the doc_name scores 3,
    in the category 1.5, in the path 1.  Tokens that match nothing add 0.
    """
    if not query_tokens:
        return 0.0, []
    name = file_entry["name"].lower()
    cat = file_entry["category"].lower()
    tokens = set(file_entry["tokens"])
    score = 0.0
    matched: List[str] = []
    for tok in query_tokens:
        hit = False
        if tok == name or tok in name.split("-"):
            score += 3.0
            hit = True
        elif tok in name:
            score += 2.0
            hit = True
        if tok == cat or tok in cat.split("-"):
            score += 1.5
            hit = True
        elif tok in tokens:
            score += 1.0
            hit = True
        if hit:
            matched.append(tok)
    # Prefer the literal hierarchy file (e.g. ``bgp.rst``) over deep
    # children when both match: shorter path = more authoritative.
    score += max(0.0, 1.5 - 0.05 * len(file_entry["tokens"]))
    # _Backlog is intentionally lower priority: those are draft
    # commands.  Do not zero them out -- some users need draft syntax.
    if "_Backlog" in file_entry["path"]:
        score *= 0.6
    return score, matched


def search_local_rst(query: str, limit: int = 6) -> List[Evidence]:
    """Search the bundled DNOS RST tree for evidence matching ``query``."""
    if not query or not query.strip():
        return []
    _ensure_index()
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []
    # Restrict candidates to files that share at least one token with
    # the query -- on a 4K-file tree this typically narrows to <200.
    candidate_ids: set = set()
    for tok in query_tokens:
        bucket = _INDEX_STATE["by_token"].get(tok)
        if bucket:
            candidate_ids.update(bucket)
    if not candidate_ids:
        return []
    files = _INDEX_STATE["files"]
    scored: List[Tuple[float, int, List[str]]] = []
    for fid in candidate_ids:
        entry = files[fid]
        score, matched = _score_file(entry, query_tokens)
        if score > 0:
            scored.append((score, fid, matched))
    if not scored:
        return []
    scored.sort(key=lambda t: (-t[0], files[t[1]]["path"]))
    out: List[Evidence] = []
    for score, fid, matched in scored[: max(1, int(limit))]:
        entry = files[fid]
        snippet = _read_snippet(entry["path"], matched or query_tokens)
        if not snippet:
            continue
        out.append(Evidence(
            source="rst",
            doc_name=entry["name"],
            category=entry["category"],
            path=entry["path"],
            snippet=snippet,
            score=round(float(score), 3),
            matched_terms=list(matched),
        ))
    return out


# ---------------------------------------------------------------------------
# Network Mapper ``search_cli_docs`` (best-effort secondary signal).
# ---------------------------------------------------------------------------
# Importing the MCP client is optional; the topology app must keep
# working without it.  We keep a single in-process flag so a missing
# dependency does not produce repeated import noise on every chat turn.
_MCP_LOCK = threading.Lock()
_MCP_STATE: Dict[str, Any] = {
    "tried_import": False,
    "client": None,
    "import_error": "",
    # Deduplicated cache of recent queries -> evidence list. Tiny TTL
    # so a follow-up "what about ipv6 of that?" turn can hit cache.
    "cache": {},   # dict[query] = (timestamp, list[Evidence])
}
_MCP_CACHE_TTL_S = 60


def _get_mcp_client():
    """Lazily build a singleton ``NetworkMapperClient``; tolerate failure."""
    with _MCP_LOCK:
        if _MCP_STATE["tried_import"]:
            return _MCP_STATE.get("client")
        _MCP_STATE["tried_import"] = True
        try:
            # Local RST search is the primary path; MCP is purely a
            # bonus.  Importing inside the function keeps cold start
            # fast on hosts where the ``mcp`` package is unavailable.
            from scaler.network_mapper_client import NetworkMapperClient  # type: ignore
            client = NetworkMapperClient()
            _MCP_STATE["client"] = client
            return client
        except Exception as exc:  # pragma: no cover -- environment dep
            _MCP_STATE["import_error"] = str(exc)
            return None


def _parse_mcp_search_result(raw: str) -> List[Evidence]:
    """Best-effort markdown -> evidence parser for ``search_cli_docs``."""
    if not raw or not isinstance(raw, str):
        return []
    out: List[Evidence] = []
    # The MCP server emits markdown-ish blocks. We don't rely on a
    # specific format: split on blank lines and look for "## " or
    # ":file:" hints to identify each result.  Whatever we don't
    # parse becomes a single fallback evidence bundle so the snippet
    # is still surfaced.
    blocks = [b.strip() for b in re.split(r"\n\s*\n", raw) if b.strip()]
    for block in blocks[:6]:
        first_line = block.splitlines()[0].strip()
        # Try to lift a doc/path hint from the first line.
        m = re.search(r"`?([A-Za-z0-9_\-/.]+\.(?:md|rst))`?", first_line)
        path_hint = m.group(1) if m else ""
        doc_name = os.path.basename(path_hint)[: -3] if path_hint else first_line[:60]
        category = path_hint.split("/")[0] if path_hint and "/" in path_hint else "mcp"
        out.append(Evidence(
            source="mcp",
            doc_name=doc_name,
            category=category,
            path=path_hint or "(network-mapper search_cli_docs)",
            snippet=block[:1200],
            score=0.0,
            matched_terms=[],
        ))
    if not out:
        # Couldn't split: keep the whole result as one snippet.
        out.append(Evidence(
            source="mcp",
            doc_name="search_cli_docs",
            category="mcp",
            path="(network-mapper search_cli_docs)",
            snippet=raw[:1200],
            score=0.0,
            matched_terms=[],
        ))
    return out


def search_mcp_cli_docs(query: str, limit: int = 4, timeout: int = 8) -> List[Evidence]:
    """Call ``NetworkMapperClient._call_tool('search_cli_docs', ...)``.

    Returns ``[]`` on any error (import / SSE / timeout). Cached for
    ``_MCP_CACHE_TTL_S`` seconds so follow-up turns reuse the result.
    """
    if not query or not query.strip():
        return []
    cache_key = query.strip().lower()
    with _MCP_LOCK:
        cached = _MCP_STATE["cache"].get(cache_key)
        if cached and (time.time() - cached[0]) < _MCP_CACHE_TTL_S:
            return list(cached[1])
    client = _get_mcp_client()
    if client is None:
        return []
    try:
        raw = client._call_tool(  # noqa: SLF001 -- existing internal API
            "search_cli_docs",
            {"query": query.strip()},
            timeout=timeout,
        )
    except Exception:
        return []
    if not isinstance(raw, str):
        try:
            raw = str(raw)
        except Exception:
            raw = ""
    items = _parse_mcp_search_result(raw)[: max(1, int(limit))]
    with _MCP_LOCK:
        _MCP_STATE["cache"][cache_key] = (time.time(), list(items))
    return items


# ---------------------------------------------------------------------------
# Public API.
# ---------------------------------------------------------------------------
def search_dnos_docs(
    query: str,
    *,
    limit: int = 6,
    use_mcp: bool = True,
    mcp_timeout: int = 8,
) -> List[Evidence]:
    """Combined search: local RST first, MCP ``search_cli_docs`` as bonus.

    De-duplicates results by ``(category, doc_name)`` so the model does
    not see two slightly different snippets for the same hierarchy.
    """
    local = search_local_rst(query, limit=limit)
    extras: List[Evidence] = []
    if use_mcp:
        extras = search_mcp_cli_docs(query, limit=max(2, limit // 2), timeout=mcp_timeout)
    seen: set = set()
    out: List[Evidence] = []
    for ev in list(local) + list(extras):
        key = (ev.category.lower(), ev.doc_name.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(ev)
        if len(out) >= limit:
            break
    return out


def format_evidence_for_prompt(items: List[Evidence]) -> str:
    """Render the evidence bundle as a markdown block for the system prompt.

    The model is told to ground its answer in this block.  Snippets are
    bracketed with citation markers (e.g. ``[1]``) so a downstream
    post-filter can recognise quoted DNOS commands.
    """
    if not items:
        return ""
    lines: List[str] = [
        "## DNOS documentation evidence (authoritative -- ground every command in this block)",
        "",
        "Use ONLY the syntax shown in these snippets.  If you cannot ground a "
        "command in this block, omit it and add a one-line explanation -- do "
        "NOT invent CLI keywords.",
        "",
    ]
    for idx, ev in enumerate(items, start=1):
        header = f"[{idx}] {ev.category}/{ev.doc_name} ({ev.source}, path: {ev.path})"
        lines.append(header)
        # Indent the snippet with two spaces so it renders as a clean
        # block without colliding with the system prompt's outer
        # markdown structure.
        for s in ev.snippet.splitlines():
            lines.append("  " + s.rstrip())
        lines.append("")
    return "\n".join(lines).strip()


def serialize_sources(items: List[Evidence]) -> List[Dict[str, Any]]:
    """Wire-format used by ``serve.py`` to echo sources back to the UI."""
    out: List[Dict[str, Any]] = []
    for ev in items:
        d = asdict(ev)
        # Trim the snippet for the wire so the response stays small.
        # Frontend renders a "Verified from DNOS docs" chip and shows
        # the full snippet only when the user expands it.
        snippet = d.get("snippet") or ""
        if len(snippet) > 600:
            snippet = snippet[:600] + "..."
        d["snippet"] = snippet
        out.append(d)
    return out


# ---------------------------------------------------------------------------
# DNOS config system prompt used by the grounded backend flow.
# ---------------------------------------------------------------------------
def build_grounded_system_prompt(evidence: List[Evidence]) -> str:
    """Render the strict system prompt used when DNOS config intent fires.

    Strategy: lock the model to "produce ONLY DNOS CLI lines" and pin
    every command to the evidence block.  We deliberately drop every
    other tool / blueprint / canvas knob from the prompt because this
    request path must NEVER mutate the canvas or persist a topology.
    """
    evidence_block = format_evidence_for_prompt(evidence)
    return (
        "## Role\n"
        "You are the DNOS configuration assistant for DriveNets Network "
        "Operating System.  Your output MUST be valid DNOS CLI syntax, "
        "grounded ONLY in the documentation block below.\n\n"
        "## Output contract\n"
        "1. Reply with DNOS CLI commands only -- no prose, no greetings, "
        "   no closing remarks. Wrap the commands in a single fenced "
        "   ```dnos block.\n"
        "2. Begin with `configure` if the snippet enters config mode.\n"
        "3. Use the exact hierarchy keywords shown in the evidence -- "
        "   never invent CLI keywords, options, or flags.\n"
        "4. When a command requires a parameter the user did not supply, "
        "   use a clearly placeholder value like `<NEIGHBOR-IP>`, "
        "   `<AS-NUMBER>`, or `<INTERFACE-NAME>`. Never guess real values.\n"
        "5. If the documentation block does NOT cover the user's request, "
        "   reply with EXACTLY this single line, with no fences and no "
        "   extra prose:\n"
        "       NO_VERIFIED_DNOS_SOURCE\n"
        "6. Do not call tools. Do not produce JSON. Do not modify the "
        "   canvas. Do not list blueprints.\n\n"
        "## Style\n"
        "- One DNOS command per line.\n"
        "- Match indentation in the evidence (DNOS hierarchy is "
        "  indentation-sensitive in `show config` output, but the "
        "  configure-mode commands are flat -- mirror what the evidence "
        "  shows).\n"
        "- End with `commit` only if the user asked for an applied "
        "  config and the evidence supports it.\n\n"
        f"{evidence_block}\n"
    )


def parse_dnos_block(text: str) -> str:
    """Extract the first ```dnos / ```cli / ```text fenced block.

    Returns the raw command body (no fences).  When no fence is present
    we still try a heuristic: lines that start with ``configure``,
    ``set``, ``no ``, or look like a DNOS prompt are treated as the
    body.  When neither matches we return ``""`` so the caller can
    surface a "no config detected" error.
    """
    if not text:
        return ""
    # Prefer an explicit dnos/cli fence.
    m = re.search(r"```(?:dnos|cli|text)?\s*\n(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if m:
        body = m.group(1).strip()
        if body:
            return body
    # No fence -- look for a contiguous run of CLI-shaped lines.
    # We require an EXPLICIT DNOS structural keyword on the first line
    # of the run; otherwise we'd false-positive on prose like
    # "just a plain explanation". Once a run has started we accept
    # indented continuations and 'exit'/'commit' as legitimate body.
    _CLI_HEADERS = (
        "configure", "set ", "no ", "commit",
        "interface ", "interfaces ", "sub-interface ", "bundle ",
        "protocols ", "protocol ", "system ", "network-services ",
        "routing-options ", "routing-policy ", "policy ",
        "forwarding-options ", "tracking-policy ", "tracking-group ",
        "segment-routing ", "mpls ", "qos ", "access-list ",
        "static ", "vrrp ", "bfd ", "ldp ", "ospf ", "isis ", "is-is ",
        "bgp ", "evpn ", "vpws ", "vpls ", "vrf ", "bridge-domain ",
        "ipsec ", "ike ", "lacp ", "pim ", "igmp ", "msdp ",
        "snmp ", "ntp ", "tacacs ", "aaa ",
    )
    cli_lines: List[str] = []
    started = False
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip().lower()
        if not stripped:
            if started:
                cli_lines.append("")
                continue
            continue
        is_header = any(stripped.startswith(h) for h in _CLI_HEADERS)
        is_continuation = (
            started
            and (
                line.startswith((" ", "\t"))
                or stripped in ("exit", "commit", "end", "top")
            )
        )
        if is_header or is_continuation:
            started = True
            cli_lines.append(line)
        elif started:
            break
    return "\n".join(cli_lines).strip()


def validate_dnos_text(config_text: str) -> Dict[str, Any]:
    """Run ``validate_generated_config`` if available; soft-fail otherwise.

    Returns a dict with ``ok`` and a list of issues for the wire.
    ``cli_validator`` is part of the Scaler package, which the topology
    process imports lazily; we mirror that pattern.
    """
    if not config_text or not config_text.strip():
        return {"ok": False, "issues": [{
            "severity": "error",
            "message": "Empty config body produced by AI grounding flow",
        }]}
    try:
        from scaler.cli_validator import validate_generated_config  # type: ignore
    except Exception as exc:
        # Validation is desirable but not fatal -- if the validator
        # cannot import (Scaler not installed in this deployment) we
        # still want to return the grounded config rather than fail
        # the entire turn.
        return {"ok": True, "issues": [], "validator_unavailable": str(exc)}
    try:
        result = validate_generated_config(
            config_text, check_limits=False, check_interface_order=False,
        )
    except Exception as exc:
        return {"ok": True, "issues": [], "validator_error": str(exc)}
    issues_out: List[Dict[str, Any]] = []
    has_error = False
    for issue in getattr(result, "issues", []) or []:
        sev = getattr(getattr(issue, "severity", None), "value", None) or str(getattr(issue, "severity", ""))
        sev_lower = sev.lower() if isinstance(sev, str) else ""
        msg = getattr(issue, "message", "") or ""
        line = getattr(issue, "line_number", None)
        hierarchy = getattr(issue, "hierarchy", None)
        issues_out.append({
            "severity": sev_lower or "info",
            "message": str(msg),
            "line": line,
            "hierarchy": hierarchy,
        })
        if sev_lower in ("error", "critical"):
            has_error = True
    return {"ok": not has_error, "issues": issues_out}


# ---------------------------------------------------------------------------
# Intent detection: is this turn asking for DNOS configuration syntax?
# ---------------------------------------------------------------------------
# Order matters: we test on the NORMALIZED user turn, then on a small set of
# discriminator phrases.  This keeps false positives low (a user asking
# "explain how BGP works" is NOT asking for config syntax even though "BGP"
# matches).  We only classify the LAST user message because earlier turns
# are conversation context, not the active intent.
_CONFIG_VERBS = (
    "configure", "config", "configs", "configuration", "configurations",
    "set up", "setup", "provision", "provisioning",
    "generate config", "generate configuration", "generate dnos",
    "give me config", "give me the config", "give me the configuration",
    "give me a config", "give me dnos",
    "show me config", "show me the config", "show me the configuration",
    "show config", "show me dnos", "show me a config",
    "build config", "build the config", "build dnos",
    "write config", "write the config", "write dnos",
    "produce config", "produce a config", "produce dnos",
    "draft config", "draft the config",
    "dnos config", "dnos configuration", "dnos commands",
    "dnos cli", "dnos syntax", "dnos snippet",
    "config snippet", "configuration snippet",
    "cli config", "cli configuration", "cli syntax",
    "config example", "configuration example",
    "config hierarchy", "configuration hierarchy",
    "command syntax", "command for", "commands for",
    "what is the syntax", "what's the syntax",
    "how do i configure", "how do you configure", "how to configure",
    "how do i set", "how do you set",
)

# DNOS hierarchy keywords that strongly suggest config intent on their own
# when paired with a verb-ish word ("show", "give", "make", "set").
_CONFIG_OBJECTS = (
    "interface", "interfaces", "sub-interface", "subinterface", "bundle",
    "bgp", "ospf", "isis", "is-is", "ldp", "rsvp", "mpls",
    "evpn", "vpws", "vpls", "vrf", "l3vpn", "l2vpn",
    "bridge-domain", "bridge", "vxlan",
    "segment-routing", "sr-mpls", "sr-policy",
    "pim", "igmp", "msdp", "mvpn",
    "qos", "policy-map", "class-map",
    "access-list", "acl",
    "route-policy", "routing-policy",
    "tracking-policy", "flowspec",
    "vrrp", "bfd", "lacp",
    "ipsec", "ike",
    "dnaas", "ncp", "ncf",
    "tacacs", "snmp", "ntp", "ssh",
    "static route", "default-route",
)

# Negative signals -- things the user clearly wants NOT to be config.
_NON_CONFIG_VERBS = (
    "explain", "what does", "what is the difference",
    "compare ", " vs ", " versus ",
    "draw", "topology", "diagram",
    "create topology", "build topology", "generate topology",
    "list blueprints", "what blueprints",
    "show on the canvas", "on the canvas",
    "add device", "add link", "add a router", "add an router",
    "remove device", "remove link", "delete device", "delete link",
    "rename", "move ", "color ",
    "troubleshoot", "debug", "why isn't", "why is", "why is the",
    "design ", "what topology", "recommend ",
)


@dataclass
class IntentResult:
    """Result of classifying a chat turn.  ``confidence`` is 0.0-1.0."""

    is_config_intent: bool
    confidence: float
    reason: str
    matched_objects: List[str] = field(default_factory=list)
    query: str = ""


def _last_user_text(messages: List[Dict[str, Any]]) -> str:
    """Return the content of the most recent user message."""
    for m in reversed(messages or []):
        if (m.get("role") or "") == "user":
            content = m.get("content") or ""
            if isinstance(content, str):
                return content.strip()
            if isinstance(content, list):
                # Anthropic-style list of {type, text} parts.
                parts = []
                for p in content:
                    if isinstance(p, dict) and p.get("type") == "text":
                        parts.append(p.get("text") or "")
                return "\n".join(parts).strip()
    return ""


def detect_config_intent(
    messages: List[Dict[str, Any]],
    *,
    canvas: Optional[Dict[str, Any]] = None,
) -> IntentResult:
    """Classify whether the latest user turn is a DNOS config request.

    The classifier is intentionally lexical (no LLM round-trip) so it
    runs in <1 ms and is auditable.  It looks at the LAST user turn
    only -- conversation history would muddy the signal because a
    chat that started with topology design might ask for config three
    turns later.
    """
    text = _last_user_text(messages)
    if not text:
        return IntentResult(False, 0.0, "no user message", query=text)
    lower = text.lower()
    # Hard veto: the most explicit "do NOT touch the canvas" signals.
    # We do NOT veto on isolated words like "topology" because a user
    # might write "give me the dnos config for this topology" -- that
    # is still a config intent. We require a verbed canvas action.
    for neg in _NON_CONFIG_VERBS:
        if neg in lower:
            # Soft veto: only trigger when no positive verb is present.
            if not any(v in lower for v in _CONFIG_VERBS):
                return IntentResult(
                    False, 0.05,
                    f"non-config intent ({neg!r})",
                    query=text,
                )
    # Positive: explicit config verb.
    matched_verb = ""
    for v in _CONFIG_VERBS:
        if v in lower:
            matched_verb = v
            break
    matched_objects: List[str] = []
    for obj in _CONFIG_OBJECTS:
        if obj in lower:
            matched_objects.append(obj)
    if matched_verb and matched_objects:
        return IntentResult(
            True, 0.95,
            f"verb={matched_verb!r} objects={matched_objects}",
            matched_objects=matched_objects,
            query=text,
        )
    if matched_verb and ("dnos" in lower or "cli" in lower or "syntax" in lower):
        return IntentResult(
            True, 0.85,
            f"verb={matched_verb!r} mentions dnos/cli/syntax",
            query=text,
        )
    # User pasted a CLI prompt and asked "fix this" / "what's wrong".
    if (
        re.search(r"\b(?:dnRouter|cfg|cfg-[a-z\-]+)\b", text)
        and any(w in lower for w in ("fix", "validate", "check", "correct", "wrong"))
    ):
        return IntentResult(
            True, 0.8,
            "looks like pasted DNOS CLI for review",
            query=text,
        )
    if matched_objects and ("snippet" in lower or "example" in lower or "syntax" in lower):
        return IntentResult(
            True, 0.7,
            f"objects={matched_objects} + snippet/example/syntax",
            matched_objects=matched_objects,
            query=text,
        )
    return IntentResult(
        False, 0.1,
        "no strong config-intent signal",
        matched_objects=matched_objects,
        query=text,
    )


def build_search_query(intent: IntentResult, fallback_text: str = "") -> str:
    """Pick the best query string for ``search_dnos_docs``.

    We prefer the matched objects (compact, hierarchy-flavoured) plus
    a couple of discriminator words from the user turn.  Falls back to
    the raw user text if no objects matched.
    """
    if intent.matched_objects:
        # Pull a few extra discriminator words from the user turn so we
        # match e.g. ``bgp neighbor address-family`` rather than just
        # ``bgp``.
        text_tokens = _tokenize(intent.query or fallback_text or "")
        extras: List[str] = []
        for tok in text_tokens:
            if len(extras) >= 4:
                break
            if tok in intent.matched_objects:
                continue
            if tok in ("config", "configuration", "configure", "configs", "dnos", "cli"):
                continue
            extras.append(tok)
        return " ".join(intent.matched_objects + extras)
    return intent.query or fallback_text or ""


# ---------------------------------------------------------------------------
# Lightweight self-test for diagnostics (`python -m topology.ai.dnos_config_grounding`).
# ---------------------------------------------------------------------------
if __name__ == "__main__":  # pragma: no cover -- manual invocation
    import sys
    q = " ".join(sys.argv[1:]) or "evpn vpws fxc interface"
    print(f"RST_ROOT = {RST_ROOT}")
    _ensure_index()
    print(f"Indexed {len(_INDEX_STATE['files'])} RST files")
    items = search_dnos_docs(q, use_mcp=False)
    print(f"Query: {q!r} -> {len(items)} hits")
    for it in items:
        print(f"  - {it.score:>5.2f} {it.category}/{it.doc_name}  (path: {it.path})")
    intent = detect_config_intent([{"role": "user", "content": q}])
    print(f"Intent: is_config={intent.is_config_intent} conf={intent.confidence} reason={intent.reason}")
