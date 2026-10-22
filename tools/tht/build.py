"""SPECTRE rev D board builder: netlist, values, footprints and symbol links come from the approved schematic."""
import json, os, sys
import pcbnew
from pcbnew import VECTOR2I, FromMM

D = os.path.dirname(os.path.abspath(__file__))
LIB = "/usr/share/kicad/footprints"
layout = json.load(open(os.path.join(D, os.environ.get("LAYOUT", "layout_revd.json"))))
NET = json.load(open(os.path.join(D, "netmap_tht.json")))
W, H = layout["W"], layout["H"]
EDGE_CU = layout.get("edge_cu", 1.0)          # copper-to-edge clearance (mm)
OUTDIR = os.path.join(D, "board"); os.makedirs(OUTDIR, exist_ok=True)
PCB = os.path.join(OUTDIR, "spectre.kicad_pcb")
PRO = os.path.join(OUTDIR, "spectre.kicad_pro")

POWER_NETS = ["/+12V_IN", "+12V", "/LED_NEG"]          # GND is carried by the two pours
def netclass(name, tw, cl, vd, vdr):
    return {"bus_width": 12, "clearance": cl, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
            "diff_pair_width": 0.2, "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
            "name": name, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
            "track_width": tw, "via_diameter": vd, "via_drill": vdr, "wire_width": 6}
pro = json.load(open(os.path.join(D, "..", "revd", "spectre.kicad_pro")))          # keep schematic settings from the project
pro.setdefault("board", {}).setdefault("design_settings", {})
pro["board"]["design_settings"]["rules"] = {
    "min_clearance": 0.2, "min_copper_edge_clearance": EDGE_CU, "min_hole_clearance": 0.25,
    "min_track_width": 0.2, "min_via_diameter": 0.6, "min_via_annular_width": 0.13,
    "min_resolved_spokes": 1, "solder_mask_clearance": 0.0, "solder_mask_min_width": 0.0}
pro["net_settings"] = {
    "classes": [netclass("Default", 0.4, 0.2, 0.7, 0.35), netclass("Power", 1.2, 0.25, 0.9, 0.45)],
    "meta": {"version": 3}, "net_colors": None, "netclass_assignments": None,
    "netclass_patterns": [{"netclass": "Power", "pattern": p} for p in POWER_NETS]}
pro["meta"]["filename"] = "spectre.kicad_pro"
json.dump(pro, open(PRO, "w"), indent=2)

board = pcbnew.NewBoard(PCB)
ds = board.GetDesignSettings()
ds.SetCopperLayerCount(2)
ds.m_MinClearance = FromMM(0.2)
ds.m_TrackMinWidth = FromMM(0.2)
ds.m_ViasMinSize = FromMM(0.6)
ds.m_CopperEdgeClearance = FromMM(EDGE_CU)

nets = {}
def net(name):
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(board, name); board.Add(n); nets[name] = n
    return nets[name]

fps = {}
for ref, info in NET.items():
    x, y, rot = layout["place"][ref][:3]
    lib, name = info["fp"].split(":")
    fp = pcbnew.FootprintLoad(f"{LIB}/{lib}.pretty", name)
    assert fp is not None, info["fp"]
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    fp.SetReference(ref); fp.SetValue(info["value"])
    fp.SetPath(pcbnew.KIID_PATH("/" + info["tstamps"][0]))
    fp.SetProperty("Sheetfile", "spectre.kicad_sch"); fp.SetProperty("Sheetname", "")
    board.Add(fp)
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(VECTOR2I(FromMM(x), FromMM(y)))
    fp.Value().SetVisible(False)
    t = fp.Reference(); t.SetTextSize(VECTOR2I(FromMM(0.8), FromMM(0.8))); t.SetTextThickness(FromMM(0.15))
    if ref in layout.get("labels", {}):                    # label slot chosen by the placer (absolute angle)
        lx, ly, la = layout["labels"][ref]
        t.SetPosition(VECTOR2I(FromMM(lx), FromMM(ly))); t.SetTextAngleDegrees((la - rot) % 360)
    for p in fp.Pads():
        n = info["pins"].get(p.GetNumber(), "")
        if n: p.SetNet(net(n))
    fps[ref] = fp

def edge(x1, y1, x2, y2):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(VECTOR2I(FromMM(x1), FromMM(y1))); s.SetEnd(VECTOR2I(FromMM(x2), FromMM(y2)))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(FromMM(0.1)); board.Add(s)
edge(0, 0, W, 0); edge(W, 0, W, H); edge(W, H, 0, H); edge(0, H, 0, 0)

def gnd_zone(layer):
    z = pcbnew.ZONE(board); z.SetLayer(layer); z.SetNet(net("GND")); z.SetAssignedPriority(0)
    z.SetLocalClearance(FromMM(0.25)); z.SetMinThickness(FromMM(0.2))
    z.SetThermalReliefGap(FromMM(0.3)); z.SetThermalReliefSpokeWidth(FromMM(0.4))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    board.Add(z)
    o = z.Outline(); o.NewOutline()
    m = EDGE_CU
    for x, y in [(m, m), (W - m, m), (W - m, H - m), (m, H - m)]:
        o.Append(FromMM(x), FromMM(y))
if os.environ.get("ZONES", "1") == "1":
    gnd_zone(pcbnew.B_Cu)
    if os.environ.get("FZONE", "1") == "1":
        gnd_zone(pcbnew.F_Cu)

pcbnew.SaveBoard(PCB, board)
print("saved", PCB, len(fps), "footprints,", len(nets), "nets")
