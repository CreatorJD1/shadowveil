import sys,numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
v,dx,dy,x0,y0,x1,y1,s=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),*map(int,sys.argv[4:9])
D='/workspace/tmpsv/hg'; T='/workspace/shadowveil/body_tools/work/hairless_division_staged'
r=np.load(f'{D}/{v}_r.npy').astype(float)
def enc(a): op=a[...,3]>=254.5; return ndimage.binary_fill_holes(op)&~op
er=enc(r); panels=[]
for lab,f,nn in [('rest',None,None),(f'BEFORE head ({dx:+d},{dy:+d})','pieces_pre_headgroup',None),(f'AFTER head ({dx:+d},{dy:+d})','pieces',None)]:
    a=r if f is None else np.load(f'{D}/{v}_{f}_m.npy').astype(float)
    c=a[y0:y1,x0:x1]; al=c[...,3:]/255; bg=np.zeros_like(c[...,:3]); bg[:]=[150,230,150]; rgb=c[...,:3]*al+bg*(1-al)
    if f:
        ne=np.load(f'{D}/{v}_{f}_newneck.npy')[y0:y1,x0:x1]; rgb[ne]=rgb[ne]*0.5+np.array([0,255,255])*0.5
        e=(enc(a)&~er)[y0:y1,x0:x1]&(c[...,3]<233); rgb[e]=[255,0,0]
    im=Image.fromarray(rgb.astype(np.uint8)).resize(((x1-x0)*s,(y1-y0)*s),Image.NEAREST); d=ImageDraw.Draw(im); d.rectangle([0,0,im.width,14],fill=(255,255,255)); d.text((3,2),f'{v} {lab}',fill=(0,0,0)); panels.append(im)
W=sum(p.width for p in panels)+20; c=Image.new('RGB',(W,panels[0].height+16),'white'); x=0
for p in panels: c.paste(p,(x,0)); x+=p.width+10
ImageDraw.Draw(c).text((3,panels[0].height+2),'cyan tint = neck px newly visible at the handoff offset; red = new enclosed px below her alpha floor (none); body pieces only (hair/face move with the head)',fill=(0,0,0))
c.save(f'{T}/{v}/sheet_headgroup_neck_before_after.png')
