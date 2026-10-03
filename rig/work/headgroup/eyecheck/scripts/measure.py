# Base Eyes QA: eye offsets at turn handoffs with ?headgroup=1 (read-only; outputs in this folder).
# residual = turn frame (warped into view px with Body's angle_map handoff) minus rig render with head group at rest.
import json,numpy as np,cv2
from PIL import Image
from scipy import ndimage as ndi
R='/workspace/shadowveil/';Q=R+'rig/work/headgroup/eyecheck/'
AM=json.load(open(R+'body_tools/work/apose_turn/angle_map.json'))['handoff']
HGJ=json.load(open(R+'rig/partmesh/staged/headgroup.json'))['handoffs']
EYES=[('apose','EyeR'),('apose','EyeL'),('left','EyeL'),('right','EyeR')]
SR=18
def onblue(p):
    a=Image.open(p).convert('RGBA');bg=Image.new('RGBA',a.size,(0,0,255,255));bg.alpha_composite(a);return np.asarray(bg.convert('RGB'))
def warp_frame(v):
    h=AM[v];s=h['scale'];fr=Image.open(R+f"reference/apose_turn/frames/f{h['frame']:03d}.png").convert('RGB')
    return np.asarray(fr.transform((1365,1739),Image.AFFINE,(1/s,0,-h['dx']/s,0,1/s,-h['dy']/s),resample=Image.BICUBIC))
def lab(I):
    L=cv2.cvtColor(np.ascontiguousarray(I),cv2.COLOR_RGB2LAB).astype(float);return L[...,0]*100/255,L[...,1]-128,L[...,2]-128
def part(v,E,p,dx,dy):
    a=np.asarray(Image.open(R+f'views/{v}/eyes/{E}_{p}.png').convert('RGBA'))[...,3]>127
    return ndi.shift(a,(dy,dx),order=0)
def bgm(I): return (I[...,2].astype(int)>I[...,0]+60)&(I[...,2].astype(int)>I[...,1]+60)
def iris_mask(I,E,win,ref=None):
    """colour iris(+enclosed pupil) segmentation, same rule for rig and frame."""
    x0,y0,x1,y1=win;L,a,b=lab(I);bg=bgm(I)
    W=np.zeros(L.shape,bool);W[y0:y1,x0:x1]=True
    W&=ndi.distance_transform_edt(~bg)>4   # drop key-fringe px at the face silhouette
    skin=W&~bg&(L>45)&(L<80)&(a>8)&(b>15)
    sL,sa,sb=[np.median(q[skin]) for q in (L,a,b)];sh=np.degrees(np.arctan2(sb,sa))
    hue=np.degrees(np.arctan2(b,a));C=np.hypot(a,b)
    if E=='EyeL':  # green: a* well below skin
        c=W&~bg&(a<sa-14)&(L>12)
    else:          # amber: yellower than skin (hue up), saturated, not white
        sC=np.hypot(sa,sb);dE=np.sqrt((L-sL)**2+(a-sa)**2+(b-sb)**2)
        white=(L>72)&(C<16)
        # amber: non-skin, non-white, not lash-black px (dE from the local skin median > 15)
        c=W&~bg&~white&(dE>15)&(L>30)&(L<85)&~((C<22)&(L<42))
    c=ndi.binary_opening(c,iterations=1) if c.sum()>40 else c
    lb,n=ndi.label(c)
    if n==0:return c,dict(skin=[sL,sa,sb])
    sz=np.array(ndi.sum(c,lb,range(1,n+1)))
    if ref is not None:
        cm=ndi.center_of_mass(c,lb,range(1,n+1));sz=sz/(1+np.array([np.hypot(q[1]-ref[0],q[0]-ref[1]) for q in cm])/8)
    m=lb==(1+int(np.argmax(sz)))
    m=ndi.binary_fill_holes(ndi.binary_closing(m,iterations=2))&W
    return m,dict(skin=[round(sL,1),round(sa,1),round(sb,1)])
def dark_mask(I,win,thr=None):
    x0,y0,x1,y1=win;L,_,_=lab(I);W=np.zeros(L.shape,bool);W[y0:y1,x0:x1]=True
    return W&(L<(thr or 14))&~bgm(I)
