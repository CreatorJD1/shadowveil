#!/usr/bin/env python3
"""Job B step 1: cut her closed rest lips out of the diagonal turn frames (45 = f033, 315 = f191) and map them to
view space with the read-only fit in body_tools/work/apose_turn/diagonals/diagonals.json (base = scale*frame + d).
Lips are found by colour distance from her local skin colour (no painting; RGB is her frame pixels, resampled
bilinearly, alpha = the measured lip coverage)."""
import json, os, sys
import numpy as np, cv2
from PIL import Image
from scipy.ndimage import label, binary_fill_holes, binary_dilation
ROOT = '/workspace/shadowveil'
HERE = f'{ROOT}/mouth/staged/diagonals'
W, H = 1365, 1739
DJ = json.load(open(f'{ROOT}/body_tools/work/apose_turn/diagonals/diagonals.json'))
DIAG = {'045': dict(angle='45', frame=33, search=(330, 198, 385, 228)),
        '315': dict(angle='315', frame=191, search=(383, 198, 438, 228))}
D0, D1 = 25.0, 75.0     # colour-distance ramp (RGB units) from skin -> lip coverage 0..1

def fit(tag):
    f = DJ['diagonals'][DIAG[tag]['angle']]['view_fit']; return f['scale'], f['dx'], f['dy']

def frame_rgb(tag):
    return np.asarray(Image.open(f"{ROOT}/reference/apose_turn/frames/f{DIAG[tag]['frame']:03d}.png").convert('RGB')).astype(float)

