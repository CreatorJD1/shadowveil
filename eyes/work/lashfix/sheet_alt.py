"""Closed frame (lid_7) choice sheet: live | staged (crease kept) | staged_alt (crease hidden), every view. Temp trees only."""
import sys, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '/workspace/shadowveil/eyes/tools')
import render_eyes, lfcommon as L
z = 5; rows = []
trees = [('live (before)', f'{L.ROOT}/views'), ('staged: crease kept', f'{L.HERE}/tmp/vstaged'), ('alt: crease hidden', f'{L.HERE}/tmp/valt')]
for v in ['apose', 'tpose', 'left', 'right']:
    bx = []
    for e in L.EYES[v]:
        g = L.geo(v, e); ys, xs = np.nonzero(g['bb']); bx.append((xs.min() - 4, ys.min() - 8, xs.max() + 5, ys.max() + 3))
    x0 = min(b[0] for b in bx); y0 = min(b[1] for b in bx); x1 = max(b[2] for b in bx); y1 = max(b[3] for b in bx)
    tiles = []
    for name, root in trees:
        render_eyes.VIEWS = root; render_eyes._cache.clear()
        im = render_eyes.render(v, dict(EyeLOpen=0, EyeROpen=0), base=f'{L.ROOT}/views/{v}/base.png')[y0:y1, x0:x1, :3]
        I = Image.fromarray(im).resize(((x1 - x0) * z, (y1 - y0) * z), Image.NEAREST)
        C = Image.new('RGB', (I.width, I.height + 18), 'white'); C.paste(I, (0, 18)); ImageDraw.Draw(C).text((3, 3), f'{v} lid_7 {name}', fill=(0, 0, 0))
        tiles.append(np.array(C)); tiles.append(np.full((C.height, 8, 3), 255, np.uint8))
    rows.append(np.concatenate(tiles, 1))
Wm = max(r.shape[1] for r in rows)
rows = [np.pad(r, ((0, 8), (0, Wm - r.shape[1]), (0, 0)), constant_values=255) for r in rows]
Image.fromarray(np.concatenate(rows, 0)).save(sys.argv[1]); print('wrote', sys.argv[1])