def chamfer(tp,fp,trunc=6,sr=SR):
    # symmetric truncated chamfer: template->frame, plus frame px inside the shifted template hull (dilated 2) -> template
    DT=ndi.distance_transform_edt(~fp);DTt=ndi.distance_transform_edt(~tp);ys,xs=np.nonzero(tp);best=(1e9,0,0);S=np.zeros((2*sr+1,2*sr+1))
    hull=ndi.binary_dilation(tp,iterations=2)
    for dy in range(-sr,sr+1):
        for dx in range(-sr,sr+1):
            a=np.mean(np.minimum(DT[ys+dy,xs+dx],trunc))
            fy,fx=np.nonzero(fp[ys.min()+dy-2:ys.max()+dy+3,xs.min()+dx-2:xs.max()+dx+3]);fy=fy+ys.min()-2;fx=fx+xs.min()-2
            b=np.mean(np.minimum(DTt[fy,fx],trunc)) if len(fy) else trunc
            s=0.5*(a+b);S[dy+sr,dx+sr]=s
            if s<best[0]:best=(s,dx,dy)
    return best,S
def ncc(t,m,f,sr=SR):
    ys,xs=np.nonzero(m);tv=t[ys,xs];tv=(tv-tv.mean())/(tv.std()+1e-6);best=(-9,0,0)
    for dy in range(-sr,sr+1):
        for dx in range(-sr,sr+1):
            c=f[ys+dy,xs+dx];c=(c-c.mean())/(c.std()+1e-6);s=float((tv*c).mean())
            if s>best[0]:best=(s,dx,dy)
    return best
def subpix(S,dx,dy,sr=SR,minimize=True):
    # parabolic refinement of the score surface around the integer best
    j,i=dy+sr,dx+sr;f=lambda a,b,c:0.5*(a-c)/(a-2*b+c) if (a-2*b+c)!=0 else 0
    ox=f(S[j,i-1],S[j,i],S[j,i+1]) if 0<i<S.shape[1]-1 else 0;oy=f(S[j-1,i],S[j,i],S[j+1,i]) if 0<j<S.shape[0]-1 else 0
    return round(dx+ox,2),round(dy+oy,2)
def mole(I,ctr,win):
    x0,y0,x1,y1=win;L,_,_=lab(I);W=np.zeros(L.shape,bool);W[y0:y1,x0:x1]=True
    d=W&(L<35)&~bgm(I);lb,n=ndi.label(d);best=None
    for k in range(1,n+1):
        ys,xs=np.nonzero(lb==k)
        if not(4<=len(xs)<=40) or np.ptp(xs)>7 or np.ptp(ys)>7:continue
        dist=np.hypot(xs.mean()-ctr[0],ys.mean()-ctr[1])
        if best is None or dist<best[0]:best=(dist,float(xs.mean()),float(ys.mean()),len(xs))
    return best
