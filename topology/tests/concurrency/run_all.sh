#!/usr/bin/env bash
# run_all.sh -- run every concurrency / multi-user regression test in sequence.
#
# Exits 0 if every test passes, non-zero on the first failure. Each test
# prints its own summary line. Intended to be copy-paste-friendly for the
# developer loop (no pytest dependency, no fixtures).
#
# Usage:
#   bash topology/tests/concurrency/run_all.sh

set -u
cd "$(dirname "$0")/../../.." || exit 2
REPO="$(pwd)"
export PYTHONPATH="${REPO}/topology:${REPO}/scaler"

HERE="${REPO}/topology/tests/concurrency"
FAIL=0

run_case() {
    local name="$1"
    shift
    echo
    echo "================================================================"
    echo "  ${name}"
    echo "================================================================"
    if ! "$@"; then
        echo "[FAIL] ${name} (exit $?)"
        FAIL=$((FAIL + 1))
    fi
}

run_case "Wave 2: DeviceOpScheduler" \
    env TP_AUTH_ENFORCE=never \
        python3 "${HERE}/test_wave2_scheduler.py"

run_case "Wave 6: 100-user storm" \
    python3 "${HERE}/test_wave6_storm.py"

run_case "Wave 7: unit-level hardening primitives" \
    python3 "${HERE}/test_wave7_hardening.py"

run_case "Wave 7.9: end-to-end HTTP integration" \
    python3 "${HERE}/test_wave7_integration.py"

echo
echo "================================================================"
if [[ "${FAIL}" -eq 0 ]]; then
    echo "[PASS] all ${PWD##*/} concurrency regressions green"
    exit 0
else
    echo "[FAIL] ${FAIL} suite(s) failed"
    exit 1
fi
