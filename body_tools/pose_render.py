# Offline pose renderer for Base Body parts (mirrors the preview's drawImage + transform maths).
import json, os, math
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load_rig(view):
    return json.load(open(os.path.join(ROOT, f'views/{view}/body/rig.json')))
def mat(a, px, py):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    # T(p) R T(-p)
    return np.array([[c, -s, px - c*px + s*py], [s, c, py - s*px - c*py], [0, 0, 1]])
def world(rig, pose):
    P = {p['id']: p for p in rig['parts']}; out = {}
    def w(i):
        if i in out: return out[i]
        p = P[i]; m = mat(pose.get(p.get('param') or '', 0.0) * p.get('rotDir', 1), p['pivotX'], p['pivotY'])   # toes: pose = anatomical deg (neg = up)
        out[i] = (w(p['parent']) @ m) if p['parent'] else m
        return out[i]
    for i in P: w(i)
    return out
def render(view, pose_deg, scale=0.5, bg=(0, 0, 255, 255), extra=None):
    """pose_deg: {param: degrees}. extra: list of (layer, PIL image full canvas, parent part id or None)."""
    rig = load_rig(view); W, H = rig['canvas']; Wm = world(rig, pose_deg)
    S = np.diag([scale, scale, 1.0])
    out = Image.new('RGBA', (int(W*scale), int(H*scale)), bg)
    items = [(p['layer'], Image.open(os.path.join(ROOT, f'views/{view}/body/{p["file"]}')), p['id']) for p in rig['parts'] if p.get('file')]
    if extra: items += extra
    for layer, im, pid in sorted(items, key=lambda t: t[0]):
        M = S @ (Wm[pid] if pid else np.eye(3))
        inv = np.linalg.inv(M)
        t = im.convert('RGBA').convert('RGBa').transform(out.size, Image.AFFINE, tuple(inv[:2].ravel()), resample=Image.BILINEAR).convert('RGBA')
        out.alpha_composite(t)
    return out

def owner_parts(view):
    """Other owners' parts at rest: (layer, image, attach part id). Hands ride the forearm; face+hair ride the head."""
    base = os.path.join(ROOT, f'views/{view}')
    def J(p):
        try: return json.load(open(p))
        except Exception: return None
    items = []
    hr = J(f'{base}/hair/rig.json'); hr = hr if isinstance(hr, list) else ((hr or {}).get('parts') or [])
    for p in hr:
        if p.get('file') and os.path.exists(f'{base}/hair/{p["file"]}'):
            items.append((p['layer'] if p['id'] != 'hair_back' else 100, Image.open(f'{base}/hair/{p["file"]}'), 'head'))
    hd = J(f'{base}/hands/rig.json')
    if hd:
        for p in hd['parts']:
            if p.get('file') and not p.get('hidden'):
                side = p['id'][0]
                items.append((p['layer'], Image.open(f'{base}/hands/{p["file"]}'), f'forearm_{side}'))
    ey = J(f'{base}/eyes/rig.json')
    if ey:
        for E in ey.get('eyes', []):
            w = f'{base}/eyes/{E}_white.png'; i = f'{base}/eyes/{E}_iris.png'
            if os.path.exists(w):
                wi = Image.open(w).convert('RGBA'); e = wi
                if os.path.exists(i):
                    ia = np.array(Image.open(i).convert('RGBA')).astype(float); wa = np.array(wi).astype(float)
                    ai = ia[..., 3:4]/255; rgb = ia[..., :3]*ai + wa[..., :3]*(1-ai)
                    e = Image.fromarray(np.concatenate([rgb, wa[..., 3:4]], -1).astype('uint8'), 'RGBA')
                items.append((800, e, 'head'))
            for f, l in ((f'{base}/eyes/{E}_lid_0.png', 801), (f'{base}/eyes/{E}_lash.png', 802)):
                if os.path.exists(f): items.append((l, Image.open(f), 'head'))
    if os.path.exists(f'{base}/mouth/rest.png'): items.append((850, Image.open(f'{base}/mouth/rest.png'), 'head'))
    return items
