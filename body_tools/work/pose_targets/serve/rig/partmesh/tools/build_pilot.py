#!/usr/bin/env python3
"""Build the partmesh v0.1 pilot meshes (read-only on views/; writes rig/partmesh/staged/*.json + manifest.json).
usage: python3 rig/partmesh/tools/build_pilot.py [--blend part=px ...] [--step 2]
Model (FORMAT.md): each drawing gets a grid mesh over its own authored PNG. Each vertex carries two bend weights:
  w = share of the part's own joint (root joint: parent -> part), u = share of the child's joint (tip joint: part -> child).
  Posed vertex = M_parent * D_self(w) * D_child(u) * x, where D(t) = T(t*d) * rotAt(c, t*a) is the fraction t of the
  relative joint transform (angle a about centre c, plus offset d). Both sides of a joint use the same centre, axis and blend,
  so the parent's distal end and the child's root deform identically where they overlap (no seam, no gap).
"""
import json, os, sys, hashlib, numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT = '/workspace/shadowveil'; OUT = os.environ.get('PARTMESH_OUT', f'{ROOT}/rig/partmesh/staged')  # candidates can be built elsewhere
args = sys.argv[1:]; STEP = 2
BL = {}; OFF = {}; WP = {}   # WP: per-drawing weight patches  --wpatch=<part>/<key>:x0,y0,x1,y1:w[:feather]
for i, a in enumerate(args):
    if a == '--step': STEP = int(args[i + 1])
    if a == '--blend': pass
    if a.startswith('--wpatch='):
        dk, box, wv, *fe = a[len('--wpatch='):].split(':'); WP.setdefault(dk, []).append(([float(x) for x in box.split(',')], float(wv), float(fe[0]) if fe else 2.0))
    if '=' in a and not a.startswith('--'):
        k, x = a.split('=')
        if k.endswith('@c'): OFF[k[:-2]] = float(x)   # blend centre offset along the joint axis (px, + = distal/child side)
        else: BL[k] = float(x)
