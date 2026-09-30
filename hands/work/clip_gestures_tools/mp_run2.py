import numpy as np,sys,os,json,cv2
import mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision
VD='/workspace/shadowveil/reference/grok_build/public/clean-room/videos'
def mk(n): return vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path='/workspace/gb/hand_landmarker.task'),num_hands=n,min_hand_detection_confidence=0.3,min_hand_presence_confidence=0.3,running_mode=vision.RunningMode.IMAGE))
D2=mk(2); D1=mk(1)
YMAX=float(os.environ.get('YMAX','0.70'))
def frames(c):
    cap=cv2.VideoCapture(f'{VD}/{c}.mp4'); out=[]
    while True:
        ok,f=cap.read()
        if not ok: break
        out.append(cv2.cvtColor(f,cv2.COLOR_BGR2RGB))
    return out
def det(d,im): return d.detect(mp.Image(image_format=mp.ImageFormat.SRGB,data=np.ascontiguousarray(im)))
def crop_detect(d,im,x0,y0,x1,y1,out_px=512):
    H,W=im.shape[:2]; x0,y0,x1,y1=max(0,int(x0)),max(0,int(y0)),min(W,int(x1)),min(H,int(y1))
    if x1-x0<20 or y1-y0<20: return []
    s=out_px/max(x1-x0,y1-y0); cr=cv2.resize(im[y0:y1,x0:x1],None,fx=s,fy=s,interpolation=cv2.INTER_CUBIC); r=det(d,cr); o=[]
    for lm,wl,hd in zip(r.hand_landmarks,r.hand_world_landmarks,r.handedness):
        o.append(dict(img=[(x0+p.x*cr.shape[1]/s,y0+p.y*cr.shape[0]/s) for p in lm],world=[(p.x,p.y,p.z) for p in wl],score=float(hd[0].score)))
    return o
def refine(im,h):
    a=np.array(h['img']); cx,cy=a.mean(0); s=max(np.ptp(a[:,0]),np.ptp(a[:,1]),30)*1.6
    r=crop_detect(D1,im,cx-s,cy-s,cx+s,cy+s)
    if r and np.linalg.norm(np.array(r[0]['img'][0])-a[0])<s*0.6: r[0]['refined']=True; return r[0]
    h['refined']=False; return h
def merge(L):
    L=sorted(L,key=lambda h:-h['score']); out=[]
    for h in L:
        a=np.array(h['img']); 
        if all(np.linalg.norm(a.mean(0)-np.array(o['img']).mean(0))>35 for o in out): out.append(h)
    return out
clips=sys.argv[1].split(',')
for c in clips:
    F=frames(c); H,W=F[0].shape[:2]; rows=[]; prev=[]
    for i,im in enumerate(F):
        cand=[]
        for y in range(0,max(1,H-256),256):
            for x in range(0,max(1,W-256),256):
                cand+=crop_detect(D2,im,x,y,x+384,y+384,576)
        for p in prev:   # tracking seed from previous frame
            a=np.array(p['img']); cx,cy=a.mean(0); s=max(np.ptp(a[:,0]),np.ptp(a[:,1]),30)*1.6
            cand+=crop_detect(D1,im,cx-s,cy-s,cx+s,cy+s)
        cand+=crop_detect(D2,im,0,0,W,H,max(W,H))
        cand=[h for h in cand if np.array(h['img'])[:,1].mean()<YMAX*H]
        hs=merge(cand)[:2]; hs=[refine(im,h) for h in hs]; hs=[h for h in merge(hs) if np.array(h['img'])[:,1].mean()<YMAX*H]
        rows.append([dict(img=[(round(float(a),1),round(float(b),1)) for a,b in h['img']],world=[tuple(round(float(q),5) for q in w) for w in h['world']],score=round(h['score'],3),refined=h.get('refined',False)) for h in hs]); prev=hs
    json.dump(dict(W=W,H=H,n=len(F),frames=rows),open(f'/workspace/gb/mp2_{c}.json','w'))
    print(c,len(F),'frames; detections per frame',np.bincount([len(h) for h in rows],minlength=3).tolist(),flush=True)
