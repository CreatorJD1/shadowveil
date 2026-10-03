# sim.py view piecesdir dx dy -> metrics json + composite arrays (npz) ; head piece shifted by (dx,dy), others at rest
import sys,json,numpy as np
from PIL import Image
from scipy import ndimage
T='/workspace/shadowveil/body_tools/work/hairless_division_staged'
def load(v,pd):
    pj=json.load(open(f'{T}/{v}/parts.json')); order=pj['layerOrder_backToFront']
    return order,{k:np.array(Image.open(f'{T}/{v}/{pd}/{k}.png')).astype(float) for k in order}
def shift(a,dx,dy):
    o=np.zeros_like(a); H,W=a.shape[:2]
    ys=slice(max(dy,0),H+min(dy,0)); yd=slice(max(-dy,0),H+min(-dy,0)); xs=slice(max(dx,0),W+min(dx,0)); xd=slice(max(-dx,0),W+min(-dx,0))
    o[ys,xs]=a[yd,xd]; return o
def over(d,s):
    sa=s[...,3:]/255.; da=d[...,3:]/255.; oa=sa+da*(1-sa)
    rgb=np.where(oa>0,(s[...,:3]*sa+d[...,:3]*da*(1-sa))/np.maximum(oa,1e-9),0); return np.concatenate([rgb,oa*255],-1)
def comp(order,P,dx,dy,moving=('head',)):
    c=np.zeros_like(P[order[0]])
    for k in order: c=over(c,shift(P[k],dx,dy) if k in moving else P[k])
    return c
def metrics(v,pd,dx,dy,box):
    order,P=load(v,pd); r=comp(order,P,0,0); m=comp(order,P,dx,dy)
    y0,y1,x0,x1=box
    op=m[...,3]>=254.5; rop=r[...,3]>=254.5
    enc=ndimage.binary_fill_holes(op)&~op; renc=ndimage.binary_fill_holes(rop)&~rop
    B=np.zeros(op.shape,bool); B[y0:y1,x0:x1]=True
    hs=shift(P['head'],dx,dy)[...,3]>0
    sil=(r[...,3]>0)|hs
    outside=(m[...,3]>0)&~sil&B
    neck=P['neck'][...,3]>0
    newenc=enc&~renc&B
    return dict(view=v,pieces=pd,offset=[dx,dy],enclosed_new=int(newenc.sum()),enclosed_new_alpha0=int((newenc&(m[...,3]<1)).sum()),
        enclosed_all_in_box=int((enc&B).sum()),enclosed_rest_in_box=int((renc&B).sum()),
        px_outside_rest_sil_or_moved_head=int(outside.sum()),neck_px_visible_outside=int((outside&neck).sum()),
        enc_xy=[[int(x),int(y),int(m[y,x,3])] for y,x in zip(*np.nonzero(newenc))][:40],out_xy=[[int(x),int(y)] for y,x in zip(*np.nonzero(outside))][:40]),r,m
if __name__=='__main__':
    v,pd,dx,dy=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]); box=[int(a) for a in sys.argv[5:9]]
    d,r,m=metrics(v,pd,dx,dy,box); print(json.dumps(d))
    np.save(f'/workspace/tmpsv/hg/{v}_{pd}_m.npy',m.astype(np.uint8)); np.save(f'/workspace/tmpsv/hg/{v}_r.npy',r.astype(np.uint8))
