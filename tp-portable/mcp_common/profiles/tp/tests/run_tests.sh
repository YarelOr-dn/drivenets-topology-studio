#!/usr/bin/env bash
# Regression suite for /TP portable profile gates.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GATES="$ROOT/gates"
export PYTHONPATH="$(cd "$ROOT/../.." && pwd):$(dirname "$(cd "$ROOT/../.." && pwd)"):${PYTHONPATH:-}"
cd "$ROOT/tests"
echo "[INFO] Running scenario tooling tests..."
PYTHONPATH="$GATES:$PYTHONPATH" python3 -m unittest -v test_scenario_tooling.py
echo "[INFO] Running Stage-7 refine worklist tests..."
PYTHONPATH="$GATES:$PYTHONPATH" python3 -m unittest -v test_refine_worklist.py
echo "[INFO] Running spec-binding tests..."
PYTHONPATH="$GATES:$PYTHONPATH" python3 -m unittest -v test_spec_binding.py
echo "[OK] Portable /TP gate unit tests passed"
