#!/bin/bash
# Start tp-agent-mcp server as a background daemon
# Usage: ./start_daemon.sh [start|stop|status|restart]
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="/tmp/tp_agent_mcp.pid"
LOG_FILE="/tmp/tp_agent_mcp.log"

start() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "[INFO] tp-agent-mcp already running (PID $(cat "$PID_FILE"))"
        return 0
    fi
    echo "[INFO] Starting tp-agent-mcp server..."
    cd "$SCRIPT_DIR/.."
    nohup python3 -m tp_agent_mcp.server > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 2
    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "[OK] tp-agent-mcp started (PID $(cat "$PID_FILE"))"
        echo "[INFO] HTTP API: http://localhost:9200/api/health"
        echo "[INFO] MCP SSE:  http://localhost:9200/sse"
        echo "[INFO] Log file: $LOG_FILE"
    else
        echo "[ERROR] Failed to start. Check $LOG_FILE"
        return 1
    fi
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "[INFO] Stopping tp-agent-mcp (PID $PID)..."
            kill "$PID"
            rm -f "$PID_FILE"
            echo "[OK] Stopped"
        else
            echo "[INFO] Process not running, cleaning up PID file"
            rm -f "$PID_FILE"
        fi
    else
        echo "[INFO] tp-agent-mcp not running (no PID file)"
    fi
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "[OK] tp-agent-mcp running (PID $(cat "$PID_FILE"))"
        curl -s http://localhost:9200/health 2>/dev/null || echo "[WARN] HTTP not responding"
    else
        echo "[INFO] tp-agent-mcp not running"
    fi
}

case "${1:-start}" in
    start)   start ;;
    stop)    stop ;;
    status)  status ;;
    restart) stop; sleep 1; start ;;
    *)       echo "Usage: $0 {start|stop|status|restart}"; exit 1 ;;
esac
