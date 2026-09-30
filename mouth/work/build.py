from PIL import Image
import numpy as np, json, os
from scipy import ndimage as ndi
OUT='/workspace/shadowveil/mouth'
SRC='front.png'
base=np.array(Image.open(SRC).convert('RGBA')).astype(np.float64)
H,W=base.shape[:2]
AX,AY=681,285                 # anchor: lip seam centre in A-pose canvas px
CW,CH=112,72; OX,OY=AX-56,AY-26   # local drawing box (pasted into full canvas)
SS=8
def hx(s): return np.array([int(s[i:i+2],16) for i in (0,2,4)],float)
PAL=dict(skin=hx('B98357'),line=hx('210800'),upper=hx('533117'),lower=hx('633C22'),
         hl=hx('E8C2AC'),inner=hx('2E0D0B'),teeth=hx('F3ECE2'),tongue=hx('8E4440'))
BLUE=np.array([0,0,255.])
# local 8x grid coords, in base px relative to anchor
ys,xs=np.mgrid[0:CH*SS,0:CW*SS]
X=(xs+0.5)/SS-56; Y=(ys+0.5)/SS-26

# ---------- underlay: base lip mask dilated 2px, feathered ----------
m=np.load('mask.npy'); full=np.zeros((H,W),bool); full[266:310,640:722]=m
und=ndi.binary_dilation(full,iterations=2)
und_loc=und[OY:OY+CH,OX:OX+CW]
und_hi=np.kron(und_loc,np.ones((SS,SS)))>0
und3=np.kron(ndi.binary_dilation(full,iterations=3)[OY:OY+CH,OX:OX+CW],np.ones((SS,SS)))>0
und_soft=np.maximum(ndi.gaussian_filter(und3.astype(float),SS*0.6),und_hi)   # opaque over dilated lips, ~1px feathered rim

def paint(layers):
    """layers: list of (color, mask8x). returns local RGBA float 1x (premult downsample)"""
    rgb=np.zeros((CH*SS,CW*SS,3)); a=np.zeros((CH*SS,CW*SS))
    # underlay first (soft alpha)
    rgb[:]=PAL['skin']; a[:]=np.clip(und_soft*1.0,0,1)
    for col,mk in layers:
        rgb[mk]=col; a[mk]=1.0
    pre=rgb*a[...,None]
    pre=pre.reshape(CH,SS,CW,SS,3).mean((1,3)); al=a.reshape(CH,SS,CW,SS).mean((1,3))
    out=np.zeros((CH,CW,4)); nz=al>1e-6
    out[nz,:3]=pre[nz]/al[nz,None]; out[...,3]=al
    return out

# ---------- REST: from her own pixels, cleaned to flat palette ----------
def rest_layers():
    reg=base[OY:OY+CH,OX:OX+CW,:3]
    up=np.array(Image.fromarray(reg.astype(np.uint8)).resize((CW*SS,CH*SS),Image.BICUBIC)).astype(float)
    names=['skin','line','upper','lower','hl']
    d=np.stack([((up-PAL[n])**2).sum(-1) for n in names],-1)
    cls=np.argmin(d,-1)
    lip=np.kron(ndi.binary_dilation(full[OY:OY+CH,OX:OX+CW],iterations=1),np.ones((SS,SS)))>0
    oh=np.stack([ndi.gaussian_filter((cls==i).astype(float),SS*0.3) for i in range(5)],-1)
    cls=np.argmax(oh,-1); cls[~lip]=0
    filled=ndi.binary_fill_holes(cls>0)
    cls[filled&(cls==0)]=3
    hl_ok=np.kron(np.pad(np.ones((1,1)),0),np.ones((1,1)))
    # highlight only inside lower-lip body
    cls[(cls==4)&~ndi.binary_erosion(filled,iterations=SS)]=3
    return [(PAL[names[i]],cls==i) for i in (2,3,1,4)]

