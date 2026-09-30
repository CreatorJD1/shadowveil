#!/usr/bin/env python3
"""Outline (line-art) consistency in fixed regions of idle renders: per frame, per region, vs rest.png of the same render
(and vs a baseline render of the same frames if given). Line = luma < 35 (her navy/brown ink; the dark-grey briefs are luma ~47).
Metrics: width = line px / skeleton px (components with >= 8 skeleton px); ends = skeleton endpoints (breaks add 2 each);
comps = line components >= 4 px; kinks = skeleton px where the line direction turns > 60 deg within 3 px (sharp corners/zigzags).
Usage: outline_check.py <render dir> a-b [baseline render dir]"""
import sys, os, json, numpy as np
from PIL import Image
from scipy import ndimage as nd
from skimage.morphology import skeletonize
ROI = {'armpit': (640, 560, 760, 680), 'hip': (650, 700, 750, 870)}
def line(im): a = im.astype(np.float32); return (a[..., 3] > 128) & ((a[..., :3] @ np.array([.299, .587, .114], np.float32)) < 35)
def metrics(m):
    lab, n = nd.label(m, np.ones((3, 3))); sz = nd.sum(np.ones_like(lab), lab, range(1, n + 1)) if n else []
    keep = np.isin(lab, [i + 1 for i in range(n) if sz[i] >= 4]); sk = skeletonize(keep)
    nb = nd.convolve(sk.astype(int), np.ones((3, 3), int), mode='constant') - sk
    ends = int((sk & (nb == 1)).sum())
    sl, sn = nd.label(sk, np.ones((3, 3))); ssz = nd.sum(np.ones_like(sl), sl, range(1, sn + 1)) if sn else []
    big = [i + 1 for i in range(sn) if ssz[i] >= 8]; bm = np.isin(sl, big)
    own = np.isin(nd.label(keep, np.ones((3, 3)))[0], np.unique(nd.label(keep, np.ones((3, 3)))[0][bm]))
    width = float((keep & own).sum() / max(1, bm.sum()))
    # direction along the skeleton: structure tensor of the smoothed line mask
    g = nd.gaussian_filter(keep.astype(np.float32), 1.2); gy, gx = nd.sobel(g, 0), nd.sobel(g, 1)
    Jxx, Jyy, Jxy = [nd.gaussian_filter(v, 1.5) for v in (gx * gx, gy * gy, gx * gy)]; th = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy)
    ys, xs = np.nonzero(bm & (nb == 2)); kinks = 0
    for y, x in zip(ys, xs):
        y0, y1, x0, x1 = max(0, y - 3), y + 4, max(0, x - 3), x + 4; w = bm[y0:y1, x0:x1]
        d = np.abs(np.angle(np.exp(2j * (th[y0:y1, x0:x1][w] - th[y, x])))) / 2
        if d.size and np.degrees(d.max()) > 60: kinks += 1
    return {'width': round(width, 2), 'ends': ends, 'comps': int(sum(1 for s in sz if s >= 4)), 'kinks': kinks, 'px': int(keep.sum())}
def run(D, a, b):
    rest = np.array(Image.open(f'{D}/rest.png')); out = {'rest': {k: metrics(line(rest)[y0:y1, x0:x1]) for k, (x0, y0, x1, y1) in ROI.items()}, 'frames': {}}
    for f in range(a, b + 1):
        p = f'{D}/frames/f{f:04d}.png'
        if not os.path.exists(p) or os.path.getsize(p) < 10: continue
        L = line(np.array(Image.open(p))); out['frames'][f] = {k: metrics(L[y0:y1, x0:x1]) for k, (x0, y0, x1, y1) in ROI.items()}
    return out
if __name__ == '__main__':
    D = sys.argv[1]; a, b = [int(v) for v in sys.argv[2].split('-')]; r = run(D, a, b)
    json.dump(r, open(D.rstrip('/') + '.outline.json', 'w'))
    for k in ROI:
        R = r['rest'][k]; F = [v[k] for v in r['frames'].values()]
        if not F: continue
        dw = max(abs(x['width'] - R['width']) for x in F)
        print(f"{os.path.basename(D)} {k}: rest w{R['width']} ends{R['ends']} comps{R['comps']} kinks{R['kinks']} | frames max|dw| {dw:.2f}, ends max {max(x['ends'] for x in F)}, comps max {max(x['comps'] for x in F)}, kinks max {max(x['kinks'] for x in F)}")
