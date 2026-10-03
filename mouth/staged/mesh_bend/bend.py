#!/usr/bin/env python3
"""Job A: offline Live2D-style mesh-bend prototype of the Shadowveil mouth (apose, tpose). STAGED, not live.
Sources (read-only): views/<v>/base.png, views/<v>/mouth/*.png, mouth/staged/mesh_split/<v>/*.
Every output pixel is a bilinear (premultiplied) interpolation of those pixels; nothing is painted.
Draw order (bottom->top): upper_flap, lower_flap, interior (clipped to the lip gap), lower_lip, upper_lip.
"""
import json, os, sys, copy
import numpy as np
from PIL import Image
from scipy.ndimage import label, binary_fill_holes
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mb import *

HERE = f'{ROOT}/mouth/staged/mesh_bend'
T_SEAM = 43          # same seam threshold as make_mesh_split.py
FLAP = 2
INTERIOR_FILL = True # close the staged interior's per-column notches with the AA.png pixels there
P_MAX = 6.0          # upper bound for the fitted corner-curl exponent
T_BAND = 43          # luminance limit for the rigid line band (set per run; 43 = seam rule only)
PAD = 3              # px of base.png skin padded around the rest lips (set 0 to disable)
OPENS = [0, .25, .5, .75, 1]
FORMS = [-1, -.5, 0, .5, 1]
HER = {(0, 0): 'rest', (0, -1): 'M', (0, 1): 'smile', (.5, -1): 'OH_half', (.5, 0): 'AA_half', (.5, 1): 'EE_half',
       (1, -1): 'OH', (1, 0): 'AA', (1, 1): 'EE'}
CALIB_SHAPES = {'AA_half', 'AA', 'M', 'smile'}   # shapes the controls are calibrated against

DEFAULT_CFG = dict(mesh='strip', sx=1, sy=2, bands=True, pins=True, flaps='own_layers', clip_ext=1.0,
                   minfill=0.25, open_profile='her', press=True, corner_dx=True, interior_tuck=1.5, interior_xover=2.0)

