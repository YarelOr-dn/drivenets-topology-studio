"""
MCP tool definitions for the TP Agent MCP server.

These tools are exposed to the Cursor agent via MCP protocol so it can:
1. Pull pending TP generation requests
2. Get context (checklist, guidelines, topology, DNOS syntax, examples, QA gates)
3. Submit staged artifacts and final structured results
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional, Tuple

from .quality_validator import (
    summarize_coverage,
    validate_cli_syntax,
    validate_framework_rules,
    validate_structured_result,
    validate_test_plan_markdown,
)
from .queue_manager import QueueManager

TP_REFERENCE_DIR = Path.home() / ".cursor" / "tp-reference"
BUNDLED_REFERENCE_DIR = Path(__file__).resolve().parent / "bundled_reference"

queue = QueueManager()


# Make the shared feature-knowledge library importable. It lives at
# /home/dn/mcp_common/ and is shared with /debug-dnos and /TEST so all three
# command MCPs read the same grandmaster-truthproof cache.
_MCP_COMMON_PARENT = Path.home()
if str(_MCP_COMMON_PARENT) not in sys.path:
    sys.path.insert(0, str(_MCP_COMMON_PARENT))

try:
    from mcp_common import feature_knowledge as _fk  # noqa: E402
except Exception as _exc:  # pragma: no cover - defensive
    _fk = None
    _FK_IMPORT_ERROR = str(_exc)
else:
    _FK_IMPORT_ERROR = None


def _resolve_context_file(context_type: str) -> Tuple[Optional[Path], Optional[str]]:
    """Prefer ~/.cursor/tp-reference; fall back to bundled_reference."""
    mapping = CONTEXT_FILES.get(context_type)
    if not mapping:
        return None, f"Unknown context_type: {context_type}"
    name, bundled_name = mapping
    p = TP_REFERENCE_DIR / name
    if p.exists():
        return p, None
    bname = bundled_name or name
    bp = BUNDLED_REFERENCE_DIR / bname
    if bp.exists():
        return bp, None
    return None, f"Context file not found: {p} (bundled {bp} also missing)"


def get_tool_definitions() -> list[dict]:
    """Return MCP tool definitions for registration."""
    return [
        {
            "name": "tp_get_pending_requests",
            "description": "Get all pending TP generation requests from the queue. Returns list of requests with their parameters.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "tp_claim_request",
            "description": "Claim a pending request to start working on it. Sets status to in_progress.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "string",
                        "description": "The request ID to claim",
                    },
                },
                "required": ["request_id"],
            },
        },
        {
            "name": "tp_submit_stage_result",
            "description": "Write an intermediate TP artifact (epic documentation, test plan draft, self-review notes) to ~/SCALER/TEST/tp/<EPIC>/ and attach to the request.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "string"},
                    "stage": {
                        "type": "string",
                        "enum": [
                            "epic_documentation",
                            "test_plan",
                            "self_review",
                            "coverage_matrix",
                            "misc",
                        ],
                    },
                    "markdown": {
                        "type": "string",
                        "description": "Primary body (alias: content)",
                    },
                    "content": {"type": "string"},
                    "filename": {
                        "type": "string",
                        "description": "Optional file name; default <stage>.md",
                    },
                    "meta": {"type": "object"},
                },
                "required": ["request_id", "stage"],
            },
        },
        {
            "name": "tp_validate_plan",
            "description": "Run lightweight validators on markdown test plan and/or structured result JSON (TC template, schema_version>=2 fields). ALSO runs the epic-agnostic framework rules (no-internal-jargon, config-as-block, DNOS syntax shape, full service config hierarchy = route-distinguisher + import/export route-target, concise pass-criteria, enough steps, control-plane show) so every epic's plan is held to the same bar.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "markdown": {"type": "string"},
                    "result": {"type": "object"},
                    "strict": {
                        "type": "boolean",
                        "description": "If true, structured schema_version>=2 AND framework hard-fails (jargon/inline-config/vendor-syntax/suspect-CLI) must pass",
                    },
                    "design_terms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "CLI tokens taken from the epic's CLI user-stories (cli-reference). Commands matching these are classified DESIGN (not-yet-live) instead of suspect.",
                    },
                    "epic_cli_text": {
                        "type": "string",
                        "description": "Raw epic user-story / cli-reference text. DESIGN tokens are auto-derived from it - use this for a PRE-RELEASE epic whose CLI is not yet on any live build (cmd search returns nothing), so feature syntax is sourced from the epic, not the device.",
                    },
                    "scenario_inventory_path": {
                        "type": "string",
                        "description": "Optional path to scenario_inventory.json for coverage-closure check (WARN-first unless SCENARIO_COVERAGE_HARD_FAIL).",
                    },
                    "scenario_inventory": {
                        "type": "object",
                        "description": "Optional inline scenario_inventory object (alternative to scenario_inventory_path).",
                    },
                },
            },
        },
        {
            "name": "tp_validate_syntax",
            "description": "DNOS syntax-validation layer. Extracts every configure/show/clear command from the rendered plan and classifies each as ok | design | suspect. 'suspect' = matches a known other-vendor/made-up shape (Cisco/Junos forms, 'lo0.N', 'evi <n>' leaf, 'ip igmp', 'switchport', '| save file', 'address-family ... activate'). 'design' = matches a token from the epic's CLI user-stories (pass design_terms). Use BEFORE declaring a plan ready so no invented syntax ships.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "markdown": {"type": "string"},
                    "design_terms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "CLI tokens from the epic CLI user-stories that mark not-yet-live commands as DESIGN.",
                    },
                    "live_terms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: tokens confirmed LIVE via dnos-config cmd search.",
                    },
                    "epic_cli_text": {
                        "type": "string",
                        "description": "Raw epic user-story / cli-reference text; DESIGN tokens are auto-derived. Use for a PRE-RELEASE epic whose CLI is not yet on any live build.",
                    },
                },
                "required": ["markdown"],
            },
        },
        {
            "name": "tp_submit_result",
            "description": "Submit the generated test plan result for a claimed request. Prefer schema_version=2 with artifacts, quality_gate, traceability, optional test_plan_markdown.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "string", "description": "The request ID"},
                    "result": {
                        "type": "object",
                        "description": "Structured TP result (see qa_skill_pipeline + automation_mapping context)",
                    },
                    "strict": {
                        "type": "boolean",
                        "description": "If true, reject submit when schema_version>=2 validation fails",
                    },
                },
                "required": ["request_id", "result"],
            },
        },
        {
            "name": "tp_submit_error",
            "description": "Report an error for a claimed request.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "string", "description": "The request ID"},
                    "error": {"type": "string", "description": "Error description"},
                },
                "required": ["request_id", "error"],
            },
        },
        {
            "name": "tp_get_context",
            "description": "Get TP generation context files. Returns the content of a specific context file (user ~/.cursor/tp-reference overrides bundled defaults).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "context_type": {
                        "type": "string",
                        "enum": list(CONTEXT_FILES.keys()),
                        "description": "Which context file to retrieve",
                    },
                },
                "required": ["context_type"],
            },
        },
        {
            "name": "tp_get_request_status",
            "description": "Get the current status of a specific request.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "string",
                        "description": "The request ID to check",
                    },
                },
                "required": ["request_id"],
            },
        },
        {
            "name": "tp_knowledge_lookup",
            "description": (
                "Read cached expected-behavior knowledge for a DNOS feature from the shared "
                "knowledge cache (~/.cursor/knowledge_base/<feature_id>/). Same data as "
                "debug_knowledge_lookup and test_knowledge_lookup. Use this during TP generation "
                "to pull live-validated show commands, expected keywords, anti-patterns, and "
                "known bugs so the generated TP says what good behavior looks like instead of "
                "inventing it. Omit feature_id to get the cache index."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "feature_id": {
                        "type": "string",
                        "description": "Feature identifier, e.g. evpn_si_vpls_proxy_arp_ndp",
                    },
                    "slice": {
                        "type": "string",
                        "description": "Optional slice: manifest|sources|config_paths|show_commands|xraycli_paths|trace_patterns|interactions|bugs|expected_behavior_md",
                    },
                },
            },
        },
    ]


# Maps context_type -> (tp-reference filename, bundled filename if different)
CONTEXT_FILES: dict[str, tuple[str, Optional[str]]] = {
    "checklist": ("tp_checklist.json", None),
    "qa_guidelines": ("qa_guidelines.md", None),
    "topology": ("topology_reference.md", None),
    "dnos_syntax": ("dnos_syntax_rules.md", None),
    "test_examples": ("test_examples.md", None),
    "test_format": ("test_format_template.md", None),
    "taxonomy": ("taxonomy.md", "taxonomy.md"),
    "test_plan_requirements": ("test_plan_requirements.md", "test_plan_requirements_excerpt.md"),
    "qa_skill_pipeline": ("qa_skill_pipeline.md", "qa_skill_pipeline.md"),
    "quality_gate_schema": ("quality_gate_schema.json", "quality_gate_schema.json"),
    "jira_push_format": ("jira_push_format.md", "jira_push_format.md"),
    "automation_mapping": ("automation_mapping.md", "automation_mapping.md"),
    "related_epics": ("related_epics.md", "related_epics.md"),
    "epic_documentation": ("epic_documentation_template.md", "epic_documentation_template.md"),
}


def handle_tool_call(name: str, arguments: dict[str, Any]) -> Any:
    """Handle an MCP tool call and return the result."""
    if name == "tp_get_pending_requests":
        requests = queue.get_pending_requests()
        return {"pending_count": len(requests), "requests": requests}

    if name == "tp_claim_request":
        request_id = arguments["request_id"]
        claimed = queue.claim_request(request_id)
        if claimed:
            return {"status": "claimed", "request": claimed}
        return {"status": "failed", "error": "Request not found or already claimed"}

    if name == "tp_submit_stage_result":
        request_id = arguments["request_id"]
        stage = arguments["stage"]
        payload = {
            "markdown": arguments.get("markdown") or arguments.get("content") or "",
            "filename": arguments.get("filename"),
            "meta": arguments.get("meta") or {},
        }
        return queue.submit_stage(request_id, stage, payload)

    if name == "tp_validate_plan":
        md = arguments.get("markdown") or ""
        res = arguments.get("result")
        strict = bool(arguments.get("strict"))
        out: dict[str, Any] = {"markdown_ok": None, "markdown_errors": [], "result_ok": None, "result_errors": []}
        if not (isinstance(md, str) and md.strip()) and not isinstance(res, dict):
            out["ok"] = False
            out["error"] = "provide non-empty markdown and/or result object"
            return out
        if isinstance(md, str) and md.strip():
            ok, errs = validate_test_plan_markdown(md)
            out["markdown_ok"] = ok
            out["markdown_errors"] = errs
        if isinstance(res, dict):
            ok2, errs2 = validate_structured_result(res)
            out["result_ok"] = ok2
            out["result_errors"] = errs2
            if strict and not ok2:
                out["strict_failed"] = True
        # Epic-agnostic framework rules + syntax layer over the markdown.
        scenario_inv = arguments.get("scenario_inventory")
        if scenario_inv is None:
            inv_path = arguments.get("scenario_inventory_path")
            if inv_path:
                p = Path(str(inv_path)).expanduser()
                if p.is_file():
                    scenario_inv = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(md, str) and md.strip():
            fw = validate_framework_rules(
                md,
                design_terms=arguments.get("design_terms"),
                epic_cli_text=arguments.get("epic_cli_text"),
                result=res if isinstance(res, dict) else None,
                scenario_inventory=scenario_inv if isinstance(scenario_inv, dict) else None,
            )
            out["framework_findings"] = fw
            out["framework_ok"] = fw["ok"]
            if strict and not fw["ok"]:
                out["strict_failed"] = True
        parts = [out["markdown_ok"], out["result_ok"], out.get("framework_ok")]
        tested = [p for p in parts if p is not None]
        out["ok"] = all(tested) if tested else False
        if strict and (out.get("result_ok") is False or out.get("framework_ok") is False):
            out["ok"] = False
        return out

    if name == "tp_validate_syntax":
        md = arguments.get("markdown") or ""
        if not (isinstance(md, str) and md.strip()):
            return {"ok": False, "error": "provide non-empty markdown"}
        syn = validate_cli_syntax(
            md,
            live_terms=arguments.get("live_terms"),
            design_terms=arguments.get("design_terms"),
            epic_cli_text=arguments.get("epic_cli_text"),
        )
        syn["ok"] = not syn["suspect"]
        syn["action"] = "tp validate syntax"
        return syn

    if name == "tp_submit_result":
        request_id = arguments["request_id"]
        result = arguments["result"]
        if not isinstance(result, dict):
            return {"status": "failed", "error": "result must be an object"}

        req = queue.get_request(request_id)
        epic_data = (req or {}).get("params", {}).get("epic_data") or {}
        cov = summarize_coverage(epic_data, result)
        result.setdefault("traceability", {})
        if isinstance(result["traceability"], dict):
            result["traceability"]["user_story_coverage_hint"] = cov

        ok, verr = validate_structured_result(result)
        result.setdefault("quality_gate", {})
        if isinstance(result["quality_gate"], dict):
            result["quality_gate"]["validator_warnings"] = verr
            result["quality_gate"]["validator_ok"] = ok

        strict = bool(arguments.get("strict") or result.get("strict_validation"))
        if strict and not ok:
            return {"status": "failed", "error": "validation failed", "details": verr}

        if queue.submit_result(request_id, result):
            return {"status": "submitted", "validation_ok": ok, "validation_warnings": verr}
        return {"status": "failed", "error": "submit_result rejected (missing request?)"}

    if name == "tp_submit_error":
        request_id = arguments["request_id"]
        error = arguments["error"]
        ok = queue.submit_error(request_id, error)
        return {"status": "submitted" if ok else "failed"}

    if name == "tp_get_context":
        context_type = arguments["context_type"]
        path, err = _resolve_context_file(context_type)
        if err or path is None:
            return {"error": err or "missing path"}
        content = path.read_text(encoding="utf-8")
        if len(content) > 100_000:
            content = content[:100_000] + "\n\n... [TRUNCATED at 100K chars] ..."
        return {
            "context_type": context_type,
            "path": str(path),
            "content": content,
        }

    if name == "tp_get_request_status":
        request_id = arguments["request_id"]
        status = queue.get_status(request_id)
        if not status:
            return {"error": f"Request {request_id} not found"}
        return status

    if name == "tp_knowledge_lookup":
        if _fk is None:
            return {
                "ok": False,
                "action": "tp knowledge lookup",
                "errors": [f"mcp_common.feature_knowledge unavailable: {_FK_IMPORT_ERROR}"],
            }
        feature_id = arguments.get("feature_id")
        if not feature_id:
            out = _fk.list_features()
            out["action"] = "tp knowledge lookup (list)"
            return out
        out = _fk.lookup(feature_id, arguments.get("slice"))
        out["action"] = "tp knowledge lookup"
        return out

    return {"error": f"Unknown tool: {name}"}
