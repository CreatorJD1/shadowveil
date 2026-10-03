#!/usr/bin/env python3
"""Base Eyes supplement to rig/qa_gates.py (read-only; imports its functions, writes only here).
1) G2 leak on the staged diagonal eye parts eyes/staged/diagonals/{045,315}/*.png (not in qa_gates' diag_sets),
   palette = qa_gates.palette_sources(<ang>, 'eyes', f) (5 base.png + live eye files of all 5 views + turn frame), tol 2.
2) Same G2 on the composited diagonal eye renders: 9 gaze (X,Y in -1,0,1) x 8 lid frames x {current, diag} limits,
   counted inside the eye workRegion (rigid drawImage, integer offsets).
3) Locates every off-palette / chroma px of qa_gates' diagonal set (hair/mouth/hands, view space) and tests whether it
   lands on an eye part (view->frame via the eye rig viewFit; union of white, iris shifted <=4px, all lids, lash; +1px)."""
import sys, os, json, glob, math, numpy as np
sys.dont_write_bytecode = True
R = '/workspace/shadowveil'; sys.path.insert(0, f'{R}/rig'); sys.argv = sys.argv[:1]
import qa_gates as Q
from scipy.spatial import cKDTree
from scipy.ndimage import binary_dilation
OUT = os.path.dirname(os.path.abspath(__file__)); TOL = 2.0; D = f'{R}/eyes/staged/diagonals'
def offmask(img, pal, tol=TOL):
    op = img[..., 3] == 255; c = img[..., :3].astype(np.int32); codes = (c[..., 0] << 16) | (c[..., 1] << 8) | c[..., 2]
    miss = op & ~np.isin(codes, pal)
    if miss.any():
        d, _ = cKDTree(Q.unpack(pal)).query(img[..., :3][miss].astype(float), k=1); m2 = np.zeros_like(miss); m2[miss] = d > tol; miss = m2
    return miss
def chmask(img):
    r, g, b, a = [img[..., i].astype(int) for i in range(4)]; return (a >= 1) & (b > np.maximum(r, g) + 60) & (b > 120)
res = {'doc': __doc__, 'tol': TOL, 'files': {}, 'composites': {}, 'baseline_diag_px_on_eyes': {}}
sys.path.insert(0, f'{R}/eyes/qa/irislimits_diag')
LIM = json.load(open(f'{R}/rig/work/irislimits/diag_irislimits.json'))
for ang in ('045', '315'):
    rig = json.load(open(f'{D}/{ang}/rig.json')); fs = sorted(f for f in glob.glob(f'{D}/{ang}/*.png') if not f.endswith('_chroma.png'))
    pal = Q.palette(Q.palette_sources(ang, 'eyes', 'x.png'))
    rows = []
    for f in fs:
        im = Q.rgba(f); m = offmask(im, pal); ch = chmask(im); ys, xs = np.nonzero(m | ch)
        rows.append({'file': os.path.relpath(f, R), 'opaque': int((im[..., 3] == 255).sum()), 'off_palette': int(m.sum()), 'chroma': int(ch.sum()),
                     'soft_edge': Q.soft_count(im), 'px': [[int(x), int(y), im[y, x, :3].tolist()] for y, x in zip(ys, xs)][:50]})
    res['files'][ang] = rows
    # composites
    ld = lambda p: Q.rgba(p).astype(float) / 255
    def pm(x): y = x.copy(); y[..., :3] *= y[..., 3:]; return y
    over = lambda d, s: s + d * (1 - s[..., 3:])
    def atop(d, s): o = s * d[..., 3:] + d * (1 - s[..., 3:]); o[..., 3] = d[..., 3]; return o
    def shift(a, dx, dy):
        o = np.zeros_like(a); H, W = a.shape[:2]; o[max(0, dy):H + min(0, dy), max(0, dx):W + min(0, dx)] = a[max(0, -dy):H + min(0, -dy), max(0, -dx):W + min(0, -dx)]; return o
    rnd = lambda z: int(math.floor(z + .5))
    a0, b0, a1, b1 = rig['workRegion']; CR = (slice(b0 - 8, b1 + 8), slice(a0 - 8, a1 + 8))
    FR = pm(ld(f'{R}/{rig["frameSource"]}')[CR]); Pt = {e: {n: pm(ld(f'{D}/{ang}/{e}_{n}.png')[CR]) for n in ['white', 'iris', 'lash'] + [f'lid_{k}' for k in range(8)]} for e in rig['eyes']}
    comp = {}
    for L in ('current', 'diag'):
        tot = {'off_palette': 0, 'chroma': 0, 'cases': 0, 'worst': None}
        for X in (-1, 0, 1):
            for Y in (-1, 0, 1):
                for k in range(8):
                    cv = FR.copy()
                    for e in rig['eyes']:
                        l = dict(rig['irisLimitsPx'][e]); 
                        if L == 'diag': l.update({q: v for q, v in LIM[ang]['eyes'][e]['irislimits_diag'].items() if q.startswith('dx')})
                        dx = rnd(X * (l['dxAtXplus1'] if X > 0 else -l['dxAtXminus1'])); dy = rnd(Y * (l['dyAtYplus1'] if Y > 0 else -l['dyAtYminus1']))
                        lay = atop(Pt[e]['white'].copy(), shift(Pt[e]['iris'], dx, dy)); cv = over(over(over(cv, lay), Pt[e][f'lid_{k}']), Pt[e]['lash'])
                    a = np.clip(cv[..., 3:], 1e-9, 1); im = np.dstack([np.round(cv[..., :3] / a * 255), np.round(cv[..., 3] * 255)]).astype(np.uint8)
                    o = int(offmask(im, pal).sum()); c = int(chmask(im).sum()); tot['off_palette'] += o; tot['chroma'] += c; tot['cases'] += 1
                    if o + c and (tot['worst'] is None or o + c > tot['worst'][1]): tot['worst'] = [f'X{X} Y{Y} k{k}', o + c]
        comp[L] = tot
    res['composites'][ang] = comp
