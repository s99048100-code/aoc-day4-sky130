#!/usr/bin/env python3
"""
Generate KLayout layout screenshots via klayout Python API (headless).
Image 1 (klayout_layout.png):  full die, fit to bounding box.
Image 2 (klayout_caravel_context.png): die inside TT 4x2 tile outline.
"""

import os, sys
try:
    import klayout.db  as db
    import klayout.lay as lay
except ImportError:
    sys.exit("klayout Python package not found")

GDS  = "/mnt/d/aoc_day4/runs/baseline/final/klayout_gds/tt_um_day4_forklift.klayout.gds"
DOCS = "/mnt/d/aoc_day4/docs"
W, H = 2400, 1800
BG   = "#0d0d0d"

# Sky130 layer colours — fill + frame both visible, nwell outline-only.
STYLE = {
    # (layer, dt): (fill_hex or None, frame_hex, visible)
    (64, 20): (None,      "#7070bb", True),   # nwell — outline only
    (65, 20): ("#204878", "#5080c0", True),   # diff — blue
    (66, 20): ("#7a1f1f", "#c05050", True),   # poly — red
    (67, 20): ("#1a5a6a", "#4a9aba", True),   # li1 — teal
    (68, 20): ("#3a2060", "#8b6fb5", True),   # met1 — purple
    (69, 20): ("#1a4a30", "#4a9e6e", True),   # met2 — green
    (70, 20): ("#5a3010", "#c47a3d", True),   # met3 — orange
    (71, 20): ("#2a4a10", "#6a9e4a", True),   # met4 — lime
    (72, 20): ("#4a1040", "#b54a8b", True),   # met5 — pink
}

def css_rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16) << 16) | (int(h[2:4], 16) << 8) | int(h[4:6], 16)

BG_INT = css_rgb(BG)


def apply_styles(lv):
    li = lv.begin_layers()
    while not li.at_end():
        lp  = li.current()
        key = (lp.source_layer, lp.source_datatype)
        if key in STYLE:
            fill_h, frame_h, vis = STYLE[key]
            lp.visible     = vis
            lp.frame_color = css_rgb(frame_h)
            lp.fill_color  = css_rgb(fill_h) if fill_h else BG_INT
            lp.width       = 1
        else:
            lp.visible = False
        li.next()


def render_layout(gds_path, out_path):
    """Full die, fit to bounding box."""
    lv  = lay.LayoutView()
    idx = lv.load_layout(gds_path, True)
    lv.max_hier()
    lv.set_config("background-color", BG)
    lv.set_config("grid-visible",     "false")
    apply_styles(lv)

    cv   = lv.cellview(idx)
    bbox = cv.cell.dbbox()
    lv.zoom_box(db.DBox(bbox.left, bbox.bottom, bbox.right, bbox.top))

    lv.save_image(out_path, W, H)
    print(f"  saved: {out_path}  ({os.path.getsize(out_path)//1024} KB)")


def render_context(gds_path, out_path):
    """Full die + TT 4x2 tile outline (1360x680 µm)."""
    lv  = lay.LayoutView()
    idx = lv.load_layout(gds_path, True)
    lv.max_hier()
    lv.set_config("background-color", BG)
    lv.set_config("grid-visible",     "false")
    apply_styles(lv)

    cv   = lv.cellview(idx)
    bbox = cv.cell.dbbox()
    cx   = (bbox.left  + bbox.right)  / 2.0
    cy   = (bbox.bottom + bbox.top)   / 2.0

    tw, th = 1360.0, 680.0
    tile   = db.DBox(cx - tw/2, cy - th/2, cx + tw/2, cy + th/2)
    mx, my = tw * 0.05, th * 0.05
    lv.zoom_box(db.DBox(tile.left - mx, tile.bottom - my,
                        tile.right + mx, tile.top + my))

    ann         = lay.Annotation()
    ann.p1      = db.DPoint(tile.left,  tile.bottom)
    ann.p2      = db.DPoint(tile.right, tile.top)
    ann.outline = lay.Annotation.OutlineBox
    ann.style   = lay.Annotation.StyleLine
    ann.text    = "TT 4x2 tile  1360x680 µm"
    lv.insert_annotation(ann)

    lv.save_image(out_path, W, H)
    print(f"  saved: {out_path}  ({os.path.getsize(out_path)//1024} KB)")


os.makedirs(DOCS, exist_ok=True)

print("Rendering klayout_layout.png ...")
render_layout(GDS, f"{DOCS}/klayout_layout.png")

print("Rendering klayout_caravel_context.png ...")
render_context(GDS, f"{DOCS}/klayout_caravel_context.png")

print("Done.")
