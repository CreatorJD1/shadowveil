import sys
from PIL import Image, ImageDraw
import numpy as np
def cropc(v,x0,y0,x1,y1,s=8,out=None,marks=None):
    a=np.array(Image.open(v+'.png').convert('RGBA')).astype(float)
    rgb=a[...,:3]*a[...,3:]/255+255*(1-a[...,3:]/255)
    L=rgb.mean(2)
    # stretch: skin ~ 125 -> 235, line 30 -> 0
    e=np.clip((L-40)/(128-40),0,1)**1.5*235
    c=np.stack([e,e,e],2)
    c[a[...,3]<10]=[255,255,230]
    c=Image.fromarray(c[y0:y1,x0:x1].astype(np.uint8)).resize(((x1-x0)*s,(y1-y0)*s),Image.NEAREST)
    d=ImageDraw.Draw(c)
    for x in range((x0//5+1)*5,x1,5):
        col=(255,0,0) if x%50==0 else ((0,160,255) if x%10==0 else (190,230,255))
        d.line([((x-x0)*s,0),((x-x0)*s,c.size[1])],fill=col)
        if x%10==0: d.text(((x-x0)*s+2,2),str(x),fill=(255,0,0))
    for y in range((y0//5+1)*5,y1,5):
        col=(255,0,0) if y%50==0 else ((0,160,255) if y%10==0 else (190,230,255))
        d.line([(0,(y-y0)*s),(c.size[0],(y-y0)*s)],fill=col)
        if y%10==0: d.text((2,(y-y0)*s+2),str(y),fill=(255,0,0))
    if marks:
        for (x,y) in marks:
            X,Y=(x-x0+.5)*s,(y-y0+.5)*s; d.ellipse([X-4,Y-4,X+4,Y+4],outline=(255,0,255),width=2)
    c.save(out or f'z_{v}_{x0}_{y0}.png')
if __name__=='__main__':
    a=sys.argv; cropc(a[1],*map(int,a[2:7]))
