# Face / mouth measurement on one RGB image (numpy HxWx3). Read-only helper, shared by the video and our views.
import numpy as np
from scipy import ndimage as ndi
def lum(a): return a[...,:3].astype(float)@[0.299,0.587,0.114]
def isblue(a): a=a.astype(int); return (a[...,2]>a[...,0]+60)&(a[...,2]>a[...,1]+60)
def irises(a,box):
    y0,y1,x0,x1=box; s=a[y0:y1,x0:x1].astype(int); r,g,b=s[...,0],s[...,1],s[...,2]
    out={}
    for name,m in (('orange',(r>g+30)&(g>b+45)&(r>140)),('green',(g>r+8)&(g>b+25)&(g>70))):
        lab,n=ndi.label(m)
        if n==0: continue
        sz=ndi.sum(m,lab,range(1,n+1)); k=int(np.argmax(sz))+1
        if sz[k-1]<4: continue
        cy,cx=ndi.center_of_mass(lab==k); out[name]=(cx+x0,cy+y0,float(sz[k-1]))
    return out
def skin_level(a,box):
    y0,y1,x0,x1=box; s=a[y0:y1,x0:x1]; l=lum(s); bl=isblue(s)
    m=(~bl)&(l>110)&(l<200)&(s[...,0].astype(int)>s[...,2].astype(int)+30)
    return float(np.median(l[m])) if m.sum()>20 else 140.0
def mouth(a,box,skin_l,UP=4):
    """Find the lip blob in box (y0,y1,x0,x1). Returns dict in image px or None."""
    from PIL import Image
    y0,y1,x0,x1=box; s=a[y0:y1,x0:x1]
    big=np.array(Image.fromarray(s.astype(np.uint8)).resize(((x1-x0)*UP,(y1-y0)*UP),Image.BICUBIC)).astype(float)
    l=lum(big); r,g,b=big[...,0],big[...,1],big[...,2]; bl=(b>r+60)&(b>g+60)
    lipbody=(l>30)&(l<skin_l-42)&(r-b>25)&(r-g>15)&~bl
    dark=(l<skin_l-30)&~bl
    lab,n=ndi.label(ndi.binary_closing(lipbody,iterations=UP))
    if n==0: return None
    best=None
    for k in range(1,n+1):
        m=lab==k; ys,xs=np.nonzero(m); area=m.sum()/UP**2
        if area<6: continue
        w=(xs.max()-xs.min()+1)/UP; h=(ys.max()-ys.min()+1)/UP
        score=area*min(w/h,3.0)                    # horizontal lip blobs beat vertical hair strands
        if best is None or score>best[0]: best=(score,k)
    if best is None: return None
    core=lab==best[1]
    m=ndi.binary_fill_holes(ndi.binary_dilation(core,iterations=UP)&(dark|core)|core)
    ys,xs=np.nonzero(m)
    lx,rx=xs.min(),xs.max(); ty,by=ys.min(),ys.max()
    def coly(c): rr=np.nonzero(m[:,c])[0]; return (rr.min()+rr.max())/2 if len(rr) else np.nan
    yL=np.nanmean([coly(c) for c in range(lx,min(lx+UP,rx+1))]); yR=np.nanmean([coly(c) for c in range(max(rx-UP+1,lx),rx+1)])
    cxm=(lx+rx)//2
    # seam: darkest row in the centre columns inside the mouth
    lc=l[:,max(cxm-UP,0):cxm+UP+1].mean(1).copy(); lc[~m[:,cxm]]=999
    if not m[:,cxm].any(): lc=l[:,cxm].copy()
    seam=float(np.argmin(lc))
    # opening: near-black cavity or teeth strictly inside
    inner=ndi.binary_erosion(m,iterations=UP)
    teeth=(l>skin_l+45)&(np.abs(r-b)<45)&inner
    cav=(l<22)&inner
    op=ndi.binary_opening(cav|teeth,iterations=1)
    span=0
    for c in range(int(lx+0.25*(rx-lx)),int(lx+0.75*(rx-lx))+1):
        rr=np.nonzero(op[:,c])[0]; span=max(span,(rr.max()-rr.min()+1) if len(rr) else 0)
    # silhouette contact: background within 2 px outside either extreme (mouth corner on the face contour)
    def touches(c,dirn):
        rows=np.nonzero(m[:,c])[0]
        if not len(rows): return False
        cc=np.clip(c+dirn*np.arange(1,2*UP+1),0,m.shape[1]-1)
        return bool(bl[rows.min():rows.max()+1][:,cc].any())
    # sharpness: mean gradient magnitude on the lip outline band, and max edge contrast
    gy,gx=np.gradient(l); gm=np.hypot(gx,gy); band=m^ndi.binary_erosion(m,iterations=UP)
    sharp=float(gm[band].mean()) if band.any() else 0.0
    f=1/UP
    return dict(cx=x0+(lx+rx+1)/2*f, cy=y0+(seam+0.5)*f, top=y0+ty*f, bot=y0+(by+1)*f, left=x0+lx*f, right=x0+(rx+1)*f,
                W=(rx-lx+1)*f, H=(by-ty+1)*f, lift=((seam-(yL+yR)/2))*f, yL=y0+yL*f, yR=y0+yR*f,
                openSpan=span*f, teethPx=float(teeth.sum()*f*f), leftOnContour=touches(lx,-1), rightOnContour=touches(rx,1),
                sharp=sharp, _m=m, _big=big, _box=box)
def chin_below(a,x,y_start,skin_l,ymax):
    """scan down the column from y_start: chin = first background or dark-outline pixel after >=2 skin px"""
    col=a[:,int(round(x))].astype(int); l=lum(col); seen=0
    for y in range(int(y_start),min(ymax,a.shape[0])):
        bg=col[y,2]>col[y,0]+60 and col[y,2]>col[y,1]+60
        if bg or l[y]<skin_l-50:
            if seen>=2: return float(y)
        else: seen+=1
    return None
def nose(a,x0,x1,y0,y1,skin_l,facing):
    """facing: 0 frontish -> nostril centroid; -1/+1 profile facing screen-left/right -> silhouette tip"""
    s=a[y0:y1,x0:x1].astype(int); l=lum(s); bl=(s[...,2]>s[...,0]+60)&(s[...,2]>s[...,1]+60)
    if facing==0:
        m=(l<skin_l-40)&~bl&(s[...,0]>s[...,2]+15)
        lab,n=ndi.label(m)
        if n==0: return None
        ys,xs=np.nonzero(m); return (float(xs.mean()+x0),float(ys.mean()+y0))
    fg=~bl; best=None
    for yy in range(fg.shape[0]):
        xs=np.nonzero(fg[yy])[0]
        if not len(xs): continue
        xe=xs.min() if facing<0 else xs.max()
        v=-xe if facing>0 else xe
        if best is None or v<best[0]: best=(v,xe,yy)
    return (float(best[1]+x0),float(best[2]+y0)) if best else None
