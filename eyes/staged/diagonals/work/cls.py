import sys, numpy as np
from seg import load
def classes(sub, ic):
    s = sub.astype(float); r, g, b = s[..., 0], s[..., 1], s[..., 2]; lum = s.mean(2)
    mx = s.max(2); mn = s.min(2); sat = (mx - mn) / np.maximum(mx, 1)
    scl = (lum > 150) & (sat < 0.36)
    if ic == 'green': iris = (g > r + 8) & (g > 50)
    else: iris = ((sat > 0.5) & (b < 0.42 * r) & (lum > 60) & (r > 110)) | ((lum > 148) & (sat > 0.33) & (b < 0.56 * r))
    return scl, iris, lum, sat
if __name__ == '__main__':
    f, ic = sys.argv[1], sys.argv[2]; x0, y0, x1, y1 = map(int, sys.argv[3:7])
    a = load(f); sub = a[y0:y1, x0:x1]; scl, iris, lum, sat = classes(sub, ic)
    print('     ' + ''.join(str((x0 + i) % 10) for i in range(x1 - x0)))
    for y in range(y1 - y0):
        print('%3d  ' % (y + y0) + ''.join('W' if scl[y, x] else ('I' if iris[y, x] else ('#' if lum[y, x] < 60 else ('+' if lum[y, x] < 100 else '.'))) for x in range(x1 - x0)))
