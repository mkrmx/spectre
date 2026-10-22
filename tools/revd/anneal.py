"""Simulated-annealing placement for SPECTRE rev D.
Fixed anchors keep the box interface (connectors, sensors, trimpot); everything else is optimised for
short connections, no courtyard overlap and a clear strip along all board edges."""
import json, math, os, random, sys
D = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(os.path.join(D, "geom.json")))
NET = json.load(open(os.path.join(D, "netmap_sch.json")))
args = dict(a.split("=") for a in sys.argv[1:])
SEED = int(args.get("seed", 1)); random.seed(SEED)
ITERS = int(args.get("iters", 300000)); T0 = float(args.get("t0", 4.0)); T1 = float(args.get("t1", 0.003))
SPACE = float(args.get("space", 0.12))          # extra half-gap around each courtyard (mm)
OUT = args.get("out", "layout_revd.json")
W, H, KEEP = 42.0, 32.0, 0.75                   # courtyard may not come closer than 0.75 mm to an edge

FIXED = {"J1": (5.0, 13.4, 90), "J2": (35.9, 13.4, 90), "U2": (2.9, 18.4, 0),
         "LDR1": (1.95, 22.7, 0), "R9": (18.6, 27.9, 0)}
base = json.load(open(os.path.join(D, "..", "layout.json")))["place"]
INIT_NEW = {"R15": (9.0, 17.5, 90), "D4": (9.0, 21.0, 90), "C6": (13.0, 26.0, 0), "R16": (20.0, 25.0, 0),
            "R17": (20.0, 27.0, 0), "R18": (17.0, 14.0, 0)}
pos = {}
INIT = args.get("init")
if INIT:
    base = json.load(open(os.path.join(D, INIT)))["place"]
for r in NET:
    if r in FIXED: pos[r] = list(FIXED[r])
    elif r in base: pos[r] = list(base[r]); pos[r][2] = int(pos[r][2]) % 360
    else: pos[r] = list(INIT_NEW[r])
movable = [r for r in NET if r not in FIXED]

W_NET = {"GND": 0.12, "+5V": 0.45, "+12V": 1.5, "/+12V_IN": 1.5, "/LED_NEG": 1.5}
nets = {}
for r, info in NET.items():
    for pin, n in info["pins"].items():
        nets.setdefault(n, []).append((r, pin))
PAIRS = [(("C5", "1"), ("U2", "1"), 4.0), (("C1", "1"), ("U1", "1"), 3.0), (("C2", "1"), ("U1", "3"), 3.0),
         (("C6", "1"), ("U3", "5"), 0.8)]
part_nets = {r: sorted({n for n, pins in nets.items() for (rr, _) in pins if rr == r}) for r in NET}
part_pairs = {r: [i for i, (a, b, w) in enumerate(PAIRS) if a[0] == r or b[0] == r] for r in NET}

def box(r, p=None):
    x, y, rot = p or pos[r]
    b = G[r][str(int(rot) % 360)]["box"]
    return (x + b[0] - SPACE, y + b[1] - SPACE, x + b[2] + SPACE, y + b[3] + SPACE)
def pad(r, pin, p=None):
    x, y, rot = p or pos[r]
    o = G[r][str(int(rot) % 360)]["pads"][pin]
    return (x + o[0], y + o[1])
def hpwl(n):
    pts = [pad(r, p) for r, p in nets[n]]
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    return (max(xs) - min(xs) + max(ys) - min(ys)) * W_NET.get(n, 1.0)
def pair_cost(i):
    (ra, pa), (rb, pb), w = PAIRS[i]
    a = pad(ra, pa); c = pad(rb, pb)
    return w * (abs(a[0] - c[0]) + abs(a[1] - c[1]))
def ov(a, b):
    w_ = min(a[2], b[2]) - max(a[0], b[0]); h_ = min(a[3], b[3]) - max(a[1], b[1])
    return w_ * h_ if w_ > 0 and h_ > 0 else 0.0
def edge_pen(bx):
    s = SPACE
    out = max(0, KEEP - (bx[0] + s)) + max(0, (bx[2] - s) - (W - KEEP)) + max(0, KEEP - (bx[1] + s)) + max(0, (bx[3] - s) - (H - KEEP))
    return out
