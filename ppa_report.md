# PPA Report — baseline

Source: `/mnt/d/aoc_day4/runs/baseline/final/metrics.json`

## Area

| Metric | Value |
|--------|-------|
| Die    | `0.0 0.0 670.0 434.0` µm |
| Core   | `5.52 10.88 664.24 421.6` µm |
| Std-cell instances | 5745 |
| Cell area | 19870.3 µm² |

## Routing

| Metric | Value |
|--------|-------|
| Total wire length | 40779 µm |
| Vias | 12068 |
| Antenna violations | 0 |

## Timing

| Corner | Setup WS (ns) | Setup TNS (ns) | Setup vio | Hold WS (ns) |
|--------|--------------|----------------|-----------|--------------|
| TT nom | 0.000 | 0.0 | 0 | 0.325 |
| SS nom | -13.016 | -1059.3 | 88 | 0.900 |
| FF nom | 0.000 | 0.0 | 0 | 0.109 |
| SS max | -13.205 | -1076.7 | 88 | 0.908 |
| FF min | 0.000 | 0.0 | 0 | 0.107 |

## Power (typical corner, µW)

| Component | µW |
|-----------|-----|
| Internal | 547.4 |
| Switching | 348.2 |
| Leakage | 32.53 nW |
| **Total** | **895.6** |

## Sign-off

- TT 50 MHz setup: **MET** ✓  (WNS = 0.000 ns)
- SS 50 MHz setup: FAIL (WNS = -13.016 ns)
- Hold (all corners): MET (WS = 0.107 ns)
