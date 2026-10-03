#!/usr/bin/env python3
"""Job A deliverables: renders, derived parts, contact sheets, results.json (STAGED, nothing live)."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run import *

Z = 8
def to_canvas(V, crop_u8):
    full = np.zeros((H, W, 4), np.uint8); x0, y0 = V.off
    full[y0:y0 + crop_u8.shape[0], x0:x0 + crop_u8.shape[1]] = crop_u8
    return full

def mouth_crop_box(V):
    x0, y0 = V.off
    return (V.xmin - 6 - x0, min(c['Rt'] for c in V.cols.values()) - 4 - y0,
            V.xmax + 7 - x0, max(c['Rb'] for c in V.cols.values()) + 10 - y0)

def on_blue(img_u8):
    a = img_u8[..., 3:4] / 255.0
    out = img_u8[..., :3] * a + np.array([0, 0, 255]) * (1 - a)
    return np.rint(out).astype(np.uint8)

def zoom(rgb, box, z=Z):
    c = rgb[box[1]:box[3], box[0]:box[2]]
    return np.kron(c, np.ones((z, z, 1), np.uint8))

def label(img, text, h=22):
    im = Image.new('RGB', (img.shape[1], img.shape[0] + h), (255, 255, 255))
    im.paste(Image.fromarray(img), (0, h))
    ImageDraw.Draw(im).text((4, 4), text, fill=(0, 0, 0))
    return np.array(im)

def hcat(ims, gap=6):
    hh = max(i.shape[0] for i in ims)
    out = [np.pad(i, ((0, hh - i.shape[0]), (0, gap), (0, 0)), constant_values=255) for i in ims]
    return np.concatenate(out, 1)

def vcat(ims, gap=6):
    ww = max(i.shape[1] for i in ims)
    out = [np.pad(i, ((0, gap), (0, ww - i.shape[1]), (0, 0)), constant_values=255) for i in ims]
    return np.concatenate(out, 0)

def main():
    label_, cfg = ITERATIONS[FINAL]
    res = run_cfg(cfg, keep=True)
    S = summarise(res)
    sheet_rows, grid_imgs = [], {}
    for v in VIEWS:
        V = view_for(v, cfg)
        od = f'{HERE}/{v}'; os.makedirs(f'{od}/parts', exist_ok=True); os.makedirs(f'{od}/renders', exist_ok=True)
        # derived parts (full canvas): bodies with skin pad, overlapping flaps, notch-filled interior
        L0 = res[v][(0, 0)]['_cell']
        srcs = {'upper_lip': V.layers_src['upper_body'], 'lower_lip': V.layers_src['lower_body'],
                'upper_flap': V.flapsets['overlap'][0], 'lower_flap': V.flapsets['overlap'][1], 'interior': V.interior}
        for k, a in srcs.items(): Image.fromarray(to_canvas(V, a), 'RGBA').save(f'{od}/parts/{k}.png')
        box = mouth_crop_box(V)
        tiles = {}
        for (o, f), m in res[v].items():
            st = stack(m['_cell']['L']); u8 = unpremul_u8(st)
            Image.fromarray(to_canvas(V, u8), 'RGBA').save(f'{od}/renders/o{o}_f{f}.png')
            tiles[(o, f)] = (zoom(on_blue(u8), box), zoom(m['_comp'][..., :3], box))
        # 5x5 grid sheet (blue and on-face)
        rows = []
        for o in OPENS:
            rows.append(hcat([label(tiles[(o, f)][0], f'{v} Open {o} Form {f}') for f in FORMS]))
        rows_face = []
        for o in OPENS:
            rows_face.append(hcat([label(tiles[(o, f)][1], f'{v} Open {o} Form {f} (on base.png)') for f in FORMS]))
        Image.fromarray(vcat(rows)).save(f'{HERE}/grid_{v}.png')
        Image.fromarray(vcat(rows_face)).save(f'{HERE}/grid_{v}_on_face.png')
        # her shapes beside bent
        her = her_crops(V)
        pairs = []
        for (o, f), n in HER.items():
            m = res[v][(o, f)]
            hb = zoom(on_blue(her[n]['img']), box)
            tag = f"IoU sil {m['iou_sil']}" + (f" open {m['iou_opening']}" if m.get('iou_opening') else '')
            pairs.append(hcat([label(hb, f'{v} HER {n}.png'), label(tiles[(o, f)][0], f'BENT Open {o} Form {f}  {tag}')], gap=2))
        for i in range(0, 9, 3): sheet_rows.append(hcat(pairs[i:i + 3], gap=18))
    Image.fromarray(vcat(sheet_rows, gap=14)).save(f'{HERE}/sheet.png')
    # results.json
    hist = json.load(open(f'{HERE}/iterations.json'))
    out = {
        'status': 'STAGED prototype - not live, not referenced by rig/ or views/*/mouth/rig.json',
        'job': 'A: offline mesh-bend mouth (apose, tpose)',
        'sampling': 'bilinear, premultiplied alpha, pixel centres at i+0.5',
        'drawOrder': ['upper_flap', 'lower_flap', 'interior (clipped to the lip gap)', 'lower_lip', 'upper_lip'],
        'final_iteration': FINAL + 1, 'final_label': label_, 'config': cfg,
        'calibration': {v: {k: get_calib(v)[k] for k in ['cx', 'hw', 'AA_half', 'AA', 'M', 'smile', 'rest_corners']} for v in VIEWS},
        'pass_marks': {v: S[v]['pass'] for v in VIEWS},
        'summary': S,
        'cells': {v: jsonable(res[v]) for v in VIEWS},
        'iterations': [{'n': int(k), 'label': h['label'], 'summary': {v: {kk: vv for kk, vv in h['summary'][v].items()} for v in h['summary']}}
                       for k, h in sorted(hist.items(), key=lambda kv: int(kv[0]))],
        'derived_parts': {v: {'interior_notch_px_filled_from_AA': view_for(v, cfg).interior_notch_px,
                              'skin_pad_px': {'upper': int(view_for(v, cfg).pad_u.sum()),
                                              'lower': int(view_for(v, cfg).pad_l.sum())}} for v in VIEWS},
    }
    def clean(o):
        if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)): return [clean(v) for v in o]
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, (np.floating,)): return float(o)
        if isinstance(o, np.bool_): return bool(o)
        return o
    json.dump(clean(out), open(f'{HERE}/results.json', 'w'), indent=1)
    for v in VIEWS: print(v, json.dumps(S[v]['pass']), S[v]['iou_sil'], S[v]['iou_opening'])

if __name__ == '__main__':
    main()
