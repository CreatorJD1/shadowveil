import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
from seg import load
def interior(a, bb, seed, dth=80, it=2):
    x0, y0, x1, y1 = bb; sub = a[y0:y1, x0:x1]; lum = sub.mean(2)
    dark = lum < dth
    cl = ndi.binary_closing(np.pad(dark, it + 1), iterations=it)[it + 1:-it - 1, it + 1:-it - 1] | dark
    filled = ndi.binary_fill_holes(cl)
    inn = filled & ~dark
    lab, _ = ndi.label(filled & (lum >= dth - 20) | (filled & ~cl), structure=np.ones((3, 3)))
    return inn, lum, dark
if __name__ == '__main__':
    f = sys.argv[1]; bb = tuple(map(int, sys.argv[2:6])); dth = float(sys.argv[6]); it = int(sys.argv[7])
    a = load(f); inn, lum, dark = interior(a, bb, None, dth, it)
    x0, y0, x1, y1 = bb
    for y in range(y1 - y0):
        print('%3d ' % (y + y0) + ''.join(('#' if dark[y, x] else ('O' if inn[y, x] else '.')) for x in range(x1 - x0)))
