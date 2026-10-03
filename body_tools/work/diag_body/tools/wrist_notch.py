"""Wrist +-25 bend test with Hands' F8 parts + F12 wrist flaps, and a candidate forearm hidden underlap ("wristcap") that closes the outline-corner notch.
Scene (back->front): F8 hand (with its F12 flap underneath), rotated about f8_palm_pivot_frame; body pieces on top (forearm above the hand).
Candidate wristcap_<S>: belongs to forearm_<S> (does NOT rotate with the hand), drawn UNDER the F8 hand: px = F8 hand px with alpha 255 within DEPTH px past the
wrist boundary line (hand side), and within 30 px of the palm pivot; flat her skin tone, her line tone on px within 2 px of the hand's outline. Hidden at rest.
Metrics = Hands' F12 definitions (f12.py): end_notch = px closed by a 5 px disk (or enclosed) in the two seam-end zones, not gaps at rest; seam gap the same in the interior.
Usage: python3 wrist_notch.py [DEPTH ...]   (writes ../<ang>/wrist_test/)"""
import sys; sys.path.insert(0, '.'); from common import *
from collections import Counter
K8 = np.ones((3, 3), bool)
def over(d, s):
    a = s[..., 3:4]; oa = a + d[..., 3:4] * (1 - a)
    return np.concatenate([np.where(oa > 0, (s[..., :3] * a + d[..., :3] * d[..., 3:4] * (1 - a)) / np.maximum(oa, 1e-9), 0), oa], -1)
def rot(im, deg, c):
    if deg == 0: return im
    t = np.radians(deg); yy, xx = np.mgrid[:im.shape[0], :im.shape[1]].astype(float); x = xx + .5 - c[0]; y = yy + .5 - c[1]
    sx = np.cos(t) * x + np.sin(t) * y + c[0] - .5; sy = -np.sin(t) * x + np.cos(t) * y + c[1] - .5
    pm = np.concatenate([im[..., :3] * im[..., 3:4], im[..., 3:4]], -1); o = np.stack([ndi.map_coordinates(pm[..., k], [sy, sx], order=1, mode='constant') for k in range(4)], -1)
    return np.concatenate([np.where(o[..., 3:4] > 0, o[..., :3] / np.maximum(o[..., 3:4], 1e-9), 0), o[..., 3:4]], -1)
