"""Remove GND vias inside a rectangle (plus the short stub that fed only that via), refill and report.
usage: python3 clearvias.py <pcb> x0 y0 x1 y1"""
import sys, pcbnew
f = sys.argv[1]; x0, y0, x1, y1 = map(float, sys.argv[2:6])
b = pcbnew.LoadBoard(f); MM = 1e6
gnd = b.FindNet("GND").GetNetCode()
tracks = [(t, (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)) for t in b.GetTracks()
          if t.GetClass() != "PCB_VIA" and t.GetNetCode() == gnd]
padpolys = [p for fp in b.GetFootprints() for p in fp.Pads()]
def on_pad(pt):
    v = pcbnew.VECTOR2I(int(pt[0]), int(pt[1]))
    return any(p.HitTest(v) for p in padpolys)
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetCode() == gnd
        and x0 <= t.GetPosition().x / MM <= x1 and y0 <= t.GetPosition().y / MM <= y1]
gone = set()
for v in vias:
    front = [(v.GetPosition().x, v.GetPosition().y)]; seen = set(front); chain = []
    while front:
        pt = front.pop()
        for i, (t, s, e) in enumerate(tracks):
            if i in gone or i in chain: continue
            if s == pt or e == pt:
                chain.append(i); nxt = e if s == pt else s
                if nxt not in seen and not on_pad(nxt):
                    seen.add(nxt); front.append(nxt)
    print("via", round(v.GetPosition().x / MM, 2), round(v.GetPosition().y / MM, 2), "stub segments", len(chain))
    for i in chain: b.Remove(tracks[i][0]); gone.add(i)
    b.Remove(v)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(f, b)
print("removed", len(vias))
