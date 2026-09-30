"""Anger mouth (front views): pixels CUT from the approved Clean-room anger art (public/puppet/emotions/anger.png, the file
faces.json points to), placed by uniform scale + translate (rotation 0) onto our rest mouth, over the same skin underlay
the other open shapes use. No painting: every lip pixel is an area-resampled source pixel. Writes only anger.png /
anger_chroma.png (+ rig entries via register.py). Never touches base.png or the nine existing shapes."""
import json,sys,os,hashlib; import numpy as np; from PIL import Image; from scipy import ndimage as ndi
sys.path.insert(0,'/workspace/shadowveil/mouth/work'); from lipmask import load, lip_mask
from measure import src_mask, SRC
ROOT='/workspace/shadowveil'; SS=8; BLUE=np.array([0,0,255.])
GUESS={'apose':(681,289),'tpose':(684,281)}
SRC_CX,SRC_SEAM=371.0,436.5          # source mouth, pixel-edge coords: bbox cols 323..418 -> centre 371.0; seam row 436 (corner rows 436.5, dark seam band 430-439) -> 436.5
SRC_W=96.0
def build(view,out_dir=None,live=True,fit=None):
    """fit=None: live front build (uniform scale = rest width / source width). fit=dict(sx,sy,cx,seam,D): PROPOSAL (non-uniform)."""
    b=load(view); H,W=b.shape[:2]
    if fit is None: M,D,_=lip_mask(b,*GUESS[view])
    else: D=fit['D']
    rig=json.load(open(f'{ROOT}/views/{view}/mouth/rig.json')); skin=np.array([int(rig['colors']['skin'][i:i+2],16) for i in (1,3,5)],float)
    yd,xd=np.nonzero(D); x0,x1=xd.min(),xd.max()+1           # rest drawn lips span [x0,x1) in px edges
    Lb=b[...,:3]@[.299,.587,.114]; cx=(x0+x1)/2.0
    cols=range(int(cx)-2,int(cx)+3); seam=np.mean([yd.min()+np.argmin(Lb[yd.min():yd.max()+1,x]) for x in cols])+0.5   # row centre
    s=(x1-x0)/SRC_W; rot=0.0; sxx=syy=s
    if fit is not None: sxx,syy,cx,seam=fit['sx'],fit['sy'],fit['cx'],fit['seam']
    T=dict(scale=s if fit is None else None,scaleX=sxx,scaleY=syy,rotationDeg=rot,srcCentre=[SRC_CX,SRC_SEAM],dstCentre=[cx,seam],
           note='dst = dstCentre + scale*(src - srcCentre) in pixel-edge coordinates (src px i spans [i,i+1))')
    A,Ls,core=src_mask()
    cut=ndi.binary_dilation(core,iterations=1)                 # lips + their 1 px anti-aliased rim (all source pixels)
    # local 8x box
    AX,AY=int(round(cx)),int(round(seam)); CW,CH=120,80; OX,OY=AX-CW//2,AY-30
    ys8,xs8=np.mgrid[0:CH*SS,0:CW*SS]; X=OX+(xs8+0.5)/SS; Y=OY+(ys8+0.5)/SS
    sx=SRC_CX+(X-cx)/sxx; sy=SRC_SEAM+(Y-seam)/syy                   # inverse map (rotation 0)
    ix=np.floor(sx).astype(int); iy=np.floor(sy).astype(int)
    ok=(ix>=0)&(iy>=0)&(ix<A.shape[1])&(iy<A.shape[0]); ix=ix.clip(0,A.shape[1]-1); iy=iy.clip(0,A.shape[0]-1)
    lip8=ok&cut[iy,ix]; col8=A[iy,ix,:3]
    kr=lambda m: np.kron(m,np.ones((SS,SS)))>0
    Dl=D[OY:OY+CH,OX:OX+CW]
    lipcov=lip8.reshape(CH,SS,CW,SS).mean((1,3))
    need=Dl|(lipcov>0)                                           # rest lips + anger lips
    und_hard=kr(ndi.binary_dilation(need,iterations=2))
    und_soft=np.maximum(ndi.gaussian_filter(kr(ndi.binary_dilation(need,iterations=3)).astype(float),SS*0.6),und_hard)
    rgb8=np.zeros((CH*SS,CW*SS,3)); rgb8[:]=skin; a8=und_soft.copy()
    rgb8[lip8]=col8[lip8]; a8[lip8]=1.0
    if fit is not None:   # profile proposal: nothing outside her opaque silhouette (like build5 profiles)
        sil=kr((b[OY:OY+CH,OX:OX+CW,3]==255)|Dl); a8*=sil
    pre=(rgb8*a8[...,None]).reshape(CH,SS,CW,SS,3).mean((1,3)); al=a8.reshape(CH,SS,CW,SS).mean((1,3))
    loc=np.zeros((CH,CW,4)); nz=al>1e-6; loc[nz,:3]=pre[nz]/al[nz,None]; loc[...,3]=al
    full=np.zeros((H,W,4)); full[OY:OY+CH,OX:OX+CW]=loc
    fix=D&(full[...,3]>0.5)&(full[...,3]<1); full[...,3][fix]=1.0  # same rule as build5: drawn-lip px fully covered
    # chroma preview -> key (feather pixels are skin over blue: unmix against skin; everything else opaque)
    alf=full[...,3:]; chroma=np.round(full[...,:3]*alf+BLUE*(1-alf)).clip(0,255).astype(np.uint8)
    c=chroma.astype(float); isb=np.linalg.norm(c-BLUE,axis=-1)<3
    d=skin-BLUE; a=((c-BLUE)@d)/(d@d); res=np.linalg.norm(c-(BLUE+a[...,None]*d),axis=-1)
    rim=~isb&(res<4)&(a<0.97)&ndi.binary_dilation(isb,iterations=4)
    k=np.zeros(c.shape[:2]+(4,)); k[~isb,:3]=c[~isb]; k[~isb,3]=255
    k[rim,:3]=skin; k[rim,3]=np.round(a[rim].clip(0,1)*255)
    k=np.round(k).clip(0,255).astype(np.uint8)
    mx=np.maximum(k[...,0],k[...,1]); k[...,2]=np.minimum(k[...,2],mx); k[k[...,3]==0,:3]=0
    err=np.abs(k[...,3]/255-alf[...,0])
    rep=dict(view=view,transform=T,restDrawnBBox=[int(x0),int(yd.min()),int(x1-1),int(yd.max())],restSeamY=float(seam),
             maxAlphaErr=float(err.max()),uncoveredRestLipPx=int((D&(k[...,3]<255)).sum()),restLipPx=int(D.sum()))
    od=out_dir or f'{ROOT}/views/{view}/mouth'
    Image.fromarray(k,'RGBA').save(f'{od}/anger.png')
    pd=f'{ROOT}/mouth/{view}' if live else od
    Image.fromarray(chroma,'RGB').save(f'{pd}/anger_chroma.png')
    return rep,k
if __name__=='__main__':
    reps={}
    for v in sys.argv[1:] or ['apose','tpose']:
        h=[hashlib.sha256(open(f'{ROOT}/views/{v}/{p}','rb').read()).hexdigest() for p in ('base.png','mouth/rest.png')]
        rep,k=build(v); reps[v]=rep
        assert h==[hashlib.sha256(open(f'{ROOT}/views/{v}/{p}','rb').read()).hexdigest() for p in ('base.png','mouth/rest.png')]
        print(json.dumps(rep))
    json.dump(reps,open('build_report.json','w'),indent=1)
