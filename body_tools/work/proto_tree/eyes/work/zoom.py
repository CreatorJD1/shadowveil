import sys
from PIL import Image, ImageDraw
src,x0,y0,x1,y1,s,out=sys.argv[1],*map(int,sys.argv[2:7]),sys.argv[7]
im=Image.open(src).convert('RGBA'); bg=Image.new('RGBA',im.size,(255,0,255,255)); bg.alpha_composite(im)
c=bg.crop((x0,y0,x1,y1)).convert('RGB').resize(((x1-x0)*s,(y1-y0)*s),Image.NEAREST)
d=ImageDraw.Draw(c)
for x in range(x0,x1):
    if x%5==0: d.line([((x-x0)*s,0),((x-x0)*s,c.height)],fill=(0,255,255) if x%10==0 else (0,120,120))
for y in range(y0,y1):
    if y%5==0: d.line([(0,(y-y0)*s),(c.width,(y-y0)*s)],fill=(0,255,255) if y%10==0 else (0,120,120))
for x in range(x0,x1):
    if x%10==0: d.text(((x-x0)*s+2,2),str(x),fill=(255,255,0))
for y in range(y0,y1):
    if y%10==0: d.text((2,(y-y0)*s+2),str(y),fill=(255,255,0))
c.save(out)
