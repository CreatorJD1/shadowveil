"""Per-frame direct eye detection (streamed): no tracking; gaze = iris centre relative to the visible eye (sclera+iris) extents."""
import cv2,numpy as np,json,sys
V='/workspace/shadowveil/reference/grok_build/public/clean-room/videos/'
from analyze import hsvm
def run(clip):
    r=json.load(open(f'raw/{clip}.json'))
    if r.get('eyes',1) is None: return None
    tx0,ty0,tx1,ty1=r['template']; rows=r['rows']
    cap=cv2.VideoCapture(V+clip+'.mp4'); out=[]; i=-1
    while True:
        ok,f=cap.read(); i+=1
        if not ok: break
        H,W=f.shape[:2]; dx,dy=rows[i]['head_dx'],rows[i]['head_dy']
        # generous region around the tracked eye band (tracking only used to bound the search)
        X0=max(0,tx0+dx-60); X1=min(W,tx1+dx+60); Y0=max(0,ty0+dy-40); Y1=min(H,ty1+dy+40)
        sub=f[Y0:Y1,X0:X1]; m=hsvm(sub)
        hsv=cv2.cvtColor(sub,cv2.COLOR_BGR2HSV); h,s,v=[hsv[...,k].astype(int) for k in range(3)]
        skin=(h>=5)&(h<=20)&(s>=90)&(s<=200)&(v>=110)
        eye=(m['white']|m['green']|m['amber'])&cv2.dilate(skin.astype(np.uint8),np.ones((9,9),np.uint8)).astype(bool)
        n,l,st,cen=cv2.connectedComponentsWithStats(cv2.dilate(eye.astype(np.uint8),np.ones((3,3),np.uint8)))
        comps=[]
        for k in range(1,n):
            x,y,w,hh,a=st[k]
            if a<10 or w<5 or w>60 or hh>30: continue
            reg=(l==k)&eye; gi=(l==k)&m['green']; ai=(l==k)&m['amber']
            comps.append(dict(x0=int(X0+x),x1=int(X0+x+w),y0=int(Y0+y),y1=int(Y0+y+hh),cx=X0+cen[k][0],cy=Y0+cen[k][1],a=int(reg.sum()),g=int(gi.sum()),am=int(ai.sum()),
                              gx=(X0+np.nonzero(gi)[1].mean()) if gi.sum()>=4 else None, ax=(X0+np.nonzero(ai)[1].mean()) if ai.sum()>=4 else None))
        comps.sort(key=lambda c:-c['a']); comps=comps[:4]
        L=max((c for c in comps if c['g']>=4),key=lambda c:c['g'],default=None)
        R=None
        if L:
            cand=[c for c in comps if c is not L and abs(c['cy']-L['cy'])<12 and c['cx']<L['cx']-8]
            R=max(cand,key=lambda c:c['a'],default=None)
        rec=dict(frame=i)
        nomw={E:(r['boxes'][E][2]-r['boxes'][E][0]) if r['boxes'].get(E) else None for E in 'RL'}
        for E,c,key,col in (('L',L,'gx','green'),('R',R,'ax','amber')):
            if c is None or nomw[E] is None: continue
            rec[E+'_cx']=round(c['cx'],1); rec[E+'_cy']=round(c['cy'],1)
            ix=c[key]
            if ix is None: continue
            # eye extent: white/iris pixels in a window around the iris (rows of the iris), not the component bbox
            ir=np.zeros(m[col].shape,bool); gy_=np.nonzero(m[col])
            iy=float(c['cy']); nw=nomw[E]
            wx0=int(max(0,ix-X0-1.1*nw)); wx1=int(min(sub.shape[1],ix-X0+1.1*nw)); wy0=int(max(0,iy-Y0-4)); wy1=int(min(sub.shape[0],iy-Y0+5))
            ep=(m['white']|m[col])[wy0:wy1,wx0:wx1]
            ys_,xs_=np.nonzero(ep)
            if len(xs_)<8: continue
            ex0=X0+wx0+np.percentile(xs_,3); ex1=X0+wx0+np.percentile(xs_,97)+1
            w=ex1-ex0; rec[E+'_w']=round(float(w),1)
            if w>=0.5*nw: rec[E+'_gaze']=round(float((ix-(ex0+ex1)/2)/w),3)
        # face: skin blob in the region -> centre x, top (for yaw / nod proxies)
        ns,ls,sts,cs=cv2.connectedComponentsWithStats(skin.astype(np.uint8))
        if ns>1:
            k=1+int(np.argmax(sts[1:,4])); rec['face_cx']=round(X0+cs[k][0],1); rec['face_w']=int(sts[k,2]); rec['face_cy']=round(Y0+cs[k][1],1)
        out.append(rec)
    cap.release(); return out
if __name__=='__main__':
    for c in sys.argv[1:]:
        o=run(c)
        if o is None: continue
        json.dump(o,open(f'raw/{c}_gaze.json','w'))
        g=[x.get('L_gaze') for x in o]; print(c,'L gaze valid',sum(v is not None for v in g),'/',len(g),'median',np.nanmedian([v for v in g if v is not None]) if any(v is not None for v in g) else None)
