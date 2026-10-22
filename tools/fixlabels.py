import sys, json, pcbnew
from pcbnew import VECTOR2I, FromMM
f = sys.argv[1]; ov = json.loads(sys.argv[2])
b = pcbnew.LoadBoard(f)
fps = {x.GetReference(): x for x in b.GetFootprints()}
for r, (x, y, a) in ov.items():
    t = fps[r].Reference(); t.SetPosition(VECTOR2I(FromMM(x), FromMM(y))); t.SetTextAngleDegrees(a)
pcbnew.SaveBoard(f, b)
