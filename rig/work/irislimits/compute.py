#!/usr/bin/env python3
"""Iris gaze limits for the staged diagonal eye rigs (eyes/staged/diagonals/<ang>/), read-only.
Draw order is white, iris source-atop on white, lid_k, lash, so the iris is always clipped to her eye-white mask and drawn
under her lid line and lash. A shift d (frame px) is allowed when, on every lid frame k = 0..7:
  (1) the iris bbox leading edge stays within the eye corner (the extreme column/row of the eye lock E = white U rest iris), and
  (2) the visible iris (shifted core alpha>=128, inside E, not under lid_k or lash ink) keeps >= KEEP of what the
      centred iris shows on that frame. Frames where the centred iris is already < 4 px visible are skipped (closed).
The limit is the largest |d| reached stepping out 1 px at a time; the failing frame and rule are recorded."""
import json, sys, os, numpy as np
from PIL import Image
KEEP = float(os.environ.get('KEEP', 0.75))
ROOT = '/workspace/shadowveil'; D = f'{ROOT}/eyes/staged/diagonals'; OUT = os.path.dirname(os.path.abspath(__file__))
def A(p): return np.asarray(Image.open(p).convert('RGBA'))[..., 3]
def sh(m, dx, dy):
    o = np.zeros_like(m); H, W = m.shape
    o[max(0, dy):H + min(0, dy), max(0, dx):W + min(0, dx)] = m[max(0, -dy):H + min(0, -dy), max(0, -dx):W + min(0, -dx)]; return o
res = {'rule': __doc__.split('\n', 1)[1].strip(), 'KEEP': KEEP}
for ang in sorted(os.listdir(D)):
    if not os.path.exists(f'{D}/{ang}/rig.json'): continue
    rig = json.load(open(f'{D}/{ang}/rig.json')); sc = rig['viewFit']['scale']
    res[ang] = {'rig': f'eyes/staged/diagonals/{ang}/rig.json', 'frame': rig['frameSource'], 'viewFitScale': sc, 'eyes': {}}
    for e in rig['eyes']:
        wh = A(f'{D}/{ang}/{e}_white.png') > 0; ir = A(f'{D}/{ang}/{e}_iris.png'); core = ir >= 128; E = wh | (ir > 0)
        lash = A(f'{D}/{ang}/{e}_lash.png') > 0
        ink = [(A(f'{D}/{ang}/{e}_lid_{k}.png') > 0) | lash for k in range(8)]
        ys, xs = np.nonzero(E); cys, cxs = np.nonzero(core)
        vis = lambda c, k: int((c & E & ~ink[k]).sum())
        base = [vis(core, k) for k in range(8)]
        def ok(dx, dy):
            if cxs.max() + dx > xs.max() or cxs.min() + dx < xs.min() or cys.max() + dy > ys.max() or cys.min() + dy < ys.min():
                return False, 'iris edge passes the eye corner'
            c = sh(core, dx, dy)
            for k in range(8):
                if base[k] >= 4 and vis(c, k) < KEEP * base[k]: return False, f'lid_{k}: visible iris {vis(c, k)} < {KEEP:.0%} of {base[k]} (would slide under lid line/lash)'
            return True, ''
        lim = {}; why = {}
        for key, vx, vy in (('dxAtXplus1', 1, 0), ('dxAtXminus1', -1, 0), ('dyAtYplus1', 0, 1), ('dyAtYminus1', 0, -1)):
            d = 0
            while d < 12:
                good, r = ok((d + 1) * vx, (d + 1) * vy)
                if not good: why[key] = f'stops at {d + 1}: {r}'; break
                d += 1
            lim[key] = d * (vx + vy)
        cur = rig['irisLimitsPx'][e]
        res[ang]['eyes'][e] = {'current': cur, 'irislimits_diag': lim, 'limited_by': why, 'visible_iris_px_per_lid_frame_centred': base,
                               'view_px': {k: round(v * sc, 2) for k, v in lim.items()}}
for ang in ('135', '225'):
    res[ang] = {'note': 'no staged diagonal eye rig (back diagonals: eyes not cut); nothing to widen'}
json.dump(res, open(f'{OUT}/diag_irislimits.json', 'w'), indent=1)
for a, r in res.items():
    if isinstance(r, dict) and 'eyes' in r:
        for e, x in r['eyes'].items(): print(a, e, 'current', x['current'], '-> diag', x['irislimits_diag'], x['limited_by'])
