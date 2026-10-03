# forearm+hand offset at each turn handoff: turn frame vs live rig (edge-NCC, same method as headgroup/measure_offsets.py),
# reported relative to the torso offset (what an arm sub-offset would have to correct). Read-only.
import json, numpy as np; from PIL import Image; from scipy import ndimage as nd
ROOT = '/workspace/shadowveil'; D = f'{ROOT}/rig/work/qa_post6d5b239/driver_turn'
def edges(f):
    a = np.array(Image.open(f).convert('RGBA')).astype(float); g = a[..., :3].mean(-1)*a[..., 3]/255 + 255*(1 - a[..., 3]/255)
    return np.hypot(nd.sobel(g, 0), nd.sobel(g, 1))
def best(A, B, box, R=32):
    x0, y0, x1, y1 = box; b = B[y0:y1, x0:x1]; b = (b - b.mean())/(b.std() + 1e-9); res = (-9, 0, 0)
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            a = A[y0+dy:y1+dy, x0+dx:x1+dx]
            if a.shape != b.shape: continue
            a = (a - a.mean())/(a.std() + 1e-9); s = float((a*b).mean())
            if s > res[0]: res = (s, dx, dy)
    return res
def bbox(p, pad=6):
    a = np.array(Image.open(p).convert('RGBA'))[..., 3]; ys, xs = np.nonzero(a)
    return [int(xs.min()) - pad, int(ys.min()) - pad, int(xs.max()) + pad + 1, int(ys.max()) + pad + 1] if len(ys) else None
def union(a, b): return [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])] if a and b else (a or b)
HO = {'left': 62, 'back': 109, 'right': 160}; TORSO = json.load(open(f'{ROOT}/rig/work/headgroup/handoff_offsets.json'))
out = {}
for v, f in HO.items():
    A = edges(f'{D}/handoff_{v}_frame.png'); B = edges(f'{D}/handoff_{v}_live.png'); r = {'frame': f, 'torso': TORSO[v]['torso']}
    hr = {p['id']: p for p in json.load(open(f'{ROOT}/views/{v}/hands/rig.json'))['parts']}
    for s in ('L', 'R'):
        import os; fp = f'{ROOT}/views/{v}/body/forearm_{s}.png'; fa = bbox(fp) if os.path.exists(fp) else None
        pm = hr.get(f'{s}_palm'); hb = bbox(f'{ROOT}/views/{v}/hands/{pm["file"]}') if pm and pm.get('file') else None
        box = union(fa, hb)
        if not box: continue
        # lower forearm + hand only (the part that would move with a forearm sub-rotation)
        sc, dx, dy = best(A, B, box)
        r[f'forearm_{s}'] = {'box': box, 'dx': dx, 'dy': dy, 'ncc': round(sc, 3), 'rel_torso': {'dx': dx - TORSO[v]['torso']['dx'], 'dy': dy - TORSO[v]['torso']['dy']}}
    out[v] = r; print(v, json.dumps(r))
json.dump(out, open('handoff_arm_offsets.json', 'w'), indent=1)
