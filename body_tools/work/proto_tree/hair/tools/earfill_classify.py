import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from earfill_lib import *
from earfill_regions import EARBOX
DIRS=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
def rays(v,cand,L=24):
    """per candidate pixel: number of the 8 rays that reach Body's drawn pixels (rest stack alpha>=128) before
    reaching true background (base.png alpha 0 outside the hair erase mask)"""
    mid=unpremul(mid_stack(v)); body=mid[...,3]>=128
    base=np.array(Image.open(f'{R}/views/{v}/base.png').convert('RGBA'))
    em=np.array(Image.open(f'{R}/hair/{v}_hair_erase_mask.png').convert('L'))>127
    bg=(base[...,3]==0)|((mid[...,3]==0)&~em)
    H,W=body.shape; cnt=np.zeros(cand.shape,int)
    for y,x in np.argwhere(cand):
        n=0
        for dx,dy in DIRS:
            for k in range(1,L+1):
                xx,yy=x+dx*k,y+dy*k
                if not(0<=xx<W and 0<=yy<H) or bg[yy,xx]: break
                if body[yy,xx]: n+=1; break
        cnt[y,x]=n
    return cnt
def in_boxes(v,shape):
    m=np.zeros(shape,bool)
    for x0,y0,x1,y1 in EARBOX[v]: m[y0:y1,x0:x1]=True
    return m
