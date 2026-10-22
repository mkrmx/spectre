import sys, json, numpy as np, pcbnew, cairosvg, subprocess, os, tempfile
TMP = tempfile.mkdtemp()
from PIL import Image, ImageDraw
S = os.path.dirname(os.path.abspath(__file__))
f, out = sys.argv[1], sys.argv[2]
cfg = json.load(open(os.path.join(S, "layout.json"))); W, H = cfg["W"], cfg["H"]
subprocess.run(["kicad-cli", "pcb", "export", "svg", "--layers", "B.Cu,Edge.Cuts", "--page-size-mode", "2",
                "--exclude-drawing-sheet", "--mirror", "-o", os.path.join(TMP, "bcu.svg"), f], capture_output=True)
cairosvg.svg2png(url=os.path.join(TMP, "bcu.svg"), write_to=os.path.join(TMP, "bcu.png"), output_width=1400, background_color="white")
cu = np.array(Image.open(os.path.join(TMP, "bcu.png")).convert("RGB")).astype(int)
Hh, Ww, _ = cu.shape
nonwhite = np.abs(cu - 255).sum(2) > 30
ys, xs = np.nonzero(nonwhite); x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
sx = (x1 - x0) / W; sy = (y1 - y0) / H
o = np.full((Hh, Ww, 3), (245, 245, 240), np.uint8); o[y0:y1 + 1, x0:x1 + 1] = (29, 85, 55)
copper = (cu[..., 2] > 150) & (cu[..., 0] < 150); o[copper] = (42, 110, 71)
holes = (np.abs(cu - 255).sum(2) < 30); inb = np.zeros_like(holes); inb[y0 + 3:y1 - 2, x0 + 3:x1 - 2] = True; o[holes & inb] = (20, 20, 20)
img = Image.fromarray(o); d = ImageDraw.Draw(img)
b = pcbnew.LoadBoard(f)
for dr in b.GetDrawings():
    if dr.GetLayer() == pcbnew.B_SilkS:
        ps = dr.GetPolyShape()
        for i in range(ps.OutlineCount()):
            ol = ps.Outline(i)
            d.polygon([(x0 + (W - ol.CPoint(j).x / 1e6) * sx, y0 + ol.CPoint(j).y / 1e6 * sy) for j in range(ol.PointCount())], fill=(241, 241, 232))
img.save(out)
