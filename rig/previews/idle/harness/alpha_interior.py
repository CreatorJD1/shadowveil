# pixels inside the character silhouette (>= 4 px from any fully transparent pixel) with alpha < 255; only the outer edge may be partial
import sys,json,os,numpy as np
from PIL import Image
from scipy import ndimage as nd
def interior_partial(a,depth=4):
    inside=nd.binary_erosion(a>0,iterations=depth);m=inside&(a<255);interior_partial.lt240=int((inside&(a<240)).sum());return int(m.sum()),(int(a[inside].min()) if inside.any() else 255),m
if __name__=='__main__':
    if sys.argv[1]=='--files':
        for f in sys.argv[2:]:
            a=np.array(Image.open(f).convert('RGBA'))[...,3];n,mn,_=interior_partial(a);print(os.path.basename(f),'interior alpha<255 px',n,'<240',interior_partial.lt240,'min alpha',mn)
    else: # frames dir -> per-frame series json
        fd,out=sys.argv[1],sys.argv[2];fs=sorted(x for x in os.listdir(fd) if x.endswith('.png'));step=int(sys.argv[3]) if len(sys.argv)>3 else 1;ser=[]
        for f in fs[::step]:
            a=np.array(Image.open(os.path.join(fd,f)))[...,3];n,mn,_=interior_partial(a);ser.append([f,n,mn,interior_partial.lt240])
        ns=[s[1] for s in ser];r=dict(frames=len(ser),step=step,max=max(ns),mean=round(float(np.mean(ns)),1),framesAbove0=sum(1 for x in ns if x>0),minAlpha=min(s[2] for s in ser),max240=max(s[3] for s in ser),mean240=round(float(np.mean([s[3] for s in ser])),1),series=ser)
        json.dump(r,open(out,'w'));print(fd,{k:v for k,v in r.items() if k!='series'})
