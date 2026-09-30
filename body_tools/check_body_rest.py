#!/usr/bin/env python3
# Base Body rest check: composites every view's body parts (views/<view>/body/rig.json, sorted by layer,
# all at rest, x/y offsets applied) and diffs against views/<view>/base_body.png. Must be 0 px everywhere.
# Also validates part files: full-canvas RGBA, no leftover chroma blue (#0000FF within tolerance),
# no white background, hidden parts carry no file.
import json, os, sys
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = ['apose', 'tpose', 'left', 'right', 'back']
PARAMS = ['BodyLean','ShoulderL','ShoulderR','ElbowL','ElbowR','HipL','HipR','KneeL','KneeR','AnkleL','AnkleR','ToeL','ToeR']
out = {}; ok = True
for v in VIEWS:
    d = os.path.join(ROOT, f'views/{v}')
    rig = json.load(open(f'{d}/body/rig.json'))
    base = Image.open(f'{d}/base_body.png').convert('RGBA'); W, H = base.size
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    problems = []
    if rig.get('params') != PARAMS: problems.append('params list mismatch')
    for p in sorted(rig['parts'], key=lambda p: p['layer']):
        if not (200 <= p['layer'] <= 299): problems.append(f"{p['id']} layer {p['layer']} outside 200-299")
        if p.get('hidden'):
            if p.get('file'): problems.append(f"{p['id']} hidden but has a file")
            continue
        im = Image.open(f"{d}/body/{p['file']}")
        if im.mode != 'RGBA' or im.size != (W, H): problems.append(f"{p['id']} not full-canvas RGBA"); im = im.convert('RGBA')
        a = np.array(im).astype(int); vis = a[..., 3] > 0
        blue = vis & (a[..., 2] > 200) & (a[..., 0] < 60) & (a[..., 1] < 60)
        white = vis & (a[..., :3].min(-1) > 245)
        if blue.any(): problems.append(f"{p['id']} {int(blue.sum())} chroma-blue px")
        if white.sum() > 50: problems.append(f"{p['id']} {int(white.sum())} white px")
        img.alpha_composite(im, (int(p['x']), int(p['y'])))
    A = np.array(img).astype(int); B = np.array(base).astype(int)
    diff = (np.abs(A - B).max(-1) > 0) & ~((A[..., 3] == 0) & (B[..., 3] == 0))
    out[v] = {'diffPx': int(diff.sum()), 'problems': problems}
    if diff.any() or problems: ok = False
print(json.dumps(out, indent=1))
print('PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
