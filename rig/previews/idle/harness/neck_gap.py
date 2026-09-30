import numpy as np,json,sys
from PIL import Image
from scipy import ndimage as nd
N=json.loads(sys.argv[1]);out={}
def disk(r):
    y,x=np.ogrid[-r:r+1,-r:r+1];return x*x+y*y<=r*r
for v,(nx,ny) in N.items():
    rest=np.array(Image.open(f'{v}_rest.png'));out[v]={}
    z=np.array(Image.open(f'{v}_zero.png'));out[v]['zero_vs_rest_px']=int((np.abs(z.astype(int)-rest.astype(int)).max(-1)>0).sum())
    win=(slice(int(ny)-110,int(ny)+60),slice(int(nx)-150,int(nx)+150))
    def gaps(A):
        op=A>=128;lab,n=nd.label(~op);b=set(np.unique(np.r_[lab[0],lab[-1],lab[:,0],lab[:,-1]]));enc=np.isin(lab,list(b),invert=True)&~op
        cl=nd.binary_closing(op,structure=disk(3),border_value=0);tear=cl&~op&~enc
        semi=(A>0)&(A<255)&nd.binary_erosion(op,structure=disk(4))
        return enc,tear,semi
        
    re,rt,rs=gaps(rest[...,3][win])
    for n in ('tiltP','tiltM','nodP','nodM','tiltP_leanM','nodP_leanP'):
        a=np.array(Image.open(f'{v}_{n}.png'))[...,3][win];e,t,s=gaps(a)
        ne=e&~nd.binary_dilation(re,iterations=3);nt=t&~nd.binary_dilation(rt,iterations=3);ns=s&~nd.binary_dilation(rs,iterations=2)
        # widest gap: max distance-transform of holes+tears
        g=ne|nt;w=float(2*nd.distance_transform_edt(g).max()) if g.any() else 0.0
        out[v][n]=dict(holes=int(ne.sum()),tears=int(nt.sum()),seamAlpha=int(ns.sum()),maxGapWidthPx=round(w,1))
    print(v,out[v])
json.dump(out,open('neck_gap.json','w'),indent=1)
