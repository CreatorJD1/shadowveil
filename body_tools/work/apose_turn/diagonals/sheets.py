import json, numpy as np, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0,'/workspace/shadowveil/body_tools/work/apose_turn'); from seg import mask_of
R='/workspace/shadowveil'; D=R+'/body_tools/work/apose_turn/diagonals'
A=json.load(open(D+'/_analysis.json'))
try: F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15); FB=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',18)
except: F=FB=ImageFont.load_default()
TH=700; TOP=40; CW=330; HDR=40; FOOT=110
def frame_cut(f):
    p=R+'/reference/apose_turn/frames/f%03d.png'%f; im=Image.open(p).convert('RGB'); m=mask_of(p)
    rgb=np.array(im).astype(int); key=(rgb[...,2]-np.maximum(rgb[...,0],rgb[...,1]))>120; a=np.dstack([np.array(im),((m&~key)*255).astype(np.uint8)]); return Image.fromarray(a,'RGBA'), m
def view_cut(v):
    im=Image.open(f'{R}/views/{v}/base.png').convert('RGBA'); m=np.array(im)[...,3]>0; return im,m
def place(im,m,canvas,x0,y0):
    ys,xs=np.nonzero(m); t,b=ys.min(),ys.max(); s=TH/(b-t)
    cx=(xs.min()+xs.max())/2
    sm=im.resize((round(im.width*s),round(im.height*s)),Image.LANCZOS)
    canvas.alpha_composite(sm,(int(x0+CW/2-cx*s),int(y0+TOP-t*s)))
def cell_bg(canvas,x0,y0,h):
    d=ImageDraw.Draw(canvas); d.rectangle([x0+2,y0,x0+CW-3,y0+h],fill=(236,236,240,255))
def footline(canvas,y0,w):
    d=ImageDraw.Draw(canvas); y=y0+TOP+TH; d.line([(0,y),(w,y)],fill=(220,0,0,255),width=2); d.line([(0,y0+TOP),(w,y0+TOP)],fill=(0,120,220,255),width=1)
# ring
ring=[(0,'view','apose'),(45,'frame',None),(90,'view','left'),(135,'frame',None),(180,'view','back'),(225,'frame',None),(270,'view','right'),(315,'frame',None)]
PICK=json.load(open(D+'/picks.json'))
W=CW*8; Hh=HDR+TOP+TH+FOOT; c=Image.new('RGBA',(W,Hh),(255,255,255,255)); d=ImageDraw.Draw(c)
for i,(ang,kind,v) in enumerate(ring):
    x0=i*CW; cell_bg(c,x0,HDR,TOP+TH+30)
    if kind=='view': im,m=view_cut(v); lab=f'{ang}°  views/{v} (sharp)'
    else: f=PICK[str(ang)]; im,m=frame_cut(f); lab=f'{ang}°  f{f:03d} (video)'
    place(im,m,c,x0,HDR); d.text((x0+8,10),lab,fill=(0,0,0),font=FB)
footline(c,HDR,W)
d.text((8,HDR+TOP+TH+40),'All cells scaled to identical head-top (blue) -> sole (red) height. Order = 8-point ring 0..315. Video frames are not mirrored. Diagonal frames per diagonals.json.',fill=(0,0,0),font=F)
c.convert('RGB').save(D+'/diagonals_sheet.png')
# strips
for ang,rows in A['rows'].items():
    n=len(rows); c=Image.new('RGBA',(CW*n,HDR+TOP+TH+FOOT+40),(255,255,255,255)); d=ImageDraw.Draw(c)
    for i,r in enumerate(rows):
        f=r['frame']; x0=i*CW; cell_bg(c,x0,HDR,TOP+TH+30)
        if f==PICK[ang]: ImageDraw.Draw(c).rectangle([x0+2,HDR,x0+CW-3,HDR+TOP+TH+30],outline=(0,170,0,255),width=5)
        im,m=frame_cut(f); place(im,m,c,x0,HDR)
        d.text((x0+8,10),f'f{f:03d}  ~{r["angle_est"]}°'+('  PICK' if f==PICK[ang] else ''),fill=(0,120,0) if f==PICK[ang] else (0,0,0),font=FB)
        h=r['hands']; hi=r['handoff_interp']
        t=(f"H {r['raw_H']}px  sole y {r['raw_sole']}\n"
           f"interp handoff: H {hi['H_view']} sole {hi['sole_view']}\n"
           f"arm° R{r['arm_angle_deg'].get('R')} L{r['arm_angle_deg'].get('L')} (views≈46/44)\n"
           f"hands clear R:{'Y' if h['R']['clear'] else 'N'} L:{'Y' if h['L']['clear'] else 'N'}  aa {r['aa_band']}  lap {r['lap_var_inner']:.0f}")
        d.multiline_text((x0+8,HDR+TOP+TH+34),t,fill=(0,0,0),font=F,spacing=3)
    footline(c,HDR,CW*n)
    c.convert('RGB').save(D+f'/strip_{int(ang):03d}.png')
