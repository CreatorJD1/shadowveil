import numpy as np
from PIL import Image
from scipy.ndimage import shift as nshift
def load(p):
  a=np.asarray(Image.open(p).convert('RGBA')).astype(np.float64)/255
  return a[...,:3]*a[...,3:]+(1-a[...,3:])
def comp(base,top,alpha=1.0):
  b=np.asarray(Image.open(base).convert('RGBA')).astype(float)/255 if isinstance(base,str) else base
  t=np.asarray(Image.open(top).convert('RGBA')).astype(float)/255 if isinstance(top,str) else top
  a=t[...,3:]*alpha; rgb=t[...,:3]*a+b[...,:3]*(1-a); al=a+b[...,3:]*(1-a)
  return np.concatenate([rgb,al],-1)
def white(rgba): return rgba[...,:3]*rgba[...,3:]+(1-rgba[...,3:])
def fit(img,tpl,box,mask=None,rng=3.0):
  """find (dx,dy): img ~= tpl shifted by (dx,dy). returns rmse(0-255),dx,dy"""
  x0,y0,x1,y1=box; pad=5
  T=tpl[y0-pad:y1+pad,x0-pad:x1+pad]; I=img[y0:y1,x0:x1]
  M=np.ones(I.shape[:2]) if mask is None else mask[y0:y1,x0:x1]
  M=M[...,None]/M.sum()
  best=(1e9,0,0)
  for st,r,c in ((0.25,rng,(0,0)),(0.025,0.3,None)):
    if c is None: c=(best[1],best[2])
    for dy in np.arange(c[1]-r,c[1]+r+1e-9,st):
      for dx in np.arange(c[0]-r,c[0]+r+1e-9,st):
        S=nshift(T,(dy,dx,0),order=1,mode='nearest')[pad:-pad,pad:-pad]
        e=np.sum(M*(S-I)**2)/3
        if e<best[0]: best=(e,dx,dy)
  return (round(best[0]**.5*255,2),round(float(best[1]),3),round(float(best[2]),3))
