import sys, numpy as np
from PIL import Image, ImageDraw
# sheet.py out.png  rows: label|dir|frame|box ; cols tags
out=sys.argv[1]; tags=sys.argv[2].split(','); rows=[r.split('|') for r in sys.argv[3:]]
S=320; pad=24
W=len(tags)*(S+8)+8; H=len(rows)*(S+pad+8)+8
sh=Image.new('RGB',(W,H),(255,255,255)); dr=ImageDraw.Draw(sh)
for i,(lab,clip,f,box) in enumerate(rows):
    box=tuple(int(v) for v in box.split(','))
    for k,t in enumerate(tags):
        p=f'render/{t}_{clip}/frames/f{int(f):04d}.png' if f!='rest' else f'render/{t}_{clip}/rest.png'
        im=Image.open(p).convert('RGBA').crop(box); bg=Image.new('RGBA',im.size,(0,170,255,255)); bg.alpha_composite(im)
        bg=bg.resize((S,int(S*im.size[1]/im.size[0])),Image.NEAREST).crop((0,0,S,S))
        x=8+k*(S+8); y=8+i*(S+pad+8); sh.paste(bg.convert('RGB'),(x,y+pad)); dr.text((x,y+4),f'{t} {clip} f{f} {lab}',fill=(0,0,0))
sh.save(out); print(out)
