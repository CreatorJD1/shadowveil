import cv2,json,sys,numpy as np
V='/workspace/shadowveil/reference/grok_build/public/clean-room/videos/'
def rowimg(clip,a,b,scale=2,label='',step=1):
    r=json.load(open(f'raw/{clip}.json')); tx0,ty0,tx1,ty1=r['template']; rows=r['rows']
    ev=json.load(open('events.json'))[clip]; oR=ev.get('R_open'); oL=ev.get('L_open')
    cap=cv2.VideoCapture(V+clip+'.mp4'); cap.set(cv2.CAP_PROP_POS_FRAMES,max(0,a)); tiles=[]
    for i in range(max(0,a),min(len(rows)-1,b)+1):
        ok,f=cap.read()
        if not ok: break
        if (i-a)%step: continue
        dx,dy=rows[i]['head_dx'],rows[i]['head_dy']; H,W=f.shape[:2]
        x0=max(0,tx0+dx-6);y0=max(0,ty0+dy+4);x1=min(W,tx1+dx+6);y1=min(H,ty1+dy-6)
        c=cv2.resize(f[y0:y1,x0:x1],None,fx=scale,fy=scale,interpolation=cv2.INTER_CUBIC)
        t=np.full((c.shape[0]+12,c.shape[1],3),30,np.uint8); t[12:]=c
        cv2.putText(t,f'{i} {oR[i] if oR else "-"}/{oL[i] if oL else "-"}',(1,9),cv2.FONT_HERSHEY_SIMPLEX,0.3,(0,255,255),1); tiles.append(t)
    cap.release()
    h=max(t.shape[0] for t in tiles); w=max(t.shape[1] for t in tiles); C=10
    tiles=[np.pad(t,((0,h-t.shape[0]+1),(0,w-t.shape[1]+1),(0,0))) for t in tiles]
    while len(tiles)%C: tiles.append(np.zeros_like(tiles[0]))
    S=np.vstack([np.hstack(tiles[k:k+C]) for k in range(0,len(tiles),C)])
    L=np.full((12,S.shape[1],3),0,np.uint8); cv2.putText(L,f'{clip} {label}',(2,10),cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
    return np.vstack([L,S])
if __name__=='__main__':
    out=sys.argv[1]; specs=sys.argv[2:]   # clip:a:b[:scale]
    ims=[]
    for s in specs:
        p=s.split(':'); st=int(p[4]) if len(p)>4 else 1; ims.append(rowimg(p[0],int(p[1]),int(p[2]),float(p[3]) if len(p)>3 else 2,f'{p[1]}-{p[2]} step {st}',st))
    W=max(i.shape[1] for i in ims); S=np.vstack([np.pad(i,((0,4),(0,W-i.shape[1]),(0,0))) for i in ims]); cv2.imwrite(out,S)