# ---------- parametric mouth ----------
def mouth(Wi,Wo,cy,Hup,bow,Su,Sl,Lo,pu=0.8,pl=0.8,po=0.8,pho=0.7,cx=-0.5,
          tc=1.4,te=2.2,tlow=0.0,teeth_up=0,teeth_lo=0,tongue=None,flick=(4,1.6,1.2),
          hl=(0,0,3.5,0.8),lowline=0.0):
    x=X-cx; ui=np.clip(x/Wi,-1,1); uo=np.clip(x/Wo,-1,1)
    g=(1-uo**2).clip(0)**pho*(1-bow*np.exp(-(uo/0.16)**2))
    y_uo=cy-Hup*g
    y_ui=cy+Su*(1-ui**2).clip(0)**pu
    y_li=cy+Sl*(1-ui**2).clip(0)**pl
    y_lo=cy+Lo*(1-uo**2).clip(0)**po
    inW=np.abs(x)<Wo; inWi=np.abs(x)<Wi
    outer=inW&(Y>=y_uo)&(Y<=y_lo)
    opening=inWi&(Y>y_ui)&(Y<y_li)&(Sl>Su)
    seam=np.where(inWi,y_ui,cy)
    upper=outer&~opening&(Y<seam)
    lower=outer&~opening&(Y>=seam)
    L=[(PAL['upper'],upper),(PAL['lower'],lower)]
    if Sl>Su:
        L.append((PAL['inner'],opening))
        if tongue:
            tx,ty,rx,ry=tongue
            L.append((PAL['tongue'],opening&(((x-tx)/rx)**2+((Y-ty)/ry)**2<1)))
        if teeth_up: L.append((PAL['teeth'],opening&(Y<y_ui+teeth_up)&(np.abs(x)<Wi*0.82)))
        if teeth_lo: L.append((PAL['teeth'],opening&(Y>y_li-teeth_lo)&(np.abs(x)<Wi*0.7)))
    # line band just below upper lip (seam / upper inner edge), thicker toward corners
    t=(tc+(te-tc)*np.abs(ui)**2)
    d_up=ndi.distance_transform_edt(~upper)/SS
    line=(~upper)&(d_up<t)&inWi&(outer|opening)
    if lowline>0:
        d_lo=ndi.distance_transform_edt(~lower)/SS
        line|=opening&(d_lo<lowline)
    # corner flicks: tapered stroke, inward along seam to slightly outward/up
    if flick:
        ln,out,up=flick
        for s in (-1,1):
            p0=np.array([cx+s*(Wi-ln),cy+Su*(1-((Wi-ln)/Wi)**2)**pu if Sl<=Su else cy+0.3])
            p1=np.array([cx+s*(Wo+out),cy-up])
            v=p1-p0; w=np.stack([X-p0[0],Y-p0[1]],-1)
            tt=np.clip((w@v)/(v@v),0,1)
            dist=np.hypot(X-(p0[0]+tt*v[0]),Y-(p0[1]+tt*v[1]))
            r=1.15*(1-tt)+0.55*tt
            line|=dist<r
    L.append((PAL['line'],line))
    if hl:
        hx_,hy,rx,ry=hl
        L.append((PAL['hl'],lower&(((x-hx_)/rx)**2+((Y-hy)/ry)**2<1)))
    return L

SHAPES={
 'rest':None,
 'M':    dict(Wi=20.5,Wo=20.5,cy=-1.0,Hup=3.0,bow=0.35,Su=1.6,Sl=1.6,Lo=8.0,pu=1.0,po=0.9,
              tc=1.8,te=2.3,flick=(4,1.3,0.6),hl=(0,5.2,3.0,0.7)),
 'smile':dict(Wi=25.5,Wo=25.5,cy=-4.0,Hup=3.8,bow=0.45,Su=4.4,Sl=4.4,Lo=11.5,pu=1.1,po=1.0,
              tc=1.4,te=2.1,flick=(5,1.6,2.2),hl=(0,8.6,3.5,0.75)),
 'OH':   dict(Wi=7.5,Wo=10.5,cy=2.0,Hup=11.0,bow=0.12,Su=-6.0,Sl=9.5,Lo=15.5,pu=0.5,pl=0.5,po=0.55,pho=0.5,
              tc=1.3,te=1.3,flick=None,tongue=(0,10.5,6,3.5),hl=(0,13.6,2.2,0.6),lowline=0.7),
 'AA':   dict(Wi=19.0,Wo=21.0,cy=0.5,Hup=6.5,bow=0.3,Su=-3.2,Sl=15.5,Lo=21.5,pu=0.55,pl=0.6,po=0.6,
              tc=1.4,te=1.8,flick=(2,1.2,0.6),teeth_up=2.6,tongue=(0,17.5,11,5),hl=(0,18.8,3.2,0.7),lowline=0.7),
 'EE':   dict(Wi=24.0,Wo=25.0,cy=-2.5,Hup=3.6,bow=0.35,Su=1.2,Sl=7.2,Lo=13.5,pu=0.8,pl=0.75,po=0.85,
              tc=1.3,te=1.8,flick=(3,1.4,1.6),teeth_up=3.6,teeth_lo=1.4,hl=(0,10.5,3.2,0.7),lowline=0.6),
}

