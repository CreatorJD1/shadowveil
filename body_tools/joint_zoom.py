# Joint zoom sheet: every visible joint of every view, rotated -25/-12/0/+12/+25 deg (only that joint;
# BodyLean at -8/-4/0/4/8 because it is clamped to maxRotDeg 8),
# body parts only (plus WristL/R rows with the current Hands parts attached at forearm wristPivot, read-only), on a light-blue background so gaps/background show clearly.
# Writes body_tools/joint_zoom_sheet.png and body_tools/work/jz_<view>.png
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pose_render as pr
ROOT = pr.ROOT
ANG = [-25, -12, 0, 12, 25]
SIZE = {'BodyLean': 300, 'Shoulder': 170, 'Elbow': 130, 'Hip': 240, 'Knee': 130, 'Ankle': 130, 'Toe': 110}
T = 220; BG = (0, 170, 255, 255)
cache = {}
def parts(view):
    if view not in cache:
        rig = pr.load_rig(view)
        cache[view] = (rig, [(p['layer'], Image.open(os.path.join(ROOT, f'views/{view}/body/{p["file"]}')).convert('RGBa'), p['id'])
                             for p in sorted(rig['parts'], key=lambda p: p['layer']) if p.get('file')])
    return cache[view]
hcache = {}
def hand_items(view):
    # current Hands parts (read-only) at rest frames, attached to forearm_<side> like the preview does
    if view not in hcache:
        hcache[view] = [(l, im.convert('RGBa'), pid) for l, im, pid in pr.owner_parts(view) if pid.startswith('forearm_')]
    return hcache[view]
def render_crop(view, pose, box, out=T, hands=False, center=None):
    rig, items = parts(view); Wm = pr.world(rig, pose)
    if hands: items = sorted(items + hand_items(view), key=lambda t: t[0])
    x0, y0, x1, y1 = box; s = out / (x1 - x0)
    S = np.array([[s, 0, -x0*s], [0, s, -y0*s], [0, 0, 1]])
    img = Image.new('RGBA', (out, out), BG)
    for layer, im, pid in items:
        inv = np.linalg.inv(S @ Wm[pid])
        img.alpha_composite(im.transform((out, out), Image.AFFINE, tuple(inv[:2].ravel()), resample=Image.BILINEAR).convert('RGBA'))
    return img
def joints(view):
    rig, _ = parts(view)
    js = []
    for p in rig['parts']:
        if p.get('param') and not p.get('hidden'):
            k = next(k for k in SIZE if p['param'].startswith(k))
            js.append((p['param'], p['pivotX'], p['pivotY'], SIZE[k]))
    order = ['BodyLean','ShoulderL','ShoulderR','ElbowL','ElbowR','HipL','HipR','KneeL','KneeR','AnkleL','AnkleR','ToeL','ToeR']
    return sorted(js, key=lambda j: order.index(j[0]))
WR = [('rest', None, 0), ('Elbow', 'Elbow', -25), ('Elbow', 'Elbow', 25), ('Shoulder', 'Shoulder', -25), ('Shoulder', 'Shoulder', 25)]
def wrists(view):
    rig, _ = parts(view); out = []
    for p in rig['parts']:
        if p['id'].startswith('forearm') and not p.get('hidden') and p.get('wristPivot'):
            out.append((p['id'][-1], p['wristPivot']['x'], p['wristPivot']['y']))
    return out
def wrist_row(view, side, wx, wy, sz=190):
    rig, _ = parts(view); tiles = []
    for lab, j, a in WR:
        pose = {} if j is None else {f'{j}{side}': a}
        Wm = pr.world(rig, pose); cx, cy, _ = Wm[f'forearm_{side}'] @ [wx, wy, 1]   # crop follows the wrist
        box = (cx - sz/2, cy - sz/2, cx + sz/2, cy + sz/2)
        tiles.append((f'{lab} {a:+d}' if j else 'rest', render_crop(view, pose, box, hands=True)))
    return tiles
