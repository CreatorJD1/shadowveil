"""Diagonal (45 / 315 deg) eye cuts from the turn frames' own pixels (STAGED; nothing wired into the rig).

Frames: reference/apose_turn/frames/f033.png (45, green/EyeL near) and f191.png (315, amber/EyeR near), 768x1168 on blue.
Parts are full-canvas in FRAME px (768x1168, x=y=0); rig.json carries diagonals.json view_fit
(base_x = scale*frame_x + dx, base_y = scale*frame_y + dy) to place them in the 1365x1739 view space.
Per eye: white (opening; iris footprint backfilled with her nearest sclera pixel of the row), iris (+pupil, her pixels),
lid_0 (her exact pixels around the opening: upper lash band, crease, lower line, AA ring), lid_1..7 (upper lid only:
her lash band moved down as her own pixels, flat lid skin = median of her skin ring above it; eye shows below; lid_7
closed: flat skin down to the lower line), lash (her wing pixels outside the opening columns, drawn on top).
Binary alpha everywhere; each part has a *_chroma.png on #0000FF.
Eyes are ~13-24 px wide in the frame: the segmentation is coarse and the art is soft (AA'd, slight compression),
so edges of white/iris/lid are approximate (rest is still exact because every part is her pixels).
Usage: python3 cut_diag.py   (writes eyes/staged/diagonals/045 and /315)
"""
import json, os, numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.spatial import ConvexHull
ROOT = '/workspace/shadowveil'; OUT = f'{ROOT}/eyes/staged/diagonals'
KEY = np.array([0, 0, 255]); KC = 7; NF = 8; LINE = 90; SLOPE = 2
DIAG = json.load(open(f'{ROOT}/body_tools/work/apose_turn/diagonals/diagonals.json'))['diagonals']
# per eye: tight opening box (x0,y0,x1,y1 exclusive), a sclera seed, iris colour, near/far
CFG = {
 '045': dict(frame='f033', angle=45, eyes={
    'EyeR': dict(bb=(332, 172, 347, 183), seed=(334, 175), ic='amber', near=False),
    'EyeL': dict(bb=(365, 166, 392, 181), seed=(370, 176), ic='green', near=True)}),
 '315': dict(frame='f191', angle=315, eyes={
    'EyeR': dict(bb=(380, 169, 403, 181), seed=(398, 178), ic='amber', near=True),
    'EyeL': dict(bb=(417, 172, 433, 183), seed=(429, 177), ic='green', near=False)}),
}
def classes(s, ic):
    s = s.astype(float); r, g, b = s[..., 0], s[..., 1], s[..., 2]; lum = s.mean(2)
    mx = s.max(2); mn = s.min(2); sat = (mx - mn) / np.maximum(mx, 1)
    scl = (lum > 150) & (sat < 0.36)
    if ic == 'green': iris = (g > r + 8) & (g > 50)
    else: iris = ((sat > 0.5) & (b < 0.42 * r) & (lum > 60) & (r > 110)) | ((lum > 148) & (sat > 0.33) & (b < 0.56 * r))
    return scl, iris, lum, sat
def hull(m, shape):
    ys, xs = np.nonzero(m)
    pts = np.stack([xs, ys], 1).astype(float)
    if len(pts) < 3: return m.copy()
    h = ConvexHull(pts); yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    P = np.stack([xx.ravel(), yy.ravel()], 1)
    inside = np.all(P @ h.equations[:, :2].T + h.equations[:, 2] <= 1e-6, axis=1).reshape(shape)
    return inside | m
def save(rgb, A, path):
    H, W = A.shape; out = np.zeros((H, W, 4), np.uint8); out[A, :3] = rgb[A]; out[A, 3] = 255
    Image.fromarray(out, 'RGBA').save(path)
    ch = np.where(A[..., None], rgb, KEY).astype(np.uint8); Image.fromarray(ch, 'RGB').save(path.replace('.png', '_chroma.png'))