# ====================================================================== view data
class View:
    def __init__(s, v, pad=None, t_band=None, pad_split='seam_row', interior_fill=True):
        s.v = v
        s.pad_split, s.interior_fill = pad_split, interior_fill
        s.pad = PAD if pad is None else pad
        s.t_band = T_BAND if t_band is None else t_band
        s.rj, s.pal = palette(v)
        s.ax, s.ay = s.rj['anchor']['x'], s.rj['anchor']['y']
        s.box = (s.ax - 90, s.ay - 60, s.ax + 90, s.ay + 60)     # crop x0,y0,x1,y1 (exclusive end)
        x0, y0, x1, y1 = s.box
        s.off = (x0, y0)
        cr = lambda a: a[y0:y1, x0:x1]
        s.base_full = load_rgba(f'{ROOT}/views/{v}/base.png')
        s.base = cr(s.base_full)
        s.R = cr(load_rgba(f'{ROOT}/views/{v}/mouth/rest.png')[..., 3] > 0)
        sp = f'{ROOT}/mouth/staged/mesh_split/{v}'
        s.parts_json = json.load(open(f'{sp}/parts.json'))
        up = cr(load_rgba(f'{sp}/upper_lip.png')); lo = cr(load_rgba(f'{sp}/lower_lip.png'))
        s.interior = cr(load_rgba(f'{sp}/interior.png'))
        # fill the 1-2 px column notches of the staged interior with the AA.png pixels that sit there (her art;
        # the cavity classifier left them out as line/lip-coloured AA blends). Same pixels, holes closed per column.
        s.interior_notch_px = 0
        if s.interior_fill:
            aa = cr(load_rgba(f'{ROOT}/views/{v}/mouth/AA.png'))
            ia = s.interior[..., 3] > 0
            for c in np.nonzero(ia.any(0))[0]:
                ys = np.nonzero(ia[:, c])[0]
                for y in range(ys.min(), ys.max() + 1):
                    if not ia[y, c] and aa[y, c, 3] == 255:
                        s.interior[y, c] = aa[y, c]; s.interior_notch_px += 1
        s.sb1 = {x: y for x, y in s.parts_json['seam']['boundary_firstLowerRow']}   # canvas coords
        # ---- flap split (derived from the same pixels, make_mesh_split's rule): overlap rows below the
        # seam boundary = upper flap; overlap rows above = lower flap
        ov = (up[..., 3] > 0) & (lo[..., 3] > 0)
        yy = np.arange(y0, y1)[:, None] + np.zeros((1, x1 - x0), int)
        sbm = np.full(x1 - x0, 10 ** 6)
        for x, y in s.sb1.items(): sbm[x - x0] = y
        kx = np.array(sorted(s.sb1))
        for c in range(x1 - x0):                   # extend the boundary row past the corners (nearest column)
            if sbm[c] == 10 ** 6: sbm[c] = s.sb1[int(kx[np.argmin(np.abs(kx - (c + x0)))])]
        s.sbm = sbm
        below = yy >= sbm[None, :]
        s.uflap_m = ov & below; s.lflap_m = ov & ~below
        z = lambda a, m: np.where(m[..., None], a, 0).astype(np.uint8)
        s.layers_src = {'upper_body': z(up, (up[..., 3] > 0) & ~s.uflap_m), 'upper_flap': z(up, s.uflap_m),
                        'lower_body': z(lo, (lo[..., 3] > 0) & ~s.lflap_m), 'lower_flap': z(lo, s.lflap_m),
                        'interior': s.interior}
        ub = s.layers_src['upper_body'][..., 3] > 0; lb = s.layers_src['lower_body'][..., 3] > 0
        assert not (ub & lb).any() and ((ub | lb) == s.R).all(), 'bodies must tile the rest lips'
        cls, d = nearest_class(s.base, s.pal)
        s.core = s.R & ~((cls == 'skin') & (d < 200))
        # ---- skin pad: a PAD-px ring of base.png's own skin pixels around the rest lips, given to the nearer
        # body. Identical to base at rest (0 px), it gives every column a skin margin to stretch on the side the
        # lip moves away from (the cupid's-bow peaks have no margin inside rest.png).
        s.pad_u = s.pad_l = np.zeros_like(ub)
        if s.pad > 0:
            from scipy.ndimage import binary_dilation, distance_transform_edt
            cls0, d0 = nearest_class(s.base, s.pal)
            ring = binary_dilation(s.R, np.ones((3, 3)), iterations=s.pad) & ~s.R & (cls0 == 'skin') & (s.base[..., 3] == 255)
            if s.pad_split == 'seam_row':
                s.pad_u = ring & (yy < sbm[None, :]); s.pad_l = ring & (yy >= sbm[None, :])   # split at the seam row
            else:                                                                             # nearer body
                du = distance_transform_edt(~ub); dl = distance_transform_edt(~lb)
                s.pad_u = ring & (du <= dl); s.pad_l = ring & (dl < du)
            for k, m in (('upper_body', s.pad_u), ('lower_body', s.pad_l)):
                s.layers_src[k][m] = s.base[m]
            ub = ub | s.pad_u; lb = lb | s.pad_l
        # ---- flap variants. 'msplit' = make_mesh_split's flaps as staged (lip columns only, 2 rows, abutting
        # their owner). 'overlap' = same rule extended to every column of the padded part, plus 2 rows of the
        # owner's own pixels so the flap overlaps its owner (no partial-alpha seam between owner and flap):
        #   upper_flap rows seam-2..seam+1: upper's own pixels above the seam, byte copy of the lower lip below it
        #   lower_flap rows seam-2..seam+1: make_mesh_split's hidden lower flap (lower top-row colour extended up)
        #                                   above the seam, lower's own pixels below it
        both = ub | lb
        band_u = both & (yy >= sbm[None, :] - 2) & (yy < sbm[None, :] + FLAP)
        uf2 = np.zeros_like(s.base); uf2[band_u] = s.base[band_u]
        lf2 = np.zeros_like(s.base)
        rows_above = both & (yy >= sbm[None, :] - FLAP) & (yy < sbm[None, :])
        rows_below = both & (yy >= sbm[None, :]) & (yy < sbm[None, :] + 2)
        lf2[rows_below] = s.base[rows_below]
        top_row = s.base[np.clip(sbm - y0, 0, y1 - y0 - 1), np.arange(x1 - x0)]          # lower's top-row pixel
        rep = np.broadcast_to(top_row[None], s.base.shape)
        lf2[rows_above] = np.where(s.lflap_m[rows_above][:, None], lo[rows_above], rep[rows_above])
        s.flapsets = {'msplit': (s.layers_src['upper_flap'], s.layers_src['lower_flap']), 'overlap': (uf2, lf2)}
        s.P = {k: premul(a) for k, a in s.layers_src.items()}
        s.Pflap = {k: (premul(a), premul(b)) for k, (a, b) in s.flapsets.items()}
        # ---- per-column features (canvas coords, pixel-boundary y)
        L = lum(s.base)
        s.L = L
        s.cols = {}
        for x in sorted(s.sb1):
            c = x - x0
            Ib = s.sb1[x]
            ucol = np.nonzero(ub[:, c])[0] + y0; lcol = np.nonzero(lb[:, c])[0] + y0
            ucore = np.nonzero(ub[:, c] & s.core[:, c])[0] + y0; lcore = np.nonzero(lb[:, c] & s.core[:, c])[0] + y0
            Rt = int(ucol.min()) if len(ucol) else Ib
            Rb = int(lcol.max()) + 1 if len(lcol) else Ib
            Ct = int(ucore.min()) if len(ucore) else Ib
            Cb = int(lcore.max()) + 1 if len(lcore) else Ib
            # seam dark run at the bottom of upper body
            St = Ib
            while St - 1 >= Rt and L[St - 1 - y0, c] < T_SEAM and ub[St - 1 - y0, c]: St -= 1
            if St < Ib and s.t_band > T_SEAM:          # widen the rigid band over the line's dark AA / corner branch
                while St - 1 >= Rt and L[St - 1 - y0, c] < s.t_band and ub[St - 1 - y0, c] and s.core[St - 1 - y0, c]: St -= 1
            s.cols[x] = dict(Ib=Ib, Rt=Rt, Rb=Rb, Ct=Ct, Cb=Cb, St=St, has_seam=St < Ib)
        xs = sorted(s.cols)
        s.xmin, s.xmax = xs[0], xs[-1]
        sc = s.parts_json['seam']['darkSeamColumns']
        s.cornerL, s.cornerR = sc
        # interior columns
        ia = s.interior[..., 3] > 0
        s.icols = {}
        for c in np.nonzero(ia.any(0))[0]:
            ys = np.nonzero(ia[:, c])[0] + y0
            s.icols[int(c + x0)] = (int(ys.min()), int(ys.max()) + 1)

