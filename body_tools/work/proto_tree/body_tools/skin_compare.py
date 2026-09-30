#!/usr/bin/env python3
"""Before/after sheet at 25 deg: rows = joints, columns = rest | cut parts | draft skin | shipped skin (ss2 filter).
Inputs are renderer frames (rig/index.html render path, headless Chrome) in <cut_and_draft_dir> (cut_*, skin_* = draft)
and <final_dir> (skin_* = views/apose/body/skin.json). Usage: skin_compare.py <draft_dir> <final_dir> <out.png>"""
import sys
from PIL import Image, ImageDraw
dd, fd, out = sys.argv[1:4]
J = {'ShoulderL': (822, 439), 'ShoulderR': (541, 439), 'ElbowL': (925.5, 561.5), 'ElbowR': (438, 563), 'HipL': (747, 792.5),
     'HipR': (618, 791.5), 'KneeL': (759.5, 1150), 'KneeR': (603.5, 1150), 'AnkleL': (772, 1570), 'AnkleR': (590.5, 1570)}
T, R, HD = 240, 100, 22
cols = [('rest', lambda k: f'{fd}/rest.png'), ('cut parts', lambda k: f'{dd}/cut_{k}_p.png'),
        ('draft skin', lambda k: f'{dd}/skin_{k}_p.png'), ('shipped skin', lambda k: f'{fd}/skin_{k}_p.png')]
sheet = Image.new('RGB', (110 + T * len(cols), HD + T * len(J)), (40, 40, 48)); dr = ImageDraw.Draw(sheet)
for j, (n, _) in enumerate(cols): dr.text((110 + j * T + 6, 5), n + ' (25 deg, ss2)' if j else n, fill=(255, 255, 255))
for i, (k, (cx, cy)) in enumerate(J.items()):
    dr.text((6, HD + i * T + T // 2), k, fill=(255, 255, 255))
    for j, (_, f) in enumerate(cols):
        im = Image.open(f(k)).convert('RGBA').crop((int(cx - R), int(cy - R), int(cx + R), int(cy + R)))
        bg = Image.new('RGBA', im.size, (0, 200, 0, 255)); bg.alpha_composite(im)
        sheet.paste(bg.convert('RGB').resize((T - 4, T - 4), Image.LANCZOS), (110 + j * T + 2, HD + i * T + 2))
sheet.save(out); print(out, sheet.size)
