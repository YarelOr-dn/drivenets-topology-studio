"""
FastAPI HTTP endpoints for the TP Agent MCP server.

These endpoints are called by the Streamlit GUI to submit requests
and poll for results. The Cursor agent consumes requests via MCP tools.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .queue_manager import QueueManager
from .epic_prefetch import fetch_epic, extract_epic_ids

app = FastAPI(title="TP Agent MCP - HTTP API", version="1.0.0")
queue = QueueManager()

TP_REFERENCE_DIR = Path.home() / ".cursor" / "tp-reference"


class GenerateRequest(BaseModel):
    epic_id: str = Field(..., description="Primary EPIC ID (e.g. SW-182545)")
    categories: List[str] = Field(default=[], description="TP checklist categories to generate (empty = all)")
    max_tasks_per_category: int = Field(default=3, description="Max tasks to generate per category")
    additional_instructions: str = Field(default="", description="Extra instructions for the agent")
    push_to_jira: bool = Field(default=False, description="Auto-push generated tasks to Jira")
    qa_owner: Optional[str] = Field(default=None, description="QA owner for Jira tasks")
    related_epic_ids: List[str] = Field(
        default_factory=list,
        description="Optional extra SW-* epics (DP/Infra/NM enablers) to merge into TP context",
    )


class StatusResponse(BaseModel):
    request_id: str
    status: str
    submitted_at: Optional[str] = None
    claimed_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    has_result: bool = False


@app.get("/health")
async def health():
    return {"status": "ok", "service": "tp-agent-mcp"}


@app.post("/generate", response_model=StatusResponse)
async def submit_generation(req: GenerateRequest):
    """Submit a TP generation request. Returns request_id for polling."""
    epic_data = None
    try:
        epic_data = await fetch_epic(req.epic_id)
    except Exception as e:
        epic_data = {"epic_id": req.epic_id, "error": str(e), "name": "", "description": ""}

    related_epics_data: Dict[str, Any] = {}
    extra_ids = [k for k in req.related_epic_ids if k and k.startswith("SW-")]
    if extra_ids:
        try:
            fetched = await asyncio.gather(
                *[fetch_epic(k) for k in extra_ids], return_exceptions=True
            )
            for kid, data in zip(extra_ids, fetched):
                if isinstance(data, Exception):
                    related_epics_data[kid] = {"epic_id": kid, "error": str(data)}
                else:
                    related_epics_data[kid] = data
        except Exception as e:
            related_epics_data["_error"] = str(e)

    checklist = _load_checklist()
    if not req.categories:
        req.categories = list(checklist.keys())

    params = {
        "epic_id": req.epic_id,
        "epic_data": epic_data,
        "related_epic_ids": req.related_epic_ids,
        "related_epics_data": related_epics_data,
        "categories": req.categories,
        "max_tasks_per_category": req.max_tasks_per_category,
        "additional_instructions": req.additional_instructions,
        "push_to_jira": req.push_to_jira,
        "qa_owner": req.qa_owner,
        "checklist_tasks": {cat: checklist.get(cat, {}).get("tasks", []) for cat in req.categories},
    }

    request_id = queue.submit_request(params)
    status = queue.get_status(request_id)
    return StatusResponse(**status)


@app.get("/status/{request_id}", response_model=StatusResponse)
async def get_status(request_id: str):
    """Poll for request status."""
    status = queue.get_status(request_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    return StatusResponse(**status)


@app.get("/result/{request_id}")
async def get_result(request_id: str):
    """Get the generated test plan result."""
    result = queue.get_result(request_id)
    if result is None:
        status = queue.get_status(request_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
        if status["status"] != "completed":
            raise HTTPException(status_code=202, detail=f"Request {status['status']}, not yet completed")
        raise HTTPException(status_code=500, detail="Result missing despite completed status")
    return result


@app.get("/checklist")
async def get_checklist():
    """Return the TP checklist (21+ categories with tasks)."""
    return _load_checklist()


@app.get("/queue")
async def list_queue():
    """List all pending requests (for monitoring)."""
    pending = queue.get_pending_requests()
    return {"pending_count": len(pending), "requests": [{"request_id": r["request_id"], "epic_id": r["params"].get("epic_id", "?"), "submitted_at": r.get("submitted_at")} for r in pending]}


@app.post("/cleanup")
async def cleanup():
    """Remove old queue entries (>72h)."""
    queue.cleanup_old()
    return {"status": "cleaned"}


def _load_checklist() -> Dict[str, Any]:
    checklist_path = TP_REFERENCE_DIR / "tp_checklist.json"
    if not checklist_path.exists():
        return {}
    try:
        return json.loads(checklist_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
