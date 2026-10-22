"""SPECTRE schematic generator with real wires. Coordinates in grid units u = 1.27 mm."""
import os, sys, uuid, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import lib_symbol, sym_pins, props, dump, q

U = 1.27
OUT = sys.argv[1] if len(sys.argv) > 1 else "spectre.kicad_sch"
ROOT = str(uuid.uuid5(uuid.NAMESPACE_DNS, "spectre-root"))
_n = [0]
def uid():
    _n[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"spectre-{_n[0]}"))

LIB = {
    "R": ("Device", "R"), "C": ("Device", "C"), "CP": ("Device", "C_Polarized"), "D": ("Device", "D"),
    "NPN": ("Device", "Q_NPN_BEC"), "NMOS": ("Device", "Q_NMOS_GDS"), "LDR": ("Device", "R_Photo"),
    "POT": ("Device", "R_Potentiometer_Trim"), "REG": ("Regulator_Linear", "L7805"),
    "CMP": ("Comparator", "LM2903"), "HALL": ("Sensor_Magnetic", "DRV5033FAxDBZ"),
    "CONN": ("Connector_Generic", "Conn_01x02"),
    "+5V": ("power", "+5V"), "+12V": ("power", "+12V"), "GND": ("power", "GND"), "FLAG": ("power", "PWR_FLAG"),
}
FP = {
    "R": "Resistor_SMD:R_0603_1608Metric", "C0805": "Capacitor_SMD:C_0805_2012Metric",
    "C0603": "Capacitor_SMD:C_0603_1608Metric", "CP5": "Capacitor_SMD:CP_Elec_5x5.3",
    "CP4": "Capacitor_SMD:CP_Elec_4x5.4", "SMA": "Diode_SMD:D_SMA", "SOD": "Diode_SMD:D_SOD-123",
    "SOT": "Package_TO_SOT_SMD:SOT-23", "SOT3": "Package_TO_SOT_SMD:SOT-23-3", "DPAK": "Package_TO_SOT_SMD:TO-252-2",
    "SOIC": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "POT": "Potentiometer_SMD:Potentiometer_Bourns_3314J_Vertical",
    "LDR": "OptoDevice:R_LDR_5.1x4.3mm_P3.4mm_Vertical", "VH": "Connector_JST:JST_VH_B2P-VH_1x02_P3.96mm_Vertical",
}

def rot(x, y, r):
    return {0: (x, y), 90: (-y, x), 180: (-x, -y), 270: (y, -x)}[r]

symbols, pinpos, wires, labels, texts, noconn = [], {}, [], [], [], []
lib_used = {}
pwr_n = [0]

