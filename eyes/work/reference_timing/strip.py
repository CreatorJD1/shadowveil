import cv2,json,sys,numpy as np
V='/workspace/shadowveil/reference/grok_build/public/clean-room/videos/'
def strip(clip,out,f0=0,f1=None,step=1,scale=3,cols=16,pad=14):
    r=json.load(open(f'raw/{clip}.json')); tx0,ty0,tx1,ty1=r['template']; rows=r['rows']
    ev=json.load(open('events.json'))[clip]; oR=ev.get('R_open'); oL=ev.get('L_open')
    cap=cv2.VideoCapture(V+clip+'.mp4'); tiles=[]; i=-1
    f1=len(rows)-1 if f1 is None else f1
    while True:
        ok,f=cap.read(); i+=1
        if not ok or i>f1: break
        if i<f0 or (i-f0)%step: continue
        dx,dy=rows[i]['head_dx'],rows[i]['head_dy']
        H,W=f.shape[:2]; x0=max(0,tx0+dx-4); y0=max(0,ty0+dy+6); x1=min(W,tx1+dx+4); y1=min(H,ty1+dy-10)
        c=cv2.resize(f[y0:y1,x0:x1],None,fx=scale,fy=scale,interpolation=cv2.INTER_NEAREST)
        t=np.full((c.shape[0]+pad,c.shape[1],3),30,np.uint8); t[pad:]=c
        lab=f'{i} R{oR[i] if oR else "-"} L{oL[i] if oL else "-"}'
        cv2.putText(t,lab,(2,11),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,255,255),1)
        tiles.append(t)
    cap.release()
    h=max(t.shape[0] for t in tiles); w=max(t.shape[1] for t in tiles)
    rowsn=(len(tiles)+cols-1)//cols; S=np.full((rowsn*(h+2),cols*(w+2),3),60,np.uint8)
    for k,t in enumerate(tiles):
        y=(k//cols)*(h+2); x=(k%cols)*(w+2); S[y:y+t.shape[0],x:x+t.shape[1]]=t
    cv2.imwrite(out,S)
if __name__=='__main__':
    a=sys.argv; strip(a[1],a[2],*(int(x) for x in a[3:]))
