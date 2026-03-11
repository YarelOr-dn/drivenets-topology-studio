#!/usr/bin/env bash
# One-command launcher for topology app stack (serve.py + discovery_api + scaler_bridge).
# Usage: ./start.sh [--stop | --watch]

set -e
CURSOR="${CURSOR:-$HOME/CURSOR}"
cd "$CURSOR"

kill_port() {
    local port=$1
    local pids
    pids=$(lsof -ti ":$port" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "[INFO] Stopping process(es) on port $port: $pids"
        echo "$pids" | xargs kill 2>/dev/null || true
        sleep 1
        # Force kill if still running
        pids=$(lsof -ti ":$port" 2>/dev/null || true)
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -9 2>/dev/null || true
        fi
    fi
}

stop_all() {
    echo "[INFO] Stopping topology app stack..."
    kill_port 8080
    kill_port 8765
    kill_port 8766
    echo "[OK] All services stopped"
}

if [ "$1" = "--stop" ]; then
    stop_all
    exit 0
fi

# Clean slate: kill any existing instances
stop_all
sleep 2

# Optional: start Network Mapper MCP if local (enables LLDP enrichment + Map All)
if [ -d "$HOME/network-mapper" ]; then
    echo "[INFO] Starting Network Mapper MCP..."
    (cd "$HOME/network-mapper" && npm start &)
    sleep 2
fi

if [ "$1" = "--watch" ]; then
    echo "[INFO] Watch mode: will restart when serve.py changes"
    while true; do
        sleep 2
        python3 serve.py &
        SERVE_PID=$!
        LAST_MTIME=$(stat -c %Y serve.py 2>/dev/null || stat -f %m serve.py 2>/dev/null)
        while true; do
            sleep 5
            if ! kill -0 "$SERVE_PID" 2>/dev/null; then
                echo "[WARN] serve.py exited, restarting..."
                break
            fi
            CURR_MTIME=$(stat -c %Y serve.py 2>/dev/null || stat -f %m serve.py 2>/dev/null)
            if [ "$CURR_MTIME" != "$LAST_MTIME" ]; then
                echo "[INFO] serve.py changed, restarting..."
                kill "$SERVE_PID" 2>/dev/null || true
                sleep 2
                stop_all
                sleep 2
                break
            fi
        done
    done
else
    echo "[INFO] Starting topology app at http://0.0.0.0:8080"
    exec python3 serve.py
fi
