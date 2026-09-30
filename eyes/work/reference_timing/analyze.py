import cv2, numpy as np, json, sys, os
from probe import frames
FPS=24
def hsvm(f):
    hsv=cv2.cvtColor(f,cv2.COLOR_BGR2HSV); h,s,v=[hsv[...,i].astype(int) for i in range(3)]
    return dict(green=(h>=35)&(h<=85)&(s>60)&(v>60),
                amber=(h>=14)&(h<=22)&(s>=150)&(v>150),
                white=(s<60)&(v>170)&~((h>=95)&(h<=135)&(s>25)),   # not keyed-blue fringe
                dark=(v<70))
def find_eyes(f):
    H,W=f.shape[:2]; m=hsvm(f)
    g=m['green'].copy(); g[int(H*0.5):]=False
    n,l,st,cen=cv2.connectedComponentsWithStats(g.astype(np.uint8))
    best=None
    for i in range(1,n):
        if st[i,4]<12: continue
        x,y,w,h,a=st[i]
        wn=m['white'][max(0,y-4):y+h+4,max(0,x-10):x+w+10].sum()
        if wn<6: continue
        if best is None or a>best[4]: best=st[i]
    if best is None: return None
    x,y,w,h,a=best
    # EyeL box: white+green pixels connected within the neighbourhood
    def eyebox(cx,cy,rw,rh):
        x0,x1=max(0,cx-rw),min(W,cx+rw); y0,y1=max(0,cy-rh),min(H,cy+rh)
        e=(m['white']|m['green']|m['amber'])[y0:y1,x0:x1]
        ys,xs=np.nonzero(e)
        if len(xs)<8: return None
        return [int(x0+np.percentile(xs,2)),int(y0+np.percentile(ys,2)),int(x0+np.percentile(xs,98))+1,int(y0+np.percentile(ys,98))+1]
    Lc=(x+w//2,y+h//2); bL=eyebox(Lc[0],Lc[1],max(14,int(w*1.3)),max(7,int(h*0.8)))
    ew=bL[2]-bL[0]
    # EyeR: white/amber blob left of EyeL at similar height
    sx0=max(0,bL[0]-int(ew*3.2)); sx1=max(0,bL[0]-int(ew*0.4)); sy0=max(0,bL[1]-8); sy1=bL[3]+8
    wr=(m['white']|m['amber'])[sy0:sy1,sx0:sx1]
    bR=None
    if wr.sum()>=10:
        n2,l2,st2,c2=cv2.connectedComponentsWithStats(ndil(wr))
        j=1+np.argmax(st2[1:,4]) if n2>1 else None
        if j is not None and st2[j,4]>=10:
            cx=int(sx0+c2[j][0]); cy=int(sy0+c2[j][1]); bR=eyebox(cx,cy,max(14,ew//2+4),max(7,(bL[3]-bL[1])//2+3))
    return dict(L=bL,R=bR)
def ndil(m): return cv2.dilate(m.astype(np.uint8),np.ones((3,3),np.uint8))
def analyze(clip):
    """streaming: one decoded frame in memory at a time; tracker matches the first-frame template and the
    previous frame's patch (adaptive), keeping whichever scores higher"""
    V='/workspace/shadowveil/reference/grok_build/public/clean-room/videos/'
    cap=cv2.VideoCapture(V+clip+'.mp4'); n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    init=None; i=-1
    while True:
        ok,f=cap.read(); i+=1
        if not ok: break
        e=find_eyes(f)
        if e: init=(i,e); break
    cap.release()
    if init is None: return dict(clip=clip,frames=n,eyes=None)
    i0,e=init; H,W=f.shape[:2]
    boxes=[b for b in (e['R'],e['L']) if b]
    ux0=min(b[0] for b in boxes); uy0=min(b[1] for b in boxes); ux1=max(b[2] for b in boxes); uy1=max(b[3] for b in boxes)
    ew=ux1-ux0; pad_x=max(12,ew//3); tx0=max(0,ux0-pad_x); tx1=min(W,ux1+pad_x); ty0=max(0,uy0-18); ty1=min(H,uy1+22)
    T0=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)[ty0:ty1,tx0:tx1].copy(); Tp=T0.copy()
    th,tw=T0.shape
    cap=cv2.VideoCapture(V+clip+'.mp4'); rows=[]; prev=(tx0,ty0); prevg=None; i=-1
    while True:
        ok,f=cap.read(); i+=1
        if not ok: break
        g=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)
        if i<=i0: p,sc=(tx0,ty0),1.0
        else:
            R=36; px,py=prev
            sx0=max(0,px-R); sy0=max(0,py-R); sx1=min(W,px+R+tw); sy1=min(H,py+R+th); win=g[sy0:sy1,sx0:sx1]
            best=(prev,0.0)
            for T in (T0,Tp):
                r=cv2.matchTemplate(win,T,cv2.TM_CCOEFF_NORMED); _,mx,_,ml=cv2.minMaxLoc(r)
                if mx>best[1]: best=((sx0+ml[0],sy0+ml[1]),mx)
            p,sc=best
        cand=g[p[1]:p[1]+th,p[0]:p[0]+tw]
        if sc>0.75 and cand.shape==T0.shape: Tp=cand.copy()
        prev=p; dx=p[0]-tx0; dy=p[1]-ty0
        cx0=max(0,tx0+dx-10); cy0=max(0,ty0+dy-10); cx1=min(W,tx1+dx+10); cy1=min(H,ty1+dy+10)
        mc=hsvm(f[cy0:cy1,cx0:cx1])
        row=dict(frame=i,t_ms=round(i*1000/FPS,1),head_dx=int(dx),head_dy=int(dy),track=round(float(sc),3))
        for E,b,ic in (('R',e['R'],'amber'),('L',e['L'],'green')):
            if not b: continue
            x0,y0,x1,y1=b[0]+dx,b[1]+dy,b[2]+dx,b[3]+dy
            X0,Y0,X1,Y1=max(cx0,x0-3),max(cy0,y0-3),min(cx1,x1+3),min(cy1,y1+3)
            wm=mc['white'][Y0-cy0:Y1-cy0,X0-cx0:X1-cx0]; im_=mc[ic][Y0-cy0:Y1-cy0,X0-cx0:X1-cx0]
            row[E+'_white']=int(wm.sum()); row[E+'_iris']=int(im_.sum())
            ys,xs=np.nonzero(im_)
            if len(xs)>=4:
                row[E+'_iris_x']=round(float((X0+xs.mean()-(x0+x1)/2)/(x1-x0)),3)
                row[E+'_iris_y']=round(float((Y0+ys.mean()-(y0+y1)/2)/(y1-y0)),3)
            else: row[E+'_iris_x']=row[E+'_iris_y']=None
        if prevg is not None:
            a_=g[cy0:cy1,cx0:cx1].astype(np.int16); b_=prevg[cy0:cy1,cx0:cx1].astype(np.int16)
            row['face_diff']=round(float(np.abs(a_-b_).mean()),2)
        else: row['face_diff']=None
        prevg=g; rows.append(row)
    cap.release()
    return dict(clip=clip,frames=len(rows),size=[W,H],init_frame=i0,boxes=e,template=[tx0,ty0,tx1,ty1],rows=rows)
if __name__=='__main__':
    for c in sys.argv[1:]:
        r=analyze(c); os.makedirs('raw',exist_ok=True); json.dump(r,open(f'raw/{c}.json','w'))
        if r.get('eyes',1) is None: print(c,'no eyes'); continue
        rw=r['rows']; print(c,'init',r['init_frame'],r['boxes'],'track min',min(x['track'] for x in rw))
