import os, numpy as np
from PIL import Image
from scipy import ndimage as ndi
import sys
sys.path.insert(0,'/workspace/shadowveil/eyes/work')
from build import EYES, SRC, seg_eye, OUTER
NF=8; KC=7; W,H=1365,1739
def full(m,off):
    F=np.zeros((H,W),bool); x0,y0=off; F[y0:y0+m.shape[0],x0:x0+m.shape[1]]=m; return F
# geometry of one eye, copied verbatim from eyes/work/export.py (lines 37-45, 50-114, 117-182)
# so the lash-fix works on exactly the regions export.py uses (no part files written here)
def geom(v,e):
    cfg=EYES[v][e]
    a=np.array(Image.open(SRC[v]).convert('RGBA')).astype(int)
    assert a.shape[:2]==(H,W)
    rgb=a[...,:3]; lum=rgb.mean(2)
    from hair_swept import swept
    hair_sw=swept(v,dilate=False)          # exact positions any hair pixel can take (hard: no lid pixel there)
    if hair_sw is None: hair_sw=np.zeros((H,W),bool)
    hair_near8=ndi.binary_dilation(hair_sw,iterations=9)   # crease cover-up keeps >=8 px clear
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
    # smooth the cover outline (no ragged single-pixel notches against her skin)
    du1=ndi.binary_dilation(dark_unconn,iterations=1)
    cs=ndi.binary_closing(cover,structure=np.ones((3,3)),iterations=2)|cover
    cs=ndi.binary_fill_holes(cs)&bb&~du1
    cover=cover|cs
    # tiny dark specks that the cover would enclose are drawn eye pixels too (not moles/brows)
    encl=ndi.binary_fill_holes(cover|dark_unconn)&dark_unconn
    dl,_=ndi.label(dark_unconn,structure=np.ones((3,3)))
    for i_ in np.unique(dl[encl]):
        if i_>0 and not (ndi.binary_dilation(dl==i_)&~(cover|(dl==i_))&(skin_d<45)).sum()>2: cover|=dl==i_
    cover=ndi.binary_fill_holes(cover)&bb
    # lid skin: median of her skin in a thin ring right around the cover (lid, cheek and corners all count)
    ringc=ndi.binary_dilation(cover,iterations=3)&~ndi.binary_dilation(cover,iterations=1)&bb&(skin_d<45)&(lum>60)&~du1
    if ringc.sum()>20: skin=np.median(rgb[ringc],0).round().astype(int)
    # long crease / fold strokes leaving the eye: thin lines that stand out from her local skin
    bgm=np.stack([ndi.median_filter(rgb[...,i].astype(float),size=7) for i in range(3)],-1)
    linepx=np.sqrt(((rgb-bgm)**2).sum(2))>11
    bbx=np.zeros((H,W),bool); bbx[max(0,y0-10):y1+4,max(0,x0-6):x1+6]=True
    near14=ndi.binary_dilation(cover,iterations=14)
    brow=ndi.binary_dilation(dark_unconn,iterations=2)
    brow1=ndi.binary_dilation(dark_unconn,iterations=1)
    # never touch hair: stay 8 px clear of every hair part's swept area; never touch the fringe of brows/hair masses
    dark_other=(lum<90)&~cover&~eye_region
    do_l,do_n=ndi.label(dark_other,structure=np.ones((3,3)))
    if do_n:
        sz=ndi.sum(dark_other,do_l,index=np.arange(1,do_n+1))
        dark_other=np.isin(do_l,np.nonzero(sz>=40)[0]+1)     # brow / hair masses only; thin crease cores stay eligible
    cand=linepx&near14&bbx&~brow1&(lum>=45)&~cover&~hair_near8&~ndi.binary_dilation(dark_other,iterations=2)
    # allow 1 px gaps along a faint stroke (propagate through the 1 px dilation, keep only true stroke pixels)
    crease=ndi.binary_propagation(cover,mask=cover|(ndi.binary_dilation(cand,iterations=1)&~brow1),structure=np.ones((3,3)))&cand
    if os.environ.get('DBG'): pass
    # fill value for crease pixels on the closed frame: copy of the nearest plain skin pixel of hers
    plain=bbx&~linepx&~cover&~brow&(skin_d<45)&(lum>60)
    _,(iy_,ix_)=ndi.distance_transform_edt(~plain,return_indices=True)
    crease_rgb=rgb[iy_,ix_]
    # profile forward lashes (inner side beyond the lid cover): they ride with the lid on frames 1-4
    fwd=np.zeros((H,W),bool)
    if v in ('left','right'):
        outside=(xx_<c0-2) if side>0 else (xx_>c1+2)
        fwd=lash&outside
        fwd=ndi.binary_propagation(fwd,mask=fwd|(ndi.binary_dilation(fwd,iterations=1)&bb&(skin_d>25)&outside),structure=np.ones((3,3)))
        lash=lash&~fwd
        pass
    fwd_cover=ndi.binary_dilation(fwd,iterations=1)&bb&(skin_d>18)|fwd
    if fwd.any():   # plus the pale fringe of her lash strokes (light, not hair)
        fwd_cover|=ndi.binary_dilation(fwd,iterations=2)&bb&(skin_d>18)&(lum>110)&~ndi.binary_dilation(mask,iterations=1)
    if os.environ.get('DBG'): np.save(f'/tmp/dbgf_{v}_{e}.npy',np.stack([fwd,fwd_cover,mask,cover]))
    Ue=np.full(W,-1)
    for c in np.nonzero(cover.any(0))[0]: Ue[c]=np.nonzero(cover[:,c])[0].min()
    return dict(locals())
