#!/usr/bin/env python3
"""Measurements for the mesh-bend mouth (bilinear sampling throughout)."""
import numpy as np
from scipy.ndimage import label, binary_fill_holes
from mb import *
from bend import *

def her_crops(V):
    out = {}
    x0, y0, x1, y1 = V.box
    for (o, f), n in HER.items():
        im = load_rgba(f'{ROOT}/views/{V.v}/mouth/{n}.png')[y0:y1, x0:x1]
        a = im[..., 3:4] / 255.0
        comp = (im[..., :3] * a + V.base[..., :3] * (1 - a))
        out[n] = dict(img=im, comp=comp, sil=mouth_sil(comp, V.pal),
                      cav=cavity_mask(im, V.pal))
    return out

def darkness(rgb_u8, pal):
    Lr = lum(pal['upper'][None])[0]; Ll = lum(pal['line'][None])[0]
    return np.clip((Lr - lum(rgb_u8)) / (Lr - Ll), 0, 1)

def seam_profile(V, layer_pm):
    U = unpremul_u8(layer_pm)
    w = darkness(U, V.pal) * (U[..., 3] / 255.0)
    return w

def edge_width(t, rev=False):
    """20%-80% rise distance along a 1-D lipness profile (from skin side)"""
    if rev: t = t[::-1]
    if len(t) == 0 or t.max() < 0.5: return None
    t = t / t.max()                      # normalise to the column's own lip value (thin corners, blur)
    def cross(th):
        for k in range(1, len(t)):
            if t[k - 1] < th <= t[k]:
                return k - 1 + (th - t[k - 1]) / (t[k] - t[k - 1])
        return None
    a, b = cross(0.2), cross(0.8)
    if a is None or b is None or b < a: return None
    return b - a

def mouth_window(V):
    x0, y0 = V.off
    w = np.zeros(V.base.shape[:2], bool)
    ya = min(c['Rt'] for c in V.cols.values()) - 10 - y0; yb = max(c['Rb'] for c in V.cols.values()) + 14 - y0
    w[ya:yb, V.xmin - 8 - x0:V.xmax + 9 - x0] = True
    return w

MIN_LIP = 3   # outline is measured where the lip (edge to seam) is >= 3 px thick at rest; thinner corner columns
              # are all line/edge and are covered by the seam metric instead

def rest_edges(V):
    """rest lip/skin edge (t=0.5 crossing) per column: upper top edge and lower bottom edge (canvas y)"""
    if hasattr(V, '_redges'): return V._redges
    x0, y0 = V.off
    tu = lipness(V.base, V.pal, 'upper'); tl = lipness(V.base, V.pal, 'lower')
    res = {}
    for x in [x for x in sorted(V.cols) if V.cornerL + 1 <= x <= V.cornerR - 1]:
        F = V.cols[x]; c = x - x0
        if F['Ct'] < F['St']:
            ys = np.arange(F['Rt'], F['St']); col = tu[ys - y0, c]
            if col.max() >= 0.5:
                k = int(np.argmax(col >= 0.5 * col.max()))
                if k > 0 and F['St'] - (F['Rt'] + k) >= MIN_LIP: res[(x, 'top')] = (F['Rt'] + k, F['St'])
        if F['Rb'] > F['Ib'] + 1:
            ys = np.arange(F['Ib'], F['Rb']); col = tl[ys - y0, c][::-1]
            if col.max() >= 0.5:
                k = int(np.argmax(col >= 0.5 * col.max()))
                if k > 0 and (F['Rb'] - 1 - k) - F['Ib'] + 1 >= MIN_LIP: res[(x, 'bot')] = (F['Rb'] - 1 - k, F['Ib'])
    V._redges = res
    return res

