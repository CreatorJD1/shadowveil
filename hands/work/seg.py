import json, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage.graph import MCP_Geometric
from skimage.draw import line as skline, polygon as skpoly, disk as skdisk

SRC={v:f'/workspace/shadowveil/views/{v}/base.png' for v in ['apose','tpose','left','right','back']}
FINGERS=['thumb','index','middle','ring','pinky']
SEGN={'thumb':['metacarpal','proximal','distal']}
for f in FINGERS[1:]: SEGN[f]=['proximal','middle','distal']
_cache={}
def load(v):
    if v not in _cache: _cache[v]=np.array(Image.open(SRC[v]).convert('RGBA')).astype(np.float32)
    return _cache[v]

def colors(v, box):
    a=load(v); x0,y0,x1,y1=box
    p=a[y0:y1,x0:x1].reshape(-1,4); p=p[p[:,3]==255][:,:3]; L=p.mean(1)
    sk=p[(L>115)&(L<140)]; S=np.median(sk,0)
    ln=p[L<45]; Lc=np.median(ln,0)
    return S,Lc

def lum(c): return c[...,0]*.299+c[...,1]*.587+c[...,2]*.114

def flatten(rgb,S,Lc,thr=0.3):
    lS=lum(S); lL=lum(Lc)
    t=np.clip((lS-lum(rgb))/(lS-lL),0,1)
    t=np.where(t<thr,0,np.clip((t-thr)/(1-thr)*1.0,0,1))   # remap so faint shading ->0, keep lines
    out=S[None,None,:]*(1-t[...,None])+Lc[None,None,:]*t[...,None]
    return out,t

def seg_len_proj(p,a,b):
    d=b-a; L2=(d**2).sum(); 
    return d, L2

def rasterize_chain(pts,shape):
    m=np.zeros(shape,bool)
    for i in range(len(pts)-1):
        r,c=skline(int(round(pts[i][1])),int(round(pts[i][0])),int(round(pts[i+1][1])),int(round(pts[i+1][0])))
        ok=(r>=0)&(r<shape[0])&(c>=0)&(c<shape[1]); m[r[ok],c[ok]]=True
    return m

def expand_chain(ch, ratios=(0.47,0.29,0.24)):
    # ch: [base, tip] or [base,j1,j2,tip]
    ch=[np.array(p,float) for p in ch]
    if len(ch)==4: return ch
    a,b=ch; r=np.cumsum((0,)+tuple(ratios))
    return [a+(b-a)*t for t in r]

