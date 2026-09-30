#!/usr/bin/env python3
"""Draft underlay generator (test fixture / starting point for Base Body; contract v1.5).
Usage: python3 rig/skin_tools/make_underlay.py <view> [--skin=...] [--cell 2]
Takes Base Body's own hidden fill from the cut parts (pixels of a part that are covered by a higher part at rest),
keeps only pixels that sit under main-skin alpha-255 pixels, packs them into one W×H image and builds an own underlay
mesh (pixel-aligned cells, one owner bone per cell, 100% weight). Writes ONLY to rig/skin_tools/drafts/:
  <view>_underlay.png, <view>_skin_ul.json (= the skin + "underlay"). Load with ?skin=draft:<view>_skin_ul.json."""
import sys, os, json
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE)); sys.path.insert(0, HERE)
import skinlib

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; view = args[0]
    opt = dict(a[2:].split('=', 1) for a in sys.argv[1:] if a.startswith('--') and '=' in a)
    cell = int(opt.get('cell', 2)); vd = f'{ROOT}/views/{view}'
    bj = json.load(open(f'{vd}/body/rig.json'))
    sp = skinlib.skin_path(vd, view, ROOT, opt.get('skin'), bj.get('skin'))
    j, V, T, L = skinlib.load(sp); W, H = Image.open(f'{vd}/base.png').size
    main_img = np.array(Image.open(os.path.join(vd, j.get('image', 'base_body.png'))).convert('RGBA'))
    lm, _ = skinlib.coverage(V, T, L, W, H)
    bone_ix = {b['name']: i for i, b in enumerate(j['bones'])}
    parts = [p for p in bj['parts'] if p.get('file') and p['id'] in bone_ix]
    ims = {p['id']: np.array(Image.open(f"{vd}/body/{p['file']}").convert('RGBA')) for p in parts}
    order = sorted(parts, key=lambda p: p['layer'])
    top = np.full((H, W), -1, np.int32)            # index (in order) of the topmost opaque part
    for k, p in enumerate(order): top[ims[p['id']][..., 3] >= 128] = k
    owner = np.full((H, W), -1, np.int32)          # highest part that is opaque but not topmost = hidden fill
    for k, p in enumerate(order): owner[(ims[p['id']][..., 3] >= 128) & (top > k)] = k
    ul_layer = int(L.min()) - 0.5
    ok = (owner >= 0) & (main_img[..., 3] == 255) & (lm > ul_layer)
    owner[~ok] = -1
    img = np.zeros((H, W, 4), np.uint8)
    for k, p in enumerate(order): m = owner == k; img[m] = ims[p['id']][m]
    img[owner >= 0, 3] = 255
    # mesh: cells of `cell` px containing pixels of exactly one owner; mixed cells fall back to 1 px cells
    verts, vix, tris, wts = [], {}, [], []
    def vid(x, y, k):
        key = (x, y, k)
        if key not in vix: vix[key] = len(verts); verts.append([x, y]); wts.append([[bone_ix[order[k]['id']], 1.0]])
        return vix[key]
    def quad(x, y, s, k):
        a, b, c, d = vid(x, y, k), vid(x + s, y, k), vid(x + s, y + s, k), vid(x, y + s, k); tris.extend([[a, b, c], [a, c, d]])
    ys, xs = np.nonzero(owner >= 0)
    cells = {(x // cell, y // cell) for x, y in zip(xs, ys)}
    for cx, cy in sorted((int(a), int(b)) for a, b in cells):
        blk = owner[cy * cell:(cy + 1) * cell, cx * cell:(cx + 1) * cell]; ks = set(blk[blk >= 0].tolist())
        if len(ks) == 1: quad(cx * cell, cy * cell, cell, ks.pop())
        else:
            for dy in range(blk.shape[0]):
                for dx in range(blk.shape[1]):
                    if blk[dy, dx] >= 0: quad(cx * cell + dx, cy * cell + dy, 1, int(blk[dy, dx]))
    os.makedirs(f'{HERE}/drafts', exist_ok=True)
    png = f'{HERE}/drafts/{view}_underlay.png'; Image.fromarray(img).save(png)
    j2 = dict(j); j2['underlay'] = {'image': os.path.relpath(png, vd), 'vertices': verts, 'triangles': tris, 'weights': wts,
        'note': 'DRAFT test fixture from the cut parts\' hidden fill (make_underlay.py); layer defaults to just below the main mesh'}
    out = f'{HERE}/drafts/{view}_skin_ul.json'
    assert '/views/' not in out
    json.dump(j2, open(out, 'w'), separators=(',', ':'))
    per = {order[k]['id']: int((owner == k).sum()) for k in range(len(order)) if (owner == k).any()}
    print(json.dumps({'png': os.path.relpath(png, ROOT), 'skin': os.path.relpath(out, ROOT), 'pixels': int((owner >= 0).sum()), 'perBone': per,
                      'vertices': len(verts), 'triangles': len(tris)}))

if __name__ == '__main__': main()
