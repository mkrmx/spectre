"""Add a GND via inside every F.Cu GND-pour island (and B.Cu islands) so all copper islands join the planes."""
import sys, os, pcbnew
from pcbnew import VECTOR2I, FromMM
from shapely.geometry import Polygon, Point
f = sys.argv[1]
b = pcbnew.LoadBoard(f)
gnd = b.FindNet("GND")
pcbnew.ZONE_FILLER(b).Fill(b.Zones())

def polys(layer):
    out = []
    for z in b.Zones():
        if z.GetLayer() != layer or z.GetNetname() != "GND": continue
        fp = z.GetFilledPolysList(layer)
        for i in range(fp.OutlineCount()):
            o = fp.Outline(i)
            ext = [(o.CPoint(j).x / 1e6, o.CPoint(j).y / 1e6) for j in range(o.PointCount())]
            holes = []
            for h in range(fp.HoleCount(i)):
                hh = fp.Hole(i, h)
                holes.append([(hh.CPoint(j).x / 1e6, hh.CPoint(j).y / 1e6) for j in range(hh.PointCount())])
            p = Polygon(ext, holes).buffer(0)
            if p.area > 0: out.append(p)
    return out

existing = [Point(t.GetPosition().x / 1e6, t.GetPosition().y / 1e6) for t in b.GetTracks()
            if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND"]
thpads = [Point(p.GetPosition().x / 1e6, p.GetPosition().y / 1e6) for fp in b.GetFootprints() for p in fp.Pads()
          if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNetname() == "GND"]
top, bot = polys(pcbnew.F_Cu), polys(pcbnew.B_Cu)
added = 0
VIA_R = 0.35
for layer_polys in (top, bot):
    for p in layer_polys:
        if any(p.buffer(0.05).contains(e) for e in existing + thpads):
            continue
        core = p.buffer(-(VIA_R + 0.05))
        if core.is_empty:
            continue
        other = bot if layer_polys is top else top
        pt = None
        # pick a point inside this island that is also inside the other layer's plane
        cand = core.intersection(__import__("shapely.ops", fromlist=["unary_union"]).unary_union([q.buffer(-(VIA_R + 0.05)) for q in other]))
        tgt = cand if not cand.is_empty else core
        pt = tgt.representative_point()
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(VECTOR2I(FromMM(pt.x), FromMM(pt.y)))
        v.SetWidth(FromMM(0.7)); v.SetDrill(FromMM(0.35))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(gnd); b.Add(v)
        existing.append(pt); added += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(f, b)
print("stitching vias added", added, "| islands top", len(top), "bottom", len(bot))
