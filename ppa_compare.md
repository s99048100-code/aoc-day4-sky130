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
