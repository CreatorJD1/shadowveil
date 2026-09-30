#!/usr/bin/env python3
"""Base Body skin.json builder (contract v1.4 section 8), tuned from rig/skin_tools/auto_skin.py.

    python3 body_tools/build_skin.py <view> [--out PATH] [--image base_body_skin.png] [--coarse 6] [--fine 2]
        [--sigma 7] [--sigma-hip 14] [--sigma-shoulder 9] [--wrist-rigid 8]

Same pixel-aligned conforming grid as auto_skin (rest exact), with these changes:
- Weights come from Gaussian-blurred bone-ownership maps (a smooth partition of unity across every parent/child seam),
  restricted per vertex to its owner and the owner's parent/children. So the blend follows the real seam (e.g. the
  panty leg line at the hip, the armpit), not just a disc around the pivot; the draft tore open there.
- Vertices are shared between parent/child cells wherever both bones carry weight, so seams stretch instead of tearing.
- Fine 2 px cells wherever a cell's weights are mixed.
- head: every head-owned vertex is 100% head (never deforms); head is never blended into torso.
- forearm end: every forearm vertex within --wrist-rigid px of the forearm's distal end (the wristPivot region and the
  hidden fill under the palm) is 100% forearm, so the palm (which overlaps the forearm by ~3 px) stays aligned.
"""
import json, os, sys, argparse
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ap = argparse.ArgumentParser()
ap.add_argument('view'); ap.add_argument('--out'); ap.add_argument('--image', default='base_body_skin.png')
ap.add_argument('--coarse', type=int, default=6); ap.add_argument('--fine', type=int, default=2)
ap.add_argument('--sigma', type=float, default=7.0); ap.add_argument('--sigma-hip', type=float, default=14.0)
ap.add_argument('--sigma-shoulder', type=float, default=9.0); ap.add_argument('--sigma-ankle', type=float, default=None)
ap.add_argument('--sigma-knee', type=float, default=None); ap.add_argument('--sigma-elbow', type=float, default=None)
ap.add_argument('--wrist-rigid', type=float, default=8.0)
ap.add_argument('--radius-shoulder', type=float, default=None)  # limit shoulder blending to this distance from the shoulder pivot (profile: arm lies over the torso)
ap.add_argument('--radius-hip', type=float, default=None)       # same for the hip seams
ap.add_argument('--hip-outer-lift', type=float, default=None)  # outer hip: pelvis pixels within this distance of the thigh count as thigh before blurring (panty corner follows the thigh)
ap.add_argument('--hip-outer-bg', type=float, default=None)  # ... and only within this distance of the background (the outline corner)
ap.add_argument('--hip-outer-x', type=float, default=100.0)  # ... only where |x - pelvis pivot x| exceeds this
ap.add_argument('--radius-ramp', type=float, default=12.0)
ap.add_argument('--sigma-hip-outer', type=float, default=None)   # wider hip blend toward the outer hip, where the seam meets the side outline
ap.add_argument('--hip-outer-ramp', type=float, nargs=2, default=[55.0, 95.0])  # |x - pelvis pivot x| ramp (px) from sigma-hip to sigma-hip-outer
A = ap.parse_args(); C, F = A.coarse, A.fine
vd = f'{ROOT}/views/{A.view}'
rig = json.load(open(f'{vd}/body/rig.json'))
img = np.array(Image.open(f'{vd}/{A.image}').convert('RGBA')); H, W = img.shape[:2]; opaque = img[..., 3] > 0
parts = rig['parts']; pm = rig.get('paramMap') or {}; inv_pm = {v: k for k, v in pm.items()}
bones = []
for p in parts:
    b = {'name': p['id'], 'parent': p.get('parent'), 'pivot': [p.get('pivotX', 0), p.get('pivotY', 0)],
         'param': p['param'] if 'param' in p else inv_pm.get(p['id'])}
    for k in ('maxRotDeg', 'minRotDeg', 'rotDir', 'degAtPlus1', 'degAtMinus1', 'maxDeg', 'wristPivot'):
        if p.get(k) is not None: b[k] = p[k]
    bones.append(b)
bi = {b['name']: i for i, b in enumerate(bones)}; NB = len(bones)
layer_of = {p['id']: p.get('layer', 220) for p in parts}
HEAD = bi.get('head')
# segmentation (topmost cut part), unclaimed pixels -> nearest claimed
owner = np.full((H, W), -1, np.int32); top = np.full((H, W), -1e9)
for p in parts:
    if not p.get('file') or not os.path.exists(f"{vd}/body/{p['file']}"): continue
    m = np.array(Image.open(f"{vd}/body/{p['file']}").convert('RGBA'))[..., 3] > 0
    sel = m & (layer_of[p['id']] > top); owner[sel] = bi[p['id']]; top[sel] = layer_of[p['id']]
