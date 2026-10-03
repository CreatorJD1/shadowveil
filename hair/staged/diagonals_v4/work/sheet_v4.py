# zoom sheet: per angle (045, 315): source | v3 | v4 (view scale, over the source with its key greyed), then frame_scale v4 over the frame; cyan = px added in v4
import sys,glob,json,numpy as np
sys.path.insert(0,'/workspace/shadowveil/hair/staged/diagonals_v3/work')
from common import *
from PIL import ImageDraw
CR={'045':(560,640,180,250),'315':(730,810,180,250)}; Z=6; rows=[]
for ang,(x0,x1,y0,y1) in CR.items():
    sv=src_view(ang).astype(float); bg=sv[...,:3].copy(); kb=(sv[...,2]-np.maximum(sv[...,0],sv[...,1])>60); bg[kb]=[90,90,90]
    def comp(d,b):
        c=b.copy(); m=np.zeros(c.shape[:2],bool)
        for f in sorted(glob.glob(f'{R}/hair/staged/{d}/{ang}/hair/*.png')):
            a=A(f); al=a[...,3:]/255.; c=c*(1-al)+a[...,:3]*al; m|=a[...,3]>0
        return c,m
    c3,m3=comp('diagonals_v3',bg); c4,m4=comp('diagonals_v4',bg); c4h=c4.copy(); c4h[m4&~m3]=[0,255,255]
    t=[sv[...,:3],c3,c4,c4h]
    rows.append(np.concatenate([np.pad(x[y0:y1,x0:x1],((0,1),(0,1),(0,0)),constant_values=255) for x in t],1))
    # frame-scale crop (same region in frame coords), scaled to the same height
    s,dx,dy=fit(ang); fx0,fx1,fy0,fy1=[int(v) for v in ((x0-dx)/s,(x1-dx)/s,(y0-dy)/s,(y1-dy)/s)]
    fr=A(f'{R}/reference/apose_turn/frames/f{FR[ang]:03d}.png')[...,:3].astype(float); fb=fr.copy(); fb[(fr[...,2]-np.maximum(fr[...,0],fr[...,1])>60)]=[90,90,90]
    fc=fb.copy()
    for f in glob.glob(f'{R}/hair/staged/diagonals_v4/{ang}/frame_scale/hair/*.png'):
        a=A(f); al=a[...,3:]/255.; fc=fc*(1-al)+a[...,:3]*al
    hm=np.zeros(fr.shape[:2],bool)
    for f in glob.glob(f'{R}/hair/staged/diagonals_v4/{ang}/frame_scale/hair/*.png'): hm|=A(f)[...,3]>0
    fo=fb.copy(); fo[hm]=[255,160,0]
    row=[np.pad(x[fy0:fy1,fx0:fx1],((0,1),(0,1),(0,0)),constant_values=255) for x in (fr,fc,fo)]
    fr_row=np.concatenate(row,1); fr_row=np.array(Image.fromarray(fr_row.astype(np.uint8)).resize((int(fr_row.shape[1]*rows[-1].shape[0]/fr_row.shape[0]),rows[-1].shape[0]),Image.NEAREST)).astype(float)
    rows.append(fr_row)
w=max(r.shape[1] for r in rows); rows=[np.pad(r,((0,2),(0,w-r.shape[1]),(0,0)),constant_values=255) for r in rows]
im=Image.fromarray(np.concatenate(rows,0).astype(np.uint8)); im=im.resize((im.width*Z,im.height*Z),Image.NEAREST)
c=Image.new('RGB',(im.width,im.height+40),'white'); c.paste(im,(0,40)); d=ImageDraw.Draw(c)
d.text((6,6),'rows: 045 view | 045 frame_scale | 315 view | 315 frame_scale.  view row: source | v3 | v4 | v4 (cyan = added in v4).  frame row: her frame | v4 frame_scale over frame (key grey) | orange = frame_scale hair px',fill='black')
c.save('../eye_crops_v3_v4_source.png'); print(c.size)
