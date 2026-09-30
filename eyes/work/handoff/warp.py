import cv2, numpy as np, json
M=json.load(open('body_tools/work/apose_turn/angle_map.json'))['handoff']
OUT='eyes/work/handoff/tmp/'
for v in ['apose','left','right']:
    h=M[v]; f=cv2.imread('reference/apose_turn/frames/f%03d.png'%h['frame'])
    A=np.float32([[h['scale'],0,h['dx']],[0,h['scale'],h['dy']]])
    w=cv2.warpAffine(f,A,(1365,1739),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=(255,255,255))
    cv2.imwrite(OUT+'warp_%s.png'%v,w)
    b=cv2.imread('views/%s/base.png'%v,cv2.IMREAD_UNCHANGED)
    a=b[...,3:4]/255.; bb=(b[...,:3]*a+255*(1-a)).astype(np.uint8)
    cv2.imwrite(OUT+'baseflat_%s.png'%v,bb)
    x0,y0,x1,y1={'apose':(590,180,780,280),'left':(560,160,680,260),'right':(690,160,810,260)}[v]
    z=6
    for n,im in [('w',w),('b',bb)]:
        c=cv2.resize(im[y0:y1,x0:x1],None,fx=z,fy=z,interpolation=cv2.INTER_NEAREST)
        for gx in range(0,x1-x0,10): cv2.line(c,(gx*z,0),(gx*z,c.shape[0]),(0,0,255) if (x0+gx)%50==0 else (200,200,200),1)
        for gy in range(0,y1-y0,10): cv2.line(c,(0,gy*z),(c.shape[1],gy*z),(0,0,255) if (y0+gy)%50==0 else (200,200,200),1)
        cv2.imwrite(OUT+'z_%s_%s.png'%(v,n),c)
    print(v,'origin',x0,y0,'grid 10px, red every 50')
