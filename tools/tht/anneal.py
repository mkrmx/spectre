"""Label-aware simulated-annealing placement for SPECTRE rev D.
Every part carries its reference label in one of its precomputed slots (geom2.json); labels may not overlap
other courtyards, other labels or the 1 mm rail strip, so the silkscreen stays readable."""
import json, math, os, random, sys
D = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(os.path.join(D, "geom.json")))
G2 = json.load(open(os.path.join(D, "geom2.json")))
NET = json.load(open(os.path.join(D, "netmap_tht.json")))
args = dict(a.split("=") for a in sys.argv[1:])
SEED = int(args.get("seed", 1)); random.seed(SEED)
ITERS = int(args.get("iters", 200000)); T0 = float(args.get("t0", 1.0)); T1 = float(args.get("t1", 0.002))
SPACE = float(args.get("space", 0.3)); OUT = args.get("out", "lab_out.json")
W, H = float(args.get("W", 48)), float(args.get("H", 40)); KEEP, LMARG, LG = 0.75, 1.0, 0.12
LAM_OV, LAM_LAB, LAM_EDGE = float(args.get("lamov", 60.0)), float(args.get("lamlab", 60.0)), 200.0
W_PREF = float(args.get("wpref", 1.0))
FIXED = {}
EDGEPARTS = {r: float(args.get("wedge", 40)) for r in ("J1", "J2", "J3", "J4")}
if "init" in args: init = json.load(open(os.path.join(D, args["init"])))
else:
    random.seed(SEED); init = {"place": {}}
    for r in NET: init["place"][r] = [random.uniform(6, W - 6), random.uniform(6, H - 6), random.choice((0, 90, 180, 270)), 0]
    random.seed(SEED)
pos = {}
for r in NET:
    p = list(FIXED[r]) if r in FIXED else list(init["place"][r][:3])
    p[2] = int(p[2]) % 360
    p.append(int(init["place"][r][3]) if len(init["place"][r]) > 3 else 0)
    pos[r] = p
movable = [r for r in NET if r not in FIXED]
W_NET = {"GND": 0.12, "+5V": 0.45, "+12V": 1.5, "/+12V_IN": 1.5, "/LED_NEG": 1.5}
nets = {}
for r, info in NET.items():
    for pin, n in info["pins"].items(): nets.setdefault(n, []).append((r, pin))
PAIRS = [(("C5", "1"), ("J3", "1"), 2.0), (("C1", "1"), ("U1", "1"), 3.0), (("C2", "1"), ("U1", "3"), 3.0), (("C6", "1"), ("U3", "5"), 0.8)]
part_nets = {r: sorted({n for n, pins in nets.items() for (rr, _) in pins if rr == r}) for r in NET}
part_pairs = {r: [i for i, (a, b, w) in enumerate(PAIRS) if a[0] == r or b[0] == r] for r in NET}

def cy(r, s=0.0):
    x, y, rot = pos[r][:3]; b = G[r][str(rot)]["box"]
    return (x + b[0] - s, y + b[1] - s, x + b[2] + s, y + b[3] + s)
def box(r): return cy(r, SPACE)
def lab(r):
    x, y, rot, sl = pos[r]; s = G2[r][str(rot)][sl]
    return (x + s[0] - s[3] / 2, y + s[1] - s[4] / 2, x + s[0] + s[3] / 2, y + s[1] + s[4] / 2)
def pref(r):
    x, y, rot, sl = pos[r]; return G2[r][str(rot)][sl][5]
def pad(r, pin):
    x, y, rot = pos[r][:3]; o = G[r][str(rot)]["pads"][pin]; return (x + o[0], y + o[1])
def hpwl(n):
    pts = [pad(r, p) for r, p in nets[n]]
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    return (max(xs) - min(xs) + max(ys) - min(ys)) * W_NET.get(n, 1.0)
def pair_cost(i):
    (ra, pa), (rb, pb), w = PAIRS[i]; a = pad(ra, pa); c = pad(rb, pb)
    return w * (abs(a[0] - c[0]) + abs(a[1] - c[1]))
def ov(a, b):
    w_ = min(a[2], b[2]) - max(a[0], b[0]); h_ = min(a[3], b[3]) - max(a[1], b[1])
    return w_ * h_ if w_ > 0 and h_ > 0 else 0.0
def grow(a, g): return (a[0] - g, a[1] - g, a[2] + g, a[3] + g)
def edge_pen(bx, m):
    return max(0, m - bx[0]) + max(0, bx[2] - (W - m)) + max(0, m - bx[1]) + max(0, bx[3] - (H - m))
def inter(a, b):
    c = LAM_OV * ov(box(a), box(b))
    la, lb = lab(a), lab(b)
    return c + LAM_LAB * (ov(la, cy(b)) + ov(lb, cy(a)) + ov(grow(la, LG), lb))
def selfc(r):
    c = LAM_EDGE * (edge_pen(cy(r), KEEP) + edge_pen(lab(r), LMARG)) + W_PREF * pref(r)
    if r in EDGEPARTS:
        b = cy(r); c += EDGEPARTS[r] * min(b[0], b[1], W - b[2], H - b[3])
    return c
