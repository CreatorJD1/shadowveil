#!/usr/bin/env python3
"""Labelled grid zoom of a source box (for reading landmarks). Usage: gridcrop.py file x0 y0 x1 y1 zoom out"""
import sys
from PIL import Image, ImageDraw
f,x0,y0,x1,y1,z,out=sys.argv[1],*map(int,sys.argv[2:7]),sys.argv[7]
im=Image.open(f).convert('RGB').crop((x0,y0,x1,y1))
im=im.resize(((x1-x0)*z,(y1-y0)*z),Image.NEAREST)
M=30; c=Image.new('RGB',(im.width+M,im.height+M),'white'); c.paste(im,(M,M)); d=ImageDraw.Draw(c)
for x in range(x0,x1+1):
    if x%10==0:
        X=M+(x-x0)*z; d.line([(X,M),(X,c.height)],fill=(0,255,255) if x%50 else (255,0,255)); d.text((X-8,2 if (x//10)%2 else 14),str(x),fill='black')
for y in range(y0,y1+1):
    if y%10==0:
        Y=M+(y-y0)*z; d.line([(M,Y),(c.width,Y)],fill=(0,255,255) if y%50 else (255,0,255)); d.text((0,Y-5),str(y),fill='black')
c.save(out)