def cut_eye(a, e, c):
    H, W, _ = a.shape; rgb = a; lum = a.mean(2)
    x0, y0, x1, y1 = c['bb']; sub = a[y0:y1, x0:x1]
    scl, iris, sl, _ = classes(sub, c['ic'])
    E = scl | iris
    lab, n = ndi.label(E, structure=np.ones((3, 3)))
    sid = lab[c['seed'][1] - y0, c['seed'][0] - x0]; assert sid > 0, (e, 'seed not on eyeball')
    near = ndi.binary_dilation(lab == sid, iterations=2)
    core = np.zeros_like(E)
    for i in range(1, n + 1):
        comp = lab == i
        if (comp & near).any() and comp.sum() >= 2: core |= comp
    m = hull(core, core.shape)
    mask = np.zeros((H, W), bool); mask[y0:y1, x0:x1] = m
    scm0 = np.zeros((H, W), bool); scm0[y0:y1, x0:x1] = scl
    # iris footprint: hull of iris-class pixels in the opening (pupil / dark rim inside included)
    ir = np.zeros((H, W), bool); ir[y0:y1, x0:x1] = iris & m
    lab2, n2 = ndi.label(ir, structure=np.ones((3, 3)))
    if n2:
        sz = ndi.sum(ir, lab2, range(1, n2 + 1)); big = np.argmax(sz) + 1
        keep = lab2 == big; dist = ndi.distance_transform_edt(~keep)
        for i in range(1, n2 + 1):
            if i != big and dist[lab2 == i].min() <= 3: keep |= lab2 == i
        ys, xs = np.nonzero(keep); foot = hull(keep[ys.min():ys.max() + 1, xs.min():xs.max() + 1], (ys.max() - ys.min() + 1, xs.max() - xs.min() + 1))
        footF = np.zeros((H, W), bool); footF[ys.min():ys.max() + 1, xs.min():xs.max() + 1] = foot; footF &= mask
        inner = ndi.binary_fill_holes(keep | (ndi.binary_dilation(keep, iterations=1) & (lum < LINE)))
        footF &= ~(scm0 & ~inner); footF = ndi.binary_fill_holes(footF)   # hull corners that are her sclera stay in the white (enclosed highlights stay iris)
    else: footF = np.zeros((H, W), bool)
    # her dark iris outline (AA rim) belongs to the iris: grow the footprint into adjacent non-sclera opening pixels (2 steps)
    for _ in range(2):
        footF = footF | (ndi.binary_dilation(footF, iterations=1) & mask & ~scm0)
    cols = np.nonzero(mask.any(0))[0]; c0, c1 = int(cols.min()), int(cols.max())
    top = {int(x): int(np.nonzero(mask[:, x])[0].min()) for x in cols}; bot = {int(x): int(np.nonzero(mask[:, x])[0].max()) for x in cols}
    # her upper lash band: dark pixels touching the opening from above (search box 7 px up)
    bx0, by0, bx1, by1 = x0 - 6, y0 - 7, x1 + 6, y1 + 4
    box = np.zeros((H, W), bool); box[by0:by1, bx0:bx1] = True
    dark = box & (lum < LINE) & ~mask
    yy = np.mgrid[0:H, 0:W][0]; cy = (min(top.values()) + max(bot.values())) / 2
    dl, _ = ndi.label(dark, structure=np.ones((3, 3)))
    ids = np.unique(dl[ndi.binary_dilation(mask, iterations=1) & dark & (yy < cy)]); ids = ids[ids > 0]
    band = np.isin(dl, ids) & (yy < cy + 1)
    ids2 = np.unique(dl[ndi.binary_dilation(mask, iterations=1) & dark & (yy > cy)]); ids2 = ids2[ids2 > 0]
    lower = np.isin(dl, ids2) & (yy > cy) & ~band
    xx = np.mgrid[0:H, 0:W][1]
    colr = (xx >= c0) & (xx <= c1)
    lash = band & ~colr & ~ndi.binary_dilation(mask, iterations=1)          # wing outside the opening columns
    # lid_0 cover: her pixels of band, lower line and a 2 px ring around opening+lines (not the opening)
    cover = (ndi.binary_dilation(mask | band | lower, iterations=2) & box) & ~mask
    # flat lid skin: median of her skin in a ring 2-4 px around the cover, above the eye centre
    dist = ndi.distance_transform_edt(~(cover | mask))
    s_ = rgb.astype(float); mx = s_.max(2); mn = s_.min(2); sat = (mx - mn) / np.maximum(mx, 1)
    ring = (dist >= 2) & (dist <= 4) & (yy < cy) & (lum > 95) & (lum < 175) & (sat > 0.2) & (sat < 0.6) & (s_[..., 2] < s_[..., 0] * 0.8)
    ring &= np.abs(xx - (c0 + c1) / 2) <= (c1 - c0) / 2 + 3
    skin = np.median(rgb[ring], 0).round().astype(int)
    # white: opening pixels, iris footprint backfilled with her nearest sclera pixel of the same row (then +-1, +-2)
    scm = np.zeros((H, W), bool); scm[y0:y1, x0:x1] = scl
    src = mask & ~footF & scm                                        # her sclera pixels
    if src.sum() < 3: src = mask & ~footF & (lum > 140)
    white = rgb.copy()
    for y_, x_ in zip(*np.nonzero(footF)):
        for dy_ in (0, 1, -1, 2, -2, 3, -3):
            xs2 = np.nonzero(src[y_ + dy_])[0]
            if len(xs2): white[y_, x_] = rgb[y_ + dy_, xs2[np.argmin(np.abs(xs2 - x_))]]; break
        else: white[y_, x_] = np.median(rgb[src], 0) if src.any() else rgb[y_, x_]
    # top row of the opening under the iris: her lid-shadow tone (lash-band bottom pixel of the column), not bright sclera
    colsA = np.nonzero(mask.any(0))[0]; topA = {int(x): int(np.nonzero(mask[:, x])[0].min()) for x in colsA}
    trow = [(topA[x], x) for x in topA if not footF[topA[x], x]]
    for x in topA:                                                   # the iris's first row per column (if within 1 row of the lid edge)
        fc = np.nonzero(footF[:, x])[0]
        if len(fc) and fc.min() <= topA[x] + 1 and trow:
            for y_ in range(topA[x], fc.min() + 1):                  # her lash-band bottom pixel of this column (lid shadow line)
                if footF[y_, x]: white[y_, x] = rgb[topA[x] - 1, x]
    # lash band per opening column: dark run directly above the opening (+1 soft row), then shading rows (<= 1)
    Lt = {}
    sk = skin.mean()
    for x in cols:
        t = top[x]; r = t - 1; n_ = 0
        while n_ < 2 and not band[r, x] and lum[r, x] >= LINE and lum[r, x] < sk + 40: r -= 1; n_ += 1   # soft AA rows under the band
        m_ = 0
        while (band[r, x] or lum[r, x] < LINE) and m_ < 8: r -= 1; m_ += 1                               # her dark band run
        if m_ and LINE <= lum[r, x] < sk - 10: r -= 1                                                     # one soft row on top
        Lt[int(x)] = r + 1 if m_ else t
    # outliers (columns where the run was not found / overshot) -> median of the 2 neighbours each side
    xs_ = [int(x) for x in cols]; L0_ = dict(Lt)
    for i, x in enumerate(xs_):
        nb = [L0_[xs_[j]] for j in range(max(0, i - 2), min(len(xs_), i + 3)) if j != i]
        md = int(np.median(nb))
        if abs(L0_[x] - md) > 2: Lt[x] = md
    return dict(mask=mask, foot=footF, white=white, band=band, lower=lower, lash=lash, cover=cover, skin=skin,
                cols=[int(x) for x in cols], c0=c0, c1=c1, top=top, bot=bot, Lt=Lt, ring_n=int(ring.sum()))

