# iris displacement relative to the eye opening: eye-local alignment on the outline ring, then ECC on the iris footprint
import cv2,numpy as np,json,sys,glob
from expect import ld,V
R='/workspace/shadowveil/rig/previews/idle/frames/'
name,view=sys.argv[1],sys.argv[2]; step=int(sys.argv[3]) if len(sys.argv)>3 else 1
rig=json.load(open(V+f'{view}/eyes/rig.json'))
rest=ld(R+f'{name}/rest.png'); res=json.load(open(f'res_{name}.json'))['frames']
g=lambda im:cv2.cvtColor((np.clip(im[...,:3],0,1)*255).astype(np.uint8),cv2.COLOR_BGR2GRAY).astype(np.float32)
out={}
files=sorted(glob.glob(R+f'{name}/frames/f*.png'))
for e in rig['eyes']:
    w=ld(V+f'{view}/eyes/{e}_white.png')[...,3]>0; ir=ld(V+f'{view}/eyes/{e}_iris.png')[...,3]>0
    ys,xs=np.nonzero(w); P=14; x0,y0,x1,y1=xs.min()-P,ys.min()-P,xs.max()+P+1,ys.max()+P+1
    rc=rest[y0:y1,x0:x1]; wc=w[y0:y1,x0:x1].astype(np.uint8); ic=(ir[y0:y1,x0:x1]).astype(np.uint8)
    ring=((cv2.dilate(wc,np.ones((7,7),np.uint8))>0)&~(cv2.dilate(ic,np.ones((5,5),np.uint8))>0)).astype(np.uint8)
    im=cv2.dilate(ic,np.ones((3,3),np.uint8))&wc
    rows=[]
    for i in range(0,len(files),step):
        if res[i]['k'][0 if e=='EyeR' else 1]!=0: continue
        fr=ld(files[i])[y0:y1,x0:x1]; W=np.eye(2,3,dtype=np.float32)
        try: _,W=cv2.findTransformECC(g(rc),g(fr),W,cv2.MOTION_EUCLIDEAN,(3,80,1e-5),ring,3)
        except cv2.error: pass
        al=cv2.warpAffine(fr,W,(x1-x0,y1-y0),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REPLICATE)
        T=np.eye(2,3,dtype=np.float32)
        try: _,T=cv2.findTransformECC(g(rc),g(al),T,cv2.MOTION_TRANSLATION,(3,80,1e-5),im,3)
        except cv2.error: T[:]=np.nan
        rows.append((i,round(float(T[0,2]),2),round(float(T[1,2]),2)))
    out[e]=dict(width=int(np.ptp(xs)+1),rows=rows)
    # print runs of rounded offsets
    runs=[];prev=None
    for i,dx,dy in rows:
        key=(round(dx*2)/2,round(dy*2)/2) if dx==dx else None
        if key!=prev: runs.append((i,key)); prev=key
    dxs=np.array([r[1] for r in rows]); print(name,e,'w',out[e]['width'],'dx range',np.nanmin(dxs),np.nanmax(dxs),'| changes (frame,(dx,dy) to 0.5px):',runs)
json.dump(out,open(f'iris2_{name}.json','w'))
