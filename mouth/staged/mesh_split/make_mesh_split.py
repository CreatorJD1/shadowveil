#!/usr/bin/env python3
"""Staged upper/lower lip + interior split for a future mesh mouth (NOT live).
Every output pixel is copied from views/<v>/base.png (lips) or views/<v>/mouth/AA.png (interior).
Usage: make_mesh_split.py [view ...]   (default: apose tpose)"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import label, binary_fill_holes

ROOT = '/workspace/shadowveil'
W, H = 1365, 1739
T_SEAM = 43          # luminance threshold: midpoint of line #220C00 (L~17) and lower lip #633B22 (L~69)
FLAP = 2             # flap height in px
BLUE = (0, 0, 255, 255)

def lum(a): return (a[..., 0]*299 + a[..., 1]*587 + a[..., 2]*114) // 1000

def hexc(s): return np.array([int(s[i:i+2], 16) for i in (1, 3, 5)])

def run(v):
    vd = f'{ROOT}/views/{v}'; out = f'{ROOT}/mouth/staged/mesh_split/{v}'; os.makedirs(out, exist_ok=True)
    rj = json.load(open(f'{vd}/mouth/rig.json'))
    ax, ay = rj['anchor']['x'], rj['anchor']['y']
    base = np.array(Image.open(f'{vd}/base.png').convert('RGBA'))
    R = np.array(Image.open(f'{vd}/mouth/rest.png').convert('RGBA'))[..., 3] > 0
    assert (np.array(Image.open(f'{vd}/mouth/rest.png').convert('RGBA'))[R] == base[R]).all()
    L = lum(base.astype(int))
    xs_r = np.nonzero(R.any(0))[0]
    y_lo, y_hi = ay - 6, ay + 3
    # ---- seam per column: darkest pixel in band, then the contiguous dark run (L<T) around it
    seam_top, seam_bot, seam_c, dark_cols = {}, {}, {}, []
    for x in xs_r:
        ys = [y for y in range(y_lo, y_hi+1) if R[y, x]]
        if not ys: continue
        ym = min(ys, key=lambda y: (L[y, x], abs(y-ay)))
        if L[ym, x] < T_SEAM:
            t = b = ym
            while t-1 >= y_lo and R[t-1, x] and L[t-1, x] < T_SEAM: t -= 1
            while b+1 <= y_hi and R[b+1, x] and L[b+1, x] < T_SEAM: b += 1
            seam_top[x], seam_bot[x] = t, b; dark_cols.append(int(x))
        else:
            seam_top[x] = seam_bot[x] = None
        seam_c[x] = ym
    # columns without a dark seam pixel: take the nearest dark column's seam (corner extension / gaps)
    gap_cols = []
    for x in xs_r:
        if seam_bot.get(x) is None:
            near = min(dark_cols, key=lambda d: abs(d-x))
            seam_top[x], seam_bot[x] = seam_top[near], seam_bot[near]; gap_cols.append(int(x))
    yy = np.arange(H)[:, None]
    sb = np.full(W, -1); st = np.full(W, -1)
    for x in xs_r: sb[x] = seam_bot[x]; st[x] = seam_top[x]
    upper_m = R & (yy <= sb[None, :])
    lower_m = R & (yy > sb[None, :])
    assert not (upper_m & lower_m).any() and ((upper_m | lower_m) == R).all()
    # lip columns = columns where both parts carry real lip (not just skin margin) next to the seam
    lip_cols = [x for x in dark_cols if R[sb[x]+1, x] and R[st[x]-1, x]]
    # ---- flaps
    upper = np.zeros_like(base); lower = np.zeros_like(base)
    upper[upper_m] = base[upper_m]; lower[lower_m] = base[lower_m]
    lflap = np.zeros((H, W), bool); uflap = np.zeros((H, W), bool)
    for x in lip_cols:
        src = base[sb[x]+1, x]                       # lower lip's top pixel in this column (her colour)
        for k in range(FLAP):
            y = sb[x] - k
            if upper_m[y, x]:
                lower[y, x] = src; lflap[y, x] = True  # hidden under upper's opaque seam/lip pixels
        for k in range(1, FLAP+1):
            y = sb[x] + k
            if lower_m[y, x]:
                upper[y, x] = base[y, x]; uflap[y, x] = True   # coincident copy of the lower lip's top rows
    # ---- interior from AA.png: cavity enclosed by the AA lips
    aa = np.array(Image.open(f'{vd}/mouth/AA.png').convert('RGBA'))
    C = rj['colors']
    pal = {k: hexc(C[k]) for k in ['skin', 'upper', 'lower', 'line', 'hl', 'inner', 'teeth', 'tongue']}
    names = list(pal); P = np.stack([pal[k] for k in names])
    d = ((aa[..., None, :3].astype(int) - P[None, None])**2).sum(-1)
    near = np.array(names)[d.argmin(-1)]
    cav_cand = (aa[..., 3] == 255) & np.isin(near, ['inner', 'teeth', 'tongue', 'hl'])  # hl = teeth-strip AA blends
    lab, n = label(cav_cand, structure=np.ones((3, 3)))
    # seed: the biggest component touching the inner colour below the anchor
    sizes = [(lab == i).sum() for i in range(1, n+1)]
    comp = 1 + int(np.argmax(sizes))
    cav = lab == comp
    cav = binary_fill_holes(cav) & (aa[..., 3] == 255)
    interior = np.zeros_like(aa); interior[cav] = aa[cav]
    cnt = {k: int((cav & (near == k)).sum()) for k in names if (cav & (near == k)).sum()}
    teeth_rows = sorted(set(np.nonzero(cav & (near == 'teeth'))[0].tolist()))
    # ---- save
    Image.fromarray(upper, 'RGBA').save(f'{out}/upper_lip.png')
    Image.fromarray(lower, 'RGBA').save(f'{out}/lower_lip.png')
    Image.fromarray(interior, 'RGBA').save(f'{out}/interior.png')
    # provenance check: every opaque pixel is a pixel colour from her art
    lipcols = {tuple(c) for c in base[R]}
    assert all(tuple(c) in lipcols for c in upper[upper[..., 3] > 0])
    assert all(tuple(c) in lipcols for c in lower[lower[..., 3] > 0])
    assert (interior[cav] == aa[cav]).all()
    # ---- 0 px proof: composite lower then upper (upper on top) over base
    def over(dst, src):
        a = src[..., 3:4].astype(float)/255; o = dst.astype(float)
        o[..., :3] = src[..., :3]*a + o[..., :3]*(1-a)
        o[..., 3:4] = a*255 + o[..., 3:4]*(1-a)
        return np.rint(o).astype(np.uint8)
    comp_ul = over(over(base, lower), upper)
    diff_ul = int((comp_ul != base).any(-1).sum())
    comp_lu = over(over(base, upper), lower)               # reverse order for information
    diff_lu = int((comp_lu != base).any(-1).sum())
    lflap_hidden = bool((upper[lflap][:, 3] == 255).all())
    interior_uncovered = int((cav & ~R).sum())
    # ---- geometry
    def bbox(m):
        ys, xs = np.nonzero(m); return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    seam_x = sorted(dark_cols)
    centre = {x: (st[x]+sb[x])/2 for x in xs_r}
    pts = []
    for x in [int(xs_r.min())] + list(range(int(xs_r.min())+2, int(xs_r.max())-1, 3)) + [int(xs_r.max())]:
        pts.append([x, round(float(centre[x]) + 0.5, 1)])   # +0.5 = pixel-centre y in view px
    seam_lower_edge = [[int(x), int(sb[x]) + 1] for x in xs_r]  # boundary line (first lower-lip row)
    ub, lb, ib = bbox(upper[..., 3] > 0), bbox(lower[..., 3] > 0), bbox(cav)
    lc = [min(seam_x), max(seam_x)]
    parts = {
        'status': 'STAGED - not live, not referenced by rig/ or views/*/mouth/rig.json',
        'view': v, 'canvas': {'width': W, 'height': H}, 'anchor': rj['anchor'],
        'source': {'lips': f'views/{v}/base.png (located by views/{v}/mouth/rest.png alpha)',
                   'interior': f'views/{v}/mouth/AA.png'},
        'drawOrder': ['interior', 'lower_lip', 'upper_lip'],
        'seam': {
            'rule': f'per column: darkest pixel in rows {y_lo}..{y_hi}, extended to its contiguous run with luminance < {T_SEAM}; the whole dark run goes to upper_lip',
            'polyline_centre': pts,
            'boundary_firstLowerRow': seam_lower_edge,
            'darkSeamColumns': [min(seam_x), max(seam_x)],
            'columnsWithoutDarkSeam_extended': gap_cols,
        },
        'parts': {
            'upper_lip': {'file': 'upper_lip.png', 'bbox': ub, 'opaquePx': int((upper[..., 3] > 0).sum()),
                          'flap': {'px': int(uflap.sum()), 'rows': f'{FLAP} px below the seam',
                                   'kind': 'coincident: exact copy of the lower lip pixels it covers, so it is invisible at rest whichever part is on top; shows as lower-lip colour under the line only if lips separate before the interior appears'},
                          'bendAxes': [
                              {'name': 'seam_arc', 'type': 'polyline', 'points': pts, 'use': 'MouthForm: bend corners up (smile) / down (frown) about the seam; keep the seam row rigid against lower_lip'},
                              {'name': 'centre_vertical', 'type': 'line', 'points': [[ax, ub[1]], [ax, ub[3]]], 'use': 'pucker/OH: squeeze width toward x=%d' % ax},
                              {'name': 'lift', 'type': 'line', 'points': [[lc[0], ay], [lc[1], ay]], 'use': 'MouthOpen: translate up ~1-2 px max, pivot at corners (%d,%d)-(%d,%d)' % (lc[0], sb[lc[0]], lc[1], sb[lc[1]])}]},
            'lower_lip': {'file': 'lower_lip.png', 'bbox': lb, 'opaquePx': int((lower[..., 3] > 0).sum()),
                          'flap': {'px': int(lflap.sum()), 'rows': f'{FLAP} px above the seam boundary',
                                   'kind': 'hidden: lower lip top-row colour (per column) extended up under upper_lip opaque pixels', 'fullyCoveredByUpper': lflap_hidden},
                          'bendAxes': [
                              {'name': 'seam_arc', 'type': 'polyline', 'points': [[x, y] for x, y in seam_lower_edge[::3]], 'use': 'MouthForm: corners follow upper seam_arc'},
                              {'name': 'centre_vertical', 'type': 'line', 'points': [[ax, lb[1]], [ax, lb[3]]], 'use': 'pucker/OH squeeze'},
                              {'name': 'drop', 'type': 'line', 'points': [[lc[0], int(sb[lc[0]])+1], [lc[1], int(sb[lc[1]])+1]], 'use': 'MouthOpen: hinge at the corners, centre drops most (jaw)'}]},
            'interior': {'file': 'interior.png', 'bbox': ib, 'opaquePx': int(cav.sum()), 'colourCounts': cnt,
                         'teethRows': teeth_rows,
                         'pxOutsideRestLips': interior_uncovered,
                         'note': 'cavity of AA.png (inner dark + teeth strip + tongue) at AA geometry; set opacity 0 at MouthOpen=0 or clip to the gap between lips',
                         'bendAxes': [
                             {'name': 'open_stretch', 'type': 'line', 'points': [[ax, ib[1]], [ax, ib[3]]], 'use': 'MouthOpen: scale vertically from the top edge (teeth stay under upper lip)'},
                             {'name': 'width', 'type': 'line', 'points': [[ib[0], (ib[1]+ib[3])//2], [ib[2], (ib[1]+ib[3])//2]], 'use': 'MouthForm: widen (EE) / narrow (OH)'}]},
        },
        'proof': {'upper_over_lower_over_base_changed_px': diff_ul,
                  'lower_over_upper_over_base_changed_px': diff_lu,
                  'upper_union_lower_equals_rest_mask': True},
    }
    json.dump(parts, open(f'{out}/parts.json', 'w'), indent=1)
    # ---- contact sheet, 8x, chroma blue
    Z = 8; x0, y0, x1, y1 = ib[0]-0, 0, 0, 0
    x0 = min(ub[0], lb[0], ib[0]) - 4; x1 = max(ub[2], lb[2], ib[2]) + 5
    y0 = min(ub[1], ib[1]) - 4; y1 = max(lb[3], ib[3]) + 5
    def crop(a): return a[y0:y1, x0:x1]
    def on_blue(a):
        bg = np.zeros((y1-y0, x1-x0, 4), np.uint8); bg[:] = BLUE
        return over(bg, crop(a))
    def zoom(a): return Image.fromarray(a, 'RGBA').resize(((x1-x0)*Z, (y1-y0)*Z), Image.NEAREST)
    gap = 4; hh = y1 - y0 + 2*gap
    ex = np.zeros((hh, x1-x0, 4), np.uint8); ex[:] = BLUE
    def paste(dst, src, dy):
        c = crop(src); a = c[..., 3:4].astype(float)/255
        reg = dst[gap+dy:gap+dy+c.shape[0]]
        reg[..., :3] = np.rint(c[..., :3]*a + reg[..., :3]*(1-a)).astype(np.uint8)
    paste(ex, interior, 0); paste(ex, lower, gap); paste(ex, upper, -gap)
    diffimg = np.zeros((y1-y0, x1-x0, 4), np.uint8); diffimg[:] = BLUE
    dm = crop((comp_ul != base).any(-1)); diffimg[dm] = (255, 0, 0, 255)
    tiles = [('base.png rest lips', on_blue(base * R[..., None].astype(np.uint8))),
             ('upper_lip (+coincident flap)', on_blue(upper)),
             ('lower_lip (+hidden flap)', on_blue(lower)),
             ('interior (from AA.png)', on_blue(interior)),
             ('exploded: upper -%dpx, lower +%dpx' % (gap, gap), ex),
             ('recomposite lower+upper', on_blue(over(lower, upper))),
             ('recomposite over base.png', crop(comp_ul)),
             ('diff vs base: %d px changed' % diff_ul, diffimg)]
    imgs = [(t, zoom(a)) for t, a in tiles]
    tw = max(i.width for _, i in imgs); th = max(i.height for _, i in imgs)
    cols = 2; rows = (len(imgs)+1)//cols; pad = 24
    sheet = Image.new('RGB', (cols*(tw+pad)+pad, rows*(th+pad+18)+pad+30), (40, 40, 40))
    dr = ImageDraw.Draw(sheet)
    dr.text((pad, 8), f'Shadowveil {v} mesh_split (STAGED) - 8x, chroma #0000FF, crop x{x0}-{x1-1} y{y0}-{y1-1}; seam polyline in parts.json', fill=(255, 255, 255))
    for i, (t, im) in enumerate(imgs):
        cx = pad + (i % cols)*(tw+pad); cy = 30 + pad + (i//cols)*(th+pad+18)
        dr.text((cx, cy), t, fill=(255, 255, 255))
        sheet.paste(im.convert('RGB'), (cx, cy+16))
    sheet.save(f'{out}/sheet.png')
    print(v, 'diff upper-on-top', diff_ul, 'reverse', diff_lu, 'lflap hidden', lflap_hidden,
          'bbox U/L/I', ub, lb, ib, 'flaps', int(uflap.sum()), int(lflap.sum()), 'gap cols', gap_cols,
          'interior px', int(cav.sum()), cnt, 'teeth rows', teeth_rows, 'interior outside rest', interior_uncovered)

for v in (sys.argv[1:] or ['apose', 'tpose']): run(v)
