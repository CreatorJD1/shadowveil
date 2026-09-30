"""Shadowveil mouth parts v2 (contract v1). Never writes to views/<view>/base.png."""
from PIL import Image, ImageDraw
import numpy as np, json, os, hashlib, itertools
from scipy import ndimage as ndi
from lipmask import load, lip_mask
ROOT='/workspace/shadowveil'; PREV=f'{ROOT}/mouth'
SS=8; BLUE=np.array([0,0,255.])
NAMES=['rest','M','smile','OH','AA','EE']
GRID={'rest':(0,0),'M':(0,-1),'smile':(0,1),'OH':(1,-1),'AA':(1,0),'EE':(1,1)}
GUESS={'apose':(681,289),'tpose':(684,281),'left':(609,285),'right':(774,272)}
def hx(c): return '#%02X%02X%02X'%tuple(int(round(v)) for v in c)

def palette(b,M,seam_y,profile):
    rgb=b[...,:3]; lum=rgb@[0.299,0.587,0.114]; H,W=lum.shape
    ys,xs=np.nonzero(M); x0,x1,y0,y1=xs.min(),xs.max(),ys.min(),ys.max()
    ring=ndi.binary_dilation(M,iterations=7)&~ndi.binary_dilation(M,iterations=3)&(b[...,3]==255)&(lum>110)
    P={}
    P['skin']=np.median(rgb[ring],0)
    yy=np.mgrid[0:H,0:W][0]
    P['upper']=np.median(rgb[M&(yy<seam_y-0.5)&(lum>35)&(lum<85)],0)
    P['lower']=np.median(rgb[M&(yy>seam_y+1.5)&(lum>45)&(lum<100)],0)
    P['line']=np.median(rgb[M&(lum<32)],0)
    hl=M&(lum>130); P['hl']=np.median(rgb[hl],0) if hl.sum() else np.array([232.,194.,172.])
    if hl.sum(): P['hl']=rgb[hl][np.argsort(lum[hl])[-max(1,hl.sum()//3):]].mean(0)  # brightest third = the flat gloss colour
    near=ndi.binary_dilation(M,iterations=6)&(b[...,3]>200)&(rgb[...,2]>rgb[...,0])&(lum<90)
    P['outline']=np.median(rgb[near],0) if near.sum()>3 else P['line']
    P['outline'][2]=min(P['outline'][2],max(P['outline'][0],P['outline'][1]))   # despill: no blue cast in our pixels
    P['inner']=np.array([0x33,0x19,0x0F],float); P['teeth']=np.array([0xED,0xE3,0xDA],float); P['tongue']=np.array([0x93,0x59,0x4A],float)
    return P

# ---------------- front parametric mouth (units = apose px; scaled per view) ----------------
def front_layers(Xn,Yn,P,Wi,Wo,cy,Hup,bow,Su,Sl,Lo,pu=0.8,pl=0.8,po=0.8,pho=0.7,cx=-0.5,
          tc=1.4,te=2.2,teeth_up=0,teeth_lo=0,tongue=None,flick=(4,1.6,1.2),hl=(0,0,3.5,0.8),lowline=0.0,s=1.0):
    X,Y=Xn,Yn; x=X-cx; ui=np.clip(x/Wi,-1,1); uo=np.clip(x/Wo,-1,1); SSn=SS*s
    g=(1-uo**2).clip(0)**pho*(1-bow*np.exp(-(uo/0.16)**2))
    y_uo=cy-Hup*g; y_ui=cy+Su*(1-ui**2).clip(0)**pu; y_li=cy+Sl*(1-ui**2).clip(0)**pl; y_lo=cy+Lo*(1-uo**2).clip(0)**po
    inW=np.abs(x)<Wo; inWi=np.abs(x)<Wi
    outer=inW&(Y>=y_uo)&(Y<=y_lo); opening=inWi&(Y>y_ui)&(Y<y_li)&(Sl>Su)
    seam=np.where(inWi,y_ui,cy); upper=outer&~opening&(Y<seam); lower=outer&~opening&(Y>=seam)
    L=[(P['upper'],upper),(P['lower'],lower)]
    if Sl>Su:
        L.append((P['inner'],opening))
        if tongue:
            tx,ty,rx,ry=tongue; L.append((P['tongue'],opening&(((x-tx)/rx)**2+((Y-ty)/ry)**2<1)))
        if teeth_up: L.append((P['teeth'],opening&(Y<y_ui+teeth_up)&(np.abs(x)<Wi*0.82)))
        if teeth_lo: L.append((P['teeth'],opening&(Y>y_li-teeth_lo)&(np.abs(x)<Wi*0.7)))
    t=(tc+(te-tc)*np.abs(ui)**2)
    d_up=ndi.distance_transform_edt(~upper)/SSn
    line=(~upper)&(d_up<t)&inWi&(outer|opening)
    if lowline>0: line|=opening&(ndi.distance_transform_edt(~lower)/SSn<lowline)
    if flick:
        ln,out,up=flick
        for sg in (-1,1):
            p0=np.array([cx+sg*(Wi-ln),cy+Su*(1-((Wi-ln)/Wi)**2)**pu if Sl<=Su else cy+0.3]); p1=np.array([cx+sg*(Wo+out),cy-up])
            v=p1-p0; tt=np.clip(((X-p0[0])*v[0]+(Y-p0[1])*v[1])/(v@v),0,1)
            line|=np.hypot(X-(p0[0]+tt*v[0]),Y-(p0[1]+tt*v[1]))<(1.15*(1-tt)+0.55*tt)
    L.append((P['line'],line))
    if hl:
        a,bq,rx,ry=hl; L.append((P['hl'],lower&(((x-a)/rx)**2+((Y-bq)/ry)**2<1)))
    return L
FRONT={
 'M':    dict(Wi=20.5,Wo=20.5,cy=-1.0,Hup=3.0,bow=0.35,Su=1.6,Sl=1.6,Lo=8.0,pu=1.0,po=0.9,tc=1.8,te=2.3,flick=(4,1.3,0.6),hl=(0,5.2,3.0,0.7)),
 'smile':dict(Wi=25.5,Wo=25.5,cy=-7.0,Hup=3.4,bow=0.45,Su=7.6,Sl=7.6,Lo=14.2,pu=1.35,po=1.25,pho=0.9,tc=1.4,te=2.0,flick=(5,1.4,3.0),hl=(0,11.4,3.3,0.75)),
 'OH':   dict(Wi=7.5,Wo=10.5,cy=2.0,Hup=11.0,bow=0.12,Su=-6.0,Sl=9.5,Lo=15.5,pu=0.5,pl=0.5,po=0.55,pho=0.5,tc=1.3,te=1.3,flick=None,tongue=(0,11.5,7.5,5.5),hl=(0,13.6,2.2,0.6),lowline=0.7),
 'AA':   dict(Wi=19.0,Wo=21.0,cy=0.5,Hup=6.5,bow=0.3,Su=-3.2,Sl=15.5,Lo=21.5,pu=0.55,pl=0.6,po=0.6,tc=1.4,te=1.8,flick=(2,1.2,0.6),teeth_up=2.6,tongue=(0,19,14,8),hl=(0,18.8,3.2,0.7),lowline=0.7),
 'EE':   dict(Wi=24.0,Wo=25.0,cy=-2.5,Hup=3.6,bow=0.35,Su=1.2,Sl=7.2,Lo=13.5,pu=0.8,pl=0.75,po=0.85,tc=1.3,te=1.8,flick=(3,1.4,1.6),teeth_up=3.6,teeth_lo=1.4,hl=(0,10.5,3.2,0.7),lowline=0.6),
}

# ---------------- profile polygons (right-facing frame, origin = mouth corner, x forward; right-view units) -------------
def poly_mask(pts,X,Y):
    # rasterise polygon on the 8x grid via PIL (pts in local px units)
    return pts
# right-view units (x forward from the back corner, y down from the seam). Base-like lip outlines measured from right/base.png;
# anything forward of her silhouette is clipped to it (except OH/AA, which push past it and get an outline).
UP=[(0,-0.3),(6,-1.6),(10,-4),(13,-6.5),(15.5,-8.3),(18,-8.2),(30,-7.5),(30,-0.2)]
LO=[(0.5,0.4),(30,0.4),(30,6),(18,7),(16,8.5),(13.5,10.3),(11.5,10.6),(9,8.5),(6,6),(3,2.5)]
def sc(P,fy=1.0,dy=0.0,dx=0.0,fx=1.0): return [(x*fx+dx,y*fy+dy) for x,y in P]
PROF={
 'M':dict(upper=sc(UP,0.75),lower=sc(LO,0.72,0.3),seam=[(-0.9,0.1),(8,0.15),(30,0.2)],seam_w=1.7,hl=(14,4.2,1.1,0.8)),
 'smile':dict(upper=[(-2.5,-1.9),(2,-1.5)]+sc(UP[1:],0.85),lower=[(-2.5,-1.7),(2,-0.9),(30,-0.1)]+sc(LO[2:],0.85,0.2),
          seam=[(-3.2,-2.4),(-1,-1.4),(3,-0.7),(10,-0.25),(30,-0.1)],seam_w=1.5,hl=(14,4.8,1.1,0.8)),
 'EE':dict(upper=[(-2.2,-1.5),(2,-1.4)]+sc(UP[1:],0.85,-0.6),
          inner=[(-1.5,-1.0),(4,-1.1),(30,-1.3),(30,2.4),(4,1.2),(-1.2,-0.7)],
          teeth=[(6,-1.1),(30,-1.3),(30,2.1),(6,0.9)],
          lower=[(-1.5,-0.8),(4,1.3),(30,2.4)]+sc(LO[2:],0.8,2.0),
          seam=[(-2.8,-1.9),(-0.8,-1.2),(8,-1.2),(30,-1.3)],seam_w=1.3,hl=(13.5,6.5,1.1,0.8),
          push=dict(fwd=0.8,down=0.0,part='lips')),
 # lips pushed forward ~2 px, small round opening at the front
 'OH':dict(upper=sc([(5,0.6),(8,-1.6)]+UP[2:-1]+[(30,-1.4),(14,-0.9),(8,0.2)],1.0,-0.6,1.8),
          inner=sc([(6,0.7),(8,0.2),(14,-0.9),(30,-1.4),(30,4.6),(14,3.6),(8,1.6)],1.0,0,1.8),
          tongue=sc([(10,2.6),(16,3.7),(30,4.4),(30,3.4),(16,2.6)],1.0,0,1.8),
          lower=sc([(5.5,1.0),(8,1.6),(14,3.6),(30,4.6),(30,9.5),(18,10),(15.5,11.5),(13,12.6),(11,12.4),(8.5,9.5),(6.5,5)],1.0,0,1.8),
          seam=sc([(5,0.5),(8,0.1),(14,-0.8),(30,-1.3)],1,0,1.8),seam_w=1.1,lowline=sc([(8,1.7),(14,3.7),(30,4.7)],1,0,1.8),hl=(16.5,8.3,1.1,0.8),
          push=dict(fwd=2.0,down=0.0,part='lips')),
 # small jaw drop: lower lip + chin front move down ~4 px
 'AA':dict(upper=UP[:-2]+[(30,-7.5),(30,-1.2),(18,-0.9),(8,-0.5)],
          inner=[(0,0.4),(8,-0.5),(18,-0.9),(30,-1.2),(30,5.6),(17,5.6),(9,4.6),(3,2.5)],
          teeth=[(10,-0.6),(18.5,-0.9),(30,-1.2),(30,1.1),(18.5,1.2),(10.5,0.7)],
          tongue=[(4,3.0),(9,4.7),(13,5.4),(11,4.4),(7,3.2)],
          lower=[(1.5,1.4),(3,2.5),(9,4.6),(17,5.6),(30,5.6)]+sc(LO[2:],1.0,5.0),
          seam=[(-0.5,0.2),(8,-0.4),(18,-0.85)],seam_w=1.4,lowline=[(14,5.5),(17,5.7)],hl=(13.5,10.3,1.1,0.8),
          push=dict(fwd=0.0,down=5.0,part='lower')),
}

def raster(pts,sx,sy,ox,oy,shape):
    """polygon (local units) -> 8x mask. local->8x px: X8=(ox+x*sx)*SS"""
    im=Image.new('L',(shape[1],shape[0]),0)
    ImageDraw.Draw(im).polygon([((ox+x*sx)*SS,(oy+y*sy)*SS) for x,y in pts],fill=255)
    return np.array(im)>0
def stroke(pts,w,sx,sy,ox,oy,shape):
    im=Image.new('L',(shape[1],shape[0]),0); d=ImageDraw.Draw(im)
    P=[((ox+x*sx)*SS,(oy+y*sy)*SS) for x,y in pts]
    d.line(P,fill=255,width=max(1,int(round(w*SS))),joint='curve')
    r=w*SS/2
    for q in (P[0],P[-1]): d.ellipse([q[0]-r,q[1]-r,q[0]+r,q[1]+r],fill=255)
    return np.array(im)>0

def down(rgb8,a8,CH,CW):
    pre=(rgb8*a8[...,None]).reshape(CH,SS,CW,SS,3).mean((1,3)); al=a8.reshape(CH,SS,CW,SS).mean((1,3))
    out=np.zeros((CH,CW,4)); nz=al>1e-6; out[nz,:3]=pre[nz]/al[nz,None]; out[...,3]=al; return out

def key_palette(chroma,pal):
    """Chroma key for flat-palette art: interior pixels keep their colour at alpha 1; pixels within 2 px of blue are
    unmixed as w1*P_i + w2*P_j + (1-w1-w2)*BLUE over pairs of palette colours (NNLS), colour = palette mix (despilled)."""
    c=chroma.astype(float); isb=np.linalg.norm(c-BLUE,axis=-1)<3
    Pm0=np.array(pal); pure=np.min(np.linalg.norm(c[...,None,:]-Pm0[None,None],axis=-1),-1)<2.5
    edge=ndi.binary_dilation(isb,iterations=5)&~isb&~pure
    out=np.zeros(c.shape[:2]+(4,)); fg=~isb
    out[fg,:3]=c[fg]; out[fg,3]=1
    Pm=np.array(pal); ys,xs=np.nonzero(edge); C=c[ys,xs]-BLUE
    best=np.full(len(C),1e9); A=np.zeros(len(C)); F=np.zeros((len(C),3))
    from scipy.optimize import nnls
    D=Pm-BLUE
    for i,j in itertools.combinations_with_replacement(range(len(Pm)),2):
        Mx=np.stack([D[i],D[j]],1)
        # least squares for all pixels, then clamp (fast approx of nnls) 
        pinv=np.linalg.pinv(Mx); w=(C@pinv.T).clip(0)
        s=w.sum(1); w[s>1]/=s[s>1,None]
        res=np.linalg.norm(C-w@Mx.T,axis=1)
        if i!=j: res=res+1.5   # prefer single-colour-over-blue explanations; pairs only when clearly better
        better=res<best; best[better]=res[better]; A[better]=w[better].sum(1)
        Fm=(w[:,:1]*Pm[i]+w[:,1:]*Pm[j])/np.maximum(w.sum(1,keepdims=True),1e-6); F[better]=Fm[better]
    A[A>0.90]=1.0; A[A<0.02]=0.0   # snap near-opaque / near-empty
    out[ys,xs,:3]=F; out[ys,xs,3]=A
    out[isb]=0
    return np.round(np.dstack([out[...,:3],out[...,3:]*255])).clip(0,255).astype(np.uint8), best.max() if len(best) else 0

def key_hard(chroma):
    c=chroma.astype(int); isb=(c[...,0]==0)&(c[...,1]==0)&(c[...,2]==255)
    out=np.zeros(c.shape[:2]+(4,),np.uint8); out[...,:3]=np.where(isb[...,None],0,c); out[...,3]=np.where(isb,0,255); return out

def blue_left(k):
    r,g,b,a=[k[...,i].astype(int) for i in range(4)]
    vis=a>0
    return int((vis&(b>np.maximum(r,g)+45)&(b>90)).sum()), int((vis&(np.abs(r)<40)&(np.abs(g)<40)&(b>200)).sum())

def build(view):
    b=load(view); H,W=b.shape[:2]; profile=view in('left','right')
    M,D,_=lip_mask(b,*GUESS[view],profile=profile)
    ys,xs=np.nonzero(M); bbox=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())]
    rgb=b[...,:3]; lum=rgb@[0.299,0.587,0.114]
    flip=(view=='left')
    if not profile:
        cxm=(xs.min()+xs.max())/2; cols=range(int(cxm)-2,int(cxm)+3)
        seam=np.mean([ys.min()+np.argmin(lum[ys.min():ys.max()+1,x]) for x in cols])
        AX,AY=int(round(cxm+0.01)),int(round(seam))
    else:
        bx=xs.max() if flip else xs.min()   # back corner of mouth
        colp=np.nonzero(M[:,bx])[0]; AX,AY=int(bx),int(round(colp.mean()))
        seam=AY
    P=palette(b,M,seam,profile)
    # local box
    CW,CH=(120,80); OX,OY=AX-CW//2,AY-30
    loc=lambda A: A[OY:OY+CH,OX:OX+CW]
    kr=lambda m: np.kron(m,np.ones((SS,SS)))>0
    Dl=loc(D); Ml=loc(M); bl=loc(b)
    # underlay: covers every drawn lip pixel (dilated 2 px), hard alpha 1, then ~1px feather outside
    und_hard=kr(ndi.binary_dilation(Dl,iterations=2))
    if profile:  # skin fills the mouth zone right up to her (opaque) silhouette; never outside it
        inside=kr(bl[...,3]>0)|kr(Dl)
        zone=ndi.binary_dilation(Dl,iterations=5)
        und_hard=kr((zone&(bl[...,3]==255))|Dl)
    und_soft=np.maximum(ndi.gaussian_filter(kr(ndi.binary_dilation(Dl,iterations=3)).astype(float),SS*0.6),und_hard)
    if profile: und_soft*=inside
    parts={}; truths={}
    # REST: straight cut of base pixels, no cleanup, only where base is fully opaque (so base+rest == base exactly)
    rest_region=ndi.binary_dilation(D,iterations=3)&(b[...,3]==255)
    rest=np.zeros((H,W,4)); rest[rest_region]=b[rest_region]; rest[...,3]/=255.0
    truths['rest']=rest
    ys8,xs8=np.mgrid[0:CH*SS,0:CW*SS]
    X=(xs8+0.5)/SS-(AX-OX); Y=(ys8+0.5)/SS-(AY-OY)
    if not profile:
        s=(bbox[2]-bbox[0]+1)/48.0
        for n,p in FRONT.items():
            L=front_layers(X/s,Y/s,P,s=s,**p)
            rgb8=np.zeros((CH*SS,CW*SS,3)); a8=np.zeros((CH*SS,CW*SS)); rgb8[:]=P['skin']; a8[:]=und_soft
            for col,mk in L: rgb8[mk]=col; a8[mk]=1
            full=np.zeros((H,W,4)); full[OY:OY+CH,OX:OX+CW]=down(rgb8,a8,CH,CW); truths[n]=full
    else:
        # right-facing frame; for left view mirror x.  scale to this view's lip size (right view = reference)
        sign=-1 if flip else 1
        row=b[AY,:,3]>128
        xsil=(np.nonzero(row[:AX])[0].min() if flip else np.nonzero(row[AX:])[0].max()+AX)
        Fs=abs(xsil-AX); Lb=ys.max()-AY
        sx=sign*Fs/24.0; sy=Lb/12.0
        ox=AX-OX+0.5*(1 if not flip else 0); oy=AY-OY+0.5
        shp=(CH*SS,CW*SS); px=float(SS)
        alpha8=np.array(Image.fromarray(bl[...,3].astype(np.uint8)).resize((CW*SS,CH*SS),Image.BILINEAR)).astype(float)/255
        S8=ndi.gaussian_filter(alpha8,0.35*px)>0.4          # her silhouette, sub-pixel smooth
        Dk=kr(Dl); Ml_=Ml
        seam_row=AY-OY
        lowerM=Ml_.copy(); lowerM[:seam_row+1]=False
        for n,p in PROF.items():
            R=lambda k: raster(p[k],sx,sy,ox,oy,shp)
            # ---- new silhouette: hers, plus a swept push of the lips/lower lip, then smoothed; always contains drawn lips
            N=S8|Dk
            add=np.zeros(shp,bool)
            if 'push' in p:
                pp=p['push']; src=kr(ndi.binary_dilation(lowerM if pp['part']=='lower' else Ml_,iterations=2))&N
                dxp=int(round(pp['fwd']*abs(sx)*px))*sign; dyp=int(round(pp['down']*sy*px))
                steps=max(abs(dxp),abs(dyp),1)
                for t in np.linspace(0,1,max(2,steps//2+1)):
                    add|=ndi.shift(src,(t*dyp,t*dxp),order=0)
                N=N|add
            zone=ndi.binary_dilation(Dl,iterations=7)
            if add.any(): zone|=ndi.binary_dilation(add.reshape(CH,SS,CW,SS).any((1,3)),iterations=4)
            Z8=kr(zone)
            Ns=ndi.gaussian_filter(N.astype(float),1.0*px)>0.35
            N=np.where(Z8,Ns|Dk,S8|Dk)
            # ---- paint
            rgb8=np.zeros(shp+(3,)); a8=np.zeros(shp)
            rgb8[:]=P['skin']; a8[N]=1.0                                # skin underlay right up to the (new) silhouette
            edt=ndi.distance_transform_edt(N)/px
            band=N&(edt<1.05)                                          # her ~1 px line, drawn by the part
            inner_clip=N&~band
            cav=np.zeros(shp,bool)
            order=[('upper','upper'),('inner','inner'),('tongue','tongue'),('teeth','teeth'),('lower','lower')]
            for key,col in order:
                if key not in p: continue
                m=R(key)
                if key=='teeth': m&=N&(edt>1.8)                       # teeth sit behind the lips, never on the edge
                elif key=='tongue': m&=N&(edt>1.6); cav|=m
                elif key=='inner': m&=N; cav|=m
                else: m&=N
                rgb8[m]=P[col]
            st=stroke(p['seam'],p['seam_w']*abs(sy),sx,sy,ox,oy,shp)
            if 'lowline' in p: st|=stroke(p['lowline'],0.8*abs(sy),sx,sy,ox,oy,shp)
            st&=N; rgb8[st]=P['line']
            if 'hl' in p:
                hx_,hy,rx,ry=p['hl']; e=(((X-hx_*sx)/(rx*abs(sx)))**2+((Y-hy*sy)/(ry*abs(sy)))**2<1)&np.all(rgb8==P['lower'],-1)
                rgb8[e]=P['hl']
            ob=band&~cav                                               # open mouth: cavity reaches the front, no line across it
            rgb8[ob]=P['outline']
            # ---- only act inside the mouth zone; fade out over 3 px so our line joins hers smoothly
            wz=np.clip(ndi.distance_transform_edt(Z8)/(3*px),0,1)
            core=kr(ndi.binary_dilation(Dl,iterations=3))
            wz[core]=1.0
            a8=a8*wz
            part=down(rgb8,a8,CH,CW)
            full=np.zeros((H,W,4)); full[OY:OY+CH,OX:OX+CW]=part; truths[n]=full
    # ---- export: chroma preview -> key -> delivered RGBA
    od=f'{ROOT}/views/{view}/mouth'; pd=f'{PREV}/{view}'; os.makedirs(od,exist_ok=True); os.makedirs(pd,exist_ok=True)
    pal=[P[k] for k in ('skin','upper','lower','line','hl','inner','teeth','tongue','outline')]
    report={}
    for n in NAMES:
        t=truths[n]; al=t[...,3:]
        chroma=np.round(t[...,:3]*al+BLUE*(1-al)).clip(0,255).astype(np.uint8)
        Image.fromarray(chroma,'RGB').save(f'{pd}/{n}_chroma.png')
        if n=='rest': k=key_hard(chroma); kres=0
        else:
            k,kres=key_palette(chroma,pal)
            mx=np.maximum(k[...,0],k[...,1]); k[...,2]=np.minimum(k[...,2],mx)   # despill: B never above max(R,G)
            k[k[...,3]==0,:3]=0
        Image.fromarray(k,'RGBA').save(f'{od}/{n}.png')
        e=np.abs(k[...,3]/255-al[...,0]); wy,wx=np.unravel_index(e.argmax(),e.shape)
        report[n]=dict(maxAlphaErr=float(e.max()),worstAt=(int(wx),int(wy),round(float(al[wy,wx,0]),3)),meanAlphaErrOnPart=float(e[al[...,0]>0].mean()),keyResidual=float(kres),blue=blue_left(k))
    rig=dict(contract='v1',view=view,owner='Base Mouth',canvas=dict(width=W,height=H),
        anchor=dict(x=AX,y=AY,desc='front: lip-seam centre; profile: back corner of the mouth (seam end)'),
        drawnMouthBBox=dict(x0=bbox[0],y0=bbox[1],x1=bbox[2],y1=bbox[3],note='inclusive, view px, lip pixels of base.png'),
        partsBBox={},
        params=dict(MouthOpen=dict(min=0,max=1,default=0),MouthForm=dict(min=-1,max=1,default=0)),
        grid={n:dict(MouthOpen=GRID[n][0],MouthForm=GRID[n][1]) for n in NAMES},
        selection=dict(mode='nearest',metric='euclidean on (MouthOpen, MouthForm), both clamped',
            tieBreak='prefer rest, then closed shapes (MouthOpen=0)',crossfadeMs=60,crossfade='opacity only: outgoing 1->0, incoming 0->1, drawImage + globalAlpha'),
        colors={k:hx(v) for k,v in P.items()},
        parts=[])
    for n in NAMES:
        k=np.array(Image.open(f'{od}/{n}.png')); yy,xx=np.nonzero(k[...,3])
        rig['partsBBox'][n]=[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())]
        rig['parts'].append(dict(id=f'mouth_{n}',file=f'{n}.png',x=0,y=0,pivotX=AX,pivotY=AY,parent='base',layer=5))
    json.dump(rig,open(f'{od}/rig.json','w'),indent=2)
    return b,M,D,report,(AX,AY),bbox,P

if __name__=='__main__':
    import sys
    views=sys.argv[1:] or ['apose','tpose','right','left']
    allrep={}
    for v in views:
        h0=hashlib.md5(open(f'{ROOT}/views/{v}/base.png','rb').read()).hexdigest()
        b,M,D,rep,anc,bbox,P=build(v)
        # self-check
        base_u8=np.array(Image.open(f'{ROOT}/views/{v}/base.png').convert('RGBA'))
        bim=Image.fromarray(base_u8)
        res={}
        for n in NAMES:
            part=Image.open(f'{ROOT}/views/{v}/mouth/{n}.png')
            comp=np.array(Image.alpha_composite(bim,part))
            pa=np.array(part)[...,3]
            res[n]=dict(changedPx=int((comp!=base_u8).any(-1).sum()),uncoveredLipPx=int((D&(pa<255)).sum()),lipPx=int(D.sum()),**rep[n])
        h1=hashlib.md5(open(f'{ROOT}/views/{v}/base.png','rb').read()).hexdigest()
        print(v,'anchor',anc,'bbox',bbox,'base unchanged',h0==h1)
        for n in NAMES: print('  ',n,res[n])
        allrep[v]=dict(anchor=anc,bbox=bbox,colors={k:hx(c) for k,c in P.items()},checks=res,baseMd5=h1)
    json.dump(allrep,open(f'{PREV}/selfcheck_{"_".join(views)}.json','w'),indent=2)
