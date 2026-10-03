import sys, numpy as np, colorsys
from PIL import Image
f, x0, y0, x1, y1 = sys.argv[1], *map(int, sys.argv[2:6])
a = np.array(Image.open(f'/workspace/shadowveil/reference/apose_turn/frames/{f}.png').convert('RGB')).astype(int)
for y in range(y0, y1):
    s = ''
    for x in range(x0, x1):
        r, g, b = a[y, x]; h, sat, val = colorsys.rgb_to_hsv(r/255, g/255, b/255); lum = (r+g+b)/3
        if b > 150 and r < 80: ch = '~'
        elif lum > 165 and sat < 0.3: ch = 'W'
        elif sat > 0.3 and 0.2 < h < 0.5 and lum > 45: ch = 'G'
        elif lum < 55: ch = '#'
        elif lum < 95: ch = '+'
        elif sat > 0.45 and 0.06 < h < 0.15 and lum > 100 and r > 170: ch = 'A'
        else: ch = '.'
        s += ch
    print('%3d ' % y + s)
