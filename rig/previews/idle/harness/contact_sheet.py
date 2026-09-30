# contact-sheet PNG: 8 evenly spaced frames per run (rows), on flat mid-grey; labels go in a margin strip, never on her
import sys,os
from PIL import Image,ImageDraw
out=sys.argv[1]; runs=sys.argv[2:]  # each "label=framesdir"
N=8; S=0.2; tw,th=int(1365*S),int(1739*S); lab=150
sheet=Image.new('RGB',(lab+N*tw,len(runs)*(th+22)),(40,40,44)); d=ImageDraw.Draw(sheet)
for r,spec in enumerate(runs):
    name,fd=spec.split('=',1); fs=sorted(os.listdir(fd)); idx=[round(i*(len(fs)-1)/(N-1)) for i in range(N)]
    y=r*(th+22); d.text((8,y+th//2),name,fill=(230,230,230))
    for c,i in enumerate(idx):
        im=Image.open(f'{fd}/{fs[i]}'); g=Image.new('RGBA',im.size,(128,128,128,255)); g.alpha_composite(im)
        sheet.paste(g.convert('RGB').resize((tw,th),Image.LANCZOS),(lab+c*tw,y))
        d.text((lab+c*tw+4,y+th+4),f't={i/30:.2f}s',fill=(200,200,200))
sheet.save(out); print(out,sheet.size)