LAM_OV, LAM_EDGE = float(args.get("lamov", 60.0)), 200.0
def part_cost(r):
    bx = box(r)
    c = LAM_EDGE * edge_pen(bx)
    for o in NET:
        if o != r: c += LAM_OV * ov(bx, box(o))
    return c
def total():
    c = sum(hpwl(n) for n in nets) + sum(pair_cost(i) for i in range(len(PAIRS)))
    c += sum(LAM_EDGE * edge_pen(box(r)) for r in NET)
    rs = list(NET)
    for i in range(len(rs)):
        for j in range(i + 1, len(rs)):
            c += LAM_OV * ov(box(rs[i]), box(rs[j]))
    return c

cur = total(); best = cur; best_pos = {r: list(v) for r, v in pos.items()}
for it in range(ITERS):
    T = T0 * (T1 / T0) ** (it / ITERS)
    sigma = max(0.15, 3.5 * (T / T0) ** 0.5)
    mv = random.random()
    if mv < 0.1:                                   # swap two movable parts of similar size
        a, b = random.sample(movable, 2)
        ba, bb = G[a]["0"]["box"], G[b]["0"]["box"]
        if abs((ba[2]-ba[0]) * (ba[3]-ba[1]) - (bb[2]-bb[0]) * (bb[3]-bb[1])) > 2.0: continue
        parts = [a, b]
        old = {a: list(pos[a]), b: list(pos[b])}
        aff_n = set(part_nets[a]) | set(part_nets[b]); aff_p = set(part_pairs[a]) | set(part_pairs[b])
        before = sum(hpwl(n) for n in aff_n) + sum(pair_cost(i) for i in aff_p) + part_cost(a) + part_cost(b) - LAM_OV * ov(box(a), box(b))
        pos[a][0], pos[a][1], pos[b][0], pos[b][1] = old[b][0], old[b][1], old[a][0], old[a][1]
    else:
        a = random.choice(movable); parts = [a]
        old = {a: list(pos[a])}
        aff_n = set(part_nets[a]); aff_p = set(part_pairs[a])
        before = sum(hpwl(n) for n in aff_n) + sum(pair_cost(i) for i in aff_p) + part_cost(a)
        if mv < 0.25:
            pos[a][2] = (pos[a][2] + random.choice((90, 180, 270))) % 360
        else:
            pos[a][0] += random.gauss(0, sigma); pos[a][1] += random.gauss(0, sigma)
    if len(parts) == 2:
        after = sum(hpwl(n) for n in aff_n) + sum(pair_cost(i) for i in aff_p) + part_cost(parts[0]) + part_cost(parts[1]) - LAM_OV * ov(box(parts[0]), box(parts[1]))
    else:
        after = sum(hpwl(n) for n in aff_n) + sum(pair_cost(i) for i in aff_p) + part_cost(a)
    d = after - before
    if d <= 0 or random.random() < math.exp(-d / max(T, 1e-9)):
        cur += d
        if cur < best - 1e-9:
            best = cur; best_pos = {r: list(v) for r, v in pos.items()}
    else:
        for r, v in old.items(): pos[r] = v
pos = best_pos
# snap to 0.05 mm
for r in movable:
    pos[r][0] = round(pos[r][0] / 0.05) * 0.05; pos[r][1] = round(pos[r][1] / 0.05) * 0.05
final = total()
ovl = sum(ov(box(a), box(b)) for i, a in enumerate(NET) for b in list(NET)[i + 1:])
edg = sum(edge_pen(box(r)) for r in NET)
wl = sum(hpwl(n) for n in nets)
SPACE_SAVE = SPACE; SPACE = 0.0
real = sum(ov(box(a), box(b)) for i, a in enumerate(NET) for b in list(NET)[i + 1:])
SPACE = SPACE_SAVE
print(f"real courtyard overlap {real:.4f}")
print(f"seed {SEED}: cost {final:.1f}  wirelength {wl:.1f}  overlap {ovl:.3f}  edge {edg:.3f}")
json.dump({"W": W, "H": H, "edge_cu": 1.0, "place": {r: [round(v[0], 3), round(v[1], 3), int(v[2])] for r, v in pos.items()}},
          open(os.path.join(D, OUT), "w"), indent=1)
