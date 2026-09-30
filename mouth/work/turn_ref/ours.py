# Our rest mouth (views/<v>/mouth/rest.png over base.png), measured with the same functions. Read-only.
import numpy as np, json
from PIL import Image
from scipy import ndimage as ndi
from facemeas import *
out={}
for v,(ax,ay,facing) in {'apose':(681,286,0),'left':(601,271,-1),'right':(771,274,1)}.items():
    b=Image.open(f'/workspace/shadowveil/views/{v}/base.png').convert('RGBA'); b.alpha_composite(Image.open(f'/workspace/shadowveil/views/{v}/mouth/rest.png').convert('RGBA'))
    A=np.array(b); a=A[...,:3].copy(); a[A[...,3]<128]=(0,0,255)
    skin=skin_level(a,(ay-45,ay-15,ax-25,ax+25))
    m=mouth(a,(ay-14,ay+16,ax-40,ax+40),skin)
    # iris: stricter orange for our more saturated skin
    s=a[ay-90:ay-20,ax-100:ax+100].astype(int); r,g,bb=s[...,0],s[...,1],s[...,2]
    eyes={}
    for name,mm in (('orange',(r>g+40)&(g>bb+60)&(r>150)),('green',(g>r+8)&(g>bb+25)&(g>70))):
        lab,n=ndi.label(mm)
        if n: 
            sz=ndi.sum(mm,lab,range(1,n+1)); k=int(np.argmax(sz))+1
            if sz[k-1]>=6: cy,cx=ndi.center_of_mass(lab==k); eyes[name]=(round(cx+ax-100,1),round(cy+ay-90,1),int(sz[k-1]))
    on=m['leftOnContour'] or m['rightOnContour']
    if not on: chin=chin_below(a,m['cx'],m['bot']+1,skin,int(m['cy']+70))
    else:
        fd=-1 if m['leftOnContour'] else 1; ys=list(range(int(m['bot'])+1,int(m['cy'])+70)); e=[]
        for y in ys:
            fg=A[y,int(m['cx'])-60:int(m['cx'])+60,3]>128; xs=np.nonzero(fg)[0]+int(m['cx'])-60
            e.append(((xs.min() if fd<0 else xs.max())*fd) if len(xs) else -1e9)
        k=int(np.argmax(e[:35])); chin=None
        for j in range(k+1,len(e)):
            if e[j]<e[j-1]-8: chin=float(ys[j-1]); break
    nb=nose(a,int(m['cx']-45),int(m['cx']+45),int(m['cy']-40),int(m['top']-1),skin,facing if on else 0)
    ey=float(np.mean([e_[1] for e_ in eyes.values()]))
    row=a[int(round(m['cy']))].astype(int); bgr=(row[:,2]>row[:,0]+60)&(row[:,2]>row[:,1]+60); c0=int(round(m['cx'])); L=c0
    while L>0 and not bgr[L-1]: L-=1
    R_=c0
    while R_<len(bgr)-1 and not bgr[R_+1]: R_+=1
    if on: yf,yb=(m['yL'],m['yR']) if m['leftOnContour'] else (m['yR'],m['yL']); lift=yf-yb
    else: lift=m['lift']
    ce=chin-ey
    out[v]=dict(eyes=eyes,eyeLineY=round(ey,2),chinY=chin,CE_px=round(ce,2),mouthCx=round(m['cx'],2),seamY=round(m['cy'],2),mouthL=round(m['left'],2),mouthR=round(m['right'],2),
        W_px=m['W'],H_px=m['H'],W_over_CE=round(m['W']/ce,3),cornerLift_px=round(lift,2),cornerLift_over_CE=round(lift/ce,3),bothCornersVisible=not on,
        contourSide=('left' if m['leftOnContour'] else 'right' if m['rightOnContour'] else ''),noseX=nb[0] if nb else None,noseY=nb[1] if nb else None,
        seam_below_eye_over_CE=round((m['cy']-ey)/ce,3),chin_below_seam_over_CE=round((chin-m['cy'])/ce,3),
        seam_below_nose_over_CE=round((m['cy']-nb[1])/ce,3) if nb else None,mouth_dx_from_nose_over_CE=round((m['cx']-nb[0])/ce,3) if nb else None,
        faceL=L,faceR=R_,mouth_pos_in_jaw=round((m['cx']-L)/(R_-L),3),closed=bool(m['openSpan']<1.5 and m['teethPx']<3),sharp=m['sharp'],skinL=skin)
    ov=m['_big'].astype(np.uint8).copy(); e2=m['_m']^ndi.binary_erosion(m['_m']); ov[e2]=(0,255,0); Image.fromarray(ov).save(f'tmp/ours_{v}_qa.png')
    print(v,{k:out[v][k] for k in out[v] if k!='eyes'},out[v]['eyes'])
json.dump(out,open('ours_rest.json','w'),indent=1,default=float)
