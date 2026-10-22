"""Place the (already mirrored) MKr SPECTRE logo on B.SilkS as large as possible, clear of THT pads and holes."""
import sys, os, json, pickle, pcbnew
from pcbnew import FromMM
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import affinity
S = os.path.dirname(os.path.abspath(__file__))
f = sys.argv[1]
cfg = json.load(open(os.path.join(S, "..", "layout.json")))
W, H = float(os.environ.get("BW", cfg["W"])), float(os.environ.get("BH", cfg["H"]))
raw = pickle.load(open(os.path.join(S, "..", "logo_polys.pkl"), "rb"))
# Rebuild the logo: the saved outlines are fractured polygons (holes already cut in), so a plain union is exact.
logo = unary_union([Polygon(p).buffer(0) for p in raw if len(p) > 2])
x0, y0, x1, y1 = logo.bounds
logo = affinity.translate(logo, -x0, -y0)
LW, LH = x1 - x0, y1 - y0

b = pcbnew.LoadBoard(f)
obst = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD: continue
        r = max(p.GetSize().x, p.GetSize().y, p.GetDrillSize().x) / 2e6
        obst.append(Point(p.GetPosition().x / 1e6, p.GetPosition().y / 1e6).buffer(3.6 if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH else r + 0.35))
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        obst.append(Point(t.GetPosition().x / 1e6, t.GetPosition().y / 1e6).buffer(t.GetWidth() / 2e6 + 0.2))
    elif os.environ.get("AVOID_TRACKS") and t.GetLayer() == pcbnew.B_Cu:
        from shapely.geometry import LineString
        s_, e_ = t.GetStart(), t.GetEnd()
        obst.append(LineString([(s_.x / 1e6, s_.y / 1e6), (e_.x / 1e6, e_.y / 1e6)]).buffer(t.GetWidth() / 2e6 + 0.2))
obst = unary_union(obst)
MARG = float(os.environ.get("MARG", "0.6"))
YMIN = max(float(os.environ.get("YMIN", "0.6")), MARG)
inside = box(MARG, YMIN, W - MARG, H - MARG)

best = None
h = float(os.environ.get("HMAX", "9.0"))
while h >= float(os.environ.get("HMIN", "3.0")) and best is None:
    k = h / LH
    g = affinity.scale(logo, k, k, origin=(0, 0))
    gw = LW * k
    yy = YMIN
    while yy + h <= H - MARG and best is None:
        xx = MARG
        while xx + gw <= W - MARG:
            c = affinity.translate(g, xx, yy)
            if inside.contains(c) and not c.intersects(obst):
                best = (h, xx, yy, c); break
            xx += 0.2
        yy += 0.2
    h -= 0.1
if best is None: sys.exit("no fit")
h, xx, yy, g = best
# centre horizontally within the free span at that height
lo, hi = xx, xx
gw = g.bounds[2] - g.bounds[0]
step = 0.1
while True:
    c = affinity.translate(g, hi - xx + step, 0)
    if inside.contains(c) and not c.intersects(obst): hi += step
    else: break
g = affinity.translate(g, (hi - lo) / 2, 0)
lo2 = hi2 = 0.0
while True:
    c = affinity.translate(g, 0, hi2 + step)
    if inside.contains(c) and not c.intersects(obst): hi2 += step
    else: break
g = affinity.translate(g, 0, hi2 / 2)
print("logo %.2f x %.2f mm at x %.2f..%.2f y %.2f..%.2f" % (gw, h, *[g.bounds[i] for i in (0, 2, 1, 3)]))

for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.B_SilkS: b.Remove(d)
n = 0
for p in (g.geoms if hasattr(g, "geoms") else [g]):
    ps = pcbnew.SHAPE_POLY_SET(); ps.NewOutline()
    for x, y in list(p.exterior.coords)[:-1]: ps.Append(FromMM(x), FromMM(y))
    for r in p.interiors:
        hi_ = ps.NewHole(0)
        for x, y in list(r.coords)[:-1]: ps.Append(FromMM(x), FromMM(y), 0, hi_)
    ps.Fracture(pcbnew.SHAPE_POLY_SET.PM_FAST)
    for i in range(ps.OutlineCount()):
        sh = pcbnew.PCB_SHAPE(b); sh.SetShape(pcbnew.SHAPE_T_POLY)
        one = pcbnew.SHAPE_POLY_SET(); one.AddOutline(ps.Outline(i))
        sh.SetPolyShape(one); sh.SetFilled(True); sh.SetWidth(0); sh.SetLayer(pcbnew.B_SilkS)
        b.Add(sh); n += 1
pcbnew.SaveBoard(f, b)
print("logo shapes", n, "area check", round(g.area, 2))
