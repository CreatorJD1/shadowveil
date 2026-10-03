import json,sys,numpy as np
from PIL import Image,ImageDraw
from seg import seg
NEAR={'45_L':None,'135_L':None,'225_R':None,'315_R':None}
SIGN={'+v':1,'-v':-1};DC=json.load(open('../turn_check/diag_check.json'))
OV=json.load(open('seg_override.json')) if len(sys.argv)>1 else {}
COL={'palm':(200,200,200)};import colorsys
names=[f+s for f in ['Index','Middle','Ring','Pinky','Thumb'] for s in '123']
for i,n in enumerate(names): r,g,b=colorsys.hsv_to_rgb((i//3)/5,0.4+0.25*(i%3),1);COL[n]=(int(r*255),int(g*255),int(b*255))
res={}
for k in NEAR:
    z=np.load(f'cut/{k}.npz');lab,piv,dbg=seg(z,SIGN[DC[k]['thumb_side']],override=OV.get(k));res[k]=dict(piv=piv,dbg=dbg)
    np.save(f'cut/{k}_lab.npy',lab)
    m=z['alpha']>0;ys,xs=np.nonzero(m);x0,y0=xs.min()-4,ys.min()-4;x1,y1=xs.max()+5,ys.max()+5
    c=np.zeros((y1-y0,x1-x0,3),np.uint8)+40
    for n,cl in COL.items(): c[(lab[y0:y1,x0:x1]==n)]=cl
    im=Image.fromarray(c).resize(((x1-x0)*5,(y1-y0)*5),Image.NEAREST);d=ImageDraw.Draw(im);T=lambda p:((p[0]-x0+.5)*5,(p[1]-y0+.5)*5)
    for n,p in piv.items():
        q=T(p);d.ellipse([q[0]-4,q[1]-4,q[0]+4,q[1]+4],outline=(0,0,0) if 'tip' not in n else (255,0,0),width=2)
    for p in dbg['valleys']: q=T(p);d.rectangle([q[0]-3,q[1]-3,q[0]+3,q[1]+3],fill=(0,0,255))
    d.text((3,3),k,fill=(255,255,255));im.save(f'cut/{k}_lab.png');print(k,{n:int((lab==n).sum()) for n in COL})
json.dump(res,open('seg.json','w'),indent=1)