def outline_widths(V, comp, cell):
    """10-90 edge width (normalised to the column's lip value) of the upper-lip top edge and the lower-lip
    bottom edge, measured in a +-4 px window around where the mesh carries each rest edge pixel"""
    x0, y0 = V.off
    tu = lipness(comp, V.pal, 'upper'); tl = lipness(comp, V.pal, 'lower')
    res = {}
    for (x, part), (ye, ylim) in rest_edges(V).items():
        mesh = cell['meshes']['upper' if part == 'top' else 'lower']
        p = mesh.forward([[x + 0.5, ye + 0.5], [x + 0.5, ylim]])
        if np.isnan(p).any(): res[(x, part)] = None; continue
        cd = int(np.floor(p[0, 0])) - x0; yc = p[0, 1]
        if part == 'top':      # window stays inside the upper lip (never reaches the gap below the seam)
            a = int(np.floor(yc - 4)); b = int(min(np.floor(yc + 3), np.ceil(p[1, 1]) + 1))
            res[(x, part)] = edge_width(tu[a - y0:b - y0, cd])
        else:                  # window stays inside the lower lip (never reaches the gap above it)
            a = int(max(np.ceil(yc - 3), np.floor(p[1, 1]))); b = int(np.ceil(yc + 4))
            res[(x, part)] = edge_width(tl[a - y0:b - y0, cd], rev=True)
    return res

