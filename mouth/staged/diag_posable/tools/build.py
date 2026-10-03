#!/usr/bin/env python3
"""diag_posable build (STAGED). Frame-scale (768x1168, her turn-frame coords) is primary; view-scale (1365x1739) secondary.
rest  = her own closed lips cut from f033/f191 (hard alpha, RGB = her frame px, nothing painted).
shapes = FRONT apose mouth art (Job A mesh_bend) bent onto her diagonal lips by diag.py's G map, rendered NATIVELY at each
scale (no down/upsampling of a finished part), then: hard alpha, 1 px skeleton line in her diagonal seam tone, lip px snapped
to her diagonal frame lip tones, interior snapped to inner/tongue/teeth, skin pad = her frame skin, clipped to her face."""
from common import *
from PIL import Image
from scipy.ndimage import binary_dilation, binary_fill_holes, label as cc
from scipy.spatial import cKDTree
from skimage.morphology import skeletonize
OUT = f'{ROOT}/mouth/staged/diag_posable'
FW, FH = 768, 1168
SHAPES = {'M': (0, -1), 'smile': (0, 1), 'OH_half': (.5, -1), 'AA_half': (.5, 0), 'EE_half': (.5, 1), 'OH': (1, -1), 'AA': (1, 0), 'EE': (1, 1)}
INTERIOR = {'inner': (63, 35, 25), 'tongue': (156, 90, 74), 'teeth': (239, 228, 218)}   # #3F2319 #9C5A4A #EFE4DA (live rig.json colours)
FRONT_SKIN = np.array([184, 129, 86.]); FRONT_LIP_MEAN = np.array([117.7, 77.4, 49.0])
lum = lambda c: c[..., 0] * .299 + c[..., 1] * .587 + c[..., 2] * .114

def class_layers(L):
    """premul class stack: R = interior visible, G = line visible (non-interior px with lum<35), B unused; A = alpha"""
    out = {}
    for k in ORDER:
        P = L[k]; a = P[..., 3]; rgb = np.where(a[..., None] > 0, P[..., :3] * 255 / np.clip(a, 1e-9, None)[..., None], 0)
        Q = np.zeros_like(P); Q[..., 3] = a
        if k == 'interior': Q[..., 0] = a
        else: Q[..., 1] = a * (lum(rgb) < 35)
        out[k] = Q
    return out

def render(L, mesh, box, ss):
    V, _ = VC()
    P = D.render_to(stack(L), V.off, mesh, box, ss)
    Q = D.render_to(stack(class_layers(L)), V.off, mesh, box, ss)
    return P, Q

def her_tones(tag):
    rgb, skin, soft, comp = cut_frame(tag)
    m = rest_mask_frame(tag)
    cols = rgb[m].astype(int); u, c = np.unique(cols, axis=0, return_counts=True)
    core = m & (soft >= 0.9)                              # her lip body (not the pale AA edge)
    lipt = np.unique(rgb[core].astype(int), axis=0)
    dark = cols[lum(cols.astype(float)) <= np.percentile(lum(cols.astype(float)), 12)]
    du, dc = np.unique(dark, axis=0, return_counts=True); line = du[np.argmax(dc)]
    # her local skin tones: frame px around the mouth that are not lip and not key blue
    x0, y0, x1, y1 = DIAG[tag]['search']; ring = np.zeros(rgb.shape[:2], bool); ring[y0:y1, x0:x1] = True
    ring &= ~binary_dilation(m, iterations=2) & (rgb[..., 2] <= rgb[..., 0] + 40)
    sk = rgb[ring].astype(int); su, sc = np.unique(sk, axis=0, return_counts=True)
    skin_c = su[np.argmin(((su - skin) ** 2).sum(1))]
    return rgb.astype(np.uint8), lipt, line, skin_c

_rm = {}
def rest_mask_frame(tag):
    if tag not in _rm:
        rgb, skin, soft, comp = cut_frame(tag)
        fc = binary_fill_holes(comp)
        _rm[tag] = (fc | (binary_dilation(fc) & (soft >= 0.25))) & ~(rgb[..., 2] > rgb[..., 0] + 40)
    return _rm[tag]