# ====================================================================== calibration
def sub_cross(vals, ys, thr=0.5):
    """first crossing of thr going along ys (pixel-centre values) -> boundary coordinate"""
    for k in range(1, len(vals)):
        a, b = vals[k - 1], vals[k]
        if (a - thr) * (b - thr) <= 0 and a != b:
            return ys[k - 1] + 0.5 + (thr - a) / (b - a) * (ys[k] - ys[k - 1])
    return None

def lipness(rgb, pal, ref='upper'):
    Ls = lum(pal['skin'][None])[0]; Lu = lum(pal[ref][None])[0]
    return np.clip((Ls - lum(rgb)) / (Ls - Lu), 0, 1)

def shape_edges(V, img, cx):
    """centre edges of a shape: top, UI (upper inner), LI (lower inner), LB (bottom) as boundary y (canvas)"""
    a = img[..., 3:4] / 255.0
    full = img[..., :3] * a + V.base_full[..., :3] * (1 - a)
    t = lipness(full, V.pal); L = lum(img)
    cav = cavity_mask(img, V.pal)
    open_ = cav[:, cx - 4:cx + 5].any() and cav.sum() >= 40
    res = {k: [] for k in ['top', 'UI', 'LI', 'LB']}
    for x in range(cx - 3, cx + 4):
        ys = list(range(V.ay - 16, V.ay + 25))
        col = [t[y, x] for y in ys]
        top = sub_cross(col, ys); bot = sub_cross(col[::-1], ys[::-1])
        if bot is not None: bot = bot  # crossing going upward; boundary coordinate as computed
        res['top'].append(top); res['LB'].append(bot)
        # dark line run below the top
        y = int(np.floor(top))
        while y < V.ay + 10 and not L[y, x] < T_SEAM: y += 1
        while L[y, x] < T_SEAM: y += 1
        res['UI'].append(y)
        if open_:
            cy = np.nonzero(cav[:, x])[0]
            res['LI'].append(int(cy.max()) + 1)
        else:
            res['LI'].append(y)
    return {k: float(np.median(v)) for k, v in res.items()}, open_

