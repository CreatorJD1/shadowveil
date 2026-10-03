import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
def load(f): return np.array(Image.open(f'/workspace/shadowveil/reference/apose_turn/frames/{f}.png').convert('RGB')).astype(int)
def opening(a, bb, seed, th):
    x0, y0, x1, y1 = bb; sub = a[y0:y1, x0:x1]; lum = sub.mean(2)
    cand = lum >= th
    lab, _ = ndi.label(cand, structure=[[0,1,0],[1,1,1],[0,1,0]])
    l = lab[seed[1]-y0, seed[0]-x0]; assert l > 0
    m = lab == l
    return m, lum
if __name__ == '__main__':
    f = sys.argv[1]; bb = tuple(map(int, sys.argv[2:6])); seed = tuple(map(int, sys.argv[6:8])); th = float(sys.argv[8])
    a = load(f); m, lum = opening(a, bb, seed, th)
    print('size', m.sum())
    x0, y0, x1, y1 = bb
    for y in range(y1 - y0):
        print('%3d ' % (y + y0) + ''.join(('O' if m[y, x] else ('#' if lum[y, x] < 60 else ('+' if lum[y, x] < th else '.'))) for x in range(x1 - x0)))