def lid_frames(a, g):
    H, W, _ = a.shape; rgb = a; c0, c1, top, bot, Lt, skin = g['c0'], g['c1'], g['top'], g['bot'], g['Lt'], g['skin']
    frames = []; dlog = {}
    for k in range(1, NF):
        n = c1 - c0 + 1; d = np.zeros(n, int)
        for i, x in enumerate(range(c0, c1 + 1)):
            h = bot[x] + 1 - top[x]
            d[i] = int(round((k / KC) * h))
            d[i] = min(d[i], max(0, bot[x] - top[x] + 1 - (1 if k == KC else 0)))
        d[0] = 0; d[-1] = 0                                     # corners stay put
        for _ in range(n):                                      # slope <= SLOPE px per column (eyes are 13-24 px wide)
            for i in range(n):
                for j in (i - 1, i + 1):
                    if 0 <= j < n: d[i] = min(d[i], d[j] + SLOPE)
        A = np.zeros((H, W), bool); col = np.zeros((H, W, 3), int)
        for i, x in enumerate(range(c0, c1 + 1)):
            dc = int(d[i]); lt = Lt[x]; t = top[x]
            for r in range(lt, bot[x] + 1):
                if r < lt + dc: A[r, x] = True; col[r, x] = skin
                elif r < t + dc: A[r, x] = True; col[r, x] = rgb[r - dc, x]
                elif k == KC: A[r, x] = True; col[r, x] = skin
        if k == KC: assert (A[g['mask']]).all(), 'closed frame must hide the opening'
        frames.append((A, col)); dlog[k] = [int(v) for v in d]
    return frames, dlog

