# PPA Comparison — 50 MHz baseline vs 100 MHz aggressive

- Baseline: `runs\baseline\final\metrics.json`
- Aggressive: `runs\aggressive\final\metrics.json`

> **Note (aggressive run):** Partial run — flow crashed at OpenROAD.CTS (step 34/~60). Numbers are from mid-PNR STA (step 30, post-global-placement, pre-CTS). Routing metrics unavailable.

## Area

| Metric | Baseline (50 MHz) | Aggressive (100 MHz) | Delta |
|--------|-------------------|----------------------|-------|
| Std-cell count | 5745 | 5599 | -146 |
| Cell area (µm²) | 19870.3 | 21330.5 | +1460.2 |

## Routing

| Metric | Baseline | Aggressive | Delta |
|--------|----------|------------|-------|
| Antenna violations | 0 | n/a (routing incomplete) | — |

## Timing — Setup WNS (ns)

| Corner | Baseline WNS | Aggressive WNS | Delta | Status |
|--------|-------------|----------------|-------|--------|
| TT nom | 0.000 | -8.854 | -8.854 | FAIL (88 vio) |
| SS nom | -13.016 | -25.838 | -12.822 | FAIL (88 vio) |
| FF nom | 0.000 | -1.322 | -1.322 | FAIL (85 vio) |
| SS max | -13.205 | n/a | — | — |
| FF min | 0.000 | n/a | — | — |

## Timing — Hold WS (ns)

| Corner | Baseline WS | Aggressive WS | Delta |
|--------|------------|---------------|-------|
| TT nom | 0.325 | 0.244 | -0.082 |
| SS nom | 0.900 | 0.641 | -0.259 |
| FF nom | 0.109 | 0.049 | -0.060 |
| SS max | 0.908 | n/a | — |
| FF min | 0.107 | n/a | — |

## Power (typical corner)

| Component | Baseline (µW) | Aggressive (µW) | Delta (µW) |
|-----------|--------------|-----------------|------------|
| Internal  | 547.4 | 752.0 | +204.5 |
| Switching | 348.2  | 382.8  | +34.6  |
| **Total** | **895.6** | **1134.7** | **+239.1** |

## Speed Limit Conclusion

- **Baseline 50 MHz TT**: MET (WNS = 0.000 ns)
- **Baseline 50 MHz SS**: FAIL (WNS = -13.016 ns)
- **Aggressive 100 MHz TT**: FAIL (WNS = -8.854 ns)
- **Aggressive 100 MHz SS**: FAIL (WNS = -25.838 ns)

The design closes at TT nominal 50 MHz but fails SS — the `COMB_MARK` 64-cell sweep is the
critical path (~7–9 LUT levels). Slower transistors at high temperature push it over the 20 ns budget.
Retiming the mark accumulator or pipelining the popcount would recover the SS corner.
100 MHz fails at TT: design cannot run above 50 MHz without architectural changes.