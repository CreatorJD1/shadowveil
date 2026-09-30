import cv2,numpy as np,sys
# usage: zoom.py out.png x0 y0 w h scale f1 f2 ...
out=sys.argv[1]; x0,y0,w,h,s=map(int,sys.argv[2:7]); want=set(map(int,sys.argv[7:]))
cap=cv2.VideoCapture('../../../reference/grok_build/public/clean-room/videos/apose-turn.mp4')
tiles=[];i=-1
while want:
    ok,f=cap.read(); i+=1
    if not ok: break
    if i not in want: continue
    want.discard(i)
    c=cv2.resize(f[y0:y0+h,x0:x0+w],None,fx=s,fy=s,interpolation=cv2.INTER_NEAREST)
    for ax in range((x0+4)//5*5,x0+w+1,5):
        x=ax-x0; X=x*s; L=14 if ax%10==0 else 5
        cv2.line(c,(X,0),(X,L),(0,255,255),1); cv2.line(c,(X,h*s-1),(X,h*s-1-L),(0,255,255),1)
        cv2.line(c,(X,0),(X,h*s),(0,255,255) if ax%10==0 else (0,160,160),1) if False else None
        if ax%10==0: cv2.putText(c,str(ax%100),(X+2,h*s-18),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,255,255),1)
    for ay in range((y0+4)//5*5,y0+h+1,5):
        y=ay-y0; Y=y*s; L=14 if ay%10==0 else 5
        cv2.line(c,(0,Y),(L,Y),(0,255,255),1)
        if ay%10==0: cv2.putText(c,str(ay),(12,Y+4),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,255,255),1)
    cv2.putText(c,f'f{i}',(w*s-40,h*s-6),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255),1)
    tiles.append(c)
cap.release()
cv2.imwrite(out,np.vstack(tiles))
