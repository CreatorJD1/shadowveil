import numpy as np,glob,json
from PIL import Image
from scipy import ndimage as ndi
def interior(alpha):
    t=alpha==0;lab,n=ndi.label(t);border=set(np.unique(np.r_[lab[0],lab[-1],lab[:,0],lab[:,-1]]))-{0}
    big={i+1 for i,s in enumerate(ndi.sum(t,lab,range(1,n+1))) if s>5000}
    return t&~np.isin(lab,list(border|big))
out={}
for f in sorted(glob.glob('br/*_live__*.png')):
    v,p=f.split('/')[-1].split('_live__');p=p[:-4]
    a=np.asarray(Image.open(f))[...,3];b=np.asarray(Image.open(f.replace('_live__','_fix__')))[...,3]
    ia,ib=interior(a),interior(b);edge_new=(b==0)&(a>0)&~ib
    out[f'{v}/{p}']={'interior_holes_live':int(ia.sum()),'interior_holes_fix':int(ib.sum()),'new_interior_holes':int((ib&~ia).sum()),'outline_px_uncovered':int(edge_new.sum()),'outline_px_covered':int(((a==0)&(b>0)).sum())}
json.dump(out,open('holes_live_vs_fix.json','w'),indent=1)
for k,r in out.items():
    if any(r[x] for x in r): print(k,r)
