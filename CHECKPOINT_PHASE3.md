# CHECKPOINT_PHASE3 — Portfolio Hardening

Plan file: `~/.claude/plans/dazzling-painting-deer.md`

## Milestones

| # | Title | Status |
|---|-------|--------|
| M1 | Cleanup (delete phase2 checkpoint, unify docs) | ✓ done |
| M2 | README architecture rationale + critical-path analysis | pending |
| M3 | cocotb 1024-vector random regression + iter histogram | pending |
| M4 | SBY formal property check (FSM safety + bounds) | pending |
| M5 | 2-stage pipelined RTL variant (stretch) | pending |

## Resume command

Next session: pick up M2.
- Read `runs/baseline/54-openroad-stapostpnr/max_ss_100C_1v60/max.rpt` for critical-path data.
- Insert 3 new sections in `README.md` between **Sign-off Numbers** and **Re-running at 100 MHz** (Architecture Rationale, Critical Path, Why It Won't Run at 100 MHz).
- Add caveat banner at top of `ppa_compare.md` noting aggressive numbers are pre-CTS.
- Commit message: `docs: add architecture rationale and critical-path analysis`.

## Push convention
Use **PowerShell** git (Windows Credential Manager); WSL git hangs on auth prompt.
