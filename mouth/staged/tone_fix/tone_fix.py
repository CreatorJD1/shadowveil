#!/usr/bin/env python3
"""Snap live mouth shapes to her exact base.png palette (staged copies only).
Reads views/<v>/base.png, views/<v>/mouth/*.png, mouth/handoff_hairless/<v>_mouth_lock.png.
Writes only under mouth/staged/tone_fix/."""
import os, json, glob, hashlib, colorsys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = '/workspace/shadowveil'
OUT = os.path.join(ROOT, 'mouth/staged/tone_fix')
VIEWS = ['apose', 'tpose', 'left', 'right']
MAXD = 5          # max Chebyshev change (levels)
DIL = 10          # px dilation of the mouth region (Chebyshev, 21x21 square)
LINE_LUMA = 32    # luma < 32 = line-art tone; a snap may not cross this
NEUTRAL_RANGE = 12  # max-min < 12 = neutral (hue undefined)

def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def load(p): return np.array(Image.open(p).convert('RGBA')).astype(np.int16)

def hue_class(c):
    r, g, b = [int(x) for x in c]
    if max(r, g, b) - min(r, g, b) < NEUTRAL_RANGE: return 'neutral'
    h = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[0] * 360
    if h >= 345 or h < 60: return 'warm'          # red/orange/brown/skin/lip
    if h < 170: return 'green'
    if h < 260: return 'blue'                     # includes key blue #0000FF
    return 'purple'                               # plum/magenta
def is_line(c): return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] < LINE_LUMA
def kind(c): return (hue_class(c), 'line' if is_line(c) else 'fill')
def keyblue_mask(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (a[..., 3] > 0) & (b >= 200) & (r <= 60) & (g <= 60)

def line_width_stats(a):
    """per line pixel: min(horizontal run, vertical run) of opaque line pixels."""
    m = (a[..., 3] == 255) & (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2] < LINE_LUMA)
    def runs(mm):
        out = np.zeros(mm.shape, int)
        for i, row in enumerate(mm):
            j = 0; n = len(row)
            while j < n:
                if row[j]:
                    k = j
                    while k < n and row[k]: k += 1
                    out[i, j:k] = k - j; j = k
                else: j += 1
        return out
    w = np.minimum(runs(m), runs(m.T).T)[m]
    if w.size == 0: return {'line_px': 0}
    return {'line_px': int(m.sum()), 'median_width': float(np.median(w)),
            'pct_width1': round(100 * float((w == 1).mean()), 1), 'max_width': int(w.max())}, m

def cheb_nearest(px, P):
    d = np.full(len(px), 999); idx = np.zeros(len(px), int)
    for i in range(0, len(P), 1500):
        dd = np.abs(px[:, None, :] - P[None, i:i + 1500, :]).max(2)
        j = dd.argmin(1); v = dd[np.arange(len(px)), j]
        better = v < d; d[better] = v[better]; idx[better] = j[better] + i
    return d, idx

log = {'params': {'max_change_levels': MAXD, 'metric': 'Chebyshev (max |dR|,|dG|,|dB|)',
                  'region': f'(rest.png alpha OR handoff_hairless/<view>_mouth_lock.png) dilated {DIL} px (Chebyshev), opaque base.png pixels only',
                  'kind': f'hue class (neutral if max-min<{NEUTRAL_RANGE}; warm [345,60) deg; green [60,170); blue [170,260); purple [260,345)) + line band (luma<{LINE_LUMA} = line). Snap must keep both.',
                  'already_exact': 'pixels whose colour is already an exact opaque base.png colour (anywhere) are left as is',
                  'alpha': 'never changed; partially transparent pixels (0<a<255) left untouched'},
       'views': {}}
