import sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np
def crop(v,x0,y0,x1,y1,s=4,out=None,grid=10,overlay=None):
    im=Image.open(v+'.png').convert('RGBA')
    bg=Image.new('RGBA',im.size,(255,255,255,255)); bg.alpha_composite(im)
    if overlay is not None: bg.alpha_composite(overlay)
    c=bg.crop((x0,y0,x1,y1)).resize(((x1-x0)*s,(y1-y0)*s),Image.NEAREST).convert('RGB')
    d=ImageDraw.Draw(c)
    for x in range((x0//grid+1)*grid,x1,grid):
        col=(255,0,0) if x%50==0 else (0,200,255)
        d.line([((x-x0)*s,0),((x-x0)*s,c.size[1])],fill=col,width=1)
        if x%50==0: d.text(((x-x0)*s+2,2),str(x),fill=(255,0,0))
    for y in range((y0//grid+1)*grid,y1,grid):
        col=(255,0,0) if y%50==0 else (0,200,255)
        d.line([(0,(y-y0)*s),(c.size[0],(y-y0)*s)],fill=col,width=1)
        if y%50==0: d.text((2,(y-y0)*s+2),str(y),fill=(255,0,0))
    c.save(out or f'c_{v}_{x0}_{y0}.png')
if __name__=='__main__':
    a=sys.argv; crop(a[1],*map(int,a[2:6]),s=int(a[6]) if len(a)>6 else 4)
