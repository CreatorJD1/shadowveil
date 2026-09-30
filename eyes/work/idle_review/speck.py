import cv2,numpy as np,glob,json,sys
from expect import ld,V
R='/workspace/shadowveil/rig/previews/idle/frames/'
name,view=sys.argv[1],sys.argv[2]
d=json.load(open(f'res_{name}.json')); x0,y0,x1,y1=d['box']
rest=ld(R+f'{name}/rest.png')[y0:y1,x0:x1]
rig=json.load(open(V+f'{view}/eyes/rig.json'))
for e in rig['eyes']:
    ir=ld(V+f'{view}/eyes/{e}_iris.png')[y0:y1,x0:x1,3]>0; wh=ld(V+f'{view}/eyes/{e}_white.png')[y0:y1,x0:x1,3]>0
    hits=[]
    for i,f in enumerate(sorted(glob.glob(R+f'{name}/frames/f*.png'))):
        r=d['frames'][i]
        if r['k'][0 if e=='EyeR' else 1]!=0: continue
        dx,dy=r[e]['dx'],r[e]['dy']
        core=np.roll(cv2.erode(ir.astype(np.uint8),np.ones((3,3),np.uint8)),(dy,dx),(0,1))>0
        core&=cv2.erode(wh.astype(np.uint8),np.ones((3,3),np.uint8))>0
        tx,ty,rot=r['face']; c,s=np.cos(np.radians(rot)),np.sin(np.radians(rot))
        W=np.array([[c,-s,tx],[s,c,ty]],np.float32)
        fr=ld(f)[y0:y1,x0:x1]
        al=cv2.warpAffine(fr,W,(x1-x0,y1-y0),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REPLICATE)
        E=np.roll(rest,(0,0),(0,1))
        b=(al[...,:3].min(2)>0.78)&core
        if b.sum():
            yy,xx=np.nonzero(b); hits.append((i,int(b.sum()),int(xx[0]+x0),int(yy[0]+y0),(dx,dy)))
    print(name,e,'open frames with near-white px inside iris core:',len(hits),hits[:40])
