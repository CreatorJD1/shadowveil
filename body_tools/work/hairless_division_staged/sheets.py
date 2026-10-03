import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
ROOT='/workspace/shadowveil'; V=(sys.argv[1:] or ['apose'])[0]; OUT=f'{ROOT}/body_tools/work/hairless_division_staged/{V}'
pj=json.load(open(f'{OUT}/parts.json')); order=pj['layerOrder_backToFront']; pc={p['id']:p for p in pj['pieces']}
img={k:np.array(Image.open(f'{OUT}/pieces/{k}.png')).astype(float) for k in order}
h=np.array(Image.open(f'{OUT}/hairless_{V}.png')).astype(float); b=np.array(Image.open(f'{ROOT}/views/{V}/base.png')).astype(float)
Hh,W=h.shape[:2]; yy,xx=np.mgrid[0:Hh,0:W]
def over(dst,src):
    sa=src[...,3:]/255.; da=dst[...,3:]/255.; oa=sa+da*(1-sa)
    rgb=np.where(oa>0,(src[...,:3]*sa+dst[...,:3]*da*(1-sa))/np.maximum(oa,1e-9),0); return np.concatenate([rgb,oa*255],-1)
def flat(x,bg=(235,235,235)):
    a=x[...,3:]/255.; return (x[...,:3]*a+np.array(bg)*(1-a)).astype(np.uint8)
def rot_img(im,c,th):   # nearest-neighbour inverse map, + = clockwise on screen
    t=np.radians(-th); dx,dy=xx-c[0],yy-c[1]
    sx=np.round(c[0]+np.cos(t)*dx-np.sin(t)*dy).astype(int); sy=np.round(c[1]+np.sin(t)*dx+np.cos(t)*dy).astype(int)
    ok=(sx>=0)&(sx<W)&(sy>=0)&(sy<Hh); o=np.zeros_like(im); o[ok]=im[sy[ok],sx[ok]]; return o
def rot_pt(p,c,th):
    t=np.radians(th); dx,dy=p[0]-c[0],p[1]-c[1]; return [c[0]+np.cos(t)*dx-np.sin(t)*dy, c[1]+np.sin(t)*dx+np.cos(t)*dy]
kids={}
for p in pj['pieces']: kids.setdefault(p['parent'],[]).append(p['id'])
def subtree(k): s=[k]; [s.extend(subtree(c)) for c in kids.get(k,[])]; return s
def composite(imgs):
    c=np.zeros((Hh,W,4))
    for k in order: c=over(c,imgs[k])
    return c
# ---- 1. hairless vs original ----
y0,y1,x0,x1=20,420,500,860
def crop(x): return flat(x)[y0:y1,x0:x1]
mask=np.array(Image.open(f'{OUT}/hair_mask_used.png'))>0
mv=flat(b).astype(float); mv[mask]=mv[mask]*0.4+np.array([255,0,180])*0.6
row=np.concatenate([crop(b),crop(h),mv.astype(np.uint8)[y0:y1,x0:x1]],1)
full=np.concatenate([flat(b),flat(h)],1)
s1=Image.fromarray(row).resize((row.shape[1]*2,row.shape[0]*2),Image.NEAREST)
f1=Image.fromarray(full).resize((full.shape[1]*800//full.shape[0]*0+ (full.shape[1]*800)//full.shape[0],800))
sheet=Image.new('RGB',(max(s1.width,f1.width),s1.height+f1.height+30),(255,255,255)); sheet.paste(s1,(0,30)); sheet.paste(f1,(0,s1.height+30))
ImageDraw.Draw(sheet).text((5,5),'original | hairless | hair mask used (magenta)   -   head crop x2; full view below',fill=(0,0,0))
sheet.save(f'{OUT}/sheet_hairless_vs_original.png')
# ---- 2. exploded parts sheet ----
cols=5; tiles=[]
for k in order:
    a=img[k][...,3]>0; ys,xs=np.nonzero(a); t=img[k][ys.min():ys.max()+1,xs.min():xs.max()+1]
    fl=flat(t,(200,230,255)); tiles.append((k,fl))
tw=260; th=300; sh=Image.new('RGB',(cols*tw,((len(tiles)+cols-1)//cols)*th),(255,255,255)); d=ImageDraw.Draw(sh)
for i,(k,t) in enumerate(tiles):
    im=Image.fromarray(t); sc=min((tw-10)/im.width,(th-30)/im.height,2.0); im=im.resize((max(1,int(im.width*sc)),max(1,int(im.height*sc))),Image.NEAREST)
    X=(i%cols)*tw; Y=(i//cols)*th; sh.paste(im,(X+5,Y+25)); d.text((X+5,Y+5),f"{k}  L{pc[k]['layer']}  flap {pc[k]['flapPx']}px",fill=(0,0,0))
sh.save(f'{OUT}/sheet_parts_exploded.png')
# exploded in place (pieces pushed out from centre) + flap highlight
cx0,cy0=681,{'apose':700,'tpose':690}.get(V,700); PADX=500; ex=np.zeros((Hh+2*PADX,W+2*PADX,4))
for k in order:
    a=img[k][...,3]>0; ys,xs=np.nonzero(a); mx,my=xs.mean(),ys.mean()
    ox=int((mx-cx0)*0.45)+PADX; oy=int((my-cy0)*0.30)+PADX
    t=img[k]
    sub=ex[oy:oy+Hh,ox:ox+W]; ex[oy:oy+Hh,ox:ox+W]=over(sub,t)
Image.fromarray(flat(ex)).resize(((W+2*PADX)//2,(Hh+2*PADX)//2)).save(f'{OUT}/sheet_parts_exploded_inplace.png')
# ---- 3. rest recomposite diff ----
rc=composite(img); rc=np.round(rc); hand=np.array(Image.open(f'{OUT}/hand_mask.png'))>0
ref=h.copy(); ref[hand]=0; rc[rc[...,3]==0]=0
diff=(rc.astype(int)!=ref.astype(int)).any(-1)
dv=flat(rc).astype(float)*0.35+255*0.65; dv[diff]=[255,0,0]; dv[hand]=[120,160,255]
dimg=Image.fromarray(dv.astype(np.uint8)); ImageDraw.Draw(dimg).text((10,10),f'rest recomposite vs hairless: {int(diff.sum())} px differ (red); blue = hand mask (Base Hands layer)',fill=(0,0,0))
dimg.save(f'{OUT}/rest_recomposite_diff.png')
