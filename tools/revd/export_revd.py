"""Export the SPECTRE rev D manufacturing package into an output folder."""
import csv, os, shutil, subprocess, sys, zipfile
import pcbnew
D = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
SMT = os.path.join(D, "..", "..", "smt"); SCH = os.path.join(D, "..", "..", "docs")
os.makedirs(OUT, exist_ok=True)
pcb = os.path.join(OUT, "spectre.kicad_pcb")
shutil.copy(os.path.join(SMT, "spectre.kicad_pcb"), pcb)
shutil.copy(os.path.join(SMT, "spectre.kicad_pro"), os.path.join(OUT, "spectre.kicad_pro"))
shutil.copy(os.path.join(SMT, "spectre.kicad_sch"), os.path.join(OUT, "spectre.kicad_sch"))
for f in ("spectre-esquematico.pdf", "esquematico.png"):
    shutil.copy(os.path.join(SCH, f), os.path.join(OUT, f))

# Gerbers + drill
g = os.path.join(D, "export", "gerbers"); shutil.rmtree(g, ignore_errors=True); os.makedirs(g)
subprocess.run(["kicad-cli", "pcb", "export", "gerbers", "--layers",
                "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts",
                "--subtract-soldermask", "-o", g + "/", pcb], check=True, capture_output=True)
subprocess.run(["kicad-cli", "pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm",
                "--generate-map", "--map-format", "gerberx2", "-o", g + "/", pcb], check=True, capture_output=True)
with zipfile.ZipFile(os.path.join(OUT, "spectre-gerbers.zip"), "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(g)): z.write(os.path.join(g, f), f)
print("gerbers:", sorted(os.listdir(g)))

# BOM / CPL
MPN = {  # (value, footprint) -> (manufacturer part, description)
    ("0.33uF", "C_0805_2012Metric"): ("CL21B334KBFNNNE (o equivalente)", "Cerámico 0805 X7R 50 V"),
    ("0.1uF", "C_0805_2012Metric"): ("CL21B104KBCNNNC (o equivalente)", "Cerámico 0805 X7R 50 V"),
    ("0.1uF", "C_0603_1608Metric"): ("CL10B104KB8NNNC (o equivalente)", "Cerámico 0603 X7R 50 V, desacoplo de U2"),
    ("22uF", "C_0805_2012Metric"): ("22 µF 0805 X5R, 16 V o más (o equivalente)", "Cerámico 0805 X5R, retardo de armado (C6)"),
    ("47uF 16V", "CP_Elec_5x5.3"): ("Panasonic EEE-1CA470WR", "Electrolítico SMD"),
    ("22uF 16V", "CP_Elec_4x5.4"): ("Panasonic EEE-1CA220WR", "Electrolítico SMD"),
    ("M7", "D_SMA"): ("M7 (1000 V 1 A, SMA)", "Diodo rectificador"),
    ("1N4148W", "D_SOD-123"): ("1N4148W (SOD-123)", "Diodo de señal"),
    ("10k trim", "Potentiometer_Bourns_3314J_Vertical"): ("Bourns 3314J-1-103E", "Trimpot 10 kΩ SMD"),
    ("10k", "R_0603_1608Metric"): ("0603WAF1002T5E (o equivalente)", "Resistencia 0603 1% 1/10 W"),
    ("100k", "R_0603_1608Metric"): ("0603WAF1003T5E (o equivalente)", "Resistencia 0603 1% 1/10 W"),
    ("1M", "R_0603_1608Metric"): ("0603WAF1004T5E (o equivalente)", "Resistencia 0603 1% 1/10 W"),
    ("1k", "R_0603_1608Metric"): ("0603WAF1001T5E (o equivalente)", "Resistencia 0603 1% 1/10 W"),
    ("68k", "R_0603_1608Metric"): ("0603WAF6802T5E (o equivalente)", "Resistencia 0603 1% 1/10 W"),
    ("LM393", "SOIC-8_3.9x4.9mm_P1.27mm"): ("LM393DR", "Comparador dual SOIC-8"),
    ("MMBT2222A", "SOT-23"): ("MMBT2222A (SOT-23)", "NPN"),
    ("DRV5033FA", "SOT-23-3"): ("DRV5033FAQDBZR", "Sensor Hall omnipolar, 3.5 mT, SOT-23 (TI)"),
    ("IRLR2905", "TO-252-2"): ("IRLR2905TRPBF", "N-MOSFET nivel lógico 55 V, DPAK"),
    ("L78M05", "TO-252-2"): ("L78M05ABDT-TR", "Regulador 5 V 500 mA, DPAK"),
    ("12V IN", "JST_VH_B2P-VH_1x02_P3.96mm_Vertical"): ("JST B2P-VH(LF)(SN)", "Header VH 2P top entry, THT; acopla con VHR-2N"),
    ("LED 12V", "JST_VH_B2P-VH_1x02_P3.96mm_Vertical"): ("JST B2P-VH(LF)(SN)", "Header VH 2P top entry, THT; acopla con VHR-2N"),
    ("GL5528", "R_LDR_5.1x4.3mm_P3.4mm_Vertical"): ("GL5528", "Fotorresistencia 5 mm, THT"),
}
COMMENT = {"0.33uF": "0.33uF 50V X7R", "0.1uF": "0.1uF 50V X7R", "22uF": "22uF 16V X5R", "LM393": "LM393 SOIC-8",
           "IRLR2905": "IRLR2905 DPAK", "L78M05": "L78M05 DPAK", "10k trim": "10k trim 3314J",
           "12V IN": "B2P-VH", "LED 12V": "B2P-VH"}
b = pcbnew.LoadBoard(pcb)
def key(r): return (r.rstrip("0123456789"), int("".join(c for c in r if c.isdigit()) or 0))
groups = {}
for fp in b.GetFootprints():
    fpn = str(fp.GetFPID().GetLibItemName()); val = fp.GetValue()
    mpn, desc = MPN[(val, fpn)]
    tht = any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in fp.Pads())
    k = (COMMENT.get(val, val), fpn, mpn, desc, "THT" if tht else "SMT")
    groups.setdefault(k, []).append(fp.GetReference())