def place(ref, kind, gx, gy, r=0, value="", fp="", unit=1, mirror=False, refpos=None, valpos=None, hide_val=False):
    lib, name = LIB[kind]
    s = lib_symbol(lib, name); lid = f"{lib}:{name}"; lib_used[lid] = s
    X, Y = gx * U, gy * U
    pins = sym_pins(s)
    pr = props(s)
    is_pwr = lib == "power"
    if is_pwr:
        pwr_n[0] += 1
        ref = ("#FLG" if kind == "FLAG" else "#PWR") + f"{pwr_n[0]:02d}"
        value = name
    node = ["symbol", ["lib_id", q(lid)], ["at", f"{X:.2f}", f"{Y:.2f}", str(r)]]
    if mirror: node.append(["mirror", "y"])
    node += [["unit", str(unit)], ["in_bom", "no" if is_pwr else "yes"], ["on_board", "no" if is_pwr else "yes"],
             ["dnp", "no"], ["uuid", q(uid())]]
    def fieldpos(key, override):
        if override is not None:
            ox, oy, just = override
            return (X + ox * U, Y + oy * U, just)
        at = next(e for e in pr[key] if isinstance(e, list) and e[0] == "at")
        lx, ly = float(at[1]), float(at[2])
        if mirror: lx = -lx
        rx, ry = rot(lx, ly, r) if not is_pwr else (lx, ly)
        return (X + rx, Y - ry, None)
    F = ["font", ["size", "1.27", "1.27"]]
    for key, val, ov, hidden in (("Reference", ref, refpos, is_pwr), ("Value", value, valpos, hide_val)):
        x, y, just = fieldpos(key, ov)
        eff = ["effects", F]
        if just: eff.append(["justify", just])
        if hidden: eff.append("hide")
        node.append(["property", q(key), q(val), ["at", f"{x:.2f}", f"{y:.2f}", "90" if r in (90, 270) and not is_pwr else "0"], eff])
    node.append(["property", q("Footprint"), q(fp), ["at", f"{X:.2f}", f"{Y:.2f}", "0"], ["effects", F, "hide"]])
    node.append(["property", q("Datasheet"), q("~"), ["at", f"{X:.2f}", f"{Y:.2f}", "0"], ["effects", F, "hide"]])
    for num, lst in pins.items():
        for (px, py, pa, pl, pu, pn) in lst:
            if pu not in (0, unit): continue
            node.append(["pin", q(num), ["uuid", q(uid())]])
            if mirror: px = -px
            dx, dy = rot(px, py, r)
            pinpos[(ref, num)] = (round(X + dx, 2), round(Y - dy, 2))
    node.append(["instances", ["project", q("spectre"), ["path", q("/" + ROOT), ["reference", q(ref)], ["unit", str(unit)]]]])
    symbols.append(node)
    return ref

def pwr(kind, gx, gy):
    return place(None, kind, gx, gy)

def P(ref, num):
    x, y = pinpos[(ref, num)]
    return (round(x / U), round(y / U))

def W(*pts):
    """Polyline in grid units; pts may be (gx,gy) tuples or ('ref','pin')."""
    pp = [P(*p) if isinstance(p[0], str) else p for p in pts]
    for a, b in zip(pp, pp[1:]):
        if a != b:
            assert a[0] == b[0] or a[1] == b[1], ("diagonal wire", a, b)
            wires.append((a, b))

def label(name, gx, gy, ang=0):
    labels.append((name, gx, gy, ang))

def text(t, gx, gy, size=2.0):
    texts.append((t, gx, gy, size))

# ======================= A) ALIMENTACIÓN =======================
text("Alimentación 12 V → 5 V", 14, 22)
place("J1", "CONN", 18, 30, mirror=True, value="12V IN", fp=FP["VH"], refpos=(0, -2.5, None), valpos=(0, 4.5, None))
place("D1", "D", 30, 30, r=180, value="M7", fp=FP["SMA"], refpos=(0, -2.2, None), valpos=(0, 2.4, None))
place("C1", "C", 40, 34, value="0.33uF", fp=FP["C0805"], refpos=(1.8, -0.7, "left"), valpos=(1.8, 0.8, "left"))
place("U1", "REG", 52, 30, value="L78M05", fp=FP["DPAK"], refpos=(0, -3.2, None), valpos=(1.5, 8.6, "left"))
place("C2", "C", 64, 34, value="0.1uF", fp=FP["C0805"], refpos=(1.8, -0.7, "left"), valpos=(1.8, 0.8, "left"))
W(("J1", "1"), ("D1", "2"))
label("+12V_IN", 23, 30)
W(("D1", "1"), (36, 30), (44, 30), (46, 30))
W((40, 30), ("C1", "1"))
pwr("+12V", 36, 30)
pwr("FLAG", 44, 26); W((44, 26), (44, 30))
W(("U1", "3"), (70, 30)); W((64, 30), ("C2", "1"))
pwr("+5V", 70, 30)
pwr("GND", 40, 38); W(("C1", "2"), (40, 38))
pwr("GND", 64, 38); W(("C2", "2"), (64, 38))
pwr("GND", 52, 38); W(("U1", "2"), (52, 38))
W(("J1", "2"), (25, 32), (25, 38))
pwr("GND", 25, 38)
pwr("FLAG", 29, 38); W((25, 38), (29, 38))

