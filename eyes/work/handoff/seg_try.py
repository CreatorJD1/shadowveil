import cv2, numpy as np, json
T='eyes/work/handoff/tmp/'
def hsv(im): return cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
for v,e in [('apose','EyeR'),('apose','EyeL'),('left','EyeL'),('right','EyeR')]:
    r=json.load(open('views/%s/eyes/rig.json'%v))['measurements'][e]
    x0,y0,x1,y1=r['opening_bbox']; P=22
    X0,Y0,X1,Y1=x0-P,y0-P,x1+P+1,y1+P+1
    rows=[]
    for n in ['warp','baseflat']:
        im=cv2.imread(T+'%s_%s.png'%(n,v))[Y0:Y1,X0:X1]; H=hsv(im)
        h,s,val=H[...,0],H[...,1],H[...,2]
        dark=val<75
        scl=(s<60)&(val>170)
        if e=='EyeL': iris=(h>=35)&(h<=95)&(s>50)&(val>50)
        else: iris=(h>=8)&(h<=30)&(s>150)&(val>120)
        vis=np.zeros_like(im); vis[dark]=(0,0,255); vis[scl]=(255,255,0); vis[iris]=(0,255,0) if e=='EyeL' else (0,200,255)
        rows.append(np.hstack([im,vis]))
    out=cv2.resize(np.vstack(rows),None,fx=5,fy=5,interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(T+'seg_%s_%s.png'%(v,e),out); print(v,e,(X0,Y0))
