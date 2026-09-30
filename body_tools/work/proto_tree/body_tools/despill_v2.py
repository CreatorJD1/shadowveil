#!/usr/bin/env python3
"""Blue-fringe despill v2 — PROPOSAL. Dry run is the default and the only mode that touches nothing.

Finds key-blue contamination in views/<view>/base.png: bright blue fringe blended with #0000FF along the
transparent silhouette edge. A pixel is contaminated when
    alpha > 0, B > max(R,G) + 20, B >= 120, and it lies within 3 px of a pixel with alpha < 255,
excluding
  * dark navy line art: dark-bluish pixels (max(R,G) < 60, B < 170) whose 8-connected run reaches more than
    4 px inside the silhouette (a line, not an edge fringe),
  * the mouth boxes (left x590-612 y261-283, right x760-782 y263-286; front views: the drawn-mouth bbox from
    views/<view>/mouth/rig.json),
  * each view's eye part bboxes (union of the eye PNGs' alpha bboxes and eyes/rig.json workRegion).
Fix proposed: B := max(R, G), alpha kept.

Usage:
  python3 body_tools/despill_v2.py              # dry run (default): report + previews, writes no image of the drawing
  python3 body_tools/despill_v2.py --dry-run    # same
  python3 body_tools/despill_v2.py --apply      # writes CORRECTED COPIES to body_tools/work/despill_v2_out/<view>/base.png
                                                # (never in place; replacing base.png / base_body.png is a separate step)
Note: B >= 120 deliberately leaves the dark navy edge pixels (B~25-75, R,G~0) alone; they are counted as
'darkNavyEdgeBelowB120' in the report.
Outputs: body_tools/work/despill_v2_report.json, body_tools/work/despill_preview_<view>.png
"""
import argparse, glob, json, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = ['apose', 'tpose', 'left', 'right', 'back']
MOUTH_BOX = {'left': (590, 261, 612, 283), 'right': (760, 263, 782, 286)}   # inclusive x0,y0,x1,y1

def mask_png(p, shape):
    if not os.path.exists(p): return np.zeros(shape, bool)
    m = np.array(Image.open(p))
    return (m[..., -1] if m.ndim == 3 else m) > 127

def box_mask(shape, box):
    m = np.zeros(shape, bool)
    if box: x0, y0, x1, y1 = box; m[y0:y1 + 1, x0:x1 + 1] = True
    return m

def eye_boxes(v, shape):
    m = np.zeros(shape, bool); boxes = []
    for f in glob.glob(os.path.join(ROOT, f'views/{v}/eyes/Eye*_*.png')):
        if f.endswith('_chroma.png'): continue
        a = np.array(Image.open(f).convert('RGBA'))[..., 3] > 0
        if a.any():
            ys, xs = np.nonzero(a); boxes.append((int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())))
    try:
        wr = json.load(open(os.path.join(ROOT, f'views/{v}/eyes/rig.json'))).get('workRegion')
        if wr: boxes.append(tuple(int(t) for t in wr))
    except Exception: pass
    for bx in boxes: m |= box_mask(shape, bx)
    return m, boxes

def union_alpha(files, shape):
    m = np.zeros(shape, bool)
    for f in files:
        if os.path.exists(f) and not f.endswith('_chroma.png'):
            m |= np.array(Image.open(f).convert('RGBA'))[..., 3] > 0
    return m

def analyse(v):
    base = np.array(Image.open(os.path.join(ROOT, f'views/{v}/base.png')).convert('RGBA')).astype(int)
    H, W = base.shape[:2]; R, G, B, A = base[..., 0], base[..., 1], base[..., 2], base[..., 3]
    mx = np.maximum(R, G)
    near_edge = ndimage.distance_transform_edt(A == 255) <= 3          # within 3 px of alpha < 255
    cand = (A > 0) & (B > mx + 20) & (B >= 120) & near_edge
    # navy line art: dark-bluish runs that reach well inside the silhouette
    dark = (A > 0) & (mx < 60) & (B < 170) & (B > mx)
    lab, n = ndimage.label(dark, structure=np.ones((3, 3)))
    depth = ndimage.distance_transform_edt(A == 255)
    navy = np.zeros_like(dark)
    if n:
        deep = ndimage.maximum(depth, lab, index=np.arange(1, n + 1))
        navy = np.isin(lab, np.nonzero(np.asarray(deep) > 4)[0] + 1)
    mouth_x = box_mask((H, W), MOUTH_BOX.get(v))
    try:
        dm = json.load(open(os.path.join(ROOT, f'views/{v}/mouth/rig.json'))).get('drawnMouthBBox')
        if dm and v not in MOUTH_BOX: mouth_x |= box_mask((H, W), (dm['x0'], dm['y0'], dm['x1'], dm['y1']))
    except Exception: pass
    eye_x, eboxes = eye_boxes(v, (H, W))
    excluded = {'navyLineArt': int((cand & navy).sum()), 'mouthBox': int((cand & ~navy & mouth_x).sum()),
                'eyeBox': int((cand & ~navy & ~mouth_x & eye_x).sum())}
    change = cand & ~navy & ~mouth_x & ~eye_x
    # categories (a pixel can sit in more than one; counted in each)
    hand = mask_png(os.path.join(ROOT, f'hands/{v}_hand_erase_mask.png'), (H, W))
    hair = mask_png(os.path.join(ROOT, f'hair/{v}_hair_erase_mask.png'), (H, W))
    eyes = union_alpha(glob.glob(os.path.join(ROOT, f'views/{v}/eyes/Eye*_*.png')), (H, W))
    mouth = union_alpha(glob.glob(os.path.join(ROOT, f'views/{v}/mouth/*.png')), (H, W))
    body = union_alpha(glob.glob(os.path.join(ROOT, f'views/{v}/body/*.png')), (H, W))
    bb = np.array(Image.open(os.path.join(ROOT, f'views/{v}/base_body.png')).convert('RGBA')).astype(int)
    same_in_bb = (bb == base).all(-1)
    counts = {'total': int(change.sum()), 'handMask': int((change & hand).sum()), 'hairMask': int((change & hair).sum()),
              'eyeParts': int((change & eyes).sum()), 'mouthParts': int((change & mouth).sum()),
              'bodyParts': int((change & body & same_in_bb).sum()),
              'none': int((change & ~hand & ~hair & ~eyes & ~mouth & ~(body & same_in_bb)).sum())}
    # near-miss class kept for reporting: dark navy edge pixels (blue-dominant but B < 120), NOT changed
    nearmiss = (A > 0) & (B > mx + 20) & (B < 120) & near_edge
    excluded['darkNavyEdgeBelowB120'] = int(nearmiss.sum())
    fixed = base.copy(); fixed[change, 2] = mx[change]
    return base, fixed, change, counts, excluded, eboxes, nearmiss