def key(chroma):
    """chroma key #0000FF -> RGBA with alpha by projection onto nearest core fg colour (despilled)."""
    c=chroma.astype(float)
    dist=np.linalg.norm(c-BLUE,axis=-1)
    fg=dist>6
    spill=c[...,2]-np.maximum(c[...,0],c[...,1])
    cand=ndi.binary_erosion(fg,iterations=1)&(spill<-8)
    core=cand.copy()
    for y,x in zip(*np.nonzero(cand)):
        # reject a candidate if it is just a neighbour colour blended toward blue (partial alpha)
        n=c[max(0,y-2):y+3,max(0,x-2):x+3].reshape(-1,3); n=n[cand[max(0,y-2):y+3,max(0,x-2):x+3].reshape(-1)]
        d=n-BLUE; aa=((c[y,x]-BLUE)*d).sum(1)/((d**2).sum(1)+1e-9)
        res=np.linalg.norm(c[y,x]-(aa[:,None]*n+(1-aa[:,None])*BLUE),axis=1)
        if np.any((aa<0.97)&(res<4)): core[y,x]=False
    a=np.zeros(c.shape[:2]); F=np.zeros_like(c); a[core]=1; F[core]=c[core]
    corec=np.where(core[...,None],c,np.nan)
    for y,x in zip(*np.nonzero(fg&~core)):
        R=4; win=corec[max(0,y-R):y+R+1,max(0,x-R):x+R+1].reshape(-1,3)
        win=win[~np.isnan(win[:,0])]
        if len(win)==0:
            idx=ndi.distance_transform_edt(~core,return_distances=False,return_indices=True); win=c[idx[0][y,x],idx[1][y,x]][None]
        win=np.unique(np.round(win),axis=0)
        d=win-BLUE; aa=np.clip(((c[y,x]-BLUE)*d).sum(1)/((d**2).sum(1)+1e-9),0,1)
        res=np.linalg.norm(c[y,x]-(aa[:,None]*win+(1-aa[:,None])*BLUE),axis=1)
        j=np.argmin(res); a[y,x]=aa[j]
        # unmix with chosen alpha, then despill (clamp blue to the reference colour's blue)
        F[y,x]=win[j]   # despill: edge colour = matched flat fg colour (no blue carried over)
    out=np.zeros(c.shape[:2]+(4,)); out[...,:3]=F; out[...,3]=a*255
    out[core,:3]=c[core]
    return np.round(out).clip(0,255).astype(np.uint8)

os.makedirs(OUT,exist_ok=True)
truth={}
for name,p in SHAPES.items():
    loc=paint(rest_layers() if p is None else mouth(**p))
    fullrgba=np.zeros((H,W,4)); fullrgba[OY:OY+CH,OX:OX+CW]=loc
    truth[name]=fullrgba
    al=fullrgba[...,3:]
    chroma=np.round(fullrgba[...,:3]*al+BLUE*(1-al)).clip(0,255).astype(np.uint8)
    Image.fromarray(chroma,'RGB').save(f'{OUT}/{name}_chroma.png')
    k=key(chroma)
    Image.fromarray(k,'RGBA').save(f'{OUT}/{name}.png')
    ea=np.abs(k[...,3]/255-al[...,0]).max()
    m2=k[...,3]>8
    fr=(k[m2,2].astype(int)-np.maximum(k[m2,0],k[m2,1])).max()
    ys_,xs_=np.nonzero(k[...,3]>0)
    print(name,'maxAlphaErr %.3f'%ea,'max(B-maxRG) on visible px',fr,'bbox',xs_.min(),ys_.min(),xs_.max(),ys_.max())

# diagnostics
for name in SHAPES:
    k=np.array(Image.open(f'{OUT}/{name}.png')).astype(float)
    e=np.abs(k[...,3]/255-truth[name][...,3]); y,x=np.unravel_index(e.argmax(),e.shape)
    print(name,'alpha err mean(on part) %.4f'%e[truth[name][...,3]>0].mean(),'worst at',x,y,'truth a %.2f'%truth[name][y,x,3],'key a %.2f'%(k[y,x,3]/255))
