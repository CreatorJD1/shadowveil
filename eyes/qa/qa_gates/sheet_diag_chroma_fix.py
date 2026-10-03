#!/usr/bin/env python3
"""Before/after zoom sheet for the diagonal far-eye chroma fix -> eyes/qa/qa_gates/diag_chroma_fix.png"""
import json, numpy as np
from PIL import Image, ImageDraw
R = '/workspace/shadowveil'; D = f'{R}/eyes/staged/diagonals'; BK = f'{D}/backups_chroma_fix'
L = json.load(open(f'{R}/eyes/qa/qa_gates/fix_diag_chroma.json'))['files']; FR = {'045': 'f033', '315': 'f191'}
z = 14; rows = []
def on(bg, part): a = part[..., 3:] / 255.; return (part[..., :3] * a + bg * (1 - a)).astype(np.uint8)
for key, s in L.items():
    ang, f = key.split('/'); xs = [p['xy'][0] for p in s['px']]; ys = [p['xy'][1] for p in s['px']]
    x0, x1, y0, y1 = min(xs) - 6, max(xs) + 7, min(ys) - 6, max(ys) + 7
    B = np.asarray(Image.open(f'{BK}/{ang}/{f}.png').convert('RGBA')).astype(float)[y0:y1, x0:x1]
    A = np.asarray(Image.open(f'{D}/{ang}/{f}.png').convert('RGBA')).astype(float)[y0:y1, x0:x1]
    F = np.asarray(Image.open(f'{R}/reference/apose_turn/frames/{FR[ang]}.png').convert('RGB')).astype(float)[y0:y1, x0:x1]
    grey = np.full(F.shape, 128.); chk = np.where(((np.indices(F.shape[:2]).sum(0)) % 2)[..., None], 200., 235.) * np.ones(3)
    M = np.full(F.shape, 255, np.uint8)
    for p in s['px']:
        x, y = p['xy'][0] - x0, p['xy'][1] - y0; M[y, x] = (230, 40, 40) if p['action'].startswith('clear') else (40, 170, 40)
    M[(B[..., 3] > 0) & (M == 255).all(-1)] = (90, 90, 90)
    panels = [('before on grey', on(grey, B)), ('after on grey', on(grey, A)), ('before on checker', on(chk, B)), ('after on checker', on(chk, A)),
              ('frame', F.astype(np.uint8)), ('change: red=cleared green=snapped', M)]
    tiles = []
    for name, im in panels:
        I = Image.fromarray(im).resize((im.shape[1] * z, im.shape[0] * z), Image.NEAREST); T = Image.new('RGB', (I.width + 8, I.height + 20), 'white'); T.paste(I, (4, 18))
        ImageDraw.Draw(T).text((4, 3), name, fill=(0, 0, 0)); tiles.append(np.array(T))
    Hm = max(t.shape[0] for t in tiles); row = np.concatenate([np.pad(t, ((0, Hm - t.shape[0]), (0, 0), (0, 0)), constant_values=255) for t in tiles], 1)
    hdr = Image.new('RGB', (row.shape[1], 22), (230, 230, 230))
    ImageDraw.Draw(hdr).text((4, 5), f"{key}.png (frame x{x0}-{x1-1}, y{y0}-{y1-1}): chroma {s['chroma_before']} -> {s['chroma_after']}; cleared {s['clear']} (speck {s['speck_cleared']}), snapped to palette {s['snap']} (kept for continuity {s['kept_for_continuity']}); components {s['components_before']} -> {s['components_after']}", fill=(0, 0, 0))
    rows.append(np.concatenate([np.array(hdr), row], 0))
W = max(r.shape[1] for r in rows); rows = [np.pad(r, ((0, 10), (0, W - r.shape[1]), (0, 0)), constant_values=255) for r in rows]
Image.fromarray(np.concatenate(rows, 0)).save(f'{R}/eyes/qa/qa_gates/diag_chroma_fix.png'); print('ok')
