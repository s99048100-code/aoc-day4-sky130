# CHECKPOINT_PHASE3 — Portfolio Hardening

Plan file: `~/.claude/plans/dazzling-painting-deer.md`

## Milestones

| # | Title | Status |
|---|-------|--------|
| M1 | Cleanup (delete phase2 checkpoint, unify docs) | ✓ done |
| M2 | README architecture rationale + critical-path analysis | ✓ done |
| M3 | cocotb 1024-vector random regression + iter histogram | pending |
| M4 | SBY formal property check (FSM safety + bounds) | pending |
| M5 | 2-stage pipelined RTL variant (stretch) | pending |

## Resume command

Next session: pick up M3 (cocotb random regression).
- Add `random_grid(seed)` to `day4_golden_model.py` if missing.
- Add `test_random_vectors` and `test_coverage_summary` to `test/test.py`.
- Run `cd /mnt/d/aoc_day4/test && make` in WSL (Icarus Verilog needed).
- Capture log to `docs/cocotb_log.txt`.
- Update README Verification section: "8 directed + 1024 random, 1032/1032 PASS".
- Commit: `test: add 1024-vector random regression + iteration histogram`.

## Push convention
Use **PowerShell** git (Windows Credential Manager); WSL git hangs on auth prompt.
