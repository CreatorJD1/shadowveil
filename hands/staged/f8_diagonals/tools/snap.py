# F8 try 6: try5 parts with every px RGB (alpha>0) snapped to the nearest colour of HER cut palette for that hand
# (cut/<ang>_<S>.npz rgb where alpha==255; keyed, no blue).  Per-colour function -> parts still rebuild the snapped hand exactly.
import numpy as np,json,glob,os,shutil,sys
from PIL import Image
from scipy.spatial import cKDTree
SRC,OUT=sys.argv[1],sys.argv[2];shutil.rmtree(OUT,ignore_errors=True);shutil.copytree(SRC,OUT)
def blue(c): c=c.astype(int);return c[...,2]-np.maximum(c[...,0],c[...,1])>25
log={}
for ang in ['45','135','225','315']:
    for S in 'LR':
        z=np.load(f'cut/{ang}_{S}.npz');pal=np.unique(z['rgb'][z['alpha']==255],axis=0);assert not blue(pal).any();T=cKDTree(pal.astype(float))
        files=sorted(glob.glob(f'{OUT}/{ang}/{S}_*.png'));ch=0;dmax=0;n=0
        for f in files:
            a=np.array(Image.open(f).convert('RGBA'));m=a[...,3]>0
            if not m.any(): continue
            d,i=T.query(a[m][:,:3].astype(float));new=pal[i];ch+=int((new!=a[m][:,:3]).any(1).sum());dmax=max(dmax,float(d.max()));n+=int(m.sum())
            a[...,:3][m]=new;Image.fromarray(a).save(f)
        log[f'{ang}_{S}']=dict(palette=len(pal),px=n,snapped_px=ch,max_rgb_dist=round(dmax,2))
        print(ang,S,log[f'{ang}_{S}'],flush=True)
json.dump(log,open(f'{OUT}/snap_log.json','w'),indent=1)
