import numpy as np, json, math, sys
from PIL import Image
from scipy import ndimage as nd
sys.path.insert(0, '.'); from seg import mask_of
ROOT = '/workspace/shadowveil'
# landmark levels as fractions of height, from OUR apose rig pivots (top 40, foot 1682): shoulder 439, hip 792, knee 1150, ankle 1570
U = {'shoulder': (439 - 40) / 1642, 'knee': (1150 - 40) / 1642}
WIN = {'bust': (0.27, 0.36, 'max'), 'waist': (0.36, 0.45, 'min'), 'hip': (0.44, 0.53, 'max')}
def runs(row):
    x = np.nonzero(row)[0]
    if not len(x): return []
    br = np.nonzero(np.diff(x) > 1)[0]; st = np.r_[x[0], x[br + 1]]; en = np.r_[x[br], x[-1]]
    return list(zip(st.tolist(), en.tolist()))
def measure(m):
    ys, xs = np.nonzero(m); top, foot = int(ys.min()), int(ys.max()); H = foot - top
    Y = lambda u: int(round(top + u * H))
    hipband = m[Y(0.45):Y(0.50)]; cx = int(np.median(np.nonzero(hipband)[1]))
    def trun(y):
        for a, b in runs(m[y]):
            if a <= cx <= b: return (a, b)
        return None
    out = {'top': top, 'foot': foot, 'H': H, 'cx': cx}
    r = trun(Y(U['shoulder'])); out['shoulder_w'] = r[1] - r[0] + 1 if r else None
    for k, (a, b, mode) in WIN.items():
        ws = [(trun(y)[1] - trun(y)[0] + 1, y) for y in range(Y(a), Y(b)) if trun(y)]
        w, y = (max if mode == 'max' else min)(ws); out[k + '_w'] = w; out[k + '_y'] = y
    # crotch: scanning up from knee level, first row where the centre column is opaque
    yk = Y(U['knee']); cr = None
    for y in range(yk, Y(0.40), -1):
        if m[y, cx]: cr = y; break
        pass
    legsep = cr is not None and cr < yk - 5 and not m[yk, cx]
    out['crotch_y'] = cr if legsep else None
    # per-leg widths at knee; ankle = narrowest leg run in u 0.86..0.95
    def legruns(y): return [(a, b) for a, b in runs(m[y]) if b - a > 4]
    kr = legruns(yk); out['knee_w'] = float(np.mean([b - a + 1 for a, b in kr])) if kr and len(kr) <= 3 else None; out['knee_runs'] = len(kr)
    best = None
    for y in range(Y(0.91), Y(0.95)):
        lr = legruns(y)
        if lr:
            w = float(np.mean([b - a + 1 for a, b in lr]))
            if best is None or w < best[0]: best = (w, y, len(lr))
    out['ankle_w'], out['ankle_y'], out['ankle_runs'] = best
    out['leg_len'] = (out['ankle_y'] - out['crotch_y']) if out['crotch_y'] else None
    # arms (only when separated from the torso): armpit = first row below the shoulder where that side has an extra outer run
    arms = {}
    for side in (-1, 1):
        ap = None
        for y in range(Y(U['shoulder']), Y(0.45)):
            rr = runs(m[y]); t = trun(y)
            if not t: continue
            outer = [r for r in rr if (r[1] < t[0] if side < 0 else r[0] > t[1])]
            if outer: ap = (y, (t[0] if side < 0 else t[1])); break
        if not ap: continue
        cen, wid = [], []
        for y in range(ap[0], Y(0.62)):
            rr = runs(m[y]); t = trun(y)
            outer = [r for r in rr if t and (r[1] < t[0] if side < 0 else r[0] > t[1])]
            if not outer: break
            r = outer[0] if side < 0 else outer[-1]; r = min(outer, key=lambda q: q[0]) if side < 0 else max(outer, key=lambda q: q[1])
            cen.append(((r[0] + r[1]) / 2, y)); wid.append(r[1] - r[0] + 1)
        if len(cen) < 20: continue
        # reach: armpit -> farthest pixel of the separated arm (fingertip); elbow/wrist are not detectable in a silhouette
        yy = np.arange(ap[0], ap[0] + len(cen)); best = (0, None)
        for y in yy:
            rr = runs(m[y]); t = trun(y); outer = [r for r in rr if t and (r[1] < t[0] if side < 0 else r[0] > t[1])]
            for r in outer:
                for x in (r[0], r[1]):
                    d = math.hypot(x - ap[1], y - ap[0])
                    if d > best[0]: best = (d, (x, int(y)))
        arms['L' if side > 0 else 'R'] = {'armpit': [ap[1], ap[0]], 'tip': list(best[1]), 'len': best[0]}
    out['arms'] = arms   # 'L' = viewer's right side (her left in front views)
    return out
def normalize(o, top_t, foot_t):
    s = (foot_t - top_t) / o['H']; f = lambda y: None if y is None else round(foot_t - (o['foot'] - y) * s, 1); g = lambda w: None if w is None else round(w * s, 1)
    n = {'scale': round(s, 4), 'top': f(o['top']), 'foot': f(o['foot'])}
    for k in ('shoulder_w', 'bust_w', 'waist_w', 'hip_w', 'knee_w', 'ankle_w', 'leg_len'): n[k] = g(o[k])
    for k in ('bust_y', 'waist_y', 'hip_y', 'crotch_y', 'ankle_y'): n[k] = f(o[k])
    n['arms'] = {sd: {'reach': g(a['len']), 'armpit_y': f(a['armpit'][1]), 'tip_y': f(a['tip'][1])} for sd, a in o['arms'].items()}
    return n
