"""Check the board against the schematic netlist: every pad's net, value, footprint and symbol link."""
import json, os, sys, pcbnew
D = os.path.dirname(os.path.abspath(__file__))
N = json.load(open(os.path.join(D, "netmap_sch.json")))
b = pcbnew.LoadBoard(sys.argv[1])
fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
errs = 0; pins = 0
assert set(fps) == set(N), (set(fps) ^ set(N))
for ref, info in N.items():
    fp = fps[ref]
    fpid = fp.GetFPID(); name = f"{fpid.GetLibNickname()}:{fpid.GetLibItemName()}"
    if name != info["fp"]: print("FOOTPRINT", ref, name, info["fp"]); errs += 1
    if fp.GetValue() != info["value"]: print("VALUE", ref, fp.GetValue(), info["value"]); errs += 1
    if fp.GetPath().AsString() != "/" + info["tstamps"][0]: print("PATH", ref, fp.GetPath().AsString()); errs += 1
    seen = {}
    for p in fp.Pads():
        n = p.GetNumber()
        if not n: continue
        seen.setdefault(n, set()).add(p.GetNetname())
    for n, nets in seen.items():
        want = info["pins"].get(n, "")
        if nets != {want}: print("NET", ref, n, nets, "want", want); errs += 1
        pins += 1
    for n in info["pins"]:
        if n not in seen: print("MISSING PAD", ref, n); errs += 1
print(f"{len(N)} footprints, {pins} pads checked, {len({v for i in N.values() for v in i['pins'].values()})} nets, {errs} differences")
