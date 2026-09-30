#!/usr/bin/env python3
"""Line-art QA for the bikini bottom / hip lines of a front view (apose, tpose, back).
usage: bk_measure.py VIEW SKIN_JSON RENDER_DIR [--out report.json] [--overlay DIR]
RENDER_DIR holds <name>.png renders (shots.js, transparent bg) named rest, hipL+12, hipL-12, hipL+25, ... (the param
values are read from the name: +12 -> 0.5, +25 -> 1.0).
Curves (rest, from the fabric mask of base_body_skin.png and the alpha silhouette): waistband, legOpen_R/L (leg openings
incl. the crotch curve), thighOuter_R/L (side outline from the waistband corner down 150 px), thighInner_R/L (thigh gap).
Each rest sample is carried into the pose through the actual skin mesh (topmost containing triangle, barycentric, LBS
with the renderer's canvas-rotate convention), then in the posed render:
  width  = ink width across the line (integral of clip((45-L)/30,0,1) along the normal, +-6 px, connected run only)
  break  = no ink (min luma > 45) within +-3 px of the mapped point
  turn   = max turning angle (deg) of the line centre (ink centroid) between chords of 6 px (3 px resample), i.e. kinks
"""
import json, sys, os, math, argparse
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import measure
ROOT = '/workspace/shadowveil'
ap = argparse.ArgumentParser(); ap.add_argument('view'); ap.add_argument('skin'); ap.add_argument('renders')
ap.add_argument('--out'); ap.add_argument('--overlay'); ap.add_argument('--names', default=None)
A = ap.parse_args()
sk = json.load(open(A.skin)); bones = sk['bones']; bn = [b['name'] for b in bones]; bi = {n: i for i, n in enumerate(bn)}
V = np.array(sk['vertices'], float); TR = np.array(sk['triangles'], int); WT = sk['weights']
img = np.asarray(Image.open(f"{ROOT}/views/{A.view}/{sk['image']}").convert('RGBA')).astype(float)
H, W = img.shape[:2]
MIDX = bones[bi['pelvis']]['pivot'][0]
hipY = min(bones[bi['thigh_L']]['pivot'][1], bones[bi['thigh_R']]['pivot'][1])
# ---------------- rest curves
def lum(a): return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
Y0, Y1, X0, X1 = int(hipY - 140), int(hipY + 170), int(MIDX - 230), int(MIDX + 230)
sub = img[Y0:Y1, X0:X1]
mx = sub[..., :3].max(-1); mn = sub[..., :3].min(-1)
fab = (sub[..., 3] > 200) & (mx < 95) & (mx - mn < 22)
lab, n = ndi.label(fab); sz = ndi.sum(fab, lab, range(1, n + 1))
# the bikini bottom = largest dark blob whose centroid lies below the navel line and around the midline
cands = sorted(range(1, n + 1), key=lambda k: -sz[k - 1])
fabm = None
for k in cands[:6]:
    ys, xs = np.nonzero(lab == k)
    if abs(xs.mean() + X0 - MIDX) < 60 and ys.mean() + Y0 > hipY - 80: fabm = ndi.binary_fill_holes(lab == k); break
fabm = ndi.binary_opening(fabm, iterations=1)
con = max(measure.find_contours(fabm.astype(float), 0.5), key=len)[:, ::-1] + [X0, Y0]   # (x, y)
sil = ndi.binary_fill_holes(sub[..., 3] > 127)
scon = [c - 1 for c in measure.find_contours(np.pad(sil, 1).astype(float), 0.5)]
def resample(P, step=3.0):
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    if d[-1] < step: return P
    s = np.arange(0, d[-1], step); return np.c_[np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])]
# split the fabric contour: waistband = the top run (upward normal), legs = the rest split by the midline
fy = con[:, 1]; top_y = np.array([fy[np.abs(con[:, 0] - x) < 1.5].min() if (np.abs(con[:, 0] - x) < 1.5).any() else np.nan for x in con[:, 0]])
is_top = np.abs(fy - top_y) < 1.0
xl, xr = con[:, 0].min(), con[:, 0].max()
curves = {}
wb = con[is_top & (con[:, 0] > xl + 6) & (con[:, 0] < xr - 6)]; wb = wb[np.argsort(wb[:, 0])]; curves['waistband'] = resample(wb)
low = con[~is_top]
for side, sel in (('R', low[:, 0] < MIDX), ('L', low[:, 0] >= MIDX)):
    P = low[sel]; P = P[np.argsort(P[:, 1])] if True else P
    # order along the contour instead of by y (the crotch curve turns horizontal)
    idx = np.nonzero(~is_top & ((con[:, 0] < MIDX) if side == 'R' else (con[:, 0] >= MIDX)))[0]
    # longest contiguous run of contour indices (cyclic)
    runs = np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1); r = max(runs, key=len)
    P = con[r]; P = P[(P[:, 0] > xl + 6) & (P[:, 0] < xr - 6)]
    curves[f'legOpen_{side}'] = resample(P)
