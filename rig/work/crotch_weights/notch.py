#!/usr/bin/env python3
"""Crotch-notch measure: rasterize the posed body skin (+ underlay) around the crotch, count px opaque at rest that become
uncovered (holes) at each bend extreme. Writes PNG crops + JSON into rig/work/crotch_weights/. Read-only otherwise.
  python3 notch.py <view> <label>=<skin.json> [...]"""
import sys, json, os
import numpy as np, cv2
from PIL import Image
sys.path.insert(0, '/workspace/shadowveil/rig'); import qa_gates as Q
ROOT = '/workspace/shadowveil'; OUT = os.path.dirname(os.path.abspath(__file__))
view = sys.argv[1]; cands = [a.split('=', 1) for a in sys.argv[2:]]
X0, Y0, X1, Y1 = 560, 760, 800, 1000
def tex(name):
    for p in (f'{OUT}/{name}', f'{ROOT}/views/{view}/{name}', f'{ROOT}/views/{view}/body/{name}'):
        if os.path.exists(p): return np.asarray(Image.open(p).convert('RGBA')).astype(np.float32)
def render(sk, ang):
    bones = sk['bones']; nb = len(bones); mats = Q.bone_mats(bones, ang)
    out = np.zeros((Y1 - Y0, X1 - X0, 4), np.float32)
    layers = []
    for m, lay in ((sk.get('underlay'), 'u'), (sk, 's')):
        if not isinstance(m, dict) or not m.get('weights'): continue
        T = tex(m['image']); V = np.asarray(m['vertices'], float); W = Q.dense_w(m['weights'], nb); Pp = Q.lbs_fast(V, W, mats)
        tri = np.asarray(m['triangles']); order = np.argsort(tri[:, 3], kind='stable') if tri.shape[1] > 3 else np.arange(len(tri))
        layers.append(((sk.get('underlay') or {}).get('layer', 0) if lay == 'u' else sk.get('layer', 220), T, V, Pp, tri[order]))
    layers.sort(key=lambda l: l[0])
    for _, T, V, Pp, tri in layers:
        for t in tri:
            a, b, c = t[:3]; src = V[[a, b, c]].astype(np.float32); dst = (Pp[[a, b, c]] - [X0, Y0]).astype(np.float32)
            if dst[:, 0].max() < -2 or dst[:, 1].max() < -2 or dst[:, 0].min() > X1 - X0 + 2 or dst[:, 1].min() > Y1 - Y0 + 2: continue
            M = cv2.getAffineTransform(src, dst)
            bx0, by0 = np.floor(dst.min(0)).astype(int); bx1, by1 = np.ceil(dst.max(0)).astype(int) + 1
            bx0, by0 = max(bx0, 0), max(by0, 0); bx1, by1 = min(bx1, X1 - X0), min(by1, Y1 - Y0)
            if bx1 <= bx0 or by1 <= by0: continue
            Mo = M.copy(); Mo[:, 2] -= [bx0, by0]
            wp = cv2.warpAffine(T, Mo, (bx1 - bx0, by1 - by0), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT)
            mk = np.zeros((by1 - by0, bx1 - bx0), np.uint8); cv2.fillConvexPoly(mk, np.round((dst - [bx0, by0]) * 16).astype(np.int32), 1, lineType=cv2.LINE_8, shift=4)
            sel = (mk > 0) & (wp[..., 3] > 0); reg = out[by0:by1, bx0:bx1]
            al = wp[..., 3:4] / 255.0; reg[sel] = (wp * al + reg * (1 - al))[sel]; reg[..., 3][sel] = np.maximum(reg[..., 3][sel], wp[..., 3][sel])
    return out
res = {}; sheets = []
sk0 = Q.jload(cands[0][1]); bones = sk0['bones']; bb = {b['name']: b for b in bones}
poses = {'rest': {}}
for nm, prm in (('thigh_L', 'HipL'), ('thigh_R', 'HipR')):
    for x in (1, -1): poses[f'{prm}{x:+d}'] = {nm: Q.body_angle(bb[nm], x)}
poses['Hips+1'] = {n: Q.body_angle(bb[n], 1) for n in ('thigh_L', 'thigh_R')}
poses['Hips-1'] = {n: Q.body_angle(bb[n], -1) for n in ('thigh_L', 'thigh_R')}
poses['HipL+1,HipR-1'] = {'thigh_L': Q.body_angle(bb['thigh_L'], 1), 'thigh_R': Q.body_angle(bb['thigh_R'], -1)}
poses['HipL-1,HipR+1'] = {'thigh_L': Q.body_angle(bb['thigh_L'], -1), 'thigh_R': Q.body_angle(bb['thigh_R'], 1)}
for lab, path in cands:
    sk = Q.jload(path); rest = render(sk, {}); ro = rest[..., 3] > 0; res[lab] = {'skin': os.path.relpath(path, ROOT)}; row = []
    for pn, ang in poses.items():
        im = rest if pn == 'rest' else render(sk, ang); cov = im[..., 3] > 0
        # notch = px inside the crotch box (x 640..722, y 820..900) opaque at rest, background after posing
        hole = ro & ~cov; box = np.zeros_like(hole); box[820 - Y0:900 - Y0, 640 - X0:722 - X0] = True
        ab = np.zeros_like(hole); ab[:875 - Y0, 640 - X0:722 - X0] = True   # above the rest crotch apex (cut end y=875)
        ys = np.nonzero((hole & box).any(1))[0]
        res[lab][pn] = {'holes_roi': int(hole.sum()), 'holes_crotch_box': int((hole & box).sum()), 'holes_above_apex_y875': int((hole & ab).sum()),
                        'notch_top_y': int(ys.min() + Y0) if len(ys) else None}
        vis = im[..., :3].copy(); vis[im[..., 3] == 0] = [235, 235, 235]; vis[hole] = [255, 0, 255]
        row.append(vis.astype(np.uint8))
    sheets.append(np.concatenate(row, 1))
json.dump({'view': view, 'roi': [X0, Y0, X1, Y1], 'crotch_box': [640, 820, 722, 900], 'poses': list(poses), 'angles': poses, 'result': res},
          open(f'{OUT}/notch_{view}.json', 'w'), indent=1)
Image.fromarray(np.concatenate(sheets, 0)).save(f'{OUT}/notch_{view}.png')
for lab in res: print(lab, {p: (r['holes_crotch_box'], r['holes_above_apex_y875'], r['notch_top_y']) for p, r in res[lab].items() if p != 'skin'})
