"""
Queue manager for TP Agent MCP -- file-based request/result queue.

Handles async communication between the Streamlit GUI (producer) and
the Cursor agent (consumer) through a shared filesystem queue.

Supports staged artifact writes (epic documentation, test plan, self-review)
and rich manifests for /TEST import and Jira traceability.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

QUEUE_DIR = Path.home() / "SCALER" / "TEST" / "tp" / ".queue"
TP_OUTPUT_DIR = Path.home() / "SCALER" / "TEST" / "tp"


def _atomic_write_json(path: Path, obj: Any) -> None:
    """Atomic write (tempfile -> fsync -> os.replace) for TP artifacts, per
    atomic-file-writes discipline (these files are large + shared across /TP-/TEST)."""
    body = json.dumps(obj, indent=2)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as f:
            f.write(body)
            f.flush()
            os.fsync(f.fileno())
        try:
            os.chmod(tmp, os.stat(path).st_mode & 0o777)
        except FileNotFoundError:
            os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise

_ALLOWED_STAGES = frozenset(
    {"epic_documentation", "test_plan", "self_review", "coverage_matrix", "misc"}
)


class QueueManager:

    def __init__(self):
        QUEUE_DIR.mkdir(parents=True, exist_ok=True)

    def submit_request(self, params: Dict[str, Any]) -> str:
        """Submit a TP generation request from the GUI. Returns request_id."""
        request_id = f"tp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        request = {
            "request_id": request_id,
            "status": "pending",
            "submitted_at": datetime.now().isoformat(),
            "params": params,
            "result": None,
            "error": None,
            "stages": {},
        }
        self._write_request(request_id, request)
        return request_id

    def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Get all pending requests (for the Cursor agent to pull)."""
        requests = []
        for f in sorted(QUEUE_DIR.glob("tp_*.json")):
            try:
                data = json.loads(f.read_text())
                if data.get("status") == "pending":
                    requests.append(data)
            except (json.JSONDecodeError, OSError):
                continue
        return requests

    def claim_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Mark a request as in_progress (claimed by the agent). Returns the request or None."""
        request = self._read_request(request_id)
        if not request or request.get("status") != "pending":
            return None
        request["status"] = "in_progress"
        request["claimed_at"] = datetime.now().isoformat()
        self._write_request(request_id, request)
        return request

    def submit_stage(
        self, request_id: str, stage: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Persist intermediate markdown or JSON for a claimed (or pending) request.

        payload keys:
          - markdown | content: text body
          - filename: optional file name under ~/SCALER/TEST/tp/<EPIC>/
          - meta: optional dict stored alongside
        """
        if stage not in _ALLOWED_STAGES:
            return {"ok": False, "error": f"invalid stage: {stage}"}

        request = self._read_request(request_id)
        if not request:
            return {"ok": False, "error": "request not found"}
        if request.get("status") not in ("pending", "in_progress"):
            return {"ok": False, "error": "request not in pending/in_progress state"}

        epic_id = request.get("params", {}).get("epic_id", "unknown")
        out_dir = TP_OUTPUT_DIR / epic_id
        out_dir.mkdir(parents=True, exist_ok=True)

        body = payload.get("markdown") or payload.get("content") or ""
        if not isinstance(body, str):
            body = json.dumps(body, indent=2)

        fname = payload.get("filename") or f"{stage}.md"
        fname = os.path.basename(str(fname).replace("..", "_"))
        path = out_dir / fname
        path.write_text(body, encoding="utf-8")

        stages = request.setdefault("stages", {})
        stages[stage] = {
            "path": str(path),
            "bytes": len(body.encode("utf-8")),
            "updated_at": datetime.now().isoformat(),
            "meta": payload.get("meta") or {},
        }
        if request.get("status") == "pending":
            request["status"] = "in_progress"
            request["claimed_at"] = request.get("claimed_at") or datetime.now().isoformat()
        self._write_request(request_id, request)
        return {"ok": True, "path": str(path), "stage": stage}

    def submit_result(self, request_id: str, result: Dict[str, Any]) -> bool:
        """Submit a completed result for a request."""
        request = self._read_request(request_id)
        if not request:
            return False
        if request.get("status") not in ("pending", "in_progress"):
            return False
        request["status"] = "completed"
        request["completed_at"] = datetime.now().isoformat()
        request["result"] = result
        self._write_request(request_id, request)

        epic_id = request.get("params", {}).get("epic_id", "unknown")
        output_dir = TP_OUTPUT_DIR / epic_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write large markdown bodies as sidecar files to keep queue JSON smaller
        if isinstance(result.get("test_plan_markdown"), str):
            tpath = output_dir / f"test_plan_{epic_id}.md"
            tpath.write_text(result["test_plan_markdown"], encoding="utf-8")
            result.setdefault("artifacts", {})
            result["artifacts"]["test_plan_md"] = str(tpath)

        if isinstance(result.get("epic_documentation_markdown"), str):
            epath = output_dir / f"epic_documentation_{epic_id}.md"
            epath.write_text(result["epic_documentation_markdown"], encoding="utf-8")
            result.setdefault("artifacts", {})
            result["artifacts"]["epic_documentation_md"] = str(epath)

        # Rich, runnable-grade manifest (Phase F): carry the test_cases (with their
        # jira keys + /TEST import hints) and tp_rules so the queue-based /TP path
        # produces a manifest that passes _tp_parity_gate and that /TEST can import
        # to faithful recipes directly -- no separate _apply_* enrichment step.
        test_cases = result.get("test_cases") or []
        manifest = {
            "schema_version": result.get("schema_version", 2),
            "request_id": request_id,
            "epic_id": epic_id,
            "generated_at": datetime.now().isoformat(),
            "categories": result.get("categories", {}),
            "test_count": result.get("test_count", len(test_cases)),
            "test_cases": test_cases,
            "tp_rules": result.get("tp_rules"),
            "stages": request.get("stages", {}),
            "artifacts": result.get("artifacts", {}),
            "quality_gate": result.get("quality_gate"),
            "linked_epics": result.get("linked_epics"),
            "traceability": result.get("traceability"),
            "jira_push": result.get("jira_push"),
        }
        _atomic_write_json(output_dir / "manifest.json", manifest)
        _atomic_write_json(output_dir / "full_result.json", result)
        return True

    def submit_error(self, request_id: str, error: str) -> bool:
        """Mark a request as failed."""
        request = self._read_request(request_id)
        if not request:
            return False
        request["status"] = "error"
        request["error"] = error
        request["failed_at"] = datetime.now().isoformat()
        self._write_request(request_id, request)
        return True

    def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Return the full queue record (for agents validating before submit)."""
        return self._read_request(request_id)

    def get_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a request."""
        request = self._read_request(request_id)
        if not request:
            return None
        return {
            "request_id": request_id,
            "status": request["status"],
            "submitted_at": request.get("submitted_at"),
            "claimed_at": request.get("claimed_at"),
            "completed_at": request.get("completed_at"),
            "error": request.get("error"),
            "has_result": request.get("result") is not None,
            "stages": list((request.get("stages") or {}).keys()),
        }

    def get_result(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get the full result of a completed request."""
        request = self._read_request(request_id)
        if not request or request.get("status") != "completed":
            return None
        return request.get("result")

    def cleanup_old(self, max_age_hours: int = 72):
        """Remove requests older than max_age_hours."""
        cutoff = time.time() - (max_age_hours * 3600)
        for f in QUEUE_DIR.glob("tp_*.json"):
            if f.stat().st_mtime < cutoff:
                f.unlink(missing_ok=True)

    def _request_path(self, request_id: str) -> Path:
        return QUEUE_DIR / f"{request_id}.json"

    def _read_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        path = self._request_path(request_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def _write_request(self, request_id: str, data: Dict[str, Any]):
        path = self._request_path(request_id)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
