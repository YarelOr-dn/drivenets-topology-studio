#!/usr/bin/env python3
"""
Scaler Bridge API - REST wrapper for scaler-wizard modules.

Runs on port 8766. Routers live under topology/routes/.
"""
import os
import sys
from pathlib import Path

SCALER_ROOT = Path(os.environ.get("SCALER_ROOT", str(Path.home() / "SCALER")))
if str(SCALER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCALER_ROOT))

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
except ImportError:
    print("Install fastapi and uvicorn: pip install fastapi uvicorn")
    sys.exit(1)

from routes.ssh import router as ssh_router
from routes.config import router as config_router
from routes.operations import router as operations_router
from routes.upgrade import router as upgrade_router
from routes.devices import router as devices_router
from routes.operations_stub import router as operations_stub_router

app = FastAPI(title="Scaler Bridge", version="0.2.0")


@app.on_event("startup")
def _startup_recover():
    """Recover in-flight jobs from before the last server restart."""
    try:
        from routes.upgrade import _recover_active_builds
        _recover_active_builds()
    except Exception as e:
        print(f"[STARTUP] Build recovery failed: {e}")
    try:
        from routes.upgrade import _recover_active_upgrades
        _recover_active_upgrades()
    except Exception as e:
        print(f"[STARTUP] Upgrade recovery failed: {e}")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ssh_router)
app.include_router(config_router)
app.include_router(operations_router)
app.include_router(upgrade_router)
app.include_router(devices_router)
app.include_router(operations_stub_router)


@app.get("/api/health")
def health():
    """Health check."""
    return {"status": "ok", "service": "scaler-bridge"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8766)
