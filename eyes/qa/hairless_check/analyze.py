# Eyes on hairless base: diff hairless vs live inside dilated eye+brow lock, per view and pose; contact sheet.
import json,os
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
ROOT='/workspace/shadowveil'
POSES=['rest','posed_default','blink0.5','blink0','gx+1','gx-1','gy+1','gy-1','gx+1y+1','gx+1y-1','gx-1y+1','gx-1y-1','closed_gx+1','closed_gx-1']
DIL=6
def A(p): return np.array(Image.open(p).convert('RGBA'))
def diffmask(a,b):
    d=(a!=b).any(-1); both0=(a[...,3]==0)&(b[...,3]==0); return d&~both0
yy,xx=np.mgrid[-DIL:DIL+1,-DIL:DIL+1]; DISK=(xx*xx+yy*yy)<=DIL*DIL
rep={'method':{'urls':'http://127.0.0.1:8765/rig/?view=<view>&quality=linear[&hairless=1]','renderer':'headless Chrome (puppeteer-core), rig render(g,rest) like rig/work/hairless/hl_render.js; rest = render(g,true); other poses = render(g,false) with params set',
 'region':f'eyes/handoff_hairless/<view>_eye_brow_lock.png dilated by {DIL} px (disk)','diff':'any RGBA channel differs (px transparent in both ignored)','base':'base.png compared after the same canvas round-trip as the renders (renders/<view>_base_canvas.png, drawn from the rig R.im.base); raw-PNG counts also given'},'views':{}}
crops=[]
for v in ['apose','tpose','left','right']:
    lock=np.array(Image.open(f'{ROOT}/eyes/handoff_hairless/{v}_eye_brow_lock.png'))>0
    reg=ndimage.binary_dilation(lock,structure=DISK)
    ys,xs=np.where(reg); bb=[int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1]
    base=A(f'{ROOT}/views/{v}/base.png'); basec=A(f'renders/{v}_base_canvas.png')
    V={'lockPx':int(lock.sum()),'regionPx':int(reg.sum()),'regionBBox_xyxy':bb,'poses':{}}
    for p in POSES:
        L=A(f'renders/{v}_live_{p}.png'); Hh=A(f'renders/{v}_hairless_{p}.png')
        dm=diffmask(Hh,L); din=dm&reg
        e={'diffInRegion':int(din.sum()),'diffInLock':int((dm&lock).sum()),'diffWholeFrame':int(dm.sum())}
        if din.any():
            y,x=np.where(din); e['diffBBox_xyxy']=[int(x.min()),int(y.min()),int(x.max())+1,int(y.max())+1]
            e['samples']=[{'x':int(a),'y':int(b),'hairless':Hh[b,a].tolist(),'live':L[b,a].tolist(),'base':base[b,a].tolist()} for b,a in list(zip(y,x))[:20]]
        if p in('rest','posed_default'):
            for tag,img in (('hairless',Hh),('live',L)):
                bm=diffmask(img,basec); e[f'{tag}_vs_base_inRegion']=int((bm&reg).sum()); e[f'{tag}_vs_base_wholeFrame']=int(bm.sum())
                rm=diffmask(img,base); e[f'{tag}_vs_rawBasePNG_inRegion']=int((rm&reg).sum()); e[f'{tag}_vs_rawBasePNG_wholeFrame']=int(rm.sum())
                if (rm&reg).any(): ad=np.abs(img.astype(int)-base.astype(int))[rm&reg]; e[f'{tag}_vs_rawBasePNG_note']=f'only semi-transparent px (alpha {int(base[rm&reg][:,3].min())}-{int(base[rm&reg][:,3].max())}), alpha equal, max RGB delta {int(ad[:,:3].max())}: canvas premultiplied-alpha rounding, not a content difference' if (ad[:,3].max()==0 and base[rm&reg][:,3].max()<255) else 'content difference'
        V['poses'][p]=e
        crops.append((v,p,L,Hh,din,bb))
    rep['views'][v]=V
