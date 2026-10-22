"""Assembly map: F.Fab outlines of every part with its reference centred on the body; the rev D arming-delay
parts are tinted red. usage: python3 asmmap.py <pcb> <png>"""
import sys, math, pcbnew
from PIL import Image, ImageDraw, ImageFont
f, out = sys.argv[1], sys.argv[2]
NEW = {"R15", "R16", "R17", "R18", "C6", "D4"}
K = 2; SC = 44 * K; M = 24 * K; W, H = 42.0, 32.0; LEG = 70 * K
img = Image.new("RGB", (int(W * SC) + 2 * M, int(H * SC) + 2 * M + LEG), "white"); d = ImageDraw.Draw(img)
P = lambda x, y: (M + x * SC, M + y * SC)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
b = pcbnew.LoadBoard(f)
def mm(v): return v / 1e6
fab = {}
for fp in b.GetFootprints():
    items = [g for g in fp.GraphicalItems() if g.GetLayer() == pcbnew.F_Fab and g.GetClass() not in ("FP_TEXT", "PCB_TEXT")]
    bbs = [g.GetBoundingBox() for g in items]
    fab[fp.GetReference()] = (items, (mm(min(r.GetLeft() for r in bbs)), mm(min(r.GetTop() for r in bbs)),
                                      mm(max(r.GetRight() for r in bbs)), mm(max(r.GetBottom() for r in bbs))))
# tint the new parts
for r, (items, (x0, y0, x1, y1)) in fab.items():
    if r in NEW: d.rectangle([P(x0, y0), P(x1, y1)], fill=(255, 214, 214))
# rail strip
for x in range(0, int(W * SC), 14 * K):
    d.line([P(x / SC, 1.0), P(min(x / SC + 0.15, W - 1), 1.0)], fill=(170, 170, 170), width=K)
    d.line([P(x / SC, H - 1.0), P(min(x / SC + 0.15, W - 1), H - 1.0)], fill=(170, 170, 170), width=K)
for y in range(0, int(H * SC), 14 * K):
    d.line([P(1.0, y / SC), P(1.0, min(y / SC + 0.15, H - 1))], fill=(170, 170, 170), width=K)
    d.line([P(W - 1.0, y / SC), P(W - 1.0, min(y / SC + 0.15, H - 1))], fill=(170, 170, 170), width=K)
d.rectangle([P(0, 0), P(W, H)], outline=(0, 0, 0), width=3 * K)
def arcpts(g):
    c = g.GetCenter(); r = mm(g.GetRadius())
    a0 = math.atan2(mm(g.GetStart().y - c.y), mm(g.GetStart().x - c.x)); a1 = math.atan2(mm(g.GetEnd().y - c.y), mm(g.GetEnd().x - c.x))
    am = math.atan2(mm(g.GetArcMid().y - c.y), mm(g.GetArcMid().x - c.x))
    def between(a, s, e):
        return (a - s) % (2 * math.pi) <= (e - s) % (2 * math.pi)
    if not between(am, a0, a1): a0, a1 = a1, a0
    span = (a1 - a0) % (2 * math.pi); n = max(8, int(span * 20))
    return [P(mm(c.x) + r * math.cos(a0 + span * i / n), mm(c.y) + r * math.sin(a0 + span * i / n)) for i in range(n + 1)]
for r, (items, bb) in fab.items():
    col = (150, 0, 0) if r in NEW else (0, 0, 0)
    for g in items:
        w = max(2 * K, int(mm(g.GetWidth()) * SC))
        sh = g.GetShape()
        if sh == pcbnew.SHAPE_T_SEGMENT:
            d.line([P(mm(g.GetStart().x), mm(g.GetStart().y)), P(mm(g.GetEnd().x), mm(g.GetEnd().y))], fill=col, width=w)
        elif sh == pcbnew.SHAPE_T_RECT:
            s, e = g.GetStart(), g.GetEnd()
            d.rectangle([P(mm(min(s.x, e.x)), mm(min(s.y, e.y))), P(mm(max(s.x, e.x)), mm(max(s.y, e.y)))], outline=col, width=w)
        elif sh == pcbnew.SHAPE_T_CIRCLE:
            c = g.GetCenter(); rr = mm(g.GetRadius()); x, y = P(mm(c.x), mm(c.y))
            d.ellipse([x - rr * SC, y - rr * SC, x + rr * SC, y + rr * SC], outline=col, width=w)
        elif sh == pcbnew.SHAPE_T_ARC:
            d.line(arcpts(g), fill=col, width=w, joint="curve")
        elif sh == pcbnew.SHAPE_T_POLY:
            ps = g.GetPolyShape()
            for i in range(ps.OutlineCount()):
                o = ps.Outline(i); pts = [P(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())]
                if g.IsFilled(): d.polygon(pts, fill=col)
                else: d.line(pts + pts[:1], fill=col, width=w)