def seam_points(V, img, band=(-12, 4)):
    L = lum(img); al = img[..., 3] == 255; pts = {}
    for x in range(V.ax - 60, V.ax + 61):
        ys = [y for y in range(V.ay + band[0], V.ay + band[1] + 1) if al[y, x] and L[y, x] < T_SEAM]
        if ys: pts[x] = min(ys, key=lambda y: (L[y, x], abs(y - V.ay)))
    l = r = V.ax
    while l - 1 in pts or l - 2 in pts: l = l - 1 if l - 1 in pts else l - 2
    while r + 1 in pts or r + 2 in pts: r = r + 1 if r + 1 in pts else r + 2
    return {x: y for x, y in pts.items() if l <= x <= r}, (l, pts[l]), (r, pts[r])

def calibrate(V):
    cx = int(round((V.cornerL + V.cornerR) / 2))
    hw = (V.cornerR - V.cornerL) / 2
    shapes = {n: load_rgba(f'{ROOT}/views/{V.v}/mouth/{n}.png') for n in ['rest', 'M', 'smile', 'AA_half', 'AA']}
    E = {n: shape_edges(V, im, cx)[0] for n, im in shapes.items()}
    r = E['rest']
    C = {'cx': (V.cornerL + V.cornerR) / 2, 'hw': hw, 'edges': E}
    for n in ['AA_half', 'AA']:
        C[n] = {k: round(E[n][k] - r[k], 2) for k in r}
        C[n]['gap'] = round(E[n]['LI'] - E[n]['UI'], 2)
        # her cavity height profile vs u (normalised to the centre)
        cav = cavity_mask(shapes[n], V.pal)
        xs = np.nonzero(cav.any(0))[0]
        h = np.array([cav[:, x].sum() for x in xs], float)
        ccx = (xs.min() + xs.max() + 1) / 2; chw = (xs.max() + 1 - xs.min()) / 2
        uu = (xs + 0.5 - ccx) / chw
        hc = np.median(h[np.abs(uu) < 0.15])
        prof = np.convolve(h / hc, np.ones(3) / 3, 'same')
        C[n]['profile_u'] = [round(float(u), 3) for u in uu]; C[n]['profile'] = [round(float(p), 3) for p in np.clip(prof, 0, 1.2)]
    restseam, rl, rr = seam_points(V, shapes['rest'])
    C['rest_corners'] = [rl, rr]
    for n in ['M', 'smile']:
        sp, l, rgt = seam_points(V, shapes[n])
        C[n] = {'top': round(E[n]['top'] - r['top'], 2), 'LB': round(E[n]['LB'] - r['LB'], 2),
                'cornerL': [l[0] - rl[0], l[1] - rl[1]], 'cornerR': [rgt[0] - rr[0], rgt[1] - rr[1]], 'seam': sp}
        # fit curl exponent p: rest seam point (x,y) -> (x+dx(u), y+dy(u)); compare to her seam
        best = None
        for p in np.arange(1.0, P_MAX + 0.001, 0.25):
            err = []
            for x, y in restseam.items():
                u = np.clip((x + 0.5 - C['cx']) / hw, -1, 1)
                side = 'cornerL' if u < 0 else 'cornerR'
                dx = C[n][side][0] * abs(u) ** p; dy = C[n][side][1] * abs(u) ** p
                xo = x + dx; xi = int(round(xo))
                if xi in sp: err.append(abs(y + dy - sp[xi]))
            e = float(np.mean(err)) if err else 99
            if best is None or e < best[1]: best = (float(p), e)
        C[n]['p'], C[n]['seam_mae_px'] = best
        del C[n]['seam']
    return C

# ====================================================================== deformation
def interp_open(o, half, full):
    return np.interp(o, [0, .5, 1], [0, half, full])