# ======================= B) SENSOR HALL + RETARDO =======================
text("Sensor Hall y retardo de armado (~0.75 s)", 14, 58)
place("U2", "HALL", 24, 75, value="DRV5033FA", fp=FP["SOT3"], refpos=(4, 6.5, "left"), valpos=(4, 8, "left"))
pwr("+5V", 22, 64); W((22, 64), ("U2", "1"))
pwr("GND", 22, 88); W(("U2", "3"), (22, 88))
place("C5", "C", 16, 76, value="0.1uF", fp=FP["C0603"], refpos=(-1.8, -0.7, "right"), valpos=(-1.8, 0.8, "right"))
pwr("+5V", 16, 70); W((16, 70), ("C5", "1"))
pwr("GND", 16, 82); W(("C5", "2"), (16, 82))
place("R11", "R", 34, 69, value="10k", fp=FP["R"], refpos=(1.8, -0.7, "left"), valpos=(1.8, 0.8, "left"))
pwr("+5V", 34, 64); W((34, 64), ("R11", "1"))
W(("U2", "2"), (41, 75)); W(("R11", "2"), (34, 75))
label("HALL_OUT", 31, 75)
place("R15", "R", 44, 75, r=90, value="100k", fp=FP["R"], refpos=(0, -2.6, None), valpos=(0, 2, None))
place("D4", "D", 44, 81, value="1N4148W", fp=FP["SOD"], refpos=(0, -2.2, None), valpos=(0, 2.4, None))
W((38, 75), (38, 81), ("D4", "1"))
W(("R15", "2"), (74, 75))
W(("D4", "2"), (52, 81), (52, 75))
label("DELAY", 60, 75)
place("C6", "C", 56, 80, value="10uF", fp=FP["C0805"], refpos=(1.8, -0.7, "left"), valpos=(1.8, 0.8, "left"))
W((56, 75), ("C6", "1")); pwr("GND", 56, 85); W(("C6", "2"), (56, 85))
place("U3", "CMP", 80, 77, unit=2, value="LM393", fp=FP["SOIC"], refpos=(0, -5.5, None), valpos=(0, 4.5, None))
place("R16", "R", 68, 86, value="100k", fp=FP["R"], refpos=(-1.8, -0.7, "right"), valpos=(-1.8, 0.8, "right"))
place("R17", "R", 68, 92, value="100k", fp=FP["R"], refpos=(-1.8, -0.7, "right"), valpos=(-1.8, 0.8, "right"))
pwr("+5V", 68, 83)
W(("R16", "2"), ("R17", "1"))
pwr("GND", 68, 95)
W((68, 89), (72, 89), (72, 79), ("U3", "6"))
label("VTH", 69, 89)
place("R18", "R", 90, 71, value="10k", fp=FP["R"], refpos=(1.8, -0.7, "left"), valpos=(1.8, 0.8, "left"))
pwr("+5V", 90, 66); W((90, 66), ("R18", "1"))
W(("R18", "2"), (90, 77))
W(("U3", "7"), (103, 77))
label("ARM", 92, 77)

