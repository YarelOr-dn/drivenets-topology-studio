"""LLM client abstraction for the AI assistant.

Per-request flow:
  1. serve.py receives /api/ai/chat or /api/ai/topology/generate.
  2. It reads the user's per-user ai_config.json via user_store
     (user_ai_config_path).
  3. It calls resolve_client_for_user(username) which returns a
     concrete LlmClient (AnthropicClient or OpenAiClient).
  4. It builds the system prompt (knowledge digest + live context)
     and calls client.chat(messages, tools=...).
  5. LlmClient returns a normalized response:
         { "text": str, "tool_calls": [ {"name": str, "args": dict} ] }

No third-party SDKs: we use urllib so this module works with whatever
Python the existing serve.py runs on (the rest of serve.py is already
urllib-based, e.g. _jira_request). Timeouts are conservative (60 s for
chat, enough for a 4 KB topology generation with Claude 3.5 Sonnet).

Provider support:
  - anthropic : Claude (primary). POST /v1/messages.
  - openai    : OpenAI or any OpenAI-compatible endpoint (base_url
                override supported). POST /v1/chat/completions.
"""

from __future__ import annotations

import contextlib
import http.client
import json
import os
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


# -------------------------------------------------------------------------
# IPv4-only DNS for upstream AI calls (Groq, OpenAI, Anthropic, ...).
#
# Why: `socket.getaddrinfo` on this host returns IPv6 addresses FIRST
# for Cloudflare-fronted providers like Groq (`2606:4700:...`). Python's
# `urllib.request` dutifully tries IPv6 first, but this host's v6 path
# to Cloudflare is broken -- the TCP handshake doesn't fail, it just
# hangs for ~30 s and then returns a 0-byte body. curl doesn't see
# this because it has `happy-eyeballs` (RFC 8305) that falls back to
# v4 after ~300 ms; Python's stdlib does not.
#
# Measured impact (2026-04-21, same host, same key, same payload):
#     dual-stack urllib:  40 670 ms wall, empty body
#     IPv4-only   urllib:     211 ms wall, good body
#
# Rather than monkey-patch `socket.getaddrinfo` process-wide (would
# break any other code that legitimately wants IPv6), we scope the
# override to just the `urllib.request.urlopen` call that matters.
# The context manager swaps `socket.getaddrinfo` for the duration of
# the single POST and restores it on exit.
# -------------------------------------------------------------------------
_ORIG_GETADDRINFO = socket.getaddrinfo


def _ipv4_only_getaddrinfo(host, port, family=0, *args, **kwargs):  # type: ignore[no-untyped-def]
    return _ORIG_GETADDRINFO(host, port, socket.AF_INET, *args, **kwargs)


@contextlib.contextmanager
def _force_ipv4():
    """Temporarily force ``socket.getaddrinfo`` to return IPv4 only.

    Used around upstream AI POSTs because several providers
    (Groq/Cloudflare today; likely others in the future) have an IPv6
    path that stalls silently from this host. Not a permanent
    workaround -- if the host's v6 routing is fixed we can drop this
    wrapper without code changes elsewhere.
    """
    socket.getaddrinfo = _ipv4_only_getaddrinfo  # type: ignore[assignment]
    try:
        yield
    finally:
        socket.getaddrinfo = _ORIG_GETADDRINFO  # type: ignore[assignment]

try:
    # Preferred: canonical per-user path helper.
    from api.auth.user_store import user_store
except Exception:  # pragma: no cover -- soft for non-scaler contexts.
    user_store = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Knowledge digest (baked into every system prompt).
# ---------------------------------------------------------------------------
_KNOWLEDGE_PATH = Path(__file__).with_name("knowledge.md")
_knowledge_cache: Dict[str, Any] = {"mtime": 0.0, "text": ""}


def load_knowledge_digest() -> str:
    """Return the app knowledge digest, re-reading it on mtime change.

    Called on every turn. Cheap in the hot path (stat + in-memory
    cache); authors can hot-edit knowledge.md without a process
    restart.
    """
    try:
        mtime = _KNOWLEDGE_PATH.stat().st_mtime
    except OSError:
        return _knowledge_cache.get("text") or ""
    if mtime == _knowledge_cache.get("mtime") and _knowledge_cache.get("text"):
        return _knowledge_cache["text"]
    try:
        text = _KNOWLEDGE_PATH.read_text(encoding="utf-8")
    except OSError:
        text = ""
    _knowledge_cache["mtime"] = mtime
    _knowledge_cache["text"] = text
    return text


