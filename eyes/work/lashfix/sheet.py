"""Contact sheet: lid frames 0-7 per eye, live (before) vs staged (after), zoomed. Renders from temp trees only.
Usage: python3 sheet.py <view> <out.png> [zoom] [eye]"""
import sys, json, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '/workspace/shadowveil/eyes/tools')
import render_eyes, lfcommon as L
v, out = sys.argv[1], sys.argv[2]; z = int(sys.argv[3]) if len(sys.argv) > 3 else 6
eyes = [sys.argv[4]] if len(sys.argv) > 4 else L.EYES[v]
base = f'{L.ROOT}/views/{v}/base.png'
trees = [('before (live)', f'{L.ROOT}/views'), ('after (staged)', f'{L.HERE}/tmp/vstaged')]
boxes = {}
for e in eyes:
    g = L.geo(v, e); ys, xs = np.nonzero(g['bb']); boxes[e] = (xs.min() - 4, ys.min() - 6, xs.max() + 5, ys.max() + 3)
Y0 = min(b[1] for b in boxes.values()); Y1 = max(b[3] for b in boxes.values())
boxes = {e: (b[0], Y0, b[2], Y1) for e, b in boxes.items()}   # same rows for both eyes of a view
cols = []
for e in eyes:
    for name, root in trees:
        render_eyes.VIEWS = root; render_eyes._cache.clear(); x0, y0, x1, y1 = boxes[e]; tiles = []
        for k in range(8):
            o = 1 - k / 7
            im = render_eyes.render(v, dict(EyeLOpen=o, EyeROpen=o), base=base)[y0:y1, x0:x1, :3]
            im = np.array(Image.fromarray(im).resize(((x1 - x0) * z, (y1 - y0) * z), Image.NEAREST))
            tiles.append(im); tiles.append(np.full((4, im.shape[1], 3), 255, np.uint8))
        col = np.concatenate([np.full((22, tiles[0].shape[1], 3), 255, np.uint8)] + tiles, 0)
        I = Image.fromarray(col); ImageDraw.Draw(I).text((4, 5), f'{v} {e} {name}', fill=(0, 0, 0)); cols.append(np.array(I))
        cols.append(np.full((col.shape[0], 8, 3), 255, np.uint8))
sheet = np.concatenate(cols, 1)
lab = np.full((sheet.shape[0], 30, 3), 255, np.uint8); L_ = Image.fromarray(lab); d = ImageDraw.Draw(L_)
th = (sheet.shape[0] - 22) // 8
for k in range(8): d.text((4, 22 + k * th + th // 2 - 5), f'k{k}', fill=(0, 0, 0))
Image.fromarray(np.concatenate([np.array(L_), sheet], 1)).save(out); print('wrote', out, sheet.shape)