# ======================= C) LDR + COMPARADOR =======================
text("Detección de oscuridad (LDR + comparador con histéresis)", 14, 104)
place("R8", "R", 40, 117, value="10k", fp=FP["R"], refpos=(1.8, -0.7, "left"), valpos=(1.8, 0.8, "left"))
pwr("+5V", 40, 112); W((40, 112), ("R8", "1"))
place("LDR1", "LDR", 40, 127, value="GL5528", fp=FP["LDR"], refpos=(1.8, 1.2, "left"), valpos=(1.8, 2.7, "left"))
W(("R8", "2"), ("LDR1", "1"))
pwr("GND", 40, 132); W(("LDR1", "2"), (40, 132))
place("C3", "CP", 50, 127, value="47uF 16V", fp=FP["CP5"], refpos=(1.8, -0.7, "left"), valpos=(1.8, 0.8, "left"))
pwr("GND", 50, 132); W(("C3", "2"), (50, 132))
place("U3", "CMP", 80, 126, unit=1, value="LM393", fp=FP["SOIC"], refpos=(0, -5.5, None), valpos=(0, 4.5, None))
W((40, 124), (50, 124), (60, 124), ("U3", "3"))
label("LDR_DIV", 41, 124)
place("R13", "R", 73, 117, r=270, value="100k", fp=FP["R"], refpos=(0, -2, None), valpos=(0, 2, None))
W((60, 124), (60, 117), ("R13", "2"))
W(("R13", "1"), (92, 117), (92, 126))
place("R9", "POT", 64, 135, value="10k trim", fp=FP["POT"], refpos=(-2, -0.7, "right"), valpos=(-2, 0.8, "right"))
pwr("+5V", 64, 130); W((64, 130), ("R9", "1"))
pwr("GND", 64, 140); W(("R9", "3"), (64, 140))
W(("R9", "2"), (72, 135), (72, 128), ("U3", "2"))
label("REF", 68, 135)
place("R10", "R", 96, 120, value="10k", fp=FP["R"], refpos=(1.8, -0.7, "left"), valpos=(1.8, 0.8, "left"))
pwr("+5V", 96, 115); W((96, 115), ("R10", "1"))
W(("R10", "2"), (96, 126))
W(("U3", "1"), (100, 126), (100, 89), (103, 89))
label("CMP_OUT", 87, 126)
place("U3", "CMP", 82, 148, unit=3, value="LM393", fp=FP["SOIC"], refpos=(3, -1, "left"), valpos=(3, 1, "left"))
pwr("+5V", 80, 140); W((80, 140), ("U3", "8"))
pwr("GND", 80, 156); W(("U3", "4"), (80, 156))

# ======================= D) LÓGICA: AND con latch =======================
text("Lógica: ARM AND oscuro, con latch", 104, 46)
place("R1", "R", 106, 77, r=90, value="10k", fp=FP["R"], refpos=(0, -2, None), valpos=(0, 2, None))
place("Q1", "NPN", 116, 77, value="MMBT2222A", fp=FP["SOT"], refpos=(3.5, -0.7, "left"), valpos=(3.5, 0.8, "left"))
W(("R1", "2"), ("Q1", "1"))
place("R3", "R", 118, 66, value="10k", fp=FP["R"], refpos=(1.8, -0.7, "left"), valpos=(1.8, 0.8, "left"))
pwr("+5V", 118, 61); W((118, 61), ("R3", "1"))
W(("R3", "2"), ("Q1", "3"))
place("Q2", "NPN", 116, 89, value="MMBT2222A", fp=FP["SOT"], refpos=(3.5, -0.7, "left"), valpos=(3.5, 0.8, "left"))
W(("Q1", "2"), ("Q2", "3"))
pwr("GND", 118, 96); W(("Q2", "2"), (118, 96))
place("R2", "R", 106, 89, r=90, value="10k", fp=FP["R"], refpos=(0, -2, None), valpos=(0, 2, None))
W(("R2", "2"), ("Q2", "1"))
place("R12", "R", 114, 102, r=270, value="10k", fp=FP["R"], refpos=(0, -2, None), valpos=(0, 2, None))
W((110, 89), (110, 102), ("R12", "2"))
place("D2", "D", 122, 102, value="1N4148W", fp=FP["SOD"], refpos=(0, -2.2, None), valpos=(0, 2.4, None))
W(("R12", "1"), ("D2", "1"))
label("LATCH", 117, 102)
W((118, 71), (125, 71))
label("NODO_A", 119, 71)
place("R4", "R", 128, 71, r=90, value="10k", fp=FP["R"], refpos=(0, -2, None), valpos=(0, 2, None))
place("Q3", "NPN", 138, 71, value="MMBT2222A", fp=FP["SOT"], refpos=(0.5, -6.6, "right"), valpos=(0.5, -5.1, "right"))
W(("R4", "2"), ("Q3", "1"))
pwr("GND", 140, 78); W(("Q3", "2"), (140, 78))
place("R5", "R", 140, 59, value="1k", fp=FP["R"], refpos=(1.8, -0.7, "left"), valpos=(1.8, 0.8, "left"))
pwr("+5V", 140, 54); W((140, 54), ("R5", "1"))
W(("R5", "2"), ("Q3", "3"))
W((140, 65), (157, 65))
label("NODO_B", 141, 65)
W((146, 65), (146, 102), ("D2", "2"))

