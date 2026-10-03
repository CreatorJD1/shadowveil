#!/usr/bin/env python3
"""Fix the chroma (key-blue) px in the staged diagonal far-eye files (Base Eyes, own files only).
Per chroma px p (qa_gates rule: a>0, b>max(r,g)+60, b>120), unmix against the frame's local key blue B:
  for every palette tone P (qa_gates palette for <ang>/eyes, minus bluish tones b>max(r,g)+40) find t in [0,1]
  minimising |p - ((1-t)P + tB)|; take the best P -> (P*, t).
  t >= 0.9                -> background: alpha 0
  t <= 0.5                -> line/skin edge blend: set to P* (exact palette tone), alpha 255
  (a snapped px left as an island with no untouched original px in its component is cleared: floating speck)
  0.5 < t < 0.9           -> mostly blue: alpha 0, UNLESS removing it splits the part's 8-connected opaque art
                             (more components than before) - then it is set to P* instead (keeps the line within 1 px).
Then <file>_chroma.png is regenerated exactly as before: part RGB where alpha>0, (0,0,255) elsewhere.
Originals: eyes/staged/diagonals/backups_chroma_fix/<ang>/."""
import sys, os, json, numpy as np
sys.dont_write_bytecode = True
R = '/workspace/shadowveil'; sys.path.insert(0, f'{R}/rig'); sys.argv = sys.argv[:1]
import qa_gates as Q
from PIL import Image
from scipy.ndimage import label
D = f'{R}/eyes/staged/diagonals'; BK = f'{D}/backups_chroma_fix'; OUT = f'{R}/eyes/qa/qa_gates'
FR = {'045': 'f033', '315': 'f191'}; JOBS = [('045', 'EyeR', 'lash'), ('045', 'EyeR', 'lid_0'), ('315', 'EyeL', 'lash'), ('315', 'EyeL', 'lid_0')]
def isch(c): c = np.asarray(c, int); return (c[..., 2] > np.maximum(c[..., 0], c[..., 1]) + 60) & (c[..., 2] > 120)
def ncomp(a): return label(a, structure=np.ones((3, 3)))[1]
log = {'doc': __doc__, 'files': {}}
for ang, e, n in JOBS:
    fr = Q.rgba(f'{R}/reference/apose_turn/frames/{FR[ang]}.png')[..., :3].astype(float)
    pal = Q.unpack(Q.palette(Q.palette_sources(ang, 'eyes', 'x.png'))).astype(float)
    pal = pal[~(pal[:, 2] > np.maximum(pal[:, 0], pal[:, 1]) + 40)]
    I = Q.rgba(f'{BK}/{ang}/{e}_{n}.png').copy(); H, W = I.shape[:2]
    m = (I[..., 3] > 0) & isch(I[..., :3]); ys, xs = np.nonzero(m)
    # local key blue: mean of frame px that are near-pure key (b>230, r,g<20) within 6 px, else (0,0,255)
    keymask = (fr[..., 2] > 230) & (fr[..., 0] < 20) & (fr[..., 1] < 20)
    dec = []
    for y, x in zip(ys, xs):
        y0, y1, x0, x1 = max(0, y - 6), y + 7, max(0, x - 6), x + 7; km = keymask[y0:y1, x0:x1]
        B = fr[y0:y1, x0:x1][km].mean(0) if km.any() else np.array([0., 0., 255.])
        p = I[y, x, :3].astype(float); d = B - pal; num = ((p - pal) * d).sum(1); den = (d * d).sum(1) + 1e-9
        t = np.clip(num / den, 0, 1); res = np.linalg.norm(p - (pal + t[:, None] * d), axis=1); j = int(res.argmin())
        dec.append({'xy': [int(x), int(y)], 'rgb': I[y, x, :3].tolist(), 't_blue': round(float(t[j]), 3), 'P': pal[j].astype(int).tolist(), 'resid': round(float(res[j]), 1)})
    before_c = ncomp(I[..., 3] > 0); A = I[..., 3] > 0
    # first pass: background + clear blends; mid ones to transparent tentatively
    for d in dec:
        x, y = d['xy']
        if d['t_blue'] <= 0.5: d['action'] = 'snap'
        else: d['action'] = 'clear'; A[y, x] = False
    # connectivity guard: re-add mid-t px (lowest t first) while components exceed original
    mids = sorted([d for d in dec if 0.5 < d['t_blue'] < 0.9], key=lambda d: d['t_blue'])
    for d in mids:
        if ncomp(A) <= before_c: break
        x, y = d['xy']; A2 = A.copy(); A2[y, x] = True
        if ncomp(A2) < ncomp(A): A = A2; d['action'] = 'snap (kept for line continuity)'
    # islands: a snapped px whose 8-connected component contains no untouched original px is a floating speck -> clear
    keep = A.copy()
    for d in dec:
        if d['action'].startswith('snap'): x, y = d['xy']; keep[y, x] = True
    lab, nl = label(keep, structure=np.ones((3, 3))); untouched = (I[..., 3] > 0) & ~m
    good = set(np.unique(lab[untouched & keep]).tolist())
    for d in dec:
        x, y = d['xy']
        if d['action'].startswith('snap') and lab[y, x] not in good: d['action'] = 'clear (isolated speck after unmixing)'
    O = I.copy()
    for d in dec:
        x, y = d['xy']
        if d['action'].startswith('snap'): O[y, x, :3] = d['P']; O[y, x, 3] = 255
        else: O[y, x] = 0
    Image.fromarray(O).save(f'{D}/{ang}/{e}_{n}.png')
    C = np.zeros_like(O); C[..., 2] = 255; C[..., 3] = 255; a = O[..., 3] > 0; C[a, :3] = O[a, :3]
    Image.fromarray(C).save(f'{D}/{ang}/{e}_{n}_chroma.png')
    after_c = ncomp(O[..., 3] > 0)
    s = {k: sum(d['action'].startswith(k) for d in dec) for k in ('clear', 'snap')}
    s.update({'chroma_before': int(m.sum()), 'components_before': int(before_c), 'components_after': int(after_c),
              'bg_t>=0.9': sum(d['t_blue'] >= 0.9 for d in dec), 'mid_0.5<t<0.9': len(mids), 'blend_t<=0.5': sum(d['t_blue'] <= 0.5 for d in dec),
              'kept_for_continuity': sum('continuity' in d['action'] for d in dec), 'speck_cleared': sum('speck' in d['action'] for d in dec), 'chroma_after': int(((O[..., 3] > 0) & isch(O[..., :3])).sum()), 'px': dec})
    log['files'][f'{ang}/{e}_{n}'] = s
    print(ang, e, n, {k: v for k, v in s.items() if k != 'px'})
json.dump(log, open(f'{OUT}/fix_diag_chroma.json', 'w'), indent=1)
