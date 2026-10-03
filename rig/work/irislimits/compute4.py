#!/usr/bin/env python3
"""v4 diagonal iris limits: v2 X/Y limits (Y=0 sideways extremes and dy unchanged) + per-corner sideways offsets.
Corners (X+-1, Y+-1): start from the v3 oval offset dx = round(0.7071*range) (dy stays whole: +-1); per eye reduce |dx|
one px at a time (down to 0) until iris lost (shifted core px outside the white; the same for every lid frame, so it is the
worst-frame value) <= that eye's Y+-1 baseline. Then link (v2 rule) per corner: same direction, |a| <= |b|+1, and 0 if the
other eye is 0; capping repeats until stable. Read-only on eyes/."""
import json, math, os, numpy as np
from PIL import Image
ROOT = '/workspace/shadowveil'; D = f'{ROOT}/eyes/staged/diagonals'; OUT = os.path.dirname(os.path.abspath(__file__))
V2 = json.load(open(f'{OUT}/diag_irislimits_v2.json'))['angles']
def A(p): return np.asarray(Image.open(p).convert('RGBA'))[..., 3]
def sh(m, dx, dy):
    o = np.zeros_like(m); H, W = m.shape
    o[max(0, dy):H + min(0, dy), max(0, dx):W + min(0, dx)] = m[max(0, -dy):H + min(0, -dy), max(0, -dx):W + min(0, -dx)]; return o
rnd = lambda z: int(math.floor(z + 0.5))
res = {'rule': __doc__.split('\n', 1)[1].strip(), 'angles': {}}
for ang in ('045', '315'):
    rig = json.load(open(f'{D}/{ang}/rig.json')); eyes = rig['eyes']; C = {}; info = {}
    for e in eyes:
        wh = A(f'{D}/{ang}/{e}_white.png') > 0; core = A(f'{D}/{ang}/{e}_iris.png') >= 128
        L = V2[ang]['eyes'][e]['irislimits_diag_v2']; base = V2[ang]['eyes'][e]['baseline_clip_Y']
        clip = lambda dx, dy, core=core, wh=wh: int((sh(core, dx, dy) & ~wh).sum())
        info[e] = {'L': L, 'base': base, 'clip': clip}; C[e] = {}
        for X in (-1, 1):
            for Y in (-1, 1):
                dx0 = rnd(0.70710678 * X * (L['dxAtXplus1'] if X > 0 else -L['dxAtXminus1']))
                dy = rnd(0.70710678 * Y * (L['dyAtYplus1'] if Y > 0 else -L['dyAtYminus1']))
                dx = dx0
                while dx != 0 and clip(dx, dy) > base: dx -= int(math.copysign(1, dx))
                C[e][f'{X:+d},{Y:+d}'] = {'v3_dx': dx0, 'dx': dx, 'dy': dy}
    for key in C[eyes[0]]:
        for _ in range(4):
            a, b = C[eyes[0]][key], C[eyes[1]][key]
            for p, q in ((a, b), (b, a)):
                if q['dx'] == 0 or (p['dx'] * q['dx'] < 0): p['dx'] = 0 if q['dx'] == 0 or p['dx'] * q['dx'] < 0 else p['dx']
                elif abs(p['dx']) > abs(q['dx']) + 1: p['dx'] = int(math.copysign(abs(q['dx']) + 1, p['dx']))
    out = {'eyes': {}}
    for e in eyes:
        x = info[e]; cc = {}
        for key, c in C[e].items():
            cc[key] = dict(c, lost=x['clip'](c['dx'], c['dy']), baseline=x['base'], lost_v3=x['clip'](c['v3_dx'], c['dy']))
        out['eyes'][e] = {'irislimits_diag_v2': x['L'], 'baseline_clip_Y': x['base'], 'corners': cc}
    res['angles'][ang] = out
json.dump(res, open(f'{OUT}/diag_irislimits_v4.json', 'w'), indent=1)
for a, r in res['angles'].items():
    for e, x in r['eyes'].items():
        for k, c in x['corners'].items(): print(a, e, k, 'v3 dx', c['v3_dx'], '-> v4 (dx,dy)', (c['dx'], c['dy']), 'lost', c['lost'], 'base', c['baseline'], 'v3 lost', c['lost_v3'])
