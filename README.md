# DriveNets Topology Studio

Unified DriveNets Topology Editor + Scaler Configurator.

## What's Inside

| Directory | Source Repo | Purpose |
|-----------|-------------|---------|
| `topology/` | [topology-creator](https://github.com/YarelOr-dn/topology-creator) | Canvas-based network topology editor (HTML5/JS) + backend servers |
| `scaler/` | [dnos-scaler](https://github.com/YarelOr-dn/dnos-scaler) | DNOS config generation library, wizard modules, config push, validation |

## Architecture

```
Browser <-> serve.py (8080) --proxy--> discovery_api.py (8765) --MCP--> Network Mapper
                            --proxy--> scaler_bridge.py (8766) --import--> scaler/wizard/*
```

- **serve.py** (port 8080) — Main web server, static files, API proxy, service orchestrator
- **discovery_api.py** (port 8765) — LLDP/DNAAS device discovery, Network Mapper MCP client
- **scaler_bridge.py** (port 8766) — Wraps scaler library for GUI wizards (config generation, push, validation)

## Quick Start

```bash
# Clone with full history
git clone git@github.com:YarelOr-dn/drivenets-topology-studio.git
cd drivenets-topology-studio

# Start the full stack
chmod +x start.sh
./start.sh

# Open in browser
open http://localhost:8080
```

## Prerequisites

- Python 3.10+
- `pip install paramiko aiohttp fastapi uvicorn`
- SSH access to DNOS devices (for scaler wizards)
- Network Mapper MCP server (optional, for LLDP discovery)

## Repo Structure (Git Subtree)

Both `topology/` and `scaler/` are git subtrees. Their original repos remain fully
independent and can be developed separately. Changes flow in both directions:

```bash
# Pull latest from topology-creator into this repo
git subtree pull --prefix=topology topology-origin feature/brand-ui-refresh --squash

# Pull latest from dnos-scaler into this repo
git subtree pull --prefix=scaler scaler-origin main --squash

# Push changes made here back to topology-creator
git subtree push --prefix=topology topology-origin feature/brand-ui-refresh

# Push changes made here back to dnos-scaler
git subtree push --prefix=scaler scaler-origin main
```

## Key Features

### Topology Editor
- Canvas-based network diagram editor with drag-and-drop devices
- BUL (Bound Unbound Link) chain system for complex link topologies
- LLDP animation, DNAAS discovery, Network Mapper auto-layout
- XRAY live packet capture integration (CP/DP)
- Save/load/export topologies, undo/redo, auto-save

### Scaler Configurator (GUI Wizards)
- Interface, Service, VRF, Bridge Domain, BGP, IGP, FlowSpec, Routing Policy wizards
- Live device context with smart suggestions (LLDP, free interfaces, next EVI)
- Config generation via backend (identical output to terminal wizard)
- Commit check + hold-and-commit flow (single SSH session)
- Wizard run history with re-run and mirror-to-other-device
- Collision detection (skip-existing sub-interfaces)
- Config mirror (copy config between devices with interface remapping)

### Scaler Library (Terminal)
- Interactive terminal wizard (`python3 -m scaler wizard`)
- Config builders for all DNOS hierarchies
- Scale operations (bulk sub-interface creation)
- Config pusher with SSH terminal paste
- Mirror config between devices
- CLI validator for DNOS syntax
