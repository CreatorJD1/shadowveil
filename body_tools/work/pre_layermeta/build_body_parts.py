# Base Body: cuts views/<view>/base_body.png into posable parts (views/<view>/body/*.png + rig.json).
# Parts partition base_body's pixels exactly; the only added pixels are (a) round joint caps drawn UNDER
# their parent, placed only where the parent is fully opaque, and (b) flat under-fills beneath limbs that
# are layered ABOVE the body (profile near arm), placed only where that limb is fully opaque.
# So the rest composite equals base_body.png bit-for-bit. Flat colours only; no shading.
import json, sys, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = json.load(open(os.path.join(ROOT, 'body_tools/body_specs.json')))
PARTS = ['head','torso','pelvis','upperArm_L','upperArm_R','forearm_L','forearm_R',
         'thigh_L','thigh_R','shin_L','shin_R','foot_L','foot_R','toes_L','toes_R']
PARAMS = ['BodyLean','ShoulderL','ShoulderR','ElbowL','ElbowR','HipL','HipR','KneeL','KneeR','AnkleL','AnkleR','ToeL','ToeR']
# Toes: asymmetric range. param -1..0..+1 -> -30..0..+20 deg anatomical (negative = toes bend UP / push-off,
# positive = curl down); canvas degrees = rotDir * that (rotDir = +1 when toes point right on screen, -1 when left)
TOE_MIN, TOE_MAX = -30, 20
# part -> (parent, joint key, param, maxRotDeg)
CHAIN = {
 'pelvis': (None, None, None, 0), 'torso': ('pelvis','waist','BodyLean',8), 'head': ('torso','neck',None,0),
 'upperArm_L': ('torso','shoulder_L','ShoulderL',25), 'upperArm_R': ('torso','shoulder_R','ShoulderR',25),
 'forearm_L': ('upperArm_L','elbow_L','ElbowL',25), 'forearm_R': ('upperArm_R','elbow_R','ElbowR',25),
 'thigh_L': ('pelvis','hip_L','HipL',25), 'thigh_R': ('pelvis','hip_R','HipR',25),
 'shin_L': ('thigh_L','knee_L','KneeL',25), 'shin_R': ('thigh_R','knee_R','KneeR',25),
 'foot_L': ('shin_L','ankle_L','AnkleL',25), 'foot_R': ('shin_R','ankle_R','AnkleR',25),
 'toes_L': ('foot_L','toe_L','ToeL',TOE_MAX), 'toes_R': ('foot_R','toe_R','ToeR',TOE_MAX)}
OUTLINE = np.array([40, 32, 30])

def layers_for(view, near):
    if view in ('left', 'right'):
        far = 'R' if near == 'L' else 'L'
        L = {f'toes_{far}':200, f'foot_{far}':201, f'shin_{far}':202, f'thigh_{far}':203, f'forearm_{far}':205, f'upperArm_{far}':206,
             'torso':220, 'head':222,
             f'toes_{near}':239, f'foot_{near}':240, f'shin_{near}':241, f'thigh_{near}':242, 'pelvis':246,
             f'forearm_{near}':250, f'upperArm_{near}':251}
    else:
        L = {'toes_L':200,'toes_R':200,'foot_L':201,'foot_R':201,'shin_L':203,'shin_R':203,'thigh_L':205,'thigh_R':205,
             'forearm_L':220,'forearm_R':220,'upperArm_L':222,'upperArm_R':222,
             'torso':240,'head':242,'pelvis':250}
    return L

def line_mask(shape, pts, w=3):
    im = Image.new('L', (shape[1], shape[0]), 0); ImageDraw.Draw(im).line([tuple(p) for p in pts], fill=255, width=w)
    return np.array(im) > 0

def poly_mask(shape, pts):
    im = Image.new('L', (shape[1], shape[0]), 0); ImageDraw.Draw(im).polygon([tuple(p) for p in pts], fill=255, outline=255)
    return np.array(im) > 0

def classes(b):
    rgb = b[..., :3]; lum = rgb.mean(-1); a = b[..., 3]
    skin = (a == 255) & (rgb[..., 0] > 140) & (rgb[..., 2] < 120) & (rgb[..., 0] - rgb[..., 2] > 60)
    outline = (a > 0) & (lum < 70) & (rgb[..., 0] - rgb[..., 2] > 8)
    garment = (a == 255) & (lum < 110) & (np.abs(rgb[..., 0] - rgb[..., 2]) <= 12) & ~outline
    return skin, garment, outline

