#!/usr/bin/env python3
# before (live views/) vs after (scratch copy with staged whites) at EyeBallX -1/0/+1, Y 0, eyes open.
import sys,json,importlib.util
import numpy as np
from PIL import Image,ImageDraw
SCR=sys.argv[1] if len(sys.argv)>1 else '/tmp/wt_scratch/views'
def mod(views):
    s=importlib.util.spec_from_file_location('re'+str(abs(hash(views))),'/workspace/shadowveil/eyes/tools/render_eyes.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); m.VIEWS=views; return m
B=mod('/workspace/shadowveil/views'); A=mod(SCR)
Z=5; rows=[]; stats={}
for v in ['apose','tpose','left','right']:
    rig=json.load(open(f'/workspace/shadowveil/views/{v}/eyes/rig.json')); x0,y0,x1,y1=rig['workRegion']
    y0+=18; y1-=14
    cells=[];st={}
    for lab,M in (('before',B),('after',A)):
        for X in (-1,0,1):
            im=M.render(v,{'EyeBallX':X})
            cells.append((f'{lab} X={X:+d}',im[y0:y1,x0:x1]))
            st[f'{lab}{X:+d}']=im
    for X in (-1,0,1): stats[f'{v} X={X:+d}']=int((st[f'before{X:+d}']!=st[f'after{X:+d}']).any(-1).sum())
    h,w=cells[0][1].shape[:2]; pad=6
    row=Image.new('RGB',(6*(w*Z+pad)+120,h*Z+22),(40,40,40)); d=ImageDraw.Draw(row); d.text((4,h*Z//2),v,fill=(255,255,255))
    for i,(t,c) in enumerate(cells):
        xo=120+i*(w*Z+pad)+(pad*2 if i>=3 else 0)
        row.paste(Image.fromarray(c[...,:3]).resize((w*Z,h*Z),Image.NEAREST),(xo,20)); d.text((xo+2,4),t,fill=(255,255,0) if i>=3 else (200,200,200))
    rows.append(row)
W=max(r.width for r in rows)+12; H=sum(r.height+8 for r in rows)+30
sh=Image.new('RGB',(W,H),(25,25,25)); d=ImageDraw.Draw(sh)
d.text((6,8),'Side-glance white tone (STAGED): before = live, after = eyes/staged/white_tone; EyeBallY 0, eyes open, x5. Rest (X=0) identical.',fill=(255,255,255))
y=30
for r in rows: sh.paste(r,(6,y)); y+=r.height+8
sh.save('/workspace/shadowveil/eyes/staged/white_tone/sheet.png'); print(stats)
json.dump(stats,open('/workspace/shadowveil/eyes/staged/white_tone/sheet_pxdiff.json','w'),indent=1)
