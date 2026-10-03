#!/usr/bin/env python3
"""Pass 2: navy fringe in the staged diagonal far-eye files (after fix_diag_chroma.py).
Targets: px with a>0 and b - max(r,g) > 30 in 045 EyeR_{lid_0,lash}, 315 EyeL_{lid_0,lash}.
Same unmix rule as pass 1 (local key blue B from the frame; palette = qa_gates palette for <ang>/eyes, here restricted to
tones with b - max(r,g) <= 30 so no snapped px is itself fringe):
  t >= 0.5 -> alpha 0 ; t <= 0.5 -> exact palette tone P*, alpha 255.
  The 11 pass-1 palette-tone edge px are kept opaque (re-toned to a <=30 tone if they are targets), never cleared.
Continuity guard (vs the pass-1 state): 8-conn components of the file itself AND of lid_k U lash for k=0..7 must not
increase; cleared px are re-added (as P*) lowest-t first until no metric is worse. Isolated snapped specks are cleared.
Backup of the pass-1 state: eyes/staged/diagonals/backups_chroma_fix/pass2/<ang>/. _chroma.png regenerated as before."""
import sys, os, json, shutil, numpy as np
sys.dont_write_bytecode = True
R = '/workspace/shadowveil'; sys.path.insert(0, f'{R}/rig'); sys.argv = sys.argv[:1]
import qa_gates as Q
from PIL import Image
from scipy.ndimage import label
D = f'{R}/eyes/staged/diagonals'; BK2 = f'{D}/backups_chroma_fix/pass2'; OUT = f'{R}/eyes/qa/qa_gates'
FR = {'045': 'f033', '315': 'f191'}; EYES = [('045', 'EyeR'), ('315', 'EyeL')]
P1 = json.load(open(f'{OUT}/fix_diag_chroma.json'))['files']
ST = np.ones((3, 3)); nc = lambda a: label(a, structure=ST)[1]
fringe = lambda I: (I[..., 3] > 0) & (I[..., 2].astype(int) - np.maximum(I[..., 0], I[..., 1]).astype(int) > 30)
log = {'doc': __doc__, 'files': {}}
for ang, e in EYES:
    os.makedirs(f'{BK2}/{ang}', exist_ok=True)
    for n in ('lid_0', 'lash'):
        for suf in ('', '_chroma'):
            dst = f'{BK2}/{ang}/{e}_{n}{suf}.png'
            if not os.path.exists(dst): shutil.copy2(f'{D}/{ang}/{e}_{n}{suf}.png', dst)   # keep the pass-1 state if rerun
    fr = Q.rgba(f'{R}/reference/apose_turn/frames/{FR[ang]}.png')[..., :3].astype(float)
    keymask = (fr[..., 2] > 230) & (fr[..., 0] < 20) & (fr[..., 1] < 20)
    pal = Q.unpack(Q.palette(Q.palette_sources(ang, 'eyes', 'x.png'))).astype(float); pal = pal[pal[:, 2] - np.maximum(pal[:, 0], pal[:, 1]) <= 30]
    lids = {k: Q.rgba(f'{D}/{ang}/{e}_lid_{k}.png')[..., 3] > 0 for k in range(1, 8)}
    cur = {n: Q.rgba(f'{BK2}/{ang}/{e}_{n}.png').copy() for n in ('lid_0', 'lash')}
    def metrics(A0, Al):  # A0 = lid_0 alpha mask, Al = lash alpha mask
        return [nc(A0), nc(Al)] + [nc((A0 if k == 0 else lids[k]) | Al) for k in range(8)]
    base = metrics(cur['lid_0'][..., 3] > 0, cur['lash'][..., 3] > 0)
    dec = {}; keep11 = {}
    for n in ('lid_0', 'lash'):
        I = cur[n]; m = fringe(I); ys, xs = np.nonzero(m)
        keep11[n] = {tuple(p['xy']) for p in P1[f'{ang}/{e}_{n}']['px'] if p['action'].startswith('snap')}
        L = []
        for y, x in zip(ys, xs):
            y0, x0 = max(0, y - 6), max(0, x - 6); km = keymask[y0:y + 7, x0:x + 7]
            B = fr[y0:y + 7, x0:x + 7][km].mean(0) if km.any() else np.array([0., 0., 255.])
            p = I[y, x, :3].astype(float); d = B - pal; t = np.clip(((p - pal) * d).sum(1) / ((d * d).sum(1) + 1e-9), 0, 1)
            r = np.linalg.norm(p - (pal + t[:, None] * d), axis=1); j = int(r.argmin())
            act = 'snap' if t[j] <= 0.5 else 'clear'
            if (int(x), int(y)) in keep11[n]: act = 'snap (pass-1 edge px kept, re-toned)'
            L.append({'xy': [int(x), int(y)], 'rgb': I[y, x, :3].tolist(), 't_blue': round(float(t[j]), 3), 'P': pal[j].astype(int).tolist(), 'resid': round(float(r[j]), 1), 'action': act})
        dec[n] = L
    A = {n: cur[n][..., 3] > 0 for n in cur}
    for n in dec:
        for d in dec[n]:
            if d['action'] == 'clear': A[n][d['xy'][1], d['xy'][0]] = False
    def worse(): return any(a > b for a, b in zip(metrics(A['lid_0'], A['lash']), base))
    cand = sorted([(d['t_blue'], n, d) for n in dec for d in dec[n] if d['action'] == 'clear'], key=lambda z: z[0])
    while worse():
        tot = sum(max(0, a - b) for a, b in zip(metrics(A['lid_0'], A['lash']), base)); best = None
        for t, n, d in cand:
            if d['action'] != 'clear': continue
            x, y = d['xy']; A[n][y, x] = True
            t2 = sum(max(0, a - b) for a, b in zip(metrics(A['lid_0'], A['lash']), base)); A[n][y, x] = False
            if t2 < tot: best = (n, d); break
        if best is None:  # no single px helps: add the lowest-t cleared px touching any kept art, then retry
            for t, n, d in cand:
                x, y = d['xy']
                if d['action'] == 'clear' and A[n][max(0, y - 1):y + 2, max(0, x - 1):x + 2].any(): best = (n, d); break
        if best is None: break
        n, d = best; A[n][d['xy'][1], d['xy'][0]] = True; d['action'] = 'snap (kept for line continuity)'
    # specks: snapped px whose component has no untouched px
    for n in dec:
        tgt = fringe(cur[n]); lab, _ = label(A[n], structure=ST); good = set(np.unique(lab[A[n] & ~tgt]).tolist())
        for d in dec[n]:
            x, y = d['xy']
            if d['action'] == 'snap' and lab[y, x] not in good:
                A[n][y, x] = False
                if worse(): A[n][y, x] = True
                else: d['action'] = 'clear (isolated speck)'
    for n in dec:
        O = cur[n].copy()
        for d in dec[n]:
            x, y = d['xy']
            if d['action'].startswith('snap'): O[y, x, :3] = d['P']; O[y, x, 3] = 255
            else: O[y, x] = 0
        Image.fromarray(O).save(f'{D}/{ang}/{e}_{n}.png')
        C = np.zeros_like(O); C[..., 2] = 255; C[..., 3] = 255; a = O[..., 3] > 0; C[a, :3] = O[a, :3]; Image.fromarray(C).save(f'{D}/{ang}/{e}_{n}_chroma.png')
        cur[n] = O
    after = metrics(cur['lid_0'][..., 3] > 0, cur['lash'][..., 3] > 0)
    for n in dec:
        L = dec[n]; s = {'fringe_before': len(L), 'cleared': sum(d['action'].startswith('clear') for d in L), 'snapped': sum(d['action'].startswith('snap') for d in L),
             'kept_for_continuity': sum('continuity' in d['action'] for d in L), 'pass1_edge_px_retoned': sum('re-toned' in d['action'] for d in L),
             'specks_cleared': sum('speck' in d['action'] for d in L), 'fringe_after': int(fringe(cur[n]).sum()),
             'chroma_after': int(((cur[n][..., 3] > 0) & (cur[n][..., 2].astype(int) > np.maximum(cur[n][..., 0], cur[n][..., 1]).astype(int) + 60) & (cur[n][..., 2] > 120)).sum()), 'px': L}
        log['files'][f'{ang}/{e}_{n}'] = s; print(ang, e, n, {k: v for k, v in s.items() if k != 'px'})
    log['files'][f'{ang}/{e}_components'] = {'order': 'lid_0, lash, lid_k|lash k0..7', 'before': base, 'after': after}
    print(ang, e, 'components before', base, 'after', after)
json.dump(log, open(f'{OUT}/fix_diag_fringe_pass2.json', 'w'), indent=1)
