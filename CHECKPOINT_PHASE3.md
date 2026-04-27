# CHECKPOINT_PHASE3 — Portfolio Hardening

Plan file: `~/.claude/plans/dazzling-painting-deer.md`

## Milestones

| # | Title | Status |
|---|-------|--------|
| M1 | Cleanup (delete phase2 checkpoint, unify docs) | ✓ done |
| M2 | README architecture rationale + critical-path analysis | ✓ done |
| M3 | cocotb 1024-vector random regression + iter histogram | ✓ done (1024/1024 PASS, 6.39s) |
| M4 | SBY formal property check (FSM safety + bounds) | pending |
| M5 | 2-stage pipelined RTL variant (stretch) | pending |

## Resume command

Next session: pick up M4 (SBY formal property check).
- Check if `sby` and `yosys` are installed in WSL: `wsl -e bash -c "which sby yosys"`.
- If yes: create `formal/properties.sv`, `formal/forklift.sby`, `formal/run_formal.sh`.
  Properties: `iter_cnt <= 64`, `state` always in {IDLE,RX,COMPUTE,TX_P1,TX_P2}, `part1_q <= 64`, `part2_q <= 64`.
- If `sby` not installed: fall back to a `yosys` `sat` script proving the same bounds (no `assume`-based liveness, just safety).
- Run, capture to `docs/formal_log.txt`.
- Commit: `verif: add SBY formal properties for FSM safety + bounds`.

## Push convention
Use **PowerShell** git (Windows Credential Manager); WSL git hangs on auth prompt.
