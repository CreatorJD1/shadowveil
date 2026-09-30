# measure-only per-frame body checks of Coder's idle renders (keys_idle_<clip>_<view>); writes only into this folder
import sys, json, os, math, numpy as np
from PIL import Image
from scipy import ndimage as nd
ID = os.environ.get('FRAMES_ROOT', '/workspace/shadowveil/rig/previews/idle/frames'); VD = '/workspace/shadowveil/views'
FOOT = {'apose': 1682, 'tpose': 1682, 'left': 1681, 'right': 1681, 'back': 1681}
def disk(r): y, x = np.ogrid[-r:r + 1, -r:r + 1]; return x * x + y * y <= r * r
def owner(view, o, shape):
    m = np.zeros(shape, bool)
    try: j = json.load(open(f'{VD}/{view}/{o}/rig.json'))
    except Exception: return m
    for p in (j if isinstance(j, list) else j.get('parts', [])):
        f = p.get('file') if isinstance(p, dict) else None
        if f and os.path.exists(f'{VD}/{view}/{o}/{f}'):
            a = np.array(Image.open(f'{VD}/{view}/{o}/{f}').convert('RGBA'))[..., 3]
            if a.shape == shape: m |= a > 0
    return m
def enclosed(op):
    lab, n = nd.label(~op); border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
    keep = np.ones(n + 1, bool); keep[list(border)] = False; keep[0] = False; return keep[lab]
def run(name):
    D = f'{ID}/{name}'; meta = json.load(open(D + '/meta.json')); view = meta['view']
    rest = np.array(Image.open(D + '/rest.png')); RA = rest[..., 3] >= 128; sh = RA.shape
    ys, xs = np.nonzero(RA); y0, y1, x0, x1 = max(0, ys.min() - 120), min(sh[0], ys.max() + 40), max(0, xs.min() - 150), min(sh[1], xs.max() + 150)
    C = (slice(y0, y1), slice(x0, x1))
    hair = nd.binary_dilation(owner(view, 'hair', sh)[C], structure=disk(12))
    hands = nd.binary_dilation(owner(view, 'hands', sh)[C], structure=disk(10)) & ~hair
    face = nd.binary_dilation((owner(view, 'eyes', sh) | owner(view, 'mouth', sh))[C], structure=disk(10))
    other = hair | hands | face
    ul = np.array(Image.open(f'{VD}/{view}/base_body_underlay.png').convert('RGBA'))
    ulc = np.unique(ul[..., :3][ul[..., 3] > 200].reshape(-1, 3), axis=0)
    ulc = ulc[:12] if len(ulc) <= 12 else None   # flat underlay palette (profile views)
    def M(im):
        A = im[..., 3][C] >= 128; rgb = im[..., :3][C].astype(int)
        enc = enclosed(A)
        tear = nd.binary_closing(A, structure=disk(3), border_value=0) & ~A & ~enc
        inner = nd.binary_erosion(A, structure=disk(5), border_value=0)
        navy = inner & (rgb.sum(-1) < 130) & (rgb[..., 2] > rgb[..., 0] + 6)
        return A, enc, tear, navy, rgb
    rA, renc, rtear, rnavy, _ = M(rest)
    renc_d = nd.binary_dilation(renc, structure=disk(3)); rtear_d = nd.binary_dilation(rtear, structure=disk(3))
    rnavy_n = int((rnavy & ~other).sum())
    pel = meta['info']['bones']; pelx = [b for b in pel if b['id'] == 'pelvis'][0]['pivot'][0] - x0
    def feet(A):
        band = A[-260:]; o = {}
        for s, sl in (('xlo', slice(0, int(pelx))), ('xhi', slice(int(pelx), A.shape[1]))):
            r = np.nonzero(band[:, sl].any(1))[0]
            if not len(r): o[s] = None; continue
            low = r.max(); cx = np.nonzero(band[max(0, low - 5):low + 1, sl].any(0))[0]
            o[s] = (int(low + y1 - 260), float(cx.mean() + sl.start + x0), int(cx.min() + sl.start + x0), int(cx.max() + sl.start + x0))
        return o
    rf = feet(rA)
    # neck/shoulder band for the head flicker: rows from chin (bottom of face owners) to +90 px, body-only, full alpha
    fy = np.nonzero(face.any(1))[0]; nb0 = fy.max() if len(fy) else 250; neck = np.zeros_like(rA); neck[nb0:nb0 + 110] = True
    neck &= nd.binary_erosion(rA, structure=disk(6)) & ~hair & ~hands & ~face
    def S(im):
        L = im[..., :3][C].astype(np.float32) @ np.array([.299, .587, .114], np.float32); g = np.hypot(nd.sobel(L, 0), nd.sobel(L, 1)); return float(g[neck].mean())
    s0 = S(rest); rows = []
    FR = [int(x) for x in os.environ['FRAME_RANGE'].split('-')] if os.environ.get('FRAME_RANGE') else None   # optional a-b window (frame number from the file name)
    for fn in sorted(os.listdir(D + '/frames')):
        i = int(fn[1:5])
        if FR and not (FR[0] <= i <= FR[1]): continue
        im = np.array(Image.open(f'{D}/frames/{fn}')); A, enc, tear, navy, rgb = M(im)
        nh = enc & ~renc_d; nt = tear & ~rtear_d
        def comps(m):
            lab, n = nd.label(m); out = []
            for k in range(1, n + 1):
                yy, xx = np.nonzero(lab == k)
                if len(yy) >= 2: out.append([int(len(yy)), int(xx.min() + x0), int(yy.min() + y0), int(xx.max() + x0), int(yy.max() + y0)])
            return sorted(out, reverse=True)[:4]
        bh = nh & ~other; bt = nt & ~other; wh = nh & hands; wt = nt & hands
        uls = 0
        if ulc is not None:
            for c in ulc: uls += int((A & (np.abs(rgb - c).max(-1) <= 1)).sum())
        ft = feet(A); fb = meta['frames'][i]['bones']; hr = fb.get('head')
        rows.append({'f': i, 't': round(meta['frames'][i]['t'], 3),
            'holes_body': int(bh.sum()), 'holes_body_comps': comps(bh), 'holes_hand': int(wh.sum()), 'holes_hair': int((nh & hair).sum()),
            'tears_body': int(bt.sum()), 'tears_body_comps': comps(bt), 'tears_hand': int(wt.sum()),
            'navy_interior_new': int((navy & ~other).sum()) - rnavy_n, 'underlay_flat_visible': uls,
            'foot': {s: None if not ft[s] else {'y': ft[s][0], 'dy_target': ft[s][0] - FOOT[view], 'dx': round(ft[s][1] - rf[s][1], 2), 'edge': max(abs(ft[s][2] - rf[s][2]), abs(ft[s][3] - rf[s][3]))} for s in ft},
            'headAxis': bool(hr and abs(hr[2]) < 0.01), 'neckSharp': round(S(im) / s0, 4)})
    json.dump({'name': name, 'view': view, 'foot_target': FOOT[view], 'rest_navy_interior': rnavy_n, 'rows': rows}, open(name + '.check.json.tmp', 'w'))
    os.replace(name + '.check.json.tmp', name + '.check.json'); print(name, 'done', flush=True)
if __name__ == '__main__':
    for n in sys.argv[1:]: run(n)
