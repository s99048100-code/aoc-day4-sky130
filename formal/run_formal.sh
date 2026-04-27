#!/usr/bin/env bash
# Run yosys-only formal proof of FSM safety + bounds for tt_um_day4_forklift.
# Output is teed to docs/formal_log.txt.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
LOG="${HERE}/../docs/formal_log.txt"

cd "${HERE}"
echo "=== yosys formal run $(date -Iseconds) ===" | tee "${LOG}"
yosys -s forklift.ys 2>&1 | tee -a "${LOG}"
echo "=== done ===" | tee -a "${LOG}"
