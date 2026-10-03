import numpy as np, json, sys, itertools
from scipy.ndimage import binary_dilation, distance_transform_edt
from skimage.morphology import skeletonize
Q='/workspace/shadowveil/rig/work/mouthfix/qa/'
LINE_T=0.13   # luminance threshold for the dark outline/seam (#220C00 L=0.06; lips L>=0.19, skin ~0.55)
def lum(X): return (X[...,:3]@np.array([0.299,0.587,0.114]))/255
def blue_px(X,thr=20): return int(np.sum((X[...,2]>np.maximum(X[...,0],X[...,1])+thr)&(X[...,3]>0)))
class Run:
  def __init__(s,view):
    s.view=view;s.d=Q+f'run_{view}/';s.m=json.load(open(s.d+'meta.json'));b=s.m['box'];s.h,s.w=b[3]-b[1],b[2]-b[0]
    s.ref={k[0:]:s.ld('ref_'+k) for k in s.m['refs']}
  def ld(s,n): return np.frombuffer(open(s.d+f'crops/{n}.rgba','rb').read(),np.uint8).reshape(s.h,s.w,4).astype(np.int32)
def ndiff(a,b): return int(np.sum(np.any(a!=b,-1)&~((a[...,3]==0)&(b[...,3]==0))))
def sharp(X,mask):
  L=lum(X); gy,gx=np.gradient(L); return float(np.mean(np.hypot(gx,gy)[mask]))
def line_width(X,mouthmask):
  m=(lum(X)<LINE_T)&(X[...,3]>0)&mouthmask
  if m.sum()<5: return None
  sk=skeletonize(m); dt=distance_transform_edt(m)
  w=2*dt[sk]-1 if sk.any() else np.array([0.])
  return float(np.median(w)), float(np.percentile(w,90)), int(m.sum())
def comp(base,top,a):  # top RGBA over base RGBA (0..255), opacity a
  ta=top[...,3:]/255*a; rgb=top[...,:3]*ta+base[...,:3]*(1-ta); return rgb
def fit_fade(F,base,P,C):
  """F ~ C(aIn) over P(aOut) over base. grid search"""
  best=(1e9,0,0);Fr=F[...,:3].astype(float)
  for ao in np.linspace(0,1,51):
    PB=np.concatenate([comp(base,P,ao),base[...,3:]],-1)
    for ai in np.linspace(0,1,51):
      e=np.mean((comp(PB,C,ai)-Fr)**2)
      if e<best[0]: best=(e,ai,ao)
  return dict(aIn=round(best[1],2),aOut=round(best[2],2),rmse=round(best[0]**.5,2))
def doubled(F,P,C,mouthmask):
  """two lip lines visible: outgoing-only line px and incoming-only line px both shown at >=25% contrast"""
  Lp,Lc,Lf=lum(P),lum(C),lum(F)
  lp=(Lp<0.09)&mouthmask; lc=(Lc<0.09)&mouthmask
  po=lp&~binary_dilation(lc,iterations=1); co=lc&~binary_dilation(lp,iterations=1)
  def vis(mask,full,other):  # fraction of the line's contrast present in F
    if mask.sum()<5: return None,0
    c=(other[mask]-Lf[mask])/np.maximum(other[mask]-full[mask],1e-3); return float(np.clip(np.median(c),0,1.5)),int(mask.sum())
  vp,np_=vis(po,Lp,Lc); vc,nc=vis(co,Lc,Lp)
  # px where the frame shows a line pixel (L<T) on outgoing-only AND incoming-only locations
  vis_po=int(np.sum((Lf<(Lc+Lp)/2)&po)); vis_co=int(np.sum((Lf<(Lc+Lp)/2)&co))
  dbl=(vp is not None and vc is not None and vp>=0.25 and vc>=0.25 and np_>=10 and nc>=10)
  return dict(out_only_px=np_,out_vis=None if vp is None else round(vp,2),in_only_px=nc,in_vis=None if vc is None else round(vc,2),out_dark_px=vis_po,in_dark_px=vis_co,doubled=bool(dbl))
