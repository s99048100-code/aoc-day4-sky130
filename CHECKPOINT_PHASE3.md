# CHECKPOINT_PHASE3 — Portfolio Hardening

Plan file: `~/.claude/plans/dazzling-painting-deer.md`

## Milestones

| # | Title | Status |
|---|-------|--------|
| M1 | Cleanup (delete phase2 checkpoint, unify docs) | ✓ done |
| M2 | README architecture rationale + critical-path analysis | ✓ done |
| M3 | cocotb 1024-vector random regression + iter histogram | ✓ done (1024/1024 PASS, 6.39s) |
| M4 | Yosys SAT formal property check (FSM safety + bounds) | ✓ done (12-cycle BMC PASS in 7s) |
| M5 | 2-stage pipelined RTL variant (stretch) | pending |

## Resume command

Next session: pick up M5 (2-stage pipelined RTL variant).
- Create `src/project_pipelined.v` — same module name `tt_um_day4_forklift`, but register `nbr_count_q[r][c]` between `grid` and `mark`.
- Add `VARIANT ?= baseline` to `test/Makefile` so `VARIANT=pipelined make` swaps the source.
- Run cocotb on the pipelined variant — must still match golden model (latency may differ but P1/P2 results identical).
- Optional: run OpenLane2 at 100 MHz on the pipelined variant; if it closes, append column to `ppa_compare.md`.
- Commit: `rtl: add 2-stage pipelined variant + sim verification`.

M5 is a **stretch goal** — defer if token budget tight.

## Push convention
Use **PowerShell** git (Windows Credential Manager); WSL git hangs on auth prompt.
