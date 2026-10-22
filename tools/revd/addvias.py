"""Add stand-alone GND vias at the given points, keeping only those that leave DRC clean.
usage: python3 addvias.py <pcb> x,y [x,y ...]"""
import sys, os, subprocess, shutil, pcbnew
from pcbnew import VECTOR2I, FromMM
src = sys.argv[1]; here = os.path.dirname(src)
drc = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drc_revd.py")
def clean(f):
    subprocess.run([sys.executable, drc, f], capture_output=True, text=True)
    rpt = open(os.path.splitext(f)[0] + ".rpt").read()
    errs = [l for l in rpt.splitlines() if l.startswith("[") and not l.startswith(("[silk", "[lib_footprint"))]
    return "Found 0 unconnected" in rpt and not errs, errs
for c in sys.argv[2:]:
    x, y = map(float, c.split(","))
    b = pcbnew.LoadBoard(src); gnd = b.FindNet("GND")
    v = pcbnew.PCB_VIA(b); v.SetPosition(VECTOR2I(FromMM(x), FromMM(y))); v.SetWidth(FromMM(0.7)); v.SetDrill(FromMM(0.35))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(gnd); b.Add(v)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    tryf = os.path.join(here, "try_via.kicad_pcb"); pcbnew.SaveBoard(tryf, b)
    shutil.copy(os.path.join(here, "spectre.kicad_pro"), os.path.join(here, "try_via.kicad_pro"))
    ok, errs = clean(tryf)
    print((x, y), "added" if ok else "rejected", errs[:1])
    if ok: shutil.copy(tryf, src)
for f in ("try_via.kicad_pcb", "try_via.kicad_pro", "try_via.rpt"):
    if os.path.exists(os.path.join(here, f)): os.remove(os.path.join(here, f))
