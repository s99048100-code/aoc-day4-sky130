#!/usr/bin/env python3
"""
Generate KLayout layout screenshots via klayout Python API (headless).
Output:
  docs/klayout_layout.png           - design, dark theme
  docs/klayout_caravel_context.png  - same + TT 4x2 tile outline annotation
"""

import os, sys
try:
    import klayout.db  as db
    import klayout.lay as lay
except ImportError:
    sys.exit("klayout Python package not found — pip install klayout")

GDS   = "/mnt/d/aoc_day4/runs/baseline/final/klayout_gds/tt_um_day4_forklift.klayout.gds"
DOCS  = "/mnt/d/aoc_day4/docs"
W, H  = 2400, 1800
BG    = "#0d0d0d"

# GDS layer/datatype -> fill colour (RRGGBB)
LAYER_COLORS = {
    (67, 20): "#3d6b8c",   # li1
    (68, 20): "#5c4a7a",   # met1
    (69, 20): "#2e6b4f",   # met2
    (70, 20): "#7a4a2e",   # met3
    (71, 20): "#4a6b3d",   # met4
    (72, 20): "#6b3d5c",   # met5
    (66, 20): "#8c3d3d",   # poly
    (65, 20): "#3d5c8c",   # ndiff
    (64, 20): "#5c8c3d",   # pdiff
    (64,  0): "#1a1a2e",   # nwell (fallback datatype)
}

def css_to_qrgb(h):
    h = h.lstrip("#")
    return (int(h[0:2],16) << 16) | (int(h[2:4],16) << 8) | int(h[4:6],16)

def render(gds_path, out_path, tile_outline=False):
    lv = lay.LayoutView()
    idx = lv.load_layout(gds_path, True)
    lv.max_hier()
    lv.set_config("background-color", BG)

    # tint each layer
    li = lv.begin_layers()
    while not li.at_end():
        lp = li.current()
        layer_no = lp.source_layer
        dt_no    = lp.source_datatype
        key = (layer_no, dt_no)
        color_hex = LAYER_COLORS.get(key, "#4a4a7a")
        rgb = css_to_qrgb(color_hex)
        lp.fill_color  = rgb
        lp.frame_color = rgb
        lp.width = 1
        li.next()

    lv.zoom_fit()

    if tile_outline:
        cv   = lv.cellview(idx)
        bbox = cv.cell.dbbox()           # micron bbox of top cell
        cx   = (bbox.left + bbox.right)  / 2.0
        cy   = (bbox.bottom + bbox.top)  / 2.0
        # TT 4x2 tile ≈ 1360 x 680 µm
        tw, th = 1360.0, 680.0
        ann = lay.Annotation()
        ann.p1 = db.DPoint(cx - tw/2, cy - th/2)
        ann.p2 = db.DPoint(cx + tw/2, cy + th/2)
        ann.outline = lay.Annotation.OutlineBox
        ann.style   = lay.Annotation.StyleLine
        ann.text    = "TT 4x2 tile"
        lv.insert_annotation(ann)

    lv.save_image(out_path, W, H)
    sz = os.path.getsize(out_path)
    print(f"  saved: {out_path}  ({sz // 1024} KB)")


os.makedirs(DOCS, exist_ok=True)

print("Rendering klayout_layout.png ...")
render(GDS, f"{DOCS}/klayout_layout.png", tile_outline=False)

print("Rendering klayout_caravel_context.png ...")
render(GDS, f"{DOCS}/klayout_caravel_context.png", tile_outline=True)

print("Done.")
