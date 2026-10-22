"""Place each reference label where it touches no pad (mask opening), no other silkscreen, no hole and stays on board."""
import sys, json, os, math, pcbnew
from pcbnew import VECTOR2I, FromMM
from shapely.geometry import box, LineString, Point
from shapely.ops import unary_union
S = os.path.dirname(os.path.abspath(__file__))
f = sys.argv[1]
cfg = json.load(open(os.path.join(S, "layout.json")))
W, H = cfg["W"], cfg["H"]
b = pcbnew.LoadBoard(f)
MM = 1e6

def bb(o, grow=0.0):
    r = o.GetBoundingBox()
    return box(r.GetLeft() / MM - grow, r.GetTop() / MM - grow, r.GetRight() / MM + grow, r.GetBottom() / MM + grow)

pads, silk, holes = [], [], []
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            holes.append(Point(p.GetPosition().x / MM, p.GetPosition().y / MM).buffer(p.GetDrillSize().x / MM / 2 + 3.0))
        else:
            pads.append(bb(p, 0.2))
    for g in fp.GraphicalItems():
        if g.GetLayer() == pcbnew.F_SilkS and g.GetClass() != "PCB_TEXT" and g.GetClass() != "FP_TEXT":
            if hasattr(g, "GetShape") and g.GetShape() == pcbnew.SHAPE_T_SEGMENT:
                s, e = g.GetStart(), g.GetEnd()
                silk.append(LineString([(s.x / MM, s.y / MM), (e.x / MM, e.y / MM)]).buffer(0.15))
            else:
                silk.append(bb(g, 0.1))
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        pads.append(Point(t.GetPosition().x / MM, t.GetPosition().y / MM).buffer(t.GetWidth() / MM / 2 + 0.1))
obst = unary_union(pads + silk + holes)
M_ = float(os.environ.get("MARGIN", "0.4")); inside = box(M_, M_, W - M_, H - M_)

def cy_box(fp):
    c = fp.GetCourtyard(pcbnew.F_CrtYd)
    r = c.BBox() if c.OutlineCount() else fp.GetBoundingBox(False, False)
    return box(r.GetLeft() / MM, r.GetTop() / MM, r.GetRight() / MM, r.GetBottom() / MM)
for _fp in b.GetFootprints(): _fp.BuildCourtyardCaches()
CY = {fp.GetReference(): cy_box(fp) for fp in b.GetFootprints() if not fp.GetReference().startswith("H")}
placed = []
order = sorted([fp for fp in b.GetFootprints() if not fp.GetReference().startswith("H")],
               key=lambda fp: -bb(fp).area)
report = []
for fp in order:
    t = fp.Reference()
    t.SetTextSize(VECTOR2I(FromMM(0.8), FromMM(0.8))); t.SetTextThickness(FromMM(0.15))
    fb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if fp.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else fp.GetBoundingBox(False, False)
    x0, y0, x1, y1 = fb.GetLeft() / MM, fb.GetTop() / MM, fb.GetRight() / MM, fb.GetBottom() / MM
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    cands = []
    for ang in (0, 90):
        cands += [(cx, y0 - 0.55, ang), (cx, y1 + 0.55, ang), (x0 - 0.9, cy, ang), (x1 + 0.9, cy, ang), (cx, cy, ang)]
        for dx in (-2, -1, 1, 2):
            cands += [(cx + dx, y0 - 0.55, ang), (cx + dx, y1 + 0.55, ang)]
        for dy in (-1.5, 1.5):
            cands += [(x0 - 0.9, cy + dy, ang), (x1 + 0.9, cy + dy, ang)]
        for r in (1.2, 1.8, 2.5, 3.2):
            for k in range(16):
                a = 2 * math.pi * k / 16
                cands.append((cx + (x1 - x0) / 2 * math.cos(a) + r * math.cos(a), cy + (y1 - y0) / 2 * math.sin(a) + r * math.sin(a), ang))
    best = None
    for x, y, ang in cands:
        t.SetPosition(VECTOR2I(FromMM(x), FromMM(y))); t.SetTextAngleDegrees(ang)
        tb = bb(t, 0.08)
        if not inside.contains(tb): continue
        bad = tb.intersection(obst).area + sum(tb.intersection(p).area for p in placed) * 3
        dist = math.hypot(x - cx, y - cy) + (0.3 if ang else 0)
        me = fp.GetReference()
        d_own = tb.distance(CY[me])
        d_oth = min(tb.distance(v) for k, v in CY.items() if k != me)
        amb = (d_own > d_oth - 0.05) and os.environ.get("AMB", "0") == "1"
        score = (bad > 1e-6, amb, bad, dist)
        if best is None or score < best[0]:
            best = (score, x, y, ang)
    _, x, y, ang = best
    t.SetPosition(VECTOR2I(FromMM(x), FromMM(y))); t.SetTextAngleDegrees(ang)
    placed.append(bb(t, 0.05))
    report.append((fp.GetReference(), round(x, 2), round(y, 2), ang, "OK" if not (best[0][0] or best[0][1]) else ("overlap %.3f" % best[0][2] if best[0][0] else "ambiguous")))
pcbnew.SaveBoard(f, b)
# final ambiguity report (label nearer to another part than to its own)
for fp in order:
    me = fp.GetReference(); tb = bb(fp.Reference(), 0.0)
    d_own = tb.distance(CY[me]); oth = min(((tb.distance(v), k) for k, v in CY.items() if k != me))
    if d_own > oth[0] - 0.05: print("AMBIG", me, "nearer to", oth[1], round(d_own, 2), round(oth[0], 2))
for r in report:
    if r[4] != "OK": print(r)
print("labels placed", len(report))