def build(view):
    sp = SPEC[view]; near = sp.get('near')
    b = np.array(Image.open(os.path.join(ROOT, f'views/{view}/base_body.png'))).astype(np.int32)
    H, W = b.shape[:2]; A = b[..., 3] > 0; A255 = b[..., 3] == 255
    idx = {p: i for i, p in enumerate(PARTS)}
    lab = np.full((H, W), -1, np.int32)
    yy, xx = np.mgrid[0:H, 0:W]
    n = sp['neck']; lx, ly = zip(*n['line'])
    head = A & (yy < np.interp(xx, lx, ly)) & (xx >= n['x0']) & (xx <= n['x1'])
    lab[head] = idx['head']
    for p, pts in sp.get('polys', {}).items():
        m = poly_mask((H, W), pts) & A & (lab < 0); lab[m] = idx[p]
    cut = np.zeros((H, W), bool)
    for j in sp['joints'].values():
        if len(j['cut']) >= 2: cut |= line_mask((H, W), j['cut'])
    for c in sp.get('extraCuts', []):
        cut |= line_mask((H, W), c)
    M = A & (lab < 0) & ~cut
    comp, k = ndimage.label(M)
    used = {}
    for p, pts in sp['seeds'].items():
        if isinstance(pts[0], (int, float)): pts = [pts]
        for sx, sy in pts:
            c = comp[sy, sx]
            if c == 0: raise SystemExit(f'{view}: seed {p} at {sx},{sy} is not in the free body mask')
            if c in used and used[c] != p: raise SystemExit(f'{view}: seeds {p} and {used[c]} share one component (cut does not close)')
            used[c] = p; lab[comp == c] = idx[p]
    report_small = int(((comp > 0) & ~np.isin(comp, list(used))).sum())
    # leftovers (cut lines, crumbs) -> nearest labelled pixel
    rest = A & (lab < 0)
    if rest.any():
        _, (iy, ix) = ndimage.distance_transform_edt(lab < 0, return_indices=True)
        lab[rest] = lab[iy[rest], ix[rest]]
    skin, garment, outline = classes(b)
    def flat(p):
        m = (lab == idx[p]) & skin
        if m.sum() < 50: m = skin & A
        return np.median(b[m][:, :3], 0).astype(int)
    gcol = np.median(b[garment & A][:, :3], 0).astype(int) if garment.any() else OUTLINE
    layers = layers_for(view, near)
    merged = set(sp.get('merged', []))            # not separable in this view: stays part of the parent
    hidden = set(sp.get('hidden', [])) | merged
    imgs = {p: np.where((lab == idx[p])[..., None], b, 0) for p in PARTS}
    extra = {p: np.zeros((H, W), bool) for p in PARTS}   # added (non-rest) pixels per part
    report = {'view': view, 'caps': {}, 'fills': {}, 'unseededPx': report_small}
    sil_d = ndimage.distance_transform_edt(b[..., 3] == 255)   # distance to the silhouette (alpha<255)
    # ---- under-fill beneath limbs drawn above the body (profile near arm) ----
    occ_parts = sp.get('overBody', [])
    if occ_parts:
        occ = np.isin(lab, [idx[p] for p in occ_parts])
        body_ok = A & ~occ & np.isin(lab, [idx[p] for p in ('torso','pelvis','thigh_L','thigh_R','head')])
        region = occ & A255
        # nearest non-occluder body pixel in the same row (left or right, whichever is closer)
        owner = np.full((H, W), -1, np.int32); src = np.zeros((H, W, 2), np.int32)
        for y in np.nonzero(region.any(1))[0]:
            okx = np.nonzero(body_ok[y])[0]
            if len(okx) == 0: continue
            xs = np.nonzero(region[y])[0]
            pos = np.searchsorted(okx, xs)
            lft = okx[np.clip(pos - 1, 0, len(okx) - 1)]; rgt = okx[np.clip(pos, 0, len(okx) - 1)]
            pick = np.where(np.abs(xs - lft) <= np.abs(rgt - xs), lft, rgt)
            maxgap = sp.get('fillMaxGap', 120)
            good = np.abs(pick - xs) <= maxgap
            owner[y, xs[good]] = lab[y, pick[good]]; src[y, xs[good], 0] = pick[good]
        def gpart(p):
            m = (lab == idx[p]) & garment
            return np.median(b[m][:, :3], 0).astype(int) if m.sum() > 50 else gcol
        # Smooth continuation: diffuse owner and garment/skin indicators from the surrounding body into the
        # hidden region (Laplace fill, Neumann at the silhouette), so drawn edges continue instead of stepping.
        ys_, xs_ = np.nonzero(region); y0, y1 = ys_.min() - 6, ys_.max() + 7; x0, x1 = xs_.min() - 6, xs_.max() + 7
        R = region[y0:y1, x0:x1]; Lb = lab[y0:y1, x0:x1]
        OWN = [p for p in ('torso','pelvis','thigh_L','thigh_R','head') if p not in hidden]
        known = body_ok[y0:y1, x0:x1] & ~outline[y0:y1, x0:x1]
        dom = R | known
        chans = [(Lb == idx[p]).astype(float) for p in OWN] + [garment[y0:y1, x0:x1].astype(float)]
        U = np.stack(chans, 0)
        # init hidden region from the row-nearest pass
        ini = [(owner[y0:y1, x0:x1] == idx[p]).astype(float) for p in OWN]
        sxg = garment[np.clip(np.arange(y0, y1)[:, None], 0, H-1), np.clip(src[y0:y1, x0:x1, 0], 0, W-1)].astype(float)
        U[:, R] = np.stack(ini + [sxg], 0)[:, R]
        w = dom.astype(float)
        def nb(a):
            o = np.zeros_like(a); o[..., 1:, :] += a[..., :-1, :]; o[..., :-1, :] += a[..., 1:, :]
            o[..., :, 1:] += a[..., :, :-1]; o[..., :, :-1] += a[..., :, 1:]; return o
        wn = nb(w); wn[wn == 0] = 1
        for _ in range(sp.get('fillIters', 1500)):
            V = nb(U * w) / wn
            U[:, R] = V[:, R]
        own_i = np.argmax(U[:len(OWN)], 0); gar = U[-1] > 0.5
        sil = ndimage.binary_dilation(~A, iterations=2)[y0:y1, x0:x1]
        edge = gar & ~ndimage.binary_erosion(gar, iterations=2)          # garment edge -> drawn line
        edge |= ~gar & ndimage.binary_dilation(gar, iterations=1)
        # Body outline behind the arm: where the arm itself forms the silhouette (row's outermost opaque pixel is
        # arm), the body's own edge is unknown; interpolate it (PCHIP over rows) from the rows above/below where
        # the body edge is visible. The fill is clipped to that edge with anti-aliased coverage and carries a
        # drawn outline along it, so a moving arm reveals a smooth body contour instead of a stair/dotted edge.
        from scipy.interpolate import PchipInterpolator
        al = b[..., 3]
        ext = sp.get('edgeRows', 60)
        ry = np.arange(max(0, y0 - ext), min(H, y1 + ext))
        Ledge = np.full(len(ry), np.nan); Redge = np.full(len(ry), np.nan); Lk = np.zeros(len(ry), bool); Rk = np.zeros(len(ry), bool)
        L255 = np.full(len(ry), -1e9); R255 = np.full(len(ry), 1e9)
        for i, y in enumerate(ry):
            xs = np.nonzero(A[y])[0]
            if len(xs) == 0: continue
            xl, xr = xs[0], xs[-1]
            Ledge[i] = xl + 1 - al[y, xl] / 255.0; Redge[i] = xr + al[y, xr] / 255.0
            Lk[i] = not occ[y, xl:xl + 4].any(); Rk[i] = not occ[y, max(0, xr - 3):xr + 1].any()
            # solid run: first/last x starting a run of >=4 fully opaque pixels (skips the base's stray
            # 249-alpha anti-alias pixels just inside the arm edge, which must not get fill underneath)
            run = np.convolve(A255[y].astype(int), np.ones(4, int), 'valid') == 4
            x2 = np.nonzero(run)[0]
            if len(x2): L255[i], R255[i] = x2[0], x2[-1] + 4
        lw_f = float(sp.get('fillLineW', 2.6))
        cov = np.ones((y1 - y0, x1 - x0)); olw = np.zeros((y1 - y0, x1 - x0))
        gx = np.arange(x0, x1)[None, :].astype(float) + 0.5
        for E, K, sgn in ((Ledge, Lk, 1), (Redge, Rk, -1)):
            ok = K & ~np.isnan(E)
            if ok.sum() < 4 or ok.all(): continue
            f = PchipInterpolator(ry[ok], E[ok], extrapolate=False)
            e = np.where(K, E, f(ry))
            e = np.where(np.isnan(e), E, e)
            # keep the drawn edge (and its outline band) on fully opaque arm pixels, i.e. hidden at rest
            # (clamp curve smoothed over 9 rows and pushed 1 px inward so the edge stays smooth, not a stair;
            # the fill itself is still restricted to fully opaque arm pixels)
            cl = np.where(np.abs(L255 if sgn == 1 else R255) > 1e8, np.nan, L255 if sgn == 1 else R255)
            okc = ~np.isnan(cl)
            if okc.any():
                clf = np.interp(np.arange(len(cl)), np.nonzero(okc)[0], cl[okc])
                cls = ndimage.uniform_filter1d(clf, 9) + sgn * 1.0
                cls = np.where(okc, cls, np.nan)
                e = np.where(np.isnan(cls), e, np.maximum(e, cls) if sgn == 1 else np.minimum(e, cls))
            unk = ~K
            sl = np.gradient(np.nan_to_num(e, nan=0.0)); cs = 1 / np.sqrt(1 + sl ** 2)
            rows = ry - y0; sel = (rows >= 0) & (rows < y1 - y0)
            ee = e[sel][:, None]; uu = unk[sel][:, None]; cc = cs[sel][:, None]
            dd = sgn * (gx - ee) * cc          # >0 inside the body
            cv = np.clip(dd + 0.5, 0, 1)
            cov[rows[sel]] = np.where(uu, np.minimum(cov[rows[sel]], cv), cov[rows[sel]])
            olw[rows[sel]] = np.where(uu, np.maximum(olw[rows[sel]], np.clip(lw_f - dd + 0.5, 0, 1)), olw[rows[sel]])
        report['fillEdge'] = {'rowsL': int((~Lk).sum()), 'rowsR': int((~Rk).sum())}
        for k, p in enumerate(OWN):
            m = R & (own_i == k) & (cov > 0)
            if not m.any(): continue
            gp = gpart(p); fp = flat(p)
            c = np.zeros(m.shape + (3,), int); c[:] = fp; c[gar] = gp; c[edge & R] = OUTLINE
            ow = olw[..., None]; c = np.round(c * (1 - ow) + np.array(OUTLINE) * ow).astype(int)
            full = np.zeros((H, W), bool); full[y0:y1, x0:x1] = m
            imgs[p][full, :3] = c[m]; imgs[p][full, 3] = np.round(255 * cov[m]).astype(int); extra[p] |= full
            report['fills'][p] = int(m.sum())
    # ---- joint caps: child drawn under parent ----
    # Geometry comes from the cut itself: the child's cross-section on the cut line gives the two edge points
    # E1/E2; the pivot is their midpoint and the cap is the disc of radius |E1E2|/2 around it (so the child's
    # cut corners sit exactly on the cap circle and nothing pokes out while rotating). The disc is clipped to
    # pixels where the parent is fully opaque (hidden at rest). The cap's exposed boundary carries the limb's
    # own outline colour, the inside the limb's local flat skin.
    for p, (par, jk, prm, mx) in CHAIN.items():
        if par is None or jk == 'neck' or p in hidden: continue
        j = sp['joints'][jk]
        if len(j['cut']) < 2: continue
        cm = line_mask((H, W), j['cut'], 1) & A
        near_child = ndimage.binary_dilation(lab == idx[p], iterations=2)
        cy, cx = np.nonzero(cm & near_child)
        c0 = np.array(j['cut'][0], float); c1 = np.array(j['cut'][-1], float); u = (c1 - c0) / np.linalg.norm(c1 - c0)
        t = (cx - c0[0]) * u[0] + (cy - c0[1]) * u[1]
        i0, i1 = np.argmin(t), np.argmax(t)
        E1 = np.array([cx[i0], cy[i0]], float) - 0.5 * u; E2 = np.array([cx[i1], cy[i1]], float) + 0.5 * u
        if 'pivot' not in j.get('keep', []):
            j['pivot'] = [round(float((E1[0] + E2[0]) / 2), 1), round(float((E1[1] + E2[1]) / 2), 1)]
        px, py = j['pivot']
        hw = float(max(np.hypot(*(E1 - [px, py])), np.hypot(*(E2 - [px, py]))))
        j['_hw'] = hw; j['_E'] = [E1.tolist(), E2.tolist()]
        if layers[p] > layers[par]: continue          # child above parent: handled by under-fill
        # radius: farthest child pixel on the cut (curved cuts such as the hip line arch well above the chord),
        # so every child edge point sweeps inside the cap while rotating; the tube clip keeps it inside the limb
        rc = float(np.hypot(cx - px, cy - py).max()) + 0.5
        r = min(max(hw, rc), j.get('maxR', 999))
        dist = np.hypot(xx - px, yy - py)
        region = (dist <= r) & (imgs[par][..., 3] == 255) & (imgs[p][..., 3] == 0)
        if 'band' in j:
            region &= ndimage.distance_transform_edt(~line_mask((H, W), j['cut'], 1)) <= j['band']
        # colours: the child's own skin extended by nearest-neighbour + 9px box smoothing (same technique as
        # build_base_body.py uses under the hand), outline = the child's local outline colour. No new shading.
        loc = np.isin(lab, [idx[p], idx[par]]) & (dist <= r * 2.5)   # child + parent skin: cap blends with both
        sk = loc & (b[..., 3] == 255) & ~outline & ~garment & (b[..., :3].mean(-1) > 90); ol = loc & outline & (b[..., 3] == 255)
        olc = np.median(b[ol][:, :3], 0).astype(int) if ol.sum() > 10 else OUTLINE
        yy0, yy1 = int(max(0, py - r - 12)), int(min(H, py + r + 13)); xx0, xx1 = int(max(0, px - r - 12)), int(min(W, px + r + 13))
        sk_c = sk[yy0:yy1, xx0:xx1]
        col = np.zeros((H, W, 4), np.int32); col[..., 3] = 255; col[..., :3] = flat(p)
        if sk_c.sum() > 30:
            _, (iy, ix) = ndimage.distance_transform_edt(~sk_c, return_indices=True)
            nn = b[yy0:yy1, xx0:xx1][iy, ix][..., :3].astype(float)
            col[yy0:yy1, xx0:xx1, :3] = np.round(ndimage.uniform_filter(nn, size=(9, 9, 1))).astype(int)
        lw = float(j.get('lineW', 2.6))
        # anti-aliased outline ring and rim (coverage from the exact distance), so rotated caps stay smooth
        region = (dist <= r + 0.5) & (imgs[par][..., 3] == 255) & (imgs[p][..., 3] == 0) & (region | (dist > r - 1))
        if 'band' in j:
            region &= ndimage.distance_transform_edt(~line_mask((H, W), j['cut'], 1)) <= j['band']
        ringw = np.clip(dist - (r - lw) + 0.5, 0, 1)[..., None]
        col[..., :3] = np.round(col[..., :3] * (1 - ringw) + olc * ringw).astype(int)
        col[..., 3] = np.round(255 * np.clip(r + 0.5 - dist, 0, 1)).astype(int)
        # Keep the cap inside the limb's own tube continued under the parent: reflect each cap pixel across the
        # cut chord E1E2 and require the mirror image to be on the child. So the cap never reaches past the
        # line of the limb's outline (no flaps at the crotch/armpit, no bumps at knee sides). Along the tube
        # sides the cap copies the child's own mirrored edge pixels (outline + anti-aliasing) so the outline
        # simply continues when the joint opens.
        dvec = E2 - E1; nrm = np.array([-dvec[1], dvec[0]]) / np.linalg.norm(dvec)
        ys_, xs_ = np.nonzero(region)
        sd = (xs_ - E1[0]) * nrm[0] + (ys_ - E1[1]) * nrm[1]
        mxp = np.round(xs_ - 2 * sd * nrm[0]).astype(int); myp = np.round(ys_ - 2 * sd * nrm[1]).astype(int)
        inb = (mxp >= 0) & (mxp < W) & (myp >= 0) & (myp < H)
        mxp = np.clip(mxp, 0, W - 1); myp = np.clip(myp, 0, H - 1)
        chm = ndimage.binary_dilation(lab == idx[p], iterations=1)
        keep = inb & chm[myp, mxp]
        if not j.get('tubeClip', False): keep[:] = True
        use_edge = j.get('mirrorEdge', False)
        edge = use_edge & keep & (lab[myp, mxp] == idx[p]) & (sil_d[myp, mxp] <= j.get('edgeBand', 4))
        ey, ex = ys_[edge], xs_[edge]
        src_px = b[myp[edge], mxp[edge]]
        col[ey, ex, :3] = src_px[:, :3]
        col[ey, ex, 3] = np.minimum(col[ey, ex, 3], src_px[:, 3])
        drop = np.zeros((H, W), bool); drop[ys_[~keep], xs_[~keep]] = True
        region &= ~drop & (col[..., 3] > 0)
        # Tube clip: at each end of the cut the child's own outline (fitted over 6-30 px of its silhouette next to
        # E1/E2) is extended under the parent as a straight line; the cap stays on the inside of both lines and
        # carries an anti-aliased outline along them. So an opening joint continues the limb's outline instead of
        # growing a round flap (crotch/armpit) or a bump past the outline (knee sides, shoulder tops).
        if j.get('tube', True):
            chd = (lab == idx[p]) & (sil_d <= 1.5)
            by, bx = np.nonzero(chd)
            clipw = np.zeros((H, W)); keepm = np.ones((H, W), bool); tube_info = []
            for E in (E1, E2):
                dd = np.hypot(bx - E[0], by - E[1]); m = (dd >= 6) & (dd <= 30)
                if m.sum() < 6: tube_info.append(None); continue
                P = np.stack([bx[m], by[m]], 1).astype(float); c = P.mean(0)
                w_, v_ = np.linalg.eigh(np.cov((P - c).T)); u = v_[:, 1]
                nvec = np.array([-u[1], u[0]])
                if (np.array([px, py]) - E) @ nvec < 0: nvec = -nvec
                sdv = (xx - E[0]) * nvec[0] + (yy - E[1]) * nvec[1] + j.get('tubeMargin', 1.0)
                keepm &= sdv >= -0.5
                clipw = np.maximum(clipw, np.clip(lw - sdv + 0.5, 0, 1))
                col[..., 3] = np.minimum(col[..., 3], np.round(255 * np.clip(sdv + 0.5, 0, 1)).astype(int))
                tube_info.append([round(float(u[0]), 3), round(float(u[1]), 3)])
            cw = clipw[..., None]
            col[..., :3] = np.round(col[..., :3] * (1 - cw) + olc * cw).astype(int)
            region &= keepm & (col[..., 3] > 0)
            j['_tube'] = tube_info
        # Sweep clip (toes): drop cap pixels that would leave the rest silhouette anywhere in the joint's range,
        # e.g. the heel-side part of the toe cap swinging below the sole when the toes bend up.
        if j.get('sweep'):
            ys_, xs_ = np.nonzero(region); bad = np.zeros(len(ys_), bool)
            for th in np.arange(j['sweep'][0], j['sweep'][1] + 0.1, 2.5):
                c_, s_ = np.cos(np.radians(th)), np.sin(np.radians(th))
                rx = np.round(px + c_ * (xs_ - px) - s_ * (ys_ - py)).astype(int); ry_ = np.round(py + s_ * (xs_ - px) + c_ * (ys_ - py)).astype(int)
                inside = (rx >= 0) & (rx < W) & (ry_ >= 0) & (ry_ < H)
                bad |= ~inside | ~A[np.clip(ry_, 0, H - 1), np.clip(rx, 0, W - 1)]
            region[ys_[bad], xs_[bad]] = False
        imgs[p][region] = col[region]; extra[p] |= region
        report['caps'][p] = {'under': par, 'r': round(r, 1), 'pivot': j['pivot'], 'px': int(region.sum()), 'E': np.round(np.array(j['_E']), 1).tolist(), 'tube': j.get('_tube')}
    # ---- write ----
    od = os.path.join(ROOT, f'views/{view}/body'); os.makedirs(od, exist_ok=True)
    entries = []; pending = []
    for p in PARTS:
        par, jk, prm, mx = CHAIN[p]
        e = {'id': p, 'file': None if p in hidden else f'{p}.png', 'x': 0, 'y': 0}
        if jk and jk != 'neck': px, py = sp['joints'][jk]['pivot']
        elif p == 'head': px, py = sp['joints']['waist']['pivot']
        else: px, py = sp['joints']['waist']['pivot'] if p == 'pelvis' else (0, 0)
        e.update({'pivotX': float(px), 'pivotY': float(py), 'parent': par, 'layer': layers[p], 'maxRotDeg': mx, 'param': prm})
        if p.startswith('toes'):
            e['minRotDeg'] = TOE_MIN; e['maxRotDeg'] = TOE_MAX
            e['rotDir'] = sp.get('toeRotDir', {}).get(p[-1], 1)
            e['rotRule'] = 'deg = rotDir * (v<0 ? -v*minRotDeg : v*maxRotDeg); v in [-1,1]; v<0 = toes bend up (push-off)'
        if p.startswith('forearm'):
            s = p[-1]; wx, wy = sp['wrist'][s]; e['wristPivot'] = {'x': float(wx), 'y': float(wy)}
        if p in merged:
            e['hidden'] = True; e['notSeparable'] = True
            e['note'] = 'toes not separable in this view (bend is out of the image plane; no clean ball-of-foot cut); drawn as part of the foot'
        elif p in hidden:
            e['hidden'] = True; e['note'] = 'far-side limb, fully occluded by the body in this profile; nothing drawn'
            if (lab == idx[p]).any(): raise SystemExit(f'{view}: hidden part {p} has pixels')
        else:
            im = imgs[p].astype(np.uint8); im[im[..., 3] == 0] = 0
            fn = os.path.join(od, f'{p}.png'); Image.fromarray(im, 'RGBA').save(fn + '.tmp', format='PNG'); pending.append(fn)  # atomic: renamed below
            e['pixels'] = int((im[..., 3] > 0).sum()); e['addedHiddenPixels'] = int(extra[p].sum())
        if p == 'pelvis': e['note'] = 'root; pivot = hip-line centre'
        if p == 'head': e['note'] = 'head+neck above the neck base, rigid child of torso (partition only, never rotates on its own)'
        entries.append(e)
    rig = {'contract': 'v1.2', 'owner': 'Base Body', 'view': view, 'canvas': [W, H], 'keyColor': '#0000FF',
           'coordinateSpace': 'view pixels, origin top-left; every part PNG is full-canvas (x=y=0)',
           'rotSign': 'canvas rotate() convention: + = clockwise on screen (y down); param value in [-1,1] times maxRotDeg',
           'params': PARAMS,
           'paramMap': {e['param']: e['id'] for e in entries if e['param']},
           'layerBand': [200, 299], 'handsAttach': 'palms ride on forearm_L/R transform at wristPivot',
           'parts': entries}
    if view in ('left', 'right'):
        far = 'R' if near == 'L' else 'L'
        rig['profile'] = {'nearSide': near, 'farSide': far, 'farLayers': [201, 209], 'reservedForFarHand': [210, 219],
                          'note': f'{far} (far) arm and leg are behind the body and fully hidden; listed with hidden:true'}
    # keep a declared v1.4 skin (views/<view>/body/skin.json) across rebuilds; key sits right after "view"
    try: prev = json.load(open(os.path.join(od, 'rig.json')))
    except Exception: prev = {}
    if isinstance(prev.get('skin'), str) and os.path.exists(os.path.join(od, prev['skin'])):
        rig = {k: rig[k] for k in list(rig)[:3]} | {'skin': prev['skin']} | {k: rig[k] for k in list(rig)[3:]}
    rj = os.path.join(od, 'rig.json'); json.dump(rig, open(rj + '.tmp', 'w'), indent=1)
    # atomic publish: every file was written to <name>.tmp; os.replace() swaps each in one step, so a reader
    # (renderer, rest_check) never sees a missing or half-written part. PNGs first, rig.json last.
    for fn in pending: os.replace(fn + '.tmp', fn)
    os.replace(rj + '.tmp', rj)
    np.save(os.path.join(ROOT, f'body_tools/work/lab_{view}.npy'), lab)
    report['counts'] = {p: int((lab == idx[p]).sum()) for p in PARTS}
    return report

if __name__ == '__main__':
    for v in (sys.argv[1:] or ['apose','tpose','left','right','back']):
        print(json.dumps(build(v)))
