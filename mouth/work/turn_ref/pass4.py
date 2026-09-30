# mouth tracking on Coder's frames f001..f241 (read-only). Forward from f001, backward from f241.
import numpy as np, json, pickle
from PIL import Image
from facemeas import *
TH=json.load(open('tmp/theta.json'))['theta']; N=241
FR='/workspace/shadowveil/reference/apose_turn/frames/f%03d.png'
def load(i): return np.array(Image.open(FR%(i+1)).convert('RGB'))
def measure_at(a,px,py,pw):
    skin=skin_level(a,(int(py-45),int(py-12),int(px-25),int(px+25)))
    hw=int(pw/2+12)
    box=(int(py-10),int(py+12),int(px-hw),int(px+hw))
    m=mouth(a,box,skin)
    return m,skin
def track(order):
    res={}; px,py,pw=None,None,None
    for i in order:
        a=load(i)
        if px is None:   # seed: front frame, mouth found in the lower face
            m,skin=None,None
            m,skin=measure_at(a,383,213,32)
        else:
            m,skin=measure_at(a,px,py,pw)
        if m is None or m['W']<4 or abs(m['cx']-px if px else 0)>10: break
        res[i]=(m,skin); px,py,pw=m['cx'],m['cy'],m['W']
    return res
fw=track(range(0,N)); bw=track(range(N-1,-1,-1))
print('forward frames',min(fw),max(fw),'backward',min(bw),max(bw))
json.dump(dict(fw=[min(fw),max(fw)],bw=[min(bw),max(bw)]),open('tmp/track_range.json','w'))
rows=[]; qa={}
for i in range(N):
    src=fw if i in fw else bw if i in bw else None
    th=TH[i]; r=dict(frame='f%03d'%(i+1),idx=i,theta=round(th,1))
    if src is None: rows.append(r); continue
    m,skin=src[i]; a=load(i)
    ir=irises(a,(int(m['cy']-46),int(m['cy']-27),int(m['cx']-55),int(m['cx']+55)))   # eye band 27-46 px above the seam
    eyeY=float(np.mean([v[1] for v in ir.values()])) if ir else None
    facing=0 if (th<50 or th>310) else (-1 if th<180 else 1)
    touch=m['leftOnContour'] or m['rightOnContour']
    if not touch:
        chin=chin_below(a,m['cx'],m['bot']+1,skin,int(m['cy']+45)); chinMode='outline'
    else:   # profile: chin bottom on the silhouette = where the contour below the lips recedes 3 px behind the chin tip
        fd=-1 if m['leftOnContour'] else 1; ys=range(int(m['bot'])+1,int(m['cy'])+45); edge=[]
        for y in ys:
            row=a[y].astype(int); fg=~((row[:,2]>row[:,0]+60)&(row[:,2]>row[:,1]+60)); xs=np.nonzero(fg[int(m['cx'])-40:int(m['cx'])+40])[0]+int(m['cx'])-40
            edge.append((xs.min() if fd<0 else xs.max()) if len(xs) else np.nan)
        e=np.array(edge,float)*fd; e=np.where(np.isnan(e),-1e9,e); k=int(np.argmax(e[:25])); chin=None   # e = forwardness
        for j in range(k+1,len(e)):
            if e[j]<e[j-1]-8: chin=float(ys[j-1]); break          # under-chin: the silhouette jumps back to the neck
        chinMode='silhouette'
    nb=nose(a,int(m['cx']-30),int(m['cx']+30),int(m['cy']-26),int(m['top']-1),skin,facing if touch or facing!=0 else 0)
    row=a[int(round(m['cy']))].astype(int); bgr=(row[:,2]>row[:,0]+60)&(row[:,2]>row[:,1]+60)
    c0=int(round(m['cx'])); L=c0
    while L>0 and not bgr[L-1]: L-=1
    R_=c0
    while R_<len(bgr)-1 and not bgr[R_+1]: R_+=1
    r.update(dict(skinL=round(skin,1),mouthCx=round(m['cx'],2),mouthCy=round(m['cy'],2),mouthL=round(m['left'],2),mouthR=round(m['right'],2),
        W=round(m['W'],2),H=round(m['H'],2),lift=round(m['lift'],2),yL=round(m['yL'],2),yR=round(m['yR'],2),
        leftOnContour=m['leftOnContour'],rightOnContour=m['rightOnContour'],openSpan=round(m['openSpan'],2),teethPx=round(m['teethPx'],1),
        sharp=round(m['sharp'],2),irises={k:[round(v[0],1),round(v[1],1)] for k,v in ir.items()},eyeY=(round(eyeY,2) if eyeY else None),
        chinY=chin,chinMode=chinMode,noseX=(round(nb[0],1) if nb else None),noseY=(round(nb[1],1) if nb else None),faceL=L,faceR=R_))
    rows.append(r)
    big=m['_big'].astype(np.uint8); ov=big.copy(); e=m['_m']^ndi.binary_erosion(m['_m']); ov[e]=(0,255,0)
    qa[i]=(ov,big,m['_box'])
json.dump(rows,open('tmp/pass4.json','w'),default=float)
pickle.dump(qa,open('tmp/qa4.pkl','wb'))
for r in rows[::6]: print({k:r.get(k) for k in ['frame','theta','W','lift','eyeY','chinY','noseX','noseY','mouthCx','mouthCy','faceL','faceR','leftOnContour','rightOnContour','openSpan','sharp']})
