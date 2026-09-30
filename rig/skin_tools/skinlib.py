"""Shared skin.json helpers (contract v1.4): load, validate, rest coverage by pixel-centre rasterisation.
A pixel belongs to a triangle when its centre (x+0.5, y+0.5) is inside; shared edges use a fixed tie rule so every
centre is claimed at most once. At rest the renderer draws each layer group's pixels exactly from the image."""
import json, os
import numpy as np

def load(path):
    j = json.load(open(path))
    tris = j['triangles']; lay = j.get('triangleLayers')
    T = np.array([t[:3] for t in tris], np.int64)
    L = np.array([t[3] if len(t) > 3 else (lay[i] if lay else j.get('layer', 220)) for i, t in enumerate(tris)], np.int64)
    V = np.array(j['vertices'], float)
    return j, V, T, L

def validate(j, V, T):
    errs = []
    nb = len(j['bones'])
    names = {b['name'] for b in j['bones']}
    for b in j['bones']:
        if b.get('parent') not in (None, '') and b['parent'] not in names: errs.append(f"bone {b['name']}: unknown parent {b['parent']}")
    if len(j['weights']) != len(V): errs.append(f"weights {len(j['weights'])} != vertices {len(V)}")
    for i, wl in enumerate(j['weights']):
        if not (1 <= len(wl) <= 4): errs.append(f'vertex {i}: {len(wl)} influences'); break
        if any(not (0 <= k < nb) for k, _ in wl): errs.append(f'vertex {i}: bad bone index'); break
        if abs(sum(w for _, w in wl) - 1) > 1e-3: errs.append(f'vertex {i}: weights sum {sum(w for _, w in wl):.4f}'); break
    if T.size and (T.min() < 0 or T.max() >= len(V)): errs.append('triangle index out of range')
    return errs

def coverage(V, T, L, W, H):
    """Returns (layerMap int32 HxW, -1 = uncovered; count HxW)."""
    lm = np.full((H, W), -1, np.int32); cnt = np.zeros((H, W), np.int16)
    P = V[T]  # n,3,2
    for (a, b, c), l in zip(P, L):
        area = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if area == 0: continue
        if area < 0: b, c = c, b
        x0 = max(0, int(np.floor(min(a[0], b[0], c[0])))); x1 = min(W - 1, int(np.ceil(max(a[0], b[0], c[0]))))
        y0 = max(0, int(np.floor(min(a[1], b[1], c[1])))); y1 = min(H - 1, int(np.ceil(max(a[1], b[1], c[1]))))
        if x1 < x0 or y1 < y0: continue
        ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1]; px = xs + 0.5; py = ys + 0.5
        inside = np.ones(px.shape, bool)
        for (p, q) in ((a, b), (b, c), (c, a)):
            dx, dy = q[0] - p[0], q[1] - p[1]
            e = dx * (py - p[1]) - dy * (px - p[0])
            tie = (dy > 0) or (dy == 0 and dx < 0)
            inside &= (e > 0) | ((e == 0) & tie)
        lm[ys[inside], xs[inside]] = l; cnt[ys[inside], xs[inside]] += 1
    return lm, cnt

def skin_path(view_dir, view, root, which=None, declared=None):
    """which='draft' -> rig/skin_tools/drafts/<view>_skin.json; which=<file> -> views/<view>/body/<file>;
    otherwise the file declared in body/rig.json "skin" (e.g. "skin.json"), or None when not declared (same rule as index.html)"""
    if which == 'draft': return f'{root}/rig/skin_tools/drafts/{view}_skin.json'
    if which and which.startswith('draft:'):
        if which[6:].startswith(view + '_'): return f'{root}/rig/skin_tools/drafts/{which[6:]}'
        which = None  # a named draft applies only to its own view (<view>_*.json)
    if which == 'off': return None
    if which: return f'{view_dir}/body/{which}'
    if isinstance(declared, str) and declared: return f'{view_dir}/body/{declared}'
    return None

# ---------------- v1.5 underlay ----------------
# "underlay": { "image": png (relative to views/<view>/, W×H), "layer"?: int (default: just below the lowest main group),
#               own mesh: "vertices", "triangles" ([i,j,k]), "weights" (main bone indices)  -- or reuse the main mesh topology --
#               "uvs"?: [[u,v] in image px per vertex] (default: the rest position) }
# Rest rule: every pixel the underlay would draw at rest must lie under a main-skin pixel with alpha 255 drawn above it
# (main group layer > underlay layer). Otherwise the underlay is rejected (warning) and not drawn.

