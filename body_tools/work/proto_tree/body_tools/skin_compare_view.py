#!/usr/bin/env python3
"""Per-view compare sheet at 25 deg (ss2): rows = joints of the declared skin, columns = rest | cut parts | skin (+underlay).
Frames come from the renderer (headless Chrome, /workspace/jt/shots.js): <dir>/rest.png, cut_<Param>.png, skin_<Param>.png.
Usage: skin_compare_view.py <view> <frames_dir> <out.png>   |   --spec <view> > spec.json (frame list for shots.js)"""
import sys, json
from PIL import Image, ImageDraw
def joints(view):
    j = json.load(open(f'views/{view}/body/skin.json')); vis = {p['id'] for p in json.load(open(f'views/{view}/body/rig.json'))['parts'] if p.get('file')}
    return [(b['param'], b['pivot']) for b in j['bones'] if b['name'] in vis and b.get('param') and b['param'][:-1] in ('Shoulder', 'Elbow', 'Hip', 'Knee', 'Ankle', 'Toe')]
if sys.argv[1] == '--spec':
    sp = [{'name': 'rest', 'body': 'skin', 'rest': True}]
    for k, _ in joints(sys.argv[2]): sp += [{'name': f'cut_{k}', 'body': 'cut', 'q': 'ss2', 'params': {k: 1}}, {'name': f'skin_{k}', 'body': 'skin', 'q': 'ss2', 'params': {k: 1}}]
    print(json.dumps(sp)); sys.exit()
view, fd, out = sys.argv[1:4]; J = joints(view)
T, R, HD = 240, 100, 22
cols = [('rest', lambda k: f'{fd}/rest.png'), ('cut parts', lambda k: f'{fd}/cut_{k}.png'), ('skin+underlay', lambda k: f'{fd}/skin_{k}.png')]
sheet = Image.new('RGB', (110 + T * len(cols), HD + T * len(J)), (40, 40, 48)); dr = ImageDraw.Draw(sheet)
for j, (n, _) in enumerate(cols): dr.text((110 + j * T + 6, 5), n + ' (25 deg, ss2)' if j else n, fill=(255, 255, 255))
for i, (k, (cx, cy)) in enumerate(J):
    dr.text((6, HD + i * T + T // 2), k, fill=(255, 255, 255))
    for j, (_, f) in enumerate(cols):
        im = Image.open(f(k)).convert('RGBA').crop((int(cx - R), int(cy - R), int(cx + R), int(cy + R)))
        bg = Image.new('RGBA', im.size, (0, 200, 0, 255)); bg.alpha_composite(im)
        sheet.paste(bg.convert('RGB').resize((T - 4, T - 4), Image.LANCZOS), (110 + j * T + 2, HD + i * T + 2))
sheet.save(out); print(out, sheet.size)