import sys;sys.path.insert(0,Q+'scripts');import opening as OP
res={};vis={}
for v,E in EYES:
    hg=HGJ[v];dx0,dy0=hg['dx'],hg['dy']
    RG=onblue(Q+f'caps/hg_{v}_rest.png');LV=onblue(Q+f'caps/live_{v}_rest.png');F=warp_frame(v)
    ir=part(v,E,'iris',dx0,dy0)&part(v,E,'white',dx0,dy0);wh=part(v,E,'white',dx0,dy0)
    lash=part(v,E,'lash',dx0,dy0)|part(v,E,'lid_0',dx0,dy0)
    eye=ir|wh|lash;ys,xs=np.nonzero(eye);bx=(xs.min(),ys.min(),xs.max()+1,ys.max()+1)
    twin=(bx[0]-3,bx[1]-3,bx[2]+3,bx[3]+3);swin=(bx[0]-22,bx[1]-12,bx[2]+22,bx[3]+24)
    iy,ix=np.nonzero(ir);part_c=(ix.mean(),iy.mean())
    out={'frame':'f%03d'%AM[v]['frame'],'headgroup_offset':[dx0,dy0]}
    # sanity: rig hg render vs live render (must equal head offset)
    imRc,_=iris_mask(RG,E,twin,part_c);imR=ir.copy();imL0,_=iris_mask(LV,E,(twin[0]-dx0,twin[1]-dy0,twin[2]-dx0,twin[3]-dy0))
    cRc=ndi.center_of_mass(imRc);cL0=ndi.center_of_mass(imL0);cR=ndi.center_of_mass(imR)
    LLv,_,_=lab(LV);LRg,_,_=lab(RG);mk=np.zeros(LLv.shape,bool);mk[twin[1]-dy0:twin[3]-dy0,twin[0]-dx0:twin[2]-dx0]=True
    sn=ncc(LLv,mk,LRg,sr=12);out['sanity_hg_minus_live_eye_ncc']=[sn[1],sn[2],round(sn[0],4)]
    out['rig_iris_part_centroid']=[round(part_c[0],2),round(part_c[1],2)]
    out['rig_iris_colour_centroid']=[round(cRc[1],2),round(cRc[0],2)]
    out['rig_iris_colour_vs_part']=[round(cRc[1]-part_c[0],2),round(cRc[0]-part_c[1],2)]
    # M1 iris colour centroid in frame
    imF,sk=iris_mask(F,E,swin,part_c);cF=ndi.center_of_mass(imF)
    out['M1_iris_colour_centroid']=[round(cF[1]-cR[1],2),round(cF[0]-cR[0],2)]
    out['iris_px']={'rig':int(imR.sum()),'frame':int(imF.sum())}
    fy,fx=np.nonzero(imF);ry,rx=np.nonzero(imR)
    out['iris_bbox']={'rig':[int(rx.min()),int(ry.min()),int(rx.max()),int(ry.max())],'frame':[int(fx.min()),int(fy.min()),int(fx.max()),int(fy.max())]}
    dR=dark_mask(RG,twin)&ndi.binary_dilation(lash,iterations=1);up=np.zeros_like(dR);up[:int(part_c[1])+2]=True;tmpl=dR&up
    # M1 (opening-based): iris = non-skin, non-sclera px in the opening under the lash band; same rule on rig and frame
    ty,tx=np.nonzero(tmpl);lref=(tx.mean(),ty.mean())
    oR=OP.seg(RG,lab,bgm,swin,E,lref);oF=OP.seg(F,lab,bgm,swin,E,lref)
    cRo=ndi.center_of_mass(oR['iris']);cFo=ndi.center_of_mass(oF['iris'])
    out['M1o_iris_opening_centroid']=[round(cFo[1]-cRo[1],2),round(cFo[0]-cRo[0],2)]
    out['M1o_rig_vs_part']=[round(cRo[1]-part_c[0],2),round(cRo[0]-part_c[1],2)]
    out['M1o_px']={'rig':int(oR['iris'].sum()),'frame':int(oF['iris'].sum())}
    cRb=ndi.center_of_mass(oR['opening']);cFb=ndi.center_of_mass(oF['opening'])
    out['M1p_opening_centroid']=[round(cFb[1]-cRb[1],2),round(cFb[0]-cRb[0],2)]
    # lash band geometry (largest near-black band over the opening; same rule both sides)
    def bandgeo(bm):
        ys,xs=np.nonzero(bm);c=ndi.center_of_mass(bm)
        return dict(x0=int(xs.min()),x1=int(xs.max()),w=int(np.ptp(xs)+1),cx=round(c[1],2),cy=round(c[0],2),
                    y_at_x0=round(float(ys[xs<=xs.min()+1].mean()),1),y_at_x1=round(float(ys[xs>=xs.max()-1].mean()),1),
                    bottom_med=round(float(np.median([ys[xs==x].max() for x in np.unique(xs)])),1))
    gR=bandgeo(oR['band']);gF=bandgeo(oF['band'])
    out['lash_band']={'rig':gR,'frame':gF,'centroid_offset':[round(gF['cx']-gR['cx'],2),round(gF['cy']-gR['cy'],2)],
        'minx_corner_offset':[gF['x0']-gR['x0'],round(gF['y_at_x0']-gR['y_at_x0'],1)],'maxx_corner_offset':[gF['x1']-gR['x1'],round(gF['y_at_x1']-gR['y_at_x1'],1)],
        'width_ratio':round(gF['w']/gR['w'],3)}
    # M1b pupil: darkest 15% of iris pixels (centroid)
    Lr,_,_=lab(RG);Lf,_,_=lab(F)
    def pup(Lm,m):
        v_=Lm[m];t=np.percentile(v_,15);yy,xx=np.nonzero(m&(Lm<=t));return xx.mean(),yy.mean()
    pr=pup(Lr,oR['iris']);pf=pup(Lf,oF['iris']);out['M1b_pupil_dark_core']=[round(pf[0]-pr[0],2),round(pf[1]-pr[1],2)]
    # M2 lash / upper-lid line chamfer: rig template = dark px of lash+lid_0 above the iris centre row (+2)
    dR=dark_mask(RG,twin)&ndi.binary_dilation(lash,iterations=1);up=np.zeros_like(dR);up[:int(part_c[1])+2]=True
    tmpl=dR&up;dF=dark_mask(F,swin)
    (cs,mx,my),S=chamfer(tmpl,dF);out['M2_upper_lash_chamfer']=[mx,my,round(cs,2)];out['M2_subpx']=subpix(S,mx,my)
    # M2b whole dark eye outline (upper+lower lid, lash)
    (cs2,m2x,m2y),_=chamfer(dR,dF);out['M2b_all_lid_chamfer']=[m2x,m2y,round(cs2,2)]
    # M2c upper-lid line profile: per column, lowest dark row of the upper band (lid edge onto the opening), 1-D shift search
    def lidline(D,win,ref_y):
        x0,y0,x1,y1=win;pts={}
        for x in range(x0,x1):
            col=np.nonzero(D[y0:y1,x])[0]+y0
            if len(col):
                # take the first dark run from the top, its bottom row
                runs=np.split(col,np.nonzero(np.diff(col)>1)[0]+1);r=max(runs,key=len)
                pts[x]=float(r.max())
        return pts
    lr=lidline(tmpl,twin,0)
    # frame: per column the bottom of the thickest dark run within the search window
    lf=lidline(dF,swin,0);best=(1e9,0,0)
    for sx in range(-SR,SR+1):
        common=[x for x in lr if x+sx in lf and abs(lf[x+sx]-lr[x])<=SR]
        if len(common)<0.6*len(lr):continue
        d=np.array([lf[x+sx]-lr[x] for x in common]);sy=float(np.median(d));e=float(np.median(np.abs(d-sy)))+0.02*abs(sx)
        if e<best[0]:best=(e,sx,sy)
    out['M2c_lid_edge_profile']=[best[1],round(best[2],1),round(best[0],2)]
    # M3 masked luminance NCC of the eye (parts dilated 3 px, bg excluded)
    msk=ndi.binary_dilation(eye,iterations=3)&~bgm(RG)
    n3,ex,ey=ncc(Lr,msk,Lf);out['M3_eye_luma_ncc']=[ex,ey,round(n3,3)]
    # M4 nearest cheek mole (face landmark next to the eye)
    mwin=(bx[0]-15,bx[3]-2,bx[2]+15,bx[3]+30);mr=mole(RG,((bx[0]+bx[2])/2,bx[3]+8),mwin)
    if mr:
        mf=mole(F,(mr[1],mr[2]+8),(mwin[0]-20,mwin[1],mwin[2]+20,mwin[3]+20))
        out['M4_cheek_mole']=[round(mf[1]-mr[1],1),round(mf[2]-mr[2],1)] if mf else None
        out['mole_pos']={'rig':[round(mr[1],1),round(mr[2],1)],'frame':[round(mf[1],1),round(mf[2],1)] if mf else None}
    out['windows']={'template':[int(q) for q in twin],'search':[int(q) for q in swin]}
    res[f'{v}_{E}']=out;vis[f'{v}_{E}']=dict(RG=RG,F=F,imR=oR['iris'],imF=oF['iris'],oR=oR,oF=oF,imRc=imR,imFc=imF,tmpl=tmpl,dF=dF,box=swin,M2=(mx,my),M1=out['M1_iris_colour_centroid'])
    print(v,E,json.dumps({k:q for k,q in out.items() if k not in('windows',)}))
np.save(Q+'work/vis.npy',vis,allow_pickle=True)
json.dump(res,open(Q+'work/measure_raw.json','w'),indent=1)
