"""Catch-all stub for /api/operations/* — register LAST."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.api_route("/api/operations/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
def operations_stub(path: str):
    """Stub for operations - use scaler-wizard for full functionality."""
    raise HTTPException(
        status_code=501,
        detail="Operation not implemented in bridge. Use scaler-wizard CLI for scale up/down, mirror, multihoming sync, image upgrade."
    )