# labels (diodes get theirs beside the body so the polarity symbol stays visible)
boxes = {r: bb for r, (items, bb) in fab.items()}
def ovl(a, b_): return not (a[2] <= b_[0] or b_[2] <= a[0] or a[3] <= b_[1] or b_[3] <= a[1])
taken = []
for r, (items, (x0, y0, x1, y1)) in fab.items():
    bw, bh = (x1 - x0) * SC, (y1 - y0) * SC; cx, cy = P((x0 + x1) / 2, (y0 + y1) / 2)
    if r.startswith("D"):
        fnt = ImageFont.truetype(FB, int(0.6 * SC)); tw = d.textlength(r, font=fnt) / SC; th = 0.6
        g = 0.2; mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        cands = [(x1 + g + tw / 2 + 0.05, my), (x0 - g - tw / 2 - 0.05, my), (mx, y1 + g + th / 2 + 0.05), (mx, y0 - g - th / 2 - 0.05)]
        for lx, ly in cands:
            lb = (lx - tw / 2 - 0.1, ly - th / 2 - 0.1, lx + tw / 2 + 0.1, ly + th / 2 + 0.1)
            if lb[0] < 0.2 or lb[2] > W - 0.2 or lb[1] < 0.2 or lb[3] > H - 0.2: continue
            if any(ovl(lb, v) for k, v in boxes.items() if k != r) or any(ovl(lb, t_) for t_ in taken): continue
            break
        taken.append(lb)
        col = (150, 0, 0) if r in NEW else (0, 0, 0)
        d.text(P(lx, ly), r, font=fnt, fill=col, anchor="mm")
        continue
    big = min(x1 - x0, y1 - y0) > 3.0
    size = int((0.9 if big else 0.5) * SC)
    while True:
        fnt = ImageFont.truetype(FB, size); tw = d.textlength(r, font=fnt); th = size
        vertical = (not big) and bh > bw * 1.3 and tw > bw * 0.9
        fits = (th * 1.0 < bw and tw < bh) if vertical else (tw < bw * 0.95 and th < bh)
        if fits or size <= int(0.34 * SC): break
        size -= K
    col = (150, 0, 0) if r in NEW else (0, 0, 0)
    bg = (255, 214, 214) if r in NEW else (255, 255, 255)
    t = Image.new("RGBA", (int(tw) + 8 * K, size + 8 * K), bg + (235,))
    ImageDraw.Draw(t).text((t.width / 2, t.height / 2), r, font=fnt, fill=col, anchor="mm")
    if vertical: t = t.rotate(90, expand=True)
    img.paste(t, (int(cx - t.width / 2), int(cy - t.height / 2)), t)
# legend
fl = ImageFont.truetype(FB, 15 * K); fr = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14 * K)
y = M + H * SC + 18 * K
d.rectangle([M, y, M + 22 * K, y + 16 * K], fill=(255, 214, 214), outline=(150, 0, 0), width=K)
d.text((M + 30 * K, y - 1 * K), "Retardo de armado nuevo en rev D: R15, R16, R17, R18, C6, D4", font=fl, fill=(150, 0, 0))
d.text((M, y + 26 * K), "Vista desde la cara de componentes. Línea punteada: franja libre de 1 mm para los rieles de la caja.", font=fr, fill=(60, 60, 60))
img = img.resize((img.width // K, img.height // K), Image.LANCZOS)
img.save(out)
print("saved", out, img.size)