def underlay_load(j, V, T, L, view_dir, W, H):
    """Returns (ul dict or None, errors list). ul: {img(HxWx4 uint8), V, T, UV, weights, layer, own, identityUV, file}"""
    u = j.get('underlay')
    if u is None: return None, []
    errs = []
    if not isinstance(u, dict) or not isinstance(u.get('image'), str): return None, ['underlay: "image" missing']
    p = os.path.normpath(os.path.join(view_dir, u['image']))
    if not os.path.exists(p): return None, [f'underlay: image {u["image"]} missing']
    from PIL import Image
    im = np.array(Image.open(p).convert('RGBA'))
    if im.shape[:2] != (H, W): return None, [f'underlay: image is {im.shape[1]}x{im.shape[0]}, not {W}x{H}']
    own = 'vertices' in u or 'triangles' in u or 'weights' in u
    nb = len(j['bones'])
    if own:
        try:
            UVt = np.array(u['vertices'], float); UT = np.array([t[:3] for t in u['triangles']], np.int64); UW = u['weights']
        except Exception as e: return None, [f'underlay: own mesh needs vertices, triangles, weights ({e})']
        if UVt.ndim != 2 or UVt.shape[1] != 2: errs.append('underlay: vertices must be [x,y]')
        if len(UW) != len(UVt): errs.append(f'underlay: weights {len(UW)} != vertices {len(UVt)}')
        if UT.size and (UT.min() < 0 or UT.max() >= len(UVt)): errs.append('underlay: triangle index out of range')
        for i, wl in enumerate(UW):
            if not (1 <= len(wl) <= 4) or any(not (0 <= k < nb) for k, _ in wl) or abs(sum(w for _, w in wl) - 1) > 1e-3:
                errs.append(f'underlay: vertex {i}: bad weights'); break
        Vu, Tu = UVt, UT
    else:
        Vu, Tu, UW = V, T, j['weights']
    uv = u.get('uvs')
    if uv is not None:
        UV = np.array(uv, float)
        if UV.shape != Vu.shape: errs.append(f'underlay: uvs {UV.shape} must match vertices {Vu.shape}'); UV = Vu
    else: UV = Vu
    minL = int(L.min()) if L.size else 220
    lay = u.get('layer')
    if lay is None: layer = minL - 0.5
    elif not (isinstance(lay, int) and 200 <= lay <= 299): errs.append(f'underlay: layer {lay} not an integer in the body band'); layer = minL - 0.5
    else: layer = lay
    if errs: return None, errs
    return {'img': im, 'V': Vu, 'T': Tu, 'UV': UV, 'weights': UW, 'layer': layer, 'own': own,
            'identityUV': bool(np.array_equal(UV, Vu)), 'file': p}, []

def underlay_footprint(ul, W, H):
    """Conservative rest footprint: pixel centres inside or on the edge of any triangle whose sampled underlay alpha > 0
    (identity UVs: that pixel; custom UVs: any of the 4 texels around the interpolated UV)."""
    V, T, UV, A = ul['V'], ul['T'], ul['UV'], ul['img'][..., 3]
    fp = np.zeros((H, W), bool); ident = ul['identityUV']
    for t in T:
        a, b, c = V[t[0]], V[t[1]], V[t[2]]
        area = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if area == 0: continue
        x0 = max(0, int(np.floor(min(a[0], b[0], c[0])))); x1 = min(W - 1, int(np.ceil(max(a[0], b[0], c[0]))))
        y0 = max(0, int(np.floor(min(a[1], b[1], c[1])))); y1 = min(H - 1, int(np.ceil(max(a[1], b[1], c[1]))))
        if x1 < x0 or y1 < y0: continue
        ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1]; px = xs + 0.5; py = ys + 0.5
        l1 = ((b[1] - c[1]) * (px - c[0]) + (c[0] - b[0]) * (py - c[1])) / ((b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1]))
        l2 = ((c[1] - a[1]) * (px - c[0]) + (a[0] - c[0]) * (py - c[1])) / ((b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1]))
        l3 = 1 - l1 - l2; eps = -1e-9
        ins = (l1 >= eps) & (l2 >= eps) & (l3 >= eps)
        if not ins.any(): continue
        yy, xx = ys[ins], xs[ins]
        if ident: hit = A[yy, xx] > 0
        else:
            ua, ub, uc = UV[t[0]], UV[t[1]], UV[t[2]]
            u_ = l1[ins] * ua[0] + l2[ins] * ub[0] + l3[ins] * uc[0] - 0.5; v_ = l1[ins] * ua[1] + l2[ins] * ub[1] + l3[ins] * uc[1] - 0.5
            hit = np.zeros(len(yy), bool)
            for ox in (0, 1):
                for oy in (0, 1):
                    tx = np.clip(np.floor(u_).astype(int) + ox, 0, W - 1); ty = np.clip(np.floor(v_).astype(int) + oy, 0, H - 1)
                    hit |= A[ty, tx] > 0
        fp[yy[hit], xx[hit]] = True
    return fp

def underlay_check(ul, main_img, layer_map, W, H):
    """Returns dict with counts; ok when the rest footprint lies entirely under main pixels with alpha 255 drawn above it."""
    fp = underlay_footprint(ul, W, H); a = main_img[..., 3]
    above = layer_map > ul['layer']            # -1 (uncovered) is never above
    transparent = fp & ((a == 0) | (layer_map < 0))
    partial = fp & (a > 0) & (a < 255) & (layer_map >= 0)
    below = fp & (a == 255) & (layer_map >= 0) & ~above
    r = {'footprintPx': int(fp.sum()), 'touchTransparent': int(transparent.sum()), 'touchPartialAlpha': int(partial.sum()),
         'touchNotAbove': int(below.sum()), 'layer': ul['layer']}
    r['ok'] = r['touchTransparent'] == 0 and r['touchPartialAlpha'] == 0 and r['touchNotAbove'] == 0
    return r, fp, transparent | partial | below