def preview(v, base, fixed, change, nearmiss):
    H, W = change.shape; S = 48
    pick = change if change.any() else nearmiss
    if pick.any():
        dens = ndimage.uniform_filter(pick.astype(float), S)
        cy, cx = np.unravel_index(np.argmax(dens), dens.shape)
    else: cy, cx = H // 2, W // 2
    x0 = int(np.clip(cx - S // 2, 0, W - S)); y0 = int(np.clip(cy - S // 2, 0, H - S)); Z = 8
    def panel(arr, bg):
        im = Image.new('RGBA', (S, S), bg); im.alpha_composite(Image.fromarray(arr[y0:y0 + S, x0:x0 + S].astype(np.uint8), 'RGBA'))
        return im.convert('RGB').resize((S * Z, S * Z), Image.NEAREST)
    mk = np.zeros((S, S, 3), np.uint8); mk[..., :] = 40; mk[nearmiss[y0:y0 + S, x0:x0 + S]] = (230, 200, 0); mk[change[y0:y0 + S, x0:x0 + S]] = (255, 40, 40)
    tiles = [('before / white', panel(base, (255, 255, 255, 255))), ('after / white', panel(fixed, (255, 255, 255, 255))),
             ('before / dark', panel(base, (32, 32, 32, 255))), ('after / dark', panel(fixed, (32, 32, 32, 255))),
             ('red: changed / yellow: navy edge, kept', Image.fromarray(mk).resize((S * Z, S * Z), Image.NEAREST))]
    out = Image.new('RGB', (len(tiles) * S * Z + (len(tiles) - 1) * 6, S * Z + 40), (20, 20, 20)); d = ImageDraw.Draw(out)
    for i, (t, im) in enumerate(tiles):
        out.paste(im, (i * (S * Z + 6), 40)); d.text((i * (S * Z + 6) + 4, 24), t, fill=(255, 255, 255))
    d.text((4, 5), f'{v}: {"worst" if change.any() else "no change; densest navy edge"} {S}x{S} at x{x0} y{y0}: {int(change[y0:y0+S, x0:x0+S].sum())} px changed', fill=(255, 255, 0))
    p = os.path.join(ROOT, f'body_tools/work/despill_preview_{v}.png'); out.save(p)
    return {'x': x0, 'y': y0, 'size': S, 'px': int(change[y0:y0 + S, x0:x0 + S].sum()), 'file': os.path.relpath(p, ROOT)}

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--dry-run', action='store_true', default=True, help='report only (default)')
    g.add_argument('--apply', action='store_true', help='write corrected COPIES to body_tools/work/despill_v2_out/')
    ap.add_argument('views', nargs='*', default=VIEWS)
    a = ap.parse_args()
    os.makedirs(os.path.join(ROOT, 'body_tools/work'), exist_ok=True)
    rep = {'mode': 'apply-copies' if a.apply else 'dry-run', 'rule': 'alpha>0 & B>max(R,G)+20 & B>=120 & within 3px of alpha<255; fix B:=max(R,G), alpha kept', 'views': {}}
    for v in a.views:
        base, fixed, change, counts, excluded, eboxes, nearmiss = analyse(v)
        rep['views'][v] = {'changed': counts, 'excluded': excluded, 'eyeBoxes': eboxes, 'mouthBox': MOUTH_BOX.get(v),
                           'worst': preview(v, base, fixed, change, nearmiss)}
        if a.apply:
            od = os.path.join(ROOT, f'body_tools/work/despill_v2_out/{v}'); os.makedirs(od, exist_ok=True)
            Image.fromarray(fixed.astype(np.uint8), 'RGBA').save(os.path.join(od, 'base.png'))
        print(v, json.dumps(counts), 'excluded', json.dumps(excluded), flush=True)
    json.dump(rep, open(os.path.join(ROOT, 'body_tools/work/despill_v2_report.json'), 'w'), indent=1)

if __name__ == '__main__':
    main()
