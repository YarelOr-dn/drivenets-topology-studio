"""
Network Studio API - FastAPI Backend

This application serves as the backend for the unified Network Studio,
combining Topology Creator with SCALER functionality.

Replaces the simple serve.py with a full-featured API server.
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Import route modules
from api.routes import devices, config, operations, dnaas
from api.websocket_manager import manager

# Project paths
PROJECT_ROOT = Path("/home/dn/CURSOR")
STATIC_DIR = PROJECT_ROOT


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print("🚀 Network Studio API starting...")
    print(f"   Static files: {STATIC_DIR}")
    print(f"   API docs: http://localhost:8080/docs")
    yield
    print("👋 Network Studio API shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Network Studio API",
    description="Unified API for Topology Creator and SCALER",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Routes
# ============================================================================

# Include route modules
app.include_router(devices.router, prefix="/api/devices", tags=["Devices"])
app.include_router(config.router, prefix="/api/config", tags=["Configuration"])
app.include_router(operations.router, prefix="/api/operations", tags=["Operations"])
app.include_router(dnaas.router, prefix="/api/dnaas", tags=["DNAAS Discovery"])


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@app.websocket("/ws/progress/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time operation progress."""
    await manager.connect(job_id, websocket)
    try:
        while True:
            # Keep connection alive, receive any client messages
            data = await websocket.receive_text()
            # Echo back for ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(job_id, websocket)


# ============================================================================
# Health Check
# ============================================================================

@app.get("/api/health", tags=["Health"])
async def health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "service": "Network Studio API",
        "version": "1.0.0"
    }


# ============================================================================
# Device Inventory (for DNAAS Discovery)
# ============================================================================

