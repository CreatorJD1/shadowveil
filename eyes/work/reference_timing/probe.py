import cv2,numpy as np,sys
V='/workspace/shadowveil/reference/grok_build/public/clean-room/videos/'
def frames(clip):
    cap=cv2.VideoCapture(V+clip+'.mp4'); out=[]
    while True:
        ok,f=cap.read()
        if not ok: break
        out.append(f)
    return out
def masks(f):
    hsv=cv2.cvtColor(f,cv2.COLOR_BGR2HSV); h,s,v=hsv[...,0].astype(int),hsv[...,1].astype(int),hsv[...,2].astype(int)
    green=(h>=35)&(h<=85)&(s>60)&(v>60)
    white=(s<60)&(v>170)
    return green,white,hsv
if __name__=='__main__':
    clip=sys.argv[1]; F=frames(clip); print(len(F),F[0].shape)
    g,w,hsv=masks(F[0])
    n,l,st,cen=cv2.connectedComponentsWithStats(g.astype(np.uint8))
    for i in np.argsort(-st[:,4])[:6]:
        if i==0: continue
        print('green blob',st[i],cen[i])
    n,l,st,cen=cv2.connectedComponentsWithStats(w.astype(np.uint8))
    for i in np.argsort(-st[:,4])[:8]:
        if i==0: continue
        print('white blob',st[i],cen[i])
