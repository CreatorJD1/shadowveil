#!/usr/bin/env python3
"""Find where each authored eye/hand/hair still sits on the matching turnaround still (read-only).
Blue chroma is keyed out for matching only; multi-scale normalised cross-correlation on grey.
Writes app/driver/align.json. An overlay is accepted only if the match score is high."""
import cv2, numpy as np, json, pathlib
GB = pathlib.Path('/workspace/shadowveil/reference/grok_build')
ROT = GB / 'public/clean-room/layers/rotation'
T = GB / 'artifacts/turn'
def load_turn(a):
    im = cv2.imread(str(ROT / f'turn-{a:03d}.png'), cv2.IMREAD_UNCHANGED)
    al = im[..., 3:4].astype(np.float32)/255
    rgb = (im[..., :3].astype(np.float32)*al + 128*(1-al)).astype(np.uint8)
    return rgb, im[..., 3]
def keymask(bgr):
    b, g, r = [bgr[..., i].astype(int) for i in range(3)]
    return ~((b > 140) & (b - r > 90) & (b - g > 50))
def match(ov_path, a, region=None):
    ov = cv2.imread(str(ov_path)); m = keymask(ov)
    if m.mean() < 0.05: return None
    tr, alpha = load_turn(a)
    full = tr
    rx0, ry0 = 0, 0
    if region: rx0, ry0, rx1, ry1 = region; tr = tr[ry0:ry1, rx0:rx1]
    D = 4
    trs = cv2.resize(tr, None, fx=1/D, fy=1/D, interpolation=cv2.INTER_AREA)
    def score(img, s, f):
        o = cv2.resize(ov, None, fx=s*f, fy=s*f, interpolation=cv2.INTER_AREA)
        mm = cv2.resize(m.astype(np.uint8), (o.shape[1], o.shape[0]), interpolation=cv2.INTER_NEAREST)
        if o.shape[0] >= img.shape[0] or o.shape[1] >= img.shape[1] or o.shape[0] < 8: return None
        res = cv2.matchTemplate(img, o, cv2.TM_CCORR_NORMED, mask=np.dstack([mm]*3)*255); res[~np.isfinite(res)] = 0
        _, v, _, loc = cv2.minMaxLoc(res); return v, loc, o.shape[1], o.shape[0]
    best = None
    for s in np.arange(0.20, 1.21, 0.02):
        r = score(trs, s, 1/D)
        if r and (best is None or r[0] > best[0]): best = (r[0], s, r[1])
    _, s0, (lx, ly) = best
    # refine at full res in a window around the coarse hit
    best = None
    for s in np.arange(s0 - 0.03, s0 + 0.031, 0.0025):
        ow, oh = int(ov.shape[1]*s), int(ov.shape[0]*s)
        x0, y0 = max(0, lx*D - 24), max(0, ly*D - 24)
        win = tr[y0:y0 + oh + 48, x0:x0 + ow + 48]
        r = score(win, s, 1)
        if r and (best is None or r[0] > best[0]): best = (r[0], s, (r[1][0] + x0, r[1][1] + y0), r[2], r[3])
    best = (best[0], best[1], (best[2][0] + rx0, best[2][1] + ry0), best[3], best[4])
    tr = full
    v, s, loc, w, h = best
    # refine score with plain correlation on keyed pixels (more discriminative than CCORR)
    o = cv2.resize(ov, None, fx=s, fy=s, interpolation=cv2.INTER_AREA).astype(np.float32)
    mm = cv2.resize(m.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST).astype(bool)
    crop = tr[loc[1]:loc[1]+h, loc[0]:loc[0]+w].astype(np.float32)
    x, y = o[mm].ravel(), crop[mm].ravel()
    ncc = float(np.corrcoef(x, y)[0, 1]); mad = float(np.abs(x - y).mean())
    return dict(src=str(ov_path.relative_to('/workspace/shadowveil')), angle=a, scale=round(float(s), 3), x=int(loc[0]), y=int(loc[1]),
                w=int(w), h=int(h), ccorr=round(float(v), 4), ncc=round(ncc, 4), mad=round(mad, 2))
jobs = []
for a in (0, 45, 90, 270, 315): jobs.append(('eyes', a, T / f'fix/eyes-{a:03d}.jpg'))
for a in (0, 45, 90, 270, 315): jobs.append(('face', a, T / f'face-{a:03d}.jpg'))
for a in (0, 45, 315):
    for side in 'LR': jobs.append(('hand' + side, a, T / f'lock/hand-{a:03d}{side}.jpg'))
for a in (0, 45, 180, 315): jobs.append(('hands', a, T / f'hands-{a:03d}.jpg'))
for a in range(0, 360, 45): jobs.append(('hair', a, GB / f'public/clean-room/layers/hair/hair-{a:03d}.png'))
out = []
for kind, a, p in jobs:
    region = (0, 0, 1365, 520) if kind in ('eyes', 'face') else None if kind == 'hair' else (0, 450, 1365, 1250)
    r = match(p, a, region)
    if r: r['kind'] = kind; out.append(r); print(kind, a, r['scale'], r['x'], r['y'], r['ccorr'], r['ncc'], r['mad'])
json.dump(out, open('/workspace/shadowveil/app/driver/align.json', 'w'), indent=1)