@app.get("/api/device/inventory", tags=["Devices"])
async def get_device_inventory():
    """
    Get device inventory for DNAAS discovery.
    
    Returns a mapping of device serials to hostnames/IPs.
    This is used by the UI to resolve device names to serial numbers.
    """
    import json
    
    inventory_file = PROJECT_ROOT / "device_inventory.json"
    
    if inventory_file.exists():
        try:
            with open(inventory_file, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            return {"devices": {}, "error": str(e)}
    
    # Return empty inventory if file doesn't exist
    return {"devices": {}}


# ============================================================================
# iTerm SSH Connection
# ============================================================================

from pydantic import BaseModel as PydanticBaseModel

class OpenItermRequest(PydanticBaseModel):
    """Request model for opening iTerm SSH connection."""
    host: str
    user: str = "dnroot"
    password: str = ""


@app.post("/api/open-iterm", tags=["Terminal"])
async def open_iterm(request: OpenItermRequest):
    """
    Open iTerm with SSH connection to device.
    
    This works on macOS with iTerm2 installed.
    Uses AppleScript to open iTerm and execute SSH command.
    """
    import subprocess
    import platform
    import shlex
    
    host = request.host
    user = request.user or "dnroot"
    password = request.password
    
    if not host:
        return {"success": False, "error": "No host specified"}
    
    # Build SSH command
    if password:
        # Use sshpass for auto-password (requires: brew install hudochenkov/sshpass/sshpass)
        ssh_cmd = f"sshpass -p {shlex.quote(password)} ssh -o StrictHostKeyChecking=no {user}@{host}"
    else:
        ssh_cmd = f"ssh {user}@{host}"
    
    system = platform.system()
    
    if system == "Darwin":  # macOS
        # Use AppleScript to open iTerm and run SSH
        applescript = f'''
        tell application "iTerm"
            activate
            set newWindow to (create window with default profile)
            tell current session of newWindow
                write text "{ssh_cmd}"
            end tell
        end tell
        '''
        try:
            subprocess.Popen(["osascript", "-e", applescript])
            return {"success": True, "message": f"iTerm opened with SSH to {user}@{host}"}
        except Exception as e:
            # Fallback: try opening Terminal.app
            try:
                terminal_script = f'''
                tell application "Terminal"
                    activate
                    do script "{ssh_cmd}"
                end tell
                '''
                subprocess.Popen(["osascript", "-e", terminal_script])
                return {"success": True, "message": f"Terminal.app opened with SSH to {user}@{host}"}
            except Exception as e2:
                return {"success": False, "error": str(e2)}
    
    elif system == "Linux":
        # Try common Linux terminal emulators
        terminals = [
            # GNOME Terminal
            ["gnome-terminal", "--", "bash", "-c", f"{ssh_cmd}; exec bash"],
            # Konsole
            ["konsole", "-e", "bash", "-c", f"{ssh_cmd}; exec bash"],
            # xterm
            ["xterm", "-e", f"{ssh_cmd}"],
            # xfce4-terminal
            ["xfce4-terminal", "-e", f"{ssh_cmd}"],
        ]
        
        for terminal_cmd in terminals:
            try:
                subprocess.Popen(terminal_cmd)
                return {"success": True, "message": f"Terminal opened with SSH to {user}@{host}"}
            except FileNotFoundError:
                continue
        
        return {"success": False, "error": "No supported terminal emulator found"}
    
    elif system == "Windows":
        # Try Windows Terminal or cmd
        try:
            subprocess.Popen(["wt", "ssh", f"{user}@{host}"])
            return {"success": True, "message": f"Windows Terminal opened with SSH to {user}@{host}"}
        except FileNotFoundError:
            try:
                subprocess.Popen(["cmd", "/c", "start", "cmd", "/k", ssh_cmd])
                return {"success": True, "message": f"CMD opened with SSH to {user}@{host}"}
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    return {"success": False, "error": f"Unsupported operating system: {system}"}


# ============================================================================
# Static File Serving
# ============================================================================

# Serve index.html at root
@app.get("/", response_class=FileResponse)
async def serve_root():
    """Serve the main index.html."""
    return FileResponse(STATIC_DIR / "index.html")


# Serve specific static files (before the catch-all mount)
@app.get("/topology.js", response_class=FileResponse)
async def serve_topology_js():
    return FileResponse(STATIC_DIR / "topology.js")


@app.get("/styles.css", response_class=FileResponse)
async def serve_styles():
    return FileResponse(STATIC_DIR / "styles.css")


@app.get("/debugger.js", response_class=FileResponse)
async def serve_debugger():
    return FileResponse(STATIC_DIR / "debugger.js")


@app.get("/topology-momentum.js", response_class=FileResponse)
async def serve_momentum():
    return FileResponse(STATIC_DIR / "topology-momentum.js")


@app.get("/topology-history.js", response_class=FileResponse)
async def serve_history():
    return FileResponse(STATIC_DIR / "topology-history.js")


# All topology module files
@app.get("/topology-groups.js", response_class=FileResponse)
async def serve_groups():
    return FileResponse(STATIC_DIR / "topology-groups.js")

@app.get("/topology-toolbar.js", response_class=FileResponse)
async def serve_toolbar():
    return FileResponse(STATIC_DIR / "topology-toolbar.js")

@app.get("/topology-dnaas.js", response_class=FileResponse)
async def serve_dnaas_module():
    return FileResponse(STATIC_DIR / "topology-dnaas.js")

@app.get("/topology-registry.js", response_class=FileResponse)
async def serve_registry():
    return FileResponse(STATIC_DIR / "topology-registry.js")

@app.get("/topology-tests.js", response_class=FileResponse)
async def serve_tests():
    return FileResponse(STATIC_DIR / "topology-tests.js")

@app.get("/topology-link-editor.js", response_class=FileResponse)
async def serve_link_editor():
    return FileResponse(STATIC_DIR / "topology-link-editor.js")

@app.get("/topology-errors.js", response_class=FileResponse)
async def serve_errors():
    return FileResponse(STATIC_DIR / "topology-errors.js")

@app.get("/topology-geometry.js", response_class=FileResponse)
async def serve_geometry():
    return FileResponse(STATIC_DIR / "topology-geometry.js")

@app.get("/topology-events.js", response_class=FileResponse)
async def serve_events():
    return FileResponse(STATIC_DIR / "topology-events.js")

@app.get("/topology-minimap.js", response_class=FileResponse)
async def serve_minimap():
    return FileResponse(STATIC_DIR / "topology-minimap.js")

@app.get("/topology-devices.js", response_class=FileResponse)
async def serve_devices():
    return FileResponse(STATIC_DIR / "topology-devices.js")

@app.get("/topology-files.js", response_class=FileResponse)
async def serve_files():
    return FileResponse(STATIC_DIR / "topology-files.js")

@app.get("/topology-platform-data.js", response_class=FileResponse)
async def serve_platform_data():
    return FileResponse(STATIC_DIR / "topology-platform-data.js")

@app.get("/topology-shapes.js", response_class=FileResponse)
async def serve_shapes():
    return FileResponse(STATIC_DIR / "topology-shapes.js")

@app.get("/topology-links.js", response_class=FileResponse)
async def serve_links():
    return FileResponse(STATIC_DIR / "topology-links.js")

@app.get("/topology-ui.js", response_class=FileResponse)
async def serve_ui():
    return FileResponse(STATIC_DIR / "topology-ui.js")

@app.get("/topology-menus.js", response_class=FileResponse)
async def serve_menus():
    return FileResponse(STATIC_DIR / "topology-menus.js")

@app.get("/topology-text.js", response_class=FileResponse)
async def serve_text():
    return FileResponse(STATIC_DIR / "topology-text.js")

@app.get("/topology-input.js", response_class=FileResponse)
async def serve_input():
    return FileResponse(STATIC_DIR / "topology-input.js")

@app.get("/topology-drawing.js", response_class=FileResponse)
async def serve_drawing():
    return FileResponse(STATIC_DIR / "topology-drawing.js")


@app.get("/scaler-api.js", response_class=FileResponse)
async def serve_scaler_api():
    """Serve SCALER API client (will be created in Phase 2)."""
    file_path = STATIC_DIR / "scaler-api.js"
    if file_path.exists():
        return FileResponse(file_path)
    return JSONResponse({"error": "scaler-api.js not yet created"}, status_code=404)


@app.get("/scaler-gui.js", response_class=FileResponse)
async def serve_scaler_gui():
    """Serve SCALER GUI (will be created in Phase 3)."""
    file_path = STATIC_DIR / "scaler-gui.js"
    if file_path.exists():
        return FileResponse(file_path)
    return JSONResponse({"error": "scaler-gui.js not yet created"}, status_code=404)


# Catch-all for other static files (images, fonts, etc.)
@app.get("/{file_path:path}")
async def serve_static(file_path: str):
    """Serve other static files with correct MIME types."""
    full_path = STATIC_DIR / file_path
    if full_path.exists() and full_path.is_file():
        # Ensure correct media type for JavaScript files
        if file_path.endswith('.js'):
            return FileResponse(full_path, media_type="application/javascript")
        elif file_path.endswith('.css'):
            return FileResponse(full_path, media_type="text/css")
        elif file_path.endswith('.html'):
            return FileResponse(full_path, media_type="text/html")
        elif file_path.endswith('.json'):
            return FileResponse(full_path, media_type="application/json")
        return FileResponse(full_path)
    # Return 404 for missing files
    return JSONResponse({"error": f"File not found: {file_path}"}, status_code=404)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        reload_dirs=[str(PROJECT_ROOT / "api")]
    )

