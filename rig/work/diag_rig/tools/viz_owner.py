import json, sys, numpy as np
from PIL import Image, ImageDraw
D = '/workspace/shadowveil/rig/work/diag_rig'
out = []
for ang in sys.argv[1].split(','):
    sd = f'{D}/slots/d{ang}'; r = json.load(open(f'{sd}/body/rig.json'))
    cv = np.full((1168, 768, 3), 255, np.uint8); rng = np.random.RandomState(3)
    for p in r['parts']:
        if not p.get('file'): continue
        m = np.asarray(Image.open(f'{sd}/body/{p["file"]}'))[:1168, :768, 3] > 0
        cv[m] = rng.randint(60, 230, 3)
    for sysn in ('hands', 'hair'):
        for p in json.load(open(f'{sd}/{sysn}/rig.json'))['parts']:
            if p.get('file'):
                try: m = np.asarray(Image.open(f'{sd}/{sysn}/{p["file"]}'))[:1168, :768, 3] > 0
                except FileNotFoundError: continue
                cv[m] = (cv[m] * 0.5 + np.array([0, 0, 0] if sysn == 'hair' else [255, 0, 0]) * 0.5).astype(np.uint8)
    im = Image.fromarray(cv); d = ImageDraw.Draw(im); by = {p['id']: p for p in r['parts']}
    for p in r['parts']:
        x, y = p['pivotX'], p['pivotY']; d.ellipse([x - 4, y - 4, x + 4, y + 4], outline=(0, 0, 0), width=2)
        if p.get('parent') in by: q = by[p['parent']]; d.line([x, y, q['pivotX'], q['pivotY']], fill=(0, 0, 0), width=1)
        if p.get('wristPivot'): w = p['wristPivot']; d.line([x, y, w['x'], w['y']], fill=(0, 0, 0), width=1); d.ellipse([w['x'] - 3, w['y'] - 3, w['x'] + 3, w['y'] + 3], outline=(255, 0, 0))
    d.text((5, 5), f'd{ang} owner map (debug only)', fill=(0, 0, 0)); out.append(np.asarray(im))
Image.fromarray(np.concatenate(out, 1)).save(f'{D}/tmp/owner.png')