_, (iy, ix) = ndi.distance_transform_edt(owner < 0, return_indices=True); owner = owner[iy, ix]
if HEAD is not None and 'torso' in bi: pass
# related bones (self, parent, children); head excluded from blending
rel = {i: {i} for i in range(NB)}
for b in bones:
    if b['parent'] in bi:
        c, p = bi[b['name']], bi[b['parent']]
        if HEAD in (c, p): continue
        rel[c].add(p); rel[p].add(c)
# per-seam sigma: seam of child bone c (with its parent)
def sig_for(name):
    for key, val in (('thigh', A.sigma_hip), ('upperArm', A.sigma_shoulder), ('foot', A.sigma_ankle), ('shin', A.sigma_knee), ('forearm', A.sigma_elbow)):
        if name.startswith(key) and val is not None: return val
    return A.sigma
# blurred ownership maps. For each child bone c: its indicator blurred with the seam's sigma, applied only against its
# parent. Build per-bone maps by blurring each indicator with the sigma of the seams it takes part in: we blur each bone
# indicator with a per-pixel sigma choice = sigma of the nearest seam (approximated by computing, for every bone, the
# blur with each distinct sigma and picking per pixel by nearest seam).
ind = [(owner == i).astype(np.float32) for i in range(NB)]
if A.hip_outer_lift and 'pelvis' in bi:
    pv = bi['pelvis']; midx_ = bones[pv]['pivot'][0]; outer = np.abs(np.arange(W) + 0.5 - midx_)[None, :] > A.hip_outer_x
    for b in bones:
        if b['name'].startswith('thigh') and b['parent'] == 'pelvis':
            t = bi[b['name']]
            if not (owner == t).any(): continue
            sel = (owner == pv) & (ndi.distance_transform_edt(owner != t) <= A.hip_outer_lift) & outer
            sel &= (np.arange(W) + 0.5 < midx_)[None, :] if b['pivot'][0] < midx_ else (np.arange(W) + 0.5 > midx_)[None, :]
            if A.hip_outer_bg: sel &= ndi.distance_transform_edt(opaque) <= A.hip_outer_bg
            ind[pv][sel] = 0; ind[t][sel] = 1
seams = []  # (child, parent, sigma, dist map to seam)
for b in bones:
    if b['parent'] in bi and bi[b['parent']] != HEAD and bi[b['name']] != HEAD:
        c, p = bi[b['name']], bi[b['parent']]
        mc, mp = owner == c, owner == p
        if not mc.any() or not mp.any(): continue
        dc = ndi.distance_transform_edt(~mc); dp = ndi.distance_transform_edt(~mp)
        seams.append((c, p, sig_for(b['name']), np.maximum(dc, dp)))
nearest = np.argmin(np.stack([s[3] for s in seams]), 0) if seams else None
sigmas = sorted({s[2] for s in seams})
blur = {sg: [ndi.gaussian_filter(ind[i], sg, mode='nearest') for i in range(NB)] for sg in sigmas}
sig_px = np.array([s[2] for s in seams], np.float32)[nearest]
Wm = np.zeros((NB, H, W), np.float32)
for sg in sigmas:
    sel = sig_px == sg
    for i in range(NB): Wm[i][sel] = blur[sg][i][sel]
if A.sigma_hip_outer:
    # hip seams only: lerp the hip-sigma maps toward a wider blur with a smoothstep in |x - midline| (both are partitions of unity)
    bo = [ndi.gaussian_filter(ind[i], A.sigma_hip_outer, mode='nearest') for i in range(NB)]
    midx = bones[bi['pelvis']]['pivot'][0]; xx_ = np.abs(np.arange(W) + 0.5 - midx)[None, :].repeat(H, 0)
    a0, a1 = A.hip_outer_ramp; u = np.clip((xx_ - a0) / (a1 - a0), 0, 1); u = (u * u * (3 - 2 * u)).astype(np.float32)
    hipsel = (sig_px == A.sigma_hip) & np.isin(nearest, [k for k, s_ in enumerate(seams) if bones[s_[0]]['name'].startswith('thigh')])
    for i in range(NB): Wm[i][hipsel] = ((1 - u) * blur[A.sigma_hip][i] + u * bo[i])[hipsel]