# silhouette: outer thigh line from the waistband corner down 150 px, inner thigh (gap) near the crotch
S = np.vstack([c[:, ::-1] + [X0, Y0] for c in scon if len(c) > 200])
cy_ = con[:, 1].max()
for side in 'RL':
    o = S[((S[:, 0] < MIDX - 60) if side == 'R' else (S[:, 0] > MIDX + 60)) & (S[:, 1] > wb[:, 1].min() - 5) & (S[:, 1] < hipY + 150)]
    o = o[np.argsort(o[:, 1])]; curves[f'thighOuter_{side}'] = resample(o)
gaps = [c[:, ::-1] + [X0, Y0] for c in scon if len(c) > 30]
gap = [g for g in gaps if abs(g[:, 0].mean() - MIDX) < 40 and g[:, 1].min() > cy_ - 30]
inner = np.vstack(gap) if gap else S[(np.abs(S[:, 0] - MIDX) < 45) & (S[:, 1] > cy_ - 5)]
inner = inner[(inner[:, 1] > cy_ - 4) & (inner[:, 1] < cy_ + 60)]
for side in 'RL':
    q = inner[(inner[:, 0] < MIDX) if side == 'R' else (inner[:, 0] >= MIDX)]
    if len(q) > 3: q = q[np.argsort(q[:, 1])]; curves[f'thighInner_{side}'] = resample(q)
LTH = {}  # ink threshold: fabric-side lines 45 (fabric luma ~53), silhouette lines 90 (skin ~140 / transparent)
# ---------------- mesh mapping
tri_xy = V[TR[:, :3]]
bb0 = tri_xy.min(1); bb1 = tri_xy.max(1)
def locate(p):
    c = np.nonzero((bb0[:, 0] <= p[0] + 1e-6) & (bb1[:, 0] >= p[0] - 1e-6) & (bb0[:, 1] <= p[1] + 1e-6) & (bb1[:, 1] >= p[1] - 1e-6))[0]
    best = None
    for t in c:
        a, b, cc = tri_xy[t]; m = np.array([[b[0] - a[0], cc[0] - a[0]], [b[1] - a[1], cc[1] - a[1]]])
        if abs(np.linalg.det(m)) < 1e-9: continue
        u, v = np.linalg.solve(m, p - a); l = np.array([1 - u - v, u, v])
        if l.min() >= -1e-6 and (best is None or TR[t, 3] > best[2]): best = (t, l, TR[t, 3])
    return best
def world(params):
    M = [None] * len(bones)
    def get(i):
        if M[i] is not None: return M[i]
        b = bones[i]; par = get(bi[b['parent']]) if b.get('parent') in bi else np.eye(3)
        x = params.get(b.get('param'), 0.0) if b.get('param') else 0.0
        mx_ = b.get('maxDeg', b.get('maxRotDeg', 0)) or 0; rd = b.get('rotDir', 1)
        up = b.get('degAtPlus1', rd * mx_); dn = b.get('degAtMinus1', -rd * mx_)
        ang = math.radians(x * up if x >= 0 else abs(x) * dn)
        px, py = b['pivot']; c, s = math.cos(ang), math.sin(ang)
        R = np.array([[c, -s, px - c * px + s * py], [s, c, py - s * px - c * py], [0, 0, 1]])
        M[i] = par @ R; return M[i]
    for i in range(len(bones)): get(i)
    return M
def posed_vert(vi, M):
    p = np.array([V[vi, 0], V[vi, 1], 1.0]); return sum(w * (M[k] @ p)[:2] for k, w in WT[vi])
