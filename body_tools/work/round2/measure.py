#!/usr/bin/env python3
"""measure-only: new enclosed holes vs rest per frame, split into armpit box, hip box, elsewhere (y>=320, not hair)."""
import sys, os, json, re, numpy as np
from PIL import Image
from scipy import ndimage as nd
ARM=(670,580,730,670); HIP=(680,700,720,870)
def enclosed(op):
    lab, n = nd.label(~op); border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
    keep = np.ones(n + 1, bool); keep[list(border)] = False; keep[0] = False; return keep[lab]
def inbox(b, x, y): return b[0] <= x <= b[2] and b[1] <= y <= b[3]
def run(D):
    rest = np.array(Image.open(D + '/rest.png'))[..., 3] >= 128; renc = nd.binary_dilation(enclosed(rest), iterations=3)
    out = {}
    for fn in sorted(os.listdir(D + '/frames')):
        f = int(re.findall(r'\d+', fn)[0]); A = np.array(Image.open(f'{D}/frames/{fn}'))[..., 3] >= 128
        h = enclosed(A) & ~renc; lab, n = nd.label(h); r = {'arm': 0, 'hip': 0, 'hipComps': 0, 'else': 0, 'hair': 0, 'elseBoxes': []}
        for k in range(1, n + 1):
            yy, xx = np.nonzero(lab == k); cx, cy = xx.mean(), yy.mean()
            if inbox(ARM, cx, cy): r['arm'] += len(yy)
            elif inbox(HIP, cx, cy): r['hip'] += len(yy); r['hipComps'] += 1
            elif cy < 320: r['hair'] += len(yy)
            else: r['else'] += len(yy); r['elseBoxes'].append([int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max()), len(yy)])
        out[f] = r
    return out
if __name__ == '__main__':
    D = sys.argv[1]; o = run(D); json.dump(o, open(D.rstrip('/') + '.holes.json', 'w'))
    def rng(a, b, k): return sum(o[f][k] for f in o if a <= f <= b)
    pk = lambda k: max(((o[f][k], f) for f in o), default=(0, None))
    print(os.path.basename(D), 'arm peak', pk('arm'), 'arm f160-176', rng(160, 176, 'arm'), '| hip peak', pk('hip'), 'hip f173-190', rng(173, 190, 'hip'), 'hip all', rng(0, 999, 'hip'), 'maxcomps', max(v['hipComps'] for v in o.values()), '| else peak', pk('else'))
    nz = {f: (v['arm'], v['hip'], v['else']) for f, v in o.items() if v['arm'] or v['hip'] or v['else']}; print(' per-frame (arm,hip,else):', nz)
