"""Unified Jira/Confluence client with REST / plugin / dn-mcp backends."""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from typing import Any

from mcp_common.profiles.tp.tp_env import (
    load_tp_config,
    resolve_confluence_base_url,
    resolve_jira_base_url,
    resolve_jira_credentials,
    resolve_jira_mode,
)


class JiraClientError(RuntimeError):
    pass


def _rest_request(
    method: str,
    url: str,
    *,
    email: str,
    token: str,
    body: dict[str, Any] | None = None,
) -> Any:
    data = None
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Basic "
        + base64.b64encode(f"{email}:{token}".encode()).decode(),
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise JiraClientError(f"HTTP {exc.code} {method} {url}: {detail}") from exc


class RestJiraBackend:
    name = "rest"

    def __init__(self) -> None:
        creds = resolve_jira_credentials()
        self.base_url = creds["base_url"].rstrip("/")
        self.email = creds["user_email"]
        self.token = creds["api_token"]
        self.confluence_base = resolve_confluence_base_url().rstrip("/")

    def available(self) -> bool:
        return bool(self.email and self.token and self.base_url)

    def get_issue(self, key: str, fields: list[str] | None = None) -> dict[str, Any]:
        field_q = ""
        if fields:
            field_q = "?fields=" + ",".join(fields)
        return _rest_request(
            "GET",
            f"{self.base_url}/rest/api/3/issue/{key}{field_q}",
            email=self.email,
            token=self.token,
        )

    def search_jql(self, jql: str, *, max_results: int = 100, fields: list[str] | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"jql": jql, "maxResults": max_results}
        if fields:
            body["fields"] = fields
        return _rest_request(
            "POST",
            f"{self.base_url}/rest/api/3/search",
            email=self.email,
            token=self.token,
            body=body,
        )

    def get_confluence_page(self, page_id: str) -> dict[str, Any]:
        url = f"{self.confluence_base}/rest/api/content/{page_id}?expand=body.storage,version"
        return _rest_request("GET", url, email=self.email, token=self.token)

    def create_issue(self, fields: dict[str, Any]) -> dict[str, Any]:
        return _rest_request(
            "POST",
            f"{self.base_url}/rest/api/3/issue",
            email=self.email,
            token=self.token,
            body={"fields": fields},
        )

    def update_issue(self, key: str, fields: dict[str, Any]) -> dict[str, Any]:
        return _rest_request(
            "PUT",
            f"{self.base_url}/rest/api/3/issue/{key}",
            email=self.email,
            token=self.token,
            body={"fields": fields},
        )

    def add_comment(self, key: str, body_adf: dict[str, Any]) -> dict[str, Any]:
        return _rest_request(
            "POST",
            f"{self.base_url}/rest/api/3/issue/{key}/comment",
            email=self.email,
            token=self.token,
            body={"body": body_adf},
        )


class PluginJiraBackend:
    """Placeholder for Cursor Atlassian plugin - used when agent calls MCP directly."""

    name = "plugin"

    def available(self) -> bool:
        return os.environ.get("TP_JIRA_PLUGIN_AVAILABLE", "").lower() in ("1", "true", "yes")

    def get_issue(self, key: str, fields: list[str] | None = None) -> dict[str, Any]:
        raise JiraClientError("plugin backend requires Cursor MCP; use REST in CLI mode")

    def search_jql(self, jql: str, *, max_results: int = 100, fields: list[str] | None = None) -> dict[str, Any]:
        raise JiraClientError("plugin backend requires Cursor MCP; use REST in CLI mode")

    def get_confluence_page(self, page_id: str) -> dict[str, Any]:
        raise JiraClientError("plugin backend requires Cursor MCP; use REST in CLI mode")

    def create_issue(self, fields: dict[str, Any]) -> dict[str, Any]:
        raise JiraClientError("plugin backend requires Cursor MCP; use REST in CLI mode")

    def update_issue(self, key: str, fields: dict[str, Any]) -> dict[str, Any]:
        raise JiraClientError("plugin backend requires Cursor MCP; use REST in CLI mode")

    def add_comment(self, key: str, body_adf: dict[str, Any]) -> dict[str, Any]:
        raise JiraClientError("plugin backend requires Cursor MCP; use REST in CLI mode")


class DnMcpJiraBackend:
    """Remote dn-mcp-server - probe reachability only in CLI; actual calls via MCP in agent."""

    name = "dn-mcp"

    def __init__(self) -> None:
        cfg = load_tp_config()
        self.url = str(cfg.get("dn_mcp_url") or os.environ.get("DN_MCP_URL") or "http://ai-server:8000/mcp")

    def available(self) -> bool:
        try:
            req = urllib.request.Request(self.url, method="GET")
            with urllib.request.urlopen(req, timeout=3):
                return True
        except Exception:
            return False

    def get_issue(self, key: str, fields: list[str] | None = None) -> dict[str, Any]:
        raise JiraClientError("dn-mcp backend requires MCP agent; use REST in CLI mode")

    def search_jql(self, jql: str, *, max_results: int = 100, fields: list[str] | None = None) -> dict[str, Any]:
        raise JiraClientError("dn-mcp backend requires MCP agent; use REST in CLI mode")

    def get_confluence_page(self, page_id: str) -> dict[str, Any]:
        raise JiraClientError("dn-mcp backend requires MCP agent; use REST in CLI mode")

    def create_issue(self, fields: dict[str, Any]) -> dict[str, Any]:
        raise JiraClientError("dn-mcp backend requires MCP agent; use REST in CLI mode")

    def update_issue(self, key: str, fields: dict[str, Any]) -> dict[str, Any]:
        raise JiraClientError("dn-mcp backend requires MCP agent; use REST in CLI mode")

    def add_comment(self, key: str, body_adf: dict[str, Any]) -> dict[str, Any]:
        raise JiraClientError("dn-mcp backend requires MCP agent; use REST in CLI mode")


_BACKENDS = {
    "rest": RestJiraBackend,
    "plugin": PluginJiraBackend,
    "dn-mcp": DnMcpJiraBackend,
}


def resolve_backend(mode: str | None = None):
    mode = (mode or resolve_jira_mode()).lower()
    order = ["rest", "plugin", "dn-mcp"] if mode == "auto" else [mode]
    for name in order:
        cls = _BACKENDS.get(name)
        if not cls:
            continue
        backend = cls()
        if backend.available():
            return backend
    return RestJiraBackend()


def doctor_backends() -> list[dict[str, Any]]:
    out = []
    for name, cls in _BACKENDS.items():
        b = cls()
        out.append({"name": name, "available": b.available()})
    return out