class Deform:
    """per-column displacements for a given (open, form)"""
    def __init__(s, V, C, cfg, o, f):
        s.V, s.C, s.cfg, s.o, s.f = V, C, cfg, o, f
        s.cache = {}

    def u(s, x):  # x = pixel column (int) -> normalised position
        return (x + 0.5 - s.C['cx']) / s.C['hw']

    def prof_open(s, which, u):
        if abs(u) >= 1: return 0.0
        if s.cfg['open_profile'] == 'her':
            P = s.C[which]
            return float(np.interp(u, P['profile_u'], P['profile'], left=0, right=0))
        return float(max(0.0, 1 - u * u))

    def col(s, x):
        if x in s.cache: return s.cache[x]
        C, o, f, cfg = s.C, s.o, s.f, s.cfg
        u = s.u(x); uc = float(np.clip(u, -1, 1))
        ph, pf = s.prof_open('AA_half', u), s.prof_open('AA', u)
        def op(k):
            return float(np.interp(o, [0, .5, 1], [0, C['AA_half'][k] * ph, C['AA'][k] * pf]))
        dT_o, dUI_o, dLI_o, dLB_o = op('top'), op('UI'), op('LI'), op('LB')
        tgt = C['smile'] if f > 0 else C['M']
        side = 'cornerL' if uc < 0 else 'cornerR'
        w = abs(uc) ** tgt['p'] * abs(f)
        dyf = tgt[side][1] * w
        wx = (abs(uc) if cfg.get('dx_profile', 'curl') == 'linear' else abs(uc) ** tgt['p']) * abs(f)
        dxf = tgt[side][0] * wx if cfg['corner_dx'] else 0.0
        pp = max(0.0, 1 - uc * uc) * abs(f) if (cfg['press'] and abs(u) < 1) else 0.0
        dT_f, dLB_f = tgt['top'] * pp, tgt['LB'] * pp
        d = dict(dT=dyf + dT_o + dT_f, dS=dyf + dUI_o, dLI=dyf + dLI_o, dLB=dyf + dLB_o + dLB_f, dx=dxf)
        if cfg.get('snap'):      # pixel-snap the rigid bands: line art moves by whole pixels (exact copies)
            d = {k: (float(np.round(v)) if (k != 'dx' or cfg['snap'] == 'xy') else v) for k, v in d.items()}  # 'y': x stays continuous
        s.cache[x] = d
        return d

    # ---- knots (source y, dest y) for each part at column x
    def knots_upper(s, x):
        F = s.V.cols[x]; d = s.col(x)
        Rt, Ct, St, Ib = F['Rt'], F['Ct'], F['St'], F['Ib']
        Et = min(Ct + 2, St) if s.cfg['bands'] else Ct
        dT, dS = d['dT'], d['dS']
        if s.cfg['bands'] and s.cfg.get('xsmooth'):
            dT = s.smoothed()['dT'][x]
        elif s.cfg['bands']:
            fill = max(0, St - Et)
            if (fill > 0 or s.cfg.get('clamp_always', True)) and (St + dS) - (Et + dT) < s.cfg['minfill'] * fill:
                dT = St + dS - Et - s.cfg['minfill'] * fill
        else:
            dT = dS  # rigid whole lip
        top_pin = 0.0
        if not s.cfg['pins']: top_pin = dT
        src = [Rt - 10, Rt, Ct, Et, St, Ib, Ib + FLAP + 2]
        dst_d = [0.0 if s.cfg['pins'] else dT, (dT if dT < 0 else top_pin), dT, dT, dS, dS, dS]
        return src, dst_d

    def knots_lower(s, x):
        F = s.V.cols[x]; d = s.col(x)
        Ib, Cb, Rb = F['Ib'], F['Cb'], F['Rb']
        Ei = min(Ib + 1, Cb) if s.cfg['bands'] else Ib
        Eb = max(Cb - 2, Ei) if s.cfg['bands'] else Cb
        dI, dB = d['dLI'], d['dLB']
        if s.cfg['bands'] and s.cfg.get('xsmooth'):
            dB = s.smoothed()['dB'][x]
        elif s.cfg['bands']:
            fill = max(0, Eb - Ei)
            if (fill > 0 or s.cfg.get('clamp_always', True)) and (Eb + dB) - (Ei + dI) < s.cfg['minfill'] * fill:
                dB = Ei + dI + s.cfg['minfill'] * fill - Eb
        else:
            dB = dI
        bot_pin = 0.0 if s.cfg['pins'] else dB
        src = [Ib - FLAP - 2, Ib, Ei, Eb, Cb, Rb, Rb + 10]
        dst_d = [dI, dI, dI, dB, dB, (dB if dB > 0 else bot_pin), 0.0 if s.cfg['pins'] else dB]
        return src, dst_d

    def smoothed(s):
        """it15: the min-fill clamp is computed per column, then made consistent along x so the
        outline band moves as one piece (no comb).  upper: dT = boxavg_k(minfilt_k(min(dT0, lim)));
        every averaged value is a min over a window containing x, so the clamp (fill >= minfill)
        still holds at every column.  lower: same with max.  With snap the result is floored/ceiled
        (never rounded towards violating the clamp)."""
        if 'sm' in s.cache: return s.cache['sm']
        k = int(s.cfg['xsmooth']); mf = s.cfg['minfill']; xs = sorted(s.V.cols)
        up, lo, u0, l0 = [], [], [], []
        for x in xs:          # only the clamp EXCESS is spread along x (the control itself is already smooth)
            F = s.V.cols[x]; d = s.col(x)
            Et = min(F['Ct'] + 2, F['St']); fill = max(0, F['St'] - Et)
            u0.append(d['dT']); up.append(min(0.0, F['St'] + d['dS'] - Et - mf * fill - d['dT']))
            Ei = min(F['Ib'] + 1, F['Cb']); Eb = max(F['Cb'] - 2, Ei); fill = max(0, Eb - Ei)
            l0.append(d['dLB']); lo.append(max(0.0, Ei + d['dLI'] + mf * fill - Eb - d['dLB']))
        up, lo = np.array(up), np.array(lo); n = len(xs)
        def filt(a, fn):
            m = np.array([fn(a[max(0, i - k):i + k + 1]) for i in range(n)])
            return np.array([m[max(0, i - k):i + k + 1].mean() for i in range(n)])
        su, sl = np.array(u0) + filt(up, np.min), np.array(l0) + filt(lo, np.max)
        if s.cfg.get('snap'):
            su, sl = np.floor(su + 1e-6), np.ceil(sl - 1e-6)
        r = dict(dT={x: float(a) for x, a in zip(xs, su)}, dB={x: float(a) for x, a in zip(xs, sl)})
        s.cache['sm'] = r
        return r

    def dx_at(s, x):
        """horizontal displacement of column x incl. pin ramp beyond the corners"""
        V = s.V
        if V.cornerL <= x <= V.cornerR: return s.col(x)['dx']
        if x < V.cornerL:
            dc = s.col(V.cornerL)['dx']
            if dc < 0 or not s.cfg['pins']: return dc            # advancing outward: rigid
            return dc * (x - V.xmin) / max(1, V.cornerL - V.xmin)  # vacating: pin at R edge
        dc = s.col(V.cornerR)['dx']
        if dc > 0 or not s.cfg['pins']: return dc
        return dc * (V.xmax - x) / max(1, V.xmax - V.cornerR)

