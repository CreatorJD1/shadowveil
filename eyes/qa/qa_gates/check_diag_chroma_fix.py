#!/usr/bin/env python3
"""Post-fix checks for the diagonal far-eye chroma fix (read-only).
 rest_on_frame: composite (white, iris, lid_0, lash per eye; gaze 0) on the turn frame vs the frame.
   face px = frame px that are NOT key-blue by the qa_gates chroma rule. Reports diff px in face / outside face.
 grey: composite of the eye parts alone over neutral grey (128,128,128), 9 gaze x 8 lid frames x {current, diag} limits:
   chroma px (qa_gates rule) anywhere; before (backups) vs after.
 continuity: 8-connected components of (lid_k U lash) per eye per k, before vs after."""
import json, math, os, sys, numpy as np
from PIL import Image
from scipy.ndimage import label
R = '/workspace/shadowveil'; D = f'{R}/eyes/staged/diagonals'; BK = f'{D}/backups_chroma_fix'; OUT = os.path.dirname(os.path.abspath(__file__))
LIM = json.load(open(f'{R}/rig/work/irislimits/diag_irislimits.json')); FIXED = {('045', 'EyeR'), ('315', 'EyeL')}
def isch(c): c = c.astype(int); return (c[..., 2] > np.maximum(c[..., 0], c[..., 1]) + 60) & (c[..., 2] > 120)
def ld(ang, e, n, src):
    p = f'{BK}/{ang}/{e}_{n}.png' if (src == 'before' and (ang, e) in FIXED and n in ('lash', 'lid_0')) else f'{D}/{ang}/{e}_{n}.png'
    x = np.asarray(Image.open(p).convert('RGBA')).astype(float) / 255; x[..., :3] *= x[..., 3:]; return x
over = lambda d, s: s + d * (1 - s[..., 3:])
def atop(d, s): o = s * d[..., 3:] + d * (1 - s[..., 3:]); o[..., 3] = d[..., 3]; return o
def shift(a, dx, dy):
    o = np.zeros_like(a); H, W = a.shape[:2]; o[max(0, dy):H + min(0, dy), max(0, dx):W + min(0, dx)] = a[max(0, -dy):H + min(0, -dy), max(0, -dx):W + min(0, -dx)]; return o
rnd = lambda z: int(math.floor(z + .5))
res = {'doc': __doc__}
for ang in ('045', '315'):
    rig = json.load(open(f'{D}/{ang}/rig.json')); fr8 = np.asarray(Image.open(f'{R}/{rig["frameSource"]}').convert('RGBA'))
    a0, b0, a1, b1 = rig['workRegion']; CR = (slice(b0 - 10, b1 + 10), slice(a0 - 10, a1 + 10)); oy, ox = b0 - 10, a0 - 10
    out = {}
    for src in ('before', 'after'):
        P = {e: {n: ld(ang, e, n, src)[CR] for n in ['white', 'iris', 'lash'] + [f'lid_{k}' for k in range(8)]} for e in rig['eyes']}
        def comp(bg, lim, X, Y, k):
            cv = bg.copy(); touched = np.zeros(cv.shape[:2], bool)
            for e in rig['eyes']:
                l = dict(rig['irisLimitsPx'][e])
                if lim == 'diag': l.update({q: v for q, v in LIM[ang]['eyes'][e]['irislimits_diag'].items() if q.startswith('dx')})
                dx = rnd(X * (l['dxAtXplus1'] if X > 0 else -l['dxAtXminus1'])); dy = rnd(Y * (l['dyAtYplus1'] if Y > 0 else -l['dyAtYminus1']))
                lay = atop(P[e]['white'].copy(), shift(P[e]['iris'], dx, dy))
                for s in (lay, P[e][f'lid_{k}'], P[e]['lash']): cv = over(cv, s); touched |= s[..., 3] > 0
            return np.round(cv[..., :3] / np.clip(cv[..., 3:], 1e-9, 1) * 255).astype(np.uint8), touched
        F = fr8[CR].astype(float) / 255; F[..., :3] *= F[..., 3:]
        im, t = comp(F, 'current', 0, 0, 0); f3 = fr8[CR][..., :3]; diff = (im != f3).any(-1); face = ~isch(f3)
        ys, xs = np.nonzero(diff)
        r = {'rest_on_frame_diff_px': int(diff.sum()), 'rest_diff_in_face_px': int((diff & face).sum()), 'rest_diff_outside_face_px': int((diff & ~face).sum()),
             'rest_diff_xy_frame': [[int(x + ox), int(y + oy), f3[y, x].tolist(), im[y, x].tolist()] for y, x in zip(ys, xs)]}
        G = np.zeros_like(F); G[..., :3] = 128 / 255; G[..., 3] = 1
        gch = 0; gworst = []
        for lim in ('current', 'diag'):
            for X in (-1, 0, 1):
                for Y in (-1, 0, 1):
                    for k in range(8):
                        im, t = comp(G, lim, X, Y, k); c = int((isch(im) & t).sum()); gch += c
                        if c: gworst.append([lim, X, Y, k, c])
        r['grey_chroma_px_total_144_renders'] = gch; r['grey_cases_with_chroma'] = len(gworst); r['grey_worst'] = sorted(gworst, key=lambda z: -z[-1])[:3]
        r['components_lid_k_union_lash'] = {e: [int(label((P[e][f'lid_{k}'][..., 3] > 0) | (P[e]['lash'][..., 3] > 0), np.ones((3, 3)))[1]) for k in range(8)] for e in rig['eyes']}
        out[src] = r
    res[ang] = out
    for src in ('before', 'after'):
        r = out[src]; print(ang, src, {k: v for k, v in r.items() if k != 'rest_diff_xy_frame'})
json.dump(res, open(f'{OUT}/check_diag_chroma_fix.json', 'w'), indent=1)
