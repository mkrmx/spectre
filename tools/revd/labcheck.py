import json, sys
G = json.load(open("geom.json")); G2 = json.load(open("geom2.json"))
L = json.load(open(sys.argv[1]))
pos = L["place"]
def cy(r, s=0.0):
    x, y, rot = pos[r][:3]; b = G[r][str(rot)]["box"]; return (x + b[0] - s, y + b[1] - s, x + b[2] + s, y + b[3] + s)
def lab(r):
    x, y, rot, sl = pos[r]; s = G2[r][str(rot)][sl]
    return (x + s[0] - s[3] / 2, y + s[1] - s[4] / 2, x + s[0] + s[3] / 2, y + s[1] + s[4] / 2)
def ov(a, b):
    w_ = min(a[2], b[2]) - max(a[0], b[0]); h_ = min(a[3], b[3]) - max(a[1], b[1])
    return w_ * h_ if w_ > 0 and h_ > 0 else 0.0
rs = list(pos)
for a in rs:
    for b in rs:
        if a == b: continue
        o = ov(lab(a), cy(b))
        if o > 1e-6: print("label", a, "over courtyard", b, round(o, 4))
        if a < b:
            o2 = ov(lab(a), lab(b))
            if o2 > 1e-6: print("label", a, "over label", b, round(o2, 4))
            o3 = ov(cy(a, 0.3), cy(b, 0.3))
            if o3 > 1e-6: print("spaced", a, b, round(o3, 3))