# ======================= E) FADE + POTENCIA =======================
text("Fade y etapa de potencia", 160, 46)
place("R6", "R", 160, 65, r=90, value="100k", fp=FP["R"], refpos=(0, -2, None), valpos=(0, 2, None))
W(("R6", "2"), (186, 65))
place("D3", "D", 154, 72, r=180, value="1N4148W", fp=FP["SOD"], refpos=(0, 2.2, None), valpos=(0, 3.8, None))
W((150, 65), (150, 72), ("D3", "2"))
place("R14", "R", 161, 72, r=90, value="68k", fp=FP["R"], refpos=(0, 2, None), valpos=(0, 3.6, None))
W(("D3", "1"), ("R14", "1"))
label("FAST", 157, 72)
W(("R14", "2"), (168, 72), (168, 65))
place("R7", "R", 172, 72, value="1M", fp=FP["R"], refpos=(1.8, -0.7, "left"), valpos=(1.8, 0.8, "left"))
W((172, 65), ("R7", "1")); pwr("GND", 172, 78); W(("R7", "2"), (172, 78))
place("C4", "CP", 179, 72, value="22uF 16V", fp=FP["CP4"], refpos=(1.8, -0.7, "left"), valpos=(1.8, 0.8, "left"))
W((179, 65), ("C4", "1")); pwr("GND", 179, 78); W(("C4", "2"), (179, 78))
label("GATE", 164, 65)
place("Q4", "NMOS", 190, 65, value="IRLR2905", fp=FP["DPAK"], refpos=(3.5, -0.7, "left"), valpos=(3.5, 0.8, "left"))
pwr("GND", 192, 72); W(("Q4", "3"), (192, 72))
place("J2", "CONN", 210, 56, value="LED 12V", fp=FP["VH"], refpos=(0, -2.5, None), valpos=(0, 4.5, None))
W(("Q4", "2"), (192, 58), ("J2", "2"))
label("LED_NEG", 194, 58)
W(("J2", "1"), (200, 56), (200, 52))
pwr("+12V", 200, 52)

notes = [
    "Retardo de armado: al abrir, C6 se carga por R11+R15; U3B habilita ARM cuando DELAY > VTH (2.5 V): t ≈ 0.69·110k·10µF ≈ 0.75 s.",
    "Al cerrar, el DRV5033 lleva HALL_OUT a GND y D4 descarga C6 al instante: ARM baja, el latch se libera y empieza el fade.",
    "Encendido: ARM (cajuela abierta y retardo cumplido) AND CMP_OUT (oscuro) → Q1+Q2 bajan NODO_A → Q3 apaga → NODO_B sube.",
    "Latch: NODO_B → D2 → R12 mantiene Q2 encendido aunque la LDR vea luz después.",
]
for i, t in enumerate(notes):
    text(t, 104, 164 + i * 4, 1.27)

# ======================= connectivity bookkeeping =======================
def on_seg(p, a, b):
    if a[0] == b[0] == p[0]:
        return min(a[1], b[1]) < p[1] < max(a[1], b[1])
    if a[1] == b[1] == p[1]:
        return min(a[0], b[0]) < p[0] < max(a[0], b[0])
    return False

