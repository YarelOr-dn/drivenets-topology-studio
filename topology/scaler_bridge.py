#!/usr/bin/env python3
"""
Scaler Bridge API - REST wrapper for scaler-wizard modules.

Runs on port 8766. Routers live under topology/routes/.
"""
import os
import sys
import urllib.parse
from pathlib import Path

SCALER_ROOT = Path(os.environ.get("SCALER_ROOT", str(Path.home() / "SCALER")))
if str(SCALER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCALER_ROOT))

try:
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
except ImportError:
    print("Install fastapi and uvicorn: pip install fastapi uvicorn")
    sys.exit(1)

from routes.ssh import router as ssh_router
from routes.config import router as config_router
from routes.operations import router as operations_router
from routes.upgrade import router as upgrade_router
from routes.devices import router as devices_router
from routes.operations_stub import router as operations_stub_router
from routes.events import router as events_router
from routes.topology_generator import router as topology_generator_router
from routes.link_telemetry import router as link_telemetry_router
# Auto-monitor reference-counted device registry (Phase 2 MVP).
# See topology/docs/AUTO_MONITOR_ON_ATTACH.md for the full design.
from routes.monitored_devices import router as monitored_devices_router

try:
    from api.auth.router import router as auth_router
    from api.domains.router import router as domains_router
    from routes.integration_cursor import router as integration_cursor_router
    from mcp.server import create_mcp_app
    _multiuser_available = True
except ImportError as _e:
    _multiuser_available = False
    print(f"[STARTUP] Multi-user module not loaded: {_e}")

app = FastAPI(title="Scaler Bridge", version="0.2.0")


def _mcp_oauth_metadata_response(request: Request) -> JSONResponse:
    """JSON response for MCP clients that probe OAuth resource metadata.

    Topology MCP auth is still static per-user bearer-token auth. This endpoint
    exists so Cursor's MCP client receives machine-readable metadata instead of
    a framework HTML 404 during discovery.
    """
    base = str(request.base_url).rstrip("/")
    return JSONResponse({
        "resource": f"{base}/mcp",
        "resource_name": "DriveNets Topology MCP",
        "authorization_servers": [],
        "bearer_methods_supported": ["header"],
        "scopes_supported": [],
    })


@app.get("/.well-known/oauth-protected-resource")
@app.get("/.well-known/oauth-protected-resource/{rest:path}")
@app.get("/mcp/.well-known/oauth-protected-resource")
@app.get("/mcp/.well-known/oauth-protected-resource/{rest:path}")
async def mcp_oauth_metadata(request: Request):
    return _mcp_oauth_metadata_response(request)


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
    # Unified device-mode resolver: layered monitoring so the cached
    # mode is always within seconds of reality regardless of who is
    # looking. Three pollers run as daemon threads:
    #   * in-flight  (45 s)  - devices currently upgrading/deploying
    #   * watcher    (15 s)  - devices with at least one active watcher
    #   * global     (300 s) - every device with operational.json,
    #                          safety net for lab-side mode flips
    # All three are idempotent and survive restart via this hook.
    try:
        from routes._device_mode_resolver import start_all_pollers
        start_all_pollers()
        print("[STARTUP] Device-mode pollers running: inflight+watcher+global")
    except Exception as e:
        print(f"[STARTUP] Device-mode pollers failed to start: {e}")


@app.on_event("startup")
def _start_dryrun_reaper():
    """Wave 7.1: start the background reaper that releases abandoned
    dry-run push sessions. Safe to call multiple times (idempotent).
    """
    try:
        from routes._reaper import start_reaper
        start_reaper()
    except Exception as e:
        print(f"[STARTUP] Dry-run reaper failed to start: {e}")


@app.on_event("shutdown")
def _stop_dryrun_reaper():
    try:
        from routes._reaper import stop_reaper
        stop_reaper(timeout=3.0)
    except Exception:
        pass


@app.on_event("shutdown")
def _stop_devmode_pollers():
    try:
        from routes._device_mode_resolver import stop_all_pollers
        stop_all_pollers(timeout=3.0)
    except Exception:
        pass


@app.on_event("startup")
async def _capture_event_loop_for_bus():
    """Let the device EventBus schedule broadcasts from sync endpoints.

    Sync FastAPI handlers run in a threadpool where ``get_running_loop``
    raises RuntimeError. Capturing the main loop during startup means
    ``event_bus.publish_to_device_watchers_sync`` from those handlers
    can still hop onto the loop via ``run_coroutine_threadsafe``.
    """
    try:
        import asyncio
        from api.event_bus import event_bus
        event_bus.attach_loop(asyncio.get_running_loop())
    except Exception as e:
        print(f"[STARTUP] Event bus loop capture failed: {e}")


