import numpy as np,sys
from PIL import Image
from scipy import ndimage as ndi
S=np.array([185,128,86.]);Lc=np.array([17,12,30.])
def ink(a,S=S,Lc=Lc): return np.clip(((S-a[...,:3])@(S-Lc))/((S-Lc)@(S-Lc)),0,1)*a[...,3]/255
def width(p,S_=None,L_=None):
  S0=S if S_ is None else np.asarray(S_,float); L0=Lc if L_ is None else np.asarray(L_,float)
  a=np.array(Image.open(p).convert('RGBA')).astype(float); m=a[...,3]>128
  e=m&~ndi.binary_erosion(m); t=ink(a,S0,L0); band=ndi.binary_dilation(e,iterations=3)&m
  ep=e&(ndi.maximum_filter(t,5)>0.5)
  return t[band&ndi.binary_dilation(ep,iterations=3)].sum()/ep.sum()
if __name__=='__main__':
    R='/workspace/shadowveil'
    h=[];f=[]
    for H in 'LR':
      for F in ['Index','Middle','Ring','Pinky']:
        h.append(width(f'{R}/views/apose/hands/{H}_{F}3.png')); f.append(width(f'{R}/hands/work/frames/apose_v2/{H}_{F}3_f1.png'))
    print('her %.2f  v2 %.2f'%(np.mean(h),np.mean(f)))
    