#!/usr/bin/env python3
"""Job B step 2 -- STAGED PROPOSAL, REUSES FRONT ART.
Bends the front apose Job A mouth (mesh_bend, FINAL config) onto the diagonal rest lips cut by lipcut.py:
  front view px --(Job A per-column strip mesh: open/form)--> front px --(G: homography H fitted to her diagonal lip
  silhouette + per-column vertical residual knots for top edge / seam / bottom edge)--> diagonal view px.
G is a dense triangle grid (2 px) rendered with bilinear sampling at 4x supersampling then 4x4 box (area) downsample.
Every pixel is a resample of her front pixels (base.png / mesh_split parts / AA.png notch fill); nothing painted."""
import json, os, sys
import numpy as np, cv2
from PIL import Image
from scipy.optimize import minimize
from scipy.ndimage import binary_fill_holes, binary_erosion, median_filter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, f'{HERE}/../mesh_bend')
from lipcut import *          # noqa
from run import ITERATIONS, FINAL, view_for, get_calib
from bend import render_cell, stack
from mb import bilinear, Mesh, premul
from final import label, hcat, vcat
SS = 4
GSTEP = 2
PERSP_MAX = 0.15
T = np.array([[1, 0, .5], [0, 1, .5], [0, 0, 1.]])        # index -> continuous (pixel centre at i+.5)

def h_apply(Hc, pts):
    p = np.c_[pts, np.ones(len(pts))] @ Hc.T; return p[:, :2] / p[:, 2:3]

def warp_cv(img, Hc, box):
    """bilinear perspective warp of a full-canvas front image into diag window box (continuous-coord H)"""
    x0, y0, x1, y1 = box
    Hi = np.linalg.inv(T) @ np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1.]]) @ Hc @ T
    return cv2.warpPerspective(img.astype(np.float32), Hi, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR)

def soft_iou(a, b): return float(np.minimum(a, b).sum() / max(np.maximum(a, b).sum(), 1e-9))
def bin_iou(a, b):
    a, b = a > .5, b > .5; return float((a & b).sum() / max((a | b).sum(), 1))

def fit_map(fsoft, dsoft, box, kind):
    """fit front->diag map (affine 6 / homography 8 params) maximising soft IoU of her lip silhouettes"""
    fy, fx = np.nonzero(fsoft > .5); dy, dx = np.nonzero(dsoft > .5)
    fsrc = np.float32([[fx.min(), fy.min()], [fx.max() + 1, fy.min()], [fx.max() + 1, fy.max() + 1], [fx.min(), fy.max() + 1]])
    x0, y0 = box[:2]
    ddst = np.float32([[dx.min() + x0, dy.min() + y0], [dx.max() + 1 + x0, dy.min() + y0], [dx.max() + 1 + x0, dy.max() + 1 + y0], [dx.min() + x0, dy.max() + 1 + y0]])
    def H_of(p):
        q = ddst + p.reshape(4, 2).astype(np.float32)
        if kind == 'affine':
            A = cv2.getAffineTransform(fsrc[:3], q[:3]); return np.vstack([A, [0, 0, 1]])
        return cv2.getPerspectiveTransform(fsrc, q)
    n = 6 if kind == 'affine' else 8
    cx, cy = fx.mean() + .5, fy.mean() + .5
    probe = np.array([[cx - 90, cy - 60], [cx + 90, cy - 60], [cx + 90, cy + 60], [cx - 90, cy + 60]])
    def loss(p):
        p8 = np.r_[p, np.zeros(8 - n)]; Hm = H_of(p8)
        # keep the perspective mild over the whole front crop (+-90 x +-60): the projective scale w may vary by
        # at most PERSP_MAX relative to the mouth centre, else the horizon line lands near the crop and folds the mesh
        w = np.c_[probe, np.ones(4)] @ Hm[2]; wc = np.array([cx, cy, 1]) @ Hm[2]
        pen = 10 * np.clip(np.abs(w / wc - 1) - PERSP_MAX, 0, None).sum()
        return 1 - soft_iou(warp_cv(fsoft, Hm, box), dsoft) + pen
    best = None
    for it in range(3):
        r = minimize(loss, np.zeros(n) if best is None else best.x, method='Powell', options=dict(xtol=1e-3, ftol=1e-5, maxfev=4000))
        best = r if best is None or r.fun <= best.fun else best
    return H_of(np.r_[best.x, np.zeros(8 - n)]), 1 - best.fun