# optional seam radius: outside R (smoothstep ramp) of the child's pivot the weights fall back to the rigid owner, so a limb
# that merely lies across its parent (profile arm over the torso) is not glued to it along the whole contact
yy0, xx0 = np.mgrid[:H, :W]
for k_, (c_, p_, sg_, _) in enumerate(seams):
    nm = bones[c_]['name']; Rj = A.radius_shoulder if nm.startswith('upperArm') else A.radius_hip if nm.startswith('thigh') else None
    if Rj is None: continue
    px_, py_ = bones[c_]['pivot']; d_ = np.hypot(xx0 + .5 - px_, yy0 + .5 - py_)
    f = np.clip((Rj - d_) / A.radius_ramp, 0, 1); f = (f * f * (3 - 2 * f)).astype(np.float32)
    sel = (nearest == k_) & np.isin(owner, [c_, p_])
    for i in range(NB): Wm[i][sel] = (f * Wm[i] + (1 - f) * (owner == i))[sel]
# forearm distal rigid zone: forearm pixels within wrist_rigid px of the distal end (projection on the elbow->wrist axis)
rigid = np.zeros((NB, H, W), bool)
yy, xx = np.mgrid[:H, :W]
for b in bones:
    if b.get('wristPivot'):
        i = bi[b['name']]; J = np.array(b['pivot'], float); Wp = np.array([b['wristPivot']['x'], b['wristPivot']['y']])
        d = (Wp - J) / np.linalg.norm(Wp - J); s = (xx + .5 - J[0]) * d[0] + (yy + .5 - J[1]) * d[1]
        L = np.linalg.norm(Wp - J); rigid[i] = (owner == i) & (s >= L - A.wrist_rigid - 3)
def vweights(x, y, owners):
    x0, x1 = max(0, x - 1), min(W - 1, x); y0, y1 = max(0, y - 1), min(H - 1, y)
    if HEAD is not None and HEAD in owners: return {HEAD: 1.0}
    for o in owners:
        if rigid[o, y0:y1 + 1, x0:x1 + 1].any(): return {o: 1.0}
    allowed = set().union(*[rel[o] for o in owners]) - ({HEAD} if HEAD is not None else set())
    w = {k: float(Wm[k, y0:y1 + 1, x0:x1 + 1].mean()) for k in allowed}
    w = {k: v for k, v in w.items() if v > 2e-3}
    if not w: return {owners[0]: 1.0}
    return w
# ---- cells ----
ncx, ncy = (W + C - 1) // C, (H + C - 1) // C
def occ(x0, y0, s): return opaque[y0:min(y0 + s, H), x0:min(x0 + s, W)].any()
def cell_owner(x0, y0, s):
    o = owner[y0:min(y0 + s, H), x0:min(x0 + s, W)]; m = opaque[y0:min(y0 + s, H), x0:min(x0 + s, W)]
    v = o[m] if m.any() else o.ravel()
    if HEAD is not None and (v == HEAD).any(): return HEAD   # any head pixel -> head cell (head/chin never ride another bone)
    return int(np.bincount(v).argmax())
maxw = Wm.max(0)
def mixed(x0, y0, s):
    ya, yb, xa, xb = max(0, y0 - 1), min(H, y0 + s + 1), max(0, x0 - 1), min(W, x0 + s + 1)
    return (maxw[ya:yb, xa:xb] < 0.998).any() or len(np.unique(owner[ya:yb, xa:xb])) > 1
cells = []
for cy in range(ncy):
    for cx in range(ncx):
        x0, y0 = cx * C, cy * C
        if not occ(x0, y0, C): continue
        if mixed(x0, y0, C):
            for sy in range(0, C, F):
                for sx in range(0, C, F):
                    if occ(x0 + sx, y0 + sy, F): cells.append((x0 + sx, y0 + sy, F, cell_owner(x0 + sx, y0 + sy, F), False))
        else: cells.append((x0, y0, C, cell_owner(x0, y0, C), True))
fine_pts = set()
for (x0, y0, s, o, fan) in cells:
    if not fan:
        for pt in ((x0, y0), (x0 + s, y0), (x0 + s, y0 + s), (x0, y0 + s)): fine_pts.add(pt)
def boundary(x0, y0, s, fan):
    if not fan: return [(x0, y0), (x0 + s, y0), (x0 + s, y0 + s), (x0, y0 + s)]
    pts = []
    for (ax, ay, bx, by_) in ((x0, y0, x0 + s, y0), (x0 + s, y0, x0 + s, y0 + s), (x0 + s, y0 + s, x0, y0 + s), (x0, y0 + s, x0, y0)):
        n = s // F
        for k in range(n):
            px, py = ax + (bx - ax) * k // n, ay + (by_ - ay) * k // n
            if k == 0 or (px, py) in fine_pts: pts.append((px, py))
    return pts
