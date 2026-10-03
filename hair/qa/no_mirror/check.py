# No-mirror check: every live + staged hair part vs the horizontally flipped version of every part (incl. itself).
# Crop to alpha bbox; for each pair (A flipped, B) whose bbox sizes differ by <=3 px, slide over the size slack and score
#  mask IoU and exact-RGBA match of overlapping opaque px. A flipped copy (with or without translation) scores ~1.0.
import glob,json,numpy as np
from PIL import Image
R='/workspace/shadowveil'
files=sorted(glob.glob(R+'/views/*/hair/*.png')+glob.glob(R+'/hair/staged/**/hair/*.png',recursive=True))
P=[]
for f in files:
    a=np.array(Image.open(f).convert('RGBA')); m=a[...,3]>0
    if m.sum()<20: continue
    ys,xs=np.nonzero(m); c=a[ys.min():ys.max()+1,xs.min():xs.max()+1]
    P.append(dict(f=f[len(R)+1:],c=c,px=int(m.sum())))
def score(A,B):
    best=(0,0)
    H=min(A.shape[0],B.shape[0]); W=min(A.shape[1],B.shape[1])
    for dy in range(A.shape[0]-H+1):
        for dx in range(A.shape[1]-W+1):
            for ey in range(B.shape[0]-H+1):
                for ex in range(B.shape[1]-W+1):
                    a=A[dy:dy+H,dx:dx+W]; b=B[ey:ey+H,ex:ex+W]; ma=a[...,3]>0; mb=b[...,3]>0
                    iou=(ma&mb).sum()/max(1,(ma|mb).sum()); both=ma&mb
                    ex_=(a[both]==b[both]).all(-1).mean() if both.any() else 0
                    if iou>best[0]: best=(float(iou),float(ex_))
    return best
res=[]; maxiou=0
for i,A in enumerate(P):
    Af=A['c'][:,::-1]
    for j,B in enumerate(P):
        if abs(Af.shape[0]-B['c'].shape[0])>3 or abs(Af.shape[1]-B['c'].shape[1])>3: continue
        iou,ex=score(Af,B['c'])
        res.append(dict(a=A['f'],b=B['f'],iou=round(iou,4),exact=round(ex,4)))
res.sort(key=lambda r:-r['iou'])
res=[r for r in res if 'erase_mask' not in r['a'] and 'erase_mask' not in r['b']]
out=dict(parts=len(P),pairs_tested=len(res),top=res[:25],flagged=[r for r in res if r['iou']>=0.6 or r['exact']>=0.5])
json.dump(out,open(R+'/hair/qa/no_mirror/pairs.json','w'),indent=1)
print(len(P),len(res)); [print(r) for r in res[:12]]