def segment_hand(v,H):
    a=load(v); Hh,W=a.shape[:2]
    x0,y0,x1,y1=H['box']
    sub=a[y0:y1,x0:x1]
    alpha=sub[...,3]
    from handmask import hand_mask
    mask=hand_mask(a,H)[y0:y1,x0:x1]
    # keep component(s) connected to chains
    Lum=lum(sub[...,:3])
    line=Lum<H.get('lineL',100)
    flat=None
    cost=np.where(line,H.get('linecost',12.0),1.0)
    cost=np.where(mask,cost,np.inf)
    chains={f:expand_chain(H['fingers'][f]) for f in H['fingers']}
    chains_l={f:[p-np.array([x0,y0]) for p in ch] for f,ch in chains.items()}
    dists={}
    seeds={}
    for f,ch in chains_l.items():
        sm=rasterize_chain(ch,mask.shape)&mask
        seeds[f]=sm
    ps=[np.array(p,float)-np.array([x0,y0]) for p in H['palm_seed']]
    seeds['palm']=rasterize_chain(ps,mask.shape)&mask
    names=list(seeds)
    D=[]
    for n in names:
        m=MCP_Geometric(np.where(np.isfinite(cost),cost,1e9))
        st=np.argwhere(seeds[n])
        if len(st)==0: D.append(np.full(mask.shape,np.inf)); continue
        d,_=m.find_costs(st)
        d[~mask]=np.inf; D.append(d)
    D=np.stack(D)
    lab=np.argmin(D,0)
    yy,xx=np.mgrid[0:mask.shape[0],0:mask.shape[1]]
    P=np.stack([xx,yy],-1).astype(float)
    labels=np.full(mask.shape,'',object)
    labels[mask]='palm'
    for i,n in enumerate(names):
        if n=='palm': continue
        ch=chains_l[n]
        sel=mask&(lab==i)
        # joints: ch[0]=base(MCP or CMC), ch[1], ch[2]; cut plane normals
        segidx=np.zeros(mask.shape,int)
        for j in range(3):
            if j==0: d=ch[1]-ch[0]
            else:
                d1=(ch[j]-ch[j-1]); d2=(ch[j+1]-ch[j]); d=d1/np.linalg.norm(d1)+d2/np.linalg.norm(d2)
            d=d/np.linalg.norm(d)
            past=((P-ch[j])@d)>0
            segidx+=past
        if n=='thumb':
            dmin=np.full(mask.shape,1e9); sd=np.zeros(mask.shape)
            pc=np.mean(ps,0)
            for j in range(3):
                a_,b_=ch[j],ch[j+1]; d_=b_-a_; tt=np.clip(((P-a_)@d_)/(d_@d_),0,1)
                dj=np.linalg.norm(P-(a_+tt[...,None]*d_),axis=-1)
                cr=d_[0]*(P[...,1]-a_[1])-d_[1]*(P[...,0]-a_[0])
                crp=d_[0]*(pc[1]-a_[1])-d_[1]*(pc[0]-a_[0])
                upd=dj<dmin; dmin=np.where(upd,dj,dmin); sd=np.where(upd,np.sign(cr)*np.sign(crp),sd)
            tw=H.get('thumb_w',9)
            lim=np.where(segidx==1,tw,H.get('thumb_w2',tw*1.8))
            sel=sel&~((dmin>lim)&(sd>0))
        for k,sn in enumerate(SEGN[n]):
            labels[sel&(segidx==k+1)]=f'{n}_{sn}'
        # before base -> palm (already)
    # stray palm islands (not connected to main palm) -> nearest finger label
    pm=labels=='palm'
    lab_,n_=ndi.label(pm)
    if n_>1:
        sizes=ndi.sum(pm,lab_,range(1,n_+1)); keep=1+int(np.argmax(sizes))
        stray=pm&(lab_!=keep)
        other=mask&~pm
        _,(iy,ix)=ndi.distance_transform_edt(~other,return_indices=True)
        labels[stray]=labels[iy[stray],ix[stray]]
    return dict(mask=mask,labels=labels,flat=flat,alpha=alpha,chains=chains,box=H['box'],names=names,line=line)

PAL={'palm':(200,200,200)}
import colorsys
for i,f in enumerate(FINGERS):
    for k,s in enumerate(SEGN[f]):
        h=i/5.0; rgb=colorsys.hsv_to_rgb(h,[1,.7,.45][k],[.9,1,.8][k])
        PAL[f'{f}_{s}']=tuple(int(c*255) for c in rgb)

def overlay(v,H,R,s=5,out='ov.png'):
    x0,y0,x1,y1=H['box']
    a=load(v)[y0:y1,x0:x1]
    base=a[...,:3]*a[...,3:]/255+255*(1-a[...,3:]/255)
    col=base.copy()
    for k,c in PAL.items():
        m=R['labels']==k
        col[m]=0.45*base[m]+0.55*np.array(c)
    col[R['line']&R['mask']]=col[R['line']&R['mask']]*0.4
    im=Image.fromarray(col.astype(np.uint8)).resize(((x1-x0)*s,(y1-y0)*s),Image.NEAREST)
    d=ImageDraw.Draw(im)
    for x in range((x0//10+1)*10,x1,10):
        d.line([((x-x0)*s,0),((x-x0)*s,6)],fill=(255,0,0)); d.text(((x-x0)*s+1,6),str(x%100),fill=(255,0,0))
    for y in range((y0//10+1)*10,y1,10):
        d.line([(0,(y-y0)*s),(6,(y-y0)*s)],fill=(255,0,0)); d.text((7,(y-y0)*s-5),str(y%100),fill=(255,0,0))
    for f,ch in R['chains'].items():
        pts=[((p[0]-x0+.5)*s,(p[1]-y0+.5)*s) for p in ch]
        d.line(pts,fill=(255,255,255),width=1)
        for p in pts: d.ellipse([p[0]-3,p[1]-3,p[0]+3,p[1]+3],outline=(255,0,255),width=2)
    im.save(out)
