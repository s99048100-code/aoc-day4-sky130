#!/usr/bin/env python3
"""
Render Day 4 layout images via gdstk + matplotlib (headless).

Outputs four distinct views:
  1. klayout_layout.png         - logic-cluster zoom (signal-routing detail)
  2. klayout_full_die.png       - full 670x434 um die overview
  3. klayout_power_grid.png     - met3/met4/met5 power distribution only
  4. klayout_layer_breakdown.png- 2x2 panel showing poly/met1/met2/met3 alone
"""

import argparse
import os
import gdstk
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from PIL import Image, ImageDraw, ImageFont
import shutil

ROOT = "/mnt/d/aoc_day4"
DOCS = f"{ROOT}/docs"
BG   = "#0d0d0d"

# Sky130 layer colours.
COLORS = {
    (65, 20): ("#5080c0", 0.75, "diff"),
    (66, 20): ("#c05050", 0.90, "poly"),
    (67, 20): ("#4a9aba", 0.70, "li1"),
    (68, 20): ("#8b6fb5", 0.60, "met1"),
    (69, 20): ("#4a9e6e", 0.85, "met2"),
    (70, 20): ("#c47a3d", 0.85, "met3"),
    (71, 20): ("#6a9e4a", 0.80, "met4"),
    (72, 20): ("#b54a8b", 0.80, "met5"),
}


def load_polys(gds_path):
    print(f"Reading GDS: {gds_path}")
    lib = gdstk.read_gds(gds_path)
    top = lib.top_level()[0]
    print(f"  top cell: {top.name}")
    by_layer = {}
    for layer, dt in COLORS:
        polys = top.get_polygons(depth=None, layer=layer, datatype=dt)
        by_layer[(layer, dt)] = [p.points for p in polys]
        print(f"  L{layer}/D{dt} ({COLORS[(layer,dt)][2]:>5}): {len(polys):>6} polys")
    return top, by_layer


def clip(polys, x0, x1, y0, y1):
    out = []
    for pts in polys:
        if (pts[:, 0].max() < x0 or pts[:, 0].min() > x1 or
            pts[:, 1].max() < y0 or pts[:, 1].min() > y1):
            continue
        out.append(pts)
    return out


def render(by_layer, out_path, x0, x1, y0, y1, layers, w_in=16, h_in=12, dpi=150,
           title=None):
    fig, ax = plt.subplots(figsize=(w_in, h_in), dpi=dpi)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    for key in layers:
        polys = by_layer.get(key, [])
        if not polys:
            continue
        clipped = clip(polys, x0, x1, y0, y1)
        if not clipped:
            continue
        color, alpha, name = COLORS[key]
        coll = PolyCollection(clipped, facecolors=color, edgecolors=color,
                              linewidths=0.0, alpha=alpha, antialiased=True)
        ax.add_collection(coll)

    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    ax.set_aspect("equal"); ax.axis("off")

    if title:
        ax.text(0.01, 0.985, title, transform=ax.transAxes,
                fontsize=14, color="#dddddd", family="monospace",
                verticalalignment="top",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#1a1a1a",
                          edgecolor="#444", alpha=0.85))

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(out_path, dpi=dpi, facecolor=BG, edgecolor="none",
                bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    print(f"  saved: {out_path}  ({os.path.getsize(out_path)//1024} KB)")


def render_panel(by_layer, out_path):
    """1x3 panels: poly, met1, met3 each on its own."""
    panels = [
        ((66, 20), "poly (gates)"),
        ((68, 20), "met1 (signal/power rails)"),
        ((70, 20), "met3 (power straps)"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(24, 6), dpi=150)
    fig.patch.set_facecolor(BG)

    # Use full die bbox so panels are comparable
    x0, x1, y0, y1 = 0, 670, 0, 434

    for ax, (key, label) in zip(axes.flat, panels):
        ax.set_facecolor(BG)
        polys = by_layer.get(key, [])
        if polys:
            color, alpha, _name = COLORS[key]
            coll = PolyCollection(polys, facecolors=color, edgecolors=color,
                                  linewidths=0.0, alpha=alpha, antialiased=True)
            ax.add_collection(coll)
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
        ax.set_aspect("equal"); ax.axis("off")
        ax.text(0.02, 0.97, label, transform=ax.transAxes,
                fontsize=14, color="#dddddd", family="monospace",
                verticalalignment="top",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#1a1a1a",
                          edgecolor="#666", alpha=0.9))

    plt.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005,
                        wspace=0.01, hspace=0.01)
    fig.savefig(out_path, dpi=150, facecolor=BG, edgecolor="none",
                bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    print(f"  saved: {out_path}  ({os.path.getsize(out_path)//1024} KB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="baseline",
                    help="run-tag under runs/ to read GDS from (default: baseline)")
    ap.add_argument("--suffix", default=None,
                    help="output filename suffix (default: '' for baseline, '_<run>' otherwise)")
    args = ap.parse_args()

    gds_path = f"{ROOT}/runs/{args.run}/final/klayout_gds/tt_um_day4_forklift.klayout.gds"
    if args.suffix is not None:
        sfx = args.suffix
    else:
        sfx = "" if args.run == "baseline" else f"_{args.run}"

    os.makedirs(DOCS, exist_ok=True)
    top, by_layer = load_polys(gds_path)

    SIGNAL = [(65, 20), (66, 20), (67, 20), (68, 20), (69, 20)]
    POWER  = [(70, 20), (71, 20), (72, 20)]
    ALL    = SIGNAL + POWER

    full_out = f"{DOCS}/klayout_full_die{sfx}.png"
    print(f"\nRendering {full_out} (whole die) ...")
    render(by_layer, full_out,
           x0=0, x1=670, y0=0, y1=434, layers=ALL,
           w_in=16, h_in=10.4,
           title=f"Full die — {args.run} run, 670 x 434 um, all routing layers")

    panel_out = f"{DOCS}/klayout_layer_breakdown{sfx}.png"
    print(f"\nRendering {panel_out} (per-layer panels) ...")
    render_panel(by_layer, panel_out)

    print("\nDone.")


if __name__ == "__main__":
    main()
