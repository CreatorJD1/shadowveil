# Contact sheet: per view -> rest (whole character), colour-coded part map with pivots, arms raised ~20deg, one knee bent ~20deg.
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pose_render as pr
ROOT = pr.ROOT
VIEWS = sys.argv[1:] or ['apose','tpose','left','right','back']
SC = 0.4
COL = {'head':(200,200,200),'torso':(230,80,80),'pelvis':(120,60,200),'upperArm_L':(60,180,60),'upperArm_R':(240,200,40),
       'forearm_L':(30,120,30),'forearm_R':(200,140,0),'thigh_L':(40,160,230),'thigh_R':(240,120,200),
       'shin_L':(20,90,160),'shin_R':(180,60,140),'foot_L':(0,60,100),'foot_R':(120,30,90),'toes_L':(0,200,200),'toes_R':(255,120,200)}
def poses(view):
    rig = pr.load_rig(view); near = rig.get('profile', {}).get('nearSide')
    if view in ('apose','tpose'): sL, sR = -20, 20      # her L arm is on viewer right
    elif view == 'back': sL, sR = 20, -20
    elif view == 'left': sL = sR = 20                   # faces viewer-left: forward raise = clockwise
    else: sL = sR = -20
    arms = {'ShoulderL': sL, 'ShoulderR': sR}
    if view == 'left': knee = {'KneeL': -20}
    elif view == 'right': knee = {'KneeR': 20}
    else: knee = {'KneeR': 20, 'HipR': 0}
    return arms, knee
def partmap(view):
    rig = pr.load_rig(view); W, H = rig['canvas']
    img = np.zeros((H, W, 4), np.uint8); img[..., 2] = 255; img[..., 3] = 255
    lab = np.load(os.path.join(ROOT, f'body_tools/work/lab_{view}.npy'))
    from build_body_parts import PARTS
    for i, pn in enumerate(PARTS):
        img[lab == i, :3] = COL[pn]
    im = Image.fromarray(img, 'RGBA').resize((int(W*SC), int(H*SC)), Image.NEAREST)
    d = ImageDraw.Draw(im)
    for p in rig['parts']:
        if p.get('hidden'): continue
        if p['param'] or p['id'] == 'pelvis':
            x, y = p['pivotX']*SC, p['pivotY']*SC; d.ellipse([x-4, y-4, x+4, y+4], fill=(255,255,255), outline=(0,0,0))
        if 'wristPivot' in p:
            x, y = p['wristPivot']['x']*SC, p['wristPivot']['y']*SC; d.rectangle([x-3, y-3, x+3, y+3], fill=(255,0,255))
    return im
tiles = []
for v in VIEWS:
    ex = pr.owner_parts(v)
    arms, knee = poses(v)
    row = [pr.render(v, {}, SC, extra=ex), partmap(v), pr.render(v, arms, SC, extra=ex), pr.render(v, knee, SC, extra=ex)]
    tiles.append((v, row))
w, h = tiles[0][1][0].size
sheet = Image.new('RGB', (w*4, (h+24)*len(tiles)), (30,30,30)); d = ImageDraw.Draw(sheet)
for r, (v, row) in enumerate(tiles):
    for c, t in enumerate(row):
        sheet.paste(t.convert('RGB'), (c*w, r*(h+24)+24))
    for c, lab in enumerate(['rest', 'part map + pivots (white) / wrist (magenta)', 'arms raised ~20', 'knee bent ~20']):
        d.text((c*w+6, r*(h+24)+6), f'{v}: {lab}', fill=(255,255,255))
out = os.path.join(ROOT, 'body_tools/contact_sheet.png') if len(VIEWS) == 5 else f'/tmp/sv/cs_{"_".join(VIEWS)}.png'
sheet.save(out); print(out)