def col_features(soft, rgb):
    """per window column: top edge, bottom edge (0.5 crossings, sub-px) and seam (darkest vs lip tone, sub-px)"""
    Y = rgb @ np.array([0.299, 0.587, 0.114]); m = soft > .9
    Yl = float(np.median(Y[m])) if m.any() else 0
    out = {}
    for x in range(soft.shape[1]):
        a = soft[:, x]
        ys = np.nonzero(a > .5)[0]
        if len(ys) < 3: continue
        i0, i1 = ys[0], ys[-1]
        t = i0 - (a[i0] - .5) / max(a[i0] - a[i0 - 1], 1e-6) + .5 if i0 > 0 else i0
        b = i1 + (a[i1] - .5) / max(a[i1] - a[i1 + 1], 1e-6) + .5 if i1 < len(a) - 1 else i1 + 1
        dk = np.clip(Yl - Y[i0:i1 + 1, x], 0, None)
        j = int(np.argmax(dk)); s = i0 + j + .5
        if 0 < j < len(dk) - 1:
            den = dk[j - 1] - 2 * dk[j] + dk[j + 1]
            if abs(den) > 1e-9: s += .5 * (dk[j - 1] - dk[j + 1]) / den
        out[x] = (t, s, b, float(dk[j]))
    return out

def residuals(feat_h, feat_d, ncols, clip=3.0):
    r = np.zeros((3, ncols)); have = np.zeros(ncols, bool)
    for x in range(ncols):
        if x in feat_h and x in feat_d:
            r[:, x] = [feat_d[x][k] - feat_h[x][k] for k in range(3)]; have[x] = True
    xs = np.nonzero(have)[0]
    for k in range(3):
        v = np.clip(median_filter(r[k, xs], 3, mode='nearest'), -clip, clip)
        v = np.convolve(np.pad(v, 1, mode='edge'), np.ones(3) / 3, 'valid')
        r[k] = np.interp(np.arange(ncols), xs, v)
    Th = np.interp(np.arange(ncols), xs, [feat_h[x][0] for x in xs])
    Sh = np.interp(np.arange(ncols), xs, [feat_h[x][1] for x in xs])
    Bh = np.interp(np.arange(ncols), xs, [feat_h[x][2] for x in xs])
    return r, Th, Sh, Bh, xs

class GMap:
    def __init__(s, Hc, box, res=None):
        s.H, s.box, s.res = Hc, box, res
    def __call__(s, pts):
        p = h_apply(s.H, pts)
        if s.res is None: return p
        r, Th, Sh, Bh, xs = s.res; x0, y0 = s.box[:2]
        X = p[:, 0] - x0 - .5; Yy = p[:, 1] - y0
        out = p.copy()
        for n in range(len(p)):
            xi = np.clip(X[n], 0, r.shape[1] - 1)
            rt, rs, rb = (np.interp(xi, np.arange(r.shape[1]), r[k]) for k in range(3))
            t, sm, b = (np.interp(xi, np.arange(r.shape[1]), a) for a in (Th, Sh, Bh))
            if not (t < sm < b): sm = (t + b) / 2
            out[n, 1] += np.interp(Yy[n], [t, sm, b], [rt, rs, rb])   # constant beyond the edges (column shift)
        return out

def g_mesh(V, G):
    x0, y0 = V.off; h, w = V.base.shape[:2]
    xs = np.arange(x0, x0 + w + 1, GSTEP, dtype=float); ys = np.arange(y0, y0 + h + 1, GSTEP, dtype=float)
    src = np.array([[x, y] for y in ys for x in xs]); dst = G(src)
    nx = len(xs); tris = []
    for j in range(len(ys) - 1):
        for i in range(nx - 1):
            a = j * nx + i; tris += [[a, a + 1, a + nx + 1], [a, a + nx + 1, a + nx]]
    return Mesh(src, dst, tris)