def reload_knowledge() -> Dict[str, Any]:
    """Force a re-read of ``knowledge.md`` bypassing the mtime cache.

    Wired to the admin menu (``Reload AI Knowledge``) via
    ``serve.py :: _handle_admin_reload_knowledge``. The normal hot path
    already notices mtime changes, but the admin action is useful when
    the file was touched without changing mtime (rare -- most editors
    preserve it on in-place writes) or when the caller wants a
    deterministic round-trip with stats.

    Returns a small status dict so the frontend can surface "reloaded
    NNN bytes" in the toast.
    """
    text = ""
    mtime = 0.0
    size = 0
    try:
        st = _KNOWLEDGE_PATH.stat()
        mtime = st.st_mtime
        size = st.st_size
    except OSError:
        pass
    try:
        text = _KNOWLEDGE_PATH.read_text(encoding="utf-8")
    except OSError:
        text = ""
    _knowledge_cache["mtime"] = mtime
    _knowledge_cache["text"] = text
    return {
        "ok": True,
        "path": str(_KNOWLEDGE_PATH),
        "mtime": mtime,
        "size": size,
        "length": len(text),
    }


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------
class LlmError(Exception):
    """Normalized error raised by every LlmClient.

    Carries an HTTP-like status_code so the HTTP router can map to a
    sensible response code (401 for bad key, 402 for quota, 503 for
    upstream timeouts, 500 otherwise).

    The optional ``kind`` string gives the frontend a stable tag to
    branch on without parsing prose. Known kinds:

    - ``"insufficient_quota"`` (OpenAI billing exhausted)
    - ``"rate_limited"``       (transient; retryable)
    - ``"api_key_rejected"``   (wrong or revoked key)
    - ``"model_not_found"``    (bad model id, often cross-provider)
    - ``"context_overflow"``   (prompt too long)
    - ``"upstream_error"``     (generic)
    - ``"timeout"``            (we timed the request out)
    - ``"unreachable"``        (DNS / network failure)

    The raw upstream body (if any) is kept on ``details`` so the UI can
    expose it behind a "Technical details" disclosure for debugging.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        kind: str = "upstream_error",
        details: str = "",
        provider: str = "",
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.kind = kind
        self.details = details
        self.provider = provider


# ---------------------------------------------------------------------------
# Upstream error classification
# ---------------------------------------------------------------------------
# Both OpenAI and Anthropic return structured JSON error bodies. Rather
# than dump the raw blob into chat, this helper extracts a stable "kind"
# plus a one-line friendly message. The frontend branches on ``kind`` to
# render a targeted card (billing banner, rate-limit hint, key-rejected
# banner, etc.) and shows the raw body only behind a "Technical details"
# disclosure.
#
# Both providers look like one of:
#
#   OpenAI   { "error": { "message": "...", "type": "...", "code": "..." } }
#   Anthropic{ "type": "error", "error": { "type": "...", "message": "..." } }
#
# We read whichever of {code, type} classifies to a known kind. Fallback
# is the raw HTTP status.
def _classify_upstream_error(status: int, body_txt: str) -> "tuple[str, str]":
    """Return (kind, friendly_one_liner) from an upstream error body.

    HTTP 429 is used by OpenAI for BOTH "your per-minute rate-limit"
    AND "you are out of credits, top up" -- which are semantically
    very different (one retries after seconds, the other needs a
    credit card). We disambiguate by looking at the typed fields
    (``code`` / ``type``) and well-known messages BEFORE falling back
    to the status code.

    Quota detection MUST use explicit signals only. Before 2026-04-21k
    we also matched ``"billing" in msg_lower`` -- which misclassified
    Groq's 429 rate-limit bodies (which contain the URL
    ``https://console.groq.com/settings/billing``) as quota-exhausted,
    confusingly scaring users into opening billing pages that weren't
    the actual problem.
    """
    # 2026-04-24k -- Gemini wraps its error body in a LIST:
    #   [{"error": {"code": 429, "message": "...", ...}}]
    # The previous code only handled `isinstance(j, dict)` and bailed
    # to an empty `parsed = {}` on a list, which meant we never read
    # Gemini's `message`, `code`, or `status` fields. Every Gemini
    # error therefore fell through to the plain "status == 429" branch
    # below and got tagged `rate_limited` -- even when the real cause
    # was a DAILY free-tier quota exhaustion ("limit: 20, model:
    # gemini-2.5-flash"), which should surface to the user as
    # `insufficient_quota` so the chat UI can show the "top up /
    # switch provider" card instead of a pointless "wait a few
    # seconds" retry loop.
    parsed: Dict[str, Any] = {}
    try:
        j = json.loads(body_txt) if body_txt else {}
        if isinstance(j, list):
            # Gemini-style list wrapper: pick the first dict item.
            for item in j:
                if isinstance(item, dict):
                    j = item
                    break
            else:
                j = {}
        if isinstance(j, dict):
            parsed = j.get("error") if isinstance(j.get("error"), dict) else j
    except ValueError:
        parsed = {}

    def _as_str(v):
        """Normalise a parsed JSON field to a lowercased string.

        Gemini returns `"code": 503` (int), OpenAI returns
        `"code": "insufficient_quota"` (str), Anthropic returns
        `"type": "overloaded_error"` (str). Before 2026-04-22 this
        helper did not exist and `(v or "").strip().lower()` crashed
        with AttributeError when `v` was an int, swallowing the real
        classification into a generic "upstream_error" 502. Coerce
        to str first so every provider's shape is handled.
        """
        if v is None:
            return ""
        try:
            return str(v).strip().lower()
        except Exception:
            return ""

    if not isinstance(parsed, dict):
        parsed = {}
    # `msg` keeps the original case because it gets surfaced verbatim
    # in the UI error card ("Provider says: ..."). `msg_lower` is the
    # lowercase companion used only for substring matching below.
    try:
        msg = str(parsed.get("message") or "").strip()
    except Exception:
        msg = ""
    code = _as_str(parsed.get("code"))
    typ  = _as_str(parsed.get("type"))
    msg_lower = msg.lower()

    # Quota / billing FIRST, but only with STRONG signals. "billing" as
    # a substring is NOT a strong signal; quota messages use explicit
    # phrasing or typed fields.
    if (
        code == "insufficient_quota"
        or "insufficient_quota" in typ
        or "exceeded your current quota" in msg_lower
        or "you have exceeded your" in msg_lower
        or "account is out of credits" in msg_lower
        or "no credits left" in msg_lower
    ):
        return (
            "insufficient_quota",
            msg or "Provider billing quota exhausted. Top up the account or switch provider.",
        )
    # Rate-limit. This catches Groq's 429 (``code: rate_limit_exceeded``,
    # message starts with "Rate limit reached...") AND every other
    # provider's 429 that isn't the rarer "out of quota" case above.
    if (
        status == 429
        or code == "rate_limit_exceeded"
        or "rate_limit" in typ
        or "rate limit" in msg_lower
    ):
        return (
            "rate_limited",
            msg or "Provider rate limit hit. Wait a few seconds and try again.",
        )
    # Bad / revoked key.
    if status == 401 or code in {"invalid_api_key", "authentication_error"} or "authentication" in typ:
        return ("api_key_rejected", msg or "API key rejected by provider.")
    # Wrong model id (often "this key doesn't have access to this model"
    # or cross-provider mistakes).
    if code in {"model_not_found", "invalid_model"} or "model" in msg.lower() and "not found" in msg.lower():
        return ("model_not_found", msg or "Model not available for this key.")
    # Context length exceeded.
    if code == "context_length_exceeded" or "context length" in msg.lower() or "too long" in msg.lower():
        return ("context_overflow", msg or "Prompt is too long for this model's context window.")
    # Cloudflare bot-management challenges. Providers like Groq sit
    # behind CF and will return 403 with an HTML error page that
    # contains `error code: 1010` (User-Agent signature blocked),
    # `error code: 1020` (managed challenge), or `ray id:`. These
    # look exactly like an auth error but they aren't -- the user's
    # key is fine, our TCP path just got bot-flagged. Classify them
    # separately so the UI can show a "transient block, retry" card
    # instead of nudging the user to re-enter a perfectly good key.
    body_lower = body_txt.lower()
    if status == 403 and (
        "cloudflare" in body_lower
        or "error code: 1010" in body_lower
        or "error code: 1020" in body_lower
        or "attention required" in body_lower
        or ("ray id" in body_lower and "access denied" in body_lower)
    ):
        return (
            "cf_bot_blocked",
            "Upstream CDN (Cloudflare) blocked our request. This is a "
            "transient bot-management challenge, not a bad key -- retry "
            "in a moment, or switch to a different provider.",
        )
    # Provider-side overload / temporary unavailability. Gemini returns
    # HTTP 503 with `"status": "UNAVAILABLE"` + `"This model is
    # currently experiencing high demand. Spikes in demand are usually
    # temporary."`; OpenAI has returned 503 with "The server is
    # overloaded or not ready yet"; Anthropic returns 529 "overloaded_error".
    # Before 2026-04-22 our classifier fell through to "upstream_error"
    # and mapped these to OUR HTTP 502, which is wrong semantically
    # (the upstream *is* up; it just throttled this one request). Treat
    # them as transient + retry-safe and let the caller map to 503 so
    # the browser / UI can surface a clean "try again" prompt rather
    # than a generic Bad Gateway.
    status_str = _as_str(parsed.get("status")).upper()
    if (
        status in (503, 529)
        or status_str in {"UNAVAILABLE", "RESOURCE_EXHAUSTED"}
        or code in {"overloaded_error", "server_overloaded", "unavailable"}
        or "overloaded" in msg_lower
        or "experiencing high demand" in msg_lower
        or "currently unavailable" in msg_lower
        or "temporarily unavailable" in msg_lower
        or "service unavailable" in msg_lower
    ):
        return (
            "upstream_overloaded",
            msg or (
                "Upstream model is temporarily overloaded. This is a "
                "provider-side spike, not your config -- wait a few "
                "seconds and retry, or switch to a different model."
            ),
        )
    return ("upstream_error", msg or f"Upstream HTTP {status}")


# ---------------------------------------------------------------------------
# Config I/O -- the actual file is owned by serve.py (legacy pattern); we
# only read it here. Keep this loader defensive so a broken / partial file
# never crashes the service.
# ---------------------------------------------------------------------------
def _read_ai_config(username: str) -> Optional[Dict[str, Any]]:
    """Read the user's AI config. Returns None if missing / malformed."""
    if not username or user_store is None:
        return None
    try:
        path = user_store.user_ai_config_path(username)
    except Exception:
        return None
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    provider = (data.get("provider") or "").strip().lower()
    if not provider:
        return None
    api_key = data.get("api_key") or ""
    if not api_key:
        # Shared-key deploys: an empty api_key + provider=gemini is a
        # valid state when the operator has exported GEMINI_API_KEY on
        # the server (resolve_client_for_user swaps it in at request
        # time). Without the env var the resolver still produces an
        # empty key which OpenAiClient will 401 on -- better than
        # silently returning None here, because the 401 triggers the
        # frontend's "paste your own key" error card instead of the
        # generic "AI assistant not configured" banner.
        if provider == "gemini" and os.environ.get("GEMINI_API_KEY", "").strip():
            return data
        return None
    return data


