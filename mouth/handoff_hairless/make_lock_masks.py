#!/usr/bin/env python3
"""Mouth lock masks for Base Body's hairless/divided base (staged, not live).
Locked (white) = union of every mouth shape's opaque pixels inside its partsBBox
 + rest lips of base.png (base pixels under views/<v>/mouth/rest.png alpha),
 dilated by 4 px (Chebyshev / 9x9 square, i.e. conservative)."""
import json, os
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
ROOT = '/workspace/shadowveil'; OUT = os.path.join(ROOT, 'mouth/handoff_hairless')
W, H, R = 1365, 1739, 4
summary = {}
for v in ['apose', 'tpose', 'left', 'right']:
    vd = f'{ROOT}/views/{v}'
    rj = json.load(open(f'{vd}/mouth/rig.json'))
    base = np.array(Image.open(f'{vd}/base.png').convert('RGBA'))
    assert base.shape[:2] == (H, W)
    u = np.zeros((H, W), bool)
    shapes = {}
    for k, (x0, y0, x1, y1) in rj['partsBBox'].items():
        a = np.array(Image.open(f'{vd}/mouth/{k}.png').convert('RGBA'))[..., 3] > 0
        clip = np.zeros_like(a); clip[y0:y1+1, x0:x1+1] = True
        m = a & clip
        assert m.sum() == a.sum(), f'{v}/{k}: opaque pixels outside partsBBox'
        shapes[k] = int(m.sum()); u |= m
    rest = np.array(Image.open(f'{vd}/mouth/rest.png').convert('RGBA'))
    rm = rest[..., 3] > 0
    assert (rest[rm] == base[rm]).all(), 'rest.png differs from base.png lips'
    u |= rm
    lock = binary_dilation(u, structure=np.ones((2*R+1, 2*R+1), bool))
    Image.fromarray((lock*255).astype(np.uint8), 'L').save(f'{OUT}/{v}_mouth_lock.png')
    ys, xs = np.nonzero(lock); uy, ux = np.nonzero(u)
    info = {
        'view': v, 'canvas': {'width': W, 'height': H},
        'mask': f'mouth/handoff_hairless/{v}_mouth_lock.png',
        'meaning': 'white(255)=locked: Body must keep these base pixels byte-identical (RGBA); black(0)=free',
        'bbox': {'x0': int(xs.min()), 'y0': int(ys.min()), 'x1': int(xs.max()), 'y1': int(ys.max()), 'note': 'inclusive, view px'},
        'pixelCount': int(lock.sum()),
        'undilatedBBox': {'x0': int(ux.min()), 'y0': int(uy.min()), 'x1': int(ux.max()), 'y1': int(uy.max())},
        'undilatedPixelCount': int(u.sum()),
        'dilation': {'px': R, 'metric': 'chebyshev (9x9 square)'},
        'sources': {'shapes_opaque_px': shapes, 'rest_lips_of_base_px': int(rm.sum())},
        'anchor': rj['anchor'], 'drawnMouthBBox': rj['drawnMouthBBox'],
        'base_sha_note': 'check: base[lock] of Body output == views/%s/base.png[lock]' % v,
    }
    json.dump(info, open(f'{OUT}/{v}_mouth_lock.json', 'w'), indent=2)
    summary[v] = {'bbox': info['bbox'], 'pixelCount': info['pixelCount']}
    print(v, info['bbox'], info['pixelCount'])
json.dump(summary, open(f'{OUT}/mouth_lock_summary.json', 'w'), indent=2)
