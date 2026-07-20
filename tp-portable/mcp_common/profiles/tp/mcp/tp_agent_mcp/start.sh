#!/bin/bash
# Start the TP Agent MCP server
# Usage: ./start.sh [--install]
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ "$1" = "--install" ]; then
    echo "[INFO] Installing dependencies..."
    pip install -r requirements.txt 2>&1 | tail -5
fi

export PYTHONPATH="${SCRIPT_DIR}/..:${PYTHONPATH}"

echo "[INFO] Starting TP Agent MCP server on port 9200..."
echo "[INFO] HTTP API: http://localhost:9200/api/health"
echo "[INFO] MCP SSE:  http://localhost:9200/sse"
echo ""

python -m tp_agent_mcp.server