# OpenAI-compatible providers (Groq, Ollama, ...) -- they all speak the
# OpenAI /v1/chat/completions wire protocol so we reuse OpenAiClient and
# just swap the base_url + provider_name for logging / error cards.
#
# The model lists below are the curated defaults served when a user
# hasn't picked one explicitly. Users can still enter a custom model id
# from the UI's "Custom model..." dropdown entry; the server doesn't
# police the model string beyond passing it through.
_OPENAI_COMPAT_PROVIDERS: Dict[str, Dict[str, str]] = {
    # Google Gemini via the OpenAI-compatible endpoint
    # (https://generativelanguage.googleapis.com/v1beta/openai/).
    # Free tier has ~15 RPM on Flash models with a 1M TPM budget --
    # a completely separate quota from Groq. Kept FIRST in this map so
    # it mirrors the frontend PROVIDER_PRESETS ordering (gemini is the
    # default first-time pick). When the server operator exports
    # GEMINI_API_KEY in the process environment, resolve_client_for_user
    # below swaps in the shared key at request time for any user whose
    # config has a blank or "__server_shared__" api_key, giving the
    # whole deployment zero-setup Gemini access. Keys are "AIza..."
    # issued from https://aistudio.google.com/app/apikey.
    "gemini": {
        "base_url":     "https://generativelanguage.googleapis.com/v1beta/openai",
        # 2026-04-24t -- swapped default from "gemini-2.5-flash" to
        # "gemini-flash-latest". The latter is a Google-managed alias
        # that transparently routes to the newest flash model with
        # capacity, bypassing the per-model-per-day 20-req free-tier
        # cap that pinned users to a dead bucket for 24h. Individual
        # pinned model names still work as overrides via per-user
        # config, and the serve.py retry ladder walks both aliases
        # and pinned versions if the primary fails.
        "default_model": "gemini-flash-latest",
    },
    # https://console.groq.com/docs/models -- tool calling supported on
    # Llama 3.3, Llama 3.1, Qwen, DeepSeek-R1-distill (Apr 2026).
    "groq": {
        "base_url":     "https://api.groq.com/openai",
        # openai/gpt-oss-120b beats llama-3.3-70b-versatile on both
        # latency (~0.46s vs ~0.51s for small responses) AND tool-call
        # reliability on the create_topology schema in our bench on
        # 2026-04-21. 120B params + OpenAI's training pipeline + Groq's
        # LPU = GPT-4-class quality at sub-second latency.
        "default_model": "openai/gpt-oss-120b",
    },
    # Local-only; the runtime listens on 127.0.0.1:11434 by default.
    # Auth header is ignored by Ollama so we inject "ollama" as a dummy
    # when the user didn't paste anything into the API key field.
    "ollama": {
        "base_url":     "http://localhost:11434",
        "default_model": "qwen2.5:7b-instruct",
    },
}