cell_bound = [boundary(*c[:3], c[4]) for c in cells]
point_cells = {}
for ci, bnd in enumerate(cell_bound):
    for pt in bnd: point_cells.setdefault(pt, []).append(ci)
def share_zone(a, b, x, y):
    if b not in rel[a] or a == b: return a == b
    xa, ya = min(W - 1, max(0, x)), min(H - 1, max(0, y))
    xs, ys = slice(max(0, xa - 1), xa + 1), slice(max(0, ya - 1), ya + 1)
    return Wm[a, ys, xs].max() > 2e-3 and Wm[b, ys, xs].max() > 2e-3
def classes_at(pt):
    owners = sorted({cells[c][3] for c in point_cells[pt]}); par = {o: o for o in owners}
    def f(o):
        while par[o] != o: o = par[o]
        return o
    for i in range(len(owners)):
        for k in range(i + 1, len(owners)):
            if share_zone(owners[i], owners[k], *pt): par[f(owners[i])] = f(owners[k])
    return {o: f(o) for o in owners}
cls_cache, vindex, verts, vown = {}, {}, [], []
def vid(pt, o):
    if pt not in cls_cache: cls_cache[pt] = classes_at(pt)
    cl = cls_cache[pt]; key = (pt[0], pt[1], cl[o])
    if key not in vindex:
        vindex[key] = len(verts); verts.append([pt[0], pt[1]]); vown.append(sorted({k for k, r in cl.items() if r == cl[o]}, key=lambda k: k != o))
    return vindex[key]
MIDX = bones[bi['pelvis']]['pivot'][0] if 'pelvis' in bi else W / 2
tris = []
for ci, (x0, y0, s, o, fan) in enumerate(cells):
    lay = layer_of[bones[o]['name']]; bnd = [vid(pt, o) for pt in cell_bound[ci]]
    if fan:
        key = (x0 + s // 2, y0 + s // 2, ('c', ci)); vindex[key] = len(verts); verts.append([x0 + s // 2, y0 + s // 2]); vown.append([o]); c0 = vindex[key]
        for k in range(len(bnd)): tris.append([c0, bnd[k], bnd[(k + 1) % len(bnd)], lay])
    else:
        a, b, c, d = bnd   # corners TL, TR, BR, BL; diagonal mirrored about the body midline so L/R seams sample alike
        if x0 + s / 2 < MIDX: tris += [[a, b, d, lay], [b, c, d, lay]]
        else: tris += [[a, b, c, lay], [a, c, d, lay]]
weights = []
for (x, y), ow in zip(verts, vown):
    w = vweights(x, y, ow)
    top4 = sorted(w.items(), key=lambda kv: -kv[1])[:4]; tot = sum(v for _, v in top4)
    wl = [[int(k), round(v / tot, 5)] for k, v in top4]; s = sum(v for _, v in wl); wl[0][1] = round(wl[0][1] + (1 - s), 5)
    weights.append(wl)
out = {'contract': 'v1.4', 'owner': 'Base Body', 'view': A.view, 'image': A.image, 'size': [W, H], 'layer': 220,
       'bones': bones, 'headBone': 'head' if 'head' in bi else 'torso',
       'vertices': verts, 'triangles': tris, 'weights': weights,
       'generator': {'tool': 'body_tools/build_skin.py (from rig/skin_tools/auto_skin.py)', 'coarse': C, 'fine': F,
                     'sigma': A.sigma, 'sigmaHip': A.sigma_hip, 'sigmaShoulder': A.sigma_shoulder, 'sigmaAnkle': A.sigma_ankle,
                     'sigmaKnee': A.sigma_knee, 'sigmaHipOuter': A.sigma_hip_outer, 'hipOuterRamp': A.hip_outer_ramp, 'radiusShoulder': A.radius_shoulder, 'hipOuterLift': A.hip_outer_lift, 'hipOuterX': A.hip_outer_x, 'hipOuterBg': A.hip_outer_bg, 'radiusHip': A.radius_hip, 'sigmaElbow': A.sigma_elbow, 'wristRigidPx': A.wrist_rigid, 'mirroredDiagonalsLeftOfX': MIDX,
                     'notes': 'weights = blurred ownership maps across parent/child seams; head 100% head; forearm distal end 100% forearm'}}
dst = A.out or f'{ROOT}/body_tools/work/{A.view}_skin_candidate.json'
json.dump(out, open(dst + '.tmp', 'w'), separators=(',', ':')); os.replace(dst + '.tmp', dst)
print(json.dumps({'out': dst, 'vertices': len(verts), 'triangles': len(tris), 'cells': len(cells), 'bytes': os.path.getsize(dst)}))