curves = {k: P for k, P in curves.items() if len(P) >= 6}
print("curves", {k: (len(P), [round(float(v)) for v in P.min(0)], [round(float(v)) for v in P.max(0)]) for k, P in curves.items()}, file=sys.stderr)
loc = {k: [locate(p) for p in P] for k, P in curves.items()}
for k in curves: LTH[k] = 45.0 if k.startswith(('waist', 'legOpen')) else 90.0
def map_curve(k, M):
    out = []
    for p, L in zip(curves[k], loc[k]):
        if L is None: out.append([np.nan, np.nan]); continue
        t, l, _ = L; out.append(sum(l[j] * posed_vert(TR[t, j], M) for j in range(3)))
    return np.array(out)
# ---------------- measurement in a render
def bil(Lm, x, y):
    x0 = np.clip(np.floor(x).astype(int), 0, Lm.shape[1] - 2); y0 = np.clip(np.floor(y).astype(int), 0, Lm.shape[0] - 2)
    fx, fy = x - x0, y - y0
    return (Lm[y0, x0] * (1 - fx) * (1 - fy) + Lm[y0, x0 + 1] * fx * (1 - fy) + Lm[y0 + 1, x0] * (1 - fx) * fy + Lm[y0 + 1, x0 + 1] * fx * fy)
def turn_arr(P, chord=3, smooth=3):
    """per-sample turning angle (deg) between the chords (i-chord -> i) and (i -> i+chord); NaN-safe, ends = NaN"""
    P = P.copy(); n = len(P); out = np.full(n, np.nan)
    ok = ~np.isnan(P).any(1)
    if ok.sum() < 2 * chord + 3: return out
    idx = np.arange(n); 
    for d in (0, 1): P[~ok, d] = np.interp(idx[~ok], idx[ok], P[ok, d])
    if smooth > 1:
        k = np.ones(smooth) / smooth; P = np.c_[np.convolve(P[:, 0], k, 'same'), np.convolve(P[:, 1], k, 'same')]
    for i in range(chord + smooth, n - chord - smooth):
        a = P[i] - P[i - chord]; b = P[i + chord] - P[i]
        out[i] = abs(math.degrees(math.atan2(a[0] * b[1] - a[1] * b[0], a @ b)))
    return out
def measure_img(path, params):
    im = np.asarray(Image.open(path).convert('RGBA')).astype(float)
    Al = im[..., 3] / 255; Lm = lum(im[..., :3])
    M = world(params); res = {}; cents = {}
    for k in curves:
        P = map_curve(k, M); ok = ~np.isnan(P).any(1)
        T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9; N = np.c_[-T[:, 1], T[:, 0]]
        s = np.arange(-6, 6.01, 0.25); widths = []; brk = []; C = []
        for p, nrm, o in zip(P, N, ok):
            if not o: widths.append(np.nan); brk.append(False); C.append([np.nan, np.nan]); continue
            xs, ys = p[0] + s * nrm[0], p[1] + s * nrm[1]
            ink = bil(Al * np.clip((LTH[k] - Lm) / (LTH[k] - 15), 0, None), xs, ys)   # alpha-weighted ink
            near = np.abs(s) <= 3
            if ink[near].max() <= 0.05: widths.append(0.0); brk.append(True); C.append([np.nan, np.nan]); continue
            j = np.nonzero(near)[0][np.argmax(ink[near])]
            lo = j; hi = j
            while lo > 0 and ink[lo - 1] > 0.05: lo -= 1
            while hi < len(s) - 1 and ink[hi + 1] > 0.05: hi += 1
            run = ink[lo:hi + 1]; widths.append(float(run.sum() * 0.25)); brk.append(False)
            off = float((run * s[lo:hi + 1]).sum() / run.sum()); C.append([p[0] + off * nrm[0], p[1] + off * nrm[1]])
        widths = np.array(widths); C = np.array(C)
        tg = turn_arr(P, smooth=1); tc = turn_arr(C)
        offs = np.hypot(*(C - P)[~np.isnan(C).any(1)].T)
        res[k] = {'n': int(ok.sum()), 'widthMed': round(float(np.nanmedian(widths)), 2), 'widthP5': round(float(np.nanpercentile(widths, 5)), 2),
                  'widthP95': round(float(np.nanpercentile(widths, 95)), 2), 'breaks': int(np.sum(brk)),
                  'turnMaxGeomDeg': round(float(np.nanmax(tg)), 1) if np.isfinite(tg).any() else None, 'turnMaxInkDeg': round(float(np.nanmax(tc)), 1) if np.isfinite(tc).any() else None,
                  'inkOffsetMeanPx': round(float(offs.mean()), 2) if len(offs) else None,
                  '_w': widths, '_C': C, '_P': P, '_tc': tc, '_tg': tg}
    return res