PILOTS = [
    dict(file='apose_hair_strand_03.json', view='apose', system='hair', chain=['strand_03', 'strand_03_tip'],
         blend={'strand_03': 6.0, 'strand_03_tip': 10.0}),
    dict(file='tpose_hands_R_Middle.json', view='tpose', system='hands', chain=['R_Middle1', 'R_Middle2', 'R_Middle3'],
         blend={'R_Middle1': 6.0, 'R_Middle2': 6.0, 'R_Middle3': 4.0}),
]
def alpha(p): return np.array(Image.open(p).convert('RGBA'))[..., 3]
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
def smooth(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
def grid(a, step):
    m = ndi.binary_dilation(a > 0, iterations=2); ys, xs = np.nonzero(m)
    x0, y0 = (xs.min() // step) * step, (ys.min() // step) * step; x1, y1 = xs.max() + 1, ys.max() + 1
    nx, ny = int(np.ceil((x1 - x0) / step)), int(np.ceil((y1 - y0) / step))
    vid = {}; V = []; T = []
    def v(i, j):
        k = (i, j)
        if k not in vid: vid[k] = len(V); V.append([float(x0 + i * step), float(y0 + j * step)])
        return vid[k]
    for j in range(ny):
        for i in range(nx):
            cx0, cy0 = x0 + i * step, y0 + j * step
            if not m[cy0:cy0 + step, cx0:cx0 + step].any(): continue
            a_, b_, c_, d_ = v(i, j), v(i + 1, j), v(i + 1, j + 1), v(i, j + 1)
            T += [[a_, b_, c_], [a_, c_, d_]]
    return np.array(V), T
def axis_of(a, piv):
    ys, xs = np.nonzero(a > 0); w = a[ys, xs].astype(float)
    c = np.array([(xs + .5) @ w / w.sum(), (ys + .5) @ w / w.sum()]); d = c - np.array(piv); return d / np.linalg.norm(d)
manifest = []
for P in PILOTS:
    vd = f"{ROOT}/views/{P['view']}/{P['system']}"; rj = json.load(open(f'{vd}/rig.json'))
    parts = rj if isinstance(rj, list) else rj['parts']; by = {p['id']: p for p in parts}
    blend = {k: BL.get(k, x) for k, x in P['blend'].items()}
    # joints: one per chain part (root joint parent->part); axis = from the part's base pivot to its base drawing's centroid
    J = {}
    for pid in P['chain']:
        p = by[pid]; piv = [p['pivotX'], p['pivotY']]; a = alpha(f"{vd}/{p['file']}")
        J[pid] = dict(parent=p.get('parent'), centre=piv, axis=axis_of(a, piv).round(5).tolist(), blend=blend[pid], blendOffset=OFF.get(pid, 0.0))
    out = dict(contract='partmesh v0.1', owner='Coder (pilot)', view=P['view'], system=P['system'], status='staged pilot, read by rig/index.html only with ?partmesh=1',
               generator='rig/partmesh/tools/build_pilot.py step=%d' % STEP, deform='angle', joints=J, parts=[])
    for k, pid in enumerate(P['chain']):
        p = by[pid]; child = P['chain'][k + 1] if k + 1 < len(P['chain']) else None
        ds = [('part', p['file'], None)] + [(f'f{i}', (e if isinstance(e, str) else e['file']), (None if isinstance(e, str) else e.get('pivot'))) for i, e in enumerate(p.get('frames') or [])]
        D = {}
        for key, fn, fpiv in ds:
            path = f'{vd}/{fn}'; a = alpha(path); V, T = grid(a, STEP)
            piv = fpiv or [p['pivotX'], p['pivotY']]; jr = J[pid]
            n = np.array(jr['axis']); s = (V - np.array(piv)) @ n; w = smooth((s - jr['blendOffset'] + jr['blend']) / (2 * jr['blend'])) if jr['blend'] > 0 else np.ones(len(V))  # blend 0 = rigid root joint
            for (bx, wv, fe) in WP.get(f'{pid}/{key}', []):   # per-drawing weights (FORMAT 2.3: owners/builder may supply any w); feathered box, w pulled toward wv
                dx_ = np.maximum(0, np.maximum(bx[0] - V[:, 0], V[:, 0] - (bx[2] + 1))); dy_ = np.maximum(0, np.maximum(bx[1] - V[:, 1], V[:, 1] - (bx[3] + 1)))
                k_ = smooth(1 - np.hypot(dx_, dy_) / fe) if fe > 0 else (np.hypot(dx_, dy_) == 0).astype(float); w = w + (wv - w) * k_
            if child:
                jc = J[child]; nc = np.array(jc['axis']); sc = (V - np.array(jc['centre'])) @ nc; u = smooth((sc - jc['blendOffset'] + jc['blend']) / (2 * jc['blend'])) if jc['blend'] > 0 else np.zeros(len(V))
            else: u = np.zeros(len(V))
            D[key] = dict(image=os.path.relpath(path, ROOT), sha256=sha(path), pivot=[float(piv[0]), float(piv[1])],
                          spine=[(np.array(piv) - n * jr['blend']).round(2).tolist(), [float(piv[0]), float(piv[1])],
                                 (np.array(J[child]['centre']) if child else np.array(piv) + n * 20).round(2).tolist()],
                          mesh=dict(vertices=V.round(2).tolist(), triangles=T, weights=np.c_[w, u].round(5).tolist()), **({'weightPatch': [dict(box=b_, w=w_, feather=f_) for b_, w_, f_ in WP[f'{pid}/{key}']]} if f'{pid}/{key}' in WP else {}))
        out['parts'].append(dict(id=pid, parent=p.get('parent'), child=child, layer=p.get('layer'), joint=pid, childJoint=child, drawings=D))
    os.makedirs(OUT, exist_ok=True); json.dump(out, open(f"{OUT}/{P['file']}", 'w'), separators=(',', ':'))
    manifest.append(dict(file=P['file'], view=P['view'], system=P['system'], parts=P['chain']))
    print(P['file'], 'offsets', {k: J[k]['blendOffset'] for k in J}, {pp['id']: {k: len(d['mesh']['vertices']) for k, d in pp['drawings'].items()} for pp in out['parts']}, 'blend', blend)
json.dump(dict(contract='partmesh v0.1', files=manifest), open(f'{OUT}/manifest.json', 'w'), indent=1)
