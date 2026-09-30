import cv2,numpy as np,json,sys,glob
from expect import ld,over,expected,V
R='/workspace/shadowveil/rig/previews/idle/frames/'
name,view=sys.argv[1],sys.argv[2]
rig=json.load(open(V+f'{view}/eyes/rig.json')); L=rig['irisLimitsPx']
meta=json.load(open(R+f'{name}/meta.json'))['frames']
rest=ld(R+f'{name}/rest.png')
wr=rig['workRegion']; P=40
box=[wr[0]-P,wr[1]-P,wr[2]+1+P,wr[3]+1+P+30]
x0,y0,x1,y1=box
# eye footprints
fp=np.zeros((y1-y0,x1-x0),bool); ring=None
eyes=rig['eyes']; per={}
for e in eyes:
    w=ld(V+f'{view}/eyes/{e}_white.png')[y0:y1,x0:x1,3]>0
    la=ld(V+f'{view}/eyes/{e}_lash.png')[y0:y1,x0:x1,3]>0
    lid=np.zeros_like(w)
    for k in range(8): lid|=ld(V+f'{view}/eyes/{e}_lid_{k}.png')[y0:y1,x0:x1,3]>0
    foot=w|la|lid; per[e]=dict(white=w,foot=foot)
    fp|=foot
fpd=cv2.dilate(fp.astype(np.uint8),np.ones((9,9),np.uint8))>0
gray=lambda im:cv2.cvtColor((np.clip(im[...,:3],0,1)*255).astype(np.uint8),cv2.COLOR_BGR2GRAY).astype(np.float32)
restc=rest[y0:y1,x0:x1]
alpha_ok=restc[...,3]>0.99
face_mask=((~fpd)&alpha_ok).astype(np.uint8)
def rule(X,Y):
    dx=round(X*(L['dxAtXplus1'] if X>0 else -L['dxAtXminus1'])); dy=round(Y*(L['dyAtYplus1'] if Y>0 else -L['dyAtYminus1']))
    return int(np.floor(dx+0.5)) if False else dx,dy
def jsround(v): return int(np.floor(v+0.5))
cache={}
def exp(k,dx,dy):
    key=(k,dx,dy)
    if key not in cache: cache[key]=expected(view,k,rest,dx,dy,box)
    return cache[key]
out=[]
frames=sorted(glob.glob(R+f'{name}/frames/f*.png'))
Wm=np.eye(2,3,dtype=np.float32)
for i,fpth in enumerate(frames):
    fr=ld(fpth)[y0:y1,x0:x1]
    p=meta[i]['params']
    # face transform: frame -> rest coordinates
    try:
        _,Wf=cv2.findTransformECC(gray(restc),gray(fr),Wm.copy(),cv2.MOTION_EUCLIDEAN,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,60,1e-5),face_mask,3)
    except cv2.error: Wf=Wm.copy()
    al=cv2.warpAffine(fr,Wf,(x1-x0,y1-y0),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REPLICATE)
    rec=dict(i=i,face=[float(Wf[0,2]),float(Wf[1,2]),float(np.degrees(np.arctan2(Wf[1,0],Wf[0,0])))])
    kR=jsround((1-p.get('EyeROpen',1))*7); kL=jsround((1-p.get('EyeLOpen',1))*7)
    X,Y=p['EyeBallX'],p['EyeBallY']
    dxr=jsround(X*(L['dxAtXplus1'] if X>0 else -L['dxAtXminus1'])); dyr=jsround(Y*(L['dyAtYplus1'] if Y>0 else -L['dyAtYminus1']))
    rec.update(k=[kR,kL],rule=[dxr,dyr])
    # best k and iris offset per eye (open-eye only for offset)
    for e in eyes:
        m=per[e]['foot']; md=cv2.dilate(m.astype(np.uint8),np.ones((5,5),np.uint8))>0
        kexp=kR if e=='EyeR' else kL
        best=None
        cands=[(kexp,dx,dy) for dx in range(-4,5) for dy in range(-3,4)] if kexp==0 else [(k,dxr,dyr) for k in range(8)]
        for (k,dx,dy) in cands:
            E=exp(k,dx,dy); d=np.abs(E[...,:3]-al[...,:3]).max(2)[md].mean()
            if best is None or d<best[0]: best=(d,k,dx,dy)
        E=exp(best[1],best[2],best[3])
        # slide: ECC of eye neighbourhood between expected and aligned frame
        try:
            _,We=cv2.findTransformECC(gray(E),gray(al),Wm.copy(),cv2.MOTION_TRANSLATION,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,60,1e-5),md.astype(np.uint8),3)
            sl=[float(We[0,2]),float(We[1,2])]
        except cv2.error: sl=[None,None]
        diff=np.abs(E[...,:3]-al[...,:3]).max(2)*255
        adrop=(al[...,3]<0.9)&(E[...,3]>0.99)&md
        bright=(al[...,:3].min(2)>0.75)&(E[...,:3].min(2)<0.55)&md
        rec[e]=dict(k=best[1],dx=best[2],dy=best[3],err=round(float(best[0]*255),2),slide=sl,
                    bad20=int(((diff>60)&md).sum()),alphaHole=int(adrop.sum()),newWhite=int(bright.sum()))
    out.append(rec)
    if i%40==0: print(name,i,rec,flush=True)
json.dump(dict(name=name,view=view,box=box,frames=out),open(f'res_{name}.json','w'))