sheets = []
for v in VIEWS:
    vd = os.path.join(ROOT, 'views', v)
    base = load(f'{vd}/base.png')
    bop = base[..., 3] == 255
    gpal = np.unique(base[bop][:, :3], axis=0)
    gset = set(map(tuple, gpal.tolist()))
    rest = load(f'{vd}/mouth/rest.png')
    lock = np.array(Image.open(f'{ROOT}/mouth/handoff_hairless/{v}_mouth_lock.png').convert('L')) > 127
    region = ndimage.binary_dilation((rest[..., 3] > 0) | lock, np.ones((2 * DIL + 1, 2 * DIL + 1), bool)) & bop
    lpal = np.unique(base[region][:, :3], axis=0)
    lkind = [kind(c) for c in lpal]
    os.makedirs(f'{OUT}/views/{v}/mouth', exist_ok=True)
    Image.fromarray((region * 255).astype(np.uint8)).save(f'{OUT}/views/{v}/palette_region.png')
    # rest check
    rop = rest[..., 3] > 0
    rest_diff = int((np.abs(rest[rop] - base[rop]).max(1) > 0).sum())
    V = {'global_palette_tones': len(gpal), 'local_palette_tones': len(lpal), 'region_px': int(region.sum()),
         'rest': {'opaque_px': int(rop.sum()), 'px_differing_from_base': rest_diff, 'sha256': sha(f'{vd}/mouth/rest.png'),
                  'staged': False}, 'shapes': {}}
    ys, xs = np.nonzero(lock | rop)
    crop = (max(xs.min() - 8, 0), max(ys.min() - 8, 0), xs.max() + 9, ys.max() + 9)
    rows = []
    for f in sorted(glob.glob(f'{vd}/mouth/*.png')):
        s = os.path.basename(f)[:-4]
        if s == 'rest': continue
        a = load(f)
        op = a[..., 3] == 255; part = (a[..., 3] > 0) & (a[..., 3] < 255)
        yy, xx = np.nonzero(op); px = a[op][:, :3]
        dg, _ = cheb_nearest(px, gpal); dl, il = cheb_nearest(px, lpal)
        rec = {'opaque_px': int(op.sum()), 'partial_alpha_px_untouched': int(part.sum()),
               'before': {'off_palette_px': int((dg > 0).sum()), 'gt5_px': int((dg > 5).sum()), 'max_dist': int(dg.max()),
                          'dist_hist': {str(k): int((dg == k).sum()) for k in range(1, int(dg.max()) + 1) if (dg == k).any()}},
               'keyblue_px_before': int(keyblue_mask(a).sum())}
        lw0, lm0 = line_width_stats(a)
        if s == 'anger':
            rec['note'] = 'APPROVED Clean room art: not changed, not staged; numbers only'
            rec['local_off_px'] = int((dl > 0).sum()); rec['local_gt5_px'] = int((dl > 5).sum())
            rec['hue_classes'] = {}
            for c in px.tolist():
                k = '/'.join(kind(c)); rec['hue_classes'][k] = rec['hue_classes'].get(k, 0) + 1
            rec['line_width'] = lw0
            V['shapes'][s] = rec; continue
        out = a.copy()
        snapped = []; unsnapped = []; exact_global_not_local = 0
        for i in range(len(px)):
            c = tuple(px[i].tolist()); y, x = int(yy[i]), int(xx[i])
            if dg[i] == 0:
                if dl[i] > 0: exact_global_not_local += 1
                continue
            k = kind(c)
            # candidates: local tones within MAXD and same kind
            dd = np.abs(lpal - px[i]).max(1)
            ok = np.nonzero(dd <= MAXD)[0]
            same = [j for j in ok if lkind[j] == k]
            if same:
                best = min(same, key=lambda j: (dd[j], int(((lpal[j] - px[i]) ** 2).sum())))
                t = tuple(lpal[best].tolist()); out[y, x, :3] = lpal[best]
                snapped.append({'x': x, 'y': y, 'from': c, 'to': t, 'd': int(dd[best])})
            else:
                reason = 'gt5_from_local_palette' if len(ok) == 0 else 'kind_change'
                nj = int(il[i])
                unsnapped.append({'x': x, 'y': y, 'rgb': c, 'hex': '#%02x%02x%02x' % c, 'reason': reason,
                                  'kind': '/'.join(k), 'nearest_local': tuple(lpal[nj].tolist()), 'nearest_local_d': int(dl[i]),
                                  'nearest_local_kind': '/'.join(lkind[nj]), 'nearest_global_d': int(dg[i])})
        assert (out[..., 3] == a[..., 3]).all()
        assert (out[part] == a[part]).all()
        Image.fromarray(out.astype(np.uint8), 'RGBA').save(f'{OUT}/views/{v}/mouth/{s}.png')
        chk = load(f'{OUT}/views/{v}/mouth/{s}.png')
        cp = chk[op][:, :3]
        exact_after = sum(1 for c in map(tuple, cp.tolist()) if c in gset)
        lw1, lm1 = line_width_stats(chk)
        ds = [p['d'] for p in snapped]
        rec.update({'snapped_px': len(snapped), 'left_unsnapped_px': len(unsnapped),
                    'unsnapped_gt5': sum(u['reason'] == 'gt5_from_local_palette' for u in unsnapped),
                    'unsnapped_kind_change': sum(u['reason'] == 'kind_change' for u in unsnapped),
                    'max_change': max(ds) if ds else 0,
                    'change_hist': {str(k): ds.count(k) for k in sorted(set(ds))},
                    'already_exact_global_not_in_local_region': exact_global_not_local,
                    'after': {'exact_palette_px': exact_after, 'off_palette_px': int(op.sum()) - exact_after},
                    'alpha_identical': bool((chk[..., 3] == a[..., 3]).all()),
                    'partial_pixels_identical': bool((chk[part] == a[part]).all()),
                    'keyblue_px_after': int(keyblue_mask(chk).sum()),
                    'new_keyblue_px': int((keyblue_mask(chk) & ~keyblue_mask(a)).sum()),
                    'line_width_before': lw0, 'line_width_after': lw1,
                    'line_mask_identical': bool((lm0 == lm1).all()),
                    'source_sha256': sha(f), 'staged_sha256': sha(f'{OUT}/views/{v}/mouth/{s}.png'),
                    'unsnapped': unsnapped, 'snapped': snapped})
        V['shapes'][s] = rec
        rows.append((s, a, chk, snapped, unsnapped, part))
    log['views'][v] = V
    # ---- sheet for this view
    Z = 6; x0, y0, x1, y1 = crop; W, H = (x1 - x0) * Z, (y1 - y0) * Z
    def comp(arr):
        im = Image.fromarray(base[y0:y1, x0:x1].astype(np.uint8), 'RGBA')
        im.alpha_composite(Image.fromarray(arr[y0:y1, x0:x1].astype(np.uint8), 'RGBA'))
        return im.resize((W, H), Image.NEAREST)
    def hl(arr, sn, un, part):
        g = comp(arr).convert('L').point(lambda p: p // 3 + 60).convert('RGBA')
        d = ImageDraw.Draw(g)
        for (yy_, xx_) in zip(*np.nonzero(part[y0:y1, x0:x1])):
            d.rectangle([xx_ * Z, yy_ * Z, xx_ * Z + Z - 1, yy_ * Z + Z - 1], outline=(255, 220, 0, 255))
        cols = {1: (0, 200, 255), 2: (0, 255, 120), 3: (255, 160, 0), 4: (255, 90, 0), 5: (255, 0, 200)}
        for p in sn:
            X, Y = (p['x'] - x0) * Z, (p['y'] - y0) * Z
            d.rectangle([X, Y, X + Z - 1, Y + Z - 1], fill=cols[p['d']] + (255,))
        for p in un:
            X, Y = (p['x'] - x0) * Z, (p['y'] - y0) * Z
            d.rectangle([X, Y, X + Z - 1, Y + Z - 1], fill=(255, 0, 0, 255), outline=(255, 255, 255, 255))
        return g
    pad = 10; lab = 18
    sheet = Image.new('RGBA', (3 * W + 4 * pad, len(rows) * (H + lab + pad) + 60), (30, 30, 34, 255))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 6), f'{v}: before (live) | after (staged tone_fix) | changes. Zoom {Z}x, crop x{x0}-{x1-1} y{y0}-{y1-1}', fill='white')
    d.text((pad, 22), 'snap d=1 cyan, 2 green, 3 orange, 4 dark orange, 5 magenta; RED = left unsnapped; yellow outline = partial alpha (untouched)', fill='white')
    d.text((pad, 38), 'anger not shown (approved art, unchanged). rest not staged (exact).', fill='white')
    for r_, (s, a, chk, sn, un, part) in enumerate(rows):
        Y = 60 + r_ * (H + lab + pad)
        d.text((pad, Y), f'{s}: snapped {len(sn)}, unsnapped {len(un)}, max d {max([p["d"] for p in sn] or [0])}', fill='white')
        sheet.paste(comp(a), (pad, Y + lab)); sheet.paste(comp(chk), (2 * pad + W, Y + lab)); sheet.paste(hl(chk, sn, un, part), (3 * pad + 2 * W, Y + lab))
    sp = f'{OUT}/sheet_{v}.png'; sheet.convert('RGB').save(sp); sheets.append(sheet)
# combined sheet (views side by side)
Wt = sum(s.width for s in sheets) + 10 * (len(sheets) - 1); Ht = max(s.height for s in sheets)
allsh = Image.new('RGB', (Wt, Ht), (30, 30, 34)); x = 0
for s in sheets: allsh.paste(s.convert('RGB'), (x, 0)); x += s.width + 10
allsh.save(f'{OUT}/sheet.png')
json.dump(log, open(f'{OUT}/tone_fix_log.json', 'w'), indent=1)
print('ok')
