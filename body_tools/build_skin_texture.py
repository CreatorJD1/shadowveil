#!/usr/bin/env python3
"""Skin underfill texture (contract v1.4 section 8) for views/<view>/: writes views/<view>/base_body_skin.png.
= base_body.png, plus hidden flat fill where the fill is covered at rest by another owner's fully opaque part:
forearm skin continued under each palm (L_palm/R_palm alpha 255) near the wristPivot, so a WristL/R bend or palm
overlap never reveals background. Flat colour only (the forearm's dominant flat skin colour), no shading.
Every pixel visible at rest is untouched (rest composite identical). base_body.png is never modified.
Note: the v1.4 skin format has one image with UV = rest position, and at rest the whole image is drawn, so fill
cannot be placed under a limb's own pixels or on transparent background; see skin notes in the report."""
import json, sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
view = sys.argv[1] if len(sys.argv) > 1 else 'apose'
# per-view wrist extension (Hands tpose wrist check 2026-09-29, Coder: no rest tolerance): fill ~4 px past the forearm end
# under the palm's turning area, kept off base.png's semi-transparent wrist rows (alpha 253 / 241-249) and the row above each,
# and only on the rows between them (rows outside would close the semi-row slit into an enclosed hole)
WRIST_EXT = {'tpose': {'px': 4, 'skipY': [389, 390, 413, 414], 'rowsY': [391, 412]}}   # rowsY: only between the semi rows, so no enclosed slit forms
vd = f'views/{view}'
bb = np.array(Image.open(f'{vd}/base_body.png').convert('RGBA'))
H, W = bb.shape[:2]; out = bb.copy()
rig = json.load(open(f'{vd}/body/rig.json')); by = {p['id']: p for p in rig['parts']}
yy, xx = np.mgrid[:H, :W]
rep = {}
hands = json.load(open(f'{vd}/hands/rig.json'))['parts']
for s in 'LR':
    fa = by.get(f'forearm_{s}')
    pl = next((p for p in hands if p.get('parentExternal') == f'forearm_{s}' and p.get('file') and not p.get('hidden')), None)
    if not fa or not fa.get('file') or fa.get('hidden') or not pl: continue   # profile far arm: hidden, nothing to fill
    cx, cy = fa['wristPivot']['x'], fa['wristPivot']['y']
    palm = np.array(Image.open(f"{vd}/hands/{pl['file']}").convert('RGBA'))[..., 3] == 255
    fam = np.array(Image.open(f'{vd}/body/forearm_{s}.png').convert('RGBA'))
    d = np.hypot(xx + .5 - cx, yy + .5 - cy)
    ring = (fam[..., 3] == 255) & (d < 40)
    cols, n = np.unique(fam[ring][:, :3], axis=0, return_counts=True); col = cols[n.argmax()]
    # fill: under the palm's solid pixels (1 px inset from its edge), transparent in base_body, within 30 px of the wrist,
    # connected to the forearm
    cand = ndi.binary_erosion(palm, iterations=1) & (bb[..., 3] == 0) & (d < 30)
    lab, k = ndi.label(cand | ((bb[..., 3] > 0) & (d < 30)))
    fl = set(np.unique(lab[(fam[..., 3] > 0) & (d < 30)])) - {0}
    fill = cand & np.isin(lab, list(fl))
    ext = np.zeros_like(fill); ex = WRIST_EXT.get(view)
    if ex:
        # extension (Hands' tpose wrist check): ex['px'] px past the forearm's opaque end, under palm alpha 255 only (no inset),
        # never on the skip rows (base.png's semi-transparent wrist rows and the row above each: rest must stay exact)
        fo = (bb[..., 3] > 0) & (fam[..., 3] > 0)
        ext = (palm & (bb[..., 3] == 0) & ~fill & (ndi.distance_transform_edt(~fo) <= ex['px']) & (d < 30)
               & ~np.isin(yy, ex['skipY']) & (yy >= ex['rowsY'][0]) & (yy <= ex['rowsY'][1]))
    out[fill | ext, :3] = col; out[fill | ext, 3] = 255
    rep[s] = {'fillPx': int(fill.sum()), 'extPx': int(ext.sum()), 'rgb': [int(c) for c in col]}
import os; Image.fromarray(out, 'RGBA').save(f'{vd}/base_body_skin.png.tmp', format='PNG'); os.replace(f'{vd}/base_body_skin.png.tmp', f'{vd}/base_body_skin.png')  # atomic
print(json.dumps({'out': f'{vd}/base_body_skin.png', **rep}))