def _gemini_shared_key() -> str:
    """The deploy-wide Gemini key, if the operator has exported it.

    Returns an empty string when the env var is absent or empty. Shared
    by `resolve_client_for_user` (for the forced-Gemini override) and
    by the HTTP handlers in `serve.py` (via `os.environ` directly).
    """
    return os.environ.get("GEMINI_API_KEY", "").strip()


def resolve_client_for_user(username: str) -> "LlmClient":
    """Build the appropriate LlmClient from the user's saved config.

    Raises LlmError(401) if the user has not configured a key yet, so
    the router can surface a user-facing "Set up your key" panel.

    Deploy-wide Gemini override: when the operator has exported
    GEMINI_API_KEY in the server environment, EVERY user gets a Gemini
    client regardless of what's stored in their per-user ai_config.json.
    The override is deliberately silent -- it does NOT rewrite the
    stored config, so removing the env var instantly reverts each user
    to their previous provider. The single exception is a user who has
    explicitly saved `provider=gemini` with their own personal
    `AIza...` key; in that case we respect their choice and use their
    key instead of the shared one. Rationale: the user's frustration
    ("the model is still llama by default, i want gemini always") is
    that the stored-config-wins semantics defeat the whole point of
    setting a deploy-wide Gemini key. Forcing Gemini here makes the
    shared-key env var the single source of truth for "which provider
    does this deployment use".
    """
    cfg = _read_ai_config(username)
    shared_gemini = _gemini_shared_key()

    # Forced-Gemini path: shared key is set AND the user either has no
    # config at all or has a non-Gemini config. Build a Gemini client
    # directly -- skip the per-provider dispatch below.
    if shared_gemini:
        stored_provider = ((cfg or {}).get("provider") or "").strip().lower()
        stored_api_key = ((cfg or {}).get("api_key") or "").strip()
        # Keep personal Gemini configs intact: if the user has their own
        # AIza key stored, we'd be silently downgrading them to the
        # shared quota. Only the empty / "__server_shared__" placeholder
        # falls through to the shared key here.
        user_has_personal_gemini = (
            stored_provider == "gemini"
            and stored_api_key not in ("", "__server_shared__")
        )
        if not user_has_personal_gemini:
            preset = _OPENAI_COMPAT_PROVIDERS["gemini"]
            # Let users who have an explicit Gemini config pick a
            # different Gemini model (e.g. 2.5-pro) even under the
            # forced path. When cfg is missing we fall back to the
            # preset default (gemini-2.5-flash).
            forced_model = ""
            if stored_provider == "gemini":
                forced_model = ((cfg or {}).get("model") or "").strip()
            if not forced_model:
                forced_model = preset["default_model"]
            client = OpenAiClient(
                api_key=shared_gemini,
                model=forced_model,
                base_url=preset["base_url"],
            )
            client.provider_name = "gemini"
            return client

    if not cfg:
        raise LlmError("AI assistant not configured -- set an API key first", 401)
    provider = (cfg.get("provider") or "").strip().lower()
    if provider == "anthropic":
        return AnthropicClient(
            api_key=cfg["api_key"],
            model=(cfg.get("model") or "").strip() or "claude-3-5-sonnet-latest",
            base_url=(cfg.get("base_url") or "").strip() or None,
        )
    if provider == "openai":
        return OpenAiClient(
            api_key=cfg["api_key"],
            model=(cfg.get("model") or "").strip() or "gpt-4o-mini",
            base_url=(cfg.get("base_url") or "").strip() or None,
        )
    if provider in _OPENAI_COMPAT_PROVIDERS:
        preset = _OPENAI_COMPAT_PROVIDERS[provider]
        # Ollama ignores the Authorization header entirely; we still send
        # something so the Bearer string is well-formed. A user-provided
        # base_url override wins over the preset (e.g. remote Ollama box,
        # a reverse proxy in front of Groq, etc.).
        api_key = (cfg.get("api_key") or "").strip() or ("ollama" if provider == "ollama" else "")
        # Shared-key fallback for Gemini: when the server operator exports
        # GEMINI_API_KEY in the environment, any user config whose stored
        # api_key is blank or the "__server_shared__" placeholder gets
        # the deploy-wide shared key swapped in at request time. This
        # keeps the real secret OUT of each user's ai_config.json (so
        # rotating the key is a single env change + service restart,
        # not a per-user config rewrite) and lets the GUI offer a
        # zero-setup "Use Gemini" flow for every user. If the env var
        # is absent we still strip the placeholder -- forwarding
        # "__server_shared__" as a Bearer token would produce a garbled
        # 401 from Google. An empty api_key triggers OpenAiClient's
        # clean "no credentials" 401 which the frontend renders as the
        # "paste your own AIza key" error card.
        if provider == "gemini" and api_key in ("", "__server_shared__"):
            api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        base_url = (cfg.get("base_url") or "").strip() or preset["base_url"]
        client = OpenAiClient(
            api_key=api_key,
            model=(cfg.get("model") or "").strip() or preset["default_model"],
            base_url=base_url,
        )
        # Stamp the real provider name so error cards say "Groq quota
        # exhausted" instead of "OpenAI quota exhausted".
        client.provider_name = provider
        return client
    raise LlmError(f"Unknown AI provider: {provider!r}", 400)


