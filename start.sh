#!/usr/bin/env bash
# DriveNets Topology Studio - Unified Launcher
# Starts the topology editor + scaler configurator backend stack
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOPOLOGY_DIR="$SCRIPT_DIR/topology"
SCALER_DIR="$SCRIPT_DIR/scaler"

export PYTHONPATH="${SCALER_DIR}:${TOPOLOGY_DIR}:${PYTHONPATH:-}"

usage() {
    echo "Usage: $0 [--stop] [--watch] [--help]"
    echo ""
    echo "  (no args)   Start the full stack (serve.py + discovery_api + scaler_bridge)"
    echo "  --stop      Stop all running services"
    echo "  --watch     Start with file-watcher (auto-restart on changes)"
    echo "  --help      Show this help"
    echo ""
    echo "Components:"
    echo "  topology/   Topology Creator canvas editor + backend servers"
    echo "  scaler/     DNOS Scaler library (wizard, config builders, pusher)"
}

case "${1:-}" in
    --stop)
        echo "[STOP] Killing services on ports 8080, 8765, 8766..."
        for port in 8080 8765 8766; do
            pid=$(lsof -ti :$port 2>/dev/null || true)
            if [ -n "$pid" ]; then
                kill $pid 2>/dev/null && echo "  Killed PID $pid (port $port)" || true
            fi
        done
        echo "[STOP] Done."
        exit 0
        ;;
    --watch)
        cd "$TOPOLOGY_DIR"
        exec bash start.sh --watch
        ;;
    --help|-h)
        usage
        exit 0
        ;;
    *)
        if [ -f "$TOPOLOGY_DIR/start.sh" ]; then
            cd "$TOPOLOGY_DIR"
            exec bash start.sh
        else
            cd "$TOPOLOGY_DIR"
            exec python3 serve.py
        fi
        ;;
esac
