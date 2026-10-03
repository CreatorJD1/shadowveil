"""Measure source shapes (shape guides only; no source pixel is ever painted). Writes src.json + look/src_*.png overlays."""
import json, numpy as np, sys
sys.path.insert(0,'.')
from fitlib import *
from PIL import ImageDraw
SHEET=f'{ROOT}/reference/test_sheet_expressions.jpg'
CR=f'{ROOT}/reference/grok_build/public/clean-room/sheets'
# face: file, user box, per side (her R = image-left, her L = image-right): eye box, brow box (source px, x0,y0,x1,y1)
FACES={
 'neutral':dict(file=SHEET,box=[164,165,344,265],R=dict(eye=[168,218,236,250],brow=[176,198,242,224]),L=dict(eye=[262,218,334,250],brow=[256,198,328,224])),
 'happy':dict(file=SHEET,box=[1012,165,1192,265],R=dict(eye=[1026,212,1092,242],brow=[1030,190,1098,216],closed=True),L=dict(eye=[1108,212,1178,244],brow=[1106,190,1172,216],closed=True)),
 'anger':dict(file=SHEET,box=[1441,165,1621,265],R=dict(eye=[1455,229,1530,258],brow=[1462,205,1530,238]),L=dict(eye=[1552,229,1612,258],brow=[1546,205,1612,238])),
 'wide':dict(file=SHEET,box=[1012,635,1192,735],R=dict(eye=[1022,672,1090,712],brow=[1028,648,1094,674]),L=dict(eye=[1106,680,1180,718],brow=[1110,654,1180,684])),
 'emo2_sad':dict(file=f'{CR}/emo-2.jpg',box=[115,208,335,313],R=dict(eye=[140,264,218,300],brow=[146,236,224,264]),L=dict(eye=[244,264,324,300],brow=[244,236,316,264])),
 'react_sad':dict(file=f'{CR}/reactions.jpg',box=[415,151,635,256],R=dict(eye=[462,205,532,236],brow=[468,186,538,206]),L=dict(eye=[552,205,622,236],brow=[552,186,616,206])),
 'emo2_flat':dict(file=f'{CR}/emo-2.jpg',box=[1023,208,1243,313],R=dict(eye=[1040,266,1112,300],brow=[1050,240,1118,266]),L=dict(eye=[1138,266,1216,300],brow=[1124,238,1214,266])),
}
def opening(rgb):
    r,g,b=rgb[...,0],rgb[...,1],rgb[...,2]; Lc=lum(rgb); mx=rgb.max(-1); mn=rgb.min(-1)
    scl=(Lc>165)&((mx-mn)<80)
    amber=(r>170)&((r-b)>120)&(Lc>120)&(g>110)
    green=(g>r+15)&(g>90)
    m=scl|amber|green
    m=ndi.binary_closing(m,np.ones((3,3)),iterations=2)
    m=ndi.binary_fill_holes(m)
    lab,n=ndi.label(m); 
    if n==0: return m
    sz=ndi.sum(m,lab,range(1,n+1)); m=lab==(np.argmax(sz)+1)
    return ndi.binary_fill_holes(m)
res={}
for name,F in FACES.items():
    img=load_rgb(F['file']); res[name]={'file':F['file'].replace(ROOT+'/',''),'box':F['box']}
    fx0,fy0,fx1,fy1=F['box']; Z=4
    vis=Image.fromarray(img[fy0:fy1,fx0:fx1].astype(np.uint8)).resize(((fx1-fx0)*Z,(fy1-fy0)*Z),Image.NEAREST); d=ImageDraw.Draw(vis)
    P=lambda x,y:((x-fx0)*Z,(y-fy0)*Z)
    for side in ['R','L']:
        S=F[side]; R={}
        x0,y0,x1,y1=S['brow']; c=img[y0:y1,x0:x1]; prof,comp=ink_profile(lum(c),x0,y0,thr=80)
        # inner end = toward the nose: her R brow inner end is its right end (max x); her L inner end is its left end
        prof=prof[np.argsort(prof[:,0])]
        R['brow']=prof[:,:3].round(2).tolist()
        for x,yc,w,_,_ in prof: d.point([P(x,yc)],fill=(255,0,255))
        x0,y0,x1,y1=S['eye']; c=img[y0:y1,x0:x1]
        if S.get('closed'):
            pr,comp=ink_profile(lum(c),x0,y0,thr=80)
            pr=pr[np.argsort(pr[:,0])]; R['closed']=pr[:,:3].round(2).tolist()
            for x,yc,w,_,_ in pr: d.point([P(x,yc)],fill=(0,255,255))
        else:
            m=opening(c); ys,xs=np.nonzero(m)
            top=[];bot=[]
            for x in np.unique(xs):
                rr=ys[xs==x]; top.append((x+x0+0.5,rr.min()+y0)); bot.append((x+x0+0.5,rr.max()+1+y0))
            R['top']=top; R['bot']=bot
            xl,xr=xs.min(),xs.max()
            pl=(xl+x0+0.0, ys[xs==xl].mean()+y0+0.5); pr_=(xr+x0+1.0, ys[xs==xr].mean()+y0+0.5)
            R['outer'],R['inner']=(pl,pr_) if side=='R' else (pr_,pl)
            for x,y in top: d.point([P(x,y)],fill=(0,255,0))
            for x,y in bot: d.point([P(x,y)],fill=(255,255,0))
            for p in (pl,pr_): d.ellipse([P(*p)[0]-4,P(*p)[1]-4,P(*p)[0]+4,P(*p)[1]+4],outline=(255,0,0))
            # iris: amber/green px
            r,g,b=c[...,0],c[...,1],c[...,2]
            iris=((r>170)&((r-b)>120)&(g>110))|((g>r+15)&(g>90))
            iris=ndi.binary_closing(iris,iterations=2)&m
            iy,ix=np.nonzero(iris)
            if len(ix): R['iris_bbox']=[int(ix.min()+x0),int(iy.min()+y0),int(ix.max()+x0),int(iy.max()+y0)]
        res[name][side]=R
    vis.save(f'look/src_{name}.png')
json.dump(res,open('src_raw.json','w'),indent=0,default=float)
for n in res:
    for s in 'RL':
        R=res[n][s]; print(n,s,'corners',R.get('outer'),R.get('inner'),'iris',R.get('iris_bbox'),'brow x',R['brow'][0][0],R['brow'][-1][0])
