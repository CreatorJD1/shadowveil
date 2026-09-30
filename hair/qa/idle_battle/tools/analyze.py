# Per-frame hair QA of one per-view idle video (streamed ROI crop, one frame in memory at a time).
import sys, json, csv
from common import *
name, vid, view = sys.argv[1], sys.argv[2], sys.argv[3]
meta=json.load(open(f'{IDLE}/frames/{name}/meta.json')); F=meta['frames']; del meta
s=View(view); w,h=s.w,s.h
D2=disk(2); D1=disk(1)
restM=s.hair_M(None,rest=True)
front=[k for k in s.by if s.layers[k]>=600]      # hair drawn above the face parts
def hair_alpha(Ms,keys):
    a=np.zeros((h,w),np.float32)
    for k in keys: a=np.maximum(a,warp(s.pa[k],s.roi_M(Ms[k]),w,h))
    return a
rest_front=hair_alpha(restM,front)
# bun geometry
ys,xs=np.nonzero(s.pa['bun']>0.5); bun_c0=np.array([xs.mean()+s.x0,ys.mean()+s.y0])
bb=(xs.min(),ys.min(),xs.max(),ys.max())
# static hair edge band for the flicker metric (outline of hair_back/hair_front, away from strands/bun/face boxes)
st=np.zeros((h,w),np.uint8)
for k in s.static: st|=(s.pa[k]>0.5).astype(np.uint8)
swr=np.zeros((h,w),np.uint8)
for k in s.sway: swr|=(s.pa[k]>0).astype(np.uint8)
band=(cv2.morphologyEx(st,cv2.MORPH_GRADIENT,disk(1))>0)&~(cv2.dilate(swr,disk(4))>0)&~s.boxmask
# control band: edges of face parts (eyes/mouth box interiors) that are not hair
ctrl=s.boxmask&~(cv2.dilate(st|swr,disk(3))>0)
# strand edge band (moves with strands; computed per frame from predicted alpha)
# bun/anchor templates (head-local)
def crop(a,b): return a[b[1]:b[3]+1,b[0]:b[2]+1]
pad=10
bun_box=(bb[0]-pad,bb[1],bb[2]+pad,bb[3]+pad)
if s.boxes:
    ex=[s.boxes[k] for k in s.boxes]; ax0=min(e[0] for e in ex)-s.x0-6; ay0=min(e[1] for e in ex)-s.y0-6; ax1=max(e[2] for e in ex)-s.x0+6; ay1=max(e[3] for e in ex)-s.y0+6
    anchor=(ax0,ay0,ax1,ay1)   # eyes+mouth region
else:  # back: ears / nape region = lower part of hair_back outline
    ys2,xs2=np.nonzero(s.pa['hair_back']>0.5); anchor=(xs2.min()-8,ys2.max()-70,xs2.max()+8,ys2.max()+8)
rows=[]; rest=None; restL=None; prev=None
tipvid={k:None for k in s.tips}
def tmatch(img,tmpl_box,ref,search=12):
    x0,y0,x1,y1=tmpl_box; t=cv2.cvtColor(np.ascontiguousarray(crop(ref,tmpl_box)),cv2.COLOR_RGB2GRAY).astype(np.float32)
    X0,Y0=max(0,x0-search),max(0,y0-search); X1,Y1=min(w-1,x1+search),min(h-1,y1+search)
    I=cv2.cvtColor(np.ascontiguousarray(img[Y0:Y1+1,X0:X1+1]),cv2.COLOR_RGB2GRAY).astype(np.float32)
    r=cv2.matchTemplate(I,t,cv2.TM_SQDIFF_NORMED); mn,_,loc,_=cv2.minMaxLoc(r)
    def sub(v_,i,n):
        if 0<i<n-1:
            a,b,c=v_[i-1],v_[i],v_[i+1]; d=a-2*b+c
            return i+(0.5*(a-c)/d if d!=0 else 0)
        return i
    xx=sub(r[loc[1],:],loc[0],r.shape[1]); yy=sub(r[:,loc[0]],loc[1],r.shape[0])
    return xx+X0-x0, yy+Y0-y0, mn