def gaze_limits(g):
    m, f = g['mask'], g['foot']
    if not f.any(): return dict(dxAtXminus1=0, dxAtXplus1=0, dyAtYminus1=0, dyAtYplus1=0), {}
    fy, fx = np.nonzero(f); cy = int(round(fy.mean()))
    rowm = np.nonzero(m[cy])[0]; rowf = np.nonzero(f[cy])[0]
    roomL = int(rowf.min() - rowm.min()); roomR = int(rowm.max() - rowf.max())
    my = np.nonzero(m[:, int(round(fx.mean()))])[0]
    room = dict(left=roomL, right=roomR, top_at_center=int(fy.min() - my.min()), bottom_at_center=int(my.max() - fy.max()))
    # frame px (about 0.65 view px): keep 1 px of white, at most 2 px each way; vertical 1 px (clipped by the white)
    lim = dict(dxAtXminus1=-min(2, max(0, roomL - 1)), dxAtXplus1=min(2, max(0, roomR - 1)), dyAtYminus1=-1, dyAtYplus1=1)
    return lim, room

def main():
    for tag, C in CFG.items():
        fr = C['frame']; a = np.array(Image.open(f'{ROOT}/reference/apose_turn/frames/{fr}.png').convert('RGB')).astype(int)
        H, W, _ = a.shape; od = f'{OUT}/{tag}'; os.makedirs(od, exist_ok=True)
        fit = DIAG[str(C['angle'])]['view_fit']
        parts = []; meas = {}; lims = {}; dl = {}; wr = [W, H, 0, 0]
        layer0 = {'EyeR': 400, 'EyeL': 410}
        for e, c in C['eyes'].items():
            g = cut_eye(a, e, c)
            frames, dlog = lid_frames(a, g); dl[e] = dlog
            lid0 = g['cover'] & ~g['lash']
            save(g['white'].astype(np.uint8), g['mask'], f'{od}/{e}_white.png')
            save(a.astype(np.uint8), g['foot'], f'{od}/{e}_iris.png')
            save(a.astype(np.uint8), lid0, f'{od}/{e}_lid_0.png')
            for k, (A, col) in enumerate(frames, 1):
                A = A & ~g['lash']
                save(col.astype(np.uint8), A, f'{od}/{e}_lid_{k}.png')
            save(a.astype(np.uint8), g['lash'], f'{od}/{e}_lash.png')
            lim, room = gaze_limits(g); lims[e] = lim
            fy, fx = np.nonzero(g['foot']); my, mx = np.nonzero(g['mask'])
            allm = g['mask'] | g['cover'] | g['lash']
            for F in [A for A, _ in frames]: allm |= F
            ys_, xs_ = np.nonzero(allm); wr = [min(wr[0], xs_.min()), min(wr[1], ys_.min()), max(wr[2], xs_.max() + 1), max(wr[3], ys_.max() + 1)]
            hexc = lambda v: '#%02X%02X%02X' % tuple(int(q) for q in v)
            meas[e] = dict(near=c['near'], skin=hexc(g['skin']), skin_ring_px=g['ring_n'],
                           iris_bbox=[int(fx.min()), int(fy.min()), int(fx.max()), int(fy.max())] if len(fx) else None,
                           iris_w=int(fx.max() - fx.min() + 1) if len(fx) else 0, iris_h=int(fy.max() - fy.min() + 1) if len(fx) else 0,
                           iris_center=[round(float(fx.mean()), 1), round(float(fy.mean()), 1)] if len(fx) else None,
                           opening_bbox=[int(mx.min()), int(my.min()), int(mx.max()), int(my.max())], opening_w=int(mx.max() - mx.min() + 1),
                           room_px=room, mask_px=int(g['mask'].sum()), iris_px=int(g['foot'].sum()), lash_px=int(g['lash'].sum()),
                           lid_travel_px_per_frame=dlog)
            L0 = layer0[e]; pcx = float((mx.min() + mx.max()) / 2); pcy = float((my.min() + my.max()) / 2)
            ic = meas[e]['iris_center'] or [pcx, pcy]
            parts.append(dict(id=f'{e}_white', file=f'{e}_white.png', x=0, y=0, pivotX=pcx, pivotY=pcy, parent=None, layer=L0, composite='source-over',
                              note='offscreen eye layer; cut from the frame, iris footprint backfilled with her own sclera pixels'))
            parts.append(dict(id=f'{e}_iris', file=f'{e}_iris.png', x=0, y=0, pivotX=ic[0], pivotY=ic[1], parent=f'{e}_white', layer=L0 + 1,
                              composite='source-atop', drive=dict(EyeBallX=[lim['dxAtXminus1'], lim['dxAtXplus1']], EyeBallY=[lim['dyAtYminus1'], lim['dyAtYplus1']],
                              rule='dx = round(X*(EyeBallX[1] if X>0 else -EyeBallX[0])); dy = round(Y*(EyeBallY[1] if Y>0 else -EyeBallY[0])) - per iris at this angle')))
            for k in range(NF):
                parts.append(dict(id=f'{e}_lid_{k}', file=f'{e}_lid_{k}.png', x=0, y=0, pivotX=pcx, pivotY=float(my.min()), parent=f'{e}_white', layer=L0 + 2,
                                  frame=k, param=f'{e}Open', showWhen=f'round((1-{e}Open)*7)=={k}'))
            parts.append(dict(id=f'{e}_lash', file=f'{e}_lash.png', x=0, y=0, pivotX=pcx, pivotY=pcy, parent=f'{e}_white', layer=L0 + 3, composite='source-over'))
        near = [e for e in C['eyes'] if C['eyes'][e]['near']][0]
        rig = {"contract": "runtime-contract v1.2 (staged diagonal; per-iris limits)",
               "workRegion": [int(v) for v in wr], "view": f"diagonal_{tag}", "canvas": [W, H],
               "units": "FRAME pixels of the turn frame, origin top-left; all parts are full-canvas (x=y=0), in drawn position. Map to the 1365x1739 view space with viewFit.",
               "viewFit": dict(fit, rule="base_x = scale*frame_x + dx; base_y = scale*frame_y + dy", source="body_tools/work/apose_turn/diagonals/diagonals.json"),
               "angleDeg": C['angle'], "frameSource": f"reference/apose_turn/frames/{fr}.png",
               "chromaKey": "#0000FF", "eyes": list(C['eyes']), "nearEye": near,
               "eyeIdentity": {"EyeR": "her right eye, amber", "EyeL": "her left eye, green"},
               "baseSource": f"reference/apose_turn/frames/{fr}.png (parts cut from it; rest compared against it)",
               "drawOrderPerEye": ["white", "iris (source-atop on white, offscreen layer)", "lid frame", "lash"],
               "params": {"EyeLOpen": {"range": [0, 1], "default": 1, "frames": "frame=round((1-EyeLOpen)*7); 0=open(exact) .. 7=closed"},
                          "EyeROpen": {"range": [0, 1], "default": 1, "frames": "frame=round((1-EyeROpen)*7)"},
                          "EyeBallX": {"range": [-1, 1], "default": 0, "note": "-1 = her right (viewer-left in these frames)"},
                          "EyeBallY": {"range": [-1, 1], "default": 0, "note": "-1 up, 1 down"}},
               "irisLimitsPx": lims,
               "irisOffsetRule": "per iris (this angle): dx = round(X*(dxAtXplus1 if X>0 else -dxAtXminus1)); dy = round(Y*(dyAtYplus1 if Y>0 else -dyAtYminus1)); irisLimitsPx is keyed by eye here (views use one set for both eyes); frame px - multiply by viewFit.scale for view px",
               "parts": parts, "measurements": meas,
               "layerScheme": "v1.2 global layers, eyes band 400-499 (EyeR 400-403, EyeL 410-413: white 0, iris 1, lid frame 2, lash 3)",
               "lidFrames": 8, "lidFrameFiles": {e: [f'{e}_lid_{k}.png' for k in range(NF)] for e in C['eyes']},
               "lidFrameSelection": "frame = Math.round((1-<E>Open)*(lidFrames-1)) = Math.round((1-<E>Open)*7); lid_0 = open (exact drawing), lid_7 = closed",
               "notes": {"lid_0": "her exact pixels around the opening (binary alpha)",
                         "lid_1..7": "upper lid only: her lash band rows moved down as her own pixels (integer per column, slope <= 2 px/col, corners fixed); vacated rows = flat skin (median of her skin ring); eye shows below; lid_7 = flat skin down to her lower line",
                         "softness": "eyes are 12-21 px wide in the frame and soft/anti-aliased: opening, iris and band edges are approximate (1 px); at view scale (x1.54) they are softer than the views' parts",
                         "farEye": "kept whole (no cheek clipping applied)"}}
        json.dump(rig, open(f'{od}/rig.json', 'w'), indent=1)
        print(tag, {e: (meas[e]['opening_bbox'], meas[e]['iris_bbox'], lims[e], meas[e]['skin']) for e in meas})

if __name__ == '__main__':
    main()
