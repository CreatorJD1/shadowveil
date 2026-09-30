# before/after zoom with new-defect overlay (magenta), hand-only composite over grey. cmp_zoom.py out box scale side dirA dirB cases...
import sys,numpy as np
from PIL import Image,ImageDraw
from qalib import *
out,box,sc,S,DA,DB=sys.argv[1],tuple(map(int,sys.argv[2].split(','))),int(sys.argv[3]),sys.argv[4],sys.argv[5],sys.argv[6];cases=sys.argv[7:]
x0,y0,x1,y1=box;w,h=(x1-x0)*sc,(y1-y0)*sc
sh=Image.new('RGB',(len(cases)*w,2*(h+14)),(30,30,30));d=ImageDraw.Draw(sh)
for rI,D in enumerate([DA,DB]):
    r=Run(D)
    for cI,cn in enumerate(cases):
        A=r.comp(cn,S);g=Image.new('RGBA',(x1-x0,y1-y0),(128,128,128,255));g.alpha_composite(Image.fromarray(A).crop(box));a=np.array(g)
        if cn!='rest':
            e,t,s=r.defects(cn,S);m=(e|t|s)[y0:y1,x0:x1];a[m]=[255,0,255,255]
        sh.paste(Image.fromarray(a).convert('RGB').resize((w,h),Image.NEAREST),(cI*w,rI*(h+14)+14));d.text((cI*w+3,rI*(h+14)+1),f'{D.split("renders/")[-1]} {cn} {S}',fill=(230,230,230))
sh.save(out);print(out)
