#!/usr/bin/env python3
"""Measure her own mouth shapes (views/<v>/mouth/*.png) to calibrate MouthOpen / MouthForm targets.
Writes calib.json. Read-only on views/."""
import json, sys
import numpy as np
from mb import *

SHAPES = ['rest', 'M', 'smile', 'AA_half', 'AA', 'OH_half', 'OH', 'EE_half', 'EE']

def seam_cols(img, pal, ay, T, band=(-12, 4)):
    L = lum(img); a = img[..., 3] == 255
    res = {}
    for x in range(600, 760):
        ys = [y for y in range(ay + band[0], ay + band[1] + 1) if a[y, x] and L[y, x] < T]
        if ys:
            ym = min(ys, key=lambda y: (L[y, x], abs(y - ay)))
            res[x] = ym
    return res

def run(v):
    rj, pal = palette(v)
    ax, ay = rj['anchor']['x'], rj['anchor']['y']
    parts = json.load(open(f'{ROOT}/mouth/staged/mesh_split/{v}/parts.json'))
    T = (lum(pal['line'][None]) [0] + lum(pal['lower'][None])[0]) / 2
    base = load_rgba(f'{ROOT}/views/{v}/base.png')
    sb1 = {x: y for x, y in parts['seam']['boundary_firstLowerRow']}   # first lower-lip row (rest)
    out = {'view': v, 'anchor': [ax, ay], 'T_seam': round(float(T), 2), 'shapes': {}}
    for s in SHAPES:
        img = load_rgba(f'{ROOT}/views/{v}/mouth/{s}.png')
        comp = img.astype(float)  # composite over base for silhouette
        a = img[..., 3:4] / 255.0
        comp = (img[..., :3] * a + base[..., :3] * (1 - a))
        sil = mouth_sil(comp, pal) & (img[..., 3] > 0)
        cav = cavity_mask(img, pal)
        if not cav[:, ax-4:ax+5].any() or cav.sum() < 40: cav[:] = False
        cols = range(ax - 4, ax + 5)
        def colstat(m, fn):
            vals = [fn(np.nonzero(m[:, x])[0]) for x in cols if m[:, x].any()]
            return float(np.median(vals)) if vals else None
        rec = {'sil_top_c': colstat(sil, min), 'sil_bot_c': colstat(sil, max),
               'sil_px': int(sil.sum()), 'cav_px': int(cav.sum())}
        if cav.any():
            rec['cav_top_c'] = colstat(cav, min); rec['cav_bot_c'] = colstat(cav, max)
            rec['cav_h_c'] = rec['cav_bot_c'] - rec['cav_top_c'] + 1
            # per-column cavity height profile
            prof = {}
            for x in range(600, 760):
                ys = np.nonzero(cav[:, x])[0]
                if len(ys): prof[x] = [int(ys.min()), int(ys.max())]
            rec['cav_cols'] = prof
            # upper lift: rest inner edge (first lower row) vs cavity top
            rec['upper_lift_c'] = float(np.median([sb1[x] - prof[x][0] for x in cols if x in prof]))
        sc = seam_cols(img, pal, ay, T)
        if sc and not cav.any():
            xs = sorted(sc)
            # endpoints of the contiguous run containing ax
            run_ = [ax]
            l = ax
            while l - 1 in sc or l - 2 in sc: l = l - 1 if l - 1 in sc else l - 2
            r = ax
            while r + 1 in sc or r + 2 in sc: r = r + 1 if r + 1 in sc else r + 2
            rec['seam'] = {str(x): int(sc[x]) for x in xs}
            rec['corner_L'] = [l, int(sc[l])]; rec['corner_R'] = [r, int(sc[r])]
            rec['seam_c'] = float(np.median([sc[x] for x in cols if x in sc]))
        out['shapes'][s] = rec
    R = out['shapes']['rest']
    for s in ['M', 'smile']:
        S = out['shapes'][s]
        S['corner_dL'] = [S['corner_L'][0] - R['corner_L'][0], S['corner_L'][1] - R['corner_L'][1]]
        S['corner_dR'] = [S['corner_R'][0] - R['corner_R'][0], S['corner_R'][1] - R['corner_R'][1]]
        # seam offset profile vs rest, as function of u
        hw = (R['corner_R'][0] - R['corner_L'][0]) / 2; cx = (R['corner_R'][0] + R['corner_L'][0]) / 2
        prof = []
        for x, y in S['seam'].items():
            x = int(x)
            if str(x) in R['seam']:
                prof.append([round((x - cx) / hw, 3), y - R['seam'][str(x)]])
        S['seam_offset_vs_rest'] = prof
    out['rest_corner_centre_x'] = (R['corner_R'][0] + R['corner_L'][0]) / 2
    out['rest_half_width'] = (R['corner_R'][0] - R['corner_L'][0]) / 2
    return out

if __name__ == '__main__':
    res = {v: run(v) for v in (sys.argv[1:] or ['apose', 'tpose'])}
    json.dump(res, open(f'{ROOT}/mouth/staged/mesh_bend/calib.json', 'w'), indent=1)
    for v, o in res.items():
        print(v, 'T', o['T_seam'], 'hw', o['rest_half_width'], 'cx', o['rest_corner_centre_x'])
        for s, r in o['shapes'].items():
            print(' ', s, {k: r[k] for k in r if k not in ('seam', 'cav_cols', 'seam_offset_vs_rest')})
        for s in ['M', 'smile']:
            print(' ', s, 'offset', o['shapes'][s]['seam_offset_vs_rest'])
