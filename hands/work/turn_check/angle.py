import cv2,numpy as np,json
V='/workspace/shadowveil/reference/grok_build/public/clean-room/videos/apose-turn.mp4'
def fg(im):
    im=im.astype(int); return ~((im[...,2]>120)&(im[...,2]>im[...,0]+60)&(im[...,2]>im[...,1]+60))
cap=cv2.VideoCapture(V); R=[]; i=0
while True:
    ok,f=cap.read()
    if not ok: break
    m=fg(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)); ys,xs=np.nonzero(m); top,bot=ys.min(),ys.max(); H=bot-top+1
    ws={}
    for fr in (0.17,0.19,0.21,0.23):
        y=int(top+fr*H); row=np.nonzero(m[y])[0]; ws[fr]=int(row.max()-row.min()+1) if len(row) else 0
    R.append(dict(f=i,top=int(top),bot=int(bot),H=int(H),left=int(xs.min()),right=int(xs.max()),w=ws,wmed=float(np.median(list(ws.values())))))
    i+=1
json.dump(R,open('silhouette.json','w'))
for r in R[::8]: print(r['f'],r['H'],r['left'],r['right'],r['w'])
