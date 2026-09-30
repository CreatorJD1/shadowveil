#!/usr/bin/env python3
"""Draft skin.json generator for Base Body (contract v1.4, section 4 "Body skin").

    python3 rig/skin_tools/auto_skin.py <view> [--out PATH] [--coarse 6] [--fine 2] [--falloff 14] [--image base_body.png]

Reads (never writes) views/<view>/base_body.png (or --image, relative to views/<view>/), its alpha, and the joint
pivots/limits in views/<view>/body/rig.json. The cut part PNGs in views/<view>/body/ are used only as a segmentation
(which bone owns which pixel: topmost part layer wins). Writes a DRAFT to rig/skin_tools/drafts/<view>_skin.json.

Mesh: pixel-aligned grid over every cell containing an opaque pixel. Coarse cells (default 6 px) are fanned from
their centre; cells near driven joints are split into fine 2 px cells. Coarse cells include every fine vertex lying
on their edges, so the mesh is conforming (no T-junction cracks). All rest vertices are on integer pixel corners,
so at identity every pixel centre lies strictly inside exactly one cell (texel-exact rest).
Vertices are shared across cells only when the owning bones are the same, or are a parent/child pair and the vertex
lies in that joint's blend zone; elsewhere (e.g. an arm resting against the torso) the mesh is split so the limb
can separate cleanly.
Weights: rigid to the owning bone, blended across each driven joint with a smoothstep over +-falloff px measured
along the child bone's axis; normalised, at most 4 influences. Each cell carries the layer of its owning part so
profile far limbs keep their draw order (triangle "layer" groups).
"""
import json, os, sys, argparse
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ap = argparse.ArgumentParser()
ap.add_argument('view'); ap.add_argument('--out'); ap.add_argument('--image', default='base_body.png')
ap.add_argument('--coarse', type=int, default=6); ap.add_argument('--fine', type=int, default=2)
ap.add_argument('--falloff', type=float, default=14.0)
A = ap.parse_args()
C, F, R = A.coarse, A.fine, A.falloff
assert C % F == 0
vd = f'{ROOT}/views/{A.view}'
rig = json.load(open(f'{vd}/body/rig.json'))
img = np.array(Image.open(f'{vd}/{A.image}').convert('RGBA'))
H, W = img.shape[:2]
opaque = img[..., 3] > 0

# ---- bones from body/rig.json ----
parts = rig['parts']
pm = rig.get('paramMap') or {}
inv_pm = {v: k for k, v in pm.items()}
bones = []
for p in parts:
    b = {'name': p['id'], 'parent': p.get('parent'), 'pivot': [p.get('pivotX', 0), p.get('pivotY', 0)],
         'param': p['param'] if 'param' in p else inv_pm.get(p['id'])}
    for k in ('maxRotDeg', 'minRotDeg', 'rotDir', 'degAtPlus1', 'degAtMinus1', 'maxDeg', 'wristPivot'):
        if p.get(k) is not None: b[k] = p[k]
    bones.append(b)
bi = {b['name']: i for i, b in enumerate(bones)}
layer_of = {p['id']: p.get('layer', 220) for p in parts}

# ---- segmentation: topmost cut part covering each pixel ----
owner = np.full((H, W), -1, np.int32); top = np.full((H, W), -1e9)
for p in parts:
    if not p.get('file') or not os.path.exists(f"{vd}/body/{p['file']}"): continue
    m = np.array(Image.open(f"{vd}/body/{p['file']}").convert('RGBA'))[..., 3] > 0
    sel = m & (layer_of[p['id']] > top)
    owner[sel] = bi[p['id']]; top[sel] = layer_of[p['id']]
if (owner >= 0).any():
    _, (iy, ix) = ndi.distance_transform_edt(owner < 0, return_indices=True)
    owner = owner[iy, ix]          # pixels no part claims -> nearest claimed pixel's bone
else:
    owner[:] = bi.get('torso', 0)

# ---- joints (driven child bones) ----
children = {}
for b in bones:
    if b['parent'] in bi: children.setdefault(b['parent'], []).append(b['name'])
def bone_end(name):
    ch = [c for c in children.get(name, []) if bones[bi[c]]['pivot'] != bones[bi[name]]['pivot']]
    if ch:
        return np.mean([bones[bi[c]]['pivot'] for c in ch], 0)
    ys, xs = np.where(owner == bi[name])
    return np.array([xs.mean(), ys.mean()]) if len(xs) else np.array(bones[bi[name]]['pivot']) + [0, 1]
joints = []
for b in bones:
    if b['parent'] in bi and b['param']:
        J = np.array(b['pivot'], float); d = bone_end(b['name']) - J; n = np.linalg.norm(d)
        joints.append({'child': bi[b['name']], 'parent': bi[b['parent']], 'J': J, 'd': d / n if n > 1e-6 else np.array([0, 1.0])})

def near_joint(x, y, rad):
    return any(np.hypot(x - j['J'][0], y - j['J'][1]) < rad for j in joints)

# ---- cells ----
ncx, ncy = (W + C - 1) // C, (H + C - 1) // C
def occ(x0, y0, s):
    return opaque[y0:min(y0 + s, H), x0:min(x0 + s, W)].any()
def cell_owner(x0, y0, s):
    o = owner[y0:min(y0 + s, H), x0:min(x0 + s, W)]; m = opaque[y0:min(y0 + s, H), x0:min(x0 + s, W)]
    v = o[m] if m.any() else o.ravel()
    return int(np.bincount(v).argmax())
