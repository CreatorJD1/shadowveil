import numpy as np, json, os, sys
from PIL import Image
from scipy import ndimage as nd
sys.path.insert(0, '.'); from seg import mask_of
R = '/workspace/shadowveil'
def load(src):
    if src.startswith('f'):
        p = f'{R}/reference/apose_turn/frames/{src}.png'; a = np.array(Image.open(p).convert('RGB')).astype(int); m = mask_of(p)
    else:
        b = np.array(Image.open(f'{R}/views/{src}/base.png').convert('RGBA')).astype(int); a = b[..., :3]; m = b[..., 3] > 127
    ys, xs = np.nonzero(m); top = ys.min(); H = ys.max() - top
    return a, m, top, H
def measure(src, facing):   # facing -1 = nose toward -x (viewer-left), +1 = toward +x
    a, m, top, H = load(src); s = 1641.0 / H; r, g, b = a[..., 0], a[..., 1], a[..., 2]
    Y0, Y1 = top, top + int(0.20 * H)
    reg = np.zeros_like(m); reg[Y0:Y1] = True; reg &= m
    skin = reg & (r > 110) & (r - b > 45) & (r + g + b > 260)
    mx, Mx = r.clip(0) * 0, 0
    sat = a.max(2) - a.min(2); tot = r + g + b
    # nose tip first: face-side extreme skin pixel in u 0.105..0.140
    ext = []
    for y in range(top + int(0.105 * H), top + int(0.140 * H)):
        xx = np.nonzero(skin[y])[0]
        if len(xx): ext.append(((xx.min() if facing < 0 else -xx.max()), y))
    k, ny = min(ext); nx = k if facing < 0 else -k
    # eye opening = sclera + iris (low r-b, not skin, not lash/hair-dark), window set from the nose tip
    op = m & (tot > 200) & (((r - b) < 35) & (g >= r - 15) & ((g - b > 12) | (tot > 480))) 
    op |= m & (r > 150) & (g > 110) & (b < 110) & (g > 0.74 * r) & (sat > 90) & ((r - g) < 70)
    win = np.zeros_like(m); ya, yb = ny - int(0.040 * H), ny - int(0.004 * H)
    xa, xb = (nx, nx + int(0.05 * H)) if facing < 0 else (nx - int(0.05 * H), nx + 1)
    win[ya:yb, xa:xb] = True; eye = op & win
    lab, n = nd.label(nd.binary_dilation(eye, iterations=1))
    if n == 0: return {'src': src, 'fail': 'no eye'}
    sizes = nd.sum(eye, lab, range(1, n + 1)); i = int(np.argmax(sizes)) + 1
    eyy, exx = np.nonzero((lab == i) & eye); ey = eyy.mean()
    eye_front = exx.min() if facing < 0 else exx.max(); eye_back = exx.max() if facing < 0 else exx.min()
    # back of skull: rear silhouette extreme, rows eye-0.02H .. eye+0.03H (below the bun)
    rr0, rr1 = int(ey - 0.02 * H), int(ey + 0.03 * H); back = []
    for y in range(rr0, rr1):
        xx = np.nonzero(m[y])[0]; back.append(xx.max() if facing < 0 else xx.min())
    bx = max(back) if facing < 0 else min(back)
    # ear: rearmost skin run in rows eye-0.005H .. eye+0.02H, must be behind the eye by > 0.02H
    ep = []
    for y in range(int(ey - 0.005 * H), int(ey + 0.02 * H)):
        xx = np.nonzero(skin[y])[0]
        xx = xx[(xx - eye_back) * facing < -0.02 * H]
        if len(xx) < 2: continue
        # split into runs, take the rearmost run
        br = np.nonzero(np.diff(xx) > 1)[0]; runs = np.split(xx, br + 1)
        run = runs[-1] if facing < 0 else runs[0]
        if len(run) >= 2: ep.append((run.min(), run.max(), y))
    if ep:
        ear_front = np.median([p[0] if facing < 0 else p[1] for p in ep]); ear_c = np.median([(p[0] + p[1]) / 2 for p in ep])
        ear_back = np.median([p[1] if facing < 0 else p[0] for p in ep])
    else: ear_front = ear_c = ear_back = np.nan
    d = lambda x: round(float(abs(x - nx) * s), 1)
    return {'src': src, 'H': int(H), 'scale': round(s, 4), 'nose_tip': [int(nx), int(ny)], 'eye_y_rig': round(float((ey - top) * s + 40), 1),
            'nose_y_rig': round(float((ny - top) * s + 40), 1),
            'head_depth_nose_to_back': d(bx), 'nose_to_ear_front': d(ear_front), 'nose_to_ear_centre': d(ear_c), 'nose_to_ear_back': d(ear_back),
            'nose_to_eye_front': d(eye_front), 'nose_to_eye_back': d(eye_back), 'eye_width': round(float((exx.max() - exx.min() + 1) * s), 1),
            'ear_rows': len(ep)}
if __name__ == '__main__':
    out = {'ours': {'left': measure('left', -1), 'right': measure('right', +1)}, 'video': {}}
    for f in list(range(61, 68)): out['video'][f'f{f:03d}'] = measure(f'f{f:03d}', -1)
    for f in list(range(151, 164)): out['video'][f'f{f:03d}'] = measure(f'f{f:03d}', +1)
    json.dump(out, open('head/h.tmp', 'w'), indent=1); os.replace('head/h.tmp', 'head/head_profile.json')
    K = ['H', 'eye_y_rig', 'nose_y_rig', 'head_depth_nose_to_back', 'nose_to_ear_front', 'nose_to_ear_centre', 'nose_to_eye_front', 'nose_to_eye_back', 'eye_width', 'ear_rows']
    for k, v in list(out['ours'].items()) + list(out['video'].items()): print(k, v and [v[x] for x in K])
