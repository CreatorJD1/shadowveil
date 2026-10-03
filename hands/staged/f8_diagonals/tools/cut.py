# F8 step 1: cut her hand from the diagonal turn frame at the red wrist line (diag_check.json), key out the blue fringe, re-matte.
# cut.py -> work/f8/cut/<ang>_<S>.npz (rgb, alpha binary, geometry) + debug png
import json,os,numpy as np
from PIL import Image
from scipy import ndimage as nd
import sys; sys.path.insert(0,'../turn_check'); from locate import fg
ROOT='/workspace/shadowveil/';DC=json.load(open('../turn_check/diag_check.json'));DG=json.load(open(ROOT+'body_tools/work/apose_turn/diagonals/diagonals.json'))['diagonals']
SW={e['f']:e for e in json.load(open('../turn_check/sweep2.json'))}
UNDER=float(os.environ.get('F8_UNDER',3))   # px of her forearm kept past the cut (hidden under Base Body's forearm)
os.makedirs('cut',exist_ok=True)
def blue(a): a=a.astype(int); return a[...,2]-np.maximum(a[...,0],a[...,1])>25
for key,r in DC.items():
    ang,S=key.split('_');dg=DG[ang];im=np.array(Image.open(ROOT+dg['file']).convert('RGB'));h=SW[r['frame']]['hands'][S]
    w=np.array(h['wrist']);u=np.array(h['axis'],float);u/=np.linalg.norm(u);v=np.array([-u[1],u[0]])
    yy,xx=np.mgrid[:im.shape[0],:im.shape[1]];pu=(xx-w[0])*u[0]+(yy-w[1])*u[1];pv=(xx-w[0])*v[0]+(yy-w[1])*v[1]
    F=fg(im);B=blue(im)
    box=(pu>=-UNDER)&(pu<=h['L']+6)&(np.abs(pv)<=h['W']/2+8)
    lab,_=nd.label(F&box);k=lab[int(round(w[1]+3*u[1])),int(round(w[0]+3*u[0]))];hand0=lab==k
    # on the forearm side keep only the strip within the wrist width (no sleeve/forearm edge spill)
    hand0&=~((pu<0)&(np.abs(pv)>h['wrist_w']/2+1))
    keyed=hand0&B                                   # bluish fringe -> keyed out
    m=hand0&~B
    lab2,n2=nd.label(m);sz=np.bincount(lab2.ravel());sz[0]=0;m=lab2==sz.argmax()   # drop specks cut off by keying
    # re-matte: outer 2 px ring px that are still a key blend (B>G+10 and not her dark line) get alpha by unmixing against the key
    # (key G=0 -> alpha = G/G_ref) and the colour of the nearest clean interior px of hers; px with alpha<0.1 are dropped.
    ii=im.astype(int);lum=0.299*ii[...,0]+0.587*ii[...,1]+0.114*ii[...,2]
    ring=m&~nd.binary_erosion(m,iterations=2);fr=ring&(ii[...,2]-ii[...,1]>10)&(lum>=95)
    clean=m&~fr&~(ring&(ii[...,2]-ii[...,1]>10))
    idx=nd.distance_transform_edt(~clean,return_distances=False,return_indices=True);ny,nx=idx[0],idx[1]
    rgb=im.copy();A=m.astype(float)
    ref=im[ny,nx].astype(float);a=np.clip(ii[...,1]/np.maximum(ref[...,1],1),0,1)
    A[fr]=a[fr];rgb[fr]=im[ny,nx][fr]
    drop=fr&(A<0.1);A[drop]=0;m=A>0
    al=np.round(A*255).astype(np.uint8)
    holes=nd.binary_fill_holes(m)&~m               # enclosed key holes inside the hand (cannot be filled with her px -> report)
    np.savez_compressed(f'cut/{key}.npz',rgb=rgb,alpha=al,orig=im,fringe=fr,pu=pu,pv=pv,w=w,u=u,v=v,frame=r['frame'],scale=dg['view_fit']['scale'],dx=dg['view_fit']['dx'],dy=dg['view_fit']['dy'])
    ys,xs=np.nonzero(m);x0,x1,y0,y1=xs.min()-4,xs.max()+5,ys.min()-4,ys.max()+5
    c=np.zeros((y1-y0,x1-x0,4),np.uint8);c[...,:3]=rgb[y0:y1,x0:x1];c[...,3]=al[y0:y1,x0:x1]
    bg=Image.new('RGBA',(x1-x0,y1-y0),(60,60,60,255));bg.alpha_composite(Image.fromarray(c));bg.resize(((x1-x0)*4,(y1-y0)*4),Image.NEAREST).save(f'cut/{key}.png')
    print(key,r['frame'],'px',int(m.sum()),'keyed',int(keyed.sum()),'specks',int(n2-1),'rematted',int(fr.sum()),'dropped',int(drop.sum()),'holes',int(holes.sum()),'blue_left',int((blue(rgb)&m).sum()),'bbox',(x0,y0,x1,y1))
