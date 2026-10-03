#!/usr/bin/env python3
"""Fast offline LBS coverage sim of views/right skin (+underlay) in an ROI, using bone world [x,y,deg] from a render meta.json.
Coverage only (alpha>=128 from the texture, nearest sample). For screening candidates; verified later with the browser harness."""
import json, os, sys, numpy as np
from PIL import Image
ROOT='/workspace/shadowveil'; VD='/workspace/r2tree/views/right'
def load_skin(path):
    j=json.load(open(path)); bones=j['bones']; names=[b['name'] for b in bones]
    def pack(V,Wt,T,img):
        V=np.array(V,float); T=np.array([t[:3] for t in T],int)
        WI=np.zeros((len(V),4),int); WW=np.zeros((len(V),4))
        for i,wl in enumerate(Wt):
            for k,(b,w) in enumerate(wl): WI[i,k]=b; WW[i,k]=w
        A=np.array(Image.open(img).convert('RGBA'))[...,3]
        return dict(V=V,T=T,WI=WI,WW=WW,A=A)
    main=pack(j['vertices'],j['weights'],j['triangles'],os.path.join(VD,j['image']))
    main['L']=np.array([t[3] for t in j['triangles']])
    ul=None
    if j.get('underlay'):
        u=j['underlay']; ul=pack(u['vertices'],u['weights'],u['triangles'],os.path.join(VD,u['image']))
    return names,[b['pivot'] for b in bones],main,ul
def deform(m,names,piv,bw):
    M=[]
    for n,p in zip(names,piv):
        x,y,a=bw[n]; c,s=np.cos(np.radians(a)),np.sin(np.radians(a)); M.append((c,s,x,y,p[0],p[1]))
    M=np.array(M); V=m['V']; out=np.zeros_like(V)
    for k in range(4):
        mm=M[m['WI'][:,k]]; dx=V[:,0]-mm[:,4]; dy=V[:,1]-mm[:,5]
        out[:,0]+=m['WW'][:,k]*(mm[:,0]*dx-mm[:,1]*dy+mm[:,2]); out[:,1]+=m['WW'][:,k]*(mm[:,1]*dx+mm[:,0]*dy+mm[:,3])
    return out
def raster(m,P,roi,H=None):
    x0,y0,x1,y1=roi; cov=np.zeros((y1-y0,x1-x0),bool); V=m['V']; A=m['A']; h,w=A.shape
    tri=P[m['T']]; inr=(tri[:,:,0].max(1)>=x0)&(tri[:,:,0].min(1)<=x1)&(tri[:,:,1].max(1)>=y0)&(tri[:,:,1].min(1)<=y1)
    for ti in np.nonzero(inr)[0]:
        a,b,c=tri[ti]; d=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(d)<1e-9: continue
        bx0=max(x0,int(np.floor(min(a[0],b[0],c[0])))); bx1=min(x1-1,int(np.ceil(max(a[0],b[0],c[0])))); by0=max(y0,int(np.floor(min(a[1],b[1],c[1])))); by1=min(y1-1,int(np.ceil(max(a[1],b[1],c[1]))))
        if bx1<bx0 or by1<by0: continue
        ys,xs=np.mgrid[by0:by1+1,bx0:bx1+1]; px=xs+.5; py=ys+.5
        l1=((b[1]-c[1])*(px-c[0])+(c[0]-b[0])*(py-c[1]))/d; l2=((c[1]-a[1])*(px-c[0])+(a[0]-c[0])*(py-c[1]))/d; l3=1-l1-l2
        ins=(l1>=-1e-6)&(l2>=-1e-6)&(l3>=-1e-6)
        if not ins.any(): continue
        ua,ub,uc=V[m['T'][ti]]; u=l1*ua[0]+l2*ub[0]+l3*uc[0]; v=l1*ua[1]+l2*ub[1]+l3*uc[1]
        ui=np.clip(np.floor(u).astype(int),0,w-1); vi=np.clip(np.floor(v).astype(int),0,h-1)
        ok=ins&(A[vi,ui]>=128); cov[ys[ok]-y0,xs[ok]-x0]=True
    return cov
def coverage(skin,bw,roi,use_ul=True):
    names,piv,main,ul=skin; c=raster(main,deform(main,names,piv,bw),roi)
    if ul is not None and use_ul: c|=raster(ul,deform(ul,names,piv,bw),roi)
    return c
