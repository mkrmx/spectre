"""Label slots for every footprint and rotation: where the reference text (0.8 mm, stroke 0.15) can sit next to
the courtyard, or inside it on big parts without touching own pads or silkscreen.
Writes geom2.json: {ref: {rot: [[dx, dy, abs_angle, w, h, pref], ...]}} (offsets from the footprint origin)."""
import json, os, math
import pcbnew
from pcbnew import VECTOR2I
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
D = os.path.dirname(os.path.abspath(__file__))
LIB = "/usr/share/kicad/footprints"
NET = json.load(open(os.path.join(D, "netmap_sch.json")))
G = json.load(open(os.path.join(D, "geom.json")))
ctx = pcbnew.LoadBoard(os.path.join(D, "..", "..", "smt", "spectre.kicad_pcb"))
# ink size of each reference (length along the text, thickness across)
INK = {}
for fp in ctx.GetFootprints():
    t = fp.Reference(); t.SetTextSize(VECTOR2I(800000, 800000)); t.SetTextThickness(150000)
    bb = t.GetEffectiveTextShape().BBox()
    a, c = bb.GetWidth() / 1e6, bb.GetHeight() / 1e6
    INK[fp.GetReference()] = (max(a, c), min(a, c) if min(a, c) > 0.9 else 0.95)
GAP = 0.08
out = {}; keep = []
for ref, info in NET.items():
    lib, name = info["fp"].split(":")
    L, T = INK[ref]
    out[ref] = {}
    for rot in (0, 90, 180, 270):
        fp = pcbnew.FootprintLoad(f"{LIB}/{lib}.pretty", name); keep.append(fp)
        fp.SetOrientationDegrees(rot); fp.SetPosition(VECTOR2I(0, 0))
        x0, y0, x1, y1 = G[ref][str(rot)]["box"]
        pads = []
        for p in fp.Pads():
            ps = p.GetEffectivePolygon()
            for i in range(ps.OutlineCount()):
                o = ps.Outline(i)
                pads.append(Polygon([(o.CPoint(j).x / 1e6, o.CPoint(j).y / 1e6) for j in range(o.PointCount())]).buffer(0.15))
        silk = []
        for g in fp.GraphicalItems():
            if g.GetLayer() != pcbnew.F_SilkS or g.GetClass() in ("FP_TEXT", "PCB_TEXT"): continue
            w = g.GetWidth() / 1e6 / 2 + 0.1
            sh = g.GetShape()
            if sh == pcbnew.SHAPE_T_SEGMENT:
                silk.append(LineString([(g.GetStart().x / 1e6, g.GetStart().y / 1e6), (g.GetEnd().x / 1e6, g.GetEnd().y / 1e6)]).buffer(w))
            elif sh == pcbnew.SHAPE_T_CIRCLE:
                c = Point(g.GetCenter().x / 1e6, g.GetCenter().y / 1e6); r = g.GetRadius() / 1e6
                silk.append(c.buffer(r + w).difference(c.buffer(max(r - w, 0))))
            elif sh == pcbnew.SHAPE_T_ARC:
                pts = [g.GetStart(), g.GetArcMid(), g.GetEnd()]
                silk.append(LineString([(q.x / 1e6, q.y / 1e6) for q in pts]).buffer(w + 0.1))
            elif sh == pcbnew.SHAPE_T_RECT:
                s_, e_ = g.GetStart(), g.GetEnd()
                silk.append(box(min(s_.x, e_.x) / 1e6, min(s_.y, e_.y) / 1e6, max(s_.x, e_.x) / 1e6, max(s_.y, e_.y) / 1e6).exterior.buffer(w))
            elif sh == pcbnew.SHAPE_T_POLY:
                ps = g.GetPolyShape()
                for i in range(ps.OutlineCount()):
                    o = ps.Outline(i)
                    silk.append(Polygon([(o.CPoint(j).x / 1e6, o.CPoint(j).y / 1e6) for j in range(o.PointCount())]).exterior.buffer(w))
        blocked = unary_union(pads + silk)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        slots = []
        for ang in (0, 90):
            w, h = (L, T) if ang == 0 else (T, L)
            pv = 0.0 if ang == 0 else 0.25
            xs = sorted({cx, x0 + w / 2, x1 - w / 2}) if x1 - x0 > w + 0.2 else [cx]
            ys = sorted({cy, y0 + h / 2, y1 - h / 2}) if y1 - y0 > h + 0.2 else [cy]
            for x in xs:
                slots.append([x, y0 - GAP - h / 2, ang, w, h, pv + (0 if x == cx else 0.1)])
                slots.append([x, y1 + GAP + h / 2, ang, w, h, pv + (0 if x == cx else 0.1)])
            for y in ys:
                slots.append([x0 - GAP - w / 2, y, ang, w, h, pv + (0 if y == cy else 0.1)])
                slots.append([x1 + GAP + w / 2, y, ang, w, h, pv + (0 if y == cy else 0.1)])
            # inside the courtyard (big parts): free of own pads and outline silk
            if (x1 - x0) > w + 0.4 and (y1 - y0) > h + 0.4 and (x1 - x0) * (y1 - y0) > 12:
                ins = []
                nx, ny = int((x1 - x0 - w - 0.2) / 0.2), int((y1 - y0 - h - 0.2) / 0.2)
                for i in range(nx + 1):
                    for j in range(ny + 1):
                        px = x0 + 0.1 + w / 2 + i * 0.2; py = y0 + 0.1 + h / 2 + j * 0.2
                        rb = box(px - w / 2, py - h / 2, px + w / 2, py + h / 2)
                        if not rb.intersects(blocked):
                            ins.append((math.hypot(px - cx, py - cy), px, py))
                ins.sort()
                chosen = []
                for d_, px, py in ins:
                    if all(math.hypot(px - a, py - b_) > 1.0 for a, b_ in chosen):
                        chosen.append((px, py))
                    if len(chosen) >= 4: break
                for px, py in chosen:
                    slots.append([px, py, ang, w, h, 1.0 + pv])
        out[ref][str(rot)] = [[round(v, 3) if isinstance(v, float) else v for v in s] for s in slots]
json.dump(out, open(os.path.join(D, "geom2.json"), "w"))
print({r: len(out[r]["0"]) for r in out})
print({r: INK[r] for r in ("R10", "C1", "LDR1", "Q4", "J1")})
