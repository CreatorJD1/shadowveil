#!/usr/bin/env python3
"""Base Eyes independent check of Coder's diag iris limits v4 (rig/work/irislimits/diag_irislimits_v4.json; read-only),
on the post-fix staged diagonal eye files. Derived from eyes/qa/irislimits_diag/verify_irislimits.py (own compositor).
v4 offsets per eye: X+-1,Y0 -> irislimits_diag_v2 dx; X0,Y+-1 -> dy +-1; corners -> corners['X,Y'] dx/dy; rest 0.
Per render (045/315 x 9 gaze x 8 lids, both eyes = 288 eye-renders):
  outside = iris px (final != no-iris render) outside white & ~lid_k & ~lash ; on_ink = iris px on lid_k/lash
  lost    = shifted iris core (a>=128) px outside the white (lid-independent), vs each eye's Y-1 / Y+1 baseline (X0)
Also: X travel, both-eyes direction (same sign or zero, |dR-dL|<=1), rest diff v4 vs current rig and vs frame."""
import json, math, os, numpy as np
from PIL import Image, ImageDraw
R = '/workspace/shadowveil'; D = f'{R}/eyes/staged/diagonals'; OUT = os.path.dirname(os.path.abspath(__file__))
V4 = json.load(open(f'{R}/rig/work/irislimits/diag_irislimits_v4.json'))['angles']
ld = lambda p: np.asarray(Image.open(p).convert('RGBA')).astype(np.float64) / 255
def pm(x): y = x.copy(); y[..., :3] *= y[..., 3:]; return y
over = lambda d, s: s + d * (1 - s[..., 3:])
def atop(d, s): o = s * d[..., 3:] + d * (1 - s[..., 3:]); o[..., 3] = d[..., 3]; return o
def shift(a, dx, dy):
    o = np.zeros_like(a); H, W = a.shape[:2]; o[max(0, dy):H + min(0, dy), max(0, dx):W + min(0, dx)] = a[max(0, -dy):H + min(0, -dy), max(0, -dx):W + min(0, -dx)]; return o
rnd = lambda z: int(math.floor(z + .5))
def isch(c): c = c.astype(int); return (c[..., 2] > np.maximum(c[..., 0], c[..., 1]) + 60) & (c[..., 2] > 120)
def off_cur(l, X, Y): return (rnd(X * (l['dxAtXplus1'] if X > 0 else -l['dxAtXminus1'])), rnd(Y * (l['dyAtYplus1'] if Y > 0 else -l['dyAtYminus1'])))
def off_v4(ev, X, Y):
    if X and Y: c = ev['corners'][f'{X:+d},{Y:+d}']; return (int(c['dx']), int(c['dy']))
    return off_cur(ev['irislimits_diag_v2'], X, Y)
