"""Connect an isolated GND SMD pad to the bottom plane: short track + via, first candidate that passes DRC."""
import sys, os, subprocess, shutil, pcbnew, itertools
from pcbnew import VECTOR2I, FromMM
src, ref, padnum = sys.argv[1], sys.argv[2], sys.argv[3]
here = os.path.dirname(src)
b = pcbnew.LoadBoard(src)
fp = [f for f in b.GetFootprints() if f.GetReference() == ref][0]
pad = [p for p in fp.Pads() if p.GetNumber() == padnum][0]
px, py = pad.GetPosition().x / 1e6, pad.GetPosition().y / 1e6
print("pad at", round(px, 2), round(py, 2))
cands = []
for r in (1.0, 1.3, 1.6, 2.0, 2.4):
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
        n = (dx * dx + dy * dy) ** 0.5
        cands.append((px + dx / n * r, py + dy / n * r))
drc = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drc_revd.py")
for i, (vx, vy) in enumerate(cands):
    b = pcbnew.LoadBoard(src)
    gnd = b.FindNet("GND")
    t = pcbnew.PCB_TRACK(b); t.SetStart(VECTOR2I(FromMM(px), FromMM(py))); t.SetEnd(VECTOR2I(FromMM(vx), FromMM(vy)))
    t.SetWidth(FromMM(0.4)); t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd); b.Add(t)
    v = pcbnew.PCB_VIA(b); v.SetPosition(VECTOR2I(FromMM(vx), FromMM(vy))); v.SetWidth(FromMM(0.7)); v.SetDrill(FromMM(0.35))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(gnd); b.Add(v)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    tryf = os.path.join(here, "try_via.kicad_pcb"); pcbnew.SaveBoard(tryf, b)
    shutil.copy(os.path.join(here, "routed.kicad_pro"), os.path.join(here, "try_via.kicad_pro"))
    out = subprocess.run([sys.executable, drc, tryf], capture_output=True, text=True).stdout
    rpt = open(os.path.join(here, "try_via.rpt")).read()
    errs = [l for l in rpt.splitlines() if l.startswith("[") and not l.startswith(("[silk", "[lib_footprint"))]
    unc = "Found 0 unconnected" in rpt
    print(i, (round(vx, 2), round(vy, 2)), "unconnected OK" if unc else "still unconnected", errs[:2])
    if unc and not errs:
        shutil.copy(tryf, src); print("applied"); break
