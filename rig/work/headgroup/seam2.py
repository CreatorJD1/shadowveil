import json,numpy as np; from PIL import Image; from scipy import ndimage as nd
L=lambda f:np.array(Image.open(f).convert('RGBA')).astype(int)
def holes(a):
    t=a<128; lab,n=nd.label(t); b=set(np.unique(np.r_[lab[0],lab[-1],lab[:,0],lab[:,-1]])); return np.isin(lab,[i for i in range(1,n+1) if i not in b])
def bg_inside(A):   # see-through px inside the figure's row span (between leftmost and rightmost opaque px per row), neck band only
    op=A[...,3]>=250; m=np.zeros_like(op)
    for y in range(op.shape[0]):
        xs=np.nonzero(op[y])[0]
        if len(xs): m[y,xs.min():xs.max()+1]=~op[y,xs.min():xs.max()+1]
    return m
H=json.load(open('hg_render.json')); S=json.load(open('seam.json')); out={}
NECK={'apose':(600,300,765,400),'left':(590,290,740,400),'right':(625,290,775,400),'back':(600,280,760,400)}
for v,info in H.items():
    dx,dy=info['applied']['dx'],info['applied']['dy']; A0=L(f'renders/{v}_a0.png'); A1=L(f'renders/{v}_a1.png'); x0,y0,x1,y1=NECK[v]
    h0,h1=holes(A0[...,3]),holes(A1[...,3])
    semi=lambda A:int(((A[y0:y1,x0:x1,3]>0)&(A[y0:y1,x0:x1,3]<250)&nd.binary_erosion(A[y0:y1,x0:x1,3]>0,iterations=3)).sum())
    out[v]=dict(frame=info['handoff']['frame'],offset_dx_dy=[dx,dy],
        neck_gap_px=int((h1&~h0)[y0:y1,x0:x1].sum()),                       # new enclosed see-through px at the neck
        neck_gap_px_whole_figure=int((h1&~h0).sum()),
        neck_interior_semitransparent_px=[semi(A0),semi(A1)],
        neck_stretch_px=-dy, neck_shear_px=dx,
        neck_overlap_px=max(0,dy)*0, note='skin mesh: neck skin stretches (dy<0) or compresses (dy>0) by the offset; no cut')
    print(v,out[v])
json.dump(out,open('neck_seam.json','w'),indent=1)