def measure_cell(V, cell, rest_cell, her, o, f):
    x0, y0 = V.off
    L = cell['L']; D = cell['D']
    st = stack(L)
    comp = onto(V.base, st)
    m = {}
    # ---------------- rest diff
    m['diff_vs_base_px'] = int((comp != V.base).any(-1).sum())
    # ---------------- seam (line art inside upper_lip layer)
    w = seam_profile(V, L['upper_body']); w0 = seam_profile(V, rest_cell['L']['upper_body'])
    ink = w.sum(0); ink0 = w0.sum(0)
    dU = np.array([w[:, c].max() for c in range(w.shape[1])])
    seam_cols = [x for x in sorted(V.cols) if V.cols[x]['has_seam']]
    dev, brk = [], []
    for x in seam_cols:
        c0 = x - x0
        xd = x + D.dx_at(x)              # dest column centre (float)
        cd = xd - x0
        ib = np.interp(cd, np.arange(len(ink)), ink)
        dev.append(ib - ink0[c0])
        mx = max(dU[int(np.floor(cd))], dU[min(int(np.floor(cd)) + 1, len(dU) - 1)])
        if ink0[c0] >= 0.5 and (ib < 0.5 or mx < 0.4): brk.append(x)
    dev = np.array(dev)
    # discrete dark-run width (px with L<43 in the layer)
    U = unpremul_u8(L['upper_body']); U0 = unpremul_u8(rest_cell['L']['upper_body'])
    dk = ((lum(U) < T_SEAM) & (U[..., 3] > 127)).sum(0); dk0 = ((lum(U0) < T_SEAM) & (U0[..., 3] > 127)).sum(0)
    ddev = np.array([dk[int(round(x + D.dx_at(x) - x0))] - dk0[x - x0] for x in seam_cols])
    # geometric line width: the rest line's coverage (darkness at rest) carried through the same mesh
    lm = rest_cell.get('_linemask')
    lab, ncomp = label(w >= 0.35, structure=np.ones((3, 3))); lab0, ncomp0 = label(w0 >= 0.35, structure=np.ones((3, 3)))
    big = lambda lb, n: sum(1 for i in range(1, n + 1) if (lb == i).sum() >= 3)
    m['seam'] = dict(ink_dev_median=float(np.median(np.abs(dev))), ink_dev_max=float(np.abs(dev).max()),
                     ink_dev_signed_mean=float(dev.mean()),
                     darkrun_dev_median=float(np.median(np.abs(ddev))), darkrun_dev_max=int(np.abs(ddev).max()),
                     break_cols=brk, components=big(lab, ncomp), components_rest=big(lab0, ncomp0))
    # ---------------- outline (lip/skin edge) on the composite
    ow = outline_widths(V, comp, cell); ow0 = rest_cell['outline_w']
    odev = []; obreak = []
    for k, r0 in ow0.items():
        if r0 is None: continue
        rb = ow.get(k)
        if rb is None: obreak.append(list(k)); continue
        odev.append(rb - r0)
    odev = np.array(odev) if odev else np.zeros(1)
    m['outline'] = dict(dev_median=float(np.median(np.abs(odev))), dev_max=float(np.abs(odev).max()),
                        signed_mean=float(odev.mean()), n=int(len(odev)), break_cols=obreak)
    # ---------------- holes / gaps
    cov = st[..., 3]
    core0 = V.core
    stale = (cov < 250) & core0          # base lip shows through by >=2%
    stale_strict = (cov < 254.5) & core0
    filled = binary_fill_holes(cov > 127.5)
    inner = filled & (cov < 127.5)
    m['holes'] = dict(base_lip_showing_px=int(stale.sum()), base_lip_showing_strict_px=int(stale_strict.sum()),
                      max_seethrough=round(float(((255 - cov) / 255 * core0).max()), 4),
                      inner_hole_px=int(inner.sum()), total=int((stale | inner).sum()))
    # ---------------- interior spill
    above = over(L['lower_body'], L['upper_body'])[..., 3] / 255.0
    vis = L['interior'][..., 3] * (1 - above)
    eU, eL = cell['eU'], cell['eL']
    ys = np.arange(vis.shape[0])[:, None] + y0
    ingap = (ys + 1 > eU[None, :]) & (ys < eL[None, :]) & (eL - eU > 1e-6)[None, :]
    ingap = np.where(np.isnan(eU)[None, :], False, ingap)
    lips_hull = binary_fill_holes((L['upper_body'][..., 3] > 127) | (L['lower_body'][..., 3] > 127) | ingap)
    ingap_tol = (ys + 1 > eU[None, :] - 0.5) & (ys < eL[None, :] + 0.5) & (eL - eU > 1e-6)[None, :]
    ingap_tol = np.where(np.isnan(eU)[None, :], False, ingap_tol)
    spill = (vis > 5) & ~ingap_tol
    m_spill_strict = int(((vis > 5) & ~ingap).sum())
    m['interior'] = dict(spill_px=int(spill.sum()), spill_strict_px=m_spill_strict, outside_lip_hull_px=int(((vis > 5) & ~lips_hull).sum()),
                         unclipped_outside_gap_px=int(((cell['Iraw'][..., 3] > 5) & ~ingap & (1 - above > 0.02)).sum()),
                         visible_px=int((vis > 127).sum()))
    # ---------------- key blue spill
    bl = unpremul_u8(over(bg_blue(V), st))
    opaque = st[..., 3] >= 254.5
    m['blue_spill_px'] = int((opaque & (bl[..., 2].astype(int) > bl[..., 0].astype(int))).sum())
    # straight-alpha check of sources: transparent texels' rgb (premultiplied sampling ignores them anyway)
    # ---------------- flips
    m['flipped_tris'] = {k: me.flipped() for k, me in cell['meshes'].items()}
    # ---------------- shape match
    win = mouth_window(V)
    sil = mouth_sil(comp, V.pal) & win
    m['sil_px'] = int(sil.sum())
    n = HER.get((o, f))
    if n:
        H = her[n]
        m['her'] = n
        m['iou_sil'] = round(iou(sil, H['sil'] & win), 4)
        opening = vis > 127
        m['iou_opening'] = round(iou(opening, H['cav']), 4) if (opening.any() or H['cav'].any()) else None
    # centre gap and corners achieved
    xs, pu, pl = cell['edges']
    ci = int(np.argmin(np.abs(xs + 0.5 - D.C['cx'])))
    m['gap_centre_px'] = round(float(pl[ci, 1] - pu[ci, 1]), 2)
    m['upper_inner_dy_centre'] = round(float(pu[ci, 1] - V.cols[int(xs[ci])]['Ib']), 2)
    cl = cell['meshes']['upper'].forward([[V.cornerL + 0.5, V.cols[V.cornerL]['St'] + 0.5], [V.cornerR + 0.5, V.cols[V.cornerR]['St'] + 0.5]])
    m['corner_dL'] = [round(float(cl[0, 0] - V.cornerL - 0.5), 2), round(float(cl[0, 1] - V.cols[V.cornerL]['St'] - 0.5), 2)]
    m['corner_dR'] = [round(float(cl[1, 0] - V.cornerR - 0.5), 2), round(float(cl[1, 1] - V.cols[V.cornerR]['St'] - 0.5), 2)]
    return m, comp
