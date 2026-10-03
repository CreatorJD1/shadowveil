#!/usr/bin/env python3
"""Base Eyes independent check of rig/work/irislimits diag irisLimitsPx (read-only on rig/ and eyes/staged/).
Own compositor (premultiplied over / source-atop; no import of render_eyes or render_diag_limits).
For 045/315, X,Y in {-1,0,1}, lid k 0..7, limits in {current, diag}:
  iris_px   = px whose final RGBA differs from the same render with the iris removed (where iris actually shows)
  outside   = iris_px outside opening_k = white & ~lid_k & ~lash   (must be 0)
  on_ink    = iris_px on lid_k or lash ink (must be 0)
  clipped   = shifted iris core (a>=128) px lost because they fall outside the white (iris cut by the corner / lid edge)
Rest: (0,0,k0) diag vs current vs frame. Corner reach: gap (px) from iris leading edge to white extreme on iris rows."""
import json, math, os, numpy as np
from PIL import Image, ImageDraw
R = '/workspace/shadowveil'; D = f'{R}/eyes/staged/diagonals'; OUT = os.path.dirname(os.path.abspath(__file__)) + '/verify_v4'; os.makedirs(OUT, exist_ok=True)
LIM = json.load(open(f'{R}/rig/work/irislimits/diag_irislimits_v2_flat.json'))  # copy of Base Eyes' verify pointed at v2
ld = lambda p: np.asarray(Image.open(p).convert('RGBA')).astype(np.float64) / 255
def pm(x): y = x.copy(); y[..., :3] *= y[..., 3:]; return y
def over(dst, src): return src + dst * (1 - src[..., 3:])
def atop(dst, src): o = src * dst[..., 3:] + dst * (1 - src[..., 3:]); o[..., 3] = dst[..., 3]; return o
def shift(a, dx, dy):
    o = np.zeros_like(a); H, W = a.shape[:2]
    o[max(0, dy):H + min(0, dy), max(0, dx):W + min(0, dx)] = a[max(0, -dy):H + min(0, -dy), max(0, -dx):W + min(0, -dx)]; return o
rnd = lambda z: int(math.floor(z + 0.5))
V4 = json.load(open(f'{R}/rig/work/irislimits/diag_irislimits_v4.json'))['angles']  # v4: per-corner table
def off(l, X, Y):
    if X and Y and '_c' in l:
        c = l['_c'][f'{X:+d},{Y:+d}']; return (c['dx'], c['dy'])
    return (rnd(X * (l['dxAtXplus1'] if X > 0 else -l['dxAtXminus1'])), rnd(Y * (l['dyAtYplus1'] if Y > 0 else -l['dyAtYminus1'])))
res = {'method': __doc__, 'angles': {}}; tiles = {}
for ang in ('045', '315'):
    rig = json.load(open(f'{D}/{ang}/rig.json')); a0, b0, a1, b1 = rig['workRegion']; CR = (slice(b0 - 12, b1 + 12), slice(a0 - 12, a1 + 12))
    # crop to workRegion+12 px (max iris shift 4); verified below that no eye part has alpha outside the crop
    fr = ld(f'{R}/{rig["frameSource"]}')[CR]; FR = pm(fr)
    for e in rig['eyes']:
        for n in ['white', 'iris', 'lash'] + [f'lid_{k}' for k in range(8)]:
            full = ld(f'{D}/{ang}/{e}_{n}.png')[..., 3]; assert full.sum() == full[CR].sum(), (e, n)
    P = {e: {n: pm(ld(f'{D}/{ang}/{e}_{n}.png')[CR]) for n in ['white', 'iris', 'lash'] + [f'lid_{k}' for k in range(8)]} for e in rig['eyes']}
    lims = {e: {'current': rig['irisLimitsPx'][e], 'diag': {**rig['irisLimitsPx'][e], **{k: v for k, v in LIM[ang]['eyes'][e]['irislimits_diag'].items() if k.startswith('dx')}}} for e in rig['eyes']}
    for e in rig['eyes']: lims[e]['diag']['_c'] = V4[ang]['eyes'][e]['corners']
    def render(lim, X, Y, k, iris=True):
        cv = FR.copy()
        for e in rig['eyes']:
            p = P[e]; layer = p['white'].copy()
            if iris: layer = atop(layer, shift(p['iris'], *off(lims[e][lim], X, Y)))
            cv = over(over(over(cv, layer), p[f'lid_{k}']), p['lash'])
        return np.round(cv * 255).astype(np.int32)
    A = {'cases': [], 'eyes': {}}
    for e in rig['eyes']:
        p = P[e]; wh = p['white'][..., 3] > 0; core = p['iris'][..., 3] >= 0.5; ys, xs = np.nonzero(core)
        rows = range(ys.min(), ys.max() + 1); wxmax = max(np.nonzero(wh[y])[0].max() for y in rows if wh[y].any()); wxmin = min(np.nonzero(wh[y])[0].min() for y in rows if wh[y].any())
        A['eyes'][e] = {'limits': lims[e], 'white_px': int(wh.sum()), 'iris_core_px': int(core.sum()),
            'corner_gap_px_on_iris_rows': {L: {'X+1': int(wxmax - (xs.max() + off(lims[e][L], 1, 0)[0])), 'X-1': int((xs.min() + off(lims[e][L], -1, 0)[0]) - wxmin)} for L in ('current', 'diag')},
            'corner_gap_rest': {'X+1 side': int(wxmax - xs.max()), 'X-1 side': int(xs.min() - wxmin)},
            'move_px_Xplus1': {L: off(lims[e][L], 1, 0)[0] for L in ('current', 'diag')},
            'move_px_Xminus1': {L: off(lims[e][L], -1, 0)[0] for L in ('current', 'diag')}}
    for lim in ('current', 'diag'):
        for X in (-1, 0, 1):
            for Y in (-1, 0, 1):
                for k in range(8):
                    im = render(lim, X, Y, k); no = render(lim, X, Y, k, False); shows = (im != no).any(-1)
                    c = {'lim': lim, 'X': X, 'Y': Y, 'k': k, 'eyes': {}}
                    for e in rig['eyes']:
                        p = P[e]; wh = p['white'][..., 3] > 0; ink = (p[f'lid_{k}'][..., 3] > 0) | (p['lash'][..., 3] > 0)
                        region = wh | ink | (shift(p['iris'], *off(lims[e][lim], X, Y))[..., 3] > 0)
                        s = shows & region; opening = wh & ~ink
                        sc = shift((p['iris'][..., 3] >= 0.5).astype(np.uint8), *off(lims[e][lim], X, Y)) > 0
                        c['eyes'][e] = {'off': off(lims[e][lim], X, Y), 'iris_px': int(s.sum()), 'outside': int((s & ~opening).sum()),
                                        'on_ink': int((s & ink).sum()), 'clipped': int((sc & ~wh).sum()), 'opening_px': int(opening.sum())}
                    A['cases'].append(c)
                    if lim == 'diag': tiles[(ang, X, Y, k)] = (im[..., :3].astype(np.uint8), shows, c)
    # rest + diag-vs-current per case
    rest_d = render('diag', 0, 0, 0); rest_c = render('current', 0, 0, 0); frame8 = np.round(FR * 255).astype(np.int32)
    A['rest'] = {'diag_vs_current_px': int((rest_d != rest_c).any(-1).sum()), 'diag_vs_frame_px': int((rest_d[..., :3] != frame8[..., :3]).any(-1).sum()),
                 'all_k_X0_diag_vs_current_px': sum(int((render('diag', 0, Y, k) != render('current', 0, Y, k)).any(-1).sum()) for Y in (-1, 0, 1) for k in range(8))}
    A['rig'] = rig; del A['rig']; A['workRegion'] = [12-3, 12-3, 12 + a1 - a0 + 3, 12 + b1 - b0 + 3]; A['workRegion_frame'] = rig['workRegion']; res['angles'][ang] = A