def feet(view):
    rig, _ = parts(view); P = {p['id']: p for p in rig['parts']}; out = []
    for sd in 'LR':
        f = P.get(f'foot_{sd}')
        if f and not f.get('hidden'):
            t = P.get(f'toes_{sd}'); out.append((sd, f, t if t and not t.get('hidden') else None, bool(t and t.get('notSeparable'))))
    return out
def foot_row(view, sd, f, t, sz=190):
    tiles = []
    cx, cy = ((f['pivotX'] + 2 * t['pivotX']) / 3, t['pivotY'] - 35) if t else (f['pivotX'], f['pivotY'] + 40)
    box = (cx - sz/2, cy - sz/2, cx + sz/2, cy + sz/2)
    for lab, pose in [('rest', {}), ('Ankle -20', {f'Ankle{sd}': -20}), ('Ankle +20', {f'Ankle{sd}': 20}),
                      ('Toe -30 up', {f'Toe{sd}': -30}), ('Toe +20 curl', {f'Toe{sd}': 20})]:
        if lab.startswith('Toe') and not t: tiles.append((lab + ' n/a', None)); continue
        tiles.append((lab, render_crop(view, pose, box)))
    return tiles
def sheet(view):
    js = joints(view); ws = wrists(view); fs = feet(view)
    img = Image.new('RGB', (80 + T*len(ANG), T*(len(js) + len(ws) + len(fs))), (25, 25, 25)); d = ImageDraw.Draw(img)
    for k, (sd, f, t, ns) in enumerate(fs):
        r = len(js) + len(ws) + k
        d.text((4, r*T + 6), f'{view}\nFoot{sd} bend' + ('\ntoes not\nseparable' if ns else ''), fill=(255, 255, 255))
        for c, (lab, tile) in enumerate(foot_row(view, sd, f, t)):
            if tile is not None: img.paste(tile.convert('RGB'), (80 + c*T, r*T))
            d.text((84 + c*T, r*T + 4), lab, fill=(255, 255, 0))
    for k, (side, wx, wy) in enumerate(ws):
        r = len(js) + k
        d.text((4, r*T + 6), f'{view}\nWrist{side}\n+hands', fill=(255, 255, 255))
        for c, (lab, t) in enumerate(wrist_row(view, side, wx, wy)):
            img.paste(t.convert('RGB'), (80 + c*T, r*T)); d.text((84 + c*T, r*T + 4), lab, fill=(255, 255, 0))
    for r, (prm, px, py, sz) in enumerate(js):
        box = (px - sz/2, py - sz/2, px + sz/2, py + sz/2)
        d.text((4, r*T + 6), f'{view}\n{prm}', fill=(255, 255, 255))
        angs = ANG if prm != 'BodyLean' else [-8, -4, 0, 4, 8]   # BodyLean is clamped to its maxRotDeg (8)
        if prm.startswith('Toe'): angs = [-30, -15, 0, 10, 20]      # toes: anatomical deg, -30 = up (push-off) .. +20 curl
        for c, a in enumerate(angs):
            t = render_crop(view, {prm: a}, box)
            img.paste(t.convert('RGB'), (80 + c*T, r*T)); d.text((84 + c*T, r*T + 4), f'{a:+d}', fill=(255, 255, 0))
    return img
if __name__ == '__main__':
    views = sys.argv[1:] or ['apose','tpose','left','right','back']
    os.makedirs(os.path.join(ROOT, 'body_tools/work'), exist_ok=True)
    ims = []
    for v in views:
        im = sheet(v); im.save(os.path.join(ROOT, f'body_tools/work/jz_{v}.png')); ims.append(im); print(v, im.size, flush=True)
    if len(views) == 5:
        W = max(i.size[0] for i in ims); H = sum(i.size[1] for i in ims)
        out = Image.new('RGB', (W*5, max(i.size[1] for i in ims)), (25, 25, 25))
        for i, im in enumerate(ims): out.paste(im, (i*W, 0))
        out.save(os.path.join(ROOT, 'body_tools/joint_zoom_sheet.png')); print('sheet', out.size)
