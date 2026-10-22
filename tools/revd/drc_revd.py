import sys, os, re, shutil, pcbnew
S = os.path.dirname(os.path.abspath(__file__))
f = sys.argv[1] if len(sys.argv) > 1 else sys.argv[1]
# DRC needs the project file next to the board with the same stem
stem = os.path.splitext(f)[0]
pro = os.path.join(os.path.dirname(sys.argv[1]), "spectre.kicad_pro")
if not os.path.exists(stem + ".kicad_pro"): shutil.copy(pro, stem + ".kicad_pro")
b = pcbnew.LoadBoard(f)
rpt = stem + ".rpt"
pcbnew.WriteDRCReport(b, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
t = open(rpt).read()
for l in t.splitlines():
    if l.startswith("** Found"): print(l)
from collections import Counter
c = Counter(re.findall(r"^\[(\w+)\]", t, re.M))
c.pop("lib_footprint_issues", None)
print(dict(c))
if os.environ.get("V"):
    blocks = t.split("\n[")
    for bl in blocks[1:]:
        if bl.startswith("lib_footprint"): continue
        lines = [x.strip() for x in bl.splitlines() if x.strip().startswith("@") or not x.startswith(" ")]
        print("[" + " | ".join(lines[:4]))
