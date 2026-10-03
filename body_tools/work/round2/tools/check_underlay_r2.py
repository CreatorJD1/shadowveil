#!/usr/bin/env python3
"""Validate a skin.json underlay (contract v1.5).
Usage: python3 rig/skin_tools/check_underlay.py <view> [--skin=draft|draft:<file>|<file in views/<view>/body/>]
Default skin = the one declared in views/<view>/body/rig.json ("skin").
Rule: the underlay's rest footprint (pixels it would draw with all parameters at 0) must lie entirely under main-skin
pixels with alpha 255 whose triangle layer is above the underlay layer. Any footprint pixel over a transparent pixel,
a partially transparent main pixel, or a main pixel at/below the underlay layer rejects the underlay.
Writes rig/skin_tools/drafts/<view>_underlay_check.png (grey = main skin, green = valid footprint, red = violations).
Exit: 0 valid, 1 rejected, 2 no skin / no underlay."""
import sys, os, json
import numpy as np
from PIL import Image
HERE = '/workspace/shadowveil/rig/skin_tools'; ROOT = '/workspace/r2tree'; sys.path.insert(0, HERE); OUTD = '/workspace/shadowveil/body_tools/work/round2/drafts'
import skinlib

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args: print(__doc__); return 2
    view = args[0]; which = next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('--skin=')), None)
    vd = f'{ROOT}/views/{view}'
    try: bj = json.load(open(f'{vd}/body/rig.json'))
    except Exception: bj = {}
    sp = skinlib.skin_path(vd, view, ROOT, which, bj.get('skin') if isinstance(bj, dict) else None)
    if not sp or not os.path.exists(sp): print(json.dumps({'view': view, 'error': 'no skin declared/found', 'skin': sp})); return 2
    j, V, T, L = skinlib.load(sp); errs = skinlib.validate(j, V, T)
    base = Image.open(f'{vd}/base.png'); W, H = base.size
    ip = os.path.normpath(os.path.join(vd, j.get('image', 'base_body.png')))
    if errs or not os.path.exists(ip): print(json.dumps({'view': view, 'skin': os.path.relpath(sp, ROOT), 'error': errs or 'main image missing'})); return 1
    main_img = np.array(Image.open(ip).convert('RGBA'))
    ul, uerr = skinlib.underlay_load(j, V, T, L, vd, W, H)
    out = {'view': view, 'skin': os.path.relpath(sp, ROOT)}
    if ul is None and not uerr: out['underlay'] = None; print(json.dumps(out)); return 2
    if uerr: out['underlay'] = {'ok': False, 'errors': uerr}; print(json.dumps(out, indent=1)); return 1
    lm, _ = skinlib.coverage(V, T, L, W, H)
    r, fp, bad = skinlib.underlay_check(ul, main_img, lm, W, H)
    r.update({'image': os.path.relpath(ul['file'], ROOT), 'ownMesh': ul['own'], 'vertices': int(len(ul['V'])), 'triangles': int(len(ul['T'])), 'identityUV': ul['identityUV']})
    out['underlay'] = r
    vis = np.full((H, W, 3), 255, np.uint8); m = main_img[..., 3] > 0
    vis[m] = 190
    vis[fp & ~bad] = (60, 200, 60); vis[bad] = (255, 0, 0)
    os.makedirs(OUTD, exist_ok=True); png = f'{OUTD}/{view}_underlay_check.png'; Image.fromarray(vis).save(png)
    out['map'] = os.path.relpath(png, ROOT)
    print(json.dumps(out, indent=1)); return 0 if r['ok'] else 1

if __name__ == '__main__': sys.exit(main())