# ---------------------------------------------------------------------------
# LlmClient interface
# ---------------------------------------------------------------------------
class LlmClient:
    """Provider-agnostic chat interface.

    Concrete subclasses normalize the response to the shape documented
    in the module docstring. ``messages`` uses OpenAI-style roles
    (``system`` / ``user`` / ``assistant``); providers that require a
    different layout (Anthropic splits ``system``) remap internally.
    """

    provider_name = "base"

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    # --- shared helpers ---------------------------------------------------
    @staticmethod
    def _post_json(
        url: str,
        headers: Dict[str, str],
        body: Dict[str, Any],
        timeout: int,
    ) -> Dict[str, Any]:
        """POST JSON body; raise LlmError on non-2xx / timeout / bad JSON.

        We deliberately override the User-Agent because Python's default
        `Python-urllib/3.X` trips Cloudflare's Bot Management on several
        providers (observed: Groq returns HTTP 403 + `error code: 1010`
        for the same key + URL that succeeds from curl). A polite but
        identifiable UA avoids the challenge while still letting the
        provider see who's calling. We also send a modern Accept header
        so the response isn't negotiated down to text/html (Cloudflare
        challenge pages are HTML and that's what the 1010 body looks
        like).
        """
        data = json.dumps(body).encode("utf-8")
        merged_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "DriveNets-Topology-Studio/1.0 (+https://drivenets.com)",
            **headers,
        }
        req = urllib.request.Request(
            url, data=data, headers=merged_headers,
            method="POST",
        )
        try:
            # `_force_ipv4` shaves ~40 s off every upstream call on this
            # host (see the long comment near the top of this file).
            # Once the host's IPv6 routing to Cloudflare is fixed this
            # wrapper can be dropped with zero other changes.
            with _force_ipv4(), urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                try:
                    return json.loads(raw.decode("utf-8"))
                except (ValueError, UnicodeDecodeError) as exc:
                    raise LlmError(f"Upstream returned non-JSON response: {exc}", 502)
        except urllib.error.HTTPError as exc:
            body_txt = ""
            try:
                body_txt = exc.read().decode("utf-8", errors="replace")[:2000]
            except Exception:
                pass
            status = exc.code or 500
            kind, friendly = _classify_upstream_error(status, body_txt)
            # Map the common error cases so the UI can decide what to render.
            # The status_code we raise with is what the HTTP router returns
            # to the browser; the `kind` lets the chat UI pick a card
            # (billing banner, retry-with-backoff chip, etc.) and `details`
            # is the raw upstream body for a collapsible "Technical details".
            if kind == "api_key_rejected":
                raise LlmError(friendly, 401, kind=kind, details=body_txt) from exc
            if kind == "insufficient_quota":
                raise LlmError(friendly, 402, kind=kind, details=body_txt) from exc
            if kind == "rate_limited":
                raise LlmError(friendly, 429, kind=kind, details=body_txt) from exc
            if kind == "context_overflow":
                raise LlmError(friendly, 413, kind=kind, details=body_txt) from exc
            if kind == "model_not_found":
                raise LlmError(friendly, 404, kind=kind, details=body_txt) from exc
            if kind == "cf_bot_blocked":
                # 503 is the most honest mapping -- it IS transient, and
                # browsers / clients know to back off on 503.
                raise LlmError(friendly, 503, kind=kind, details=body_txt) from exc
            if kind == "upstream_overloaded":
                # Same reasoning as cf_bot_blocked: the provider is up,
                # just throttling this specific call. 503 tells the UI
                # "this is transient, retry is the right action" and
                # matches the upstream's own status so the devtools
                # Network tab doesn't lie about the situation.
                raise LlmError(friendly, 503, kind=kind, details=body_txt) from exc
            raise LlmError(friendly, 502, kind="upstream_error", details=body_txt) from exc
        except urllib.error.URLError as exc:
            raise LlmError(f"Upstream unreachable: {exc.reason}", 503, kind="unreachable") from exc
        except TimeoutError as exc:  # Python 3.10+
            raise LlmError(f"Upstream timed out after {timeout}s", 504, kind="timeout") from exc


