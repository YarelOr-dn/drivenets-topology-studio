#!/usr/bin/env python3
"""
Split topology/scaler_bridge.py.bak_split into routes/bridge_helpers.py + routers + slim scaler_bridge.py.

Run: python3 topology/scripts/split_scaler_bridge.py
"""
from __future__ import annotations

from pathlib import Path

TOPOLOGY = Path(__file__).resolve().parent.parent
SRC = TOPOLOGY / "scaler_bridge.py.bak_split"
if not SRC.exists():
    SRC = TOPOLOGY / "scaler_bridge.py"
ROUTES = TOPOLOGY / "routes"

# Non-route helper code (no @app / @router decorators)
HELPER_RANGES = [
    (1, 722),
    (1128, 1624),  # ZOHAR + console/PDU helpers through _pdu_power_action; before discover-console route
    (1791, 2159),  # virsh + _discover_ncc_mgmt_ip_sync; before websocket route
    (3643, 3651),  # _build_job_name
    (4053, 4185),  # push history paths + helpers through _remove_active_upgrade (before _recover_*)
    (9150, 9714),  # INVENTORY + _get_device_context + _compute_wizard_suggestions
]


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def concat_ranges(lines: list[str], ranges: list[tuple[int, int]]) -> str:
    out: list[str] = []
    for a, b in ranges:
        out.append("".join(lines[a - 1 : b]))
    return "".join(out)


def main() -> None:
    lines = read_lines(SRC)

    ROUTES.mkdir(exist_ok=True)
    (ROUTES / "__init__.py").write_text('"""Scaler bridge route modules."""\n', encoding="utf-8")

    (ROUTES / "_state.py").write_text(
        '"""Mutable shared state for scaler bridge."""\n'
        "import threading\n\n"
        "_push_jobs = {}\n"
        "_push_jobs_lock = threading.Lock()\n",
        encoding="utf-8",
    )

    merged = concat_ranges(lines, HELPER_RANGES)
    merged = (
        '"""Shared helpers for scaler bridge routers (extracted from scaler_bridge)."""\n'
        "from __future__ import annotations\n\n"
        "from fastapi import HTTPException\n\n"
        "from routes._state import _push_jobs, _push_jobs_lock\n\n"
        + merged
    )
    merged = merged.replace(
        'INVENTORY_FILE = Path(__file__).resolve().parent / "device_inventory.json"',
        'INVENTORY_FILE = Path(__file__).resolve().parent.parent / "device_inventory.json"',
    )
    merged = merged.replace(
        'DEVICE_INVENTORY_JSON = Path(__file__).resolve().parent / "device_inventory.json"',
        'DEVICE_INVENTORY_JSON = Path(__file__).resolve().parent.parent / "device_inventory.json"',
    )
    (ROUTES / "bridge_helpers.py").write_text(merged, encoding="utf-8")

    def extract_router(name: str, ranges: list[tuple[int, int]], extra: str = "") -> None:
        body = concat_ranges(lines, ranges)
        body = body.replace("@app.", "@router.")
        out = [
            f'"""Scaler bridge routes: {name}."""\n',
            "from __future__ import annotations\n\n",
            "from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect\n",
            "from fastapi.responses import StreamingResponse\n\n",
            "from routes.bridge_helpers import *\n",
            "from routes._state import _push_jobs, _push_jobs_lock\n\n",
        ]
        if extra:
            out.append(extra + "\n")
        out.append("router = APIRouter()\n\n")
        out.append(body)
        if not body.endswith("\n"):
            out.append("\n")
        (ROUTES / f"{name}.py").write_text("".join(out), encoding="utf-8")

    # ssh: pool/probe/check/discover-ncc, then discover-console/console-scan/pdu, then websocket
    extract_router("ssh", [(756, 1126), (1625, 1788), (2161, 2367)])
    extract_router("config", [(2369, 3526)])
    extract_router("operations", [(3528, 3634), (3653, 4824)])
    # Upgrade routes + inner helpers, then startup recovery (needs _auto_push_upgrade in module)
    extract_router("upgrade", [(4826, 9139), (4186, 4481)])
    extract_router("devices", [(9716, 9934)])

    stub = "".join(lines[9140:9147]).replace("@app.", "@router.")
    (ROUTES / "operations_stub.py").write_text(
        '"""Catch-all stub for /api/operations/* — register LAST."""\n'
        "from __future__ import annotations\n\n"
        "from fastapi import APIRouter, HTTPException\n\n"
        "router = APIRouter()\n\n"
        + stub,
        encoding="utf-8",
    )

    slim = '''#!/usr/bin/env python3
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
'''
    (TOPOLOGY / "scaler_bridge.py").write_text(slim, encoding="utf-8")

    print("[OK] routes/* and slim scaler_bridge.py")


if __name__ == "__main__":
    main()
