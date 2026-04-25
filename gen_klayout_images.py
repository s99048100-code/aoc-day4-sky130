#!/usr/bin/env python3
"""
Render Day 4 layout images via gdstk + matplotlib (headless).

Image 1 (klayout_layout.png):  zoomed to logic-cluster bbox
                               (where met2 signal routing is dense).
Image 2 (klayout_caravel_context.png): same crop + white 4x2 tile outline.
"""

import os
import gdstk
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from PIL import Image, ImageDraw, ImageFont
import shutil

GDS  = "/mnt/d/aoc_day4/runs/baseline/final/klayout_gds/tt_um_day4_forklift.klayout.gds"
OUT1 = "/mnt/d/aoc_day4/docs/klayout_layout.png"
OUT2 = "/mnt/d/aoc_day4/docs/klayout_caravel_context.png"
BG   = "#0d0d0d"

# Sky130 layer colours.
COLORS = {
    (65, 20): ("#5080c0", 0.75),  # diff
    (66, 20): ("#c05050", 0.90),  # poly
    (67, 20): ("#4a9aba", 0.70),  # li1
    (68, 20): ("#8b6fb5", 0.60),  # met1
    (69, 20): ("#4a9e6e", 0.85),  # met2
}
ORDER = [(65, 20), (66, 20), (67, 20), (68, 20), (69, 20)]

# Zoom box from met2-density analysis (logic cluster).
# Cluster sits at x=[320,416] y=[282,389]; pad to 4:3 aspect.
ZOOM_X = (290.0, 450.0)
ZOOM_Y = (270.0, 390.0)


def collect_polygons(gds_path):
    lib = gdstk.read_gds(gds_path)
    top = lib.top_level()[0]
    print(f"  top cell: {top.name}")
    by_layer = {}
    for layer, dt in COLORS:
        polys = top.get_polygons(depth=None, layer=layer, datatype=dt)
        by_layer[(layer, dt)] = polys
        print(f"  L{layer}/D{dt}: {len(polys)} polygons")
    return by_layer


def clip_to_zoom(polys, x0, x1, y0, y1):
    """Keep only polygons whose bbox intersects the zoom window."""
    out = []
    for p in polys:
        (px0, py0), (px1, py1) = p.bounding_box()
        if px1 < x0 or px0 > x1 or py1 < y0 or py0 > y1:
            continue
        out.append(p.points)
    return out


def render(by_layer, out_path):
    fig, ax = plt.subplots(figsize=(16, 12), dpi=150)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    x0, x1 = ZOOM_X
    y0, y1 = ZOOM_Y
    print(f"  zoom: x=[{x0},{x1}] y=[{y0},{y1}]")

    for key in ORDER:
        polys = by_layer.get(key, [])
        if not polys:
            continue
        clipped = clip_to_zoom(polys, x0, x1, y0, y1)
        if not clipped:
            continue
        color, alpha = COLORS[key]
        coll = PolyCollection(clipped, facecolors=color, edgecolors=color,
                              linewidths=0.0, alpha=alpha, antialiased=True)
        ax.add_collection(coll)
        print(f"    L{key[0]}/D{key[1]}: rendered {len(clipped)} polygons")

    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(out_path, dpi=150, facecolor=BG, edgecolor="none",
                bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    print(f"  saved: {out_path}  ({os.path.getsize(out_path)//1024} KB)")


def add_tile_outline(src, dst):
    """Copy src to dst, overlay white 4x2 tile rectangle + label."""
    shutil.copy(src, dst)
    img = Image.open(dst).convert("RGB")
    draw = ImageDraw.Draw(img)
    W, H = img.size
    m = 30
    draw.rectangle([m, m, W - m, H - m],
                   outline=(235, 235, 235), width=4)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 36)
    except Exception:
        font = ImageFont.load_default()
    draw.text((m + 14, m + 10),
              "tt_um_day4_forklift  -  Sky130A 4x2 tile (1360 x 680 um)",
              fill=(235, 235, 235), font=font)
    img.save(dst)
    print(f"  saved: {dst}  ({os.path.getsize(dst)//1024} KB)")


print("Collecting polygons (flattened)...")
by_layer = collect_polygons(GDS)

print("\nRendering klayout_layout.png ...")
render(by_layer, OUT1)

print("\nRendering klayout_caravel_context.png ...")
add_tile_outline(OUT1, OUT2)

print("\nDone.")