class AnthropicClient(LlmClient):
    """Claude via the Anthropic Messages API.

    Docs: https://docs.anthropic.com/en/api/messages
    """

    provider_name = "anthropic"
    DEFAULT_BASE = "https://api.anthropic.com"
    API_VERSION = "2023-06-01"

    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or self.DEFAULT_BASE).rstrip("/")

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        system_parts: List[str] = []
        msgs: List[Dict[str, Any]] = []
        for m in messages:
            role = (m.get("role") or "").strip()
            content = m.get("content") or ""
            if role == "system":
                if isinstance(content, str) and content.strip():
                    system_parts.append(content)
            elif role in ("user", "assistant"):
                msgs.append({"role": role, "content": content})
        if not msgs:
            raise LlmError("No user / assistant messages provided", 400)

        body: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": msgs,
        }
        if system_parts:
            body["system"] = "\n\n".join(system_parts)
        if tools:
            # Anthropic tool schema: {name, description, input_schema}
            body["tools"] = [
                {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "input_schema": t.get("parameters") or t.get("input_schema") or {},
                }
                for t in tools
            ]

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION,
        }
        raw = self._post_json(f"{self.base_url}/v1/messages", headers, body, timeout)
        return self._normalize_response(raw)

    @staticmethod
    def _normalize_response(raw: Dict[str, Any]) -> Dict[str, Any]:
        text_parts: List[str] = []
        tool_calls: List[Dict[str, Any]] = []
        for block in raw.get("content", []) or []:
            btype = block.get("type")
            if btype == "text":
                txt = block.get("text") or ""
                if txt:
                    text_parts.append(txt)
            elif btype == "tool_use":
                tool_calls.append({
                    "name": block.get("name") or "",
                    "args": block.get("input") or {},
                    "id": block.get("id") or "",
                })
        usage = raw.get("usage") or {}
        return {
            "text": "".join(text_parts).strip(),
            "tool_calls": tool_calls,
            "stop_reason": raw.get("stop_reason"),
            "usage": {
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
            },
            "model": raw.get("model"),
            "provider": "anthropic",
        }