GZ = [(X, Y) for Y in (-1, 0, 1) for X in (-1, 0, 1)]
res = {'method': __doc__, 'angles': {}}; tiles = {}
for ang in ('045', '315'):
    rig = json.load(open(f'{D}/{ang}/rig.json')); a0, b0, a1, b1 = rig['workRegion']; CR = (slice(b0 - 12, b1 + 12), slice(a0 - 12, a1 + 12))
    names = ['white', 'iris', 'lash'] + [f'lid_{k}' for k in range(8)]
    for e in rig['eyes']:
        for n in names: full = ld(f'{D}/{ang}/{e}_{n}.png')[..., 3]; assert full.sum() == full[CR].sum(), (e, n)
    FR = pm(ld(f'{R}/{rig["frameSource"]}')[CR]); P = {e: {n: pm(ld(f'{D}/{ang}/{e}_{n}.png')[CR]) for n in names} for e in rig['eyes']}
    OFF = {'v4': {e: {g: off_v4(V4[ang]['eyes'][e], *g) for g in GZ} for e in rig['eyes']},
           'current': {e: {g: off_cur(rig['irisLimitsPx'][e], *g) for g in GZ} for e in rig['eyes']}}
    def render(lim, g, k, iris=True):
        cv = FR.copy()
        for e in rig['eyes']:
            lay = P[e]['white'].copy()
            if iris: lay = atop(lay, shift(P[e]['iris'], *OFF[lim][e][g]))
            cv = over(over(over(cv, lay), P[e][f'lid_{k}']), P[e]['lash'])
        return np.round(cv * 255).astype(np.int32)
    A = {'cases': [], 'eyes': {}, 'offsets_v4': {e: {f'{g[0]:+d},{g[1]:+d}': OFF['v4'][e][g] for g in GZ} for e in rig['eyes']}}
    lost = {}
    for e in rig['eyes']:
        wh = P[e]['white'][..., 3] > 0; core = (P[e]['iris'][..., 3] >= .5).astype(np.uint8)
        lost[e] = {g: int(((shift(core, *OFF['v4'][e][g]) > 0) & ~wh).sum()) for g in GZ}
    for g in GZ:
        for k in range(8):
            im = render('v4', g, k); shows = (im != render('v4', g, k, False)).any(-1); c = {'X': g[0], 'Y': g[1], 'k': k, 'eyes': {}}
            for e in rig['eyes']:
                p = P[e]; wh = p['white'][..., 3] > 0; ink = (p[f'lid_{k}'][..., 3] > 0) | (p['lash'][..., 3] > 0)
                s = shows & (wh | ink | (shift(p['iris'], *OFF['v4'][e][g])[..., 3] > 0))
                c['eyes'][e] = {'off': OFF['v4'][e][g], 'iris_px': int(s.sum()), 'outside': int((s & ~(wh & ~ink)).sum()), 'on_ink': int((s & ink).sum()), 'lost': lost[e][g]}
            A['cases'].append(c); tiles[(ang, g, k)] = (im[..., :3].astype(np.uint8), c)
    for e in rig['eyes']:
        bm, bp = lost[e][(0, -1)], lost[e][(0, 1)]
        A['eyes'][e] = {'baseline_lost_Y-1': bm, 'baseline_lost_Y+1': bp,
            'corners': {f'{X:+d},{Y:+d}': {'dx': OFF['v4'][e][(X, Y)][0], 'dy': OFF['v4'][e][(X, Y)][1], 'lost': lost[e][(X, Y)],
                        'vs_sameY_baseline': lost[e][(X, Y)] - (bm if Y < 0 else bp), 'vs_max_baseline': lost[e][(X, Y)] - max(bm, bp)} for X in (-1, 1) for Y in (-1, 1)},
            'X_travel': {f'{X:+d},{Y:+d}': OFF['v4'][e][(X, Y)][0] for X in (-1, 1) for Y in (-1, 0, 1)},
            'X_travel_current': {f'{X:+d},{Y:+d}': OFF['current'][e][(X, Y)][0] for X in (-1, 1) for Y in (-1, 0, 1)},
            'lost_Xpm1_Y0': {'X-1': lost[e][(-1, 0)], 'X+1': lost[e][(1, 0)]}}
    eR, eL = rig['eyes']
    A['direction'] = {f'{X:+d},{Y:+d}': {'dR': OFF['v4']['EyeR'][(X, Y)][0], 'dL': OFF['v4']['EyeL'][(X, Y)][0],
                      'ok': (OFF['v4']['EyeR'][(X, Y)][0] * OFF['v4']['EyeL'][(X, Y)][0] >= 0) and abs(OFF['v4']['EyeR'][(X, Y)][0] - OFF['v4']['EyeL'][(X, Y)][0]) <= 1} for X, Y in GZ}
    rv, rc = render('v4', (0, 0), 0), render('current', (0, 0), 0); f8 = np.round(FR * 255).astype(np.int32); dfr = (rv[..., :3] != f8[..., :3]).any(-1); face = ~isch(f8[..., :3])
    A['rest'] = {'v4_vs_current_px': int((rv != rc).any(-1).sum()), 'v4_vs_frame_inside_face_px': int((dfr & face).sum()), 'v4_vs_frame_outside_face_edge_px': int((dfr & ~face).sum())}
    A['workRegion'] = [9, 9, 12 + a1 - a0 + 3, 12 + b1 - b0 + 3]; res['angles'][ang] = A
