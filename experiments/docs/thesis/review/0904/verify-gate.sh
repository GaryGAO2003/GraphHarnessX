#!/usr/bin/env bash
# verify-gate.sh — objective gate of the overnight thesis review loop.
# Exit 0 = GATE PASSED, non-zero = GATE FAILED.  Details in gate_result.json.
# Usage: bash verify-gate.sh [--no-regen]
set -uo pipefail
cd "$(dirname "$0")"
python gate_checks.py "$@"
exit $?
