# mirror-pair test with key holes left open (seg fill_holes closes the leg gap at f083-084 / f130-135)
import sys,json,numpy as np
from PIL import Image
sys.path.insert(0,'/workspace/shadowveil/body_tools/work/apose_turn'); from seg import mask_of
FR='/workspace/shadowveil/reference/apose_turn/frames/f%03d.png'
def mk(f):
    a=np.array(Image.open(FR%f).convert('RGB')).astype(int); key=(a[...,2]-np.maximum(a[...,0],a[...,1]))>120
    return mask_of(FR%f)&~key
def norm(f,mirror=False):
    m=mk(f); ys,xs=np.nonzero(m); t,b=ys.min(),ys.max(); s=1000/(b-t)
    hb=m[int(t+.45*(b-t)):int(t+.5*(b-t))]; cx=np.median(np.nonzero(hb)[1])
    if mirror: m=m[:,::-1]; cx=m.shape[1]-1-cx
    im=Image.fromarray((m*255).astype(np.uint8)).transform((800,1100),Image.AFFINE,(1/s,0,cx-400/s,0,1/s,t-50/s),resample=Image.BILINEAR)
    return np.array(im)>127
def iou(a,b): return round(float((a&b).sum()/(a|b).sum()),4)
out={}
for name,ref,rng in (('225_vs_mirror_f087',87,range(125,138)),('225_vs_mirror180_f033',33,range(125,138)),('135_vs_mirror_f131',131,range(81,94)),('135_vs_mirror180_f191',191,range(81,94))):
    R=norm(ref,True); out[name]={f:iou(norm(f),R) for f in rng}
    best=max(out[name],key=out[name].get); print(name,'best f%03d'%best,out[name])
json.dump(out,open('/workspace/shadowveil/body_tools/work/apose_turn/diagonals/_mirror_open.json','w'),indent=1)
