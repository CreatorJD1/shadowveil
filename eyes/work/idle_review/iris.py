# iris centroid relative to the eye opening (aligned on white/lash outline, iris excluded)
import cv2,numpy as np,json,sys,glob
from expect import ld,V
R='/workspace/shadowveil/rig/previews/idle/frames/'
name,view=sys.argv[1],sys.argv[2]
rig=json.load(open(V+f'{view}/eyes/rig.json'))
rest=ld(R+f'{name}/rest.png'); meta=json.load(open(R+f'{name}/meta.json'))['frames']
res=json.load(open(f'res_{name}.json'))['frames']
out={}
for e in rig['eyes']:
    w=ld(V+f'{view}/eyes/{e}_white.png')[...,3]>0; ir=ld(V+f'{view}/eyes/{e}_iris.png')[...,3]>0
    ys,xs=np.nonzero(w); P=14; x0,y0,x1,y1=xs.min()-P,ys.min()-P,xs.max()+P+1,ys.max()+P+1
    rc=rest[y0:y1,x0:x1]; wc=w[y0:y1,x0:x1]; ic=ir[y0:y1,x0:x1]
    ring=(cv2.dilate(wc.astype(np.uint8),np.ones((7,7),np.uint8))>0)&~cv2.erode(wc.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
    hsv=lambda im:cv2.cvtColor((np.clip(im[...,:3],0,1)*255).astype(np.uint8),cv2.COLOR_BGR2HSV).astype(int)
    hr=hsv(rc)
    # iris colour model from rest: pixels in iris footprint, hue range
    hues=hr[ic][:,0]; sat=hr[ic][:,1]
    lo,hi=np.percentile(hues,5),np.percentile(hues,95)
    def irismask(h): return (h[...,0]>=lo-2)&(h[...,0]<=hi+2)&(h[...,1]>=np.percentile(sat,10)*0.8)
    g=lambda im:cv2.cvtColor((np.clip(im[...,:3],0,1)*255).astype(np.uint8),cv2.COLOR_BGR2GRAY).astype(np.float32)
    im0=irismask(hr)&cv2.dilate(wc.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
    c0=np.array(np.nonzero(im0)[::-1]).mean(1)
    wx=np.nonzero(wc.any(0))[0]; width=wx.max()-wx.min()+1
    rows=[]
    for i,fp in enumerate(sorted(glob.glob(R+f'{name}/frames/f*.png'))):
        k=res[i]['k'][0 if e=='EyeR' else 1]
        if k!=0: rows.append(None); continue
        fr=ld(fp)[y0:y1,x0:x1]
        W=np.eye(2,3,dtype=np.float32)
        try: _,W=cv2.findTransformECC(g(rc),g(fr),W,cv2.MOTION_EUCLIDEAN,(3,80,1e-5),ring.astype(np.uint8),3)
        except cv2.error: pass
        al=cv2.warpAffine(fr,W,(x1-x0,y1-y0),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REPLICATE)
        m=irismask(hsv(al))&cv2.dilate(wc.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
        outside=irismask(hsv(al))&~cv2.dilate(wc.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)&(cv2.dilate(wc.astype(np.uint8),np.ones((9,9),np.uint8))>0)
        c=np.array(np.nonzero(m)[::-1]).mean(1)
        rows.append(dict(i=i,dx=round(float(c[0]-c0[0]),2),dy=round(float(c[1]-c0[1]),2),n=int(m.sum()),out=int(outside.sum()),out0=int((irismask(hr)&~cv2.dilate(wc.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)&(cv2.dilate(wc.astype(np.uint8),np.ones((9,9),np.uint8))>0)).sum())))
    out[e]=dict(width=int(width),rows=rows)
    v=[r for r in rows if r]; dx=np.array([r['dx'] for r in v])
    print(name,e,'eye width',width,'iris dx range',dx.min(),dx.max(),'(frac of width',round(dx.min()/width,3),round(dx.max()/width,3),') outside-iris px max',max(r['out'] for r in v),'rest',v[0]['out0'])
json.dump(out,open(f'iris_{name}.json','w'))