names = sorted(f[:-4] for f in os.listdir(A.renders) if f.endswith('.png')) if not A.names else A.names.split(',')
def params_of(nm):
    out = {}
    for tok in nm.split('_'):
        for j in ('HipL', 'HipR'):
            lj = j[0].lower() + j[1:]
            if tok.startswith(lj):
                v = tok[len(lj):]; v = float(v); out[j] = {12: 0.5, 25: 1.0}.get(abs(int(v)), v) * (1 if v > 0 else -1)
    return out
rep = {'view': A.view, 'skin': A.skin, 'curvesRest': {k: len(v) for k, v in curves.items()}, 'poses': {}}
rest = measure_img(f'{A.renders}/{"zero" if os.path.exists(A.renders + "/zero.png") else "rest"}.png', {})
for nm in names:
    r = measure_img(f'{A.renders}/{nm}.png', params_of(nm))
    row = {}
    for k in curves:
        a, b = r[k], rest[k]
        dw = np.abs(a['_w'] - b['_w']); dw = dw[~np.isnan(dw)]
        row[k] = {kk: vv for kk, vv in a.items() if not kk.startswith('_')}
        row[k]['dWidthMaxVsRest'] = round(float(np.percentile(dw, 100)), 2) if len(dw) else None
        row[k]['dWidthP95VsRest'] = round(float(np.percentile(dw, 95)), 2) if len(dw) else None
        dt = a['_tc'] - b['_tc']; dg = a['_tg'] - b['_tg']
        row[k]['newKinkInkDeg'] = round(float(np.nanmax(dt)), 1) if np.isfinite(dt).any() else None     # max per-sample turn increase vs rest
        row[k]['newKinkGeomDeg'] = round(float(np.nanmax(dg)), 1) if np.isfinite(dg).any() else None
        j = int(np.nanargmax(dt)) if np.isfinite(dt).any() else None
        row[k]['newKinkAt'] = [round(float(v), 1) for v in a['_P'][j]] if j is not None else None
        row[k]['newKinkRestAt'] = [round(float(v), 1) for v in curves[k][j]] if j is not None else None
        row[k]['breakRestAt'] = [[round(float(v)) for v in curves[k][i]] for i in np.nonzero(a['_w'] == 0)[0]][:12]
        wd = np.abs(a['_w'] - b['_w']); row[k]['dWidthMaxRestAt'] = [round(float(v)) for v in curves[k][int(np.nanargmax(wd))]] if np.isfinite(wd).any() else None
    rep['poses'][nm] = {'params': params_of(nm), 'curves': row}
    if A.overlay:
        os.makedirs(A.overlay, exist_ok=True)
        im = Image.open(f'{A.renders}/{nm}.png').convert('RGBA'); bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); bg = bg.convert('RGB')
        from PIL import ImageDraw
        d = ImageDraw.Draw(bg); cols = {'waistband': (0, 200, 0), 'legOpen_R': (255, 0, 0), 'legOpen_L': (255, 0, 255), 'thighOuter_R': (0, 150, 255), 'thighOuter_L': (0, 255, 255), 'thighInner_R': (255, 150, 0), 'thighInner_L': (200, 200, 0)}
        for k in curves:
            for p, w in zip(r[k]['_P'], r[k]['_w']):
                if np.isnan(p).any(): continue
                c = cols.get(k, (0, 0, 0)) if w > 0 else (255, 255, 0)
                p = p + [0, 0]
                d.ellipse((p[0] - 1, p[1] - 1, p[0] + 1, p[1] + 1), outline=c)
        bg.crop((X0 - 20, Y0, X1 + 20, Y1 + 40)).save(f'{A.overlay}/{nm}_qa.png')
js = json.dumps(rep, indent=1)
if A.out: open(A.out, 'w').write(js)
# summary table
for nm, pr in rep['poses'].items():
    print(nm, ' | '.join(f"{k}: w{v['widthMed']}[{v['widthP5']}-{v['widthP95']}] dW95 {v['dWidthP95VsRest']} max {v['dWidthMaxVsRest']} brk{v['breaks']} kink+{v['newKinkInkDeg']}/{v['newKinkGeomDeg']} off{v['inkOffsetMeanPx']}" for k, v in pr['curves'].items()))
