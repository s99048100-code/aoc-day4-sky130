"""
Compare baseline (50 MHz) vs aggressive (100 MHz) synthesis results.
Reads runs/baseline/final/metrics.json and runs/aggressive/final/metrics.json.
Emits ppa_compare.md.
"""
import json
import os
import sys

BASE_DIR = os.path.dirname(__file__)


def load(tag):
    path = os.path.join(BASE_DIR, "runs", tag, "final", "metrics.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f), path


def gf(m, key):
    v = m.get(key)
    return float(v) if v is not None else None


def fmt(v, fmt_str, fallback="n/a"):
    return format(v, fmt_str) if v is not None else fallback


try:
    base, base_path = load("baseline")
    agg, agg_path = load("aggressive")
except FileNotFoundError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

lines = []
lines.append("# PPA Comparison — 50 MHz baseline vs 100 MHz aggressive\n")
lines.append(f"- Baseline: `{base_path}`")
lines.append(f"- Aggressive: `{agg_path}`")
lines.append("")
if agg.get("_note"):
    lines.append(f"> **Note (aggressive run):** {agg['_note']}")
    lines.append("")

# --- Area ---
lines.append("## Area\n")
lines.append("| Metric | Baseline (50 MHz) | Aggressive (100 MHz) | Delta |")
lines.append("|--------|-------------------|----------------------|-------|")

b_area = gf(base, "design__instance__area") or 0
a_area = gf(agg, "design__instance__area") or 0
b_cells = base.get("design__instance__count__stdcell", "?")
a_cells = agg.get("design__instance__count__stdcell", "?")
b_util = gf(base, "design__core__utilization")
a_util = gf(agg, "design__core__utilization")

lines.append(f"| Std-cell count | {b_cells} | {a_cells} | {int(a_cells or 0) - int(b_cells or 0):+d} |")
lines.append(f"| Cell area (µm²) | {b_area:.1f} | {a_area:.1f} | {a_area - b_area:+.1f} |")
if b_util is not None and a_util is not None:
    lines.append(f"| Core utilization (%) | {b_util:.2f} | {a_util:.2f} | {a_util - b_util:+.2f} |")
lines.append("")

# --- Routing ---
lines.append("## Routing\n")
lines.append("| Metric | Baseline | Aggressive | Delta |")
lines.append("|--------|----------|------------|-------|")

b_wl = gf(base, "route__wirelength")
a_wl = gf(agg, "route__wirelength")
b_via = gf(base, "route__vias")
a_via = gf(agg, "route__vias")
b_ant = base.get("antenna__violating__nets", 0)
a_ant = agg.get("antenna__violating__nets", 0)

if b_wl is not None and a_wl is not None:
    lines.append(f"| Wire length (µm) | {b_wl:.0f} | {a_wl:.0f} | {a_wl - b_wl:+.0f} |")
if b_via is not None and a_via is not None:
    lines.append(f"| Vias | {int(b_via)} | {int(a_via)} | {int(a_via) - int(b_via):+d} |")
lines.append(f"| Antenna violations | {b_ant} | {a_ant} | — |")
lines.append("")

# --- Timing ---
lines.append("## Timing — Setup WNS (ns)\n")
lines.append("| Corner | Baseline WNS | Aggressive WNS | Delta | Status |")
lines.append("|--------|-------------|----------------|-------|--------|")

corners = [
    ("nom_tt_025C_1v80", "TT nom"),
    ("nom_ss_100C_1v60", "SS nom"),
    ("nom_ff_n40C_1v95", "FF nom"),
    ("max_ss_100C_1v60", "SS max"),
    ("min_ff_n40C_1v95", "FF min"),
]

for cid, label in corners:
    bw = gf(base, f"timing__setup__wns__corner:{cid}")
    aw = gf(agg, f"timing__setup__wns__corner:{cid}")
    bw_s = fmt(bw, ".3f")
    aw_s = fmt(aw, ".3f")
    if bw is not None and aw is not None:
        delta = aw - bw
        status = "MET" if aw >= 0 else f"FAIL ({agg.get(f'timing__setup_vio__count__corner:{cid}', '?')} vio)"
        lines.append(f"| {label} | {bw_s} | {aw_s} | {delta:+.3f} | {status} |")
    else:
        lines.append(f"| {label} | {bw_s} | {aw_s} | — | — |")
lines.append("")

# Hold
lines.append("## Timing — Hold WS (ns)\n")
lines.append("| Corner | Baseline WS | Aggressive WS | Delta |")
lines.append("|--------|------------|---------------|-------|")
for cid, label in corners:
    bh = gf(base, f"timing__hold__ws__corner:{cid}")
    ah = gf(agg, f"timing__hold__ws__corner:{cid}")
    bh_s = fmt(bh, ".3f")
    ah_s = fmt(ah, ".3f")
    if bh is not None and ah is not None:
        lines.append(f"| {label} | {bh_s} | {ah_s} | {ah - bh:+.3f} |")
    else:
        lines.append(f"| {label} | {bh_s} | {ah_s} | — |")
lines.append("")

# --- Power ---
lines.append("## Power (typical corner)\n")
lines.append("| Component | Baseline (µW) | Aggressive (µW) | Delta (µW) |")
lines.append("|-----------|--------------|-----------------|------------|")

b_int = (gf(base, "power__internal__total") or 0) * 1e6
b_sw  = (gf(base, "power__switching__total") or 0) * 1e6
b_lk  = (gf(base, "power__leakage__total") or 0) * 1e6
b_tot = b_int + b_sw + b_lk

a_int = (gf(agg, "power__internal__total") or 0) * 1e6
a_sw  = (gf(agg, "power__switching__total") or 0) * 1e6
a_lk  = (gf(agg, "power__leakage__total") or 0) * 1e6
a_tot = a_int + a_sw + a_lk

lines.append(f"| Internal  | {b_int:.1f} | {a_int:.1f} | {a_int - b_int:+.1f} |")
lines.append(f"| Switching | {b_sw:.1f}  | {a_sw:.1f}  | {a_sw - b_sw:+.1f}  |")
lines.append(f"| **Total** | **{b_tot:.1f}** | **{a_tot:.1f}** | **{a_tot - b_tot:+.1f}** |")
lines.append("")

# --- Conclusion ---
lines.append("## Speed Limit Conclusion\n")

tt_b = gf(base, "timing__setup__wns__corner:nom_tt_025C_1v80")
tt_a = gf(agg, "timing__setup__wns__corner:nom_tt_025C_1v80")
ss_b = gf(base, "timing__setup__wns__corner:nom_ss_100C_1v60")
ss_a = gf(agg, "timing__setup__wns__corner:nom_ss_100C_1v60")

tt_a_ok = tt_a is not None and tt_a >= 0
ss_a_ok = ss_a is not None and ss_a >= 0
tt_b_ok = tt_b is not None and tt_b >= 0
ss_b_ok = ss_b is not None and ss_b >= 0

lines.append(f"- **Baseline 50 MHz TT**: {'MET' if tt_b_ok else 'FAIL'} (WNS = {fmt(tt_b, '.3f')} ns)")
lines.append(f"- **Baseline 50 MHz SS**: {'MET' if ss_b_ok else 'FAIL'} (WNS = {fmt(ss_b, '.3f')} ns)")
lines.append(f"- **Aggressive 100 MHz TT**: {'MET' if tt_a_ok else 'FAIL'} (WNS = {fmt(tt_a, '.3f')} ns)")
lines.append(f"- **Aggressive 100 MHz SS**: {'MET' if ss_a_ok else 'FAIL'} (WNS = {fmt(ss_a, '.3f')} ns)")
lines.append("")

if tt_b_ok and not ss_b_ok:
    lines.append("The design closes at TT nominal 50 MHz but fails SS — the `COMB_MARK` 64-cell sweep is the")
    lines.append("critical path (~7–9 LUT levels). Slower transistors at high temperature push it over the 20 ns budget.")
    lines.append("Retiming the mark accumulator or pipelining the popcount would recover the SS corner.")
elif tt_b_ok and ss_b_ok:
    lines.append("Baseline closes at all corners at 50 MHz.")

if tt_a_ok and ss_a_ok:
    lines.append("Aggressive 100 MHz also closes — design has more timing margin than expected.")
elif tt_a_ok and not ss_a_ok:
    lines.append("100 MHz closes at TT but fails SS: speed limit is between 50 MHz (SS pass) and 100 MHz (SS fail).")
    lines.append("The `COMB_MARK` block needs pipelining to push past this point.")
else:
    lines.append("100 MHz fails at TT: design cannot run above 50 MHz without architectural changes.")

md = "\n".join(lines)
out = os.path.join(BASE_DIR, "ppa_compare.md")
with open(out, "w", encoding="utf-8") as f:
    f.write(md)
sys.stdout.buffer.write(f"Written {out}\n".encode())
sys.stdout.buffer.write(md.encode("utf-8"))
