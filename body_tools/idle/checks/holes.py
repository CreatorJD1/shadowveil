# measure-only: per-frame NEW enclosed holes vs rest (alpha<128 enclosed by opaque), components with size/bbox/nearest bone
import sys, json, os, math, numpy as np
from PIL import Image
from scipy import ndimage as nd
ID = '/workspace/shadowveil/rig/previews/idle/frames'
def enclosed(op):
    lab, n = nd.label(~op); border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
    keep = np.ones(n + 1, bool); keep[list(border)] = False; keep[0] = False; return keep[lab]
def run(name):
    D = f'{ID}/{name}'; meta = json.load(open(D + '/meta.json'))
    rest = np.array(Image.open(D + '/rest.png'))[..., 3] >= 128; renc = nd.binary_dilation(enclosed(rest), iterations=3)
    out = []
    for i, fn in enumerate(sorted(os.listdir(D + '/frames'))):
        A = np.array(Image.open(f'{D}/frames/{fn}'))[..., 3] >= 128
        h = enclosed(A) & ~renc; lab, n = nd.label(h); comps = []
        fb = meta['frames'][i]['bones']
        for k in range(1, n + 1):
            yy, xx = np.nonzero(lab == k)
            if len(yy) < 2: continue
            cx, cy = xx.mean(), yy.mean()
            nb = min(((b, math.hypot(v[0] - cx, v[1] - cy)) for b, v in fb.items()), key=lambda t: t[1])
            comps.append({'px': int(len(yy)), 'bbox': [int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())], 'c': [round(cx, 1), round(cy, 1)], 'nearBone': nb[0], 'd': round(nb[1], 1)})
        out.append({'f': i, 't': meta['frames'][i]['t'], 'holes_px': int(sum(c['px'] for c in comps)), 'comps': comps})
    json.dump(out, open(f'{name}.holes.json.tmp', 'w')); os.replace(f'{name}.holes.json.tmp', f'{name}.holes.json')
    fr = [r for r in out if r['holes_px'] > 0]
    print(name, 'frames with holes', len(fr), 'max', max([r['holes_px'] for r in out]), 'at', max(out, key=lambda r: r['holes_px'])['f'])
    return out
if __name__ == '__main__':
    for n in sys.argv[1:]: run(n)
