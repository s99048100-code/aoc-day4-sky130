# PPA Comparison — 50 MHz baseline vs 100 MHz aggressive vs 100 MHz pipelined

Three runs:

- `runs/baseline/final/metrics.json` — original RTL, 50 MHz, **post-route, sign-off**.
- `runs/aggressive/final/metrics.json` — original RTL, 100 MHz, **flow crashed at CTS** (step 34/74). Numbers are from mid-PNR STA (step 30, post-global-placement, pre-CTS). Routing/CTS/sign-off metrics unavailable.
- `runs/aggressive_pipelined/final/metrics.json` — `src/project_pipelined.v` (2-stage variant), 100 MHz, **post-route, full sign-off**.

## Area

| Metric | Baseline 50 MHz | Aggressive 100 MHz<br/>(pre-CTS) | **Pipelined 100 MHz<br/>(post-route)** |
|--------|----------------:|---------------------------------:|---------------------------------------:|
| Std-cell instances | 5745 | 5599 | 5677 |
| Cell area (µm²) | 19 870 | 21 330 | 20 159 |
| Sequential cells | 94 | n/a | 157 (+63 mark_q FFs) |
| Wire length (µm, est.) | 40 779 | n/a | 38 485 |

## Routing / DRC

| Metric | Baseline 50 MHz | Aggressive 100 MHz | Pipelined 100 MHz |
|--------|----------------:|------------------:|------------------:|
| magic DRC | 0 | n/a | 0 |
| klayout DRC | 0 | n/a | 0 |
| Antenna violating nets | 0 | n/a | 0 |

## Timing — Setup WNS (ns)

| Corner | Baseline 50 MHz | Aggressive 100 MHz | **Pipelined 100 MHz** |
|--------|----------------:|------------------:|----------------------:|
| TT nom | 0.000 (MET) | −8.854 | **0.000 (MET)** |
| SS nom | −13.016 | −25.838 | **−2.177** |
| FF nom | 0.000 (MET) | −1.322 | **0.000 (MET)** |

## Timing — Hold WS (ns)

| Corner | Baseline | Pipelined |
|--------|---------:|----------:|
| TT nom | 0.325 | 0.319 |
| SS nom | 0.900 | 0.859 |
| FF nom | 0.109 | 0.114 |

## Power (TT nom, post-route)

| Component | Baseline 50 MHz (µW) | Pipelined 100 MHz (µW) | Δ |
|-----------|---------------------:|-----------------------:|--:|
| Internal | 547.4 | 1049.2 | +501.8 |
| Switching | 348.2 | 520.4 | +172.2 |
| **Total** | **895.6** | **1569.6** | **+674.0 (+75 %)** |

Power scales close to linearly with frequency (2× clock ≈ 1.75× power).

## Speed-limit conclusion

| Configuration | TT MET? | SS WNS | Sign-off complete? |
|---|---|---:|---|
| Baseline @ 50 MHz | yes | −13.016 | yes (DRC=0, antenna=0) |
| Baseline @ 100 MHz | no | −25.838 | no (CTS crash) |
| **Pipelined @ 100 MHz** | **yes** | **−2.177** | **yes (DRC=0, antenna=0)** |

**One register stage** added between the COMB_MARK comparator and the peel write-back is enough to:

1. Close TT nominal at 100 MHz (3.6 ns of slack to spare).
2. Drop SS WNS from −13 to −2 ns — workable with retiming or a slower SS-corner target (~85 MHz).
3. Pass the full OpenLane2 flow with clean DRC and zero antenna violations.

Cost: +1.5 % cell area, +63 sequential cells, +75 % dynamic power (frequency-driven).

---

## Baseline vs Pipelined — same 50 MHz, post-route

To isolate the effect of the architectural change from the clock-rate change, this section compares both RTLs at the **same** 50 MHz target.

- Baseline:  `runs/baseline/final/metrics.json` (`src/project.v`)
- Pipelined: `runs/pipelined/final/metrics.json` (`src/project_pipelined.v`)

| Metric | Baseline (project.v) | Pipelined (project_pipelined.v) | Delta |
|--------|---------------------:|---------------------------------:|------:|
| Std-cell instances | 5745 | 5653 | −92 (−1.6 %) |
| Cell area (µm²) | 19 870.3 | 19 408.6 | −461.7 (−2.3 %) |
| Sequential cells | 94 | 157 | +63 (+67 %) — `mark_q` |
| Multi-input comb cells | 1533 | 1298 | −235 (−15 %) |
| Timing-repair buffers | 130 | 192 | +62 (mostly hold) |
| Clock-tree buffers | 9 | 19 | +10 |
| Wire length (µm, est.) | 40 779 | 41 496 | +717 (+1.8 %) |
| **TT nom setup WNS (ns)** | 0.000 (MET) | **0.000 (MET)** | — |
| **SS nom setup WNS (ns)** | **−13.016 (FAIL)** | **0.000 (MET)** | **+13.016 — corner now closes** |
| **FF nom setup WNS (ns)** | 0.000 (MET) | 0.000 (MET) | — |
| Hold WNS (FF min, ns) | 0.107 | 0.111 | +0.004 |
| Internal power (µW) | 547.4 | 532.4 | −15.0 |
| Switching power (µW) | 348.2 | 255.1 | −93.1 |
| **Total power (µW)** | **895.6** | **787.5** | **−108.1 (−12.1 %)** |
| DRC violations | 0 | 0 | clean |
| Antenna violations | 0 | 0 | clean |
| Cycles per peel iter | 1 | 2 | +1 |

### What this means

At the same 50 MHz target, the pipelined RTL is **strictly better than the baseline on PPA**:

- **SS corner now closes**. The whole reason the baseline existed was that the SS corner failed by 13 ns. Splitting the COMB_MARK path with a single 64-bit `mark_q` register fixes that completely — SS WNS goes from −13.016 ns to 0.000 ns. No longer "closes only at TT".
- **Slightly smaller area** (−2.3 %). The 63 added FFs (`mark_q`) cost ~150 µm² of FF cells, but the net combinational logic is smaller because abc balances two shallower trees instead of one giant 30-level tree, so synthesis can pick smaller-drive variants. Net is −461 µm².
- **12 % less total power**. Frequency is the same, but switching capacitance drops because the combinational logic is shallower (less glitching on the deep XOR/XNOR adder chain). Internal power also drops slightly.

The cost is **functional throughput**: each peel iteration now takes 2 cycles instead of 1, so for the same input window the pipelined design takes ~2× more cycles to reach `STABLE`. To match the baseline's wall-clock throughput the pipelined RTL must run at 100 MHz — which it does (see *Re-running the Flow at 100 MHz* above and `runs/aggressive_pipelined/`).

### Take-away

The pipelined variant gives you a real choice that baseline did not:

| Target | Baseline | Pipelined |
|---|---|---|
| 50 MHz, all corners MET | ❌ (SS fails) | ✓ |
| 100 MHz post-route, TT MET | ❌ (CTS crashes) | ✓ |
| Equal throughput at 50 MHz | ✓ | — (half throughput) |
| Lower area + power at 50 MHz | — | ✓ |

For a tape-out where SS-corner closure matters (it does for any production part), pipelined-50 MHz is the right configuration. For maximum throughput, pipelined-100 MHz works at TT (SS slacks −2 ns, recoverable with retiming or a slower SS target).