def monotone(src, dst, eps=1e-3):
    src = list(map(float, src)); dst = list(map(float, dst))
    for k in range(1, len(src)):
        if src[k] < src[k - 1] + eps: src[k] = src[k - 1] + eps
        if dst[k] < dst[k - 1] + eps * 0.5: dst[k] = dst[k - 1] + eps * 0.5
    return src, dst

def strip_mesh(columns, knots_fn, dx_fn, pad_cols):
    """columns: list of pixel columns (ints) in order; vertices at pixel centres x+0.5.
    knots_fn(x) -> (src_y list, disp list). pad_cols: (left_pad_x, right_pad_x) pinned transparent columns."""
    src, dst = [], []
    allc = [('pad', pad_cols[0], columns[0])] + [('c', x, x) for x in columns] + [('pad', pad_cols[1], columns[-1])]
    nlev = None
    for kind, x, feat_x in allc:
        sy, dd = knots_fn(feat_x)
        if kind == 'pad': dd = [0.0] * len(dd); dxx = 0.0
        else: dxx = dx_fn(x)
        sy, dy = monotone(sy, [a + b for a, b in zip(sy, dd)])
        nlev = len(sy)
        for a, b in zip(sy, dy):
            src.append([x + 0.5, a]); dst.append([x + 0.5 + dxx, b])
    tris = []
    ncol = len(allc)
    for i in range(ncol - 1):
        for k in range(nlev - 1):
            a, b = i * nlev + k, (i + 1) * nlev + k
            tris += [[a, b, b + 1], [a, b + 1, a + 1]]
    return Mesh(src, dst, tris)

