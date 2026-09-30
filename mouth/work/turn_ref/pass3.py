import numpy as np, json
from facemeas import *
P=json.load(open('tmp/pass1.json')); C=np.load('tmp/headcrops.npy',mmap_mode='r'); TH=json.load(open('tmp/theta.json'))['theta']
N=len(P); rows=[]; qa=[]
prev=None
for i in range(N):
    a=np.array(C[i]); X0,Y0=P[i]['cropX0'],P[i]['cropY0']; th=TH[i]
    ir=irises(a,(85,150,10,210))
    eyeY=np.mean([v[1] for v in ir.values()]) if ir else None
    skin=skin_level(a,(120,175,60,160))
    facing=0 if (th<50 or th>310) else (-1 if th<180 else 1)
    # mouth search box (crop coords): below the eye line; x from the previous mouth if known
    ey=eyeY if eyeY is not None else (prev['eyeY_c'] if prev else 117)
    if prev and abs(prev['theta']-th)<15: cx=prev['cx_c']
    else: cx=110
    box=(int(ey+18),int(ey+56),int(max(cx-45,0)),int(min(cx+45,219)))
    back=90<th<270 and not ir
    m=None if (115<th<245) else mouth(a,box,skin)
    r=dict(frame=i,t_ms=round(i*1000/24,1),theta=round(th,1),facing=facing,irises=sorted(ir.keys()),eyeY=(round(ey+Y0,2) if eyeY is not None else None))
    if m:
        chin=chin_below(a,m['cx'],m['bot']+1,skin,a.shape[0])
        # nose between the eye line and the mouth top
        nb=nose(a,int(max(m['cx']-30,0)),int(min(m['cx']+30,219)),int(ey+6),int(m['top']-1),skin,facing) if m['top']-1>ey+6 else None
        # face contour at the seam row: first background pixel left/right of the mouth centre
        row=a[int(round(m['cy']))].astype(int); bgr=(row[:,2]>row[:,0]+60)&(row[:,2]>row[:,1]+60)
        c0=int(round(m['cx'])); L=c0
        while L>0 and not bgr[L-1]: L-=1
        R_=c0
        while R_<len(bgr)-1 and not bgr[R_+1]: R_+=1
        r.update(dict(mouthCx=round(m['cx']+X0,2),mouthCy=round(m['cy']+Y0,2),W=round(m['W'],2),H=round(m['H'],2),lift=round(m['lift'],2),
            yLc=round(m['yL']+Y0,2),yRc=round(m['yR']+Y0,2),leftOnContour=m['leftOnContour'],rightOnContour=m['rightOnContour'],
            openSpan=round(m['openSpan'],2),teethPx=round(m['teethPx'],1),sharp=round(m['sharp'],2),
            chinY=(round(chin+Y0,1) if chin else None),noseX=(round(nb[0]+X0,1) if nb else None),noseY=(round(nb[1]+Y0,1) if nb else None),
            faceL=L+X0,faceR=R_+X0,mouthL=round(m['left']+X0,2),mouthR=round(m['right']+X0,2),
            eyeXs={k:round(v[0]+X0,2) for k,v in ir.items()}))
        prev=dict(cx_c=m['cx'],eyeY_c=ey,theta=th)
        big=m['_big'].astype(np.uint8).copy(); e=m['_m']^ndi.binary_erosion(m['_m']); big[e]=(0,255,0)
        qa.append((i,big,m['_big'].astype(np.uint8)))
    rows.append(r)
json.dump(rows,open('tmp/pass3.json','w'))
import pickle; pickle.dump([(i,b,c) for i,b,c in qa],open('tmp/qa.pkl','wb'))
for r in rows[::6]: print({k:r.get(k) for k in ['frame','theta','irises','W','lift','chinY','eyeY','noseX','mouthCx','faceL','faceR','leftOnContour','rightOnContour','openSpan','sharp']})
