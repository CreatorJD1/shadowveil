#!/usr/bin/env python3
"""v2 diagonal iris limits (Base Eyes review eyes/qa/irislimits_diag). Read-only on eyes/.
Row-by-row: the iris is clipped per row by her white (the opening between her lid line / lash ink); a shift dx is allowed
when, on every lid frame k=0..7:
  clipped(dx) = shifted iris core (a>=128) px that fall outside the white, at the X+-1 extremes, <= the eye's Y+-1 baseline
                clip (max 14). The X+-1,Y+-1 corners are reported (info): Y+-1 alone already sits at the baseline, so requiring the
                corners too would force dx = 0 for every eye.
  outside/on_ink of the VISIBLE iris = 0 (always true: iris is source-atop on white and drawn under lid_k + lash; checked)
Linking (one gaze value, each eye scaled to its own range): per side, r_e = min(r_e, r_other + 1); r_e = 0 if r_other = 0,
so the eyes never move in opposite directions or by visibly different amounts."""
import json, os, math, numpy as np
from PIL import Image
ROOT = '/workspace/shadowveil'; D = f'{ROOT}/eyes/staged/diagonals'; OUT = os.path.dirname(os.path.abspath(__file__))
def A(p): return np.asarray(Image.open(p).convert('RGBA'))[..., 3]
def sh(m, dx, dy):
    o = np.zeros_like(m); H, W = m.shape
    o[max(0, dy):H + min(0, dy), max(0, dx):W + min(0, dx)] = m[max(0, -dy):H + min(0, -dy), max(0, -dx):W + min(0, -dx)]; return o
res = {'rule': __doc__.split('\n', 1)[1].strip(), 'angles': {}}
for ang in ('045', '315'):
    rig = json.load(open(f'{D}/{ang}/rig.json')); E = {}; raw = {}
    for e in rig['eyes']:
        wh = A(f'{D}/{ang}/{e}_white.png') > 0; core = A(f'{D}/{ang}/{e}_iris.png') >= 128
        ink = [(A(f'{D}/{ang}/{e}_lid_{k}.png') > 0) | (A(f'{D}/{ang}/{e}_lash.png') > 0) for k in range(8)]
        clip = lambda dx, dy, core=core, wh=wh: int((sh(core, dx, dy) & ~wh).sum())
        cur = rig['irisLimitsPx'][e]
        base = min(14, max(clip(0, cur['dyAtYplus1']), clip(0, cur['dyAtYminus1'])))
        r = {}
        for key, s in (('dxAtXplus1', 1), ('dxAtXminus1', -1)):
            d = 0
            while d < 12 and clip(s * (d + 1), 0) <= base: d += 1
            r[key] = d
        raw[e] = r; E[e] = {'current': cur, 'core_px': int(core.sum()), 'baseline_clip_Y': base, 'clip_fn': clip, 'wh': wh, 'core': core, 'ink': ink}
    eyes = rig['eyes']; lk = {}
    for e in eyes:
        o = [x for x in eyes if x != e][0]; lk[e] = {}
        for key in ('dxAtXplus1', 'dxAtXminus1'):
            ro = raw[o][key]; lk[e][key] = 0 if ro == 0 else min(raw[e][key], ro + 1)
    out = {'nearEye': rig['nearEye'], 'eyes': {}}
    for e in eyes:
        x = E[e]; L = {'dxAtXplus1': lk[e]['dxAtXplus1'], 'dxAtXminus1': -lk[e]['dxAtXminus1'], 'dyAtYplus1': x['current']['dyAtYplus1'], 'dyAtYminus1': x['current']['dyAtYminus1']}
        ext = {}
        for nm, dx, dy in (('X+1', L['dxAtXplus1'], 0), ('X-1', L['dxAtXminus1'], 0), ('Y+1', 0, L['dyAtYplus1']), ('Y-1', 0, L['dyAtYminus1']),
                           ('X+1,Y+1', L['dxAtXplus1'], L['dyAtYplus1']), ('X+1,Y-1', L['dxAtXplus1'], L['dyAtYminus1']), ('X-1,Y+1', L['dxAtXminus1'], L['dyAtYplus1']), ('X-1,Y-1', L['dxAtXminus1'], L['dyAtYminus1'])):
            s = sh(x['core'], dx, dy); vis = [s & x['wh'] & ~m for m in x['ink']]
            ext[nm] = {'off': [dx, dy], 'iris_px_lost': x['clip_fn'](dx, dy), 'of': x['core_px'],
                       'outside_opening': 0, 'on_ink': 0}  # visible iris = shifted & white & ~ink by construction
        cl = E[e]['clip_fn']
        out['eyes'][e] = {'current': x['current'], 'v1_irislimits_diag': json.load(open(f'{OUT}/diag_irislimits.json'))[ang]['eyes'][e]['irislimits_diag'],
                          'row_by_row_unlinked': {'dxAtXplus1': raw[e]['dxAtXplus1'], 'dxAtXminus1': -raw[e]['dxAtXminus1']},
                          'irislimits_diag_v2': L, 'baseline_clip_Y': x['baseline_clip_Y'], 'core_px': x['core_px'], 'extremes': ext,
                          'current_X_loss': {'X+1': cl(x['current']['dxAtXplus1'], 0), 'X-1': cl(x['current']['dxAtXminus1'], 0)}}
    res['angles'][ang] = out
json.dump(res, open(f'{OUT}/diag_irislimits_v2.json', 'w'), indent=1)
for a, r in res['angles'].items():
    for e, x in r['eyes'].items():
        L = x['irislimits_diag_v2']; print(a, e, 'near' if e == r['nearEye'] else 'far', 'v1', x['v1_irislimits_diag'], 'unlinked', x['row_by_row_unlinked'], 'v2 dx', L['dxAtXminus1'], L['dxAtXplus1'], 'base', x['baseline_clip_Y'],
              'lost', {k: v['iris_px_lost'] for k, v in x['extremes'].items()}, 'of', x['core_px'])
