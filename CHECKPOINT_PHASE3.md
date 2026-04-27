# CHECKPOINT_PHASE3 — Portfolio Hardening

Plan file: `~/.claude/plans/dazzling-painting-deer.md`

## Milestones

| # | Title | Status |
|---|-------|--------|
| M1 | Cleanup (delete phase2 checkpoint, unify docs) | ✓ done |
| M2 | README architecture rationale + critical-path analysis | ✓ done |
| M3 | cocotb 1024-vector random regression + iter histogram | ✓ done (1024/1024 PASS, 6.39s) |
| M4 | Yosys SAT formal property check (FSM safety + bounds) | ✓ done (12-cycle BMC PASS in 7s) |
| M5 | 2-stage pipelined RTL variant + sim verification | ✓ done (1024/1024 PASS, +19% sim latency) |

## All milestones complete

Optional follow-ups:
- Run OpenLane2 at 100 MHz on `src/project_pipelined.v` to demonstrate the predicted SS WNS recovery (from −13 ns to ≈ −2 ns).
- Add `formal_log.txt` of pipelined variant (separate `forklift_pipelined.ys`).
- Submit to a real Tiny Tapeout shuttle (TT10/TT11).

## Push convention
Use **PowerShell** git (Windows Credential Manager); WSL git hangs on auth prompt.
