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
def save_part_aa(rgbf,alphaf,path):
    """partial-alpha part (lid frames 1-4 only): keyed RGBA + chroma reference copy composited over #0000FF"""
    al=np.clip(np.round(alphaf*255),0,255).astype(np.uint8); op=al>0
    out=np.zeros((H,W,4),np.uint8); out[...,:3]=np.where(op[...,None],np.clip(np.round(rgbf),0,255),0); out[...,3]=al
    Image.fromarray(out,'RGBA').save(path)
    a=al[...,None]/255.0; ch=(np.clip(rgbf,0,255)*a+KEY*(1-a)).round().astype(np.uint8)
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
        # inner-side columns next to the opening (e.g. the profile's front edge) belong to the lid cover, not the lash
        xx_=np.mgrid[0:H,0:W][1]
        inner_zone=((xx_>c1)&(xx_<=c1+2)) if side<0 else ((xx_<c0)&(xx_>=c0-2))
        lash=lash&~inner_zone
        # hair/temple strands that touch the wing are not lash (Base Hair owns them); cut at the skin gap
        LASH_XMAX={('apose','EyeL'):745}      # exclusive x limit; tpose EyeL wing ends at x=743 before its hair strip (x>=745)
        if (v,e) in LASH_XMAX: lash&=xx_<LASH_XMAX[(v,e)]
        # --- parts ---
        save_part(rgb,lash,f'{od}/{e}_lash.png')
        # ---- extended cover: every drawn eye pixel near the opening (outline AA, crease, corner slivers) ----
        colr3=np.zeros((H,W),bool); colr3[:,c0-2:c1+3]=True
        near4=ndi.binary_dilation(eye_region,iterations=4)
        nonskin=skin_d>20
        dk_lab,_=ndi.label(bb&(lum<80),structure=np.ones((3,3)))
        touch=np.unique(dk_lab[ndi.binary_dilation(eye_region,iterations=1)]); touch=touch[touch>0]
        dark_unconn=(dk_lab>0)&~np.isin(dk_lab,touch)          # moles / brows: never covered
        extra=near4&colr3&bb&nonskin&~dark_unconn&~eye_region
        cover=eye_region|extra
        # drawn crease / fold lines leaving the eye (light or mid tone, connected to it): hidden when closed too
        near7=ndi.binary_dilation(eye_region,iterations=7)
        crease_ok=near7&bb&(skin_d>20)&(lum>=60)&~dark_unconn
        cover=ndi.binary_propagation(cover,mask=cover|crease_ok,structure=np.ones((3,3)))
        # make it column-contiguous (skin gaps between crease and lash get the same flat skin)
        for c in np.nonzero(cover.any(0))[0]:
            rr=np.nonzero(cover[:,c])[0]; cover[rr.min():rr.max()+1,c]=True
        cover&=~dark_unconn
        Ue=np.full(W,-1)
        for c in np.nonzero(cover.any(0))[0]: Ue[c]=np.nonzero(cover[:,c])[0].min()
        # ---- continuous curves (x in pixel units, pixel c spans [c,c+1)) ----
        xc=cols+0.5; mu=xc.mean(); sd=max(1.0,xc.std())
        def pfit(vals,deg=3):
            p=np.polyfit((xc-mu)/sd,np.asarray(vals,float),deg); return lambda x: np.polyval(p,(x-mu)/sd)
        Tc=pfit(top[cols]); Bc=pfit(bot[cols]+1)
        thc=pfit(np.clip(th,1,6),2)
        span=max(1.0,c1+1-c0)
        def outerf(x):
            f=np.clip((x-c0)/span,0,1); return f if side>0 else 1-f
        def sstep(z): z=np.clip(z,0,1); return z*z*(3-2*z)
        m0=(top[c0]+bot[c0]+1)/2; m1=(top[c1]+bot[c1]+1)/2
        def C4(x):   # closed lash bottom edge: gentle arc between corner midpoints sagging toward the lower lid
            ch=m0+(np.clip(x,c0,c1+1)-c0)/span*(m1-m0)
            return ch+0.85*(np.maximum(Bc(x),ch)-ch)
        tmax4=2.4 if wide else 1.6
        def T4(x):
            o=outerf(x); return (0.45+tmax4*sstep((o-0.1)/0.8))*sstep(o/0.18)*sstep((1-o)/0.04+0.2)
        def Tk(x,k):
            o=outerf(x); base_t=np.clip(thc(x),1.4,3.0 if wide else 2.2)
            return (base_t*(1-k/4)+T4(x)*(k/4))*sstep(o/0.15+0.15)
        S=8
        ys_all,xs_all=np.nonzero(cover); by0,by1=ys_all.min(),ys_all.max()+1; bx0,bx1=xs_all.min(),xs_all.max()+1
        sub_off=(np.arange(S)+0.5)/S
        for k in range(5):
            A=np.zeros((H,W)); LF=np.zeros((H,W))     # alpha, lash fraction of covered area
            if k==0:
                lid=(cover|eye_region)&~mask
                save_part(rgb,lid,f'{od}/{e}_lid_0.png'); continue
            for c in range(bx0,bx1):
                colpix=np.nonzero(cover[by0:by1,c])[0]+by0
                if len(colpix)==0: continue
                X=c+sub_off                             # S sub-columns
                incol=(c>=c0)&(c<=c1)
                for y in colpix:
                    Y=y+sub_off                         # S sub-rows
                    Xg,Yg=np.meshgrid(X,Y)
                    if k<4:
                        inner_c=(side<0 and c1<c<=c1+2) or (side>0 and c0-2<=c<c0)
                        if not (incol or inner_c): continue
                        cn=min(max(c,c0),c1); Xq=np.clip(Xg,c0,c1+1)
                        T_=Tc(Xq); B_=Bc(Xq); E=np.clip(T_+k/4*(B_-T_),T_,B_)
                        E=np.minimum(E,bot[cn]+1.0)
                        covered=(Yg>=Ue[c])&(Yg<E)
                        lashm=covered&(Yg>=E-Tk(Xg,k))
                    else:
                        covered=np.ones_like(Xg,bool)
                        E=C4(Xg); lashm=(Yg<E)&(Yg>=E-T4(Xg)) if incol else np.zeros_like(Xg,bool)
                    a_=covered.mean()
                    if a_>0: A[y,c]=a_; LF[y,c]=lashm.sum()/covered.sum()
            A=np.where(cover,A,0)
            # flat colours only: skin and her lash colour; boundary pixels carry coverage (1 px anti-alias)
            col=skin[None,None,:]*(1-LF[...,None])+lashcolor[None,None,:]*LF[...,None]
            save_part_aa(col,A,f'{od}/{e}_lid_{k}.png')
        eye_region=cover|eye_region
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
        e='EyeL'; lim=dict(dxAtXminus1=min(2,max(0,eyeinfo[e]['room_px']['right']-2)),dxAtXplus1=-min(0,eyeinfo[e]['room_px']['left']),dyAtYminus1=-1,dyAtYplus1=1)
    else:            # faces screen-right; her right (-1) = toward camera -> iris toward eye centre (-x)
        e='EyeR'; lim=dict(dxAtXminus1=-min(2,max(0,eyeinfo[e]['room_px']['left']-2)),dxAtXplus1=min(0,eyeinfo[e]['room_px']['right']),dyAtYminus1=-1,dyAtYplus1=1)
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