def render_to(P, src_off, mesh, box, ss=SS):
    """warp premultiplied crop P (top-left canvas src_off) through mesh into diag box at ss x, then box-filter down"""
    x0, y0, x1, y1 = box; Wd, Hd = (x1 - x0) * ss, (y1 - y0) * ss
    out = np.zeros((Hd, Wd, P.shape[2])); done = np.zeros((Hd, Wd), bool)
    for t in mesh.tris_:
        S = mesh.src[t] - src_off; D = (mesh.dst[t] - [x0, y0]) * ss
        M = np.array([[D[1, 0] - D[0, 0], D[2, 0] - D[0, 0]], [D[1, 1] - D[0, 1], D[2, 1] - D[0, 1]]])
        if abs(np.linalg.det(M)) < 1e-12: continue
        Mi = np.linalg.inv(M)
        bx0, by0 = max(int(np.floor(D[:, 0].min())), 0), max(int(np.floor(D[:, 1].min())), 0)
        bx1, by1 = min(int(np.ceil(D[:, 0].max())), Wd - 1), min(int(np.ceil(D[:, 1].max())), Hd - 1)
        if bx1 < bx0 or by1 < by0: continue
        yy, xx = np.mgrid[by0:by1 + 1, bx0:bx1 + 1]
        px, py = xx + .5 - D[0, 0], yy + .5 - D[0, 1]
        l1 = Mi[0, 0] * px + Mi[0, 1] * py; l2 = Mi[1, 0] * px + Mi[1, 1] * py
        ins = (l1 >= -1e-9) & (l2 >= -1e-9) & (l1 + l2 <= 1 + 1e-9) & ~done[yy, xx]
        if not ins.any(): continue
        sx = S[0, 0] + l1 * (S[1, 0] - S[0, 0]) + l2 * (S[2, 0] - S[0, 0])
        sy = S[0, 1] + l1 * (S[1, 1] - S[0, 1]) + l2 * (S[2, 1] - S[0, 1])
        out[yy[ins], xx[ins]] = bilinear(P, sx[ins], sy[ins]); done[yy[ins], xx[ins]] = True
    return out.reshape(Hd // ss, ss, Wd // ss, ss, -1).mean((1, 3)) if ss > 1 else out

def over_bg(bg_rgb, pm):
    a = pm[..., 3:4] / 255.0; return np.clip(pm[..., :3] + bg_rgb * (1 - a), 0, 255)

def zoomc(rgb, z=8): return np.kron(np.clip(np.round(rgb), 0, 255).astype(np.uint8), np.ones((z, z, 1), np.uint8))

def main():
    cfg = ITERATIONS[FINAL][1]; V = view_for('apose', cfg); C = get_calib('apose')
    fx0, fy0 = V.off
    frgb, fskin, fsoft_full, frest = front_reference('apose')
    # front rest mouth (Job A rest = base.png exactly) and her rest silhouette as a premul layer
    stacks = {}
    def front_stack(o, f):
        if (o, f) not in stacks: stacks[(o, f)] = stack(render_cell(V, C, cfg, o, f)['L'])
        return stacks[(o, f)]
    silP = np.zeros(V.base.shape[:2] + (4,)); silP[..., 3] = 255 * fsoft_full[fy0:fy0 + V.base.shape[0], fx0:fx0 + V.base.shape[1]]
    results = {'_note': 'STAGED PROPOSAL - reuses FRONT apose art bent to the diagonal rest lips; not her diagonal drawing.',
               'job_a_config': ITERATIONS[FINAL][0], 'supersample': SS, 'g_grid_step_px': GSTEP}
    sheet_rows = []
    rest_meta = json.load(open(f'{HERE}/rest_lips.json'))
    for tag in DIAG:
        d = rest_meta[tag]['view_space']; bx = d['bbox']
        box = (bx[0] - 20, bx[1] - 16, bx[2] + 20, bx[3] + 24)
        x0, y0, x1, y1 = box
        dsoft = np.asarray(Image.open(f'{HERE}/diag_{tag}_rest_mask.png')).astype(float)[y0:y1, x0:x1] / 255
        frame_v = np.load(f'{ROOT}/mouth/work/diag_{tag}_frame_in_view.npy')[y0:y1, x0:x1].astype(float)
        fr = frame_rgb(tag); face = np.clip(to_view((fr[..., 2] <= fr[..., 0] + 40).astype(float), tag), 0, 1)[y0:y1, x0:x1]
        R = {}
        for kind in ('affine', 'homography'):
            Hc, siou = fit_map(fsoft_full, dsoft, box, kind)
            R[kind] = dict(H=Hc, soft_iou=siou)
        Hc = R['homography']['H']
        # residual knots from her features: H-only render vs her frame lips
        G0 = GMap(Hc, box); m0 = g_mesh(V, G0)
        rest_h = render_to(front_stack(0, 0), (fx0, fy0), m0, box)
        sil_h = render_to(silP, (fx0, fy0), m0, box)[..., 3] / 255
        feat_h = col_features(sil_h, over_bg(frame_v, rest_h)); feat_d = col_features(dsoft, frame_v)
        res = residuals(feat_h, feat_d, x1 - x0)
        G = GMap(Hc, box, res); mG = g_mesh(V, G)
        sil_g = render_to(silP, (fx0, fy0), mG, box)[..., 3] / 255
        rest_g = render_to(front_stack(0, 0), (fx0, fy0), mG, box)
        sil_a = render_to(silP, (fx0, fy0), g_mesh(V, GMap(R['affine']['H'], box)), box)[..., 3] / 255
        comp_g = over_bg(frame_v, rest_g)
        # classifier IoU on the composite (same colour rule as the cut, her frame skin as reference)
        pad_skin_delta = (np.array(rest_meta['front_apose']['skin_rgb']) - np.array(rest_meta[tag]['view_space']['skin_rgb'])).tolist()
        feat_g = col_features(sil_g, comp_g)
        common = [x for x in feat_g if x in feat_d]
        err = {k: float(np.median([abs(feat_g[x][i] - feat_d[x][i]) for x in common])) for i, k in enumerate(('top', 'seam', 'bottom'))}
        m_in = (sil_g > .5) & (dsoft > .5)
        st_g = stats(comp_g, sil_g, np.array(rest_meta[tag]['view_space']['skin_rgb']))
        rr = dict(iou_rest=dict(affine=bin_iou(sil_a, dsoft), homography=bin_iou(sil_h, dsoft), homography_plus_mesh=bin_iou(sil_g, dsoft),
                                homography_plus_mesh_soft=soft_iou(sil_g, dsoft)),
                  front_skin_pad_minus_frame_skin_rgb=pad_skin_delta,
                  H=Hc.tolist(), affine=R['affine']['H'].tolist(), mesh_flipped_tris=mG.flipped(),
                  residual_px_max=dict(top=float(np.abs(res[0][0]).max()), seam=float(np.abs(res[0][1]).max()), bottom=float(np.abs(res[0][2]).max())),
                  feature_err_median_px=err,
                  proposal_rest_stats=dict(width=st_g['width'], height=st_g['height'], edge2080_top_median=st_g['edge2080_top_median'],
                                           edge2080_bot_median=st_g['edge2080_bot_median'], seam_fwhm_median=st_g['seam_fwhm_median'],
                                           seam_dark_median=st_g['seam_dark_median'], lip_rgb_mean=st_g['lip_rgb_mean']),
                  her_rest_stats={k: d[k] for k in ('width', 'height', 'edge2080_top_median', 'edge2080_bot_median', 'seam_fwhm_median', 'seam_dark_median', 'lip_rgb_mean')},
                  lip_colour_mae_inside_both=float(np.abs(comp_g[m_in] - frame_v[m_in]).mean()),
                  box=list(box))
        # talking grid
        od = f'{HERE}/{tag}/renders'; os.makedirs(od, exist_ok=True)
        cells = {}; tiles_blue, tiles_frame = {}, {}
        blue = np.zeros_like(frame_v); blue[..., 2] = 255
        for o in (0, .25, .5, .75, 1):
            for f in (-1, -.5, 0, .5, 1):
                P = render_to(front_stack(o, f), (fx0, fy0), mG, box)
                off_face = int(((P[..., 3] > 127.5) & (face < .5)).sum())
                P = P * face[..., None]          # clip to her own face silhouette in the frame (315 jaw edge)
                ob = over_bg(blue, P); a = P[..., 3]
                core = binary_erosion(binary_fill_holes(a > 127.5), iterations=2)   # >=2 px inside the outer edge: stage-2 area filtering softens the outer staircase only
                hy, hx = np.nonzero(core & (a < 250))
                cells[f'o{o}_f{f}'] = dict(blue_spill_px=int(((a >= 254.5) & (ob[..., 2] > ob[..., 0])).sum()),
                                           holes_px=int(len(hy)), past_jaw_before_clip_px=off_face, holes_at=[[int(x + x0), int(y + y0), round(float(a[y, x]) / 255, 3)] for y, x in zip(hy, hx)][:12])
                full = np.zeros((H, W, 4), np.uint8)
                aa = np.clip(a, 1e-9, None)[..., None]
                full[y0:y1, x0:x1, :3] = np.clip(np.round(np.where(a[..., None] > 0, P[..., :3] * 255 / aa, 0)), 0, 255)
                full[y0:y1, x0:x1, 3] = np.clip(np.round(a), 0, 255)
                Image.fromarray(full).save(f'{od}/o{o}_f{f}.png')
                tiles_blue[(o, f)] = ob; tiles_frame[(o, f)] = over_bg(frame_v, P)
        rr['talking_grid'] = dict(cells=cells, blue_spill_max=max(c['blue_spill_px'] for c in cells.values()),
                                  holes_max=max(c['holes_px'] for c in cells.values()),
                                  past_jaw_before_clip_max=max(c['past_jaw_before_clip_px'] for c in cells.values()))
        results[tag] = rr
        # sheet rows for this diagonal
        her_cut = over_bg(blue, np.dstack([frame_v * dsoft[..., None], dsoft * 255]))
        r1 = [label(zoomc(frame_v), f'{tag}: her frame f{DIAG[tag]["frame"]:03d} (view space)'),
              label(zoomc(her_cut), f'her rest lips cut (on key blue)'),
              label(zoomc(over_bg(blue, rest_h)), f'PROPOSAL front art, H only  IoU {rr["iou_rest"]["homography"]:.3f}'),
              label(zoomc(over_bg(blue, rest_g)), f'PROPOSAL H+mesh  IoU {rr["iou_rest"]["homography_plus_mesh"]:.3f}'),
              label(zoomc(comp_g), 'PROPOSAL H+mesh rest over her frame')]
        r2 = [label(zoomc(tiles_frame[(o, f)]), f'PROPOSAL {tag} Open {o} Form {f} (front art)') for o, f in ((.5, 0), (1, 0), (0, -1), (0, 1), (1, 1))]
        sheet_rows += [hcat(r1), hcat(r2)]
        print(tag, json.dumps({k: rr[k] for k in ('iou_rest', 'feature_err_median_px', 'mesh_flipped_tris', 'lip_colour_mae_inside_both')}), rr['talking_grid']['blue_spill_max'], rr['talking_grid']['holes_max'])
        # 5x5 grid image
        g = vcat([hcat([label(zoomc(tiles_frame[(o, f)], 4), f'O{o} F{f}') for f in (-1, -.5, 0, .5, 1)]) for o in (0, .25, .5, .75, 1)])
        Image.fromarray(g).save(f'{HERE}/grid_{tag}.png')
    banner = np.full((40, 400, 3), 255, np.uint8)
    banner = label(banner, 'STAGED PROPOSAL - Job B diagonals: FRONT apose mouth art bent (homography + per-column mesh) to her f033/f191 rest lips. Not her own diagonal drawing.', 30)
    Image.fromarray(vcat([banner] + sheet_rows)).save(f'{HERE}/sheet.png')
    json.dump(results, open(f'{HERE}/results.json', 'w'), indent=1)

if __name__ == '__main__':
    main()