def finish(P, Q, box, canvas, frame_bg, lipmask, face, tones, line_rgb, skin_rgb, pad_pal=None):
    """P,Q in box; returns full-canvas RGBA uint8 + class map + stats"""
    x0, y0, x1, y1 = box; Wc, Hc = canvas
    a = P[..., 3] / 255; op = (a >= .5) & face[y0:y1, x0:x1]
    fb = frame_bg[y0:y1, x0:x1].astype(int)
    lm = lipmask[y0:y1, x0:x1]
    # her closed lips + their pale outer ring (her drawing, within 2 px of the lip cut and not plain skin): covered by the pad
    # on open shapes so no ghost of the rest mouth shows around a different shape
    hl = lm | (binary_dilation(lm, iterations=2) & (np.sqrt(((fb - skin_rgb) ** 2).sum(-1)) > 18) & ~(fb[..., 2] > fb[..., 0] + 40))
    peek = hl & ~op                                       # her rest lips not covered by the shape -> skin pad covers them
    hl = hl & face[y0:y1, x0:x1]
    op2 = op | hl
    rgb = np.where(a[..., None] > 0, P[..., :3] / np.clip(a, 1e-9, None)[..., None], 0)
    ac = np.clip(Q[..., 3], 1e-9, None)
    intr = (Q[..., 0] / ac > .5) & op
    linecov = Q[..., 1] / 255
    line = bridge(skeletonize((linecov > .2) & op) & ~peek, op)
    dS = ((rgb - FRONT_SKIN) ** 2).sum(-1); dL = ((rgb - FRONT_LIP_MEAN) ** 2).sum(-1)
    skin = op2 & ~intr & ~line & ((dS < 35 ** 2) | (dS < dL) | peek)        # skin/lip blends at the edge go to skin (flat, no halo)
    lip = op & ~intr & ~line & ~skin
    out = np.zeros((y1 - y0, x1 - x0, 4), np.uint8); cls = np.zeros((y1 - y0, x1 - x0), np.uint8)
    # interior -> nearest of inner/tongue/teeth
    IT = np.array(list(INTERIOR.values()))
    if intr.any(): out[intr, :3] = IT[cKDTree(IT).query(rgb[intr])[1]]; cls[intr] = 1
    # lip -> nearest of HER diagonal lip tones after the front->diag mean tone shift
    shift = tones.mean(0) - FRONT_LIP_MEAN
    if lip.any(): out[lip, :3] = tones[cKDTree(tones).query(rgb[lip] + shift)[1]]; cls[lip] = 2
    out[line, :3] = line_rgb; cls[line] = 3
    # skin pad: her own frame skin px where the frame shows skin there, else her local skin tone
    if skin.any():
        ok = skin & ~hl & ~(fb[..., 2] > fb[..., 0] + 40)
        if pad_pal is None: out[ok, :3] = fb[ok]                      # frame scale: her exact frame px
        else: out[ok, :3] = pad_pal[cKDTree(pad_pal).query(fb[ok])[1]]  # view scale: resampled frame px snapped to her frame colours
        out[skin & ~ok, :3] = skin_rgb; cls[skin] = 4
    # skin pad is only kept where it has to hide her rest lips (hl); elsewhere it would just repeat her frame -> transparent
    padout = skin & ~hl
    op2 = op2 & ~padout; cls[padout] = 0; out[padout] = 0
    out[..., 3] = np.where(op2, 255, 0)
    full = np.zeros((Hc, Wc, 4), np.uint8); full[y0:y1, x0:x1] = out
    fcls = np.zeros((Hc, Wc), np.uint8); fcls[y0:y1, x0:x1] = cls
    return full, fcls, dict(peek_covered_px=int(peek.sum()), line_px=int(line.sum()), interior_px=int(intr.sum()), lip_px=int(lip.sum()), skin_px=int(skin.sum()))

def bridge(m, allow, maxgap=3):
    """join skeleton components whose nearest px are <= maxgap apart with a 1 px straight run (inside the opaque mask)"""
    m = m.copy()
    for _ in range(4):
        lab, n = cc(m, structure=np.ones((3, 3)))
        if n < 2: break
        pts = [np.argwhere(lab == i) for i in range(1, n + 1)]; done = False
        for i in range(n):
            for j in range(i + 1, n):
                d = np.sqrt(((pts[i][:, None] - pts[j][None]) ** 2).sum(-1)); k = np.unravel_index(np.argmin(d), d.shape)
                if d[k] <= maxgap:
                    (ya, xa), (yb, xb) = pts[i][k[0]], pts[j][k[1]]; L = int(max(abs(ya - yb), abs(xa - xb)))
                    for t in range(1, L):
                        y, x = int(round(ya + (yb - ya) * t / L)), int(round(xa + (xb - xa) * t / L))
                        if allow[y, x]: m[y, x] = True
                    done = True
        if not done: break
    return m

def line_breaks(cls):
    m = cls == 3; lab, n = cc(m, structure=np.ones((3, 3)))
    sizes = sorted([int((lab == i).sum()) for i in range(1, n + 1)], reverse=True)
    # thickness: any 2x2 block fully line = thicker than 1 px
    blk = m[:-1, :-1] & m[1:, :-1] & m[:-1, 1:] & m[1:, 1:]
    return dict(components=n, sizes=sizes, blocks_2x2=int(blk.sum()))

def chroma(img):
    """#0000FF convention as live mouth/<view>/<shape>_chroma.png: part over pure blue, RGB"""
    a = img[..., 3:4] / 255.; bg = np.zeros(img.shape[:2] + (3,)); bg[..., 2] = 255
    return np.round(img[..., :3] * a + bg * (1 - a)).astype(np.uint8)

