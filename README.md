# sky130-aoc-day4-backend

AoC 2025 Day 4 forklift cellular automaton — original RTL, Sky130A / Tiny Tapeout 4×2 tile, OpenLane2 PnR, cocotb verified, KLayout GDS render.

---

## Algorithm

**Puzzle input** — a 2-D grid of scroll characters.  
A scroll is *accessible* if it has fewer than 4 occupied Moore-neighbours.

- **Part 1**: count accessible scrolls on the initial grid.  
- **Part 2**: peel accessible scrolls iteratively until the grid is stable; return total removed.

Hardware receives the 8×8 window as 8 bytes over AXI-Stream (one byte = one row, MSB = column 0). It computes both answers and returns them as 2 bytes (Part 1, then Part 2) on the same AXI-Stream interface.

```
s_tvalid/s_tdata  ──►  [tt_um_day4_forklift]  ──►  m_tvalid/m_tdata
    8 bytes (grid)                                     2 bytes (answers)
```

### FSM

```mermaid
%%{init: {'theme':'dark', 'themeVariables': {'darkMode':true, 'background':'#000000', 'primaryColor':'#1e293b', 'primaryTextColor':'#f8fafc', 'primaryBorderColor':'#94a3b8', 'lineColor':'#cbd5e1', 'mainBkg':'#1e293b'}}}%%
stateDiagram-v2
    [*] --> IDLE
    IDLE --> RX : s_tvalid
    RX --> PART1 : 8 bytes received
    PART1 --> P2_SCAN : part1 counted
    P2_SCAN --> P2_REMOVE : marks ready
    P2_REMOVE --> STABLE : removed
    STABLE --> P2_SCAN : mark_count > 0
    STABLE --> TX : mark_count == 0
    TX --> [*]
```

---

## HW vs SW

| Aspect | Hardware | Software |
|--------|----------|----------|
| Control flow | FSM (IDLE→RX→COMPUTE→TX) | Python `while` loop |
| Grid storage | 8×8 register array `grid[0:7]` | `set` of `(r, c)` tuples |
| Neighbour count | 64 parallel combinational evaluations, 3 LUT levels | `sum()` over Moore 8-neighbourhood |
| Mark phase | `COMB_MARK` — single combinational pass | list comprehension |
| Accumulate | `part2 += popcount(mark)`, 8-bit register | `total += len(accessible)` |
| Stability check | `mark_count == 0` or `iter == 64` (guard) | `len(accessible) == 0` |
| Output | AXI-Stream `m_tdata`/`m_tvalid`/`m_tready` | `print()` |

---

## Verification

### Golden model — full 136×136 puzzle

```
Grid: 136 x 136  (12038 scrolls total)
Part 1 (initial accessible):    1464
Part 2 (total removed, stable): 8409
Iterations until stable:        47

[full puzzle] Part 1 = 1464  (expected 1464)  OK
[full puzzle] Part 2 = 8409  (expected 8409)  OK

FULL PUZZLE: PASS
REGRESSION : PASS
```

### cocotb regression — 8 directed + 1024 random, Icarus Verilog

```
TEST                          STATUS  SIM TIME (ns)  REAL TIME (s)
test.test_regression           PASS        4540.00           0.06
test.test_random_vectors       PASS      547620.00           6.39
TESTS=2 PASS=2 FAIL=0 SKIP=0
```

- Directed: 8 hand-built corner cases (empty / full / checker / single corner / surrounded centre / 3×3 block / two clusters / puzzle-window).
- Random: 1024 deterministic vectors (`seed = 0xC0DECAFE + i`), all match the Python golden model bit-for-bit.

Iteration-count histogram from the random run (= how many peel iterations the DUT needed before stable):

| iters | count | % |
|------:|------:|---:|
| 1 | 1 | 0.1% |
| 2 | 185 | 18.1% |
| 3 | 325 | 31.7% |
| 4 | 249 | 24.3% |
| 5 | 162 | 15.8% |
| 6 | 62 | 6.1% |
| 7 | 28 | 2.7% |
| 8 | 7 | 0.7% |
| 9 | 3 | 0.3% |
| 10 | 2 | 0.2% |

No 8×8 random window converged in more than 10 iterations — well under the `iter_cnt == 64` watchdog.

Full log: `docs/cocotb_log.txt`.

---

## Sign-off Numbers

Baseline run: 50 MHz, OpenLane2 / Sky130A HD.

| Metric | Value |
|--------|-------|
| Die | 670 × 434 µm |
| Core | 658.72 × 410.72 µm |
| Std-cell instances | 5745 |
| Cell area | 19870.3 µm² |
| Total wire length | 40779 µm |
| Vias | 12068 |
| Antenna violations | 0 |
| DRC violations | 0 |
| TT nom setup WNS | 0.000 ns (MET) |
| Hold WNS (FF min) | 0.107 ns (MET) |
| Total power (TT nom) | 895.6 µW |

SS corner fails (WNS −13.016 ns) — see **Critical Path** below.

---

## Architecture Rationale

**Why 8×8?**  
The TT user pin width is 8 (`ui_in[7:0]`). One byte = one row makes RX a clean 8-cycle stream with no packing logic. 64 cells fit in eight 8-bit registers — the entire grid is ~64 FF, comfortably small for a TT 4×2 tile.

**Why fully-combinational `COMB_MARK`?**  
Each iteration of the peel does: compute neighbour count for all 64 cells → mark accessible cells → accumulate `part2` → AND-NOT the mark back into `grid`. Doing the whole thing combinationally lets one peel iteration finish in one cycle. The full puzzle converges in ≤ 47 iterations, so worst-case compute = 47 cycles = 940 ns @ 50 MHz. Trades silicon area (parallel popcount × 64) for latency.

