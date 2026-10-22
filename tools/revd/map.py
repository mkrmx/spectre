import json, sys, os
from PIL import Image, ImageDraw, ImageFont
D = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(os.path.join(D, "geom.json")))
L = json.load(open(os.path.join(D, sys.argv[1])))
out = sys.argv[2]
K = 22; W, H = L["W"], L["H"]
im = Image.new("RGB", (int(W*K)+40, int(H*K)+40), "white"); d = ImageDraw.Draw(im)
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 11)
o = 20
d.rectangle([o, o, o+W*K, o+H*K], outline=(0, 0, 0), width=2)
d.rectangle([o+0.75*K, o+0.75*K, o+(W-0.75)*K, o+(H-0.75)*K], outline=(200, 120, 0))
FIX = {"J1", "J2", "U2", "LDR1", "R9"}
NEW = {"R15", "R16", "R17", "R18", "C6", "D4"}
G2 = json.load(open(os.path.join(D, "geom2.json")))
for r, pl in L["place"].items():
    x, y, rot = pl[:3]
    b = G[r][str(rot % 360)]["box"]
    col = (60, 120, 220) if r in FIX else ((220, 60, 60) if r in NEW else (90, 90, 90))
    d.rectangle([o+(x+b[0])*K, o+(y+b[1])*K, o+(x+b[2])*K, o+(y+b[3])*K], outline=col, width=2)
    for pin, (px, py) in G[r][str(rot % 360)]["pads"].items():
        d.ellipse([o+(x+px)*K-3, o+(y+py)*K-3, o+(x+px)*K+3, o+(y+py)*K+3], fill=col)
    if len(pl) > 3:
        s_ = G2[r][str(rot % 360)][pl[3]]; lx, ly, w, h = x + s_[0], y + s_[1], s_[3], s_[4]
        d.rectangle([o+(lx-w/2)*K, o+(ly-h/2)*K, o+(lx+w/2)*K, o+(ly+h/2)*K], fill=(255, 235, 150), outline=(180, 140, 0))
        if s_[2] == 0: d.text((o+lx*K, o+ly*K), r, fill=(0, 0, 0), font=f, anchor="mm")
        else:
            t = Image.new("RGBA", (60, 16), (0, 0, 0, 0)); ImageDraw.Draw(t).text((30, 8), r, fill=(0, 0, 0), font=f, anchor="mm")
            t = t.rotate(90, expand=True); im.paste(t, (int(o+lx*K-8), int(o+ly*K-30)), t)
    else:
        d.text((o+x*K-8, o+y*K-6), r, fill=col, font=f)
im.save(out)
