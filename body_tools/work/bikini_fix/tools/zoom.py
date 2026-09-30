# zoom.py OUT.png dir1 [dir2 ...] -- poses: hipR+25 hipR-25 hipL+25 hipL-25 ; crops: R corner, crotch, L corner (4x) rows=dirs*poses
import sys
from PIL import Image
out, dirs = sys.argv[1], sys.argv[2:]
poses = ['hipR+25', 'hipR-25', 'hipL+25', 'hipL-25']
boxes = [(525, 685, 625, 785), (625, 795, 740, 900), (740, 685, 840, 785)]
S = 2
rows = []
for d in dirs:
    for p in poses:
        im = Image.open(f'{d}/{p}.png').convert('RGBA'); bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); bg = bg.convert('RGB')
        rows.append([bg.crop(b).resize(((b[2] - b[0]) * S, (b[3] - b[1]) * S), Image.LANCZOS) for b in boxes])
W = sum(c.width for c in rows[0]); H = max(c.height for c in rows[0])
o = Image.new('RGB', (W, H * len(rows)), (255, 255, 255))
for r, row in enumerate(rows):
    x = 0
    for c in row: o.paste(c, (x, r * H)); x += c.width
o.save(out)