**Bandwidth.**  
RX = 8 bytes / 8 cycles = 50 MB/s sustained @ 50 MHz handshake. Compute = ≤ 64 cycles. TX = 2 bytes / 2 cycles. End-to-end window throughput = 1 window per ~76 cycles = 1.52 µs. The full 136×136 puzzle is 17×17 = 289 windows = 440 µs of pure HW time (ignoring host overhead).

---

## Critical Path (post-PNR STA, SS corner)

From `runs/baseline/54-openroad-stapostpnr/max_ss_100C_1v60/max.rpt` — worst violated path:

```
Startpoint:  grid[0][2]  (FF Q, sky130_fd_sc_hd__dfxtp_4)
Endpoint:    another grid[*][*] FF (mark feedback)
WNS at SS:   −13.205 ns  (slack VIOLATED)
Logic depth: ~30 cells along the path
```

The path traces the popcount of 8 Moore neighbours through a chain of `xor2/xnor2/a2111o/o211a` cells, then a `< 4` comparator, then the `grid AND ~mark` write-back. Roughly:

```
grid[r][c]  ──►  8× xor2/xnor2  ──►  popcount adder tree  ──►
                     (~12 cells)        (~10 cells)
            ──►  <4 comparator  ──►  AND ~mark  ──►  grid_n[r][c]
                     (~4 cells)         (~2 cells)
```

At TT nominal, this measures ~20 ns / 50 MHz = MET (WNS 0.000). At SS the same logic blows out to ~33 ns due to slow PMOS, which is exactly the −13 ns slack.

---

## Why It Won't Run at 100 MHz

The path above is fundamentally O(`adder_tree_depth + comparator + AND`). At 100 MHz (10 ns target) the logic levels alone exceed the budget at TT — confirmed by `−8.854 ns` WNS at TT in the aggressive run (which crashed at CTS, so the number is pre-CTS upper-bound; it is **not** comparable to the baseline post-route number, just an architectural ceiling).

To close 100 MHz the combinational sweep must be split. Two options, neither implemented in this baseline:

| Option | New stages | Iter latency | Δ FF | Expected SS WNS |
|--------|-----------|--------------|------|-----------------|
| Register `nbr_count[r][c]` | 2 | 2× | +256 (4-bit × 64) | ~−2 ns (close-able with retiming) |
| Process 2-row strips serially | 4 | 4× | +128 | clean MET at SS |

The 2-stage variant is sketched in M5 of `CHECKPOINT_PHASE3.md` but defers to future work; the baseline RTL is intentionally kept single-cycle for clarity.

---

## Re-running the Flow at 100 MHz

> **Caveat:** the aggressive flow crashed at OpenROAD.CTS (step 34/74). The numbers below are from `stamidpnr` (step 30/74, post-global-placement, pre-CTS). They are **not** like-for-like with the baseline post-route numbers — clock skew, hold buffers, and final routing parasitics are missing. Read them as an architectural ceiling, not a final result.

| Corner | Baseline WNS (50 MHz, post-route) | Aggressive WNS (100 MHz, pre-CTS) |
|--------|-----------------------------------|------------------------------------|
| TT nom | 0.000 ns | −8.854 ns |
| SS nom | −13.016 ns | −25.838 ns |
| FF nom | 0.000 ns | −1.322 ns |

Power numbers below are also pre-CTS for the aggressive column.

| Component | Baseline (µW) | Aggressive pre-CTS (µW) | Delta |
|-----------|--------------|-----------------|-------|
| Internal | 547.4 | 752.0 | +204.5 |
| Switching | 348.2 | 382.8 | +34.6 |
| **Total** | **895.6** | **1134.7** | **+239.1** |

100 MHz does not close at TT even before CTS adds clock-tree pessimism, so this RTL is **not 100 MHz-capable** without the architectural change in *Why It Won't Run at 100 MHz* above.

Full comparison: `ppa_compare.md`.

---

## Layout

![layout](https://github.com/s99048100-code/aoc-day4-sky130/raw/main/docs/klayout_layout.png?v=3)

---

## Repo Layout

```
src/
  project.v              RTL — FSM + 8×8 cellular automaton core
test/
  test.py                cocotb regression (8 vectors)
  Makefile               Icarus Verilog + cocotb runner
runs/
  baseline/              50 MHz OpenLane2 run
    final/metrics.json
    final/klayout_gds/tt_um_day4_forklift.klayout.gds
  aggressive/            100 MHz attempt (partial, crashed at CTS)
    final/metrics.json
docs/
  klayout_layout.png
  klayout_caravel_context.png
  design_notes.md
  cocotb_log.txt
  golden_model_output.txt
day4_golden_model.py     reference Python implementation
ppa_report.md            baseline PPA numbers
ppa_compare.md           50 vs 100 MHz comparison
gen_klayout_images.py    KLayout headless render script
info.yaml                Tiny Tapeout project metadata
```

---

## Reproducing

```bash
# Puzzle input — login required, not included (AoC policy)
# https://adventofcode.com/2025/day/4/input  → save as puzzle_input.txt

# Golden model
python day4_golden_model.py full-grid

# cocotb regression
cd test && make

# Re-run PnR (baseline)
openlane --run-all runs/baseline

# Regenerate KLayout renders
pip install klayout
python gen_klayout_images.py
```

---

## License & Credits

Apache-2.0 — see `LICENSE`.

RTL (`src/project.v`) is original work by the repository maintainer.  
AoC 2025 Day 4 puzzle by Eric Wastl (adventofcode.com).  
Puzzle input: https://adventofcode.com/2025/day/4/input

---

Related: [sky130-aoc-day12-backend](https://github.com/s99048100-code/sky130-aoc-day12-backend) — backend study on an existing RTL; this repo is the follow-up with original RTL.