from scipy.ndimage import maximum_filter, shift as nshift
L_LINE=0.065
def ink_width(X,refline,skel_len):
  """blur-invariant effective line width: integrated darkness deficit (vs local 7x7 max luminance) over the ref line mask dilated 2 px, / ref skeleton length"""
  L=lum(X); bg=maximum_filter(L,size=7)
  cov=np.clip((bg-L)/np.maximum(bg-L_LINE,0.05),0,1)
  m=binary_dilation(refline,iterations=2)
  return float(cov[m].sum()/max(skel_len,1))
def ref_line(X,mm,T=0.09):
  m=(lum(X)<T)&mm; sk=skeletonize(m); return m,int(sk.sum())
from scipy.ndimage import grey_closing
def ink_width2(X,refline,skel_len,size=7):
  L=lum(X); bg=grey_closing(L,size=(size,size))
  cov=np.clip((bg-L)/np.maximum(bg-L_LINE,0.04),0,1)
  m=binary_dilation(refline,iterations=2)
  return float(cov[m].sum()/max(skel_len,1))
def fwhm(X,refline,win=4):
  """median vertical FWHM (px, linear interp) of the dark line across columns where the ref line exists; local bg = max of the +-win profile"""
  L=lum(X); H=L.shape[0]; out=[]
  ys,xs=np.nonzero(refline)
  for x in np.unique(xs):
    for y0 in ys[xs==x]:
      if y0-win<0 or y0+win+1>H: continue
      p=L[y0-win:y0+win+1,x]; c=p.max()-p; k=np.argmax(c); cm=c[k]
      if cm<0.05: continue
      h=cm/2; i=k
      while i>0 and c[i-1]>=h: i-=1
      j=k
      while j<len(c)-1 and c[j+1]>=h: j+=1
      l=i-(c[i]-h)/(c[i]-c[i-1]+1e-9) if i>0 else i-0.5
      r=j+(c[j]-h)/(c[j]-c[j+1]+1e-9) if j<len(c)-1 else j+0.5
      out.append(min(r-l,2*win))
  return float(np.median(out)) if out else None
def bin_width(X,mm,T=0.09):
  m=(lum(X)<T)&mm
  if m.sum()<3: return None
  sk=skeletonize(m);dt=distance_transform_edt(m);wv=2*dt[sk]-1
  return float(np.median(wv)),float(np.percentile(wv,90)),int(m.sum())

def blue_spill(X,base,mm):
  """bluish px inside the mouth mask (dilated 3 px) that are not bluish in base.png: B>max(R,G)+20 (any), and key-like B>100 & B>max(R,G)+60"""
  def bl(Y,t): return (Y[...,2]>np.maximum(Y[...,0],Y[...,1])+t)&(Y[...,3]>0)
  return [int(np.sum(bl(X,20)&~bl(base,20)&mm)),int(np.sum((X[...,2]>100)&bl(X,60)&mm))]
def edges(X):
  L=lum(X); gy,gx=np.gradient(L); return np.hypot(gx,gy)
def doubled2(F,P,C,mm,thr=0.06,vis_t=0.2,min_px=15):
  """two lip contours visible at once. Contour px = |grad L| > thr in the pure outgoing (P) / incoming (C) composite.
  P-only contours (not within 1 px of a C contour) and C-only contours; visibility = median(|grad F| / |grad pure|) on each set.
  doubled = both sets >= min_px and both visibilities >= vis_t (i.e. >=20% of the line's full contrast, ~>=0.03-0.1 luminance step)."""
  eP,eC,eF=edges(P),edges(C),edges(F)
  mP=(eP>thr)&mm; mC=(eC>thr)&mm
  po=mP&~binary_dilation(mC,iterations=1); co=mC&~binary_dilation(mP,iterations=1)
  vp=float(np.median(eF[po]/eP[po])) if po.sum() else None; vc=float(np.median(eF[co]/eC[co])) if co.sum() else None
  d=bool(po.sum()>=min_px and co.sum()>=min_px and vp>=vis_t and vc>=vis_t)
  return dict(out_px=int(po.sum()),out_vis=None if vp is None else round(vp,2),in_px=int(co.sum()),in_vis=None if vc is None else round(vc,2),doubled=d)
