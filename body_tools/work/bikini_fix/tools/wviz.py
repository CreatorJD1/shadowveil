# wviz.py VIEW SKIN OUT.png : thigh_L+thigh_R weight heat over the art in the hip region (per triangle, interpolated)
import json, sys, numpy as np
from PIL import Image, ImageDraw
v, sk, out = sys.argv[1:4]
s = json.load(open(sk)); names = [b['name'] for b in s['bones']]; th = {names.index('thigh_L'), names.index('thigh_R')}
V = np.array(s['vertices'], float); wt = np.array([sum(x for k, x in w if k in th) for w in s['weights']])
base = Image.open(f'/workspace/shadowveil/views/{v}/{s["image"]}').convert('RGBA')
mid = s['bones'][names.index('pelvis')]['pivot']; x0, y0 = int(mid[0] - 190), int(mid[1] - 80)
box = (x0, y0, x0 + 380, y0 + 230)
heat = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(heat)
for t in s['triangles']:
    P = V[t[:3]]
    if not ((P[:, 0] > box[0]).any() and (P[:, 0] < box[2]).any() and (P[:, 1] > box[1]).any() and (P[:, 1] < box[3]).any()): continue
    w = wt[t[:3]].mean()
    c = (int(255 * w), int(255 * (1 - abs(2 * w - 1))), int(255 * (1 - w)), 150)
    d.polygon([tuple(p) for p in P], fill=c)
bg = Image.new('RGBA', base.size, (255, 255, 255, 255)); bg.alpha_composite(base); bg.alpha_composite(heat)
bg.crop(box).resize((760, 460), Image.NEAREST).save(out)
