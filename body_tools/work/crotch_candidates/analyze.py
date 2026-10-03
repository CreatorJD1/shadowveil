# Base Body crotch candidates: metrics + before/after sheet from browser-rig renders on the scratch tree (rig md5 562c32a7)
import json, os, numpy as np
from PIL import Image, ImageDraw
D = '/workspace/scratch_basebody/out_t2'; OUT = os.path.dirname(os.path.abspath(__file__)); ROOT = '/workspace/shadowveil'
S = {r['tag']: r for r in json.load(open(f'{D}/summary.json'))}
L = lambda t, p: np.asarray(Image.open(f'{D}/{t}__{p}.png')).astype(np.int16)
CUT = {'apose': (681, 838, 875), 'tpose': (682, 830, 870), 'back': (681, 835, 870)}
res = {}; sheet_rows = []
ref = Image.open(f'{ROOT}/reference/approved_turnaround.jpg').convert('RGB')
REFBOX = {'apose': (222, 400, 362, 560), 'tpose': (222, 400, 362, 560), 'back': (1430, 400, 1570, 560)}
for v in ('apose', 'tpose', 'back'):
    cx, y0c, y1c = CUT[v]; bx0, bx1, by0, by1 = cx - 41, cx + 41, y0c - 18, y1c + 25
    base = np.asarray(Image.open(f'{ROOT}/views/{v}/base.png').convert('RGBA')).astype(np.int16)
    pal = np.unique(base[base[..., 3] == 255][:, :3], axis=0).astype(np.int32); lut = np.zeros(1 << 24, bool)
    for dr in range(-2, 3):
        for dg in range(-2, 3):
            for db in range(-2, 3):
                q = np.clip(pal + [dr, dg, db], 0, 255); lut[(q[:, 0] << 16) | (q[:, 1] << 8) | q[:, 2]] = True
    rest_op = base[..., 3] > 0
    res[v] = {}
    for c in ('live', 'ulnb', 'cb24'):
        t = f'{v}_{c}'; r = {'rest_px_vs_base': S[t]['restPixels_vs_base'], 'underlay': S[t]['underlay'], 'skin': S[t]['skinsrc'], 'errors': len(S[t]['errors']), 'poses': {}}
        rest_live = L(f'{v}_live', 'rest'); rest_c = L(t, 'rest'); r['rest_vs_live_px'] = int((rest_live != rest_c).any(-1).sum())
        for p in S[t]['frames']:
            im = L(t, p); lv = L(f'{v}_live', p); op = im[..., 3] > 0
            box = np.zeros(op.shape, bool); box[by0:by1, bx0:bx1] = True; above = box.copy(); above[y1c:, :] = False
            hole = rest_op & ~op
            dark = op & (im[..., :3].max(-1) < 70); darkl = (lv[..., 3] > 0) & (lv[..., :3].max(-1) < 70)
            wide = np.zeros(op.shape, bool); wide[y0c - 60:y1c + 200, cx - 140:cx + 140] = True
            leak = op & ~rest_op & (lv[..., 3] == 0) & wide           # colour where her rest art and the live rig are both background
            px = im[..., :3][(im[..., 3] == 255) & wide].astype(np.int32); offp = ~lut[(px[:, 0] << 16) | (px[:, 1] << 8) | px[:, 2]]
            r['poses'][p] = {'holes_crotch_box': int((hole & box).sum()), 'holes_above_apex': int((hole & above).sum()),
                             'notch_closed': bool((hole & above).sum() == 0),
                             'new_dark_px_vs_live_box': int((dark & ~darkl & box).sum()), 'dark_px_box': int((dark & box).sum()),
                             'leak_px_outside_rest_and_live': int(leak.sum()), 'off_palette_px_roi_tol2': int(offp.sum()),
                             'vs_live_px': int((im != lv).any(-1).sum())}
        res[v][c] = r
    # sheet rows: reference crop | live | ulnb | cb24 per pose (holes magenta, new dark px vs live cyan)
    X0, X1, Y0, Y1 = cx - 110, cx + 110, y0c - 60, y1c + 110
    rc = ref.crop(REFBOX[v]).resize((X1 - X0, Y1 - Y0))
    for p in ['rest', 'wide_HipL-1_HipR+1', 'HipL-1', 'HipR+1', 'Hips+1', 'Hips-1', 'HipL+1', 'HipR-1']:
        cells = [np.asarray(rc)]
        for c in ('live', 'ulnb', 'cb24'):
            im = L(f'{v}_{c}', p); lv = L(f'{v}_live', p); al = im[..., 3:4] / 255.
            vis = (im[..., :3] * al + 235 * (1 - al)).astype(np.uint8); vis[rest_op & (im[..., 3] == 0) & (np.arange(im.shape[0])[:, None] < y1c)] = [255, 0, 255]
            nd = (im[..., 3] > 0) & (im[..., :3].max(-1) < 70) & ~((lv[..., 3] > 0) & (lv[..., :3].max(-1) < 70)); vis[nd] = [0, 230, 230]
            cells.append(vis[Y0:Y1, X0:X1])
        row = np.concatenate([np.kron(x, np.ones((2, 2, 1), np.uint8)) for x in cells], 1)
        lab = Image.fromarray(np.full((row.shape[0], 150, 3), 255, np.uint8)); dd = ImageDraw.Draw(lab); dd.text((4, 4), f'{v}\n{p}', fill=(0, 0, 0))
        for k, c in enumerate(('live', 'ulnb', 'cb24')):
            q = res[v][c]['poses'][p]; dd.text((4, 40 + 26 * k), f"{c}: holes>apex {q['holes_above_apex']}\n  newdark {q['new_dark_px_vs_live_box']} leak {q['leak_px_outside_rest_and_live']}", fill=(0, 0, 0))
        sheet_rows.append(np.concatenate([np.asarray(lab), row], 1))
json.dump(res, open(f'{OUT}/crotch_metrics.json', 'w'), indent=1)
hdr = Image.new('RGB', (sheet_rows[0].shape[1], 24), 'white')
ImageDraw.Draw(hdr).text((154, 6), 'reference/approved_turnaround.jpg crop (front for apose/tpose, back) | live (before) | ulnb = underlay --crotch 0, no --bgk (Coder rec.) | cb24 = inner-thigh blend R24   2x; magenta = notch hole, cyan = new dark px vs live', fill=(0, 0, 0))
Image.fromarray(np.concatenate([np.asarray(hdr)] + sheet_rows, 0)).save(f'{OUT}/sheet_crotch_before_after.png')
for v in res:
    for c, r in res[v].items():
        print(v, c, 'rest', r['rest_px_vs_base'], 'rest_vs_live', r['rest_vs_live_px'], 'underlay ok', (r['underlay'] or {}).get('ok'), (r['underlay'] or {}).get('src'), 'errs', r['errors'])
        for p, q in r['poses'].items(): print('   ', p, q)
