import cv2, numpy as np, json
T='eyes/work/handoff/tmp/'
for v,e,win in [('apose','EyeR',(620,205,672,245)),('right','EyeR',(730,200,775,235)),('left','EyeL',(595,200,640,240))]:
    X0,Y0,X1,Y1=win
    rows=[]
    for n in ['warp','baseflat']:
        im=cv2.imread(T+'%s_%s.png'%(n,v))[Y0:Y1,X0:X1]
        lab=cv2.cvtColor(im,cv2.COLOR_BGR2LAB).astype(float)
        # skin = median of pixels with lab close to mode: use border ring
        ring=np.concatenate([lab[:3].reshape(-1,3),lab[-3:].reshape(-1,3)])
        sk=np.median(ring,0)
        a=lab[...,1]-128; b=lab[...,2]-128; L=lab[...,0]*100/255
        hue=np.degrees(np.arctan2(b,a)); C=np.hypot(a,b)
        print(n,v,'skin Lab',sk)
        vis=[]
        for ch,sc in [(L,2.55),(C,4),(hue%180,1.4)]:
            g=np.clip(ch*sc,0,255).astype(np.uint8); vis.append(cv2.applyColorMap(g,cv2.COLORMAP_JET))
        rows.append(np.hstack([im]+vis))
    cv2.imwrite(T+'lab_%s.png'%v,cv2.resize(np.vstack(rows),None,fx=5,fy=5,interpolation=cv2.INTER_NEAREST))
