# Base Body handorder wrist trim: metrics + sheet from the scratch-tree renders (read-only; writes here)
import json, os, numpy as np
from PIL import Image, ImageDraw
D = '/workspace/scratch_basebody/out_t1'; OUT = os.path.dirname(os.path.abspath(__file__))
S = {r['tag']: r for r in json.load(open(f'{D}/summary.json'))}
L = lambda t, p: np.asarray(Image.open(f'{D}/{t}__{p}.png')).astype(np.int16)
WP = {'left': {'L': (678, 852)}, 'right': {'R': (676, 857)}, 'apose': {}, 'tpose': {}, 'back': {'L': (308, 730), 'R': (1055, 730)}}
res = {}
views = ['left', 'right', 'apose', 'tpose', 'back']; poses = list(S['left_hot']['frames'])
for v in views:
    res[v] = {'rest_px_vs_base': {c: S[f'{v}_{c}']['restPixels_vs_base'] for c in ('def', 'ctl', 'ho', 'hot')},
              'hot_loaded_trim_dir': any('handorder_wrist_trim' in s for s in S[f'{v}_hot']['staged']), 'def_staged_requests': len(S[f'{v}_def']['staged']),
              'errors': sum(len(S[f'{v}_{c}']['errors']) for c in ('def', 'ctl', 'ho', 'hot')), 'poses': {}}
    for p in poses:
        a, b, c = L(f'{v}_ho', p), L(f'{v}_hot', p), L(f'{v}_ctl', p)
        ch = (a != b).any(-1); nh = (b[..., 3] == 0) & (a[..., 3] > 0); nh_c = (b[..., 3] == 0) & (c[..., 3] > 0)
        ys, xs = np.nonzero(ch)
        res[v]['poses'][p] = {'hot_vs_ho_px': int(ch.sum()), 'new_holes_vs_ho': int(nh.sum()), 'holes_vs_ctl': int(nh_c.sum()),
                              'hot_vs_ctl_px': int((c != b).any(-1).sum()), 'ho_vs_ctl_px': int((c != a).any(-1).sum()),
                              'changed_bbox': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None}
json.dump(res, open(f'{OUT}/render_metrics.json', 'w'), indent=1)
for v in views:
    print(v, res[v]['rest_px_vs_base'], 'trim loaded', res[v]['hot_loaded_trim_dir'], 'errs', res[v]['errors'])
    for p, r in res[v]['poses'].items():
        if r['hot_vs_ho_px'] or r['new_holes_vs_ho'] or r['holes_vs_ctl']: print('  ', p, r)
# sheet: left/right wrist crops, rows = poses, cols = ctl | ho | trimmed | diff(ho vs trimmed, magenta) ; 4x zoom
rows = []; Z = 4; R_ = 34
for v, s in (('left', 'L'), ('right', 'R')):
    cx, cy = WP[v][s]
    for p in ['rest', f'Wrist{s}+1', f'Wrist{s}-1', f'Elbow{s}+1', f'Elbow{s}-1', 'EW+1', 'EW-1']:
        ims = [L(f'{v}_{c}', p) for c in ('ctl', 'ho', 'hot')]
        if p == 'rest' or 'Wrist' in p:
            ox, oy = cx, cy
        else:  # follow the wrist: centre on changed/ho-vs-ctl bbox
            d = (ims[0] != ims[1]).any(-1); ys, xs = np.nonzero(d[cy-200:cy+200, cx-200:cx+200]) if d.any() else ([], [])
            ox, oy = (int(np.median(xs)) + cx - 200, int(np.median(ys)) + cy - 200) if len(xs) else (cx, cy)
        crop = lambda im: im[oy-R_:oy+R_, ox-R_:ox+R_]
        cs = []
        for im in ims:
            c = crop(im).astype(np.uint8); bg = np.full(c.shape[:2] + (3,), 230, np.uint8); al = c[..., 3:4] / 255.
            cs.append((c[..., :3] * al + bg * (1 - al)).astype(np.uint8))
        dd = cs[2].copy(); dm = (crop(ims[1]) != crop(ims[2])).any(-1); dd[dm] = [255, 0, 255]; hm = (crop(ims[2])[..., 3] == 0) & (crop(ims[1])[..., 3] > 0); dd[hm] = [0, 255, 255]
        cs.append(dd); row = np.concatenate([np.kron(c, np.ones((Z, Z, 1), np.uint8)) for c in cs], 1)
        lab = Image.fromarray(np.full((row.shape[0], 150, 3), 255, np.uint8)); ImageDraw.Draw(lab).text((4, 4), f'{v}\n{p}', fill=(0, 0, 0)); rows.append(np.concatenate([np.asarray(lab), row], 1))
hdr = Image.new('RGB', (rows[0].shape[1], 22), 'white'); ImageDraw.Draw(hdr).text((154, 5), 'hairless control (palm over forearm) | handorder (untrimmed staged skin) | handorder + TRIMMED skin | diff untrimmed vs trimmed (magenta), new hole (cyan)   4x', fill=(0, 0, 0))
Image.fromarray(np.concatenate([np.asarray(hdr)] + rows, 0)).save(f'{OUT}/sheet_wrist_trim.png'); print('sheet', f'{OUT}/sheet_wrist_trim.png')