def knot_eval(src, dst, y):
    return float(np.interp(y, src, dst))

def grid_from_fn(x0, y0, x1, y1, sx, sy, fn):
    g = Grid(x0, y0, x1, y1, sx, sy)
    for j in range(g.src.shape[0]):
        for i in range(g.src.shape[1]):
            g.dst[j, i] = fn(*g.src[j, i])
    return grid_mesh(g)

def lip_meshes(V, D, cfg):
    cols = sorted(V.cols)
    if cfg['mesh'] == 'strip':
        sel = cols[::cfg['sx']]
        if sel[-1] != cols[-1]: sel.append(cols[-1])
        mU = strip_mesh(sel, D.knots_upper, D.dx_at, (V.xmin - 6, V.xmax + 6))
        mL = strip_mesh(sel, D.knots_lower, D.dx_at, (V.xmin - 6, V.xmax + 6))
    else:
        def mkfn(kfn):
            def fn(x, y):
                xc = int(np.clip(np.floor(x), V.xmin, V.xmax))
                if x < V.xmin - 0.5 or x > V.xmax + 1.5: return [x, y]
                sy, dd = kfn(xc); sy, dy = monotone(sy, [a + b for a, b in zip(sy, dd)])
                return [x + D.dx_at(xc), knot_eval(sy, dy, y)]
            return fn
        uy0 = min(V.cols[x]['Rt'] for x in cols) - 10; uy1 = max(V.cols[x]['Ib'] for x in cols) + FLAP + 2
        ly0 = min(V.cols[x]['Ib'] for x in cols) - FLAP - 2; ly1 = max(V.cols[x]['Rb'] for x in cols) + 10
        mU = grid_from_fn(V.xmin - 6, uy0, V.xmax + 7, uy1, cfg['sx'], cfg['sy'], mkfn(D.knots_upper))
        mL = grid_from_fn(V.xmin - 6, ly0, V.xmax + 7, ly1, cfg['sx'], cfg['sy'], mkfn(D.knots_lower))
    return mU, mL

def lip_edges(V, D, mU, mL):
    """dest inner edges of the two bodies at lip columns: arrays (xd, eU, eL)"""
    xs = [x for x in sorted(V.cols) if V.cornerL <= x <= V.cornerR]
    pu = mU.forward([[x + 0.5, V.cols[x]['Ib']] for x in xs])
    pl = mL.forward([[x + 0.5, V.cols[x]['Ib']] for x in xs])
    return np.array(xs), pu, pl

def interior_mesh(V, D, cfg, edges):
    xs, pu, pl = edges
    ic = sorted(V.icols)
    ccx = (ic[0] + ic[-1] + 1) / 2; chw = (ic[-1] + 1 - ic[0]) / 2
    src, dst = [], []
    cols = ic[::max(1, cfg['sx'])]
    if cols[-1] != ic[-1]: cols.append(ic[-1])
    allc = [ic[0] - 3] + cols + [ic[-1] + 3]
    for x in allc:
        xf = min(max(x, ic[0]), ic[-1])
        t0, t1 = V.icols[xf]
        u = (x + 0.5 - ccx) / chw
        xr = D.C['cx'] + u * (D.C['hw'] + cfg.get('interior_xover', 0.0)) - 0.5   # matching lip column
        # dest x and edges from the warped lip edges (interpolated along the lip columns)
        xd = np.interp(xr + 0.5, xs + 0.5, pu[:, 0])
        if cfg.get('interior_extrap', True):
            if xr < xs[0]: xd = pu[0, 0] + (xr - xs[0])          # extrapolate past the corners (no fold)
            if xr > xs[-1]: xd = pu[-1, 0] + (xr - xs[-1])
        eU = np.interp(xr + 0.5, xs + 0.5, pu[:, 1]); eL = np.interp(xr + 0.5, xs + 0.5, pl[:, 1])
        gap = max(0.0, eL - eU); h = t1 - t0
        ov = cfg.get('interior_tuck', 0.0)          # px of interior tucked under each lip edge
        k = max(1.0, (gap + 2 * ov) / h) if cfg.get('interior_fit', True) else 1.0
        for y in [t0 - 3, t0, t1, t1 + 3]:
            src.append([x + 0.5, y]); dst.append([xd, eU - ov + (y - t0) * k])
    nlev = 4; tris = []
    for i in range(len(allc) - 1):
        for kk in range(nlev - 1):
            a, b = i * nlev + kk, (i + 1) * nlev + kk
            tris += [[a, b, b + 1], [a, b + 1, a + 1]]
    return Mesh(src, dst, tris)