# back: no face; just record whole-frame rest diffs
L=A('renders/back_live_rest.png');Hh=A('renders/back_hairless_rest.png');b=A('renders/back_base_canvas.png')
rep['views']['back']={'note':'no face (eyes not drawn); no eye lock; rest only','rest':{'diffWholeFrame_hairless_vs_live':int(diffmask(Hh,L).sum()),'hairless_vs_base_wholeFrame':int(diffmask(Hh,b).sum()),'live_vs_base_wholeFrame':int(diffmask(L,b).sum())}}
tot=sum(e['diffInRegion'] for vv in ['apose','tpose','left','right'] for e in rep['views'][vv]['poses'].values())
restok=all(rep['views'][vv]['poses']['rest']['hairless_vs_base_inRegion']==0 for vv in ['apose','tpose','left','right'])
rep['summary']={'totalDiffInRegion':tot,'allZero':tot==0,'restHairlessMatchesBaseInRegion':restok}
json.dump(rep,open('report.json','w'),indent=1)
# contact sheet: per view row-block; per pose column pair live|hairless (zoom), diff in magenta overlay on hairless
Z=3; rows=[]
from PIL import ImageFont
for v in ['apose','tpose','left','right']:
    cs=[c for c in crops if c[0]==v]; bb=cs[0][5]; pad=4; x0,y0,x1,y1=bb[0]-pad,bb[1]-pad,bb[2]+pad,bb[3]+pad
    cw,ch=(x1-x0)*Z,(y1-y0)*Z
    # region outline from first
    lock=np.array(Image.open(f'{ROOT}/eyes/handoff_hairless/{v}_eye_brow_lock.png'))>0; reg=ndimage.binary_dilation(lock,structure=DISK)
    edge=reg&~ndimage.binary_erosion(reg)
    tiles=[]
    for (_,p,L,Hh,din,_) in cs:
        pair=[]
        for nm,img in (('live',L),('hairless',Hh)):
            c=img[y0:y1,x0:x1].copy(); bg=np.full(c.shape[:2]+(3,),255,np.uint8)
            al=c[...,3:4]/255.; rgb=(c[...,:3]*al+bg*(1-al)).astype(np.uint8)
            e=edge[y0:y1,x0:x1]; rgb[e]=(0,170,255)
            if nm=='hairless': rgb[din[y0:y1,x0:x1]]=(255,0,255)
            pair.append(Image.fromarray(rgb).resize((cw,ch),Image.NEAREST))
        t=Image.new('RGB',(cw*2+6,ch+16),'white'); t.paste(pair[0],(0,16)); t.paste(pair[1],(cw+6,16))
        ImageDraw.Draw(t).text((2,2),f'{p}  live | hairless   diff={int(din.sum())}',fill=(0,0,0) if din.sum()==0 else (220,0,0))
        tiles.append(t)
    ncol=2; tw,th=tiles[0].size; blk=Image.new('RGB',(ncol*(tw+10),20+((len(tiles)+ncol-1)//ncol)*(th+8)),'white')
    ImageDraw.Draw(blk).text((4,4),f'{v}: eye+brow region (lock dilated {DIL}px, blue outline), x{Z}; magenta = hairless!=live',fill=(0,0,0))
    for i,t in enumerate(tiles): blk.paste(t,((i%ncol)*(tw+10),20+(i//ncol)*(th+8)))
    rows.append(blk)
W=max(r.width for r in rows); S=Image.new('RGB',(W,sum(r.height for r in rows)+40),'white')
d=ImageDraw.Draw(S); d.text((4,4),f'Eyes on hairless base (?hairless=1) vs live, quality=linear. Total diff px in region: {tot}. Rest hairless == base.png in region: {restok}',fill=(0,0,0))
y=40
for r in rows: S.paste(r,(0,y)); y+=r.height
S.save('sheet.png'); print(S.size)
for v in ['apose','tpose','left','right']:
    print(v,{p:e['diffInRegion'] for p,e in rep['views'][v]['poses'].items()}, 'rest hl/live vs base in region:',rep['views'][v]['poses']['rest']['hairless_vs_base_inRegion'],rep['views'][v]['poses']['rest']['live_vs_base_inRegion'],'whole:',{p:e['diffWholeFrame'] for p,e in rep['views'][v]['poses'].items()}['rest'])
print(rep['views']['back']); print(rep['summary'])