json.dump(res, open(f'{OUT}/verify_irislimits.json', 'w'), indent=1)
# summary
for ang, A in res['angles'].items():
    print(ang, 'rest', A['rest'])
    for e, x in A['eyes'].items(): print(' ', e, 'move X+1', x['move_px_Xplus1'], 'X-1', x['move_px_Xminus1'], 'gap', x['corner_gap_px_on_iris_rows'], 'rest gap', x['corner_gap_rest'])
    for lim in ('current', 'diag'):
        cs = [c for c in A['cases'] if c['lim'] == lim]
        for e in A['eyes']:
            print('  ', lim, e, 'max outside', max(c['eyes'][e]['outside'] for c in cs), 'max on_ink', max(c['eyes'][e]['on_ink'] for c in cs),
                  'clipped>0 cases', sum(c['eyes'][e]['clipped'] > 0 for c in cs), '/', len(cs), 'max clipped', max(c['eyes'][e]['clipped'] for c in cs))
# sheet: per angle, rows k0..7, cols 9 gaze (diag); magenta = iris px outside opening (none expected); label = outside per eye
z = 5; blocks = []
for ang in ('045', '315'):
    x0, y0, x1, y1 = res['angles'][ang]['workRegion']; eyes = list(res['angles'][ang]['eyes'])
    rowsI = []
    for k in range(8):
        row = []
        for Y in (-1, 0, 1):
            for X in (-1, 0, 1):
                im, shows, c = tiles[(ang, X, Y, k)]; im = im.copy()
                for e in eyes:
                    pass
                I = Image.fromarray(im[y0:y1, x0:x1]).resize(((x1 - x0) * z, (y1 - y0) * z), Image.NEAREST)
                T = Image.new('RGB', (I.width + 6, I.height + 30), 'white'); T.paste(I, (3, 28)); d = ImageDraw.Draw(T)
                d.text((3, 1), f'{ang} k{k} X{X:+d} Y{Y:+d}', fill=(0, 0, 0))
                d.text((3, 14), ' '.join(f"{e[-1]}:{c['eyes'][e]['off']} out{c['eyes'][e]['outside']}" for e in eyes), fill=(0, 0, 0) if all(c['eyes'][e]['outside'] == 0 for e in eyes) else (255, 0, 0))
                row.append(np.array(T))
        rowsI.append(np.concatenate(row, 1))
    hdr = Image.new('RGB', (rowsI[0].shape[1], 24), (230, 230, 230))
    ImageDraw.Draw(hdr).text((4, 6), f"{ang} deg, irislimits=diag. Rows lid k0..k7, cols (Y,X). L=EyeL green, R=EyeR amber. 'out'=iris px outside white&~lid&~lash. Rest diag-vs-current {res['angles'][ang]['rest']['diag_vs_current_px']} px", fill=(0, 0, 0))
    blocks.append(np.concatenate([np.array(hdr)] + rowsI, 0))
W = max(b.shape[1] for b in blocks); blocks = [np.pad(b, ((0, 12), (0, W - b.shape[1]), (0, 0)), constant_values=255) for b in blocks]
Image.fromarray(np.concatenate(blocks, 0)).save(f'{OUT}/irislimits_diag_check.png'); print('wrote', f'{OUT}/irislimits_diag_check.png')
