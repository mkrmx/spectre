"""Re-seat the listed reference labels using the real text ink: no pads, no silkscreen lines, no vias, no other
labels (0.35 mm apart so they never read as one word), out of the 1 mm rail strip, as close to their own part
as possible and preferably off other parts' courtyards.  usage: python3 labfix.py <pcb> REF [REF ...]"""
import sys, math, pcbnew
from pcbnew import VECTOR2I, FromMM
from shapely.geometry import box, LineString, Point
from shapely.ops import unary_union
f = sys.argv[1]
TGT = {a.split(':')[0]: tuple(map(float, a.split(':')[1:])) for a in sys.argv[2:] if ':' in a}
refs = [a.split(':')[0] for a in sys.argv[2:]]
b = pcbnew.LoadBoard(f); MM = 1e6
fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
def ink(t):
    r = t.GetEffectiveTextShape().BBox()
    return box(r.GetLeft() / MM, r.GetTop() / MM, r.GetRight() / MM, r.GetBottom() / MM)
def cyb(fp):
    c = fp.GetCourtyard(pcbnew.F_CrtYd); r = c.BBox()
    return box(r.GetLeft() / MM, r.GetTop() / MM, r.GetRight() / MM, r.GetBottom() / MM)
for fp in b.GetFootprints(): fp.BuildCourtyardCaches()
hard = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        r = p.GetBoundingBox(); hard.append(box(r.GetLeft() / MM - 0.1, r.GetTop() / MM - 0.1, r.GetRight() / MM + 0.1, r.GetBottom() / MM + 0.1))
    for g in fp.GraphicalItems():
        if g.GetLayer() != pcbnew.F_SilkS or g.GetClass() in ("PCB_TEXT", "FP_TEXT"): continue
        w = g.GetWidth() / MM / 2 + 0.08
        if g.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            hard.append(LineString([(g.GetStart().x / MM, g.GetStart().y / MM), (g.GetEnd().x / MM, g.GetEnd().y / MM)]).buffer(w))
        elif g.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            c = Point(g.GetCenter().x / MM, g.GetCenter().y / MM); rr = g.GetRadius() / MM
            hard.append(c.buffer(rr + w).difference(c.buffer(max(rr - w, 0))))
        elif g.GetShape() == pcbnew.SHAPE_T_ARC:
            hard.append(LineString([(q.x / MM, q.y / MM) for q in (g.GetStart(), g.GetArcMid(), g.GetEnd())]).buffer(w + 0.1))
        else:
            r = g.GetBoundingBox(); hard.append(box(r.GetLeft() / MM, r.GetTop() / MM, r.GetRight() / MM, r.GetBottom() / MM).exterior.buffer(w))
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        hard.append(Point(t.GetPosition().x / MM, t.GetPosition().y / MM).buffer(t.GetWidth() / MM / 2 + 0.05))
for r, fp in fps.items():
    if r not in refs: hard.append(ink(fp.Reference()).buffer(0.35))
hard = unary_union(hard)
inside = box(1.0, 1.0, 41.0, 31.0)
CY = {r: cyb(fp) for r, fp in fps.items()}
for ref in refs:
    fp = fps[ref]; t = fp.Reference(); rot = fp.GetOrientationDegrees()
    p0 = t.GetPosition(); x0, y0 = p0.x / MM, p0.y / MM
    if ref in TGT: x0, y0 = TGT[ref][:2]
    R_ = int(TGT[ref][2] / 0.1) if ref in TGT and len(TGT[ref]) > 2 else 20
    own = CY[ref]; best = None
    for ang in (0, 90):
        for i in range(-R_, R_ + 1):
            for j in range(-R_, R_ + 1):
                x, y = x0 + i * 0.1, y0 + j * 0.1
                t.SetPosition(VECTOR2I(FromMM(x), FromMM(y))); t.SetTextAngleDegrees((ang - rot) % 360)
                ib = ink(t)
                if not inside.contains(ib) or ib.intersects(hard): continue
                if ib.intersects(own.buffer(-0.05)): continue
                oth = sum(ib.intersection(c).area for k, c in CY.items() if k != ref)
                d_own = ib.distance(own); d_oth = min(ib.distance(c) for k, c in CY.items() if k != ref)
                sc = oth * 20 + d_own * 3 + max(0, d_own - d_oth + 0.1) * 5 + 0.15 * math.hypot(x - x0, y - y0) + (0.3 if ang else 0)
                if best is None or sc < best[0]: best = (sc, x, y, ang, d_own, d_oth, oth)
    if best is None:
        t.SetPosition(p0); print(ref, "no clean spot, left as is"); continue
    sc, x, y, ang, d_own, d_oth, oth = best
    t.SetPosition(VECTOR2I(FromMM(x), FromMM(y))); t.SetTextAngleDegrees((ang - rot) % 360)
    hard = unary_union([hard, ink(t).buffer(0.35)])
    print(ref, "->", round(x, 2), round(y, 2), ang, "| own %.2f other %.2f overlap %.3f" % (d_own, d_oth, oth))
pcbnew.SaveBoard(f, b)