cells = []   # (x0, y0, size, ownerBone, fanned)
fine_rad = 2.5 * R + C
for cy in range(ncy):
    for cx in range(ncx):
        x0, y0 = cx * C, cy * C
        if not occ(x0, y0, C): continue
        if near_joint(x0 + C / 2, y0 + C / 2, fine_rad):
            for sy in range(0, C, F):
                for sx in range(0, C, F):
                    if occ(x0 + sx, y0 + sy, F): cells.append((x0 + sx, y0 + sy, F, cell_owner(x0 + sx, y0 + sy, F), False))
        else:
            cells.append((x0, y0, C, cell_owner(x0, y0, C), True))

# fine grid points present (for conforming coarse fans)
fine_pts = set()
for (x0, y0, s, o, fan) in cells:
    if not fan:
        for (px, py) in ((x0, y0), (x0 + s, y0), (x0 + s, y0 + s), (x0, y0 + s)): fine_pts.add((px, py))

def joint_pair_zone(a, b, x, y):
    for j in joints:
        if {a, b} == {j['child'], j['parent']} and np.hypot(x - j['J'][0], y - j['J'][1]) < 2.5 * R: return True
    return False

# vertex identity: (x, y, class) where cells whose owners are connected at that point share the vertex
verts, vindex = [], {}
point_cells = {}
def boundary(x0, y0, s, fan):
    if not fan: return [(x0, y0), (x0 + s, y0), (x0 + s, y0 + s), (x0, y0 + s)]
    pts = []
    for (ax, ay, bx, by) in ((x0, y0, x0 + s, y0), (x0 + s, y0, x0 + s, y0 + s), (x0 + s, y0 + s, x0, y0 + s), (x0, y0 + s, x0, y0)):
        n = s // F
        for k in range(n):
            px, py = ax + (bx - ax) * k // n, ay + (by - ay) * k // n
            if k == 0 or (px, py) in fine_pts: pts.append((px, py))
    return pts
cell_bound = [boundary(*c[:3], c[4]) for c in cells]
for ci, bnd in enumerate(cell_bound):
    for pt in bnd: point_cells.setdefault(pt, []).append(ci)
# union owners at each point
def classes_at(pt):
    cs = point_cells[pt]; owners = sorted({cells[c][3] for c in cs}); parent = {o: o for o in owners}
    def f(o):
        while parent[o] != o: o = parent[o]
        return o
    for i in range(len(owners)):
        for k in range(i + 1, len(owners)):
            if joint_pair_zone(owners[i], owners[k], *pt): parent[f(owners[i])] = f(owners[k])
    return {o: f(o) for o in owners}
cls_cache = {}
def vid(pt, o):
    if pt not in cls_cache: cls_cache[pt] = classes_at(pt)
    key = (pt[0], pt[1], cls_cache[pt][o])
    if key not in vindex: vindex[key] = len(verts); verts.append([pt[0], pt[1], o])
    return vindex[key]
tris, tlayers = [], []
for ci, (x0, y0, s, o, fan) in enumerate(cells):
    lay = layer_of[bones[o]['name']]
    bnd = [vid(pt, o) for pt in cell_bound[ci]]
    if fan:
        key = (x0 + s // 2, y0 + s // 2, ('c', ci)); vindex[key] = len(verts); verts.append([x0 + s // 2, y0 + s // 2, o]); c0 = vindex[key]
        for k in range(len(bnd)): tris.append([c0, bnd[k], bnd[(k + 1) % len(bnd)]]); tlayers.append(lay)
    else:
        a, b, c, d = bnd; tris += [[a, b, c], [a, c, d]]; tlayers += [lay, lay]

# ---- weights ----
def smooth(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)
weights = []
for (x, y, o) in verts:
    w = {o: 1.0}
    best = None
    for j in joints:
        if o not in (j['child'], j['parent']): continue
        dist = np.hypot(x - j['J'][0], y - j['J'][1])
        if dist < 2.5 * R and (best is None or dist < best[0]): best = (dist, j)
    if best:
        j = best[1]; s = float(np.dot(np.array([x, y]) - j['J'], j['d'])) / R
        wc = smooth((s + 1) / 2); w = {j['child']: wc, j['parent']: 1 - wc}
    w = {k: v for k, v in w.items() if v > 1e-4}
    top4 = sorted(w.items(), key=lambda kv: -kv[1])[:4]; tot = sum(v for _, v in top4)
    weights.append([[int(k), round(v / tot, 5)] for k, v in top4])
# exact sums after rounding
for wl in weights:
    s = sum(v for _, v in wl); wl[0][1] = round(wl[0][1] + (1 - s), 5)

out = {'contract': 'v1.4', 'owner': 'Base Body (DRAFT generated by rig/skin_tools/auto_skin.py; Base Body tunes and owns it)',
       'view': A.view, 'image': A.image, 'size': [W, H], 'layer': 220,
       'bones': bones, 'headBone': 'head' if 'head' in bi else 'torso',
       'vertices': [[v[0], v[1]] for v in verts], 'triangles': [t + [l] for t, l in zip(tris, tlayers)], 'weights': weights,
       'generator': {'coarse': C, 'fine': F, 'falloffPx': R, 'joints': [bones[j['child']]['name'] for j in joints]}}
dst = A.out or f'{ROOT}/rig/skin_tools/drafts/{A.view}_skin.json'
assert '/views/' not in os.path.abspath(dst), 'drafts must not be written into views/'
os.makedirs(os.path.dirname(dst), exist_ok=True)
json.dump(out, open(dst, 'w'), separators=(',', ':'))
print(json.dumps({'out': dst, 'vertices': len(verts), 'triangles': len(tris), 'cells': len(cells), 'joints': out['generator']['joints'],
                  'layers': sorted(set(tlayers)), 'bytes': os.path.getsize(dst)}))