def main():
    V, C = VC(); log = {}
    for tag in DIAG:
        s, dx, dy = fit(tag)
        frame, lipt, line_rgb, skin_rgb = her_tones(tag)
        fmask = rest_mask_frame(tag)
        fi = frame.astype(int)
        face_f = ~(fi[..., 2] > np.maximum(fi[..., 0], fi[..., 1]) + 20)   # her silhouette minus key blue AND blue-tinted edge px (loose rule)
        frame_v = np.clip(np.round(to_view(frame.astype(float), tag)), 0, 255).astype(np.uint8)
        vmask = to_view(fmask.astype(float), tag) >= .5
        face_v = to_view(face_f.astype(float), tag) >= .5
        od, of = f'{OUT}/{tag}', f'{OUT}/{tag}/frame_scale'
        for d in (od, of, f'{od}/chroma', f'{of}/chroma'): os.makedirs(d, exist_ok=True)
        # ---- rest
        rf = np.zeros((FH, FW, 4), np.uint8); rf[fmask, :3] = frame[fmask]; rf[fmask, 3] = 255
        rv = np.zeros((H, W, 4), np.uint8); rv[vmask, :3] = frame_v[vmask]; rv[vmask, 3] = 255
        Image.fromarray(rf).save(f'{of}/rest.png'); Image.fromarray(rv).save(f'{od}/rest.png')
        Image.fromarray(chroma(rf)).save(f'{of}/chroma/rest_chroma.png'); Image.fromarray(chroma(rv)).save(f'{od}/chroma/rest_chroma.png')
        ref = np.asarray(Image.open(f"{ROOT}/reference/apose_turn/frames/f{DIAG[tag]['frame']:03d}.png").convert('RGB'))
        comp_f = np.where(rf[..., 3:4] == 255, rf[..., :3], ref)
        comp_v = np.where(rv[..., 3:4] == 255, rv[..., :3], frame_v)
        L = {'rest': dict(frame_px=int(fmask.sum()), view_px=int(vmask.sum()),
             diff_frame_vs_ref_px=int((comp_f != ref).any(-1).sum()), diff_view_vs_resample_px=int((comp_v != frame_v).any(-1).sum()))}
        # ---- shapes, native at both scales
        mG, vbox = gmesh(tag); mF = to_frame_mesh(mG, tag)
        fx0, fy0 = int(np.floor((vbox[0] - dx) / s)) - 2, int(np.floor((vbox[1] - dy) / s)) - 2
        fbox = (fx0, fy0, int(np.ceil((vbox[2] - dx) / s)) + 2, int(np.ceil((vbox[3] - dy) / s)) + 2)
        lip_tones = lipt.astype(int)
        fcol = frame.reshape(-1, 3).astype(int); pad_pal = np.unique(fcol[~(fcol[:, 2] > fcol[:, 0] + 40)], axis=0)
        for name, (o, f) in SHAPES.items():
            Ld = render_cell(V, C, cfg, o, f)['L']
            Pf, Qf = render(Ld, mF, fbox, 8); Pv, Qv = render(Ld, mG, vbox, 4)
            imf, cf, stf = finish(Pf, Qf, fbox, (FW, FH), frame, fmask, face_f, lip_tones, line_rgb, skin_rgb)
            imv, cv_, stv = finish(Pv, Qv, vbox, (W, H), frame_v, vmask, face_v, lip_tones, line_rgb, skin_rgb, pad_pal)
            stv['pad_px_outside_her_lips'] = int(((imv[..., 3] == 255) & (cv_ == 4) & ~vmask).sum())
            Image.fromarray(imf).save(f'{of}/{name}.png'); Image.fromarray(imv).save(f'{od}/{name}.png')
            Image.fromarray(chroma(imf)).save(f'{of}/chroma/{name}_chroma.png'); Image.fromarray(chroma(imv)).save(f'{od}/chroma/{name}_chroma.png')
            np.save(f'{ROOT}/mouth/staged/diag_posable/tools/cls_{tag}_{name}_frame.npy', cf); np.save(f'{ROOT}/mouth/staged/diag_posable/tools/cls_{tag}_{name}_view.npy', cv_)
            L[name] = dict(MouthOpen=o, MouthForm=f, frame=dict(stf, lines=line_breaks(cf)), view=dict(stv, lines=line_breaks(cv_)))
        L['_tones'] = dict(her_lip_tones=len(lip_tones), line_rgb=line_rgb.tolist(), skin_rgb=skin_rgb.tolist(), frame_box=list(fbox), view_box=list(vbox))
        log[tag] = L
        print(tag, json.dumps(L['rest']), {k: (v['frame']['lines']['components'], v['view']['lines']['components']) for k, v in L.items() if k in SHAPES})
    json.dump(log, open(f'{ROOT}/mouth/staged/diag_posable/build_log.json', 'w'), indent=1)

if __name__ == '__main__':
    main()