def to_view(img, tag, interp=cv2.INTER_LINEAR):
    """frame-space image -> full view canvas, pixel-centre convention, bilinear"""
    s, dx, dy = fit(tag)
    M = np.array([[s, 0, dx + 0.5 * s - 0.5], [0, s, dy + 0.5 * s - 0.5]])
    return cv2.warpAffine(img.astype(np.float32), M, (W, H), flags=interp, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

def skin_ref(rgb, box):
    x0, y0, x1, y1 = box; c = rgb[y0:y1, x0:x1].reshape(-1, 3)
    Y = c @ [0.299, 0.587, 0.114]
    skin = c[(Y > np.percentile(Y, 40)) & (c[:, 2] < c[:, 0])]        # bright, not key blue
    return np.median(skin, 0)

def lipness(rgb, skin):
    d = np.sqrt(((rgb - skin) ** 2).sum(-1))
    return np.clip((d - D0) / (D1 - D0), 0, 1)

def cut_frame(tag):
    rgb = frame_rgb(tag); box = DIAG[tag]['search']; x0, y0, x1, y1 = box
    skin = skin_ref(rgb, box)
    lp = np.zeros(rgb.shape[:2]); lp[y0:y1, x0:x1] = lipness(rgb[y0:y1, x0:x1], skin)
    blue = (rgb[..., 2] > rgb[..., 0] + 40)
    lp[blue] = 0
    lab, n = label(lp > 0.5, structure=np.ones((3, 3)))
    sizes = [(lab == i).sum() for i in range(1, n + 1)]
    comp = binary_fill_holes(lab == 1 + int(np.argmax(sizes)))
    near = binary_dilation(comp, iterations=2)
    soft = np.where(comp, np.maximum(lp, 0.5 * comp), lp * near)      # inside the component >= .5, AA ring kept
    soft = np.where(binary_fill_holes(comp), np.maximum(soft, 1.0 * binary_fill_holes(binary_dilation(comp) ) * (lp > 0.2) ), soft)
    soft[binary_fill_holes(comp) & ~binary_dilation(~comp)] = 1.0        # interior highlight pixels count as lip
    return rgb, skin, soft, comp

def edge_widths(alpha, cols, which):
    """20-80 rise distance along columns (px) for the top ('t') or bottom ('b') outer edge of a soft mask"""
    out = []
    for x in cols:
        a = alpha[:, x]
        if a.max() < 0.8: continue
        ys = np.nonzero(a >= 0.8)[0]
        if which == 't':
            i = ys[0]; seg = a[max(0, i - 8):i + 1]; ry = np.arange(len(seg))
        else:
            i = ys[-1]; seg = a[i:i + 9][::-1]; ry = np.arange(len(seg))
        if len(seg) < 2 or seg[0] > 0.2: continue
        y2 = np.interp(0.2, seg, ry); y8 = np.interp(0.8, seg, ry)
        out.append(y8 - y2)
    return out

def seam_profile(rgb, alpha, skin):
    """per column: seam row (darkest, sub-pixel) and dark-line FWHM, inside the lip mask"""
    Y = rgb @ np.array([0.299, 0.587, 0.114])
    Yl = float(np.median(Y[alpha > 0.9]))          # her lip body tone; the seam is the line darker than it
    dark = np.clip(Yl - Y, 0, None) * (alpha > 0.5)
    rows, fw, dk = {}, {}, {}
    for x in np.nonzero((alpha > 0.5).any(0))[0]:
        col = dark[:, x]; i = int(np.argmax(col))
        if col[i] <= 0: continue
        a, b, c = col[max(i - 1, 0)], col[i], col[min(i + 1, len(col) - 1)]
        den = a - 2 * b + c; off = 0.5 * (a - c) / den if abs(den) > 1e-9 else 0
        rows[int(x)] = i + 0.5 + off
        half = b / 2; lo = i
        while lo > 0 and col[lo - 1] >= half: lo -= 1
        hi = i
        while hi < len(col) - 1 and col[hi + 1] >= half: hi += 1
        # sub-pixel FWHM
        l = lo - (col[lo] - half) / max(col[lo] - col[lo - 1], 1e-9) if lo > 0 else lo
        h = hi + (col[hi] - half) / max(col[hi] - col[hi + 1], 1e-9) if hi < len(col) - 1 else hi
        fw[int(x)] = float(min(h - l + 1, hi - lo + 2)); dk[int(x)] = float(b)
    return rows, fw, dk

def stats(rgb, soft, skin):
    m = soft > 0.5
    ys, xs = np.nonzero(m)
    cols = range(xs.min(), xs.max() + 1)
    et = edge_widths(soft, cols, 't'); eb = edge_widths(soft, cols, 'b')
    rows, fw, dk = seam_profile(rgb, soft, skin)
    w = soft * m
    sx = sorted(rows)
    return dict(bbox=[int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1],
                width=int(xs.max() - xs.min() + 1), height=int(ys.max() - ys.min() + 1),
                area_px=float(soft.sum()), area_bin=int(m.sum()),
                centroid=[float((soft * np.arange(soft.shape[1])[None]).sum() / soft.sum() + 0.5),
                          float((soft * np.arange(soft.shape[0])[:, None]).sum() / soft.sum() + 0.5)],
                corners=[[sx[0] + 0.5, rows[sx[0]]], [sx[-1] + 0.5, rows[sx[-1]]]],
                seam_center_row=float(np.median([rows[x] for x in sx[len(sx) // 3: 2 * len(sx) // 3]])),
                edge2080_top_median=float(np.median(et)) if et else None,
                edge2080_bot_median=float(np.median(eb)) if eb else None,
                seam_fwhm_median=float(np.median(list(fw.values()))), seam_dark_median=float(np.median(list(dk.values()))),
                lip_rgb_mean=[float(v) for v in (rgb[m].mean(0))], skin_rgb=[float(v) for v in skin])

def front_reference(view='apose'):
    """her front rest lips in base.png measured with the same colour rule (for sharpness comparison)"""
    base = np.asarray(Image.open(f'{ROOT}/views/{view}/base.png').convert('RGBA')).astype(float)
    rj = json.load(open(f'{ROOT}/views/{view}/mouth/rig.json')) if os.path.exists(f'{ROOT}/views/{view}/mouth/rig.json') else None
    rest = np.asarray(Image.open(f'{ROOT}/views/{view}/mouth/rest.png').convert('RGBA'))[..., 3] > 0
    ys, xs = np.nonzero(rest); box = (xs.min() - 15, ys.min() - 12, xs.max() + 16, ys.max() + 13)
    rgb = base[..., :3]; skin = skin_ref(rgb, box)
    lp = np.zeros(rest.shape); x0, y0, x1, y1 = box; lp[y0:y1, x0:x1] = lipness(rgb[y0:y1, x0:x1], skin)
    soft = np.where(binary_dilation(rest, iterations=1), lp, 0); soft[rest & ~binary_dilation(~rest)] = 1.0
    return rgb, skin, soft, rest

if __name__ == '__main__':
    out = {}
    frgb, fskin, fsoft, frest = front_reference()
    out['front_apose'] = stats(frgb, fsoft, fskin)
    for tag in DIAG:
        rgb, skin, soft, comp = cut_frame(tag)
        st_frame = stats(rgb, soft, skin)
        vrgb = to_view(rgb, tag); vsoft = np.clip(to_view(soft, tag), 0, 1)
        st_view = stats(vrgb.astype(float), vsoft, skin)
        s, dx, dy = fit(tag)
        cut = np.zeros((H, W, 4), np.uint8); cut[..., :3] = np.clip(np.round(vrgb), 0, 255).astype(np.uint8)
        cut[..., 3] = np.round(vsoft * 255).astype(np.uint8)
        Image.fromarray(cut).save(f'{HERE}/diag_{tag}_rest_lips.png')
        Image.fromarray(np.round(vsoft * 255).astype(np.uint8)).save(f'{HERE}/diag_{tag}_rest_mask.png')
        fr = np.zeros((H, W, 4), np.uint8); fr[..., :3] = np.clip(np.round(vrgb), 0, 255); fr[..., 3] = 255
        np.save(f'{ROOT}/mouth/work/diag_{tag}_frame_in_view.npy', vrgb.astype(np.float32))
        out[tag] = dict(frame=f"f{DIAG[tag]['frame']:03d}", view_fit=dict(scale=s, dx=dx, dy=dy),
                        frame_space=st_frame, view_space=st_view,
                        offset_from_apose_anchor=[st_view['centroid'][0] - 681, st_view['centroid'][1] - 286])
    json.dump(out, open(f'{HERE}/rest_lips.json', 'w'), indent=1)
    for k, v in out.items():
        vs = v.get('view_space', v)
        print(k, {kk: vs[kk] for kk in ('bbox', 'width', 'height', 'area_px', 'centroid', 'seam_center_row', 'edge2080_top_median', 'edge2080_bot_median', 'seam_fwhm_median', 'seam_dark_median')})
