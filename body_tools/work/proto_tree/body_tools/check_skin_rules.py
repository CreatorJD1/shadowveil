#!/usr/bin/env python3
"""Check Base Body skin rules on a skin.json: (1) every triangle that covers a head-part pixel is 100% head at all 3 vertices
(head, chin, jaw and neck down to the head/torso cut never ride another bone); (2) the forearm end (wrist rigid zone,
last wristRigidPx + 3 px palm overlap before wristPivot) is 100% forearm; (3) wrist pivots equal rig.json.
Usage: python3 body_tools/check_skin_rules.py <view> [skin file in views/<view>/body/, default skin.json]"""
import sys, json, numpy as np
from PIL import Image
view = sys.argv[1]; sf = sys.argv[2] if len(sys.argv) > 2 else 'skin.json'
vd = f'views/{view}'; j = json.load(open(f'{vd}/body/{sf}')); rig = json.load(open(f'{vd}/body/rig.json'))
names = [b['name'] for b in j['bones']]; bi = {n: i for i, n in enumerate(names)}
V = np.array(j['vertices'], float); T = np.array([t[:3] for t in j['triangles']]); Wt = j['weights']
H, W = j['size'][1], j['size'][0]
def w_of(v, b): return sum(w for k, w in Wt[v] if k == b)
head = np.array(Image.open(f'{vd}/body/head.png'))[..., 3] > 0
# rasterise pixel centres per triangle (bbox + barycentric, edges inclusive)
def pix(t):
    a, b, c = V[t]; x0, x1 = int(np.floor(min(a[0], b[0], c[0]))), int(np.ceil(max(a[0], b[0], c[0]))); y0, y1 = int(np.floor(min(a[1], b[1], c[1]))), int(np.ceil(max(a[1], b[1], c[1])))
    xs, ys = np.meshgrid(np.arange(x0, x1) + .5, np.arange(y0, y1) + .5); P = np.stack([xs.ravel(), ys.ravel()], 1)
    d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(d) < 1e-9: return np.zeros((0, 2), int)
    l1 = ((b[1] - c[1]) * (P[:, 0] - c[0]) + (c[0] - b[0]) * (P[:, 1] - c[1])) / d; l2 = ((c[1] - a[1]) * (P[:, 0] - c[0]) + (a[0] - c[0]) * (P[:, 1] - c[1])) / d; l3 = 1 - l1 - l2
    m = (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9); return np.floor(P[m]).astype(int)
hb = bi['head']; bad_head = 0; head_tris = 0
ys_, xs_ = np.nonzero(head); hx0, hx1, hy0, hy1 = xs_.min(), xs_.max(), ys_.min(), ys_.max()
for t in T:
    c = V[t].mean(0)
    if not (hx0 - 8 <= c[0] <= hx1 + 8 and hy0 - 8 <= c[1] <= hy1 + 8): continue
    p = pix(t); p = p[(p[:, 0] >= 0) & (p[:, 0] < W) & (p[:, 1] >= 0) & (p[:, 1] < H)]
    if len(p) and head[p[:, 1], p[:, 0]].any():
        head_tris += 1
        if min(w_of(v, hb) for v in t) < 0.99999: bad_head += 1
# forearm end
by = {p['id']: p for p in rig['parts']}; fa = {}
for s in 'LR':
    n = f'forearm_{s}'
    if n not in bi or not by.get(n, {}).get('file'): continue
    b = j['bones'][bi[n]]; wp = b.get('wristPivot'); rp = by[n].get('wristPivot')
    J = np.array(b['pivot']); Wp = np.array([wp['x'], wp['y']]); dd = (Wp - J) / np.linalg.norm(Wp - J); L = np.linalg.norm(Wp - J)
    own = np.array(Image.open(f'{vd}/body/' + by[n]['file']))[..., 3] > 0
    lay = by[n]['layer']; fv = {int(v) for t in j['triangles'] if len(t) > 3 and t[3] == lay for v in t[:3]} if all(len(t) > 3 for t in j['triangles']) else set(range(len(V)))
    # forearm-mesh vertices (triangles in the forearm's layer group) whose position is on a forearm pixel in the last 11 px before wristPivot
    s_ = (V - J) @ dd; near = [v for v in fv if s_[v] >= L - 11 and s_[v] <= L + 4 and own[min(H - 1, int(V[v][1])) , min(W - 1, int(V[v][0]))]]
    fa[n] = {'wristPivot': wp, 'rigWristPivot': rp, 'same': wp == rp, 'vertsInLast11px': len(near), 'not100pct': sum(1 for v in near if w_of(v, bi[n]) < 0.99999)}
print(json.dumps({'view': view, 'skin': sf, 'headTriangles': head_tris, 'headTrianglesNot100pctHead': bad_head, 'headPartBottomY': int(hy1), 'forearmEnd': fa}))