class OpenAiClient(LlmClient):
    """OpenAI (or OpenAI-compatible) chat completions.

    Works with anything that serves POST /v1/chat/completions and
    accepts Bearer auth. Pass base_url for Groq / OpenRouter /
    self-hosted. Tool call shape is the OpenAI function-tools one.
    """

    provider_name = "openai"
    DEFAULT_BASE = "https://api.openai.com"

    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or self.DEFAULT_BASE).rstrip("/")

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if tools:
            body["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": t.get("parameters") or t.get("input_schema") or {},
                    },
                }
                for t in tools
            ]
            body["tool_choice"] = "auto"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        raw = self._post_json(
            f"{self.base_url}/v1/chat/completions", headers, body, timeout,
        )
        return self._normalize_response(raw)

    @staticmethod
    def _normalize_response(raw: Dict[str, Any]) -> Dict[str, Any]:
        choices = raw.get("choices") or []
        if not choices:
            return {
                "text": "",
                "tool_calls": [],
                "stop_reason": "empty",
                "usage": raw.get("usage") or {},
                "model": raw.get("model"),
                "provider": "openai",
            }
        msg = (choices[0] or {}).get("message") or {}
        text = msg.get("content") or ""
        tool_calls: List[Dict[str, Any]] = []
        for tc in msg.get("tool_calls") or []:
            if not isinstance(tc, dict):
                continue
            fn = tc.get("function") or {}
            name = fn.get("name") or ""
            args_raw = fn.get("arguments") or "{}"
            try:
                args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
            except json.JSONDecodeError:
                # Model occasionally emits non-JSON if it aborts mid-call; keep
                # raw text so the caller can show a useful error card.
                args = {"__raw": args_raw}
            tool_calls.append({"name": name, "args": args, "id": tc.get("id") or ""})
        return {
            "text": (text or "").strip(),
            "tool_calls": tool_calls,
            "stop_reason": (choices[0] or {}).get("finish_reason"),
            "usage": raw.get("usage") or {},
            "model": raw.get("model"),
            "provider": "openai",
        }


