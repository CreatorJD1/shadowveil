import numpy as np, json, os
from PIL import Image
from scipy import ndimage as ndi
from build import EYES, SRC, seg_eye, OUTER
ROOT='/workspace/shadowveil/views'
KEY=np.array([0,0,255])
W,H=1365,1739
LAYER_BASE={'EyeR':400,'EyeL':410}
PARAM_OPEN={'EyeR':'EyeROpen','EyeL':'EyeLOpen'}
def save_part(rgb,alpha,path):
    """rgb HxWx3 int, alpha bool. writes keyed RGBA and chroma copy"""
    out=np.zeros((H,W,4),np.uint8); out[...,:3]=np.where(alpha[...,None],rgb,0); out[...,3]=alpha*255
    Image.fromarray(out,'RGBA').save(path)
    ch=np.zeros((H,W,3),np.uint8); ch[:]=KEY; ch[alpha]=rgb[alpha]
    Image.fromarray(ch,'RGB').save(path.replace('.png','_chroma.png'))
def full(m,off):
    F=np.zeros((H,W),bool); x0,y0=off; F[y0:y0+m.shape[0],x0:x0+m.shape[1]]=m; return F
report={}
for v,eyes in EYES.items():
    a=np.array(Image.open(SRC[v]).convert('RGBA')).astype(int)
    assert a.shape[:2]==(H,W)
    rgb=a[...,:3]; lum=rgb.mean(2)
    od=f'{ROOT}/{v}/eyes'; os.makedirs(od,exist_ok=True)
    parts=[]; eyeinfo={}; segs={}
    for e,cfg in eyes.items():
        r=seg_eye(a,cfg); off=r['off']
        mask=full(r['mask'],off); foot=full(r['foot'],off)
        assert a[...,3][mask].min()==255
        # colours sampled from her drawing (flat medians)
        sc=full(r['sc'],off)&mask&~foot
        sclera=np.median(rgb[sc],0).round().astype(int)
        dist=ndi.distance_transform_edt(~mask)
        bb=np.zeros((H,W),bool); x0,y0,x1,y1=cfg['bb']; bb[y0:y1,x0:x1]=True
        ys=np.nonzero(mask)[0]; cy=(ys.min()+ys.max())/2
        yy=np.mgrid[0:H,0:W][0]
        ring=bb&(dist>=3)&(dist<=7)&(yy>cy)&(lum>90)
        ref=np.median(rgb[ring],0); ring&=np.sqrt(((rgb-ref)**2).sum(2))<30
        skin=np.median(rgb[ring],0).round().astype(int)
        # upper lash band: dark pixels connected to the dark band touching the mask top, above centre
        dark=bb&(lum<85)
        lab,_=ndi.label(dark,structure=np.ones((3,3)))
        top_touch=ndi.binary_dilation(mask,iterations=1)&dark&(yy<cy)
        ids=np.unique(lab[top_touch]); ids=ids[ids>0]
        band=np.isin(lab,ids)&(yy<cy+1)&~mask      # her drawn upper lash / liner band
        cols=np.nonzero(mask.any(0))[0]; c0,c1=int(cols.min()),int(cols.max())
        top=np.full(W,-1); bot=np.full(W,-1)
        for c in cols:
            rr=np.nonzero(mask[:,c])[0]; top[c]=rr.min(); bot[c]=rr.max()
        # her drawn lower lid line: dark pixels touching the opening from below
        bot_touch=ndi.binary_dilation(mask,iterations=1)&dark&(yy>cy)&~band
        ids2=np.unique(lab[bot_touch]); ids2=ids2[ids2>0]
        lower=np.isin(lab,ids2)&(yy>cy)&~mask&~band
        skin_d=np.sqrt(((rgb-skin)**2).sum(2))
        # anti-alias pixels of those lines (not skin-like) directly touching them
        aa=bb&ndi.binary_dilation(band|lower,iterations=1)&~(band|lower|mask)&(skin_d>28)
        colr=np.zeros((H,W),bool); colr[:,c0:c1+1]=True
        eye_region=(mask|((band|lower|aa)&colr))
        colr2=np.zeros((H,W),bool); colr2[:,c0-1:c1+2]=True
        from seg2 import hsvarr
        _,satf,_=hsvarr(rgb)
        lightfr=ndi.binary_dilation(eye_region,structure=np.ones((3,3)))&~eye_region&colr2&(lum>140)&(satf<0.4)&bb
        eye_region|=lightfr
        U=np.full(W,-1); Lr=np.full(W,-1)
        for c in cols:
            rr=np.nonzero(eye_region[:,c])[0]; U[c]=rr.min(); Lr[c]=rr.max()
        # smooth curves (least squares polys) for the lid edge
        xs_=cols.astype(float); xn=(xs_-xs_.mean())/max(1,xs_.std())
        def fit(vals,deg=3):
            p=np.polyfit(xn,vals.astype(float),deg); return np.polyval(p,xn)
        Tf=fit(top[cols]); Bf=fit(bot[cols]+1)       # bottom edge of opening (exclusive)
        Lf=fit(Lr[cols].astype(float))
        # closed lash curve: a gentle arc from corner to corner that sags toward her lower lid
        mid0=(top[c0]+bot[c0])/2; mid1=(top[c1]+bot[c1])/2
        chord=mid0+(xs_-c0)/max(1,c1-c0)*(mid1-mid0)
        C4=chord+0.85*(np.maximum(Bf-1,chord)-chord)
        side=OUTER[(v,e)]; frac=(xs_-c0)/max(1,c1-c0); outer=frac if side>0 else 1-frac
        wide=(c1-c0)>=26
        t4=1+np.round((2 if wide else 1)*np.clip((outer-0.15)/0.7,0,1)).astype(int)   # closed lash: thin inner, thick outer
        th=np.array([((band|aa)[:,c]&(np.arange(H)<top[c])).sum() for c in cols],float)
        thf=np.clip(fit(th,2),2,4 if wide else 3)
        # lash = parts of her upper lash that lie outside the opening's columns (outer wing), always on top
        lash=(band|(aa&(yy<cy)))&~colr
        lashcolor=np.median(rgb[band&(lum<50)],0).round().astype(int)
        # --- parts ---
        save_part(rgb,lash,f'{od}/{e}_lash.png')
        for k in range(5):
            lid=np.zeros((H,W),bool); edge=np.zeros((H,W),bool)
            if k>0:
                for i,c in enumerate(cols):
                    if k<4:
                        ev=int(round(Tf[i]+k/4*(Bf[i]-Tf[i])))-1          # last covered row
                        ev=min(max(ev,top[c]),bot[c])
                        t=int(round(thf[i]*(1-k/4)+t4[i]*(k/4)))
                        cov_end=ev
                    else:
                        ev=int(round(C4[i]))
                        ev=min(max(ev,top[c]),Lr[c]); t=int(t4[i]); cov_end=Lr[c]
                    lid[U[c]:cov_end+1,c]=True
                    edge[max(U[c],ev-t+1):ev+1,c]=True
                    # keep the lash line 8-connected (no gaps / dangling dots where the curve is steep)
                    if i>0 and abs(ev-prev)>1:
                        lo_,hi_=sorted((prev,ev))
                        cc=c if ev<prev else cols[i-1]   # fill in the column whose edge is higher
                        edge[lo_:hi_,cc]=True; lid[U[cc]:hi_,cc]=True
                    prev=ev
                lid&=eye_region; edge&=lid
                if k==4: lid|=lightfr
            lr=np.zeros((H,W,3),int); lr[lid]=skin; lr[edge]=lashcolor
            if k==0:   # frame 0 = exactly her drawn lid/lash pixels around the opening (so rest never depends on base_body)
                lid=eye_region&~mask; lr=rgb.copy()
            save_part(lr,lid,f'{od}/{e}_lid_{k}.png')
        # iris / white: iris part carries no light sclera fringe; white backfills the whole drawn iris
        irref=np.median(rgb[full(r['ir'],off)&foot],0)
        near=mask&~foot&ndi.binary_dilation(foot,iterations=3)&(lum>120)
        scl_local=np.median(rgb[near],0) if near.sum()>5 else sclera
        d_i=np.sqrt(((rgb-irref)**2).sum(2)); d_s=np.sqrt(((rgb-scl_local)**2).sum(2))
        edgezone=foot&~ndi.binary_erosion(foot,iterations=2)
        fringe=edgezone&(d_s<d_i)&(lum>120)&(satf<0.25)
        iris=foot&~fringe
        sclera=scl_local.round().astype(int)
        # backfill under the iris with her own sclera pixels: each pixel copies the nearest
        # sclera pixel of the same row (then +-1..3 rows) inside the opening (no invented colour)
        src_ok=mask&~ndi.binary_dilation(foot,iterations=1)&full(r['sc'],off)
        if src_ok.sum()<10: src_ok=mask&~foot&(lum>100)
        white_rgb=rgb.copy(); iy,ix=np.nonzero(iris)
        for y_,x_ in zip(iy,ix):
            done=False
            for dy_ in [0,1,-1,2,-2,3,-3]:
                xs2=np.nonzero(src_ok[y_+dy_])[0]
                if len(xs2):
                    white_rgb[y_,x_]=rgb[y_+dy_,xs2[np.argmin(np.abs(xs2-x_))]]; done=True; break
            if not done: white_rgb[y_,x_]=sclera
        save_part(white_rgb,mask,f'{od}/{e}_white.png')
        save_part(rgb,iris,f'{od}/{e}_iris.png')
        foot=iris
        np.save(f'/workspace/shadowveil/eyes/work/{v}_{e}_mask.npy',eye_region)
        # measurements
        fy,fx=np.nonzero(foot)
        pup=foot&(lum<45)&(yy>=np.nonzero(foot.any(1))[0].min()+1)
        pl,_=ndi.label(pup); 
        icx,icy=fx.mean(),fy.mean()
        if pl.max():
            # component closest to iris centroid
            best=max(range(1,pl.max()+1),key=lambda i:(pl==i).sum())
            py,px=np.nonzero(pl==best); pupil=dict(w=int(np.ptp(px)+1),h=int(np.ptp(py)+1),bbox=[int(px.min()),int(py.min()),int(px.max()),int(py.max())])
        else: pupil=None
        # gaze room along iris centre row
        yc=int(round(icy)); rowm=np.nonzero(mask[yc])[0]; rowf=np.nonzero(foot[yc])[0]
        roomL=int(rowf.min()-rowm.min()); roomR=int(rowm.max()-rowf.max())
        mys=np.nonzero(mask[:,int(round(icx))])[0]
        segs[e]=dict(eye_region=eye_region,mask=mask,foot=foot,top=top,bot=bot,cols=cols)
        eyeinfo[e]=dict(sclera='#%02X%02X%02X'%tuple(sclera),skin='#%02X%02X%02X'%tuple(skin),lash='#%02X%02X%02X'%tuple(lashcolor),
            iris_bbox=[int(fx.min()),int(fy.min()),int(fx.max()),int(fy.max())],iris_w=int(np.ptp(fx)+1),iris_h=int(np.ptp(fy)+1),
            iris_center=[round(float(icx),1),round(float(icy),1)],pupil=pupil,
            opening_bbox=[int(cols.min()),int(np.nonzero(mask.any(1))[0].min()),int(cols.max()),int(np.nonzero(mask.any(1))[0].max())],
            room_px=dict(left=roomL,right=roomR,top_at_center=int(fy.min()-mys.min()),bottom_at_center=int(mys.max()-fy.max())),
            mask_px=int(mask.sum()),iris_px=int(foot.sum()),lash_px=int(lash.sum()))
    # gaze limits (screen px), shared by both eyes in a view
    if v in ('apose','tpose'):
        L=max(0,min(eyeinfo[e]['room_px']['left'] for e in eyes)-2); R=max(0,min(eyeinfo[e]['room_px']['right'] for e in eyes)-2)
        lim=dict(dxAtXminus1=-L,dxAtXplus1=R,dyAtYminus1=-2,dyAtYplus1=2)
    elif v=='left':   # faces screen-left; her right (-1) = toward camera -> iris toward eye centre (+x); front edge is at the iris
        e='EyeL'; lim=dict(dxAtXminus1=min(3,max(0,eyeinfo[e]['room_px']['right']-2)),dxAtXplus1=-min(0,eyeinfo[e]['room_px']['left']),dyAtYminus1=-1,dyAtYplus1=1)
    else:            # faces screen-right; her right (-1) = toward camera -> iris toward eye centre (-x)
        e='EyeR'; lim=dict(dxAtXminus1=-min(3,max(0,eyeinfo[e]['room_px']['left']-2)),dxAtXplus1=min(0,eyeinfo[e]['room_px']['right']),dyAtYminus1=-1,dyAtYplus1=1)
    for k in lim: lim[k]=int(lim[k])
    for e in eyes:
        b=LAYER_BASE[e]; inf=eyeinfo[e]; icx,icy=inf['iris_center']
        ob=inf['opening_bbox']; ocx=(ob[0]+ob[2])/2; ocy=(ob[1]+ob[3])/2
        parts.append(dict(id=f'{e}_white',file=f'{e}_white.png',x=0,y=0,pivotX=ocx,pivotY=ocy,parent=None,layer=b,
                          composite='source-over',note='offscreen eye layer; cut from drawing, iris footprint backfilled with flat sampled sclera'))
        parts.append(dict(id=f'{e}_iris',file=f'{e}_iris.png',x=0,y=0,pivotX=icx,pivotY=icy,parent=f'{e}_white',layer=b+1,
                          composite='source-atop',drive=dict(EyeBallX=[lim['dxAtXminus1'],lim['dxAtXplus1']],EyeBallY=[lim['dyAtYminus1'],lim['dyAtYplus1']],
                          rule='see irisOffsetRule')))
        for k in range(5):
            parts.append(dict(id=f'{e}_lid_{k}',file=f'{e}_lid_{k}.png',x=0,y=0,pivotX=ocx,pivotY=ob[1],parent=f'{e}_white',layer=b+2,
                              frame=k,param=PARAM_OPEN[e],showWhen=f'round((1-{PARAM_OPEN[e]})*4)=={k}'))
        parts.append(dict(id=f'{e}_lash',file=f'{e}_lash.png',x=0,y=0,pivotX=ocx,pivotY=ob[1],parent=f'{e}_white',layer=b+3,composite='source-over'))
    allm=np.zeros((H,W),bool)
    for e_ in eyes:
        allm|=segs[e_]['eye_region']
    import glob as _g
    for f in _g.glob(f'{od}/*_lash.png'): allm|=np.array(Image.open(f))[...,3]>0
    ys_,xs_=np.nonzero(allm); pad=12
    work=[int(xs_.min()-pad),int(ys_.min()-pad),int(xs_.max()+pad+1),int(ys_.max()+pad+1)]
    rig=dict(contract='runtime-contract v1.1',workRegion=work,view=v,canvas=[W,H],units='view pixels, origin top-left; all parts are full-canvas (x=y=0), already in drawn position',
             chromaKey='#0000FF',eyes=list(eyes.keys()),
             eyeIdentity={'EyeR':'her right eye, amber','EyeL':'her left eye, green'},
             baseSource=f'views/{v}/base.png (parts cut from it; rest compared against it)',drawOrderPerEye=['white','iris (source-atop on white, offscreen layer)','lid frame','lash'],
             params=dict(EyeLOpen=dict(range=[0,1],default=1,frames='frame=round((1-EyeLOpen)*4); 0=open(empty) .. 4=closed'),
                         EyeROpen=dict(range=[0,1],default=1,frames='frame=round((1-EyeROpen)*4)'),
                         EyeBallX=dict(range=[-1,1],default=0,note='-1 = her right'),EyeBallY=dict(range=[-1,1],default=0,note='-1 up, 1 down')),
             irisLimitsPx=lim,
             irisOffsetRule='dx = round(X*(dxAtXplus1 if X>0 else -dxAtXminus1)); dy = round(Y*(dyAtYplus1 if Y>0 else -dyAtYminus1)); same offset for every eye in the view',
             parts=parts,measurements=eyeinfo)
    json.dump(rig,open(f'{od}/rig.json','w'),indent=1)
    report[v]=dict(lim=lim,eyes=eyeinfo)
print(json.dumps(report,indent=1))