worst={}
for i,img in stream(vid,s.x0,s.y0,w,h):
    if i>=len(F): break
    fm=F[i]; hb=fm['bones'].get('head') or fm['bones'].get('torso'); ang=hb[2]
    Hm=rotAt(PIV[0],PIV[1],ang); HmR=s.roi_M(Hm); HmRi=np.linalg.inv(HmR)
    local=warp(img,HmRi,w,h)
    if i==0: rest=s.base_comp; restL=s.base_comp; f0diff=float(np.abs(local.astype(np.int16)-restL).mean()); rest_cls={'white':cls_white(rest),'blue':cls_blue(rest),'grey':cls_grey(rest)}; rest_hl=s.hairlike(restL)
    # ---- check 1: new white / blue / background(grey = transparent) inside head/neck mask, frame coords
    Mw=warp(s.Mhead.astype(np.uint8),HmR,w,h,True)>0
    Bw=warp(s.boxmask.astype(np.uint8),HmR,w,h,True)>0
    Sw=warp(s.sil.astype(np.uint8),HmR,w,h,True)>0
    r1={}
    for c_,fn in (('white',cls_white),('blue',cls_blue),('grey',cls_grey)):
        rc=warp(rest_cls[c_].astype(np.uint8),HmR,w,h,True)
        new=fn(img)&Mw&~Bw&~(cv2.dilate(rc,D2)>0)
        if c_=='grey':
            r1['grey_in']=new&Sw; r1['grey_out']=new&~Sw
        else: r1[c_]=new
    # speckle filter: ignore isolated single pixels (compression)
    cnt={}
    for k,m in r1.items():
        lab,n=nd.label(m); sz=nd.sum(m,lab,range(1,n+1)) if n else []
        cnt[k]=int(m.sum()); cnt[k+'_blob']=int(max(sz) if n else 0)
        if cnt[k]:
            ys_,xs_=np.nonzero(m); cnt[k+'_bbox']=[int(xs_.min()+s.x0),int(ys_.min()+s.y0),int(xs_.max()+s.x0),int(ys_.max()+s.y0)]
    # ---- check 2: hair over eye / mouth boxes
    Ms=s.hair_M(fm['hair'])
    fa=hair_alpha(Ms,front)
    geo={k:int(((fa>=0.25)&(rest_front<0.25)&m).sum()) for k,m in s.boxm.items()}
    geo_any={k:int(((fa>=0.05)&(rest_front<0.05)&m).sum()) for k,m in s.boxm.items()}
    hl=s.hairlike(local)
    newhl=hl&~(cv2.dilate(rest_hl.astype(np.uint8),D1)>0)
    vid2={k:int((newhl&m).sum()) for k,m in s.boxm.items()}
    p=fm['params']; lid=max(round((1-p['EyeLOpen'])*7),round((1-p['EyeROpen'])*7)); iris=abs(p['EyeBallX'])>0.2 or abs(p['EyeBallY'])>0.2
    mouthchg=fm['mouth']!='mouth_rest' or (fm.get('mouthPrev') not in (None,'mouth_rest') and fm['t']*1000-fm['mouthT0']<60)
    # ---- check 3: bun (geometry + video template tracking, head-local)
    Mb=Ms['bun']; bc=(Mb@np.array([bun_c0[0],bun_c0[1],1]))[:2]-bun_c0
    bx,by_,bq=tmatch(local,bun_box,restL,10); axx,ayy,aq=tmatch(local,anchor,restL,6)
    # detachment: new background pixels between bun and hair_back (band around bun lower outline)
    ring=(cv2.dilate((s.pa['bun']>0.5).astype(np.uint8),disk(4))>0)&~(s.pa['bun']>0.5)&s.behind
    gap=int((cls_grey(local)&ring&~(cv2.dilate(rest_cls['grey'].astype(np.uint8),D2)>0)).sum())
    # ---- check 4: edge sharpness (frame coords, no resampling of pixels)
    g=cv2.cvtColor(img,cv2.COLOR_RGB2GRAY).astype(np.float32)
    gm=np.hypot(cv2.Sobel(g,cv2.CV_32F,1,0,ksize=3),cv2.Sobel(g,cv2.CV_32F,0,1,ksize=3))
    lap=np.abs(cv2.Laplacian(g,cv2.CV_32F))
    Bd=warp(band.astype(np.uint8),HmR,w,h,True)>0; Cd=warp(ctrl.astype(np.uint8),HmR,w,h,True)>0
    sa=np.zeros((h,w),np.float32)
    for k in s.sway:
        if k!='bun' and s.layers[k]>=600: sa=np.maximum(sa,warp(s.pa[k],s.roi_M(Hm@Ms[k]),w,h))
    Sd=(cv2.morphologyEx((sa>0.5).astype(np.uint8),cv2.MORPH_GRADIENT,D1)>0)&~Bw
    dprev=float(np.abs(g-prev).mean()) if prev is not None else 0.0
    dprev_band=float(np.abs(g-prev)[Bd].mean()) if prev is not None else 0.0
    prev=g
    # ---- check 5: strand tips (geometry head-local and world; video tracking of tip patches)
    tips={}
    for r_,(k,tx,ty) in s.tips.items():
        P0=np.array([tx+s.x0,ty+s.y0,1]); P1=Ms[k]@P0; Pw=Hm@P1
        tips[r_]=[round(float(P1[0]-P0[0]),3),round(float(P1[1]-P0[1]),3),round(float(Pw[0]-P0[0]),3),round(float(Pw[1]-P0[1]),3)]
    tv={}
    for r_,(k,tx,ty) in s.tips.items():
        tb=(int(tx)-9,int(ty)-12,int(tx)+9,int(ty)+4)
        dx_,dy_,q_=tmatch(local,tb,restL,10); tv[r_]=[round(dx_,2),round(dy_,2),round(q_,4)]
    row=dict(frame=i,t=fm['t'],video_t=round(i/FPS,4),head_deg=ang,head_axis=abs(ang)<0.01,lid=lid,iris=bool(iris),mouth=fm['mouth'],mouth_change=bool(mouthchg),
             **{'c1_'+k:v_ for k,v_ in cnt.items()},geo=geo,geo_any=geo_any,vid=vid2,
             bun_geo=[round(float(bc[0]),3),round(float(bc[1]),3)],bun_vid=[round(bx,2),round(by_,2),round(bq,4)],anchor_vid=[round(axx,2),round(ayy,2),round(aq,4)],bun_gap=gap,
             sharp_band=float(gm[Bd].mean()),lap_band=float(lap[Bd].mean()),sharp_ctrl=float(gm[Cd].mean()) if Cd.any() else 0.0,sharp_strand=float(gm[Sd].mean()) if Sd.any() else 0.0,
             dprev=dprev,dprev_band=dprev_band,tips=tips,tips_vid=tv)
    rows.append(row)
    # keep masks for the worst frames (check1 total, check2 video, strand tip) so the sheet can reproduce them
    score=cnt['white']+cnt['blue']+cnt['grey_in']
    for key,sc in (('c1',score),('c1out',cnt['grey_out']),('c2geo',sum(geo.values())),('c2vid',sum(vid2.values()) if not(lid or iris or mouthchg) else 0)):
        if sc>0 and (key not in worst or sc>worst[key]['score']):
            m=np.zeros((h,w),np.uint8)
            if key=='c1': m=((r1['white'])*1+(r1['blue'])*2+(r1['grey_in'])*3).astype(np.uint8)
            elif key=='c1out': m=r1['grey_out'].astype(np.uint8)*3
            elif key=='c2geo': m=((fa>=0.25)&(rest_front<0.25)&s.boxmask).astype(np.uint8)*4
            else: m=(newhl&s.boxmask).astype(np.uint8)*5
            worst[key]=dict(score=int(sc),frame=i,t=fm['t'])
            np.save(f'{OUT}/data/{name}_{key}_mask.npy',m)
class E(json.JSONEncoder):
    def default(self,o):
        return o.item() if hasattr(o,'item') else o.tolist()
json.dump(dict(name=name,frame0_vs_base_meanabs=f0diff,video=vid,view=view,roi=[s.x0,s.y0,s.w,s.h],boxes=s.boxes,anchor=[int(anchor[0]+s.x0),int(anchor[1]+s.y0),int(anchor[2]+s.x0),int(anchor[3]+s.y0)],
               bun_c0=bun_c0.tolist(),tips={k:[v_[0],v_[1]+s.x0,v_[2]+s.y0] for k,v_ in s.tips.items()},worst=worst,rows=rows),open(f'{OUT}/data/{name}.json','w'),cls=E)
print(name,len(rows),'done',worst)