# ---------------------------------------------------------------------------
# Convenience: default models per provider so the UI has a safe fallback.
# ---------------------------------------------------------------------------
PROVIDER_DEFAULTS: Dict[str, Dict[str, str]] = {
    # Google Gemini -- OpenAI-compatible free-tier endpoint. Kept FIRST
    # to mirror the frontend PROVIDER_PRESETS order (gemini is the
    # default first-time pick). Keys are "AIza..." prefixed (unambiguous,
    # used by _detectProviderFromKey in topology-ai.js for the
    # "mismatched key / provider" nudge).
    "gemini": {
        "model": "gemini-2.5-flash",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "key_prefix": "AIza",
    },
    "anthropic": {
        "model": "claude-3-5-sonnet-latest",
        "base_url": "https://api.anthropic.com",
        "key_prefix": "sk-ant-",
    },
    "openai": {
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com",
        "key_prefix": "sk-",
    },
    # OpenAI-compatible free options. Groq keys are "gsk_...". Ollama
    # runs locally with no real auth; we stash a placeholder "ollama"
    # when the user leaves the key blank.
    "groq": {
        "model": "llama-3.3-70b-versatile",
        "base_url": "https://api.groq.com/openai",
        "key_prefix": "gsk_",
    },
    "ollama": {
        "model": "qwen2.5:7b-instruct",
        "base_url": "http://localhost:11434",
        "key_prefix": "",
    },
}


def default_model_for(provider: str) -> str:
    return PROVIDER_DEFAULTS.get(provider, {}).get("model", "")


def now_unix() -> int:
    return int(time.time())