@app.on_event("startup")
async def _attach_event_bus_backend():
    """Install the cross-process backend (default: in-process no-op).

    Wave 5.1: ``TP_EVENT_BUS_BACKEND=redis`` with ``TP_REDIS_URL`` set
    enables Redis pub/sub so events published on one uvicorn worker
    fan out to WebSocket clients attached to peer workers. Errors
    during start degrade to in-process so the server still boots.
    """
    try:
        from api.event_bus import event_bus
        from api.event_bus_backend import select_backend
        backend = select_backend()
        await event_bus.attach_backend(backend)
        print(f"[STARTUP] Event bus backend: {event_bus.backend_kind()}")
    except Exception as e:
        print(f"[STARTUP] Event bus backend attach failed: {e}")


@app.on_event("shutdown")
async def _shutdown_event_bus_backend():
    try:
        from api.event_bus import event_bus
        await event_bus.shutdown_backend()
    except Exception:
        pass


@app.on_event("startup")
async def _start_knowledge_poller():
    """Background poller that keeps live-status knowledge rows (branches,
    Jira EPICs, test-suite RUN_* results, Spirent sessions) fresh without
    every user having to click refresh manually.

    Runs one asyncio task per enabled kind. ``KNOWLEDGE_POLLER_KINDS=none``
    disables it entirely (useful for tests and offline development where
    we don't want Jenkins HTTP calls at all).
    """
    try:
        from api.domains.knowledge_poller import poller
        await poller.start()
    except Exception as e:
        print(f"[STARTUP] Knowledge poller failed to start: {e}")


@app.on_event("shutdown")
async def _stop_knowledge_poller():
    try:
        from api.domains.knowledge_poller import poller
        await poller.stop()
    except Exception:
        pass


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_AUTH_EXEMPT_PATHS = frozenset({
    "/api/health",
    "/api/auth/login",
    "/api/auth/register",
})
_AUTH_EXEMPT_PREFIXES = (
    "/api/auth/",
    # Wave 4.2: /api/health/concurrency (and any future health sub-paths)
    # return operational counts only -- safe to expose for monitoring.
    "/api/health/",
)


class JwtAuthMiddleware:
    """Validate JWT on every /api/ request except auth endpoints and health.

    Accepts the token from two sources (in priority order):
      1. ``Authorization: Bearer <jwt>`` header -- used by all fetch/XHR
         calls via the global interceptor in topology-auth.js.
      2. ``?token=<jwt>`` query parameter -- required by
         EventSource/SSE (and historically WebSocket) clients that
         cannot attach custom headers. Without this fallback the
         browser's EventSource gets 401 before ever reaching the route
         handler, which then stalls the upgrade/push progress UI and
         makes Cancel look broken because the cancellation event never
         reaches the client.

    Plain ASGI middleware is required here. FastAPI's function middleware is
    implemented with Starlette BaseHTTPMiddleware, which is unsafe around the
    mounted MCP SSE app and can crash uvicorn with "Unexpected http.response.start".
    """

    def __init__(self, inner_app):
        self.app = inner_app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if scope.get("method") == "OPTIONS":
            await self.app(scope, receive, send)
            return
        if path.startswith("/.well-known/oauth-protected-resource") or path.startswith("/mcp/.well-known/oauth-protected-resource"):
            await self.app(scope, receive, send)
            return
        if path == "/mcp" or path.startswith("/mcp/"):
            # The MCP mount has its own auth middleware that accepts both normal
            # app JWTs and per-user Cursor MCP tokens. Do not pre-filter here with
            # the bridge JWT-only decoder, or Cursor-issued tokens can never bind.
            await self.app(scope, receive, send)
            return
        if path.startswith("/api/integration/cursor/"):
            # Cursor install endpoints also accept Cursor MCP tokens for skill
            # downloads and verification. The route dependency performs the
            # mixed JWT/Cursor-token validation.
            await self.app(scope, receive, send)
            return
        if path in _AUTH_EXEMPT_PATHS or any(path.startswith(p) for p in _AUTH_EXEMPT_PREFIXES):
            await self.app(scope, receive, send)
            return

        state = scope.setdefault("state", {})
        if not _multiuser_available:
            state["user"] = "default"
            state["role"] = "admin"
            try:
                from routes.bridge_helpers import current_app_user
                marker = current_app_user.set("default")
                try:
                    await self.app(scope, receive, send)
                    return
                finally:
                    try:
                        current_app_user.reset(marker)
                    except Exception:
                        pass
            except Exception:
                await self.app(scope, receive, send)
                return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        auth_header = headers.get("authorization", "")
        jwt_token = ""
        if auth_header.startswith("Bearer "):
            jwt_token = auth_header[7:]
        else:
            query = scope.get("query_string", b"").decode("latin-1", "replace")
            jwt_token = (urllib.parse.parse_qs(query).get("token") or [""])[0]
        if not jwt_token:
            response = JSONResponse(status_code=401, content={"detail": "Authentication required"})
            await response(scope, receive, send)
            return
        try:
            from api.auth.service import decode_token
            payload = decode_token(jwt_token)
        except Exception:
            payload = None
        if not payload:
            response = JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})
            await response(scope, receive, send)
            return
        state["user"] = payload.get("sub", "unknown")
        state["role"] = payload.get("role", "viewer")

        # Propagate username to the per-request ContextVar so legacy
        # _get_credentials() / _user_xray_dir() lookups become per-user.
        try:
            from routes.bridge_helpers import current_app_user
            marker = current_app_user.set(state["user"] or "")
            try:
                await self.app(scope, receive, send)
                return
            finally:
                try:
                    current_app_user.reset(marker)
                except Exception:
                    pass
        except Exception:
            await self.app(scope, receive, send)