# 3) baseline diagonal off-palette px vs eye parts
eyemask = {}
for ang in ('045', '315'):
    rig = json.load(open(f'{D}/{ang}/rig.json')); m = None
    for e in rig['eyes']:
        for f in glob.glob(f'{D}/{ang}/{e}_*.png'):
            if f.endswith('_chroma.png'): continue
            a = Q.rgba(f)[..., 3] > 0
            if f.endswith('_iris.png'): a = binary_dilation(a, iterations=4)
            m = a if m is None else (m | a)
    eyemask[ang] = (binary_dilation(m, iterations=1), rig['viewFit'])
tot = {'off_palette': 0, 'chroma': 0, 'on_eye_off_palette': 0, 'on_eye_chroma': 0, 'by_system': {}}
for ang, s, f in Q.diag_sets(lambda *_: True):
    im = Q.rgba(f); pal = Q.palette(Q.palette_sources(ang, s, os.path.basename(f))); m = offmask(im, pal); ch = chmask(im)
    tot['off_palette'] += int(m.sum()); tot['chroma'] += int(ch.sum()); bs = tot['by_system'].setdefault(s, {'off_palette': 0, 'chroma': 0})
    bs['off_palette'] += int(m.sum()); bs['chroma'] += int(ch.sum())
    for kind, mm in (('off_palette', m), ('chroma', ch)):
        for y, x in zip(*np.nonzero(mm)):
            on = False; fx = fy = None
            if ang in eyemask:
                em, vf = eyemask[ang]; fx = (x - vf['dx']) / vf['scale']; fy = (y - vf['dy']) / vf['scale']
                xi, yi = int(round(fx)), int(round(fy)); on = 0 <= yi < em.shape[0] and 0 <= xi < em.shape[1] and bool(em[yi, xi])
            if on: tot['on_eye_' + kind] += 1
            res['baseline_diag_px_on_eyes'].setdefault(os.path.relpath(f, R), []).append({'kind': kind, 'view_xy': [int(x), int(y)], 'frame_xy': None if fx is None else [round(fx, 1), round(fy, 1)], 'rgb': im[y, x, :3].tolist(), 'alpha': int(im[y, x, 3]), 'on_eye_part': on})
res['baseline_diag_totals'] = tot
json.dump(res, open(f'{OUT}/eyes_diag_leak_supplement.json', 'w'), indent=1)
for ang in res['files']:
    t = {k: sum(r[k] for r in res['files'][ang]) for k in ('off_palette', 'chroma', 'soft_edge')}; print('diag eye files', ang, len(res['files'][ang]), t)
    for r in res['files'][ang]:
        if r['off_palette'] or r['chroma']: print('   ', r['file'], r['off_palette'], r['chroma'], r['px'][:10])
print('composites', json.dumps(res['composites']))
print('baseline diag', json.dumps(tot))
