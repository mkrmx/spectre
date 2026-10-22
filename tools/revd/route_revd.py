"""Build a rev D board from a layout, route it with Freerouting, import the result and fill zones.
usage: python3 route_revd.py <layout.json> <tag> [max_passes]"""
import os, re, subprocess, sys, shutil
D = os.path.dirname(os.path.abspath(__file__))
layout, tag = sys.argv[1], sys.argv[2]
mp = sys.argv[3] if len(sys.argv) > 3 else "30"
work = os.path.join(D, "r_" + tag); os.makedirs(work, exist_ok=True)
env = dict(os.environ, LAYOUT=layout, FZONE="0")
subprocess.run([sys.executable, os.path.join(D, "build_revd.py")], env=env, check=True, capture_output=True)
for ext in ("kicad_pcb", "kicad_pro"):
    shutil.copy(os.path.join(D, "board", "spectre." + ext), os.path.join(work, "spectre." + ext))
import pcbnew
from pcbnew import VECTOR2I, FromMM
src = os.path.join(work, "spectre.kicad_pcb")
dsn, ses = os.path.join(work, "spectre.dsn"), os.path.join(work, "spectre.ses")
b = pcbnew.LoadBoard(src)
assert pcbnew.ExportSpecctraDSN(b, dsn)
# keep the router out of the rail strip: keepouts along all four edges on both layers
K = int(float(os.environ.get("KEEP", "0.85")) * 1000); Wd, Hd = 42000, 32000
rects = [(0, 0, Wd, K), (0, Hd - K, Wd, Hd), (0, 0, K, Hd), (Wd - K, 0, Wd, Hd)]
ko = ""
for lay in ("F.Cu", "B.Cu"):
    for x1, y1, x2, y2 in rects:
        ko += f'    (keepout "" (polygon {lay} 0  {x1} {-y1}  {x2} {-y1}  {x2} {-y2}  {x1} {-y2}  {x1} {-y1}))\n'
t = open(dsn).read()
i = t.index("    (via ")
open(dsn, "w").write(t[:i] + ko + t[i:])
if os.path.exists(ses): os.remove(ses)
with open(os.path.join(work, "fr.log"), "w") as log:
    try:
        subprocess.run(["java", "-jar", os.path.join(D, "..", "fr.jar"), "-de", dsn, "-do", ses, "-mp", mp,
                        "--gui.enabled=false", "--api_server.enabled=false", "--feature_flags.save_jobs=false"],
                       stdout=log, stderr=subprocess.STDOUT, timeout=int(os.environ.get("FRT", "220")))
    except subprocess.TimeoutExpired:
        print("router timeout")
txt = open(os.path.join(work, "fr.log")).read()
inc = re.findall(r'"incomplete_count": (\d+)', txt)
print(tag, "incomplete", inc[-1] if inc else "?")
if not os.path.exists(ses): sys.exit("no session")
b = pcbnew.LoadBoard(src)
layers = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}
s = open(ses).read(); u = 10000.0; nw = nv = 0
for blk in re.split(r'\n\s+\(net ', s.split("(network_out")[1])[1:]:
    name = blk.split("\n")[0].strip()
    if name.startswith('"'): name = name[1:name.index('"', 1)]
    net = b.FindNet(name)
    assert net is not None, name
    for lay, w, pts in re.findall(r'\(path (\S+) (\d+)\s+([-\d\s]+)\)', blk):
        c = [int(v) / u for v in pts.split()]
        p = [(c[i], -c[i + 1]) for i in range(0, len(c), 2)]
        for (x1, y1), (x2, y2) in zip(p, p[1:]):
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(VECTOR2I(FromMM(x1), FromMM(y1))); t.SetEnd(VECTOR2I(FromMM(x2), FromMM(y2)))
            t.SetWidth(int(int(w) / u * 1e6)); t.SetLayer(layers[lay]); t.SetNet(net); b.Add(t); nw += 1
    for dia, drl, x, y in re.findall(r'\(via "?Via\[0-1\]_(\d+):(\d+)_um"? (-?\d+) (-?\d+)', blk):
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(VECTOR2I(FromMM(int(x) / u), FromMM(-int(y) / u)))
        v.SetWidth(int(dia) * 1000); v.SetDrill(int(drl) * 1000)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net); b.Add(v); nv += 1
# add the top GND pour after routing (same settings as the bottom one)
zb = [z for z in b.Zones() if z.GetLayer() == pcbnew.B_Cu][0]
zt = zb.Duplicate(); zt.SetLayer(pcbnew.F_Cu); b.Add(zt)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
dst = os.path.join(work, "routed.kicad_pcb")
pcbnew.SaveBoard(dst, b)
shutil.copy(os.path.join(work, "spectre.kicad_pro"), os.path.join(work, "routed.kicad_pro"))
print(tag, "segments", nw, "vias", nv)
