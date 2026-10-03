"""Read-only: test f087 (135) / f131 (225) head regions for eye pixels (lash/lid line, white, iris).
Frame source and classes() follow eyes/staged/diagonals/cut_diag.py. Writes only into eyes/qa/diag_135_225/."""
import json, os, sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
ROOT = '/workspace/shadowveil'; OUT = f'{ROOT}/eyes/qa/diag_135_225'
sys.dont_write_bytecode = True; sys.path.insert(0, f'{ROOT}/eyes/staged/diagonals'); from cut_diag import classes, LINE   # import only (main() not run)
FR = f'{ROOT}/reference/apose_turn/frames'
def ld(p):
    a = np.array(Image.open(p).convert('RGBA')); return a[..., :3][a[..., 3] > 0].astype(int)
# ---- palette from staged diagonal parts (045/315) + live view parts
pal = {'white': [], 'amber': [], 'green': [], 'lash': []}
srcs = [f'{ROOT}/eyes/staged/diagonals/045', f'{ROOT}/eyes/staged/diagonals/315'] + [f'{ROOT}/views/{v}/eyes' for v in ('apose', 'tpose', 'left', 'right')]
for d in srcs:
    for e, ic in (('EyeR', 'amber'), ('EyeL', 'green')):
        if not os.path.exists(f'{d}/{e}_white.png'): continue
        w = ld(f'{d}/{e}_white.png'); pal['white'].append(w[(w.mean(1) > 150)])        # sclera tones only
        ir = ld(f'{d}/{e}_iris.png'); s, i, _, _ = classes(ir[None], ic); pal[ic].append(ir[i[0]])  # iris-class tones only
        la = [ld(f'{d}/{e}_lash.png'), ld(f'{d}/{e}_lid_0.png')]; la = np.concatenate(la); pal['lash'].append(la[la.mean(1) < LINE])
pal = {k: np.unique(np.concatenate(v), axis=0) for k, v in pal.items()}
TH = 16   # RGB euclidean distance to the nearest palette tone
res = {}
for ang, fr, box in (('135', 'f087', (290, 40, 480, 250)), ('225', 'f131', (290, 40, 480, 250))):
    a = np.array(Image.open(f'{FR}/{fr}.png').convert('RGB')).astype(int); H, W, _ = a.shape
    x0, y0, x1, y1 = box; sub = a[y0:y1, x0:x1]
    key = (sub[..., 2] - np.maximum(sub[..., 0], sub[..., 1])) > 120; body = ~key
    scl, iris_a, lum, sat = classes(sub, 'amber'); _, iris_g, _, _ = classes(sub, 'green')
    s_ = sub.astype(float); skin = body & (lum > 95) & (lum < 200) & (sat > 0.2) & (sat < 0.7) & (s_[..., 2] < 0.8 * s_[..., 0])
    flat = sub.reshape(-1, 3)
    near = {k: (cKDTree(v).query(flat)[0].reshape(sub.shape[:2]) <= TH) & body for k, v in pal.items()}
    # candidates: palette tone AND cut_diag class test
    cand = {'white': near['white'] & scl, 'amber': near['amber'] & iris_a, 'green': near['green'] & iris_g & ~iris_a}
    # lash / lid-line tone: dark pixels inside the skin area (enclosed by skin within 2 px), i.e. a line on the face rather than hair mass/outline
    dark = body & (lum < LINE)
    skin_d = ndi.binary_dilation(skin, iterations=2)
    hair_mass = ndi.binary_opening(dark, iterations=2)                      # thick dark regions = hair
    hair_mass = ndi.binary_dilation(hair_mass, iterations=1)
    edge = ndi.binary_dilation(key, iterations=2) & body                    # silhouette band (cheek edge / outline)
    line_in_skin = dark & near['lash'] & skin_d & ~hair_mass & ~edge
    cand['lash_line'] = line_in_skin
    # face-edge zone: skin pixels within 4 px of background (cheek/jaw silhouette)
    face_edge = skin & ndi.binary_dilation(key, iterations=4)
    stat = {}
    for k, m in cand.items():
        ys, xs = np.nonzero(m)
        lab, n = ndi.label(m, structure=np.ones((3, 3)))
        stat[k] = dict(px=int(m.sum()), components=int(n),
                       bbox_frame=[int(xs.min() + x0), int(ys.min() + y0), int(xs.max() + x0), int(ys.max() + y0)] if len(xs) else None,
                       largest=int(np.bincount(lab.ravel())[1:].max()) if n else 0)
    stat['palette_only_px'] = {k: int(v.sum()) for k, v in near.items()}
    stat['skin_px'] = int(skin.sum()); stat['face_edge_skin_px'] = int(face_edge.sum())
    res[ang] = dict(frame=f'reference/apose_turn/frames/{fr}.png', crop_frame_px=list(box), **stat)
    # images: plain crop x4, overlay x4 (dimmed frame + colored candidates), palette-only overlay x4
    z = 4
    def up(img): return Image.fromarray(img.astype(np.uint8)).resize(((x1 - x0) * z, (y1 - y0) * z), Image.NEAREST)
    up(sub).save(f'{OUT}/{fr}_{ang}_head_x4.png')
    col = {'white': (255, 0, 255), 'amber': (255, 140, 0), 'green': (0, 255, 0), 'lash_line': (255, 0, 0)}
    ov = (sub * 0.45).astype(int)
    ov[face_edge] = [90, 90, 160]
    for k, m in cand.items(): ov[m] = col[k]
    I = up(ov); D = ImageDraw.Draw(I)
    D.text((4, 4), f'{fr} {ang}deg candidates: magenta=white {stat["white"]["px"]} orange=amber {stat["amber"]["px"]} green=green {stat["green"]["px"]} red=lash/line-in-skin {stat["lash_line"]["px"]}; slate=cheek-edge skin', fill=(255, 255, 255))
    I.save(f'{OUT}/{fr}_{ang}_eye_mask_overlay_x4.png')
    ov2 = (sub * 0.45).astype(int)
    for k, c in (('lash', (255, 0, 0)), ('white', (255, 0, 255)), ('amber', (255, 140, 0)), ('green', (0, 255, 0))): ov2[near[k]] = c
    I = up(ov2); ImageDraw.Draw(I).text((4, 4), f'{fr} palette-tone-only (no shape/class test): red=lash tone (= hair tone), magenta=white, orange=amber, green=green', fill=(255, 255, 255))
    I.save(f'{OUT}/{fr}_{ang}_palette_only_x4.png')
res['_palette_sizes'] = {k: int(len(v)) for k, v in pal.items()}; res['_threshold_rgb'] = TH; res['_palette_sources'] = [p.replace(ROOT + '/', '') for p in srcs]
json.dump(res, open(f'{OUT}/results.json', 'w'), indent=1); print(json.dumps(res, indent=1))
