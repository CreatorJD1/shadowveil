# segmentation of the apose/tpose/back bikini bottom + its outline curves from base_body_skin.png (rest)
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
def load(view, root='/workspace/shadowveil'):
    a = np.asarray(Image.open(f'{root}/views/{view}/base_body_skin.png').convert('RGBA')).astype(int)
    return a
def fabric_mask(a, box):
    x0, y0, x1, y1 = box
    r, g, b, al = [a[y0:y1, x0:x1, i] for i in range(4)]
    mx = np.maximum(np.maximum(r, g), b); mn = np.minimum(np.minimum(r, g), b)
    m = (al > 200) & (mx < 95) & (mx - mn < 22)          # charcoal fabric + its dark outline (low saturation)
    lab, n = ndi.label(m); 
    if n == 0: return m
    sz = ndi.sum(m, lab, range(1, n + 1)); k = int(np.argmax(sz)) + 1
    return ndi.binary_fill_holes(lab == k)
