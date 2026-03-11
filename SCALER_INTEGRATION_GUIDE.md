# SCALER Integration Guide - Step by Step Implementation

> **Project**: Unified Network Studio  
> **Goal**: Integrate SCALER CLI functionality into Topology Creator as a full GUI web application  
> **Created**: December 30, 2025  
> **Status**: In Progress

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Prerequisites Checklist](#prerequisites-checklist)
4. [Phase 1: Backend Foundation](#phase-1-backend-foundation)
5. [Phase 2: Frontend API Client](#phase-2-frontend-api-client)
6. [Phase 3: GUI Components](#phase-3-gui-components)
7. [Phase 4: Topology Integration](#phase-4-topology-integration)
8. [Phase 5: Advanced Features](#phase-5-advanced-features)
9. [Testing Procedures](#testing-procedures)
10. [Rollback Procedures](#rollback-procedures)

---

## Project Overview

### Source Projects

| Project | Location | Repository | Purpose |
|---------|----------|------------|---------|
| Topology Creator | `/home/dn/CURSOR` | github.com/YarelOr-dn/topology-creator | Web-based network topology visualization |
| SCALER | `/home/dn/SCALER` | github.com/YarelOr-dn/dnos-scaler | CLI-based multi-device configuration tool |

### Backup Branches (Created Dec 30, 2025)

- **Topology**: `backup-pre-scaler-integration-dec30-2025`
- **SCALER**: `main` (initial commit)

### Key Decisions Made

1. **Frontend**: Vanilla JavaScript (consistent with topology.js)
2. **Backend**: FastAPI (replaces serve.py)
3. **Device DB Master**: SCALER's `/home/dn/SCALER/db/devices.json`
4. **CLI Fate**: Keep both CLI and GUI working
5. **Migration**: Topology-first (add SCALER into CURSOR project)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         BROWSER                                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ topology.js  │  │ scaler-gui.js│  │ scaler-api.js        │   │
│  │ (Canvas)     │  │ (GUI Panels) │  │ (HTTP/WS Client)     │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    index.html                             │   │
│  │              (Unified UI Container)                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ HTTP / WebSocket
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (api/main.py)                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ /api/devices│  │ /api/config │  │ /api/operations         │  │
│  │ (CRUD)      │  │ (Extract)   │  │ (Push/Delete/MH)        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              scaler_bridge.py                             │   │
│  │         (Imports SCALER Python modules)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ Python imports
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SCALER (/home/dn/SCALER)                      │
├─────────────────────────────────────────────────────────────────┤
│  DeviceManager │ ConfigExtractor │ ConfigPusher │ interactive   │
│                │                 │              │ _scale.py     │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ SSH (Paramiko)
                               ▼
                    ┌─────────────────────┐
                    │   Network Devices   │
                    │   (PE-1, PE-2, etc) │
                    └─────────────────────┘
```

---

## Prerequisites Checklist

Before starting, verify:

- [ ] Git backups created and pushed
  - [ ] Topology: `backup-pre-scaler-integration-dec30-2025` on GitHub
  - [ ] SCALER: `main` branch on GitHub
- [ ] Python 3.8+ available
- [ ] Current serve.py works: `cd /home/dn/CURSOR && python3 serve.py`
- [ ] SCALER CLI works: `cd /home/dn/SCALER && python3 -m scaler`
- [ ] Network devices accessible (PE-1, PE-2, etc.)

### Verify Commands

```bash
# Check Python version
python3 --version

# Check current topology server works
cd /home/dn/CURSOR && python3 serve.py &
curl http://localhost:8080/ | head -20
# Should see HTML content

# Check SCALER imports work
cd /home/dn/SCALER && python3 -c "from scaler.device_manager import DeviceManager; print('OK')"

# Check devices accessible
cd /home/dn/SCALER && python3 -c "
from scaler.device_manager import DeviceManager
dm = DeviceManager()
for d in dm.list_devices():
    print(f'{d.hostname}: {d.ip}')
"
```

---

## Phase 1: Backend Foundation

### Step 1.1: Create API Directory Structure

**Files to create:**
```
/home/dn/CURSOR/api/
├── __init__.py
├── main.py
├── requirements.txt
├── scaler_bridge.py
├── websocket_manager.py
└── routes/
    ├── __init__.py
    ├── devices.py
    ├── config.py
    └── operations.py
```

**Action:**
```bash
mkdir -p /home/dn/CURSOR/api/routes
touch /home/dn/CURSOR/api/__init__.py
touch /home/dn/CURSOR/api/routes/__init__.py
```

**Verification:**
```bash
ls -la /home/dn/CURSOR/api/
ls -la /home/dn/CURSOR/api/routes/
# Should see __init__.py in both directories
```

---

### Step 1.2: Create requirements.txt

**File:** `/home/dn/CURSOR/api/requirements.txt`

**Contents:**
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
websockets>=12.0
python-multipart>=0.0.6
pydantic>=2.5.0
```

**Action:** Create the file with above contents

**Verification:**
```bash
cat /home/dn/CURSOR/api/requirements.txt
pip3 install -r /home/dn/CURSOR/api/requirements.txt
python3 -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
# Should print FastAPI version
```

---

### Step 1.3: Create scaler_bridge.py

**File:** `/home/dn/CURSOR/api/scaler_bridge.py`

**Purpose:** Import SCALER modules and expose them for API use

**Key imports needed:**
```python
# Add SCALER to Python path
import sys
sys.path.insert(0, '/home/dn/SCALER')

# Import SCALER modules
from scaler.device_manager import DeviceManager
from scaler.config_extractor import ConfigExtractor
from scaler.config_parser import ConfigParser
from scaler.config_pusher import ConfigPusher
from scaler.models import Device, Platform
```

**Functions to expose:**
- `get_device_manager()` → Returns DeviceManager instance
- `get_config_extractor()` → Returns ConfigExtractor instance
- `extract_config_summary(config_text)` → Returns parsed summary dict
- `parse_multihoming(config_text)` → Returns MH interfaces dict

**Verification:**
```bash
cd /home/dn/CURSOR && python3 -c "
from api.scaler_bridge import get_device_manager
dm = get_device_manager()
print(f'Loaded {len(dm.list_devices())} devices')
"
# Should print number of devices
```

---

### Step 1.4: Create main.py (FastAPI App)

**File:** `/home/dn/CURSOR/api/main.py`

**Purpose:** Main FastAPI application that:
1. Serves static files (replaces serve.py)
2. Mounts API routes
3. Handles WebSocket connections

**Key components:**

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI(title="Network Studio API", version="1.0.0")

# Serve index.html at root
@app.get("/")
async def root():
    return FileResponse("/home/dn/CURSOR/index.html")

# Mount API routes
from api.routes import devices, config, operations
app.include_router(devices.router, prefix="/api/devices", tags=["devices"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(operations.router, prefix="/api/operations", tags=["operations"])

# Serve static files (js, css, etc.)
app.mount("/", StaticFiles(directory="/home/dn/CURSOR", html=True), name="static")
```

**Verification:**
```bash
# Start the new server
cd /home/dn/CURSOR && python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload &

# Test static file serving
curl http://localhost:8080/ | head -20
# Should see index.html content

# Test API docs
curl http://localhost:8080/docs
# Should see FastAPI Swagger UI (or redirect)

# Kill test server
pkill -f uvicorn
```

---

### Step 1.5: Create routes/devices.py

**File:** `/home/dn/CURSOR/api/routes/devices.py`

**Endpoints:**

| Method | Endpoint | Description | SCALER Function |
|--------|----------|-------------|-----------------|
| GET | `/` | List all devices | `dm.list_devices()` |
| POST | `/` | Add new device | `dm.add_device()` |
| GET | `/{device_id}` | Get device by ID | `dm.get_device()` |
| PUT | `/{device_id}` | Update device | `dm.update_device()` |
| DELETE | `/{device_id}` | Delete device | `dm.remove_device()` |
| POST | `/{device_id}/test` | Test connection | `extractor.test_connection()` |
| POST | `/{device_id}/sync` | Sync config | `extractor.extract_running_config()` |

**Response models (Pydantic):**
```python
class DeviceResponse(BaseModel):
    id: str
    hostname: str
    ip: str
    platform: str
    last_sync: Optional[str]
    description: Optional[str]

class DeviceListResponse(BaseModel):
    devices: List[DeviceResponse]
    count: int
```

**Verification:**
```bash
# Test list devices endpoint
curl http://localhost:8080/api/devices/
# Should return JSON with devices array

# Test single device
curl http://localhost:8080/api/devices/pe1
# Should return PE-1 device details

# Test connection
curl -X POST http://localhost:8080/api/devices/pe1/test
# Should return connection status
```

---

### Step 1.6: Create routes/config.py

**File:** `/home/dn/CURSOR/api/routes/config.py`

**Endpoints:**

| Method | Endpoint | Description | SCALER Function |
|--------|----------|-------------|-----------------|
| GET | `/{device_id}/running` | Get running config | `extractor.extract_running_config()` |
| GET | `/{device_id}/summary` | Get config summary | `show_current_config_summary()` logic |
| GET | `/{device_id}/interfaces` | List interfaces | Parse from config |
| GET | `/{device_id}/services` | List services | Parse from config |
| GET | `/{device_id}/multihoming` | Get MH config | `parse_existing_multihoming()` |
| GET | `/{device_id}/hierarchy/{name}` | Get hierarchy section | `extract_hierarchy_section()` |

**Response models:**
```python
class ConfigSummaryResponse(BaseModel):
    system: SystemSummary
    interfaces: InterfaceSummary
    services: ServiceSummary
    bgp: BGPSummary
    igp: IGPSummary
    multihoming: MultihomingSummary

class MultihomingResponse(BaseModel):
    count: int
    interfaces: Dict[str, str]  # interface -> ESI
    esi_prefix: Optional[str]
```

**Verification:**
```bash
# Test config summary
curl http://localhost:8080/api/config/pe1/summary
# Should return JSON with system, interfaces, services, etc.

# Test multihoming
curl http://localhost:8080/api/config/pe1/multihoming
# Should return MH interfaces and ESI values

# Test interfaces list
curl http://localhost:8080/api/config/pe1/interfaces
# Should return list of all interfaces
```

---

### Step 1.7: Create routes/operations.py

**File:** `/home/dn/CURSOR/api/routes/operations.py`

**Endpoints:**

| Method | Endpoint | Description | SCALER Function |
|--------|----------|-------------|-----------------|
| POST | `/validate` | Validate config | `validator.validate()` |
| POST | `/push` | Push config to device | `pusher.push_config()` |
| POST | `/delete` | Delete hierarchy | `delete_hierarchy()` |
| POST | `/multihoming/sync` | Sync MH between devices | `push_synchronized_multihoming()` |
| POST | `/multihoming/compare` | Compare MH configs | `_show_multi_device_compare()` |
| GET | `/{job_id}` | Get operation status | Job status lookup |
| POST | `/{job_id}/cancel` | Cancel operation | Cancel running job |

**Request models:**
```python
class PushRequest(BaseModel):
    device_id: str
    config: str
    hierarchy: str  # 'system', 'interfaces', 'services', etc.
    mode: str  # 'merge', 'replace'
    dry_run: bool = True

class MultihomingSyncRequest(BaseModel):
    device_ids: List[str]
    esi_prefix: Optional[int]
    match_neighbor: bool = True
    redundancy_mode: str = "single-active"
```

**Verification:**
```bash
# Test validate (dry run)
curl -X POST http://localhost:8080/api/operations/validate \
  -H "Content-Type: application/json" \
  -d '{"device_id": "pe1", "config": "interfaces\n  lo0\n!", "hierarchy": "interfaces"}'
# Should return validation result

# Test push (dry run mode)
curl -X POST http://localhost:8080/api/operations/push \
  -H "Content-Type: application/json" \
  -d '{"device_id": "pe1", "config": "...", "hierarchy": "interfaces", "mode": "merge", "dry_run": true}'
# Should return what would be pushed
```

---

### Step 1.8: Create websocket_manager.py

**File:** `/home/dn/CURSOR/api/websocket_manager.py`

**Purpose:** Manage WebSocket connections for real-time progress updates

**Key features:**
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)
    
    async def broadcast(self, job_id: str, message: dict):
        if job_id in self.active_connections:
            for connection in self.active_connections[job_id]:
                await connection.send_json(message)

# Message types:
# - {"type": "progress", "percent": 45, "message": "Pushing config..."}
# - {"type": "terminal", "line": "> configure"}
# - {"type": "step", "current": 2, "total": 5, "name": "Committing"}
# - {"type": "complete", "success": true, "result": {...}}
# - {"type": "error", "message": "Connection failed"}
```

**WebSocket endpoint in main.py:**
```python
@app.websocket("/ws/progress/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    await manager.connect(job_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        manager.disconnect(job_id, websocket)
```

**Verification:**
```bash
# Test WebSocket with wscat (install: npm install -g wscat)
wscat -c ws://localhost:8080/ws/progress/test-job-123
# Should connect successfully

# Or test with Python
python3 -c "
import asyncio
import websockets

async def test():
    async with websockets.connect('ws://localhost:8080/ws/progress/test') as ws:
        print('Connected!')
        await ws.close()

asyncio.run(test())
"
```

---

### Step 1.9: Phase 1 Final Verification

**Complete test script:**
```bash
#!/bin/bash
# Save as: /home/dn/CURSOR/test_phase1.sh

echo "=== Phase 1 Verification ==="

# 1. Check all files exist
echo -n "Checking files... "
FILES=(
    "api/__init__.py"
    "api/main.py"
    "api/requirements.txt"
    "api/scaler_bridge.py"
    "api/websocket_manager.py"
    "api/routes/__init__.py"
    "api/routes/devices.py"
    "api/routes/config.py"
    "api/routes/operations.py"
)
for f in "${FILES[@]}"; do
    if [ ! -f "/home/dn/CURSOR/$f" ]; then
        echo "MISSING: $f"
        exit 1
    fi
done
echo "OK"

# 2. Check imports work
echo -n "Checking Python imports... "
cd /home/dn/CURSOR
python3 -c "from api.scaler_bridge import get_device_manager" || exit 1
echo "OK"

# 3. Start server
echo "Starting FastAPI server..."
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8080 &
SERVER_PID=$!
sleep 3

# 4. Test endpoints
echo -n "Testing static files... "
curl -s http://localhost:8080/ | grep -q "Network Topology" && echo "OK" || echo "FAIL"

echo -n "Testing /api/devices... "
curl -s http://localhost:8080/api/devices/ | grep -q "devices" && echo "OK" || echo "FAIL"

echo -n "Testing /api/config/pe1/summary... "
curl -s http://localhost:8080/api/config/pe1/summary | grep -q "system" && echo "OK" || echo "FAIL"

# 5. Cleanup
kill $SERVER_PID 2>/dev/null

echo "=== Phase 1 Complete ==="
```

**Expected results:**
- [ ] All files exist in correct locations
- [ ] Python imports work without errors
- [ ] FastAPI server starts on port 8080
- [ ] Static files served (index.html loads)
- [ ] API endpoints return JSON responses
- [ ] WebSocket connections work

---

## Phase 2: Frontend API Client

### Step 2.1: Create scaler-api.js

**File:** `/home/dn/CURSOR/scaler-api.js`

**Purpose:** JavaScript module for API communication

**Structure:**
```javascript
const ScalerAPI = {
    baseUrl: '',  // Same origin
    
    // ===== Device Operations =====
    async getDevices() {
        const response = await fetch('/api/devices/');
        return response.json();
    },
    
    async getDevice(deviceId) {
        const response = await fetch(`/api/devices/${deviceId}`);
        return response.json();
    },
    
    async addDevice(device) {
        const response = await fetch('/api/devices/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(device)
        });
        return response.json();
    },
    
    async testConnection(deviceId) {
        const response = await fetch(`/api/devices/${deviceId}/test`, {
            method: 'POST'
        });
        return response.json();
    },
    
    // ===== Config Operations =====
    async getConfigSummary(deviceId) {
        const response = await fetch(`/api/config/${deviceId}/summary`);
        return response.json();
    },
    
    async getInterfaces(deviceId) {
        const response = await fetch(`/api/config/${deviceId}/interfaces`);
        return response.json();
    },
    
    async getMultihoming(deviceId) {
        const response = await fetch(`/api/config/${deviceId}/multihoming`);
        return response.json();
    },
    
    // ===== Push Operations =====
    async pushConfig(request) {
        const response = await fetch('/api/operations/push', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(request)
        });
        return response.json();
    },
    
    async deleteHierarchy(deviceId, hierarchy) {
        const response = await fetch('/api/operations/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({device_id: deviceId, hierarchy: hierarchy})
        });
        return response.json();
    },
    
    // ===== WebSocket for Progress =====
    connectProgress(jobId, callbacks) {
        const ws = new WebSocket(`ws://${location.host}/ws/progress/${jobId}`);
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            switch(data.type) {
                case 'progress':
                    callbacks.onProgress?.(data.percent, data.message);
                    break;
                case 'terminal':
                    callbacks.onTerminal?.(data.line);
                    break;
                case 'step':
                    callbacks.onStep?.(data.current, data.total, data.name);
                    break;
                case 'complete':
                    callbacks.onComplete?.(data.success, data.result);
                    break;
                case 'error':
                    callbacks.onError?.(data.message);
                    break;
            }
        };
        
        ws.onerror = (error) => callbacks.onError?.(error.message);
        ws.onclose = () => callbacks.onClose?.();
        
        return ws;
    }
};
```

**Verification:**
```javascript
// In browser console after loading page:

// Test device list
ScalerAPI.getDevices().then(console.log);
// Should log: {devices: [...], count: N}

// Test config summary
ScalerAPI.getConfigSummary('pe1').then(console.log);
// Should log config summary object

// Test WebSocket
const ws = ScalerAPI.connectProgress('test-123', {
    onProgress: (p, m) => console.log(`Progress: ${p}% - ${m}`),
    onComplete: (s, r) => console.log('Done!', s, r)
});
```

---

### Step 2.2: Add scaler-api.js to index.html

**File:** `/home/dn/CURSOR/index.html`

**Change:** Add script tag before closing `</body>`:
```html
    <!-- Existing scripts -->
    <script src="topology.js"></script>
    
    <!-- NEW: SCALER API Client -->
    <script src="scaler-api.js"></script>
    
    <!-- NEW: SCALER GUI (Phase 3) -->
    <script src="scaler-gui.js"></script>
</body>
```

**Verification:**
```bash
# Check scripts are loaded
curl -s http://localhost:8080/ | grep "scaler-api.js"
# Should find the script tag

# In browser console:
typeof ScalerAPI
# Should return "object"
```

---

## Phase 3: GUI Components

### Step 3.1: Create scaler-gui.js Structure

**File:** `/home/dn/CURSOR/scaler-gui.js`

**Base structure:**
```javascript
const ScalerGUI = {
    // State
    state: {
        currentDevice: null,
        selectedDevices: [],
        activePanel: null,
        jobs: {}
    },
    
    // Panel containers (created dynamically)
    panels: {},
    
    // Initialize
    init() {
        this.createPanelContainer();
        this.bindKeyboardShortcuts();
    },
    
    // Create main panel container
    createPanelContainer() {
        const container = document.createElement('div');
        container.id = 'scaler-panel-container';
        container.className = 'scaler-panel-container';
        document.body.appendChild(container);
    },
    
    // ===== Panel Management =====
    openPanel(name, content) {...},
    closePanel(name) {...},
    closeAllPanels() {...},
    
    // ===== Device Manager =====
    openDeviceManager() {...},
    
    // ===== Config Summary =====
    showConfigSummary(deviceId) {...},
    
    // ===== Interface Wizard =====
    openInterfaceWizard(deviceId) {...},
    
    // ===== Service Config =====
    openServiceConfig(deviceId) {...},
    
    // ===== Multihoming =====
    openMultihomingSync(deviceIds) {...},
    
    // ===== Progress Panel =====
    showProgress(jobId, title) {...},
    
    // ===== Utility Functions =====
    createTable(headers, rows) {...},
    createForm(fields, onSubmit) {...},
    showNotification(message, type) {...}
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => ScalerGUI.init());
```

---

### Step 3.2: Implement Device Manager Panel

**Function:** `ScalerGUI.openDeviceManager()`

**UI Components:**
```
┌─────────────────────────────────────────────────────────────┐
│ Device Manager                                          [X] │
├─────────────────────────────────────────────────────────────┤
│ [+ Add Device]  [↻ Refresh]                                 │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────┬──────────────┬──────────┬────────┬───────────┐ │
│ │ Name    │ IP           │ Platform │ Status │ Actions   │ │
│ ├─────────┼──────────────┼──────────┼────────┼───────────┤ │
│ │ PE-1    │ wk31d7vv0... │ NCP      │ ● OK   │ [⚙] [🗑]  │ │
│ │ PE-2    │ 100.64.0.220 │ NCP      │ ● OK   │ [⚙] [🗑]  │ │
│ │ PE-4    │ kvm108-cl... │ NCP      │ ○ ?    │ [⚙] [🗑]  │ │
│ └─────────┴──────────────┴──────────┴────────┴───────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Verification:**
```javascript
// In browser console:
ScalerGUI.openDeviceManager();
// Should open device manager panel with device list
```

---

### Step 3.3: Implement Config Summary Panel

**Function:** `ScalerGUI.showConfigSummary(deviceId)`

**UI Components:**
```
┌─────────────────────────────────────────────────────────────┐
│ PE-1 Configuration Summary                              [X] │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────┬────────────────────────────────────────────┐│
│ │ System      │ PE-1 │ l3-pe (PWHE ok) │ Users: 2         ││
│ ├─────────────┼────────────────────────────────────────────┤│
│ │ Interfaces  │ Parents: 4 │ Sub-ifs: 200 │ PWHE: 50      ││
│ ├─────────────┼────────────────────────────────────────────┤│
│ │ Services    │ FXC: 100 │ VPLS: 50 │ RTs: 150            ││
│ ├─────────────┼────────────────────────────────────────────┤│
│ │ BGP         │ AS: 65000 │ Peers: 2                       ││
│ ├─────────────┼────────────────────────────────────────────┤│
│ │ IGP         │ ISIS │ Instance: IGP │ Interfaces: 6      ││
│ ├─────────────┼────────────────────────────────────────────┤│
│ │ Multihoming │ 200 interfaces │ ESI: 00:01:02:...        ││
│ └─────────────┴────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│ [Configure Interfaces] [Configure Services] [Sync MH]      │
└─────────────────────────────────────────────────────────────┘
```

**Verification:**
```javascript
ScalerGUI.showConfigSummary('pe1');
// Should show config summary for PE-1
```

---

### Step 3.4: Implement Interface Wizard

**Function:** `ScalerGUI.openInterfaceWizard(deviceId)`

**Steps:**
1. Select parent interfaces (checkboxes)
2. Configure sub-interface pattern (form)
3. Review generated config (preview)
4. Push with progress

**UI for Step 2:**
```
┌─────────────────────────────────────────────────────────────┐
│ Interface Wizard - Step 2/4: Configure Pattern         [X] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Sub-interfaces per parent: [____100____]                  │
│                                                             │
│   VLAN Configuration:                                       │
│   ○ Single tag    ● Double tag (QinQ)                       │
│                                                             │
│   Outer VLAN start: [____100____]  Step: [____1____]        │
│   Inner VLAN start: [____1______]  Step: [____1____]        │
│                                                             │
│   IP Configuration:                                         │
│   ○ None  ● IPv4  ○ IPv6  ○ Both                           │
│                                                             │
│   Starting IP: [__10.0.0.1/30__]  Step: [____4____]        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                              [← Back]  [Next: Review →]     │
└─────────────────────────────────────────────────────────────┘
```

---

### Step 3.5: Implement Progress Panel

**Function:** `ScalerGUI.showProgress(jobId, title)`

**UI Components:**
```
┌─────────────────────────────────────────────────────────────┐
│ Pushing Configuration to PE-1                           [X] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ████████████████████░░░░░░░░░░ 67%                       │
│                                                             │
│   Step 3 of 5: Committing changes                          │
│   ─────────────────────────────────────                    │
│   ✓ Step 1: Connecting to device                           │
│   ✓ Step 2: Loading configuration                          │
│   ● Step 3: Committing changes                             │
│   ○ Step 4: Verifying                                      │
│   ○ Step 5: Complete                                       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Terminal Output:                                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ > configure                                             │ │
│ │ > load merge terminal                                   │ │
│ │ > interfaces                                            │ │
│ │ >   ge100-0/0/1.100                                     │ │
│ │ > ...                                                   │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                                              [Cancel]       │
└─────────────────────────────────────────────────────────────┘
```

---

### Step 3.6: Add CSS Styles

**File:** `/home/dn/CURSOR/styles.css`

**Add SCALER-specific styles:**
```css
/* ===== SCALER GUI Styles ===== */

.scaler-panel-container {
    position: fixed;
    top: 0;
    right: 0;
    width: 450px;
    height: 100vh;
    z-index: 1000;
    pointer-events: none;
}

.scaler-panel {
    pointer-events: auto;
    background: var(--bg-primary, #1a1a2e);
    border-left: 1px solid var(--border-color, #333);
    box-shadow: -5px 0 20px rgba(0,0,0,0.3);
    height: 100%;
    display: flex;
    flex-direction: column;
}

.scaler-panel-header {
    padding: 15px 20px;
    border-bottom: 1px solid var(--border-color, #333);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.scaler-panel-content {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
}

.scaler-table {
    width: 100%;
    border-collapse: collapse;
}

.scaler-table th,
.scaler-table td {
    padding: 10px;
    text-align: left;
    border-bottom: 1px solid var(--border-color, #333);
}

.scaler-progress-bar {
    height: 8px;
    background: var(--bg-secondary, #252540);
    border-radius: 4px;
    overflow: hidden;
}

.scaler-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #4CAF50, #8BC34A);
    transition: width 0.3s ease;
}

.scaler-terminal {
    background: #0d0d0d;
    font-family: 'Monaco', 'Consolas', monospace;
    font-size: 12px;
    padding: 10px;
    border-radius: 4px;
    max-height: 200px;
    overflow-y: auto;
}

.scaler-btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: background 0.2s;
}

.scaler-btn-primary {
    background: #4CAF50;
    color: white;
}

.scaler-btn-danger {
    background: #f44336;
    color: white;
}
```

---

## Phase 4: Topology Integration

### Step 4.1: Add Right-Click Menu to Devices

**File:** `/home/dn/CURSOR/topology.js`

**Find:** Device right-click handler (search for `contextmenu` or right-click handling)

**Add menu items:**
```javascript
// In device context menu creation:
contextMenu.addItem('─── SCALER ───', null, true);  // Separator
contextMenu.addItem('View Config Summary', () => {
    ScalerGUI.showConfigSummary(device.id);
});
contextMenu.addItem('Configure Interfaces', () => {
    ScalerGUI.openInterfaceWizard(device.id);
});
contextMenu.addItem('Configure Services', () => {
    ScalerGUI.openServiceConfig(device.id);
});
contextMenu.addItem('Delete Configuration', () => {
    ScalerGUI.openDeleteHierarchy(device.id);
});
```

---

### Step 4.2: Add Multi-Device Selection

**File:** `/home/dn/CURSOR/topology.js`

**Features to add:**
1. Shift+click to add device to selection
2. Visual highlight for selected devices
3. "Configure Selected" button when multiple selected

```javascript
// Track selected devices
let selectedDevices = [];

// On device click with Shift
if (event.shiftKey) {
    if (selectedDevices.includes(device.id)) {
        selectedDevices = selectedDevices.filter(id => id !== device.id);
    } else {
        selectedDevices.push(device.id);
    }
    updateSelectedDevicesUI();
}

// Show multi-device action bar
function updateSelectedDevicesUI() {
    if (selectedDevices.length > 1) {
        showMultiDeviceBar();
    } else {
        hideMultiDeviceBar();
    }
}
```

---

### Step 4.3: Add Visual Indicators

**Features:**
1. Device sync status indicator (green dot = synced, yellow = stale)
2. MH indicator (show if device has multihoming configured)
3. Hover tooltip with quick summary

```javascript
// In device rendering:
function drawDeviceStatus(ctx, device) {
    // Sync status dot
    const statusColor = device.lastSync ? '#4CAF50' : '#FFC107';
    ctx.fillStyle = statusColor;
    ctx.beginPath();
    ctx.arc(device.x + device.width - 10, device.y + 10, 5, 0, Math.PI * 2);
    ctx.fill();
    
    // MH indicator
    if (device.hasMH) {
        ctx.fillStyle = '#2196F3';
        ctx.font = '10px Arial';
        ctx.fillText('MH', device.x + 5, device.y + device.height - 5);
    }
}
```

---

## Phase 5: Advanced Features

### Step 5.1: Config Diff Between Devices

**Endpoint:** `POST /api/operations/diff`
**UI:** Side-by-side diff view with highlighting

### Step 5.2: Configuration Templates

**Endpoint:** `GET/POST /api/templates`
**UI:** Template browser, save/load templates

### Step 5.3: Configuration History

**Endpoint:** `GET /api/devices/{id}/history`
**UI:** Timeline view, rollback option

### Step 5.4: Batch Operations

**Endpoint:** `POST /api/operations/batch`
**UI:** Apply same config to multiple devices

---

## Testing Procedures

### Unit Tests

```bash
# Test SCALER bridge
cd /home/dn/CURSOR
python3 -m pytest api/tests/ -v

# Test API endpoints
python3 -m pytest api/tests/test_routes.py -v
```

### Integration Tests

```bash
# Start server
python3 -m uvicorn api.main:app --port 8080 &

# Run integration tests
./test_integration.sh
```

### Manual Testing Checklist

- [ ] Static files load correctly
- [ ] Device list displays
- [ ] Config summary shows all sections
- [ ] Interface wizard completes all steps
- [ ] Push operation shows progress
- [ ] WebSocket receives updates
- [ ] Right-click menu works
- [ ] Multi-device selection works
- [ ] Visual indicators display

---

## Rollback Procedures

### Restore Topology Creator

```bash
cd /home/dn/CURSOR
git fetch origin
git checkout backup-pre-scaler-integration-dec30-2025
# Or: git checkout origin/backup-pre-scaler-integration-dec30-2025

# Restore serve.py as main server
python3 serve.py
```

### Restore SCALER

```bash
cd /home/dn/SCALER
git checkout main
# SCALER CLI continues to work independently
python3 -m scaler
```

### Quick Rollback (Keep API but disable)

```bash
# Just use old serve.py instead of FastAPI
cd /home/dn/CURSOR
mv api api.disabled
python3 serve.py
```

---

## Progress Tracking

| Phase | Step | Status | Date | Notes |
|-------|------|--------|------|-------|
| 1 | 1.1 Directory structure | ⬜ | | |
| 1 | 1.2 requirements.txt | ⬜ | | |
| 1 | 1.3 scaler_bridge.py | ⬜ | | |
| 1 | 1.4 main.py | ⬜ | | |
| 1 | 1.5 routes/devices.py | ⬜ | | |
| 1 | 1.6 routes/config.py | ⬜ | | |
| 1 | 1.7 routes/operations.py | ⬜ | | |
| 1 | 1.8 websocket_manager.py | ⬜ | | |
| 1 | 1.9 Phase 1 verification | ⬜ | | |
| 2 | 2.1 scaler-api.js | ⬜ | | |
| 2 | 2.2 Add to index.html | ⬜ | | |
| 3 | 3.1 scaler-gui.js structure | ⬜ | | |
| 3 | 3.2 Device Manager Panel | ⬜ | | |
| 3 | 3.3 Config Summary Panel | ⬜ | | |
| 3 | 3.4 Interface Wizard | ⬜ | | |
| 3 | 3.5 Progress Panel | ⬜ | | |
| 3 | 3.6 CSS Styles | ⬜ | | |
| 4 | 4.1 Right-click menu | ⬜ | | |
| 4 | 4.2 Multi-device selection | ⬜ | | |
| 4 | 4.3 Visual indicators | ⬜ | | |
| 5 | 5.1 Config diff | ⬜ | | |
| 5 | 5.2 Templates | ⬜ | | |
| 5 | 5.3 History | ⬜ | | |
| 5 | 5.4 Batch operations | ⬜ | | |

---

## Legend

- ⬜ Not started
- 🔄 In progress
- ✅ Complete
- ❌ Blocked
- ⏸️ Paused

---

*Last updated: December 30, 2025*