rows = sorted(groups.items(), key=lambda kv: (kv[0][4], key(sorted(kv[1], key=key)[0])))
with open(os.path.join(OUT, "spectre-BOM.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["Comment", "Designator", "Footprint", "Manufacturer Part", "Descripción", "Cantidad", "Montaje"])
    for (c, fpn, mpn, desc, mnt), refs in rows:
        w.writerow([c, ",".join(sorted(refs, key=key)), fpn, mpn, desc, len(refs), mnt])
with open(os.path.join(OUT, "spectre-CPL.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for fp in sorted(b.GetFootprints(), key=lambda x: key(x.GetReference())):
        p = fp.GetPosition()
        w.writerow([fp.GetReference(), "%.3fmm" % (p.x / 1e6), "%.3fmm" % (-p.y / 1e6), "Top", "%g" % (fp.GetOrientationDegrees() % 360)])
print("BOM lines", len(rows), "parts", sum(len(v) for v in groups.values()))

# previews
import cairosvg
def svg2png(layers, out, width, bw=False, bg="white"):
    tmp = os.path.join(D, "export", "tmp.svg")
    cmd = ["kicad-cli", "pcb", "export", "svg", "--layers", layers, "--page-size-mode", "2", "--exclude-drawing-sheet", "-o", tmp, pcb]
    if bw: cmd.insert(4, "--black-and-white")
    subprocess.run(cmd, check=True, capture_output=True)
    cairosvg.svg2png(url=tmp, write_to=out, output_width=width, background_color=bg); os.remove(tmp)
svg2png("F.Cu,B.Cu,F.SilkS,Edge.Cuts", os.path.join(OUT, "vista-superior.png"), 1400)
subprocess.run([sys.executable, os.path.join(D, "asmmap.py"), pcb, os.path.join(OUT, "mapa-ensamble.png")], check=True)
subprocess.run([sys.executable, os.path.join(D, "..", "render.py"), pcb, os.path.join(OUT, "vista-inferior-logo.png")], check=True)
shutil.copy(os.path.join(SCH, "logo-MKr-SPECTRE.svg"), os.path.join(OUT, "logo-MKr-SPECTRE.svg"))
# DRC report for the delivered board
env = dict(os.environ, KICAD7_FOOTPRINT_DIR="/usr/share/kicad/footprints", KICAD7_SYMBOL_DIR="/usr/share/kicad/symbols")
subprocess.run([sys.executable, os.path.join(D, "drc_revd.py"), pcb], check=True, capture_output=True, env=env)
os.replace(os.path.join(OUT, "spectre.rpt"), os.path.join(OUT, "drc.rpt"))
for junk in ("spectre.kicad_prl",):
    if os.path.exists(os.path.join(OUT, junk)): os.remove(os.path.join(OUT, junk))
print(sorted(os.listdir(OUT)))
