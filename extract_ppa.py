"""
Read runs/<tag>/final/metrics.json and emit a ppa_report.md.
Usage: python3 extract_ppa.py [run_tag]   (default: baseline)
"""
import json
import sys
import os

TAG = sys.argv[1] if len(sys.argv) > 1 else "baseline"
METRICS = os.path.join(os.path.dirname(__file__), "runs", TAG, "final", "metrics.json")

with open(METRICS) as f:
    m = json.load(f)


def get(key, default="n/a"):
    v = m.get(key, default)
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def get_f(key):
    v = m.get(key)
    return float(v) if v is not None else None


lines = []
lines.append(f"# PPA Report — {TAG}\n")
lines.append(f"Source: `{METRICS}`\n")

# Area
die_bbox = m.get("design__die__bbox", "?")
core_bbox = m.get("design__core__bbox", "?")
inst_area = get_f("design__instance__area") or 0
stdcells = m.get("design__instance__count__stdcell", "?")
util = get_f("design__core__utilization")

lines.append("## Area\n")
lines.append(f"| Metric | Value |")
lines.append(f"|--------|-------|")
lines.append(f"| Die    | `{die_bbox}` µm |")
lines.append(f"| Core   | `{core_bbox}` µm |")
lines.append(f"| Std-cell instances | {stdcells} |")
lines.append(f"| Cell area | {inst_area:.1f} µm² |")
if util is not None:
    lines.append(f"| Core utilization | {util:.2f}% |")
lines.append("")

# Routing
wire_length = get_f("route__wirelength")
vias = get_f("route__vias")
ant_vio = m.get("antenna__violating__nets", 0)
lines.append("## Routing\n")
lines.append(f"| Metric | Value |")
lines.append(f"|--------|-------|")
if wire_length is not None:
    lines.append(f"| Total wire length | {wire_length:.0f} µm |")
if vias is not None:
    lines.append(f"| Vias | {int(vias)} |")
lines.append(f"| Antenna violations | {ant_vio} |")
lines.append("")

# Timing (all corners)
lines.append("## Timing\n")
lines.append(f"| Corner | Setup WS (ns) | Setup TNS (ns) | Setup vio | Hold WS (ns) |")
lines.append(f"|--------|--------------|----------------|-----------|--------------|")
corners = [
    ("nom_tt_025C_1v80", "TT nom"),
    ("nom_ss_100C_1v60", "SS nom"),
    ("nom_ff_n40C_1v95", "FF nom"),
    ("max_ss_100C_1v60", "SS max"),
    ("min_ff_n40C_1v95", "FF min"),
]
for corner_id, label in corners:
    wns = get_f(f"timing__setup__wns__corner:{corner_id}")
    tns = get_f(f"timing__setup__tns__corner:{corner_id}")
    vio = m.get(f"timing__setup_vio__count__corner:{corner_id}", "?")
    hws = get_f(f"timing__hold__ws__corner:{corner_id}")
    wns_s = f"{wns:.3f}" if wns is not None else "n/a"
    tns_s = f"{tns:.1f}" if tns is not None else "n/a"
    hws_s = f"{hws:.3f}" if hws is not None else "n/a"
    lines.append(f"| {label} | {wns_s} | {tns_s} | {vio} | {hws_s} |")
lines.append("")

# Power (at typical corner)
p_int = get_f("power__internal__total") or 0
p_sw = get_f("power__switching__total") or 0
p_lk = get_f("power__leakage__total") or 0
p_tot = p_int + p_sw + p_lk
lines.append("## Power (typical corner, µW)\n")
lines.append(f"| Component | µW |")
lines.append(f"|-----------|-----|")
lines.append(f"| Internal | {p_int*1e6:.1f} |")
lines.append(f"| Switching | {p_sw*1e6:.1f} |")
lines.append(f"| Leakage | {p_lk*1e9:.2f} nW |")
lines.append(f"| **Total** | **{p_tot*1e6:.1f}** |")
lines.append("")

# Sign-off summary
lines.append("## Sign-off\n")
tt_wns = get_f("timing__setup__wns__corner:nom_tt_025C_1v80")
ss_wns = get_f("timing__setup__wns__corner:nom_ss_100C_1v60")
h_ws = get_f("timing__hold__ws")
setup_ok = tt_wns is not None and tt_wns >= 0
hold_ok = h_ws is not None and h_ws >= 0
lines.append(f"- TT 50 MHz setup: {'**MET** ✓' if setup_ok else '**FAIL** ✗'}  (WNS = {tt_wns:.3f} ns)" if tt_wns is not None else "- TT setup: n/a")
lines.append(f"- SS 50 MHz setup: {'MET' if (ss_wns or -1) >= 0 else 'FAIL'} (WNS = {ss_wns:.3f} ns)" if ss_wns is not None else "- SS setup: n/a")
lines.append(f"- Hold (all corners): {'MET' if hold_ok else 'FAIL'} (WS = {h_ws:.3f} ns)" if h_ws is not None else "- Hold: n/a")
lines.append("")

md = "\n".join(lines)
out_path = os.path.join(os.path.dirname(__file__), f"ppa_report.md")
with open(out_path, "w") as f:
    f.write(md)
print(f"Written {out_path}")
print(md)
