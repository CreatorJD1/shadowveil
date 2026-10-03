# Base Body weight_bleed: browser-rig renders (scratch tree, rig md5 562c32a7) live skin vs staged --zero-cross-limb candidate
import json, os, numpy as np
from PIL import Image, ImageDraw
D = '/workspace/scratch_basebody/out_t3'; OUT = os.path.dirname(os.path.abspath(__file__))
S = {r['tag']: r for r in json.load(open(f'{D}/summary.json'))}; res = {}; rows = []
L = lambda t, p: np.asarray(Image.open(f'{D}/{t}__{p}.png')).astype(np.int16)
for v in ('left', 'right'):
    res[v] = {'rest_px_vs_base': {c: S[f'{v}_{c}']['restPixels_vs_base'] for c in ('live', 'xlimb')}, 'skin': S[f'{v}_xlimb']['skinsrc'], 'poses': {}}
    for p in S[f'{v}_live']['frames']:
        a, b = L(f'{v}_live', p), L(f'{v}_xlimb', p); ch = (a != b).any(-1)
        nh = (b[..., 3] == 0) & (a[..., 3] > 0); ys, xs = np.nonzero(ch)
        res[v]['poses'][p] = {'px_changed': int(ch.sum()), 'new_holes': int(nh.sum()), 'bbox': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None}
        if p != 'rest' and ch.any() and not p.startswith('Hip'):
            cx, cy = int(np.median(xs)), int(np.median(ys)); R = 60
            def c(im):
                im = im[cy-R:cy+R, cx-R:cx+R].astype(np.uint8); al = im[..., 3:4] / 255.; return (im[..., :3] * al + 230 * (1 - al)).astype(np.uint8)
            d = c(b).copy(); d[ch[cy-R:cy+R, cx-R:cx+R]] = [255, 0, 255]
            row = np.concatenate([np.kron(x, np.ones((3, 3, 1), np.uint8)) for x in (c(a), c(b), d)], 1)
            lab = Image.fromarray(np.full((row.shape[0], 170, 3), 255, np.uint8)); ImageDraw.Draw(lab).text((4, 4), f'{v}\n{p}\n{int(ch.sum())} px changed', fill=(0, 0, 0)); rows.append(np.concatenate([np.asarray(lab), row], 1))
json.dump(res, open(f'{OUT}/browser_live_vs_xlimb.json', 'w'), indent=1)
hdr = Image.new('RGB', (rows[0].shape[1], 22), 'white'); ImageDraw.Draw(hdr).text((174, 5), 'live skin.json | staged --zero-cross-limb | changed px (magenta)   3x, browser rig', fill=(0, 0, 0))
Image.fromarray(np.concatenate([np.asarray(hdr)] + rows, 0)).save(f'{OUT}/sheet_browser_live_vs_xlimb.png')
for v in res:
    print(v, res[v]['rest_px_vs_base'], res[v]['skin'])
    for p, r in res[v]['poses'].items(): print('  ', p, r)
