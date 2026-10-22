"""Move selected reference labels to the clean spot closest to a target point (keeps all other labels fixed)."""
import sys, json, math, pcbnew
from pcbnew import VECTOR2I, FromMM
from shapely.geometry import box, LineString, Point
from shapely.ops import unary_union
f = sys.argv[1]; targets = json.loads(sys.argv[2])
b = pcbnew.LoadBoard(f)
MM = 1e6
def bb(o, g=0.0):
    r = o.GetBoundingBox()
    return box(r.GetLeft()/MM - g, r.GetTop()/MM - g, r.GetRight()/MM + g, r.GetBottom()/MM + g)
fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
obs = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            obs.append(Point(p.GetPosition().x/MM, p.GetPosition().y/MM).buffer(p.GetDrillSize().x/MM/2 + 0.3))
        else:
            obs.append(bb(p, 0.12))
    for g in fp.GraphicalItems():
        if g.GetLayer() != pcbnew.F_SilkS or g.GetClass() in ("PCB_TEXT", "FP_TEXT"): continue
        if g.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            s, e = g.GetStart(), g.GetEnd()
            obs.append(LineString([(s.x/MM, s.y/MM), (e.x/MM, e.y/MM)]).buffer(g.GetWidth()/MM/2 + 0.1))
        elif g.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            c = g.GetCenter(); r = g.GetRadius()/MM
            obs.append(Point(c.x/MM, c.y/MM).buffer(r + g.GetWidth()/MM/2 + 0.1).exterior.buffer(g.GetWidth()/MM/2 + 0.1))
        elif g.GetShape() == pcbnew.SHAPE_T_ARC:
            obs.append(bb(g, 0.1).exterior.buffer(0.15))
        else:
            obs.append(bb(g, 0.1))
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        obs.append(Point(t.GetPosition().x/MM, t.GetPosition().y/MM).buffer(t.GetWidth()/MM/2 + 0.1))
for r, fp in fps.items():
    if r not in targets and fp.Reference().IsVisible():
        obs.append(bb(fp.Reference(), 0.1))
obst = unary_union(obs)
W = b.GetBoardEdgesBoundingBox()
inside = box(W.GetLeft()/MM + 0.4, W.GetTop()/MM + 0.4, W.GetRight()/MM - 0.4, W.GetBottom()/MM - 0.4)
placed = []
for ref, (tx, ty, pref) in targets.items():
    t = fps[ref].Reference()
    best = None
    for ang in ([pref, 90 - pref] if pref in (0, 90) else [0, 90]):
        for i in range(-12, 13):
            for j in range(-12, 13):
                x, y = tx + i*0.15, ty + j*0.15
                t.SetPosition(VECTOR2I(FromMM(x), FromMM(y))); t.SetTextAngleDegrees(ang)
                tb = bb(t, 0.05)
                if not inside.contains(tb): continue
                bad = tb.intersection(obst).area + sum(tb.intersection(p).area for p in placed)
                sc = (bad > 1e-9, bad, math.hypot(x - tx, y - ty) + (0.4 if ang != pref else 0))
                if best is None or sc < best[0]: best = (sc, x, y, ang)
    sc, x, y, ang = best
    t.SetPosition(VECTOR2I(FromMM(x), FromMM(y))); t.SetTextAngleDegrees(ang)
    placed.append(bb(t, 0.1))
    print(ref, round(x, 2), round(y, 2), ang, "clean" if not sc[0] else "OVERLAP %.3f" % sc[1], "moved %.2f" % sc[2])
pcbnew.SaveBoard(f, b)
