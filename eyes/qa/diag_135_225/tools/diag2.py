"""Stage 2 (read-only): discriminative test. A pixel is an eye candidate only if its tone is closer to the eye palette
(white / amber iris / green iris / lash+lid line from the 045/315 + live parts) than to her NON-eye head tones in
f033/f191 (skin, hair, ear, outline AA; eye-part alphas dilated 3 px excluded), is within TH of the eye palette,
passes cut_diag.classes() for white/iris, and is not on the silhouette AA band (2 px from #0000FF key).
Validation: same detector on f033/f191 (where the eyes are known) must find the eyes."""
import json, os, sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
sys.dont_write_bytecode = True
ROOT = '/workspace/shadowveil'; OUT = f'{ROOT}/eyes/qa/diag_135_225'; FR = f'{ROOT}/reference/apose_turn/frames'
sys.path.insert(0, f'{ROOT}/eyes/staged/diagonals'); from cut_diag import classes, LINE
BOX = (290, 40, 480, 250); TH = 16
def rgba(p): return np.array(Image.open(p).convert('RGBA'))
def frame(f): return np.array(Image.open(f'{FR}/{f}.png').convert('RGB')).astype(int)
pal = {'white': [], 'amber': [], 'green': [], 'lash': []}
srcs = [f'{ROOT}/eyes/staged/diagonals/045', f'{ROOT}/eyes/staged/diagonals/315'] + [f'{ROOT}/views/{v}/eyes' for v in ('apose', 'tpose', 'left', 'right')]
for d in srcs:
    for e, ic in (('EyeR', 'amber'), ('EyeL', 'green')):
        if not os.path.exists(f'{d}/{e}_white.png'): continue
        A = rgba(f'{d}/{e}_white.png'); w = A[..., :3][A[..., 3] > 0].astype(int); pal['white'].append(w[w.mean(1) > 150])
        A = rgba(f'{d}/{e}_iris.png'); ir = A[..., :3][A[..., 3] > 0].astype(int); _, i, _, _ = classes(ir[None], ic); pal[ic].append(ir[i[0]])
        la = np.concatenate([(lambda A: A[..., :3][A[..., 3] > 0].astype(int))(rgba(f'{d}/{e}_{p}.png')) for p in ('lash', 'lid_0')]); pal['lash'].append(la[la.mean(1) < LINE])
pal = {k: np.unique(np.concatenate(v), axis=0) for k, v in pal.items()}
# non-eye head tones from f033/f191 (eye parts excluded)
non = []
eyemask = {}
for tag, f in (('045', 'f033'), ('315', 'f191')):
    a = frame(f); m = np.zeros(a.shape[:2], bool)
    for fn in os.listdir(f'{ROOT}/eyes/staged/diagonals/{tag}'):
        if fn.endswith('.png') and 'chroma' not in fn: m |= rgba(f'{ROOT}/eyes/staged/diagonals/{tag}/{fn}')[..., 3] > 0
    eyemask[f] = m
    x0, y0, x1, y1 = BOX; sub = a[y0:y1, x0:x1]; key = (sub[..., 2] - np.maximum(sub[..., 0], sub[..., 1])) > 120
    ok = ~key & ~ndi.binary_dilation(m[y0:y1, x0:x1], iterations=3)
    non.append(sub[ok])
non = np.unique(np.concatenate(non), axis=0); Tn = cKDTree(non)
Te = {k: cKDTree(v) for k, v in pal.items()}
def detect(a):
    x0, y0, x1, y1 = BOX; sub = a[y0:y1, x0:x1]; flat = sub.reshape(-1, 3); S = sub.shape[:2]
    key = (sub[..., 2] - np.maximum(sub[..., 0], sub[..., 1])) > 120; body = ~key
    aa = ndi.binary_dilation(key, iterations=2)
    scl, ia, lum, sat = classes(sub, 'amber'); _, ig, _, _ = classes(sub, 'green')
    dn = Tn.query(flat)[0].reshape(S); de = {k: T.query(flat)[0].reshape(S) for k, T in Te.items()}
    excl = lambda k: body & ~aa & (de[k] <= TH) & (de[k] < dn)
    c = {'white': excl('white') & scl, 'amber': excl('amber') & ia, 'green': excl('green') & ig & ~ia, 'lash': excl('lash') & (lum < LINE)}
    return sub, key, c
res = {'_method': __doc__, '_threshold_rgb': TH, '_crop_frame_px': list(BOX), '_non_eye_tones': int(len(non)), '_palette_sizes': {k: int(len(v)) for k, v in pal.items()}}
col = {'white': (255, 0, 255), 'amber': (255, 140, 0), 'green': (0, 255, 0), 'lash': (255, 0, 0)}
for ang, f in (('135', 'f087'), ('225', 'f131'), ('045_validation', 'f033'), ('315_validation', 'f191')):
    a = frame(f); sub, key, c = detect(a); x0, y0, x1, y1 = BOX; st = {}
    for k, m in c.items():
        ys, xs = np.nonzero(m); lab, n = ndi.label(m, structure=np.ones((3, 3)))
        st[k] = dict(px=int(m.sum()), components=int(n), largest=int(np.bincount(lab.ravel())[1:].max()) if n else 0,
                     bbox_frame=[int(xs.min() + x0), int(ys.min() + y0), int(xs.max() + x0), int(ys.max() + y0)] if len(xs) else None)
        if f in eyemask: st[k]['px_inside_known_eye_parts'] = int((m & eyemask[f][y0:y1, x0:x1]).sum())
    res[ang] = dict(frame=f'reference/apose_turn/frames/{f}.png', **st)
    ov = (sub * 0.45).astype(int)
    for k in ('lash', 'white', 'amber', 'green'): ov[c[k]] = col[k]
    I = Image.fromarray(ov.astype(np.uint8)).resize(((x1 - x0) * 4, (y1 - y0) * 4), Image.NEAREST)
    ImageDraw.Draw(I).text((4, 4), f'{f} {ang}: discriminative eye candidates  magenta=white {st["white"]["px"]}  orange=amber {st["amber"]["px"]}  green=green {st["green"]["px"]}  red=lash/line {st["lash"]["px"]}', fill=(255, 255, 255))
    I.save(f'{OUT}/{f}_{ang.split("_")[0]}_eye_mask_discriminative_x4.png')
json.dump(res, open(f'{OUT}/results_discriminative.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if not k.startswith('_')}, indent=1))
