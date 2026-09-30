import cv2,json,sys,numpy as np
V='/workspace/shadowveil/reference/grok_build/public/clean-room/videos/'
def clip_rows(clip,step,cols,scale=1.0):
    r=json.load(open(f'raw/{clip}.json')); tx0,ty0,tx1,ty1=r['template']; rows=r['rows']
    cap=cv2.VideoCapture(V+clip+'.mp4'); tiles=[]; i=-1
    while True:
        ok,f=cap.read(); i+=1
        if not ok: break
        if i%step: continue
        dx,dy=rows[i]['head_dx'],rows[i]['head_dy']; H,W=f.shape[:2]
        x0=max(0,tx0+dx);y0=max(0,ty0+dy+8);x1=min(W,tx1+dx);y1=min(H,ty1+dy-12)
        c=cv2.resize(f[y0:y1,x0:x1],None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA)
        t=np.full((c.shape[0]+10,c.shape[1],3),30,np.uint8); t[10:]=c
        cv2.putText(t,str(i),(1,8),cv2.FONT_HERSHEY_SIMPLEX,0.28,(0,255,255),1); tiles.append(t)
    cap.release()
    h=max(t.shape[0] for t in tiles); w=max(t.shape[1] for t in tiles); n=(len(tiles)+cols-1)//cols
    S=np.full((n*(h+1)+12,cols*(w+1),3),60,np.uint8); cv2.putText(S,clip,(2,10),cv2.FONT_HERSHEY_SIMPLEX,0.4,(255,255,255),1)
    for k,t in enumerate(tiles):
        y=12+(k//cols)*(h+1); x=(k%cols)*(w+1); S[y:y+t.shape[0],x:x+t.shape[1]]=t
    return S
if __name__=='__main__':
    out=sys.argv[1]; step=int(sys.argv[2]); cols=int(sys.argv[3]); clips=sys.argv[4:]
    parts=[clip_rows(c,step,cols) for c in clips]; W=max(p.shape[1] for p in parts)
    S=np.full((sum(p.shape[0]+4 for p in parts),W,3),20,np.uint8); y=0
    for p in parts: S[y:y+p.shape[0],:p.shape[1]]=p; y+=p.shape[0]+4
    cv2.imwrite(out,S)