def gap_cov(V, edges, ext, shape):
    """per-pixel coverage of the gap [eU-ext, eL+ext] (crop coords); 0 where the lips are closed"""
    xs, pu, pl = edges
    x0, y0 = V.off
    cov = np.zeros(shape)
    eUc = np.full(shape[1], np.nan); eLc = np.full(shape[1], np.nan)
    xmin, xmax = pu[:, 0].min(), pu[:, 0].max()
    for c in range(shape[1]):
        X = x0 + c + 0.5
        if X < xmin or X > xmax: continue
        eU = np.interp(X, pu[:, 0], pu[:, 1]); eL = np.interp(X, pl[:, 0], pl[:, 1])
        eUc[c], eLc[c] = eU, eL
        if eL - eU <= 1e-6: continue
        a, b = eU - ext, eL + ext
        ys = np.arange(shape[0]) + y0
        cov[:, c] = np.clip(np.minimum(ys + 1, b) - np.maximum(ys, a), 0, 1)
    return cov, eUc, eLc

# ====================================================================== render one cell
ORDER = ['upper_flap', 'lower_flap', 'interior', 'lower_body', 'upper_body']

def render_cell(V, C, cfg, o, f):
    D = Deform(V, C, cfg, o, f)
    mU, mL = lip_meshes(V, D, cfg)
    edges = lip_edges(V, D, mU, mL)
    L = {}
    L['upper_body'] = render(V.P['upper_body'], mU, V.off)
    L['lower_body'] = render(V.P['lower_body'], mL, V.off)
    if cfg['flaps'] in ('own_layers', 'own_layers_overlap'):
        pu, pl = V.Pflap['overlap' if cfg['flaps'] == 'own_layers_overlap' else 'msplit']
        L['upper_flap'] = render(pu, mU, V.off)
        L['lower_flap'] = render(pl, mL, V.off)
    elif cfg['flaps'] == 'in_parts':   # make_mesh_split as-is: flaps drawn with their owner part
        L['upper_body'] = over(render(V.P['upper_flap'], mU, V.off), L['upper_body'])
        L['lower_body'] = over(render(V.P['lower_flap'], mL, V.off), L['lower_body'])
        L['upper_flap'] = np.zeros_like(L['upper_body']); L['lower_flap'] = np.zeros_like(L['upper_body'])
    else:
        L['upper_flap'] = np.zeros_like(L['upper_body']); L['lower_flap'] = np.zeros_like(L['upper_body'])
    mI = interior_mesh(V, D, cfg, edges)
    Iraw = render(V.P['interior'], mI, V.off)
    cov, eUc, eLc = gap_cov(V, edges, cfg['clip_ext'] or 0.0, Iraw.shape[:2])
    vis = 1.0 if o > 0 else 0.0
    L['interior'] = Iraw * (cov[..., None] if cfg['clip_ext'] is not None else 1) * vis
    meshes = {'upper': mU, 'lower': mL, 'interior': mI}
    if o == 0 and f == 0:
        import measure
        comp = onto(V.base, stack(L))
        ow = measure.outline_widths(V, comp, {'meshes': meshes})
    else:
        ow = None
    return dict(outline_w=ow, L=L, Iraw=Iraw * vis, cov=cov, eU=eUc, eL=eLc, meshes=meshes, D=D, edges=edges)

def stack(L, bg=None):
    out = np.zeros_like(L['upper_body']) if bg is None else bg.copy()
    for k in ORDER: out = over(out, L[k])
    return out

def bg_base(V):
    return premul(V.base)

def bg_blue(V):
    b = np.zeros(V.base.shape, float); b[..., 2] = 255; b[..., 3] = 255; return b