app.add_middleware(JwtAuthMiddleware)


if _multiuser_available:
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
    app.include_router(domains_router, prefix="/api/domains", tags=["Domains"])
    app.include_router(integration_cursor_router)
    app.mount("/mcp", create_mcp_app())

app.include_router(ssh_router)
app.include_router(config_router)
app.include_router(operations_router)
app.include_router(upgrade_router)
app.include_router(devices_router)
app.include_router(operations_stub_router)
app.include_router(events_router)
app.include_router(topology_generator_router)
app.include_router(link_telemetry_router)
app.include_router(monitored_devices_router)


@app.get("/api/health")
def health():
    """Health check with multi-user status."""
    result = {"status": "ok", "service": "scaler-bridge", "multiuser": _multiuser_available}
    if _multiuser_available:
        try:
            from api.auth.user_store import user_store
            users = user_store.list_users()
            result["users_total"] = len(users)
        except Exception:
            result["users_total"] = -1
    return result


@app.get("/api/health/concurrency")
def health_concurrency():
    """Wave 4.2: concurrency observability snapshot.

    Aggregates live state from every concurrency primitive introduced in
    Waves 2-4 so an operator can see at a glance:

    - Which devices are currently locked (and by whom)
    - Whether the global upgrade slot cap is saturated
    - Live-coalescer cache hit rate and in-flight count
    - Event bus queue depth per WebSocket subscriber
    - Push/upgrade job counts by status

    All fields are safe to expose -- we intentionally avoid returning
    credentials or raw command output.
    """
    import time as _time

    snapshot = {
        "service": "scaler-bridge",
        "status": "ok",
        "captured_at": _time.time(),
    }

    try:
        from routes._device_scheduler import scheduler as _scheduler
        snapshot["scheduler"] = _scheduler.snapshot()
    except Exception as exc:
        snapshot["scheduler"] = {"error": str(exc)}

    try:
        from routes._live_coalescer import coalescer as _coalescer
        snapshot["live_coalescer"] = _coalescer.snapshot()
    except Exception as exc:
        snapshot["live_coalescer"] = {"error": str(exc)}

    try:
        from api.event_bus import event_bus as _event_bus
        snapshot["event_bus"] = _event_bus.stats()
    except Exception as exc:
        snapshot["event_bus"] = {"error": str(exc)}

    try:
        # Wave 5.2: prefer the JobStore facade so the snapshot reports
        # the same counts regardless of backend (in-memory dict or
        # future file-snapshot / Redis variants).
        from routes._state import job_store as _job_store
        js_stats = _job_store.stats()
        snapshot["jobs"] = {
            "total": js_stats.get("count", 0),
            "active": js_stats.get("active", 0),
            "by_status": js_stats.get("by_status", {}),
            "by_type": js_stats.get("by_type", {}),
            "backend": js_stats.get("kind", "unknown"),
        }
    except Exception as exc:
        snapshot["jobs"] = {"error": str(exc)}

    # Wave 6.2: worker pool (bounded push/upgrade executors).
    try:
        from routes._worker_pool import pool_stats as _pool_stats
        snapshot["worker_pools"] = _pool_stats()
    except Exception as exc:
        snapshot["worker_pools"] = {"error": str(exc)}

    # Wave 6.3: SSH connection pool capacity + fill.
    try:
        from routes.bridge_helpers import _ssh_pool
        snapshot["ssh_pool"] = _ssh_pool.health_stats()
    except Exception as exc:
        snapshot["ssh_pool"] = {"error": str(exc)}

    # Wave 7.1: dry-run abandonment reaper stats.
    try:
        from routes._reaper import reaper_stats as _reaper_stats
        snapshot["reaper"] = _reaper_stats()
    except Exception as exc:
        snapshot["reaper"] = {"error": str(exc)}

    # Wave 7.5: audit log stats.
    try:
        from routes._audit_log import audit_stats as _audit_stats
        snapshot["audit"] = _audit_stats()
    except Exception as exc:
        snapshot["audit"] = {"error": str(exc)}

    return snapshot


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8766)
