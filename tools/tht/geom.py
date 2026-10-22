"""Courtyard boxes and pad centres (relative to footprint origin) for every footprint at 0/90/180/270 degrees."""
import json, os
import pcbnew
from pcbnew import VECTOR2I

D = os.path.dirname(os.path.abspath(__file__))
LIB = "/usr/share/kicad/footprints"
NET = json.load(open(os.path.join(D, "netmap_tht.json")))
b = pcbnew.LoadBoard(os.path.join(D, "..", "..", "smt", "spectre.kicad_pcb"))   # any board works as SWIG context
out = {}
keep = []
for ref, info in NET.items():
    lib, name = info["fp"].split(":")
    g = {}
    for rot in (0, 90, 180, 270):
        fp = pcbnew.FootprintLoad(f"{LIB}/{lib}.pretty", name)
        keep.append(fp)
        fp.SetOrientationDegrees(rot); fp.SetPosition(VECTOR2I(0, 0))
        xs, ys = [], []
        for gi in fp.GraphicalItems():
            if gi.GetLayer() == pcbnew.F_CrtYd:
                r_ = gi.GetBoundingBox(); xs += [r_.GetLeft(), r_.GetRight()]; ys += [r_.GetTop(), r_.GetBottom()]
        class _B: pass
        bb = _B()
        bb.GetLeft = lambda: min(xs); bb.GetRight = lambda: max(xs); bb.GetTop = lambda: min(ys); bb.GetBottom = lambda: max(ys)
        pads = {}
        for p in fp.Pads():
            if p.GetNumber():
                pads.setdefault(p.GetNumber(), []).append((p.GetPosition().x / 1e6, p.GetPosition().y / 1e6))
        g[rot] = {"box": [bb.GetLeft() / 1e6, bb.GetTop() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6],
                  "pads": {k: [sum(c[0] for c in v) / len(v), sum(c[1] for c in v) / len(v)] for k, v in pads.items()}}
    out[ref] = g
json.dump(out, open(os.path.join(D, "geom.json"), "w"), indent=0)
print("geometry for", len(out), "footprints")