cs = [(a, c, e) for a, A in res['angles'].items() for c in A['cases'] for e in c['eyes']]
res['totals'] = {'eye_renders': len(cs), 'max_outside': max(c['eyes'][e]['outside'] for a, c, e in cs), 'sum_outside': sum(c['eyes'][e]['outside'] for a, c, e in cs),
                 'max_on_ink': max(c['eyes'][e]['on_ink'] for a, c, e in cs)}
json.dump(res, open(f'{OUT}/verify_v4_independent.json', 'w'), indent=1)
print('totals', res['totals'])
for a, A in res['angles'].items():
    print(a, 'rest', A['rest'])
    for e, x in A['eyes'].items(): print(' ', e, 'base Y-1/Y+1', x['baseline_lost_Y-1'], x['baseline_lost_Y+1'], 'lost X-1/X+1 Y0', x['lost_Xpm1_Y0'], '\n    corners', x['corners'], '\n    Xtravel v4', x['X_travel'], '\n    Xtravel cur', x['X_travel_current'])
    print('  direction', {g: (d['dR'], d['dL'], d['ok']) for g, d in A['direction'].items()})
# sheet: per angle rows k0..7, cols 9 gaze (v4)
z = 5; blocks = []
for ang in ('045', '315'):
    x0, y0, x1, y1 = res['angles'][ang]['workRegion']; eyes = list(res['angles'][ang]['eyes']); rowsI = []
    for k in range(8):
        row = []
        for g in GZ:
            im, c = tiles[(ang, g, k)]
            I = Image.fromarray(im[y0:y1, x0:x1]).resize(((x1 - x0) * z, (y1 - y0) * z), Image.NEAREST)
            T = Image.new('RGB', (I.width + 6, I.height + 30), 'white'); T.paste(I, (3, 28)); d = ImageDraw.Draw(T)
            d.text((3, 1), f'{ang} k{k} X{g[0]:+d} Y{g[1]:+d}', fill=(0, 0, 0))
            bad = any(c['eyes'][e]['outside'] or c['eyes'][e]['on_ink'] for e in eyes)
            d.text((3, 14), ' '.join(f"{e[-1]}:dx{c['eyes'][e]['off'][0]:+d} out{c['eyes'][e]['outside']} lost{c['eyes'][e]['lost']}" for e in eyes), fill=(255, 0, 0) if bad else (0, 0, 0))
            row.append(np.array(T))
        rowsI.append(np.concatenate(row, 1))
    A = res['angles'][ang]; hdr = Image.new('RGB', (rowsI[0].shape[1], 24), (230, 230, 230))
    ImageDraw.Draw(hdr).text((4, 6), f"{ang} deg, irislimits v4 (Coder), post-fix staged eyes. Rows lid k0..k7, cols (Y,X). R=EyeR amber, L=EyeL green. out=iris px outside white&~lid&~lash; lost=core px cut by the white. Rest v4 vs current {A['rest']['v4_vs_current_px']} px", fill=(0, 0, 0))
    blocks.append(np.concatenate([np.array(hdr)] + rowsI, 0))
W = max(b.shape[1] for b in blocks); blocks = [np.pad(b, ((0, 12), (0, W - b.shape[1]), (0, 0)), constant_values=255) for b in blocks]
Image.fromarray(np.concatenate(blocks, 0)).save(f'{OUT}/sheet_v4.png'); print('wrote sheet_v4.png')
