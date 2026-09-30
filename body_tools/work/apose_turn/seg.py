import numpy as np
from PIL import Image
from scipy import ndimage as nd
def mask_of(path):
    a=np.array(Image.open(path).convert('RGB')).astype(int)
    blue=(a[...,2]-np.maximum(a[...,0],a[...,1]))>120
    m=~blue
    lab,n=nd.label(m);
    if n==0: return m
    sz=nd.sum(m,lab,range(1,n+1));keep=np.isin(lab,1+np.nonzero(sz>=200)[0])
    return nd.binary_fill_holes(keep)|keep