# split every segment at interior points that are endpoints of other segments (KiCad connects only at ends)
changed = True
while changed:
    changed = False
    endpts = {p for a, b in wires for p in (a, b)}
    nw = []
    for a, b in wires:
        cut = sorted([p for p in endpts if on_seg(p, a, b)], key=lambda p: abs(p[0]-a[0]) + abs(p[1]-a[1]))
        if cut:
            changed = True
            pts = [a] + cut + [b]
            nw += list(zip(pts, pts[1:]))
        else:
            nw.append((a, b))
    wires[:] = nw
pin_pts = {}
for (ref, num), (x, y) in pinpos.items():
    pin_pts.setdefault((round(x / U), round(y / U)), []).append((ref, num))
ends = {}
for a, b in wires:
    for p in (a, b):
        ends[p] = ends.get(p, 0) + 1
junctions = set()
problems = []
for p, n in ends.items():
    deg = n + len(pin_pts.get(p, []))
    mid = any(on_seg(p, a, b) for a, b in wires)
    if mid:
        junctions.add(p)
    elif deg >= 3:
        junctions.add(p)
for p, who in pin_pts.items():
    for a, b in wires:
        if on_seg(p, a, b):
            problems.append(("pin on wire interior", who, p))
# dangling wire ends: an endpoint touched by exactly one wire and nothing else
for p, n in ends.items():
    if n == 1 and p not in pin_pts and not any((gx, gy) == p for _, gx, gy, _a in labels):
        problems.append(("dangling wire end", p))
lab_ok = []
for name, gx, gy, ang in labels:
    hit = any(on_seg((gx, gy), a, b) or (gx, gy) in (a, b) for a, b in wires)
    if not hit: problems.append(("label not on wire", name, (gx, gy)))
# every non-power pin must touch a wire end or a power symbol
for (ref, num), (x, y) in pinpos.items():
    p = (round(x / U), round(y / U))
    if ref.startswith("#"): continue
    if p not in ends and len(pin_pts[p]) < 2:
        problems.append(("pin unconnected", ref, num, p))

# ======================= write file =======================
F = lambda v: f"{v * U:.2f}"
L = ['(kicad_sch (version 20230121) (generator eeschema)', f'  (uuid "{ROOT}")', '  (paper "A3")',
     '  (title_block (title "SPECTRE — luz de cajuela") (date "2026-10-15") (rev "D") (company "MKr")'
     ' (comment 1 "Hall DRV5033 + LDR, retardo de armado con U3B, latch NPN, fade en gate"))',
     '  (lib_symbols']
for lid, s in lib_used.items():
    s2 = list(s); s2[1] = q(lid); L.append("    " + dump(s2))
L.append("  )")
for p in sorted(junctions):
    L.append(f'  (junction (at {F(p[0])} {F(p[1])}) (diameter 0) (color 0 0 0 0) (uuid "{uid()}"))')
for name, gx, gy, ang in labels:
    L.append(f'  (label "{name}" (at {F(gx)} {F(gy)} {ang}) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{uid()}"))')
for a, b in wires:
    L.append(f'  (wire (pts (xy {F(a[0])} {F(a[1])}) (xy {F(b[0])} {F(b[1])})) (stroke (width 0) (type default)) (uuid "{uid()}"))')
for t, gx, gy, size in texts:
    L.append(f'  (text "{t}" (at {F(gx)} {F(gy)} 0) (effects (font (size {size} {size}) bold) (justify left bottom)) (uuid "{uid()}"))')
for s in symbols:
    L.append("  " + dump(s))
L.append('  (sheet_instances (path "/" (page "1")))')
L.append(")")
open(OUT, "w").write("\n".join(L) + "\n")
print("symbols", len(symbols), "wires", len(wires), "junctions", len(junctions), "labels", len(labels))
for pr_ in problems: print("PROBLEM", pr_)
