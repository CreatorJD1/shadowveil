# Base Body weight_bleed: python raster (nearest, same maths as rig/work/crotch_weights/notch.py) of live vs staged skin, arm ROI. Read-only except outputs here.
import sys, json, os, numpy as np, cv2, importlib.util
from PIL import Image
spec = importlib.util.spec_from_file_location('qg', '/workspace/shadowveil/rig/qa_gates.py'); Q = importlib.util.module_from_spec(spec); spec.loader.exec_module(Q)
ROOT = '/workspace/shadowveil'; OUT = os.path.dirname(os.path.abspath(__file__))
view, cand = sys.argv[1], sys.argv[2]; X0, Y0, X1, Y1 = 540, 400, 840, 920
def tex(name):
    for p in (f'{ROOT}/views/{view}/{name}', f'{ROOT}/views/{view}/body/{name}'):
        if os.path.exists(p): return np.asarray(Image.open(p).convert('RGBA')).astype(np.float32)
def render(sk, ang):
    bones = sk['bones']; nb = len(bones); mats = Q.bone_mats(bones, ang); out = np.zeros((Y1 - Y0, X1 - X0, 4), np.float32); layers = []
    for m, lay in ((sk.get('underlay'), 'u'), (sk, 's')):
        if not isinstance(m, dict) or not m.get('weights'): continue
        T = tex(m['image']); V = np.asarray(m['vertices'], float); W = Q.dense_w(m['weights'], nb); Pp = Q.lbs_fast(V, W, mats)
        tri = np.asarray(m['triangles']); order = np.argsort(tri[:, 3], kind='stable') if tri.shape[1] > 3 else np.arange(len(tri))
        layers.append((m.get('layer', 200) if lay == 'u' else sk.get('layer', 220), T, V, Pp, tri[order]))
    layers.sort(key=lambda l: l[0])
    for _, T, V, Pp, tri in layers:
        for t in tri:
            a, b, c = t[:3]; src = V[[a, b, c]].astype(np.float32); dst = (Pp[[a, b, c]] - [X0, Y0]).astype(np.float32)
            if dst[:, 0].max() < -2 or dst[:, 1].max() < -2 or dst[:, 0].min() > X1 - X0 + 2 or dst[:, 1].min() > Y1 - Y0 + 2: continue
            M = cv2.getAffineTransform(src, dst); bx0, by0 = np.floor(dst.min(0)).astype(int); bx1, by1 = np.ceil(dst.max(0)).astype(int) + 1
            bx0, by0 = max(bx0, 0), max(by0, 0); bx1, by1 = min(bx1, X1 - X0), min(by1, Y1 - Y0)
            if bx1 <= bx0 or by1 <= by0: continue
            Mo = M.copy(); Mo[:, 2] -= [bx0, by0]
            wp = cv2.warpAffine(T, Mo, (bx1 - bx0, by1 - by0), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT)
            mk = np.zeros((by1 - by0, bx1 - bx0), np.uint8); cv2.fillConvexPoly(mk, np.round((dst - [bx0, by0]) * 16).astype(np.int32), 1, lineType=cv2.LINE_8, shift=4)
            sel = (mk > 0) & (wp[..., 3] > 0); reg = out[by0:by1, bx0:bx1]; al = wp[..., 3:4] / 255.0
            reg[sel] = (wp * al + reg * (1 - al))[sel]; reg[..., 3][sel] = np.maximum(reg[..., 3][sel], wp[..., 3][sel])
    return out
A = Q.jload(f'{ROOT}/views/{view}/body/skin.json'); B = Q.jload(cand); bb = {b['name']: b for b in A['bones']}
s = 'L' if view == 'left' else 'R'; ua, fa = f'upperArm_{s}', f'forearm_{s}'
poses = {'rest': {}}
for x in (1, -1):
    poses[f'Shoulder{s}{x:+d}'] = {ua: Q.body_angle(bb[ua], x)}; poses[f'Elbow{s}{x:+d}'] = {fa: Q.body_angle(bb[fa], x)}
    poses[f'Shoulder{s}{x:+d},Elbow{s}{x:+d}'] = {ua: Q.body_angle(bb[ua], x), fa: Q.body_angle(bb[fa], x)}
res = {}; rows = []
for pn, ang in poses.items():
    a = render(A, ang); b = render(B, ang); ra = np.round(a).astype(np.uint8); rb = np.round(b).astype(np.uint8)
    diff = (ra != rb).any(-1); hole_new = (ra[..., 3] > 0) & (rb[..., 3] == 0); hole_fixed = (ra[..., 3] == 0) & (rb[..., 3] > 0)
    dark = lambda r: (r[..., 3] > 0) & (r[..., :3].max(-1) < 70)
    res[pn] = {'px_changed': int(diff.sum()), 'new_holes': int(hole_new.sum()), 'holes_filled': int(hole_fixed.sum()), 'dark_line_px_live': int(dark(ra).sum()), 'dark_line_px_cand': int(dark(rb).sum())}
    def vis(r): v = r[..., :3].copy(); v[r[..., 3] == 0] = 235; return v
    dv = vis(rb).copy(); dv[diff] = [255, 0, 255]
    rows.append(np.concatenate([vis(ra), vis(rb), dv], 1))
Image.fromarray(np.concatenate(rows, 0)).save(f'{OUT}/raster_{view}_live_vs_xlimb.png')
json.dump({'view': view, 'roi': [X0, Y0, X1, Y1], 'cand': os.path.relpath(cand, ROOT), 'poses': res}, open(f'{OUT}/raster_{view}_live_vs_xlimb.json', 'w'), indent=1)
for k, v in res.items(): print(view, k, v)
