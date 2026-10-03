# Gates on diag_posable outputs, using rig/qa_gates.py's own functions (read-only import): G2 leak file_report
# (diagonal palette for 045/315: 5 base.png + her live mouth files + her turn frame), plus strict checks.
from common import *
import glob, hashlib
import qa_gates as G
from PIL import Image
from scipy.ndimage import label as cc
OUT = f'{ROOT}/mouth/staged/diag_posable'
INT = {(63, 35, 25), (156, 90, 74), (239, 228, 218)}
res = {'rig_md5': hashlib.md5(open(f'{ROOT}/rig/index.html', 'rb').read()).hexdigest(),
       'qa_gates_md5': hashlib.md5(open(f'{ROOT}/rig/qa_gates.py', 'rb').read()).hexdigest(), 'files': []}
for tag in ('045', '315'):
    fr = np.asarray(Image.open(f"{ROOT}/reference/apose_turn/frames/{G.DIAG_FRAME[tag]}.png").convert('RGB')).astype(int)
    frame_cols = set(map(tuple, np.unique(fr.reshape(-1, 3), axis=0)))
    face_f = ~(fr[..., 2] > fr[..., 0] + 40)
    face_v = to_view(face_f.astype(float), tag) >= .5
    for scale, pat in (('frame', f'{OUT}/{tag}/frame_scale/*.png'), ('view', f'{OUT}/{tag}/*.png')):
        for f in sorted(glob.glob(pat)):
            r = G.file_report(tag, 'mouth', f, 2.0)
            img = G.rgba(f).astype(int); op = img[..., 3] == 255
            cols = set(map(tuple, np.unique(img[op][:, :3], axis=0)))
            r['scale'] = scale; r['size'] = [img.shape[1], img.shape[0]]
            r['strict_not_in_her_frame_or_interior'] = int(sum(1 for c in cols if c not in frame_cols and c not in INT))
            r['strict_px'] = int(sum(((img[op][:, :3] == np.array(c)).all(1)).sum() for c in cols if c not in frame_cols and c not in INT)) if r['strict_not_in_her_frame_or_interior'] else 0
            face = face_f if scale == 'frame' else face_v
            r['outside_face_px'] = int((op & ~face).sum())
            if scale == 'frame':   # extra rest gate: opaque where her frame is key blue (loose rule B>max(R,G)+20) or outside her filled silhouette
                from scipy.ndimage import binary_fill_holes
                kb = fr[..., 2] > np.maximum(fr[..., 0], fr[..., 1]) + 20
                sil = binary_fill_holes(~(fr[..., 2] > fr[..., 0] + 40))
                r['opaque_on_key_blue_px'] = int((op & kb).sum()); r['opaque_outside_silhouette_px'] = int((op & ~sil).sum())
            r['alpha_values'] = sorted(map(int, np.unique(img[..., 3])))
            name = os.path.basename(f)[:-4]
            if name != 'rest':
                cls = np.load(f'{OUT}/tools/cls_{tag}_{name}_{scale}.npy'); m = cls == 3
                lab, n = cc(m, structure=np.ones((3, 3)))
                r['line'] = dict(px=int(m.sum()), components=int(n), blocks_2x2=int((m[:-1, :-1] & m[1:, :-1] & m[:-1, 1:] & m[1:, 1:]).sum()))
            res['files'].append(r)
tot = {k: sum(r[k] for r in res['files']) for k in ('off_palette', 'chroma', 'soft_edge', 'strict_px', 'outside_face_px')}
tot.update({k: sum(r.get(k, 0) for r in res['files']) for k in ('opaque_on_key_blue_px', 'opaque_outside_silhouette_px')})
for sc in ('frame', 'view'): tot[sc] = {k: sum(r[k] for r in res['files'] if r['scale'] == sc) for k in ('off_palette', 'chroma', 'soft_edge', 'strict_px', 'outside_face_px')}
res['totals'] = tot; res['n_files'] = len(res['files'])
json.dump(res, open(f'{OUT}/gate.json', 'w'), indent=1)
print(res['rig_md5'][:8], res['n_files'], tot)
for r in res['files']:
    if r['off_palette'] or r['chroma'] or r['soft_edge'] or r['strict_px'] or r['outside_face_px'] or r.get('line', {}).get('components', 1) != 1 or r.get('line', {}).get('blocks_2x2', 0): print(r)