def disk(r): y, x = np.ogrid[-r:r + 1, -r:r + 1]; return x * x + y * y <= r * r
def key(c): c = c.astype(int); return c[..., 2] - np.maximum(c[..., 0], c[..., 1]) > 25
DEPTHS = [int(a) for a in sys.argv[1:]] or [4, 6, 8]
res = {}
for ang in ['045', '315']:
    a8 = ANG[ang]['hands']; F = frame(ang); fg, _ = fg_mask(F); WC = json.load(open(f'{OUT}/{ang}/wrist_cuts.json'))
    base = f'{ROOT}/hands/staged/f8_diagonals/{a8}'; fs = f'{base}/frame_scale'; rig = json.load(open(f'{ROOT}/hands/staged/f12_wrist_diag/{a8}/rig.json'))
    pj = json.load(open(f'{OUT}/{ang}/parts.json'))
    body = np.zeros(F.shape[:2] + (4,))
    for k in pj['layerOrder_backToFront']: body = over(body, np.array(Image.open(f'{OUT}/{ang}/pieces/{k}.png')).astype(float) / 255)
    HS = {}; Hm = {}; FL = {}
    for S in 'LR':
        ps = sorted([p for p in rig['parts'] if p['id'].startswith(S + '_') and 'wristflap' not in p['id']], key=lambda p: p['layer']); c = None
        for p in ps:
            im = np.array(Image.open(f"{fs}/{p['file']}").convert('RGBA')).astype(float) / 255; c = im if c is None else over(c, im)
        HS[S] = c; Hm[S] = c[..., 3] > 0
        fp = [p for p in rig['parts'] if p['id'] == S + '_wristflap'][0]
        FL[S] = np.array(Image.open(os.path.normpath(f"{base}/{fp['frame_file']}")).convert('RGBA')).astype(float) / 255
    piv = {S: tuple(WC['wrists'][S]['f8_palm_pivot_frame']) for S in 'LR'}
    os.makedirs(f'{OUT}/{ang}/wrist_test', exist_ok=True)
    FULL = dict(F=F, fg=fg, body=body, HS=HS, Hm=Hm, FL=FL, piv=piv)
    for S in 'LR':
        cx, cy = map(int, FULL['piv'][S]); X0, Y0 = cx - 70, cy - 70; sl = (slice(Y0, Y0 + 140), slice(X0, X0 + 140))
        F = FULL['F'][sl]; fg = FULL['fg'][sl]; body = FULL['body'][sl]; HS = {k: v[sl] for k, v in FULL['HS'].items()}; Hm = {k: v[sl] for k, v in FULL['Hm'].items()}
        FL = {k: v[sl] for k, v in FULL['FL'].items()}; piv = {k: (v[0] - X0, v[1] - Y0) for k, v in FULL['piv'].items()}
        yy, xx = np.mgrid[:140, :140]
        W = WC['wrists'][S]; (x0, y0), (x1, y1) = [(p[0] - X0, p[1] - Y0) for p in W['boundary_line_fit']]; px, py = piv[S]
        t = np.array([x1 - x0, y1 - y0]); t /= np.linalg.norm(t); n = np.array([-t[1], t[0]]); d = (xx + .5 - x0) * n[0] + (yy + .5 - y0) * n[1]
        if d[Hm[S] & (np.hypot(xx - px, yy - py) < 15)].mean() > 0: d = -d   # d>0 forearm side
        near = np.hypot(xx + .5 - px, yy + .5 - py) <= 30
        tt = (xx + .5 - x0) * t[0] + (yy + .5 - y0) * t[1]; tl = np.hypot(x1 - x0, y1 - y0)
        zoneW = (np.abs(d) <= 6) & (tt >= 2) & (tt <= tl - 2); zoneE = (np.abs(d) <= 6) & (((tt >= -3) & (tt < 2)) | ((tt > tl - 2) & (tt <= tl + 3)))
        cols = F[(Hm[S] | (fg & (d > 0))) & near & fg & ~key(F)]; lum = cols @ [.299, .587, .114]
        SKIN = Counter(map(tuple, cols[lum > 110].tolist())).most_common(1)[0][0]; LINE = Counter(map(tuple, cols[lum < 60].tolist())).most_common(1)[0][0]
        hand_full = over(FL[S], HS[S])
        def scene(deg, cap=None):
            out = np.zeros_like(body)
            if cap is not None: out = over(out, cap)
            for T in 'LR':
                h = over(FL[T], HS[T]); out = over(out, rot(h, deg if T == S else 0, piv[T]))
            return over(out, body)
        def gap(c, c0):
            op = c[..., 3] >= .5; lb, nn = ndi.label(~op); brd = set(np.unique(np.concatenate([lb[0], lb[-1], lb[:, 0], lb[:, -1]])))
            enc = np.isin(lb, [k for k in range(1, nn + 1) if k not in brd])
            g = (ndi.binary_closing(op, structure=disk(5), border_value=0) & ~op) | enc
            op0 = c0[..., 3] >= .5; g0 = ndi.binary_closing(op0, structure=disk(5), border_value=0) & ~op0
            return dict(seam_gap=int((g & zoneW & ~g0).sum()), holes=int((enc & (zoneW | zoneE)).sum()), end_notch=int((g & zoneE & ~g0).sum()))
        r0 = scene(0); r = dict(skin=list(SKIN), line=list(LINE), variants={})
        for D in [0] + DEPTHS:
            if D == 0: cap = None; capm = np.zeros_like(fg)
            else:
                full = HS[S][..., 3] >= 0.999
                capm = full & (d <= 0) & (d >= -D) & near
                outside = ~(Hm[S] | fg)
                ln = capm & ndi.binary_dilation(outside | ~Hm[S] & ~fg, structure=K8, iterations=2)
                cap = np.zeros(F.shape[:2] + (4,)); cap[capm, :3] = np.array(SKIN) / 255; cap[ln, :3] = np.array(LINE) / 255; cap[capm, 3] = 1
            rc = scene(0, cap)
            v = dict(cap_px=int(capm.sum()), rest_change_px=int((np.round(rc * 255) != np.round(r0 * 255)).any(-1).sum()))
            for deg in (25, -25):
                c = scene(deg, cap); v[f'{deg:+d}'] = gap(c, r0)
                Image.fromarray(np.round(c[int(py) - 40:int(py) + 40, int(px) - 40:int(px) + 40] * 255).astype(np.uint8)).resize((320, 320), Image.NEAREST).save(f'{OUT}/{ang}/wrist_test/{S}_{deg:+d}_cap{D}.png')
            r['variants'][f'cap_depth_{D}'] = v
            if D:
                o = np.zeros(F.shape[:2] + (4,), np.uint8); o[..., :3] = np.round(cap[..., :3] * 255); o[..., 3] = np.round(cap[..., 3] * 255)
                oo = np.zeros((1168, 768, 4), np.uint8); oo[sl] = o; Image.fromarray(oo, 'RGBA').save(f'{OUT}/{ang}/wrist_test/forearm_{S}_wristcap_d{D}.png')
        res[f'{ang}_{S}'] = r; print(ang, S, json.dumps(r['variants']), flush=True)
json.dump(res, open(f'{OUT}/wrist_test_report.json', 'w'), indent=1)