def part_cost(r): return selfc(r) + sum(inter(r, o) for o in NET if o != r)
def total():
    c = sum(hpwl(n) for n in nets) + sum(pair_cost(i) for i in range(len(PAIRS))) + sum(selfc(r) for r in NET)
    rs = list(NET)
    for i in range(len(rs)):
        for j in range(i + 1, len(rs)): c += inter(rs[i], rs[j])
    return c
# greedy initial slot choice
for _ in range(2):
    for r in NET:
        best = None
        for k in range(len(G2[r][str(pos[r][2])])):
            pos[r][3] = k; c = part_cost(r)
            if best is None or c < best[0]: best = (c, k)
        pos[r][3] = best[1]
cur = total(); best = cur; best_pos = {r: list(v) for r, v in pos.items()}
allr = list(NET)
for it in range(ITERS):
    T = T0 * (T1 / T0) ** (it / ITERS)
    sigma = max(0.12, float(args.get('smax', 6.0)) * (T / T0) ** 0.5)
    mv = random.random()
    if mv < 0.08:
        a, b = random.sample(movable, 2)
        ba, bb = G[a]["0"]["box"], G[b]["0"]["box"]
        if abs((ba[2] - ba[0]) * (ba[3] - ba[1]) - (bb[2] - bb[0]) * (bb[3] - bb[1])) > 2.0: continue
        parts = [a, b]; old = {a: list(pos[a]), b: list(pos[b])}
        aff_n = set(part_nets[a]) | set(part_nets[b]); aff_p = set(part_pairs[a]) | set(part_pairs[b])
        before = sum(hpwl(n) for n in aff_n) + sum(pair_cost(i) for i in aff_p) + part_cost(a) + part_cost(b) - inter(a, b)
        pos[a][0], pos[a][1], pos[b][0], pos[b][1] = old[b][0], old[b][1], old[a][0], old[a][1]
        after = sum(hpwl(n) for n in aff_n) + sum(pair_cost(i) for i in aff_p) + part_cost(a) + part_cost(b) - inter(a, b)
    else:
        if mv < 0.30: a = random.choice(allr)          # label slot move: fixed parts too
        else: a = random.choice(movable)
        parts = [a]; old = {a: list(pos[a])}
        aff_n = set(part_nets[a]); aff_p = set(part_pairs[a])
        before = sum(hpwl(n) for n in aff_n) + sum(pair_cost(i) for i in aff_p) + part_cost(a)
        if mv < 0.30:
            pos[a][3] = random.randrange(len(G2[a][str(pos[a][2])]))
        elif mv < 0.42:
            pos[a][2] = (pos[a][2] + random.choice((90, 180, 270))) % 360
            pos[a][3] = random.randrange(len(G2[a][str(pos[a][2])]))
        else:
            pos[a][0] += random.gauss(0, sigma); pos[a][1] += random.gauss(0, sigma)
        after = sum(hpwl(n) for n in aff_n) + sum(pair_cost(i) for i in aff_p) + part_cost(a)
    d = after - before
    if d <= 0 or random.random() < math.exp(-d / max(T, 1e-9)):
        cur += d
        if cur < best - 1e-9: best = cur; best_pos = {r: list(v) for r, v in pos.items()}
    else:
        for r, v in old.items(): pos[r] = v
pos = best_pos
for r in movable:
    pos[r][0] = round(pos[r][0] / 0.05) * 0.05; pos[r][1] = round(pos[r][1] / 0.05) * 0.05
wl = sum(hpwl(n) for n in nets)
rs = list(NET)
cyo = sum(ov(cy(a), cy(b)) for i, a in enumerate(rs) for b in rs[i + 1:])
spo = sum(ov(box(a), box(b)) for i, a in enumerate(rs) for b in rs[i + 1:])
lbo = sum(ov(lab(a), cy(b)) for a in rs for b in rs if a != b) + sum(ov(lab(a), lab(b)) for i, a in enumerate(rs) for b in rs[i + 1:])
lbg = sum(ov(grow(lab(a), LG), lab(b)) for i, a in enumerate(rs) for b in rs[i + 1:])
edg = sum(edge_pen(cy(r), KEEP) + edge_pen(lab(r), LMARG) for r in rs)
nin = sum(1 for r in rs if pref(r) >= 1.0)
print(f"seed {SEED}: cost {total():.1f} wl {wl:.1f} | courtyard ov {cyo:.3f} spaced ov {spo:.3f} label ov {lbo:.3f} (gap {lbg:.3f}) edge {edg:.3f} inside-labels {nin}")
labels = {}
for r in rs:
    x, y, rot, sl = pos[r]; s = G2[r][str(rot)][sl]
    labels[r] = [round(x + s[0], 3), round(y + s[1], 3), s[2]]
json.dump({"W": W, "H": H, "edge_cu": 1.0, "place": {r: [round(v[0], 3), round(v[1], 3), int(v[2]), int(v[3])] for r, v in pos.items()},
           "labels": labels}, open(os.path.join(D, OUT), "w"), indent=1)
