"""Shared helpers for lashfix2.py / measure.py: cached eye geometry (from lashgeo.geom == export.py's regions)."""
import os, sys, numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = '/workspace/shadowveil'
EYES = {'apose': ['EyeR', 'EyeL'], 'tpose': ['EyeR', 'EyeL'], 'left': ['EyeL'], 'right': ['EyeR']}
H, W, NF, KC = 1739, 1365, 8, 7
KEYS_B = ['mask', 'cover', 'crease', 'band', 'aa', 'fwd', 'fwd_cover', 'hair_sw', 'dark_unconn', 'lash', 'bb']
def geo(v, e):
    p = f'{HERE}/tmp/cache/{v}_{e}.npz'
    if not os.path.exists(p):
        import lashgeo
        g = lashgeo.geom(v, e)
        d = {k: np.asarray(g[k], bool) for k in KEYS_B}
        d.update(top=g['top'], bot=g['bot'], cols=g['cols'], c0=g['c0'], c1=g['c1'], side=g['side'],
                 skin=np.asarray(g['skin']), lashcolor=np.asarray(g['lashcolor']))
        np.savez_compressed(p, **d); del g
    z = np.load(p); d = {k: z[k] for k in z.files}
    for k in ('c0', 'c1', 'side'): d[k] = int(d[k])
    rgb = np.array(Image.open(f'{ROOT}/views/{v}/base.png').convert('RGB')).astype(int)
    d['rgb'] = rgb; d['lum'] = rgb.mean(2)
    return d
