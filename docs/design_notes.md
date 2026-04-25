# Design Notes — tt_um_day4_forklift

## 1. Why 8×8?

The TT pin budget is the binding constraint: `ui_in[7:0]` = 8 bits = one grid row.
Sending a 16×16 grid at 1 byte/cycle would require 16 RX cycles instead of 8 and a `4-bit rx_idx`; more importantly the output counter would overflow 8 bits (max scrolls = 256 > 255).
An 8×8 cap keeps Part1/Part2 ≤ 64, fits in one byte each, and maps cleanly to the TT AXI-stream pin convention without any packetisation logic.

## 2. Critical path

The combinational hot spot is `COMB_MARK` in `src/project.v`.
Every clock cycle in `S_COMPUTE`, the block sweeps all 64 cells and, for each set cell, calls `nbr_count()` — itself an 8-entry loop summing 1-bit grid values into a 4-bit sum.
In the worst case the synthesiser must propagate through:

```
grid[r][c]  →  8× (grid[rr][cc] adder tree)  →  comparison (<4)  →  mark[r][c]  →  popcount → part2_q
```

The adder tree for one `nbr_count` is ≤ 3 levels of LUTs (8 inputs, 4-bit sum).
64 mark bits then feed a reduce-add for `mark_count` (8-bit popcount, ~3 more LUT levels).
Estimated critical-path depth: ~7–9 LUT levels.  At sky130 HD nominal corner the target is 20 ns (50 MHz) — 待 STA 確認.

## 3. Worst-case cycle count

| Phase     | Formula          | Max cycles |
|-----------|------------------|------------|
| S_RX      | 8 bytes, 1/cycle | 8          |
| S_COMPUTE | iters + 1 check  | 65 (guard) |
| S_TX_P1   | wait m_tready    | ≥1         |
| S_TX_P2   | wait m_tready    | ≥1         |
| **Total** |                  | **≥75**    |

At 50 MHz: 75 × 20 ns = **1.5 µs** per 8×8 query.
The golden model measured 47 iterations on the 136×136 full puzzle, so real worst-case for any 8×8 sub-grid is closer to 20–30 cycles of COMPUTE.

## 4. Cost of upgrading to 16×16

A 16×16 grid needs 256 cells in `COMB_MARK`.
Back-of-envelope:

- `nbr_count` loops stay the same depth; 4× more instances → 4× the LUT count.
- `mark_count` popcount widens from 8-bit to 9-bit (max 256 marks).
- `part1_q`, `part2_q` need 9 bits each.
- RX phase doubles to 16 cycles; `rx_idx` widens from 3- to 4-bit.
- Grid storage: 256 × 1-bit FFs vs 64 today — still trivial.

Net area impact: roughly 4× logic, same number of FFs (256 → still fits in TT 4×2 tile).
The bigger risk is timing: the 256-cell popcount adds ~2 LUT levels to the critical path.
At 50 MHz this is probably fine; at 100 MHz it likely fails without retiming the mark accumulator.

## 5. Comparison with Day 12

Day 12 (`sky130-aoc-day12-backend`) uses Robert Saab's pre-written RTL — a range-finder FSM, unmodified.
This project is wholly original RTL.

Key differences:

| | Day 12 | Day 4 |
|---|---|---|
| RTL author | Robert Saab | this project |
| Algorithm | BFS/DFS range-finder | cellular automaton peel |
| Combinational core | ~10 LUT levels (待 STA) | `COMB_MARK` sweep, ~7–9 LUT levels |
| Max iterations | problem-dependent | 64 (HW guard), 47 on full puzzle |
| Proven timing at 50 MHz | TT closes (from memory: +1.95 ns SS) | 待 STA 確認 |
| Proven timing at 100 MHz | fails (SS −5.47 ns) | 待 STA 確認 |

The Day 12 100 MHz failure was traced to the AXI byte interface feeding a long FSM chain without retiming.
Day 4's critical path is the `COMB_MARK` sweep, which is purely combinational with no cross-cycle dependency — it should be easier to pipeline if higher frequency is needed.
